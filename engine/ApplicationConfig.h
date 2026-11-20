#pragma once

#include "engine/AssetPackIndex.h"
#include "engine/AssetScaleTier.h"

#include <cstddef>
#include <cstdint>
#include <optional>
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
    std::string activeWorldId;
    std::string startupMapFileOverride;
    // The ruleset of a game started directly, without the New Game screen ("--ruleset maw:hell:horizontal"; see
    // game/content/RulesetOptions.h). Empty plays the Standard rules.
    std::string startupRuleset;
    std::optional<size_t> loadUniqueActorIndex;
    AssetScaleTier assetScaleTier;
    AssetScaleProfile assetScaleProfile;
    InstalledContentOptions installedContent;
    int windowWidth;
    int windowHeight;
    WindowMode windowMode;
    bool verticalSync;
    // Upper limit of anisotropic texture filtering; 1 turns it off.
    uint8_t maxAnisotropy;
    bool fpsTrace;
    bool performanceTrace;
    bool hitchTrace;
    float hitchThresholdMilliseconds;
    // False for headless commands: their runs must not rewrite the player's settings file (start_world).
    bool saveSettings = true;

    static ApplicationConfig createDefault();
};
}
