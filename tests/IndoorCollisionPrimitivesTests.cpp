#include "doctest/doctest.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorCollisionPrimitives.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/maps/MapDeltaData.h"

#include <cmath>
#include <optional>
#include <vector>

using OpenYAMM::Game::FaceAttribute;
using OpenYAMM::Game::IndoorFace;
using OpenYAMM::Game::IndoorFaceGeometryData;
using OpenYAMM::Game::IndoorFaceGeometryCache;
using OpenYAMM::Game::IndoorFaceKind;
using OpenYAMM::Game::IndoorInitialActorPlacement;
using OpenYAMM::Game::IndoorCeilingSample;
using OpenYAMM::Game::IndoorFloorSample;
using OpenYAMM::Game::IndoorFaceSweepOptions;
using OpenYAMM::Game::IndoorMapData;
using OpenYAMM::Game::IndoorProjectionAxis;
using OpenYAMM::Game::IndoorSector;
using OpenYAMM::Game::IndoorSweptBody;
using OpenYAMM::Game::IndoorSweptBodyBounds;
using OpenYAMM::Game::IndoorSweptCylinder;
using OpenYAMM::Game::IndoorSweptCylinderHit;
using OpenYAMM::Game::IndoorSweptFaceHit;
using OpenYAMM::Game::IndoorSweptSphere;
using OpenYAMM::Game::MapDeltaDoor;
using OpenYAMM::Game::MapDeltaData;
using OpenYAMM::Game::RuntimeMechanismState;
using OpenYAMM::Game::EventRuntimeState;
using OpenYAMM::Game::applyIndoorMechanismDoorToVertices;
using OpenYAMM::Game::buildIndoorMechanismAdjustedVertices;
using OpenYAMM::Game::chooseIndoorBountyHuntSpawnPoint;
using OpenYAMM::Game::buildIndoorSweptBodyBounds;
using OpenYAMM::Game::faceAttributeBit;
using OpenYAMM::Game::findIndoorStandingFloorHeight;
using OpenYAMM::Game::indoorSweptBodyBoundsTouchFace;
using OpenYAMM::Game::indoorSweptBodyTouchesPortalFace;
using OpenYAMM::Game::projectIndoorVelocityAlongPlane;
using OpenYAMM::Game::resolveIndoorInitialActorPlacement;
using OpenYAMM::Game::sampleIndoorCeiling;
using OpenYAMM::Game::sampleIndoorFloor;
using OpenYAMM::Game::selectNearestIndoorFaceHit;
using OpenYAMM::Game::sweepIndoorBodyAgainstCylinder;
using OpenYAMM::Game::sweepIndoorBodyAgainstFace;
using OpenYAMM::Game::sweepIndoorSphereAgainstCylinder;
using OpenYAMM::Game::sweepIndoorSphereAgainstFace;

namespace
{
constexpr float TestEpsilon = 0.001f;

IndoorFaceGeometryData makeVerticalWall(float x, size_t faceIndex = 0)
{
    IndoorFaceGeometryData geometry = {};
    geometry.faceIndex = faceIndex;
    geometry.hasPlane = true;
    geometry.kind = IndoorFaceKind::Wall;
    geometry.minX = x;
    geometry.maxX = x;
    geometry.minY = -100.0f;
    geometry.maxY = 100.0f;
    geometry.minZ = 0.0f;
    geometry.maxZ = 200.0f;
    geometry.projectionAxis = IndoorProjectionAxis::DropX;
    geometry.normal = {-1.0f, 0.0f, 0.0f};
    geometry.vertices = {
        {x, -100.0f, 0.0f},
        {x, 100.0f, 0.0f},
        {x, 100.0f, 200.0f},
        {x, -100.0f, 200.0f}
    };
    geometry.projectedVertices = {
        {-100.0f, 0.0f},
        {100.0f, 0.0f},
        {100.0f, 200.0f},
        {-100.0f, 200.0f}
    };
    return geometry;
}

IndoorFaceGeometryData makeVerticalPortal(float x, size_t faceIndex = 0)
{
    IndoorFaceGeometryData geometry = makeVerticalWall(x, faceIndex);
    geometry.isPortal = true;
    return geometry;
}

IndoorSweptSphere makeSphere(float x, float y, float z, float radius, float heightOffset = 0.0f)
{
    IndoorSweptSphere sphere = {};
    sphere.center = {x, y, z};
    sphere.radius = radius;
    sphere.heightOffset = heightOffset;
    return sphere;
}

IndoorSweptBody makeBody()
{
    IndoorSweptBody body = {};
    body.lowSphere = makeSphere(0.0f, 0.0f, 40.0f, 20.0f, 40.0f);
    body.highSphere = makeSphere(0.0f, 0.0f, 120.0f, 20.0f, 120.0f);
    return body;
}

IndoorSweptCylinder makeCylinder(float x, float y, float z, float radius, float height)
{
    IndoorSweptCylinder cylinder = {};
    cylinder.baseCenter = {x, y, z};
    cylinder.radius = radius;
    cylinder.height = height;
    return cylinder;
}

IndoorMapData makeInitialPlacementRoom()
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {0, -128, 0},
        {256, -128, 0},
        {256, 128, 0},
        {0, 128, 0},
        {0, -128, 200},
        {0, 128, 200}
    };

    IndoorFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;

    IndoorFace wall = {};
    wall.vertexIndices = {0, 4, 5, 3};
    wall.facetType = 1;
    wall.roomNumber = 1;

    IndoorSector emptySector = {};
    IndoorSector roomSector = {};
    roomSector.minX = 0;
    roomSector.maxX = 256;
    roomSector.minY = -128;
    roomSector.maxY = 128;
    roomSector.minZ = 0;
    roomSector.maxZ = 200;
    roomSector.floorFaceIds = {0};
    roomSector.wallFaceIds = {1};
    roomSector.faceIds = {0, 1};

    mapData.faces = {floor, wall};
    mapData.sectors = {emptySector, roomSector};
    return mapData;
}
}

