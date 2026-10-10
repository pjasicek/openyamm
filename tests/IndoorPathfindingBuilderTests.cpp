#include "doctest/doctest.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/indoor/IndoorPathfindingBuilder.h"
#include "game/pathfinding/ActorPathRuntime.h"
#include "tests/RegressionMapLoader.h"

#include <cmath>
#include <utility>
#include <vector>

TEST_SUITE_BEGIN(OpenYAMM::Tests::SharedRegressionMapSuite);

using OpenYAMM::Game::FaceAttribute;
using OpenYAMM::Game::IndoorFace;
using OpenYAMM::Game::IndoorFaceGeometryCache;
using OpenYAMM::Game::IndoorMapData;
using OpenYAMM::Game::IndoorPathMapBuildResult;
using OpenYAMM::Game::IndoorPathfindingBuilder;
using OpenYAMM::Game::IndoorVertex;
using OpenYAMM::Game::MapDeltaData;
using OpenYAMM::Game::PathObject;
using OpenYAMM::Game::faceAttributeBit;

namespace
{
IndoorFace makeIndoorFace(std::vector<uint16_t> vertexIndices, uint8_t facetType, uint32_t attributes = 0)
{
    IndoorFace face = {};
    face.vertexIndices = std::move(vertexIndices);
    face.facetType = facetType;
    face.attributes = attributes;
    face.roomNumber = 0;
    face.roomBehindNumber = 0;
    face.isPortal = (attributes & faceAttributeBit(FaceAttribute::IsPortal)) != 0;
    return face;
}

PathObject makeIndoorPathObject()
{
    PathObject object = {};
    object.radius = 8.0f;
    object.stepLength = 24.0f;
    object.stepHeight = 40.0f;
    return object;
}
}

TEST_CASE("indoor pathfinding builder converts BLV faces into walkable and blocking path facets")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-100, -100, 0},
        {100, -100, 0},
        {100, 100, 0},
        {-100, 100, 0},
        {0, -40, 0},
        {0, 40, 0},
        {0, 40, 120},
        {0, -40, 120}
    };
    mapData.faces = {
        makeIndoorFace({0, 1, 2, 3}, 3),
        makeIndoorFace({4, 5, 6, 7}, 1)
    };

    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    const IndoorPathMapBuildResult result =
        IndoorPathfindingBuilder::buildPathMap(mapData, mapData.vertices, nullptr, &geometryCache);

    REQUIRE_EQ(result.sourceFaceCount, 2u);
    REQUIRE_EQ(result.pathFacetCount, 2u);
    REQUIRE_EQ(result.skippedFaceCount, 0u);
    CHECK(result.pathMap.floorAt({-50.0f, 0.0f, 20.0f}).hasFloor);
    CHECK_FALSE(
        result.pathMap.canReachDirectly(
            {-50.0f, 0.0f, 0.0f},
            {50.0f, 0.0f, 0.0f},
            makeIndoorPathObject()));
}

TEST_CASE("indoor pathfinding builder keeps portals non-blocking")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-100, -100, 0},
        {100, -100, 0},
        {100, 100, 0},
        {-100, 100, 0},
        {0, -40, 0},
        {0, 40, 0},
        {0, 40, 120},
        {0, -40, 120}
    };
    mapData.faces = {
        makeIndoorFace({0, 1, 2, 3}, 3),
        makeIndoorFace({4, 5, 6, 7}, 1, faceAttributeBit(FaceAttribute::IsPortal))
    };

    const IndoorPathMapBuildResult result =
        IndoorPathfindingBuilder::buildPathMap(mapData, mapData.vertices);

    REQUIRE_EQ(result.pathFacetCount, 2u);
    CHECK(
        result.pathMap.canReachDirectly(
            {-50.0f, 0.0f, 0.0f},
            {50.0f, 0.0f, 0.0f},
            makeIndoorPathObject()));
}

