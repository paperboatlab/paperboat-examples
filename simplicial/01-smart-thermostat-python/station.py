"""01-smart-thermostat-python: Home Thermal Comfort & Bang-Bang Hysteresis.

The station file Simplicial's engine loads into a Python runtime (paperboat_runtime): it registers
the room (a station object: the equipment, its physics and its 3D scene) and the two blocks the Flow
wires to it, the sensor and the heater.
"""

import paperboat_runtime as pb

from domain.blocks import HeaterActuator, RoomSensor
from domain.state import RoomThermostat

pb.register("room", RoomThermostat, definition={
    "base": "object",
    "label": "Living Room",
    "description": "Room air, walls, window and a baseboard heater",
    "props": {"open_window": False},
})
pb.register("heater", HeaterActuator, definition={
    "label": "Heater · Baseboard Radiator",
    "inputs": ["cmd"],
})
pb.register("room_sensor", RoomSensor, definition={
    "label": "Room Sensor · Telemetry",
    "kind": "source",
    "outputs": ["t_room", "t_amb"],
})
