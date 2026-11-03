"""The mass-spring domain's own blocks, defined by their class attributes. They reach the
mass through ctx.state, the run's MassSpring (domain/plant.py)."""

import paperboat


class Force(paperboat.Block):
    """F1: pushes the mass with its `force` input."""

    type, label, kind = "F1", "F1 · Force on mass", "source"
    inputs = ["force"]

    def step(self, ctx, inputs) -> dict:
        ctx.state.force += inputs.get("force", 0.0)
        return {}


class Probe(paperboat.Block):
    """P1: reads the mass's position and velocity."""

    type, label, kind = "P1", "P1 · Mass probe", "probe"
    outputs = ["x", "v"]

    def step(self, ctx, inputs) -> dict:
        return {"x": ctx.state.x, "v": ctx.state.v}


BLOCKS = [Force, Probe]
