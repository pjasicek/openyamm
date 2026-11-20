#pragma once

#include "game/maps/MapAssetLoader.h"

namespace OpenYAMM::Game
{
struct MapDecorationTexture
{
    std::string name;
    std::string file;
    int16_t paletteId = 0;
    int width = 0;
    int height = 0;
    int pixelScale = 1;
};

std::optional<std::vector<MapDecorationTexture>> parseMapDecorationTextures(
    const std::string &yaml, std::string &error);

// Absent map-local manifests produce an empty set. Invalid declared overrides fail the map load.
std::optional<std::vector<OutdoorBitmapTexture>> loadMapDecorationTextures(
    const Engine::AssetFileSystem &assets, const std::string &worldId, const std::string &mapFile,
    std::string &error);
}
