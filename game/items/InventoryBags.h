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

// Several bags per character (MAW's multibag, zzMaw-MultiBag.lua; ItemRules::bagCount): the inventory is the open
// bag, the others wait in the character's ruleset state, each on a grid of its own. Event and quest item checks and the
// Workbench see every bag (Party::inventoryItemCount, removeItem, removeItemFromMember; CraftingRuntime,
// AlchemyBenchRuntime), since the inventory shows all of them; the Sort button sees only the open bag, as in MAW.
namespace InventoryBags
{
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
// sorts (T, G; Ctrl and Ctrl+Shift on Sort). With an alchemist (ItemRules::alchemist), the items alchemyRank ranks go from all of them to
// the alchemist, lowest rank first, as far as they fit after the alchemist's own; the rest stays with its owner
// (zzMaw-Item-Sorter.lua sortInventory). Sorting every bag also honours the bag tags (ours; MAW's sort has none): an
// item bagTagOf tags goes to the member's bags with that tag first. False, with nothing changed, when a member's items
// no longer fit.
bool sortPartyBags(
    Party &party,
    const std::vector<size_t> &members,
    bool allBags,
    int bagCount,
    std::optional<size_t> alchemist,
    const std::function<std::optional<int>(const InventoryItem &)> &alchemyRank,
    const std::function<std::optional<BagTag>(const InventoryItem &)> &bagTagOf = {});
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
const std::vector<InventoryItem> &itemsInBag(const Character &character, uint8_t bag);
// The item of `bag` covering the cell, or none.
const InventoryItem *itemInBagAt(const Character &character, uint8_t bag, uint8_t gridX, uint8_t gridY);
InventoryItem *itemInBagAt(Character &character, uint8_t bag, uint8_t gridX, uint8_t gridY);
// Places `item` in `bag` of the member at the cell as the open bag's grid does (Party::tryPlaceItemInMemberInventoryCell:
// the one item in the way comes out as replacedItem). The open bag stays open. False, with nothing changed, when it does
// not fit there or `bag` is beyond `bagCount`.
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
    const Character &character,
    uint8_t bag,
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY);
// Whether `bag` of the character carries the tag.
bool hasTag(const Character &character, uint8_t bag, BagTag tag);
// Tags or untags `bag`; returns whether it carries the tag now.
bool toggleTag(Character &character, uint8_t bag, BagTag tag);
// A ground item the party picks up, into a bag tagged for it (MAW's crafting bag, zzzMaw_CraftingBag.lua:195-254): the
// picker's tagged bags first, then every other member's in party order, each item where Character::addInventoryItem
// would put it. The member who got it, or none when no tagged bag has room.
std::optional<size_t> placeInTaggedBag(
    Party &party,
    size_t pickerIndex,
    const InventoryItem &item,
    BagTag tag,
    int bagCount);
// Runs the open bag's own operation on `bag`: it is opened for the call and the bag that was open is opened again.
// False, without the call, when `bag` is beyond `bagCount`.
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
