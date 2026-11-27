# Tutorial 04: Cocktail Barista

> **Level**: 04 · Intermediate  
> **Domain**: Beverage Process Automation  
> **Language**: Python  
> **Port**: 51304  
> **UI Cockpit**: Inspector / Step Flow  
> **Core Concepts**: Step-flow tokens, visual groups (`Ctrl+G`), subsystems, priority keyboard interrupts, Console logs.

---

## 1. Overview

The bar is the equipment; the Flow page is the recipe. A **Step flow** moves one path from
block to block along dark step wires. `Start` fires once, each pour holds the path for its
duration, and `Shake & Chill` is a reusable subsystem. A second hat — `When Space rises` —
runs beside the recipe, so pressing **Space** closes every valve and starts a clean-in-place
rinse even while a drink is being made.

- **Powders are volumes**: a pour adds millilitres at a constant rate over `seconds`.
- **Hysteresis-free sequence**: one token, one active stage, so the audit trail is exact.
- **Priority interrupt**: the E-stop path is independent of the recipe path.

The menu is read from the bar manager's Excel workbook, `data/recipes.xlsx`: one row per
pour, with the drink name, valve, millilitres, pour time, shake time and garnish. The
starter menu has **Negroni**, **Spritz** and **Americano**. Pick one with the **Choice**
control on the Board (or the Variables dock); the recipe stages read the same workbook.

---

## 2. Cockpit exploration

```sh
paperboat run 04
# http://localhost:30471/?station=ws://localhost:51304
```

1. **Flow** — watch the token walk `Start → Detect Cup → Pour Base → Shake & Chill →
   Strain & Serve → Stop`. Each Dispense block shows its progress while it holds the path.
2. **Groups and subsystem** — `Pour Base` is a visual frame; `Shake & Chill` is a subsystem.
   Double-click it to open its own level, then use the breadcrumb (or `Escape`) to return.
3. **Emergency stop** — press **Space**. The `When` hat fires, the valves close, the E-stop
   mushroom turns red, and the Console records the rinse. The recipe path resumes when the
   rinse ends; press Space again to interrupt it.
4. **Menu** — the Board's Choice control selects a drink from the Excel workbook. Edit
   `data/recipes.xlsx` and restart the station to add a row or a new drink; the dispense and
   shake times are read from the sheet.
5. **Station** — the stainless counter, four-valve gantry with LEDs, rotary shaker and the
   rising liquid level in the serving glass.
6. **Board** — the Scope plots fill volume and served state, and the Console streams the
   pour-by-pour audit trail.

---

## 3. Files

```text
04-cocktail-barista-python/
├── station.toml          # format = 0, port 51304, solver = discrete
├── descriptor.toml       # variables, Step-flow starter, groups, board
├── station.py            # the station file: registers the bar and the blocks (paperboat_runtime)
├── data/
│   └── recipes.xlsx      # the bar manager's recipe sheet
├── domain/
│   ├── __init__.py
│   ├── recipe.py         # stdlib XLSX reader; RECIPES/BY_NAME
│   ├── state.py          # Barista, the bar (a station object): valves, volumes, shaker, E-stop, scene
│   └── blocks.py         # CupSensor, CheckCup, Dispense, ShakeChill, Serve…
├── expected.json         # golden run: 90 ml served, Negroni log
├── example.toml          # how the golden harness runs it (docs/golden.md)
└── README.md
```

The station's code runs out of process, in a Python runtime `paperboatd` leases; `station.py`
registers each type with its definition (Simplicial's docs/stations.rst). The bar is a station
object (`[station] objects`): the engine makes one per run and steps it after each pass, and the
blocks reach it through `state.current()`. Each step block is `"base": "step"` with
`enter(ctx, inputs)` and `tick(ctx, inputs)`, which returns the port to leave by (`"next"`, or
`""` to stay); the timed ones (`Dispense`, `ShakeChill`, `Rinse`) count their own time from
`ctx["dt"]` and output their `progress`. When the run is done the Console shows the bar's
`served` and `fill_ml`.

---

## 4. Verification

```sh
python3 golden.py simplicial/04-cocktail-barista-python   # from the repository root: run, compare
paperboat check simplicial/04-cocktail-barista-python     # manifest, catalog, smoke and golden
```
