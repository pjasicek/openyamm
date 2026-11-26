#pragma once

#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/pathfinding/PathMap.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
struct MapDeltaData;

enum class OutdoorPathTerrainMode
{
    Full,
    LandOnly
};

struct OutdoorPathMapBuildOptions
{
    OutdoorPathTerrainMode terrainMode = OutdoorPathTerrainMode::Full;
    bool includeTerrain = true;
    bool includeBModels = true;
    float spatialGridCellSize = 512.0f;
};

struct OutdoorPathMapBuildResult
{
    PathMap pathMap;
    size_t terrainTriangleCount = 0;
    size_t skippedWaterTerrainTriangleCount = 0;
    size_t skippedVoidTerrainTriangleCount = 0;
    // Upright walls the planner keeps bodies from, one per edge between a void cell and the land.
    size_t voidRimWallCount = 0;
    size_t sourceBModelFaceCount = 0;
    size_t bModelPathFacetCount = 0;
    size_t skippedBModelFaceCount = 0;
    size_t pathFacetCount = 0;
    size_t cookedNavigationFacetCount = 0;
    size_t dynamicNavigationFacetCount = 0;
};

class OutdoorPathfindingBuilder
{
public:
    static OutdoorPathMapBuildResult buildPathMap(
        const OutdoorMapData &outdoorMapData,
        const MapDeltaData *pMapDeltaData = nullptr,
        const std::vector<OutdoorFaceGeometryData> *pFaceGeometries = nullptr,
        const OutdoorPathMapBuildOptions &options = OutdoorPathMapBuildOptions(),
        const std::vector<uint8_t> *pOutdoorLandMask = nullptr
    );

    static int32_t bModelSourceId(size_t bModelIndex, size_t faceIndex);
    static uint64_t bModelSourceKey(size_t bModelIndex, size_t faceIndex);
};
}
