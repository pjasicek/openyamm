#pragma once

#include "game/gameplay/GameplayHudInputController.h"
#include "game/gameplay/GameplayScreenHotkeyController.h"
#include "game/ui/GameplayUiOverlayOrchestrator.h"

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

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
        GameplayOverlayContext &context,
        int width,
        int height,
        float deltaSeconds,
        const GameplayScreenFrameUpdateConfig &config);

    static bool updateRenderedHudItemInspectOverlay(
        GameplayOverlayContext &context,
        int width,
        int height,
        bool requireOpaqueHitTest);

    static void applySharedItemInspectSkillInteraction(
        GameplayOverlayContext &context);

    static void updateRestOverlayProgress(
        GameplayOverlayContext &context,
        float deltaSeconds);

    static void handlePartyPortraitInput(
        GameplayOverlayContext &context,
        const GameplayPartyPortraitInputConfig &config);

    static void handleGameplayHudButtonInput(
        GameplayOverlayContext &context,
        const GameplayHudButtonInputConfig &config);

    static GameplayUiOverlayInputResult handleSharedOverlayInput(
        GameplayOverlayContext &context,
        const bool *pKeyboardState,
        int width,
        int height,
        const GameplayUiOverlayInputConfig &config);

    static void handleSharedHotkeys(
        GameplayOverlayContext &context,
        const bool *pKeyboardState,
        const GameplayScreenHotkeyConfig &config);

    static void handleUtilitySpellOverlayInput(
        GameplayOverlayContext &context,
        const bool *pKeyboardState,
        int width,
        int height);

    static void renderSharedOverlays(
        GameplayOverlayContext &context,
        int width,
        int height,
        const GameplayScreenRenderConfig &config);
};
} // namespace OpenYAMM::Game
