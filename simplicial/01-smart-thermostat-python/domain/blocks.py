"""Blocks for the smart thermostat domain: heater actuator and room sensor."""

import paperboat
from domain.state import Q_HEATER


class HeaterActuator(paperboat.Block):
    """Heater actuator: receives binary ON/OFF command or continuous power ratio [0, 1]."""

    type, label, kind = "heater", "Heater · Baseboard Radiator", "function"
    inputs = ["cmd"]

    def step(self, ctx, inputs) -> dict:
        cmd = float(inputs.get("cmd", 0.0))
        ctx.state.heater_on = 1.0 if cmd > 0.5 else 0.0
        ctx.state.heater_power = Q_HEATER * min(max(cmd, 0.0), 1.0)
        return {}


class RoomSensor(paperboat.Block):
    """Room temperature sensor: emits indoor temperature and ambient outdoor temperature."""

    type, label, kind = "room_sensor", "Room Sensor · Telemetry", "source"
    outputs = ["t_room", "t_amb"]

    def step(self, ctx, inputs) -> dict:
        return {
            "t_room": ctx.state.t_room,
            "t_amb": ctx.state.t_amb,
        }


BLOCKS = [HeaterActuator, RoomSensor]
