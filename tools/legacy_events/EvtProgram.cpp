#include "tools/legacy_events/EvtProgram.h"

#include <algorithm>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
template <typename T>
bool readValue(const std::vector<uint8_t> &bytes, size_t offset, T &value)
{
    if (offset + sizeof(T) > bytes.size())
    {
        return false;
    }

    std::memcpy(&value, bytes.data() + offset, sizeof(T));
    return true;
}

template <typename T>
std::optional<T> readPayloadValue(const std::vector<uint8_t> &bytes, size_t offset)
{
    T value = {};

    if (!readValue(bytes, offset, value))
    {
        return std::nullopt;
    }

    return value;
}

std::optional<std::string> readNullTerminatedString(const std::vector<uint8_t> &bytes, size_t offset)
{
    if (offset > bytes.size())
    {
        return std::nullopt;
    }

    std::string value;

    for (size_t index = offset; index < bytes.size(); ++index)
    {
        if (bytes[index] == 0)
        {
            return value;
        }

        value.push_back(static_cast<char>(bytes[index]));
    }

    return std::nullopt;
}

std::string quote(const std::string &value)
{
    return "\"" + value + "\"";
}

std::string formatDoorAction(uint32_t value)
{
    switch (value)
    {
        case 0: return "DoorAction.Open";
        case 1: return "DoorAction.Close";
        case 2: return "DoorAction.Trigger";
        default: return std::to_string(value);
    }
}
}

bool EvtProgram::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    m_events.clear();
    size_t offset = 0;

    while (offset < bytes.size())
    {
        const size_t recordSize = static_cast<size_t>(bytes[offset]) + 1;

        if (recordSize < 5)
        {
            return false;
        }

        const size_t recordEnd = offset + recordSize;

        if (recordEnd > bytes.size())
        {
            return false;
        }

        uint16_t eventId = 0;

        if (!readValue(bytes, offset + 1, eventId))
        {
            return false;
        }

        std::vector<uint8_t> record(bytes.begin() + static_cast<ptrdiff_t>(offset + 3), bytes.begin() + static_cast<ptrdiff_t>(recordEnd));
        EvtInstruction instruction = {};

        if (!parseInstruction(record, instruction))
        {
            return false;
        }

        auto eventIt = std::find_if(
            m_events.begin(),
            m_events.end(),
            [eventId](const EvtEvent &event)
            {
                return event.eventId == eventId;
            }
        );

        if (eventIt == m_events.end())
        {
            EvtEvent event = {};
            event.eventId = eventId;
            event.instructions.push_back(std::move(instruction));
            m_events.push_back(std::move(event));
        }
        else
        {
            eventIt->instructions.push_back(std::move(instruction));
        }

        offset = recordEnd;
    }

    std::sort(
        m_events.begin(),
        m_events.end(),
        [](const EvtEvent &left, const EvtEvent &right)
        {
            return left.eventId < right.eventId;
        }
    );

    for (EvtEvent &event : m_events)
    {
        std::sort(
            event.instructions.begin(),
            event.instructions.end(),
            [](const EvtInstruction &left, const EvtInstruction &right)
            {
                return left.step < right.step;
            }
        );
    }

    return true;
}

const std::vector<EvtEvent> &EvtProgram::getEvents() const
{
    return m_events;
}

size_t EvtProgram::getInstructionCount() const
{
    size_t instructionCount = 0;

    for (const EvtEvent &event : m_events)
    {
        instructionCount += event.instructions.size();
    }

    return instructionCount;
}

const EvtEvent *EvtProgram::findEvent(uint16_t eventId) const
{
    auto eventIt = std::find_if(
        m_events.begin(),
        m_events.end(),
        [eventId](const EvtEvent &event)
        {
            return event.eventId == eventId;
        }
    );

    if (eventIt == m_events.end())
    {
        return nullptr;
    }

    return &(*eventIt);
}

bool EvtProgram::hasEvent(uint16_t eventId) const
{
    return findEvent(eventId) != nullptr;
}

