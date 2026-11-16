#pragma once

#include "core/MapLoad.h"

#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Writes a project for a shipped map (PLAN.md section 4, "Import of shipped maps"): an overlay project, whose
// `base` is the map. It holds what the studio derives from the map and what a change would refer to:
//   project.yml   the map card (id, world, kind, base, neighbours the map's exits lead to)
//   plan.yml      indoor: the room graph (a space per sector with a floor to stand on, a link per pair of sectors
//                 joined by a portal, door or open), the arrival and the exits, totals; outdoor: totals only
//   ids.lock.yml  the map's own numbers under stable ids (room:s12, door:d4, evt:e23), so overlays and later
//                 builds keep them
// The geometry stays in the base map: nothing of it is copied. False with a message when a file cannot be written.
bool importMapAsProject(
    const LoadedMap &map,
    const std::filesystem::path &projectDirectory,
    std::vector<std::string> &writtenFiles,
    std::string &errorMessage);
}
