#include "game/gameplay/LootContainerRuntime.h"

#include "game/events/EvtEnums.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cstring>
#include <random>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t ChestItemRecordSize = 36;
constexpr size_t ChestItemGoldAmountOffset = 0x0c;
constexpr size_t DefaultChestGridSize = 9 * 9;

uint32_t makeContainerSeed(uint32_t sessionSeed, int mapId, uint32_t containerId)
{
    return sessionSeed
        ^ static_cast<uint32_t>(mapId) * 1315423911u
        ^ (containerId + 1u) * 2654435761u;
}

int generatedGoldAmount(int treasureLevel, std::mt19937 &rng)
{
    switch (std::clamp(treasureLevel, 1, 6))
    {
        case 1: return std::uniform_int_distribution<int>(50, 100)(rng);
        case 2: return std::uniform_int_distribution<int>(100, 200)(rng);
        case 3: return std::uniform_int_distribution<int>(200, 500)(rng);
        case 4: return std::uniform_int_distribution<int>(500, 1000)(rng);
        case 5: return std::uniform_int_distribution<int>(1000, 2000)(rng);
        default: return std::uniform_int_distribution<int>(2000, 5000)(rng);
    }
}

uint32_t findGoldHeapItemId(const ItemTable *pItemTable)
{
    if (pItemTable == nullptr)
    {
        return 0;
    }

    for (const ItemDefinition &item : pItemTable->entries())
    {
        if (item.isGold())
        {
            return item.itemId;
        }
    }
    return 0;
}

void appendRecord(MapDeltaChest &chest, int32_t itemId, int32_t goldAmount = 0)
{
    const size_t recordIndex = chest.rawItems.size() / ChestItemRecordSize;
    chest.rawItems.resize(chest.rawItems.size() + ChestItemRecordSize, 0);
    std::memcpy(chest.rawItems.data() + recordIndex * ChestItemRecordSize, &itemId, sizeof(itemId));
    if (goldAmount > 0)
    {
        std::memcpy(
            chest.rawItems.data() + recordIndex * ChestItemRecordSize + ChestItemGoldAmountOffset,
            &goldAmount,
            sizeof(goldAmount));
    }
    if (recordIndex < chest.inventoryMatrix.size())
    {
        chest.inventoryMatrix[recordIndex] = static_cast<int16_t>(recordIndex + 1);
    }
}
}

MapLootContainerSource materializeSpawnedLootContainerSource(
    const MapSpawnedLootContainerSource &source,
    uint32_t containerId)
{
    MapLootContainerSource materialized = {};
    materialized.sourceId = source.sourceId;
    materialized.sourceObjectIndex = source.sourceObjectIndex;
    materialized.sourceName = source.sourceName;
    materialized.position = source.position;
    materialized.containerId = containerId;
    materialized.kind = source.kind;
    materialized.presentation = source.presentation;
    materialized.randomTreasureLevel = source.randomTreasureLevel;
    materialized.treasureType = source.treasureType;
    materialized.gold = source.gold;
    materialized.goldOnly = source.goldOnly;
    materialized.random = source.random;
    materialized.aiDrop = source.aiDrop;
    materialized.fixedItems = source.fixedItems;
    materialized.removeWhenEmpty = source.removeWhenEmpty;
    return materialized;
}

MapDeltaChest buildLootContainerChest(
    const MapLootContainerSource &source,
    int mapTreasureLevel,
    int mapId,
    uint32_t sessionSeed,
    const ItemTable *pItemTable,
    const ChestTable *pChestTable)
{
    MapDeltaChest chest = {};
    if (pChestTable != nullptr && !source.presentation.empty())
    {
        chest.chestTypeId = pChestTable->findIdByName(source.presentation).value_or(0);
    }
    chest.inventoryMatrix.assign(DefaultChestGridSize, 0);
    if (source.trapLevel > 0)
    {
        chest.flags |= static_cast<uint16_t>(EvtChestFlag::Trapped);
    }

    for (const MapFixedContainerItem &item : source.fixedItems)
    {
        appendRecord(chest, static_cast<int32_t>(item.itemId));
    }

    std::mt19937 rng(makeContainerSeed(sessionSeed, mapId, source.containerId));
    if (source.goldOnly || source.gold > 0)
    {
        const uint32_t goldHeapItemId = findGoldHeapItemId(pItemTable);
        const int treasureLevel = source.randomTreasureLevel > 0
            ? source.randomTreasureLevel
            : std::max(1, mapTreasureLevel + 1);
        const int goldAmount = source.gold > 0 ? source.gold : generatedGoldAmount(treasureLevel, rng);
        if (goldHeapItemId > 0 && goldAmount > 0)
        {
            appendRecord(chest, static_cast<int32_t>(goldHeapItemId), goldAmount);
        }
    }

    if (!source.randomItemPool.empty())
    {
        // Explicit map-local equipment rewards bypass the merged tier pool. Store ordinary positive
        // native item records, chosen without replacement from the same persistent session seed.
        std::vector<uint32_t> pool = source.randomItemPool;
        std::shuffle(pool.begin(), pool.end(), rng);
        for (size_t index = 0; index < source.randomItemCount; ++index)
        {
            appendRecord(chest, int32_t(pool.at(index)));
        }
    }
    else if (!source.goldOnly && (source.random || source.aiDrop) && source.randomTreasureLevel > 0)
    {
        appendRecord(chest, -std::clamp(source.randomTreasureLevel, 1, 7));
    }
    return chest;
}
}
