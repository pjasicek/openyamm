#pragma once

#include "game/tables/ClassSkillTable.h"
#include "game/events/EventRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/tables/HouseTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/NpcDialogTable.h"

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
    MapTransitionConfirm,
    MapTransitionCancel,
    RosterJoinOffer,
    RosterJoinAccept,
    RosterJoinDecline,
    MasteryTeacherOffer,
    MasteryTeacherLearn,
};

enum class EventDialogParticipantVisual
{
    Portrait,
    MapIcon,
};

enum class EventDialogPresentation
{
    Standard,
    Transition,
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
    EventDialogParticipantVisual participantVisual = EventDialogParticipantVisual::Portrait;
    EventDialogPresentation presentation = EventDialogPresentation::Standard;
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
    const std::optional<ScriptedEventProgram> *pGlobalEventProgram,
    const HouseTable *pHouseTable,
    const ClassSkillTable *pClassSkillTable,
    const NpcDialogTable *pNpcDialogTable,
    const MapStatsEntry *pCurrentMap,
    const std::vector<MapStatsEntry> *pMapEntries,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime,
    float currentGameMinutes
);
}
