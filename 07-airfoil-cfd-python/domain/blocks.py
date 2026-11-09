"""The wind tunnel's Flow blocks: airfoil mask, lattice step and the polar readout."""

import math

import paperboat
from domain.forces import polars
from domain.airfoil import naca0012_mask


class Airfoil(paperboat.Block):
    """The NACA 0012 mask at the angle of attack on its input."""

    type, label, kind = "airfoil", "NACA 0012 Mask", "function"
    inputs = ["alpha"]
    outputs = ["alpha", "solid_fraction", "stalled"]

    def step(self, ctx, inputs) -> dict:
        alpha = float(inputs.get("alpha", 0.0))
        mask = naca0012_mask(80, 40, 28, 20, 46, alpha)
        return {
            "alpha": alpha,
            "solid_fraction": float(mask.mean()),
            "stalled": 1.0 if abs(alpha) > 14.0 else 0.0,
        }


class Inflow(paperboat.Block):
    """Free-stream speed and Reynolds number."""

    type, label, kind = "inflow", "Inflow Condition", "function"
    inputs = ["speed"]
    outputs = ["u", "reynolds"]

    def step(self, ctx, inputs) -> dict:
        u = max(1e-4, float(inputs.get("speed", 0.08)))
        # Lattice units: chord 90, nu = (tau - 0.5) / 3 with tau = 0.53.
        nu = (0.53 - 0.5) / 3.0
        return {"u": u, "reynolds": u * 90.0 / nu}


class LbmStep(paperboat.Block):
    """Advance the D2Q9 lattice by a few substeps and report convergence."""

    type, label = "lbm_step", "LBM Step (D2Q9)"
    inputs = ["alpha", "u"]
    outputs = ["steps", "residual", "max_speed"]
    params = {"substeps": 6}

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        self.last_log = -100

    def step(self, ctx, inputs) -> dict:
        tunnel = ctx.state
        alpha = float(inputs.get("alpha", tunnel.alpha))
        u = float(inputs.get("u", tunnel.speed))
        residual = tunnel.advance(alpha, u, int(self.params.get("substeps", 6)))
        if tunnel.steps - self.last_log >= 120:
            self.last_log = tunnel.steps
            ctx.log(f"LBM {tunnel.steps} steps, residual {residual:.2e}, max |u| {tunnel.lattice.max_speed():.3f}")
        return {
            "steps": float(tunnel.steps),
            "residual": residual,
            "max_speed": tunnel.lattice.max_speed(),
        }


class Forces(paperboat.Block):
    """Lift and drag coefficients, and the glide ratio."""

    type, label, kind = "forces", "Lift & Drag Polars", "probe"
    inputs = ["alpha", "u"]
    outputs = ["cl", "cd", "ld", "lift", "drag"]

    def step(self, ctx, inputs) -> dict:
        alpha = float(inputs.get("alpha", ctx.state.alpha))
        u = float(inputs.get("u", ctx.state.speed))
        c = polars(alpha, u)
        ctx.state.coefficients = c
        return {key: float(value) for key, value in c.items()}


BLOCKS = [Airfoil, Inflow, LbmStep, Forces]
