#pragma once

#include "game/OutdoorCollisionData.h"
#include "game/MapAssetLoader.h"
#include "game/MapStats.h"
#include "game/MonsterTable.h"
#include "game/OutdoorMapData.h"
#include "game/ChestTable.h"
#include "game/EvtProgram.h"
#include "game/HouseTable.h"
#include "game/StrTable.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <cstdint>
#include <memory>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class OutdoorMovementDriver;

class TerrainDebugRenderer
{
public:
    TerrainDebugRenderer();
    ~TerrainDebugRenderer();

    TerrainDebugRenderer(const TerrainDebugRenderer &) = delete;
    TerrainDebugRenderer &operator=(const TerrainDebugRenderer &) = delete;

    bool initialize(
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const OutdoorMapData &outdoorMapData,
        const std::optional<std::vector<uint8_t>> &outdoorLandMask,
        const std::optional<std::vector<uint32_t>> &outdoorTileColors,
        const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas,
        const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet,
        const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
        const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
        const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet,
        const std::optional<DecorationBillboardSet> &outdoorDecorationBillboardSet,
        const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet,
        const std::optional<SpriteObjectBillboardSet> &outdoorSpriteObjectBillboardSet,
        const std::optional<MapDeltaData> &outdoorMapDeltaData,
        const ChestTable &chestTable,
        const HouseTable &houseTable,
        const std::optional<StrTable> &localStrTable,
        const std::optional<EvtProgram> &localEvtProgram,
        const std::optional<EvtProgram> &globalEvtProgram
    );
    void render(int width, int height, float mouseWheelDelta);
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

    struct TexturedTerrainVertex
    {
        float x;
        float y;
        float z;
        float u;
        float v;

        static void init();

        static bgfx::VertexLayout ms_layout;
    };

    struct TexturedBModelBatch
    {
        bgfx::VertexBufferHandle vertexBufferHandle = BGFX_INVALID_HANDLE;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
        uint32_t vertexCount = 0;
    };

    struct BillboardTextureHandle
    {
        std::string textureName;
        int width = 0;
        int height = 0;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

    struct InspectHit
    {
        bool hasHit = false;
        size_t bModelIndex = 0;
        size_t faceIndex = 0;
        std::string textureName;
        float distance = 0.0f;
        uint32_t attributes = 0;
        int16_t bitmapIndex = 0;
        uint16_t cogNumber = 0;
        uint16_t cogTriggeredNumber = 0;
        uint16_t cogTrigger = 0;
        uint8_t polygonType = 0;
        uint8_t shade = 0;
        uint8_t visibility = 0;
        std::string kind;
        std::string name;
        bool isFriendly = false;
        uint16_t decorationListId = 0;
        uint16_t eventIdPrimary = 0;
        uint16_t eventIdSecondary = 0;
        uint16_t variablePrimary = 0;
        uint16_t variableSecondary = 0;
        uint16_t specialTrigger = 0;
        uint16_t spawnTypeId = 0;
        std::string spawnSummary;
        std::string spawnDetail;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        int32_t spellId = 0;
    };

