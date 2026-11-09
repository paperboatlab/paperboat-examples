#include "vision.hpp"

#include <algorithm>
#include <cmath>
#include <memory>
#include <string>

#include "state.hpp"

#ifdef PAPERBOAT_HAS_OPENCV
#include <opencv2/imgproc.hpp>
#include <paperboat/toolkit/opencv.hpp>
#endif

namespace air_hockey {
namespace {

using paperboat::Block;
using paperboat::Context;
using paperboat::Kind;
using paperboat::Values;

#ifdef PAPERBOAT_HAS_OPENCV
Values make_image(cv::Mat image) { return {{"image", paperboat::toolkit::opencv::image_out(std::move(image))}}; }
Values make_image(const SyntheticFrame& frame) { return {{"image", paperboat::make_handle("image", frame)}}; }
const cv::Mat* image_in(const Values& in, std::string_view port) {
  return paperboat::toolkit::get_handle<cv::Mat>(in, port, "image");
}
#else
Values make_image(const SyntheticFrame& frame) { return {{"image", paperboat::make_handle("image", frame)}}; }
#endif

// The high-speed camera: a synthetic frame and the truth the tutorial compares against.
class Camera final : public Block {
 public:
  Values step(const Context& ctx, const Values&) override {
    auto* state = static_cast<AirHockey*>(ctx.state);
    Values out{{"truth_u", state->u()}, {"truth_v", state->v()},
               {"bounces", static_cast<double>(state->bounces())}, {"frames", static_cast<double>(state->frames())}};
#ifdef PAPERBOAT_HAS_OPENCV
    if (state->has_frame()) out.merge(Values{{"image", paperboat::toolkit::opencv::image_out(state->frame())}});
    else out.merge(make_image(state->synthetic()));
#else
    out.merge(make_image(state->synthetic()));
#endif
    return out;
  }
};

// Degraded path: no OpenCV, so the "vision" stage simply passes the camera's truth on.
class Vision final : public Block {
 public:
  Values step(const Context&, const Values& in) override {
    const double fallback_u = paperboat::get_or(in, "truth_u", 160.0);
    const double fallback_v = paperboat::get_or(in, "truth_v", 120.0);
    Values out{{"u", fallback_u}, {"v", fallback_v}, {"radius", 3.85}, {"found", 1.0}};
#ifdef PAPERBOAT_HAS_OPENCV
    const cv::Mat* source = image_in(in, "image");
    if (source && !source->empty()) {
      cv::Mat hsv, mask;
      cv::cvtColor(*source, hsv, cv::COLOR_BGR2HSV);
      cv::inRange(hsv, cv::Scalar(0, 120, 80), cv::Scalar(12, 255, 255), mask);
      const cv::Mat kernel = cv::getStructuringElement(cv::MORPH_ELLIPSE, {3, 3});
      cv::morphologyEx(mask, mask, cv::MORPH_OPEN, kernel);
      cv::morphologyEx(mask, mask, cv::MORPH_CLOSE, kernel);
      const cv::Moments moments = cv::moments(mask, true);
      if (moments.m00 > 4.0) {
        out = {{"u", moments.m10 / moments.m00}, {"v", moments.m01 / moments.m00},
               {"radius", std::sqrt(moments.m00 / CV_PI)}, {"found", 1.0}};
      }
      out.merge(make_image(std::move(mask)));
    } else {
      out.merge(make_image(SyntheticFrame{fallback_u, fallback_v, 3.85, 0}));
    }
#else
    const auto* frame = paperboat::toolkit::get_handle<SyntheticFrame>(in, "image", "image");
    if (frame) out = {{"u", frame->u}, {"v", frame->v}, {"radius", std::max(3.0, frame->radius)}, {"found", 1.0}};
    out.merge(make_image(SyntheticFrame{fallback_u, fallback_v, 3.85, 0}));
#endif
    return out;
  }
};

// An alpha-beta tracker in image space; the world point comes from the camera mapping.
class Tracker final : public Block {
 public:
  Values step(const Context& ctx, const Values& in) override {
    const double u = paperboat::get_or(in, "u", 160.0);
    const double v = paperboat::get_or(in, "v", 120.0);
    const double dt = std::max(ctx.dt, 1e-4);
    if (!init_) {
      pu_ = u;
      pv_ = v;
      du_ = dv_ = 0.0;
      init_ = true;
    } else {
      const double predicted_u = pu_ + du_ * dt;
      const double predicted_v = pv_ + dv_ * dt;
      const double error_u = u - predicted_u;
      const double error_v = v - predicted_v;
      pu_ = predicted_u + alpha_ * error_u;
      pv_ = predicted_v + alpha_ * error_v;
      du_ += beta_ * error_u / dt;
      dv_ += beta_ * error_v / dt;
    }
    // A rail or mallet hit reverses one image velocity component.
    const bool flip_u = std::abs(du_) > 40.0 && du_ * last_du_ < 0.0;
    const bool flip_v = std::abs(dv_) > 40.0 && dv_ * last_dv_ < 0.0;
    if (init_last_ && (flip_u || flip_v)) {
      ++bounces_;
      ctx.log("tracker: direction change (" + std::to_string(bounces_) + ")");
    }
    last_du_ = du_;
    last_dv_ = dv_;
    init_last_ = true;
    return {
        {"u", pu_}, {"v", pv_}, {"du", du_}, {"dv", dv_},
        {"x", (pu_ - 160.0) / 110.0}, {"z", (pv_ - 120.0) / 110.0},
        {"bounces", static_cast<double>(bounces_)},
    };
  }

