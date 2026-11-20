#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/maps/SaveGame.h"
#include "game/scene/IndoorSceneRuntime.h"

#include <array>
#include <cmath>
#include <filesystem>
#include <utility>

using namespace OpenYAMM::Game;

TEST_CASE("legacy Snake Temple saves keep the rear lift wall closed throughout its travel")
{
    MapDeltaDoor door;
    door.doorId = 3;
    door.directionZ = -65536;
    door.moveLength = 696;
    door.state = 1;
    door.timeSinceTriggered = 1234;
    door.numVertices = door.numOffsets = 6;
    door.vertexIds = {848, 844, 853, 845, 857, 847};
    door.xOffsets = {-1152, -1280, -1028, -1280, -1280, -1028};
    door.yOffsets = {1152, 1152, 1408, 1280, 1408, 1152};
    door.zOffsets = {700, 700, 700, 700, 700, 700};
    IndoorSceneRuntime::Snapshot snapshot;
    snapshot.mapDeltaData.emplace();
    snapshot.mapDeltaData->doors.push_back(door);
    GameSaveData save;
    save.mapFileName = "mm6:6t8.blv";
    save.hasIndoorSceneState = true;
    save.indoorScene = snapshot;
    save.indoorSceneStates["6t8.blv"] = snapshot;
    save.indoorSceneStates["mm6:6t8.blv"] = snapshot;
    save.indoorSceneStates["mm7:6t8.blv"] = snapshot;

    migrateLegacySnakeTempleLift(save);
    migrateLegacySnakeTempleLift(save);
    const auto checkLift = [](const IndoorSceneRuntime::Snapshot &state)
    {
        REQUIRE(state.mapDeltaData);
        const MapDeltaDoor &lift = state.mapDeltaData->doors.front();
        REQUIRE_EQ(lift.vertexIds.size(), 7u);
        CHECK_EQ(lift.numVertices, 7);
        CHECK_EQ(lift.numOffsets, 7);
        CHECK_EQ(lift.state, 1);
        CHECK_EQ(lift.timeSinceTriggered, 1234u);
        CHECK_EQ(state.mapDeltaData->doorsData.size(), 28u);
        for (const float distance : {0.0f, 174.0f, 348.0f, 522.0f, 696.0f})
        {
            std::vector<IndoorVertex> vertices(858);
            vertices[821] = {-1152, 1408, 700};
            applyIndoorMechanismDoorToVertices(lift, distance, vertices);
            CHECK_EQ(vertices[821].z, vertices[853].z);
            CHECK_EQ(vertices[821].z, vertices[857].z);
            CHECK_EQ(vertices[821].z, 700 - int(distance));
        }
    };
    checkLift(save.indoorScene);
    checkLift(save.indoorSceneStates.at("6t8.blv"));
    checkLift(save.indoorSceneStates.at("mm6:6t8.blv"));
    CHECK_EQ(save.indoorSceneStates.at("mm7:6t8.blv").mapDeltaData->doors.front().vertexIds.size(), 6u);
}

TEST_CASE("Tsantsa pit floor carries the monsters standing on it and resting loot")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "6t3.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();

    const MonsterTable::MonsterStatsEntry *pStats = nullptr;
    uint16_t monsterId = 1;

    for (; monsterId < 700 && (pStats == nullptr || pStats->canFly); ++monsterId)
    {
        pStats = data.getMonsterTable().findStatsById(monsterId);
    }

    REQUIRE(pStats != nullptr);
    --monsterId;

    // Pit floor face 2755 of door 19 spans x 1920..2176, y -384..-72 at z -496 and rises 496 units.
    constexpr int PitFloorZ = -496;
    const std::array<std::pair<int, int>, 2> actorPositions = {{{1990, -300}, {2110, -150}}};

    for (const std::pair<int, int> &position : actorPositions)
    {
        MapDeltaActor actor = {};
        actor.monsterId = actor.monsterInfoId = monsterId;
        actor.hp = pStats->hitPoints;
        actor.x = position.first;
        actor.y = position.second;
        actor.z = PitFloorZ;
        actor.sectorId = 13;
        actor.radius = 32;
        actor.height = 128;
        delta->actors.push_back(actor);
    }

    MapDeltaSpriteObject loot = {};
    loot.spriteId = 373;
    loot.objectDescriptionId = 373;
    loot.x = 2050;
    loot.y = -220;
    loot.z = PitFloorZ + 1;
    loot.sectorId = 13;
    delta->spriteObjects.push_back(loot);
    const size_t lootIndex = delta->spriteObjects.size() - 1;

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, &actorService, nullptr);
    IndoorWorldRuntime &world = scene.worldRuntime();
    REQUIRE_EQ(world.mapActorCount(), 2u);

    MapDeltaData *pDelta = world.mapDeltaData();
    REQUIRE(pDelta != nullptr);
    const MapDeltaDoor *pDoor = nullptr;

    for (const MapDeltaDoor &door : pDelta->doors)
    {
        if (door.doorId == 19)
        {
            pDoor = &door;
        }
    }

    REQUIRE(pDoor != nullptr);
    EventRuntimeState *pEventState = world.eventRuntimeState();
    REQUIRE(pEventState != nullptr);
    EventRuntime::applyMechanismAction(pEventState->mechanisms[19], pDoor, MechanismAction::Trigger);

    // Monsters that never moved since loading have no support face; ones running AI find theirs as they act.
    bool runActorAi = false;
    SUBCASE("monsters placed on the floor")
    {
        runActorAi = false;
    }
    SUBCASE("monsters acting while the floor rises")
    {
        runActorAi = true;
    }

    for (int step = 0; step < 8 * 60; ++step)
    {
        scene.advanceSimulation(1000.0f / 60.0f);

        if (runActorAi)
        {
            world.updateActorAi(1.0f / 60.0f);
        }
    }

    // Door 19 rises its full 496 units, to the level of the surrounding floor.
    constexpr float RaisedPitFloorZ = PitFloorZ + 496.0f;
    CHECK_EQ(pDelta->spriteObjects[lootIndex].z, static_cast<int>(RaisedPitFloorZ) + 1);

    for (size_t actorIndex = 0; actorIndex < 2; ++actorIndex)
    {
        CAPTURE(actorIndex);
        CHECK_EQ(world.mapActorAiState(actorIndex)->preciseZ, doctest::Approx(RaisedPitFloorZ).epsilon(0.001));
    }
}

