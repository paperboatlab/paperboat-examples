# 06 Speed control

A feedback loop from MSL blocks: a PI controller (`Modelica.Blocks.Continuous.LimPID`) drives a torque on a loaded shaft to hold a speed set point. Its torque saturates while the shaft spins up, and anti-windup keeps the overshoot small.

**Docs:** Articula's manual, <https://paperboatlab.org/apps/articula/>. Back to the [Modelica examples](../README.md).

## Open

```sh
paperboat package add omc Modelica@4.1.0 --project modelica/06-speed-control   # once: the MSL it uses
paperboat app open articula modelica/06-speed-control
```

The folder is the workspace: open `SpeedControl` from **Files** and press **Simulate** (`Ctrl R`).

## Check

```sh
python3 golden.py modelica/06-speed-control   # from the repository root: omc simulate.mos, then compare with golden.json
```

It checks the shaft's speed and the controller's torque at the experiment's output times (`example.toml`, [golden tests](../../docs/golden.md)).
