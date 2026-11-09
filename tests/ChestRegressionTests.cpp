#include "doctest/doctest.h"

#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/gameplay/ChestRuntime.h"
#include "game/gameplay/TreasureRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/tables/ChestTable.h"

#include "tests/RegressionGameData.h"

#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <optional>
#include <random>
#include <set>
#include <sstream>
#include <string>
#include <vector>

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

const OpenYAMM::Game::GameplayChestItemState *firstGoldChestItem(
    const OpenYAMM::Game::GameplayChestViewState &view)
{
    const auto isGold =
        [](const OpenYAMM::Game::GameplayChestItemState &item)
        {
            return item.isGold;
        };

    const auto itemIt = std::find_if(view.items.begin(), view.items.end(), isGold);

    if (itemIt != view.items.end())
    {
        return &*itemIt;
    }

    const auto hiddenItemIt = std::find_if(view.hiddenItems.begin(), view.hiddenItems.end(), isGold);

    if (hiddenItemIt != view.hiddenItems.end())
    {
        return &*hiddenItemIt;
    }

    return nullptr;
}

bool chestViewContainsItemId(const OpenYAMM::Game::GameplayChestViewState &view, uint32_t itemId)
{
    const auto matchesItem =
        [itemId](const OpenYAMM::Game::GameplayChestItemState &item)
        {
            return item.itemId == itemId || item.item.objectDescriptionId == itemId;
        };

    return std::any_of(view.items.begin(), view.items.end(), matchesItem)
        || std::any_of(view.hiddenItems.begin(), view.hiddenItems.end(), matchesItem);
}