    static uint32_t colorFromHeight(float normalizedHeight);
    static uint32_t colorFromBModel();
    static bgfx::ProgramHandle loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName);
    static bgfx::ShaderHandle loadShader(const char *pShaderName);
    static std::vector<TerrainVertex> buildVertices(const OutdoorMapData &outdoorMapData);
    static std::vector<uint16_t> buildIndices();
    static std::vector<TexturedTerrainVertex> buildTexturedTerrainVertices(
        const OutdoorMapData &outdoorMapData,
        const OutdoorTerrainTextureAtlas &outdoorTerrainTextureAtlas
    );
    static std::vector<TexturedTerrainVertex> buildTexturedBModelVertices(
        const OutdoorMapData &outdoorMapData,
        const OutdoorBitmapTexture &texture
    );
    static std::vector<TerrainVertex> buildFilledTerrainVertices(
        const OutdoorMapData &outdoorMapData,
        const std::optional<std::vector<uint32_t>> &outdoorTileColors
    );
    static std::vector<TerrainVertex> buildBModelWireframeVertices(const OutdoorMapData &outdoorMapData);
    static std::vector<TerrainVertex> buildBModelCollisionFaceVertices(const OutdoorMapData &outdoorMapData);
    static std::vector<TerrainVertex> buildEntityMarkerVertices(const OutdoorMapData &outdoorMapData);
    static std::vector<TerrainVertex> buildSpawnMarkerVertices(const OutdoorMapData &outdoorMapData);
    InspectHit inspectBModelFace(
        const OutdoorMapData &outdoorMapData,
        const bx::Vec3 &rayOrigin,
        const bx::Vec3 &rayDirection
    );
    void updateCameraFromInput();
    void renderDecorationBillboards(
        uint16_t viewId,
        uint16_t viewWidth,
        uint16_t viewHeight,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition
    );
    void renderActorPreviewBillboards(uint16_t viewId, const float *pViewMatrix, const bx::Vec3 &cameraPosition);
    void renderSpriteObjectBillboards(uint16_t viewId, const float *pViewMatrix, const bx::Vec3 &cameraPosition);
    const BillboardTextureHandle *findBillboardTexture(const std::string &textureName) const;
    bool m_isInitialized;
    bool m_isRenderable;
    std::optional<MapStatsEntry> m_map;
    std::optional<MonsterTable> m_monsterTable;
    std::optional<OutdoorMapData> m_outdoorMapData;
    std::optional<DecorationBillboardSet> m_outdoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> m_outdoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> m_outdoorSpriteObjectBillboardSet;
    std::optional<MapDeltaData> m_outdoorMapDeltaData;
    std::optional<HouseTable> m_houseTable;
    std::optional<ChestTable> m_chestTable;
    std::optional<StrTable> m_localStrTable;
    std::optional<EvtProgram> m_localEvtProgram;
    std::optional<EvtProgram> m_globalEvtProgram;
    bgfx::VertexBufferHandle m_vertexBufferHandle;
    bgfx::IndexBufferHandle m_indexBufferHandle;
    bgfx::VertexBufferHandle m_texturedTerrainVertexBufferHandle;
    bgfx::VertexBufferHandle m_filledTerrainVertexBufferHandle;
    bgfx::VertexBufferHandle m_bmodelVertexBufferHandle;
    bgfx::VertexBufferHandle m_bmodelCollisionVertexBufferHandle;
    bgfx::VertexBufferHandle m_entityMarkerVertexBufferHandle;
    bgfx::VertexBufferHandle m_spawnMarkerVertexBufferHandle;
    bgfx::ProgramHandle m_programHandle;
    bgfx::ProgramHandle m_texturedTerrainProgramHandle;
    bgfx::TextureHandle m_terrainTextureAtlasHandle;
    bgfx::UniformHandle m_terrainTextureSamplerHandle;
    float m_elapsedTime;
    float m_framesPerSecond;
    uint32_t m_bmodelLineVertexCount;
    uint32_t m_bmodelCollisionVertexCount;
    uint32_t m_bmodelFaceCount;
    uint32_t m_entityMarkerVertexCount;
    uint32_t m_spawnMarkerVertexCount;
    std::vector<TexturedBModelBatch> m_texturedBModelBatches;
    std::vector<BillboardTextureHandle> m_billboardTextureHandles;
    float m_cameraTargetX;
    float m_cameraTargetY;
    float m_cameraTargetZ;
    float m_cameraYawRadians;
    float m_cameraPitchRadians;
    float m_cameraEyeHeight;
    float m_cameraDistance;
    float m_cameraOrthoScale;
    uint64_t m_lastTickCount;
    bool m_showFilledTerrain;
    bool m_showTerrainWireframe;
    bool m_showBModels;
    bool m_showBModelWireframe;
    bool m_showBModelCollisionFaces;
    bool m_showDecorationBillboards;
    bool m_showActors;
    bool m_showSpriteObjects;
    bool m_showEntities;
    bool m_showSpawns;
    bool m_inspectMode;
    bool m_isRotatingCamera;
    float m_lastMouseX;
    float m_lastMouseY;
    bool m_toggleFilledLatch;
    bool m_toggleWireframeLatch;
    bool m_toggleBModelsLatch;
    bool m_toggleBModelWireframeLatch;
    bool m_toggleBModelCollisionFacesLatch;
    bool m_toggleDecorationBillboardsLatch;
    bool m_toggleActorsLatch;
    bool m_toggleSpriteObjectsLatch;
    bool m_toggleEntitiesLatch;
    bool m_toggleSpawnsLatch;
    bool m_toggleInspectLatch;
    bool m_toggleRunningLatch;
    bool m_toggleFlyingLatch;
    bool m_toggleWaterWalkLatch;
    bool m_toggleFeatherFallLatch;
    std::unique_ptr<OutdoorMovementDriver> m_pOutdoorMovementDriver;
};
}
