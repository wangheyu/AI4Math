#!/usr/bin/env python3
"""Dash + Plotly MRI medical image viewer.

Displays the OpenDX MRI sample (128×128×16, uint16) using ``go.Volume`` with
orthogonal slice planes and adjustable window/level.

Run from the repository root::

    conda activate ai4math-vis
    python medical_mri/mri_demo.py

Then open http://127.0.0.1:8055 in a browser.
"""

from __future__ import annotations

import argparse
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update


DATA_DIR = Path(__file__).resolve().parent

GRID_SHAPE = (128, 128, 16)
DEFAULT_WINDOW_CENTER = 10000.0
DEFAULT_WINDOW_WIDTH = 18000.0
DEFAULT_OPACITY = 0.3
DEFAULT_SLICE_X = GRID_SHAPE[0] // 2
DEFAULT_SLICE_Y = GRID_SHAPE[1] // 2
DEFAULT_SLICE_Z = GRID_SHAPE[2] // 2

DEFAULT_CONTROLS = {
    "window_center": DEFAULT_WINDOW_CENTER,
    "window_width": DEFAULT_WINDOW_WIDTH,
    "opacity": DEFAULT_OPACITY,
    "slice_x": DEFAULT_SLICE_X,
    "slice_y": DEFAULT_SLICE_Y,
    "slice_z": DEFAULT_SLICE_Z,
    "show_volume": True,
    "show_slices": True,
    "camera_x": 1.8,
    "camera_y": -2.0,
    "camera_z": 1.2,
    "show_axes": True,
}

CAMERA_SLIDER_IDS = {"camera-x", "camera-y", "camera-z"}


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def normalize_controls(controls: dict | None) -> dict:
    merged = dict(DEFAULT_CONTROLS)
    if controls:
        merged.update(controls)
    merged["window_center"] = round(clamp(float(merged["window_center"]), 500.0, 60000.0), 0)
    merged["window_width"] = round(clamp(float(merged["window_width"]), 1000.0, 60000.0), 0)
    merged["opacity"] = round(clamp(float(merged["opacity"]), 0.01, 1.0), 3)
    merged["slice_x"] = int(clamp(float(merged["slice_x"]), 0, GRID_SHAPE[0] - 1))
    merged["slice_y"] = int(clamp(float(merged["slice_y"]), 0, GRID_SHAPE[1] - 1))
    merged["slice_z"] = int(clamp(float(merged["slice_z"]), 0, GRID_SHAPE[2] - 1))
    for key in ("camera_x", "camera_y"):
        merged[key] = round(clamp(float(merged[key]), -6.0, 6.0), 2)
    merged["camera_z"] = round(clamp(float(merged["camera_z"]), 0.2, 6.0), 2)
    for key in ("show_volume", "show_slices", "show_axes"):
        merged[key] = bool(merged.get(key, True))
    return merged


# ---------------------------------------------------------------------------
# MRI data loading
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_mri() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """Load MRI data. Returns (x, y, z, volume_3d, metadata)."""
    data_dir = DATA_DIR
    metadata = {}
    for line in (data_dir / "mri.general").read_text().splitlines():
        s = line.split("#")[0].strip()
        if s and "=" in s:
            k, v = s.split("=", 1)
            metadata[k.strip()] = v.strip()

    counts_match = re.split(r"\s*x\s*", metadata["grid"].replace(" ", ""))
    nx, ny, nz = int(counts_match[0]), int(counts_match[1]), int(counts_match[2])

    positions = [float(x.strip()) for x in metadata["positions"].split(",")]
    x_origin, x_spacing = positions[0], positions[1]
    y_origin, y_spacing = positions[2], positions[3]
    z_origin, z_spacing = positions[4], positions[5]

    raw = np.fromfile(data_dir / metadata["file"], dtype=">u2", count=nx * ny * nz)
    # OpenDX sample values are stored in row-major order for the logical grid.
    volume_3d = raw.reshape((nx, ny, nz), order="C").astype(float)

    x = np.linspace(x_origin, x_origin + (nx - 1) * x_spacing, nx)
    y = np.linspace(y_origin, y_origin + (ny - 1) * y_spacing, ny)
    z = np.linspace(z_origin, z_origin + (nz - 1) * z_spacing, nz)

    return x, y, z, volume_3d, metadata


