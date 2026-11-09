# Tutorial 04: Cocktail Barista

> **Level**: 04 · Intermediate  
> **Domain**: Beverage Process Automation  
> **Language**: Python  
> **Port**: 8768  
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
./bin/paperboat run 04
# http://localhost:3047/?backend=ws://localhost:8768
```

1. **Flow** — watch the token walk `Start → Detect Cup → Pour Base → Shake & Chill →
   Strain & Serve → Stop`. Each Dispense block shows its progress while it holds the path.
2. **Groups and subsystem** — `Pour Base` is a visual frame; `Shake & Chill` is a subsystem.
   Double-click it to open its own level, then use the breadcrumb (or `Escape`) to return.
3. **Emergency stop** — press **Space**. The `When` hat fires, the valves close, the E-stop
   mushroom turns red, and the Console records the rinse. The recipe path resumes when the
   rinse ends; press Space again to interrupt it.
4. **Menu** — the Board's Choice control selects a drink from the Excel workbook. Edit
   `data/recipes.xlsx` and restart the backend to add a row or a new drink; the dispense and
   shake times are read from the sheet.
5. **Station** — the stainless counter, four-valve gantry with LEDs, rotary shaker and the
   rising liquid level in the serving glass.
6. **Board** — the Scope plots fill volume and served state, and the Console streams the
   pour-by-pour audit trail.

---

## 3. Files

```text
04-cocktail-barista-python/
├── backend.toml          # format = 0, port 8768, solver = discrete
├── descriptor.toml       # variables, Step-flow starter, groups, dashboard
├── server.py             # paperboat.serve (mode = "clock", step blocks)
├── data/
│   └── recipes.xlsx      # the bar manager's recipe sheet
├── domain/
│   ├── __init__.py
│   ├── recipe.py         # stdlib XLSX reader; RECIPES/BY_NAME
│   ├── state.py          # Barista: valves, volumes, shaker, E-stop, scene
│   └── blocks.py         # CupSensor, CheckCup, Dispense (Timed), ShakeChill, Serve…
├── expected.json         # golden run: 90 ml served, Negroni log
└── README.md
```

The Timed blocks (`Dispense`, `ShakeChill`, `Rinse`) derive from `paperboat.Timed` and
implement `advance(ctx, start, end)`; the engine owns the clock, the progress output and the
step wire. Everything else is a `paperboat.Step` with `enter()` / `tick()`.

---

## 4. Verification

```sh
./paperboat/bin/paperboat check paperboat-examples/04-cocktail-barista-python
python3 paperboat/protocol/golden.py --examples paperboat-examples 04-cocktail-barista-python
```
