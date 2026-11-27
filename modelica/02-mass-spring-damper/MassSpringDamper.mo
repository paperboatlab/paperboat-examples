model MassSpringDamper "A mass on a spring and a damper, released 10 cm from rest"
  parameter Real m(unit = "kg") = 1 "Mass";
  parameter Real k(unit = "N/m") = 10 "Spring stiffness";
  parameter Real d(unit = "N.s/m") = 0.5 "Damping";
  Real x(unit = "m", start = 0.1, fixed = true) "Position";
  Real v(unit = "m/s", start = 0, fixed = true) "Velocity";
equation
  der(x) = v;
  m * der(v) = -k * x - d * v;
  annotation(
    experiment(StopTime = 10, Interval = 0.5),
    Documentation(info = "<html><p>Second order as two first-order equations: an underdamped oscillation.</p></html>"));
end MassSpringDamper;
