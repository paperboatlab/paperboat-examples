---
id: n_furuta03
created: 2026-11-16T11:00:00Z
author: bench3
kind: protocol
project: furuta
status: done
tags: [protocol, balance]
---

# Protocol: balance and arm move

Every closed-loop experiment (E1, E4, E5) is done the same way, so they compare.

1. Arm at its zero mark, the encoders reset with the pendulum hanging still (α = 180°).
2. Lift the pendulum by hand into the catch window, |α| < 5°. The loop engages at 2° and the run's
   clock starts there.
3. The flow plays the planned move from Julix's `design/trajectory.jl`: out to **60°** starting at
   1 s, hold, back to 0 at 4 s, stop at 7 s. The move's length is the shortest whose feedforward
   voltage stays within 6 V, so the loop keeps 4 V of headroom.
4. Save the run as `runs/<date>_<experiment>/run.csv` (t, u, θ, α at the loop's rate, from the
   flow's recorder), then compute the figures of merit in [[hypothesis]] in the experiment's note.
5. If the arm passes 90°, stop the run (Esc) and note it.

The trajectory is planned through the linear model's flat output: a degree-9 rest-to-rest step of
$y = q\,x$ (the last row of the inverse controllability matrix) gives the whole state
$x_{ref}(t)$ and the voltage $u_{ff}(t)$ that drives it; the loop corrects around them:

$$
u = u_{ff} - K\,(x - x_{ref})
$$

So a plan made on a wrong model is wrong twice: its feedforward pushes the rig somewhere else than
the plan says, and the loop then fights the plan.
