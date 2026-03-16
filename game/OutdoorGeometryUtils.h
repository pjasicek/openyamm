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

bool isOutdoorWalkablePolygonType(uint8_t polygonType);
bx::Vec3 outdoorBModelPointToWorld(int x, int y, int z);
bx::Vec3 outdoorBModelVertexToWorld(const OutdoorBModelVertex &vertex);
float sampleOutdoorTerrainHeight(const OutdoorMapData &outdoorMapData, float x, float y);
float sampleOutdoorTerrainNormalZ(const OutdoorMapData &outdoorMapData, float x, float y);
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
}
