#include "game/indoor/IndoorGeometryUtils.h"

#include "game/FaceEnums.h"
#include "game/events/EvtEnums.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr float GeometryEpsilon = 0.0001f;
constexpr float FloorSlack = 8.0f;

struct ProjectedFacePoint
{
    float x = 0.0f;
    float y = 0.0f;
};

float fixedDoorDirectionComponentToFloat(int value)
{
    return static_cast<float>(value) / 65536.0f;
}

bx::Vec3 vecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

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

    if (length <= GeometryEpsilon)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {value.x / length, value.y / length, value.z / length};
}

bx::Vec3 computeFaceNormal(const std::vector<IndoorVertex> &vertices, const IndoorFace &face)
{
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};

    if (face.vertexIndices.size() < 3)
    {
        return normal;
    }

    for (size_t index = 0; index < face.vertexIndices.size(); ++index)
    {
        const uint16_t currentVertexIndex = face.vertexIndices[index];
        const uint16_t nextVertexIndex = face.vertexIndices[(index + 1) % face.vertexIndices.size()];

        if (currentVertexIndex >= vertices.size() || nextVertexIndex >= vertices.size())
        {
            return {0.0f, 0.0f, 0.0f};
        }

        const IndoorVertex &currentVertex = vertices[currentVertexIndex];
        const IndoorVertex &nextVertex = vertices[nextVertexIndex];

        normal.x += (static_cast<float>(currentVertex.y) - static_cast<float>(nextVertex.y))
            * (static_cast<float>(currentVertex.z) + static_cast<float>(nextVertex.z));
        normal.y += (static_cast<float>(currentVertex.z) - static_cast<float>(nextVertex.z))
            * (static_cast<float>(currentVertex.x) + static_cast<float>(nextVertex.x));
        normal.z += (static_cast<float>(currentVertex.x) - static_cast<float>(nextVertex.x))
            * (static_cast<float>(currentVertex.y) + static_cast<float>(nextVertex.y));
    }

    return normal;
}

IndoorProjectionAxis chooseProjectionAxis(const bx::Vec3 &normal)
{
    const float absoluteX = std::fabs(normal.x);
    const float absoluteY = std::fabs(normal.y);
    const float absoluteZ = std::fabs(normal.z);

    if (absoluteX >= absoluteY && absoluteX >= absoluteZ)
    {
        return IndoorProjectionAxis::DropX;
    }

    if (absoluteY >= absoluteX && absoluteY >= absoluteZ)
    {
        return IndoorProjectionAxis::DropY;
    }

    return IndoorProjectionAxis::DropZ;
}

ProjectedFacePoint projectFacePoint(IndoorProjectionAxis projectionAxis, const bx::Vec3 &vertex)
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

float orient2d(const ProjectedFacePoint &a, const ProjectedFacePoint &b, const ProjectedFacePoint &c)
{
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
}

bool faceIsWalkable(const IndoorFace &face, const bx::Vec3 &normal)
{
    if (face.vertexIndices.size() < 3)
    {
        return false;
    }

    if (face.facetType == 3 || face.facetType == 4)
    {
        return normal.z > 0.0f;
    }

    if (face.facetType == 5 || face.facetType == 6)
    {
        return normal.z > 0.0f;
    }

    return normal.z > 0.70767211914f;
}

bool sectorBoundingBoxIntersectsProbe(const IndoorSector &sector, const bx::Vec3 &point)
{
    constexpr float ProbeHalfWidth = 5.0f;
    constexpr float ProbeHalfHeight = 64.0f;

    return point.x + ProbeHalfWidth >= sector.minX
        && point.x - ProbeHalfWidth <= sector.maxX
        && point.y + ProbeHalfWidth >= sector.minY
        && point.y - ProbeHalfWidth <= sector.maxY
        && point.z + ProbeHalfHeight >= sector.minZ
        && point.z - ProbeHalfHeight <= sector.maxZ;
}

