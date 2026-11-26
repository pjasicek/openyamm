#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/content/ContentManifest.h"
#include "game/content/ContentTableComposer.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"

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
        // MM6-MM8 keep MMerge's street NPCs (group news, generated peasants) unless world.yml turns them off.
        CHECK(world.streetNpcs);
        CHECK(world.streetNpcGroupNews);
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
        "loadingScreens: [world_page]\n"
        "mapLoadingScreens: {Custom01.ODM: arrival_page}\n"
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
        "  mm9Sight: {allRound: true, scale: 1.5}\n"
        "  mm9Provoke: {range: 4096, radius: 256}\n"
        "actorCombat:\n"
        "  meleeVerticalReach: 0.5\n"
        "tavernHirelings: false\n"
        "streetNpcs: false\n"
        "streetNpcGroupNews: false\n"
        "music:\n"
        "  repeatGapSeconds: 10\n"
        "  battleTrack: 90003\n"
        "ambientSounds:\n"
        "  dayHours: [5, 17]\n"
        "  pan: false\n"
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
        const OpenYAMM::Game::MergedContinentSettingTable continents;
        CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, std::nullopt, "CUSTOM01.ODM")
            == std::vector<std::string>{"arrival_page"});
        CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, std::nullopt, "other.blv")
            == std::vector<std::string>{"world_page"});
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
        CHECK(world.actorAwareness.mm9SightAllRound);
        CHECK_EQ(world.actorAwareness.mm9SightScale, 1.5f);
        CHECK_EQ(world.actorAwareness.mm9ProvokeRange, 4096.0f);
        CHECK_EQ(world.actorAwareness.mm9ProvokeRadius, 256.0f);
        CHECK_EQ(world.actorCombat.meleeVerticalReach, 0.5f);
        CHECK_FALSE(world.tavernHirelings);
        CHECK_FALSE(world.streetNpcs);
        CHECK_FALSE(world.streetNpcGroupNews);
        CHECK_EQ(world.music.repeatGapSeconds, 10.0f);
        CHECK_EQ(world.music.battleTrack, 90003);
        CHECK_EQ(world.music.battleFadeSeconds, 2.5f);
        CHECK_EQ(world.ambientSounds.dayStartHour, 5.0f);
        CHECK_EQ(world.ambientSounds.dayEndHour, 17.0f);
        CHECK_FALSE(world.ambientSounds.pan);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("only MM9 turns MMerge's street NPCs off: its dogs and townsfolk without DoRude get no generated dialogue")
{
    // The 2026-11-07 playtest bug: Sturmford City's dogs (group 3, no NPC, no RUDE id) answered with npc_group.txt
    // group 3's MM8 news and a stand-in portrait. MM9's groups are its scripts'; MM6-MM8 keep their street NPCs.
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;

    for (const char *pWorldId : {"mm6", "mm7", "mm8", "mm9", "xeen"})
    {
        if (!std::filesystem::exists(sourceRoot / "assets_dev" / "worlds" / pWorldId / "world.yml"))
        {
            continue;
        }

        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            sourceRoot,
            sourceRoot / "assets_dev",
            OpenYAMM::Engine::AssetScaleTier::X1,
            pWorldId));
        std::string error;
        const OpenYAMM::Game::WorldManifest world =
            OpenYAMM::Game::loadActiveWorldManifestOrDefault(assetFileSystem, pWorldId, error);
        CAPTURE(pWorldId);
        CHECK(error.empty());
        CHECK_EQ(world.streetNpcs, std::string(pWorldId) != "mm9");
        // Xeen keeps its generated villagers but not MMerge's group news: its groups are its maps' own.
        CHECK_EQ(world.streetNpcGroupNews, std::string(pWorldId) != "xeen");
    }
}

