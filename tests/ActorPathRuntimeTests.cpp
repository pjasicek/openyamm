#include "doctest/doctest.h"

#include "game/pathfinding/ActorPathRuntime.h"

#include <array>
#include <chrono>
#include <cmath>
#include <memory>
#include <thread>
#include <vector>

using OpenYAMM::Game::ActorPathResolveRequest;
using OpenYAMM::Game::ActorPathResolveResult;
using OpenYAMM::Game::ActorPathRuntime;
using OpenYAMM::Game::PathFacet;
using OpenYAMM::Game::PathFacetKind;
using OpenYAMM::Game::PathMap;
using OpenYAMM::Game::PathObject;
using OpenYAMM::Game::PathPoint;
using OpenYAMM::Game::PathPlanner;
using OpenYAMM::Game::PathPlanRequest;
using OpenYAMM::Game::PathPlanStatus;

namespace
{
PathFacet makeRuntimeFloor(float minX, float maxX, float minY, float maxY, float z)
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

PathFacet makeRuntimeWall(float x, float minY, float maxY, float minZ, float maxZ)
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

PathObject makeRuntimeObject()
{
    PathObject object = {};
    object.radius = 8.0f;
    object.stepLength = 24.0f;
    object.stepHeight = 40.0f;
    return object;
}

ActorPathResolveRequest makeRuntimeRequest()
{
    ActorPathResolveRequest request = {};
    request.object = makeRuntimeObject();
    request.nodeLimit = 8000;
    request.waypointReachDistance = request.object.radius;
    return request;
}

float runtimeDistance2d(const PathPoint &from, const PathPoint &to)
{
    const float dx = to.x - from.x;
    const float dy = to.y - from.y;
    return std::sqrt(dx * dx + dy * dy);
}
}

TEST_CASE("actor path runtime keeps direct movement when target is reachable")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -48.0f, 48.0f, 0.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();

    ActorPathRuntime runtime;
    const ActorPathResolveResult result = runtime.resolveWaypoint(map, request);

    CHECK(result.directReachable);
    CHECK_FALSE(result.pathActive);
    CHECK_FALSE(result.planned);
}

TEST_CASE("actor path runtime caches direct reachability until movement or interval requires another check")
{
    PathMap map;
    map.setFacets({makeRuntimeFloor(-48.0f, 256.0f, -48.0f, 48.0f, 0.0f)});
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();

    ActorPathRuntime runtime;
    const ActorPathResolveResult first = runtime.resolveWaypoint(map, request);
    REQUIRE(first.directReachable);
    CHECK(first.directChecked);

    request.nowSeconds = 0.1;
    request.source.x += 4.0f;
    request.target.x += 4.0f;
    const ActorPathResolveResult cached = runtime.resolveWaypoint(map, request);
    CHECK(cached.directReachable);
    CHECK_FALSE(cached.directChecked);
    CHECK_FALSE(cached.planned);
    CHECK_FALSE(cached.queued);
    CHECK_FALSE(runtime.actorHasActivePath(request.actorIndex));

    request.nowSeconds = request.directCheckIntervalSeconds;
    const ActorPathResolveResult expired = runtime.resolveWaypoint(map, request);
    CHECK(expired.directReachable);
    CHECK(expired.directChecked);
}

TEST_CASE("actor path runtime retains a distant valid route between straight line checks")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 1400.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.distantRouteReuseDistance = 100.0f;
    request.shortcutCheckIntervalSeconds = 100.0;
    ActorPathRuntime runtime;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    REQUIRE(planned.planned);
    REQUIRE(planned.pathActive);
    REQUIRE_FALSE(planned.directReachable);

    request.nowSeconds = 0.1;
    request.source.y += 16.0f;
    request.target.y += 16.0f;
    const ActorPathResolveResult retained = runtime.resolveWaypoint(map, request);
    REQUIRE(retained.pathActive);
    CHECK_FALSE(retained.directChecked);
    CHECK_FALSE(retained.planned);
    CHECK_FALSE(retained.directReachable);

    SUBCASE("movement does not extend the one second check deadline")
    {
        request.nowSeconds = 0.99;
        request.target.y += 16.0f;
        CHECK_FALSE(runtime.resolveWaypoint(map, request).directChecked);
        request.nowSeconds = 1.0;
        CHECK(runtime.resolveWaypoint(map, request).directChecked);
    }
    SUBCASE("nearby targets refresh immediately after endpoint movement")
    {
        request.distantRouteReuseDistance = 200.0f;
        CHECK(runtime.resolveWaypoint(map, request).directChecked);
    }
    SUBCASE("a large target displacement refreshes immediately")
    {
        request.target.x += 1100.0f;
        CHECK(runtime.resolveWaypoint(map, request).directChecked);
    }
    SUBCASE("collision size changes refresh immediately")
    {
        request.object.radius += 1.0f;
        CHECK(runtime.resolveWaypoint(map, request).directChecked);
    }
    SUBCASE("opening a door invalidates the route immediately")
    {
        map.setFacets({makeRuntimeFloor(-48.0f, 1400.0f, -120.0f, 120.0f, 0.0f)});
        request.mapRevision = map.revision();
        const ActorPathResolveResult opened = runtime.resolveWaypoint(map, request);
        CHECK(opened.directChecked);
        CHECK(opened.directReachable);
        CHECK_FALSE(opened.pathActive);
    }
}

