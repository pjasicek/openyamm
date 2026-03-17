#include "game/EventIr.h"

#include <algorithm>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
std::string hexValue(uint32_t value)
{
    std::ostringstream stream;
    stream << "0x" << std::hex << value;
    return stream.str();
}

std::string quote(const std::string &value)
{
    return "\"" + value + "\"";
}

std::string decodeVariableRef(uint32_t rawValue)
{
    const uint32_t tag = rawValue & 0xFFFF;
    const uint32_t index = rawValue >> 16;

    if (tag == 0x0010)
    {
        return "QBits[" + std::to_string(index) + "]";
    }

    if (tag == 0x0011)
    {
        return "Inventory[" + std::to_string(index) + "]";
    }

    if (tag == 0x000c)
    {
        return "Awards[" + std::to_string(index) + "]";
    }

    if (tag == 0x0006 || tag == 0x013e)
    {
        return "Players[" + std::to_string(index) + "]";
    }

    std::ostringstream stream;
    stream << "Var(tag=" << hexValue(tag) << ", index=" << index << ")";
    return stream.str();
}

std::string decodeFacetBit(uint32_t rawValue)
{
    switch (rawValue)
    {
        case 0x00002000: return "Invisible";
        case 0x20000000: return "Untouchable";
        default: return hexValue(rawValue);
    }
}

std::string decodeActorBit(uint32_t rawValue)
{
    switch (rawValue)
    {
        case 0x00010000: return "Invisible";
        default: return hexValue(rawValue);
    }
}
}

bool EventIrProgram::buildFromEvtProgram(
    const EvtProgram &evtProgram,
    const StrTable &strTable,
    const HouseTable &houseTable,
    const NpcDialogTable &npcDialogTable
)
{
    m_events.clear();

    for (const EvtEvent &evtEvent : evtProgram.getEvents())
    {
        EventIrEvent irEvent = {};
        irEvent.eventId = evtEvent.eventId;

        for (const EvtInstruction &evtInstruction : evtEvent.instructions)
        {
            irEvent.instructions.push_back(
                convertInstruction(evtEvent.eventId, evtInstruction, strTable, houseTable, npcDialogTable)
            );
        }

        m_events.push_back(std::move(irEvent));
    }

    return true;
}

const std::vector<EventIrEvent> &EventIrProgram::getEvents() const
{
    return m_events;
}

size_t EventIrProgram::getInstructionCount() const
{
    size_t instructionCount = 0;

    for (const EventIrEvent &event : m_events)
    {
        instructionCount += event.instructions.size();
    }

    return instructionCount;
}

std::string EventIrProgram::dump() const
{
    std::ostringstream stream;

    for (const EventIrEvent &event : m_events)
    {
        stream << "event " << event.eventId << '\n';

        for (const EventIrInstruction &instruction : event.instructions)
        {
            stream << "  " << static_cast<unsigned>(instruction.step) << ": "
                   << operationName(instruction.operation);

            if (!instruction.arguments.empty())
            {
                stream << " [";

                for (size_t index = 0; index < instruction.arguments.size(); ++index)
                {
                    if (index > 0)
                    {
                        stream << ", ";
                    }

                    stream << instruction.arguments[index];
                }

                stream << "]";
            }

            if (instruction.jumpTargetStep)
            {
                stream << " -> " << static_cast<unsigned>(*instruction.jumpTargetStep);
            }

            if (instruction.text && !instruction.text->empty())
            {
                stream << " " << quote(*instruction.text);
            }

            if (instruction.note && !instruction.note->empty())
            {
                stream << " ; " << *instruction.note;
            }

            stream << '\n';
        }

        stream << "end\n\n";
    }

    return stream.str();
}

