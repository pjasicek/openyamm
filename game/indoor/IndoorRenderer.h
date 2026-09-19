#pragma once

#include <deque>

#include "game/render/SpriteAtlasCache.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/indoor/IndoorMapData.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/indoor/IndoorPortalGraph.h"
#include "game/indoor/IndoorPortalVisibility.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ObjectTable.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MapAssetLoader.h"
#include "game/render/TextureFiltering.h"
#include "game/render/BillboardOpacityMask.h"
#include "game/tables/ItemTable.h"
#include "game/fx/WorldFxRenderResources.h"
#include "game/fx/WorldFxSystem.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/tables/HouseTable.h"
#include "game/ui/GameplayHudCommon.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <array>
#include <cstdint>
#include <functional>
#include <limits>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class GameSession;
struct GameSettings;
struct GameplayInputFrame;
struct PartySpellCastResult;
class IndoorSceneRuntime;

struct BakedStaticLightSource
{
    bx::Vec3 position = {0.0f, 0.0f, 0.0f};
    float radius = 0.0f;
    uint8_t red = 255;
    uint8_t green = 255;
    uint8_t blue = 255;
    float alpha = 1.0f;
};

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

    IndoorRenderer();
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
        bool allowWorldSimulation = true);
    void updateWorldMovement(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput);
    void setCameraPosition(float x, float y, float z);
    void setCameraAngles(float yawRadians, float pitchRadians);
    bool hasHudRenderResources() const;
    bgfx::ProgramHandle hudTexturedProgramHandle() const;
    bgfx::UniformHandle hudTextureSamplerHandle() const;
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
    WorldFxSystem &worldFxSystem();
    const WorldFxSystem &worldFxSystem() const;
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
    std::optional<size_t> gameplayClosestVisibleHostileActorIndex() const;
    std::optional<bx::Vec3> gameplayActorTargetPoint(size_t actorIndex) const;
    std::optional<bx::Vec3> gameplayGroundTargetPoint(float screenX, float screenY) const;
    std::vector<int16_t> visibleIndoorMapRevealSectorIds(int16_t sectorId, int16_t eyeSectorId) const;
    float cameraYawRadians() const;
    float cameraPitchRadians() const;
    bool canActivateGameplayWorldHit(const GameplayWorldHit &hit) const;
    bool activateGameplayWorldHit(const GameplayWorldHit &hit);
    void shutdown();

