#pragma once

#include "game/party/Party.h"
#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class ItemTable;
class PotionMixingTable;
struct ItemDefinition;

enum class InventoryItemMixAction : uint8_t
{
    None = 0,
    PotionMix,
    ReagentBottleMix,
    RechargePotion,
};

struct InventoryItemMixResult
{
    bool handled = false;
    bool success = false;
    bool heldItemConsumed = false;
    bool targetItemRemoved = false;
    bool targetItemChanged = false;
    InventoryItemMixAction action = InventoryItemMixAction::None;
    uint8_t failureDamageLevel = 0;
    std::optional<InventoryItem> heldItemReplacement;
    std::string statusText;
};

class InventoryItemMixingRuntime
{
public:
    static bool isWandItem(const ItemDefinition &itemDefinition);

    static uint16_t calculateSpellRechargeCharges(
        uint16_t maxCharges,
        uint16_t currentCharges,
        uint32_t skillLevel,
        SkillMastery mastery);

    static uint16_t calculatePotionRechargeCharges(
        uint16_t maxCharges,
        uint16_t currentCharges,
        uint16_t potionPower);

    static InventoryItemMixResult tryApplyHeldItemToInventoryItem(
        Party &party,
        size_t memberIndex,
        InventoryItem &heldItem,
        uint8_t targetGridX,
        uint8_t targetGridY,
        const ItemTable &itemTable,
        const PotionMixingTable &potionMixingTable);
};
}
