#include "game/mm9/Mm9DatCollisionWorld.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr float CollisionEpsilon = 0.000001f;
constexpr float HitTieEpsilon = 0.00001f;

Mm9DatVec3 add(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.x + right.x,
        left.y + right.y,
        left.z + right.z,
    };
}

Mm9DatVec3 subtract(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.x - right.x,
        left.y - right.y,
        left.z - right.z,
    };
}

Mm9DatVec3 multiply(const Mm9DatVec3 &value, float scalar)
{
    return {
        value.x * scalar,
        value.y * scalar,
        value.z * scalar,
    };
}

float length(const Mm9DatVec3 &value)
{
    return std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
}

std::optional<Mm9DatVec3> normalize(const Mm9DatVec3 &value)
{
    const float vectorLength = length(value);
    if (vectorLength <= CollisionEpsilon)
    {
        return std::nullopt;
    }

    return multiply(value, 1.0f / vectorLength);
}

float dot(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

Mm9DatVec3 cross(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x,
    };
}

struct RayTriangleIntersection
{
    float distance = 0.0f;
    float barycentricU = 0.0f;
    float barycentricV = 0.0f;
};

std::optional<RayTriangleIntersection> intersectRayTriangle(
    const Mm9DatPickRay &ray,
    const Mm9DatPhysicsQueryTriangle &triangle,
    bool includeBackfaces)
{
    const Mm9DatVec3 edge1 = subtract(triangle.vertex1, triangle.vertex0);
    const Mm9DatVec3 edge2 = subtract(triangle.vertex2, triangle.vertex0);
    const Mm9DatVec3 pvec = cross(ray.direction, edge2);
    const float determinant = dot(edge1, pvec);

    if (includeBackfaces)
    {
        if (std::fabs(determinant) <= CollisionEpsilon)
        {
            return std::nullopt;
        }
    }
    else if (determinant <= CollisionEpsilon)
    {
        return std::nullopt;
    }

    const float inverseDeterminant = 1.0f / determinant;
    const Mm9DatVec3 tvec = subtract(ray.origin, triangle.vertex0);
    const float barycentricU = dot(tvec, pvec) * inverseDeterminant;

    if (barycentricU < -CollisionEpsilon || barycentricU > 1.0f + CollisionEpsilon)
    {
        return std::nullopt;
    }

    const Mm9DatVec3 qvec = cross(tvec, edge1);
    const float barycentricV = dot(ray.direction, qvec) * inverseDeterminant;

    if (barycentricV < -CollisionEpsilon || barycentricU + barycentricV > 1.0f + CollisionEpsilon)
    {
        return std::nullopt;
    }

    const float distance = dot(edge2, qvec) * inverseDeterminant;

    if (distance < -CollisionEpsilon)
    {
        return std::nullopt;
    }

    RayTriangleIntersection intersection = {};
    intersection.distance = std::max(0.0f, distance);
    intersection.barycentricU = barycentricU;
    intersection.barycentricV = barycentricV;
    return intersection;
}

int32_t floorCell(float value, float cellSize)
{
    return static_cast<int32_t>(std::floor(value / cellSize));
}

int32_t minCellForValues(float first, float second, float third, float cellSize)
{
    return floorCell(std::min({first, second, third}), cellSize);
}

int32_t maxCellForValues(float first, float second, float third, float cellSize)
{
    return floorCell(std::max({first, second, third}), cellSize);
}

bool isBetterFloorHit(
    const Mm9DatFloorSupportHit &candidate,
    const Mm9DatFloorSupportHit &current)
{
    if (candidate.rayDistance < current.rayDistance - HitTieEpsilon)
    {
        return true;
    }

    if (std::fabs(candidate.rayDistance - current.rayDistance) > HitTieEpsilon)
    {
        return false;
    }

    return candidate.source.renderTriangleIndex < current.source.renderTriangleIndex;
}

bool isBetterRayHit(const Mm9DatPhysicsRayHit &candidate, const Mm9DatPhysicsRayHit &current)
{
    if (candidate.distance < current.distance - HitTieEpsilon)
    {
        return true;
    }

    if (std::fabs(candidate.distance - current.distance) > HitTieEpsilon)
    {
        return false;
    }

    return candidate.source.renderTriangleIndex < current.source.renderTriangleIndex;
}
}

