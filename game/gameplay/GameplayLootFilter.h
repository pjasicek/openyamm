#pragma once

#include "game/rules/LootFilter.h"

#include <cstdint>

namespace OpenYAMM::Game
{
class Party;
class SpecialItemEnchantTable;
class StandardItemEnchantTable;
struct InventoryItem;
struct ItemDefinition;

// The members' mean level, which the loot filter and Sell trash weigh an item's level against.
int meanPartyLevel(const Party *pParty);

struct FilteredLoot
{
    LootFilterVerdict verdict = LootFilterVerdict::Keep;
    // The gold it turned into (Gold only).
    uint32_t gold = 0;
};

// The ruleset's loot filter (ItemRules::lootFilter) on a monster's or chest's drop, against the party's mean level:
// the item stays (Keep), turns into gold (Gold, with the combat log line "Filtered: <rarity> <item> -> N gold"), or
// stays where it fell marked as filtered (Ground: ItemRulesetFields::lootFiltered). Every drop the filter can take
// joins this session's recent drops.
FilteredLoot filterDroppedLoot(
    InventoryItem &item,
    const ItemDefinition &definition,
    const Party *pParty,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable);
}
