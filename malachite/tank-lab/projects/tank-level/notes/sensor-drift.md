---
id: n_example0004
created: 2026-11-18T11:30:00Z
author: lab
project: tank-level
kind: issue
status: open
due: 2026-11-30
tags: [level-sensor, calibration]
---

# Level sensor reads high above 8 cm

Seen first in [[step-response-5cm]], above 8 cm. Check against [[protocol-level-sensor]]. #needs-review

| Ruler [cm] | Sensor [cm] | Error [mm] |
| ---: | ---: | ---: |
| 8.0 | 7.999 | 0.0 |
| 9.0 | 9.031 | +0.3 |
| 10.0 | 10.072 | +0.7 |
| 11.0 | 11.111 | +1.1 |
| 12.0 | 12.151 | +1.5 |

From `calibrate.jl`, which fits a line with a hinge near 8 cm.

> [!bug]- Suspected cause
> [[level-sensor-datasheet.pdf|The datasheet]]: its accuracy changes at 8 cm, to 1 % of the reading above.
