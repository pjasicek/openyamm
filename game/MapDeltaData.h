#pragma once

#include "game/IndoorMapData.h"
#include "game/OutdoorMapData.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct MapDeltaLocationInfo
{
    int32_t respawnCount = 0;
    int32_t lastRespawnDay = 0;
    int32_t reputation = 0;
    int32_t alertStatus = 0;
    uint32_t totalFacesCount = 0;
    uint32_t decorationCount = 0;
    uint32_t bmodelCount = 0;
};

struct MapDeltaPersistentVariables
{
    std::array<uint8_t, 75> mapVars = {};
    std::array<uint8_t, 125> decorVars = {};
};

struct MapDeltaLocationTime
{
    int64_t lastVisitTime = 0;
    std::string skyTextureName;
    int32_t weatherFlags = 0;
    int32_t fogWeakDistance = 0;
    int32_t fogStrongDistance = 0;
    std::array<uint8_t, 24> reserved = {};
};

struct MapDeltaActor
{
    std::string name;
    int16_t npcId = 0;
    uint32_t attributes = 0;
    int16_t hp = 0;
    uint8_t hostilityType = 0;
    int16_t monsterInfoId = 0;
    int16_t monsterId = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint16_t moveSpeed = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    std::array<uint16_t, 4> spriteIds = {};
    int16_t sectorId = 0;
    uint16_t currentActionAnimation = 0;
    uint32_t group = 0;
    uint32_t ally = 0;
    int32_t uniqueNameIndex = 0;
};

struct MapDeltaSpriteObject
{
    uint16_t spriteId = 0;
    uint16_t objectDescriptionId = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    int16_t velocityX = 0;
    int16_t velocityY = 0;
    int16_t velocityZ = 0;
    uint16_t yawAngle = 0;
    uint16_t soundId = 0;
    uint16_t attributes = 0;
    int16_t sectorId = 0;
    uint16_t timeSinceCreated = 0;
    int16_t temporaryLifetime = 0;
    int16_t glowRadiusMultiplier = 0;
    int32_t spellId = 0;
    int32_t spellLevel = 0;
    int32_t spellSkill = 0;
    int32_t field54 = 0;
    int32_t spellCasterPid = 0;
    int32_t spellTargetPid = 0;
    int8_t lodDistance = 0;
    int8_t spellCasterAbility = 0;
    int initialX = 0;
    int initialY = 0;
    int initialZ = 0;
    std::vector<uint8_t> rawContainingItem;
};

struct MapDeltaChest
{
    uint16_t chestTypeId = 0;
    uint16_t flags = 0;
    std::vector<uint8_t> rawItems;
    std::vector<int16_t> inventoryMatrix;
};

struct MapDeltaDoor
{
    uint32_t slotIndex = 0;
    uint32_t attributes = 0;
    uint32_t doorId = 0;
    uint32_t timeSinceTriggered = 0;
    int directionX = 0;
    int directionY = 0;
    int directionZ = 0;
    uint32_t moveLength = 0;
    uint32_t openSpeed = 0;
    uint32_t closeSpeed = 0;
    uint16_t numVertices = 0;
    uint16_t numFaces = 0;
    uint16_t numSectors = 0;
    uint16_t numOffsets = 0;
    uint16_t state = 0;
    std::vector<uint16_t> vertexIds;
    std::vector<uint16_t> faceIds;
    std::vector<uint16_t> sectorIds;
    std::vector<int16_t> deltaUs;
    std::vector<int16_t> deltaVs;
    std::vector<int16_t> xOffsets;
    std::vector<int16_t> yOffsets;
    std::vector<int16_t> zOffsets;
};

struct MapDeltaData
{
    MapDeltaLocationInfo locationInfo = {};
    std::vector<uint8_t> fullyRevealedCells;
    std::vector<uint8_t> partiallyRevealedCells;
    std::vector<uint8_t> visibleOutlines;
    std::vector<uint32_t> faceAttributes;
    std::vector<uint16_t> decorationFlags;
    std::vector<MapDeltaActor> actors;
    std::vector<MapDeltaSpriteObject> spriteObjects;
    std::vector<MapDeltaChest> chests;
    uint32_t doorSlotCount = 0;
    std::vector<MapDeltaDoor> doors;
    std::vector<int16_t> doorsData;
    MapDeltaPersistentVariables eventVariables = {};
    MapDeltaLocationTime locationTime = {};
};

class MapDeltaDataLoader
{
public:
    std::optional<MapDeltaData> loadOutdoorFromBytes(
        const std::vector<uint8_t> &bytes,
        const OutdoorMapData &outdoorMapData
    ) const;
    std::optional<MapDeltaData> loadIndoorFromBytes(
        const std::vector<uint8_t> &bytes,
        const IndoorMapData &indoorMapData
    ) const;
};
}
