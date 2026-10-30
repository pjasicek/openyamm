#include "game/items/InventoryItemMixingRuntime.h"

#include "game/tables/ItemTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/PotionMixingTable.h"
#include "game/tables/PotionNoteTable.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t RechargePotionItemId = 233;

bool parsePositiveInteger(const std::string &value, uint32_t &result)
{
    result = 0;
    bool hasDigit = false;

    for (char character : value)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            break;
        }

        hasDigit = true;
        result = result * 10 + static_cast<uint32_t>(character - '0');
    }

    return hasDigit;
}

uint16_t itemPower(const InventoryItem &item)
{
    return item.standardEnchantPower;
}

uint16_t averagePotionPower(const InventoryItem &heldItem, const InventoryItem &targetItem)
{
    return static_cast<uint16_t>((static_cast<uint32_t>(itemPower(heldItem)) + itemPower(targetItem)) / 2u);
}

SkillMastery alchemyMastery(const Character &member)
{
    const CharacterSkill *pSkill = member.findSkill("Alchemy");
    return pSkill != nullptr ? pSkill->mastery : SkillMastery::None;
}

uint32_t alchemyLevel(const Character &member)
{
    const CharacterSkill *pSkill = member.findSkill("Alchemy");
    return pSkill != nullptr ? pSkill->level : 0;
}

uint8_t requiredFailureDamageLevel(
    uint32_t resultItemId,
    SkillMastery mastery,
    const MergedPotionSettingTable &potionSettingTable)
{
    const MergedPotionSettingEntry *pSetting = potionSettingTable.getByItemId(resultItemId);

    if (pSetting == nullptr || !pSetting->requiredMastery.has_value() || *pSetting->requiredMastery == 0)
    {
        return 0;
    }

    return static_cast<uint32_t>(mastery) < *pSetting->requiredMastery
        ? static_cast<uint8_t>(std::min<uint32_t>(*pSetting->requiredMastery, 255))
        : 0;
}

void attachBottleResult(
    Party &party,
    size_t memberIndex,
    const ItemTable &itemTable,
    uint32_t bottleItemId,
    InventoryItemMixResult &result)
{
    InventoryItem bottle = InventoryItemMixingRuntime::makeBottleItem(itemTable, bottleItemId);

    if (!party.tryAutoPlaceItemInMemberInventory(memberIndex, bottle))
    {
        result.heldItemReplacement = bottle;
    }
}
}

InventoryItem InventoryItemMixingRuntime::makeBottleItem(const ItemTable &itemTable, uint32_t bottleItemId)
{
    InventoryItem bottle = {};
    bottle.objectDescriptionId = bottleItemId;
    bottle.quantity = 1;

    if (const ItemDefinition *pDefinition = itemTable.get(bottleItemId))
    {
        bottle.width = std::max<uint8_t>(1, pDefinition->inventoryWidth);
        bottle.height = std::max<uint8_t>(1, pDefinition->inventoryHeight);
    }

    return bottle;
}

uint16_t InventoryItemMixingRuntime::reagentPower(const ItemDefinition &itemDefinition)
{
    uint32_t power = 0;
    return parsePositiveInteger(itemDefinition.mod1, power)
        ? static_cast<uint16_t>(std::min<uint32_t>(power, 0xFFFFu))
        : 0;
}

bool InventoryItemMixingRuntime::isWandItem(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "WeaponW";
}

uint16_t InventoryItemMixingRuntime::calculateSpellRechargeCharges(
    uint16_t maxCharges,
    uint16_t currentCharges,
    uint32_t skillLevel,
    SkillMastery mastery)
{
    float factor = 0.0f;

    if (mastery == SkillMastery::Normal || mastery == SkillMastery::Expert)
    {
        factor = 0.5f + static_cast<float>(skillLevel) * 0.01f;
    }
    else if (mastery == SkillMastery::Master)
    {
        factor = 0.7f + static_cast<float>(skillLevel) * 0.01f;
    }
    else if (mastery == SkillMastery::Grandmaster)
    {
        factor = 0.8f + static_cast<float>(skillLevel) * 0.01f;
    }

    factor = std::clamp(factor, 0.0f, 1.0f);
    const uint16_t newCharges = static_cast<uint16_t>(static_cast<float>(maxCharges) * factor);
    return newCharges > currentCharges ? newCharges : 0;
}

