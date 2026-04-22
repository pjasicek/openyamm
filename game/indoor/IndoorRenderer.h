#pragma once

#include "engine/AssetScaleTier.h"
#include "game/indoor/IndoorMapData.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ObjectTable.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MapAssetLoader.h"
#include "game/render/TextureFiltering.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/tables/HouseTable.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct GameplayInputFrame;
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

    IndoorRenderer();
    ~IndoorRenderer();

    IndoorRenderer(const IndoorRenderer &) = delete;
    IndoorRenderer &operator=(const IndoorRenderer &) = delete;

    bool initialize(
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
        const ChestTable &chestTable,
        const HouseTable &houseTable
    );
    void render(
        int width,
        int height,
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput = true);
    void updateWorldMovement(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput);
    void setCameraPosition(float x, float y, float z);
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
    void triggerPendingSpellWorldFx(const PartySpellCastResult &castResult);
    void triggerProjectileImpactWorldFx(float x, float y, float z, uint32_t spellId);
    std::optional<GameplayActorPick> gameplayActorPickAtCursor(
        int viewWidth,
        int viewHeight,
        float screenX,
        float screenY) const;
    GameplayWorldPickRequest buildGameplayWorldPickRequest(const GameplayWorldPickRequestInput &input) const;
    GameplayWorldHit pickGameplayWorldHit(const GameplayWorldPickRequest &request) const;
    GameplayWorldHoverCacheState gameplayWorldHoverCacheState() const;
    GameplayHoverStatusPayload refreshGameplayWorldHover(const GameplayWorldHoverRequest &request);
    GameplayHoverStatusPayload readCachedGameplayWorldHover() const;
    void clearGameplayWorldHover();
    std::optional<size_t> gameplayHoveredActorIndex() const;
    std::optional<size_t> gameplayClosestVisibleHostileActorIndex() const;
    std::optional<bx::Vec3> gameplayActorTargetPoint(size_t actorIndex) const;
    std::optional<bx::Vec3> gameplayGroundTargetPoint(float screenX, float screenY) const;
    float cameraYawRadians() const;
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

        static void init();
        static bgfx::VertexLayout ms_layout;
    };

    struct TexturedBatch
    {
        bgfx::DynamicVertexBufferHandle vertexBufferHandle = BGFX_INVALID_HANDLE;
        std::string textureName;
        int16_t sectorId = -1;
        int16_t backSectorId = -1;
        std::vector<bgfx::TextureHandle> frameTextureHandles;
        std::vector<uint32_t> frameLengthTicks;
        uint32_t animationLengthTicks = 0;
        uint32_t vertexCapacity = 0;
        uint32_t vertexCount = 0;
        std::vector<TexturedVertex> vertices;
    };

    struct IndoorTextureHandle
    {
        std::string textureName;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

    struct BillboardTextureHandle
    {
        std::string textureName;
        int16_t paletteId = 0;
        int width = 0;
        int height = 0;
        int physicalWidth = 0;
        int physicalHeight = 0;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
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
        std::string mechanismFaceSummary;
        std::string mechanismLinkedEventSummary;
    };

    struct PendingSpellWorldFx
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float ageSeconds = 0.0f;
        float durationSeconds = 0.0f;
        float radius = 0.0f;
        uint32_t colorAbgr = 0xffffffffu;
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
        const std::optional<EventRuntimeState> &eventRuntimeState
    );
    static std::vector<TexturedVertex> buildTexturedVertices(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        const OutdoorBitmapTexture &texture,
        const std::vector<size_t> *pFaceIndices,
        const std::optional<MapDeltaData> &indoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState
    );
    static std::vector<TexturedVertex> buildFaceTexturedVertices(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        const OutdoorBitmapTexture &texture,
        size_t faceIndex,
        const std::optional<MapDeltaData> &indoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState
    );
    static std::vector<TerrainVertex> buildWireframeVertices(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
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
    bool tryActivateInspectEvent(const InspectHit &inspectHit);
    InspectHit inspectAtCursor(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        const std::vector<uint8_t> &visibleSectorMask,
        const bx::Vec3 &rayOrigin,
        const bx::Vec3 &rayDirection) const;
    std::optional<InspectHit> inspectGameplayWorldHit(const GameplayWorldPickRequest &request) const;
    GameplayWorldHit translateInspectHitToGameplayWorldHit(
        const InspectHit &inspectHit,
        const GameplayWorldPickRequest &request) const;
    std::optional<InspectHit> inspectHitFromGameplayWorldHit(const GameplayWorldHit &hit) const;
    void updateCameraFromInput(const GameplayInputFrame &input, float deltaSeconds, bool allowWorldInput);
    void renderDecorationBillboards(
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        const std::vector<uint8_t> &visibleSectorMask
    );
    void renderActorPreviewBillboards(
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        const std::vector<uint8_t> &visibleSectorMask
    );
    void renderSpriteObjectBillboards(
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        const std::vector<uint8_t> &visibleSectorMask
    );
    void advancePendingSpellWorldFx(float deltaSeconds);
    void renderPendingSpellWorldFx(
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition
    );
    const bgfx::TextureHandle *findIndoorTextureHandle(const std::string &textureName) const;
    const BillboardTextureHandle *findBillboardTexture(const std::string &textureName, int16_t paletteId = 0) const;
    const std::optional<MapDeltaData> &runtimeMapDeltaData() const;
    const std::optional<EventRuntimeState> &runtimeEventRuntimeStateStorage() const;
    EventRuntimeState *runtimeEventRuntimeState();
    const EventRuntimeState *runtimeEventRuntimeState() const;
    bool hasScriptVisualOverrides() const;
    void rebuildMechanismBindings();
    bool rebuildAllTexturedBatches(uint64_t &texturedBuildNanoseconds);
    bool updateMovingMechanismFaceVertices(uint64_t &texturedBuildNanoseconds, uint64_t &uploadNanoseconds);
    std::vector<size_t> collectMovingMechanismFaceIndices() const;
    std::vector<uint8_t> buildVisibleSectorMask(const bx::Vec3 &cameraPosition) const;
    bool isSectorVisible(int16_t sectorId, const std::vector<uint8_t> &visibleSectorMask) const;
    bool isBatchVisible(const TexturedBatch &batch, const std::vector<uint8_t> &visibleSectorMask) const;

    bool m_isInitialized;
    bool m_isRenderable;
    std::optional<MapStatsEntry> m_map;
    std::optional<MonsterTable> m_monsterTable;
    std::optional<ObjectTable> m_objectTable;
    std::optional<IndoorMapData> m_indoorMapData;
    std::vector<IndoorVertex> m_renderVertices;
    IndoorSceneRuntime *m_pSceneRuntime = nullptr;
    std::optional<IndoorTextureSet> m_indoorTextureSet;
    std::optional<DecorationBillboardSet> m_indoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> m_indoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> m_indoorSpriteObjectBillboardSet;
    std::optional<HouseTable> m_houseTable;
    std::optional<ChestTable> m_chestTable;
    Engine::AssetScaleTier m_assetScaleTier = Engine::AssetScaleTier::X1;
    bgfx::DynamicVertexBufferHandle m_wireframeVertexBufferHandle;
    bgfx::DynamicVertexBufferHandle m_portalVertexBufferHandle;
    bgfx::VertexBufferHandle m_entityMarkerVertexBufferHandle;
    bgfx::VertexBufferHandle m_spawnMarkerVertexBufferHandle;
    bgfx::DynamicVertexBufferHandle m_doorMarkerVertexBufferHandle;
    bgfx::ProgramHandle m_programHandle;
    bgfx::ProgramHandle m_texturedProgramHandle;
    bgfx::UniformHandle m_textureSamplerHandle;
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
    std::vector<TexturedBatch> m_texturedBatches;
    std::vector<IndoorTextureHandle> m_indoorTextureHandles;
    std::vector<BillboardTextureHandle> m_billboardTextureHandles;
    std::vector<PendingSpellWorldFx> m_pendingSpellWorldFx;
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
    bool m_gameplayMouseLookEnabled = false;
    bool m_gameplayCursorMode = false;
    bool m_activateInspectLatch;
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
    GameplayWorldPickRequest m_cachedGameplayWorldPickRequest = {};
    mutable int16_t m_cachedVisibleSectorId = -1;
    mutable std::vector<uint32_t> m_cachedVisibleDoorStateSignature;
    mutable std::vector<uint8_t> m_cachedVisibleSectorMask;
};
}
