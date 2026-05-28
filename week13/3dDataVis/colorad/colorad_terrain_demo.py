#!/usr/bin/env python3
"""Dash + Plotly Colorado terrain viewer.

Based on ``basic_3d/plotly_unit_cube_demo.py`` as a template, adapted to display
the OpenDX Colorado terrain sample (elevation + aerial photo).

Run from the repository root::

    conda activate ai4math-vis
    python colorad/colorad_terrain_demo.py

Then open http://127.0.0.1:8052 in a browser.
"""

from __future__ import annotations

import argparse
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from PIL import Image


DATA_DIR = Path(__file__).resolve().parent

STRIDE_OPTIONS = (1, 2, 4, 5, 8)

DEFAULT_CONTROLS = {
    "z_scale": 2.0,
    "stride": 4,
    "color_mode": "image_gray",
    "light_x": 1000.0,
    "light_y": -1000.0,
    "light_z": 1500.0,
    "ambient": 0.35,
    "diffuse": 0.8,
    "specular": 0.25,
    "roughness": 0.7,
    "camera_x": 1.45,
    "camera_y": -1.55,
    "camera_z": 0.85,
    "show_axes": True,
}

COLOR_MODE_OPTIONS = [
    {"label": "Image luminance 影像灰度", "value": "image_gray"},
    {"label": "Elevation colormap 高程色图", "value": "elevation"},
]

CAMERA_SLIDER_IDS = {"camera-x", "camera-y", "camera-z"}


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def nearest_stride(value: int) -> int:
    return min(STRIDE_OPTIONS, key=lambda option: abs(option - int(value)))


def normalize_controls(controls: dict | None) -> dict:
    merged = dict(DEFAULT_CONTROLS)
    if controls:
        merged.update(controls)

    merged["z_scale"] = round(clamp(float(merged["z_scale"]), 0.5, 6.0), 2)
    merged["stride"] = nearest_stride(int(merged["stride"]))
    if merged["color_mode"] not in {"image_gray", "elevation"}:
        merged["color_mode"] = DEFAULT_CONTROLS["color_mode"]

    merged["light_x"] = round(clamp(float(merged["light_x"]), -3000.0, 3000.0), 1)
    merged["light_y"] = round(clamp(float(merged["light_y"]), -3000.0, 3000.0), 1)
    merged["light_z"] = round(clamp(float(merged["light_z"]), 100.0, 4000.0), 1)

    merged["ambient"] = round(clamp(float(merged["ambient"]), 0.0, 1.0), 2)
    merged["diffuse"] = round(clamp(float(merged["diffuse"]), 0.0, 1.0), 2)
    merged["specular"] = round(clamp(float(merged["specular"]), 0.0, 2.0), 2)
    merged["roughness"] = round(clamp(float(merged["roughness"]), 0.0, 1.0), 2)

    merged["camera_x"] = round(clamp(float(merged["camera_x"]), -4.0, 4.0), 2)
    merged["camera_y"] = round(clamp(float(merged["camera_y"]), -4.0, 4.0), 2)
    merged["camera_z"] = round(clamp(float(merged["camera_z"]), 0.2, 4.0), 2)
    merged["show_axes"] = bool(merged.get("show_axes", True))
    return merged


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _read_general(path: Path) -> dict[str, str]:
    """Parse a minimal OpenDX .general header file."""
    metadata: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def _grid_counts(value: str) -> tuple[int, int]:
    counts = tuple(int(item) for item in re.split(r"\s*x\s*", value.replace(" ", "")) if item)
    if len(counts) != 2:
        raise ValueError(f"Expected a 2D grid, got {value!r}")
    return counts


@lru_cache(maxsize=4)
def _load_full_arrays(data_dir_key: str) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """Load full-resolution elevation and RGB image arrays.

    Returns ``(elevation, image, (nx, ny))``.  Cached so callbacks never re-read files.
    """
    data_dir = Path(data_dir_key)
    metadata = _read_general(data_dir / "colo_elev.general")
    counts = _grid_counts(metadata["grid"])

    header_match = re.search(r"bytes\s+([0-9]+)", metadata.get("header", "bytes 0"))
    header_bytes = int(header_match.group(1)) if header_match else 0

    raw = np.fromfile(data_dir / metadata["file"], dtype=np.uint8)
    expected = int(np.prod(counts))
    elevation = raw[header_bytes : header_bytes + expected].reshape(counts, order="C")

    image = np.asarray(Image.open(data_dir / "colorado.tiff").convert("RGB"))
    if image.shape[:2] != elevation.shape:
        image = np.asarray(Image.fromarray(image).resize((elevation.shape[1], elevation.shape[0])))

    return elevation, image, counts


# ---------------------------------------------------------------------------
# Figure building
# ---------------------------------------------------------------------------


