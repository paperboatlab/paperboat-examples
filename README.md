# furuta-lab

An example [Paperboat](https://github.com/paperboatlab/paperboat) hub: a made-up research study, kept the
way a lab would keep it, with the four apps working on the same files. Bench 3's Furuta pendulum gets
a grey-box model fitted to it and an MPC on top, and the notebook records whether that beat the
datasheet's LQR. The rig is simulated (`tools/`); the study, its files and its numbers are consistent
with it.

**Read it in Malachite:** open the hub and start at `index.md`, the reading order. The report is
`report.md`. **Docs:** <https://paperboatlab.org/apps/malachite/> (hubs, notes, cells).

## Layout

```text
index.md, report.md, notes/   Malachite: the notebook (start at index.md)
model/                        Articula: Furuta.mo (the model, and the rig); furuta.jl, the same in Julia
stations/furuta-rig/          the Simplicial station Articula generated from Furuta.Rig
flows/                        Simplicial: one flow per experiment, the NLP and MPC problems
design/                       Julix: the LQR gain and the planned trajectory
runs/                         the recorded runs (CSV), one folder per experiment
media/, results.toml          the figures and numbers the notes quote
tools/                        the simulated bench: make_runs.jl regenerates runs, outputs, figures, flows
```

Nothing has to run in order: each file is what one app left behind, and `index.md` says which to read
when.

## Open it

```sh
paperboat app open malachite furuta-lab     # the notebook; Connect to a hub in the other apps
```

The flows run on `stations/furuta-rig`, which needs Simplicial with the control and optimization
toolkits (`paperboat toolkit install control`). A block's file param resolves against the station's
folder, so the flows use the station folder in the hub rather than a packed `.pst`.

## Regenerate

```sh
julia tools/make_runs.jl     # plain Julia 1.11, no packages; about 40 s, deterministic
```

It rebuilds every run, design output, flow and figure from `tools/rig.toml`, the simulated bench (the
truth the study tries to find).

## Licence

GNU General Public License version 3 (see [LICENSE](LICENSE)).
