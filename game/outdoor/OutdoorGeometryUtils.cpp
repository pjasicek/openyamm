#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/events/EvtEnums.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr float GeometryEpsilon = 0.0001f;
constexpr uint8_t OutdoorPolygonFloor = 0x3;
constexpr uint8_t OutdoorPolygonInBetweenFloorAndWall = 0x4;
constexpr uint8_t TerrainTileBurn = 0x01;
constexpr uint8_t TerrainTileWater = 0x02;
constexpr float FloorCheckSlack = 5.0f;
constexpr float FloorSelectionHeightTolerance = 5.0f;
constexpr float TerrainSteepTileHeight = static_cast<float>(OutdoorMapData::TerrainTileSize);
constexpr float OutdoorFacePlaneScale = 65536.0f;
constexpr uint16_t OutdoorFaceReservedNotAStep = 0x0001;
constexpr float BModelGroundSupportRise = 128.0f;

bool outdoorFaceIsEthereal(uint32_t attributes)
{
    return hasFaceAttribute(attributes, FaceAttribute::Untouchable);
}

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

bool hasAuthoredPlaneNormal(const OutdoorBModelFace &face)
{
    return face.planeNormalX != 0 || face.planeNormalY != 0 || face.planeNormalZ != 0;
}

bx::Vec3 authoredPlaneNormal(const OutdoorBModelFace &face)
{
    return vecNormalize({
        static_cast<float>(face.planeNormalX) / OutdoorFacePlaneScale,
        static_cast<float>(face.planeNormalY) / OutdoorFacePlaneScale,
        static_cast<float>(face.planeNormalZ) / OutdoorFacePlaneScale
    });
}
}

bool outdoorFaceOccupiesSameGridCells(
    const OutdoorFaceGeometryData &before,
    const OutdoorFaceGeometryData &after,
    float gridMinX,
    float gridMinY,
    size_t gridWidth,
    size_t gridHeight,
    float cellSize)
{
    if (gridWidth == 0 || gridHeight == 0 || cellSize <= 0.0f)
    {
        return false;
    }

    const float gridMaxX = gridMinX + static_cast<float>(gridWidth) * cellSize;
    const float gridMaxY = gridMinY + static_cast<float>(gridHeight) * cellSize;

    if (after.minX < gridMinX || after.maxX > gridMaxX || after.minY < gridMinY || after.maxY > gridMaxY)
    {
        return false;
    }

    const auto cellIndex =
        [cellSize](float value, float gridMinimum, size_t cellCount)
        {
            return std::min(
                cellCount - 1,
                static_cast<size_t>(std::floor((value - gridMinimum) / cellSize)));
        };

    return cellIndex(before.minX, gridMinX, gridWidth) == cellIndex(after.minX, gridMinX, gridWidth)
        && cellIndex(before.maxX, gridMinX, gridWidth) == cellIndex(after.maxX, gridMinX, gridWidth)
        && cellIndex(before.minY, gridMinY, gridHeight) == cellIndex(after.minY, gridMinY, gridHeight)
        && cellIndex(before.maxY, gridMinY, gridHeight) == cellIndex(after.maxY, gridMinY, gridHeight);
}

bool isOutdoorWalkablePolygonType(uint8_t polygonType)
{
    return polygonType == OutdoorPolygonFloor || polygonType == OutdoorPolygonInBetweenFloorAndWall;
}

bool outdoorMapUsesBModelGround(const OutdoorMapData &outdoorMapData)
{
    if (!outdoorMapData.noTerrain || outdoorMapData.bmodels.empty() || outdoorMapData.heightMap.empty())
    {
        return false;
    }

    const uint8_t firstHeightSample = outdoorMapData.heightMap.front();

    for (uint8_t heightSample : outdoorMapData.heightMap)
    {
        if (heightSample != firstHeightSample)
        {
            return false;
        }
    }

    return true;
}

bx::Vec3 outdoorBModelPointToWorld(int x, int y, int z)
{
    return {
        static_cast<float>(x),
        static_cast<float>(y),
        static_cast<float>(z)
    };
}

