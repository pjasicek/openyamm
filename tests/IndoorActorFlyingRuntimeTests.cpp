#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/scene/IndoorSceneRuntime.h"

#include <array>
#include <filesystem>

using namespace OpenYAMM::Game;

TEST_CASE("a lone flying devil can rise through the Hive pit portal to the party")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "hive.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();

    const MonsterTable::MonsterStatsEntry *pStats = data.getMonsterTable().findStatsById(501);
    REQUIRE(pStats != nullptr);
    MapDeltaActor devil = {};
    devil.monsterId = devil.monsterInfoId = 501;
    devil.hp = pStats->hitPoints;
    devil.x = 754;
    devil.y = 7241;
    devil.z = -400;
    devil.sectorId = 4;
    devil.radius = 73;
    devil.height = 225;
    devil.hostilityType = 4;
    devil.attributes = uint32_t(EvtActorAttribute::Aggressor) | uint32_t(EvtActorAttribute::Nearby);
    delta->actors.push_back(devil);

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, &actorService, nullptr);
    scene.partyRuntime().teleportPartyPosition(712.484f, 7147.493f, 0);
    const IndoorWorldRuntime &world = scene.worldRuntime();
    REQUIRE_EQ(world.mapActorCount(), 1u);
    REQUIRE(world.mapActorAiState(0)->canFly);
    REQUIRE_LT(world.mapActorAiState(0)->preciseZ, -330);

    // With nobody to collide with, the actor must climb past the former false ceiling at about Z=-330.
    for (int step = 0; step < 3 * 128; ++step)
    {
        scene.advanceSimulation(1000.0f / 128);
        scene.worldRuntime().updateActorAi(1.0f / 128);
    }
    CHECK(world.mapActorAiState(0)->hasDetectedParty);
    CHECK_GT(world.mapActorAiState(0)->preciseZ, -100);
}

TEST_CASE("evt.SetMapActorPosition indoors stands a walker at the point and makes it its home")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "hive.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();

    int16_t walkerId = 0;
    for (int16_t id = 1; id < 300 && walkerId == 0; ++id)
    {
        const MonsterTable::MonsterStatsEntry *pStats = data.getMonsterTable().findStatsById(id);
        if (pStats != nullptr && !pStats->canFly && pStats->hitPoints > 0)
        {
            walkerId = id;
        }
    }
    REQUIRE_GT(walkerId, 0);
    MapDeltaActor walker = {};
    walker.monsterId = walker.monsterInfoId = walkerId;
    walker.hp = data.getMonsterTable().findStatsById(walkerId)->hitPoints;
    walker.x = 754;
    walker.y = 7241;
    walker.z = -400;
    walker.sectorId = 4;
    walker.radius = 32;
    walker.height = 128;
    delta->actors.push_back(walker);

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, &actorService, nullptr);
    IndoorWorldRuntime &world = scene.worldRuntime();
    REQUIRE_EQ(world.mapActorCount(), 1u);
    const float startX = world.mapActorAiState(0)->preciseX;
    const float startY = world.mapActorAiState(0)->preciseY;
    const float floorZ = world.mapActorAiState(0)->preciseZ;

    CHECK_FALSE(world.setMapActorPosition(1, startX, startY, floorZ));
    CHECK_FALSE(world.setMapActorPosition(0, 1.0e6f, 1.0e6f, floorZ));

    bool moved = false;
    const std::array<std::array<float, 2>, 4> offsets = {{{64.0f, 0.0f}, {-64.0f, 0.0f}, {0.0f, 64.0f}, {0.0f, -64.0f}}};
    for (const std::array<float, 2> &offset : offsets)
    {
        if (world.setMapActorPosition(0, startX + offset[0], startY + offset[1], floorZ))
        {
            moved = true;
            const auto &state = *world.mapActorAiState(0);
            CHECK(state.preciseX == doctest::Approx(startX + offset[0]));
            CHECK(state.preciseY == doctest::Approx(startY + offset[1]));
            CHECK(state.homePreciseX == doctest::Approx(state.preciseX));
            CHECK(state.homePreciseY == doctest::Approx(state.preciseY));
            float x = 0, y = 0, z = 0;
            REQUIRE(world.mapActorPosition(0, x, y, z));
            CHECK(x == doctest::Approx(startX + offset[0]));
            break;
        }
    }
    CHECK(moved);
}
