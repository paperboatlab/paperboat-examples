"""The lunar module: 2D flight, propellant, touchdown checks and the CRT scene.

The autopilot lives on the Flow page (domain/blocks.py); this file is only the vehicle and
the moon. The custom web station (station/index.html) draws the scene the engine sends.
"""

import math

from paperboat import DomainState

G_MOON = 1.62          # m/s²
DRY_MASS = 220.0       # kg
FUEL_START = 90.0      # kg
MAIN_THRUST = 4200.0   # N
RCS_THRUST = 520.0     # N
MAIN_BURN = 6.0        # kg/s at full throttle
RCS_BURN = 0.8         # kg/s at full deflection
LAND_Y = 0.0           # m, the pad's surface
MAX_TOUCH_VY = 1.5     # m/s
MAX_TOUCH_VX = 0.5     # m/s
PAD_X = 0.0           # default; the tunable landing_x moves it
PAD_HALF = 1.1


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


class Lander(DomainState):
    """A two-dimensional lunar module above the LZ-1 pad."""

    def __init__(self) -> None:
        self.y = 70.0
        self.vy = -2.0
        self.x = -8.0
        self.vx = 0.5
        self.fuel = FUEL_START
        self.main = 0.0
        self.rcs = 0.0
        self.cmd_main = 0.0
        self.cmd_rcs = 0.0
        self.target_x = PAD_X
        self.landed = False
        self.crashed = False
        self.touchdown_vy = 0.0
        self.touchdown_vx = 0.0
        self.sim_time = 0.0

    # --- vehicle ------------------------------------------------------------------------

    def mass(self) -> float:
        return DRY_MASS + self.fuel

    def on_pad(self) -> bool:
        return abs(self.x - self.target_x) <= PAD_HALF

    def step(self, ctx) -> str | None:
        self.sim_time = ctx.t
        # The floating dock slider is a live variable: move the pad and the target with it.
        target = ctx.variable("landing_x")
        if target is not None:
            self.target_x = float(target)
        self.main = _clamp(self.cmd_main, 0.0, 1.0)
        self.rcs = _clamp(self.cmd_rcs, -1.0, 1.0)
        if self.fuel <= 0.0:
            self.fuel = 0.0
            self.main = 0.0
            self.rcs = 0.0

        mass = self.mass()
        ay = self.main * MAIN_THRUST / mass - G_MOON
        ax = self.rcs * RCS_THRUST / mass

        # Simple semi-implicit integration; the engine calls this once per clock pass.
        dt = ctx.dt
        self.vy += ay * dt
        self.y += self.vy * dt
        self.vx += ax * dt
        self.x += self.vx * dt
        self.fuel = max(0.0, self.fuel - (self.main * MAIN_BURN + abs(self.rcs) * RCS_BURN) * dt)

        if self.y <= LAND_Y and not self.landed:
            self.y = LAND_Y
            self.landed = True
            self.touchdown_vy = self.vy
            self.touchdown_vx = self.vx
            safe = abs(self.vy) <= MAX_TOUCH_VY and abs(self.vx) <= MAX_TOUCH_VX and self.on_pad()
            if safe:
                return (f"Touchdown at LZ-1: vy = {self.vy:.2f} m/s, "
                        f"vx = {self.vx:.2f} m/s, fuel = {self.fuel:.1f} kg")
            self.crashed = True
            return (f"CRASH at x = {self.x:.2f} m: vy = {self.vy:.2f} m/s, "
                    f"vx = {self.vx:.2f} m/s")
        if self.y < -2.0:
            self.crashed = True
            return "CRASH: the module went below the lunar surface"
        return None

    def summary(self) -> str:
        if self.landed and not self.crashed:
            return f"Landed safely at LZ-1 with {self.fuel:.1f} kg propellant left"
        return "Mission failed: the module did not reach LZ-1"

    # --- the station's scene --------------------------------------------------------------

    def _terrain(self) -> list[dict]:
        segments = []
        for index in range(-16, 17):
            x = index * 1.0
            # A deterministic cratered profile that stays below the pad.
            h = 0.18 + 0.12 * math.sin(index * 0.7) + 0.07 * math.cos(index * 1.9)
            if abs(x - self.target_x) < 2.0:
                h = 0.0
            segments.append({
                "id": f"terrain-{index + 16}",
                "shape": "box",
                "pos": [x, -h / 2 - 0.02, 0.0],
                "size": [1.02, max(0.04, h), 1.2],
                "color": "#3f3f46" if abs(x - self.target_x) >= 2.0 else "#64748b",
            })
        return segments

    def entities(self) -> list[dict]:
        return [
            {"id": "sky", "shape": "box", "pos": [0, 30, -1.5], "size": [40, 90, 0.1], "color": "#0b1020"},
            {"id": "pad", "shape": "box", "pos": [self.target_x, 0.02, 0.0], "size": [2.2, 0.06, 1.6], "color": "#f59e0b"},
            {"id": "pad-mark", "shape": "box", "pos": [self.target_x, 0.06, 0.0], "size": [0.7, 0.02, 0.7], "color": "#fbbf24"},
            {"id": "beacon", "shape": "line", "pos": [self.target_x, 0.1, 0.0], "to": [self.target_x, 1.4, 0.0], "color": "#facc15"},
            *self._terrain(),
            *self.patch(),
        ]

    def patch(self) -> list[dict]:
        body_y = self.y + 0.42
        tilt = 0.0
        if self.crashed:
            tilt = 0.5
        flame = []
        if self.main > 0.05 and not self.landed:
            length = 0.25 + 0.9 * self.main
            flame = [{
                "id": "flame",
                "shape": "box",
                "pos": [self.x, self.y - length / 2 + 0.02, 0.0],
                "size": [0.16 + 0.18 * self.main, length, 0.16 + 0.18 * self.main],
                "color": "#f97316" if self.main > 0.55 else "#fbbf24",
            }]
        else:
            flame = [{"id": "flame", "shape": "box", "pos": [self.x, -5.0, 0.0], "size": [0.01, 0.01, 0.01], "color": "#0b1020"}]
        return [
            {"id": "lander", "shape": "box", "pos": [self.x, body_y, 0.0], "size": [0.62, 0.5, 0.5],
             "rot": [0.0, 0.0, tilt], "color": "#d4d4d8"},
            {"id": "lander-cabin", "shape": "box", "pos": [self.x, body_y + 0.32, 0.0], "size": [0.34, 0.24, 0.34],
             "rot": [0.0, 0.0, tilt], "color": "#a1a1aa"},
            {"id": "leg-left", "shape": "line", "pos": [self.x - 0.24, self.y + 0.2, 0.0],
             "to": [self.x - 0.46, self.y + 0.01, 0.0], "color": "#71717a"},
            {"id": "leg-right", "shape": "line", "pos": [self.x + 0.24, self.y + 0.2, 0.0],
             "to": [self.x + 0.46, self.y + 0.01, 0.0], "color": "#71717a"},
            {"id": "rcs-left", "shape": "box", "pos": [self.x - 0.34, body_y, 0.0], "size": [0.08, 0.08, 0.08],
             "color": "#f87171" if self.rcs < -0.05 else "#52525b"},
            {"id": "rcs-right", "shape": "box", "pos": [self.x + 0.34, body_y, 0.0], "size": [0.08, 0.08, 0.08],
             "color": "#f87171" if self.rcs > 0.05 else "#52525b"},
            *flame,
        ]
