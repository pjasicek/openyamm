#pragma once

#include "game/items/ItemRulesetFields.h"
#include "game/tables/ItemTable.h"

#include <cstdint>

namespace OpenYAMM::Game
{
struct InventoryItem
{
    uint32_t objectDescriptionId = 0;
    uint32_t quantity = 1;
    uint8_t width = 1;
    uint8_t height = 1;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
    bool identified = true;
    bool broken = false;
    bool stolen = false;
    // Set by the Harden Item potion: the item can no longer break.
    bool hardened = false;
    uint16_t standardEnchantId = 0;
    uint16_t standardEnchantPower = 0;
    uint16_t specialEnchantId = 0;
    uint16_t artifactId = 0;
    ItemRarity rarity = ItemRarity::Common;
    uint16_t currentCharges = 0;
    uint16_t maxCharges = 0;
    float temporaryBonusRemainingSeconds = 0.0f;
    ItemRulesetFields rulesetFields;
    // The Workshop mod fitted to it (a world's workshop_mods row), 0: none.
    uint16_t workshopModId = 0;

    bool operator==(const InventoryItem &) const = default;
};
}
