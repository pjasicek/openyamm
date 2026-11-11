#include "doctest/doctest.h"

#include "game/pathfinding/PathPlanner.h"

#include <algorithm>
#include <cmath>
#include <vector>

using OpenYAMM::Game::PathFacet;
using OpenYAMM::Game::PathFacetKind;
using OpenYAMM::Game::PathMap;
using OpenYAMM::Game::PathObject;
using OpenYAMM::Game::PathPlanRequest;
using OpenYAMM::Game::PathPlanResult;
using OpenYAMM::Game::PathPlanStatus;
using OpenYAMM::Game::PathPlanner;
using OpenYAMM::Game::PathPoint;

namespace
{
PathFacet makePlannerFloor(float minX, float maxX, float minY, float maxY, float z)
{
    PathFacet facet = {};
    facet.kind = PathFacetKind::Floor;
    facet.blocking = false;
    facet.walkableFloor = true;
    facet.vertices = {
        {minX, minY, z},
        {maxX, minY, z},
        {maxX, maxY, z},
        {minX, maxY, z}
    };
    return facet;
}

PathFacet makePlannerWall(float x, float minY, float maxY, float minZ, float maxZ)
{
    PathFacet facet = {};
    facet.kind = PathFacetKind::Wall;
    facet.blocking = true;
    facet.vertices = {
        {x, minY, minZ},
        {x, maxY, minZ},
        {x, maxY, maxZ},
        {x, minY, maxZ}
    };
    return facet;
}

PathObject makeGroundObject()
{
    PathObject object = {};
    object.radius = 8.0f;
    object.stepLength = 24.0f;
    object.stepHeight = 40.0f;
    return object;
}

PathPlanRequest makeRequest()
{
    PathPlanRequest request = {};
    request.object = makeGroundObject();
    request.nodeLimit = 8000;
    return request;
}
}

TEST_CASE("path planner routes ground movement around a wall")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makePlannerWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });

    PathPlanRequest request = makeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    REQUIRE(result.status == PathPlanStatus::Success);
    REQUIRE(result.waypoints.size() > 1);
    CHECK(result.analyzedNodeCount > 0u);
    CHECK(std::fabs(result.waypoints.back().x - request.target.x) < 0.001f);
    CHECK(std::fabs(result.waypoints.back().y - request.target.y) < 0.001f);
}

TEST_CASE("path planner ends a route within the goal distance of a point the body cannot reach")
{
    // A corridor's end wall at x 200; the point lies 10 from it, inside the body's 42 (Thjorad Mine's MMarker2 for
    // Hjarrand), and a wall in the corridor stands between it and the start.
    PathMap map;
    map.setFacets({
        makePlannerFloor(-200.0f, 200.0f, -200.0f, 200.0f, 0.0f),
        makePlannerWall(200.0f, -200.0f, 200.0f, 0.0f, 200.0f),
        makePlannerWall(60.0f, -80.0f, 80.0f, 0.0f, 200.0f)
    });

    PathPlanRequest request = makeRequest();
    request.object.radius = 42.0f;
    request.object.stepLength = 40.0f;
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {190.0f, 0.0f, 0.0f};
    request.goalDistance = 42.0f;

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    REQUIRE(result.status == PathPlanStatus::Success);
    REQUIRE_FALSE(result.waypoints.empty());
    const PathPoint &end = result.waypoints.back();
    CHECK(std::hypot(end.x - request.target.x, end.y - request.target.y) <= request.goalDistance);
    CHECK(end.x <= 200.0f - request.object.radius + 0.5f);
    CHECK(result.waypoints.size() < 20u);
}

TEST_CASE("path planner snaps elevated ground target to floor")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(-48.0f, 192.0f, -48.0f, 48.0f, 0.0f)
    });

    PathPlanRequest request = makeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 300.0f};

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    REQUIRE(result.status == PathPlanStatus::Success);
    REQUIRE_FALSE(result.waypoints.empty());
    CHECK(std::fabs(result.waypoints.back().x - request.target.x) < 0.001f);
    CHECK(std::fabs(result.waypoints.back().y - request.target.y) < 0.001f);
    CHECK(std::fabs(result.waypoints.back().z) < 0.001f);
}

TEST_CASE("path planner returns no route across missing floor")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(-48.0f, 48.0f, -48.0f, 48.0f, 0.0f),
        makePlannerFloor(192.0f, 288.0f, -48.0f, 48.0f, 0.0f)
    });

    PathPlanRequest request = makeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {240.0f, 0.0f, 0.0f};

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    CHECK(result.status == PathPlanStatus::NoRoute);
}

