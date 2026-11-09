"""06-robot-pick-place-python: a 3-DOF arm sorts three workpieces (Level 06).

The Flow page sequences the cell: Repeat 3 × (S-curve to the part → vacuum on → S-curve
to the bin → vacuum off). The inverse-kinematics block converts each Cartesian waypoint to
joint angles; the arm's probes plot joint rates on the Board.
"""

from pathlib import Path

from domain.blocks import BLOCKS
from domain.state import RobotCell
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="06-robot-pick-place-python",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=RobotCell,
        blocks=BLOCKS,
        mode="clock",
        dt=1 / 50,
        duration=22.0,
        emit_every=2,
        view={"mode": "3d", "camera": {"eye": [4.6, 3.2, 5.4], "target": [0.0, 1.0, 0.0]}},
        port=8770,
    ))
