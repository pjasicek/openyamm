#pragma once

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

class GameplayOverlayInputController
{
public:
    static bool handleRestOverlayInput(
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleMenuOverlayInput(
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleControlsOverlayInput(
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleKeyboardOverlayInput(
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleVideoOptionsOverlayInput(
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleSaveGameOverlayInput(
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static bool handleJournalOverlayInput(
        GameplayOverlayContext &view,
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
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight,
        bool isResidentSelectionMode);
    static void handleLootOverlayInput(
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight,
        bool hasActiveLootView);
};
} // namespace OpenYAMM::Game