bool Mm9DatCollisionWorld::build(
    const Mm9DatPhysicsQueryView &queryView,
    const Mm9DatCollisionWorldBuildOptions &options)
{
    m_triangles = queryView.triangles;
    m_horizontalCellSize = options.horizontalCellSize > CollisionEpsilon ? options.horizontalCellSize : 512.0f;
    m_triangleIndicesByCell.clear();
    m_stats = {};
    m_stats.sourceTriangleCount = m_triangles.size();
    m_stats.horizontalCellSize = m_horizontalCellSize;

    for (size_t triangleIndex = 0; triangleIndex < m_triangles.size(); ++triangleIndex)
    {
        const Mm9DatPhysicsQueryTriangle &triangle = m_triangles[triangleIndex];

        if (triangle.source.channelFlags == 0)
        {
            continue;
        }

        const int32_t minCellX =
            minCellForValues(triangle.vertex0.x, triangle.vertex1.x, triangle.vertex2.x, m_horizontalCellSize);
        const int32_t maxCellX =
            maxCellForValues(triangle.vertex0.x, triangle.vertex1.x, triangle.vertex2.x, m_horizontalCellSize);
        const int32_t minCellZ =
            minCellForValues(triangle.vertex0.z, triangle.vertex1.z, triangle.vertex2.z, m_horizontalCellSize);
        const int32_t maxCellZ =
            maxCellForValues(triangle.vertex0.z, triangle.vertex1.z, triangle.vertex2.z, m_horizontalCellSize);

        for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
        {
            for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
            {
                CellCoord coord = {};
                coord.x = cellX;
                coord.z = cellZ;
                m_triangleIndicesByCell[cellKey(coord)].push_back(triangleIndex);
                ++m_stats.cellTriangleRefs;
            }
        }

        ++m_stats.indexedTriangleCount;
    }

    m_stats.cellCount = m_triangleIndicesByCell.size();

    for (const auto &cellEntry : m_triangleIndicesByCell)
    {
        m_stats.maxCellTriangleRefs = std::max(m_stats.maxCellTriangleRefs, cellEntry.second.size());
    }

    m_stats.valid = !m_triangles.empty() && m_stats.cellCount > 0;
    return m_stats.valid;
}

const Mm9DatCollisionWorldStats &Mm9DatCollisionWorld::stats() const
{
    return m_stats;
}

std::optional<Mm9DatFloorSupportHit> Mm9DatCollisionWorld::findFloorSupport(
    const Mm9DatFloorSupportQuery &query) const
{
    if (!m_stats.valid || query.channelMask == 0 || query.maxDropDistance <= CollisionEpsilon)
    {
        return std::nullopt;
    }

    const CellCoord coord = cellCoordForPoint(query.position);
    const auto cellIterator = m_triangleIndicesByCell.find(cellKey(coord));

    if (cellIterator == m_triangleIndicesByCell.end())
    {
        return std::nullopt;
    }

    Mm9DatPickRay ray = {};
    ray.origin = query.position;
    ray.direction = {0.0f, -1.0f, 0.0f};

    std::optional<Mm9DatFloorSupportHit> bestHit;
    size_t testedTriangleCount = 0;

    for (size_t triangleIndex : cellIterator->second)
    {
        if (triangleIndex >= m_triangles.size())
        {
            continue;
        }

        const Mm9DatPhysicsQueryTriangle &triangle = m_triangles[triangleIndex];

        if ((triangle.source.channelFlags & query.channelMask) == 0)
        {
            continue;
        }

        ++testedTriangleCount;
        const std::optional<RayTriangleIntersection> intersection =
            intersectRayTriangle(ray, triangle, query.includeBackfaces);

        if (!intersection || intersection->distance > query.maxDropDistance + CollisionEpsilon)
        {
            continue;
        }

        Mm9DatFloorSupportHit hit = {};
        hit.floorPoint = add(ray.origin, multiply(ray.direction, intersection->distance));
        hit.normal = triangle.normal;
        hit.adjustedPosition = query.position;
        hit.adjustedPosition.y = hit.floorPoint.y + query.halfHeight + query.placementBias;
        hit.rayDistance = intersection->distance;
        hit.dropDistance = std::max(0.0f, query.position.y - hit.adjustedPosition.y);
        hit.candidateTriangleCount = cellIterator->second.size();
        hit.source = triangle.source;

        if (!bestHit || isBetterFloorHit(hit, *bestHit))
        {
            bestHit = hit;
        }
    }

    if (bestHit)
    {
        bestHit->testedTriangleCount = testedTriangleCount;
    }

    return bestHit;
}

