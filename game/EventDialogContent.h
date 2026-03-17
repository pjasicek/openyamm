#pragma once

#include "game/ClassSkillTable.h"
#include "game/EventRuntime.h"
#include "game/HouseTable.h"
#include "game/NpcDialogTable.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Party;

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
    std::string label;
    bool enabled = true;
    std::string disabledReason;
};

struct EventDialogContent
{
    bool isActive = false;
    bool isHouseDialog = false;
    uint32_t sourceId = 0;
    std::string title;
    std::vector<std::string> lines;
    std::vector<EventDialogAction> actions;
};

EventDialogContent buildEventDialogContent(
    EventRuntimeState &eventRuntimeState,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const std::optional<EventIrProgram> *pGlobalEventIrProgram,
    const HouseTable *pHouseTable,
    const ClassSkillTable *pClassSkillTable,
    const NpcDialogTable *pNpcDialogTable,
    const Party *pParty,
    int currentHour
);
}
