#pragma once

#include "game/audio/SoundRef.h"
#include "game/events/EvtEnums.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/gameplay/NpcFollowerTypes.h"
#include "game/maps/MapDeltaData.h"
#include "game/party/Party.h"
#include "game/tables/PortraitFxEventTable.h"

#include <array>
#include <cstdint>
#include <limits>
#include <optional>
#include <memory>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
class ISceneEventContext;
class HouseTable;
class NpcDialogTable;
struct LuaSessionCache;

enum class DialogueContextKind
{
    None,
    MapEvent,
    HouseService,
    NpcTalk,
    NpcNews,
    MapTransition,
};

enum class DialogueMenuId : uint32_t
{
    None = 0,
    LearnSkills,
    ShopEquipment,
    TavernArcomage,
    HouseServiceRoot,
};

enum class DialogueOfferKind : uint32_t
{
    None = 0,
    RosterJoin,
    MasteryTeacher,
    GuildMembership,
    NpcHire,
};

enum class MechanismAction
{
    Trigger = 0,
    Open = 1,
    Close = 2,
};

enum class EventRuntimeHookKind : uint8_t
{
    NpcEnter = 0,
    NpcExit,
    HouseTopicFilter,
    HouseTopicClick,
    RestFoodCost,
    GameplayAction,
    MapRefill,
    MapTransition,
    MonsterKilled,
    MonsterDamage,
    ChestOpen,
    InventoryOpen,
};

struct RuntimeMechanismState
{
    uint16_t state = 0;
    float timeSinceTriggeredMs = 0.0f;
    float currentDistance = 0.0f;
    bool isMoving = false;
};

struct EventRuntimeState
{
    struct OutdoorModelMechanismDefinition
    {
        uint32_t mechanismId = 0;
        std::string modelName;
        size_t bmodelIndex = static_cast<size_t>(-1);
        int32_t dx = 0;
        int32_t dy = 0;
        int32_t dz = 0;
        uint32_t moveTimeMs = 0;
        bool closed = true;
        bool moveParty = false;
    };

    struct PendingMapMove
    {
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        std::optional<std::string> mapName;
        std::optional<int32_t> directionDegrees;
        bool useMapStartPosition = false;
        bool useFullscreenLoading = false;
        std::string traceSourceKind;
        uint32_t traceSourceId = 0;
        uint32_t traceActionId = 0;
        uint32_t traceEventId = 0;
        std::string traceDestinationName;
    };

    struct MapNoteSourcePoint
    {
        int32_t x = 0;
        int32_t y = 0;
    };

    struct PendingDialogueContext
    {
        DialogueContextKind kind = DialogueContextKind::None;
        uint32_t sourceId = 0;
        std::optional<uint32_t> sourceActorIndex;
        uint32_t hostHouseId = 0;
        uint32_t newsId = 0;
        uint32_t participantPictureId = 0;
        std::optional<std::string> titleOverride;
        std::optional<PendingMapMove> transitionMapMove;
        uint32_t transitionTextId = 0;
        uint32_t transitionImageId = 0;
        std::optional<MapNoteSourcePoint> mapNoteSourcePoint;
    };

    struct PendingMovie
    {
        std::string movieName;
        bool restoreAfterPlayback = false;
    };

    struct PendingWinGame
    {
        uint32_t houseId = 0;
    };

    struct PendingInputPrompt
    {
        enum class Kind : uint8_t
        {
            InputString = 0,
            PressAnyKey,
        };

        Kind kind = Kind::InputString;
        uint16_t eventId = 0;
        uint8_t continueStep = 0;
        uint8_t correctStep = 0;
        uint32_t textId = 0;
        std::vector<uint32_t> answerTextIds;
        std::vector<std::string> answers;
        std::vector<uint8_t> answerContinueSteps;
        std::optional<std::string> text;
    };

    struct PendingSound
    {
        enum class Kind
        {
            PlayOneShot,
            PlayLoopingKeyed,
            StopKeyed,
        };

        Kind kind = Kind::PlayOneShot;
        SoundScope soundScope = SoundScope::Engine;
        uint32_t soundId = 0;
        uint64_t key = 0;
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        bool positional = false;
        bool hasExplicitZ = false;
    };

    struct SpriteOverride
    {
        bool hidden = false;
        std::optional<std::string> textureName;
    };

    struct PendingArcomageGame
    {
        uint32_t houseId = 0;
    };

    struct DialogueOfferState
    {
        DialogueOfferKind kind = DialogueOfferKind::None;
        uint32_t npcId = 0;
        uint32_t topicId = 0;
        uint32_t messageTextId = 0;
        uint32_t rosterId = 0;
        uint32_t partyFullTextId = 0;
        std::optional<uint32_t> sourceActorIndex;
    };

