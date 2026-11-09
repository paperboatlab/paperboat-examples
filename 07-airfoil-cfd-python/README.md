# Tutorial 07: Airfoil CFD Wind Tunnel

> **Level**: 07 · Advanced  
> **Domain**: Aerodynamics & Fluid Dynamics  
> **Language**: Python  
> **Port**: 8771  
> **UI Cockpit**: Navigator Mode  
> **Core Concepts**: D2Q9 lattice-Boltzmann solver, NACA 0012 mask, 2-D velocity field, lift/drag polars, stall.

---

## 1. Overview

The backend runs a 2-D **D2Q9 lattice-Boltzmann** wind tunnel around a NACA 0012 profile at
a variable angle of attack.

- **Lattice**: 160 × 80 cells, nine discrete velocities, BGK collision with `τ = 0.53`.
- **Obstacle**: a NACA 0012 thickness mask rotated by `alpha`; populations that enter a solid
  node reflect (bounce-back).
- **Boundaries**: steady free stream on the left, zero-gradient on the right, periodic top and
  bottom.
- **Polars**: lift follows the linear slope up to 14° and breaks past stall; drag rises with
  `sin²α` plus a stall term. `C_L`, `C_D` and `L/D` stream to the Board.

The Flow page is the tunnel pipeline:

```text
alpha → NACA 0012 Mask ─┐
                        ├→ LBM Step (D2Q9) → steps / residual
speed → Inflow ─────────┘
                        └→ Lift & Drag Polars → CL, CD, L/D
```

Tuning `alpha` rebuilds the mask and restarts the field; watch it separate and the lift curve
break past 14°. The Station page draws velocity arrows coloured by speed, streamlines, the
airfoil outline, the chord line and lift/drag arrows.

---

## 2. Cockpit exploration

```sh
./bin/paperboat run 07
# http://localhost:3047/?backend=ws://localhost:8771
```

1. **Variables** (`Alt+V`) — `alpha` is tunable: try `0°`, `6°`, `14°`, `20°`, `25°`.
   `flow_speed` changes the free stream. Both are live `variable` blocks on the canvas.
2. **Board** — `C_L`, `C_D`, `L/D` readouts and a Scope; `display-steps` counts lattice steps.
3. **Station** — the wind-tunnel frame, rotating airfoil, vector field, streamlines and force
   vectors; the field settles over a few seconds after each change.
4. **Console** — periodic `LBM <n> steps, residual …` convergence lines.

The lattice is pure NumPy; a full run is a few seconds on a laptop.

---

## 3. Files

```text
07-airfoil-cfd-python/
├── backend.toml          # format = 0, port 8771, solver = discrete
├── descriptor.toml       # wind-tunnel variables, LBM flow, dashboard
├── server.py             # paperboat.serve (dt = 0.1, duration = 9 s)
├── domain/
│   ├── __init__.py
│   ├── airfoil.py        # NACA 0012 mask and outline
│   ├── lbm_solver.py     # D2Q9 equilibrium, collision, streaming, bounce-back
│   ├── forces.py         # lift/drag polars with the stall break
│   ├── state.py          # WindTunnel: lattice, scene, arrows and streamlines
│   └── blocks.py         # Airfoil, Inflow, LbmStep, Forces
├── expected.json         # golden run: C_L ≈ 0.591 at 6°, 546 lattice steps
└── README.md
```

---

## 4. Verification

```sh
./paperboat/bin/paperboat check paperboat-examples/07-airfoil-cfd-python
python3 paperboat/protocol/golden.py --examples paperboat-examples 07-airfoil-cfd-python
```