bx::Vec3 outdoorBModelVertexToWorld(const OutdoorBModelVertex &vertex)
{
    return outdoorBModelPointToWorld(vertex.x, vertex.y, vertex.z);
}

bx::Vec3 transformOutdoorBModelPoint(
    const bx::Vec3 &point,
    const OutdoorBModelTransform &transform,
    float fraction)
{
    const float clampedFraction = std::clamp(fraction, 0.0f, 1.0f);
    const float radiansX = bx::toRad(transform.rotationDegreesX * clampedFraction);
    const float radiansY = bx::toRad(transform.rotationDegreesY * clampedFraction);
    const float radiansZ = bx::toRad(transform.rotationDegreesZ * clampedFraction);
    bx::Vec3 result = {
        point.x - transform.pivotX,
        point.y - transform.pivotY,
        point.z - transform.pivotZ
    };

    if (std::fabs(radiansX) > GeometryEpsilon)
    {
        const float cosine = std::cos(radiansX);
        const float sine = std::sin(radiansX);
        result = {result.x, result.y * cosine - result.z * sine, result.y * sine + result.z * cosine};
    }

    if (std::fabs(radiansY) > GeometryEpsilon)
    {
        const float cosine = std::cos(radiansY);
        const float sine = std::sin(radiansY);
        result = {result.x * cosine + result.z * sine, result.y, -result.x * sine + result.z * cosine};
    }

    if (std::fabs(radiansZ) > GeometryEpsilon)
    {
        const float cosine = std::cos(radiansZ);
        const float sine = std::sin(radiansZ);
        result = {result.x * cosine - result.y * sine, result.x * sine + result.y * cosine, result.z};
    }

    result.x += transform.pivotX + transform.translationX * clampedFraction;
    result.y += transform.pivotY + transform.translationY * clampedFraction;
    result.z += transform.pivotZ + transform.translationZ * clampedFraction;
    return result;
}

bx::Vec3 transformOutdoorBModelDirection(
    const bx::Vec3 &direction,
    const OutdoorBModelTransform &transform,
    float fraction)
{
    const float clampedFraction = std::clamp(fraction, 0.0f, 1.0f);
    const float radiansX = bx::toRad(transform.rotationDegreesX * clampedFraction);
    const float radiansY = bx::toRad(transform.rotationDegreesY * clampedFraction);
    const float radiansZ = bx::toRad(transform.rotationDegreesZ * clampedFraction);
    bx::Vec3 result = direction;

    if (std::fabs(radiansX) > GeometryEpsilon)
    {
        const float cosine = std::cos(radiansX);
        const float sine = std::sin(radiansX);
        result = {result.x, result.y * cosine - result.z * sine, result.y * sine + result.z * cosine};
    }

    if (std::fabs(radiansY) > GeometryEpsilon)
    {
        const float cosine = std::cos(radiansY);
        const float sine = std::sin(radiansY);
        result = {result.x * cosine + result.z * sine, result.y, -result.x * sine + result.z * cosine};
    }

    if (std::fabs(radiansZ) > GeometryEpsilon)
    {
        const float cosine = std::cos(radiansZ);
        const float sine = std::sin(radiansZ);
        result = {result.x * cosine - result.y * sine, result.x * sine + result.y * cosine, result.z};
    }

    const float length = vecLength(result);

    if (length <= GeometryEpsilon)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {result.x / length, result.y / length, result.z / length};
}

