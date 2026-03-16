#include "game/OutdoorGeometryUtils.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float GeometryEpsilon = 0.0001f;
constexpr uint8_t OutdoorPolygonFloor = 0x3;
constexpr uint8_t OutdoorPolygonInBetweenFloorAndWall = 0x4;
constexpr uint8_t TerrainTileBurn = 0x01;
constexpr uint8_t TerrainTileWater = 0x02;

bx::Vec3 vecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

bx::Vec3 vecCross(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
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
}

bool isOutdoorWalkablePolygonType(uint8_t polygonType)
{
    return polygonType == OutdoorPolygonFloor || polygonType == OutdoorPolygonInBetweenFloorAndWall;
}

bx::Vec3 outdoorBModelPointToWorld(int x, int y, int z)
{
    return {
        static_cast<float>(-x),
        static_cast<float>(y),
        static_cast<float>(z)
    };
}

bx::Vec3 outdoorBModelVertexToWorld(const OutdoorBModelVertex &vertex)
{
    return outdoorBModelPointToWorld(vertex.x, vertex.y, vertex.z);
}

float sampleOutdoorTerrainHeight(const OutdoorMapData &outdoorMapData, float x, float y)
{
    const float gridX = 64.0f - (x / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const float gridY = 64.0f - (y / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const int sampleX0 = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 1);
    const int sampleY0 = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 1);
    const int sampleX1 = std::clamp(sampleX0 + 1, 0, OutdoorMapData::TerrainWidth - 1);
    const int sampleY1 = std::clamp(sampleY0 + 1, 0, OutdoorMapData::TerrainHeight - 1);
    const float fractionX = std::clamp(gridX - static_cast<float>(sampleX0), 0.0f, 1.0f);
    const float fractionY = std::clamp(gridY - static_cast<float>(sampleY0), 0.0f, 1.0f);

    const size_t index00 = static_cast<size_t>(sampleY0 * OutdoorMapData::TerrainWidth + sampleX0);
    const size_t index10 = static_cast<size_t>(sampleY0 * OutdoorMapData::TerrainWidth + sampleX1);
    const size_t index01 = static_cast<size_t>(sampleY1 * OutdoorMapData::TerrainWidth + sampleX0);
    const size_t index11 = static_cast<size_t>(sampleY1 * OutdoorMapData::TerrainWidth + sampleX1);

    const float height00 = static_cast<float>(outdoorMapData.heightMap[index00]);
    const float height10 = static_cast<float>(outdoorMapData.heightMap[index10]);
    const float height01 = static_cast<float>(outdoorMapData.heightMap[index01]);
    const float height11 = static_cast<float>(outdoorMapData.heightMap[index11]);

    const float topHeight = height00 + (height10 - height00) * fractionX;
    const float bottomHeight = height01 + (height11 - height01) * fractionX;
    const float heightSample = topHeight + (bottomHeight - topHeight) * fractionY;

    return heightSample * static_cast<float>(OutdoorMapData::TerrainHeightScale);
}

float sampleOutdoorTerrainNormalZ(const OutdoorMapData &outdoorMapData, float x, float y)
{
    const float sampleOffset = static_cast<float>(OutdoorMapData::TerrainTileSize);
    const float heightLeft = sampleOutdoorTerrainHeight(outdoorMapData, x - sampleOffset, y);
    const float heightRight = sampleOutdoorTerrainHeight(outdoorMapData, x + sampleOffset, y);
    const float heightDown = sampleOutdoorTerrainHeight(outdoorMapData, x, y - sampleOffset);
    const float heightUp = sampleOutdoorTerrainHeight(outdoorMapData, x, y + sampleOffset);
    const float gradientX = (heightRight - heightLeft) / (sampleOffset * 2.0f);
    const float gradientY = (heightUp - heightDown) / (sampleOffset * 2.0f);
    return 1.0f / std::sqrt(gradientX * gradientX + gradientY * gradientY + 1.0f);
}