TEST_CASE("actor path runtime rechecks a cached direct route when either endpoint moves off it")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 256.0f, -256.0f, 256.0f, 0.0f),
        makeRuntimeWall(72.0f, 48.0f, 256.0f, 0.0f, 128.0f)
    });
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.allowPlan = false;
    ActorPathRuntime runtime;
    REQUIRE(runtime.resolveWaypoint(map, request).directReachable);

    request.nowSeconds = 0.01;
    SUBCASE("source movement")
    {
        request.source.y = 192.0f;
    }
    SUBCASE("target movement")
    {
        request.target.y = 192.0f;
    }
    const ActorPathResolveResult changed = runtime.resolveWaypoint(map, request);
    CHECK(changed.directChecked);
    CHECK_FALSE(changed.directReachable);
    CHECK(changed.deferred);
}

TEST_CASE("actor path runtime rechecks cached reachability when the collision object changes")
{
    PathMap map;
    map.setFacets({makeRuntimeFloor(-48.0f, 256.0f, -48.0f, 48.0f, 0.0f)});
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    ActorPathRuntime runtime;
    REQUIRE(runtime.resolveWaypoint(map, request).directReachable);
    request.nowSeconds = 0.01;

    SUBCASE("flight")
    {
        request.object.canFly = true;
    }
    SUBCASE("radius")
    {
        request.object.radius += 1.0f;
    }
    SUBCASE("height")
    {
        request.object.height += 1.0f;
    }
    SUBCASE("step length")
    {
        request.object.stepLength += 1.0f;
    }
    SUBCASE("step height")
    {
        request.object.stepHeight += 1.0f;
    }
    SUBCASE("drop height")
    {
        request.object.dropHeight += 1.0f;
    }
    CHECK(runtime.resolveWaypoint(map, request).directChecked);
}

TEST_CASE("actor path runtime rejects cached direct movement after geometry changes")
{
    PathMap map;
    const PathFacet floor = makeRuntimeFloor(-48.0f, 256.0f, -48.0f, 48.0f, 0.0f);
    map.setFacets({floor});
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.allowPlan = false;
    ActorPathRuntime runtime;
    REQUIRE(runtime.resolveWaypoint(map, request).directReachable);

    map.setFacets({floor, makeRuntimeWall(72.0f, -48.0f, 48.0f, 0.0f, 128.0f)});
    request.mapRevision = map.revision();
    request.nowSeconds = 0.01;
    const ActorPathResolveResult changed = runtime.resolveWaypoint(map, request);
    CHECK(changed.directChecked);
    CHECK_FALSE(changed.directReachable);
    CHECK(changed.deferred);
}

TEST_CASE("actor path runtime invalidates cached direct movement when movement is blocked")
{
    PathMap map;
    map.setFacets({makeRuntimeFloor(-48.0f, 256.0f, -48.0f, 48.0f, 0.0f)});
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    ActorPathRuntime runtime;
    REQUIRE(runtime.resolveWaypoint(map, request).directReachable);

    request.nowSeconds = 0.01;
    request.allowDirect = false;
    const ActorPathResolveResult blocked = runtime.resolveWaypoint(map, request);
    CHECK_FALSE(blocked.directReachable);
    CHECK_FALSE(blocked.directChecked);
    CHECK(blocked.pathActive);

    request.nowSeconds = 0.02;
    request.allowDirect = true;
    const ActorPathResolveResult unblocked = runtime.resolveWaypoint(map, request);
    CHECK(unblocked.directChecked);
    CHECK(unblocked.directReachable);
    CHECK_FALSE(runtime.actorHasActivePath(request.actorIndex));
}

