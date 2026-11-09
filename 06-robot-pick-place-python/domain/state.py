"""The robot cell: the arm, three workpieces, the conveyor and the two sorting bins."""

import math

from paperboat import DomainState
from domain.kinematics import BIN_A, BIN_B, HOME, LINK1, LINK2, BASE_HEIGHT, forward, inverse, quintic, shortest_delta


class Part:
    def __init__(self, index: int) -> None:
        self.index = index
        self.position = (-1.15 + 0.0, 0.78, -0.85 + 0.0)
        self.state = "conveyor"  # conveyor | held | placed
        self.bin = "A" if index % 2 == 0 else "B"


class RobotCell(DomainState):
    """Three joints, a vacuum gripper and the parts on the infeed conveyor."""

    def __init__(self) -> None:
        self.q = list(inverse(HOME))
        self.q_prev = list(self.q)
        self.dq = [0.0, 0.0, 0.0]
        self.gripper = 0.0
        self.parts = [Part(i) for i in range(3)]
        self.current = 0
        self.picked = 0
        self.placed = 0
        self.placed_a = 0
        self.placed_b = 0
        self.held: Part | None = None
        self.move_start = forward(tuple(self.q))
        self.move_end = HOME
        self.move_lift = 0.0
        self.moving = False
        self.sim_time = 0.0

    # --- the arm --------------------------------------------------------------------------

    def tcp(self) -> tuple[float, float, float]:
        return forward(tuple(self.q))

    def current_part(self) -> Part:
        return self.parts[min(self.current, len(self.parts) - 1)]

    def bin_point(self, part: Part) -> tuple[float, float, float]:
        return BIN_A if part.bin == "A" else BIN_B

    def start_move(self, target: str, lift: float) -> None:
        self.move_start = self.tcp()
        self.move_lift = lift
        if target == "home":
            self.move_end = HOME
        elif target == "pick":
            self.move_end = self.current_part().position
        elif target == "bin":
            self.move_end = self.bin_point(self.current_part())
        else:
            raise ValueError(f"unknown trajectory target {target!r}")
        self.moving = True

    def advance_move(self, s: float) -> None:
        progress = quintic(s)
        start, end = self.move_start, self.move_end
        x = start[0] + (end[0] - start[0]) * progress
        z = start[2] + (end[2] - start[2]) * progress
        # A raised transfer arc: zero at both ends, `lift` high in the middle.
        y = start[1] + (end[1] - start[1]) * progress + self.move_lift * math.sin(math.pi * progress)
        target = inverse((x, y, z))
        target = (self.q[0] + shortest_delta(self.q[0], target[0]), target[1], target[2])
        self.q = list(target)

    def finish_move(self) -> None:
        self.moving = False

    def grip(self) -> bool:
        """Attach the current part if the tool is over it."""
        part = self.current_part()
        if part.state != "conveyor":
            return False
        if math.dist(self.tcp(), part.position) > 0.18:
            return False
        part.state = "held"
        self.held = part
        self.gripper = 1.0
        self.picked += 1
        return True

    def release(self) -> Part | None:
        """Drop the held part into its bin."""
        if self.held is None:
            return None
        part = self.held
        part.position = self.bin_point(part)
        part.state = "placed"
        self.held = None
        self.gripper = 0.0
        self.placed += 1
        if part.bin == "A":
            self.placed_a += 1
        else:
            self.placed_b += 1
        self.current += 1
        return part

    def step(self, ctx) -> None:
        self.sim_time = ctx.t
        if ctx.dt > 0:
            self.dq = [(a - b) / ctx.dt for a, b in zip(self.q, self.q_prev)]
        self.q_prev = list(self.q)
        if self.held is not None:
            self.held.position = self.tcp()

    def summary(self) -> str:
        return f"Cell complete: {self.placed} parts sorted ({self.placed_a} in BIN A, {self.placed_b} in BIN B)"

    # --- the station's scene --------------------------------------------------------------

    def _joint_points(self) -> tuple[tuple[float, float, float], ...]:
        t1, t2, t3 = self.q
        shoulder = (0.0, BASE_HEIGHT, 0.0)
        elbow = (
            shoulder[0] + LINK1 * math.sin(t2) * math.sin(t1),
            shoulder[1] + LINK1 * math.cos(t2),
            shoulder[2] + LINK1 * math.sin(t2) * math.cos(t1),
        )
        wrist = (
            elbow[0] + LINK2 * math.sin(t2 + t3) * math.sin(t1),
            elbow[1] + LINK2 * math.cos(t2 + t3),
            elbow[2] + LINK2 * math.sin(t2 + t3) * math.cos(t1),
        )
        return shoulder, elbow, wrist

    def entities(self) -> list[dict]:
        shoulder, elbow, wrist = self._joint_points()
        parts = []
        for part in self.parts:
            if part.state == "placed":
                color = "#22c55e"
            elif part.state == "held":
                color = "#f59e0b"
            else:
                color = "#cbd5e1"
            parts.append({
                "id": f"part-{part.index}",
                "shape": "box",
                "pos": [round(v, 4) for v in part.position],
                "size": [0.16, 0.16, 0.16],
                "color": color,
            })
        # ABB IRB 460-style palletizer: a cast pedestal, a turret, a two-link arm and a
        # wide fork. This is a primitive stand-in for the real CAD (mesh import is not yet
        # part of the Station API).
        crates = []
        for row, z in enumerate((-0.78, -0.46, -0.14, 0.18)):
            crates.append({"id": f"crate-a-{row}", "shape": "box", "pos": [1.30, 0.13 + row * 0.2, z],
                           "size": [0.26, 0.18, 0.26], "color": "#d6d3d1" if row % 2 == 0 else "#a8a29e"})
        for row, z in enumerate((-0.78, -0.46, -0.14, 0.18)):
            crates.append({"id": f"crate-b-{row}", "shape": "box", "pos": [1.30, 0.13 + row * 0.2, z + 1.3],
                           "size": [0.26, 0.18, 0.26], "color": "#d6d3d1" if row % 2 == 0 else "#a8a29e"})
        pallets = [
            {"id": "pallet-a", "shape": "box", "pos": [1.30, 0.03, -0.46], "size": [1.10, 0.08, 1.10], "color": "#92400e"},
            {"id": "pallet-b", "shape": "box", "pos": [1.30, 0.03, 0.84], "size": [1.10, 0.08, 1.10], "color": "#92400e"},
            {"id": "pallet-a-label", "shape": "box", "pos": [1.30, 0.09, -1.02], "size": [0.32, 0.04, 0.04], "color": "#f59e0b"},
            {"id": "pallet-b-label", "shape": "box", "pos": [1.30, 0.09, 1.40], "size": [0.32, 0.04, 0.04], "color": "#f59e0b"},
        ]
        return [
            {"id": "floor", "shape": "box", "pos": [0, -0.06, 0], "size": [6.4, 0.12, 4.8], "color": "#1f2429"},
            {"id": "pedestal", "shape": "box", "pos": [0, 0.34, 0], "size": [1.15, 0.68, 1.15], "color": "#3f3f46"},
            {"id": "turret", "shape": "box", "pos": [0, 0.78, 0], "size": [0.82, 0.28, 0.82], "color": "#f97316"},
            {"id": "column", "shape": "box", "pos": [0, 1.35, 0], "size": [0.46, 0.9, 0.46], "color": "#ea580c"},
            {"id": "shoulder", "shape": "sphere", "pos": list(shoulder), "size": [0.32, 0, 0], "color": "#ea580c"},
            {"id": "link1", "shape": "line", "pos": list(shoulder), "to": list(elbow), "color": "#f97316"},
            {"id": "link1-back", "shape": "line", "pos": [shoulder[0] + 0.08, shoulder[1], shoulder[2]],
             "to": [elbow[0] + 0.08, elbow[1], elbow[2]], "color": "#c2410c"},
            {"id": "elbow", "shape": "sphere", "pos": list(elbow), "size": [0.26, 0, 0], "color": "#ea580c"},
            {"id": "link2", "shape": "line", "pos": list(elbow), "to": list(wrist), "color": "#fb923c"},
            {"id": "link2-back", "shape": "line", "pos": [elbow[0] + 0.07, elbow[1], elbow[2]],
             "to": [wrist[0] + 0.07, wrist[1], wrist[2]], "color": "#c2410c"},
            {"id": "wrist", "shape": "sphere", "pos": list(wrist), "size": [0.2, 0, 0], "color": "#c2410c"},
            {"id": "fork", "shape": "box", "pos": [wrist[0], wrist[1] - 0.12, wrist[2]], "size": [0.62, 0.08, 0.18],
             "color": "#facc15" if self.gripper > 0.5 else "#a16207"},
            {"id": "fork-tine-1", "shape": "box", "pos": [wrist[0] - 0.22, wrist[1] - 0.18, wrist[2] - 0.24],
             "size": [0.12, 0.04, 0.42], "color": "#a16207"},
            {"id": "fork-tine-2", "shape": "box", "pos": [wrist[0] + 0.22, wrist[1] - 0.18, wrist[2] - 0.24],
             "size": [0.12, 0.04, 0.42], "color": "#a16207"},
            {"id": "conveyor", "shape": "box", "pos": [-1.15, 0.55, -0.85], "size": [2.2, 0.14, 0.6], "color": "#475569"},
            {"id": "conveyor-leg-1", "shape": "box", "pos": [-2.0, 0.26, -0.85], "size": [0.1, 0.52, 0.5], "color": "#334155"},
            {"id": "conveyor-leg-2", "shape": "box", "pos": [-0.3, 0.26, -0.85], "size": [0.1, 0.52, 0.5], "color": "#334155"},
            *pallets,
            *crates,
            *parts,
        ]
