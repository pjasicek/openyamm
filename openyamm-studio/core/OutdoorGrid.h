#pragma once

#include "core/Project.h"

namespace OpenYAMM::Studio
{
// The terrain grid of an outdoor map: how many height samples along each side (the classic ODM's 128, or the side of
// an OpenYAMM ODM v2, devdocs/hesper DECISIONS.md H-33: game/outdoor/OutdoorMapData.h `terrainSide`) and the square
// the party walks inside it.
//
// The outdoor code reads the grid of the map it works on through `outdoorGrid()`: the classic one unless an
// `OutdoorGridScope` is open. Every entry point that works on one map (a project's build, validation, lowering and
// pictures; the readers of a built map) opens a scope with that map's side, so the code under it reads its side
// instead of a fixed 128, and a classic map is built exactly as before.

// Samples along each side of a classic ODM.
constexpr int OutdoorClassicSide = 128;
// The half-width of the square the party walks on a classic map, map units from the middle (the game's merged
// outdoor bounds, game/tables/MapStats.cpp).
constexpr int OutdoorClassicPartyBounds = 23143;

struct OutdoorGrid
{
    // Height samples along each side (nodes 0 to side - 1; the sketch's cells 0 to side).
    int side = OutdoorClassicSide;
    // The nodes of the square the party walks, on both axes: 19 to 109 on a classic map.
    int playableFirst = 19;
    int playableLast = 109;
    // That square's half-width in map units: 23143 on a classic map.
    int partyBounds = OutdoorClassicPartyBounds;
};

// The grid of a side. Classic for 128. Another side keeps the classic map's share of walked land: the party's square
// grows with the side (23143 x side / 128: 28928 at 160), and its nodes are those inside it (24 to 136 at 160: a rim
// of 24 rows in the north and west and 23 in the south and east, as the classic 19 and 18).
OutdoorGrid outdoorGridOfSide(int side);

// The grid the outdoor code works on now.
const OutdoorGrid &outdoorGrid();

inline int outdoorNodeCount()
{
    return outdoorGrid().side;
}

// Nodes along each side, squared.
inline size_t outdoorNodeTotal()
{
    return static_cast<size_t>(outdoorGrid().side) * static_cast<size_t>(outdoorGrid().side);
}

// Opens the grid of a side for the code under it, and restores the one before when it closes.
class OutdoorGridScope
{
public:
    explicit OutdoorGridScope(int side);
    // The side of an outdoor project (outdoorProjectSide).
    explicit OutdoorGridScope(const Project &project);
    ~OutdoorGridScope();
    OutdoorGridScope(const OutdoorGridScope &) = delete;
    OutdoorGridScope &operator=(const OutdoorGridScope &) = delete;

private:
    OutdoorGrid m_previous;
};

// project.yml `terrain.side`: the samples along each side of the map the project builds (an even number from 32 to
// 256, ODM v2 for any side but 128). 128 where it is not said or not a whole even number in range (the schema
// refuses those).
int outdoorProjectSide(const Project &project);

// Whether a side can be built: even, 32 to 256 (game/outdoor/OutdoorMapData.cpp's loader).
bool outdoorSideAllowed(int side);
}
