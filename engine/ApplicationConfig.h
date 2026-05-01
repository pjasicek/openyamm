#pragma once

#include "engine/AssetScaleTier.h"

#include <string>

namespace OpenYAMM::Engine
{
enum class WindowMode
{
    Windowed,
    WindowedFullscreen,
    Fullscreen
};

struct ApplicationConfig
{
    std::string appName;
    std::string assetRoot;
    std::string campaignId;
    std::string activeWorldId;
    std::string startupMapFileOverride;
    AssetScaleTier assetScaleTier;
    int windowWidth;
    int windowHeight;
    WindowMode windowMode;

    static ApplicationConfig createDefault();
};
}