TEST_CASE("incremental mechanism vertex update matches full adjusted vertex build")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {0, 0, 0},
        {100, 0, 0},
        {0, 100, 0}
    };

    MapDeltaDoor door = {};
    door.doorId = 12;
    door.directionX = 65536;
    door.directionY = 32768;
    door.directionZ = -65536;
    door.vertexIds = {0, 2};
    door.xOffsets = {10, 20};
    door.yOffsets = {30, 40};
    door.zOffsets = {50, 60};

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(door);

    RuntimeMechanismState mechanism = {};
    mechanism.currentDistance = 8.0f;

    EventRuntimeState eventRuntimeState = {};
    eventRuntimeState.mechanisms[door.doorId] = mechanism;

    const std::vector<OpenYAMM::Game::IndoorVertex> fullVertices =
        buildIndoorMechanismAdjustedVertices(mapData, &mapDeltaData, &eventRuntimeState);
    std::vector<OpenYAMM::Game::IndoorVertex> incrementalVertices = mapData.vertices;
    applyIndoorMechanismDoorToVertices(door, nullptr, mechanism.currentDistance, 1, incrementalVertices);

    REQUIRE(incrementalVertices.size() == fullVertices.size());

    for (size_t vertexIndex = 0; vertexIndex < fullVertices.size(); ++vertexIndex)
    {
        CHECK(incrementalVertices[vertexIndex].x == fullVertices[vertexIndex].x);
        CHECK(incrementalVertices[vertexIndex].y == fullVertices[vertexIndex].y);
        CHECK(incrementalVertices[vertexIndex].z == fullVertices[vertexIndex].z);
    }
}

TEST_CASE("indoor bounty hunt spawn chooses floor supported room face")
{
    const IndoorMapData mapData = makeInitialPlacementRoom();
    const std::optional<bx::Vec3> spawnPoint =
        chooseIndoorBountyHuntSpawnPoint(mapData, nullptr, nullptr, 1234);

    REQUIRE(spawnPoint.has_value());
    CHECK_EQ(spawnPoint->x, doctest::Approx(128.0f));
    CHECK_EQ(spawnPoint->y, doctest::Approx(0.0f));
    CHECK_EQ(spawnPoint->z, doctest::Approx(0.0f));
}

namespace
{
// An open-air BLV in small: a walkable ramp (z = x * 400 / 1024 over x 0..1024) above the sky shell's floor (an
// IndoorSky face at -800), as Guberland's terrain above its sky shell.
IndoorMapData makeRampOverSkyFloor()
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-2048, -2048, -800},
        {2048, -2048, -800},
        {2048, 2048, -800},
        {-2048, 2048, -800},
        {0, -512, 0},
        {1024, -512, 400},
        {1024, 512, 400},
        {0, 512, 0}
    };

    IndoorFace sky = {};
    sky.vertexIndices = {0, 1, 2, 3};
    sky.facetType = 3;
    sky.roomNumber = 1;
    sky.attributes = faceAttributeBit(FaceAttribute::IndoorSky);

    IndoorFace ramp = {};
    ramp.vertexIndices = {4, 5, 6, 7};
    ramp.facetType = 3;
    ramp.roomNumber = 1;

    IndoorSector emptySector = {};
    IndoorSector openSector = {};
    openSector.minX = -2048;
    openSector.maxX = 2048;
    openSector.minY = -2048;
    openSector.maxY = 2048;
    openSector.minZ = -800;
    openSector.maxZ = 2000;
    openSector.floorFaceIds = {0, 1};
    openSector.faceIds = {0, 1};

    mapData.faces = {sky, ramp};
    mapData.sectors = {emptySector, openSector};
    return mapData;
}
}

