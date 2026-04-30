#include "game/indoor/IndoorPortalVisibility.h"

#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/maps/MapDeltaData.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr float VisibilityEpsilon = 0.001f;
constexpr float FrustumClipEpsilon = 5.0f;
constexpr float NearPortalSlack = 128.0f;
constexpr float DoorPortalRevealSlack = 64.0f;

struct IndoorVisibilityBounds
{
    bx::Vec3 min = {0.0f, 0.0f, 0.0f};
    bx::Vec3 max = {0.0f, 0.0f, 0.0f};
    bool hasPoint = false;
};

float dotVec(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

bx::Vec3 addVec(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

bx::Vec3 subtractVec(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

bx::Vec3 scaleVec(const bx::Vec3 &value, float scale)
{
    return {value.x * scale, value.y * scale, value.z * scale};
}

bx::Vec3 crossVec(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
}

float lengthVec(const bx::Vec3 &value)
{
    return std::sqrt(dotVec(value, value));
}

bx::Vec3 normalizeVec(const bx::Vec3 &value)
{
    const float length = lengthVec(value);

    if (length <= VisibilityEpsilon)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return scaleVec(value, 1.0f / length);
}

float signedPlaneDistance(const IndoorVisibilityPlane &plane, const bx::Vec3 &point)
{
    return dotVec(plane.normal, point) + plane.distance;
}

IndoorVisibilityPlane makePlaneFromPoints(
    const bx::Vec3 &a,
    const bx::Vec3 &b,
    const bx::Vec3 &c,
    const bx::Vec3 &insidePoint
)
{
    IndoorVisibilityPlane plane = {};
    plane.normal = normalizeVec(crossVec(subtractVec(b, a), subtractVec(c, a)));
    plane.distance = -dotVec(plane.normal, a);

    if (signedPlaneDistance(plane, insidePoint) < 0.0f)
    {
        plane.normal = scaleVec(plane.normal, -1.0f);
        plane.distance = -plane.distance;
    }

    return plane;
}

std::vector<IndoorVisibilityPlane> buildCameraFrustumPlanes(const IndoorPortalVisibilityInput &input)
{
    const bx::Vec3 forward = normalizeVec(input.cameraForward);
    const bx::Vec3 up = normalizeVec(input.cameraUp);
    bx::Vec3 right = normalizeVec(crossVec(forward, up));

    if (lengthVec(right) <= VisibilityEpsilon)
    {
        right = {0.0f, -1.0f, 0.0f};
    }

    const bx::Vec3 correctedUp = normalizeVec(crossVec(right, forward));
    const float halfHeight = std::tan((input.verticalFovDegrees * 3.14159265358979323846f / 180.0f) * 0.5f);
    const float halfWidth = halfHeight * std::max(input.aspectRatio, 0.01f);
    const bx::Vec3 center = addVec(input.cameraPosition, forward);
    const bx::Vec3 rightOffset = scaleVec(right, halfWidth);
    const bx::Vec3 upOffset = scaleVec(correctedUp, halfHeight);
    const bx::Vec3 topLeft = addVec(subtractVec(center, rightOffset), upOffset);
    const bx::Vec3 topRight = addVec(addVec(center, rightOffset), upOffset);
    const bx::Vec3 bottomLeft = subtractVec(subtractVec(center, rightOffset), upOffset);
    const bx::Vec3 bottomRight = subtractVec(addVec(center, rightOffset), upOffset);
    const bx::Vec3 insidePoint = addVec(input.cameraPosition, forward);

    std::vector<IndoorVisibilityPlane> planes;
    planes.reserve(4);
    planes.push_back(makePlaneFromPoints(input.cameraPosition, topLeft, bottomLeft, insidePoint));
    planes.push_back(makePlaneFromPoints(input.cameraPosition, bottomRight, topRight, insidePoint));
    planes.push_back(makePlaneFromPoints(input.cameraPosition, topRight, topLeft, insidePoint));
    planes.push_back(makePlaneFromPoints(input.cameraPosition, bottomLeft, bottomRight, insidePoint));
    return planes;
}

std::vector<bx::Vec3> clipPolygonToPlane(
    const std::vector<bx::Vec3> &polygon,
    const IndoorVisibilityPlane &plane
)
{
    if (polygon.empty())
    {
        return {};
    }

    std::vector<bx::Vec3> clipped;
    clipped.reserve(polygon.size() + 1);

    for (size_t pointIndex = 0; pointIndex < polygon.size(); ++pointIndex)
    {
        const bx::Vec3 &current = polygon[pointIndex];
        const bx::Vec3 &next = polygon[(pointIndex + 1) % polygon.size()];
        const float currentDistance = signedPlaneDistance(plane, current);
        const float nextDistance = signedPlaneDistance(plane, next);
        const bool currentInside = currentDistance >= -FrustumClipEpsilon;
        const bool nextInside = nextDistance >= -FrustumClipEpsilon;

        if (currentInside && nextInside)
        {
            clipped.push_back(next);
        }
        else if (currentInside != nextInside)
        {
            const float denominator = currentDistance - nextDistance;
            const float factor = std::fabs(denominator) > VisibilityEpsilon ? currentDistance / denominator : 0.0f;
            const bx::Vec3 edge = subtractVec(next, current);
            clipped.push_back(addVec(current, scaleVec(edge, factor)));

            if (nextInside)
            {
                clipped.push_back(next);
            }
        }
    }

    return clipped;
}

std::vector<bx::Vec3> clipPolygonToFrustum(
    const std::vector<bx::Vec3> &polygon,
    const std::vector<IndoorVisibilityPlane> &planes
)
{
    std::vector<bx::Vec3> clipped = polygon;

    for (const IndoorVisibilityPlane &plane : planes)
    {
        clipped = clipPolygonToPlane(clipped, plane);

        if (clipped.size() < 3)
        {
            return {};
        }
    }

    return clipped;
}

std::vector<IndoorVisibilityPlane> buildPortalFrustumPlanes(
    const bx::Vec3 &cameraPosition,
    const std::vector<bx::Vec3> &portalPolygon
)
{
    if (portalPolygon.size() < 3)
    {
        return {};
    }

    bx::Vec3 centroid = {0.0f, 0.0f, 0.0f};
    for (const bx::Vec3 &point : portalPolygon)
    {
        centroid = addVec(centroid, point);
    }
    centroid = scaleVec(centroid, 1.0f / static_cast<float>(portalPolygon.size()));

    std::vector<IndoorVisibilityPlane> planes;
    planes.reserve(portalPolygon.size());

    for (size_t pointIndex = 0; pointIndex < portalPolygon.size(); ++pointIndex)
    {
        const bx::Vec3 &current = portalPolygon[pointIndex];
        const bx::Vec3 &next = portalPolygon[(pointIndex + 1) % portalPolygon.size()];
        IndoorVisibilityPlane plane = makePlaneFromPoints(cameraPosition, current, next, centroid);

        if (lengthVec(plane.normal) > VisibilityEpsilon)
        {
            planes.push_back(plane);
        }
    }

    return planes;
}

bool indoorPortalFaceVisible(
    size_t faceIndex,
    const IndoorFace &face,
    const MapDeltaData *pMapDeltaData,
    const std::optional<EventRuntimeState> *pEventRuntimeState)
{
    const uint32_t effectiveAttributes =
        pMapDeltaData != nullptr && faceIndex < pMapDeltaData->faceAttributes.size()
            ? pMapDeltaData->faceAttributes[faceIndex]
            : face.attributes;

    if (hasFaceAttribute(effectiveAttributes, FaceAttribute::Invisible))
    {
        return false;
    }

    return pEventRuntimeState == nullptr
        || !pEventRuntimeState->has_value()
        || !(*pEventRuntimeState)->hasFacetInvisibleOverride(static_cast<uint32_t>(faceIndex));
}

float resolveMechanismDistance(
    const MapDeltaDoor &door,
    const std::optional<EventRuntimeState> *pEventRuntimeState
)
{
    RuntimeMechanismState runtimeMechanism = {};
    runtimeMechanism.state = door.state;
    runtimeMechanism.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
    runtimeMechanism.currentDistance = EventRuntime::calculateMechanismDistance(door, runtimeMechanism);
    runtimeMechanism.isMoving =
        door.state == static_cast<uint16_t>(EvtMechanismState::Opening)
        || door.state == static_cast<uint16_t>(EvtMechanismState::Closing);

    if (pEventRuntimeState == nullptr || !pEventRuntimeState->has_value())
    {
        return runtimeMechanism.currentDistance;
    }

    const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
        (*pEventRuntimeState)->mechanisms.find(door.doorId);

    if (mechanismIterator == (*pEventRuntimeState)->mechanisms.end())
    {
        return runtimeMechanism.currentDistance;
    }

    return mechanismIterator->second.isMoving
        ? EventRuntime::calculateMechanismDistance(door, mechanismIterator->second)
        : mechanismIterator->second.currentDistance;
}

uint16_t resolveMechanismState(
    const MapDeltaDoor &door,
    const std::optional<EventRuntimeState> *pEventRuntimeState
)
{
    if (pEventRuntimeState == nullptr || !pEventRuntimeState->has_value())
    {
        return door.state;
    }

    const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
        (*pEventRuntimeState)->mechanisms.find(door.doorId);

    if (mechanismIterator == (*pEventRuntimeState)->mechanisms.end())
    {
        return door.state;
    }

    return mechanismIterator->second.state;
}

IndoorVisibilityBounds makeEmptyVisibilityBounds()
{
    IndoorVisibilityBounds bounds = {};
    bounds.min = {
        std::numeric_limits<float>::max(),
        std::numeric_limits<float>::max(),
        std::numeric_limits<float>::max()
    };
    bounds.max = {
        std::numeric_limits<float>::lowest(),
        std::numeric_limits<float>::lowest(),
        std::numeric_limits<float>::lowest()
    };
    return bounds;
}

void includeVisibilityBoundsPoint(IndoorVisibilityBounds &bounds, const IndoorVertex &vertex)
{
    bounds.min.x = std::min(bounds.min.x, static_cast<float>(vertex.x));
    bounds.min.y = std::min(bounds.min.y, static_cast<float>(vertex.y));
    bounds.min.z = std::min(bounds.min.z, static_cast<float>(vertex.z));
    bounds.max.x = std::max(bounds.max.x, static_cast<float>(vertex.x));
    bounds.max.y = std::max(bounds.max.y, static_cast<float>(vertex.y));
    bounds.max.z = std::max(bounds.max.z, static_cast<float>(vertex.z));
    bounds.hasPoint = true;
}

IndoorVisibilityBounds buildFaceBounds(const IndoorFace &face, const std::vector<IndoorVertex> &vertices)
{
    IndoorVisibilityBounds bounds = makeEmptyVisibilityBounds();

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex < vertices.size())
        {
            includeVisibilityBoundsPoint(bounds, vertices[vertexIndex]);
        }
    }

    return bounds;
}

IndoorVisibilityBounds buildDoorBounds(const MapDeltaDoor &door, const std::vector<IndoorVertex> &vertices)
{
    IndoorVisibilityBounds bounds = makeEmptyVisibilityBounds();

    for (uint16_t vertexIndex : door.vertexIds)
    {
        if (vertexIndex < vertices.size())
        {
            includeVisibilityBoundsPoint(bounds, vertices[vertexIndex]);
        }
    }

    return bounds;
}

bool visibilityBoundsOverlapWithSlack(
    const IndoorVisibilityBounds &left,
    const IndoorVisibilityBounds &right,
    float slack
)
{
    if (!left.hasPoint || !right.hasPoint)
    {
        return false;
    }

    return left.max.x + slack >= right.min.x
        && left.min.x - slack <= right.max.x
        && left.max.y + slack >= right.min.y
        && left.min.y - slack <= right.max.y
        && left.max.z + slack >= right.min.z
        && left.min.z - slack <= right.max.z;
}

bool portalBlockedByClosedDoor(
    const IndoorFace &portalFace,
    const std::vector<IndoorVertex> &vertices,
    const MapDeltaData *pMapDeltaData,
    const std::optional<EventRuntimeState> *pEventRuntimeState
)
{
    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    const IndoorVisibilityBounds portalBounds = buildFaceBounds(portalFace, vertices);

    if (!portalBounds.hasPoint)
    {
        return false;
    }

    for (const MapDeltaDoor &door : pMapDeltaData->doors)
    {
        const uint16_t mechanismState = resolveMechanismState(door, pEventRuntimeState);

        if (mechanismState == static_cast<uint16_t>(EvtMechanismState::Opening)
            || mechanismState == static_cast<uint16_t>(EvtMechanismState::Closing))
        {
            continue;
        }

        if (resolveMechanismDistance(door, pEventRuntimeState) <= 1.0f)
        {
            continue;
        }

        if (visibilityBoundsOverlapWithSlack(buildDoorBounds(door, vertices), portalBounds, DoorPortalRevealSlack))
        {
            return true;
        }
    }

    return false;
}

bool hasAncestorSector(
    const std::vector<IndoorVisibilityNode> &nodes,
    int16_t nodeIndex,
    int16_t sectorId
)
{
    int16_t currentIndex = nodeIndex;

    while (currentIndex >= 0 && static_cast<size_t>(currentIndex) < nodes.size())
    {
        const IndoorVisibilityNode &node = nodes[static_cast<size_t>(currentIndex)];

        if (node.sectorId == sectorId)
        {
            return true;
        }

        currentIndex = node.parentNodeIndex;
    }

    return false;
}

bool cameraNearPortal(const bx::Vec3 &cameraPosition, const std::vector<bx::Vec3> &portalPolygon)
{
    if (portalPolygon.empty())
    {
        return false;
    }

    bx::Vec3 minBounds = portalPolygon.front();
    bx::Vec3 maxBounds = portalPolygon.front();

    for (const bx::Vec3 &point : portalPolygon)
    {
        minBounds.x = std::min(minBounds.x, point.x);
        minBounds.y = std::min(minBounds.y, point.y);
        minBounds.z = std::min(minBounds.z, point.z);
        maxBounds.x = std::max(maxBounds.x, point.x);
        maxBounds.y = std::max(maxBounds.y, point.y);
        maxBounds.z = std::max(maxBounds.z, point.z);
    }

    return cameraPosition.x >= minBounds.x - NearPortalSlack
        && cameraPosition.x <= maxBounds.x + NearPortalSlack
        && cameraPosition.y >= minBounds.y - NearPortalSlack
        && cameraPosition.y <= maxBounds.y + NearPortalSlack
        && cameraPosition.z >= minBounds.z - NearPortalSlack
        && cameraPosition.z <= maxBounds.z + NearPortalSlack;
}

bool faceFrontSideFacesCamera(const IndoorFaceGeometryData &geometry, const bx::Vec3 &cameraPosition)
{
    if (!geometry.hasPlane || geometry.vertices.empty())
    {
        return false;
    }

    return dotVec(geometry.normal, subtractVec(cameraPosition, geometry.vertices.front())) > 0.0f;
}

void appendUniqueFaceId(std::vector<uint16_t> &faceIds, uint16_t faceId)
{
    if (std::find(faceIds.begin(), faceIds.end(), faceId) == faceIds.end())
    {
        faceIds.push_back(faceId);
    }
}

void appendPortalFacesLinkedToSector(
    std::vector<uint16_t> &faceIds,
    const IndoorMapData &mapData,
    const MapDeltaData *pMapDeltaData,
    int16_t sectorId)
{
    if (sectorId < 0)
    {
        return;
    }

    for (size_t faceIndex = 0; faceIndex < mapData.faces.size(); ++faceIndex)
    {
        if (faceIndex > std::numeric_limits<uint16_t>::max())
        {
            break;
        }

        const IndoorFace &face = mapData.faces[faceIndex];

        if (face.roomNumber != static_cast<uint16_t>(sectorId)
            && face.roomBehindNumber != static_cast<uint16_t>(sectorId))
        {
            continue;
        }

        const uint32_t effectiveAttributes =
            pMapDeltaData != nullptr && faceIndex < pMapDeltaData->faceAttributes.size()
                ? pMapDeltaData->faceAttributes[faceIndex]
                : face.attributes;

        if (!face.isPortal && !hasFaceAttribute(effectiveAttributes, FaceAttribute::IsPortal))
        {
            continue;
        }

        appendUniqueFaceId(faceIds, static_cast<uint16_t>(faceIndex));
    }
}

bool sectorHasFaceInsideFrustum(
    const IndoorMapData &mapData,
    const std::vector<IndoorVertex> &vertices,
    int16_t sectorId,
    const std::vector<IndoorVisibilityPlane> &frustumPlanes,
    IndoorFaceGeometryCache &geometryCache
)
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= mapData.sectors.size())
    {
        return false;
    }

    const IndoorSector &sector = mapData.sectors[static_cast<size_t>(sectorId)];

    for (uint16_t faceId : sector.faceIds)
    {
        if (faceId >= mapData.faces.size())
        {
            continue;
        }

        const IndoorFace &face = mapData.faces[faceId];

        if (face.isPortal || hasFaceAttribute(face.attributes, FaceAttribute::IsPortal))
        {
            continue;
        }

        const IndoorFaceGeometryData *pGeometry =
            geometryCache.geometryForFace(mapData, vertices, static_cast<size_t>(faceId));

        if (pGeometry == nullptr || pGeometry->vertices.size() < 3)
        {
            continue;
        }

        if (clipPolygonToFrustum(pGeometry->vertices, frustumPlanes).size() >= 3)
        {
            return true;
        }
    }

    return false;
}

