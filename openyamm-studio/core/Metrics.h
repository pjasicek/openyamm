#pragma once

#include "core/Json.h"
#include "core/MapLoad.h"

namespace OpenYAMM::Studio
{
struct MetricsOptions
{
    // Walk the map (core/Reachability) for the reachable share; seconds per indoor map.
    bool withReachability = false;
    // The asset root's engine/data_tables/decoration_data.txt, to count the decorations that carry a light (wall
    // torches, braziers); empty: they are not counted.
    std::string decorationTableText;
};

// The comparison metrics of devdocs/map_studio/CALIBRATION.md, computed the same way for an original map and for a
// build: structure, scale, mechanisms, density, palette and play. Written as one JSON object of numbers and short
// lists; a calibration round compares two of them.
void writeMetricsJson(const LoadedMap &map, const MetricsOptions &options, JsonWriter &writer);
}
