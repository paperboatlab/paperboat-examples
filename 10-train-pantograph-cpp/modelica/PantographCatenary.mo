model PantographCatenary
  "Reference acausal model of the pantograph head on a compliant contact wire.

   This is the Squero Studio OM schematic that accompanies the C++ tutorial. The same
   equations are implemented in domain/pantograph.cpp: a head mass on a suspension
   spring/damper, a contact spring with the wire, aerodynamic uplift proportional to v²,
   and an active pneumatic force. Open it in Squero Studio OM to inspect the connections.
  "
  parameter Real m(unit = "kg") = 12 "Head mass";
  parameter Real k_s(unit = "N/m") = 400 "Suspension stiffness";
  parameter Real c_s(unit = "N.s/m") = 260 "Suspension damping";
  parameter Real k_w(unit = "N/m") = 500 "Contact-wire stiffness";
  parameter Real c_w(unit = "N.s/m") = 30 "Contact-wire damping";
  parameter Real v_max(unit = "m/s") = 320 / 3.6 "Top speed";
  parameter Real aero(unit = "kg/m") = 0.012 "Aerodynamic uplift coefficient, 0.5*rho*Cl*A";

  Real t(unit = "s") "Run time";
  Real x(unit = "m") "Distance travelled";
  Real v(unit = "m/s") "Train speed";
  Real z(unit = "m") "Contact-strip height";
  Real vz(unit = "m/s") "Contact-strip vertical speed";
  Real z_w(unit = "m") "Contact-wire height";
  Real F_c(unit = "N") "Contact force";
  Real F_aero(unit = "N") "Aerodynamic uplift";
  Real F_act(unit = "N") "Pneumatic actuator force";

equation
  der(t) = 1;
  v = min(v_max, v_max * t / 25);
  der(x) = v;
  z_w = 5.2 + 0.010 * sin(2 * 3.141592653589793 * x / 18) + 0.004 * sin(2 * 3.141592653589793 * x / 6.2);
  F_c = max(0, k_w * (z - z_w) + c_w * (vz - der(z_w)));
  F_aero = 0.5 * 1.2 * v * v * 0.020;
  der(z) = vz;
  m * der(vz) = k_s * (5.15 - z) - c_s * vz + F_act + F_aero - F_c;
end PantographCatenary;
