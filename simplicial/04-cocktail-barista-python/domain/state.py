"""The bar counter: dispenser valves, a shaker cradle, a serving glass and an E-stop.

The menu comes from `data/recipes.xlsx` (see domain/recipe.py). The station is the equipment
(ISA-88); the blocks on the Flow page are the procedure that opens valves, shakes and serves.
"""

import math

from paperboat import DomainState
from domain.recipe import RECIPES

VALVES = tuple(dict.fromkeys([pour.valve for recipe in RECIPES for pour in recipe.pours] + ["soda"]))
VALVE_X = {name: (index - (len(VALVES) - 1) / 2) * 0.42 for index, name in enumerate(VALVES)}
BOTTLE_COLORS = {
    "gin": "#dbeafe",
    "vermouth": "#fecaca",
    "campari": "#fca5a5",
    "soda": "#bae6fd",
    "prosecco": "#fef3c7",
    "aperol": "#fdba74",
}


def _clamp01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


class Barista(DomainState):
    """The beverage station's live state and its 3D stainless-steel scene."""

    def __init__(self) -> None:
        self.recipe_index = 0
        self.recipe = RECIPES[0]
        self.cup_present = True
        self.volumes = {name: 0.0 for name in VALVES}
        self.dispensing: str | None = None
        self.shake_angle = 0.0
        self.shake_energy = 0.0
        self.estop = False
        self.rinsing = False
        self.served = False
        self.sim_time = 0.0

    # --- the procedure's actions ----------------------------------------------------------

    def set_recipe(self, index: int) -> None:
        self.recipe_index = max(0, min(int(index), len(RECIPES) - 1))
        self.recipe = RECIPES[self.recipe_index]

    def pour(self, valve: str, millilitres: float) -> None:
        self.volumes[valve] = min(180.0, self.volumes.get(valve, 0.0) + max(0.0, millilitres))

    def total_ml(self) -> float:
        return sum(self.volumes.values())

    def start_dispensing(self, valve: str) -> None:
        self.dispensing = valve

    def stop_dispensing(self) -> None:
        self.dispensing = None

    def shake(self, energy: float) -> None:
        self.shake_energy = _clamp01(energy)

    # --- the run's clock ------------------------------------------------------------------

    def step(self, ctx) -> None:
        self.sim_time = ctx.t
        if self.shake_energy > 0.0:
            self.shake_angle = 0.16 * math.sin(14.0 * self.sim_time) * self.shake_energy
        else:
            self.shake_angle *= 0.85

    def summary(self) -> str:
        return f"Served {self.recipe.name}: {self.recipe.total_ml():.0f} ml"

    # --- the station's scene --------------------------------------------------------------

    def entities(self) -> list[dict]:
        liquid_level = min(0.38, 0.02 + self.total_ml() / 420.0)
        glass_x = 0.0
        mixed = self.total_ml() > 0.1

        valves = []
        for name in VALVES:
            active = self.dispensing == name
            valves.extend([
                {"id": f"valve-{name}", "shape": "box", "pos": [VALVE_X[name], 1.18, 0.0],
                 "size": [0.16, 0.26, 0.16], "color": "#e2e8f0"},
                {"id": f"led-{name}", "shape": "sphere", "pos": [VALVE_X[name], 1.34, 0.0],
                 "size": [0.07, 0.07, 0.07], "color": "#22c55e" if active else "#334155"},
            ])
            if active:
                valves.append({
                    "id": f"stream-{name}", "shape": "box", "pos": [VALVE_X[name], 0.86, 0.0],
                    "size": [0.035, 0.46, 0.035], "color": "#fbbf24",
                })

        entities = [
            {"id": "counter", "shape": "box", "pos": [0.0, -0.86, 0.0], "size": [3.6, 0.16, 1.3], "color": "#64748b"},
            {"id": "drip-tray", "shape": "box", "pos": [0.0, -0.76, 0.24], "size": [1.4, 0.04, 0.7], "color": "#334155"},
            {"id": "gantry", "shape": "box", "pos": [0.0, 1.5, 0.0], "size": [3.0, 0.1, 0.24], "color": "#94a3b8"},
            *valves,
            {"id": "glass", "shape": "box", "pos": [glass_x, -0.52, 0.2], "size": [0.34, 0.46, 0.34], "color": "#cbd5e1"},
            {"id": "liquid", "shape": "box", "pos": [glass_x, -0.74 + liquid_level / 2, 0.2],
             "size": [0.29, liquid_level, 0.29],
             "color": "#dc2626" if mixed and not self.rinsing else "#f8fafc"},
            {"id": "shaker-base", "shape": "box", "pos": [-0.95, -0.7, 0.18], "size": [0.5, 0.12, 0.4], "color": "#475569"},
            {"id": "shaker-cup", "shape": "box", "pos": [-0.95, -0.48, 0.18], "size": [0.3, 0.36, 0.3],
             "rot": [0.0, 0.0, self.shake_angle], "color": "#94a3b8"},
            {"id": "estop-base", "shape": "box", "pos": [1.58, -0.7, 0.24], "size": [0.28, 0.08, 0.28], "color": "#1e293b"},
            {"id": "estop-button", "shape": "sphere", "pos": [1.58, -0.6, 0.24], "size": [0.17, 0.17, 0.17],
             "color": "#ef4444" if self.estop else "#b91c1c"},
            {"id": "shelf", "shape": "box", "pos": [0.0, 1.05, -0.48], "size": [3.2, 0.08, 0.3], "color": "#78350f"},
        ]
        for index, name in enumerate(VALVES):
            entities.append({
                "id": f"bottle-{name}",
                "shape": "box",
                "pos": [VALVE_X[name], 1.3, -0.48],
                "size": [0.18, 0.42, 0.18],
                "color": BOTTLE_COLORS.get(name, "#e2e8f0"),
            })
        return entities