IndoorFaceKind classifyFaceKind(const IndoorFace &face, const bx::Vec3 &normal)
{
    if (face.facetType == 1)
    {
        return IndoorFaceKind::Wall;
    }

    if (face.facetType == 3 || face.facetType == 4)
    {
        return normal.z >= 0.0f ? IndoorFaceKind::Floor : IndoorFaceKind::Ceiling;
    }

    if (face.facetType == 5 || face.facetType == 6)
    {
        return normal.z >= 0.0f ? IndoorFaceKind::Floor : IndoorFaceKind::Ceiling;
    }

    if (normal.z > 0.70767211914f)
    {
        return IndoorFaceKind::Floor;
    }

    if (normal.z < -0.70767211914f)
    {
        return IndoorFaceKind::Ceiling;
    }

    return IndoorFaceKind::Wall;
}

float faceCandidatePriority(
    int16_t sectorId,
    std::optional<int16_t> preferredSectorId
)
{
    if (!preferredSectorId)
    {
        return 0.0f;
    }

    return sectorId == *preferredSectorId ? 1000000.0f : 0.0f;
}

void appendConnectedIndoorSectors(
    const IndoorMapData &indoorMapData,
    int16_t sectorId,
    std::vector<int16_t> &sectorIds,
    std::vector<uint8_t> &visitedSectorMask
)
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= indoorMapData.sectors.size())
    {
        return;
    }

    if (static_cast<size_t>(sectorId) >= visitedSectorMask.size() || visitedSectorMask[sectorId] != 0)
    {
        return;
    }

    visitedSectorMask[sectorId] = 1;
    sectorIds.push_back(sectorId);

    const IndoorSector &sector = indoorMapData.sectors[sectorId];

    auto appendConnectedSector = [&](uint16_t connectedSectorId)
    {
        if (connectedSectorId >= indoorMapData.sectors.size())
        {
            return;
        }

        if (visitedSectorMask[connectedSectorId] != 0)
        {
            return;
        }

        visitedSectorMask[connectedSectorId] = 1;
        sectorIds.push_back(static_cast<int16_t>(connectedSectorId));
    };

    for (uint16_t faceId : sector.portalFaceIds)
    {
        if (faceId >= indoorMapData.faces.size())
        {
            continue;
        }

        const IndoorFace &face = indoorMapData.faces[faceId];

        if (face.roomNumber == sectorId)
        {
            appendConnectedSector(face.roomBehindNumber);
        }
        else if (face.roomBehindNumber == sectorId)
        {
            appendConnectedSector(face.roomNumber);
        }
    }

    for (uint16_t faceId : sector.faceIds)
    {
        if (faceId >= indoorMapData.faces.size())
        {
            continue;
        }

        const IndoorFace &face = indoorMapData.faces[faceId];

        if (face.roomNumber == sectorId)
        {
            appendConnectedSector(face.roomBehindNumber);
        }
        else if (face.roomBehindNumber == sectorId)
        {
            appendConnectedSector(face.roomNumber);
        }
    }
}

bool isPointInsideProjectedPolygon(
    const ProjectedFacePoint &projectedPoint,
    const std::vector<IndoorProjectedFacePoint> &projectedVertices
)
{
    if (projectedVertices.size() < 3)
    {
        return false;
    }

    auto pointOnSegment = [&](const IndoorProjectedFacePoint &start, const IndoorProjectedFacePoint &end) -> bool
    {
        const float cross =
            (projectedPoint.x - start.x) * (end.y - start.y)
            - (projectedPoint.y - start.y) * (end.x - start.x);

        if (std::fabs(cross) > GeometryEpsilon)
        {
            return false;
        }

        const float minX = std::min(start.x, end.x) - GeometryEpsilon;
        const float maxX = std::max(start.x, end.x) + GeometryEpsilon;
        const float minY = std::min(start.y, end.y) - GeometryEpsilon;
        const float maxY = std::max(start.y, end.y) + GeometryEpsilon;
        return projectedPoint.x >= minX
            && projectedPoint.x <= maxX
            && projectedPoint.y >= minY
            && projectedPoint.y <= maxY;
    };

    bool inside = false;

    for (size_t index = 0; index < projectedVertices.size(); ++index)
    {
        const IndoorProjectedFacePoint &current = projectedVertices[index];
        const IndoorProjectedFacePoint &next = projectedVertices[(index + 1) % projectedVertices.size()];

        if (pointOnSegment(current, next))
        {
            return true;
        }

        const bool intersectsYAxis =
            (current.y > projectedPoint.y) != (next.y > projectedPoint.y);

        if (!intersectsYAxis)
        {
            continue;
        }

        const float edgeHeight = next.y - current.y;

        if (std::fabs(edgeHeight) <= GeometryEpsilon)
        {
            continue;
        }

        const float intersectionX =
            current.x + (projectedPoint.y - current.y) * (next.x - current.x) / edgeHeight;

        if (intersectionX >= projectedPoint.x - GeometryEpsilon)
        {
            inside = !inside;
        }
    }

    return inside;
}

