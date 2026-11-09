// 09-modular-synth-cpp: a six-voice polyphonic Eurorack synthesizer.
//
// Vector wires carry one control voltage and one gate per voice; the VCO, ADSR and VCA
// modules run elementwise over that vector, the VCF filters each voice, and the mixer feeds
// the Board's multi-channel Scope. The Station page is a walnut-and-aluminium Eurorack case.

#include <paperboat/sdk.hpp>

#include "domain/synth.hpp"

int main(int argc, char** argv) {
  static const paperboat::Registry registry = [] {
    paperboat::Registry r = paperboat::builtins();
    synth::register_synth(r);
    return r;
  }();
  static const paperboat::Catalog catalog = paperboat::load_descriptor_file(PAPERBOAT_DESCRIPTOR, registry);
  const paperboat::Backend backend{
      .engine = "09-modular-synth-cpp",
      .catalog = &catalog,
      .state = [] { return std::make_unique<synth::Synth>(); },
      .view = {{"mode", "3d"}, {"camera", {{"eye", {0.4, 1.4, 4.2}}, {"target", {0, 0.55, 0}}}}},
      .run = {.dt = 1.0 / 60.0, .duration = 6.0, .emit_every = 2},
  };
  return paperboat::main(backend, argc, argv, 8773);
}
