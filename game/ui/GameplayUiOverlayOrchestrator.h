#pragma once

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

struct GameplayUiOverlayInputConfig
{
    bool hasActiveLootView = false;
    bool canToggleJournal = false;
    bool mapShortcutPressed = false;
    bool storyShortcutPressed = false;
    bool notesShortcutPressed = false;
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
    bool renderDebugLootFallback = false;
    bool renderDebugDialogueFallback = false;
};

class GameplayUiOverlayOrchestrator
{
public:
    static GameplayUiOverlayInputResult handleStandardOverlayInput(
        GameplayOverlayContext &overlayContext,
        const bool *pKeyboardState,
        int width,
        int height,
        const GameplayUiOverlayInputConfig &config);

    static void renderStandardOverlays(
        GameplayOverlayContext &overlayContext,
        int width,
        int height,
        const GameplayUiOverlayRenderConfig &config);
};
} // namespace OpenYAMM::Game
