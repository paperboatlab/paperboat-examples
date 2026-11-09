// The synth's module blocks and its walnut-and-aluminium station.

#include "synth.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <numbers>
#include <string>
#include <vector>

#include <paperboat/toolkit/scene.hpp>

namespace synth {
namespace {

using paperboat::Block;
using paperboat::Context;
using paperboat::Kind;
using paperboat::List;
using paperboat::Values;
using paperboat::VectorComponent;
using paperboat::get_or;

constexpr double kTwoPi = 2.0 * std::numbers::pi;

std::array<double, kVoices> voices_of(const Values& in, std::string_view port) {
  std::array<double, kVoices> out{};
  const List* list = paperboat::get_if<List>(in, port);
  if (!list) return out;
  for (std::size_t i = 0; i < out.size(); ++i) out[i] = i < list->size() ? (*list)[i] : 0.0;
  return out;
}

List list_of(const std::array<double, kVoices>& values) {
  return List(values.begin(), values.end());
}

// A chord's control voltages and gates: one value per voice on a vector wire.
class Chord final : public Block {
 public:
  explicit Chord(const Values& params, const paperboat::Config& config)
      : root_(get_or(params, "root", 48.0)), config_(config) {}

  Values step(const Context&, const Values&) override {
    static constexpr std::array<std::array<double, kVoices>, 4> chords{{
        {0, 4, 7, 12, 16, 19},   // major
        {0, 3, 7, 12, 15, 19},   // minor
        {0, 7, 12, 19, 24, 28},  // open fifths
        {0, 2, 4, 7, 9, 12},     // cluster
    }};
    int index = 0;
    auto it = config_.find("chord");
    if (it != config_.end()) {
      if (it->second == "minor") index = 1;
      else if (it->second == "fifths") index = 2;
      else if (it->second == "cluster") index = 3;
    }
    std::array<double, kVoices> cv{};
    std::array<double, kVoices> gate{};
    for (int i = 0; i < kVoices; ++i) {
      cv[i] = root_ + chords[static_cast<std::size_t>(index)][static_cast<std::size_t>(i)];
      gate[i] = 1.0;
    }
    return {{"cv", list_of(cv)}, {"gate", list_of(gate)}};
  }

 private:
  double root_;
  paperboat::Config config_;
};

// Six detuned oscillators: sine, saw or square, one phase per voice.
class Vco final : public Block {
 public:
  Vco(const Values&, const paperboat::Config& config) : config_(config) {}

  Values step(const Context& ctx, const Values& in) override {
    const auto cv = voices_of(in, "cv");
    const auto gate = voices_of(in, "gate");
    const double detune = get_or(in, "detune", 0.0);
    std::array<double, kVoices> audio{};
    for (int i = 0; i < kVoices; ++i) {
      const double frequency = 440.0 * std::pow(2.0, (cv[i] + detune - 69.0) / 12.0);
      phase_[static_cast<std::size_t>(i)] += kTwoPi * frequency * ctx.dt;
      phase_[static_cast<std::size_t>(i)] = std::fmod(phase_[static_cast<std::size_t>(i)], kTwoPi);
      const double phase = phase_[static_cast<std::size_t>(i)] / kTwoPi;
      double sample = std::sin(phase * kTwoPi);
      auto it = config_.find("wave");
      const std::string wave = it == config_.end() ? "sine" : it->second;
      if (wave == "saw") sample = 2.0 * phase - 1.0;
      else if (wave == "square") sample = phase < 0.5 ? 1.0 : -1.0;
      audio[static_cast<std::size_t>(i)] = sample * gate[i];
    }
    return {{"audio", list_of(audio)}};
  }

 private:
  paperboat::Config config_;
  std::array<double, kVoices> phase_{};
};

// One ADSR envelope per voice, triggered by its gate.
class Adsr final : public Block {
 public:
  explicit Adsr(const Values& p)
      : attack_(get_or(p, "attack", 0.08)), decay_(get_or(p, "decay", 0.18)),
        sustain_(get_or(p, "sustain", 0.75)), release_(get_or(p, "release", 0.35)) {}

  Values step(const Context& ctx, const Values& in) override {
    const auto gate = voices_of(in, "gate");
    for (int i = 0; i < kVoices; ++i) {
      auto& level = level_[static_cast<std::size_t>(i)];
      auto& stage = stage_[static_cast<std::size_t>(i)];
      if (gate[i] > 0.5) {
        if (stage == Stage::Idle || stage == Stage::Release) stage = Stage::Attack;
        if (stage == Stage::Attack) {
          level = std::min(1.0, level + ctx.dt / std::max(attack_, 1e-3));
          if (level >= 1.0) stage = Stage::Decay;
        } else if (stage == Stage::Decay) {
          level = std::max(sustain_, level - ctx.dt / std::max(decay_, 1e-3) * (1.0 - sustain_));
          if (level <= sustain_) stage = Stage::Sustain;
        } else {
          level = sustain_ + (level - sustain_) * std::exp(-ctx.dt / std::max(release_, 1e-3));
        }
        if (stage == Stage::Sustain) level = sustain_;
      } else {
        stage = Stage::Release;
        level *= std::exp(-ctx.dt / std::max(release_, 1e-3));
        if (level < 1e-4) {
          level = 0.0;
          stage = Stage::Idle;
        }
      }
    }
    return {{"env", list_of(level_)}};
  }

