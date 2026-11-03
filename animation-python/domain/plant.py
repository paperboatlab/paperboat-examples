"""The animation plant: one actor (a box with a nose) with a position, an orientation and a
uniform size. Move, Rotate and Scale steps change it; Pose reads it."""

import math

from paperboat import DomainState

BODY = [1.0, 0.5, 0.6]  # actor box size; it faces +x, its nose shows which way


# --- The actor: a position, an orientation (quaternion w, x, y, z) and a uniform size.

def quat_mul(a: list[float], b: list[float]) -> list[float]:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return [
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ]


def quat_from_vector(v: list[float]) -> list[float]:
    """Rotation by |v| radians about v."""
    angle = math.sqrt(sum(c * c for c in v))
    if angle < 1e-12:
        return [1.0, 0.0, 0.0, 0.0]
    s = math.sin(angle / 2) / angle
    return [math.cos(angle / 2), v[0] * s, v[1] * s, v[2] * s]


def rotate(q: list[float], v: list[float]) -> list[float]:
    w, x, y, z = quat_mul(quat_mul(q, [0.0, *v]), [q[0], -q[1], -q[2], -q[3]])
    return [x, y, z]


def euler_xyz(q: list[float]) -> list[float]:
    """Quaternion → three.js "XYZ" Euler angles (the protocol's `rot`)."""
    w, x, y, z = q
    m11, m12, m13 = 1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)
    m22, m23 = 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)
    m32, m33 = 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)
    ry = math.asin(max(-1.0, min(1.0, m13)))
    if abs(m13) < 0.9999999:
        return [math.atan2(-m23, m33), ry, math.atan2(-m12, m11)]
    return [math.atan2(m32, m22), ry, 0.0]


class Actor(DomainState):
    def __init__(self) -> None:
        self.pos = [-1.0, 0.0, 1.0]  # on the ground, at the box's centre
        self.q = [1.0, 0.0, 0.0, 0.0]
        self.size = 1.0

    def heading(self) -> float:
        """Degrees about +y from +x, counter-clockwise seen from above."""
        f = rotate(self.q, [1.0, 0.0, 0.0])
        return math.degrees(math.atan2(-f[2], f[0]))

    def entities(self) -> list[dict]:
        s, rot = self.size, euler_xyz(self.q)
        centre = [self.pos[0], self.pos[1] + BODY[1] / 2 * s, self.pos[2]]
        nose = rotate(self.q, [BODY[0] / 2 * s, 0.05 * s, 0.0])
        return [
            {"id": "body", "shape": "box", "pos": centre, "size": BODY, "rot": rot, "scale": [s, s, s], "color": "#2f5d62"},
            {"id": "nose", "shape": "sphere", "pos": [c + n for c, n in zip(centre, nose)], "size": [0.15, 0, 0],
             "scale": [s, s, s], "color": "#c2410c"},
        ]
