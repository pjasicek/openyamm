#pragma once

#include <cstdint>
#include <limits>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class LootContainerKind
{
    Chest,
    TreasureBag,
};

struct MapItemSourcePosition
{
    int x = 0;
    int y = 0;
    int z = 0;
};

struct MapFixedContainerItem
{
    uint8_t slot = 0;
    uint32_t rawMm9ItemId = 0;
    uint32_t itemId = 0;
};

struct MapWorldItemGrant
{
    uint32_t rawMm9ItemId = 0;
    uint32_t itemId = 0;
    uint32_t quantity = 1;
};

struct MapWorldItemSource
{
    std::string sourceId;
    uint32_t sourceObjectIndex = 0;
    std::string sourceName;
    MapItemSourcePosition position = {};
    std::string kind;
    uint32_t rawPrimaryItemId = 0;
    uint32_t itemId = 0;
    std::vector<uint32_t> requiredQBits;
    std::vector<uint32_t> forbiddenQBits;
    std::vector<uint32_t> requiredItems;
    std::vector<uint32_t> forbiddenItems;
    std::vector<MapWorldItemGrant> grantItems;
    std::vector<uint32_t> takeItems;
    std::vector<uint32_t> setQBits;
    std::vector<uint32_t> clearQBits;
    std::vector<uint32_t> randomItemPool;
    std::string onPickupEvent;
    bool consumeOnSuccess = true;
};

struct MapLootContainerSource
{
    std::string sourceId;
    uint32_t sourceObjectIndex = 0;
    std::string sourceName;
    MapItemSourcePosition position = {};
    uint32_t containerId = 0;
    LootContainerKind kind = LootContainerKind::Chest;
    std::string presentation;
    int randomTreasureLevel = 0;
    int treasureType = 0;
    int gold = 0;
    bool goldOnly = false;
    bool random = false;
    bool aiDrop = false;
    int trapLevel = 0;
    bool shouldRepopulate = false;
    std::vector<MapFixedContainerItem> fixedItems;
    std::vector<uint32_t> randomItemPool;
    uint32_t randomItemCount = 0;
    // random_records (optional): the random_treasure_level records the container holds; each rolls 1-5 times when
    // opened, like an MM6-MM8 chest slot (MM9 chests at MM7's average, BALANCE_PLAN.md 3.7).
    uint32_t randomRecords = 1;
    bool removeWhenEmpty = false;
};

struct MapSearchableLootPropSource
{
    std::string sourceId;
    uint32_t sourceObjectIndex = 0;
    std::string sourceName;
    MapItemSourcePosition position = {};
    std::string kind;
    int randomTreasureLevel = 0;
    int lootRolls = 0;
    std::string hazardCondition;
    int hazardChance = 0;
    std::string hazardComparison;
    int sourceDiseasePower = 0;
    bool keepVisualAfterSearch = false;
};

struct MapActorLootOverride
{
    uint32_t sourceObjectIndex = 0;
    bool proceduralDeathLoot = false;
};

struct MapSpawnedLootContainerSource
{
    std::string sourceId;
    uint32_t sourceObjectIndex = 0;
    std::string sourceName;
    MapItemSourcePosition position = {};
    LootContainerKind kind = LootContainerKind::TreasureBag;
    std::string presentation;
    int randomTreasureLevel = 0;
    int treasureType = 0;
    int gold = 0;
    bool goldOnly = false;
    bool random = false;
    bool aiDrop = false;
    std::vector<MapFixedContainerItem> fixedItems;
    bool removeWhenEmpty = false;
};

struct MapPersistentItemMechanismSource
{
    std::string sourceId;
    uint32_t sourceObjectIndex = 0;
    std::string sourceName;
    MapItemSourcePosition position = {};
    std::string kind;
    std::string handler;
    std::vector<uint32_t> requiredItems;
    std::vector<MapWorldItemGrant> grantItems;
    std::vector<uint32_t> randomItemPool;
    std::vector<std::string> modelVariants;
    std::vector<std::string> modelVariantSkins;
};

struct MapMm9BarrelSource
{
    std::string sourceId;
    uint32_t sourceObjectIndex = 0;
    std::string sourceName;
    MapItemSourcePosition position = {};
    uint16_t interactionEventId = 0;
    uint16_t liquidTextureCog = 0;
    uint32_t bmodelIndex = std::numeric_limits<uint32_t>::max();
    std::vector<uint32_t> liquidFaces;
    std::vector<std::string> liquidTextureAliases;
};

struct MapItemSourceData
{
    std::vector<MapWorldItemSource> worldItems;
    std::vector<MapLootContainerSource> lootContainers;
    std::vector<MapSearchableLootPropSource> searchableLootProps;
    std::vector<MapActorLootOverride> actorLootOverrides;
    std::vector<MapSpawnedLootContainerSource> spawnedLootContainers;
    std::vector<MapPersistentItemMechanismSource> persistentItemMechanisms;
    std::vector<MapMm9BarrelSource> mm9Barrels;
};
}