TEST_CASE("indoor pathfinding excludes horizontal portals from floor and overhead support")
{
    using namespace OpenYAMM::Game;
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-100, -100, 0}, {100, -100, 0}, {100, 100, 0}, {-100, 100, 0},
        {-100, -100, 128}, {100, -100, 128}, {100, 100, 128}, {-100, 100, 128},
        {-100, -100, 512}, {100, -100, 512}, {100, 100, 512}, {-100, 100, 512}
    };
    mapData.faces = {
        makeIndoorFace({0, 1, 2, 3}, 3),
        makeIndoorFace({4, 5, 6, 7}, 3, faceAttributeBit(FaceAttribute::IsPortal)),
        makeIndoorFace({8, 9, 10, 11}, 3)
    };
    const IndoorPathMapBuildResult build =
        IndoorPathfindingBuilder::buildPathMap(mapData, mapData.vertices);

    // An opening has neither a floor to stand on nor an overhead floor to stop a flyer.
    const PathFloorQueryDebug belowPortal = build.pathMap.debugFloorQuery({0, 0, 64});
    REQUIRE(belowPortal.bestBelow.hasFloor);
    CHECK_EQ(belowPortal.bestBelow.z, doctest::Approx(0));
    REQUIRE(belowPortal.bestAbove.hasFloor);
    CHECK_EQ(belowPortal.bestAbove.z, doctest::Approx(512));
    const PathFloorSample abovePortal = build.pathMap.floorAt({0, 0, 256});
    REQUIRE(abovePortal.hasFloor);
    CHECK_EQ(abovePortal.z, doctest::Approx(0));

    PathObject flyer = makeIndoorPathObject();
    flyer.canFly = true;
    CHECK(build.pathMap.canReachDirectly({0, 0, 64}, {0, 0, 256}, flyer));
    CHECK_FALSE(build.pathMap.canReachDirectly({0, 0, 256}, {0, 0, 600}, flyer));
    CHECK_FALSE(build.pathMap.canReachDirectly({0, 0, 64}, {0, 0, -64}, flyer));
}

TEST_CASE("hive pit portal is not a floor or a ceiling for flying path queries")
{
    using namespace OpenYAMM::Game;
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader data = regressionMapLoader().gameDataLoader;
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "hive.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    const IndoorMapData &map = *loaded.indoorMapData;
    const IndoorPathMapBuildResult build = IndoorPathfindingBuilder::buildPathMap(map, map.vertices);

    // Devil 124 stalled at Z=-331: portal 2316 at Z=0 was misclassified as an overhead floor.
    for (float z : {-331.0f, -106.0f, 40.0f})
    {
        const PathFloorQueryDebug query = build.pathMap.debugFloorQuery({754.299f, 7241.0f, z});
        INFO("query Z=" << z);
        REQUIRE(query.result.hasFloor);
        CHECK_FALSE(query.result.inVoid);
        CHECK_EQ(query.result.z, doctest::Approx(-768));
        CHECK_FALSE(query.bestAbove.hasFloor);
    }
}

TEST_CASE("indoor pathfinding builder applies map delta face attributes")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-100, -100, 0},
        {100, -100, 0},
        {100, 100, 0},
        {-100, 100, 0},
        {0, -40, 0},
        {0, 40, 0},
        {0, 40, 120},
        {0, -40, 120}
    };
    mapData.faces = {
        makeIndoorFace({0, 1, 2, 3}, 3),
        makeIndoorFace({4, 5, 6, 7}, 1)
    };

    MapDeltaData deltaData = {};
    deltaData.faceAttributes = {
        mapData.faces[0].attributes,
        faceAttributeBit(FaceAttribute::Untouchable)
    };

    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    const IndoorPathMapBuildResult result =
        IndoorPathfindingBuilder::buildPathMap(mapData, mapData.vertices, &deltaData, &geometryCache);

    REQUIRE_EQ(result.pathFacetCount, 2u);
    CHECK(
        result.pathMap.canReachDirectly(
            {-50.0f, 0.0f, 0.0f},
            {50.0f, 0.0f, 0.0f},
            makeIndoorPathObject()));
}

