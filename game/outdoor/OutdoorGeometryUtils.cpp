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

bool outdoorFaceHasInvisibleAttribute(uint32_t attributes)
{
    return hasFaceAttribute(attributes, FaceAttribute::Invisible);
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
}

bool isOutdoorWalkablePolygonType(uint8_t polygonType)
{
    return polygonType == OutdoorPolygonFloor || polygonType == OutdoorPolygonInBetweenFloorAndWall;
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
    OutdoorFaceGeometryData &geometry
)
{
    if (outdoorFaceHasInvisibleAttribute(face.attributes))
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
    const float terrainHeight = sampleOutdoorTerrainHeight(outdoorMapData, x, y);
    OutdoorSupportFloorSample bestSample = {};
    bestSample.height = terrainHeight;

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

            if (faceHeight < terrainHeight || faceHeight > z + maxRise)
            {
                continue;
            }

            if (!bestSample.fromBModel || faceHeight >= bestSample.height)
            {
                bestSample.height = faceHeight;
                bestSample.fromBModel = true;
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
}
