#include "game/indoor/IndoorPortalVisibility.h"

#include "game/events/EventRuntime.h"
#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorPortalGraph.h"
#include "game/maps/MapDeltaData.h"

#include <algorithm>
#include <cmath>
#include <string_view>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float VisibilityEpsilon = 0.001f;
constexpr float FrustumClipEpsilon = 0.001f;
constexpr float NearPortalSlack = 16.0f;
constexpr float NearPortalPlaneDistance = 9.0f;
constexpr float PortalNearClipDistance = 8.0f;

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
    const IndoorVisibilityPlane &plane,
    float epsilon = FrustumClipEpsilon
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
        const bx::Vec3 &next = polygon[pointIndex + 1 < polygon.size() ? pointIndex + 1 : 0];
        const float currentDistance = signedPlaneDistance(plane, current);
        const float nextDistance = signedPlaneDistance(plane, next);
        const bool currentInside = currentDistance >= -epsilon;
        const bool nextInside = nextDistance >= -epsilon;

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

bool portalHasScreenHeight(
    const std::vector<bx::Vec3> &polygon,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &forward,
    const bx::Vec3 &up,
    float projectionScale,
    int viewportHeight)
{
    if (polygon.size() < 3)
    {
        return false;
    }
    if (viewportHeight <= 0)
    {
        return true;
    }

    int minRow = viewportHeight;
    int maxRow = 0;
    for (const bx::Vec3 &point : polygon)
    {
        const bx::Vec3 relative = subtractVec(point, cameraPosition);
        const float depth = std::max(dotVec(relative, forward), PortalNearClipDistance);
        const int row = viewportHeight / 2 - int(std::floor(dotVec(relative, up) * projectionScale / depth));
        minRow = std::min(minRow, row);
        maxRow = std::max(maxRow, row);
    }
    // MM8 rejects equal min/max projected Y, including after clipping to the parent window.
    return minRow < maxRow;
}

bool indoorPortalFaceVisible(
    size_t faceIndex,
    const std::optional<EventRuntimeState> *pEventRuntimeState)
{
    return pEventRuntimeState == nullptr
        || !pEventRuntimeState->has_value()
        || !(*pEventRuntimeState)->hasFacetInvisibleOverride(static_cast<uint32_t>(faceIndex));
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

bool cameraNearPortal(
    const bx::Vec3 &cameraPosition,
    const std::vector<bx::Vec3> &portalPolygon,
    float slack = NearPortalSlack)
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

    return cameraPosition.x >= minBounds.x - slack
        && cameraPosition.x <= maxBounds.x + slack
        && cameraPosition.y >= minBounds.y - slack
        && cameraPosition.y <= maxBounds.y + slack
        && cameraPosition.z >= minBounds.z - slack
        && cameraPosition.z <= maxBounds.z + slack;
}

bool sectorHasPortalGraphLinks(const IndoorPortalGraph &portalGraph, int16_t sectorId)
{
    return sectorId >= 0
        && static_cast<size_t>(sectorId) < portalGraph.sectors.size()
        && !portalGraph.sectors[static_cast<size_t>(sectorId)].portalLinkIds.empty();
}

bool sameVisibilityPlane(const IndoorVisibilityPlane &left, const IndoorVisibilityPlane &right)
{
    return left.normal.x == right.normal.x
        && left.normal.y == right.normal.y
        && left.normal.z == right.normal.z
        && left.distance == right.distance;
}

bool sameVisibilityFrustum(const IndoorVisibilityFrustum &left, const IndoorVisibilityFrustum &right)
{
    if (left.size() != right.size())
    {
        return false;
    }

    for (size_t index = 0; index < left.size(); ++index)
    {
        if (!sameVisibilityPlane(left[index], right[index]))
        {
            return false;
        }
    }

    return true;
}

