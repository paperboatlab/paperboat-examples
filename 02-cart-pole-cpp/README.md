# Tutorial 02: Modernized Cart-Pole

> **Level**: 02 · Elementary  
> **Domain**: Inverted Pendulum Balancing on Precision Rail  
> **Language**: C++  
> **Port**: 8766  
> **UI Cockpit**: Commander Mode Split View (`Alt+C`)  
> **Core Concepts**: C++ SDK (`<paperboat/sdk.hpp>`), ISA-88 `StationObject`, Variables Sheet (`Alt+V`) formula bindings (`kd = kp / 5`), closed-loop PID control.

---

## 1. Overview & Physics

Tutorial 02 modernizes Paperboat's classic benchmark into a precision instrument. A free-swinging inverted pendulum is attached to a carriage sliding along a horizontal guide rail. Left unassisted, gravity causes the pole to topple. By accelerating the cart horizontally, a feedback controller stabilizes the pole upright ($\theta \to 0$) while keeping the cart centered ($x \to 0$).

### 1.1 Physical Constants & Parameters
- **Cart Mass ($M$)**: $1.0\,\text{kg}$ (machined brushed aluminum chassis)
- **Pole Mass ($m$)**: $0.1\,\text{kg}$ (carbon-fiber rod with brass top bob)
- **Pole Length ($2l$)**: $1.0\,\text{m}$ (half-length $l = 0.5\,\text{m}$)
- **Rail Travel Limits**: $x \in [-1.50\,\text{m}, +1.50\,\text{m}]$ (hard rubber end stops)
- **Actuator Force Limit**: $F_{\text{cmd}} \in [-25.0\,\text{N}, +25.0\,\text{N}]$

### 1.2 Equations of Motion
The nonlinear system dynamics are governed by:
$$\ddot{\theta} = \frac{g \sin\theta + \cos\theta \left( \frac{-F - m l \dot{\theta}^2 \sin\theta}{M + m} \right)}{l \left( \frac{4}{3} - \frac{m \cos^2\theta}{M + m} \right)}$$
$$\ddot{x} = \frac{F + m l \left( \dot{\theta}^2 \sin\theta - \ddot{\theta}\cos\theta \right)}{M + m}$$

---

## 2. Cockpit Exploration (The Web UI)

Launch the backend and open the Paperboat Cockpit:
```bash
./bin/paperboat run 02-cart-pole-cpp
```
Navigate to `http://localhost:3047/?backend=ws://localhost:8766`.

### 2.1 Commander Mode Split View (`Alt+C`)
Switch to **Commander Mode** (`Alt+C`):
- **Left Pane (Station Page)**: 3D WebGL scene showing the rail, stops, aluminum cart, and carbon pole.
- **Right Pane (Flow Page)**: Visual block diagram driving the cart's motor force.
- **Bottom Drawer (Board)**: Real-time oscilloscopes graphing $\theta(t)$ and $x(t)$.

### 2.2 Variables Sheet (`Alt+V`) & Dynamic Formula Bindings
Press `Alt+V` to open the **Variables Sheet**:
- `kp_theta`: Proportional angle gain (default `45.0`).
- `kd_theta`: Evaluates the formula `= kp_theta / 5` ($9.0\,\text{N}\cdot\text{s}/\text{rad}$).
- `kp_x`: Cart position gain (default `2.5`).
- `kd_x`: Evaluates the formula `= kp_x / 2` ($1.25\,\text{N}\cdot\text{s}/\text{m}$).

**Try this live**:
1. Drag the `kp_theta` slider up to `70.0`.
2. Notice how `kd_theta` automatically recalculates to `14.0` in real time.
3. Observe how the cart stiffens its response to tilt disturbances without introducing high-frequency chatter.

### 2.3 Station 3D Instrument Details
- **Linear Guide Rail**: Ground steel track with crimson end stops at $\pm 1.5\,\text{m}$.
- **Rotary Bearing Hub & Protractor**: Blue precision bearing hub with recessed degree dial.
- **Dynamic Force Vector Arrow**: A bright orange vector arrow (`#f97316`) extends horizontally from the cart proportional to the instantaneous control force $F_{\text{cmd}}$.

---

## 3. C++ SDK Architecture

The backend is organized as a standalone C++ project:
```text
02-cart-pole-cpp/
├── backend.toml          # Format = 0 manifest (port = 8766, solver = "rk4")
├── descriptor.toml       # Variables, starter Station, and starter Flow wiring
├── CMakeLists.txt        # Native C++ build linking paperboat::core
├── main.cpp              # Canonical paperboat::main entrypoint
├── domain/
│   ├── cart_pole.hpp     # Registration declaration
│   └── cart_pole.cpp     # ISA-88 StationObject, step(), and entities()
├── expected.json         # Golden run verification baseline
└── README.md
```

### 3.1 Defining the StationObject (`domain/cart_pole.cpp`)
The cart-pole implements `paperboat::StationObject`:
- `read()`: Emits telemetry $[x, v, \theta, \omega]$ into the linked Flow block.
- `step(ctx, in)`: Reads actuator `force` from the Flow canvas and integrates equations of motion.
- `entities(id, z)`: Yields 3D entities for WebGL rendering.

---

## 4. Verification

Run verification from the command line:
```bash
# Verify backend manifest and catalog
./paperboat/bin/paperboat check paperboat-examples/02-cart-pole-cpp --fast

# Run headless golden protocol test
python3 paperboat/protocol/golden.py --examples paperboat-examples 02-cart-pole-cpp
```
