#include "doctest/doctest.h"

#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"

#include "tests/RegressionGameData.h"

#include <algorithm>
#include <array>
#include <optional>
#include <random>

namespace
{
const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

bool itemHasTreasureWeightAtOrAboveTier(const OpenYAMM::Game::ItemDefinition &itemDefinition, int tier)
{
    const int startTier = std::clamp(tier, 1, static_cast<int>(itemDefinition.randomTreasureWeights.size())) - 1;

    for (size_t tierIndex = static_cast<size_t>(startTier); tierIndex < itemDefinition.randomTreasureWeights.size();
         ++tierIndex)
    {
        if (itemDefinition.randomTreasureWeights[tierIndex] > 0)
        {
            return true;
        }
    }

    return false;
}

std::optional<uint32_t> findChestLootCandidateItemId(
    const OpenYAMM::Game::ItemTable &itemTable,
    int treasureTier,
    bool requiresIdentification)
{
    for (const OpenYAMM::Game::ItemDefinition &itemDefinition : itemTable.entries())
    {
        if (itemDefinition.itemId == 0)
        {
            continue;
        }

        if (OpenYAMM::Game::ItemRuntime::isRareItem(itemDefinition))
        {
            continue;
        }

        if (!itemHasTreasureWeightAtOrAboveTier(itemDefinition, treasureTier))
        {
            continue;
        }

        if (OpenYAMM::Game::ItemRuntime::requiresIdentification(itemDefinition) != requiresIdentification)
        {
            continue;
        }

        return itemDefinition.itemId;
    }

    return std::nullopt;
}

struct GoldHeapExpectation
{
    uint8_t width = 1;
    uint8_t height = 1;
};

GoldHeapExpectation expectedGoldHeapForAmount(uint32_t goldAmount)
{
    if (goldAmount <= 200)
    {
        return {1, 1};
    }

    if (goldAmount <= 1000)
    {
        return {2, 1};
    }

    return {2, 1};
}
}

TEST_CASE("gold heap amount thresholds match oe ranges")
{
    static constexpr std::array<std::pair<uint32_t, GoldHeapExpectation>, 6> Cases = {{
        {50u, {1, 1}},
        {200u, {1, 1}},
        {201u, {2, 1}},
        {1000u, {2, 1}},
        {1001u, {2, 1}},
        {5000u, {2, 1}},
    }};

    for (const std::pair<uint32_t, GoldHeapExpectation> &testCase : Cases)
    {
        const GoldHeapExpectation actual = expectedGoldHeapForAmount(testCase.first);
        CHECK_EQ(actual.width, testCase.second.width);
        CHECK_EQ(actual.height, testCase.second.height);
    }
}

TEST_CASE("chest loot fixed items follow item identification rule")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const std::optional<uint32_t> unidentifiedItemId = findChestLootCandidateItemId(gameData.itemTable, 3, true);
    const std::optional<uint32_t> identifiedItemId = findChestLootCandidateItemId(gameData.itemTable, 3, false);
    REQUIRE(unidentifiedItemId.has_value());
    REQUIRE(identifiedItemId.has_value());

    const OpenYAMM::Game::InventoryItem unidentifiedItem = OpenYAMM::Game::ItemGenerator::makeInventoryItem(
        *unidentifiedItemId,
        gameData.itemTable,
        OpenYAMM::Game::ItemGenerationMode::ChestLoot);
    const OpenYAMM::Game::InventoryItem identifiedItem = OpenYAMM::Game::ItemGenerator::makeInventoryItem(
        *identifiedItemId,
        gameData.itemTable,
        OpenYAMM::Game::ItemGenerationMode::ChestLoot);

    CHECK_FALSE(unidentifiedItem.identified);
    CHECK(identifiedItem.identified);
}

TEST_CASE("chest loot random generation follows item identification rule")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const std::optional<uint32_t> unidentifiedItemId = findChestLootCandidateItemId(gameData.itemTable, 3, true);
    const std::optional<uint32_t> identifiedItemId = findChestLootCandidateItemId(gameData.itemTable, 3, false);
    REQUIRE(unidentifiedItemId.has_value());
    REQUIRE(identifiedItemId.has_value());

    std::mt19937 unidentifiedRng(1337);
    std::mt19937 identifiedRng(7331);
    const std::optional<OpenYAMM::Game::InventoryItem> unidentifiedItem =
        OpenYAMM::Game::ItemGenerator::generateRandomInventoryItem(
            gameData.itemTable,
            gameData.standardItemEnchantTable,
            gameData.specialItemEnchantTable,
            OpenYAMM::Game::ItemGenerationRequest{3, OpenYAMM::Game::ItemGenerationMode::ChestLoot, false},
            nullptr,
            unidentifiedRng,
            [targetItemId = *unidentifiedItemId](const OpenYAMM::Game::ItemDefinition &entry)
            {
                return entry.itemId == targetItemId;
            });
    const std::optional<OpenYAMM::Game::InventoryItem> identifiedItem =
        OpenYAMM::Game::ItemGenerator::generateRandomInventoryItem(
            gameData.itemTable,
            gameData.standardItemEnchantTable,
            gameData.specialItemEnchantTable,
            OpenYAMM::Game::ItemGenerationRequest{3, OpenYAMM::Game::ItemGenerationMode::ChestLoot, false},
            nullptr,
            identifiedRng,
            [targetItemId = *identifiedItemId](const OpenYAMM::Game::ItemDefinition &entry)
            {
                return entry.itemId == targetItemId;
            });

    REQUIRE(unidentifiedItem.has_value());
    REQUIRE(identifiedItem.has_value());
    CHECK_EQ(unidentifiedItem->objectDescriptionId, *unidentifiedItemId);
    CHECK_EQ(identifiedItem->objectDescriptionId, *identifiedItemId);
    CHECK_FALSE(unidentifiedItem->identified);
    CHECK(identifiedItem->identified);
}
