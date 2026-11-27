---
id: n_example0007
created: 2026-11-17T13:00:00Z
author: lab
kind: guide
tags:
  - guide
  - tank/level
---

# Start here

A small lab notebook: one tank, its level held by a PI controller on a pump. Open
[[projects/tank-level/tank-level|the project]], then its experiments. #tank/level

What each note shows:

- [[step-response-5cm]]: a picture and a video embedded, math, and code cells that run in Python and
  Julia sessions ([[step-response-5cm#Run|the run]]).
- [[protocol-level-sensor]]: a PDF embedded, a numbered protocol.
- [[sensor-drift]]: a table, tags written inline, a folded callout.
- [[tank-characterisation-v2]]: a table with aligned columns and a diagram.
- [[pump-check]]: the plainest note; every note above links to another, so each has backlinks.

The board in `views/tank-level.toml` groups the project's notes by status.

## Callouts

Every kind Malachite knows, each once:

> [!note]
> A kind without a title takes its name as the title.

> [!abstract] Summary
> The tank holds 5 cm within 9 % overshoot.

> [!info] Bench 2
> The rig lives on bench 2, next to the sink.

> [!todo] This week
> Steps 2 and 3 of [[tank-characterisation-v2]].

> [!tip] Zero the sensor first
> Before every run: [[protocol-level-sensor]].

> [!success] Step 1 done
> See [[step-response-5cm]].

> [!question]- Why does it read high?
> Probably the sensor's accuracy band: [[sensor-drift]].

> [!warning] Hot pump
> The pump runs hot above 80 % for more than a minute.

> [!failure] First step test
> The sensor was not zeroed; the run was thrown away.

> [!danger] Mains
> The pump's supply is mains: unplug it before opening the box.

> [!bug] Logger drops a sample
> Now and then, at a minute boundary.

> [!example] A step test
> [[step-response-5cm]] is one.

> [!quote] The lab rule
> If it isn't written down, it didn't happen.

The same kinds answer to other names, fold open with `+`, and an unknown kind is shown as a note:

> [!tldr]+ An alias, open
> `tldr` is an abstract.

> [!caution]- An alias, closed
> `caution` is a warning.

> [!sticky] Unknown
> Shown as a note.
