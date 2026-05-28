#pragma once

#include "game/tables/ClassSkillTable.h"
#include "game/events/EventRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/tables/HouseTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/TransitionTable.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
class MergedNpcProfessionTable;
class MergedNewsProfessionTopicTable;
class MergedNpcBtbTable;
class MergedTeacherTopicTable;
class MergedContinentSettingTable;

enum class EventDialogActionKind
{
    None,
    HouseService,
    HouseProprietor,
    HouseExtraExit,
    HouseResident,
    NpcTopic,
    NpcProfessionNews,
    NpcProfessionAction,
    NpcProfessionDescription,
    NpcHireOffer,
    NpcHireAccept,
    NpcHireDecline,
    NpcDismiss,
    NpcBtb,
    MapTransitionConfirm,
    MapTransitionCancel,
    RosterJoinOffer,
    RosterJoinAccept,
    RosterJoinDecline,
    MasteryTeacherOffer,
    MasteryTeacherLearn,
    GuildMembershipOffer,
    GuildMembershipJoin,
    GeneratedMercenaryJoinOffer,
    ArenaDifficulty,
    Mm9Topic,
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

enum class NpcFollowerActionTopicId : uint32_t
{
    HealParty = 1714,
    MakeFood = 1715,
    CastFly = 1716,
    CastWaterWalk = 1717,
    CastTownPortal = 1718,
    CastBless = 1719,
    CastHeroism = 1720,
};

struct EventDialogAction
{
    EventDialogActionKind kind = EventDialogActionKind::None;
    uint32_t id = 0;
    uint32_t secondaryId = 0;
    uint32_t participantPictureId = 0;
    EventDialogParticipantVisual participantVisual = EventDialogParticipantVisual::Portrait;
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
    std::optional<uint32_t> sourceActorIndex;
    uint32_t participantPictureId = 0;
    EventDialogParticipantVisual participantVisual = EventDialogParticipantVisual::Portrait;
    EventDialogPresentation presentation = EventDialogPresentation::Standard;
    std::string participantTextureName;
    std::string videoName;
    std::string videoDirectory;
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

uint32_t npcBtbDialogueAccessVariableKey(uint32_t npcId);
uint32_t npcBtbDialogueAccessDay(float currentGameMinutes);
bool npcProfessionActionTopicHasDailyCooldown(uint32_t topicId);
uint32_t npcProfessionActionCooldownVariableKey(uint32_t npcId);
uint32_t npcProfessionActionCooldownDay(float currentGameMinutes);
bool npcProfessionActionUsedToday(
    const EventRuntimeState &eventRuntimeState,
    uint32_t npcId,
    float currentGameMinutes);

EventDialogContent buildEventDialogContent(
    EventRuntimeState &eventRuntimeState,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const std::optional<ScriptedEventProgram> *pGlobalEventProgram,
    const HouseTable *pHouseTable,
    const ClassSkillTable *pClassSkillTable,
    const NpcDialogTable *pNpcDialogTable,
    const TransitionTable *pTransitionTable,
    const MapStatsEntry *pCurrentMap,
    const std::vector<MapStatsEntry> *pMapEntries,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime,
    float currentGameMinutes,
    const MergedNpcProfessionTable *pNpcProfessionTable = nullptr,
    const MergedNewsProfessionTopicTable *pNewsProfessionTopicTable = nullptr,
    const MergedNpcBtbTable *pNpcBtbTable = nullptr,
    const MergedTeacherTopicTable *pTeacherTopicTable = nullptr,
    const MergedContinentSettingTable *pContinentSettingTable = nullptr
);
}