TEST_CASE("only MM9's friendly actors block the party: MM6-MM8 parties walk through townsfolk")
{
    // The user, 2026-11-07: MM9's NPCs, townsfolk and animals are solid; MM6-MM8 keep the walk-through rule.
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;

    for (const char *pWorldId : {"mm6", "mm7", "mm8", "mm9"})
    {
        if (!std::filesystem::exists(sourceRoot / "assets_dev" / "worlds" / pWorldId / "world.yml"))
        {
            continue;
        }

        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            sourceRoot,
            sourceRoot / "assets_dev",
            OpenYAMM::Engine::AssetScaleTier::X1,
            pWorldId));
        std::string error;
        const OpenYAMM::Game::WorldManifest world =
            OpenYAMM::Game::loadActiveWorldManifestOrDefault(assetFileSystem, pWorldId, error);
        CAPTURE(pWorldId);
        CHECK(error.empty());
        CHECK_EQ(world.friendlyActorsBlockParty, std::string(pWorldId) == "mm9");
    }

    CHECK_FALSE(OpenYAMM::Game::WorldManifest{}.friendlyActorsBlockParty);

    using OpenYAMM::Game::GameplayActorControlMode;
    OpenYAMM::Game::GameplayActorService actorService;
    // MM6-MM8 (the default): only hostile actors block.
    CHECK(actorService.actorBlocksPartyMovement(true, GameplayActorControlMode::None));
    CHECK_FALSE(actorService.actorBlocksPartyMovement(false, GameplayActorControlMode::None));
    // MM9: friendly actors block too, except the party's own charmed, enslaved or raised monsters.
    actorService.setFriendlyActorsBlockParty(true);
    CHECK(actorService.actorBlocksPartyMovement(true, GameplayActorControlMode::None));
    CHECK(actorService.actorBlocksPartyMovement(false, GameplayActorControlMode::None));
    CHECK(actorService.actorBlocksPartyMovement(false, GameplayActorControlMode::Berserk));
    CHECK_FALSE(actorService.actorBlocksPartyMovement(false, GameplayActorControlMode::Charm));
    CHECK_FALSE(actorService.actorBlocksPartyMovement(false, GameplayActorControlMode::Enslaved));
    CHECK_FALSE(actorService.actorBlocksPartyMovement(false, GameplayActorControlMode::ControlUndead));
    CHECK_FALSE(actorService.actorBlocksPartyMovement(false, GameplayActorControlMode::Reanimated));
}

