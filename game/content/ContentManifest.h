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

struct CampaignManifest
{
    std::string id = "default";
    std::string name = "Default Campaign";
    std::vector<std::string> worlds = {"mm8"};
    std::vector<std::string> startWorlds = {"mm8"};
    bool loadedFromFile = false;
};

WorldManifest loadActiveWorldManifestOrDefault(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &worldId,
    std::string &errorMessage
);

CampaignManifest loadCampaignManifestOrDefault(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &campaignId,
    const std::string &activeWorldId,
    std::string &errorMessage
);
}

