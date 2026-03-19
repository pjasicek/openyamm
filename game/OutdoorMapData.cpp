#include "game/OutdoorMapData.h"
#include "game/BinaryReader.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t VersionOffset = 0x40;
constexpr size_t VersionFieldSize = 16;
constexpr size_t MasterTileOffset = 0x5f;
constexpr size_t TileSetLookupOffset = 0xa0;
constexpr size_t TerrainSectionOffset = 0xb0;
constexpr size_t TerrainSectionOffsetV8 = 0xb4;
constexpr size_t TerrainMapSize = 0x4000;
constexpr size_t CMap1Size = 0x20000;
constexpr size_t CMap2Size = 0x10000;
constexpr size_t BModelHeaderSize = 0xbc;
constexpr size_t BModelVertexSize = 12;
constexpr size_t BModelFaceSize = 0x134;
constexpr size_t BModelFaceFlagsSize = 2;
constexpr size_t BModelTextureNameSize = 10;
constexpr size_t BModelBspNodeSize = 8;
constexpr size_t BModelFaceVertexIndicesOffset = 0x20;
constexpr size_t BModelFaceTextureUOffset = 0x48;
constexpr size_t BModelFaceTextureVOffset = 0x70;
constexpr size_t BModelFaceAttributesOffset = 0x1c;
constexpr size_t BModelFaceBitmapIndexOffset = 0x110;
constexpr size_t BModelFaceTextureDeltaUOffset = 0x112;
constexpr size_t BModelFaceTextureDeltaVOffset = 0x114;
constexpr size_t BModelFaceCogNumberOffset = 0x122;
constexpr size_t BModelFaceCogTriggeredNumberOffset = 0x124;
constexpr size_t BModelFaceCogTriggerOffset = 0x126;
constexpr size_t BModelFaceReservedOffset = 0x128;
constexpr size_t BModelFaceNumVerticesOffset = 0x12e;
constexpr size_t BModelFacePolygonTypeOffset = 0x12f;
constexpr size_t BModelFaceShadeOffset = 0x130;
constexpr size_t BModelFaceVisibilityOffset = 0x131;
constexpr size_t EntityNameSize = 0x20;
constexpr size_t Version6EntitySize = 0x1c;
constexpr size_t Version7EntitySize = 0x20;
constexpr size_t Version6SpawnSize = 0x14;
constexpr size_t Version7SpawnSize = 0x18;
constexpr char Version6Tag[] = "MM6 Outdoor v1.11";
constexpr char Version7Tag[] = "MM6 Outdoor v7.00";

bool advanceOffset(size_t &offset, size_t byteCount, size_t totalSize)
{
    if (byteCount > (totalSize - offset))
    {
        return false;
    }

    offset += byteCount;
    return true;
}

std::optional<int> detectVersion(const ByteReader &reader)
{
    if (reader.matchesText(VersionOffset, Version6Tag))
    {
        return 6;
    }

    if (reader.matchesText(VersionOffset, Version7Tag))
    {
        return 7;
    }

    if (reader.isZeroBlock(VersionOffset, VersionFieldSize))
    {
        return 8;
    }

    return std::nullopt;
}

bool isOutdoorMapData(const std::vector<uint8_t> &bytes)
{
    const ByteReader reader(bytes);
    return detectVersion(reader).has_value();
}

std::string readCString(const ByteReader &reader, size_t offset, size_t maxLength)
{
    return reader.readFixedString(offset, maxLength);
}

std::string readFixedString(const ByteReader &reader, size_t offset, size_t maxLength)
{
    return readCString(reader, offset, maxLength);
}
}

