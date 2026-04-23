#include "game/gameplay/TreasureRuntime.h"

#include "game/tables/ItemTable.h"

#include <algorithm>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr int RandomTreasureMinLevel = 1;
constexpr int RandomTreasureMaxLevel = 7;
constexpr int SpawnableItemTreasureLevels = 6;
constexpr uint32_t GoldHeapSmallItemId = 187;
constexpr uint32_t GoldHeapLargeItemId = 189;
constexpr uint32_t TreasureSpawnSeedSalt = 0x54524541u;

uint32_t makeTreasureSpawnSeed(uint32_t sessionSeed, int mapId, uint32_t spawnIndex)
{
    return sessionSeed
        ^ uint32_t(mapId) * 1315423911u
        ^ (spawnIndex + 1u) * 2654435761u
        ^ (TreasureSpawnSeedSalt + 1u) * 2246822519u;
}

int normalizedMapTreasureLevel(int mapTreasureLevel)
{
    return std::clamp(mapTreasureLevel + 1, RandomTreasureMinLevel, RandomTreasureMaxLevel);
}

int generateGoldAmount(int treasureLevel, std::mt19937 &rng)
{
    switch (treasureLevel)
    {
        case 1: return std::uniform_int_distribution<int>(50, 100)(rng);
        case 2: return std::uniform_int_distribution<int>(100, 200)(rng);
        case 3: return std::uniform_int_distribution<int>(200, 500)(rng);
        case 4: return std::uniform_int_distribution<int>(500, 1000)(rng);
        case 5: return std::uniform_int_distribution<int>(1000, 2000)(rng);
        case 6: return std::uniform_int_distribution<int>(2000, 5000)(rng);
        default: return 0;
    }
}

std::pair<int, int> remapTreasureLevelRange(int itemTreasureLevel, int mapTreasureLevel)
{
    static constexpr int Mapping[7][7][2] = {
        {{1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}},
        {{1, 1}, {1, 2}, {2, 2}, {2, 2}, {2, 2}, {2, 2}, {2, 2}},
        {{1, 2}, {2, 2}, {2, 3}, {3, 3}, {3, 3}, {3, 3}, {3, 3}},
        {{2, 2}, {2, 2}, {3, 3}, {3, 4}, {4, 4}, {4, 4}, {4, 4}},
        {{2, 2}, {2, 2}, {3, 4}, {4, 4}, {4, 5}, {5, 5}, {5, 5}},
        {{2, 2}, {2, 2}, {4, 4}, {4, 5}, {5, 5}, {5, 6}, {6, 6}},
        {{2, 2}, {2, 2}, {7, 7}, {7, 7}, {7, 7}, {7, 7}, {7, 7}}
    };

    const int clampedItemLevel = std::clamp(itemTreasureLevel, RandomTreasureMinLevel, RandomTreasureMaxLevel);
    const int clampedMapLevel = std::clamp(mapTreasureLevel, RandomTreasureMinLevel, RandomTreasureMaxLevel);
    const int minimumLevel = Mapping[clampedItemLevel - 1][clampedMapLevel - 1][0];
    const int maximumLevel = Mapping[clampedItemLevel - 1][clampedMapLevel - 1][1];
    return {minimumLevel, maximumLevel};
}

int sampleRemappedTreasureLevel(int itemTreasureLevel, int mapTreasureLevel, std::mt19937 &rng)
{
    const std::pair<int, int> range = remapTreasureLevelRange(itemTreasureLevel, mapTreasureLevel);
    return std::uniform_int_distribution<int>(range.first, range.second)(rng);
}
}

std::optional<GameplayTreasureSpawnResult> generateTreasureSpawnItem(
    int spawnTreasureLevel,
    int mapTreasureLevel,
    uint32_t sessionSeed,
    int mapId,
    uint32_t spawnIndex,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    Party *pParty,
    const std::function<bool(const ItemDefinition &)> &filter)
{
    const int treasureLevel = std::clamp(spawnTreasureLevel, RandomTreasureMinLevel, RandomTreasureMaxLevel);
    std::mt19937 rng(makeTreasureSpawnSeed(sessionSeed, mapId, spawnIndex));
    const int resolvedTreasureLevel =
        sampleRemappedTreasureLevel(treasureLevel, normalizedMapTreasureLevel(mapTreasureLevel), rng);

    GameplayTreasureSpawnResult result = {};

    if (resolvedTreasureLevel != RandomTreasureMaxLevel)
    {
        const int roll = std::uniform_int_distribution<int>(0, 99)(rng);

        if (roll < 20)
        {
            return std::nullopt;
        }

        if (roll < 60)
        {
            result.goldAmount = uint32_t(std::max(0, generateGoldAmount(treasureLevel, rng)));
            const uint32_t goldHeapItemId =
                result.goldAmount <= 200 ? GoldHeapSmallItemId : GoldHeapLargeItemId;
            result.item = ItemGenerator::makeInventoryItem(goldHeapItemId, itemTable, ItemGenerationMode::ChestLoot);
            result.isGold = result.goldAmount > 0;
            return result;
        }

        ItemGenerationRequest request = {};
        request.treasureLevel = std::min(resolvedTreasureLevel, SpawnableItemTreasureLevels);
        request.mode = ItemGenerationMode::ChestLoot;
        const std::optional<InventoryItem> generatedItem =
            ItemGenerator::generateRandomInventoryItem(
                itemTable,
                standardItemEnchantTable,
                specialItemEnchantTable,
                request,
                pParty,
                rng,
                filter);

        if (!generatedItem)
        {
            return std::nullopt;
        }

        result.item = *generatedItem;
        return result;
    }

    ItemGenerationRequest request = {};
    request.treasureLevel = SpawnableItemTreasureLevels;
    request.mode = ItemGenerationMode::ChestLoot;
    request.allowRareItems = true;
    request.rareItemsOnly = true;
    const std::optional<InventoryItem> generatedItem =
        ItemGenerator::generateRandomInventoryItem(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            request,
            pParty,
            rng,
            filter);

    if (!generatedItem)
    {
        return std::nullopt;
    }

    result.item = *generatedItem;
    return result;
}
}
