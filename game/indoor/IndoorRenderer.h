#pragma once

#include <deque>

#include "game/render/SurfaceReflectionBinding.h"
#include "game/render/SpriteAtlasCache.h"
#include "game/render/NativeSpriteTextureCache.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/render/ModelRenderer.h"
#include "game/indoor/IndoorFaceDrawGroups.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/DecorationModelSet.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/render/IndoorStaticLighting.h"
#include "game/indoor/IndoorPortalGraph.h"
#include "game/indoor/IndoorPortalVisibility.h"
#include "game/indoor/IndoorPortalDebugView.h"
#include "game/indoor/IndoorTerrainSurface.h"
#include "game/indoor/IndoorOpenSkyWeather.h"
#include "game/outdoor/OutdoorMeadow.h"
#include "game/outdoor/TerrainBushSet.h"
#include "game/outdoor/TerrainDecorationRenderer.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ObjectTable.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MapAssetLoader.h"
#include "game/render/TerrainMaterialSet.h"
#include "game/render/TextureFiltering.h"
#include "game/render/WaterRenderer.h"
#include "game/render/SkyRenderer.h"
#include "game/render/BillboardOpacityMask.h"
#include "game/tables/ItemTable.h"
#include "game/fx/WorldFxRenderResources.h"
#include "game/fx/WorldFxSystem.h"
#include "game/fx/EffectRenderer.h"
#include "game/fx/MistWisps.h"
#include "game/render/ShieldDomeRenderer.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/tables/HouseTable.h"
#include "game/ui/EnemyHealthBarRenderer.h"
#include "game/ui/GameplayHudCommon.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <array>
#include <cstdint>
#include <functional>
#include <limits>
#include <optional>
#include <string>
#include <span>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class CinematicGrading;
class GameSession;
struct GameSettings;
struct GameplayInputFrame;
struct GameplayPartyAttackFallbackQuery;
struct PartySpellCastResult;
class IndoorSceneRuntime;


class IndoorRenderer
{
public:
    struct GameplayActorPick
    {
        size_t runtimeActorIndex = 0;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceWidth = 0.0f;
        float sourceHeight = 0.0f;
    };

    IndoorRenderer(SpriteAtlasCache &spriteAtlasCache, NativeSpriteTextureCache &nativeSpriteCache);
    ~IndoorRenderer();

    IndoorRenderer(const IndoorRenderer &) = delete;
    IndoorRenderer &operator=(const IndoorRenderer &) = delete;

