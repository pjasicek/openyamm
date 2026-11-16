#pragma once

#include "core/MapLoad.h"
#include "core/OutdoorCompare.h"

#include <filesystem>
#include <string>

namespace OpenYAMM::Studio
{
// `oymap compare` on two outdoor maps that are read already (core/OutdoorCompare): prints the report or its
// summary and, with an output folder, writes report.json, differences.json, the pictures and shots.yml. Returns
// the process exit code. `rimByNodes`: the land beyond the playable square is judged node by node with the rest
// (the reading before 2026-11-13), not by its skyline.
// Two outdoor maps read already, compared (core/OutdoorCompare) with the world's tile tables: false with a message
// when the world cannot be opened or a side is no outdoor map. `warning`: the tile table could not be read (ground,
// water and roads then compare nothing).
bool compareLoadedOutdoorMaps(
    const std::filesystem::path &assetRoot,
    const std::string &world,
    const LoadedMap &original,
    const LoadedMap &rebuilt,
    OutdoorCompareResult &result,
    std::string &errorMessage,
    std::string &warning,
    bool rimByNodes = false);

int runOutdoorCompare(
    const std::filesystem::path &assetRoot,
    const std::string &world,
    const LoadedMap &original,
    const LoadedMap &rebuilt,
    const std::string &output,
    bool asJson,
    bool rimByNodes = false);
}
