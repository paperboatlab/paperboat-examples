// The pantograph's multibody head, the compliant catenary and the active regulator.
//
// The reference acausal model is modelica/PantographCatenary.mo. This backend carries the
// same equations in code: a head mass on a suspension spring/damper, a contact spring with
// the wire, aerodynamic uplift growing with v², and a PI pneumatic actuator.

#include "pantograph.hpp"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <string>
#include <vector>

#include <paperboat/toolkit/scene.hpp>

namespace pantograph {
namespace {

using paperboat::Block;
using paperboat::Context;
using paperboat::Entity;
using paperboat::Kind;
using paperboat::StationObject;
using paperboat::Values;
using paperboat::get_or;

constexpr double kG = 9.81;
constexpr double kRoofY = 3.55;      // m, train roof
constexpr double kWireHeight = 5.2;  // m, mean contact-wire height above the rail

// The wire's slow height ripple: messenger-wire sag and the dropper spacing.
double wire_height(double x) {
  return kWireHeight + 0.010 * std::sin(2.0 * std::numbers::pi * x / 18.0) +
         0.004 * std::sin(2.0 * std::numbers::pi * x / 6.2);
}

// The head and its suspension, linked to the Flow through `force` (N).
class Pantograph final : public StationObject {
 public:
  explicit Pantograph(const Values& p)
      : mass_(get_or(p, "mass", 12.0)),
        stiffness_(get_or(p, "stiffness", 400.0)),
        damping_(get_or(p, "damping", 260.0)),
        wire_stiffness_(get_or(p, "wire_stiffness", 500.0)),
        wire_damping_(get_or(p, "wire_damping", 30.0)),
        base_(get_or(p, "base", 5.15)),
        target_(get_or(p, "target_force", 108.0)),
        vmax_(get_or(p, "max_speed", 320.0) / 3.6),
        aero_(get_or(p, "aero_lift", 0.020)),
        z_(wire_height(0.0) + target_ / get_or(p, "wire_stiffness", 500.0)) {}

  Values read() const override {
    return {{"contact", contact_}, {"speed", speed_ * 3.6}, {"z", z_}, {"wire", wire_},
            {"uplift", uplift_}, {"losses", static_cast<double>(losses_)}, {"arcing", arcing_ ? 1.0 : 0.0},
            {"in_window", contact_ >= 90.0 && contact_ <= 140.0 ? 1.0 : 0.0}};
  }

  void step(const Context& ctx, const Values& in) override {
    const double dt = ctx.dt;
    time_ += dt;
    const double actuator = std::clamp(get_or(in, "force", 150.0), 0.0, 700.0);
    speed_ = std::min(vmax_, vmax_ * time_ / 25.0);
    const double previous_wire = wire_;
    wire_ = wire_height(distance_);
    const double wire_speed = (wire_ - previous_wire) / std::max(dt, 1e-6);
    const double gap = z_ - wire_;
    contact_ = std::max(0.0, wire_stiffness_ * gap + wire_damping_ * (vz_ - wire_speed));
    uplift_ = 0.5 * 1.2 * speed_ * speed_ * aero_;

    const double acceleration =
        (stiffness_ * (base_ - z_) - damping_ * vz_ + actuator + uplift_ - contact_) / mass_;
    vz_ += acceleration * dt;
    z_ += vz_ * dt;
    distance_ += speed_ * dt;

    const bool lost = contact_ < 20.0;
    const bool over = contact_ > 200.0;
    if (lost) {
      if (!arcing_) {
        ctx.log("ARCING: contact lost at " + std::to_string(speed_ * 3.6) + " km/h", "warn");
        arcing_ = true;
      }
      ++losses_;
    } else if (arcing_ && contact_ > 40.0) {
      ctx.log("contact restored at " + std::to_string(speed_ * 3.6) + " km/h");
      arcing_ = false;
    }
    if (over && !overforce_) {
      ctx.log("OVER-FORCE: contact " + std::to_string(contact_) + " N", "warn");
      overforce_ = true;
    } else if (overforce_ && contact_ < 180.0) {
      overforce_ = false;
    }
  }

