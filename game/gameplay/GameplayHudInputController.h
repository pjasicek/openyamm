#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

struct GameplayPartyPortraitInputConfig
{
    int screenWidth = 0;
    int screenHeight = 0;
    float pointerX = 0.0f;
    float pointerY = 0.0f;
    bool leftButtonPressed = false;
    bool allowInput = false;
    bool requireGameplayReady = false;
    bool hasActiveLootView = false;
    std::function<bool(size_t memberIndex)> onPortraitActivated;
};

struct GameplayHudButtonInputConfig
{
    int screenWidth = 0;
    int screenHeight = 0;
    float pointerX = 0.0f;
    float pointerY = 0.0f;
    bool leftButtonPressed = false;
    bool allowInput = false;
};

class GameplayHudInputController
{
public:
    static void handlePartyPortraitInput(
        GameplayOverlayContext &context,
        const GameplayPartyPortraitInputConfig &config);

    static void handleGameplayHudButtonInput(
        GameplayOverlayContext &context,
        const GameplayHudButtonInputConfig &config);
};
} // namespace OpenYAMM::Game