    struct DialogueRuntimeState
    {
        uint32_t hostHouseId = 0;
        std::vector<DialogueMenuId> menuStack;
        std::optional<DialogueOfferState> currentOffer;
        std::array<uint8_t, 4> templeDonationCounters = {};
    };

    using HiredNpcFollower = ::OpenYAMM::Game::HiredNpcFollower;

    struct GeneratedMercenaryRecruit
    {
        uint32_t npcId = 0;
        uint32_t rosterId = 0;
        uint32_t houseId = 0;
        uint32_t portraitPictureId = 0;
        uint32_t npcPictureId = 0;
        Character character = {};
    };

    struct ActiveDecorationContext
    {
        uint8_t decorVarIndex = 0;
        uint16_t baseEventId = 0;
        uint16_t currentEventId = 0;
        uint8_t eventCount = 0;
        bool hideWhenCleared = false;
    };

    struct PortraitFxRequest
    {
        PortraitFxEventKind kind = PortraitFxEventKind::None;
        std::vector<size_t> memberIndices;
    };

    struct SpellFxRequest
    {
        uint32_t spellId = 0;
        std::vector<size_t> memberIndices;
    };

    struct RuntimeMapNote
    {
        uint32_t id = 0;
        int32_t x = 0;
        int32_t y = 0;
        std::string mapFileName;
        std::string text;
        bool active = false;
    };

    struct SavedLocation
    {
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        uint32_t continentId = 0;
        std::string mapName;
    };

    struct TransportRouteOverride
    {
        uint32_t houseId = 0;
        uint32_t routeIndex = 0;
        std::string destinationName;
        std::string mapFileName;
        std::array<bool, 7> daysAvailable = {true, true, true, true, true, true, true};
        uint32_t travelDays = 0;
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        int32_t directionDegrees = 0;
        uint32_t requiredQBit = 0;
        bool useMapStartPosition = false;
    };

    struct ChestItemRequest
    {
        uint32_t itemId = 0;
        uint8_t gridX = 0;
        uint8_t gridY = 0;
    };

    struct OpenedChestRequest
    {
        uint32_t chestId = 0;
        bool openedByTelekinesis = false;
    };

    struct PressurePlateTrigger
    {
        std::string world;
        uint32_t eventId = 0;
        size_t bmodelIndex = std::numeric_limits<size_t>::max();
        size_t faceIndex = std::numeric_limits<size_t>::max();
        uint32_t attributes = 0;
    };

    struct DialogueCanceled
    {
        std::string kind;
        uint32_t sourceId = 0;
        uint32_t activeSourceId = 0;
        bool houseDialog = false;
        size_t actionCount = 0;
    };

    struct MapTransitionTrace
    {
        std::string sourceKind;
        uint32_t sourceId = 0;
        uint32_t actionId = 0;
        uint32_t eventId = 0;
        std::optional<uint32_t> routeIndex;
        bool confirmationRequired = false;
        std::string destinationMap;
        std::string destinationName;
        uint32_t travelDays = 0;
        bool useStartPosition = false;
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        std::optional<int32_t> directionDegrees;
    };

    struct ChestOpenedTrace
    {
        std::string sceneKind;
        std::string map;
        uint32_t chestId = 0;
        size_t itemCount = 0;
        size_t hiddenItemCount = 0;
    };

    struct ActorDialogStartedTrace
    {
        std::string kind;
        std::string map;
        uint32_t npcId = 0;
        uint32_t sourceId = 0;
        uint32_t hostHouseId = 0;
        std::optional<uint32_t> actorIndex;
    };

    struct ActiveHookContext
    {
        EventRuntimeHookKind kind = EventRuntimeHookKind::NpcEnter;
        uint32_t npcId = 0;
        std::optional<uint32_t> actorIndex;
        uint32_t monsterId = 0;
        int32_t damage = 0;
        uint32_t damageType = 0;
        uint32_t houseId = 0;
        uint32_t houseServiceType = 0;
        uint32_t menuId = 0;
        uint32_t houseActionId = 0;
        uint32_t gameplayActionId = 0;
        uint32_t boundaryEdge = 0;
        uint32_t chestId = 0;
        uint32_t heldItemId = 0;
        uint32_t inventorySource = 0;
        uint32_t inventorySourceIndex = 0;
        uint32_t inventoryPage = 0;
        std::string destinationMapName;
        int32_t baseRestFoodCost = 0;
        std::optional<int32_t> restFoodCostOverride;
        std::optional<int32_t> damageOverride;
        bool blocked = false;
        std::optional<std::string> statusText;
        std::vector<uint32_t> houseTopicActionIds;
    };

