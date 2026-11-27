"""04-cocktail-barista-python: automated beverage recipes as a Step flow (Level 04).

The bar (domain/state.py) is the equipment, a station object; the Flow page is the recipe: a Start
hat, a Detect Cup check, three Dispense steps, the Shake & Chill subsystem, and Strain & Serve. A
second hat (When the Space key rises) interrupts any recipe with an emergency stop and a
clean-in-place rinse, so several paths run side by side.

The engine loads this file into a Python runtime (paperboat_runtime); each type is registered
with its definition: its ports, its params and, for a step, `"base": "step"`.
"""

import paperboat_runtime as pb

from domain import blocks
from domain.state import Barista

IN = {"id": "in", "type": "step"}      # a step's path arrives here
NEXT = {"id": "next", "type": "step"}  # and leaves here

pb.register("barista", Barista, definition={
    "base": "object",
    "label": "Bar Counter",
    "description": "Dispenser valves, a shaker cradle, a serving glass and an E-stop",
})
pb.register("cup_sensor", blocks.CupSensor, definition={
    "label": "Cup Sensor · Optical", "kind": "probe", "outputs": ["present", "fill_ml", "total_ml"],
})
pb.register("recipe_choice", blocks.RecipeChoice, definition={"label": "Recipe Choice", "inputs": ["index"]})
pb.register("check_cup", blocks.CheckCup, definition={
    "base": "step", "label": "Detect Cup", "inputs": [IN], "outputs": [NEXT],
})
pb.register("dispense", blocks.Dispense, definition={
    "base": "step", "label": "Dispense", "inputs": [IN], "outputs": [NEXT, "progress"], "params": {"stage": 1},
})
pb.register("shake_chill", blocks.ShakeChill, definition={
    "base": "step", "label": "Shake & Chill", "inputs": [IN], "outputs": [NEXT, "progress"],
})
pb.register("serve", blocks.Serve, definition={
    "base": "step", "label": "Strain & Serve", "inputs": [IN], "outputs": [NEXT],
})
pb.register("emergency_stop", blocks.EmergencyStop, definition={
    "base": "step", "label": "Emergency Stop", "inputs": [IN], "outputs": [NEXT],
})
pb.register("rinse", blocks.Rinse, definition={
    "base": "step", "label": "Clean-in-Place Rinse", "inputs": [IN], "outputs": [NEXT, "progress"],
    "params": {"seconds": 1.0},
})
pb.register("recipe_stage", blocks.RecipeStage, definition={
    "label": "Recipe · Stage", "kind": "probe", "outputs": ["fill_ml", "served", "estop", "recipe_index"],
})
