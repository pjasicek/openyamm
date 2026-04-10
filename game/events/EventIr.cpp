#include "game/events/EventIr.h"

#include <algorithm>
#include <cstring>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
template <typename TValue>
std::optional<TValue> readPayloadValue(const std::vector<uint8_t> &payload, size_t offset)
{
    TValue value = {};

    if (offset > payload.size() || sizeof(TValue) > (payload.size() - offset))
    {
        return std::nullopt;
    }

    std::memcpy(&value, payload.data() + offset, sizeof(TValue));
    return value;
}

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
    const EvtVariable variableId = static_cast<EvtVariable>(rawValue & 0xFFFFu);
    const uint32_t index = rawValue >> 16;

    if (variableId == EvtVariable::QBits)
    {
        return "QBits[" + std::to_string(index) + "]";
    }

    if (variableId == EvtVariable::Inventory)
    {
        return "Inventory[" + std::to_string(index) + "]";
    }

    if (variableId == EvtVariable::Awards)
    {
        return "Awards[" + std::to_string(index) + "]";
    }

    if (variableId >= EvtVariable::MapPersistentVariableBegin && variableId <= EvtVariable::MapPersistentVariableEnd)
    {
        return "MapVar[" + std::to_string(static_cast<uint32_t>(variableId) -
            static_cast<uint32_t>(EvtVariable::MapPersistentVariableBegin)) + "]";
    }

    if (variableId >= EvtVariable::MapPersistentDecorVariableBegin
        && variableId <= EvtVariable::MapPersistentDecorVariableEnd)
    {
        return "DecorVar[" + std::to_string(static_cast<uint32_t>(variableId) -
            static_cast<uint32_t>(EvtVariable::MapPersistentDecorVariableBegin)) + "]";
    }

    if (variableId >= EvtVariable::UnknownTimeEventBegin && variableId <= EvtVariable::UnknownTimeEventEnd)
    {
        return "UnknownTimeEvent[" + std::to_string(static_cast<uint32_t>(variableId) -
            static_cast<uint32_t>(EvtVariable::UnknownTimeEventBegin)) + "]";
    }

    if (variableId >= EvtVariable::HistoryBegin && variableId <= EvtVariable::HistoryEnd)
    {
        return "History[" + std::to_string(static_cast<uint32_t>(variableId) -
            static_cast<uint32_t>(EvtVariable::HistoryBegin)) + "]";
    }

    switch (variableId)
    {
        case EvtVariable::Sex: return "Sex";
        case EvtVariable::ClassId: return "Class";
        case EvtVariable::CurrentHealth: return "CurrentHP";
        case EvtVariable::MaxHealth: return "MaxHP";
        case EvtVariable::CurrentSpellPoints: return "CurrentSP";
        case EvtVariable::MaxSpellPoints: return "MaxSP";
        case EvtVariable::ActualArmorClass: return "ActualAC";
        case EvtVariable::ArmorClassBonus: return "ACModifier";
        case EvtVariable::BaseLevel: return "BaseLevel";
        case EvtVariable::LevelBonus: return "LevelModifier";
        case EvtVariable::Age: return "Age";
        case EvtVariable::Experience: return "Experience";
        case EvtVariable::Race: return "Race";
        case EvtVariable::Hour: return "Hour";
        case EvtVariable::DayOfYear: return "DayOfYear";
        case EvtVariable::DayOfWeek: return "DayOfWeek";
        case EvtVariable::Gold:
        case EvtVariable::RandomGold: return "Gold";
        case EvtVariable::Food:
        case EvtVariable::RandomFood: return "Food";
        case EvtVariable::MightBonus: return "MightBonus";
        case EvtVariable::IntellectBonus: return "IntellectBonus";
        case EvtVariable::PersonalityBonus: return "PersonalityBonus";
        case EvtVariable::EnduranceBonus: return "EnduranceBonus";
        case EvtVariable::SpeedBonus: return "SpeedBonus";
        case EvtVariable::AccuracyBonus: return "AccuracyBonus";
        case EvtVariable::LuckBonus: return "LuckBonus";
        case EvtVariable::BaseMight: return "BaseMight";
        case EvtVariable::BaseIntellect: return "BaseIntellect";
        case EvtVariable::BasePersonality: return "BasePersonality";
        case EvtVariable::BaseEndurance: return "BaseEndurance";
        case EvtVariable::BaseSpeed: return "BaseSpeed";
        case EvtVariable::BaseAccuracy: return "BaseAccuracy";
        case EvtVariable::BaseLuck: return "BaseLuck";
        case EvtVariable::ActualMight: return "ActualMight";
        case EvtVariable::ActualIntellect: return "ActualIntellect";
        case EvtVariable::ActualPersonality: return "ActualPersonality";
        case EvtVariable::ActualEndurance: return "ActualEndurance";
        case EvtVariable::ActualSpeed: return "ActualSpeed";
        case EvtVariable::ActualAccuracy: return "ActualAccuracy";
        case EvtVariable::ActualLuck: return "ActualLuck";
        case EvtVariable::FireResistance: return "FireResistance";
        case EvtVariable::AirResistance: return "AirResistance";
        case EvtVariable::WaterResistance: return "WaterResistance";
        case EvtVariable::EarthResistance: return "EarthResistance";
        case EvtVariable::SpiritResistance: return "SpiritResistance";
        case EvtVariable::MindResistance: return "MindResistance";
        case EvtVariable::BodyResistance: return "BodyResistance";
        case EvtVariable::LightResistance: return "LightResistance";
        case EvtVariable::DarkResistance: return "DarkResistance";
        case EvtVariable::PhysicalResistance: return "PhysicalResistance";
        case EvtVariable::MagicResistance: return "MagicResistance";
        case EvtVariable::FireResistanceBonus: return "FireResistanceBonus";
        case EvtVariable::AirResistanceBonus: return "AirResistanceBonus";
        case EvtVariable::WaterResistanceBonus: return "WaterResistanceBonus";
        case EvtVariable::EarthResistanceBonus: return "EarthResistanceBonus";
        case EvtVariable::SpiritResistanceBonus: return "SpiritResistanceBonus";
        case EvtVariable::MindResistanceBonus: return "MindResistanceBonus";
        case EvtVariable::BodyResistanceBonus: return "BodyResistanceBonus";
        case EvtVariable::LightResistanceBonus: return "LightResistanceBonus";
        case EvtVariable::DarkResistanceBonus: return "DarkResistanceBonus";
        case EvtVariable::PhysicalResistanceBonus: return "PhysicalResistanceBonus";
        case EvtVariable::MagicResistanceBonus: return "MagicResistanceBonus";
        case EvtVariable::AutoNotes: return "AutoNotes";
        case EvtVariable::IsMightMoreThanBase: return "IsMightMoreThanBase";
        case EvtVariable::IsIntellectMoreThanBase: return "IsIntellectMoreThanBase";
        case EvtVariable::IsPersonalityMoreThanBase: return "IsPersonalityMoreThanBase";
        case EvtVariable::IsEnduranceMoreThanBase: return "IsEnduranceMoreThanBase";
        case EvtVariable::IsSpeedMoreThanBase: return "IsSpeedMoreThanBase";
        case EvtVariable::IsAccuracyMoreThanBase: return "IsAccuracyMoreThanBase";
        case EvtVariable::IsLuckMoreThanBase: return "IsLuckMoreThanBase";
        case EvtVariable::PlayerBits: return "PlayerBits";
        case EvtVariable::Npcs2: return "NPCs2";
        case EvtVariable::IsFlying: return "IsFlying";
        case EvtVariable::HiredNpcHasSpeciality: return "HiredNPCHasSpeciality";
        case EvtVariable::CircusPrises: return "CircusPrises";
        case EvtVariable::NumSkillPoints: return "NumSkillPoints";
        case EvtVariable::MonthIs: return "MonthIs";
        case EvtVariable::Counter1: return "Counter1";
        case EvtVariable::Counter2: return "Counter2";
        case EvtVariable::Counter3: return "Counter3";
        case EvtVariable::Counter4: return "Counter4";
        case EvtVariable::Counter5: return "Counter5";
        case EvtVariable::Counter6: return "Counter6";
        case EvtVariable::Counter7: return "Counter7";
        case EvtVariable::Counter8: return "Counter8";
        case EvtVariable::Counter9: return "Counter9";
        case EvtVariable::Counter10: return "Counter10";
        case EvtVariable::ReputationInCurrentLocation: return "ReputationInCurrentLocation";
        case EvtVariable::Unknown1: return "Unknown1";
        case EvtVariable::GoldInBank: return "GoldInBank";
        case EvtVariable::NumDeaths: return "NumDeaths";
        case EvtVariable::NumBounties: return "NumBounties";
        case EvtVariable::PrisonTerms: return "PrisonTerms";
        case EvtVariable::ArenaWinsPage: return "ArenaWinsPage";
        case EvtVariable::ArenaWinsSquire: return "ArenaWinsSquire";
        case EvtVariable::ArenaWinsKnight: return "ArenaWinsKnight";
        case EvtVariable::ArenaWinsLord: return "ArenaWinsLord";
        case EvtVariable::Invisible: return "Invisible";
        case EvtVariable::ItemEquipped: return "ItemEquipped";
        case EvtVariable::Players: return "Players[" + std::to_string(index) + "]";
        default: break;
    }

    std::ostringstream stream;
    stream << "Var(tag=" << hexValue(static_cast<uint32_t>(variableId)) << ", index=" << index << ")";
    return stream.str();
}

