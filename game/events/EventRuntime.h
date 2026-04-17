#pragma once

#include "game/events/EvtEnums.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/maps/MapDeltaData.h"
#include "game/party/Party.h"
#include "game/tables/PortraitFxEventTable.h"

#include <array>
#include <cstdint>
#include <optional>
#include <memory>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
class ISceneEventContext;
struct LuaSessionCache;

enum class DialogueContextKind
{
    None,
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
};

enum class DialogueOfferKind : uint32_t
{
    None = 0,
    RosterJoin,
    MasteryTeacher,
};

enum class MechanismAction
{
    Trigger = 0,
    Open = 1,
    Close = 2,
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
    struct PendingDialogueContext
    {
        DialogueContextKind kind = DialogueContextKind::None;
        uint32_t sourceId = 0;
        uint32_t hostHouseId = 0;
        uint32_t newsId = 0;
        std::optional<std::string> titleOverride;
    };

    struct PendingMapMove
    {
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        std::optional<std::string> mapName;
        std::optional<int32_t> directionDegrees;
        bool useMapStartPosition = false;
    };

    struct PendingMovie
    {
        std::string movieName;
        bool restoreAfterPlayback = false;
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
        uint32_t textId = 0;
        std::optional<std::string> text;
    };

    struct PendingSound
    {
        uint32_t soundId = 0;
        int32_t x = 0;
        int32_t y = 0;
        bool positional = false;
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
    };

    struct DialogueRuntimeState
    {
        uint32_t hostHouseId = 0;
        std::vector<DialogueMenuId> menuStack;
        std::optional<DialogueOfferState> currentOffer;
        std::array<uint8_t, 4> templeDonationCounters = {};
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

    std::unordered_map<uint32_t, int32_t> variables;
    std::unordered_map<uint32_t, int32_t> historyEventTimes;
    std::array<uint8_t, 75> mapVars = {};
    std::unordered_map<uint32_t, uint32_t> facetSetMasks;
    std::unordered_map<uint32_t, uint32_t> facetClearMasks;
    uint64_t outdoorSurfaceRevision = 0;
    std::unordered_map<uint32_t, RuntimeMechanismState> mechanisms;
    std::unordered_map<uint32_t, std::string> textureOverrides;
    std::unordered_map<uint32_t, SpriteOverride> spriteOverrides;
    std::unordered_map<uint32_t, bool> indoorLightsEnabled;
    std::optional<bool> snowEnabled;
    std::optional<bool> rainEnabled;
    std::unordered_map<uint32_t, uint32_t> actorSetMasks;
    std::unordered_map<uint32_t, uint32_t> actorClearMasks;
    std::unordered_map<uint32_t, uint32_t> actorGroupSetMasks;
    std::unordered_map<uint32_t, uint32_t> actorGroupClearMasks;
    std::unordered_map<uint32_t, uint32_t> actorIdGroupOverrides;
    std::unordered_map<uint32_t, uint32_t> actorGroupOverrides;
    std::unordered_map<uint32_t, uint32_t> actorGroupAllyOverrides;
    std::unordered_map<uint32_t, uint32_t> chestSetMasks;
    std::unordered_map<uint32_t, uint32_t> chestClearMasks;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> npcTopicOverrides;
    std::unordered_map<uint32_t, uint32_t> npcGroupNews;
    std::unordered_map<uint32_t, uint32_t> npcGreetingOverrides;
    std::unordered_map<uint32_t, uint32_t> npcGreetingDisplayCounts;
    std::unordered_map<uint32_t, uint32_t> npcHouseOverrides;
    std::unordered_map<uint32_t, uint32_t> npcItemOverrides;
    std::unordered_map<uint32_t, uint32_t> actorItemOverrides;
    std::unordered_set<uint32_t> unavailableNpcIds;
    DialogueRuntimeState dialogueState;
    std::array<uint8_t, 125> decorVars = {};
    std::optional<ActiveDecorationContext> activeDecorationContext;
    std::vector<std::string> messages;
    std::vector<std::string> statusMessages;
    std::vector<uint32_t> openedChestIds;
    std::vector<InventoryItem> grantedItems;
    std::vector<uint32_t> grantedItemIds;
    std::vector<uint32_t> removedItemIds;
    std::vector<uint32_t> grantedAwardIds;
    std::vector<uint32_t> removedAwardIds;
    std::vector<PortraitFxRequest> portraitFxRequests;
    std::vector<SpellFxRequest> spellFxRequests;
    std::optional<PendingDialogueContext> pendingDialogueContext;
    std::optional<PendingMapMove> pendingMapMove;
    std::optional<PendingMovie> pendingMovie;
    std::optional<PendingInputPrompt> pendingInputPrompt;
    std::optional<PendingArcomageGame> pendingArcomageGame;
    std::vector<PendingSound> pendingSounds;
    std::vector<uint32_t> lastAffectedMechanismIds;
    std::optional<std::string> lastActivationResult;
    size_t localOnLoadEventsExecuted = 0;
    size_t globalOnLoadEventsExecuted = 0;
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

class EventRuntime
{
public:
    EventRuntime();
    ~EventRuntime();

    EventRuntime(const EventRuntime &) = delete;
    EventRuntime &operator=(const EventRuntime &) = delete;

    EventRuntime(EventRuntime &&other) noexcept;
    EventRuntime &operator=(EventRuntime &&other) noexcept;

    static float calculateMechanismDistance(const MapDeltaDoor &door, const RuntimeMechanismState &runtimeMechanism);
    bool buildOnLoadState(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        const std::optional<MapDeltaData> &mapDeltaData,
        EventRuntimeState &runtimeState
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
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool canShowTopic(
        const std::optional<ScriptedEventProgram> &globalProgram,
        uint16_t topicId,
        const EventRuntimeState &runtimeState,
        const Party *pParty,
        const ISceneEventContext *pSceneEventContext = nullptr
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
        const std::optional<size_t> &memberIndex = std::nullopt
    );
    static void setVariableValue(
        EventRuntimeState &runtimeState,
        const VariableRef &variable,
        int32_t value,
        Party *pParty,
        const std::vector<size_t> &targetMemberIndices
    );
    static void addVariableValue(
        EventRuntimeState &runtimeState,
        const VariableRef &variable,
        int32_t value,
        Party *pParty,
        const std::vector<size_t> &targetMemberIndices
    );
    static void subtractVariableValue(
        EventRuntimeState &runtimeState,
        const VariableRef &variable,
        int32_t value,
        Party *pParty,
        const std::vector<size_t> &targetMemberIndices
    );
    static void applyMechanismAction(RuntimeMechanismState &runtimeMechanism, MechanismAction action);
    static int32_t getInventoryItemCount(
        const EventRuntimeState &runtimeState,
        const Party *pParty,
        uint32_t objectDescriptionId,
        const std::optional<size_t> &memberIndex = std::nullopt
    );
    mutable std::unique_ptr<LuaSessionCache> m_luaSessionCache;
    mutable const ScriptedEventProgram *m_pCachedLocalProgram = nullptr;
    mutable const ScriptedEventProgram *m_pCachedGlobalProgram = nullptr;
};
}
