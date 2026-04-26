#include "doctest/doctest.h"

#include "game/gameplay/ChestRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/maps/MapDeltaData.h"
#include "game/tables/ChestTable.h"

#include "tests/RegressionGameData.h"

#include <algorithm>
#include <array>
#include <cstring>
#include <optional>
#include <random>
#include <string>

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

std::optional<uint32_t> findSmallChestLootCandidateItemId(
    const OpenYAMM::Game::ItemTable &itemTable,
    uint32_t excludedItemId = 0)
{
    for (const OpenYAMM::Game::ItemDefinition &itemDefinition : itemTable.entries())
    {
        if (itemDefinition.itemId != 0
            && itemDefinition.itemId != excludedItemId
            && itemDefinition.inventoryWidth <= 1
            && itemDefinition.inventoryHeight <= 1
            && !OpenYAMM::Game::ItemRuntime::isRareItem(itemDefinition))
        {
            return itemDefinition.itemId;
        }
    }

    return std::nullopt;
}

const OpenYAMM::Game::GameplayChestItemState *firstChestItem(const OpenYAMM::Game::GameplayChestViewState &view)
{
    if (!view.items.empty())
    {
        return &view.items.front();
    }

    if (!view.hiddenItems.empty())
    {
        return &view.hiddenItems.front();
    }

    return nullptr;
}

OpenYAMM::Game::Party makeChestTestParty(const OpenYAMM::Tests::RegressionGameData &gameData)
{
    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);
    return party;
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

OpenYAMM::Game::ChestTable makeChestTable(uint8_t gridWidth, uint8_t gridHeight)
{
    OpenYAMM::Game::ChestTable chestTable;
    REQUIRE(chestTable.loadRows({
        {
            "0",
            "Test",
            "1",
            "1",
            "1",
            "chest01",
            "0",
            "0",
            std::to_string(gridWidth),
            std::to_string(gridHeight),
        },
    }));
    return chestTable;
}

void writeRawChestItemId(OpenYAMM::Game::MapDeltaChest &chest, size_t recordIndex, int32_t rawItemId)
{
    constexpr size_t RecordSize = 36;

    if (chest.rawItems.size() < (recordIndex + 1) * RecordSize)
    {
        chest.rawItems.resize((recordIndex + 1) * RecordSize, 0);
    }

    std::memcpy(chest.rawItems.data() + recordIndex * RecordSize, &rawItemId, sizeof(rawItemId));
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

TEST_CASE("chest materialization keeps unplaced guaranteed items hidden instead of dropping them")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const std::optional<uint32_t> firstItemId = findSmallChestLootCandidateItemId(gameData.itemTable);
    REQUIRE(firstItemId.has_value());
    const std::optional<uint32_t> secondItemId = findSmallChestLootCandidateItemId(gameData.itemTable, *firstItemId);
    REQUIRE(secondItemId.has_value());
    OpenYAMM::Game::Party party = makeChestTestParty(gameData);
    OpenYAMM::Game::ChestTable chestTable = makeChestTable(1, 1);
    OpenYAMM::Game::MapDeltaChest chest = {};
    chest.chestTypeId = 0;
    chest.inventoryMatrix.assign(140, 0);
    chest.inventoryMatrix[0] = 1;
    writeRawChestItemId(chest, 0, static_cast<int32_t>(*firstItemId));
    writeRawChestItemId(chest, 1, static_cast<int32_t>(*secondItemId));

    OpenYAMM::Game::GameplayChestViewState view =
        OpenYAMM::Game::buildMaterializedChestView(
            0,
            chest,
            6,
            0,
            1234,
            &chestTable,
            &gameData.itemTable,
            &party);

    REQUIRE_EQ(view.items.size(), 1u);
    REQUIRE_EQ(view.hiddenItems.size(), 1u);
    CHECK_EQ(view.items.front().itemId, *firstItemId);
    CHECK_EQ(view.hiddenItems.front().itemId, *secondItemId);

    OpenYAMM::Game::GameplayChestItemState removedItem = {};
    REQUIRE(OpenYAMM::Game::takeChestItem(view, 0, removedItem));
    REQUIRE_EQ(view.items.size(), 1u);
    CHECK(view.hiddenItems.empty());
    CHECK_EQ(view.items.front().itemId, *secondItemId);
}

TEST_CASE("chest level seven random placeholder generates a guaranteed rare item")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    std::mt19937 directRng(4321);
    const std::optional<OpenYAMM::Game::InventoryItem> directRare =
        OpenYAMM::Game::ItemGenerator::generateRandomInventoryItem(
            gameData.itemTable,
            gameData.standardItemEnchantTable,
            gameData.specialItemEnchantTable,
            OpenYAMM::Game::ItemGenerationRequest{
                6,
                OpenYAMM::Game::ItemGenerationMode::ChestLoot,
                true,
                true},
            nullptr,
            directRng);
    REQUIRE(directRare.has_value());

    OpenYAMM::Game::Party party = makeChestTestParty(gameData);
    OpenYAMM::Game::ChestTable chestTable = makeChestTable(9, 9);
    OpenYAMM::Game::MapDeltaChest chest = {};
    chest.chestTypeId = 0;
    chest.inventoryMatrix.assign(140, 0);
    chest.inventoryMatrix[0] = 1;
    writeRawChestItemId(chest, 0, -7);

    OpenYAMM::Game::GameplayChestViewState view =
        OpenYAMM::Game::buildMaterializedChestView(
            0,
            chest,
            6,
            0,
            4321,
            &chestTable,
            &gameData.itemTable,
            &party);

    const OpenYAMM::Game::GameplayChestItemState *pGeneratedItem = firstChestItem(view);
    REQUIRE(pGeneratedItem != nullptr);
    const OpenYAMM::Game::ItemDefinition *pItemDefinition = gameData.itemTable.get(pGeneratedItem->itemId);
    REQUIRE(pItemDefinition != nullptr);
    CHECK(OpenYAMM::Game::ItemRuntime::isRareItem(*pItemDefinition));
}
