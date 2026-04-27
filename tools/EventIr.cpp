#include "tools/EventIr.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <exception>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
template <typename TValue>
bool readRequiredScalar(const YAML::Node &node, const char *pKey, TValue &value)
{
    const YAML::Node child = node[pKey];

    if (!child || !child.IsScalar())
    {
        return false;
    }

    try
    {
        value = child.as<TValue>();
        return true;
    }
    catch (const std::exception &)
    {
        return false;
    }
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
    uint32_t variableTag = rawValue & 0xFFFFu;
    if (variableTag == 0x013Cu)
    {
        variableTag = static_cast<uint32_t>(EvtVariable::Invisible);
    }
    else if (variableTag == 0x013Du)
    {
        variableTag = static_cast<uint32_t>(EvtVariable::ItemEquipped);
    }

    const EvtVariable variableId = static_cast<EvtVariable>(variableTag);
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
        case EvtFaceAttribute::HasHint: return "HasHint";
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

std::string EventIrProgram::saveToYamlText() const
{
    YAML::Emitter emitter;
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "version" << YAML::Value << 1;
    emitter << YAML::Key << "events" << YAML::Value << YAML::BeginSeq;

    for (const EventIrEvent &event : m_events)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "event_id" << YAML::Value << event.eventId;
        emitter << YAML::Key << "instructions" << YAML::Value << YAML::BeginSeq;

        for (const EventIrInstruction &instruction : event.instructions)
        {
            emitter << YAML::BeginMap;
            emitter << YAML::Key << "step" << YAML::Value << static_cast<uint32_t>(instruction.step);
            emitter << YAML::Key << "operation" << YAML::Value << static_cast<uint32_t>(instruction.operation);
            emitter << YAML::Key << "source_opcode" << YAML::Value << static_cast<uint32_t>(instruction.sourceOpcode);
            emitter << YAML::Key << "arguments" << YAML::Value << YAML::BeginSeq;

            for (uint32_t argument : instruction.arguments)
            {
                emitter << argument;
            }

            emitter << YAML::EndSeq;

            if (instruction.jumpTargetStep.has_value())
            {
                emitter << YAML::Key << "jump_target_step"
                        << YAML::Value << static_cast<uint32_t>(*instruction.jumpTargetStep);
            }

            if (instruction.text.has_value())
            {
                emitter << YAML::Key << "text" << YAML::Value << *instruction.text;
            }

            if (instruction.note.has_value())
            {
                emitter << YAML::Key << "note" << YAML::Value << *instruction.note;
            }

            emitter << YAML::EndMap;
        }

        emitter << YAML::EndSeq;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;
    return emitter.c_str();
}

bool EventIrProgram::loadFromYamlText(const std::string &text, std::string &error)
{
    m_events.clear();

    try
    {
        const YAML::Node root = YAML::Load(text);
        const YAML::Node eventsNode = root["events"];

        if (!eventsNode || !eventsNode.IsSequence())
        {
            error = "missing or invalid events sequence";
            return false;
        }

        for (const YAML::Node &eventNode : eventsNode)
        {
            uint16_t eventId = 0;

            if (!readRequiredScalar(eventNode, "event_id", eventId))
            {
                error = "event is missing event_id";
                return false;
            }

            const YAML::Node instructionsNode = eventNode["instructions"];

            if (!instructionsNode || !instructionsNode.IsSequence())
            {
                error = "event is missing instructions sequence";
                return false;
            }

            EventIrEvent event = {};
            event.eventId = eventId;

            for (const YAML::Node &instructionNode : instructionsNode)
            {
                uint32_t step = 0;
                uint32_t operation = 0;
                uint32_t sourceOpcode = 0;

                if (!readRequiredScalar(instructionNode, "step", step)
                    || !readRequiredScalar(instructionNode, "operation", operation)
                    || !readRequiredScalar(instructionNode, "source_opcode", sourceOpcode))
                {
                    error = "instruction is missing required scalar fields";
                    return false;
                }

                EventIrInstruction instruction = {};
                instruction.eventId = event.eventId;
                instruction.step = static_cast<uint8_t>(step);
                instruction.operation = static_cast<EventIrOperation>(operation);
                instruction.sourceOpcode = sourceOpcode;

                const YAML::Node argumentsNode = instructionNode["arguments"];

                if (argumentsNode)
                {
                    if (!argumentsNode.IsSequence())
                    {
                        error = "instruction arguments must be a sequence";
                        return false;
                    }

                    for (const YAML::Node &argumentNode : argumentsNode)
                    {
                        instruction.arguments.push_back(argumentNode.as<uint32_t>());
                    }
                }

                const YAML::Node jumpTargetNode = instructionNode["jump_target_step"];

                if (jumpTargetNode)
                {
                    instruction.jumpTargetStep = jumpTargetNode.as<uint8_t>();
                }

                const YAML::Node textNode = instructionNode["text"];

                if (textNode)
                {
                    instruction.text = textNode.as<std::string>();
                }

                const YAML::Node noteNode = instructionNode["note"];

                if (noteNode)
                {
                    instruction.note = noteNode.as<std::string>();
                }

                event.instructions.push_back(std::move(instruction));
            }

            m_events.push_back(std::move(event));
        }
    }
    catch (const std::exception &exception)
    {
        error = exception.what();
        m_events.clear();
        return false;
    }

    return true;
}

const EventIrEvent *EventIrProgram::findEvent(uint16_t eventId) const
{
    const auto eventIt = std::find_if(
        m_events.begin(),
        m_events.end(),
        [eventId](const EventIrEvent &event)
        {
            return event.eventId == eventId;
        });

    if (eventIt == m_events.end())
    {
        return nullptr;
    }

    return &(*eventIt);
}

bool EventIrProgram::hasEvent(uint16_t eventId) const
{
    return findEvent(eventId) != nullptr;
}

std::optional<std::string> EventIrProgram::getHint(uint16_t eventId) const
{
    const EventIrEvent *pEvent = findEvent(eventId);

    if (pEvent == nullptr)
    {
        return std::nullopt;
    }

    bool mouseOverFound = false;

    for (const EventIrInstruction &instruction : pEvent->instructions)
    {
        if (instruction.operation == EventIrOperation::TriggerMouseOver)
        {
            mouseOverFound = true;

            if (instruction.text && !instruction.text->empty())
            {
                return instruction.text;
            }
        }

        if (mouseOverFound
            && instruction.operation == EventIrOperation::SpeakInHouse
            && instruction.text
            && !instruction.text->empty())
        {
            return instruction.text;
        }
    }

    return std::nullopt;
}

std::optional<std::string> EventIrProgram::summarizeEvent(uint16_t eventId) const
{
    const EventIrEvent *pEvent = findEvent(eventId);

    if (pEvent == nullptr)
    {
        return std::nullopt;
    }

    std::ostringstream stream;
    stream << eventId << ":";

    const std::optional<std::string> hint = getHint(eventId);

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

        stream << operationName(pEvent->instructions[instructionIndex].operation);
    }

    if (pEvent->instructions.size() > instructionCount)
    {
        stream << ",...";
    }

    return stream.str();
}

std::vector<uint32_t> EventIrProgram::getOpenedChestIds(uint16_t eventId) const
{
    std::vector<uint32_t> chestIds;
    const EventIrEvent *pEvent = findEvent(eventId);

    if (pEvent == nullptr)
    {
        return chestIds;
    }

    for (const EventIrInstruction &instruction : pEvent->instructions)
    {
        if (instruction.operation != EventIrOperation::OpenChest || instruction.arguments.empty())
        {
            continue;
        }

        chestIds.push_back(instruction.arguments[0]);
    }

    return chestIds;
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

void EventIrProgram::setLuaSource(std::string chunkText, std::string chunkName)
{
    m_luaSourceText = std::move(chunkText);
    m_luaSourceName = std::move(chunkName);
}

const std::optional<std::string> &EventIrProgram::luaSourceText() const
{
    return m_luaSourceText;
}

const std::optional<std::string> &EventIrProgram::luaSourceName() const
{
    return m_luaSourceName;
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

}
