#include "doctest/doctest.h"

#include "game/maps/MapItemSourceYml.h"
#include "game/gameplay/GameplayWorldItemPolicy.h"
#include "game/gameplay/LootContainerRuntime.h"
#include "game/gameplay/SearchableLootPropRuntime.h"
#include "game/party/Party.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ItemTable.h"

#include <yaml-cpp/yaml.h>

#include <cstring>
#include <algorithm>
#include <set>
#include <filesystem>
#include <string>

TEST_CASE("MM9 native item-source scene data keeps containers and bone piles distinct")
{
    const YAML::Node rootNode = YAML::Load(R"(
world_items:
  - source_id: mm9:drangheim:object:26
    source_object_index: 26
    source_name: Plow
    position: {x: -55, y: -4783, z: 721}
    item_id: 10371
    random_item_pool: []
    required_qbits: [90128]
    forbidden_qbits: [90130]
    pickup_qbits: []
    set_qbits: [90130]
    pickup_event: 30026
loot_containers:
  - source_id: mm9:drangheim:object:19
    source_object_index: 19
    source_name: TreasureChest0
    position: {x: -88, y: -4648, z: 636}
    container_id: 0
    kind: chest
    presentation: mm9_chest
    random_treasure_level: 3
    treasure_type: 7
    gold: 25
    gold_only: false
    random: true
    ai_drop: false
    trap_level: 2
    should_repopulate: false
    fixed_items:
      - {slot: 1, raw_mm9_item_id: 371, item_id: 10371}
    remove_when_empty: false
searchable_loot_props:
  - source_id: mm9:drangheim:object:192
    source_object_index: 192
    source_name: BonePile2
    position: {x: -8448, y: -7552, z: 1446}
    kind: bone_pile
    random_treasure_level: 1
    loot_rolls: 1
    hazard:
      condition: disease
      chance: 50
      comparison: roll_1_100_strictly_less_than
    source_disease_power: 0
    keep_visual_after_search: true
actor_loot_overrides:
  - source_object_index: 42
    procedural_death_loot: true
spawned_loot_containers:
  - source_id: mm9:bathhouse:object:224
    source_object_index: 224
    source_name: DestructableProp0
    position: {x: 10, y: 20, z: 30}
    kind: treasure_bag
    presentation: mm9_treasure_bag
    random_treasure_level: 5
    treasure_type: 0
    gold: 0
    gold_only: false
    random: true
    ai_drop: false
    fixed_items: []
    remove_when_empty: true
persistent_item_mechanisms:
  - source_id: mm9:lichlab:object:1507
    source_object_index: 1507
    source_name: Prop18
    position: {x: 272, y: 1536, z: 972}
    kind: reusable_converter
    handler: elixir_cookpot
    required_items: [10378]
    grant_items:
      - {raw_mm9_item_id: 561, item_id: 10561, quantity: 1}
    random_item_pool: [10254]
    model_variants: [models/example.abc]
    model_variant_skins: [skins/example.dtx]
barrels:
  - source_id: mm9:bootcamp:barrel:372
    source_object_index: 372
    source_name: Barrel6
    position: {x: 1, y: 2, z: 3}
    interaction_event_id: 30372
    liquid_texture_cog: 20000
    bmodel_index: 44
    liquid_faces: [12, 13]
    liquid_texture_aliases: [red, blue, green, purple, white, yellow, swamp, water]
)");

    OpenYAMM::Game::MapItemSourceData sources = {};
    std::string errorMessage;
    REQUIRE(OpenYAMM::Game::parseMapItemSourceData(rootNode, sources, errorMessage));

    REQUIRE_EQ(sources.worldItems.size(), 1u);
    CHECK_EQ(sources.worldItems[0].itemId, 10371u);
    CHECK_EQ(sources.worldItems[0].requiredQBits[0], 90128u);
    CHECK_EQ(sources.worldItems[0].setQBits[0], 90130u);
    CHECK_EQ(sources.worldItems[0].pickupEvent, 30026u);

    REQUIRE_EQ(sources.lootContainers.size(), 1u);
    CHECK(sources.lootContainers[0].kind == OpenYAMM::Game::LootContainerKind::Chest);
    CHECK_EQ(sources.lootContainers[0].fixedItems[0].itemId, 10371u);
    CHECK_FALSE(sources.lootContainers[0].removeWhenEmpty);

    REQUIRE_EQ(sources.searchableLootProps.size(), 1u);
    CHECK_EQ(sources.searchableLootProps[0].lootRolls, 1);
    CHECK_EQ(sources.searchableLootProps[0].hazardChance, 50);
    CHECK(sources.searchableLootProps[0].keepVisualAfterSearch);

    REQUIRE_EQ(sources.actorLootOverrides.size(), 1u);
    CHECK(sources.actorLootOverrides[0].proceduralDeathLoot);

    REQUIRE_EQ(sources.spawnedLootContainers.size(), 1u);
    CHECK(sources.spawnedLootContainers[0].kind == OpenYAMM::Game::LootContainerKind::TreasureBag);
    CHECK(sources.spawnedLootContainers[0].removeWhenEmpty);

    REQUIRE_EQ(sources.persistentItemMechanisms.size(), 1u);
    CHECK_EQ(sources.persistentItemMechanisms[0].handler, "elixir_cookpot");
    CHECK_EQ(sources.persistentItemMechanisms[0].requiredItems[0], 10378u);
    CHECK_EQ(sources.persistentItemMechanisms[0].grantItems[0].itemId, 10561u);
    CHECK_EQ(sources.persistentItemMechanisms[0].randomItemPool[0], 10254u);
    CHECK_EQ(sources.persistentItemMechanisms[0].modelVariants[0], "models/example.abc");
    CHECK_EQ(sources.persistentItemMechanisms[0].modelVariantSkins[0], "skins/example.dtx");

    REQUIRE_EQ(sources.mm9Barrels.size(), 1u);
    CHECK_EQ(sources.mm9Barrels[0].sourceObjectIndex, 372u);
    CHECK_EQ(sources.mm9Barrels[0].interactionEventId, 30372u);
    CHECK_EQ(sources.mm9Barrels[0].liquidFaces.size(), 2u);
    CHECK_EQ(sources.mm9Barrels[0].liquidTextureAliases[7], "water");
}

