#pragma once

#include "engine/AssetFileSystem.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/events/EventRuntime.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MapItemSourceData.h"
#include "game/indoor/IndoorMapData.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/ObjectTable.h"
#include "game/outdoor/OutdoorCollisionData.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorWeatherProfile.h"
#include "game/tables/SurfaceAnimation.h"
#include "game/tables/SurfaceMaterialTable.h"
#include "game/tables/SpriteTables.h"
#include "game/tables/TextureFrameTable.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
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
    bool isWater = false;
    // Some native lava tiles also carry the Water flag; keep their legacy animation without water shading.
    bool isWaterSurface = false;
    bool isTransitionOverlay = false;
    uint32_t waterColorAbgr = 0;
};

struct OutdoorAnimatedWaterTileSource
{
    OutdoorTerrainAtlasRegion region;
    std::vector<std::vector<uint8_t>> framePixels;
    SurfaceAnimationSequence animation;
    size_t currentFrameIndex = 0;
};

struct OutdoorTerrainTextureAtlas
{
    int width = 0;
    int height = 0;
    int tileSize = 0;
    int tilePadding = 0;
    std::vector<uint8_t> pixels;
    std::array<OutdoorTerrainAtlasRegion, 256> tileRegions = {};
    std::array<std::string, 256> tileTextureNames = {};
    std::vector<OutdoorAnimatedWaterTileSource> animatedWaterTiles;
    std::array<std::vector<uint8_t>, 256> waterCoverageMasks;
};

struct OutdoorBitmapTexture
{
    std::string textureName;
    int16_t paletteId = 0;
    int width = 0;
    int height = 0;
    int physicalWidth = 0;
    int physicalHeight = 0;
    bool hasTransparentPixels = false;
    bool hasPartialAlphaPixels = false;
    bool pixelsPreparedForUpload = false;
    SurfaceMaterialSemantic surfaceSemantic = SurfaceMaterialSemantic::GenericAnimated;
    uint32_t waterColorAbgr = 0;
    std::vector<uint8_t> pixels;
    // Explicit source identity for map-local art that overrides a shared sprite name.
    std::string resourceIdentity;
};

struct OutdoorBModelTextureSet
{
    std::vector<OutdoorBitmapTexture> textures;
    std::vector<std::pair<std::string, SurfaceAnimationSequence>> animationBindings;
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
    uint16_t eventIdPrimary = 0;
    uint16_t eventIdSecondary = 0;
    int16_t sectorId = -1;
    std::string name;

    uint32_t spriteOverrideKey() const
    {
        return eventIdPrimary != 0 ? eventIdPrimary : static_cast<uint32_t>(entityIndex);
    }
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
    size_t runtimeActorIndex = static_cast<size_t>(-1);
    uint16_t spriteFrameIndex = 0;
    std::array<uint16_t, 8> actionSpriteFrameIndices = {};
    int16_t npcId = 0;
    int16_t monsterId = 0;
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
    std::vector<std::pair<std::string, SurfaceAnimationSequence>> animationBindings;
};

enum class AuthoredCompanionSource
{
    None,
    LegacyCompanion,
    SceneYml,
};

struct MapCompanionLoadOptions
{
    bool allowSceneYml = true;
    bool allowLegacyCompanion = true;
};

struct MapAssetBitmapPixelsResult
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};

