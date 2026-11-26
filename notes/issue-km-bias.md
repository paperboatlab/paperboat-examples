---
id: n_furuta10
created: 2026-11-19T17:00:00Z
author: bench3
kind: issue
project: furuta
status: open
tags: [identification, motor, dead band]
---

# Is the motor really 20 % weak, or is it the amplifier?

[[e3-greybox]] puts $k_m$ at 0.0358 N m/A against the datasheet's 0.045, with a standard error of
0.0003. The standard error only counts the noise: it says nothing of what the model leaves out.

What the model leaves out sits right in the voltage path: the amplifier has a dead band (we read
about 0.15 V on the scope, no load), and the loop's 2 ms lag. With the PRBS at ±2 V a 0.15 V dead
band takes 7 % off every voltage the fit sees, and the fit can only put that in $k_m$. $m_p$ comes
out a little low too (0.0313 kg; the magnet and its screw should make it about 0.034), and $J_{\hat r}$
scales with it: the fit trades inertia for motor constant.

To settle it:
- Measure $k_m$ directly: back-emf with the arm spun by hand, or a locked-rotor torque.
- Fit again with the dead band in the model (one more parameter), or with a larger excitation where
  it matters less.
- Weigh the pendulum and its magnet.

Doesn't block the study: the identified model fits the validation run at 91–94 % and the redesign
works ([[e4-lqr-identified]]). It matters for the next study, which pushes the voltage harder.
