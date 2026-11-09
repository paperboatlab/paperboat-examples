# Tutorial 09: Modular Synthesizer

> **Level**: 09 · Expert  
> **Domain**: Music Production & Audio Technology  
> **Language**: C++  
> **Port**: 8773  
> **UI Cockpit**: Lookout Mode (`Alt+L`)  
> **Core Concepts**: vector wires `[6]`, polyphonic CV/gate, per-voice ADSR/VCA/VCF, multi-channel Scope, Eurorack scene.

---

## 1. Overview

A six-voice polyphonic synthesizer on vector wires. Each wire carries one element per voice —
six control voltages, six gates, six audio samples.

- **Chord CV / Gate** — root note plus a major/minor/fifths/cluster chord; six CVs and six
  gates out.
- **VCO** — six oscillators (sine, saw or square) with an LFO detune input.
- **ADSR** — one attack/decay/sustain/release envelope per voice.
- **VCA** — audio × envelope, voice by voice.
- **VCF** — a resonant low-pass ladder with one state per voice; the LFO sweeps its cutoff.
- **Stereo Mixer** — sums the voices with soft clipping and reports RMS and peak.

The Scope receives the VCF output vector as one channel per component, plus the master mix,
so the Board shows six voices and the mix together. An **Audio Out** block renders the same
six voices at 44.1 kHz into a PCM vector; the Board's **Speaker** instrument plays it through
Web Audio. Browsers keep audio suspended until a click, so press **Click for sound** once.

---

## 2. Cockpit exploration

```sh
./bin/paperboat run 09
# http://localhost:3047/?backend=ws://localhost:8773
```

1. **Lookout mode** (`Alt+L`) — the Board alone, full screen, for the Scope and readouts.
2. **Scope** — six channel traces from the VCF plus the summed mix (input `b`), with the
   normal zoom, cursors and triggers.
3. **Variables** (`Alt+V`) — `root_note`, `cutoff` and `resonance` are bound to the chord,
   cutoff sum and VCF.
4. **Flow** — open the `6-Voice Voice Card` subsystem to see VCO → VCA with the ADSR feeding
   its envelope; the `VCF & LFO` frame shows the modulation path.
5. **Speaker** — press **Click for sound** on the Board once (browsers keep audio suspended
   until a click); the backend sends one PCM buffer per two control passes and the
   instrument queues them back to back.

`Mixer` writes the six levels into the domain state; the station object patches only the VU
bars each frame.

---

## 3. Files

```text
09-modular-synth-cpp/
├── backend.toml          # format = 0, port 8773, solver = rk4
├── descriptor.toml       # six-voice vector graph, variables, dashboard
├── CMakeLists.txt        # native C++ linking paperboat::core
├── main.cpp              # paperboat::main, domain state factory
├── domain/
│   ├── synth.hpp         # Synth state: levels, mix, RMS, scene
│   └── synth.cpp         # Chord, VCO, ADSR, VCA, VCF, LFO, Mixer, AudioOut, VoiceProbe
├── expected.json         # golden run: 6 voices, final RMS/peak
└── README.md
```

Vector ports are declared with `paperboat::vector_port("cv", 6)`; blocks read a `List` input
with `paperboat::get_if<List>` and return a `List` output. The engine checks the declared
dimension at run time.

---

## 4. Verification

```sh
./paperboat/bin/paperboat check paperboat-examples/09-modular-synth-cpp
python3 paperboat/protocol/golden.py --examples paperboat-examples 09-modular-synth-cpp
```
