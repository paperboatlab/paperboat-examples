# Tutorial 10: High-Speed Train Pantograph

> **Level**: 10 · Master  
> **Domain**: Rail Electrification & Multibody Dynamics  
> **Language**: C++ & Modelica reference  
> **Port**: 8774  
> **UI Cockpit**: Commander Split View  
> **Core Concepts**: articulated pantograph, compliant catenary, aerodynamic uplift, active pneumatic force regulation, bypass and arcing.

---

## 1. Overview

The capstone: a train accelerates from 0 to 320 km/h in 25 s under an overhead contact wire.
The pantograph head is a mass on a suspension spring/damper; the wire has a periodic height
ripple (messenger sag and droppers) and a contact spring.

```text
m·z̈ = k_s(z_base − z) − c_s·ż + F_act + F_aero − F_contact
F_contact = max(0, k_w(z − z_w) + c_w(ż − ż_w))
F_aero = ½·ρ·v²·C_L·A
```

The Flow page is the **active pneumatic regulator**: a PI actuator holds the contact force in
the 90–140 N window. The Station page shows the roof, articulated arm, contact strip, moving
wire/droppers and a force vector that turns green, amber or red.

### Bypass for arcing

The Board switch (or **B**) bypasses the regulator to 0 N. The pantograph then sags, contact
is lost at speed, and the Console logs `ARCING: contact lost …` until the regulator is
re-enabled. The golden starter keeps the regulator on, so it ends with zero losses.

### Modelica reference

`modelica/PantographCatenary.mo` is the acausal Squero Studio OM model of the same system:
head mass, suspension, wire contact spring/damper, aerodynamic uplift and actuator force.
The C++ implementation in `domain/pantograph.cpp` carries the same equations; open the
`.mo` in Squero Studio OM to inspect or edit the schematic.

---

## 2. Cockpit exploration

```sh
./bin/paperboat run 10
# http://localhost:3047/?backend=ws://localhost:8774
```

1. **Commander view** (`Alt+C`) — the train/pantograph on the left, the regulator on the
   right. The speed gauge on the roof fills over the run.
2. **Variables** (`Alt+V`) — `target_force` (80–140 N) and `max_speed` (80–400 km/h).
3. **Board** — a three-channel Scope (contact force, speed, aerodynamic uplift), the
   regulator switch, and readouts for force, speed, losses, in-window flag, uplift and
   actuator command.
4. **Bypass** — turn the switch off (or press **B**) at high speed: the force drops, the
   vector turns red and the Console reports arcing. Turn it back on to restore contact.
5. **Station** — the roof fairing, lower/upper arm, tie rod, carbon contact strip, mast,
   catenary wire and droppers.

---

## 3. Files

```text
10-train-pantograph-cpp/
├── backend.toml          # format = 0, port 8774, solver = rk4
├── descriptor.toml       # station object, regulator graph, variables
├── CMakeLists.txt        # native C++ linking paperboat::core
├── main.cpp              # paperboat::main
├── domain/
│   ├── pantograph.hpp    # registration
│   └── pantograph.cpp    # Pantograph StationObject, Regulator, ContactProbe
├── modelica/
│   └── PantographCatenary.mo  # acausal reference model
├── expected.json         # golden run: 126.7 N, 320 km/h, 0 losses
└── README.md
```

The `Pantograph` is an ISA-88 `StationObject`: its props (mass, stiffness, damping, wire
stiffness, target force, top speed) are edited on the Station page; its linked block gives
the Flow `contact`, `speed`, `z`, `wire`, `uplift`, `losses`, `arcing` and `in_window`.

---

## 4. Verification

```sh
./paperboat/bin/paperboat check paperboat-examples/10-train-pantograph-cpp
python3 paperboat/protocol/golden.py --examples paperboat-examples 10-train-pantograph-cpp
```
