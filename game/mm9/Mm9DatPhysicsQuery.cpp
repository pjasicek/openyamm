#include "game/mm9/Mm9DatPhysicsQuery.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <unordered_set>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Mm9DatPhysicsQueryEpsilon = 0.000001f;
constexpr float Mm9DatPhysicsQueryTieEpsilon = 0.00001f;

Mm9DatVec3 renderVertexPosition(const Mm9DatRenderVertex &vertex)
{
    return {vertex.x, vertex.y, vertex.z};
}

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

float length(const Mm9DatVec3 &value)
{
    return std::sqrt(dot(value, value));
}

std::optional<Mm9DatVec3> normalize(const Mm9DatVec3 &value)
{
    const float valueLength = length(value);

    if (valueLength <= Mm9DatPhysicsQueryEpsilon)
    {
        return std::nullopt;
    }

    return multiply(value, 1.0f / valueLength);
}

uint32_t queryChannelsFromRenderFlags(uint32_t renderFlags)
{
    uint32_t channelFlags = 0;

    if ((renderFlags & Mm9DatRenderFilterVisual) != 0)
    {
        channelFlags |= Mm9DatPhysicsQueryChannelVisible;
    }

    if ((renderFlags & Mm9DatRenderFilterPhysics) != 0)
    {
        channelFlags |= Mm9DatPhysicsQueryChannelPhysics;
    }

    if ((renderFlags & Mm9DatRenderFilterVisibility) != 0)
    {
        channelFlags |= Mm9DatPhysicsQueryChannelVisibility;
    }

    if ((renderFlags & Mm9DatRenderFilterTrigger) != 0)
    {
        channelFlags |= Mm9DatPhysicsQueryChannelTrigger;
    }

    if ((renderFlags & Mm9DatRenderFilterWater) != 0)
    {
        channelFlags |= Mm9DatPhysicsQueryChannelWater;
    }

    if ((renderFlags & Mm9DatRenderFilterSky) != 0)
    {
        channelFlags |= Mm9DatPhysicsQueryChannelSky;
    }

    if ((renderFlags & Mm9DatRenderFilterMovable) != 0)
    {
        channelFlags |= Mm9DatPhysicsQueryChannelMovable;
    }

    if ((renderFlags & Mm9DatRenderFilterHelper) != 0)
    {
        channelFlags |= Mm9DatPhysicsQueryChannelHelper;
    }

    return channelFlags;
}

void addChannelStats(Mm9DatPhysicsQueryStats &stats, uint32_t channelFlags)
{
    if ((channelFlags & Mm9DatPhysicsQueryChannelVisible) != 0)
    {
        ++stats.visibleTriangles;
    }

    if ((channelFlags & Mm9DatPhysicsQueryChannelPhysics) != 0)
    {
        ++stats.physicsTriangles;
    }

    if ((channelFlags & Mm9DatPhysicsQueryChannelVisibility) != 0)
    {
        ++stats.visibilityTriangles;
    }

    if ((channelFlags & Mm9DatPhysicsQueryChannelTrigger) != 0)
    {
        ++stats.triggerTriangles;
    }

    if ((channelFlags & Mm9DatPhysicsQueryChannelWater) != 0)
    {
        ++stats.waterTriangles;
    }

    if ((channelFlags & Mm9DatPhysicsQueryChannelSky) != 0)
    {
        ++stats.skyTriangles;
    }

    if ((channelFlags & Mm9DatPhysicsQueryChannelMovable) != 0)
    {
        ++stats.movableTriangles;
    }

    if ((channelFlags & Mm9DatPhysicsQueryChannelHelper) != 0)
    {
        ++stats.helperTriangles;
    }

    if (channelFlags == 0)
    {
        ++stats.unclassifiedTriangles;
    }
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
        if (std::fabs(determinant) <= Mm9DatPhysicsQueryEpsilon)
        {
            return std::nullopt;
        }
    }
    else if (determinant <= Mm9DatPhysicsQueryEpsilon)
    {
        return std::nullopt;
    }

    const float inverseDeterminant = 1.0f / determinant;
    const Mm9DatVec3 tvec = subtract(ray.origin, triangle.vertex0);
    const float barycentricU = dot(tvec, pvec) * inverseDeterminant;

    if (barycentricU < -Mm9DatPhysicsQueryEpsilon || barycentricU > 1.0f + Mm9DatPhysicsQueryEpsilon)
    {
        return std::nullopt;
    }

    const Mm9DatVec3 qvec = cross(tvec, edge1);
    const float barycentricV = dot(ray.direction, qvec) * inverseDeterminant;

    if (barycentricV < -Mm9DatPhysicsQueryEpsilon
        || barycentricU + barycentricV > 1.0f + Mm9DatPhysicsQueryEpsilon)
    {
        return std::nullopt;
    }

    const float distance = dot(edge2, qvec) * inverseDeterminant;

    if (distance < -Mm9DatPhysicsQueryEpsilon)
    {
        return std::nullopt;
    }

    RayTriangleIntersection intersection = {};
    intersection.distance = std::max(0.0f, distance);
    intersection.barycentricU = barycentricU;
    intersection.barycentricV = barycentricV;
    return intersection;
}

