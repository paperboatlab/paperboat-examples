"""01-smart-thermostat-python: Home Thermal Comfort & Bang-Bang Hysteresis."""

from pathlib import Path

from domain.blocks import BLOCKS
from domain.state import RoomThermostat
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="01-smart-thermostat-python",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=RoomThermostat,
        blocks=BLOCKS,
        mode="clock",
        dt=0.05,
        duration=20.0,
        emit_every=4,
        port=8765,
    ))
