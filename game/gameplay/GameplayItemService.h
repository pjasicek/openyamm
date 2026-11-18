#pragma once

#include "game/items/QuickItemSlots.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <cstddef>
#include <string>

namespace OpenYAMM::Game
{
struct EventRuntimeState;
class GameSession;
class GameplayScreenRuntime;
class Party;
struct InventoryItemMixResult;
struct CraftItemRef;

class GameplayItemService
{
public:
    explicit GameplayItemService(GameSession &session);

    bool tryUseHeldItemOnPartyMember(
        GameplayScreenRuntime &runtime,
        size_t memberIndex,
        bool keepCharacterScreenOpen);
    // The held item when the rules make it travel (MAW's dimension maps): the move to the map it names is queued and
    // the item is used only as the party sets off (useTravelItemForMove). False for every other item.
    bool tryUseHeldTravelItem(GameplayScreenRuntime &runtime);
    // The second step of a travel item's use (PendingMapMove::travelItem), as the party sets off: the rules set the
    // visit up and the item is used up if they say so, from the player's hand or from the bag it went back to. False
    // when the party no longer has the item or the rules now refuse: the party stays.
    bool useTravelItemForMove(GameplayScreenRuntime &runtime, const InventoryItem &item);
    // The member's quick item slot (the potion radial): the matching potion or scroll from the member's bags, else
    // another member's (QuickItemSlots::findPartyItem), used on the member as a held item is (a scroll casts, a potion is drunk under the rules' recovery). What remains goes back
    // where it lay. False, with a status line, when nothing was used.
    bool useQuickItemSlot(GameplayScreenRuntime &runtime, size_t memberIndex, size_t slot);
    // The same for a kind of potion or scroll not in the member's six slots (a solo run's action bar slot).
    bool useQuickItemKind(GameplayScreenRuntime &runtime, size_t memberIndex, const QuickItemSlot &kind);
    // A carried potion or scroll used on (drunk or read by) the member exactly as a held item dropped on their portrait:
    // the quick slots and the basebar's potion and scroll popups. What remains goes back where it lay.
    bool useCarriedItem(
        GameplayScreenRuntime &runtime,
        size_t memberIndex,
        const QuickItemSlots::PartyLocation &location);

    bool tryUseHeldItemOnInventoryItem(
        GameplayScreenRuntime &runtime,
        size_t memberIndex,
        uint8_t targetGridX,
        uint8_t targetGridY);

    // Mixes the alchemy bench's two slots; mixAll repeats the recipe until the ingredients run out.
    bool mixAlchemyBench(GameplayScreenRuntime &runtime, bool mixAll);
    // Brews the bench's selected recipe, brewing missing ingredients first from known recipes.
    bool brewAlchemyChain(GameplayScreenRuntime &runtime, bool brewAll);
    // Brews what the upkeep lists' potion stock lacks (PotionUpkeep::restock: the Upkeep key's auto-brew and the
    // potion popup's Brew button) and says in the status line what it brewed and what it could not; returns that
    // text. With `quietWhenFull` nothing is said when the stock lacks nothing.
    std::string restockUpkeepPotions(GameplayScreenRuntime &runtime, bool quietWhenFull);
    // A crafting material held over an item (right-click) opens the Workbench's Crafting tab with both in place; the
    // material goes back to the party. False when the held item is no material or the item takes none.
    bool openWorkbenchForHeldMaterial(GameplayScreenRuntime &runtime, const CraftItemRef &target);
    // The Workbench's Crafting tab: applies its material to its item once, or as often as the materials allow.
    bool applyCraft(GameplayScreenRuntime &runtime, bool all);
    // Merges three gems of the chosen tier into one of the next, once or (`all`) as often as the gems allow.
    bool combineGems(GameplayScreenRuntime &runtime, bool all);

    void updateReadableScrollOverlayForHeldItem(
        GameplayScreenRuntime &runtime,
        size_t memberIndex,
        const GameplayCharacterPointerTarget &pointerTarget,
        bool isLeftMousePressed,
        bool isRightMousePressed);
    // Shows a message scroll's text for this frame (the Use key held over it in the pack); false when the item is not
    // a readable message scroll.
    bool showReadableScroll(GameplayScreenRuntime &runtime, size_t memberIndex, const InventoryItem &item);
    // A message scroll read with a right click on a portrait stays open until that button is released.
    bool readableScrollOverlayHeldByRightButton(bool isRightMousePressed) const;

    bool identifyInspectedItem(
        const GameplayUiController::ItemInspectOverlayState &overlay,
        std::string &statusText);
    bool tryIdentifyInspectedItem(
        const GameplayUiController::ItemInspectOverlayState &overlay,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool tryRepairInspectedItem(
        const GameplayUiController::ItemInspectOverlayState &overlay,
        size_t inspectorMemberIndex,
        std::string &statusText);
    // Opens an inspected item the inspector can unseal (ItemRules::openSealedItem) in an inventory, chest or corpse.
    bool tryOpenInspectedItem(const GameplayUiController::ItemInspectOverlayState &overlay, size_t inspectorMemberIndex);

    void closeReadableScrollOverlay();

private:
    void applyMixResultEffects(
        GameplayScreenRuntime &runtime,
        Party &party,
        size_t memberIndex,
        const InventoryItemMixResult &mixResult,
        bool keepInventoryOpen);
    void unlockAutonote(GameplayScreenRuntime &runtime, Party &party, size_t memberIndex, uint32_t autonoteId);
    // Reading a potion recipe teaches every mix that brews the potion, in the journal and at the alchemy bench.
    void learnRecipeScroll(GameplayScreenRuntime &runtime, Party &party, size_t memberIndex, uint32_t scrollItemId);

    GameSession &m_session;
};
}
