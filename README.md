# Paperboat examples

Examples for the [Paperboat](https://github.com/paperboatlab/paperboat) apps, grouped by app, each
with golden results that CI checks: Simplicial stations, Julix folders, Modelica models, and hubs
that use them all. They exist to prove the apps and to learn them from, not as products.

**Docs:** each group's README below, and each app's manual at <https://paperboatlab.org/apps/>.

## Layout

```text
simplicial/   the ten-level Simplicial tutorial curriculum: stations and flows
julix/        standalone Julix folders: scripts and notebooks
modelica/     standalone Modelica models, for Articula and omc
hubs/         Malachite hubs that use every app (furuta-lab)
legacy/       the nine stations from before the curriculum, kept for reference; not tested
golden.py     the golden harness; its manifest, example.toml, is in docs/golden.md
```

An app finds its examples here: Simplicial looks for a checkout next to its own
(`../paperboat-examples/simplicial`, or `$PAPERBOAT_EXAMPLES_DIR`), and `paperboat station examples`
fetches this repository when there is none.

## Check

```sh
python3 golden.py            # every example: run headless, compare with its golden files
python3 golden.py --update simplicial/09-modular-synth-cpp   # rewrite one example's golden files
```

A C++ station builds against a [simplicial](https://github.com/paperboatlab/simplicial) checkout
next to this one (or `$SIMPLICIAL_DIR`); a check whose tools are missing is skipped, not failed.

## CI

| Check | What it runs | `dev` |
| --- | --- | --- |
| Golden | `golden.py` over each group, on Linux | [![golden](https://github.com/paperboatlab/paperboat-examples/actions/workflows/golden.yml/badge.svg?branch=dev)](https://github.com/paperboatlab/paperboat-examples/actions/workflows/golden.yml?query=branch%3Adev) |

## Licence

GNU General Public License version 3 (see [LICENSE](LICENSE)).
