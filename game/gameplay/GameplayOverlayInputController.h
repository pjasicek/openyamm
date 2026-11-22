#pragma once

#include "game/gameplay/NpcFollowerRuntime.h"

#include <cstddef>
#include <cstdint>

namespace OpenYAMM::Game
{
enum class HouseStockAction : uint8_t;
enum class HouseStockMode : uint8_t;
struct GameplayInputFrame;
struct HouseEntry;
class GameplayScreenRuntime;
class IGameplayWorldRuntime;
class ItemTable;
class Party;

class GameplayOverlayInputController
{
public:
    // The open chest's Take All (goldOnly: Take Gold) button: gold, then every item that fits in the party's packs.
    static void takeAllActiveChestItems(GameplayScreenRuntime &view, bool goldOnly);
    // The taking itself, for the party of whichever player has the world's open chest: what the party got in gold,
    // how many things it took and whether something stayed for want of room.
    struct ChestTakeAllResult
    {
        FoundGold gold;
        size_t taken = 0;
        bool leftBehind = false;
    };
    static ChestTakeAllResult takeAllActiveChestItems(
        IGameplayWorldRuntime &worldRuntime,
        Party &party,
        const ItemTable *pItemTable,
        bool goldOnly);
    // Buying, stealing or rerolling a shop's stock for the party that stands in the house, with what the player hears
    // and reads of it. The local player's click, or a co-op host doing it for another player.
    static void performHouseStockAction(
        GameplayScreenRuntime &view,
        const HouseEntry &houseEntry,
        HouseStockMode stockMode,
        size_t slotIndex,
        HouseStockAction action);
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
