# Tutorial 01: Smart Thermostat

> **Level**: 01 · Beginner  
> **Domain**: Thermal Comfort & Bang-Bang Hysteresis  
> **Language**: Python  
> **Port**: 8765  
> **UI Cockpit**: Navigator Mode  
> **Core Concepts**: Continuous ODE clock flow, scalar signal wiring, Board Wave Plot, `backend.toml` (format = 0).

---

## 1. Overview & Physics

This tutorial introduces the foundations of the Paperboat platform. You will build and observe a **closed-loop thermal comfort system** for a living room during winter.

### Physical Model
- **Heat Loss to Outdoors**: Heat leaves the room through the glass window and walls proportional to the temperature gradient:
  $$Q_{\text{loss}} = k_{\text{loss}} \cdot (T_{\text{room}} - T_{\text{ambient}})$$
- **Ambient Diurnal Oscillation**: The outdoor winter temperature fluctuates sinusoidally around a cold baseline:
  $$T_{\text{ambient}}(t) = T_{\text{base}} + A \cdot \sin(2\pi f t)$$
- **Room Heat Capacity**: Indoor temperature changes according to thermal capacitance balance:
  $$C_{\text{room}} \frac{dT_{\text{room}}}{dt} = Q_{\text{heater}} - Q_{\text{loss}}$$
- **Thermostat Decision**: When $T_{\text{room}} < T_{\text{target}}$, the baseboard heater energizes ($Q_{\text{heater}} = 1500\,\text{W}$). When the room warms to the setpoint, the heater de-energizes.

---

## 2. Cockpit Exploration (The Web UI)

Launch the backend and open the Paperboat Cockpit:
```bash
./bin/paperboat run 01-smart-thermostat-python
```
Navigate to `http://localhost:3047/?backend=ws://localhost:8765`.

### 2.1 The Navigator Mode
Paperboat opens in **Navigator Mode**, designed for clean signal flow observation:
1. **Flow Canvas**: Notice the starter graph:
   - `Room Sensor`: Reads indoor and outdoor temperature.
   - `Constant`: The target setpoint ($21.0^\circ\text{C}$).
   - `Subtract`: Computes error $e = T_{\text{target}} - T_{\text{room}}$.
   - `Threshold`: Evaluates if $e > 0$, outputting $1.0$ (ON) or $0.0$ (OFF).
   - `Heater`: Actuates the physical baseboard radiator.
2. **Station 3D View**:
   - Left-click and drag to orbit around the room.
   - Observe the baseboard heater on the left wall: when the heater activates, it glows bright orange (`#f97316`) and convective heat plumes rise along the glass wall.
   - The round thermostat dial mounted on the back wall glows emerald green when within target comfort bounds.
3. **Board Telemetry**:
   - The **Wave Plot** graphs room temperature in real time.
   - The **Display Readout** shows the exact current temperature chip.
4. **Run Controls (`Space`)**:
   - Press `Space` to pause and resume simulation.
   - Adjust execution time scale in the bottom Run Dock (`1×`, `2×`, `5×`).

---

## 3. API & Code Structure

The backend directory contains:
```text
01-smart-thermostat-python/
├── backend.toml          # Declarative format = 0 manifest
├── descriptor.toml       # Imports, variables, and starter Flow wiring
├── server.py             # Minimal Python entrypoint (paperboat.serve)
├── domain/
│   ├── __init__.py
│   ├── state.py          # RoomThermostat (DomainState) & 3D entities
│   └── blocks.py         # RoomSensor and HeaterActuator blocks
├── expected.json         # Headless golden verification baseline
└── README.md
```

### 3.1 Backend Manifest (`backend.toml`)
Every Paperboat backend is declared with a `backend.toml` manifest:
```toml
[backend]
format = 0
name = "01-smart-thermostat-python"
version = "0.1.0"
engine = ">=0.1"
language = "python"
run = "server.py"
port = 8765
descriptor = "descriptor.toml"
solver = "euler"

[test]
golden = "expected.json"
```

### 3.2 Running Headless & Verifying
Verify this backend from the command line without opening a browser:
```bash
# Run 4-stage verification
./paperboat/bin/paperboat check paperboat-examples/01-smart-thermostat-python --fast

# Verify golden test protocol conformance
python3 paperboat/protocol/golden.py --examples paperboat-examples 01-smart-thermostat-python
```
