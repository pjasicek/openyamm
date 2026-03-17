#include "game/EventRuntime.h"
#include "game/Party.h"

#include <iostream>
#include <algorithm>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
std::string sanitizeEventString(const std::string &value)
{
    std::string sanitized;
    sanitized.reserve(value.size());

    for (char character : value)
    {
        if (std::isprint(static_cast<unsigned char>(character)) != 0)
        {
            sanitized.push_back(character);
        }
    }

    return sanitized;
}

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
    else if (variable.tag == 0x0011)
    {
        variable.kind = VariableKind::Inventory;
        variable.rawId = variable.index;
    }
    else if (variable.tag == 0x000c)
    {
        variable.kind = VariableKind::Awards;
        variable.rawId = rawId;
    }
    else if (variable.tag == 0x0006 || variable.tag == 0x013e)
    {
        variable.kind = VariableKind::Players;
        variable.rawId = rawId;
    }
    else if (variable.tag == 0x0087 || variable.tag == 0x0088 || variable.tag == 0x0089)
    {
        variable.kind = VariableKind::Generic;
        variable.rawId = variable.tag;
    }

    return variable;
}

int32_t EventRuntime::getVariableValue(
    const EventRuntimeState &runtimeState,
    const VariableRef &variable,
    const Party *pParty
)
{
    if (variable.kind == VariableKind::Inventory)
    {
        return getInventoryItemCount(runtimeState, pParty, variable.rawId);
    }

    if (variable.kind == VariableKind::Players)
    {
        if (pParty == nullptr)
        {
            return 0;
        }

        return pParty->hasRosterMember(variable.index) ? static_cast<int32_t>(variable.index) : 0;
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        if (variable.kind == VariableKind::QBits
            && variable.rawId >= 400
            && variable.rawId <= 449
            && pParty != nullptr)
        {
            const uint32_t rosterId = variable.rawId - 399;
            return pParty->hasRosterMember(rosterId) ? 1 : 0;
        }

        const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = runtimeState.variables.find(variable.rawId);
        return iterator != runtimeState.variables.end() ? iterator->second : 0;
    }

    const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = runtimeState.variables.find(variable.rawId);
    return iterator != runtimeState.variables.end() ? iterator->second : 0;
}

void EventRuntime::setVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value)
{
    if (variable.kind == VariableKind::Inventory)
    {
        return;
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        runtimeState.variables[variable.rawId] = value != 0 ? 1 : 0;
        return;
    }

    runtimeState.variables[variable.rawId] = value;
}

void EventRuntime::addVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value)
{
    if (variable.kind == VariableKind::Inventory)
    {
        if (value > 0)
        {
            runtimeState.grantedItemIds.push_back(static_cast<uint32_t>(value));
        }
        return;
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        runtimeState.variables[variable.rawId] = value != 0 ? 1 : 0;
        return;
    }

    runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable, nullptr) + value;
}

void EventRuntime::subtractVariableValue(EventRuntimeState &runtimeState, const VariableRef &variable, int32_t value)
{
    if (variable.kind == VariableKind::Inventory)
    {
        if (value > 0)
        {
            runtimeState.removedItemIds.push_back(static_cast<uint32_t>(value));
        }
        return;
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        runtimeState.variables[variable.rawId] = 0;
        return;
    }

    runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable, nullptr) - value;
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
    EventRuntimeState &runtimeState,
    const Party *pParty
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
            return executeEvent(*pEvent, runtimeState, pParty);
        }
    }

    if (globalProgram)
    {
        const EventIrEvent *pEvent = findEventById(*globalProgram, eventId);

        if (pEvent != nullptr)
        {
            std::cout << "Executing global event " << eventId << '\n';
            return executeEvent(*pEvent, runtimeState, pParty);
        }
    }

    return false;
}

