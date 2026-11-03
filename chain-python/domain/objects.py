"""The chain's structural elements: station objects wired to each other on the Station
page (its graph view). A spring or damper links two other elements (`a` and `b`) and
pushes on them; a mass moves under what pushes it; a wall stays put.

Each class's attributes define the station object (props are edited on the Station page
only, ISA-88); `block = Linked(...)` gives it a linked block on the Flow page, through
which the test logic pushes on it or reads it.
"""

import paperboat
from paperboat import Linked


class Element(paperboat.StationObject):
    """Something with a position along the chain that forces can act on."""

    def __init__(self, props: dict) -> None:
        super().__init__(props)
        self.x, self.v, self.f = props.get("x0", 0.0), 0.0, 0.0

    def push(self, force: float) -> None:
        self.f += force


class Wall(Element):
    """A fixed anchor."""

    type, label, role = "wall", "Wall", "body"
    props = {"x0": 0.0}

    def entities(self, id, z):
        return [{"id": f"{id}/wall", "shape": "box", "pos": [self.x - 0.1, 0, z], "size": [0.2, 1.2, 0.6], "color": "#57534e"}]


class Mass(Element):
    """A point mass on a frictionless track. Its linked block pushes it (`force`) and reads
    its position and velocity."""

    type, label, role = "mass", "Mass", "body"
    props = {"mass": 1.0, "x0": 1.0}
    block = Linked(inputs=["force"], outputs=["x", "v"], kind="source")

    def read(self) -> dict:
        return {"x": self.x, "v": self.v}

    def step(self, ctx, inputs) -> None:
        a = (self.f + inputs.get("force", 0.0)) / self.props["mass"]
        self.v += a * ctx.dt  # semi-implicit Euler
        self.x += self.v * ctx.dt
        self.f = 0.0

    def entities(self, id, z):
        return [{"id": f"{id}/body", "shape": "box", "pos": [self.x, 0, z], "size": [0.4, 0.4, 0.4], "color": "#2f5d62"}]


class Link(paperboat.StationObject):
    """Joins two elements, `a` (left) and `b` (right)."""

    role = "joint"
    links = ["a", "b"]

    def __init__(self, props: dict) -> None:
        super().__init__(props)
        self.a: Element | None = None
        self.b: Element | None = None
        self.force = 0.0  # pulling a and b together when positive

    def link(self, slot, other) -> None:
        setattr(self, slot, other)

    def read(self) -> dict:
        return {"tension": self.force}

    def step(self, ctx, inputs) -> None:
        if self.a is None or self.b is None:
            return
        self.force = self.law()
        self.a.push(self.force)
        self.b.push(-self.force)

    def law(self) -> float:
        raise NotImplementedError

    def entities(self, id, z):
        if self.a is None or self.b is None:
            return []
        return [{"id": f"{id}/line", "shape": "line", "pos": [self.a.x, 0, z], "to": [self.b.x, 0, z], "color": "#b45309"}]


class Spring(Link):
    """A linear spring: tension k · (length − rest)."""

    type, label = "spring", "Spring"
    props = {"k": 20.0, "rest": 1.0}
    block = Linked(outputs=["tension"], kind="probe")

    def law(self) -> float:
        return self.props["k"] * ((self.b.x - self.a.x) - self.props["rest"])


class Damper(Link):
    """A linear damper: force c · (relative velocity)."""

    type, label = "damper", "Damper"
    props = {"c": 1.5}

    def law(self) -> float:
        return self.props["c"] * (self.b.v - self.a.v)


OBJECTS = [Wall, Mass, Spring, Damper]
