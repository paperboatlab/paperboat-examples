model SpeedControl "A PI controller holds a loaded shaft at a speed set point, its torque limited"
  parameter Modelica.Units.SI.AngularVelocity w_ref = 10 "Speed set point";
  Modelica.Blocks.Sources.Step setpoint(height = w_ref, startTime = 0.5) annotation(
    Placement(transformation(origin = {-80, 0}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Blocks.Continuous.LimPID pi(controllerType = Modelica.Blocks.Types.SimpleController.PI, k = 2, Ti = 0.2, yMax = 5, initType = Modelica.Blocks.Types.Init.InitialState) annotation(
    Placement(transformation(origin = {-40, 0}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Mechanics.Rotational.Sources.Torque torque annotation(
    Placement(transformation(origin = {0, 0}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Mechanics.Rotational.Components.Inertia inertia(J = 0.5, phi(start = 0, fixed = true), w(start = 0, fixed = true)) annotation(
    Placement(transformation(origin = {40, 0}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Mechanics.Rotational.Components.Damper friction(d = 0.2) annotation(
    Placement(transformation(origin = {70, -30}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
  Modelica.Mechanics.Rotational.Components.Fixed fixed annotation(
    Placement(transformation(origin = {70, -60}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Mechanics.Rotational.Sensors.SpeedSensor speed annotation(
    Placement(transformation(origin = {40, -40}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
equation
  connect(setpoint.y, pi.u_s) annotation(Line(points = {{-69, 0}, {-52, 0}}, color = {0, 0, 127}));
  connect(pi.y, torque.tau) annotation(Line(points = {{-29, 0}, {-12, 0}}, color = {0, 0, 127}));
  connect(torque.flange, inertia.flange_a) annotation(Line(points = {{10, 0}, {30, 0}}));
  connect(inertia.flange_b, friction.flange_a) annotation(Line(points = {{50, 0}, {70, 0}, {70, -20}}));
  connect(friction.flange_b, fixed.flange) annotation(Line(points = {{70, -40}, {70, -60}}));
  connect(inertia.flange_b, speed.flange) annotation(Line(points = {{50, 0}, {50, -20}, {40, -20}, {40, -30}}));
  connect(speed.w, pi.u_m) annotation(Line(points = {{40, -51}, {40, -70}, {-40, -70}, {-40, -12}}, color = {0, 0, 127}));
  annotation(
    uses(Modelica(version = "4.1.0")),
    experiment(StopTime = 5, Interval = 0.25),
    Documentation(info = "<html><p>A feedback loop from MSL blocks: the set point steps at 0.5 s, the PI's torque saturates at 5 N.m while the shaft spins up, then settles at the set point (anti-windup).</p></html>"));
end SpeedControl;
