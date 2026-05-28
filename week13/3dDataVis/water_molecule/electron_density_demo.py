#!/usr/bin/env python3
"""Dash + Plotly water molecule electron density isosurface viewer.

Based on ``basic_3d/plotly_unit_cube_demo.py`` as a template, adapted to display
the OpenDX water molecule electron density sample via Plotly ``go.Isosurface``.

Run from the repository root::

    conda activate ai4math-vis
    python water_molecule/electron_density_demo.py

Then open http://127.0.0.1:8053 in a browser.
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
    {"label": "Jet", "value": "jet"},
    {"label": "Turbo", "value": "turbo"},
    {"label": "Thermal", "value": "thermal"},
]

DISPLAY_OPTIONS = [
    {"label": "Axes 坐标轴", "value": "axes"},
    {"label": "Outline 边框", "value": "outline"},
]

THRESHOLD_MARKS = {
    0.001: ".001",
    0.2: "0.2",
    0.5: "0.5",
    1.1: "1.1",
}

SHELL_WIDTH_MARKS = {
    0.005: ".005",
    0.05: ".05",
    0.2: "0.2",
    0.5: "0.5",
}

DEFAULT_CONTROLS = {
    "threshold": 0.05,
    "shell_width": 0.05,
    "opacity": 0.75,
    "colorscale": "viridis",
    "light_x": 1.6,
    "light_y": -1.2,
    "light_z": 2.0,
    "ambient": 0.4,
    "diffuse": 0.8,
    "specular": 0.3,
    "roughness": 0.5,
    "camera_x": 3.8,
    "camera_y": -7.0,
    "camera_z": 4.2,
    "show_outline": True,
    "show_axes": True,
}

CAMERA_SLIDER_IDS = {"camera-x", "camera-y", "camera-z"}
THRESHOLD_RANGE = (0.001, 1.1)
SHELL_WIDTH_RANGE = (0.005, 0.5)
CAMERA_XY_RANGE = (-8.0, 8.0)
CAMERA_Z_RANGE = (-3.0, 6.0)


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def normalize_controls(controls: dict | None) -> dict:
    merged = dict(DEFAULT_CONTROLS)
    if controls:
        merged.update(controls)

    merged["threshold"] = round(clamp(float(merged["threshold"]), *THRESHOLD_RANGE), 3)
    merged["shell_width"] = round(clamp(float(merged["shell_width"]), *SHELL_WIDTH_RANGE), 3)
    merged["opacity"] = round(clamp(float(merged["opacity"]), 0.1, 1.0), 2)
    if merged["colorscale"] not in {"viridis", "plasma", "inferno", "jet", "turbo", "thermal"}:
        merged["colorscale"] = DEFAULT_CONTROLS["colorscale"]

    merged["light_x"] = round(clamp(float(merged["light_x"]), -5.0, 5.0), 2)
    merged["light_y"] = round(clamp(float(merged["light_y"]), -5.0, 5.0), 2)
    merged["light_z"] = round(clamp(float(merged["light_z"]), -3.0, 5.0), 2)

    merged["ambient"] = round(clamp(float(merged["ambient"]), 0.0, 1.0), 2)
    merged["diffuse"] = round(clamp(float(merged["diffuse"]), 0.0, 1.0), 2)
    merged["specular"] = round(clamp(float(merged["specular"]), 0.0, 2.0), 2)
    merged["roughness"] = round(clamp(float(merged["roughness"]), 0.0, 1.0), 2)

    merged["camera_x"] = round(clamp(float(merged["camera_x"]), *CAMERA_XY_RANGE), 2)
    merged["camera_y"] = round(clamp(float(merged["camera_y"]), *CAMERA_XY_RANGE), 2)
    merged["camera_z"] = round(clamp(float(merged["camera_z"]), *CAMERA_Z_RANGE), 2)
    merged["show_outline"] = bool(merged.get("show_outline", True))
    merged["show_axes"] = bool(merged.get("show_axes", True))
    return merged


# ---------------------------------------------------------------------------
# Data loading — parse ASCII OpenDX directly (no PyVista dependency)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _parse_watermolecule_dx(path_key: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, tuple[int, int, int]]:
    """Parse watermolecule.dx and return ``(x, y, z, value_3d, (nx, ny, nz))``.

    The raw DX file stores values in C-order (first grid index varies fastest).
    For Plotly ``go.Isosurface``, ``value[i, j, k]`` must correspond to
    ``(x[i], y[j], z[k])``, which requires a Fortran-ordered reshape.
    """
    path = Path(path_key)
    text = path.read_text(encoding="ascii")

    # --- grid metadata ---
    counts_match = re.search(r"gridpositions\s+counts\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)", text)
    if not counts_match:
        raise ValueError("Could not find gridpositions counts in watermolecule.dx")
    nx, ny, nz = int(counts_match.group(1)), int(counts_match.group(2)), int(counts_match.group(3))
    npoints = nx * ny * nz

    origin_match = re.search(r"origin\s+([^\n]+)", text)
    if not origin_match:
        raise ValueError("Could not find origin in watermolecule.dx")
    origin = tuple(float(v) for v in origin_match.group(1).split())

    delta_matches = re.findall(r"delta\s+([^\n]+)", text)
    if len(delta_matches) < 3:
        raise ValueError("Could not find deltas in watermolecule.dx")
    spacings = []
    for i, line in enumerate(delta_matches[:3]):
        vals = [float(v) for v in line.split()]
        spacings.append(vals[i])  # axis-aligned: non-zero on diagonal

    # --- scalar values ---
    start_marker = "data follows"
    start = text.index(start_marker) + len(start_marker)
    end_match = re.search(r'\n\s*attribute\s+"dep"', text[start:])
    if not end_match:
        raise ValueError("Could not find end of data array in watermolecule.dx")
    values_str = text[start : start + end_match.start()]
    raw_values = np.fromstring(values_str, sep=" ", dtype=float)

    if raw_values.size != npoints:
        raise ValueError(f"Expected {npoints} values, got {raw_values.size}")

    # OpenDX C-order → Plotly 3D: Fortran reshape so that
    # value_3d[i, j, k] = raw_values[i + j*nx + k*nx*ny]
    value_3d = raw_values.reshape((nx, ny, nz), order="F")

    x = np.linspace(origin[0], origin[0] + (nx - 1) * spacings[0], nx)
    y = np.linspace(origin[1], origin[1] + (ny - 1) * spacings[1], ny)
    z = np.linspace(origin[2], origin[2] + (nz - 1) * spacings[2], nz)

    return x, y, z, value_3d, (nx, ny, nz)


def _grid_bounds(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> dict:
    """Return the 8 corners and 12 edges of the grid bounding box."""
    x0, x1 = float(x[0]), float(x[-1])
    y0, y1 = float(y[0]), float(y[-1])
    z0, z1 = float(z[0]), float(z[-1])
    corners = [
        (x0, y0, z0), (x1, y0, z0), (x0, y1, z0), (x1, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x0, y1, z1), (x1, y1, z1),
    ]
    edges = [
        (0, 1), (0, 2), (1, 3), (2, 3),   # z=z0 face
        (4, 5), (4, 6), (5, 7), (6, 7),   # z=z1 face
        (0, 4), (1, 5), (2, 6), (3, 7),   # vertical
    ]
    return {"corners": corners, "edges": edges}


# ---------------------------------------------------------------------------
# Figure building
# ---------------------------------------------------------------------------


def make_edge_trace(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> go.Scatter3d:
    """Build a box-outline trace for the grid bounding box."""
    bounds = _grid_bounds(x, y, z)
    corners = bounds["corners"]
    edge_pairs = bounds["edges"]

    xs: list[float | None] = []
    ys: list[float | None] = []
    zs: list[float | None] = []
    for a, b in edge_pairs:
        xs.extend([corners[a][0], corners[b][0], None])
        ys.extend([corners[a][1], corners[b][1], None])
        zs.extend([corners[a][2], corners[b][2], None])

    return go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode="lines",
        name="grid outline",
        line={"color": "#111827", "width": 2},
        hoverinfo="skip",
        showlegend=False,
    )


def flatten_grid_for_plotly(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    value_3d: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return per-vertex 1D arrays required by ``go.Isosurface``."""
    xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")
    return xx.ravel(), yy.ravel(), zz.ravel(), value_3d.ravel()


