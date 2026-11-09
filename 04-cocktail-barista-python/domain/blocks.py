"""The barista's Flow blocks: Excel-driven recipe stages and the station probes."""

import paperboat


class CupSensor(paperboat.Block):
    """The optical cup sensor and the glass's current volume."""

    type, label, kind = "cup_sensor", "Cup Sensor · Optical", "probe"
    outputs = ["present", "fill_ml", "total_ml"]

    def step(self, ctx, inputs) -> dict:
        bar = ctx.state
        return {
            "present": 1.0 if bar.cup_present else 0.0,
            "fill_ml": bar.total_ml(),
            "total_ml": bar.total_ml(),
        }


class RecipeChoice(paperboat.Block):
    """Read the Board's choice and make it the bar's current recipe."""

    type, label, kind = "recipe_choice", "Recipe Choice", "function"
    inputs = ["index"]

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        self.last = None

    def step(self, ctx, inputs) -> dict:
        index = int(round(float(inputs.get("index", 0.0))))
        if index != self.last:
            self.last = index
            ctx.state.set_recipe(index)
            ctx.log(f"menu: {ctx.state.recipe.name}")
        return {}


class CheckCup(paperboat.Step):
    """Recipe start: wait for a glass on the drip tray, then hand the path on."""

    type, label = "check_cup", "Detect Cup"

    def enter(self, ctx, inputs) -> None:
        if not ctx.state.cup_present:
            ctx.log("no cup on the tray: place a glass to start")
        else:
            ctx.log(f"cup detected: beginning {ctx.state.recipe.name}")

    def tick(self, ctx, inputs) -> str:
        return "next" if ctx.state.cup_present else ""


class Dispense(paperboat.Step):
    """Pour one stage of the selected recipe, at the workbook's volume and rate."""

    type, label = "dispense", "Dispense"
    outputs = [paperboat.Port("next", "step"), paperboat.Port("progress")]
    params = {"stage": 1}

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        self.progress = 0.0

    def enter(self, ctx, inputs) -> None:
        self.stage = max(1, int(self.params.get("stage", 1))) - 1
        pours = ctx.state.recipe.pours
        self.pour = pours[self.stage] if self.stage < len(pours) else None
        self.elapsed = 0.0
        self.poured = 0.0
        self.progress = 0.0
        if self.pour is None:
            ctx.log(f"recipe has no stage {self.stage + 1}; skipping")
            return
        ctx.state.start_dispensing(self.pour.valve)
        ctx.log(f"pour {self.pour.millilitres:.0f} ml {self.pour.valve}")

    def tick(self, ctx, inputs) -> str:
        if self.pour is None:
            return "next"
        self.elapsed += ctx.dt
        target = self.pour.millilitres * min(1.0, self.elapsed / max(self.pour.seconds, 1e-3))
        delta = target - self.poured
        if delta > 0.0:
            ctx.state.pour(self.pour.valve, delta)
            self.poured = target
        self.progress = min(1.0, self.elapsed / max(self.pour.seconds, 1e-3))
        if self.progress >= 1.0:
            ctx.state.stop_dispensing()
            ctx.log(f"{self.pour.valve} pour complete")
            return "next"
        return ""

    def current(self) -> dict:
        return {"progress": self.progress}


class ShakeChill(paperboat.Step):
    """Run the rotary shaker for the recipe's shake time, then hand the path on."""

    type, label = "shake_chill", "Shake & Chill"
    outputs = [paperboat.Port("next", "step"), paperboat.Port("progress")]

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        self.progress = 0.0

    def enter(self, ctx, inputs) -> None:
        self.seconds = max(0.0, ctx.state.recipe.shake_seconds)
        self.elapsed = 0.0
        self.progress = 0.0
        self.finished = False
        if self.seconds > 0:
            ctx.state.shake(1.0)
            ctx.log(f"shake & chill: agitation for {self.seconds:.1f} s")

    def tick(self, ctx, inputs) -> str:
        if self.seconds <= 0:
            return "next"
        self.elapsed += ctx.dt
        self.progress = min(1.0, self.elapsed / self.seconds)
        ctx.state.shake(1.0 - self.progress * 0.5)
        if self.progress >= 1.0 and not self.finished:
            self.finished = True
            ctx.state.shake(0.0)
            ctx.log("shake & chill: drink strained and chilled")
            return "next"
        return ""

    def current(self) -> dict:
        return {"progress": self.progress}


class Serve(paperboat.Step):
    """Finish the order: report it on the Console and close the recipe path."""

    type, label = "serve", "Strain & Serve"

    def enter(self, ctx, inputs) -> None:
        bar = ctx.state
        bar.served = True
        ctx.log(f"Order complete: {bar.recipe.name} ({bar.recipe.total_ml():.0f} ml)")

    def tick(self, ctx, inputs) -> str:
        return "next"


class EmergencyStop(paperboat.Step):
    """Priority interrupt: close every valve and start the clean-in-place rinse."""

    type, label = "emergency_stop", "Emergency Stop"

    def enter(self, ctx, inputs) -> None:
        bar = ctx.state
        bar.estop = True
        bar.rinsing = True
        bar.stop_dispensing()
        ctx.log("EMERGENCY STOP: all valves closed, rinse cycle started")

    def tick(self, ctx, inputs) -> str:
        return "next"


class Rinse(paperboat.Timed):
    """Clean-in-place rinse after an E-stop; ends with the rig ready again."""

    type, label = "rinse", "Clean-in-Place Rinse"
    params = {"seconds": 1.0}

    def begin(self, ctx, inputs) -> None:
        self.finished = False

    def advance(self, ctx, start: float, end: float) -> None:
        if end >= 0.999 and not self.finished:
            self.finished = True
            ctx.state.estop = False
            ctx.state.rinsing = False
            ctx.state.volumes = {name: 0.0 for name in ctx.state.volumes}
            ctx.log("rinse complete: rig ready")


class RecipeStage(paperboat.Block):
    """A readout of the menu, how much has been poured and whether the order is served."""

    type, label, kind = "recipe_stage", "Recipe · Stage", "probe"
    outputs = ["fill_ml", "served", "estop", "recipe_index"]

    def step(self, ctx, inputs) -> dict:
        bar = ctx.state
        return {
            "fill_ml": bar.total_ml(),
            "served": 1.0 if bar.served else 0.0,
            "estop": 1.0 if bar.estop else 0.0,
            "recipe_index": float(bar.recipe_index),
        }


BLOCKS = [CupSensor, RecipeChoice, CheckCup, Dispense, ShakeChill, Serve, EmergencyStop, Rinse, RecipeStage]
