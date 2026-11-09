"""05-rover-lander-python: lunar soft touchdown with a custom HTML5 web station.

The Flow page is the guidance computer: Lander Telemetry -> GNC Autopilot -> Thrusters.
A dashboard Switch (or P) hands control to the pilot; W/A/D then fire the engines. The
Station page is the backend's own CRT cockpit (descriptor `[station] view = "web"`).
"""

from pathlib import Path

from domain.blocks import BLOCKS
from domain.state import Lander
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="05-rover-lander-python",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=Lander,
        blocks=BLOCKS,
        mode="clock",
        dt=1 / 60,
        duration=50.0,
        emit_every=2,
        speed=4.0,
        view={"mode": "2d", "center": [0, 18], "height": 46},
        port=8769,
    ))
