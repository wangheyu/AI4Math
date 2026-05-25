#!/usr/bin/env python3
"""PyVista animation examples for multivariable calculus surfaces.

Examples:
  orbit   - rotate the camera around z = x^2 - y^2
  deform  - morph z = x^2 + a y^2 from positive definite to indefinite
  wave    - animate z = sin(x - t) cos(y)

By default, all three animations are rendered as MP4 files. Use
``--format gif`` to render animated GIFs instead.
"""

from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
from pathlib import Path

# Keep PyVista/Matplotlib/Mesa quiet and writable in restricted environments.
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("MESA_SHADER_CACHE_DISABLE", "true")

import numpy as np
import pyvista as pv


DEFAULT_FRAMES = 60
DEFAULT_FPS = 15
DEFAULT_N = 81
FORMATS = ("mp4", "gif")


def configure_pyvista() -> None:
    """Set PyVista defaults for headless, deterministic rendering."""
    pv.OFF_SCREEN = True
    pv.global_theme.background = "white"
    pv.global_theme.font.color = "black"
    pv.global_theme.cmap = "viridis"


def make_grid(xlim: tuple[float, float], ylim: tuple[float, float], n: int):
    """Return X, Y meshgrid arrays."""
    x = np.linspace(xlim[0], xlim[1], n)
    y = np.linspace(ylim[0], ylim[1], n)
    return np.meshgrid(x, y, indexing="ij")


def make_surface_mesh(X: np.ndarray, Y: np.ndarray, Z: np.ndarray) -> pv.StructuredGrid:
    """Build a PyVista structured grid from coordinate arrays."""
    mesh = pv.StructuredGrid(X, Y, Z)
    mesh["height"] = np.asarray(Z, dtype=float).ravel(order="F")
    return mesh


def update_surface_mesh(mesh: pv.StructuredGrid, Z: np.ndarray) -> None:
    """Update an existing structured grid's z coordinates and scalar values."""
    points = mesh.points.copy()
    points[:, 2] = np.asarray(Z, dtype=float).ravel(order="F")
    mesh.points = points
    mesh["height"] = np.asarray(Z, dtype=float).ravel(order="F")


def quadratic_classification(a: float, tol: float = 1e-10) -> str:
    """Classify z = x^2 + a y^2 by the signs of its eigenvalues."""
    if a > tol:
        return "positive definite"
    if a < -tol:
        return "indefinite"
    return "semidefinite"


def add_surface(
    plotter: pv.Plotter,
    mesh: pv.StructuredGrid,
    clim: tuple[float, float] | None = None,
):
    """Add a calculus surface with scalar colors and light contour lines."""
    plotter.add_mesh(
        mesh,
        scalars="height",
        cmap="viridis",
        clim=clim,
        smooth_shading=True,
        scalar_bar_args={"title": "z", "vertical": True},
    )
    contours = mesh.contour(isosurfaces=12, scalars="height")
    if contours.n_points:
        plotter.add_mesh(contours, color="white", line_width=2)
    plotter.add_axes(line_width=2)
    plotter.show_grid(
        xtitle="x",
        ytitle="y",
        ztitle="z",
        color="black",
        grid="back",
        location="outer",
    )


def setup_plotter(window_size: tuple[int, int], title: str) -> pv.Plotter:
    """Create a configured off-screen plotter."""
    plotter = pv.Plotter(off_screen=True, window_size=window_size)
    plotter.set_background("white")
    plotter.add_text(title, position="upper_left", font_size=12, color="black")
    return plotter


def open_animation(plotter: pv.Plotter, output: Path, fps: int) -> None:
    """Open a PyVista animation writer based on the output extension."""
    suffix = output.suffix.lower()
    if suffix == ".gif":
        plotter.open_gif(str(output), fps=fps)
    elif suffix == ".mp4":
        plotter.open_movie(str(output), framerate=fps)
    else:
        raise ValueError(f"Unsupported output extension: {output.suffix}. Use .mp4 or .gif.")


def write_orbit_saddle(
    output: Path,
    frames: int = DEFAULT_FRAMES,
    fps: int = DEFAULT_FPS,
    n: int = DEFAULT_N,
) -> Path:
    """Render a camera orbit around the saddle surface z = x^2 - y^2."""
    X, Y = make_grid((-3, 3), (-3, 3), n)
    Z = X**2 - Y**2
    mesh = make_surface_mesh(X, Y, Z)

    plotter = setup_plotter((896, 640), "Camera orbit: z = x^2 - y^2")
    add_surface(plotter, mesh, clim=(-9, 9))
    plotter.camera_position = [(7, -7, 5), (0, 0, 0), (0, 0, 1)]
    open_animation(plotter, output, fps)

    radius = 10.0
    z_camera = 5.0
    for frame in range(frames):
        theta = 2 * math.pi * frame / frames
        plotter.camera.position = (radius * math.cos(theta), radius * math.sin(theta), z_camera)
        plotter.camera.focal_point = (0, 0, 0)
        plotter.camera.up = (0, 0, 1)
        plotter.write_frame()

    plotter.close()
    return output


