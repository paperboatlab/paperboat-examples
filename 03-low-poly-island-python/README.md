# Tutorial 03: Low-Poly Island

> **Level**: 03 · Elementary  
> **Domain**: Creative Coding & Procedural Game Worlds  
> **Language**: Python  
> **Port**: 8767  
> **UI Cockpit**: Navigator Mode  
> **Core Concepts**: One-shot static evaluation (`solver = "discrete"`), list/array wires, block commenting (`Ctrl+/`), block bypassing (`Ctrl+Shift+Y`).

---

## 1. Overview & Domain Mechanics

Unlike time-series physical simulations driven by continuous ODE integration clocks, **Tutorial 03: Low-Poly Island** demonstrates **static pipeline evaluation**. The Flow canvas executes as a procedural generative graph where wires carry structured arrays—lists of coordinate pairs, elevation heights, and 3D entity positions.

### Domain Mechanics
- **Grid Generation**: Generates a centered 2D grid matrix of $(x, z)$ coordinate pairs.
- **Noise Harmonics**: Evaluates multi-octave 2D Simplex/Perlin noise (fractal Brownian motion):
  $$\text{fBm}(x, z) = \sum_{k=0}^{\text{octaves}-1} p^k \cdot \text{noise}\left(x \cdot \frac{l^k}{\text{scale}},\, z \cdot \frac{l^k}{\text{scale}}\right)$$
  where $p$ is persistence and $l$ is lacunarity.
- **Radial Falloff**: Multiplies heights by a radial distance weighting function to taper edges down into the ocean:
  $$f(r) = \max\left(0,\, 1 - \left(\frac{r}{R}\right)^{\gamma}\right)$$
- **Erosion & Terracing**: Filters raw noise elevation by clamping sub-surface heights to zero, creating a flat sandy beach shelf, and sharpening high mountain ridges.
- **Vegetation Placement**: Scans terrain slopes and elevation bands ($0.28 \le h \le 0.85$, gentle slope $\Delta h \le 0.40$) to procedurally place instanced 3D coconut palm trees with minimum distance spacing.
- **Sun Angle Vector**: Directional incident vector $\vec{L} = [0.6, -0.7, 0.4]$ computes flat-shaded facet lighting across terrain blocks.

---

## 2. Cockpit UI Exploration

Launch the backend and open the Paperboat Cockpit:
```bash
./bin/paperboat run 03-low-poly-island-python
```
Navigate to `http://localhost:3047/?backend=ws://localhost:8767`.

### 2.1 One-Shot Static Evaluation
In continuous backends, a simulation clock steps forward in time. In this procedural backend:
- The backend manifest specifies `solver = "discrete"` and server mode `"once"`.
- The entire pipeline evaluates in dependency order whenever a parameter or wire changes.

### 2.2 List & Array Wires
Trace the signal flow through the canvas:
1. `Grid`: Outputs an array wire carrying $(x, z)$ 2D point tuples.
2. `Noise Harmonics`: Computes elevation array `heights` from point coordinates.
3. `Radial Falloff`: Blends `points` and `heights` to constrain the island archipelago.
4. `Erosion & Terracing`: Filters `heights` to shape sandy beaches and craggy peaks.
5. `Vegetation Placement`: Evaluates slope gradients to emit palm tree coordinate instances.
6. `Island Scene`: Translates geometry arrays into 3D Station entities.

### 2.3 Block Commenting (`Ctrl+/`)
Select the **Vegetation Placement** block (`trees-1`) and press `Ctrl+/`:
- The block is commented out (`// commented`).
- The downstream `Island Scene` receives an empty tree list, immediately regenerating the island without palm trees.
- Press `Ctrl+/` again to re-enable procedural vegetation.

### 2.4 Block Bypassing (`Ctrl+Shift+Y`)
Select the **Erosion & Terracing** block (`erosion-1`) and press `Ctrl+Shift+Y`:
- The block is commented through (`// bypass`).
- Because its input and output port IDs match (`heights` $\to$ `heights`), the upstream raw radial falloff heights pass straight through without breaking wire connectivity.
- Observe the terrain mutate into jagged, un-eroded noise cliffs. Press `Ctrl+Shift+Y` again to restore the erosion filter.

### 2.5 Variables Sheet (`Alt+V`)
Press `Alt+V` to open the Variables sheet:
- `seed`: Modify the procedural seed (e.g. from `42` to `1337`) to generate completely new archipelago topographies.
- `octaves`: Adjust harmonic detail layers between `1` (smooth rolling hills) and `6` (highly craggy ridges).
- `scale`: Tweak horizontal feature scale.
- `sea_level`: Raise or lower sea level to submerge low-lying atolls or expose more beach.

### 2.6 Station 3D Scene Visuals
- **Turquoise Ocean Plane**: Flat water surface plate (`#0e7490`).
- **Low-Poly Terrain Facets**: 3D extruded prism facets colored across sandy beach (`#eab308`), tropical forest (`#15803d`), rocky slopes (`#64748b`), and snowy peaks (`#f8fafc`).
- **Solar Incident Vector**: Visual yellow arrow indicator and sun orb along $\vec{L} = [0.6, -0.7, 0.4]$ casting directional facet illumination.
- **Palm Tree Instances**: Procedural coconut palms with wooden trunks and green canopies.

---

## 3. Architecture & File Structure

```text
03-low-poly-island-python/
├── backend.toml          # Declarative format = 0 manifest (port = 8767, solver = "discrete")
├── descriptor.toml       # Variables sheet (seed, octaves, scale), Flow starter graph
├── server.py             # Minimal Python entrypoint (paperboat.serve)
├── domain/
│   ├── __init__.py       # Exports BLOCKS, IslandState, IslandScene
│   ├── noise.py          # Pure Python multi-octave 2D Simplex noise generator
│   └── mesh_builder.py   # Procedural blocks, erosion filter, 3D scene assembler
├── expected.json         # Golden run assertions
└── README.md             # Hands-on tutorial guide
```

---

## 4. Verification

Run local verification suites:
```bash
# Fast manifest & catalog check
./paperboat/bin/paperboat check paperboat-examples/03-low-poly-island-python --fast

# Full 4-stage check (manifest, catalog, smoke, golden)
./paperboat/bin/paperboat check paperboat-examples/03-low-poly-island-python

# Golden verification
python3 paperboat/protocol/golden.py --examples paperboat-examples 03-low-poly-island-python
```
