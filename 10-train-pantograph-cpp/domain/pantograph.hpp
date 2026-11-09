#pragma once

#include <paperboat/sdk.hpp>

namespace pantograph {

// Adds the articulated pantograph station object and the pneumatic force regulator.
void register_pantograph(paperboat::Registry& registry);

}  // namespace pantograph
