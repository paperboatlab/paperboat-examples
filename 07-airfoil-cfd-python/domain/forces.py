"""Lift and drag polars for a NACA 0012, including stall past 14 degrees.

The lattice supplies the flow field on the Station; these polars give stable, readable
coefficients for the Board while the field is still developing. They follow the usual
linear lift slope with a stall break and a quadratic drag rise.
"""

import math

STALL_DEG = 14.0
LIFT_SLOPE = 2 * math.pi * 0.9


def polars(alpha_deg: float, speed: float) -> dict:
    alpha = math.radians(alpha_deg)
    stall = math.radians(STALL_DEG)
    if abs(alpha) <= stall:
        cl = LIFT_SLOPE * math.sin(alpha)
    else:  # past the stall break the lift falls away quickly
        peak = LIFT_SLOPE * math.sin(stall)
        beyond = max(0.0, abs(alpha) - stall)
        cl = math.copysign(peak * (1.0 - 0.45 * beyond / (math.pi / 2 - stall)), alpha)
    cd = 0.008 + 0.012 * (abs(alpha) / stall) ** 2 + 0.9 * math.sin(alpha) ** 2
    if abs(alpha) > stall:
        cd += 0.9 * (abs(alpha) - stall) ** 2
    ld = cl / cd if abs(cd) > 1e-9 else 0.0
    q = 0.5 * 1.0 * max(speed, 1e-6) ** 2
    return {"cl": cl, "cd": cd, "ld": ld, "lift": q * cl, "drag": q * cd}
