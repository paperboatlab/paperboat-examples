---
id: n_furuta04
created: 2026-11-17T14:00:00Z
author: bench3
kind: experiment
project: furuta
status: done
tags: [e1, lqr, baseline]
---

# E1: the datasheet LQR on the rig

The baseline for [[hypothesis]]: gain and plan both from the datasheet, run by
[[protocol-balance-move]].

**Design** (Julix, `design/lqr.jl` and `design/trajectory.jl` on `design/datasheet.toml`):
discrete LQR at 2 ms, $Q = \mathrm{diag}(100, 300, 0.3, 0.3)$, $R = 1$:

$$
K = [-9.61,\ -70.9,\ -3.65,\ -6.54]
$$

The planned move takes 0.64 s each way, the pendulum leaning up to 14.0° and the feedforward peaking
at 6.1 V. **Flow** (Simplicial): `flows/e1-lqr-datasheet.psf`. **Run**:
`runs/2026-11-17_e1-lqr-datasheet/run.csv`.

## Result

It held the pendulum, but not the plan. On the way out the arm ran past its 60° to **85.6°**, 4.4°
short of the cables' limit, and the pendulum went **13.0°** off its plan; the amplifier sat at
10 V for 5.9 % of the run, the loop asking for up to 17.7 V.

![[e1-arm.svg|The arm against its plan]]

```julia
include("../tools/notebook.jl")
figures("../runs/2026-11-17_e1-lqr-datasheet/run.csv", "../design/out/trajectory-datasheet.csv")
# (max_alpha_err = 12.96, rms_alpha_err = 2.89, rms_track = 8.55, max_theta = 85.6, saturated_pct = 5.9, peak_u = 17.7)
```

The overshoot is the feedforward: it is the datasheet's voltage for the datasheet's pendulum, and the
arm on the rig answers it differently. The loop then pulls back hard, saturates, and the pendulum
swings off.

## Decision

The datasheet isn't good enough to plan on: identify the rig before comparing controllers
([[e2-excitation]]). E1 stays the baseline for H1: 12.96° is the number to beat by 60 %, i.e. 5.2°.