bool chestViewContainsRareItem(
    const OpenYAMM::Game::GameplayChestViewState &view,
    const OpenYAMM::Game::ItemTable &itemTable)
{
    const auto isRareItem =
        [&itemTable](const OpenYAMM::Game::GameplayChestItemState &item)
        {
            const uint32_t itemId = item.item.objectDescriptionId != 0
                ? item.item.objectDescriptionId
                : item.itemId;
            const OpenYAMM::Game::ItemDefinition *pItemDefinition = itemTable.get(itemId);
            return pItemDefinition != nullptr && OpenYAMM::Game::ItemRuntime::isRareItem(*pItemDefinition);
        };

    return std::any_of(view.items.begin(), view.items.end(), isRareItem)
        || std::any_of(view.hiddenItems.begin(), view.hiddenItems.end(), isRareItem);
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

void writeRawChestItemInt32(
    OpenYAMM::Game::MapDeltaChest &chest,
    size_t recordIndex,
    size_t fieldOffset,
    int32_t value)
{
    constexpr size_t RecordSize = 36;

    REQUIRE_LE(fieldOffset + sizeof(value), RecordSize);

    if (chest.rawItems.size() < (recordIndex + 1) * RecordSize)
    {
        chest.rawItems.resize((recordIndex + 1) * RecordSize, 0);
    }

    std::memcpy(chest.rawItems.data() + recordIndex * RecordSize + fieldOffset, &value, sizeof(value));
}

OpenYAMM::Game::OutdoorSceneData loadOutdoorScene(const char *pRelativeScenePath)
{
    const std::filesystem::path scenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / pRelativeScenePath;
    std::ifstream sceneFile(scenePath);
    REQUIRE(sceneFile.good());

    std::ostringstream sceneText;
    sceneText << sceneFile.rdbuf();

    std::string errorMessage;
    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<OpenYAMM::Game::OutdoorSceneData> sceneData =
        sceneLoader.loadFromText(sceneText.str(), errorMessage);
    REQUIRE_MESSAGE(sceneData.has_value(), errorMessage.c_str());
    return *sceneData;
}

OpenYAMM::Game::OutdoorSceneData loadOut01Scene()
{
    return loadOutdoorScene("assets_dev/worlds/mm8/maps/out01.scene.yml");
}

int chestItemValue(
    const OpenYAMM::Game::GameplayChestItemState &item,
    const OpenYAMM::Tests::RegressionGameData &gameData)
{
    if (item.isGold)
    {
        return static_cast<int>(item.goldAmount);
    }

    const uint32_t itemId = item.item.objectDescriptionId != 0 ? item.item.objectDescriptionId : item.itemId;
    const OpenYAMM::Game::ItemDefinition *pItemDefinition = gameData.itemTable.get(itemId);

    if (pItemDefinition == nullptr)
    {
        return 0;
    }

    return OpenYAMM::Game::ItemEnchantRuntime::itemValue(
        item.item,
        *pItemDefinition,
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable) * std::max(1u, item.quantity);
}

OpenYAMM::Game::GameplayChestViewState materializeOut01Chest(
    const OpenYAMM::Game::OutdoorSceneData &sceneData,
    const OpenYAMM::Tests::RegressionGameData &gameData,
    OpenYAMM::Game::Party &party,
    uint32_t chestId)
{
    REQUIRE_LT(chestId, sceneData.initialState.chests.size());

    OpenYAMM::Game::ChestTable chestTable = makeChestTable(9, 9);
    return OpenYAMM::Game::buildMaterializedChestView(
        chestId,
        sceneData.initialState.chests[chestId],
        0,
        1,
        12345,
        &chestTable,
        &gameData.itemTable,
        &party,
        "mm8");
}

OpenYAMM::Game::Party makeTrapTestParty(const OpenYAMM::Game::Character &member)
{
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(member);

    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    return party;
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

TEST_CASE("fixed chest gold with authored amount materializes as lootable gold")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeChestTestParty(gameData);
    OpenYAMM::Game::ChestTable chestTable = makeChestTable(9, 9);
    OpenYAMM::Game::MapDeltaChest chest = {};
    chest.chestTypeId = 0;
    chest.inventoryMatrix.assign(140, 0);

    constexpr uint32_t LargeGoldItemId = 189;
    constexpr uint32_t GoldAmount = 1234;
    writeRawChestItemId(chest, 0, static_cast<int32_t>(LargeGoldItemId));
    writeRawChestItemInt32(chest, 0, 0x0c, static_cast<int32_t>(GoldAmount));

    const OpenYAMM::Game::GameplayChestViewState view =
        OpenYAMM::Game::buildMaterializedChestView(
            0,
            chest,
            3,
            0,
            1234,
            &chestTable,
            &gameData.itemTable,
            &party,
            "mm8");

    const OpenYAMM::Game::GameplayChestItemState *pGoldItem = firstGoldChestItem(view);
    REQUIRE(pGoldItem != nullptr);
    CHECK_EQ(pGoldItem->itemId, LargeGoldItemId);
    CHECK_EQ(pGoldItem->goldAmount, GoldAmount);
    CHECK_EQ(pGoldItem->goldRollCount, 1u);
}

TEST_CASE("fixed chest gold with zero authored amount receives deterministic legacy fallback")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeChestTestParty(gameData);
    OpenYAMM::Game::ChestTable chestTable = makeChestTable(9, 9);
    OpenYAMM::Game::MapDeltaChest chest = {};
    chest.chestTypeId = 0;
    chest.inventoryMatrix.assign(140, 0);

    constexpr uint32_t LargeGoldItemId = 189;
    writeRawChestItemId(chest, 0, static_cast<int32_t>(LargeGoldItemId));

    const OpenYAMM::Game::GameplayChestViewState firstView =
        OpenYAMM::Game::buildMaterializedChestView(
            0,
            chest,
            6,
            0,
            1234,
            &chestTable,
            &gameData.itemTable,
            &party,
            "mm8");
    const OpenYAMM::Game::GameplayChestViewState secondView =
        OpenYAMM::Game::buildMaterializedChestView(
            0,
            chest,
            6,
            0,
            1234,
            &chestTable,
            &gameData.itemTable,
            &party,
            "mm8");

    const OpenYAMM::Game::GameplayChestItemState *pFirstGoldItem = firstGoldChestItem(firstView);
    const OpenYAMM::Game::GameplayChestItemState *pSecondGoldItem = firstGoldChestItem(secondView);
    REQUIRE(pFirstGoldItem != nullptr);
    REQUIRE(pSecondGoldItem != nullptr);
    CHECK_EQ(pFirstGoldItem->itemId, LargeGoldItemId);
    CHECK_GE(pFirstGoldItem->goldAmount, 2000u);
    CHECK_LE(pFirstGoldItem->goldAmount, 5000u);
    CHECK_EQ(pFirstGoldItem->goldAmount, pSecondGoldItem->goldAmount);
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
            &party,
            "mm8");

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

