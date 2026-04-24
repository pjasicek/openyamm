#pragma once

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"

#include <string>

namespace OpenYAMM::Tests
{
struct RegressionMapLoader
{
    Engine::AssetFileSystem assetFileSystem = {};
    Game::GameDataLoader gameDataLoader = {};
};

bool regressionMapLoaderLoaded();
const std::string &regressionMapLoaderFailure();
const RegressionMapLoader &regressionMapLoader();
}
