#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/FaceEnums.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/scene/IndoorSceneRuntime.h"

#include <array>
#include <filesystem>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
struct GoblinwatchDetectionFixture
{
    // Outlives the loader: the map load parses the sprite frame table on a worker that reads these assets.
    OpenYAMM::Engine::AssetFileSystem assets;
    GameDataLoader data;
    IndoorMapData map;
    Party party;
    GameplayActorService actorService;
    std::unique_ptr<IndoorSceneRuntime> pScene;

    GoblinwatchDetectionFixture(int actorX = -640, int actorY = 3456)
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
        REQUIRE(data.loadForHeadlessGameplay(assets));
        REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "6d01.blv"));
        const MapAssetInfo &loaded = *data.getSelectedMap();
        map = *loaded.indoorMapData;
        map.spawns.clear();
        std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
        REQUIRE(delta);
        delta->actors.clear();
        const MonsterTable::MonsterStatsEntry *pStats = data.getMonsterTable().findStatsById(550);
        REQUIRE(pStats != nullptr);
        MapDeltaActor actor = {};
        actor.monsterId = actor.monsterInfoId = 550;
        actor.hp = pStats->hitPoints;
        actor.x = actorX;
        actor.y = actorY;
        actor.sectorId = 4;
        actor.radius = 56;
        actor.height = 145;
        actor.hostilityType = 4;
        actor.attributes = uint32_t(EvtActorAttribute::Aggressor);
        delta->actors.push_back(actor);
        party.setItemTable(&data.getItemTable());
        actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
        pScene = std::make_unique<IndoorSceneRuntime>(loaded.map.fileName, loaded.map, map,
            data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
            data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
            loaded.localEventProgram, std::nullopt, &actorService, nullptr);
        pScene->partyRuntime().teleportPartyPosition(565.634f, 6210.096f, 0);
        REQUIRE_EQ(pScene->worldRuntime().mapActorCount(), 1u);
        REQUIRE_FALSE(pScene->worldRuntime().mapActorAiState(0)->hasDetectedParty);
    }

    void advance(float seconds)
    {
        for (int step = 0; step < int(seconds * 128); ++step)
        {
            pScene->advanceSimulation(1000.0f / 128);
            pScene->worldRuntime().updateActorAi(1.0f / 128);
        }
    }

    void checkUnseen() const
    {
        const IndoorWorldRuntime &world = pScene->worldRuntime();
        CHECK_FALSE(world.mapActorAiState(0)->hasDetectedParty);
        CHECK_EQ(world.mapDeltaData()->actors[0].attributes & uint32_t(EvtActorAttribute::Nearby), 0u);
    }
};

struct DetectionWall
{
    int x = -512;
    int minY = -512;
    int maxY = 512;
    int topZ = 512;
};

struct SectorDetectionFixture
{
    // Outlives the loader, as in the Goblinwatch fixture.
    OpenYAMM::Engine::AssetFileSystem assets;
    GameDataLoader data;
    IndoorMapData map;
    Party party;
    GameplayActorService actorService;
    std::unique_ptr<IndoorSceneRuntime> pScene;

    // Three sectors in a row along X, joined by full-height portals at X=0 and X=2048: [-8192,0], [0,2048] and
    // [2048,4096]. Each wall is an opaque full-height face in sector 1. Actors stand in sector 1.
    SectorDetectionFixture(int partyX, const std::vector<DetectionWall> &walls,
        const std::vector<std::array<int, 2>> &actorPositions, bool neighbourWakes = true)
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
        REQUIRE(data.loadForHeadlessGameplay(assets));