TEST_CASE("chest materialization discards random overflow instead of hiding it")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeChestTestParty(gameData);
    OpenYAMM::Game::ChestTable chestTable = makeChestTable(1, 1);
    OpenYAMM::Game::MapDeltaChest chest = {};
    chest.chestTypeId = 0;
    chest.inventoryMatrix.assign(140, 0);

    for (size_t recordIndex = 0; recordIndex < 20; ++recordIndex)
    {
        writeRawChestItemId(chest, recordIndex, -6);
    }

    OpenYAMM::Game::GameplayChestViewState view =
        OpenYAMM::Game::buildMaterializedChestView(
            0,
            chest,
            6,
            0,
            1234,
            &chestTable,
            &gameData.itemTable,
            &party,
            "mm8");

    REQUIRE_EQ(view.items.size(), 1u);
    CHECK(view.hiddenItems.empty());

    OpenYAMM::Game::GameplayChestItemState removedItem = {};
    REQUIRE(OpenYAMM::Game::takeChestItem(view, 0, removedItem));
    CHECK(view.items.empty());
    CHECK(view.hiddenItems.empty());
}

TEST_CASE("chest materialization places random loot in descending value order")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeChestTestParty(gameData);
    OpenYAMM::Game::ChestTable chestTable = makeChestTable(9, 9);
    OpenYAMM::Game::MapDeltaChest chest = {};
    chest.chestTypeId = 0;
    chest.inventoryMatrix.assign(140, 0);

    for (size_t recordIndex = 0; recordIndex < 20; ++recordIndex)
    {
        writeRawChestItemId(chest, recordIndex, -6);
    }

    OpenYAMM::Game::GameplayChestViewState view =
        OpenYAMM::Game::buildMaterializedChestView(
            0,
            chest,
            6,
            0,
            1234,
            &chestTable,
            &gameData.itemTable,
            &party,
            "mm8");

    REQUIRE_GT(view.items.size(), 1u);
    CHECK(view.hiddenItems.empty());

    int previousValue = chestItemValue(view.items.front(), gameData);

    for (size_t itemIndex = 1; itemIndex < view.items.size(); ++itemIndex)
    {
        const int currentValue = chestItemValue(view.items[itemIndex], gameData);
        CHECK_GE(previousValue, currentValue);
        previousValue = currentValue;
    }
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
            // Artifacts roll only in their own world (World:<id>); the regression data is MM8's.
            OpenYAMM::Game::ItemGenerationRequest{
                6,
                OpenYAMM::Game::ItemGenerationMode::ChestLoot,
                true,
                true,
                "mm8"},
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
            &party,
            "mm8");

    const OpenYAMM::Game::GameplayChestItemState *pGeneratedItem = firstChestItem(view);
    REQUIRE(pGeneratedItem != nullptr);
    const OpenYAMM::Game::ItemDefinition *pItemDefinition = gameData.itemTable.get(pGeneratedItem->itemId);
    REQUIRE(pItemDefinition != nullptr);
    CHECK(OpenYAMM::Game::ItemRuntime::isRareItem(*pItemDefinition));
}