    std::string mapFileName;
    std::unordered_map<uint32_t, int32_t> variables;
    std::unordered_map<std::string, int32_t> namedMapVars;
    std::unordered_map<std::string, int32_t> namedGlobalVars;
    std::unordered_map<uint32_t, RuntimeMapNote> runtimeMapNotes;
    std::unordered_map<std::string, SavedLocation> savedLocations;
    std::unordered_map<uint64_t, TransportRouteOverride> transportRouteOverrides;
    uint32_t eventRandomState = 0;
    std::optional<MapNoteSourcePoint> activeEventMapNoteSourcePoint;
    uint32_t activeHistoryContinentId = 1;
    std::unordered_map<uint32_t, int32_t> historyEventTimes;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, int32_t>> historyEventTimesByContinent;
    std::array<uint8_t, 75> mapVars = {};
    int32_t currentLocationReputation = 0;
    std::unordered_map<uint32_t, uint32_t> facetSetMasks;
    std::unordered_map<uint32_t, uint32_t> facetClearMasks;
    uint64_t outdoorSurfaceRevision = 0;
    mutable uint64_t facetInvisibleOverrideCacheRevision = std::numeric_limits<uint64_t>::max();
    mutable size_t facetInvisibleOverrideCacheSetSize = 0;
    mutable size_t facetInvisibleOverrideCacheClearSize = 0;
    mutable std::vector<uint8_t> facetInvisibleOverrideCache;
    std::unordered_map<uint32_t, RuntimeMechanismState> mechanisms;
    std::unordered_map<uint32_t, OutdoorModelMechanismDefinition> outdoorModelMechanisms;
    std::unordered_map<uint32_t, std::string> textureOverrides;
    std::unordered_map<uint32_t, std::string> outdoorModelFacetTextureOverrides;
    std::unordered_map<uint32_t, SpriteOverride> spriteOverrides;
    std::unordered_map<uint32_t, bool> indoorLightsEnabled;
    std::optional<bool> snowEnabled;
    std::optional<bool> rainEnabled;
    std::optional<std::string> outdoorSkyTextureOverride;
    std::optional<int32_t> outdoorFogWeakDistanceOverride;
    std::optional<int32_t> outdoorFogStrongDistanceOverride;
    std::unordered_map<uint32_t, uint32_t> actorSetMasks;
    std::unordered_map<uint32_t, uint32_t> actorClearMasks;
    std::unordered_map<uint32_t, uint32_t> actorGroupSetMasks;
    std::unordered_map<uint32_t, uint32_t> actorGroupClearMasks;
    std::unordered_map<uint32_t, bool> actorHostilityRequests;
    std::unordered_map<uint32_t, bool> actorGroupHostilityRequests;
    std::unordered_map<uint32_t, uint32_t> actorIdGroupOverrides;
    std::unordered_map<uint32_t, uint32_t> actorGroupOverrides;
    std::unordered_map<uint32_t, uint32_t> actorGroupAllyOverrides;
    std::unordered_map<uint32_t, uint32_t> chestSetMasks;
    std::unordered_map<uint32_t, uint32_t> chestClearMasks;
    std::optional<PressurePlateTrigger> lastPressurePlateTrigger;
    std::optional<DialogueCanceled> lastDialogueCanceled;
    std::optional<MapTransitionTrace> lastMapTransitionRequested;
    std::optional<MapTransitionTrace> lastMapTransitionConfirmed;
    std::optional<MapTransitionTrace> lastMapTransitionCanceled;
    std::optional<ChestOpenedTrace> lastChestOpened;
    std::optional<ActorDialogStartedTrace> lastActorDialogStarted;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> npcTopicOverrides;
    std::unordered_map<uint32_t, uint32_t> npcGroupNews;
    std::unordered_map<uint32_t, uint32_t> npcGreetingOverrides;
    std::unordered_map<uint32_t, uint32_t> npcGreetingDisplayCounts;
    std::unordered_map<uint32_t, uint32_t> npcHouseOverrides;
    std::unordered_map<uint32_t, std::string> npcNameOverrides;
    std::unordered_map<uint32_t, uint32_t> npcPictureOverrides;
    std::unordered_map<uint32_t, uint32_t> npcProfessionOverrides;
    std::unordered_map<std::string, uint32_t> generatedNpcIdsByActorKey;
    std::unordered_map<uint32_t, GeneratedMercenaryRecruit> generatedMercenaryRecruitsByNpcId;
    std::unordered_map<uint32_t, uint32_t> npcItemOverrides;
    std::unordered_map<uint32_t, uint32_t> actorItemOverrides;
    std::unordered_map<uint32_t, std::vector<uint32_t>> actorExtraItemOverrides;
    std::unordered_map<uint32_t, int32_t> monsterRelationOverrides;
    std::unordered_map<uint32_t, std::vector<ChestItemRequest>> chestItemRequests;
    std::unordered_set<uint32_t> unavailableNpcIds;
    std::vector<HiredNpcFollower> hiredNpcFollowers;
    bool pendingDimensionDoorOverlay = false;
    DialogueRuntimeState dialogueState;
    std::array<uint8_t, 125> decorVars = {};
    std::optional<ActiveDecorationContext> activeDecorationContext;
    std::optional<ActiveHookContext> activeHookContext;
    std::vector<std::string> messages;
    std::vector<std::string> statusMessages;
    std::vector<uint32_t> openedChestIds;
    std::vector<OpenedChestRequest> openedChestRequests;
    bool activeEventOpenedByTelekinesis = false;
    uint32_t activeEventSpellId = 0;
    std::vector<InventoryItem> grantedItems;
    std::vector<uint32_t> grantedItemIds;
    bool clearHeldItemRequest = false;
    std::vector<uint32_t> removedItemIds;
    std::vector<uint32_t> grantedAwardIds;
    std::vector<uint32_t> removedAwardIds;
    std::vector<PortraitFxRequest> portraitFxRequests;
    std::vector<SpellFxRequest> spellFxRequests;
    std::optional<PendingDialogueContext> pendingDialogueContext;
    std::optional<PendingMapMove> pendingMapMove;
    std::optional<PendingMovie> pendingMovie;
    std::optional<PendingWinGame> pendingWinGame;
    bool pendingReturnToMainMenu = false;
    std::optional<PendingInputPrompt> pendingInputPrompt;
    std::optional<PendingArcomageGame> pendingArcomageGame;
    std::vector<PendingSound> pendingSounds;
    std::vector<uint32_t> lastAffectedMechanismIds;
    std::optional<std::string> lastActivationResult;
    size_t localOnLoadEventsExecuted = 0;
    size_t globalOnLoadEventsExecuted = 0;
    int32_t processedMapRespawnCount = 0;

