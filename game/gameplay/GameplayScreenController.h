#pragma once

#include "game/gameplay/GameplayHudInputController.h"
#include "game/gameplay/GameplayScreenHotkeyController.h"
#include "game/ui/GameplayUiOverlayOrchestrator.h"

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

struct GameplayScreenRenderConfig
{
    GameplayUiOverlayRenderConfig base = {};
    bool renderDeferredInventoryOverlay = false;
    bool renderUtilitySpellOverlay = true;
    bool renderCharacterInspectOverlay = true;
    bool renderBuffInspectOverlay = true;
    bool renderCharacterDetailOverlay = true;
    bool renderActorInspectOverlay = true;
    bool renderSpellInspectOverlay = true;
    bool renderReadableScrollOverlay = true;
};

struct GameplayScreenFrameUpdateConfig
{
    bool updateBuffInspectOverlay = true;
};

class GameplayScreenController
{
public:
    static void updateSharedFrameState(
        GameplayScreenRuntime &context,
        int width,
        int height,
        float deltaSeconds,
        const GameplayScreenFrameUpdateConfig &config);

    static bool updateRenderedHudItemInspectOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool requireOpaqueHitTest);

    static void applySharedItemInspectSkillInteraction(
        GameplayScreenRuntime &context);

    static void updateRestOverlayProgress(
        GameplayScreenRuntime &context,
        float deltaSeconds);

    static void handlePartyPortraitInput(
        GameplayScreenRuntime &context,
        const GameplayPartyPortraitInputConfig &config);

    static void handleGameplayHudButtonInput(
        GameplayScreenRuntime &context,
        const GameplayHudButtonInputConfig &config);

    static GameplayUiOverlayInputResult handleSharedOverlayInput(
        GameplayScreenRuntime &context,
        const bool *pKeyboardState,
        int width,
        int height,
        const GameplayUiOverlayInputConfig &config);

    static void handleSharedHotkeys(
        GameplayScreenRuntime &context,
        const bool *pKeyboardState,
        const GameplayScreenHotkeyConfig &config);

    static void handleUtilitySpellOverlayInput(
        GameplayScreenRuntime &context,
        const bool *pKeyboardState,
        int width,
        int height);

    static void renderSharedOverlays(
        GameplayScreenRuntime &context,
        int width,
        int height,
        const GameplayScreenRenderConfig &config);
};
} // namespace OpenYAMM::Game