TEST_CASE("actor path runtime caches blocked direct checks while planning is deferred")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 256.0f, -48.0f, 48.0f, 0.0f),
        makeRuntimeWall(72.0f, -48.0f, 48.0f, 0.0f, 128.0f)
    });
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.allowPlan = false;
    ActorPathRuntime runtime;
    CHECK(runtime.resolveWaypoint(map, request).directChecked);

    request.nowSeconds = 0.1;
    const ActorPathResolveResult cached = runtime.resolveWaypoint(map, request);
    CHECK_FALSE(cached.directChecked);
    CHECK_FALSE(cached.directReachable);
    CHECK(cached.deferred);

    request.nowSeconds = 0.25;
    CHECK(runtime.resolveWaypoint(map, request).directChecked);
}

TEST_CASE("actor path runtime clears cached direct checks on actor or map reset")
{
    PathMap map;
    map.setFacets({makeRuntimeFloor(-48.0f, 256.0f, -48.0f, 48.0f, 0.0f)});
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    ActorPathRuntime runtime;
    REQUIRE(runtime.resolveWaypoint(map, request).directReachable);
    SUBCASE("actor reset")
    {
        runtime.resetActor(request.actorIndex);
    }
    SUBCASE("map reset")
    {
        runtime.clear();
    }
    request.nowSeconds = 0.01;
    CHECK(runtime.resolveWaypoint(map, request).directChecked);
}

TEST_CASE("actor path runtime can force planning after direct movement is rejected")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -48.0f, 48.0f, 0.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.allowDirect = false;

    ActorPathRuntime runtime;
    const ActorPathResolveResult result = runtime.resolveWaypoint(map, request);

    CHECK_FALSE(result.directReachable);
    REQUIRE(result.pathActive);
    CHECK(result.planned);
    CHECK_EQ(result.waypointIndex, 0);
    CHECK(std::fabs(result.waypoint.x - request.target.x) > 0.001f);
}

TEST_CASE("actor path runtime plans a waypoint when direct movement is blocked")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();

    ActorPathRuntime runtime;
    const ActorPathResolveResult result = runtime.resolveWaypoint(map, request);

    CHECK_FALSE(result.directReachable);
    REQUIRE(result.pathActive);
    CHECK(result.planned);
    CHECK(result.waypointIndex < result.waypointCount);
    const bool waypointMoved =
        std::fabs(result.waypoint.x - request.source.x) > 0.001f
        || std::fabs(result.waypoint.y - request.source.y) > 0.001f;
    CHECK(waypointMoved);
}

