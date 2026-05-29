#include "game/mm9/Mm9DatWorldRuntime.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <limits>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float DefaultFloorPlacementMaxDrop = 10000.0f;
constexpr float DefaultFloorPlacementBias = 0.1f;
constexpr float DefaultMechanismDurationSeconds = 1.0f;
constexpr float MinimumMechanismDurationSeconds = 0.01f;
constexpr float DefaultObjectPickCellSize = 512.0f;
constexpr float DefaultMechanismBoundsCellSize = 512.0f;
constexpr float PickEpsilon = 0.0001f;
constexpr size_t InvalidRuntimeIndex = static_cast<size_t>(-1);

Mm9DatVec3 vertexPosition(const Mm9DatRenderVertex &vertex)
{
    return {
        vertex.x,
        vertex.y,
        vertex.z,
    };
}

void includePoint(Mm9DatRenderBounds &bounds, const Mm9DatVec3 &point)
{
    if (!bounds.valid)
    {
        bounds.min = point;
        bounds.max = point;
        bounds.center = point;
        bounds.radius = 0.0f;
        bounds.valid = true;
        return;
    }

    bounds.min.x = std::min(bounds.min.x, point.x);
    bounds.min.y = std::min(bounds.min.y, point.y);
    bounds.min.z = std::min(bounds.min.z, point.z);
    bounds.max.x = std::max(bounds.max.x, point.x);
    bounds.max.y = std::max(bounds.max.y, point.y);
    bounds.max.z = std::max(bounds.max.z, point.z);
}

float distance(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    const float dx = left.x - right.x;
    const float dy = left.y - right.y;
    const float dz = left.z - right.z;
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

Mm9DatVec3 addVec3(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.x + right.x,
        left.y + right.y,
        left.z + right.z,
    };
}

Mm9DatVec3 subtractVec3(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.x - right.x,
        left.y - right.y,
        left.z - right.z,
    };
}

Mm9DatVec3 multiplyVec3(const Mm9DatVec3 &value, float scalar)
{
    return {
        value.x * scalar,
        value.y * scalar,
        value.z * scalar,
    };
}

float dotVec3(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

Mm9DatVec3 normalizedOrZero(const Mm9DatVec3 &value)
{
    const float valueLength = std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
    if (valueLength <= 0.0001f)
    {
        return {};
    }

    return multiplyVec3(value, 1.0f / valueLength);
}

Mm9DatVec3 crossVec3(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x,
    };
}

int32_t floorCell(float value, float cellSize)
{
    return static_cast<int32_t>(std::floor(value / cellSize));
}

int64_t horizontalCellKey(int32_t x, int32_t z)
{
    const uint64_t xBits = static_cast<uint32_t>(x);
    const uint64_t zBits = static_cast<uint32_t>(z);
    return static_cast<int64_t>((xBits << 32) | zBits);
}

Mm9DatVec3 collisionPlaneNormalForDisplacement(
    const Mm9DatVec3 &displacement,
    const Mm9DatVec3 &normal)
{
    if (dotVec3(displacement, normal) > 0.0f)
    {
        return multiplyVec3(normal, -1.0f);
    }

    return normal;
}

std::vector<size_t> objectCandidatesForRay(
    const Mm9DatObjectRegistry &registry,
    const Mm9DatPickRay &ray,
    float maxDistance)
{
    std::vector<size_t> result;
    std::unordered_set<size_t> seenObjectIndices;

    if (maxDistance <= PickEpsilon || registry.pickableObjectIndicesByCell.empty())
    {
        return result;
    }

    const float cellSize =
        registry.pickableObjectCellSize > PickEpsilon
            ? registry.pickableObjectCellSize
            : DefaultObjectPickCellSize;
    const Mm9DatVec3 end = addVec3(ray.origin, multiplyVec3(ray.direction, maxDistance));
    const int32_t minCellX = floorCell(std::min(ray.origin.x, end.x), cellSize);
    const int32_t maxCellX = floorCell(std::max(ray.origin.x, end.x), cellSize);
    const int32_t minCellZ = floorCell(std::min(ray.origin.z, end.z), cellSize);
    const int32_t maxCellZ = floorCell(std::max(ray.origin.z, end.z), cellSize);

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
        {
            const auto cellIterator =
                registry.pickableObjectIndicesByCell.find(horizontalCellKey(cellX, cellZ));
            if (cellIterator == registry.pickableObjectIndicesByCell.end())
            {
                continue;
            }

            for (size_t objectIndex : cellIterator->second)
            {
                if (seenObjectIndices.insert(objectIndex).second)
                {
                    result.push_back(objectIndex);
                }
            }
        }
    }

    return result;
}

std::vector<size_t> collidableObjectCandidatesForRay(
    const Mm9DatObjectRegistry &registry,
    const Mm9DatPickRay &ray,
    float maxDistance)
{
    std::vector<size_t> result;
    std::unordered_set<size_t> seenObjectIndices;

    if (maxDistance <= PickEpsilon || registry.collidableObjectIndicesByCell.empty())
    {
        return result;
    }

    const float cellSize =
        registry.collidableObjectCellSize > PickEpsilon
            ? registry.collidableObjectCellSize
            : DefaultObjectPickCellSize;
    const Mm9DatVec3 end = addVec3(ray.origin, multiplyVec3(ray.direction, maxDistance));
    const int32_t minCellX = floorCell(std::min(ray.origin.x, end.x), cellSize);
    const int32_t maxCellX = floorCell(std::max(ray.origin.x, end.x), cellSize);
    const int32_t minCellZ = floorCell(std::min(ray.origin.z, end.z), cellSize);
    const int32_t maxCellZ = floorCell(std::max(ray.origin.z, end.z), cellSize);

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
        {
            const auto cellIterator =
                registry.collidableObjectIndicesByCell.find(horizontalCellKey(cellX, cellZ));
            if (cellIterator == registry.collidableObjectIndicesByCell.end())
            {
                continue;
            }

            for (size_t objectIndex : cellIterator->second)
            {
                if (seenObjectIndices.insert(objectIndex).second)
                {
                    result.push_back(objectIndex);
                }
            }
        }
    }

    return result;
}

std::vector<int64_t> boundsCellKeys(const Mm9DatRenderBounds &bounds, float cellSize)
{
    std::vector<int64_t> result;

    if (!bounds.valid || cellSize <= PickEpsilon)
    {
        return result;
    }

    const int32_t minCellX = floorCell(bounds.min.x, cellSize);
    const int32_t maxCellX = floorCell(bounds.max.x, cellSize);
    const int32_t minCellZ = floorCell(bounds.min.z, cellSize);
    const int32_t maxCellZ = floorCell(bounds.max.z, cellSize);
    result.reserve(
        static_cast<size_t>(std::max(0, maxCellX - minCellX + 1))
        * static_cast<size_t>(std::max(0, maxCellZ - minCellZ + 1)));

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
        {
            result.push_back(horizontalCellKey(cellX, cellZ));
        }
    }

    return result;
}

void recomputeMechanismBoundsIndexStats(Mm9DatMechanismBoundsIndex &index)
{
    index.stats = {};
    index.stats.cellSize = index.cellSize;
    index.stats.mechanismCount = index.cellKeysByMechanismIndex.size();
    index.stats.cellCount = index.mechanismIndicesByCell.size();

    for (const std::vector<int64_t> &cellKeys : index.cellKeysByMechanismIndex)
    {
        if (!cellKeys.empty())
        {
            ++index.stats.indexedMechanismCount;
            index.stats.mechanismCellRefs += cellKeys.size();
        }
    }

    for (const auto &cellEntry : index.mechanismIndicesByCell)
    {
        index.stats.maxCellMechanismRefs =
            std::max(index.stats.maxCellMechanismRefs, cellEntry.second.size());
    }
}

void removeMechanismFromBoundsIndexCells(
    Mm9DatMechanismBoundsIndex &index,
    size_t mechanismIndex)
{
    if (mechanismIndex >= index.cellKeysByMechanismIndex.size())
    {
        return;
    }

    for (int64_t cellKey : index.cellKeysByMechanismIndex[mechanismIndex])
    {
        auto cellIterator = index.mechanismIndicesByCell.find(cellKey);
        if (cellIterator == index.mechanismIndicesByCell.end())
        {
            continue;
        }

        std::vector<size_t> &cellMechanisms = cellIterator->second;
        cellMechanisms.erase(
            std::remove(cellMechanisms.begin(), cellMechanisms.end(), mechanismIndex),
            cellMechanisms.end());

        if (cellMechanisms.empty())
        {
            index.mechanismIndicesByCell.erase(cellIterator);
        }
    }

    index.cellKeysByMechanismIndex[mechanismIndex].clear();
}

void addMechanismToBoundsIndexCells(
    Mm9DatMechanismBoundsIndex &index,
    const Mm9DatMechanismRuntime &runtime,
    size_t mechanismIndex)
{
    if (mechanismIndex >= runtime.mechanisms.size())
    {
        return;
    }

    if (mechanismIndex >= index.cellKeysByMechanismIndex.size())
    {
        index.cellKeysByMechanismIndex.resize(mechanismIndex + 1);
    }

    const Mm9DatMechanismInstance &mechanism = runtime.mechanisms[mechanismIndex];
    if (!mechanism.active || mechanism.inert || !mechanism.currentBounds.valid)
    {
        return;
    }

    std::vector<int64_t> cellKeys = boundsCellKeys(mechanism.currentBounds, index.cellSize);
    for (int64_t cellKey : cellKeys)
    {
        index.mechanismIndicesByCell[cellKey].push_back(mechanismIndex);
    }

    index.cellKeysByMechanismIndex[mechanismIndex] = std::move(cellKeys);
}

std::vector<size_t> mechanismCandidatesForRay(
    const Mm9DatMechanismBoundsIndex &index,
    const Mm9DatPickRay &ray,
    float maxDistance)
{
    std::vector<size_t> result;
    std::unordered_set<size_t> seenMechanismIndices;

    if (maxDistance <= PickEpsilon || index.mechanismIndicesByCell.empty())
    {
        return result;
    }

    const float cellSize =
        index.cellSize > PickEpsilon
            ? index.cellSize
            : DefaultMechanismBoundsCellSize;
    const Mm9DatVec3 end = addVec3(ray.origin, multiplyVec3(ray.direction, maxDistance));
    const int32_t minCellX = floorCell(std::min(ray.origin.x, end.x), cellSize);
    const int32_t maxCellX = floorCell(std::max(ray.origin.x, end.x), cellSize);
    const int32_t minCellZ = floorCell(std::min(ray.origin.z, end.z), cellSize);
    const int32_t maxCellZ = floorCell(std::max(ray.origin.z, end.z), cellSize);

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
        {
            const auto cellIterator =
                index.mechanismIndicesByCell.find(horizontalCellKey(cellX, cellZ));
            if (cellIterator == index.mechanismIndicesByCell.end())
            {
                continue;
            }

            for (size_t mechanismIndex : cellIterator->second)
            {
                if (seenMechanismIndices.insert(mechanismIndex).second)
                {
                    result.push_back(mechanismIndex);
                }
            }
        }
    }

    return result;
}

struct RayObjectIntersection
{
    float distance = 0.0f;
    Mm9DatVec3 point;
    Mm9DatVec3 normal;
};

std::optional<RayObjectIntersection> intersectRayObjectBounds(
    const Mm9DatPickRay &ray,
    const Mm9DatRuntimeObject &object,
    float maxDistance)
{
    if (maxDistance <= PickEpsilon || object.radius <= PickEpsilon)
    {
        return std::nullopt;
    }

    const Mm9DatVec3 objectCenter = {
        object.position.x,
        object.position.y + std::max(0.0f, object.height * 0.5f),
        object.position.z,
    };
    const Mm9DatVec3 relativeOrigin = subtractVec3(ray.origin, objectCenter);
    const float a = dotVec3(ray.direction, ray.direction);
    const float b = 2.0f * dotVec3(relativeOrigin, ray.direction);
    const float c = dotVec3(relativeOrigin, relativeOrigin) - object.radius * object.radius;
    const float discriminant = b * b - 4.0f * a * c;

    if (a <= PickEpsilon || discriminant < 0.0f)
    {
        return std::nullopt;
    }

    const float sqrtDiscriminant = std::sqrt(discriminant);
    const float firstDistance = (-b - sqrtDiscriminant) / (2.0f * a);
    const float secondDistance = (-b + sqrtDiscriminant) / (2.0f * a);
    const float distance =
        firstDistance >= 0.0f
            ? firstDistance
            : secondDistance;

    if (distance < 0.0f || distance > maxDistance + PickEpsilon)
    {
        return std::nullopt;
    }

    RayObjectIntersection intersection = {};
    intersection.distance = distance;
    intersection.point = addVec3(ray.origin, multiplyVec3(ray.direction, distance));
    intersection.normal = normalizedOrZero(subtractVec3(intersection.point, objectCenter));
    return intersection;
}

std::optional<float> intersectRayBounds(
    const Mm9DatPickRay &ray,
    const Mm9DatRenderBounds &bounds,
    float maxDistance)
{
    if (!bounds.valid || maxDistance <= PickEpsilon)
    {
        return std::nullopt;
    }

    float nearDistance = 0.0f;
    float farDistance = maxDistance;

    const std::array<float, 3> origin = {{ray.origin.x, ray.origin.y, ray.origin.z}};
    const std::array<float, 3> direction = {{ray.direction.x, ray.direction.y, ray.direction.z}};
    const std::array<float, 3> minBounds = {{bounds.min.x, bounds.min.y, bounds.min.z}};
    const std::array<float, 3> maxBounds = {{bounds.max.x, bounds.max.y, bounds.max.z}};

    for (size_t axis = 0; axis < 3; ++axis)
    {
        if (std::fabs(direction[axis]) <= PickEpsilon)
        {
            if (origin[axis] < minBounds[axis] || origin[axis] > maxBounds[axis])
            {
                return std::nullopt;
            }

            continue;
        }

        const float inverseDirection = 1.0f / direction[axis];
        float axisNear = (minBounds[axis] - origin[axis]) * inverseDirection;
        float axisFar = (maxBounds[axis] - origin[axis]) * inverseDirection;

        if (axisNear > axisFar)
        {
            std::swap(axisNear, axisFar);
        }

        nearDistance = std::max(nearDistance, axisNear);
        farDistance = std::min(farDistance, axisFar);

        if (nearDistance > farDistance)
        {
            return std::nullopt;
        }
    }

    return nearDistance;
}

Mm9DatVec3 normalForRenderTriangle(const Mm9DatRenderTriangle &triangle)
{
    const Mm9DatVec3 first = vertexPosition(triangle.vertices[0]);
    const Mm9DatVec3 second = vertexPosition(triangle.vertices[1]);
    const Mm9DatVec3 third = vertexPosition(triangle.vertices[2]);
    const Mm9DatVec3 edgeA = subtractVec3(second, first);
    const Mm9DatVec3 edgeB = subtractVec3(third, first);
    const Mm9DatVec3 normal = crossVec3(edgeA, edgeB);
    return normalizedOrZero(normal);
}

struct RuntimeRayTriangleIntersection
{
    float distance = 0.0f;
    float barycentricU = 0.0f;
    float barycentricV = 0.0f;
};

std::optional<RuntimeRayTriangleIntersection> intersectRuntimeRayTriangle(
    const Mm9DatPickRay &ray,
    const Mm9DatRenderTriangle &triangle,
    bool includeBackfaces)
{
    const Mm9DatVec3 vertex0 = vertexPosition(triangle.vertices[0]);
    const Mm9DatVec3 vertex1 = vertexPosition(triangle.vertices[1]);
    const Mm9DatVec3 vertex2 = vertexPosition(triangle.vertices[2]);
    const Mm9DatVec3 edge1 = subtractVec3(vertex1, vertex0);
    const Mm9DatVec3 edge2 = subtractVec3(vertex2, vertex0);
    const Mm9DatVec3 pvec = crossVec3(ray.direction, edge2);
    const float determinant = dotVec3(edge1, pvec);

    if (!includeBackfaces && determinant < PickEpsilon)
    {
        return std::nullopt;
    }

    if (std::fabs(determinant) <= PickEpsilon)
    {
        return std::nullopt;
    }

    const float inverseDeterminant = 1.0f / determinant;
    const Mm9DatVec3 tvec = subtractVec3(ray.origin, vertex0);
    const float barycentricU = dotVec3(tvec, pvec) * inverseDeterminant;

    if (barycentricU < -PickEpsilon || barycentricU > 1.0f + PickEpsilon)
    {
        return std::nullopt;
    }

    const Mm9DatVec3 qvec = crossVec3(tvec, edge1);
    const float barycentricV = dotVec3(ray.direction, qvec) * inverseDeterminant;

    if (barycentricV < -PickEpsilon || barycentricU + barycentricV > 1.0f + PickEpsilon)
    {
        return std::nullopt;
    }

    const float distance = dotVec3(edge2, qvec) * inverseDeterminant;
    if (distance < 0.0f)
    {
        return std::nullopt;
    }

    RuntimeRayTriangleIntersection intersection = {};
    intersection.distance = distance;
    intersection.barycentricU = barycentricU;
    intersection.barycentricV = barycentricV;
    return intersection;
}

std::optional<Mm9DatRenderMeshPickHit> pickMechanismCollisionBatchTriangles(
    const Mm9DatMechanismCollisionBatch &batch,
    const Mm9DatPickRay &ray,
    bool includeBackfaces)
{
    std::optional<Mm9DatRenderMeshPickHit> bestHit;
    float bestDistance = std::numeric_limits<float>::max();

    for (size_t triangleIndex = 0; triangleIndex < batch.transformedTriangles.size(); ++triangleIndex)
    {
        const Mm9DatRenderTriangle &triangle = batch.transformedTriangles[triangleIndex];
        const std::optional<RuntimeRayTriangleIntersection> intersection =
            intersectRuntimeRayTriangle(ray, triangle, includeBackfaces);

        if (!intersection || intersection->distance >= bestDistance)
        {
            continue;
        }

        Mm9DatRenderMeshPickHit hit = {};
        hit.triangleIndex = triangleIndex;
        hit.sourceModelIndex = triangle.sourceModelIndex;
        hit.sourcePolyIndex = triangle.sourcePolyIndex;
        hit.sourceSurfaceIndex = triangle.sourceSurfaceIndex;
        hit.sourceTextureIndex = triangle.sourceTextureIndex;
        hit.sourceModelName = triangle.sourceModelName;
        hit.sourceTexture = triangle.sourceTexture;
        hit.distance = intersection->distance;
        hit.barycentricU = intersection->barycentricU;
        hit.barycentricV = intersection->barycentricV;
        hit.position = addVec3(ray.origin, multiplyVec3(ray.direction, intersection->distance));
        bestHit = std::move(hit);
        bestDistance = intersection->distance;
    }

    return bestHit;
}

const Mm9DatMechanismCollisionBatch *findMechanismCollisionBatch(
    const Mm9DatMechanismCollisionCache &cache,
    uint32_t mechanismHandle)
{
    const auto batchIterator = cache.batchIndexByMechanismHandle.find(mechanismHandle);

    return batchIterator != cache.batchIndexByMechanismHandle.end()
        && batchIterator->second < cache.batches.size()
            ? &cache.batches[batchIterator->second]
            : nullptr;
}

Mm9DatMechanismCollisionBatch *findMechanismCollisionBatch(
    Mm9DatMechanismCollisionCache &cache,
    uint32_t mechanismHandle)
{
    const auto batchIterator = cache.batchIndexByMechanismHandle.find(mechanismHandle);

    return batchIterator != cache.batchIndexByMechanismHandle.end()
        && batchIterator->second < cache.batches.size()
            ? &cache.batches[batchIterator->second]
            : nullptr;
}

struct MechanismSegmentHitResult
{
    Mm9DatMechanismCollisionHit hit;
    size_t candidateMechanismCount = 0;
    size_t testedMechanismCount = 0;
    size_t candidateTriangleCount = 0;
    size_t testedTriangleCount = 0;
};

struct MechanismFloorSupportResult
{
    Mm9DatFloorSupportHit floorHit;
    Mm9DatMechanismCollisionHit mechanismHit;
    size_t candidateMechanismCount = 0;
    size_t testedMechanismCount = 0;
    size_t candidateTriangleCount = 0;
    size_t testedTriangleCount = 0;
};

struct ObjectSegmentHitResult
{
    Mm9DatObjectCollisionHit hit;
    size_t candidateObjectCount = 0;
    size_t testedObjectCount = 0;
};

