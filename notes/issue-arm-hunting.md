---
id: n_furuta09
created: 2026-11-21T09:30:00Z
author: bench3
kind: issue
project: furuta
status: open
tags: [arm, friction, dead band]
---

# The arm hunts 2–4° at the holds

In every closed-loop run the arm wanders around its plan when it should rest: at 60° and at 0, up to
2.4° off with the LQR and 4.0° with the MPC, a mean under 1.6°. Same on either loop, on either model ([[e4-lqr-identified]],
[[e5-mpc]]).

Likely cause: the arm's Coulomb friction (1.2 mN m, [[e3-greybox]]) and the amplifier's dead band
(about 0.15 V, [[issue-km-bias]]). Breaking the friction takes $f_c R_m / k_m \approx 0.25$ V, plus
the dead band, 0.40 V; with $K_\theta \approx 9.6$ V/rad the arm has to be 2.4° off before it moves,
which is the hunting's size. The pendulum's loop then pulls it back past.

To try:
- Integral action on the arm (augment the state with $\int (\theta - \theta_{ref})$).
- A friction feedforward, $f_c\,\mathrm{sign}(\dot\theta_{ref})\,R_m/k_m$, and a dead-band inverse.