bool isBetterHit(
    const Mm9DatPhysicsRayHit &candidate,
    const Mm9DatPhysicsRayHit &current)
{
    if (candidate.distance < current.distance - Mm9DatPhysicsQueryTieEpsilon)
    {
        return true;
    }

    if (std::fabs(candidate.distance - current.distance) > Mm9DatPhysicsQueryTieEpsilon)
    {
        return false;
    }

    return candidate.source.renderTriangleIndex < current.source.renderTriangleIndex;
}
}

Mm9DatPhysicsQueryView buildMm9DatPhysicsQueryView(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatRenderFilterResult &filters)
{
    Mm9DatPhysicsQueryView view = {};
    view.triangles.reserve(mesh.triangles.size());

    std::unordered_set<size_t> sourceModelIndices;
    const size_t entryCount = std::min(mesh.triangles.size(), filters.entries.size());

    for (size_t filterIndex = 0; filterIndex < entryCount; ++filterIndex)
    {
        const Mm9DatRenderFilterEntry &entry = filters.entries[filterIndex];

        if (entry.triangleIndex >= mesh.triangles.size())
        {
            continue;
        }

        const Mm9DatRenderTriangle &renderTriangle = mesh.triangles[entry.triangleIndex];
        const Mm9DatVec3 vertex0 = renderVertexPosition(renderTriangle.vertices[0]);
        const Mm9DatVec3 vertex1 = renderVertexPosition(renderTriangle.vertices[1]);
        const Mm9DatVec3 vertex2 = renderVertexPosition(renderTriangle.vertices[2]);
        const Mm9DatVec3 normalVector = cross(subtract(vertex1, vertex0), subtract(vertex2, vertex0));
        const std::optional<Mm9DatVec3> normal = normalize(normalVector);

        if (!normal)
        {
            continue;
        }

        Mm9DatPhysicsQueryTriangle queryTriangle = {};
        queryTriangle.source.queryTriangleIndex = view.triangles.size();
        queryTriangle.source.renderTriangleIndex = entry.triangleIndex;
        queryTriangle.source.sourceModelIndex = renderTriangle.sourceModelIndex;
        queryTriangle.source.sourceModelName = renderTriangle.sourceModelName;
        queryTriangle.source.sourcePolyIndex = renderTriangle.sourcePolyIndex;
        queryTriangle.source.sourceSurfaceIndex = renderTriangle.sourceSurfaceIndex;
        queryTriangle.source.sourceTextureIndex = renderTriangle.sourceTextureIndex;
        queryTriangle.source.sourceTexture = renderTriangle.sourceTexture;
        queryTriangle.source.surfaceFlags = renderTriangle.surfaceFlags;
        queryTriangle.source.textureFlags = renderTriangle.textureFlags;
        queryTriangle.source.channelFlags = queryChannelsFromRenderFlags(entry.flags);
        queryTriangle.vertex0 = vertex0;
        queryTriangle.vertex1 = vertex1;
        queryTriangle.vertex2 = vertex2;
        queryTriangle.normal = *normal;
        queryTriangle.planeDistance = dot(queryTriangle.normal, queryTriangle.vertex0);

        addChannelStats(view.stats, queryTriangle.source.channelFlags);
        sourceModelIndices.insert(queryTriangle.source.sourceModelIndex);
        view.triangles.push_back(std::move(queryTriangle));
    }

    view.stats.totalTriangles = view.triangles.size();
    view.stats.sourceModelCount = sourceModelIndices.size();
    view.stats.hasPhysicsGeometry = view.stats.physicsTriangles > 0;
    view.stats.hasVisibilityGeometry = view.stats.visibilityTriangles > 0;

    if (!view.stats.hasPhysicsGeometry)
    {
        view.stats.warnings.push_back("MM9 DAT physics query view has no physics-channel geometry");
    }

    if (filters.entries.size() != mesh.triangles.size())
    {
        view.stats.warnings.push_back("MM9 DAT physics query view built from incomplete render filter entries");
    }

    return view;
}

