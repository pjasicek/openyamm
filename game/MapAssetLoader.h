#pragma once

#include "engine/AssetFileSystem.h"
#include "game/EventIr.h"
#include "game/EventRuntime.h"
#include "game/EvtProgram.h"
#include "game/MapDeltaData.h"
#include "game/IndoorMapData.h"
#include "game/MapStats.h"
#include "game/MonsterTable.h"
#include "game/ObjectTable.h"
#include "game/OutdoorCollisionData.h"
#include "game/OutdoorMapData.h"
#include "game/SpriteTables.h"
#include "game/StrTable.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorTerrainAtlasRegion
{
    float u0 = 0.0f;
    float v0 = 0.0f;
    float u1 = 0.0f;
    float v1 = 0.0f;
    bool isValid = false;
};

struct OutdoorTerrainTextureAtlas
{
    int width = 0;
    int height = 0;
    int tileSize = 0;
    std::vector<uint8_t> pixels;
    std::array<OutdoorTerrainAtlasRegion, 256> tileRegions = {};
};

struct OutdoorBitmapTexture
{
    std::string textureName;
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};

struct OutdoorBModelTextureSet
{
    std::vector<OutdoorBitmapTexture> textures;
};

struct DecorationBillboard
{
    size_t entityIndex = 0;
    uint16_t decorationId = 0;
    uint16_t spriteId = 0;
    uint16_t flags = 0;
    uint16_t height = 0;
    int16_t radius = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    int facing = 0;
    std::string name;
};

struct DecorationBillboardSet
{
    DecorationTable decorationTable;
    SpriteFrameTable spriteFrameTable;
    std::vector<OutdoorBitmapTexture> textures;
    std::vector<DecorationBillboard> billboards;
};

enum class ActorPreviewSource
{
    Spawn,
    Companion,
};

struct ActorPreviewBillboard
{
    size_t spawnIndex = 0;
    uint16_t spriteFrameIndex = 0;
    int16_t npcId = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint16_t typeId = 0;
    uint16_t index = 0;
    uint16_t attributes = 0;
    uint32_t group = 0;
    int32_t uniqueNameIndex = 0;
    bool useStaticFrame = false;
    bool isFriendly = false;
    ActorPreviewSource source = ActorPreviewSource::Spawn;
    std::string actorName;
};

struct ActorPreviewBillboardSet
{
    SpriteFrameTable spriteFrameTable;
    std::vector<OutdoorBitmapTexture> textures;
    std::vector<ActorPreviewBillboard> billboards;
    size_t mapDeltaActorCount = 0;
    size_t spawnActorCount = 0;
    size_t texturedActorCount = 0;
    size_t missingTextureActorCount = 0;
};

struct SpriteObjectBillboard
{
    size_t index = 0;
    uint16_t spriteFrameIndex = 0;
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t attributes = 0;
    uint16_t soundId = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    int16_t radius = 0;
    int16_t height = 0;
    int16_t sectorId = 0;
    int16_t temporaryLifetime = 0;
    int16_t glowRadiusMultiplier = 0;
    int32_t spellId = 0;
    int32_t spellLevel = 0;
    int32_t spellSkill = 0;
    int32_t spellCasterPid = 0;
    int32_t spellTargetPid = 0;
    uint32_t timeSinceCreatedTicks = 0;
    std::string objectName;
};

struct SpriteObjectBillboardSet
{
    SpriteFrameTable spriteFrameTable;
    std::vector<OutdoorBitmapTexture> textures;
    std::vector<SpriteObjectBillboard> billboards;
    size_t texturedObjectCount = 0;
    size_t missingTextureObjectCount = 0;
};

struct IndoorTextureSet
{
    std::vector<OutdoorBitmapTexture> textures;
};

struct MapAssetInfo
{
    MapStatsEntry map;
    std::string geometryPath;
    size_t geometrySize;
    std::vector<uint8_t> geometryHeader;
    std::optional<std::string> companionPath;
    std::optional<size_t> companionSize;
    std::optional<OutdoorMapData> outdoorMapData;
    std::optional<IndoorMapData> indoorMapData;
    std::optional<MapDeltaData> outdoorMapDeltaData;
    std::optional<MapDeltaData> indoorMapDeltaData;
    std::optional<StrTable> localStrTable;
    std::optional<EvtProgram> localEvtProgram;
    std::optional<EvtProgram> globalEvtProgram;
    std::optional<EventIrProgram> localEventIrProgram;
    std::optional<EventIrProgram> globalEventIrProgram;
    std::optional<EventRuntimeState> eventRuntimeState;
    std::optional<std::vector<uint8_t>> outdoorLandMask;
    std::optional<std::vector<uint32_t>> outdoorTileColors;
    std::optional<OutdoorTerrainTextureAtlas> outdoorTerrainTextureAtlas;
    std::optional<OutdoorBModelTextureSet> outdoorBModelTextureSet;
    std::optional<OutdoorDecorationCollisionSet> outdoorDecorationCollisionSet;
    std::optional<OutdoorActorCollisionSet> outdoorActorCollisionSet;
    std::optional<OutdoorSpriteObjectCollisionSet> outdoorSpriteObjectCollisionSet;
    std::optional<DecorationBillboardSet> outdoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> outdoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> outdoorSpriteObjectBillboardSet;
    std::optional<DecorationBillboardSet> indoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> indoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> indoorSpriteObjectBillboardSet;
    std::optional<IndoorTextureSet> indoorTextureSet;
};

class MapAssetLoader
{
public:
    std::optional<MapAssetInfo> load(
        const Engine::AssetFileSystem &assetFileSystem,
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const ObjectTable &objectTable
    ) const;

private:
    static std::string toLower(const std::string &value);
    static std::optional<std::string> findAssetPath(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &fileName
    );
    static std::optional<std::string> buildCompanionFileName(const std::string &fileName);
};
}
