#include "game/indoor/IndoorMapData.h"
#include "game/BinaryReader.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
void copyFaceVertex(IndoorFace &face, size_t sourceIndex, size_t destinationIndex)
{
    face.vertexIndices[destinationIndex] = face.vertexIndices[sourceIndex];
    face.textureUs[destinationIndex] = face.textureUs[sourceIndex];
    face.textureVs[destinationIndex] = face.textureVs[sourceIndex];
}

void dropDuplicateFaceVertices(IndoorFace &face)
{
    if (face.vertexIndices.size() != face.textureUs.size()
        || face.vertexIndices.size() != face.textureVs.size())
    {
        face.vertexIndices.clear();
        face.textureUs.clear();
        face.textureVs.clear();
        return;
    }

    size_t writeIndex = 0;

    for (size_t readIndex = 0; readIndex < face.vertexIndices.size(); ++readIndex)
    {
        if (writeIndex > 0 && face.vertexIndices[readIndex] == face.vertexIndices[writeIndex - 1])
        {
            continue;
        }

        if (writeIndex > 1 && face.vertexIndices[readIndex] == face.vertexIndices[writeIndex - 2])
        {
            --writeIndex;
            continue;
        }

        if (readIndex != writeIndex)
        {
            copyFaceVertex(face, readIndex, writeIndex);
        }

        ++writeIndex;
    }

    if (writeIndex == 0)
    {
        face.vertexIndices.clear();
        face.textureUs.clear();
        face.textureVs.clear();
        return;
    }

    size_t left = 0;
    size_t right = writeIndex - 1;

    while (left < right)
    {
        if (face.vertexIndices[left] == face.vertexIndices[right])
        {
            --right;
        }
        else if (right > left + 1 && face.vertexIndices[left] == face.vertexIndices[right - 1])
        {
            right -= 2;
        }
        else if (right > left + 1 && face.vertexIndices[left + 1] == face.vertexIndices[right])
        {
            left += 2;
        }
        else
        {
            break;
        }
    }

    if (left != 0)
    {
        for (size_t index = left; index <= right; ++index)
        {
            copyFaceVertex(face, index, index - left);
        }
    }

    const size_t finalCount = right >= left ? (right - left + 1) : 0;
    face.vertexIndices.resize(finalCount);
    face.textureUs.resize(finalCount);
    face.textureVs.resize(finalCount);
}

constexpr size_t SectionOffset = 0x88;
constexpr size_t FaceDataSizeOffset = 0x68;
constexpr size_t SectorRDataSizeOffset = 0x6c;
constexpr size_t SectorRLDataSizeOffset = 0x70;
constexpr size_t TextureNameSize = 10;
constexpr size_t FaceParamRecordSize = 0x24;
constexpr size_t FaceParamNameSize = 0x0a;
constexpr size_t OutlineRecordSize = 0x0c;
constexpr size_t Unknown9RecordSize = 0x08;
constexpr size_t VertexRecordSize = 0x06;
constexpr size_t SpriteNameSize = 0x20;

struct VersionLayout
{
    int version = 0;
    size_t faceRecordSize = 0;
    size_t sectorRecordSize = 0;
    size_t spriteRecordSize = 0;
    size_t lightRecordSize = 0;
    size_t spawnRecordSize = 0;
};

struct SectorLayout
{
    size_t unknown0Offset = 0;
    size_t floorCountOffset = 0;
    size_t wallCountOffset = 0;
    size_t ceilingCountOffset = 0;
    size_t fluidCountOffset = 0;
    size_t portalCountOffset = 0;
    size_t faceCountOffset = 0;
    size_t nonBspFaceCountOffset = 0;
    size_t cylinderFaceCountOffset = 0;
    size_t cogCountOffset = 0;
    size_t decorationCountOffset = 0;
    size_t markerCountOffset = 0;
    size_t lightCountOffset = 0;
    size_t waterLevelOffset = 0;
    size_t mistLevelOffset = 0;
    size_t lightDistanceMultiplierOffset = 0;
    size_t minAmbientLightLevelOffset = 0;
    size_t firstBspNodeOffset = 0;
    size_t exitTagOffset = 0;
    size_t boundingBoxOffset = 0;
};

