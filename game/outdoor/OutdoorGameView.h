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
#include "game/audio/HouseVideoPlayer.h"
#include "game/audio/GameAudioSystem.h"
#include "game/tables/HouseTable.h"
#include "game/tables/IconFrameTable.h"
#include "game/tables/JournalAutonoteTable.h"
#include "game/tables/JournalHistoryTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/items/ItemEquipPosTable.h"
#include "game/items/ItemEnchantTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ObjectTable.h"
#include "game/party/PartySpellSystem.h"
#include "game/tables/PortraitFxEventTable.h"
#include "game/tables/PortraitFrameTable.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/tables/SpellFxTable.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayOverlayContext.h"
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
class GameplayOverlayContext;
class HudUiService;
struct ArcomageLibrary;
class ItemTable;
struct GameApplicationTestAccess;
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
        const ArcomageLibrary &arcomageLibrary,
        const CharacterDollTable &characterDollTable,
        const CharacterInspectTable &characterInspectTable,
        const ObjectTable &objectTable,
        const SpellTable &spellTable,
        const JournalQuestTable &journalQuestTable,
        const JournalHistoryTable &journalHistoryTable,
        const JournalAutonoteTable &journalAutonoteTable,
        const ItemTable &itemTable,
        const ReadableScrollTable &readableScrollTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const ItemEquipPosTable &itemEquipPosTable,
        GameAudioSystem *pGameAudioSystem,
        OutdoorSceneRuntime &sceneRuntime,
        const GameSettings &settings,
        const std::vector<MapStatsEntry> &mapEntries,
        std::function<bool(
            const std::filesystem::path &,
            const std::string &,
            const std::vector<uint8_t> &,
            std::string &)> saveGameToPathCallback,
        std::function<bool(const std::filesystem::path &, std::string &)> loadGameFromPathCallback,
        std::function<void(const GameSettings &)> settingsChangedCallback
    );
    void render(int width, int height, float mouseWheelDelta, float deltaSeconds);
    void shutdown();
    float cameraYawRadians() const;
    float cameraPitchRadians() const;
    void setCameraAngles(float yawRadians, float pitchRadians);
    void reopenMenuScreen();
    void requestOpenNewGameScreen();
    bool consumePendingOpenNewGameScreenRequest();
    bool consumePendingOpenLoadGameScreenRequest();
    bool requestQuickSave();
    void setSettingsSnapshot(const GameSettings &settings);
    const GameSettings &settingsSnapshot() const;

