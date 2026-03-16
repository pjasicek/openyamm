#include "game/EventRuntime.h"

#include <iostream>
#include <algorithm>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
float mechanismDistanceForState(const MapDeltaDoor &door, uint16_t state, float timeSinceTriggeredMs)
{
    if (state == 0)
    {
        return 0.0f;
    }

    if (state == 2 || (door.attributes & 0x2) != 0)
    {
        return static_cast<float>(door.moveLength);
    }

    const float elapsedMilliseconds = static_cast<float>(timeSinceTriggeredMs);

    if (state == 3)
    {
        const float openDistance = elapsedMilliseconds * static_cast<float>(door.openSpeed) / 1000.0f;
        return std::max(0.0f, static_cast<float>(door.moveLength) - openDistance);
    }

    if (state == 1)
    {
        const float closeDistance = elapsedMilliseconds * static_cast<float>(door.closeSpeed) / 1000.0f;
        return std::min(closeDistance, static_cast<float>(door.moveLength));
    }

    return 0.0f;
}
}

EventRuntime::VariableRef EventRuntime::decodeVariable(uint32_t rawId)
{
    VariableRef variable = {};
    variable.rawId = rawId;
    variable.tag = static_cast<uint16_t>(rawId & 0xFFFF);
    variable.index = rawId >> 16;

    if (variable.tag == 0x0010)
    {
        variable.kind = VariableKind::QBits;
        variable.rawId = variable.index;
    }
    else if ((variable.tag >= 0x007d && variable.tag <= 0x0084) || variable.tag == 0x009a)
    {
        variable.kind = VariableKind::BoolFlag;
        variable.rawId = variable.tag;
    }
    else if (variable.tag == 0x0087 || variable.tag == 0x0088 || variable.tag == 0x0089)
    {
        variable.kind = VariableKind::Generic;
        variable.rawId = variable.tag;
    }

    return variable;
}

int32_t EventRuntime::getVariableValue(const EventRuntimeState &runtimeState, const VariableRef &variable)
{
    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = runtimeState.variables.find(variable.rawId);
        return iterator != runtimeState.variables.end() ? iterator->second : 0;
    }

    const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = runtimeState.variables.find(variable.rawId);
    return iterator != runtimeState.variables.end() ? iterator->second : 0;
}

void EventRuntime::setVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value)
{
    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        runtimeState.variables[variable.rawId] = value != 0 ? 1 : 0;
        return;
    }

    runtimeState.variables[variable.rawId] = value;
}

void EventRuntime::addVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value)
{
    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        runtimeState.variables[variable.rawId] = value != 0 ? 1 : 0;
        return;
    }

    runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable) + value;
}

void EventRuntime::subtractVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value)
{
    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        runtimeState.variables[variable.rawId] = 0;
        return;
    }

    runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable) - value;
}

bool EventRuntime::buildOnLoadState(
    const std::optional<EventIrProgram> &localProgram,
    const std::optional<EventIrProgram> &globalProgram,
    const std::optional<MapDeltaData> &mapDeltaData,
    EventRuntimeState &runtimeState
) const
{
    runtimeState = {};

    if (mapDeltaData)
    {
        for (const MapDeltaDoor &door : mapDeltaData->doors)
        {
            RuntimeMechanismState runtimeMechanism = {};
            runtimeMechanism.state = door.state;
            runtimeMechanism.timeSinceTriggeredMs = float(door.timeSinceTriggered);
            runtimeMechanism.currentDistance =
                mechanismDistanceForState(door, runtimeMechanism.state, runtimeMechanism.timeSinceTriggeredMs);
            runtimeMechanism.isMoving = door.state == 1 || door.state == 3;
            runtimeState.mechanisms[door.doorId] = runtimeMechanism;
        }

        for (size_t mapVarIndex = 0; mapVarIndex < mapDeltaData->eventVariables.mapVars.size(); ++mapVarIndex)
        {
            if (mapDeltaData->eventVariables.mapVars[mapVarIndex] == 0)
            {
                continue;
            }

            const uint32_t rawId = static_cast<uint32_t>(mapVarIndex) << 16 | 0x0011u;
            runtimeState.variables[rawId] = mapDeltaData->eventVariables.mapVars[mapVarIndex];
        }
    }

    if (globalProgram)
    {
        executeProgramOnLoad(*globalProgram, runtimeState, runtimeState.globalOnLoadEventsExecuted);
    }

    if (localProgram)
    {
        executeProgramOnLoad(*localProgram, runtimeState, runtimeState.localOnLoadEventsExecuted);
    }

    return true;
}

