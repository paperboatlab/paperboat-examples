// 08-air-hockey-tracker-cpp: a top-down air-hockey puck tracker.
//
// The full graph uses the optional OpenCV toolkit blocks (HSV range, open/close, centroid,
// image view). Without OpenCV the backend runs `descriptor-degraded.toml`, whose synthetic
// camera/vision path keeps the same tracker and dashboard useful.

#include <paperboat/sdk.hpp>

#include "domain/state.hpp"
#include "domain/vision.hpp"

#ifdef PAPERBOAT_HAS_OPENCV
#include <paperboat/toolkit/opencv.hpp>
#endif

int main(int argc, char** argv) {
  static const paperboat::Registry registry = [] {
    paperboat::Registry r = paperboat::builtins();
#ifdef PAPERBOAT_HAS_OPENCV
    paperboat::toolkit::opencv::register_opencv(r);
#endif
    air_hockey::register_tracker(r);
    return r;
  }();
#ifdef PAPERBOAT_HAS_OPENCV
  static const paperboat::Catalog catalog = paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR, registry);
#else
  static const paperboat::Catalog catalog = paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR_DEGRADED, registry);
#endif
  const paperboat::Backend backend{
      .engine = "08-air-hockey-tracker-cpp",
      .catalog = &catalog,
      .state = [] { return std::make_unique<air_hockey::AirHockey>(); },
      .view = {{"mode", "3d"}, {"camera", {{"eye", {2.4, 2.9, 2.4}}, {"target", {0, 0.1, 0}}}}},
      .run = {.dt = 1.0 / 60.0, .duration = 8.0, .emit_every = 2, .speed = 2.0},
  };
  return paperboat::main(backend, argc, argv, 8772);
}