bool isPointInsideFaceXYPolygon(const bx::Vec3 &point, const std::vector<bx::Vec3> &vertices)
{
    if (vertices.size() < 3)
    {
        return false;
    }

    auto pointOnSegment = [&](const bx::Vec3 &start, const bx::Vec3 &end) -> bool
    {
        const float cross =
            (point.x - start.x) * (end.y - start.y)
            - (point.y - start.y) * (end.x - start.x);

        if (std::fabs(cross) > GeometryEpsilon)
        {
            return false;
        }

        const float minX = std::min(start.x, end.x) - GeometryEpsilon;
        const float maxX = std::max(start.x, end.x) + GeometryEpsilon;
        const float minY = std::min(start.y, end.y) - GeometryEpsilon;
        const float maxY = std::max(start.y, end.y) + GeometryEpsilon;
        return point.x >= minX && point.x <= maxX && point.y >= minY && point.y <= maxY;
    };

    bool inside = false;

    for (size_t index = 0; index < vertices.size(); ++index)
    {
        const bx::Vec3 &current = vertices[index];
        const bx::Vec3 &next = vertices[(index + 1) % vertices.size()];

        if (pointOnSegment(current, next))
        {
            return true;
        }

        const bool intersectsYAxis = (current.y > point.y) != (next.y > point.y);

        if (!intersectsYAxis)
        {
            continue;
        }

        const float edgeHeight = next.y - current.y;

        if (std::fabs(edgeHeight) <= GeometryEpsilon)
        {
            continue;
        }

        const float intersectionX = current.x + (point.y - current.y) * (next.x - current.x) / edgeHeight;

        if (intersectionX >= point.x - GeometryEpsilon)
        {
            inside = !inside;
        }
    }

    return inside;
}

const IndoorFaceGeometryData *getIndoorFaceGeometry(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    size_t faceIndex,
    IndoorFaceGeometryCache *pGeometryCache,
    IndoorFaceGeometryData &geometryStorage
)
{
    if (pGeometryCache != nullptr)
    {
        return pGeometryCache->geometryForFace(indoorMapData, vertices, faceIndex);
    }

    if (!buildIndoorFaceGeometry(indoorMapData, vertices, faceIndex, geometryStorage))
    {
        return nullptr;
    }

    return &geometryStorage;
}

IndoorFloorSample evaluateIndoorFloorFace(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    size_t faceIndex,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    const std::vector<uint8_t> *pFaceExclusionMask,
    IndoorFaceGeometryCache *pGeometryCache
)
{
    if (pFaceExclusionMask != nullptr
        && faceIndex < pFaceExclusionMask->size()
        && (*pFaceExclusionMask)[faceIndex] != 0)
    {
        return {};
    }

    IndoorFaceGeometryData geometryStorage = {};
    const IndoorFaceGeometryData *pGeometry = getIndoorFaceGeometry(
        indoorMapData,
        vertices,
        faceIndex,
        pGeometryCache,
        geometryStorage);

    if (pGeometry == nullptr
        || !pGeometry->isWalkable
        || pGeometry->kind != IndoorFaceKind::Floor
        || x < pGeometry->minX - FloorSlack
        || x > pGeometry->maxX + FloorSlack
        || y < pGeometry->minY - FloorSlack
        || y > pGeometry->maxY + FloorSlack)
    {
        return {};
    }

    const bx::Vec3 point = {x, y, pGeometry->vertices.front().z};

    if (!isPointInsideFaceXYPolygon(point, pGeometry->vertices))
    {
        return {};
    }

    const float height = calculateIndoorFaceHeight(*pGeometry, x, y);
    const float delta = height - z;

    if (delta > maxRise || delta < -maxDrop)
    {
        return {};
    }

    IndoorFloorSample sample = {};
    sample.hasFloor = true;
    sample.height = height;
    sample.normalZ = pGeometry->normal.z;
    sample.sectorId = static_cast<int16_t>(pGeometry->sectorId);
    sample.faceIndex = faceIndex;
    return sample;
}
}

