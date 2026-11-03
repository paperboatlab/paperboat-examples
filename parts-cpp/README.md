# Parts backend (C++): classic image processing

Counts and sorts the bolts, nuts and washers in a photo. Not a simulation: the flow is
evaluated once (run style `Once`).

- **Station:** an Image station object (the photo, `file` set on the Station page).
- **Flow:** Image → Gray → Blur → Threshold (Otsu, inverted) → Close → Open (the toolkit's
  `opencv` package) → **Count parts** (this domain's own block, `domain/count.cpp`: sorts
  by elongation, roundness and holes) → Show on Station; counts → Graphs.

`data/parts.png` was provided by the user; check its licence before publishing the repo.

```sh
npm run backend:parts        # from the repo root: builds, serves ws://localhost:8770
```