def flatten_grid_for_plotly(
    x: np.ndarray, y: np.ndarray, z: np.ndarray, value_3d: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # go.Volume needs four equal-length 1D arrays: one (x,y,z,value) tuple per grid point.
    xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")
    return xx.ravel(), yy.ravel(), zz.ravel(), value_3d.ravel()


# ---------------------------------------------------------------------------
# Figure building
# ---------------------------------------------------------------------------


def make_mri_figure(
    *,
    window_center: float,
    window_width: float,
    opacity: float,
    slice_x: int,
    slice_y: int,
    slice_z: int,
    show_volume: bool,
    show_slices: bool,
    camera_x: float,
    camera_y: float,
    camera_z: float,
    show_axes: bool,
    camera_override: dict | None = None,
) -> go.Figure:
    x, y, z, vol, _meta = _load_mri()
    nx, ny, nz = vol.shape
    ix = int(np.clip(slice_x, 0, nx - 1))
    iy = int(np.clip(slice_y, 0, ny - 1))
    iz = int(np.clip(slice_z, 0, nz - 1))

    low = window_center - window_width / 2.0
    high = window_center + window_width / 2.0

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "scene"}, {"type": "xy"}]],
        subplot_titles=(
            "3D Volume 体渲染",
            f"Axial 横断面 (z={z[iz]:.1f} mm, layer {iz}/{nz - 1})",
        ),
        horizontal_spacing=0.10,
        column_widths=[0.5, 0.5],
    )

    # 3D Volume (1,1)
    if show_volume or show_slices:
        x_flat, y_flat, z_flat, value_flat = flatten_grid_for_plotly(x, y, z, vol)
        fig.add_trace(
            go.Volume(
                x=x_flat, y=y_flat, z=z_flat,
                value=value_flat,
                isomin=low + 0.05 * window_width,
                isomax=high,
                opacity=opacity if show_volume else 0.0,
                surface={"show": show_volume, "count": 1},
                caps={"x": {"show": False}, "y": {"show": False}, "z": {"show": False}},
                slices={
                    "x": {"show": show_slices, "locations": [x[ix]]},
                    "y": {"show": show_slices, "locations": [y[iy]]},
                    "z": {"show": show_slices, "locations": [z[iz]]},
                },
                colorscale="Viridis",
                cmin=low, cmax=high, cauto=False,
                showscale=False,
                name="mri-3d",
                hovertemplate="x=%{x:.1f}<br>y=%{y:.1f}<br>z=%{z:.1f}<br>I=%{value:.0f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # 2D slices share the same window/level mapping as the 3D view.
    heatmap_common = dict(colorscale="Viridis", zmin=low, zmax=high, zauto=False)

    # Axial (1,2): vol[:, :, iz] — X horizontal, Y vertical
    fig.add_trace(
        go.Heatmap(
            x=x, y=y, z=vol[:, :, iz].T,
            showscale=True,
            colorbar={"title": "MR signal (raw)", "x": 1.02, "len": 0.85, "y": 0.5},
            name="axial",
            hovertemplate="x=%{x:.1f} mm<br>y=%{y:.1f} mm<br>I=%{z:.0f}<extra>axial</extra>",
            **heatmap_common,
        ),
        row=1, col=2,
    )

    fig.update_xaxes(title="x (mm)", row=1, col=2)
    fig.update_yaxes(title="y (mm)", scaleanchor="x", scaleratio=1, row=1, col=2)

    axis_style = {
        "showgrid": show_axes,
        "gridcolor": "#cbd5e1",
        "gridwidth": 1,
        "showline": show_axes,
        "linecolor": "#1f2937",
        "linewidth": 2,
        "zeroline": show_axes,
        "zerolinecolor": "#1f2937",
        "zerolinewidth": 2,
        "ticks": "outside" if show_axes else "",
        "showticklabels": show_axes,
        "visible": show_axes,
        "backgroundcolor": "#f8fafc",
        "color": "#1f2937",
    }

    camera = {"eye": {"x": camera_x, "y": camera_y, "z": camera_z}, "center": {"x": 0, "y": 0, "z": 0}}
    if camera_override:
        for key in ("eye", "center", "up"):
            if key in camera_override:
                camera[key] = camera_override[key]

    fig.update_layout(
        title=f"MRI — WL={window_center:.0f}/{window_width:.0f}",
        margin={"l": 40, "r": 90, "t": 70, "b": 40},
        uirevision="mri-viewer",
        paper_bgcolor="#f1f5f9",
        plot_bgcolor="#f8fafc",
        font={"color": "#1f2937"},
        scene={
            "xaxis": {**axis_style, "title": "x (mm)"},
            "yaxis": {**axis_style, "title": "y (mm)"},
            "zaxis": {**axis_style, "title": "z (mm)"},
            "aspectmode": "data",
            "camera": camera,
        },
    )
    return fig


def make_figure_from_controls(controls: dict, camera_override: dict | None = None) -> go.Figure:
    controls = normalize_controls(controls)
    return make_mri_figure(
        window_center=controls["window_center"],
        window_width=controls["window_width"],
        opacity=controls["opacity"],
        slice_x=controls["slice_x"],
        slice_y=controls["slice_y"],
        slice_z=controls["slice_z"],
        show_volume=controls["show_volume"],
        show_slices=controls["show_slices"],
        camera_x=controls["camera_x"],
        camera_y=controls["camera_y"],
        camera_z=controls["camera_z"],
        show_axes=controls["show_axes"],
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
    _x, _y, _z, vol, _meta = _load_mri()
    vmin, vmax = float(vol.min()), float(vol.max())

    app = Dash(__name__)
    app.title = "MRI Viewer"
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.H2("MRI Viewer"),
                    html.P("OpenDX sample — 128×128×16, uint16"),
                    html.H4("Window / Level 灰度窗"),
                    slider("Center 窗位", "window-center", minimum=500, maximum=60000, step=100,
                           value=DEFAULT_CONTROLS["window_center"],
                           marks={5000: "5k", 10000: "10k", 20000: "20k", 40000: "40k", 60000: "60k"}),
                    slider("Width 窗宽", "window-width", minimum=100, maximum=60000, step=100,
                           value=DEFAULT_CONTROLS["window_width"],
                           marks={8000: "8k", 18000: "18k", 30000: "30k", 45000: "45k", 60000: "60k"}),
                    html.H4("Volume 体渲染"),
                    slider("Opacity", "opacity", minimum=0.01, maximum=1.0, step=0.01,
                           value=DEFAULT_CONTROLS["opacity"]),
                    dcc.Checklist(id="show-volume", options=[{"label": "Show volume", "value": "on"}],
                                  value=["on"], style={"marginTop": "10px"}, inputStyle={"marginRight": "6px"}),
                    html.H4("Orthogonal Slices 正交切片", style={"marginTop": "22px"}),
                    slider("X slice sagittal 矢状面", "slice-x", minimum=0, maximum=GRID_SHAPE[0] - 1, step=1,
                           value=DEFAULT_CONTROLS["slice_x"],
                           marks={float(v): str(v) for v in [0, 32, 64, 96, 127]}),
                    slider("Y slice coronal 额状面", "slice-y", minimum=0, maximum=GRID_SHAPE[1] - 1, step=1,
                           value=DEFAULT_CONTROLS["slice_y"],
                           marks={float(v): str(v) for v in [0, 32, 64, 96, 127]}),
                    slider("Z slice axial 横断面", "slice-z", minimum=0, maximum=GRID_SHAPE[2] - 1, step=1,
                           value=DEFAULT_CONTROLS["slice_z"],
                           marks={float(v): str(v) for v in [0, 4, 8, 12, 15]}),
                    dcc.Checklist(id="show-slices", options=[{"label": "Show slices", "value": "on"}],
                                  value=["on"], style={"marginTop": "10px"}, inputStyle={"marginRight": "6px"}),
                    html.H4("Camera", style={"marginTop": "22px"}),
                    slider("Camera X", "camera-x", minimum=-6, maximum=6, step=0.05, value=DEFAULT_CONTROLS["camera_x"]),
                    slider("Camera Y", "camera-y", minimum=-6, maximum=6, step=0.05, value=DEFAULT_CONTROLS["camera_y"]),
                    slider("Camera Z", "camera-z", minimum=0.2, maximum=6, step=0.05, value=DEFAULT_CONTROLS["camera_z"]),
                    dcc.Checklist(id="show-axes", options=[{"label": "Axes", "value": "axes"}],
                                  value=["axes"], style={"marginTop": "10px"}, inputStyle={"marginRight": "6px"}),
                    html.Div(id="mri-stats", style={"marginTop": "22px", "fontSize": "14px", "lineHeight": "1.5"}),
                ],
                style={"boxSizing": "border-box", "width": "360px", "padding": "18px", "borderRight": "1px solid #ddd",
                       "fontFamily": "Arial, sans-serif", "overflowY": "auto"},
            ),
            html.Div(
                [dcc.Graph(id="mri-graph", config={"displaylogo": False, "scrollZoom": True},
                           style={"height": "calc(100vh - 24px)"})],
                style={"flex": "1", "padding": "12px"},
            ),
        ],
        style={"display": "flex", "height": "100vh", "margin": "0"},
    )

    @app.callback(
        Output("mri-graph", "figure"),
        Output("mri-stats", "children"),
        Input("window-center", "value"),
        Input("window-width", "value"),
        Input("opacity", "value"),
        Input("show-volume", "value"),
        Input("slice-x", "value"),
        Input("slice-y", "value"),
        Input("slice-z", "value"),
        Input("show-slices", "value"),
        Input("camera-x", "value"),
        Input("camera-y", "value"),
        Input("camera-z", "value"),
        Input("show-axes", "value"),
        State("mri-graph", "relayoutData"),
    )
    def update_mri(*args):
        (window_center, window_width, opacity, show_volume, slice_x, slice_y, slice_z,
         show_slices, camera_x, camera_y, camera_z, show_axes, relayout_data) = args
        controls = normalize_controls({
            "window_center": window_center, "window_width": window_width,
            "opacity": opacity, "show_volume": "on" in (show_volume or []),
            "slice_x": slice_x, "slice_y": slice_y, "slice_z": slice_z,
            "show_slices": "on" in (show_slices or []),
            "camera_x": camera_x, "camera_y": camera_y, "camera_z": camera_z,
            "show_axes": "axes" in (show_axes or []),
        })
        relayout_camera = camera_from_relayout(relayout_data)
        if ctx.triggered_id in CAMERA_SLIDER_IDS and camera_eye_matches_controls(relayout_camera, controls):
            return no_update, [html.Div(f"Value range: [{vmin}, {vmax}]"),
                               html.Div(f"Window: center={controls['window_center']:.0f}, width={controls['window_width']:.0f}")]
        camera_override = relayout_camera if should_preserve_user_camera(ctx.triggered_id) else None
        stats = [
            html.Div(f"Grid: {GRID_SHAPE[0]}×{GRID_SHAPE[1]}×{GRID_SHAPE[2]}"),
            html.Div(f"Value range: [{vmin}, {vmax}]"),
            html.Div(f"Window: center={controls['window_center']:.0f}, width={controls['window_width']:.0f}"),
            html.Div(f"Slices: x={controls['slice_x']}, y={controls['slice_y']}, z={controls['slice_z']}"),
        ]
        return make_figure_from_controls(controls, camera_override), stats

    @app.callback(
        Output("camera-x", "value"), Output("camera-y", "value"), Output("camera-z", "value"),
        Input("mri-graph", "relayoutData"),
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
    parser.add_argument("--port", type=int, default=8055)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        x, y, z, vol, meta = _load_mri()
        print(f"Grid: {vol.shape}, range [{vol.min():.0f}, {vol.max():.0f}]")
        print(f"Physical: {x[0]:.1f}–{x[-1]:.1f} × {y[0]:.1f}–{y[-1]:.1f} × {z[0]:.1f}–{z[-1]:.1f} mm")
        print(f"Default window: center={DEFAULT_WINDOW_CENTER:.0f}, width={DEFAULT_WINDOW_WIDTH:.0f}")
        print(f"Default slices: x={DEFAULT_SLICE_X}, y={DEFAULT_SLICE_Y}, z={DEFAULT_SLICE_Z}")
        fig = make_figure_from_controls(DEFAULT_CONTROLS)
        print(f"Traces: {len(fig.data)}, JSON: {len(fig.to_json())}")
        return
    app = create_app()
    print(f"Dash app running at http://{args.host}:{args.port}")
    (app.run if hasattr(app, "run") else app.run_server)(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
