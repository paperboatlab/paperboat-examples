// The double pendulum on a cart: the station object (physics and drawing) and the four
// blocks the three stories use (identify the payload, swing up, check the catch, balance).
//
// The plant is a Model: it owns six states and never steps by hand. The blocks are ordinary
// signal Blocks: they read the plant's linked block on the Flow page and write a force.

#include "pendulum.hpp"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <string>
#include <vector>

#include "dynamics.hpp"

namespace double_pendulum {
namespace {

using paperboat::Block;
using paperboat::BlockDef;
using paperboat::Context;
using paperboat::Entity;
using paperboat::Kind;
using paperboat::ParamDef;
using paperboat::PortDef;
using paperboat::Values;
using paperboat::get_or;
using paperboat::get_text;

constexpr double kPi = std::numbers::pi;
constexpr double kCartWidth = 0.6, kCartHeight = 0.3, kCartDepth = 0.4;
constexpr double kPivotY = kCartHeight / 2;

// The known part of the model, shared by the story blocks. The payload is the only
// parameter the flow does not know: it starts from `payload0` and is estimated. The link
// lengths come from the descriptor's variables (l1, l2), so one edit reaches every block.
Params known_model(double l1 = 0.5, double l2 = 0.5) {
  Params p{};
  p.link1_length = l1;
  p.link2_length = l2;
  return p;
}

State6 state_of(const Values& in) {
  State6 state{};
  if (const auto* vector = paperboat::get_vector(in, "state"); vector && vector->size() == state.size())
    std::copy(vector->begin(), vector->end(), state.begin());
  return state;
}

PortDef state_port() {
  return paperboat::vector_port("state", std::vector<paperboat::VectorComponent>{{"x", "m"},
                                                                                  {"theta1", "rad"},
                                                                                  {"theta2", "rad"},
                                                                                  {"v", "m/s"},
                                                                                  {"omega1", "rad/s"},
                                                                                  {"omega2", "rad/s"}});
}

std::vector<PortDef> state_inputs() { return {state_port()}; }

// --- The station object -----------------------------------------------------------------

class Pendulum final : public paperboat::Model {
 public:
  explicit Pendulum(const Values& p)
      : Model({get_or(p, "x0"), get_or(p, "theta1_0", kPi + 0.05), get_or(p, "theta2_0", kPi - 0.03),
               get_or(p, "v0"), get_or(p, "omega1_0"), get_or(p, "omega2_0")},
              get_text(p, "solver", "rk4")),
        params_{.cart_mass = get_or(p, "cart_mass", 1.0),
                .link1_mass = get_or(p, "link1_mass", 0.3),
                .link1_length = get_or(p, "link1_length", 0.5),
                .link2_mass = get_or(p, "link2_mass", 0.2),
                .link2_length = get_or(p, "link2_length", 0.5),
                .payload = get_or(p, "payload", 0.25),
                .cart_damping = get_or(p, "cart_damping", 0.1),
                .joint1_damping = get_or(p, "joint1_damping", 0.002),
                .joint2_damping = get_or(p, "joint2_damping", 0.002)},
        max_force_(get_or(p, "max_force", 80.0)) {}

  Values read() const override {
    // Keep integrated angles continuous internally for the solver, but publish the vector
    // and scalar readouts in one revolution so the Dashboard says 0 rad when upright.
    paperboat::Vector public_state = x();
    public_state[1] = wrap(public_state[1]);
    public_state[2] = wrap(public_state[2]);
    return {{"state", public_state},
            {"x", x()[0]}, {"theta1", public_state[1]}, {"theta2", public_state[2]},
            {"v", x()[3]}, {"omega1", x()[4]}, {"omega2", x()[5]}};
  }

  paperboat::solve::State derivatives(double, const paperboat::solve::State& s, const Values& in) const override {
    State6 x{};
    for (std::size_t i = 0; i < x.size() && i < s.size(); ++i) x[i] = s[i];
    const double force = std::clamp(get_or(in, "force"), -max_force_, max_force_);
    const State6 d = double_pendulum::derivatives(params_, x, force);
    return {d.begin(), d.end()};
  }

