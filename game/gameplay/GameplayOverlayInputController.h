#pragma once

namespace OpenYAMM::Game
{
struct GameplayInputFrame;
class GameplayScreenRuntime;

class GameplayOverlayInputController
{
public:
    static bool handleRestOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input);
    static bool handleMenuOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input);
    static bool handleControlsOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input);
    static bool handleKeyboardOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input);
    static bool handleVideoOptionsOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input);
    static bool handleSaveGameOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input);
    static bool handleJournalOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input,
        bool canToggleJournal,
        bool mapShortcutPressed,
        bool storyShortcutPressed,
        bool notesShortcutPressed,
        bool zoomInPressed,
        bool zoomOutPressed,
        float mouseWheelDelta);
    static void handleDialogueOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input,
        bool isResidentSelectionMode);
    static void handleLootOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input,
        bool hasActiveLootView);
};
} // namespace OpenYAMM::Game