def build_surface(
    elevation: np.ndarray,
    image: np.ndarray,
    *,
    z_scale: float,
    stride: int,
    color_mode: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, str, bool]:
    """Sample the terrain arrays and return surface data arrays."""
    if stride not in STRIDE_OPTIONS:
        raise ValueError(f"Unsupported stride {stride}")

    elev = elevation[::stride, ::stride].astype(float)
    img = image[::stride, ::stride].astype(float)
    x, y = np.meshgrid(
        np.arange(elev.shape[0]) * stride,
        np.arange(elev.shape[1]) * stride,
        indexing="ij",
    )
    z = elev * z_scale

    if color_mode == "image_gray":
        color = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
        return x, y, z, color, "gray", False
    if color_mode == "elevation":
        return x, y, z, elev, "Earth", True
    raise ValueError(f"Unknown color mode: {color_mode}")


def make_terrain_figure(
    elevation: np.ndarray,
    image: np.ndarray,
    *,
    z_scale: float,
    stride: int,
    color_mode: str,
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
    camera_override: dict | None = None,
) -> go.Figure:
    x, y, z, surface_color, colorscale, showscale = build_surface(
        elevation, image, z_scale=z_scale, stride=stride, color_mode=color_mode,
    )

    color_title = "image luminance" if color_mode == "image_gray" else "elevation"
    fig = go.Figure(
        data=[
            go.Surface(
                x=x,
                y=y,
                z=z,
                surfacecolor=surface_color,
                colorscale=colorscale,
                showscale=showscale,
                colorbar={"title": color_title} if showscale else None,
                lighting={
                    "ambient": ambient,
                    "diffuse": diffuse,
                    "specular": specular,
                    "roughness": roughness,
                },
                lightposition={"x": light_x, "y": light_y, "z": light_z},
                hovertemplate=(
                    "x=%{x}<br>y=%{y}<br>"
                    "height=%{z:.1f}<br>"
                    f"{color_title}=%{{surfacecolor:.1f}}<extra></extra>"
                ),
            )
        ]
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

    z_aspect = min(1.2, max(0.18, 0.18 * z_scale))
    camera: dict = {
        "eye": {"x": camera_x, "y": camera_y, "z": camera_z},
        "center": {"x": 0, "y": 0, "z": 0},
    }
    if camera_override:
        for key in ("eye", "center", "up"):
            if key in camera_override:
                camera[key] = camera_override[key]

    fig.update_layout(
        title=f"Colorado terrain — height scale = {z_scale:g}, stride = {stride}",
        margin={"l": 0, "r": 0, "t": 46, "b": 0},
        uirevision="colorado-terrain",
        paper_bgcolor="#ffffff",
        scene={
            "xaxis": {**axis_style, "title": "x"},
            "yaxis": {**axis_style, "title": "y"},
            "zaxis": {**axis_style, "title": "elevation"},
            "aspectmode": "manual",
            "aspectratio": {"x": 1.0, "y": 1.0, "z": z_aspect},
            "camera": camera,
        },
    )
    return fig


def make_figure_from_controls(
    elevation: np.ndarray, image: np.ndarray, controls: dict, camera_override: dict | None = None
) -> go.Figure:
    controls = normalize_controls(controls)
    return make_terrain_figure(
        elevation,
        image,
        z_scale=controls["z_scale"],
        stride=controls["stride"],
        color_mode=controls["color_mode"],
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
        camera_override=camera_override,
    )


# ---------------------------------------------------------------------------
# Camera helpers (mirror the template's bidirectional sync pattern)
# ---------------------------------------------------------------------------


def numeric_xyz(source: dict | None) -> dict | None:
    if not isinstance(source, dict):
        return None
    try:
        return {axis: float(source[axis]) for axis in ("x", "y", "z")}
    except (KeyError, TypeError, ValueError):
        return None


def camera_from_relayout(relayout_data: dict | None) -> dict | None:
    """Extract the current Plotly camera from a graph relayout event."""
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


def terrain_stats(elevation: np.ndarray, image: np.ndarray, controls: dict) -> list:
    controls = normalize_controls(controls)
    sampled_shape = elevation[:: controls["stride"], :: controls["stride"]].shape
    return [
        html.Div(f"Source grid: {elevation.shape[0]} x {elevation.shape[1]}"),
        html.Div(f"Displayed grid: {sampled_shape[0]} x {sampled_shape[1]}"),
        html.Div(f"Surface vertices: {sampled_shape[0] * sampled_shape[1]:,}"),
        html.Div(f"Height scale: {controls['z_scale']:.1f}"),
        html.Div(
            f"Light: ({controls['light_x']:.0f}, {controls['light_y']:.0f}, {controls['light_z']:.0f})"
        ),
        html.Div(
            f"Camera: ({controls['camera_x']:.2f}, {controls['camera_y']:.2f}, {controls['camera_z']:.2f})"
        ),
        html.Div(
            f"Material: A {controls['ambient']:.2f}, D {controls['diffuse']:.2f}, "
            f"S {controls['specular']:.2f}, R {controls['roughness']:.2f}"
        ),
        html.Div("Stride 1 uses full 400×400 resolution and may be slow.", style={"marginTop": "8px"}),
    ]


def create_app() -> Dash:
    elevation, image, _counts = _load_full_arrays(str(DATA_DIR.resolve()))

    app = Dash(__name__)
    app.title = "Colorado Terrain"
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.H2("Colorado Terrain"),
                    html.H4("Data"),
                    slider(
                        "Height scale 高度缩放",
                        "z-scale",
                        minimum=0.5,
                        maximum=6.0,
                        step=0.5,
                        value=DEFAULT_CONTROLS["z_scale"],
                        marks={value: str(value) for value in [0.5, 2.0, 4.0, 6.0]},
                    ),
                    html.Label("Sampling stride 采样步长", style={"marginTop": "15px", "display": "block"}),
                    dcc.Slider(
                        id="stride",
                        min=min(STRIDE_OPTIONS),
                        max=max(STRIDE_OPTIONS),
                        step=None,
                        value=DEFAULT_CONTROLS["stride"],
                        marks={value: str(value) for value in STRIDE_OPTIONS},
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                    html.Label("Color mode 颜色模式", style={"marginTop": "15px", "display": "block"}),
                    dcc.Dropdown(
                        id="color-mode",
                        value=DEFAULT_CONTROLS["color_mode"],
                        clearable=False,
                        options=COLOR_MODE_OPTIONS,
                    ),
                    html.Label("Display 显示", style={"marginTop": "18px", "display": "block"}),
                    dcc.Checklist(
                        id="show-axes",
                        options=[{"label": "Axes 坐标轴", "value": "axes"}],
                        value=["axes"] if DEFAULT_CONTROLS["show_axes"] else [],
                        inputStyle={"marginRight": "6px"},
                    ),
                    html.H4("Lighting 光源", style={"marginTop": "22px"}),
                    slider("Light X", "light-x", minimum=-3000, maximum=3000, step=250, value=DEFAULT_CONTROLS["light_x"]),
                    slider("Light Y", "light-y", minimum=-3000, maximum=3000, step=250, value=DEFAULT_CONTROLS["light_y"]),
                    slider("Light Z", "light-z", minimum=100, maximum=4000, step=250, value=DEFAULT_CONTROLS["light_z"]),
                    slider("Ambient 环境光", "ambient", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["ambient"]),
                    slider("Diffuse 漫反射", "diffuse", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["diffuse"]),
                    slider("Specular 镜面反射", "specular", minimum=0, maximum=2, step=0.05, value=DEFAULT_CONTROLS["specular"]),
                    slider("Roughness 粗糙度", "roughness", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["roughness"]),
                    html.H4("Camera 相机", style={"marginTop": "22px"}),
                    slider("Camera X", "camera-x", minimum=-4, maximum=4, step=0.05, value=DEFAULT_CONTROLS["camera_x"]),
                    slider("Camera Y", "camera-y", minimum=-4, maximum=4, step=0.05, value=DEFAULT_CONTROLS["camera_y"]),
                    slider("Camera Z", "camera-z", minimum=0.2, maximum=4, step=0.05, value=DEFAULT_CONTROLS["camera_z"]),
                    html.Div(id="terrain-stats", style={"marginTop": "22px", "fontSize": "14px", "lineHeight": "1.5"}),
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
                        id="terrain-graph",
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
        Output("terrain-graph", "figure"),
        Output("terrain-stats", "children"),
        Input("z-scale", "value"),
        Input("stride", "value"),
        Input("color-mode", "value"),
        Input("show-axes", "value"),
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
        State("terrain-graph", "relayoutData"),
    )
    def update_terrain(
        z_scale,
        stride,
        color_mode,
        show_axes,
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
                "z_scale": z_scale,
                "stride": stride,
                "color_mode": color_mode,
                "show_axes": "axes" in (show_axes or []),
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
            return no_update, terrain_stats(elevation, image, controls)

        camera_override = None
        if should_preserve_user_camera(ctx.triggered_id):
            camera_override = relayout_camera
        return (
            make_figure_from_controls(elevation, image, controls, camera_override),
            terrain_stats(elevation, image, controls),
        )

    # --- Callback 2: sync camera sliders when user drags the graph ---

    @app.callback(
        Output("camera-x", "value"),
        Output("camera-y", "value"),
        Output("camera-z", "value"),
        Input("terrain-graph", "relayoutData"),
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
    parser.add_argument("--port", type=int, default=8052)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--check", action="store_true", help="Build the default figure and exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        elevation, image, counts = _load_full_arrays(str(DATA_DIR.resolve()))
        fig = make_figure_from_controls(elevation, image, DEFAULT_CONTROLS)
        print(f"Grid: {counts[0]} x {counts[1]}")
        print(f"Elevation range: [{elevation.min()}, {elevation.max()}]")
        print(f"Image shape: {image.shape}")
        print(f"Default figure traces: {len(fig.data)}")
        print(f"Default figure JSON length: {len(fig.to_json())}")
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