  std::vector<Entity> entities(const std::string& id, double z) const override {
    const auto& s = x();
    const double cart = s[0], t1 = s[1], t2 = s[2];
    const double pivot_x = cart, pivot_y = kPivotY;
    const double joint_x = pivot_x + params_.link1_length * std::sin(t1);
    const double joint_y = pivot_y + params_.link1_length * std::cos(t1);
    const double tip_x = joint_x + params_.link2_length * std::sin(t2);
    const double tip_y = joint_y + params_.link2_length * std::cos(t2);
    return {
        paperboat::scene::box(id + "/rail", {0, -0.15, z}, {8, 0.04, 0.25}, "#8a8f8c"),
        paperboat::scene::box(id + "/cart", {cart, 0, z}, {kCartWidth, kCartHeight, kCartDepth}, "#2f5d62"),
        paperboat::scene::rod(id + "/link1", {pivot_x, pivot_y, z}, {joint_x, joint_y, z}, 0.05, "#1c2321"),
        paperboat::scene::sphere(id + "/joint", {joint_x, joint_y, z}, 0.06, "#c2410c"),
        paperboat::scene::rod(id + "/link2", {joint_x, joint_y, z}, {tip_x, tip_y, z}, 0.04, "#344e41"),
        paperboat::scene::sphere(id + "/payload", {tip_x, tip_y, z}, 0.09, "#b45309"),
    };
  }

 private:
  Params params_;
  double max_force_;
};

// --- Story 1: identify the payload ------------------------------------------------------

// Recursive least squares on the cart equation, which is linear in the unknown payload:
//
//   F = (M + m_p)·ẍ + A1(cos θ1·θ̈1 − sin θ1·ω1²) + A2(cos θ2·θ̈2 − sin θ2·ω2²) + b0·ẋ
//
// The block reads the state and the force the engine actually applied last step (the sum
// output), finite-differences the accelerations, and updates m_p one step at a time.
class Identify final : public Block {
 public:
  explicit Identify(const Values& p)
      : payload_(get_or(p, "payload0", 0.05)),
        covariance_(get_or(p, "covariance0", 1.0)),
        forgetting_(get_or(p, "forgetting", 0.999)),
        drive_(get_or(p, "drive", 8.0)),
        frequency_(get_or(p, "frequency", 0.7)),
        link1_length_(get_or(p, "l1", 0.5)),
        link2_length_(get_or(p, "l2", 0.5)) {}

  Values step(const Context& ctx, const Values& in) override {
    const State6 x = state_of(in);
    const double force = get_or(in, "force");  // the sum, i.e. last step's story output
    if (have_previous_ && ctx.dt > 0) update(x, ctx.dt);

    previous_ = x;
    previous_force_ = force;
    have_previous_ = true;

    // A slow sweep of the cart: it makes the regressor persistently exciting so every
    // parameter is identifiable, and keeps the cart near home while it does.
    const double drive = drive_ * std::sin(2 * kPi * frequency_ * ctx.t) - 2.0 * x[0] - 3.0 * x[3];
    return {{"m_hat", payload_}, {"drive", drive}, {"cov", covariance_}};
  }

 private:
  void update(const State6& x, double dt) {
    const State6& p = previous_;
    const double ax = (x[3] - p[3]) / dt;
    const double a1 = (x[4] - p[4]) / dt;
    const double a2 = (x[5] - p[5]) / dt;

    Params known = known_model(link1_length_, link2_length_);
    known.payload = 0.0;  // the part already accounted for
    const Consts c = constants(known);
    const double base = c.total * ax + c.a1 * std::cos(p[1]) * a1 - c.a1 * std::sin(p[1]) * p[4] * p[4] +
                        c.a2 * std::cos(p[2]) * a2 - c.a2 * std::sin(p[2]) * p[5] * p[5] + known.cart_damping * p[3];
    const double y = previous_force_ - base;
    const double regressor = ax + link1_length_ * (std::cos(p[1]) * a1 - std::sin(p[1]) * p[4] * p[4]) +
                             link2_length_ * (std::cos(p[2]) * a2 - std::sin(p[2]) * p[5] * p[5]);

    const double gain = covariance_ * regressor / (forgetting_ + regressor * regressor * covariance_);
    payload_ += gain * (y - regressor * payload_);
    covariance_ = (covariance_ - gain * regressor * covariance_) / forgetting_;
    payload_ = std::clamp(payload_, 0.0, 2.0);
  }

  double payload_, covariance_, forgetting_, drive_, frequency_;
  double link1_length_, link2_length_;
  State6 previous_{};
  double previous_force_ = 0.0;
  bool have_previous_ = false;
};

// --- Story 2: swing up by energy shaping -------------------------------------------------

class Swing final : public Block {
 public:
  explicit Swing(const Values& p)
      : k_energy_(get_or(p, "k_energy", 5.0)),
        u_max_(get_or(p, "u_max", 15.0)),
        k_x_(get_or(p, "k_x", 1.0)),
        k_v_(get_or(p, "k_v", 2.0)),
        max_force_(get_or(p, "max_force", 80.0)),
        park_limit_(get_or(p, "park_limit", 10.0)),
        link1_length_(get_or(p, "l1", 0.5)),
        link2_length_(get_or(p, "l2", 0.5)) {}

