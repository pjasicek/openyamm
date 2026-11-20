#pragma once

namespace OpenYAMM::Game
{
struct GameplayInputFrame;
class GameplayScreenRuntime;

class GameplayOverlayInputController
{
public:
    // The open chest's Take All (goldOnly: Take Gold) button: gold, then every item that fits in the party's packs.
    static void takeAllActiveChestItems(GameplayScreenRuntime &view, bool goldOnly);
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
        bool questsShortcutPressed,
        bool progressShortcutPressed,
        bool zoomInPressed,
        bool zoomOutPressed,
        float mouseWheelDelta);
    static bool handleQuickReferenceOverlayInput(
        GameplayScreenRuntime &view,
        const GameplayInputFrame &input);
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
