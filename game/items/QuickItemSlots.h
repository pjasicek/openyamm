#pragma once

#include "game/party/QuickItemSlot.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class MergedPotionSettingTable;
class MergedReagentSettingTable;
class Party;
struct Character;
struct InventoryItem;

// The potion radial's slots (devdocs/maw/GAPS.md H.6, level_generation/ui/maw_potion_radial_20261025/): which items a
// slot may hold, and which carried item it uses.
namespace QuickItemSlots
{
// Whether a slot may hold this item: a potion one drinks or a spell scroll one reads.
bool canHold(
    const InventoryItem &item,
    const ItemTable &itemTable,
    const MergedPotionSettingTable *pPotionSettingTable,
    const MergedReagentSettingTable *pReagentSettingTable);

// Where the item a slot uses lies: the bag (0-based) and its cell.
struct Location
{
    uint8_t bag = 0;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
};

// The item of the slot's kind the character would use, by its bottle rule (weakest or strongest by power; for equal
// power the first found), from every bag up to `bagCount`. None when the slot is empty or nothing matches.
std::optional<Location> findItem(const Character &character, const QuickItemSlot &slot, int bagCount);
// How many items of the slot's kind the character carries in every bag.
size_t countItems(const Character &character, const QuickItemSlot &slot, int bagCount);

// The item a member's slot uses from the whole party (user, 2026-10-25): the slot owner's bags first, then every other
// member's in party order, each by the slot's bottle rule.
struct PartyLocation
{
    size_t memberIndex = 0;
    Location location;
};
std::optional<PartyLocation> findPartyItem(
    const Party &party,
    size_t ownerIndex,
    const QuickItemSlot &slot,
    int bagCount);
// How many items of the slot's kind the whole party carries.
size_t countPartyItems(const Party &party, const QuickItemSlot &slot, int bagCount);

// One kind of potion or scroll the party carries at one power (the ring's picker and the basebar popups list these):
// how many, in whose bags (member indices in party order), and whether it is a scroll.
struct PartyItemKind
{
    uint32_t itemId = 0;
    uint16_t power = 0;
    size_t count = 0;
    bool scroll = false;
    std::vector<size_t> carriers;
};

// Every potion and scroll a slot may hold across the party's bags, in order of first appearance (the caller sorts).
std::vector<PartyItemKind> partyItemKinds(
    const Party &party,
    const ItemTable &itemTable,
    const MergedPotionSettingTable *pPotionSettingTable,
    const MergedReagentSettingTable *pReagentSettingTable,
    int bagCount);

// An item of exactly this kind and power: the preferred member's bags first, then the others' in party order.
std::optional<PartyLocation> findPartyItemOfPower(
    const Party &party,
    size_t preferredIndex,
    uint32_t itemId,
    uint16_t power,
    int bagCount);
}
}
