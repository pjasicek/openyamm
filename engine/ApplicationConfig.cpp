#include "engine/ApplicationConfig.h"

#include "engine/AssetPaths.h"

namespace OpenYAMM::Engine
{
ApplicationConfig ApplicationConfig::createDefault()
{
    ApplicationConfig config;
    config.appName = "OpenYAMM";
    config.assetRoot = AssetPaths::getDevelopmentAssetRoot();
    config.activeWorldId = "mm8";
    config.startupMapFileOverride.clear();
    config.assetScaleTier = AssetScaleTier::X1;
    config.windowWidth = OPENYAMM_WINDOW_WIDTH;
    config.windowHeight = OPENYAMM_WINDOW_HEIGHT;
    config.windowMode = WindowMode::Windowed;
    return config;
}
}
