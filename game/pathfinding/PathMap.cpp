#include "game/pathfinding/PathMap.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <tuple>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float PathEpsilon = 0.0001f;
constexpr int32_t MaxPathGridCellSpan = 4096;
constexpr int64_t MaxSpatialCellsPerFacet = 4096;
constexpr uint64_t PathGridScanCostRatio = 8;
// The top of a flyer's body is traced this far below its height, clear of a ceiling it touches.
constexpr float FlyingBodyTopClearance = 4.0f;
// A step's underside is a ceiling face with the step's tread at most this far above it (MM9's slab treads: 15-16).
constexpr float StepSlabMaxThickness = 24.0f;
// A riser's top meets its tread within this height, and the tread is looked for this far past the riser's face.
constexpr float RiserTreadHeightTolerance = 2.0f;
constexpr float RiserTreadProbeDistance = 4.0f;
// A riser faces the body's move within 60 degrees (cos 60).
constexpr float RiserMinimumFacing = 0.5f;

PathPoint pointAdd(const PathPoint &left, const PathPoint &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

PathPoint pointSubtract(const PathPoint &left, const PathPoint &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

PathPoint pointScale(const PathPoint &point, float scale)
{
    return {point.x * scale, point.y * scale, point.z * scale};
}

float pointDot(const PathPoint &left, const PathPoint &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

PathPoint pointCross(const PathPoint &left, const PathPoint &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
}

float pointLengthSquared(const PathPoint &point)
{
    return pointDot(point, point);
}

float pointLength(const PathPoint &point)
{
    return std::sqrt(pointLengthSquared(point));
}

PathPoint pointNormalize(const PathPoint &point)
{
    const float length = pointLength(point);

    if (length <= PathEpsilon)
    {
        return {};
    }

    return {point.x / length, point.y / length, point.z / length};
}

float xyDistance(const PathPoint &from, const PathPoint &to)
{
    const float dx = to.x - from.x;
    const float dy = to.y - from.y;
    return std::sqrt(dx * dx + dy * dy);
}

float pointSegmentDistanceSquared(const PathPoint &point, const PathPoint &from, const PathPoint &to)
{
    const PathPoint direction = pointSubtract(to, from);
    const float lengthSquared = pointLengthSquared(direction);
    const float progress = lengthSquared > PathEpsilon
        ? std::clamp(pointDot(pointSubtract(point, from), direction) / lengthSquared, 0.0f, 1.0f)
        : 0.0f;
    return pointLengthSquared(pointSubtract(pointSubtract(point, from), pointScale(direction, progress)));
}

float segmentDistanceSquared(
    const PathPoint &from,
    const PathPoint &to,
    const PathPoint &edgeFrom,
    const PathPoint &edgeTo)
{
    float distanceSquared = std::min({
        pointSegmentDistanceSquared(from, edgeFrom, edgeTo),
        pointSegmentDistanceSquared(to, edgeFrom, edgeTo),
        pointSegmentDistanceSquared(edgeFrom, from, to),
        pointSegmentDistanceSquared(edgeTo, from, to)
    });
    const PathPoint direction = pointSubtract(to, from);
    const PathPoint edge = pointSubtract(edgeTo, edgeFrom);
    const PathPoint offset = pointSubtract(from, edgeFrom);
    const float lengthSquared = pointLengthSquared(direction);
    const float edgeLengthSquared = pointLengthSquared(edge);
    const float alignment = pointDot(direction, edge);
    const float determinant = lengthSquared * edgeLengthSquared - alignment * alignment;

    if (determinant > PathEpsilon * lengthSquared * edgeLengthSquared)
    {
        const float alongDirection = pointDot(offset, direction);
        const float alongEdge = pointDot(offset, edge);
        const float progress = (alignment * alongEdge - edgeLengthSquared * alongDirection) / determinant;
        const float edgeProgress = (lengthSquared * alongEdge - alignment * alongDirection) / determinant;

        if (progress >= 0.0f && progress <= 1.0f && edgeProgress >= 0.0f && edgeProgress <= 1.0f)
        {
            const PathPoint separation = pointSubtract(
                pointAdd(offset, pointScale(direction, progress)), pointScale(edge, edgeProgress));
            distanceSquared = std::min(distanceSquared, pointLengthSquared(separation));
        }
    }

    return distanceSquared;
}

bool walkStepDeltaAllowed(float fromZ, float toZ, const PathObject &object)
{
    const float deltaZ = toZ - fromZ;

    if (deltaZ > object.stepHeight + PathEpsilon)
    {
        return false;
    }

    if (-deltaZ > object.dropHeight + PathEpsilon)
    {
        return false;
    }

    return true;
}

float distanceSquared2d(const PathPoint &from, const PathPoint &to)
{
    const float dx = to.x - from.x;
    const float dy = to.y - from.y;
    return dx * dx + dy * dy;
}

PathPoint closestPointOnSegment2d(const PathPoint &point, const PathPoint &from, const PathPoint &to)
{
    const float edgeX = to.x - from.x;
    const float edgeY = to.y - from.y;
    const float edgeLengthSquared = edgeX * edgeX + edgeY * edgeY;

    if (edgeLengthSquared <= PathEpsilon)
    {
        return {from.x, from.y, point.z};
    }

    const float t =
        std::clamp(((point.x - from.x) * edgeX + (point.y - from.y) * edgeY) / edgeLengthSquared, 0.0f, 1.0f);
    return {from.x + edgeX * t, from.y + edgeY * t, point.z};
}

PathPoint interpolatePoint(const PathPoint &from, const PathPoint &to, float t)
{
    return {
        from.x + (to.x - from.x) * t,
        from.y + (to.y - from.y) * t,
        from.z + (to.z - from.z) * t
    };
}

PathBounds facetBounds(const PathFacet &facet)
{
    PathBounds bounds = {};

    if (facet.vertices.empty())
    {
        return bounds;
    }

    bounds.minX = facet.vertices.front().x;
    bounds.maxX = facet.vertices.front().x;
    bounds.minY = facet.vertices.front().y;
    bounds.maxY = facet.vertices.front().y;
    bounds.minZ = facet.vertices.front().z;
    bounds.maxZ = facet.vertices.front().z;

    for (const PathPoint &vertex : facet.vertices)
    {
        bounds.minX = std::min(bounds.minX, vertex.x);
        bounds.maxX = std::max(bounds.maxX, vertex.x);
        bounds.minY = std::min(bounds.minY, vertex.y);
        bounds.maxY = std::max(bounds.maxY, vertex.y);
        bounds.minZ = std::min(bounds.minZ, vertex.z);
        bounds.maxZ = std::max(bounds.maxZ, vertex.z);
    }

    return bounds;
}

PathBounds segmentBounds(const PathPoint &from, const PathPoint &to, float padding)
{
    PathBounds bounds = {};
    bounds.minX = std::min(from.x, to.x) - padding;
    bounds.maxX = std::max(from.x, to.x) + padding;
    bounds.minY = std::min(from.y, to.y) - padding;
    bounds.maxY = std::max(from.y, to.y) + padding;
    bounds.minZ = std::min(from.z, to.z) - padding;
    bounds.maxZ = std::max(from.z, to.z) + padding;
    return bounds;
}

bool boundsOverlap(const PathBounds &left, const PathBounds &right)
{
    return left.maxX + PathEpsilon >= right.minX
        && left.minX - PathEpsilon <= right.maxX
        && left.maxY + PathEpsilon >= right.minY
        && left.minY - PathEpsilon <= right.maxY
        && left.maxZ + PathEpsilon >= right.minZ
        && left.minZ - PathEpsilon <= right.maxZ;
}

bool pointIsFinite(const PathPoint &point)
{
    return std::isfinite(point.x) && std::isfinite(point.y) && std::isfinite(point.z);
}

bool boundsAreFinite(const PathBounds &bounds)
{
    return std::isfinite(bounds.minX)
        && std::isfinite(bounds.maxX)
        && std::isfinite(bounds.minY)
        && std::isfinite(bounds.maxY)
        && std::isfinite(bounds.minZ)
        && std::isfinite(bounds.maxZ);
}

PathPoint computeFacetNormal(const PathFacet &facet)
{
    if (facet.vertices.size() < 3)
    {
        return {};
    }

    const PathPoint &origin = facet.vertices.front();

    for (size_t index = 1; index + 1 < facet.vertices.size(); ++index)
    {
        const PathPoint edgeA = pointSubtract(facet.vertices[index], origin);
        const PathPoint edgeB = pointSubtract(facet.vertices[index + 1], origin);
        const PathPoint normal = pointNormalize(pointCross(edgeA, edgeB));

        if (pointLengthSquared(normal) > PathEpsilon)
        {
            return normal;
        }
    }

    return {};
}

int dominantAxisToDrop(const PathPoint &normal)
{
    const float absX = std::fabs(normal.x);
    const float absY = std::fabs(normal.y);
    const float absZ = std::fabs(normal.z);

    if (absX >= absY && absX >= absZ)
    {
        return 0;
    }

    if (absY >= absZ)
    {
        return 1;
    }

    return 2;
}

void projectPoint(const PathPoint &point, int dropAxis, float &outX, float &outY)
{
    if (dropAxis == 0)
    {
        outX = point.y;
        outY = point.z;
        return;
    }

    if (dropAxis == 1)
    {
        outX = point.x;
        outY = point.z;
        return;
    }

    outX = point.x;
    outY = point.y;
}

bool projectedPointOnSegment(float px, float py, float ax, float ay, float bx, float by)
{
    const float cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax);

    if (std::fabs(cross) > PathEpsilon)
    {
        return false;
    }

    return px >= std::min(ax, bx) - PathEpsilon
        && px <= std::max(ax, bx) + PathEpsilon
        && py >= std::min(ay, by) - PathEpsilon
        && py <= std::max(ay, by) + PathEpsilon;
}

bool pointInsideFacet(const PathPoint &point, const PathFacet &facet, const PathPoint &normal)
{
    if (facet.vertices.size() < 3)
    {
        return false;
    }

    const int dropAxis = dominantAxisToDrop(normal);
    float px = 0.0f;
    float py = 0.0f;
    projectPoint(point, dropAxis, px, py);

    bool inside = false;

    for (size_t index = 0; index < facet.vertices.size(); ++index)
    {
        const PathPoint &current = facet.vertices[index];
        const PathPoint &next = facet.vertices[(index + 1) % facet.vertices.size()];
        float currentX = 0.0f;
        float currentY = 0.0f;
        float nextX = 0.0f;
        float nextY = 0.0f;
        projectPoint(current, dropAxis, currentX, currentY);
        projectPoint(next, dropAxis, nextX, nextY);

        if (projectedPointOnSegment(px, py, currentX, currentY, nextX, nextY))
        {
            return true;
        }

        if ((currentY > py) == (nextY > py))
        {
            continue;
        }

        const float intersectionX = (nextX - currentX) * (py - currentY) / (nextY - currentY) + currentX;

        if (px < intersectionX)
        {
            inside = !inside;
        }
    }

    return inside;
}

float pointFacetDistanceSquared(const PathPoint &point, const PathFacet &facet, const PathPoint &normal)
{
    const float distance = pointDot(normal, pointSubtract(point, facet.vertices.front()));
    const PathPoint projected = pointSubtract(point, pointScale(normal, distance));
    if (pointInsideFacet(projected, facet, normal))
    {
        return distance * distance;
    }
    float nearest = std::numeric_limits<float>::max();
    for (size_t edge = 0; edge < facet.vertices.size(); ++edge)
    {
        nearest = std::min(nearest, pointSegmentDistanceSquared(point, facet.vertices[edge],
            facet.vertices[(edge + 1) % facet.vertices.size()]));
    }
    return nearest;
}

bool segmentIntersectsFacet(
    const PathPoint &from,
    const PathPoint &to,
    const PathFacet &facet,
    const PathPoint &normal,
    PathPoint &outPoint
)
{
    if (facet.vertices.size() < 3 || pointLengthSquared(normal) <= PathEpsilon)
    {
        return false;
    }

    const PathPoint segment = pointSubtract(to, from);
    const float denominator = pointDot(normal, segment);

    if (std::fabs(denominator) <= PathEpsilon)
    {
        return false;
    }

    const float t = pointDot(normal, pointSubtract(facet.vertices.front(), from)) / denominator;

    if (t < -PathEpsilon || t > 1.0f + PathEpsilon)
    {
        return false;
    }

    outPoint = interpolatePoint(from, to, std::clamp(t, 0.0f, 1.0f));
    return pointInsideFacet(outPoint, facet, normal);
}

bool facetBlocksBodyOverlap(const PathFacet &facet, const PathPoint &normal)
{
    if (facet.kind == PathFacetKind::Floor
        || facet.kind == PathFacetKind::Ceiling
        || facet.kind == PathFacetKind::Portal
        || facet.walkableFloor)
    {
        return false;
    }

    if (facet.kind != PathFacetKind::Wall && std::fabs(normal.z) >= 0.5f)
    {
        return false;
    }

    return true;
}

bool segmentMovesIntoFacetBodyOverlap(
    const PathPoint &from,
    const PathPoint &to,
    const PathFacet &facet,
    const PathPoint &normal,
    float radius,
    PathPoint &outPoint
)
{
    if (radius <= PathEpsilon || !facetBlocksBodyOverlap(facet, normal))
    {
        return false;
    }

    const float fromSignedDistance = pointDot(normal, pointSubtract(from, facet.vertices.front()));
    const float toSignedDistance = pointDot(normal, pointSubtract(to, facet.vertices.front()));
    const float fromDistance = std::fabs(fromSignedDistance);
    const float toDistance = std::fabs(toSignedDistance);

    if (toDistance >= radius - PathEpsilon)
    {
        return false;
    }

    const PathPoint projectedPoint = pointSubtract(to, pointScale(normal, toSignedDistance));

    if (!pointInsideFacet(projectedPoint, facet, normal))
    {
        return false;
    }

    const bool startedInsideWallRadius = fromDistance <= radius + 0.5f;
    const bool stayedOnSameSide =
        fromSignedDistance == 0.0f
        || toSignedDistance == 0.0f
        || (fromSignedDistance > 0.0f) == (toSignedDistance > 0.0f);
    const bool didNotMoveTowardWall = toDistance >= fromDistance - 0.5f;

    if (startedInsideWallRadius && stayedOnSameSide && didNotMoveTowardWall)
    {
        return false;
    }

    outPoint = projectedPoint;
    return true;
}

bool bodyTraceIsNonBlockingContact(
    const PathPoint &from,
    const PathPoint &to,
    const PathFacet &facet,
    const PathPoint &normal,
    const PathPoint &hitPoint,
    float radius
)
{
    if (!facetBlocksBodyOverlap(facet, normal))
    {
        return false;
    }

    const float fromDistance = pointDot(normal, pointSubtract(from, facet.vertices.front()));
    const float toDistance = pointDot(normal, pointSubtract(to, facet.vertices.front()));
    const bool sameSide = fromDistance * toDistance > 0.0f;

    if (sameSide && std::min(std::fabs(fromDistance), std::fabs(toDistance)) >= radius - PathEpsilon)
    {
        return true;
    }

    if (sameSide
        && std::fabs(fromDistance) <= radius + PathEpsilon
        && std::fabs(toDistance) > std::fabs(fromDistance) + PathEpsilon)
    {
        const PathPoint projectedFrom = pointSubtract(from, pointScale(normal, fromDistance));

        if (pointInsideFacet(projectedFrom, facet, normal))
        {
            return true;
        }
    }

    bool touchesEdge = false;

    for (size_t index = 0; index < facet.vertices.size(); ++index)
    {
        const PathPoint &edgeFrom = facet.vertices[index];
        const PathPoint &edgeTo = facet.vertices[(index + 1) % facet.vertices.size()];

        if (pointSegmentDistanceSquared(hitPoint, edgeFrom, edgeTo) <= PathEpsilon * PathEpsilon)
        {
            if (segmentDistanceSquared(from, to, edgeFrom, edgeTo) < radius * radius - PathEpsilon)
            {
                return false;
            }

            touchesEdge = true;
        }
    }

    return touchesEdge;
}

bool facetIsNonBlocking(const PathFacet &facet)
{
    return !facet.blocking
        || facet.attributes.portal
        || facet.kind == PathFacetKind::Portal
        || (facet.attributes.invisible && facet.attributes.untouchable);
}
}

void PathMap::clear()
{
    m_facets.clear();
    m_geometry.clear();
    m_floorFacetIndices.clear();
    m_spatialGrid.clear();
    m_floorGrid.clear();
    m_spatialGridFacets.clear();
    m_floorGridFacets.clear();
    m_largeSpatialFacets.clear();
    ++m_revision;
}

void PathMap::setFacets(std::vector<PathFacet> facets)
{
    m_facets = std::move(facets);
    rebuildGeometry();
    ++m_revision;
}

size_t PathMap::addFacet(const PathFacet &facet)
{
    m_facets.push_back(facet);
    rebuildGeometry();
    ++m_revision;
    return m_facets.size() - 1;
}

void PathMap::buildSpatialGrid(float cellSize)
{
    m_gridCellSize = std::max(0.0f, cellSize);
    rebuildSpatialGrid();
}

const std::vector<PathFacet> &PathMap::facets() const
{
    return m_facets;
}

size_t PathMap::revision() const
{
    return m_revision;
}

PathFloorSample PathMap::floorAt(const PathPoint &position) const
{
    return debugFloorQuery(position).result;
}

PathPoint PathMap::snapToWalkableSourceFacet(
    int32_t sourceId,
    const PathPoint &position,
    float maxDistance,
    bool &valid,
    PathFloorSample *pFloorSample) const
{
    valid = false;

    if (sourceId < 0 || !pointIsFinite(position) || !std::isfinite(maxDistance) || maxDistance < 0.0f)
    {
        return position;
    }

    const auto sampleFacet = [&](size_t facetIndex, const PathPoint &probe, PathFloorSample &sample) -> bool
    {
        if (facetIndex >= m_facets.size() || facetIndex >= m_geometry.size())
        {
            return false;
        }

        const PathFacet &facet = m_facets[facetIndex];
        const FacetGeometry &geometry = m_geometry[facetIndex];

        if (!facet.walkableFloor || !geometry.valid || std::fabs(geometry.normal.z) <= PathEpsilon)
        {
            return false;
        }

        if (probe.x < geometry.bounds.minX - PathEpsilon
            || probe.x > geometry.bounds.maxX + PathEpsilon
            || probe.y < geometry.bounds.minY - PathEpsilon
            || probe.y > geometry.bounds.maxY + PathEpsilon)
        {
            return false;
        }

        const float z =
            facet.vertices.front().z
            - (geometry.normal.x * (probe.x - facet.vertices.front().x)
                + geometry.normal.y * (probe.y - facet.vertices.front().y)) / geometry.normal.z;
        const PathPoint floorPoint = {probe.x, probe.y, z};

        if (!pointInsideFacet(floorPoint, facet, geometry.normal))
        {
            return false;
        }

        sample.hasFloor = true;
        sample.inVoid = z > probe.z + PathEpsilon;
        sample.z = z;
        sample.normalZ = geometry.normal.z;
        sample.facetIndex = facetIndex;
        return true;
    };

    for (size_t facetIndex = 0; facetIndex < m_facets.size(); ++facetIndex)
    {
        const PathFacet &facet = m_facets[facetIndex];

        if (facet.sourceId != sourceId || !facet.walkableFloor || facet.vertices.empty())
        {
            continue;
        }

        PathFloorSample directSample = {};

        if (sampleFacet(facetIndex, position, directSample) && !directSample.inVoid)
        {
            valid = true;

            if (pFloorSample != nullptr)
            {
                *pFloorSample = directSample;
            }

            return {position.x, position.y, directSample.z};
        }

        PathPoint closestPoint = {facet.vertices.front().x, facet.vertices.front().y, position.z};
        float closestDistanceSquared = distanceSquared2d(position, closestPoint);
        PathPoint centroid = {};

        for (const PathPoint &vertex : facet.vertices)
        {
            centroid.x += vertex.x;
            centroid.y += vertex.y;
        }

        centroid.x /= static_cast<float>(facet.vertices.size());
        centroid.y /= static_cast<float>(facet.vertices.size());
        centroid.z = position.z;

        for (size_t vertexIndex = 0; vertexIndex < facet.vertices.size(); ++vertexIndex)
        {
            const PathPoint &from = facet.vertices[vertexIndex];
            const PathPoint &to = facet.vertices[(vertexIndex + 1) % facet.vertices.size()];
            const PathPoint edgePoint = closestPointOnSegment2d(position, from, to);
            const float edgeDistanceSquared = distanceSquared2d(position, edgePoint);

            if (edgeDistanceSquared < closestDistanceSquared)
            {
                closestDistanceSquared = edgeDistanceSquared;
                closestPoint = edgePoint;
            }
        }

        if (closestDistanceSquared > maxDistance * maxDistance)
        {
            continue;
        }

        const float inwardX = centroid.x - closestPoint.x;
        const float inwardY = centroid.y - closestPoint.y;
        const float inwardLength = std::sqrt(inwardX * inwardX + inwardY * inwardY);
        const std::array<float, 9> inwardDistances = {{
            128.0f,
            96.0f,
            64.0f,
            48.0f,
            32.0f,
            16.0f,
            8.0f,
            4.0f,
            0.0f
        }};

        for (float inwardDistance : inwardDistances)
        {
            PathPoint probe = closestPoint;

            if (inwardLength > PathEpsilon && inwardDistance > 0.0f)
            {
                probe.x += inwardX / inwardLength * inwardDistance;
                probe.y += inwardY / inwardLength * inwardDistance;
            }

            probe.z = position.z;
            PathFloorSample sample = {};

            if (!sampleFacet(facetIndex, probe, sample) || sample.inVoid)
            {
                continue;
            }

            valid = true;

            if (pFloorSample != nullptr)
            {
                *pFloorSample = sample;
            }

            return {probe.x, probe.y, sample.z};
        }
    }

    return position;
}

PathPoint PathMap::snapToNearestWalkableFloor(
    const PathPoint &position,
    float maxDistance,
    bool &valid,
    PathFloorSample *pFloorSample) const
{
    valid = false;

    if (!pointIsFinite(position) || !std::isfinite(maxDistance) || maxDistance < 0.0f)
    {
        return position;
    }

    PathPoint bestPoint = position;
    PathFloorSample bestSample = {};
    float bestDistanceSquared = std::numeric_limits<float>::max();

    for (size_t facetIndex : m_floorFacetIndices)
    {
        if (facetIndex >= m_facets.size() || facetIndex >= m_geometry.size())
        {
            continue;
        }

        const PathFacet &facet = m_facets[facetIndex];
        const FacetGeometry &geometry = m_geometry[facetIndex];

        if (!facet.walkableFloor || !geometry.valid || std::fabs(geometry.normal.z) <= PathEpsilon)
        {
            continue;
        }

        PathPoint closestPoint = {facet.vertices.front().x, facet.vertices.front().y, position.z};
        float closestDistanceSquared = distanceSquared2d(position, closestPoint);
        PathPoint centroid = {};

        for (const PathPoint &vertex : facet.vertices)
        {
            centroid.x += vertex.x;
            centroid.y += vertex.y;
        }

        centroid.x /= static_cast<float>(facet.vertices.size());
        centroid.y /= static_cast<float>(facet.vertices.size());
        centroid.z = position.z;

        for (size_t vertexIndex = 0; vertexIndex < facet.vertices.size(); ++vertexIndex)
        {
            const PathPoint &from = facet.vertices[vertexIndex];
            const PathPoint &to = facet.vertices[(vertexIndex + 1) % facet.vertices.size()];
            const PathPoint edgePoint = closestPointOnSegment2d(position, from, to);
            const float edgeDistanceSquared = distanceSquared2d(position, edgePoint);

            if (edgeDistanceSquared < closestDistanceSquared)
            {
                closestDistanceSquared = edgeDistanceSquared;
                closestPoint = edgePoint;
            }
        }

        if (closestDistanceSquared > maxDistance * maxDistance
            || closestDistanceSquared >= bestDistanceSquared)
        {
            continue;
        }

        const float inwardX = centroid.x - closestPoint.x;
        const float inwardY = centroid.y - closestPoint.y;
        const float inwardLength = std::sqrt(inwardX * inwardX + inwardY * inwardY);
        const std::array<float, 9> inwardDistances = {{
            128.0f,
            96.0f,
            64.0f,
            48.0f,
            32.0f,
            16.0f,
            8.0f,
            4.0f,
            0.0f
        }};

        for (float inwardDistance : inwardDistances)
        {
            PathPoint probe = closestPoint;

            if (inwardLength > PathEpsilon && inwardDistance > 0.0f)
            {
                probe.x += inwardX / inwardLength * inwardDistance;
                probe.y += inwardY / inwardLength * inwardDistance;
            }

            probe.z = position.z;
            const PathFloorSample sample = floorAt(probe);

            if (!sample.hasFloor || sample.inVoid)
            {
                continue;
            }

            valid = true;
            bestDistanceSquared = closestDistanceSquared;
            bestSample = sample;
            bestPoint = {probe.x, probe.y, sample.z};
            break;
        }
    }

    if (!valid)
    {
        return position;
    }

    if (pFloorSample != nullptr)
    {
        *pFloorSample = bestSample;
    }

    return bestPoint;
}

PathFloorQueryDebug PathMap::debugFloorQuery(const PathPoint &position) const
{
    if (!pointIsFinite(position))
    {
        PathFloorQueryDebug debug = {};
        debug.position = position;
        debug.result.inVoid = true;
        return debug;
    }

    PathFloorQueryDebug debug = {};
    debug.position = position;
    float bestBelowDistance = std::numeric_limits<float>::max();
    float bestAboveDistance = std::numeric_limits<float>::max();

    const std::span<const size_t> candidates = candidateFloorFacetsForPoint(position.x, position.y);
    debug.candidateCount = candidates.size();

    for (size_t index : candidates)
    {
        if (index >= m_facets.size() || index >= m_geometry.size())
        {
            ++debug.invalidFacetCount;
            continue;
        }

        const PathFacet &facet = m_facets[index];
        const FacetGeometry &geometry = m_geometry[index];

        if (!facet.walkableFloor || !geometry.valid || std::fabs(geometry.normal.z) <= PathEpsilon)
        {
            ++debug.nonWalkableCount;
            continue;
        }

        if (position.x < geometry.bounds.minX - PathEpsilon
            || position.x > geometry.bounds.maxX + PathEpsilon
            || position.y < geometry.bounds.minY - PathEpsilon
            || position.y > geometry.bounds.maxY + PathEpsilon)
        {
            ++debug.boundsRejectCount;
            continue;
        }

        const float z =
            facet.vertices.front().z
            - (geometry.normal.x * (position.x - facet.vertices.front().x)
                + geometry.normal.y * (position.y - facet.vertices.front().y)) / geometry.normal.z;
        const PathPoint floorPoint = {position.x, position.y, z};

        if (!pointInsideFacet(floorPoint, facet, geometry.normal))
        {
            ++debug.polygonRejectCount;
            continue;
        }

        if (z <= position.z + PathEpsilon)
        {
            const float distance = position.z - z;
            ++debug.belowCount;

            if (distance < bestBelowDistance)
            {
                bestBelowDistance = distance;
                debug.bestBelow.hasFloor = true;
                debug.bestBelow.inVoid = false;
                debug.bestBelow.z = z;
                debug.bestBelow.normalZ = geometry.normal.z;
                debug.bestBelow.facetIndex = index;
            }
        }
        else
        {
            const float distance = z - position.z;
            ++debug.aboveCount;

            if (distance < bestAboveDistance)
            {
                bestAboveDistance = distance;
                debug.bestAbove.hasFloor = true;
                debug.bestAbove.inVoid = true;
                debug.bestAbove.z = z;
                debug.bestAbove.normalZ = geometry.normal.z;
                debug.bestAbove.facetIndex = index;
            }
        }
    }

    if (debug.bestBelow.hasFloor)
    {
        debug.result = debug.bestBelow;
        return debug;
    }

    if (debug.bestAbove.hasFloor)
    {
        debug.result = debug.bestAbove;
        return debug;
    }

    debug.result.inVoid = true;
    return debug;
}

PathTraceResult PathMap::traceLine(
    const PathPoint &from,
    const PathPoint &to,
    float radius,
    bool checkBody
) const
{
    TraceCandidateCache cache;
    return traceLineInternal(from, to, radius, checkBody, &cache);
}

bool PathMap::isSteppableRiser(const FacetGeometry &geometry, float fromFloorZ, float riserHeight) const
{
    // The floor sampling along the walk already limits each rise to a step; a face the low probes touch ahead whose
    // top is within riserHeight of the floor the body walks from (a riser or tread of a stair whose treads are
    // shorter than the body's radius) is one it climbs, not a wall.
    return riserHeight > 0.0f && geometry.bounds.maxZ <= fromFloorZ + riserHeight + PathEpsilon;
}

bool PathMap::isClimbedStepFace(
    const PathFacet &facet,
    const FacetGeometry &geometry,
    const PathPoint &from,
    const PathPoint &to,
    const PathObject &object) const
{
    if (!isSteppableRiser(geometry, from.z, object.riserHeight))
    {
        return false;
    }

    const float topZ = geometry.bounds.maxZ;

    if (facet.kind == PathFacetKind::Ceiling || geometry.normal.z < -0.5f)
    {
        // A slab step's underside: its tread lies just above it.
        PathPoint centre = {};

        for (const PathPoint &vertex : facet.vertices)
        {
            centre = pointAdd(centre, vertex);
        }

        centre = pointScale(centre, 1.0f / static_cast<float>(facet.vertices.size()));
        const PathFloorSample tread = floorAt({centre.x, centre.y, topZ + StepSlabMaxThickness});
        return tread.hasFloor && !tread.inVoid && tread.z >= topZ - PathEpsilon;
    }

    const float horizontalLength =
        std::sqrt(geometry.normal.x * geometry.normal.x + geometry.normal.y * geometry.normal.y);
    const float moveLength = xyDistance(from, to);

    // A riser faces the way the body climbs or descends. A stair's side (its stringer) runs along that way and
    // still keeps the body off.
    if (horizontalLength <= PathEpsilon
        || moveLength <= PathEpsilon
        || std::fabs(geometry.normal.x * (to.x - from.x) + geometry.normal.y * (to.y - from.y))
            < RiserMinimumFacing * horizontalLength * moveLength)
    {
        return false;
    }

    // A riser: a tread meets its top edge on one side. A railing or a parapet has none and still blocks.
    PathPoint topEdge = {};
    float topVertexCount = 0.0f;

    for (const PathPoint &vertex : facet.vertices)
    {
        if (vertex.z >= topZ - RiserTreadHeightTolerance)
        {
            topEdge = pointAdd(topEdge, vertex);
            topVertexCount += 1.0f;
        }
    }

    topEdge = pointScale(topEdge, 1.0f / topVertexCount);
    const float awayX = geometry.normal.x / horizontalLength * RiserTreadProbeDistance;
    const float awayY = geometry.normal.y / horizontalLength * RiserTreadProbeDistance;

    for (const float side : {1.0f, -1.0f})
    {
        const PathFloorSample tread =
            floorAt({topEdge.x + awayX * side, topEdge.y + awayY * side, topZ + RiserTreadHeightTolerance});

        if (tread.hasFloor && !tread.inVoid && std::fabs(tread.z - topZ) <= RiserTreadHeightTolerance)
        {
            return true;
        }
    }

    return false;
}

PathTraceResult PathMap::traceLineInternal(
    const PathPoint &from,
    const PathPoint &to,
    float radius,
    bool checkBody,
    TraceCandidateCache *pCache,
    float riserHeight,
    bool probeVerticalMoves) const
{
    if (!pointIsFinite(from) || !pointIsFinite(to) || !std::isfinite(radius))
    {
        PathTraceResult result = {};
        result.blocked = true;
        return result;
    }

    std::array<std::pair<PathPoint, PathPoint>, 9> traces = {};
    size_t traceCount = 1;
    traces[0] = {from, to};

    const float xyLength = xyDistance(from, to);

    // A straight climb or drop has no direction across: its probes take the axes (probeVerticalMoves), or its centre
    // line alone slipped through the seam between two floor faces, a route no body could follow.
    const bool verticalMove = xyLength <= PathEpsilon;

    if (checkBody && radius > PathEpsilon && (!verticalMove || probeVerticalMoves))
    {
        constexpr float DiagonalOffsetScale = 0.70710678f;
        const float forwardX = verticalMove ? 1.0f : (to.x - from.x) / xyLength;
        const float forwardY = verticalMove ? 0.0f : (to.y - from.y) / xyLength;
        const float sideX = -forwardY;
        const float sideY = forwardX;
        const std::array<PathPoint, 8> offsets = {{
            {sideX * radius, sideY * radius, 0.0f},
            {-sideX * radius, -sideY * radius, 0.0f},
            {forwardX * radius, forwardY * radius, 0.0f},
            {-forwardX * radius, -forwardY * radius, 0.0f},
            {(sideX + forwardX) * radius * DiagonalOffsetScale,
                (sideY + forwardY) * radius * DiagonalOffsetScale,
                0.0f},
            {(sideX - forwardX) * radius * DiagonalOffsetScale,
                (sideY - forwardY) * radius * DiagonalOffsetScale,
                0.0f},
            {(-sideX + forwardX) * radius * DiagonalOffsetScale,
                (-sideY + forwardY) * radius * DiagonalOffsetScale,
                0.0f},
            {(-sideX - forwardX) * radius * DiagonalOffsetScale,
                (-sideY - forwardY) * radius * DiagonalOffsetScale,
                0.0f}
        }};

        for (const PathPoint &offset : offsets)
        {
            traces[traceCount++] = {pointAdd(from, offset), pointAdd(to, offset)};
        }
    }

    PathTraceResult result = {};
    std::vector<size_t> candidates;

    for (size_t traceIndex = 0; traceIndex < traceCount; ++traceIndex)
    {
        const std::pair<PathPoint, PathPoint> &trace = traces[traceIndex];
        const PathBounds bounds = segmentBounds(trace.first, trace.second, radius);
        candidateFacetsForBounds(bounds, candidates, pCache);

        for (size_t facetIndex : candidates)
        {
            if (facetIndex >= m_facets.size() || facetIndex >= m_geometry.size())
            {
                continue;
            }

            const PathFacet &facet = m_facets[facetIndex];
            const FacetGeometry &geometry = m_geometry[facetIndex];

            if (!geometry.valid || geometry.nonBlocking || !boundsOverlap(bounds, geometry.bounds))
            {
                continue;
            }

            PathPoint hitPoint = {};

            if (segmentIntersectsFacet(trace.first, trace.second, facet, geometry.normal, hitPoint))
            {
                // Radius probes may touch a wall or doorway edge without penetrating it,
                // including when leaving an existing contact. Center crossings still block.
                if (traceIndex > 0
                    && bodyTraceIsNonBlockingContact(from, to, facet, geometry.normal, hitPoint, radius))
                {
                    continue;
                }

                // A radius probe at the body's height reaches a stair's next riser before the body has climbed the
                // tread in between (a tread shorter than the radius): isSteppableRiser.
                if (traceIndex > 0 && isSteppableRiser(geometry, from.z - radius, riserHeight))
                {
                    continue;
                }

                result.blocked = true;
                result.facetIndex = facetIndex;
                result.point = hitPoint;
                return result;
            }

            if (traceIndex == 0
                && checkBody
                && segmentMovesIntoFacetBodyOverlap(
                    trace.first,
                    trace.second,
                    facet,
                    geometry.normal,
                    radius,
                    hitPoint)
                && !isSteppableRiser(geometry, from.z - radius, riserHeight))
            {
                result.blocked = true;
                result.facetIndex = facetIndex;
                result.point = hitPoint;
                return result;
            }
        }
    }

    return result;
}

bool PathMap::traceWalkSegment(const PathPoint &from, const PathPoint &to, const PathObject &object) const
{
    return traceWalkSegmentInternal(from, to, object, nullptr);
}

bool PathMap::resolveWalkStep(const PathPoint &from, PathPoint &to, const PathObject &object) const
{
    if (!pointIsFinite(from) || !pointIsFinite(to) || !std::isfinite(object.radius)
        || !std::isfinite(object.height) || object.height < 0.0f
        || !std::isfinite(object.stepLength) || !std::isfinite(object.stepHeight) || !std::isfinite(object.dropHeight))
    {
        return false;
    }
    // A descending body leaves its upper support before falling; its floor
    // endpoint may temporarily overlap the side of that support.
    if (to.z < from.z - PathEpsilon && traceWalkSegment(from, to, object))
    {
        return true;
    }

    const PathPoint requestedTarget = to;
    PathPoint candidate = to;
    const float maxAdjustment = object.stepLength * 0.5f;
    const float nearbyRadius = object.radius + maxAdjustment;
    std::vector<size_t> nearbyFacets;
    candidateFacetsForBounds(segmentBounds(to, to, nearbyRadius), nearbyFacets);

    for (int attempt = 0; attempt < 4; ++attempt)
    {
        const PathPoint center = {candidate.x, candidate.y, candidate.z + object.radius};
        float nearestAdjustment = std::numeric_limits<float>::max();
        PathPoint adjustmentNormal = {};
        bool hasUnresolvedOverlap = false;
        for (size_t facetIndex : nearbyFacets)
        {
            const PathFacet &facet = m_facets[facetIndex];
            const FacetGeometry &geometry = m_geometry[facetIndex];
            const PathPoint &normal = geometry.normal;
            if (!geometry.valid || geometry.nonBlocking || !facetBlocksBodyOverlap(facet, normal)
                || std::fabs(normal.z) > PathEpsilon
                || geometry.bounds.maxZ <= candidate.z + object.stepHeight + PathEpsilon)
            {
                continue;
            }
            const float distance = pointDot(normal, pointSubtract(center, facet.vertices.front()));
            if (std::fabs(distance) >= object.radius - PathEpsilon)
            {
                continue;
            }
            const float distanceSquared = pointFacetDistanceSquared(center, facet, normal);
            if (distanceSquared > nearbyRadius * nearbyRadius)
            {
                continue;
            }

            const float sourceDistance = pointDot(normal, pointSubtract(from, facet.vertices.front()));
            const float side = sourceDistance < 0.0f ? -1.0f : 1.0f;
            const PathPoint awayNormal = pointScale(normal, side);
            float adjustment = object.radius + PathEpsilon - distance * side;
            const bool overlapsBody = distanceSquared < object.radius * object.radius - PathEpsilon;

            float oppositeAllowance = std::numeric_limits<float>::max();
            for (size_t oppositeIndex : nearbyFacets)
            {
                const PathFacet &oppositeFacet = m_facets[oppositeIndex];
                const FacetGeometry &oppositeGeometry = m_geometry[oppositeIndex];
                const float alignment = pointDot(oppositeGeometry.normal, awayNormal);
                if (!oppositeGeometry.valid || oppositeGeometry.nonBlocking
                    || !facetBlocksBodyOverlap(oppositeFacet, oppositeGeometry.normal)
                    || std::fabs(alignment) < 1.0f - PathEpsilon
                    || oppositeGeometry.bounds.maxZ <= candidate.z + object.stepHeight + PathEpsilon)
                {
                    continue;
                }
                const float oppositeDistance = pointDot(
                    oppositeGeometry.normal, pointSubtract(center, oppositeFacet.vertices.front()));
                if (oppositeDistance * alignment >= 0.0f
                    || pointFacetDistanceSquared(center, oppositeFacet, oppositeGeometry.normal)
                        > nearbyRadius * nearbyRadius)
                {
                    continue;
                }
                oppositeAllowance = std::min(
                    oppositeAllowance, std::fabs(oppositeDistance) - object.radius - PathEpsilon);
            }
            if (!overlapsBody && oppositeAllowance == std::numeric_limits<float>::max())
            {
                continue;
            }
            if (oppositeAllowance < adjustment)
            {
                // A different wall adjustment may clear this corner. Reject the
                // direction, then validate the final move against every face.
                hasUnresolvedOverlap = hasUnresolvedOverlap || overlapsBody;
                continue;
            }
            if (oppositeAllowance < std::numeric_limits<float>::max())
            {
                // Align before entering the rounded doorway corners, not only
                // once the endpoint overlaps them. Late alignment can clip the jamb.
                adjustment = (adjustment + oppositeAllowance) * 0.5f;
            }
            if (!overlapsBody && adjustment > maxAdjustment)
            {
                continue;
            }
            if (adjustment < nearestAdjustment)
            {
                nearestAdjustment = adjustment;
                adjustmentNormal = awayNormal;
            }
        }

        if (nearestAdjustment == std::numeric_limits<float>::max())
        {
            if (hasUnresolvedOverlap || !traceWalkSegment(from, candidate, object))
            {
                return false;
            }
            to = candidate;
            return true;
        }

        // A fixed search lattice can miss the entire usable width of a narrow
        // passage. Align this neighbor to wall clearance, within half a step,
        // while retaining the actor's radius and validating the complete move.
        candidate.x += adjustmentNormal.x * nearestAdjustment;
        candidate.y += adjustmentNormal.y * nearestAdjustment;
        if (xyDistance(candidate, requestedTarget) > maxAdjustment)
        {
            return false;
        }
        const PathFloorSample floor = floorAt({candidate.x, candidate.y, requestedTarget.z + object.stepHeight});
        if (!floor.hasFloor || floor.inVoid || !walkStepDeltaAllowed(from.z, floor.z, object))
        {
            return false;
        }
        candidate.z = floor.z;
    }

    return false;
}

PathWalkSegmentDebug PathMap::debugTraceWalkSegment(
    const PathPoint &from,
    const PathPoint &to,
    const PathObject &object
) const
{
    PathWalkSegmentDebug debug = {};
    debug.from = from;
    debug.to = to;

    traceWalkSegmentInternal(from, to, object, &debug);
    return debug;
}

PathTraceResult PathMap::traceWalkBody(
    const PathPoint &from,
    const PathPoint &to,
    const PathObject &object,
    TraceCandidateCache &cache) const
{
    if (object.radius > PathEpsilon)
    {
        // Most floor samples are in open space. Enclose all radius probes and the
        // upper-body checks before generating their individual collision queries.
        PathBounds bodyBounds = segmentBounds(from, to, object.radius * 2.0f);
        bodyBounds.minZ = std::min(from.z, to.z);
        bodyBounds.maxZ = std::max(from.z, to.z) + std::max(object.height, object.radius * 2.0f);
        if (boundsAreFinite(bodyBounds))
        {
            std::vector<size_t> nearbyFacets;
            candidateFacetsForBounds(bodyBounds, nearbyFacets, &cache);
            const float lowestProbeZ = std::min(from.z, to.z) + object.radius;
            const bool hasObstacle = std::any_of(nearbyFacets.begin(), nearbyFacets.end(),
                [this, lowestProbeZ](size_t facetIndex)
                {
                    const FacetGeometry &geometry = m_geometry[facetIndex];
                    return geometry.valid && !geometry.nonBlocking
                        && (!m_facets[facetIndex].walkableFloor
                            || geometry.bounds.maxZ >= lowestProbeZ - PathEpsilon);
                });
            if (!hasObstacle)
            {
                return {};
            }
        }
    }

    const PathPoint lowFrom = {from.x, from.y, from.z + object.radius};
    const PathPoint lowTo = {to.x, to.y, to.z + object.radius};
    PathTraceResult result = traceLineInternal(lowFrom, lowTo, object.radius, true, &cache, object.riserHeight);
    if (result.blocked || object.height <= 0.0f)
    {
        return result;
    }

    const float highOffset = std::max(object.radius, object.height - object.radius);
    const PathPoint highFrom = {from.x, from.y, from.z + highOffset};
    const PathPoint highTo = {to.x, to.y, to.z + highOffset};
    // A squat body (wider than it is tall), indoors: its upper sphere sits at its radius. It would reach down into the
    // stair the low probes climb (the next tread's riser, a slab step's underside) and need 2R of headroom where the
    // body is H tall: the obstacle loop skips both.
    const bool squatBody = object.riserHeight > 0.0f && object.height < 2.0f * object.radius;
    if (highOffset > object.radius + PathEpsilon)
    {
        result = traceLineInternal(highFrom, highTo, object.radius, true, &cache);
        if (result.blocked)
        {
            return result;
        }
    }

    // Horizontal radius probes alone miss low ceilings and sloped overhangs.
    // Include obstacle-height probes between the end spheres, as movement does.
    PathBounds bounds = segmentBounds(highFrom, highTo, object.radius);
    bounds.minZ = std::min({bounds.minZ, from.z, to.z});
    bounds.maxZ = std::max(bounds.maxZ, to.z + object.height);
    std::vector<size_t> candidates;
    candidateFacetsForBounds(bounds, candidates, &cache);
    for (size_t facetIndex : candidates)
    {
        const PathFacet &facet = m_facets[facetIndex];
        const FacetGeometry &geometry = m_geometry[facetIndex];
        if (!geometry.valid || geometry.nonBlocking || !boundsOverlap(bounds, geometry.bounds)
            || facet.walkableFloor)
        {
            continue;
        }

        // Movement steps over low wall faces before resolving body contacts.
        // Floor sampling enforces the rise limit; upper probes must not reject
        // that same riser while the feet are still on the lower floor.
        if (facet.kind == PathFacetKind::Wall
            && geometry.bounds.maxZ <= from.z + std::max(0.0f, object.stepHeight) + PathEpsilon)
        {
            continue;
        }

        // A squat body's sphere reaches 2R up and down to its feet: it ignores what lies wholly over its head and the
        // steps it climbs.
        if (squatBody
            && (geometry.bounds.minZ >= std::max(from.z, to.z) + object.height - PathEpsilon
                || isClimbedStepFace(facet, geometry, from, to, object)))
        {
            continue;
        }

        PathPoint hitPoint = {};
        const PathPoint head = {to.x, to.y, to.z + object.height};
        const float faceHeightOffset =
            std::clamp((geometry.bounds.minZ + geometry.bounds.maxZ) * 0.5f - from.z, object.radius, highOffset);
        const PathPoint faceFrom = {from.x, from.y, from.z + faceHeightOffset};
        const PathPoint faceTo = {to.x, to.y, to.z + faceHeightOffset};
        const bool checkFaceHeight = faceHeightOffset > object.radius + PathEpsilon
            && faceHeightOffset < highOffset - PathEpsilon;
        const bool bodyAxisBlocked = segmentIntersectsFacet(to, head, facet, geometry.normal, hitPoint)
            && hitPoint.z > to.z + PathEpsilon && hitPoint.z < head.z - PathEpsilon;
        bool blocked = bodyAxisBlocked
            || (checkFaceHeight && segmentIntersectsFacet(faceFrom, faceTo, facet, geometry.normal, hitPoint));
        // Descending from a tread temporarily overlaps its side while falling.
        // The lower trace already validates that step; upper-body clearance must
        // not turn the support being left into an overhead obstruction.
        if (!blocked && geometry.bounds.maxZ > from.z + PathEpsilon)
        {
            const std::array<std::pair<PathPoint, PathPoint>, 2> probes = {{{highFrom, highTo}, {faceFrom, faceTo}}};
            const size_t probeCount = checkFaceHeight ? 2 : 1;
            for (size_t probeIndex = 0; probeIndex < probeCount && !blocked; ++probeIndex)
            {
                const std::pair<PathPoint, PathPoint> &probe = probes[probeIndex];
                const float endDistanceSquared = pointFacetDistanceSquared(probe.second, facet, geometry.normal);
                if (endDistanceSquared < object.radius * object.radius - PathEpsilon)
                {
                    const float startDistanceSquared = pointFacetDistanceSquared(probe.first, facet, geometry.normal);
                    // Existing contact may slide along or out of a surface, but
                    // a route must not push the body farther into it.
                    blocked = endDistanceSquared < startDistanceSquared - PathEpsilon;
                    hitPoint = probe.second;
                }
            }
        }
        if (blocked)
        {
            result.blocked = true;
            result.facetIndex = facetIndex;
            result.point = hitPoint;
            return result;
        }
    }
    return result;
}

bool PathMap::traceWalkSegmentInternal(
    const PathPoint &from,
    const PathPoint &to,
    const PathObject &object,
    PathWalkSegmentDebug *pDebug
) const
{
    if (!pointIsFinite(from)
        || !pointIsFinite(to)
        || !std::isfinite(object.radius)
        || !std::isfinite(object.height)
        || object.height < 0.0f
        || !std::isfinite(object.stepLength)
        || !std::isfinite(object.stepHeight)
        || !std::isfinite(object.dropHeight))
    {
        if (pDebug != nullptr)
        {
            pDebug->rejectReason = PathWalkRejectReason::InvalidInput;
        }

        return false;
    }

    const float distance = xyDistance(from, to);
    const float sampleStep = 2.0f;
    const size_t sampleCount = std::max<size_t>(1, static_cast<size_t>(std::ceil(distance / sampleStep)));
    const float stepHeight = std::max(0.0f, object.stepHeight);

    if (pDebug != nullptr)
    {
        pDebug->sampleCount = sampleCount;
    }

    PathPoint previousPoint = from;
    // Each check owns its cache, so worker snapshots and geometry changes cannot share stale candidates.
    TraceCandidateCache cache;
    PathFloorSample previousFloor = floorAt({from.x, from.y, from.z + stepHeight});

    if (pDebug != nullptr)
    {
        pDebug->startFloor = previousFloor;
        pDebug->previousFloor = previousFloor;
    }

    if (!previousFloor.hasFloor)
    {
        if (pDebug != nullptr)
        {
            pDebug->rejectReason = PathWalkRejectReason::StartNoFloor;
        }

        return false;
    }

    if (previousFloor.inVoid)
    {
        if (pDebug != nullptr)
        {
            pDebug->rejectReason = PathWalkRejectReason::StartVoid;
        }

        return false;
    }

    for (size_t sampleIndex = 1; sampleIndex <= sampleCount; ++sampleIndex)
    {
        const float t = static_cast<float>(sampleIndex) / static_cast<float>(sampleCount);
        const PathPoint probe = interpolatePoint(from, to, t);
        const PathFloorSample floor = floorAt({probe.x, probe.y, previousFloor.z + stepHeight + PathEpsilon});

        if (pDebug != nullptr)
        {
            pDebug->sampleIndex = sampleIndex;
            pDebug->probe = probe;
            pDebug->failedFloor = floor;
            pDebug->previousFloor = previousFloor;
        }

        if (!floor.hasFloor)
        {
            if (pDebug != nullptr)
            {
                pDebug->rejectReason = PathWalkRejectReason::SampleNoFloor;
            }

            return false;
        }

        if (floor.inVoid)
        {
            if (pDebug != nullptr)
            {
                pDebug->rejectReason = PathWalkRejectReason::SampleVoid;
            }

            return false;
        }

        if (!walkStepDeltaAllowed(previousFloor.z, floor.z, object))
        {
            if (pDebug != nullptr)
            {
                pDebug->rejectReason = PathWalkRejectReason::StepHeight;
                pDebug->stepDeltaZ = std::fabs(floor.z - previousFloor.z);
            }

            return false;
        }

        const PathPoint segmentFrom = {previousPoint.x, previousPoint.y, previousFloor.z};
        const PathPoint segmentTo = {probe.x, probe.y, floor.z};
        PathTraceResult traceResult;

        if (floor.facetIndex != previousFloor.facetIndex && floor.z < previousFloor.z - PathEpsilon)
        {
            // Leave the upper support before descending. A diagonal trace through
            // an abrupt floor-height change cuts through the step's vertical face.
            const PathPoint stepEdge = {probe.x, probe.y, segmentFrom.z};
            traceResult = traceWalkBody(segmentFrom, stepEdge, object, cache);
            if (!traceResult.blocked)
            {
                traceResult = traceWalkBody(stepEdge, segmentTo, object, cache);
            }
        }
        else
        {
            traceResult = traceWalkBody(segmentFrom, segmentTo, object, cache);
        }

        if (traceResult.blocked)
        {
            if (pDebug != nullptr)
            {
                pDebug->rejectReason = PathWalkRejectReason::Blocked;
                pDebug->blockedFacet = traceResult.facetIndex;
                pDebug->blockedPoint = traceResult.point;
            }

            return false;
        }

        previousPoint = probe;
        previousFloor = floor;
    }

    if (!walkStepDeltaAllowed(previousFloor.z, to.z, object))
    {
        if (pDebug != nullptr)
        {
            pDebug->rejectReason = PathWalkRejectReason::StepHeight;
            pDebug->failedFloor = previousFloor;
            pDebug->stepDeltaZ = std::fabs(to.z - previousFloor.z);
        }

        return false;
    }

    if (pDebug != nullptr)
    {
        pDebug->success = true;
        pDebug->rejectReason = PathWalkRejectReason::None;
        pDebug->previousFloor = previousFloor;
    }

    return true;
}

// A flyer's path points are its feet, and its back has to pass as well: traced at its feet alone, a door's opening was
// clear for a flyer whose back then hit the wall above the door, where it hovered for good.
PathTraceResult PathMap::traceFlyingBody(const PathPoint &from, const PathPoint &to, const PathObject &object) const
{
    TraceCandidateCache cache;
    PathTraceResult result = traceLineInternal(from, to, object.radius, true, &cache, 0.0f, true);
    const float topOffset = object.height - FlyingBodyTopClearance;

    if (result.blocked || topOffset <= PathEpsilon)
    {
        return result;
    }

    return traceLineInternal(pointAdd(from, {0.0f, 0.0f, topOffset}), pointAdd(to, {0.0f, 0.0f, topOffset}),
        object.radius, true, &cache, 0.0f, true);
}

bool PathMap::canReachDirectly(const PathPoint &from, const PathPoint &to, const PathObject &object) const
{
    if (object.canFly)
    {
        return !traceFlyingBody(from, to, object).blocked;
    }

    return traceWalkSegment(from, to, object);
}

void PathMap::candidateFacetsForBounds(
    const PathBounds &bounds,
    std::vector<size_t> &candidates,
    TraceCandidateCache *pCache) const
{
    candidates.clear();

    if (!boundsAreFinite(bounds))
    {
        return;
    }

    using OrderedFacet = std::tuple<int32_t, int32_t, int32_t, size_t>;
    struct CandidateScratch
    {
        std::vector<uint32_t> marks;
        uint32_t markId = 0;
        std::vector<OrderedFacet> orderedFacets;
    };

    thread_local CandidateScratch scratch;

    if (m_gridCellSize <= PathEpsilon || m_spatialGrid.empty())
    {
        candidates.reserve(m_facets.size());

        for (size_t index = 0; index < m_geometry.size(); ++index)
        {
            if (boundsOverlap(bounds, m_geometry[index].bounds))
            {
                candidates.push_back(index);
            }
        }

        return;
    }

    const int32_t minCellX = gridCoordinate(bounds.minX);
    const int32_t maxCellX = gridCoordinate(bounds.maxX);
    const int32_t minCellY = gridCoordinate(bounds.minY);
    const int32_t maxCellY = gridCoordinate(bounds.maxY);
    const int32_t minCellZ = gridCoordinate(bounds.minZ);
    const int32_t maxCellZ = gridCoordinate(bounds.maxZ);

    if (static_cast<int64_t>(maxCellX) - static_cast<int64_t>(minCellX) > MaxPathGridCellSpan
        || static_cast<int64_t>(maxCellY) - static_cast<int64_t>(minCellY) > MaxPathGridCellSpan
        || static_cast<int64_t>(maxCellZ) - static_cast<int64_t>(minCellZ) > MaxPathGridCellSpan)
    {
        candidates.reserve(m_facets.size());

        for (size_t index = 0; index < m_geometry.size(); ++index)
        {
            if (boundsOverlap(bounds, m_geometry[index].bounds))
            {
                candidates.push_back(index);
            }
        }

        return;
    }

    const uint64_t cellCountX = static_cast<int64_t>(maxCellX) - minCellX + 1;
    const uint64_t cellCountY = static_cast<int64_t>(maxCellY) - minCellY + 1;
    const uint64_t cellCountZ = static_cast<int64_t>(maxCellZ) - minCellZ + 1;
    // Long diagonal queries can cover thousands of empty cells in their bounding box.
    // The span checks above keep this multiplication bounded, including extreme coordinates.
    // Allow for candidate ordering, which also costs more than a single bounds check.
    if (cellCountX * cellCountY * cellCountZ / PathGridScanCostRatio > m_geometry.size())
    {
        scratch.orderedFacets.clear();
        for (size_t index = 0; index < m_geometry.size(); ++index)
        {
            const FacetGeometry &geometry = m_geometry[index];
            if (!geometry.valid || !boundsAreFinite(geometry.bounds) || !boundsOverlap(bounds, geometry.bounds))
            {
                continue;
            }
            // Match the set of faces actually inserted by rebuildSpatialGrid().
            if (static_cast<int64_t>(gridCoordinate(geometry.bounds.maxX))
                    - gridCoordinate(geometry.bounds.minX) > MaxPathGridCellSpan
                || static_cast<int64_t>(gridCoordinate(geometry.bounds.maxY))
                    - gridCoordinate(geometry.bounds.minY) > MaxPathGridCellSpan
                || static_cast<int64_t>(gridCoordinate(geometry.bounds.maxZ))
                    - gridCoordinate(geometry.bounds.minZ) > MaxPathGridCellSpan)
            {
                continue;
            }
            scratch.orderedFacets.emplace_back(
                std::max(minCellX, gridCoordinate(geometry.bounds.minX)),
                std::max(minCellY, gridCoordinate(geometry.bounds.minY)),
                std::max(minCellZ, gridCoordinate(geometry.bounds.minZ)), index);
        }
        // A face first appears in the earliest overlapping cell; faces within a cell
        // were inserted by index. Keep that order for first-hit traces and equal-clearance moves.
        std::sort(scratch.orderedFacets.begin(), scratch.orderedFacets.end());
        candidates.reserve(scratch.orderedFacets.size());
        for (const OrderedFacet &facet : scratch.orderedFacets)
        {
            candidates.push_back(std::get<3>(facet));
        }
        return;
    }

    TraceCandidateCache::Entry *pEntry = nullptr;
    if (pCache != nullptr)
    {
        const GridCellKey minCell = {minCellX, minCellY, minCellZ};
        const GridCellKey maxCell = {maxCellX, maxCellY, maxCellZ};
        for (const TraceCandidateCache::Entry &entry : pCache->entries)
        {
            if (entry.minCell == minCell && entry.maxCell == maxCell)
            {
                for (size_t facetIndex : entry.facets)
                {
                    if (boundsOverlap(bounds, m_geometry[facetIndex].bounds))
                    {
                        candidates.push_back(facetIndex);
                    }
                }
                return;
            }
        }

        constexpr size_t MaxTraceCandidateCacheEntries = 16;
        if (pCache->entries.size() < MaxTraceCandidateCacheEntries)
        {
            pCache->entries.emplace_back();
            pEntry = &pCache->entries.back();
        }
        else
        {
            pEntry = &pCache->entries[pCache->nextEntry];
            pCache->nextEntry = (pCache->nextEntry + 1) % MaxTraceCandidateCacheEntries;
        }
        pEntry->minCell = minCell;
        pEntry->maxCell = maxCell;
        pEntry->facets.clear();
    }

    if (scratch.marks.size() != m_geometry.size())
    {
        scratch.marks.assign(m_geometry.size(), 0u);
        scratch.markId = 0;
    }

    ++scratch.markId;

    if (scratch.markId == 0)
    {
        std::fill(scratch.marks.begin(), scratch.marks.end(), 0u);
        ++scratch.markId;
    }

    const auto consider = [&](size_t facetIndex)
    {
        if (facetIndex >= m_geometry.size())
        {
            return;
        }

        if (scratch.marks[facetIndex] != scratch.markId
            && (pEntry != nullptr || boundsOverlap(bounds, m_geometry[facetIndex].bounds)))
        {
            scratch.marks[facetIndex] = scratch.markId;
            if (pEntry != nullptr)
            {
                pEntry->facets.push_back(facetIndex);
            }
            if (boundsOverlap(bounds, m_geometry[facetIndex].bounds))
            {
                candidates.push_back(facetIndex);
            }
        }
    };

    for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
    {
        for (int32_t cellY = minCellY; cellY <= maxCellY; ++cellY)
        {
            for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
            {
                const auto cellIt = m_spatialGrid.find({cellX, cellY, cellZ});

                if (cellIt == m_spatialGrid.end())
                {
                    continue;
                }

                for (size_t facetIndex : std::span<const size_t>(
                         m_spatialGridFacets.data() + cellIt->second.offset, cellIt->second.count))
                {
                    consider(facetIndex);
                }
            }
        }
    }

    // Facets spanning more cells than MaxSpatialCellsPerFacet are in no cell: every query tests them by bounds.
    for (size_t facetIndex : m_largeSpatialFacets)
    {
        consider(facetIndex);
    }
}

std::span<const size_t> PathMap::candidateFloorFacetsForPoint(float x, float y) const
{
    if (!std::isfinite(x) || !std::isfinite(y))
    {
        return {};
    }

    if (m_gridCellSize <= PathEpsilon || m_floorGrid.empty())
    {
        return m_floorFacetIndices;
    }

    const auto cellIt = m_floorGrid.find({gridCoordinate(x), gridCoordinate(y)});

    if (cellIt == m_floorGrid.end())
    {
        return {};
    }

    return std::span<const size_t>(m_floorGridFacets.data() + cellIt->second.offset, cellIt->second.count);
}

void PathMap::rebuildGeometry()
{
    m_geometry.clear();
    m_floorFacetIndices.clear();
    m_geometry.reserve(m_facets.size());
    m_floorFacetIndices.reserve(m_facets.size());

    for (size_t index = 0; index < m_facets.size(); ++index)
    {
        const PathFacet &facet = m_facets[index];
        FacetGeometry geometry = {};
        geometry.bounds = facetBounds(facet);
        geometry.normal = computeFacetNormal(facet);
        geometry.valid = facet.vertices.size() >= 3 && pointLengthSquared(geometry.normal) > PathEpsilon;
        geometry.nonBlocking = facetIsNonBlocking(facet);

        if (facet.walkableFloor && geometry.valid)
        {
            m_floorFacetIndices.push_back(index);
        }

        m_geometry.push_back(geometry);
    }
    rebuildSpatialGrid();
}

void PathMap::rebuildSpatialGrid()
{
    m_spatialGrid.clear();
    m_floorGrid.clear();
    m_spatialGridFacets.clear();
    m_floorGridFacets.clear();
    m_largeSpatialFacets.clear();

    if (m_gridCellSize <= PathEpsilon || m_geometry.empty())
    {
        return;
    }

    std::vector<std::pair<GridCellKey, size_t>> spatialEntries;
    std::vector<std::pair<FloorCellKey, size_t>> floorEntries;
    spatialEntries.reserve(m_geometry.size() * 4);
    floorEntries.reserve(m_geometry.size());

    for (size_t index = 0; index < m_geometry.size(); ++index)
    {
        const FacetGeometry &geometry = m_geometry[index];

        if (!geometry.valid)
        {
            continue;
        }

        if (!boundsAreFinite(geometry.bounds))
        {
            continue;
        }

        const int32_t minCellX = gridCoordinate(geometry.bounds.minX);
        const int32_t maxCellX = gridCoordinate(geometry.bounds.maxX);
        const int32_t minCellY = gridCoordinate(geometry.bounds.minY);
        const int32_t maxCellY = gridCoordinate(geometry.bounds.maxY);
        const int32_t minCellZ = gridCoordinate(geometry.bounds.minZ);
        const int32_t maxCellZ = gridCoordinate(geometry.bounds.maxZ);

        if (static_cast<int64_t>(maxCellX) - static_cast<int64_t>(minCellX) > MaxPathGridCellSpan
            || static_cast<int64_t>(maxCellY) - static_cast<int64_t>(minCellY) > MaxPathGridCellSpan
            || static_cast<int64_t>(maxCellZ) - static_cast<int64_t>(minCellZ) > MaxPathGridCellSpan)
        {
            continue;
        }

        const int64_t spatialCells = (int64_t(maxCellX) - minCellX + 1) * (int64_t(maxCellY) - minCellY + 1)
            * (int64_t(maxCellZ) - minCellZ + 1);

        if (spatialCells > MaxSpatialCellsPerFacet)
        {
            // A huge facet (an open-air map's sky lid, its sea floor) listed in each of its cells cost a region-sized
            // map ~100 ms per rebuild; queries test the few of them by bounds instead.
            m_largeSpatialFacets.push_back(index);
        }
        else
        {
            for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
            {
                for (int32_t cellY = minCellY; cellY <= maxCellY; ++cellY)
                {
                    for (int32_t cellZ = minCellZ; cellZ <= maxCellZ; ++cellZ)
                    {
                        spatialEntries.push_back({{cellX, cellY, cellZ}, index});
                    }
                }
            }
        }

        if (!m_facets[index].walkableFloor)
        {
            continue;
        }

        for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
        {
            for (int32_t cellY = minCellY; cellY <= maxCellY; ++cellY)
            {
                floorEntries.push_back({{cellX, cellY}, index});
            }
        }
    }

    // Grouped by cell, each cell's facets ascending as they were added.
    std::sort(spatialEntries.begin(), spatialEntries.end(),
        [](const std::pair<GridCellKey, size_t> &left, const std::pair<GridCellKey, size_t> &right)
        {
            return std::tie(left.first.x, left.first.y, left.first.z, left.second)
                < std::tie(right.first.x, right.first.y, right.first.z, right.second);
        });
    std::sort(floorEntries.begin(), floorEntries.end(),
        [](const std::pair<FloorCellKey, size_t> &left, const std::pair<FloorCellKey, size_t> &right)
        {
            return std::tie(left.first.x, left.first.y, left.second) < std::tie(right.first.x, right.first.y, right.second);
        });

    m_spatialGridFacets.reserve(spatialEntries.size());
    m_floorGridFacets.reserve(floorEntries.size());

    for (size_t begin = 0; begin < spatialEntries.size();)
    {
        size_t end = begin;
        const GridCellKey &key = spatialEntries[begin].first;
        while (end < spatialEntries.size() && spatialEntries[end].first == key)
        {
            m_spatialGridFacets.push_back(spatialEntries[end].second);
            ++end;
        }
        m_spatialGrid.emplace(key, GridRange{uint32_t(m_spatialGridFacets.size() - (end - begin)), uint32_t(end - begin)});
        begin = end;
    }

    for (size_t begin = 0; begin < floorEntries.size();)
    {
        size_t end = begin;
        const FloorCellKey &key = floorEntries[begin].first;
        while (end < floorEntries.size() && floorEntries[end].first == key)
        {
            m_floorGridFacets.push_back(floorEntries[end].second);
            ++end;
        }
        m_floorGrid.emplace(key, GridRange{uint32_t(m_floorGridFacets.size() - (end - begin)), uint32_t(end - begin)});
        begin = end;
    }
}

int32_t PathMap::gridCoordinate(float value) const
{
    if (m_gridCellSize <= PathEpsilon || !std::isfinite(value))
    {
        return 0;
    }

    const float coordinate = std::floor(value / m_gridCellSize);

    if (!std::isfinite(coordinate))
    {
        return 0;
    }

    if (coordinate <= static_cast<float>(std::numeric_limits<int32_t>::min()))
    {
        return std::numeric_limits<int32_t>::min();
    }

    if (coordinate >= static_cast<float>(std::numeric_limits<int32_t>::max()))
    {
        return std::numeric_limits<int32_t>::max();
    }

    return static_cast<int32_t>(coordinate);
}

bool PathMap::GridCellKey::operator==(const GridCellKey &other) const
{
    return x == other.x && y == other.y && z == other.z;
}

size_t PathMap::GridCellKeyHash::operator()(const GridCellKey &key) const
{
    const uint32_t x = static_cast<uint32_t>(key.x) * 73856093u;
    const uint32_t y = static_cast<uint32_t>(key.y) * 19349663u;
    const uint32_t z = static_cast<uint32_t>(key.z) * 83492791u;
    return static_cast<size_t>(x ^ y ^ z);
}

bool PathMap::FloorCellKey::operator==(const FloorCellKey &other) const
{
    return x == other.x && y == other.y;
}

size_t PathMap::FloorCellKeyHash::operator()(const FloorCellKey &key) const
{
    const uint32_t x = static_cast<uint32_t>(key.x) * 73856093u;
    const uint32_t y = static_cast<uint32_t>(key.y) * 19349663u;
    return static_cast<size_t>(x ^ y);
}
}
