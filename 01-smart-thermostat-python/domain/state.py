"""Room thermal dynamics state: room temperature with ambient heat loss, electric heating, and operable 3D window."""

import math
from paperboat import DomainState

# Thermal constants
C_ROOM = 800.0        # J/K (thermal capacitance of the room air mass)
K_LOSS_CLOSED = 20.0  # W/K (heat transfer coefficient with window closed)
K_LOSS_OPEN = 140.0   # W/K (heat transfer coefficient when window is fully open to winter air)
Q_HEATER = 1500.0     # W (baseboard convection heater maximum power)
T_AMB_BASE = 2.0      # °C (winter baseline outdoor temperature)
T_AMB_AMP = 6.0       # °C (sinusoidal diurnal amplitude)
T_AMB_FREQ = 0.05     # Hz (weather fluctuation frequency)


class RoomThermostat(DomainState):
    """Living room thermal dynamics state with 3D architectural station entities."""

    def __init__(self) -> None:
        self.t_room = 18.5         # °C (initial indoor room temperature)
        self.t_amb = T_AMB_BASE    # °C (current outdoor ambient temperature)
        self.heater_power = 0.0    # W (active heating power)
        self.heater_on = 0.0       # 1.0 = ON, 0.0 = OFF
        self.window_open = False   # Tunable variable state ("open_window")
        self.window_opening = 0.0  # 0.0 (shut) to 1.0 (fully open), smoothly animated
        self.sim_time = 0.0

    def step(self, ctx) -> None:
        self.sim_time = ctx.t
        # Calculate ambient diurnal outdoor temperature
        self.t_amb = T_AMB_BASE + T_AMB_AMP * math.sin(2.0 * math.pi * T_AMB_FREQ * ctx.t)

        # Read tunable project variable "open_window" from the dock control
        win_var = ctx.variable("open_window")
        if win_var is not None:
            self.window_open = bool(float(win_var) > 0.5)

        # Animate smooth window opening/closing transition (~0.6s)
        target = 1.0 if self.window_open else 0.0
        speed = 2.0  # rate / sec
        if self.window_opening < target:
            self.window_opening = min(target, self.window_opening + speed * ctx.dt)
        elif self.window_opening > target:
            self.window_opening = max(target, self.window_opening - speed * ctx.dt)

        # Thermal energy balance: C_room * dT_room/dt = Q_in - Q_loss
        k_eff = K_LOSS_CLOSED + (K_LOSS_OPEN - K_LOSS_CLOSED) * self.window_opening
        q_in = self.heater_power if self.heater_on > 0.5 else 0.0
        q_loss = k_eff * (self.t_room - self.t_amb)
        dt_room = (q_in - q_loss) / C_ROOM

        # Integrate indoor temperature
        self.t_room += dt_room * ctx.dt

    def entities(self) -> list[dict]:
        """Architectural cross-section of a living room with baseboard heater, digital thermostat, and 3D window."""
        return [
            # Room floor (dark charcoal wood parquet)
            {"id": "floor", "shape": "box", "pos": [0, -1.5, 0], "size": [6.0, 0.2, 4.0], "color": "#2a2d32"},
            # Interior back wall (matte architectural slate)
            {"id": "back_wall", "shape": "box", "pos": [0, 0.5, -2.0], "size": [6.0, 3.8, 0.2], "color": "#1e2124"},
            # Left exterior window wall solid framing
            {"id": "wall_left_bottom", "shape": "box", "pos": [-2.95, -1.05, 0], "size": [0.1, 0.7, 3.6], "color": "#1e2124"},
            {"id": "wall_left_top", "shape": "box", "pos": [-2.95, 1.85, 0], "size": [0.1, 0.9, 3.6], "color": "#1e2124"},
            {"id": "wall_left_back", "shape": "box", "pos": [-2.95, 0.4, -1.3], "size": [0.1, 2.0, 1.0], "color": "#1e2124"},
            {"id": "wall_left_front", "shape": "box", "pos": [-2.95, 0.4, 1.3], "size": [0.1, 2.0, 1.0], "color": "#1e2124"},
            # Window outer frame & sill
            {"id": "window_sill", "shape": "box", "pos": [-2.9, -0.65, 0], "size": [0.22, 0.08, 1.8], "color": "#334155"},
            {"id": "window_lintel", "shape": "box", "pos": [-2.9, 1.45, 0], "size": [0.22, 0.08, 1.8], "color": "#334155"},
            {"id": "window_jamb_back", "shape": "box", "pos": [-2.9, 0.4, -0.85], "size": [0.22, 2.02, 0.08], "color": "#334155"},
            {"id": "window_jamb_front", "shape": "box", "pos": [-2.9, 0.4, 0.85], "size": [0.22, 2.02, 0.08], "color": "#334155"},
            # Deep winter dusk exterior backdrop outside
            {"id": "window_backdrop", "shape": "box", "pos": [-3.2, 0.4, 0], "size": [0.05, 2.1, 1.9], "color": "#0b132b"},
            # Baseboard convection heater housing
            {"id": "heater_unit", "shape": "box", "pos": [-2.4, -1.3, 0], "size": [0.4, 0.3, 2.4], "color": "#3f464d"},
            # Thermostat wall plate
            {"id": "thermostat_plate", "shape": "box", "pos": [1.2, 0.3, -1.88], "size": [0.6, 0.6, 0.06], "color": "#16181a"},
            *self.patch(),
        ]

    def patch(self) -> list[dict]:
        """Dynamic per-frame state visualizations (heater glow, heat plumes, dial color, animated 3D window)."""
        heater_active = self.heater_on > 0.5
        heat_color = "#f97316" if heater_active else "#3f464d"
        plume_scale = 1.0 if heater_active else 0.05
        dial_color = "#38bdf8" if self.t_room < 20.5 else ("#22c55e" if self.t_room <= 22.0 else "#f97316")

        # 3D Window sash opening kinematics (hinged at x=-2.85, z=-0.80)
        theta = 1.25 * self.window_opening
        xh, zh = -2.85, -0.80
        radius = 0.80
        wx = xh + radius * math.sin(theta)
        wz = zh + radius * math.cos(theta)

        # Freezing cold draft gust entering through window (pulsing wind)
        gust_pulse = 0.85 + 0.15 * math.sin(8.0 * self.sim_time)
        draft_scale = max(0.001, self.window_opening * gust_pulse)
        draft_pos_x = -2.5 + 0.7 * self.window_opening

        return [
            # Baseboard heater active glow element
            {"id": "heater_glow", "shape": "box", "pos": [-2.4, -1.2, 0], "size": [0.38, 0.1, 2.2], "color": heat_color},
            # Rising convective heat plume
            {"id": "heat_plume", "shape": "box", "pos": [-2.4, -0.6 * plume_scale, 0], "size": [0.3, 1.0 * plume_scale, 2.0], "color": heat_color},
            # Digital thermostat dial face
            {"id": "thermostat_dial", "shape": "box", "pos": [1.2, 0.3, -1.82], "size": [0.4, 0.4, 0.08], "color": dial_color},
            # Operable 3D window sash & glass pane
            {"id": "window_sash", "shape": "box", "pos": [round(wx, 4), 0.4, round(wz, 4)], "size": [0.06, 1.92, 1.62], "rot": [0.0, round(theta, 4), 0.0], "color": "#475569"},
            {"id": "window_glass", "shape": "box", "pos": [round(wx, 4), 0.4, round(wz, 4)], "size": [0.04, 1.80, 1.50], "rot": [0.0, round(theta, 4), 0.0], "color": "#38bdf8"},
            # Inflowing freezing outdoor breeze draft
            {"id": "cold_draft", "shape": "box", "pos": [round(draft_pos_x, 3), 0.4, 0.0], "size": [1.3, 0.9, 1.2], "scale": [round(draft_scale, 3), round(draft_scale, 3), round(draft_scale, 3)], "color": "#a5f3fc"},
        ]

    def summary(self) -> str:
        return f"done, final T_room = {self.t_room:.2f} °C, T_amb = {self.t_amb:.2f} °C"
