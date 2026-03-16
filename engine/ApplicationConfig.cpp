#include "engine/ApplicationConfig.h"

#include "engine/AssetPaths.h"

namespace OpenYAMM::Engine
{
ApplicationConfig ApplicationConfig::createDefault()
{
    ApplicationConfig config;
    config.appName = "OpenYAMM";
    config.assetRoot = AssetPaths::getDevelopmentAssetRoot();
    config.windowWidth = OPENYAMM_WINDOW_WIDTH;
    config.windowHeight = OPENYAMM_WINDOW_HEIGHT;
    return config;
}
}