OutdoorBModel transformOutdoorBModel(
    const OutdoorBModel &bmodel,
    const OutdoorBModelTransform &transform,
    float fraction)
{
    OutdoorBModel transformed = bmodel;

    for (OutdoorBModelVertex &vertex : transformed.vertices)
    {
        const bx::Vec3 transformedPoint = transformOutdoorBModelPoint(
            {static_cast<float>(vertex.x), static_cast<float>(vertex.y), static_cast<float>(vertex.z)},
            transform,
            fraction);
        vertex.x = static_cast<int>(std::lround(transformedPoint.x));
        vertex.y = static_cast<int>(std::lround(transformedPoint.y));
        vertex.z = static_cast<int>(std::lround(transformedPoint.z));
    }

    if (!transformed.vertices.empty())
    {
        transformed.minX = transformed.maxX = transformed.vertices.front().x;
        transformed.minY = transformed.maxY = transformed.vertices.front().y;
        transformed.minZ = transformed.maxZ = transformed.vertices.front().z;

        for (const OutdoorBModelVertex &vertex : transformed.vertices)
        {
            transformed.minX = std::min(transformed.minX, vertex.x);
            transformed.maxX = std::max(transformed.maxX, vertex.x);
            transformed.minY = std::min(transformed.minY, vertex.y);
            transformed.maxY = std::max(transformed.maxY, vertex.y);
            transformed.minZ = std::min(transformed.minZ, vertex.z);
            transformed.maxZ = std::max(transformed.maxZ, vertex.z);
        }

        transformed.boundingCenterX = (transformed.minX + transformed.maxX) / 2;
        transformed.boundingCenterY = (transformed.minY + transformed.maxY) / 2;
        transformed.boundingCenterZ = (transformed.minZ + transformed.maxZ) / 2;
        transformed.positionX = transformed.boundingCenterX;
        transformed.positionY = transformed.boundingCenterY;
        transformed.positionZ = transformed.boundingCenterZ;
    }

    OutdoorBModelTransform normalTransform = transform;
    normalTransform.translationX = 0.0f;
    normalTransform.translationY = 0.0f;
    normalTransform.translationZ = 0.0f;
    normalTransform.pivotX = 0.0f;
    normalTransform.pivotY = 0.0f;
    normalTransform.pivotZ = 0.0f;

    for (OutdoorBModelFace &face : transformed.faces)
    {
        const bx::Vec3 transformedNormal = transformOutdoorBModelPoint(
            {
                static_cast<float>(face.planeNormalX) / 65536.0f,
                static_cast<float>(face.planeNormalY) / 65536.0f,
                static_cast<float>(face.planeNormalZ) / 65536.0f
            },
            normalTransform,
            fraction);
        face.planeNormalX = static_cast<int32_t>(std::lround(transformedNormal.x * 65536.0f));
        face.planeNormalY = static_cast<int32_t>(std::lround(transformedNormal.y * 65536.0f));
        face.planeNormalZ = static_cast<int32_t>(std::lround(transformedNormal.z * 65536.0f));
    }

    return transformed;
}

