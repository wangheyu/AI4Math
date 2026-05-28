#!/usr/bin/env python3
"""Dash + Plotly weather simulation viewer: cloudwater scalar + wind vector field.

Displays the OpenDX cloudwater and wind samples on a shared 25×14×8 grid.
Uses ``go.Isosurface`` for cloudwater density and ``go.Cone`` for wind glyphs.

Run from the repository root::

    conda activate ai4math-vis
    python weather_simulation/weather_demo.py

Then open http://127.0.0.1:8054 in a browser.
"""

from __future__ import annotations

import argparse
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update


DATA_DIR = Path(__file__).resolve().parent

COLORSCALE_OPTIONS = [
    {"label": "Viridis", "value": "viridis"},
    {"label": "Plasma", "value": "plasma"},
    {"label": "Inferno", "value": "inferno"},
    {"label": "Blues", "value": "blues"},
    {"label": "Turbo", "value": "turbo"},
]

DEFAULT_CONTROLS = {
    "cloud_threshold": 0.1,
    "cloud_opacity": 0.5,
    "cloud_colorscale": "blues",
    "wind_sample": 1,
    "wind_scale": 0.3,
    "wind_color": "#ef4444",
    "stream_density": 4,
    "stream_width": 0.9,
    "light_x": 1000.0,
    "light_y": -1000.0,
    "light_z": 2000.0,
    "ambient": 0.4,
    "diffuse": 0.8,
    "specular": 0.2,
    "roughness": 0.6,
    "camera_x": 1.8,
    "camera_y": -2.0,
    "camera_z": 1.2,
    "show_axes": True,
    "show_cloud": True,
    "show_wind": True,
    "show_streamlines": False,
}

CAMERA_SLIDER_IDS = {"camera-x", "camera-y", "camera-z"}
WIND_SAMPLE_OPTIONS = [1, 2, 4, 6]
STREAM_DENSITY_OPTIONS = [1, 2, 3, 4]
STREAM_DENSITY_TO_STRIDE = {1: 5, 2: 4, 3: 3, 4: 2}
STREAM_DENSITY_TO_X_COUNT = {1: 3, 2: 5, 3: 7, 4: 9}
STREAM_DENSITY_TO_MAX_STARTS = {1: 25, 2: 50, 3: 75, 4: 100}
STREAMTUBE_MAXDISPLAYED = {1: 1500, 2: 2500, 3: 4500, 4: 9000}
CLOUD_THRESHOLD_MIN = 0.001
CLOUD_THRESHOLD_MAX = 2.0
WIND_SCALE_MIN = 0.1
WIND_SCALE_MAX = 1.0
WIND_ARROW_BASE_SIZEREF = 15.0
STREAM_WIDTH_MIN = 0.1
STREAM_WIDTH_MAX = 2.0


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def normalize_controls(controls: dict | None) -> dict:
    merged = dict(DEFAULT_CONTROLS)
    if controls:
        merged.update(controls)
    merged["cloud_threshold"] = round(
        clamp(float(merged["cloud_threshold"]), CLOUD_THRESHOLD_MIN, CLOUD_THRESHOLD_MAX),
        3,
    )
    merged["cloud_opacity"] = round(clamp(float(merged["cloud_opacity"]), 0.1, 1.0), 2)
    merged["wind_sample"] = min(WIND_SAMPLE_OPTIONS, key=lambda o: abs(o - int(merged.get("wind_sample", 2))))
    merged["wind_scale"] = round(clamp(float(merged["wind_scale"]), WIND_SCALE_MIN, WIND_SCALE_MAX), 2)
    merged["stream_density"] = min(
        STREAM_DENSITY_OPTIONS,
        key=lambda o: abs(o - int(merged.get("stream_density", 2))),
    )
    merged["stream_width"] = round(
        clamp(float(merged["stream_width"]), STREAM_WIDTH_MIN, STREAM_WIDTH_MAX),
        2,
    )
    if merged.get("cloud_colorscale", "") not in {o["value"] for o in COLORSCALE_OPTIONS}:
        merged["cloud_colorscale"] = DEFAULT_CONTROLS["cloud_colorscale"]
    for key in ("light_x", "light_y", "light_z"):
        merged[key] = round(clamp(float(merged[key]), -5000, 5000), 1)
    for key in ("ambient", "diffuse", "roughness"):
        merged[key] = round(clamp(float(merged[key]), 0.0, 1.0), 2)
    merged["specular"] = round(clamp(float(merged["specular"]), 0.0, 2.0), 2)
    for key in ("camera_x", "camera_y"):
        merged[key] = round(clamp(float(merged[key]), -6.0, 6.0), 2)
    merged["camera_z"] = round(clamp(float(merged["camera_z"]), -3.0, 6.0), 2)
    for key in ("show_axes", "show_cloud", "show_wind", "show_streamlines"):
        merged[key] = bool(merged.get(key, True))
    return merged