def density_label(value: float) -> str:
    return f"{value:.4g}"


def surface_count_for_shell(shell_width: float) -> int:
    """Use more surfaces for wider density bands so the lower threshold remains visible."""
    return int(clamp(round(shell_width / 0.05) + 1, 2, 8))


def make_isosurface_figure(
    *,
    threshold: float,
    shell_width: float,
    opacity: float,
    colorscale: str,
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
    show_outline: bool,
    show_axes: bool,
    camera_override: dict | None = None,
) -> go.Figure:
    x, y, z, value_3d, _counts = _parse_watermolecule_dx(str(DATA_DIR / "watermolecule.dx"))
    x_flat, y_flat, z_flat, value_flat = flatten_grid_for_plotly(x, y, z, value_3d)

    isomin = threshold
    isomax = min(threshold + shell_width, float(value_3d.max()))
    surface_count = surface_count_for_shell(shell_width)
    traces: list[go.BaseTraceType] = [
        go.Isosurface(
            x=x_flat,
            y=y_flat,
            z=z_flat,
            value=value_flat,
            isomin=isomin,
            isomax=isomax,
            surface={"show": True, "count": surface_count},
            colorscale=colorscale,
            opacity=opacity,
            caps={"x": {"show": False}, "y": {"show": False}, "z": {"show": False}},
            slices={"x": {"show": False}, "y": {"show": False}, "z": {"show": False}},
            lighting={
                "ambient": ambient,
                "diffuse": diffuse,
                "specular": specular,
                "roughness": roughness,
            },
            lightposition={"x": light_x, "y": light_y, "z": light_z},
            colorbar={"title": "density"},
            hovertemplate=(
                "x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<br>"
                "density=%{value:.4f}<extra></extra>"
            ),
        )
    ]

    if show_outline:
        traces.append(make_edge_trace(x, y, z))

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

    camera = {
        "eye": {"x": camera_x, "y": camera_y, "z": camera_z},
        "center": {"x": 0, "y": 0, "z": 0},
    }
    if camera_override:
        for key in ("eye", "center", "up"):
            if key in camera_override:
                camera[key] = camera_override[key]

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=(
            "Water molecule electron density — "
            f"density band [{density_label(isomin)}, {density_label(isomax)}]"
        ),
        margin={"l": 0, "r": 0, "t": 46, "b": 0},
        uirevision="water-molecule",
        paper_bgcolor="#ffffff",
        scene={
            "xaxis": {**axis_style, "title": "x (Å)", "range": [-1.5, 3.5]},
            "yaxis": {**axis_style, "title": "y (Å)", "range": [-3.5, 3.5]},
            "zaxis": {**axis_style, "title": "z (Å)", "range": [-2.5, 0.5]},
            "aspectmode": "data",
            "camera": camera,
        },
    )
    return fig


