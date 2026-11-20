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
class MergedPotionSettingTable;
class MergedReagentSettingTable;
class PotionMixingTable;
class PotionNoteTable;
struct ItemDefinition;

enum class InventoryItemMixAction : uint8_t
{
    None = 0,
    PotionMix,
    ReagentBottleMix,
    RechargePotion,
    HardenPotion,
    WeaponEnchantPotion,
};

struct InventoryItemMixResult
{
    bool handled = false;
    bool success = false;
    bool heldItemConsumed = false;
    bool targetItemRemoved = false;
    bool targetItemChanged = false;
    // The mix leaves an empty bottle behind; tryApplyHeldItemToInventoryItem places it in the pack.
    bool returnsBottle = false;
    InventoryItemMixAction action = InventoryItemMixAction::None;
    uint8_t failureDamageLevel = 0;
    uint32_t unlockedAutonoteId = 0;
    std::optional<InventoryItem> heldItemReplacement;
    std::string statusText;
};

class InventoryItemMixingRuntime
{
public:
    static bool isWandItem(const ItemDefinition &itemDefinition);
    static InventoryItem makeBottleItem(const ItemTable &itemTable, uint32_t bottleItemId);
    // The power a reagent adds to the alchemist's skill level when it fills a bottle.
    static uint16_t reagentPower(const ItemDefinition &itemDefinition);

    static uint16_t calculateSpellRechargeCharges(
        uint16_t maxCharges,
        uint16_t currentCharges,
        uint32_t skillLevel,
        SkillMastery mastery);

    static uint16_t calculatePotionRechargeCharges(
        uint16_t maxCharges,
        uint16_t currentCharges,
        uint16_t potionPower);

    // Mixes heldItem into targetItem by the potion rules alone; the caller owns both items and their removal.
    static InventoryItemMixResult mixItems(
        InventoryItem &heldItem,
        InventoryItem &targetItem,
        SkillMastery alchemyMastery,
        uint32_t alchemyLevel,
        const ItemTable &itemTable,
        const PotionMixingTable &potionMixingTable,
        const MergedPotionSettingTable &potionSettingTable,
        const MergedReagentSettingTable &reagentSettingTable,
        const PotionNoteTable *pPotionNoteTable = nullptr);

    static InventoryItemMixResult tryApplyHeldItemToInventoryItem(
        Party &party,
        size_t memberIndex,
        InventoryItem &heldItem,
        uint8_t targetGridX,
        uint8_t targetGridY,
        const ItemTable &itemTable,
        const PotionMixingTable &potionMixingTable,
        const MergedPotionSettingTable &potionSettingTable,
        const MergedReagentSettingTable &reagentSettingTable,
        const PotionNoteTable *pPotionNoteTable = nullptr);
};
}
