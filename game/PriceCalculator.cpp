#include "game/PriceCalculator.h"

#include "game/CharacterState.h"
#include "game/HouseTable.h"
#include "game/ItemEnchantRuntime.h"
#include "game/ItemEnchantTables.h"
#include "game/ItemTable.h"
#include "game/Party.h"
#include "game/SkillData.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
int masteryMerchantMultiplier(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return 1;

        case SkillMastery::Expert:
            return 2;

        case SkillMastery::Master:
            return 3;

        case SkillMastery::Grandmaster:
            return 5;

        case SkillMastery::None:
        default:
            return 0;
    }
}

int worstConditionSeverity(const Character &member)
{
    if (member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
    {
        return 10;
    }

    if (member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified)))
    {
        return 5;
    }

    if (member.conditions.test(static_cast<size_t>(CharacterCondition::Paralyzed))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::DiseaseMedium))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::DiseaseSevere))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::PoisonSevere)))
    {
        return 3;
    }

    if (member.conditions.test(static_cast<size_t>(CharacterCondition::Weak))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::PoisonWeak))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::PoisonMedium))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::Fear))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::Insane))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::Cursed)))
    {
        return 2;
    }

    if (member.health < member.maxHealth || member.spellPoints < member.maxSpellPoints)
    {
        return 1;
    }

    return 0;
}

int classTierForClassName(const std::string &className)
{
    static_cast<void>(className);
    return 1;
}
}

int PriceCalculator::playerMerchant(const Character *pCharacter)
{
    if (pCharacter == nullptr)
    {
        return 0;
    }

    const CharacterSkill *pMerchant = pCharacter->findSkill("Merchant");
    const int merchantBonus = std::max(0, pCharacter->merchantBonus);

    if (pMerchant == nullptr || pMerchant->mastery == SkillMastery::None)
    {
        return std::clamp(merchantBonus, 0, 100);
    }

    if (pMerchant->mastery == SkillMastery::Grandmaster)
    {
        return 100;
    }

    const int bonus = static_cast<int>(pMerchant->level) * masteryMerchantMultiplier(pMerchant->mastery) + merchantBonus;

    if (bonus <= 0)
    {
        return 0;
    }

    return std::clamp(bonus + 7, 0, 100);
}

int PriceCalculator::applyMerchantDiscount(const Character *pCharacter, int goldAmount)
{
    if (goldAmount <= 0)
    {
        return 0;
    }

    return goldAmount * (100 - playerMerchant(pCharacter)) / 100;
}

int PriceCalculator::itemBuyingPrice(
    const Character *pCharacter,
    int realValue,
    float priceMultiplier)
{
    const int clampedValue = std::max(1, realValue);
    int price = applyMerchantDiscount(pCharacter, static_cast<int>(static_cast<float>(clampedValue) * priceMultiplier));
    return std::max(clampedValue, price);
}

int PriceCalculator::itemValue(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    return ItemEnchantRuntime::itemValue(item, itemDefinition, pStandardEnchantTable, pSpecialEnchantTable);
}

int PriceCalculator::itemSellingPrice(
    const Character *pCharacter,
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    float priceMultiplier,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    if (item.broken)
    {
        return 1;
    }

    const int realValue = itemValue(item, itemDefinition, pStandardEnchantTable, pSpecialEnchantTable);

    if (realValue <= 0)
    {
        return 1;
    }

    const int merchant = playerMerchant(pCharacter);
    const int result = static_cast<int>(
        static_cast<float>(realValue) / (priceMultiplier + 2.0f)
        + static_cast<float>(realValue * merchant) / 100.0f);
    return std::clamp(result, 1, realValue) * std::max(1u, item.quantity);
}

int PriceCalculator::itemIdentificationPrice(
    const Character *pCharacter,
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    float priceMultiplier,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    const int realValue = itemValue(item, itemDefinition, pStandardEnchantTable, pSpecialEnchantTable);
    const int basePrice = std::max(1, static_cast<int>(static_cast<float>(realValue) * priceMultiplier / 32.0f));
    const int minimumPrice = std::max(1, basePrice / 3);
    return std::max(minimumPrice, applyMerchantDiscount(pCharacter, basePrice));
}

