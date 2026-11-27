---
id: n_furuta02
created: 2026-11-16T10:00:00Z
author: bench3
kind: plan
project: furuta
status: done
tags: [hypothesis, metrics]
---

# Hypothesis and how we measure it

**H1.** On the same planned arm move (out to 60° and back, see [[protocol-balance-move]]), an MPC on a
grey-box-identified model keeps the pendulum within **40 %** of the datasheet LQR's worst deviation
from its plan, max |α − α_ref|, with the arm within ±90° and the voltage within ±10 V.

**H0.** It doesn't: the datasheet is close enough, or MPC adds nothing.

The datasheet LQR is the baseline ([[e1-lqr-datasheet]]). If E1 is clearly off, we identify the rig
([[e2-excitation]], [[e3-greybox]]), and then compare two loops on the identified model: the same LQR
design ([[e4-lqr-identified]]) and MPC ([[e5-mpc]]). The comparison tells the identification's share
from the MPC's.

## Figures of merit, every closed-loop run

| | |
| --- | --- |
| max \|α − α_ref\| | the pendulum's worst deviation from its plan: **H1's measure** |
| RMS α − α_ref | the same over the whole run |
| RMS θ − θ_ref | how well the arm follows its plan |
| max \|θ\| | must stay under 90° |
| saturated | share of samples with the voltage at ±10 V |

The reference is the plan's whole state, not only the arm's angle: during a move the pendulum is
*meant* to lean (about 11–14°, that's what accelerates the arm under it), so a deviation is what
counts.

## What would change the plan

- The pendulum falls in E1: identify first, then compare (it didn't fall, but see E1).
- The identified model fits the validation run worse than 80 % on α: identify again, with a richer
  excitation, before any redesign.
