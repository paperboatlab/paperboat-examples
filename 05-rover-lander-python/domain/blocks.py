"""The lunar lander's Flow blocks: telemetry, the GNC autopilot, manual keys and thrusters."""

import math

import paperboat
from domain.state import G_MOON, MAIN_THRUST, RCS_THRUST


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


class LanderProbe(paperboat.Block):
    """The vehicle's state, as the Flow sees it."""

    type, label, kind = "lander_probe", "Lander Telemetry", "probe"
    outputs = ["y", "vy", "x", "vx", "fuel", "main", "landed"]

    def step(self, ctx, inputs) -> dict:
        lander = ctx.state
        return {
            "y": lander.y,
            "vy": lander.vy,
            "x": lander.x,
            "vx": lander.vx,
            "fuel": lander.fuel,
            "main": lander.main,
            "landed": 1.0 if lander.landed else 0.0,
        }


class Guidance(paperboat.Block):
    """Autonomous guidance, navigation and control: a terminal deceleration burn.

    It follows a descent-speed profile and steers the horizontal drift to the LZ-1 pad,
    then shuts the engine down just above the surface. `mode` (the dashboard switch) turns
    it off so the keyboard can fly the module.
    """

    type, label, kind = "guidance", "GNC Autopilot", "source"
    inputs = ["y", "vy", "x", "vx", "fuel", "mode", "target_x"]
    outputs = ["main", "rcs", "target_vy"]
    params = {"descent": 0.32, "floor": 0.55, "kp_vertical": 1.6, "kp_horizontal": 1.2}

    def step(self, ctx, inputs) -> dict:
        mode = float(inputs.get("mode", 1.0))
        if mode <= 0.5:
            return {"main": 0.0, "rcs": 0.0, "target_vy": 0.0}
        y = max(0.0, float(inputs.get("y", 0.0)))
        vy = float(inputs.get("vy", 0.0))
        x = float(inputs.get("x", 0.0))
        vx = float(inputs.get("vx", 0.0))
        fuel = float(inputs.get("fuel", 0.0))
        mass = 220.0 + max(0.0, fuel)

        floor = float(self.params.get("floor", 0.55))
        target_vy = -min(2.4, max(floor, float(self.params.get("descent", 0.32)) * math.sqrt(y) + 0.30))
        a_cmd = float(self.params.get("kp_vertical", 1.6)) * (target_vy - vy)
        main = _clamp(mass * (G_MOON + a_cmd) / MAIN_THRUST, 0.0, 1.0)

        target_x = float(inputs.get("target_x", 0.0))
        target_vx = _clamp(-0.35 * (x - target_x), -1.4, 1.4)
        rcs = _clamp(mass * float(self.params.get("kp_horizontal", 1.2)) * (target_vx - vx) / RCS_THRUST, -1.0, 1.0)

        # Final flare: hold a gentle descent, then cut the engine at the pad.
        if y < 0.35 and abs(vy) < 2.0:
            main, rcs = 0.0, 0.0
        return {"main": main, "rcs": rcs, "target_vy": target_vy}


class ManualThrusters(paperboat.Block):
    """The pilot's keyboard: W fires the main engine, A/D pulse the RCS."""

    type, label, kind = "manual_thrusters", "Manual Keys (W/A/D)", "source"
    inputs = ["w", "a", "d", "mode"]
    outputs = ["main", "rcs"]

    def step(self, ctx, inputs) -> dict:
        if float(inputs.get("mode", 1.0)) > 0.5:
            return {"main": 0.0, "rcs": 0.0}
        w = 1.0 if inputs.get("w", 0.0) > 0.5 else 0.0
        a = 1.0 if inputs.get("a", 0.0) > 0.5 else 0.0
        d = 1.0 if inputs.get("d", 0.0) > 0.5 else 0.0
        return {"main": w, "rcs": d - a}


class Thrusters(paperboat.Block):
    """Apply the combined autopilot and manual commands to the vehicle."""

    type, label, kind = "thrusters", "Thrusters", "function"
    inputs = ["main_auto", "rcs_auto", "main_manual", "rcs_manual"]

    def step(self, ctx, inputs) -> dict:
        lander = ctx.state
        lander.cmd_main = max(0.0, float(inputs.get("main_auto", 0.0)) + float(inputs.get("main_manual", 0.0)))
        lander.cmd_rcs = (_clamp(float(inputs.get("rcs_auto", 0.0)) + float(inputs.get("rcs_manual", 0.0)), -1.0, 1.0))
        return {}


BLOCKS = [LanderProbe, Guidance, ManualThrusters, Thrusters]