bool EvtProgram::isHintOnlyEvent(uint16_t eventId) const
{
    const EvtEvent *pEvent = findEvent(eventId);

    if (pEvent == nullptr || pEvent->instructions.size() < 2)
    {
        return false;
    }

    return pEvent->instructions[0].opcode == EvtOpcode::MouseOver
        && pEvent->instructions[1].opcode == EvtOpcode::Exit;
}

std::optional<std::string> EvtProgram::getHint(uint16_t eventId, const StrTable &strTable, const HouseTable &houseTable) const
{
    const EvtEvent *pEvent = findEvent(eventId);

    if (pEvent == nullptr)
    {
        return std::nullopt;
    }

    bool mouseOverFound = false;

    for (const EvtInstruction &instruction : pEvent->instructions)
    {
        if (instruction.opcode == EvtOpcode::MouseOver && instruction.textId)
        {
            mouseOverFound = true;
            const std::optional<std::string> text = strTable.get(*instruction.textId);

            if (text && !text->empty())
            {
                return text;
            }
        }

        if (mouseOverFound && instruction.opcode == EvtOpcode::SpeakInHouse && instruction.value1)
        {
            const std::optional<std::string> houseName = houseTable.getName(*instruction.value1);

            if (houseName && !houseName->empty())
            {
                return houseName;
            }
        }
    }

    return std::nullopt;
}

std::optional<std::string> EvtProgram::summarizeEvent(uint16_t eventId, const StrTable &strTable, const HouseTable &houseTable) const
{
    const EvtEvent *pEvent = findEvent(eventId);

    if (pEvent == nullptr)
    {
        return std::nullopt;
    }

    std::ostringstream stream;
    stream << eventId << ":";

    const std::optional<std::string> hint = getHint(eventId, strTable, houseTable);

    if (hint && !hint->empty())
    {
        stream << " " << quote(*hint);
    }

    if (!pEvent->instructions.empty())
    {
        stream << " ";
    }

    const size_t instructionCount = std::min<size_t>(pEvent->instructions.size(), 3);

    for (size_t instructionIndex = 0; instructionIndex < instructionCount; ++instructionIndex)
    {
        if (instructionIndex > 0)
        {
            stream << ",";
        }

        stream << opcodeName(pEvent->instructions[instructionIndex].opcode);
    }

    if (pEvent->instructions.size() > instructionCount)
    {
        stream << ",...";
    }

    return stream.str();
}

std::vector<uint32_t> EvtProgram::getOpenedChestIds(uint16_t eventId) const
{
    std::vector<uint32_t> chestIds;
    const EvtEvent *pEvent = findEvent(eventId);

    if (pEvent == nullptr)
    {
        return chestIds;
    }

    for (const EvtInstruction &instruction : pEvent->instructions)
    {
        if (instruction.opcode != EvtOpcode::OpenChest || !instruction.value1)
        {
            continue;
        }

        chestIds.push_back(*instruction.value1);
    }

    return chestIds;
}

std::string EvtProgram::dump(const StrTable &strTable) const
{
    std::ostringstream stream;
    const HouseTable emptyHouseTable = {};

    for (const EvtEvent &event : m_events)
    {
        stream << "event " << event.eventId;

        const std::optional<std::string> hint = getHint(event.eventId, strTable, emptyHouseTable);

        if (hint && !hint->empty())
        {
            stream << "  -- " << quote(*hint);
        }

        stream << '\n';

        for (const EvtInstruction &instruction : event.instructions)
        {
            stream << "  " << formatInstruction(instruction, strTable) << '\n';
        }

        stream << "end\n\n";
    }

    return stream.str();
}

