#include "game/MapDeltaData.h"

#include <algorithm>
#include <cctype>
#include <cstring>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t OutdoorRevealMapBytes = 88 * 11 * 2;
constexpr size_t IndoorVisibleOutlinesBytes = 875;
constexpr size_t LocationHeaderSize = 40;
constexpr size_t ActorRecordSize = 0x3cc;
constexpr size_t SpriteObjectRecordSize = 0x70;
constexpr size_t ChestRecordSize = 5324;
constexpr size_t DoorRecordSize = 0x50;
constexpr size_t PersistentVariablesSize = 0xc8;
constexpr size_t LocationTimeSize = 0x38;
constexpr size_t ActorNameSize = 32;
constexpr size_t SpriteObjectContainingItemOffset = 0x1c;
constexpr size_t SpriteObjectContainingItemSize = 0x30;
constexpr size_t ChestItemsOffset = 0x04;
constexpr size_t ChestItemsSize = 140 * 36;
constexpr size_t ChestInventoryMatrixOffset = ChestItemsOffset + ChestItemsSize;
constexpr size_t ActorNpcIdOffset = 0x20;
constexpr size_t ActorAttributesOffset = 0x24;
constexpr size_t ActorHpOffset = 0x28;
constexpr size_t ActorHostilityTypeOffset = 0x2c;
constexpr size_t ActorMonsterInfoIdOffset = 0x6a;
constexpr size_t ActorMonsterIdOffset = 0x7c;
constexpr size_t ActorRadiusOffset = 0x90;
constexpr size_t ActorHeightOffset = 0x92;
constexpr size_t ActorMoveSpeedOffset = 0x94;
constexpr size_t ActorPositionOffset = 0x96;
constexpr size_t ActorSpriteIdsOffset = 0xd4;
constexpr size_t ActorSectorIdOffset = 0xdc;
constexpr size_t ActorCurrentActionAnimationOffset = 0xde;
constexpr size_t ActorAllyOffset = 0x340;
constexpr size_t ActorGroupOffset = 0x34c;
constexpr size_t ActorUniqueNameIndexOffset = 0x3bc;
constexpr uint32_t TicksPerRealtimeSecond = 128;

uint32_t ticksToRealtimeMilliseconds(uint32_t ticks)
{
    return ticks * 1000u / TicksPerRealtimeSecond;
}

class ByteReader
{
public:
    explicit ByteReader(const std::vector<uint8_t> &bytes)
        : m_bytes(bytes)
    {
    }

    bool canRead(size_t offset, size_t byteCount) const
    {
        if (offset > m_bytes.size())
        {
            return false;
        }

        return byteCount <= (m_bytes.size() - offset);
    }

