#pragma once

#include "game/ui/GameplayUiRuntime.h"

namespace OpenYAMM::Game
{
struct GameplayInputFrame;
class GameplayScreenRuntime;

struct GameplayUiOverlayInputConfig
{
    bool hasActiveLootView = false;
    bool canToggleJournal = false;
    bool mapShortcutPressed = false;
    bool storyShortcutPressed = false;
    bool questsShortcutPressed = false;
    // MAW: opens the Journal on its Progress tab.
    bool progressShortcutPressed = false;
    bool zoomInPressed = false;
    bool zoomOutPressed = false;
    float mouseWheelDelta = 0.0f;
    bool activeEventDialog = false;
    bool residentSelectionMode = false;
    bool restActive = false;
    bool menuActive = false;
    bool controlsActive = false;
    bool keyboardActive = false;
    bool videoOptionsActive = false;
    bool saveGameActive = false;
    bool quickReferenceActive = false;
    bool spellbookActive = false;
    bool characterScreenOpen = false;
};

struct GameplayUiOverlayInputResult
{
    bool journalInputConsumed = false;
};

struct GameplayUiOverlayRenderConfig
{
    bool canRenderHudOverlays = false;
    bool hasActiveLootView = false;
    bool activeEventDialog = false;
    bool renderGameplayMouseLookOverlay = false;
    bool renderChestBelowHud = false;
    bool renderChestAboveHud = false;
    bool renderInventoryBelowHud = false;
    bool renderInventoryAboveHud = false;
    bool renderDialogueBelowHud = false;
    bool renderDialogueAboveHud = false;
    bool renderCharacterBelowHud = false;
    bool renderCharacterAboveHud = false;
    bool renderItemInspectOverlay = true;
    bool renderDebugDialogueFallback = false;
};

class GameplayUiOverlayOrchestrator
{
public:
    static GameplayUiOverlayInputResult handleStandardOverlayInput(
        GameplayScreenRuntime &overlayContext,
        const GameplayInputFrame &input,
        const GameplayUiOverlayInputConfig &config);

    static void renderStandardOverlays(
        GameplayScreenRuntime &overlayContext,
        int width,
        int height,
        const GameplayUiOverlayRenderConfig &config,
        GameplayUiOverlayFramePerformanceDiagnostics *pPerformanceDiagnostics = nullptr);
};
} // namespace OpenYAMM::Game