float sampleOutdoorTerrainHeight(const OutdoorMapData &outdoorMapData, float x, float y)
{
    const float gridX = outdoorWorldToGridXFloat(x);
    const float gridY = outdoorWorldToGridYFloat(y);
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

float sampleOutdoorRenderedTerrainHeight(const OutdoorMapData &outdoorMapData, float x, float y)
{
    const float gridX = outdoorWorldToGridXFloat(x);
    const float gridY = outdoorWorldToGridYFloat(y);
    const int sampleX0 = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int sampleY0 = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    const int sampleX1 = sampleX0 + 1;
    const int sampleY1 = sampleY0 + 1;
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

    float heightSample = 0.0f;

    if (fractionX + fractionY <= 1.0f)
    {
        heightSample =
            height00
            + (height10 - height00) * fractionX
            + (height01 - height00) * fractionY;
    }
    else
    {
        heightSample =
            height11
            + (height10 - height11) * (1.0f - fractionY)
            + (height01 - height11) * (1.0f - fractionX);
    }

    return heightSample * static_cast<float>(OutdoorMapData::TerrainHeightScale);
}

bx::Vec3 sampleOutdoorRenderedTerrainNormal(const OutdoorMapData &outdoorMapData, float x, float y)
{
    const float gridX = outdoorWorldToGridXFloat(x);
    const float gridY = outdoorWorldToGridYFloat(y);
    const int sampleX0 = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int sampleY0 = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    const int sampleX1 = sampleX0 + 1;
    const int sampleY1 = sampleY0 + 1;
    const float fractionX = std::clamp(gridX - static_cast<float>(sampleX0), 0.0f, 1.0f);
    const float fractionY = std::clamp(gridY - static_cast<float>(sampleY0), 0.0f, 1.0f);
    const float tileSize = static_cast<float>(OutdoorMapData::TerrainTileSize);

    const size_t index00 = static_cast<size_t>(sampleY0 * OutdoorMapData::TerrainWidth + sampleX0);
    const size_t index10 = static_cast<size_t>(sampleY0 * OutdoorMapData::TerrainWidth + sampleX1);
    const size_t index01 = static_cast<size_t>(sampleY1 * OutdoorMapData::TerrainWidth + sampleX0);
    const size_t index11 = static_cast<size_t>(sampleY1 * OutdoorMapData::TerrainWidth + sampleX1);

    const float height00 =
        static_cast<float>(outdoorMapData.heightMap[index00] * OutdoorMapData::TerrainHeightScale);
    const float height10 =
        static_cast<float>(outdoorMapData.heightMap[index10] * OutdoorMapData::TerrainHeightScale);
    const float height01 =
        static_cast<float>(outdoorMapData.heightMap[index01] * OutdoorMapData::TerrainHeightScale);
    const float height11 =
        static_cast<float>(outdoorMapData.heightMap[index11] * OutdoorMapData::TerrainHeightScale);

    if (fractionX + fractionY <= 1.0f)
    {
        return vecNormalize({
            (height00 - height10) / tileSize,
            (height01 - height00) / tileSize,
            1.0f
        });
    }

    return vecNormalize({
        (height01 - height11) / tileSize,
        (height11 - height10) / tileSize,
        1.0f
    });
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

bool outdoorTerrainSlopeTooHigh(const OutdoorMapData &outdoorMapData, float x, float y)
{
    const float gridXFloat = outdoorWorldToGridXFloat(x);
    const float gridYFloat = outdoorWorldToGridYFloat(y);
    const int gridX = std::clamp(static_cast<int>(std::floor(gridXFloat)), 0, OutdoorMapData::TerrainWidth - 2);
    const int gridY = std::clamp(static_cast<int>(std::floor(gridYFloat)), 0, OutdoorMapData::TerrainHeight - 2);
    const size_t index00 = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
    const size_t index01 = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
    const size_t index10 = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + (gridX + 1));
    const size_t index11 = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + (gridX + 1));
    const int z00 = static_cast<int>(outdoorMapData.heightMap[index00]) * OutdoorMapData::TerrainHeightScale;
    const int z01 = static_cast<int>(outdoorMapData.heightMap[index01]) * OutdoorMapData::TerrainHeightScale;
    const int z10 = static_cast<int>(outdoorMapData.heightMap[index10]) * OutdoorMapData::TerrainHeightScale;
    const int z11 = static_cast<int>(outdoorMapData.heightMap[index11]) * OutdoorMapData::TerrainHeightScale;
    const int minZ = std::min({z00, z01, z10, z11});
    const int maxZ = std::max({z00, z01, z10, z11});
    return static_cast<float>(maxZ - minZ) > TerrainSteepTileHeight;
}

uint8_t sampleOutdoorTerrainTileAttributes(const OutdoorMapData &outdoorMapData, float x, float y)
{
    if (outdoorMapData.attributeMap.empty())
    {
        return 0;
    }

    const float gridX = outdoorWorldToGridXFloat(x);
    const float gridY = outdoorWorldToGridYFloat(y);
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
    OutdoorFaceGeometryData &geometry,
    bool includeEtherealFaces
)
{
    if (!includeEtherealFaces && outdoorFaceIsEthereal(face.attributes))
    {
        return false;
    }

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
    geometry.notAStep = (face.reserved & OutdoorFaceReservedNotAStep) != 0;
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
    geometry.normal = hasAuthoredPlaneNormal(face) ? authoredPlaneNormal(face) : vecNormalize(vecCross(edge1, edge2));
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

    auto projectedX = [projectionAxis](const bx::Vec3 &vertex) -> float
    {
        if (projectionAxis == ProjectionAxis::X)
        {
            return vertex.y;
        }

        if (projectionAxis == ProjectionAxis::Y)
        {
            return vertex.x;
        }

        return vertex.x;
    };
    auto projectedY = [projectionAxis](const bx::Vec3 &vertex) -> float
    {
        if (projectionAxis == ProjectionAxis::X || projectionAxis == ProjectionAxis::Y)
        {
            return vertex.z;
        }

        return vertex.y;
    };

    const float x = projectedX(point);
    const float y = projectedY(point);
    bool isInside = false;
    size_t previousIndex = vertices.size() - 1;

    for (size_t currentIndex = 0; currentIndex < vertices.size(); ++currentIndex)
    {
        const float currentX = projectedX(vertices[currentIndex]);
        const float currentY = projectedY(vertices[currentIndex]);
        const float previousX = projectedX(vertices[previousIndex]);
        const float previousY = projectedY(vertices[previousIndex]);
        const bool intersects =
            ((currentY > y) != (previousY > y))
            && (x < (previousX - currentX) * (y - currentY)
                    / ((previousY - currentY) + GeometryEpsilon)
                + currentX);

        if (intersects)
        {
            isInside = !isInside;
        }

        previousIndex = currentIndex;
    }

    return isInside;
}