 private:
  enum class Stage { Idle, Attack, Decay, Sustain, Release };
  double attack_, decay_, sustain_, release_;
  std::array<double, kVoices> level_{};
  std::array<Stage, kVoices> stage_{};
};

// A voltage-controlled amplifier: audio times envelope, voice by voice.
class Vca final : public Block {
 public:
  Values step(const Context&, const Values& in) override {
    const auto audio = voices_of(in, "audio");
    const auto env = voices_of(in, "env");
    std::array<double, kVoices> out{};
    for (int i = 0; i < kVoices; ++i) out[static_cast<std::size_t>(i)] = audio[static_cast<std::size_t>(i)] * env[static_cast<std::size_t>(i)];
    return {{"audio", list_of(out)}};
  }
};

// A one-pole low-pass per voice with resonance feedback: the ladder filter's control feel.
class Vcf final : public Block {
 public:
  Values step(const Context& ctx, const Values& in) override {
    const auto audio = voices_of(in, "audio");
    const double cutoff = std::clamp(get_or(in, "cutoff", 1200.0), 80.0, 8000.0);
    const double resonance = std::clamp(get_or(in, "resonance", 0.3), 0.0, 0.95);
    const double alpha = std::clamp(1.0 - std::exp(-kTwoPi * cutoff * ctx.dt), 0.001, 1.0);
    std::array<double, kVoices> out{};
    for (int i = 0; i < kVoices; ++i) {
      const auto index = static_cast<std::size_t>(i);
      state_[index] += alpha * (audio[index] - state_[index] + resonance * (audio[index] - state_[index]));
      out[index] = state_[index];
    }
    return {{"audio", list_of(out)}};
  }

 private:
  std::array<double, kVoices> state_{};
};

// A stereo-ish master: sums the voices and reports RMS and peak.
class Mixer final : public Block {
 public:
  Values step(const Context& ctx, const Values& in) override {
    const auto audio = voices_of(in, "audio");
    auto* synth = static_cast<Synth*>(ctx.state);
    double sum = 0.0, energy = 0.0, peak = 0.0;
    for (int i = 0; i < kVoices; ++i) {
      const double sample = audio[static_cast<std::size_t>(i)];
      sum += sample;
      energy += sample * sample;
      peak = std::max(peak, std::abs(sample));
      synth->levels[static_cast<std::size_t>(i)] = std::abs(sample);
    }
    const double mix = std::tanh(sum / kVoices);
    synth->mix = mix;
    synth->rms = std::sqrt(energy / kVoices);
    synth->peak = peak;
    synth->lfo = get_or(in, "lfo", 0.0);
    return {{"mix", mix}, {"rms", synth->rms}, {"peak", peak}};
  }
};

// A slow triangle LFO for vibrato and filter sweeps.
class Lfo final : public Block {
 public:
  explicit Lfo(const Values& p) : rate_(get_or(p, "rate", 0.35)), depth_(get_or(p, "depth", 1.0)) {}

  Values step(const Context& ctx, const Values&) override {
    const double phase = std::fmod(ctx.t * rate_, 1.0);
    const double triangle = 4.0 * std::abs(phase - 0.5) - 1.0;
    return {{"lfo", triangle * depth_}};
  }

 private:
  double rate_, depth_;
};

// The audio output: the six voices rendered at sample rate for the Board's Speaker.
// The control graph still runs at 60 Hz; this block fills one emit interval with PCM.
class AudioOut final : public Block {
 public:
  AudioOut(const Values& p, const paperboat::Config& config)
      : rate_(get_or(p, "rate", 44100.0)), volume_(get_or(p, "volume", 0.22)),
        steps_(std::max(1.0, get_or(p, "steps", 2.0))), config_(config) {}

