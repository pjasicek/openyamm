#pragma once

#include <cstdint>
#include <array>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
struct OutdoorMapData;
struct OutdoorTerrainTile;
struct OutdoorTerrainMaterialShore;

// CPU water surface shared by rendering and movement, independent of graphics quality and GPU initialization.
struct OutdoorWaterDepthData
{
    static constexpr float WadingDepth = 96.0f;

    std::vector<uint8_t> shore;
    int shoreSize = 0;
    float distanceRange = 0.0f;
    float seabedSlope = 0.0f;
    float renderedSeabedDepth = 0.0f;
    std::vector<float> levels;
    std::vector<uint8_t> otherLiquids;

    float shoreDistance(float x, float y) const;
    float cellLevel(int cellX, int cellY, float u, float v) const;
    std::optional<float> depth(float x, float y) const;
    std::optional<float> movementHeight(float x, float y, bool waterWalk) const;
};

OutdoorWaterDepthData buildOutdoorWaterDepthData(const OutdoorMapData &map,
    const std::array<OutdoorTerrainTile, 256> &tiles, const OutdoorTerrainMaterialShore &shore,
    std::vector<uint8_t> encoded, int size);
bool loadOutdoorWaterDepthData(const Engine::AssetFileSystem &assets, OutdoorMapData &map,
    const std::array<OutdoorTerrainTile, 256> &tiles, std::string &error);
}