bool intersectOutdoorSegmentWithFace(
    const OutdoorFaceGeometryData &geometry,
    const bx::Vec3 &segmentStart,
    const bx::Vec3 &segmentEnd,
    float &intersectionFactor,
    bx::Vec3 &intersectionPoint
)
{
    if (!geometry.hasPlane || geometry.vertices.size() < 3)
    {
        return false;
    }

    if (std::max(segmentStart.x, segmentEnd.x) < geometry.minX
        || std::min(segmentStart.x, segmentEnd.x) > geometry.maxX
        || std::max(segmentStart.y, segmentEnd.y) < geometry.minY
        || std::min(segmentStart.y, segmentEnd.y) > geometry.maxY
        || std::max(segmentStart.z, segmentEnd.z) < geometry.minZ
        || std::min(segmentStart.z, segmentEnd.z) > geometry.maxZ)
    {
        return false;
    }

    const bx::Vec3 segment = vecSubtract(segmentEnd, segmentStart);
    const float denominator = vecDot(geometry.normal, segment);

    if (std::fabs(denominator) <= GeometryEpsilon)
    {
        return false;
    }

    const bx::Vec3 startToPlane = vecSubtract(geometry.vertices[0], segmentStart);
    const float factor = vecDot(geometry.normal, startToPlane) / denominator;

    if (factor < 0.0f || factor > 1.0f)
    {
        return false;
    }

    const bx::Vec3 candidatePoint = {
        segmentStart.x + segment.x * factor,
        segmentStart.y + segment.y * factor,
        segmentStart.z + segment.z * factor
    };

    if (!isPointInsideOutdoorPolygonProjected(candidatePoint, geometry.vertices, geometry.normal))
    {
        return false;
    }

    intersectionFactor = factor;
    intersectionPoint = candidatePoint;
    return true;
}

float calculateOutdoorFaceHeight(const OutdoorFaceGeometryData &geometry, float x, float y)
{
    if (geometry.polygonType == OutdoorPolygonFloor)
    {
        return geometry.vertices[0].z;
    }

    if (!geometry.hasPlane || std::fabs(geometry.normal.z) <= GeometryEpsilon)
    {
        return geometry.minZ;
    }

    return geometry.vertices[0].z
        - (geometry.normal.x * (x - geometry.vertices[0].x) + geometry.normal.y * (y - geometry.vertices[0].y))
            / geometry.normal.z;
}

bool isPointInsideOrNearOutdoorPolygon(float x, float y, const std::vector<bx::Vec3> &vertices, float slack)
{
    if (isPointInsideOutdoorPolygon(x, y, vertices))
    {
        return true;
    }

    const float slackSquared = slack * slack;

    for (size_t index = 0; index < vertices.size(); ++index)
    {
        const size_t nextIndex = (index + 1) % vertices.size();
        const float segmentX = vertices[nextIndex].x - vertices[index].x;
        const float segmentY = vertices[nextIndex].y - vertices[index].y;
        const float segmentLengthSquared = segmentX * segmentX + segmentY * segmentY;

        if (segmentLengthSquared <= GeometryEpsilon)
        {
            continue;
        }

        const float projection =
            ((x - vertices[index].x) * segmentX + (y - vertices[index].y) * segmentY) / segmentLengthSquared;
        const float clampedProjection = std::clamp(projection, 0.0f, 1.0f);
        const float closestX = vertices[index].x + segmentX * clampedProjection;
        const float closestY = vertices[index].y + segmentY * clampedProjection;
        const float deltaX = x - closestX;
        const float deltaY = y - closestY;

        if ((deltaX * deltaX + deltaY * deltaY) <= slackSquared)
        {
            return true;
        }
    }

    return false;
}