std::optional<ObjectSegmentHitResult> segmentcastMm9DatObjects(
    const Mm9DatObjectRegistry &registry,
    const Mm9DatPartyMovementStep &step)
{
    const Mm9DatVec3 displacement = step.desiredDisplacement;
    const float maxDistance =
        std::sqrt(displacement.x * displacement.x + displacement.y * displacement.y + displacement.z * displacement.z);
    const Mm9DatVec3 direction = normalizedOrZero(displacement);
    if (maxDistance <= PickEpsilon)
    {
        return std::nullopt;
    }

    Mm9DatPickRay ray = {};
    ray.origin = step.position;
    ray.direction = direction;
    const std::vector<size_t> candidates =
        collidableObjectCandidatesForRay(registry, ray, maxDistance);

    std::optional<ObjectSegmentHitResult> bestHit;
    size_t testedObjectCount = 0;
    for (size_t objectIndex : candidates)
    {
        if (objectIndex >= registry.objects.size())
        {
            continue;
        }

        const Mm9DatRuntimeObject &object = registry.objects[objectIndex];
        if (!object.solid
            || object.radius <= PickEpsilon
            || object.height <= PickEpsilon)
        {
            continue;
        }

        ++testedObjectCount;
        const float objectHalfHeight = std::max(0.0f, object.height * 0.5f);
        const float partyHalfHeight = std::max(0.0f, step.halfHeight);
        if (step.position.y + partyHalfHeight < object.position.y - objectHalfHeight
            || step.position.y - partyHalfHeight > object.position.y + objectHalfHeight)
        {
            continue;
        }

        const float radius = std::max(0.0f, step.radius) + object.radius;
        const float dx = step.position.x - object.position.x;
        const float dz = step.position.z - object.position.z;
        const float vx = displacement.x;
        const float vz = displacement.z;
        const float a = vx * vx + vz * vz;
        if (a <= PickEpsilon)
        {
            continue;
        }

        const float b = 2.0f * (dx * vx + dz * vz);
        const float c = dx * dx + dz * dz - radius * radius;
        const float discriminant = b * b - 4.0f * a * c;
        if (discriminant < 0.0f)
        {
            continue;
        }

        const float sqrtDiscriminant = std::sqrt(discriminant);
        const float firstT = (-b - sqrtDiscriminant) / (2.0f * a);
        const float secondT = (-b + sqrtDiscriminant) / (2.0f * a);
        const float t = firstT >= 0.0f ? firstT : secondT;
        if (t < 0.0f || t > 1.0f)
        {
            continue;
        }

        const float distance = maxDistance * t;
        if (bestHit && distance >= bestHit->hit.distance)
        {
            continue;
        }

        ObjectSegmentHitResult hit = {};
        hit.hit.distance = distance;
        hit.hit.point = addVec3(step.position, multiplyVec3(displacement, t));
        hit.hit.normal = normalizedOrZero({
            hit.hit.point.x - object.position.x,
            0.0f,
            hit.hit.point.z - object.position.z,
        });
        hit.hit.objectHandle = object.handle;
        hit.hit.objectId = object.objectId;
        hit.hit.sourceObjectIndex = object.sourceObjectIndex;
        hit.hit.sourceClass = object.sourceClass;
        hit.hit.sourceName = object.sourceName;
        hit.candidateObjectCount = candidates.size();
        hit.testedObjectCount = testedObjectCount;
        bestHit = std::move(hit);
    }

    if (bestHit)
    {
        bestHit->candidateObjectCount = candidates.size();
        bestHit->testedObjectCount = testedObjectCount;
    }

    return bestHit;
}

std::optional<MechanismSegmentHitResult> segmentcastMm9DatMechanisms(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatVec3 &start,
    const Mm9DatVec3 &end,
    bool includeBackfaces)
{
    const Mm9DatVec3 direction = subtractVec3(end, start);
    const float maxDistance =
        std::sqrt(direction.x * direction.x + direction.y * direction.y + direction.z * direction.z);
    const Mm9DatVec3 normalizedDirection = normalizedOrZero(direction);

    if (maxDistance <= PickEpsilon)
    {
        return std::nullopt;
    }

    Mm9DatPickRay ray = {};
    ray.origin = start;
    ray.direction = normalizedDirection;

    std::optional<MechanismSegmentHitResult> bestHit;
    size_t candidateMechanismCount = 0;
    size_t testedMechanismCount = 0;

    const std::vector<size_t> mechanismCandidates =
        mechanismCandidatesForRay(runtime.mechanismBoundsIndex, ray, maxDistance);
    candidateMechanismCount = mechanismCandidates.size();

    for (size_t mechanismIndex : mechanismCandidates)
    {
        if (mechanismIndex >= runtime.mechanismRuntime.mechanisms.size())
        {
            continue;
        }

        const Mm9DatMechanismInstance &mechanism =
            runtime.mechanismRuntime.mechanisms[mechanismIndex];
        if (!mechanism.active || mechanism.inert || !mechanism.currentBounds.valid)
        {
            continue;
        }

        const std::optional<float> boundsDistance =
            intersectRayBounds(ray, mechanism.currentBounds, maxDistance);

        if (!boundsDistance)
        {
            continue;
        }

        ++testedMechanismCount;
        const Mm9DatMechanismCollisionBatch *pCollisionBatch =
            findMechanismCollisionBatch(runtime.mechanismCollisionCache, mechanism.handle);
        if (pCollisionBatch == nullptr || pCollisionBatch->transformedTriangles.empty())
        {
            continue;
        }

        const std::optional<Mm9DatRenderMeshPickHit> meshHit =
            pickMechanismCollisionBatchTriangles(*pCollisionBatch, ray, includeBackfaces);

        if (!meshHit || meshHit->distance > maxDistance + PickEpsilon)
        {
            continue;
        }

        if (bestHit && meshHit->distance >= bestHit->hit.distance)
        {
            continue;
        }

        MechanismSegmentHitResult result = {};
        result.hit.point = meshHit->position;
        result.hit.distance = meshHit->distance;
        result.hit.mechanismHandle = mechanism.handle;
        result.hit.mechanismId = mechanism.mechanismId;
        result.hit.objectId = mechanism.objectId;
        result.hit.sourceObjectIndex =
            mechanism.sourceObjectIndex >= 0
                ? static_cast<size_t>(mechanism.sourceObjectIndex)
                : 0;
        result.hit.sourceModelIndex = meshHit->sourceModelIndex;
        result.hit.sourcePolyIndex = meshHit->sourcePolyIndex;
        result.hit.sourceSurfaceIndex = meshHit->sourceSurfaceIndex;
        result.hit.sourceModelName = meshHit->sourceModelName;
        if (meshHit->triangleIndex < pCollisionBatch->transformedTriangles.size())
        {
            result.hit.normal =
                normalForRenderTriangle(pCollisionBatch->transformedTriangles[meshHit->triangleIndex]);
        }
        result.candidateTriangleCount = pCollisionBatch->transformedTriangles.size();
        result.testedTriangleCount = pCollisionBatch->transformedTriangles.size();
        bestHit = std::move(result);
    }

    if (bestHit)
    {
        bestHit->candidateMechanismCount = candidateMechanismCount;
        bestHit->testedMechanismCount = testedMechanismCount;
    }

    return bestHit;
}

std::optional<MechanismFloorSupportResult> findMm9DatMechanismFloorSupport(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatFloorSupportQuery &query)
{
    if (query.maxDropDistance <= PickEpsilon)
    {
        return std::nullopt;
    }

    Mm9DatPickRay ray = {};
    ray.origin = query.position;
    ray.direction = {0.0f, -1.0f, 0.0f};

    const std::vector<size_t> mechanismCandidates =
        mechanismCandidatesForRay(runtime.mechanismBoundsIndex, ray, query.maxDropDistance);

    std::optional<MechanismFloorSupportResult> bestSupport;
    size_t testedMechanismCount = 0;
    size_t candidateTriangleCount = 0;
    size_t testedTriangleCount = 0;

    for (size_t mechanismIndex : mechanismCandidates)
    {
        if (mechanismIndex >= runtime.mechanismRuntime.mechanisms.size())
        {
            continue;
        }

        const Mm9DatMechanismInstance &mechanism =
            runtime.mechanismRuntime.mechanisms[mechanismIndex];
        if (!mechanism.active || mechanism.inert || !mechanism.currentBounds.valid)
        {
            continue;
        }

        const std::optional<float> boundsDistance =
            intersectRayBounds(ray, mechanism.currentBounds, query.maxDropDistance);
        if (!boundsDistance)
        {
            continue;
        }

        ++testedMechanismCount;
        const Mm9DatMechanismCollisionBatch *pCollisionBatch =
            findMechanismCollisionBatch(runtime.mechanismCollisionCache, mechanism.handle);
        if (pCollisionBatch == nullptr || pCollisionBatch->transformedTriangles.empty())
        {
            continue;
        }

        candidateTriangleCount += pCollisionBatch->transformedTriangles.size();
        testedTriangleCount += pCollisionBatch->transformedTriangles.size();

        const std::optional<Mm9DatRenderMeshPickHit> meshHit =
            pickMechanismCollisionBatchTriangles(*pCollisionBatch, ray, query.includeBackfaces);
        if (!meshHit || meshHit->distance > query.maxDropDistance + PickEpsilon)
        {
            continue;
        }

        if (bestSupport && meshHit->distance >= bestSupport->floorHit.rayDistance)
        {
            continue;
        }

        MechanismFloorSupportResult support = {};
        support.floorHit.floorPoint = meshHit->position;
        support.floorHit.adjustedPosition = query.position;
        support.floorHit.adjustedPosition.y =
            meshHit->position.y + query.halfHeight + query.placementBias;
        support.floorHit.rayDistance = meshHit->distance;
        support.floorHit.dropDistance =
            std::max(0.0f, query.position.y - support.floorHit.adjustedPosition.y);
        support.floorHit.candidateTriangleCount = pCollisionBatch->transformedTriangles.size();
        support.floorHit.testedTriangleCount = pCollisionBatch->transformedTriangles.size();
        support.floorHit.source.sourceModelIndex = meshHit->sourceModelIndex;
        support.floorHit.source.sourceModelName = meshHit->sourceModelName;
        support.floorHit.source.sourcePolyIndex = meshHit->sourcePolyIndex;
        support.floorHit.source.sourceSurfaceIndex = meshHit->sourceSurfaceIndex;
        support.floorHit.source.sourceTextureIndex = meshHit->sourceTextureIndex;
        support.floorHit.source.sourceTexture = meshHit->sourceTexture;
        if (meshHit->triangleIndex < pCollisionBatch->sourceTriangleIndices.size())
        {
            support.floorHit.source.renderTriangleIndex =
                pCollisionBatch->sourceTriangleIndices[meshHit->triangleIndex];
        }

        support.mechanismHit.point = meshHit->position;
        support.mechanismHit.distance = meshHit->distance;
        support.mechanismHit.mechanismHandle = mechanism.handle;
        support.mechanismHit.mechanismId = mechanism.mechanismId;
        support.mechanismHit.objectId = mechanism.objectId;
        support.mechanismHit.sourceObjectIndex =
            mechanism.sourceObjectIndex >= 0
                ? static_cast<size_t>(mechanism.sourceObjectIndex)
                : 0;
        support.mechanismHit.sourceModelIndex = meshHit->sourceModelIndex;
        support.mechanismHit.sourcePolyIndex = meshHit->sourcePolyIndex;
        support.mechanismHit.sourceSurfaceIndex = meshHit->sourceSurfaceIndex;
        support.mechanismHit.sourceModelName = meshHit->sourceModelName;

        if (meshHit->triangleIndex < pCollisionBatch->transformedTriangles.size())
        {
            const Mm9DatVec3 normal =
                normalForRenderTriangle(pCollisionBatch->transformedTriangles[meshHit->triangleIndex]);
            support.floorHit.normal = normal;
            support.mechanismHit.normal = normal;
        }

        bestSupport = std::move(support);
    }

    if (bestSupport)
    {
        bestSupport->candidateMechanismCount = mechanismCandidates.size();
        bestSupport->testedMechanismCount = testedMechanismCount;
        bestSupport->candidateTriangleCount = candidateTriangleCount;
        bestSupport->testedTriangleCount = testedTriangleCount;
    }

    return bestSupport;
}

void applyMm9DatRuntimeFloorSupport(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatPartyMovementStep &step,
    Mm9DatPartyMovementResult &result)
{
    if (step.floorChannelMask == 0
        || step.floorSnapDistance <= 0.0f
        || step.desiredDisplacement.y > step.floorBias)
    {
        return;
    }

    Mm9DatFloorSupportQuery floorQuery = {};
    floorQuery.position = result.finalPosition;
    floorQuery.channelMask = step.floorChannelMask;
    floorQuery.maxDropDistance = step.floorSnapDistance;
    floorQuery.halfHeight = std::max(0.0f, step.halfHeight);
    floorQuery.placementBias = step.floorBias;

    const std::optional<MechanismFloorSupportResult> mechanismFloor =
        findMm9DatMechanismFloorSupport(runtime, floorQuery);
    if (!mechanismFloor)
    {
        return;
    }

    if (result.floorHit
        && result.floorHit->rayDistance <= mechanismFloor->floorHit.rayDistance + PickEpsilon)
    {
        return;
    }

    result.floorHit = mechanismFloor->floorHit;
    result.mechanismFloorHit = mechanismFloor->mechanismHit;
    result.onGround = true;
    result.finalPosition.y = mechanismFloor->floorHit.adjustedPosition.y;
    result.floorCandidateTriangleCount = mechanismFloor->candidateTriangleCount;
    result.floorTestedTriangleCount = mechanismFloor->testedTriangleCount;
    result.mechanismCandidateCount =
        std::max(result.mechanismCandidateCount, mechanismFloor->candidateMechanismCount);
    result.mechanismTestedCount =
        std::max(result.mechanismTestedCount, mechanismFloor->testedMechanismCount);
    result.mechanismCandidateTriangleCount =
        std::max(result.mechanismCandidateTriangleCount, mechanismFloor->candidateTriangleCount);
    result.mechanismTestedTriangleCount =
        std::max(result.mechanismTestedTriangleCount, mechanismFloor->testedTriangleCount);
}

void finishBounds(Mm9DatRenderBounds &bounds)
{
    if (!bounds.valid)
    {
        return;
    }

    bounds.center = {
        (bounds.min.x + bounds.max.x) * 0.5f,
        (bounds.min.y + bounds.max.y) * 0.5f,
        (bounds.min.z + bounds.max.z) * 0.5f,
    };
    bounds.radius = 0.0f;

    const std::array<Mm9DatVec3, 8> corners = {{
        {bounds.min.x, bounds.min.y, bounds.min.z},
        {bounds.min.x, bounds.min.y, bounds.max.z},
        {bounds.min.x, bounds.max.y, bounds.min.z},
        {bounds.min.x, bounds.max.y, bounds.max.z},
        {bounds.max.x, bounds.min.y, bounds.min.z},
        {bounds.max.x, bounds.min.y, bounds.max.z},
        {bounds.max.x, bounds.max.y, bounds.min.z},
        {bounds.max.x, bounds.max.y, bounds.max.z},
    }};

    for (const Mm9DatVec3 &corner : corners)
    {
        bounds.radius = std::max(bounds.radius, distance(bounds.center, corner));
    }
}

Mm9DatRenderBounds lerpBounds(
    const Mm9DatRenderBounds &closedBounds,
    const Mm9DatRenderBounds &openBounds,
    float progress)
{
    if (!closedBounds.valid)
    {
        return openBounds;
    }

    if (!openBounds.valid)
    {
        return closedBounds;
    }

    const float t = std::clamp(progress, 0.0f, 1.0f);
    Mm9DatRenderBounds bounds = {};
    bounds.valid = true;
    bounds.min = {
        closedBounds.min.x + (openBounds.min.x - closedBounds.min.x) * t,
        closedBounds.min.y + (openBounds.min.y - closedBounds.min.y) * t,
        closedBounds.min.z + (openBounds.min.z - closedBounds.min.z) * t,
    };
    bounds.max = {
        closedBounds.max.x + (openBounds.max.x - closedBounds.max.x) * t,
        closedBounds.max.y + (openBounds.max.y - closedBounds.max.y) * t,
        closedBounds.max.z + (openBounds.max.z - closedBounds.max.z) * t,
    };
    finishBounds(bounds);
    return bounds;
}

std::vector<const Mm9DatRenderFilterEntry *> filtersByTriangle(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatRenderFilterResult &filters)
{
    std::vector<const Mm9DatRenderFilterEntry *> result(mesh.triangles.size(), nullptr);

    for (const Mm9DatRenderFilterEntry &entry : filters.entries)
    {
        if (entry.triangleIndex < result.size())
        {
            result[entry.triangleIndex] = &entry;
        }
    }

    return result;
}

std::vector<const Mm9DatRenderMaterialAssignment *> assignmentsByTriangle(
    const Mm9DatRenderMesh &mesh,
    const std::vector<Mm9DatRenderMaterialAssignment> &assignments)
{
    std::vector<const Mm9DatRenderMaterialAssignment *> result(mesh.triangles.size(), nullptr);

    for (const Mm9DatRenderMaterialAssignment &assignment : assignments)
    {
        if (assignment.triangleIndex < result.size())
        {
            result[assignment.triangleIndex] = &assignment;
        }
    }

    return result;
}

std::unordered_set<size_t> sourceModelSet(const std::vector<size_t> &sourceModelIndices)
{
    std::unordered_set<size_t> result;

    for (size_t sourceModelIndex : sourceModelIndices)
    {
        result.insert(sourceModelIndex);
    }

    return result;
}

std::vector<size_t> activeMechanismSourceModelIndices(const Mm9DatMechanismRuntime &mechanismRuntime)
{
    std::vector<size_t> result;
    std::unordered_set<size_t> seenSourceModelIndices;

    for (const Mm9DatMechanismInstance &mechanism : mechanismRuntime.mechanisms)
    {
        if (!mechanism.active || mechanism.inert)
        {
            continue;
        }

        if (seenSourceModelIndices.insert(mechanism.sourceModelIndex).second)
        {
            result.push_back(mechanism.sourceModelIndex);
        }
    }

    return result;
}

Mm9DatRenderFilterResult filterRenderEntriesExcludingSourceModels(
    const Mm9DatRenderFilterResult &filters,
    const std::vector<size_t> &excludedSourceModelIndices)
{
    if (excludedSourceModelIndices.empty())
    {
        return filters;
    }

    const std::unordered_set<size_t> excludedSourceModels = sourceModelSet(excludedSourceModelIndices);
    Mm9DatRenderFilterResult result = {};
    result.entries.reserve(filters.entries.size());

    for (const Mm9DatRenderFilterEntry &entry : filters.entries)
    {
        if (excludedSourceModels.find(entry.sourceModelIndex) != excludedSourceModels.end())
        {
            continue;
        }

        result.entries.push_back(entry);
    }

    return result;
}

bool isNormalRuntimeVisual(uint32_t flags)
{
    if ((flags & Mm9DatRenderFilterWaterVolume) != 0
        || (flags & Mm9DatRenderFilterRail) != 0
        || (flags & Mm9DatRenderFilterTrigger) != 0
        || (flags & Mm9DatRenderFilterVisibility) != 0)
    {
        return false;
    }

    return (flags & (Mm9DatRenderFilterVisual | Mm9DatRenderFilterVisibleWater | Mm9DatRenderFilterSky)) != 0;
}

bool isTranslucentMaterial(const Mm9DatRenderTriangle &triangle)
{
    return (triangle.surfaceFlags & Mm9DatSurfaceFlagTransparent) != 0;
}

std::string materialKeyForTriangle(
    const Mm9DatRenderTriangle &triangle,
    const Mm9DatRenderMaterialAssignment *pAssignment)
{
    if (pAssignment != nullptr && pAssignment->assigned && pAssignment->sourceDtxResolved)
    {
        return pAssignment->resolvedSourcePath.empty() ? pAssignment->alias : pAssignment->resolvedSourcePath;
    }

    if (!triangle.sourceTexture.empty())
    {
        return "source:" + triangle.sourceTexture;
    }

    return "missing";
}

std::string partitionKey(
    size_t sourceModelIndex,
    const std::string &materialKey,
    Mm9DatRenderPartitionBlendMode blendMode,
    uint32_t flags)
{
    const uint32_t passFlags =
        flags
        & (Mm9DatRenderFilterVisual | Mm9DatRenderFilterSky | Mm9DatRenderFilterWater
            | Mm9DatRenderFilterVisibleWater | Mm9DatRenderFilterTerrain | Mm9DatRenderFilterMovable);
    return std::to_string(sourceModelIndex) + "|" + std::to_string(static_cast<int>(blendMode)) + "|"
        + std::to_string(passFlags) + "|" + materialKey;
}

std::string lowerCopy(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return result;
}

bool startsWith(const std::string &value, const std::string &prefix)
{
    return value.size() >= prefix.size()
        && value.compare(0, prefix.size(), prefix) == 0;
}

std::string normalizeTextureCatalogKey(const std::string &value)
{
    std::string normalized = value;
    std::replace(normalized.begin(), normalized.end(), '\\', '/');

    while (!normalized.empty() && normalized.front() == '/')
    {
        normalized.erase(normalized.begin());
    }

    return lowerCopy(normalized);
}

bool isDtxTexturePath(const std::filesystem::path &path)
{
    return lowerCopy(path.extension().string()) == ".dtx";
}

bool isKnownTextureFamilyRootName(const std::string &rootName)
{
    return rootName == "textures"
        || rootName == "skins"
        || rootName == "sprite_textures";
}