IndoorFaceGeometryCache::IndoorFaceGeometryCache(size_t faceCount)
{
    reset(faceCount);
}

void IndoorFaceGeometryCache::reset(size_t faceCount)
{
    m_entryStates.assign(faceCount, 0);
    m_entries.resize(faceCount);
}

const IndoorFaceGeometryData *IndoorFaceGeometryCache::geometryForFace(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    size_t faceIndex
)
{
    if (faceIndex >= m_entryStates.size())
    {
        return nullptr;
    }

    if (m_entryStates[faceIndex] == 0)
    {
        const bool valid = buildIndoorFaceGeometry(indoorMapData, vertices, faceIndex, m_entries[faceIndex]);
        m_entryStates[faceIndex] = valid ? 2 : 1;
    }

    return m_entryStates[faceIndex] == 2 ? &m_entries[faceIndex] : nullptr;
}

std::vector<IndoorVertex> buildIndoorMechanismAdjustedVertices(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pIndoorMapDeltaData,
    const EventRuntimeState *pEventRuntimeState
)
{
    std::vector<IndoorVertex> vertices = indoorMapData.vertices;

    if (pIndoorMapDeltaData == nullptr)
    {
        return vertices;
    }

    for (const MapDeltaDoor &baseDoor : pIndoorMapDeltaData->doors)
    {
        MapDeltaDoor door = baseDoor;
        RuntimeMechanismState runtimeMechanism = {};
        runtimeMechanism.state = door.state;
        runtimeMechanism.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
        runtimeMechanism.currentDistance = EventRuntime::calculateMechanismDistance(door, runtimeMechanism);
        runtimeMechanism.isMoving =
            door.state == static_cast<uint16_t>(EvtMechanismState::Opening)
            || door.state == static_cast<uint16_t>(EvtMechanismState::Closing);
        float distance = runtimeMechanism.currentDistance;

        if (pEventRuntimeState != nullptr)
        {
            const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
                pEventRuntimeState->mechanisms.find(door.doorId);

            if (mechanismIterator != pEventRuntimeState->mechanisms.end())
            {
                door.state = mechanismIterator->second.state;
                distance = mechanismIterator->second.isMoving
                    ? EventRuntime::calculateMechanismDistance(door, mechanismIterator->second)
                    : mechanismIterator->second.currentDistance;
            }
        }

        const size_t movableVertexCount = std::min(
            door.vertexIds.size(),
            std::min(door.xOffsets.size(), std::min(door.yOffsets.size(), door.zOffsets.size()))
        );

        if (movableVertexCount == 0)
        {
            continue;
        }

        const float directionX = fixedDoorDirectionComponentToFloat(door.directionX);
        const float directionY = fixedDoorDirectionComponentToFloat(door.directionY);
        const float directionZ = fixedDoorDirectionComponentToFloat(door.directionZ);

        for (size_t vertexOffsetIndex = 0; vertexOffsetIndex < movableVertexCount; ++vertexOffsetIndex)
        {
            const uint16_t vertexId = door.vertexIds[vertexOffsetIndex];

            if (vertexId >= vertices.size())
            {
                continue;
            }

            IndoorVertex &vertex = vertices[vertexId];
            vertex.x = static_cast<int>(std::lround(
                static_cast<float>(door.xOffsets[vertexOffsetIndex]) + directionX * distance));
            vertex.y = static_cast<int>(std::lround(
                static_cast<float>(door.yOffsets[vertexOffsetIndex]) + directionY * distance));
            vertex.z = static_cast<int>(std::lround(
                static_cast<float>(door.zOffsets[vertexOffsetIndex]) + directionZ * distance));
        }
    }

    return vertices;
}