TEST_CASE("indoor spawn ground under a slope is the slope, never the sky floor below")
{
    const IndoorMapData mapData = makeRampOverSkyFloor();
    IndoorFaceGeometryCache cache(mapData.faces.size());

    // 200 under the ramp (a spawn's offset point uphill of its centre): the ramp, not the sky shell 800 down.
    const std::optional<float> underRamp =
        findIndoorStandingFloorHeight(mapData, mapData.vertices, cache, 512.0f, 0.0f, 0.0f, 1024.0f);
    REQUIRE(underRamp.has_value());
    CHECK_EQ(*underRamp, doctest::Approx(200.0f));

    // Far under the ramp, nearer the sky shell (a summon halfway to the party, at the mean of their heights under a
    // hill): still the ramp above.
    const std::optional<float> nearSky =
        findIndoorStandingFloorHeight(mapData, mapData.vertices, cache, 512.0f, 0.0f, -700.0f, 1024.0f);
    REQUIRE(nearSky.has_value());
    CHECK_EQ(*nearSky, doctest::Approx(200.0f));

    // Only the sky floor: no ground.
    CHECK_FALSE(findIndoorStandingFloorHeight(mapData, mapData.vertices, cache, -1500.0f, 0.0f, -800.0f, 1024.0f));
}

TEST_CASE("indoor bounty hunt spawn stands on walkable ground, never a sky face")
{
    const IndoorMapData mapData = makeRampOverSkyFloor();

    for (uint32_t seed = 1; seed <= 32; ++seed)
    {
        const std::optional<bx::Vec3> spawnPoint = chooseIndoorBountyHuntSpawnPoint(mapData, nullptr, nullptr, seed);
        REQUIRE(spawnPoint.has_value());
        CHECK_EQ(spawnPoint->x, doctest::Approx(512.0f));
        CHECK_EQ(spawnPoint->z, doctest::Approx(200.0f));
    }

    // An anchor over the sky floor alone is passed over for one on the ramp.
    const std::vector<bx::Vec3> anchors = {{-1500.0f, 0.0f, -800.0f}, {256.0f, 100.0f, 100.0f}};

    for (uint32_t seed = 1; seed <= 8; ++seed)
    {
        const std::optional<bx::Vec3> spawnPoint =
            chooseIndoorBountyHuntSpawnPoint(mapData, nullptr, nullptr, seed, anchors);
        REQUIRE(spawnPoint.has_value());
        CHECK_EQ(spawnPoint->x, doctest::Approx(256.0f));
        CHECK_EQ(spawnPoint->y, doctest::Approx(100.0f));
        CHECK_EQ(spawnPoint->z, doctest::Approx(100.0f));
    }
}

TEST_CASE("swept indoor sphere misses face outside polygon")
{
    const IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    const IndoorSweptSphere sphere = makeSphere(0.0f, 180.0f, 80.0f, 20.0f);
    const std::optional<IndoorSweptFaceHit> hit =
        sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, wall);

    CHECK_FALSE(hit.has_value());
}

TEST_CASE("swept indoor sphere can slide out of a touching cave triangle edge")
{
    // GW_2: the lower sphere of goblin 55 touches the edge of Goblinwatch face 1043.
    IndoorMapData map = {};
    map.vertices = {{9040, 2444, -768}, {10048, 2752, -768}, {9468, 2772, -588}};
    IndoorFace face = {};
    face.vertexIndices = {0, 1, 2};
    face.facetType = 4;
    map.faces = {face};
    IndoorFaceGeometryCache cache(1);
    const IndoorFaceGeometryData *pFace = cache.geometryForFace(map, map.vertices, 0);
    REQUIRE(pFace != nullptr);
    const IndoorSweptSphere sphere = makeSphere(9286.1796875f, 2637.93017578125f, -604.572021484375f, 56.0f);
    const std::optional<IndoorSweptFaceHit> hit =
        sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 2.0f, *pFace);
    REQUIRE(hit.has_value());
    REQUIRE(hit->boundaryHit);
    CHECK_EQ(hit->moveDistance, 0.0f);
    const bx::Vec3 slide = projectIndoorVelocityAlongPlane({1.0f, 0.0f, 0.0f}, hit->normal);
    CHECK_FALSE(sweepIndoorSphereAgainstFace(sphere, slide, 2.0f, *pFace).has_value());
    // A tangent response must not disable subsequent inward movement.
    CHECK(sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 2.0f, *pFace).has_value());
}

TEST_CASE("initial indoor actor placement snaps to floor without moving clear actor")
{
    IndoorMapData mapData = makeInitialPlacementRoom();
    IndoorFaceGeometryCache geometryCache(mapData.faces.size());

    const IndoorInitialActorPlacement placement =
        resolveIndoorInitialActorPlacement(
            mapData,
            mapData.vertices,
            geometryCache,
            80.0f,
            0.0f,
            32.0f,
            16.0f,
            64.0f,
            false,
            128.0f,
            256.0f);

    CHECK(placement.hasFloor);
    CHECK_FALSE(placement.movedHorizontally);
    CHECK_FALSE(placement.wallOverlapResolved);
    CHECK_EQ(placement.sectorId, 1);
    CHECK_EQ(placement.x, doctest::Approx(80.0f));
    CHECK_EQ(placement.y, doctest::Approx(0.0f));
    CHECK_EQ(placement.z, doctest::Approx(0.0f));
}

