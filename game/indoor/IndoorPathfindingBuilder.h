#pragma once

#include "game/indoor/IndoorGeometryUtils.h"
#include "game/pathfinding/PathMap.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorPathMapBuildResult
{
    PathMap pathMap;
    size_t sourceFaceCount = 0;
    size_t pathFacetCount = 0;
    size_t skippedFaceCount = 0;
};

class IndoorPathfindingBuilder
{
public:
    // A door MM9 monsters open (scene `ai_open`) is left out of the map while it is shut; openAiDoorIds lists those
    // standing open (or opening), whose faces block routes where they stand, as any other door's do.
    static IndoorPathMapBuildResult buildPathMap(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        const MapDeltaData *pMapDeltaData = nullptr,
        IndoorFaceGeometryCache *pGeometryCache = nullptr,
        float spatialGridCellSize = 512.0f,
        const std::vector<uint32_t> &openAiDoorIds = {}
    );
};
}
