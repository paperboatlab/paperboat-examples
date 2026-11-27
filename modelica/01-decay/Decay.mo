model Decay "First-order decay: x falls to 1/e of its value every tau seconds"
  parameter Real tau(unit = "s") = 2 "Time constant";
  Real x(start = 1, fixed = true) "The decaying quantity";
equation
  der(x) = -x / tau;
  annotation(
    experiment(StopTime = 10, Interval = 1),
    Documentation(info = "<html><p>One state and one equation, <code>der(x) = -x/tau</code>: x(t) = exp(-t/tau).</p></html>"));
end Decay;