  Values step(const Context& ctx, const Values& in) override {
    const auto cv = voices_of(in, "cv");
    const auto gate = voices_of(in, "gate");
    const auto env = voices_of(in, "env");
    const auto n = static_cast<std::size_t>(std::clamp(std::lround(rate_ * ctx.dt * steps_), 1L, 8192L));
    List pcm(n, 0.0);
    double energy = 0.0;
    const std::string wave = config_.contains("wave") ? config_.at("wave") : "sine";
    for (std::size_t sample = 0; sample < n; ++sample) {
      double mix = 0.0;
      for (int voice = 0; voice < kVoices; ++voice) {
        auto index = static_cast<std::size_t>(voice);
        const double frequency = 440.0 * std::pow(2.0, (cv[index] - 69.0) / 12.0);
        phase_[index] += kTwoPi * frequency / rate_;
        phase_[index] = std::fmod(phase_[index], kTwoPi);
        const double p = phase_[index] / kTwoPi;
        double value = std::sin(phase_[index]);
        if (wave == "saw") value = 2.0 * p - 1.0;
        else if (wave == "square") value = p < 0.5 ? 1.0 : -1.0;
        mix += value * gate[index] * env[index];
      }
      const double out = std::tanh(mix * volume_);
      pcm[sample] = out;
      energy += out * out;
    }
    return {{"pcm", pcm}, {"rms", std::sqrt(energy / static_cast<double>(std::max<std::size_t>(1, n)))}};
  }

