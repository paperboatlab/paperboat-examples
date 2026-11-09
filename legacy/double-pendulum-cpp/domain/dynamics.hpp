#pragma once

// The double pendulum on a cart: its equations, its energy, and the two pieces of control
// math the example needs (a recursive least-squares estimate of the unknown payload, and an
// LQR balance gain). Pure C++ with no Paperboat types, so the math reads like the paper.

#include <array>
#include <string>

namespace double_pendulum {

constexpr double kG = 9.81;  // m/s²

// A physical model: the cart and the two links, plus the payload at the end of link 2.
// The controllers know every field except `payload`: that is what the first story estimates.
struct Params {
  double cart_mass = 1.0;      // kg
  double link1_mass = 0.3;     // kg, a uniform rod
  double link1_length = 0.5;   // m
  double link2_mass = 0.2;     // kg, a uniform rod
  double link2_length = 0.5;   // m
  double payload = 0.25;       // kg, at the tip of link 2 (unknown to the controllers)
  double cart_damping = 0.1;   // N·s/m
  double joint1_damping = 0.002;  // N·m·s/rad
  double joint2_damping = 0.002;  // N·m·s/rad
};

// The lumped constants of the equations of motion, from Params (as in model.py).
struct Consts {
  double total;  // cart + links + payload
  double a1, a2, a3;
  double j1, j2;
};

using Vec3 = std::array<double, 3>;
using State6 = std::array<double, 6>;  // x, θ1, θ2, ẋ, ω1, ω2

Consts constants(const Params& p);
std::array<Vec3, 3> mass_matrix(const Params& p, const Vec3& q);

// x' = f(x, force): the state derivative with a horizontal force on the cart.
State6 derivatives(const Params& p, const State6& s, double force);

// The total energy of the links alone (cart motion excluded), and the energy at rest upright.
double energy_links(const Params& p, const State6& s);
double energy_ref(const Params& p);

double wrap(double angle);              // into [−π, π)
State6 wrap_angles(const State6& s);    // angles only, for an error vector

// One classic RK4 step of the plant, the same integrator the model uses on the clock.
State6 rk4(const Params& p, const State6& s, double force, double dt);

// The energy-shaping swing-up force: drive the links' energy to the upright value and keep
// the cart near home. `u` is the cart acceleration it asks for; the force is what the cart
// needs to deliver it under the current configuration.
double swing_force(const Params& p, const State6& s, double k_energy, double u_max, double k_x,
                   double k_v, double max_force, bool kick);

// Whether a balance gain K would bring this state to rest at upright within `horizon` s,
// under a one-step force delay and the force limit. The story uses it to decide the catch.
bool catch_ok(const Params& p, const State6& start, const std::array<double, 6>& gain, double max_force,
              double horizon, double dt);

// The discrete LQR gain at upright for a model with payload `payload`, with
// Q = diag(100, 10, 10, 10, 10, 10) and R = 1. Solves the DARE by iteration.
std::array<double, 6> lqr_gain(const Params& nominal, double payload, int* iterations = nullptr);

}  // namespace double_pendulum
