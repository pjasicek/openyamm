#include "engine/AssetFileSystem.h"
#include "game/content/ContentTableComposer.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/tables/ItemTable.h"

#include <doctest/doctest.h>

#include <filesystem>
#include <random>
#include <set>
#include <string>
#include <vector>

using namespace OpenYAMM;
using namespace OpenYAMM::Game;

namespace
{
// An item row: id, picture, name, value, equip stat, skill, mod1, mod2, material; package id in column 17.
std::vector<std::string> itemRow(
    const std::string &id,
    const std::string &name,
    const std::string &equipStat,
    const std::string &material,
    const std::string &packageId,
    const std::string &contentFlags = "")
{
    std::vector<std::string> row(21);
    row[0] = id;
    row[1] = "item" + id;
    row[2] = name;
    row[3] = "100";
    row[4] = equipStat;
    row[5] = equipStat == "Weapon" ? "Sword" : "Misc";
    row[6] = equipStat == "Weapon" ? "2d4" : "0";
    row[7] = "0";
    row[8] = material;
    row[17] = packageId;
    row[20] = contentFlags;
    return row;
}

std::vector<std::string> weightRow(const std::string &id, int level3Weight)
{
    return {id, "item" + id, "0", "0", std::to_string(level3Weight), "0", "0", "0"};
}

// Engine (merged MM6-MM8) items 1-2 and 5-6, MM9 items 3-4. Artifacts carry their world (World:<id>).
const std::vector<std::vector<std::string>> ItemRows = {
    itemRow("1", "Engine Sword", "Weapon", "0", ""),
    itemRow("2", "Engine Potion", "Bottle", "0", ""),
    itemRow("3", "MM9 Sword", "Weapon", "0", "mm9"),
    itemRow("4", "MM9 Artifact", "Weapon", "Artifact", "mm9", "World:mm9"),
    itemRow("5", "MM7 Artifact", "Weapon", "Artifact", "", "World:mm7"),
    itemRow("6", "MM6 Relic", "Weapon", "Relic", "", "World:mm6"),
};

ItemTable loadTable(const std::vector<std::vector<std::string>> &randomRows)
{
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem fs;
    REQUIRE(fs.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1));
    ItemTable table;
    REQUIRE(table.load(fs, ItemRows, randomRows));
    return table;
}
}

TEST_CASE("a world's random_items contribution weights its own items inside its item id range")
{
    const std::vector<std::vector<std::string>> engineRows = {
        {"Random Item Generation By Treasure Level 1 - 6"}, {"Item #", "Pic File", "1", "2", "3", "4", "5", "6"},
        weightRow("1", 5)};
    KeyedTableContributionRows world = {};
    world.packageId = "mm9";
    world.idRange = {.begin = 3, .end = 4};
    world.rows = {{"Item #", "Pic File", "1", "2", "3", "4", "5", "6"}, weightRow("3", 7)};
    std::vector<std::vector<std::string>> composed;
    std::string error;
    REQUIRE_MESSAGE(composeKeyedAppendTableRows(engineRows, {world}, composed, error), error);

    const ItemTable table = loadTable(composed);
    CHECK(table.get(1)->randomTreasureWeights[2] == 5);
    CHECK(table.get(3)->randomTreasureWeights[2] == 7);

    // A world may weight only items in its own range, and only once.
    world.rows = {weightRow("1", 9)};
    CHECK_FALSE(composeKeyedAppendTableRows(engineRows, {world}, composed, error));
    CHECK(error.find("outside") != std::string::npos);
}

TEST_CASE("a shop stocks its world's own equipment and artifacts, everything else from anywhere")
{
    const ItemTable table = loadTable({});
    CHECK(table.lootPoolForWorld("mm9") == "mm9");
    CHECK(table.lootPoolForWorld("mm7") == "engine");
    CHECK(table.lootPoolForWorld("").empty());

    const auto allowed = [&table](const std::string &world)
    {
        std::set<uint32_t> ids;
        for (uint32_t id = 1; id <= 6; ++id)
        {
            if (ItemGenerator::shopPoolAllows(*table.get(id), table.lootPoolForWorld(world)))
            {
                ids.insert(id);
            }
        }
        return ids;
    };

    // MM9: its own sword and artifact, consumables from the merged base. MM7: the merged base.
    CHECK(allowed("mm9") == std::set<uint32_t>{2, 3, 4});
    CHECK(allowed("mm7") == std::set<uint32_t>{1, 2, 5, 6});
    // A request without a world is not filtered.
    CHECK(allowed("") == std::set<uint32_t>{1, 2, 3, 4, 5, 6});
}

