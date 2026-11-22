#pragma once

#include "core/Json.h"
#include "core/MapLoad.h"

#include <vector>

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

// How far an indoor map's rooms are shaped as caves are (decision D-89, feedback F12: caves built as boxes), per room
// (sector) and for the map. Floor: the share of floor area not level with its room's main floor (sloped, or a level
// piece more than 16 above or below it). Ceiling: the mean distance of the ceiling from its room's main ceiling height
// (area-weighted), and the share not level with it. Walls: the share of wall area that is rough (leaning more than 5
// degrees, or running more than 5 degrees off the 45-degree grid a built room keeps). Portals are left out.
struct CaveShapeRoom
{
    size_t sector = 0;
    double floorArea = 0.0;
    double floorUnevenShare = 0.0;
    double ceilingSpread = 0.0;
    double ceilingUnevenShare = 0.0;
    double wallRoughShare = 0.0;
};

struct CaveShape
{
    double floorUnevenShare = 0.0;
    double ceilingSpread = 0.0;
    double ceilingUnevenShare = 0.0;
    double wallRoughShare = 0.0;
    // The rooms of at least 256 x 256 of floor, the largest first.
    std::vector<CaveShapeRoom> rooms;
};

CaveShape caveShapeOf(const Game::IndoorMapData &indoor);

// The targets a cave or mine map is held to (`identity: {shape: cave}`; measured on MM6-MM8's caves and mines,
// openyamm-studio/README.md "Cave shape"): the map's numbers at or above these.
struct CaveShapeTargets
{
    double floorUnevenShare = 0.0;
    double ceilingSpread = 0.0;
    double wallRoughShare = 0.0;
};

CaveShapeTargets caveShapeTargets();

// The comparison metrics of devdocs/map_studio/CALIBRATION.md, computed the same way for an original map and for a
// build: structure, scale, mechanisms, density, palette and play. Written as one JSON object of numbers and short
// lists; a calibration round compares two of them.
void writeMetricsJson(const LoadedMap &map, const MetricsOptions &options, JsonWriter &writer);
}