    bool hasFacetInvisibleOverride(uint32_t faceId) const;
};

struct EventRuntimeBindingReport
{
    size_t localEventCount = 0;
    size_t localHandlerCount = 0;
    size_t globalEventCount = 0;
    size_t globalHandlerCount = 0;
    size_t canShowTopicEventCount = 0;
    size_t canShowTopicHandlerCount = 0;
    std::vector<uint16_t> missingLocalHandlerEventIds;
    std::vector<uint16_t> missingGlobalHandlerEventIds;
    std::vector<uint16_t> missingCanShowTopicEventIds;
    std::optional<std::string> errorMessage;
};

void clearTransientEventRuntimeState(EventRuntimeState &runtimeState);
std::vector<uint32_t> consumeOpenedChestIds(EventRuntimeState &runtimeState);
std::vector<EventRuntimeState::OpenedChestRequest> consumeOpenedChestRequests(EventRuntimeState &runtimeState);
uint32_t normalizedHistoryContinentId(uint32_t continentId);
void setActiveHistoryContinent(EventRuntimeState &runtimeState, uint32_t continentId);
const std::unordered_map<uint32_t, int32_t> &historyEventTimesForActiveContinent(
    const EventRuntimeState &runtimeState);

class EventRuntime
{
public:
    EventRuntime(const HouseTable *pHouseTable = nullptr, const NpcDialogTable *pNpcDialogTable = nullptr);
    ~EventRuntime();

    EventRuntime(const EventRuntime &) = delete;
    EventRuntime &operator=(const EventRuntime &) = delete;

    EventRuntime(EventRuntime &&other) noexcept;
    EventRuntime &operator=(EventRuntime &&other) noexcept;

    void bindHouseTable(const HouseTable *pHouseTable);
    const HouseTable *houseTable() const;
    void bindNpcDialogTable(const NpcDialogTable *pNpcDialogTable);
    const NpcDialogTable *npcDialogTable() const;

    static uint32_t outdoorModelFacetTextureOverrideKey(uint32_t modelIndex, uint32_t faceIndex);
    static uint32_t monsterRelationOverrideKey(uint32_t leftMonsterId, uint32_t rightMonsterId);
    static uint64_t transportRouteOverrideKey(uint32_t houseId, uint32_t routeIndex);