bool EventRuntime::executeEventById(
    const std::optional<EventIrProgram> &localProgram,
    const std::optional<EventIrProgram> &globalProgram,
    uint16_t eventId,
    EventRuntimeState &runtimeState
) const
{
    if (eventId == 0)
    {
        return false;
    }

    if (localProgram)
    {
        const EventIrEvent *pEvent = findEventById(*localProgram, eventId);

        if (pEvent != nullptr)
        {
            std::cout << "Executing local event " << eventId << '\n';
            const bool executed = executeEvent(*pEvent, runtimeState);
            executeTimerEvents(*localProgram, runtimeState);
            return executed;
        }
    }

    if (globalProgram)
    {
        const EventIrEvent *pEvent = findEventById(*globalProgram, eventId);

        if (pEvent != nullptr)
        {
            std::cout << "Executing global event " << eventId << '\n';
            const bool executed = executeEvent(*pEvent, runtimeState);
            executeTimerEvents(*globalProgram, runtimeState);
            return executed;
        }
    }

    return false;
}

void EventRuntime::advanceMechanisms(
    const std::optional<MapDeltaData> &mapDeltaData,
    float deltaMilliseconds,
    EventRuntimeState &runtimeState
) const
{
    if (!mapDeltaData || deltaMilliseconds == 0)
    {
        return;
    }

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::iterator iterator =
            runtimeState.mechanisms.find(door.doorId);

        if (iterator == runtimeState.mechanisms.end() || !iterator->second.isMoving)
        {
            continue;
        }

        RuntimeMechanismState &runtimeMechanism = iterator->second;
        runtimeMechanism.timeSinceTriggeredMs += deltaMilliseconds;
        runtimeMechanism.currentDistance =
            calculateMechanismDistance(door, runtimeMechanism);

        if (runtimeMechanism.state == 3)
        {
            const float openedDistance = runtimeMechanism.timeSinceTriggeredMs * float(door.openSpeed) / 1000.0f;

            if (openedDistance >= float(door.moveLength))
            {
                runtimeMechanism.state = 0;
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = 0.0f;
                runtimeMechanism.isMoving = false;
            }
        }
        else if (runtimeMechanism.state == 1)
        {
            const float closedDistance = runtimeMechanism.timeSinceTriggeredMs * float(door.closeSpeed) / 1000.0f;

            if (closedDistance >= float(door.moveLength))
            {
                runtimeMechanism.state = 2;
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = static_cast<float>(door.moveLength);
                runtimeMechanism.isMoving = false;
            }
        }
        else
        {
            runtimeMechanism.isMoving = false;
        }
    }
}

void EventRuntime::executeProgramOnLoad(
    const EventIrProgram &program,
    EventRuntimeState &runtimeState,
    size_t &executedCount
)
{
    for (const EventIrEvent &event : program.getEvents())
    {
        bool hasOnLoadTrigger = false;

        for (const EventIrInstruction &instruction : event.instructions)
        {
            if (instruction.operation == EventIrOperation::TriggerOnLoadMap)
            {
                hasOnLoadTrigger = true;
                break;
            }
        }

        if (!hasOnLoadTrigger)
        {
            continue;
        }

        if (executeEvent(event, runtimeState))
        {
            ++executedCount;
        }
    }
}

const EventIrEvent *EventRuntime::findEventById(const EventIrProgram &program, uint16_t eventId)
{
    for (const EventIrEvent &event : program.getEvents())
    {
        if (event.eventId == eventId)
        {
            return &event;
        }
    }

    return nullptr;
}

void EventRuntime::executeTimerEvents(const EventIrProgram &program, EventRuntimeState &runtimeState)
{
    for (const EventIrEvent &event : program.getEvents())
    {
        bool hasTimerTrigger = false;

        for (const EventIrInstruction &instruction : event.instructions)
        {
            if (instruction.operation == EventIrOperation::TriggerOnTimer)
            {
                hasTimerTrigger = true;
                break;
            }
        }

        if (!hasTimerTrigger)
        {
            continue;
        }

        std::cout << "Executing timer event " << event.eventId << '\n';
        executeEvent(event, runtimeState);
    }
}

float EventRuntime::calculateMechanismDistance(
    const MapDeltaDoor &door,
    const RuntimeMechanismState &runtimeMechanism
)
{
    return mechanismDistanceForState(door, runtimeMechanism.state, runtimeMechanism.timeSinceTriggeredMs);
}

void EventRuntime::applyMechanismAction(
    RuntimeMechanismState &runtimeMechanism,
    MechanismAction action
)
{
    if (action == MechanismAction::Trigger)
    {
        if (runtimeMechanism.state == 1 || runtimeMechanism.state == 3)
        {
            return;
        }

        runtimeMechanism.timeSinceTriggeredMs = 0.0f;

        if (runtimeMechanism.state == 2)
        {
            runtimeMechanism.state = 3;
        }
        else
        {
            runtimeMechanism.state = 1;
        }

        runtimeMechanism.isMoving = true;
        return;
    }

    if (action == MechanismAction::Open)
    {
        if (runtimeMechanism.state == 0 || runtimeMechanism.state == 3)
        {
            return;
        }

        runtimeMechanism.timeSinceTriggeredMs = 0.0f;
        runtimeMechanism.state = 3;
        runtimeMechanism.isMoving = true;
        return;
    }

    if (action == MechanismAction::Close)
    {
        if (runtimeMechanism.state == 2 || runtimeMechanism.state == 1)
        {
            return;
        }

        runtimeMechanism.timeSinceTriggeredMs = 0.0f;
        runtimeMechanism.state = 1;
        runtimeMechanism.isMoving = true;
    }
}