TEST_CASE("a level seven slot's artifact takes a random cell, not the slot's top-left anchor")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = makeChestTestParty(gameData);
    OpenYAMM::Game::ChestTable chestTable = makeChestTable(9, 9);
    std::set<std::pair<int, int>> cells;

    for (uint32_t chestId = 0; chestId < 12; ++chestId)
    {
        OpenYAMM::Game::MapDeltaChest chest = {};
        chest.inventoryMatrix.assign(140, 0);
        chest.inventoryMatrix[0] = 1;
        writeRawChestItemId(chest, 0, -7);
        const OpenYAMM::Game::GameplayChestViewState view =
            OpenYAMM::Game::buildMaterializedChestView(
                chestId, chest, 6, 0, 4321, &chestTable, &gameData.itemTable, &party, "mm8");
        REQUIRE_EQ(view.items.size(), 1u);
        cells.insert({view.items.front().gridX, view.items.front().gridY});
    }

    CHECK_GT(cells.size(), 3u);
}

TEST_CASE("a chest-artifacts-only world rolls no artifact at level six and refills an exhausted level-seven slot")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::ItemTable itemTable = gameData.itemTable;
    itemTable.setChestArtifactsOnlyWorlds({"mm8"});
    int rareAtLevelSix = 0;

    for (uint32_t seed = 1; seed <= 400; ++seed)
    {
        std::mt19937 rng(seed);
        const std::optional<OpenYAMM::Game::InventoryItem> item =
            OpenYAMM::Game::ItemGenerator::generateRandomInventoryItem(
                itemTable,
                gameData.standardItemEnchantTable,
                gameData.specialItemEnchantTable,
                OpenYAMM::Game::ItemGenerationRequest{
                    .treasureLevel = 6,
                    .mode = OpenYAMM::Game::ItemGenerationMode::ChestLoot,
                    .worldId = "mm8",
                },
                nullptr,
                rng);
        const OpenYAMM::Game::ItemDefinition *pDefinition =
            item.has_value() ? itemTable.get(item->objectDescriptionId) : nullptr;
        rareAtLevelSix += pDefinition != nullptr && OpenYAMM::Game::ItemRuntime::isArtifact(*pDefinition) ? 1 : 0;
    }

    CHECK_EQ(rareAtLevelSix, 0);

    OpenYAMM::Game::Party party = makeChestTestParty(gameData);

    for (const OpenYAMM::Game::ItemDefinition &entry : itemTable.entries())
    {
        if (OpenYAMM::Game::ItemRuntime::isUniquelyGeneratedRareItem(entry))
        {
            party.markArtifactItemFound(entry.itemId);
        }
    }

    OpenYAMM::Game::ChestTable chestTable = makeChestTable(9, 9);
    OpenYAMM::Game::MapDeltaChest chest = {};
    chest.inventoryMatrix.assign(140, 0);
    chest.inventoryMatrix[0] = 1;
    writeRawChestItemId(chest, 0, -7);
    const OpenYAMM::Game::GameplayChestViewState view =
        OpenYAMM::Game::buildMaterializedChestView(0, chest, 6, 0, 4321, &chestTable, &itemTable, &party, "mm8");
    bool hasGold = false;
    bool hasItem = false;

    for (const OpenYAMM::Game::GameplayChestItemState &item : view.items)
    {
        hasGold = hasGold || item.isGold;
        const OpenYAMM::Game::ItemDefinition *pDefinition = item.isGold ? nullptr : itemTable.get(item.itemId);
        if (pDefinition != nullptr)
        {
            hasItem = true;
            CHECK_FALSE(OpenYAMM::Game::ItemRuntime::isArtifact(*pDefinition));
        }
    }

    CHECK(hasGold);
    CHECK(hasItem);
}

TEST_CASE("Ravenshore hidden tree chest retains its guaranteed artifact")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::OutdoorSceneData sceneData =
        loadOutdoorScene("assets_dev/worlds/mm8/maps/out02.scene.yml");
    REQUIRE_GT(sceneData.initialState.chests.size(), 11u);

    const OpenYAMM::Game::MapDeltaChest &treeChest = sceneData.initialState.chests[11];
    REQUIRE_GE(treeChest.rawItems.size(), sizeof(int32_t));

    int32_t firstRawItemId = 0;
    std::memcpy(&firstRawItemId, treeChest.rawItems.data(), sizeof(firstRawItemId));
    REQUIRE_EQ(firstRawItemId, -7);

    OpenYAMM::Game::Party party = makeChestTestParty(gameData);
    OpenYAMM::Game::ChestTable chestTable = makeChestTable(9, 9);
    const OpenYAMM::Game::GameplayChestViewState view =
        OpenYAMM::Game::buildMaterializedChestView(
            11,
            treeChest,
            1,
            2,
            12345,
            &chestTable,
            &gameData.itemTable,
            &party,
            "mm8");

    CHECK(chestViewContainsRareItem(view, gameData.itemTable));
}