std::string readTextureName(const ByteReader &reader, size_t offset)
{
    return reader.readFixedString(offset, TextureNameSize);
}

std::string readFixedString(const ByteReader &reader, size_t offset, size_t maxLength)
{
    return reader.readFixedString(offset, maxLength);
}

bool canParseVersion(const ByteReader &reader, const VersionLayout &layout)
{
    size_t offset = SectionOffset;
    int vertexCount = 0;

    if (!reader.readInt32(offset, vertexCount) || vertexCount < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);
    offset += static_cast<size_t>(vertexCount) * VertexRecordSize;

    int faceCount = 0;

    if (!reader.readInt32(offset, faceCount) || faceCount < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);
    offset += static_cast<size_t>(faceCount) * layout.faceRecordSize;

    int faceDataSize = 0;

    if (!reader.readInt32(FaceDataSizeOffset, faceDataSize) || faceDataSize < 0)
    {
        return false;
    }

    offset += static_cast<size_t>(faceDataSize);
    offset += static_cast<size_t>(faceCount) * TextureNameSize;

    int faceParamCount = 0;

    if (!reader.readInt32(offset, faceParamCount) || faceParamCount < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);
    offset += static_cast<size_t>(faceParamCount) * FaceParamRecordSize;
    offset += static_cast<size_t>(faceParamCount) * FaceParamNameSize;

    int sectorCount = 0;

    if (!reader.readInt32(offset, sectorCount) || sectorCount < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);
    offset += static_cast<size_t>(sectorCount) * layout.sectorRecordSize;

    int sectorRDataSize = 0;
    int sectorRLDataSize = 0;

    if (!reader.readInt32(SectorRDataSizeOffset, sectorRDataSize) || sectorRDataSize < 0)
    {
        return false;
    }

    if (!reader.readInt32(SectorRLDataSizeOffset, sectorRLDataSize) || sectorRLDataSize < 0)
    {
        return false;
    }

    offset += static_cast<size_t>(sectorRDataSize);
    offset += static_cast<size_t>(sectorRLDataSize);

    int spriteHeaderCount = 0;
    int spriteCount = 0;

    if (!reader.readInt32(offset, spriteHeaderCount) || spriteHeaderCount < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);

    if (!reader.readInt32(offset, spriteCount) || spriteCount < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);
    offset += static_cast<size_t>(spriteCount) * layout.spriteRecordSize;
    offset += static_cast<size_t>(spriteCount) * SpriteNameSize;

    int lightCount = 0;

    if (!reader.readInt32(offset, lightCount) || lightCount < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);
    offset += static_cast<size_t>(lightCount) * layout.lightRecordSize;

    int unknown9Count = 0;

    if (!reader.readInt32(offset, unknown9Count) || unknown9Count < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);
    offset += static_cast<size_t>(unknown9Count) * Unknown9RecordSize;

    int spawnCount = 0;

    if (!reader.readInt32(offset, spawnCount) || spawnCount < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);
    offset += static_cast<size_t>(spawnCount) * layout.spawnRecordSize;

    int outlineCount = 0;

    if (!reader.readInt32(offset, outlineCount) || outlineCount < 0)
    {
        return false;
    }

    offset += sizeof(int32_t);
    offset += static_cast<size_t>(outlineCount) * OutlineRecordSize;

    return offset == reader.size();
}