uint16_t InventoryItemMixingRuntime::calculatePotionRechargeCharges(
    uint16_t maxCharges,
    uint16_t currentCharges,
    uint16_t potionPower)
{
    const int maxChargesDecreasePercent = std::max(0, 70 - static_cast<int>(potionPower));
    const float factor = static_cast<float>(100 - maxChargesDecreasePercent) * 0.01f;
    const uint16_t newCharges = static_cast<uint16_t>(static_cast<float>(maxCharges) * factor);
    return newCharges > currentCharges ? newCharges : 0;
}

InventoryItemMixResult InventoryItemMixingRuntime::mixItems(
    InventoryItem &heldItem,
    InventoryItem &targetItem,
    SkillMastery alchemyMastery,
    uint32_t alchemyLevel,
    const ItemTable &itemTable,
    const PotionMixingTable &potionMixingTable,
    const MergedPotionSettingTable &potionSettingTable,
    const MergedReagentSettingTable &reagentSettingTable,
    const PotionNoteTable *pPotionNoteTable)
{
    const ItemDefinition *pHeldDefinition = itemTable.get(heldItem.objectDescriptionId);
    const ItemDefinition *pTargetDefinition = itemTable.get(targetItem.objectDescriptionId);

    if (pHeldDefinition == nullptr || pTargetDefinition == nullptr)
    {
        return {};
    }

    const uint32_t bottleItemId = potionSettingTable.emptyBottleItemId();
    const uint32_t catalystItemId = potionSettingTable.catalystPotionItemId();
    const uint32_t heldItemId = heldItem.objectDescriptionId;
    const uint32_t targetItemId = targetItem.objectDescriptionId;
    const MergedPotionSettingEntry *pHeldPotionSetting = potionSettingTable.getByItemId(heldItemId);
    const MergedPotionSettingEntry *pTargetPotionSetting = potionSettingTable.getByItemId(targetItemId);

    if (heldItemId == RechargePotionItemId && isWandItem(*pTargetDefinition))
    {
        if (targetItem.broken)
        {
            return {};
        }

        InventoryItemMixResult result = {};
        result.handled = true;
        result.action = InventoryItemMixAction::RechargePotion;
        result.heldItemConsumed = true;
        const uint16_t newCharges =
            calculatePotionRechargeCharges(targetItem.maxCharges, targetItem.currentCharges, itemPower(heldItem));

        if (newCharges == 0)
        {
            result.statusText = "Wand already charged!";
            return result;
        }

        targetItem.maxCharges = newCharges;
        targetItem.currentCharges = newCharges;
        result.success = true;
        result.targetItemChanged = true;
        return result;
    }

    const std::optional<uint32_t> heldReagentResult = reagentSettingTable.resultItemIdForReagent(heldItemId);
    const std::optional<uint32_t> targetReagentResult = reagentSettingTable.resultItemIdForReagent(targetItemId);
    const auto mixReagentIntoBottle =
        [&targetItem, alchemyLevel](uint32_t resultItemId, const ItemDefinition &reagentDefinition)
        {
            targetItem.objectDescriptionId = resultItemId;
            const uint32_t power = alchemyLevel + InventoryItemMixingRuntime::reagentPower(reagentDefinition);
            targetItem.standardEnchantPower = static_cast<uint16_t>(std::min<uint32_t>(0xFFFFu, power));
            targetItem.identified = true;

            InventoryItemMixResult result = {};
            result.handled = true;
            result.success = true;
            result.heldItemConsumed = true;
            result.targetItemChanged = true;
            result.action = InventoryItemMixAction::ReagentBottleMix;
            result.statusText = "Mixed potion";
            return result;
        };

    if (heldReagentResult.has_value() && targetItemId == bottleItemId)
    {
        return mixReagentIntoBottle(*heldReagentResult, *pHeldDefinition);
    }

    if (heldItemId == bottleItemId && targetReagentResult.has_value())
    {
        return mixReagentIntoBottle(*targetReagentResult, *pTargetDefinition);
    }

    if (pHeldPotionSetting == nullptr || pTargetPotionSetting == nullptr)
    {
        return {};
    }

    InventoryItemMixResult result = {};
    result.handled = true;
    result.action = InventoryItemMixAction::PotionMix;

    if (heldItemId == catalystItemId || targetItemId == catalystItemId)
    {
        if (heldItemId == catalystItemId && targetItemId == catalystItemId)
        {
            targetItem.standardEnchantPower = std::max(itemPower(targetItem), itemPower(heldItem));
        }
        else if (targetItemId == catalystItemId)
        {
            targetItem.objectDescriptionId = heldItemId;
            targetItem.standardEnchantPower = itemPower(heldItem);
        }
        else
        {
            targetItem.standardEnchantPower = itemPower(heldItem);
        }

        targetItem.identified = true;
        result.success = true;
        result.heldItemConsumed = true;
        result.targetItemChanged = true;
        result.returnsBottle = true;
        result.statusText = "Mixed potion";
        return result;
    }

    const std::optional<PotionMixingTable::PotionCombination> combination =
        potionMixingTable.potionCombination(heldItemId, targetItemId);

    if (!combination || combination->noMix)
    {
        return {};
    }

    const uint8_t damageLevel = combination->failureDamageLevel != 0
        ? combination->failureDamageLevel
        : requiredFailureDamageLevel(combination->resultItemId, alchemyMastery, potionSettingTable);

    if (damageLevel != 0)
    {
        result.success = false;
        result.heldItemConsumed = true;
        result.targetItemRemoved = true;
        result.failureDamageLevel = damageLevel;
        result.statusText = "Ooops";
        return result;
    }

    targetItem.objectDescriptionId = combination->resultItemId;
    targetItem.standardEnchantPower = averagePotionPower(heldItem, targetItem);
    targetItem.identified = true;
    result.success = true;
    result.heldItemConsumed = true;
    result.targetItemChanged = true;
    result.returnsBottle = true;

    if (pPotionNoteTable != nullptr)
    {
        const std::optional<uint32_t> autonoteId = pPotionNoteTable->autonoteIdForMix(targetItemId, heldItemId);

        if (autonoteId.has_value())
        {
            result.unlockedAutonoteId = *autonoteId;
        }
    }

    result.statusText = "Mixed potion";
    return result;
}

