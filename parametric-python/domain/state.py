"""The parametric domain state: nothing moves. It holds the boxes the Boxes block built, on a
ground plate, for the scene at the end of an evaluation."""

from paperboat import DomainState

Points = list[tuple[float, float]]  # (x, z) on the ground plane
Numbers = list[float]

GROUND = {"id": "ground", "shape": "box", "pos": [0, -0.05, 0], "size": [10, 0.1, 10], "color": "#c9cecb"}


def height_color(t: float) -> str:
    """Steel blue at 0 → orange at 1."""
    t = min(max(t, 0.0), 1.0)
    lo, hi = (0x2F, 0x5D, 0x62), (0xC2, 0x41, 0x0C)
    return "#" + "".join(f"{round(a + (b - a) * t):02x}" for a, b in zip(lo, hi))


class Boxes(DomainState):
    def __init__(self) -> None:
        self.boxes: list[dict] = []

    def entities(self) -> list[dict]:
        return [GROUND, *self.boxes]

    def summary(self) -> str:
        return f"{len(self.boxes)} boxes"
