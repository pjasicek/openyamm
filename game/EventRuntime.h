#pragma once

#include "game/EventIr.h"
#include "game/MapDeltaData.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class Party;

enum class DialogueContextKind
{
    None,
    HouseService,
    NpcTalk,
    NpcNews,
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
        uint32_t newsId = 0;
        std::optional<std::string> titleOverride;
    };

    struct PendingMapMove
    {
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        std::optional<std::string> mapName;
    };

    struct PendingRosterJoinInvite
    {
        uint32_t npcId = 0;
        uint32_t rosterId = 0;
        uint32_t inviteTextId = 0;
        uint32_t partyFullTextId = 0;
    };

    struct PendingMasteryTeacherOffer
    {
        uint32_t npcId = 0;
        uint32_t topicId = 0;
    };

    std::unordered_map<uint32_t, int32_t> variables;
    std::unordered_map<uint32_t, uint32_t> facetSetMasks;
    std::unordered_map<uint32_t, uint32_t> facetClearMasks;
    std::unordered_map<uint32_t, RuntimeMechanismState> mechanisms;
    std::unordered_map<uint32_t, std::string> textureOverrides;
    std::unordered_map<uint32_t, bool> indoorLightsEnabled;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> npcTopicOverrides;
    std::unordered_map<uint32_t, uint32_t> npcGroupNews;
    std::unordered_map<uint32_t, uint32_t> npcGreetingDisplayCounts;
    std::unordered_map<uint32_t, uint32_t> npcHouseOverrides;
    std::unordered_set<uint32_t> unavailableNpcIds;
    std::vector<std::string> messages;
    std::vector<uint32_t> openedChestIds;
    std::vector<uint32_t> grantedItemIds;
    std::vector<uint32_t> removedItemIds;
    std::optional<PendingDialogueContext> pendingDialogueContext;
    std::optional<PendingMapMove> pendingMapMove;
    std::optional<PendingRosterJoinInvite> pendingRosterJoinInvite;
    std::optional<PendingMasteryTeacherOffer> pendingMasteryTeacherOffer;
    std::vector<uint32_t> lastAffectedMechanismIds;
    std::optional<std::string> lastActivationResult;
    size_t localOnLoadEventsExecuted = 0;
    size_t globalOnLoadEventsExecuted = 0;
};

class EventRuntime
{
public:
    static float calculateMechanismDistance(const MapDeltaDoor &door, const RuntimeMechanismState &runtimeMechanism);

    bool buildOnLoadState(
        const std::optional<EventIrProgram> &localProgram,
        const std::optional<EventIrProgram> &globalProgram,
        const std::optional<MapDeltaData> &mapDeltaData,
        EventRuntimeState &runtimeState
    ) const;
    bool executeEventById(
        const std::optional<EventIrProgram> &localProgram,
        const std::optional<EventIrProgram> &globalProgram,
        uint16_t eventId,
        EventRuntimeState &runtimeState,
        const Party *pParty = nullptr
    ) const;
    bool canShowTopic(
        const std::optional<EventIrProgram> &globalProgram,
        uint16_t topicId,
        const EventRuntimeState &runtimeState,
        const Party *pParty
    ) const;
    void advanceMechanisms(
        const std::optional<MapDeltaData> &mapDeltaData,
        float deltaMilliseconds,
        EventRuntimeState &runtimeState
    ) const;

private:
    enum class VariableKind
    {
        Generic,
        QBits,
        BoolFlag,
        Inventory,
        Awards,
        Players,
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
        const Party *pParty
    );
    static void setVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value);
    static void addVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value);
    static void subtractVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value);
    static void executeProgramOnLoad(const EventIrProgram &program, EventRuntimeState &runtimeState, size_t &executedCount);
    static const EventIrEvent *findEventById(const EventIrProgram &program, uint16_t eventId);
    static void executeTimerEvents(const EventIrProgram &program, EventRuntimeState &runtimeState);
    static void applyMechanismAction(RuntimeMechanismState &runtimeMechanism, MechanismAction action);
    static int32_t getInventoryItemCount(
        const EventRuntimeState &runtimeState,
        const Party *pParty,
        uint32_t objectDescriptionId
    );
    static bool evaluateCompare(
        const EventRuntimeState &runtimeState,
        const EventIrInstruction &instruction,
        const Party *pParty
    );
    static bool evaluateCanShowTopic(const EventIrEvent &event, const EventRuntimeState &runtimeState, const Party *pParty);
    static bool executeEvent(const EventIrEvent &event, EventRuntimeState &runtimeState, const Party *pParty);
};
}
