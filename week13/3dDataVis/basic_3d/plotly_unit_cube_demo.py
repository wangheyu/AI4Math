#!/usr/bin/env python3
"""Dash + Plotly unit-cube scene for basic 3D rendering concepts.

Run from the repository root:

    conda activate ai4math-vis
    python basic_3d/plotly_unit_cube_demo.py

Then open http://127.0.0.1:8051 in a browser.
"""

from __future__ import annotations

import argparse
import math

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update


DEFAULT_CONTROLS = {
    "object_shape": "cube",
    "solid_color": "#3b82f6",
    "ambient": 0.15,
    "diffuse": 0.95,
    "specular": 0.65,
    "roughness": 0.35,
    "fresnel": 0.25,
    "light_x": 1.6,
    "light_y": -1.2,
    "light_z": 2.0,
    "camera_x": 1.8,
    "camera_y": 1.55,
    "camera_z": 1.25,
    "show_edges": False,
    "show_axes": True,
}

SOLID_COLORS = {
    "Blue": "#3b82f6",
    "Green": "#16a34a",
    "Red": "#dc2626",
    "Gold": "#d97706",
    "Graphite": "#475569",
    "White": "#f8fafc",
}

DISPLAY_OPTIONS = [
    {"label": "Axes", "value": "axes"},
    {"label": "Edges", "value": "edges"},
]

OBJECT_OPTIONS = [
    {"label": "Unit cube 单位立方体", "value": "cube"},
    {"label": "Unit sphere 单位球", "value": "sphere"},
]

