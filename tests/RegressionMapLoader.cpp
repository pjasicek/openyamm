#include "tests/RegressionMapLoader.h"

#include "engine/AssetScaleTier.h"

#include <filesystem>
#include <string>

namespace OpenYAMM::Tests
{
namespace
{
struct RegressionMapLoaderState
{
    bool loaded = false;
    RegressionMapLoader loader = {};
    std::string failure;
};

bool loadRegressionMapLoader(RegressionMapLoader &loader, std::string &failure)
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetsRoot = sourceRoot / "assets_dev";

    if (!loader.assetFileSystem.initialize(sourceRoot, assetsRoot, Engine::AssetScaleTier::X1))
    {
        failure = "could not initialize asset file system for regression map tests";
        return false;
    }

    if (!loader.gameDataLoader.loadForHeadlessGameplay(loader.assetFileSystem))
    {
        failure = "could not load gameplay data for regression map tests";
        return false;
    }

    return true;
}

const RegressionMapLoaderState &regressionMapLoaderState()
{
    static const RegressionMapLoaderState *pState = []()
    {
        RegressionMapLoaderState *pState = new RegressionMapLoaderState();
        pState->loaded = loadRegressionMapLoader(pState->loader, pState->failure);
        return pState;
    }();

    return *pState;
}
}

bool regressionMapLoaderLoaded()
{
    return regressionMapLoaderState().loaded;
}

const std::string &regressionMapLoaderFailure()
{
    return regressionMapLoaderState().failure;
}

const RegressionMapLoader &regressionMapLoader()
{
    return regressionMapLoaderState().loader;
}
}
