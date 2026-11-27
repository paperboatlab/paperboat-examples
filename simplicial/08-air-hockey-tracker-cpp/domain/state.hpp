#pragma once

// The air-hockey domain: the puck, its synthetic camera and the vision/tracking blocks.

#include <array>
#include <deque>
#include <string>
#include <vector>

#include <paperboat/sdk.hpp>

#ifdef PAPERBOAT_HAS_OPENCV
#include <opencv2/core.hpp>
#endif

namespace air_hockey {

// The fallback image payload when OpenCV is absent: just the true centroid and radius.
struct SyntheticFrame {
  double u = 0.0;
  double v = 0.0;
  double radius = 0.0;
  int index = 0;
};

// A puck on an air-hockey table, seen by an overhead camera.
class AirHockey final : public paperboat::DomainState {
 public:
  AirHockey();

  std::optional<std::string> step(const paperboat::Context& ctx) override;
  std::optional<std::string> summary() const override;
  std::vector<paperboat::Entity> entities() const override;
  std::vector<paperboat::Entity> patch() const override;

  bool has_frame() const;
#ifdef PAPERBOAT_HAS_OPENCV
  const cv::Mat& frame() const { return frame_; }
#endif
  SyntheticFrame synthetic() const { return {u_, v_, radius_px_, frames_}; }

  double x() const { return x_; }
  double z() const { return z_; }
  double u() const { return u_; }
  double v() const { return v_; }
  double radius() const { return radius_; }
  int bounces() const { return bounces_; }
  int frames() const { return frames_; }

 private:
  void render();

  double x_ = 0.0, z_ = 0.0;
  double vx_ = 1.75, vz_ = 1.15;
  double radius_ = 0.035;
  double u_ = 0.0, v_ = 0.0, radius_px_ = 0.0;
  int bounces_ = 0;
  int frames_ = 0;
  double time_ = 0.0;
  std::deque<std::array<double, 2>> trail_;
  std::vector<std::array<double, 2>> bounce_marks_;
#ifdef PAPERBOAT_HAS_OPENCV
  cv::Mat frame_;
#endif
};

}  // namespace air_hockey