bx::Vec3 indoorVertexToWorld(const IndoorVertex &vertex)
{
    return {
        static_cast<float>(vertex.x),
        static_cast<float>(vertex.y),
        static_cast<float>(vertex.z)
    };
}

bool buildIndoorFaceGeometry(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    size_t faceIndex,
    IndoorFaceGeometryData &geometry
)
{
    if (faceIndex >= indoorMapData.faces.size())
    {
        return false;
    }

    const IndoorFace &face = indoorMapData.faces[faceIndex];

    if (hasFaceAttribute(face.attributes, FaceAttribute::Invisible) || face.vertexIndices.size() < 3)
    {
        return false;
    }

    geometry = {};
    geometry.faceIndex = faceIndex;
    geometry.attributes = face.attributes;
    geometry.sectorId = face.roomNumber;
    geometry.backSectorId = face.roomBehindNumber;
    geometry.facetType = face.facetType;
    geometry.isPortal = face.isPortal || hasFaceAttribute(face.attributes, FaceAttribute::IsPortal);

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            geometry.vertices.clear();
            return false;
        }

        geometry.vertices.push_back(indoorVertexToWorld(vertices[vertexIndex]));
    }

    geometry.minX = geometry.maxX = geometry.vertices[0].x;
    geometry.minY = geometry.maxY = geometry.vertices[0].y;
    geometry.minZ = geometry.maxZ = geometry.vertices[0].z;

    for (const bx::Vec3 &vertex : geometry.vertices)
    {
        geometry.minX = std::min(geometry.minX, vertex.x);
        geometry.maxX = std::max(geometry.maxX, vertex.x);
        geometry.minY = std::min(geometry.minY, vertex.y);
        geometry.maxY = std::max(geometry.maxY, vertex.y);
        geometry.minZ = std::min(geometry.minZ, vertex.z);
        geometry.maxZ = std::max(geometry.maxZ, vertex.z);
    }

    geometry.normal = vecNormalize(computeFaceNormal(vertices, face));
    geometry.projectionAxis = chooseProjectionAxis(geometry.normal);
    geometry.hasPlane = vecLength(geometry.normal) > GeometryEpsilon;
    geometry.kind = classifyFaceKind(face, geometry.normal);
    geometry.isWalkable =
        !hasFaceAttribute(face.attributes, FaceAttribute::Untouchable) && faceIsWalkable(face, geometry.normal);

    for (const bx::Vec3 &vertex : geometry.vertices)
    {
        const ProjectedFacePoint projected = projectFacePoint(geometry.projectionAxis, vertex);
        geometry.projectedVertices.push_back({projected.x, projected.y});
    }

    return true;
}

bool isPointInsideIndoorPolygonProjected(
    const bx::Vec3 &point,
    const std::vector<bx::Vec3> &vertices,
    const bx::Vec3 &normal
)
{
    if (vertices.size() < 3)
    {
        return false;
    }

    std::vector<ProjectedFacePoint> projectedVertices;
    projectedVertices.reserve(vertices.size());
    const IndoorProjectionAxis projectionAxis = chooseProjectionAxis(normal);

    for (const bx::Vec3 &vertex : vertices)
    {
        projectedVertices.push_back(projectFacePoint(projectionAxis, vertex));
    }

    const ProjectedFacePoint projectedPoint = projectFacePoint(projectionAxis, point);
    float sign = 0.0f;

    for (size_t index = 0; index < projectedVertices.size(); ++index)
    {
        const ProjectedFacePoint &current = projectedVertices[index];
        const ProjectedFacePoint &next = projectedVertices[(index + 1) % projectedVertices.size()];
        const float orientation = orient2d(current, next, projectedPoint);

        if (std::fabs(orientation) <= GeometryEpsilon)
        {
            continue;
        }

        if (sign == 0.0f)
        {
            sign = orientation;
            continue;
        }

        if ((sign > 0.0f && orientation < -GeometryEpsilon)
            || (sign < 0.0f && orientation > GeometryEpsilon))
        {
            return false;
        }
    }

    return true;
}

