#pragma once

#include "game/OutdoorCollisionData.h"
#include "game/MapAssetLoader.h"
#include "game/MapStats.h"
#include "game/MonsterTable.h"
#include "game/OutdoorMapData.h"
#include "game/Party.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/CharacterDollTable.h"
#include "game/ChestTable.h"
#include "game/ClassSkillTable.h"
#include "game/EventDialogContent.h"
#include "game/EvtProgram.h"
#include "game/EventIr.h"
#include "game/EventRuntime.h"
#include "game/HouseVideoPlayer.h"
#include "game/HouseTable.h"
#include "game/ItemEquipPosTable.h"
#include "game/NpcDialogTable.h"
#include "game/ObjectTable.h"
#include "game/RosterTable.h"
#include "game/SpellTable.h"
#include "game/StrTable.h"
#include "engine/AssetFileSystem.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <array>
#include <cstdint>
#include <memory>
#include <optional>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class OutdoorPartyRuntime;
class OutdoorWorldRuntime;
class ItemTable;
struct ItemDefinition;

class OutdoorGameView
{
public:
    OutdoorGameView();
    ~OutdoorGameView();

    OutdoorGameView(const OutdoorGameView &) = delete;
    OutdoorGameView &operator=(const OutdoorGameView &) = delete;

    bool initialize(
        const Engine::AssetFileSystem &assetFileSystem,
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
        const ClassSkillTable &classSkillTable,
        const NpcDialogTable &npcDialogTable,
        const RosterTable &rosterTable,
        const CharacterDollTable &characterDollTable,
        const ObjectTable &objectTable,
        const SpellTable &spellTable,
        const ItemTable &itemTable,
        const ItemEquipPosTable &itemEquipPosTable,
        const std::optional<StrTable> &localStrTable,
        const std::optional<EvtProgram> &localEvtProgram,
        const std::optional<EvtProgram> &globalEvtProgram,
        const std::optional<EventIrProgram> &localEventIrProgram,
        const std::optional<EventIrProgram> &globalEventIrProgram,
        OutdoorPartyRuntime *pOutdoorPartyRuntime,
        OutdoorWorldRuntime *pOutdoorWorldRuntime
    );
    void render(int width, int height, float mouseWheelDelta, float deltaSeconds);
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
        int16_t paletteId = 0;
        int width = 0;
        int height = 0;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

    struct HudTextureHandle
    {
        std::string textureName;
        int width = 0;
        int height = 0;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

    struct HudFontGlyphMetrics
    {
        int leftSpacing = 0;
        int width = 0;
        int rightSpacing = 0;
    };

    struct HudFontHandle
    {
        std::string fontName;
        int firstChar = 0;
        int lastChar = 0;
        int fontHeight = 0;
        int atlasCellWidth = 0;
        int atlasWidth = 0;
        int atlasHeight = 0;
        std::array<HudFontGlyphMetrics, 256> glyphMetrics = {{}};
        std::vector<uint8_t> mainAtlasPixels;
        bgfx::TextureHandle mainTextureHandle = BGFX_INVALID_HANDLE;
        bgfx::TextureHandle shadowTextureHandle = BGFX_INVALID_HANDLE;
    };

    struct HudFontColorTextureHandle
    {
        std::string fontName;
        uint32_t colorAbgr = 0xffffffffu;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

    enum class HudLayoutAnchor
    {
        TopLeft,
        TopCenter,
        TopRight,
        Left,
        Center,
        Right,
        BottomLeft,
        BottomCenter,
        BottomRight
    };

    enum class HudLayoutAttachMode
    {
        None,
        RightOf,
        LeftOf,
        Above,
        Below,
        CenterAbove,
        CenterBelow,
        InsideLeft,
        InsideRight,
        InsideTopCenter,
        InsideTopLeft,
        InsideTopRight,
        InsideBottomLeft,
        InsideBottomCenter,
        InsideBottomRight,
        CenterIn
    };

    enum class HudTextAlignX
    {
        Left,
        Center,
        Right
    };

    enum class HudTextAlignY
    {
        Top,
        Middle,
        Bottom
    };

    enum class HudScreenState
    {
        Gameplay,
        Dialogue,
        Character
    };

