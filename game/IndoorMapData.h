#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorVertex
{
    int x = 0;
    int y = 0;
    int z = 0;
};

struct IndoorFace
{
    uint32_t attributes = 0;
    std::vector<uint16_t> vertexIndices;
    std::vector<int16_t> textureUs;
    std::vector<int16_t> textureVs;
    int16_t textureDeltaU = 0;
    int16_t textureDeltaV = 0;
    uint16_t textureFrameTableIndex = 0;
    uint16_t textureFrameTableCog = 0;
    uint16_t cogNumber = 0;
    uint16_t cogTriggered = 0;
    uint16_t cogTriggerType = 0;
    uint16_t lightLevel = 0;
    uint16_t roomNumber = 0;
    uint16_t roomBehindNumber = 0;
    uint8_t facetType = 0;
    std::string textureName;
    bool isPortal = false;
};

struct IndoorSector
{
    int32_t flags = 0;
    uint16_t floorCount = 0;
    uint16_t wallCount = 0;
    uint16_t ceilingCount = 0;
    int16_t portalCount = 0;
    uint16_t faceCount = 0;
    uint16_t nonBspFaceCount = 0;
    uint16_t decorationCount = 0;
    uint16_t lightCount = 0;
    int16_t waterLevel = 0;
    int16_t mistLevel = 0;
    int16_t lightDistanceMultiplier = 0;
    int16_t minAmbientLightLevel = 0;
    int16_t firstBspNode = 0;
    std::vector<uint16_t> faceIds;
    std::vector<uint16_t> lightIds;
    std::vector<uint16_t> decorationIds;
    std::vector<uint16_t> portalFaceIds;
};

struct IndoorLight
{
    int16_t x = 0;
    int16_t y = 0;
    int16_t z = 0;
    int16_t radius = 0;
    uint8_t red = 0;
    uint8_t green = 0;
    uint8_t blue = 0;
    uint8_t type = 0;
    int16_t attributes = 0;
    int16_t brightness = 0;
};

struct IndoorBspNode
{
    int16_t front = 0;
    int16_t back = 0;
    int16_t faceIdOffset = 0;
    int16_t faceCount = 0;
};

struct IndoorOutline
{
    uint16_t vertex1Id = 0;
    uint16_t vertex2Id = 0;
    uint16_t face1Id = 0;
    uint16_t face2Id = 0;
    int16_t z = 0;
    uint16_t flags = 0;
};

struct IndoorEntity
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

struct IndoorSpawn
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

struct IndoorMapData
{
    int version = 0;
    int32_t faceDataSizeBytes = 0;
    int32_t sectorDataSizeBytes = 0;
    int32_t sectorLightDataSizeBytes = 0;
    int32_t doorsDataSizeBytes = 0;
    uint32_t rawFaceCount = 0;
    std::vector<IndoorVertex> vertices;
    std::vector<IndoorFace> faces;
    std::vector<IndoorSector> sectors;
    std::vector<uint16_t> sectorData;
    std::vector<uint16_t> sectorLightData;
    std::vector<IndoorEntity> entities;
    std::vector<IndoorLight> lights;
    std::vector<IndoorBspNode> bspNodes;
    std::vector<IndoorSpawn> spawns;
    std::vector<IndoorOutline> outlines;
    uint32_t doorCount = 0;
    size_t sectorCount = 0;
    size_t spriteCount = 0;
    size_t lightCount = 0;
    size_t spawnCount = 0;
};

class IndoorMapDataLoader
{
public:
    std::optional<IndoorMapData> loadFromBytes(const std::vector<uint8_t> &bytes) const;
};
}