void addTextureCatalogKey(
    Mm9DatRuntimeTextureCatalog &catalog,
    const std::string &key,
    size_t catalogEntryIndex)
{
    if (key.empty())
    {
        return;
    }

    const auto inserted = catalog.entryIndexByKey.emplace(key, catalogEntryIndex);
    if (!inserted.second && inserted.first->second != catalogEntryIndex)
    {
        ++catalog.stats.duplicateCatalogKeyCount;
    }
}

std::optional<size_t> findTextureCatalogEntry(
    const Mm9DatRuntimeTextureCatalog &catalog,
    const std::string &textureName)
{
    const std::string key = normalizeTextureCatalogKey(textureName);
    if (key.empty())
    {
        return std::nullopt;
    }

    const auto exactIterator = catalog.entryIndexByKey.find(key);
    if (exactIterator != catalog.entryIndexByKey.end())
    {
        return exactIterator->second;
    }

    if (std::filesystem::path(key).extension().empty())
    {
        const auto dtxIterator = catalog.entryIndexByKey.find(key + ".dtx");
        if (dtxIterator != catalog.entryIndexByKey.end())
        {
            return dtxIterator->second;
        }
    }

    return std::nullopt;
}

bool floorPlacementPolicySkipsObject(const Mm9ScriptedObject &object)
{
    const std::string className = lowerCopy(object.sourceClass);
    const std::string sourceName = lowerCopy(object.sourceName);

    return object.movement.flying
        || className.find("terrain") != std::string::npos
        || className.find("physicsbsp") != std::string::npos
        || className.find("visbsp") != std::string::npos
        || className.find("rail") != std::string::npos
        || className.find("sky") != std::string::npos
        || className.find("trigger") != std::string::npos
        || className.find("volume") != std::string::npos
        || className.find("water") != std::string::npos
        || sourceName.find("terrain") != std::string::npos
        || sourceName.find("physicsbsp") != std::string::npos
        || sourceName.find("visbsp") != std::string::npos
        || sourceName.find("rail") != std::string::npos
        || sourceName.find("sky") != std::string::npos
        || sourceName.find("trigger") != std::string::npos;
}

uint32_t objectHandleForIndex(size_t objectIndex)
{
    return static_cast<uint32_t>(objectIndex + 1);
}

uint32_t mechanismHandleForIndex(size_t mechanismIndex)
{
    return static_cast<uint32_t>(mechanismIndex + 1);
}

bool vec3FromFloatVector(const std::vector<float> &values, Mm9DatVec3 &result)
{
    if (values.size() < 3)
    {
        return false;
    }

    result = {values[0], values[1], values[2]};
    return true;
}

const Mm9EventBinding *findBindingForMechanism(
    const Mm9EventsData &events,
    const Mm9EventMechanism &mechanism)
{
    for (const Mm9EventBinding &binding : events.bindings)
    {
        if (binding.objectId == mechanism.objectId)
        {
            return &binding;
        }
    }

    return nullptr;
}

const Mm9EventBindingTarget *findFirstWorldModelTarget(const Mm9EventBinding &binding)
{
    for (const Mm9EventBindingTarget &target : binding.targets)
    {
        if (target.bmodelIndex.has_value())
        {
            return &target;
        }
    }

    return nullptr;
}

bool buildMechanismMotion(
    const Mm9EventMechanism &mechanism,
    const Mm9EventBindingTarget &target,
    float progress,
    Mm9DatMechanismPreviewMotion &motion)
{
    if (!target.bmodelIndex.has_value())
    {
        return false;
    }

    motion = {};
    motion.sourceModelIndex = *target.bmodelIndex;
    motion.progress = std::clamp(progress, 0.0f, 1.0f);
    motion.hasLinearMotion =
        mechanism.linear.hasMoveDir
        && mechanism.linear.hasMoveDist
        && std::fabs(mechanism.linear.moveDistLt) > 0.0001f
        && vec3FromFloatVector(mechanism.linear.moveDirLt, motion.moveDirLt);
    motion.moveDistLt = mechanism.linear.moveDistLt;
    motion.hasRotationMotion =
        mechanism.rotation.hasRotationPoint
        && mechanism.rotation.hasRotationAngles
        && vec3FromFloatVector(mechanism.rotation.rotationPointLt, motion.rotationPointLt)
        && vec3FromFloatVector(mechanism.rotation.rotationAnglesDeg, motion.rotationAnglesDeg);

    return motion.hasLinearMotion || motion.hasRotationMotion;
}

float vectorLength(const Mm9DatVec3 &value)
{
    return std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
}

float authoredMechanismTravelDistance(const Mm9EventMechanism &mechanism)
{
    if (mechanism.linear.hasMoveDist && std::fabs(mechanism.linear.moveDistLt) > 0.0001f)
    {
        return std::fabs(mechanism.linear.moveDistLt);
    }

    Mm9DatVec3 rotationAngles = {};
    if (mechanism.rotation.hasRotationAngles
        && vec3FromFloatVector(mechanism.rotation.rotationAnglesDeg, rotationAngles))
    {
        return vectorLength(rotationAngles);
    }

    return 0.0f;
}

float mechanismDurationSeconds(float travelDistance, float authoredSpeed)
{
    if (travelDistance > 0.0001f && authoredSpeed > 0.0001f)
    {
        return std::max(MinimumMechanismDurationSeconds, travelDistance / authoredSpeed);
    }

    return DefaultMechanismDurationSeconds;
}

void updateMechanismCurrentTransform(Mm9DatMechanismInstance &mechanism)
{
    mechanism.progress = std::clamp(mechanism.progress, 0.0f, 1.0f);
    mechanism.motion.progress = mechanism.progress;

    if (mechanism.boundsChangeKnown)
    {
        mechanism.currentBounds = lerpBounds(mechanism.closedBounds, mechanism.openBounds, mechanism.progress);
    }
    else
    {
        mechanism.currentBounds = mechanism.closedBounds.valid ? mechanism.closedBounds : mechanism.openBounds;
    }
}

bool mechanismIsMoving(const Mm9DatMechanismInstance &mechanism)
{
    return mechanism.state == Mm9DatMechanismState::Opening
        || mechanism.state == Mm9DatMechanismState::Closing;
}

bool mechanismNeedsQueuedUpdate(const Mm9DatMechanismInstance &mechanism)
{
    return mechanismIsMoving(mechanism)
        || mechanism.moveDelayRemainingSeconds > 0.0f
        || mechanism.openWaitRemainingSeconds > 0.0f;
}

Mm9DatMechanismInstance *findMechanismByHandle(
    Mm9DatMechanismRuntime &runtime,
    uint32_t handle,
    size_t *pMechanismIndex = nullptr)
{
    const auto iterator = runtime.mechanismIndexByHandle.find(handle);
    if (iterator != runtime.mechanismIndexByHandle.end()
        && iterator->second < runtime.mechanisms.size())
    {
        if (pMechanismIndex != nullptr)
        {
            *pMechanismIndex = iterator->second;
        }

        return &runtime.mechanisms[iterator->second];
    }

    return nullptr;
}

void queueMechanismUpdate(Mm9DatMechanismRuntime &runtime, size_t mechanismIndex)
{
    if (mechanismIndex >= runtime.mechanisms.size())
    {
        return;
    }

    Mm9DatMechanismInstance &mechanism = runtime.mechanisms[mechanismIndex];
    if (mechanism.queuedForUpdate || !mechanismNeedsQueuedUpdate(mechanism))
    {
        return;
    }

    mechanism.queuedForUpdate = true;
    runtime.movingMechanismIndices.push_back(mechanismIndex);
}

void addPlacementStats(Mm9DatObjectRegistryStats &stats, const Mm9DatRuntimeObject &object)
{
    ++stats.objectCount;

    if (object.visible)
    {
        ++stats.visibleObjectCount;
    }

    if (object.solid)
    {
        ++stats.solidObjectCount;
    }

    if (object.rayHit)
    {
        ++stats.rayHitObjectCount;
    }

    if (object.moveToFloor)
    {
        ++stats.moveToFloorObjectCount;
    }

    if (object.placementStatus == Mm9DatObjectPlacementStatus::SnappedToFloor)
    {
        ++stats.snappedToFloorCount;
    }
    else if (object.placementStatus == Mm9DatObjectPlacementStatus::UnsupportedMoveToFloor)
    {
        ++stats.unsupportedMoveToFloorCount;
    }
    else if (object.placementStatus == Mm9DatObjectPlacementStatus::PolicySkipped)
    {
        ++stats.policySkippedMoveToFloorCount;
    }
}

void addObjectToPickableCells(Mm9DatObjectRegistry &registry, size_t objectIndex)
{
    if (objectIndex >= registry.objects.size())
    {
        return;
    }

    const Mm9DatRuntimeObject &object = registry.objects[objectIndex];
    if (!object.visible || !object.rayHit || object.radius <= PickEpsilon)
    {
        return;
    }

    const float cellSize =
        registry.pickableObjectCellSize > PickEpsilon
            ? registry.pickableObjectCellSize
            : DefaultObjectPickCellSize;
    const int32_t minCellX = floorCell(object.position.x - object.radius, cellSize);
    const int32_t maxCellX = floorCell(object.position.x + object.radius, cellSize);
    const int32_t minCellZ = floorCell(object.position.z - object.radius, cellSize);
    const int32_t maxCellZ = floorCell(object.position.z + object.radius, cellSize);

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
        {
            registry.pickableObjectIndicesByCell[horizontalCellKey(cellX, cellZ)].push_back(objectIndex);
            ++registry.stats.pickableCellObjectRefs;
        }
    }
}

void finishObjectPickableCells(Mm9DatObjectRegistry &registry)
{
    registry.stats.pickableCellCount = registry.pickableObjectIndicesByCell.size();
    registry.stats.maxPickableCellObjectRefs = 0;

    for (const auto &cellEntry : registry.pickableObjectIndicesByCell)
    {
        registry.stats.maxPickableCellObjectRefs =
            std::max(registry.stats.maxPickableCellObjectRefs, cellEntry.second.size());
    }
}

bool objectTextContainsToken(const Mm9DatRuntimeObject &object, const std::string &token)
{
    return lowerCopy(object.sourceClass).find(token) != std::string::npos
        || lowerCopy(object.sourceName).find(token) != std::string::npos
        || lowerCopy(object.sourceModel).find(token) != std::string::npos
        || lowerCopy(object.modelAsset).find(token) != std::string::npos
        || lowerCopy(object.scriptName).find(token) != std::string::npos;
}

bool objectIsTriggerLike(const Mm9DatRuntimeObject &object)
{
    return objectTextContainsToken(object, "trigger")
        || objectTextContainsToken(object, "volume")
        || objectTextContainsToken(object, "zone");
}

bool objectIsPickupLike(const Mm9DatRuntimeObject &object)
{
    return objectTextContainsToken(object, "pickup")
        || objectTextContainsToken(object, "item")
        || objectTextContainsToken(object, "loot");
}

bool objectIsLightLike(const Mm9DatRuntimeObject &object)
{
    return objectTextContainsToken(object, "light");
}

bool objectIsHelperLike(const Mm9DatRuntimeObject &object)
{
    return objectTextContainsToken(object, "terrain")
        || objectTextContainsToken(object, "physicsbsp")
        || objectTextContainsToken(object, "visbsp")
        || objectTextContainsToken(object, "rail")
        || objectTextContainsToken(object, "sky")
        || objectTextContainsToken(object, "water");
}

bool objectIsSoundLike(const Mm9DatRuntimeObject &object)
{
    return objectTextContainsToken(object, "sound")
        || lowerCopy(object.sourceModel).rfind("sounds/", 0) == 0;
}

std::unordered_set<std::string> mechanismObjectIds(const Mm9DatMechanismRuntime *pMechanismRuntime)
{
    std::unordered_set<std::string> result;
    if (pMechanismRuntime == nullptr)
    {
        return result;
    }

    for (const Mm9DatMechanismInstance &mechanism : pMechanismRuntime->mechanisms)
    {
        if (!mechanism.objectId.empty())
        {
            result.insert(mechanism.objectId);
        }
    }

    return result;
}

void addObjectRegistryMembership(
    Mm9DatObjectRegistry &registry,
    size_t objectIndex,
    const std::unordered_set<std::string> &mechanismObjectIds)
{
    if (objectIndex >= registry.objects.size())
    {
        return;
    }

    const Mm9DatRuntimeObject &object = registry.objects[objectIndex];
    const bool renderable =
        object.visible
        && !objectIsHelperLike(object)
        && !objectIsSoundLike(object)
        && (!object.sourceModel.empty() || !object.modelAsset.empty() || !object.visualId.empty());
    const bool collidable =
        object.solid
        && object.radius > PickEpsilon
        && object.height > PickEpsilon
        && !objectIsHelperLike(object)
        && !objectIsSoundLike(object);
    const bool rayHit =
        object.visible
        && object.rayHit
        && object.radius > PickEpsilon;
    const bool trigger = objectIsTriggerLike(object);
    const bool mechanism = mechanismObjectIds.find(object.objectId) != mechanismObjectIds.end();
    const bool interactable = rayHit && (mechanism || !object.scriptName.empty() || object.pickable);
    const bool pickup = objectIsPickupLike(object);
    const bool light = objectIsLightLike(object);
    const bool prop = lowerCopy(object.sourceClass) == "prop";
    const bool actor =
        object.visible
        && !prop
        && !trigger
        && !mechanism
        && !pickup
        && !light
        && !objectIsSoundLike(object)
        && !objectIsHelperLike(object);

    if (renderable)
    {
        registry.renderableObjectIndices.push_back(objectIndex);
        ++registry.stats.renderableObjectCount;
    }
    if (collidable)
    {
        registry.collidableObjectIndices.push_back(objectIndex);
        ++registry.stats.collidableObjectCount;
    }
    if (rayHit)
    {
        registry.rayHitObjectIndices.push_back(objectIndex);
    }
    if (trigger)
    {
        registry.triggerObjectIndices.push_back(objectIndex);
        ++registry.stats.triggerObjectCount;
    }
    if (interactable)
    {
        registry.interactableObjectIndices.push_back(objectIndex);
        ++registry.stats.interactableObjectCount;
    }
    if (actor)
    {
        if (objectIndex < registry.actorIndexByObjectIndex.size())
        {
            registry.actorIndexByObjectIndex[objectIndex] = registry.actorObjectIndices.size();
        }
        registry.actorObjectIndices.push_back(objectIndex);
        ++registry.stats.actorObjectCount;
    }
    if (prop)
    {
        registry.propObjectIndices.push_back(objectIndex);
        ++registry.stats.propObjectCount;
    }
    if (pickup)
    {
        registry.pickupObjectIndices.push_back(objectIndex);
        ++registry.stats.pickupObjectCount;
    }
    if (light)
    {
        registry.lightObjectIndices.push_back(objectIndex);
        ++registry.stats.lightObjectCount;
    }
    if (mechanism)
    {
        registry.mechanismObjectIndices.push_back(objectIndex);
        ++registry.stats.mechanismObjectCount;
    }
    if (object.needsTick)
    {
        registry.tickingObjectIndices.push_back(objectIndex);
        ++registry.stats.tickingObjectCount;
    }
}

void addObjectToCollidableCells(Mm9DatObjectRegistry &registry, size_t objectIndex)
{
    if (objectIndex >= registry.objects.size())
    {
        return;
    }

    const Mm9DatRuntimeObject &object = registry.objects[objectIndex];
    if (!object.solid
        || objectIsHelperLike(object)
        || objectIsSoundLike(object)
        || object.radius <= PickEpsilon
        || object.height <= PickEpsilon)
    {
        return;
    }

    const float cellSize =
        registry.collidableObjectCellSize > PickEpsilon
            ? registry.collidableObjectCellSize
            : DefaultObjectPickCellSize;
    const int32_t minCellX = floorCell(object.position.x - object.radius, cellSize);
    const int32_t maxCellX = floorCell(object.position.x + object.radius, cellSize);
    const int32_t minCellZ = floorCell(object.position.z - object.radius, cellSize);
    const int32_t maxCellZ = floorCell(object.position.z + object.radius, cellSize);

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
        {
            registry.collidableObjectIndicesByCell[horizontalCellKey(cellX, cellZ)].push_back(objectIndex);
            ++registry.stats.collidableCellObjectRefs;
        }
    }
}

void finishObjectCollidableCells(Mm9DatObjectRegistry &registry)
{
    registry.stats.collidableCellCount = registry.collidableObjectIndicesByCell.size();
    registry.stats.maxCollidableCellObjectRefs = 0;
    for (const auto &cellEntry : registry.collidableObjectIndicesByCell)
    {
        registry.stats.maxCollidableCellObjectRefs =
            std::max(registry.stats.maxCollidableCellObjectRefs, cellEntry.second.size());
    }
}

void addObjectToActorCells(Mm9DatObjectRegistry &registry, size_t objectIndex)
{
    if (objectIndex >= registry.objects.size()
        || objectIndex >= registry.actorIndexByObjectIndex.size()
        || registry.actorIndexByObjectIndex[objectIndex] == InvalidRuntimeIndex)
    {
        return;
    }

    const Mm9DatRuntimeObject &object = registry.objects[objectIndex];
    if (!object.visible || object.radius <= PickEpsilon)
    {
        return;
    }

    const float cellSize =
        registry.actorObjectCellSize > PickEpsilon
            ? registry.actorObjectCellSize
            : DefaultObjectPickCellSize;
    const int32_t minCellX = floorCell(object.position.x - object.radius, cellSize);
    const int32_t maxCellX = floorCell(object.position.x + object.radius, cellSize);
    const int32_t minCellZ = floorCell(object.position.z - object.radius, cellSize);
    const int32_t maxCellZ = floorCell(object.position.z + object.radius, cellSize);

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
        {
            registry.actorObjectIndicesByCell[horizontalCellKey(cellX, cellZ)].push_back(objectIndex);
            ++registry.stats.actorCellObjectRefs;
        }
    }
}

void finishObjectActorCells(Mm9DatObjectRegistry &registry)
{
    registry.stats.actorCellCount = registry.actorObjectIndicesByCell.size();
    registry.stats.maxActorCellObjectRefs = 0;
    for (const auto &cellEntry : registry.actorObjectIndicesByCell)
    {
        registry.stats.maxActorCellObjectRefs =
            std::max(registry.stats.maxActorCellObjectRefs, cellEntry.second.size());
    }
}

bool containsObjectIndex(const std::vector<size_t> &indices, size_t objectIndex)
{
    return std::find(indices.begin(), indices.end(), objectIndex) != indices.end();
}

Mm9DatObjectPresentationKind presentationKindForObject(
    const Mm9DatObjectRegistry &registry,
    size_t objectIndex)
{
    if (containsObjectIndex(registry.mechanismObjectIndices, objectIndex))
    {
        return Mm9DatObjectPresentationKind::Mechanism;
    }
    if (objectIndex < registry.actorIndexByObjectIndex.size()
        && registry.actorIndexByObjectIndex[objectIndex] != InvalidRuntimeIndex)
    {
        return Mm9DatObjectPresentationKind::Actor;
    }
    if (containsObjectIndex(registry.propObjectIndices, objectIndex))
    {
        return Mm9DatObjectPresentationKind::Prop;
    }
    if (containsObjectIndex(registry.pickupObjectIndices, objectIndex))
    {
        return Mm9DatObjectPresentationKind::Pickup;
    }
    if (containsObjectIndex(registry.lightObjectIndices, objectIndex))
    {
        return Mm9DatObjectPresentationKind::Light;
    }

    return Mm9DatObjectPresentationKind::Object;
}

void addPresentationStats(
    Mm9DatObjectPresentationWorldStats &stats,
    const Mm9DatObjectPresentationInstance &instance)
{
    ++stats.instanceCount;

    if (instance.collidable)
    {
        ++stats.collidableInstanceCount;
    }
    if (instance.interactable)
    {
        ++stats.interactableInstanceCount;
    }
    if (instance.ticking)
    {
        ++stats.tickingInstanceCount;
    }
    if (!instance.sourceModel.empty())
    {
        ++stats.sourceModelInstanceCount;
    }
    if (!instance.modelAsset.empty())
    {
        ++stats.modelAssetInstanceCount;
    }
    if (!instance.visualId.empty())
    {
        ++stats.visualIdInstanceCount;
    }
    if (!instance.sourceModel.empty() && instance.modelAsset.empty())
    {
        ++stats.sourceModelWithoutModelAssetCount;
    }

    switch (instance.kind)
    {
    case Mm9DatObjectPresentationKind::Actor:
        ++stats.actorInstanceCount;
        break;
    case Mm9DatObjectPresentationKind::Prop:
        ++stats.propInstanceCount;
        break;
    case Mm9DatObjectPresentationKind::Pickup:
        ++stats.pickupInstanceCount;
        break;
    case Mm9DatObjectPresentationKind::Light:
        ++stats.lightInstanceCount;
        break;
    case Mm9DatObjectPresentationKind::Mechanism:
        ++stats.mechanismInstanceCount;
        break;
    case Mm9DatObjectPresentationKind::Object:
        ++stats.genericObjectInstanceCount;
        break;
    }
}

