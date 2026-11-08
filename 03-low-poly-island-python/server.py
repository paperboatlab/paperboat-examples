"""Tutorial 03: Procedural low-poly archipelago & static evaluation (Level 03).

Static pipeline evaluation (solver = 'discrete'), list & array wires,
block commenting (Ctrl+/), and block bypassing (Ctrl+Shift+Y).
"""

from pathlib import Path

from domain import BLOCKS, IslandState
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="03-low-poly-island-python",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=IslandState,
        blocks=BLOCKS,
        mode="once",
        port=8767,
        solver="discrete",
    ))
