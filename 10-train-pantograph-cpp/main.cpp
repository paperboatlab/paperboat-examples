// 10-train-pantograph-cpp: a high-speed pantograph on a compliant catenary.
//
// The Station page is the train roof, articulated pantograph and overhead wire; the Flow
// page is the active pneumatic regulator. Bypass the regulator (Ctrl+Shift+Y or the Board
// switch) to watch the contact force leave its window and the Console report arcing.

#include <paperboat/sdk.hpp>

#include "domain/pantograph.hpp"

int main(int argc, char** argv) {
  static const paperboat::Registry registry = [] {
    paperboat::Registry r = paperboat::builtins();
    pantograph::register_pantograph(r);
    return r;
  }();
  static const paperboat::Catalog catalog = paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR, registry);
  const paperboat::Backend backend{
      .engine = "10-train-pantograph-cpp",
      .catalog = &catalog,
      .view = {{"mode", "3d"}, {"camera", {{"eye", {7.0, 5.6, 8.5}}, {"target", {0.5, 4.6, 0}}}}},
      .run = {.dt = 1.0 / 60.0, .duration = 30.0, .emit_every = 3, .speed = 6.0},
  };
  return paperboat::main(backend, argc, argv, 8774);
}