TEST_CASE("worlds without music or ambient sound rules keep the MM6-MM8 defaults")
{
    const OpenYAMM::Game::WorldManifest world = {};
    CHECK_EQ(world.music.repeatGapSeconds, 0.0f);
    CHECK_EQ(world.music.battleTrack, 0);
    CHECK_EQ(world.ambientSounds.dayStartHour, 6.0f);
    CHECK_EQ(world.ambientSounds.dayEndHour, 20.0f);
    CHECK(world.ambientSounds.pan);
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

TEST_CASE("content manifests parse story ambience choices and QBit-gated music areas")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "worlds" / "story" / "world.yml",
        "id: story\n"
        "ambience:\n"
        "  plain.odm: wind\n"
        "  Story.odm: [{sound: calm, qbit: 120060}, {sound: storm, until_qbit: 120071}, {sound: ash}]\n"
        "musicAreas:\n"
        "  story.odm:\n"
        "    - {track: 11, rect: [-100, -100, 100, 100], qbit: 120060}\n"
        "    - {track: 12, rect: [0, 0, 50, 50], until_qbit: 120057}\n"
        "    - {track: 13, rect: [0, 0, 50, 50]}\n");
    writeTextFile(assetRoot / "worlds" / "nosound" / "world.yml", "id: nosound\nambience:\n  a.odm: [{qbit: 5}]\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        std::string error;
        const std::optional<OpenYAMM::Game::WorldManifest> story =
            OpenYAMM::Game::loadWorldManifest(assetFileSystem, "worlds/story/world.yml", "story", error);
        REQUIRE(story.has_value());
        REQUIRE_EQ(story->ambience.at("plain.odm").size(), 1u);
        CHECK_EQ(story->ambience.at("plain.odm")[0].sound, "wind");
        CHECK_EQ(story->ambience.at("plain.odm")[0].qbit, 0u);
        const std::vector<OpenYAMM::Game::WorldManifest::AmbienceChoice> &choices = story->ambience.at("story.odm");
        REQUIRE_EQ(choices.size(), 3u);
        CHECK_EQ(choices[0].sound, "calm");
        CHECK_EQ(choices[0].qbit, 120060u);
        CHECK_EQ(choices[1].untilQBit, 120071u);
        CHECK_EQ(choices[2].sound, "ash");
        const std::vector<OpenYAMM::Game::WorldManifest::MusicArea> &areas = story->musicAreas.at("story.odm");
        REQUIRE_EQ(areas.size(), 3u);
        CHECK_EQ(areas[0].qbit, 120060u);
        CHECK_EQ(areas[1].untilQBit, 120057u);
        CHECK_EQ(areas[2].qbit, 0u);
        CHECK_EQ(areas[2].untilQBit, 0u);
        CHECK_FALSE(OpenYAMM::Game::loadWorldManifest(assetFileSystem, "worlds/nosound/world.yml", "nosound", error)
            .has_value());
        CHECK(error.find("ambience choices need a sound") != std::string::npos);
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

TEST_CASE("map-keyed table contributions add only the world's own new maps")
{
    const std::vector<std::vector<std::string>> baseRows = {
        {"Key map", "Up", "Side"},
        {"7out02.odm", "7out04.odm", "down"},
    };

    OpenYAMM::Game::MapKeyedTableContributionRows xeen = {};
    xeen.packageId = "xeen";
    xeen.mapFileNames = {"xeen_x1.odm", "xeen_x2.odm"};
    xeen.rows = {
        {"Key map", "Up", "Side"},
        {"Xeen_X1.odm", "xeen_x2.odm", "down"},
    };

    std::vector<std::vector<std::string>> composedRows;
    std::string error;
    REQUIRE(OpenYAMM::Game::composeMapKeyedAppendTableRows(baseRows, {xeen}, 0, composedRows, error));
    REQUIRE_EQ(composedRows.size(), 3);
    CHECK_EQ(composedRows.back()[0], "Xeen_X1.odm");

    OpenYAMM::Game::MapKeyedTableContributionRows foreign = xeen;
    foreign.rows = {{"7out02.odm", "xeen_x1.odm", "up"}};
    CHECK_FALSE(OpenYAMM::Game::composeMapKeyedAppendTableRows(baseRows, {foreign}, 0, composedRows, error));
    CHECK(error.find("not a map of package") != std::string::npos);

    OpenYAMM::Game::MapKeyedTableContributionRows repeated = xeen;
    repeated.rows.push_back({"xeen_x1.odm", "xeen_x2.odm", "left"});
    CHECK_FALSE(OpenYAMM::Game::composeMapKeyedAppendTableRows(baseRows, {repeated}, 0, composedRows, error));
    CHECK(error.find("already has a row") != std::string::npos);
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

TEST_CASE("a world's own continents show their continent_settings loading pages")
{
    const auto continentRow = [](const std::string &id, const std::string &pictures)
    {
        return std::vector<std::string>{id, "Note", "", "", "", "", "x", "0.9", "1.0", "losegame", "", "x1.odm", "0",
            "0", "0", "0", "x1.odm", "0", "0", "0", "0", "sky", pictures};
    };
    OpenYAMM::Game::MergedContinentSettingTable continents;
    REQUIRE(continents.loadFromRows({{"#"}, continentRow("2", "7load1.pcx,7load2.pcx"),
        continentRow("6", "xeenloadc1,xeenloadc2"), continentRow("7", "xeenloadd1.pcx"), continentRow("8", "")}));

    OpenYAMM::Game::WorldManifest world;
    world.loadingScreens = {"worldpage"};
    // No continent range: the world's own list, whatever the map's continent.
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 2u) == std::vector<std::string>{"worldpage"});

    world.idRanges.push_back({"continents", 6, 8});
    world.mapLoadingScreens.emplace("castle.blv", "castle_page");
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 6u, "castle.blv")
        == std::vector<std::string>{"castle_page"});
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 6u, "castle.blv", false)
        == std::vector<std::string>{"castle_page"});
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 6u, "other.blv", false).empty());
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 6u, "other.blv")
        == std::vector<std::string>{"xeenloadc1", "xeenloadc2"});
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 6u)
        == std::vector<std::string>{"xeenloadc1", "xeenloadc2"});
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 7u) == std::vector<std::string>{"xeenloadd1"});
    // A continent of the world that names no pages, or a continent outside the world (an engine one), or none.
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 8u) == std::vector<std::string>{"worldpage"});
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 2u) == std::vector<std::string>{"worldpage"});
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, 0u) == std::vector<std::string>{"worldpage"});
    // The map is not known yet: any of the world's continents' pages.
    CHECK(OpenYAMM::Game::worldLoadingPages(world, continents, std::nullopt)
        == std::vector<std::string>{"xeenloadc1", "xeenloadc2", "xeenloadd1"});
}