        map.sectors.resize(4);
        const std::array<int, 4> boundaries = {-8192, 0, 2048, 4096};
        for (uint16_t sectorId = 1; sectorId < 4; ++sectorId)
        {
            const int minX = boundaries[sectorId - 1];
            const int maxX = boundaries[sectorId];
            IndoorSector &sector = map.sectors[sectorId];
            sector.minX = minX;
            sector.maxX = maxX;
            sector.minY = -512;
            sector.maxY = 512;
            sector.minZ = 0;
            sector.maxZ = 512;
            addFace({{minX, -512, 0}, {maxX, -512, 0}, {maxX, 512, 0}, {minX, 512, 0}}, 3, sectorId);
            addFace({{minX, 512, 512}, {maxX, 512, 512}, {maxX, -512, 512}, {minX, -512, 512}}, 5, sectorId);
            if (sectorId < 3)
            {
                addFace({{maxX, -512, 0}, {maxX, -512, 512}, {maxX, 512, 512}, {maxX, 512, 0}},
                    1, sectorId, sectorId + 1);
            }
        }
        for (const DetectionWall &wall : walls)
        {
            addFace({{wall.x, wall.minY, 0}, {wall.x, wall.minY, wall.topZ}, {wall.x, wall.maxY, wall.topZ},
                {wall.x, wall.maxY, 0}}, 1, 1);
        }

        std::optional<MapDeltaData> delta = MapDeltaData{};
        for (const std::array<int, 2> &position : actorPositions)
        {
            delta->actors.push_back(goblin(position[0], position[1], 0, 1));
        }
        map.actorNeighbourWakes = neighbourWakes;
        createScene(delta);
        pScene->partyRuntime().teleportPartyPosition(partyX, 0, 0);
        for (size_t actorIndex = 0; actorIndex < actorPositions.size(); ++actorIndex)
        {
            REQUIRE_EQ(pScene->worldRuntime().mapActorAiState(actorIndex)->sectorId, 1);
            REQUIRE_FALSE(pScene->worldRuntime().mapActorAiState(actorIndex)->hasDetectedParty);
        }
    }

    // Two rooms stacked without a portal between them: the party's room below a ceiling at upperFloorZ - 16,
    // and one actor in the room above, standing 200 units to the side of the party.
    explicit SectorDetectionFixture(int upperFloorZ)
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
        REQUIRE(data.loadForHeadlessGameplay(assets));

        map.sectors.resize(3);
        const std::array<std::array<int, 2>, 3> heights = {{{0, 0}, {0, upperFloorZ - 16}, {upperFloorZ, 1024}}};
        for (uint16_t sectorId = 1; sectorId < 3; ++sectorId)
        {
            const int floorZ = heights[sectorId][0];
            const int ceilingZ = heights[sectorId][1];
            IndoorSector &sector = map.sectors[sectorId];
            sector.minX = -1024;
            sector.maxX = 1024;
            sector.minY = -512;
            sector.maxY = 512;
            sector.minZ = floorZ;
            sector.maxZ = ceilingZ;
            addFace({{-1024, -512, floorZ}, {1024, -512, floorZ}, {1024, 512, floorZ}, {-1024, 512, floorZ}},
                3, sectorId);
            addFace({{-1024, 512, ceilingZ}, {1024, 512, ceilingZ}, {1024, -512, ceilingZ},
                {-1024, -512, ceilingZ}}, 5, sectorId);
        }

        std::optional<MapDeltaData> delta = MapDeltaData{};
        delta->actors.push_back(goblin(200, 0, upperFloorZ, 2));
        createScene(delta);
        pScene->partyRuntime().teleportPartyPosition(0, 0, 0);
        REQUIRE_EQ(pScene->partyRuntime().movementState().sectorId, 1);
        REQUIRE_EQ(pScene->worldRuntime().mapActorAiState(0)->sectorId, 2);
        REQUIRE_FALSE(pScene->worldRuntime().mapActorAiState(0)->hasDetectedParty);
    }

    void advance(float seconds)
    {
        for (int step = 0; step < int(seconds * 128); ++step)
        {
            pScene->worldRuntime().updateActorAi(1.0f / 128);
        }
    }

    bool detected(size_t actorIndex) const
    {
        const IndoorWorldRuntime &world = pScene->worldRuntime();
        const bool nearby =
            (world.mapDeltaData()->actors[actorIndex].attributes & uint32_t(EvtActorAttribute::Nearby)) != 0;
        CHECK_EQ(world.mapActorAiState(actorIndex)->hasDetectedParty, nearby);
        return world.mapActorAiState(actorIndex)->hasDetectedParty;
    }

