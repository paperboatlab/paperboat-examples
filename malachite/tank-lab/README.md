# Tank Lab

A small [Paperboat Malachite](https://github.com/paperboatlab/malachite) hub: the lab notebook of a
tank whose level a pump holds. Its notes embed a picture, a video and a PDF, link each other (so
each has backlinks), and carry tags, every kind of callout, tables, a diagram and code cells that
run in Python and Julia sessions. Start at [`start-here.md`](start-here.md). A copy of Malachite's
own `examples/tank-lab`, with its broken link fixed (malachite#66).

**Docs:** <https://paperboatlab.org/apps/malachite/>

## Run

```sh
paperboat app open malachite malachite/tank-lab
```

## Check

```sh
python3 golden.py malachite/tank-lab
```

- `index`: Malachite's index over the hub (links, backlinks, tags, cells, callout kinds) against
  [`index.json`](index.json); `"unresolved": []` says every link and embed resolves.
- `cells`: pending on malachite#67, a headless run of the cells. [`cells.json`](cells.json) holds
  the outputs each cell gives, recorded by running its code with `python3` and `julia` in the
  note's folder; a rich result keeps its richest type only.

The diagram is a `mermaid` fence, for malachite#45 (the quick diagram tool) to draw; the tables
are plain GFM, for malachite#64 (the table tool) to edit.