std::string EvtProgram::opcodeName(EvtOpcode opcode)
{
    switch (opcode)
    {
        case EvtOpcode::Exit: return "Exit";
        case EvtOpcode::SpeakInHouse: return "SpeakInHouse";
        case EvtOpcode::PlaySound: return "PlaySound";
        case EvtOpcode::MouseOver: return "MouseOver";
        case EvtOpcode::LocationName: return "LocationName";
        case EvtOpcode::MoveToMap: return "MoveToMap";
        case EvtOpcode::OpenChest: return "OpenChest";
        case EvtOpcode::ShowFace: return "ShowFace";
        case EvtOpcode::ReceiveDamage: return "ReceiveDamage";
        case EvtOpcode::SetSnow: return "SetSnow";
        case EvtOpcode::SetTexture: return "SetTexture";
        case EvtOpcode::ShowMovie: return "ShowMovie";
        case EvtOpcode::SetSprite: return "SetSprite";
        case EvtOpcode::Compare: return "Cmp";
        case EvtOpcode::ChangeDoorState: return "ChangeDoorState";
        case EvtOpcode::Add: return "Add";
        case EvtOpcode::Subtract: return "Subtract";
        case EvtOpcode::Set: return "Set";
        case EvtOpcode::SummonMonsters: return "SummonMonsters";
        case EvtOpcode::CastSpell: return "CastSpell";
        case EvtOpcode::SpeakNpc: return "SpeakNPC";
        case EvtOpcode::SetFacesBit: return "SetFacetBit";
        case EvtOpcode::ToggleActorFlag: return "ToggleActorFlag";
        case EvtOpcode::RandomGoTo: return "RandomGoTo";
        case EvtOpcode::InputString: return "InputString";
        case EvtOpcode::StatusText: return "StatusText";
        case EvtOpcode::ShowMessage: return "ShowMessage";
        case EvtOpcode::OnTimer: return "OnTimer";
        case EvtOpcode::ToggleIndoorLight: return "ToggleIndoorLight";
        case EvtOpcode::PressAnyKey: return "PressAnyKey";
        case EvtOpcode::SummonItem: return "SummonItem";
        case EvtOpcode::ForPartyMember: return "ForPartyMember";
        case EvtOpcode::Jmp: return "GoTo";
        case EvtOpcode::OnMapReload: return "OnLoadMap";
        case EvtOpcode::OnLongTimer: return "OnLongTimer";
        case EvtOpcode::SetNpcTopic: return "SetNPCTopic";
        case EvtOpcode::MoveNpc: return "MoveNPC";
        case EvtOpcode::GiveItem: return "GiveItem";
        case EvtOpcode::ChangeEvent: return "ChangeEvent";
        case EvtOpcode::CheckSkill: return "CheckSkill";
        case EvtOpcode::OnCanShowDialogItemCmp: return "CanShowTopic.Cmp";
        case EvtOpcode::EndCanShowDialogItem: return "CanShowTopic.Exit";
        case EvtOpcode::SetCanShowDialogItem: return "CanShowTopic.Set";
        case EvtOpcode::SetNpcGroupNews: return "SetNPCGroupNews";
        case EvtOpcode::SetActorGroup: return "SetActorGroup";
        case EvtOpcode::NpcSetItem: return "NPCSetItem";
        case EvtOpcode::SetNpcGreeting: return "SetNPCGreeting";
        case EvtOpcode::IsActorKilled: return "IsActorKilled";
        case EvtOpcode::CanShowTopicIsActorKilled: return "CanShowTopic.IsActorKilled";
        case EvtOpcode::OnMapLeave: return "OnLeaveMap";
        case EvtOpcode::ChangeGroup: return "ChangeGroup";
        case EvtOpcode::ChangeGroupAlly: return "ChangeGroupAlly";
        case EvtOpcode::CheckSeason: return "CheckSeason";
        case EvtOpcode::ToggleActorGroupFlag: return "SetMonGroupBit";
        case EvtOpcode::ToggleChestFlag: return "ToggleChestFlag";
        case EvtOpcode::CharacterAnimation: return "CharacterAnimation";
        case EvtOpcode::SetActorItem: return "SetActorItem";
        case EvtOpcode::OnDateTimer: return "OnDateTimer";
        case EvtOpcode::EnableDateTimer: return "EnableDateTimer";
        case EvtOpcode::StopAnimation: return "StopAnimation";
        case EvtOpcode::CheckItemsCount: return "CheckItemsCount";
        case EvtOpcode::RemoveItems: return "RemoveItems";
        case EvtOpcode::SpecialJump: return "SpecialJump";
        case EvtOpcode::IsTotalBountyHuntingAwardInRange: return "IsTotalBountyHuntingAwardInRange";
        case EvtOpcode::IsNpcInParty: return "IsNPCInParty";
        case EvtOpcode::Invalid: break;
    }

    return "Unknown";
}