TEST_CASE("actor path runtime applies failed route cooldown")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(192.0f, 288.0f, -48.0f, 48.0f, 0.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {240.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    request.failedRetrySeconds = 5.0;

    ActorPathRuntime runtime;
    const ActorPathResolveResult failed = runtime.resolveWaypoint(map, request);
    CHECK(failed.failed);
    CHECK(failed.planned);

    request.nowSeconds = 12.0;
    const ActorPathResolveResult cooldown = runtime.resolveWaypoint(map, request);
    CHECK(cooldown.cooldown);
    CHECK_FALSE(cooldown.planned);
}

TEST_CASE("actor path runtime can follow opt-in partial route toward target with no floor")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -48.0f, 48.0f, 0.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {240.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.allowPartialPath = true;

    ActorPathRuntime runtime;
    const ActorPathResolveResult result = runtime.resolveWaypoint(map, request);

    CHECK_FALSE(result.directReachable);
    REQUIRE(result.pathActive);
    CHECK(result.planned);
    CHECK_FALSE(result.failed);
    CHECK_EQ(result.planStatus, PathPlanStatus::Partial);
    CHECK(result.waypoint.x > request.source.x);
    CHECK(result.waypoint.x < request.target.x);
}

TEST_CASE("actor path runtime can recover source from nearby no-floor position")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -48.0f, 48.0f, 0.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {240.0f, 0.0f, 0.0f};
    request.target = {0.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.sourceSnapDistance = 96.0f;

    ActorPathRuntime runtime;
    const ActorPathResolveResult result = runtime.resolveWaypoint(map, request);

    CHECK_FALSE(result.directReachable);
    REQUIRE(result.pathActive);
    CHECK(result.planned);
    CHECK_FALSE(result.failed);
    CHECK_EQ(result.planStatus, PathPlanStatus::Success);
    CHECK(result.waypoint.x < request.source.x);
    CHECK(result.waypoint.x > request.target.x);
}

TEST_CASE("actor path runtime uses best reachable point after first failed route")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-96.0f, 240.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -120.0f, 120.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {192.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    request.failedRetrySeconds = 5.0;

    ActorPathRuntime runtime;
    const ActorPathResolveResult failed = runtime.resolveWaypoint(map, request);
    CHECK(failed.failed);
    CHECK(failed.planned);
    REQUIRE(failed.pathActive);
    CHECK(failed.waypoint.x > request.source.x);

    request.nowSeconds = 12.0;
    const ActorPathResolveResult recovery = runtime.resolveWaypoint(map, request);
    CHECK_FALSE(recovery.cooldown);
    REQUIRE(recovery.pathActive);
    CHECK(recovery.waypoint.x == doctest::Approx(failed.waypoint.x));
}

TEST_CASE("actor path runtime drops stalled recovery best waypoint")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-96.0f, 240.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -120.0f, 120.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {192.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    request.failedRetrySeconds = 5.0;
    request.directCheckIntervalSeconds = 100.0;
    request.shortcutCheckIntervalSeconds = 100.0;

    ActorPathRuntime runtime;
    const ActorPathResolveResult failed = runtime.resolveWaypoint(map, request);
    REQUIRE(failed.failed);
    REQUIRE(failed.pathActive);

    request.source = {
        failed.waypoint.x - 20.0f,
        failed.waypoint.y,
        failed.waypoint.z
    };

    request.nowSeconds = 10.10;
    ActorPathResolveResult active = runtime.resolveWaypoint(map, request);
    REQUIRE(active.pathActive);

    request.nowSeconds = 10.60;
    const ActorPathResolveResult stalled = runtime.resolveWaypoint(map, request);
    CHECK(stalled.stalledWaypointCount == 1);
    CHECK_FALSE(stalled.pathActive);

    request.nowSeconds = 11.00;
    const ActorPathResolveResult cooldown = runtime.resolveWaypoint(map, request);
    CHECK(cooldown.cooldown);
    CHECK_FALSE(cooldown.pathActive);
}

TEST_CASE("actor path runtime defers blocked route planning when plan budget is exhausted")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    request.allowPlan = false;

    ActorPathRuntime runtime;
    const ActorPathResolveResult deferred = runtime.resolveWaypoint(map, request);
    CHECK(deferred.deferred);
    CHECK_FALSE(deferred.planned);
    CHECK_FALSE(deferred.pathActive);

    request.nowSeconds = 10.01;
    request.allowPlan = true;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    CHECK(planned.planned);
    CHECK(planned.pathActive);
}

TEST_CASE("actor path runtime can finish blocked route planning on a worker thread")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;

    ActorPathRuntime runtime;
    runtime.setWorkerCount(1);

    const ActorPathResolveResult queued = runtime.resolveWaypoint(map, request);
    CHECK(queued.queued);
    CHECK(queued.requested);
    CHECK(queued.deferred);
    CHECK_FALSE(queued.planned);
    CHECK_FALSE(queued.pathActive);

    ActorPathResolveResult completed = {};

    for (size_t attempt = 0; attempt < 100; ++attempt)
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
        request.nowSeconds += 0.01;
        completed = runtime.resolveWaypoint(map, request);

        if (completed.planned)
        {
            break;
        }
    }

    CHECK(completed.planned);
    // Taking up the finished plan starts none: the AI's per-step plan budget counts only started plans.
    CHECK_FALSE(completed.requested);
    CHECK(completed.pathActive);
}

