#pragma once

#include "game/party/CharacterRulesetState.h"
#include "game/party/InventoryItem.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class Party;
struct Character;

// An item of a member's bag, by the cell it begins at.
struct BagItemRef
{
    size_t memberIndex = 0;
    uint8_t bag = 0;
    uint8_t gridX = 0;
    uint8_t gridY = 0;

    bool operator==(const BagItemRef &) const = default;
};

// Several bags per character (MAW's multibag, zzMaw-MultiBag.lua; ItemRules::bagCount): the inventory is the open
// bag, the others wait in the character's ruleset state, each on a grid of its own. Event and quest item checks and the
// Workbench see every bag (Party::inventoryItemCount, removeItem, removeItemFromMember; CraftingRuntime,
// AlchemyBenchRuntime), since the inventory shows all of them; the Sort button sees only the open bag, as in MAW.
//
// The party's pouches (ItemPouch, rulesets with ItemRules::hasPouches) are three more bags, the same for every member:
// the items of pouchBag(pouch) are the party's (Party::pouchItems) whichever member the bag is asked of, on a grid of
// their own (PouchColumns wide, PouchRows deep, filled row by row). An item with a pouch lies nowhere else, and a
// pouch takes nothing else (Party::tryPlaceItemInMemberInventoryCell and the grants see to both). The loot pouch is
// the exception: no item's own pouch, it takes any item without one, and such items leave it for a bag freely.
namespace InventoryBags
{
constexpr uint8_t CraftingPouchBag = 240;
constexpr uint8_t AlchemyPouchBag = 241;
constexpr uint8_t QuestPouchBag = 242;
constexpr uint8_t LootPouchBag = 243;
// A pouch's grid: as wide as two bags side by side, as the bag overview shows them; the inventory shows
// PouchVisibleRows of its rows (two bags' worth) and scrolls.
constexpr int PouchColumns = 28;
constexpr int PouchVisibleRows = 18;
constexpr int PouchRows = 240;

inline bool isPouchBag(uint8_t bag)
{
    return bag >= CraftingPouchBag && bag <= LootPouchBag;
}

// A pouch of one kind of item (every pouch but the loot pouch): it takes nothing else.
inline bool isKindPouchBag(uint8_t bag)
{
    return isPouchBag(bag) && bag != LootPouchBag;
}

inline uint8_t pouchBag(ItemPouch pouch)
{
    return CraftingPouchBag + static_cast<uint8_t>(pouch);
}

inline ItemPouch pouchOfBag(uint8_t bag)
{
    return static_cast<ItemPouch>(bag - CraftingPouchBag);
}

// Bags a tab: a party of one has several tabs of four (MAW's solo tabs, ItemRules::bagCount 20; a party has one); the
// inventory shows the open bag's tab.
constexpr int TabBags = 4;
// Where a save's items that fit in no bag wait (fitIntoBagCount) until takeOverflow drops them for the world.
constexpr uint8_t OverflowBag = 255;

// The first bag of the tab holding `bag`, and how many tabs `bagCount` bags make.
inline uint8_t tabFirstBag(uint8_t bag)
{
    return uint8_t(bag / TabBags * TabBags);
}

inline int tabCount(int bagCount)
{
    return (std::max(1, bagCount) + TabBags - 1) / TabBags;
}

// Opens `bag` (0-based) of the character: the open bag's items are stored and the chosen bag's become the
// inventory. False, with nothing changed, when it is open already or beyond `bagCount`.
bool openBag(Character &character, uint8_t bag, int bagCount);
// Sorts the items of all the character's bags as one (zzMaw-Item-Sorter.lua sortMultibag): the tallest first, then
// by skill and item id, filled column by column from the first bag on; the same bag stays open. False, with nothing
// changed, when they would no longer fit.
bool sortAllBags(Character &character, int bagCount, const ItemTable *pItemTable);
// Sorts the open bags (allBags: every bag of the open bag's tab) of the members in sortAllBags' order, MAW's party
// sorts (T, G; Ctrl and Ctrl+Shift on Sort); every member's items stay with that member (MAW's alchemist, who took the
// party's alchemy items, is retired: those lie in the party's alchemy pouch). With more than one tab, what the open
// tab's bags have no room for goes to the free places of the other tabs' bags, the next tab first (OY-651). False,
// with nothing changed, when a member's items no longer fit.
bool sortPartyBags(Party &party, const std::vector<size_t> &members, bool allBags, int bagCount);
// Sorts a pouch in sortAllBags' order, then by what tells two of a kind apart (a reagent's level, a bottle's
// drinks), and packs it row by row from the top.
void sortPouch(Party &party, ItemPouch pouch);
// A save from when the ruleset had more bags (MAW had five, and 25 for a party of one, before 2026-10-25): every
// member's items past `bagCount` bags go to the first free place of the owner's bags, else of another member's; a
// member whose open bag is gone opens the first. Returns how many fit nowhere: they wait in OverflowBag for
// takeOverflow.
size_t fitIntoBagCount(Party &party, int bagCount);
// Takes what fitIntoBagCount could not place (OverflowBag), for the world. Bags past the count otherwise keep their
// items: a party of one's other tabs while the party has more members.
std::vector<InventoryItem> takeOverflow(Character &character);
// Items in bags other than the open one.
size_t storedItemCount(const Character &character);
// The items of `bag`: the inventory when it is the open bag, else the bag's stored items (empty for an unused bag).
// Of the member's own bags only; the Party forms below know the pouches too.
const std::vector<InventoryItem> &itemsInBag(const Character &character, uint8_t bag);
// The item of `bag` covering the cell, or none.
const InventoryItem *itemInBagAt(const Character &character, uint8_t bag, uint8_t gridX, uint8_t gridY);
InventoryItem *itemInBagAt(Character &character, uint8_t bag, uint8_t gridX, uint8_t gridY);
// The same for a bag of a member or a pouch (the party's, whoever the member is). No items for a member who is not
// there.
const std::vector<InventoryItem> &itemsInBag(const Party &party, size_t memberIndex, uint8_t bag);
const InventoryItem *itemInBagAt(const Party &party, size_t memberIndex, uint8_t bag, uint8_t gridX, uint8_t gridY);
InventoryItem *itemInBagAt(Party &party, size_t memberIndex, uint8_t bag, uint8_t gridX, uint8_t gridY);
inline const InventoryItem *itemAt(const Party &party, const BagItemRef &ref)
{
    return itemInBagAt(party, ref.memberIndex, ref.bag, ref.gridX, ref.gridY);
}
// The bags a walk over everything the party carries visits for a member: the member's `bagCount` bags, and for
// `withPouches` (one member of the walk, so the pouches' items come once) the party's pouches after them.
std::vector<uint8_t> carriedBags(const Party &party, int bagCount, bool withPouches);
// Places `item` in `bag` of the member at the cell as the open bag's grid does
// (Party::tryPlaceItemInMemberInventoryCell: the one item in the way comes out as replacedItem). The open bag stays
// open. False, with nothing changed, when it does not fit there or `bag` is beyond `bagCount`.
bool placeInBag(
    Party &party,
    size_t memberIndex,
    uint8_t bag,
    int bagCount,
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY,
    std::optional<InventoryItem> &replacedItem);
// What placeInBag would do with `item` at the cell, for showing it before the drop: whether it fits, where it would lie
// (a swap puts it where the replaced item began, or in the first free place) and the item it would replace.
struct PlacementPreview
{
    bool fits = false;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
    std::optional<InventoryItem> replacedItem;
};
PlacementPreview previewPlaceInBag(
    const Party &party,
    size_t memberIndex,
    uint8_t bag,
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY);
// Runs the open bag's own operation on `bag`: it is opened for the call and the bag that was open is opened again.
// A pouch is the member's open bag for the call as any other bag is (the member's inventory is the pouch's items, the
// character's grid the pouch's: Character::addInventoryItem and the rest). False, without the call, when `bag` is
// beyond `bagCount`, or a pouch another member has open.
bool withBagOpen(Party &party, size_t memberIndex, uint8_t bag, int bagCount, const std::function<bool()> &operation);
// After the item covering the cell changed in place into another (a bottle mixed into its potion: OY-240), gives it
// the new item's inventory size: where it lies when that fits without moving another item, else wherever the party has
// room. False, the item left as it was, when nothing has room or there is no item.
bool refitChangedItem(
    Party &party,
    size_t memberIndex,
    uint8_t bag,
    int bagCount,
    uint8_t gridX,
    uint8_t gridY,
    const ItemTable &itemTable);
// Takes the item covering the cell out of `bag` of the member; the open bag stays open.
bool takeFromBag(
    Party &party,
    size_t memberIndex,
    uint8_t bag,
    int bagCount,
    uint8_t gridX,
    uint8_t gridY,
    InventoryItem &item);
}
}