TEST_CASE("trapped chest opens when active character disarms it")
{
    OpenYAMM::Game::Character member = {};
    member.name = "Disarmer";
    member.maxHealth = 50;
    member.health = 50;
    member.skills["DisarmTraps"] = OpenYAMM::Game::CharacterSkill{
        .name = "DisarmTraps",
        .level = 2,
        .mastery = OpenYAMM::Game::SkillMastery::Normal,
    };
    OpenYAMM::Game::Party party = makeTrapTestParty(member);

    OpenYAMM::Game::MapStatsEntry map = {};
    map.disarmDifficulty = 1;
    map.trapDamageD20DiceCount = 0;

    OpenYAMM::Game::ChestTrapOpenContext context = {};
    context.seed = 1234;
    const OpenYAMM::Game::ChestTrapOpenResult result = OpenYAMM::Game::resolveChestTrapOpen(
        party,
        map,
        static_cast<uint16_t>(OpenYAMM::Game::EvtChestFlag::Trapped),
        context,
        nullptr,
        nullptr,
        nullptr);

    CHECK(result.trapWasPresent);
    CHECK(result.trapDisarmed);
    CHECK_FALSE(result.trapDischarged);
    CHECK(result.shouldOpenChest);
    CHECK(result.memberResults.empty());
}

TEST_CASE("trapped chest opens when another party member disarms it")
{
    OpenYAMM::Game::Character activeMember = {};
    activeMember.name = "Opener";
    activeMember.maxHealth = 50;
    activeMember.health = 50;

    OpenYAMM::Game::Character disarmer = {};
    disarmer.name = "Disarmer";
    disarmer.maxHealth = 50;
    disarmer.health = 50;
    disarmer.skills["DisarmTraps"] = OpenYAMM::Game::CharacterSkill{
        .name = "DisarmTraps",
        .level = 1,
        .mastery = OpenYAMM::Game::SkillMastery::Grandmaster,
    };

    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(activeMember);
    seed.members.push_back(disarmer);

    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    REQUIRE(party.setActiveMemberIndex(0));

    OpenYAMM::Game::MapStatsEntry map = {};
    map.disarmDifficulty = 20;
    map.trapDamageD20DiceCount = 0;

    OpenYAMM::Game::ChestTrapOpenContext context = {};
    context.seed = 1234;
    const OpenYAMM::Game::ChestTrapOpenResult result = OpenYAMM::Game::resolveChestTrapOpen(
        party,
        map,
        static_cast<uint16_t>(OpenYAMM::Game::EvtChestFlag::Trapped),
        context,
        nullptr,
        nullptr,
        nullptr);

    CHECK(result.trapWasPresent);
    CHECK(result.trapDisarmed);
    CHECK_FALSE(result.trapDischarged);
    CHECK(result.shouldOpenChest);
}