bool EventRuntime::executeEvent(const EventIrEvent &event, EventRuntimeState &runtimeState)
{
    runtimeState.lastAffectedMechanismIds.clear();

    std::unordered_map<uint8_t, size_t> stepToInstructionIndex;

    for (size_t instructionIndex = 0; instructionIndex < event.instructions.size(); ++instructionIndex)
    {
        stepToInstructionIndex[event.instructions[instructionIndex].step] = instructionIndex;
    }

    size_t instructionIndex = 0;

    while (instructionIndex < event.instructions.size())
    {
        const EventIrInstruction &instruction = event.instructions[instructionIndex];

        switch (instruction.operation)
        {
            case EventIrOperation::Exit:
                return true;

            case EventIrOperation::TriggerMouseOver:
            case EventIrOperation::TriggerOnLoadMap:
            case EventIrOperation::TriggerOnLeaveMap:
            case EventIrOperation::TriggerOnTimer:
            case EventIrOperation::TriggerOnLongTimer:
            case EventIrOperation::TriggerOnDateTimer:
            case EventIrOperation::EnableDateTimer:
            case EventIrOperation::CompareCanShowTopic:
            case EventIrOperation::SetCanShowTopic:
            case EventIrOperation::EndCanShowTopic:
            case EventIrOperation::ForPartyMember:
            case EventIrOperation::CheckItemsCount:
            case EventIrOperation::RemoveItems:
            case EventIrOperation::CheckSkill:
            case EventIrOperation::SpeakInHouse:
            case EventIrOperation::SpeakNpc:
            case EventIrOperation::MoveToMap:
            case EventIrOperation::MoveNpc:
            case EventIrOperation::ChangeEvent:
            case EventIrOperation::RandomJump:
            case EventIrOperation::SummonMonsters:
            case EventIrOperation::SummonItem:
            case EventIrOperation::GiveItem:
            case EventIrOperation::CastSpell:
            case EventIrOperation::SetNpcGreeting:
            case EventIrOperation::CharacterAnimation:
            case EventIrOperation::IsActorKilled:
                break;

            case EventIrOperation::Compare:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const VariableRef variable = decodeVariable(instruction.arguments[0]);
                    const int32_t compareValue = static_cast<int32_t>(instruction.arguments[1]);
                    const int32_t currentValue = getVariableValue(runtimeState, variable);
                    const bool compareSucceeded =
                        variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag
                        ? (currentValue != 0)
                        : (currentValue >= compareValue);

                    std::cout << "  cmp raw=" << instruction.arguments[0]
                              << " current=" << currentValue
                              << " expect=" << compareValue
                              << " -> " << (compareSucceeded ? "true" : "false") << '\n';

                    if (compareSucceeded && instruction.jumpTargetStep)
                    {
                        const std::unordered_map<uint8_t, size_t>::const_iterator iterator =
                            stepToInstructionIndex.find(*instruction.jumpTargetStep);

                        if (iterator != stepToInstructionIndex.end())
                        {
                            instructionIndex = iterator->second;
                            continue;
                        }
                    }
                }
                break;
            }

            case EventIrOperation::Jump:
            {
                std::cout << "  jump -> "
                          << (instruction.jumpTargetStep ? std::to_string(*instruction.jumpTargetStep) : "-")
                          << '\n';

                if (instruction.jumpTargetStep)
                {
                    const std::unordered_map<uint8_t, size_t>::const_iterator iterator =
                        stepToInstructionIndex.find(*instruction.jumpTargetStep);

                    if (iterator != stepToInstructionIndex.end())
                    {
                        instructionIndex = iterator->second;
                        continue;
                    }
                }
                break;
            }

            case EventIrOperation::Add:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const VariableRef variable = decodeVariable(instruction.arguments[0]);
                    addVariableValue(
                        runtimeState,
                        variable,
                        static_cast<int32_t>(instruction.arguments[1])
                    );
                    std::cout << "  add raw=" << instruction.arguments[0]
                              << " value=" << instruction.arguments[1]
                              << " -> " << getVariableValue(runtimeState, variable) << '\n';
                }
                break;
            }

            case EventIrOperation::Subtract:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const VariableRef variable = decodeVariable(instruction.arguments[0]);
                    subtractVariableValue(
                        runtimeState,
                        variable,
                        static_cast<int32_t>(instruction.arguments[1])
                    );
                    std::cout << "  sub raw=" << instruction.arguments[0]
                              << " value=" << instruction.arguments[1]
                              << " -> " << getVariableValue(runtimeState, variable) << '\n';
                }
                break;
            }

            case EventIrOperation::Set:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const VariableRef variable = decodeVariable(instruction.arguments[0]);
                    setVariableValue(
                        runtimeState,
                        variable,
                        static_cast<int32_t>(instruction.arguments[1])
                    );
                    std::cout << "  set raw=" << instruction.arguments[0]
                              << " value=" << instruction.arguments[1]
                              << " -> " << getVariableValue(runtimeState, variable) << '\n';
                }
                break;
            }

            case EventIrOperation::ShowMessage:
            case EventIrOperation::StatusText:
            {
                if (instruction.text && !instruction.text->empty())
                {
                    runtimeState.messages.push_back(*instruction.text);
                    std::cout << "  text: " << *instruction.text << '\n';
                }
                break;
            }

            case EventIrOperation::OpenChest:
                break;

            case EventIrOperation::ChangeDoorState:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const uint32_t mechanismId = instruction.arguments[0];
                    RuntimeMechanismState &runtimeMechanism = runtimeState.mechanisms[mechanismId];
                    const uint32_t actionValue = instruction.arguments[1];
                    MechanismAction action = MechanismAction::Open;

                    if (actionValue == 1)
                    {
                        action = MechanismAction::Close;
                    }
                    else if (actionValue == 2)
                    {
                        action = MechanismAction::Trigger;
                    }

                    applyMechanismAction(runtimeMechanism, action);
                    runtimeState.lastAffectedMechanismIds.push_back(mechanismId);
                    std::cout << "  mech " << mechanismId
                              << " action=" << actionValue
                              << " state=" << runtimeMechanism.state
                              << " moving=" << (runtimeMechanism.isMoving ? "yes" : "no") << '\n';
                }
                break;
            }

            case EventIrOperation::StopAnimation:
            {
                if (!instruction.arguments.empty())
                {
                    const uint32_t mechanismId = instruction.arguments[0];
                    RuntimeMechanismState &runtimeMechanism = runtimeState.mechanisms[mechanismId];
                    runtimeMechanism.isMoving = false;
                    runtimeState.lastAffectedMechanismIds.push_back(mechanismId);
                    std::cout << "  mech " << mechanismId
                              << " stopped at distance=" << runtimeMechanism.currentDistance << '\n';
                }
                break;
            }

            case EventIrOperation::SetTexture:
            {
                if (instruction.arguments.empty())
                {
                    break;
                }

                const uint32_t cogNumber = instruction.arguments[0];

                if (instruction.text && !instruction.text->empty())
                {
                    runtimeState.textureOverrides[cogNumber] = *instruction.text;
                    std::cout << "  texture cog=" << cogNumber << " name=\"" << *instruction.text << "\"\n";
                }
                else
                {
                    runtimeState.textureOverrides.erase(cogNumber);
                    std::cout << "  texture cog=" << cogNumber << " cleared\n";
                }
                break;
            }

            case EventIrOperation::ToggleIndoorLight:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const uint32_t lightId = instruction.arguments[0];
                    const bool isEnabled = instruction.arguments[1] != 0;
                    runtimeState.indoorLightsEnabled[lightId] = isEnabled;
                    std::cout << "  light " << lightId << " on=" << (isEnabled ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::SetFacetBit:
            {
                if (instruction.arguments.size() >= 3)
                {
                    const uint32_t faceId = instruction.arguments[0];
                    const uint32_t bit = instruction.arguments[1];
                    const bool isOn = instruction.arguments[2] != 0;

                    if (isOn)
                    {
                        runtimeState.facetSetMasks[faceId] |= bit;
                        runtimeState.facetClearMasks[faceId] &= ~bit;
                    }
                    else
                    {
                        runtimeState.facetClearMasks[faceId] |= bit;
                        runtimeState.facetSetMasks[faceId] &= ~bit;
                    }

                    std::cout << "  facet " << faceId
                              << " bit=0x" << std::hex << bit << std::dec
                              << " on=" << (isOn ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::SetActorFlag:
            case EventIrOperation::SetActorGroupFlag:
                break;

            case EventIrOperation::SetNpcTopic:
            {
                if (instruction.arguments.size() >= 3)
                {
                    runtimeState.npcTopics[instruction.arguments[0]][instruction.arguments[1]] =
                        instruction.arguments[2] != 0;
                }
                break;
            }

            case EventIrOperation::SetNpcGroupNews:
                break;

            case EventIrOperation::Unknown:
                break;
        }

        ++instructionIndex;
    }

    return true;
}
}
