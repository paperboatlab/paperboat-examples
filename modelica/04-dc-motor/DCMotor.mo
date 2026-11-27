model DCMotor "A DC motor on a 10 V step, driving a load through an elastic shaft"
  parameter Modelica.Units.SI.Resistance R = 1 "Armature resistance";
  parameter Modelica.Units.SI.Inductance L = 0.05 "Armature inductance";
  parameter Real k(unit = "N.m/A") = 0.5 "Motor constant";
  parameter Modelica.Units.SI.Inertia J_motor = 0.01 "Rotor inertia";
  parameter Modelica.Units.SI.Inertia J_load = 0.05 "Load inertia";
  parameter Modelica.Units.SI.RotationalSpringConstant c = 10 "Shaft stiffness";
  parameter Modelica.Units.SI.RotationalDampingConstant d = 1 "Shaft damping";
  Modelica.Electrical.Analog.Sources.StepVoltage source(V = 10, startTime = 0.1) annotation(
    Placement(transformation(origin = {-80, 0}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
  Modelica.Electrical.Analog.Basic.Resistor resistor(R = R) annotation(
    Placement(transformation(origin = {-50, 30}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Electrical.Analog.Basic.Inductor inductor(L = L, i(start = 0, fixed = true)) annotation(
    Placement(transformation(origin = {-20, 30}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Electrical.Analog.Basic.RotationalEMF emf(k = k) annotation(
    Placement(transformation(origin = {0, 0}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Electrical.Analog.Basic.Ground ground annotation(
    Placement(transformation(origin = {-80, -40}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Mechanics.Rotational.Components.Inertia rotor(J = J_motor) annotation(
    Placement(transformation(origin = {30, 0}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Mechanics.Rotational.Components.SpringDamper shaft(c = c, d = d) annotation(
    Placement(transformation(origin = {60, 0}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Mechanics.Rotational.Components.Inertia load(J = J_load, phi(start = 0, fixed = true), w(start = 0, fixed = true)) annotation(
    Placement(transformation(origin = {90, 0}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Mechanics.Rotational.Sensors.SpeedSensor speed annotation(
    Placement(transformation(origin = {90, -40}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
equation
  connect(source.p, resistor.p) annotation(Line(points = {{-80, 10}, {-80, 30}, {-60, 30}}, color = {0, 0, 255}));
  connect(resistor.n, inductor.p) annotation(Line(points = {{-40, 30}, {-30, 30}}, color = {0, 0, 255}));
  connect(inductor.n, emf.p) annotation(Line(points = {{-10, 30}, {0, 30}, {0, 10}}, color = {0, 0, 255}));
  connect(emf.n, source.n) annotation(Line(points = {{0, -10}, {0, -20}, {-80, -20}, {-80, -10}}, color = {0, 0, 255}));
  connect(ground.p, source.n) annotation(Line(points = {{-80, -30}, {-80, -10}}, color = {0, 0, 255}));
  connect(emf.flange, rotor.flange_a) annotation(Line(points = {{10, 0}, {20, 0}}));
  connect(rotor.flange_b, shaft.flange_a) annotation(Line(points = {{40, 0}, {50, 0}}));
  connect(shaft.flange_b, load.flange_a) annotation(Line(points = {{70, 0}, {80, 0}}));
  connect(load.flange_b, speed.flange) annotation(Line(points = {{100, 0}, {110, 0}, {110, -20}, {90, -20}, {90, -30}}));
  annotation(
    uses(Modelica(version = "4.1.0")),
    experiment(StopTime = 2, Interval = 0.1),
    Documentation(info = "<html><p>Electrical and rotational MSL parts in one model: the armature circuit's EMF turns the rotor; the shaft's spring-damper carries it to the load. The DC drive of Articula's station export, standalone.</p></html>"));
end DCMotor;
