#pragma once

#include "game/tables/ClassSkillTable.h"
#include "game/events/EventRuntime.h"
#include "game/tables/HouseTable.h"
#include "game/tables/NpcDialogTable.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
class OutdoorWorldRuntime;

enum class EventDialogActionKind
{
    None,
    HouseService,
    HouseResident,
    NpcTopic,
    RosterJoinOffer,
    RosterJoinAccept,
    RosterJoinDecline,
    MasteryTeacherOffer,
    MasteryTeacherLearn,
};

struct EventDialogAction
{
    EventDialogActionKind kind = EventDialogActionKind::None;
    uint32_t id = 0;
    uint32_t secondaryId = 0;
    std::string label;
    std::string argument;
    bool enabled = true;
    bool textOnly = false;
    std::string disabledReason;
};

struct EventDialogContent
{
    bool isActive = false;
    bool isHouseDialog = false;
    uint32_t sourceId = 0;
    uint32_t participantPictureId = 0;
    std::string houseTitle;
    std::string title;
    std::vector<std::string> lines;
    std::vector<EventDialogAction> actions;
};

std::vector<uint32_t> collectSelectableResidentNpcIds(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState
);

EventDialogContent buildEventDialogContent(
    EventRuntimeState &eventRuntimeState,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const std::optional<EventIrProgram> *pGlobalEventIrProgram,
    const HouseTable *pHouseTable,
    const ClassSkillTable *pClassSkillTable,
    const NpcDialogTable *pNpcDialogTable,
    const Party *pParty,
    const OutdoorWorldRuntime *pOutdoorWorldRuntime,
    float currentGameMinutes
);
}
