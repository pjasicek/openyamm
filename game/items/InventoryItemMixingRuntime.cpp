#include "game/items/InventoryItemMixingRuntime.h"

#include "game/tables/ItemTable.h"
#include "game/tables/PotionMixingTable.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t FirstReagentItemId = 200;
constexpr uint32_t LastReagentItemId = 219;
constexpr uint32_t PotionBottleItemId = 220;
constexpr uint32_t CatalystPotionItemId = 221;
constexpr uint32_t FirstPotionItemId = 222;
constexpr uint32_t LastPotionItemId = 271;
constexpr uint32_t RechargePotionItemId = 233;

bool isReagent(uint32_t itemId)
{
    return itemId >= FirstReagentItemId && itemId <= LastReagentItemId;
}

bool isMixingPotion(uint32_t itemId)
{
    return itemId >= CatalystPotionItemId && itemId <= LastPotionItemId;
}

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

uint8_t requiredFailureDamageLevel(uint32_t resultItemId, SkillMastery mastery)
{
    if (resultItemId >= 225 && resultItemId <= 227 && mastery == SkillMastery::None)
    {
        return 1;
    }

    if (resultItemId >= 228 && resultItemId <= 239 && mastery <= SkillMastery::Normal)
    {
        return 2;
    }

    if (resultItemId >= 240 && resultItemId <= 261 && mastery <= SkillMastery::Expert)
    {
        return 3;
    }

    if (resultItemId >= 262 && mastery <= SkillMastery::Master)
    {
        return 4;
    }

    return 0;
}

uint32_t reagentPotionResultItemId(uint32_t reagentItemId)
{
    if (reagentItemId >= 200 && reagentItemId <= 204)
    {
        return 222;
    }

    if (reagentItemId >= 205 && reagentItemId <= 209)
    {
        return 223;
    }

    if (reagentItemId >= 210 && reagentItemId <= 214)
    {
        return 224;
    }

    if (reagentItemId >= 215 && reagentItemId <= 219)
    {
        return 221;
    }

    return 0;
}

uint16_t reagentPower(const ItemDefinition &itemDefinition)
{
    uint32_t power = 0;
    return parsePositiveInteger(itemDefinition.mod1, power)
        ? static_cast<uint16_t>(std::min<uint32_t>(power, 0xFFFFu))
        : 0;
}

InventoryItem makeBottleItem(const ItemTable &itemTable)
{
    InventoryItem bottle = {};
    bottle.objectDescriptionId = PotionBottleItemId;
    bottle.quantity = 1;

    if (const ItemDefinition *pDefinition = itemTable.get(PotionBottleItemId))
    {
        bottle.width = std::max<uint8_t>(1, pDefinition->inventoryWidth);
        bottle.height = std::max<uint8_t>(1, pDefinition->inventoryHeight);
    }

    return bottle;
}

void attachBottleResult(
    Party &party,
    size_t memberIndex,
    const ItemTable &itemTable,
    InventoryItemMixResult &result)
{
    InventoryItem bottle = makeBottleItem(itemTable);

    if (!party.tryAutoPlaceItemInMemberInventory(memberIndex, bottle))
    {
        result.heldItemReplacement = bottle;
    }
}

InventoryItemMixResult makeFailureResult(InventoryItemMixAction action, const std::string &statusText)
{
    InventoryItemMixResult result = {};
    result.handled = true;
    result.success = false;
    result.action = action;
    result.statusText = statusText;
    return result;
}
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

