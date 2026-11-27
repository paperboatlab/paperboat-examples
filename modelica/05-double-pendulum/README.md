# 05 Double pendulum

`Modelica.Mechanics.MultiBody`: the World, two revolute joints and two box bodies, falling from horizontal with a damper on the upper joint. Articula draws the bodies in 3D. As MSL `MultiBody.Examples.Elementary.DoublePendulum`.

**Docs:** Articula's manual, <https://paperboatlab.org/apps/articula/>. Back to the [Modelica examples](../README.md).

## Open

```sh
paperboat package add omc Modelica@4.1.0 --project modelica/05-double-pendulum   # once: the MSL it uses
paperboat app open articula modelica/05-double-pendulum
```

The folder is the workspace: open `DoublePendulum` from **Files** and press **Simulate** (`Ctrl R`).

## Check

```sh
python3 golden.py modelica/05-double-pendulum   # from the repository root: omc simulate.mos, then compare with golden.json
```

It checks both joint angles, to 1e-3 rad (the motion is chaotic, so the run is short) at the experiment's output times (`example.toml`, [golden tests](../../docs/golden.md)).
