#pragma once

#include "editor/document/EditorSession.h"
#include "editor/import/ObjModelImport.h"
#include "game/events/EventRuntime.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <array>
#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Editor
{
class EditorOutdoorViewport
{
public:
    enum class PreviewMaterialMode
    {
        Textured,
        Clay,
        Grid
    };

    enum class TransformGizmoMode
    {
        Translate,
        Rotate
    };

    enum class TransformSpaceMode
    {
        World,
        Local
    };

    enum class IndoorDoorFaceEditMode
    {
        None,
        Add,
        Remove
    };

    struct PreviewVertex
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        uint32_t abgr = 0xffffffffu;

        static void init();

        static bgfx::VertexLayout ms_layout;
    };

    struct TexturedPreviewVertex
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float u = 0.0f;
        float v = 0.0f;

        static void init();

        static bgfx::VertexLayout ms_layout;
    };

    struct ProceduralPreviewVertex
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float u = 0.0f;
        float v = 0.0f;
        float normalX = 0.0f;
        float normalY = 0.0f;
        float normalZ = 1.0f;
        float reserved = 0.0f;

        static void init();

        static bgfx::VertexLayout ms_layout;
    };

    EditorOutdoorViewport();
    ~EditorOutdoorViewport();

    EditorOutdoorViewport(const EditorOutdoorViewport &) = delete;
    EditorOutdoorViewport &operator=(const EditorOutdoorViewport &) = delete;

    void shutdown();
    void updateAndRender(
        EditorSession &session,
        int viewportX,
        int viewportY,
        uint16_t viewportWidth,
        uint16_t viewportHeight,
        bool isHovered,
        bool isFocused,
        bool leftMouseClicked,
        bool leftMouseDown,
        float mouseX,
        float mouseY,
        float deltaSeconds);
    void renderOverlayUi(const EditorSession &session);
    void setPlacementKind(EditorSelectionKind kind);
    EditorSelectionKind placementKind() const;
    struct ImportedModelPreviewRequest
    {
        enum class TargetMode
        {
            ReplaceSelectedBModel,
            NewImportPlacement
        };

        std::string sourcePath;
        std::string sourceMeshName;
        float importScale = 1.0f;
        bool mergeCoplanarFaces = false;
        TargetMode targetMode = TargetMode::NewImportPlacement;
        size_t bmodelIndex = std::numeric_limits<size_t>::max();
    };
    bool snapEnabled() const;
    void setSnapEnabled(bool enabled);
    int snapStep() const;
    void setSnapStep(int step);
    bool showTerrainFill() const;
    void setShowTerrainFill(bool enabled);
    bool showTerrainGrid() const;
    void setShowTerrainGrid(bool enabled);
    PreviewMaterialMode previewMaterialMode() const;
    void setPreviewMaterialMode(PreviewMaterialMode mode);
    bool forcePreviewOnSelectedOnly() const;
    void setForcePreviewOnSelectedOnly(bool enabled);
    bool showBModels() const;
    void setShowBModels(bool enabled);
    bool showIndoorPortals() const;
    void setShowIndoorPortals(bool enabled);
    bool showIndoorFloors() const;
    void setShowIndoorFloors(bool enabled);
    bool showIndoorCeilings() const;
    void setShowIndoorCeilings(bool enabled);
    bool showIndoorGizmosEverywhere() const;
    void setShowIndoorGizmosEverywhere(bool enabled);
    std::optional<uint16_t> isolatedIndoorRoomId() const;
    void setIsolatedIndoorRoomId(std::optional<uint16_t> roomId);
    bool showBModelWireframe() const;
    void setShowBModelWireframe(bool enabled);
    bool showEntities() const;
    void setShowEntities(bool enabled);
    bool showEntityBillboards() const;
    void setShowEntityBillboards(bool enabled);
    bool showSpawns() const;
    void setShowSpawns(bool enabled);
    bool showActors() const;
    void setShowActors(bool enabled);
    bool showActorBillboards() const;
    void setShowActorBillboards(bool enabled);
    bool showSpriteObjects() const;
    void setShowSpriteObjects(bool enabled);
    bool showSpawnActorBillboards() const;
    void setShowSpawnActorBillboards(bool enabled);
    bool showEventMarkers() const;
    void setShowEventMarkers(bool enabled);
    bool showChestLinks() const;
    void setShowChestLinks(bool enabled);
    void setImportedModelPreviewRequest(const std::optional<ImportedModelPreviewRequest> &request);
    TransformGizmoMode transformGizmoMode() const;
    void setTransformGizmoMode(TransformGizmoMode mode);
    TransformSpaceMode transformSpaceMode() const;
    void setTransformSpaceMode(TransformSpaceMode mode);
    void focusSelection(const EditorDocument &document, const EditorSelection &selection);
    void focusBModel(const EditorDocument &document, size_t bmodelIndex);
    void previewIndoorMechanismOpen(const EditorDocument &document, size_t doorIndex);
    void previewIndoorMechanismClose(const EditorDocument &document, size_t doorIndex);
    void previewIndoorMechanismSimulate(const EditorDocument &document, size_t doorIndex);
    void setIndoorMechanismPreviewState(
        const EditorDocument &document,
        size_t doorIndex,
        const Game::RuntimeMechanismState &state);
    void clearIndoorMechanismPreview(const EditorDocument &document);
    bool tryGetIndoorMechanismPreview(
        const EditorDocument &document,
        size_t doorIndex,
        uint16_t &state,
        float &distance,
        bool &isMoving) const;
    void setIndoorDoorFaceEditMode(IndoorDoorFaceEditMode mode, std::optional<size_t> doorIndex = std::nullopt);
    IndoorDoorFaceEditMode indoorDoorFaceEditMode() const;
    std::optional<size_t> indoorDoorFaceEditDoorIndex() const;

    const bx::Vec3 &cameraPosition() const;
    float cameraYawRadians() const;
    float cameraPitchRadians() const;
    bgfx::TextureHandle viewportTextureHandle() const;
    bgfx::TextureHandle terrainTextureAtlasHandle() const;
    bool tryGetTerrainTilePreviewUv(uint8_t tileId, float &u0, float &v0, float &u1, float &v1) const;

