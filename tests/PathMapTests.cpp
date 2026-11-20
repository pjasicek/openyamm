#include "doctest/doctest.h"

#include "game/pathfinding/PathMap.h"

#include <array>
#include <cmath>
#include <limits>
#include <utility>
#include <vector>

using OpenYAMM::Game::PathFacet;
using OpenYAMM::Game::PathFacetKind;
using OpenYAMM::Game::PathFloorSample;
using OpenYAMM::Game::PathMap;
using OpenYAMM::Game::PathObject;
using OpenYAMM::Game::PathPoint;
using OpenYAMM::Game::PathTraceResult;
using OpenYAMM::Game::PathWalkRejectReason;
using OpenYAMM::Game::PathWalkSegmentDebug;

namespace
{
constexpr float TestEpsilon = 0.001f;

PathFacet makeFloor(float minX, float maxX, float minY, float maxY, float z)
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

PathFacet makeWall(float x, float minY, float maxY, float minZ, float maxZ)
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

PathFacet makeHorizontalWall(float y, float minX, float maxX, float minZ, float maxZ)
{
    PathFacet facet = {};
    facet.kind = PathFacetKind::Wall;
    facet.blocking = true;
    facet.vertices = {
        {minX, y, minZ},
        {maxX, y, minZ},
        {maxX, y, maxZ},
        {minX, y, maxZ}
    };
    return facet;
}
}

TEST_CASE("path map line trace blocks through a wall and allows a route around it")
{
    PathMap map;
    map.setFacets({
        makeWall(50.0f, -10.0f, 10.0f, 0.0f, 100.0f)
    });

    const PathTraceResult blocked = map.traceLine({0.0f, 0.0f, 50.0f}, {100.0f, 0.0f, 50.0f});
    CHECK(blocked.blocked);
    CHECK_EQ(blocked.facetIndex, 0u);
    CHECK(std::fabs(blocked.point.x - 50.0f) < TestEpsilon);

    const PathTraceResult clear = map.traceLine({0.0f, 30.0f, 50.0f}, {100.0f, 30.0f, 50.0f});
    CHECK_FALSE(clear.blocked);
}

TEST_CASE("path map floor selection prefers the nearest floor below and marks floors above as void")
{
    PathMap map;
    map.setFacets({
        makeFloor(-100.0f, 100.0f, -100.0f, 100.0f, 0.0f),
        makeFloor(-100.0f, 100.0f, -100.0f, 100.0f, 50.0f)
    });

    const PathFloorSample below = map.floorAt({0.0f, 0.0f, 30.0f});
    REQUIRE(below.hasFloor);
    CHECK_FALSE(below.inVoid);
    CHECK(std::fabs(below.z - 0.0f) < TestEpsilon);

    const PathFloorSample above = map.floorAt({0.0f, 0.0f, -10.0f});
    REQUIRE(above.hasFloor);
    CHECK(above.inVoid);
    CHECK(std::fabs(above.z - 0.0f) < TestEpsilon);
}

TEST_CASE("path map walking rejects segments through void")
{
    PathMap map;
    map.setFacets({
        makeFloor(0.0f, 100.0f, 0.0f, 100.0f, 0.0f)
    });

    PathObject object = {};
    object.radius = 8.0f;
    object.stepLength = 24.0f;
    object.stepHeight = 40.0f;

    CHECK(map.traceWalkSegment({10.0f, 50.0f, 0.0f}, {90.0f, 50.0f, 0.0f}, object));
    CHECK_FALSE(map.traceWalkSegment({10.0f, 50.0f, 0.0f}, {150.0f, 50.0f, 0.0f}, object));
}

TEST_CASE("path map walking climbs a stair whose treads are shorter than the body's radius")
{
    // Four 32 risers on 48 treads, rising toward +x from x 0 (D8's Fab Line A stair), then a landing at 128.
    std::vector<OpenYAMM::Game::PathFacet> facets = {makeFloor(-400.0f, 0.0f, -300.0f, 300.0f, 0.0f)};
    for (int step = 0; step < 4; ++step)
    {
        const float x = float(step) * 48.0f;
        const float top = float(step + 1) * 32.0f;
        facets.push_back(makeWall(x, -300.0f, 300.0f, top - 32.0f, top));
        facets.push_back(makeFloor(x, step == 3 ? 600.0f : x + 48.0f, -300.0f, 300.0f, top));
    }
    PathMap map;
    map.setFacets(facets);
    PathObject object = {};
    object.radius = 55.0f;
    object.height = 208.0f;
    object.stepHeight = 40.0f;
    object.dropHeight = 512.0f;
    // Without the indoor riser rule the side probes stop at the next riser.
    CHECK_FALSE(map.traceWalkSegment({-300.0f, 0.0f, 0.0f}, {450.0f, 0.0f, 128.0f}, object));
    object.riserHeight = 80.0f;
    CHECK(map.traceWalkSegment({-300.0f, 0.0f, 0.0f}, {450.0f, 0.0f, 128.0f}, object));
    CHECK(map.traceWalkSegment({450.0f, 0.0f, 128.0f}, {-300.0f, 0.0f, 0.0f}, object));

    // A ledge of 96 in one step still stops it.
    PathMap ledge;
    ledge.setFacets({makeFloor(-400.0f, 0.0f, -300.0f, 300.0f, 0.0f), makeWall(0.0f, -300.0f, 300.0f, 0.0f, 96.0f),
        makeFloor(0.0f, 600.0f, -300.0f, 300.0f, 96.0f)});
    CHECK_FALSE(ledge.traceWalkSegment({-300.0f, 0.0f, 0.0f}, {450.0f, 0.0f, 96.0f}, object));
}

