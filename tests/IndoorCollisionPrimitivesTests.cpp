#include "doctest/doctest.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorCollisionPrimitives.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/maps/MapDeltaData.h"

#include <cmath>
#include <optional>
#include <vector>

using OpenYAMM::Game::FaceAttribute;
using OpenYAMM::Game::IndoorFaceGeometryData;
using OpenYAMM::Game::IndoorFaceGeometryCache;
using OpenYAMM::Game::IndoorFaceKind;
using OpenYAMM::Game::IndoorFaceSweepOptions;
using OpenYAMM::Game::IndoorMapData;
using OpenYAMM::Game::IndoorProjectionAxis;
using OpenYAMM::Game::IndoorSweptBody;
using OpenYAMM::Game::IndoorSweptBodyBounds;
using OpenYAMM::Game::IndoorSweptCylinder;
using OpenYAMM::Game::IndoorSweptCylinderHit;
using OpenYAMM::Game::IndoorSweptFaceHit;
using OpenYAMM::Game::IndoorSweptSphere;
using OpenYAMM::Game::MapDeltaData;
using OpenYAMM::Game::buildIndoorSweptBodyBounds;
using OpenYAMM::Game::faceAttributeBit;
using OpenYAMM::Game::indoorSweptBodyBoundsTouchFace;
using OpenYAMM::Game::indoorSweptBodyTouchesPortalFace;
using OpenYAMM::Game::projectIndoorVelocityAlongPlane;
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
}

TEST_CASE("swept indoor sphere misses face outside polygon")
{
    const IndoorFaceGeometryData wall = makeVerticalWall(100.0f);
    const IndoorSweptSphere sphere = makeSphere(0.0f, 180.0f, 80.0f, 20.0f);
    const std::optional<IndoorSweptFaceHit> hit =
        sweepIndoorSphereAgainstFace(sphere, {1.0f, 0.0f, 0.0f}, 150.0f, wall);

    CHECK_FALSE(hit.has_value());
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