def make_figure_from_controls(controls: dict, camera_override: dict | None = None) -> go.Figure:
    controls = normalize_controls(controls)
    return make_isosurface_figure(
        threshold=controls["threshold"],
        shell_width=controls["shell_width"],
        opacity=controls["opacity"],
        colorscale=controls["colorscale"],
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
        show_outline=controls["show_outline"],
        show_axes=controls["show_axes"],
        camera_override=camera_override,
    )


# ---------------------------------------------------------------------------
# Camera helpers (from template)
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
        parsed = {
            key: value
            for key in ("eye", "center", "up")
            if (value := numeric_xyz(camera.get(key))) is not None
        }
        if "eye" in parsed:
            return parsed

    eye = numeric_xyz(relayout_data.get("scene.camera.eye"))
    if eye is not None:
        return {"eye": eye}

    parsed = {}
    for part in ("eye", "center", "up"):
        value = numeric_xyz(
            {axis: relayout_data.get(f"scene.camera.{part}.{axis}") for axis in ("x", "y", "z")}
        )
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
    return all(
        abs(float(eye[axis]) - controls[f"camera_{axis}"]) <= tolerance for axis in ("x", "y", "z")
    )


# ---------------------------------------------------------------------------
# Dash UI
# ---------------------------------------------------------------------------