float calculateIndoorFaceHeight(const IndoorFaceGeometryData &geometry, float x, float y)
{
    if (!geometry.hasPlane || std::fabs(geometry.normal.z) <= GeometryEpsilon || geometry.vertices.empty())
    {
        return geometry.vertices.empty() ? 0.0f : geometry.vertices.front().z;
    }

    return geometry.vertices.front().z
        - (geometry.normal.x * (x - geometry.vertices.front().x)
           + geometry.normal.y * (y - geometry.vertices.front().y))
            / geometry.normal.z;
}

bool isIndoorCylinderBlockedByFace(
    const IndoorFaceGeometryData &geometry,
    float x,
    float y,
    float z,
    float radius,
    float height
)
{
    if (!geometry.hasPlane || geometry.vertices.empty())
    {
        return false;
    }

    if ((x + radius) < geometry.minX
        || (x - radius) > geometry.maxX
        || (y + radius) < geometry.minY
        || (y - radius) > geometry.maxY
        || (z + height) < geometry.minZ
        || z > geometry.maxZ)
    {
        return false;
    }

    const bx::Vec3 center = {
        x,
        y,
        z + std::min(height * 0.5f, std::max(radius, 1.0f))
    };
    const bx::Vec3 pointDelta = vecSubtract(center, geometry.vertices.front());
    const float signedDistance = vecDot(pointDelta, geometry.normal);

    if (std::abs(signedDistance) > radius)
    {
        return false;
    }

    const bx::Vec3 projectedPoint = {
        center.x - geometry.normal.x * signedDistance,
        center.y - geometry.normal.y * signedDistance,
        center.z - geometry.normal.z * signedDistance
    };
    const ProjectedFacePoint projectedFacePoint = projectFacePoint(geometry.projectionAxis, projectedPoint);
    return isPointInsideProjectedPolygon(projectedFacePoint, geometry.projectedVertices);
}

IndoorFloorSample sampleIndoorFloor(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    std::optional<int16_t> preferredSectorId,
    const std::vector<uint8_t> *pFaceExclusionMask,
    IndoorFaceGeometryCache *pGeometryCache
)
{
    IndoorFloorSample bestSample = {};
    float bestScore = -std::numeric_limits<float>::infinity();
    std::vector<uint8_t> visitedSectorMask;
    std::vector<int16_t> candidateSectorIds;

    auto evaluateFloorFaces = [&](const std::vector<uint16_t> &faceIds)
    {
        for (uint16_t faceId : faceIds)
        {
            const IndoorFloorSample candidate = evaluateIndoorFloorFace(
                indoorMapData,
                vertices,
                faceId,
                x,
                y,
                z,
                maxRise,
                maxDrop,
                pFaceExclusionMask,
                pGeometryCache);

            if (!candidate.hasFloor)
            {
                continue;
            }

            const float score = faceCandidatePriority(candidate.sectorId, preferredSectorId)
                - std::fabs(candidate.height - z);

            if (!bestSample.hasFloor || score > bestScore)
            {
                bestSample = candidate;
                bestScore = score;
            }
        }
    };

    auto evaluateSectorFloorFaces = [&](int16_t sectorId)
    {
        if (sectorId < 0 || static_cast<size_t>(sectorId) >= indoorMapData.sectors.size())
        {
            return;
        }

        evaluateFloorFaces(indoorMapData.sectors[sectorId].floorFaceIds);
    };

    if (preferredSectorId
        && *preferredSectorId >= 0
        && static_cast<size_t>(*preferredSectorId) < indoorMapData.sectors.size())
    {
        visitedSectorMask.assign(indoorMapData.sectors.size(), 0);
        appendConnectedIndoorSectors(indoorMapData, *preferredSectorId, candidateSectorIds, visitedSectorMask);

        for (int16_t sectorId : candidateSectorIds)
        {
            evaluateSectorFloorFaces(sectorId);
        }
    }

    if (bestSample.hasFloor)
    {
        return bestSample;
    }

    for (size_t sectorIndex = 0; sectorIndex < indoorMapData.sectors.size(); ++sectorIndex)
    {
        if (!visitedSectorMask.empty() && visitedSectorMask[sectorIndex] != 0)
        {
            continue;
        }

        evaluateSectorFloorFaces(static_cast<int16_t>(sectorIndex));
    }

    return bestSample;
}

