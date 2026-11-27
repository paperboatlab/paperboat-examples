---
id: n_example0002
created: 2026-11-10T09:00:00Z
author: lab
project: tank-level
kind: protocol
status: open
tags: [level-sensor]
---

# Level sensor: weekly zero check

1. Drain the tank and wait 2 minutes.
2. Read the sensor; it should say 0.0 ± 0.5 mm.
3. Note the reading in a new entry linked to [[tank-level]].

> [!warning] Drain it first
> A reading with water in the tank is not a zero: the sensor sees the surface.

The sensor's datasheet, for the range and the accuracy to expect:

![[level-sensor-datasheet.pdf]]
