within Basics;
model Control
  "The block and the function together."

  Gain gain(k = 2);
  parameter Real rate(unit = "K/s") = 0.5 "Heating rate";
  Real T(unit = "K", start = 300, fixed = true) "Temperature";
  Real p "Saturation pressure";

equation
  der(T) = rate;
  gain.u = T;
  p = Saturation(T);

  annotation(experiment(StopTime = 10, Interval = 1), Documentation(info = "<html><p>A model that instantiates a block and calls a function.</p></html>"));
end Control;