# ---------------------------------------------------------------------------
# Binary OpenDX parser (for cloudwater.dx and wind.dx)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=2)
def _parse_binary_dx(path_key: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple]:
    """Parse an axis-aligned binary OpenDX file.

    Returns full coordinate grids ``(x, y, z, info)``. The full grids are needed
    because this sample's second and third DX delta vectors map to z and y,
    respectively, rather than to y and z in simple axis order.
    """
    path = Path(path_key)
    payload = path.read_bytes()

    if b"data follows" in payload:
        raise ValueError("ASCII DX not supported by this parser")
    end_marker = b"\nend\n"
    marker_pos = payload.find(end_marker)
    if marker_pos < 0:
        raise ValueError(f"Could not find DX header end marker in {path.name}")
    bin_offset = marker_pos + len(end_marker)
    text = payload[:bin_offset].decode("ascii", errors="ignore")

    counts_match = re.search(r"gridpositions\s+counts\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)", text)
    if not counts_match:
        raise ValueError("Could not find gridpositions in DX file")
    nx, ny, nz = int(counts_match.group(1)), int(counts_match.group(2)), int(counts_match.group(3))

    origin_match = re.search(r"origin\s+([^\n]+)", text)
    origin = np.array([float(v) for v in origin_match.group(1).split()]) if origin_match else np.zeros(3)

    delta_lines = re.findall(r"delta\s+([^\n]+)", text)
    if len(delta_lines) < 3:
        raise ValueError(f"Could not find 3 delta vectors in {path.name}")
    deltas = np.array([[float(v) for v in line.split()] for line in delta_lines[:3]])

    # Coordinate grid: each DX grid index uses the corresponding delta vector.
    i, j, k = np.meshgrid(
        np.arange(nx, dtype=float), np.arange(ny, dtype=float), np.arange(nz, dtype=float),
        indexing="ij",
    )
    x = origin[0] + deltas[0, 0] * i + deltas[1, 0] * j + deltas[2, 0] * k
    y = origin[1] + deltas[0, 1] * i + deltas[1, 1] * j + deltas[2, 1] * k
    z = origin[2] + deltas[0, 2] * i + deltas[1, 2] * j + deltas[2, 2] * k

    # check array metadata for components
    arr_match = re.search(
        r"class\s+array\s+type\s+([a-zA-Z]+)\s+rank\s+([0-9]+)\s+shape\s+([0-9]+)\s+items\s+([0-9]+)",
        text,
    )
    components = 1
    if arr_match:
        shape = int(arr_match.group(3))
        if shape > 1:
            components = shape

    npoints = nx * ny * nz * components
    dtype = np.dtype(">f4")
    values = np.frombuffer(payload[bin_offset : bin_offset + npoints * dtype.itemsize], dtype=dtype, count=npoints)
    # Plotly's orjson serializer rejects non-native byte order, so promote big-endian to native float32.
    values = values.astype(np.float32)
    if values.size != npoints:
        raise ValueError(f"Expected {npoints} float values in {path.name}, got {values.size}")

    return x, y, z, (nx, ny, nz, components, values)


