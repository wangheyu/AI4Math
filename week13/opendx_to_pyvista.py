#!/usr/bin/env python3
"""Utilities for using OpenDX sample data with PyVista.

The repository keeps a small subset of OpenDX sample data in ``opendx_data``.
PyVista does not read OpenDX ``.dx`` files directly, so this module implements
the limited readers needed by the Week 13 teaching examples:

- regular OpenDX grids with ASCII or inline big-endian binary arrays
- OpenDX ``.general`` headers for MRI and Colorado elevation samples
- a textured Colorado terrain helper

The functions return PyVista data sets and can be imported from notebooks.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("MESA_SHADER_CACHE_DISABLE", "true")

import pyvista as pv


DATA_DIR = Path(__file__).with_name("opendx_data")


def _numbers(text: str) -> tuple[float, ...]:
    return tuple(float(item) for item in text.split())


def _point_order_indices(counts: tuple[int, ...]) -> np.ndarray:
    """Return indices converting OpenDX point order to VTK point order."""
    return np.arange(int(np.prod(counts))).reshape(counts, order="C").ravel(order="F")


def _parse_regular_grid_header(text: str) -> tuple[tuple[int, int, int], np.ndarray, np.ndarray]:
    counts_match = re.search(r"gridpositions\s+counts\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)", text)
    if not counts_match:
        raise ValueError("Only 3D regular OpenDX gridpositions are supported")
    counts = tuple(int(value) for value in counts_match.groups())

    origin_match = re.search(r"origin\s+([^\n]+)", text)
    if not origin_match:
        raise ValueError("Missing OpenDX grid origin")
    origin = np.array(_numbers(origin_match.group(1)), dtype=float)

    delta_lines = re.findall(r"delta\s+([^\n]+)", text)
    if len(delta_lines) < 3:
        raise ValueError("Missing OpenDX grid deltas")
    deltas = np.array([_numbers(line) for line in delta_lines[:3]], dtype=float)
    return counts, origin, deltas


def _field_name(text: str, fallback: str) -> str:
    name_match = re.search(r'attribute\s+"name"\s+string\s+"([^"]+)"', text)
    if name_match:
        return name_match.group(1).replace(" ", "_")
    object_match = re.search(r'object\s+"([^"]+)"\s+class\s+field', text)
    if object_match:
        return object_match.group(1).replace(" ", "_")
    return fallback


def _structured_grid(counts: tuple[int, int, int], origin: np.ndarray, deltas: np.ndarray) -> pv.StructuredGrid:
    i, j, k = np.meshgrid(
        np.arange(counts[0], dtype=float),
        np.arange(counts[1], dtype=float),
        np.arange(counts[2], dtype=float),
        indexing="ij",
    )
    x = origin[0] + deltas[0, 0] * i + deltas[1, 0] * j + deltas[2, 0] * k
    y = origin[1] + deltas[0, 1] * i + deltas[1, 1] * j + deltas[2, 1] * k
    z = origin[2] + deltas[0, 2] * i + deltas[1, 2] * j + deltas[2, 2] * k
    return pv.StructuredGrid(x, y, z)


def _array_metadata(text: str) -> tuple[str, int, int, int]:
    match = re.search(
        r"class\s+array(?:\s+type\s+([a-zA-Z]+))?"
        r"(?:\s+rank\s+([0-9]+)(?:\s+shape\s+([0-9]+))?)?"
        r"\s+items\s+([0-9]+)",
        text,
    )
    if not match:
        raise ValueError("Could not parse OpenDX array metadata")
    data_type = match.group(1) or "float"
    rank = int(match.group(2) or 0)
    shape = int(match.group(3) or 1)
    items = int(match.group(4))
    components = shape if rank == 1 else 1
    return data_type, rank, components, items


def read_regular_dx(path: Path | str, field_name: str | None = None) -> pv.StructuredGrid:
    """Read a regular OpenDX grid into a PyVista ``StructuredGrid``.

    This supports the OpenDX sample files used in the teaching notebook,
    including ASCII ``data follows`` arrays and inline big-endian binary arrays.
    """
    path = Path(path)
    payload = path.read_bytes()

    if b"data follows" in payload:
        text = payload.decode("ascii", errors="ignore")
        counts, origin, deltas = _parse_regular_grid_header(text)
        data_type, _rank, components, items = _array_metadata(text)
        if data_type != "float":
            raise ValueError(f"Unsupported ASCII OpenDX data type: {data_type}")

        start = text.index("data follows") + len("data follows")
        end_match = re.search(r'\n\s*attribute\s+"dep"', text[start:])
        if not end_match:
            raise ValueError("Could not find end of ASCII OpenDX data array")
        values = np.fromstring(text[start : start + end_match.start()], sep=" ", dtype=float)
    else:
        end_marker = b"\nend\n"
        binary_offset = payload.find(end_marker)
        if binary_offset < 0:
            raise ValueError("Could not find OpenDX binary payload marker")
        binary_offset += len(end_marker)
        text = payload[:binary_offset].decode("ascii", errors="ignore")
        counts, origin, deltas = _parse_regular_grid_header(text)
        data_type, _rank, components, items = _array_metadata(text)

        if data_type != "float":
            raise ValueError(f"Unsupported binary OpenDX data type: {data_type}")
        dtype = np.dtype(">f4")
        nvalues = items * components
        nbytes = nvalues * dtype.itemsize
        values = np.frombuffer(payload[binary_offset : binary_offset + nbytes], dtype=dtype, count=nvalues)

    expected = int(np.prod(counts)) * components
    if values.size != expected or items != int(np.prod(counts)):
        raise ValueError(f"OpenDX array size mismatch: expected {expected}, got {values.size}")

    indices = _point_order_indices(counts)
    grid = _structured_grid(counts, origin, deltas)
    name = field_name or _field_name(text, path.stem)
    if components == 1:
        grid.point_data[name] = values[indices]
    else:
        vectors = values.reshape((items, components), order="C")
        grid.point_data[name] = vectors[indices]
        grid.point_data[f"{name}_magnitude"] = np.linalg.norm(vectors[indices], axis=1)
    return grid


def _read_general(path: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def _grid_counts(value: str) -> tuple[int, ...]:
    return tuple(int(item) for item in re.split(r"\s*x\s*", value.replace(" ", "")) if item)


def load_mri(data_dir: Path | str = DATA_DIR) -> pv.ImageData:
    """Load the OpenDX MRI sample as ``ImageData`` with an ``intensity`` array."""
    data_dir = Path(data_dir)
    metadata = _read_general(data_dir / "mri.general")
    counts = _grid_counts(metadata["grid"])
    if len(counts) != 3:
        raise ValueError("MRI sample must be a 3D grid")

    positions = [float(item.strip()) for item in metadata["positions"].split(",")]
    origin = (positions[0], positions[2], positions[4])
    spacing = (positions[1], positions[3], positions[5])
    raw = np.fromfile(data_dir / metadata["file"], dtype=">u2", count=int(np.prod(counts)))
    values = raw.reshape(counts, order="C")

    grid = pv.ImageData(dimensions=counts, spacing=spacing, origin=origin)
    grid.point_data["intensity"] = values.ravel(order="F")
    return grid


def load_colorado_terrain(
    data_dir: Path | str = DATA_DIR,
    z_scale: float = 4.0,
) -> tuple[pv.StructuredGrid, pv.Texture]:
    """Load Colorado image/elevation data as a textured terrain surface."""
    data_dir = Path(data_dir)
    metadata = _read_general(data_dir / "colo_elev.general")
    counts = _grid_counts(metadata["grid"])
    if len(counts) != 2:
        raise ValueError("Colorado elevation sample must be a 2D grid")
    header_match = re.search(r"bytes\s+([0-9]+)", metadata.get("header", "bytes 0"))
    header_bytes = int(header_match.group(1)) if header_match else 0

    raw = np.fromfile(data_dir / metadata["file"], dtype=np.uint8)
    elevation = raw[header_bytes : header_bytes + int(np.prod(counts))].reshape(counts, order="C")

    x, y = np.meshgrid(np.arange(counts[0]), np.arange(counts[1]), indexing="ij")
    z = elevation.astype(float) * z_scale
    terrain = pv.StructuredGrid(x.astype(float), y.astype(float), z)
    terrain.point_data["elevation"] = elevation.ravel(order="F")

    u, v = np.meshgrid(np.linspace(0.0, 1.0, counts[0]), np.linspace(0.0, 1.0, counts[1]), indexing="ij")
    terrain.active_texture_coordinates = np.column_stack((u.ravel(order="F"), v.ravel(order="F")))
    texture = pv.read_texture(data_dir / "colorado.tiff")
    return terrain, texture


def load_watermolecule(data_dir: Path | str = DATA_DIR) -> pv.StructuredGrid:
    """Load the water molecule electron-density sample."""
    return read_regular_dx(Path(data_dir) / "watermolecule.dx", field_name="electron_density")


def load_storm_cloud_and_wind(data_dir: Path | str = DATA_DIR) -> pv.StructuredGrid:
    """Load cloud-water scalar data and attach wind vectors on the same grid."""
    data_dir = Path(data_dir)
    cloud = read_regular_dx(data_dir / "cloudwater.dx", field_name="cloudwater")
    wind = read_regular_dx(data_dir / "wind.dx", field_name="wind")
    cloud.point_data["wind"] = wind.point_data["wind"]
    cloud.point_data["wind_magnitude"] = wind.point_data["wind_magnitude"]
    return cloud


def main() -> None:
    """Print a compact summary of all teaching data sets."""
    datasets = {
        "colorado_terrain": load_colorado_terrain()[0],
        "watermolecule": load_watermolecule(),
        "storm_cloud_wind": load_storm_cloud_and_wind(),
        "mri": load_mri(),
    }
    for name, dataset in datasets.items():
        print(f"{name}: {dataset.__class__.__name__}, points={dataset.n_points}, arrays={list(dataset.point_data)}")


if __name__ == "__main__":
    main()