    bool initialize(
        const Engine::AssetFileSystem *pAssetFileSystem,
        Engine::AssetScaleTier assetScaleTier,
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const IndoorMapData &indoorMapData,
        const std::optional<IndoorTextureSet> &indoorTextureSet,
        const std::optional<DecorationBillboardSet> &indoorDecorationBillboardSet,
        const std::optional<ActorPreviewBillboardSet> &indoorActorPreviewBillboardSet,
        const std::optional<SpriteObjectBillboardSet> &indoorSpriteObjectBillboardSet,
        IndoorSceneRuntime &sceneRuntime,
        const ObjectTable &objectTable,
        const ItemTable &itemTable,
        const ChestTable &chestTable,
        const HouseTable &houseTable
    );
    void render(
        int width,
        int height,
        GameSession &gameSession,
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput = true,
        bool allowWorldSimulation = true,
        bool preparingResources = false);
    void updateWorldMovement(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput);
    void setCameraPosition(float x, float y, float z);
    void setCameraAngles(float yawRadians, float pitchRadians);
    // The weather over an open sky (scene `sky: {weather}`): the map's profile from GameDataLoader (none: no weather)
    // and the audio system its rain and thunder play on. Called after initialize.
    void setOpenSkyWeather(const std::optional<OutdoorWeatherProfile> &profile, GameAudioSystem *pAudioSystem);
    IndoorOpenSkyWeather &openSkyWeather()
    {
        return m_openSkyWeather;
    }
    // While held (a screenshot tour's poses), game time, timers, face triggers and positioned transitions stand still;
    // doors and lifts keep moving, as in turn-based mode.
    void setWorldTimeHeld(bool held);
    bool hasHudRenderResources() const;
    bgfx::ProgramHandle hudTexturedProgramHandle() const;
    bgfx::UniformHandle hudTextureSamplerHandle() const;
    bgfx::ProgramHandle hudTintedProgramHandle() const;
    bgfx::UniformHandle hudTintUniformHandle() const;
    void prepareHudView(int width, int height) const;
    void submitHudTextureQuad(
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight,
        float u0,
        float v0,
        float u1,
        float v1,
        TextureFilterProfile filterProfile = TextureFilterProfile::Ui) const;
    void setGameplayMouseLookMode(bool enabled, bool cursorMode);
    bool isWaterSupportFace(size_t faceIndex) const;
    WorldFxSystem &worldFxSystem();
    const WorldFxSystem &worldFxSystem() const;
    // The model a decoration shows now, by its sprite override key (a talking prop's talk portrait).
    std::optional<DecorationPortraitModel> decorationPortraitModel(uint32_t spriteOverrideKey) const;
    // Sprite frames of a monster the map did not preload (a summon by id), into the renderer's actor frames, which the
    // runtime and the actor models share.
    bool ensureMonsterVisualResources(int16_t monsterId);
    const SpriteFrameTable *actorSpriteFrameTable() const;
    Engine::ModelRenderer &modelRenderer() { return m_modelRenderer; }
    EffectRenderer &effectRenderer() { return m_effectRenderer; }
    const EffectRenderer::Diagnostics &effectRenderDiagnostics() const;
    std::optional<GameplayActorPick> gameplayActorPickAtCursor(
        int viewWidth,
        int viewHeight,
        float screenX,
        float screenY) const;
    GameplayWorldPickRequest buildGameplayWorldPickRequest(const GameplayWorldPickRequestInput &input) const;
    GameplayWorldHit pickGameplayWorldHit(const GameplayWorldPickRequest &request) const;
    GameplayWorldHit pickKeyboardGameplayWorldHit(const GameplayWorldPickRequest &request) const;
    GameplayWorldHoverCacheState gameplayWorldHoverCacheState() const;
    GameplayHoverStatusPayload refreshGameplayWorldHover(const GameplayWorldHoverRequest &request);
    GameplayHoverStatusPayload readCachedGameplayWorldHover() const;
    void clearGameplayWorldHover();
    bool projectGameplayWorldPointToScreen(
        const bx::Vec3 &point,
        int viewWidth,
        int viewHeight,
        float &screenX,
        float &screenY) const;
    std::optional<size_t> gameplayHoveredActorIndex() const;
    // The hostile actors on screen in line of sight that have noticed the party, closest first.
    std::vector<size_t> gameplayVisibleHostileActorIndices() const;
    std::optional<bx::Vec3> gameplayActorTargetPoint(size_t actorIndex) const;
    std::optional<bx::Vec3> gameplayActorNearestOpaquePoint(
        size_t actorIndex,
        const GameplayPartyAttackFallbackQuery &query) const;
    std::optional<bx::Vec3> gameplayGroundTargetPoint(float screenX, float screenY) const;
    const std::vector<int16_t> &visibleIndoorMapRevealSectorIds() const;
    uint64_t indoorMapRevealRevision() const;
    float cameraYawRadians() const;
    // The camera's last world position (for `weather status`).
    std::array<float, 3> cameraPosition() const
    {
        return {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
    }
    float cameraPitchRadians() const;
    // Width over height of the last drawn view; 4:3 before the first frame.
    float viewAspectRatio() const;
    bool canActivateGameplayWorldHit(const GameplayWorldHit &hit) const;
    bool activateGameplayWorldHit(const GameplayWorldHit &hit);
    void setWorldPostProcessing(CinematicGrading *pPostProcessing) { m_pPostProcessing = pPostProcessing; }
    // The portal and visibility debug view (console `portals`; IndoorRendererPortalDebug.cpp). Off by default.
    void setPortalDebugSettings(const IndoorPortalDebugSettings &settings);
    const IndoorPortalDebugSettings &portalDebugSettings() const { return m_portalDebug; }
    // The last drawn frame's counts and timings, valid while the view is on.
    const IndoorPortalDebugStats &portalDebugStats() const { return m_portalDebugStats; }
    // One line per sector of the map: faces, drawn faces, portal faces and links, open to the sky, bounds.
    std::vector<std::string> portalDebugSectorSummary() const;
    void shutdown();

private:
    // The camera as drawn and picked: the party's view plus the melee camera kick (GameplayActorHitFeedback).
    float viewYawRadians() const;
    float viewPitchRadians() const;
    void setBillboardFogColor(const float *pFogColor);
    // The billboard fog uniforms: the map's fog, or the constants every map without one has always passed.
    void setBillboardFog();
    // The face and blood splat fog uniforms, for the fog programs.
    void setFaceFog();
    // This frame's daylight (scene daylight, devdocs/INDOOR_OPEN_SKY.md) and fog (its night state), by the game time.
    void updateFrameDaylightAndFog();
    // evt.SetFog / evt.ClearFog over this frame's fog, faded in over the script's seconds.
    void applyScriptedFog();
    // Multiplies the frame by the tint of the water the party's eye is in (scene water volumes); nothing out of it.
    void renderWaterTint(uint16_t viewId);
    // The daylight's room light for the models and sprites of the sectors open to the sky.
    void applyDaylightToLightingFrame(IndoorLightingFrame &lightingFrame) const;
    // The face programs' daylight uniform: this frame's daylight for a face open to the sky, zero for every other.
    void setFaceDaylight(bool daylit);
    void applyDaylightSun(Engine::ModelRenderLighting &lighting, float exposure) const;
    struct TerrainVertex
    {
        float x;
        float y;
        float z;
        uint32_t abgr;

        static void init();
        static bgfx::VertexLayout ms_layout;
    };

    struct TexturedVertex
    {
        float x;
        float y;
        float z;
        float u;
        float v;
        float secretPulse;
        float barycentric0;
        float barycentric1;
        float barycentric2;
        float boundaryEdgeMask;
        float flowUPerSecond;
        float flowVPerSecond;
        float lavaFlow;
        float fluidFlow;
        uint32_t bakedLightAbgr;
        // The face's texture gradients per world unit (surface materials; SurfaceTextureGradients.h).
        std::array<float, 3> gradientU = {};
        std::array<float, 3> gradientV = {};
        // The face's sector and back sector (-1: none), which the dynamic lights' portal reach tests, and 1 when it
        // takes the scene daylight (TexturedBatch::daylit); one attribute with sectors.
        std::array<float, 2> sectors = {-1.0f, -1.0f};
        float daylight = 0.0f;

        static void init();
        static bgfx::VertexLayout ms_layout;
    };

    // The second vertex stream of a lightmapped batch: each vertex's coordinate on its lightmap page.
    struct LightmapUvVertex
    {
        static void init();
        static bgfx::VertexLayout ms_layout;
    };

    struct LitBillboardVertex
    {
        float x;
        float y;
        float z;
        float u;
        float v;
        uint32_t abgr;
        // Actor hit flash (GameplayActorHitFeedback): fraction of the flash colour mixed over the lit texel.
        float hitFlash = 0.0f;

        static void init();
        static bgfx::VertexLayout ms_layout;
    };

    struct BillboardLightingCacheEntry
    {
        bx::Vec3 position = {0.0f, 0.0f, 0.0f};
        std::array<float, 3> staticDetailRgb = {0.0f, 0.0f, 0.0f};
        float sampleClockSeconds = -1.0f;
        uint64_t lightRevision = 0;
        int16_t sectorId = -1;
        bool coloredLights = true;
        bool valid = false;
    };

    // A 3D model's sector (its room ambient and grid light reach), kept while the model's centre stays near the
    // sampled point.
    struct ModelSectorCacheEntry
    {
        uint32_t generation = 0;
        bx::Vec3 center = {0.0f, 0.0f, 0.0f};
        int16_t sectorId = -1;
        bool valid = false;
    };

    struct TexturedFaceTriangle
    {
        std::array<size_t, 3> faceVertexIndices = {};
        uint32_t vertexOffset = 0;
        uint32_t vertexCount = 0;
    };

    struct TexturedFaceMesh
    {
        std::vector<TexturedVertex> vertices;
        std::vector<uint32_t> indices;
        std::vector<TexturedFaceTriangle> triangles;
    };

    // One sector's faces of one texture (and back sector, lightmap page, liquid): the unit of visibility, lighting
    // refresh and mover updates. Its vertices are a range of its draw group's buffer (IndoorFaceDrawGroups.h).
    struct TexturedBatch
    {
        std::string textureName;
        int16_t sectorId = -1;
        int16_t backSectorId = -1;
        uint32_t drawGroup = 0;
        // Where its vertices start in the group's vertex buffer.
        uint32_t groupVertexOffset = 0;
        uint32_t vertexCount = 0;
        uint32_t indexCount = 0;
        bx::Vec3 boundsMin = {0.0f, 0.0f, 0.0f};
        bx::Vec3 boundsMax = {0.0f, 0.0f, 0.0f};
        bool hasBounds = false;
        uint32_t waterColorAbgr = 0;
        LiquidKind liquid = LiquidKind::None;
        // Its faces take the scene daylight: vertex-lit faces of a sector open to the sky (a lightmap has it).
        bool daylit = false;
        // A batch of lightmapped faces (devdocs/INDOOR_BAKED_LIGHTING.md): its page of the map's baked lighting and
        // each vertex's coordinate on it (its group's second vertex stream, kept only while building); -1 for
        // vertex-lit faces.
        int32_t lightmapPage = -1;
        std::vector<std::array<float, 2>> lightmapUvs;
        // A translucent face (IndoorMapData::translucentFaces, devdocs/INDOOR_TRANSLUCENT_FACES.md): one face per
        // batch, drawn back to front after the opaque scene; its plane normal decides a single-sided face's side.
        bool translucent = false;
        IndoorFaceTranslucency translucency = {};
        std::array<float, 3> faceNormal = {0.0f, 0.0f, 0.0f};
        std::vector<TexturedVertex> vertices;
        // Local to the batch's vertices; kept only for liquid batches (their water surfaces), the group has them all.
        std::vector<uint32_t> indices;
    };

    // The batches with one draw state (IndoorFaceDrawGroups.h): the texture and its animation, lightmap page and
    // liquid. Their vertices share one buffer and their indices one index buffer (m_faceDrawPlan's lists).
    struct TexturedDrawGroup
    {
        IndoorFaceDrawGroupKey key;
        bgfx::DynamicVertexBufferHandle vertexBufferHandle = BGFX_INVALID_HANDLE;
        uint32_t vertexCapacity = 0;
        uint32_t vertexCount = 0;
        bgfx::IndexBufferHandle indexBufferHandle = BGFX_INVALID_HANDLE;
        // The lightmap coordinates of a lightmapped group (a second vertex stream).
        bgfx::VertexBufferHandle lightmapUvBufferHandle = BGFX_INVALID_HANDLE;
        std::vector<bgfx::TextureHandle> frameTextureHandles;
        std::vector<uint32_t> frameLengthTicks;
        uint32_t animationLengthTicks = 0;
        // Surface material maps of a single-frame texture (devdocs/SURFACE_MATERIALS_PLAN.md), owned by its
        // IndoorTextureHandle; invalid when it has none.
        bgfx::TextureHandle materialNormal = BGFX_INVALID_HANDLE;
        bgfx::TextureHandle materialDetail = BGFX_INVALID_HANDLE;
        int textureWidth = 0;
        int textureHeight = 0;
        // Terrain faces (scene `terrain`): drawn from the blended ground materials, not the texture.
        bool terrain = false;
    };

    struct IndoorTextureHandle
    {
        std::string textureName;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
        // Its surface material maps, when it has them.
        bgfx::TextureHandle materialNormal = BGFX_INVALID_HANDLE;
        bgfx::TextureHandle materialDetail = BGFX_INVALID_HANDLE;
    };

    using BillboardTextureHandle = SpriteBillboardTexture;


    struct BillboardTextureLookupKey
    {
        std::string textureName;
        int16_t paletteId = 0;

        bool operator==(const BillboardTextureLookupKey &other) const
        {
            return textureName == other.textureName && paletteId == other.paletteId;
        }
    };

    struct BillboardTextureLookupKeyHash
    {
        size_t operator()(const BillboardTextureLookupKey &key) const
        {
            const size_t textureHash = std::hash<std::string>{}(key.textureName);
            const size_t paletteHash = std::hash<int16_t>{}(key.paletteId);
            const size_t hashSeed = 0x9e3779b97f4a7c15ull;

            return textureHash ^ (paletteHash + hashSeed + (textureHash << 6) + (textureHash >> 2));
        }
    };

    struct MechanismBinding
    {
        uint16_t linkedEventId = 0;
        std::string faceSummary;
        std::string linkedEventSummary;
    };

    struct InspectHit
    {
        bool hasHit = false;
        std::string kind;
        size_t index = 0;
        std::string name;
        std::string textureName;
        float distance = 0.0f;
        uint32_t attributes = 0;
        uint16_t decorationListId = 0;
        uint16_t eventIdPrimary = 0;
        uint16_t eventIdSecondary = 0;
        uint16_t variablePrimary = 0;
        uint16_t variableSecondary = 0;
        uint16_t specialTrigger = 0;
        uint16_t cogTriggered = 0;
        uint16_t cogTriggerType = 0;
        uint16_t cogNumber = 0;
        uint16_t roomNumber = 0;
        uint16_t roomBehindNumber = 0;
        uint8_t facetType = 0;
        bool isPortal = false;
        bool isFriendly = false;
        std::string spawnSummary;
        std::string spawnDetail;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        int32_t spellId = 0;
        bool hasContainingItem = false;
        // The item an object carries (0 for none).
        uint32_t containedItemId = 0;
        uint32_t doorAttributes = 0;
        uint32_t doorId = 0;
        uint16_t doorState = 0;
        uint16_t mechanismLinkedEventId = 0;
        size_t mechanismFaceIndex = static_cast<size_t>(-1);
        std::string mechanismFaceSummary;
        std::string mechanismLinkedEventSummary;
    };

    static bgfx::ProgramHandle loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName);
    static bgfx::ShaderHandle loadShader(const char *pShaderName);
    static std::vector<IndoorVertex> buildMechanismAdjustedVertices(
        const IndoorMapData &indoorMapData,
        const std::optional<MapDeltaData> &indoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState
    );
    static bool isFaceVisible(
        size_t faceIndex,
        const IndoorFace &face,
        const std::optional<MapDeltaData> &indoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState
    );
    static TexturedFaceMesh buildFaceTexturedMesh(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        const OutdoorBitmapTexture &texture,
        size_t faceIndex,
        const std::optional<MapDeltaData> &indoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState,
        bool coloredLights = true,
        const DecorationBillboardSet *pDecorationBillboardSet = nullptr,
        const std::vector<BakedStaticLightSource> *pBakedStaticLightSources = nullptr,
        const std::vector<BakedStaticLightSource> *pBakedStaticLightSubdivisionSources = nullptr,
        bool useBaseSubdivisionGeometry = false,
        std::span<const TexturedVertex> subdivisionTemplate = {},
        std::span<const TexturedFaceTriangle> triangleTemplate = {},
        std::span<const IndoorLightReachList> sourceReach = {}
    );
    void destroyBakedLightingResources();
    // Scene terrain: the material set, the terrain face mask, the smooth surface and the programs (a map without a
    // `terrain` block keeps none); false with an error for a broken terrain, which draws its faces textured instead.
    bool initializeTerrain(const Engine::AssetFileSystem &assets, const std::string &worldId,
        const IndoorMapData &indoorMapData, std::string &error);
    void destroyTerrainResources();
    bool isTerrainFace(size_t faceIndex) const
    {
        return faceIndex < m_terrainFaceMask.size() && m_terrainFaceMask[faceIndex] != 0;
    }
    bool isSingleMaterialTerrainFace(size_t faceIndex) const
    {
        return faceIndex < m_terrainFaceMask.size() && m_terrainFaceMask[faceIndex] == SingleMaterialTerrainFace;
    }
    // Marks the terrain faces whose pixels can read one ground layer only (the outdoor mesh's single-material test,
    // OutdoorTerrainMaterials::createMesh): no other layer has weight in the weight texels they reach, with two more
    // for the coarser mips, and the slope layer cannot blend in. Needs the material set's weight bits.
    void markSingleMaterialTerrainFaces(const IndoorMapData &indoorMapData, const OutdoorTerrainMaterialConfig &config);
    // A terrain face's vertices take the smooth ground normal (gradientU, the INDOOR_TERRAIN programs' a_tangent) and
    // the slope layer's steepness with the meadow value (u, v).
    void applyTerrainVertices(size_t faceIndex, std::vector<TexturedVertex> &vertices) const;
    // Grass over the terrain (scene `terrain: {grass}`): scattered on first use from the terrain faces and the grass
    // layers' density, drawn into viewId with the open sky's daylight and haze (settings: terrain decorations).
    void ensureTerrainGrass();
    // The terrain faces as triangles, each with the smooth ground normal at its face's centre.
    std::vector<TerrainDecorationSurfaceTriangle> terrainSurfaceTriangles() const;
    // The low bushes placed with the grass: their dissolve by distance and the open sky's light.
    void updateTerrainBushes(const bx::Vec3 &eye);
    void renderTerrainGrass(uint16_t viewId, const bx::Vec3 &eye, const bx::Vec3 &forward,
        const float *pProjectionMatrix, float aspect);
    static TexturedVertex interpolateTexturedVertex(const TexturedVertex &first, const TexturedVertex &second);
    // The vertex's baked light: the receiving room's ambient plus its static lights.
    static void refreshBakedStaticLight(
        const std::vector<BakedStaticLightSource> &bakedStaticLightSources,
        bool coloredLights,
        float ambient,
        TexturedVertex &vertex
    );
    static void appendBakedStaticLightSubdividedTriangle(
        TexturedFaceMesh &mesh,
        std::unordered_map<uint64_t, uint32_t> &vertexIndices,
        const std::vector<BakedStaticLightSource> &bakedStaticLightSources,
        const std::vector<BakedStaticLightSource> &bakedStaticLightSubdivisionSources,
        bool coloredLights,
        float ambient,
        const TexturedVertex (&triangleVertices)[3],
        const std::array<bx::Vec3, 3> &subdivisionPositions,
        int depth
    );
    static std::vector<TerrainVertex> buildWireframeVertices(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        const std::optional<MapDeltaData> &indoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState
    );
    static std::vector<TerrainVertex> buildPortalVertices(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices
    );
    static std::vector<TerrainVertex> buildEntityMarkerVertices(const IndoorMapData &indoorMapData);
    static std::vector<TerrainVertex> buildSpawnMarkerVertices(const IndoorMapData &indoorMapData);
    static std::vector<TerrainVertex> buildDoorMarkerVertices(
        const std::vector<IndoorVertex> &vertices,
        const MapDeltaData &mapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState
    );
    void destroyDerivedGeometryResources();
    void destroyIndoorTextureHandles();
    bool rebuildDerivedGeometryResources();
    bool updateMovingMechanismGeometryResources();
    bool updateMovingMechanismRenderVertices();
    bool tryActivateInspectEvent(const InspectHit &inspectHit);
    InspectHit inspectAtCursor(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        const std::vector<uint8_t> &visibleSectorMask,
        const bx::Vec3 &rayOrigin,
        const bx::Vec3 &rayDirection,
        const GameplayWorldPickRequest *pPickRequest = nullptr) const;
    std::optional<InspectHit> inspectGameplayWorldHit(const GameplayWorldPickRequest &request) const;
    GameplayWorldHit translateInspectHitToGameplayWorldHit(
        const InspectHit &inspectHit,
        const GameplayWorldPickRequest &request) const;
    std::optional<InspectHit> inspectHitFromGameplayWorldHit(const GameplayWorldHit &hit) const;
    uint16_t inspectHitEventId(const InspectHit &inspectHit) const;
    std::optional<std::string> resolveEntityDecorationHoverStatusText(const InspectHit &inspectHit) const;
    std::optional<std::string> resolveEventTargetHoverStatusText(const InspectHit &inspectHit) const;
    // The current event of an interactive decoration hit, whose title the hover shows.
    std::optional<uint16_t> resolveInteractiveDecorationHitEventId(const InspectHit &inspectHit) const;
    void updateCameraFromInput(const GameplayInputFrame &input, float deltaSeconds, bool allowWorldInput);
    // The sprite a decoration shows now (event SetSprite), and whether it is hidden (cleared or event-hidden).
    uint16_t resolveDecorationBillboardSpriteId(const DecorationBillboard &billboard, bool &hidden) const;
    // Places, hides and lights the 3D decoration models for this frame: visible in the rendered sectors, as bright
    // as the sprite each replaces, outlined when the context action highlights its decoration.
    void updateDecorationModels(const std::vector<uint8_t> &visibleSectorMask, const IndoorLightingFrame &lightingFrame,
        const GameplayContextActionState *pContextActionState, LightingStats *pLightingStats);
    void renderDecorationBillboards(
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        const std::vector<uint8_t> &visibleSectorMask,
        const std::vector<std::vector<IndoorVisibilityFrustum>> &visibleSectorFrustums,
        const IndoorLightingFrame &lightingFrame,
        const GameplayContextActionState *pContextActionState = nullptr,
        LightingStats *pLightingStats = nullptr,
        const WaterRenderer::Reflection *pReflection = nullptr
    );
    void renderActorPreviewBillboards(
        uint16_t viewId,
        const float *pViewMatrix,
        const float *pProjectionMatrix,
        const bx::Vec3 &cameraPosition,
        const std::vector<uint8_t> &visibleSectorMask,
        const IndoorLightingFrame &lightingFrame,
        bool spriteOutlineEnabled,
        const GameplayContextActionState *pContextActionState = nullptr,
        const GameSession *pGameSession = nullptr,
        const GameSettings *pSettings = nullptr,
        LightingStats *pLightingStats = nullptr,
        const WaterRenderer::Reflection *pReflection = nullptr
    );
    void renderSpriteObjectBillboards(
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        const std::vector<uint8_t> &visibleSectorMask,
        const IndoorLightingFrame &lightingFrame,
        bool spriteOutlineEnabled,
        const GameplayContextActionState *pContextActionState = nullptr,
        LightingStats *pLightingStats = nullptr
    );
    std::array<float, 4> billboardLightingUniform(
        const IndoorLightingFrame &lightingFrame,
        const SpriteFrameEntry &frame,
        const bx::Vec3 &position,
        int16_t sectorId,
        uint64_t cacheKey,
        LightingStats *pLightingStats);
    std::array<float, 3> cachedBillboardStaticDetailLighting(
        const IndoorLightingFrame &lightingFrame,
        const bx::Vec3 &position,
        int16_t sectorId,
        uint64_t cacheKey,
        LightingStats *pLightingStats);
    void renderContextActionGeometryHighlight(
        uint16_t viewId,
        const GameplayContextActionState *pContextActionState);
    void renderFxSegmentProjectiles(uint16_t viewId, const float *pViewMatrix);
    bgfx::TextureHandle ensureBloodSplatTexture();
    void ensureBloodSplatVertexBuffer();
    void renderBloodSplats(
        uint16_t viewId,
        const IndoorDrawLightSet &lightSet);
    const IndoorTextureHandle *findIndoorTextureHandle(const std::string &textureName) const;
    static BillboardTextureLookupKey makeBillboardTextureLookupKey(
        const std::string &textureName,
        int16_t paletteId);
    void registerBillboardTextureIndex(size_t textureIndex);
    const BillboardTextureHandle *findBillboardTexture(const std::string &textureName, int16_t paletteId) const;
    const BillboardTextureHandle *restoreBillboardTexture(
        const std::string &name, int16_t palette, const std::string &resourceIdentity = {});
    void preloadAtlasAnimations();
    const BillboardTextureHandle *ensureSpriteBillboardTexture(const std::string &textureName, int16_t paletteId);
    const std::optional<MapDeltaData> &runtimeMapDeltaData() const;
    const std::optional<EventRuntimeState> &runtimeEventRuntimeStateStorage() const;
    EventRuntimeState *runtimeEventRuntimeState();
    const EventRuntimeState *runtimeEventRuntimeState() const;
    uint64_t currentTexturedBatchGeometryRevision() const;
    uint64_t currentEventSurfaceSignature() const;
    uint64_t currentBakedStaticLightRevision() const;
    bool texturedBatchesNeedFullRebuild() const;
    void rebuildIndoorRenderMemberships();
    void rebuildMechanismBindings();
    // Adds a texture an event swaps onto faces (evt.SetTexture) to the texture set when no face of the map uses it.
    void ensureIndoorSwapTexture(const std::string &textureName);
    bool rebuildAllTexturedBatches(uint64_t &texturedBuildNanoseconds);
    // A new draw group's texture state; it takes over the vertex buffer of previousGroups' group with the same key.
    TexturedDrawGroup createTexturedDrawGroup(const IndoorFaceDrawGroupKey &key, const std::string &textureName,
        std::vector<TexturedDrawGroup> &previousGroups);
    static void destroyTexturedDrawGroups(std::vector<TexturedDrawGroup> &groups);
    // The draw order between batches whose faces touch (IndoorFaceDrawPlan::addConflict): all faces after a
    // rebuild, the moved faces of a mover (their new positions add pairs; none are removed until the next rebuild).
    void addFaceDrawConflicts(std::span<const size_t> faceIndices);
    bool updateWaterGeometry();
    // One draw of a group's faces: draw.indexCount indices from draw.firstIndex of the group's index buffer, or of
    // the main view's merged list (draw.merged). pTranslucentBatch: the translucent face drawn (its tint and opacity).
    // pLightGrid: the main view's grid for the faces' dynamic lights; without it they take `lights`.
    // terrainDepthWritten: the view already holds the terrain's depth (the main view's pre-pass), so a terrain draw
    // only tests it.
    bool submitTexturedFaces(const TexturedDrawGroup &group, const IndoorFaceGroupDraw &draw,
        const TexturedBatch *pTranslucentBatch, uint16_t viewId, const IndoorDrawLightSet &lights,
        const Engine::LightGridTextures *pLightGrid, const bx::Vec3 &eye, float yaw, float pitch, int width,
        int height, bool secretFacesDetected, const std::array<float, 4> &clipPlane, bool terrainDepthWritten,
        float projectionScale = 1.0f);
    // The animation frame a draw of the group shows, or nothing when the group cannot be drawn.
    std::optional<size_t> drawableFaceFrame(const TexturedDrawGroup &group, const IndoorFaceGroupDraw &draw) const;
    // One batch's own draw (water reflections, translucent faces).
    bool submitTexturedBatch(size_t batchIndex, uint16_t viewId, const IndoorDrawLightSet &lights,
        const Engine::LightGridTextures *pLightGrid, const bx::Vec3 &eye, float yaw, float pitch, int width,
        int height, bool secretFacesDetected, const std::array<float, 4> &clipPlane, float projectionScale = 1.0f);
    // The main view's opaque face draws: the drawn batches merged per group (m_faceDrawPlan); returns the draws.
    // The terrain's depth goes first (colour masked), so its expensive shading runs once per pixel instead of for
    // every hill behind a hill, the seabed under the shore and the back faces.
    size_t submitMainViewFaces(const std::vector<uint8_t> &drawnBatches, int width, int height,
        bool secretFacesDetected);
    // The visible translucent batches, back to front, blended over the finished opaque scene.
    // The open sky (m_openSky) behind the opaque scene, at the game's time of day.
    void renderOpenSky(uint16_t viewId, const float *pViewMatrix, const float *pProjectionMatrix);
    // The scene's sky-fog uniform (flat fog, or the outdoor view's sky haze), again after a sky pass set its own.
    void applySceneSkyFog();
    void renderTranslucentFaces(uint16_t viewId, const bx::Vec3 &eye, const std::vector<uint8_t> &visibleSectorMask,
        int width, int height, bool secretFacesDetected);
    void renderWaterReflections(const bx::Vec3 &forward,
        const IndoorLightingFrameInput &lightingInput, int width, int height, bool billboards);

