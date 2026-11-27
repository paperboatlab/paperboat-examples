# Hub examples

[Paperboat Malachite](https://github.com/paperboatlab/malachite) hubs that use every app: notes,
Simplicial stations and flows, Julix design scripts and Modelica models in one folder. The first is
the Furuta pendulum study, `furuta-lab/` (ex#47). Hubs of notes alone are in [`malachite/`](../malachite/). Back to the [repository](../README.md).

A hub's `example.toml` has one check per app it uses, each run in its folder of the hub
([golden tests](../docs/golden.md)).

`furuta-lab/` is a git subtree of its own repository: its history is kept, and only `example.toml`
and `golden/` are this repository's. Take its later changes with
`git subtree pull --prefix=hubs/furuta-lab <furuta-lab repository> main` (or, without git-subtree,
`git pull -X subtree=hubs/furuta-lab <repository> main`), then `python3 golden.py --update hubs/furuta-lab`
when its numbers moved on purpose.