InventoryItemMixResult InventoryItemMixingRuntime::tryApplyHeldItemToInventoryItem(
    Party &party,
    size_t memberIndex,
    InventoryItem &heldItem,
    uint8_t targetGridX,
    uint8_t targetGridY,
    const ItemTable &itemTable,
    const PotionMixingTable &potionMixingTable)
{
    Character *pMember = party.member(memberIndex);
    InventoryItem *pTargetItem = party.memberInventoryItemMutable(memberIndex, targetGridX, targetGridY);

    if (pMember == nullptr || pTargetItem == nullptr)
    {
        return {};
    }

    const ItemDefinition *pHeldDefinition = itemTable.get(heldItem.objectDescriptionId);
    const ItemDefinition *pTargetDefinition = itemTable.get(pTargetItem->objectDescriptionId);

    if (pHeldDefinition == nullptr || pTargetDefinition == nullptr)
    {
        return {};
    }

    if (heldItem.objectDescriptionId == RechargePotionItemId)
    {
        if (!isWandItem(*pTargetDefinition) || pTargetItem->broken)
        {
            return {};
        }

        InventoryItemMixResult result = {};
        result.handled = true;
        result.action = InventoryItemMixAction::RechargePotion;
        result.heldItemConsumed = true;
        const uint16_t newCharges =
            calculatePotionRechargeCharges(pTargetItem->maxCharges, pTargetItem->currentCharges, itemPower(heldItem));

        if (newCharges == 0)
        {
            result.statusText = "Wand already charged!";
            return result;
        }

        pTargetItem->maxCharges = newCharges;
        pTargetItem->currentCharges = newCharges;
        result.success = true;
        result.targetItemChanged = true;
        return result;
    }

    if (isReagent(heldItem.objectDescriptionId) && pTargetItem->objectDescriptionId == PotionBottleItemId)
    {
        const uint32_t resultItemId = reagentPotionResultItemId(heldItem.objectDescriptionId);

        if (resultItemId == 0)
        {
            return {};
        }

        pTargetItem->objectDescriptionId = resultItemId;
        pTargetItem->standardEnchantPower =
            static_cast<uint16_t>(std::min<uint32_t>(
                0xFFFFu,
                alchemyLevel(*pMember) + reagentPower(*pHeldDefinition)));
        pTargetItem->identified = true;

        InventoryItemMixResult result = {};
        result.handled = true;
        result.success = true;
        result.heldItemConsumed = true;
        result.targetItemChanged = true;
        result.action = InventoryItemMixAction::ReagentBottleMix;
        result.statusText = "Mixed potion";
        return result;
    }

    if (heldItem.objectDescriptionId == PotionBottleItemId && isReagent(pTargetItem->objectDescriptionId))
    {
        const uint32_t resultItemId = reagentPotionResultItemId(pTargetItem->objectDescriptionId);

        if (resultItemId == 0)
        {
            return {};
        }

        pTargetItem->objectDescriptionId = resultItemId;
        pTargetItem->standardEnchantPower =
            static_cast<uint16_t>(std::min<uint32_t>(
                0xFFFFu,
                alchemyLevel(*pMember) + reagentPower(*pTargetDefinition)));
        pTargetItem->identified = true;

        InventoryItemMixResult result = {};
        result.handled = true;
        result.success = true;
        result.heldItemConsumed = true;
        result.targetItemChanged = true;
        result.action = InventoryItemMixAction::ReagentBottleMix;
        result.statusText = "Mixed potion";
        return result;
    }

    if (!isMixingPotion(heldItem.objectDescriptionId) || !isMixingPotion(pTargetItem->objectDescriptionId))
    {
        return {};
    }

    InventoryItemMixResult result = {};
    result.handled = true;
    result.action = InventoryItemMixAction::PotionMix;

    if (heldItem.objectDescriptionId == CatalystPotionItemId
        || pTargetItem->objectDescriptionId == CatalystPotionItemId)
    {
        if (heldItem.objectDescriptionId == CatalystPotionItemId
            && pTargetItem->objectDescriptionId == CatalystPotionItemId)
        {
            pTargetItem->standardEnchantPower = std::max(itemPower(*pTargetItem), itemPower(heldItem));
        }
        else if (pTargetItem->objectDescriptionId == CatalystPotionItemId)
        {
            pTargetItem->objectDescriptionId = heldItem.objectDescriptionId;
            pTargetItem->standardEnchantPower = itemPower(heldItem);
        }
        else
        {
            pTargetItem->standardEnchantPower = itemPower(heldItem);
        }

        pTargetItem->identified = true;
        result.success = true;
        result.heldItemConsumed = true;
        result.targetItemChanged = true;
        result.statusText = "Mixed potion";
        attachBottleResult(party, memberIndex, itemTable, result);
        return result;
    }

    const std::optional<PotionMixingTable::PotionCombination> combination =
        potionMixingTable.potionCombination(heldItem.objectDescriptionId, pTargetItem->objectDescriptionId);

    if (!combination || combination->noMix)
    {
        return {};
    }

    const uint8_t damageLevel = combination->failureDamageLevel != 0
        ? combination->failureDamageLevel
        : requiredFailureDamageLevel(combination->resultItemId, alchemyMastery(*pMember));

    if (damageLevel != 0)
    {
        InventoryItem removedItem = {};
        party.takeItemFromMemberInventoryCell(memberIndex, pTargetItem->gridX, pTargetItem->gridY, removedItem);
        result.success = false;
        result.heldItemConsumed = true;
        result.targetItemRemoved = true;
        result.failureDamageLevel = damageLevel;
        result.statusText = "Ooops";
        return result;
    }

    pTargetItem->objectDescriptionId = combination->resultItemId;
    pTargetItem->standardEnchantPower = averagePotionPower(heldItem, *pTargetItem);
    pTargetItem->identified = true;
    result.success = true;
    result.heldItemConsumed = true;
    result.targetItemChanged = true;
    result.statusText = "Mixed potion";
    attachBottleResult(party, memberIndex, itemTable, result);
    return result;
}
}
