"""07-airfoil-cfd-python: a 2-D lattice-Boltzmann wind tunnel (Level 07).

The Flow page is the tunnel's pipeline: the airfoil mask, the inflow condition, the D2Q9
lattice step and the lift/drag polar readout. Move `alpha` in the Variables sheet (or bind
it to a knob) to watch the field separate and the lift curve break past 14 degrees. The
Station page draws the velocity vectors, streamlines and force arrows.
"""

from pathlib import Path

from domain.blocks import BLOCKS
from domain.state import WindTunnel
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="07-airfoil-cfd-python",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=WindTunnel,
        blocks=BLOCKS,
        mode="clock",
        dt=0.1,
        duration=9.0,
        emit_every=1,
        view={"mode": "2d", "center": [1.8, 0.95], "height": 2.4},
        port=8771,
    ))