TEST_CASE("indoor mechanisms advance without the world simulation (turn-based)")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "6t3.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, &actorService, nullptr);
    IndoorWorldRuntime &world = scene.worldRuntime();
    MapDeltaData *pDelta = world.mapDeltaData();
    REQUIRE(pDelta != nullptr);
    const MapDeltaDoor *pDoor = nullptr;

    for (const MapDeltaDoor &door : pDelta->doors)
    {
        if (door.doorId == 19)
        {
            pDoor = &door;
        }
    }

    REQUIRE(pDoor != nullptr);
    EventRuntimeState *pEventState = world.eventRuntimeState();
    REQUIRE(pEventState != nullptr);
    EventRuntime::applyMechanismAction(pEventState->mechanisms[19], pDoor, MechanismAction::Trigger);
    const float initialDistance = pEventState->mechanisms[19].currentDistance;
    const float initialGameMinutes = world.gameMinutes();

    CHECK(scene.advanceMechanisms(1000.0f / 60.0f));

    for (int step = 1; step < 8 * 60; ++step)
    {
        scene.advanceMechanisms(1000.0f / 60.0f);
    }

    // Door 19 travels its full 496 units while game time stays frozen.
    CHECK_EQ(std::abs(pEventState->mechanisms[19].currentDistance - initialDistance), doctest::Approx(496.0f));
    CHECK_FALSE(pEventState->mechanisms[19].isMoving);
    CHECK_EQ(world.gameMinutes(), doctest::Approx(initialGameMinutes));
    CHECK_FALSE(scene.advanceMechanisms(1000.0f / 60.0f));
}

TEST_CASE("Tsantsa safe path keeps the party on the tile under its centre near a trap tile")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "6t3.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, &actorService, nullptr);

    // Safe face 2628 (x 3904..4032) meets trap face 2638 (x 4032..4096) on the flat floor at z -256.
    constexpr size_t SafeFaceIndex = 2628;
    constexpr size_t TrapFaceIndex = 2638;
    constexpr float TileSeamX = 4032.0f;
    IndoorPartyRuntime &partyRuntime = scene.partyRuntime();
    partyRuntime.teleportPartyPosition(3960.0f, -480.0f, -256.0f);

    for (int frame = 0; frame < 30; ++frame)
    {
        partyRuntime.update(0.0f, 0.0f, false, false, 1.0f / 60.0f);
        scene.advanceSimulation(1000.0f / 60.0f);
    }

    REQUIRE(partyRuntime.movementState().grounded);
    REQUIRE_EQ(partyRuntime.movementState().supportFaceIndex, SafeFaceIndex);

    // Walk toward the seam: within a body radius of it the leading probe is over the trap tile.
    bool reachedTrap = false;

    for (int frame = 0; frame < 120 && !reachedTrap; ++frame)
    {
        partyRuntime.update(120.0f, 0.0f, false, false, 1.0f / 60.0f);
        scene.advanceSimulation(1000.0f / 60.0f);
        const IndoorMoveState &state = partyRuntime.movementState();

        if (state.x < TileSeamX - 1.0f)
        {
            CAPTURE(state.x);
            CHECK_EQ(state.supportFaceIndex, SafeFaceIndex);
        }
        else if (state.x > TileSeamX + 1.0f)
        {
            reachedTrap = state.supportFaceIndex == TrapFaceIndex;
        }
    }

    CHECK(reachedTrap);
}
