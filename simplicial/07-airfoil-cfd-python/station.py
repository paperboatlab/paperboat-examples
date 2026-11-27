"""07-airfoil-cfd-python: a lattice-Boltzmann wind tunnel (Level 07).

The Flow page is the tunnel's pipeline: the airfoil mask, the inflow condition, the D2Q9 lattice
step and the lift/drag polar readout. Move `alpha` in the Variables sheet (or bind it to a knob) to
watch the field separate and the lift curve break past 14 degrees. The Station page draws the
velocity vectors, streamlines and force arrows.

The engine loads this file into a Python runtime (paperboat_runtime): the tunnel is a station
object, the rest are blocks, each registered with its ports and params. The lattice needs numpy,
in the station's package volume: `paperboat package add python numpy --project .`.
"""

import glob
import os
import sys

import paperboat_runtime as pb

# The station's package volume (`paperboat package add`) is a venv the Python runtime doesn't put on
# sys.path in station mode yet (paperboatlab/paperboat#74): add its site-packages here until it does.
for site in glob.glob(os.path.join(os.environ.get("PAPERBOAT_DEPS", "/work/deps"), "venv/lib/python*/site-packages")):
    if site not in sys.path:
        sys.path.append(site)

from domain import blocks  # noqa: E402 (numpy, imported by the domain, is in the volume)
from domain.state import WindTunnel  # noqa: E402

pb.register("wind_tunnel", WindTunnel, definition={
    "base": "object",
    "label": "Wind Tunnel",
    "description": "A 2-D test section with a NACA 0012 and a live velocity field",
})
pb.register("airfoil", blocks.Airfoil, definition={
    "label": "NACA 0012 Mask", "inputs": ["alpha"], "outputs": ["alpha", "solid_fraction", "stalled"],
})
pb.register("inflow", blocks.Inflow, definition={
    "label": "Inflow Condition", "inputs": ["speed"], "outputs": ["u", "reynolds"],
})
pb.register("lbm_step", blocks.LbmStep, definition={
    "label": "LBM Step (D2Q9)", "inputs": ["alpha", "u"], "outputs": ["steps", "residual", "max_speed"],
    "params": {"substeps": 6},
})
pb.register("forces", blocks.Forces, definition={
    "label": "Lift & Drag Polars", "kind": "probe", "inputs": ["alpha", "u"],
    "outputs": ["cl", "cd", "ld", "lift", "drag"],
})
