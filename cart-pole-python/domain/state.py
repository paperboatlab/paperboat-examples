"""Cart-pole domain state: a pole balanced on a cart."""

import math

M, m, L, g = 1.0, 0.1, 1.0, 9.81
b = 0.1


class CartPole:
    def __init__(self) -> None:
        self.x, self.v = 0.0, 0.0
        self.theta, self.omega = 0.1, 0.0
        self.force = 0.0

    def step(self, ctx) -> None:
        # Cart-pole dynamics (semi-implicit Euler).
        sin_t = math.sin(self.theta)
        cos_t = math.cos(self.theta)
        denom = M + m * sin_t * sin_t
        a_cart = (self.force + m * L * self.omega * self.omega * sin_t - m * g * sin_t * cos_t - b * self.v) / denom
        a_pole = (g * sin_t - a_cart * cos_t) / L
        self.v += a_cart * ctx.dt
        self.x += self.v * ctx.dt
        self.omega += a_pole * ctx.dt
        self.theta += self.omega * ctx.dt
        self.force = 0.0

    def entities(self) -> list[dict]:
        return [
            {"id": "cart", "shape": "box", "pos": [self.x, 0, 0], "size": [0.6, 0.3, 0.4], "color": "#2f5d62"},
            {"id": "pole", "shape": "line", "pos": [self.x, 0.15, 0], "to": [self.x + L * math.sin(self.theta), L * math.cos(self.theta), 0], "color": "#c2410c"},
        ]

    def patch(self) -> list[dict]:
        return [
            {"id": "cart", "shape": "box", "pos": [self.x, 0, 0], "size": [0.6, 0.3, 0.4], "color": "#2f5d62"},
            {"id": "pole", "shape": "line", "pos": [self.x, 0.15, 0], "to": [self.x + L * math.sin(self.theta), L * math.cos(self.theta), 0], "color": "#c2410c"},
        ]

    def summary(self) -> str:
        return f"done, theta = {self.theta:.3f} rad"
