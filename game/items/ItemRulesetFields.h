#pragma once

#include <array>
#include <cstdint>

namespace OpenYAMM::Game
{
// Item state that only a ruleset uses (MAW: devdocs/maw/HANDOFF.md §3.7). Standard items leave it empty, and saves
// store it only for items that have it.
struct ItemRulesetFields
{
    // A second standard enchantment besides InventoryItem::standardEnchantId.
    uint16_t secondStandardEnchantId = 0;
    uint16_t secondStandardEnchantPower = 0;
    // The ruleset's loot rarity tier, stored when the item drops and never derived (separate from ItemRarity).
    uint8_t lootRarity = 0;
    // MAW's ancient tier from the drop (1 Ancient, 2 Primordial or Celestial), kept apart from a legendary affix and the
    // Celestial status, so the rarity reads back as MAW's does when crafting takes those away.
    uint8_t ancientTier = 0;
    uint16_t legendaryAffixId = 0;
    uint16_t itemPower = 0;
    uint16_t dropLevel = 0;
    uint8_t qualityPercent = 0;
    uint32_t craftSeed = 0;
    uint8_t potionCharges = 0;
    // How often the item was crafted on (it moves the item's craft random stream on), and what a stateful item holds
    // (an orb's stored affix, a charged Celestial Orb, the charges an Endless Potion adds, the book id inside a sealed
    // spellbook).
    uint16_t craftCount = 0;
    uint16_t craftState = 0;
    // A dimension map (MAW): the map table id it opens, four affix slots, the active slots (0: all four) and its power.
    uint16_t dimensionMapId = 0;
    std::array<uint8_t, 4> dimensionAffixes = {};
    uint8_t dimensionActiveSlots = 0;
    uint8_t dimensionPower = 0;
    // The loot filter left the drop where it fell instead of turning it into gold (RulesetLootFilter::leaveOnGround): it
    // shows a grey outline there in place of its rarity's.
    uint8_t lootFiltered = 0;

    bool empty() const
    {
        return *this == ItemRulesetFields{};
    }

    bool operator==(const ItemRulesetFields &) const = default;
};
}