    static float calculateMechanismDistance(const MapDeltaDoor &door, const RuntimeMechanismState &runtimeMechanism);
    void initializeMapRuntimeState(
        const std::optional<MapDeltaData> &mapDeltaData,
        EventRuntimeState &runtimeState
    ) const;
    bool buildOnLoadState(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        const std::optional<MapDeltaData> &mapDeltaData,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool executeOnLoadEvents(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool executeOnLeaveEvents(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool validateProgramBindings(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        EventRuntimeBindingReport &report
    ) const;
    bool executeEventById(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        uint16_t eventId,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr,
        std::optional<uint8_t> continueStep = std::nullopt,
        bool allowGlobalFallback = true
    ) const;
    bool executeNpcTopicEventById(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        uint16_t eventId,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr,
        std::optional<uint8_t> continueStep = std::nullopt
    ) const;
    bool canShowTopic(
        const std::optional<ScriptedEventProgram> &globalProgram,
        uint16_t topicId,
        const EventRuntimeState &runtimeState,
        const Party *pParty,
        const ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool executeHooks(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        EventRuntimeHookKind kind,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool executeMapRefillHooks(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        const std::optional<MapDeltaData> &mapDeltaData,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    void advanceMechanisms(
        const std::optional<MapDeltaData> &mapDeltaData,
        float deltaMilliseconds,
        EventRuntimeState &runtimeState
    ) const;

    enum class VariableKind
    {
        Generic,
        PartyState,
        CharacterState,
        QBits,
        BoolFlag,
        AutoNote,
        History,
        Food,
        Inventory,
        Awards,
        Players,
        CircusPrises,
        ClassId,
        Experience,
        CurrentHealth,
        MaxHealth,
        CurrentSpellPoints,
        MaxSpellPoints,
        Hour,
        DayOfYear,
        DayOfWeek,
        Gold,
        GoldInBank,
        BaseLevel,
        LevelBonus,
        Sex,
        Race,
        Age,
        ArmorClass,
        ArmorClassBonus,
        BaseStat,
        ActualStat,
        StatMoreThanBase,
        StatBonus,
        BaseResistance,
        ResistanceBonus,
        Skill,
        Condition,
        MajorCondition,
        MapPersistent,
        DecorPersistent,
    };

    struct VariableRef
    {
        VariableKind kind = VariableKind::Generic;
        uint32_t rawId = 0;
        uint16_t tag = 0;
        uint32_t index = 0;
    };

    static VariableRef decodeVariable(uint32_t rawId);
    static int32_t getVariableValue(
        const EventRuntimeState &runtimeState,
        const VariableRef &variable,
        const Party *pParty,
        const std::optional<size_t> &memberIndex = std::nullopt,
        const ISceneEventContext *pSceneEventContext = nullptr
    );
    static void setVariableValue(
        EventRuntimeState &runtimeState,
        const VariableRef &variable,
        int32_t value,
        Party *pParty,
        const std::vector<size_t> &targetMemberIndices,
        const ISceneEventContext *pSceneEventContext = nullptr
    );
    static void addVariableValue(
        EventRuntimeState &runtimeState,
        const VariableRef &variable,
        int32_t value,
        Party *pParty,
        const std::vector<size_t> &targetMemberIndices,
        const ISceneEventContext *pSceneEventContext = nullptr
    );
    static void subtractVariableValue(
        EventRuntimeState &runtimeState,
        const VariableRef &variable,
        int32_t value,
        Party *pParty,
        const std::vector<size_t> &targetMemberIndices
    );
    static void applyMechanismAction(
        RuntimeMechanismState &runtimeMechanism,
        const MapDeltaDoor *pDoor,
        MechanismAction action);
    static int32_t getInventoryItemCount(
        const EventRuntimeState &runtimeState,
        const Party *pParty,
        uint32_t objectDescriptionId,
        const std::optional<size_t> &memberIndex = std::nullopt
    );
    mutable std::unique_ptr<LuaSessionCache> m_luaSessionCache;
    mutable const ScriptedEventProgram *m_pCachedLocalProgram = nullptr;
    mutable const ScriptedEventProgram *m_pCachedGlobalProgram = nullptr;
    mutable uint64_t m_cachedLocalProgramCacheId = 0;
    mutable uint64_t m_cachedGlobalProgramCacheId = 0;
    const HouseTable *m_pHouseTable = nullptr;
    const NpcDialogTable *m_pNpcDialogTable = nullptr;
};
}