EventIrOperation EventIrProgram::mapOperation(EvtOpcode opcode)
{
    switch (opcode)
    {
        case EvtOpcode::Exit: return EventIrOperation::Exit;
        case EvtOpcode::MouseOver: return EventIrOperation::TriggerMouseOver;
        case EvtOpcode::OnMapReload: return EventIrOperation::TriggerOnLoadMap;
        case EvtOpcode::OnMapLeave: return EventIrOperation::TriggerOnLeaveMap;
        case EvtOpcode::OnTimer: return EventIrOperation::TriggerOnTimer;
        case EvtOpcode::OnLongTimer: return EventIrOperation::TriggerOnLongTimer;
        case EvtOpcode::OnDateTimer: return EventIrOperation::TriggerOnDateTimer;
        case EvtOpcode::EnableDateTimer: return EventIrOperation::EnableDateTimer;
        case EvtOpcode::Compare: return EventIrOperation::Compare;
        case EvtOpcode::OnCanShowDialogItemCmp: return EventIrOperation::CompareCanShowTopic;
        case EvtOpcode::Jmp: return EventIrOperation::Jump;
        case EvtOpcode::SetCanShowDialogItem: return EventIrOperation::SetCanShowTopic;
        case EvtOpcode::EndCanShowDialogItem: return EventIrOperation::EndCanShowTopic;
        case EvtOpcode::Add: return EventIrOperation::Add;
        case EvtOpcode::Subtract: return EventIrOperation::Subtract;
        case EvtOpcode::Set: return EventIrOperation::Set;
        case EvtOpcode::ShowMessage: return EventIrOperation::ShowMessage;
        case EvtOpcode::StatusText: return EventIrOperation::StatusText;
        case EvtOpcode::SpeakInHouse: return EventIrOperation::SpeakInHouse;
        case EvtOpcode::SpeakNpc: return EventIrOperation::SpeakNpc;
        case EvtOpcode::MoveToMap: return EventIrOperation::MoveToMap;
        case EvtOpcode::MoveNpc: return EventIrOperation::MoveNpc;
        case EvtOpcode::ChangeEvent: return EventIrOperation::ChangeEvent;
        case EvtOpcode::OpenChest: return EventIrOperation::OpenChest;
        case EvtOpcode::RandomGoTo: return EventIrOperation::RandomJump;
        case EvtOpcode::SummonMonsters: return EventIrOperation::SummonMonsters;
        case EvtOpcode::SummonItem: return EventIrOperation::SummonItem;
        case EvtOpcode::GiveItem: return EventIrOperation::GiveItem;
        case EvtOpcode::CastSpell: return EventIrOperation::CastSpell;
        case EvtOpcode::ChangeDoorState: return EventIrOperation::ChangeDoorState;
        case EvtOpcode::StopAnimation: return EventIrOperation::StopAnimation;
        case EvtOpcode::SetTexture: return EventIrOperation::SetTexture;
        case EvtOpcode::ToggleIndoorLight: return EventIrOperation::ToggleIndoorLight;
        case EvtOpcode::SetFacesBit: return EventIrOperation::SetFacetBit;
        case EvtOpcode::ToggleActorFlag: return EventIrOperation::SetActorFlag;
        case EvtOpcode::ToggleActorGroupFlag: return EventIrOperation::SetActorGroupFlag;
        case EvtOpcode::SetNpcTopic: return EventIrOperation::SetNpcTopic;
        case EvtOpcode::SetNpcGroupNews: return EventIrOperation::SetNpcGroupNews;
        case EvtOpcode::SetNpcGreeting: return EventIrOperation::SetNpcGreeting;
        case EvtOpcode::CharacterAnimation: return EventIrOperation::CharacterAnimation;
        case EvtOpcode::ForPartyMember: return EventIrOperation::ForPartyMember;
        case EvtOpcode::CheckItemsCount: return EventIrOperation::CheckItemsCount;
        case EvtOpcode::RemoveItems: return EventIrOperation::RemoveItems;
        case EvtOpcode::CheckSkill: return EventIrOperation::CheckSkill;
        case EvtOpcode::IsActorKilled: return EventIrOperation::IsActorKilled;
        default: return EventIrOperation::Unknown;
    }
}

