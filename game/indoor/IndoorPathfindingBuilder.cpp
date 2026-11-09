#include "game/indoor/IndoorPathfindingBuilder.h"

#include "game/FaceEnums.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
PathFacetKind convertPathFacetKind(const IndoorFaceGeometryData &geometry)
{
    if (geometry.isPortal)
    {
        return PathFacetKind::Portal;
    }

    switch (geometry.kind)
    {
        case IndoorFaceKind::Floor:
            return PathFacetKind::Floor;
        case IndoorFaceKind::Ceiling:
            return PathFacetKind::Ceiling;
        case IndoorFaceKind::Wall:
            return PathFacetKind::Wall;
        case IndoorFaceKind::Unknown:
        default:
            return PathFacetKind::Generic;
    }
}

PathFacet buildPathFacet(const IndoorFaceGeometryData &geometry, bool actorBarrier)
{
    PathFacet facet = {};
    facet.kind = convertPathFacetKind(geometry);
    facet.attributes.portal = geometry.isPortal;
    // The path map is the monsters': the scene's monster-only walls (IndoorMapData::actorBarrierFaceIds) are solid
    // walls to it, never a floor, although the face is invisible and untouchable.
    facet.attributes.invisible = !actorBarrier && hasFaceAttribute(geometry.attributes, FaceAttribute::Invisible);
    facet.attributes.untouchable = !actorBarrier && hasFaceAttribute(geometry.attributes, FaceAttribute::Untouchable);
    // Horizontal portals connect sectors; they provide no physical floor or overhead support.
    facet.walkableFloor = geometry.isWalkable && !geometry.isPortal && !actorBarrier;
    facet.blocking = !geometry.isPortal && !facet.attributes.untouchable;
    facet.sourceId = static_cast<int32_t>(geometry.faceIndex);
    facet.vertices.reserve(geometry.vertices.size());

    for (const bx::Vec3 &vertex : geometry.vertices)
    {
        facet.vertices.push_back({vertex.x, vertex.y, vertex.z});
    }

    return facet;
}
}

IndoorPathMapBuildResult IndoorPathfindingBuilder::buildPathMap(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const MapDeltaData *pMapDeltaData,
    IndoorFaceGeometryCache *pGeometryCache,
    float spatialGridCellSize,
    const std::vector<uint32_t> &openAiDoorIds
)
{
    IndoorFaceGeometryCache localGeometryCache;
    IndoorFaceGeometryCache *pActiveGeometryCache = pGeometryCache;

    if (pActiveGeometryCache == nullptr)
    {
        localGeometryCache.reset(indoorMapData.faces.size());
        pActiveGeometryCache = &localGeometryCache;
    }

    pActiveGeometryCache->setAttributeOverrides(pMapDeltaData);

    IndoorPathMapBuildResult result = {};
    result.sourceFaceCount = indoorMapData.faces.size();
    std::vector<PathFacet> pathFacets;
    pathFacets.reserve(indoorMapData.faces.size());
    std::vector<uint8_t> actorBarrierMask;

    if (!indoorMapData.actorBarrierFaceIds.empty())
    {
        actorBarrierMask.assign(indoorMapData.faces.size(), 0);

        for (uint16_t faceId : indoorMapData.actorBarrierFaceIds)
        {
            if (faceId < actorBarrierMask.size())
            {
                actorBarrierMask[faceId] = 1;
            }
        }
    }

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFaceGeometryData *pGeometry =
            pActiveGeometryCache->geometryForFace(indoorMapData, vertices, faceIndex);

        if (pGeometry == nullptr || !pGeometry->hasPlane || pGeometry->vertices.size() < 3)
        {
            ++result.skippedFaceCount;
            continue;
        }

        // A shut door MM9 monsters open (scene `ai_open`) does not block their routes, as MM9's rails run through
        // doors: walking into it, they open it (BaseDoor.inc; MM9_MONSTER_AI_PLAN.md phase 4a). Open, it stands where
        // it swung or slid to and blocks there: Thjorad Mine's slag extractor hatch, swung open across the corridor,
        // had Hjarrand walk into it for ever on his way back to MMarker1.
        const IndoorAiDoor *pAiDoor = findIndoorAiDoorByFace(indoorMapData, faceIndex);

        if (pAiDoor != nullptr
            && std::find(openAiDoorIds.begin(), openAiDoorIds.end(), pAiDoor->doorId) == openAiDoorIds.end())
        {
            ++result.skippedFaceCount;
            continue;
        }

        pathFacets.push_back(
            buildPathFacet(*pGeometry, faceIndex < actorBarrierMask.size() && actorBarrierMask[faceIndex] != 0));
    }

    result.pathFacetCount = pathFacets.size();
    result.pathMap.setFacets(std::move(pathFacets));
    result.pathMap.buildSpatialGrid(spatialGridCellSize);
    return result;
}
}