TEST_CASE("path map walking checks full height beneath ceilings")
{
    PathFacet ceiling = makeFloor(50.0f, 200.0f, -100.0f, 100.0f, 120.0f);
    ceiling.kind = PathFacetKind::Ceiling;
    ceiling.blocking = true;
    ceiling.walkableFloor = false;
    PathMap map;
    map.setFacets({makeFloor(-100.0f, 300.0f, -200.0f, 200.0f, 0.0f), ceiling});
    PathObject object = {};
    object.radius = 20.0f;
    object.height = 80.0f;
    CHECK(map.canReachDirectly({0.0f, 0.0f, 0.0f}, {150.0f, 0.0f, 0.0f}, object));
    object.height = 120.0f;
    CHECK(map.canReachDirectly({0.0f, 0.0f, 0.0f}, {150.0f, 0.0f, 0.0f}, object));
    CHECK(map.traceWalkSegment({80.0f, 0.0f, 0.0f}, {90.0f, 0.0f, 0.0f}, object));
    object.height = 121.0f;
    CHECK_FALSE(map.canReachDirectly({0.0f, 0.0f, 0.0f}, {150.0f, 0.0f, 0.0f}, object));
    object.height = 145.0f;
    CHECK_FALSE(map.canReachDirectly({0.0f, 0.0f, 0.0f}, {150.0f, 0.0f, 0.0f}, object));
    CHECK(map.canReachDirectly({0.0f, -150.0f, 0.0f}, {150.0f, -150.0f, 0.0f}, object));
    // The check must also reject standing entirely underneath the low ceiling.
    CHECK_FALSE(map.traceWalkSegment({80.0f, 0.0f, 0.0f}, {90.0f, 0.0f, 0.0f}, object));
    object.height = std::numeric_limits<float>::quiet_NaN();
    CHECK_FALSE(map.traceWalkSegment({0.0f, 0.0f, 0.0f}, {150.0f, 0.0f, 0.0f}, object));
}

TEST_CASE("path map full body clearance respects climbable risers")
{
    for (const float radius : {90.0f, 110.0f})
    {
        CAPTURE(radius);
        PathObject object = {};
        object.radius = radius;
        object.height = radius * 2.0f + 2.0f;
        object.stepHeight = 40.0f;
        for (const float rise : {16.0f, 40.0f, 41.0f})
        {
            CAPTURE(rise);
            PathMap map;
            map.setFacets({makeFloor(-300.0f, 0.0f, -200.0f, 200.0f, 0.0f),
                makeFloor(0.0f, 300.0f, -200.0f, 200.0f, rise),
                makeWall(0.0f, -200.0f, 200.0f, 0.0f, rise)});
            CHECK_EQ(map.traceWalkSegment({-180.0f, 0.0f, 0.0f}, {180.0f, 0.0f, rise}, object), rise <= 40.0f);
        }
    }
}

namespace
{
PathFacet makeCeiling(float minX, float maxX, float minY, float maxY, float z)
{
    PathFacet facet = makeFloor(minX, maxX, minY, maxY, z);
    facet.kind = PathFacetKind::Ceiling;
    facet.blocking = true;
    facet.walkableFloor = false;
    std::swap(facet.vertices[1], facet.vertices[3]);
    return facet;
}

// MM9's slab stair (the Thousand Terrors' spiral, straightened at radius 300): 30-unit rises on 120-unit treads
// toward +x from x 0, each tread a 15-thick slab (its top, its underside and its front face) over an open slot, then a
// landing at 180.
std::vector<PathFacet> makeSlabStair()
{
    std::vector<PathFacet> facets = {makeFloor(-600.0f, 0.0f, -400.0f, 400.0f, 0.0f)};

    for (int step = 0; step < 6; ++step)
    {
        const float x = static_cast<float>(step) * 120.0f;
        const float top = static_cast<float>(step + 1) * 30.0f;
        const float endX = step == 5 ? 1400.0f : x + 120.0f;
        facets.push_back(makeFloor(x, endX, -400.0f, 400.0f, top));
        facets.push_back(makeCeiling(x, endX, -400.0f, 400.0f, top - 15.0f));
        facets.push_back(makeWall(x, -400.0f, 400.0f, top - 15.0f, top));
    }

    return facets;
}

PathObject makeSquatBody(float riserHeight)
{
    // A Reptilian Terror: wider than it is tall.
    PathObject object = {};
    object.radius = 190.0f;
    object.height = 256.0f;
    object.stepHeight = 40.0f;
    object.dropHeight = 100.0f;
    object.riserHeight = riserHeight;
    return object;
}
}

