#pragma once

#include <array>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorMapData;
struct OutdoorTerrainTextureAtlas;

// What lies past each side of an outdoor map's edge. Most MM6-MM8 maps face the sea on some sides; the Enhanced sky
// continues that sea to the horizon instead of leaving fog where the terrain square ends.
struct OutdoorDistantSea
{
    // Per side, west (-X), east (+X), south (-Y), north (+Y): 0 = land or a mixed coast, 1 = open water.
    std::array<float, 4> sideWeights = {};
    float seaLevel = 0.0f;
    // Average unlit colour of the border water tiles, display space (0-1).
    std::array<float, 3> waterColorDisplay = {};
};

// landMask is the per-cell land (1) / water (0) mask of the terrain grid; pAtlas supplies the water tiles' colours.
OutdoorDistantSea measureOutdoorDistantSea(
    const OutdoorMapData &mapData, const std::vector<uint8_t> &landMask, const OutdoorTerrainTextureAtlas *pAtlas);
}