TEST_CASE("goblinwatch chest permits a goblin to descend to the party")
{
    using namespace OpenYAMM::Game;
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader gameDataLoader = regressionMapLoader().gameDataLoader;
    REQUIRE(gameDataLoader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "6d01.blv"));
    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();
    REQUIRE(selectedMap.has_value());
    REQUIRE(selectedMap->indoorMapData.has_value());
    const IndoorMapData &mapData = *selectedMap->indoorMapData;
    const IndoorMovementController controller(mapData, &selectedMap->indoorMapDeltaData, nullptr);

    // GW_1: Goblin Shaman at the front edge of the chest, above the 16-unit tread and room floor.
    const IndoorBodyDimensions body{56.0f, 145.0f};
    IndoorMoveState state = controller.initializeStateFromEyePosition(-1146.81f, 3980.99f, 96.0f + body.height, body);
    REQUIRE(state.grounded);
    REQUIRE_EQ(state.supportFaceIndex, 1821u);
    REQUIRE_EQ(state.footZ, doctest::Approx(96.0f));
    const PathPoint target{-1148.23f, 4538.85f, 0.0f};

    bool usePath = false;
    SUBCASE("direct pursuit descends while the planner is deferred")
    {
    }
    SUBCASE("planned pursuit descends")
    {
        usePath = true;
    }

    const IndoorPathMapBuildResult build = IndoorPathfindingBuilder::buildPathMap(mapData, mapData.vertices);
    ActorPathRuntime runtime;
    ActorPathResolveRequest follow = {};
    follow.target = target;
    follow.object.radius = body.radius;
    follow.object.height = body.height;
    follow.object.stepLength = 40.0f;
    follow.object.stepHeight = 40.0f;
    follow.object.dropHeight = IndoorActorMaxDropHeight;
    follow.allowDirect = false;
    follow.waypointReachDistance = 32.0f;
    bool fell = false;
    bool arrived = false;

    for (int step = 0; step < 3 * 128; ++step)
    {
        const float targetX = target.x - state.x;
        const float targetY = target.y - state.y;
        if (targetX * targetX + targetY * targetY < 128.0f * 128.0f)
        {
            arrived = true;
            break;
        }
        PathPoint waypoint = target;
        if (usePath)
        {
            follow.source = {state.x, state.y, state.footZ};
            follow.nowSeconds = step / 128.0;
            const ActorPathResolveResult result = runtime.resolveWaypoint(build.pathMap, follow);
            INFO("step=" << step << " position=" << state.x << "," << state.y << "," << state.footZ
                << " plan status=" << int(result.planStatus));
            REQUIRE(result.pathActive);
            waypoint = result.waypoint;
        }
        const float deltaX = waypoint.x - state.x;
        const float deltaY = waypoint.y - state.y;
        const float distance = std::hypot(deltaX, deltaY);
        REQUIRE(distance > 0.0f);
        state = controller.resolveMove(state, body, deltaX / distance * 255.0f, deltaY / distance * 255.0f,
            false, 1.0f / 128.0f, nullptr, 133, false, nullptr, false, false, 420.0f, 1.0f,
            false, !usePath, usePath, true, true);
        fell = fell || (!state.grounded && state.verticalVelocity < 0.0f);
    }
    CHECK(fell);
    CHECK(arrived);
    CHECK(state.grounded);
    CHECK_EQ(state.footZ, doctest::Approx(0.0f));
}

