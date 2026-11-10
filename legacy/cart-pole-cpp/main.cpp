// Example Paperboat backend: cart-poles balanced by PID blocks.
//
// A simple backend on the SDK (GUIDELINES §6.1). The domain is descriptor.toml, next to
// this file (the signal, math, control and dashboard packages, the starter station and
// graph), plus one station object of its own, the Cart-pole, defined in code (domain/):
// its physics, how it's drawn, and the linked block a flow drives it through.

#include <paperboat/sdk.hpp>

#include "paperboat/toolkit/control.hpp"
#include "domain/cart_pole.hpp"

int main(int argc, char** argv) {
  // Static: catalog entries point into the registry, so both live as long as the server.
  static const paperboat::Registry registry = [] {
    paperboat::Registry r = paperboat::builtins();
    paperboat::toolkit::control::register_control(r);
    cart_pole::register_cart_pole(r);
    return r;
  }();
  static const paperboat::Catalog catalog = paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR, registry);
  return paperboat::main({.engine = "cpp-cartpole", .catalog = &catalog}, argc, argv, 8766);
}