TEST_CASE("path map squat body climbs slab treads whose undersides lie in its upper sphere")
{
    PathMap map;
    map.setFacets(makeSlabStair());
    // The sphere model (no indoor riser rule): the next slab's underside, 15 above the feet, stops every step.
    CHECK_FALSE(map.traceWalkSegment({-400.0f, 0.0f, 0.0f}, {1100.0f, 0.0f, 180.0f}, makeSquatBody(0.0f)));
    // Indoors (the riser rule), its upper sphere passes the steps it climbs: up and back down.
    CHECK(map.traceWalkSegment({-400.0f, 0.0f, 0.0f}, {1100.0f, 0.0f, 180.0f}, makeSquatBody(80.0f)));
    CHECK(map.traceWalkSegment({1100.0f, 0.0f, 180.0f}, {-400.0f, 0.0f, 0.0f}, makeSquatBody(80.0f)));

    // A body taller than it is wide keeps its upper sphere and climbs as before.
    PathObject tall = {};
    tall.radius = 65.0f;
    tall.height = 179.0f;
    tall.stepHeight = 40.0f;
    tall.dropHeight = 100.0f;
    tall.riserHeight = 80.0f;
    CHECK(map.traceWalkSegment({-400.0f, 0.0f, 0.0f}, {1100.0f, 0.0f, 180.0f}, tall));
}

TEST_CASE("path map squat body is still blocked by low ceilings, railings and narrow doorways")
{
    const PathObject squat = makeSquatBody(80.0f);

    // Overhead clearance is the body's height, not twice its radius.
    for (const float ceilingZ : {200.0f, 260.0f})
    {
        CAPTURE(ceilingZ);
        PathMap map;
        map.setFacets({makeFloor(-600.0f, 600.0f, -400.0f, 400.0f, 0.0f),
            makeCeiling(100.0f, 400.0f, -400.0f, 400.0f, ceilingZ)});
        CHECK_EQ(map.traceWalkSegment({-400.0f, 0.0f, 0.0f}, {250.0f, 0.0f, 0.0f}, squat), ceilingZ > 256.0f);
        CHECK_FALSE(map.traceWalkSegment({-400.0f, 0.0f, 0.0f}, {250.0f, 0.0f, 0.0f}, makeSquatBody(0.0f)));
    }

    // A 70 railing with no tread on top is not a riser: the floor on both sides is at 0.
    PathMap railing;
    railing.setFacets({makeFloor(-600.0f, 600.0f, -400.0f, 400.0f, 0.0f),
        makeWall(0.0f, -400.0f, 400.0f, 0.0f, 70.0f)});
    CHECK_FALSE(railing.traceWalkSegment({-400.0f, 0.0f, 0.0f}, {400.0f, 0.0f, 0.0f}, squat));

    // A raised floor's edge that the body only runs along (a stair's side) is not a riser it climbs.
    PathMap platform;
    platform.setFacets({makeFloor(-600.0f, 0.0f, -400.0f, 400.0f, 0.0f),
        makeFloor(0.0f, 600.0f, -400.0f, 400.0f, 60.0f), makeWall(0.0f, -400.0f, 400.0f, 0.0f, 60.0f)});
    PathObject smaller = makeSquatBody(80.0f);
    smaller.radius = 100.0f;
    smaller.height = 150.0f;
    CHECK_FALSE(platform.traceWalkSegment({-150.0f, -200.0f, 0.0f}, {-40.0f, 200.0f, 0.0f}, smaller));
    CHECK(platform.traceWalkSegment({-150.0f, -200.0f, 0.0f}, {-110.0f, 200.0f, 0.0f}, smaller));

    // Jambs 200 apart stop a body 380 wide; 400 apart they let it through. A lintel under its height stops it.
    for (const float halfGap : {100.0f, 200.0f})
    {
        CAPTURE(halfGap);
        PathMap doorway;
        doorway.setFacets({makeFloor(-600.0f, 600.0f, -600.0f, 600.0f, 0.0f),
            makeWall(0.0f, halfGap, 600.0f, 0.0f, 400.0f), makeWall(0.0f, -600.0f, -halfGap, 0.0f, 400.0f)});
        CHECK_EQ(doorway.traceWalkSegment({-400.0f, 0.0f, 0.0f}, {400.0f, 0.0f, 0.0f}, squat), halfGap > 190.0f);
    }
    for (const float lintelZ : {230.0f, 270.0f})
    {
        CAPTURE(lintelZ);
        PathMap lintel;
        lintel.setFacets({makeFloor(-600.0f, 600.0f, -600.0f, 600.0f, 0.0f),
            makeWall(0.0f, -300.0f, 300.0f, lintelZ, 400.0f)});
        CHECK_EQ(lintel.traceWalkSegment({-400.0f, 0.0f, 0.0f}, {400.0f, 0.0f, 0.0f}, squat), lintelZ > 256.0f);
    }
}

