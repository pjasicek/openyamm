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
constexpr float GravityPerSecond = 10000.0f;
constexpr uint8_t PolygonFloor = 0x3;
constexpr uint8_t PolygonInBetweenFloorAndWall = 0x4;

struct FloorSample
{
    bool hasFloor = false;
    float height = 0.0f;
    float normalZ = 1.0f;
    bool fromBModel = false;
    size_t bModelIndex = 0;
    size_t faceIndex = 0;
};

struct CollisionHit
{
    size_t bModelIndex = 0;
    size_t faceIndex = 0;
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
            geometry.bModelIndex,
            geometry.faceIndex,
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

FloorSample queryFloorLevel(
    const OutdoorMapData &outdoorMapData,
    const std::vector<OutdoorFaceGeometryData> &faces,
    float x,
    float y,
    float z)
{
    const FloorSample terrainSample = {
        true,
        sampleOutdoorTerrainHeight(outdoorMapData, x, y),
        sampleOutdoorTerrainNormalZ(outdoorMapData, x, y),
        false,
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
            geometry.bModelIndex,
            geometry.faceIndex
        });
    }

    return chooseBestFloorSample(terrainSample, samples, z);
}

}

OutdoorMovementController::OutdoorMovementController(const OutdoorMapData &outdoorMapData)
    : m_pOutdoorMapData(&outdoorMapData)
{
    buildFaceCache();
}

OutdoorMoveState OutdoorMovementController::initializeState(float x, float y, float footZHint) const
{
    const FloorSample floor = queryFloorLevel(*m_pOutdoorMapData, m_faces, x, y, footZHint);
    return {x, y, floor.height + GroundSnapHeight, 0.0f};
}

OutdoorMoveState OutdoorMovementController::resolveMove(
    const OutdoorMoveState &state,
    float desiredVelocityX,
    float desiredVelocityY,
    float deltaSeconds
) const
{
    const FloorSample currentFloor = queryFloorLevel(*m_pOutdoorMapData, m_faces, state.x, state.y, state.footZ);
    const float currentGroundLevel = currentFloor.height + GroundSnapHeight;
    const bool partyAtHighSlope = !currentFloor.fromBModel && terrainSlopeTooHigh(*m_pOutdoorMapData, state.x, state.y);
    bool partyNotOnModel = !currentFloor.fromBModel;
    bool partyNotTouchingFloor = state.footZ > currentGroundLevel + GroundSnapHeight;

    bx::Vec3 partyNewPosition = {state.x, state.y, state.footZ};
    bx::Vec3 partyInputSpeed = {desiredVelocityX, desiredVelocityY, state.verticalVelocity};

    if (partyNewPosition.z < currentGroundLevel)
    {
        partyNewPosition.z = currentGroundLevel;
        partyInputSpeed.z = 0.0f;
    }

    if (partyNotTouchingFloor)
    {
        partyInputSpeed.z -= GravityPerSecond * deltaSeconds;
    }
    else if (!currentFloor.fromBModel && partyAtHighSlope)
    {
        partyNewPosition.z = currentGroundLevel;
    }

    const auto runCollisionPass =
        [this, deltaSeconds](
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
                newPosLow.x,
                newPosLow.y,
                newPosLow.z);
            const FloorSample xAdvanceFloor = queryFloorLevel(
                *m_pOutdoorMapData,
                m_faces,
                newPosLow.x,
                passPosition.y,
                newPosLow.z);
            const FloorSample yAdvanceFloor = queryFloorLevel(
                *m_pOutdoorMapData,
                m_faces,
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
        partyNewPosition.x,
        partyNewPosition.y,
        partyNewPosition.z);
    const float finalGroundLevel = finalFloor.height + GroundSnapHeight;

    if (partyNewPosition.z <= finalGroundLevel)
    {
        partyNewPosition.z = finalGroundLevel;
        partyInputSpeed.z = 0.0f;
    }

    return {partyNewPosition.x, partyNewPosition.y, partyNewPosition.z, partyInputSpeed.z};
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
}