Mm9DatPreparedRenderVertex preparedVertex(const Mm9DatRenderVertex &vertex)
{
    return {
        vertex.x,
        vertex.y,
        vertex.z,
        vertex.uPixels,
        vertex.vPixels,
    };
}

bool appendPreparedTriangle(
    Mm9DatPreparedRenderWorld &preparedRenderWorld,
    Mm9DatPreparedRenderSection &section,
    const Mm9DatRenderTriangle &triangle)
{
    if (preparedRenderWorld.vertices.size() > static_cast<size_t>(std::numeric_limits<uint32_t>::max()) - 3)
    {
        return false;
    }

    const uint32_t baseVertex = static_cast<uint32_t>(preparedRenderWorld.vertices.size());
    for (const Mm9DatRenderVertex &vertex : triangle.vertices)
    {
        preparedRenderWorld.vertices.push_back(preparedVertex(vertex));
        includePoint(section.bounds, vertexPosition(vertex));
    }

    preparedRenderWorld.indices.push_back(baseVertex);
    preparedRenderWorld.indices.push_back(baseVertex + 1);
    preparedRenderWorld.indices.push_back(baseVertex + 2);
    section.vertexCount += 3;
    section.indexCount += 3;
    return true;
}

void finishPreparedRenderWorldStats(Mm9DatPreparedRenderWorld &preparedRenderWorld)
{
    preparedRenderWorld.stats = {};
    preparedRenderWorld.stats.sectionCount = preparedRenderWorld.sections.size();
    preparedRenderWorld.stats.vertexCount = preparedRenderWorld.vertices.size();
    preparedRenderWorld.stats.indexCount = preparedRenderWorld.indices.size();
    preparedRenderWorld.stats.triangleCount = preparedRenderWorld.indices.size() / 3;

    for (Mm9DatPreparedRenderSection &section : preparedRenderWorld.sections)
    {
        finishBounds(section.bounds);

        const size_t triangleCount = section.indexCount / 3;
        if (section.dynamic)
        {
            ++preparedRenderWorld.stats.dynamicSectionCount;
            preparedRenderWorld.stats.dynamicTriangleCount += triangleCount;
        }
        else
        {
            ++preparedRenderWorld.stats.staticSectionCount;
            preparedRenderWorld.stats.staticTriangleCount += triangleCount;
        }

        if (section.blendMode == Mm9DatRenderPartitionBlendMode::Opaque)
        {
            ++preparedRenderWorld.stats.opaqueSectionCount;
        }
        else
        {
            ++preparedRenderWorld.stats.translucentSectionCount;
        }
    }
}

std::string preparedDynamicSectionKey(
    const Mm9DatMechanismRenderBatch &batch,
    const std::string &materialKey,
    Mm9DatRenderPartitionBlendMode blendMode,
    uint32_t flags)
{
    const uint32_t passFlags =
        flags
        & (Mm9DatRenderFilterVisual | Mm9DatRenderFilterSky | Mm9DatRenderFilterWater
            | Mm9DatRenderFilterVisibleWater | Mm9DatRenderFilterTerrain | Mm9DatRenderFilterMovable);
    return std::to_string(batch.mechanismHandle) + "|" + std::to_string(batch.sourceModelIndex) + "|"
        + std::to_string(static_cast<int>(blendMode)) + "|" + std::to_string(passFlags) + "|" + materialKey;
}

void fillMechanismCollisionBatchTriangles(
    Mm9DatMechanismCollisionBatch &batch,
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismInstance &mechanism)
{
    batch.motion = mechanism.motion;
    batch.currentBounds = mechanism.currentBounds;
    batch.transformedTriangles.clear();
    batch.transformedTriangles.reserve(batch.sourceTriangleIndices.size());

    for (size_t triangleIndex : batch.sourceTriangleIndices)
    {
        if (triangleIndex >= mesh.triangles.size())
        {
            continue;
        }

        batch.transformedTriangles.push_back(
            transformMm9DatMechanismPreviewTriangle(mesh.triangles[triangleIndex], mechanism.motion));
    }
}

void recomputeMechanismCollisionCacheStats(Mm9DatMechanismCollisionCache &cache)
{
    cache.stats = {};
    cache.stats.batchCount = cache.batches.size();
    cache.stats.indexedBatchCount = cache.batchIndexByMechanismHandle.size();

    for (const Mm9DatMechanismCollisionBatch &batch : cache.batches)
    {
        ++cache.stats.activeMechanismCount;
        cache.stats.sourceTriangleCount += batch.sourceTriangleIndices.size();
        cache.stats.transformedTriangleCount += batch.transformedTriangles.size();
    }
}

std::string datRuntimeObjectSourceName(const Mm9DatObject &object)
{
    for (const Mm9DatObjectProperty &property : object.properties)
    {
        if (property.decoded
            && property.type == Mm9DatObjectPropertyType::String
            && lowerCopy(property.name) == "name"
            && !property.stringValue.empty())
        {
            return property.stringValue;
        }
    }

    return object.className + std::to_string(object.sourceObjectIndex);
}

std::optional<Mm9LightSourceProperty> lightSourcePropertyFromDatProperty(
    const Mm9DatObjectProperty &property)
{
    if (!property.decoded)
    {
        return std::nullopt;
    }

    switch (property.type)
    {
    case Mm9DatObjectPropertyType::String:
        return mm9LightStringProperty(property.name, property.stringValue);
    case Mm9DatObjectPropertyType::Vector:
    case Mm9DatObjectPropertyType::Color:
        return mm9LightVec3Property(property.name, property.vectorValue);
    case Mm9DatObjectPropertyType::Real:
        return mm9LightNumberProperty(property.name, property.floatValue);
    case Mm9DatObjectPropertyType::Flags:
    case Mm9DatObjectPropertyType::LongInt:
        return mm9LightIntegerProperty(property.name, property.intValue);
    case Mm9DatObjectPropertyType::Bool:
        return mm9LightBooleanProperty(property.name, property.boolValue);
    case Mm9DatObjectPropertyType::Rotation:
        return mm9LightVec3Property(
            property.name,
            {property.rotationValue[0], property.rotationValue[1], property.rotationValue[2]});
    case Mm9DatObjectPropertyType::Unknown:
        return std::nullopt;
    }

    return std::nullopt;
}

std::optional<Mm9SkySourceProperty> skySourcePropertyFromDatProperty(
    const Mm9DatObjectProperty &property)
{
    if (!property.decoded)
    {
        return std::nullopt;
    }

    switch (property.type)
    {
    case Mm9DatObjectPropertyType::String:
        return mm9SkyStringProperty(property.name, property.stringValue);
    case Mm9DatObjectPropertyType::Vector:
    case Mm9DatObjectPropertyType::Color:
        return mm9SkyVec3Property(property.name, property.vectorValue);
    case Mm9DatObjectPropertyType::Real:
        return mm9SkyNumberProperty(property.name, property.floatValue);
    case Mm9DatObjectPropertyType::Flags:
    case Mm9DatObjectPropertyType::LongInt:
        return mm9SkyIntegerProperty(property.name, property.intValue);
    case Mm9DatObjectPropertyType::Bool:
        return mm9SkyIntegerProperty(property.name, property.boolValue ? 1 : 0);
    case Mm9DatObjectPropertyType::Rotation:
        return mm9SkyVec3Property(
            property.name,
            {property.rotationValue[0], property.rotationValue[1], property.rotationValue[2]});
    case Mm9DatObjectPropertyType::Unknown:
        return std::nullopt;
    }

    return std::nullopt;
}

std::vector<Mm9LightSourceObject> buildMm9LightSourceObjectsFromDatObjects(
    const std::vector<Mm9DatObject> &objects)
{
    std::vector<Mm9LightSourceObject> sourceObjects;
    sourceObjects.reserve(objects.size());

    for (const Mm9DatObject &object : objects)
    {
        Mm9LightSourceObject sourceObject = {};
        sourceObject.sourceObjectIndex = object.sourceObjectIndex;
        sourceObject.sourceClass = object.className;
        sourceObject.sourceName = datRuntimeObjectSourceName(object);
        sourceObject.properties.reserve(object.properties.size());

        for (const Mm9DatObjectProperty &property : object.properties)
        {
            const std::optional<Mm9LightSourceProperty> lightProperty =
                lightSourcePropertyFromDatProperty(property);
            if (lightProperty)
            {
                sourceObject.properties.push_back(*lightProperty);
            }
        }

        sourceObjects.push_back(std::move(sourceObject));
    }

    return sourceObjects;
}

std::vector<Mm9SkySourceObject> buildMm9SkySourceObjectsFromDatObjects(
    const std::vector<Mm9DatObject> &objects)
{
    std::vector<Mm9SkySourceObject> sourceObjects;
    sourceObjects.reserve(objects.size());

    for (const Mm9DatObject &object : objects)
    {
        Mm9SkySourceObject sourceObject = {};
        sourceObject.sourceObjectIndex = object.sourceObjectIndex;
        sourceObject.sourceClass = object.className;
        sourceObject.sourceName = datRuntimeObjectSourceName(object);
        sourceObject.properties.reserve(object.properties.size());

        for (const Mm9DatObjectProperty &property : object.properties)
        {
            const std::optional<Mm9SkySourceProperty> skyProperty =
                skySourcePropertyFromDatProperty(property);
            if (skyProperty)
            {
                sourceObject.properties.push_back(*skyProperty);
            }
        }

        sourceObjects.push_back(std::move(sourceObject));
    }

    return sourceObjects;
}

void addLightDiagnostics(Mm9DatWorldRuntime &runtime)
{
    for (const Mm9LightLayerDiagnostic &diagnostic : runtime.lightLayer.diagnostics)
    {
        runtime.diagnostics.push_back(
            "MM9 DAT light object "
            + std::to_string(diagnostic.sourceObjectIndex)
            + " "
            + diagnostic.propertyName
            + ": "
            + diagnostic.message);
    }
}

void addSkyDiagnostics(Mm9DatWorldRuntime &runtime)
{
    for (const Mm9SkyLayerDiagnostic &diagnostic : runtime.skyLayer.diagnostics)
    {
        runtime.diagnostics.push_back(
            "MM9 DAT sky object "
            + std::to_string(diagnostic.sourceObjectIndex)
            + " "
            + diagnostic.propertyName
            + ": "
            + diagnostic.message);
    }
}
}

Mm9DatRenderWorld buildMm9DatRenderWorld(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatRenderFilterResult &filters,
    const std::vector<Mm9DatRenderMaterialAssignment> &materialAssignments,
    const std::vector<size_t> &dynamicSourceModelIndices)
{
    Mm9DatRenderWorld renderWorld = {};
    renderWorld.stats.sourceTriangleCount = mesh.triangles.size();

    const std::vector<const Mm9DatRenderFilterEntry *> filterLookup = filtersByTriangle(mesh, filters);
    const std::vector<const Mm9DatRenderMaterialAssignment *> materialLookup =
        assignmentsByTriangle(mesh, materialAssignments);
    std::unordered_map<std::string, size_t> partitionIndexByKey;
    const std::unordered_set<size_t> dynamicSourceModels = sourceModelSet(dynamicSourceModelIndices);

    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        const Mm9DatRenderTriangle &triangle = mesh.triangles[triangleIndex];
        if (dynamicSourceModels.find(triangle.sourceModelIndex) != dynamicSourceModels.end())
        {
            ++renderWorld.stats.dynamicMechanismSkippedTriangleCount;
            continue;
        }

        const Mm9DatRenderFilterEntry *pFilter = filterLookup[triangleIndex];

        if (pFilter == nullptr || !isNormalRuntimeVisual(pFilter->flags))
        {
            if (pFilter != nullptr && (pFilter->flags & Mm9DatRenderFilterWaterVolume) != 0)
            {
                ++renderWorld.stats.waterVolumeSkippedTriangleCount;
            }
            ++renderWorld.stats.helperSkippedTriangleCount;
            continue;
        }

        const Mm9DatRenderMaterialAssignment *pAssignment = materialLookup[triangleIndex];
        const std::string materialKey = materialKeyForTriangle(triangle, pAssignment);
        const Mm9DatRenderPartitionBlendMode blendMode =
            isTranslucentMaterial(triangle)
                ? Mm9DatRenderPartitionBlendMode::Translucent
                : Mm9DatRenderPartitionBlendMode::Opaque;
        const std::string key = partitionKey(triangle.sourceModelIndex, materialKey, blendMode, pFilter->flags);
        auto partitionIterator = partitionIndexByKey.find(key);

        if (partitionIterator == partitionIndexByKey.end())
        {
            Mm9DatRenderPartition partition = {};
            partition.partitionIndex = renderWorld.partitions.size();
            partition.sourceModelIndex = triangle.sourceModelIndex;
            partition.materialKey = materialKey;
            partition.filterFlags = pFilter->flags;
            partition.blendMode = blendMode;
            renderWorld.partitions.push_back(std::move(partition));
            partitionIterator =
                partitionIndexByKey.emplace(key, renderWorld.partitions.size() - 1).first;

            if (blendMode == Mm9DatRenderPartitionBlendMode::Opaque)
            {
                ++renderWorld.stats.opaquePartitionCount;
            }
            else
            {
                ++renderWorld.stats.translucentPartitionCount;
            }
        }

        Mm9DatRenderPartition &partition = renderWorld.partitions[partitionIterator->second];
        partition.triangleIndices.push_back(triangleIndex);

        for (const Mm9DatRenderVertex &vertex : triangle.vertices)
        {
            includePoint(partition.bounds, vertexPosition(vertex));
        }

        if (pAssignment == nullptr || !pAssignment->assigned || !pAssignment->sourceDtxResolved)
        {
            ++renderWorld.stats.missingMaterialTriangleCount;
        }

        ++renderWorld.stats.normalVisualTriangleCount;
        if ((pFilter->flags & Mm9DatRenderFilterVisibleWater) != 0)
        {
            ++renderWorld.stats.visibleWaterTriangleCount;
        }
    }

    for (Mm9DatRenderPartition &partition : renderWorld.partitions)
    {
        finishBounds(partition.bounds);
    }

    renderWorld.stats.partitionCount = renderWorld.partitions.size();
    return renderWorld;
}

Mm9DatMechanismRenderWorld buildMm9DatMechanismRenderWorld(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismRuntime &mechanismRuntime)
{
    Mm9DatMechanismRenderWorld renderWorld = {};

    for (const Mm9DatMechanismInstance &mechanism : mechanismRuntime.mechanisms)
    {
        if (!mechanism.active || mechanism.inert)
        {
            continue;
        }

        Mm9DatMechanismRenderBatch batch = {};
        batch.mechanismHandle = mechanism.handle;
        batch.mechanismId = mechanism.mechanismId;
        batch.objectId = mechanism.objectId;
        batch.sourceModelIndex = mechanism.sourceModelIndex;
        batch.sourceModelName = mechanism.sourceModelName;
        batch.motion = mechanism.motion;
        batch.currentBounds = mechanism.currentBounds;

        for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
        {
            if (mesh.triangles[triangleIndex].sourceModelIndex == mechanism.sourceModelIndex)
            {
                batch.triangleIndices.push_back(triangleIndex);
            }
        }

        if (batch.triangleIndices.empty())
        {
            continue;
        }

        ++renderWorld.stats.activeMechanismCount;
        renderWorld.stats.sourceTriangleCount += batch.triangleIndices.size();
        renderWorld.stats.transformedTriangleCount += batch.triangleIndices.size();
        renderWorld.batches.push_back(std::move(batch));
    }

    renderWorld.stats.batchCount = renderWorld.batches.size();
    return renderWorld;
}

void updateMm9DatMechanismRenderWorldTransforms(
    Mm9DatMechanismRenderWorld &renderWorld,
    const Mm9DatMechanismRuntime &mechanismRuntime)
{
    std::unordered_map<uint32_t, const Mm9DatMechanismInstance *> mechanismsByHandle;

    for (const Mm9DatMechanismInstance &mechanism : mechanismRuntime.mechanisms)
    {
        mechanismsByHandle[mechanism.handle] = &mechanism;
    }

    for (Mm9DatMechanismRenderBatch &batch : renderWorld.batches)
    {
        const auto mechanismIterator = mechanismsByHandle.find(batch.mechanismHandle);
        if (mechanismIterator == mechanismsByHandle.end())
        {
            continue;
        }

        const Mm9DatMechanismInstance &mechanism = *mechanismIterator->second;
        batch.motion = mechanism.motion;
        batch.currentBounds = mechanism.currentBounds;
    }
}

Mm9DatPreparedRenderWorld buildMm9DatPreparedRenderWorld(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatRenderWorld &renderWorld,
    const Mm9DatMechanismRenderWorld &mechanismRenderWorld,
    const Mm9DatRenderFilterResult &filters,
    const std::vector<Mm9DatRenderMaterialAssignment> &materialAssignments)
{
    Mm9DatPreparedRenderWorld preparedRenderWorld = {};
    preparedRenderWorld.sections.reserve(renderWorld.partitions.size() + mechanismRenderWorld.batches.size());
    preparedRenderWorld.vertices.reserve(
        (renderWorld.stats.normalVisualTriangleCount + mechanismRenderWorld.stats.transformedTriangleCount) * 3);
    preparedRenderWorld.indices.reserve(
        (renderWorld.stats.normalVisualTriangleCount + mechanismRenderWorld.stats.transformedTriangleCount) * 3);

    for (const Mm9DatRenderPartition &partition : renderWorld.partitions)
    {
        Mm9DatPreparedRenderSection section = {};
        section.sectionIndex = preparedRenderWorld.sections.size();
        section.dynamic = false;
        section.sourceModelIndex = partition.sourceModelIndex;
        section.materialKey = partition.materialKey;
        section.filterFlags = partition.filterFlags;
        section.blendMode = partition.blendMode;
        section.vertexStart = preparedRenderWorld.vertices.size();
        section.indexStart = preparedRenderWorld.indices.size();
        section.sourceTriangleIndices.reserve(partition.triangleIndices.size());

        for (size_t triangleIndex : partition.triangleIndices)
        {
            if (triangleIndex >= mesh.triangles.size())
            {
                continue;
            }

            if (!appendPreparedTriangle(preparedRenderWorld, section, mesh.triangles[triangleIndex]))
            {
                continue;
            }

            section.sourceTriangleIndices.push_back(triangleIndex);
            if (section.sourceModelName.empty())
            {
                section.sourceModelName = mesh.triangles[triangleIndex].sourceModelName;
            }
        }

        if (section.indexCount != 0)
        {
            preparedRenderWorld.sections.push_back(std::move(section));
        }
    }

    const std::vector<const Mm9DatRenderFilterEntry *> filterLookup = filtersByTriangle(mesh, filters);
    const std::vector<const Mm9DatRenderMaterialAssignment *> materialLookup =
        assignmentsByTriangle(mesh, materialAssignments);
    std::unordered_map<std::string, size_t> sectionIndexByKey;

    for (const Mm9DatMechanismRenderBatch &batch : mechanismRenderWorld.batches)
    {
        for (size_t triangleIndex : batch.triangleIndices)
        {
            if (triangleIndex >= mesh.triangles.size())
            {
                continue;
            }

            const Mm9DatRenderFilterEntry *pFilter = filterLookup[triangleIndex];
            if (pFilter == nullptr || !isNormalRuntimeVisual(pFilter->flags))
            {
                continue;
            }

            const Mm9DatRenderTriangle &sourceTriangle = mesh.triangles[triangleIndex];
            const Mm9DatRenderTriangle transformedTriangle =
                transformMm9DatMechanismPreviewTriangle(sourceTriangle, batch.motion);
            const Mm9DatRenderMaterialAssignment *pAssignment = materialLookup[triangleIndex];
            const std::string materialKey = materialKeyForTriangle(sourceTriangle, pAssignment);
            const Mm9DatRenderPartitionBlendMode blendMode =
                isTranslucentMaterial(sourceTriangle)
                    ? Mm9DatRenderPartitionBlendMode::Translucent
                    : Mm9DatRenderPartitionBlendMode::Opaque;
            const std::string key =
                preparedDynamicSectionKey(batch, materialKey, blendMode, pFilter->flags);
            auto sectionIterator = sectionIndexByKey.find(key);

            if (sectionIterator == sectionIndexByKey.end())
            {
                Mm9DatPreparedRenderSection section = {};
                section.sectionIndex = preparedRenderWorld.sections.size();
                section.dynamic = true;
                section.mechanismHandle = batch.mechanismHandle;
                section.mechanismId = batch.mechanismId;
                section.objectId = batch.objectId;
                section.sourceModelIndex = batch.sourceModelIndex;
                section.sourceModelName = batch.sourceModelName;
                section.materialKey = materialKey;
                section.filterFlags = pFilter->flags;
                section.blendMode = blendMode;
                section.vertexStart = preparedRenderWorld.vertices.size();
                section.indexStart = preparedRenderWorld.indices.size();
                preparedRenderWorld.sections.push_back(std::move(section));
                sectionIterator =
                    sectionIndexByKey.emplace(key, preparedRenderWorld.sections.size() - 1).first;
            }

            Mm9DatPreparedRenderSection &section = preparedRenderWorld.sections[sectionIterator->second];
            if (!appendPreparedTriangle(preparedRenderWorld, section, transformedTriangle))
            {
                continue;
            }

            section.sourceTriangleIndices.push_back(triangleIndex);
        }
    }

    finishPreparedRenderWorldStats(preparedRenderWorld);
    return preparedRenderWorld;
}