TEST_CASE("temple of baa hallway actors can follow paths through the floor seam and narrow passage")
{
    using namespace OpenYAMM::Game;
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader gameDataLoader = regressionMapLoader().gameDataLoader;
    REQUIRE(gameDataLoader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "d04.blv"));
    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();
    REQUIRE(selectedMap.has_value());
    REQUIRE(selectedMap->indoorMapData.has_value());
    const IndoorMapData &mapData = *selectedMap->indoorMapData;
    const IndoorMovementController controller(mapData, &selectedMap->indoorMapDeltaData, nullptr);
    const IndoorPathMapBuildResult build = IndoorPathfindingBuilder::buildPathMap(mapData, mapData.vertices);
    const PathPoint target{2782.63f, 7202.05f, -1920.0f};

    PathPoint source;
    IndoorBodyDimensions body;
    size_t supportFace = 0;
    float speed = 0.0f;
    SUBCASE("Cleric of Baa crosses coplanar floor seam")
    {
        source = {2085.705078f, 5620.802734f, -1408.0f};
        body = {74.0f, 190.0f};
        supportFace = 616;
        speed = 270.0f;
    }
    SUBCASE("Venemous Spider uses its full collision radius")
    {
        source = {1634.645264f, 6144.69043f, -1408.0f};
        body = {127.0f, 256.0f};
        supportFace = 619;
        speed = 735.0f;
    }

    IndoorMoveState state = controller.initializeStateFromEyePosition(source.x, source.y, source.z + body.height, body);
    state.supportFaceIndex = supportFace;
    REQUIRE(state.grounded);
    REQUIRE_EQ(state.footZ, source.z);
    ActorPathRuntime runtime;
    ActorPathResolveRequest follow = {};
    follow.target = target;
    follow.object.radius = body.radius;
    follow.object.height = body.height;
    follow.object.stepLength = 40.0f;
    follow.object.dropHeight = IndoorActorMaxDropHeight;
    follow.allowDirect = false;
    follow.waypointReachDistance = std::max(32.0f, body.radius * 0.35f);
    bool arrived = false;
    for (int step = 0; step < 30 * 128; ++step)
    {
        if (std::hypot(target.x - state.x, target.y - state.y) < 128.0f)
        {
            arrived = true;
            break;
        }
        follow.source = {state.x, state.y, state.footZ};
        follow.preferredSourceFacetSourceId = state.grounded ? int32_t(state.supportFaceIndex) : -1;
        follow.nowSeconds = step / 128.0;
        const ActorPathResolveResult result = runtime.resolveWaypoint(build.pathMap, follow);
        REQUIRE(result.pathActive);
        const float deltaX = result.waypoint.x - state.x;
        const float deltaY = result.waypoint.y - state.y;
        const float distance = std::hypot(deltaX, deltaY);
        REQUIRE(distance > 0.0f);
        state = controller.resolveMove(state, body, deltaX / distance * speed, deltaY / distance * speed,
            false, 1.0f / 128.0f, nullptr, 12, false, nullptr, false, false, 420.0f, 1.0f,
            false, false, true, true, true);
    }
    INFO("final position=" << state.x << "," << state.y << "," << state.footZ);
    CHECK(arrived);
    CHECK(state.grounded);
    CHECK_EQ(state.footZ, doctest::Approx(target.z));
}