std::string EventIrProgram::operationName(EventIrOperation operation)
{
    switch (operation)
    {
        case EventIrOperation::Exit: return "Exit";
        case EventIrOperation::TriggerMouseOver: return "Trigger.MouseOver";
        case EventIrOperation::TriggerOnLoadMap: return "Trigger.OnLoadMap";
        case EventIrOperation::TriggerOnLeaveMap: return "Trigger.OnLeaveMap";
        case EventIrOperation::TriggerOnTimer: return "Trigger.OnTimer";
        case EventIrOperation::TriggerOnLongTimer: return "Trigger.OnLongTimer";
        case EventIrOperation::TriggerOnDateTimer: return "Trigger.OnDateTimer";
        case EventIrOperation::EnableDateTimer: return "EnableDateTimer";
        case EventIrOperation::Compare: return "Compare";
        case EventIrOperation::CompareCanShowTopic: return "CompareCanShowTopic";
        case EventIrOperation::Jump: return "Jump";
        case EventIrOperation::SetCanShowTopic: return "SetCanShowTopic";
        case EventIrOperation::EndCanShowTopic: return "EndCanShowTopic";
        case EventIrOperation::Add: return "Add";
        case EventIrOperation::Subtract: return "Subtract";
        case EventIrOperation::Set: return "Set";
        case EventIrOperation::ShowMessage: return "ShowMessage";
        case EventIrOperation::StatusText: return "StatusText";
        case EventIrOperation::SpeakInHouse: return "SpeakInHouse";
        case EventIrOperation::SpeakNpc: return "SpeakNpc";
        case EventIrOperation::MoveToMap: return "MoveToMap";
        case EventIrOperation::MoveNpc: return "MoveNpc";
        case EventIrOperation::ChangeEvent: return "ChangeEvent";
        case EventIrOperation::OpenChest: return "OpenChest";
        case EventIrOperation::RandomJump: return "RandomJump";
        case EventIrOperation::SummonMonsters: return "SummonMonsters";
        case EventIrOperation::SummonItem: return "SummonItem";
        case EventIrOperation::GiveItem: return "GiveItem";
        case EventIrOperation::CastSpell: return "CastSpell";
        case EventIrOperation::ChangeDoorState: return "ChangeMechanismState";
        case EventIrOperation::StopAnimation: return "StopMechanism";
        case EventIrOperation::SetTexture: return "SetTexture";
        case EventIrOperation::ToggleIndoorLight: return "ToggleIndoorLight";
        case EventIrOperation::SetFacetBit: return "SetFacetBit";
        case EventIrOperation::SetActorFlag: return "SetActorFlag";
        case EventIrOperation::SetActorGroupFlag: return "SetActorGroupFlag";
        case EventIrOperation::SetNpcTopic: return "SetNpcTopic";
        case EventIrOperation::SetNpcGroupNews: return "SetNpcGroupNews";
        case EventIrOperation::SetNpcGreeting: return "SetNpcGreeting";
        case EventIrOperation::CharacterAnimation: return "CharacterAnimation";
        case EventIrOperation::ForPartyMember: return "ForPartyMember";
        case EventIrOperation::CheckItemsCount: return "CheckItemsCount";
        case EventIrOperation::RemoveItems: return "RemoveItems";
        case EventIrOperation::CheckSkill: return "CheckSkill";
        case EventIrOperation::IsActorKilled: return "IsActorKilled";
        case EventIrOperation::Unknown: break;
    }

    return "Unknown";
}

