#pragma once

#include "engine/AssetFileSystem.h"
#include "game/outdoor/OutdoorMapData.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
constexpr uint16_t TerrainTileFlagBurn = 0x0001;
constexpr uint16_t TerrainTileFlagWater = 0x0002;
constexpr uint16_t TerrainTileFlagShore = 0x0100;
constexpr uint16_t TerrainTileFlagTransition = 0x0200;

struct TerrainTileDescriptor
{
    std::string textureName;
    uint16_t tileset = 0;
    uint16_t variant = 0;
    uint16_t flags = 0;
};

std::string terrainTileDataPath(uint8_t masterTile);

std::optional<std::vector<TerrainTileDescriptor>> loadTerrainTileDescriptors(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData);

std::optional<std::vector<std::string>> loadTerrainTileTextureNames(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData);

bool applyTerrainTileDescriptorAttributes(
    const Engine::AssetFileSystem &assetFileSystem,
    OutdoorMapData &outdoorMapData);
} // namespace OpenYAMM::Game