bool sectorBoundsContainPoint(const IndoorSector &sector, const bx::Vec3 &point, float slack)
{
    return point.x >= static_cast<float>(sector.minX) - slack
        && point.x <= static_cast<float>(sector.maxX) + slack
        && point.y >= static_cast<float>(sector.minY) - slack
        && point.y <= static_cast<float>(sector.maxY) + slack
        && point.z >= static_cast<float>(sector.minZ) - slack
        && point.z <= static_cast<float>(sector.maxZ) + slack;
}

bool sectorHasPortalGraphLinks(const IndoorSector &sector)
{
    return !sector.portalFaceIds.empty();
}

void appendRootVisibilityNode(
    IndoorPortalVisibilityResult &result,
    int16_t sectorId,
    const std::vector<IndoorVisibilityPlane> &rootFrustumPlanes)
{
    if (sectorId < 0
        || static_cast<size_t>(sectorId) >= result.visibleSectorMask.size()
        || result.visibleSectorMask[static_cast<size_t>(sectorId)] != 0)
    {
        return;
    }

    IndoorVisibilityNode rootNode = {};
    rootNode.sectorId = sectorId;
    rootNode.parentNodeIndex = -1;
    rootNode.entryPortalFaceId = -1;
    rootNode.depth = 0;
    rootNode.frustumPlanes = rootFrustumPlanes;
    const uint16_t rootNodeIndex = static_cast<uint16_t>(result.nodes.size());
    result.nodes.push_back(std::move(rootNode));
    result.visibleSectorMask[static_cast<size_t>(sectorId)] = 1;
    result.nodeIndicesBySector[static_cast<size_t>(sectorId)].push_back(rootNodeIndex);
}
}