IndoorFloorSample sampleIndoorFloorOnFace(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    size_t faceIndex,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    const std::vector<uint8_t> *pFaceExclusionMask,
    IndoorFaceGeometryCache *pGeometryCache
)
{
    return evaluateIndoorFloorFace(
        indoorMapData,
        vertices,
        faceIndex,
        x,
        y,
        z,
        maxRise,
        maxDrop,
        pFaceExclusionMask,
        pGeometryCache);
}

IndoorCeilingSample sampleIndoorCeiling(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    float x,
    float y,
    float z,
    std::optional<int16_t> preferredSectorId,
    const std::vector<uint8_t> *pFaceExclusionMask,
    IndoorFaceGeometryCache *pGeometryCache
)
{
    IndoorCeilingSample bestSample = {};
    float bestHeight = std::numeric_limits<float>::max();
    std::vector<uint8_t> visitedSectorMask;
    std::vector<int16_t> candidateSectorIds;

    auto evaluateCeilingFaces = [&](const std::vector<uint16_t> &faceIds)
    {
        for (uint16_t faceId : faceIds)
        {
            if (pFaceExclusionMask != nullptr
                && faceId < pFaceExclusionMask->size()
                && (*pFaceExclusionMask)[faceId] != 0)
            {
                continue;
            }

            IndoorFaceGeometryData geometryStorage = {};
            const IndoorFaceGeometryData *pGeometry = getIndoorFaceGeometry(
                indoorMapData,
                vertices,
                faceId,
                pGeometryCache,
                geometryStorage);

            if (pGeometry == nullptr
                || pGeometry->kind != IndoorFaceKind::Ceiling
                || x < pGeometry->minX - FloorSlack
                || x > pGeometry->maxX + FloorSlack
                || y < pGeometry->minY - FloorSlack
                || y > pGeometry->maxY + FloorSlack)
            {
                continue;
            }

            const bx::Vec3 point = {x, y, pGeometry->vertices.front().z};

            if (!isPointInsideFaceXYPolygon(point, pGeometry->vertices))
            {
                continue;
            }

            const float height = calculateIndoorFaceHeight(*pGeometry, x, y);

            if (height + FloorSlack < z)
            {
                continue;
            }

            if (!bestSample.hasCeiling
                || height < bestHeight
                || (std::fabs(height - bestHeight) <= GeometryEpsilon
                    && pGeometry->sectorId == static_cast<uint16_t>(preferredSectorId.value_or(-1))))
            {
                bestSample.hasCeiling = true;
                bestSample.height = height;
                bestSample.sectorId = static_cast<int16_t>(pGeometry->sectorId);
                bestSample.faceIndex = faceId;
                bestHeight = height;
            }
        }
    };

    auto evaluateSectorCeilingFaces = [&](int16_t sectorId)
    {
        if (sectorId < 0 || static_cast<size_t>(sectorId) >= indoorMapData.sectors.size())
        {
            return;
        }

        evaluateCeilingFaces(indoorMapData.sectors[sectorId].ceilingFaceIds);
    };

    if (preferredSectorId
        && *preferredSectorId >= 0
        && static_cast<size_t>(*preferredSectorId) < indoorMapData.sectors.size())
    {
        visitedSectorMask.assign(indoorMapData.sectors.size(), 0);
        appendConnectedIndoorSectors(indoorMapData, *preferredSectorId, candidateSectorIds, visitedSectorMask);

        for (int16_t sectorId : candidateSectorIds)
        {
            evaluateSectorCeilingFaces(sectorId);
        }
    }

    if (bestSample.hasCeiling)
    {
        return bestSample;
    }

    for (size_t sectorIndex = 0; sectorIndex < indoorMapData.sectors.size(); ++sectorIndex)
    {
        if (!visitedSectorMask.empty() && visitedSectorMask[sectorIndex] != 0)
        {
            continue;
        }

        evaluateSectorCeilingFaces(static_cast<int16_t>(sectorIndex));
    }

    return bestSample;
}