void updateMm9DatPreparedMechanismRenderWorld(
    Mm9DatPreparedRenderWorld &preparedRenderWorld,
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismRenderWorld &mechanismRenderWorld)
{
    std::unordered_map<uint32_t, const Mm9DatMechanismRenderBatch *> batchesByHandle;

    for (const Mm9DatMechanismRenderBatch &batch : mechanismRenderWorld.batches)
    {
        batchesByHandle[batch.mechanismHandle] = &batch;
    }

    for (Mm9DatPreparedRenderSection &section : preparedRenderWorld.sections)
    {
        if (!section.dynamic || section.mechanismHandle == 0)
        {
            continue;
        }

        const auto batchIterator = batchesByHandle.find(section.mechanismHandle);
        if (batchIterator == batchesByHandle.end())
        {
            continue;
        }

        const Mm9DatMechanismRenderBatch &batch = *batchIterator->second;
        section.bounds = {};
        section.mechanismId = batch.mechanismId;
        section.objectId = batch.objectId;
        section.sourceModelIndex = batch.sourceModelIndex;
        section.sourceModelName = batch.sourceModelName;

        for (size_t triangleOffset = 0; triangleOffset < section.sourceTriangleIndices.size(); ++triangleOffset)
        {
            const size_t sourceTriangleIndex = section.sourceTriangleIndices[triangleOffset];
            const size_t preparedVertexIndex = section.vertexStart + triangleOffset * 3;
            if (sourceTriangleIndex >= mesh.triangles.size()
                || preparedVertexIndex + 2 >= preparedRenderWorld.vertices.size())
            {
                continue;
            }

            const Mm9DatRenderTriangle transformedTriangle =
                transformMm9DatMechanismPreviewTriangle(mesh.triangles[sourceTriangleIndex], batch.motion);
            for (size_t vertexIndex = 0; vertexIndex < transformedTriangle.vertices.size(); ++vertexIndex)
            {
                preparedRenderWorld.vertices[preparedVertexIndex + vertexIndex] =
                    preparedVertex(transformedTriangle.vertices[vertexIndex]);
                includePoint(section.bounds, vertexPosition(transformedTriangle.vertices[vertexIndex]));
            }
        }

        finishBounds(section.bounds);
    }
}

Mm9DatRuntimeMaterialTable buildMm9DatRuntimeMaterialTable(
    Mm9DatPreparedRenderWorld &preparedRenderWorld)
{
    Mm9DatRuntimeMaterialTable table = {};
    std::unordered_map<std::string, size_t> materialIndexByKey;

    for (Mm9DatPreparedRenderSection &section : preparedRenderWorld.sections)
    {
        const std::string materialKey = section.materialKey.empty() ? "missing" : section.materialKey;
        const std::unordered_map<std::string, size_t>::const_iterator existingMaterial =
            materialIndexByKey.find(materialKey);
        if (existingMaterial != materialIndexByKey.end())
        {
            section.materialIndex = existingMaterial->second;
            continue;
        }

        Mm9DatRuntimeMaterial material = {};
        material.materialIndex = table.materials.size();
        material.materialKey = materialKey;
        material.missing = materialKey == "missing";
        material.sourceTextureMaterial = startsWith(materialKey, "source:");
        material.resolvedMaterial = !material.missing && !material.sourceTextureMaterial;

        if (material.sourceTextureMaterial)
        {
            material.sourceTexture = materialKey.substr(std::string("source:").size());
        }
        else if (material.resolvedMaterial)
        {
            material.resolvedSourcePath = materialKey;
        }

        material.textureCacheEligible =
            !material.missing
            && (!material.sourceTexture.empty() || !material.resolvedSourcePath.empty());
        section.materialIndex = material.materialIndex;
        materialIndexByKey.emplace(materialKey, material.materialIndex);
        table.materials.push_back(std::move(material));
    }

    table.stats.materialCount = table.materials.size();
    for (const Mm9DatRuntimeMaterial &material : table.materials)
    {
        if (material.sourceTextureMaterial)
        {
            ++table.stats.sourceTextureMaterialCount;
        }

        if (material.resolvedMaterial)
        {
            ++table.stats.resolvedMaterialCount;
        }

        if (material.missing)
        {
            ++table.stats.missingMaterialCount;
        }

        if (material.textureCacheEligible)
        {
            ++table.stats.textureCacheEligibleCount;
        }
    }

    return table;
}

Mm9DatRuntimeTextureCatalog buildMm9DatRuntimeTextureCatalog(
    const std::vector<std::filesystem::path> &sourceRoots)
{
    Mm9DatRuntimeTextureCatalog catalog = {};
    catalog.sourceRoots = sourceRoots;
    catalog.stats.sourceRootCount = sourceRoots.size();

    for (const std::filesystem::path &sourceRoot : sourceRoots)
    {
        std::error_code errorCode;
        if (!std::filesystem::is_directory(sourceRoot, errorCode) || errorCode)
        {
            continue;
        }

        const std::string sourceRootNameKey =
            normalizeTextureCatalogKey(sourceRoot.filename().generic_string());
        const bool addFamilyPrefixKeys = isKnownTextureFamilyRootName(sourceRootNameKey);
        std::filesystem::recursive_directory_iterator iterator(sourceRoot, errorCode);
        const std::filesystem::recursive_directory_iterator endIterator;

        while (!errorCode && iterator != endIterator)
        {
            const std::filesystem::directory_entry entry = *iterator;
            iterator.increment(errorCode);

            if (!entry.is_regular_file(errorCode) || errorCode)
            {
                errorCode.clear();
                continue;
            }

            ++catalog.stats.scannedFileCount;
            const std::filesystem::path physicalPath = entry.path();
            if (!isDtxTexturePath(physicalPath))
            {
                continue;
            }

            ++catalog.stats.dtxFileCount;
            Mm9DatRuntimeTextureCatalogEntry catalogEntry = {};
            catalogEntry.catalogEntryIndex = catalog.entries.size();
            catalogEntry.physicalPath = physicalPath.lexically_normal();
            catalogEntry.relativePathKey = normalizeTextureCatalogKey(
                physicalPath.lexically_relative(sourceRoot).generic_string());
            catalogEntry.fileNameKey = normalizeTextureCatalogKey(physicalPath.filename().generic_string());
            catalogEntry.stemKey = normalizeTextureCatalogKey(physicalPath.stem().generic_string());

            addTextureCatalogKey(catalog, catalogEntry.relativePathKey, catalogEntry.catalogEntryIndex);
            if (addFamilyPrefixKeys)
            {
                addTextureCatalogKey(
                    catalog,
                    sourceRootNameKey + "/" + catalogEntry.relativePathKey,
                    catalogEntry.catalogEntryIndex);
            }
            addTextureCatalogKey(catalog, catalogEntry.fileNameKey, catalogEntry.catalogEntryIndex);
            addTextureCatalogKey(catalog, catalogEntry.stemKey, catalogEntry.catalogEntryIndex);
            catalog.entries.push_back(std::move(catalogEntry));
        }
    }

    catalog.stats.catalogEntryCount = catalog.entries.size();
    catalog.stats.catalogKeyCount = catalog.entryIndexByKey.size();
    return catalog;
}

Mm9DatRuntimeTextureBindings bindMm9DatRuntimeTextures(
    const Mm9DatRuntimeMaterialTable &materialTable,
    const Mm9DatRuntimeTextureCatalog &textureCatalog)
{
    Mm9DatRuntimeTextureBindings bindings = {};
    bindings.bindings.reserve(materialTable.materials.size());

    for (const Mm9DatRuntimeMaterial &material : materialTable.materials)
    {
        if (!material.textureCacheEligible)
        {
            continue;
        }

        ++bindings.stats.materialLookupCount;
        Mm9DatRuntimeTextureBinding binding = {};
        binding.materialIndex = material.materialIndex;
        binding.materialKey = material.materialKey;
        binding.sourceTexture =
            !material.sourceTexture.empty() ? material.sourceTexture : material.resolvedSourcePath;

        const std::optional<size_t> catalogEntryIndex =
            findTextureCatalogEntry(textureCatalog, binding.sourceTexture);
        if (catalogEntryIndex.has_value() && *catalogEntryIndex < textureCatalog.entries.size())
        {
            const Mm9DatRuntimeTextureCatalogEntry &entry = textureCatalog.entries[*catalogEntryIndex];
            binding.catalogEntryIndex = *catalogEntryIndex;
            binding.physicalPath = entry.physicalPath;
            binding.resolved = true;
            ++bindings.stats.resolvedMaterialCount;
        }
        else
        {
            binding.missing = true;
            ++bindings.stats.missingMaterialCount;
        }

        bindings.bindings.push_back(std::move(binding));
    }

    return bindings;
}

Mm9DatRenderSubmissionPlan buildMm9DatRenderSubmissionPlan(
    const Mm9DatPreparedRenderWorld &preparedRenderWorld,
    const Mm9DatRenderSubmissionOptions &options)
{
    Mm9DatRenderSubmissionPlan plan = {};
    plan.stats.sourceSectionCount = preparedRenderWorld.sections.size();
    plan.commands.reserve(preparedRenderWorld.sections.size());

    for (const Mm9DatPreparedRenderSection &section : preparedRenderWorld.sections)
    {
        if (section.indexCount == 0)
        {
            continue;
        }

        if (section.dynamic && !options.includeDynamic)
        {
            continue;
        }

        if (!section.dynamic && !options.includeStatic)
        {
            continue;
        }

        if (section.blendMode == Mm9DatRenderPartitionBlendMode::Opaque && !options.includeOpaque)
        {
            continue;
        }

        if (section.blendMode == Mm9DatRenderPartitionBlendMode::Translucent && !options.includeTranslucent)
        {
            continue;
        }

        if (options.cullByDistance
            && options.maxVisibleDistance > 0.0f
            && section.bounds.valid
            && distance(section.bounds.center, options.viewPosition)
                > options.maxVisibleDistance + section.bounds.radius)
        {
            ++plan.stats.culledSectionCount;
            continue;
        }

        Mm9DatRenderDrawCommand command = {};
        command.sectionIndex = section.sectionIndex;
        command.dynamic = section.dynamic;
        command.mechanismHandle = section.mechanismHandle;
        command.sourceModelIndex = section.sourceModelIndex;
        command.materialKey = section.materialKey;
        command.materialIndex = section.materialIndex;
        command.blendMode = section.blendMode;
        command.vertexStart = section.vertexStart;
        command.vertexCount = section.vertexCount;
        command.indexStart = section.indexStart;
        command.indexCount = section.indexCount;
        command.triangleCount = section.indexCount / 3;
        command.bounds = section.bounds;
        plan.commands.push_back(std::move(command));
    }

    std::stable_sort(
        plan.commands.begin(),
        plan.commands.end(),
        [](const Mm9DatRenderDrawCommand &left, const Mm9DatRenderDrawCommand &right)
        {
            if (left.blendMode != right.blendMode)
            {
                return left.blendMode == Mm9DatRenderPartitionBlendMode::Opaque;
            }

            if (left.dynamic != right.dynamic)
            {
                return !left.dynamic;
            }

            return left.sectionIndex < right.sectionIndex;
        });

    for (size_t commandIndex = 0; commandIndex < plan.commands.size(); ++commandIndex)
    {
        Mm9DatRenderDrawCommand &command = plan.commands[commandIndex];
        command.commandIndex = commandIndex;
        ++plan.stats.drawCallCount;
        ++plan.stats.visibleSectionCount;
        plan.stats.submittedTriangleCount += command.triangleCount;
        plan.stats.submittedIndexCount += command.indexCount;

        if (command.blendMode == Mm9DatRenderPartitionBlendMode::Opaque)
        {
            ++plan.stats.opaqueDrawCallCount;
        }
        else
        {
            ++plan.stats.translucentDrawCallCount;
        }

        if (command.dynamic)
        {
            ++plan.stats.dynamicDrawCallCount;
        }
        else
        {
            ++plan.stats.staticDrawCallCount;
        }

        if (command.materialKey == "missing")
        {
            ++plan.stats.textureMissDrawCallCount;
        }
    }

    return plan;
}

Mm9DatObjectRegistry buildMm9DatObjectRegistry(
    const std::vector<Mm9ScriptedObject> &objects,
    const Mm9DatCollisionWorld &collisionWorld,
    const Mm9DatMechanismRuntime *pMechanismRuntime)
{
    Mm9DatObjectRegistry registry = {};
    registry.pickableObjectCellSize = DefaultObjectPickCellSize;
    registry.collidableObjectCellSize = DefaultObjectPickCellSize;
    registry.actorObjectCellSize = DefaultObjectPickCellSize;
    registry.objects.reserve(objects.size());
    registry.actorIndexByObjectIndex.reserve(objects.size());
    const std::unordered_set<std::string> mechanismIds = mechanismObjectIds(pMechanismRuntime);

    for (size_t objectIndex = 0; objectIndex < objects.size(); ++objectIndex)
    {
        const Mm9ScriptedObject &sourceObject = objects[objectIndex];
        Mm9DatRuntimeObject object = {};
        object.handle = objectHandleForIndex(objectIndex);
        object.sourceObjectIndex = sourceObject.sourceObjectIndex;
        object.objectId = sourceObject.objectId;
        object.sourceClass = sourceObject.sourceClass;
        object.sourceName = sourceObject.sourceName;
        object.sourceModel = sourceObject.sourceModel;
        object.modelAsset = sourceObject.modelAsset;
        object.visualId = sourceObject.visualId;
        object.scriptName = sourceObject.scriptName;
        object.scriptParams = sourceObject.scriptParams;
        object.originalPosition = {sourceObject.x, sourceObject.y, sourceObject.z};
        object.position = object.originalPosition;
        object.radius = sourceObject.radius;
        object.height = sourceObject.height;
        object.visible = sourceObject.visible;
        object.solid = sourceObject.solid;
        object.rayHit = sourceObject.rayHit;
        object.pickable = sourceObject.pickable;
        object.moveToFloor = sourceObject.movement.moveToFloor;
        object.flying = sourceObject.movement.flying;
        object.needsTick = sourceObject.needsTick;

        if (object.moveToFloor && floorPlacementPolicySkipsObject(sourceObject))
        {
            object.placementStatus = Mm9DatObjectPlacementStatus::PolicySkipped;
            object.placementDiagnostic = "move_to_floor_policy_skipped";
        }
        else if (object.moveToFloor)
        {
            Mm9DatFloorSupportQuery query = {};
            query.position = object.position;
            query.channelMask = Mm9DatPhysicsQueryChannelPhysics;
            query.maxDropDistance = DefaultFloorPlacementMaxDrop;
            query.halfHeight = std::max(0.0f, object.height * 0.5f);
            query.placementBias = DefaultFloorPlacementBias;

            const std::optional<Mm9DatFloorSupportHit> support = collisionWorld.findFloorSupport(query);

            if (support)
            {
                object.position = support->adjustedPosition;
                object.placementStatus = Mm9DatObjectPlacementStatus::SnappedToFloor;
                object.floorCandidateTriangleCount = support->candidateTriangleCount;
                object.floorTestedTriangleCount = support->testedTriangleCount;
                object.placementDiagnostic = "snapped_to_floor";
            }
            else
            {
                object.placementStatus = Mm9DatObjectPlacementStatus::UnsupportedMoveToFloor;
                object.placementDiagnostic = "move_to_floor_no_support";
            }
        }

        registry.objects.push_back(std::move(object));
        const size_t runtimeObjectIndex = registry.objects.size() - 1;
        registry.objectIndexByObjectId[registry.objects.back().objectId] = runtimeObjectIndex;
        registry.objectIndexByHandle[registry.objects.back().handle] = runtimeObjectIndex;
        const std::string sourceNameKey = lowerCopy(registry.objects.back().sourceName);
        if (!sourceNameKey.empty())
        {
            registry.objectIndicesBySourceNameLower[sourceNameKey].push_back(runtimeObjectIndex);
        }
        registry.actorIndexByObjectIndex.push_back(InvalidRuntimeIndex);
        addPlacementStats(registry.stats, registry.objects.back());
        addObjectRegistryMembership(registry, runtimeObjectIndex, mechanismIds);
        addObjectToPickableCells(registry, runtimeObjectIndex);
        addObjectToCollidableCells(registry, runtimeObjectIndex);
        addObjectToActorCells(registry, runtimeObjectIndex);
    }

    finishObjectPickableCells(registry);
    finishObjectCollidableCells(registry);
    finishObjectActorCells(registry);
    return registry;
}

Mm9DatObjectPresentationWorld buildMm9DatObjectPresentationWorld(
    const Mm9DatObjectRegistry &registry)
{
    Mm9DatObjectPresentationWorld world = {};
    world.instances.reserve(registry.renderableObjectIndices.size());

    for (size_t objectIndex : registry.renderableObjectIndices)
    {
        if (objectIndex >= registry.objects.size())
        {
            continue;
        }

        const Mm9DatRuntimeObject &object = registry.objects[objectIndex];
        Mm9DatObjectPresentationInstance instance = {};
        instance.instanceIndex = world.instances.size();
        instance.objectIndex = objectIndex;
        instance.objectHandle = object.handle;
        instance.sourceObjectIndex = object.sourceObjectIndex;
        instance.objectId = object.objectId;
        instance.sourceClass = object.sourceClass;
        instance.sourceName = object.sourceName;
        instance.sourceModel = object.sourceModel;
        instance.modelAsset = object.modelAsset;
        instance.visualId = object.visualId;
        instance.position = object.position;
        instance.radius = object.radius;
        instance.height = object.height;
        instance.kind = presentationKindForObject(registry, objectIndex);
        instance.collidable = containsObjectIndex(registry.collidableObjectIndices, objectIndex);
        instance.interactable = containsObjectIndex(registry.interactableObjectIndices, objectIndex);
        instance.ticking = containsObjectIndex(registry.tickingObjectIndices, objectIndex);

        addPresentationStats(world.stats, instance);
        world.instances.push_back(std::move(instance));
    }

    return world;
}

Mm9DatObjectModelRenderPlan buildMm9DatObjectModelRenderPlan(
    const Mm9DatObjectPresentationWorld &presentationWorld,
    const std::vector<Mm9ScriptedObject> &scriptedObjects)
{
    Mm9DatObjectModelRenderPlan plan = {};
    plan.stats.presentationInstanceCount = presentationWorld.instances.size();

    std::unordered_map<size_t, const Mm9ScriptedObject *> scriptedObjectBySourceIndex;
    scriptedObjectBySourceIndex.reserve(scriptedObjects.size());
    for (const Mm9ScriptedObject &object : scriptedObjects)
    {
        scriptedObjectBySourceIndex.emplace(object.sourceObjectIndex, &object);
    }

    plan.instances.reserve(presentationWorld.stats.sourceModelInstanceCount);
    for (const Mm9DatObjectPresentationInstance &presentation : presentationWorld.instances)
    {
        if (presentation.sourceModel.empty() && presentation.modelAsset.empty())
        {
            continue;
        }

        ++plan.stats.candidateInstanceCount;
        if (!presentation.sourceModel.empty())
        {
            ++plan.stats.sourceModelCandidateCount;
        }
        if (!presentation.modelAsset.empty())
        {
            ++plan.stats.modelAssetCandidateCount;
        }

        const auto scriptedIterator = scriptedObjectBySourceIndex.find(presentation.sourceObjectIndex);
        if (scriptedIterator == scriptedObjectBySourceIndex.end())
        {
            ++plan.stats.missingScriptedObjectCount;
            continue;
        }

        ++plan.stats.scriptedObjectMatchCount;

        Mm9DatObjectModelRenderInstance instance = {};
        instance.renderInstanceIndex = plan.instances.size();
        instance.presentationInstanceIndex = presentation.instanceIndex;
        instance.sourceObjectIndex = presentation.sourceObjectIndex;
        instance.objectHandle = presentation.objectHandle;
        instance.runtimePosition = presentation.position;
        instance.object = *scriptedIterator->second;
        instance.object.x = presentation.position.x;
        instance.object.y = presentation.position.z;
        instance.object.z = presentation.position.y;
        instance.object.sourceModel = presentation.sourceModel;
        instance.object.modelAsset = presentation.modelAsset;
        instance.object.visualId = presentation.visualId;
        instance.object.radius = presentation.radius;
        instance.object.height = presentation.height;
        instance.object.visible = true;
        plan.instances.push_back(std::move(instance));
    }

    plan.stats.renderInstanceCount = plan.instances.size();
    return plan;
}

