"""Example Paperboat backend: a Step flow that animates a 3D actor (Python).

The Step flow example: blocks with step ports form paths (Start → Repeat → Move →
Rotate → …) and each path moves along one block at a time, like a flowchart or Scratch.
Hats start paths: Start once at the beginning, When each time its condition rises (press
Space), so several paths run at once. Signal blocks (Key, Threshold, Pose, Graph) feed
conditions and monitors, sampled once per clock step.

The actor is the plant (domain/plant.py); Move, Rotate, Scale and Pose are the domain's
blocks (domain/blocks.py); everything else is the toolkit's step and base packages. The
palette and the starter graph are in descriptor.toml; the protocol and the Step flow run
are the C++ engine, through the Python bindings (python/).
"""

from pathlib import Path

from domain.blocks import BLOCKS
from domain.plant import Actor
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="python-animation",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=Actor,
        blocks=BLOCKS,
        mode="clock",  # a Step flow: the engine sees the step blocks
        dt=1 / 50,
        duration=30.0,  # When blocks wait for events forever; stop the run here, s
        emit_every=2,  # 25 fps
        view={"mode": "3d"},
        port=8769,
    ))