bool isOutdoorCylinderBlockedByFace(
    const OutdoorFaceGeometryData &geometry,
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

    return isPointInsideOutdoorPolygonProjected(projectedPoint, geometry.vertices, geometry.normal);
}

OutdoorSupportFloorSample sampleOutdoorSupportFloor(
    const OutdoorMapData &outdoorMapData,
    float x,
    float y,
    float z,
    float maxRise,
    float xySlack
)
{
    const bool bModelGround = outdoorMapUsesBModelGround(outdoorMapData);
    const float effectiveMaxRise = bModelGround ? std::max(maxRise, BModelGroundSupportRise) : maxRise;
    const float terrainHeight = bModelGround ? std::numeric_limits<float>::lowest()
                                             : sampleOutdoorTerrainHeight(outdoorMapData, x, y);
    OutdoorSupportFloorSample bestSample = {};
    bestSample.height = bModelGround ? z : terrainHeight;
    bestSample.hasFloor = !bModelGround;

    for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bModel = outdoorMapData.bmodels[bModelIndex];

        for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
        {
            OutdoorFaceGeometryData geometry = {};

            if (!buildOutdoorFaceGeometry(bModel, bModelIndex, bModel.faces[faceIndex], faceIndex, geometry)
                || !geometry.isWalkable
                || x < geometry.minX
                || x > geometry.maxX
                || y < geometry.minY
                || y > geometry.maxY
                || !isPointInsideOrNearOutdoorPolygon(x, y, geometry.vertices, xySlack))
            {
                continue;
            }

            const float faceHeight = calculateOutdoorFaceHeight(geometry, x, y);

            if (faceHeight < terrainHeight
                || faceHeight > z + effectiveMaxRise
                || (geometry.notAStep && faceHeight > z + maxRise))
            {
                continue;
            }

            if (!bestSample.hasFloor || !bestSample.fromBModel || faceHeight >= bestSample.height)
            {
                bestSample.height = faceHeight;
                bestSample.fromBModel = true;
                bestSample.hasFloor = true;
                bestSample.bModelIndex = bModelIndex;
                bestSample.faceIndex = faceIndex;
            }
        }
    }

    return bestSample;
}

float sampleOutdoorSupportFloorHeight(const OutdoorMapData &outdoorMapData, float x, float y, float z)
{
    return sampleOutdoorSupportFloor(
        outdoorMapData,
        x,
        y,
        z,
        FloorSelectionHeightTolerance,
        FloorCheckSlack).height;
}

float sampleOutdoorPlacementFloorHeight(const OutdoorMapData &outdoorMapData, float x, float y, float z)
{
    return sampleOutdoorSupportFloor(
        outdoorMapData,
        x,
        y,
        z,
        std::numeric_limits<float>::max(),
        FloorCheckSlack).height;
}

float sampleOutdoorActorPlacementFloorHeight(
    const OutdoorMapData &outdoorMapData,
    float x,
    float y,
    float z,
    float xySlack)
{
    const OutdoorSupportFloorSample support = sampleOutdoorSupportFloor(
        outdoorMapData,
        x,
        y,
        z,
        FloorSelectionHeightTolerance,
        xySlack);

    if (outdoorMapUsesBModelGround(outdoorMapData))
    {
        return support.hasFloor ? support.height : z;
    }

    const float terrainHeight = sampleOutdoorRenderedTerrainHeight(outdoorMapData, x, y);

    if (support.fromBModel)
    {
        return std::max(terrainHeight, support.height);
    }

    return terrainHeight;
}

float sampleOutdoorActorPlacementFloorHeight(const OutdoorMapData &outdoorMapData, float x, float y, float z)
{
    return sampleOutdoorActorPlacementFloorHeight(outdoorMapData, x, y, z, FloorCheckSlack);
}
}
