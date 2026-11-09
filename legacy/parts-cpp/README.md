# parts-cpp: classical image processing with OpenCV

A simple Paperboat backend on the C++ SDK. The domain is `descriptor.toml` (starter
station and flow, the `opencv` toolkit and `dashboard` packages) plus one block defined
in code (`Count parts`, in `domain/`).

Gray, blur, threshold, morphology, and Image view come from the `opencv` toolkit. The
photo is an Image station object; the parts are counted and sorted by area, and
evaluated once (run style `Once`).

`data/parts.png` was provided by the user; check its licence before publishing the repo.

The OpenCV requirement is declared in `toolkit_requirements.toml`. Without the opencv
toolkit the backend starts in a reduced form and the app offers to install it. Use
Paperboat's `scripts/run_backend.py` to get a confirmation prompt listing missing
toolkits before they are installed; declining leaves the backend and engine unchanged.

```sh
npm run backend:parts        # from the repo root: builds, serves ws://localhost:8770
```
