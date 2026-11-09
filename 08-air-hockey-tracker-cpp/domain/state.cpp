#include "state.hpp"

#include <algorithm>
#include <cmath>

#include <paperboat/toolkit/scene.hpp>

#ifdef PAPERBOAT_HAS_OPENCV
#include <opencv2/imgproc.hpp>
#endif

namespace air_hockey {
namespace {

constexpr double kTableX = 1.00;   // half-length, m
constexpr double kTableZ = 0.55;   // half-width, m
constexpr double kPuckRadius = 0.035;
constexpr double kMalletRadius = 0.09;
constexpr double kRestitution = 0.94;
constexpr double kFriction = 0.12;
constexpr int kWidth = 320;
constexpr int kHeight = 240;

using paperboat::scene::Vec;

struct Mallet {
  double x, z;
};

Mallet player_mallet(double t) { return {-0.58 + 0.16 * std::sin(0.7 * t), -0.18 + 0.24 * std::sin(0.5 * t)}; }
Mallet rival_mallet(double t) { return {0.58 + 0.14 * std::sin(0.6 * t + 1.0), 0.16 + 0.28 * std::sin(0.4 * t)}; }

paperboat::Entity cylinder(std::string id, Vec pos, double radius, double height, std::string color) {
  return {.id = std::move(id), .shape = "cylinder", .pos = pos, .size = {radius, height, 0.0}, .color = std::move(color)};
}

}  // namespace

AirHockey::AirHockey() { render(); }

bool AirHockey::has_frame() const {
#ifdef PAPERBOAT_HAS_OPENCV
  return !frame_.empty();
#else
  return false;
#endif
}

std::optional<std::string> AirHockey::step(const paperboat::Context& ctx) {
  const double dt = ctx.dt;
  time_ = ctx.t;
  const double damping = std::exp(-kFriction * dt);
  vx_ *= damping;
  vz_ *= damping;
  x_ += vx_ * dt;
  z_ += vz_ * dt;

  // Rails.
  if (x_ + radius_ > kTableX) {
    x_ = kTableX - radius_;
    vx_ = -std::abs(vx_) * kRestitution;
    ++bounces_;
    bounce_marks_.push_back({x_, z_});
  } else if (x_ - radius_ < -kTableX) {
    x_ = -kTableX + radius_;
    vx_ = std::abs(vx_) * kRestitution;
    ++bounces_;
    bounce_marks_.push_back({x_, z_});
  }
  if (z_ + radius_ > kTableZ) {
    z_ = kTableZ - radius_;
    vz_ = -std::abs(vz_) * kRestitution;
    ++bounces_;
    bounce_marks_.push_back({x_, z_});
  } else if (z_ - radius_ < -kTableZ) {
    z_ = -kTableZ + radius_;
    vz_ = std::abs(vz_) * kRestitution;
    ++bounces_;
    bounce_marks_.push_back({x_, z_});
  }

  // The mallets are part of the game: reflect the puck off either one.
  for (const Mallet mallet : {player_mallet(ctx.t), rival_mallet(ctx.t)}) {
    const double dx = x_ - mallet.x;
    const double dz = z_ - mallet.z;
    const double distance = std::hypot(dx, dz);
    const double sum = radius_ + kMalletRadius;
    if (distance < sum && distance > 1e-9) {
      const double nx = dx / distance;
      const double nz = dz / distance;
      x_ = mallet.x + nx * sum;
      z_ = mallet.z + nz * sum;
      const double dot = vx_ * nx + vz_ * nz;
      if (dot < 0.0) {
        vx_ -= 1.85 * dot * nx;
        vz_ -= 1.85 * dot * nz;
        ++bounces_;
        bounce_marks_.push_back({x_, z_});
      }
    }
  }

  trail_.push_back({x_, z_});
  if (trail_.size() > 48) trail_.pop_front();
  ++frames_;
  render();
  return std::nullopt;
}

std::optional<std::string> AirHockey::summary() const {
  return "Tracked " + std::to_string(frames_) + " frames; " + std::to_string(bounces_) +
         " rail/mallet bounces; final puck at (" + std::to_string(x_) + ", " + std::to_string(z_) + ")";
}

void AirHockey::render() {
  // Pinhole camera from above: table metres to pixels.
  u_ = kWidth / 2.0 + x_ * 110.0;
  v_ = kHeight / 2.0 + z_ * 110.0;
  radius_px_ = radius_ * 110.0;
#ifdef PAPERBOAT_HAS_OPENCV
  frame_ = cv::Mat(kHeight, kWidth, CV_8UC3, cv::Scalar(34, 22, 16));
  const auto at = [](double x, double z) {
    return cv::Point(static_cast<int>(kWidth / 2.0 + x * 110.0), static_cast<int>(kHeight / 2.0 + z * 110.0));
  };
  // The rink: rails, centre line, goal creases.
  cv::rectangle(frame_, at(-kTableX, -kTableZ), at(kTableX, kTableZ), cv::Scalar(180, 180, 180), 2);
  cv::line(frame_, at(0, -kTableZ), at(0, kTableZ), cv::Scalar(120, 120, 120), 1);
  cv::circle(frame_, at(0, 0), 28, cv::Scalar(120, 120, 120), 1, cv::LINE_AA);
  cv::rectangle(frame_, at(-kTableX, -0.2), at(-kTableX + 0.12, 0.2), cv::Scalar(120, 120, 120), 1);
  cv::rectangle(frame_, at(kTableX - 0.12, -0.2), at(kTableX, 0.2), cv::Scalar(120, 120, 120), 1);
  // Mallets.
  const auto player = player_mallet(time_);
  const auto rival = rival_mallet(time_);
  cv::circle(frame_, at(player.x, player.z), static_cast<int>(kMalletRadius * 110.0), cv::Scalar(220, 120, 30), cv::FILLED, cv::LINE_AA);
  cv::circle(frame_, at(rival.x, rival.z), static_cast<int>(kMalletRadius * 110.0), cv::Scalar(80, 200, 60), cv::FILLED, cv::LINE_AA);
  // The puck: a saturated red disc. White glints and the table are not in the HSV window.
  cv::circle(frame_, {static_cast<int>(u_), static_cast<int>(v_)}, std::max(3, static_cast<int>(radius_px_)),
             cv::Scalar(30, 30, 245), cv::FILLED, cv::LINE_AA);
  cv::circle(frame_, {static_cast<int>(u_), static_cast<int>(v_)}, std::max(3, static_cast<int>(radius_px_)),
             cv::Scalar(60, 60, 255), 1, cv::LINE_AA);
#endif
}

std::vector<paperboat::Entity> AirHockey::entities() const {
  const Vec player{player_mallet(time_).x, 0.02, player_mallet(time_).z};
  const Vec rival{rival_mallet(time_).x, 0.02, rival_mallet(time_).z};
  std::vector<paperboat::Entity> out = {
      paperboat::scene::box("table", {0, -0.04, 0}, {2.12, 0.08, 1.22}, "#1e3a5f"),
      paperboat::scene::box("rail-north", {0, 0.03, kTableZ + 0.03}, {2.12, 0.08, 0.06}, "#cbd5e1"),
      paperboat::scene::box("rail-south", {0, 0.03, -kTableZ - 0.03}, {2.12, 0.08, 0.06}, "#cbd5e1"),
      paperboat::scene::box("rail-west", {-kTableX - 0.03, 0.03, 0}, {0.06, 0.08, 1.22}, "#cbd5e1"),
      paperboat::scene::box("rail-east", {kTableX + 0.03, 0.03, 0}, {0.06, 0.08, 1.22}, "#cbd5e1"),
      paperboat::scene::box("centre-line", {0, 0.005, 0}, {0.012, 0.01, 1.1}, "#94a3b8"),
      paperboat::scene::box("goal-west", {-kTableX + 0.06, 0.005, 0}, {0.12, 0.01, 0.4}, "#f59e0b"),
      paperboat::scene::box("goal-east", {kTableX - 0.06, 0.005, 0}, {0.12, 0.01, 0.4}, "#f59e0b"),
  };
  for (std::size_t i = 1; i < trail_.size(); ++i)
    out.push_back(paperboat::scene::line("trail-" + std::to_string(i),
                                         {trail_[i - 1][0], 0.012, trail_[i - 1][1]},
                                         {trail_[i][0], 0.012, trail_[i][1]}, "#f97316"));
  for (std::size_t i = 0; i < bounce_marks_.size(); ++i)
    out.push_back(paperboat::scene::sphere("bounce-" + std::to_string(i),
                                           {bounce_marks_[i][0], 0.02, bounce_marks_[i][1]}, 0.02, "#ef4444"));
  out.push_back(cylinder("mallet-player", player, kMalletRadius, 0.06, "#f97316"));
  out.push_back(cylinder("mallet-rival", rival, kMalletRadius, 0.06, "#22c55e"));
  out.push_back(cylinder("puck", {x_, 0.025, z_}, radius_, 0.03, "#ef4444"));
  return out;
}

std::vector<paperboat::Entity> AirHockey::patch() const {
  std::vector<paperboat::Entity> out;
  for (std::size_t i = 1; i < trail_.size(); ++i)
    out.push_back(paperboat::scene::line("trail-" + std::to_string(i),
                                         {trail_[i - 1][0], 0.012, trail_[i - 1][1]},
                                         {trail_[i][0], 0.012, trail_[i][1]}, "#f97316"));
  for (std::size_t i = 0; i < bounce_marks_.size(); ++i)
    out.push_back(paperboat::scene::sphere("bounce-" + std::to_string(i),
                                           {bounce_marks_[i][0], 0.02, bounce_marks_[i][1]}, 0.02, "#ef4444"));
  out.push_back(cylinder("puck", {x_, 0.025, z_}, radius_, 0.03, "#ef4444"));
  return out;
}

}  // namespace air_hockey
