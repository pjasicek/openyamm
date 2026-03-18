#pragma once

#include "game/OutdoorMapData.h"

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
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
bool isPointInsideOutdoorPolygonProjected(
    const bx::Vec3 &point,
    const std::vector<bx::Vec3> &vertices,
    const bx::Vec3 &normal
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
