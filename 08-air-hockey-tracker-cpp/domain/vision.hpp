#pragma once

#include <paperboat/sdk.hpp>

namespace air_hockey {

// Adds the camera, the degraded synthetic vision path, the tracker and the truth probe
// under the "air-hockey" package. The full OpenCV descriptor uses the toolkit's own
// hsv_range/open/close/centroid/view blocks instead.
void register_tracker(paperboat::Registry& registry);

}  // namespace air_hockey