void appendUniqueSectorFrustum(
    IndoorPortalVisibilityResult &result,
    int16_t sectorId,
    const IndoorVisibilityFrustum &frustum)
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= result.frustumsBySector.size())
    {
        return;
    }

    std::vector<IndoorVisibilityFrustum> &sectorFrustums =
        result.frustumsBySector[static_cast<size_t>(sectorId)];

    for (const IndoorVisibilityFrustum &existingFrustum : sectorFrustums)
    {
        if (sameVisibilityFrustum(existingFrustum, frustum))
        {
            return;
        }
    }

    sectorFrustums.push_back(frustum);
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

    appendUniqueSectorFrustum(result, sectorId, rootFrustumPlanes);
}

void appendPortalTrace(
    IndoorPortalVisibilityResult &result,
    bool collectTrace,
    int16_t sourceSectorId,
    int16_t targetSectorId,
    uint16_t faceId,
    uint16_t portalLinkId,
    uint16_t depth,
    bool accepted,
    std::string_view reason)
{
    if (!collectTrace)
    {
        return;
    }

    result.portalTraces.push_back({
        .sourceSectorId = sourceSectorId,
        .targetSectorId = targetSectorId,
        .faceId = faceId,
        .portalLinkId = portalLinkId,
        .depth = depth,
        .accepted = accepted,
        .reason = std::string(reason),
    });
}