TEST_CASE("map item-source parser rejects an unknown container kind")
{
    const YAML::Node rootNode = YAML::Load(R"(
loot_containers:
  - source_id: invalid
    source_object_index: 1
    source_name: Invalid
    position: {x: 0, y: 0, z: 0}
    container_id: 0
    kind: bone_pile
)");

    OpenYAMM::Game::MapItemSourceData sources = {};
    std::string errorMessage;
    CHECK_FALSE(OpenYAMM::Game::parseMapItemSourceData(rootNode, sources, errorMessage));
    CHECK(errorMessage == "item-source kind must be chest or treasure_bag");
}

TEST_CASE("quest world-item availability evaluates shared party qbits")
{
    OpenYAMM::Game::MapWorldItemSource source = {};
    source.requiredQBits = {90128};
    source.forbiddenQBits = {90130};

    OpenYAMM::Game::Party party = {};
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());
    CHECK_FALSE(OpenYAMM::Game::worldItemPolicyAvailable(source, party));

    party.setQuestBit(90128, true);
    CHECK(OpenYAMM::Game::worldItemPolicyAvailable(source, party));

    party.setQuestBit(90130, true);
    CHECK_FALSE(OpenYAMM::Game::worldItemPolicyAvailable(source, party));
}

TEST_CASE("a placed world item's pickup quest bits gate the take, not the showing")
{
    OpenYAMM::Game::MapWorldItemSource source = {};
    source.forbiddenQBits = {90216};
    source.pickupQBits = {90214};

    OpenYAMM::Game::Party party = {};
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());
    CHECK(OpenYAMM::Game::worldItemPolicyAvailable(source, party));
    CHECK_FALSE(OpenYAMM::Game::worldItemPickupAllowed(source, party));

    party.setQuestBit(90214, true);
    CHECK(OpenYAMM::Game::worldItemPickupAllowed(source, party));
}