std::optional<VersionLayout> detectLayout(const ByteReader &reader)
{
    const std::array<VersionLayout, 3> layouts = {{
        {6, 0x50, 0x74, 0x1c, 0x0c, 0x14},
        {7, 0x60, 0x74, 0x20, 0x10, 0x18},
        {8, 0x60, 0x78, 0x20, 0x14, 0x18},
    }};

    for (const VersionLayout &layout : layouts)
    {
        if (canParseVersion(reader, layout))
        {
            return layout;
        }
    }

    return std::nullopt;
}

SectorLayout sectorLayoutForVersion(int version)
{
    if (version >= 8)
    {
        return {
            .unknown0Offset = 0x04,
            .floorCountOffset = 0x08,
            .wallCountOffset = 0x10,
            .ceilingCountOffset = 0x18,
            .fluidCountOffset = 0x20,
            .portalCountOffset = 0x28,
            .faceCountOffset = 0x30,
            .nonBspFaceCountOffset = 0x32,
            .cylinderFaceCountOffset = 0x38,
            .cogCountOffset = 0x40,
            .decorationCountOffset = 0x48,
            .markerCountOffset = 0x50,
            .lightCountOffset = 0x58,
            .waterLevelOffset = 0x60,
            .mistLevelOffset = 0x62,
            .lightDistanceMultiplierOffset = 0x64,
            .minAmbientLightLevelOffset = 0x66,
            .firstBspNodeOffset = 0x68,
            .exitTagOffset = 0x6a,
            .boundingBoxOffset = 0x6c,
        };
    }

    return {
        .unknown0Offset = 0x00,
        .floorCountOffset = 0x04,
        .wallCountOffset = 0x0c,
        .ceilingCountOffset = 0x14,
        .fluidCountOffset = 0x1c,
        .portalCountOffset = 0x24,
        .faceCountOffset = 0x2c,
        .nonBspFaceCountOffset = 0x2e,
        .cylinderFaceCountOffset = 0x34,
        .cogCountOffset = 0x3c,
        .decorationCountOffset = 0x44,
        .markerCountOffset = 0x4c,
        .lightCountOffset = 0x54,
        .waterLevelOffset = 0x5c,
        .mistLevelOffset = 0x5e,
        .lightDistanceMultiplierOffset = 0x60,
        .minAmbientLightLevelOffset = 0x62,
        .firstBspNodeOffset = 0x64,
        .exitTagOffset = 0x66,
        .boundingBoxOffset = 0x68,
    };
}
}

