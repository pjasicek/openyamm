#include "game/ItemGenerator.h"

#include "game/ItemEnchantRuntime.h"
#include "game/ItemEnchantTables.h"
#include "game/ItemRuntime.h"
#include "game/ItemTable.h"

#include <algorithm>

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

    if (!ItemRuntime::requiresIdentification(itemDefinition))
    {
        return true;
    }

    return false;
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
    }

    return item;
}

std::optional<InventoryItem> ItemGenerator::generateRandomInventoryItem(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const ItemGenerationRequest &request,
    std::mt19937 &rng,
    const std::function<bool(const ItemDefinition &)> &filter)
{
    const std::optional<uint32_t> itemId = chooseRandomBaseItem(itemTable, request.treasureLevel, rng, filter);

    if (!itemId)
    {
        return std::nullopt;
    }

    InventoryItem item = makeInventoryItem(*itemId, itemTable, request.mode);
    const ItemDefinition *pItemDefinition = itemTable.get(*itemId);

    if (pItemDefinition == nullptr || !ItemEnchantRuntime::isEnchantable(*pItemDefinition))
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
