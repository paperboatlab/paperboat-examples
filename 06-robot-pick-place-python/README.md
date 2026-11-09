# Tutorial 06: ABB-Style Palletizer

> **Level**: 06 · Intermediate  
> **Domain**: Articulated Industrial Robotics  
> **Language**: Python  
> **Port**: 8770  
> **UI Cockpit**: Commander Split View  
> **Core Concepts**: 3-DOF forward/inverse kinematics, quintic S-curve trajectories, vacuum gripper state machine, joint-rate scopes.

---

## 1. Overview

An ABB IRB 460-style palletizer (a cast pedestal, turret, two-link arm and wide fork)
sorts three workpieces from an infeed conveyor onto two pallets. Links are 1.6 m and 1.2 m
on a 1.05 m pedestal. The moving parts are loaded from binary STL files in `data/cad/` and
sent as Station **mesh** entities; `data/generate_cad.py` rebuilds them from parametric
primitives. This is an ABB-style CAD stand-in: the official ABB STEP model is available
from TraceParts/ABB Library behind a sign-in, and Paperboat does not parse STEP itself.

- **Forward kinematics** `P = f(θ1, θ2, θ3)` gives the tool-centre point.
- **Analytical IK** solves the two-link planar chain for the given Cartesian target, with the
  yaw from `atan2(x, z)`. Out-of-reach points are rejected by the IK block.
- **Quintic S-curve** `s(τ) = 10τ³ − 15τ⁴ + 6τ⁵` moves the TCP with zero velocity and
  acceleration at both ends. The transfer rises by `lift` mid-path, arcing over the conveyor.
- **Vacuum gripper**: `Grip` attaches the nearest workpiece, `release` drops it into its bin;
  even-indexed parts go to BIN A and odd-indexed ones to BIN B.

The Flow page is a Step flow: `Start → Repeat 3 × (S-curve to part → vacuum on →
S-curve to bin → vacuum off) → Stop`.

---

## 2. Cockpit exploration

```sh
./bin/paperboat run 06
# http://localhost:3047/?backend=ws://localhost:8770
```

1. **Flow** — open the `Pick & Place Cycle ×3` frame; each S-curve block shows its progress.
   The `IK Solver` group computes joint angles for a fixed Cartesian point and shows them on
   the Board.
2. **Commander view** (`Alt+C`) — the 3D cell on the left and the trajectory/IK blocks on the
   right. Drag `transfer_seconds` or `transfer_lift` in the Variables sheet (`Alt+V`).
3. **Board** — a three-channel Scope of joint angular rates verifies the motor limits; the
   placed count reaches 3.
4. **Station** — the CAD base, turret, orange arm links, wide fork, conveyor, two pallet
   stacks and the workpieces. The arms and fork are mesh entities; only their pose is
   patched each frame, not their vertices.
5. **Console** — `Picked part N` / `Placed part N in BIN A|B` audit lines.

---

## 3. Files

```text
06-robot-pick-place-python/
├── backend.toml          # format = 0, port 8770, solver = euler
├── descriptor.toml       # variables, Step-flow cycle, IK demo, dashboard
├── server.py             # paperboat.serve (dt = 1/50, duration = 22 s)
├── domain/
│   ├── __init__.py
│   ├── kinematics.py     # forward, analytical inverse, quintic, angle wrap
│   ├── state.py          # RobotCell: joints, parts, pallets, CAD scene
│   ├── stl.py            # binary/ASCII STL reader for the CAD parts
│   └── blocks.py         # ArmProbe, InverseKinematics, Trajectory, Grip, CellStatus
├── data/
│   ├── generate_cad.py   # rebuilds the palletizer STL parts
│   └── cad/*.stl         # base, turret, arm1, arm2, fork
├── expected.json         # golden run: 3 parts placed, BIN A/B audit
└── README.md
```

`Trajectory` is a `paperboat.Timed` step: `begin()` captures the start TCP and target,
`advance()` evaluates the quintic, raises the Cartesian path and calls the analytical IK.
The 3D geometry is assembled in `RobotCell.entities()`: the static base/turret and moving
arm/fork are `shape = "mesh"` entities carrying `vertices` and `indices`; `patch()` sends
only their pose. The IK, quintic paths and fork state machine are the substantive part.

---

## 4. Verification

```sh
./paperboat/bin/paperboat check paperboat-examples/06-robot-pick-place-python
python3 paperboat/protocol/golden.py --examples paperboat-examples 06-robot-pick-place-python
```