TEST_CASE("goblinwatch cave actors escape sloped floor seams and low ceilings")
{
    using namespace OpenYAMM::Game;
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader loader = regressionMapLoader().gameDataLoader;
    REQUIRE(loader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "6d01.blv"));
    const MapAssetInfo &map = *loader.getSelectedMap();
    const IndoorMapData &geometry = *map.indoorMapData;
    const IndoorMovementController controller(geometry, &map.indoorMapDeltaData, nullptr);
    const IndoorPathMapBuildResult build = IndoorPathfindingBuilder::buildPathMap(geometry, geometry.vertices);
    const IndoorBodyDimensions body{56.0f, 145.0f};
    const PathPoint target{11016.8f, 4211.41f, -768.0f};
    IndoorMoveState state = {};
    state.eyeHeight = body.height;
    state.sectorId = 42;
    state.eyeSectorId = 42;
    state.grounded = true;
    SUBCASE("GW_2 goblin 55 at adjacent floor triangle edge")
    {
        state.x = 9286.1796875f;
        state.y = 2637.93017578125f;
        state.footZ = -660.572021484375f;
        state.supportFaceIndex = 1044;
    }
    SUBCASE("GW_2 goblin 56 below the sloping ceiling")
    {
        state.x = 8953.66f;
        state.y = 2578.29f;
        state.footZ = -656.209f;
        state.supportFaceIndex = 1044;
    }
    SUBCASE("GW_2 goblin 167 at ceiling triangle edge")
    {
        state.x = 7206.85f;
        state.y = 2139.68f;
        state.footZ = -670.94f;
        state.supportFaceIndex = 1047;
    }
    ActorPathRuntime runtime;
    ActorPathResolveRequest follow = {};
    follow.target = target;
    follow.object.radius = body.radius;
    follow.object.height = body.height;
    follow.object.stepLength = 40.0f;
    follow.object.dropHeight = IndoorActorMaxDropHeight;
    follow.allowDirect = false;
    follow.waypointReachDistance = 32.0f;
    bool arrived = false;
    for (int step = 0; step < 30 * 128; ++step)
    {
        if (std::hypot(target.x - state.x, target.y - state.y) < 160.0f)
        {
            arrived = true;
            break;
        }
        follow.source = {state.x, state.y, state.footZ};
        follow.preferredSourceFacetSourceId = state.grounded ? int32_t(state.supportFaceIndex) : -1;
        follow.nowSeconds = step / 128.0;
        const ActorPathResolveResult path = runtime.resolveWaypoint(build.pathMap, follow);
        REQUIRE(path.pathActive);
        const float distance = std::hypot(path.waypoint.x - state.x, path.waypoint.y - state.y);
        REQUIRE(distance > 0.0f);
        IndoorMoveDebugInfo debug = {};
        const IndoorMoveState moved = controller.resolveMove(state, body,
            (path.waypoint.x - state.x) / distance * 300.0f,
            (path.waypoint.y - state.y) / distance * 300.0f,
            false, 1.0f / 128.0f, nullptr, 55, false, &debug, false, false, 420.0f, 1.0f,
            false, false, true, true, true);
        INFO("step=" << step << " position=" << state.x << "," << state.y << "," << state.footZ
            << " face=" << debug.hitFaceIndex);
        if (debug.collisionResponseSucceeded)
        {
            CHECK(std::hypot(moved.x - state.x, moved.y - state.y) > 0.0001f);
        }
        state = moved;
    }
    INFO("final position=" << state.x << "," << state.y << "," << state.footZ);
    CHECK(arrived);
    CHECK(state.grounded);
    CHECK_EQ(state.footZ, doctest::Approx(target.z));
}

