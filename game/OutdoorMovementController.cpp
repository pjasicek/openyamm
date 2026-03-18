#include "game/OutdoorMovementController.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr float CollisionEpsilon = 0.01f;
constexpr float CollisionMinMoveDistance = 0.5f;
constexpr float AllowedCollisionOvershoot = -100.0f;
constexpr float ClosestDistance = 0.5f;
constexpr float FloorSelectionHeightTolerance = 5.0f;
constexpr float FloorCheckSlack = 5.0f;
constexpr float WalkableNormalZ = 0.70767211914f;
constexpr float PartyRadius = 37.0f;
constexpr float PartyHeight = 192.0f;
constexpr float MaxSmallSlopeHeight = 128.0f;
constexpr float GroundSnapHeight = 1.0f;
constexpr float CloseToGroundHeight = 32.0f;
// OE outdoor party gravity is -2 * dtTicks * Gravity, with default Gravity = 5 and dt at 128 Hz.
constexpr float GravityPerSecond = 1280.0f;
constexpr uint8_t PolygonFloor = 0x3;
constexpr uint8_t PolygonInBetweenFloorAndWall = 0x4;
constexpr uint32_t FaceAttributeFluid = 0x00000010u;

struct FloorSample
{
    bool hasFloor = false;
    float height = 0.0f;
    float normalZ = 1.0f;
    bool fromBModel = false;
    bool isFluid = false;
    bool isBurning = false;
    size_t bModelIndex = 0;
    size_t faceIndex = 0;
};

struct CollisionHit
{
    enum class Kind
    {
        Face,
        Decoration,
        Actor,
        SpriteObject,
    };

    Kind kind = Kind::Face;
    size_t bModelIndex = 0;
    size_t faceIndex = 0;
    size_t colliderIndex = 0;
    uint8_t polygonType = 0;
    float floorHeight = 0.0f;
    float moveDistance = 0.0f;
    float heightOffset = 0.0f;
    bx::Vec3 collisionPoint = {0.0f, 0.0f, 0.0f};
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
    float minZ = 0.0f;
    float maxZ = 0.0f;
};

struct CollisionState
{
    bool checkHi = true;
    float radiusLo = PartyRadius;
    float radiusHi = PartyRadius;
    bx::Vec3 positionLo = {0.0f, 0.0f, 0.0f};
    bx::Vec3 positionHi = {0.0f, 0.0f, 0.0f};
    bx::Vec3 newPositionLo = {0.0f, 0.0f, 0.0f};
    bx::Vec3 newPositionHi = {0.0f, 0.0f, 0.0f};
    bx::Vec3 velocity = {0.0f, 0.0f, 0.0f};
    bx::Vec3 direction = {0.0f, 0.0f, 0.0f};
    bx::Vec3 collisionPoint = {0.0f, 0.0f, 0.0f};
    float speed = 0.0f;
    float totalMoveDistance = 0.0f;
    float moveDistance = 0.0f;
    float adjustedMoveDistance = 0.0f;
    float heightOffset = 0.0f;
    float bboxMinX = 0.0f;
    float bboxMinY = 0.0f;
    float bboxMinZ = 0.0f;
    float bboxMaxX = 0.0f;
    float bboxMaxY = 0.0f;
    float bboxMaxZ = 0.0f;
    std::optional<CollisionHit> hit;
};

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