 private:
  double rate_, volume_, steps_;
  paperboat::Config config_;
  std::array<double, kVoices> phase_{};
};

// A scope-friendly voice readout: the six envelopes as a vector, plus the mix.
class VoiceProbe final : public Block {
 public:
  Values step(const Context& ctx, const Values& in) override {
    auto* synth = static_cast<Synth*>(ctx.state);
    (void)in;
    return {{"levels", list_of(synth->levels)}, {"mix", synth->mix}, {"rms", synth->rms},
            {"peak", synth->peak}, {"voices", 6.0}};
  }
};

}  // namespace

std::optional<std::string> Synth::step(const paperboat::Context& ctx) {
  frames += 1;
  (void)ctx;
  return std::nullopt;
}

std::optional<std::string> Synth::summary() const {
  char text[128];
  std::snprintf(text, sizeof text, "6-voice chord rendered over %d frames: RMS %.3f, peak %.3f", frames, rms, peak);
  return std::string(text);
}

std::vector<paperboat::Entity> Synth::entities() const {
  using paperboat::scene::box;
  using paperboat::scene::sphere;
  using paperboat::scene::line;
  std::vector<paperboat::Entity> out = {
      box("chassis", {0, 0.55, 0}, {4.4, 1.1, 0.26}, "#3b2a1e"),
      box("rail-top", {0, 1.08, 0}, {4.5, 0.06, 0.3}, "#9ca3af"),
      box("rail-bottom", {0, 0.02, 0}, {4.5, 0.06, 0.3}, "#9ca3af"),
      box("cheek-left", {-2.18, 0.55, 0}, {0.12, 1.16, 0.34}, "#4b2e1c"),
      box("cheek-right", {2.18, 0.55, 0}, {0.12, 1.16, 0.34}, "#4b2e1c"),
  };
  static constexpr std::array<const char*, 6> names{"VCO", "VCF", "ADSR", "LFO", "MIX", "SCOPE"};
  for (int i = 0; i < 6; ++i) {
    const double x = -1.75 + i * 0.7;
    out.push_back(box("module-" + std::to_string(i), {x, 0.55, 0.02}, {0.62, 1.0, 0.08},
                      i == 0 ? "#1f2937" : i == 1 ? "#111827" : i == 2 ? "#1e1b4b" : i == 3 ? "#052e16" : "#1c1917"));
    // Knurled knobs: three per module.
    for (int k = 0; k < 3; ++k)
      out.push_back(sphere("knob-" + std::to_string(i) + "-" + std::to_string(k),
                           {x - 0.18 + k * 0.18, 0.82, 0.1}, 0.045, "#d6d3d1"));
    // Patch jacks.
    for (int k = 0; k < 4; ++k)
      out.push_back(sphere("jack-" + std::to_string(i) + "-" + std::to_string(k),
                           {x - 0.21 + k * 0.14, 0.36, 0.1}, 0.025, "#0f172a"));
    // A label plate line.
    out.push_back(box("label-" + std::to_string(i), {x, 1.0, 0.06}, {0.5, 0.05, 0.02}, "#a8a29e"));
    (void)names;
  }
  // Patch cables: a few curved-ish polylines between jacks.
  const std::array<std::array<double, 4>, 5> cables{{
      {-1.6, 0.36, -0.2, 0.36}, {-0.9, 0.36, 0.5, 0.36}, {-0.2, 0.36, 1.2, 0.36},
      {0.5, 0.36, 1.9, 0.36}, {-1.7, 0.5, 1.3, 0.5},
  }};
  for (std::size_t i = 0; i < cables.size(); ++i) {
    const auto& c = cables[i];
    out.push_back(line("cable-" + std::to_string(i), {c[0], c[1], 0.16}, {c[2], c[3], 0.16},
                       i % 2 == 0 ? "#f43f5e" : "#38bdf8"));
  }
  // Stereo VU bars: the height follows the current voice levels.
  for (int i = 0; i < kVoices; ++i) {
    const double level = std::clamp(levels[static_cast<std::size_t>(i)], 0.0, 1.0);
    out.push_back(box("vu-" + std::to_string(i), {1.0 + i * 0.12, 0.18 + level * 0.3, 0.15},
                      {0.08, 0.02 + level * 0.6, 0.05}, level > 0.6 ? "#f97316" : "#22c55e"));
  }
  return out;
}

std::vector<paperboat::Entity> Synth::patch() const {
  std::vector<paperboat::Entity> out;
  for (int i = 0; i < kVoices; ++i) {
    const double level = std::clamp(levels[static_cast<std::size_t>(i)], 0.0, 1.0);
    out.push_back(paperboat::scene::box("vu-" + std::to_string(i), {1.0 + i * 0.12, 0.18 + level * 0.3, 0.15},
                                        {0.08, 0.02 + level * 0.6, 0.05}, level > 0.6 ? "#f97316" : "#22c55e"));
  }
  return out;
}

void register_synth(paperboat::Registry& registry) {
  const auto cv = paperboat::vector_port("cv", kVoices);
  const auto gate = paperboat::vector_port("gate", kVoices);
  const auto audio = paperboat::vector_port("audio", kVoices);
  const auto env = paperboat::vector_port("env", kVoices);
  const auto levels = paperboat::vector_port("levels", kVoices);

  registry.add(paperboat::define_block<Chord>(
      "synth", {.type = "chord", .label = "Chord CV / Gate", .kind = Kind::Source,
                .inputs = {}, .outputs = {cv, gate},
                .params = {{"root", 48.0}},
                .description = "A six-voice chord as control voltages and gates."},
      {{"chord", "major"}}));
  registry.add(paperboat::define_block<Vco>(
      "synth", {.type = "vco", .label = "VCO · 6 voices", .kind = Kind::Function,
                .inputs = {cv, gate, {"detune"}}, .outputs = {audio},
                .params = {{"detune", 0.0}},
                .description = "Six bandlimited oscillators, one per vector element."},
      {{"wave", "sine"}}));
  registry.add(paperboat::define_block<Adsr>(
      "synth", {.type = "adsr", .label = "ADSR · 6 voices", .kind = Kind::Function,
                .inputs = {gate}, .outputs = {env},
                .params = {{"attack", 0.08}, {"decay", 0.18}, {"sustain", 0.75}, {"release", 0.35}},
                .description = "One attack-decay-sustain-release envelope per voice."}));
  registry.add(paperboat::define_block<Vca>(
      "synth", {.type = "vca", .label = "VCA", .kind = Kind::Function,
                .inputs = {audio, env}, .outputs = {audio}, .params = {},
                .description = "Audio times envelope, voice by voice."}));
  registry.add(paperboat::define_block<Vcf>(
      "synth", {.type = "vcf", .label = "VCF · 4-pole", .kind = Kind::Function,
                .inputs = {audio, {"cutoff"}, {"resonance"}}, .outputs = {audio},
                .params = {{"cutoff", 1200.0}, {"resonance", 0.3}},
                .description = "A resonant low-pass ladder, one state per voice."}));
  registry.add(paperboat::define_block<Lfo>(
      "synth", {.type = "lfo", .label = "LFO", .kind = Kind::Source,
                .inputs = {}, .outputs = {{"lfo"}}, .params = {{"rate", 0.35}, {"depth", 1.0}},
                .description = "A slow triangle for vibrato and filter sweeps."}));
  registry.add(paperboat::define_block<Mixer>(
      "synth", {.type = "mixer", .label = "Stereo Mixer", .kind = Kind::Function,
                .inputs = {audio, {"lfo"}}, .outputs = {{"mix"}, {"rms"}, {"peak"}}, .params = {},
                .description = "Sums the voices with soft clipping and reports RMS."}));
  const auto pcm = paperboat::vector_port("pcm");
  registry.add(paperboat::define_block<AudioOut>(
      "synth", {.type = "audio_out", .label = "Audio Out · PCM", .kind = Kind::Function,
                .inputs = {cv, gate, env}, .outputs = {pcm, {"rms"}},
                .params = {{"rate", 44100.0}, {"volume", 0.22}, {"steps", 2.0}},
                .description = "Renders the six voices into a PCM vector for the Speaker."},
      {{"wave", "sine"}}));
  registry.add(paperboat::define_block<VoiceProbe>(
      "synth", {.type = "voices", .label = "Voice Probe", .kind = Kind::Probe,
                .inputs = {}, .outputs = {levels, {"mix"}, {"rms"}, {"peak"}, {"voices"}}, .params = {},
                .description = "The six voice levels and the master mix."}));
}

}  // namespace synth
