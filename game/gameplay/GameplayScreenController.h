#pragma once

#include "game/gameplay/GameplayInputController.h"
#include "game/gameplay/GameplayHudInputController.h"
#include "game/ui/GameplayUiOverlayOrchestrator.h"

#include <functional>

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

struct GameplayStandardUiInputConfig
{
    const bool *pKeyboardState = nullptr;
    int width = 0;
    int height = 0;
    float pointerX = 0.0f;
    float pointerY = 0.0f;
    bool leftButtonPressed = false;
    bool allowGameplayPointerInput = false;
    float mouseWheelDelta = 0.0f;
    bool blockPortraitInput = false;
    bool blockHudButtonInput = false;
    bool blockJournalToggle = false;
    bool requireGameplayReadyForPortraitSelection = true;
    std::function<bool(size_t memberIndex)> onPortraitActivated;
};

struct GameplayStandardWorldInputGateConfig
{
    const bool *pKeyboardState = nullptr;
    int width = 0;
    int height = 0;
    bool blockOnDialogue = true;
    bool blockOnRest = true;
    bool blockOnSpellbook = true;
    bool blockOnUtilitySpellOverlay = true;
    bool utilitySpellInventoryTargetKeepsWorldInput = true;
    bool blockOnSaveGame = true;
    bool blockOnLoadGame = true;
    bool blockOnControls = true;
    bool blockOnKeyboard = true;
    bool blockOnVideoOptions = true;
    bool blockOnMenu = true;
    bool blockOnCharacterScreen = true;
    bool blockOnJournal = true;
    bool clearCharacterOverlayInputState = true;
    bool closeReadableScrollOverlay = true;
};

struct GameplayStandardWorldInputGateResult
{
    bool blocked = false;
    bool utilitySpellOverlayHandled = false;
};

struct GameplayStandardWorldInteractionFrameState
{
    bool restActiveBeforeInput = false;
    bool menuActiveBeforeInput = false;
    bool controlsActiveBeforeInput = false;
    bool keyboardActiveBeforeInput = false;
    bool videoOptionsActiveBeforeInput = false;
    bool saveGameActiveBeforeInput = false;
    bool loadGameActiveBeforeInput = false;
    bool journalActiveBeforeInput = false;
};

struct GameplayStandardWorldInteractionFrameGateConfig
{
    GameplayStandardWorldInteractionFrameState state = {};
    bool hasActiveLootView = false;
};

struct GameplayStandardWorldInspectOverlayConfig
{
    int width = 0;
    int height = 0;
    bool worldReady = false;
    bool hasHeldItem = false;
    bool hasPendingSpellTarget = false;
    bool hasActiveLootView = false;
};

struct GameplayStandardGameplayActionGateConfig
{
    bool hasActiveLootView = false;
    bool hasPendingSpellCast = false;
    bool hasHeldItem = false;
    bool blockOnCharacterScreen = false;
    bool blockOnHeldItem = false;
};

struct GameplayMouseLookEnableConfig
{
    bool hasPendingSpellTarget = false;
    bool blockOnReadableScrollOverlay = false;
    bool blockOnUtilitySpellOverlay = false;
    bool utilitySpellInventoryTargetKeepsMouseLook = true;
};

struct GameplayStandardUiRenderConfig
{
    bool canRenderHudOverlays = false;
    bool renderGameplayHud = true;
    bool renderGameplayMouseLookOverlay = false;
    bool renderActorInspectOverlay = true;
    bool renderDebugFallbacks = false;
    std::function<void()> onRenderedHud;
};

struct GameplayStandardUiFrameConfig
{
    GameplayScreenFrameUpdateConfig frame = {};
    GameplayStandardUiHotkeyConfig hotkeys = {};
    GameplayStandardUiInputConfig input = {};
    GameplayStandardUiRenderConfig render = {};
    bool updateHudItemInspectOverlayFromMouse = false;
    bool blockHudItemInspectOverlayFromMouseUpdate = false;
    bool requireOpaqueHudItemInspectHit = false;
};

struct GameplayStandardUiInputFrameConfig
{
    GameplayStandardUiHotkeyConfig hotkeys = {};
    GameplayStandardUiInputConfig input = {};
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

    static bool canUpdateStandardHudItemInspectOverlayFromMouse(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool additionalBlock = false);

    static bool canUpdateStandardWorldInspectOverlayFromMouse(
        GameplayScreenRuntime &context,
        const GameplayStandardWorldInspectOverlayConfig &config);

    static bool canRunStandardGameplayAction(
        GameplayScreenRuntime &context,
        const GameplayStandardGameplayActionGateConfig &config);

    static bool canEnableGameplayMouseLook(
        GameplayScreenRuntime &context,
        const GameplayMouseLookEnableConfig &config);

    static void updateStandardHudItemInspectOverlayFromMouse(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool enabled,
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

    static GameplayUiOverlayInputResult handleStandardUiInput(
        GameplayScreenRuntime &context,
        const GameplayStandardUiInputConfig &config);

    static GameplayStandardWorldInputGateResult gateStandardWorldInput(
        GameplayScreenRuntime &context,
        const GameplayStandardWorldInputGateConfig &config);

    static GameplayStandardWorldInteractionFrameState captureStandardWorldInteractionFrameState(
        GameplayScreenRuntime &context);

    static bool isStandardWorldInteractionBlockedForFrame(
        GameplayScreenRuntime &context,
        const GameplayStandardWorldInteractionFrameGateConfig &config);

    static void renderStandardUi(
        GameplayScreenRuntime &context,
        int width,
        int height,
        const GameplayStandardUiRenderConfig &config);

    static void processStandardUiFrame(
        GameplayScreenRuntime &context,
        int width,
        int height,
        float deltaSeconds,
        const GameplayStandardUiFrameConfig &config);

    static GameplayUiOverlayInputResult processStandardUiInputFrame(
        GameplayScreenRuntime &context,
        const GameplayStandardUiInputFrameConfig &config);

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
