#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

struct GameplayPartyPortraitInputConfig
{
    int screenWidth = 0;
    int screenHeight = 0;
    float pointerX = 0.0f;
    float pointerY = 0.0f;
    bool leftButtonPressed = false;
    bool rightButtonPressed = false;
    // False while the right button is the Modern cursor key: its release over a portrait uses the item instead.
    bool rightPressUsesHeldItem = true;
    bool touchItemReleased = false;
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
    static void activatePartyPortrait(
        GameplayScreenRuntime &context,
        size_t memberIndex,
        const GameplayPartyPortraitInputConfig &config);
    // A click on an MM9 hireling's face (its combatant index): makes it the acting combatant, or opens its dialogue
    // when it already acts or on a double click.
    static void activateHirelingPortrait(GameplayScreenRuntime &context, size_t combatantIndex);

    // Modern controls: the right button frees the cursor, so its release over a portrait uses the held item on that
    // member. False when the pointer is on no portrait or the item was not used.
    static bool useHeldItemOnPortraitAtPointer(
        GameplayScreenRuntime &context,
        int screenWidth,
        int screenHeight,
        float pointerX,
        float pointerY);
    static void handlePartyPortraitInput(
        GameplayScreenRuntime &context,
        const GameplayPartyPortraitInputConfig &config);

    static void handleGameplayHudButtonInput(
        GameplayScreenRuntime &context,
        const GameplayHudButtonInputConfig &config);
};
} // namespace OpenYAMM::Game
