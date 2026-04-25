#include "game/items/ItemGenerator.h"

#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cctype>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
bool defaultIdentifiedState(const ItemDefinition &itemDefinition, ItemGenerationMode mode)
{
    if (mode == ItemGenerationMode::Shop)
    {
        return true;
    }

    // Loot identification is item-driven, not chest-driven:
    // items that do not require identification spawn identified,
    // while loot items that do require identification do not.
    if (!ItemRuntime::requiresIdentification(itemDefinition))
    {
        return true;
    }

    return false;
}

bool shouldTryGenerateRareItem(const ItemGenerationRequest &request)
{
    return request.allowRareItems
        && request.mode != ItemGenerationMode::Shop
        && std::clamp(request.treasureLevel, 1, 6) >= 6;
}

std::optional<uint32_t> chooseRandomRareItem(
    const ItemTable &itemTable,
    Party *pParty,
    std::mt19937 &rng,
    const std::function<bool(const ItemDefinition &)> &filter)
{
    std::vector<uint32_t> candidateIds;

    for (const ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId == 0 || !ItemRuntime::isUniquelyGeneratedRareItem(entry))
        {
            continue;
        }

        if (filter && !filter(entry))
        {
            continue;
        }

        if (pParty != nullptr && pParty->hasFoundArtifactItem(entry.itemId))
        {
            continue;
        }

        candidateIds.push_back(entry.itemId);
    }

    if (candidateIds.empty())
    {
        return std::nullopt;
    }

    const size_t index = std::uniform_int_distribution<size_t>(0, candidateIds.size() - 1)(rng);
    return candidateIds[index];
}

int parsePositiveInteger(const std::string &value)
{
    int result = 0;
    bool hasDigit = false;

    for (char character : value)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            break;
        }

        hasDigit = true;
        result = result * 10 + character - '0';
    }

    return hasDigit ? std::max(0, result) : 0;
}

uint16_t baseWandCharges(const ItemDefinition &itemDefinition)
{
    if (itemDefinition.equipStat != "WeaponW")
    {
        return 0;
    }

    return static_cast<uint16_t>(std::clamp(parsePositiveInteger(itemDefinition.mod2) + 1, 1, 0xFFFF));
}

void initializeWandCharges(InventoryItem &item, const ItemDefinition &itemDefinition, int randomBonus)
{
    const uint16_t baseCharges = baseWandCharges(itemDefinition);

    if (baseCharges == 0)
    {
        return;
    }

    const int maxCharges = std::clamp(static_cast<int>(baseCharges) + std::max(0, randomBonus), 1, 0xFFFF);
    item.currentCharges = static_cast<uint16_t>(maxCharges);
    item.maxCharges = static_cast<uint16_t>(maxCharges);
}
}

InventoryItem ItemGenerator::makeInventoryItem(
    uint32_t itemId,
    const ItemTable &itemTable,
    ItemGenerationMode mode)
{
    InventoryItem item = {};
    item.objectDescriptionId = itemId;
    item.quantity = 1;
    const ItemDefinition *pItemDefinition = itemTable.get(itemId);

    if (pItemDefinition != nullptr)
    {
        item.width = std::max<uint8_t>(1, pItemDefinition->inventoryWidth);
        item.height = std::max<uint8_t>(1, pItemDefinition->inventoryHeight);
        item.identified = defaultIdentifiedState(*pItemDefinition, mode);
        item.rarity = pItemDefinition->rarity;
        initializeWandCharges(item, *pItemDefinition, 0);

        if (ItemRuntime::isRareItem(*pItemDefinition))
        {
            item.artifactId = static_cast<uint16_t>(std::min<uint32_t>(pItemDefinition->itemId, 0xFFFFu));
        }
    }

    return item;
}