TEST_CASE("failed trapped chest opening discharges trap and damages nearby party")
{
    OpenYAMM::Game::Character member = {};
    member.name = "Victim";
    member.maxHealth = 50;
    member.health = 50;

    OpenYAMM::Game::Character unconsciousMember = {};
    unconsciousMember.name = "Unconscious";
    unconsciousMember.maxHealth = 50;
    unconsciousMember.health = -1;
    unconsciousMember.endurance = 3;
    unconsciousMember.conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Unconscious));

    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(member);
    seed.members.push_back(unconsciousMember);

    OpenYAMM::Game::Party party = {};
    party.seed(seed);

    OpenYAMM::Game::MapStatsEntry map = {};
    map.disarmDifficulty = 5;
    map.trapDamageD20DiceCount = 0;

    OpenYAMM::Game::ChestTrapOpenContext context = {};
    context.trapX = 10.0f;
    context.trapY = 20.0f;
    context.trapZ = 30.0f;
    context.partyX = 10.0f;
    context.partyY = 20.0f;
    context.partyZ = 30.0f;
    context.seed = 5678;
    const OpenYAMM::Game::ChestTrapOpenResult result = OpenYAMM::Game::resolveChestTrapOpen(
        party,
        map,
        static_cast<uint16_t>(OpenYAMM::Game::EvtChestFlag::Trapped),
        context,
        nullptr,
        nullptr,
        nullptr);

    CHECK(result.trapWasPresent);
    CHECK_FALSE(result.trapDisarmed);
    CHECK(result.trapDischarged);
    CHECK_FALSE(result.shouldOpenChest);
    CHECK_GE(result.trapObjectId, 811);
    CHECK_LE(result.trapObjectId, 814);
    CHECK_EQ(result.trapDamage, 5);
    REQUIRE_EQ(result.memberResults.size(), 2u);
    CHECK_EQ(result.memberResults[0].memberIndex, 0u);
    CHECK_FALSE(result.memberResults[0].avoided);
    CHECK_EQ(result.memberResults[0].damage, 5);
    CHECK_EQ(result.memberResults[1].memberIndex, 1u);
    CHECK_FALSE(result.memberResults[1].avoided);
    CHECK_EQ(result.memberResults[1].damage, 5);

    OpenYAMM::Game::applyChestTrapOpenResultToParty(party, result);
    REQUIRE_EQ(party.members().size(), 2u);
    CHECK_EQ(party.members()[0].health, 45);
    CHECK_EQ(party.members()[1].health, -5);
    CHECK(party.members()[1].conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead)));
    CHECK_FALSE(party.members()[1].conditions.test(
        static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Unconscious)));
}

TEST_CASE("outdoor Dagger Wound chests retain authored Cure Disease scrolls")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::OutdoorSceneData sceneData = loadOut01Scene();
    REQUIRE_GT(sceneData.initialState.chests.size(), 10u);

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable);

    const uint32_t cureDiseaseScrollId = 373;
    const std::vector<uint32_t> scrollChestIds = {3, 4, 5, 6, 8, 10};

    for (uint32_t chestId : scrollChestIds)
    {
        const OpenYAMM::Game::GameplayChestViewState view =
            materializeOut01Chest(sceneData, gameData, party, chestId);

        INFO("chestId=" << chestId);
        CHECK(chestViewContainsItemId(view, cureDiseaseScrollId));
    }
}

TEST_CASE("outdoor Ravage Roaming pirate treasure fixed gold materializes as lootable gold")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::OutdoorSceneData sceneData =
        loadOutdoorScene("assets_dev/worlds/mm8/maps/out08.scene.yml");
    REQUIRE_GT(sceneData.initialState.chests.size(), 10u);

    OpenYAMM::Game::Party party = makeChestTestParty(gameData);
    OpenYAMM::Game::ChestTable chestTable = makeChestTable(9, 9);

    const OpenYAMM::Game::GameplayChestViewState view =
        OpenYAMM::Game::buildMaterializedChestView(
            10,
            sceneData.initialState.chests[10],
            3,
            8,
            12345,
            &chestTable,
            &gameData.itemTable,
            &party,
            "mm8");

    const OpenYAMM::Game::GameplayChestItemState *pGoldItem = firstGoldChestItem(view);
    REQUIRE(pGoldItem != nullptr);
    CHECK_GT(pGoldItem->goldAmount, 0u);
    CHECK(chestViewContainsItemId(view, 503));
}