void appendAcceptedPortalVisibility(
    IndoorPortalVisibilityResult &result,
    int16_t targetSectorId,
    uint16_t faceId)
{
    result.acceptedPortals.push_back({
        .targetSectorId = targetSectorId,
        .faceId = faceId,
    });
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
    IndoorPortalGraph localPortalGraph = {};
    const IndoorPortalGraph *pPortalGraph = input.pPortalGraph;

    if (pPortalGraph == nullptr)
    {
        localPortalGraph = buildIndoorPortalGraph(mapData, input.pMapDeltaData);
        pPortalGraph = &localPortalGraph;
    }

    const std::vector<IndoorVisibilityPlane> rootFrustumPlanes = buildCameraFrustumPlanes(input);
    const bx::Vec3 forward = normalizeVec(input.cameraForward);
    const bx::Vec3 right = normalizeVec(crossVec(forward, input.cameraUp));
    const bx::Vec3 up = normalizeVec(crossVec(right, forward));
    const float projectionScale = input.viewportHeight * 0.5f
        / std::tan(input.verticalFovDegrees * 3.14159265358979323846f / 360.0f);
    const IndoorVisibilityPlane nearClipPlane = {
        forward, -dotVec(forward, input.cameraPosition) - PortalNearClipDistance
    };
    result.visibleSectorMask.assign(mapData.sectors.size(), 0);
    result.nodeIndicesBySector.resize(mapData.sectors.size());
    result.frustumsBySector.resize(mapData.sectors.size());
    result.nodes.reserve(std::min<size_t>(input.maxNodes, mapData.sectors.size() * 2 + 1));

    appendRootVisibilityNode(result, input.startSectorId, rootFrustumPlanes);

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

        if (!sectorHasPortalGraphLinks(*pPortalGraph, currentNode.sectorId))
        {
            continue;
        }

        const IndoorSectorPortalCache &sectorCache =
            pPortalGraph->sectors[static_cast<size_t>(currentNode.sectorId)];
        std::vector<bx::Vec3> portalPolygon;

        for (uint16_t portalLinkId : sectorCache.portalLinkIds)
        {
            if (result.nodes.size() >= input.maxNodes || portalLinkId >= pPortalGraph->portals.size())
            {
                result.maxNodeLimitHit = result.nodes.size() >= input.maxNodes;
                ++result.rejectedPortalCount;
                ++result.invalidPortalCount;
                appendPortalTrace(
                    result,
                    input.collectPortalTraces,
                    currentNode.sectorId,
                    -1,
                    0,
                    portalLinkId,
                    currentNode.depth,
                    false,
                    result.maxNodeLimitHit ? "max_node_limit" : "invalid_portal_link");
                continue;
            }

            const IndoorPortalLink &portalLink = pPortalGraph->portals[portalLinkId];
            const uint16_t faceId = portalLink.faceId;
            int16_t connectedSectorId = -1;

            if (portalLink.sectorA == static_cast<uint16_t>(currentNode.sectorId))
            {
                connectedSectorId = static_cast<int16_t>(portalLink.sectorB);
            }
            else if (portalLink.sectorB == static_cast<uint16_t>(currentNode.sectorId))
            {
                connectedSectorId = static_cast<int16_t>(portalLink.sectorA);
            }

            if (faceId >= mapData.faces.size())
            {
                ++result.rejectedPortalCount;
                ++result.invalidPortalCount;
                appendPortalTrace(
                    result,
                    input.collectPortalTraces,
                    currentNode.sectorId,
                    connectedSectorId,
                    faceId,
                    portalLinkId,
                    currentNode.depth,
                    false,
                    "invalid_face_id");
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
                || !indoorPortalFaceVisible(faceId, input.pEventRuntimeState))
            {
                ++result.rejectedPortalCount;
                ++result.invalidPortalCount;
                const char *reason =
                    static_cast<int16_t>(faceId) == currentNode.entryPortalFaceId
                        ? "entry_portal"
                        : ((!face.isPortal && !hasFaceAttribute(effectiveAttributes, FaceAttribute::IsPortal))
                            ? "not_portal_face"
                            : "portal_hidden_override");
                appendPortalTrace(
                    result,
                    input.collectPortalTraces,
                    currentNode.sectorId,
                    connectedSectorId,
                    faceId,
                    portalLinkId,
                    currentNode.depth,
                    false,
                    reason);
                continue;
            }

            if (connectedSectorId < 0
                || static_cast<size_t>(connectedSectorId) >= mapData.sectors.size()
                || hasAncestorSector(result.nodes, static_cast<int16_t>(nodeIndex), connectedSectorId))
            {
                ++result.rejectedPortalCount;
                ++result.ancestorRejectedPortalCount;
                const char *reason =
                    connectedSectorId < 0 || static_cast<size_t>(connectedSectorId) >= mapData.sectors.size()
                        ? "invalid_target_sector"
                        : "ancestor_sector";
                appendPortalTrace(
                    result,
                    input.collectPortalTraces,
                    currentNode.sectorId,
                    connectedSectorId,
                    faceId,
                    portalLinkId,
                    currentNode.depth,
                    false,
                    reason);
                continue;
            }

            // Door movement changes the aperture, not its authored front/back orientation.
            // Use the current vertices with the original face normal, as MM8 does.
            portalPolygon.clear();
            for (uint16_t vertexId : face.vertexIndices)
            {
                if (vertexId >= input.pVertices->size())
                {
                    portalPolygon.clear();
                    break;
                }
                portalPolygon.push_back(indoorVertexToWorld((*input.pVertices)[vertexId]));
            }
            bx::Vec3 planeNormal = {0.0f, 0.0f, 0.0f};
            if (face.planeNormal)
            {
                planeNormal = normalizeVec({float((*face.planeNormal)[0]), float((*face.planeNormal)[1]),
                    float((*face.planeNormal)[2])});
            }
            else
            {
                IndoorFaceGeometryData geometry = {};
                if (buildIndoorFaceGeometry(mapData, mapData.vertices, faceId, geometry))
                {
                    planeNormal = geometry.normal;
                }
            }
            if (portalPolygon.size() < 3 || lengthVec(planeNormal) <= VisibilityEpsilon)
            {
                ++result.rejectedPortalCount;
                ++result.invalidPortalCount;
                appendPortalTrace(
                    result, input.collectPortalTraces, currentNode.sectorId, connectedSectorId,
                    faceId, portalLinkId, currentNode.depth, false, "invalid_portal_geometry");
                continue;
            }

            float planeSide = dotVec(planeNormal, subtractVec(portalPolygon.front(), input.cameraPosition));
            // MM8's full-view exception applies only at the initial node, within 9 units of
            // the portal plane and its bounds expanded by 16 units.
            const bool nearPortal = nodeIndex == 0
                && std::fabs(planeSide) <= NearPortalPlaneDistance
                && cameraNearPortal(input.cameraPosition, portalPolygon);
            // A portal beside the camera that the view would drop passes on the view it is reached through instead
            // (nearPortalReach: a converter's map, whose floor or wall near a doorway may be the room's across it, so
            // the camera's sector from the floor under it is that room's; MM9's voxels are 41 units). At the camera's
            // own sector that is the whole view; deeper, the frustum the portal's sector was entered with (a camera at
            // a corner where two portals meet sees the second one edge-on).
            const bool portalWithinReach = input.nearPortalReach > 0.0f
                && std::fabs(planeSide) <= input.nearPortalReach
                && cameraNearPortal(input.cameraPosition, portalPolygon, input.nearPortalReach);
            if (currentNode.sectorId != face.roomNumber)
            {
                planeSide = -planeSide;
            }
            bool wholeView = nearPortal;
            bool passOnView = false;
            if (!wholeView && planeSide >= 0.0f)
            {
                if (!portalWithinReach)
                {
                    ++result.rejectedPortalCount;
                    ++result.directionRejectedPortalCount;
                    appendPortalTrace(
                        result, input.collectPortalTraces, currentNode.sectorId, connectedSectorId,
                        faceId, portalLinkId, currentNode.depth, false, "portal_facing");
                    continue;
                }
                passOnView = true;
            }

            std::vector<IndoorVisibilityPlane> childFrustumPlanes;
            if (wholeView)
            {
                childFrustumPlanes = rootFrustumPlanes;
            }
            else if (passOnView)
            {
                childFrustumPlanes = currentNode.frustumPlanes;
            }
            else
            {
                // Reject an empty aperture instead of expanding it to adjoining sector bounds.
                // The same clipping applies to horizontal portals and every traversal depth.
                const std::vector<bx::Vec3> clippedPortal = clipPolygonToFrustum(
                    clipPolygonToPlane(portalPolygon, nearClipPlane), currentNode.frustumPlanes);
                if (input.maxDistance > 0.0f && !clippedPortal.empty())
                {
                    // Beyond the view distance: its nearest point (depth is linear, so a corner) past the far plane.
                    float nearestDepth = std::numeric_limits<float>::max();
                    for (const bx::Vec3 &point : clippedPortal)
                    {
                        nearestDepth = std::min(nearestDepth, dotVec(forward, subtractVec(point, input.cameraPosition)));
                    }
                    if (nearestDepth > input.maxDistance)
                    {
                        ++result.rejectedPortalCount;
                        ++result.clippedPortalRejectedCount;
                        appendPortalTrace(
                            result, input.collectPortalTraces, currentNode.sectorId, connectedSectorId,
                            faceId, portalLinkId, currentNode.depth, false, "beyond_view_distance");
                        continue;
                    }
                }
                if (portalHasScreenHeight(clippedPortal, input.cameraPosition, forward, up,
                        projectionScale, input.viewportHeight))
                {
                    childFrustumPlanes = buildPortalFrustumPlanes(input.cameraPosition, clippedPortal);
                }
                if (childFrustumPlanes.size() < 3)
                {
                    if (!portalWithinReach)
                    {
                        ++result.rejectedPortalCount;
                        ++result.clippedPortalRejectedCount;
                        appendPortalTrace(
                            result, input.collectPortalTraces, currentNode.sectorId, connectedSectorId,
                            faceId, portalLinkId, currentNode.depth, false, "clipped_portal");
                        continue;
                    }
                    childFrustumPlanes = currentNode.frustumPlanes;
                }
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
            appendUniqueSectorFrustum(result, connectedSectorId, result.nodes.back().frustumPlanes);
            result.visibleSectorMask[static_cast<size_t>(connectedSectorId)] = 1;
            appendAcceptedPortalVisibility(result, connectedSectorId, faceId);
            appendPortalTrace(
                result,
                input.collectPortalTraces,
                currentNode.sectorId,
                connectedSectorId,
                faceId,
                portalLinkId,
                currentNode.depth,
                true,
                "accepted");
            ++result.acceptedPortalCount;
        }
    }

    return result;
}
}