private:
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

        // Unit world-space normal from the transformed face geometry; zero marks faces
        // without a usable plane.
        float normalX = 0.0f;
        float normalY = 0.0f;
        float normalZ = 0.0f;

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

    struct TexturedBatch
    {
        bgfx::DynamicVertexBufferHandle vertexBufferHandle = BGFX_INVALID_HANDLE;
        std::string textureName;
        int16_t sectorId = -1;
        int16_t backSectorId = -1;
        uint32_t stableId = 0;
        uint16_t materialId = SurfaceMaterialRuntimeSet::NeutralMaterialId;
        std::vector<bgfx::TextureHandle> frameTextureHandles;
        std::vector<uint32_t> frameLengthTicks;
        uint32_t animationLengthTicks = 0;
        int textureWidth = 0;
        int textureHeight = 0;
        uint32_t vertexCapacity = 0;
        uint32_t vertexCount = 0;
        bx::Vec3 boundsMin = {0.0f, 0.0f, 0.0f};
        bx::Vec3 boundsMax = {0.0f, 0.0f, 0.0f};
        bool hasBounds = false;
        std::vector<TexturedVertex> vertices;
    };

    struct CachedIndoorLightSelection
    {
        IndoorLightSelectionHistory history = {};
        uint32_t lastSeenFrame = 0;
    };

    struct IndoorTextureHandle
    {
        std::string textureName;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
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
    static std::vector<TexturedVertex> buildTexturedVertices(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        const OutdoorBitmapTexture &texture,
        const std::vector<size_t> *pFaceIndices,
        const std::optional<MapDeltaData> &indoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState,
        bool coloredLights = true,
        const DecorationBillboardSet *pDecorationBillboardSet = nullptr,
        const std::vector<BakedStaticLightSource> *pBakedStaticLightSources = nullptr,
        const std::vector<BakedStaticLightSource> *pBakedStaticLightSubdivisionSources = nullptr,
        bool allowBakedLightSubdivision = true
    );
    static std::vector<TexturedVertex> buildFaceTexturedVertices(
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
        bool allowBakedLightSubdivision = true
    );
    static bool bakedStaticLightMayAffectTriangle(
        const std::vector<BakedStaticLightSource> &bakedStaticLightSources,
        const TexturedVertex (&triangleVertices)[3]
    );
    static float texturedVertexDistanceSquared(const TexturedVertex &first, const TexturedVertex &second);
    static TexturedVertex interpolateTexturedVertex(const TexturedVertex &first, const TexturedVertex &second);
    static void refreshBakedStaticLight(
        const std::vector<BakedStaticLightSource> &bakedStaticLightSources,
        bool coloredLights,
        TexturedVertex &vertex
    );
    static void appendBakedStaticLightSubdividedTriangle(
        std::vector<TexturedVertex> &vertices,
        const std::vector<BakedStaticLightSource> &bakedStaticLightSources,
        const std::vector<BakedStaticLightSource> &bakedStaticLightSubdivisionSources,
        bool coloredLights,
        const TexturedVertex (&triangleVertices)[3],
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
    void updateCameraFromInput(const GameplayInputFrame &input, float deltaSeconds, bool allowWorldInput);
    void renderDecorationBillboards(
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        const std::vector<uint8_t> &visibleSectorMask,
        const std::vector<std::vector<IndoorVisibilityFrustum>> &visibleSectorFrustums,
        const IndoorLightingFrame &lightingFrame,
        const GameplayContextActionState *pContextActionState = nullptr,
        LightingStats *pLightingStats = nullptr
    );
    void renderActorPreviewBillboards(
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        const std::vector<uint8_t> &visibleSectorMask,
        const IndoorLightingFrame &lightingFrame,
        bool spriteOutlineEnabled,
        const GameplayContextActionState *pContextActionState = nullptr,
        const GameSession *pGameSession = nullptr,
        const GameSettings *pSettings = nullptr,
        LightingStats *pLightingStats = nullptr
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
    bgfx::TextureHandle ensureMaterialMaskTexture(uint16_t materialId);
    void ensureBloodSplatVertexBuffer();
    void renderBloodSplats(
        uint16_t viewId,
        const IndoorDrawLightSet &lightSet);
    const bgfx::TextureHandle *findIndoorTextureHandle(const std::string &textureName) const;
    static BillboardTextureLookupKey makeBillboardTextureLookupKey(
        const std::string &textureName,
        int16_t paletteId);
    void registerBillboardTextureIndex(size_t textureIndex);
    const BillboardTextureHandle *findBillboardTexture(const std::string &textureName, int16_t paletteId) const;
    const BillboardTextureHandle *ensureSpriteBillboardTexture(const std::string &textureName, int16_t paletteId);
    const std::optional<MapDeltaData> &runtimeMapDeltaData() const;
    const std::optional<EventRuntimeState> &runtimeEventRuntimeStateStorage() const;
    EventRuntimeState *runtimeEventRuntimeState();
    const EventRuntimeState *runtimeEventRuntimeState() const;
    uint64_t currentTexturedBatchGeometryRevision() const;
    uint64_t currentBakedStaticLightRevision() const;
    bool texturedBatchesNeedFullRebuild() const;
    void rebuildIndoorRenderMemberships();
    void rebuildMechanismBindings();
    bool rebuildAllTexturedBatches(uint64_t &texturedBuildNanoseconds);
    bool refreshBakedStaticLighting(
        bool refreshAllVertices,
        size_t &refreshedVertexCount,
        size_t &uploadedBatchCount);
    bool updateMovingMechanismFaceVertices(
        uint64_t &texturedBuildNanoseconds,
        uint64_t &uploadNanoseconds,
        size_t *pUpdatedFaceCount = nullptr,
        size_t *pDirtyBatchCount = nullptr);
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
        int16_t sectorId = -1;
        float cameraX = 0.0f;
        float cameraY = 0.0f;
        float cameraZ = 0.0f;
        float yawRadians = 0.0f;
        float pitchRadians = 0.0f;
        float aspectRatio = 1.0f;
        std::vector<uint8_t> visibleSectorMask;
        std::vector<std::vector<IndoorVisibilityFrustum>> visibleSectorFrustums;
        std::vector<IndoorAcceptedPortalVisibility> acceptedPortals;
        std::vector<IndoorPortalVisibilityTrace> portalTraces;

        void clear()
        {
            valid = false;
            sectorId = -1;
            visibleSectorMask.clear();
            visibleSectorFrustums.clear();
            acceptedPortals.clear();
            portalTraces.clear();
        }
    };
    void clearPortalVisibilityCaches() const;
    std::vector<uint8_t> buildVisibleSectorMask(const bx::Vec3 &cameraPosition) const;
    void logIndoorVisibilityDiagnostics(
        const std::vector<uint8_t> &baseVisibleSectorMask,
        const std::vector<uint8_t> &renderVisibleSectorMask,
        uint32_t currentTick
    ) const;
    bool isSectorVisible(int16_t sectorId, const std::vector<uint8_t> &visibleSectorMask) const;
    bool isRenderSectorVisible(int16_t sectorId, const std::vector<uint8_t> &visibleSectorMask) const;
    bool isTexturedBatchVisible(const TexturedBatch &batch, const std::vector<uint8_t> &visibleSectorMask) const;

    bool m_isInitialized;
    bool m_isRenderable;
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
    std::optional<DecorationBillboardSet> m_indoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> m_indoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> m_indoorSpriteObjectBillboardSet;
    std::vector<uint8_t> m_indoorInteractiveDecorationDecorVarIndicesByEntity;
    std::vector<uint16_t> m_indoorInteractiveDecorationBaseEventIdsByEntity;
    std::vector<uint8_t> m_indoorInteractiveDecorationEventCountsByEntity;
    std::vector<uint8_t> m_indoorInteractiveDecorationHideWhenClearedByEntity;
    std::vector<std::vector<size_t>> m_decorationBillboardIndicesBySector;
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
    bgfx::ProgramHandle m_indoorLitProgramHandle;
    bgfx::ProgramHandle m_billboardProgramHandle;
    bgfx::VertexBufferHandle m_bloodSplatVertexBufferHandle;
    bgfx::TextureHandle m_bloodSplatTextureHandle;
    bgfx::UniformHandle m_textureSamplerHandle;
    bgfx::UniformHandle m_indoorLightPositionsUniformHandle;
    bgfx::UniformHandle m_indoorLightColorsUniformHandle;
    bgfx::UniformHandle m_indoorLightParamsUniformHandle;
    bgfx::UniformHandle m_secretPulseParamsUniformHandle;
    bgfx::UniformHandle m_indoorSkyParamsUniformHandle;
    bgfx::UniformHandle m_indoorSkyProjectionParamsUniformHandle;
    bgfx::UniformHandle m_indoorCameraPositionUniformHandle;
    bgfx::UniformHandle m_materialShadingUniformHandle;
    bgfx::UniformHandle m_materialEmissiveColorUniformHandle;
    bgfx::UniformHandle m_materialEnvironmentUniformHandle;
    bgfx::UniformHandle m_materialWetnessUniformHandle;
    bgfx::UniformHandle m_materialMaskSamplerHandle;
    bgfx::TextureHandle m_materialMaskNeutralTexelHandle = BGFX_INVALID_HANDLE;
    // Packed facade mask textures keyed by resolved material id, created on first use.
    std::unordered_map<uint16_t, bgfx::TextureHandle> m_materialMaskTextureHandles;
    std::unordered_set<uint16_t> m_failedMaterialMaskIds;
    uint16_t m_lastSubmittedMaterialId = 0xffff;
    bgfx::UniformHandle m_billboardAmbientUniformHandle;
    bgfx::UniformHandle m_billboardOverrideColorUniformHandle;
    bgfx::UniformHandle m_billboardOutlineParamsUniformHandle;
    bgfx::UniformHandle m_billboardFogColorUniformHandle;
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
    std::unordered_map<uint32_t, CachedIndoorLightSelection> m_indoorLightingSelectionCache;
    std::vector<IndoorTextureHandle> m_indoorTextureHandles;
    SpriteAtlasCache m_spriteAtlasCache;
    std::deque<BillboardTextureHandle> m_billboardTextureHandles;
    std::unordered_map<BillboardTextureLookupKey, size_t, BillboardTextureLookupKeyHash>
        m_billboardTextureIndexByKey;
    std::unordered_set<BillboardTextureLookupKey, BillboardTextureLookupKeyHash>
        m_runtimeBillboardLoadWarningKeys;
    uint64_t m_texturedBatchGeometryRevision = std::numeric_limits<uint64_t>::max();
    uint64_t m_bakedStaticLightRevision = std::numeric_limits<uint64_t>::max();
    std::vector<uint8_t> m_bakedStaticLightEnabledStates;
    bool m_bakedStaticColoredLights = true;
    uint32_t m_indoorLightingSelectionFrame = 0;
    std::unordered_map<uint64_t, BillboardLightingCacheEntry> m_billboardLightingCache;
    WorldFxRenderResources m_worldFxRenderResources;
    WorldFxSystem m_worldFxSystem;
    IndoorLightingRuntime m_indoorLightingRuntime;
    std::vector<MechanismBinding> m_mechanismBindings;
    std::vector<int32_t> m_faceBatchIndices;
    std::vector<uint32_t> m_faceVertexOffsets;
    std::vector<uint32_t> m_faceVertexCounts;
    float m_cameraPositionX;
    float m_cameraPositionY;
    float m_cameraPositionZ;
    float m_cameraYawRadians;
    float m_cameraPitchRadians;
    bool m_isRotatingCamera;
    float m_lastMouseX;
    float m_lastMouseY;
    int m_lastRenderWidth = 0;
    int m_lastRenderHeight = 0;
    mutable PortalVisibilityCache m_renderPortalVisibilityCache;
    bool m_logIndoorVisibilityDiagnostics = false;
    bool m_logIndoorPerformanceDiagnostics = false;
    mutable IndoorPerformanceDiagnostics m_indoorPerformanceDiagnostics;
    bool m_gameplayMouseLookEnabled = false;
    bool m_gameplayCursorMode = false;
    bool m_jumpHeld;
    bool m_indoorGeometryRenderingDisabled = false;
    bool m_indoorGeometryRenderingToggleHeld = false;
    bool m_indoorGeometryTranslucent = false;
    bool m_indoorGeometryTranslucentToggleHeld = false;
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
};
}