std::vector<size_t> collectMm9DatActorObjectIndicesWithinRadius(
    const Mm9DatObjectRegistry &registry,
    const Mm9DatVec3 &center,
    float radius)
{
    std::vector<size_t> result;
    std::unordered_set<size_t> seenObjectIndices;
    if (radius <= PickEpsilon || registry.actorObjectIndicesByCell.empty())
    {
        return result;
    }

    const float cellSize =
        registry.actorObjectCellSize > PickEpsilon
            ? registry.actorObjectCellSize
            : DefaultObjectPickCellSize;
    const int32_t minCellX = floorCell(center.x - radius, cellSize);
    const int32_t maxCellX = floorCell(center.x + radius, cellSize);
    const int32_t minCellZ = floorCell(center.z - radius, cellSize);
    const int32_t maxCellZ = floorCell(center.z + radius, cellSize);

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
        {
            const auto cellIterator =
                registry.actorObjectIndicesByCell.find(horizontalCellKey(cellX, cellZ));
            if (cellIterator == registry.actorObjectIndicesByCell.end())
            {
                continue;
            }

            for (size_t objectIndex : cellIterator->second)
            {
                if (seenObjectIndices.insert(objectIndex).second)
                {
                    result.push_back(objectIndex);
                }
            }
        }
    }

    return result;
}

Mm9DatMechanismRuntime buildMm9DatMechanismRuntime(
    const Mm9EventsData &events,
    const Mm9DatRenderMesh &renderMesh)
{
    Mm9DatMechanismRuntime runtime = {};
    runtime.stats.mechanismCount = events.mechanisms.size();
    runtime.mechanisms.reserve(events.mechanisms.size());

    for (size_t mechanismIndex = 0; mechanismIndex < events.mechanisms.size(); ++mechanismIndex)
    {
        const Mm9EventMechanism &sourceMechanism = events.mechanisms[mechanismIndex];
        Mm9DatMechanismInstance mechanism = {};
        mechanism.handle = mechanismHandleForIndex(mechanismIndex);
        mechanism.mechanismIndex = mechanismIndex;
        runtime.mechanismIndexByHandle.emplace(mechanism.handle, mechanismIndex);
        mechanism.mechanismId = sourceMechanism.mechanismId;
        mechanism.objectId = sourceMechanism.objectId;
        if (!mechanism.objectId.empty())
        {
            runtime.mechanismIndexByObjectId.emplace(mechanism.objectId, mechanismIndex);
        }
        mechanism.sourceObjectIndex = sourceMechanism.sourceObjectIndex;
        mechanism.sourceClass = sourceMechanism.sourceClass;
        mechanism.sourceName = sourceMechanism.sourceName;
        mechanism.kind = sourceMechanism.kind;
        mechanism.state =
            sourceMechanism.activation.startOpen
                ? Mm9DatMechanismState::Open
                : Mm9DatMechanismState::Closed;
        mechanism.progress = sourceMechanism.activation.startOpen ? 1.0f : 0.0f;
        mechanism.locked = sourceMechanism.activation.locked;
        mechanism.lockOnClose = sourceMechanism.activation.lockOnClose;
        mechanism.pushOpen = sourceMechanism.activation.pushOpen;
        mechanism.touchToOpen = sourceMechanism.activation.touchToOpen;
        mechanism.reopenOnContact = sourceMechanism.activation.reopenOnContact;
        mechanism.moveDelaySeconds =
            sourceMechanism.timing.hasMoveDelaySecondsSource
                ? std::max(0.0f, sourceMechanism.timing.moveDelaySecondsSource)
                : 0.0f;
        mechanism.openWaitSeconds =
            sourceMechanism.timing.hasOpenWaitSecondsSource
                ? std::max(0.0f, sourceMechanism.timing.openWaitSecondsSource)
                : 0.0f;
        if (sourceMechanism.activation.startOpen && mechanism.openWaitSeconds > 0.0f)
        {
            mechanism.openWaitRemainingSeconds = mechanism.openWaitSeconds;
        }
        const float travelDistance = authoredMechanismTravelDistance(sourceMechanism);
        mechanism.openingDurationSeconds =
            mechanismDurationSeconds(travelDistance, sourceMechanism.linear.openSpeedLtPerSecond);
        mechanism.closingDurationSeconds =
            mechanismDurationSeconds(travelDistance, sourceMechanism.linear.closeSpeedLtPerSecond);
        mechanism.triggerOutputs = sourceMechanism.triggerOutputs;
        mechanism.sounds = sourceMechanism.sounds;

        const Mm9EventBinding *pBinding = findBindingForMechanism(events, sourceMechanism);
        if (pBinding == nullptr)
        {
            mechanism.inert = true;
            mechanism.inertReason = "missing_binding";
            ++runtime.stats.unresolvedBindingCount;
            ++runtime.stats.inertMechanismCount;
            runtime.mechanisms.push_back(std::move(mechanism));
            continue;
        }

        const Mm9EventBindingTarget *pTarget = findFirstWorldModelTarget(*pBinding);
        if (pTarget == nullptr || !pTarget->bmodelIndex.has_value())
        {
            mechanism.inert = true;
            mechanism.inertReason = "missing_world_model_target";
            ++runtime.stats.unresolvedTargetCount;
            ++runtime.stats.inertMechanismCount;
            runtime.mechanisms.push_back(std::move(mechanism));
            continue;
        }

        mechanism.sourceModelIndex = *pTarget->bmodelIndex;
        mechanism.sourceModelName =
            !pTarget->bmodelName.empty() ? pTarget->bmodelName : pTarget->sourceModelName;

        Mm9DatMechanismPreviewMotion openMotion = {};
        if (!buildMechanismMotion(sourceMechanism, *pTarget, 1.0f, openMotion))
        {
            mechanism.inert = true;
            mechanism.inertReason = "missing_motion";
            ++runtime.stats.inertMechanismCount;
            runtime.mechanisms.push_back(std::move(mechanism));
            continue;
        }

        mechanism.motion = openMotion;
        mechanism.motion.progress = mechanism.progress;
        mechanism.closedBounds =
            computeMm9DatRenderBoundsForSourceModel(renderMesh, mechanism.sourceModelIndex);
        const Mm9DatMechanismPreviewResult preview =
            buildMm9DatMechanismPreviewMesh(renderMesh, openMotion);
        mechanism.openBounds = preview.previewTargetBounds;
        mechanism.boundsChangeKnown = mechanism.closedBounds.valid && mechanism.openBounds.valid;
        mechanism.boundsChanged = preview.boundsChanged;
        updateMechanismCurrentTransform(mechanism);
        mechanism.active = mechanism.boundsChangeKnown;
        mechanism.inert = !mechanism.active;

        if (!mechanism.active)
        {
            mechanism.inertReason = "missing_target_geometry";
            ++runtime.stats.inertMechanismCount;
        }
        else
        {
            ++runtime.stats.activeMechanismCount;

            if (mechanism.motion.hasLinearMotion)
            {
                ++runtime.stats.linearMotionCount;
            }

            if (mechanism.motion.hasRotationMotion)
            {
                ++runtime.stats.rotationMotionCount;
            }

            if (mechanism.boundsChanged)
            {
                ++runtime.stats.changedBoundsCount;
            }
        }

        runtime.mechanisms.push_back(std::move(mechanism));
        if (mechanismNeedsQueuedUpdate(runtime.mechanisms.back()))
        {
            runtime.mechanisms.back().queuedForUpdate = true;
            runtime.movingMechanismIndices.push_back(runtime.mechanisms.size() - 1);
        }
    }

    return runtime;
}

Mm9DatMechanismBoundsIndex buildMm9DatMechanismBoundsIndex(
    const Mm9DatMechanismRuntime &runtime,
    float cellSize)
{
    Mm9DatMechanismBoundsIndex index = {};
    index.cellSize =
        cellSize > PickEpsilon
            ? cellSize
            : DefaultMechanismBoundsCellSize;
    index.cellKeysByMechanismIndex.resize(runtime.mechanisms.size());

    for (size_t mechanismIndex = 0; mechanismIndex < runtime.mechanisms.size(); ++mechanismIndex)
    {
        addMechanismToBoundsIndexCells(index, runtime, mechanismIndex);
    }

    recomputeMechanismBoundsIndexStats(index);
    return index;
}

void updateMm9DatMechanismBoundsIndex(
    Mm9DatMechanismBoundsIndex &index,
    const Mm9DatMechanismRuntime &runtime,
    const std::vector<size_t> &mechanismIndices)
{
    if (index.cellSize <= PickEpsilon)
    {
        index.cellSize = DefaultMechanismBoundsCellSize;
    }

    if (index.cellKeysByMechanismIndex.size() < runtime.mechanisms.size())
    {
        index.cellKeysByMechanismIndex.resize(runtime.mechanisms.size());
    }

    for (size_t mechanismIndex : mechanismIndices)
    {
        if (mechanismIndex >= runtime.mechanisms.size())
        {
            continue;
        }

        removeMechanismFromBoundsIndexCells(index, mechanismIndex);
        addMechanismToBoundsIndexCells(index, runtime, mechanismIndex);
    }

    recomputeMechanismBoundsIndexStats(index);
}

Mm9DatMechanismCollisionCache buildMm9DatMechanismCollisionCache(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismRuntime &runtime)
{
    Mm9DatMechanismCollisionCache cache = {};

    for (const Mm9DatMechanismInstance &mechanism : runtime.mechanisms)
    {
        if (!mechanism.active || mechanism.inert)
        {
            continue;
        }

        Mm9DatMechanismCollisionBatch batch = {};
        batch.mechanismHandle = mechanism.handle;
        batch.mechanismId = mechanism.mechanismId;
        batch.objectId = mechanism.objectId;
        batch.sourceModelIndex = mechanism.sourceModelIndex;
        batch.sourceModelName = mechanism.sourceModelName;

        for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
        {
            if (mesh.triangles[triangleIndex].sourceModelIndex == mechanism.sourceModelIndex)
            {
                batch.sourceTriangleIndices.push_back(triangleIndex);
            }
        }

        if (batch.sourceTriangleIndices.empty())
        {
            continue;
        }

        fillMechanismCollisionBatchTriangles(batch, mesh, mechanism);
        cache.batchIndexByMechanismHandle[batch.mechanismHandle] = cache.batches.size();
        cache.batches.push_back(std::move(batch));
    }

    recomputeMechanismCollisionCacheStats(cache);
    return cache;
}

void updateMm9DatMechanismCollisionCache(
    Mm9DatMechanismCollisionCache &cache,
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismRuntime &runtime,
    const std::vector<size_t> &mechanismIndices)
{
    for (size_t mechanismIndex : mechanismIndices)
    {
        if (mechanismIndex >= runtime.mechanisms.size())
        {
            continue;
        }

        const Mm9DatMechanismInstance &mechanism = runtime.mechanisms[mechanismIndex];
        Mm9DatMechanismCollisionBatch *pBatch =
            findMechanismCollisionBatch(cache, mechanism.handle);
        if (pBatch != nullptr)
        {
            fillMechanismCollisionBatchTriangles(*pBatch, mesh, mechanism);
        }
    }

    recomputeMechanismCollisionCacheStats(cache);
}

Mm9DatMechanismCommandResult commandMm9DatMechanism(
    Mm9DatMechanismRuntime &runtime,
    uint32_t handle,
    Mm9DatMechanismCommand command,
    bool ignoreLocks)
{
    Mm9DatMechanismCommandResult result = {};
    result.handle = handle;

    size_t mechanismIndex = 0;
    Mm9DatMechanismInstance *pMechanism = findMechanismByHandle(runtime, handle, &mechanismIndex);
    if (pMechanism == nullptr)
    {
        result.status = Mm9DatMechanismCommandStatus::MissingHandle;
        return result;
    }

    Mm9DatMechanismInstance &mechanism = *pMechanism;
    result.mechanismIndex = mechanismIndex;
    result.previousState = mechanism.state;
    result.newState = mechanism.state;
    result.previousProgress = mechanism.progress;
    result.newProgress = mechanism.progress;

    if (!mechanism.active || mechanism.inert)
    {
        result.status = Mm9DatMechanismCommandStatus::Inert;
        return result;
    }

    if (mechanism.locked && !ignoreLocks)
    {
        result.status = Mm9DatMechanismCommandStatus::Locked;
        return result;
    }

    Mm9DatMechanismState requestedState = mechanism.state;
    if (command == Mm9DatMechanismCommand::Open)
    {
        requestedState = Mm9DatMechanismState::Opening;
    }
    else if (command == Mm9DatMechanismCommand::Close)
    {
        requestedState = Mm9DatMechanismState::Closing;
    }
    else if (mechanism.state == Mm9DatMechanismState::Open
        || mechanism.state == Mm9DatMechanismState::Opening)
    {
        requestedState = Mm9DatMechanismState::Closing;
    }
    else
    {
        requestedState = Mm9DatMechanismState::Opening;
    }

    const bool alreadyOpen =
        requestedState == Mm9DatMechanismState::Opening
        && mechanism.state == Mm9DatMechanismState::Open
        && mechanism.progress >= 1.0f;
    const bool alreadyClosed =
        requestedState == Mm9DatMechanismState::Closing
        && mechanism.state == Mm9DatMechanismState::Closed
        && mechanism.progress <= 0.0f;

    if (alreadyOpen || alreadyClosed)
    {
        result.status = Mm9DatMechanismCommandStatus::AlreadyInRequestedState;
        return result;
    }

    mechanism.state = requestedState;
    mechanism.moveDelayRemainingSeconds = mechanism.moveDelaySeconds;
    mechanism.openWaitRemainingSeconds = 0.0f;
    updateMechanismCurrentTransform(mechanism);
    queueMechanismUpdate(runtime, mechanismIndex);
    result.status = Mm9DatMechanismCommandStatus::Applied;
    result.newState = mechanism.state;
    result.newProgress = mechanism.progress;
    result.stateChanged =
        result.previousState != result.newState
        || std::fabs(result.previousProgress - result.newProgress) > 0.0001f;
    return result;
}

Mm9DatMechanismUpdateStats updateMm9DatMechanisms(
    Mm9DatMechanismRuntime &runtime,
    float deltaSeconds)
{
    Mm9DatMechanismUpdateStats stats = {};

    if (deltaSeconds <= 0.0f)
    {
        return stats;
    }

    std::vector<size_t> stillMoving;
    stillMoving.reserve(runtime.movingMechanismIndices.size());

    for (size_t mechanismIndex : runtime.movingMechanismIndices)
    {
        if (mechanismIndex >= runtime.mechanisms.size())
        {
            continue;
        }

        Mm9DatMechanismInstance &mechanism = runtime.mechanisms[mechanismIndex];
        if (!mechanism.active || mechanism.inert)
        {
            mechanism.queuedForUpdate = false;
            continue;
        }

        const float previousProgress = mechanism.progress;
        const bool wasMoving = mechanismIsMoving(mechanism);
        float remainingSeconds = deltaSeconds;

        if (mechanism.moveDelayRemainingSeconds > 0.0f)
        {
            const float consumedSeconds = std::min(mechanism.moveDelayRemainingSeconds, remainingSeconds);
            mechanism.moveDelayRemainingSeconds -= consumedSeconds;
            remainingSeconds -= consumedSeconds;
        }

        if (remainingSeconds <= 0.0f)
        {
            stillMoving.push_back(mechanismIndex);
            continue;
        }

        if (mechanism.state == Mm9DatMechanismState::Open
            && mechanism.openWaitRemainingSeconds > 0.0f)
        {
            const float consumedSeconds = std::min(mechanism.openWaitRemainingSeconds, remainingSeconds);
            mechanism.openWaitRemainingSeconds -= consumedSeconds;
            remainingSeconds -= consumedSeconds;

            if (mechanism.openWaitRemainingSeconds <= 0.0f)
            {
                mechanism.state = Mm9DatMechanismState::Closing;
                mechanism.moveDelayRemainingSeconds = mechanism.moveDelaySeconds;
            }

            if (remainingSeconds <= 0.0f)
            {
                stillMoving.push_back(mechanismIndex);
                continue;
            }
        }

        if (mechanism.moveDelayRemainingSeconds > 0.0f)
        {
            const float consumedSeconds = std::min(mechanism.moveDelayRemainingSeconds, remainingSeconds);
            mechanism.moveDelayRemainingSeconds -= consumedSeconds;
            remainingSeconds -= consumedSeconds;
        }

        if (mechanism.state == Mm9DatMechanismState::Opening)
        {
            const float duration = std::max(MinimumMechanismDurationSeconds, mechanism.openingDurationSeconds);
            mechanism.progress = std::min(1.0f, mechanism.progress + remainingSeconds / duration);

            if (mechanism.progress >= 1.0f)
            {
                mechanism.state = Mm9DatMechanismState::Open;
                mechanism.openWaitRemainingSeconds = mechanism.openWaitSeconds;
                ++stats.completedMechanismCount;
            }
        }
        else if (mechanism.state == Mm9DatMechanismState::Closing)
        {
            const float duration = std::max(MinimumMechanismDurationSeconds, mechanism.closingDurationSeconds);
            mechanism.progress = std::max(0.0f, mechanism.progress - remainingSeconds / duration);

            if (mechanism.progress <= 0.0f)
            {
                mechanism.state = Mm9DatMechanismState::Closed;
                if (mechanism.lockOnClose)
                {
                    mechanism.locked = true;
                }
                ++stats.completedMechanismCount;
            }
        }

        if (wasMoving)
        {
            ++stats.updatedMechanismCount;
        }

        if (std::fabs(previousProgress - mechanism.progress) > 0.0001f)
        {
            updateMechanismCurrentTransform(mechanism);
            if (mechanism.boundsChanged)
            {
                ++stats.changedBoundsCount;
                stats.changedMechanismIndices.push_back(mechanismIndex);
            }
        }

        if (mechanismNeedsQueuedUpdate(mechanism))
        {
            stillMoving.push_back(mechanismIndex);
        }
        else
        {
            mechanism.queuedForUpdate = false;
        }
    }

    runtime.movingMechanismIndices = std::move(stillMoving);
    return stats;
}

Mm9DatMechanismCommandResult commandMm9DatMechanismByObject(
    Mm9DatMechanismRuntime &runtime,
    const std::string &objectId,
    Mm9DatMechanismCommand command,
    bool ignoreLocks)
{
    const auto mechanismIterator = runtime.mechanismIndexByObjectId.find(objectId);
    if (mechanismIterator != runtime.mechanismIndexByObjectId.end()
        && mechanismIterator->second < runtime.mechanisms.size())
    {
        return commandMm9DatMechanism(
            runtime,
            runtime.mechanisms[mechanismIterator->second].handle,
            command,
            ignoreLocks);
    }

    Mm9DatMechanismCommandResult result = {};
    result.status = Mm9DatMechanismCommandStatus::MissingHandle;
    return result;
}

