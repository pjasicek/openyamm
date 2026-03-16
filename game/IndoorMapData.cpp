#include "game/IndoorMapData.h"

#include <array>
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

class ByteReader
{
public:
    explicit ByteReader(const std::vector<uint8_t> &bytes)
        : m_bytes(bytes)
    {
    }

    size_t size() const
    {
        return m_bytes.size();
    }

    bool canRead(size_t offset, size_t byteCount) const
    {
        if (offset > m_bytes.size())
        {
            return false;
        }

        return byteCount <= (m_bytes.size() - offset);
    }

    bool readInt32(size_t offset, int &value) const
    {
        if (!canRead(offset, sizeof(int32_t)))
        {
            return false;
        }

        int32_t rawValue = 0;
        std::memcpy(&rawValue, m_bytes.data() + offset, sizeof(rawValue));
        value = rawValue;
        return true;
    }

    bool readUInt16(size_t offset, uint16_t &value) const
    {
        if (!canRead(offset, sizeof(uint16_t)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readInt16(size_t offset, int16_t &value) const
    {
        if (!canRead(offset, sizeof(int16_t)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readUInt8(size_t offset, uint8_t &value) const
    {
        if (!canRead(offset, sizeof(uint8_t)))
        {
            return false;
        }

        value = m_bytes[offset];
        return true;
    }

    bool readUInt32(size_t offset, uint32_t &value) const
    {
        if (!canRead(offset, sizeof(uint32_t)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

private:
    const std::vector<uint8_t> &m_bytes;
};

struct VersionLayout
{
    int version = 0;
    size_t faceRecordSize = 0;
    size_t sectorRecordSize = 0;
    size_t spriteRecordSize = 0;
    size_t lightRecordSize = 0;
    size_t spawnRecordSize = 0;
};

std::string readTextureName(const ByteReader &reader, size_t offset)
{
    std::string textureName;
    textureName.reserve(TextureNameSize);

    for (size_t index = 0; index < TextureNameSize; ++index)
    {
        uint8_t character = 0;

        if (!reader.readUInt8(offset + index, character))
        {
            return {};
        }

        if (character == 0)
        {
            break;
        }

        if (character < 32 || character > 126)
        {
            break;
        }

        textureName.push_back(static_cast<char>(character));
    }

    while (!textureName.empty() && textureName.back() == ' ')
    {
        textureName.pop_back();
    }

    return textureName;
}

std::string readFixedString(const ByteReader &reader, size_t offset, size_t maxLength)
{
    std::string value;
    value.reserve(maxLength);

    for (size_t index = 0; index < maxLength; ++index)
    {
        uint8_t character = 0;

        if (!reader.readUInt8(offset + index, character))
        {
            return {};
        }

        if (character == 0)
        {
            break;
        }

        if (character < 32 || character > 126)
        {
            break;
        }

        value.push_back(static_cast<char>(character));
    }

    while (!value.empty() && value.back() == ' ')
    {
        value.pop_back();
    }

    return value;
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

    indoorMapData.faces.reserve(static_cast<size_t>(faceCount));

    size_t faceDataCursor = faceDataOffset;

    for (int faceIndex = 0; faceIndex < faceCount; ++faceIndex)
    {
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

        if (vertexPerFaceCount < 3)
        {
            continue;
        }

        IndoorFace face = {};
        face.attributes = attributes;
        face.isPortal = (attributes & 0x1u) != 0;
        face.roomNumber = roomNumber;
        face.roomBehindNumber = roomBehindNumber;
        face.facetType = facetType;
        face.textureName = readTextureName(
            reader,
            faceTextureNamesOffset + static_cast<size_t>(faceIndex) * TextureNameSize
        );

        face.vertexIndices.reserve(vertexPerFaceCount);
        face.textureUs.reserve(vertexPerFaceCount);
        face.textureVs.reserve(vertexPerFaceCount);

        const size_t streamStride = static_cast<size_t>(vertexPerFaceCount + 1) * sizeof(int16_t);

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
                break;
            }

            face.vertexIndices.push_back(vertexId);
            face.textureUs.push_back(textureU);
            face.textureVs.push_back(textureV);
        }

        faceDataCursor += streamStride * 6;

        if (face.vertexIndices.size() < 3)
        {
            continue;
        }

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

        indoorMapData.faces.push_back(face);
    }

    int sectorCount = 0;
    reader.readInt32(offset, sectorCount);
    indoorMapData.sectorCount = static_cast<size_t>(sectorCount);
    offset += sizeof(int32_t);

    indoorMapData.sectors.reserve(indoorMapData.sectorCount);

    for (size_t sectorIndex = 0; sectorIndex < indoorMapData.sectorCount; ++sectorIndex)
    {
        const size_t sectorOffset = offset + sectorIndex * layout->sectorRecordSize;
        IndoorSector sector = {};
        reader.readInt32(sectorOffset + 0x00, sector.flags);
        reader.readUInt16(sectorOffset + 0x04, sector.floorCount);
        reader.readUInt16(sectorOffset + 0x0c, sector.wallCount);
        reader.readUInt16(sectorOffset + 0x14, sector.ceilingCount);
        reader.readInt16(sectorOffset + 0x24, sector.portalCount);
        reader.readUInt16(sectorOffset + 0x2c, sector.faceCount);
        reader.readUInt16(sectorOffset + 0x2e, sector.nonBspFaceCount);
        reader.readUInt16(sectorOffset + 0x44, sector.decorationCount);
        reader.readUInt16(sectorOffset + 0x54, sector.lightCount);
        reader.readInt16(sectorOffset + 0x5c, sector.waterLevel);
        reader.readInt16(sectorOffset + 0x5e, sector.mistLevel);
        reader.readInt16(sectorOffset + 0x60, sector.lightDistanceMultiplier);
        reader.readInt16(sectorOffset + 0x62, sector.minAmbientLightLevel);
        reader.readInt16(sectorOffset + 0x64, sector.firstBspNode);
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
