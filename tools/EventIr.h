#pragma once

#include "game/events/EvtEnums.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class EventIrOperation
{
    Unknown,
    Exit,
    TriggerMouseOver,
    TriggerOnLoadMap,
    TriggerOnLeaveMap,
    TriggerOnTimer,
    TriggerOnLongTimer,
    TriggerOnDateTimer,
    EnableDateTimer,
    PlaySound,
    LocationName,
    Compare,
    CompareCanShowTopic,
    Jump,
    SetCanShowTopic,
    EndCanShowTopic,
    Add,
    Subtract,
    Set,
    ShowMessage,
    StatusText,
    SpeakInHouse,
    SpeakNpc,
    MoveToMap,
    MoveNpc,
    ChangeEvent,
    OpenChest,
    RandomJump,
    SummonMonsters,
    SummonItem,
    GiveItem,
    CastSpell,
    ShowFace,
    ReceiveDamage,
    SetSnow,
    ShowMovie,
    SetSprite,
    ChangeDoorState,
    StopAnimation,
    SetTexture,
    ToggleIndoorLight,
    SetFacetBit,
    SetActorFlag,
    SetActorGroupFlag,
    SetActorGroup,
    SetNpcTopic,
    SetNpcGroupNews,
    SetNpcGreeting,
    SetNpcItem,
    SetActorItem,
    CharacterAnimation,
    ForPartyMember,
    CheckItemsCount,
    RemoveItems,
    CheckSkill,
    IsActorKilled,
    IsActorKilledCanShowTopic,
    ChangeGroup,
    ChangeGroupAlly,
    CheckSeason,
    ToggleChestFlag,
    InputString,
    PressAnyKey,
    SpecialJump,
    IsTotalBountyHuntingAwardInRange,
    IsNpcInParty,
};

struct EventIrInstruction
{
    uint16_t eventId = 0;
    uint8_t step = 0;
    EventIrOperation operation = EventIrOperation::Unknown;
    uint32_t sourceOpcode = 0;
    std::vector<uint32_t> arguments;
    std::optional<uint8_t> jumpTargetStep;
    std::optional<std::string> text;
    std::optional<std::string> note;
};

struct EventIrEvent
{
    uint16_t eventId = 0;
    std::vector<EventIrInstruction> instructions;
};

class EventIrProgram
{
public:
    static EventIrProgram fromEvents(std::vector<EventIrEvent> events);

    const std::vector<EventIrEvent> &getEvents() const;
    size_t getInstructionCount() const;
    bool hasEvent(uint16_t eventId) const;
    std::optional<std::string> getHint(uint16_t eventId) const;
    std::optional<std::string> summarizeEvent(uint16_t eventId) const;
    std::vector<uint32_t> getOpenedChestIds(uint16_t eventId) const;
    std::string dump() const;
    std::string saveToYamlText() const;
    bool loadFromYamlText(const std::string &text, std::string &error);
    void setLuaSource(std::string chunkText, std::string chunkName);
    const std::optional<std::string> &luaSourceText() const;
    const std::optional<std::string> &luaSourceName() const;

private:
    static std::string operationName(EventIrOperation operation);

    const EventIrEvent *findEvent(uint16_t eventId) const;

    std::vector<EventIrEvent> m_events;
    std::optional<std::string> m_luaSourceText;
    std::optional<std::string> m_luaSourceName;
};
}
