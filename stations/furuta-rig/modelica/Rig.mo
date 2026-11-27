package Furuta "Bench 3 rotary pendulum (Furuta pendulum): the model, and the rig as the lab has it"

  model Pendulum "Arm and pendulum in MultiBody: two revolute joints, a DC motor, the friction"
    import Modelica.Units.SI;
    import Modelica.Mechanics.MultiBody;
    import Modelica.Mechanics.Rotational;
    import Modelica.Electrical.Analog;
    parameter SI.Length Lr = 0.100 "Arm, motor axis to pendulum pivot";
    parameter SI.MomentOfInertia Jr = 3.7e-4 "Arm and hub about the motor axis";
    parameter SI.Mass mp = 0.030 "Pendulum";
    parameter SI.Length Lp = 0.150 "Pendulum rod's length";
    parameter SI.Length lp = 0.075 "Pendulum pivot to its centre of mass";
    parameter SI.MomentOfInertia Jp = mp * Lp ^ 2 / 12 "Pendulum about its centre of mass (a rod)";
    parameter SI.RotationalDampingConstant Br = 8.0e-4 "Arm viscous friction";
    parameter SI.RotationalDampingConstant Bp = 3.0e-5 "Pendulum viscous friction";
    parameter SI.Resistance Rm = 7.5 "Motor armature resistance";
    parameter Real km(unit = "N.m/A") = 0.045 "Motor torque and back-emf constant";
    parameter SI.Torque fc = 0 "Arm Coulomb friction (smoothed at 0.01 rad/s)";
    parameter SI.Angle alpha0 = 0.035 "Pendulum's start, from upright";
    Modelica.Blocks.Interfaces.RealInput u(unit = "V") "Motor voltage"
      annotation(Placement(transformation(extent = {{-120, -10}, {-100, 10}})));
    Modelica.Blocks.Interfaces.RealOutput theta(unit = "rad") "Arm angle"
      annotation(Placement(transformation(extent = {{100, 30}, {120, 50}})));
    Modelica.Blocks.Interfaces.RealOutput alpha(unit = "rad") "Pendulum angle from upright"
      annotation(Placement(transformation(extent = {{100, -50}, {120, -30}})));
    inner MultiBody.World world(g = 9.81) "Gravity along -y: y is up (g as furuta.jl has it)"
      annotation(Placement(transformation(extent = {{-80, -80}, {-60, -60}})));
    MultiBody.Joints.Revolute arm(n = {0, 1, 0}, useAxisFlange = true,
      phi(fixed = true, start = 0), w(fixed = true, start = 0)) "Motor axis, vertical"
      annotation(Placement(transformation(extent = {{-40, -80}, {-20, -60}})));
    MultiBody.Parts.FixedTranslation rod(r = {Lr, 0, 0}) "The arm, along x at theta = 0"
      annotation(Placement(transformation(extent = {{0, -80}, {20, -60}})));
    MultiBody.Joints.Revolute pivot(n = {-1, 0, 0}, useAxisFlange = true,
      phi(fixed = true, start = alpha0), w(fixed = true, start = 0)) "Pendulum pivot, along the arm"
      annotation(Placement(transformation(extent = {{40, -80}, {60, -60}})));
    MultiBody.Parts.Body pendulum(m = mp, r_CM = {0, lp, 0}, I_11 = Jp, I_22 = 0, I_33 = Jp)
      "The rod, upright at alpha = 0"
      annotation(Placement(transformation(extent = {{70, -80}, {90, -60}})));
    Rotational.Components.Inertia hub(J = Jr) "Arm and hub"
      annotation(Placement(transformation(extent = {{-40, -10}, {-20, 10}})));
    Rotational.Components.Damper armFriction(d = Br)
      annotation(Placement(transformation(extent = {{-40, -40}, {-20, -20}})));
    Rotational.Sources.Torque coulomb "Arm Coulomb friction"
      annotation(Placement(transformation(extent = {{0, -10}, {-20, 10}})));
    Rotational.Components.Damper pivotFriction(d = Bp)
      annotation(Placement(transformation(extent = {{40, -40}, {60, -20}})));
    Analog.Sources.SignalVoltage supply "The amplifier's output"
      annotation(Placement(transformation(origin = {-90, 30}, extent = {{-10, -10}, {10, 10}}, rotation = 270)));
    Analog.Basic.Resistor armature(R = Rm)
      annotation(Placement(transformation(extent = {{-80, 40}, {-60, 60}})));
    Analog.Basic.RotationalEMF motor(k = km)
      annotation(Placement(transformation(extent = {{-60, -10}, {-40, 10}})));
    Analog.Basic.Ground ground
      annotation(Placement(transformation(extent = {{-100, -10}, {-80, 10}})));
  equation
    coulomb.tau = -fc * arm.w / sqrt(arm.w ^ 2 + 1e-4);
    theta = arm.phi;
    alpha = pivot.phi;
    connect(u, supply.v);
    connect(supply.p, armature.p);
    connect(armature.n, motor.p);
    connect(motor.n, supply.n);
    connect(supply.n, ground.p);
    connect(motor.flange, hub.flange_a);
    connect(hub.flange_b, arm.axis);
    connect(coulomb.flange, arm.axis);
    connect(armFriction.flange_a, arm.support);
    connect(armFriction.flange_b, arm.axis);
    connect(world.frame_b, arm.frame_a);
    connect(arm.frame_b, rod.frame_a);
    connect(rod.frame_b, pivot.frame_a);
    connect(pivot.frame_b, pendulum.frame_a);
    connect(pivotFriction.flange_a, pivot.support);
    connect(pivotFriction.flange_b, pivot.axis);
    annotation(Documentation(info = "<html><p>The arm turns about a vertical axis (theta); the pendulum swings in the plane across the arm's tip (alpha, 0 upright). Built from MultiBody, Rotational and Analog components; model/furuta.jl writes the same physics as Lagrange's equations.</p></html>"));
  end Pendulum;

  model Rig "The bench: the true parameters, the amplifier's dead band and saturation"
    import Modelica.Units.SI;
    parameter SI.Voltage deadband = 0.15 "Amplifier's dead band around 0";
    parameter SI.Voltage umax = 10 "Amplifier's saturation";
    parameter SI.Angle alpha0 = 0.035 "Pendulum's start, from upright (pi: hanging)";
    Pendulum pendulum(mp = 0.034, lp = 0.081, Br = 1.6e-3, Bp = 4.5e-5, km = 0.040, fc = 1.5e-3, alpha0 = alpha0) "The truth, which the study has to find";
    Modelica.Blocks.Interfaces.RealInput cmd(unit = "V") "Voltage command to the amplifier";
    Modelica.Blocks.Interfaces.RealOutput theta(unit = "rad") "Arm angle";
    Modelica.Blocks.Interfaces.RealOutput alpha(unit = "rad") "Pendulum angle from upright";
  equation
    pendulum.u = max(-umax, min(umax, if abs(cmd) <= deadband then 0 else cmd - sign(cmd) * deadband));
    theta = pendulum.theta;
    alpha = pendulum.alpha;
    annotation(Documentation(info = "<html><p>What tools/rig.toml simulates, less the encoder counts, the 2 ms delay and the end stops.</p></html>"));
  end Rig;

  annotation(uses(Modelica(version = "4.1.0")));
end Furuta;