TEST_CASE("temple of baa priest clears the stair side edge")
{
    using namespace OpenYAMM::Game;
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader loader = regressionMapLoader().gameDataLoader;
    REQUIRE(loader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "d04.blv"));
    const MapAssetInfo &map = *loader.getSelectedMap();
    const IndoorMapData &geometry = *map.indoorMapData;
    const IndoorMovementController controller(geometry, &map.indoorMapDeltaData, nullptr);
    const IndoorBodyDimensions body{74.0f, 190.0f};
    // BAA_2: actor 34 touches the diagonal boundary of stair side face 1029 with its upper sphere.
    IndoorMoveState state = controller.initializeStateFromEyePosition(
        3280.3515625f, 7334.9423828125f, -1920.0f + body.height, body);
    REQUIRE(state.grounded);
    REQUIRE_EQ(state.supportFaceIndex, 1094u);

    SUBCASE("upper sphere collision slides along the edge")
    {
        IndoorMoveDebugInfo debug = {};
        const IndoorMoveState moved = controller.resolveMove(state, body, -212.132034f, 212.132034f,
            false, 1.0f / 128.0f, nullptr, 34, false, &debug, false, false, 420.0f, 1.0f,
            false, false, false, false, true);
        CHECK_EQ(debug.hitFaceIndex, 1029u);
        CHECK_EQ(debug.hitHeightOffset, doctest::Approx(body.height - body.radius));
        CHECK(std::hypot(moved.x - state.x, moved.y - state.y) > 0.1f);
        CHECK(std::hypot(moved.x - state.x, moved.y - state.y) <= 300.0f / 128.0f);
        CHECK_EQ(moved.footZ, doctest::Approx(state.footZ));
    }
    SUBCASE("planned pursuit reaches the party around the stairs")
    {
        const IndoorPathMapBuildResult build = IndoorPathfindingBuilder::buildPathMap(geometry, geometry.vertices);
        ActorPathRuntime runtime;
        ActorPathResolveRequest follow = {};
        follow.actorIndex = 34;
        follow.target = {2798.114014f, 7245.755371f, -1920.0f};
        follow.object.radius = body.radius;
        follow.object.height = body.height;
        follow.object.stepLength = 40.0f;
        follow.object.dropHeight = IndoorActorMaxDropHeight;
        follow.allowDirect = false;
        follow.waypointReachDistance = 32.0f;
        bool arrived = false;
        for (int step = 0; step < 5 * 128; ++step)
        {
            if (std::hypot(follow.target.x - state.x, follow.target.y - state.y) < 128.0f)
            {
                arrived = true;
                break;
            }
            follow.source = {state.x, state.y, state.footZ};
            follow.preferredSourceFacetSourceId = state.grounded ? int32_t(state.supportFaceIndex) : -1;
            follow.nowSeconds = step / 128.0;
            const ActorPathResolveResult path = runtime.resolveWaypoint(build.pathMap, follow);
            REQUIRE(path.pathActive);
            const float deltaX = path.waypoint.x - state.x;
            const float deltaY = path.waypoint.y - state.y;
            const float distance = std::hypot(deltaX, deltaY);
            REQUIRE(distance > 0.0f);
            state = controller.resolveMove(state, body, deltaX / distance * 300.0f, deltaY / distance * 300.0f,
                false, 1.0f / 128.0f, nullptr, 34, false, nullptr, false, false, 420.0f, 1.0f,
                false, false, true, true, true);
        }
        INFO("final position=" << state.x << "," << state.y << "," << state.footZ);
        CHECK(arrived);
        CHECK(state.grounded);
        CHECK_EQ(state.footZ, doctest::Approx(follow.target.z));
    }
}

TEST_CASE("temple of baa doorway admits a body equal to its height")
{
    using namespace OpenYAMM::Game;
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader loader = regressionMapLoader().gameDataLoader;
    REQUIRE(loader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "d04.blv"));
    const MapAssetInfo &map = *loader.getSelectedMap();
    const IndoorMapData &geometry = *map.indoorMapData;
    const IndoorMovementController controller(geometry, &map.indoorMapDeltaData, nullptr);
    const IndoorPathMapBuildResult build = IndoorPathfindingBuilder::buildPathMap(geometry, geometry.vertices);
    for (float height : {255.0f, 256.0f, 257.0f})
    {
        CAPTURE(height);
        const IndoorBodyDimensions body{127.0f, height};
        PathObject object;
        object.radius = body.radius;
        object.height = body.height;
        object.stepLength = 40.0f;
        object.dropHeight = IndoorActorMaxDropHeight;
        const PathPoint source{2111.0f, 2816.0f, -1120.0f};
        const PathPoint target{1620.0f, 2816.0f, -1120.0f};
        CHECK_EQ(build.pathMap.traceWalkSegment(source, target, object), height <= 256.0f);
        IndoorMoveState state = controller.initializeStateFromEyePosition(
            source.x, source.y, source.z + body.height, body);
        for (int step = 0; step < 2 * 128 && state.x > target.x; ++step)
        {
            state = controller.resolveMove(state, body, -300.0f, 0.0f,
                false, 1.0f / 128.0f, nullptr, 53, false, nullptr, false, false, 420.0f, 1.0f,
                false, false, false, false, true);
        }
        CHECK_EQ(state.x <= target.x, height <= 256.0f);
        CHECK_EQ(state.footZ, doctest::Approx(source.z));
    }
}

