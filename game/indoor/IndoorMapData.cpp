#include "game/indoor/IndoorMapData.h"
#include "game/BinaryReader.h"

#include <array>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
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

template <typename ValueType>
void writeValue(std::vector<uint8_t> &bytes, size_t offset, ValueType value)
{
    if (offset + sizeof(ValueType) > bytes.size())
    {
        return;
    }

    std::memcpy(bytes.data() + offset, &value, sizeof(ValueType));
}

void appendZeroBytes(std::vector<uint8_t> &bytes, size_t count)
{
    bytes.insert(bytes.end(), count, 0);
}

void appendInt32(std::vector<uint8_t> &bytes, int32_t value)
{
    const size_t offset = bytes.size();
    appendZeroBytes(bytes, sizeof(value));
    writeValue(bytes, offset, value);
}

void appendUInt16(std::vector<uint8_t> &bytes, uint16_t value)
{
    const size_t offset = bytes.size();
    appendZeroBytes(bytes, sizeof(value));
    writeValue(bytes, offset, value);
}

void appendInt16(std::vector<uint8_t> &bytes, int16_t value)
{
    const size_t offset = bytes.size();
    appendZeroBytes(bytes, sizeof(value));
    writeValue(bytes, offset, value);
}

void appendFixedString(std::vector<uint8_t> &bytes, const std::string &value, size_t maxLength)
{
    const size_t offset = bytes.size();
    appendZeroBytes(bytes, maxLength);
    const size_t copyLength = std::min(maxLength, value.size());

    if (copyLength > 0)
    {
        std::memcpy(bytes.data() + offset, value.data(), copyLength);
    }
}

uint16_t clampedUInt16(size_t value)
{
    return static_cast<uint16_t>(std::min<size_t>(value, 0xffffu));
}

