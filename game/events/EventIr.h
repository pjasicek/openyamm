#pragma once

#include "game/events/EvtEnums.h"
#include "game/events/EvtProgram.h"
#include "game/tables/HouseTable.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/StrTable.h"

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
    EvtOpcode sourceOpcode = EvtOpcode::Invalid;
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
    bool buildFromEvtProgram(
        const EvtProgram &evtProgram,
        const StrTable &strTable,
        const HouseTable &houseTable,
        const NpcDialogTable &npcDialogTable
    );
    const std::vector<EventIrEvent> &getEvents() const;
    size_t getInstructionCount() const;
    std::string dump() const;

private:
    static EventIrOperation mapOperation(EvtOpcode opcode);
    static std::string operationName(EventIrOperation operation);
    static EventIrInstruction convertInstruction(
        uint16_t eventId,
        const EvtInstruction &evtInstruction,
        const StrTable &strTable,
        const HouseTable &houseTable,
        const NpcDialogTable &npcDialogTable
    );

    std::vector<EventIrEvent> m_events;
};
}
