#include "dynamics.hpp"

#include <algorithm>
#include <cmath>
#include <numbers>

namespace double_pendulum {
namespace {

using Mat3 = std::array<Vec3, 3>;

Vec3 solve3(Mat3 a, Vec3 b) {
  // Gaussian elimination with partial pivoting; the matrices here are 3×3 and well behaved.
  for (int col = 0; col < 3; ++col) {
    int pivot = col;
    for (int row = col + 1; row < 3; ++row)
      if (std::abs(a[row][col]) > std::abs(a[pivot][col])) pivot = row;
    std::swap(a[col], a[pivot]);
    std::swap(b[col], b[pivot]);
    for (int row = col + 1; row < 3; ++row) {
      const double f = a[row][col] / a[col][col];
      for (int k = col; k < 3; ++k) a[row][k] -= f * a[col][k];
      b[row] -= f * b[col];
    }
  }
  Vec3 x{};
  for (int row = 2; row >= 0; --row) {
    double sum = b[row];
    for (int k = row + 1; k < 3; ++k) sum -= a[row][k] * x[k];
    x[row] = sum / a[row][row];
  }
  return x;
}

Vec3 rhs_terms(const Params& p, const Vec3& q, const Vec3& dq) {
  const Consts c = constants(p);
  const double x = q[0], t1 = q[1], t2 = q[2];
  const double dx = dq[0], w1 = dq[1], w2 = dq[2];
  (void)x;
  const Vec3 h = {-c.a1 * std::sin(t1) * w1 * w1 - c.a2 * std::sin(t2) * w2 * w2,
                  c.a3 * std::sin(t1 - t2) * w2 * w2,
                  -c.a3 * std::sin(t1 - t2) * w1 * w1};
  const Vec3 gravity = {0.0, -kG * c.a1 * std::sin(t1), -kG * c.a2 * std::sin(t2)};
  const Vec3 damping = {p.cart_damping * dx, p.joint1_damping * w1 - p.joint2_damping * (w2 - w1),
                        p.joint2_damping * (w2 - w1)};
  return {h[0] + gravity[0] + damping[0], h[1] + gravity[1] + damping[1], h[2] + gravity[2] + damping[2]};
}

}  // namespace

Consts constants(const Params& p) {
  const double l1 = p.link1_length / 2;
  const double link2 = p.link2_mass + p.payload;
  const double c2 = (p.link2_mass * p.link2_length / 2 + p.payload * p.link2_length) / link2;
  Consts c{};
  c.total = p.cart_mass + p.link1_mass + link2;
  c.a1 = p.link1_mass * l1 + link2 * p.link1_length;
  c.a2 = link2 * c2;
  c.a3 = link2 * p.link1_length * c2;
  c.j1 = p.link1_mass * p.link1_length * p.link1_length / 3 + link2 * p.link1_length * p.link1_length;
  c.j2 = p.link2_mass * p.link2_length * p.link2_length / 3 + p.payload * p.link2_length * p.link2_length;
  return c;
}

std::array<Vec3, 3> mass_matrix(const Params& p, const Vec3& q) {
  const Consts c = constants(p);
  const double t1 = q[1], t2 = q[2];
  return {{{c.total, c.a1 * std::cos(t1), c.a2 * std::cos(t2)},
           {c.a1 * std::cos(t1), c.j1, c.a3 * std::cos(t1 - t2)},
           {c.a2 * std::cos(t2), c.a3 * std::cos(t1 - t2), c.j2}}};
}

State6 derivatives(const Params& p, const State6& s, double force) {
  const Vec3 q = {s[0], s[1], s[2]};
  const Vec3 dq = {s[3], s[4], s[5]};
  const Vec3 rhs = rhs_terms(p, q, dq);
  const Vec3 ddq = solve3(mass_matrix(p, q), {force - rhs[0], -rhs[1], -rhs[2]});
  return {dq[0], dq[1], dq[2], ddq[0], ddq[1], ddq[2]};
}

double energy_links(const Params& p, const State6& s) {
  const Consts c = constants(p);
  const auto m = mass_matrix(p, {s[0], s[1], s[2]});
  const double w1 = s[4], w2 = s[5];
  const double kinetic = 0.5 * (m[1][1] * w1 * w1 + 2 * m[1][2] * w1 * w2 + m[2][2] * w2 * w2);
  return kinetic + kG * (c.a1 * std::cos(s[1]) + c.a2 * std::cos(s[2]));
}

double energy_ref(const Params& p) {
  const Consts c = constants(p);
  return kG * (c.a1 + c.a2);
}

double wrap(double angle) {
  return std::remainder(angle, 2 * std::numbers::pi);
}

State6 wrap_angles(const State6& s) {
  return {s[0], wrap(s[1]), wrap(s[2]), s[3], s[4], s[5]};
}

State6 rk4(const Params& p, const State6& s, double force, double dt) {
  const auto add = [dt](const State6& a, const State6& b, double scale) {
    State6 out{};
    for (std::size_t i = 0; i < out.size(); ++i) out[i] = a[i] + scale * dt * b[i];
    return out;
  };
  const State6 k1 = derivatives(p, s, force);
  const State6 k2 = derivatives(p, add(s, k1, 0.5), force);
  const State6 k3 = derivatives(p, add(s, k2, 0.5), force);
  const State6 k4 = derivatives(p, add(s, k3, 1.0), force);
  State6 out{};
  for (std::size_t i = 0; i < out.size(); ++i) out[i] = s[i] + dt / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
  return out;
}

double swing_force(const Params& p, const State6& s, double k_energy, double u_max, double k_x, double k_v,
                   double max_force, bool kick) {
  const Consts c = constants(p);
  const double er = energy_ref(p);
  const double e = energy_links(p, s);
  const double w = c.a1 * std::cos(s[1]) * s[4] + c.a2 * std::cos(s[2]) * s[5];
  double u = k_energy * (e - er) * w - k_x * s[0] - k_v * s[3];
  // At a link's turning point w is ~0 and the energy control has no authority; a small
  // nudge keeps the swing growing from rest.
  if (kick && std::abs(w) < 1e-3 && std::abs(e - er) > 0.5) u += 1.0;
  u = std::clamp(u, -u_max, u_max);
  // Convert the desired cart acceleration to the force that produces it now.
  const Mat3 m = mass_matrix(p, {s[0], s[1], s[2]});
  const Vec3 rhs = rhs_terms(p, {s[0], s[1], s[2]}, {s[3], s[4], s[5]});
  const double a = solve3(m, {-rhs[0], -rhs[1], -rhs[2]})[0];
  const double b = solve3(m, {1, 0, 0})[0];
  return std::clamp((u - a) / b, -max_force, max_force);
}

bool catch_ok(const Params& p, const State6& start, const std::array<double, 6>& gain, double max_force,
              double horizon, double dt) {
  const auto force_at = [&](const State6& z) {
    const State6 e = wrap_angles(z);
    double u = 0;
    for (std::size_t i = 0; i < gain.size(); ++i) u += gain[i] * e[i];
    return std::clamp(-u, -max_force, max_force);
  };
  State6 s = start;
  double previous = force_at(s);  // the engine applies a story's force one clock step later
  const int steps = static_cast<int>(std::lround(horizon / dt));
  for (int i = 0; i < steps; ++i) {
    const double force = force_at(s);
    s = rk4(p, s, previous, dt);
    previous = force;
    if (std::abs(s[0]) > 3.0) return false;  // it ran off the rail: not a catch
  }
  const State6 e = wrap_angles(s);
  return std::max(std::abs(e[1]), std::abs(e[2])) < 0.05 && std::abs(e[0]) < 2.0;
}

std::array<double, 6> lqr_gain(const Params& nominal, double payload, int* iterations) {
  Params p = nominal;
  p.payload = payload;

  constexpr double dt = 0.01;
  constexpr double eps = 1e-6;
  constexpr int n = 6;
  using Mat = std::array<std::array<double, n>, n>;
  Mat a{};
  std::array<double, n> b{};
  const State6 zero{};
  for (int col = 0; col < n; ++col) {
    State6 plus{}, minus{};
    plus[col] = eps;
    minus[col] = -eps;
    const State6 fp = derivatives(p, plus, 0);
    const State6 fm = derivatives(p, minus, 0);
    for (int row = 0; row < n; ++row) a[row][col] = (fp[row] - fm[row]) / (2 * eps);
  }
  const State6 bp = derivatives(p, zero, eps);
  const State6 bm = derivatives(p, zero, -eps);
  for (int row = 0; row < n; ++row) b[row] = (bp[row] - bm[row]) / (2 * eps);

  // Discretise the linear system with the same RK4 series the prototype uses.
  Mat ad{};
  for (int i = 0; i < n; ++i) ad[i][i] = 1.0;
  Mat power = a;  // A^k
  double coeff = dt;
  for (int k = 1; k <= 4; ++k) {
    for (int i = 0; i < n; ++i)
      for (int j = 0; j < n; ++j) ad[i][j] += coeff * power[i][j];
    Mat next{};
    for (int i = 0; i < n; ++i)
      for (int j = 0; j < n; ++j)
        for (int l = 0; l < n; ++l) next[i][j] += a[i][l] * power[l][j];
    power = next;
    coeff *= dt / (k + 1);
  }
  std::array<double, n> bd{};
  std::array<double, n> v = b;  // A^(k-1) B
  coeff = dt;
  for (int k = 1; k <= 4; ++k) {
    for (int i = 0; i < n; ++i) bd[i] += coeff * v[i];
    std::array<double, n> next{};
    for (int i = 0; i < n; ++i)
      for (int j = 0; j < n; ++j) next[i] += a[i][j] * v[j];
    v = next;
    coeff *= dt / (k + 1);
  }

  const std::array<double, n> q = {100, 10, 10, 10, 10, 10};
  constexpr double r = 1.0;
  Mat P{};
  for (int i = 0; i < n; ++i) P[i][i] = q[i];
  int it = 0;
  // Iterate the DARE in its feedback form, P ← Q + Adᵀ P (Ad − Bd K) with
  // K = (R + Bdᵀ P Bd)⁻¹ Bdᵀ P Ad. The algebraically equivalent expansion
  // P ← Q + Adᵀ P Ad − Adᵀ P Bd (R + Bdᵀ P Bd)⁻¹ Bdᵀ P Ad loses the positive-definite
  // structure to rounding once P is large and then diverges; this form stays stable.
  Mat pn{};
  for (; it < 20000; ++it) {
    // pb = P·Bd, S = R + Bdᵀ·pb.
    std::array<double, n> pb{};
    for (int i = 0; i < n; ++i)
      for (int k = 0; k < n; ++k) pb[i] += P[i][k] * bd[k];
    double s = r;
    for (int i = 0; i < n; ++i) s += bd[i] * pb[i];
    // K = Bdᵀ P Ad / S (a row), as a gain vector.
    std::array<double, n> gain{};
    for (int j = 0; j < n; ++j) {
      double v = 0;
      for (int k = 0; k < n; ++k)
        for (int l = 0; l < n; ++l) v += bd[k] * P[k][l] * ad[l][j];
      gain[j] = v / s;
    }
    // M = Ad − Bd K, Pn = Q + Adᵀ P M.
    Mat m{};
    for (int i = 0; i < n; ++i)
      for (int j = 0; j < n; ++j) m[i][j] = ad[i][j] - bd[i] * gain[j];
    Mat pm{};
    for (int i = 0; i < n; ++i)
      for (int j = 0; j < n; ++j)
        for (int k = 0; k < n; ++k) pm[i][j] += P[i][k] * m[k][j];
    double scale = 0;
    pn = {};
    for (int i = 0; i < n; ++i)
      for (int j = 0; j < n; ++j) {
        for (int k = 0; k < n; ++k) pn[i][j] += ad[k][i] * pm[k][j];
        pn[i][j] += i == j ? q[i] : 0.0;
        scale = std::max(scale, std::abs(pn[i][j]));
      }
    double change = 0;
    for (int i = 0; i < n; ++i)
      for (int j = 0; j < n; ++j) change = std::max(change, std::abs(pn[i][j] - P[i][j]));
    P = pn;
    if (change < 1e-9 * scale) {
      ++it;
      break;
    }
  }
  if (iterations) *iterations = it;
  // The gain at the converged P.
  std::array<double, n> gain{};
  std::array<double, n> pb{};
  for (int i = 0; i < n; ++i)
    for (int k = 0; k < n; ++k) pb[i] += P[i][k] * bd[k];
  double s = r;
  for (int i = 0; i < n; ++i) s += bd[i] * pb[i];
  for (int j = 0; j < n; ++j) {
    double v = 0;
    for (int k = 0; k < n; ++k)
      for (int l = 0; l < n; ++l) v += bd[k] * P[k][l] * ad[l][j];
    gain[j] = v / s;
  }
  return gain;
}

}  // namespace double_pendulum
