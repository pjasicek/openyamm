#pragma once

#include "engine/AssetFileSystem.h"
#include "game/outdoor/OutdoorMapData.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
std::string terrainTileDataPath(uint8_t masterTile);

std::optional<std::vector<std::string>> loadTerrainTileTextureNames(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData);
} // namespace OpenYAMM::Game
