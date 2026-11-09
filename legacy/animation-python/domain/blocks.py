"""The animation domain's own blocks: three timed steps that change the actor over
`seconds`, a probe that reads it, and Spin, a signal block that turns it while it runs.
Class attributes define each block (the palette has them without the descriptor listing
them); the methods are what the engine calls.

Move, Rotate and Scale are paperboat.Timed steps: the engine runs the timing (seconds, the
optional `curve` input, the `progress` output) and calls advance(ctx, start, end) to move
the work between two points of its progress. Each block only says what that means.
"""

import math

import paperboat

from .state import quat_from_vector, quat_mul, rotate


class Tween(paperboat.Timed):
    def begin(self, ctx, inputs) -> None:
        self.actor = ctx.state  # the run's Actor (domain/state.py)

    def advance(self, ctx, start: float, end: float) -> None:
        self.apply(end - start)

    def apply(self, share: float) -> None:
        raise NotImplementedError


class Move(Tween):
    """Moves the actor by (dx, dy, dz) in its own frame."""

    type, label = "move", "Move"
    params = {"dx": 2, "dy": 0, "dz": 0, "seconds": 1}

    def apply(self, share: float) -> None:
        d = rotate(self.actor.q, [self.params["dx"] * share, self.params["dy"] * share, self.params["dz"] * share])
        self.actor.pos = [a + b for a, b in zip(self.actor.pos, d)]


class Rotate(Tween):
    """Turns the actor by x, y, z degrees about its own axes."""

    type, label = "rotate", "Rotate"
    params = {"x": 0, "y": 90, "z": 0, "seconds": 1}

    def apply(self, share: float) -> None:
        v = [math.radians(self.params[k]) * share for k in ("x", "y", "z")]
        self.actor.q = quat_mul(self.actor.q, quat_from_vector(v))  # about its own axes


class Scale(Tween):
    """Grows or shrinks the actor to `to` times its size."""

    type, label = "scale", "Scale"
    params = {"to": 1.5, "seconds": 0.5}

    def begin(self, ctx, inputs) -> None:
        super().begin(ctx, inputs)
        self.start = self.actor.size

    def apply(self, share: float) -> None:
        self.actor.size += (self.params["to"] - self.start) * share


class Pose(paperboat.Block):
    """The actor's position, heading (degrees about +y) and size."""

    type, label, kind = "pose", "Pose", "probe"
    outputs = ["x", "y", "z", "heading", "size"]

    def step(self, ctx, inputs) -> dict:
        a = ctx.state
        return {"x": a.pos[0], "y": a.pos[1], "z": a.pos[2], "heading": a.heading(), "size": a.size}


class Spin(paperboat.Block):
    """A signal block, not a step: while it runs it turns the actor about its own y axis at
    `rate` degrees per second. Put it in a story group to spin for the story's seconds."""

    type, label, kind = "spin", "Spin", "source"
    inputs = ["rate"]

    def step(self, ctx, inputs) -> dict:
        rate = inputs.get("rate", 0.0)
        if rate:
            ctx.state.q = quat_mul(ctx.state.q, quat_from_vector([0.0, math.radians(rate) * ctx.dt, 0.0]))
        return {}


BLOCKS = [Move, Rotate, Scale, Pose, Spin]
