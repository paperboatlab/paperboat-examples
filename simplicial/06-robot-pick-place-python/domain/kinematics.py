"""Forward and analytical inverse kinematics for the 3-DOF arm.

Joints: theta1 yaw about +y at the base, theta2 shoulder pitch from vertical, theta3 elbow
pitch. The arm is a 2-link planar chain in the plane the base yaw selects.
"""

import math

LINK1 = 1.6
LINK2 = 1.2
BASE_HEIGHT = 1.05

HOME = (0.0, 2.15, 0.0)
PICK = (-1.15, 0.78, -0.85)
BIN_A = (1.30, 0.92, -0.46)
BIN_B = (1.30, 0.92, 0.84)


def forward(theta: tuple[float, float, float]) -> tuple[float, float, float]:
    """Tool-centre point from the three joint angles (radians)."""
    t1, t2, t3 = theta
    r = LINK1 * math.sin(t2) + LINK2 * math.sin(t2 + t3)
    y = BASE_HEIGHT + LINK1 * math.cos(t2) + LINK2 * math.cos(t2 + t3)
    return r * math.sin(t1), y, r * math.cos(t1)


def inverse(point: tuple[float, float, float], elbow: float = 1.0) -> tuple[float, float, float]:
    """Joint angles for a tool-centre point, with the elbow up or down.

    Raises ValueError when the point is out of reach. The yaw is continuous in the point;
    the two pitch angles are the standard two-link solution from the vertical.
    """
    x, y, z = point
    radius = math.hypot(x, z)
    yaw = math.atan2(x, z)
    height = y - BASE_HEIGHT
    cosine = (radius * radius + height * height - LINK1 * LINK1 - LINK2 * LINK2) / (2 * LINK1 * LINK2)
    if cosine < -1.0 or cosine > 1.0:
        raise ValueError(f"target {point} is outside the arm's reach")
    elbow_angle = elbow * math.acos(max(-1.0, min(1.0, cosine)))
    shoulder = math.atan2(radius, height) - math.atan2(
        LINK2 * math.sin(elbow_angle), LINK1 + LINK2 * math.cos(elbow_angle)
    )
    return yaw, shoulder, elbow_angle


def quintic(t: float) -> float:
    """S-curve progress: zero velocity and acceleration at both ends."""
    s = min(max(t, 0.0), 1.0)
    return 10 * s**3 - 15 * s**4 + 6 * s**5


def wrap(angle: float) -> float:
    """The same angle in (-pi, pi]."""
    return math.remainder(angle, 2 * math.pi)


def shortest_delta(start: float, end: float) -> float:
    return wrap(end - start)