private:
    friend struct GameApplicationTestAccess;
    friend class GameplayOverlayContext;
    friend class GameplayHudRenderer;
    friend class GameplayPartyOverlayRenderer;
    friend class GameplayPartyOverlayInputController;
    friend class HudUiService;
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

    struct HudTextureHandle
    {
        std::string textureName;
        int width = 0;
        int height = 0;
        int physicalWidth = 0;
        int physicalHeight = 0;
        std::vector<uint8_t> bgraPixels;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

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

    struct HudTextureColorTextureHandle
    {
        std::string textureName;
        uint32_t colorAbgr = 0xffffffffu;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

    using HudLayoutAnchor = UiLayoutManager::LayoutAnchor;
    using HudLayoutAttachMode = UiLayoutManager::LayoutAttachMode;
    using HudTextAlignX = UiLayoutManager::TextAlignX;
    using HudTextAlignY = UiLayoutManager::TextAlignY;

    enum class HudScreenState
    {
        Gameplay,
        Dialogue,
        Character,
        TownPortal,
        LloydsBeacon,
        Chest,
        Spellbook,
        Rest,
        Menu,
        Controls,
        Keyboard,
        VideoOptions,
        SaveGame,
        LoadGame,
        Journal
    };

    using CharacterPage = GameplayUiController::CharacterPage;
    using CharacterScreenSource = GameplayUiController::CharacterScreenSource;

    enum class CharacterPointerTargetType
    {
        None,
        PageButton,
        ExitButton,
        DismissButton,
        MagnifyButton,
        AdventurersInnHireButton,
        AdventurersInnScrollUpButton,
        AdventurersInnScrollDownButton,
        AdventurersInnPortrait,
        StatRow,
        SkillRow,
        InventoryItem,
        InventoryCell,
        EquipmentSlot,
        DollPanel
    };

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

    struct TownPortalDestination
    {
        std::string id;
        std::string label;
        std::string buttonLayoutId;
        std::string mapName;
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        std::optional<int32_t> directionDegrees;
        bool useMapStartPosition = false;
        uint32_t unlockQBitId = 0;
    };

    enum class UtilitySpellPointerTargetType
    {
        None = 0,
        Close,
        TownPortalDestination,
        LloydSetTab,
        LloydRecallTab,
        LloydSlot,
    };

    struct UtilitySpellPointerTarget
    {
        UtilitySpellPointerTargetType type = UtilitySpellPointerTargetType::None;
        size_t index = 0;

        bool operator==(const UtilitySpellPointerTarget &other) const
        {
            return type == other.type && index == other.index;
        }
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

    enum class SpellbookPointerTargetType
    {
        None,
        SchoolButton,
        SpellButton,
        CloseButton,
        QuickCastButton
    };

    enum class MenuPointerTargetType
    {
        None,
        NewGameButton,
        SaveGameButton,
        LoadGameButton,
        ControlsButton,
        QuitButton,
        ReturnButton
    };

    enum class ControlsPointerTargetType
    {
        None,
        ConfigureKeyboardButton,
        VideoOptionsButton,
        TurnRate16Button,
        TurnRate32Button,
        TurnRateSmoothButton,
        WalkSoundButton,
        ShowHitsButton,
        AlwaysRunButton,
        FlipOnExitButton,
        SoundLeftButton,
        SoundTrack,
        SoundRightButton,
        MusicLeftButton,
        MusicTrack,
        MusicRightButton,
        VoiceLeftButton,
        VoiceTrack,
        VoiceRightButton,
        ReturnButton
    };

    enum class KeyboardPointerTargetType
    {
        None,
        BindingRow,
        Page1Button,
        Page2Button,
        DefaultButton,
        BackButton,
        ReturnButton
    };

    enum class VideoOptionsPointerTargetType
    {
        None,
        BloodSplatsButton,
        ColoredLightsButton,
        TintingButton,
        ReturnButton
    };

    enum class SaveLoadPointerTargetType
    {
        None,
        Slot,
        ScrollUpButton,
        ScrollDownButton,
        ConfirmButton,
        CancelButton
    };

private:
    enum class RestPointerTargetType
    {
        None,
        OpenButton,
        Rest8HoursButton,
        WaitUntilDawnButton,
        Wait1HourButton,
        Wait5MinutesButton,
        ExitButton
    };

    enum class InventoryNestedOverlayPointerTargetType
    {
        None,
        CloseButton
    };

    enum class JournalPointerTargetType
    {
        None,
        MainMapView,
        MainQuestsView,
        MainStoryView,
        MainNotesView,
        PrevPageButton,
        NextPageButton,
        NotesPotionButton,
        NotesFountainButton,
        NotesObeliskButton,
        NotesSeerButton,
        NotesMiscButton,
        NotesTrainerButton,
        MapZoomInButton,
        MapZoomOutButton,
        MapPanNorthButton,
        MapPanSouthButton,
        MapPanEastButton,
        MapPanWestButton,
        CloseButton
    };

    using ItemInspectSourceType = GameplayUiController::ItemInspectSourceType;

    struct CharacterPointerTarget
    {
        CharacterPointerTargetType type = CharacterPointerTargetType::None;
        CharacterPage page = CharacterPage::Inventory;
        std::string statName;
        std::string skillName;
        uint8_t gridX = 0;
        uint8_t gridY = 0;
        EquipmentSlot equipmentSlot = EquipmentSlot::MainHand;
        size_t innIndex = 0;

        bool operator==(const CharacterPointerTarget &other) const = default;
    };

    using HeldInventoryItemState = GameplayUiController::HeldInventoryItemState;
    using ItemInspectOverlayState = GameplayUiController::ItemInspectOverlayState;

    struct PortraitFxState
    {
        bool active = false;
        size_t animationId = 0;
        uint32_t startedTicks = 0;
    };

    using CharacterInspectMasteryLine = GameplayUiController::CharacterInspectMasteryLine;
    using CharacterInspectOverlayState = GameplayUiController::CharacterInspectOverlayState;
    using BuffInspectOverlayState = GameplayUiController::BuffInspectOverlayState;
    using CharacterDetailOverlayState = GameplayUiController::CharacterDetailOverlayState;
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

    struct SpellbookPointerTarget
    {
        SpellbookPointerTargetType type = SpellbookPointerTargetType::None;
        SpellbookSchool school = SpellbookSchool::Fire;
        uint32_t spellId = 0;

        bool operator==(const SpellbookPointerTarget &other) const = default;
    };

    using SpellbookState = GameplayUiController::SpellbookState;
    using UtilitySpellOverlayState = GameplayUiController::UtilitySpellOverlayState;
    using RestScreenState = GameplayUiController::RestScreenState;
    using RestMode = GameplayUiController::RestMode;
    using MenuScreenState = GameplayUiController::MenuScreenState;
    using ControlsScreenState = GameplayUiController::ControlsScreenState;
    using KeyboardScreenState = GameplayUiController::KeyboardScreenState;
    using VideoOptionsScreenState = GameplayUiController::VideoOptionsScreenState;
    using SaveSlotSummary = GameplayUiController::SaveSlotSummary;
    using SaveGameScreenState = GameplayUiController::SaveGameScreenState;
    using LoadGameScreenState = GameplayUiController::LoadGameScreenState;
    using JournalScreenState = GameplayUiController::JournalScreenState;
    using JournalView = GameplayUiController::JournalView;
    using JournalNotesCategory = GameplayUiController::JournalNotesCategory;

    struct RestPointerTarget
    {
        RestPointerTargetType type = RestPointerTargetType::None;

        bool operator==(const RestPointerTarget &other) const = default;
    };

    struct InventoryNestedOverlayPointerTarget
    {
        InventoryNestedOverlayPointerTargetType type = InventoryNestedOverlayPointerTargetType::None;

        bool operator==(const InventoryNestedOverlayPointerTarget &other) const = default;
    };

    struct JournalPointerTarget
    {
        JournalPointerTargetType type = JournalPointerTargetType::None;

        bool operator==(const JournalPointerTarget &other) const = default;
    };

    struct MenuPointerTarget
    {
        MenuPointerTargetType type = MenuPointerTargetType::None;

        bool operator==(const MenuPointerTarget &other) const = default;
    };

    struct SaveLoadPointerTarget
    {
        SaveLoadPointerTargetType type = SaveLoadPointerTargetType::None;
        size_t slotIndex = 0;

        bool operator==(const SaveLoadPointerTarget &other) const = default;
    };

    struct ControlsPointerTarget
    {
        ControlsPointerTargetType type = ControlsPointerTargetType::None;
        int sliderValue = 0;

        bool operator==(const ControlsPointerTarget &other) const = default;
    };

    struct KeyboardPointerTarget
    {
        KeyboardPointerTargetType type = KeyboardPointerTargetType::None;
        KeyboardAction action = KeyboardAction::Forward;

        bool operator==(const KeyboardPointerTarget &other) const = default;
    };

    struct VideoOptionsPointerTarget
    {
        VideoOptionsPointerTargetType type = VideoOptionsPointerTargetType::None;

        bool operator==(const VideoOptionsPointerTarget &other) const = default;
    };

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

    struct ResolvedHudLayoutElement
    {
        float x = 0.0f;
        float y = 0.0f;
        float width = 0.0f;
        float height = 0.0f;
        float scale = 1.0f;
    };

public:
    using OverlayResolvedHudLayoutElement = ResolvedHudLayoutElement;
    using OverlayHudScreenState = HudScreenState;

private:

    struct SpriteLoadCache
    {
        std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryAssetPathsByPath;
        std::unordered_map<std::string, std::optional<std::string>> assetPathByKey;
        std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> binaryFilesByPath;
        std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesById;
    };

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

private:
    static ResolvedHudLayoutElement resolveAttachedHudLayoutRect(
        HudLayoutAttachMode attachTo,
        const ResolvedHudLayoutElement &parent,
        float width,
        float height,
        float gapX,
        float gapY,
        float scale);
    void updateCameraFromInput(float deltaSeconds);
    float effectiveCameraYawRadians() const;
    float effectiveCameraPitchRadians() const;
    void renderGameplayHudArt(int width, int height);
    void renderGameplayHud(int width, int height) const;
    void renderChestPanel(int width, int height, bool renderAboveHud) const;
    void renderInventoryNestedOverlay(int width, int height, bool renderAboveHud) const;
    std::optional<ResolvedHudLayoutElement> resolveChestGridArea(int width, int height) const;
    std::optional<ResolvedHudLayoutElement> resolveInventoryNestedOverlayGridArea(int width, int height) const;
    std::optional<ResolvedHudLayoutElement> resolveHouseShopOverlayFrame(int width, int height) const;
    void renderEventDialogPanel(int width, int height, bool renderAboveHud);
    void preloadSpriteFrameTextures(const SpriteFrameTable &spriteFrameTable, uint16_t spriteFrameIndex);
    void queueSpriteFrameWarmup(uint16_t spriteFrameIndex);
    HudScreenState currentHudScreenState() const;
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void updateStatusBarEvent(float deltaSeconds);
    void updateHouseVideoPlayback(float deltaSeconds);
    void renderCharacterOverlay(int width, int height, bool renderAboveHud) const;
    void renderDialogueOverlay(int width, int height, bool renderAboveHud);
    void renderHeldInventoryItem(int width, int height) const;
    void renderItemInspectOverlay(int width, int height) const;
    void renderCharacterInspectOverlay(int width, int height) const;
    void renderBuffInspectOverlay(int width, int height) const;
    void renderCharacterDetailOverlay(int width, int height) const;
    void renderActorInspectOverlay(int width, int height);
    void renderSpellInspectOverlay(int width, int height) const;
    void renderReadableScrollOverlay(int width, int height) const;
    void renderPendingSpellTargetingOverlay(int width, int height) const;
    void renderSpellbookOverlay(int width, int height) const;
    void renderUtilitySpellOverlay(int width, int height) const;
    void renderRestOverlay(int width, int height) const;
    void renderMenuOverlay(int width, int height) const;
    void renderControlsOverlay(int width, int height) const;
    void renderKeyboardOverlay(int width, int height) const;
    void renderVideoOptionsOverlay(int width, int height) const;
    void renderSaveGameOverlay(int width, int height) const;
    void renderLoadGameOverlay(int width, int height) const;
    void renderJournalOverlay(int width, int height) const;
    void submitHudTexturedQuad(const HudTextureHandle &texture, float x, float y, float quadWidth, float quadHeight) const;
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
    void openHouseShopOverlay(uint32_t houseId, HouseShopMode mode);
    void closeHouseShopOverlay();
    void beginHouseBankInput(uint32_t houseId, HouseBankInputMode mode);
    void clearHouseBankState();
    bool hasActiveEventDialog() const;
    std::optional<size_t> resolvePartyPortraitIndexAtPoint(int width, int height, float x, float y);
    std::optional<ResolvedHudLayoutElement> resolvePartyPortraitRect(int width, int height, size_t memberIndex);
    bool trySelectPartyMember(size_t memberIndex, bool requireGameplayReady);
    bool tryAutoPlaceHeldItemOnPartyMember(size_t memberIndex, bool showFailureStatus = true);
    bool tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen);
    void openInventoryNestedOverlay(InventoryNestedOverlayMode mode, uint32_t houseId = 0);
    void closeInventoryNestedOverlay();
    void updateItemInspectOverlayState(int width, int height);
    void tryApplyItemInspectSkillInteraction();
    void updateCharacterInspectOverlayState(int width, int height);
    void updateBuffInspectOverlayState(int width, int height);
    void updateCharacterDetailOverlayState(int width, int height);
    void updateActorInspectOverlayState(int width, int height);
    void updateSpellInspectOverlayState(int width, int height);
    bool loadPortraitAnimationData(const Engine::AssetFileSystem &assetFileSystem);
    bool loadPortraitFxData(const Engine::AssetFileSystem &assetFileSystem);
    void updatePartyPortraitAnimations(float deltaSeconds);
    void updatePortraitAnimation(Character &member, size_t memberIndex, uint32_t deltaTicks);
    void playPortraitExpression(size_t memberIndex, PortraitId portraitId, std::optional<uint32_t> durationTicks = std::nullopt);
    void triggerPortraitFaceAnimation(size_t memberIndex, FaceAnimationId animationId);
    void triggerPortraitFaceAnimationForAllLivingMembers(FaceAnimationId animationId);
    uint32_t defaultPortraitAnimationLengthTicks(PortraitId portraitId) const;
    bool isAdventurersInnCharacterSourceActive() const;
    bool isAdventurersInnScreenActive() const;
    bool isReadOnlyAdventurersInnCharacterViewActive() const;
    const Character *selectedCharacterScreenCharacter() const;
    Character *selectedCharacterScreenCharacter();
    const AdventurersInnMember *selectedAdventurersInnMember() const;
    AdventurersInnMember *selectedAdventurersInnMember();
    std::string resolvePortraitTextureName(const Character &character) const;
    bool triggerPortraitFxAnimation(const std::string &animationName, const std::vector<size_t> &memberIndices);
    void triggerPortraitSpellFx(const PartySpellCastResult &result);
    void triggerPortraitEventFx(const EventRuntimeState::PortraitFxRequest &request);
    void consumePendingPortraitEventFxRequests();
    bool canPlaySpeechReaction(size_t memberIndex, SpeechId speechId, uint32_t nowTicks);
    void playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation);
    void consumePendingPartyAudioRequests();
    void consumePendingEventRuntimeAudioRequests();
    void consumePendingWorldAudioEvents();
    void updateFootstepAudio(float deltaSeconds);
    void renderPortraitFx(size_t memberIndex, float portraitX, float portraitY, float portraitWidth, float portraitHeight) const;
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
    void updateReadableScrollOverlayForHeldItem(size_t memberIndex, const CharacterPointerTarget &pointerTarget, bool isLeftMousePressed);
    void triggerPortraitEventFxWithoutSpeech(size_t memberIndex, PortraitFxEventKind kind);
    bool tryCastSpellRequest(const PartySpellCastRequest &request, const std::string &spellName);
    bool loadTownPortalDestinations(const Engine::AssetFileSystem &assetFileSystem);
    void openSpellbook();
    void closeSpellbook(const std::string &statusText = "");
    void openRestScreen();
    void closeRestScreen();
    void openMenu();
    void closeMenu();
    void openControlsScreen();
    void closeControlsScreen();
    void openKeyboardScreen();
    void closeKeyboardScreenToControls();
    void closeKeyboardScreenToMenu();
    void openVideoOptionsScreen();
    void closeVideoOptionsScreen();
    void openSaveGameScreen();
    void closeSaveGameScreen();
    void openLoadGameScreen();
    void closeLoadGameScreen();
    void openJournal();
    void closeJournal();
    void refreshSaveGameSlots();
    void refreshLoadGameSlots();
    std::string resolveSaveLocationName(const std::string &mapFileName) const;
    bool beginSaveWithPreview(const std::filesystem::path &path, const std::string &saveName, bool closeUiOnSuccess);
    bool trySaveToSelectedGameSlot();
    bool tryLoadFromSelectedGameSlot();
    void commitSettingsChange();
    void clearWorldInteractionInputLatches();
    int restFoodRequired() const;
    float innRestDurationMinutes(uint32_t houseId) const;
    void startInnRest(uint32_t houseId);
    void beginRestAction(RestMode mode, float minutes, bool consumeFood);
    void startRestAction(RestMode mode, float minutes);
    void updateRestScreen(float deltaSeconds);
    void closeReadableScrollOverlay();
    void clearPendingSpellCast(const std::string &statusText = "");
    bool tryResolvePendingSpellCast(
        const InspectHit &actorInspectHit,
        const std::optional<size_t> &portraitMemberIndex,
        const std::optional<bx::Vec3> &fallbackGroundTargetPoint = std::nullopt);
    std::optional<bx::Vec3> resolvePendingSpellGroundTargetPoint(const InspectHit &inspectHit) const;
    std::optional<size_t> resolveRuntimeActorIndexForInspectHit(const InspectHit &inspectHit) const;
    bool shouldEnableGameplayMouseLook() const;
    void syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled);
    void renderGameplayMouseLookOverlay(int width, int height) const;
    bool isOpaqueHudPixelAtPoint(const GameplayRenderedInspectableHudItem &item, float x, float y) const;
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
    bool loadHudFont(const Engine::AssetFileSystem &assetFileSystem, const std::string &fontName);
    bool loadHudTexture(const Engine::AssetFileSystem &assetFileSystem, const std::string &textureName);
    bool m_isInitialized;
    bool m_isRenderable;
    std::optional<MapStatsEntry> m_map;
    std::vector<MapStatsEntry> m_mapEntries;
    std::optional<MonsterTable> m_monsterTable;
    std::optional<OutdoorMapData> m_outdoorMapData;
    std::optional<DecorationBillboardSet> m_outdoorDecorationBillboardSet;
    std::optional<ActorPreviewBillboardSet> m_outdoorActorPreviewBillboardSet;
    std::optional<SpriteObjectBillboardSet> m_outdoorSpriteObjectBillboardSet;
    std::optional<MapDeltaData> m_outdoorMapDeltaData;
    FaceAnimationTable m_faceAnimationTable;
    IconFrameTable m_iconFrameTable;
    PortraitFrameTable m_portraitFrameTable;
    SpellFxTable m_spellFxTable;
    PortraitFxEventTable m_portraitFxEventTable;
    std::optional<HouseTable> m_houseTable;
    std::optional<ClassSkillTable> m_classSkillTable;
    std::optional<NpcDialogTable> m_npcDialogTable;
    std::optional<CharacterInspectTable> m_characterInspectTable;
    const ReadableScrollTable *m_pReadableScrollTable;
    const RosterTable *m_pRosterTable;
    const ArcomageLibrary *m_pArcomageLibrary;
    const CharacterDollTable *m_pCharacterDollTable;
    std::optional<ChestTable> m_chestTable;
    const ItemTable *m_pItemTable;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable;
    const ItemEquipPosTable *m_pItemEquipPosTable;
    const ObjectTable *m_pObjectTable;
    const SpellTable *m_pSpellTable;
    const JournalQuestTable *m_pJournalQuestTable;
    const JournalHistoryTable *m_pJournalHistoryTable;
    const JournalAutonoteTable *m_pJournalAutonoteTable;
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
    std::vector<HudTextureHandle> m_hudTextureHandles;
    std::vector<HudFontHandle> m_hudFontHandles;
    mutable std::vector<HudFontColorTextureHandle> m_hudFontColorTextureHandles;
    mutable std::vector<HudTextureColorTextureHandle> m_hudTextureColorTextureHandles;
    UiLayoutManager m_uiLayoutManager;
    mutable std::unordered_map<std::string, float> m_hudLayoutRuntimeHeightOverrides;
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
    std::vector<PortraitFxState> m_portraitSpellFxStates;
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
    bool m_activateInspectLatch;
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
    bool m_spellbookToggleLatch;
    bool m_spellbookClickLatch;
    bool m_pendingSpellTargetClickLatch;
    bool m_restToggleLatch;
    bool m_restClickLatch;
    bool m_optionsButtonClickLatch;
    bool m_booksButtonClickLatch;
    bool m_menuToggleLatch;
    bool m_menuClickLatch;
    bool m_controlsToggleLatch;
    bool m_controlsClickLatch;
    bool m_keyboardToggleLatch;
    bool m_keyboardClickLatch;
    bool m_videoOptionsToggleLatch;
    bool m_videoOptionsClickLatch;
    bool m_saveGameToggleLatch;
    bool m_saveGameClickLatch;
    bool m_loadGameToggleLatch;
    bool m_loadGameClickLatch;
    bool m_journalToggleLatch;
    bool m_journalClickLatch;
    bool m_inventoryScreenToggleLatch;
    bool m_adventurersInnToggleLatch;
    std::array<uint8_t, SDL_SCANCODE_COUNT> m_previousKeyboardState = {};
    GameplayUiController m_gameplayUiController;
    GameplayDialogController m_gameplayDialogController;
    bool &m_characterScreenOpen;
    bool &m_characterDollJewelryOverlayOpen;
    bool &m_adventurersInnRosterOverlayOpen;
    CharacterPage &m_characterPage;
    CharacterScreenSource &m_characterScreenSource;
    size_t &m_characterScreenSourceIndex;
    size_t &m_adventurersInnScrollOffset;
    bool m_characterClickLatch;
    bool m_characterMemberCycleLatch;
    CharacterPointerTarget m_characterPressedTarget;
    bool m_partyPortraitClickLatch;
    std::optional<size_t> m_partyPortraitPressedIndex;
    uint64_t m_lastPartyPortraitClickTicks;
    std::optional<size_t> m_lastPartyPortraitClickedIndex;
    uint64_t m_lastAdventurersInnPortraitClickTicks;
    std::optional<size_t> m_lastAdventurersInnPortraitClickedIndex;
    std::optional<size_t> m_pendingCharacterDismissMemberIndex;
    uint64_t m_pendingCharacterDismissExpiresTicks;
    HeldInventoryItemState &m_heldInventoryItem;
    ItemInspectOverlayState &m_itemInspectOverlay;
    bool m_itemInspectInteractionLatch;
    uint64_t m_itemInspectInteractionKey;
    CharacterInspectOverlayState &m_characterInspectOverlay;
    BuffInspectOverlayState &m_buffInspectOverlay;
    CharacterDetailOverlayState &m_characterDetailOverlay;
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
    bool m_cachedJournalMapValid = false;
    int m_cachedJournalMapWidth = 0;
    int m_cachedJournalMapHeight = 0;
    int m_cachedJournalMapZoomStep = 0;
    float m_cachedJournalMapCenterX = 0.0f;
    float m_cachedJournalMapCenterY = 0.0f;
    InventoryNestedOverlayState &m_inventoryNestedOverlay;
    HouseShopOverlayState &m_houseShopOverlay;
    HouseBankState &m_houseBankState;
    bool m_utilitySpellClickLatch = false;
    UtilitySpellPointerTarget m_utilitySpellPressedTarget = {};
    std::vector<TownPortalDestination> m_townPortalDestinations;
    bool m_townPortalDestinationsLoaded = false;
    SpellbookPointerTarget m_spellbookPressedTarget;
    RestPointerTarget m_restPressedTarget;
    bool m_optionsButtonPressed = false;
    bool m_booksButtonPressed = false;
    MenuPointerTarget m_menuPressedTarget;
    ControlsPointerTarget m_controlsPressedTarget;
    KeyboardPointerTarget m_keyboardPressedTarget;
    VideoOptionsPointerTarget m_videoOptionsPressedTarget;
    bool m_controlsSliderDragActive = false;
    ControlsPointerTargetType m_controlsDraggedSlider = ControlsPointerTargetType::None;
    SaveLoadPointerTarget m_saveGamePressedTarget;
    SaveLoadPointerTarget m_loadGamePressedTarget;
    uint64_t m_lastSaveGameSlotClickTicks = 0;
    std::optional<size_t> m_lastSaveGameClickedSlotIndex;
    uint64_t m_lastLoadGameSlotClickTicks = 0;
    std::optional<size_t> m_lastLoadGameClickedSlotIndex;
    std::array<bool, 39> m_saveGameEditKeyLatches = {};
    bool m_saveGameEditBackspaceLatch = false;
    JournalPointerTarget m_journalPressedTarget;
    bool m_journalMapKeyZoomLatch = false;
    uint64_t m_lastSpellbookSpellClickTicks;
    uint32_t m_lastSpellbookClickedSpellId;
    uint64_t m_lastSpellFailSoundTicks;
    uint64_t m_lastMeteorShowerImpactSoundTicks = 0;
    uint64_t m_lastStarburstImpactSoundTicks = 0;
    bool m_pendingOpenNewGameScreen = false;
    bool m_pendingOpenLoadGameScreen = false;
    PendingSpellCastState m_pendingSpellCast;
    SpellAreaPreviewCacheState m_spellAreaPreviewCache;
    mutable std::vector<GameplayRenderedInspectableHudItem> m_renderedInspectableHudItems;
    mutable HudScreenState m_renderedInspectableHudState = HudScreenState::Gameplay;
    bool m_heldInventoryDropLatch;
    bool m_closeOverlayLatch;
    bool m_dialogueClickLatch;
    GameplayDialoguePointerTarget m_dialoguePressedTarget;
    bool m_houseShopClickLatch;
    size_t m_houseShopPressedSlotIndex;
    bool m_chestClickLatch;
    bool m_chestItemClickLatch;
    GameplayChestPointerTarget m_chestPressedTarget;
    bool m_inventoryNestedOverlayClickLatch;
    bool m_inventoryNestedOverlayItemClickLatch;
    InventoryNestedOverlayPointerTarget m_inventoryNestedOverlayPressedTarget;
    std::array<bool, 10> m_houseBankDigitLatches;
    bool m_houseBankBackspaceLatch;
    bool m_houseBankConfirmLatch;
    bool m_lootChestItemLatch;
    bool m_chestSelectUpLatch;
    bool m_chestSelectDownLatch;
    bool m_eventDialogSelectUpLatch;
    bool m_eventDialogSelectDownLatch;
    bool m_eventDialogAcceptLatch;
    std::array<bool, 5> m_eventDialogPartySelectLatches;
    size_t m_chestSelectionIndex;
    size_t &m_eventDialogSelectionIndex;
    std::string &m_statusBarHoverText;
    std::string &m_statusBarEventText;
    float &m_statusBarEventRemainingSeconds;
    bool m_cachedHoverInspectHitValid;
    uint64_t m_lastHoverInspectUpdateNanoseconds;
    InspectHit m_cachedHoverInspectHit;
    EventDialogContent &m_activeEventDialog;
    HouseVideoPlayer m_houseVideoPlayer;
    OutdoorPartyRuntime *m_pOutdoorPartyRuntime;
    const Engine::AssetFileSystem *m_pAssetFileSystem;
    GameSettings m_gameSettings = GameSettings::createDefault();
    std::function<bool(
        const std::filesystem::path &,
        const std::string &,
        const std::vector<uint8_t> &,
        std::string &)> m_saveGameToPathCallback;
    std::filesystem::path m_autosavePath =
        std::filesystem::path("saves") / "autosave.oysav";
    std::function<bool(const std::filesystem::path &, std::string &)> m_loadGameFromPathCallback;
    std::function<void(const GameSettings &)> m_settingsChangedCallback;
    PendingSavePreviewCaptureState m_pendingSavePreviewCapture;
    InspectHit m_pressedInspectHit;
    int m_lastRenderWidth = 0;
    int m_lastRenderHeight = 0;
};
}
