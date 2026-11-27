"""The wind tunnel's Flow blocks: airfoil mask, lattice step and the polar readout.

The lattice step and the polars act on the tunnel, the station object (domain/state.py), through
`current()`; station.py registers each block with its ports and params.
"""

import paperboat_runtime as pb

from domain.airfoil import naca0012_mask
from domain.forces import polars
from domain.state import current


class Airfoil:
    """The NACA 0012 mask at the angle of attack on its input."""

    def step(self, ctx, inputs) -> dict:
        alpha = float(inputs.get("alpha", 0.0))
        mask = naca0012_mask(80, 40, 28, 20, 46, alpha)
        return {
            "alpha": alpha,
            "solid_fraction": float(mask.mean()),
            "stalled": 1.0 if abs(alpha) > 14.0 else 0.0,
        }


class Inflow:
    """Free-stream speed and Reynolds number."""

    def step(self, ctx, inputs) -> dict:
        u = max(1e-4, float(inputs.get("speed", 0.08)))
        # Lattice units: chord 90, nu = (tau - 0.5) / 3 with tau = 0.53.
        nu = (0.53 - 0.5) / 3.0
        return {"u": u, "reynolds": u * 90.0 / nu}


class LbmStep:
    """Advance the D2Q9 lattice by a few substeps and report convergence."""

    def __init__(self, substeps: float = 6) -> None:
        self.substeps = int(substeps)
        self.last_log = -100

    def step(self, ctx, inputs) -> dict:
        tunnel = current()
        alpha = float(inputs.get("alpha", tunnel.alpha))
        u = float(inputs.get("u", tunnel.speed))
        residual = tunnel.advance(alpha, u, self.substeps)
        if tunnel.steps - self.last_log >= 120:
            self.last_log = tunnel.steps
            pb.log(f"LBM {tunnel.steps} steps, residual {residual:.2e}, max |u| {tunnel.lattice.max_speed():.3f}")
        return {
            "steps": float(tunnel.steps),
            "residual": residual,
            "max_speed": tunnel.lattice.max_speed(),
        }


class Forces:
    """Lift and drag coefficients, and the glide ratio."""

    def step(self, ctx, inputs) -> dict:
        tunnel = current()
        alpha = float(inputs.get("alpha", tunnel.alpha))
        u = float(inputs.get("u", tunnel.speed))
        c = polars(alpha, u)
        tunnel.coefficients = c
        return {key: float(value) for key, value in c.items()}

