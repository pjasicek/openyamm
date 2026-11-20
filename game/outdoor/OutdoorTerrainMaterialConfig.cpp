#include "game/outdoor/OutdoorTerrainMaterialConfig.h"
#include "game/outdoor/OutdoorMapData.h"

#include <filesystem>

namespace OpenYAMM::Game
{
std::optional<OutdoorTerrainMaterialConfig> loadOutdoorTerrainMaterialConfig(
    const Engine::AssetFileSystem &assets, const OutdoorMapData &map, std::string &error)
{
    error.clear();
    const std::string directory = "worlds/" + map.worldId + "/terrain_materials/";
    const std::string path = directory + std::filesystem::path(map.fileName).stem().string() + ".yml";
    const std::optional<std::string> text = assets.readTextFile(path);
    if (!text)
    {
        error = "missing " + path + " (tools/terrain_materials.py weights)";
        return std::nullopt;
    }
    return parseTerrainMaterialConfig(*text, directory, path, error);
}
}
