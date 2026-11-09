// Example Paperboat backend: a double pendulum on a cart with an unknown payload.
//
// Three stories run in order (GUIDELINES §6): identify the payload by gray-box recursive
// least squares, swing the links up by energy shaping, and balance them with an LQR whose
// gain comes from the estimated payload. The plant, the estimator and the controllers live
// in domain/; the sequence and the wiring live in descriptor.toml.

#include <paperboat/sdk.hpp>

#include "domain/pendulum.hpp"

int main(int argc, char** argv) {
  static const paperboat::Registry registry = [] {
    paperboat::Registry r = paperboat::builtins();
    double_pendulum::register_pendulum(r);
    return r;
  }();
  static const paperboat::Catalog catalog = paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR, registry);
  const paperboat::Backend backend{.engine = "cpp-double-pendulum",
                                   .catalog = &catalog,
                                   .run = {.dt = 0.01, .duration = 45.0, .emit_every = 4}};
  return paperboat::main(backend, argc, argv, 8767);
}
