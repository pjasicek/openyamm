#pragma once

#include "game/outdoor/OutdoorMapData.h"

#include <array>
#include <vector>

namespace OpenYAMM::Game
{
// How dry or lush the ground grows, from its shape (level_generation/terrain/MEADOW.md): crests and steep exposed
// slopes are drier, hollows and the land along water lusher. The terrain tints its grass layers by it and the grass
// decorations take the same tint, density and height, so the two agree.
struct OutdoorMeadowField
{
    // Per terrain grid corner (TerrainWidth squared, row 0 at the north edge like heightMap): -1 lush .. +1 dry.
    std::vector<float> values;

    // Bilinear at a world position; 0 (neutral) without a field.
    float sample(float x, float y) const;
};

OutdoorMeadowField buildOutdoorMeadowField(const OutdoorMapData &map);
// The same from any ground in the outdoor map frame (an open-air BLV's terrain faces): heights per grid corner
// (TerrainWidth squared, row 0 north) and per cell (the same indexing, last row and column unused) nonzero for water.
OutdoorMeadowField buildMeadowField(const std::vector<float> &heights, const std::vector<uint8_t> &waterCells);

// The colour multiplier at a meadow value: towards dry above 0, towards lush below, scaled by strength.
std::array<float, 3> outdoorMeadowTint(float meadow, const std::array<float, 3> &dry, const std::array<float, 3> &lush,
    float strength = 1.0f);
} // namespace OpenYAMM::Game
