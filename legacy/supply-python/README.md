# Supply network backend (Python)

Stock moving between sites, and an ordering policy to try, on the
[Paperboat protocol](../../../protocol/README.md). No physics, no game, and no toolkit of
its own.

- **The Station page is a graph** (`[station] view = "graph"`): a factory → a warehouse →
  two stores. Each site is a station object linked to whoever supplies it (its `from`
  slot): drag from a site's right handle onto another's `from` to re-route. Set stock,
  capacity, lead time and demand on the Station panel.
- **The Flow page is the policy:** each site's linked block takes an `order` (units a
  day) and reports its `stock`. The starter wires each stock into a **Reorder** rule: order
  `rate` a day while the stock is under `point`. Store-north's point (8) is too low for a
  one-day delivery, so it runs out and loses about 29 units in four weeks (Dashboard:
  lost sales). Raise it and run again.
- **Reorder is a definition, not code:** in `descriptor.toml` it `use`s the signal
  package's C++ parent `signal/generator`, adds `point` and `rate`, and sets
  `f = "t < point ? rate : 0"` (its input `t` is whatever is wired in: here, a stock).

Each step a site orders from its supplier (as much as the supplier has), the goods spend
`lead_days` on the road, and a store sells `demand` a day, busier at weekends; what it
can't sell is lost.

## Layout

```
descriptor.toml   imports, the Reorder definition, the starter network (a graph) and policy
domain/
  sites.py        Supplier, Warehouse, Store: station objects linked by `from`
server.py         fills a paperboat.Backend and serves it: no logic
expected.json     what the starter run must produce (npm run golden)
```