def write_quadratic_deform(
    output: Path,
    frames: int = DEFAULT_FRAMES,
    fps: int = DEFAULT_FPS,
    n: int = DEFAULT_N,
) -> Path:
    """Render z = x^2 + a y^2 as a changes from 1 to -1."""
    X, Y = make_grid((-3, 3), (-3, 3), n)
    a_values = np.linspace(1.0, -1.0, frames)
    Z = X**2 + a_values[0] * Y**2
    mesh = make_surface_mesh(X, Y, Z)

    plotter = setup_plotter((896, 640), "Quadratic deformation")
    add_surface(plotter, mesh, clim=(-9, 18))
    text_actor = None
    plotter.camera_position = [(7, -7, 5), (0, 0, 0), (0, 0, 1)]
    open_animation(plotter, output, fps)

    for a in a_values:
        update_surface_mesh(mesh, X**2 + a * Y**2)
        if text_actor is not None:
            plotter.remove_actor(text_actor)
        text_actor = plotter.add_text(
            f"z = x^2 + a y^2,  a = {a:.2f},  {quadratic_classification(float(a))}",
            position="lower_left",
            font_size=11,
            color="black",
        )
        plotter.write_frame()

    plotter.close()
    return output


def write_wave_surface(
    output: Path,
    frames: int = DEFAULT_FRAMES,
    fps: int = DEFAULT_FPS,
    n: int = DEFAULT_N,
) -> Path:
    """Render the traveling wave z = sin(x - t) cos(y)."""
    X, Y = make_grid((-2 * math.pi, 2 * math.pi), (-2 * math.pi, 2 * math.pi), n)
    t_values = np.linspace(0.0, 2 * math.pi, frames, endpoint=False)
    Z = np.sin(X - t_values[0]) * np.cos(Y)
    mesh = make_surface_mesh(X, Y, Z)

    plotter = setup_plotter((896, 640), "Traveling wave: z = sin(x - t) cos(y)")
    add_surface(plotter, mesh, clim=(-1, 1))
    text_actor = None
    plotter.camera_position = [(9, -9, 5), (0, 0, 0), (0, 0, 1)]
    open_animation(plotter, output, fps)

    for t in t_values:
        update_surface_mesh(mesh, np.sin(X - t) * np.cos(Y))
        if text_actor is not None:
            plotter.remove_actor(text_actor)
        text_actor = plotter.add_text(f"t = {t:.2f}", position="lower_left", font_size=11, color="black")
        plotter.write_frame()

    plotter.close()
    return output


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render PyVista animation examples.")
    parser.add_argument(
        "example",
        nargs="?",
        choices=("all", "orbit", "deform", "wave"),
        default="all",
        help="animation to render",
    )
    parser.add_argument("--frames", type=positive_int, default=DEFAULT_FRAMES, help="number of frames")
    parser.add_argument("--fps", type=positive_int, default=DEFAULT_FPS, help="frames per second")
    parser.add_argument("--n", type=positive_int, default=DEFAULT_N, help="grid resolution per axis")
    parser.add_argument("--outdir", type=Path, default=Path("."), help="output directory")
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default="mp4",
        help="output animation format",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    jobs = {
        "orbit": (write_orbit_saddle, "pyvista_orbit_saddle.mp4"),
        "deform": (write_quadratic_deform, "pyvista_quadratic_deform.mp4"),
        "wave": (write_wave_surface, "pyvista_wave_surface.mp4"),
    }

    if args.example == "all":
        script = Path(__file__).resolve()
        for name in jobs:
            cmd = [
                sys.executable,
                str(script),
                name,
                "--frames",
                str(args.frames),
                "--fps",
                str(args.fps),
                "--n",
                str(args.n),
                "--outdir",
                str(args.outdir),
                "--format",
                args.format,
            ]
            subprocess.run(cmd, check=True)
        return

    configure_pyvista()

    writer, filename = jobs[args.example]
    filename = f"{Path(filename).stem}.{args.format}"
    path = args.outdir / filename
    print(f"Rendering {args.example}: {path}", flush=True)
    writer(path, frames=args.frames, fps=args.fps, n=args.n)
    size = path.stat().st_size if path.exists() else 0
    print(f"Saved {path} ({size} bytes)", flush=True)


if __name__ == "__main__":
    main()