namespace
{
const Mm9DatRuntimeObject *findRuntimeObjectById(
    const Mm9DatObjectRegistry &registry,
    const std::string &objectId)
{
    const auto iterator = registry.objectIndexByObjectId.find(objectId);
    if (iterator == registry.objectIndexByObjectId.end()
        || iterator->second >= registry.objects.size())
    {
        return nullptr;
    }

    return &registry.objects[iterator->second];
}

const Mm9DatRuntimeObject *findRuntimeObjectBySourceName(
    const Mm9DatObjectRegistry &registry,
    const std::string &sourceName,
    size_t *pCandidateCount = nullptr,
    bool *pAmbiguous = nullptr)
{
    if (pCandidateCount != nullptr)
    {
        *pCandidateCount = 0;
    }
    if (pAmbiguous != nullptr)
    {
        *pAmbiguous = false;
    }

    const auto iterator = registry.objectIndicesBySourceNameLower.find(lowerCopy(sourceName));
    if (iterator == registry.objectIndicesBySourceNameLower.end())
    {
        return nullptr;
    }

    if (pCandidateCount != nullptr)
    {
        *pCandidateCount = iterator->second.size();
    }
    if (pAmbiguous != nullptr)
    {
        *pAmbiguous = iterator->second.size() > 1;
    }

    for (size_t objectIndex : iterator->second)
    {
        if (objectIndex < registry.objects.size())
        {
            return &registry.objects[objectIndex];
        }
    }

    return nullptr;
}

const Mm9DatMechanismInstance *findRuntimeMechanismByHandle(
    const Mm9DatMechanismRuntime &runtime,
    uint32_t handle)
{
    const auto iterator = runtime.mechanismIndexByHandle.find(handle);
    if (iterator == runtime.mechanismIndexByHandle.end()
        || iterator->second >= runtime.mechanisms.size())
    {
        return nullptr;
    }

    return &runtime.mechanisms[iterator->second];
}

const Mm9DatMechanismInstance *findRuntimeMechanismByObjectId(
    const Mm9DatMechanismRuntime &runtime,
    const std::string &objectId)
{
    const auto iterator = runtime.mechanismIndexByObjectId.find(objectId);
    if (iterator == runtime.mechanismIndexByObjectId.end()
        || iterator->second >= runtime.mechanisms.size())
    {
        return nullptr;
    }

    return &runtime.mechanisms[iterator->second];
}

void fillMm9DatActivationObject(
    Mm9DatWorldActivationInfo &activation,
    const Mm9DatRuntimeObject &object)
{
    activation.hasObject = true;
    activation.objectHandle = object.handle;
    activation.objectId = object.objectId;
    activation.objectSourceObjectIndex = static_cast<int>(object.sourceObjectIndex);
    activation.objectSourceClass = object.sourceClass;
    activation.objectSourceName = object.sourceName;
    activation.objectSourceModel = object.sourceModel;
    activation.objectScriptName = object.scriptName;
    activation.objectScriptParams = object.scriptParams;
}

void fillMm9DatActivationMechanism(
    Mm9DatWorldActivationInfo &activation,
    const Mm9DatMechanismInstance &mechanism)
{
    activation.hasMechanism = true;
    activation.mechanismHandle = mechanism.handle;
    activation.mechanismId = mechanism.mechanismId;
    if (activation.objectId.empty())
    {
        activation.objectId = mechanism.objectId;
    }
    activation.mechanismSourceObjectIndex = mechanism.sourceObjectIndex;
    activation.mechanismSourceClass = mechanism.sourceClass;
    activation.mechanismSourceName = mechanism.sourceName;
    activation.mechanismKind = mechanism.kind;
    activation.mechanismSourceModelName = mechanism.sourceModelName;
    activation.triggerOutputs = mechanism.triggerOutputs;
    activation.sounds = mechanism.sounds;
}

Mm9DatWorldActivationInfo buildMm9DatWorldActivationInfo(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatWorldPickHit &hit)
{
    Mm9DatWorldActivationInfo activation = {};

    const Mm9DatMechanismInstance *pMechanism = nullptr;
    if (hit.kind == Mm9DatWorldPickHitKind::Mechanism && hit.mechanismHandle != 0)
    {
        pMechanism = findRuntimeMechanismByHandle(runtime.mechanismRuntime, hit.mechanismHandle);
    }
    else if (hit.kind == Mm9DatWorldPickHitKind::Object && !hit.objectId.empty())
    {
        pMechanism = findRuntimeMechanismByObjectId(runtime.mechanismRuntime, hit.objectId);
    }

    if (hit.kind == Mm9DatWorldPickHitKind::Object && !hit.objectId.empty())
    {
        const Mm9DatRuntimeObject *pObject = findRuntimeObjectById(runtime.objectRegistry, hit.objectId);
        if (pObject != nullptr)
        {
            fillMm9DatActivationObject(activation, *pObject);
        }
    }

    if (pMechanism != nullptr)
    {
        fillMm9DatActivationMechanism(activation, *pMechanism);
        if (!pMechanism->objectId.empty() && !activation.hasObject)
        {
            const Mm9DatRuntimeObject *pObject =
                findRuntimeObjectById(runtime.objectRegistry, pMechanism->objectId);
            if (pObject != nullptr)
            {
                fillMm9DatActivationObject(activation, *pObject);
            }
        }
    }

    return activation;
}

std::string selectedMm9DatTriggerPhase(const Mm9DatWorldUseResult &result)
{
    if (result.mechanismCommand.newState == Mm9DatMechanismState::Opening
        || result.mechanismCommand.newState == Mm9DatMechanismState::Open)
    {
        return "open";
    }
    if (result.mechanismCommand.newState == Mm9DatMechanismState::Closing
        || result.mechanismCommand.newState == Mm9DatMechanismState::Closed)
    {
        return "close";
    }

    return "trigger";
}

bool mm9DatTriggerOutputMatchesUsePhase(
    const Mm9EventTriggerOutput &output,
    const std::string &selectedPhase)
{
    const std::string phase = lowerCopy(output.phase);
    return phase == lowerCopy(selectedPhase) || phase == "trigger";
}

std::vector<Mm9DatWorldTriggerDispatch> buildMm9DatWorldTriggerDispatches(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatWorldUseResult &result)
{
    std::vector<Mm9DatWorldTriggerDispatch> dispatches;
    if (!result.activated)
    {
        return dispatches;
    }

    const std::string selectedPhase = selectedMm9DatTriggerPhase(result);
    for (const Mm9EventTriggerOutput &output : result.activation.triggerOutputs)
    {
        if (!mm9DatTriggerOutputMatchesUsePhase(output, selectedPhase))
        {
            continue;
        }

        Mm9DatWorldTriggerDispatch dispatch = {};
        dispatch.phase = output.phase;
        dispatch.slot = output.slot;
        dispatch.sourceObjectId = result.activation.objectId;
        dispatch.sourceMechanismId = result.activation.mechanismId;
        dispatch.targetName = output.targetName;
        dispatch.messageName = output.messageName;

        size_t candidateCount = 0;
        bool ambiguousTarget = false;
        const Mm9DatRuntimeObject *pTarget = findRuntimeObjectById(runtime.objectRegistry, output.targetName);
        if (pTarget == nullptr)
        {
            pTarget = findRuntimeObjectBySourceName(
                runtime.objectRegistry,
                output.targetName,
                &candidateCount,
                &ambiguousTarget);
        }
        else
        {
            candidateCount = 1;
        }

        dispatch.targetCandidateCount = candidateCount;
        dispatch.ambiguousTarget = ambiguousTarget;
        if (pTarget != nullptr)
        {
            dispatch.resolvedTarget = true;
            dispatch.targetHandle = pTarget->objectId;
            dispatch.targetObjectId = pTarget->objectId;
            dispatch.targetObjectHandle = pTarget->handle;
            dispatch.targetSourceObjectIndex = static_cast<int>(pTarget->sourceObjectIndex);
            dispatch.targetSourceClass = pTarget->sourceClass;
            dispatch.targetSourceName = pTarget->sourceName;
        }

        dispatches.push_back(std::move(dispatch));
    }

    return dispatches;
}

void syncMm9DatWorldRuntimeAfterMechanismCommand(
    Mm9DatWorldRuntime &runtime,
    size_t mechanismIndex)
{
    updateMm9DatMechanismBoundsIndex(
        runtime.mechanismBoundsIndex,
        runtime.mechanismRuntime,
        {mechanismIndex});
    updateMm9DatMechanismCollisionCache(
        runtime.mechanismCollisionCache,
        runtime.renderMesh,
        runtime.mechanismRuntime,
        {mechanismIndex});
    runtime.stats.mechanismBoundsCellCount =
        runtime.mechanismBoundsIndex.stats.cellCount;
    runtime.stats.mechanismBoundsCellRefs =
        runtime.mechanismBoundsIndex.stats.mechanismCellRefs;
    runtime.stats.mechanismCollisionBatchCount =
        runtime.mechanismCollisionCache.stats.batchCount;
    runtime.stats.mechanismCollisionTriangleCount =
        runtime.mechanismCollisionCache.stats.transformedTriangleCount;
    updateMm9DatMechanismRenderWorldTransforms(
        runtime.mechanismRenderWorld,
        runtime.mechanismRuntime);
    updateMm9DatPreparedMechanismRenderWorld(
        runtime.preparedRenderWorld,
        runtime.renderMesh,
        runtime.mechanismRenderWorld);
    runtime.renderSubmissionPlan =
        buildMm9DatRenderSubmissionPlan(runtime.preparedRenderWorld);
    runtime.stats.renderDrawCallCount =
        runtime.renderSubmissionPlan.stats.drawCallCount;
    runtime.stats.renderSubmittedTriangleCount =
        runtime.renderSubmissionPlan.stats.submittedTriangleCount;
    runtime.stats.renderTextureMissDrawCallCount =
        runtime.renderSubmissionPlan.stats.textureMissDrawCallCount;
}

bool mechanismOpensOnContact(const Mm9DatMechanismInstance &mechanism)
{
    if (!mechanism.active || mechanism.inert)
    {
        return false;
    }

    if (mechanism.state == Mm9DatMechanismState::Open
        || mechanism.state == Mm9DatMechanismState::Opening)
    {
        return false;
    }

    return mechanism.touchToOpen
        || mechanism.pushOpen
        || (mechanism.reopenOnContact && mechanism.state == Mm9DatMechanismState::Closing);
}

void applyMechanismContactCommand(
    Mm9DatWorldRuntime &runtime,
    Mm9DatPartyMovementResult &movement)
{
    if (!movement.mechanismHit.has_value())
    {
        return;
    }

    const Mm9DatMechanismInstance *pMechanism =
        findRuntimeMechanismByHandle(runtime.mechanismRuntime, movement.mechanismHit->mechanismHandle);
    if (pMechanism == nullptr || !mechanismOpensOnContact(*pMechanism))
    {
        return;
    }

    movement.mechanismContactCommandAttempted = true;
    movement.mechanismContactCommand =
        commandMm9DatMechanism(
            runtime.mechanismRuntime,
            movement.mechanismHit->mechanismHandle,
            Mm9DatMechanismCommand::Open,
            false);

    if (movement.mechanismContactCommand.status == Mm9DatMechanismCommandStatus::Applied)
    {
        syncMm9DatWorldRuntimeAfterMechanismCommand(
            runtime,
            movement.mechanismContactCommand.mechanismIndex);
    }
}
}

Mm9DatWorldUseResult useMm9DatWorldPickedHitRuntime(
    Mm9DatWorldRuntime &runtime,
    const Mm9DatWorldPickHit &hit,
    Mm9DatMechanismCommand command,
    bool ignoreLocks)
{
    Mm9DatWorldUseResult result = {};
    result.picked = true;
    result.hit = hit;
    result.activation = buildMm9DatWorldActivationInfo(runtime, hit);

    if (hit.kind == Mm9DatWorldPickHitKind::Mechanism && hit.mechanismHandle != 0)
    {
        result.commandAttempted = true;
        result.mechanismCommand =
            commandMm9DatMechanism(runtime.mechanismRuntime, hit.mechanismHandle, command, ignoreLocks);
    }
    else if (hit.kind == Mm9DatWorldPickHitKind::Object && !hit.objectId.empty())
    {
        result.commandAttempted = true;
        result.mechanismCommand =
            commandMm9DatMechanismByObject(runtime.mechanismRuntime, hit.objectId, command, ignoreLocks);
    }

    result.activated =
        result.commandAttempted
        && result.mechanismCommand.status == Mm9DatMechanismCommandStatus::Applied;

    if (result.activated)
    {
        result.triggerDispatches = buildMm9DatWorldTriggerDispatches(runtime, result);
        syncMm9DatWorldRuntimeAfterMechanismCommand(runtime, result.mechanismCommand.mechanismIndex);
    }

    return result;
}

Mm9DatWorldUseResult useMm9DatWorldRuntime(
    Mm9DatWorldRuntime &runtime,
    const Mm9DatPickRay &ray,
    const Mm9DatWorldPickOptions &options,
    Mm9DatMechanismCommand command,
    bool ignoreLocks)
{
    const std::optional<Mm9DatWorldPickHit> hit =
        pickMm9DatWorldRuntime(runtime, ray, options);

    if (!hit)
    {
        return {};
    }

    return useMm9DatWorldPickedHitRuntime(runtime, *hit, command, ignoreLocks);
}

Mm9DatWorldRuntimeUpdateStats updateMm9DatWorldRuntime(
    Mm9DatWorldRuntime &runtime,
    float deltaSeconds)
{
    Mm9DatWorldRuntimeUpdateStats stats = {};
    stats.mechanisms = updateMm9DatMechanisms(runtime.mechanismRuntime, deltaSeconds);

    if (stats.mechanisms.updatedMechanismCount != 0
        || stats.mechanisms.completedMechanismCount != 0
        || stats.mechanisms.changedBoundsCount != 0)
    {
        updateMm9DatMechanismBoundsIndex(
            runtime.mechanismBoundsIndex,
            runtime.mechanismRuntime,
            stats.mechanisms.changedMechanismIndices);
        updateMm9DatMechanismCollisionCache(
            runtime.mechanismCollisionCache,
            runtime.renderMesh,
            runtime.mechanismRuntime,
            stats.mechanisms.changedMechanismIndices);
        runtime.stats.mechanismBoundsCellCount =
            runtime.mechanismBoundsIndex.stats.cellCount;
        runtime.stats.mechanismBoundsCellRefs =
            runtime.mechanismBoundsIndex.stats.mechanismCellRefs;
        runtime.stats.mechanismCollisionBatchCount =
            runtime.mechanismCollisionCache.stats.batchCount;
        runtime.stats.mechanismCollisionTriangleCount =
            runtime.mechanismCollisionCache.stats.transformedTriangleCount;
        updateMm9DatMechanismRenderWorldTransforms(
            runtime.mechanismRenderWorld,
            runtime.mechanismRuntime);
        updateMm9DatPreparedMechanismRenderWorld(
            runtime.preparedRenderWorld,
            runtime.renderMesh,
            runtime.mechanismRenderWorld);
        runtime.renderSubmissionPlan =
            buildMm9DatRenderSubmissionPlan(runtime.preparedRenderWorld);
        runtime.stats.renderDrawCallCount =
            runtime.renderSubmissionPlan.stats.drawCallCount;
        runtime.stats.renderSubmittedTriangleCount =
            runtime.renderSubmissionPlan.stats.submittedTriangleCount;
        runtime.stats.renderTextureMissDrawCallCount =
            runtime.renderSubmissionPlan.stats.textureMissDrawCallCount;
        stats.mechanismRenderWorldUpdated = true;
    }

    return stats;
}

Mm9DatPartyMovementResult moveMm9DatParty(
    const Mm9DatCollisionWorld &collisionWorld,
    const Mm9DatPartyMovementStep &step)
{
    Mm9DatPartyMovementResult result = {};
    result.startPosition = step.position;
    result.finalPosition = step.position;

    const float desiredDistance = vectorLength(step.desiredDisplacement);
    if (desiredDistance > 0.0001f && step.wallChannelMask != 0)
    {
        const Mm9DatVec3 desiredEnd = addVec3(step.position, step.desiredDisplacement);
        Mm9DatPhysicsRaycastOptions wallOptions = {};
        wallOptions.channelMask = step.wallChannelMask;
        wallOptions.includeBackfaces = true;

        const std::optional<Mm9DatCollisionRayHit> wallHit =
            collisionWorld.segmentcast(step.position, desiredEnd, wallOptions);

        if (wallHit)
        {
            result.wallHit = wallHit;
            result.blockedByWall = true;
            result.wallCandidateTriangleCount += wallHit->candidateTriangleCount;
            result.wallTestedTriangleCount += wallHit->testedTriangleCount;

            if (step.maxStepHeight > 0.0f
                && step.floorChannelMask != 0
                && step.floorSnapDistance > 0.0f
                && step.desiredDisplacement.y <= step.floorBias)
            {
                const Mm9DatVec3 stepOffset = {0.0f, step.maxStepHeight, 0.0f};
                const Mm9DatVec3 raisedStart = addVec3(step.position, stepOffset);
                const Mm9DatVec3 raisedEnd = addVec3(desiredEnd, stepOffset);
                const std::optional<Mm9DatCollisionRayHit> raisedHit =
                    collisionWorld.segmentcast(raisedStart, raisedEnd, wallOptions);

                if (raisedHit)
                {
                    result.wallCandidateTriangleCount += raisedHit->candidateTriangleCount;
                    result.wallTestedTriangleCount += raisedHit->testedTriangleCount;
                }
                else
                {
                    Mm9DatFloorSupportQuery stepFloorQuery = {};
                    stepFloorQuery.position = raisedEnd;
                    stepFloorQuery.channelMask = step.floorChannelMask;
                    stepFloorQuery.maxDropDistance = step.floorSnapDistance + step.maxStepHeight;
                    stepFloorQuery.halfHeight = std::max(0.0f, step.halfHeight);
                    stepFloorQuery.placementBias = step.floorBias;

                    const std::optional<Mm9DatFloorSupportHit> stepFloorHit =
                        collisionWorld.findFloorSupport(stepFloorQuery);
                    if (stepFloorHit
                        && stepFloorHit->adjustedPosition.y <= step.position.y + step.maxStepHeight + step.floorBias)
                    {
                        result.finalPosition = stepFloorHit->adjustedPosition;
                        result.floorHit = stepFloorHit;
                        result.onGround = true;
                        result.blockedByWall = false;
                        result.steppedUp = true;
                        result.floorCandidateTriangleCount = stepFloorHit->candidateTriangleCount;
                        result.floorTestedTriangleCount = stepFloorHit->testedTriangleCount;
                        result.appliedDisplacement =
                            subtractVec3(result.finalPosition, result.startPosition);
                        return result;
                    }
                }
            }

            const Mm9DatVec3 desiredDirection = normalizedOrZero(step.desiredDisplacement);
            const float safeTravelDistance = std::max(0.0f, wallHit->hit.distance - std::max(0.0f, step.radius));
            result.finalPosition = addVec3(step.position, multiplyVec3(desiredDirection, safeTravelDistance));

            const Mm9DatVec3 remainingDisplacement = subtractVec3(desiredEnd, result.finalPosition);
            const Mm9DatVec3 slideNormal =
                collisionPlaneNormalForDisplacement(remainingDisplacement, wallHit->hit.normal);
            const Mm9DatVec3 slideDisplacement =
                projectMm9DatPhysicsVelocityAlongPlane(remainingDisplacement, slideNormal);

            if (vectorLength(slideDisplacement) > 0.0001f)
            {
                const Mm9DatVec3 slideEnd = addVec3(result.finalPosition, slideDisplacement);
                const std::optional<Mm9DatCollisionRayHit> slideHit =
                    collisionWorld.segmentcast(result.finalPosition, slideEnd, wallOptions);

                if (slideHit)
                {
                    result.wallCandidateTriangleCount += slideHit->candidateTriangleCount;
                    result.wallTestedTriangleCount += slideHit->testedTriangleCount;

                    const Mm9DatVec3 slideDirection = normalizedOrZero(slideDisplacement);
                    const float slideTravelDistance =
                        std::max(0.0f, slideHit->hit.distance - std::max(0.0f, step.radius));
                    result.finalPosition =
                        addVec3(result.finalPosition, multiplyVec3(slideDirection, slideTravelDistance));
                }
                else
                {
                    result.finalPosition = slideEnd;
                    result.slidAlongWall = true;
                }
            }
        }
        else
        {
            result.finalPosition = desiredEnd;
        }
    }
    else
    {
        result.finalPosition = addVec3(step.position, step.desiredDisplacement);
    }

    if (step.floorChannelMask != 0 && step.floorSnapDistance > 0.0f && step.desiredDisplacement.y <= step.floorBias)
    {
        Mm9DatFloorSupportQuery floorQuery = {};
        floorQuery.position = result.finalPosition;
        floorQuery.channelMask = step.floorChannelMask;
        floorQuery.maxDropDistance = step.floorSnapDistance;
        floorQuery.halfHeight = std::max(0.0f, step.halfHeight);
        floorQuery.placementBias = step.floorBias;

        const std::optional<Mm9DatFloorSupportHit> floorHit =
            collisionWorld.findFloorSupport(floorQuery);

        if (floorHit)
        {
            result.floorHit = floorHit;
            result.onGround = true;
            result.finalPosition.y = floorHit->adjustedPosition.y;
            result.floorCandidateTriangleCount = floorHit->candidateTriangleCount;
            result.floorTestedTriangleCount = floorHit->testedTriangleCount;
        }
    }

    result.appliedDisplacement = subtractVec3(result.finalPosition, result.startPosition);
    return result;
}