TEST_CASE("path map walking allows leaving a sloped ceiling contact but rejects entering it")
{
    PathFacet ceiling = {};
    ceiling.kind = PathFacetKind::Ceiling;
    ceiling.blocking = true;
    ceiling.vertices = {{-200.0f, -200.0f, 400.0f}, {-200.0f, 200.0f, 400.0f},
        {200.0f, 200.0f, 0.0f}, {200.0f, -200.0f, 0.0f}};
    PathMap map;
    map.setFacets({makeFloor(-200.0f, 200.0f, -200.0f, 200.0f, 0.0f), ceiling});
    PathObject object = {};
    object.radius = 56.0f;
    object.height = 145.0f;
    // At x=50 the head fits, but the upper sphere already touches the overhang.
    CHECK(map.traceWalkSegment({50.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 0.0f}, object));
    CHECK_FALSE(map.traceWalkSegment({0.0f, 0.0f, 0.0f}, {50.0f, 0.0f, 0.0f}, object));
}

TEST_CASE("path map walking checks obstacles between the lower and upper body probes")
{
    PathMap map;
    map.setFacets({makeFloor(-100.0f, 100.0f, -100.0f, 100.0f, 0.0f),
        makeWall(0.0f, -5.0f, 5.0f, 80.0f, 120.0f)});
    PathObject object = {};
    object.radius = 20.0f;
    object.height = 200.0f;
    CHECK_FALSE(map.traceWalkSegment({-60.0f, 0.0f, 0.0f}, {60.0f, 0.0f, 0.0f}, object));
    CHECK_FALSE(map.traceWalkSegment({-60.0f, 15.0f, 0.0f}, {60.0f, 15.0f, 0.0f}, object));
    CHECK(map.traceWalkSegment({-60.0f, 30.0f, 0.0f}, {60.0f, 30.0f, 0.0f}, object));
}

TEST_CASE("path map walking samples below long path step length near void edge")
{
    PathMap map;
    map.setFacets({
        makeFloor(0.0f, 10.0f, 0.0f, 100.0f, 0.0f),
        makeFloor(40.0f, 160.0f, 0.0f, 100.0f, 0.0f)
    });

    PathObject object = {};
    object.radius = 40.0f;
    object.stepLength = 64.0f;
    object.stepHeight = 48.0f;

    const PathWalkSegmentDebug debug =
        map.debugTraceWalkSegment({8.0f, 50.0f, 0.0f}, {120.0f, 50.0f, 0.0f}, object);

    CHECK_FALSE(debug.success);
    CHECK_EQ(debug.rejectReason, PathWalkRejectReason::SampleNoFloor);
}

TEST_CASE("path map walking rejects diagonal corner cuts through a small void span")
{
    PathMap map;
    map.setFacets({
        makeFloor(0.0f, 512.0f, 0.0f, 512.0f, 0.0f),
        makeFloor(512.0f, 1024.0f, 512.0f, 1024.0f, 0.0f)
    });

    PathObject object = {};
    object.radius = 40.0f;
    object.stepLength = 64.0f;
    object.stepHeight = 128.0f;

    const PathWalkSegmentDebug debug =
        map.debugTraceWalkSegment({500.0f, 510.0f, 0.0f}, {564.0f, 574.0f, 0.0f}, object);

    CHECK_FALSE(debug.success);
    CHECK_EQ(debug.rejectReason, PathWalkRejectReason::SampleNoFloor);
}

TEST_CASE("path map walking rejects narrow void strips before bridge support")
{
    PathMap map;
    map.setFacets({
        makeFloor(0.0f, 3.0f, 0.0f, 100.0f, 0.0f),
        makeFloor(5.0f, 100.0f, 0.0f, 100.0f, 0.0f)
    });

    PathObject object = {};
    object.radius = 40.0f;
    object.stepLength = 64.0f;
    object.stepHeight = 128.0f;

    const PathWalkSegmentDebug debug =
        map.debugTraceWalkSegment({0.5f, 50.0f, 0.0f}, {64.5f, 50.0f, 0.0f}, object);

    CHECK_FALSE(debug.success);
    CHECK_EQ(debug.rejectReason, PathWalkRejectReason::SampleNoFloor);
}

TEST_CASE("path map walking rejects floor height deltas above the actor step height")
{
    PathMap map;
    map.setFacets({
        makeFloor(0.0f, 50.0f, 0.0f, 100.0f, 0.0f),
        makeFloor(50.0f, 100.0f, 0.0f, 100.0f, 80.0f)
    });

    PathObject object = {};
    object.radius = 8.0f;
    object.stepLength = 24.0f;
    object.stepHeight = 40.0f;

    CHECK_FALSE(map.traceWalkSegment({25.0f, 50.0f, 0.0f}, {75.0f, 50.0f, 0.0f}, object));

    object.stepHeight = 90.0f;
    CHECK(map.traceWalkSegment({25.0f, 50.0f, 0.0f}, {75.0f, 50.0f, 80.0f}, object));
}