IndoorPortalVisibilityResult buildIndoorPortalVisibility(const IndoorPortalVisibilityInput &input)
{
    IndoorPortalVisibilityResult result = {};

    if (input.pMapData == nullptr
        || input.pVertices == nullptr
        || input.startSectorId < 0
        || static_cast<size_t>(input.startSectorId) >= input.pMapData->sectors.size())
    {
        return result;
    }

    const IndoorMapData &mapData = *input.pMapData;
    const std::vector<IndoorVertex> &vertices = *input.pVertices;
    const std::vector<IndoorVisibilityPlane> rootFrustumPlanes = buildCameraFrustumPlanes(input);

    result.visibleSectorMask.assign(mapData.sectors.size(), 0);
    result.nodeIndicesBySector.resize(mapData.sectors.size());
    result.nodes.reserve(std::min<size_t>(input.maxNodes, mapData.sectors.size() * 2 + 1));

    appendRootVisibilityNode(result, input.startSectorId, rootFrustumPlanes);

    const IndoorSector &startSector = mapData.sectors[static_cast<size_t>(input.startSectorId)];

    if (!sectorHasPortalGraphLinks(startSector))
    {
        constexpr float RootSectorBoundsSlack = 96.0f;

        for (size_t sectorId = 0; sectorId < mapData.sectors.size() && result.nodes.size() < input.maxNodes; ++sectorId)
        {
            const IndoorSector &sector = mapData.sectors[sectorId];

            if (!sectorHasPortalGraphLinks(sector)
                || !sectorBoundsContainPoint(sector, input.cameraPosition, RootSectorBoundsSlack))
            {
                continue;
            }

            appendRootVisibilityNode(result, static_cast<int16_t>(sectorId), rootFrustumPlanes);
        }
    }

    IndoorFaceGeometryCache geometryCache(mapData.faces.size());

    for (size_t nodeIndex = 0; nodeIndex < result.nodes.size(); ++nodeIndex)
    {
        if (nodeIndex >= input.maxNodes)
        {
            break;
        }

        const IndoorVisibilityNode currentNode = result.nodes[nodeIndex];

        if (currentNode.depth >= input.maxDepth
            || currentNode.sectorId < 0
            || static_cast<size_t>(currentNode.sectorId) >= mapData.sectors.size())
        {
            continue;
        }

        const IndoorSector &sector = mapData.sectors[static_cast<size_t>(currentNode.sectorId)];
        std::vector<uint16_t> portalFaceIds;
        portalFaceIds.reserve(sector.portalFaceIds.size() + sector.faceIds.size());

        for (uint16_t faceId : sector.portalFaceIds)
        {
            appendUniqueFaceId(portalFaceIds, faceId);
        }

        for (uint16_t faceId : sector.faceIds)
        {
            appendUniqueFaceId(portalFaceIds, faceId);
        }

        appendPortalFacesLinkedToSector(portalFaceIds, mapData, input.pMapDeltaData, currentNode.sectorId);

        for (uint16_t faceId : portalFaceIds)
        {
            if (result.nodes.size() >= input.maxNodes || faceId >= mapData.faces.size())
            {
                result.maxNodeLimitHit = result.nodes.size() >= input.maxNodes;
                ++result.rejectedPortalCount;
                ++result.invalidPortalCount;
                continue;
            }

            ++result.portalCandidateCount;
            const IndoorFace &face = mapData.faces[faceId];
            const uint32_t effectiveAttributes =
                input.pMapDeltaData != nullptr && faceId < input.pMapDeltaData->faceAttributes.size()
                    ? input.pMapDeltaData->faceAttributes[faceId]
                    : face.attributes;

            if (static_cast<int16_t>(faceId) == currentNode.entryPortalFaceId
                || (!face.isPortal && !hasFaceAttribute(effectiveAttributes, FaceAttribute::IsPortal))
                || !indoorPortalFaceVisible(faceId, face, input.pMapDeltaData, input.pEventRuntimeState))
            {
                ++result.rejectedPortalCount;
                ++result.invalidPortalCount;
                continue;
            }

            if (!input.ignoreMechanismBlockers
                && portalBlockedByClosedDoor(face, vertices, input.pMapDeltaData, input.pEventRuntimeState))
            {
                ++result.rejectedPortalCount;
                ++result.blockedPortalCount;
                continue;
            }

            int16_t connectedSectorId = -1;
            const bool portalFlipped = face.roomNumber != static_cast<uint16_t>(currentNode.sectorId);

            if (face.roomNumber == static_cast<uint16_t>(currentNode.sectorId))
            {
                connectedSectorId = static_cast<int16_t>(face.roomBehindNumber);
            }
            else if (face.roomBehindNumber == static_cast<uint16_t>(currentNode.sectorId))
            {
                connectedSectorId = static_cast<int16_t>(face.roomNumber);
            }

            if (connectedSectorId < 0
                || static_cast<size_t>(connectedSectorId) >= mapData.sectors.size()
                || hasAncestorSector(result.nodes, static_cast<int16_t>(nodeIndex), connectedSectorId))
            {
                ++result.rejectedPortalCount;
                ++result.ancestorRejectedPortalCount;
                continue;
            }

            const IndoorFaceGeometryData *pGeometry =
                geometryCache.geometryForFace(mapData, vertices, static_cast<size_t>(faceId));

            if (pGeometry == nullptr || pGeometry->vertices.size() < 3)
            {
                ++result.rejectedPortalCount;
                ++result.invalidPortalCount;
                continue;
            }

            if (currentNode.parentNodeIndex >= 0
                && portalFlipped == faceFrontSideFacesCamera(*pGeometry, input.cameraPosition))
            {
                ++result.rejectedPortalCount;
                ++result.directionRejectedPortalCount;
                continue;
            }

            const bool nearPortal = cameraNearPortal(input.cameraPosition, pGeometry->vertices);
            const std::vector<bx::Vec3> clippedPortal =
                nearPortal
                ? pGeometry->vertices
                : clipPolygonToFrustum(pGeometry->vertices, currentNode.frustumPlanes);

            if (clippedPortal.size() < 3)
            {
                ++result.rejectedPortalCount;
                ++result.clippedPortalRejectedCount;
                continue;
            }

            std::vector<IndoorVisibilityPlane> childFrustumPlanes;
            if (std::fabs(pGeometry->normal.z) > 0.999f || nearPortal)
            {
                childFrustumPlanes = rootFrustumPlanes;
            }
            else
            {
                childFrustumPlanes = buildPortalFrustumPlanes(input.cameraPosition, clippedPortal);
            }

            if (childFrustumPlanes.size() < 3)
            {
                ++result.rejectedPortalCount;
                ++result.clippedPortalRejectedCount;
                continue;
            }

            IndoorVisibilityNode childNode = {};
            childNode.sectorId = connectedSectorId;
            childNode.parentNodeIndex = static_cast<int16_t>(nodeIndex);
            childNode.entryPortalFaceId = static_cast<int16_t>(faceId);
            childNode.depth = static_cast<uint16_t>(currentNode.depth + 1);
            childNode.frustumPlanes = std::move(childFrustumPlanes);
            const uint16_t childNodeIndex = static_cast<uint16_t>(result.nodes.size());
            result.nodes.push_back(std::move(childNode));
            result.nodeIndicesBySector[static_cast<size_t>(connectedSectorId)].push_back(childNodeIndex);
            result.visibleSectorMask[static_cast<size_t>(connectedSectorId)] = 1;
            ++result.acceptedPortalCount;
        }
    }

    // Some compiled BLVs contain standalone/moving-geometry sectors with no portal links. They are not traversal nodes,
    // but their faces still need to render when they are directly in the camera frustum, e.g. elevator platforms/shafts.
    for (size_t sectorId = 0; sectorId < mapData.sectors.size(); ++sectorId)
    {
        if (result.visibleSectorMask[sectorId] != 0)
        {
            continue;
        }

        const IndoorSector &sector = mapData.sectors[sectorId];

        if (!sector.portalFaceIds.empty() || sector.faceIds.empty())
        {
            continue;
        }

        if (sectorHasFaceInsideFrustum(
                mapData,
                vertices,
                static_cast<int16_t>(sectorId),
                rootFrustumPlanes,
                geometryCache))
        {
            result.visibleSectorMask[sectorId] = 1;
            ++result.orphanVisibleSectorCount;
        }
    }

    return result;
}
}
