---
id: n_furuta00
created: 2026-11-16T08:00:00Z
author: bench3
kind: project
project: furuta
status: done
tags: [furuta, control, identification, mpc]
---

# Furuta pendulum: grey-box identification and MPC on bench 3

**Question.** Can an MPC built on a grey-box-identified model hold bench 3's pendulum upright through a
fast arm move with the pendulum off its plan by at most 40 % of what the datasheet's LQR gives, and the
arm within ±90° and the motor within ±10 V? The full statement is in [[hypothesis]].

**Answer.** Yes: 2.0° against 13.0° (84 % less). But the identification did the work, not the MPC: the
LQR redesigned on the identified model does better still (1.6°). See [[report]].

## Reading order

Nothing here has to run in sequence; this is the order the study went in, and the order to read it.

1. **The rig.** [[rig-datasheet]]: what bench 3 is, the datasheet's numbers. The model in Articula:
   `model/Furuta.mo` (`Furuta.Pendulum`, MultiBody; `Furuta.Rig`, the bench as the lab has it),
   and the station Articula generated from it, `stations/furuta-rig/`.
2. **The plan.** [[hypothesis]], and how every closed-loop run is done: [[protocol-balance-move]].
3. **Design on the datasheet.** Julix: `design/lqr.jl` (the gain) and `design/trajectory.jl` (the
   planned move, the state and the voltage). Outputs in `design/out/`.
4. **E1, the baseline.** [[e1-lqr-datasheet]]: the datasheet's LQR on the rig. Simplicial:
   `flows/e1-lqr-datasheet.psf`.
5. **E2, excitation.** [[e2-excitation]]: two runs to fit and to check a model. `flows/excite.psf`.
6. **E3, the grey-box estimate.** [[e3-greybox]]: six parameters fitted, the model checked on the
   other run. `flows/estimate.psf` (the nlp block on `flows/greybox.nlp.json`); the result in
   `flows/out/identified.toml`.
7. **E4, the LQR redesigned.** [[e4-lqr-identified]]: the same Julix scripts on the identified model.
8. **E5, MPC.** [[e5-mpc]]: the control toolkit's mpc block on the identified model. `flows/mpc.psf`,
   its model `flows/mpc.json`.
9. **The report.** [[report]]. Open questions: [[issue-arm-hunting]], [[issue-km-bias]].

## Files

| Where | App | What |
| --- | --- | --- |
| `model/` | Articula | `Furuta.mo` (MultiBody); `furuta.jl`, its equations for the Julia scripts |
| `stations/` | Articula → Simplicial | `furuta-rig/`, generated from `Furuta.Rig`; `furuta-rig-0.1.0.pst`, packed |
| `design/` | Julix | the gain and the trajectory, on `datasheet.toml` or the identified parameters |
| `flows/` | Simplicial | one flow per experiment, the NLP and MPC problems, `out/identified.toml` |
| `runs/` | the bench | the recorded runs, one folder per experiment (CSV: t, u, θ, α) |
| `notes/`, `report.md` | Malachite | this notebook |
| `media/` | | the figures the notes show |
| `tools/` | | the bench, simulated: `julia tools/make_runs.jl` regenerates every run, output and figure |

An `out/` folder holds what an app made from the hub, so the hub's history leaves it out (its
`ignore`, and `out/` in `.gitignore`); the outputs above ship with the example all the same. Take `out/`
out of both to version them.