 private:
  static constexpr double alpha_ = 0.55;
  static constexpr double beta_ = 0.22;
  bool init_ = false;
  double pu_ = 0.0, pv_ = 0.0, du_ = 0.0, dv_ = 0.0;
  double last_du_ = 0.0, last_dv_ = 0.0;
  bool init_last_ = false;
  int bounces_ = 0;
};

// The truth, for the Board's numeric comparison.
class Truth final : public Block {
 public:
  Values step(const Context& ctx, const Values&) override {
    auto* state = static_cast<AirHockey*>(ctx.state);
    return {{"x", state->x()}, {"z", state->z()}, {"u", state->u()}, {"v", state->v()},
            {"bounces", static_cast<double>(state->bounces())}, {"frames", static_cast<double>(state->frames())}};
  }
};

// Degraded Image view: no OpenCV means no picture, so it says so instead of showing a blank tile.
class ViewFallback final : public Block {
 public:
  Values step(const Context&, const Values&) override {
#ifdef PAPERBOAT_HAS_OPENCV
    return {{"value", std::string("OpenCV image")}};
#else
    return {{"value", std::string("camera offline (OpenCV not built)")}};
#endif
  }
};

}  // namespace

void register_tracker(paperboat::Registry& registry) {
  registry.add(paperboat::define_block<Camera>(
      "air-hockey", {.type = "camera", .label = "Overhead Camera", .kind = Kind::Source,
                     .inputs = {}, .outputs = {{"image", "image"}, {"truth_u"}, {"truth_v"},
                                                 {"bounces"}, {"frames"}},
                     .params = {}, .description = "A synthetic overhead camera and the puck's truth."}));
  registry.add(paperboat::define_block<Vision>(
      "air-hockey", {.type = "vision", .label = "Synthetic Vision", .kind = Kind::Function,
                     .inputs = {{"image", "image"}, {"truth_u"}, {"truth_v"}},
                     .outputs = {{"image", "image"}, {"u"}, {"v"}, {"radius"}, {"found"}},
                     .params = {}, .description = "Degraded path: pass the camera's truth as a centroid."}));
  registry.add(paperboat::define_block<Tracker>(
      "air-hockey", {.type = "tracker", .label = "Puck Tracker", .kind = Kind::Probe,
                     .inputs = {{"u"}, {"v"}, {"radius"}},
                     .outputs = {{"u"}, {"v"}, {"du"}, {"dv"}, {"x"}, {"z"}, {"bounces"}},
                     .params = {}, .description = "An alpha-beta filter in image space."}));
  registry.add(paperboat::define_block<Truth>(
      "air-hockey", {.type = "truth", .label = "Puck Truth", .kind = Kind::Probe,
                     .inputs = {}, .outputs = {{"x"}, {"z"}, {"u"}, {"v"}, {"bounces"}, {"frames"}},
                     .params = {}, .description = "The simulated puck's true state."}));
  registry.add(paperboat::define_block<ViewFallback>(
      "air-hockey", {.type = "view_fallback", .label = "Image View (degraded)", .kind = Kind::Monitor,
                     .inputs = {{"image", "image"}}, .outputs = {}, .params = {}, .instrument = "image",
                     .description = "A placeholder Image view when OpenCV is not built."}));
}

}  // namespace air_hockey