TEST_CASE("a world's edge spans send one map edge to two maps, by where the party meets it")
{
    using OpenYAMM::Game::MapBoundaryEdge;
    using OpenYAMM::Game::MapEdgeTransition;
    const auto mapRow = [](const std::string &id, const std::string &file, const std::string &world)
    {
        return std::vector<std::string>{id, "Map " + id, file, "0", "0", "0", "672", "0", "1", "0", "0", "0", "10",
            "0", "100", "0", "", "", "1", " 2-5", "", "", "1", " 1-3", "", "", "1", " 1-3", "4", "FOREST", "", "", "",
            "", world};
    };
    OpenYAMM::Game::MapStats maps;
    REQUIRE(maps.loadFromRows({{"#"}, mapRow("1", "out01.odm", "mm7"), mapRow("9102", "xeen_x2.odm", "xeen"),
        mapRow("9103", "xeen_x3.odm", "xeen"), mapRow("9104", "xeen_x4.odm", "xeen")}));
    std::string error;
    REQUIRE(maps.applyEdgeSpans("xeen",
        "edge_spans:\n"
        "  - {map: xeen_x4.odm, edge: south, from: -32768, to: 0, to_map: xeen_x3.odm, side: up, days: 5,"
        " at: [-7168, 22016, 1120], facing: 1536}\n"
        "  - {map: xeen_x4.odm, edge: south, from: 0, to: 32768, to_map: XEEN_X2.ODM, side: up, days: 5}\n",
        error));

    const OpenYAMM::Game::MapStatsEntry &x4 = *maps.findByFileName("xeen_x4.odm");
    uint32_t sourceId = 99;
    // West of x 0: X3, at its own arrival, facing 270 degrees (1536 of 2048).
    const std::optional<MapEdgeTransition> *pWest = x4.edgeTransitionAt(MapBoundaryEdge::South, -100.0f, 22000.0f,
        sourceId);
    REQUIRE(pWest != nullptr);
    REQUIRE(pWest->has_value());
    CHECK((*pWest)->destinationMapFileName == "xeen_x3.odm");
    CHECK_FALSE((*pWest)->useMapStartPosition);
    CHECK((*pWest)->arrivalX == -7168);
    CHECK((*pWest)->arrivalY == 22016);
    CHECK((*pWest)->arrivalZ == 1120);
    CHECK((*pWest)->directionDegrees == 270);
    CHECK((*pWest)->travelDays == 5);
    CHECK(sourceId == 5u);
    CHECK(x4.mapTransitionAtSource(sourceId) == pWest);
    CHECK(OpenYAMM::Game::mapTransitionSourceEdge(sourceId) == MapBoundaryEdge::South);

    // East of it: X2 (its file as map_stats spells it), at its north start.
    const std::optional<MapEdgeTransition> *pEast = x4.edgeTransitionAt(MapBoundaryEdge::South, 0.0f, 22000.0f,
        sourceId);
    REQUIRE(pEast != nullptr);
    REQUIRE(pEast->has_value());
    CHECK((*pEast)->destinationMapFileName == "xeen_x2.odm");
    CHECK((*pEast)->useMapStartPosition);
    CHECK((*pEast)->arrivalSide == MapBoundaryEdge::North);
    CHECK_FALSE((*pEast)->directionDegrees.has_value());
    CHECK(sourceId == 9u);
    CHECK(x4.mapTransitionAtSource(9u) == pEast);

    // An edge without spans is the edge's own way; source ids naming no span name nothing.
    CHECK(x4.edgeTransitionAt(MapBoundaryEdge::North, 0.0f, -22000.0f, sourceId) == &x4.northTransition);
    CHECK(sourceId == 0u);
    CHECK(x4.mapTransitionAtSource(1u) == &x4.southTransition);
    CHECK(x4.mapTransitionAtSource(13u) == nullptr);
    CHECK(x4.mapTransitionAtSource(6u) == nullptr);

    // Refused: another world's map, overlapping spans, an unknown destination, no arrival at all.
    CHECK_FALSE(maps.applyEdgeSpans("xeen",
        "edge_spans: [{map: out01.odm, edge: west, from: 0, to: 10, to_map: xeen_x2.odm, side: up}]", error));
    CHECK(error.find("not a map of world xeen") != std::string::npos);
    CHECK_FALSE(maps.applyEdgeSpans("xeen",
        "edge_spans: [{map: xeen_x4.odm, edge: south, from: -10, to: 10, to_map: xeen_x2.odm, side: up}]", error));
    CHECK(error.find("overlap") != std::string::npos);
    CHECK_FALSE(maps.applyEdgeSpans("xeen",
        "edge_spans: [{map: xeen_x3.odm, edge: north, from: 0, to: 10, to_map: xeen_x9.odm, side: down}]", error));
    CHECK(error.find("no known map") != std::string::npos);
    CHECK_FALSE(maps.applyEdgeSpans("xeen",
        "edge_spans: [{map: xeen_x3.odm, edge: north, from: 0, to: 10, to_map: xeen_x4.odm}]", error));
    CHECK(error.find("neither at nor a side") != std::string::npos);
}