std::optional<Mm9DatCollisionRayHit> Mm9DatCollisionWorld::segmentcast(
    const Mm9DatVec3 &start,
    const Mm9DatVec3 &end,
    const Mm9DatPhysicsRaycastOptions &options) const
{
    const Mm9DatVec3 direction = subtract(end, start);
    const float distance = length(direction);
    const std::optional<Mm9DatVec3> normalizedDirection = normalize(direction);

    if (!m_stats.valid || !normalizedDirection || options.channelMask == 0)
    {
        return std::nullopt;
    }

    const float minX = std::min(start.x, end.x);
    const float maxX = std::max(start.x, end.x);
    const float minZ = std::min(start.z, end.z);
    const float maxZ = std::max(start.z, end.z);
    const std::vector<size_t> candidateTriangleIndices =
        triangleIndicesForHorizontalBounds(minX, maxX, minZ, maxZ);

    if (candidateTriangleIndices.empty())
    {
        return std::nullopt;
    }

    Mm9DatPickRay ray = {};
    ray.origin = start;
    ray.direction = *normalizedDirection;

    std::optional<Mm9DatCollisionRayHit> bestHit;
    size_t testedTriangleCount = 0;

    for (size_t triangleIndex : candidateTriangleIndices)
    {
        if (triangleIndex >= m_triangles.size())
        {
            continue;
        }

        const Mm9DatPhysicsQueryTriangle &triangle = m_triangles[triangleIndex];
        if ((triangle.source.channelFlags & options.channelMask) == 0)
        {
            continue;
        }

        ++testedTriangleCount;
        const std::optional<RayTriangleIntersection> intersection =
            intersectRayTriangle(ray, triangle, options.includeBackfaces);

        if (!intersection || intersection->distance > distance + CollisionEpsilon)
        {
            continue;
        }

        if (options.hasMaxDistance && intersection->distance > options.maxDistance + CollisionEpsilon)
        {
            continue;
        }

        Mm9DatCollisionRayHit hit = {};
        hit.hit.point = add(ray.origin, multiply(ray.direction, intersection->distance));
        hit.hit.normal = triangle.normal;
        hit.hit.planeDistance = triangle.planeDistance;
        hit.hit.distance = intersection->distance;
        hit.hit.barycentricU = intersection->barycentricU;
        hit.hit.barycentricV = intersection->barycentricV;
        hit.hit.source = triangle.source;
        hit.hit.channelFlags = triangle.source.channelFlags;
        hit.candidateTriangleCount = candidateTriangleIndices.size();

        if (!bestHit || isBetterRayHit(hit.hit, bestHit->hit))
        {
            bestHit = std::move(hit);
        }
    }

    if (bestHit)
    {
        bestHit->testedTriangleCount = testedTriangleCount;
    }

    return bestHit;
}

int64_t Mm9DatCollisionWorld::cellKey(const CellCoord &coord)
{
    const uint64_t xBits = static_cast<uint32_t>(coord.x);
    const uint64_t zBits = static_cast<uint32_t>(coord.z);
    return static_cast<int64_t>((xBits << 32) | zBits);
}

Mm9DatCollisionWorld::CellCoord Mm9DatCollisionWorld::cellCoordForPoint(const Mm9DatVec3 &point) const
{
    CellCoord coord = {};
    coord.x = floorCell(point.x, m_horizontalCellSize);
    coord.z = floorCell(point.z, m_horizontalCellSize);
    return coord;
}

std::vector<size_t> Mm9DatCollisionWorld::triangleIndicesForHorizontalBounds(
    float minX,
    float maxX,
    float minZ,
    float maxZ) const
{
    std::vector<size_t> result;
    std::unordered_set<size_t> seenTriangleIndices;

    if (!m_stats.valid)
    {
        return result;
    }

    const int32_t minCellX = floorCell(minX, m_horizontalCellSize);
    const int32_t maxCellX = floorCell(maxX, m_horizontalCellSize);
    const int32_t minCellZ = floorCell(minZ, m_horizontalCellSize);
    const int32_t maxCellZ = floorCell(maxZ, m_horizontalCellSize);

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
        {
            CellCoord coord = {};
            coord.x = cellX;
            coord.z = cellZ;

            const auto cellIterator = m_triangleIndicesByCell.find(cellKey(coord));
            if (cellIterator == m_triangleIndicesByCell.end())
            {
                continue;
            }

            for (size_t triangleIndex : cellIterator->second)
            {
                if (seenTriangleIndices.insert(triangleIndex).second)
                {
                    result.push_back(triangleIndex);
                }
            }
        }
    }

    return result;
}
}