TEST_CASE("path planner can return best partial route when requested")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(-48.0f, 48.0f, -48.0f, 48.0f, 0.0f),
        makePlannerFloor(192.0f, 288.0f, -48.0f, 48.0f, 0.0f)
    });

    PathPlanRequest request = makeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {240.0f, 0.0f, 0.0f};
    request.allowPartialPath = true;

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    CHECK(result.status == PathPlanStatus::Partial);
    REQUIRE_FALSE(result.waypoints.empty());
    CHECK(result.waypoints.back().x > request.source.x);
    CHECK(result.waypoints.back().x < request.target.x);
}

TEST_CASE("path planner can return partial route toward target with no floor")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(-48.0f, 192.0f, -48.0f, 48.0f, 0.0f)
    });

    PathPlanRequest request = makeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {240.0f, 0.0f, 0.0f};
    request.allowPartialPath = true;

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    CHECK(result.status == PathPlanStatus::Partial);
    REQUIRE_FALSE(result.waypoints.empty());
    CHECK(result.waypoints.back().x > request.source.x);
    CHECK(result.waypoints.back().x < request.target.x);
}

TEST_CASE("path planner can recover source from nearby no-floor position when requested")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(-48.0f, 192.0f, -48.0f, 48.0f, 0.0f)
    });

    PathPlanRequest request = makeRequest();
    request.source = {240.0f, 0.0f, 0.0f};
    request.target = {0.0f, 0.0f, 0.0f};

    PathPlanner planner;
    const PathPlanResult blockedResult = planner.plan(map, request);
    CHECK(blockedResult.status == PathPlanStatus::NoRoute);

    request.sourceSnapDistance = 96.0f;
    const PathPlanResult recoveredResult = planner.plan(map, request);

    CHECK(recoveredResult.status == PathPlanStatus::Success);
    CHECK(recoveredResult.debug.sourceValid);
    CHECK(recoveredResult.debug.preferredSourceSnapUsed);
    CHECK(recoveredResult.debug.snappedSource.x < request.source.x);
    REQUIRE_FALSE(recoveredResult.waypoints.empty());
}

TEST_CASE("path planner aligns ground steps with narrow passage clearance")
{
    for (const float halfWidth : {128.0f, 126.0f})
    {
        CAPTURE(halfWidth);
        PathMap map;
        map.setFacets({
            makePlannerFloor(-400.0f, 400.0f, -200.0f, 1000.0f, 0.0f),
            makePlannerWall(-halfWidth, 200.0f, 1000.0f, 0.0f, 300.0f),
            makePlannerWall(halfWidth, 200.0f, 1000.0f, 0.0f, 300.0f)
        });
        for (const float offset : {2.645f, 7.9f, -7.9f})
        {
            CAPTURE(offset);
            PathPlanRequest request = makeRequest();
            request.source = {offset, 0.0f, 0.0f};
            request.target = {0.0f, 800.0f, 0.0f};
            request.object.radius = 127.0f;
            request.object.stepLength = 40.0f;
            request.allowDirect = false;
            PathPlanner planner;
            const PathPlanResult result = planner.plan(map, request);
            if (halfWidth < request.object.radius)
            {
                CHECK_EQ(result.status, PathPlanStatus::NoRoute);
                continue;
            }
            REQUIRE_EQ(result.status, PathPlanStatus::Success);
            REQUIRE_FALSE(result.waypoints.empty());
            for (const OpenYAMM::Game::PathPoint &waypoint : result.waypoints)
            {
                if (waypoint.y > 300.0f && waypoint.y < 900.0f)
                {
                    CHECK_LE(std::fabs(waypoint.x) + request.object.radius, halfWidth + 0.001f);
                }
            }
        }
    }
}

TEST_CASE("path planner respects independent rise and drop limits")
{
    PathPlanRequest request = makeRequest();
    request.object.dropHeight = 100.0f;
    request.allowDirect = false;
    for (const float drop : {96.0f, 100.0f, 101.0f})
    {
        CAPTURE(drop);
        PathMap map;
        map.setFacets({
            makePlannerFloor(-48.0f, 48.0f, -48.0f, 48.0f, drop),
            makePlannerFloor(48.0f, 192.0f, -48.0f, 48.0f, 0.0f)
        });
        request.source = {0.0f, 0.0f, drop};
        request.target = {144.0f, 0.0f, 0.0f};
        PathPlanner planner;
        CHECK_EQ(planner.plan(map, request).status, drop <= 100.0f ? PathPlanStatus::Success : PathPlanStatus::NoRoute);
        request.source = {144.0f, 0.0f, 0.0f};
        request.target = {0.0f, 0.0f, drop};
        CHECK_EQ(planner.plan(map, request).status, PathPlanStatus::NoRoute);
    }
}