TEST_CASE("initial indoor actor placement clears wall-overlapping actor")
{
    IndoorMapData mapData = makeInitialPlacementRoom();
    IndoorFaceGeometryCache geometryCache(mapData.faces.size());

    const IndoorInitialActorPlacement placement =
        resolveIndoorInitialActorPlacement(
            mapData,
            mapData.vertices,
            geometryCache,
            8.0f,
            0.0f,
            32.0f,
            16.0f,
            64.0f,
            false,
            128.0f,
            256.0f);

    CHECK(placement.hasFloor);
    CHECK(placement.movedHorizontally);
    CHECK(placement.wallOverlapResolved);
    CHECK_EQ(placement.sectorId, 1);
    CHECK_GE(placement.x, 16.0f);
    CHECK_EQ(placement.y, doctest::Approx(0.0f));
    CHECK_EQ(placement.z, doctest::Approx(0.0f));
}

TEST_CASE("swept indoor sphere touching a plane can pass its polygon edge without snagging")
{
    const IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    // A near-edge horizontal offset can vanish when added to radius squared in float precision.
    // Contact with the plane still leaves every point on its boundary outside the sphere.
    for (const float x : {26.0f, 174.0f})
    {
        const IndoorSweptSphere sphere = makeSphere(x, 100.01f, 100.0f, 74.0f);
        CHECK_FALSE(sweepIndoorSphereAgainstFace(sphere, {0.0f, -1.0f, 0.0f}, 5.0f, wall));
    }

    const IndoorSweptSphere clippingSphere = makeSphere(26.25f, 107.0f, 100.0f, 74.0f);
    REQUIRE(sweepIndoorSphereAgainstFace(clippingSphere, {0.0f, -1.0f, 0.0f}, 5.0f, wall));
    const IndoorSweptSphere touchingSphere = makeSphere(26.0f, 99.0f, 100.0f, 74.0f);
    REQUIRE(sweepIndoorSphereAgainstFace(touchingSphere, {1.0f, 0.0f, 0.0f}, 5.0f, wall));
}

TEST_CASE("swept indoor sphere preserves small clearance beneath a doorway edge")
{
    const IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    IndoorFaceSweepOptions options;
    options.backoffDistance = 0.0f;
    for (const float y : {0.0f, 100.0f})
    {
        // The squared horizontal clearance is lost when added to 127 squared in float precision.
        const IndoorSweptSphere sphere = makeSphere(100.015625f, y, -127.0f, 127.0f);
        const std::optional<IndoorSweptFaceHit> hit =
            sweepIndoorSphereAgainstFace(sphere, {-1.0f, 0.0f, 0.0f}, 5.0f, wall, options);
        REQUIRE(hit.has_value());
        CHECK_EQ(hit->moveDistance, doctest::Approx(0.015625f));
        CHECK_EQ(hit->normal.x, doctest::Approx(0.0f));
        CHECK_EQ(hit->normal.z, doctest::Approx(-1.0f));
        const IndoorSweptSphere clearSphere = makeSphere(100.015625f, y, -127.01f, 127.0f);
        CHECK_FALSE(sweepIndoorSphereAgainstFace(clearSphere, {-1.0f, 0.0f, 0.0f}, 5.0f, wall, options));
    }
}

TEST_CASE("swept indoor sphere hits wall at sphere radius")
{
    IndoorFaceSweepOptions options = {};
    options.backoffDistance = 0.0f;
    const IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    const IndoorSweptSphere sphere = makeSphere(0.0f, 0.0f, 80.0f, 20.0f);
    const std::optional<IndoorSweptFaceHit> hit =
        sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, wall, options);

    REQUIRE(hit.has_value());
    CHECK_EQ(hit->faceIndex, 0u);
    CHECK(std::fabs(hit->moveDistance - 80.0f) < TestEpsilon);
    CHECK(std::fabs(hit->point.x - 100.0f) < TestEpsilon);
    CHECK(std::fabs(hit->point.y) < TestEpsilon);
    CHECK(std::fabs(hit->point.z - 80.0f) < TestEpsilon);
}

TEST_CASE("swept indoor sphere hits face edge when plane contact is outside polygon")
{
    IndoorFaceSweepOptions options = {};
    options.backoffDistance = 0.0f;
    IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    wall.minY = -20.0f;
    wall.maxY = 20.0f;
    wall.minZ = 0.0f;
    wall.maxZ = 40.0f;
    wall.vertices = {
        {100.0f, -20.0f, 0.0f},
        {100.0f, 20.0f, 0.0f},
        {100.0f, 20.0f, 40.0f},
        {100.0f, -20.0f, 40.0f}
    };
    wall.projectedVertices = {
        {-20.0f, 0.0f},
        {20.0f, 0.0f},
        {20.0f, 40.0f},
        {-20.0f, 40.0f}
    };

    const IndoorSweptSphere sphere = makeSphere(0.0f, 50.0f, 20.0f, 30.0f);
    const std::optional<IndoorSweptFaceHit> hit =
        sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, wall, options);

    REQUIRE(hit.has_value());
    CHECK(std::fabs(hit->moveDistance - 100.0f) < TestEpsilon);
    CHECK(std::fabs(hit->point.x - 100.0f) < TestEpsilon);
    CHECK(std::fabs(hit->point.y - 20.0f) < TestEpsilon);
    CHECK(std::fabs(hit->point.z - 20.0f) < TestEpsilon);
}

