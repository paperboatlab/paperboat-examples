---
id: n_furuta05
created: 2026-11-18T10:00:00Z
author: bench3
kind: experiment
project: furuta
status: done
tags: [e2, identification, excitation]
---

# E2: excitation runs

Two runs to identify the rig from ([[e3-greybox]]): one to fit, one kept apart to check the model on.

**Set-up.** The pendulum hanging (stable, so the run needs no controller that depends on the model we
are after). The arm on a gentle PD loop, $u = 4\,(r - \theta) - 0.08\,\dot\theta + v$, so it stays
inside ±90°, around a chirp $r$ (±30°, 0.2 → 2.5 Hz over 20 s); $v$ a ±2 V PRBS held 150 ms (a hash of the slot and the seed, so the
flow's function block makes the same one as `tools/make_runs.jl`). The
chirp sweeps through the pendulum's swing (about 1.5 Hz hanging); the PRBS keeps the voltage rich and
breaks the voltage's correlation with the arm's angle that the PD loop would otherwise make.

**Flow** (Simplicial): `flows/excite.psf`, with the station's `alpha0` set to π (hanging). Seeds 1
and 2 for the PRBS.

**Runs**: `runs/2026-11-18_e2-excitation/identification.csv` (seed 1) and `validation.csv` (seed 2),
20 s each at 500 Hz.

## Notes on the runs

- A first try with a ±3 V PRBS and a softer loop (gain 1.5) drove the arm into its end stop at −101°.
  Discarded; the gain went to 4, the chirp to ±30° and the PRBS to ±2 V. The kept runs stay within
  −79° and +69° (identification) and −82° and +86° (validation).
- The pendulum swings up to 65° about hanging: well into the nonlinear range, as wanted.

```julia
include("../tools/notebook.jl")
r = read_csv("../runs/2026-11-18_e2-excitation/identification.csv")
(theta_deg = round.(extrema(rad2deg.(r.theta)), digits = 1),
 swing_deg = round.(extrema(rad2deg.(r.alpha)) .- 180, digits = 1),
 volts = round.(extrema(r.u), digits = 2))
```
