#pragma once

#include <paperboat/sdk.hpp>

namespace cart_pole {

// Adds this domain's Cart-pole station object (and its linked block) to `registry`.
void register_cart_pole(paperboat::Registry& registry);

}  // namespace cart_pole
