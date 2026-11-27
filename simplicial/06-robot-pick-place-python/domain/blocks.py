"""The robot cell's Flow blocks: IK, quintic trajectories and the vacuum gripper."""

import math

import paperboat
from domain.kinematics import inverse, quintic


class ArmProbe(paperboat.Block):
    """Joint angles, joint rates and the tool-centre point."""

    type, label, kind = "arm_probe", "Arm Telemetry", "probe"
    outputs = ["t1", "t2", "t3", "dt1", "dt2", "dt3", "x", "y", "z", "gripper", "placed"]

    def step(self, ctx, inputs) -> dict:
        robot = ctx.state
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


class InverseKinematics(paperboat.Block):
    """Analytical IK: a Cartesian tool point to three joint angles (degrees)."""

    type, label, kind = "inverse_kinematics", "Inverse Kinematics", "function"
    inputs = ["x", "y", "z"]
    outputs = ["t1", "t2", "t3", "reachable"]

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


class Trajectory(paperboat.Timed):
    """Move the tool centre point to `target` along a quintic S-curve.

    `target` is `home`, `pick` (the current workpiece) or `bin` (its sorting bin). The
    Cartesian path rises by `lift` in the middle, so transfers arc over the conveyor.
    """

    type, label = "trajectory", "S-Curve Trajectory"
    params = {
        "target": paperboat.Param("pick", "enum", ["home", "pick", "bin"]),
        "seconds": 1.4,
        "lift": 0.35,
    }

    def begin(self, ctx, inputs) -> None:
        ctx.state.start_move(str(self.params.get("target", "pick")), float(self.params.get("lift", 0.8)))
        self.finished = False

    def advance(self, ctx, start: float, end: float) -> None:
        ctx.state.advance_move(end)
        if end >= 0.999 and not self.finished:
            self.finished = True
            ctx.state.finish_move()


class Grip(paperboat.Step):
    """Pallet fork on or off: pick the workpiece below the tool, or drop it on its pallet."""

    type, label = "grip", "Vacuum Gripper"
    params = {"action": paperboat.Param("grip", "enum", ["grip", "release"])}

    def enter(self, ctx, inputs) -> None:
        robot = ctx.state
        action = str(self.params.get("action", "grip"))
        if action == "grip":
            if robot.grip():
                ctx.log(f"Picked part {robot.current + 1}")
            else:
                ctx.log("gripper closed on nothing: check the approach waypoint")
        else:
            part = robot.release()
            if part is not None:
                ctx.log(f"Placed part {part.index + 1} in BIN {part.bin}")

    def tick(self, ctx, inputs) -> str:
        return "next"


class CellStatus(paperboat.Block):
    """How many parts are sorted, and which one is next."""

    type, label, kind = "cell_status", "Cell Status", "probe"
    outputs = ["placed", "placed_a", "placed_b", "part"]

    def step(self, ctx, inputs) -> dict:
        robot = ctx.state
        return {
            "placed": float(robot.placed),
            "placed_a": float(robot.placed_a),
            "placed_b": float(robot.placed_b),
            "part": float(min(robot.current + 1, len(robot.parts))),
        }


BLOCKS = [ArmProbe, InverseKinematics, Trajectory, Grip, CellStatus]
