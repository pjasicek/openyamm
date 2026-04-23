#include "game/indoor/IndoorCollisionPrimitives.h"

#include "game/FaceEnums.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float CollisionEpsilon = 0.0001f;

float vecDot(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

float vecLength(const bx::Vec3 &value)
{
    return std::sqrt(vecDot(value, value));
}

bx::Vec3 vecNormalize(const bx::Vec3 &value)
{
    const float length = vecLength(value);

    if (length <= CollisionEpsilon)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {value.x / length, value.y / length, value.z / length};
}

bx::Vec3 vecAdd(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

bx::Vec3 vecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

bx::Vec3 vecScale(const bx::Vec3 &value, float scale)
{
    return {value.x * scale, value.y * scale, value.z * scale};
}

IndoorProjectedFacePoint projectFacePoint(IndoorProjectionAxis projectionAxis, const bx::Vec3 &vertex)
{
    switch (projectionAxis)
    {
        case IndoorProjectionAxis::DropX:
            return {vertex.y, vertex.z};
        case IndoorProjectionAxis::DropY:
            return {vertex.x, vertex.z};
        case IndoorProjectionAxis::DropZ:
        default:
            return {vertex.x, vertex.y};
    }
}

bool isPointInsideProjectedPolygon(
    const IndoorProjectedFacePoint &point,
    const std::vector<IndoorProjectedFacePoint> &vertices
)
{
    if (vertices.size() < 3)
    {
        return false;
    }

    auto pointOnSegment =
        [&point](const IndoorProjectedFacePoint &start, const IndoorProjectedFacePoint &end) -> bool
    {
        const float cross =
            (point.x - start.x) * (end.y - start.y)
            - (point.y - start.y) * (end.x - start.x);

        if (std::fabs(cross) > CollisionEpsilon)
        {
            return false;
        }

        const float minX = std::min(start.x, end.x) - CollisionEpsilon;
        const float maxX = std::max(start.x, end.x) + CollisionEpsilon;
        const float minY = std::min(start.y, end.y) - CollisionEpsilon;
        const float maxY = std::max(start.y, end.y) + CollisionEpsilon;
        return point.x >= minX && point.x <= maxX && point.y >= minY && point.y <= maxY;
    };

    bool inside = false;

    for (size_t index = 0; index < vertices.size(); ++index)
    {
        const IndoorProjectedFacePoint &current = vertices[index];
        const IndoorProjectedFacePoint &next = vertices[(index + 1) % vertices.size()];

        if (pointOnSegment(current, next))
        {
            return true;
        }

        if ((current.y > point.y) == (next.y > point.y))
        {
            continue;
        }

        const float intersectionX =
            (next.x - current.x) * (point.y - current.y) / (next.y - current.y) + current.x;

        if (point.x < intersectionX)
        {
            inside = !inside;
        }
    }

    return inside;
}

bool maskAllowsFace(const std::vector<uint8_t> *pMask, size_t faceIndex, bool emptyMaskAllowsAll)
{
    if (pMask == nullptr)
    {
        return true;
    }

    if (pMask->empty())
    {
        return emptyMaskAllowsAll;
    }

    return faceIndex < pMask->size() && (*pMask)[faceIndex] != 0;
}

bool sweptSphereBoundsTouchFace(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorFaceGeometryData &geometry
)
{
    const bx::Vec3 endCenter = vecAdd(sphere.center, vecScale(direction, moveDistance));
    const float minX = std::min(sphere.center.x, endCenter.x) - sphere.radius;
    const float maxX = std::max(sphere.center.x, endCenter.x) + sphere.radius;
    const float minY = std::min(sphere.center.y, endCenter.y) - sphere.radius;
    const float maxY = std::max(sphere.center.y, endCenter.y) + sphere.radius;
    const float minZ = std::min(sphere.center.z, endCenter.z) - sphere.radius;
    const float maxZ = std::max(sphere.center.z, endCenter.z) + sphere.radius;

    return maxX >= geometry.minX
        && minX <= geometry.maxX
        && maxY >= geometry.minY
        && minY <= geometry.maxY
        && maxZ >= geometry.minZ
        && minZ <= geometry.maxZ;
}

IndoorSweptBodyBounds boundsForSphereSweep(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance
)
{
    const bx::Vec3 endCenter = vecAdd(sphere.center, vecScale(direction, moveDistance));

    IndoorSweptBodyBounds bounds = {};
    bounds.minX = std::min(sphere.center.x, endCenter.x) - sphere.radius;
    bounds.maxX = std::max(sphere.center.x, endCenter.x) + sphere.radius;
    bounds.minY = std::min(sphere.center.y, endCenter.y) - sphere.radius;
    bounds.maxY = std::max(sphere.center.y, endCenter.y) + sphere.radius;
    bounds.minZ = std::min(sphere.center.z, endCenter.z) - sphere.radius;
    bounds.maxZ = std::max(sphere.center.z, endCenter.z) + sphere.radius;
    return bounds;
}

void mergeBounds(IndoorSweptBodyBounds &bounds, const IndoorSweptBodyBounds &other)
{
    bounds.minX = std::min(bounds.minX, other.minX);
    bounds.maxX = std::max(bounds.maxX, other.maxX);
    bounds.minY = std::min(bounds.minY, other.minY);
    bounds.maxY = std::max(bounds.maxY, other.maxY);
    bounds.minZ = std::min(bounds.minZ, other.minZ);
    bounds.maxZ = std::max(bounds.maxZ, other.maxZ);
}

float closestPlaneDistanceAlongSegment(float startDistance, float endDistance)
{
    if ((startDistance <= 0.0f && endDistance >= 0.0f) || (startDistance >= 0.0f && endDistance <= 0.0f))
    {
        return 0.0f;
    }

    return std::min(std::fabs(startDistance), std::fabs(endDistance));
}

bool sweptSphereTouchesPlane(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorFaceGeometryData &geometry,
    float planeSlack
)
{
    if (geometry.vertices.empty())
    {
        return false;
    }

    const bx::Vec3 normal = vecNormalize(geometry.normal);

    if (vecLength(normal) <= CollisionEpsilon)
    {
        return false;
    }

    const bx::Vec3 endCenter = vecAdd(sphere.center, vecScale(direction, moveDistance));
    const float startDistance = vecDot(vecSubtract(sphere.center, geometry.vertices.front()), normal);
    const float endDistance = vecDot(vecSubtract(endCenter, geometry.vertices.front()), normal);
    const float closestDistance = closestPlaneDistanceAlongSegment(startDistance, endDistance);
    return closestDistance <= sphere.radius + std::max(0.0f, planeSlack);
}

IndoorSweptSphere buildMidSphere(const IndoorSweptBody &body)
{
    IndoorSweptSphere sphere = {};
    sphere.center = {
        (body.lowSphere.center.x + body.highSphere.center.x) * 0.5f,
        (body.lowSphere.center.y + body.highSphere.center.y) * 0.5f,
        (body.lowSphere.center.z + body.highSphere.center.z) * 0.5f
    };
    sphere.radius = body.highSphere.radius;
    sphere.heightOffset = (body.lowSphere.heightOffset + body.highSphere.heightOffset) * 0.5f;
    return sphere;
}

std::optional<IndoorSweptSphere> buildFaceCenterHeightSphere(
    const IndoorSweptBody &body,
    const IndoorFaceGeometryData &geometry
)
{
    const float faceCenterZ = (geometry.minZ + geometry.maxZ) * 0.5f;
    const IndoorSweptSphere midSphere = buildMidSphere(body);

    if (faceCenterZ <= body.lowSphere.center.z
        || faceCenterZ >= body.highSphere.center.z
        || std::fabs(midSphere.center.z - faceCenterZ) <= 10.0f)
    {
        return std::nullopt;
    }

    IndoorSweptSphere sphere = body.lowSphere;
    sphere.center.z = faceCenterZ;
    sphere.radius = body.highSphere.radius;
    sphere.heightOffset = body.lowSphere.heightOffset + faceCenterZ - body.lowSphere.center.z;
    return sphere;
}

bool sweptSphereVerticallyOverlapsCylinder(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorSweptCylinder &cylinder
)
{
    const float sphereCenterZ = sphere.center.z + direction.z * moveDistance;
    return sphereCenterZ + sphere.radius >= cylinder.baseCenter.z
        && sphereCenterZ - sphere.radius <= cylinder.baseCenter.z + cylinder.height;
}

void keepNearestHit(std::optional<IndoorSweptFaceHit> &bestHit, const std::optional<IndoorSweptFaceHit> &candidate)
{
    if (!candidate)
    {
        return;
    }

    if (!bestHit || candidate->adjustedMoveDistance < bestHit->adjustedMoveDistance)
    {
        bestHit = candidate;
    }
}

void keepNearestCylinderHit(
    std::optional<IndoorSweptCylinderHit> &bestHit,
    const std::optional<IndoorSweptCylinderHit> &candidate)
{
    if (!candidate)
    {
        return;
    }

    if (!bestHit || candidate->adjustedMoveDistance < bestHit->adjustedMoveDistance)
    {
        bestHit = candidate;
    }
}

float adjustedSweepMoveDistance(float hitDistance, float backoffDistance)
{
    const float effectiveBackoff = std::max(0.0f, backoffDistance);

    if (hitDistance <= effectiveBackoff)
    {
        return std::max(0.0f, hitDistance);
    }

    return hitDistance - effectiveBackoff;
}

bool solveNearestSweepDistance(
    float a,
    float b,
    float c,
    float maxDistance,
    float &distance
)
{
    if (std::fabs(a) <= CollisionEpsilon)
    {
        return false;
    }

    const float discriminant = b * b - 4.0f * a * c;

    if (discriminant < 0.0f)
    {
        return false;
    }

    float rootA = (-b - std::sqrt(discriminant)) / (2.0f * a);
    float rootB = (-b + std::sqrt(discriminant)) / (2.0f * a);

    if (rootA > rootB)
    {
        std::swap(rootA, rootB);
    }

    if (rootA > CollisionEpsilon && rootA <= maxDistance + CollisionEpsilon)
    {
        distance = std::clamp(rootA, 0.0f, maxDistance);
        return true;
    }

    if (rootB > CollisionEpsilon && rootB <= maxDistance + CollisionEpsilon)
    {
        distance = std::clamp(rootB, 0.0f, maxDistance);
        return true;
    }

    return false;
}

std::optional<IndoorSweptFaceHit> sweepIndoorSphereAgainstPoint(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const bx::Vec3 &point,
    size_t faceIndex,
    float backoffDistance
)
{
    const bx::Vec3 normalizedDirection = vecNormalize(direction);
    const bx::Vec3 delta = vecSubtract(sphere.center, point);
    const float a = vecDot(normalizedDirection, normalizedDirection);
    const float b = 2.0f * vecDot(delta, normalizedDirection);
    const float c = vecDot(delta, delta) - sphere.radius * sphere.radius;
    float hitDistance = 0.0f;

    if (!solveNearestSweepDistance(a, b, c, moveDistance, hitDistance))
    {
        return std::nullopt;
    }

    const bx::Vec3 sphereCenterAtHit = vecAdd(sphere.center, vecScale(normalizedDirection, hitDistance));
    bx::Vec3 collisionNormal = vecNormalize(vecSubtract(sphereCenterAtHit, point));

    if (vecLength(collisionNormal) <= CollisionEpsilon)
    {
        collisionNormal = vecScale(normalizedDirection, -1.0f);
    }

    IndoorSweptFaceHit hit = {};
    hit.hit = true;
    hit.boundaryHit = true;
    hit.faceIndex = faceIndex;
    hit.point = point;
    hit.normal = collisionNormal;
    hit.moveDistance = hitDistance;
    hit.adjustedMoveDistance = adjustedSweepMoveDistance(hitDistance, backoffDistance);
    hit.heightOffset = sphere.heightOffset;
    return hit;
}

std::optional<IndoorSweptFaceHit> sweepIndoorSphereAgainstSegment(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const bx::Vec3 &start,
    const bx::Vec3 &end,
    size_t faceIndex,
    float backoffDistance
)
{
    const bx::Vec3 edge = vecSubtract(end, start);
    const float edgeLength = vecLength(edge);

    if (edgeLength <= CollisionEpsilon)
    {
        return sweepIndoorSphereAgainstPoint(sphere, direction, moveDistance, start, faceIndex, backoffDistance);
    }

    const bx::Vec3 edgeDirection = vecScale(edge, 1.0f / edgeLength);
    const bx::Vec3 normalizedDirection = vecNormalize(direction);
    const float directionAlongEdge = vecDot(normalizedDirection, edgeDirection);
    const bx::Vec3 perpendicularDirection =
        vecSubtract(normalizedDirection, vecScale(edgeDirection, directionAlongEdge));
    const bx::Vec3 startDelta = vecSubtract(sphere.center, start);
    const float startAlongEdge = vecDot(startDelta, edgeDirection);
    const bx::Vec3 perpendicularStartDelta =
        vecSubtract(startDelta, vecScale(edgeDirection, startAlongEdge));
    const float a = vecDot(perpendicularDirection, perpendicularDirection);
    const float b = 2.0f * vecDot(perpendicularStartDelta, perpendicularDirection);
    const float c = vecDot(perpendicularStartDelta, perpendicularStartDelta) - sphere.radius * sphere.radius;
    float hitDistance = 0.0f;

    if (!solveNearestSweepDistance(a, b, c, moveDistance, hitDistance))
    {
        return std::nullopt;
    }

    const bx::Vec3 sphereCenterAtHit = vecAdd(sphere.center, vecScale(normalizedDirection, hitDistance));
    const float hitAlongEdge = vecDot(vecSubtract(sphereCenterAtHit, start), edgeDirection);

    if (hitAlongEdge < -CollisionEpsilon || hitAlongEdge > edgeLength + CollisionEpsilon)
    {
        return std::nullopt;
    }

    const float clampedHitAlongEdge = std::clamp(hitAlongEdge, 0.0f, edgeLength);
    const bx::Vec3 contactPoint = vecAdd(start, vecScale(edgeDirection, clampedHitAlongEdge));
    bx::Vec3 collisionNormal = vecNormalize(vecSubtract(sphereCenterAtHit, contactPoint));

    if (vecLength(collisionNormal) <= CollisionEpsilon)
    {
        collisionNormal = vecScale(normalizedDirection, -1.0f);
    }

    IndoorSweptFaceHit hit = {};
    hit.hit = true;
    hit.boundaryHit = true;
    hit.faceIndex = faceIndex;
    hit.point = contactPoint;
    hit.normal = collisionNormal;
    hit.moveDistance = hitDistance;
    hit.adjustedMoveDistance = adjustedSweepMoveDistance(hitDistance, backoffDistance);
    hit.heightOffset = sphere.heightOffset;
    return hit;
}

std::optional<IndoorSweptFaceHit> sweepIndoorSphereAgainstFaceBoundary(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorFaceGeometryData &geometry,
    const IndoorFaceSweepOptions &options
)
{
    std::optional<IndoorSweptFaceHit> bestHit;

    for (size_t index = 0; index < geometry.vertices.size(); ++index)
    {
        const bx::Vec3 &vertex = geometry.vertices[index];
        const bx::Vec3 &nextVertex = geometry.vertices[(index + 1) % geometry.vertices.size()];

        keepNearestHit(
            bestHit,
            sweepIndoorSphereAgainstPoint(
                sphere,
                direction,
                moveDistance,
                vertex,
                geometry.faceIndex,
                options.backoffDistance));
        keepNearestHit(
            bestHit,
            sweepIndoorSphereAgainstSegment(
                sphere,
                direction,
                moveDistance,
                vertex,
                nextVertex,
                geometry.faceIndex,
                options.backoffDistance));
    }

    return bestHit;
}
}

IndoorSweptBodyBounds buildIndoorSweptBodyBounds(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance
)
{
    const bx::Vec3 normalizedDirection = vecNormalize(direction);
    IndoorSweptBodyBounds bounds = boundsForSphereSweep(body.lowSphere, normalizedDirection, moveDistance);
    mergeBounds(bounds, boundsForSphereSweep(body.highSphere, normalizedDirection, moveDistance));
    return bounds;
}

bool indoorSweptBodyBoundsTouchFace(
    const IndoorSweptBodyBounds &bounds,
    const IndoorFaceGeometryData &geometry,
    float padding
)
{
    const float effectivePadding = std::max(0.0f, padding);
    return bounds.maxX + effectivePadding >= geometry.minX
        && bounds.minX - effectivePadding <= geometry.maxX
        && bounds.maxY + effectivePadding >= geometry.minY
        && bounds.minY - effectivePadding <= geometry.maxY
        && bounds.maxZ + effectivePadding >= geometry.minZ
        && bounds.minZ - effectivePadding <= geometry.maxZ;
}

bool indoorSweptBodyTouchesPortalFace(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorFaceGeometryData &geometry,
    float planeSlack
)
{
    if (!geometry.isPortal || !geometry.hasPlane)
    {
        return false;
    }

    const bx::Vec3 normalizedDirection = vecNormalize(direction);
    const IndoorSweptBodyBounds bounds = buildIndoorSweptBodyBounds(body, normalizedDirection, moveDistance);

    if (!indoorSweptBodyBoundsTouchFace(bounds, geometry))
    {
        return false;
    }

    return sweptSphereTouchesPlane(body.lowSphere, normalizedDirection, moveDistance, geometry, planeSlack)
        || sweptSphereTouchesPlane(body.highSphere, normalizedDirection, moveDistance, geometry, planeSlack);
}

bool canSweepAgainstIndoorFace(
    const IndoorFaceGeometryData &geometry,
    const IndoorFaceSweepOptions &options
)
{
    if (!geometry.hasPlane
        || geometry.vertices.size() < 3
        || hasFaceAttribute(geometry.attributes, FaceAttribute::Invisible)
        || hasFaceAttribute(geometry.attributes, FaceAttribute::Untouchable)
        || (geometry.isPortal && !options.includePortalFaces))
    {
        return false;
    }

    if (!maskAllowsFace(options.pCollisionFaceMask, geometry.faceIndex, true))
    {
        return false;
    }

    return maskAllowsFace(options.pMechanismBlockingFaceMask, geometry.faceIndex, true);
}

std::optional<IndoorSweptFaceHit> sweepIndoorSphereAgainstFace(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorFaceGeometryData &geometry,
    const IndoorFaceSweepOptions &options
)
{
    if (sphere.radius <= 0.0f || moveDistance <= CollisionEpsilon || !canSweepAgainstIndoorFace(geometry, options))
    {
        return std::nullopt;
    }

    const bx::Vec3 normalizedDirection = vecNormalize(direction);

    if (vecLength(normalizedDirection) <= CollisionEpsilon
        || !sweptSphereBoundsTouchFace(sphere, normalizedDirection, moveDistance, geometry))
    {
        return std::nullopt;
    }

    std::optional<IndoorSweptFaceHit> bestHit;
    bx::Vec3 collisionNormal = vecNormalize(geometry.normal);

    if (vecLength(collisionNormal) > CollisionEpsilon)
    {
        const float rawStartDistance = vecDot(vecSubtract(sphere.center, geometry.vertices.front()), collisionNormal);
        const float rawEndDistance = rawStartDistance + vecDot(normalizedDirection, collisionNormal) * moveDistance;
        const float rawStartAbsDistance = std::fabs(rawStartDistance);
        const float rawEndAbsDistance = std::fabs(rawEndDistance);
        const bool startsInsideFaceRadius = rawStartAbsDistance <= sphere.radius + CollisionEpsilon;
        const bool staysOnSameSide =
            rawStartDistance == 0.0f
            || rawEndDistance == 0.0f
            || (rawStartDistance > 0.0f) == (rawEndDistance > 0.0f);

        if (startsInsideFaceRadius && staysOnSameSide && rawEndAbsDistance >= rawStartAbsDistance - CollisionEpsilon)
        {
            return std::nullopt;
        }
    }

    float directionDotNormal = vecDot(normalizedDirection, collisionNormal);

    if (directionDotNormal > 0.0f)
    {
        collisionNormal = vecScale(collisionNormal, -1.0f);
        directionDotNormal = -directionDotNormal;
    }

    if (directionDotNormal >= -CollisionEpsilon)
    {
        return sweepIndoorSphereAgainstFaceBoundary(sphere, normalizedDirection, moveDistance, geometry, options);
    }

    const float startDistance = vecDot(vecSubtract(sphere.center, geometry.vertices.front()), collisionNormal);
    const float endDistance = startDistance + directionDotNormal * moveDistance;

    if (startDistance < -sphere.radius || (startDistance > sphere.radius && endDistance > sphere.radius))
    {
        return sweepIndoorSphereAgainstFaceBoundary(sphere, normalizedDirection, moveDistance, geometry, options);
    }

    float hitDistance = 0.0f;

    if (startDistance > sphere.radius)
    {
        hitDistance = (sphere.radius - startDistance) / directionDotNormal;
    }

    if (hitDistance < -CollisionEpsilon || hitDistance > moveDistance + CollisionEpsilon)
    {
        return sweepIndoorSphereAgainstFaceBoundary(sphere, normalizedDirection, moveDistance, geometry, options);
    }

    hitDistance = std::clamp(hitDistance, 0.0f, moveDistance);

    const bx::Vec3 sphereCenterAtHit = vecAdd(sphere.center, vecScale(normalizedDirection, hitDistance));
    const bx::Vec3 contactPoint = vecSubtract(sphereCenterAtHit, vecScale(collisionNormal, sphere.radius));
    const IndoorProjectedFacePoint projectedContactPoint =
        projectFacePoint(geometry.projectionAxis, contactPoint);

    if (isPointInsideProjectedPolygon(projectedContactPoint, geometry.projectedVertices))
    {
        IndoorSweptFaceHit hit = {};
        hit.hit = true;
        hit.faceIndex = geometry.faceIndex;
        hit.point = contactPoint;
        hit.normal = collisionNormal;
        hit.moveDistance = hitDistance;
        hit.adjustedMoveDistance = adjustedSweepMoveDistance(hitDistance, options.backoffDistance);
        hit.heightOffset = sphere.heightOffset;
        bestHit = hit;
    }

    keepNearestHit(
        bestHit,
        sweepIndoorSphereAgainstFaceBoundary(sphere, normalizedDirection, moveDistance, geometry, options));
    return bestHit;
}

std::optional<IndoorSweptFaceHit> sweepIndoorBodyAgainstFace(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorFaceGeometryData &geometry,
    const IndoorFaceSweepOptions &options
)
{
    std::optional<IndoorSweptFaceHit> bestHit;

    keepNearestHit(bestHit, sweepIndoorSphereAgainstFace(body.lowSphere, direction, moveDistance, geometry, options));
    keepNearestHit(bestHit, sweepIndoorSphereAgainstFace(body.highSphere, direction, moveDistance, geometry, options));
    keepNearestHit(
        bestHit,
        sweepIndoorSphereAgainstFace(buildMidSphere(body), direction, moveDistance, geometry, options));

    const std::optional<IndoorSweptSphere> faceCenterSphere = buildFaceCenterHeightSphere(body, geometry);

    if (faceCenterSphere)
    {
        keepNearestHit(
            bestHit,
            sweepIndoorSphereAgainstFace(*faceCenterSphere, direction, moveDistance, geometry, options));
    }

    return bestHit;
}

std::optional<IndoorSweptFaceHit> selectNearestIndoorFaceHit(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance,
    const std::vector<const IndoorFaceGeometryData *> &faces,
    const IndoorFaceSweepOptions &options
)
{
    std::optional<IndoorSweptFaceHit> bestHit;

    for (const IndoorFaceGeometryData *pFace : faces)
    {
        if (pFace == nullptr)
        {
            continue;
        }

        keepNearestHit(bestHit, sweepIndoorBodyAgainstFace(body, direction, moveDistance, *pFace, options));
    }

    return bestHit;
}

std::optional<IndoorSweptCylinderHit> sweepIndoorSphereAgainstCylinder(
    const IndoorSweptSphere &sphere,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorSweptCylinder &cylinder,
    float backoffDistance
)
{
    if (sphere.radius <= 0.0f
        || cylinder.radius <= 0.0f
        || cylinder.height <= 0.0f
        || moveDistance <= CollisionEpsilon)
    {
        return std::nullopt;
    }

    const bx::Vec3 normalizedDirection = vecNormalize(direction);
    const float horizontalA =
        normalizedDirection.x * normalizedDirection.x + normalizedDirection.y * normalizedDirection.y;

    if (horizontalA <= CollisionEpsilon)
    {
        return std::nullopt;
    }

    const float combinedRadius = sphere.radius + cylinder.radius;
    const float startDeltaX = sphere.center.x - cylinder.baseCenter.x;
    const float startDeltaY = sphere.center.y - cylinder.baseCenter.y;
    const float horizontalB =
        2.0f * (startDeltaX * normalizedDirection.x + startDeltaY * normalizedDirection.y);
    const float horizontalC = startDeltaX * startDeltaX + startDeltaY * startDeltaY
        - combinedRadius * combinedRadius;
    float hitDistance = 0.0f;

    if (horizontalC <= 0.0f)
    {
        if (horizontalB >= 0.0f)
        {
            return std::nullopt;
        }
    }
    else
    {
        const float discriminant = horizontalB * horizontalB - 4.0f * horizontalA * horizontalC;

        if (discriminant < 0.0f)
        {
            return std::nullopt;
        }

        hitDistance = (-horizontalB - std::sqrt(discriminant)) / (2.0f * horizontalA);

        if (hitDistance < -CollisionEpsilon || hitDistance > moveDistance + CollisionEpsilon)
        {
            return std::nullopt;
        }

        hitDistance = std::clamp(hitDistance, 0.0f, moveDistance);
    }

    if (!sweptSphereVerticallyOverlapsCylinder(sphere, normalizedDirection, hitDistance, cylinder))
    {
        return std::nullopt;
    }

    const bx::Vec3 sphereCenterAtHit = vecAdd(sphere.center, vecScale(normalizedDirection, hitDistance));
    bx::Vec3 collisionNormal = vecNormalize(
        {
            sphereCenterAtHit.x - cylinder.baseCenter.x,
            sphereCenterAtHit.y - cylinder.baseCenter.y,
            0.0f
        });

    if (vecLength(collisionNormal) <= CollisionEpsilon)
    {
        collisionNormal = vecNormalize({-normalizedDirection.x, -normalizedDirection.y, 0.0f});
    }

    IndoorSweptCylinderHit hit = {};
    hit.hit = true;
    hit.point = {
        cylinder.baseCenter.x + collisionNormal.x * cylinder.radius,
        cylinder.baseCenter.y + collisionNormal.y * cylinder.radius,
        sphereCenterAtHit.z
    };
    hit.normal = collisionNormal;
    hit.moveDistance = hitDistance;
    hit.adjustedMoveDistance = adjustedSweepMoveDistance(hitDistance, backoffDistance);
    hit.heightOffset = sphere.heightOffset;
    return hit;
}

std::optional<IndoorSweptCylinderHit> sweepIndoorBodyAgainstCylinder(
    const IndoorSweptBody &body,
    const bx::Vec3 &direction,
    float moveDistance,
    const IndoorSweptCylinder &cylinder,
    float backoffDistance
)
{
    std::optional<IndoorSweptCylinderHit> bestHit;

    keepNearestCylinderHit(
        bestHit,
        sweepIndoorSphereAgainstCylinder(body.lowSphere, direction, moveDistance, cylinder, backoffDistance));
    keepNearestCylinderHit(
        bestHit,
        sweepIndoorSphereAgainstCylinder(body.highSphere, direction, moveDistance, cylinder, backoffDistance));
    keepNearestCylinderHit(
        bestHit,
        sweepIndoorSphereAgainstCylinder(buildMidSphere(body), direction, moveDistance, cylinder, backoffDistance));
    return bestHit;
}

bx::Vec3 projectIndoorVelocityAlongPlane(
    const bx::Vec3 &velocity,
    const bx::Vec3 &normal,
    float damping
)
{
    const bx::Vec3 normalizedNormal = vecNormalize(normal);

    if (vecLength(normalizedNormal) <= CollisionEpsilon)
    {
        return velocity;
    }

    const float velocityIntoNormal = vecDot(velocity, normalizedNormal);
    const bx::Vec3 projected = vecSubtract(velocity, vecScale(normalizedNormal, velocityIntoNormal));
    const float clampedDamping = std::max(0.0f, damping);
    return vecScale(projected, clampedDamping);
}

}
