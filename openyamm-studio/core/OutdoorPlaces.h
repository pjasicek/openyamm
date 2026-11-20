#pragma once

#include "core/OutdoorLowering.h"
#include "core/Project.h"

#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// What stands on the land of an outdoor map beside its buildings: decorations scattered by kind and number over
// the sketch's `scatter` areas, and the spawn points of its encounter `areas`. Every place is chosen by a fixed
// rule from the sketch alone (no random numbers: the same sketch gives the same places), on land a thing can stand
// on: never in water or on its shore, on a road or under a building; spawn points also not on ground too steep to
// walk.

struct OutdoorPlacedDecoration
{
    // The decoration's internal name and its number as an ODM stores it (its row of decoration_data.txt less 1).
    std::string name;
    int listId = 0;
    // World units, standing on the terrain.
    int x = 0;
    int y = 0;
    int z = 0;
    // The `id` of the scatter entry it comes from (empty for none), and the number events change it by (filled by
    // the build: every decoration of one id carries the same, as the shipped maps' forests do).
    std::string target;
    int number = 0;
    // The scatter entry it comes from (its index in `scatter`), -1 for none; the event a click on it runs (the
    // entry's `event`, filled by the build), 0 for none.
    int entry = -1;
    int event = 0;
};

struct OutdoorPlacedSpawn
{
    // The sketch area's id (a plan population).
    std::string area;
    // The map's monster slot the marker spawns from, 1 to 3.
    int slot = 1;
    int x = 0;
    int y = 0;
    int z = 0;
    // What the marker spawns, as the maps store it: 3 monsters of the slot, 2 an item of a treasure level
    // (`slot` is then the level, 1 to 7).
    int type = 3;
};

struct OutdoorPlaces
{
    std::vector<OutdoorPlacedDecoration> decorations;
    std::vector<OutdoorPlacedSpawn> spawns;
};

// `decorationTable`: the text of engine/data_tables/decoration_data.txt, which names the decorations; empty when
// no asset root is at hand (the scatter is then left out, with a warning). False with issues when the sketch asks
// for what cannot be placed.
bool placeOutdoorThings(
    const Project &project,
    const LoweredOutdoorMap &lowered,
    const std::string &decorationTable,
    OutdoorPlaces &places,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings,
    const std::vector<std::array<double, 4>> &keepOff = {});
}
