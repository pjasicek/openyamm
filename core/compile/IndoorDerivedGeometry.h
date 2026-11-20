#pragma once

#include "game/indoor/IndoorMapData.h"

#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
// Moving faces stay outside the static partition tree. The native format also supports static faces
// crossing partition planes in the sector's non-BSP list, preserving their original IDs and event bindings.
bool generateIndoorDerivedGeometry(
    Game::IndoorMapData &geometry,
    const std::vector<uint16_t> &movingFaceIds,
    bool generateBsp,
    bool generateOutlines,
    std::string &errorMessage);
}
