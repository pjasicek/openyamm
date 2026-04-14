#pragma once

#include "engine/AssetScaleTier.h"

#include <string>

namespace OpenYAMM::Engine
{
struct ApplicationConfig
{
    std::string appName;
    std::string assetRoot;
    std::string startupMapFileOverride;
    AssetScaleTier assetScaleTier;
    int windowWidth;
    int windowHeight;

    static ApplicationConfig createDefault();
};
}