std::optional<IndoorMapData> IndoorMapDataLoader::loadFromBytes(const std::vector<uint8_t> &bytes) const
{
    const ByteReader reader(bytes);
    const std::optional<VersionLayout> layout = detectLayout(reader);

    if (!layout)
    {
        return std::nullopt;
    }

    IndoorMapData indoorMapData = {};
    indoorMapData.version = layout->version;
    reader.readInt32(FaceDataSizeOffset, indoorMapData.faceDataSizeBytes);
    reader.readInt32(SectorRDataSizeOffset, indoorMapData.sectorDataSizeBytes);
    reader.readInt32(SectorRLDataSizeOffset, indoorMapData.sectorLightDataSizeBytes);

    if (layout->version > 6)
    {
        reader.readInt32(0x74, indoorMapData.doorsDataSizeBytes);
    }

    size_t offset = SectionOffset;
    int vertexCount = 0;
    reader.readInt32(offset, vertexCount);
    offset += sizeof(int32_t);

    indoorMapData.vertices.reserve(static_cast<size_t>(vertexCount));

    for (int vertexIndex = 0; vertexIndex < vertexCount; ++vertexIndex)
    {
        const size_t vertexOffset = offset + static_cast<size_t>(vertexIndex) * VertexRecordSize;
        int16_t x = 0;
        int16_t y = 0;
        int16_t z = 0;
        reader.readInt16(vertexOffset + 0, x);
        reader.readInt16(vertexOffset + 2, y);
        reader.readInt16(vertexOffset + 4, z);
        indoorMapData.vertices.push_back({x, y, z});
    }

    offset += static_cast<size_t>(vertexCount) * VertexRecordSize;

    int faceCount = 0;
    reader.readInt32(offset, faceCount);
    indoorMapData.rawFaceCount = static_cast<uint32_t>(std::max(faceCount, 0));
    offset += sizeof(int32_t);

    const size_t faceHeadersOffset = offset;
    offset += static_cast<size_t>(faceCount) * layout->faceRecordSize;

    int faceDataSize = 0;
    reader.readInt32(FaceDataSizeOffset, faceDataSize);
    const size_t faceDataOffset = offset;
    offset += static_cast<size_t>(faceDataSize);

    const size_t faceTextureNamesOffset = offset;
    offset += static_cast<size_t>(faceCount) * TextureNameSize;

    int faceParamCount = 0;
    reader.readInt32(offset, faceParamCount);
    offset += sizeof(int32_t);

    const size_t faceParamsOffset = offset;
    offset += static_cast<size_t>(faceParamCount) * FaceParamRecordSize;
    offset += static_cast<size_t>(faceParamCount) * FaceParamNameSize;

    indoorMapData.faces.resize(static_cast<size_t>(std::max(faceCount, 0)));

    size_t faceDataCursor = faceDataOffset;

    for (int faceIndex = 0; faceIndex < faceCount; ++faceIndex)
    {
        IndoorFace &face = indoorMapData.faces[static_cast<size_t>(faceIndex)];
        const size_t headerOffset = faceHeadersOffset + static_cast<size_t>(faceIndex) * layout->faceRecordSize;
        const size_t faceStructOffset = (layout->version > 6) ? headerOffset + 0x10 : headerOffset;

        uint32_t attributes = 0;
        uint16_t faceParamIndex = 0;
        uint16_t roomNumber = 0;
        uint16_t roomBehindNumber = 0;
        uint8_t vertexPerFaceCount = 0;
        uint8_t facetType = 0;
        reader.readUInt32(faceStructOffset + 0x1c, attributes);
        reader.readUInt16(faceStructOffset + 0x38, faceParamIndex);
        reader.readUInt16(faceStructOffset + 0x3c, roomNumber);
        reader.readUInt16(faceStructOffset + 0x3e, roomBehindNumber);
        reader.readUInt8(faceStructOffset + 0x4c, facetType);
        reader.readUInt8(faceStructOffset + 0x4d, vertexPerFaceCount);

        face = {};
        face.attributes = attributes;
        face.isPortal = (attributes & 0x1u) != 0;
        face.roomNumber = roomNumber;
        face.roomBehindNumber = roomBehindNumber;
        face.facetType = facetType;
        face.textureName = readTextureName(
            reader,
            faceTextureNamesOffset + static_cast<size_t>(faceIndex) * TextureNameSize
        );

        const size_t streamStride = static_cast<size_t>(vertexPerFaceCount + 1) * sizeof(int16_t);

        face.vertexIndices.reserve(vertexPerFaceCount);
        face.textureUs.reserve(vertexPerFaceCount);
        face.textureVs.reserve(vertexPerFaceCount);
        if (vertexPerFaceCount >= 3)
        {
            for (size_t vertexIndex = 0; vertexIndex < vertexPerFaceCount; ++vertexIndex)
            {
                uint16_t vertexId = 0;
                int16_t textureU = 0;
                int16_t textureV = 0;

                reader.readUInt16(faceDataCursor + vertexIndex * sizeof(uint16_t), vertexId);
                reader.readInt16(faceDataCursor + streamStride * 4 + vertexIndex * sizeof(int16_t), textureU);
                reader.readInt16(faceDataCursor + streamStride * 5 + vertexIndex * sizeof(int16_t), textureV);

                if (vertexId >= indoorMapData.vertices.size())
                {
                    face.vertexIndices.clear();
                    face.textureUs.clear();
                    face.textureVs.clear();
                    break;
                }

                face.vertexIndices.push_back(vertexId);
                face.textureUs.push_back(textureU);
                face.textureVs.push_back(textureV);
            }
        }

        faceDataCursor += streamStride * 6;

        if (faceParamIndex < static_cast<uint16_t>(faceParamCount))
        {
            const size_t faceParamOffset =
                faceParamsOffset + static_cast<size_t>(faceParamIndex) * FaceParamRecordSize;
            reader.readInt16(faceParamOffset + 0x14, face.textureDeltaU);
            reader.readInt16(faceParamOffset + 0x16, face.textureDeltaV);
            reader.readUInt16(faceParamOffset + 0x10, face.textureFrameTableIndex);
            reader.readUInt16(faceParamOffset + 0x12, face.textureFrameTableCog);
            reader.readUInt16(faceParamOffset + 0x18, face.cogNumber);
            reader.readUInt16(faceParamOffset + 0x1a, face.cogTriggered);
            reader.readUInt16(faceParamOffset + 0x1c, face.cogTriggerType);
            reader.readUInt16(faceParamOffset + 0x22, face.lightLevel);
        }

        if (face.vertexIndices.size() >= 3)
        {
            dropDuplicateFaceVertices(face);
        }
    }

    int sectorCount = 0;
    reader.readInt32(offset, sectorCount);
    indoorMapData.sectorCount = static_cast<size_t>(sectorCount);
    offset += sizeof(int32_t);

    indoorMapData.sectors.reserve(indoorMapData.sectorCount);
    const SectorLayout sectorLayout = sectorLayoutForVersion(layout->version);

    for (size_t sectorIndex = 0; sectorIndex < indoorMapData.sectorCount; ++sectorIndex)
    {
        const size_t sectorOffset = offset + sectorIndex * layout->sectorRecordSize;
        IndoorSector sector = {};
        reader.readInt32(sectorOffset + 0x00, sector.flags);
        reader.readInt32(sectorOffset + sectorLayout.unknown0Offset, sector.unknown0);
        reader.readUInt16(sectorOffset + sectorLayout.floorCountOffset, sector.floorCount);
        reader.readUInt16(sectorOffset + sectorLayout.wallCountOffset, sector.wallCount);
        reader.readUInt16(sectorOffset + sectorLayout.ceilingCountOffset, sector.ceilingCount);
        reader.readUInt16(sectorOffset + sectorLayout.fluidCountOffset, sector.fluidCount);
        reader.readInt16(sectorOffset + sectorLayout.portalCountOffset, sector.portalCount);
        reader.readUInt16(sectorOffset + sectorLayout.faceCountOffset, sector.faceCount);
        reader.readUInt16(sectorOffset + sectorLayout.nonBspFaceCountOffset, sector.nonBspFaceCount);
        reader.readUInt16(sectorOffset + sectorLayout.cylinderFaceCountOffset, sector.cylinderFaceCount);
        reader.readUInt16(sectorOffset + sectorLayout.cogCountOffset, sector.cogCount);
        reader.readUInt16(sectorOffset + sectorLayout.decorationCountOffset, sector.decorationCount);
        reader.readUInt16(sectorOffset + sectorLayout.markerCountOffset, sector.markerCount);
        reader.readUInt16(sectorOffset + sectorLayout.lightCountOffset, sector.lightCount);
        reader.readInt16(sectorOffset + sectorLayout.waterLevelOffset, sector.waterLevel);
        reader.readInt16(sectorOffset + sectorLayout.mistLevelOffset, sector.mistLevel);
        reader.readInt16(
            sectorOffset + sectorLayout.lightDistanceMultiplierOffset,
            sector.lightDistanceMultiplier
        );
        reader.readInt16(
            sectorOffset + sectorLayout.minAmbientLightLevelOffset,
            sector.minAmbientLightLevel
        );
        reader.readInt16(sectorOffset + sectorLayout.firstBspNodeOffset, sector.firstBspNode);
        reader.readInt16(sectorOffset + sectorLayout.exitTagOffset, sector.exitTag);
        reader.readInt16(sectorOffset + sectorLayout.boundingBoxOffset + 0x00, sector.minX);
        reader.readInt16(sectorOffset + sectorLayout.boundingBoxOffset + 0x02, sector.maxX);
        reader.readInt16(sectorOffset + sectorLayout.boundingBoxOffset + 0x04, sector.minY);
        reader.readInt16(sectorOffset + sectorLayout.boundingBoxOffset + 0x06, sector.maxY);
        reader.readInt16(sectorOffset + sectorLayout.boundingBoxOffset + 0x08, sector.minZ);
        reader.readInt16(sectorOffset + sectorLayout.boundingBoxOffset + 0x0a, sector.maxZ);
        indoorMapData.sectors.push_back(sector);
    }

    offset += indoorMapData.sectorCount * layout->sectorRecordSize;

    int sectorRDataSize = 0;
    int sectorRLDataSize = 0;
    reader.readInt32(SectorRDataSizeOffset, sectorRDataSize);
    reader.readInt32(SectorRLDataSizeOffset, sectorRLDataSize);
    indoorMapData.sectorData.reserve(static_cast<size_t>(sectorRDataSize) / sizeof(uint16_t));

    for (size_t dataOffset = 0; dataOffset < static_cast<size_t>(sectorRDataSize); dataOffset += sizeof(uint16_t))
    {
        uint16_t value = 0;
        reader.readUInt16(offset + dataOffset, value);
        indoorMapData.sectorData.push_back(value);
    }

    offset += static_cast<size_t>(sectorRDataSize);
    indoorMapData.sectorLightData.reserve(static_cast<size_t>(sectorRLDataSize) / sizeof(uint16_t));

    for (size_t dataOffset = 0; dataOffset < static_cast<size_t>(sectorRLDataSize); dataOffset += sizeof(uint16_t))
    {
        uint16_t value = 0;
        reader.readUInt16(offset + dataOffset, value);
        indoorMapData.sectorLightData.push_back(value);
    }

    offset += static_cast<size_t>(sectorRLDataSize);

    size_t sectorDataIndex = 0;

    for (IndoorSector &sector : indoorMapData.sectors)
    {
        const auto consumeSectorData = [&indoorMapData, &sectorDataIndex](size_t count, std::vector<uint16_t> &output)
        {
            output.clear();
            output.reserve(count);

            for (size_t index = 0; index < count && sectorDataIndex < indoorMapData.sectorData.size(); ++index)
            {
                output.push_back(indoorMapData.sectorData[sectorDataIndex++]);
            }
        };

        consumeSectorData(sector.floorCount, sector.floorFaceIds);
        consumeSectorData(sector.wallCount, sector.wallFaceIds);
        consumeSectorData(sector.ceilingCount, sector.ceilingFaceIds);
        sectorDataIndex += sector.fluidCount;
        consumeSectorData(static_cast<size_t>(std::max<int16_t>(sector.portalCount, 0)), sector.portalFaceIds);
        consumeSectorData(sector.faceCount, sector.faceIds);

        if (sector.nonBspFaceCount < sector.faceIds.size())
        {
            sector.nonBspFaceIds.assign(sector.faceIds.begin(), sector.faceIds.begin() + sector.nonBspFaceCount);
        }
        else
        {
            sector.nonBspFaceIds = sector.faceIds;
        }

        consumeSectorData(sector.cylinderFaceCount, sector.cylinderFaceIds);
        sectorDataIndex += sector.cogCount;
        consumeSectorData(sector.decorationCount, sector.decorationIds);
        sectorDataIndex += sector.markerCount;
    }

    size_t sectorLightDataIndex = 0;

    for (IndoorSector &sector : indoorMapData.sectors)
    {
        sector.lightIds.clear();
        sector.lightIds.reserve(sector.lightCount);

        for (size_t lightIndex = 0;
             lightIndex < sector.lightCount && sectorLightDataIndex < indoorMapData.sectorLightData.size();
             ++lightIndex)
        {
            sector.lightIds.push_back(indoorMapData.sectorLightData[sectorLightDataIndex++]);
        }
    }

    int spriteHeaderCount = 0;
    int spriteCount = 0;

    if (!reader.readInt32(offset, spriteHeaderCount))
    {
        return std::nullopt;
    }

    indoorMapData.doorCount = static_cast<uint32_t>(spriteHeaderCount);
    offset += sizeof(int32_t);

    if (!reader.readInt32(offset, spriteCount))
    {
        return std::nullopt;
    }

    indoorMapData.spriteCount = static_cast<size_t>(spriteCount);
    offset += sizeof(int32_t);

    const size_t spriteDataOffset = offset;
    offset += indoorMapData.spriteCount * layout->spriteRecordSize;
    const size_t spriteNamesOffset = offset;
    offset += indoorMapData.spriteCount * SpriteNameSize;

    indoorMapData.entities.reserve(indoorMapData.spriteCount);

    for (size_t spriteIndex = 0; spriteIndex < indoorMapData.spriteCount; ++spriteIndex)
    {
        const size_t spriteOffset = spriteDataOffset + spriteIndex * layout->spriteRecordSize;
        IndoorEntity entity = {};
        int32_t coordinateX = 0;
        int32_t coordinateY = 0;
        int32_t coordinateZ = 0;
        int32_t facing = 0;

        if (!reader.readUInt16(spriteOffset + 0x00, entity.decorationListId)
            || !reader.readUInt16(spriteOffset + 0x02, entity.aiAttributes)
            || !reader.readInt32(spriteOffset + 0x04, coordinateX)
            || !reader.readInt32(spriteOffset + 0x08, coordinateY)
            || !reader.readInt32(spriteOffset + 0x0c, coordinateZ)
            || !reader.readInt32(spriteOffset + 0x10, facing)
            || !reader.readUInt16(spriteOffset + 0x14, entity.eventIdPrimary)
            || !reader.readUInt16(spriteOffset + 0x16, entity.eventIdSecondary)
            || !reader.readUInt16(spriteOffset + 0x18, entity.variablePrimary)
            || !reader.readUInt16(spriteOffset + 0x1a, entity.variableSecondary))
        {
            return std::nullopt;
        }

        entity.x = coordinateX;
        entity.y = coordinateY;
        entity.z = coordinateZ;
        entity.facing = facing;

        if (layout->version > 6)
        {
            if (!reader.readUInt16(spriteOffset + 0x1c, entity.specialTrigger))
            {
                return std::nullopt;
            }
        }

        entity.name = readFixedString(reader, spriteNamesOffset + spriteIndex * SpriteNameSize, SpriteNameSize);
        indoorMapData.entities.push_back(entity);
    }

    int lightCount = 0;

    if (!reader.readInt32(offset, lightCount))
    {
        return std::nullopt;
    }

    indoorMapData.lightCount = static_cast<size_t>(lightCount);
    offset += sizeof(int32_t);

    indoorMapData.lights.reserve(indoorMapData.lightCount);

    for (size_t lightIndex = 0; lightIndex < indoorMapData.lightCount; ++lightIndex)
    {
        const size_t lightOffset = offset + lightIndex * layout->lightRecordSize;
        IndoorLight light = {};
        uint8_t red = 0;
        uint8_t green = 0;
        uint8_t blue = 0;
        uint8_t type = 0;
        reader.readInt16(lightOffset + 0x00, light.x);
        reader.readInt16(lightOffset + 0x02, light.y);
        reader.readInt16(lightOffset + 0x04, light.z);
        reader.readInt16(lightOffset + 0x06, light.radius);
        reader.readUInt8(lightOffset + 0x08, red);
        reader.readUInt8(lightOffset + 0x09, green);
        reader.readUInt8(lightOffset + 0x0a, blue);
        reader.readUInt8(lightOffset + 0x0b, type);
        light.red = red;
        light.green = green;
        light.blue = blue;
        light.type = type;

        if (layout->version > 6)
        {
            reader.readInt16(lightOffset + 0x0c, light.attributes);
            reader.readInt16(lightOffset + 0x0e, light.brightness);
        }
        else
        {
            uint16_t brightness = 0;
            reader.readUInt16(lightOffset + 0x0a, brightness);
            light.brightness = static_cast<int16_t>(brightness);
        }

        indoorMapData.lights.push_back(light);
    }

    offset += indoorMapData.lightCount * layout->lightRecordSize;

    int unknown9Count = 0;

    if (!reader.readInt32(offset, unknown9Count))
    {
        return std::nullopt;
    }

    offset += sizeof(int32_t);
    indoorMapData.bspNodes.reserve(static_cast<size_t>(unknown9Count));

    for (int nodeIndex = 0; nodeIndex < unknown9Count; ++nodeIndex)
    {
        const size_t nodeOffset = offset + static_cast<size_t>(nodeIndex) * Unknown9RecordSize;
        IndoorBspNode node = {};
        reader.readInt16(nodeOffset + 0x00, node.front);
        reader.readInt16(nodeOffset + 0x02, node.back);
        reader.readInt16(nodeOffset + 0x04, node.faceIdOffset);
        reader.readInt16(nodeOffset + 0x06, node.faceCount);
        indoorMapData.bspNodes.push_back(node);
    }

    offset += static_cast<size_t>(unknown9Count) * Unknown9RecordSize;

    int spawnCount = 0;
    if (!reader.readInt32(offset, spawnCount))
    {
        return std::nullopt;
    }

    indoorMapData.spawnCount = static_cast<size_t>(spawnCount);
    offset += sizeof(int32_t);

    const size_t spawnDataOffset = offset;
    indoorMapData.spawns.reserve(indoorMapData.spawnCount);

    for (size_t spawnIndex = 0; spawnIndex < indoorMapData.spawnCount; ++spawnIndex)
    {
        const size_t spawnOffset = spawnDataOffset + spawnIndex * layout->spawnRecordSize;
        IndoorSpawn spawn = {};
        int32_t coordinateX = 0;
        int32_t coordinateY = 0;
        int32_t coordinateZ = 0;

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

        if (layout->version > 6)
        {
            if (!reader.readUInt32(spawnOffset + 0x14, spawn.group))
            {
                return std::nullopt;
            }
        }

        indoorMapData.spawns.push_back(spawn);
    }

    offset += indoorMapData.spawnCount * layout->spawnRecordSize;

    int outlineCount = 0;

    if (!reader.readInt32(offset, outlineCount) || outlineCount < 0)
    {
        return std::nullopt;
    }

    offset += sizeof(int32_t);
    indoorMapData.outlines.reserve(static_cast<size_t>(outlineCount));

    for (int outlineIndex = 0; outlineIndex < outlineCount; ++outlineIndex)
    {
        const size_t outlineOffset = offset + static_cast<size_t>(outlineIndex) * OutlineRecordSize;
        IndoorOutline outline = {};
        reader.readUInt16(outlineOffset + 0x00, outline.vertex1Id);
        reader.readUInt16(outlineOffset + 0x02, outline.vertex2Id);
        reader.readUInt16(outlineOffset + 0x04, outline.face1Id);
        reader.readUInt16(outlineOffset + 0x06, outline.face2Id);
        reader.readInt16(outlineOffset + 0x08, outline.z);
        reader.readUInt16(outlineOffset + 0x0a, outline.flags);
        indoorMapData.outlines.push_back(outline);
    }

    return indoorMapData;
}
}