@lru_cache(maxsize=1)
def _load_cloudwater() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, tuple]:
    """Load cloudwater scalar field. Returns (x, y, z, value_3d, info)."""
    x_grid, y_grid, z_grid, info = _parse_binary_dx(str(DATA_DIR / "cloudwater.dx"))
    nx, ny, nz, components, values = info
    value_3d = values.reshape((nx, ny, nz), order="F")
    return x_grid, y_grid, z_grid, value_3d, (nx, ny, nz, components)


@lru_cache(maxsize=1)
def _load_wind() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, tuple]:
    """Load wind vector field. Returns (x, y, z, vectors_4d, info) where vectors_4d is (nx, ny, nz, 3)."""
    x_grid, y_grid, z_grid, info = _parse_binary_dx(str(DATA_DIR / "wind.dx"))
    nx, ny, nz, components, values = info
    # OpenDX stores vectors as (npoints, 3) in C order. Reshape to (nx, ny, nz, 3) with F order for axes.
    vectors_2d = values.reshape((-1, 3), order="C")
    vectors_4d = np.zeros((nx, ny, nz, 3), dtype=float)
    # Reorder from C to F grid indexing
    for c in range(3):
        flat = vectors_2d[:, c]
        vectors_4d[:, :, :, c] = flat.reshape((nx, ny, nz), order="F")
    return x_grid, y_grid, z_grid, vectors_4d, (nx, ny, nz, components)