TEST_CASE("actor path runtime shares immutable snapshots across workers and foreground queries")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });
    map.buildSpatialGrid(24.0f);
    std::shared_ptr<const PathMap> snapshot = std::make_shared<PathMap>(map);
    const std::shared_ptr<const PathMap> replacement = std::make_shared<PathMap>(map);

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = snapshot->revision();
    request.nowSeconds = 10.0;

    ActorPathRuntime runtime;
    runtime.setWorkerCount(2);
    std::array<bool, 8> completed = {};
    for (size_t actorIndex = 0; actorIndex < completed.size(); ++actorIndex)
    {
        request.actorIndex = actorIndex;
        REQUIRE(runtime.resolveWaypoint(snapshot, request).queued);
    }
    // The world can replace its ownership while jobs still use the previous snapshot.
    snapshot.reset();
    request.allowPlan = false;
    const std::chrono::steady_clock::time_point deadline =
        std::chrono::steady_clock::now() + std::chrono::seconds(2);
    while (std::chrono::steady_clock::now() < deadline)
    {
        CHECK_FALSE(replacement->canReachDirectly(request.source, request.target, request.object));
        size_t completedCount = 0;
        for (size_t actorIndex = 0; actorIndex < completed.size(); ++actorIndex)
        {
            request.actorIndex = actorIndex;
            if (!completed[actorIndex])
            {
                const ActorPathResolveResult result = runtime.resolveWaypoint(replacement, request);
                if (result.planned)
                {
                    CHECK(result.pathActive);
                    CHECK_FALSE(result.discarded);
                    CHECK(replacement->canReachDirectly(request.source, result.waypoint, request.object));
                    completed[actorIndex] = true;
                }
            }
            completedCount += completed[actorIndex] ? 1 : 0;
        }
        if (completedCount == completed.size())
        {
            break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    for (bool actorCompleted : completed)
    {
        CHECK(actorCompleted);
    }
}

TEST_CASE("actor path runtime discards worker routes after a door changes the snapshot revision")
{
    PathMap map;
    map.setFacets({makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f)});
    std::shared_ptr<const PathMap> snapshot = std::make_shared<PathMap>(map);
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = snapshot->revision();
    request.allowDirect = false;
    request.nowSeconds = 10.0;
    ActorPathRuntime runtime;
    runtime.setWorkerCount(1);
    REQUIRE(runtime.resolveWaypoint(snapshot, request).queued);

    map.addFacet(makeRuntimeWall(72.0f, -120.0f, 120.0f, 0.0f, 120.0f));
    snapshot = std::make_shared<PathMap>(map);
    request.mapRevision = snapshot->revision();
    request.allowPlan = false;
    ActorPathResolveResult result = {};
    const std::chrono::steady_clock::time_point deadline =
        std::chrono::steady_clock::now() + std::chrono::seconds(2);
    while (!result.discarded && std::chrono::steady_clock::now() < deadline)
    {
        result = runtime.resolveWaypoint(snapshot, request);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    CHECK(result.discarded);
    CHECK_FALSE(result.pathActive);
    CHECK_FALSE(result.planned);
    CHECK_FALSE(snapshot->canReachDirectly(request.source, request.target, request.object));
}

TEST_CASE("actor path runtime owns a copy when the caller supplies a mutable borrowed map")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });
    const PathMap replacement = map;
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    ActorPathRuntime runtime;
    runtime.setWorkerCount(1);
    REQUIRE(runtime.resolveWaypoint(map, request).queued);
    map.clear();
    request.allowPlan = false;
    ActorPathResolveResult result = {};
    const std::chrono::steady_clock::time_point deadline =
        std::chrono::steady_clock::now() + std::chrono::seconds(2);
    while (!result.planned && std::chrono::steady_clock::now() < deadline)
    {
        result = runtime.resolveWaypoint(replacement, request);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    CHECK(result.planned);
    CHECK(result.pathActive);
}

TEST_CASE("actor path runtime keeps active route when replan fails")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    request.failedRetrySeconds = 5.0;

    ActorPathRuntime runtime;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    REQUIRE(planned.planned);
    REQUIRE(planned.pathActive);

    request.nowSeconds = 12.0;
    request.target = {2000.0f, 0.0f, 0.0f};
    const ActorPathResolveResult failedReplan = runtime.resolveWaypoint(map, request);

    CHECK(failedReplan.failed);
    CHECK(failedReplan.pathActive);
    CHECK_FALSE(failedReplan.directReachable);
}

TEST_CASE("actor path runtime skips a near waypoint after progress stalls")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    request.directCheckIntervalSeconds = 100.0;
    request.shortcutCheckIntervalSeconds = 100.0;

    ActorPathRuntime runtime;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    REQUIRE(planned.planned);
    REQUIRE(planned.pathActive);
    REQUIRE(planned.waypointIndex + 1 < planned.waypointCount);

    request.nowSeconds = 10.01;
    ActorPathResolveResult active = runtime.resolveWaypoint(map, request);
    REQUIRE(active.pathActive);
    REQUIRE(active.waypointIndex + 1 < planned.waypointCount);

    const PathPoint waypoint = active.waypoint;
    // Exercise route recovery even when this new position permits direct movement.
    request.allowDirect = false;
    request.source = {
        waypoint.x + request.waypointReachDistance + 4.0f,
        waypoint.y,
        waypoint.z
    };

    request.nowSeconds = 10.10;
    active = runtime.resolveWaypoint(map, request);
    REQUIRE(active.pathActive);
    const size_t stalledIndex = active.waypointIndex;

    request.nowSeconds = 10.60;
    const ActorPathResolveResult skipped = runtime.resolveWaypoint(map, request);

    CHECK(skipped.pathActive);
    CHECK(skipped.stalledWaypointCount == 1);
    CHECK(skipped.waypointIndex == stalledIndex + 1);
}

