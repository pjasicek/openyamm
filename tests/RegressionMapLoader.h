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

// The shared loader keeps PhysFS (one per process) initialized, so tests that mount their own AssetFileSystem cannot
// run while it is alive. Files that use it put their tests in this doctest suite (TEST_SUITE_BEGIN/END); a listener
// releases the loader before any other test starts, and the next suite test loads it again.
constexpr const char *SharedRegressionMapSuite = "shared regression map";

bool regressionMapLoaderLoaded();
const std::string &regressionMapLoaderFailure();
const RegressionMapLoader &regressionMapLoader();
void releaseRegressionMapLoader();
}