def _as_streamtube_grid(
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    z_grid: np.ndarray,
    wind_4d: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Reorder the DX index axes into conventional x, y, z order for streamtube integration."""
    return (
        np.transpose(x_grid, (0, 2, 1)),
        np.transpose(y_grid, (0, 2, 1)),
        np.transpose(z_grid, (0, 2, 1)),
        np.transpose(wind_4d, (0, 2, 1, 3)),
    )


def _interior_indices(size: int, *, stride: int | None = None, count: int | None = None) -> np.ndarray:
    if size <= 2:
        return np.arange(size)
    if count is not None:
        return np.unique(np.linspace(1, size - 2, min(count, size - 2)).round().astype(int))
    values = np.arange(1, size - 1, stride or 1)
    return np.unique(np.r_[values, size - 2])


def _streamline_starts(
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    z_grid: np.ndarray,
    density: int,
) -> dict[str, np.ndarray]:
    """Place streamline seeds across several x sections to cover the full domain."""
    stride = STREAM_DENSITY_TO_STRIDE[density]
    nx, ny, nz = x_grid.shape
    i_idx = _interior_indices(nx, count=STREAM_DENSITY_TO_X_COUNT[density])
    j_idx = _interior_indices(ny, stride=stride)
    k_idx = _interior_indices(nz, stride=stride)
    ii, jj, kk = np.meshgrid(i_idx, j_idx, k_idx, indexing="ij")
    flat_indices = np.arange(ii.size)
    max_starts = STREAM_DENSITY_TO_MAX_STARTS[density]
    if ii.size > max_starts:
        flat_indices = np.unique(np.linspace(0, ii.size - 1, max_starts).round().astype(int))
    return {
        "x": x_grid[ii, jj, kk].ravel()[flat_indices],
        "y": y_grid[ii, jj, kk].ravel()[flat_indices],
        "z": z_grid[ii, jj, kk].ravel()[flat_indices],
    }


# ---------------------------------------------------------------------------
# Figure building
# ---------------------------------------------------------------------------


def make_weather_figure(
    *,
    cloud_threshold: float,
    cloud_opacity: float,
    cloud_colorscale: str,
    wind_sample: int,
    wind_scale: float,
    wind_color: str,
    stream_density: int,
    stream_width: float,
    light_x: float,
    light_y: float,
    light_z: float,
    ambient: float,
    diffuse: float,
    specular: float,
    roughness: float,
    camera_x: float,
    camera_y: float,
    camera_z: float,
    show_axes: bool,
    show_cloud: bool,
    show_wind: bool,
    show_streamlines: bool,
    camera_override: dict | None = None,
) -> go.Figure:
    traces: list[go.BaseTraceType] = []

    # --- Cloud isosurface ---
    if show_cloud:
        x_grid, y_grid, z_grid, cloud_3d, _info = _load_cloudwater()
        isomax_val = min(cloud_threshold + 0.1, float(cloud_3d.max()))
        traces.append(
            go.Isosurface(
                x=x_grid.ravel(order="F"),
                y=y_grid.ravel(order="F"),
                z=z_grid.ravel(order="F"),
                value=cloud_3d.ravel(order="F"),
                isomin=cloud_threshold,
                isomax=isomax_val,
                surface={"show": True, "count": 1},
                colorscale=cloud_colorscale,
                opacity=cloud_opacity,
                caps={"x": {"show": False}, "y": {"show": False}, "z": {"show": False}},
                slices={"x": {"show": False}, "y": {"show": False}, "z": {"show": False}},
                lighting={"ambient": ambient, "diffuse": diffuse, "specular": specular, "roughness": roughness},
                lightposition={"x": light_x, "y": light_y, "z": light_z},
                colorbar={"title": "cloudwater"},
                name="cloud",
                hovertemplate="x=%{x:.0f}<br>y=%{y:.0f}<br>z=%{z:.0f}<br>cloud=%{value:.3f}<extra></extra>",
            )
        )

    # --- Wind streamtubes ---
    if show_streamlines:
        x_grid, y_grid, z_grid, wind_4d, _info = _load_wind()
        x_stream, y_stream, z_stream, wind_stream = _as_streamtube_grid(x_grid, y_grid, z_grid, wind_4d)
        u = wind_stream[:, :, :, 0]
        v = wind_stream[:, :, :, 1]
        w = wind_stream[:, :, :, 2]
        speed = np.linalg.norm(wind_stream, axis=3)
        traces.append(
            go.Streamtube(
                x=x_stream.ravel(order="C"),
                y=y_stream.ravel(order="C"),
                z=z_stream.ravel(order="C"),
                u=u.ravel(order="C"),
                v=v.ravel(order="C"),
                w=w.ravel(order="C"),
                starts=_streamline_starts(x_stream, y_stream, z_stream, stream_density),
                sizeref=stream_width,
                maxdisplayed=STREAMTUBE_MAXDISPLAYED[stream_density],
                colorscale="Turbo",
                cmin=float(speed.min()),
                cmax=float(speed.max()),
                opacity=0.8,
                colorbar={"title": "wind speed"},
                name="wind streamlines",
                hoverinfo="skip",
            )
        )

    # --- Wind cone glyphs ---
    if show_wind:
        x_grid, y_grid, z_grid, wind_4d, info = _load_wind()
        nx, ny, nz = info[0], info[1], info[2]
        # Subsample
        sx, sy, sz = slice(None, None, wind_sample), slice(None, None, wind_sample), slice(None, None, wind_sample)
        u = wind_4d[sx, sy, sz, 0].ravel(order="F")
        v = wind_4d[sx, sy, sz, 1].ravel(order="F")
        w = wind_4d[sx, sy, sz, 2].ravel(order="F")

        npoints = len(u)
        if npoints > 0:
            traces.append(
                go.Cone(
                    x=x_grid[sx, sy, sz].ravel(order="F"),
                    y=y_grid[sx, sy, sz].ravel(order="F"),
                    z=z_grid[sx, sy, sz].ravel(order="F"),
                    u=u, v=v, w=w,
                    sizemode="scaled",
                    sizeref=WIND_ARROW_BASE_SIZEREF * wind_scale,
                    anchor="center",
                    colorscale=[[0, wind_color], [1, wind_color]],
                    showscale=False,
                    name="wind",
                    hoverinfo="skip",
                )
            )

    axis_style = {
        "showgrid": show_axes,
        "gridcolor": "#d1d5db",
        "gridwidth": 2,
        "showline": show_axes,
        "linecolor": "#111827",
        "linewidth": 3,
        "zeroline": show_axes,
        "zerolinecolor": "#111827",
        "zerolinewidth": 3,
        "ticks": "outside" if show_axes else "",
        "showticklabels": show_axes,
        "visible": show_axes,
        "backgroundcolor": "#ffffff",
    }

    camera = {"eye": {"x": camera_x, "y": camera_y, "z": camera_z}, "center": {"x": 0, "y": 0, "z": 0}}
    if camera_override:
        for key in ("eye", "center", "up"):
            if key in camera_override:
                camera[key] = camera_override[key]

    stream_label = f", streamlines d{stream_density}, width {stream_width:.1f}" if show_streamlines else ""
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=f"Weather simulation - cloud >= {cloud_threshold:.3f}, wind stride {wind_sample}, arrows x{wind_scale:.1f}{stream_label}",
        margin={"l": 0, "r": 0, "t": 46, "b": 0},
        uirevision="weather-sim",
        paper_bgcolor="#ffffff",
        scene={
            "xaxis": {**axis_style, "title": "x (m)"},
            "yaxis": {**axis_style, "title": "y (m)"},
            "zaxis": {**axis_style, "title": "z (m)"},
            "aspectmode": "data",
            "camera": camera,
        },
    )
    return fig


def make_figure_from_controls(controls: dict, camera_override: dict | None = None) -> go.Figure:
    controls = normalize_controls(controls)
    return make_weather_figure(
        cloud_threshold=controls["cloud_threshold"],
        cloud_opacity=controls["cloud_opacity"],
        cloud_colorscale=controls["cloud_colorscale"],
        wind_sample=controls["wind_sample"],
        wind_scale=controls["wind_scale"],
        wind_color=controls["wind_color"],
        stream_density=controls["stream_density"],
        stream_width=controls["stream_width"],
        light_x=controls["light_x"],
        light_y=controls["light_y"],
        light_z=controls["light_z"],
        ambient=controls["ambient"],
        diffuse=controls["diffuse"],
        specular=controls["specular"],
        roughness=controls["roughness"],
        camera_x=controls["camera_x"],
        camera_y=controls["camera_y"],
        camera_z=controls["camera_z"],
        show_axes=controls["show_axes"],
        show_cloud=controls["show_cloud"],
        show_wind=controls["show_wind"],
        show_streamlines=controls["show_streamlines"],
        camera_override=camera_override,
    )


# ---------------------------------------------------------------------------
# Camera helpers
# ---------------------------------------------------------------------------


def numeric_xyz(source: dict | None) -> dict | None:
    if not isinstance(source, dict):
        return None
    try:
        return {axis: float(source[axis]) for axis in ("x", "y", "z")}
    except (KeyError, TypeError, ValueError):
        return None


def camera_from_relayout(relayout_data: dict | None) -> dict | None:
    if not isinstance(relayout_data, dict):
        return None
    camera = relayout_data.get("scene.camera")
    if isinstance(camera, dict):
        parsed = {key: value for key in ("eye", "center", "up") if (value := numeric_xyz(camera.get(key))) is not None}
        if "eye" in parsed:
            return parsed
    eye = numeric_xyz(relayout_data.get("scene.camera.eye"))
    if eye is not None:
        return {"eye": eye}
    parsed = {}
    for part in ("eye", "center", "up"):
        value = numeric_xyz({axis: relayout_data.get(f"scene.camera.{part}.{axis}") for axis in ("x", "y", "z")})
        if value is not None:
            parsed[part] = value
    if "eye" in parsed:
        return parsed
    return None


def should_preserve_user_camera(triggered_id: str | None) -> bool:
    return triggered_id not in CAMERA_SLIDER_IDS


def camera_eye_matches_controls(camera: dict | None, controls: dict, tolerance: float = 0.026) -> bool:
    if not camera or "eye" not in camera:
        return False
    eye = camera["eye"]
    return all(abs(float(eye[axis]) - controls[f"camera_{axis}"]) <= tolerance for axis in ("x", "y", "z"))


# ---------------------------------------------------------------------------
# Dash UI
# ---------------------------------------------------------------------------


def slider(label: str, component_id: str, *, minimum: float, maximum: float, step: float, value: float, marks=None):
    return html.Div(
        [html.Label(label, style={"display": "block"}),
         dcc.Slider(id=component_id, min=minimum, max=maximum, step=step, value=value, marks=marks,
                    updatemode="drag", tooltip={"placement": "bottom", "always_visible": False})],
        style={"marginTop": "15px"},
    )


def create_app() -> Dash:
    app = Dash(__name__)
    app.title = "Weather Simulation"
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.H2("Weather Simulation"),
                    html.P("Cloudwater + Wind — OpenDX sample"),
                    html.H4("Cloud 云水"),
                    slider("Threshold 阈值", "cloud-threshold",
                           minimum=CLOUD_THRESHOLD_MIN, maximum=CLOUD_THRESHOLD_MAX, step=0.001,
                           value=DEFAULT_CONTROLS["cloud_threshold"],
                           marks={0.001: ".001", 0.2: "0.2", 0.5: "0.5", 1.0: "1.0", 2.0: "2.0"}),
                    slider("Opacity 透明度", "cloud-opacity", minimum=0.1, maximum=1.0, step=0.05, value=DEFAULT_CONTROLS["cloud_opacity"]),
                    html.Label("Colorscale", style={"marginTop": "15px", "display": "block"}),
                    dcc.Dropdown(id="cloud-colorscale", value=DEFAULT_CONTROLS["cloud_colorscale"], clearable=False, options=COLORSCALE_OPTIONS),
                    dcc.Checklist(id="show-cloud", options=[{"label": "Show cloud", "value": "on"}], value=["on"], style={"marginTop": "10px"},
                                  inputStyle={"marginRight": "6px"}),
                    html.H4("Wind 风场", style={"marginTop": "22px"}),
                    html.Label("Sample stride", style={"display": "block"}),
                    dcc.Slider(id="wind-sample", min=1, max=6, step=None, value=DEFAULT_CONTROLS["wind_sample"],
                               marks={v: str(v) for v in WIND_SAMPLE_OPTIONS},
                               tooltip={"placement": "bottom", "always_visible": False}),
                    slider("Arrow scale 箭头缩放", "wind-scale",
                           minimum=WIND_SCALE_MIN, maximum=WIND_SCALE_MAX, step=0.1,
                           value=DEFAULT_CONTROLS["wind_scale"],
                           marks={0.1: "0.1", 0.5: "0.5", 1.0: "1.0"}),
                    dcc.Checklist(id="show-wind", options=[{"label": "Show arrows", "value": "on"}], value=["on"], style={"marginTop": "10px"},
                                  inputStyle={"marginRight": "6px"}),
                    dcc.Checklist(id="show-streamlines", options=[{"label": "Show streamlines", "value": "on"}], value=[], style={"marginTop": "10px"},
                                  inputStyle={"marginRight": "6px"}),
                    html.Label("Streamline density", style={"marginTop": "15px", "display": "block"}),
                    dcc.Slider(id="stream-density", min=1, max=4, step=None, value=DEFAULT_CONTROLS["stream_density"],
                               marks={v: str(v) for v in STREAM_DENSITY_OPTIONS},
                               tooltip={"placement": "bottom", "always_visible": False}),
                    slider("Streamline width 流线粗细", "stream-width",
                           minimum=STREAM_WIDTH_MIN, maximum=STREAM_WIDTH_MAX, step=0.1,
                           value=DEFAULT_CONTROLS["stream_width"],
                           marks={0.1: "0.1", 0.9: "0.9", 2.0: "2.0"}),
                    html.H4("Lighting", style={"marginTop": "22px"}),
                    slider("Light X", "light-x", minimum=-5000, maximum=5000, step=250, value=DEFAULT_CONTROLS["light_x"]),
                    slider("Light Y", "light-y", minimum=-5000, maximum=5000, step=250, value=DEFAULT_CONTROLS["light_y"]),
                    slider("Light Z", "light-z", minimum=-1000, maximum=5000, step=250, value=DEFAULT_CONTROLS["light_z"]),
                    slider("Ambient", "ambient", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["ambient"]),
                    slider("Diffuse", "diffuse", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["diffuse"]),
                    slider("Specular", "specular", minimum=0, maximum=2, step=0.05, value=DEFAULT_CONTROLS["specular"]),
                    slider("Roughness", "roughness", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["roughness"]),
                    html.H4("Camera", style={"marginTop": "22px"}),
                    slider("Camera X", "camera-x", minimum=-6, maximum=6, step=0.05, value=DEFAULT_CONTROLS["camera_x"]),
                    slider("Camera Y", "camera-y", minimum=-6, maximum=6, step=0.05, value=DEFAULT_CONTROLS["camera_y"]),
                    slider("Camera Z", "camera-z", minimum=-3, maximum=6, step=0.05, value=DEFAULT_CONTROLS["camera_z"]),
                    dcc.Checklist(id="show-axes", options=[{"label": "Axes", "value": "axes"}], value=["axes"], style={"marginTop": "10px"},
                                  inputStyle={"marginRight": "6px"}),
                    html.Div(id="weather-stats", style={"marginTop": "22px", "fontSize": "14px", "lineHeight": "1.5"}),
                ],
                style={"boxSizing": "border-box", "width": "360px", "padding": "18px", "borderRight": "1px solid #ddd",
                       "fontFamily": "Arial, sans-serif", "overflowY": "auto"},
            ),
            html.Div(
                [dcc.Graph(id="weather-graph", config={"displaylogo": False, "scrollZoom": True},
                           style={"height": "calc(100vh - 24px)"})],
                style={"flex": "1", "padding": "12px"},
            ),
        ],
        style={"display": "flex", "height": "100vh", "margin": "0"},
    )

    @app.callback(
        Output("weather-graph", "figure"),
        Output("weather-stats", "children"),
        Input("cloud-threshold", "value"),
        Input("cloud-opacity", "value"),
        Input("cloud-colorscale", "value"),
        Input("show-cloud", "value"),
        Input("wind-sample", "value"),
        Input("wind-scale", "value"),
        Input("show-wind", "value"),
        Input("show-streamlines", "value"),
        Input("stream-density", "value"),
        Input("stream-width", "value"),
        Input("light-x", "value"),
        Input("light-y", "value"),
        Input("light-z", "value"),
        Input("ambient", "value"),
        Input("diffuse", "value"),
        Input("specular", "value"),
        Input("roughness", "value"),
        Input("camera-x", "value"),
        Input("camera-y", "value"),
        Input("camera-z", "value"),
        Input("show-axes", "value"),
        State("weather-graph", "relayoutData"),
    )
    def update_weather(*args):
        (cloud_threshold, cloud_opacity, cloud_colorscale, show_cloud, wind_sample, wind_scale,
         show_wind, show_streamlines, stream_density, stream_width, light_x, light_y, light_z, ambient, diffuse, specular, roughness,
         camera_x, camera_y, camera_z, show_axes, relayout_data) = args
        controls = normalize_controls({
            "cloud_threshold": cloud_threshold, "cloud_opacity": cloud_opacity,
            "cloud_colorscale": cloud_colorscale, "show_cloud": "on" in (show_cloud or []),
            "wind_sample": wind_sample, "wind_scale": wind_scale, "show_wind": "on" in (show_wind or []),
            "show_streamlines": "on" in (show_streamlines or []),
            "stream_density": stream_density, "stream_width": stream_width,
            "light_x": light_x, "light_y": light_y, "light_z": light_z,
            "ambient": ambient, "diffuse": diffuse, "specular": specular, "roughness": roughness,
            "camera_x": camera_x, "camera_y": camera_y, "camera_z": camera_z,
            "show_axes": "axes" in (show_axes or []),
        })
        relayout_camera = camera_from_relayout(relayout_data)
        if ctx.triggered_id in CAMERA_SLIDER_IDS and camera_eye_matches_controls(relayout_camera, controls):
            _, _, _, cloud_3d, _ = _load_cloudwater()
            return no_update, [html.Div(f"Cloud range: [{cloud_3d.min():.3f}, {cloud_3d.max():.3f}]"),
                               html.Div(f"Threshold: {controls['cloud_threshold']:.3f}"),
                               html.Div(f"Streamline density: {controls['stream_density']}"),
                               html.Div(f"Streamline width: {controls['stream_width']:.1f}")]
        camera_override = relayout_camera if should_preserve_user_camera(ctx.triggered_id) else None
        _, _, _, cloud_3d, _ = _load_cloudwater()
        stats = [
            html.Div(f"Cloud range: [{cloud_3d.min():.3f}, {cloud_3d.max():.3f}]"),
            html.Div(f"Threshold: {controls['cloud_threshold']:.3f}"),
            html.Div(f"Wind sample: every {controls['wind_sample']}"),
            html.Div(f"Arrow scale: x{controls['wind_scale']:.1f}"),
            html.Div(f"Streamline density: {controls['stream_density']}"),
            html.Div(f"Streamline width: {controls['stream_width']:.1f}"),
        ]
        return make_figure_from_controls(controls, camera_override), stats

    @app.callback(
        Output("camera-x", "value"), Output("camera-y", "value"), Output("camera-z", "value"),
        Input("weather-graph", "relayoutData"),
        prevent_initial_call=True,
    )
    def sync_camera_sliders(relayout_data):
        camera = camera_from_relayout(relayout_data)
        if not camera or "eye" not in camera:
            return no_update, no_update, no_update
        eye = camera["eye"]
        c = normalize_controls({"camera_x": eye["x"], "camera_y": eye["y"], "camera_z": eye["z"]})
        return c["camera_x"], c["camera_y"], c["camera_z"]

    return app


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8054)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        x_grid, y_grid, z_grid, cloud_3d, _info = _load_cloudwater()
        print(f"Cloud grid: {cloud_3d.shape}, range [{cloud_3d.min():.4f}, {cloud_3d.max():.4f}]")
        print(
            f"X: [{x_grid.min():.0f}, {x_grid.max():.0f}], "
            f"Y: [{y_grid.min():.0f}, {y_grid.max():.0f}], "
            f"Z: [{z_grid.min():.0f}, {z_grid.max():.0f}]"
        )
        _x, _y, _z, wind_4d, _w = _load_wind()
        mag = np.linalg.norm(wind_4d, axis=3)
        print(f"Wind grid: {wind_4d.shape}, mag range [{mag.min():.1f}, {mag.max():.1f}]")
        fig = make_figure_from_controls(DEFAULT_CONTROLS)
        print(f"Traces: {len(fig.data)}, JSON: {len(fig.to_json())}")
        return
    app = create_app()
    print(f"Dash app running at http://{args.host}:{args.port}")
    (app.run if hasattr(app, "run") else app.run_server)(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
