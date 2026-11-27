"""03-low-poly-island-python: a procedural low-poly archipelago (Level 03).

Static pipeline evaluation (`[run] mode = "once"`), list & array wires, block commenting (Ctrl+/)
and block bypassing (Ctrl+Shift+Y). The engine loads this file into a Python runtime
(paperboat_runtime); each block is registered with its ports and params. Points travel as a table
(rows of x, z), heights as a list of numbers, trees as a table of x, y, z.
"""

import paperboat_runtime as pb

from domain import mesh_builder as m

POINTS = {"id": "points", "type": "points"}
HEIGHTS = {"id": "heights", "type": "numbers"}
TREES = {"id": "trees", "type": "trees"}

pb.register("grid", m.Grid, definition={
    "label": "Grid", "description": "Generates 2D grid matrix of (x, z) coordinates",
    "outputs": [POINTS], "params": {"nx": 24, "nz": 24, "spacing": 0.35},
})
pb.register("noise", m.NoiseHarmonics, definition={
    "label": "Noise Harmonics", "description": "Procedural multi-octave 2D noise terrain generator",
    "inputs": [POINTS], "outputs": [HEIGHTS],
    "params": {"seed": 42, "octaves": 4, "persistence": 0.5, "lacunarity": 2.0, "scale": 3.0, "height_scale": 2.8},
})
pb.register("falloff", m.RadialFalloff, definition={
    "label": "Radial Falloff", "description": "Distance-from-center falloff weighting ensuring island silhouette",
    "inputs": [POINTS, HEIGHTS], "outputs": [HEIGHTS], "params": {"radius": 3.8, "power": 2.2},
})
pb.register("erosion", m.ErosionFilter, definition={
    "label": "Erosion & Terracing", "description": "Beach shelf clamping and ridge sharpening elevation filter",
    "inputs": [HEIGHTS], "outputs": [HEIGHTS],
    "params": {"sea_level": 0.25, "beach_shelf": 0.12, "ridge_sharpness": 1.35},
})
pb.register("trees", m.TreePlacer, definition={
    "label": "Vegetation Placement", "description": "Detects slope & elevation sweet spot for procedural palm trees",
    "inputs": [POINTS, HEIGHTS], "outputs": [TREES],
    "params": {"min_elevation": 0.28, "max_elevation": 0.85, "max_slope": 0.40, "min_dist": 0.70},
})
pb.register("island_scene", m.IslandScene, definition={
    "label": "Island Scene → Station", "kind": "source",
    "description": "Packs procedural low-poly geometry into Station 3D entities",
    "inputs": [POINTS, HEIGHTS, TREES], "outputs": ["max_elevation"],
    "params": {"water_size": 12.0, "water_color": "#0e7490", "sun_x": 0.6, "sun_y": -0.7, "sun_z": 0.4,
               "block_size": 0.35, "sea_level": 0.25},
})
