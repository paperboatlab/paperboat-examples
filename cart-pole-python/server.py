from pathlib import Path
from domain.blocks import BLOCKS
from domain.state import CartPole
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="python-cart-pole",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        state=CartPole,
        blocks=BLOCKS,
        mode="clock",
        dt=0.01,
        duration=10.0,
        emit_every=4,
        port=8766,
    ))