Mm9DatPartyMovementResult moveMm9DatPartyInWorldRuntime(
    Mm9DatWorldRuntime &runtime,
    const Mm9DatPartyMovementStep &step)
{
    Mm9DatPartyMovementResult staticResult = moveMm9DatParty(runtime.collisionWorld, step);
    applyMm9DatRuntimeFloorSupport(runtime, step, staticResult);
    staticResult.appliedDisplacement = subtractVec3(staticResult.finalPosition, staticResult.startPosition);

    const float desiredDistance = vectorLength(step.desiredDisplacement);
    if (desiredDistance <= PickEpsilon || step.wallChannelMask == 0)
    {
        return staticResult;
    }

    const Mm9DatVec3 desiredEnd = addVec3(step.position, step.desiredDisplacement);
    const std::optional<ObjectSegmentHitResult> objectHit =
        segmentcastMm9DatObjects(runtime.objectRegistry, step);
    const std::optional<MechanismSegmentHitResult> mechanismHit =
        segmentcastMm9DatMechanisms(runtime, step.position, desiredEnd, true);

    if (!objectHit && !mechanismHit)
    {
        return staticResult;
    }

    float nearestDynamicDistance = std::numeric_limits<float>::max();
    if (objectHit)
    {
        nearestDynamicDistance = std::min(nearestDynamicDistance, objectHit->hit.distance);
    }
    if (mechanismHit)
    {
        nearestDynamicDistance = std::min(nearestDynamicDistance, mechanismHit->hit.distance);
    }

    if (staticResult.wallHit && staticResult.wallHit->hit.distance <= nearestDynamicDistance)
    {
        return staticResult;
    }

    if (objectHit && (!mechanismHit || objectHit->hit.distance <= mechanismHit->hit.distance))
    {
        Mm9DatPartyMovementResult result = {};
        result.startPosition = step.position;
        result.finalPosition = step.position;
        result.blockedByObject = true;
        result.objectHit = objectHit->hit;
        result.objectCandidateCount = objectHit->candidateObjectCount;
        result.objectTestedCount = objectHit->testedObjectCount;
        result.wallCandidateTriangleCount = staticResult.wallCandidateTriangleCount;
        result.wallTestedTriangleCount = staticResult.wallTestedTriangleCount;
        result.onGround = staticResult.onGround;
        result.floorHit = staticResult.floorHit;
        result.mechanismFloorHit = staticResult.mechanismFloorHit;
        result.floorCandidateTriangleCount = staticResult.floorCandidateTriangleCount;
        result.floorTestedTriangleCount = staticResult.floorTestedTriangleCount;

        const Mm9DatVec3 desiredDirection = normalizedOrZero(step.desiredDisplacement);
        const float safeTravelDistance =
            std::max(0.0f, objectHit->hit.distance - std::max(0.0f, step.radius));
        result.finalPosition = addVec3(step.position, multiplyVec3(desiredDirection, safeTravelDistance));
        applyMm9DatRuntimeFloorSupport(runtime, step, result);
        result.appliedDisplacement = subtractVec3(result.finalPosition, result.startPosition);
        return result;
    }

    if (!mechanismHit)
    {
        return staticResult;
    }

    Mm9DatPartyMovementResult result = {};
    result.startPosition = step.position;
    result.finalPosition = step.position;
    result.blockedByMechanism = true;
    result.mechanismHit = mechanismHit->hit;
    result.mechanismCandidateCount = mechanismHit->candidateMechanismCount;
    result.mechanismTestedCount = mechanismHit->testedMechanismCount;
    result.mechanismCandidateTriangleCount = mechanismHit->candidateTriangleCount;
    result.mechanismTestedTriangleCount = mechanismHit->testedTriangleCount;
    applyMechanismContactCommand(runtime, result);
    result.wallCandidateTriangleCount = staticResult.wallCandidateTriangleCount;
    result.wallTestedTriangleCount = staticResult.wallTestedTriangleCount;
    result.onGround = staticResult.onGround;
    result.floorHit = staticResult.floorHit;
    result.mechanismFloorHit = staticResult.mechanismFloorHit;
    result.floorCandidateTriangleCount = staticResult.floorCandidateTriangleCount;
    result.floorTestedTriangleCount = staticResult.floorTestedTriangleCount;

    const Mm9DatVec3 desiredDirection = normalizedOrZero(step.desiredDisplacement);
    const float safeTravelDistance =
        std::max(0.0f, mechanismHit->hit.distance - std::max(0.0f, step.radius));
    result.finalPosition = addVec3(step.position, multiplyVec3(desiredDirection, safeTravelDistance));

    const Mm9DatVec3 remainingDisplacement = subtractVec3(desiredEnd, result.finalPosition);
    const Mm9DatVec3 slideNormal =
        collisionPlaneNormalForDisplacement(remainingDisplacement, mechanismHit->hit.normal);
    const Mm9DatVec3 slideDisplacement =
        projectMm9DatPhysicsVelocityAlongPlane(remainingDisplacement, slideNormal);

    if (vectorLength(slideDisplacement) > PickEpsilon)
    {
        const Mm9DatVec3 slideEnd = addVec3(result.finalPosition, slideDisplacement);
        Mm9DatPhysicsRaycastOptions wallOptions = {};
        wallOptions.channelMask = step.wallChannelMask;
        wallOptions.includeBackfaces = true;
        const std::optional<Mm9DatCollisionRayHit> slideWallHit =
            runtime.collisionWorld.segmentcast(result.finalPosition, slideEnd, wallOptions);

        if (slideWallHit)
        {
            result.wallHit = slideWallHit;
            result.blockedByWall = true;
            result.wallCandidateTriangleCount += slideWallHit->candidateTriangleCount;
            result.wallTestedTriangleCount += slideWallHit->testedTriangleCount;

            const Mm9DatVec3 slideDirection = normalizedOrZero(slideDisplacement);
            const float slideTravelDistance =
                std::max(0.0f, slideWallHit->hit.distance - std::max(0.0f, step.radius));
            result.finalPosition =
                addVec3(result.finalPosition, multiplyVec3(slideDirection, slideTravelDistance));
        }
        else
        {
            result.finalPosition = slideEnd;
            result.slidAlongWall = true;
        }
    }

    applyMm9DatRuntimeFloorSupport(runtime, step, result);

    result.appliedDisplacement = subtractVec3(result.finalPosition, result.startPosition);
    return result;
}

std::optional<Mm9DatWorldPickHit> pickMm9DatWorldRuntime(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatPickRay &ray,
    const Mm9DatWorldPickOptions &options)
{
    const Mm9DatVec3 direction = normalizedOrZero(ray.direction);
    if (options.maxDistance <= PickEpsilon || vectorLength(direction) <= PickEpsilon)
    {
        return std::nullopt;
    }

    Mm9DatPickRay normalizedRay = {};
    normalizedRay.origin = ray.origin;
    normalizedRay.direction = direction;

    std::optional<Mm9DatWorldPickHit> bestHit;

    if (options.includeWorld && options.worldChannelMask != 0)
    {
        Mm9DatPhysicsRaycastOptions raycastOptions = {};
        raycastOptions.channelMask = options.worldChannelMask;
        raycastOptions.includeBackfaces = options.includeBackfaces;

        const Mm9DatVec3 end =
            addVec3(normalizedRay.origin, multiplyVec3(normalizedRay.direction, options.maxDistance));
        const std::optional<Mm9DatCollisionRayHit> worldHit =
            runtime.collisionWorld.segmentcast(normalizedRay.origin, end, raycastOptions);

        if (worldHit)
        {
            Mm9DatWorldPickHit hit = {};
            hit.kind = Mm9DatWorldPickHitKind::World;
            hit.point = worldHit->hit.point;
            hit.normal = worldHit->hit.normal;
            hit.distance = worldHit->hit.distance;
            hit.sourceModelIndex = worldHit->hit.source.sourceModelIndex;
            hit.sourcePolyIndex = worldHit->hit.source.sourcePolyIndex;
            hit.sourceSurfaceIndex = worldHit->hit.source.sourceSurfaceIndex;
            hit.sourceModelName = worldHit->hit.source.sourceModelName;
            hit.candidateTriangleCount = worldHit->candidateTriangleCount;
            hit.testedTriangleCount = worldHit->testedTriangleCount;
            bestHit = std::move(hit);
        }
    }

    if (options.includeObjects)
    {
        const std::vector<size_t> objectCandidates =
            objectCandidatesForRay(runtime.objectRegistry, normalizedRay, options.maxDistance);
        size_t testedObjectCount = 0;

        for (size_t objectIndex : objectCandidates)
        {
            if (objectIndex >= runtime.objectRegistry.objects.size())
            {
                continue;
            }

            const Mm9DatRuntimeObject &object = runtime.objectRegistry.objects[objectIndex];
            if (!object.visible || !object.rayHit)
            {
                continue;
            }

            ++testedObjectCount;
            const std::optional<RayObjectIntersection> objectHit =
                intersectRayObjectBounds(normalizedRay, object, options.maxDistance);

            if (!objectHit)
            {
                continue;
            }

            if (bestHit && objectHit->distance >= bestHit->distance)
            {
                continue;
            }

            Mm9DatWorldPickHit hit = {};
            hit.kind = Mm9DatWorldPickHitKind::Object;
            hit.point = objectHit->point;
            hit.normal = objectHit->normal;
            hit.distance = objectHit->distance;
            hit.objectHandle = object.handle;
            hit.objectId = object.objectId;
            hit.sourceObjectIndex = object.sourceObjectIndex;
            hit.candidateObjectCount = objectCandidates.size();
            hit.testedObjectCount = testedObjectCount;
            bestHit = std::move(hit);
        }

        if (bestHit && bestHit->kind == Mm9DatWorldPickHitKind::Object)
        {
            bestHit->candidateObjectCount = objectCandidates.size();
            bestHit->testedObjectCount = testedObjectCount;
        }
    }

    if (options.includeMechanisms)
    {
        const std::vector<size_t> mechanismCandidates =
            mechanismCandidatesForRay(runtime.mechanismBoundsIndex, normalizedRay, options.maxDistance);
        const size_t candidateMechanismCount = mechanismCandidates.size();
        size_t testedMechanismCount = 0;

        for (size_t mechanismIndex : mechanismCandidates)
        {
            if (mechanismIndex >= runtime.mechanismRuntime.mechanisms.size())
            {
                continue;
            }

            const Mm9DatMechanismInstance &mechanism =
                runtime.mechanismRuntime.mechanisms[mechanismIndex];
            if (!mechanism.currentBounds.valid)
            {
                continue;
            }

            ++testedMechanismCount;
            const std::optional<float> distance =
                intersectRayBounds(normalizedRay, mechanism.currentBounds, options.maxDistance);

            if (!distance)
            {
                continue;
            }

            if (bestHit && *distance >= bestHit->distance)
            {
                continue;
            }

            Mm9DatWorldPickHit hit = {};
            hit.kind = Mm9DatWorldPickHitKind::Mechanism;
            hit.point = addVec3(normalizedRay.origin, multiplyVec3(normalizedRay.direction, *distance));
            hit.normal = normalizedOrZero(subtractVec3(hit.point, mechanism.currentBounds.center));
            hit.distance = *distance;
            hit.mechanismHandle = mechanism.handle;
            hit.mechanismId = mechanism.mechanismId;
            hit.objectId = mechanism.objectId;
            hit.sourceObjectIndex =
                mechanism.sourceObjectIndex >= 0
                    ? static_cast<size_t>(mechanism.sourceObjectIndex)
                    : 0;
            hit.sourceModelIndex = mechanism.sourceModelIndex;
            hit.sourceModelName = mechanism.sourceModelName;
            hit.candidateMechanismCount = candidateMechanismCount;
            hit.testedMechanismCount = testedMechanismCount;
            bestHit = std::move(hit);
        }

        if (bestHit && bestHit->kind == Mm9DatWorldPickHitKind::Mechanism)
        {
            bestHit->candidateMechanismCount = candidateMechanismCount;
            bestHit->testedMechanismCount = testedMechanismCount;
        }
    }

    return bestHit;
}

Mm9DatWorldRuntime buildMm9DatWorldRuntime(const Mm9DatWorldRuntimeBuildInput &input)
{
    Mm9DatWorldRuntime runtime = {};
    runtime.mapId = input.mapId;
    runtime.stats.mapId = input.mapId;

    if (input.pWorld == nullptr)
    {
        runtime.diagnostics.push_back("missing_mm9_dat_world");
        return runtime;
    }

    runtime.stats.worldModelCount = input.pWorld->worldModels.size();
    runtime.renderMesh = buildMm9DatRenderMesh(*input.pWorld);
    runtime.stats.sourcePolyCount = runtime.renderMesh.sourcePolyCount;
    runtime.stats.renderTriangleCount = runtime.renderMesh.triangles.size();
    runtime.renderFilters =
        classifyMm9DatRenderMeshFilters(runtime.renderMesh, input.modelRoles, 0);
    runtime.stats.visibleWaterTriangleCount = runtime.renderFilters.summary.visibleWaterTriangles;
    runtime.stats.waterVolumeTriangleCount = runtime.renderFilters.summary.waterVolumeTriangles;

    if (input.pEvents != nullptr)
    {
        runtime.mechanismRuntime =
            buildMm9DatMechanismRuntime(*input.pEvents, runtime.renderMesh);
        runtime.stats.mechanismCount = runtime.mechanismRuntime.stats.mechanismCount;
        runtime.stats.activeMechanismCount =
            runtime.mechanismRuntime.stats.activeMechanismCount;
        runtime.stats.inertMechanismCount =
            runtime.mechanismRuntime.stats.inertMechanismCount;
    }

    const std::vector<size_t> dynamicSourceModelIndices =
        activeMechanismSourceModelIndices(runtime.mechanismRuntime);
    runtime.renderWorld =
        buildMm9DatRenderWorld(
            runtime.renderMesh,
            runtime.renderFilters,
            input.materialAssignments,
            dynamicSourceModelIndices);
    runtime.mechanismRenderWorld =
        buildMm9DatMechanismRenderWorld(runtime.renderMesh, runtime.mechanismRuntime);
    runtime.mechanismBoundsIndex =
        buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime, DefaultMechanismBoundsCellSize);
    runtime.mechanismCollisionCache =
        buildMm9DatMechanismCollisionCache(runtime.renderMesh, runtime.mechanismRuntime);
    runtime.preparedRenderWorld =
        buildMm9DatPreparedRenderWorld(
            runtime.renderMesh,
            runtime.renderWorld,
            runtime.mechanismRenderWorld,
            runtime.renderFilters,
            input.materialAssignments);
    runtime.materialTable = buildMm9DatRuntimeMaterialTable(runtime.preparedRenderWorld);
    runtime.textureCatalog = buildMm9DatRuntimeTextureCatalog(input.textureSourceRoots);
    runtime.textureBindings = bindMm9DatRuntimeTextures(runtime.materialTable, runtime.textureCatalog);
    runtime.stats.renderPartitionCount = runtime.renderWorld.stats.partitionCount;
    runtime.stats.dynamicMechanismRenderBatchCount =
        runtime.mechanismRenderWorld.stats.batchCount;
    runtime.stats.dynamicMechanismTriangleCount =
        runtime.mechanismRenderWorld.stats.transformedTriangleCount;
    runtime.stats.mechanismBoundsCellCount =
        runtime.mechanismBoundsIndex.stats.cellCount;
    runtime.stats.mechanismBoundsCellRefs =
        runtime.mechanismBoundsIndex.stats.mechanismCellRefs;
    runtime.stats.mechanismCollisionBatchCount =
        runtime.mechanismCollisionCache.stats.batchCount;
    runtime.stats.mechanismCollisionTriangleCount =
        runtime.mechanismCollisionCache.stats.transformedTriangleCount;
    runtime.stats.preparedRenderSectionCount =
        runtime.preparedRenderWorld.stats.sectionCount;
    runtime.stats.preparedRenderVertexCount =
        runtime.preparedRenderWorld.stats.vertexCount;
    runtime.stats.preparedRenderIndexCount =
        runtime.preparedRenderWorld.stats.indexCount;
    runtime.stats.runtimeMaterialCount =
        runtime.materialTable.stats.materialCount;
    runtime.stats.runtimeMissingMaterialCount =
        runtime.materialTable.stats.missingMaterialCount;
    runtime.stats.runtimeTextureCacheEligibleCount =
        runtime.materialTable.stats.textureCacheEligibleCount;
    runtime.stats.runtimeTextureCatalogEntryCount =
        runtime.textureCatalog.stats.catalogEntryCount;
    runtime.stats.runtimeTextureCatalogKeyCount =
        runtime.textureCatalog.stats.catalogKeyCount;
    runtime.stats.runtimeResolvedTextureMaterialCount =
        runtime.textureBindings.stats.resolvedMaterialCount;
    runtime.stats.runtimeMissingTextureMaterialCount =
        runtime.textureBindings.stats.missingMaterialCount;
    runtime.renderSubmissionPlan =
        buildMm9DatRenderSubmissionPlan(runtime.preparedRenderWorld);
    runtime.stats.renderDrawCallCount =
        runtime.renderSubmissionPlan.stats.drawCallCount;
    runtime.stats.renderSubmittedTriangleCount =
        runtime.renderSubmissionPlan.stats.submittedTriangleCount;
    runtime.stats.renderTextureMissDrawCallCount =
        runtime.renderSubmissionPlan.stats.textureMissDrawCallCount;
    runtime.physicsQueryView =
        buildMm9DatPhysicsQueryView(
            runtime.renderMesh,
            filterRenderEntriesExcludingSourceModels(runtime.renderFilters, dynamicSourceModelIndices));

    Mm9DatCollisionWorldBuildOptions collisionOptions = {};
    runtime.collisionWorld.build(runtime.physicsQueryView, collisionOptions);
    runtime.stats.collisionTriangleCount = runtime.physicsQueryView.stats.totalTriangles;
    runtime.stats.collisionCellCount = runtime.collisionWorld.stats().cellCount;
    runtime.objectRegistry =
        buildMm9DatObjectRegistry(
            input.scriptedObjects,
            runtime.collisionWorld,
            &runtime.mechanismRuntime);
    runtime.stats.objectCount = runtime.objectRegistry.stats.objectCount;
    runtime.stats.renderableObjectCount = runtime.objectRegistry.stats.renderableObjectCount;
    runtime.stats.collidableObjectCount = runtime.objectRegistry.stats.collidableObjectCount;
    runtime.stats.collidableObjectCellCount = runtime.objectRegistry.stats.collidableCellCount;
    runtime.stats.collidableObjectCellRefs = runtime.objectRegistry.stats.collidableCellObjectRefs;
    runtime.stats.maxCollidableObjectCellRefs = runtime.objectRegistry.stats.maxCollidableCellObjectRefs;
    runtime.stats.actorObjectCellCount = runtime.objectRegistry.stats.actorCellCount;
    runtime.stats.actorObjectCellRefs = runtime.objectRegistry.stats.actorCellObjectRefs;
    runtime.stats.maxActorObjectCellRefs = runtime.objectRegistry.stats.maxActorCellObjectRefs;
    runtime.objectPresentationWorld =
        buildMm9DatObjectPresentationWorld(runtime.objectRegistry);
    runtime.stats.objectRenderInstanceCount =
        runtime.objectPresentationWorld.stats.instanceCount;
    runtime.stats.actorRenderInstanceCount =
        runtime.objectPresentationWorld.stats.actorInstanceCount;
    runtime.stats.propRenderInstanceCount =
        runtime.objectPresentationWorld.stats.propInstanceCount;
    runtime.stats.objectRenderModelAssetInstanceCount =
        runtime.objectPresentationWorld.stats.modelAssetInstanceCount;
    runtime.stats.objectRenderSourceModelWithoutAssetCount =
        runtime.objectPresentationWorld.stats.sourceModelWithoutModelAssetCount;
    runtime.stats.interactableObjectCount = runtime.objectRegistry.stats.interactableObjectCount;
    runtime.stats.actorObjectCount = runtime.objectRegistry.stats.actorObjectCount;
    runtime.stats.propObjectCount = runtime.objectRegistry.stats.propObjectCount;
    runtime.stats.triggerObjectCount = runtime.objectRegistry.stats.triggerObjectCount;
    runtime.stats.mechanismObjectCount = runtime.objectRegistry.stats.mechanismObjectCount;
    runtime.stats.tickingObjectCount = runtime.objectRegistry.stats.tickingObjectCount;
    runtime.stats.snappedToFloorCount = runtime.objectRegistry.stats.snappedToFloorCount;
    runtime.lightLayer =
        buildMm9LightLayer(
            input.pWorld->worldInfo,
            buildMm9LightSourceObjectsFromDatObjects(input.pWorld->objects));
    runtime.staticRenderLights = buildMm9StaticRenderLights(runtime.lightLayer);
    runtime.stats.lightCount = runtime.lightLayer.lights.size();
    runtime.stats.staticRenderLightCount = runtime.staticRenderLights.size();
    runtime.skyLayer =
        buildMm9SkyLayer(
            *input.pWorld,
            buildMm9SkySourceObjectsFromDatObjects(input.pWorld->objects),
            input.modelRoles);
    runtime.activeSkyDef = selectActiveMm9SkyDef(runtime.skyLayer);
    if (runtime.activeSkyDef)
    {
        runtime.skyCameraMap =
            buildMm9SkyCameraMap(input.pWorld->worldInfo, *runtime.activeSkyDef);
    }
    runtime.stats.skyDefinitionCount = runtime.skyLayer.definitions.size();
    runtime.stats.skyObjectCount = runtime.skyLayer.objects.size();
    runtime.stats.skyModelCount = runtime.skyLayer.skyModelIndices.size();

    for (const std::string &warning : runtime.physicsQueryView.stats.warnings)
    {
        runtime.diagnostics.push_back(warning);
    }

    addLightDiagnostics(runtime);
    addSkyDiagnostics(runtime);

    if (runtime.renderWorld.partitions.empty() && !runtime.renderMesh.triangles.empty())
    {
        runtime.diagnostics.push_back("MM9 DAT runtime render world has no normal visual partitions");
    }

    if (runtime.materialTable.stats.textureCacheEligibleCount != 0 && input.textureSourceRoots.empty())
    {
        runtime.diagnostics.push_back("MM9 DAT runtime has texture-eligible materials but no texture source roots");
    }

    if (runtime.textureBindings.stats.missingMaterialCount != 0)
    {
        runtime.diagnostics.push_back(
            "MM9 DAT runtime has missing texture material bindings: "
            + std::to_string(runtime.textureBindings.stats.missingMaterialCount));
    }

    if (!runtime.collisionWorld.stats().valid)
    {
        runtime.diagnostics.push_back("MM9 DAT runtime collision world has no indexed triangles");
    }

    return runtime;
}
}
