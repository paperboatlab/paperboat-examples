#pragma once

#include <paperboat/sdk.hpp>

namespace double_pendulum {

// Adds this domain's station object and its story blocks to `registry`.
void register_pendulum(paperboat::Registry& registry);

}  // namespace double_pendulum
