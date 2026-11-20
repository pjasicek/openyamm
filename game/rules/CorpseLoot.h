#pragma once

#include "game/items/ItemRulesetFields.h"
#include "game/tables/MonsterTable.h"

#include <cstdint>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
// Which part of a corpse's loot to roll: all of it, the table's gold and item only (what Telepathy reveals before the
// kill), or the ruleset's extra drops only (added at the kill to a corpse Telepathy revealed).
enum class CorpseLootPart : uint8_t
{
    All,
    Table,
    Extras,
};

// What a slain monster carries, as the rules size it (MonsterRules::corpseLoot).
struct CorpseLoot
{
    MonsterTable::LootPrototype loot;
    // What the item roll reads (ItemGenerationRequest): the monster's level, and whether it is a boss.
    std::optional<int> dropLevel;
    bool boss = false;
    bool omnipotent = false;
    // The seed of the corpse's rolls, so the same kill always drops the same loot; none rolls freely (Standard).
    std::optional<uint64_t> seed;

    // An item the rules add besides the table's roll (MAW: crafting materials and reagents), with what it carries.
    struct ExtraItem
    {
        uint32_t itemId = 0;
        uint16_t craftState = 0;
        uint16_t potionPower = 0;
        uint16_t dropLevel = 0;
        // All of the item's ruleset fields instead (MAW: a dimension map).
        std::optional<ItemRulesetFields> rulesetFields;
    };

    std::vector<ExtraItem> extraItems;
};
}
