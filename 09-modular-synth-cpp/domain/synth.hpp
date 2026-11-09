#pragma once

#include <array>

#include <paperboat/sdk.hpp>

namespace synth {

constexpr int kVoices = 6;

// The shared state: what the six voices are doing now, and the Eurorack scene.
class Synth final : public paperboat::DomainState {
 public:
  std::optional<std::string> step(const paperboat::Context& ctx) override;
  std::optional<std::string> summary() const override;
  std::vector<paperboat::Entity> entities() const override;
  std::vector<paperboat::Entity> patch() const override;

  std::array<double, kVoices> levels{};
  double mix = 0.0;
  double rms = 0.0;
  double peak = 0.0;
  double lfo = 0.0;
  int frames = 0;
};

void register_synth(paperboat::Registry& registry);

}  // namespace synth
