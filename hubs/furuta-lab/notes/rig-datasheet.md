---
id: n_furuta01
created: 2026-11-16T08:30:00Z
author: bench3
kind: reference
project: furuta
status: done
tags: [rig, datasheet]
---

# Bench 3: the rotary pendulum and its datasheet

A DC motor turns a horizontal arm (θ); a free pendulum hangs from the arm's tip and swings in the
plane across it (α, 0 upright). Both axes have 2048-line encoders read in quadrature (8192 counts a
turn, 0.044°). A ±10 V linear amplifier drives the motor; the loop runs at 500 Hz. Rubber end stops
sit at ±100°, and the cables want the arm within ±90°.

The FP-150 kit's datasheet, rev B, as `design/datasheet.toml`:

| | | |
| --- | --- | --- |
| Arm length $L_r$ | 0.100 m | measured, agrees |
| Arm inertia $J_r$ | 3.7 × 10⁻⁴ kg m² | with the hub |
| Pendulum mass $m_p$ | 0.030 kg | |
| Pendulum length $L_p$ | 0.150 m | measured, agrees |
| Pivot to centre of mass $l_p$ | 0.075 m | the rod's middle |
| Arm viscous friction $B_r$ | 8.0 × 10⁻⁴ N m s/rad | |
| Pendulum viscous friction $B_p$ | 3.0 × 10⁻⁵ N m s/rad | |
| Armature resistance $R_m$ | 7.5 Ω | measured, 7.4–7.6 |
| Motor constant $k_m$ | 0.045 N m/A | |

Not on the datasheet: Coulomb friction, and the amplifier's dead band. Our pendulum also carries
the encoder's magnet and its screw near the tip, which the kit's rod doesn't.

## The model

In Articula, `model/Furuta.mo`: `Furuta.Pendulum` is built from Modelica's MultiBody library. The arm
is a vertical revolute joint, driven through the hub's inertia by a DC motor (armature resistance and
EMF); the pendulum is a body on a second revolute joint at the arm's tip; both joints have viscous
dampers, and the arm a smoothed Coulomb friction. `Furuta.Rig` wraps it with the amplifier (dead
band, saturation). The station `stations/furuta-rig/` was generated from `Furuta.Rig` (Articula took
the FMU path: the dead band is an event).

The Julia scripts need the equations themselves, and `model/furuta.jl` writes the same physics as
Lagrange's equations, with $J_{\hat r} = J_r + m_p L_r^2$, $J_{\hat p} = J_p + m_p l_p^2$ and
$h = m_p L_r l_p$:

$$
\begin{aligned}
(J_{\hat r} + J_{\hat p} \sin^2\alpha)\,\ddot\theta + h\cos\alpha\,\ddot\alpha &= \tau - 2J_{\hat p}\sin\alpha\cos\alpha\,\dot\theta\dot\alpha + h\sin\alpha\,\dot\alpha^2 \\
h\cos\alpha\,\ddot\theta + J_{\hat p}\,\ddot\alpha &= J_{\hat p}\sin\alpha\cos\alpha\,\dot\theta^2 + m_p g\, l_p \sin\alpha - B_p\dot\alpha
\end{aligned}
$$

with the motor's torque less the arm's friction $\tau = k_m (u - k_m\dot\theta)/R_m - B_r\dot\theta - f_c\,\mathrm{sign}(\dot\theta)$.
The two agree to 4 × 10⁻⁹ rad over a second of driven swing, and OpenModelica's linearization of
`Furuta.Pendulum` at the upright (`linearize`, written out as Julia) matches `linearize` in
`furuta.jl` to 10⁻¹⁰.

About the upright the linear model has one unstable pole, the pendulum falling:

```julia
include("../model/furuta.jl")
p = merge(load_params("../design/datasheet.toml"), (fc = 0.0,))
A, B = linearize(p)
round.(real.(eigvals(A)), digits = 2)     # [-12.73, -1.58, 0.0, 11.71]
```