    // Recomputes m_bakedStaticLightReach for the map's lights and decoration billboards.
    void rebuildBakedStaticLightReach();
    // Every sector's ambient level now: an event's override, else the map's.
    std::vector<int16_t> bakedSectorAmbientLevels() const;
    bool refreshBakedStaticLighting(
        bool refreshAllVertices,
        size_t &refreshedVertexCount,
        size_t &uploadedBatchCount);
    bool updateMovingMechanismFaceVertices(
        uint64_t &texturedBuildNanoseconds,
        uint64_t &uploadNanoseconds,
        size_t *pUpdatedFaceCount = nullptr,
        size_t *pDirtyBatchCount = nullptr);
    // The faces whose attributes alone changed since the batches were built, updated in place (a hidden face's vertices
    // collapse to a point); false when they need a full rebuild.
    bool updateFaceAttributeChanges();
    bool updateMechanismFaceVertices(
        const std::vector<size_t> &faceIndices,
        uint64_t &texturedBuildNanoseconds,
        uint64_t &uploadNanoseconds,
        size_t *pUpdatedFaceCount = nullptr,
        size_t *pDirtyBatchCount = nullptr);
    bool updateMechanismGeometryResourcesForDoorIds(
        const std::vector<uint32_t> &doorIds,
        uint64_t &texturedBuildNanoseconds,
        uint64_t &uploadNanoseconds,
        size_t *pUpdatedFaceCount = nullptr,
        size_t *pDirtyBatchCount = nullptr);
    static void rebuildTexturedBatchBounds(TexturedBatch &batch);
    std::vector<uint32_t> collectChangedMechanismDoorIds(
        const std::unordered_map<uint32_t, RuntimeMechanismState> &previousMechanisms) const;
    std::vector<size_t> collectMovingMechanismFaceIndices() const;
    std::vector<size_t> collectMechanismFaceIndicesForDoorIds(const std::vector<uint32_t> &doorIds) const;
    std::vector<uint8_t> collectMechanismFaceMask() const;
    bool updateMechanismRenderVerticesForDoorIds(const std::vector<uint32_t> &doorIds);
    struct IndoorPerformanceDiagnostics
    {
        uint64_t visibilityCalls = 0;
        uint64_t visibilityCacheHits = 0;
        uint64_t visibilityBuilds = 0;
        uint64_t visibilityBuildNanoseconds = 0;
        uint64_t visibilityTotalNanoseconds = 0;
        uint64_t visibilityPortalCandidates = 0;
        uint64_t visibilityPortalsAccepted = 0;
        uint64_t visibilityPortalsRejected = 0;
        uint64_t simulationCalls = 0;
        uint64_t simulationAdvancedFrames = 0;
        uint64_t simulationNanoseconds = 0;
        uint64_t mechanismProbeNanoseconds = 0;
        uint64_t movingFrames = 0;
        uint64_t movingUpdateFailures = 0;
        uint64_t movingRenderVerticesNanoseconds = 0;
        uint64_t movingFaceTotalNanoseconds = 0;
        uint64_t movingFaceBuildNanoseconds = 0;
        uint64_t movingFaceUploadNanoseconds = 0;
        uint64_t movingUpdatedFaces = 0;
        uint64_t movingDirtyBatches = 0;
        uint64_t movingFullRebuilds = 0;
        uint64_t movingFallbackFullRebuilds = 0;
        uint64_t mechanismSettleFullRebuilds = 0;
        uint64_t fullRebuildNanoseconds = 0;
        uint64_t mechanismTotalNanoseconds = 0;
        uint64_t renderFrames = 0;
        uint64_t renderTotalNanoseconds = 0;
        uint64_t renderWorldFxNanoseconds = 0;
        uint64_t renderViewSetupNanoseconds = 0;
        uint64_t renderVisibilityNanoseconds = 0;
        uint64_t renderLightingNanoseconds = 0;
        uint64_t renderBakedLightingRefreshNanoseconds = 0;
        uint64_t renderBakedLightingRefreshes = 0;
        uint64_t renderBakedLightingRefreshedVertices = 0;
        uint64_t renderBakedLightingUploadedBatches = 0;
        uint64_t renderInspectNanoseconds = 0;
        uint64_t renderTexturedSubmitNanoseconds = 0;
        uint64_t renderBloodSplatsNanoseconds = 0;
        uint64_t renderDecorationNanoseconds = 0;
        uint64_t renderActorNanoseconds = 0;
        uint64_t renderSpriteObjectNanoseconds = 0;
        uint64_t renderParticleNanoseconds = 0;
        uint64_t renderTexturedBatches = 0;
        uint64_t renderVisibleTexturedBatches = 0;
        uint64_t renderSubmittedTexturedBatches = 0;
        uint64_t renderCulledTexturedBatches = 0;
        uint64_t renderDecorationSpriteItems = 0;
        uint64_t renderDecorationSpriteSubmits = 0;
        uint64_t renderDecorationSpriteOutlineSubmits = 0;
        uint64_t renderDecorationSpriteTextureSwitches = 0;
        uint64_t renderActorSpriteItems = 0;
        uint64_t renderActorSpriteSubmits = 0;
        uint64_t renderActorSpriteOutlineSubmits = 0;
        uint64_t renderActorSpriteTextureSwitches = 0;
        uint64_t renderSpriteObjectItems = 0;
        uint64_t renderSpriteObjectProjectiles = 0;
        uint64_t renderSpriteObjectImpacts = 0;
        uint64_t renderSpriteObjectSubmits = 0;
        uint64_t renderSpriteObjectBatchSubmits = 0;
        uint64_t renderSpriteObjectBatchedItems = 0;
        uint64_t renderSpriteObjectUnbatchedItems = 0;
        uint64_t renderSpriteObjectOutlineSubmits = 0;
        uint64_t renderSpriteObjectTextureSwitches = 0;
        LightingStats lightingStats = {};

