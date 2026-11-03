"""Example Paperboat backend: a chain of masses, springs and dampers (Python).

The structure is built on the Station page, in its graph view: each element is a station
object, wired to its neighbours through link slots (a spring's `a` and `b`). The Flow page
holds the test logic: what pushes on the structure, what is measured and checked. The
elements are in domain/objects.py; everything else is the C++ engine, through the Python
bindings (python/).
"""

from pathlib import Path

from domain.objects import OBJECTS
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="python-chain",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        objects=OBJECTS,
        mode="clock",
        dt=0.005,
        duration=8.0,
        emit_every=8,
        port=8771,
    ))
