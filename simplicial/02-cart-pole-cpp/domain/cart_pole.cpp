// 02-cart-pole-cpp: Modernized Inverted Pendulum Benchmark

#include "cart_pole.hpp"

#include <algorithm>
#include <cmath>

namespace cart_pole {
namespace {

using paperboat::Context;
using paperboat::Entity;
using paperboat::Values;
using paperboat::get_or;

constexpr double kG = 9.81;                                  // m/s²
constexpr double kCartW = 0.5, kCartH = 0.22, kCartD = 0.35; // m, machined cart dimensions
constexpr double kPivotY = 0.02 + kCartH / 2;                // pivot axle height on the cart's top
constexpr double kRailLimit = 1.5;                           // m, rail end stop travel bounds

class CartPole final : public paperboat::StationObject {
 public:
  explicit CartPole(const Values& p)
      : cart_mass_(get_or(p, "cart_mass")),
        pole_mass_(get_or(p, "pole_mass")),
        half_length_(get_or(p, "pole_length") / 2),
        max_force_(get_or(p, "max_force")),
        x_(get_or(p, "x0")),
        theta_(get_or(p, "theta0")),
        last_force_(0.0) {}

  Values read() const override { return {{"x", x_}, {"v", v_}, {"theta", theta_}, {"omega", omega_}}; }

  void step(const Context& ctx, const Values& in) override {
    const double force = std::clamp(get_or(in, "force"), -max_force_, max_force_);
    last_force_ = force;
    const double total = cart_mass_ + pole_mass_;
    const double sin = std::sin(theta_), cos = std::cos(theta_);
    const double temp = (force + pole_mass_ * half_length_ * omega_ * omega_ * sin) / total;
    const double alpha = (kG * sin - cos * temp) / (half_length_ * (4.0 / 3.0 - pole_mass_ * cos * cos / total));
    const double a = temp - pole_mass_ * half_length_ * alpha * cos / total;

    v_ += a * ctx.dt;
    x_ += v_ * ctx.dt;
    omega_ += alpha * ctx.dt;
    theta_ += omega_ * ctx.dt;

    // Hard rubber stop boundaries at +/- 1.5 m
    if (x_ < -kRailLimit) {
      x_ = -kRailLimit;
      if (v_ < 0.0) v_ = -0.2 * v_;
    } else if (x_ > kRailLimit) {
      x_ = kRailLimit;
      if (v_ > 0.0) v_ = -0.2 * v_;
    }
  }

  std::vector<Entity> entities(const std::string& id, double z) const override {
    const double l = 2 * half_length_;
    const double sin = std::sin(theta_), cos = std::cos(theta_);
    const bool show_force = std::abs(last_force_) > 0.5;
    const double force_arrow_len = std::min(std::abs(last_force_) * 0.025, 0.7);
    const double force_x = x_ + (last_force_ >= 0.0 ? (kCartW / 2 + force_arrow_len / 2) : (-kCartW / 2 - force_arrow_len / 2));

    std::vector<Entity> ents = {
        // Linear precision ground guide rail base
        {.id = id + "/rail_base", .shape = "box", .pos = {0, -0.14, z}, .size = {3.4, 0.04, 0.25}, .rot = {}, .color = "#262626"},
        // Linear track
        {.id = id + "/rail_track", .shape = "box", .pos = {0, -0.10, z}, .size = {3.2, 0.04, 0.12}, .rot = {}, .color = "#475569"},
        // Rubber travel limit end stops
        {.id = id + "/stop_left", .shape = "box", .pos = {-1.55, -0.06, z}, .size = {0.1, 0.12, 0.2}, .rot = {}, .color = "#e11d48"},
        {.id = id + "/stop_right", .shape = "box", .pos = {1.55, -0.06, z}, .size = {0.1, 0.12, 0.2}, .rot = {}, .color = "#e11d48"},
        // Machined aluminum cart body
        {.id = id + "/cart", .shape = "box", .pos = {x_, 0.02, z}, .size = {kCartW, kCartH, kCartD}, .rot = {}, .color = "#94a3b8"},
        // Precision rotary bearing hub
        {.id = id + "/bearing", .shape = "box", .pos = {x_, kPivotY, z + 0.08}, .size = {0.08, 0.08, 0.08}, .rot = {}, .color = "#0284c7"},
        // Degree protractor readout disc
        {.id = id + "/protractor", .shape = "box", .pos = {x_, kPivotY, z + 0.12}, .size = {0.16, 0.16, 0.02}, .rot = {}, .color = "#1e293b"},
        // Matte carbon-fiber pole
        {.id = id + "/pole",
         .shape = "box",
         .pos = {x_ + l / 2 * sin, kPivotY + l / 2 * cos, z},
         .size = {0.03, l, 0.03},
         .rot = {0, 0, -theta_},
         .color = "#0f172a"},
        // Polished brass bob
        {.id = id + "/bob", .shape = "sphere", .pos = {x_ + l * sin, kPivotY + l * cos, z}, .size = {0.08, 0, 0}, .rot = {}, .color = "#eab308"},
    };

    if (show_force) {
      ents.push_back({
          .id = id + "/force_vector",
          .shape = "box",
          .pos = {force_x, 0.02, z},
          .size = {force_arrow_len, 0.03, 0.03},
          .rot = {},
          .color = "#f97316",
      });
    }

    return ents;
  }

 private:
  double cart_mass_, pole_mass_, half_length_, max_force_;
  double x_, v_ = 0.0, theta_, omega_ = 0.0;
  double last_force_;
};

}  // namespace

void register_cart_pole(paperboat::Registry& registry) {
  registry.add(paperboat::define_object<CartPole>(
      "cart-pole",
      {.type = "cart-pole",
       .label = "Cart-pole",
       .role = "body",
       .props = {{.id = "cart_mass", .default_value = 1.0, .unit = "kg"},
                 {.id = "pole_mass", .default_value = 0.1, .unit = "kg"},
                 {.id = "pole_length", .default_value = 1.0, .unit = "m"},
                 {.id = "max_force", .default_value = 25.0, .unit = "N"},
                 {.id = "x0", .default_value = 0.0, .unit = "m"},
                 {.id = "theta0", .default_value = 0.12, .unit = "rad"}},
       .links = {},
       .block = paperboat::BlockDef{.type = "cart-pole",
                                    .label = "Cart-pole",
                                    .kind = paperboat::Kind::Source,
                                    .inputs = {{"force", "signal", "N"}},
                                    .outputs = {{"x", "signal", "m"}, {"v", "signal", "m/s"},
                                                {"theta", "signal", "rad"}, {"omega", "signal", "rad/s"}},
                                    .params = {}},
       .description = "Precision machined cart and inverted pendulum on linear guide rail."}));
}

}  // namespace cart_pole