def slider(label: str, component_id: str, *, minimum: float, maximum: float, step: float, value: float, marks=None):
    return html.Div(
        [
            html.Label(label, style={"display": "block"}),
            dcc.Slider(
                id=component_id,
                min=minimum,
                max=maximum,
                step=step,
                value=value,
                marks=marks,
                updatemode="drag",
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ],
        style={"marginTop": "15px"},
    )


def stats_panel(controls: dict, density_range: tuple[float, float]) -> list:
    controls = normalize_controls(controls)
    _, _, _, _, counts = _parse_watermolecule_dx(str(DATA_DIR / "watermolecule.dx"))
    return [
        html.Div(f"Grid: {counts[0]} × {counts[1]} × {counts[2]}"),
        html.Div(f"Total points: {counts[0] * counts[1] * counts[2]:,}"),
        html.Div(
            f"Density range: [{density_label(density_range[0])}, {density_label(density_range[1])}]"
        ),
        html.Div(
            "Density band: "
            f"[{density_label(controls['threshold'])}, "
            f"{density_label(controls['threshold'] + controls['shell_width'])}]"
        ),
        html.Div(f"Surfaces: {surface_count_for_shell(controls['shell_width'])}"),
        html.Div(f"Opacity: {controls['opacity']:.2f}"),
        html.Div(
            f"Light: ({controls['light_x']:.1f}, {controls['light_y']:.1f}, {controls['light_z']:.1f})"
        ),
        html.Div(
            f"Camera: ({controls['camera_x']:.2f}, {controls['camera_y']:.2f}, {controls['camera_z']:.2f})"
        ),
    ]


def create_app() -> Dash:
    _parsed = _parse_watermolecule_dx(str(DATA_DIR / "watermolecule.dx"))
    value_3d = _parsed[3]
    density_range = (float(value_3d.min()), float(value_3d.max()))

    app = Dash(__name__)
    app.title = "Water Molecule Electron Density"
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.H2("Water Molecule"),
                    html.P("Electron density isosurface — OpenDX sample"),
                    html.H4("Isosurface 等值面"),
                    slider(
                        "Threshold 阈值",
                        "threshold",
                        minimum=THRESHOLD_RANGE[0],
                        maximum=THRESHOLD_RANGE[1],
                        step=0.001,
                        value=DEFAULT_CONTROLS["threshold"],
                        marks=THRESHOLD_MARKS,
                    ),
                    slider(
                        "Shell width 密度带宽",
                        "shell-width",
                        minimum=SHELL_WIDTH_RANGE[0],
                        maximum=SHELL_WIDTH_RANGE[1],
                        step=0.005,
                        value=DEFAULT_CONTROLS["shell_width"],
                        marks=SHELL_WIDTH_MARKS,
                    ),
                    slider("Opacity 透明度", "opacity", minimum=0.1, maximum=1.0, step=0.05, value=DEFAULT_CONTROLS["opacity"]),
                    html.Label("Colorscale 色阶", style={"marginTop": "15px", "display": "block"}),
                    dcc.Dropdown(
                        id="colorscale",
                        value=DEFAULT_CONTROLS["colorscale"],
                        clearable=False,
                        options=COLORSCALE_OPTIONS,
                    ),
                    html.Label("Display 显示", style={"marginTop": "18px", "display": "block"}),
                    dcc.Checklist(
                        id="display-options",
                        options=DISPLAY_OPTIONS,
                        value=["axes", "outline"],
                        inputStyle={"marginRight": "6px"},
                    ),
                    html.H4("Lighting 光源", style={"marginTop": "22px"}),
                    slider("Light X", "light-x", minimum=-5.0, maximum=5.0, step=0.25, value=DEFAULT_CONTROLS["light_x"]),
                    slider("Light Y", "light-y", minimum=-5.0, maximum=5.0, step=0.25, value=DEFAULT_CONTROLS["light_y"]),
                    slider("Light Z", "light-z", minimum=-3.0, maximum=5.0, step=0.25, value=DEFAULT_CONTROLS["light_z"]),
                    slider("Ambient 环境光", "ambient", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["ambient"]),
                    slider("Diffuse 漫反射", "diffuse", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["diffuse"]),
                    slider("Specular 镜面反射", "specular", minimum=0, maximum=2, step=0.05, value=DEFAULT_CONTROLS["specular"]),
                    slider("Roughness 粗糙度", "roughness", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["roughness"]),
                    html.H4("Camera 相机", style={"marginTop": "22px"}),
                    slider(
                        "Camera X",
                        "camera-x",
                        minimum=CAMERA_XY_RANGE[0],
                        maximum=CAMERA_XY_RANGE[1],
                        step=0.05,
                        value=DEFAULT_CONTROLS["camera_x"],
                    ),
                    slider(
                        "Camera Y",
                        "camera-y",
                        minimum=CAMERA_XY_RANGE[0],
                        maximum=CAMERA_XY_RANGE[1],
                        step=0.05,
                        value=DEFAULT_CONTROLS["camera_y"],
                    ),
                    slider(
                        "Camera Z",
                        "camera-z",
                        minimum=CAMERA_Z_RANGE[0],
                        maximum=CAMERA_Z_RANGE[1],
                        step=0.05,
                        value=DEFAULT_CONTROLS["camera_z"],
                    ),
                    html.Div(id="molecule-stats", style={"marginTop": "22px", "fontSize": "14px", "lineHeight": "1.5"}),
                ],
                style={
                    "boxSizing": "border-box",
                    "width": "360px",
                    "padding": "18px",
                    "borderRight": "1px solid #ddd",
                    "fontFamily": "Arial, sans-serif",
                    "overflowY": "auto",
                },
            ),
            html.Div(
                [
                    dcc.Graph(
                        id="molecule-graph",
                        config={"displaylogo": False, "scrollZoom": True},
                        style={"height": "calc(100vh - 24px)"},
                    )
                ],
                style={"flex": "1", "padding": "12px"},
            ),
        ],
        style={"display": "flex", "height": "100vh", "margin": "0"},
    )

    # --- Callback 1: main figure update ---

    @app.callback(
        Output("molecule-graph", "figure"),
        Output("molecule-stats", "children"),
        Input("threshold", "value"),
        Input("shell-width", "value"),
        Input("opacity", "value"),
        Input("colorscale", "value"),
        Input("display-options", "value"),
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
        State("molecule-graph", "relayoutData"),
    )
    def update_molecule(
        threshold,
        shell_width,
        opacity,
        colorscale,
        display_options,
        light_x,
        light_y,
        light_z,
        ambient,
        diffuse,
        specular,
        roughness,
        camera_x,
        camera_y,
        camera_z,
        relayout_data,
    ):
        controls = normalize_controls(
            {
                "threshold": threshold,
                "shell_width": shell_width,
                "opacity": opacity,
                "colorscale": colorscale,
                "show_outline": "outline" in (display_options or []),
                "show_axes": "axes" in (display_options or []),
                "light_x": light_x,
                "light_y": light_y,
                "light_z": light_z,
                "ambient": ambient,
                "diffuse": diffuse,
                "specular": specular,
                "roughness": roughness,
                "camera_x": camera_x,
                "camera_y": camera_y,
                "camera_z": camera_z,
            }
        )
        relayout_camera = camera_from_relayout(relayout_data)
        if ctx.triggered_id in CAMERA_SLIDER_IDS and camera_eye_matches_controls(relayout_camera, controls):
            return no_update, stats_panel(controls, density_range)

        camera_override = None
        if should_preserve_user_camera(ctx.triggered_id):
            camera_override = relayout_camera
        return make_figure_from_controls(controls, camera_override), stats_panel(controls, density_range)

    # --- Callback 2: sync camera sliders when user drags the graph ---

    @app.callback(
        Output("camera-x", "value"),
        Output("camera-y", "value"),
        Output("camera-z", "value"),
        Input("molecule-graph", "relayoutData"),
        prevent_initial_call=True,
    )
    def sync_camera_sliders(relayout_data):
        camera = camera_from_relayout(relayout_data)
        if not camera or "eye" not in camera:
            return no_update, no_update, no_update
        eye = camera["eye"]
        controls = normalize_controls(
            {"camera_x": eye["x"], "camera_y": eye["y"], "camera_z": eye["z"]}
        )
        return controls["camera_x"], controls["camera_y"], controls["camera_z"]

    return app


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8053)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--check", action="store_true", help="Build the default figure and exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        x, y, z, value_3d, counts = _parse_watermolecule_dx(str(DATA_DIR / "watermolecule.dx"))
        print(f"Grid: {counts[0]} × {counts[1]} × {counts[2]}")
        print(f"Total points: {counts[0] * counts[1] * counts[2]:,}")
        print(f"Value range: [{value_3d.min():.6f}, {value_3d.max():.6f}]")
        print(f"Volume shape: {value_3d.shape}")
        print(f"X range: [{x[0]:.2f}, {x[-1]:.2f}], spacing={x[1]-x[0]:.2f}")
        print(f"Y range: [{y[0]:.2f}, {y[-1]:.2f}], spacing={y[1]-y[0]:.2f}")
        print(f"Z range: [{z[0]:.2f}, {z[-1]:.2f}], spacing={z[1]-z[0]:.2f}")

        fig = make_figure_from_controls(DEFAULT_CONTROLS)
        iso_count = sum(1 for trace in fig.data if getattr(trace, "type", "") == "isosurface")
        scatter_count = sum(1 for trace in fig.data if getattr(trace, "type", "") == "scatter3d")
        print(f"Traces: {len(fig.data)} ({iso_count} isosurface, {scatter_count} outline)")
        print(f"Figure JSON length: {len(fig.to_json())}")
        return

    app = create_app()
    url = f"http://{args.host}:{args.port}"
    print(f"Dash app running at {url}")
    if hasattr(app, "run"):
        app.run(host=args.host, port=args.port, debug=args.debug)
    else:
        app.run_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
