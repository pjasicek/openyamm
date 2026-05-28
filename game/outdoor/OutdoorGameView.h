#pragma once

#include "game/app/GameSettings.h"
#include "game/fx/WorldFxRenderResources.h"
#include "game/fx/WorldFxSystem.h"
#include "game/outdoor/OutdoorCollisionData.h"
#include "game/outdoor/OutdoorLightingRuntime.h"
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
#include "game/items/ItemEnchantTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ObjectTable.h"
#include "game/party/PartySpellSystem.h"
#include "game/render/lighting/LightingStats.h"
#include "game/render/AnimatedModelRenderer.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/mm9/Mm9DialoguePackage.h"
#include "game/mm9/Mm9DialogueRuntime.h"
#include "game/mm9/Mm9ScriptRuntime.h"
#include "game/mm9/Mm9AnimatedActorVisual.h"
#include "game/mm9/Mm9ScriptedObjectRuntime.h"
#include "game/mm9/Mm9ScriptedBillboardVisuals.h"
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
#include <deque>
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
struct OutdoorGameViewMm9TestAccess;
struct ItemDefinition;

struct TerrainTextureAtlasMipPixels
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};

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
        const std::optional<OutdoorSceneData> &outdoorSceneData,
        const std::optional<Mm9EventsData> &mm9EventsData,
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
    bool requestTravelAutosave();
    void setSettingsSnapshot(const GameSettings &settings);
    bool executeEventHooks(EventRuntimeHookKind kind);