  Values step(const Context& ctx, const Values& in) override {
    Params p = known_model(link1_length_, link2_length_);
    p.payload = std::max(0.01, get_or(in, "m_hat", 0.05));
    const State6 x = state_of(in);
    if (start_ < 0) start_ = ctx.t;

    if (!parked_) {
      const bool quiet = energy_links(p, x) < -0.85 * energy_ref(p) && std::abs(x[4]) + std::abs(x[5]) < 0.3 &&
                         std::abs(x[3]) < 0.15;
      if (quiet || ctx.t > start_ + park_limit_) parked_ = true;
    }
    if (!parked_) return {{"force", -12.0 * x[3] - 3.0 * x[0]}};
    return {{"force", swing_force(p, x, k_energy_, u_max_, k_x_, k_v_, max_force_, true)}};
  }

 private:
  double k_energy_, u_max_, k_x_, k_v_, max_force_, park_limit_;
  double link1_length_, link2_length_;
  double start_ = -1.0;
  bool parked_ = false;
};

// --- The catch gate and story 3: LQR balance --------------------------------------------

// A plain signal block: "would the balance controller catch this state?". It simulates the
// closed loop for 2 s with the same model and force delay the engine has, and its answer
// ends the swing-up story through that story's `until` input.
class Catch final : public Block {
 public:
  explicit Catch(const Values& p)
      : max_force_(get_or(p, "max_force", 80.0)), horizon_(get_or(p, "horizon", 2.0)),
        link1_length_(get_or(p, "l1", 0.5)), link2_length_(get_or(p, "l2", 0.5)) {}

  Values step(const Context& ctx, const Values& in) override {
    const double mass = std::max(0.01, get_or(in, "m_hat", 0.05));
    if (mass != cached_mass_) {
      gain_ = lqr_gain(known_model(link1_length_, link2_length_), mass);
      cached_mass_ = mass;
    }
    const State6 x = state_of(in);
    // A cheap gate first: the 2 s simulation only makes sense near the top.
    if (std::abs(x[0]) > 3.0 || std::abs(wrap(x[1])) > 1.2 || std::abs(wrap(x[2])) > 1.2 ||
        std::abs(x[3]) > 15.0 || std::abs(x[4]) > 15.0 || std::abs(x[5]) > 15.0)
      return {{"near", 0.0}};
    Params p = known_model(link1_length_, link2_length_);
    p.payload = mass;
    return {{"near", catch_ok(p, x, gain_, max_force_, horizon_, ctx.dt > 0 ? ctx.dt : 0.01) ? 1.0 : 0.0}};
  }

 private:
  double max_force_, horizon_;
  double link1_length_, link2_length_;
  double cached_mass_ = -1.0;
  std::array<double, 6> gain_{};
};

class Balance final : public Block {
 public:
  explicit Balance(const Values& p)
      : max_force_(get_or(p, "max_force", 80.0)),
        link1_length_(get_or(p, "l1", 0.5)), link2_length_(get_or(p, "l2", 0.5)) {}

  Values step(const Context&, const Values& in) override {
    const double mass = std::max(0.01, get_or(in, "m_hat", 0.05));
    if (mass != cached_mass_) {
      gain_ = lqr_gain(known_model(link1_length_, link2_length_), mass);
      cached_mass_ = mass;
    }
    const State6 e = wrap_angles(state_of(in));
    double u = 0;
    for (std::size_t i = 0; i < gain_.size(); ++i) u += gain_[i] * e[i];
    return {{"force", std::clamp(-u, -max_force_, max_force_)}};
  }

