"""Example Paperboat backend: a mass on a spring (Python).

One mass on a spring along x; F1 pushes it and P1 reads it. The physics is the plant
(domain/plant.py), not the graph: setup says where, flow says what. The palette and the
starter graph are in descriptor.toml; every other block is a toolkit block. The protocol,
graph checking and run loop are the C++ engine, through the Python bindings (python/).
"""

from pathlib import Path

from domain.blocks import BLOCKS
from domain.plant import MassSpring
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="python-mass-spring",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=MassSpring,
        blocks=BLOCKS,
        mode="clock",
        dt=0.01,
        duration=10.0,
        emit_every=4,
        port=8765,
    ))
