"""The runner domain's own blocks: probes on the game and the two things the runner can do.
Each class's attributes define the block (the palette has them without the descriptor
listing them); its step() is what the engine calls."""

import paperboat


class Runner(paperboat.Block):
    """The runner's height, vertical speed and current height (lower while ducking)."""

    type, label, kind = "runner", "Runner", "probe"
    outputs = ["y", "vy", "height"]

    def step(self, ctx, inputs) -> dict:
        game = ctx.state  # the run's Game (domain/state.py)
        return {"y": game.y, "vy": game.vy, "height": game.h}


class NextCrate(paperboat.Block):
    """Distance from the runner's front to the next crate, and its height."""

    type, label, kind = "crate", "Next crate", "probe"
    outputs = ["dx", "height"]

    def step(self, ctx, inputs) -> dict:
        game = ctx.state  # the run's Game (domain/state.py)
        o = game.next_of(bar=False)
        return {"dx": game.dx(bar=False), "height": o.top if o else 0.0}


class NextBar(paperboat.Block):
    """Distance to the next overhead bar (negative while under it)."""

    type, label, kind = "bar", "Next bar", "probe"
    outputs = ["dx"]

    def step(self, ctx, inputs) -> dict:
        game = ctx.state  # the run's Game (domain/state.py)
        return {"dx": game.dx(bar=True)}


class Jump(paperboat.Block):
    """Jumps with `strength` m/s while `trigger` is high and the runner is on the ground."""

    type, label, kind = "jump", "Jump", "source"
    inputs = ["trigger"]
    params = {"strength": 10}

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        self.strength = params["strength"]

    def step(self, ctx, inputs) -> dict:
        game = ctx.state  # the run's Game (domain/state.py)
        if inputs.get("trigger", 0.0) > 0.5:
            game.jump_speed = self.strength
        return {}


class Duck(paperboat.Block):
    """Ducks while `hold` is high."""

    type, label, kind = "duck", "Duck", "source"
    inputs = ["hold"]

    def step(self, ctx, inputs) -> dict:
        game = ctx.state  # the run's Game (domain/state.py)
        game.duck = game.duck or inputs.get("hold", 0.0) > 0.5
        return {}


BLOCKS = [Runner, NextCrate, NextBar, Jump, Duck]

