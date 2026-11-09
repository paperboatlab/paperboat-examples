// This domain's station object: a pole on a cart that slides along x, with the classic
// equations (Barto, Sutton & Anderson 1983). Its linked block pushes the cart and reads
// both. Initial conditions are props, set on the Station.

#include "cart_pole.hpp"

#include <algorithm>
#include <cmath>

namespace cart_pole {
namespace {

using paperboat::Context;
using paperboat::Entity;
using paperboat::Values;
using paperboat::get_or;

constexpr double kG = 9.81;                         // m/s²
constexpr double kCartW = 0.6, kCartH = 0.3, kCartD = 0.4;  // m, drawn size
constexpr double kPivotY = kCartH / 2;               // pivot on the cart's top

class CartPole final : public paperboat::StationObject {
 public:
  explicit CartPole(const Values& p)
      : cart_mass_(get_or(p, "cart_mass")),
        pole_mass_(get_or(p, "pole_mass")),
        half_length_(get_or(p, "pole_length") / 2),
        max_force_(get_or(p, "max_force")),
        x_(get_or(p, "x0")),
        theta_(get_or(p, "theta0")) {}

  Values read() const override { return {{"x", x_}, {"v", v_}, {"theta", theta_}, {"omega", omega_}}; }

  // Semi-implicit Euler, as the earlier example domains did, so results match them.
  void step(const Context& ctx, const Values& in) override {
    const double force = std::clamp(get_or(in, "force"), -max_force_, max_force_);
    const double total = cart_mass_ + pole_mass_;
    const double sin = std::sin(theta_), cos = std::cos(theta_);
    const double temp = (force + pole_mass_ * half_length_ * omega_ * omega_ * sin) / total;
    const double alpha = (kG * sin - cos * temp) / (half_length_ * (4.0 / 3.0 - pole_mass_ * cos * cos / total));
    const double a = temp - pole_mass_ * half_length_ * alpha * cos / total;
    v_ += a * ctx.dt;
    x_ += v_ * ctx.dt;
    omega_ += alpha * ctx.dt;
    theta_ += omega_ * ctx.dt;
  }

  std::vector<Entity> entities(const std::string& id, double z) const override {
    const double l = 2 * half_length_;
    const double sin = std::sin(theta_), cos = std::cos(theta_);
    return {
        {.id = id + "/rail", .shape = "box", .pos = {0, -0.1, z}, .size = {8, 0.05, 0.3}, .rot = {}, .color = "#8a8f8c"},
        {.id = id + "/cart", .shape = "box", .pos = {x_, 0, z}, .size = {kCartW, kCartH, kCartD}, .rot = {}, .color = "#2f5d62"},
        {.id = id + "/pole",
         .shape = "box",
         .pos = {x_ + l / 2 * sin, kPivotY + l / 2 * cos, z},
         .size = {0.04, l, 0.04},
         .rot = {0, 0, -theta_},
         .color = "#1c2321"},
        {.id = id + "/bob", .shape = "sphere", .pos = {x_ + l * sin, kPivotY + l * cos, z}, .size = {0.08, 0, 0}, .rot = {}, .color = "#c2410c"},
    };
  }

 private:
  double cart_mass_, pole_mass_, half_length_, max_force_;
  double x_, v_ = 0.0, theta_, omega_ = 0.0;
};

}  // namespace

void register_cart_pole(paperboat::Registry& registry) {
  registry.add(paperboat::define_object<CartPole>(
      "cart-pole",  // the domain's own package: its descriptor gets it without importing it
      {.type = "cart-pole",
       .label = "Cart-pole",
       .role = "body",
       .props = {{.id = "cart_mass", .default_value = 1.0, .unit = "kg"},
                 {.id = "pole_mass", .default_value = 0.2, .unit = "kg"},
                 {.id = "pole_length", .default_value = 1.0, .unit = "m"},
                 {.id = "max_force", .default_value = 50.0, .unit = "N"},
                 {.id = "x0", .default_value = 0.0, .unit = "m"},              // initial conditions:
                 {.id = "theta0", .default_value = 0.15, .unit = "rad"}},      // from upright
       .links = {},
       .block = paperboat::BlockDef{.type = "cart-pole",
                                    .label = "Cart-pole",
                                    .kind = paperboat::Kind::Source,
                                    .inputs = {{"force", "signal", "N"}},
                                    .outputs = {{"x", "signal", "m"}, {"v", "signal", "m/s"},
                                                {"theta", "signal", "rad"}, {"omega", "signal", "rad/s"}},
                                    .params = {}},
       .description = "A pole on a cart that slides along a rail; balance it by pushing the cart."}));
}

}  // namespace cart_pole