TEST_CASE("actor path runtime skips a distant waypoint after progress stalls")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    request.directCheckIntervalSeconds = 100.0;
    request.shortcutCheckIntervalSeconds = 100.0;

    ActorPathRuntime runtime;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    REQUIRE(planned.planned);
    REQUIRE(planned.pathActive);
    REQUIRE(planned.waypointIndex + 1 < planned.waypointCount);

    const PathPoint waypoint = planned.waypoint;
    request.allowDirect = false;
    request.source = {
        waypoint.x + request.waypointReachDistance + request.object.stepLength * 2.0f,
        waypoint.y,
        waypoint.z
    };

    request.nowSeconds = 10.10;
    const ActorPathResolveResult active = runtime.resolveWaypoint(map, request);
    REQUIRE(active.pathActive);
    const size_t stalledIndex = active.waypointIndex;

    request.nowSeconds = 10.60;
    const ActorPathResolveResult skipped = runtime.resolveWaypoint(map, request);

    CHECK(skipped.pathActive);
    CHECK(skipped.stalledWaypointCount == 1);
    CHECK(skipped.waypointIndex == stalledIndex + 1);
}

TEST_CASE("actor path runtime keeps a reached waypoint when the next waypoint would cut through void")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-32.0f, 80.0f, -16.0f, 16.0f, 0.0f),
        makeRuntimeFloor(48.0f, 80.0f, -16.0f, 160.0f, 0.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.object.stepLength = 64.0f;
    request.waypointReachDistance = 24.0f;
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {64.0f, 128.0f, 0.0f};
    request.mapRevision = map.revision();
    request.allowDirect = false;
    request.directCheckIntervalSeconds = 100.0;
    request.shortcutCheckIntervalSeconds = 100.0;

    PathPlanRequest planRequest = {};
    planRequest.source = request.source;
    planRequest.target = request.target;
    planRequest.object = request.object;
    planRequest.mapRevision = static_cast<uint32_t>(request.mapRevision);
    planRequest.allowDirect = request.allowDirect;
    PathPlanner planner;
    const std::vector<PathPoint> plannedWaypoints = planner.plan(map, planRequest).waypoints;
    REQUIRE(plannedWaypoints.size() >= 2u);

    ActorPathRuntime runtime;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    REQUIRE(planned.planned);
    REQUIRE(planned.pathActive);
    REQUIRE_EQ(planned.waypointCount, plannedWaypoints.size());

    const PathPoint firstWaypoint = plannedWaypoints[0];
    const PathPoint secondWaypoint = plannedWaypoints[1];
    const std::array<PathPoint, 4> sourceCandidates = {{
        {firstWaypoint.x - 20.0f, firstWaypoint.y, firstWaypoint.z},
        {firstWaypoint.x + 20.0f, firstWaypoint.y, firstWaypoint.z},
        {firstWaypoint.x, firstWaypoint.y - 20.0f, firstWaypoint.z},
        {firstWaypoint.x, firstWaypoint.y + 20.0f, firstWaypoint.z}
    }};
    bool foundSource = false;

    for (const PathPoint &candidateSource : sourceCandidates)
    {
        if (map.canReachDirectly(candidateSource, firstWaypoint, request.object)
            && !map.canReachDirectly(candidateSource, secondWaypoint, request.object))
        {
            request.source = candidateSource;
            foundSource = true;
            break;
        }
    }

    REQUIRE(foundSource);
    CHECK(planned.waypoint.x == doctest::Approx(firstWaypoint.x));
    CHECK(planned.waypoint.y == doctest::Approx(firstWaypoint.y));
    CHECK(planned.waypoint.z == doctest::Approx(firstWaypoint.z));
    CHECK_FALSE(map.canReachDirectly(request.source, secondWaypoint, request.object));

    const ActorPathResolveResult active = runtime.resolveWaypoint(map, request);
    REQUIRE(active.pathActive);
    CHECK_EQ(active.reachedWaypointCount, 0u);
    CHECK_EQ(active.waypointIndex, planned.waypointIndex);
    CHECK(active.waypoint.x == doctest::Approx(firstWaypoint.x));
    CHECK(active.waypoint.y == doctest::Approx(firstWaypoint.y));
    CHECK(active.waypoint.z == doctest::Approx(firstWaypoint.z));
}

