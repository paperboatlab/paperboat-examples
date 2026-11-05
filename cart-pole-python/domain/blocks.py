"""Cart-pole domain blocks."""

import paperboat


class Controller(paperboat.Block):
    type, label, kind = "Controller", "Controller", "source"
    inputs = ["theta", "omega"]
    outputs = ["force"]

    def step(self, ctx, inputs) -> dict:
        theta = inputs.get("theta", 0.0)
        omega = inputs.get("omega", 0.0)
        force = -40.0 * theta - 5.0 * omega
        return {"force": force}


class Probe(paperboat.Block):
    type, label, kind = "P1", "P1 · Probe", "probe"
    outputs = ["x", "theta", "omega"]

    def step(self, ctx, inputs) -> dict:
        return {"x": ctx.state.x, "theta": ctx.state.theta, "omega": ctx.state.omega}


class Force(paperboat.Block):
    type, label, kind = "Force", "Force on cart", "source"
    inputs = ["force"]

    def step(self, ctx, inputs) -> dict:
        ctx.state.force += inputs.get("force", 0.0)
        return {}


BLOCKS = [Controller, Probe, Force]
