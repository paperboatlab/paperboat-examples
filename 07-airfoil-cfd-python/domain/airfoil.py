"""NACA 0012 geometry: a solid mask for the lattice and an outline for the scene."""

import math

import numpy as np


def _thickness(x: np.ndarray) -> np.ndarray:
    """NACA 0012 half-thickness at chord fraction x (0..1)."""
    x = np.clip(x, 0.0, 1.0)
    return 5 * 0.12 * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )


def naca0012_mask(nx: int, ny: int, cx: float, cy: float, chord: float, alpha_deg: float) -> np.ndarray:
    """True inside the rotated NACA 0012 profile on an (nx, ny) grid."""
    xs, ys = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
    x = (xs - cx) / chord
    y = (ys - cy) / chord
    angle = math.radians(alpha_deg)
    cos, sin = math.cos(-angle), math.sin(-angle)
    xr = x * cos - y * sin
    yr = x * sin + y * cos
    half = _thickness(xr)
    return (xr >= 0.0) & (xr <= 1.0) & (np.abs(yr) <= half)


def naca0012_outline(count: int = 24) -> list[tuple[float, float]]:
    """Points along the profile in chord fractions: upper surface then lower, TE to LE."""
    x = np.linspace(1.0, 0.0, count)
    half = _thickness(x)
    upper = list(zip(x.tolist(), np.maximum(half, 0.0).tolist()))
    lower = list(zip(x.tolist(), (-np.maximum(half, 0.0)).tolist()))
    return upper + lower
