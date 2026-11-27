---
id: n_furuta08
created: 2026-11-23T14:00:00Z
author: bench3
kind: experiment
project: furuta
status: done
tags: [e5, mpc]
---

# E5: MPC on the identified model

The control toolkit's **mpc** block in place of E4's state feedback, everything else the same: the
identified plan, its feedforward, the rate filters ([[protocol-balance-move]]).

**The block** solves, every 5 ms, the condensed QP over a horizon of $N$ steps,

$$
\min_{u_0 \dots u_{N-1}} \sum_{k=0}^{N-1} (x_k - r)^\top Q\,(x_k - r) + u_k^\top R\,u_k,\qquad u_{min} \le u_k \le u_{max}
$$

on the identified model linearized at the upright and discretized at 5 ms (`flows/mpc.json`, written
by `tools/make_runs.jl`). It sees the deviation from the plan, $x - x_{ref}$, with $r = 0$, and its
$u$ adds to the feedforward; its bounds are the ±4 V the plan leaves. Same $Q$ and $R$ as the LQR. It
outputs the $u$ it solved at the previous step, then solves for the next: 5 ms late, on top of the
amplifier's own lag.

## Choosing the horizon

The block has no terminal cost, so a short horizon forgets that the pendulum falls; a long one is what
the theory wants. On the bench, with the QP solved exactly, N = 200 (1 s) balanced as well as the LQR.
**In the block it diverged**: condensing 200 steps of an unstable plant gives a QP whose numbers span
about e¹¹, and the block's OSQP stops after 25 iterations calling it solved; the block then applies a
poor $u$ and the pendulum falls in the first second. Scaling $Q$ and $R$ didn't help.

| N (5 ms) | in the block | at rest, RMS α |
| --- | --- | --- |
| 200 | diverges | (0.24° solved exactly) |
| 80 | **balances** | 0.35° (LQR: 0.25°) |
| 60 | balances, the arm wanders 10° RMS | |

N = 80 (0.4 s) kept: the longest the block's solver still handles.

**Flow**: `flows/mpc.psf`. **Run**: `runs/2026-11-23_e5-mpc/run.csv` (at 5 ms).

## Result

| | E1 datasheet LQR | E4 identified LQR | **E5 MPC** |
| --- | --- | --- | --- |
| max \|α − α_ref\| | 12.96° | 1.64° | **2.01°** |
| RMS α − α_ref | 2.89° | 0.39° | **0.47°** |
| RMS θ − θ_ref | 8.55° | 1.99° | **3.16°** |
| max \|θ\| | 85.6° | 68.6° | **69.3°** |
| saturated | 5.9 % | 0 | **0** |

```julia
include("../tools/notebook.jl")
figures("../runs/2026-11-23_e5-mpc/run.csv", "../design/out/trajectory-identified.csv")
```

![[arm-error.svg|The arm off its plan in the three runs]]

MPC clears H1's bar (2.01° against 5.2°), but does worse than E4's LQR on every count: the
pendulum's worst deviation by 23 %, the arm's tracking by 60 %. The short horizon and the 5 ms
latency are the likely costs. Its bounds never became active (its correction peaked at 2.3 V of the
±4 V): on this move nothing constrained the loop, which is where an MPC would earn its place.
See [[report]].