TEST_CASE("swept indoor sphere hits face vertex when plane contact and edges miss")
{
    IndoorFaceSweepOptions options = {};
    options.backoffDistance = 0.0f;
    IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    wall.minY = -20.0f;
    wall.maxY = 20.0f;
    wall.minZ = 0.0f;
    wall.maxZ = 40.0f;
    wall.vertices = {
        {100.0f, -20.0f, 0.0f},
        {100.0f, 20.0f, 0.0f},
        {100.0f, 20.0f, 40.0f},
        {100.0f, -20.0f, 40.0f}
    };
    wall.projectedVertices = {
        {-20.0f, 0.0f},
        {20.0f, 0.0f},
        {20.0f, 40.0f},
        {-20.0f, 40.0f}
    };

    const IndoorSweptSphere sphere = makeSphere(0.0f, 50.0f, 70.0f, 50.0f);
    const std::optional<IndoorSweptFaceHit> hit =
        sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, wall, options);

    REQUIRE(hit.has_value());
    CHECK(hit->moveDistance > 73.5f);
    CHECK(hit->moveDistance < 73.6f);
    CHECK(std::fabs(hit->point.x - 100.0f) < TestEpsilon);
    CHECK(std::fabs(hit->point.y - 20.0f) < TestEpsilon);
    CHECK(std::fabs(hit->point.z - 40.0f) < TestEpsilon);
}

TEST_CASE("nearest indoor face hit selects earliest adjusted distance")
{
    IndoorFaceSweepOptions options = {};
    options.backoffDistance = 0.0f;
    const IndoorFaceGeometryData farWall = makeVerticalWall(160.0f, 1u);
    const IndoorFaceGeometryData nearWall = makeVerticalWall(100.0f, 2u);
    const std::vector<const IndoorFaceGeometryData *> faces = {&farWall, &nearWall};
    const std::optional<IndoorSweptFaceHit> hit =
        selectNearestIndoorFaceHit(makeBody(), {1.0f, 0.0f, 0.0f}, 200.0f, faces, options);

    REQUIRE(hit.has_value());
    CHECK_EQ(hit->faceIndex, 2u);
    CHECK(std::fabs(hit->moveDistance - 80.0f) < TestEpsilon);
}

TEST_CASE("body sweep uses middle sphere when low and high spheres miss")
{
    IndoorFaceSweepOptions options = {};
    options.backoffDistance = 0.0f;
    IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    wall.minZ = 70.0f;
    wall.maxZ = 90.0f;
    wall.vertices = {
        {100.0f, -100.0f, 70.0f},
        {100.0f, 100.0f, 70.0f},
        {100.0f, 100.0f, 90.0f},
        {100.0f, -100.0f, 90.0f}
    };
    wall.projectedVertices = {
        {-100.0f, 70.0f},
        {100.0f, 70.0f},
        {100.0f, 90.0f},
        {-100.0f, 90.0f}
    };

    const std::optional<IndoorSweptFaceHit> hit =
        sweepIndoorBodyAgainstFace(makeBody(), {1.0f, 0.0f, 0.0f}, 150.0f, wall, options);

    REQUIRE(hit.has_value());
    CHECK(std::fabs(hit->heightOffset - 80.0f) < TestEpsilon);
}

TEST_CASE("body sweep uses face-center-height sphere when middle sphere misses")
{
    IndoorFaceSweepOptions options = {};
    options.backoffDistance = 0.0f;
    IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    wall.minZ = 100.0f;
    wall.maxZ = 104.0f;
    wall.vertices = {
        {100.0f, -100.0f, 100.0f},
        {100.0f, 100.0f, 100.0f},
        {100.0f, 100.0f, 104.0f},
        {100.0f, -100.0f, 104.0f}
    };
    wall.projectedVertices = {
        {-100.0f, 100.0f},
        {100.0f, 100.0f},
        {100.0f, 104.0f},
        {-100.0f, 104.0f}
    };

    const std::optional<IndoorSweptFaceHit> hit =
        sweepIndoorBodyAgainstFace(makeBody(), {1.0f, 0.0f, 0.0f}, 150.0f, wall, options);

    REQUIRE(hit.has_value());
    CHECK(std::fabs(hit->heightOffset - 102.0f) < TestEpsilon);
}