std::string decodeFacetBit(uint32_t rawValue)
{
    switch (static_cast<EvtFaceAttribute>(rawValue))
    {
        case EvtFaceAttribute::Invisible: return "Invisible";
        case EvtFaceAttribute::HasHint: return "Hint";
        case EvtFaceAttribute::Clickable: return "Clickable";
        case EvtFaceAttribute::PressurePlate: return "PressurePlate";
        case EvtFaceAttribute::Untouchable: return "Untouchable";
        default: return hexValue(rawValue);
    }
}

std::string decodeActorBit(uint32_t rawValue)
{
    switch (static_cast<EvtActorAttribute>(rawValue))
    {
        case EvtActorAttribute::Invisible: return "Invisible";
        case EvtActorAttribute::FullAi: return "FullAI";
        case EvtActorAttribute::Active: return "Active";
        case EvtActorAttribute::Nearby: return "Nearby";
        case EvtActorAttribute::Fleeing: return "Fleeing";
        case EvtActorAttribute::Aggressor: return "Aggressor";
        case EvtActorAttribute::HasItem: return "HasItem";
        case EvtActorAttribute::Hostile: return "Hostile";
        default: return hexValue(rawValue);
    }
}
}

EventIrProgram EventIrProgram::fromEvents(std::vector<EventIrEvent> events)
{
    EventIrProgram program = {};
    program.m_events = std::move(events);
    return program;
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
        case EvtOpcode::PlaySound: return EventIrOperation::PlaySound;
        case EvtOpcode::LocationName: return EventIrOperation::LocationName;
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
        case EvtOpcode::ShowFace: return EventIrOperation::ShowFace;
        case EvtOpcode::ReceiveDamage: return EventIrOperation::ReceiveDamage;
        case EvtOpcode::SetSnow: return EventIrOperation::SetSnow;
        case EvtOpcode::ShowMovie: return EventIrOperation::ShowMovie;
        case EvtOpcode::SetSprite: return EventIrOperation::SetSprite;
        case EvtOpcode::ChangeDoorState: return EventIrOperation::ChangeDoorState;
        case EvtOpcode::StopAnimation: return EventIrOperation::StopAnimation;
        case EvtOpcode::SetTexture: return EventIrOperation::SetTexture;
        case EvtOpcode::ToggleIndoorLight: return EventIrOperation::ToggleIndoorLight;
        case EvtOpcode::SetFacesBit: return EventIrOperation::SetFacetBit;
        case EvtOpcode::ToggleActorFlag: return EventIrOperation::SetActorFlag;
        case EvtOpcode::ToggleActorGroupFlag: return EventIrOperation::SetActorGroupFlag;
        case EvtOpcode::SetActorGroup: return EventIrOperation::SetActorGroup;
        case EvtOpcode::SetNpcTopic: return EventIrOperation::SetNpcTopic;
        case EvtOpcode::SetNpcGroupNews: return EventIrOperation::SetNpcGroupNews;
        case EvtOpcode::SetNpcGreeting: return EventIrOperation::SetNpcGreeting;
        case EvtOpcode::NpcSetItem: return EventIrOperation::SetNpcItem;
        case EvtOpcode::SetActorItem: return EventIrOperation::SetActorItem;
        case EvtOpcode::CharacterAnimation: return EventIrOperation::CharacterAnimation;
        case EvtOpcode::ForPartyMember: return EventIrOperation::ForPartyMember;
        case EvtOpcode::CheckItemsCount: return EventIrOperation::CheckItemsCount;
        case EvtOpcode::RemoveItems: return EventIrOperation::RemoveItems;
        case EvtOpcode::CheckSkill: return EventIrOperation::CheckSkill;
        case EvtOpcode::IsActorKilled: return EventIrOperation::IsActorKilled;
        case EvtOpcode::CanShowTopicIsActorKilled: return EventIrOperation::IsActorKilledCanShowTopic;
        case EvtOpcode::ChangeGroup: return EventIrOperation::ChangeGroup;
        case EvtOpcode::ChangeGroupAlly: return EventIrOperation::ChangeGroupAlly;
        case EvtOpcode::CheckSeason: return EventIrOperation::CheckSeason;
        case EvtOpcode::ToggleChestFlag: return EventIrOperation::ToggleChestFlag;
        case EvtOpcode::InputString: return EventIrOperation::InputString;
        case EvtOpcode::PressAnyKey: return EventIrOperation::PressAnyKey;
        case EvtOpcode::SpecialJump: return EventIrOperation::SpecialJump;
        case EvtOpcode::IsTotalBountyHuntingAwardInRange:
            return EventIrOperation::IsTotalBountyHuntingAwardInRange;
        case EvtOpcode::IsNpcInParty: return EventIrOperation::IsNpcInParty;
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
        case EventIrOperation::PlaySound: return "PlaySound";
        case EventIrOperation::LocationName: return "LocationName";
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
        case EventIrOperation::ShowFace: return "ShowFace";
        case EventIrOperation::ReceiveDamage: return "ReceiveDamage";
        case EventIrOperation::SetSnow: return "SetSnow";
        case EventIrOperation::ShowMovie: return "ShowMovie";
        case EventIrOperation::SetSprite: return "SetSprite";
        case EventIrOperation::ChangeDoorState: return "ChangeMechanismState";
        case EventIrOperation::StopAnimation: return "StopMechanism";
        case EventIrOperation::SetTexture: return "SetTexture";
        case EventIrOperation::ToggleIndoorLight: return "ToggleIndoorLight";
        case EventIrOperation::SetFacetBit: return "SetFacetBit";
        case EventIrOperation::SetActorFlag: return "SetActorFlag";
        case EventIrOperation::SetActorGroupFlag: return "SetActorGroupFlag";
        case EventIrOperation::SetActorGroup: return "SetActorGroup";
        case EventIrOperation::SetNpcTopic: return "SetNpcTopic";
        case EventIrOperation::SetNpcGroupNews: return "SetNpcGroupNews";
        case EventIrOperation::SetNpcGreeting: return "SetNpcGreeting";
        case EventIrOperation::SetNpcItem: return "SetNpcItem";
        case EventIrOperation::SetActorItem: return "SetActorItem";
        case EventIrOperation::CharacterAnimation: return "CharacterAnimation";
        case EventIrOperation::ForPartyMember: return "ForPartyMember";
        case EventIrOperation::CheckItemsCount: return "CheckItemsCount";
        case EventIrOperation::RemoveItems: return "RemoveItems";
        case EventIrOperation::CheckSkill: return "CheckSkill";
        case EventIrOperation::IsActorKilled: return "IsActorKilled";
        case EventIrOperation::IsActorKilledCanShowTopic: return "IsActorKilledCanShowTopic";
        case EventIrOperation::ChangeGroup: return "ChangeGroup";
        case EventIrOperation::ChangeGroupAlly: return "ChangeGroupAlly";
        case EventIrOperation::CheckSeason: return "CheckSeason";
        case EventIrOperation::ToggleChestFlag: return "ToggleChestFlag";
        case EventIrOperation::InputString: return "InputString";
        case EventIrOperation::PressAnyKey: return "PressAnyKey";
        case EventIrOperation::SpecialJump: return "SpecialJump";
        case EventIrOperation::IsTotalBountyHuntingAwardInRange: return "IsTotalBountyHuntingAwardInRange";
        case EventIrOperation::IsNpcInParty: return "IsNpcInParty";
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
        std::optional<std::string> text;

        if (*evtInstruction.value1 <= 0xffu)
        {
            text = strTable.get(static_cast<uint8_t>(*evtInstruction.value1));
        }

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

    if (irInstruction.operation == EventIrOperation::ForPartyMember)
    {
        for (uint8_t value : evtInstruction.listValues)
        {
            irInstruction.arguments.push_back(value);
        }
    }
    else if (irInstruction.operation == EventIrOperation::RandomJump)
    {
        for (uint8_t value : evtInstruction.listValues)
        {
            if (value != 0)
            {
                irInstruction.arguments.push_back(value);
            }
        }
    }

    if (irInstruction.operation == EventIrOperation::SummonMonsters)
    {
        const std::optional<uint8_t> typeIndex = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 0);
        const std::optional<uint8_t> level = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 1);
        const std::optional<uint8_t> count = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 2);
        const std::optional<int32_t> x = readPayloadValue<int32_t>(evtInstruction.rawPayload, 3);
        const std::optional<int32_t> y = readPayloadValue<int32_t>(evtInstruction.rawPayload, 7);
        const std::optional<int32_t> z = readPayloadValue<int32_t>(evtInstruction.rawPayload, 11);
        const std::optional<uint32_t> group = readPayloadValue<uint32_t>(evtInstruction.rawPayload, 15);
        const std::optional<uint32_t> uniqueNameId = readPayloadValue<uint32_t>(evtInstruction.rawPayload, 19);

        if (typeIndex && level && count && x && y && z && group && uniqueNameId)
        {
            irInstruction.arguments.clear();
            irInstruction.arguments.push_back(*typeIndex);
            irInstruction.arguments.push_back(*level);
            irInstruction.arguments.push_back(*count);
            irInstruction.arguments.push_back(static_cast<uint32_t>(*x));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*y));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*z));
            irInstruction.arguments.push_back(*group);
            irInstruction.arguments.push_back(*uniqueNameId);
        }
    }
    else if (irInstruction.operation == EventIrOperation::SummonItem)
    {
        const std::optional<uint32_t> objectId = readPayloadValue<uint32_t>(evtInstruction.rawPayload, 0);
        const std::optional<int32_t> x = readPayloadValue<int32_t>(evtInstruction.rawPayload, 4);
        const std::optional<int32_t> y = readPayloadValue<int32_t>(evtInstruction.rawPayload, 8);
        const std::optional<int32_t> z = readPayloadValue<int32_t>(evtInstruction.rawPayload, 12);
        const std::optional<int32_t> speed = readPayloadValue<int32_t>(evtInstruction.rawPayload, 16);
        const std::optional<uint8_t> count = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 20);
        const std::optional<uint8_t> randomRotate = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 21);

        if (objectId && x && y && z && speed && count && randomRotate)
        {
            irInstruction.arguments.clear();
            irInstruction.arguments.push_back(*objectId);
            irInstruction.arguments.push_back(static_cast<uint32_t>(*x));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*y));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*z));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*speed));
            irInstruction.arguments.push_back(*count);
            irInstruction.arguments.push_back(*randomRotate);
        }
    }
    else if (irInstruction.operation == EventIrOperation::IsActorKilled)
    {
        const std::optional<uint8_t> policy = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 0);
        const std::optional<uint32_t> param = readPayloadValue<uint32_t>(evtInstruction.rawPayload, 1);
        const std::optional<uint8_t> count = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 5);
        const std::optional<uint8_t> invisibleAsDead = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 6);
        const std::optional<uint8_t> jump = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 7);

        if (policy && param && count && invisibleAsDead)
        {
            irInstruction.arguments.clear();
            irInstruction.arguments.push_back(*policy);
            irInstruction.arguments.push_back(*param);
            irInstruction.arguments.push_back(*count);
            irInstruction.arguments.push_back(*invisibleAsDead);
        }

        if (jump)
        {
            irInstruction.jumpTargetStep = *jump;
        }
    }
    else if (irInstruction.operation == EventIrOperation::IsActorKilledCanShowTopic)
    {
        const std::optional<uint8_t> policy = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 0);
        const std::optional<uint32_t> param = readPayloadValue<uint32_t>(evtInstruction.rawPayload, 1);
        const std::optional<uint8_t> count = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 5);
        const std::optional<uint8_t> invisibleAsDead = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 6);
        const std::optional<uint8_t> jump = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 7);

        if (policy && param && count && invisibleAsDead)
        {
            irInstruction.arguments.clear();
            irInstruction.arguments.push_back(*policy);
            irInstruction.arguments.push_back(*param);
            irInstruction.arguments.push_back(*count);
            irInstruction.arguments.push_back(*invisibleAsDead);
        }

        if (jump)
        {
            irInstruction.jumpTargetStep = *jump;
        }
    }
    else if (irInstruction.operation == EventIrOperation::CastSpell)
    {
        const std::optional<uint8_t> spellId = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 0);
        const std::optional<uint8_t> skillMasteryRaw = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 1);
        const std::optional<uint8_t> skillLevel = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 2);
        const std::optional<int32_t> fromX = readPayloadValue<int32_t>(evtInstruction.rawPayload, 3);
        const std::optional<int32_t> fromY = readPayloadValue<int32_t>(evtInstruction.rawPayload, 7);
        const std::optional<int32_t> fromZ = readPayloadValue<int32_t>(evtInstruction.rawPayload, 11);
        const std::optional<int32_t> toX = readPayloadValue<int32_t>(evtInstruction.rawPayload, 15);
        const std::optional<int32_t> toY = readPayloadValue<int32_t>(evtInstruction.rawPayload, 19);
        const std::optional<int32_t> toZ = readPayloadValue<int32_t>(evtInstruction.rawPayload, 23);

        if (spellId && skillLevel && skillMasteryRaw && fromX && fromY && fromZ && toX && toY && toZ)
        {
            irInstruction.arguments.clear();
            irInstruction.arguments.push_back(*spellId);
            irInstruction.arguments.push_back(*skillLevel);
            irInstruction.arguments.push_back(static_cast<uint32_t>(*skillMasteryRaw) + 1);
            irInstruction.arguments.push_back(static_cast<uint32_t>(*fromX));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*fromY));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*fromZ));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*toX));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*toY));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*toZ));
        }
    }
    else if (irInstruction.operation == EventIrOperation::MoveToMap)
    {
        const std::optional<int32_t> x = readPayloadValue<int32_t>(evtInstruction.rawPayload, 0);
        const std::optional<int32_t> y = readPayloadValue<int32_t>(evtInstruction.rawPayload, 4);
        const std::optional<int32_t> z = readPayloadValue<int32_t>(evtInstruction.rawPayload, 8);
        const std::optional<int32_t> yaw = readPayloadValue<int32_t>(evtInstruction.rawPayload, 12);
        const std::optional<int32_t> pitch = readPayloadValue<int32_t>(evtInstruction.rawPayload, 16);
        const std::optional<int32_t> zSpeed = readPayloadValue<int32_t>(evtInstruction.rawPayload, 20);
        const std::optional<uint8_t> houseId = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 24);
        const std::optional<uint8_t> exitPicId = readPayloadValue<uint8_t>(evtInstruction.rawPayload, 25);

        if (x && y && z && yaw && pitch && zSpeed && houseId && exitPicId)
        {
            irInstruction.arguments.clear();
            irInstruction.arguments.push_back(static_cast<uint32_t>(*x));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*y));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*z));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*yaw));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*pitch));
            irInstruction.arguments.push_back(static_cast<uint32_t>(*zSpeed));
            irInstruction.arguments.push_back(*houseId);
            irInstruction.arguments.push_back(*exitPicId);
        }
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

        case EventIrOperation::SummonMonsters:
        {
            if (irInstruction.arguments.size() >= 8)
            {
                std::ostringstream note;
                note << "type=" << irInstruction.arguments[0]
                     << " level=" << irInstruction.arguments[1]
                     << " count=" << irInstruction.arguments[2]
                     << " pos=("
                     << static_cast<int32_t>(irInstruction.arguments[3]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[4]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[5]) << ")"
                     << " group=" << irInstruction.arguments[6]
                     << " unique=" << irInstruction.arguments[7];
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::SummonItem:
        {
            if (irInstruction.arguments.size() >= 7)
            {
                std::ostringstream note;
                note << "object=" << irInstruction.arguments[0]
                     << " pos=("
                     << static_cast<int32_t>(irInstruction.arguments[1]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[2]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[3]) << ")"
                     << " speed=" << static_cast<int32_t>(irInstruction.arguments[4])
                     << " count=" << irInstruction.arguments[5]
                     << " randomRotate=" << irInstruction.arguments[6];
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::CastSpell:
        {
            if (irInstruction.arguments.size() >= 9)
            {
                std::ostringstream note;
                note << "spell=" << irInstruction.arguments[0]
                     << " skill=" << irInstruction.arguments[1]
                     << " mastery=" << irInstruction.arguments[2]
                     << " from=("
                     << static_cast<int32_t>(irInstruction.arguments[3]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[4]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[5]) << ")"
                     << " to=("
                     << static_cast<int32_t>(irInstruction.arguments[6]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[7]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[8]) << ")";
                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::MoveToMap:
        {
            if (irInstruction.arguments.size() >= 8)
            {
                std::ostringstream note;
                note << "pos=("
                     << static_cast<int32_t>(irInstruction.arguments[0]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[1]) << ","
                     << static_cast<int32_t>(irInstruction.arguments[2]) << ")"
                     << " yaw=" << static_cast<int32_t>(irInstruction.arguments[3])
                     << " pitch=" << static_cast<int32_t>(irInstruction.arguments[4])
                     << " zspeed=" << static_cast<int32_t>(irInstruction.arguments[5])
                     << " house=" << irInstruction.arguments[6]
                     << " exit=" << irInstruction.arguments[7];

                if (irInstruction.text && !irInstruction.text->empty())
                {
                    note << " map=" << quote(*irInstruction.text);
                }

                irInstruction.note = note.str();
            }
            break;
        }

        case EventIrOperation::IsActorKilled:
        case EventIrOperation::IsActorKilledCanShowTopic:
        {
            if (irInstruction.arguments.size() >= 4)
            {
                std::ostringstream note;
                note << "checkType=" << irInstruction.arguments[0]
                     << " id=" << irInstruction.arguments[1]
                     << " count=" << irInstruction.arguments[2]
                     << " invisibleAsDead=" << irInstruction.arguments[3];
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
