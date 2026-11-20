#include "engine/ApplicationConfig.h"

#include "engine/AssetPaths.h"

#if defined(__APPLE__)
#include <SDL3/SDL_filesystem.h>

#include <filesystem>
#endif

namespace OpenYAMM::Engine
{
namespace
{
#if defined(__APPLE__)
// An app bundle with packaged assets (Contents/Resources/assets, assets/ in an iOS bundle) is self-contained. Otherwise
// iOS reads assets/ from its working directory, the Documents folder, and macOS uses the development tree.
std::string defaultAppleAssetRoot()
{
    if (const char *pBasePath = SDL_GetBasePath())
    {
        const std::filesystem::path bundledAssetRoot = std::filesystem::path(pBasePath) / "assets";

        if (std::filesystem::is_directory(bundledAssetRoot))
        {
            return bundledAssetRoot.string();
        }
    }

#if defined(OPENYAMM_IOS)
    return "assets";
#else
    return AssetPaths::getDevelopmentAssetRoot();
#endif
}
#endif
}

ApplicationConfig ApplicationConfig::createDefault()
{
    ApplicationConfig config;
    config.appName = "OpenYAMM";
#if defined(__ANDROID__)
    config.assetRoot = "assets";
#elif defined(__APPLE__)
    config.assetRoot = defaultAppleAssetRoot();
#else
    config.assetRoot = AssetPaths::getDevelopmentAssetRoot();
#endif
    config.activeWorldId = "mm8";
    config.startupMapFileOverride.clear();
    config.loadUniqueActorIndex.reset();
    config.assetScaleTier = AssetScaleTier::X1;
    config.assetScaleProfile = createUniformAssetScaleProfile(config.assetScaleTier);
    config.windowWidth = OPENYAMM_WINDOW_WIDTH;
    config.windowHeight = OPENYAMM_WINDOW_HEIGHT;
    config.windowMode = WindowMode::Windowed;
    config.verticalSync = false;
    config.maxAnisotropy = 4;
    config.fpsTrace = false;
    config.performanceTrace = false;
    config.hitchTrace = false;
    config.hitchThresholdMilliseconds = 8.0f;
    return config;
}
}