TEST_CASE("temple of baa actors follow doorway routes when the party position cannot fit their bodies")
{
    using namespace OpenYAMM::Game;
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader loader = regressionMapLoader().gameDataLoader;
    REQUIRE(loader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "d04.blv"));
    const MapAssetInfo &map = *loader.getSelectedMap();
    const IndoorMapData &geometry = *map.indoorMapData;
    const IndoorMovementController controller(geometry, &map.indoorMapDeltaData, nullptr);
    const IndoorPathMapBuildResult build = IndoorPathfindingBuilder::buildPathMap(geometry, geometry.vertices);
    IndoorMoveState state = {};
    IndoorBodyDimensions body;
    size_t actorIndex = 0;
    float speed = 0.0f;
    SUBCASE("BAA_3 High Priest of Baa")
    {
        actorIndex = 34;
        state.x = 2058.0f;
        state.y = 3153.330322f;
        body = {74.0f, 190.0f};
        speed = 300.0f;
    }
    SUBCASE("BAA_3 Venemous Spider")
    {
        actorIndex = 53;
        state.x = 2111.0f;
        state.y = 3368.097412f;
        body = {127.0f, 256.0f};
        speed = 735.0f;
    }
    state.footZ = -1120.0f;
    state.eyeHeight = body.height;
    state.sectorId = 7;
    state.eyeSectorId = 7;
    state.supportFaceIndex = 604;
    state.grounded = true;
    ActorPathRuntime runtime;
    ActorPathResolveRequest follow = {};
    follow.actorIndex = actorIndex;
    follow.target = {1025.653687f, 3256.596436f, -1120.0f};
    follow.object.radius = body.radius;
    follow.object.height = body.height;
    follow.object.stepLength = 40.0f;
    follow.object.dropHeight = IndoorActorMaxDropHeight;
    follow.allowDirect = false;
    follow.allowPartialPath = true;
    follow.waypointReachDistance = std::max(32.0f, body.radius * 0.35f);
    // The spider's partial route ends inside the room, before the stone bier.
    // Runtime collision sliding can continue around its rounded edge afterward.
    const PathPoint arrivalPoint = actorIndex == 53 ? PathPoint{1599.0f, 2816.0f, -1120.0f} : follow.target;
    const float arrivalDistance = actorIndex == 53 ? follow.waypointReachDistance : 256.0f;
    bool entered = false;
    bool partialPath = false;
    for (int step = 0; step < 12 * 128; ++step)
    {
        if (state.x < 1664.0f && std::hypot(arrivalPoint.x - state.x, arrivalPoint.y - state.y) <= arrivalDistance)
        {
            entered = true;
            break;
        }
        follow.source = {state.x, state.y, state.footZ};
        follow.preferredSourceFacetSourceId = state.grounded ? int32_t(state.supportFaceIndex) : -1;
        follow.nowSeconds = step / 128.0;
        const ActorPathResolveResult path = runtime.resolveWaypoint(build.pathMap, follow);
        INFO("step=" << step << " position=" << state.x << "," << state.y << "," << state.footZ);
        REQUIRE(path.pathActive);
        partialPath = partialPath || path.planStatus == PathPlanStatus::Partial;
        const float deltaX = path.waypoint.x - state.x;
        const float deltaY = path.waypoint.y - state.y;
        const float distance = std::hypot(deltaX, deltaY);
        REQUIRE(distance > 0.0f);
        state = controller.resolveMove(state, body, deltaX / distance * speed, deltaY / distance * speed,
            false, 1.0f / 128.0f, nullptr, actorIndex, false, nullptr, false, false, 420.0f, 1.0f,
            false, false, true, true, true);
    }
    INFO("final position=" << state.x << "," << state.y << "," << state.footZ);
    CHECK(partialPath);
    CHECK(entered);
    CHECK(state.grounded);
    CHECK_EQ(state.footZ, doctest::Approx(follow.target.z));
}

