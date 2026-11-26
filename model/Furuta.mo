package Furuta "Bench 3 rotary pendulum (Furuta pendulum): the model, and the rig as the lab has it"

  model Pendulum "Arm and pendulum: the Lagrange equations, the motor's torque and the friction"
    import Modelica.Units.SI;
    import Modelica.Constants.g_n;
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
    Modelica.Blocks.Interfaces.RealInput u(unit = "V") "Motor voltage";
    Modelica.Blocks.Interfaces.RealOutput theta(unit = "rad") "Arm angle";
    Modelica.Blocks.Interfaces.RealOutput alpha(unit = "rad") "Pendulum angle from upright";
    SI.AngularVelocity w(start = 0, fixed = true) "Arm rate";
    SI.AngularVelocity v(start = 0, fixed = true) "Pendulum rate";
    SI.Torque tau "Motor torque less the arm's friction";
  protected
    final parameter SI.MomentOfInertia Jrh = Jr + mp * Lr ^ 2 "The arm with the pendulum's mass at its tip";
    final parameter SI.MomentOfInertia Jph = Jp + mp * lp ^ 2 "The pendulum about its pivot";
    final parameter Real h(unit = "kg.m2") = mp * Lr * lp;
  initial equation
    theta = 0;
    alpha = alpha0;
  equation
    der(theta) = w;
    der(alpha) = v;
    tau = km * (u - km * w) / Rm - Br * w - fc * w / sqrt(w ^ 2 + 1e-4);
    (Jrh + Jph * sin(alpha) ^ 2) * der(w) + h * cos(alpha) * der(v) = tau - 2 * Jph * sin(alpha) * cos(alpha) * w * v + h * sin(alpha) * v ^ 2;
    h * cos(alpha) * der(w) + Jph * der(v) = Jph * sin(alpha) * cos(alpha) * w ^ 2 + mp * g_n * lp * sin(alpha) - Bp * v;
    annotation(Documentation(info = "<html><p>The arm turns about a vertical axis (theta); the pendulum swings in the plane across the arm's tip (alpha, 0 upright). The same equations as model/furuta.jl.</p></html>"));
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
