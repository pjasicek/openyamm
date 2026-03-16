#pragma once

#include "game/EventIr.h"
#include "game/MapDeltaData.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
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
    std::unordered_map<uint32_t, int32_t> variables;
    std::unordered_map<uint32_t, uint32_t> facetSetMasks;
    std::unordered_map<uint32_t, uint32_t> facetClearMasks;
    std::unordered_map<uint32_t, RuntimeMechanismState> mechanisms;
    std::unordered_map<uint32_t, std::string> textureOverrides;
    std::unordered_map<uint32_t, bool> indoorLightsEnabled;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, bool>> npcTopics;
    std::vector<std::string> messages;
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
        EventRuntimeState &runtimeState
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
    };

    struct VariableRef
    {
        VariableKind kind = VariableKind::Generic;
        uint32_t rawId = 0;
        uint16_t tag = 0;
        uint32_t index = 0;
    };

    static VariableRef decodeVariable(uint32_t rawId);
    static int32_t getVariableValue(const EventRuntimeState &runtimeState, const VariableRef &variable);
    static void setVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value);
    static void addVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value);
    static void subtractVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value);
    static void executeProgramOnLoad(const EventIrProgram &program, EventRuntimeState &runtimeState, size_t &executedCount);
    static const EventIrEvent *findEventById(const EventIrProgram &program, uint16_t eventId);
    static void executeTimerEvents(const EventIrProgram &program, EventRuntimeState &runtimeState);
    static void applyMechanismAction(RuntimeMechanismState &runtimeMechanism, MechanismAction action);
    static bool executeEvent(const EventIrEvent &event, EventRuntimeState &runtimeState);
};
}
