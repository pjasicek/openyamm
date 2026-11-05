#include <doctest/doctest.h>

#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/maps/MapDeltaData.h"
#include "tests/RegressionMapLoader.h"

#include <array>
#include <cmath>
#include <utility>

TEST_SUITE_BEGIN(OpenYAMM::Tests::SharedRegressionMapSuite);

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

TEST_CASE("an airborne corpse wedged where it cannot move does not keep gaining fall speed")
{
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader data = regressionMapLoader().gameDataLoader;
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "6d20.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    IndoorMovementController controller(*loaded.indoorMapData, &loaded.indoorMapDeltaData, &loaded.eventRuntimeState);

    // A corpse from a playthrough save: it never moved, while its fall speed grew to -72000 and every step ran the
    // maximum substep count with a recovery search in each.
    const IndoorBodyDimensions body = {51.0f, 152.0f};
    IndoorMoveState state = {};
    state.x = 3259.48f;
    state.y = 671.319f;
    state.footZ = -205.011f;
    state.eyeHeight = body.height;
    state.verticalVelocity = -2000.0f;
    state.sectorId = 13;
    state.eyeSectorId = 13;
    state.grounded = false;

    for (int step = 0; step < 256; ++step)
    {
        state = controller.resolveMove(state, body, 0.0f, 0.0f, false, 1.0f / 128.0f, nullptr, std::nullopt, true,
            nullptr, false, false, 420.0f, 1.0f, false, true, false, false, true);
    }

    CHECK_EQ(state.footZ, doctest::Approx(-205.011f).epsilon(0.01));
    CHECK_GT(state.verticalVelocity, -32.0f);
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

TEST_CASE("the party running at the base of plane of earth cave slopes stays inside its room")
{
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader data = regressionMapLoader().gameDataLoader;
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "eleme.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    IndoorMovementController controller(*loaded.indoorMapData, &loaded.indoorMapDeltaData, &loaded.eventRuntimeState);
    controller.setSlopeRule(IndoorSlopeRule::Party);
    const IndoorBodyDimensions body = {};
    constexpr float RunSpeed = 768.0f;

    // Running west off floor 3072 toward slope 1600: the footprint probe ahead reached under the slope and found
    // room 15's floor 384 below, which dropped the party into room 15 and through the slope.
    // Running along the base of the near-vertical slope 1428: the floor sample skipped the slope above the knees
    // and took room 22's floor 950 below, inside the rock.
    struct Run
    {
        float x;
        float y;
        float footZ;
        float yaw;
        int16_t sectorId;
    };

    for (const Run &run : {Run{-3408, 4736, -384, 3.14159f, 20}, Run{-1488, 3200, -1044, 0.5236f, 16}})
    {
        CAPTURE(run.x);
        IndoorMoveState state = controller.initializeStateFromEyePosition(run.x, run.y, run.footZ + 160, body);
        REQUIRE(state.grounded);
        REQUIRE_EQ(state.sectorId, run.sectorId);

        for (int step = 0; step < 128; ++step)
        {
            state = controller.resolveMove(state, body, RunSpeed * std::cos(run.yaw), RunSpeed * std::sin(run.yaw),
                false, 1.0f / 128.0f, nullptr, std::nullopt, true, nullptr, false, false, 480.0f, 0.0f, false,
                false, false, false, false, 1280.0f);
            REQUIRE_EQ(state.sectorId, run.sectorId);
        }

        CHECK(state.grounded);
        CHECK_GE(state.footZ, run.footZ - 64.0f);
    }
}

TEST_CASE("the party walks off the low edge of a sloped lip")
{
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader data = regressionMapLoader().gameDataLoader;
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "d18.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    IndoorMovementController controller(*loaded.indoorMapData, &loaded.indoorMapDeltaData, &loaded.eventRuntimeState);
    controller.setSlopeRule(IndoorSlopeRule::Party);
    const IndoorBodyDimensions body = {};
    constexpr float RunSpeed = 768.0f;
    constexpr float Yaw = 5.5978f;

    // The lip ends above a lower floor, so the footprint probe takes that floor while the centre is on the lip. The
    // body must leave: refusing every lower floor ahead held it at the lip's edge, z 840.
    IndoorMoveState state = controller.initializeStateFromEyePosition(5969, -1088, 1004, body);

    for (int step = 0; step < 64; ++step)
    {
        state = controller.resolveMove(state, body, RunSpeed * std::cos(Yaw), RunSpeed * std::sin(Yaw), false,
            1.0f / 128.0f, nullptr, std::nullopt, true, nullptr, false, false, 480.0f, 0.0f, false, false, false, false,
            false, 1280.0f);
    }

    CHECK_GT(state.x, 6100.0f);
    CHECK_LT(state.footZ, 800.0f);
}

namespace
{
// A street (z 0) and a terrace 61 over it from x 0, MM9's 24 LT raised floor; with `halfStep`, the MM9 city
// converter's invisible half step in front of it (level_generation/projects/mm9r_common/city/hooks.py `half_steps`:
// a top at half the rise, 20 LT = 51 deep, and its riser).
IndoorMapData raisedTerrace(bool halfStep)
{
    constexpr int Rise = 61;
    constexpr int Half = 30;
    constexpr int Depth = 51;
    IndoorMapData map;
    map.vertices = {
        {-600, -256, 0}, {0, -256, 0}, {0, 256, 0}, {-600, 256, 0},
        {0, -256, Rise}, {600, -256, Rise}, {600, 256, Rise}, {0, 256, Rise},
        {-Depth, -256, Half}, {0, -256, Half}, {0, 256, Half}, {-Depth, 256, Half},
        {-Depth, -256, 0}, {-Depth, 256, 0}
    };
    IndoorFace street;
    street.vertexIndices = {0, 1, 2, 3};
    street.facetType = 3;
    street.roomNumber = 1;
    IndoorFace terrace;
    terrace.vertexIndices = {4, 5, 6, 7};
    terrace.facetType = 3;
    terrace.roomNumber = 1;
    IndoorFace riser;
    riser.vertexIndices = {1, 4, 7, 2};
    riser.facetType = 1;
    riser.roomNumber = 1;
    map.faces = {street, terrace, riser};

    if (halfStep)
    {
        IndoorFace stepTop;
        stepTop.vertexIndices = {8, 9, 10, 11};
        stepTop.facetType = 3;
        stepTop.roomNumber = 1;
        stepTop.attributes = static_cast<uint32_t>(FaceAttribute::Invisible);
        IndoorFace stepRiser;
        stepRiser.vertexIndices = {12, 8, 11, 13};
        stepRiser.facetType = 1;
        stepRiser.roomNumber = 1;
        stepRiser.attributes = static_cast<uint32_t>(FaceAttribute::Invisible);
        map.faces.push_back(stepTop);
        map.faces.push_back(stepRiser);
    }

    map.sectors.resize(2);
    IndoorSector &sector = map.sectors[1];
    sector.minX = -600;
    sector.maxX = 600;
    sector.minY = -256;
    sector.maxY = 256;
    sector.minZ = 0;
    sector.maxZ = 512;
    sector.floorFaceIds = halfStep ? std::vector<uint16_t>{0, 1, 3} : std::vector<uint16_t>{0, 1};
    sector.wallFaceIds = halfStep ? std::vector<uint16_t>{2, 4} : std::vector<uint16_t>{2};
    for (uint16_t faceId = 0; faceId < map.faces.size(); ++faceId)
    {
        sector.faceIds.push_back(faceId);
    }
    sector.nonBspFaceIds = sector.faceIds;
    sector.floorCount = static_cast<uint16_t>(sector.floorFaceIds.size());
    sector.wallCount = static_cast<uint16_t>(sector.wallFaceIds.size());
    sector.faceCount = sector.nonBspFaceCount = static_cast<uint16_t>(sector.faceIds.size());
    return map;
}

IndoorMoveState walkTowardTerrace(bool halfStep)
{
    const IndoorMapData map = raisedTerrace(halfStep);
    std::optional<MapDeltaData> delta = MapDeltaData{};
    std::optional<EventRuntimeState> events = EventRuntimeState{};
    IndoorMovementController controller(map, &delta, &events);
    controller.setSlopeRule(IndoorSlopeRule::Party);
    const IndoorBodyDimensions body = {};
    IndoorMoveState state = controller.initializeStateFromEyePosition(-300.0f, 0.0f, body.height, body);
    REQUIRE(state.grounded);

    for (int step = 0; step < 256; ++step)
    {
        state = controller.resolveMove(state, body, 384.0f, 0.0f, false, 1.0f / 128.0f, nullptr, std::nullopt, true,
            nullptr, false, false, 480.0f, 0.0f, false, false, false, false, false, 1280.0f);
    }

    return state;
}
}

TEST_CASE("the party climbs a 61-unit terrace only over the city converter's invisible half step")
{
    // The party steps 50 (MaximumRise): the bare 61 riser stops it on the street.
    const IndoorMoveState bare = walkTowardTerrace(false);
    CHECK_LT(bare.x, 0.0f);
    CHECK_EQ(bare.footZ, doctest::Approx(0.0f));

    // Two rises of 30 and 31: it walks on onto the terrace.
    const IndoorMoveState stepped = walkTowardTerrace(true);
    CHECK_GT(stepped.x, 200.0f);
    CHECK_EQ(stepped.footZ, doctest::Approx(61.0f));
}

namespace
{
// MM9 terrain converted to BLV floors: seven sloped triangles round one shared corner of the Isle of Ashes (faces
// 9866, 9867, 9872, 9873, 5229, 10141, 10452 of the pilot, moved to the corner at the origin). The body's sweep meets
// the edge of a rising face at the corner, whose first vertex lies 41 higher.
IndoorMapData terrainCorner()
{
    const std::vector<std::vector<std::array<int16_t, 3>>> triangles = {
        {{-288, 41, 41}, {-288, -286, 56}, {0, 0, 0}},
        {{0, -287, 41}, {0, 0, 0}, {-288, -286, 56}},
        {{0, 286, 0}, {0, 0, 0}, {288, 245, 82}},
        {{288, 0, 41}, {288, 245, 82}, {0, 0, 0}},
        {{288, 0, 41}, {0, 0, 0}, {0, -287, 41}, {288, -287, 82}, {576, 0, 82}},
        {{-288, 41, 41}, {0, 0, 0}, {0, 286, 0}},
        {{-288, 41, 41}, {0, 286, 0}, {-288, 245, 0}}
    };
    IndoorMapData map;
    map.sectors.resize(2);
    IndoorSector &sector = map.sectors[1];
    for (const std::vector<std::array<int16_t, 3>> &corners : triangles)
    {
        IndoorFace face;
        face.facetType = 3;
        face.roomNumber = 1;
        for (const std::array<int16_t, 3> &corner : corners)
        {
            face.vertexIndices.push_back(static_cast<uint16_t>(map.vertices.size()));
            map.vertices.push_back({corner[0], corner[1], corner[2]});
        }
        sector.floorFaceIds.push_back(static_cast<uint16_t>(map.faces.size()));
        map.faces.push_back(face);
    }
    sector.minX = -288;
    sector.maxX = 576;
    sector.minY = -287;
    sector.maxY = 286;
    sector.minZ = 0;
    sector.maxZ = 512;
    sector.faceIds = sector.nonBspFaceIds = sector.floorFaceIds;
    sector.floorCount = static_cast<uint16_t>(sector.floorFaceIds.size());
    sector.faceCount = sector.nonBspFaceCount = sector.floorCount;
    return map;
}
}

TEST_CASE("the party walking over sloped terrain faces stays on them where it meets a rising face's edge")
{
    // A floor edge the sweep meets was a tread at its first vertex's height: on terrain that lifted the party 41 and
    // dropped it again (head bob on the Isle of Ashes, 2026-11-01). It takes the face's height at the contact.
    const IndoorMapData map = terrainCorner();
    std::optional<MapDeltaData> delta = MapDeltaData{};
    std::optional<EventRuntimeState> events = EventRuntimeState{};
    IndoorMovementController controller(map, &delta, &events);
    controller.setSlopeRule(IndoorSlopeRule::Party);
    const IndoorBodyDimensions body = {};
    IndoorMoveState state = controller.initializeStateFromEyePosition(-114.0f, -141.0f, 30.0f + body.height, body);
    REQUIRE(state.grounded);
    const float yaw = 0.890f;

    for (int step = 0; step < 30; ++step)
    {
        state = controller.resolveMove(state, body, 727.0f * std::cos(yaw), 727.0f * std::sin(yaw), false,
            1.0f / 60.0f, nullptr, std::nullopt, true);
        const IndoorFloorSample floor =
            sampleIndoorFloor(map, map.vertices, state.x, state.y, state.footZ, 50.0f, 1024.0f, int16_t(1));
        CAPTURE(step);
        CAPTURE(state.x);
        CAPTURE(state.y);
        REQUIRE(floor.hasFloor);
        CHECK(state.grounded);
        CHECK_LT(std::abs(state.footZ - floor.height), 8.0f);
    }

    CHECK_GT(state.x, 100.0f);
}

namespace
{
// MM9 terrain over an MM9 floor: a flat floor at 0 runs on under a 60-degree slope rising from x = 100 (the Isle of
// Ashes' cliffs over its PhysicsBSP floors).
IndoorMapData cliffOverFloor()
{
    IndoorMapData map;
    map.vertices = {
        {-400, -256, 0}, {600, -256, 0}, {600, 256, 0}, {-400, 256, 0},
        {100, -256, 0}, {400, -256, 520}, {400, 256, 520}, {100, 256, 0}
    };
    IndoorFace floor;
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;
    IndoorFace cliff;
    cliff.vertexIndices = {4, 5, 6, 7};
    cliff.facetType = 4;
    cliff.roomNumber = 1;
    map.faces = {floor, cliff};
    map.sectors.resize(2);
    IndoorSector &sector = map.sectors[1];
    sector.minX = -400;
    sector.maxX = 600;
    sector.minY = -256;
    sector.maxY = 256;
    sector.minZ = 0;
    sector.maxZ = 1024;
    sector.floorFaceIds = {0, 1};
    sector.faceIds = sector.nonBspFaceIds = {0, 1};
    sector.floorCount = 2;
    sector.faceCount = sector.nonBspFaceCount = 2;
    return map;
}
}

TEST_CASE("a body under a steep slope's plane collides with it instead of walking on under it")
{
    // The steep-floor sweep exemption is for a body standing on the slope; one walking into it from under its plane
    // passed through (the Isle of Ashes' cliffs, 2026-11-02). With the monsters' slope rule the cliff stops it.
    const IndoorMapData map = cliffOverFloor();
    std::optional<MapDeltaData> delta = MapDeltaData{};
    std::optional<EventRuntimeState> events = EventRuntimeState{};
    IndoorMovementController controller(map, &delta, &events);
    controller.setSlopeRule(IndoorSlopeRule::Actor);
    const IndoorBodyDimensions body = {};
    IndoorMoveState state = controller.initializeStateFromEyePosition(-200.0f, 0.0f, body.height, body);
    REQUIRE(state.grounded);
    for (int step = 0; step < 120; ++step)
    {
        state = controller.resolveMove(state, body, 720.0f, 0.0f, false, 1.0f / 60.0f, nullptr, std::nullopt, true);
    }
    CHECK_LT(state.x, 160.0f);
    CHECK_LT(state.footZ, 110.0f);
}

TEST_CASE("the party crossing a crease between sloped faces follows the ground without a sawtooth")
{
    // Sloped faces meeting at a crease (MM9 terrain: one falling 30 over 300, the next rising 60 over 300). Stepping
    // early onto the face ahead at its height a radius away lifted and dropped the body by up to 5 at each step.
    IndoorMapData map;
    map.vertices = {{-300, -256, 30}, {0, -256, 0}, {0, 256, 0}, {-300, 256, 30}, {300, -256, 60}, {300, 256, 60}};
    IndoorFace down;
    down.vertexIndices = {0, 1, 2, 3};
    down.facetType = 3;
    down.roomNumber = 1;
    IndoorFace up;
    up.vertexIndices = {1, 4, 5, 2};
    up.facetType = 3;
    up.roomNumber = 1;
    map.faces = {down, up};
    map.sectors.resize(2);
    IndoorSector &sector = map.sectors[1];
    sector.minX = -300;
    sector.maxX = 300;
    sector.minY = -256;
    sector.maxY = 256;
    sector.minZ = 0;
    sector.maxZ = 512;
    sector.floorFaceIds = {0, 1};
    sector.faceIds = sector.nonBspFaceIds = {0, 1};
    sector.floorCount = 2;
    sector.faceCount = sector.nonBspFaceCount = 2;

    std::optional<MapDeltaData> delta = MapDeltaData{};
    std::optional<EventRuntimeState> events = EventRuntimeState{};
    IndoorMovementController controller(map, &delta, &events);
    controller.setSlopeRule(IndoorSlopeRule::Party);
    const IndoorBodyDimensions body = {};
    IndoorMoveState state = controller.initializeStateFromEyePosition(-250.0f, 0.0f, 25.0f + body.height, body);
    for (int step = 0; step < 35; ++step)
    {
        state = controller.resolveMove(state, body, 720.0f, 0.0f, false, 1.0f / 60.0f, nullptr, std::nullopt, true);
        const float ground = state.x < 0.0f ? -state.x * 0.1f : state.x * 0.2f;
        CAPTURE(state.x);
        CHECK(state.grounded);
        CHECK_LT(std::abs(state.footZ - ground), 1.0f);
    }
}

namespace
{
// A floor 1 000 long with an invisible, untouchable wall across it at x = 300 (MM9's AIBarrier along a bridge): face 1.
IndoorMapData floorWithBarrier()
{
    IndoorMapData map;
    map.vertices = {{-500, -256, 0}, {500, -256, 0}, {500, 256, 0}, {-500, 256, 0},
        {300, -256, 0}, {300, 256, 0}, {300, 256, 300}, {300, -256, 300}};
    IndoorFace floor;
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;
    IndoorFace barrier;
    barrier.vertexIndices = {4, 5, 6, 7};
    barrier.facetType = 1;
    barrier.roomNumber = 1;
    barrier.attributes = faceAttributeBit(FaceAttribute::Invisible) | faceAttributeBit(FaceAttribute::Untouchable);
    map.faces = {floor, barrier};
    map.sectors.resize(2);
    IndoorSector &sector = map.sectors[1];
    sector.minX = -500;
    sector.maxX = 500;
    sector.minY = -256;
    sector.maxY = 256;
    sector.minZ = 0;
    sector.maxZ = 512;
    sector.floorFaceIds = {0};
    sector.wallFaceIds = {1};
    sector.faceIds = sector.nonBspFaceIds = {0, 1};
    sector.floorCount = 1;
    sector.wallCount = 1;
    sector.faceCount = sector.nonBspFaceCount = 2;
    return map;
}

float walkEast(const IndoorMapData &map, bool blockedByActorBarriers)
{
    std::optional<MapDeltaData> delta = MapDeltaData{};
    std::optional<EventRuntimeState> events = EventRuntimeState{};
    IndoorMovementController controller(map, &delta, &events);
    controller.setBlockedByActorBarriers(blockedByActorBarriers);
    const IndoorBodyDimensions body = {};
    IndoorMoveState state = controller.initializeStateFromEyePosition(0.0f, 0.0f, body.height, body);
    for (int step = 0; step < 90; ++step)
    {
        state = controller.resolveMove(state, body, 720.0f, 0.0f, false, 1.0f / 60.0f, nullptr, std::nullopt, true);
    }
    return state.x;
}
}

TEST_CASE("the scene's monster-only walls stop monsters and nothing else")
{
    IndoorMapData map = floorWithBarrier();
    // Not listed in the scene: the untouchable face stops nobody (every MM6-MM8 map).
    CHECK_GT(walkEast(map, true), 400.0f);
    map.actorBarrierFaceIds = {1};
    // The party's controller walks through, the monsters' stops at the wall.
    CHECK_GT(walkEast(map, false), 400.0f);
    CHECK_LT(walkEast(map, true), 300.0f);
}

TEST_SUITE_END();