std::optional<OutdoorMapData> OutdoorMapDataLoader::loadFromBytes(const std::vector<uint8_t> &bytes) const
{
    if (!isOutdoorMapData(bytes))
    {
        return std::nullopt;
    }

    const ByteReader reader(bytes);
    const std::optional<int> version = detectVersion(reader);

    if (!version)
    {
        return std::nullopt;
    }

    OutdoorMapData outdoorMapData = {};
    outdoorMapData.version = *version;
    outdoorMapData.name = readCString(reader, 0x00, 32);
    outdoorMapData.fileName = readCString(reader, 0x20, 32);
    outdoorMapData.description = readCString(reader, 0x40, 32);
    outdoorMapData.skyTexture = readCString(reader, 0x60, 32);
    outdoorMapData.groundTilesetName = readCString(reader, 0x80, 32);

    if (!reader.readUInt8(MasterTileOffset, outdoorMapData.masterTile))
    {
        return std::nullopt;
    }

    for (size_t lookupIndex = 0; lookupIndex < outdoorMapData.tileSetLookupIndices.size(); ++lookupIndex)
    {
        int tileSetLookupValue = 0;

        if (!reader.readInt32(TileSetLookupOffset + (lookupIndex * sizeof(int32_t)), tileSetLookupValue))
        {
            return std::nullopt;
        }

        outdoorMapData.tileSetLookupIndices[lookupIndex] =
            static_cast<uint16_t>((static_cast<uint32_t>(tileSetLookupValue) >> 16) & 0xffff);
    }

    size_t offset = (*version == 8) ? TerrainSectionOffsetV8 : TerrainSectionOffset;

    if (!reader.readBytes(offset, TerrainMapSize, outdoorMapData.heightMap))
    {
        return std::nullopt;
    }

    if (!advanceOffset(offset, TerrainMapSize, reader.size()))
    {
        return std::nullopt;
    }

    if (!reader.readBytes(offset, TerrainMapSize, outdoorMapData.tileMap))
    {
        return std::nullopt;
    }

    if (!advanceOffset(offset, TerrainMapSize, reader.size()))
    {
        return std::nullopt;
    }

    if (!reader.readBytes(offset, TerrainMapSize, outdoorMapData.attributeMap))
    {
        return std::nullopt;
    }

    if (!advanceOffset(offset, TerrainMapSize, reader.size()))
    {
        return std::nullopt;
    }

    if (*version > 6)
    {
        int terrainNormalCount = 0;

        if (!reader.readInt32(offset, terrainNormalCount) || terrainNormalCount < 0)
        {
            return std::nullopt;
        }

        outdoorMapData.terrainNormalCount = static_cast<size_t>(terrainNormalCount);

        if (!advanceOffset(offset, sizeof(int32_t), reader.size()))
        {
            return std::nullopt;
        }

        outdoorMapData.someOtherMap.reserve(CMap1Size / sizeof(uint32_t));

        for (size_t mapOffset = 0; mapOffset < CMap1Size; mapOffset += sizeof(uint32_t))
        {
            uint32_t value = 0;

            if (!reader.readUInt32(offset + mapOffset, value))
            {
                return std::nullopt;
            }

            outdoorMapData.someOtherMap.push_back(value);
        }

        if (!advanceOffset(offset, CMap1Size, reader.size()))
        {
            return std::nullopt;
        }

        outdoorMapData.normalMap.reserve(CMap2Size / sizeof(uint16_t));

        for (size_t mapOffset = 0; mapOffset < CMap2Size; mapOffset += sizeof(uint16_t))
        {
            uint16_t value = 0;

            if (!reader.readUInt16(offset + mapOffset, value))
            {
                return std::nullopt;
            }

            outdoorMapData.normalMap.push_back(value);
        }

        if (!advanceOffset(offset, CMap2Size, reader.size()))
        {
            return std::nullopt;
        }

        outdoorMapData.normals.reserve(outdoorMapData.terrainNormalCount * 3);

        for (size_t normalIndex = 0; normalIndex < outdoorMapData.terrainNormalCount * 3; ++normalIndex)
        {
            float value = 0.0f;

            if (!reader.canRead(offset + normalIndex * sizeof(float), sizeof(float)))
            {
                return std::nullopt;
            }

            std::memcpy(&value, bytes.data() + offset + normalIndex * sizeof(float), sizeof(float));
            outdoorMapData.normals.push_back(value);
        }

        if (!advanceOffset(offset, outdoorMapData.terrainNormalCount * 12, reader.size()))
        {
            return std::nullopt;
        }
    }

    int bmodelCount = 0;

    if (!reader.readInt32(offset, bmodelCount) || bmodelCount < 0)
    {
        return std::nullopt;
    }

    outdoorMapData.bmodelCount = static_cast<size_t>(bmodelCount);

    if (!advanceOffset(offset, sizeof(int32_t), reader.size()))
    {
        return std::nullopt;
    }

    const size_t bmodelHeadersOffset = offset;

    if (!advanceOffset(offset, outdoorMapData.bmodelCount * BModelHeaderSize, reader.size()))
    {
        return std::nullopt;
    }

    for (size_t index = 0; index < outdoorMapData.bmodelCount; ++index)
    {
        const size_t headerOffset = bmodelHeadersOffset + (index * BModelHeaderSize);
        int vertexCount = 0;
        int faceCount = 0;
        int bspNodeCount = 0;

        if (!reader.readInt32(headerOffset + 0x44, vertexCount) || vertexCount < 0)
        {
            return std::nullopt;
        }

        if (!reader.readInt32(headerOffset + 0x4c, faceCount) || faceCount < 0)
        {
            return std::nullopt;
        }

        if (!reader.readInt32(headerOffset + 0x5c, bspNodeCount) || bspNodeCount < 0)
        {
            return std::nullopt;
        }

        OutdoorBModel bmodel = {};
        bmodel.vertices.reserve(static_cast<size_t>(vertexCount));
        bmodel.faces.reserve(static_cast<size_t>(faceCount));

        bmodel.name = readCString(reader, headerOffset + 0x00, 0x20);
        bmodel.secondaryName = readCString(reader, headerOffset + 0x20, 0x20);
        reader.readInt32(headerOffset + 0x68, bmodel.positionX);
        reader.readInt32(headerOffset + 0x6c, bmodel.positionY);
        reader.readInt32(headerOffset + 0x70, bmodel.positionZ);
        reader.readInt32(headerOffset + 0x74, bmodel.minX);
        reader.readInt32(headerOffset + 0x78, bmodel.minY);
        reader.readInt32(headerOffset + 0x7c, bmodel.minZ);
        reader.readInt32(headerOffset + 0x80, bmodel.maxX);
        reader.readInt32(headerOffset + 0x84, bmodel.maxY);
        reader.readInt32(headerOffset + 0x88, bmodel.maxZ);
        reader.readInt32(headerOffset + 0xa8, bmodel.boundingCenterX);
        reader.readInt32(headerOffset + 0xac, bmodel.boundingCenterY);
        reader.readInt32(headerOffset + 0xb0, bmodel.boundingCenterZ);
        reader.readInt32(headerOffset + 0xb4, bmodel.boundingRadius);

        if (bmodel.name.empty() && vertexCount > 0 && faceCount > 0)
        {
            // Some outdoor models do not appear to use a stable internal name.
        }

        for (int vertexIndex = 0; vertexIndex < vertexCount; ++vertexIndex)
        {
            const size_t vertexOffset = offset + static_cast<size_t>(vertexIndex) * BModelVertexSize;
            int vertexX = 0;
            int vertexY = 0;
            int vertexZ = 0;

            if (!reader.readInt32(vertexOffset + 0, vertexX)
                || !reader.readInt32(vertexOffset + 4, vertexY)
                || !reader.readInt32(vertexOffset + 8, vertexZ))
            {
                return std::nullopt;
            }

            OutdoorBModelVertex vertex = {};
            vertex.x = vertexX;
            vertex.y = vertexY;
            vertex.z = vertexZ;
            bmodel.vertices.push_back(vertex);
        }

        if (!advanceOffset(offset, static_cast<size_t>(vertexCount) * BModelVertexSize, reader.size()))
        {
            return std::nullopt;
        }

        const size_t facesOffset = offset;
        const size_t faceFlagsOffset = facesOffset + static_cast<size_t>(faceCount) * BModelFaceSize;
        const size_t faceTextureNamesOffset =
            faceFlagsOffset + static_cast<size_t>(faceCount) * BModelFaceFlagsSize;

        for (int faceIndex = 0; faceIndex < faceCount; ++faceIndex)
        {
            const size_t faceOffset = facesOffset + static_cast<size_t>(faceIndex) * BModelFaceSize;
            uint8_t numVertices = 0;

            if (!reader.readUInt8(faceOffset + BModelFaceNumVerticesOffset, numVertices))
            {
                return std::nullopt;
            }

            if (numVertices < 2 || numVertices > 20)
            {
                continue;
            }

            OutdoorBModelFace face = {};
            face.vertexIndices.reserve(numVertices);
            face.textureUs.reserve(numVertices);
            face.textureVs.reserve(numVertices);

            if (!reader.readUInt32(faceOffset + BModelFaceAttributesOffset, face.attributes)
                || !reader.readInt16(faceOffset + BModelFaceBitmapIndexOffset, face.bitmapIndex)
                || !reader.readInt16(faceOffset + BModelFaceTextureDeltaUOffset, face.textureDeltaU)
                || !reader.readInt16(faceOffset + BModelFaceTextureDeltaVOffset, face.textureDeltaV))
            {
                return std::nullopt;
            }

            if (!reader.readUInt16(faceOffset + BModelFaceCogNumberOffset, face.cogNumber)
                || !reader.readUInt16(faceOffset + BModelFaceCogTriggeredNumberOffset, face.cogTriggeredNumber)
                || !reader.readUInt16(faceOffset + BModelFaceCogTriggerOffset, face.cogTrigger)
                || !reader.readUInt16(faceOffset + BModelFaceReservedOffset, face.reserved)
                || !reader.readUInt8(faceOffset + BModelFacePolygonTypeOffset, face.polygonType)
                || !reader.readUInt8(faceOffset + BModelFaceShadeOffset, face.shade)
                || !reader.readUInt8(faceOffset + BModelFaceVisibilityOffset, face.visibility))
            {
                return std::nullopt;
            }

            for (uint8_t faceVertexIndex = 0; faceVertexIndex < numVertices; ++faceVertexIndex)
            {
                const size_t vertexIdOffset =
                    faceOffset + BModelFaceVertexIndicesOffset
                    + static_cast<size_t>(faceVertexIndex) * sizeof(uint16_t);
                uint16_t vertexId = 0;

                if (!reader.readUInt16(vertexIdOffset, vertexId))
                {
                    return std::nullopt;
                }

                if (vertexId >= bmodel.vertices.size())
                {
                    face.vertexIndices.clear();
                    break;
                }

                face.vertexIndices.push_back(vertexId);

                const size_t textureUOffset =
                    faceOffset + BModelFaceTextureUOffset
                    + static_cast<size_t>(faceVertexIndex) * sizeof(int16_t);
                const size_t textureVOffset =
                    faceOffset + BModelFaceTextureVOffset
                    + static_cast<size_t>(faceVertexIndex) * sizeof(int16_t);
                int16_t textureU = 0;
                int16_t textureV = 0;

                if (!reader.readInt16(textureUOffset, textureU) || !reader.readInt16(textureVOffset, textureV))
                {
                    return std::nullopt;
                }

                face.textureUs.push_back(textureU);
                face.textureVs.push_back(textureV);
            }

            face.textureName = readCString(
                reader,
                faceTextureNamesOffset + static_cast<size_t>(faceIndex) * BModelTextureNameSize,
                BModelTextureNameSize
            );

            if (face.vertexIndices.size() >= 2)
            {
                bmodel.faces.push_back(face);
            }
        }

        if (!advanceOffset(offset, static_cast<size_t>(faceCount) * BModelFaceSize, reader.size()))
        {
            return std::nullopt;
        }

        if (!advanceOffset(offset, static_cast<size_t>(faceCount) * BModelFaceFlagsSize, reader.size()))
        {
            return std::nullopt;
        }

        if (!advanceOffset(offset, static_cast<size_t>(faceCount) * BModelTextureNameSize, reader.size()))
        {
            return std::nullopt;
        }

        bmodel.bspNodes.reserve(static_cast<size_t>(bspNodeCount));

        for (int nodeIndex = 0; nodeIndex < bspNodeCount; ++nodeIndex)
        {
            const size_t nodeOffset = offset + static_cast<size_t>(nodeIndex) * BModelBspNodeSize;
            OutdoorBspNode node = {};
            reader.readInt16(nodeOffset + 0x00, node.front);
            reader.readInt16(nodeOffset + 0x02, node.back);
            reader.readInt16(nodeOffset + 0x04, node.faceIdOffset);
            reader.readInt16(nodeOffset + 0x06, node.faceCount);
            bmodel.bspNodes.push_back(node);
        }

        if (!advanceOffset(offset, static_cast<size_t>(bspNodeCount) * BModelBspNodeSize, reader.size()))
        {
            return std::nullopt;
        }

        outdoorMapData.bmodels.push_back(std::move(bmodel));
    }

    int entityCount = 0;

    if (!reader.readInt32(offset, entityCount) || entityCount < 0)
    {
        return std::nullopt;
    }

    outdoorMapData.entityCount = static_cast<size_t>(entityCount);

    if (!advanceOffset(offset, sizeof(int32_t), reader.size()))
    {
        return std::nullopt;
    }

    const size_t entitySize = (*version == 6) ? Version6EntitySize : Version7EntitySize;
    const size_t entityDataOffset = offset;

    if (!advanceOffset(offset, outdoorMapData.entityCount * entitySize, reader.size()))
    {
        return std::nullopt;
    }

    const size_t entityNamesOffset = offset;

    if (!advanceOffset(offset, outdoorMapData.entityCount * EntityNameSize, reader.size()))
    {
        return std::nullopt;
    }

    outdoorMapData.entities.reserve(outdoorMapData.entityCount);

    for (size_t entityIndex = 0; entityIndex < outdoorMapData.entityCount; ++entityIndex)
    {
        const size_t entityOffset = entityDataOffset + entityIndex * entitySize;
        OutdoorEntity entity = {};
        int coordinateX = 0;
        int coordinateY = 0;
        int coordinateZ = 0;
        int facing = 0;

        if (!reader.readUInt16(entityOffset + 0x00, entity.decorationListId)
            || !reader.readUInt16(entityOffset + 0x02, entity.aiAttributes)
            || !reader.readInt32(entityOffset + 0x04, coordinateX)
            || !reader.readInt32(entityOffset + 0x08, coordinateY)
            || !reader.readInt32(entityOffset + 0x0c, coordinateZ)
            || !reader.readInt32(entityOffset + 0x10, facing)
            || !reader.readUInt16(entityOffset + 0x14, entity.eventIdPrimary)
            || !reader.readUInt16(entityOffset + 0x16, entity.eventIdSecondary)
            || !reader.readUInt16(entityOffset + 0x18, entity.variablePrimary)
            || !reader.readUInt16(entityOffset + 0x1a, entity.variableSecondary))
        {
            return std::nullopt;
        }

        entity.x = coordinateX;
        entity.y = coordinateY;
        entity.z = coordinateZ;
        entity.facing = facing;

        if (*version > 6)
        {
            if (!reader.readUInt16(entityOffset + 0x1c, entity.specialTrigger))
            {
                return std::nullopt;
            }
        }

        entity.name = readFixedString(reader, entityNamesOffset + entityIndex * EntityNameSize, EntityNameSize);
        outdoorMapData.entities.push_back(entity);
    }

    int idListCount = 0;

    if (!reader.readInt32(offset, idListCount) || idListCount < 0)
    {
        return std::nullopt;
    }

    outdoorMapData.idListCount = static_cast<size_t>(idListCount);

    if (!advanceOffset(offset, sizeof(int32_t), reader.size()))
    {
        return std::nullopt;
    }

    if (!advanceOffset(offset, outdoorMapData.idListCount * sizeof(uint16_t), reader.size()))
    {
        return std::nullopt;
    }

    const size_t decorationMapOffset = offset;

    outdoorMapData.decorationPidList.reserve(outdoorMapData.idListCount);

    for (size_t decorationIndex = 0; decorationIndex < outdoorMapData.idListCount; ++decorationIndex)
    {
        uint16_t value = 0;

        if (!reader.readUInt16(offset - outdoorMapData.idListCount * sizeof(uint16_t) + decorationIndex * sizeof(uint16_t), value))
        {
            return std::nullopt;
        }

        outdoorMapData.decorationPidList.push_back(value);
    }

    outdoorMapData.decorationMap.reserve(TerrainMapSize);

    for (size_t cellIndex = 0; cellIndex < TerrainMapSize; ++cellIndex)
    {
        uint32_t value = 0;

        if (!reader.readUInt32(decorationMapOffset + cellIndex * sizeof(uint32_t), value))
        {
            return std::nullopt;
        }

        outdoorMapData.decorationMap.push_back(value);
    }

    if (!advanceOffset(offset, TerrainMapSize * sizeof(uint32_t), reader.size()))
    {
        return std::nullopt;
    }

    int spawnCount = 0;

    if (!reader.readInt32(offset, spawnCount) || spawnCount < 0)
    {
        return std::nullopt;
    }

    outdoorMapData.spawnCount = static_cast<size_t>(spawnCount);

    if (!advanceOffset(offset, sizeof(int32_t), reader.size()))
    {
        return std::nullopt;
    }

    const size_t spawnSize = (*version == 6) ? Version6SpawnSize : Version7SpawnSize;
    const size_t spawnDataOffset = offset;

    if (!advanceOffset(offset, outdoorMapData.spawnCount * spawnSize, reader.size()))
    {
        return std::nullopt;
    }

    outdoorMapData.spawns.reserve(outdoorMapData.spawnCount);

    for (size_t spawnIndex = 0; spawnIndex < outdoorMapData.spawnCount; ++spawnIndex)
    {
        const size_t spawnOffset = spawnDataOffset + spawnIndex * spawnSize;
        OutdoorSpawn spawn = {};
        int coordinateX = 0;
        int coordinateY = 0;
        int coordinateZ = 0;

        if (!reader.readInt32(spawnOffset + 0x00, coordinateX)
            || !reader.readInt32(spawnOffset + 0x04, coordinateY)
            || !reader.readInt32(spawnOffset + 0x08, coordinateZ)
            || !reader.readUInt16(spawnOffset + 0x0c, spawn.radius)
            || !reader.readUInt16(spawnOffset + 0x0e, spawn.typeId)
            || !reader.readUInt16(spawnOffset + 0x10, spawn.index)
            || !reader.readUInt16(spawnOffset + 0x12, spawn.attributes))
        {
            return std::nullopt;
        }

        spawn.x = coordinateX;
        spawn.y = coordinateY;
        spawn.z = coordinateZ;

        if (*version > 6)
        {
            if (!reader.readUInt32(spawnOffset + 0x14, spawn.group))
            {
                return std::nullopt;
            }
        }

        outdoorMapData.spawns.push_back(spawn);
    }

    outdoorMapData.minHeightSample = std::numeric_limits<int>::max();
    outdoorMapData.maxHeightSample = std::numeric_limits<int>::min();

    std::array<bool, 256> seenTiles = {};

    for (const uint8_t heightSample : outdoorMapData.heightMap)
    {
        outdoorMapData.minHeightSample = std::min(outdoorMapData.minHeightSample, static_cast<int>(heightSample));
        outdoorMapData.maxHeightSample = std::max(outdoorMapData.maxHeightSample, static_cast<int>(heightSample));
    }

    for (const uint8_t tileId : outdoorMapData.tileMap)
    {
        if (!seenTiles[tileId])
        {
            seenTiles[tileId] = true;
            ++outdoorMapData.uniqueTileCount;
        }
    }

    return outdoorMapData;
}
}
