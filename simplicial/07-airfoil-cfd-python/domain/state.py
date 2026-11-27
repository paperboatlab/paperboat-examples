"""The wind tunnel: the lattice, its aerodynamic coefficients and the Station scene."""

import math

from paperboat import DomainState
from domain.airfoil import naca0012_outline
from domain.forces import polars
from domain.lbm_solver import LatticeBoltzmann

NX, NY = 160, 80
TUNNEL_W, TUNNEL_H = 3.9, 1.7
LEFT, BOTTOM = -0.1, 0.1


class WindTunnel(DomainState):
    """A 2-D test section with a pitching NACA 0012 and a live velocity field."""

    def __init__(self) -> None:
        self.lattice = LatticeBoltzmann(NX, NY)
        self.alpha = 6.0
        self.speed = 0.08
        self.coefficients = polars(self.alpha, self.speed)
        self.steps = 0
        self.residual = 0.0
        self.sim_time = 0.0

    def advance(self, alpha: float, speed: float, substeps: int) -> float:
        self.alpha = float(alpha)
        self.speed = float(speed)
        self.residual = self.lattice.advance(self.alpha, self.speed, substeps)
        self.steps = self.lattice.steps
        self.coefficients = polars(self.alpha, self.speed)
        return self.residual

    def summary(self) -> str:
        c = self.coefficients
        return (f"NACA 0012 at {self.alpha:.1f} deg: CL = {c['cl']:.3f}, "
                f"CD = {c['cd']:.3f}, L/D = {c['ld']:.1f}")

    # --- mapping the lattice to the Station scene ------------------------------------------

    def _scene(self, i: float, j: float) -> tuple[float, float]:
        return LEFT + (i / (NX - 1)) * TUNNEL_W, BOTTOM + (j / (NY - 1)) * TUNNEL_H

    def _airfoil_point(self, chord_fraction: float, half_thickness: float) -> tuple[float, float]:
        cx, cy = self._scene(self.lattice.cx, self.lattice.cy)
        chord = self.lattice.chord / (NX - 1) * TUNNEL_W
        lx = (chord_fraction - 0.5) * chord
        ly = half_thickness * chord
        a = math.radians(self.alpha)
        return cx + lx * math.cos(a) + ly * math.sin(a), cy + lx * math.sin(a) - ly * math.cos(a)

    def _color(self, speed: float) -> str:
        t = min(1.0, max(0.0, speed / max(self.speed * 1.5, 1e-6)))
        r = int(40 + 215 * t)
        g = int(120 + 110 * t)
        b = int(230 - 150 * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _static_entities(self) -> list[dict]:
        x0, y0 = LEFT, BOTTOM
        x1, y1 = LEFT + TUNNEL_W, BOTTOM + TUNNEL_H
        return [
            {"id": "tunnel-floor", "shape": "line", "pos": [x0, y0, 0.0], "to": [x1, y0, 0.0], "color": "#475569"},
            {"id": "tunnel-ceiling", "shape": "line", "pos": [x0, y1, 0.0], "to": [x1, y1, 0.0], "color": "#475569"},
            {"id": "tunnel-inlet", "shape": "line", "pos": [x0, y0, 0.0], "to": [x0, y1, 0.0], "color": "#38bdf8"},
            {"id": "tunnel-outlet", "shape": "line", "pos": [x1, y0, 0.0], "to": [x1, y1, 0.0], "color": "#64748b"},
            {"id": "mount", "shape": "line", "pos": [self._scene(self.lattice.cx, self.lattice.cy)[0], y0, 0.0],
             "to": [self._scene(self.lattice.cx, self.lattice.cy)[0], self._scene(self.lattice.cx, self.lattice.cy)[1] - 0.15, 0.0],
             "color": "#94a3b8"},
        ]

    def _airfoil_entities(self) -> list[dict]:
        points = [self._airfoil_point(x, y) for x, y in naca0012_outline(26)]
        out = []
        for index in range(len(points) - 1):
            out.append({
                "id": f"airfoil-{index}",
                "shape": "line",
                "pos": [points[index][0], points[index][1], 0.0],
                "to": [points[index + 1][0], points[index + 1][1], 0.0],
                "color": "#e2e8f0",
            })
        # Chord line and the angle-of-attack arc.
        cx, cy = self._scene(self.lattice.cx, self.lattice.cy)
        chord = self.lattice.chord / (NX - 1) * TUNNEL_W
        out.append({"id": "chord", "shape": "line", "pos": [cx - chord / 2 * math.cos(math.radians(self.alpha)),
                                                               cy - chord / 2 * math.sin(math.radians(self.alpha)), 0.0],
                    "to": [cx + chord / 2 * math.cos(math.radians(self.alpha)),
                           cy + chord / 2 * math.sin(math.radians(self.alpha)), 0.0], "color": "#f59e0b"})
        return out

    def _field_entities(self) -> list[dict]:
        out = []
        max_speed = max(self.lattice.max_speed(), 1e-9)
        for i in range(8, NX - 8, 15):
            for j in range(6, NY - 6, 11):
                if self.lattice.solid[i, j]:
                    continue
                ux, uy = self.lattice.ux[i, j], self.lattice.uy[i, j]
                speed = math.hypot(ux, uy)
                if speed < 1e-5:
                    continue
                x, y = self._scene(i, j)
                scale = 0.22 * min(1.0, speed / max_speed)
                out.append({
                    "id": f"vec-{i}-{j}",
                    "shape": "line",
                    "pos": [x, y, 0.0],
                    "to": [x + ux / max(speed, 1e-9) * scale, y + uy / max(speed, 1e-9) * scale, 0.0],
                    "color": self._color(speed),
                })
        return out

    def _streamlines(self) -> list[dict]:
        out = []
        seeds = [0.22, 0.42, 0.62, 0.82, 1.02, 1.22, 1.42]
        for index, y in enumerate(seeds):
            i, j = 0.20 * (NX - 1), y / TUNNEL_H * (NY - 1)
            points = []
            for _ in range(46):
                ii = min(NX - 2, max(1, int(round(i))))
                jj = min(NY - 2, max(1, int(round(j))))
                if self.lattice.solid[ii, jj]:
                    break
                points.append(self._scene(i, j))
                ux, uy = self.lattice.ux[ii, jj], self.lattice.uy[ii, jj]
                norm = max(math.hypot(ux, uy), 1e-9)
                i += (ux / norm) * 2.2
                j += (uy / norm) * 2.2
                if i >= NX - 2:
                    break
            for k in range(len(points) - 1):
                out.append({
                    "id": f"stream-{index}-{k}",
                    "shape": "line",
                    "pos": [points[k][0], points[k][1], 0.0],
                    "to": [points[k + 1][0], points[k + 1][1], 0.0],
                    "color": "#0ea5e9",
                })
        return out

    def _force_entities(self) -> list[dict]:
        cx, cy = self._scene(self.lattice.cx, self.lattice.cy)
        c = self.coefficients
        lift_len = min(0.7, abs(c["cl"]) * 0.5)
        drag_len = min(0.7, abs(c["cd"]) * 3.0)
        return [
            {"id": "force-lift", "shape": "line", "pos": [cx, cy, 0.0], "to": [cx, cy + lift_len, 0.0],
             "color": "#22c55e" if c["cl"] >= 0 else "#ef4444"},
            {"id": "force-drag", "shape": "line", "pos": [cx, cy, 0.0], "to": [cx + drag_len, cy, 0.0],
             "color": "#f97316"},
        ]

    def entities(self) -> list[dict]:
        return [*self._static_entities(), *self._airfoil_entities(), *self._field_entities(),
                *self._streamlines(), *self._force_entities()]

    def patch(self) -> list[dict]:
        return [*self._airfoil_entities(), *self._field_entities(), *self._streamlines(), *self._force_entities()]