  std::vector<Entity> entities(const std::string& id, double z_depth) const override {
    using paperboat::scene::box;
    using paperboat::scene::line;
    using paperboat::scene::sphere;
    const std::string p = id + "/";
    std::vector<Entity> out = {
        // Train roof and the aerodynamic fairing.
        box(p + "roof", {0, kRoofY, z_depth}, {7.0, 0.34, 2.4}, "#334155"),
        box(p + "fairing", {0, kRoofY + 0.22, z_depth}, {3.2, 0.12, 1.8}, "#475569"),
        // Pantograph base frame.
        box(p + "base", {0, kRoofY + 0.24, z_depth}, {1.2, 0.12, 1.2}, "#1e293b"),
        // Articulated single arm: roof pivot, knee, head.
        line(p + "lower-arm", {0, kRoofY + 0.28, z_depth}, {0.35, 4.55, z_depth}, "#f59e0b"),
        line(p + "upper-arm", {0.35, 4.55, z_depth}, {0.02, z_, z_depth}, "#fbbf24"),
        line(p + "tie-rod", {0.0, kRoofY + 0.3, z_depth}, {0.15, 4.35, z_depth}, "#a16207"),
        sphere(p + "base-joint", {0, kRoofY + 0.28, z_depth}, 0.08, "#111827"),
        sphere(p + "knee", {0.35, 4.55, z_depth}, 0.06, "#111827"),
        // Carbon contact strip.
        box(p + "strip", {0.02, z_, z_depth}, {0.5, 0.05, 1.55}, "#0f172a"),
        // Catenary mast and droppers, drawn relative to the moving train.
        box(p + "mast", {3.6, (kRoofY + 5.5) / 2, z_depth - 0.6}, {0.12, 5.5 - kRoofY, 0.12}, "#64748b"),
    };
    // The contact wire and its droppers move over the roof as the train advances.
    for (int i = -5; i <= 5; ++i) {
      const double x = i * 0.7;
      const double y = wire_height(distance_ + x);
      out.push_back(line(p + "wire-" + std::to_string(i), {x - 0.7, wire_height(distance_ + x - 0.7), z_depth},
                         {x, y, z_depth}, "#94a3b8"));
      if (i % 2 == 0)
        out.push_back(line(p + "dropper-" + std::to_string(i), {x, y, z_depth}, {x, y + 0.55, z_depth}, "#64748b"));
    }
    // Contact force vector: green in the window, amber under, red over.
    const double force_length = std::clamp(contact_ * 0.006, 0.04, 0.9);
    const std::string force_color = contact_ < 20.0 ? "#ef4444" : contact_ > 200.0 ? "#f97316" : (contact_ < 90.0 ? "#facc15" : "#22c55e");
    out.push_back(line(p + "force", {0.02, z_, z_depth}, {0.02, z_ + force_length, z_depth}, force_color));
    // Speed gauge on the roof.
    out.push_back(box(p + "speed-bar", {-2.8, kRoofY + 0.35, z_depth}, {2.0, 0.05, 0.08}, "#1f2937"));
    out.push_back(box(p + "speed-fill", {-2.8 - 1.0 + speed_ / vmax_, kRoofY + 0.36, z_depth},
                      {2.0 * speed_ / vmax_, 0.06, 0.09}, "#38bdf8"));
    if (contact_ < 20.0) {
      for (int i = 0; i < 4; ++i) {
        const double angle = time_ * 17.0 + i * 1.7;
        out.push_back(sphere(p + "spark-" + std::to_string(i),
                             {0.02 + 0.12 * std::cos(angle), z_ + 0.08 + 0.08 * std::sin(angle * 1.3), z_depth},
                             0.025, "#facc15"));
      }
    }
    return out;
  }

  // The head alone changes every step; the teacher scene sends this as a patch.
  std::vector<Entity> moving(const std::string& id) const { return entities(id, 0.0); }

  double contact() const { return contact_; }
  double speed_kmh() const { return speed_ * 3.6; }
  double uplift() const { return uplift_; }
  int losses() const { return losses_; }

 private:
  double mass_, stiffness_, damping_, wire_stiffness_, wire_damping_, base_, target_, vmax_, aero_;
  double z_, vz_ = 0.0, wire_ = kWireHeight, contact_ = 0.0, speed_ = 0.0, uplift_ = 0.0;
  double distance_ = 0.0, time_ = 0.0;
  int losses_ = 0;
  bool arcing_ = false, overforce_ = false;
};

// The pneumatic actuator: target contact force, PI on the measured force. A dashboard
// switch bypasses it to a fixed 150 N, which loses contact at high speed.
class Regulator final : public Block {
 public:
  explicit Regulator(const Values& p)
      : target_(get_or(p, "target", 108.0)), kp_(get_or(p, "kp", 2.5)), ki_(get_or(p, "ki", 0.6)),
        base_(get_or(p, "base", 150.0)), bypass_(get_or(p, "bypass_force", 0.0)) {}