TEST_CASE("placed world item without an item or a pool is rejected")
{
    const YAML::Node rootNode = YAML::Load(R"(
world_items:
  - {source_id: a, source_object_index: 1, source_name: A, position: {x: 0, y: 0, z: 0}, item_id: 0,
     random_item_pool: [], required_qbits: [], forbidden_qbits: [], pickup_qbits: [], set_qbits: [], pickup_event: 0}
)");
    OpenYAMM::Game::MapItemSourceData sources = {};
    std::string errorMessage;
    CHECK_FALSE(OpenYAMM::Game::parseMapItemSourceData(rootNode, sources, errorMessage));
    CHECK_NE(errorMessage.find("item_id or random_item_pool"), std::string::npos);
}

TEST_CASE("MM9 bone pile uses native one-shot disease comparison without opening a container")
{
    OpenYAMM::Game::MapSearchableLootPropSource source = {};
    source.sourceId = "mm9:test:object:7";
    source.kind = "bone_pile";
    source.hazardCondition = "disease";
    source.hazardChance = 50;
    source.hazardComparison = "roll_1_100_strictly_less_than";
    source.keepVisualAfterSearch = true;

    CHECK(OpenYAMM::Game::searchableLootPropHazardTriggers(source, 49));
    CHECK_FALSE(OpenYAMM::Game::searchableLootPropHazardTriggers(source, 50));

    OpenYAMM::Game::Party party = {};
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());
    OpenYAMM::Game::SearchableLootPropState state = {};
    const OpenYAMM::Game::SearchableLootPropResult first =
        OpenYAMM::Game::applySearchableLootPropResult(source, state, 49, std::nullopt, party);

    CHECK(first.handled);
    CHECK_FALSE(first.alreadySearched);
    CHECK(first.diseaseApplied);
    CHECK_FALSE(first.itemGenerated);
    CHECK(state.searchedSourceIds.contains(source.sourceId));
    REQUIRE(party.activeMember() != nullptr);
    CHECK(party.activeMember()->conditions.test(
        static_cast<size_t>(OpenYAMM::Game::CharacterCondition::DiseaseWeak)));

    const OpenYAMM::Game::SearchableLootPropResult second =
        OpenYAMM::Game::applySearchableLootPropResult(source, state, 1, std::nullopt, party);
    CHECK(second.handled);
    CHECK(second.alreadySearched);
    CHECK_FALSE(second.diseaseApplied);
}

TEST_CASE("MM9 treasure bag materializes through chest records without bone-pile hazard state")
{
    OpenYAMM::Game::MapLootContainerSource source = {};
    source.sourceId = "mm9:test:object:8";
    source.containerId = 2;
    source.kind = OpenYAMM::Game::LootContainerKind::TreasureBag;
    source.randomTreasureLevel = 4;
    source.random = true;
    source.fixedItems.push_back(OpenYAMM::Game::MapFixedContainerItem{1, 371, 10371});

    const OpenYAMM::Game::MapDeltaChest chest =
        OpenYAMM::Game::buildLootContainerChest(source, 3, 90, 1234, nullptr, nullptr);

    REQUIRE_EQ(chest.rawItems.size(), 72u);
    REQUIRE_EQ(chest.inventoryMatrix.size(), 81u);
    CHECK_EQ(chest.inventoryMatrix[0], 1);
    CHECK_EQ(chest.inventoryMatrix[1], 2);
    int32_t fixedItemId = 0;
    int32_t randomTier = 0;
    std::memcpy(&fixedItemId, chest.rawItems.data(), sizeof(fixedItemId));
    std::memcpy(&randomTier, chest.rawItems.data() + 36, sizeof(randomTier));
    CHECK_EQ(fixedItemId, 10371);
    CHECK_EQ(randomTier, -4);
    CHECK_EQ(chest.flags, 0);
}

