"""The barista's Flow blocks: Excel-driven recipe stages and the station probes.

Each acts on the bar, the station object (domain/state.py), through `current()`; station.py
registers them with their ports and params.
"""

import paperboat_runtime as pb

from domain.state import current


class CupSensor:
    """The optical cup sensor and the glass's current volume."""

    def step(self, ctx, inputs) -> dict:
        bar = current()
        return {
            "present": 1.0 if bar.cup_present else 0.0,
            "fill_ml": bar.total_ml(),
            "total_ml": bar.total_ml(),
        }


class RecipeChoice:
    """Read the Board's choice and make it the bar's current recipe."""

    def __init__(self) -> None:
        self.last = None

    def step(self, ctx, inputs) -> dict:
        index = int(round(float(inputs.get("index", 0.0))))
        if index != self.last:
            self.last = index
            current().set_recipe(index)
            pb.log(f"menu: {current().recipe.name}")
        return {}


class CheckCup:
    """Recipe start: wait for a glass on the drip tray, then hand the path on."""

    def enter(self, ctx, inputs) -> None:
        if not current().cup_present:
            pb.log("no cup on the tray: place a glass to start")
        else:
            pb.log(f"cup detected: beginning {current().recipe.name}")

    def tick(self, ctx, inputs) -> str:
        return "next" if current().cup_present else ""


class Dispense:
    """Pour one stage of the selected recipe, at the workbook's volume and rate."""

    def __init__(self, stage: float = 1) -> None:
        self.stage = max(1, int(stage)) - 1
        self.progress = 0.0

    def enter(self, ctx, inputs) -> None:
        pours = current().recipe.pours
        self.pour = pours[self.stage] if self.stage < len(pours) else None
        self.elapsed = 0.0
        self.poured = 0.0
        self.progress = 0.0
        if self.pour is None:
            pb.log(f"recipe has no stage {self.stage + 1}; skipping")
            return
        current().start_dispensing(self.pour.valve)
        pb.log(f"pour {self.pour.millilitres:.0f} ml {self.pour.valve}")

    def tick(self, ctx, inputs) -> str:
        if self.pour is None:
            return "next"
        self.elapsed += ctx["dt"]
        target = self.pour.millilitres * min(1.0, self.elapsed / max(self.pour.seconds, 1e-3))
        delta = target - self.poured
        if delta > 0.0:
            current().pour(self.pour.valve, delta)
            self.poured = target
        self.progress = min(1.0, self.elapsed / max(self.pour.seconds, 1e-3))
        if self.progress >= 1.0:
            current().stop_dispensing()
            pb.log(f"{self.pour.valve} pour complete")
            return "next"
        return ""

    def outputs(self) -> dict:
        return {"progress": self.progress}


class ShakeChill:
    """Run the rotary shaker for the recipe's shake time, then hand the path on."""

    def __init__(self) -> None:
        self.progress = 0.0

    def enter(self, ctx, inputs) -> None:
        self.seconds = max(0.0, current().recipe.shake_seconds)
        self.elapsed = 0.0
        self.progress = 0.0
        self.finished = False
        if self.seconds > 0:
            current().shake(1.0)
            pb.log(f"shake & chill: agitation for {self.seconds:.1f} s")

    def tick(self, ctx, inputs) -> str:
        if self.seconds <= 0:
            return "next"
        self.elapsed += ctx["dt"]
        self.progress = min(1.0, self.elapsed / self.seconds)
        current().shake(1.0 - self.progress * 0.5)
        if self.progress >= 1.0 and not self.finished:
            self.finished = True
            current().shake(0.0)
            pb.log("shake & chill: drink strained and chilled")
            return "next"
        return ""

    def outputs(self) -> dict:
        return {"progress": self.progress}


class Serve:
    """Finish the order: report it on the Console and close the recipe path."""

    def enter(self, ctx, inputs) -> None:
        bar = current()
        bar.served = True
        pb.log(f"Order complete: {bar.recipe.name} ({bar.recipe.total_ml():.0f} ml)")

    def tick(self, ctx, inputs) -> str:
        return "next"


class EmergencyStop:
    """Priority interrupt: close every valve and start the clean-in-place rinse."""

    def enter(self, ctx, inputs) -> None:
        bar = current()
        bar.estop = True
        bar.rinsing = True
        bar.stop_dispensing()
        pb.log("EMERGENCY STOP: all valves closed, rinse cycle started")

    def tick(self, ctx, inputs) -> str:
        return "next"


class Rinse:
    """Clean-in-place rinse after an E-stop, over `seconds`; ends with the rig ready again."""

    def __init__(self, seconds: float = 1.0) -> None:
        self.seconds = seconds
        self.progress = 0.0

    def enter(self, ctx, inputs) -> None:
        self.elapsed = 0.0
        self.progress = 0.0

    def tick(self, ctx, inputs) -> str:
        self.elapsed += ctx["dt"]
        self.progress = min(1.0, self.elapsed / max(self.seconds, 1e-3))
        if self.progress < 1.0:
            return ""
        bar = current()
        bar.estop = False
        bar.rinsing = False
        bar.volumes = {name: 0.0 for name in bar.volumes}
        pb.log("rinse complete: rig ready")
        return "next"

    def outputs(self) -> dict:
        return {"progress": self.progress}


class RecipeStage:
    """A readout of the menu, how much has been poured and whether the order is served."""

    def step(self, ctx, inputs) -> dict:
        bar = current()
        return {
            "fill_ml": bar.total_ml(),
            "served": 1.0 if bar.served else 0.0,
            "estop": 1.0 if bar.estop else 0.0,
            "recipe_index": float(bar.recipe_index),
        }
