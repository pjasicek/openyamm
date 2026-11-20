#pragma once

#include "core/Polygon.h"
#include "core/Project.h"

#include "game/maps/TerrainTileData.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
struct LoweredOutdoorMap;

// The ground of a classic outdoor map: which tile lies on each of its 128 x 128 cells. The rules are read off the
// shipped maps and told at the top of OutdoorGround.cpp.

// Nodes along each side of the ground: the corners of the 128 x 128 cells.
constexpr int OutdoorGroundNodes = 129;

// The local tile numbers of an ODM: plain dirt and its variants, then four sets of 36 tiles.
constexpr uint8_t OutdoorDirtTile = 1;
constexpr int OutdoorFirstSetTile = 90;
constexpr int OutdoorSetTiles = 36;
// The sets as this build lays them, like most shipped maps: first ground, water, second ground, roads.
constexpr int OutdoorFirstGroundSet = 0;
constexpr int OutdoorWaterSet = 1;
constexpr int OutdoorSecondGroundSet = 2;
constexpr int OutdoorRoadSet = 3;

// A road as cells: the cells its line runs through, in order, each sharing a side with the next.
struct OutdoorRoadRun
{
    std::string link;
    // Paved: road tiles. Not paved: a dirt path (bare dirt, no road tile).
    bool paved = true;
    // Cell [x, y] as y * 128 + x.
    std::vector<int> cells;
    // The bed's height at each cell where the sketch gives the road's `bed`; empty where the bed follows the land.
    std::vector<double> bed;
};

// The sketch's roads as cells. Roads that are bridges, boat routes or of a surface that is no road are left out
// (told in `warnings`).
std::vector<OutdoorRoadRun> rasterizeOutdoorRoads(
    const Project &project,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings);

// The road tile (its offset in the road set) of a cell from which of its four neighbours are road: north, east,
// south, west. A bend is the corner piece of a staircase when `staircase` is set (the road runs on diagonally).
int outdoorRoadTileOffset(bool north, bool east, bool south, bool west, bool staircase);

// Clears from a mask of ground nodes (129 x 129, 1 where a ground kind lies) what the tiles cannot show: nodes
// that are in no block of 2 x 2 nodes of the kind (a cell wholly of the kind), and cells where the kind lies on
// two opposite corners only. Only ever clears.
void settleOutdoorGroundMask(std::vector<uint8_t> &mask);

// The offset in a ground set of the tile for a cell whose corners hold dirt as given (north-west, north-east,
// south-west, south-east); 0 for no dirt (the plain tile), -1 for two opposite corners (no such tile).
int outdoorGroundTileOffset(bool northWest, bool northEast, bool southWest, bool southEast);

// The classic ground kinds of a world, as the sketch's `ground[].material` may name them, separated by ", ".
std::string outdoorGroundKindNames(const std::string &world);

// Lays the ground of a lowered map: fills its tiles, tile sets and master tile from the sketch's ground zones, the
// lowered water and the roads. False with issues when the sketch asks for ground the world or the format cannot
// hold.
bool layOutdoorGround(const Project &project, LoweredOutdoorMap &lowered, std::vector<ProjectIssue> &issues);

// What each of an outdoor map's 128 x 128 cells holds, read from its tiles as the game resolves them (`tiles`: the
// 256 descriptors of Game::loadTerrainTileDescriptors): 0 land, 1 shore (a water tile toward dirt), 2 open water,
// 3 road, 4 another liquid (tar, lava). For plans of a map (core/Preview).
std::vector<uint8_t> outdoorCellKinds(
    const Game::OutdoorMapData &map,
    const std::vector<Game::TerrainTileDescriptor> &tiles);

// Checks the tile sets a lowered map uses against a world's tile table (the text of the table file): each set's
// rows exist, the water set is water and the road set is a road set. Empty when all is as the build takes it;
// else what is wrong.
std::string checkOutdoorTileTable(const LoweredOutdoorMap &lowered, const std::string &table);
}
