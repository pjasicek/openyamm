#pragma once

#include "game/HouseTable.h"
#include "game/StrTable.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class EvtOpcode : uint8_t
{
    Invalid = 0,
    Exit = 1,
    SpeakInHouse = 2,
    PlaySound = 3,
    MouseOver = 4,
    LocationName = 5,
    MoveToMap = 6,
    OpenChest = 7,
    ShowFace = 8,
    ReceiveDamage = 9,
    SetSnow = 10,
    SetTexture = 11,
    ShowMovie = 12,
    SetSprite = 13,
    Compare = 14,
    ChangeDoorState = 15,
    Add = 16,
    Subtract = 17,
    Set = 18,
    SummonMonsters = 19,
    CastSpell = 21,
    SpeakNpc = 22,
    SetFacesBit = 23,
    ToggleActorFlag = 24,
    RandomGoTo = 25,
    InputString = 26,
    StatusText = 29,
    ShowMessage = 30,
    OnTimer = 31,
    ToggleIndoorLight = 32,
    PressAnyKey = 33,
    SummonItem = 34,
    ForPartyMember = 35,
    Jmp = 36,
    OnMapReload = 37,
    OnLongTimer = 38,
    SetNpcTopic = 39,
    MoveNpc = 40,
    GiveItem = 41,
    ChangeEvent = 42,
    CheckSkill = 43,
    OnCanShowDialogItemCmp = 44,
    EndCanShowDialogItem = 45,
    SetCanShowDialogItem = 46,
    SetNpcGroupNews = 47,
    SetActorGroup = 48,
    NpcSetItem = 49,
    SetNpcGreeting = 50,
    IsActorKilled = 51,
    CanShowTopicIsActorKilled = 52,
    OnMapLeave = 53,
    ChangeGroup = 54,
    ChangeGroupAlly = 55,
    CheckSeason = 56,
    ToggleActorGroupFlag = 57,
    ToggleChestFlag = 58,
    CharacterAnimation = 59,
    SetActorItem = 60,
    OnDateTimer = 61,
    EnableDateTimer = 62,
    StopAnimation = 63,
    CheckItemsCount = 64,
    RemoveItems = 65,
    SpecialJump = 66,
    IsTotalBountyHuntingAwardInRange = 67,
    IsNpcInParty = 68
};

struct EvtInstruction
{
    uint8_t step = 0;
    EvtOpcode opcode = EvtOpcode::Invalid;
    std::vector<uint8_t> rawPayload;

    std::optional<uint8_t> textId;
    std::optional<uint8_t> targetStep;
    std::optional<uint8_t> booleanValue;
    std::optional<uint32_t> value1;
    std::optional<uint32_t> value2;
    std::optional<uint32_t> value3;
    std::optional<std::string> stringValue;
    std::vector<uint8_t> listValues;
};

struct EvtEvent
{
    uint16_t eventId = 0;
    std::vector<EvtInstruction> instructions;
};

class EvtProgram
{
public:
    bool loadFromBytes(const std::vector<uint8_t> &bytes);
    const std::vector<EvtEvent> &getEvents() const;
    size_t getInstructionCount() const;
    bool hasEvent(uint16_t eventId) const;
    std::optional<std::string> getHint(uint16_t eventId, const StrTable &strTable, const HouseTable &houseTable) const;
    std::optional<std::string> summarizeEvent(uint16_t eventId, const StrTable &strTable, const HouseTable &houseTable) const;
    std::vector<uint32_t> getOpenedChestIds(uint16_t eventId) const;
    std::string dump(const StrTable &strTable) const;
    static std::string opcodeName(EvtOpcode opcode);

private:
    const EvtEvent *findEvent(uint16_t eventId) const;
    static bool parseInstruction(const std::vector<uint8_t> &record, EvtInstruction &instruction);
    static std::string formatInstruction(const EvtInstruction &instruction, const StrTable &strTable);

    std::vector<EvtEvent> m_events;
};
}