TEST_CASE("naga vault actors enter the hallway over its low threshold")
{
    using namespace OpenYAMM::Game;
    using namespace OpenYAMM::Tests;
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());
    GameDataLoader loader = regressionMapLoader().gameDataLoader;
    REQUIRE(loader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "d18.blv"));
    const MapAssetInfo &map = *loader.getSelectedMap();
    const IndoorMapData &geometry = *map.indoorMapData;
    const IndoorMovementController controller(geometry, &map.indoorMapDeltaData, nullptr);
    const IndoorPathMapBuildResult build = IndoorPathfindingBuilder::buildPathMap(geometry, geometry.vertices);
    IndoorMoveState state = {};
    IndoorBodyDimensions body;
    size_t actorIndex = 0;
    float speed = 0.0f;
    SUBCASE("NV_1 Naga")
    {
        actorIndex = 7;
        state.x = -280.343292f;
        state.y = -627.092651f;
        body = {90.0f, 182.0f};
        speed = 277.5f;
    }
    SUBCASE("NV_1 Serpentman Elder")
    {
        actorIndex = 17;
        state.x = -113.231079f;
        state.y = -832.416809f;
        body = {110.0f, 222.0f};
        speed = 375.0f;
    }
    state.footZ = -144.0f;
    state.eyeHeight = body.height;
    state.sectorId = 1;
    state.eyeSectorId = 1;
    state.supportFaceIndex = 13;
    state.grounded = true;
    ActorPathResolveRequest follow = {};
    follow.actorIndex = actorIndex;
    follow.target = {-512.0f, -256.0f, -128.0f};
    follow.object.radius = body.radius;
    follow.object.height = body.height;
    follow.object.stepLength = 40.0f;
    follow.object.dropHeight = IndoorActorMaxDropHeight;
    follow.allowDirect = false;
    follow.waypointReachDistance = 32.0f;
    CHECK(build.pathMap.traceWalkSegment({-512.0f, -700.0f, -144.0f}, follow.target, follow.object));
    ActorPathRuntime runtime;
    bool arrived = false;
    for (int step = 0; step < 4 * 128; ++step)
    {
        if (std::hypot(follow.target.x - state.x, follow.target.y - state.y) <= 64.0f)
        {
            arrived = true;
            break;
        }
        follow.source = {state.x, state.y, state.footZ};
        follow.preferredSourceFacetSourceId = state.grounded ? int32_t(state.supportFaceIndex) : -1;
        follow.nowSeconds = step / 128.0;
        const ActorPathResolveResult path = runtime.resolveWaypoint(build.pathMap, follow);
        INFO("step=" << step << " position=" << state.x << "," << state.y << "," << state.footZ);
        REQUIRE(path.pathActive);
        const float deltaX = path.waypoint.x - state.x;
        const float deltaY = path.waypoint.y - state.y;
        const float distance = std::hypot(deltaX, deltaY);
        REQUIRE(distance > 0.0f);
        state = controller.resolveMove(state, body, deltaX / distance * speed, deltaY / distance * speed,
            false, 1.0f / 128.0f, nullptr, actorIndex, false, nullptr, false, false, 420.0f, 1.0f,
            false, false, false, false, true);
    }
    CHECK(arrived);
    CHECK(state.grounded);
    CHECK_EQ(state.footZ, doctest::Approx(follow.target.z));
}

TEST_SUITE_END();