uint8_t sampleOutdoorTerrainTileAttributes(const OutdoorMapData &outdoorMapData, float x, float y)
{
    if (outdoorMapData.attributeMap.empty())
    {
        return 0;
    }

    const float gridX = 64.0f - (x / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const float gridY = 64.0f - (y / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const int tileX = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int tileY = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    const size_t tileIndex = static_cast<size_t>(tileY * OutdoorMapData::TerrainWidth + tileX);

    if (tileIndex >= outdoorMapData.attributeMap.size())
    {
        return 0;
    }

    return outdoorMapData.attributeMap[tileIndex];
}

bool isOutdoorTerrainWater(const OutdoorMapData &outdoorMapData, float x, float y)
{
    return (sampleOutdoorTerrainTileAttributes(outdoorMapData, x, y) & TerrainTileWater) != 0;
}

bool isOutdoorTerrainBurning(const OutdoorMapData &outdoorMapData, float x, float y)
{
    return (sampleOutdoorTerrainTileAttributes(outdoorMapData, x, y) & TerrainTileBurn) != 0;
}

bool buildOutdoorFaceGeometry(
    const OutdoorBModel &bModel,
    size_t bModelIndex,
    const OutdoorBModelFace &face,
    size_t faceIndex,
    OutdoorFaceGeometryData &geometry
)
{
    if (face.vertexIndices.size() < 3)
    {
        return false;
    }

    geometry = {};
    geometry.bModelIndex = bModelIndex;
    geometry.faceIndex = faceIndex;
    geometry.modelName = bModel.name;
    geometry.polygonType = face.polygonType;
    geometry.attributes = face.attributes;
    geometry.isWalkable = isOutdoorWalkablePolygonType(face.polygonType);
    geometry.vertices.reserve(face.vertexIndices.size());

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= bModel.vertices.size())
        {
            geometry.vertices.clear();
            return false;
        }

        geometry.vertices.push_back(outdoorBModelVertexToWorld(bModel.vertices[vertexIndex]));
    }

    if (geometry.vertices.size() < 3)
    {
        return false;
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

    const bx::Vec3 edge1 = vecSubtract(geometry.vertices[1], geometry.vertices[0]);
    const bx::Vec3 edge2 = vecSubtract(geometry.vertices[2], geometry.vertices[0]);
    geometry.normal = vecNormalize(vecCross(edge1, edge2));
    geometry.hasPlane = vecLength(geometry.normal) > GeometryEpsilon;
    return true;
}

bool isPointInsideOutdoorPolygon(float x, float y, const std::vector<bx::Vec3> &vertices)
{
    if (vertices.size() < 3)
    {
        return false;
    }

    bool isInside = false;
    size_t previousIndex = vertices.size() - 1;

    for (size_t currentIndex = 0; currentIndex < vertices.size(); ++currentIndex)
    {
        const bx::Vec3 &currentVertex = vertices[currentIndex];
        const bx::Vec3 &previousVertex = vertices[previousIndex];
        const bool intersects =
            ((currentVertex.y > y) != (previousVertex.y > y))
            && (x < (previousVertex.x - currentVertex.x) * (y - currentVertex.y)
                    / ((previousVertex.y - currentVertex.y) + GeometryEpsilon)
                + currentVertex.x);

        if (intersects)
        {
            isInside = !isInside;
        }

        previousIndex = currentIndex;
    }

    return isInside;
}

bool isPointInsideOutdoorPolygonProjected(
    const bx::Vec3 &point,
    const std::vector<bx::Vec3> &vertices,
    const bx::Vec3 &normal
)
{
    if (vertices.size() < 3)
    {
        return false;
    }

    enum class ProjectionAxis
    {
        X,
        Y,
        Z
    };

    const float absNormalX = std::fabs(normal.x);
    const float absNormalY = std::fabs(normal.y);
    const float absNormalZ = std::fabs(normal.z);
    ProjectionAxis projectionAxis = ProjectionAxis::Z;

    if (absNormalX >= absNormalY && absNormalX >= absNormalZ)
    {
        projectionAxis = ProjectionAxis::X;
    }
    else if (absNormalY >= absNormalX && absNormalY >= absNormalZ)
    {
        projectionAxis = ProjectionAxis::Y;
    }

    auto projectVertex = [projectionAxis](const bx::Vec3 &vertex) -> bx::Vec3
    {
        if (projectionAxis == ProjectionAxis::X)
        {
            return {vertex.y, vertex.z, 0.0f};
        }

        if (projectionAxis == ProjectionAxis::Y)
        {
            return {vertex.x, vertex.z, 0.0f};
        }

        return {vertex.x, vertex.y, 0.0f};
    };

    std::vector<bx::Vec3> projectedVertices;
    projectedVertices.reserve(vertices.size());

    for (const bx::Vec3 &vertex : vertices)
    {
        projectedVertices.push_back(projectVertex(vertex));
    }

    const bx::Vec3 projectedPoint = projectVertex(point);
    return isPointInsideOutdoorPolygon(projectedPoint.x, projectedPoint.y, projectedVertices);
}
}