std::optional<int16_t> findIndoorSectorForPoint(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const bx::Vec3 &point,
    IndoorFaceGeometryCache *pGeometryCache
)
{
    if (indoorMapData.sectors.empty())
    {
        return std::nullopt;
    }

    struct SectorFaceCandidate
    {
        int16_t sectorId = -1;
        float height = 0.0f;
    };

    std::vector<SectorFaceCandidate> candidates;
    candidates.reserve(5);
    std::optional<int16_t> backupBoundingSectorId;
    std::optional<int16_t> singleSectorId;
    bool singleSector = true;
    const size_t startingSectorIndex = indoorMapData.sectors.size() > 1 ? 1 : 0;

    auto appendSectorCandidate = [&](int16_t sectorId, float height)
    {
        if (candidates.size() >= 5)
        {
            return;
        }

        candidates.push_back({sectorId, height});
    };

    for (size_t sectorIndex = startingSectorIndex; sectorIndex < indoorMapData.sectors.size(); ++sectorIndex)
    {
        const IndoorSector &sector = indoorMapData.sectors[sectorIndex];

        if (!sectorBoundingBoxIntersectsProbe(sector, point))
        {
            continue;
        }

        if (!backupBoundingSectorId)
        {
            backupBoundingSectorId = static_cast<int16_t>(sectorIndex);
        }

        if (sector.floorFaceIds.empty() && sector.portalFaceIds.empty())
        {
            continue;
        }

        if (!singleSectorId)
        {
            singleSectorId = static_cast<int16_t>(sectorIndex);
        }
        else if (*singleSectorId != static_cast<int16_t>(sectorIndex))
        {
            singleSector = false;
        }

        const auto evaluateSectorFaces = [&](const std::vector<uint16_t> &faceIds)
        {
            for (uint16_t faceId : faceIds)
            {
                IndoorFaceGeometryData geometryStorage = {};
                const IndoorFaceGeometryData *pGeometry = getIndoorFaceGeometry(
                    indoorMapData,
                    vertices,
                    faceId,
                    pGeometryCache,
                    geometryStorage);

                if (pGeometry == nullptr
                    || pGeometry->kind != IndoorFaceKind::Floor
                    || point.x < pGeometry->minX - FloorSlack
                    || point.x > pGeometry->maxX + FloorSlack
                    || point.y < pGeometry->minY - FloorSlack
                    || point.y > pGeometry->maxY + FloorSlack)
                {
                    continue;
                }

                if (!isPointInsideFaceXYPolygon(point, pGeometry->vertices))
                {
                    continue;
                }

                appendSectorCandidate(static_cast<int16_t>(sectorIndex), calculateIndoorFaceHeight(*pGeometry, point.x, point.y));

                if (candidates.size() >= 5)
                {
                    return;
                }
            }
        };

        evaluateSectorFaces(sector.floorFaceIds);

        if ((sector.flags & 0x8) != 0 && candidates.size() < 5)
        {
            evaluateSectorFaces(sector.portalFaceIds);
        }

        if (candidates.size() >= 5)
        {
            break;
        }
    }

    if (candidates.size() == 1)
    {
        return candidates.front().sectorId;
    }

    if (singleSectorId && singleSector)
    {
        return *singleSectorId;
    }

    if (candidates.empty())
    {
        return backupBoundingSectorId;
    }

    std::optional<int16_t> bestBelowSectorId;
    std::optional<int16_t> bestAboveSectorId;
    float bestBelowDistance = std::numeric_limits<float>::max();
    float bestAboveDistance = std::numeric_limits<float>::max();

    for (const SectorFaceCandidate &candidate : candidates)
    {
        const float zDistance = point.z - candidate.height;

        if (zDistance >= 0.0f)
        {
            if (zDistance < bestBelowDistance)
            {
                bestBelowDistance = zDistance;
                bestBelowSectorId = candidate.sectorId;
            }
        }
        else
        {
            const float aboveDistance = std::fabs(zDistance);

            if (aboveDistance < bestAboveDistance)
            {
                bestAboveDistance = aboveDistance;
                bestAboveSectorId = candidate.sectorId;
            }
        }
    }

    if (bestBelowSectorId)
    {
        return bestBelowSectorId;
    }

    return bestAboveSectorId;
}
}