TEST_CASE("path map walking uses independent rise and drop limits")
{
    PathObject object = {};
    object.radius = 8.0f;
    object.stepHeight = 40.0f;
    object.dropHeight = 100.0f;
    for (const float drop : {96.0f, 100.0f, 101.0f})
    {
        CAPTURE(drop);
        PathMap map;
        map.setFacets({
            makeFloor(0.0f, 100.0f, 0.0f, 100.0f, drop),
            makeFloor(100.0f, 200.0f, 0.0f, 100.0f, 0.0f)
        });
        CHECK_EQ(map.traceWalkSegment({50.0f, 50.0f, drop}, {150.0f, 50.0f, 0.0f}, object), drop <= 100.0f);
        CHECK_FALSE(map.traceWalkSegment({150.0f, 50.0f, 0.0f}, {50.0f, 50.0f, drop}, object));
    }
}

TEST_CASE("path map walking leaves a step before descending beside its vertical face")
{
    const std::vector<PathFacet> facets = {
        makeFloor(0.0f, 100.0f, 0.0f, 200.0f, 96.0f),
        makeFloor(100.0f, 300.0f, 0.0f, 200.0f, 0.0f),
        makeWall(100.0f, 0.0f, 200.0f, 0.0f, 96.0f)
    };
    PathMap map;
    map.setFacets(facets);
    PathObject object = {};
    object.radius = 56.0f;
    object.dropHeight = 100.0f;
    CHECK(map.traceWalkSegment({80.0f, 100.0f, 96.0f}, {200.0f, 100.0f, 0.0f}, object));
    CHECK_FALSE(map.traceWalkSegment({200.0f, 100.0f, 0.0f}, {80.0f, 100.0f, 96.0f}, object));

    map.addFacet(makeWall(140.0f, 0.0f, 200.0f, 0.0f, 256.0f));
    CHECK_FALSE(map.traceWalkSegment({80.0f, 100.0f, 96.0f}, {200.0f, 100.0f, 0.0f}, object));
}

TEST_CASE("path map walking rejects a higher overlapping target when trace stays on lower floor")
{
    PathMap map;
    map.setFacets({
        makeFloor(0.0f, 120.0f, 0.0f, 100.0f, 0.0f),
        makeFloor(40.0f, 120.0f, 0.0f, 100.0f, 256.0f)
    });

    PathObject object = {};
    object.radius = 40.0f;
    object.stepLength = 64.0f;
    object.stepHeight = 128.0f;

    const PathWalkSegmentDebug debug =
        map.debugTraceWalkSegment({10.0f, 50.0f, 0.0f}, {90.0f, 50.0f, 256.0f}, object);

    CHECK_FALSE(debug.success);
    CHECK_EQ(debug.rejectReason, PathWalkRejectReason::StepHeight);
    CHECK(debug.stepDeltaZ > object.stepHeight);
}

TEST_CASE("path map rejects non-finite path queries without touching spatial grids")
{
    PathMap map;
    map.setFacets({
        makeFloor(-100.0f, 100.0f, -100.0f, 100.0f, 0.0f),
        makeWall(50.0f, -10.0f, 10.0f, 0.0f, 100.0f)
    });
    map.buildSpatialGrid(16.0f);

    const float nan = std::numeric_limits<float>::quiet_NaN();
    const PathFloorSample floor = map.floorAt({nan, 0.0f, 40.0f});
    CHECK_FALSE(floor.hasFloor);
    CHECK(floor.inVoid);

    const PathTraceResult trace = map.traceLine({0.0f, 0.0f, 40.0f}, {nan, 0.0f, 40.0f}, 8.0f, true);
    CHECK(trace.blocked);

    PathObject object = {};
    object.radius = 8.0f;
    object.stepLength = 24.0f;
    object.stepHeight = 40.0f;
    CHECK_FALSE(map.traceWalkSegment({0.0f, 0.0f, 0.0f}, {nan, 0.0f, 0.0f}, object));
}

TEST_CASE("path map body-radius side trace rejects narrow wall clearance")
{
    PathMap map;
    map.setFacets({
        makeWall(50.0f, 10.0f, 20.0f, 0.0f, 100.0f)
    });

    const PathTraceResult center = map.traceLine({0.0f, 0.0f, 50.0f}, {100.0f, 0.0f, 50.0f});
    CHECK_FALSE(center.blocked);

    const PathTraceResult body = map.traceLine({0.0f, 0.0f, 50.0f}, {100.0f, 0.0f, 50.0f}, 15.0f, true);
    CHECK(body.blocked);
    CHECK_EQ(body.facetIndex, 0u);
}