TEST_CASE("path planner accepts stairs within step height")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(0.0f, 48.0f, -48.0f, 48.0f, 0.0f),
        makePlannerFloor(48.0f, 96.0f, -48.0f, 48.0f, 24.0f),
        makePlannerFloor(96.0f, 144.0f, -48.0f, 48.0f, 48.0f)
    });

    PathPlanRequest request = makeRequest();
    request.object.stepHeight = 32.0f;
    request.source = {24.0f, 0.0f, 0.0f};
    request.target = {120.0f, 0.0f, 48.0f};

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    CHECK(result.status == PathPlanStatus::Success);
}

TEST_CASE("path planner rejects stairs above step height")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(0.0f, 72.0f, -48.0f, 48.0f, 0.0f),
        makePlannerFloor(72.0f, 144.0f, -48.0f, 48.0f, 80.0f)
    });

    PathPlanRequest request = makeRequest();
    request.source = {24.0f, 0.0f, 0.0f};
    request.target = {120.0f, 0.0f, 80.0f};

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    CHECK(result.status == PathPlanStatus::NoRoute);
}

TEST_CASE("path planner lets flying movement pass over low ground obstacles")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(-48.0f, 192.0f, -48.0f, 48.0f, 0.0f),
        makePlannerWall(72.0f, -24.0f, 24.0f, 0.0f, 20.0f)
    });

    PathPlanRequest request = makeRequest();
    request.object.canFly = true;
    request.source = {0.0f, 0.0f, 80.0f};
    request.target = {144.0f, 0.0f, 80.0f};

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    REQUIRE(result.status == PathPlanStatus::Success);
    REQUIRE_EQ(result.waypoints.size(), 1u);
    CHECK(std::fabs(result.waypoints.front().z - 80.0f) < 0.001f);
}

TEST_CASE("path planner takes a flyer under a door's lintel instead of into the wall above it")
{
    // Two rooms joined by a doorway 80 wide and 120 high in the wall at x = 72.
    PathMap map;
    map.setFacets({
        makePlannerFloor(-48.0f, 192.0f, -160.0f, 160.0f, 0.0f),
        makePlannerWall(72.0f, -160.0f, -40.0f, 0.0f, 320.0f),
        makePlannerWall(72.0f, 40.0f, 160.0f, 0.0f, 320.0f),
        makePlannerWall(72.0f, -40.0f, 40.0f, 120.0f, 320.0f)
    });

    PathPlanRequest request = makeRequest();
    request.object.canFly = true;
    request.object.radius = 16.0f;
    request.object.height = 80.0f;
    // Its feet clear the lintel at this height, its back does not.
    request.source = {0.0f, 0.0f, 90.0f};
    request.target = {144.0f, 0.0f, 90.0f};
    CHECK_FALSE(map.canReachDirectly(request.source, request.target, request.object));

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    REQUIRE(result.status == PathPlanStatus::Success);
    REQUIRE(result.waypoints.size() > 1);
    PathPoint previous = request.source;

    for (const PathPoint &waypoint : result.waypoints)
    {
        CHECK(map.canReachDirectly(previous, waypoint, request.object));
        previous = waypoint;
    }

    const bool passesUnderLintel = std::any_of(result.waypoints.begin(), result.waypoints.end(),
        [](const PathPoint &waypoint)
        {
            // The top of the body is traced 4 below its height.
            return std::fabs(waypoint.x - 72.0f) <= 48.0f && waypoint.z + 76.0f <= 120.0f;
        });
    CHECK(passesUnderLintel);
}

TEST_CASE("a flyer cannot drop straight down through a crack between two floor faces")
{
    // A ledge at 288 made of two faces with a hairline crack between them at x = 0, as in Goblinwatch, where a route
    // dropped through it.
    PathFacet left = makePlannerFloor(-160.0f, -0.25f, -160.0f, 160.0f, 288.0f);
    PathFacet right = makePlannerFloor(0.25f, 160.0f, -160.0f, 160.0f, 288.0f);
    left.blocking = true;
    right.blocking = true;
    PathMap map;
    map.setFacets({left, right});

    PathObject object = makeGroundObject();
    object.canFly = true;
    object.radius = 59.0f;
    object.height = 109.0f;
    CHECK_FALSE(map.canReachDirectly({0.0f, 0.0f, 338.0f}, {0.0f, 0.0f, 102.0f}, object));
}

TEST_CASE("path planner reports node limit failure before unbounded searches")
{
    PathMap map;
    map.setFacets({
        makePlannerFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makePlannerWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });

    PathPlanRequest request = makeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.nodeLimit = 1;

    PathPlanner planner;
    const PathPlanResult result = planner.plan(map, request);

    CHECK(result.status == PathPlanStatus::NodeLimitExceeded);
}