private:
    void addFace(std::initializer_list<IndoorVertex> vertices, uint8_t type, uint16_t sectorId,
        uint16_t backSectorId = 0)
    {
        IndoorFace face = {};
        face.facetType = type;
        face.roomNumber = sectorId;
        face.roomBehindNumber = backSectorId;
        face.isPortal = backSectorId != 0;
        face.attributes = face.isPortal ? faceAttributeBit(FaceAttribute::IsPortal) : 0;
        for (const IndoorVertex &vertex : vertices)
        {
            face.vertexIndices.push_back(uint16_t(map.vertices.size()));
            map.vertices.push_back(vertex);
        }
        const uint16_t faceId = uint16_t(map.faces.size());
        map.faces.push_back(std::move(face));
        IndoorSector &sector = map.sectors[sectorId];
        sector.faceIds.push_back(faceId);
        if (backSectorId != 0)
        {
            sector.portalFaceIds.push_back(faceId);
            map.sectors[backSectorId].portalFaceIds.push_back(faceId);
            map.sectors[backSectorId].faceIds.push_back(faceId);
        }
        else if (type == 3)
        {
            sector.floorFaceIds.push_back(faceId);
        }
        else if (type == 5)
        {
            sector.ceilingFaceIds.push_back(faceId);
        }
        else
        {
            sector.wallFaceIds.push_back(faceId);
        }
    }

    MapDeltaActor goblin(int x, int y, int z, int16_t sectorId) const
    {
        const MonsterTable::MonsterStatsEntry *pStats = data.getMonsterTable().findStatsById(550);
        REQUIRE(pStats != nullptr);
        MapDeltaActor actor = {};
        actor.monsterId = actor.monsterInfoId = 550;
        actor.hp = pStats->hitPoints;
        actor.x = x;
        actor.y = y;
        actor.z = z;
        actor.sectorId = sectorId;
        actor.radius = 56;
        actor.height = 145;
        actor.hostilityType = 4;
        actor.attributes = uint32_t(EvtActorAttribute::Aggressor);
        return actor;
    }

    void createScene(std::optional<MapDeltaData> &delta)
    {
        MapStatsEntry mapStats = {};
        mapStats.fileName = "detection.blv";
        mapStats.worldId = "mm6";
        party.setItemTable(&data.getItemTable());
        actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
        pScene = std::make_unique<IndoorSceneRuntime>(mapStats.fileName, mapStats, map,
            data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
            data.getItemTable(), data.getChestTable(), party, delta, EventRuntimeState{},
            std::nullopt, std::nullopt, &actorService, nullptr);
    }
};
}

TEST_CASE("indoor detection needs sight, also within the same or a neighbouring sector")
{
    int partyX = -256;
    int16_t partySectorId = 1;
    SUBCASE("same sector")
    {
        partyX = -256;
        partySectorId = 1;
    }
    SUBCASE("one portal hop")
    {
        partyX = 1024;
        partySectorId = 2;
    }
    SectorDetectionFixture fixture(partyX, {DetectionWall{}}, {{-1024, 0}});
    IndoorSceneRuntime &scene = *fixture.pScene;
    REQUIRE_EQ(scene.partyRuntime().movementState().sectorId, partySectorId);
    REQUIRE_FALSE(scene.worldRuntime().hasIndoorCombatLineOfSight(
        {-1024, 0, 108.75f}, 1, {float(partyX), 0, 96}, partySectorId));

    fixture.advance(1);
    CHECK_FALSE(fixture.detected(0));
}

TEST_CASE("indoor detection sees the party over a low rim, eye to eye")
{
    // Castle of Air: air elementals across the fountain from the party, whose rim hides the ray from the monster's
    // chest (108.75) to the party's body (96) but not the one from its eyes (130.5) to the party's (160).
    int rimHeight = 128;
    bool seen = true;
    SUBCASE("rim below both pairs of eyes")
    {
        rimHeight = 128;
        seen = true;
    }
    SUBCASE("wall above the eye ray")
    {
        rimHeight = 200;
        seen = false;
    }
    SectorDetectionFixture fixture(-256, {DetectionWall{.x = -1024, .topZ = rimHeight}}, {{-2048, 0}});
    REQUIRE_FALSE(fixture.pScene->worldRuntime().hasIndoorCombatLineOfSight(
        {-2048, 0, 108.75f}, 1, {-256, 0, 96}, 1));

    fixture.advance(1);
    CHECK_EQ(fixture.detected(0), seen);
}

