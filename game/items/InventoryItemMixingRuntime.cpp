#include "game/items/InventoryItemMixingRuntime.h"
#include "engine/Localization.h"

#include "game/items/InventoryBags.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemRuntime.h"
#include "game/rules/GameRules.h"
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

// What a potion does when poured onto an item (potion_effects.yml), or None for other items.
PotionItemAction potionItemAction(const MergedPotionSettingTable &potionSettingTable, uint32_t itemId)
{
    const PotionDefinition *pPotion = potionSettingTable.effects().find(itemId);
    return pPotion != nullptr ? pPotion->itemAction : PotionItemAction::None;
}

bool isWeaponItem(const ItemDefinition &itemDefinition)
{
    const ItemEnchantCategory category = ItemEnchantRuntime::categoryForItem(itemDefinition);
    return category == ItemEnchantCategory::OneHandedWeapon
        || category == ItemEnchantCategory::TwoHandedWeapon
        || category == ItemEnchantCategory::Missile;
}

// Potions poured onto a weapon or piece of equipment: Harden Item, and the weapon potions that add a temporary
// special enchantment. Refused targets keep the potion, as in the original game.
InventoryItemMixResult applyEquipmentPotion(
    const InventoryItem &heldItem,
    InventoryItem &targetItem,
    const ItemDefinition &targetDefinition,
    const MergedPotionSettingTable &potionSettingTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    const bool isEquipment = ItemEnchantRuntime::categoryForItem(targetDefinition) != ItemEnchantCategory::None
        || InventoryItemMixingRuntime::isWandItem(targetDefinition);

    if (!isEquipment)
    {
        return {};
    }

    InventoryItemMixResult result = {};
    result.handled = true;

    const PotionItemAction potionAction = potionItemAction(potionSettingTable, heldItem.objectDescriptionId);

    if (potionAction == PotionItemAction::Harden)
    {
        result.action = InventoryItemMixAction::HardenPotion;

        if (targetItem.broken || ItemRuntime::isArtifact(targetDefinition))
        {
            return result;
        }

        if (targetItem.hardened)
        {
            result.statusText = Engine::tr("Item already hardened!");
            return result;
        }

        targetItem.hardened = true;
        result.success = true;
        result.heldItemConsumed = true;
        result.targetItemChanged = true;
        return result;
    }

    if (potionAction != PotionItemAction::TemporarySpecialEnchant)
    {
        return {};
    }

    result.action = InventoryItemMixAction::WeaponEnchantPotion;
    const PotionEffectTable &potionEffects = potionSettingTable.effects();
    const SpecialItemEnchantKind enchantKind = potionEffects.find(heldItem.objectDescriptionId)->enchant;
    const uint16_t enchantId = pSpecialEnchantTable != nullptr ? pSpecialEnchantTable->findId(enchantKind) : 0;

    // Only plain weapons take the enchantment; blasters, artifacts and enchanted weapons refuse it.
    if (enchantId == 0
        || !isWeaponItem(targetDefinition)
        || targetDefinition.skillGroup == "Blaster"
        || targetItem.broken
        || ItemRuntime::isArtifact(targetDefinition)
        || targetItem.rarity != ItemRarity::Common
        || targetItem.artifactId != 0
        || targetItem.standardEnchantId != 0
        || targetItem.specialEnchantId != 0)
    {
        return result;
    }

    // A zero duration would make the enchantment permanent, so a powerless potion still lasts 30 minutes.
    const uint16_t power = std::max<uint16_t>(1, itemPower(heldItem));
    targetItem.specialEnchantId = enchantId;
    targetItem.temporaryBonusRemainingSeconds = static_cast<float>(power) * potionEffects.timedSecondsPerPower();
    result.success = true;
    result.heldItemConsumed = true;
    result.targetItemChanged = true;
    return result;
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

    if (potionItemAction(potionSettingTable, heldItemId) == PotionItemAction::RechargeWand)
    {
        if (!isWandItem(*pTargetDefinition) || targetItem.broken)
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
            result.statusText = Engine::tr("Wand already charged!");
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
        [alchemyLevel, alchemyMastery](InventoryItem &bottle,
            uint32_t resultItemId, const ItemDefinition &reagentDefinition, const InventoryItem &reagent)
        {
            const uint32_t power = alchemyLevel
                + uint32_t(std::max(0,
                    boundGameRules().potions.reagentPower(reagentDefinition, reagent, alchemyMastery, alchemyLevel)));
            bottle.objectDescriptionId = resultItemId;
            bottle.standardEnchantPower = static_cast<uint16_t>(std::min<uint32_t>(0xFFFFu, power));
            bottle.identified = true;

            InventoryItemMixResult result = {};
            result.handled = true;
            result.success = true;
            result.heldItemConsumed = true;
            result.targetItemChanged = true;
            result.action = InventoryItemMixAction::ReagentBottleMix;
            result.statusText = Engine::tr("Mixed potion");
            return result;
        };

    if (heldReagentResult.has_value() && targetItemId == bottleItemId)
    {
        return mixReagentIntoBottle(targetItem, *heldReagentResult, *pHeldDefinition, heldItem);
    }

    if (heldItemId == bottleItemId && targetReagentResult.has_value())
    {
        // The held bottle takes the potion and the reagent is used up: a potion does not fit a reagent's slot.
        InventoryItem potion = heldItem;
        InventoryItemMixResult result =
            mixReagentIntoBottle(potion, *targetReagentResult, *pTargetDefinition, targetItem);
        result.targetItemChanged = false;
        result.targetItemRemoved = true;

        if (const ItemDefinition *pPotionDefinition = itemTable.get(potion.objectDescriptionId))
        {
            potion.width = std::max<uint8_t>(1, pPotionDefinition->inventoryWidth);
            potion.height = std::max<uint8_t>(1, pPotionDefinition->inventoryHeight);
        }

        result.heldItemReplacement = potion;
        return result;
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
        const int power = boundGameRules().potions.catalystMixPower(itemPower(targetItem), itemPower(heldItem),
            heldItemId == catalystItemId && targetItemId == catalystItemId, alchemyMastery, alchemyLevel);

        if (targetItemId == catalystItemId)
        {
            targetItem.objectDescriptionId = heldItemId;
        }

        targetItem.standardEnchantPower = uint16_t(std::clamp(power, 0, 0xFFFF));

        targetItem.identified = true;
        result.success = true;
        result.heldItemConsumed = true;
        result.targetItemChanged = true;
        result.returnsBottle = true;
        result.statusText = Engine::tr("Mixed potion");
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
        result.statusText = Engine::tr("Ooops");
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

    result.statusText = Engine::tr("Mixed potion");
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
    const ItemDefinition *pTargetDefinition = itemTable.get(targetItemId);
    InventoryItemMixResult result = pTargetDefinition != nullptr
        ? applyEquipmentPotion(
            heldItem,
            *pTargetItem,
            *pTargetDefinition,
            potionSettingTable,
            party.specialItemEnchantTable())
        : InventoryItemMixResult {};

    if (!result.handled)
    {
        result = mixItems(
            heldItem,
            *pTargetItem,
            alchemyMastery(alchemyMember),
            gameRulesFor(&party).potions.mixingAlchemyLevel(alchemyMember),
            itemTable,
            potionMixingTable,
            potionSettingTable,
            reagentSettingTable,
            pPotionNoteTable);
    }

    if (result.targetItemRemoved)
    {
        InventoryItem removedItem = {};
        party.takeItemFromMemberInventoryCell(memberIndex, pTargetItem->gridX, pTargetItem->gridY, removedItem);
    }
    else if (result.targetItemChanged)
    {
        // A bottle mixed into its potion takes the potion's size in the bag (OY-240).
        InventoryBags::refitChangedItem(party, memberIndex, pMember->rulesetState.currentBag,
            gameRulesFor(&party).items.bagCount(party), pTargetItem->gridX, pTargetItem->gridY, itemTable);
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