private:
    friend struct GameApplicationTestAccess;
    friend struct OutdoorGameViewMm9TestAccess;
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
        bx::Vec3 boundsMin = {0.0f, 0.0f, 0.0f};
        bx::Vec3 boundsMax = {0.0f, 0.0f, 0.0f};
        bool hasBounds = false;
    };

    struct TexturedTerrainChunk
    {
        bgfx::VertexBufferHandle vertexBufferHandle = BGFX_INVALID_HANDLE;
        uint32_t vertexCount = 0;
        bx::Vec3 boundsMin = {0.0f, 0.0f, 0.0f};
        bx::Vec3 boundsMax = {0.0f, 0.0f, 0.0f};
        int32_t cellX = 0;
        int32_t cellY = 0;
        uint32_t stableId = 0;
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
        bx::Vec3 boundsMin = {0.0f, 0.0f, 0.0f};
        bx::Vec3 boundsMax = {0.0f, 0.0f, 0.0f};
        bool hasBounds = false;
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

    struct Mm9AnimatedActorTextureHandle
    {
        std::string textureName;
        int width = 0;
        int height = 0;
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

    struct ViewDistanceCache
    {
        std::string sourceValue;
        float farClipDistance = 18000.0f;
        float runtimeProjectileDistance = 12288.0f;
        float runtimeProjectileDistanceSquared = 12288.0f * 12288.0f;
        float decorationBillboardDistance = 18000.0f;
        float decorationBillboardDistanceSquared = 18000.0f * 18000.0f;
        float actorBillboardDistance = 18000.0f;
        float actorBillboardDistanceSquared = 18000.0f * 18000.0f;
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
        std::string mm9MapId;
        std::string mm9ObjectId;
        size_t mm9SourceObjectIndex = 0;
        std::string mm9SourceClass;
        std::string mm9SourceName;
        std::string mm9VisualId;
        std::string mm9SourceModel;
        std::string mm9SourceSkin;
        std::string mm9ScriptName;
        std::string mm9ScriptParams;
        float mm9CollisionRadius = 0.0f;
        float mm9CollisionHeight = 0.0f;
        std::string mm9MovementState;
        std::string mm9CurrentClip;
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

    using Mm9ScriptedBillboardInstance = Mm9ScriptedObject;

    struct Mm9AnimatedActorInstance
    {
        Mm9AnimatedActorVisual visual;
        std::shared_ptr<AnimatedModelAsset> asset;
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
    const std::vector<Mm9ScriptedObject> &mm9ScriptedBillboardInstances() const;
    const std::vector<Mm9AnimatedActorInstance> &mm9AnimatedActorInstances() const;
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
    void updateCombatFeedback(float deltaSeconds);
    void renderCombatFeedbackOverlay(
        int width,
        int height,
        const float *pViewProjectionMatrix);
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
    void syncCursorToGameplayCrosshair(SDL_Window *pWindow = nullptr);
    void refreshViewDistanceCache();
    const BillboardTextureHandle *findBillboardTexture(const std::string &textureName, int16_t paletteId = 0) const;

    struct CombatFloatingText
    {
        size_t actorIndex = 0;
        int amount = 0;
        std::string text;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float remainingSeconds = 0.0f;
        float durationSeconds = 0.0f;
        uint32_t colorAbgr = 0xffffffffu;
        float fontScale = 1.0f;
    };

    struct CombatTargetState
    {
        bool active = false;
        size_t actorIndex = 0;
        float remainingSeconds = 0.0f;
    };

    bool m_isInitialized;
    bool m_isRenderable;
    std::optional<MapStatsEntry> m_map;
    std::optional<OutdoorMapData> m_outdoorMapData;
    std::optional<DecorationBillboardSet> m_outdoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> m_outdoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> m_outdoorSpriteObjectBillboardSet;
    std::optional<Mm9ScriptedBillboardVisualSet> m_mm9ScriptedBillboardVisuals;
    std::optional<Mm9ScriptedObjectRuntime> m_mm9ScriptedObjectRuntime;
    std::vector<Mm9ScriptedBillboardInstance> m_mm9ScriptedBillboardInstances;
    std::vector<Mm9AnimatedActorInstance> m_mm9AnimatedActorInstances;
    std::optional<MapDeltaData> m_outdoorMapDeltaData;
    GameAudioSystem *m_pGameAudioSystem;
    OutdoorSceneRuntime *m_pOutdoorSceneRuntime;
    OutdoorWorldRuntime *m_pOutdoorWorldRuntime;
    OutdoorSpatialFxRuntime m_outdoorSpatialFxRuntime;
    OutdoorLightingRuntime m_outdoorLightingRuntime;
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
    std::vector<TerrainTextureAtlasMipPixels> m_terrainTextureAtlasMipPixels;
    int m_terrainTextureAtlasWidth = 0;
    int m_terrainTextureAtlasHeight = 0;
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
    std::vector<TexturedTerrainChunk> m_texturedTerrainChunks;
    std::vector<TexturedBModelBatch> m_texturedBModelBatches;
    std::vector<BModelTextureAnimationHandle> m_bmodelTextureAnimations;
    std::vector<ResolvedBModelDrawGroup> m_resolvedBModelDrawGroups;
    uint64_t m_resolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();
    uint64_t m_bloodSplatVertexBufferRevision = std::numeric_limits<uint64_t>::max();
    std::deque<BillboardTextureHandle> m_billboardTextureHandles;
    AnimatedModelRenderResources m_animatedModelRenderResources;
    std::vector<Mm9AnimatedActorTextureHandle> m_mm9AnimatedActorTextureHandles;
    WorldFxRenderResources m_worldFxRenderResources;
    std::array<float, OutdoorFxUniformLightCount * 4> m_cachedOutdoorFxLightPositions = {};
    std::array<float, OutdoorFxUniformLightCount * 4> m_cachedOutdoorFxLightColors = {};
    std::array<float, 4> m_cachedOutdoorFxLightParams = {};
    LightingStats m_outdoorLightingStats = {};
    float m_lastOutdoorLightingStatsLogElapsedTime = 0.0f;
    struct OutdoorSpriteRenderDiagnostics
    {
        uint64_t decorationItems = 0;
        uint64_t decorationBatchSubmits = 0;
        uint64_t decorationBatchedItems = 0;
        uint64_t decorationTextureGroups = 0;
        uint64_t decorationSubmits = 0;
        uint64_t decorationOutlineSubmits = 0;
        uint64_t decorationTextureSwitches = 0;
        uint64_t actorItems = 0;
        uint64_t actorBatchSubmits = 0;
        uint64_t actorBatchedItems = 0;
        uint64_t actorSubmits = 0;
        uint64_t actorOutlineSubmits = 0;
        uint64_t actorTextureSwitches = 0;
        uint64_t combinedDepthSlices = 0;
        uint64_t combinedDepthSliceTextureGroups = 0;
        uint64_t combinedDepthSliceItems = 0;
        uint64_t worldItemItems = 0;
        uint64_t worldItemBatchSubmits = 0;
        uint64_t worldItemBatchedItems = 0;
        uint64_t worldItemSubmits = 0;
        uint64_t worldItemOutlineSubmits = 0;
        uint64_t worldItemTextureSwitches = 0;
        uint64_t worldItemDepthSlices = 0;
        uint64_t worldItemDepthSliceTextureGroups = 0;
        uint64_t worldItemDepthSliceItems = 0;
        uint64_t runtimeProjectileItems = 0;
        uint64_t runtimeProjectileBatchSubmits = 0;
        uint64_t runtimeProjectileBatchedItems = 0;
        uint64_t runtimeProjectileTextureGroups = 0;
        uint64_t staticSpriteObjectItems = 0;
        uint64_t staticSpriteObjectBatchSubmits = 0;
        uint64_t staticSpriteObjectBatchedItems = 0;
        uint64_t staticSpriteObjectSubmits = 0;
        uint64_t staticSpriteObjectTextureSwitches = 0;
        uint64_t fxGlowItems = 0;
        uint64_t fxGlowSubmits = 0;
        uint64_t fxContactShadowItems = 0;
        uint64_t fxContactShadowSubmits = 0;
    };

    struct OutdoorAnimatedModelRenderDiagnostics
    {
        uint64_t visibleAnimatedModels = 0;
        uint64_t evaluatedSkeletons = 0;
        uint64_t evaluatedNodes = 0;
        uint64_t renderPrepDrawItems = 0;
        uint64_t submittedDraws = 0;
        uint64_t submittedTriangles = 0;
        uint64_t uploadedBoneMatrices = 0;
        uint64_t materialSwitches = 0;
        uint64_t textureUploads = 0;
        uint64_t missingTextures = 0;
        uint64_t failedTextureUploads = 0;
        uint64_t skippedDrawItems = 0;
        uint64_t cpuAnimationNanoseconds = 0;
    };

    OutdoorSpriteRenderDiagnostics m_outdoorSpriteRenderDiagnostics = {};
    OutdoorAnimatedModelRenderDiagnostics m_outdoorAnimatedModelRenderDiagnostics = {};
    std::unordered_map<int16_t, std::unordered_map<std::string, size_t>> m_billboardTextureIndexByPalette;
    std::unordered_map<std::string, size_t> m_decorationBitmapTextureIndexByName;
    std::unordered_map<std::string, size_t> m_mm9AnimatedActorTextureIndexByName;
    std::vector<SkyTextureHandle> m_skyTextureHandles;
    std::unordered_map<std::string, size_t> m_skyTextureIndexByName;
    std::vector<ForcePerspectiveVertex> m_cachedSkyVertices;
    std::string m_cachedSkyTextureName;
    float m_lastSkyUpdateElapsedTime = -1.0f;
    std::shared_ptr<std::vector<OutdoorBitmapTexture>> m_pendingActorPreviewTexturePreload;
    size_t m_nextPendingActorPreviewTextureUploadIndex = 0;
    std::vector<AnimatedWaterTerrainTileState> m_animatedWaterTerrainTiles;
    std::optional<uint32_t> m_lastAnimatedWaterAnimationTicks;
    SpriteLoadCache m_spriteLoadCache;
    std::vector<uint16_t> m_pendingSpriteFrameWarmups;
    std::vector<bool> m_queuedSpriteFrameWarmups;
    size_t m_nextPendingSpriteFrameWarmupIndex;
    size_t m_runtimeActorBillboardTexturesQueuedCount;
    uint64_t m_renderableStartTickNanoseconds = 0;
    uint64_t m_renderFrameIndex = 0;
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
    bool m_walkSoundEnabled = true;
    bool m_showHitStatusMessages = true;
    bool m_flipOnExitEnabled = false;
    bool m_isRotatingCamera;
    float m_lastMouseX;
    float m_lastMouseY;
    uint64_t m_lastGameplayMouseLookCursorSyncTicks = 0;
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
    std::optional<Mm9DialoguePackage> m_mm9DialoguePackage;
    std::unique_ptr<Mm9DialogueRuntime> m_mm9DialogueRuntime;
    std::unique_ptr<Mm9ScriptRuntime> m_mm9ScriptRuntime;
    GameSettings m_gameSettings = GameSettings::createDefault();
    ViewDistanceCache m_viewDistanceCache;
    std::filesystem::path m_autosavePath =
        std::filesystem::path("saves") / "autosave.oysav";
    PendingSavePreviewCaptureState m_pendingSavePreviewCapture;
    int m_lastRenderWidth = 0;
    int m_lastRenderHeight = 0;
    std::vector<CombatFloatingText> m_combatFloatingTexts;
    CombatTargetState m_combatTargetState;
};
}