TEST_CASE("actor path runtime skips a reached waypoint when the next waypoint remains directly reachable")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-32.0f, 160.0f, -32.0f, 32.0f, 0.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.object.stepLength = 64.0f;
    request.waypointReachDistance = 24.0f;
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {128.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.allowDirect = false;
    request.directCheckIntervalSeconds = 100.0;
    request.shortcutCheckIntervalSeconds = 100.0;

    ActorPathRuntime runtime;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    REQUIRE(planned.planned);
    REQUIRE(planned.pathActive);
    REQUIRE(planned.waypointCount >= 2u);

    const PathPoint firstWaypoint = planned.waypoint;
    request.source = {
        firstWaypoint.x - 20.0f,
        firstWaypoint.y,
        firstWaypoint.z
    };
    request.nowSeconds = 10.0;

    const ActorPathResolveResult active = runtime.resolveWaypoint(map, request);
    REQUIRE(active.pathActive);
    CHECK_EQ(active.reachedWaypointCount, 1u);
    CHECK_EQ(active.waypointIndex, planned.waypointIndex + 1);
}

TEST_CASE("actor path runtime shortcuts ground route when a later waypoint is directly reachable")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-96.0f, 240.0f, -160.0f, 160.0f, 0.0f),
        makeRuntimeWall(72.0f, -72.0f, 72.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {192.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    request.directCheckIntervalSeconds = 100.0;
    request.shortcutCheckIntervalSeconds = 0.01;

    ActorPathRuntime runtime;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    REQUIRE(planned.planned);
    REQUIRE(planned.pathActive);
    CHECK(planned.shortcutWaypointCount > 0u);
    CHECK(planned.waypointIndex > 0u);
}

TEST_CASE("actor path runtime limits ground shortcuts to local route progress")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-96.0f, 864.0f, -240.0f, 240.0f, 0.0f),
        makeRuntimeWall(72.0f, -72.0f, 72.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {768.0f, 0.0f, 0.0f};
    request.object.stepLength = 64.0f;
    request.mapRevision = map.revision();
    request.nowSeconds = 10.0;
    request.directCheckIntervalSeconds = 100.0;
    request.shortcutCheckIntervalSeconds = 0.01;

    ActorPathRuntime runtime;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    REQUIRE(planned.planned);
    REQUIRE(planned.pathActive);
    CHECK(planned.shortcutWaypointCount > 0u);
    CHECK(planned.waypointIndex > 0u);
    const float shortcutDistance = runtimeDistance2d(request.source, planned.waypoint);
    CHECK(shortcutDistance <= request.object.stepLength * 6.0f + 0.001f);
}

TEST_CASE("actor path runtime reports out of range without suppressing direct fallback")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 288.0f, -48.0f, 48.0f, 0.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {240.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.planningRange = 16.0f;

    ActorPathRuntime runtime;
    const ActorPathResolveResult result = runtime.resolveWaypoint(map, request);

    CHECK(result.outOfRange);
    CHECK_FALSE(result.failed);
    CHECK_FALSE(result.cooldown);
    CHECK_FALSE(result.pathActive);
}

TEST_CASE("actor path runtime plans flying waypoints around solid walls")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -24.0f, 24.0f, 0.0f, 120.0f)
    });

    ActorPathResolveRequest request = makeRuntimeRequest();
    request.object.canFly = true;
    request.object.radius = 8.0f;
    request.object.stepLength = 32.0f;
    request.object.stepHeight = 40.0f;
    request.source = {0.0f, 0.0f, 64.0f};
    request.target = {144.0f, 0.0f, 64.0f};
    request.mapRevision = map.revision();
    request.planningRange = 6000.0f;
    request.allowPlan = true;

    ActorPathRuntime runtime;
    const ActorPathResolveResult result = runtime.resolveWaypoint(map, request);

    CHECK_FALSE(result.directReachable);
    REQUIRE(result.pathActive);
    CHECK(result.planned);
    CHECK(result.waypointCount > 0);
    CHECK(result.waypoint.z == doctest::Approx(64.0f));
}

