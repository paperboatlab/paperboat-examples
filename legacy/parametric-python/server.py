"""Example Paperboat backend: parametric geometry, no simulation (Python).

Unlike the other examples there is no clock: a run evaluates the graph once. Wires carry
lists (a grid of points, one height per point), and the Boxes block writes its result
into the 3D scene, Grasshopper style. The domain's blocks are in domain/blocks.py and the
scene in domain/state.py; the palette and the starter graph are in descriptor.toml; the
protocol, graph checking and evaluation are the C++ engine, through the Python bindings (python/).
"""

from pathlib import Path

from domain.blocks import BLOCKS
from domain.state import Boxes
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="python-parametric",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=Boxes,
        blocks=BLOCKS,
        mode="once",
        port=8767,
    ))
