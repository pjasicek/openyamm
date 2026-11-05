#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/content/ContentManifest.h"
#include "game/content/ContentTableComposer.h"
#include "game/gameplay/GameplayActorService.h"

#include <doctest/doctest.h>

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <vector>

namespace
{
std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_manifest_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}
}

TEST_CASE("content manifests default when package files are absent")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    std::filesystem::create_directories(assetRoot);

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        std::string error;
        const OpenYAMM::Game::WorldManifest world =
            OpenYAMM::Game::loadActiveWorldManifestOrDefault(assetFileSystem, "mm8", error);
        CHECK(error.empty());
        CHECK_FALSE(world.loadedFromFile);
        CHECK_EQ(world.id, "mm8");
        CHECK_EQ(world.start.mapFileName, "out01.odm");
        CHECK_FALSE(world.partyMovement.declared);
        CHECK_FALSE(world.actorAwareness.declared);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("content manifests parse mounted world definition")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(
        assetRoot / "worlds" / "custom" / "world.yml",
        "id: custom\n"
        "name: Custom World\n"
        "sourceGame: custom\n"
        "qbits:\n"
        "  begin: 90000\n"
        "  end: 99999\n"
        "  mapping: raw_mm9_key_plus_90000\n"
        "partyMovement:\n"
        "  eyeHeight: 152\n"
        "  collisionRadius: 38\n"
        "  collisionHeight: 169\n"
        "  maxStepHeight: 40.96\n"
        "actorAwareness:\n"
        "  partyEngagementRange: 4096\n"
        "actorCombat:\n"
        "  meleeVerticalReach: 0.5\n"
        "tavernHirelings: false\n"
        "start:\n"
        "  map: custom01.odm\n"
        "  introMovie: custom_intro\n");
    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "custom"));

        std::string error;
        const OpenYAMM::Game::WorldManifest world =
            OpenYAMM::Game::loadActiveWorldManifestOrDefault(assetFileSystem, "custom", error);
        CHECK(error.empty());
        REQUIRE(world.loadedFromFile);
        CHECK_EQ(world.id, "custom");
        CHECK_EQ(world.name, "Custom World");
        CHECK_EQ(world.start.mapFileName, "custom01.odm");
        CHECK_EQ(world.start.introMovie, "custom_intro");
        REQUIRE(world.qbits.declared);
        CHECK_EQ(world.qbits.begin, 90000u);
        CHECK_EQ(world.qbits.end, 99999u);
        CHECK_EQ(world.qbits.mapping, "raw_mm9_key_plus_90000");
        REQUIRE(world.partyMovement.declared);
        CHECK_EQ(world.partyMovement.eyeHeight, 152.0f);
        CHECK_EQ(world.partyMovement.collisionRadius, 38.0f);
        CHECK_EQ(world.partyMovement.collisionHeight, 169.0f);
        CHECK_EQ(world.partyMovement.maxStepHeight, doctest::Approx(40.96f));
        REQUIRE(world.actorAwareness.declared);
        CHECK_EQ(world.actorAwareness.partyEngagementRange, 4096.0f);
        CHECK_EQ(world.actorCombat.meleeVerticalReach, 0.5f);
        CHECK_FALSE(world.tavernHirelings);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("content manifests reject incomplete party movement profiles")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(
        assetRoot / "worlds" / "invalid" / "world.yml",
        "id: invalid\n"
        "partyMovement:\n"
        "  eyeHeight: 152\n"
        "  collisionRadius: 38\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        std::string error;
        CHECK_FALSE(OpenYAMM::Game::loadWorldManifest(
            assetFileSystem,
            "worlds/invalid/world.yml",
            "invalid",
            error).has_value());
        CHECK(error.find("partyMovement") != std::string::npos);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("content manifests reject invalid actor awareness profiles")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(
        assetRoot / "worlds" / "invalid" / "world.yml",
        "id: invalid\n"
        "actorAwareness:\n"
        "  partyEngagementRange: 0\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        std::string error;
        CHECK_FALSE(OpenYAMM::Game::loadWorldManifest(
            assetFileSystem,
            "worlds/invalid/world.yml",
            "invalid",
            error).has_value());
        CHECK(error.find("partyEngagementRange") != std::string::npos);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("content manifests reject invalid actor combat profiles; without one melee ignores height")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(
        assetRoot / "worlds" / "invalid" / "world.yml", "id: invalid\nactorCombat:\n  meleeVerticalReach: -1\n");
    writeTextFile(assetRoot / "worlds" / "missing" / "world.yml", "id: missing\nactorCombat: {}\n");
    writeTextFile(assetRoot / "worlds" / "plain" / "world.yml", "id: plain\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        std::string error;
        CHECK_FALSE(OpenYAMM::Game::loadWorldManifest(assetFileSystem, "worlds/invalid/world.yml", "invalid", error)
            .has_value());
        CHECK(error.find("meleeVerticalReach must be a number in 0-4") != std::string::npos);
        CHECK_FALSE(OpenYAMM::Game::loadWorldManifest(assetFileSystem, "worlds/missing/world.yml", "missing", error)
            .has_value());
        CHECK(error.find("actorCombat must declare meleeVerticalReach") != std::string::npos);
        const std::optional<OpenYAMM::Game::WorldManifest> plain =
            OpenYAMM::Game::loadWorldManifest(assetFileSystem, "worlds/plain/world.yml", "plain", error);
        REQUIRE(plain.has_value());
        CHECK_EQ(plain->actorCombat.meleeVerticalReach, 0.0f);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("content manifests parse the actor level radius limit; without one a body meets the level at its radius")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(
        assetRoot / "worlds" / "limited" / "world.yml", "id: limited\nactorMovement:\n  levelRadiusLimit: 60\n");
    writeTextFile(
        assetRoot / "worlds" / "invalid" / "world.yml", "id: invalid\nactorMovement:\n  levelRadiusLimit: -1\n");
    writeTextFile(assetRoot / "worlds" / "missing" / "world.yml", "id: missing\nactorMovement: {}\n");
    writeTextFile(assetRoot / "worlds" / "plain" / "world.yml", "id: plain\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        std::string error;
        const std::optional<OpenYAMM::Game::WorldManifest> limited =
            OpenYAMM::Game::loadWorldManifest(assetFileSystem, "worlds/limited/world.yml", "limited", error);
        REQUIRE(limited.has_value());
        CHECK_EQ(limited->actorMovement.levelRadiusLimit, 60.0f);
        CHECK_FALSE(OpenYAMM::Game::loadWorldManifest(assetFileSystem, "worlds/invalid/world.yml", "invalid", error)
            .has_value());
        CHECK(error.find("levelRadiusLimit must be a finite number, 0 or more") != std::string::npos);
        CHECK_FALSE(OpenYAMM::Game::loadWorldManifest(assetFileSystem, "worlds/missing/world.yml", "missing", error)
            .has_value());
        CHECK(error.find("actorMovement must declare levelRadiusLimit") != std::string::npos);
        const std::optional<OpenYAMM::Game::WorldManifest> plain =
            OpenYAMM::Game::loadWorldManifest(assetFileSystem, "worlds/plain/world.yml", "plain", error);
        REQUIRE(plain.has_value());
        CHECK_EQ(plain->actorMovement.levelRadiusLimit, 0.0f);

        // A Queen Cobra (radius 72) meets the level at the limit; a narrower body keeps its own radius.
        OpenYAMM::Game::GameplayActorService actorService;
        CHECK_EQ(actorService.levelCollisionRadius(72.0f), 72.0f);
        actorService.setLevelRadiusLimit(limited->actorMovement.levelRadiusLimit);
        CHECK_EQ(actorService.levelCollisionRadius(72.0f), 60.0f);
        CHECK_EQ(actorService.levelCollisionRadius(40.0f), 40.0f);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("content manifests parse stable item contribution contracts")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(
        assetRoot / "worlds" / "mm9" / "world.yml",
        "id: mm9\n"
        "name: MM9\n"
        "sourceGame: mm9\n"
        "contentSchemaVersion: 3\n"
        "dependencies:\n"
        "  - engine\n"
        "idRanges:\n"
        "  items:\n"
        "    begin: 10000\n"
        "    end: 10999\n"
        "tableContributions:\n"
        "  - table: items\n"
        "    mode: append\n"
        "    path: data_tables/items.txt\n"
        "    sourceIdColumn: 32\n"
        "    canonicalIdColumn: 33\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        std::string error;
        const std::optional<OpenYAMM::Game::WorldManifest> world = OpenYAMM::Game::loadWorldManifest(
            assetFileSystem,
            "worlds/mm9/world.yml",
            "mm9",
            error);
        REQUIRE(world.has_value());
        CHECK(error.empty());
        CHECK_EQ(world->contentSchemaVersion, 3u);
        REQUIRE_EQ(world->dependencies.size(), 1);
        CHECK_EQ(world->dependencies[0], "engine");

        const OpenYAMM::Game::ContentIdRangeDefinition *pItemRange = world->findIdRange("ITEMS");
        REQUIRE(pItemRange != nullptr);
        CHECK_EQ(pItemRange->begin, 10000u);
        CHECK_EQ(pItemRange->end, 10999u);
        REQUIRE_EQ(world->tableContributions.size(), 1);
        CHECK(world->tableContributions[0].mode == OpenYAMM::Game::TableContributionMode::Append);
        CHECK_EQ(world->tableContributions[0].idDomain, "items");
        CHECK_EQ(world->tableContributions[0].path, "data_tables/items.txt");
        CHECK_EQ(world->tableContributions[0].sourceIdColumn, 32);
        CHECK_EQ(world->tableContributions[0].canonicalIdColumn, 33);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("content manifests reject escaping contribution paths")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(
        assetRoot / "worlds" / "unsafe" / "world.yml",
        "id: unsafe\n"
        "idRanges:\n"
        "  items: {begin: 11000, end: 11999}\n"
        "tableContributions:\n"
        "  - table: items\n"
        "    mode: append\n"
        "    path: ../engine/data_tables/items.txt\n"
        "    sourceIdColumn: 32\n"
        "    canonicalIdColumn: 33\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        std::string error;
        CHECK_FALSE(OpenYAMM::Game::loadWorldManifest(
            assetFileSystem,
            "worlds/unsafe/world.yml",
            "unsafe",
            error).has_value());
        CHECK(error.find("relative path") != std::string::npos);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("item table contributions compose deterministically with normalized provenance")
{
    std::vector<std::vector<std::string>> baseRows = {{"1", "item001", "Base Sword"}};
    std::vector<std::string> mm9Row(45);
    mm9Row[0] = "10002";
    mm9Row[1] = "mm9_item_10002";
    mm9Row[2] = "Poor Sword";
    mm9Row[32] = "2";
    mm9Row[33] = "mm9:item/poor_sword";

    OpenYAMM::Game::ItemTableContributionRows mm9 = {};
    mm9.packageId = "mm9";
    mm9.idRange = OpenYAMM::Game::ContentIdRangeDefinition{"items", 10000, 10999};
    mm9.sourceIdColumn = 32;
    mm9.canonicalIdColumn = 33;
    mm9.rows.push_back(mm9Row);

    std::vector<std::vector<std::string>> composedRows;
    std::string error;
    REQUIRE(OpenYAMM::Game::composeItemTableRows(baseRows, {mm9}, composedRows, error));
    CHECK(error.empty());
    REQUIRE_EQ(composedRows.size(), 2);
    CHECK_EQ(composedRows[1][17], "mm9");
    CHECK_EQ(composedRows[1][18], "mm9:item/poor_sword");
    CHECK_EQ(composedRows[1][19], "2");
}

TEST_CASE("keyed table contributions can use a non-leading item id column")
{
    const std::vector<std::vector<std::string>> baseRows = {
        {"Id", "Item id", "Notes"},
        {"1", "84", "Leather Jerkin"},
        {"1", "109", "Helm"},
    };

    OpenYAMM::Game::KeyedTableContributionRows mm9 = {};
    mm9.packageId = "mm9";
    mm9.idRange = OpenYAMM::Game::ContentIdRangeDefinition{"items", 10000, 10999};
    mm9.idColumn = 1;
    mm9.rows = {
        {"Id", "Item id", "Notes"},
        {"1", "10086", "Arming Doublet"},
    };

    std::vector<std::vector<std::string>> composedRows;
    std::string error;
    REQUIRE(OpenYAMM::Game::composeKeyedAppendTableRows(baseRows, {mm9}, composedRows, error, 1));
    CHECK(error.empty());
    REQUIRE_EQ(composedRows.size(), 4);
    CHECK_EQ(composedRows.back()[1], "10086");
}

TEST_CASE("item table contributions reject id and range collisions")
{
    std::vector<std::string> firstRow(34);
    firstRow[0] = "10002";
    firstRow[32] = "2";
    firstRow[33] = "mm9:item/poor_sword";

    OpenYAMM::Game::ItemTableContributionRows first = {};
    first.packageId = "mm9";
    first.idRange = OpenYAMM::Game::ContentIdRangeDefinition{"items", 10000, 10999};
    first.sourceIdColumn = 32;
    first.canonicalIdColumn = 33;
    first.rows.push_back(firstRow);

    OpenYAMM::Game::ItemTableContributionRows overlapping = first;
    overlapping.packageId = "custom";
    overlapping.idRange = OpenYAMM::Game::ContentIdRangeDefinition{"items", 10900, 11900};
    overlapping.rows[0][33] = "custom:item/poor_sword";

    std::vector<std::vector<std::string>> composedRows;
    std::string error;
    CHECK_FALSE(OpenYAMM::Game::composeItemTableRows({}, {first, overlapping}, composedRows, error));
    CHECK(error.find("overlapping") != std::string::npos);

    first.idRange = OpenYAMM::Game::ContentIdRangeDefinition{"items", 10001, 10001};
    CHECK_FALSE(OpenYAMM::Game::composeItemTableRows({}, {first}, composedRows, error));
    CHECK(error.find("outside") != std::string::npos);
}
