"""Airfoil CFD domain: a D2Q9 lattice-Boltzmann wind tunnel and its aerodynamic polars."""

from .lbm_solver import LatticeBoltzmann
from .airfoil import naca0012_mask, naca0012_outline
from .forces import polars
from .state import WindTunnel
from .blocks import BLOCKS

__all__ = ["BLOCKS", "LatticeBoltzmann", "WindTunnel", "naca0012_mask", "naca0012_outline", "polars"]
