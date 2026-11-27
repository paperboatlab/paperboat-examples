# Tutorial 01: Smart Thermostat

> **Level**: 01 · Beginner  
> **Domain**: Thermal Comfort & Bang-Bang Hysteresis  
> **Language**: Python  
> **Port**: 51301  
> **UI Cockpit**: Navigator Mode  
> **Core Concepts**: Continuous ODE clock flow, scalar signal wiring, Board Wave Plot, `station.toml` (format = 0).

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

Launch the station and open the Paperboat Cockpit:
```bash
paperboat run 01
```
Navigate to `http://localhost:30471/?station=ws://localhost:51301`.

### 2.1 The Navigator Mode
Paperboat opens in **Navigator Mode**, designed for clean signal flow observation:
1. **Flow Canvas**: Notice the starter graph:
   - `Room Sensor`: Reads indoor and outdoor temperature.
   - `Constant`: The target setpoint ($21.0^\circ\text{C}$).
   - `Subtract`: Computes error $e = T_{\text{target}} - T_{\text{room}}$.
   - `Threshold`: Evaluates if $e > 0$, outputting $1.0$ (ON) or $0.0$ (OFF).
   - `Heater`: Actuates the physical baseboard radiator.
   - `Scope`: 3-channel real-time oscilloscope tracking target setpoint (channel A), heater relay state (channel B), and room temperature (channel C).
2. **Station 3D View**:
   - Left-click and drag to orbit around the room.
   - Observe the baseboard heater on the left wall: when the heater activates, it glows bright orange (`#f97316`) and convective heat plumes rise.
   - The scenic window and round thermostat dial are mounted along the back wall. The dial glows emerald green when within comfort bounds.
3. **Board Telemetry**:
   - The **Scope** instrument graphs setpoint, control signal, and indoor temperature together.
   - The **Target Label** readout displays the current target setpoint.
   - The **Console** pane displays real-time execution logs.
4. **Floating Run Dock Controls**:
   - Toggle **`open_window`** in the bottom floating dock to swing open the 3D living room window! Freezing outdoor air rushes into the room, causing thermal heat losses to jump ($140\,\text{W/K}$) and forcing the thermostat heater into overdrive. The window is a property of the room (a station object), so it opens with the next run; live, mid-run changes wait on `ctx.variable` for Python stations (paperboatlab/simplicial#60).
   - Adjust **`target_temp`** slider in the dock or Variables panel (`Alt+V`).
   - Press `Space` to pause and resume simulation.
   - Adjust execution time scale in the bottom Run Dock (`1×`, `2×`, `5×`).

---

## 3. API & Code Structure

The station directory contains:
```text
01-smart-thermostat-python/
├── station.toml          # Declarative format = 0 manifest
├── descriptor.toml       # Imports, variables, and starter Flow wiring
├── station.py            # The station file: registers the room and the blocks (paperboat_runtime)
├── domain/
│   ├── __init__.py
│   ├── state.py          # RoomThermostat, the room (a station object) & its 3D entities
│   └── blocks.py         # RoomSensor and HeaterActuator blocks
├── expected.json         # Headless golden verification baseline
├── example.toml          # how the golden harness runs it (docs/golden.md)
└── README.md
```

### 3.1 Station Manifest (`station.toml`)
Every Paperboat station is declared with a `station.toml` manifest:
```toml
[station]
format = 0
name = "01-smart-thermostat-python"
version = "0.2.0"
engine = ">=0.1"
language = "python"
run = "station.py"
port = 51301
descriptor = "descriptor.toml"
solver = "euler"

[run]
duration = 20.0
dt = 0.05
emit_every = 4
speed = 2.0

[test]
golden = "expected.json"
```

### 3.2 The station file (`station.py`)
Simplicial's engine is the station: it loads the descriptor, runs the Flow and serves the page.
Only the domain code is Python, and it runs out of process, in a Python runtime that `paperboatd`
leases (a container, or a process on the host). `station.py` registers each type with a name and
a definition (Simplicial's docs/stations.rst):

```python
pb.register("room", RoomThermostat, definition={"base": "object", "props": {"open_window": False}})
pb.register("heater", HeaterActuator, definition={"inputs": ["cmd"]})
pb.register("room_sensor", RoomSensor, definition={"kind": "source", "outputs": ["t_room", "t_amb"]})
```

The room is a station object (`[station] objects` in the descriptor): the engine makes one per
run and steps it after each pass of the Flow, and the sensor and heater reach it through
`state.room()`. When the run is done the Console shows its final `t_room` and `t_amb`.

### 3.3 Running Headless & Verifying
Verify this station from the command line without opening a browser (it needs `paperboatd`,
which the engine starts on demand):
```sh
<simplicial>/bin/simplicial host . --run   # in this folder: the starter, headless, as JSON lines
python3 golden.py simplicial/01-smart-thermostat-python   # from the repository root: run, compare
paperboat check simplicial/01-smart-thermostat-python     # manifest, catalog, smoke and golden
```
