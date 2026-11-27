# Tutorial 08: Air-Hockey Puck Tracker

> **Level**: 08 · Advanced  
> **Domain**: Sports Analytics & Computer Vision  
> **Language**: C++ (optional OpenCV)  
> **Port**: 51308  
> **UI Cockpit**: Commander Split View  
> **Core Concepts**: the optional `opencv` toolkit (HSV range → morphology → centroid → image view), image wires, alpha-beta tracking, degraded fallback.

---

## 1. Overview

A synthetic overhead camera films an air-hockey table. The Flow page is built from the
**optional OpenCV toolkit**, not a private copy of the vision code:

```text
Overhead Camera → HSV range → Open → Close → Centroid → Puck Tracker
                              ├→ Image view (mask)
                              └→ Centroid's marked image → Image view (result)
```

- **Camera** (domain block) — a deterministic 320 × 240 frame of a dark rink, rails, two
  mallets and a saturated red puck. It also exposes the truth (`truth_u`, `truth_v`, bounces).
- **HSV range** (`opencv/hsv_range`) — the red puck window (`h 0–12`, `s ≥ 120`, `v ≥ 80`);
  white rails and blue/green mallets fall outside it.
- **Open/Close** (`opencv/open`, `opencv/close`) — remove speckle, fill the puck.
- **Centroid** (`opencv/centroid`, added for this tutorial) — the largest white blob's
  centroid `u,v`, area and equivalent radius, plus a marked image for the Board.
- **Puck Tracker** (domain block) — an alpha-beta filter in image space; the table point is
  `x = (u − 160)/110`, `z = (v − 120)/110`, and a rail/mallet hit is a velocity sign flip.

### Optional toolkit and degraded mode

`station.toml` does **not** hard-require OpenCV. CMake links `paperboat::toolkit_opencv` when
it is available (installed in Simplicial's `engine/toolkit/opencv` by
`paperboat toolkit install opencv`, or a `simplicial-toolkit-opencv` checkout beside this
repository) and defines `PAPERBOAT_HAS_OPENCV`. With it, `main.cpp` loads
`descriptor.toml`. Without it, it loads `descriptor-degraded.toml`, which uses the domain's
synthetic vision stage and a placeholder Image tile. Both run the same tracker and pass the
same golden result.

---

## 2. Cockpit exploration

```sh
paperboat run 08
# http://localhost:30471/?station=ws://localhost:51308
```

1. **Commander view** (`Alt+C`) — the 3D rink, mallets, puck and trail on the left; the
   OpenCV stages on the right.
2. **Board** — three Image views (raw frame, threshold mask, centroid-marked result), a
   two-channel Scope of image velocity, and tracker/truth bounce readouts.
3. **Variables** (`Alt+V`) — `hue_min` / `hue_max` document the red window.
4. **Console** — `tracker: direction change (n)` and the per-run summary.

> The camera is synthetic so the example is reproducible and needs no webcam. Replace the
> frame in `domain/state.cpp` with a real capture and the toolkit pipeline is unchanged.

---

## 3. Files

```text
08-air-hockey-tracker-cpp/
├── station.toml               # format = 0, port 51308, solver = rk4
├── descriptor.toml            # full OpenCV pipeline
├── descriptor-degraded.toml   # synthetic vision path, no OpenCV
├── CMakeLists.txt             # optional paperboat::toolkit_opencv detection
├── main.cpp                   # chooses the descriptor from PAPERBOAT_HAS_OPENCV
├── domain/
│   ├── state.hpp              # AirHockey: puck, mallets, camera frame, trail
│   ├── state.cpp              # flight, rail/mallet collisions, 3D rink
│   ├── vision.hpp             # register_tracker()
│   └── vision.cpp             # Camera, degraded Vision, Tracker, Truth, fallback view
├── expected.json              # golden run: tracker x/z, 11 true bounces
├── example.toml               # how the golden harness builds and runs it (docs/golden.md)
└── README.md
```

The `centroid` block lives in the toolkit repository:
`simplicial-toolkit-opencv/engine/toolkit/opencv/src/opencv/centroid/`.

---

## 4. Verification

```sh
python3 golden.py simplicial/08-air-hockey-tracker-cpp   # from the repository root: build, run, compare
paperboat check simplicial/08-air-hockey-tracker-cpp     # manifest, catalog, smoke and golden
```

To force the degraded build:

```sh
cmake -S . -B build-no-cv -DPAPERBOAT_ENGINE_DIR=<simplicial>/engine -DPAPERBOAT_WITH_OPENCV=OFF
```
