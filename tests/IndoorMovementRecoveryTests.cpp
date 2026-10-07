#include <doctest/doctest.h>

#include "game/indoor/IndoorMovementController.h"
#include "game/maps/MapDeltaData.h"
#include "tests/RegressionMapLoader.h"

#include <cmath>
#include <utility>

using namespace OpenYAMM::Game;

namespace
{
IndoorMapData recoveryRoom()
{
    IndoorMapData map;
    map.vertices = {
        {-512, -512, 0}, {512, -512, 0}, {512, 512, 0}, {-512, 512, 0},
        {0, -512, 0}, {0, -512, 256}, {0, 512, 256}, {0, 512, 0}
    };
    IndoorFace floor;
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;
    IndoorFace wall;
    wall.vertexIndices = {4, 5, 6, 7};
    wall.facetType = 1;
    wall.roomNumber = 1;
    map.faces = {floor, wall};
    map.sectors.resize(2);
    IndoorSector &sector = map.sectors[1];
    sector.minX = sector.minY = -512;
    sector.maxX = sector.maxY = 512;
    sector.minZ = 0;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.wallFaceIds = {1};
    sector.faceIds = sector.nonBspFaceIds = {0, 1};
    sector.floorCount = sector.wallCount = 1;
    sector.faceCount = sector.nonBspFaceCount = 2;
    return map;
}

IndoorMoveState pressIntoWall(IndoorMovementController &controller, const IndoorMoveState &state)
{
    return controller.resolveMove(state, {56.0f, 145.0f}, -255.0f, 0.0f, false, 1.0f / 128.0f,
        nullptr, 0, false, nullptr, false, false, 420.0f, 1.0f, false, true, false, true, true);
}
}

TEST_CASE("indoor wall recovery cannot push a crowded actor through the blocking wall")
{
    const IndoorMapData map = recoveryRoom();
    std::optional<MapDeltaData> delta = MapDeltaData{};
    std::optional<EventRuntimeState> events = EventRuntimeState{};
    IndoorMovementController controller(map, &delta, &events);
    IndoorMoveState state = controller.initializeStateFromEyePosition(32.0f, 0.0f, 145.0f, {56.0f, 145.0f});
    REQUIRE(state.grounded);
    REQUIRE_EQ(state.sectorId, 1);
    controller.setActorColliders({
        {.actorIndex = 1, .sectorId = 1, .x = 140, .y = 0, .z = 0, .radius = 56, .height = 145},
        {.actorIndex = 2, .sectorId = 1, .x = 32, .y = 110, .z = 0, .radius = 56, .height = 145},
        {.actorIndex = 3, .sectorId = 1, .x = 32, .y = -110, .z = 0, .radius = 56, .height = 145},
    });

    for (int step = 0; step < 32; ++step)
    {
        const IndoorMoveState resolved = pressIntoWall(controller, state);
        CHECK_GE(resolved.x, state.x);
        state = resolved;
        REQUIRE_GE(state.x, 0.0f);
    }
}

TEST_CASE("goblinwatch wall recovery cannot jump through the closed entrance corridor door")
{
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader data = regressionMapLoader().gameDataLoader;
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "6d01.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    const IndoorMapData &map = *loaded.indoorMapData;
    IndoorMovementController controller(map, &loaded.indoorMapDeltaData, &loaded.eventRuntimeState);
    IndoorMoveState state = controller.initializeStateFromEyePosition(-264, 4416, 145, {56, 145});
    REQUIRE(state.grounded);
    REQUIRE_EQ(state.sectorId, 3);
    REQUIRE_EQ(state.supportFaceIndex, 1594u);

    // Replay the crowd at the failing movement step: actor 43 used to jump from
    // Y=4416 to Y=4544 through door face 1623 when the other actors blocked retreat.
    controller.setActorColliders({
        {.actorIndex = 42, .sectorId = 3, .x = -264, .y = 4269.55f, .z = 0, .radius = 56, .height = 145},
        {.actorIndex = 44, .sectorId = 3, .x = -231.525f, .y = 4342.89f, .z = 0, .radius = 56, .height = 145},
        {.actorIndex = 187, .sectorId = 3, .x = -151.858f, .y = 4350.18f, .z = 76.9009f,
            .radius = 59, .height = 109},
    });
    const IndoorMoveState resolved = controller.resolveMove(state, {56, 145}, -154.935f, 202.535f,
        false, 1.0f / 128.0f, nullptr, 43, false, nullptr, false, false, 420, 1, false, true, false, true, true);
    CHECK_LT(resolved.y, 4448.0f);
    CHECK_GE(resolved.x, -320.0f);
}

TEST_CASE("sloped indoor tile edge slack keeps support within the tile height range")
{
    IndoorMapData map;
    map.vertices = {{-2040, -64, 496}, {-1928, -64, 448}, {-1928, 64, 448}, {-2040, 64, 496}};
    IndoorFace tile;
    tile.vertexIndices = {0, 1, 2, 3};
    tile.facetType = 4;
    map.faces = {tile};

    for (const std::pair<float, float> &probe : {std::pair{-1927.24f, 448.0f},
             std::pair{-2041.0f, 496.0f}, std::pair{-1984.0f, 472.0f}})
    {
        const IndoorFloorSample floor = sampleIndoorFloorOnFace(
            map, map.vertices, 0, probe.first, 0, 449.854f, 50, 160);
        REQUIRE(floor.hasFloor);
        CHECK_EQ(floor.height, doctest::Approx(probe.second));
    }
}

TEST_CASE("silver helm sloped platforms admit slow walking without jumping")
{
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader data = regressionMapLoader().gameDataLoader;
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "6d07.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapDeltaData.has_value());
    std::optional<EventRuntimeState> events = EventRuntimeState{};
    for (const MapDeltaDoor &door : loaded.indoorMapDeltaData->doors)
    {
        if (door.doorId >= 21 && door.doorId <= 27)
        {
            // Open has distance zero: these horizontal mechanisms are the first flight of tiles.
            events->mechanisms[door.doorId] = RuntimeMechanismState{};
        }
    }

    for (float speed : {96.0f, 384.0f, 768.0f})
    {
        CAPTURE(speed);
        IndoorMovementController controller(*loaded.indoorMapData, &loaded.indoorMapDeltaData, &events);
        const IndoorBodyDimensions body = {};
        IndoorMoveState state = controller.initializeStateFromEyePosition(-1419.356f, 4787.935f, 416, body);
        REQUIRE(state.grounded);
        const int stepCount = int(std::ceil(1024.0f / speed * 128.0f));
        for (int step = 0; step < stepCount; ++step)
        {
            state = controller.resolveMove(state, body, speed * std::cos(3.119f), speed * std::sin(3.119f),
                false, 1.0f / 128.0f, nullptr, std::nullopt, true);
        }
        CHECK_LT(state.x, -2330.0f);
        CHECK(state.grounded);
        CHECK_EQ(state.footZ, doctest::Approx(640.0f));
        CHECK_EQ(state.supportFaceIndex, 1520u);
    }
}
