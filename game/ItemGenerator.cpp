#include "game/ItemGenerator.h"

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

std::optional<uint32_t> ItemGenerator::chooseRandomBaseItem(
    const ItemTable &itemTable,
    int treasureLevel,
    std::mt19937 &rng)
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
