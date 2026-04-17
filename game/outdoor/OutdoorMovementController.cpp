#include "game/outdoor/OutdoorMovementController.h"
#include "game/FaceEnums.h"

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
constexpr float FaceGridCellSize = 2048.0f;
constexpr float WalkableNormalZ = 0.70767211914f;
constexpr float DefaultBodyRadius = 37.0f;
constexpr float DefaultBodyHeight = 192.0f;
constexpr float MaxSmallSlopeHeight = 128.0f;
constexpr float GroundSnapHeight = 1.0f;
constexpr float CloseToGroundHeight = 32.0f;
// OE outdoor party gravity is -2 * dtTicks * Gravity, with default Gravity = 5 and dt at 128 Hz.
constexpr float GravityPerSecond = 1280.0f;
constexpr uint8_t PolygonFloor = 0x3;
constexpr uint8_t PolygonInBetweenFloorAndWall = 0x4;
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
    float radiusLo = DefaultBodyRadius;
    float radiusHi = DefaultBodyRadius;
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
    const float gridXFloat = outdoorWorldToGridXFloat(x);
    const float gridYFloat = outdoorWorldToGridYFloat(y);
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

    const float tileMinWorldX = outdoorGridCornerWorldX(gridX);
    const float tileTopWorldY = outdoorGridCornerWorldY(gridY);
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

    const float gridX = outdoorWorldToGridXFloat(x);
    const float gridY = outdoorWorldToGridYFloat(y);
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