  Values step(const Context& ctx, const Values& in) override {
    const double contact = get_or(in, "contact", 0.0);
    const double mode = get_or(in, "mode", 1.0);
    if (mode <= 0.5) {
      integral_ = 0.0;
      return {{"force", bypass_}, {"error", target_ - contact}};
    }
    const double error = target_ - contact;
    integral_ = std::clamp(integral_ + error * ctx.dt, -200.0, 200.0);
    const double force = std::clamp(base_ + kp_ * error + ki_ * integral_, 0.0, 700.0);
    return {{"force", force}, {"error", error}};
  }

 private:
  double target_, kp_, ki_, base_, bypass_;
  double integral_ = 0.0;
};

// A board readout and the once-per-run proof for the golden test.
class ContactProbe final : public Block {
 public:
  Values step(const Context& ctx, const Values& in) override {
    const double contact = get_or(in, "contact", 0.0);
    const double speed = get_or(in, "speed", 0.0);
    const double losses = get_or(in, "losses", 0.0);
    const double uplift = get_or(in, "uplift", 0.0);
    if (!reported_ && ctx.t > 29.0) {
      reported_ = true;
      ctx.log("regulator: contact " + std::to_string(contact) + " N at " + std::to_string(speed) +
              " km/h, " + std::to_string(static_cast<int>(losses)) + " contact losses");
    }
    return {{"contact", contact}, {"speed", speed}, {"losses", losses}, {"uplift", uplift},
            {"in_window", contact >= 90.0 && contact <= 140.0 ? 1.0 : 0.0}};
  }

 private:
  bool reported_ = false;
};

}  // namespace

void register_pantograph(paperboat::Registry& registry) {
  registry.add(paperboat::define_object<Pantograph>(
      "train",
      {.type = "pantograph",
       .label = "Articulated Pantograph",
       .role = "body",
       .props = {{.id = "mass", .default_value = 12.0, .unit = "kg"},
                 {.id = "stiffness", .default_value = 400.0, .unit = "N/m"},
                 {.id = "damping", .default_value = 260.0, .unit = "N·s/m"},
                 {.id = "wire_stiffness", .default_value = 500.0, .unit = "N/m"},
                 {.id = "wire_damping", .default_value = 30.0, .unit = "N·s/m"},
                 {.id = "base", .default_value = 5.15, .unit = "m"},
                 {.id = "target_force", .default_value = 108.0, .unit = "N"},
                 {.id = "max_speed", .default_value = 320.0, .unit = "km/h"},
                 {.id = "aero_lift", .default_value = 0.020, .unit = ""}},
       .links = {},
       .block = paperboat::BlockDef{.type = "pantograph",
                                    .label = "Pantograph",
                                    .kind = Kind::Source,
                                    .inputs = {{"force", "signal", "N"}},
                                    .outputs = {{"contact", "signal", "N"}, {"speed", "signal", "km/h"},
                                                {"z", "signal", "m"}, {"wire", "signal", "m"},
                                                {"uplift", "signal", "N"}, {"losses", "signal"},
                                                {"arcing", "signal"}, {"in_window", "signal"}},
                                    .params = {}},
       .description = "Articulated pantograph head on a compliant catenary."}));
  registry.add(paperboat::define_block<Regulator>(
      "train", {.type = "regulator", .label = "Pneumatic Regulator", .kind = Kind::Function,
                .inputs = {{"contact", "signal", "N"}, {"speed", "signal", "km/h"}, {"mode"}},
                .outputs = {{"force", "signal", "N"}, {"error", "signal", "N"}},
                .params = {{"target", 108.0}, {"kp", 2.5}, {"ki", 0.6}, {"base", 150.0}, {"bypass_force", 0.0}},
                .description = "PI actuator holding the contact force in its window."}));
  registry.add(paperboat::define_block<ContactProbe>(
      "train", {.type = "contact_probe", .label = "Contact Probe", .kind = Kind::Probe,
                .inputs = {{"contact", "signal", "N"}, {"speed", "signal", "km/h"},
                           {"losses", "signal"}, {"uplift", "signal", "N"}},
                .outputs = {{"contact", "signal", "N"}, {"speed", "signal", "km/h"}, {"losses", "signal"},
                            {"uplift", "signal", "N"}, {"in_window", "signal"}},
                .params = {}, .description = "Contact force, speed and aerodynamic uplift."}));
}

}  // namespace pantograph
