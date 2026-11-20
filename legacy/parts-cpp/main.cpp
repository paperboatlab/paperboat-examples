// Example Paperboat station: count and sort the parts in a photo with classic image
// processing. Not a simulation: the flow is evaluated once.
//
// A simple station on the SDK (GUIDELINES §6.1). The domain is descriptor.toml (the
// opencv and board packages, the starter station and graph) plus one block of its own,
// Count parts, defined in code (domain/). Gray, blur, threshold, morphology and Image view
// are the toolkit's opencv package; the photo is an Image station object.

#include <paperboat/sdk.hpp>

#ifdef PAPERBOAT_HAS_OPENCV
#include <paperboat/toolkit/opencv.hpp>
#include "domain/parts.hpp"
#endif

int main(int argc, char** argv) {
  // Static: catalog entries point into the registry, so both live as long as the server.
  static const paperboat::Registry registry = [] {
    paperboat::Registry r = paperboat::builtins();
#ifdef PAPERBOAT_HAS_OPENCV
    paperboat::toolkit::opencv::register_opencv(r);
    parts::register_parts(r);
#endif
    return r;
  }();
  static const paperboat::Catalog catalog =
      paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR, registry, {.optional_imports = {"opencv"}});
  const paperboat::Station station{
      .engine = "cpp-parts",
      .catalog = &catalog,
      .view = {{"mode", "2d"}, {"center", {0, 0}}, {"height", 5.6}},  // the photo; results go to the Board
      .run = {.mode = paperboat::RunSettings::Mode::Once},
  };
  return paperboat::main(station, argc, argv, 8770);
}