TEST_CASE("loot container random_records holds that many random treasure records")
{
    const YAML::Node sourceNode = YAML::Load(R"(
loot_containers:
  - source_id: mm9:test:chest
    source_object_index: 0
    source_name: TreasureChest0
    position: {x: 0, y: 0, z: 0}
    container_id: 0
    kind: chest
    presentation: mm9_chest
    random_treasure_level: 3
    treasure_type: 7
    gold: 0
    gold_only: false
    random: true
    ai_drop: false
    trap_level: 0
    should_repopulate: false
    fixed_items: []
    remove_when_empty: false
    random_records: 3
)");
    OpenYAMM::Game::MapItemSourceData sources;
    std::string error;
    REQUIRE(OpenYAMM::Game::parseMapItemSourceData(sourceNode, sources, error));
    const OpenYAMM::Game::MapDeltaChest chest =
        OpenYAMM::Game::buildLootContainerChest(sources.lootContainers.front(), 2, 9036, 7, nullptr, nullptr);
    REQUIRE_EQ(chest.rawItems.size(), 3u * 36u);

    for (size_t offset = 0; offset < chest.rawItems.size(); offset += 36)
    {
        int32_t itemId = 0;
        std::memcpy(&itemId, chest.rawItems.data() + offset, sizeof(itemId));
        CHECK_EQ(itemId, -3);
    }

    YAML::Node withoutField = YAML::Clone(sourceNode);
    withoutField["loot_containers"][0].remove("random_records");
    OpenYAMM::Game::MapItemSourceData single;
    REQUIRE(OpenYAMM::Game::parseMapItemSourceData(withoutField, single, error));
    CHECK_EQ(single.lootContainers.front().randomRecords, 1u);

    YAML::Node zero = YAML::Clone(sourceNode);
    zero["loot_containers"][0]["random_records"] = 0;
    OpenYAMM::Game::MapItemSourceData rejected;
    CHECK_FALSE(OpenYAMM::Game::parseMapItemSourceData(zero, rejected, error));
}

TEST_CASE("Map-local chest item pools validate and produce persistent native item records")
{
    const YAML::Node sourceNode = YAML::Load(R"(
loot_containers:
  - source_id: mm8:test:chest
    source_object_index: 0
    source_name: Cache
    position: {x: 0, y: 0, z: 0}
    container_id: 0
    kind: chest
    presentation: wooden chest
    random_treasure_level: 6
    treasure_type: 0
    gold: 0
    gold_only: false
    random: true
    ai_drop: false
    trap_level: 1
    should_repopulate: true
    fixed_items: []
    remove_when_empty: false
    random_item_pool: [5, 15, 35, 55, 65, 98]
    random_item_count: 3
)");
    OpenYAMM::Game::MapItemSourceData sources;
    std::string error;
    REQUIRE(OpenYAMM::Game::parseMapItemSourceData(sourceNode, sources, error));
    REQUIRE_EQ(sources.lootContainers.size(), 1u);
    const OpenYAMM::Game::MapLootContainerSource &source = sources.lootContainers.front();
    std::set<std::vector<uint8_t>> generated;
    for (uint32_t seed = 1; seed <= 8; ++seed)
    {
        const OpenYAMM::Game::MapDeltaChest chest =
            OpenYAMM::Game::buildLootContainerChest(source, 6, 9082, seed, nullptr, nullptr);
        CHECK(chest.rawItems ==
            OpenYAMM::Game::buildLootContainerChest(source, 6, 9082, seed, nullptr, nullptr).rawItems);
        REQUIRE_EQ(chest.rawItems.size(), 108u);
        std::set<int32_t> selected;
        for (size_t offset = 0; offset < chest.rawItems.size(); offset += 36)
        {
            int32_t itemId = 0;
            std::memcpy(&itemId, chest.rawItems.data() + offset, sizeof(itemId));
            CHECK(std::find(source.randomItemPool.begin(), source.randomItemPool.end(), uint32_t(itemId))
                != source.randomItemPool.end());
            selected.insert(itemId);
        }
        CHECK_EQ(selected.size(), 3u);
        generated.insert(chest.rawItems);
    }
    CHECK_GT(generated.size(), 1u);

    for (const char *pInvalid : {"random_item_pool: [0, 5, 15]", "random_item_pool: [5, 5, 15]",
        "random_item_pool: []", "random_item_pool: [4294967295, 5, 15]", "random_item_count: 0",
        "random_item_count: 7", "gold_only: true", "random: false"})
    {
        YAML::Node invalid = YAML::Clone(sourceNode);
        const YAML::Node change = YAML::Load(pInvalid);
        invalid["loot_containers"][0][change.begin()->first.as<std::string>()] = change.begin()->second;
        OpenYAMM::Game::MapItemSourceData rejected;
        CHECK_FALSE(OpenYAMM::Game::parseMapItemSourceData(invalid, rejected, error));
        CHECK_FALSE(error.empty());
    }
}

