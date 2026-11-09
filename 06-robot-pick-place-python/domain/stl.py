"""A tiny binary/ASCII STL reader for the palletizer's CAD parts.

It returns one flat vertex list (x, y, z each) and one flat index list (three per triangle),
the shape a Paperboat mesh entity takes. No third-party CAD library is needed at run time.
"""

from pathlib import Path
import re
import struct

_CACHE: dict[Path, tuple[list[float], list[int]]] = {}


def _binary(path: Path) -> tuple[list[float], list[int]] | None:
    data = path.read_bytes()
    if len(data) < 84:
        return None
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        return None
    vertices: list[float] = []
    indices: list[int] = []
    for triangle in range(count):
        base = 84 + triangle * 50
        # Skip the facet normal (3 floats); then three vertices (3 floats each).
        for corner in range(3):
            x, y, z = struct.unpack_from("<3f", data, base + 12 + corner * 12)
            vertices.extend((x, y, z))
            indices.append(len(indices))
    return vertices, indices


def _ascii(path: Path) -> tuple[list[float], list[int]]:
    vertices: list[float] = []
    indices: list[int] = []
    for line in path.read_text(errors="ignore").splitlines():
        match = re.match(r"\s*vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)", line)
        if match:
            vertices.extend(float(value) for value in match.groups())
            indices.append(len(indices))
    return vertices, indices


def load(path: Path) -> tuple[list[float], list[int]]:
    """Load an STL once; the same arrays go out on every full scene."""
    path = path.resolve()
    if path not in _CACHE:
        parsed = _binary(path) if path.suffix.lower() == ".stl" else None
        _CACHE[path] = parsed if parsed and parsed[0] else _ascii(path)
    return _CACHE[path]