TEST_CASE("actor path runtime distributes reachability checks fairly across busy actors")
{
    PathMap map;
    map.setFacets({makeRuntimeFloor(-64.0f, 256.0f, -64.0f, 64.0f, 0.0f)});
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    ActorPathRuntime runtime;
    std::array<bool, 32> checked = {};
    for (size_t frame = 0; frame < 8; ++frame)
    {
        runtime.beginReachabilityFrame(4);
        request.nowSeconds = double(frame);
        size_t checks = 0;
        for (size_t actorIndex = 0; actorIndex < checked.size(); ++actorIndex)
        {
            request.actorIndex = actorIndex;
            const ActorPathResolveResult result = runtime.resolveWaypoint(map, request);
            checks += result.directChecked ? 1 : 0;
            checked[actorIndex] = checked[actorIndex] || result.directChecked;
            CHECK_FALSE(result.failed);
            CHECK_FALSE(result.planned);
        }
        CHECK_EQ(checks, 4u);
    }
    for (bool receivedCheck : checked)
    {
        CHECK(receivedCheck);
    }
}

TEST_CASE("actor path runtime defers unverified movement without claiming a blocked route")
{
    PathMap map;
    const PathFacet floor = makeRuntimeFloor(-64.0f, 256.0f, -64.0f, 64.0f, 0.0f);
    map.setFacets({floor});
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    ActorPathRuntime runtime;
    REQUIRE(runtime.resolveWaypoint(map, request).directReachable);
    map.setFacets({floor, makeRuntimeWall(72.0f, -64.0f, 64.0f, 0.0f, 128.0f)});
    request.mapRevision = map.revision();
    request.nowSeconds = 0.01;
    runtime.beginReachabilityFrame(0);
    const ActorPathResolveResult deferred = runtime.resolveWaypoint(map, request);
    CHECK(deferred.deferred);
    CHECK_FALSE(deferred.directChecked);
    CHECK_FALSE(deferred.directReachable);
    CHECK_FALSE(deferred.pathActive);
    CHECK_FALSE(deferred.failed);
    CHECK_FALSE(deferred.planned);
    runtime.beginReachabilityFrame(1);
    const ActorPathResolveResult checked = runtime.resolveWaypoint(map, request);
    CHECK(checked.directChecked);
    CHECK_FALSE(checked.directReachable);
    CHECK(checked.planned);
    CHECK(checked.pathActive);
}

TEST_CASE("actor path runtime follows valid routes while a direct check waits for its budget")
{
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.allowDirect = false;
    ActorPathRuntime runtime;
    REQUIRE(runtime.resolveWaypoint(map, request).pathActive);
    request.allowDirect = true;
    request.nowSeconds = 0.01;
    runtime.beginReachabilityFrame(0);
    const ActorPathResolveResult deferred = runtime.resolveWaypoint(map, request);
    CHECK(deferred.deferred);
    CHECK(deferred.pathActive);
    CHECK_FALSE(deferred.directChecked);
    CHECK_FALSE(deferred.failed);
    CHECK_FALSE(deferred.planned);
}

TEST_CASE("actor path runtime passes a reached waypoint without waiting for the reachability budget")
{
    // Crowded indoor maps spend the frame's budget early; an actor on a reached waypoint must still head on to the next
    // one instead of jittering on it until a check is granted.
    PathMap map;
    map.setFacets({
        makeRuntimeFloor(-48.0f, 192.0f, -120.0f, 120.0f, 0.0f),
        makeRuntimeWall(72.0f, -60.0f, 60.0f, 0.0f, 120.0f)
    });
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    request.allowDirect = false;
    ActorPathRuntime runtime;
    const ActorPathResolveResult planned = runtime.resolveWaypoint(map, request);
    REQUIRE(planned.pathActive);
    REQUIRE(planned.waypointCount > planned.waypointIndex + 1);

    request.source = planned.waypoint;
    request.nowSeconds = 0.01;
    runtime.beginReachabilityFrame(0);
    const ActorPathResolveResult advanced = runtime.resolveWaypoint(map, request);
    CHECK(advanced.pathActive);
    CHECK(advanced.reachedWaypointCount > 0);
    CHECK(advanced.waypointIndex > planned.waypointIndex);
}

TEST_CASE("actor path runtime discards inactive reachability requests without starving later actors")
{
    PathMap map;
    map.setFacets({makeRuntimeFloor(-64.0f, 256.0f, -64.0f, 64.0f, 0.0f)});
    ActorPathResolveRequest request = makeRuntimeRequest();
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = map.revision();
    ActorPathRuntime runtime;
    runtime.beginReachabilityFrame(0);
    CHECK(runtime.resolveWaypoint(map, request).deferred);
    request.actorIndex = 1;
    CHECK(runtime.resolveWaypoint(map, request).deferred);
    runtime.resetActor(0);
    runtime.beginReachabilityFrame(1);
    CHECK(runtime.resolveWaypoint(map, request).directChecked);
    runtime.clear();
    CHECK(runtime.resolveWaypoint(map, request).directChecked);
}