CUBE_FACES = [
    {
        "name": "z = 0",
        "vertices": [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
        "normal": (0.0, 0.0, -1.0),
        "center": (0.5, 0.5, 0.0),
    },
    {
        "name": "z = 1",
        "vertices": [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
        "normal": (0.0, 0.0, 1.0),
        "center": (0.5, 0.5, 1.0),
    },
    {
        "name": "x = 0",
        "vertices": [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)],
        "normal": (-1.0, 0.0, 0.0),
        "center": (0.0, 0.5, 0.5),
    },
    {
        "name": "x = 1",
        "vertices": [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
        "normal": (1.0, 0.0, 0.0),
        "center": (1.0, 0.5, 0.5),
    },
    {
        "name": "y = 0",
        "vertices": [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
        "normal": (0.0, -1.0, 0.0),
        "center": (0.5, 0.0, 0.5),
    },
    {
        "name": "y = 1",
        "vertices": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
        "normal": (0.0, 1.0, 0.0),
        "center": (0.5, 1.0, 0.5),
    },
]

NEUTRAL_PLOTLY_LIGHTING = {
    "ambient": 1.0,
    "diffuse": 0.0,
    "specular": 0.0,
    "roughness": 1.0,
    "fresnel": 0.0,
}

CAMERA_SLIDER_IDS = {"camera-x", "camera-y", "camera-z"}


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def normalize_controls(controls: dict | None) -> dict:
    merged = dict(DEFAULT_CONTROLS)
    if controls:
        merged.update(controls)

    if merged["object_shape"] not in {"cube", "sphere"}:
        merged["object_shape"] = DEFAULT_CONTROLS["object_shape"]
    if merged["solid_color"] not in set(SOLID_COLORS.values()):
        merged["solid_color"] = DEFAULT_CONTROLS["solid_color"]

    merged["ambient"] = round(clamp(float(merged["ambient"]), 0.0, 1.0), 2)
    merged["diffuse"] = round(clamp(float(merged["diffuse"]), 0.0, 1.0), 2)
    merged["specular"] = round(clamp(float(merged["specular"]), 0.0, 2.0), 2)
    merged["roughness"] = round(clamp(float(merged["roughness"]), 0.0, 1.0), 2)
    merged["fresnel"] = round(clamp(float(merged["fresnel"]), 0.0, 2.0), 2)

    merged["light_x"] = round(clamp(float(merged["light_x"]), -1.5, 2.5), 2)
    merged["light_y"] = round(clamp(float(merged["light_y"]), -1.5, 2.5), 2)
    merged["light_z"] = round(clamp(float(merged["light_z"]), -0.5, 2.8), 2)

    merged["camera_x"] = round(clamp(float(merged["camera_x"]), -8.0, 8.0), 2)
    merged["camera_y"] = round(clamp(float(merged["camera_y"]), -8.0, 8.0), 2)
    merged["camera_z"] = round(clamp(float(merged["camera_z"]), -8.0, 8.0), 2)

    for key in ("show_edges", "show_axes"):
        merged[key] = bool(merged[key])
    return merged


def make_edge_trace() -> go.Scatter3d:
    edges = [
        ((0, 0, 0), (1, 0, 0)),
        ((0, 1, 0), (1, 1, 0)),
        ((0, 0, 1), (1, 0, 1)),
        ((0, 1, 1), (1, 1, 1)),
        ((0, 0, 0), (0, 1, 0)),
        ((1, 0, 0), (1, 1, 0)),
        ((0, 0, 1), (0, 1, 1)),
        ((1, 0, 1), (1, 1, 1)),
        ((0, 0, 0), (0, 0, 1)),
        ((1, 0, 0), (1, 0, 1)),
        ((0, 1, 0), (0, 1, 1)),
        ((1, 1, 0), (1, 1, 1)),
    ]
    x_values: list[float | None] = []
    y_values: list[float | None] = []
    z_values: list[float | None] = []
    for start, end in edges:
        x_values.extend([start[0], end[0], None])
        y_values.extend([start[1], end[1], None])
        z_values.extend([start[2], end[2], None])
    return go.Scatter3d(
        x=x_values,
        y=y_values,
        z=z_values,
        mode="lines",
        name="edges",
        line={"color": "#111827", "width": 5},
        hoverinfo="skip",
        showlegend=False,
    )


def object_center(object_shape: str) -> tuple[float, float, float]:
    if object_shape == "sphere":
        return (0.0, 0.0, 0.0)
    return (0.5, 0.5, 0.5)


def make_light_trace(
    light_x: float,
    light_y: float,
    light_z: float,
    target: tuple[float, float, float],
) -> go.Scatter3d:
    return go.Scatter3d(
        x=[light_x, target[0]],
        y=[light_y, target[1]],
        z=[light_z, target[2]],
        mode="markers+lines+text",
        text=["light", ""],
        textposition="top center",
        name="light source",
        marker={"size": [8, 0.1], "color": ["#facc15", "#facc15"], "line": {"color": "#111827", "width": 1}},
        line={"color": "#facc15", "width": 4, "dash": "dash"},
        hovertemplate="light<br>x=%{x:.2f}<br>y=%{y:.2f}<br>z=%{z:.2f}<extra></extra>",
        showlegend=False,
    )


def subtract(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(dot(vector, vector))
    if length <= 1e-12:
        return (0.0, 0.0, 0.0)
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def specular_highlight(
    normal: tuple[float, float, float],
    light_direction: tuple[float, float, float],
    view_direction: tuple[float, float, float],
    roughness: float,
) -> float:
    """Blinn-Phong highlight term tuned for a visible teaching demo."""
    half_vector = normalize(add(light_direction, view_direction))
    if half_vector == (0.0, 0.0, 0.0):
        return 0.0

    shininess = 1.5 + (1.0 - roughness) * 10.0
    roughness_attenuation = 1.15 - 0.45 * roughness
    return (max(dot(normal, half_vector), 0.0) ** shininess) * roughness_attenuation


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    stripped = color.lstrip("#")
    return tuple(int(stripped[index : index + 2], 16) for index in (0, 2, 4))


def rgb_to_hex(red: float, green: float, blue: float) -> str:
    channels = [round(clamp(value, 0, 255)) for value in (red, green, blue)]
    return "#{:02x}{:02x}{:02x}".format(*channels)


def shaded_color(base_color: str, intensity: float) -> str:
    red, green, blue = hex_to_rgb(base_color)
    if intensity <= 1.0:
        factor = max(0.06, intensity)
        return rgb_to_hex(red * factor, green * factor, blue * factor)

    highlight = clamp((intensity - 1.0) / 0.35, 0.0, 1.0)
    return rgb_to_hex(
        red + (255 - red) * highlight,
        green + (255 - green) * highlight,
        blue + (255 - blue) * highlight,
    )


def face_light_intensity(
    face: dict,
    *,
    light: tuple[float, float, float],
    camera: tuple[float, float, float],
    ambient: float,
    diffuse: float,
    specular: float,
    roughness: float,
    fresnel: float,
) -> float:
    normal = face["normal"]
    center = face["center"]
    light_direction = normalize(subtract(light, center))
    view_direction = normalize(subtract(camera, center))

    diffuse_term = max(dot(normal, light_direction), 0.0)
    specular_term = 0.0
    if diffuse_term > 0:
        specular_term = specular_highlight(normal, light_direction, view_direction, roughness)

    view_alignment = max(dot(normal, view_direction), 0.0)
    fresnel_term = (1.0 - view_alignment) ** 5
    intensity = ambient + diffuse * diffuse_term + specular * specular_term + 0.35 * fresnel * fresnel_term
    return clamp(intensity, 0.0, 1.35)


def point_light_intensity(
    *,
    point: tuple[float, float, float],
    normal: tuple[float, float, float],
    light: tuple[float, float, float],
    camera: tuple[float, float, float],
    ambient: float,
    diffuse: float,
    specular: float,
    roughness: float,
    fresnel: float,
) -> float:
    light_direction = normalize(subtract(light, point))
    view_direction = normalize(subtract(camera, point))

    diffuse_term = max(dot(normal, light_direction), 0.0)
    specular_term = 0.0
    if diffuse_term > 0:
        specular_term = specular_highlight(normal, light_direction, view_direction, roughness)

    view_alignment = max(dot(normal, view_direction), 0.0)
    fresnel_term = (1.0 - view_alignment) ** 5
    intensity = ambient + diffuse * diffuse_term + specular * specular_term + 0.35 * fresnel * fresnel_term
    return clamp(intensity, 0.0, 1.35)


def camera_tuple(controls: dict, camera_override: dict | None = None) -> tuple[float, float, float]:
    if camera_override and "eye" in camera_override:
        eye = camera_override["eye"]
        return (float(eye["x"]), float(eye["y"]), float(eye["z"]))
    return (controls["camera_x"], controls["camera_y"], controls["camera_z"])


def make_cube_face_traces(
    *,
    solid_color: str,
    controls: dict,
    camera: tuple[float, float, float],
) -> list[go.Surface]:
    light = (controls["light_x"], controls["light_y"], controls["light_z"])
    traces = []
    for face in CUBE_FACES:
        x_values, y_values, z_values, intensities = cube_face_surface_arrays(
            face,
            light=light,
            camera=camera,
            controls=controls,
        )
        traces.append(
            go.Surface(
                x=x_values,
                y=y_values,
                z=z_values,
                surfacecolor=intensities,
                colorscale=surface_colorscale(solid_color),
                cmin=0,
                cmax=1.35,
                showscale=False,
                lighting=NEUTRAL_PLOTLY_LIGHTING,
                lightposition={"x": 0, "y": 0, "z": 0},
                name=face["name"],
                hovertemplate=(
                    f"{face['name']}<br>"
                    "x=%{x:.2f}<br>y=%{y:.2f}<br>z=%{z:.2f}"
                    "<extra></extra>"
                ),
            )
        )
    return traces


def cube_face_surface_arrays(
    face: dict,
    *,
    light: tuple[float, float, float],
    camera: tuple[float, float, float],
    controls: dict,
    resolution: int = 20,
) -> tuple[list[list[float]], list[list[float]], list[list[float]], list[list[float]]]:
    x_values: list[list[float]] = []
    y_values: list[list[float]] = []
    z_values: list[list[float]] = []
    intensities: list[list[float]] = []
    normal = face["normal"]

    for row in range(resolution + 1):
        u = row / resolution
        x_row: list[float] = []
        y_row: list[float] = []
        z_row: list[float] = []
        intensity_row: list[float] = []
        for col in range(resolution + 1):
            v = col / resolution
            if face["name"] == "z = 0":
                point = (u, v, 0.0)
            elif face["name"] == "z = 1":
                point = (u, v, 1.0)
            elif face["name"] == "x = 0":
                point = (0.0, u, v)
            elif face["name"] == "x = 1":
                point = (1.0, u, v)
            elif face["name"] == "y = 0":
                point = (u, 0.0, v)
            else:
                point = (u, 1.0, v)

            x_row.append(point[0])
            y_row.append(point[1])
            z_row.append(point[2])
            intensity_row.append(
                point_light_intensity(
                    point=point,
                    normal=normal,
                    light=light,
                    camera=camera,
                    ambient=controls["ambient"],
                    diffuse=controls["diffuse"],
                    specular=controls["specular"],
                    roughness=controls["roughness"],
                    fresnel=controls["fresnel"],
                )
            )
        x_values.append(x_row)
        y_values.append(y_row)
        z_values.append(z_row)
        intensities.append(intensity_row)

    return x_values, y_values, z_values, intensities


def surface_colorscale(base_color: str) -> list[list[object]]:
    base = hex_to_rgb(base_color)
    dark = rgb_to_hex(base[0] * 0.06, base[1] * 0.06, base[2] * 0.06)
    return [[0.0, dark], [0.7407, base_color], [1.0, "#ffffff"]]


def make_sphere_surface_trace(
    *,
    solid_color: str,
    controls: dict,
    camera: tuple[float, float, float],
    resolution: int = 42,
) -> go.Surface:
    light = (controls["light_x"], controls["light_y"], controls["light_z"])
    x_values: list[list[float]] = []
    y_values: list[list[float]] = []
    z_values: list[list[float]] = []
    intensities: list[list[float]] = []

    for row in range(resolution + 1):
        theta = math.pi * row / resolution
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)
        x_row: list[float] = []
        y_row: list[float] = []
        z_row: list[float] = []
        intensity_row: list[float] = []
        for col in range(2 * resolution + 1):
            phi = 2.0 * math.pi * col / (2 * resolution)
            point = (sin_theta * math.cos(phi), sin_theta * math.sin(phi), cos_theta)
            normal = point
            x_row.append(point[0])
            y_row.append(point[1])
            z_row.append(point[2])
            intensity_row.append(
                point_light_intensity(
                    point=point,
                    normal=normal,
                    light=light,
                    camera=camera,
                    ambient=controls["ambient"],
                    diffuse=controls["diffuse"],
                    specular=controls["specular"],
                    roughness=controls["roughness"],
                    fresnel=controls["fresnel"],
                )
            )
        x_values.append(x_row)
        y_values.append(y_row)
        z_values.append(z_row)
        intensities.append(intensity_row)

    return go.Surface(
        x=x_values,
        y=y_values,
        z=z_values,
        surfacecolor=intensities,
        colorscale=surface_colorscale(solid_color),
        cmin=0,
        cmax=1.35,
        showscale=False,
        lighting=NEUTRAL_PLOTLY_LIGHTING,
        lightposition={"x": 0, "y": 0, "z": 0},
        name="unit sphere",
        hovertemplate="unit sphere<br>x=%{x:.2f}<br>y=%{y:.2f}<br>z=%{z:.2f}<extra></extra>",
        showlegend=False,
    )


def make_sphere_wireframe_trace(resolution: int = 18) -> go.Scatter3d:
    x_values: list[float | None] = []
    y_values: list[float | None] = []
    z_values: list[float | None] = []

    for theta_index in range(1, resolution):
        theta = math.pi * theta_index / resolution
        for phi_index in range(2 * resolution + 1):
            phi = 2.0 * math.pi * phi_index / (2 * resolution)
            x_values.append(math.sin(theta) * math.cos(phi))
            y_values.append(math.sin(theta) * math.sin(phi))
            z_values.append(math.cos(theta))
        x_values.append(None)
        y_values.append(None)
        z_values.append(None)

    for phi_index in range(0, 2 * resolution, 2):
        phi = 2.0 * math.pi * phi_index / (2 * resolution)
        for theta_index in range(resolution + 1):
            theta = math.pi * theta_index / resolution
            x_values.append(math.sin(theta) * math.cos(phi))
            y_values.append(math.sin(theta) * math.sin(phi))
            z_values.append(math.cos(theta))
        x_values.append(None)
        y_values.append(None)
        z_values.append(None)

    return go.Scatter3d(
        x=x_values,
        y=y_values,
        z=z_values,
        mode="lines",
        name="edges",
        line={"color": "#111827", "width": 2},
        hoverinfo="skip",
        showlegend=False,
    )


def make_scene_figure(
    *,
    object_shape: str,
    solid_color: str,
    ambient: float,
    diffuse: float,
    specular: float,
    roughness: float,
    fresnel: float,
    light_x: float,
    light_y: float,
    light_z: float,
    camera_x: float,
    camera_y: float,
    camera_z: float,
    show_edges: bool,
    show_axes: bool,
    camera_override: dict | None = None,
) -> go.Figure:
    controls = normalize_controls(locals())
    solid_color = controls["solid_color"]
    camera_for_lighting = camera_tuple(controls, camera_override)

    if controls["object_shape"] == "sphere":
        traces: list[go.BaseTraceType] = [
            make_sphere_surface_trace(
                solid_color=solid_color,
                controls=controls,
                camera=camera_for_lighting,
            )
        ]
        if controls["show_edges"]:
            traces.append(make_sphere_wireframe_trace())
    else:
        traces = make_cube_face_traces(
            solid_color=solid_color,
            controls=controls,
            camera=camera_for_lighting,
        )
        if controls["show_edges"]:
            traces.append(make_edge_trace())

    traces.append(
        make_light_trace(
            controls["light_x"],
            controls["light_y"],
            controls["light_z"],
            object_center(controls["object_shape"]),
        )
    )

    axis_style = {
        "range": [-1.7, 2.9],
        "showgrid": controls["show_axes"],
        "gridcolor": "#d1d5db",
        "gridwidth": 2,
        "showline": controls["show_axes"],
        "linecolor": "#111827",
        "linewidth": 3,
        "zeroline": controls["show_axes"],
        "zerolinecolor": "#111827",
        "zerolinewidth": 3,
        "ticks": "outside" if controls["show_axes"] else "",
        "tickmode": "array",
        "tickvals": [-1, 0, 0.5, 1, 2],
        "ticktext": ["-1", "0", "0.5", "1", "2"],
        "ticklen": 5,
        "tickwidth": 2,
        "tickcolor": "#111827",
        "tickfont": {"size": 12, "color": "#111827"},
        "showticklabels": controls["show_axes"],
        "visible": controls["show_axes"],
        "backgroundcolor": "#ffffff",
    }
    camera = {
        "eye": {
            "x": controls["camera_x"],
            "y": controls["camera_y"],
            "z": controls["camera_z"],
        },
        "center": {"x": 0, "y": 0, "z": 0},
    }
    if camera_override:
        for key in ("eye", "center", "up"):
            if key in camera_override:
                camera[key] = camera_override[key]

    fig = go.Figure(data=traces)
    fig.update_layout(
        title="Unit Cube / Sphere Rendering",
        margin={"l": 0, "r": 0, "t": 46, "b": 0},
        uirevision="unit-cube",
        paper_bgcolor="#ffffff",
        scene={
            "xaxis": {**axis_style, "title": "x"},
            "yaxis": {**axis_style, "title": "y"},
            "zaxis": {**axis_style, "title": "z"},
            "aspectmode": "cube",
            "camera": camera,
        },
    )
    return fig


def make_figure_from_controls(controls: dict, camera_override: dict | None = None) -> go.Figure:
    controls = normalize_controls(controls)
    return make_scene_figure(**controls, camera_override=camera_override)


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


def display_values(controls: dict, camera_override: dict | None = None) -> list:
    controls = normalize_controls(controls)
    camera_eye = controls
    if camera_override and "eye" in camera_override:
        camera_eye = {
            "camera_x": camera_override["eye"]["x"],
            "camera_y": camera_override["eye"]["y"],
            "camera_z": camera_override["eye"]["z"],
        }
    object_text = (
        "Sphere: center = (0, 0, 0), radius = 1"
        if controls["object_shape"] == "sphere"
        else "Cube: [0, 1] x [0, 1] x [0, 1]"
    )
    return [
        html.Div(object_text),
        html.Div(
            "Light: "
            f"({controls['light_x']:.2f}, {controls['light_y']:.2f}, {controls['light_z']:.2f})"
        ),
        html.Div(
            "Camera: "
            f"({camera_eye['camera_x']:.2f}, {camera_eye['camera_y']:.2f}, {camera_eye['camera_z']:.2f})"
        ),
        html.Div(
            "Material: "
            f"A {controls['ambient']:.2f}, D {controls['diffuse']:.2f}, "
            f"S {controls['specular']:.2f}, R {controls['roughness']:.2f}, F {controls['fresnel']:.2f}"
        ),
    ]


def selected_display_options(controls: dict) -> list[str]:
    controls = normalize_controls(controls)
    values: list[str] = []
    if controls["show_axes"]:
        values.append("axes")
    if controls["show_edges"]:
        values.append("edges")
    return values


def controls_from_display_options(values: list[str] | None) -> dict:
    values = values or []
    return {
        "show_axes": "axes" in values,
        "show_edges": "edges" in values,
    }


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
            {
                axis: relayout_data.get(f"scene.camera.{part}.{axis}")
                for axis in ("x", "y", "z")
            }
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
        abs(float(eye[axis]) - controls[f"camera_{axis}"]) <= tolerance
        for axis in ("x", "y", "z")
    )


def create_app() -> Dash:
    app = Dash(__name__)
    app.title = "Unit Cube / Sphere Rendering"
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.H2("Unit Cube / Sphere Rendering"),
                    html.H4("Surface"),
                    html.Label("Object", style={"display": "block"}),
                    dcc.Dropdown(
                        id="object-shape",
                        value=DEFAULT_CONTROLS["object_shape"],
                        clearable=False,
                        options=OBJECT_OPTIONS,
                    ),
                    html.Label("Color / texture", style={"marginTop": "15px", "display": "block"}),
                    dcc.Dropdown(
                        id="solid-color",
                        value=DEFAULT_CONTROLS["solid_color"],
                        clearable=False,
                        options=[{"label": name, "value": color} for name, color in SOLID_COLORS.items()],
                    ),
                    html.Label("Display", style={"marginTop": "18px", "display": "block"}),
                    dcc.Checklist(
                        id="display-options",
                        options=DISPLAY_OPTIONS,
                        value=selected_display_options(DEFAULT_CONTROLS),
                        inputStyle={"marginRight": "6px"},
                        labelStyle={"display": "block", "marginTop": "6px"},
                    ),
                    html.H4("Lighting", style={"marginTop": "22px"}),
                    slider("Light X", "light-x", minimum=-1.5, maximum=2.5, step=0.1, value=DEFAULT_CONTROLS["light_x"]),
                    slider("Light Y", "light-y", minimum=-1.5, maximum=2.5, step=0.1, value=DEFAULT_CONTROLS["light_y"]),
                    slider("Light Z", "light-z", minimum=-0.5, maximum=2.8, step=0.1, value=DEFAULT_CONTROLS["light_z"]),
                    slider("Ambient 环境光", "ambient", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["ambient"]),
                    slider("Diffuse 漫反射", "diffuse", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["diffuse"]),
                    slider("Specular 镜面反射", "specular", minimum=0, maximum=2, step=0.05, value=DEFAULT_CONTROLS["specular"]),
                    slider("Roughness 粗糙度", "roughness", minimum=0, maximum=1, step=0.05, value=DEFAULT_CONTROLS["roughness"]),
                    slider("Fresnel 菲涅尔", "fresnel", minimum=0, maximum=2, step=0.05, value=DEFAULT_CONTROLS["fresnel"]),
                    html.H4("Camera", style={"marginTop": "22px"}),
                    slider("Camera X", "camera-x", minimum=-8, maximum=8, step=0.05, value=DEFAULT_CONTROLS["camera_x"]),
                    slider("Camera Y", "camera-y", minimum=-8, maximum=8, step=0.05, value=DEFAULT_CONTROLS["camera_y"]),
                    slider("Camera Z", "camera-z", minimum=-8, maximum=8, step=0.05, value=DEFAULT_CONTROLS["camera_z"]),
                    html.Div(id="cube-stats", style={"marginTop": "22px", "fontSize": "14px", "lineHeight": "1.5"}),
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
                        id="cube-graph",
                        config={"displaylogo": False, "scrollZoom": True},
                        style={"height": "calc(100vh - 24px)"},
                    )
                ],
                style={"flex": "1", "padding": "12px"},
            ),
        ],
        style={"display": "flex", "height": "100vh", "margin": "0"},
    )

    @app.callback(
        Output("cube-graph", "figure"),
        Output("cube-stats", "children"),
        Input("object-shape", "value"),
        Input("solid-color", "value"),
        Input("display-options", "value"),
        Input("light-x", "value"),
        Input("light-y", "value"),
        Input("light-z", "value"),
        Input("ambient", "value"),
        Input("diffuse", "value"),
        Input("specular", "value"),
        Input("roughness", "value"),
        Input("fresnel", "value"),
        Input("camera-x", "value"),
        Input("camera-y", "value"),
        Input("camera-z", "value"),
        State("cube-graph", "relayoutData"),
    )
    def update_cube(
        object_shape,
        solid_color,
        display_options,
        light_x,
        light_y,
        light_z,
        ambient,
        diffuse,
        specular,
        roughness,
        fresnel,
        camera_x,
        camera_y,
        camera_z,
        relayout_data,
    ):
        controls = normalize_controls(
            {
                "solid_color": solid_color,
                "object_shape": object_shape,
                "light_x": light_x,
                "light_y": light_y,
                "light_z": light_z,
                "ambient": ambient,
                "diffuse": diffuse,
                "specular": specular,
                "roughness": roughness,
                "fresnel": fresnel,
                "camera_x": camera_x,
                "camera_y": camera_y,
                "camera_z": camera_z,
                **controls_from_display_options(display_options),
            }
        )
        relayout_camera = camera_from_relayout(relayout_data)
        if ctx.triggered_id in CAMERA_SLIDER_IDS and camera_eye_matches_controls(relayout_camera, controls):
            return no_update, display_values(controls, relayout_camera)

        camera_override = None
        if should_preserve_user_camera(ctx.triggered_id):
            camera_override = relayout_camera
        return make_figure_from_controls(controls, camera_override), display_values(controls, camera_override)

    @app.callback(
        Output("camera-x", "value"),
        Output("camera-y", "value"),
        Output("camera-z", "value"),
        Input("cube-graph", "relayoutData"),
        prevent_initial_call=True,
    )
    def sync_camera_sliders(relayout_data):
        camera = camera_from_relayout(relayout_data)
        if not camera or "eye" not in camera:
            return no_update, no_update, no_update
        eye = camera["eye"]
        controls = normalize_controls(
            {
                "camera_x": eye["x"],
                "camera_y": eye["y"],
                "camera_z": eye["z"],
            }
        )
        return controls["camera_x"], controls["camera_y"], controls["camera_z"]

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8051)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--check", action="store_true", help="Build the default figure and exit without starting Dash.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        fig = make_figure_from_controls(DEFAULT_CONTROLS)
        mesh_count = sum(1 for trace in fig.data if trace.type == "mesh3d")
        surface_count = sum(1 for trace in fig.data if trace.type == "surface")
        light_count = sum(1 for trace in fig.data if getattr(trace, "name", "") == "light source")
        print(f"Default figure traces: {len(fig.data)}")
        print(f"Mesh traces: {mesh_count}")
        print(f"Surface traces: {surface_count}")
        print(f"Light source traces: {light_count}")
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