TEST_CASE("path map body-radius forward trace rejects wall clearance before center crossing")
{
    PathMap map;
    map.setFacets({
        makeHorizontalWall(115.0f, -16.0f, 16.0f, 0.0f, 100.0f)
    });

    const PathTraceResult center = map.traceLine({0.0f, 0.0f, 50.0f}, {0.0f, 100.0f, 50.0f});
    CHECK_FALSE(center.blocked);

    const PathTraceResult body = map.traceLine({0.0f, 0.0f, 50.0f}, {0.0f, 100.0f, 50.0f}, 20.0f, true);
    CHECK(body.blocked);
    CHECK_EQ(body.facetIndex, 0u);
}

TEST_CASE("path map body-radius trace rejects parallel movement into a wall")
{
    PathMap map;
    map.setFacets({
        makeWall(0.0f, -100.0f, 100.0f, 0.0f, 100.0f)
    });

    const PathTraceResult clear =
        map.traceLine({10.0f, 0.0f, 50.0f}, {10.0f, 40.0f, 50.0f}, 12.0f, true);
    CHECK_FALSE(clear.blocked);

    const PathTraceResult blocked =
        map.traceLine({13.0f, 0.0f, 50.0f}, {11.0f, 40.0f, 50.0f}, 12.0f, true);
    CHECK(blocked.blocked);
    CHECK_EQ(blocked.facetIndex, 0u);
}

TEST_CASE("path map body touching a wall can move away without crossing it")
{
    PathMap map;
    map.setFacets({makeWall(0.0f, -100.0f, 100.0f, 0.0f, 100.0f)});

    for (const float side : {-1.0f, 1.0f})
    {
        INFO("wall side=" << side);
        CHECK_FALSE(map.traceLine({side * 104.0f, 0.0f, 50.0f},
            {side * 40.0f, 0.0f, 50.0f}, 40.0f, true).blocked);
        for (const float distance : {40.0f, 39.0f, 10.0f})
        {
            INFO("wall distance=" << distance);
            const PathPoint from = {side * distance, 0.0f, 50.0f};
            CHECK_FALSE(map.traceLine(from, {side * 104.0f, 0.0f, 50.0f}, 40.0f, true).blocked);
            CHECK_FALSE(map.traceLine(from, {side * 104.0f, 64.0f, 50.0f}, 40.0f, true).blocked);
            CHECK(map.traceLine(from, {side * 5.0f, 0.0f, 50.0f}, 40.0f, true).blocked);
            CHECK(map.traceLine(from, {-side * 104.0f, 0.0f, 50.0f}, 40.0f, true).blocked);
        }
    }
}

TEST_CASE("path map leaving wall contact still blocks new obstacles")
{
    PathMap map;
    map.setFacets({
        makeWall(0.0f, -100.0f, 100.0f, 0.0f, 100.0f),
        makeWall(120.0f, -100.0f, 100.0f, 0.0f, 100.0f)
    });
    CHECK(map.traceLine({40.0f, 0.0f, 50.0f}, {104.0f, 0.0f, 50.0f}, 40.0f, true).blocked);

    map.setFacets({makeWall(0.0f, 0.0f, 100.0f, 0.0f, 100.0f)});
    CHECK(map.traceLine({20.0f, -40.0f, 50.0f}, {30.0f, 40.0f, 50.0f}, 40.0f, true).blocked);
}

TEST_CASE("path map body may graze a doorway edge but cannot clip through it")
{
    PathMap map;
    map.setFacets({makeHorizontalWall(0.0f, 0.0f, 100.0f, 0.0f, 100.0f)});
    CHECK_FALSE(map.traceLine({-40.0f, -64.0f, 50.0f}, {-40.0f, 64.0f, 50.0f}, 40.0f, true).blocked);
    CHECK(map.traceLine({-39.0f, -64.0f, 50.0f}, {-39.0f, 64.0f, 50.0f}, 40.0f, true).blocked);

    // A diagonal probe hitting an edge can still penetrate the wall with the rest of the body.
    map.setFacets({makeWall(0.0f, 40.0f * 0.70710678f, 29.0f, 0.0f, 100.0f)});
    CHECK(map.traceLine({-64.0f, 0.0f, 50.0f}, {64.0f, 0.0f, 50.0f}, 40.0f, true).blocked);
}

TEST_CASE("path map spatial grid preserves floor and trace queries")
{
    PathMap map;
    map.setFacets({
        makeFloor(-100.0f, 100.0f, -100.0f, 100.0f, 0.0f),
        makeWall(50.0f, -10.0f, 10.0f, 0.0f, 100.0f)
    });
    map.buildSpatialGrid(64.0f);

    const PathFloorSample floor = map.floorAt({0.0f, 0.0f, 30.0f});
    REQUIRE(floor.hasFloor);
    CHECK_FALSE(floor.inVoid);
    CHECK(std::fabs(floor.z - 0.0f) < TestEpsilon);

    const PathTraceResult blocked = map.traceLine({0.0f, 0.0f, 50.0f}, {100.0f, 0.0f, 50.0f});
    CHECK(blocked.blocked);
    CHECK_EQ(blocked.facetIndex, 1u);
}

