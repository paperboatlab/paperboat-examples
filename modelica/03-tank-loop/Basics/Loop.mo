within Basics;
model Loop
  "A source, a pump and a tank, wired through the connector."

  Source source;
  Pump pump(medium = Medium());
  Tank tank;

equation
  connect(source.port, pump.port_a);
  connect(pump.port_b, tank.port);

  annotation(
    experiment(StopTime = 2000, Interval = 200),
    Icon(graphics = {
      Rectangle(extent = {{-100, -70}, {100, 70}}, lineColor = {0, 0, 0}, fillColor = {242, 242, 239}, fillPattern = FillPattern.Solid),
      Text(extent = {{-90, 30}, {90, -30}}, lineColor = {0, 0, 0}, textString = "Loop")}),
    Documentation(info = "<html><p>The top model: two submodels (<code>Pump</code>, <code>Tank</code>) and a source, connected through <code>FluidPort</code>: the level climbs until the tank's head stalls the pump.</p></html>"));
end Loop;