    enum class CharacterPage
    {
        Stats,
        Skills,
        Inventory,
        Awards
    };

    enum class CharacterPointerTargetType
    {
        None,
        PageButton,
        ExitButton,
        MagnifyButton,
        SkillRow,
        InventoryItem,
        InventoryCell,
        EquipmentSlot,
        DollPanel
    };

    enum class DialoguePointerTargetType
    {
        None,
        Action,
        CloseButton
    };

    struct CharacterPointerTarget
    {
        CharacterPointerTargetType type = CharacterPointerTargetType::None;
        CharacterPage page = CharacterPage::Inventory;
        std::string skillName;
        uint8_t gridX = 0;
        uint8_t gridY = 0;
        EquipmentSlot equipmentSlot = EquipmentSlot::MainHand;

        bool operator==(const CharacterPointerTarget &other) const = default;
    };

    struct HeldInventoryItemState
    {
        bool active = false;
        InventoryItem item = {};
        uint8_t grabCellOffsetX = 0;
        uint8_t grabCellOffsetY = 0;
        float grabOffsetX = 0.0f;
        float grabOffsetY = 0.0f;
    };

    struct ItemInspectOverlayState
    {
        bool active = false;
        uint32_t objectDescriptionId = 0;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceWidth = 0.0f;
        float sourceHeight = 0.0f;
    };

    struct RenderedInspectableHudItem
    {
        uint32_t objectDescriptionId = 0;
        EquipmentSlot equipmentSlot = EquipmentSlot::MainHand;
        std::string textureName;
        float x = 0.0f;
        float y = 0.0f;
        float width = 0.0f;
        float height = 0.0f;
    };

    struct DialoguePointerTarget
    {
        DialoguePointerTargetType type = DialoguePointerTargetType::None;
        size_t index = 0;

        bool operator==(const DialoguePointerTarget &other) const = default;
    };

    struct HudLayoutElement
    {
        std::string id;
        std::string screen;
        HudLayoutAnchor anchor = HudLayoutAnchor::TopLeft;
        std::string parentId;
        HudLayoutAttachMode attachTo = HudLayoutAttachMode::None;
        float gapX = 0.0f;
        float gapY = 0.0f;
        float offsetX = 0.0f;
        float offsetY = 0.0f;
        float width = 0.0f;
        float height = 0.0f;
        std::string bottomToId;
        float bottomGap = 0.0f;
        float minScale = 1.0f;
        float maxScale = 3.0f;
        bool hasExplicitScale = false;
        int zIndex = 0;
        bool visible = true;
        bool interactive = false;
        std::string primaryAsset;
        std::string hoverAsset;
        std::string pressedAsset;
        std::string secondaryAsset;
        std::string tertiaryAsset;
        std::string quaternaryAsset;
        std::string quinaryAsset;
        std::string fontName;
        std::string labelText;
        uint32_t textColorAbgr = 0xffffffffu;
        HudTextAlignX textAlignX = HudTextAlignX::Left;
        HudTextAlignY textAlignY = HudTextAlignY::Top;
        float textPadX = 0.0f;
        float textPadY = 0.0f;
        std::string notes;
    };

    struct ResolvedHudLayoutElement
    {
        float x = 0.0f;
        float y = 0.0f;
        float width = 0.0f;
        float height = 0.0f;
        float scale = 1.0f;
    };

