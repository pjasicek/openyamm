#pragma once

#include "game/outdoor/OutdoorCollisionData.h"
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
#include "game/events/EvtProgram.h"
#include "game/events/EventIr.h"
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
#include "game/tables/StrTable.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayOverlayContext.h"
#include "game/ui/UiLayoutManager.h"
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
class OutdoorSceneRuntime;
class OutdoorWorldRuntime;
class OutdoorBillboardRenderer;
class OutdoorGameplayInputController;
class OutdoorInteractionController;
class OutdoorRenderer;
class OutdoorPresentationController;
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
        const std::optional<StrTable> &localStrTable,
        const std::optional<EvtProgram> &localEvtProgram,
        const std::optional<EvtProgram> &globalEvtProgram,
        GameAudioSystem *pGameAudioSystem,
        OutdoorSceneRuntime &sceneRuntime
    );
    void render(int width, int height, float mouseWheelDelta, float deltaSeconds);
    void shutdown();
    float cameraYawRadians() const;
    float cameraPitchRadians() const;
    void setCameraAngles(float yawRadians, float pitchRadians);

private:
    friend struct GameApplicationTestAccess;
    friend class GameplayOverlayContext;
    friend class GameplayHudRenderer;
    friend class GameplayPartyOverlayRenderer;
    friend class GameplayPartyOverlayInputController;
    friend class HudUiService;
    friend class OutdoorBillboardRenderer;
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
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

    struct AnimatedWaterTerrainTileState
    {
        OutdoorTerrainAtlasRegion region;
        std::vector<uint8_t> basePixels;
        std::vector<uint8_t> overlayPixels;
        std::vector<uint8_t> animatedPixels;
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
        Chest,
        Spellbook,
        Rest,
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
    using SpellbookSchool = GameplayUiController::SpellbookSchool;
    using HouseShopMode = GameplayUiController::HouseShopMode;
    using InventoryNestedOverlayMode = GameplayUiController::InventoryNestedOverlayMode;
    using HouseBankInputMode = GameplayUiController::HouseBankInputMode;
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
        float hitX = 0.0f;
        float hitY = 0.0f;
        float hitZ = 0.0f;
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

    struct SpellbookPointerTarget
    {
        SpellbookPointerTargetType type = SpellbookPointerTargetType::None;
        SpellbookSchool school = SpellbookSchool::Fire;
        uint32_t spellId = 0;

        bool operator==(const SpellbookPointerTarget &other) const = default;
    };

    using SpellbookState = GameplayUiController::SpellbookState;
    using RestScreenState = GameplayUiController::RestScreenState;
    using RestMode = GameplayUiController::RestMode;
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
    void renderRestOverlay(int width, int height) const;
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
    bool tryBeginQuickSpellCast();
    bool tryCastSpellFromMember(size_t casterMemberIndex, uint32_t spellId, const std::string &spellName);
    bool activeMemberKnowsSpell(uint32_t spellId) const;
    bool activeMemberHasSpellbookSchool(SpellbookSchool school) const;
    void updateReadableScrollOverlayForHeldItem(size_t memberIndex, const CharacterPointerTarget &pointerTarget, bool isLeftMousePressed);
    void triggerPortraitEventFxWithoutSpeech(size_t memberIndex, PortraitFxEventKind kind);
    bool tryCastSpellRequest(const PartySpellCastRequest &request, const std::string &spellName);
    void openSpellbook();
    void closeSpellbook(const std::string &statusText = "");
    void openRestScreen();
    void closeRestScreen();
    void openJournal();
    void closeJournal();
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
    std::optional<StrTable> m_localStrTable;
    std::optional<EvtProgram> m_localEvtProgram;
    std::optional<EvtProgram> m_globalEvtProgram;
    const ObjectTable *m_pObjectTable;
    const SpellTable *m_pSpellTable;
    const JournalQuestTable *m_pJournalQuestTable;
    const JournalHistoryTable *m_pJournalHistoryTable;
    const JournalAutonoteTable *m_pJournalAutonoteTable;
    GameAudioSystem *m_pGameAudioSystem;
    OutdoorSceneRuntime *m_pOutdoorSceneRuntime;
    OutdoorWorldRuntime *m_pOutdoorWorldRuntime;
    bgfx::VertexBufferHandle m_vertexBufferHandle;
    bgfx::IndexBufferHandle m_indexBufferHandle;
    bgfx::DynamicVertexBufferHandle m_skyVertexBufferHandle;
    bgfx::DynamicVertexBufferHandle m_texturedTerrainVertexBufferHandle;
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
    std::unordered_map<std::string, size_t> m_decorationBitmapTextureIndexByName;
    std::vector<SkyTextureHandle> m_skyTextureHandles;
    std::unordered_map<std::string, size_t> m_skyTextureIndexByName;
    std::vector<TexturedTerrainVertex> m_cachedSkyVertices;
    std::string m_cachedSkyTextureName;
    float m_lastSkyUpdateElapsedTime = -1.0f;
    std::vector<TexturedTerrainVertex> m_baseTexturedTerrainVertices;
    std::vector<TexturedTerrainVertex> m_animatedTexturedTerrainVertices;
    std::vector<AnimatedWaterTerrainTileState> m_animatedWaterTerrainTiles;
    int m_lastWaterTerrainScrollX = -1;
    int m_lastWaterTerrainScrollY = -1;
    SpriteLoadCache m_spriteLoadCache;
    uint32_t m_lastPortraitAnimationUpdateTicks = 0;
    std::vector<uint16_t> m_pendingSpriteFrameWarmups;
    std::vector<bool> m_queuedSpriteFrameWarmups;
    size_t m_nextPendingSpriteFrameWarmupIndex;
    size_t m_runtimeActorBillboardTexturesQueuedCount;
    std::vector<std::vector<size_t>> m_decorationBillboardGridCells;
    std::vector<InteractiveDecorationBinding> m_interactiveDecorationBindings;
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
    bool m_keyboardUseLatch;
    bool m_activateInspectLatch;
    bool m_inspectMouseActivateLatch;
    bool m_attackInspectLatch;
    bool m_toggleRunningLatch;
    bool m_toggleFlyingLatch;
    bool m_toggleWaterWalkLatch;
    bool m_toggleFeatherFallLatch;
    bool m_quickSpellCastLatch;
    bool m_spellbookToggleLatch;
    bool m_spellbookClickLatch;
    bool m_pendingSpellTargetClickLatch;
    bool m_restToggleLatch;
    bool m_restClickLatch;
    bool m_booksButtonClickLatch;
    bool m_journalToggleLatch;
    bool m_journalClickLatch;
    bool m_inventoryScreenToggleLatch;
    bool m_adventurersInnToggleLatch;
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
    RestScreenState &m_restScreen;
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
    SpellbookPointerTarget m_spellbookPressedTarget;
    RestPointerTarget m_restPressedTarget;
    bool m_booksButtonPressed = false;
    JournalPointerTarget m_journalPressedTarget;
    bool m_journalMapKeyZoomLatch = false;
    uint64_t m_lastSpellbookSpellClickTicks;
    uint32_t m_lastSpellbookClickedSpellId;
    uint64_t m_lastSpellFailSoundTicks;
    PendingSpellCastState m_pendingSpellCast;
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
    InspectHit m_pressedInspectHit;
};
}