int16_t clampedInt16(int value)
{
    return static_cast<int16_t>(std::clamp(value, -32768, 32767));
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

std::optional<std::vector<uint8_t>> IndoorMapDataWriter::buildBytes(const IndoorMapData &indoorMapData) const
{
    static constexpr VersionLayout Layout = {8, 0x60, 0x78, 0x20, 0x14, 0x18};
    const SectorLayout sectorLayout = sectorLayoutForVersion(Layout.version);

    if (indoorMapData.vertices.size() > 0x7fffffffu || indoorMapData.faces.size() > 0x7fffffffu)
    {
        return std::nullopt;
    }

    std::vector<uint8_t> bytes(SectionOffset, 0);

    writeValue<int32_t>(bytes, 0x00, Layout.version);
    appendInt32(bytes, static_cast<int32_t>(indoorMapData.vertices.size()));

    for (const IndoorVertex &vertex : indoorMapData.vertices)
    {
        appendInt16(bytes, clampedInt16(vertex.x));
        appendInt16(bytes, clampedInt16(vertex.y));
        appendInt16(bytes, clampedInt16(vertex.z));
    }

    appendInt32(bytes, static_cast<int32_t>(indoorMapData.faces.size()));
    const size_t faceHeadersOffset = bytes.size();
    appendZeroBytes(bytes, indoorMapData.faces.size() * Layout.faceRecordSize);

    std::vector<uint8_t> faceDataBytes;

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = indoorMapData.faces[faceIndex];
        const size_t vertexCount = face.vertexIndices.size();
        const size_t streamStride = (vertexCount + 1) * sizeof(int16_t);
        const size_t faceDataOffset = faceDataBytes.size();
        appendZeroBytes(faceDataBytes, streamStride * 6);

        for (size_t vertexIndex = 0; vertexIndex < vertexCount; ++vertexIndex)
        {
            const int16_t textureU = vertexIndex < face.textureUs.size() ? face.textureUs[vertexIndex] : 0;
            const int16_t textureV = vertexIndex < face.textureVs.size() ? face.textureVs[vertexIndex] : 0;
            writeValue<uint16_t>(
                faceDataBytes,
                faceDataOffset + vertexIndex * sizeof(uint16_t),
                face.vertexIndices[vertexIndex]);
            writeValue<int16_t>(
                faceDataBytes,
                faceDataOffset + streamStride * 4 + vertexIndex * sizeof(int16_t),
                textureU);
            writeValue<int16_t>(
                faceDataBytes,
                faceDataOffset + streamStride * 5 + vertexIndex * sizeof(int16_t),
                textureV);
        }

        const size_t faceStructOffset = faceHeadersOffset + faceIndex * Layout.faceRecordSize + 0x10;
        writeValue<uint32_t>(bytes, faceStructOffset + 0x1c, face.attributes);
        writeValue<uint16_t>(bytes, faceStructOffset + 0x38, static_cast<uint16_t>(faceIndex));
        writeValue<uint16_t>(bytes, faceStructOffset + 0x3c, face.roomNumber);
        writeValue<uint16_t>(bytes, faceStructOffset + 0x3e, face.roomBehindNumber);
        writeValue<uint8_t>(bytes, faceStructOffset + 0x4c, face.facetType);
        writeValue<uint8_t>(bytes, faceStructOffset + 0x4d, static_cast<uint8_t>(std::min<size_t>(vertexCount, 255)));
    }

    writeValue<int32_t>(bytes, FaceDataSizeOffset, static_cast<int32_t>(faceDataBytes.size()));
    bytes.insert(bytes.end(), faceDataBytes.begin(), faceDataBytes.end());

    for (const IndoorFace &face : indoorMapData.faces)
    {
        appendFixedString(bytes, face.textureName, TextureNameSize);
    }

    appendInt32(bytes, static_cast<int32_t>(indoorMapData.faces.size()));

    for (const IndoorFace &face : indoorMapData.faces)
    {
        const size_t faceParamOffset = bytes.size();
        appendZeroBytes(bytes, FaceParamRecordSize);
        writeValue<uint16_t>(bytes, faceParamOffset + 0x10, face.textureFrameTableIndex);
        writeValue<uint16_t>(bytes, faceParamOffset + 0x12, face.textureFrameTableCog);
        writeValue<int16_t>(bytes, faceParamOffset + 0x14, face.textureDeltaU);
        writeValue<int16_t>(bytes, faceParamOffset + 0x16, face.textureDeltaV);
        writeValue<uint16_t>(bytes, faceParamOffset + 0x18, face.cogNumber);
        writeValue<uint16_t>(bytes, faceParamOffset + 0x1a, face.cogTriggered);
        writeValue<uint16_t>(bytes, faceParamOffset + 0x1c, face.cogTriggerType);
        writeValue<uint16_t>(bytes, faceParamOffset + 0x22, face.lightLevel);
    }

    for (const IndoorFace &face : indoorMapData.faces)
    {
        appendFixedString(bytes, face.textureName, FaceParamNameSize);
    }

    appendInt32(bytes, static_cast<int32_t>(indoorMapData.sectors.size()));
    const size_t sectorHeadersOffset = bytes.size();
    appendZeroBytes(bytes, indoorMapData.sectors.size() * Layout.sectorRecordSize);

    std::vector<uint16_t> sectorData;
    std::vector<uint16_t> sectorLightData;

    for (size_t sectorIndex = 0; sectorIndex < indoorMapData.sectors.size(); ++sectorIndex)
    {
        const IndoorSector &sector = indoorMapData.sectors[sectorIndex];
        const size_t sectorOffset = sectorHeadersOffset + sectorIndex * Layout.sectorRecordSize;
        const auto appendIds = [&sectorData](const std::vector<uint16_t> &ids)
        {
            sectorData.insert(sectorData.end(), ids.begin(), ids.end());
        };

        writeValue<int32_t>(bytes, sectorOffset + 0x00, sector.flags);
        writeValue<int32_t>(bytes, sectorOffset + sectorLayout.unknown0Offset, sector.unknown0);
        writeValue<uint16_t>(
            bytes,
            sectorOffset + sectorLayout.floorCountOffset,
            clampedUInt16(sector.floorFaceIds.size()));
        writeValue<uint16_t>(
            bytes,
            sectorOffset + sectorLayout.wallCountOffset,
            clampedUInt16(sector.wallFaceIds.size()));
        writeValue<uint16_t>(
            bytes,
            sectorOffset + sectorLayout.ceilingCountOffset,
            clampedUInt16(sector.ceilingFaceIds.size()));
        writeValue<uint16_t>(bytes, sectorOffset + sectorLayout.fluidCountOffset, sector.fluidCount);
        writeValue<int16_t>(
            bytes,
            sectorOffset + sectorLayout.portalCountOffset,
            clampedInt16(sector.portalFaceIds.size()));
        writeValue<uint16_t>(bytes, sectorOffset + sectorLayout.faceCountOffset, clampedUInt16(sector.faceIds.size()));
        writeValue<uint16_t>(
            bytes,
            sectorOffset + sectorLayout.nonBspFaceCountOffset,
            clampedUInt16(sector.nonBspFaceIds.size()));
        writeValue<uint16_t>(
            bytes,
            sectorOffset + sectorLayout.cylinderFaceCountOffset,
            clampedUInt16(sector.cylinderFaceIds.size()));
        writeValue<uint16_t>(bytes, sectorOffset + sectorLayout.cogCountOffset, sector.cogCount);
        writeValue<uint16_t>(
            bytes,
            sectorOffset + sectorLayout.decorationCountOffset,
            clampedUInt16(sector.decorationIds.size()));
        writeValue<uint16_t>(bytes, sectorOffset + sectorLayout.markerCountOffset, sector.markerCount);
        writeValue<uint16_t>(
            bytes,
            sectorOffset + sectorLayout.lightCountOffset,
            clampedUInt16(sector.lightIds.size()));
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.waterLevelOffset, sector.waterLevel);
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.mistLevelOffset, sector.mistLevel);
        writeValue<int16_t>(
            bytes,
            sectorOffset + sectorLayout.lightDistanceMultiplierOffset,
            sector.lightDistanceMultiplier);
        writeValue<int16_t>(
            bytes,
            sectorOffset + sectorLayout.minAmbientLightLevelOffset,
            sector.minAmbientLightLevel);
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.firstBspNodeOffset, sector.firstBspNode);
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.exitTagOffset, sector.exitTag);
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.boundingBoxOffset + 0x00, sector.minX);
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.boundingBoxOffset + 0x02, sector.maxX);
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.boundingBoxOffset + 0x04, sector.minY);
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.boundingBoxOffset + 0x06, sector.maxY);
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.boundingBoxOffset + 0x08, sector.minZ);
        writeValue<int16_t>(bytes, sectorOffset + sectorLayout.boundingBoxOffset + 0x0a, sector.maxZ);

        appendIds(sector.floorFaceIds);
        appendIds(sector.wallFaceIds);
        appendIds(sector.ceilingFaceIds);
        sectorData.insert(sectorData.end(), sector.fluidCount, 0);
        appendIds(sector.portalFaceIds);
        appendIds(sector.faceIds);
        appendIds(sector.cylinderFaceIds);
        sectorData.insert(sectorData.end(), sector.cogCount, 0);
        appendIds(sector.decorationIds);
        sectorData.insert(sectorData.end(), sector.markerCount, 0);
        sectorLightData.insert(sectorLightData.end(), sector.lightIds.begin(), sector.lightIds.end());
    }

    writeValue<int32_t>(bytes, SectorRDataSizeOffset, static_cast<int32_t>(sectorData.size() * sizeof(uint16_t)));
    writeValue<int32_t>(bytes, SectorRLDataSizeOffset, static_cast<int32_t>(sectorLightData.size() * sizeof(uint16_t)));

    for (uint16_t value : sectorData)
    {
        appendUInt16(bytes, value);
    }

    for (uint16_t value : sectorLightData)
    {
        appendUInt16(bytes, value);
    }

    appendInt32(bytes, static_cast<int32_t>(indoorMapData.doorCount));
    appendInt32(bytes, static_cast<int32_t>(indoorMapData.entities.size()));

    for (const IndoorEntity &entity : indoorMapData.entities)
    {
        const size_t entityOffset = bytes.size();
        appendZeroBytes(bytes, Layout.spriteRecordSize);
        writeValue<uint16_t>(bytes, entityOffset + 0x00, entity.decorationListId);
        writeValue<uint16_t>(bytes, entityOffset + 0x02, entity.aiAttributes);
        writeValue<int32_t>(bytes, entityOffset + 0x04, entity.x);
        writeValue<int32_t>(bytes, entityOffset + 0x08, entity.y);
        writeValue<int32_t>(bytes, entityOffset + 0x0c, entity.z);
        writeValue<int32_t>(bytes, entityOffset + 0x10, entity.facing);
        writeValue<uint16_t>(bytes, entityOffset + 0x14, entity.eventIdPrimary);
        writeValue<uint16_t>(bytes, entityOffset + 0x16, entity.eventIdSecondary);
        writeValue<uint16_t>(bytes, entityOffset + 0x18, entity.variablePrimary);
        writeValue<uint16_t>(bytes, entityOffset + 0x1a, entity.variableSecondary);
        writeValue<uint16_t>(bytes, entityOffset + 0x1c, entity.specialTrigger);
    }

    for (const IndoorEntity &entity : indoorMapData.entities)
    {
        appendFixedString(bytes, entity.name, SpriteNameSize);
    }

    appendInt32(bytes, static_cast<int32_t>(indoorMapData.lights.size()));

    for (const IndoorLight &light : indoorMapData.lights)
    {
        const size_t lightOffset = bytes.size();
        appendZeroBytes(bytes, Layout.lightRecordSize);
        writeValue<int16_t>(bytes, lightOffset + 0x00, light.x);
        writeValue<int16_t>(bytes, lightOffset + 0x02, light.y);
        writeValue<int16_t>(bytes, lightOffset + 0x04, light.z);
        writeValue<int16_t>(bytes, lightOffset + 0x06, light.radius);
        writeValue<uint8_t>(bytes, lightOffset + 0x08, light.red);
        writeValue<uint8_t>(bytes, lightOffset + 0x09, light.green);
        writeValue<uint8_t>(bytes, lightOffset + 0x0a, light.blue);
        writeValue<uint8_t>(bytes, lightOffset + 0x0b, light.type);
        writeValue<int16_t>(bytes, lightOffset + 0x0c, light.attributes);
        writeValue<int16_t>(bytes, lightOffset + 0x0e, light.brightness);
    }

    appendInt32(bytes, static_cast<int32_t>(indoorMapData.bspNodes.size()));

    for (const IndoorBspNode &node : indoorMapData.bspNodes)
    {
        appendInt16(bytes, node.front);
        appendInt16(bytes, node.back);
        appendInt16(bytes, node.faceIdOffset);
        appendInt16(bytes, node.faceCount);
    }

    appendInt32(bytes, static_cast<int32_t>(indoorMapData.spawns.size()));

    for (const IndoorSpawn &spawn : indoorMapData.spawns)
    {
        const size_t spawnOffset = bytes.size();
        appendZeroBytes(bytes, Layout.spawnRecordSize);
        writeValue<int32_t>(bytes, spawnOffset + 0x00, spawn.x);
        writeValue<int32_t>(bytes, spawnOffset + 0x04, spawn.y);
        writeValue<int32_t>(bytes, spawnOffset + 0x08, spawn.z);
        writeValue<uint16_t>(bytes, spawnOffset + 0x0c, spawn.radius);
        writeValue<uint16_t>(bytes, spawnOffset + 0x0e, spawn.typeId);
        writeValue<uint16_t>(bytes, spawnOffset + 0x10, spawn.index);
        writeValue<uint16_t>(bytes, spawnOffset + 0x12, spawn.attributes);
        writeValue<uint32_t>(bytes, spawnOffset + 0x14, spawn.group);
    }

    appendInt32(bytes, static_cast<int32_t>(indoorMapData.outlines.size()));

    for (const IndoorOutline &outline : indoorMapData.outlines)
    {
        appendUInt16(bytes, outline.vertex1Id);
        appendUInt16(bytes, outline.vertex2Id);
        appendUInt16(bytes, outline.face1Id);
        appendUInt16(bytes, outline.face2Id);
        appendInt16(bytes, outline.z);
        appendUInt16(bytes, outline.flags);
    }

    return bytes;
}
}
