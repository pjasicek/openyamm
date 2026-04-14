#pragma once

#include "game/outdoor/OutdoorMapData.h"

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
inline float outdoorGridCornerWorldX(int gridX)
{
    return static_cast<float>((gridX - 64) * OutdoorMapData::TerrainTileSize);
}

inline float outdoorGridCornerWorldY(int gridY)
{
    return static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
}

inline float outdoorWorldToGridXFloat(float x)
{
    return x / static_cast<float>(OutdoorMapData::TerrainTileSize) + 64.0f;
}

inline float outdoorWorldToGridYFloat(float y)
{
    return 64.0f - (y / static_cast<float>(OutdoorMapData::TerrainTileSize));
}

struct OutdoorFaceGeometryData
{
    size_t bModelIndex = 0;
    size_t faceIndex = 0;
    std::string modelName;
    uint8_t polygonType = 0;
    uint32_t attributes = 0;
    bool isWalkable = false;
    bool hasPlane = false;
    float minX = 0.0f;
    float maxX = 0.0f;
    float minY = 0.0f;
    float maxY = 0.0f;
    float minZ = 0.0f;
    float maxZ = 0.0f;
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
    std::vector<bx::Vec3> vertices;
};

struct OutdoorSupportFloorSample
{
    float height = 0.0f;
    bool fromBModel = false;
    size_t bModelIndex = 0;
    size_t faceIndex = 0;
};

bool isOutdoorWalkablePolygonType(uint8_t polygonType);
bx::Vec3 outdoorBModelPointToWorld(int x, int y, int z);
bx::Vec3 outdoorBModelVertexToWorld(const OutdoorBModelVertex &vertex);
float sampleOutdoorTerrainHeight(const OutdoorMapData &outdoorMapData, float x, float y);
float sampleOutdoorRenderedTerrainHeight(const OutdoorMapData &outdoorMapData, float x, float y);
float sampleOutdoorTerrainNormalZ(const OutdoorMapData &outdoorMapData, float x, float y);
bool outdoorTerrainSlopeTooHigh(const OutdoorMapData &outdoorMapData, float x, float y);
uint8_t sampleOutdoorTerrainTileAttributes(const OutdoorMapData &outdoorMapData, float x, float y);
bool isOutdoorTerrainWater(const OutdoorMapData &outdoorMapData, float x, float y);
bool isOutdoorTerrainBurning(const OutdoorMapData &outdoorMapData, float x, float y);
bool buildOutdoorFaceGeometry(
    const OutdoorBModel &bModel,
    size_t bModelIndex,
    const OutdoorBModelFace &face,
    size_t faceIndex,
    OutdoorFaceGeometryData &geometry
);
bool isPointInsideOutdoorPolygon(float x, float y, const std::vector<bx::Vec3> &vertices);
bool isPointInsideOrNearOutdoorPolygon(float x, float y, const std::vector<bx::Vec3> &vertices, float slack);
bool isPointInsideOutdoorPolygonProjected(
    const bx::Vec3 &point,
    const std::vector<bx::Vec3> &vertices,
    const bx::Vec3 &normal
);
float calculateOutdoorFaceHeight(const OutdoorFaceGeometryData &geometry, float x, float y);
bool intersectOutdoorSegmentWithFace(
    const OutdoorFaceGeometryData &geometry,
    const bx::Vec3 &segmentStart,
    const bx::Vec3 &segmentEnd,
    float &intersectionFactor,
    bx::Vec3 &intersectionPoint
);
bool isOutdoorCylinderBlockedByFace(
    const OutdoorFaceGeometryData &geometry,
    float x,
    float y,
    float z,
    float radius,
    float height
);
OutdoorSupportFloorSample sampleOutdoorSupportFloor(
    const OutdoorMapData &outdoorMapData,
    float x,
    float y,
    float z,
    float maxRise,
    float xySlack
);
float sampleOutdoorSupportFloorHeight(const OutdoorMapData &outdoorMapData, float x, float y, float z);
float sampleOutdoorPlacementFloorHeight(const OutdoorMapData &outdoorMapData, float x, float y, float z);
}