 private:
  double max_force_;
  double link1_length_, link2_length_;
  double cached_mass_ = -1.0;
  std::array<double, 6> gain_{};
};

}  // namespace

void register_pendulum(paperboat::Registry& registry) {
  registry.add(paperboat::define_object<Pendulum>(
      "double-pendulum",
      {.type = "double-pendulum",
       .label = "Double pendulum on a cart",
       .role = "body",
       .props = {{.id = "cart_mass", .default_value = 1.0, .unit = "kg"},
                 {.id = "link1_mass", .default_value = 0.3, .unit = "kg"},
                 {.id = "link1_length", .default_value = 0.5, .unit = "m"},
                 {.id = "link2_mass", .default_value = 0.2, .unit = "kg"},
                 {.id = "link2_length", .default_value = 0.5, .unit = "m"},
                 {.id = "payload", .default_value = 0.25, .unit = "kg"},
                 {.id = "cart_damping", .default_value = 0.1, .unit = "N·s/m"},
                 {.id = "joint1_damping", .default_value = 0.002, .unit = "N·m·s/rad"},
                 {.id = "joint2_damping", .default_value = 0.002, .unit = "N·m·s/rad"},
                 {.id = "max_force", .default_value = 80.0, .unit = "N"},
                 {.id = "x0", .default_value = 0.0, .unit = "m"},
                 {.id = "v0", .default_value = 0.0, .unit = "m/s"},
                 {.id = "theta1_0", .default_value = std::numbers::pi + 0.05, .unit = "rad"},
                 {.id = "theta2_0", .default_value = std::numbers::pi - 0.03, .unit = "rad"},
                 {.id = "omega1_0", .default_value = 0.0, .unit = "rad/s"},
                 {.id = "omega2_0", .default_value = 0.0, .unit = "rad/s"},
                 paperboat::solve::param("rk4")},
       .links = {},
       .block = BlockDef{.type = "double-pendulum",
                         .label = "Double pendulum",
                         .kind = Kind::Source,
                         .inputs = {{"force", "signal", "N"}},
                          .outputs = {state_port(), {"x", "signal", "m"}, {"theta1", "signal", "rad"},
                                      {"theta2", "signal", "rad"}, {"v", "signal", "m/s"},
                                     {"omega1", "signal", "rad/s"}, {"omega2", "signal", "rad/s"}},
                         .params = {}},
       .description = "Two links on a cart; force the cart to swing the payload upright."}));

  registry.add(paperboat::define_block<Identify>(
      "double-pendulum",
      {.type = "identify",
       .label = "Identify payload",
       .inputs = [] {
         auto ports = state_inputs();
         ports.push_back({.id = "force", .type = "signal", .unit = "N"});
         return ports;
       }(),
       .outputs = {{"m_hat", "signal", "kg"}, {"drive", "signal", "N"}, {"cov", "signal"}},
       .params = {{.id = "payload0", .default_value = 0.05, .unit = "kg"},
                  {.id = "covariance0", .default_value = 1.0},
                  {.id = "forgetting", .default_value = 0.999},
                  {.id = "drive", .default_value = 8.0, .unit = "N"},
                  {.id = "frequency", .default_value = 0.7, .unit = "Hz"},
                  {.id = "l1", .default_value = 0.5, .unit = "m"},
                  {.id = "l2", .default_value = 0.5, .unit = "m"}},
       .description = "Gray-box RLS: the payload mass from the cart equation."}));

  registry.add(paperboat::define_block<Swing>(
      "double-pendulum",
      {.type = "swing",
       .label = "Swing up",
       .inputs = [] {
         auto ports = state_inputs();
         ports.push_back({.id = "m_hat", .type = "signal", .unit = "kg"});
         return ports;
       }(),
       .outputs = {{"force", "signal", "N"}},
       .params = {{.id = "k_energy", .default_value = 5.0},
                  {.id = "u_max", .default_value = 15.0, .unit = "m/s²"},
                  {.id = "k_x", .default_value = 1.0},
                  {.id = "k_v", .default_value = 2.0},
                  {.id = "max_force", .default_value = 80.0, .unit = "N"},
                  {.id = "park_limit", .default_value = 10.0, .unit = "s"},
                  {.id = "l1", .default_value = 0.5, .unit = "m"},
                  {.id = "l2", .default_value = 0.5, .unit = "m"}},
       .description = "Energy shaping: pump the links up to upright energy, then hold the cart."}));

  registry.add(paperboat::define_block<Catch>(
      "double-pendulum",
      {.type = "catch",
       .label = "Can it catch?",
       .inputs = [] {
         auto ports = state_inputs();
         ports.push_back({.id = "m_hat", .type = "signal", .unit = "kg"});
         return ports;
       }(),
       .outputs = {{"near", "signal"}},
       .params = {{.id = "max_force", .default_value = 80.0, .unit = "N"},
                  {.id = "horizon", .default_value = 2.0, .unit = "s"},
                  {.id = "l1", .default_value = 0.5, .unit = "m"},
                  {.id = "l2", .default_value = 0.5, .unit = "m"}},
       .description = "Simulates the LQR for 2 s; 1 when the balance story can take over."}));

  registry.add(paperboat::define_block<Balance>(
      "double-pendulum",
      {.type = "balance",
       .label = "Balance",
       .inputs = [] {
         auto ports = state_inputs();
         ports.push_back({.id = "m_hat", .type = "signal", .unit = "kg"});
         return ports;
       }(),
       .outputs = {{"force", "signal", "N"}},
       .params = {{.id = "max_force", .default_value = 80.0, .unit = "N"},
                  {.id = "l1", .default_value = 0.5, .unit = "m"},
                  {.id = "l2", .default_value = 0.5, .unit = "m"}},
       .description = "LQR at upright, with the gain from the estimated payload."}));
}

}  // namespace double_pendulum
