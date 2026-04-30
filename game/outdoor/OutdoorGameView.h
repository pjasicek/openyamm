#pragma once

#include "game/app/GameSettings.h"
#include "game/fx/WorldFxRenderResources.h"
#include "game/fx/WorldFxSystem.h"
#include "game/outdoor/OutdoorCollisionData.h"
#include "game/outdoor/OutdoorSpatialFxRuntime.h"
#include "game/maps/MapAssetLoader.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/party/Party.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/CharacterInspectTable.h"
#include "game/events/EventRuntime.h"
#include "game/audio/GameAudioSystem.h"
#include "game/tables/HouseTable.h"
#include "game/tables/JournalAutonoteTable.h"
#include "game/tables/JournalHistoryTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/items/ItemEquipPosTable.h"
#include "game/items/ItemEnchantTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ObjectTable.h"
#include "game/party/PartySpellSystem.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayOverlayAdapters.h"
#include "game/ui/UiLayoutManager.h"
#include "engine/AssetFileSystem.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <array>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <limits>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

struct SDL_Window;

namespace OpenYAMM::Game
{
class GameDataRepository;
class GameSession;
class OutdoorPartyRuntime;
class OutdoorSceneRuntime;
class OutdoorWorldRuntime;
class OutdoorBillboardRenderer;
class OutdoorGameplayInputController;
struct GameplayInputFrame;
class OutdoorInteractionController;
class OutdoorRenderer;
class OutdoorPresentationController;
class GameplayDialogueRenderer;
class GameplayHudRenderer;
class GameplayPartyOverlayRenderer;
class GameplayHudOverlayRenderer;
class GameplayPartyOverlayInputController;
class GameplayOverlayInputController;
class GameplayScreenRuntime;
struct ArcomageLibrary;
class ItemTable;
struct GameApplicationTestAccess;
struct ItemDefinition;

class OutdoorGameView
    : public IGameplayOverlaySceneAdapter
{
public:
    explicit OutdoorGameView(GameSession &gameSession);
    ~OutdoorGameView();

    OutdoorGameView(const OutdoorGameView &) = delete;
    OutdoorGameView &operator=(const OutdoorGameView &) = delete;

    bool initialize(
        const Engine::AssetFileSystem &assetFileSystem,
        const MapStatsEntry &map,
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
        GameAudioSystem *pGameAudioSystem,
        OutdoorSceneRuntime &sceneRuntime,
        const GameSettings &settings);
    void render(int width, int height, const GameplayInputFrame &input, float deltaSeconds);
    void shutdown();
    float cameraYawRadians() const;
    float cameraPitchRadians() const;
    void setCameraAngles(float yawRadians, float pitchRadians);
    void reopenMenuScreen();
    bool requestQuickSave();
    void setSettingsSnapshot(const GameSettings &settings);
    void dumpDebugBModelRenderStateToConsole(uint32_t cogNumber) const;

private:
    friend struct GameApplicationTestAccess;
    friend class GameplayScreenRuntime;
    friend class GameplayHudRenderer;
    friend class GameplayPartyOverlayRenderer;
    friend class GameplayPartyOverlayInputController;
    friend class OutdoorBillboardRenderer;
    friend class OutdoorSpatialFxRuntime;
    friend class OutdoorGameplayInputController;
    friend class OutdoorInteractionController;
    friend class OutdoorRenderer;
    friend class OutdoorPresentationController;

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
        float secretPulse;
        float flowUPerSecond;
        float flowVPerSecond;
        float lavaFlow;
        float fluidFlow;

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

    struct ForcePerspectiveVertex
    {
        float x;
        float y;
        float z;
        float u;
        float v;
        float texW;
        float screenSpace;
        float reciprocalW;
        uint32_t abgr;

        static void init();

        static bgfx::VertexLayout ms_layout;
    };

    struct TexturedBModelBatch
    {
        std::vector<TexturedTerrainVertex> vertices;
        uint32_t faceId = 0;
        uint32_t cogNumber = 0;
        uint32_t baseAttributes = 0;
        size_t bModelIndex = 0;
        size_t faceIndex = 0;
        int textureWidth = 0;
        int textureHeight = 0;
        std::string textureName;
        size_t defaultAnimationIndex = static_cast<size_t>(-1);
    };

    struct BModelTextureAnimationHandle
    {
        std::string textureName;
        std::vector<bgfx::TextureHandle> frameTextureHandles;
        std::vector<uint32_t> frameLengthTicks;
        uint32_t animationLengthTicks = 0;
    };

    struct ResolvedBModelDrawGroup
    {
        bgfx::VertexBufferHandle vertexBufferHandle = BGFX_INVALID_HANDLE;
        uint32_t vertexCount = 0;
        size_t animationIndex = static_cast<size_t>(-1);
    };

    static constexpr size_t OutdoorFxUniformLightCount = 8;

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

    using HudTextureHandle = GameplayHudTextureData;

    struct SkyTextureHandle
    {
        std::string textureName;
        int width = 0;
        int height = 0;
        int physicalWidth = 0;
        int physicalHeight = 0;
        std::vector<uint8_t> bgraPixels;
        uint32_t horizonColorAbgr = 0xff000000u;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

    struct AnimatedWaterTerrainTileState
    {
        OutdoorTerrainAtlasRegion region;
        int tilePadding = 0;
        std::vector<std::vector<uint8_t>> framePixels;
        std::vector<uint32_t> frameLengthTicks;
        uint32_t animationLengthTicks = 0;
        size_t currentFrameIndex = 0;
    };

    using HudFontGlyphMetrics = GameplayHudFontGlyphMetricsData;
    using HudFontHandle = GameplayHudFontData;
    using HudFontColorTextureHandle = GameplayHudFontColorTextureData;
    using HudTextureColorTextureHandle = GameplayHudTextureColorTextureData;

    using HudLayoutAnchor = UiLayoutManager::LayoutAnchor;
    using HudLayoutAttachMode = UiLayoutManager::LayoutAttachMode;
    using HudTextAlignX = UiLayoutManager::TextAlignX;
    using HudTextAlignY = UiLayoutManager::TextAlignY;

    using HudScreenState = GameplayHudScreenState;

    using CharacterPage = GameplayUiController::CharacterPage;
    using CharacterScreenSource = GameplayUiController::CharacterScreenSource;

    using CharacterPointerTargetType = GameplayCharacterPointerTargetType;

public:
    using SpellbookSchool = GameplayUiController::SpellbookSchool;
    using HouseShopMode = GameplayUiController::HouseShopMode;
    using InventoryNestedOverlayMode = GameplayUiController::InventoryNestedOverlayMode;
    using HouseBankInputMode = GameplayUiController::HouseBankInputMode;
    using UtilitySpellOverlayMode = GameplayUiController::UtilitySpellOverlayMode;
    using DialoguePointerTargetType = GameplayDialoguePointerTargetType;
    using DialoguePointerTarget = GameplayDialoguePointerTarget;
    using ChestPointerTargetType = GameplayChestPointerTargetType;
    using ChestPointerTarget = GameplayChestPointerTarget;
    using RenderedInspectableHudItem = GameplayRenderedInspectableHudItem;

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
        uint16_t decorationId = 0;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        int32_t spellId = 0;
        size_t runtimeActorIndex = static_cast<size_t>(-1);
        float hitX = 0.0f;
        float hitY = 0.0f;
        float hitZ = 0.0f;
    };

    struct KeyboardInteractionSamplePoint
    {
        float x = 0.0f;
        float y = 0.0f;
    };

    struct KeyboardInteractionBillboardCandidate
    {
        InspectHit inspectHit;
        float cameraDepth = 0.0f;
        std::array<KeyboardInteractionSamplePoint, 6> samplePoints = {{}};
        size_t samplePointCount = 0;
    };

    enum class DecorationPickMode
    {
        HoverInfo,
        Interaction,
    };

    using SpellbookPointerTargetType = GameplaySpellbookPointerTargetType;

private:
    using ItemInspectSourceType = GameplayUiController::ItemInspectSourceType;

    using CharacterPointerTarget = GameplayCharacterPointerTarget;
    using PendingSpellCastState = GameplayScreenState::PendingSpellTargetState;
    using QuickSpellState = GameplayScreenState::QuickSpellState;
    using AttackActionState = GameplayScreenState::AttackActionState;
    using WorldInteractionInputState = GameplayScreenState::WorldInteractionInputState;
    using GameplayMouseLookState = GameplayScreenState::GameplayMouseLookState;

    using HeldInventoryItemState = GameplayUiController::HeldInventoryItemState;

    struct SpellAreaPreviewCacheState
    {
        bool valid = false;
        uint32_t spellId = 0;
        float targetX = 0.0f;
        float targetY = 0.0f;
        float targetZ = 0.0f;
        float radius = 0.0f;
        float lastRefreshElapsedTime = -1000.0f;
        std::vector<TexturedTerrainVertex> vertices;
    };

    using SpellbookPointerTarget = GameplaySpellbookPointerTarget;

    using SpellbookState = GameplayUiController::SpellbookState;
    using UtilitySpellOverlayState = GameplayUiController::UtilitySpellOverlayState;
    using RestScreenState = GameplayUiController::RestScreenState;
    using RestPointerTargetType = GameplayRestPointerTargetType;
    using RestPointerTarget = GameplayRestPointerTarget;
    using MenuScreenState = GameplayUiController::MenuScreenState;
    using ControlsScreenState = GameplayUiController::ControlsScreenState;
    using ControlsPointerTargetType = GameplayControlsPointerTargetType;
    using ControlsPointerTarget = GameplayControlsPointerTarget;
    using KeyboardScreenState = GameplayUiController::KeyboardScreenState;
    using KeyboardPointerTargetType = GameplayKeyboardPointerTargetType;
    using KeyboardPointerTarget = GameplayKeyboardPointerTarget;
    using VideoOptionsScreenState = GameplayUiController::VideoOptionsScreenState;
    using VideoOptionsPointerTargetType = GameplayVideoOptionsPointerTargetType;
    using VideoOptionsPointerTarget = GameplayVideoOptionsPointerTarget;
    using SaveSlotSummary = GameplayUiController::SaveSlotSummary;
    using JournalScreenState = GameplayUiController::JournalScreenState;
    using JournalView = GameplayUiController::JournalView;
    using JournalNotesCategory = GameplayUiController::JournalNotesCategory;

    using MenuPointerTargetType = GameplayMenuPointerTargetType;
    using SaveLoadPointerTargetType = GameplaySaveLoadPointerTargetType;
    using MenuPointerTarget = GameplayMenuPointerTarget;
    using SaveLoadPointerTarget = GameplaySaveLoadPointerTarget;

    struct PendingSavePreviewCaptureState
    {
        bool active = false;
        bool screenshotRequested = false;
        std::filesystem::path savePath;
        std::string requestId;
        std::string saveName;
        bool closeUiOnSuccess = false;
        uint64_t startedTicks = 0;
    };

    HeldInventoryItemState &heldInventoryItem();
    const HeldInventoryItemState &heldInventoryItem() const;

    GameplayUiController::UtilitySpellOverlayState &utilitySpellOverlay();
    const GameplayUiController::UtilitySpellOverlayState &utilitySpellOverlay() const;
    GameplayUiController::HouseShopOverlayState &houseShopOverlay();
    const GameplayUiController::HouseShopOverlayState &houseShopOverlay() const;

    using HudLayoutElement = UiLayoutManager::LayoutElement;

    using ResolvedHudLayoutElement = GameplayResolvedHudLayoutElement;

public:
    using OverlayResolvedHudLayoutElement = ResolvedHudLayoutElement;
    using OverlayHudScreenState = HudScreenState;

private:

    using SpriteLoadCache = GameplayAssetLoadCache;

public:
    enum class InteractiveDecorationFamily
    {
        None,
        Barrel,
        Cauldron,
        TrashHeap,
        CampFire,
        Cask,
    };

    struct InteractiveDecorationBinding
    {
        bool active = false;
        uint8_t decorVarIndex = 0;
        uint16_t entityIndex = 0;
        uint16_t baseEventId = 0;
        uint8_t eventCount = 0;
        uint8_t initialState = 0;
        bool useSeededInitialState = false;
        bool hideWhenCleared = false;
        InteractiveDecorationFamily family = InteractiveDecorationFamily::None;
    };

    void showStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void showCombatStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void setMouseRotateSpeed(float speed);
    void setWalkSoundEnabled(bool active);
    void setShowHitStatusMessages(bool active);
    void setFlipOnExitEnabled(bool active);
    OutdoorPartyRuntime *partyRuntime() const;
    IGameplayWorldRuntime *worldRuntime() const;
    GameAudioSystem *audioSystem() const;
    const GameDataRepository &data() const;
    float gameplayCameraYawRadians() const override;
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void executeActiveDialogAction() override;
    GameSettings &mutableSettings();
    std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState();
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState() const;
    bool trySaveToSelectedGameSlot() override;
    const GameSettings &settingsSnapshot() const;
    GameplayWorldUiRenderState gameplayUiRenderState(int width, int height) const;
private:
    float effectiveCameraYawRadians() const;
    float effectiveCameraPitchRadians() const;
    void preloadSpriteFrameTextures(const SpriteFrameTable &spriteFrameTable, uint16_t spriteFrameIndex);
    void queueSpriteFrameWarmup(uint16_t spriteFrameIndex);
    void updateHouseVideoPlayback(float deltaSeconds);
    std::optional<std::string> findCachedAssetPath(const std::string &directoryPath, const std::string &fileName);
    std::optional<std::vector<uint8_t>> readCachedBinaryFile(const std::string &assetPath);
    std::optional<std::array<uint8_t, 256 * 3>> loadCachedActPalette(int16_t paletteId);
    std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgraCached(
        const std::string &textureName,
        int16_t paletteId,
        int &width,
        int &height);
    bool hasActiveEventDialog() const;
    void updateItemInspectOverlayState(int width, int height, const GameplayInputFrame &input);
    void updateActorInspectOverlayState(int width, int height, const GameplayInputFrame &input);
    const AdventurersInnMember *selectedAdventurersInnMember() const;
    AdventurersInnMember *selectedAdventurersInnMember();
    void consumePendingWorldAudioEvents();
    void updateFootstepAudio(float deltaSeconds);
    bool activeMemberKnowsSpell(uint32_t spellId) const;
    bool activeMemberHasSpellbookSchool(SpellbookSchool school) const;
    bool tryCastSpellRequest(const PartySpellCastRequest &request, const std::string &spellName) override;
    bool beginSaveWithPreview(const std::filesystem::path &path, const std::string &saveName, bool closeUiOnSuccess);
    void clearWorldInteractionInputLatches();
    float innRestDurationMinutes(uint32_t houseId) const;
    void syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled);
    void syncCursorToGameplayCrosshair();
    const BillboardTextureHandle *findBillboardTexture(const std::string &textureName, int16_t paletteId = 0) const;
    bool m_isInitialized;
    bool m_isRenderable;
    std::optional<MapStatsEntry> m_map;
    std::optional<OutdoorMapData> m_outdoorMapData;
    std::optional<DecorationBillboardSet> m_outdoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> m_outdoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> m_outdoorSpriteObjectBillboardSet;
    std::optional<MapDeltaData> m_outdoorMapDeltaData;
    GameAudioSystem *m_pGameAudioSystem;
    OutdoorSceneRuntime *m_pOutdoorSceneRuntime;
    OutdoorWorldRuntime *m_pOutdoorWorldRuntime;
    OutdoorSpatialFxRuntime m_outdoorSpatialFxRuntime;
    bgfx::VertexBufferHandle m_vertexBufferHandle;
    bgfx::IndexBufferHandle m_indexBufferHandle;
    bgfx::DynamicVertexBufferHandle m_skyVertexBufferHandle;
    bgfx::DynamicVertexBufferHandle m_texturedTerrainVertexBufferHandle;
    bgfx::VertexBufferHandle m_bloodSplatVertexBufferHandle;
    bgfx::VertexBufferHandle m_filledTerrainVertexBufferHandle;
    bgfx::VertexBufferHandle m_bmodelVertexBufferHandle;
    bgfx::VertexBufferHandle m_bmodelCollisionVertexBufferHandle;
    bgfx::VertexBufferHandle m_entityMarkerVertexBufferHandle;
    bgfx::VertexBufferHandle m_spawnMarkerVertexBufferHandle;
    bgfx::ProgramHandle m_programHandle;
    bgfx::ProgramHandle m_texturedTerrainProgramHandle;
    bgfx::ProgramHandle m_spellAreaPreviewProgramHandle;
    bgfx::ProgramHandle m_outdoorLitBillboardProgramHandle;
    bgfx::ProgramHandle m_outdoorTexturedFogProgramHandle;
    bgfx::ProgramHandle m_outdoorForcePerspectiveProgramHandle;
    bgfx::TextureHandle m_terrainTextureAtlasHandle;
    bgfx::TextureHandle m_bloodSplatTextureHandle;
    bgfx::TextureHandle m_forcePerspectiveSolidTextureHandle;
    bgfx::UniformHandle m_terrainTextureSamplerHandle;
    bgfx::UniformHandle m_outdoorBillboardAmbientUniformHandle;
    bgfx::UniformHandle m_outdoorBillboardOverrideColorUniformHandle;
    bgfx::UniformHandle m_outdoorBillboardOutlineParamsUniformHandle;
    bgfx::UniformHandle m_outdoorFxLightPositionsUniformHandle;
    bgfx::UniformHandle m_outdoorFxLightColorsUniformHandle;
    bgfx::UniformHandle m_outdoorFxLightParamsUniformHandle;
    bgfx::UniformHandle m_outdoorFogColorUniformHandle;
    bgfx::UniformHandle m_outdoorFogDensitiesUniformHandle;
    bgfx::UniformHandle m_outdoorFogDistancesUniformHandle;
    bgfx::UniformHandle m_secretPulseParamsUniformHandle;
    bgfx::UniformHandle m_spellAreaPreviewParams0UniformHandle;
    bgfx::UniformHandle m_spellAreaPreviewParams1UniformHandle;
    bgfx::UniformHandle m_spellAreaPreviewColorAUniformHandle;
    bgfx::UniformHandle m_spellAreaPreviewColorBUniformHandle;
    float m_elapsedTime;
    float m_framesPerSecond;
    float m_lastOutdoorFxLightUniformUpdateElapsedTime = -1.0f;
    uint32_t m_bmodelLineVertexCount;
    uint32_t m_bloodSplatVertexCount;
    uint32_t m_bmodelCollisionVertexCount;
    uint32_t m_bmodelFaceCount;
    uint32_t m_entityMarkerVertexCount;
    uint32_t m_spawnMarkerVertexCount;
    std::vector<TexturedBModelBatch> m_texturedBModelBatches;
    std::vector<BModelTextureAnimationHandle> m_bmodelTextureAnimations;
    std::vector<ResolvedBModelDrawGroup> m_resolvedBModelDrawGroups;
    uint64_t m_resolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();
    uint64_t m_bloodSplatVertexBufferRevision = std::numeric_limits<uint64_t>::max();
    std::vector<BillboardTextureHandle> m_billboardTextureHandles;
    WorldFxRenderResources m_worldFxRenderResources;
    std::array<float, OutdoorFxUniformLightCount * 4> m_cachedOutdoorFxLightPositions = {};
    std::array<float, OutdoorFxUniformLightCount * 4> m_cachedOutdoorFxLightColors = {};
    std::array<float, 4> m_cachedOutdoorFxLightParams = {};
    std::unordered_map<int16_t, std::unordered_map<std::string, size_t>> m_billboardTextureIndexByPalette;
    std::unordered_map<std::string, size_t> m_decorationBitmapTextureIndexByName;
    std::vector<SkyTextureHandle> m_skyTextureHandles;
    std::unordered_map<std::string, size_t> m_skyTextureIndexByName;
    std::vector<ForcePerspectiveVertex> m_cachedSkyVertices;
    std::string m_cachedSkyTextureName;
    float m_lastSkyUpdateElapsedTime = -1.0f;
    std::vector<AnimatedWaterTerrainTileState> m_animatedWaterTerrainTiles;
    SpriteLoadCache m_spriteLoadCache;
    std::vector<uint16_t> m_pendingSpriteFrameWarmups;
    std::vector<bool> m_queuedSpriteFrameWarmups;
    size_t m_nextPendingSpriteFrameWarmupIndex;
    size_t m_runtimeActorBillboardTexturesQueuedCount;
    WorldFxSystem m_worldFxSystem;
    std::vector<std::vector<size_t>> m_decorationBillboardGridCells;
    std::vector<InteractiveDecorationBinding> m_interactiveDecorationBindings;
    std::vector<KeyboardInteractionBillboardCandidate> m_keyboardInteractionBillboardCandidates;
    float m_decorationBillboardGridMinX = 0.0f;
    float m_decorationBillboardGridMinY = 0.0f;
    size_t m_decorationBillboardGridWidth = 0;
    size_t m_decorationBillboardGridHeight = 0;
    float m_cameraTargetX;
    float m_cameraTargetY;
    float m_cameraTargetZ;
    float m_cameraYawRadians;
    float m_cameraPitchRadians;
    float m_cameraEyeHeight;
    float m_cameraDistance;
    float m_cameraOrthoScale;
    float m_mouseRotateSpeed = 0.0045f;
    bool m_showFilledTerrain;
    float m_lastFootstepX;
    float m_lastFootstepY;
    bool m_hasLastFootstepPosition;
    float m_walkingMotionHoldSeconds = 0.0f;
    std::optional<SoundId> m_activeWalkingSoundId;
    uint32_t m_activeHouseAudioHostId;
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
    bool m_renderGameplayUiThisFrame;
    bool m_showDebugHud;
    bool m_inspectMode;
    bool m_walkSoundEnabled = true;
    bool m_showHitStatusMessages = true;
    bool m_flipOnExitEnabled = false;
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
    bool m_toggleTextureFilteringLatch;
    bool m_toggleInspectLatch;
    bool m_triggerMeteorLatch;
    bool m_dumpGameplayStateLatch;
    bool m_toggleFlyingLatch;
    bool m_toggleWaterWalkLatch;
    bool m_toggleFeatherFallLatch;
    GameSession &m_gameSession;
    uint64_t m_lastAdventurersInnPortraitClickTicks;
    std::optional<size_t> m_lastAdventurersInnPortraitClickedIndex;
    uint64_t m_lastMeteorShowerImpactSoundTicks = 0;
    uint64_t m_lastStarburstImpactSoundTicks = 0;
    SpellAreaPreviewCacheState m_spellAreaPreviewCache;
    bool m_cachedHoverInspectHitValid;
    uint64_t m_lastHoverInspectUpdateNanoseconds;
    InspectHit m_cachedHoverInspectHit;
    OutdoorPartyRuntime *m_pOutdoorPartyRuntime;
    const Engine::AssetFileSystem *m_pAssetFileSystem;
    GameSettings m_gameSettings = GameSettings::createDefault();
    std::filesystem::path m_autosavePath =
        std::filesystem::path("saves") / "autosave.oysav";
    PendingSavePreviewCaptureState m_pendingSavePreviewCapture;
    int m_lastRenderWidth = 0;
    int m_lastRenderHeight = 0;
};
}
