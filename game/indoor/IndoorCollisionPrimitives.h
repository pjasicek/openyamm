#pragma once

#include "game/indoor/IndoorGeometryUtils.h"

#include <bx/math.h>

#include <cstddef>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorSweptSphere
{
    bx::Vec3 center = {0.0f, 0.0f, 0.0f};
    float radius = 0.0f;
    float heightOffset = 0.0f;
};

struct IndoorSweptBody
{
    IndoorSweptSphere lowSphere;
    IndoorSweptSphere highSphere;
};

struct IndoorSweptFaceHit
{
    bool hit = false;
    bool boundaryHit = false;
    size_t faceIndex = 0;
    bx::Vec3 point = {0.0f, 0.0f, 0.0f};
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
    float moveDistance = 0.0f;
    float adjustedMoveDistance = 0.0f;
    float heightOffset = 0.0f;
};

struct IndoorSweptCylinder
{
    bx::Vec3 baseCenter = {0.0f, 0.0f, 0.0f};
    float radius = 0.0f;
    float height = 0.0f;
};

struct IndoorSweptCylinderHit
{
    bool hit = false;
    bx::Vec3 point = {0.0f, 0.0f, 0.0f};
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
    float moveDistance = 0.0f;
    float adjustedMoveDistance = 0.0f;
    float heightOffset = 0.0f;
};

struct IndoorSweptBodyBounds
{
    float minX = 0.0f;
    float maxX = 0.0f;
    float minY = 0.0f;
    float maxY = 0.0f;
    float minZ = 0.0f;
    float maxZ = 0.0f;
};

struct IndoorFaceSweepOptions
{
    const std::vector<uint8_t> *pCollisionFaceMask = nullptr;
    const std::vector<uint8_t> *pMechanismBlockingFaceMask = nullptr;
    bool includePortalFaces = false;
    float backoffDistance = 1.0f;
};

IndoorSweptBodyBounds buildIndoorSweptBodyBounds(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance
);
bool indoorSweptBodyBoundsTouchFace(
    const IndoorSweptBodyBounds &bounds,
    const IndoorFaceGeometryData &geometry,
    float padding = 0.0f
);
bool indoorSweptBodyTouchesPortalFace(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorFaceGeometryData &geometry,
    float planeSlack = 4.0f
);
bool canSweepAgainstIndoorFace(
    const IndoorFaceGeometryData &geometry,
    const IndoorFaceSweepOptions &options = {}
);
std::optional<IndoorSweptFaceHit> sweepIndoorSphereAgainstFace(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorFaceGeometryData &geometry,
    const IndoorFaceSweepOptions &options = {}
);
std::optional<IndoorSweptFaceHit> sweepIndoorBodyAgainstFace(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorFaceGeometryData &geometry,
    const IndoorFaceSweepOptions &options = {}
);
std::optional<IndoorSweptFaceHit> selectNearestIndoorFaceHit(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance,
    const std::vector<const IndoorFaceGeometryData *> &faces,
    const IndoorFaceSweepOptions &options = {}
);
std::optional<IndoorSweptCylinderHit> sweepIndoorSphereAgainstCylinder(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorSweptCylinder &cylinder,
    float backoffDistance = 1.0f
);
std::optional<IndoorSweptCylinderHit> sweepIndoorBodyAgainstCylinder(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorSweptCylinder &cylinder,
    float backoffDistance = 1.0f
);
bx::Vec3 projectIndoorVelocityAlongPlane(
    const bx::Vec3 &velocity,
    const bx::Vec3 &normal,
    float damping = 1.0f
);
}
