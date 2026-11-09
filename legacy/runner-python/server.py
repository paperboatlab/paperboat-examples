"""Example Paperboat backend: a 2D runner that jumps over crates and ducks under bars (Python).

The runner and obstacles are the domain state (domain/state.py); the flow decides when to jump or
duck (control). The starter graph in descriptor.toml is an autopilot. Wire the Key blocks
to Jump and Duck instead and play it yourself with Space and Arrow Down: the UI forwards
key presses as `input` messages. The domain's blocks are in domain/blocks.py; the
protocol, graph checking and run loop are the C++ engine, through the Python bindings (python/).
"""

from pathlib import Path

from domain.blocks import BLOCKS
from domain.state import Game
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="python-runner",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=Game,
        blocks=BLOCKS,
        mode="clock",
        dt=1 / 60,
        duration=20.0,  # keep running this long to win, s
        emit_every=2,  # 30 fps
        view={"mode": "2d", "center": [5, 2.5], "height": 8},
        port=8768,
    ))