InventoryItemMixResult InventoryItemMixingRuntime::tryApplyHeldItemToInventoryItem(
    Party &party,
    size_t memberIndex,
    InventoryItem &heldItem,
    uint8_t targetGridX,
    uint8_t targetGridY,
    const ItemTable &itemTable,
    const PotionMixingTable &potionMixingTable,
    const MergedPotionSettingTable &potionSettingTable,
    const MergedReagentSettingTable &reagentSettingTable,
    const PotionNoteTable *pPotionNoteTable)
{
    Character *pMember = party.member(memberIndex);
    InventoryItem *pTargetItem = party.memberInventoryItemMutable(memberIndex, targetGridX, targetGridY);

    if (pMember == nullptr || pTargetItem == nullptr)
    {
        return {};
    }

    const Character *pAlchemyMember = party.bestPartyWideUtilitySkillMember("Alchemy");
    const Character &alchemyMember = pAlchemyMember != nullptr ? *pAlchemyMember : *pMember;
    const uint32_t targetItemId = pTargetItem->objectDescriptionId;
    const uint32_t heldItemId = heldItem.objectDescriptionId;
    InventoryItemMixResult result = mixItems(
        heldItem,
        *pTargetItem,
        alchemyMastery(alchemyMember),
        alchemyLevel(alchemyMember),
        itemTable,
        potionMixingTable,
        potionSettingTable,
        reagentSettingTable,
        pPotionNoteTable);

    if (result.targetItemRemoved)
    {
        InventoryItem removedItem = {};
        party.takeItemFromMemberInventoryCell(memberIndex, pTargetItem->gridX, pTargetItem->gridY, removedItem);
    }

    if (result.failureDamageLevel != 0)
    {
        party.recordExplosiveMix(targetItemId, heldItemId);
    }

    if (result.returnsBottle)
    {
        attachBottleResult(party, memberIndex, itemTable, potionSettingTable.emptyBottleItemId(), result);
    }

    return result;
}
}