TEST_CASE("swept indoor face collision ignores untouchable and masked faces")
{
    IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    wall.attributes = faceAttributeBit(FaceAttribute::Untouchable);
    const IndoorSweptSphere sphere = makeSphere(0.0f, 0.0f, 80.0f, 20.0f);

    CHECK_FALSE(sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, wall).has_value());

    wall.attributes = 0;
    std::vector<uint8_t> mechanismMask(1u, 0u);
    IndoorFaceSweepOptions options = {};
    options.pMechanismBlockingFaceMask = &mechanismMask;

    CHECK_FALSE(sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, wall, options).has_value());
}

TEST_CASE("swept indoor face collision keeps invisible walls solid until untouchable")
{
    IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    wall.attributes = faceAttributeBit(FaceAttribute::Invisible);
    const IndoorSweptSphere sphere = makeSphere(0.0f, 0.0f, 80.0f, 20.0f);

    CHECK(sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, wall).has_value());

    wall.attributes |= faceAttributeBit(FaceAttribute::Untouchable);
    CHECK_FALSE(sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, wall).has_value());
}

TEST_CASE("indoor face geometry cache uses runtime untouchable overrides")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {100, -100, 0},
        {100, 100, 0},
        {100, 100, 200},
        {100, -100, 200}
    };

    OpenYAMM::Game::IndoorFace wall = {};
    wall.vertexIndices = {0, 1, 2, 3};
    wall.facetType = 1;
    mapData.faces.push_back(wall);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.faceAttributes = {faceAttributeBit(FaceAttribute::Untouchable)};
    mapDeltaData.surfaceRevision = 1;

    IndoorFaceGeometryCache geometryCache(1);
    geometryCache.setAttributeOverrides(&mapDeltaData);

    const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(mapData, mapData.vertices, 0);
    REQUIRE(pGeometry != nullptr);
    CHECK((pGeometry->attributes & faceAttributeBit(FaceAttribute::Untouchable)) != 0);
    const IndoorSweptSphere sphere = makeSphere(0.0f, 0.0f, 80.0f, 20.0f);
    CHECK_FALSE(sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, *pGeometry).has_value());

    mapDeltaData.faceAttributes[0] = 0;
    ++mapDeltaData.surfaceRevision;
    geometryCache.setAttributeOverrides(&mapDeltaData);

    pGeometry = geometryCache.geometryForFace(mapData, mapData.vertices, 0);
    REQUIRE(pGeometry != nullptr);
    CHECK((pGeometry->attributes & faceAttributeBit(FaceAttribute::Untouchable)) == 0);
    CHECK(sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, *pGeometry).has_value());
}

TEST_CASE("indoor floor sampling ignores horizontal portal faces")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, -128, 0},
        {128, -128, 0},
        {128, 128, 0},
        {-128, 128, 0},
        {-128, -128, -96},
        {128, -128, -96},
        {128, 128, -96},
        {-128, 128, -96}
    };

    IndoorFace portalFloor = {};
    portalFloor.attributes = faceAttributeBit(FaceAttribute::IsPortal);
    portalFloor.vertexIndices = {0, 1, 2, 3};
    portalFloor.facetType = 3;
    portalFloor.roomNumber = 0;
    portalFloor.roomBehindNumber = 1;
    portalFloor.isPortal = true;

    IndoorFace solidFloor = {};
    solidFloor.vertexIndices = {4, 5, 6, 7};
    solidFloor.facetType = 3;
    solidFloor.roomNumber = 0;

    OpenYAMM::Game::IndoorSector sector = {};
    sector.flags = 0x8;
    sector.floorFaceIds = {1};
    sector.portalFaceIds = {0};

    mapData.faces = {portalFloor, solidFloor};
    mapData.sectors = {sector};

    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    const IndoorFloorSample sample =
        sampleIndoorFloor(mapData, mapData.vertices, 0.0f, 0.0f, 8.0f, 16.0f, 160.0f, 0, nullptr, &geometryCache);

    REQUIRE(sample.hasFloor);
    CHECK_EQ(sample.faceIndex, 1u);
    CHECK_EQ(sample.height, doctest::Approx(-96.0f));
}

TEST_CASE("indoor floor sampling ignores runtime untouchable faces")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, -128, 0},
        {128, -128, 0},
        {128, 128, 0},
        {-128, 128, 0},
        {-128, -128, -96},
        {128, -128, -96},
        {128, 128, -96},
        {-128, 128, -96}
    };

    IndoorFace hiddenFloor = {};
    hiddenFloor.vertexIndices = {0, 1, 2, 3};
    hiddenFloor.facetType = 3;
    hiddenFloor.roomNumber = 0;

    IndoorFace lowerFloor = {};
    lowerFloor.vertexIndices = {4, 5, 6, 7};
    lowerFloor.facetType = 3;
    lowerFloor.roomNumber = 0;

    IndoorSector sector = {};
    sector.floorFaceIds = {0, 1};
    mapData.faces = {hiddenFloor, lowerFloor};
    mapData.sectors = {sector};

    MapDeltaData mapDeltaData = {};
    mapDeltaData.faceAttributes = {
        faceAttributeBit(FaceAttribute::Invisible) | faceAttributeBit(FaceAttribute::Untouchable),
        0
    };
    mapDeltaData.surfaceRevision = 1;

    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    geometryCache.setAttributeOverrides(&mapDeltaData);

    const IndoorFloorSample sample =
        sampleIndoorFloor(mapData, mapData.vertices, 0.0f, 0.0f, 8.0f, 16.0f, 160.0f, 0, nullptr, &geometryCache);

    REQUIRE(sample.hasFloor);
    CHECK_EQ(sample.faceIndex, 1u);
    CHECK_EQ(sample.height, doctest::Approx(-96.0f));
}

