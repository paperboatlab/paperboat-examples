---
id: n_furuta06
created: 2026-11-19T15:00:00Z
author: bench3
kind: analysis
project: furuta
status: done
tags: [e3, identification, grey-box]
---

# E3: the grey-box estimate

The model's structure is kept ([[rig-datasheet]]); six of its physical parameters are fitted to
E2's identification run, then checked on its validation run ([[e2-excitation]]).

**Measured, kept:** $L_r$, $J_r$, $L_p$, $R_m$ (rulers, the ohmmeter, and the arm alone, unchanged).
**Fitted:** $m_p$, $l_p$, $B_r$, $B_p$, $k_m$, and the arm's Coulomb friction $f_c$; the
pendulum's own inertia follows as a rod, $J_p = m_p L_p^2/12$.

## Method: equation error

1. Rates and accelerations from the encoders by a Savitzky–Golay filter (cubic, 31 samples,
   62 ms); the voltage through the same filter, so it lines up with the smoothed accelerations.
2. At 200 instants (every 0.1 s), the two equations of motion's residuals, the pendulum's divided
   by $m_p$ (it is homogeneous in $m_p$: without that, shrinking $m_p$ shrinks its error, and a
   first fit did exactly that, to 0.005 kg).
3. Minimize their weighted sum of squares over the six parameters, each scaled by its datasheet
   value, within 0.5–2× (0–20 mN m for $f_c$).

In Simplicial this is `flows/estimate.psf`: a Step flow, start → the optimization toolkit's
**nlp** block (Ipopt) on `flows/greybox.nlp.json` → a display of x. The problem file is written by
`tools/identify.jl` from the run; the same script solves it by Levenberg–Marquardt, which is what
`flows/out/identified.toml` records. (The nlp block needs an optimization toolkit built with Ipopt;
not every Simplicial has one yet.)

## Result

| | datasheet | identified | ± (1σ) |
| --- | --- | --- | --- |
| $m_p$ (kg) | 0.030 | **0.0313** | 0.0003 |
| $l_p$ (m) | 0.075 | **0.0817** | 0.0001 |
| $B_r$ (N m s/rad) | 8.0 × 10⁻⁴ | **1.43 × 10⁻³** | 0.05 × 10⁻³ |
| $B_p$ (N m s/rad) | 3.0 × 10⁻⁵ | **3.88 × 10⁻⁵** | 0.20 × 10⁻⁵ |
| $k_m$ (N m/A) | 0.045 | **0.0358** | 0.0003 |
| $f_c$ (N m) | 0 | **1.20 × 10⁻³** | 0.11 × 10⁻³ |

The pendulum's centre of mass sits 7 mm further out than the rod's middle (the magnet), the arm's
bearing has nearly twice the datasheet's friction and some Coulomb, and the motor is 20 % weaker than
rated. $k_m$ is the one to doubt: see [[issue-km-bias]].

## Check on the validation run

The excitation loop replayed on each model with the validation run's PRBS, against what the rig did:

| fit (%) | arm θ | pendulum α |
| --- | --- | --- |
| datasheet model | 33.3 | −58.6 |
| identified model | **93.5** | **91.3** |

(fit = 100 (1 − ‖y − ŷ‖ / ‖y − ȳ‖); below 0 is worse than a constant.) Above the 80 % bar set in
[[hypothesis]]: go on to the redesign ([[e4-lqr-identified]]).

![[e3-validation.svg|Four seconds of the validation run, and both models replaying it]]

```julia
using TOML
r = TOML.parsefile("../results.toml")["identification"]
(r["fit_theta_pct"], r["fit_alpha_pct"])
```