        bool hasActivity() const
        {
            return visibilityCalls != 0
                || simulationCalls != 0
                || movingFrames != 0
                || movingFullRebuilds != 0
                || renderFrames != 0;
        }
    };
    struct PortalVisibilityCache
    {
        bool valid = false;
        // The build's traversal counts and time (the time only while the portal debug view is on).
        uint32_t portalCandidateCount = 0;
        uint32_t acceptedPortalCount = 0;
        uint32_t directionRejectedPortalCount = 0;
        uint32_t clippedPortalRejectedCount = 0;
        uint32_t rejectedPortalCount = 0;
        uint64_t buildNanoseconds = 0;
        bool rebuilt = false;
        // Kept only while the portal debug view is on: the traversed portals and each node's sector.
        std::vector<IndoorAcceptedPortalVisibility> acceptedPortals;
        std::vector<int16_t> nodeSectorIds;
        int16_t sectorId = -1;
        float cameraX = 0.0f;
        float cameraY = 0.0f;
        float cameraZ = 0.0f;
        float yawRadians = 0.0f;
        float pitchRadians = 0.0f;
        float aspectRatio = 1.0f;
        int viewportHeight = 0;
        float maxDistance = 0.0f;
        std::vector<uint8_t> visibleSectorMask;
        std::vector<std::vector<IndoorVisibilityFrustum>> visibleSectorFrustums;
        std::vector<int16_t> mapRevealSectorIds;
        std::vector<IndoorPortalVisibilityTrace> portalTraces;