EventIrInstruction EventIrProgram::convertInstruction(
    uint16_t eventId,
    const EvtInstruction &evtInstruction,
    const StrTable &strTable,
    const HouseTable &houseTable,
    const NpcDialogTable &npcDialogTable
)
{
    EventIrInstruction irInstruction = {};
    irInstruction.eventId = eventId;
    irInstruction.step = evtInstruction.step;
    irInstruction.operation = mapOperation(evtInstruction.opcode);
    irInstruction.sourceOpcode = evtInstruction.opcode;

    if (evtInstruction.value1)
    {
        irInstruction.arguments.push_back(*evtInstruction.value1);
    }

    if (evtInstruction.value2)
    {
        irInstruction.arguments.push_back(*evtInstruction.value2);
    }

    if (evtInstruction.value3)
    {
        irInstruction.arguments.push_back(*evtInstruction.value3);
    }

    if (evtInstruction.booleanValue)
    {
        irInstruction.arguments.push_back(*evtInstruction.booleanValue);
    }

    if (evtInstruction.targetStep)
    {
        irInstruction.jumpTargetStep = evtInstruction.targetStep;
    }

    if (evtInstruction.textId)
    {
        const std::optional<std::string> text = strTable.get(*evtInstruction.textId);

        if (text)
        {
            irInstruction.text = *text;
        }
    }

    if ((evtInstruction.opcode == EvtOpcode::ShowMessage || evtInstruction.opcode == EvtOpcode::StatusText)
        && evtInstruction.value1)
    {
        std::optional<std::string> text = strTable.get(static_cast<uint8_t>(*evtInstruction.value1));

        if (!text)
        {
            text = npcDialogTable.getText(*evtInstruction.value1);
        }

        if (text)
        {
            irInstruction.text = *text;
        }
    }

    if (evtInstruction.opcode == EvtOpcode::SpeakInHouse && evtInstruction.value1)
    {
        const std::optional<std::string> houseName = houseTable.getName(*evtInstruction.value1);

        if (houseName)
        {
            irInstruction.text = *houseName;
        }
    }
    else if (evtInstruction.stringValue)
    {
        irInstruction.text = *evtInstruction.stringValue;
    }

    if (!evtInstruction.listValues.empty())
    {
        std::ostringstream note;
        note << "raw_list=";

        for (size_t index = 0; index < evtInstruction.listValues.size(); ++index)
        {
            if (index > 0)
            {
                note << ",";
            }

            note << static_cast<unsigned>(evtInstruction.listValues[index]);
        }

        irInstruction.note = note.str();
    }

    switch (irInstruction.operation)
    {
        case EventIrOperation::Compare:
        case EventIrOperation::Add:
        case EventIrOperation::Subtract:
        case EventIrOperation::Set:
        {
            if (evtInstruction.value1 && evtInstruction.value2)
            {
                std::ostringstream note;
                note << decodeVariableRef(*evtInstruction.value1) << " value=" << *evtInstruction.value2;
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::TriggerOnTimer:
        case EventIrOperation::TriggerOnLongTimer:
        case EventIrOperation::TriggerOnDateTimer:
        case EventIrOperation::EnableDateTimer:
        case EventIrOperation::ForPartyMember:
        {
            if (!evtInstruction.listValues.empty())
            {
                std::ostringstream note;

                for (size_t index = 0; index < evtInstruction.listValues.size(); ++index)
                {
                    if (index > 0)
                    {
                        note << ",";
                    }

                    note << static_cast<unsigned>(evtInstruction.listValues[index]);
                }

                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::SetCanShowTopic:
        {
            if (evtInstruction.value1)
            {
                std::ostringstream note;
                note << "topic=" << *evtInstruction.value1;
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::CompareCanShowTopic:
        {
            std::ostringstream note;
            note << "topic_cmp";

            if (evtInstruction.value1 && evtInstruction.value2)
            {
                note << " " << decodeVariableRef(*evtInstruction.value1) << " value=" << *evtInstruction.value2;
            }

            irInstruction.note = note.str();
            break;
        }

        case EventIrOperation::EndCanShowTopic:
            irInstruction.note = "topic_end";
            break;

        case EventIrOperation::CheckItemsCount:
        case EventIrOperation::RemoveItems:
        {
            if (evtInstruction.value1 && evtInstruction.value2)
            {
                std::ostringstream note;
                note << "item=" << *evtInstruction.value1 << " count=" << *evtInstruction.value2;
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::CheckSkill:
        {
            if (evtInstruction.value1 && evtInstruction.value2)
            {
                std::ostringstream note;
                note << "skill=" << *evtInstruction.value1 << " mastery=" << *evtInstruction.value2;
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::SetFacetBit:
        {
            if (evtInstruction.value1 && evtInstruction.value2 && evtInstruction.booleanValue)
            {
                std::ostringstream note;
                note << "facet=" << *evtInstruction.value1
                     << " bit=" << decodeFacetBit(*evtInstruction.value2)
                     << " on=" << static_cast<unsigned>(*evtInstruction.booleanValue);
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::SetActorFlag:
        case EventIrOperation::SetActorGroupFlag:
        {
            if (evtInstruction.value1 && evtInstruction.value2 && evtInstruction.booleanValue)
            {
                std::ostringstream note;
                note << "target=" << *evtInstruction.value1
                     << " bit=" << decodeActorBit(*evtInstruction.value2)
                     << " on=" << static_cast<unsigned>(*evtInstruction.booleanValue);
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::ChangeDoorState:
        {
            if (evtInstruction.value1 && evtInstruction.value2)
            {
                std::ostringstream note;
                note << "mechanism=" << *evtInstruction.value1 << " action=" << *evtInstruction.value2;
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::StopAnimation:
        {
            if (evtInstruction.value1)
            {
                irInstruction.note = "mechanism=" + std::to_string(*evtInstruction.value1);
            }
            break;
        }

        case EventIrOperation::SetTexture:
        {
            if (evtInstruction.value1)
            {
                std::ostringstream note;
                note << "cog=" << *evtInstruction.value1;

                if (evtInstruction.stringValue)
                {
                    note << " texture=" << quote(*evtInstruction.stringValue);
                }

                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::ToggleIndoorLight:
        {
            if (evtInstruction.value1)
            {
                std::ostringstream note;
                note << "light=" << *evtInstruction.value1;

                if (evtInstruction.booleanValue)
                {
                    note << " on=" << static_cast<unsigned>(*evtInstruction.booleanValue);
                }

                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::OpenChest:
        {
            if (evtInstruction.value1)
            {
                irInstruction.note = "chest=" + std::to_string(*evtInstruction.value1);
            }
            break;
        }

        case EventIrOperation::SetNpcTopic:
        {
            if (evtInstruction.value1 && evtInstruction.value2 && evtInstruction.value3)
            {
                std::ostringstream note;
                note << "npc=" << *evtInstruction.value1
                     << " slot=" << *evtInstruction.value2
                     << " event=" << *evtInstruction.value3;
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::SetNpcGroupNews:
        {
            if (evtInstruction.value1 && evtInstruction.value2)
            {
                std::ostringstream note;
                note << "group=" << *evtInstruction.value1 << " news=" << *evtInstruction.value2;
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::RandomJump:
        {
            if (!evtInstruction.listValues.empty())
            {
                std::ostringstream note;
                note << "targets=";

                for (size_t index = 0; index < evtInstruction.listValues.size(); ++index)
                {
                    if (index > 0)
                    {
                        note << ",";
                    }

                    note << static_cast<unsigned>(evtInstruction.listValues[index]);
                }

                irInstruction.note = note.str();
            }
            break;
        }

        default:
            break;
    }

    if (irInstruction.operation != EventIrOperation::Unknown &&
        !evtInstruction.rawPayload.empty() &&
        irInstruction.arguments.empty() &&
        !irInstruction.jumpTargetStep &&
        !irInstruction.text &&
        !irInstruction.note)
    {
        std::ostringstream note;
        note << "raw=" << evtInstruction.rawPayload.size() << " bytes";
        irInstruction.note = note.str();
    }

    if (irInstruction.operation == EventIrOperation::Unknown)
    {
        std::ostringstream note;
        note << "opcode=" << static_cast<unsigned>(evtInstruction.opcode)
             << " raw=" << evtInstruction.rawPayload.size() << " bytes";
        irInstruction.note = note.str();
    }

    return irInstruction;
}
}