private:
    struct MarkerCandidate
    {
        EditorSelectionKind selectionKind = EditorSelectionKind::None;
        size_t selectionIndex = 0;
        bx::Vec3 worldPosition = {0.0f, 0.0f, 0.0f};
        float pickRadiusPixels = 18.0f;
        bool hasBillboardBounds = false;
        float billboardWorldWidth = 0.0f;
        float billboardWorldHeight = 0.0f;
        bool blockedByLineOfSight = false;
    };

    enum class GizmoDragMode
    {
        None,
        TranslatePlaneXY,
        TranslateX,
        TranslateY,
        TranslateZ,
        RotateX,
        RotateY,
        RotateZ
    };

    struct ActiveGizmoDrag
    {
        GizmoDragMode mode = GizmoDragMode::None;
        EditorSelection selection = {};
        bx::Vec3 startWorldPosition = {0.0f, 0.0f, 0.0f};
        float startMouseX = 0.0f;
        float startMouseY = 0.0f;
        float startScreenX = 0.0f;
        float startScreenY = 0.0f;
        float xAxisScreenX = 0.0f;
        float xAxisScreenY = 0.0f;
        float yAxisScreenX = 0.0f;
        float yAxisScreenY = 0.0f;
        float zAxisScreenX = 0.0f;
        float zAxisScreenY = 0.0f;
        float axisWorldLength = 1024.0f;
        bx::Vec3 xAxisWorld = {1.0f, 0.0f, 0.0f};
        bx::Vec3 yAxisWorld = {0.0f, 1.0f, 0.0f};
        bx::Vec3 zAxisWorld = {0.0f, 0.0f, 1.0f};
        float rotateHandleRadiusWorld = 0.0f;
        bx::Vec3 rotateAxisWorld = {0.0f, 0.0f, 1.0f};
        bx::Vec3 startRotateVectorWorld = {1.0f, 0.0f, 0.0f};
        std::vector<Game::OutdoorBModelVertex> startBModelVertices;
        EditorBModelSourceTransform startSourceTransform = {};
        bool hasStartSourceTransform = false;
        bool mutated = false;
    };

    struct ActiveCameraFocus
    {
        bool active = false;
        bx::Vec3 startPosition = {0.0f, 0.0f, 0.0f};
        bx::Vec3 targetPosition = {0.0f, 0.0f, 0.0f};
        float startYawRadians = 0.0f;
        float targetYawRadians = 0.0f;
        float startPitchRadians = 0.0f;
        float targetPitchRadians = 0.0f;
        float progressSeconds = 0.0f;
        float durationSeconds = 0.22f;
    };

    struct ActiveTerrainPaint
    {
        bool active = false;
        size_t lastFlatIndex = std::numeric_limits<size_t>::max();
        int anchorCellX = std::numeric_limits<int>::min();
        int anchorCellY = std::numeric_limits<int>::min();
        int lastCellX = std::numeric_limits<int>::min();
        int lastCellY = std::numeric_limits<int>::min();
        bool mutated = false;
    };

    struct ActiveTerrainSculpt
    {
        bool active = false;
        int anchorSampleX = std::numeric_limits<int>::min();
        int anchorSampleY = std::numeric_limits<int>::min();
        int anchorHeight = 0;
        int lastSampleX = std::numeric_limits<int>::min();
        int lastSampleY = std::numeric_limits<int>::min();
        int flattenTargetHeight = 0;
        bool hasFlattenTargetHeight = false;
        bool mutated = false;
    };

    struct PendingSpriteObjectPlacementPreview
    {
        int x = 0;
        int y = 0;
        int z = 0;
    };

    struct PendingEntityPlacementPreview
    {
        int x = 0;
        int y = 0;
        int z = 0;
    };

    struct PendingActorPlacementPreview
    {
        int x = 0;
        int y = 0;
        int z = 0;
    };

    struct PendingSpawnPlacementPreview
    {
        int x = 0;
        int y = 0;
        int z = 0;
    };

    bool ensureRenderResources();
    void destroyImportedModelPreview();
    void destroyGeometryBuffers();
    void ensureRenderTarget(uint16_t viewportWidth, uint16_t viewportHeight);
    void destroyRenderTarget();
    void ensureGeometryBuffers(const EditorSession &session);
    void ensureImportedModelPreview(const EditorSession &session);
    void updateCamera(
        const EditorDocument &document,
        bool isHovered,
        bool isFocused,
        float deltaSeconds);
    void resetCameraToDocument(const EditorDocument &document);
    bool tryPick(
        EditorSession &session,
        bool leftMouseClicked,
        float mouseX,
        float mouseY);
    bool trySelectTerrainCell(
        EditorSession &session,
        bool leftMouseClicked,
        float mouseX,
        float mouseY);
    void finishTerrainStroke(EditorSession &session);
    bool trySelectInteractiveFace(
        EditorSession &session,
        bool leftMouseClicked,
        float mouseX,
        float mouseY);
    bool tryPlaceObject(
        EditorSession &session,
        bool leftMouseClicked,
        float mouseX,
        float mouseY);
    bool tryBeginGizmoDrag(
        EditorSession &session,
        bool leftMouseClicked,
        float mouseX,
        float mouseY);
    void updateGizmoDrag(
        EditorSession &session,
        bool leftMouseDown,
        float mouseX,
        float mouseY);
    std::optional<bx::Vec3> selectedWorldPosition(
        const EditorDocument &document,
        const EditorSelection &selection) const;
    bool decodeSelectedTerrainCell(
        const EditorSelection &selection,
        int &cellX,
        int &cellY) const;
    bool decodeSelectedInteractiveFace(
        const EditorDocument &document,
        const EditorSelection &selection,
        size_t &bmodelIndex,
        size_t &faceIndex) const;
    bool computeMouseRay(float mouseX, float mouseY, bx::Vec3 &origin, bx::Vec3 &direction) const;
    bool sampleTerrainWorldPosition(
        const EditorDocument &document,
        float mouseX,
        float mouseY,
        bx::Vec3 &worldPosition) const;
    bool samplePlacementWorldPosition(
        const EditorDocument &document,
        float mouseX,
        float mouseY,
        bx::Vec3 &worldPosition) const;
    int snapIndoorActorZToFloor(const EditorDocument &document, int x, int y, int z) const;
    bool setSelectedWorldPosition(EditorSession &session, const bx::Vec3 &worldPosition);
    void submitStaticGeometry(const EditorSession &session) const;
    void submitEntityBillboardGeometry(const EditorSession &session, const EditorDocument &document) const;
    void submitMarkerGeometry(const EditorSession &session, const EditorDocument &document, const EditorSelection &selection);
    void ensureIndoorMechanismPreviewDocument(const EditorDocument &document) const;
    void advanceIndoorMechanismPreview(const EditorDocument &document, float deltaSeconds);
    void invalidateIndoorMechanismPreview();
    const std::vector<Game::IndoorVertex> &indoorRenderVertices(const EditorDocument &document) const;
    Game::IndoorFaceGeometryCache &indoorRenderFaceGeometryCache(const EditorDocument &document) const;
    void refreshIndoorPreviewGeometryBuffers(const EditorDocument &document);

    static std::string documentGeometryKey(const EditorDocument &document);
    static std::string documentCameraKey(const EditorDocument &document);

    struct TexturedBatch
    {
        bgfx::VertexBufferHandle vertexBufferHandle = BGFX_INVALID_HANDLE;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
        uint32_t vertexCount = 0;
        size_t bmodelIndex = std::numeric_limits<size_t>::max();
        bx::Vec3 objectOrigin = {0.0f, 0.0f, 0.0f};
        std::string key;
        int textureWidth = 0;
        int textureHeight = 0;
    };

    struct ProceduralBatch
    {
        bgfx::VertexBufferHandle vertexBufferHandle = BGFX_INVALID_HANDLE;
        uint32_t vertexCount = 0;
        size_t bmodelIndex = std::numeric_limits<size_t>::max();
        bx::Vec3 objectOrigin = {0.0f, 0.0f, 0.0f};
        std::string key;
    };

    struct ClayPreviewSettings
    {
        std::array<float, 4> baseColor = {0.66f, 0.64f, 0.61f, 1.0f};
        float slopeAccentStrength = 0.18f;
        float shadowStrength = 0.34f;
        float lightWrap = 0.2f;
    };

    struct GridPreviewSettings
    {
        std::array<float, 4> baseColorA = {0.28f, 0.30f, 0.32f, 1.0f};
        std::array<float, 4> baseColorB = {0.18f, 0.20f, 0.22f, 1.0f};
        std::array<float, 4> minorLineColor = {0.52f, 0.54f, 0.56f, 1.0f};
        std::array<float, 4> majorLineColor = {0.78f, 0.80f, 0.82f, 1.0f};
        float cellSize = 256.0f;
        float majorInterval = 8.0f;
        float lineThickness = 0.035f;
        float majorLineThickness = 0.08f;
    };

    struct SpriteBillboardTexture
    {
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
        int width = 0;
        int height = 0;
    };

    struct SpriteBillboardTextureKey
    {
        std::string textureName;
        int16_t paletteId = 0;

        bool operator==(const SpriteBillboardTextureKey &other) const
        {
            return paletteId == other.paletteId && textureName == other.textureName;
        }
    };

    struct SpriteBillboardTextureKeyHash
    {
        size_t operator()(const SpriteBillboardTextureKey &key) const
        {
            const size_t textureHash = std::hash<std::string>{}(key.textureName);
            const size_t paletteHash = std::hash<int16_t>{}(key.paletteId);
            return textureHash ^ (paletteHash + 0x9e3779b9u + (textureHash << 6) + (textureHash >> 2));
        }
    };

    std::string m_geometryKey;
    std::string m_cameraDocumentKey;
    bgfx::ProgramHandle m_programHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_texturedProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_proceduralPreviewProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_previewColorAHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_previewColorBHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_previewColorCHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_previewColorDHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_previewParams0Handle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_previewParams1Handle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_previewObjectOriginHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_colorTextureHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_depthTextureHandle = BGFX_INVALID_HANDLE;
    bgfx::FrameBufferHandle m_frameBufferHandle = BGFX_INVALID_HANDLE;
    bgfx::VertexBufferHandle m_terrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    bgfx::VertexBufferHandle m_terrainErrorVertexBufferHandle = BGFX_INVALID_HANDLE;
    bgfx::VertexBufferHandle m_texturedTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_terrainTextureAtlasHandle = BGFX_INVALID_HANDLE;
    std::array<std::array<float, 4>, 256> m_terrainTilePreviewUvs = {};
    std::array<bool, 256> m_terrainTilePreviewValid = {};
    bgfx::VertexBufferHandle m_bmodelWireVertexBufferHandle = BGFX_INVALID_HANDLE;
    uint32_t m_terrainVertexCount = 0;
    uint32_t m_terrainErrorVertexCount = 0;
    uint32_t m_texturedTerrainVertexCount = 0;
    uint32_t m_bmodelWireVertexCount = 0;
    std::vector<TexturedBatch> m_bmodelTexturedBatches;
    std::vector<ProceduralBatch> m_bmodelAllFaceBatches;
    std::vector<ProceduralBatch> m_indoorPortalBatches;
    std::vector<ProceduralBatch> m_bmodelUnassignedBatches;
    std::vector<ProceduralBatch> m_bmodelMissingAssetBatches;
    std::optional<ImportedModelPreviewRequest> m_importedModelPreviewRequest;
    std::string m_importedModelPreviewKey;
    ProceduralBatch m_importedModelPreviewBatch = {};
    mutable std::unordered_map<SpriteBillboardTextureKey, SpriteBillboardTexture, SpriteBillboardTextureKeyHash>
        m_entityBillboardTextures;
    std::string m_cachedOutdoorTerrainGridKey;
    std::vector<PreviewVertex> m_cachedOutdoorTerrainGridVertices;
    bx::Vec3 m_cameraPosition = {0.0f, -24000.0f, 9000.0f};
    float m_cameraYawRadians = 0.0f;
    float m_cameraPitchRadians = -0.35f;
    bool m_cameraInitializedForDocument = false;
    bool m_shutdownComplete = false;
    int m_viewportX = 0;
    int m_viewportY = 0;
    uint16_t m_viewportWidth = 1;
    uint16_t m_viewportHeight = 1;
    uint16_t m_renderWidth = 1;
    uint16_t m_renderHeight = 1;
    bool m_isHovered = false;
    bool m_isFocused = false;
    float m_lastMouseX = 0.0f;
    float m_lastMouseY = 0.0f;
    float m_viewMatrix[16] = {};
    float m_projectionMatrix[16] = {};
    float m_viewProjectionMatrix[16] = {};
    std::vector<MarkerCandidate> m_markerCandidates;
    ActiveGizmoDrag m_activeGizmoDrag = {};
    ActiveCameraFocus m_activeCameraFocus = {};
    ActiveTerrainPaint m_activeTerrainPaint = {};
    ActiveTerrainSculpt m_activeTerrainSculpt = {};
    std::optional<PendingEntityPlacementPreview> m_pendingEntityPlacementPreview;
    std::optional<PendingActorPlacementPreview> m_pendingActorPlacementPreview;
    std::optional<PendingSpawnPlacementPreview> m_pendingSpawnPlacementPreview;
    std::optional<PendingSpriteObjectPlacementPreview> m_pendingSpriteObjectPlacementPreview;
    bool m_hoverTerrainValid = false;
    int m_hoverTerrainCellX = 0;
    int m_hoverTerrainCellY = 0;
    std::vector<size_t> m_lastFacePickCandidates;
    float m_lastFacePickMouseX = 0.0f;
    float m_lastFacePickMouseY = 0.0f;
    size_t m_lastFacePickCycleIndex = 0;
    bool m_showTerrainFill = true;
    bool m_showTerrainGrid = true;
    PreviewMaterialMode m_previewMaterialMode = PreviewMaterialMode::Textured;
    bool m_forcePreviewOnSelectedOnly = false;
    bool m_showBModels = true;
    bool m_showIndoorPortals = true;
    bool m_showIndoorFloors = true;
    bool m_showIndoorCeilings = true;
    bool m_showIndoorGizmosEverywhere = false;
    std::optional<uint16_t> m_isolatedIndoorRoomId;
    bool m_showBModelWireframe = false;
    bool m_showEntities = true;
    bool m_showEntityBillboards = true;
    bool m_showSpawns = true;
    bool m_showActors = true;
    bool m_showActorBillboards = true;
    bool m_showSpriteObjects = true;
    bool m_showSpawnActorBillboards = true;
    bool m_showEventMarkers = true;
    bool m_showChestLinks = true;
    ClayPreviewSettings m_clayPreviewSettings = {};
    ClayPreviewSettings m_indoorPortalPreviewSettings = {
        {0.26f, 0.84f, 0.92f, 0.48f},
        0.10f,
        0.16f,
        0.24f};
    GridPreviewSettings m_gridPreviewSettings = {};
    GridPreviewSettings m_errorPreviewSettings = {
        {0.90f, 0.04f, 0.90f, 1.0f},
        {0.10f, 0.02f, 0.10f, 1.0f},
        {0.00f, 0.00f, 0.00f, 1.0f},
        {1.00f, 0.55f, 1.00f, 1.0f},
        128.0f,
        4.0f,
        0.06f,
        0.12f};
    mutable std::string m_indoorMechanismPreviewDocumentKey;
    mutable std::unordered_map<size_t, Game::RuntimeMechanismState> m_indoorMechanismPreviewOverrides;
    IndoorDoorFaceEditMode m_indoorDoorFaceEditMode = IndoorDoorFaceEditMode::None;
    std::optional<size_t> m_indoorDoorFaceEditDoorIndex;
    mutable std::string m_indoorRenderVerticesKey;
    mutable std::vector<Game::IndoorVertex> m_indoorRenderVertices;
    mutable std::string m_indoorFaceGeometryCacheKey;
    mutable Game::IndoorFaceGeometryCache m_indoorFaceGeometryCache;
    mutable std::string m_indoorMarkerVisibilityKey;
    mutable std::unordered_map<std::string, bool> m_indoorMarkerLineOfSightBlockedByKey;
    mutable std::string m_indoorActorFloorSnapKey;
    mutable std::unordered_map<uint64_t, int> m_indoorActorFloorSnapZByKey;
    uint64_t m_indoorMechanismPreviewRevision = 0;
    float m_indoorMechanismPreviewAccumulatorSeconds = 0.0f;
    bool m_indoorPreviewGeometryBuffersDirty = false;
    TransformGizmoMode m_transformGizmoMode = TransformGizmoMode::Translate;
    TransformSpaceMode m_transformSpaceMode = TransformSpaceMode::World;
    bool m_snapEnabled = true;
    int m_snapStep = 32;
    EditorSelectionKind m_placementKind = EditorSelectionKind::None;
};
}