TEST_CASE("indoor detection sees across portals within one sight-check interval")
{
    bool blockingWall = true;
    SUBCASE("two portal hops with a wall")
    {
        blockingWall = true;
    }
    SUBCASE("two portal hops with a clear ray")
    {
        blockingWall = false;
    }
    SectorDetectionFixture fixture(3072, blockingWall ? std::vector<DetectionWall>{{}} : std::vector<DetectionWall>{},
        {{-1024, 0}});
    REQUIRE_EQ(fixture.pScene->partyRuntime().movementState().sectorId, 3);
    fixture.advance(16.0f / 128);
    CHECK_EQ(fixture.detected(0), !blockingWall);
}

TEST_CASE("indoor detection does not hear the party through a close wall")
{
    SectorDetectionFixture fixture(-400, {DetectionWall{}}, {{-600, 0}});
    REQUIRE_FALSE(fixture.pScene->worldRuntime().hasIndoorCombatLineOfSight(
        {-600, 0, 108.75f}, 1, {-400, 0, 96}, 1));
    fixture.advance(1);
    CHECK_FALSE(fixture.detected(0));
}

TEST_CASE("indoor detection does not reach through a ceiling to the room above")
{
    SectorDetectionFixture fixture(240);
    fixture.advance(1);
    CHECK_FALSE(fixture.detected(0));
}

TEST_CASE("indoor detection wakes the visible neighbours of the actor that noticed the party, without chaining")
{
    // Actor 0 sees the party through the portal. A wall at X=-512 (Y -512..-150) hides actors 1 and 2 from the
    // party; actor 1 is 430 units from actor 0 and in its view, and actor 2 is 814 units from actor 1 but beyond the
    // wake radius of actor 0.
    const std::vector<DetectionWall> walls = {{-512, -512, -150}};
    std::vector<std::array<int, 2>> actors = {{-400, 50}, {-650, -300}, {-1450, -450}};
    bool sightedActor = true;
    SUBCASE("an actor notices the party")
    {
        sightedActor = true;
    }
    SUBCASE("nobody notices the party")
    {
        sightedActor = false;
        actors[0] = {-1600, -400};
    }
    SectorDetectionFixture fixture(1024, walls, actors);
    fixture.advance(0.25f);
    CHECK_EQ(fixture.detected(0), sightedActor);
    CHECK_EQ(fixture.detected(1), sightedActor);
    CHECK_FALSE(fixture.detected(2));
}

TEST_CASE("indoor party damage wakes the struck actor's visible neighbours")
{
    // Every actor is hidden from the party by the wall. Actor 2 is beyond the wake radius of actor 0; actor 3 is
    // 856 units from it.
    SectorDetectionFixture fixture(
        1024, {{-512, -512, -150}}, {{-650, -300}, {-900, -450}, {-2300, -450}, {-1500, -400}});
    fixture.advance(0.25f);
    REQUIRE_FALSE(fixture.detected(0));
    REQUIRE_FALSE(fixture.detected(1));
    REQUIRE(fixture.pScene->worldRuntime().applyPartyAttackMeleeDamage(
        0, 1, {1024, 0, 96}, ShieldAttackTier::Physical));
    // The hit marks the struck actor at once; the next selection step records its Nearby flag.
    fixture.pScene->worldRuntime().updateActorAi(1.0f / 128);
    CHECK(fixture.detected(0));
    CHECK(fixture.detected(1));
    CHECK_FALSE(fixture.detected(2));
    CHECK(fixture.detected(3));
}