bool EvtProgram::parseInstruction(const std::vector<uint8_t> &record, EvtInstruction &instruction)
{
    if (record.size() < 2)
    {
        return false;
    }

    instruction.step = record[0];
    instruction.opcode = static_cast<EvtOpcode>(record[1]);
    instruction.rawPayload.assign(record.begin() + 2, record.end());

    auto tryReadU8 = [&record](size_t offset) -> std::optional<uint8_t>
    {
        uint8_t value = 0;

        if (!readValue(record, offset, value))
        {
            return std::nullopt;
        }

        return value;
    };

    auto tryReadU32 = [&record](size_t offset) -> std::optional<uint32_t>
    {
        uint32_t value = 0;

        if (!readValue(record, offset, value))
        {
            return std::nullopt;
        }

        return value;
    };

    auto tryReadU16 = [&record](size_t offset) -> std::optional<uint16_t>
    {
        uint16_t value = 0;

        if (!readValue(record, offset, value))
        {
            return std::nullopt;
        }

        return value;
    };

    switch (instruction.opcode)
    {
        case EvtOpcode::Exit:
        case EvtOpcode::OnMapReload:
        case EvtOpcode::OnMapLeave:
        case EvtOpcode::EndCanShowDialogItem:
            break;

        case EvtOpcode::ForPartyMember:
            instruction.listValues.assign(record.begin() + 2, record.end());
            break;

        case EvtOpcode::MouseOver:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.textId = *value;
            }
            break;

        case EvtOpcode::Jmp:
        case EvtOpcode::CheckSeason:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                if (instruction.opcode == EvtOpcode::CheckSeason)
                {
                    instruction.value1 = *value;
                }
                else
                {
                    instruction.targetStep = *value;
                }
            }

            if (instruction.opcode == EvtOpcode::CheckSeason)
            {
                if (const std::optional<uint8_t> value = tryReadU8(3))
                {
                    instruction.targetStep = *value;
                }
            }
            break;

        case EvtOpcode::LocationName:
        case EvtOpcode::OpenChest:
        case EvtOpcode::SetCanShowDialogItem:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.value1 = *value;
            }
            break;

        case EvtOpcode::StatusText:
        case EvtOpcode::ShowMessage:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }
            break;

        case EvtOpcode::SpeakInHouse:
        case EvtOpcode::SpeakNpc:
        case EvtOpcode::ChangeEvent:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }
            break;

        case EvtOpcode::MoveNpc:
        case EvtOpcode::SetActorGroup:
        case EvtOpcode::ChangeGroup:
        case EvtOpcode::ChangeGroupAlly:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(6))
            {
                instruction.value2 = *value;
            }
            break;

        case EvtOpcode::PlaySound:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(6))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(10))
            {
                instruction.value3 = *value;
            }
            break;

        case EvtOpcode::ShowFace:
        case EvtOpcode::CharacterAnimation:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(3))
            {
                instruction.value2 = *value;
            }
            break;

        case EvtOpcode::ReceiveDamage:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(3))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(4))
            {
                instruction.value3 = *value;
            }
            break;

        case EvtOpcode::SetSnow:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(3))
            {
                instruction.booleanValue = *value;
            }
            break;

        case EvtOpcode::SetTexture:
        case EvtOpcode::SetSprite:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (instruction.opcode == EvtOpcode::SetTexture)
            {
                instruction.stringValue = readNullTerminatedString(record, 6);
            }
            else
            {
                if (const std::optional<uint8_t> value = tryReadU8(6))
                {
                    instruction.booleanValue = *value;
                }
                instruction.stringValue = readNullTerminatedString(record, 7);
            }
            break;

        case EvtOpcode::ShowMovie:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.booleanValue = *value;
            }

            instruction.stringValue = readNullTerminatedString(record, 4);
            break;

        case EvtOpcode::MoveToMap:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(6))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(10))
            {
                instruction.value3 = *value;
            }
            instruction.stringValue = readNullTerminatedString(record, 28);
            if (instruction.stringValue && instruction.stringValue->empty())
            {
                instruction.stringValue = readNullTerminatedString(record, 29);
            }
            break;

        case EvtOpcode::Compare:
        case EvtOpcode::Add:
        case EvtOpcode::Subtract:
        case EvtOpcode::Set:
        case EvtOpcode::OnCanShowDialogItemCmp:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(4))
            {
                instruction.value2 = *value;
            }

            if (instruction.opcode == EvtOpcode::Compare || instruction.opcode == EvtOpcode::OnCanShowDialogItemCmp)
            {
                if (const std::optional<uint8_t> value = tryReadU8(8))
                {
                    instruction.targetStep = *value;
                }
            }
            break;

        case EvtOpcode::ChangeDoorState:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(3))
            {
                instruction.value2 = *value;
            }
            break;

        case EvtOpcode::StopAnimation:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.value1 = *value;
            }
            break;

        case EvtOpcode::ToggleIndoorLight:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(6))
            {
                instruction.booleanValue = *value;
            }
            break;

        case EvtOpcode::InputString:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(6))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(10))
            {
                instruction.value3 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(14))
            {
                instruction.targetStep = *value;
            }
            break;

        case EvtOpcode::SetFacesBit:
        case EvtOpcode::ToggleActorFlag:
        case EvtOpcode::SetNpcGroupNews:
        case EvtOpcode::ToggleActorGroupFlag:
        case EvtOpcode::ToggleChestFlag:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(6))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(10))
            {
                instruction.booleanValue = *value;
            }
            break;

        case EvtOpcode::SetNpcTopic:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(6))
            {
                instruction.value2 = *value & 0xFFu;
                instruction.value3 = *value >> 8;
            }

            if (const std::optional<uint8_t> value = tryReadU8(10))
            {
                instruction.booleanValue = *value;
            }
            break;

        case EvtOpcode::SetNpcGreeting:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(6))
            {
                instruction.value2 = *value;
            }
            break;

        case EvtOpcode::NpcSetItem:
        case EvtOpcode::SetActorItem:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(6))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(10))
            {
                instruction.booleanValue = *value;
            }
            break;

        case EvtOpcode::RandomGoTo:
            instruction.listValues.assign(record.begin() + 2, record.end());
            break;

        case EvtOpcode::OnTimer:
        case EvtOpcode::OnLongTimer:
            instruction.listValues.assign(record.begin() + 2, record.end());
            break;

        case EvtOpcode::CheckItemsCount:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint16_t> value = tryReadU16(6))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(8))
            {
                instruction.targetStep = *value;
            }
            break;

        case EvtOpcode::RemoveItems:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint16_t> value = tryReadU16(6))
            {
                instruction.value2 = *value;
            }
            break;

        case EvtOpcode::CheckSkill:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(3))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(4))
            {
                instruction.value3 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(8))
            {
                instruction.targetStep = *value;
            }
            break;

        case EvtOpcode::CanShowTopicIsActorKilled:
            if (const std::optional<uint8_t> value = tryReadU8(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(3))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(7))
            {
                instruction.value3 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(8))
            {
                instruction.targetStep = *value;
            }
            break;

        case EvtOpcode::SpecialJump:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(6))
            {
                instruction.value2 = *value;
            }
            break;

        case EvtOpcode::IsTotalBountyHuntingAwardInRange:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint32_t> value = tryReadU32(6))
            {
                instruction.value2 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(10))
            {
                instruction.targetStep = *value;
            }
            break;

        case EvtOpcode::IsNpcInParty:
            if (const std::optional<uint32_t> value = tryReadU32(2))
            {
                instruction.value1 = *value;
            }

            if (const std::optional<uint8_t> value = tryReadU8(6))
            {
                instruction.targetStep = *value;
            }
            break;

        default:
            break;
    }

    return true;
}