std::optional<Mm9DatPhysicsRayHit> raycastMm9DatPhysicsQueryView(
    const Mm9DatPhysicsQueryView &view,
    const Mm9DatPickRay &ray,
    const Mm9DatPhysicsRaycastOptions &options)
{
    const std::optional<Mm9DatVec3> normalizedDirection = normalize(ray.direction);

    if (!normalizedDirection || options.channelMask == 0)
    {
        return std::nullopt;
    }

    Mm9DatPickRay normalizedRay = {};
    normalizedRay.origin = ray.origin;
    normalizedRay.direction = *normalizedDirection;

    std::optional<Mm9DatPhysicsRayHit> bestHit;

    for (const Mm9DatPhysicsQueryTriangle &triangle : view.triangles)
    {
        if ((triangle.source.channelFlags & options.channelMask) == 0)
        {
            continue;
        }

        const std::optional<RayTriangleIntersection> intersection =
            intersectRayTriangle(normalizedRay, triangle, options.includeBackfaces);

        if (!intersection)
        {
            continue;
        }

        if (options.hasMaxDistance && intersection->distance > options.maxDistance + Mm9DatPhysicsQueryEpsilon)
        {
            continue;
        }

        Mm9DatPhysicsRayHit hit = {};
        hit.point = add(normalizedRay.origin, multiply(normalizedRay.direction, intersection->distance));
        hit.normal = triangle.normal;
        hit.planeDistance = triangle.planeDistance;
        hit.distance = intersection->distance;
        hit.barycentricU = intersection->barycentricU;
        hit.barycentricV = intersection->barycentricV;
        hit.source = triangle.source;
        hit.channelFlags = triangle.source.channelFlags;

        if (!bestHit || isBetterHit(hit, *bestHit))
        {
            bestHit = std::move(hit);
        }
    }

    return bestHit;
}

std::optional<Mm9DatPhysicsRayHit> segmentcastMm9DatPhysicsQueryView(
    const Mm9DatPhysicsQueryView &view,
    const Mm9DatVec3 &start,
    const Mm9DatVec3 &end,
    const Mm9DatPhysicsRaycastOptions &options)
{
    const Mm9DatVec3 direction = subtract(end, start);
    const float distance = length(direction);

    if (distance <= Mm9DatPhysicsQueryEpsilon)
    {
        return std::nullopt;
    }

    Mm9DatPhysicsRaycastOptions segmentOptions = options;
    segmentOptions.maxDistance = distance;
    segmentOptions.hasMaxDistance = true;

    Mm9DatPickRay ray = {};
    ray.origin = start;
    ray.direction = direction;

    return raycastMm9DatPhysicsQueryView(view, ray, segmentOptions);
}

Mm9DatVec3 projectMm9DatPhysicsVelocityAlongPlane(
    const Mm9DatVec3 &velocity,
    const Mm9DatVec3 &normal)
{
    const std::optional<Mm9DatVec3> normalizedNormal = normalize(normal);

    if (!normalizedNormal)
    {
        return velocity;
    }

    const float velocityIntoNormal = dot(velocity, *normalizedNormal);

    if (velocityIntoNormal >= 0.0f)
    {
        return velocity;
    }

    return subtract(velocity, multiply(*normalizedNormal, velocityIntoNormal));
}
}
