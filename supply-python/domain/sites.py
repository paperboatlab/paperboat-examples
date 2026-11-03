"""The supply network's sites: station objects linked to whoever supplies them, built on
the Station page as a graph. Goods flow down the links; the Flow page decides how much
each site orders (its linked block's `order` input, units per day).

A site's step: take what it ordered from its supplier (as much as the supplier has), put
it on the road for `lead_days`, receive what arrives, and (a store) sell to its customers.
"""

import math

import paperboat
from paperboat import Linked


class Site(paperboat.StationObject):
    """Something that holds stock and may be supplied by another site (`from`)."""

    links = ["from"]

    def __init__(self, props: dict) -> None:
        super().__init__(props)
        self.stock = float(props.get("stock0", 0.0))
        self.source: "Site | None" = None
        self.road: list[tuple[float, float]] = []  # (arrives at, units)
        self.t = 0.0

    def link(self, slot, other) -> None:
        if slot == "from":
            self.source = other

    def give(self, wanted: float) -> float:
        """Hand over up to `wanted` units from stock."""
        got = max(0.0, min(wanted, self.stock))
        self.stock -= got
        return got

    def receive(self, ctx, inputs) -> None:
        """Order from the source, and take in what has arrived."""
        self.t = ctx.t
        order = max(0.0, inputs.get("order", 0.0)) * ctx.dt
        if self.source is not None and order > 0:
            sent = self.source.give(order)
            if sent > 0:
                self.road.append((ctx.t + self.props["lead_days"], sent))
        arrived = sum(u for when, u in self.road if when <= ctx.t)
        self.road = [(when, u) for when, u in self.road if when > ctx.t]
        self.stock = min(self.stock + arrived, self.props.get("capacity", math.inf))

    def on_road(self) -> float:
        return sum(u for _, u in self.road)


class Supplier(Site):
    """A factory: makes up to `rate` units a day into its own stock."""

    type, label, role = "supplier", "Supplier", "body"
    links = []
    props = {"rate": 40.0, "stock0": 50.0}
    block = Linked(outputs=["stock"], kind="probe")

    def read(self) -> dict:
        return {"stock": self.stock}

    def step(self, ctx, inputs) -> None:
        self.stock += self.props["rate"] * ctx.dt


class Warehouse(Site):
    """Holds stock between a supplier and the stores."""

    type, label, role = "warehouse", "Warehouse", "body"
    props = {"stock0": 120.0, "capacity": 400.0, "lead_days": 2.0}
    block = Linked(inputs=["order"], outputs=["stock", "on_road"], kind="source")

    def read(self) -> dict:
        return {"stock": self.stock, "on_road": self.on_road()}

    def step(self, ctx, inputs) -> None:
        self.receive(ctx, inputs)


class Store(Site):
    """Sells to customers: `demand` units a day, busier at weekends (±`swing`). What it
    can't sell is lost."""

    type, label, role = "store", "Store", "body"
    props = {"stock0": 40.0, "capacity": 120.0, "lead_days": 1.0, "demand": 12.0, "swing": 0.4}
    block = Linked(inputs=["order"], outputs=["stock", "lost", "sold"], kind="source")

    def __init__(self, props: dict) -> None:
        super().__init__(props)
        self.lost = self.sold = 0.0

    def read(self) -> dict:
        return {"stock": self.stock, "lost": self.lost, "sold": self.sold}

    def step(self, ctx, inputs) -> None:
        self.receive(ctx, inputs)
        p = self.props
        wanted = p["demand"] * (1 + p["swing"] * math.sin(2 * math.pi * ctx.t / 7)) * ctx.dt
        sold = self.give(wanted)
        self.sold += sold
        self.lost += wanted - sold


SITES = [Supplier, Warehouse, Store]
