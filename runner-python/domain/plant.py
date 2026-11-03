"""The runner game: a runner that jumps over crates and ducks under bars sliding at it."""

import random

from paperboat import DomainState

GRAVITY = -25.0
SPEED = 6.0  # obstacles slide toward the runner, m/s
N_OBSTACLES = 3
BAR_SHARE = 0.15  # share of obstacles that are overhead bars (duck under them): rare
BAR_BOTTOM, BAR_TOP = 0.55, 1.4  # a bar hangs in this height band: duck under it
RUNNER_X, RUNNER_W = 2.0, 0.5  # the runner is a box standing on y = 0
STAND_H, DUCK_H = 0.8, 0.45  # its height standing and ducking


class Obstacle:
    """A crate on the ground (jump it) or a bar overhead (duck it)."""

    def __init__(self, rng: random.Random, x: float) -> None:
        self.x, self.cleared = x, False  # x: left edge
        self.bar = rng.random() < BAR_SHARE
        if self.bar:
            self.w, self.bottom, self.top = rng.uniform(0.8, 1.4), BAR_BOTTOM, BAR_TOP
        else:
            self.w, self.bottom, self.top = rng.uniform(0.4, 0.8), 0.0, rng.uniform(0.5, 1.0)


class Game(DomainState):
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.y, self.vy, self.h = 0.0, 0.0, STAND_H
        # Written by the Jump and Duck blocks during a step, used and cleared by step().
        self.jump_speed: float | None = None
        self.duck = False
        self.crashed = False
        self.obstacles: list[Obstacle] = []
        x = 10.0
        for _ in range(N_OBSTACLES):
            self.obstacles.append(Obstacle(self.rng, x))
            x += self.gap()
        self.score = 0

    def gap(self) -> float:
        return self.rng.uniform(6.0, 11.0)

    def next_of(self, bar: bool) -> Obstacle | None:
        """The nearest obstacle of that kind not yet fully behind the runner."""
        ahead = [o for o in self.obstacles if o.bar == bar and o.x + o.w > RUNNER_X - RUNNER_W / 2]
        return min(ahead, key=lambda o: o.x, default=None)

    def dx(self, bar: bool) -> float:
        """Gap from the runner's front to the next obstacle of that kind (negative while passing it)."""
        o = self.next_of(bar)
        return o.x - (RUNNER_X + RUNNER_W / 2) if o else 99.0

    def on_ground(self) -> bool:
        return self.y <= 0.0

    def step(self, ctx) -> str | None:
        """Advance one step; a message when the runner hits an obstacle (ends the run)."""
        if self.advance(ctx.dt, self.jump_speed, self.duck):
            self.jump_speed, self.duck = None, False
            return None
        self.crashed = True
        return f"crashed after {self.score} cleared at t = {ctx.t:.1f} s"

    def summary(self) -> str | None:
        return None if self.crashed else f"made it! {self.score} obstacles cleared"

    def advance(self, dt: float, jump_speed: float | None, duck: bool) -> bool:
        """The game's own step; False when the runner hits an obstacle."""
        if jump_speed is not None and self.on_ground() and not duck:
            self.vy = jump_speed
        self.vy += GRAVITY * dt
        self.y = max(0.0, self.y + self.vy * dt)
        if self.on_ground():
            self.vy = 0.0
        self.h = DUCK_H if duck and self.on_ground() else STAND_H
        far = max(o.x for o in self.obstacles)
        for i, o in enumerate(self.obstacles):
            o.x -= SPEED * dt
            if not o.cleared and o.x + o.w < RUNNER_X - RUNNER_W / 2:
                o.cleared = True
                self.score += 1
            if o.x + o.w < -1.0:
                self.obstacles[i] = Obstacle(self.rng, far + self.gap())
        left, right = RUNNER_X - RUNNER_W / 2, RUNNER_X + RUNNER_W / 2
        return not any(
            o.x < right and o.x + o.w > left and self.y < o.top and self.y + self.h > o.bottom for o in self.obstacles
        )

    def entities(self) -> list[dict]:
        return [
            {"id": "sky", "shape": "box", "pos": [6, 3, -1], "size": [40, 10, 0.1], "color": "#e8eef2"},
            {"id": "ground", "shape": "box", "pos": [6, -1.5, 0], "size": [40, 3, 1], "color": "#a3a3a3"},
            *self.patch(),
        ]

    def patch(self) -> list[dict]:
        out = [
            {"id": "runner", "shape": "box", "pos": [RUNNER_X, self.y + self.h / 2, 0], "size": [RUNNER_W, STAND_H, 0.5],
             "scale": [1, self.h / STAND_H, 1], "color": "#334155"},
        ]
        for i, o in enumerate(self.obstacles):
            out.append({"id": f"obstacle-{i}", "shape": "box", "pos": [o.x + o.w / 2, (o.bottom + o.top) / 2, 0],
                        "size": [o.w, o.top - o.bottom, 0.5], "color": "#64748b" if o.bar else "#b45309"})
        return out
