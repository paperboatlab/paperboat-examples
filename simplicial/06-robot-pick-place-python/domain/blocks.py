"""The robot cell's Flow blocks: IK, quintic trajectories and the vacuum gripper.

Each acts on the cell, the station object (domain/state.py), through `current()`; station.py
registers them with their ports and params.
"""

import math

import paperboat_runtime as pb

from domain.kinematics import inverse
from domain.state import current


class ArmProbe:
    """Joint angles, joint rates and the tool-centre point."""

    def step(self, ctx, inputs) -> dict:
        robot = current()
        x, y, z = robot.tcp()
        return {
            "t1": math.degrees(robot.q[0]),
            "t2": math.degrees(robot.q[1]),
            "t3": math.degrees(robot.q[2]),
            "dt1": math.degrees(robot.dq[0]),
            "dt2": math.degrees(robot.dq[1]),
            "dt3": math.degrees(robot.dq[2]),
            "x": x,
            "y": y,
            "z": z,
            "gripper": robot.gripper,
            "placed": float(robot.placed),
        }


class InverseKinematics:
    """Analytical IK: a Cartesian tool point to three joint angles (degrees)."""

    def step(self, ctx, inputs) -> dict:
        point = (
            float(inputs.get("x", 0.0)),
            float(inputs.get("y", 0.0)),
            float(inputs.get("z", 0.0)),
        )
        try:
            t1, t2, t3 = inverse(point)
        except ValueError:
            return {"t1": 0.0, "t2": 0.0, "t3": 0.0, "reachable": 0.0}
        return {
            "t1": math.degrees(t1),
            "t2": math.degrees(t2),
            "t3": math.degrees(t3),
            "reachable": 1.0,
        }


class Trajectory:
    """Move the tool centre point to `target` along a quintic S-curve, over `seconds`.

    `target` is `home`, `pick` (the current workpiece) or `bin` (its sorting bin). The
    Cartesian path rises by `lift` in the middle, so transfers arc over the conveyor.
    """

    def __init__(self, target: str = "pick", seconds: float = 1.4, lift: float = 0.35) -> None:
        self.target, self.seconds, self.lift = target, seconds, lift
        self.progress = 0.0

    def enter(self, ctx, inputs) -> None:
        current().start_move(self.target, self.lift)
        self.elapsed = 0.0
        self.progress = 0.0

    def tick(self, ctx, inputs) -> str:
        self.elapsed += ctx["dt"]
        self.progress = min(1.0, self.elapsed / max(self.seconds, 1e-3))
        current().advance_move(self.progress)
        if self.progress < 1.0:
            return ""
        current().finish_move()
        return "next"

    def outputs(self) -> dict:
        return {"progress": self.progress}


class Grip:
    """Pallet fork on or off: pick the workpiece below the tool, or drop it on its pallet."""

    def __init__(self, action: str = "grip") -> None:
        self.action = action

    def enter(self, ctx, inputs) -> None:
        robot = current()
        if self.action == "grip":
            if robot.grip():
                pb.log(f"Picked part {robot.current + 1}")
            else:
                pb.log("gripper closed on nothing: check the approach waypoint")
        else:
            part = robot.release()
            if part is not None:
                pb.log(f"Placed part {part.index + 1} in BIN {part.bin}")
                if robot.placed == len(robot.parts):
                    pb.log(f"Cell complete: {robot.placed} parts sorted "
                           f"({robot.placed_a} in BIN A, {robot.placed_b} in BIN B)")

    def tick(self, ctx, inputs) -> str:
        return "next"


class CellStatus:
    """How many parts are sorted, and which one is next."""

    def step(self, ctx, inputs) -> dict:
        robot = current()
        return {
            "placed": float(robot.placed),
            "placed_a": float(robot.placed_a),
            "placed_b": float(robot.placed_b),
            "part": float(min(robot.current + 1, len(robot.parts))),
        }
