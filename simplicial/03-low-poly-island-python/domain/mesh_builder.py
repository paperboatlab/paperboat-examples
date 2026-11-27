"""Procedural low-poly 3D archipelago mesh builder, filters, and scene assembler.

Generates 2D coordinate grids, elevation arrays, erosion and vegetation placement,
and packs geometry into Station 3D entities.
"""

import math

import paperboat_runtime as pb

from .noise import octave_noise


def shade_color(hex_color: str, factor: float) -> str:
    """Modulate hex color brightness by factor in [0.5, 1.5]."""
    factor = min(max(factor, 0.5), 1.5)
    hex_clean = hex_color.lstrip("#")
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    r = min(255, max(0, round(r * factor)))
    g = min(255, max(0, round(g * factor)))
    b = min(255, max(0, round(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def biome_color(h: float, sea_level: float = 0.25) -> str:
    """Map elevation height to low-poly biome palette."""
    rel_h = h - sea_level
    if rel_h <= 0.12:
        # Sandy beach fringe
        return "#eab308"
    elif rel_h <= 0.85:
        # Lush tropical forest & grassy slopes
        return "#15803d"
    elif rel_h <= 1.65:
        # High mountain rocky ridge
        return "#64748b"
    else:
        # Snow-capped summit peaks
        return "#f8fafc"


class Block:
    """A block whose params (keywords, as station.py's definition gives them) are `self.p`."""

    def __init__(self, **params) -> None:
        self.p = params


class Grid(Block):
    """Generates a 2D grid matrix of (x, z) coordinate pairs."""

    def step(self, ctx, inputs) -> dict:
        nx = max(int(self.p.get("nx", 24)), 2)
        nz = max(int(self.p.get("nz", 24)), 2)
        s = float(self.p.get("spacing", 0.35))
        ox = (nx - 1) * s / 2.0
        oz = (nz - 1) * s / 2.0
        points = [(i * s - ox, j * s - oz) for i in range(nx) for j in range(nz)]
        return {"points": points}


class NoiseHarmonics(Block):
    """Evaluates multi-octave 2D procedural noise elevation heights."""

    def step(self, ctx, inputs) -> dict:
        points = inputs.get("points", [])
        seed = int(self.p.get("seed", 42))
        octaves = int(self.p.get("octaves", 4))
        persistence = float(self.p.get("persistence", 0.5))
        lacunarity = float(self.p.get("lacunarity", 2.0))
        scale = float(self.p.get("scale", 3.0))
        height_scale = float(self.p.get("height_scale", 2.8))

        heights = [
            octave_noise(
                x, z,
                seed=seed,
                octaves=octaves,
                persistence=persistence,
                lacunarity=lacunarity,
                scale=scale,
            ) * height_scale
            for x, z in points
        ]
        return {"heights": heights}


class RadialFalloff(Block):
    """Tapers elevation heights radially into the ocean."""

    def step(self, ctx, inputs) -> dict:
        points = inputs.get("points", [])
        heights = inputs.get("heights", [])
        radius = float(self.p.get("radius", 3.8))
        power = float(self.p.get("power", 2.2))

        result = []
        for i, h in enumerate(heights):
            x, z = points[i] if i < len(points) else (0.0, 0.0)
            dist = math.hypot(x, z) / max(radius, 1e-6)
            if dist >= 1.0:
                factor = 0.0
            else:
                f = max(0.0, 1.0 - (dist ** power))
                factor = f * f * (3.0 - 2.0 * f)  # smoothstep
            result.append(h * factor)
        return {"heights": result}


class ErosionFilter(Block):
    """Filters elevation heights by clamping sandy beaches and sharpening rocky ridges.

    Supports block bypass (Ctrl+Shift+Y) to inspect raw terrain.
    """

    def step(self, ctx, inputs) -> dict:
        heights = inputs.get("heights", [])
        sea_level = float(self.p.get("sea_level", 0.25))
        beach_shelf = float(self.p.get("beach_shelf", 0.12))
        ridge_sharpness = float(self.p.get("ridge_sharpness", 1.35))

        result = []
        for h in heights:
            if h <= sea_level:
                # Submerged
                result.append(0.0)
            elif h <= sea_level + beach_shelf:
                # Flat sandy beach shelf
                t = (h - sea_level) / beach_shelf
                result.append(sea_level + 0.04 * t)
            else:
                # Mountain slopes and sharpened peaks
                t = (h - sea_level - beach_shelf)
                result.append(sea_level + 0.04 + (t ** ridge_sharpness))
        return {"heights": result}


class TreePlacer(Block):
    """Identifies valid slope and elevation bands to place 3D palm trees.

    Supports block commenting (Ctrl+/) to mute vegetation.
    """

    def step(self, ctx, inputs) -> dict:
        points = inputs.get("points", [])
        heights = inputs.get("heights", [])
        if not points or not heights or len(points) != len(heights):
            return {"trees": []}

        min_elev = float(self.p.get("min_elevation", 0.28))
        max_elev = float(self.p.get("max_elevation", 0.85))
        max_slope = float(self.p.get("max_slope", 0.40))
        min_dist = float(self.p.get("min_dist", 0.70))

        # Identify candidate grid points
        candidates = []
        n = len(points)
        # Approximate grid dimension
        nx = int(round(math.sqrt(n)))
        for idx, ((x, z), h) in enumerate(zip(points, heights)):
            if not (min_elev <= h <= max_elev):
                continue
            # Check slope relative to 4 neighbors
            i, j = idx // nx, idx % nx
            max_dh = 0.0
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < nx and 0 <= nj < (n // nx):
                    neighbor_idx = ni * nx + nj
                    if neighbor_idx < len(heights):
                        max_dh = max(max_dh, abs(h - heights[neighbor_idx]))
            if max_dh <= max_slope:
                candidates.append((x, h, z))

        # Spacing filter (poisson-disc style greedy selection)
        placed: list[tuple[float, float, float]] = []
        for x, y, z in candidates:
            if all(math.hypot(x - px, z - pz) >= min_dist for px, _, pz in placed):
                placed.append((x, y, z))

        return {"trees": placed}


class IslandScene(Block):
    """Assembles 3D entities (ocean, low-poly terrain, palm trees, sun arrow) in Station scene."""

    scene: list[dict] = []

    def entities(self) -> list[dict]:
        """What the Station page draws: the island this block last built."""
        return self.scene

    def step(self, ctx, inputs) -> dict:
        points = inputs.get("points", [])
        heights = inputs.get("heights", [])
        trees = inputs.get("trees", []) or []

        water_size = float(self.p.get("water_size", 12.0))
        water_color = str(self.p.get("water_color", "#0e7490"))
        block_size = float(self.p.get("block_size", 0.35))
        sea_level = float(self.p.get("sea_level", 0.25))
        lx = float(self.p.get("sun_x", 0.6))
        ly = float(self.p.get("sun_y", -0.7))
        lz = float(self.p.get("sun_z", 0.4))
        l_len = math.sqrt(lx * lx + ly * ly + lz * lz) or 1.0
        lx, ly, lz = lx / l_len, ly / l_len, lz / l_len

        # Directional light indicator
        sun_dist = 7.0
        sun_pos = [-lx * sun_dist, -ly * sun_dist, -lz * sun_dist]
        sun_entities = [
            {
                "id": "sun-orb",
                "shape": "sphere",
                "pos": sun_pos,
                "size": [0.35, 0.35, 0.35],
                "color": "#facc15",
            },
            {
                "id": "sun-ray",
                "shape": "line",
                "pos": sun_pos,
                "to": [0.0, 1.0, 0.0],
                "color": "#facc15",
            },
        ]

        # Turquoise ocean water plane
        ocean = {
            "id": "ocean",
            "shape": "box",
            "pos": [0.0, -0.05, 0.0],
            "size": [water_size, 0.1, water_size],
            "color": water_color,
        }

        # Terrain facets/columns
        terrain_entities = []
        max_h = 0.0
        n = min(len(points), len(heights))

        for i in range(n):
            x, z = points[i]
            h = heights[i]
            if h <= sea_level:
                continue
            max_h = max(max_h, h)

            # Shading factor based on directional sun vector
            # Simulate faceted slope normal dot sun vector
            base_color = biome_color(h, sea_level)
            # Center-relative normal tilt
            nx, nz = x / (water_size / 2.0), z / (water_size / 2.0)
            ny = 1.0
            norm = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            dot = -(nx * lx + ny * ly + nz * lz) / norm
            brightness = 0.75 + 0.35 * max(0.0, dot)
            facet_color = shade_color(base_color, brightness)

            terrain_entities.append({
                "id": f"terrain-{i}",
                "shape": "box",
                "pos": [round(x, 4), round(h / 2.0, 4), round(z, 4)],
                "size": [block_size, round(h, 4), block_size],
                "color": facet_color,
            })

        # Palm tree instances
        tree_entities = []
        for j, (tx, ty, tz) in enumerate(trees):
            trunk_h = 0.45
            tree_entities.append({
                "id": f"tree-trunk-{j}",
                "shape": "box",
                "pos": [round(tx, 4), round(ty + trunk_h / 2.0, 4), round(tz, 4)],
                "size": [0.06, trunk_h, 0.06],
                "color": "#78350f",
            })
            tree_entities.append({
                "id": f"tree-crown-{j}",
                "shape": "sphere",
                "pos": [round(tx, 4), round(ty + trunk_h + 0.12, 4), round(tz, 4)],
                "size": [0.22, 0.22, 0.22],
                "color": "#15803d",
            })

        # The block draws the island on the Station page itself: its entities are the scene.
        self.scene = [ocean, *sun_entities, *terrain_entities, *tree_entities]
        pb.log(f"Archipelago generated: {len(terrain_entities)} terrain facets, "
               f"{len(tree_entities) // 2} palm trees, max elevation {max_h:.1f} m")
        return {"max_elevation": round(max_h, 4)}

