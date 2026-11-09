"""04-cocktail-barista-python: automated beverage recipes as a Step flow (Level 04).

The bar (domain/state.py) is the equipment; the Flow page is the recipe: a Start hat, a
Detect Cup check, three Dispense steps, the Shake & Chill subsystem, and Strain & Serve.
A second hat (When the Space key rises) interrupts any recipe with an emergency stop and
a clean-in-place rinse, so several paths run side by side.
"""

from pathlib import Path

from domain.blocks import BLOCKS
from domain.state import Barista
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="04-cocktail-barista-python",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=Barista,
        blocks=BLOCKS,
        mode="clock",
        dt=0.05,
        duration=18.0,
        emit_every=2,
        view={"mode": "3d", "camera": {"eye": [2.6, 1.6, 3.4], "target": [0, 0.1, 0]}},
        port=8768,
    ))
