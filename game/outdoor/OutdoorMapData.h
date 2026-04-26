#pragma once

#include <cstddef>
#include <cstdint>
#include <array>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorBModelVertex
{
    int x = 0;
    int y = 0;
    int z = 0;
};

struct OutdoorBspNode
{
    int16_t front = 0;
    int16_t back = 0;
    int16_t faceIdOffset = 0;
    int16_t faceCount = 0;
};

struct OutdoorBModelFace
{
    int32_t planeNormalX = 0;
    int32_t planeNormalY = 0;
    int32_t planeNormalZ = 0;
    int32_t planeDistance = 0;
    uint32_t attributes = 0;
    std::vector<uint16_t> vertexIndices;
    std::vector<int16_t> textureUs;
    std::vector<int16_t> textureVs;
    int16_t bitmapIndex = 0;
    int16_t textureDeltaU = 0;
    int16_t textureDeltaV = 0;
    uint16_t cogNumber = 0;
    uint16_t cogTriggeredNumber = 0;
    uint16_t cogTrigger = 0;
    uint16_t reserved = 0;
    uint8_t polygonType = 0;
    uint8_t shade = 0;
    uint8_t visibility = 0;
    std::string textureName;
};

struct OutdoorBModel
{
    std::string name;
    std::string secondaryName;
    int positionX = 0;
    int positionY = 0;
    int positionZ = 0;
    int minX = 0;
    int minY = 0;
    int minZ = 0;
    int maxX = 0;
    int maxY = 0;
    int maxZ = 0;
    int boundingCenterX = 0;
    int boundingCenterY = 0;
    int boundingCenterZ = 0;
    int boundingRadius = 0;
    std::vector<OutdoorBModelVertex> vertices;
    std::vector<OutdoorBModelFace> faces;
    std::vector<OutdoorBspNode> bspNodes;
};

struct OutdoorEntity
{
    uint16_t decorationListId = 0;
    uint16_t aiAttributes = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    int facing = 0;
    uint16_t eventIdPrimary = 0;
    uint16_t eventIdSecondary = 0;
    uint16_t variablePrimary = 0;
    uint16_t variableSecondary = 0;
    uint16_t specialTrigger = 0;
    std::string name;
};

struct OutdoorSpawn
{
    int x = 0;
    int y = 0;
    int z = 0;
    uint16_t radius = 0;
    uint16_t typeId = 0;
    uint16_t index = 0;
    uint16_t attributes = 0;
    uint32_t group = 0;
};

struct OutdoorMapData
{
    static constexpr int TerrainWidth = 128;
    static constexpr int TerrainHeight = 128;
    static constexpr int TerrainTileSize = 512;
    static constexpr int TerrainHeightScale = 32;

    int version = 0;
    std::string name;
    std::string fileName;
    std::string description;
    std::string skyTexture;
    std::string groundTilesetName;
    uint8_t masterTile = 0;
    std::array<uint16_t, 4> tileSetLookupIndices = {};
    std::vector<uint8_t> heightMap;
    std::vector<uint8_t> tileMap;
    std::vector<uint8_t> attributeMap;
    std::vector<uint32_t> someOtherMap;
    std::vector<uint16_t> normalMap;
    std::vector<float> normals;
    std::vector<OutdoorBModel> bmodels;
    std::vector<OutdoorEntity> entities;
    std::vector<uint16_t> decorationPidList;
    std::vector<uint32_t> decorationMap;
    std::vector<OutdoorSpawn> spawns;
    size_t terrainNormalCount = 0;
    size_t bmodelCount = 0;
    size_t entityCount = 0;
    size_t idListCount = 0;
    size_t spawnCount = 0;
    int minHeightSample = 0;
    int maxHeightSample = 0;
    size_t uniqueTileCount = 0;
};

class OutdoorMapDataLoader
{
public:
    std::optional<OutdoorMapData> loadFromBytes(const std::vector<uint8_t> &bytes) const;
};

class OutdoorMapDataWriter
{
public:
    std::optional<std::vector<uint8_t>> buildBytes(const OutdoorMapData &outdoorMapData) const;
    std::optional<std::vector<uint8_t>> patchBytes(
        const OutdoorMapData &outdoorMapData,
        const std::vector<uint8_t> &baseBytes) const;
};
}
