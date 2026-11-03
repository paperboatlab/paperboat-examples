"""Example Paperboat backend: a supply network (Python). Not a simulation of physics, not
a game: stock moving between sites, and an ordering policy to try.

The network is built on the Station page as a graph: sites (domain/sites.py) linked to
whoever supplies them. The Flow page holds the policy: how much each site orders, from
what it sees. No toolkit of its own: the policy is toolkit blocks, and its Reorder rule is
a TOML definition on the signal package's generator (descriptor.toml).
"""

from pathlib import Path

from domain.sites import SITES
import paperboat

if __name__ == "__main__":
    paperboat.serve(paperboat.Backend(
        engine="python-supply",
        descriptor=Path(__file__).with_name("descriptor.toml"),
        objects=SITES,
        mode="clock",
        dt=0.05,          # days
        duration=28.0,    # four weeks
        emit_every=4,
        port=8772,
    ))