bool isOutdoorPositionWater(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    float x,
    float y)
{
    return isOutdoorTerrainWater(outdoorMapData, x, y) || isOutdoorLandMaskWater(outdoorLandMask, x, y);
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

void resolveActorCylinderOverlaps(
    bx::Vec3 &bodyPosition,
    float bodyRadius,
    float bodyHeight,
    const std::vector<OutdoorActorCollision> &actorColliders,
    const std::optional<OutdoorIgnoredActorCollider> &ignoredActorCollider,
    std::vector<size_t> *pContactedActorIndices = nullptr)
{
    for (int iteration = 0; iteration < 4; ++iteration)
    {
        bool resolvedAny = false;

        for (const OutdoorActorCollision &collider : actorColliders)
        {
            if (ignoredActorCollider
                && collider.source == ignoredActorCollider->source
                && collider.sourceIndex == ignoredActorCollider->sourceIndex)
            {
                continue;
            }

            const float actorRadius = static_cast<float>(collider.radius);
            const float combinedRadius = bodyRadius + actorRadius;
            const float deltaX = bodyPosition.x - static_cast<float>(collider.worldX);
            const float deltaY = bodyPosition.y - static_cast<float>(collider.worldY);
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY;

            if (distanceSquared >= combinedRadius * combinedRadius)
            {
                continue;
            }

            const float partyMinZ = bodyPosition.z;
            const float partyMaxZ = bodyPosition.z + bodyHeight;
            const float actorMinZ = static_cast<float>(collider.worldZ);
            const float actorMaxZ = actorMinZ + static_cast<float>(collider.height);

            if (!rangesOverlap(partyMinZ, partyMaxZ, actorMinZ, actorMaxZ))
            {
                continue;
            }

            if (pContactedActorIndices != nullptr)
            {
                pContactedActorIndices->push_back(collider.sourceIndex);
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
            bodyPosition.x += outwardX * pushDistance;
            bodyPosition.y += outwardY * pushDistance;
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
    const std::vector<OutdoorFaceGeometryData> &faces,
    const std::vector<size_t> *pCandidateFaceIndices = nullptr)
{
    auto collideFace =
        [&collisionState](const OutdoorFaceGeometryData &geometry)
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
            return;
        }

        collideBodyWithFace(collisionState, geometry);
    };

    if (pCandidateFaceIndices != nullptr)
    {
        for (size_t faceIndex : *pCandidateFaceIndices)
        {
            if (faceIndex >= faces.size())
            {
                return;
            }

            collideFace(faces[faceIndex]);
        }

        return;
    }

    for (const OutdoorFaceGeometryData &geometry : faces)
    {
        collideFace(geometry);
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
                return;
            }

            if (moveDistance <= AllowedCollisionOvershoot || moveDistance >= collisionState.adjustedMoveDistance)
            {
                return;
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
    const std::vector<OutdoorActorCollision> &actorColliders,
    const std::optional<OutdoorIgnoredActorCollider> &ignoredActorCollider)
{
    auto collideOnce = [&collisionState, &actorColliders, &ignoredActorCollider](
                           const bx::Vec3 &position,
                           float radius,
                           float heightOffset)
    {
        for (size_t actorIndex = 0; actorIndex < actorColliders.size(); ++actorIndex)
        {
            const OutdoorActorCollision &collider = actorColliders[actorIndex];

            if (ignoredActorCollider
                && collider.source == ignoredActorCollider->source
                && collider.sourceIndex == ignoredActorCollider->sourceIndex)
            {
                continue;
            }

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
    const std::vector<OutdoorSpriteObjectCollision> &spriteObjectColliders,
    const std::vector<size_t> *pCandidateIndices)
{
    auto collideOnce = [&collisionState, &spriteObjectColliders, pCandidateIndices](
                           const bx::Vec3 &position,
                           float radius,
                           float heightOffset)
    {
        auto collideObject = [&](size_t objectIndex)
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
                return;
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
                return;
            }

            if (moveDistance <= AllowedCollisionOvershoot || moveDistance >= collisionState.adjustedMoveDistance)
            {
                return;
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
        };

        if (pCandidateIndices != nullptr)
        {
            for (size_t objectIndex : *pCandidateIndices)
            {
                collideObject(objectIndex);
            }
        }
        else
        {
            for (size_t objectIndex = 0; objectIndex < spriteObjectColliders.size(); ++objectIndex)
            {
                collideObject(objectIndex);
            }
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

FloorSample chooseBestFloorSample(
    const FloorSample &terrainSample,
    const std::vector<FloorSample> &samples,
    float z,
    float maxFloorRise)
{
    FloorSample bestSample = terrainSample;
    float currentFloorLevel = terrainSample.height;

    for (const FloorSample &sample : samples)
    {
        if (currentFloorLevel <= z + maxFloorRise)
        {
            if (sample.height >= currentFloorLevel && sample.height <= z + maxFloorRise)
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

float faceSignedDistance(const OutdoorFaceGeometryData &geometry, const bx::Vec3 &point)
{
    return vecDot(geometry.normal, vecSubtract(point, geometry.vertices[0]));
}

std::optional<FloorSample> queryPreferredSupportFloor(
    const std::vector<OutdoorFaceGeometryData> &faces,
    const OutdoorMoveState &state,
    float bodyRadius,
    float maxFloorRise,
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
        || x < pGeometry->minX - bodyRadius
        || x > pGeometry->maxX + bodyRadius
        || y < pGeometry->minY - bodyRadius
        || y > pGeometry->maxY + bodyRadius
        || !isPointInsideOrNearPolygon(x, y, pGeometry->vertices, bodyRadius))
    {
        return std::nullopt;
    }

    float height = 0.0f;

    if (!calculateFaceHeight(*pGeometry, x, y, height) || height > z + maxFloorRise)
    {
        return std::nullopt;
    }

    return FloorSample{
        true,
        height,
        std::fabs(pGeometry->normal.z),
        true,
        hasFaceAttribute(pGeometry->attributes, FaceAttribute::Fluid),
        false,
        pGeometry->bModelIndex,
        pGeometry->faceIndex
    };
}

FloorSample queryFloorLevel(
    const OutdoorMapData &outdoorMapData,
    const std::vector<OutdoorFaceGeometryData> &faces,
    const std::optional<OutdoorMoveState> &preferredState,
    const std::vector<size_t> *pCandidateFaceIndices,
    float bodyRadius,
    float maxFloorRise,
    float x,
    float y,
    float z)
{
    const uint8_t terrainFlags = sampleOutdoorTerrainTileAttributes(outdoorMapData, x, y);
    const FloorSample terrainSample = {
        true,
        sampleOutdoorRenderedTerrainHeight(outdoorMapData, x, y),
        sampleOutdoorTerrainNormalZ(outdoorMapData, x, y),
        false,
        (terrainFlags & 0x02) != 0,
        (terrainFlags & 0x01) != 0,
        0,
        0
    };
    std::vector<FloorSample> samples;

    auto appendFloorSample =
        [&](const OutdoorFaceGeometryData &geometry)
    {
        if (!geometry.isWalkable
            || x < geometry.minX
            || x > geometry.maxX
            || y < geometry.minY
            || y > geometry.maxY
            || !isPointInsideOrNearPolygon(x, y, geometry.vertices, FloorCheckSlack))
        {
            return;
        }

        float height = 0.0f;

        if (!calculateFaceHeight(geometry, x, y, height))
        {
            return;
        }

        samples.push_back({
            true,
            height,
            std::fabs(geometry.normal.z),
            true,
            hasFaceAttribute(geometry.attributes, FaceAttribute::Fluid),
            false,
            geometry.bModelIndex,
            geometry.faceIndex
        });
    };

    if (pCandidateFaceIndices != nullptr)
    {
        for (size_t faceIndex : *pCandidateFaceIndices)
        {
            if (faceIndex >= faces.size())
            {
                continue;
            }

            appendFloorSample(faces[faceIndex]);
        }

        FloorSample bestSample = chooseBestFloorSample(terrainSample, samples, z, maxFloorRise);

        if (preferredState)
        {
            const std::optional<FloorSample> preferredSample =
                queryPreferredSupportFloor(faces, *preferredState, bodyRadius, maxFloorRise, x, y, z);

            if (preferredSample
                && preferredSample->height >= bestSample.height
                && preferredSample->height <= z + maxFloorRise)
            {
                bestSample = *preferredSample;
            }
        }

        return bestSample;
    }

    for (const OutdoorFaceGeometryData &geometry : faces)
    {
        appendFloorSample(geometry);
    }

    FloorSample bestSample = chooseBestFloorSample(terrainSample, samples, z, maxFloorRise);

    if (preferredState)
    {
        const std::optional<FloorSample> preferredSample =
            queryPreferredSupportFloor(faces, *preferredState, bodyRadius, maxFloorRise, x, y, z);

        if (preferredSample
            && preferredSample->height >= bestSample.height
            && preferredSample->height <= z + maxFloorRise)
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
    : OutdoorMovementController(
        outdoorMapData,
        std::nullopt,
        outdoorLandMask,
        outdoorDecorationCollisionSet,
        outdoorActorCollisionSet,
        outdoorSpriteObjectCollisionSet)
{
}

OutdoorMovementController::OutdoorMovementController(
    const OutdoorMapData &outdoorMapData,
    const std::optional<MapBounds> &mapBounds,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet
)
    : m_pOutdoorMapData(&outdoorMapData)
    , m_mapBounds(mapBounds)
    , m_outdoorLandMask(outdoorLandMask)
{
    buildFaceCache();
    buildDecorationColliderCache(outdoorDecorationCollisionSet);
    buildActorColliderCache(outdoorActorCollisionSet);
    buildSpriteObjectColliderCache(outdoorSpriteObjectCollisionSet);
}

OutdoorMoveState OutdoorMovementController::initializeState(float x, float y, float footZHint) const
{
    return initializeStateForBody(x, y, footZHint, DefaultBodyRadius);
}

OutdoorMoveState OutdoorMovementController::initializeStateForBody(
    float x,
    float y,
    float footZHint,
    float bodyRadius) const
{
    clampPositionToBounds(std::max(1.0f, bodyRadius), x, y);
    std::vector<size_t> candidateFaceIndices;
    collectFaceCandidates(
        x - std::max(bodyRadius, FloorCheckSlack),
        y - std::max(bodyRadius, FloorCheckSlack),
        x + std::max(bodyRadius, FloorCheckSlack),
        y + std::max(bodyRadius, FloorCheckSlack),
        candidateFaceIndices);
    const FloorSample floor =
        queryFloorLevel(
            *m_pOutdoorMapData,
            m_faces,
            std::nullopt,
            &candidateFaceIndices,
            bodyRadius,
            FloorSelectionHeightTolerance,
            x,
            y,
            footZHint);
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
    float desiredVelocityZ,
    bool jumpRequested,
    bool flyUpRequested,
    bool flyDownRequested,
    bool flyingActive,
    bool waterWalkActive,
    float jumpVelocity,
    float flyVerticalSpeed,
    float maxFlightHeight,
    float deltaSeconds,
    std::vector<size_t> *pContactedActorIndices
) const
{
    return resolveMoveForBody(
        state,
        OutdoorBodyDimensions{DefaultBodyRadius, DefaultBodyHeight},
        desiredVelocityX,
        desiredVelocityY,
        desiredVelocityZ,
        jumpRequested,
        flyUpRequested,
        flyDownRequested,
        flyingActive,
        waterWalkActive,
        jumpVelocity,
        flyVerticalSpeed,
        maxFlightHeight,
        deltaSeconds,
        pContactedActorIndices);
}

OutdoorMoveState OutdoorMovementController::resolveMoveForBody(
    const OutdoorMoveState &state,
    const OutdoorBodyDimensions &body,
    float desiredVelocityX,
    float desiredVelocityY,
    float desiredVelocityZ,
    bool jumpRequested,
    bool flyUpRequested,
    bool flyDownRequested,
    bool flyingActive,
    bool waterWalkActive,
    float jumpVelocity,
    float flyVerticalSpeed,
    float maxFlightHeight,
    float deltaSeconds,
    std::vector<size_t> *pContactedActorIndices,
    const std::optional<OutdoorIgnoredActorCollider> &ignoredActorCollider
) const
{
    const float bodyRadius = std::max(1.0f, body.radius);
    const float bodyHeight = std::max(bodyRadius * 2.0f + 2.0f, body.height);
    std::vector<size_t> candidateFaceIndices;
    collectFaceCandidates(
        state.x - std::max(bodyRadius, FloorCheckSlack),
        state.y - std::max(bodyRadius, FloorCheckSlack),
        state.x + std::max(bodyRadius, FloorCheckSlack),
        state.y + std::max(bodyRadius, FloorCheckSlack),
        candidateFaceIndices);
    const FloorSample currentFloor =
        queryFloorLevel(
            *m_pOutdoorMapData,
            m_faces,
            state,
            &candidateFaceIndices,
            bodyRadius,
            FloorSelectionHeightTolerance,
            state.x,
            state.y,
            state.footZ);
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
        partyInputSpeed.z = desiredVelocityZ;

        if (flyUpRequested && !flyDownRequested)
        {
            partyInputSpeed.z += flyVerticalSpeed;
        }
        else if (flyDownRequested && !flyUpRequested)
        {
            partyInputSpeed.z -= flyVerticalSpeed;
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
        [this, deltaSeconds, &state, pContactedActorIndices, bodyRadius, bodyHeight, &ignoredActorCollider,
            &candidateFaceIndices, partyCloseToGround, flyingActive, waterWalkActive](
            bx::Vec3 &passPosition,
            bx::Vec3 &passInputSpeed,
            bool &passPartyNotOnModel)
    {
        CollisionState collisionState = {};
        collisionState.radiusLo = bodyRadius;
        collisionState.radiusHi = bodyRadius;
        collisionState.checkHi = bodyRadius * 2.0f <= bodyHeight;

        for (int attempt = 0; attempt < 5; ++attempt)
        {
            std::vector<size_t> candidateSpriteObjectIndices;
            resolveActorCylinderOverlaps(
                passPosition,
                bodyRadius,
                bodyHeight,
                m_actorColliders,
                ignoredActorCollider,
                pContactedActorIndices);
            collisionState.positionHi =
                vecAdd(passPosition, bx::Vec3{0.0f, 0.0f, bodyHeight - collisionState.radiusLo});
            collisionState.positionLo = vecAdd(passPosition, bx::Vec3{0.0f, 0.0f, collisionState.radiusLo});
            collisionState.velocity = passInputSpeed;

            if (prepareCollisionState(collisionState, deltaSeconds))
            {
                break;
            }

            collectFaceCandidates(
                collisionState.bboxMinX,
                collisionState.bboxMinY,
                collisionState.bboxMaxX,
                collisionState.bboxMaxY,
                candidateFaceIndices);
            collideOutdoorWithModels(collisionState, m_faces, &candidateFaceIndices);
            collideOutdoorWithDecorations(collisionState, m_decorationColliders);
            collideOutdoorWithActors(collisionState, m_actorColliders, ignoredActorCollider);
            collectSpriteObjectCandidates(
                collisionState.bboxMinX,
                collisionState.bboxMinY,
                collisionState.bboxMaxX,
                collisionState.bboxMaxY,
                candidateSpriteObjectIndices);
            collideOutdoorWithSpriteObjects(
                collisionState,
                m_spriteObjectColliders,
                candidateSpriteObjectIndices.empty() ? nullptr : &candidateSpriteObjectIndices);

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

            collectFaceCandidates(
                newPosLow.x - std::max(bodyRadius, FloorCheckSlack),
                newPosLow.y - std::max(bodyRadius, FloorCheckSlack),
                newPosLow.x + std::max(bodyRadius, FloorCheckSlack),
                newPosLow.y + std::max(bodyRadius, FloorCheckSlack),
                candidateFaceIndices);
            const FloorSample allNewFloor = queryFloorLevel(
                *m_pOutdoorMapData,
                m_faces,
                state,
                &candidateFaceIndices,
                bodyRadius,
                FloorSelectionHeightTolerance,
                newPosLow.x,
                newPosLow.y,
                newPosLow.z);
            collectFaceCandidates(
                newPosLow.x - std::max(bodyRadius, FloorCheckSlack),
                passPosition.y - std::max(bodyRadius, FloorCheckSlack),
                newPosLow.x + std::max(bodyRadius, FloorCheckSlack),
                passPosition.y + std::max(bodyRadius, FloorCheckSlack),
                candidateFaceIndices);
            const FloorSample xAdvanceFloor = queryFloorLevel(
                *m_pOutdoorMapData,
                m_faces,
                state,
                &candidateFaceIndices,
                bodyRadius,
                FloorSelectionHeightTolerance,
                newPosLow.x,
                passPosition.y,
                newPosLow.z);
            collectFaceCandidates(
                passPosition.x - std::max(bodyRadius, FloorCheckSlack),
                newPosLow.y - std::max(bodyRadius, FloorCheckSlack),
                passPosition.x + std::max(bodyRadius, FloorCheckSlack),
                newPosLow.y + std::max(bodyRadius, FloorCheckSlack),
                candidateFaceIndices);
            const FloorSample yAdvanceFloor = queryFloorLevel(
                *m_pOutdoorMapData,
                m_faces,
                state,
                &candidateFaceIndices,
                bodyRadius,
                FloorSelectionHeightTolerance,
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
                const bool currentOnWater =
                    isOutdoorPositionWater(*m_pOutdoorMapData, m_outdoorLandMask, passPosition.x, passPosition.y);
                const bool xAdvanceOnWater =
                    isOutdoorPositionWater(*m_pOutdoorMapData, m_outdoorLandMask, newPosLow.x, passPosition.y);
                const bool yAdvanceOnWater =
                    isOutdoorPositionWater(*m_pOutdoorMapData, m_outdoorLandMask, passPosition.x, newPosLow.y);
                const bool allowGroundedWaterEntry =
                    flyingActive || !partyCloseToGround || waterWalkActive || currentOnWater;

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

                if (!allowGroundedWaterEntry && xAdvanceOnWater)
                {
                    moveInX = false;
                }

                if (!allowGroundedWaterEntry && yAdvanceOnWater)
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

            pGeometry = findFaceGeometry(hit.bModelIndex, hit.faceIndex);

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

    collectFaceCandidates(
        partyNewPosition.x - std::max(bodyRadius, FloorCheckSlack),
        partyNewPosition.y - std::max(bodyRadius, FloorCheckSlack),
        partyNewPosition.x + std::max(bodyRadius, FloorCheckSlack),
        partyNewPosition.y + std::max(bodyRadius, FloorCheckSlack),
        candidateFaceIndices);
    const FloorSample finalFloor = queryFloorLevel(
        *m_pOutdoorMapData,
        m_faces,
        state,
        &candidateFaceIndices,
        bodyRadius,
        FloorSelectionHeightTolerance,
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

    if (flyingActive && partyNewPosition.z > maxFlightHeight)
    {
        partyNewPosition.z = maxFlightHeight;

        if (partyInputSpeed.z > 0.0f)
        {
            partyInputSpeed.z = 0.0f;
        }
    }

    OutdoorMoveState result = {};
    float clampedX = partyNewPosition.x;
    float clampedY = partyNewPosition.y;
    clampPositionToBounds(bodyRadius, clampedX, clampedY);
    result.x = clampedX;
    result.y = clampedY;
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
                && isOutdoorPositionWater(
                    *m_pOutdoorMapData,
                    m_outdoorLandMask,
                    partyNewPosition.x,
                    partyNewPosition.y)));
    result.supportOnBurning = !result.airborne
        && !finalFloor.fromBModel
        && isOutdoorTerrainBurning(*m_pOutdoorMapData, partyNewPosition.x, partyNewPosition.y);
    result.landedThisFrame = landedThisFrame;
    result.fallDistance = landedThisFrame ? fallDistance : 0.0f;
    result.fallStartZ = result.airborne ? std::max(fallStartZ, result.footZ) : result.footZ;
    return result;
}

std::optional<MapBoundaryEdge> OutdoorMovementController::detectBoundaryBlock(
    const OutdoorMoveState &previousState,
    const OutdoorMoveState &currentState,
    float desiredVelocityX,
    float desiredVelocityY) const
{
    (void)previousState;

    if (!m_mapBounds.has_value())
    {
        return std::nullopt;
    }

    constexpr float BoundEpsilon = 0.5f;
    const MapBounds &bounds = *m_mapBounds;
    const float boundaryRadius = DefaultBodyRadius;
    const bool blockedWest = currentState.x <= static_cast<float>(bounds.minX) + boundaryRadius + BoundEpsilon;
    const bool blockedEast = currentState.x >= static_cast<float>(bounds.maxX) - boundaryRadius - BoundEpsilon;
    const bool blockedSouth = currentState.y <= static_cast<float>(bounds.minY) + boundaryRadius + BoundEpsilon;
    const bool blockedNorth = currentState.y >= static_cast<float>(bounds.maxY) - boundaryRadius - BoundEpsilon;

    if (desiredVelocityX < 0.0f && blockedWest)
    {
        return MapBoundaryEdge::West;
    }

    if (desiredVelocityX > 0.0f && blockedEast)
    {
        return MapBoundaryEdge::East;
    }

    if (desiredVelocityY < 0.0f && blockedSouth)
    {
        return MapBoundaryEdge::South;
    }

    if (desiredVelocityY > 0.0f && blockedNorth)
    {
        return MapBoundaryEdge::North;
    }

    return std::nullopt;
}

OutdoorMoveState OutdoorMovementController::resolveOutdoorActorMove(
    const OutdoorMoveState &state,
    const OutdoorBodyDimensions &body,
    float desiredVelocityX,
    float desiredVelocityY,
    float verticalVelocity,
    bool flyingActive,
    float deltaSeconds,
    std::vector<size_t> *pContactedActorIndices,
    const std::optional<OutdoorIgnoredActorCollider> &ignoredActorCollider
) const
{
    const float bodyRadius = std::max(1.0f, body.radius);
    const float bodyHeight = std::max(bodyRadius * 2.0f + 2.0f, body.height);
    const float maxStepHeight = 128.0f;
    std::vector<size_t> candidateFaceIndices;
    collectFaceCandidates(
        state.x - std::max(bodyRadius, FloorCheckSlack),
        state.y - std::max(bodyRadius, FloorCheckSlack),
        state.x + std::max(bodyRadius, FloorCheckSlack),
        state.y + std::max(bodyRadius, FloorCheckSlack),
        candidateFaceIndices);
    const FloorSample currentFloor = queryFloorLevel(
        *m_pOutdoorMapData,
        m_faces,
        state,
        &candidateFaceIndices,
        bodyRadius,
        maxStepHeight,
        state.x,
        state.y,
        state.footZ);
    const float currentGroundLevel = currentFloor.height + GroundSnapHeight;
    bool actorGrounded = state.footZ <= currentGroundLevel + CloseToGroundHeight;
    bx::Vec3 actorPosition = {state.x, state.y, state.footZ};
    bx::Vec3 actorVelocity = {desiredVelocityX, desiredVelocityY, verticalVelocity};

    const auto settleActorToGround =
        [&](const FloorSample &floor)
    {
        const float groundLevel = floor.height + GroundSnapHeight;

        if (actorPosition.z < groundLevel)
        {
            actorPosition.z = groundLevel;
            actorVelocity.z = 0.0f;
            actorGrounded = true;
            return;
        }

        if (!flyingActive && actorGrounded)
        {
            const float dropToGround = actorPosition.z - groundLevel;

            if (dropToGround > 0.0f && dropToGround <= maxStepHeight)
            {
                actorPosition.z = groundLevel;

                if (actorVelocity.z < 0.0f)
                {
                    actorVelocity.z = 0.0f;
                }
            }
        }

        actorGrounded = actorPosition.z <= groundLevel + CloseToGroundHeight;
    };

    settleActorToGround(currentFloor);

    if (!flyingActive && actorPosition.z > currentGroundLevel + GroundSnapHeight)
    {
        actorVelocity.z -= GravityPerSecond * deltaSeconds;
        actorGrounded = false;
    }

    CollisionState collisionState = {};
    collisionState.radiusLo = bodyRadius;
    collisionState.radiusHi = bodyRadius;
    collisionState.checkHi = bodyRadius * 2.0f <= bodyHeight;

    for (int attempt = 0; attempt < 100; ++attempt)
    {
        std::vector<size_t> candidateSpriteObjectIndices;
        resolveActorCylinderOverlaps(
            actorPosition,
            bodyRadius,
            bodyHeight,
            m_actorColliders,
            ignoredActorCollider,
            pContactedActorIndices);
        collisionState.positionLo = vecAdd(actorPosition, bx::Vec3{0.0f, 0.0f, bodyRadius + 1.0f});
        collisionState.positionHi = vecAdd(actorPosition, bx::Vec3{0.0f, 0.0f, bodyHeight - bodyRadius - 1.0f});
        collisionState.positionHi.z = std::max(collisionState.positionHi.z, collisionState.positionLo.z);
        collisionState.velocity = actorVelocity;

        if (prepareCollisionState(collisionState, deltaSeconds))
        {
            break;
        }

        collectFaceCandidates(
            collisionState.bboxMinX,
            collisionState.bboxMinY,
            collisionState.bboxMaxX,
            collisionState.bboxMaxY,
            candidateFaceIndices);
        collideOutdoorWithModels(collisionState, m_faces, &candidateFaceIndices);
        collideOutdoorWithDecorations(collisionState, m_decorationColliders);
        collideOutdoorWithActors(collisionState, m_actorColliders, ignoredActorCollider);
        collectSpriteObjectCandidates(
            collisionState.bboxMinX,
            collisionState.bboxMinY,
            collisionState.bboxMaxX,
            collisionState.bboxMaxY,
            candidateSpriteObjectIndices);
        collideOutdoorWithSpriteObjects(
            collisionState,
            m_spriteObjectColliders,
            candidateSpriteObjectIndices.empty() ? nullptr : &candidateSpriteObjectIndices);

        actorPosition = vecAdd(actorPosition, vecScale(collisionState.direction, collisionState.adjustedMoveDistance));
        collectFaceCandidates(
            actorPosition.x - std::max(bodyRadius, FloorCheckSlack),
            actorPosition.y - std::max(bodyRadius, FloorCheckSlack),
            actorPosition.x + std::max(bodyRadius, FloorCheckSlack),
            actorPosition.y + std::max(bodyRadius, FloorCheckSlack),
            candidateFaceIndices);
        const FloorSample newFloor = queryFloorLevel(
            *m_pOutdoorMapData,
            m_faces,
            state,
            &candidateFaceIndices,
            bodyRadius,
            maxStepHeight,
            actorPosition.x,
            actorPosition.y,
            actorPosition.z);
        settleActorToGround(newFloor);

        if (collisionState.adjustedMoveDistance >= collisionState.moveDistance)
        {
            break;
        }

        collisionState.totalMoveDistance += collisionState.adjustedMoveDistance;

        if (!collisionState.hit)
        {
            actorVelocity = vecScale(actorVelocity, 0.89263916f);
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
                    actorVelocity = vecScale(actorVelocity, 0.89263916f);
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
                    actorVelocity = vecScale(actorVelocity, 0.89263916f);
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
                    actorVelocity = vecScale(actorVelocity, 0.89263916f);
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
                actorVelocity = vecScale(actorVelocity, 0.89263916f);
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
            actorVelocity = vecScale(newDirection, vecDot(newDirection, actorVelocity));
            actorVelocity = vecScale(actorVelocity, 0.89263916f);
            continue;
        }

        const OutdoorFaceGeometryData *pGeometry = nullptr;

        pGeometry = findFaceGeometry(hit.bModelIndex, hit.faceIndex);

        if (pGeometry == nullptr)
        {
            actorVelocity = vecScale(actorVelocity, 0.89263916f);
            continue;
        }

        if (pGeometry->polygonType == PolygonFloor)
        {
            if (actorVelocity.z < 0.0f)
            {
                actorVelocity.z = 0.0f;
            }

            actorPosition.z = std::max(actorPosition.z, hit.floorHeight + GroundSnapHeight);

            if (vecDot(actorVelocity, actorVelocity) < 400.0f)
            {
                actorVelocity.x = 0.0f;
                actorVelocity.y = 0.0f;
            }
        }
        else
        {
            float velocityDotNormal = vecDot(pGeometry->normal, actorVelocity);
            velocityDotNormal = std::max(std::abs(velocityDotNormal), collisionState.speed / 8.0f);
            actorVelocity = vecAdd(actorVelocity, vecScale(pGeometry->normal, velocityDotNormal));

            if (pGeometry->polygonType != PolygonInBetweenFloorAndWall)
            {
                const float overshoot = bodyRadius - faceSignedDistance(*pGeometry, actorPosition);

                if (overshoot > 0.0f)
                {
                    actorPosition = vecAdd(actorPosition, vecScale(pGeometry->normal, overshoot));
                }
            }
        }

        actorVelocity = vecScale(actorVelocity, 0.89263916f);
    }

    collectFaceCandidates(
        actorPosition.x - std::max(bodyRadius, FloorCheckSlack),
        actorPosition.y - std::max(bodyRadius, FloorCheckSlack),
        actorPosition.x + std::max(bodyRadius, FloorCheckSlack),
        actorPosition.y + std::max(bodyRadius, FloorCheckSlack),
        candidateFaceIndices);
    const FloorSample finalFloor = queryFloorLevel(
        *m_pOutdoorMapData,
        m_faces,
        state,
        &candidateFaceIndices,
        bodyRadius,
        maxStepHeight,
        actorPosition.x,
        actorPosition.y,
        actorPosition.z);
    settleActorToGround(finalFloor);
    const float finalGroundLevel = finalFloor.height + GroundSnapHeight;

    OutdoorMoveState result = {};
    result.x = actorPosition.x;
    result.y = actorPosition.y;
    result.footZ = actorPosition.z;
    result.verticalVelocity = actorVelocity.z;
    result.supportKind = finalFloor.fromBModel ? OutdoorSupportKind::BModelFace : OutdoorSupportKind::Terrain;
    result.supportBModelIndex = finalFloor.bModelIndex;
    result.supportFaceIndex = finalFloor.faceIndex;
    result.supportIsFluid = finalFloor.isFluid;
    result.supportOnWater = finalFloor.isFluid;
    result.supportOnBurning = finalFloor.isBurning;
    result.airborne = flyingActive && actorPosition.z > finalGroundLevel + GroundSnapHeight;
    result.landedThisFrame = false;
    result.fallStartZ = result.footZ;
    result.fallDistance = 0.0f;
    return result;
}

void OutdoorMovementController::setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders)
{
    m_actorColliders = actorColliders;
}

void OutdoorMovementController::clampPositionToBounds(float bodyRadius, float &x, float &y) const
{
    if (!m_mapBounds.has_value())
    {
        return;
    }

    const MapBounds &bounds = *m_mapBounds;
    const float radius = std::max(0.0f, bodyRadius);
    const float minX = static_cast<float>(bounds.minX) + radius;
    const float maxX = static_cast<float>(bounds.maxX) - radius;
    const float minY = static_cast<float>(bounds.minY) + radius;
    const float maxY = static_cast<float>(bounds.maxY) - radius;

    x = std::clamp(x, minX, maxX);
    y = std::clamp(y, minY, maxY);
}

void OutdoorMovementController::buildFaceCache()
{
    m_faces.clear();
    m_faceIndexById.clear();

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

            m_faces.push_back(std::move(geometry));
            const uint64_t faceId =
                (static_cast<uint64_t>(bModelIndex) << 32) | static_cast<uint32_t>(faceIndex);
            m_faceIndexById[faceId] = m_faces.size() - 1;
        }
    }

    buildFaceSpatialIndex();
}

void OutdoorMovementController::buildFaceSpatialIndex()
{
    m_faceGridCells.clear();
    m_faceGridVisitMarks.clear();
    m_faceGridVisitGeneration = 1;
    m_faceGridMinX = 0.0f;
    m_faceGridMinY = 0.0f;
    m_faceGridWidth = 0;
    m_faceGridHeight = 0;

    if (m_faces.empty())
    {
        return;
    }

    float minX = m_faces.front().minX;
    float minY = m_faces.front().minY;
    float maxX = m_faces.front().maxX;
    float maxY = m_faces.front().maxY;

    for (const OutdoorFaceGeometryData &face : m_faces)
    {
        minX = std::min(minX, face.minX);
        minY = std::min(minY, face.minY);
        maxX = std::max(maxX, face.maxX);
        maxY = std::max(maxY, face.maxY);
    }

    m_faceGridMinX = minX;
    m_faceGridMinY = minY;
    m_faceGridWidth = std::max<size_t>(1, static_cast<size_t>(std::floor((maxX - minX) / FaceGridCellSize)) + 1);
    m_faceGridHeight = std::max<size_t>(1, static_cast<size_t>(std::floor((maxY - minY) / FaceGridCellSize)) + 1);
    m_faceGridCells.assign(m_faceGridWidth * m_faceGridHeight, {});
    m_faceGridVisitMarks.assign(m_faces.size(), 0);
    const auto clampCellX =
        [this](float x)
    {
        const int cell = static_cast<int>(std::floor((x - m_faceGridMinX) / FaceGridCellSize));
        return static_cast<size_t>(std::clamp(cell, 0, static_cast<int>(m_faceGridWidth) - 1));
    };
    const auto clampCellY =
        [this](float y)
    {
        const int cell = static_cast<int>(std::floor((y - m_faceGridMinY) / FaceGridCellSize));
        return static_cast<size_t>(std::clamp(cell, 0, static_cast<int>(m_faceGridHeight) - 1));
    };

    for (size_t faceIndex = 0; faceIndex < m_faces.size(); ++faceIndex)
    {
        const OutdoorFaceGeometryData &face = m_faces[faceIndex];
        const size_t minCellX = clampCellX(face.minX);
        const size_t maxCellX = clampCellX(face.maxX);
        const size_t minCellY = clampCellY(face.minY);
        const size_t maxCellY = clampCellY(face.maxY);

        for (size_t cellY = minCellY; cellY <= maxCellY; ++cellY)
        {
            for (size_t cellX = minCellX; cellX <= maxCellX; ++cellX)
            {
                m_faceGridCells[cellY * m_faceGridWidth + cellX].push_back(faceIndex);
            }
        }
    }
}

void OutdoorMovementController::collectFaceCandidates(
    float minX,
    float minY,
    float maxX,
    float maxY,
    std::vector<size_t> &faceIndices) const
{
    faceIndices.clear();

    if (m_faces.empty())
    {
        return;
    }

    if (m_faceGridCells.empty() || m_faceGridWidth == 0 || m_faceGridHeight == 0)
    {
        faceIndices.reserve(m_faces.size());

        for (size_t faceIndex = 0; faceIndex < m_faces.size(); ++faceIndex)
        {
            faceIndices.push_back(faceIndex);
        }

        return;
    }

    if (m_faceGridVisitMarks.size() != m_faces.size())
    {
        m_faceGridVisitMarks.assign(m_faces.size(), 0);
        m_faceGridVisitGeneration = 1;
    }

    ++m_faceGridVisitGeneration;

    if (m_faceGridVisitGeneration == 0)
    {
        std::fill(m_faceGridVisitMarks.begin(), m_faceGridVisitMarks.end(), 0);
        m_faceGridVisitGeneration = 1;
    }

    const float clampedMinX = std::min(minX, maxX);
    const float clampedMinY = std::min(minY, maxY);
    const float clampedMaxX = std::max(minX, maxX);
    const float clampedMaxY = std::max(minY, maxY);
    const int minCellX = std::clamp(
        static_cast<int>(std::floor((clampedMinX - m_faceGridMinX) / FaceGridCellSize)),
        0,
        static_cast<int>(m_faceGridWidth) - 1);
    const int maxCellX = std::clamp(
        static_cast<int>(std::floor((clampedMaxX - m_faceGridMinX) / FaceGridCellSize)),
        0,
        static_cast<int>(m_faceGridWidth) - 1);
    const int minCellY = std::clamp(
        static_cast<int>(std::floor((clampedMinY - m_faceGridMinY) / FaceGridCellSize)),
        0,
        static_cast<int>(m_faceGridHeight) - 1);
    const int maxCellY = std::clamp(
        static_cast<int>(std::floor((clampedMaxY - m_faceGridMinY) / FaceGridCellSize)),
        0,
        static_cast<int>(m_faceGridHeight) - 1);

    for (int cellY = minCellY; cellY <= maxCellY; ++cellY)
    {
        for (int cellX = minCellX; cellX <= maxCellX; ++cellX)
        {
            const size_t gridIndex = static_cast<size_t>(cellY) * m_faceGridWidth + static_cast<size_t>(cellX);
            const std::vector<size_t> &cellFaceIndices = m_faceGridCells[gridIndex];

            for (size_t faceIndex : cellFaceIndices)
            {
                if (faceIndex >= m_faceGridVisitMarks.size())
                {
                    continue;
                }

                if (m_faceGridVisitMarks[faceIndex] == m_faceGridVisitGeneration)
                {
                    continue;
                }

                m_faceGridVisitMarks[faceIndex] = m_faceGridVisitGeneration;
                faceIndices.push_back(faceIndex);
            }
        }
    }
}

const OutdoorFaceGeometryData *OutdoorMovementController::findFaceGeometry(size_t bModelIndex, size_t faceIndex) const
{
    const uint64_t faceId =
        (static_cast<uint64_t>(bModelIndex) << 32) | static_cast<uint32_t>(faceIndex);
    const auto iterator = m_faceIndexById.find(faceId);

    if (iterator == m_faceIndexById.end() || iterator->second >= m_faces.size())
    {
        return nullptr;
    }

    return &m_faces[iterator->second];
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
    m_spriteObjectGridCells.clear();
    m_spriteObjectGridMinX = 0.0f;
    m_spriteObjectGridMinY = 0.0f;
    m_spriteObjectGridWidth = 0;
    m_spriteObjectGridHeight = 0;

    if (!outdoorSpriteObjectSet)
    {
        return;
    }

    m_spriteObjectColliders.reserve(outdoorSpriteObjectSet->colliders.size());

    for (const OutdoorSpriteObjectCollision &collision : outdoorSpriteObjectSet->colliders)
    {
        m_spriteObjectColliders.push_back(collision);
    }

    if (m_spriteObjectColliders.empty())
    {
        return;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();

    for (const OutdoorSpriteObjectCollision &collision : m_spriteObjectColliders)
    {
        minX = std::min(minX, static_cast<float>(collision.worldX));
        minY = std::min(minY, static_cast<float>(collision.worldY));
        maxX = std::max(maxX, static_cast<float>(collision.worldX));
        maxY = std::max(maxY, static_cast<float>(collision.worldY));
    }

    m_spriteObjectGridMinX = minX;
    m_spriteObjectGridMinY = minY;
    m_spriteObjectGridWidth = static_cast<size_t>(std::floor((maxX - minX) / FaceGridCellSize)) + 1;
    m_spriteObjectGridHeight = static_cast<size_t>(std::floor((maxY - minY) / FaceGridCellSize)) + 1;
    m_spriteObjectGridCells.assign(m_spriteObjectGridWidth * m_spriteObjectGridHeight, {});

    for (size_t objectIndex = 0; objectIndex < m_spriteObjectColliders.size(); ++objectIndex)
    {
        const OutdoorSpriteObjectCollision &collision = m_spriteObjectColliders[objectIndex];
        const size_t cellX = std::min(
            static_cast<size_t>(std::max(
                0.0f,
                std::floor((static_cast<float>(collision.worldX) - minX) / FaceGridCellSize))),
            m_spriteObjectGridWidth - 1);
        const size_t cellY = std::min(
            static_cast<size_t>(std::max(
                0.0f,
                std::floor((static_cast<float>(collision.worldY) - minY) / FaceGridCellSize))),
            m_spriteObjectGridHeight - 1);
        m_spriteObjectGridCells[cellY * m_spriteObjectGridWidth + cellX].push_back(objectIndex);
    }
}

void OutdoorMovementController::collectSpriteObjectCandidates(
    float minX,
    float minY,
    float maxX,
    float maxY,
    std::vector<size_t> &indices) const
{
    indices.clear();

    if (m_spriteObjectGridCells.empty() || m_spriteObjectGridWidth == 0 || m_spriteObjectGridHeight == 0)
    {
        return;
    }

    const int startCellX = std::clamp(
        static_cast<int>(std::floor((minX - m_spriteObjectGridMinX) / FaceGridCellSize)),
        0,
        static_cast<int>(m_spriteObjectGridWidth) - 1);
    const int endCellX = std::clamp(
        static_cast<int>(std::floor((maxX - m_spriteObjectGridMinX) / FaceGridCellSize)),
        0,
        static_cast<int>(m_spriteObjectGridWidth) - 1);
    const int startCellY = std::clamp(
        static_cast<int>(std::floor((minY - m_spriteObjectGridMinY) / FaceGridCellSize)),
        0,
        static_cast<int>(m_spriteObjectGridHeight) - 1);
    const int endCellY = std::clamp(
        static_cast<int>(std::floor((maxY - m_spriteObjectGridMinY) / FaceGridCellSize)),
        0,
        static_cast<int>(m_spriteObjectGridHeight) - 1);

    for (int cellY = startCellY; cellY <= endCellY; ++cellY)
    {
        for (int cellX = startCellX; cellX <= endCellX; ++cellX)
        {
            const std::vector<size_t> &cell =
                m_spriteObjectGridCells[static_cast<size_t>(cellY) * m_spriteObjectGridWidth
                    + static_cast<size_t>(cellX)];
            indices.insert(indices.end(), cell.begin(), cell.end());
        }
    }
}
}
