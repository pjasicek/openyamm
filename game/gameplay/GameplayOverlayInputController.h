#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

class GameplayOverlayInputController
{
public:
    static bool handleRestOverlayInput(
        GameplayScreenRuntime &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleMenuOverlayInput(
        GameplayScreenRuntime &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleControlsOverlayInput(
        GameplayScreenRuntime &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleKeyboardOverlayInput(
        GameplayScreenRuntime &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleVideoOptionsOverlayInput(
        GameplayScreenRuntime &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleSaveGameOverlayInput(
        GameplayScreenRuntime &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleJournalOverlayInput(
        GameplayScreenRuntime &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight,
        bool canToggleJournal,
        bool mapShortcutPressed,
        bool storyShortcutPressed,
        bool notesShortcutPressed,
        bool zoomInPressed,
        bool zoomOutPressed,
        float mouseWheelDelta);
    static void handleDialogueOverlayInput(
        GameplayScreenRuntime &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight,
        bool isResidentSelectionMode);
    static void handleLootOverlayInput(
        GameplayScreenRuntime &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight,
        bool hasActiveLootView);
};
} // namespace OpenYAMM::Game