TEST_CASE("indoor ceiling sampling ignores runtime untouchable faces")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, -128, 128},
        {128, -128, 128},
        {128, 128, 128},
        {-128, 128, 128},
        {-128, -128, 256},
        {128, -128, 256},
        {128, 128, 256},
        {-128, 128, 256}
    };

    IndoorFace hiddenCeiling = {};
    hiddenCeiling.vertexIndices = {0, 1, 2, 3};
    hiddenCeiling.facetType = 5;
    hiddenCeiling.roomNumber = 0;

    IndoorFace upperCeiling = {};
    upperCeiling.vertexIndices = {4, 5, 6, 7};
    upperCeiling.facetType = 5;
    upperCeiling.roomNumber = 0;

    IndoorSector sector = {};
    sector.ceilingFaceIds = {0, 1};
    mapData.faces = {hiddenCeiling, upperCeiling};
    mapData.sectors = {sector};

    MapDeltaData mapDeltaData = {};
    mapDeltaData.faceAttributes = {
        faceAttributeBit(FaceAttribute::Invisible) | faceAttributeBit(FaceAttribute::Untouchable),
        0
    };
    mapDeltaData.surfaceRevision = 1;

    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    geometryCache.setAttributeOverrides(&mapDeltaData);

    const IndoorCeilingSample sample =
        sampleIndoorCeiling(mapData, mapData.vertices, 0.0f, 0.0f, 0.0f, 0, nullptr, &geometryCache);

    REQUIRE(sample.hasCeiling);
    CHECK_EQ(sample.faceIndex, 1u);
    CHECK_EQ(sample.height, doctest::Approx(256.0f));
}

TEST_CASE("indoor ceiling sampling ignores coplanar ceiling at foot height")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, -128, 0},
        {128, -128, 0},
        {128, 128, 0},
        {-128, 128, 0},
        {-128, -128, 256},
        {128, -128, 256},
        {128, 128, 256},
        {-128, 128, 256}
    };

    IndoorFace lowerCeiling = {};
    lowerCeiling.vertexIndices = {0, 3, 2, 1};
    lowerCeiling.facetType = 5;
    lowerCeiling.roomNumber = 0;

    IndoorFace upperCeiling = {};
    upperCeiling.vertexIndices = {4, 7, 6, 5};
    upperCeiling.facetType = 5;
    upperCeiling.roomNumber = 0;

    IndoorSector sector = {};
    sector.ceilingFaceIds = {0, 1};
    mapData.faces = {lowerCeiling, upperCeiling};
    mapData.sectors = {sector};

    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    const IndoorCeilingSample sample =
        sampleIndoorCeiling(mapData, mapData.vertices, 0.0f, 0.0f, 0.0f, 0, nullptr, &geometryCache);

    REQUIRE(sample.hasCeiling);
    CHECK_EQ(sample.faceIndex, 1u);
    CHECK_EQ(sample.height, doctest::Approx(256.0f));
}

TEST_CASE("indoor floor sampling keeps steep in-between floor height without making it walkable")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, -128, 0},
        {128, -128, 512},
        {128, 128, 512},
        {-128, 128, 0}
    };

    IndoorFace steepFloor = {};
    steepFloor.vertexIndices = {0, 1, 2, 3};
    steepFloor.facetType = 4;
    steepFloor.roomNumber = 0;

    IndoorSector sector = {};
    sector.floorFaceIds = {0};
    mapData.faces = {steepFloor};
    mapData.sectors = {sector};

    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(mapData, mapData.vertices, 0);
    REQUIRE(pGeometry != nullptr);
    CHECK_EQ(pGeometry->kind, IndoorFaceKind::Wall);
    CHECK_FALSE(pGeometry->isWalkable);

    const IndoorFloorSample sample =
        sampleIndoorFloor(mapData, mapData.vertices, 0.0f, 0.0f, 256.0f, 16.0f, 160.0f, 0, nullptr, &geometryCache);

    REQUIRE(sample.hasFloor);
    CHECK_FALSE(sample.isWalkable);
    CHECK_EQ(sample.faceIndex, 0u);
    CHECK_EQ(sample.height, doctest::Approx(256.0f));
}

