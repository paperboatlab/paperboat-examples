"""A compact D2Q9 lattice-Boltzmann solver (BGK collision, bounce-back walls)."""

import math

import numpy as np

# Discrete velocities: rest, +x, +y, -x, -y and the four diagonals.
EX = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1], dtype=float)
EY = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1], dtype=float)
W = np.array([4 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 36, 1 / 36, 1 / 36, 1 / 36])
OPPOSITE = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6])


class LatticeBoltzmann:
    """A 2-D wind tunnel on a structured lattice, sized for an interactive demo."""

    def __init__(self, nx: int = 160, ny: int = 80, cx: float = 55.0, cy: float = 40.0,
                 chord: float = 90.0, tau: float = 0.53) -> None:
        self.nx, self.ny = nx, ny
        self.cx, self.cy, self.chord = cx, cy, chord
        self.tau = tau
        self.solid = np.zeros((nx, ny), dtype=bool)
        self.alpha = 6.0
        self.u0 = 0.08
        self.f = np.zeros((9, nx, ny), dtype=float)
        self.rho = np.ones((nx, ny), dtype=float)
        self.ux = np.zeros((nx, ny), dtype=float)
        self.uy = np.zeros((nx, ny), dtype=float)
        self.steps = 0
        self.residual = 0.0
        self.reset(self.alpha, self.u0)

    # --- setting up -----------------------------------------------------------------------

    def reset(self, alpha_deg: float, u0: float) -> None:
        from domain.airfoil import naca0012_mask

        self.alpha = float(alpha_deg)
        self.u0 = max(1e-3, float(u0))
        self.solid = naca0012_mask(self.nx, self.ny, self.cx, self.cy, self.chord, self.alpha)
        self.f = self._equilibrium(1.0, self.u0, 0.0)
        self.steps = 0
        self.residual = 1.0
        self._macroscopic()

    def _equilibrium(self, rho, ux, uy) -> np.ndarray:
        out = np.empty((9, self.nx, self.ny), dtype=float)
        for i in range(9):
            cu = EX[i] * ux + EY[i] * uy
            out[i] = W[i] * rho * (1.0 + 3.0 * cu + 4.5 * cu * cu - 1.5 * (ux * ux + uy * uy))
        return out

    def _macroscopic(self) -> None:
        self.rho = self.f.sum(axis=0)
        self.ux = (self.f * EX[:, None, None]).sum(axis=0) / self.rho
        self.uy = (self.f * EY[:, None, None]).sum(axis=0) / self.rho
        self.ux[self.solid] = 0.0
        self.uy[self.solid] = 0.0

    # --- one lattice step -----------------------------------------------------------------

    def step(self) -> None:
        self._macroscopic()
        feq = self._equilibrium(self.rho, self.ux, self.uy)
        self.f -= (self.f - feq) / self.tau
        for i in range(1, 9):
            self.f[i] = np.roll(np.roll(self.f[i], int(EY[i]), axis=1), int(EX[i]), axis=0)
        # Reflect the populations that entered a solid node.
        self.f[:, self.solid] = self.f[OPPOSITE][:, self.solid]
        # Inlet: a steady free stream. Outlet: zero-gradient.
        for i in range(9):
            cu = EX[i] * self.u0
            self.f[i, 0:2, :] = W[i] * (1.0 + 3.0 * cu + 4.5 * cu * cu - 1.5 * self.u0 * self.u0)
        self.f[:, -2:, :] = self.f[:, -4:-2, :]
        self.steps += 1

    def advance(self, alpha_deg: float, u0: float, substeps: int = 6) -> float:
        if abs(alpha_deg - self.alpha) > 0.05 or abs(u0 - self.u0) > 1e-4:
            self.reset(alpha_deg, u0)
        before = self.ux.copy()
        for _ in range(max(1, substeps)):
            self.step()
        self._macroscopic()
        self.residual = float(np.abs(self.ux - before).mean())
        return self.residual

    def max_speed(self) -> float:
        return float(np.hypot(self.ux, self.uy).max())