TEST_CASE("indoor wakes stay off on a map whose scene turns them off")
{
    // Scene `actor_detection: {wakes: none}` (MM9's outdoor regions): the struck actor alone notices the party.
    SectorDetectionFixture fixture(1024, {{-512, -512, -150}}, {{-650, -300}, {-900, -450}}, false);
    fixture.advance(0.25f);
    REQUIRE(fixture.pScene->worldRuntime().applyPartyAttackMeleeDamage(
        0, 1, {1024, 0, 96}, ShieldAttackTier::Physical));
    fixture.pScene->worldRuntime().updateActorAi(1.0f / 128);
    CHECK(fixture.detected(0));
    CHECK_FALSE(fixture.detected(1));
}

TEST_CASE("indoor wakes rouse every visible neighbour in range, without a count limit")
{
    std::vector<std::array<int, 2>> actors = {{-650, -300}};
    for (int index = 0; index < 8; ++index)
    {
        actors.push_back({-800 - index * 100, -350});
    }
    SectorDetectionFixture fixture(1024, {{-512, -512, -150}}, actors);
    fixture.advance(0.25f);
    REQUIRE_FALSE(fixture.detected(0));
    REQUIRE(fixture.pScene->worldRuntime().applyPartyAttackMeleeDamage(
        0, 1, {1024, 0, 96}, ShieldAttackTier::Physical));
    fixture.pScene->worldRuntime().updateActorAi(1.0f / 128);
    for (size_t actorIndex = 0; actorIndex < actors.size(); ++actorIndex)
    {
        CAPTURE(actorIndex);
        CHECK(fixture.detected(actorIndex));
    }
}

TEST_CASE("indoor detection stays blocked by walls along the Goblinwatch entrance walk")
{
    GoblinwatchDetectionFixture fixture;
    IndoorSceneRuntime &scene = *fixture.pScene;
    fixture.advance(1);
    fixture.checkUnseen();
    REQUIRE(scene.activateEvent(1, "face", 0));
    fixture.advance(3);
    fixture.checkUnseen();

    // The walk passes sector 3, whose portal leads to the goblin's sector 4, but walls block every ray.
    REQUIRE_EQ(scene.worldRuntime().mapActorAiState(0)->sectorId, 4);
    bool reachedNeighboringSector = false;
    for (int step = 0; step < 5 * 128; ++step)
    {
        scene.partyRuntime().update((535.851f - 565.634f) / 5, (4885.110f - 6210.096f) / 5,
            false, true, 1.0f / 128);
        fixture.advance(1.0f / 128);
        CAPTURE(step);
        CAPTURE(scene.partyRuntime().movementState().sectorId);
        reachedNeighboringSector = reachedNeighboringSector || scene.partyRuntime().movementState().sectorId == 3;
        REQUIRE_FALSE(scene.worldRuntime().mapActorAiState(0)->hasDetectedParty);
    }
    CHECK(scene.partyRuntime().partyX() == doctest::Approx(535.851f).epsilon(0.001));
    CHECK(scene.partyRuntime().partyY() == doctest::Approx(4885.110f).epsilon(0.001));
    CHECK(reachedNeighboringSector);
    fixture.advance(1);
    fixture.checkUnseen();
}

TEST_CASE("indoor detection waits for the Goblinwatch doorway to open and preserves the encounter on restore")
{
    GoblinwatchDetectionFixture fixture(-192, 3900);
    IndoorSceneRuntime &scene = *fixture.pScene;
    scene.partyRuntime().teleportPartyPosition(-192, 4560, 0);
    fixture.advance(1);
    fixture.checkUnseen();
    REQUIRE(scene.activateEvent(61, "face", 0));
    fixture.advance(3);
    CHECK_GT(scene.eventRuntimeState()->mechanisms.at(23).currentDistance, 0);
    CHECK(scene.worldRuntime().mapActorAiState(0)->hasDetectedParty);

    // Return behind the entrance door. Current visibility must not erase a previous encounter.
    scene.partyRuntime().teleportPartyPosition(565.634f, 6210.096f, 0);
    const IndoorSceneRuntime::Snapshot saved = scene.snapshot();
    scene.restoreSnapshot(saved);
    fixture.advance(1);
    CHECK(scene.worldRuntime().mapActorAiState(0)->hasDetectedParty);
    CHECK_NE(scene.worldRuntime().mapDeltaData()->actors[0].attributes & uint32_t(EvtActorAttribute::Nearby), 0u);
}