int PriceCalculator::itemRepairPrice(
    const Character *pCharacter,
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    float priceMultiplier,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    const int realValue = std::max(1, itemValue(item, itemDefinition, pStandardEnchantTable, pSpecialEnchantTable));
    const int basePrice = std::max(1, static_cast<int>(static_cast<float>(realValue) / (6.0f - priceMultiplier)));
    const int minimumPrice = std::max(1, basePrice / 3);
    return std::max(minimumPrice, applyMerchantDiscount(pCharacter, basePrice));
}

int PriceCalculator::skillLearningPrice(const Character *pCharacter, const HouseEntry &houseEntry, bool isGuild)
{
    const float multiplier = isGuild ? houseEntry.priceMultiplier : houseEntry.skillPriceMultiplier;
    const int basePrice = std::max(1, static_cast<int>(std::round(multiplier * 500.0f)));
    const int minimumPrice = std::max(1, basePrice / 3);
    return std::max(minimumPrice, applyMerchantDiscount(pCharacter, basePrice));
}

int PriceCalculator::transportPrice(const Character *pCharacter, const HouseEntry &houseEntry, bool isBoat)
{
    const int basePrice = isBoat ? 50 : 25;
    const int scaledBasePrice = std::max(1, static_cast<int>(std::round(static_cast<float>(basePrice) * houseEntry.priceMultiplier)));
    const int minimumPrice = std::max(1, basePrice / 3);
    return std::max(minimumPrice, applyMerchantDiscount(pCharacter, scaledBasePrice));
}

int PriceCalculator::tavernRoomPrice(const Character *pCharacter, const HouseEntry &houseEntry)
{
    const float houseMultiplier = houseEntry.priceMultiplier;
    const int basePrice = std::max(1, static_cast<int>(std::round(houseMultiplier * houseMultiplier / 10.0f)));
    const int minimumPrice = std::max(1, basePrice / 3);
    return std::max(minimumPrice, applyMerchantDiscount(pCharacter, basePrice));
}

int PriceCalculator::tavernFoodPrice(const Character *pCharacter, const HouseEntry &houseEntry)
{
    const float houseMultiplier = houseEntry.priceMultiplier;
    const int basePrice = std::max(1, static_cast<int>(std::round(
        houseMultiplier * houseMultiplier * houseMultiplier / 100.0f)));
    const int minimumPrice = std::max(1, basePrice / 3);
    return std::max(minimumPrice, applyMerchantDiscount(pCharacter, basePrice));
}

int PriceCalculator::templeHealPrice(const Character *pCharacter, const HouseEntry &houseEntry)
{
    const Character dummy = {};
    const Character &member = pCharacter != nullptr ? *pCharacter : dummy;
    const int severity = std::max(1, worstConditionSeverity(member));
    const int result = static_cast<int>(std::round(static_cast<float>(severity) * houseEntry.priceMultiplier));
    return std::clamp(result, 1, 10000);
}

int PriceCalculator::trainingPrice(const Character *pCharacter, const HouseEntry &houseEntry)
{
    if (pCharacter == nullptr)
    {
        return 0;
    }

    const uint64_t experienceForNextLevel =
        1000ull * static_cast<uint64_t>(pCharacter->level) * static_cast<uint64_t>(pCharacter->level + 1) / 2ull;

    if (pCharacter->experience < experienceForNextLevel)
    {
        return 0;
    }

    const int classTier = std::max(1, classTierForClassName(canonicalClassName(pCharacter->className)));
    const int basePrice = std::max(
        1,
        static_cast<int>(std::round(
            static_cast<float>(pCharacter->level) * houseEntry.priceMultiplier * static_cast<float>(classTier))));
    const int minimumPrice = std::max(1, basePrice / 3);
    return std::max(minimumPrice, applyMerchantDiscount(pCharacter, basePrice));
}
}