bool EventRuntime::canShowTopic(
    const std::optional<EventIrProgram> &globalProgram,
    uint16_t topicId,
    const EventRuntimeState &runtimeState,
    const Party *pParty
) const
{
    if (topicId == 0 || !globalProgram)
    {
        return topicId != 0;
    }

    const EventIrEvent *pEvent = findEventById(*globalProgram, topicId);
    return pEvent == nullptr ? true : evaluateCanShowTopic(*pEvent, runtimeState, pParty);
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

        if (executeEvent(event, runtimeState, nullptr))
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
        executeEvent(event, runtimeState, nullptr);
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

int32_t EventRuntime::getInventoryItemCount(
    const EventRuntimeState &runtimeState,
    const Party *pParty,
    uint32_t objectDescriptionId
)
{
    int32_t itemCount = 0;

    if (pParty != nullptr)
    {
        for (const Character &member : pParty->members())
        {
            for (const InventoryItem &item : member.inventory)
            {
                if (item.objectDescriptionId == objectDescriptionId)
                {
                    itemCount += static_cast<int32_t>(item.quantity);
                }
            }
        }
    }

    for (uint32_t grantedItemId : runtimeState.grantedItemIds)
    {
        if (grantedItemId == objectDescriptionId)
        {
            itemCount += 1;
        }
    }

    for (uint32_t removedItemId : runtimeState.removedItemIds)
    {
        if (removedItemId == objectDescriptionId)
        {
            itemCount = std::max(0, itemCount - 1);
        }
    }

    return itemCount;
}

bool EventRuntime::evaluateCompare(
    const EventRuntimeState &runtimeState,
    const EventIrInstruction &instruction,
    const Party *pParty
)
{
    if (instruction.arguments.size() < 2)
    {
        return false;
    }

    const VariableRef variable = decodeVariable(instruction.arguments[0]);
    const int32_t compareValue = static_cast<int32_t>(instruction.arguments[1]);
    const int32_t currentValue = getVariableValue(runtimeState, variable, pParty);

    return variable.kind == VariableKind::QBits
        || variable.kind == VariableKind::BoolFlag
        || variable.kind == VariableKind::Inventory
        ? (currentValue != 0)
        : (currentValue >= compareValue);
}

bool EventRuntime::evaluateCanShowTopic(
    const EventIrEvent &event,
    const EventRuntimeState &runtimeState,
    const Party *pParty
)
{
    std::unordered_map<uint8_t, size_t> stepToInstructionIndex;

    for (size_t instructionIndex = 0; instructionIndex < event.instructions.size(); ++instructionIndex)
    {
        stepToInstructionIndex[event.instructions[instructionIndex].step] = instructionIndex;
    }

    bool sawCanShowInstruction = false;
    bool isVisible = true;
    size_t instructionIndex = 0;

    while (instructionIndex < event.instructions.size())
    {
        const EventIrInstruction &instruction = event.instructions[instructionIndex];

        switch (instruction.operation)
        {
            case EventIrOperation::CompareCanShowTopic:
            {
                sawCanShowInstruction = true;
                const bool compareSucceeded = evaluateCompare(runtimeState, instruction, pParty);

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
                break;
            }

            case EventIrOperation::SetCanShowTopic:
                sawCanShowInstruction = true;
                isVisible = !instruction.arguments.empty() && instruction.arguments[0] != 0;
                break;

            case EventIrOperation::EndCanShowTopic:
                return isVisible;

            default:
                return sawCanShowInstruction ? isVisible : true;
        }

        ++instructionIndex;
    }

    return sawCanShowInstruction ? isVisible : true;
}

bool EventRuntime::executeEvent(const EventIrEvent &event, EventRuntimeState &runtimeState, const Party *pParty)
{
    runtimeState.lastAffectedMechanismIds.clear();
    runtimeState.openedChestIds.clear();
    runtimeState.grantedItemIds.clear();
    runtimeState.removedItemIds.clear();
    runtimeState.pendingDialogueContext.reset();
    runtimeState.pendingMapMove.reset();

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
            case EventIrOperation::CheckSkill:
            case EventIrOperation::MoveNpc:
            case EventIrOperation::ChangeEvent:
            case EventIrOperation::RandomJump:
            case EventIrOperation::SummonMonsters:
            case EventIrOperation::SummonItem:
            case EventIrOperation::CastSpell:
            case EventIrOperation::SetNpcGreeting:
            case EventIrOperation::CharacterAnimation:
            case EventIrOperation::IsActorKilled:
                break;

            case EventIrOperation::SpeakInHouse:
            {
                if (!instruction.arguments.empty())
                {
                    EventRuntimeState::PendingDialogueContext context = {};
                    context.kind = DialogueContextKind::HouseService;
                    context.sourceId = instruction.arguments[0];
                    runtimeState.pendingDialogueContext = std::move(context);
                    std::cout << "  house=" << instruction.arguments[0];

                    if (instruction.text && !instruction.text->empty())
                    {
                        std::cout << " name=\"" << *instruction.text << "\"";
                    }

                    std::cout << '\n';
                }
                break;
            }

            case EventIrOperation::SpeakNpc:
            {
                if (!instruction.arguments.empty())
                {
                    EventRuntimeState::PendingDialogueContext context = {};
                    context.kind = DialogueContextKind::NpcTalk;
                    context.sourceId = instruction.arguments[0];
                    runtimeState.pendingDialogueContext = std::move(context);
                    std::cout << "  npc=" << instruction.arguments[0] << '\n';
                }
                break;
            }

            case EventIrOperation::MoveToMap:
            {
                if (instruction.arguments.size() >= 3)
                {
                    EventRuntimeState::PendingMapMove pendingMapMove = {};
                    pendingMapMove.x = static_cast<int32_t>(instruction.arguments[0]);
                    pendingMapMove.y = static_cast<int32_t>(instruction.arguments[1]);
                    pendingMapMove.z = static_cast<int32_t>(instruction.arguments[2]);

                    if (instruction.text && !instruction.text->empty())
                    {
                        const std::string sanitizedName = sanitizeEventString(*instruction.text);

                        if (!sanitizedName.empty())
                        {
                            pendingMapMove.mapName = sanitizedName;
                        }
                    }

                    runtimeState.pendingMapMove = pendingMapMove;
                    std::cout << "  move_to_map=("
                              << pendingMapMove.x << ","
                              << pendingMapMove.y << ","
                              << pendingMapMove.z << ")";

                    if (pendingMapMove.mapName && !pendingMapMove.mapName->empty())
                    {
                        std::cout << " name=\"" << *pendingMapMove.mapName << "\"";
                    }

                    std::cout << '\n';
                }
                break;
            }

            case EventIrOperation::Compare:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const VariableRef variable = decodeVariable(instruction.arguments[0]);
                    const int32_t compareValue = static_cast<int32_t>(instruction.arguments[1]);
                    const int32_t currentValue = getVariableValue(runtimeState, variable, pParty);
                    const bool compareSucceeded = evaluateCompare(runtimeState, instruction, pParty);

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
                              << " -> " << getVariableValue(runtimeState, variable, pParty) << '\n';
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
                              << " -> " << getVariableValue(runtimeState, variable, pParty) << '\n';
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
                              << " -> " << getVariableValue(runtimeState, variable, pParty) << '\n';
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
            {
                if (!instruction.arguments.empty())
                {
                    runtimeState.openedChestIds.push_back(instruction.arguments[0]);
                    std::cout << "  open_chest=" << instruction.arguments[0] << '\n';
                }
                break;
            }

            case EventIrOperation::GiveItem:
            {
                if (!instruction.arguments.empty())
                {
                    runtimeState.grantedItemIds.push_back(instruction.arguments[0]);
                    std::cout << "  give_item=" << instruction.arguments[0] << '\n';
                }
                break;
            }

            case EventIrOperation::RemoveItems:
            {
                if (!instruction.arguments.empty())
                {
                    runtimeState.removedItemIds.push_back(instruction.arguments[0]);
                    std::cout << "  remove_item=" << instruction.arguments[0] << '\n';
                }
                break;
            }

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
                    runtimeState.npcTopicOverrides[instruction.arguments[0]][instruction.arguments[1]] =
                        instruction.arguments[2];
                    std::cout << "  npc_topic npc=" << instruction.arguments[0]
                              << " slot=" << instruction.arguments[1]
                              << " event=" << instruction.arguments[2] << '\n';
                }
                break;
            }

            case EventIrOperation::SetNpcGroupNews:
            {
                if (instruction.arguments.size() >= 2)
                {
                    runtimeState.npcGroupNews[instruction.arguments[0]] = instruction.arguments[1];
                }
                break;
            }

            case EventIrOperation::Unknown:
                break;
        }

        ++instructionIndex;
    }

    return true;
}
}