std::string EvtProgram::formatInstruction(const EvtInstruction &instruction, const StrTable &strTable)
{
    std::ostringstream stream;
    stream << static_cast<unsigned>(instruction.step) << ": " << opcodeName(instruction.opcode);

    switch (instruction.opcode)
    {
        case EvtOpcode::MouseOver:
            if (instruction.textId)
            {
                stream << " {Str=" << static_cast<unsigned>(*instruction.textId);
                const std::optional<std::string> value = strTable.get(*instruction.textId);

                if (value)
                {
                    stream << " " << quote(*value);
                }

                stream << "}";
            }
            break;

        case EvtOpcode::Compare:
        case EvtOpcode::OnCanShowDialogItemCmp:
            stream << " {Var=" << (instruction.value1 ? *instruction.value1 : 0)
                   << " Value=" << (instruction.value2 ? *instruction.value2 : 0)
                   << " jump=" << (instruction.targetStep ? static_cast<unsigned>(*instruction.targetStep) : 0) << "}";
            break;

        case EvtOpcode::Add:
        case EvtOpcode::Subtract:
        case EvtOpcode::Set:
            stream << " {Var=" << (instruction.value1 ? *instruction.value1 : 0)
                   << " Value=" << (instruction.value2 ? *instruction.value2 : 0) << "}";
            break;

        case EvtOpcode::Jmp:
        case EvtOpcode::CheckSeason:
            stream << " {jump=" << (instruction.targetStep ? static_cast<unsigned>(*instruction.targetStep) : 0) << "}";
            break;

        case EvtOpcode::OpenChest:
        case EvtOpcode::LocationName:
        case EvtOpcode::StatusText:
        case EvtOpcode::ShowMessage:
        case EvtOpcode::SetCanShowDialogItem:
        case EvtOpcode::CharacterAnimation:
            stream << " {" << (instruction.value1 ? *instruction.value1 : 0) << "}";
            break;

        case EvtOpcode::SpeakInHouse:
        case EvtOpcode::SpeakNpc:
        case EvtOpcode::MoveNpc:
        case EvtOpcode::ChangeEvent:
            stream << " {Id=" << (instruction.value1 ? *instruction.value1 : 0) << "}";
            break;

        case EvtOpcode::SetTexture:
        case EvtOpcode::SetSprite:
        case EvtOpcode::ShowMovie:
            stream << " {Id=" << (instruction.value1 ? *instruction.value1 : 0);

            if (instruction.stringValue)
            {
                stream << " " << quote(*instruction.stringValue);
            }

            stream << "}";
            break;

        case EvtOpcode::MoveToMap:
            stream << " {x=" << (instruction.value1 ? *instruction.value1 : 0)
                   << " y=" << (instruction.value2 ? *instruction.value2 : 0)
                   << " z=" << (instruction.value3 ? *instruction.value3 : 0);

            if (instruction.stringValue)
            {
                stream << " map=" << quote(*instruction.stringValue);
            }

            stream << "}";
            break;

        case EvtOpcode::SummonMonsters:
        {
            const std::optional<uint8_t> typeIndex = readPayloadValue<uint8_t>(instruction.rawPayload, 0);
            const std::optional<uint8_t> level = readPayloadValue<uint8_t>(instruction.rawPayload, 1);
            const std::optional<uint8_t> count = readPayloadValue<uint8_t>(instruction.rawPayload, 2);
            const std::optional<int32_t> x = readPayloadValue<int32_t>(instruction.rawPayload, 3);
            const std::optional<int32_t> y = readPayloadValue<int32_t>(instruction.rawPayload, 7);
            const std::optional<int32_t> z = readPayloadValue<int32_t>(instruction.rawPayload, 11);
            const std::optional<uint32_t> group = readPayloadValue<uint32_t>(instruction.rawPayload, 15);
            const std::optional<uint32_t> uniqueNameId = readPayloadValue<uint32_t>(instruction.rawPayload, 19);
            stream << " {TypeIndexInMapStats=" << (typeIndex ? static_cast<unsigned>(*typeIndex) : 0)
                   << " Level=" << (level ? static_cast<unsigned>(*level) : 0)
                   << " Count=" << (count ? static_cast<unsigned>(*count) : 0)
                   << " X=" << (x ? *x : 0)
                   << " Y=" << (y ? *y : 0)
                   << " Z=" << (z ? *z : 0)
                   << " NPCGroup=" << (group ? *group : 0)
                   << " UniqueNameId=" << (uniqueNameId ? *uniqueNameId : 0)
                   << "}";
            break;
        }

        case EvtOpcode::ChangeDoorState:
            stream << " {Id=" << (instruction.value1 ? *instruction.value1 : 0)
                   << " Action=" << formatDoorAction(instruction.value2 ? *instruction.value2 : 0) << "}";
            break;

        case EvtOpcode::StopAnimation:
            stream << " {Id=" << (instruction.value1 ? *instruction.value1 : 0) << "}";
            break;

        case EvtOpcode::ToggleIndoorLight:
            stream << " {Id=" << (instruction.value1 ? *instruction.value1 : 0)
                   << " On=" << (instruction.booleanValue ? static_cast<unsigned>(*instruction.booleanValue) : 0)
                   << "}";
            break;

        case EvtOpcode::InputString:
            stream << " {Question=" << (instruction.value1 ? *instruction.value1 : 0)
                   << " Answer1=" << (instruction.value2 ? *instruction.value2 : 0)
                   << " Answer2=" << (instruction.value3 ? *instruction.value3 : 0)
                   << " jump(ok)="
                   << (instruction.targetStep ? static_cast<unsigned>(*instruction.targetStep) : 0)
                   << "}";
            break;

        case EvtOpcode::SetFacesBit:
        case EvtOpcode::ToggleActorFlag:
        case EvtOpcode::SetNpcGroupNews:
        case EvtOpcode::ToggleActorGroupFlag:
        case EvtOpcode::ToggleChestFlag:
            stream << " {A=" << (instruction.value1 ? *instruction.value1 : 0)
                   << " B=" << (instruction.value2 ? *instruction.value2 : 0)
                   << " On=" << (instruction.booleanValue ? static_cast<unsigned>(*instruction.booleanValue) : 0)
                   << "}";
            break;

        case EvtOpcode::SetNpcTopic:
            stream << " {NPC=" << (instruction.value1 ? *instruction.value1 : 0)
                   << " Index=" << (instruction.value2 ? *instruction.value2 : 0)
                   << " Event=" << (instruction.value3 ? *instruction.value3 : 0)
                   << "}";
            break;

        case EvtOpcode::IsActorKilled:
        case EvtOpcode::CanShowTopicIsActorKilled:
        {
            const std::optional<uint8_t> policy = readPayloadValue<uint8_t>(instruction.rawPayload, 0);
            const std::optional<uint32_t> param = readPayloadValue<uint32_t>(instruction.rawPayload, 1);
            const std::optional<uint8_t> count = readPayloadValue<uint8_t>(instruction.rawPayload, 5);
            const std::optional<uint8_t> invisibleAsDead = readPayloadValue<uint8_t>(instruction.rawPayload, 6);
            const std::optional<uint8_t> jump = readPayloadValue<uint8_t>(instruction.rawPayload, 7);
            stream << " {CheckType=" << (policy ? static_cast<unsigned>(*policy) : 0)
                   << " Id=" << (param ? *param : 0)
                   << " Count=" << (count ? static_cast<unsigned>(*count) : 0)
                   << " InvisibleAsDead=" << (invisibleAsDead ? static_cast<unsigned>(*invisibleAsDead) : 0);

            if (jump)
            {
                stream << " jump=" << static_cast<unsigned>(*jump);
            }

            stream << "}";
            break;
        }

        case EvtOpcode::RandomGoTo:
        case EvtOpcode::OnTimer:
        case EvtOpcode::OnLongTimer:
            stream << " {";

            for (size_t index = 0; index < instruction.listValues.size(); ++index)
            {
                if (index > 0)
                {
                    stream << ",";
                }

                stream << static_cast<unsigned>(instruction.listValues[index]);
            }

            stream << "}";
            break;

        default:
            if (!instruction.rawPayload.empty())
            {
                stream << " {raw=" << instruction.rawPayload.size() << " bytes}";
            }
            else
            {
                stream << " {}";
            }
            break;
    }

    return stream.str();
}
}