TEST_CASE("indoor ceiling sampling keeps in-between ceiling height")
{
    IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, -128, 512},
        {-128, 128, 512},
        {128, 128, 0},
        {128, -128, 0}
    };

    IndoorFace steepCeiling = {};
    steepCeiling.vertexIndices = {0, 1, 2, 3};
    steepCeiling.facetType = 6;
    steepCeiling.roomNumber = 0;

    IndoorSector sector = {};
    sector.ceilingFaceIds = {0};
    mapData.faces = {steepCeiling};
    mapData.sectors = {sector};

    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(mapData, mapData.vertices, 0);
    REQUIRE(pGeometry != nullptr);
    CHECK_EQ(pGeometry->kind, IndoorFaceKind::Wall);
    CHECK(pGeometry->normal.z < 0.0f);

    const IndoorCeilingSample sample =
        sampleIndoorCeiling(mapData, mapData.vertices, 0.0f, 0.0f, 0.0f, 0, nullptr, &geometryCache);

    REQUIRE(sample.hasCeiling);
    CHECK_EQ(sample.faceIndex, 0u);
    CHECK_EQ(sample.height, doctest::Approx(256.0f));
}

TEST_CASE("wall velocity projection removes movement into plane")
{
    const bx::Vec3 projected = projectIndoorVelocityAlongPlane({10.0f, 5.0f, 0.0f}, {-1.0f, 0.0f, 0.0f});

    CHECK(std::fabs(projected.x) < TestEpsilon);
    CHECK(std::fabs(projected.y - 5.0f) < TestEpsilon);
    CHECK(std::fabs(projected.z) < TestEpsilon);
}

TEST_CASE("swept indoor sphere hits cylinder before destination overlap")
{
    const IndoorSweptSphere sphere = makeSphere(0.0f, 0.0f, 40.0f, 20.0f, 40.0f);
    const IndoorSweptCylinder cylinder = makeCylinder(100.0f, 0.0f, 0.0f, 30.0f, 120.0f);
    const std::optional<IndoorSweptCylinderHit> hit =
        sweepIndoorSphereAgainstCylinder(sphere, {1.0f, 0.0f, 0.0f}, 120.0f, cylinder, 0.0f);

    REQUIRE(hit.has_value());
    CHECK(std::fabs(hit->moveDistance - 50.0f) < TestEpsilon);
    CHECK(std::fabs(hit->normal.x + 1.0f) < TestEpsilon);
    CHECK(std::fabs(hit->normal.y) < TestEpsilon);
}

TEST_CASE("swept indoor body cylinder hit rejects vertical miss")
{
    const IndoorSweptCylinder cylinder = makeCylinder(100.0f, 0.0f, 220.0f, 30.0f, 60.0f);
    const std::optional<IndoorSweptCylinderHit> hit =
        sweepIndoorBodyAgainstCylinder(makeBody(), {1.0f, 0.0f, 0.0f}, 120.0f, cylinder, 0.0f);

    CHECK_FALSE(hit.has_value());
}

TEST_CASE("swept body bounds include start and end spheres")
{
    const IndoorSweptBodyBounds bounds = buildIndoorSweptBodyBounds(makeBody(), {1.0f, 0.0f, 0.0f}, 90.0f);

    CHECK(std::fabs(bounds.minX + 20.0f) < TestEpsilon);
    CHECK(std::fabs(bounds.maxX - 110.0f) < TestEpsilon);
    CHECK(std::fabs(bounds.minY + 20.0f) < TestEpsilon);
    CHECK(std::fabs(bounds.maxY - 20.0f) < TestEpsilon);
    CHECK(std::fabs(bounds.minZ - 20.0f) < TestEpsilon);
    CHECK(std::fabs(bounds.maxZ - 140.0f) < TestEpsilon);
}

TEST_CASE("swept body portal touch requires bounds and plane proximity")
{
    const IndoorFaceGeometryData portal = makeVerticalPortal(100.0f);

    CHECK(indoorSweptBodyTouchesPortalFace(makeBody(), {1.0f, 0.0f, 0.0f}, 90.0f, portal));
    CHECK_FALSE(indoorSweptBodyTouchesPortalFace(makeBody(), {1.0f, 0.0f, 0.0f}, 50.0f, portal));

    IndoorSweptBody parallelBody = makeBody();
    parallelBody.lowSphere.center.x = 70.0f;
    parallelBody.highSphere.center.x = 70.0f;

    CHECK_FALSE(indoorSweptBodyTouchesPortalFace(parallelBody, {0.0f, 1.0f, 0.0f}, 20.0f, portal));

    parallelBody.lowSphere.center.x = 82.0f;
    parallelBody.highSphere.center.x = 82.0f;

    CHECK(indoorSweptBodyTouchesPortalFace(parallelBody, {0.0f, 1.0f, 0.0f}, 20.0f, portal));
}

TEST_CASE("swept body bounds face touch can be padded")
{
    const IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    const IndoorSweptBodyBounds bounds = buildIndoorSweptBodyBounds(makeBody(), {1.0f, 0.0f, 0.0f}, 75.0f);

    CHECK_FALSE(indoorSweptBodyBoundsTouchFace(bounds, wall));
    CHECK(indoorSweptBodyBoundsTouchFace(bounds, wall, 5.0f));
}
