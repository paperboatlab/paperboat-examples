"""The mass-spring domain state: one mass on a spring along x, pushed by the force sources."""

from paperboat import DomainState

MASS, STIFFNESS, DAMPING = 1.0, 4.0, 0.4  # kg, N/m, N·s/m
WALL_X = -3.0


class MassSpring(DomainState):
    def __init__(self) -> None:
        self.x, self.v = 0.0, 0.0
        self.force = 0.0  # summed by the F1 blocks during a step, used and cleared by step()

    def step(self, ctx) -> None:
        # Semi-implicit Euler.
        a = (self.force - STIFFNESS * self.x - DAMPING * self.v) / MASS
        self.v += a * ctx.dt
        self.x += self.v * ctx.dt
        self.force = 0.0

    def entities(self) -> list[dict]:
        return [
            {"id": "ground", "shape": "box", "pos": [0, -0.6, 0], "size": [8, 0.2, 2], "color": "#8a8f8c"},
            {"id": "wall", "shape": "box", "pos": [WALL_X, 0, 0], "size": [0.2, 1.2, 2], "color": "#5b6662"},
            *self.patch(),
        ]

    def patch(self) -> list[dict]:
        return [
            {"id": "spring", "shape": "line", "pos": [WALL_X + 0.1, 0, 0], "to": [self.x - 0.5, 0, 0], "color": "#c2410c"},
            {"id": "mass", "shape": "box", "pos": [self.x, 0, 0], "size": [1, 1, 1], "color": "#2f5d62"},
        ]

    def summary(self) -> str:
        return f"done, final x = {self.x:.3f} m"