struct MapAssetInfo
{
    MapStatsEntry map;
    std::string geometryPath;
    size_t geometrySize;
    std::vector<uint8_t> geometryHeader;
    std::optional<std::string> companionPath;
    std::optional<size_t> companionSize;
    std::optional<std::string> scenePath;
    std::optional<size_t> sceneSize;
    std::optional<std::string> navigationPath;
    std::optional<size_t> navigationSize;
    std::optional<std::string> renderDataPath;
    std::optional<size_t> renderDataSize;
    std::optional<std::string> lightingDataPath;
    std::optional<size_t> lightingDataSize;
    AuthoredCompanionSource authoredCompanionSource = AuthoredCompanionSource::None;
    std::optional<OutdoorMapData> outdoorMapData;
    std::optional<IndoorMapData> indoorMapData;
    std::optional<MapDeltaData> outdoorMapDeltaData;
    std::optional<MapDeltaData> indoorMapDeltaData;
    std::optional<MapItemSourceData> itemSourceData;
    std::optional<OutdoorWeatherProfile> outdoorWeatherProfile;
    std::optional<ScriptedEventProgram> localEventProgram;
    std::optional<ScriptedEventProgram> globalEventProgram;
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

size_t mapRenderSourcePixelBytes(const MapAssetInfo &mapAssetInfo);
void clearMapRenderSourcePixels(MapAssetInfo &mapAssetInfo);
bool ensureMonsterSpriteFramesLoaded(
    const Engine::AssetFileSystem &assetFileSystem,
    const MonsterTable &monsterTable,
    int16_t monsterId,
    SpriteFrameTable &spriteFrameTable);

enum class MapLoadPurpose
{
    Full,
    FullGameplay,
    HeadlessGameplay,
    RenderSurfaces,
    ActorPreviews,
    BillboardPreviews,
    // Decoration billboards for the lighting bake's decoration export: everything the bake needs, without the baked
    // lighting itself (which it is about to replace, and which may be stale).
    DecorationPlacements,
};

using MapLoadProgressPump = std::function<void()>;

struct MapAssetLoadSharedCache
{
#if defined(__ANDROID__)
    static constexpr size_t BitmapRetentionBudget = 32 * 1024 * 1024;
#else
    static constexpr size_t BitmapRetentionBudget = 128 * 1024 * 1024;
#endif
    std::optional<std::vector<std::vector<std::string>>> decorationRows;
    std::optional<TextureFrameTable> textureFrameTable;
    std::optional<SurfaceMaterialTable> surfaceMaterialTable;
    std::optional<SpriteFrameTable> commonSpriteFrameTable;
    std::optional<std::vector<std::string>> monsterSpriteFrameFamilyEntries;
    std::unordered_map<std::string, std::optional<std::string>> monsterSpriteFrameFamilyTextByRoot;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> bitmapDirectoryAssetPathsByPath;
    std::unordered_map<std::string, std::optional<std::string>> bitmapPathByKey;
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> bitmapBinaryFilesByPath;
    std::unordered_map<std::string, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesByKey;
    std::unordered_map<std::string, std::optional<MapAssetBitmapPixelsResult>> bitmapPixelsByKey;
    std::unordered_map<std::string, uint64_t> bitmapLastUse;
    uint64_t bitmapUseSerial = 0;
    uint64_t contentGeneration = 0;

    void beginLoad(uint64_t generation)
    {
        if (contentGeneration != generation)
        {
            *this = {};
            contentGeneration = generation;
        }
    }

    void touchBitmap(const std::string &key)
    {
        bitmapLastUse[key] = ++bitmapUseSerial;
    }

    size_t retainedBitmapBytes() const
    {
        size_t bytes = 0;
        for (const auto &[key, image] : bitmapPixelsByKey)
        {
            bytes += image ? image->pixels.size() : 0;
        }
        return bytes;
    }

    void trimBitmapData(size_t budget = BitmapRetentionBudget)
    {
        bitmapBinaryFilesByPath.clear();
        size_t bytes = retainedBitmapBytes();
        if (bytes <= budget)
        {
            return;
        }
        std::vector<std::pair<uint64_t, std::string>> oldest;
        oldest.reserve(bitmapPixelsByKey.size());
        for (const auto &[key, image] : bitmapPixelsByKey)
        {
            oldest.emplace_back(bitmapLastUse[key], key);
        }
        std::sort(oldest.begin(), oldest.end());
        for (const auto &[serial, key] : oldest)
        {
            const std::optional<MapAssetBitmapPixelsResult> &image = bitmapPixelsByKey.at(key);
            bytes -= image ? image->pixels.size() : 0;
            bitmapPixelsByKey.erase(key);
            bitmapLastUse.erase(key);
            if (bytes <= budget)
            {
                break;
            }
        }
    }
};

class MapAssetLoader
{
public:
    std::optional<MapAssetInfo> load(
        const Engine::AssetFileSystem &assetFileSystem,
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const ObjectTable &objectTable,
        MapLoadPurpose purpose = MapLoadPurpose::Full,
        const MapCompanionLoadOptions &companionLoadOptions = {},
        const MapLoadProgressPump &progressPump = {},
        MapAssetLoadSharedCache *pSharedCache = nullptr
    ) const;

private:
    static std::string toLower(const std::string &value);
    static std::optional<std::string> findAssetPathInDirectory(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &directoryPath,
        const std::string &fileName
    );
    static std::optional<std::string> findAssetPath(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &worldId,
        const std::string &fileName
    );
    static std::optional<std::string> findCompanionAssetPath(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &worldId,
        const std::string &fileName
    );
    static std::optional<std::string> buildCompanionFileName(const std::string &fileName);
    static std::optional<std::string> buildSceneFileName(const std::string &fileName);
    static std::optional<std::string> buildNavigationFileName(const std::string &fileName);
    static std::optional<std::string> buildRenderDataFileName(const std::string &fileName);
    static std::optional<std::string> buildLightingDataFileName(const std::string &fileName);
};
}
