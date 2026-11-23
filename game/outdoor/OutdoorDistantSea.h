#pragma once

#include <array>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorMapData;
struct OutdoorTerrainTiles;

// What lies past each side of an outdoor map's edge. Most MM6-MM8 maps face the sea on some sides; the Enhanced sky
// continues that sea to the horizon instead of leaving fog where the terrain square ends.
struct OutdoorDistantSea
{
    // Per side, west (-X), east (+X), south (-Y), north (+Y): 0 = land or a mixed coast, 1 = open water.
    std::array<float, 4> sideWeights = {};
    float seaLevel = 0.0f;
    // Average unlit colour of the border water tiles, display space (0-1).
    std::array<float, 3> waterColorDisplay = {};
    // Per side as sideWeights: 0 = no void, 1 = the world ends there (the map's terrain.void covers the border).
    std::array<float, 4> voidWeights = {};
};

// landMask is the per-cell land (1) / water (0) mask of the terrain grid; pTerrainTiles supplies the water tiles'
// colours. Void cells (mapData.voidCells) count as neither: a side mostly in the void has no sea past it.
OutdoorDistantSea measureOutdoorDistantSea(
    const OutdoorMapData &mapData, const std::vector<uint8_t> &landMask, const OutdoorTerrainTiles *pTerrainTiles);
}
