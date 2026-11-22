#pragma once

#include "core/OutdoorBuildings.h"
#include "core/OutdoorGround.h"
#include "core/OutdoorFalls.h"
#include "core/OutdoorWaysIn.h"
#include "core/Project.h"

#include <array>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// From an outdoor project's sketch (sketch.yml) to what a classic ODM holds of the land: a 128 x 128 field of
// heights and a map of water cells. The algorithm is told at the top of OutdoorLowering.cpp.

// Height samples along each side of an ODM (the sketch's grid nodes 0 to 127; node 128 is not stored).
constexpr int OutdoorNodeCount = 128;
// Map units between two samples.
constexpr double OutdoorCellSize = 512.0;
// Map units per step of a stored height sample (one byte: 0 to 255 steps, 0 to 8160 units).
constexpr double OutdoorHeightStep = 32.0;
constexpr int OutdoorHighestSample = 255;
// How far the ground under water lies below the water's surface, map units.
constexpr double OutdoorWaterBedDepth = 64.0;

struct LoweredOutdoorStart
{
    // The plan entrance the party arrives at.
    std::string entrance;
    // World units, standing on the terrain.
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    // The game's angle units: 2048 a turn, 0 east, 512 north.
    int facing = 0;
};

struct LoweredOutdoorMap
{
    std::string mapStem;
    std::string world;
    // The world whose kits, roofs, ground tile sets and default textures the map takes (studioStyleWorld): the
    // project's own, or for a world without them (Xeen) its base.
    std::string styleWorld;
    // Per node, row by row from north to south, each row from west to east (index y * 128 + x), map units against
    // the plan's datum. Under water this is the bed: OutdoorWaterBedDepth below the surface.
    std::vector<double> ground;
    // What the ODM stores per node, in steps of OutdoorHeightStep. An ODM has no water surface of its own: a water
    // cell is a water tile lying on the terrain, so the corners of water cells hold the water's level, not the bed.
    std::vector<uint8_t> samples;
    // Per cell (the cell whose north-west corner is the node of the same index): 1 where it is open water (water
    // on all four corners).
    std::vector<uint8_t> water;
    // Per cell: which of its corners lie in water, bit 0 the north-west, 1 the north-east, 2 the south-west, 3 the
    // south-east. A cell with some corners in water is shore; its nodes lie at the water's level too.
    std::vector<uint8_t> waterCorners;
    // Per cell: the water's surface, map units. Meaningful where `waterCorners` is not 0.
    std::vector<double> waterLevel;
    // Per cell: the water body or river its water belongs to (an index of `waterSets`), -1 where none.
    std::vector<int> waterShape;
    // Per water body and river, in the order of the sketch's bodies then rivers: its `tile_set` (a liquid the
    // ground lays in a ground set: tar, lava), empty for the map's water set.
    std::vector<std::string> waterSets;
    // The roads as cells, their beds levelled into the heights.
    std::vector<OutdoorRoadRun> roads;
    // The buildings to raise, each with its floor's height; the ground under its plot is level at it.
    std::vector<OutdoorBuildingPlan> buildings;
    // The texture classes' door pictures the build read from its asset root (empty without one): a wing door
    // becomes a pair, a leaf shows its picture at its own width (F2, D-91); doorways read them too.
    OutdoorDoorPictures doorPictures;
    // The cave mouths and hatches (`structures` of those kinds), each with its floor: the land under them is set to
    // their shells (core/OutdoorWaysIn).
    std::vector<OutdoorCavePlan> caves;
    // The waterfalls (`structures` of that kind): the land where each sheet stands is cut (core/OutdoorFalls).
    std::vector<OutdoorFallPlan> falls;
    // The ground (core/OutdoorGround): per cell the ODM's local tile number, the tile table's rows where the map's
    // four tile sets begin, the master tile, and the names of the two kinds of land beside dirt.
    std::vector<uint8_t> tiles;
    std::array<uint16_t, 4> tileSets = {};
    uint8_t masterTile = 0;
    std::vector<std::string> groundKinds;
    // The file name of the world's tile table under engine/data_tables.
    std::string tileTable;
    size_t shoreCells = 0;
    size_t roadCells = 0;
    std::optional<LoweredOutdoorStart> start;
    // What the sketch asks for and the format cannot hold, and what had to be decided for it.
    std::vector<std::string> warnings;
    size_t waterCells = 0;

    // The stored height at a place in sketch cells, map units (between the samples: weighed by distance).
    double storedHeightAt(double x, double y) const;
    // The game's ground at a place in sketch cells: each cell two flat triangles split from its north-west to its
    // south-east corner (game/outdoor `outdoorNativeTerrainHeight`), what the party and things stand on. Things
    // stood on the land (decorations, actors, spawn points, chests and crates) use it; structures keep
    // `storedHeightAt`.
    double groundHeightAt(double x, double y) const;
};

// Whether the node (x, y) lies on a line drawn `width` nodes across, in sketch cells (heights.ridges, ground
// lines). Width 1: the nodes nearest the line, within half a cell of it. More: exactly that many nodes across it,
// counted along the axis the line crosses most (on a diagonal, the nodes beside it along that axis), the one more
// of an even width on the line's left as drawn (north up). `segment` and `share` say where along the line the node
// lies (for a height given per point); `beyond`, for a node off a line two or more nodes wide, how far it lies
// beyond the nodes taken, in cells square to the line (for sides that run back into the land).
bool outdoorNodeOnLine(const std::vector<std::array<double, 2>> &line, double width, int x, int y, size_t &segment,
    double &share, double &beyond);

// The land up to its peaks, kept between lowerings of one project by a long-lived core (S5_BROWSER_EDITOR.md 2.4.3:
// a structure edit or a brush stroke does not lower the land again). Keyed by outdoorLandKey; the words applied
// after it (node blocks, strokes, smoothed areas) are read every time.
class OutdoorLandCache
{
public:
    struct Kept;
    std::shared_ptr<const Kept> kept;
    // Lowerings that started from the kept land, and those that lowered it.
    size_t hits = 0;
    size_t misses = 0;
};

// A hash of the land words of a project: plan.yml's height bands and the sketch's grid, frame, water and heights
// without the words applied after the kept land (and the roads that run out of the playable square when the frame
// has rim strips or edge heights: the rim reads them).
std::string outdoorLandKey(const Project &project);

// The land words alone, read and lowered up to the peaks, as the kept land is made (for the read record's check
// that outdoorLandKey covers every word they read: `oymap reads --land`). False when they have an issue.
bool lowerOutdoorLandOnly(const Project &project);

// False when the sketch cannot be lowered; the reasons are added to `issues`. With `pLand` the land is kept there
// and taken from there. `styleWorld` (studioStyleWorld) is the world whose kits and defaults the map takes; empty:
// the project's own. `pDoorPictures`: the asset root's door pictures (readOutdoorDoorPictures), kept in `lowered`.
bool lowerOutdoorProject(const Project &project, LoweredOutdoorMap &lowered, std::vector<ProjectIssue> &issues,
    OutdoorLandCache *pLand = nullptr, const std::string &styleWorld = std::string(),
    const OutdoorDoorPictures *pDoorPictures = nullptr);
}
