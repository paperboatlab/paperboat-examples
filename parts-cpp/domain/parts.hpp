#pragma once

// The parts domain's own blocks: only what the toolkit doesn't have.

#include <paperboat/sdk.hpp>

namespace parts {

// Adds the domain's package, "parts" (the descriptor's `domain`, so it gets these without
// listing them): parts/count.
void register_parts(paperboat::Registry& registry);

}  // namespace parts
