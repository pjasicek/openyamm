#pragma once

#include "game/app/GameSettings.h"
#include "game/fx/ParticleSystem.h"
#include "game/outdoor/OutdoorCollisionData.h"
#include "game/outdoor/OutdoorFxRuntime.h"
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
#include "game/events/EventDialogContent.h"
#include "game/events/EventRuntime.h"
#include "game/tables/FaceAnimationTable.h"
#include "game/audio/GameAudioSystem.h"
#include "game/tables/HouseTable.h"
#include "game/tables/JournalAutonoteTable.h"
#include "game/tables/JournalHistoryTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/items/ItemEquipPosTable.h"
#include "game/items/ItemEnchantTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ObjectTable.h"
#include "game/party/PartySpellSystem.h"
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
class OutdoorInteractionController;
class OutdoorRenderer;
class OutdoorPresentationController;
class ParticleRenderer;
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
    void render(int width, int height, float mouseWheelDelta, float deltaSeconds);
    void shutdown();
    float cameraYawRadians() const;
    float cameraPitchRadians() const;
    void setCameraAngles(float yawRadians, float pitchRadians);
    void reopenMenuScreen();
    bool requestQuickSave();
    void setSettingsSnapshot(const GameSettings &settings);

private:
    friend struct GameApplicationTestAccess;
    friend class GameplayScreenRuntime;
    friend class GameplayHudRenderer;
    friend class GameplayPartyOverlayRenderer;
    friend class GameplayPartyOverlayInputController;
    friend class OutdoorBillboardRenderer;
    friend class OutdoorFxRuntime;
    friend class OutdoorGameplayInputController;
    friend class OutdoorInteractionController;
    friend class OutdoorRenderer;
    friend class OutdoorPresentationController;
    friend class ParticleRenderer;

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
    static constexpr float HeldGameplayActionRepeatDebounceSeconds = 0.14f;

    enum class QuickSpellCastResult
    {
        CastStarted,
        AttackFallback,
        Failed
    };

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

    using HeldInventoryItemState = GameplayUiController::HeldInventoryItemState;
    using ItemInspectOverlayState = GameplayUiController::ItemInspectOverlayState;

    using ActorInspectOverlayState = GameplayUiController::ActorInspectOverlayState;
    using SpellInspectOverlayState = GameplayUiController::SpellInspectOverlayState;
    using ReadableScrollOverlayState = GameplayUiController::ReadableScrollOverlayState;

    struct PendingSpellCastState
    {
        bool active = false;
        size_t casterMemberIndex = 0;
        uint32_t spellId = 0;
        uint32_t skillLevelOverride = 0;
        SkillMastery skillMasteryOverride = SkillMastery::None;
        bool spendMana = true;
        bool applyRecovery = true;
        PartySpellCastTargetKind targetKind = PartySpellCastTargetKind::None;
        std::string spellName;
    };

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
    using RestMode = GameplayUiController::RestMode;
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
    using SaveGameScreenState = GameplayUiController::SaveGameScreenState;
    using LoadGameScreenState = GameplayUiController::LoadGameScreenState;
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

    using InventoryNestedOverlayState = GameplayUiController::InventoryNestedOverlayState;
    using HouseShopOverlayState = GameplayUiController::HouseShopOverlayState;
    using HouseBankState = GameplayUiController::HouseBankState;

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
    bool tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen) override;
    void triggerPortraitFaceAnimation(size_t memberIndex, FaceAnimationId animationId) override;
    void updateReadableScrollOverlayForHeldItem(
        size_t memberIndex,
        const CharacterPointerTarget &pointerTarget,
        bool isLeftMousePressed);
    void closeReadableScrollOverlay();
    void playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation) override;
    bool tryCastSpellFromMember(
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName) override;
    GameSettings &mutableSettings();
    std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState();
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState() const;
    bool trySaveToSelectedGameSlot() override;
    const GameSettings &settingsSnapshot() const;