TEST_CASE("path map open-space walking retains floor gaps and surrounding obstacles")
{
    PathObject object = {};
    object.radius = 20.0f;
    object.height = 200.0f;
    object.stepLength = 64.0f;
    PathFacet floor = makeFloor(0.0f, 512.0f, 0.0f, 512.0f, 0.0f);
    floor.blocking = true;
    const PathPoint from = {100.0f, 100.0f, 0.0f};
    const PathPoint to = {200.0f, 100.0f, 0.0f};
    for (const float cellSize : {0.0f, 128.0f, 512.0f})
    {
        INFO("cell size=" << cellSize);
        PathMap map;
        map.setFacets({floor});
        map.buildSpatialGrid(cellSize);
        CHECK(map.traceWalkSegment(from, to, object));

        PathFacet portal = makeWall(150.0f, 0.0f, 200.0f, 0.0f, 256.0f);
        portal.attributes.portal = true;
        map.setFacets({floor, portal});
        CHECK(map.traceWalkSegment(from, to, object));

        for (const PathFacet &obstacle : {
            makeWall(150.0f, 114.0f, 132.0f, 0.0f, 256.0f),
            makeWall(150.0f, 90.0f, 110.0f, 80.0f, 120.0f)})
        {
            map.setFacets({floor, obstacle});
            const PathWalkSegmentDebug blocked = map.debugTraceWalkSegment(from, to, object);
            CHECK_FALSE(blocked.success);
            CHECK_EQ(blocked.rejectReason, PathWalkRejectReason::Blocked);
            CHECK_EQ(blocked.blockedFacet, 1u);
        }

        PathFacet ceiling = makeFloor(0.0f, 512.0f, 0.0f, 512.0f, 150.0f);
        ceiling.kind = PathFacetKind::Ceiling;
        ceiling.walkableFloor = false;
        ceiling.blocking = true;
        map.setFacets({floor, ceiling});
        CHECK_FALSE(map.traceWalkSegment(from, to, object));

        PathFacet gapLeft = makeFloor(0.0f, 10.0f, 0.0f, 512.0f, 0.0f);
        PathFacet gapRight = makeFloor(14.0f, 512.0f, 0.0f, 512.0f, 0.0f);
        gapLeft.blocking = true;
        gapRight.blocking = true;
        map.setFacets({gapLeft, gapRight});
        const PathWalkSegmentDebug gap = map.debugTraceWalkSegment({8.0f, 100.0f, 0.0f}, to, object);
        CHECK_FALSE(gap.success);
        CHECK_EQ(gap.rejectReason, PathWalkRejectReason::SampleNoFloor);
        CHECK_EQ(gap.sampleIndex, 2u);
    }
}

TEST_CASE("path map broad bounds scans preserve grid first-hit order and body traces")
{
    std::vector<PathFacet> facets = {
        makeWall(256.0f, -2048.0f, 2048.0f, -2048.0f, 2048.0f),
        makeWall(-256.0f, -2048.0f, 2048.0f, -2048.0f, 2048.0f),
        makeFloor(-2048.0f, 2048.0f, -2048.0f, 2048.0f, -2048.0f)
    };
    PathMap scanMap;
    scanMap.setFacets(facets);
    scanMap.buildSpatialGrid(256.0f);

    // Invalid padding leaves indexed geometry unchanged but makes the reference
    // choose grid traversal for the same queries (at most 18 cubed cells).
    facets.resize(8000);
    PathMap gridMap;
    gridMap.setFacets(facets);
    gridMap.buildSpatialGrid(256.0f);
    const std::array<std::pair<PathPoint, PathPoint>, 5> segments = {{{
        {-2048.0f, -2048.0f, -2048.0f}, {2048.0f, 2048.0f, 2048.0f}
    }, {
        {2048.0f, 2048.0f, 2048.0f}, {-2048.0f, -2048.0f, -2048.0f}
    }, {
        {-2048.0f, -2048.0f, 64.0f}, {2048.0f, 2048.0f, 64.0f}
    }, {
        {-2048.0f, 2500.0f, -2048.0f}, {2048.0f, 2500.0f, 2048.0f}
    }, {
        {-2048.0f, -2048.0f, 2500.0f}, {2048.0f, 2048.0f, 2500.0f}
    }}};
    for (const std::pair<PathPoint, PathPoint> &segment : segments)
    {
        for (float radius : {0.0f, 8.0f})
        {
            const PathTraceResult scanned = scanMap.traceLine(segment.first, segment.second, radius, true);
            const PathTraceResult indexed = gridMap.traceLine(segment.first, segment.second, radius, true);
            CHECK_EQ(scanned.blocked, indexed.blocked);
            if (indexed.blocked)
            {
                CHECK_EQ(scanned.facetIndex, indexed.facetIndex);
                CHECK(scanned.point.x == doctest::Approx(indexed.point.x));
                CHECK(scanned.point.y == doctest::Approx(indexed.point.y));
                CHECK(scanned.point.z == doctest::Approx(indexed.point.z));
            }
        }
    }
    // Cell order, rather than insertion order or ray direction, chooses the first hit.
    CHECK_EQ(scanMap.traceLine(segments[0].first, segments[0].second).facetIndex, 1u);
    CHECK_EQ(scanMap.traceLine(segments[1].first, segments[1].second).facetIndex, 1u);
    CHECK_FALSE(scanMap.traceLine(segments[3].first, segments[3].second).blocked);
}

