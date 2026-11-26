#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/scene/IndoorSceneRuntime.h"

#include <array>
#include <cmath>
#include <filesystem>
#include <utility>

using namespace OpenYAMM::Game;

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

TEST_CASE("a broken destructible drops the party, the monsters and the items standing on it")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm9"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "verhoffinruins.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();
    delta->spriteObjects.clear();

    const MonsterTable::MonsterStatsEntry *pStats = nullptr;
    uint16_t monsterId = 1;

    for (; monsterId < 700 && (pStats == nullptr || pStats->canFly); ++monsterId)
    {
        pStats = data.getMonsterTable().findStatsById(monsterId);
    }

    REQUIRE(pStats != nullptr);
    --monsterId;

    // Destructible 598 (BreakOut0) is a ceiling slab whose top lies at z 164 in sector 4, over a room whose floor
    // lies at z -328 (KingKong.scr's busts wait on it). A monster that never moved yet, a resting item and the party.
    constexpr float SlabTopZ = 164.0f;
    constexpr float RoomFloorZ = -328.0f;
    MapDeltaActor actor = {};
    actor.monsterId = actor.monsterInfoId = monsterId;
    actor.hp = pStats->hitPoints;
    actor.x = -3080;
    actor.y = -5300;
    actor.z = static_cast<int>(SlabTopZ);
    actor.sectorId = 4;
    actor.radius = 32;
    actor.height = 128;
    delta->actors.push_back(actor);
    MapDeltaSpriteObject loot = {};
    loot.spriteId = 373;
    loot.objectDescriptionId = 373;
    loot.x = -3300;
    loot.y = -5300;
    loot.z = static_cast<int>(SlabTopZ) + 1;
    loot.sectorId = 4;
    delta->spriteObjects.push_back(loot);

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, &actorService, nullptr);
    IndoorWorldRuntime &world = scene.worldRuntime();
    IndoorPartyRuntime &partyRuntime = scene.partyRuntime();
    partyRuntime.teleportPartyPosition(-3220.0f, -5420.0f, SlabTopZ);

    for (int frame = 0; frame < 30; ++frame)
    {
        partyRuntime.update(0.0f, 0.0f, false, false, 1.0f / 60.0f);
        scene.advanceSimulation(1000.0f / 60.0f);
    }

    REQUIRE(partyRuntime.movementState().grounded);
    REQUIRE_EQ(partyRuntime.movementState().footZ, doctest::Approx(SlabTopZ).epsilon(0.001));
    MapDeltaData *pDelta = world.mapDeltaData();
    REQUIRE(pDelta != nullptr);
    REQUIRE_EQ(pDelta->spriteObjects.size(), 1u);
    REQUIRE_EQ(pDelta->spriteObjects[0].z, static_cast<int>(SlabTopZ) + 1);
    REQUIRE(world.mapActorAiState(0) != nullptr);
    REQUIRE(world.mapActorAiState(0)->grounded);

    REQUIRE(world.destroyDestructible(598));

    for (int frame = 0; frame < 3 * 60; ++frame)
    {
        partyRuntime.update(0.0f, 0.0f, false, false, 1.0f / 60.0f);
        scene.advanceSimulation(1000.0f / 60.0f);
        world.updateActorAi(1.0f / 60.0f);
        world.updateWorld(1.0f / 60.0f);
    }

    CHECK(partyRuntime.movementState().grounded);
    CHECK_EQ(partyRuntime.movementState().footZ, doctest::Approx(RoomFloorZ).epsilon(0.01));
    CHECK_EQ(pDelta->spriteObjects[0].z, doctest::Approx(RoomFloorZ + 1.0f).epsilon(0.01));
    CHECK_EQ(world.mapActorAiState(0)->preciseZ, doctest::Approx(RoomFloorZ).epsilon(0.01));
}