private:
    void updateCameraFromInput(float mouseWheelDelta, float deltaSeconds);
    float effectiveCameraYawRadians() const;
    float effectiveCameraPitchRadians() const;
    void preloadSpriteFrameTextures(const SpriteFrameTable &spriteFrameTable, uint16_t spriteFrameIndex);
    void queueSpriteFrameWarmup(uint16_t spriteFrameIndex);
    void updateHouseVideoPlayback(float deltaSeconds);
    void renderPendingSpellTargetingOverlay(int width, int height) const;
    std::optional<std::string> findCachedAssetPath(const std::string &directoryPath, const std::string &fileName);
    std::optional<std::vector<uint8_t>> readCachedBinaryFile(const std::string &assetPath);
    std::optional<std::array<uint8_t, 256 * 3>> loadCachedActPalette(int16_t paletteId);
    std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgraCached(
        const std::string &textureName,
        int16_t paletteId,
        int &width,
        int &height);
    void openHouseShopOverlay(uint32_t houseId, HouseShopMode mode);
    void closeHouseShopOverlay();
    void beginHouseBankInput(uint32_t houseId, HouseBankInputMode mode);
    void clearHouseBankState();
    bool hasActiveEventDialog() const;
    void openInventoryNestedOverlay(InventoryNestedOverlayMode mode, uint32_t houseId = 0);
    void updateItemInspectOverlayState(int width, int height);
    void tryApplyWorldItemInspectSkillInteraction();
    void updateActorInspectOverlayState(int width, int height);
    bool loadPortraitAnimationData(const Engine::AssetFileSystem &assetFileSystem);
    bool loadPortraitFxData(const Engine::AssetFileSystem &assetFileSystem);
    void updatePartyPortraitAnimations(float deltaSeconds);
    void updatePortraitAnimation(Character &member, size_t memberIndex, uint32_t deltaTicks);
    void playPortraitExpression(size_t memberIndex, PortraitId portraitId, std::optional<uint32_t> durationTicks = std::nullopt);
    void triggerPortraitFaceAnimationForAllLivingMembers(FaceAnimationId animationId);
    uint32_t defaultPortraitAnimationLengthTicks(PortraitId portraitId) const;
    const AdventurersInnMember *selectedAdventurersInnMember() const;
    AdventurersInnMember *selectedAdventurersInnMember();
    bool triggerPortraitFxAnimation(const std::string &animationName, const std::vector<size_t> &memberIndices);
    void triggerPortraitSpellFx(const PartySpellCastResult &result);
    void triggerPortraitEventFx(const EventRuntimeState::PortraitFxRequest &request);
    bool canPlaySpeechReaction(size_t memberIndex, SpeechId speechId, uint32_t nowTicks);
    void consumePendingPartyAudioRequests();
    void consumePendingEventRuntimeAudioRequests();
    void consumePendingWorldAudioEvents();
    void updateFootstepAudio(float deltaSeconds);
    QuickSpellCastResult tryBeginQuickSpellCast();
    bool tryCastSpellFromMember(
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName,
        bool quickCast = false);
    bool activeMemberKnowsSpell(uint32_t spellId) const;
    bool activeMemberHasSpellbookSchool(SpellbookSchool school) const;
    bool tryResolveQuickCastRequest(PartySpellCastRequest &request, const PartySpellDescriptor &descriptor) const;
    bool isSpellQuickCastable(const PartySpellDescriptor &descriptor) const;
    std::optional<size_t> resolveQuickCastHoveredActorIndex() const;
    std::optional<size_t> resolveClosestQuickCastVisibleActorIndex(float sourceX, float sourceY, float sourceZ) const;
    bool buildQuickCastInspectRayForScreenPoint(float screenX, float screenY, bx::Vec3 &rayOrigin, bx::Vec3 &rayDirection) const;
    std::optional<bx::Vec3> resolveQuickCastCursorTargetPoint(float cursorX, float cursorY) const;
    void triggerPortraitEventFxWithoutSpeech(size_t memberIndex, PortraitFxEventKind kind);
    bool tryCastSpellRequest(const PartySpellCastRequest &request, const std::string &spellName) override;
    void closeSpellbook(const std::string &statusText = "");
    void closeInventoryNestedOverlay();
    void refreshSaveGameSlots();
    std::string resolveSaveLocationName(const std::string &mapFileName) const;
    bool beginSaveWithPreview(const std::filesystem::path &path, const std::string &saveName, bool closeUiOnSuccess);
    void clearWorldInteractionInputLatches();
    float innRestDurationMinutes(uint32_t houseId) const;
    void startInnRest(uint32_t houseId);
    void beginRestAction(RestMode mode, float minutes, bool consumeFood);
    void startRestAction(RestMode mode, float minutes);
    void completeRestAction(bool closeRestScreenAfterCompletion);
    void updateRestScreen(float deltaSeconds);
    void clearPendingSpellCast(const std::string &statusText = "");
    bool tryResolvePendingSpellCast(
        const InspectHit &actorInspectHit,
        const std::optional<size_t> &portraitMemberIndex,
        const std::optional<bx::Vec3> &fallbackGroundTargetPoint = std::nullopt);
    std::optional<bx::Vec3> resolvePendingSpellGroundTargetPoint(const InspectHit &inspectHit) const;
    std::optional<size_t> resolveRuntimeActorIndexForInspectHit(const InspectHit &inspectHit) const;
    bool shouldEnableGameplayMouseLook() const;
    void syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled);
    const BillboardTextureHandle *findBillboardTexture(const std::string &textureName, int16_t paletteId = 0) const;
    bool m_isInitialized;
    bool m_isRenderable;
    std::optional<MapStatsEntry> m_map;
    std::optional<OutdoorMapData> m_outdoorMapData;
    std::optional<DecorationBillboardSet> m_outdoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> m_outdoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> m_outdoorSpriteObjectBillboardSet;
    std::optional<MapDeltaData> m_outdoorMapDeltaData;
    FaceAnimationTable m_faceAnimationTable;
    GameAudioSystem *m_pGameAudioSystem;
    OutdoorSceneRuntime *m_pOutdoorSceneRuntime;
    OutdoorWorldRuntime *m_pOutdoorWorldRuntime;
    OutdoorFxRuntime m_outdoorFxRuntime;
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
    bgfx::ProgramHandle m_particleProgramHandle;
    bgfx::ProgramHandle m_outdoorTexturedFogProgramHandle;
    bgfx::ProgramHandle m_outdoorForcePerspectiveProgramHandle;
    bgfx::TextureHandle m_terrainTextureAtlasHandle;
    bgfx::TextureHandle m_bloodSplatTextureHandle;
    bgfx::TextureHandle m_forcePerspectiveSolidTextureHandle;
    bgfx::UniformHandle m_terrainTextureSamplerHandle;
    bgfx::UniformHandle m_particleParamsUniformHandle;
    bgfx::UniformHandle m_outdoorBillboardAmbientUniformHandle;
    bgfx::UniformHandle m_outdoorBillboardOverrideColorUniformHandle;
    bgfx::UniformHandle m_outdoorBillboardOutlineParamsUniformHandle;
    bgfx::UniformHandle m_outdoorFxLightPositionsUniformHandle;
    bgfx::UniformHandle m_outdoorFxLightColorsUniformHandle;
    bgfx::UniformHandle m_outdoorFxLightParamsUniformHandle;
    bgfx::UniformHandle m_outdoorFogColorUniformHandle;
    bgfx::UniformHandle m_outdoorFogDensitiesUniformHandle;
    bgfx::UniformHandle m_outdoorFogDistancesUniformHandle;
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
    std::array<float, OutdoorFxUniformLightCount * 4> m_cachedOutdoorFxLightPositions = {};
    std::array<float, OutdoorFxUniformLightCount * 4> m_cachedOutdoorFxLightColors = {};
    std::array<float, 4> m_cachedOutdoorFxLightParams = {};
    std::unordered_map<int16_t, std::unordered_map<std::string, size_t>> m_billboardTextureIndexByPalette;
    std::array<uint16_t, 6> m_particleTextureHandleIndices = {{
        bgfx::kInvalidHandle,
        bgfx::kInvalidHandle,
        bgfx::kInvalidHandle,
        bgfx::kInvalidHandle,
        bgfx::kInvalidHandle,
        bgfx::kInvalidHandle
    }};
    std::array<std::vector<LitBillboardVertex>, 12> m_particleVertexBatches;
    std::unordered_map<std::string, size_t> m_decorationBitmapTextureIndexByName;
    std::vector<SkyTextureHandle> m_skyTextureHandles;
    std::unordered_map<std::string, size_t> m_skyTextureIndexByName;
    std::vector<ForcePerspectiveVertex> m_cachedSkyVertices;
    std::string m_cachedSkyTextureName;
    float m_lastSkyUpdateElapsedTime = -1.0f;
    std::vector<AnimatedWaterTerrainTileState> m_animatedWaterTerrainTiles;
    SpriteLoadCache m_spriteLoadCache;
    uint32_t m_lastPortraitAnimationUpdateTicks = 0;
    std::vector<uint16_t> m_pendingSpriteFrameWarmups;
    std::vector<bool> m_queuedSpriteFrameWarmups;
    size_t m_nextPendingSpriteFrameWarmupIndex;
    size_t m_runtimeActorBillboardTexturesQueuedCount;
    float m_particleUpdateAccumulatorSeconds = 0.0f;
    ParticleSystem m_particleSystem;
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
    std::vector<uint32_t> m_memberSpeechCooldownUntilTicks;
    std::vector<uint32_t> m_memberCombatSpeechCooldownUntilTicks;
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
    bool m_showDebugHud;
    bool m_inspectMode;
    bool m_walkSoundEnabled = true;
    bool m_showHitStatusMessages = true;
    bool m_flipOnExitEnabled = false;
    bool m_gameplayMouseLookActive = false;
    bool m_gameplayCursorModeActive = false;
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
    bool m_toggleRainLatch;
    bool m_keyboardUseLatch;
    bool m_inspectMouseActivateLatch;
    bool m_attackInspectLatch;
    bool m_attackReadyMemberAvailableWhileHeld;
    float m_attackInspectRepeatCooldownSeconds;
    float m_quickSpellCastRepeatCooldownSeconds;
    bool m_toggleRunningLatch;
    bool m_toggleFlyingLatch;
    bool m_toggleWaterWalkLatch;
    bool m_toggleFeatherFallLatch;
    bool m_quickSpellCastLatch;
    bool m_quickSpellReadyMemberAvailableWhileHeld;
    bool m_quickSpellAttackFallbackRequested;
    bool m_pendingSpellTargetClickLatch;
    bool m_adventurersInnToggleLatch;
    GameSession &m_gameSession;
    GameplayUiController &m_gameplayUiController;
    GameplayDialogController &m_gameplayDialogController;
    GameplayOverlayInteractionState &m_overlayInteractionState;
    bool &m_characterScreenOpen;
    bool &m_characterDollJewelryOverlayOpen;
    bool &m_adventurersInnRosterOverlayOpen;
    CharacterPage &m_characterPage;
    CharacterScreenSource &m_characterScreenSource;
    size_t &m_characterScreenSourceIndex;
    size_t &m_adventurersInnScrollOffset;
    uint64_t m_lastAdventurersInnPortraitClickTicks;
    std::optional<size_t> m_lastAdventurersInnPortraitClickedIndex;
    HeldInventoryItemState &m_heldInventoryItem;
    ItemInspectOverlayState &m_itemInspectOverlay;
    ActorInspectOverlayState &m_actorInspectOverlay;
    SpellInspectOverlayState &m_spellInspectOverlay;
    ReadableScrollOverlayState &m_readableScrollOverlay;
    SpellbookState &m_spellbook;
    UtilitySpellOverlayState &m_utilitySpellOverlay;
    RestScreenState &m_restScreen;
    MenuScreenState &m_menuScreen;
    ControlsScreenState &m_controlsScreen;
    KeyboardScreenState &m_keyboardScreen;
    VideoOptionsScreenState &m_videoOptionsScreen;
    SaveGameScreenState &m_saveGameScreen;
    LoadGameScreenState &m_loadGameScreen;
    JournalScreenState &m_journalScreen;
    InventoryNestedOverlayState &m_inventoryNestedOverlay;
    HouseShopOverlayState &m_houseShopOverlay;
    HouseBankState &m_houseBankState;
    uint64_t m_lastSpellFailSoundTicks;
    uint64_t m_lastMeteorShowerImpactSoundTicks = 0;
    uint64_t m_lastStarburstImpactSoundTicks = 0;
    PendingSpellCastState m_pendingSpellCast;
    SpellAreaPreviewCacheState m_spellAreaPreviewCache;
    bool m_heldInventoryDropLatch;
    size_t &m_eventDialogSelectionIndex;
    std::string &m_statusBarHoverText;
    std::string &m_statusBarEventText;
    float &m_statusBarEventRemainingSeconds;
    bool m_cachedHoverInspectHitValid;
    uint64_t m_lastHoverInspectUpdateNanoseconds;
    InspectHit m_cachedHoverInspectHit;
    EventDialogContent &m_activeEventDialog;
    OutdoorPartyRuntime *m_pOutdoorPartyRuntime;
    const Engine::AssetFileSystem *m_pAssetFileSystem;
    GameSettings m_gameSettings = GameSettings::createDefault();
    std::filesystem::path m_autosavePath =
        std::filesystem::path("saves") / "autosave.oysav";
    PendingSavePreviewCaptureState m_pendingSavePreviewCapture;
    InspectHit m_pressedInspectHit;
    int m_lastRenderWidth = 0;
    int m_lastRenderHeight = 0;
};
}
