"""The parametric domain's own blocks, defined by their class attributes. Wires carry lists:
a grid of points, one height per point. Evaluated once, in dependency order."""

import math

import paperboat
from paperboat import Port

from .state import height_color


class Block(paperboat.Block):
    def __init__(self, params: dict) -> None:
        super().__init__(params)
        self.p = params


POINTS, NUMBERS = "points", "numbers"


class Grid(Block):
    type, label = "grid", "Grid"
    outputs = [Port("points", POINTS)]
    params = {"nx": 12, "nz": 12, "spacing": 0.6}

    def step(self, ctx, inputs) -> dict:
        nx, nz, s = max(int(self.p["nx"]), 1), max(int(self.p["nz"]), 1), self.p["spacing"]
        ox, oz = (nx - 1) * s / 2, (nz - 1) * s / 2
        return {"points": [(i * s - ox, j * s - oz) for i in range(nx) for j in range(nz)]}


class Wave(Block):
    type, label = "wave", "Wave"
    inputs = [Port("points", POINTS)]
    outputs = [Port("heights", NUMBERS)]
    params = {"amplitude": 0.6, "frequency": 1.2}

    def step(self, ctx, inputs) -> dict:
        a, f = self.p["amplitude"], self.p["frequency"]
        return {"heights": [a * math.sin(f * x) * math.cos(f * z) for x, z in inputs.get("points", [])]}


class Attractor(Block):
    type, label = "attractor", "Attractor"
    inputs = [Port("points", POINTS)]
    outputs = [Port("heights", NUMBERS)]
    params = {"x": 1, "z": -1, "strength": 2.5, "falloff": 1.5}

    def step(self, ctx, inputs) -> dict:
        p, fo = self.p, self.p["falloff"] or 1e-9
        return {"heights": [p["strength"] * math.exp(-((x - p["x"]) ** 2 + (z - p["z"]) ** 2) / fo**2)
                            for x, z in inputs.get("points", [])]}


class Add(Block):
    type, label = "add", "Add lists"
    inputs = [Port("a", NUMBERS), Port("b", NUMBERS)]
    outputs = [Port("y", NUMBERS)]

    def step(self, ctx, inputs) -> dict:
        a, b = inputs.get("a", []), inputs.get("b", [])
        if a and b and len(a) != len(b):
            raise ValueError(f"add: lists differ in length ({len(a)} vs {len(b)})")
        return {"y": [(a[i] if a else 0.0) + (b[i] if b else 0.0) for i in range(max(len(a), len(b)))]}


class ScaleList(Block):
    type, label = "scale", "Scale list"
    inputs = [Port("u", NUMBERS)]
    outputs = [Port("y", NUMBERS)]
    params = {"k": 1}

    def step(self, ctx, inputs) -> dict:
        return {"y": [self.p["k"] * v for v in inputs.get("u", [])]}


class BoxesOut(Block):
    """A source: puts one box per point into the scene, as tall as its height."""

    type, label, kind = "boxes", "Boxes → scene", "source"
    inputs = [Port("points", POINTS), Port("heights", NUMBERS)]
    params = {"width": 0.45, "base": 0.05}

    def step(self, ctx, inputs) -> dict:
        points, heights = inputs.get("points", []), inputs.get("heights", None)
        if heights is None:  # an unconnected input reads as 0: flat boxes
            heights = [0.0] * len(points)
        if len(points) != len(heights):
            raise ValueError(f"boxes: {len(points)} points but {len(heights)} heights")
        width, base = self.p["width"], self.p["base"]
        heights = [max(base, base + h) for h in heights]
        top = max(heights, default=1.0) or 1.0  # base can be 0
        ctx.state.boxes = [
            {"id": f"box-{i}", "shape": "box", "pos": [x, h / 2, z], "size": [width, h, width], "color": height_color(h / top)}
            for i, ((x, z), h) in enumerate(zip(points, heights))
        ]
        return {}


class ListGraph(paperboat.Monitor):
    """Plots a list by index on the Dashboard."""

    type, label = "graph", "Graph (by index)"
    inputs = [Port("in", NUMBERS)]


BLOCKS = [Grid, Wave, Attractor, Add, ScaleList, BoxesOut, ListGraph]
