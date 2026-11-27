# 04 DC motor

Modelica Standard Library parts from two domains: an armature circuit (`Modelica.Electrical.Analog`) whose EMF turns a rotor, and an elastic shaft to the load (`Modelica.Mechanics.Rotational`), on a 10 V step. The DC drive of Articula's station export, standalone.

**Docs:** Articula's manual, <https://paperboatlab.org/apps/articula/>. Back to the [Modelica examples](../README.md).

## Open

```sh
paperboat package add omc Modelica@4.1.0 --project modelica/04-dc-motor   # once: the MSL it uses
paperboat app open articula modelica/04-dc-motor
```

The folder is the workspace: open `DCMotor` from **Files** and press **Simulate** (`Ctrl R`).

## Check

```sh
python3 golden.py modelica/04-dc-motor   # from the repository root: omc simulate.mos, then compare with golden.json
```

It checks the armature current and the load's speed at the experiment's output times (`example.toml`, [golden tests](../../docs/golden.md)).