TEST_CASE("random loot rolls from every world's items and shops keep their world's pool")
{
    const ItemTable table = loadTable({weightRow("1", 10), weightRow("3", 10)});
    const StandardItemEnchantTable standardEnchants;
    const SpecialItemEnchantTable specialEnchants;
    std::mt19937 rng(7);

    const auto rolled = [&](ItemGenerationMode mode, const std::string &world)
    {
        std::set<uint32_t> ids;
        for (int roll = 0; roll < 200; ++roll)
        {
            const std::optional<InventoryItem> item = ItemGenerator::generateRandomInventoryItem(
                table, standardEnchants, specialEnchants,
                ItemGenerationRequest{.treasureLevel = 3, .mode = mode, .allowRareItems = false, .worldId = world},
                nullptr, rng);
            if (item)
            {
                ids.insert(item->objectDescriptionId);
            }
        }
        return ids;
    };

    CHECK(rolled(ItemGenerationMode::MonsterLoot, "mm9") == std::set<uint32_t>{1, 3});
    CHECK(rolled(ItemGenerationMode::MonsterLoot, "mm7") == std::set<uint32_t>{1, 3});
    CHECK(rolled(ItemGenerationMode::Shop, "mm9") == std::set<uint32_t>{3});
    CHECK(rolled(ItemGenerationMode::Shop, "mm7") == std::set<uint32_t>{1});
}

TEST_CASE("MM6-MM8 maps roll only the merged base's equipment unless MM9 loot in MM6-MM8 is on; MM9 rolls every world's")
{
    const ItemTable table = loadTable({weightRow("1", 10), weightRow("2", 10), weightRow("3", 10)});
    const StandardItemEnchantTable standardEnchants;
    const SpecialItemEnchantTable specialEnchants;
    std::mt19937 rng(5);
    Party party;
    party.setItemTable(&table);

    const auto rolled = [&](const std::string &world)
    {
        std::set<uint32_t> ids;
        for (int roll = 0; roll < 300; ++roll)
        {
            const std::optional<InventoryItem> item = ItemGenerator::generateRandomInventoryItem(
                table, standardEnchants, specialEnchants,
                ItemGenerationRequest{
                    .treasureLevel = 3, .mode = ItemGenerationMode::MonsterLoot, .allowRareItems = false,
                    .worldId = world},
                &party, rng);
            if (item)
            {
                ids.insert(item->objectDescriptionId);
            }
        }
        return ids;
    };

    // Off by default: MM7 rolls the base's sword only; the potion is not equipment, from anywhere. MM9 rolls both.
    CHECK_FALSE(party.mm9LootInOlderWorlds());
    CHECK(rolled("mm7") == std::set<uint32_t>{1, 2});
    CHECK(rolled("mm9") == std::set<uint32_t>{1, 2, 3});
    // On: MM7 rolls every world's sword too.
    party.setMm9LootInOlderWorlds(true);
    CHECK(rolled("mm7") == std::set<uint32_t>{1, 2, 3});
    CHECK(rolled("mm9") == std::set<uint32_t>{1, 2, 3});
}

TEST_CASE("an artifact or relic rolls only in its own world")
{
    const ItemTable table = loadTable({});
    const StandardItemEnchantTable standardEnchants;
    const SpecialItemEnchantTable specialEnchants;
    std::mt19937 rng(11);

    const auto rolled = [&](const std::string &world)
    {
        std::set<uint32_t> ids;
        for (int roll = 0; roll < 100; ++roll)
        {
            // A level-7 chest slot: artifacts and relics only.
            const std::optional<InventoryItem> item = ItemGenerator::generateRandomInventoryItem(
                table, standardEnchants, specialEnchants,
                ItemGenerationRequest{
                    .treasureLevel = 6, .mode = ItemGenerationMode::ChestLoot, .rareItemsOnly = true, .worldId = world},
                nullptr, rng);
            if (item)
            {
                ids.insert(item->objectDescriptionId);
            }
        }
        return ids;
    };

    CHECK(rolled("mm9") == std::set<uint32_t>{4});
    CHECK(rolled("mm7") == std::set<uint32_t>{5});
    CHECK(rolled("mm6") == std::set<uint32_t>{6});
    CHECK(rolled("mm8").empty());
}
