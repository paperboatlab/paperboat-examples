// 02-cart-pole-cpp: Modernized Inverted Pendulum Benchmark

#include <paperboat/sdk.hpp>

#include "domain/cart_pole.hpp"

int main(int argc, char** argv) {
  static const paperboat::Registry registry = [] {
    paperboat::Registry r = paperboat::builtins();
    cart_pole::register_cart_pole(r);
    return r;
  }();
  static const paperboat::Catalog catalog = paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR, registry);
  return paperboat::main({.engine = "02-cart-pole-cpp", .catalog = &catalog}, argc, argv, 8766);
}
