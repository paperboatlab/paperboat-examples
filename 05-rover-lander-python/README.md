# Tutorial 05: Lunar Rover Lander

> **Level**: 05 · Intermediate  
> **Domain**: Spacecraft Arcade Simulation  
> **Language**: Python  
> **Port**: 8769  
> **UI Cockpit**: Custom Web Station  
> **Core Concepts**: `[station] view = "web"` custom HTML5/Canvas cockpit, human keyboard play vs an autonomous GNC autopilot on the Flow page.

---

## 1. Overview

A two-dimensional lunar module descends to pad **LZ-1**. The vehicle has dry mass 220 kg,
90 kg of propellant, a 4.2 kN main engine and 520 N RCS thrusters. The moon's gravity is
1.62 m/s². Touchdown is safe when `|vy| ≤ 1.5 m/s`, `|vx| ≤ 0.5 m/s`, and fuel remains.

The Flow page is the guidance computer:

```text
Lander Telemetry → GNC Autopilot ─┐
                                  ├→ Thrusters
Keyboard W/A/D → Manual Keys ─────┘
```

The autopilot follows a descent-speed profile (`0.32·√y + 0.30`), steers the horizontal
drift to the pad, and cuts the engine in the final flare. A dashboard **Switch** (or **P**)
hands control to the pilot; **W** fires the main engine and **A/D** pulse the RCS.

The Station page is the backend's own CRT cockpit (`[station] view = "web"`): a phosphor
radar grid, terrain profile, altitude and velocity tapes, propellant gauge, thruster plume
and on-screen W/A/D buttons. The page only draws and forwards keys; the backend is
authoritative. The cockpit fills the viewport, the W/A/D controls sit above Paperboat's
floating run dock, and the **⛶** button opens it fullscreen when the Station pane is small.

---

## 2. Cockpit exploration

```sh
./bin/paperboat run 05
# http://localhost:3047/?backend=ws://localhost:8769
```

1. **Watch the autopilot** land: the flame grows and shrinks as the GNC law follows the
   profile, and the Console reports `Touchdown at LZ-1`.
2. **Fly it manually**: flip the autopilot switch on the Board (or press **P**), click the
   cockpit to focus it, then hold **W / A / D**. The switch is a `dashboard/switch` monitor
   with a keyboard binding.
3. **Move the landing pad** — the floating run dock has a **landing_x** slider. Drag it while
   the autopilot flies: LZ-1, its beacon and the target marker move laterally and the GNC law
   steers to the new point. `descent_rate` and `landing_floor` in the Variables sheet
   (`Alt+V`) change the descent profile; a slower approach costs more propellant.
4. **Board** — altitude, vertical speed, fuel and target readouts plus a three-channel Scope.
5. **Station** — the custom cockpit page, served from `station/` on the backend's port.

---

## 3. Files

```text
05-rover-lander-python/
├── backend.toml          # format = 0, port 8769, solver = rk4
├── descriptor.toml       # [station] view = "web", guidance graph, variables
├── server.py             # paperboat.serve (dt = 1/60, duration = 50 s, speed 4×)
├── domain/
│   ├── __init__.py
│   ├── state.py          # Lander: 2-D flight, propellant, touchdown, scene
│   └── blocks.py         # LanderProbe, Guidance, ManualThrusters, Thrusters
├── station/
│   ├── index.html        # CRT cockpit markup
│   ├── cockpit.js        # canvas renderer, signals, key forwarding
│   └── styles.css        # phosphor palette, scanlines
├── expected.json         # touchdown at LZ-1, 0 m altitude, ~62 kg left
└── README.md
```

`station.js` (served by the engine at `/paperboat/station.js`) gives the page
`paperboat.on("signal" | "log" | …)`, `paperboat.entities`, and `paperboat.input(key, down)`.
The page never simulates anything.

---

## 4. Verification

```sh
./paperboat/bin/paperboat check paperboat-examples/05-rover-lander-python
python3 paperboat/protocol/golden.py --examples paperboat-examples 05-rover-lander-python
```
