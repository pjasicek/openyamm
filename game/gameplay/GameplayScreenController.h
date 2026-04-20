#pragma once

#include "game/gameplay/GameplayHudInputController.h"
#include "game/gameplay/GameplayScreenHotkeyController.h"
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
    bool canOpenRest = false;
    float mouseWheelDelta = 0.0f;
    bool blockPortraitInput = false;
    bool blockHudButtonInput = false;
    bool blockMenuToggle = false;
    bool blockSpellbookToggle = false;
    bool blockInventoryToggle = false;
    bool blockPartyCycle = false;
    bool blockJournalToggle = false;
    bool requireGameplayReadyForPortraitSelection = true;
    bool requireGameplayReadyForPartySelection = false;
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

    static void handleSharedHotkeys(
        GameplayScreenRuntime &context,
        const bool *pKeyboardState,
        const GameplayScreenHotkeyConfig &config);

    static GameplayUiOverlayInputResult handleStandardUiInput(
        GameplayScreenRuntime &context,
        const GameplayStandardUiInputConfig &config);

    static GameplayStandardWorldInputGateResult gateStandardWorldInput(
        GameplayScreenRuntime &context,
        const GameplayStandardWorldInputGateConfig &config);

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