TEST_CASE("path map bounds scans preserve walk clearance and floor snapping")
{
    std::vector<PathFacet> facets = {
        makeFloor(-128.0f, 128.0f, -128.0f, 128.0f, 0.0f),
        makeWall(0.0f, -48.0f, 48.0f, 0.0f, 128.0f)
    };
    PathMap scanMap;
    scanMap.setFacets(facets);
    scanMap.buildSpatialGrid(32.0f);
    facets.resize(8000);
    PathMap gridMap;
    gridMap.setFacets(facets);
    gridMap.buildSpatialGrid(32.0f);
    PathObject object = {};
    object.radius = 8.0f;
    object.height = 64.0f;
    object.stepLength = 24.0f;
    for (float y : {-64.0f, -48.0f, 0.0f, 48.0f, 64.0f})
    {
        const PathPoint from = {-16.0f, y, 0.0f};
        PathPoint scanned = {8.0f, y, 0.0f};
        PathPoint indexed = scanned;
        CHECK_EQ(scanMap.traceWalkSegment(from, scanned, object), gridMap.traceWalkSegment(from, indexed, object));
        CHECK_EQ(scanMap.resolveWalkStep(from, scanned, object), gridMap.resolveWalkStep(from, indexed, object));
        CHECK(scanned.x == doctest::Approx(indexed.x));
        CHECK(scanned.y == doctest::Approx(indexed.y));
        CHECK(scanned.z == doctest::Approx(indexed.z));
    }
    bool scanValid = false;
    bool gridValid = false;
    const PathPoint source = {160.0f, 160.0f, 16.0f};
    const PathPoint scanned = scanMap.snapToNearestWalkableFloor(source, 512.0f, scanValid);
    const PathPoint indexed = gridMap.snapToNearestWalkableFloor(source, 512.0f, gridValid);
    CHECK_EQ(scanValid, gridValid);
    CHECK(scanned.x == doctest::Approx(indexed.x));
    CHECK(scanned.y == doctest::Approx(indexed.y));
    CHECK(scanned.z == doctest::Approx(indexed.z));
}

TEST_CASE("path map long grid walks retain thin obstacles and gaps after repeated cell queries")
{
    PathObject object = {};
    object.radius = 8.0f;
    object.height = 64.0f;
    object.stepHeight = 40.0f;
    object.dropHeight = 100.0f;
    const PathPoint from = {8.0f, 24.0f, 0.0f};
    const PathPoint to = {1016.0f, 24.0f, 0.0f};
    PathMap map;
    std::vector<PathFacet> facets = {makeFloor(0.0f, 1024.0f, 0.0f, 128.0f, 0.0f)};
    facets.resize(256);
    map.setFacets(facets);
    map.buildSpatialGrid(32.0f);
    REQUIRE(map.traceWalkSegment(from, to, object));
    facets[1] = makeWall(700.0f, 0.0f, 128.0f, 0.0f, 128.0f);
    map.setFacets(facets);
    const PathWalkSegmentDebug wall = map.debugTraceWalkSegment(from, to, object);
    CHECK_FALSE(wall.success);
    CHECK_EQ(wall.rejectReason, PathWalkRejectReason::Blocked);
    CHECK_EQ(wall.blockedFacet, 1u);
    facets[0] = makeFloor(0.0f, 700.0f, 0.0f, 128.0f, 0.0f);
    facets[1] = makeFloor(704.0f, 1024.0f, 0.0f, 128.0f, 0.0f);
    map.setFacets(facets);
    const PathWalkSegmentDebug gap = map.debugTraceWalkSegment(from, to, object);
    CHECK_FALSE(gap.success);
    CHECK_EQ(gap.rejectReason, PathWalkRejectReason::SampleNoFloor);
    CHECK(gap.probe.x > 700.0f);
    CHECK(gap.probe.x < 704.0f);
    facets[0] = makeFloor(0.0f, 1024.0f, 0.0f, 128.0f, 0.0f);
    facets[1] = makeFloor(700.0f, 704.0f, 0.0f, 128.0f, 48.0f);
    facets[1].kind = PathFacetKind::Ceiling;
    facets[1].blocking = true;
    facets[1].walkableFloor = false;
    map.setFacets(facets);
    CHECK_FALSE(map.traceWalkSegment(from, to, object));
    facets[1] = {};
    map.setFacets(facets);
    CHECK(map.traceWalkSegment(from, to, object));
}
