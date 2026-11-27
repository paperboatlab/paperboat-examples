"""05-rover-lander-python: manual pilot vs autonomous lunar landing (Level 05).

The Flow page is the guidance computer: Lander Telemetry -> GNC Autopilot -> Thrusters. A board
Switch (or P) hands control to the pilot; W/A/D then fire the engines. The Station page is the
station's own CRT cockpit (descriptor `[station] view = "web"`).

The engine loads this file into a Python runtime (paperboat_runtime): the lander is a station
object, the rest are blocks, each registered with its ports and params.
"""

import paperboat_runtime as pb

from domain import blocks
from domain.state import PAD_X, Lander

pb.register("lander", Lander, definition={
    "base": "object",
    "label": "Lunar Module",
    "description": "A two-dimensional lander above the LZ-1 pad",
    "props": {"landing_x": PAD_X},
})
pb.register("lander_probe", blocks.LanderProbe, definition={
    "label": "Lander Telemetry", "kind": "probe",
    "outputs": ["y", "vy", "x", "vx", "fuel", "main", "landed"],
})
pb.register("guidance", blocks.Guidance, definition={
    "label": "GNC Autopilot", "kind": "source",
    "inputs": ["y", "vy", "x", "vx", "fuel", "mode", "target_x"],
    "outputs": ["main", "rcs", "target_vy"],
    "params": {"descent": 0.32, "floor": 0.55, "kp_vertical": 1.6, "kp_horizontal": 1.2},
})
pb.register("manual_thrusters", blocks.ManualThrusters, definition={
    "label": "Manual Keys (W/A/D)", "kind": "source", "inputs": ["w", "a", "d", "mode"], "outputs": ["main", "rcs"],
})
pb.register("thrusters", blocks.Thrusters, definition={
    "label": "Thrusters", "inputs": ["main_auto", "rcs_auto", "main_manual", "rcs_manual"],
})
