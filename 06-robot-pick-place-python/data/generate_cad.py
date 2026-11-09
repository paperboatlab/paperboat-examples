"""Generate the palletizer's CAD meshes (binary STL) from parametric primitives.

The meshes are the tutorial's CAD stand-in for an ABB IRB 460 palletizer: a cast base,
turret, two arms and a fork. Run this script after changing a dimension:

    python3 data/generate_cad.py

It writes data/cad/*.stl next to the backend; the Python example loads them with
domain/stl.py and sends them as Station mesh entities.
"""

import math
import struct
from pathlib import Path

OUT = Path(__file__).with_name("cad")
OUT.mkdir(exist_ok=True)

Tri = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


def box(x0: float, y0: float, z0: float, x1: float, y1: float, z1: float) -> list[Tri]:
    p = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    quads = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    out: list[Tri] = []
    for a, b, c, d in quads:
        out.append((p[a], p[b], p[c]))
        out.append((p[a], p[c], p[d]))
    return out


def cylinder(cx: float, cy: float, cz: float, radius: float, height: float, segments: int = 24) -> list[Tri]:
    """A cylinder along +y, centred at (cx, cz)."""
    out: list[Tri] = []
    ring = [
        (cx + radius * math.cos(2 * math.pi * i / segments), cz + radius * math.sin(2 * math.pi * i / segments))
        for i in range(segments)
    ]
    for i in range(segments):
        x0, z0 = ring[i]
        x1, z1 = ring[(i + 1) % segments]
        out.append(((x0, cy, z0), (x1, cy, z1), (x1, cy + height, z1)))
        out.append(((x0, cy, z0), (x1, cy + height, z1), (x0, cy + height, z0)))
        out.append(((cx, cy, cz), (x1, cy, z1), (x0, cy, z0)))
        out.append(((cx, cy + height, cz), (x0, cy + height, z0), (x1, cy + height, z1)))
    return out


def write_stl(path: Path, triangles: list[Tri]) -> None:
    with path.open("wb") as file:
        file.write(b"Paperboat palletizer CAD".ljust(80, b"\0"))
        file.write(struct.pack("<I", len(triangles)))
        for a, b, c in triangles:
            ux, uy, uz = (b[i] - a[i] for i in range(3))
            vx, vy, vz = (c[i] - a[i] for i in range(3))
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            file.write(struct.pack("<3f", nx / length, ny / length, nz / length))
            for point in (a, b, c):
                file.write(struct.pack("<3f", *point))
            file.write(struct.pack("<H", 0))


# Base: a cast plinth and the fixed column the turret turns on.
base = box(-0.58, 0.0, -0.58, 0.58, 0.18, 0.58) + box(-0.36, 0.18, -0.36, 0.36, 0.70, 0.36)
write_stl(OUT / "base.stl", base)

# Turret: the rotating housing, with a shoulder bearing.
turret = box(-0.46, 0.0, -0.46, 0.46, 0.34, 0.46) + cylinder(0.0, 0.34, 0.0, 0.22, 0.16)
write_stl(OUT / "turret.stl", turret)

# Arm 1: a tapered box along +y with a bearing at the shoulder.
arm1 = box(-0.09, 0.12, -0.09, 0.09, 1.60, 0.09) + cylinder(0.0, 0.0, 0.0, 0.13, 0.12)
write_stl(OUT / "arm1.stl", arm1)

# Arm 2: a slimmer box along +y with its elbow bearing.
arm2 = box(-0.07, 0.08, -0.07, 0.07, 1.20, 0.07) + cylinder(0.0, 0.0, 0.0, 0.10, 0.10)
write_stl(OUT / "arm2.stl", arm2)

# Fork: the wrist plate and two tines extending along -z.
fork = box(-0.24, -0.05, -0.12, 0.24, 0.05, 0.12)
fork += box(-0.30, -0.02, -0.58, -0.18, 0.02, -0.12)
fork += box(0.18, -0.02, -0.58, 0.30, 0.02, -0.12)
write_stl(OUT / "fork.stl", fork)

for name in ("base", "turret", "arm1", "arm2", "fork"):
    print(name, (OUT / f"{name}.stl").stat().st_size, "bytes")
