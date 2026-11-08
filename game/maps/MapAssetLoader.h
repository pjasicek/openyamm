#pragma once

#include "engine/AssetFileSystem.h"
#include "engine/ImageAssetLoader.h"
#include "engine/render/CookedTexture.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/events/EventRuntime.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MapItemSourceData.h"
#include "game/maps/OutdoorTerrainTiles.h"
#include "game/indoor/IndoorMapData.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/ObjectTable.h"
#include "game/outdoor/OutdoorCollisionData.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorWeatherProfile.h"
#include "game/tables/SurfaceAnimation.h"
#include "game/tables/LiquidTable.h"
#include "game/tables/SpriteTables.h"
#include "game/tables/TextureFrameTable.h"

#include <algorithm>
#include <future>
#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class ActorModelManifest;

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
    // A liquids.yml texture: no art, the liquid shader draws its faces.
    LiquidKind liquid = LiquidKind::None;
    // ABGR tint of faces drawn by the liquid shader: the liquid's colour, or for a Fluid face of an ordinary texture
    // the texture's mean colour (those faces draw as water). 0: not drawn as a liquid.
    uint32_t waterColorAbgr = 0;
    std::vector<uint8_t> pixels;
    // A cooked world surface texture (GPU blocks with its mip chain) replaces pixels; see loadCookedSurfaceTexture.
    std::shared_ptr<const Engine::CookedTexture> cookedTexture;
    // Its surface material maps (devdocs/SURFACE_MATERIALS_PLAN.md), cooked beside it: the normal map (tangent-space
    // x and y, glow) and the detail map (occlusion, roughness, metal, height). Both or neither.
    std::shared_ptr<const Engine::CookedTexture> materialNormal;
    std::shared_ptr<const Engine::CookedTexture> materialDetail;
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
    // Indoors: the map light beside this torch lights further, so the decoration leaves the lighting to it
    // (resolveDuplicateTorchLights).
    bool litByMapLight = false;
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
    // Sprites a 3D model draws on this map (DecorationModelSet bindings): their textures are never loaded.
    std::unordered_set<uint16_t> modelSpriteIds;
    // Indoors, by map light id: a torch decoration beside the light reaches at least as far and lights in its place
    // (resolveDuplicateTorchLights).
    std::vector<bool> mapLightsReplacedByDecorations;

    bool mapLightReplaced(size_t lightId) const
    {
        return lightId < mapLightsReplacedByDecorations.size() && mapLightsReplacedByDecorations[lightId];
    }
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
    // An actor model draws this monster.
    bool modelled = false;
    ActorPreviewSource source = ActorPreviewSource::Spawn;
    std::string actorName;
};

struct ActorPreviewBillboardSet
{
    // True when an actor model draws this monster: none of its sprites is loaded.
    bool drawsModel(const MonsterEntry *pMonster) const;
    // The same by monster id: renderers never fall back to the sprite of such a monster, even before its model exists.
    bool drawsModel(int16_t monsterId) const;

    SpriteFrameTable spriteFrameTable;
    std::vector<OutdoorBitmapTexture> textures;
    std::vector<ActorPreviewBillboard> billboards;
    // Null while actor models are off.
    std::shared_ptr<const ActorModelManifest> actorModels;
    // Bound monsters the map shows when it loads or can summon (placed actors, spawns, every tier of its encounter
    // slots): their models are built under the loading screen instead of on first sight.
    std::vector<std::string> modelDescriptors;
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
    // The active ruleset's package directory: its maps/<map>_*.scene.yml overlays apply after the world's.
    std::string rulesetRoot;
    // Whether face textures load their surface material maps (video.surface_materials); off, nothing of them is read
    // or kept.
    bool surfaceMaterials = false;
};

struct MapAssetBitmapPixelsResult
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
    // The tier of the file the pixels were decoded from, which sets their logical size.
    Engine::AssetScaleTier assetScaleTier = Engine::AssetScaleTier::X1;
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
    // What a saved state of this map is laid out against (game/maps/MapLayoutIdentity.h), computed when it loads.
    uint64_t layoutIdentity = 0;
    std::optional<OutdoorMapData> outdoorMapData;
    std::optional<IndoorMapData> indoorMapData;
    // Per indoor face: the party's speed share while it wades on it (a shallow liquid's wade_speed); empty when the
    // map has no such face.
    std::vector<float> indoorFaceWadeSpeeds;
    std::optional<MapDeltaData> outdoorMapDeltaData;
    std::optional<MapDeltaData> indoorMapDeltaData;
    std::optional<MapItemSourceData> itemSourceData;
    std::optional<OutdoorWeatherProfile> outdoorWeatherProfile;
    std::optional<ScriptedEventProgram> localEventProgram;
    std::optional<ScriptedEventProgram> globalEventProgram;
    std::optional<EventRuntimeState> eventRuntimeState;
    std::optional<std::vector<uint8_t>> outdoorLandMask;
    std::optional<std::vector<uint32_t>> outdoorTileColors;
    std::optional<OutdoorTerrainTiles> outdoorTerrainTiles;
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
// MM6 maps place a map light 64 units from each torch (radius 4 to 1024) while the torch decoration also carries the
// decoration table's light (mostly 256): together they light it about twice as brightly. Each map light with a radius
// claims the nearest unclaimed light-emitting decoration within 128 units, and only the one of the pair that reaches
// further lights: the decoration on a tie, since it follows the torch's state. MM7 map lights have no radius and MM8
// places none beside its torches, so their lights are unchanged.
void resolveDuplicateTorchLights(const IndoorMapData &indoorMapData, DecorationBillboardSet &billboardSet);
// Whether any of a map's face textures carries surface material maps: they load only with video.surface_materials
// on, and the renderers load the material programs only for such a map.
bool hasSurfaceMaterialMaps(const std::vector<OutdoorBitmapTexture> &textures);
// A world surface texture (Data/bitmaps) whose best match in the active scale tier is its cooked file
// (tools/cook_surface_textures.py): GPU blocks with the runtime's mip chain and the source's statistics, so nothing is
// decoded, keyed or filtered at load. Empty when the best match is a source image. Throws on a corrupt cooked file
// or one cooked for another use; it is never replaced by its source.
std::optional<OutdoorBitmapTexture> loadCookedSurfaceTexture(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    Engine::DirectoryAssetPathCache &directoryAssetPathsByPath,
    Engine::AssetPathLookupCache &assetPathByKey,
    Engine::BinaryAssetCache *pBinaryFilesByPath);
// A world surface texture (Data/bitmaps) loaded by name after the map: its cooked file when the active tier has one,
// else its source image. Empty when neither exists. For a face whose texture an event swaps in (evt.SetTexture) and
// no face of the map uses.
std::optional<OutdoorBitmapTexture> loadSurfaceTexture(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName);
// A summoned monster's frames, and those of the tier its model is sized from (pActorModels: scale_reference).
bool ensureMonsterSpriteFramesLoaded(
    const Engine::AssetFileSystem &assetFileSystem,
    const MonsterTable &monsterTable,
    int16_t monsterId,
    SpriteFrameTable &spriteFrameTable,
    const ActorModelManifest *pActorModels = nullptr);

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
    std::optional<LiquidTable> liquidTable;
    std::optional<SpriteFrameTable> commonSpriteFrameTable;
    // The common table's parse on a load worker, started when a load begins without the table (MapAssetLoader::load).
    std::shared_future<std::optional<SpriteFrameTable>> commonSpriteFrameTableLoading;
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
        MapAssetLoadSharedCache *pSharedCache = nullptr,
        std::shared_ptr<const ActorModelManifest> pActorModels = {}
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
