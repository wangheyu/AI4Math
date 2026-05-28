#!/usr/bin/env python3
"""Dash + Plotly app for the OpenDX Colorado terrain sample.

Run from the repository root or from ``week13``:

    conda activate ai4math-vis
    python week13/opendx_colorado_dash.py

Then open http://127.0.0.1:8050 in a browser.
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


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = APP_DIR / "opendx_data"
STRIDE_OPTIONS = (1, 2, 4, 5, 8)
DEFAULT_CONTROLS = {
    "z_scale": 2.0,
    "stride": 2,
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
    "show_help": True,
}


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def nearest_stride(value: int) -> int:
    return min(STRIDE_OPTIONS, key=lambda option: abs(option - int(value)))


def normalize_controls(controls: dict | None) -> dict:
    """Fill missing controls and enforce display-safe ranges."""
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
    merged["show_help"] = bool(merged.get("show_help", True))
    return merged


def apply_key_event(controls: dict, key_event: dict | None) -> dict:
    """Apply one keyboard event to the controls dictionary."""
    updated = normalize_controls(controls)
    if not key_event:
        return updated

    key = str(key_event.get("key", ""))
    if key == "[":
        updated["z_scale"] -= 0.5
    elif key == "]":
        updated["z_scale"] += 0.5
    elif key in {"1", "2", "4", "5", "8"}:
        updated["stride"] = int(key)
    elif key.lower() == "c":
        updated["color_mode"] = "elevation" if updated["color_mode"] == "image_gray" else "image_gray"
    elif key.lower() == "a":
        updated["light_x"] -= 250.0
    elif key.lower() == "d":
        updated["light_x"] += 250.0
    elif key.lower() == "w":
        updated["light_y"] += 250.0
    elif key.lower() == "s":
        updated["light_y"] -= 250.0
    elif key.lower() == "q":
        updated["light_z"] -= 250.0
    elif key.lower() == "e":
        updated["light_z"] += 250.0
    elif key == "ArrowLeft":
        updated["camera_x"] -= 0.15
    elif key == "ArrowRight":
        updated["camera_x"] += 0.15
    elif key == "ArrowUp":
        updated["camera_y"] += 0.15
    elif key == "ArrowDown":
        updated["camera_y"] -= 0.15
    elif key == "PageUp":
        updated["camera_z"] += 0.15
    elif key == "PageDown":
        updated["camera_z"] -= 0.15
    elif key.lower() == "h":
        updated["show_help"] = not updated["show_help"]
    elif key.lower() == "r":
        updated = dict(DEFAULT_CONTROLS)

    updated["last_key"] = key
    return normalize_controls(updated)


def read_general_header(path: Path) -> dict[str, str]:
    """Read the small OpenDX general importer header used by this sample."""
    metadata: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def grid_counts(value: str) -> tuple[int, int]:
    """Parse OpenDX grid syntax such as ``400 x 400``."""
    counts = tuple(int(item) for item in re.split(r"\s*x\s*", value.replace(" ", "")) if item)
    if len(counts) != 2:
        raise ValueError(f"Expected a 2D grid, got {value!r}")
    return counts


@lru_cache(maxsize=4)
def load_colorado_arrays(data_dir_text: str) -> tuple[np.ndarray, np.ndarray]:
    """Load full-resolution elevation and RGB image arrays."""
    data_dir = Path(data_dir_text)
    metadata = read_general_header(data_dir / "colo_elev.general")
    counts = grid_counts(metadata["grid"])

    header_match = re.search(r"bytes\s+([0-9]+)", metadata.get("header", "bytes 0"))
    header_bytes = int(header_match.group(1)) if header_match else 0

    raw = np.fromfile(data_dir / metadata["file"], dtype=np.uint8)
    expected = int(np.prod(counts))
    elevation = raw[header_bytes : header_bytes + expected].reshape(counts, order="C")

    image = np.asarray(Image.open(data_dir / "colorado.tiff").convert("RGB"))
    if image.shape[:2] != elevation.shape:
        resized = Image.fromarray(image).resize((elevation.shape[1], elevation.shape[0]))
        image = np.asarray(resized)

    return elevation, image


def sampled_surface_arrays(
    elevation: np.ndarray,
    image: np.ndarray,
    *,
    z_scale: float,
    stride: int,
    color_mode: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, str, bool]:
    """Convert full arrays to Plotly surface arrays."""
    if stride not in STRIDE_OPTIONS:
        raise ValueError(f"Unsupported stride {stride}; choose one of {STRIDE_OPTIONS}")

    elevation_sample = elevation[::stride, ::stride].astype(float)
    image_sample = image[::stride, ::stride].astype(float)
    x, y = np.meshgrid(
        np.arange(elevation_sample.shape[0]) * stride,
        np.arange(elevation_sample.shape[1]) * stride,
        indexing="ij",
    )
    z = elevation_sample * z_scale

    if color_mode == "image_gray":
        color = 0.299 * image_sample[:, :, 0] + 0.587 * image_sample[:, :, 1] + 0.114 * image_sample[:, :, 2]
        return x, y, z, color, "gray", False
    if color_mode == "elevation":
        return x, y, z, elevation_sample, "Earth", True
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
) -> go.Figure:
    """Build a Plotly 3D terrain figure."""
    x, y, z, surface_color, colorscale, showscale = sampled_surface_arrays(
        elevation,
        image,
        z_scale=z_scale,
        stride=stride,
        color_mode=color_mode,
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
                colorbar={"title": color_title},
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

    z_aspect = min(1.2, max(0.18, 0.18 * z_scale))
    fig.update_layout(
        title=f"Colorado terrain, height scale = {z_scale:g}, stride = {stride}",
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
        uirevision="colorado-terrain",
        scene={
            "xaxis_title": "x grid index",
            "yaxis_title": "y grid index",
            "zaxis_title": "scaled elevation",
            "aspectmode": "manual",
            "aspectratio": {"x": 1.0, "y": 1.0, "z": z_aspect},
            "camera": {"eye": {"x": camera_x, "y": camera_y, "z": camera_z}},
        },
    )
    return fig


def make_figure_from_controls(elevation: np.ndarray, image: np.ndarray, controls: dict) -> go.Figure:
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
    )


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
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ],
        style={"marginTop": "16px"},
    )


def shortcuts_panel_style(show_help: bool) -> dict:
    base = {
        "marginTop": "18px",
        "fontSize": "13px",
        "lineHeight": "1.45",
        "background": "#f7f7f7",
        "border": "1px solid #ddd",
        "padding": "10px",
    }
    if not show_help:
        base["display"] = "none"
    return base


def control_stats(elevation: np.ndarray, controls: dict) -> list:
    controls = normalize_controls(controls)
    sampled_shape = elevation[:: controls["stride"], :: controls["stride"]].shape
    return [
        html.Div(f"Source grid: {elevation.shape[0]} x {elevation.shape[1]}"),
        html.Div(f"Displayed grid: {sampled_shape[0]} x {sampled_shape[1]}"),
        html.Div(f"Surface vertices: {sampled_shape[0] * sampled_shape[1]:,}"),
        html.Div(
            "Light: "
            f"({controls['light_x']:.0f}, {controls['light_y']:.0f}, {controls['light_z']:.0f})"
        ),
        html.Div(
            "Camera: "
            f"({controls['camera_x']:.2f}, {controls['camera_y']:.2f}, {controls['camera_z']:.2f})"
        ),
        html.Div(f"Last key: {controls.get('last_key', '-')}", style={"marginTop": "8px"}),
        html.Div("Stride 1 uses the original 400 x 400 resolution and may be slower."),
    ]


def create_app(data_dir: Path = DEFAULT_DATA_DIR) -> Dash:
    """Create the Dash application."""
    data_dir = data_dir.resolve()
    elevation, image = load_colorado_arrays(str(data_dir))

    app = Dash(__name__)
    app.title = "Colorado Terrain"
    app.layout = html.Div(
        [
            dcc.Store(id="terrain-controls", data=DEFAULT_CONTROLS),
            dcc.Store(id="key-event"),
            dcc.Interval(id="key-poll", interval=120, n_intervals=0),
            html.Div(
                [
                    html.H2("Colorado Terrain"),
                    html.P("OpenDX sample: colorado.tiff + colorado_elev.vit"),
                    html.H4("Data"),
                    slider(
                        "Height scale",
                        "z-scale",
                        minimum=0.5,
                        maximum=6.0,
                        step=0.5,
                        value=DEFAULT_CONTROLS["z_scale"],
                        marks={value: str(value) for value in [0.5, 2.0, 4.0, 6.0]},
                    ),
                    html.Label("Sampling stride", style={"marginTop": "16px", "display": "block"}),
                    dcc.Slider(
                        id="stride",
                        min=min(STRIDE_OPTIONS),
                        max=max(STRIDE_OPTIONS),
                        step=None,
                        value=DEFAULT_CONTROLS["stride"],
                        marks={value: str(value) for value in STRIDE_OPTIONS},
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                    html.Label("Color mode", style={"marginTop": "16px", "display": "block"}),
                    dcc.Dropdown(
                        id="color-mode",
                        value=DEFAULT_CONTROLS["color_mode"],
                        clearable=False,
                        options=[
                            {"label": "Image luminance", "value": "image_gray"},
                            {"label": "Elevation colormap", "value": "elevation"},
                        ],
                    ),
                    html.H4("Lighting", style={"marginTop": "22px"}),
                    slider("Light X", "light-x", minimum=-3000, maximum=3000, step=250, value=DEFAULT_CONTROLS["light_x"]),
                    slider("Light Y", "light-y", minimum=-3000, maximum=3000, step=250, value=DEFAULT_CONTROLS["light_y"]),
                    slider("Light Z", "light-z", minimum=100, maximum=4000, step=250, value=DEFAULT_CONTROLS["light_z"]),
                    slider("Ambient", "ambient", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["ambient"]),
                    slider("Diffuse", "diffuse", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["diffuse"]),
                    slider("Specular", "specular", minimum=0, maximum=2, step=0.05, value=DEFAULT_CONTROLS["specular"]),
                    slider("Roughness", "roughness", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["roughness"]),
                    html.H4("Camera", style={"marginTop": "22px"}),
                    slider("Camera X", "camera-x", minimum=-4, maximum=4, step=0.05, value=DEFAULT_CONTROLS["camera_x"]),
                    slider("Camera Y", "camera-y", minimum=-4, maximum=4, step=0.05, value=DEFAULT_CONTROLS["camera_y"]),
                    slider("Camera Z", "camera-z", minimum=0.2, maximum=4, step=0.05, value=DEFAULT_CONTROLS["camera_z"]),
                    html.Div(
                        [
                            html.Strong("Keyboard shortcuts"),
                            html.Div("[ / ] height"),
                            html.Div("1 2 4 5 8 stride"),
                            html.Div("c color, r reset, h help"),
                            html.Div("w/a/s/d/q/e light"),
                            html.Div("arrows + PageUp/PageDown camera"),
                        ],
                        id="shortcuts-panel",
                        style=shortcuts_panel_style(True),
                    ),
                    html.Div(id="terrain-stats", style={"marginTop": "22px", "fontSize": "14px", "lineHeight": "1.5"}),
                ],
                style={
                    "boxSizing": "border-box",
                    "width": "350px",
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

    app.clientside_callback(
        """
        function(n_intervals, current) {
            const event = window.coloradoTerrainLastKey;
            if (!event) {
                return window.dash_clientside.no_update;
            }
            if (current && current.ts === event.ts) {
                return window.dash_clientside.no_update;
            }
            return event;
        }
        """,
        Output("key-event", "data"),
        Input("key-poll", "n_intervals"),
        State("key-event", "data"),
    )

    @app.callback(
        Output("terrain-controls", "data"),
        Input("z-scale", "value"),
        Input("stride", "value"),
        Input("color-mode", "value"),
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
        Input("key-event", "data"),
        State("terrain-controls", "data"),
    )
    def sync_controls(
        z_scale,
        stride,
        color_mode,
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
        key_event,
        current_controls,
    ):
        current = normalize_controls(current_controls)
        if ctx.triggered_id == "key-event":
            updated = apply_key_event(current, key_event)
        else:
            updated = normalize_controls(
                {
                    **current,
                    "z_scale": z_scale,
                    "stride": stride,
                    "color_mode": color_mode,
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
        if updated == current:
            return no_update
        return updated

    @app.callback(
        Output("terrain-graph", "figure"),
        Output("terrain-stats", "children"),
        Output("z-scale", "value"),
        Output("stride", "value"),
        Output("color-mode", "value"),
        Output("light-x", "value"),
        Output("light-y", "value"),
        Output("light-z", "value"),
        Output("ambient", "value"),
        Output("diffuse", "value"),
        Output("specular", "value"),
        Output("roughness", "value"),
        Output("camera-x", "value"),
        Output("camera-y", "value"),
        Output("camera-z", "value"),
        Output("shortcuts-panel", "style"),
        Input("terrain-controls", "data"),
    )
    def update_terrain(controls):
        controls = normalize_controls(controls)
        fig = make_figure_from_controls(elevation, image, controls)
        return (
            fig,
            control_stats(elevation, controls),
            controls["z_scale"],
            controls["stride"],
            controls["color_mode"],
            controls["light_x"],
            controls["light_y"],
            controls["light_z"],
            controls["ambient"],
            controls["diffuse"],
            controls["specular"],
            controls["roughness"],
            controls["camera_x"],
            controls["camera_y"],
            controls["camera_z"],
            shortcuts_panel_style(controls["show_help"]),
        )

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--check", action="store_true", help="Build a default figure and exit without starting Dash.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        elevation, image = load_colorado_arrays(str(args.data_dir.resolve()))
        fig = make_figure_from_controls(elevation, image, DEFAULT_CONTROLS)
        print(f"Loaded elevation: {elevation.shape}")
        print(f"Loaded image: {image.shape}")
        print(f"Default figure traces: {len(fig.data)}")
        print(f"Default figure JSON length: {len(fig.to_json())}")
        return

    app = create_app(args.data_dir)
    url = f"http://{args.host}:{args.port}"
    print(f"Dash app running at {url}")
    if hasattr(app, "run"):
        app.run(host=args.host, port=args.port, debug=args.debug)
    else:
        app.run_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
