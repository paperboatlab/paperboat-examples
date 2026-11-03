// Example Paperboat backend: cart-poles balanced by PID blocks.
//
// A simple backend on the SDK (GUIDELINES §6): the domain is its descriptor.toml,
// next to this file, which imports the toolkit's base and control packages and holds the
// starter station and graph. There is no domain code: the cart-pole is the toolkit's
// control/cart-pole station object. A domain with its own blocks or station objects defines
// them in code and adds them to a registry before loading the descriptor (see §6.1 and the
// parts example).

#include <paperboat/sdk.hpp>

int main(int argc, char** argv) {
  // Static: catalog entries point into the registry, so both live as long as the server.
  static const paperboat::Catalog catalog = paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR);
  const paperboat::Backend backend{.engine = "cpp-cartpole", .catalog = &catalog, .run = {}};
  return paperboat::main(backend, argc, argv, 8766);
}