float vecDot(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

bx::Vec3 vecCross(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
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

bool bboxIntersects(
    float minAx,
    float minAy,
    float minAz,
    float maxAx,
    float maxAy,
    float maxAz,
    float minBx,
    float minBy,
    float minBz,
    float maxBx,
    float maxBy,
    float maxBz
)
{
    return !(maxAx < minBx
        || minAx > maxBx
        || maxAy < minBy
        || minAy > maxBy
        || maxAz < minBz
        || minAz > maxBz);
}

bool terrainSlopeTooHigh(const OutdoorMapData &outdoorMapData, float x, float y)
{
    const float gridXFloat = 64.0f - (x / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const float gridYFloat = 64.0f - (y / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const int gridX = std::clamp(static_cast<int>(std::floor(gridXFloat)), 0, OutdoorMapData::TerrainWidth - 2);
    const int gridY = std::clamp(static_cast<int>(std::floor(gridYFloat)), 0, OutdoorMapData::TerrainHeight - 2);
    const size_t index00 = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
    const size_t index01 = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
    const size_t index10 = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + (gridX + 1));
    const size_t index11 = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + (gridX + 1));
    const int z00 = static_cast<int>(outdoorMapData.heightMap[index00]) * OutdoorMapData::TerrainHeightScale;
    const int z01 = static_cast<int>(outdoorMapData.heightMap[index01]) * OutdoorMapData::TerrainHeightScale;
    const int z10 = static_cast<int>(outdoorMapData.heightMap[index10]) * OutdoorMapData::TerrainHeightScale;
    const int z11 = static_cast<int>(outdoorMapData.heightMap[index11]) * OutdoorMapData::TerrainHeightScale;

    const float tileMinWorldX =
        static_cast<float>((64 - gridX - 1) * OutdoorMapData::TerrainTileSize);
    const float tileTopWorldY =
        static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
    const int dx = static_cast<int>(std::clamp(x - tileMinWorldX, 0.0f, 511.999f));
    const int dy = static_cast<int>(std::clamp(tileTopWorldY - y, 0.0f, 511.999f));
    int triangleZ1 = 0;
    int triangleZ2 = 0;
    int triangleZ3 = 0;

    if (dy >= dx)
    {
        triangleZ1 = z01;
        triangleZ2 = z11;
        triangleZ3 = z00;
    }
    else
    {
        triangleZ1 = z10;
        triangleZ2 = z00;
        triangleZ3 = z11;
    }

    const int minZ = std::min({triangleZ1, triangleZ2, triangleZ3});
    const int maxZ = std::max({triangleZ1, triangleZ2, triangleZ3});
    return (maxZ - minZ) > OutdoorMapData::TerrainTileSize;
}

bool isOutdoorLandMaskWater(const std::optional<std::vector<uint8_t>> &outdoorLandMask, float x, float y)
{
    if (!outdoorLandMask || outdoorLandMask->empty())
    {
        return false;
    }

    const float gridX = 64.0f - (x / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const float gridY = 64.0f - (y / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const int tileX = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int tileY = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    const int landMaskWidth = OutdoorMapData::TerrainWidth - 1;
    const size_t tileIndex = static_cast<size_t>(tileY * landMaskWidth + tileX);

    if (tileIndex >= outdoorLandMask->size())
    {
        return false;
    }

    return (*outdoorLandMask)[tileIndex] == 0;
}

float pointSegmentDistanceSquared2d(
    float pointX,
    float pointY,
    float segmentStartX,
    float segmentStartY,
    float segmentEndX,
    float segmentEndY
)
{
    const float segmentX = segmentEndX - segmentStartX;
    const float segmentY = segmentEndY - segmentStartY;
    const float segmentLengthSquared = segmentX * segmentX + segmentY * segmentY;

    if (segmentLengthSquared <= CollisionEpsilon)
    {
        const float dx = pointX - segmentStartX;
        const float dy = pointY - segmentStartY;
        return dx * dx + dy * dy;
    }

    const float projection =
        ((pointX - segmentStartX) * segmentX + (pointY - segmentStartY) * segmentY) / segmentLengthSquared;
    const float clampedProjection = std::clamp(projection, 0.0f, 1.0f);
    const float closestX = segmentStartX + segmentX * clampedProjection;
    const float closestY = segmentStartY + segmentY * clampedProjection;
    const float dx = pointX - closestX;
    const float dy = pointY - closestY;
    return dx * dx + dy * dy;
}

bool isPointInsideOrNearPolygon(float x, float y, const std::vector<bx::Vec3> &vertices, float slack)
{
    if (isPointInsideOutdoorPolygon(x, y, vertices))
    {
        return true;
    }

    const float slackSquared = slack * slack;

    for (size_t index = 0; index < vertices.size(); ++index)
    {
        const size_t nextIndex = (index + 1) % vertices.size();
        const float distanceSquared = pointSegmentDistanceSquared2d(
            x,
            y,
            vertices[index].x,
            vertices[index].y,
            vertices[nextIndex].x,
            vertices[nextIndex].y
        );

        if (distanceSquared <= slackSquared)
        {
            return true;
        }
    }

    return false;
}

bool calculateFaceHeight(const OutdoorFaceGeometryData &geometry, float x, float y, float &height)
{
    if (geometry.polygonType == PolygonFloor)
    {
        height = geometry.vertices[0].z;
        return true;
    }

    if (!geometry.hasPlane || std::fabs(geometry.normal.z) <= CollisionEpsilon)
    {
        return false;
    }

    height =
        geometry.vertices[0].z
        - (geometry.normal.x * (x - geometry.vertices[0].x) + geometry.normal.y * (y - geometry.vertices[0].y))
            / geometry.normal.z;
    return true;
}

bool hasShorterSolution(float a, float b, float c, float currentSolution, float &newSolution)
{
    const float discriminant = b * b - 4.0f * a * c;

    if (discriminant < 0.0f)
    {
        return false;
    }

    const float root = std::sqrt(discriminant);
    float alpha1 = (-b - root) / (2.0f * a);
    float alpha2 = (-b + root) / (2.0f * a);

    if (alpha1 > alpha2)
    {
        std::swap(alpha1, alpha2);
    }

    if (alpha1 > 0.0f && alpha1 < currentSolution)
    {
        newSolution = alpha1;
        return true;
    }

    if (alpha2 > 0.0f && alpha2 < currentSolution)
    {
        newSolution = alpha2;
        return true;
    }

    return false;
}

bool collideWithLine(
    const bx::Vec3 &point1,
    const bx::Vec3 &point2,
    float radius,
    float currentMoveDistance,
    const CollisionState &collisionState,
    float &newMoveDistance,
    float &intersection
)
{
    const bx::Vec3 pos = collisionState.positionLo;
    const bx::Vec3 dir = collisionState.direction;
    const bx::Vec3 edge = vecSubtract(point2, point1);
    const bx::Vec3 sphereToVertex = vecSubtract(point1, pos);
    const float edgeLengthSquared = vecDot(edge, edge);
    const float edgeDotDir = vecDot(edge, dir);
    const float edgeDotSphereToVertex = vecDot(edge, sphereToVertex);
    const float sphereToVertexLengthSquared = vecDot(sphereToVertex, sphereToVertex);
    const float a = edgeLengthSquared * -vecDot(dir, dir) + edgeDotDir * edgeDotDir;
    const float b =
        edgeLengthSquared * (2.0f * vecDot(dir, sphereToVertex))
        - (2.0f * edgeDotDir * edgeDotSphereToVertex);
    const float c =
        edgeLengthSquared * (radius * radius - sphereToVertexLengthSquared)
        + (edgeDotSphereToVertex * edgeDotSphereToVertex);

    if (!hasShorterSolution(a, b, c, currentMoveDistance, newMoveDistance))
    {
        return false;
    }

    const float factor = (edgeDotDir * newMoveDistance - edgeDotSphereToVertex) / edgeLengthSquared;

    if (factor < 0.0f || factor > 1.0f)
    {
        return false;
    }

    intersection = factor;
    return true;
}

bool collideSphereWithFace(
    const OutdoorFaceGeometryData &geometry,
    const bx::Vec3 &position,
    float radius,
    const bx::Vec3 &direction,
    float currentMoveDistance,
    float &moveDistance,
    bx::Vec3 &collisionPoint
)
{
    if (geometry.vertices.size() < 3)
    {
        return false;
    }

    const float dirNormalProjection = vecDot(direction, geometry.normal);

    if (dirNormalProjection > 0.0f)
    {
        return false;
    }

    const float centerFaceDistance = vecDot(geometry.normal, vecSubtract(position, geometry.vertices[0]));
    float candidateMoveDistance = 0.0f;
    bx::Vec3 projectedPosition = position;
    bool sphereInPlane = false;

    if (std::fabs(dirNormalProjection) <= CollisionEpsilon)
    {
        if (std::fabs(centerFaceDistance) >= radius)
        {
            return false;
        }

        sphereInPlane = true;
    }
    else
    {
        candidateMoveDistance = (centerFaceDistance - radius) / -dirNormalProjection;

        if (candidateMoveDistance < -radius || candidateMoveDistance > currentMoveDistance)
        {
            return false;
        }

        projectedPosition = vecAdd(position, vecScale(direction, candidateMoveDistance));
        projectedPosition = vecSubtract(projectedPosition, vecScale(geometry.normal, radius));
    }

    if (!sphereInPlane && isPointInsideOutdoorPolygonProjected(projectedPosition, geometry.vertices, geometry.normal))
    {
        moveDistance = candidateMoveDistance;
        collisionPoint = projectedPosition;
        return true;
    }

    float bestDistance = currentMoveDistance;
    bx::Vec3 bestPoint = {0.0f, 0.0f, 0.0f};
    bool hasCollision = false;
    const float quadraticA = vecDot(direction, direction);

    for (size_t index = 0; index < geometry.vertices.size(); ++index)
    {
        const bx::Vec3 &vertex = geometry.vertices[index];
        const bx::Vec3 posToVertex = vecSubtract(position, vertex);
        const float quadraticB = 2.0f * vecDot(direction, posToVertex);
        const float quadraticC = vecDot(vecSubtract(vertex, position), vecSubtract(vertex, position)) - radius * radius;
        float newDistance = 0.0f;

        if (hasShorterSolution(quadraticA, quadraticB, quadraticC, bestDistance, newDistance))
        {
            bestDistance = newDistance;
            bestPoint = vertex;
            hasCollision = true;
        }
    }

    for (size_t index = 0; index < geometry.vertices.size(); ++index)
    {
        const size_t nextIndex = (index + 1) % geometry.vertices.size();
        float newDistance = 0.0f;
        float intersection = 0.0f;
        CollisionState tempState = {};
        tempState.positionLo = position;
        tempState.direction = direction;

        if (collideWithLine(
                geometry.vertices[index],
                geometry.vertices[nextIndex],
                radius,
                bestDistance,
                tempState,
                newDistance,
                intersection))
        {
            bestDistance = newDistance;
            bestPoint = vecAdd(
                geometry.vertices[index],
                vecScale(vecSubtract(geometry.vertices[nextIndex], geometry.vertices[index]), intersection));
            hasCollision = true;
        }
    }

    if (!hasCollision)
    {
        return false;
    }

    moveDistance = bestDistance;
    collisionPoint = bestPoint;
    return true;
}

bool collideSphereWithCylinder(
    const bx::Vec3 &centerLo,
    float cylinderRadius,
    float cylinderHeight,
    const bx::Vec3 &position,
    float sphereRadius,
    const bx::Vec3 &direction,
    float currentMoveDistance,
    float &moveDistance,
    bx::Vec3 &collisionPoint
)
{
    const float combinedRadius = cylinderRadius + sphereRadius;
    const float relativeX = position.x - centerLo.x;
    const float relativeY = position.y - centerLo.y;
    const float dirX = direction.x;
    const float dirY = direction.y;
    const float a = dirX * dirX + dirY * dirY;

    if (a <= CollisionEpsilon)
    {
        return false;
    }

    const float b = 2.0f * (relativeX * dirX + relativeY * dirY);
    const float c = relativeX * relativeX + relativeY * relativeY - combinedRadius * combinedRadius;
    float candidateMoveDistance = 0.0f;

    if (!hasShorterSolution(a, b, c, currentMoveDistance, candidateMoveDistance))
    {
        return false;
    }

    const float centerZ = position.z + direction.z * candidateMoveDistance;
    const float sphereMinZ = centerZ - sphereRadius;
    const float sphereMaxZ = centerZ + sphereRadius;
    const float cylinderMinZ = centerLo.z;
    const float cylinderMaxZ = centerLo.z + cylinderHeight;

    if (sphereMaxZ < cylinderMinZ || sphereMinZ > cylinderMaxZ)
    {
        return false;
    }

    const bx::Vec3 centerAtHit = vecAdd(position, vecScale(direction, candidateMoveDistance));
    bx::Vec3 outward = {
        centerAtHit.x - centerLo.x,
        centerAtHit.y - centerLo.y,
        0.0f
    };
    outward = vecNormalize(outward);

    if (vecLength(outward) <= CollisionEpsilon)
    {
        return false;
    }

    collisionPoint = {
        centerLo.x + outward.x * cylinderRadius,
        centerLo.y + outward.y * cylinderRadius,
        std::clamp(centerAtHit.z, cylinderMinZ, cylinderMaxZ)
    };
    moveDistance = candidateMoveDistance;
    return true;
}

bool rangesOverlap(float minA, float maxA, float minB, float maxB)
{
    return !(maxA < minB || minA > maxB);
}

void resolveActorCylinderOverlaps(bx::Vec3 &partyPosition, const std::vector<OutdoorActorCollision> &actorColliders)
{
    for (int iteration = 0; iteration < 4; ++iteration)
    {
        bool resolvedAny = false;

        for (const OutdoorActorCollision &collider : actorColliders)
        {
            const float actorRadius = static_cast<float>(collider.radius);
            const float combinedRadius = PartyRadius + actorRadius;
            const float deltaX = partyPosition.x - static_cast<float>(collider.worldX);
            const float deltaY = partyPosition.y - static_cast<float>(collider.worldY);
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY;

            if (distanceSquared >= combinedRadius * combinedRadius)
            {
                continue;
            }

            const float partyMinZ = partyPosition.z;
            const float partyMaxZ = partyPosition.z + PartyHeight;
            const float actorMinZ = static_cast<float>(collider.worldZ);
            const float actorMaxZ = actorMinZ + static_cast<float>(collider.height);

            if (!rangesOverlap(partyMinZ, partyMaxZ, actorMinZ, actorMaxZ))
            {
                continue;
            }

            float distance = std::sqrt(distanceSquared);
            float outwardX = 1.0f;
            float outwardY = 0.0f;

            if (distance > CollisionEpsilon)
            {
                outwardX = deltaX / distance;
                outwardY = deltaY / distance;
            }
            else
            {
                distance = 0.0f;
            }

            const float pushDistance = combinedRadius - distance + ClosestDistance;
            partyPosition.x += outwardX * pushDistance;
            partyPosition.y += outwardY * pushDistance;
            resolvedAny = true;
        }

        if (!resolvedAny)
        {
            break;
        }
    }
}

bool prepareCollisionState(CollisionState &collisionState, float deltaSeconds)
{
    collisionState.speed = vecLength(collisionState.velocity);

    if (collisionState.speed <= CollisionEpsilon)
    {
        return true;
    }

    collisionState.direction = vecScale(collisionState.velocity, 1.0f / collisionState.speed);
    collisionState.moveDistance = deltaSeconds * collisionState.speed - collisionState.totalMoveDistance;

    if (collisionState.moveDistance <= CollisionMinMoveDistance)
    {
        return true;
    }

    collisionState.newPositionLo = vecAdd(
        collisionState.positionLo,
        vecScale(collisionState.direction, collisionState.moveDistance));
    collisionState.newPositionHi = vecAdd(
        collisionState.positionHi,
        vecScale(collisionState.direction, collisionState.moveDistance));
    collisionState.adjustedMoveDistance = collisionState.moveDistance;
    collisionState.hit.reset();

    const auto updateBounds = [&collisionState](const bx::Vec3 &position, float radius)
    {
        collisionState.bboxMinX = std::min(collisionState.bboxMinX, position.x - radius);
        collisionState.bboxMinY = std::min(collisionState.bboxMinY, position.y - radius);
        collisionState.bboxMinZ = std::min(collisionState.bboxMinZ, position.z - radius);
        collisionState.bboxMaxX = std::max(collisionState.bboxMaxX, position.x + radius);
        collisionState.bboxMaxY = std::max(collisionState.bboxMaxY, position.y + radius);
        collisionState.bboxMaxZ = std::max(collisionState.bboxMaxZ, position.z + radius);
    };

    collisionState.bboxMinX = std::numeric_limits<float>::max();
    collisionState.bboxMinY = std::numeric_limits<float>::max();
    collisionState.bboxMinZ = std::numeric_limits<float>::max();
    collisionState.bboxMaxX = std::numeric_limits<float>::lowest();
    collisionState.bboxMaxY = std::numeric_limits<float>::lowest();
    collisionState.bboxMaxZ = std::numeric_limits<float>::lowest();
    updateBounds(collisionState.positionLo, collisionState.radiusLo);
    updateBounds(collisionState.newPositionLo, collisionState.radiusLo);
    updateBounds(collisionState.positionHi, collisionState.radiusHi);
    updateBounds(collisionState.newPositionHi, collisionState.radiusHi);

    return false;
}

void collideBodyWithFace(CollisionState &collisionState, const OutdoorFaceGeometryData &geometry)
{
    auto collideOnce = [&collisionState, &geometry](
                           const bx::Vec3 &oldPosition,
                           const bx::Vec3 &newPosition,
                           float radius,
                           float heightOffset)
    {
        const float distanceOld = vecDot(geometry.normal, vecSubtract(oldPosition, geometry.vertices[0]));
        const float distanceNew = vecDot(geometry.normal, vecSubtract(newPosition, geometry.vertices[0]));

        if (!(distanceOld > 0.0f
                && (distanceOld <= radius || distanceNew <= radius)
                && distanceNew <= distanceOld))
        {
            return;
        }

        float moveDistance = collisionState.adjustedMoveDistance;
        bx::Vec3 collisionPoint = {0.0f, 0.0f, 0.0f};

        if (!collideSphereWithFace(
                geometry,
                oldPosition,
                radius,
                collisionState.direction,
                collisionState.adjustedMoveDistance,
                moveDistance,
                collisionPoint))
        {
            return;
        }

        if (moveDistance <= AllowedCollisionOvershoot || moveDistance >= collisionState.adjustedMoveDistance)
        {
            return;
        }

        float floorHeight = geometry.minZ;
        calculateFaceHeight(geometry, collisionPoint.x, collisionPoint.y, floorHeight);

        collisionState.adjustedMoveDistance = moveDistance;
        collisionState.collisionPoint = collisionPoint;
        collisionState.heightOffset = heightOffset;
        collisionState.hit = CollisionHit{
            CollisionHit::Kind::Face,
            geometry.bModelIndex,
            geometry.faceIndex,
            0,
            geometry.polygonType,
            floorHeight,
            moveDistance,
            heightOffset,
            collisionPoint,
            geometry.normal,
            geometry.minZ,
            geometry.maxZ
        };
    };

    collideOnce(collisionState.positionLo, collisionState.newPositionLo, collisionState.radiusLo, 0.0f);

    if (!collisionState.checkHi)
    {
        return;
    }

    collideOnce(
        collisionState.positionHi,
        collisionState.newPositionHi,
        collisionState.radiusHi,
        collisionState.positionHi.z - collisionState.positionLo.z);

    bx::Vec3 midPosition = vecScale(vecAdd(collisionState.positionLo, collisionState.positionHi), 0.5f);
    bx::Vec3 newMidPosition = vecScale(vecAdd(collisionState.newPositionLo, collisionState.newPositionHi), 0.5f);
    collideOnce(midPosition, newMidPosition, collisionState.radiusHi, midPosition.z - collisionState.positionLo.z);

    const float faceCenterZ = (geometry.minZ + geometry.maxZ) * 0.5f;

    if (faceCenterZ > collisionState.positionLo.z
        && faceCenterZ < collisionState.positionHi.z
        && std::fabs(midPosition.z - faceCenterZ) > 10.0f)
    {
        const float heightOffset = faceCenterZ - collisionState.positionLo.z;
        midPosition.z = faceCenterZ;
        newMidPosition.z = collisionState.newPositionLo.z + heightOffset;
        collideOnce(midPosition, newMidPosition, collisionState.radiusHi, heightOffset);
    }
}

void collideOutdoorWithModels(
    CollisionState &collisionState,
    const std::vector<OutdoorFaceGeometryData> &faces)
{
    for (const OutdoorFaceGeometryData &geometry : faces)
    {
        if (!bboxIntersects(
                collisionState.bboxMinX,
                collisionState.bboxMinY,
                collisionState.bboxMinZ,
                collisionState.bboxMaxX,
                collisionState.bboxMaxY,
                collisionState.bboxMaxZ,
                geometry.minX,
                geometry.minY,
                geometry.minZ,
                geometry.maxX,
                geometry.maxY,
                geometry.maxZ))
        {
            continue;
        }

        collideBodyWithFace(collisionState, geometry);
    }
}

void collideOutdoorWithDecorations(
    CollisionState &collisionState,
    const std::vector<OutdoorDecorationCollision> &decorationColliders)
{
    auto collideOnce = [&collisionState, &decorationColliders](
                           const bx::Vec3 &position,
                           float radius,
                           float heightOffset)
    {
        for (size_t decorationIndex = 0; decorationIndex < decorationColliders.size(); ++decorationIndex)
        {
            const OutdoorDecorationCollision &collider = decorationColliders[decorationIndex];
            const bx::Vec3 centerLo = {
                static_cast<float>(collider.worldX),
                static_cast<float>(collider.worldY),
                static_cast<float>(collider.worldZ)
            };
            const float colliderRadius = static_cast<float>(collider.radius);
            const float colliderHeight = static_cast<float>(collider.height);
            const float cylinderMinX = centerLo.x - colliderRadius;
            const float cylinderMinY = centerLo.y - colliderRadius;
            const float cylinderMinZ = centerLo.z;
            const float cylinderMaxX = centerLo.x + colliderRadius;
            const float cylinderMaxY = centerLo.y + colliderRadius;
            const float cylinderMaxZ = centerLo.z + colliderHeight;

            if (!bboxIntersects(
                    collisionState.bboxMinX,
                    collisionState.bboxMinY,
                    collisionState.bboxMinZ,
                    collisionState.bboxMaxX,
                    collisionState.bboxMaxY,
                    collisionState.bboxMaxZ,
                    cylinderMinX,
                    cylinderMinY,
                    cylinderMinZ,
                    cylinderMaxX,
                    cylinderMaxY,
                    cylinderMaxZ))
            {
                continue;
            }

            float moveDistance = collisionState.adjustedMoveDistance;
            bx::Vec3 collisionPoint = {0.0f, 0.0f, 0.0f};

            if (!collideSphereWithCylinder(
                    centerLo,
                    colliderRadius,
                    colliderHeight,
                    position,
                    radius,
                    collisionState.direction,
                    collisionState.adjustedMoveDistance,
                    moveDistance,
                    collisionPoint))
            {
                continue;
            }

            if (moveDistance <= AllowedCollisionOvershoot || moveDistance >= collisionState.adjustedMoveDistance)
            {
                continue;
            }

            const bx::Vec3 outward = vecNormalize(
                bx::Vec3{
                    collisionPoint.x - centerLo.x,
                    collisionPoint.y - centerLo.y,
                    0.0f
                });

            collisionState.adjustedMoveDistance = moveDistance;
            collisionState.collisionPoint = collisionPoint;
            collisionState.heightOffset = heightOffset;
            collisionState.hit = CollisionHit{
                CollisionHit::Kind::Decoration,
                0,
                0,
                decorationIndex,
                0,
                0.0f,
                moveDistance,
                heightOffset,
                collisionPoint,
                outward,
                centerLo.z,
                centerLo.z + colliderHeight
            };
        }
    };

    collideOnce(collisionState.positionLo, collisionState.radiusLo, 0.0f);

    if (!collisionState.checkHi)
    {
        return;
    }

    collideOnce(
        collisionState.positionHi,
        collisionState.radiusHi,
        collisionState.positionHi.z - collisionState.positionLo.z);

    const bx::Vec3 midPosition = vecScale(vecAdd(collisionState.positionLo, collisionState.positionHi), 0.5f);
    collideOnce(midPosition, collisionState.radiusHi, midPosition.z - collisionState.positionLo.z);
}

void collideOutdoorWithActors(
    CollisionState &collisionState,
    const std::vector<OutdoorActorCollision> &actorColliders)
{
    auto collideOnce = [&collisionState, &actorColliders](
                           const bx::Vec3 &position,
                           float radius,
                           float heightOffset)
    {
        for (size_t actorIndex = 0; actorIndex < actorColliders.size(); ++actorIndex)
        {
            const OutdoorActorCollision &collider = actorColliders[actorIndex];
            const bx::Vec3 centerLo = {
                static_cast<float>(collider.worldX),
                static_cast<float>(collider.worldY),
                static_cast<float>(collider.worldZ)
            };
            const float colliderRadius = static_cast<float>(collider.radius);
            const float colliderHeight = static_cast<float>(collider.height);
            const float cylinderMinX = centerLo.x - colliderRadius;
            const float cylinderMinY = centerLo.y - colliderRadius;
            const float cylinderMinZ = centerLo.z;
            const float cylinderMaxX = centerLo.x + colliderRadius;
            const float cylinderMaxY = centerLo.y + colliderRadius;
            const float cylinderMaxZ = centerLo.z + colliderHeight;

            if (!bboxIntersects(
                    collisionState.bboxMinX,
                    collisionState.bboxMinY,
                    collisionState.bboxMinZ,
                    collisionState.bboxMaxX,
                    collisionState.bboxMaxY,
                    collisionState.bboxMaxZ,
                    cylinderMinX,
                    cylinderMinY,
                    cylinderMinZ,
                    cylinderMaxX,
                    cylinderMaxY,
                    cylinderMaxZ))
            {
                continue;
            }

            float moveDistance = collisionState.adjustedMoveDistance;
            bx::Vec3 collisionPoint = {0.0f, 0.0f, 0.0f};

            if (!collideSphereWithCylinder(
                    centerLo,
                    colliderRadius,
                    colliderHeight,
                    position,
                    radius,
                    collisionState.direction,
                    collisionState.adjustedMoveDistance,
                    moveDistance,
                    collisionPoint))
            {
                continue;
            }

            if (moveDistance <= AllowedCollisionOvershoot || moveDistance >= collisionState.adjustedMoveDistance)
            {
                continue;
            }

            const bx::Vec3 outward = vecNormalize(
                bx::Vec3{
                    collisionPoint.x - centerLo.x,
                    collisionPoint.y - centerLo.y,
                    0.0f
                });

            collisionState.adjustedMoveDistance = moveDistance;
            collisionState.collisionPoint = collisionPoint;
            collisionState.heightOffset = heightOffset;
            collisionState.hit = CollisionHit{
                CollisionHit::Kind::Actor,
                0,
                0,
                actorIndex,
                0,
                0.0f,
                moveDistance,
                heightOffset,
                collisionPoint,
                outward,
                centerLo.z,
                centerLo.z + colliderHeight
            };
        }
    };

    collideOnce(collisionState.positionLo, collisionState.radiusLo, 0.0f);

    if (!collisionState.checkHi)
    {
        return;
    }

    collideOnce(
        collisionState.positionHi,
        collisionState.radiusHi,
        collisionState.positionHi.z - collisionState.positionLo.z);

    const bx::Vec3 midPosition = vecScale(vecAdd(collisionState.positionLo, collisionState.positionHi), 0.5f);
    collideOnce(midPosition, collisionState.radiusHi, midPosition.z - collisionState.positionLo.z);
}

void collideOutdoorWithSpriteObjects(
    CollisionState &collisionState,
    const std::vector<OutdoorSpriteObjectCollision> &spriteObjectColliders)
{
    auto collideOnce = [&collisionState, &spriteObjectColliders](
                           const bx::Vec3 &position,
                           float radius,
                           float heightOffset)
    {
        for (size_t objectIndex = 0; objectIndex < spriteObjectColliders.size(); ++objectIndex)
        {
            const OutdoorSpriteObjectCollision &collider = spriteObjectColliders[objectIndex];
            const bx::Vec3 centerLo = {
                static_cast<float>(collider.worldX),
                static_cast<float>(collider.worldY),
                static_cast<float>(collider.worldZ)
            };
            const float colliderRadius = static_cast<float>(collider.radius);
            const float colliderHeight = static_cast<float>(collider.height);
            const float cylinderMinX = centerLo.x - colliderRadius;
            const float cylinderMinY = centerLo.y - colliderRadius;
            const float cylinderMinZ = centerLo.z;
            const float cylinderMaxX = centerLo.x + colliderRadius;
            const float cylinderMaxY = centerLo.y + colliderRadius;
            const float cylinderMaxZ = centerLo.z + colliderHeight;

            if (!bboxIntersects(
                    collisionState.bboxMinX,
                    collisionState.bboxMinY,
                    collisionState.bboxMinZ,
                    collisionState.bboxMaxX,
                    collisionState.bboxMaxY,
                    collisionState.bboxMaxZ,
                    cylinderMinX,
                    cylinderMinY,
                    cylinderMinZ,
                    cylinderMaxX,
                    cylinderMaxY,
                    cylinderMaxZ))
            {
                continue;
            }

            float moveDistance = collisionState.adjustedMoveDistance;
            bx::Vec3 collisionPoint = {0.0f, 0.0f, 0.0f};

            if (!collideSphereWithCylinder(
                    centerLo,
                    colliderRadius,
                    colliderHeight,
                    position,
                    radius,
                    collisionState.direction,
                    collisionState.adjustedMoveDistance,
                    moveDistance,
                    collisionPoint))
            {
                continue;
            }

            if (moveDistance <= AllowedCollisionOvershoot || moveDistance >= collisionState.adjustedMoveDistance)
            {
                continue;
            }

            const bx::Vec3 outward = vecNormalize(
                bx::Vec3{
                    collisionPoint.x - centerLo.x,
                    collisionPoint.y - centerLo.y,
                    0.0f
                });

            collisionState.adjustedMoveDistance = moveDistance;
            collisionState.collisionPoint = collisionPoint;
            collisionState.heightOffset = heightOffset;
            collisionState.hit = CollisionHit{
                CollisionHit::Kind::SpriteObject,
                0,
                0,
                objectIndex,
                0,
                0.0f,
                moveDistance,
                heightOffset,
                collisionPoint,
                outward,
                centerLo.z,
                centerLo.z + colliderHeight
            };
        }
    };

    collideOnce(collisionState.positionLo, collisionState.radiusLo, 0.0f);

    if (!collisionState.checkHi)
    {
        return;
    }

    collideOnce(
        collisionState.positionHi,
        collisionState.radiusHi,
        collisionState.positionHi.z - collisionState.positionLo.z);

    const bx::Vec3 midPosition = vecScale(vecAdd(collisionState.positionLo, collisionState.positionHi), 0.5f);
    collideOnce(midPosition, collisionState.radiusHi, midPosition.z - collisionState.positionLo.z);
}

FloorSample chooseBestFloorSample(const FloorSample &terrainSample, const std::vector<FloorSample> &samples, float z)
{
    FloorSample bestSample = terrainSample;
    float currentFloorLevel = terrainSample.height;

    for (const FloorSample &sample : samples)
    {
        if (currentFloorLevel <= z + FloorSelectionHeightTolerance)
        {
            if (sample.height >= currentFloorLevel && sample.height <= z + FloorSelectionHeightTolerance)
            {
                currentFloorLevel = sample.height;
                bestSample = sample;
            }
        }
        else if (sample.height < currentFloorLevel)
        {
            currentFloorLevel = sample.height;
            bestSample = sample;
        }
    }

    if (bestSample.height < terrainSample.height)
    {
        return terrainSample;
    }

    return bestSample;
}

const OutdoorFaceGeometryData *findFaceGeometry(
    const std::vector<OutdoorFaceGeometryData> &faces,
    size_t bModelIndex,
    size_t faceIndex)
{
    for (const OutdoorFaceGeometryData &geometry : faces)
    {
        if (geometry.bModelIndex == bModelIndex && geometry.faceIndex == faceIndex)
        {
            return &geometry;
        }
    }

    return nullptr;
}

std::optional<FloorSample> queryPreferredSupportFloor(
    const std::vector<OutdoorFaceGeometryData> &faces,
    const OutdoorMoveState &state,
    float x,
    float y,
    float z)
{
    if (state.supportKind != OutdoorSupportKind::BModelFace)
    {
        return std::nullopt;
    }

    const OutdoorFaceGeometryData *pGeometry =
        findFaceGeometry(faces, state.supportBModelIndex, state.supportFaceIndex);

    if (pGeometry == nullptr
        || !pGeometry->isWalkable
        || x < pGeometry->minX - PartyRadius
        || x > pGeometry->maxX + PartyRadius
        || y < pGeometry->minY - PartyRadius
        || y > pGeometry->maxY + PartyRadius
        || !isPointInsideOrNearPolygon(x, y, pGeometry->vertices, PartyRadius))
    {
        return std::nullopt;
    }

    float height = 0.0f;

    if (!calculateFaceHeight(*pGeometry, x, y, height) || height > z + FloorSelectionHeightTolerance)
    {
        return std::nullopt;
    }

    return FloorSample{
        true,
        height,
        std::fabs(pGeometry->normal.z),
        true,
        (pGeometry->attributes & FaceAttributeFluid) != 0,
        false,
        pGeometry->bModelIndex,
        pGeometry->faceIndex
    };
}

FloorSample queryFloorLevel(
    const OutdoorMapData &outdoorMapData,
    const std::vector<OutdoorFaceGeometryData> &faces,
    const std::optional<OutdoorMoveState> &preferredState,
    float x,
    float y,
    float z)
{
    const uint8_t terrainFlags = sampleOutdoorTerrainTileAttributes(outdoorMapData, x, y);
    const FloorSample terrainSample = {
        true,
        sampleOutdoorTerrainHeight(outdoorMapData, x, y),
        sampleOutdoorTerrainNormalZ(outdoorMapData, x, y),
        false,
        (terrainFlags & 0x02) != 0,
        (terrainFlags & 0x01) != 0,
        0,
        0
    };
    std::vector<FloorSample> samples;

    for (const OutdoorFaceGeometryData &geometry : faces)
    {
        if (!geometry.isWalkable
            || x < geometry.minX
            || x > geometry.maxX
            || y < geometry.minY
            || y > geometry.maxY
            || !isPointInsideOrNearPolygon(x, y, geometry.vertices, FloorCheckSlack))
        {
            continue;
        }

        float height = 0.0f;

        if (!calculateFaceHeight(geometry, x, y, height))
        {
            continue;
        }

        samples.push_back({
            true,
            height,
            std::fabs(geometry.normal.z),
            true,
            (geometry.attributes & FaceAttributeFluid) != 0,
            false,
            geometry.bModelIndex,
            geometry.faceIndex
        });
    }

    FloorSample bestSample = chooseBestFloorSample(terrainSample, samples, z);

    if (preferredState)
    {
        const std::optional<FloorSample> preferredSample =
            queryPreferredSupportFloor(faces, *preferredState, x, y, z);

        if (preferredSample
            && preferredSample->height >= bestSample.height
            && preferredSample->height <= z + FloorSelectionHeightTolerance)
        {
            bestSample = *preferredSample;
        }
    }

    return bestSample;
}

}

OutdoorMovementController::OutdoorMovementController(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet
)
    : m_pOutdoorMapData(&outdoorMapData)
    , m_outdoorLandMask(outdoorLandMask)
{
    buildFaceCache();
    buildDecorationColliderCache(outdoorDecorationCollisionSet);
    buildActorColliderCache(outdoorActorCollisionSet);
    buildSpriteObjectColliderCache(outdoorSpriteObjectCollisionSet);
}

OutdoorMoveState OutdoorMovementController::initializeState(float x, float y, float footZHint) const
{
    const FloorSample floor = queryFloorLevel(*m_pOutdoorMapData, m_faces, std::nullopt, x, y, footZHint);
    OutdoorMoveState state = {};
    state.x = x;
    state.y = y;
    state.footZ = floor.height + GroundSnapHeight;
    state.verticalVelocity = 0.0f;
    state.supportKind = floor.fromBModel ? OutdoorSupportKind::BModelFace : OutdoorSupportKind::Terrain;
    state.supportBModelIndex = floor.bModelIndex;
    state.supportFaceIndex = floor.faceIndex;
    state.supportIsFluid = floor.isFluid;
    state.supportOnWater = floor.isFluid
        || (!floor.fromBModel
            && (isOutdoorTerrainWater(*m_pOutdoorMapData, x, y) || isOutdoorLandMaskWater(m_outdoorLandMask, x, y)));
    state.supportOnBurning = floor.isBurning;
    state.airborne = false;
    state.landedThisFrame = false;
    state.fallStartZ = state.footZ;
    state.fallDistance = 0.0f;
    return state;
}

OutdoorMoveState OutdoorMovementController::resolveMove(
    const OutdoorMoveState &state,
    float desiredVelocityX,
    float desiredVelocityY,
    bool jumpRequested,
    bool flyDownRequested,
    bool flyingActive,
    float jumpVelocity,
    float flyVerticalSpeed,
    float deltaSeconds,
    std::vector<size_t> *pContactedActorIndices
) const
{
    const FloorSample currentFloor = queryFloorLevel(*m_pOutdoorMapData, m_faces, state, state.x, state.y, state.footZ);
    const float currentGroundLevel = currentFloor.height + GroundSnapHeight;
    const bool partyAtHighSlope = !currentFloor.fromBModel && terrainSlopeTooHigh(*m_pOutdoorMapData, state.x, state.y);
    bool partyNotTouchingFloor = state.footZ > currentGroundLevel + GroundSnapHeight;
    const bool partyCloseToGround = state.footZ <= currentGroundLevel + CloseToGroundHeight;
    const bool wasAirborne = state.airborne || partyNotTouchingFloor;
    float fallStartZ = state.fallStartZ;

    if (wasAirborne)
    {
        fallStartZ = std::max(fallStartZ, state.footZ);
    }
    else
    {
        fallStartZ = state.footZ;
    }

    bx::Vec3 partyNewPosition = {state.x, state.y, state.footZ};
    bx::Vec3 partyInputSpeed = {desiredVelocityX, desiredVelocityY, state.verticalVelocity};

    if (partyNewPosition.z < currentGroundLevel)
    {
        partyNewPosition.z = currentGroundLevel;
        partyInputSpeed.z = 0.0f;
    }

    if (flyingActive)
    {
        if (jumpRequested)
        {
            partyInputSpeed.z = flyVerticalSpeed;
        }
        else if (flyDownRequested)
        {
            partyInputSpeed.z = -flyVerticalSpeed;
        }
        else
        {
            partyInputSpeed.z = 0.0f;
        }
    }
    else if ((!partyAtHighSlope || currentFloor.fromBModel) &&
             (!partyNotTouchingFloor || (partyCloseToGround && partyInputSpeed.z <= 0.0f)) &&
             !state.supportOnWater &&
             !state.supportOnBurning &&
             jumpRequested)
    {
        partyInputSpeed.z = jumpVelocity;
        partyNewPosition.z += 1.0f;
    }
    else if (partyNotTouchingFloor)
    {
        partyInputSpeed.z -= GravityPerSecond * deltaSeconds;
    }
    else if (!currentFloor.fromBModel && partyAtHighSlope)
    {
        partyNewPosition.z = currentGroundLevel;
    }

    const auto runCollisionPass =
        [this, deltaSeconds, &state, pContactedActorIndices](
            bx::Vec3 &passPosition,
            bx::Vec3 &passInputSpeed,
            bool &passPartyNotOnModel)
    {
        CollisionState collisionState = {};
        collisionState.radiusLo = PartyRadius;
        collisionState.radiusHi = PartyRadius;
        collisionState.checkHi = true;

        for (int attempt = 0; attempt < 5; ++attempt)
        {
            resolveActorCylinderOverlaps(passPosition, m_actorColliders);
            const bx::Vec3 attemptStartPosition = passPosition;
            collisionState.positionHi =
                vecAdd(passPosition, bx::Vec3{0.0f, 0.0f, PartyHeight - collisionState.radiusLo});
            collisionState.positionLo = vecAdd(passPosition, bx::Vec3{0.0f, 0.0f, collisionState.radiusLo});
            collisionState.velocity = passInputSpeed;

            if (prepareCollisionState(collisionState, deltaSeconds))
            {
                break;
            }

            collideOutdoorWithModels(collisionState, m_faces);
            collideOutdoorWithDecorations(collisionState, m_decorationColliders);
            collideOutdoorWithActors(collisionState, m_actorColliders);
            collideOutdoorWithSpriteObjects(collisionState, m_spriteObjectColliders);

            bx::Vec3 newPosLow = {0.0f, 0.0f, 0.0f};

            if (collisionState.adjustedMoveDistance >= collisionState.moveDistance)
            {
                newPosLow = {
                    collisionState.newPositionLo.x,
                    collisionState.newPositionLo.y,
                    collisionState.newPositionLo.z - collisionState.radiusLo
                };
            }
            else
            {
                newPosLow = vecAdd(
                    passPosition,
                    vecScale(collisionState.direction, collisionState.adjustedMoveDistance - ClosestDistance));
                collisionState.collisionPoint =
                    vecSubtract(collisionState.collisionPoint, vecScale(collisionState.direction, ClosestDistance));
            }

            const FloorSample allNewFloor = queryFloorLevel(
                *m_pOutdoorMapData,
                m_faces,
                state,
                newPosLow.x,
                newPosLow.y,
                newPosLow.z);
            const FloorSample xAdvanceFloor = queryFloorLevel(
                *m_pOutdoorMapData,
                m_faces,
                state,
                newPosLow.x,
                passPosition.y,
                newPosLow.z);
            const FloorSample yAdvanceFloor = queryFloorLevel(
                *m_pOutdoorMapData,
                m_faces,
                state,
                passPosition.x,
                newPosLow.y,
                newPosLow.z);

            passPartyNotOnModel = !xAdvanceFloor.fromBModel && !yAdvanceFloor.fromBModel && !allNewFloor.fromBModel;

            if (!passPartyNotOnModel)
            {
                passPosition.x = newPosLow.x;
                passPosition.y = newPosLow.y;
            }
            else
            {
                bool moveInX = true;
                bool moveInY = true;

                if (terrainSlopeTooHigh(*m_pOutdoorMapData, newPosLow.x, passPosition.y)
                    && xAdvanceFloor.height > passPosition.z)
                {
                    moveInX = false;
                }

                if (terrainSlopeTooHigh(*m_pOutdoorMapData, passPosition.x, newPosLow.y)
                    && yAdvanceFloor.height > passPosition.z)
                {
                    moveInY = false;
                }

                if (moveInX)
                {
                    passPosition.x = newPosLow.x;

                    if (moveInY)
                    {
                        passPosition.y = newPosLow.y;
                    }
                }
                else if (moveInY)
                {
                    passPosition.y = newPosLow.y;
                }
                else if (terrainSlopeTooHigh(*m_pOutdoorMapData, newPosLow.x, newPosLow.y)
                    && allNewFloor.height <= passPosition.z)
                {
                    passPosition.x = newPosLow.x;
                    passPosition.y = newPosLow.y;
                }

            }

            if (collisionState.adjustedMoveDistance >= collisionState.moveDistance)
            {
                if (!passPartyNotOnModel)
                {
                    passPosition.x = collisionState.newPositionLo.x;
                    passPosition.y = collisionState.newPositionLo.y;
                }

                passPosition.z = collisionState.newPositionLo.z - collisionState.radiusLo;
                break;
            }

            collisionState.totalMoveDistance += collisionState.adjustedMoveDistance;
            passPosition = newPosLow;

            if (!collisionState.hit)
            {
                passInputSpeed = vecScale(passInputSpeed, 0.89263916f);
                continue;
            }

            const CollisionHit &hit = *collisionState.hit;

            if (hit.kind == CollisionHit::Kind::Decoration
                || hit.kind == CollisionHit::Kind::Actor
                || hit.kind == CollisionHit::Kind::SpriteObject)
            {
                bx::Vec3 colliderCenter = {0.0f, 0.0f, 0.0f};

                if (hit.kind == CollisionHit::Kind::Decoration)
                {
                if (hit.colliderIndex >= m_decorationColliders.size())
                {
                    passInputSpeed = vecScale(passInputSpeed, 0.89263916f);
                    continue;
                }

                    colliderCenter = {
                        static_cast<float>(m_decorationColliders[hit.colliderIndex].worldX),
                        static_cast<float>(m_decorationColliders[hit.colliderIndex].worldY),
                        static_cast<float>(m_decorationColliders[hit.colliderIndex].worldZ)
                    };
                }
                else if (hit.kind == CollisionHit::Kind::Actor)
                {
                    if (hit.colliderIndex >= m_actorColliders.size())
                    {
                        passInputSpeed = vecScale(passInputSpeed, 0.89263916f);
                        continue;
                    }

                    colliderCenter = {
                        static_cast<float>(m_actorColliders[hit.colliderIndex].worldX),
                        static_cast<float>(m_actorColliders[hit.colliderIndex].worldY),
                        static_cast<float>(m_actorColliders[hit.colliderIndex].worldZ)
                    };

                    if (pContactedActorIndices != nullptr)
                    {
                        pContactedActorIndices->push_back(m_actorColliders[hit.colliderIndex].sourceIndex);
                    }
                }
                else
                {
                    if (hit.colliderIndex >= m_spriteObjectColliders.size())
                    {
                        passInputSpeed = vecScale(passInputSpeed, 0.89263916f);
                        continue;
                    }

                    colliderCenter = {
                        static_cast<float>(m_spriteObjectColliders[hit.colliderIndex].worldX),
                        static_cast<float>(m_spriteObjectColliders[hit.colliderIndex].worldY),
                        static_cast<float>(m_spriteObjectColliders[hit.colliderIndex].worldZ)
                    };
                }

                const bx::Vec3 slidePlaneOrigin = collisionState.collisionPoint;
                bx::Vec3 slidePlaneNormal = {
                    slidePlaneOrigin.x - colliderCenter.x,
                    slidePlaneOrigin.y - colliderCenter.y,
                    0.0f
                };
                slidePlaneNormal = vecNormalize(slidePlaneNormal);

                if (vecLength(slidePlaneNormal) <= CollisionEpsilon)
                {
                    passInputSpeed = vecScale(passInputSpeed, 0.89263916f);
                    continue;
                }

                const float destinationPlaneDistance =
                    vecDot(vecSubtract(collisionState.newPositionLo, slidePlaneOrigin), slidePlaneNormal);
                const bx::Vec3 newDestination = vecSubtract(
                    collisionState.newPositionLo,
                    vecScale(slidePlaneNormal, destinationPlaneDistance));
                bx::Vec3 newDirection = vecSubtract(newDestination, collisionState.collisionPoint);
                newDirection.z = 0.0f;
                newDirection = vecNormalize(newDirection);
                passInputSpeed = vecScale(newDirection, vecDot(newDirection, passInputSpeed));
                continue;
            }

            const OutdoorFaceGeometryData *pGeometry = nullptr;

            for (const OutdoorFaceGeometryData &geometry : m_faces)
            {
                if (geometry.bModelIndex == hit.bModelIndex && geometry.faceIndex == hit.faceIndex)
                {
                    pGeometry = &geometry;
                    break;
                }
            }

            if (!pGeometry)
            {
                passInputSpeed = vecScale(passInputSpeed, 0.89263916f);
                continue;
            }

            bool faceSlopeTooSteep =
                pGeometry->normal.z > 0.0f
                && pGeometry->normal.z < WalkableNormalZ;

            if (faceSlopeTooSteep && (pGeometry->maxZ - pGeometry->minZ) < MaxSmallSlopeHeight)
            {
                faceSlopeTooSteep = false;
            }

            const bx::Vec3 slidePlaneOrigin = vecSubtract(
                collisionState.collisionPoint,
                bx::Vec3{0.0f, 0.0f, collisionState.heightOffset});
            bx::Vec3 slidePlaneNormal = vecSubtract(
                vecAdd(newPosLow, bx::Vec3{0.0f, 0.0f, collisionState.radiusLo}),
                slidePlaneOrigin);
            slidePlaneNormal = vecNormalize(slidePlaneNormal);

            if (vecLength(slidePlaneNormal) <= CollisionEpsilon)
            {
                passInputSpeed = vecScale(passInputSpeed, 0.89263916f);
                continue;
            }

            const float destinationPlaneDistance =
                vecDot(vecSubtract(collisionState.newPositionLo, slidePlaneOrigin), slidePlaneNormal);
            const bx::Vec3 newDestination = vecSubtract(
                collisionState.newPositionLo,
                vecScale(slidePlaneNormal, destinationPlaneDistance));
            bx::Vec3 newDirection = vecSubtract(newDestination, slidePlaneOrigin);

            if (faceSlopeTooSteep && newDirection.z > 0.0f)
            {
                newDirection.z = 0.0f;
            }

            newDirection = vecNormalize(newDirection);

            if (faceSlopeTooSteep)
            {
                passInputSpeed = vecAdd(
                    passInputSpeed,
                    bx::Vec3{pGeometry->normal.x * 10.0f, pGeometry->normal.y * 10.0f, -20.0f});
            }

            passInputSpeed = vecScale(newDirection, vecDot(newDirection, passInputSpeed));

            if (pGeometry->polygonType == PolygonFloor || pGeometry->polygonType == PolygonInBetweenFloorAndWall)
            {
                if (pGeometry->polygonType == PolygonFloor)
                {
                    const float floorRise = hit.floorHeight - passPosition.z;

                    if (floorRise > 0.0f && floorRise < 128.0f)
                    {
                        passPosition.z = hit.floorHeight;
                    }
                }
            }
            else
            {
                passInputSpeed = vecScale(passInputSpeed, 0.89263916f);
            }

        }
    };

    const float savedZSpeed = partyInputSpeed.z;
    bx::Vec3 horizontalInputSpeed = {partyInputSpeed.x, partyInputSpeed.y, 0.0f};
    bool partyNotOnModel = !currentFloor.fromBModel;
    runCollisionPass(partyNewPosition, horizontalInputSpeed, partyNotOnModel);

    if (partyNewPosition.z <= state.footZ)
    {
        bx::Vec3 verticalInputSpeed = {0.0f, 0.0f, savedZSpeed};
        runCollisionPass(partyNewPosition, verticalInputSpeed, partyNotOnModel);
        partyInputSpeed.z = verticalInputSpeed.z;
    }
    else
    {
        partyInputSpeed.z = savedZSpeed;
    }

    const FloorSample finalFloor = queryFloorLevel(
        *m_pOutdoorMapData,
        m_faces,
        state,
        partyNewPosition.x,
        partyNewPosition.y,
        partyNewPosition.z);
    const float finalGroundLevel = finalFloor.height + GroundSnapHeight;
    bool landedThisFrame = false;
    float fallDistance = 0.0f;

    if (partyNewPosition.z <= finalGroundLevel)
    {
        landedThisFrame = wasAirborne && partyInputSpeed.z <= 0.0f;
        fallDistance = std::max(0.0f, fallStartZ - finalGroundLevel);
        partyNewPosition.z = finalGroundLevel;
        partyInputSpeed.z = 0.0f;
    }

    OutdoorMoveState result = {};
    result.x = partyNewPosition.x;
    result.y = partyNewPosition.y;
    result.footZ = partyNewPosition.z;
    result.verticalVelocity = partyInputSpeed.z;
    result.supportKind = finalFloor.fromBModel ? OutdoorSupportKind::BModelFace : OutdoorSupportKind::Terrain;
    result.supportBModelIndex = finalFloor.bModelIndex;
    result.supportFaceIndex = finalFloor.faceIndex;
    result.supportIsFluid = finalFloor.isFluid;
    if (state.airborne)
    {
        result.airborne = result.footZ > finalGroundLevel + GroundSnapHeight;
    }
    else
    {
        result.airborne = result.footZ > finalGroundLevel + CloseToGroundHeight;
    }
    result.supportOnWater = !result.airborne
        && (finalFloor.isFluid
            || (!finalFloor.fromBModel
                && (isOutdoorTerrainWater(*m_pOutdoorMapData, partyNewPosition.x, partyNewPosition.y)
                    || isOutdoorLandMaskWater(m_outdoorLandMask, partyNewPosition.x, partyNewPosition.y))));
    result.supportOnBurning = !result.airborne
        && !finalFloor.fromBModel
        && isOutdoorTerrainBurning(*m_pOutdoorMapData, partyNewPosition.x, partyNewPosition.y);
    result.landedThisFrame = landedThisFrame;
    result.fallDistance = landedThisFrame ? fallDistance : 0.0f;
    result.fallStartZ = result.airborne ? std::max(fallStartZ, result.footZ) : result.footZ;
    return result;
}

void OutdoorMovementController::setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders)
{
    m_actorColliders = actorColliders;
}

void OutdoorMovementController::buildFaceCache()
{
    m_faces.clear();

    for (size_t bModelIndex = 0; bModelIndex < m_pOutdoorMapData->bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bModel = m_pOutdoorMapData->bmodels[bModelIndex];

        for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
        {
            const OutdoorBModelFace &face = bModel.faces[faceIndex];

            if (face.vertexIndices.size() < 3)
            {
                continue;
            }

            OutdoorFaceGeometryData geometry = {};

            if (!buildOutdoorFaceGeometry(bModel, bModelIndex, face, faceIndex, geometry))
            {
                continue;
            }

            geometry.normal = vecScale(geometry.normal, -1.0f);
            m_faces.push_back(std::move(geometry));
        }
    }
}

void OutdoorMovementController::buildDecorationColliderCache(
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet)
{
    m_decorationColliders.clear();

    if (!outdoorDecorationCollisionSet)
    {
        return;
    }

    m_decorationColliders.reserve(outdoorDecorationCollisionSet->colliders.size());

    for (const OutdoorDecorationCollision &collision : outdoorDecorationCollisionSet->colliders)
    {
        m_decorationColliders.push_back(collision);
    }
}

void OutdoorMovementController::buildActorColliderCache(
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet)
{
    m_actorColliders.clear();

    if (!outdoorActorCollisionSet)
    {
        return;
    }

    m_actorColliders.reserve(outdoorActorCollisionSet->colliders.size());

    for (const OutdoorActorCollision &collision : outdoorActorCollisionSet->colliders)
    {
        m_actorColliders.push_back(collision);
    }
}

void OutdoorMovementController::buildSpriteObjectColliderCache(
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectSet)
{
    m_spriteObjectColliders.clear();

    if (!outdoorSpriteObjectSet)
    {
        return;
    }

    m_spriteObjectColliders.reserve(outdoorSpriteObjectSet->colliders.size());

    for (const OutdoorSpriteObjectCollision &collision : outdoorSpriteObjectSet->colliders)
    {
        m_spriteObjectColliders.push_back(collision);
    }
}
}