        void clear()
        {
            valid = false;
            sectorId = -1;
            visibleSectorMask.clear();
            visibleSectorFrustums.clear();
            mapRevealSectorIds.clear();
            portalTraces.clear();
            acceptedPortals.clear();
            nodeSectorIds.clear();
        }
    };
    void clearPortalVisibilityCaches() const;
    mutable uint64_t m_indoorMapRevealRevision = 0;
    std::vector<uint8_t> buildVisibleSectorMask(const bx::Vec3 &cameraPosition) const;
    void logIndoorVisibilityDiagnostics(
        const std::vector<uint8_t> &baseVisibleSectorMask,
        const std::vector<uint8_t> &renderVisibleSectorMask,
        uint32_t currentTick
    ) const;
    bool isSectorVisible(int16_t sectorId, const std::vector<uint8_t> &visibleSectorMask) const;
    bool isRenderSectorVisible(int16_t sectorId, const std::vector<uint8_t> &visibleSectorMask) const;

    bool m_isInitialized;
    bool m_isRenderable;
    bool m_worldTimeHeld = false;
    std::optional<MapStatsEntry> m_map;
    std::optional<MonsterTable> m_monsterTable;
    std::optional<ObjectTable> m_objectTable;
    const ItemTable *m_pItemTable = nullptr;
    const IndoorMapData *m_pIndoorMapData;
    std::optional<IndoorPortalGraph> m_indoorPortalGraph;
    std::vector<IndoorVertex> m_renderVertices;
    std::vector<std::vector<uint16_t>> m_neighboringSectorIds;
    IndoorSceneRuntime *m_pSceneRuntime = nullptr;
    std::optional<IndoorTextureSet> m_indoorTextureSet;
    // Swapped-in texture names already looked for and not found (not searched again each rebuild).
    std::unordered_set<std::string> m_missingSwapTextureNames;
    std::optional<DecorationBillboardSet> m_indoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> m_indoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> m_indoorSpriteObjectBillboardSet;
    std::vector<uint8_t> m_indoorInteractiveDecorationDecorVarIndicesByEntity;
    std::vector<uint16_t> m_indoorInteractiveDecorationBaseEventIdsByEntity;
    std::vector<uint8_t> m_indoorInteractiveDecorationEventCountsByEntity;
    std::vector<uint8_t> m_indoorInteractiveDecorationHideWhenClearedByEntity;
    std::vector<uint8_t> m_indoorInteractiveDecorationFixedEventByEntity;
    std::vector<std::vector<size_t>> m_decorationBillboardIndicesBySector;
    // Decorations drawn as static 3D models (engine/models/indoor_decorations.yml and the world's own).
    DecorationModelSet m_decorationModels;
    std::vector<std::vector<size_t>> m_staticSpriteObjectBillboardIndicesBySector;
    std::optional<HouseTable> m_houseTable;
    std::optional<ChestTable> m_chestTable;
    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    GameplayAssetLoadCache m_spriteLoadCache;
    Engine::AssetScaleTier m_assetScaleTier = Engine::AssetScaleTier::X1;
    bgfx::DynamicVertexBufferHandle m_wireframeVertexBufferHandle;
    bgfx::DynamicVertexBufferHandle m_portalVertexBufferHandle;
    bgfx::VertexBufferHandle m_entityMarkerVertexBufferHandle;
    bgfx::VertexBufferHandle m_spawnMarkerVertexBufferHandle;
    bgfx::DynamicVertexBufferHandle m_doorMarkerVertexBufferHandle;
    bgfx::ProgramHandle m_programHandle;
    bgfx::ProgramHandle m_texturedProgramHandle;
    bgfx::ProgramHandle m_hudTintedProgramHandle;
    bgfx::ProgramHandle m_indoorLitProgramHandle;
    // Faces whose textures have surface material maps, with the samplers and uniforms of those maps, and the
    // frame's video settings for them.
    bgfx::ProgramHandle m_indoorLitMaterialProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_surfaceNormalSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_surfaceDetailSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_surfaceMaterialUniformHandle = BGFX_INVALID_HANDLE;
    bool m_surfaceMaterialsEnabled = false;
    // Scene terrain (IndoorMapData::terrain, devdocs/INDOOR_OPEN_SKY.md "Terrain"): its blended ground materials,
    // smooth surface and programs, and per face of the map nonzero for a terrain face; empty for every other map.
    TerrainMaterialSet m_terrainMaterials;
    IndoorTerrainSurface m_terrainSurface;
    // 1 for a terrain face, SingleMaterialTerrainFace for one drawn with the single-material programs.
    static constexpr uint8_t SingleMaterialTerrainFace = 2;
    std::vector<uint8_t> m_terrainFaceMask;
    bgfx::ProgramHandle m_indoorTerrainProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_indoorTerrainFogProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_indoorTerrainSingleProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_indoorTerrainSingleFogProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_indoorTerrainDepthProgramHandle = BGFX_INVALID_HANDLE;
    // The terrain's grass: its decoration file, the grass layers' density per weight texel (rows from the map's
    // north-west corner, as the weights) and the tufts, built on first use.
    std::string m_grassConfigPath;
    std::vector<uint8_t> m_grassDensity;
    int m_grassDensitySize = 0;
    TerrainDecorationRenderer m_terrainGrass;
    TerrainBushSet m_terrainBushes;
    // Dry crests, lush hollows and shores (level_generation/terrain/MEADOW.md): the terrain's grass layers and the
    // grass take its tint; empty without terrain.
    OutdoorMeadowField m_terrainMeadow;
    bool m_terrainGrassAttempted = false;
    bool m_terrainGrassReady = false;
    bgfx::UniformHandle m_grassSunlightUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_grassFxLightParamsUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_grassCameraPositionUniform = BGFX_INVALID_HANDLE;
    // The terrain faces' far grass colour (the grass's foliage map, GRASS_LOD.md), unbound (zero) while no grass draws.
    bgfx::UniformHandle m_terrainFoliageSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_terrainFoliageUniform = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_noTerrainFoliage = BGFX_INVALID_HANDLE;
    bool m_terrainGrassShown = false;
    std::vector<TerrainDecorationPatch> m_terrainGrassDraws;
    bool m_terrainAntiTiling = true;
    bool m_surfaceParallaxEnabled = false;
    bool m_surfaceReflectionsEnabled = false;
    SurfaceReflectionBinding m_surfaceReflectionBinding;
    // Baked lighting (IndoorMapData::bakedLighting): its programs, lightmap pages and whether the batches use it
    // (`[video] lightmaps`; switching it rebuilds the batches once).
    bgfx::ProgramHandle m_indoorBakedProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_indoorBakedMaterialProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_lightmapSamplerHandle = BGFX_INVALID_HANDLE;
    std::vector<bgfx::TextureHandle> m_lightmapTextureHandles;
    // A version 2 bake's daylight pages (IndoorBakedLighting::daylightPages, one per lightmap page; empty otherwise)
    // and u_indoorBakedDaylight[3]: the scales of their light this frame (indoorBakedDaylightScale; [0].w 1 when the
    // map has them).
    bgfx::UniformHandle m_daylightmapSamplerHandle = BGFX_INVALID_HANDLE;
    std::vector<bgfx::TextureHandle> m_daylightmapTextureHandles;
    bgfx::UniformHandle m_indoorBakedDaylightUniformHandle = BGFX_INVALID_HANDLE;
    std::array<float, 12> m_frameBakedDaylight = {};
    bool m_bakedLightingActive = false;
    // Translucent faces (IndoorMapData::translucentFaces): their programs (vertex-lit and baked) and the tint/opacity
    // uniform, created only for a map that has such faces.
    bgfx::ProgramHandle m_indoorTranslucentProgramHandle = BGFX_INVALID_HANDLE;
    // The screen tint under water (vs_screen_color/fs_cubes), only on a map with water volumes.
    bgfx::ProgramHandle m_waterTintProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_indoorBakedTranslucentProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_indoorTranslucencyUniformHandle = BGFX_INVALID_HANDLE;
    // Scene fog (IndoorMapData::fog, devdocs/INDOOR_FOG.md) and, only for a map that has it, the fog variants of the
    // face programs: vertex-lit plain, materials, translucent, then baked plain, materials, translucent.
    IndoorFog m_fog;
    // The fog drawn this frame: m_fog, or its mix into the night state by the sky's night (updateFrameDaylightAndFog).
    IndoorFog m_frameFog;
    // A map script's fog (EventRuntimeState::scriptedFog, applyScriptedFog): the revision shown, the fog it fades
    // from (the last frame's) and when, and the last frame's fog.
    uint32_t m_scriptedFogRevision = 0;
    IndoorFog m_scriptedFogFrom;
    float m_scriptedFogStartSeconds = 0.0f;
    float m_scriptedFogSeconds = 0.0f;
    IndoorFog m_lastFrameFog;
    // The face programs' fog mode and the light's fog colour (MM9's fog), created only for a map with fog.
    bgfx::UniformHandle m_indoorFogModeUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_indoorFogLightUniformHandle = BGFX_INVALID_HANDLE;
    // Scene daylight (IndoorMapData::daylight, devdocs/INDOOR_OPEN_SKY.md "Daylight") and its value this frame; the
    // face programs' u_indoorDaylight, zero on every face without it.
    IndoorDaylight m_daylight;
    IndoorDaylightLight m_frameDaylight;
    // The open air's lights' scale this frame (indoorOpenAirLightScale; u_indoorDaylight[0].w), 1 without daylight.
    float m_frameOpenAirLightScale = 1.0f;
    // The terrain faces' mean static vertex light (rebuildAllTexturedBatches): the lamps' share and the open air's
    // lights' at noon, which their grass adds to its daylight (renderTerrainGrass).
    float m_terrainLampLight = 0.0f;
    float m_terrainOpenAirLight = 0.0f;
    bgfx::UniformHandle m_indoorDaylightUniformHandle = BGFX_INVALID_HANDLE;
    std::array<bgfx::ProgramHandle, 6> m_indoorFogProgramHandles = {{
        BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE,
        BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE}};
    // Scene model lighting (IndoorMapData::modelLighting, devdocs/INDOOR_MODEL_LIGHTING.md): MM9's lighting of
    // decorations and actors; disabled, they keep the room ambient and BLV light.
    IndoorModelLighting m_modelLighting;
    // Scene open sky (IndoorMapData::openSky, devdocs/INDOOR_OPEN_SKY.md): the map's sky faces are not drawn and the
    // Enhanced outdoor sky shows behind the scene where they are; unused (never initialized) by every other map.
    IndoorOpenSky m_openSky;
    SkyRenderer m_skyRenderer;
    // Weather over the open sky (IndoorOpenSkyWeather), drawn while the camera is in a sector open to the sky
    // (one holding sky faces, m_openSkySectors); m_pWeatherAudio: its sounds' audio system.
    IndoorOpenSkyWeather m_openSkyWeather;
    GameAudioSystem *m_pWeatherAudio = nullptr;
    std::vector<uint8_t> m_openSkySectors;
    // The outdoor view (m_openSky.outdoorView, devdocs/INDOOR_OPEN_SKY.md "Outdoor view"): this frame's view distance
    // (0 without it) and the sky's fog uniform the faces, models and billboards fade into (last frame's sky).
    float m_outdoorViewDistance = 0.0f;
    // The indoor hole view ([debug] indoor_hole_view, tools/indoor_hole_sweep.py) has replaced the open sky and fog.
    bool m_holeViewApplied = false;
    SkyFogUniformValues m_outdoorSkyFog = {};
    // The scene's mist (devdocs/MIST.md) and this frame's u_skyFog without a sky: flat fog and the mist, which the
    // outdoor view's m_outdoorSkyFog carries too.
    MapMist m_mist;
    MistWisps m_mistWisps;
    // The player's video.mist this frame.
    bool m_mistSetting = true;
    float m_mistStrengthSetting = 1.0f;
    // What the mist takes of the scene's daylight this frame (1 without one).
    std::array<float, 3> m_frameMistLight = {1.0f, 1.0f, 1.0f};
    SkySurroundings m_frameSurroundings = {};
    SkyFogUniformValues m_flatSkyFog = {};
    // The far plane: the outdoor view distance, else the indoor 50 000.
    float cameraFarClipDistance() const;
    bool m_skyRendererInitializeAttempted = false;
    float m_lastSkyStateElapsedTime = -1.0f;
    bgfx::ProgramHandle m_billboardProgramHandle;
    bgfx::VertexBufferHandle m_bloodSplatVertexBufferHandle;
    bgfx::TextureHandle m_bloodSplatTextureHandle;
    bgfx::UniformHandle m_textureSamplerHandle;
    bgfx::UniformHandle m_hudTintUniformHandle;
    bgfx::UniformHandle m_indoorLightPositionsUniformHandle;
    bgfx::UniformHandle m_indoorLightColorsUniformHandle;
    bgfx::UniformHandle m_indoorLightParamsUniformHandle;
    bgfx::UniformHandle m_indoorFaceGridUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_secretPulseParamsUniformHandle;
    bgfx::UniformHandle m_indoorSkyParamsUniformHandle;
    bgfx::UniformHandle m_indoorSkyProjectionParamsUniformHandle;
    bgfx::UniformHandle m_billboardAmbientUniformHandle;
    bgfx::UniformHandle m_billboardOverrideColorUniformHandle;
    bgfx::UniformHandle m_billboardOutlineParamsUniformHandle;
    bgfx::UniformHandle m_billboardFogColorUniformHandle;
    // Shared outdoor sky-fog uniform; indoors it stays zero so billboards keep their flat fog colour.
    bgfx::UniformHandle m_skyFogUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_billboardFogDensitiesUniformHandle;
    bgfx::UniformHandle m_billboardFogDistancesUniformHandle;
    float m_elapsedTime;
    float m_framesPerSecond;
    uint32_t m_wireframeVertexCount;
    uint32_t m_wireframeVertexCapacity;
    uint32_t m_portalVertexCount;
    uint32_t m_portalVertexCapacity;
    uint32_t m_faceCount;
    uint32_t m_entityMarkerVertexCount;
    uint32_t m_spawnMarkerVertexCount;
    uint32_t m_doorMarkerVertexCount;
    uint32_t m_doorMarkerVertexCapacity;
    uint32_t m_bloodSplatVertexCount = 0;
    uint64_t m_bloodSplatVertexBufferRevision = std::numeric_limits<uint64_t>::max();
    std::vector<TexturedBatch> m_texturedBatches;
    std::vector<TexturedDrawGroup> m_texturedDrawGroups;
    // The groups' index lists and the main view's draws; the merged list's buffer (re-uploaded when the drawn
    // batches change).
    IndoorFaceDrawPlan m_faceDrawPlan;
    bgfx::DynamicIndexBufferHandle m_mergedFaceIndexBufferHandle = BGFX_INVALID_HANDLE;
    // This frame's flag per batch: drawn in the main view's opaque faces.
    std::vector<uint8_t> m_mainViewDrawnBatches;
    // Each drawn opaque face's bounds and polygon at its current pose (invalid when not one) and a plan grid of
    // them, for the faces that can meet at one depth.
    struct FaceDrawBounds
    {
        bx::Vec3 min = {0.0f, 0.0f, 0.0f};
        bx::Vec3 max = {0.0f, 0.0f, 0.0f};
        IndoorFaceShape shape;
        bool valid = false;
    };
    std::vector<FaceDrawBounds> m_faceDrawBounds;
    std::unordered_map<uint64_t, std::vector<uint32_t>> m_faceDrawGrid;
    WaterRenderer m_waterRenderer;
    bool m_waterGeometryDirty = true;
    bool m_waterResourcesInitialized = false;
    bgfx::UniformHandle m_worldClipPlaneUniform = BGFX_INVALID_HANDLE;
    std::vector<IndoorTextureHandle> m_indoorTextureHandles;
    SpriteAtlasCache &m_spriteAtlasCache;
    NativeSpriteTextureCache &m_nativeSpriteCache;
    std::deque<BillboardTextureHandle> m_billboardTextureHandles;
    std::unordered_map<BillboardTextureLookupKey, size_t, BillboardTextureLookupKeyHash>
        m_billboardTextureIndexByKey;
    std::unordered_set<BillboardTextureLookupKey, BillboardTextureLookupKeyHash>
        m_runtimeBillboardLoadWarningKeys;
    uint64_t m_texturedBatchGeometryRevision = std::numeric_limits<uint64_t>::max();
    // The face attributes, the map and event surface revisions and the event surface signature the textured batches
    // were built with. Changed face bits (a destructible's faces hidden, by the world or by evt.SetFacetBit) update the
    // changed faces in place (updateFaceAttributeChanges); a change of what the batches read from the events
    // (evt.SetTexture, a facet bit the map delta could not take) rebuilds.
    std::vector<uint32_t> m_builtFaceAttributes;
    uint64_t m_builtMapSurfaceRevision = 0;
    uint64_t m_builtEventSurfaceRevision = 0;
    uint64_t m_builtEventSurfaceSignature = 0;
    uint64_t m_bakedStaticLightRevision = std::numeric_limits<uint64_t>::max();
    std::vector<uint8_t> m_bakedStaticLightEnabledStates;
    // Every sector's ambient level the vertices were baked with (evt.SetSectorAmbient changes it).
    std::vector<int16_t> m_bakedSectorAmbientLevels;
    // Per baked source (BakedStaticLightSource::sourceId): the sectors it reaches through portals, at its larger toggle
    // radius. Faces bake only the lights that reach their sectors.
    std::vector<IndoorLightReachList> m_bakedStaticLightReach;
    bool m_bakedStaticColoredLights = true;
    std::unordered_map<uint64_t, BillboardLightingCacheEntry> m_billboardLightingCache;
    std::vector<ModelSectorCacheEntry> m_modelSectorCache;
    // Face geometry for the models' sector lookups, kept between frames (only its entry states are reset each frame).
    IndoorFaceGeometryCache m_modelSectorGeometryCache;
    WorldFxRenderResources m_worldFxRenderResources;
    EffectRenderer m_effectRenderer;
    ShieldDomeRenderer m_shieldDomeRenderer;
    Engine::ModelRenderer m_modelRenderer;
    // The main view's clustered light grid: every light of the frame, for 3D models (creatures, decorations) and
    // the dynamic lights of BLV faces.
    Engine::LightGridTextures m_lightGrid;
    Engine::LightGridBinding m_lightGridBinding;
    CinematicGrading *m_pPostProcessing = nullptr;
    WorldFxSystem m_worldFxSystem;
    IndoorLightingRuntime m_indoorLightingRuntime;
    std::vector<MechanismBinding> m_mechanismBindings;
    std::vector<int32_t> m_faceBatchIndices;
    std::vector<uint32_t> m_faceVertexOffsets;
    std::vector<uint32_t> m_faceVertexCounts;
    std::vector<std::vector<TexturedFaceTriangle>> m_faceSubdivisionTriangles;
    float m_cameraPositionX;
    float m_cameraPositionY;
    float m_cameraPositionZ;
    float m_cameraYawRadians;
    float m_cameraPitchRadians;
    // This frame's view: a playing cinematic's field of view (60 otherwise) and the camera shake, set by render().
    float m_viewVerticalFovDegrees = 60.0f;
    float m_viewShakeYawRadians = 0.0f;
    float m_viewShakePitchRadians = 0.0f;
    // A cinematic camera's sector (the portal walk's start while it draws), and the eye it was found for; -1: the party's.
    int16_t m_viewSectorOverride = -1;
    std::array<float, 3> m_viewSectorEye = {};
    bool m_isRotatingCamera;
    float m_lastMouseX;
    float m_lastMouseY;
    int m_lastRenderWidth = 0;
    int m_lastRenderHeight = 0;
    std::vector<EnemyHealthBarRenderer::Draw> m_pendingEnemyHealthBars;
    mutable PortalVisibilityCache m_renderPortalVisibilityCache;
    bool m_logIndoorVisibilityDiagnostics = false;
    bool m_logIndoorPerformanceDiagnostics = false;
    mutable IndoorPerformanceDiagnostics m_indoorPerformanceDiagnostics;
    bool m_gameplayMouseLookEnabled = false;
    bool m_gameplayCursorMode = false;
    bool m_jumpHeld;
    InspectHit m_cachedInspectHit = {};
    bool m_cachedInspectHitValid = false;
    float m_cachedInspectMouseX = 0.0f;
    float m_cachedInspectMouseY = 0.0f;
    float m_cachedInspectCameraX = 0.0f;
    float m_cachedInspectCameraY = 0.0f;
    float m_cachedInspectCameraZ = 0.0f;
    float m_cachedInspectYawRadians = 0.0f;
    float m_cachedInspectPitchRadians = 0.0f;
    uint64_t m_inspectGeometryRevision = 0;
    uint64_t m_cachedInspectGeometryRevision = 0;
    uint64_t m_lastInspectUpdateTick = 0;
    mutable uint32_t m_lastVisibilityDiagnosticsLogTick = 0;
    GameplayWorldPickRequest m_cachedGameplayWorldPickRequest = {};

    // The portal debug view (IndoorRendererPortalDebug.cpp).
    // The view a pass draws into: its own debug pass view while `portals gpu` is on, else normalView.
    uint16_t portalDebugPassView(IndoorDebugPass pass, uint16_t normalView) const;
    void preparePortalDebugPassViews(int width, int height, const float *pViewMatrix, const float *pProjectionMatrix);
    void collectPortalDebugStats(const std::vector<uint8_t> &visibleSectorMask, const float *pViewMatrix,
        const float *pProjectionMatrix, const bx::Vec3 &eye);
    void renderPortalDebugOverlay(uint16_t viewId, const std::vector<uint8_t> &visibleSectorMask);
    IndoorPortalDebugSettings m_portalDebug;
    IndoorPortalDebugStats m_portalDebugStats;
    bool m_portalDebugPassViewsBound = false;
    // Each textured batch's faces (from m_faceBatchIndices), rebuilt with the batches.
    std::vector<std::vector<uint32_t>> m_portalDebugBatchFaces;
    uint64_t m_portalDebugBatchFacesRevision = std::numeric_limits<uint64_t>::max();
    size_t m_portalDebugBatchFacesBatchCount = 0;
};
}
