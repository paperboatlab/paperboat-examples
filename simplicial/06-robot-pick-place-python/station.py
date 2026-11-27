"""06-robot-pick-place-python: ABB-style palletizer (Level 06).

The Flow page sequences the cell: Repeat 3 × (S-curve to the part → vacuum on → S-curve to the bin
→ vacuum off). The inverse-kinematics block converts each Cartesian waypoint to joint angles; the
arm's probes plot joint rates on the Board.

The engine loads this file into a Python runtime (paperboat_runtime): the cell is a station
object, the rest are blocks and steps, each registered with its ports and params.
"""

import paperboat_runtime as pb

from domain import blocks
from domain.state import RobotCell

IN = {"id": "in", "type": "step"}      # a step's path arrives here
NEXT = {"id": "next", "type": "step"}  # and leaves here

pb.register("robot_cell", RobotCell, definition={
    "base": "object",
    "label": "Robot Cell",
    "description": "A 3-DOF palletizer, an infeed conveyor and two sorting pallets",
})
pb.register("arm_probe", blocks.ArmProbe, definition={
    "label": "Arm Telemetry", "kind": "probe",
    "outputs": ["t1", "t2", "t3", "dt1", "dt2", "dt3", "x", "y", "z", "gripper", "placed"],
})
pb.register("inverse_kinematics", blocks.InverseKinematics, definition={
    "label": "Inverse Kinematics", "inputs": ["x", "y", "z"], "outputs": ["t1", "t2", "t3", "reachable"],
})
pb.register("trajectory", blocks.Trajectory, definition={
    "base": "step", "label": "S-Curve Trajectory", "inputs": [IN], "outputs": [NEXT, "progress"],
    "params": [
        {"id": "target", "default": "pick", "type": "enum", "options": ["home", "pick", "bin"]},
        {"id": "seconds", "default": 1.4},
        {"id": "lift", "default": 0.35},
    ],
})
pb.register("grip", blocks.Grip, definition={
    "base": "step", "label": "Vacuum Gripper", "inputs": [IN], "outputs": [NEXT],
    "params": [{"id": "action", "default": "grip", "type": "enum", "options": ["grip", "release"]}],
})
pb.register("cell_status", blocks.CellStatus, definition={
    "label": "Cell Status", "kind": "probe", "outputs": ["placed", "placed_a", "placed_b", "part"],
})