    bool readUInt32(size_t offset, uint32_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readInt64(size_t offset, int64_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readBytes(size_t offset, size_t byteCount, std::vector<uint8_t> &target) const
    {
        if (!canRead(offset, byteCount))
        {
            return false;
        }

        target.assign(
            m_bytes.begin() + static_cast<ptrdiff_t>(offset),
            m_bytes.begin() + static_cast<ptrdiff_t>(offset + byteCount));
        return true;
    }

    bool readInt32(size_t offset, int32_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readUInt16(size_t offset, uint16_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readInt16(size_t offset, int16_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readUInt8(size_t offset, uint8_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        value = m_bytes[offset];
        return true;
    }

    bool readInt8(size_t offset, int8_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        value = static_cast<int8_t>(m_bytes[offset]);
        return true;
    }

    std::string readFixedString(size_t offset, size_t maxLength) const
    {
        if (!canRead(offset, maxLength))
        {
            return {};
        }

        std::string value;
        value.reserve(maxLength);

        for (size_t index = 0; index < maxLength; ++index)
        {
            const char character = static_cast<char>(m_bytes[offset + index]);

            if (character == '\0')
            {
                break;
            }

            if (!std::isprint(static_cast<unsigned char>(character)))
            {
                break;
            }

            value.push_back(character);
        }

        while (!value.empty() && value.back() == ' ')
        {
            value.pop_back();
        }

        return value;
    }

private:
    const std::vector<uint8_t> &m_bytes;
};

bool readLocationHeader(const ByteReader &reader, MapDeltaLocationInfo &locationInfo)
{
    return reader.readInt32(0x00, locationInfo.respawnCount)
        && reader.readInt32(0x04, locationInfo.lastRespawnDay)
        && reader.readInt32(0x08, locationInfo.reputation)
        && reader.readInt32(0x0c, locationInfo.alertStatus)
        && reader.readUInt32(0x10, locationInfo.totalFacesCount)
        && reader.readUInt32(0x14, locationInfo.decorationCount)
        && reader.readUInt32(0x18, locationInfo.bmodelCount);
}

bool parseActorVector(const ByteReader &reader, size_t offset, MapDeltaData &mapDeltaData)
{
    uint32_t actorCount = 0;

    if (!reader.readUInt32(offset, actorCount))
    {
        return false;
    }

    const size_t actorDataOffset = offset + sizeof(uint32_t);

    if (!reader.canRead(actorDataOffset, static_cast<size_t>(actorCount) * ActorRecordSize))
    {
        return false;
    }

    mapDeltaData.actors.clear();
    mapDeltaData.actors.reserve(actorCount);

    for (uint32_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
    {
        const size_t actorOffset = actorDataOffset + static_cast<size_t>(actorIndex) * ActorRecordSize;
        MapDeltaActor actor = {};
        actor.name = reader.readFixedString(actorOffset, ActorNameSize);

        if (!reader.readInt16(actorOffset + ActorNpcIdOffset, actor.npcId)
            || !reader.readUInt32(actorOffset + ActorAttributesOffset, actor.attributes)
            || !reader.readInt16(actorOffset + ActorHpOffset, actor.hp)
            || !reader.readUInt8(actorOffset + ActorHostilityTypeOffset, actor.hostilityType)
            || !reader.readInt16(actorOffset + ActorMonsterInfoIdOffset, actor.monsterInfoId)
            || !reader.readInt16(actorOffset + ActorMonsterIdOffset, actor.monsterId)
            || !reader.readUInt16(actorOffset + ActorRadiusOffset, actor.radius)
            || !reader.readUInt16(actorOffset + ActorHeightOffset, actor.height)
            || !reader.readUInt16(actorOffset + ActorMoveSpeedOffset, actor.moveSpeed)
            || !reader.readInt16(actorOffset + ActorSectorIdOffset, actor.sectorId)
            || !reader.readUInt16(actorOffset + ActorCurrentActionAnimationOffset, actor.currentActionAnimation)
            || !reader.readUInt32(actorOffset + ActorAllyOffset, actor.ally)
            || !reader.readUInt32(actorOffset + ActorGroupOffset, actor.group)
            || !reader.readInt32(actorOffset + ActorUniqueNameIndexOffset, actor.uniqueNameIndex))
        {
            return false;
        }

        int16_t coordinateX = 0;
        int16_t coordinateY = 0;
        int16_t coordinateZ = 0;

        if (!reader.readInt16(actorOffset + ActorPositionOffset + 0, coordinateX)
            || !reader.readInt16(actorOffset + ActorPositionOffset + 2, coordinateY)
            || !reader.readInt16(actorOffset + ActorPositionOffset + 4, coordinateZ))
        {
            return false;
        }

        actor.x = coordinateX;
        actor.y = coordinateY;
        actor.z = coordinateZ;

        for (size_t spriteIndex = 0; spriteIndex < actor.spriteIds.size(); ++spriteIndex)
        {
            if (!reader.readUInt16(
                    actorOffset + ActorSpriteIdsOffset + spriteIndex * sizeof(uint16_t),
                    actor.spriteIds[spriteIndex]))
            {
                return false;
            }
        }

        mapDeltaData.actors.push_back(std::move(actor));
    }

    return true;
}

bool parseUInt32Vector(
    const ByteReader &reader,
    size_t offset,
    size_t count,
    std::vector<uint32_t> &target,
    size_t &nextOffset)
{
    if (!reader.canRead(offset, count * sizeof(uint32_t)))
    {
        return false;
    }

    target.clear();
    target.reserve(count);

    for (size_t index = 0; index < count; ++index)
    {
        uint32_t value = 0;

        if (!reader.readUInt32(offset + index * sizeof(uint32_t), value))
        {
            return false;
        }

        target.push_back(value);
    }

    nextOffset = offset + count * sizeof(uint32_t);
    return true;
}

bool parseUInt16Vector(
    const ByteReader &reader,
    size_t offset,
    size_t count,
    std::vector<uint16_t> &target,
    size_t &nextOffset)
{
    if (!reader.canRead(offset, count * sizeof(uint16_t)))
    {
        return false;
    }

    target.clear();
    target.reserve(count);

    for (size_t index = 0; index < count; ++index)
    {
        uint16_t value = 0;

        if (!reader.readUInt16(offset + index * sizeof(uint16_t), value))
        {
            return false;
        }

        target.push_back(value);
    }

    nextOffset = offset + count * sizeof(uint16_t);
    return true;
}

bool parseSpriteObjectVector(const ByteReader &reader, size_t offset, MapDeltaData &mapDeltaData, size_t &nextOffset)
{
    uint32_t spriteObjectCount = 0;

    if (!reader.readUInt32(offset, spriteObjectCount))
    {
        return false;
    }

    const size_t dataOffset = offset + sizeof(uint32_t);

    if (!reader.canRead(dataOffset, static_cast<size_t>(spriteObjectCount) * SpriteObjectRecordSize))
    {
        return false;
    }

    mapDeltaData.spriteObjects.clear();
    mapDeltaData.spriteObjects.reserve(spriteObjectCount);

    for (uint32_t objectIndex = 0; objectIndex < spriteObjectCount; ++objectIndex)
    {
        const size_t objectOffset = dataOffset + static_cast<size_t>(objectIndex) * SpriteObjectRecordSize;
        MapDeltaSpriteObject spriteObject = {};
        int16_t velocityX = 0;
        int16_t velocityY = 0;
        int16_t velocityZ = 0;

        if (!reader.readUInt16(objectOffset + 0x00, spriteObject.spriteId)
            || !reader.readUInt16(objectOffset + 0x02, spriteObject.objectDescriptionId)
            || !reader.readInt32(objectOffset + 0x04, spriteObject.x)
            || !reader.readInt32(objectOffset + 0x08, spriteObject.y)
            || !reader.readInt32(objectOffset + 0x0c, spriteObject.z)
            || !reader.readInt16(objectOffset + 0x10, velocityX)
            || !reader.readInt16(objectOffset + 0x12, velocityY)
            || !reader.readInt16(objectOffset + 0x14, velocityZ)
            || !reader.readUInt16(objectOffset + 0x16, spriteObject.yawAngle)
            || !reader.readUInt16(objectOffset + 0x18, spriteObject.soundId)
            || !reader.readUInt16(objectOffset + 0x1a, spriteObject.attributes)
            || !reader.readInt16(objectOffset + 0x1c, spriteObject.sectorId)
            || !reader.readUInt16(objectOffset + 0x1e, spriteObject.timeSinceCreated)
            || !reader.readInt16(objectOffset + 0x20, spriteObject.temporaryLifetime)
            || !reader.readInt16(objectOffset + 0x22, spriteObject.glowRadiusMultiplier)
            || !reader.readInt32(objectOffset + 0x4c, spriteObject.spellId)
            || !reader.readInt32(objectOffset + 0x50, spriteObject.spellLevel)
            || !reader.readInt32(objectOffset + 0x54, spriteObject.spellSkill)
            || !reader.readInt32(objectOffset + 0x58, spriteObject.field54)
            || !reader.readInt32(objectOffset + 0x5c, spriteObject.spellCasterPid)
            || !reader.readInt32(objectOffset + 0x60, spriteObject.spellTargetPid)
            || !reader.readInt8(objectOffset + 0x64, spriteObject.lodDistance)
            || !reader.readInt8(objectOffset + 0x65, spriteObject.spellCasterAbility))
        {
            return false;
        }
        spriteObject.velocityX = velocityX;
        spriteObject.velocityY = velocityY;
        spriteObject.velocityZ = velocityZ;

        if (!reader.readBytes(
                objectOffset + SpriteObjectContainingItemOffset,
                SpriteObjectContainingItemSize,
                spriteObject.rawContainingItem))
        {
            return false;
        }

        mapDeltaData.spriteObjects.push_back(std::move(spriteObject));
    }

    nextOffset = dataOffset + static_cast<size_t>(spriteObjectCount) * SpriteObjectRecordSize;
    return true;
}

bool parseChestVector(const ByteReader &reader, size_t offset, MapDeltaData &mapDeltaData, size_t &nextOffset)
{
    uint32_t chestCount = 0;

    if (!reader.readUInt32(offset, chestCount))
    {
        return false;
    }

    const size_t dataOffset = offset + sizeof(uint32_t);

    if (!reader.canRead(dataOffset, static_cast<size_t>(chestCount) * ChestRecordSize))
    {
        return false;
    }

    mapDeltaData.chests.clear();
    mapDeltaData.chests.reserve(chestCount);

    for (uint32_t chestIndex = 0; chestIndex < chestCount; ++chestIndex)
    {
        const size_t chestOffset = dataOffset + static_cast<size_t>(chestIndex) * ChestRecordSize;
        MapDeltaChest chest = {};

        if (!reader.readUInt16(chestOffset + 0x00, chest.chestTypeId)
            || !reader.readUInt16(chestOffset + 0x02, chest.flags)
            || !reader.readBytes(chestOffset + ChestItemsOffset, ChestItemsSize, chest.rawItems))
        {
            return false;
        }

        chest.inventoryMatrix.reserve(140);

        for (size_t itemIndex = 0; itemIndex < 140; ++itemIndex)
        {
            int16_t value = 0;

            if (!reader.readInt16(
                    chestOffset + ChestInventoryMatrixOffset + itemIndex * sizeof(int16_t),
                    value))
            {
                return false;
            }

            chest.inventoryMatrix.push_back(value);
        }

        mapDeltaData.chests.push_back(std::move(chest));
    }

    nextOffset = dataOffset + static_cast<size_t>(chestCount) * ChestRecordSize;
    return true;
}

bool parseDoors(
    const ByteReader &reader,
    size_t offset,
    const IndoorMapData &indoorMapData,
    MapDeltaData &mapDeltaData,
    size_t &nextOffset)
{
    const uint32_t doorCount = indoorMapData.doorCount;
    mapDeltaData.doorSlotCount = doorCount;
    const size_t doorDataOffset = offset;

    if (!reader.canRead(doorDataOffset, static_cast<size_t>(doorCount) * DoorRecordSize))
    {
        return false;
    }

    std::vector<MapDeltaDoor> doors;
    doors.reserve(doorCount);

    for (uint32_t doorIndex = 0; doorIndex < doorCount; ++doorIndex)
    {
        const size_t doorOffset = doorDataOffset + static_cast<size_t>(doorIndex) * DoorRecordSize;
        MapDeltaDoor door = {};
        door.slotIndex = doorIndex;
        int32_t directionX = 0;
        int32_t directionY = 0;
        int32_t directionZ = 0;

        if (!reader.readUInt32(doorOffset + 0x00, door.attributes)
            || !reader.readUInt32(doorOffset + 0x04, door.doorId)
            || !reader.readUInt32(doorOffset + 0x08, door.timeSinceTriggered)
            || !reader.readInt32(doorOffset + 0x0c, directionX)
            || !reader.readInt32(doorOffset + 0x10, directionY)
            || !reader.readInt32(doorOffset + 0x14, directionZ)
            || !reader.readUInt32(doorOffset + 0x18, door.moveLength)
            || !reader.readUInt32(doorOffset + 0x1c, door.openSpeed)
            || !reader.readUInt32(doorOffset + 0x20, door.closeSpeed)
            || !reader.readUInt16(doorOffset + 0x44, door.numVertices)
            || !reader.readUInt16(doorOffset + 0x46, door.numFaces)
            || !reader.readUInt16(doorOffset + 0x48, door.numSectors)
            || !reader.readUInt16(doorOffset + 0x4a, door.numOffsets)
            || !reader.readUInt16(doorOffset + 0x4c, door.state))
        {
            return false;
        }

        door.timeSinceTriggered = ticksToRealtimeMilliseconds(door.timeSinceTriggered);

        door.directionX = directionX;
        door.directionY = directionY;
        door.directionZ = directionZ;
        doors.push_back(std::move(door));
    }

    size_t dataVectorOffset = doorDataOffset + static_cast<size_t>(doorCount) * DoorRecordSize;
    const uint32_t doorsDataCount = static_cast<uint32_t>(std::max(indoorMapData.doorsDataSizeBytes, 0) / sizeof(int16_t));

    if (!reader.canRead(dataVectorOffset, static_cast<size_t>(doorsDataCount) * sizeof(int16_t)))
    {
        return false;
    }

    mapDeltaData.doorsData.clear();
    mapDeltaData.doorsData.reserve(doorsDataCount);

    for (uint32_t dataIndex = 0; dataIndex < doorsDataCount; ++dataIndex)
    {
        int16_t value = 0;

        if (!reader.readInt16(dataVectorOffset + static_cast<size_t>(dataIndex) * sizeof(int16_t), value))
        {
            return false;
        }

        mapDeltaData.doorsData.push_back(value);
    }

    size_t cursor = 0;

    for (MapDeltaDoor &door : doors)
    {
        const size_t requiredValues =
            static_cast<size_t>(door.numVertices)
            + static_cast<size_t>(door.numFaces)
            + static_cast<size_t>(door.numSectors)
            + static_cast<size_t>(door.numFaces) * 2
            + static_cast<size_t>(door.numOffsets) * 3;

        if (cursor + requiredValues > mapDeltaData.doorsData.size())
        {
            return false;
        }

        door.vertexIds.reserve(door.numVertices);
        for (uint16_t index = 0; index < door.numVertices; ++index)
        {
            door.vertexIds.push_back(static_cast<uint16_t>(mapDeltaData.doorsData[cursor++]));
        }

        door.faceIds.reserve(door.numFaces);
        for (uint16_t index = 0; index < door.numFaces; ++index)
        {
            door.faceIds.push_back(static_cast<uint16_t>(mapDeltaData.doorsData[cursor++]));
        }

        door.sectorIds.reserve(door.numSectors);
        for (uint16_t index = 0; index < door.numSectors; ++index)
        {
            door.sectorIds.push_back(static_cast<uint16_t>(mapDeltaData.doorsData[cursor++]));
        }

        door.deltaUs.reserve(door.numFaces);
        for (uint16_t index = 0; index < door.numFaces; ++index)
        {
            door.deltaUs.push_back(mapDeltaData.doorsData[cursor++]);
        }

        door.deltaVs.reserve(door.numFaces);
        for (uint16_t index = 0; index < door.numFaces; ++index)
        {
            door.deltaVs.push_back(mapDeltaData.doorsData[cursor++]);
        }

        door.xOffsets.reserve(door.numOffsets);
        for (uint16_t index = 0; index < door.numOffsets; ++index)
        {
            door.xOffsets.push_back(mapDeltaData.doorsData[cursor++]);
        }

        door.yOffsets.reserve(door.numOffsets);
        for (uint16_t index = 0; index < door.numOffsets; ++index)
        {
            door.yOffsets.push_back(mapDeltaData.doorsData[cursor++]);
        }

        door.zOffsets.reserve(door.numOffsets);
        for (uint16_t index = 0; index < door.numOffsets; ++index)
        {
            door.zOffsets.push_back(mapDeltaData.doorsData[cursor++]);
        }
    }

    std::vector<MapDeltaDoor> activeDoors;
    activeDoors.reserve(doors.size());

    for (MapDeltaDoor &door : doors)
    {
        const bool hasGeometry =
            door.numVertices > 0
            || door.numFaces > 0
            || door.numSectors > 0
            || door.numOffsets > 0;
        const bool hasIdentity = door.doorId != 0 || door.attributes != 0 || door.state != 0;

        if (!hasGeometry && !hasIdentity)
        {
            continue;
        }

        activeDoors.push_back(std::move(door));
    }

    mapDeltaData.doors = std::move(activeDoors);
    nextOffset = dataVectorOffset + static_cast<size_t>(doorsDataCount) * sizeof(int16_t);
    return true;
}

bool parsePersistentVariables(
    const ByteReader &reader,
    size_t offset,
    MapDeltaPersistentVariables &persistentVariables,
    size_t &nextOffset)
{
    std::vector<uint8_t> bytes;

    if (!reader.readBytes(offset, PersistentVariablesSize, bytes))
    {
        return false;
    }

    std::copy_n(bytes.begin(), persistentVariables.mapVars.size(), persistentVariables.mapVars.begin());
    std::copy_n(
        bytes.begin() + static_cast<ptrdiff_t>(persistentVariables.mapVars.size()),
        persistentVariables.decorVars.size(),
        persistentVariables.decorVars.begin());
    nextOffset = offset + PersistentVariablesSize;
    return true;
}

bool parseLocationTime(
    const ByteReader &reader,
    size_t offset,
    MapDeltaLocationTime &locationTime,
    size_t &nextOffset)
{
    if (!reader.readInt64(offset + 0x00, locationTime.lastVisitTime))
    {
        return false;
    }

    locationTime.skyTextureName = reader.readFixedString(offset + 0x08, 12);

    if (!reader.readInt32(offset + 0x14, locationTime.weatherFlags)
        || !reader.readInt32(offset + 0x18, locationTime.fogWeakDistance)
        || !reader.readInt32(offset + 0x1c, locationTime.fogStrongDistance))
    {
        return false;
    }

    std::vector<uint8_t> reserved;

    if (!reader.readBytes(offset + 0x20, locationTime.reserved.size(), reserved))
    {
        return false;
    }

    std::copy(reserved.begin(), reserved.end(), locationTime.reserved.begin());
    nextOffset = offset + LocationTimeSize;
    return true;
}

bool parseOutdoorTail(
    const ByteReader &reader,
    size_t offset,
    const OutdoorMapData &outdoorMapData,
    MapDeltaData &mapDeltaData)
{
    size_t totalFaceCount = 0;

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        totalFaceCount += bmodel.faces.size();
    }

    if (!reader.canRead(offset, OutdoorRevealMapBytes))
    {
        return false;
    }

    if (!reader.readBytes(offset, OutdoorRevealMapBytes / 2, mapDeltaData.fullyRevealedCells)
        || !reader.readBytes(offset + OutdoorRevealMapBytes / 2, OutdoorRevealMapBytes / 2, mapDeltaData.partiallyRevealedCells))
    {
        return false;
    }

    size_t nextOffset = offset + OutdoorRevealMapBytes;

    if (!parseUInt32Vector(
            reader,
            nextOffset,
            totalFaceCount,
            mapDeltaData.faceAttributes,
            nextOffset)
        || !parseUInt16Vector(
            reader,
            nextOffset,
            outdoorMapData.entities.size(),
            mapDeltaData.decorationFlags,
            nextOffset)
        || !parseActorVector(reader, nextOffset, mapDeltaData))
    {
        return false;
    }

    nextOffset += sizeof(uint32_t) + mapDeltaData.actors.size() * ActorRecordSize;

    const size_t spriteObjectOffset = nextOffset;

    if (parseSpriteObjectVector(reader, spriteObjectOffset, mapDeltaData, nextOffset)
        && parseChestVector(reader, nextOffset, mapDeltaData, nextOffset)
        && parsePersistentVariables(reader, nextOffset, mapDeltaData.eventVariables, nextOffset))
    {
        const size_t locationTimeOffset = nextOffset;
        size_t ignoredNextOffset = locationTimeOffset;
        parseLocationTime(reader, locationTimeOffset, mapDeltaData.locationTime, ignoredNextOffset);
    }

    return true;
}

bool parseIndoorTail(
    const ByteReader &reader,
    size_t offset,
    const IndoorMapData &indoorMapData,
    MapDeltaData &mapDeltaData)
{
    if (!reader.readBytes(offset, IndoorVisibleOutlinesBytes, mapDeltaData.visibleOutlines))
    {
        return false;
    }

    size_t nextOffset = offset + IndoorVisibleOutlinesBytes;

    if (!parseUInt32Vector(
            reader,
            nextOffset,
            indoorMapData.rawFaceCount,
            mapDeltaData.faceAttributes,
            nextOffset)
        || !parseUInt16Vector(
            reader,
            nextOffset,
            indoorMapData.entities.size(),
            mapDeltaData.decorationFlags,
            nextOffset)
        || !parseActorVector(reader, nextOffset, mapDeltaData))
    {
        return false;
    }

    nextOffset += sizeof(uint32_t) + mapDeltaData.actors.size() * ActorRecordSize;

    const size_t spriteObjectOffset = nextOffset;

    if (parseSpriteObjectVector(reader, spriteObjectOffset, mapDeltaData, nextOffset)
        && parseChestVector(reader, nextOffset, mapDeltaData, nextOffset)
        && parseDoors(reader, nextOffset, indoorMapData, mapDeltaData, nextOffset)
        && parsePersistentVariables(reader, nextOffset, mapDeltaData.eventVariables, nextOffset))
    {
        const size_t locationTimeOffset = nextOffset;
        size_t ignoredNextOffset = locationTimeOffset;
        parseLocationTime(reader, locationTimeOffset, mapDeltaData.locationTime, ignoredNextOffset);
    }

    return true;
}
}

std::optional<MapDeltaData> MapDeltaDataLoader::loadOutdoorFromBytes(
    const std::vector<uint8_t> &bytes,
    const OutdoorMapData &outdoorMapData
) const
{
    const ByteReader reader(bytes);
    MapDeltaData mapDeltaData = {};

    if (!readLocationHeader(reader, mapDeltaData.locationInfo))
    {
        return std::nullopt;
    }

    if (!parseOutdoorTail(reader, LocationHeaderSize, outdoorMapData, mapDeltaData))
    {
        return std::nullopt;
    }

    return mapDeltaData;
}

std::optional<MapDeltaData> MapDeltaDataLoader::loadIndoorFromBytes(
    const std::vector<uint8_t> &bytes,
    const IndoorMapData &indoorMapData
) const
{
    const ByteReader reader(bytes);
    MapDeltaData mapDeltaData = {};

    if (!readLocationHeader(reader, mapDeltaData.locationInfo))
    {
        return std::nullopt;
    }

    if (!parseIndoorTail(reader, LocationHeaderSize, indoorMapData, mapDeltaData))
    {
        return std::nullopt;
    }

    return mapDeltaData;
}
}
