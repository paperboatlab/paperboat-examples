"""Blocks for the smart thermostat domain: heater actuator and room sensor.

Both act on the room, the station object (domain/state.py): `state.room()` is the one this run made.
"""

from domain import state
from domain.state import Q_HEATER


class HeaterActuator:
    """Heater actuator: receives binary ON/OFF command or continuous power ratio [0, 1]."""

    def step(self, ctx, inputs) -> dict:
        cmd = float(inputs.get("cmd", 0.0))
        room = state.room()
        room.heater_on = 1.0 if cmd > 0.5 else 0.0
        room.heater_power = Q_HEATER * min(max(cmd, 0.0), 1.0)
        return {}


class RoomSensor:
    """Room temperature sensor: emits indoor temperature and ambient outdoor temperature."""

    def step(self, ctx, inputs) -> dict:
        room = state.room()
        return {"t_room": room.t_room, "t_amb": room.t_amb}
