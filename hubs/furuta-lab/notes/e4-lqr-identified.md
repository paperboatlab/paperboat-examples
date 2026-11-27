---
id: n_furuta07
created: 2026-11-20T14:00:00Z
author: bench3
kind: experiment
project: furuta
status: done
tags: [e4, lqr, redesign]
---

# E4: the LQR redesigned on the identified model

The same Julix scripts as E1, the same weights, on `flows/out/identified.toml` ([[e3-greybox]]):
`LQR_PARAMS=identified` for `design/lqr.jl` and `design/trajectory.jl`.

$$
K = [-9.65,\ -80.8,\ -4.01,\ -7.58]
$$

The gain hardly moved: the pendulum's angle and rate terms by 14–16 %, the arm's rate by 10 %, its
angle by under 1 %. The plan did: the
weaker motor and the heavier, longer pendulum make the move take 0.72 s instead of 0.64 s for the
same 6 V, the pendulum leaning 11.1° instead of 14.0°.

**Flow**: `flows/e4-lqr-identified.psf` (E1's flow with the identified gain and plan). **Run**:
`runs/2026-11-20_e4-lqr-identified/run.csv`, by [[protocol-balance-move]].

## Result

| | E1 datasheet | **E4 identified** |
| --- | --- | --- |
| max \|α − α_ref\| | 12.96° | **1.64°** |
| RMS α − α_ref | 2.89° | **0.39°** |
| RMS θ − θ_ref | 8.55° | **1.99°** |
| max \|θ\| | 85.6° | **68.6°** |
| saturated | 5.9 % | **0** |

![[pendulum-error.svg|The pendulum off its plan: E1 against E4 and E5]]

```julia
include("../tools/notebook.jl")
figures("../runs/2026-11-20_e4-lqr-identified/run.csv", "../design/out/trajectory-identified.csv")
```

The arm still overshoots its 60° by 8.6°, and hunts about ±2.4° around its plan at the holds
([[issue-arm-hunting]]); the voltage never reached the amplifier's limit (7.5 V at most).

**So far** the identification alone takes the pendulum's worst deviation from 12.96° to 1.64°, 87 %
less: H1's bar (5.2°) is cleared before MPC enters. [[e5-mpc]] asks what MPC adds.