TEST_CASE("outdoor Dagger Wound chest events materialize authored Cure Disease scrolls")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    REQUIRE(gameData.out01LocalEventProgram.has_value());
    const OpenYAMM::Game::OutdoorSceneData sceneData = loadOut01Scene();

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable);

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    const uint32_t cureDiseaseScrollId = 373;
    const std::vector<uint16_t> scrollEventIds = {85, 86, 87, 89, 91};

    for (uint16_t eventId : scrollEventIds)
    {
        OpenYAMM::Game::EventRuntimeState eventRuntimeState = {};
        REQUIRE(eventRuntime.executeEventById(
            gameData.out01LocalEventProgram,
            gameData.globalEventProgram,
            eventId,
            eventRuntimeState,
            &party));
        REQUIRE_FALSE(eventRuntimeState.openedChestIds.empty());

        const uint32_t chestId = eventRuntimeState.openedChestIds.back();
        const OpenYAMM::Game::GameplayChestViewState view =
            materializeOut01Chest(sceneData, gameData, party, chestId);

        INFO("eventId=" << eventId);
        INFO("chestId=" << chestId);
        CHECK(chestViewContainsItemId(view, cureDiseaseScrollId));
    }
}

TEST_CASE("chest open requests are one-shot transient event outputs")
{
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    runtimeState.openedChestIds.push_back(7);

    const std::vector<uint32_t> openedChestIds = OpenYAMM::Game::consumeOpenedChestIds(runtimeState);

    REQUIRE_EQ(openedChestIds.size(), 1u);
    CHECK_EQ(openedChestIds.front(), 7u);
    CHECK(runtimeState.openedChestIds.empty());

    runtimeState.openedChestIds.push_back(9);
    OpenYAMM::Game::clearTransientEventRuntimeState(runtimeState);

    CHECK(runtimeState.openedChestIds.empty());
}

TEST_CASE("treasure marker gold follows the marker level, or the item tier in a groundGoldByItemTier world")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::ItemTable itemTable = gameData.itemTable;
    itemTable.setGroundGoldByItemTierWorlds({"mm9"});

    // A level-3 marker on a treasure level 1 map gives T2 items: MM8's gold heaps are level 3's (200-500), MM9's T2's
    // (100-200).
    for (const std::string worldId : {"mm8", "mm9"})
    {
        const uint32_t lowest = worldId == "mm9" ? 100u : 200u;
        const uint32_t highest = worldId == "mm9" ? 200u : 500u;
        int heaps = 0;

        for (uint32_t spawnIndex = 0; spawnIndex < 300; ++spawnIndex)
        {
            const std::optional<OpenYAMM::Game::GameplayTreasureSpawnResult> marker =
                OpenYAMM::Game::generateTreasureSpawnItem(
                    3, 1, 4321, 0, spawnIndex, itemTable, gameData.standardItemEnchantTable,
                    gameData.specialItemEnchantTable, nullptr, worldId, {});

            if (marker && marker->isGold)
            {
                INFO("world=" << worldId << " gold=" << marker->goldAmount);
                CHECK(marker->goldAmount >= lowest);
                CHECK(marker->goldAmount <= highest);
                ++heaps;
            }
        }

        CHECK(heaps > 80);
    }
}

TEST_CASE("treasure markers give nothing, a gold heap or an item, as MM6-MM8, in every world")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    for (const std::string worldId : {"mm8", "mm9"})
    {
        int nothing = 0;
        int gold = 0;
        int items = 0;

        for (uint32_t spawnIndex = 0; spawnIndex < 1000; ++spawnIndex)
        {
            const std::optional<OpenYAMM::Game::GameplayTreasureSpawnResult> marker =
                OpenYAMM::Game::generateTreasureSpawnItem(
                    3, 3, 4321, 0, spawnIndex, gameData.itemTable, gameData.standardItemEnchantTable,
                    gameData.specialItemEnchantTable, nullptr, worldId, {});

            if (!marker)
            {
                ++nothing;
            }
            else if (marker->isGold)
            {
                CHECK_GT(marker->goldAmount, 0u);
                ++gold;
            }
            else
            {
                CHECK_NE(marker->item.objectDescriptionId, 0u);
                ++items;
            }
        }

        // 20% / 40% / 40% over 1000 rolls.
        CHECK(nothing > 140);
        CHECK(nothing < 260);
        CHECK(gold > 340);
        CHECK(gold < 460);
        CHECK(items > 340);
        CHECK(items < 460);
    }
}
