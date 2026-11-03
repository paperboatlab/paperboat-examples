// Example Paperboat backend: count and sort the parts in a photo with classic image
// processing. Not a simulation: the flow is evaluated once.
//
// A simple backend on the SDK (GUIDELINES §6.1). The domain is descriptor.toml (the
// opencv and dashboard packages, the starter station and graph) plus one block of its own,
// Count parts, defined in code (domain/). Gray, blur, threshold, morphology and Image view
// are the toolkit's opencv package; the photo is an Image station object.

#include <paperboat/sdk.hpp>
#include <paperboat/toolkit/opencv.hpp>

#include "domain/parts.hpp"

int main(int argc, char** argv) {
  // Static: catalog entries point into the registry, so both live as long as the server.
  static const paperboat::Registry registry = [] {
    paperboat::Registry r = paperboat::builtins();
    paperboat::toolkit::opencv::register_opencv(r);
    parts::register_parts(r);
    return r;
  }();
  static const paperboat::Catalog catalog = paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR, registry);
  const paperboat::Backend backend{
      .engine = "cpp-parts",
      .catalog = &catalog,
      .view = {{"mode", "2d"}, {"center", {0, 0}}, {"height", 5.6}},  // the photo; results go to the Dashboard
      .run = {.mode = paperboat::RunSettings::Mode::Once},
  };
  return paperboat::main(backend, argc, argv, 8770);
}
