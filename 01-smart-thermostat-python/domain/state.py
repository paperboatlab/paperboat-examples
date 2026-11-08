"""Room thermal dynamics state: room temperature with ambient heat loss and electric heating."""

import math
from paperboat import DomainState

# Thermal constants
C_ROOM = 800.0       # J/K (thermal capacitance of the room air mass)
K_LOSS = 20.0        # W/K (heat transfer coefficient to outdoor environment)
Q_HEATER = 1500.0    # W (baseboard convection heater maximum power)
T_AMB_BASE = 2.0     # °C (winter baseline outdoor temperature)
T_AMB_AMP = 6.0      # °C (sinusoidal diurnal amplitude)
T_AMB_FREQ = 0.05    # Hz (weather fluctuation frequency)


class RoomThermostat(DomainState):
    """Living room thermal dynamics state with 3D architectural station entities."""

    def __init__(self) -> None:
        self.t_room = 18.5       # °C (initial indoor room temperature)
        self.t_amb = T_AMB_BASE  # °C (current outdoor ambient temperature)
        self.heater_power = 0.0  # W (active heating power)
        self.heater_on = 0.0     # 1.0 = ON, 0.0 = OFF

    def step(self, ctx) -> None:
        # Calculate ambient diurnal outdoor temperature
        self.t_amb = T_AMB_BASE + T_AMB_AMP * math.sin(2.0 * math.pi * T_AMB_FREQ * ctx.t)

        # Thermal energy balance: C_room * dT_room/dt = Q_in - Q_loss
        q_in = self.heater_power if self.heater_on > 0.5 else 0.0
        q_loss = K_LOSS * (self.t_room - self.t_amb)
        dt_room = (q_in - q_loss) / C_ROOM

        # Integrate indoor temperature
        self.t_room += dt_room * ctx.dt

    def entities(self) -> list[dict]:
        """Architectural cross-section of a living room with baseboard heater and digital thermostat."""
        return [
            # Room floor (dark charcoal wood parquet)
            {"id": "floor", "shape": "box", "pos": [0, -1.5, 0], "size": [6.0, 0.2, 4.0], "color": "#2a2d32"},
            # Interior back wall (matte architectural slate)
            {"id": "back_wall", "shape": "box", "pos": [0, 0.5, -2.0], "size": [6.0, 3.8, 0.2], "color": "#1e2124"},
            # Exterior glass window wall (cold translucent steel cyan)
            {"id": "glass_window", "shape": "box", "pos": [-2.9, 0.5, 0], "size": [0.1, 3.2, 3.6], "color": "#4a7a96"},
            # Baseboard convection heater housing
            {"id": "heater_unit", "shape": "box", "pos": [-2.4, -1.3, 0], "size": [0.4, 0.3, 2.4], "color": "#3f464d"},
            # Thermostat wall plate
            {"id": "thermostat_plate", "shape": "box", "pos": [1.2, 0.3, -1.88], "size": [0.6, 0.6, 0.06], "color": "#16181a"},
            *self.patch(),
        ]

    def patch(self) -> list[dict]:
        """Dynamic per-frame state visualizations (heater glow, heat plumes, dial color)."""
        heater_active = self.heater_on > 0.5
        heat_color = "#f97316" if heater_active else "#3f464d"
        plume_scale = 1.0 if heater_active else 0.05
        dial_color = "#38bdf8" if self.t_room < 20.5 else ("#22c55e" if self.t_room <= 22.0 else "#f97316")

        return [
            # Baseboard heater active glow element
            {"id": "heater_glow", "shape": "box", "pos": [-2.4, -1.2, 0], "size": [0.38, 0.1, 2.2], "color": heat_color},
            # Rising convective heat plume
            {"id": "heat_plume", "shape": "box", "pos": [-2.4, -0.6 * plume_scale, 0], "size": [0.3, 1.0 * plume_scale, 2.0], "color": heat_color},
            # Digital thermostat dial face
            {"id": "thermostat_dial", "shape": "box", "pos": [1.2, 0.3, -1.82], "size": [0.4, 0.4, 0.08], "color": dial_color},
        ]

    def summary(self) -> str:
        return f"done, final T_room = {self.t_room:.2f} °C, T_amb = {self.t_amb:.2f} °C"