    struct SpriteLoadCache
    {
        std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryAssetPathsByPath;
        std::unordered_map<std::string, std::optional<std::string>> assetPathByKey;
        std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> binaryFilesByPath;
        std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesById;
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
        int16_t npcId = 0;
        uint32_t actorGroup = 0;
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
    static ResolvedHudLayoutElement resolveAttachedHudLayoutRect(
        HudLayoutAttachMode attachTo,
        const ResolvedHudLayoutElement &parent,
        float width,
        float height,
        float gapX,
        float gapY,
        float scale);
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
    bool tryActivateInspectEvent(const InspectHit &inspectHit);
    bool tryTriggerLocalEventById(uint16_t eventId);
    void applyPendingCombatEvents();
    void updateCameraFromInput(float deltaSeconds);
    void buildDecorationBillboardSpatialIndex();
    void collectDecorationBillboardCandidates(float minX, float minY, float maxX, float maxY, std::vector<size_t> &indices) const;
    void renderDecorationBillboards(
        uint16_t viewId,
        uint16_t viewWidth,
        uint16_t viewHeight,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition
    );
    void renderGameplayHudArt(int width, int height);
    void renderGameplayHud(int width, int height) const;
    void renderChestPanel(int width, int height) const;
    void renderEventDialogPanel(int width, int height, bool renderAboveHud);
    void renderActorCollisionOverlays(uint16_t viewId, const bx::Vec3 &cameraPosition) const;
    void renderActorPreviewBillboards(uint16_t viewId, const float *pViewMatrix, const bx::Vec3 &cameraPosition);
    void renderRuntimeProjectiles(uint16_t viewId, const float *pViewMatrix, const bx::Vec3 &cameraPosition);
    void renderSpriteObjectBillboards(uint16_t viewId, const float *pViewMatrix, const bx::Vec3 &cameraPosition);
    void preloadSpriteFrameTextures(const SpriteFrameTable &spriteFrameTable, uint16_t spriteFrameIndex);
    void preloadPendingSpriteFrameWarmupsParallel();
    void queueSpriteFrameWarmup(uint16_t spriteFrameIndex);
    void queueRuntimeActorBillboardTextureWarmup();
    void queueEventSpellBillboardTextureWarmup(const EventIrProgram &eventIrProgram);
    void processPendingSpriteFrameWarmups(size_t maxSpriteFrames);
    bool loadHudLayout(const Engine::AssetFileSystem &assetFileSystem);
    bool loadHudLayoutFile(const Engine::AssetFileSystem &assetFileSystem, const std::string &path);
    const HudLayoutElement *findHudLayoutElement(const std::string &layoutId) const;
    std::vector<std::string> sortedHudLayoutIdsForScreen(const std::string &screen) const;
    int maxHudLayoutZIndexForScreen(const std::string &screen) const;
    static int defaultHudLayoutZIndexForScreen(const std::string &screen);
    const HudFontHandle *findHudFont(const std::string &fontName) const;
    float measureHudTextWidth(const HudFontHandle &font, const std::string &text) const;
    std::string clampHudTextToWidth(const HudFontHandle &font, const std::string &text, float maxWidth) const;
    std::vector<std::string> wrapHudTextToWidth(const HudFontHandle &font, const std::string &text, float maxWidth) const;
    void renderHudFontLayer(
        const HudFontHandle &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale) const;
    bgfx::TextureHandle ensureHudFontMainTextureColor(
        const HudFontHandle &font,
        uint32_t colorAbgr) const;
    void renderLayoutLabel(
        const HudLayoutElement &layout,
        const ResolvedHudLayoutElement &resolved,
        const std::string &label) const;
    const HudTextureHandle *ensureHudTextureLoaded(const std::string &textureName);
    const HudTextureHandle *ensureSolidHudTextureLoaded(const std::string &textureName, uint32_t abgrColor);
    std::optional<ResolvedHudLayoutElement> resolveHudLayoutElement(
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight) const;
    std::optional<ResolvedHudLayoutElement> resolveHudLayoutElementRecursive(
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight,
        std::unordered_set<std::string> &visited) const;
    HudScreenState currentHudScreenState() const;
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void updateStatusBarEvent(float deltaSeconds);
    void updateHouseVideoPlayback(float deltaSeconds);
    void handleDialogueCloseRequest();
    void openDebugNpcDialogue(uint32_t npcId);
    void renderCharacterOverlay(int width, int height, bool renderAboveHud) const;
    void renderDialogueOverlay(int width, int height, bool renderAboveHud);
    void renderHeldInventoryItem(int width, int height) const;
    void renderItemInspectOverlay(int width, int height) const;
    std::optional<std::string> findCachedAssetPath(const std::string &directoryPath, const std::string &fileName);
    std::optional<std::vector<uint8_t>> readCachedBinaryFile(const std::string &assetPath);
    std::optional<std::array<uint8_t, 256 * 3>> loadCachedActPalette(int16_t paletteId);
    std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgraCached(
        const std::string &textureName,
        int16_t paletteId,
        int &width,
        int &height);
    std::optional<std::vector<uint8_t>> loadHudBitmapPixelsBgraCached(
        const std::string &textureName,
        int &width,
        int &height);
    void executeActiveDialogAction();
    void openPendingEventDialog(size_t previousMessageCount, bool allowNpcFallbackContent);
    void closeActiveEventDialog();
    bool hasActiveEventDialog() const;
    std::optional<size_t> resolvePartyPortraitIndexAtPoint(int width, int height, float x, float y);
    bool trySelectPartyMember(size_t memberIndex, bool requireGameplayReady);
    void updateItemInspectOverlayState(int width, int height);
    bool isOpaqueHudPixelAtPoint(const RenderedInspectableHudItem &item, float x, float y) const;
    std::string resolveEquippedItemHudTextureName(
        const ItemDefinition &itemDefinition,
        uint32_t dollTypeId,
        bool hasRightHandWeapon,
        EquipmentSlot slot) const;
    std::optional<ResolvedHudLayoutElement> resolveCharacterEquipmentRenderRect(
        const HudLayoutElement &layout,
        const ItemDefinition &itemDefinition,
        const HudTextureHandle &texture,
        const CharacterDollTypeEntry *pCharacterDollType,
        EquipmentSlot slot,
        int screenWidth,
        int screenHeight) const;
    const BillboardTextureHandle *findBillboardTexture(const std::string &textureName, int16_t paletteId = 0) const;
    const BillboardTextureHandle *ensureSpriteBillboardTexture(const std::string &textureName, int16_t paletteId);
    const HudTextureHandle *findHudTexture(const std::string &textureName) const;
    bool loadHudFont(const Engine::AssetFileSystem &assetFileSystem, const std::string &fontName);
    bool loadHudTexture(const Engine::AssetFileSystem &assetFileSystem, const std::string &textureName);
    bool isPointerInsideResolvedElement(
        const ResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY) const;
    const std::string *resolveInteractiveAssetName(
        const HudLayoutElement &layout,
        const ResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY,
        bool isLeftMousePressed) const;
    const OutdoorWorldRuntime::MapActorState *runtimeActorStateForBillboard(const ActorPreviewBillboard &billboard) const;
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
    std::optional<ClassSkillTable> m_classSkillTable;
    std::optional<NpcDialogTable> m_npcDialogTable;
    const RosterTable *m_pRosterTable;
    const CharacterDollTable *m_pCharacterDollTable;
    std::optional<ChestTable> m_chestTable;
    const ItemTable *m_pItemTable;
    const ItemEquipPosTable *m_pItemEquipPosTable;
    std::optional<StrTable> m_localStrTable;
    std::optional<EvtProgram> m_localEvtProgram;
    std::optional<EvtProgram> m_globalEvtProgram;
    EventRuntime m_eventRuntime;
    std::optional<EventIrProgram> m_localEventIrProgram;
    std::optional<EventIrProgram> m_globalEventIrProgram;
    const ObjectTable *m_pObjectTable;
    const SpellTable *m_pSpellTable;
    OutdoorWorldRuntime *m_pOutdoorWorldRuntime;
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
    std::unordered_map<int16_t, std::unordered_map<std::string, size_t>> m_billboardTextureIndexByPalette;
    SpriteLoadCache m_spriteLoadCache;
    std::vector<uint16_t> m_pendingSpriteFrameWarmups;
    std::vector<bool> m_queuedSpriteFrameWarmups;
    size_t m_nextPendingSpriteFrameWarmupIndex;
    size_t m_runtimeActorBillboardTexturesQueuedCount;
    std::vector<std::vector<size_t>> m_decorationBillboardGridCells;
    float m_decorationBillboardGridMinX = 0.0f;
    float m_decorationBillboardGridMinY = 0.0f;
    size_t m_decorationBillboardGridWidth = 0;
    size_t m_decorationBillboardGridHeight = 0;
    std::vector<HudTextureHandle> m_hudTextureHandles;
    std::vector<HudFontHandle> m_hudFontHandles;
    mutable std::vector<HudFontColorTextureHandle> m_hudFontColorTextureHandles;
    std::vector<std::string> m_hudLayoutOrder;
    std::unordered_map<std::string, HudLayoutElement> m_hudLayoutElements;
    mutable std::unordered_map<std::string, float> m_hudLayoutRuntimeHeightOverrides;
    float m_cameraTargetX;
    float m_cameraTargetY;
    float m_cameraTargetZ;
    float m_cameraYawRadians;
    float m_cameraPitchRadians;
    float m_cameraEyeHeight;
    float m_cameraDistance;
    float m_cameraOrthoScale;
    bool m_showFilledTerrain;
    bool m_showTerrainWireframe;
    bool m_showBModels;
    bool m_showBModelWireframe;
    bool m_showBModelCollisionFaces;
    bool m_showActorCollisionBoxes;
    bool m_showDecorationBillboards;
    bool m_showActors;
    bool m_showSpriteObjects;
    bool m_showEntities;
    bool m_showSpawns;
    bool m_showGameplayHud;
    bool m_showDebugHud;
    bool m_inspectMode;
    bool m_isRotatingCamera;
    float m_lastMouseX;
    float m_lastMouseY;
    bool m_toggleFilledLatch;
    bool m_toggleWireframeLatch;
    bool m_toggleBModelsLatch;
    bool m_toggleBModelWireframeLatch;
    bool m_toggleBModelCollisionFacesLatch;
    bool m_toggleActorCollisionBoxesLatch;
    bool m_toggleDecorationBillboardsLatch;
    bool m_toggleActorsLatch;
    bool m_toggleSpriteObjectsLatch;
    bool m_toggleEntitiesLatch;
    bool m_toggleSpawnsLatch;
    bool m_toggleGameplayHudLatch;
    bool m_toggleDebugHudLatch;
    bool m_toggleInspectLatch;
    bool m_triggerMeteorLatch;
    bool m_debugDialogueLatch;
    bool m_activateInspectLatch;
    bool m_inspectMouseActivateLatch;
    bool m_attackInspectLatch;
    bool m_toggleRunningLatch;
    bool m_toggleFlyingLatch;
    bool m_toggleWaterWalkLatch;
    bool m_toggleFeatherFallLatch;
    bool m_inventoryScreenToggleLatch;
    bool m_characterScreenOpen;
    bool m_characterDollJewelryOverlayOpen;
    CharacterPage m_characterPage;
    bool m_characterClickLatch;
    bool m_characterMemberCycleLatch;
    CharacterPointerTarget m_characterPressedTarget;
    bool m_partyPortraitClickLatch;
    std::optional<size_t> m_partyPortraitPressedIndex;
    uint64_t m_lastPartyPortraitClickTicks;
    std::optional<size_t> m_lastPartyPortraitClickedIndex;
    HeldInventoryItemState m_heldInventoryItem;
    ItemInspectOverlayState m_itemInspectOverlay;
    mutable std::vector<RenderedInspectableHudItem> m_renderedInspectableHudItems;
    mutable HudScreenState m_renderedInspectableHudState = HudScreenState::Gameplay;
    bool m_heldInventoryDropLatch;
    bool m_closeOverlayLatch;
    bool m_dialogueClickLatch;
    DialoguePointerTarget m_dialoguePressedTarget;
    bool m_lootChestItemLatch;
    bool m_chestSelectUpLatch;
    bool m_chestSelectDownLatch;
    bool m_eventDialogSelectUpLatch;
    bool m_eventDialogSelectDownLatch;
    bool m_eventDialogAcceptLatch;
    std::array<bool, 5> m_eventDialogPartySelectLatches;
    size_t m_chestSelectionIndex;
    size_t m_eventDialogSelectionIndex;
    std::string m_statusBarEventText;
    float m_statusBarEventRemainingSeconds;
    EventDialogContent m_activeEventDialog;
    HouseVideoPlayer m_houseVideoPlayer;
    OutdoorPartyRuntime *m_pOutdoorPartyRuntime;
    const Engine::AssetFileSystem *m_pAssetFileSystem;
    InspectHit m_pressedInspectHit;
};
}
