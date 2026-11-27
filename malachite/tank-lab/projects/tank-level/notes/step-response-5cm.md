---
id: n_example0001
created: 2026-11-17T14:03:00Z
author: lab
project: tank-level
kind: experiment
status: in progress
due: 2026-11-28
tags: [tank, step, level-sensor]
---

# Step response at 5 cm

Second step test on the tank after recalibrating the level sensor (see [[protocol-level-sensor]]).
Setpoint from 0 to **5 cm**, pump limited to 60 %, PID gains from [[pump-check]].

![[tank-rig.jpg|The rig on bench 2: pump, tank, outlet valve, level sensor]]

## Model

The tank as a first-order lag, its level $h$ driven by the pump command $u$ with gain $K$ and time constant $\tau$:

$$
\tau \, \dot h(t) = -h(t) + K \, u(t), \qquad h(s) = \frac{K}{\tau s + 1} \, u(s)
$$

## Run

The step as the camera saw it (sped up from the record):

![[step-5cm.webm]]

The run's level, read from its record, overshoot and settling time:

```python
import csv
with open("../runs/2026-11-17_14-01/level.csv") as f:
    rows = [(float(r["t"]), float(r["level"])) for r in csv.DictReader(f)]
peak = max(l for _, l in rows)
overshoot = (peak - 5.0) / 5.0
settled = next(t for t, _ in reversed(rows) if abs(_ - 5.0) > 0.1)
print(f"overshoot {overshoot:.1%}, settled after {settled - 10:.1f} s")
round(overshoot, 3)
```

A plot without any package: an object that draws itself as SVG.

```python
class Plot:
    def __init__(self, xy, w=640, h=200):
        self.xy, self.w, self.h = xy, w, h
    def _repr_svg_(self):
        xs = [x for x, _ in self.xy]; ys = [y for _, y in self.xy]
        sx = lambda x: 40 + (x - min(xs)) / (max(xs) - min(xs)) * (self.w - 50)
        sy = lambda y: self.h - 20 - (y - min(ys)) / (max(ys) - min(ys)) * (self.h - 30)
        pts = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in self.xy)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">'
                f'<line x1="40" x2="{self.w - 10}" y1="{sy(5):.1f}" y2="{sy(5):.1f}" stroke="#05a5b3" stroke-dasharray="5 4"/>'
                f'<polyline points="{pts}" fill="none" stroke="#417565" stroke-width="1.8"/></svg>')
Plot(rows)
```

The same in Julia, once its image is pulled:

```julia
level = [parse(Float64, split(l, ",")[2]) for l in collect(eachline("../runs/2026-11-17_14-01/level.csv"))[2:end]]
println("peak ", round(maximum(level), digits = 2), " cm")
```

## Observations

- Overshoot about 9 %, settled about 38 s after the step (the first cell above). Same shape as [[pump-check]] with the old sensor.
- Above 8 cm the sensor reads about 1.5 mm high: see [[sensor-drift]].
- Next: repeat at 10 cm for [[tank-characterisation-v2]].

> [!success] Within spec
> Under 10 % overshoot with the pump limited to 60 %.