TEST_CASE("MM9 destructible treasure bag becomes a dense shared loot container only at trigger time")
{
    OpenYAMM::Game::MapSpawnedLootContainerSource source = {};
    source.sourceId = "mm9:bathhouse:object:224";
    source.sourceObjectIndex = 224;
    source.kind = OpenYAMM::Game::LootContainerKind::TreasureBag;
    source.randomTreasureLevel = 5;
    source.random = true;
    source.removeWhenEmpty = true;

    const OpenYAMM::Game::MapLootContainerSource materialized =
        OpenYAMM::Game::materializeSpawnedLootContainerSource(source, 17);

    CHECK_EQ(materialized.sourceId, source.sourceId);
    CHECK_EQ(materialized.containerId, 17);
    CHECK(materialized.kind == OpenYAMM::Game::LootContainerKind::TreasureBag);
    CHECK_EQ(materialized.randomTreasureLevel, 5);
    CHECK(materialized.removeWhenEmpty);

    const OpenYAMM::Game::MapDeltaChest chest =
        OpenYAMM::Game::buildLootContainerChest(materialized, 2, 90, 1234, nullptr, nullptr);
    REQUIRE_EQ(chest.rawItems.size(), 36u);
    int32_t randomTier = 0;
    std::memcpy(&randomTier, chest.rawItems.data(), sizeof(randomTier));
    CHECK_EQ(randomTier, -5);
}

TEST_CASE("MM9 loot-container presentation resolves through the shared chest table")
{
    OpenYAMM::Game::ChestTable chestTable = {};
    REQUIRE(chestTable.loadRows({
        {"0", "wooden chest", "14", "10", "1", "chest01", "42", "34", "9", "9"},
        {"1", "mm9_treasure_bag", "14", "10", "3", "mm9_treasure_bag", "18", "30", "9", "9"},
    }));

    OpenYAMM::Game::MapLootContainerSource source = {};
    source.presentation = "mm9_treasure_bag";
    const OpenYAMM::Game::MapDeltaChest chest =
        OpenYAMM::Game::buildLootContainerChest(source, 0, 90, 1234, nullptr, &chestTable);

    CHECK_EQ(chest.chestTypeId, 1u);
    REQUIRE(chestTable.get(chest.chestTypeId) != nullptr);
    CHECK_EQ(chestTable.get(chest.chestTypeId)->textureName, "mm9_treasure_bag");

    const std::filesystem::path iconRoot =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/icons_x2";
    CHECK(std::filesystem::exists(iconRoot / "mm9_chest.png"));
    CHECK(std::filesystem::exists(iconRoot / "mm9_treasure_bag.png"));
}
