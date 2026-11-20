#pragma once

#include "engine/AssetFileSystem.h"
#include "game/render/TerrainMaterialConfig.h"

namespace OpenYAMM::Game
{
struct OutdoorMapData;

std::optional<OutdoorTerrainMaterialConfig> loadOutdoorTerrainMaterialConfig(
    const Engine::AssetFileSystem &assets, const OutdoorMapData &map, std::string &error);
}
