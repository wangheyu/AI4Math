#!/usr/bin/env python3
"""Minimal Python/PyVista workflow for simulation visualization.

The script builds a synthetic 3D scalar field similar to a Poisson/heat
simulation result, writes a ParaView-readable VTK time series, and renders two
off-screen screenshots:

  1. an orthogonal slice view of the scalar field
  2. an isosurface view

Run from week13:

    python simulation_visualization_demo.py --output-dir outputs/simulation_demo

Open the generated ``poisson_demo.pvd`` in ParaView to inspect the time series.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pyvista as pv


def configure_off_screen() -> None:
    """Use deterministic off-screen settings that work in headless sessions."""
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("MESA_SHADER_CACHE_DISABLE", "true")
    pv.OFF_SCREEN = True
    pv.global_theme.background = "white"
    pv.global_theme.font.color = "black"
    pv.global_theme.cmap = "viridis"


def make_coordinates(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return one-dimensional coordinates on [-1, 1]^3."""
    axis = np.linspace(-1.0, 1.0, n)
    return axis, axis.copy(), axis.copy()


def scalar_field(x: np.ndarray, y: np.ndarray, z: np.ndarray, time: float) -> np.ndarray:
    """Create a smooth 3D scalar field with moving source terms."""
    xg, yg, zg = np.meshgrid(x, y, z, indexing="ij")
    source_a = np.exp(-18.0 * ((xg - 0.35 * np.cos(time)) ** 2 + (yg + 0.25) ** 2 + zg**2))
    source_b = 0.65 * np.exp(-24.0 * ((xg + 0.35) ** 2 + (yg - 0.30 * np.sin(time)) ** 2 + (zg + 0.15) ** 2))
    background = 0.18 * np.sin(np.pi * xg) * np.cos(np.pi * yg) * np.cos(0.5 * np.pi * zg + time)
    return source_a - source_b + background


def vector_field_from_scalar(values: np.ndarray, spacing: tuple[float, float, float]) -> np.ndarray:
    """Return the negative gradient as a vector field for glyph experiments."""
    gx, gy, gz = np.gradient(values, *spacing, edge_order=2)
    vectors = np.stack((-gx, -gy, -gz), axis=-1)
    return np.ascontiguousarray(vectors.reshape(-1, 3, order="F"))


def make_image_data(
    values: np.ndarray,
    spacing: tuple[float, float, float],
    origin: tuple[float, float, float],
) -> pv.ImageData:
    """Convert a 3D NumPy scalar field to PyVista ImageData."""
    grid = pv.ImageData()
    grid.dimensions = values.shape
    grid.spacing = spacing
    grid.origin = origin
    grid.point_data["potential"] = np.ascontiguousarray(values.ravel(order="F"))
    grid.point_data["minus_gradient"] = vector_field_from_scalar(values, spacing)
    return grid


def write_pvd_index(entries: list[tuple[float, Path]], pvd_path: Path) -> None:
    """Write a minimal ParaView Data index for a VTK time series."""
    lines = [
        '<?xml version="1.0"?>',
        '<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">',
        '  <Collection>',
    ]
    for time_value, file_path in entries:
        lines.append(
            f'    <DataSet timestep="{time_value:.6g}" group="" part="0" file="{file_path.name}"/>'
        )
    lines.extend(["  </Collection>", "</VTKFile>", ""])
    pvd_path.write_text("\n".join(lines), encoding="utf-8")


def write_time_series(output_dir: Path, n: int, steps: int) -> tuple[list[Path], tuple[float, float]]:
    """Write VTI files and a PVD index; return generated files and scalar range."""
    output_dir.mkdir(parents=True, exist_ok=True)
    x, y, z = make_coordinates(n)
    spacing = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    origin = (float(x[0]), float(y[0]), float(z[0]))

    written: list[Path] = []
    pvd_entries: list[tuple[float, Path]] = []
    scalar_min = np.inf
    scalar_max = -np.inf

    for step in range(steps):
        time = 2.0 * np.pi * step / max(steps, 1)
        values = scalar_field(x, y, z, time)
        scalar_min = min(scalar_min, float(values.min()))
        scalar_max = max(scalar_max, float(values.max()))

        grid = make_image_data(values, spacing, origin)
        path = output_dir / f"poisson_demo_{step:04d}.vti"
        grid.save(path)
        written.append(path)
        pvd_entries.append((time, path))

    write_pvd_index(pvd_entries, output_dir / "poisson_demo.pvd")
    return written, (scalar_min, scalar_max)


def add_common_scene(plotter: pv.Plotter, title: str) -> None:
    """Apply shared camera, axes, and title settings."""
    plotter.add_text(title, position="upper_left", font_size=12, color="black")
    plotter.add_axes(line_width=2)
    plotter.show_grid(color="black", grid="back", location="outer")
    plotter.camera_position = [(2.6, -3.1, 2.2), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)]


def render_slice(grid: pv.ImageData, output_path: Path, clim: tuple[float, float]) -> None:
    """Render three orthogonal slices of the scalar field."""
    plotter = pv.Plotter(off_screen=True, window_size=(1200, 850))
    slices = grid.slice_orthogonal(x=0.0, y=0.0, z=0.0)
    plotter.add_mesh(
        slices,
        scalars="potential",
        cmap="coolwarm",
        clim=clim,
        scalar_bar_args={"title": "potential"},
    )
    add_common_scene(plotter, "Orthogonal slices of a 3D scalar field")
    plotter.screenshot(output_path)
    plotter.close()


def render_isosurface(grid: pv.ImageData, output_path: Path, clim: tuple[float, float]) -> None:
    """Render positive and negative isosurfaces."""
    plotter = pv.Plotter(off_screen=True, window_size=(1200, 850))
    contour = grid.contour(isosurfaces=[-0.20, 0.20], scalars="potential")
    plotter.add_mesh(
        contour,
        scalars="potential",
        cmap="coolwarm",
        clim=clim,
        smooth_shading=True,
        scalar_bar_args={"title": "potential"},
    )
    outline = grid.outline()
    plotter.add_mesh(outline, color="black", line_width=1)
    add_common_scene(plotter, "Isosurfaces: potential = +/- 0.20")
    plotter.screenshot(output_path)
    plotter.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/simulation_demo"))
    parser.add_argument("--grid-size", type=int, default=48)
    parser.add_argument("--steps", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.grid_size < 8:
        raise SystemExit("--grid-size must be at least 8")
    if args.steps < 1:
        raise SystemExit("--steps must be at least 1")

    configure_off_screen()
    files, scalar_range = write_time_series(args.output_dir, args.grid_size, args.steps)
    first_grid = pv.read(files[0])
    render_slice(first_grid, args.output_dir / "poisson_slice.png", scalar_range)
    render_isosurface(first_grid, args.output_dir / "poisson_isosurface.png", scalar_range)

    print(f"Wrote {len(files)} VTI files")
    print(f"Wrote {args.output_dir / 'poisson_demo.pvd'}")
    print(f"Wrote {args.output_dir / 'poisson_slice.png'}")
    print(f"Wrote {args.output_dir / 'poisson_isosurface.png'}")


if __name__ == "__main__":
    main()
