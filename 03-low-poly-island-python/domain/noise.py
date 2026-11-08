"""Procedural 2D Simplex Noise with multi-octave fractal harmonics.

Pure Python, deterministic, seeded, with zero external dependencies.
"""

import math
import random

# Skewing and unskewing factors for 2D Simplex Noise
F2 = 0.5 * (math.sqrt(3.0) - 1.0)
G2 = (3.0 - math.sqrt(3.0)) / 6.0

GRAD2 = [
    (1, 1), (-1, 1), (1, -1), (-1, -1),
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (-1, 1), (1, -1), (-1, -1)
]


def make_perm_table(seed: int) -> list[int]:
    """Generate a 512-entry permutation table seeded by `seed`."""
    rng = random.Random(seed)
    p = list(range(256))
    rng.shuffle(p)
    return p + p


def simplex2d(x: float, y: float, perm: list[int]) -> float:
    """Evaluate 2D Simplex Noise at (x, y) with permutation table `perm`.

    Returns value roughly in [-1.0, 1.0].
    """
    # Skew the input space to determine which simplex cell we're in
    s = (x + y) * F2
    i = math.floor(x + s)
    j = math.floor(y + s)

    # Unskew the cell origin back to (x, y) space
    t = (i + j) * G2
    x0 = x - (i - t)
    y0 = y - (j - t)

    # Determine which simplex (triangle) we are in
    if x0 > y0:
        i1, j1 = 1, 0  # lower triangle, XY order: (0,0)->(1,0)->(1,1)
    else:
        i1, j1 = 0, 1  # upper triangle, YX order: (0,0)->(0,1)->(1,1)

    # Offsets for middle and last corner
    x1 = x0 - i1 + G2
    y1 = y0 - j1 + G2
    x2 = x0 - 1.0 + 2.0 * G2
    y2 = y0 - 1.0 + 2.0 * G2

    # Wrap indices
    ii = i & 255
    jj = j & 255

    # Calculate contribution from the three corners
    n0, n1, n2 = 0.0, 0.0, 0.0

    t0 = 0.5 - x0 * x0 - y0 * y0
    if t0 > 0:
        t0 *= t0
        gi0 = perm[ii + perm[jj]] % 12
        gx0, gy0 = GRAD2[gi0]
        n0 = t0 * t0 * (gx0 * x0 + gy0 * y0)

    t1 = 0.5 - x1 * x1 - y1 * y1
    if t1 > 0:
        t1 *= t1
        gi1 = perm[ii + i1 + perm[jj + j1]] % 12
        gx1, gy1 = GRAD2[gi1]
        n1 = t1 * t1 * (gx1 * x1 + gy1 * y1)

    t2 = 0.5 - x2 * x2 - y2 * y2
    if t2 > 0:
        t2 *= t2
        gi2 = perm[ii + 1 + perm[jj + 1]] % 12
        gx2, gy2 = GRAD2[gi2]
        n2 = t2 * t2 * (gx2 * x2 + gy2 * y2)

    # Scale to [-1, 1] range (factor 70.0 is standard for 2D simplex)
    return 70.0 * (n0 + n1 + n2)


def octave_noise(
    x: float,
    y: float,
    seed: int = 42,
    octaves: int = 4,
    persistence: float = 0.5,
    lacunarity: float = 2.0,
    scale: float = 2.5,
) -> float:
    """Compute normalized fractal Brownian motion (fBm) noise at (x, y).

    Returns value normalized in [0.0, 1.0].
    """
    perm = make_perm_table(seed)
    total = 0.0
    frequency = 1.0 / max(scale, 1e-6)
    amplitude = 1.0
    max_val = 0.0

    for _ in range(max(1, octaves)):
        n = simplex2d(x * frequency, y * frequency, perm)
        total += n * amplitude
        max_val += amplitude
        amplitude *= persistence
        frequency *= lacunarity

    # Normalize from [-max_val, max_val] to [0.0, 1.0]
    return (total / max_val + 1.0) / 2.0
