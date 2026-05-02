#pragma once

#include "engine/AssetFileSystem.h"

#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct WorldStartDefinition
{
    std::string mapFileName;
    std::string introMovie;
};

struct WorldManifest
{
    std::string id = "mm8";
    std::string name = "MM8";
    std::string sourceGame = "mm8";
    WorldStartDefinition start;
    bool loadedFromFile = false;
};

WorldManifest loadActiveWorldManifestOrDefault(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &worldId,
    std::string &errorMessage
);
}
