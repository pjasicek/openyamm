#include "game/outdoor/OutdoorWaterDepthData.h"
#include "engine/ImageAssetLoader.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorTerrainMaterialConfig.h"
#include "game/maps/OutdoorTerrainTiles.h"

namespace OpenYAMM::Game
{
bool loadOutdoorWaterDepthData(const Engine::AssetFileSystem &assets, OutdoorMapData &map,
    const std::array<OutdoorTerrainTile, 256> &tiles, std::string &error)
{
    map.waterDepth.reset();
    const std::optional<OutdoorTerrainMaterialConfig> config = loadOutdoorTerrainMaterialConfig(assets, map, error);
    if (!config)
    {
        return false;
    }
    if (!config->shore)
    {
        return true;
    }
    const std::string path = config->directory + config->shore->file;
    Engine::BinaryAssetCache cache;
    const std::optional<Engine::ImagePixelsBgra> image = Engine::loadImageAssetPixelsBgra(assets, path, cache);
    const int size = MapCells * config->texelsPerCell;
    if (!image || image->width != size || image->height != size)
    {
        error = "terrain shore distance must be " + std::to_string(size) + " pixels square: " + path;
        return false;
    }
    std::vector<uint8_t> encoded(size_t(size) * size);
    for (size_t index = 0; index < encoded.size(); ++index)
    {
        encoded[index] = image->pixels[index * 4 + 2];
    }
    map.waterDepth = buildOutdoorWaterDepthData(map, tiles, *config->shore, std::move(encoded), size);
    return true;
}
}