std::optional<InventoryItem> ItemGenerator::generateRandomInventoryItem(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const ItemGenerationRequest &request,
    Party *pParty,
    std::mt19937 &rng,
    const std::function<bool(const ItemDefinition &)> &filter)
{
    if (request.rareItemsOnly)
    {
        if (!shouldTryGenerateRareItem(request))
        {
            return std::nullopt;
        }

        const std::optional<uint32_t> rareItemId = chooseRandomRareItem(itemTable, pParty, rng, filter);

        if (!rareItemId)
        {
            return std::nullopt;
        }

        InventoryItem item = makeInventoryItem(*rareItemId, itemTable, request.mode);

        if (pParty != nullptr)
        {
            pParty->markArtifactItemFound(*rareItemId);
        }

        return item;
    }

    if (shouldTryGenerateRareItem(request) && std::uniform_int_distribution<int>(0, 99)(rng) < 5)
    {
        const std::optional<uint32_t> rareItemId = chooseRandomRareItem(itemTable, pParty, rng, filter);

        if (rareItemId)
        {
            InventoryItem item = makeInventoryItem(*rareItemId, itemTable, request.mode);

            if (pParty != nullptr)
            {
                pParty->markArtifactItemFound(*rareItemId);
            }

            return item;
        }
    }

    const std::optional<uint32_t> itemId = chooseRandomBaseItem(itemTable, request.treasureLevel, rng, filter);

    if (!itemId)
    {
        return std::nullopt;
    }

    InventoryItem item = makeInventoryItem(*itemId, itemTable, request.mode);
    const ItemDefinition *pItemDefinition = itemTable.get(*itemId);

    if (pItemDefinition != nullptr && pItemDefinition->equipStat == "WeaponW")
    {
        initializeWandCharges(item, *pItemDefinition, std::uniform_int_distribution<int>(0, 5)(rng));
    }

    if (pItemDefinition == nullptr
        || ItemRuntime::isRareItem(*pItemDefinition)
        || !ItemEnchantRuntime::isEnchantable(*pItemDefinition))
    {
        return item;
    }

    const int clampedTreasureLevel = std::clamp(request.treasureLevel, 1, 6);
    const bool canHaveStandardEnchant = ItemEnchantRuntime::canHaveStandardEnchant(*pItemDefinition);
    const bool canHaveSpecialEnchant = ItemEnchantRuntime::canHaveSpecialEnchant(*pItemDefinition);
    const int standardChance =
        canHaveStandardEnchant ? ItemEnchantRuntime::standardEnchantChance(clampedTreasureLevel) : 0;
    const int specialChance =
        canHaveSpecialEnchant ? ItemEnchantRuntime::specialEnchantChance(*pItemDefinition, clampedTreasureLevel) : 0;

    if (!canHaveStandardEnchant)
    {
        if (specialChance <= 0)
        {
            return item;
        }

        if (specialChance > 0 && std::uniform_int_distribution<int>(0, 99)(rng) < specialChance)
        {
            const std::optional<uint16_t> specialEnchantId =
                ItemEnchantRuntime::chooseSpecialEnchantId(*pItemDefinition, specialItemEnchantTable, clampedTreasureLevel, rng);

            if (specialEnchantId)
            {
                item.specialEnchantId = *specialEnchantId;
            }
        }

        return item;
    }

    if (standardChance <= 0)
    {
        return item;
    }

    const int roll = std::uniform_int_distribution<int>(0, 99)(rng);

    if (roll < standardChance)
    {
        const std::optional<uint16_t> standardEnchantId =
            ItemEnchantRuntime::chooseStandardEnchantId(*pItemDefinition, standardItemEnchantTable, rng);

        if (standardEnchantId)
        {
            item.standardEnchantId = *standardEnchantId;

            const StandardItemEnchantEntry *pEntry = standardItemEnchantTable.get(*standardEnchantId);

            if (pEntry != nullptr)
            {
                item.standardEnchantPower =
                    static_cast<uint16_t>(ItemEnchantRuntime::generateStandardEnchantPower(
                        pEntry->kind,
                        clampedTreasureLevel,
                        rng));
            }
        }

        return item;
    }

    if (roll < standardChance + specialChance)
    {
        const std::optional<uint16_t> specialEnchantId =
            ItemEnchantRuntime::chooseSpecialEnchantId(*pItemDefinition, specialItemEnchantTable, clampedTreasureLevel, rng);

        if (specialEnchantId)
        {
            item.specialEnchantId = *specialEnchantId;
        }
    }

    return item;
}

std::optional<uint32_t> ItemGenerator::chooseRandomBaseItem(
    const ItemTable &itemTable,
    int treasureLevel,
    std::mt19937 &rng,
    const std::function<bool(const ItemDefinition &)> &filter)
{
    const int clampedTreasureLevel = std::clamp(treasureLevel, 1, 6);
    const size_t weightIndex = static_cast<size_t>(clampedTreasureLevel - 1);
    std::vector<uint32_t> itemIds;
    std::vector<int> weights;

    for (const ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId == 0 || weightIndex >= entry.randomTreasureWeights.size())
        {
            continue;
        }

        if (ItemRuntime::isRareItem(entry))
        {
            continue;
        }

        if (filter && !filter(entry))
        {
            continue;
        }

        const int weight = std::max(0, entry.randomTreasureWeights[weightIndex]);

        if (weight <= 0)
        {
            continue;
        }

        itemIds.push_back(entry.itemId);
        weights.push_back(weight);
    }

    if (itemIds.empty())
    {
        return std::nullopt;
    }

    std::discrete_distribution<size_t> distribution(weights.begin(), weights.end());
    const size_t index = distribution(rng);
    return index < itemIds.size() ? std::optional<uint32_t>(itemIds[index]) : std::nullopt;
}
}
