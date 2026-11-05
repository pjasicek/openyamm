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
struct MergedNpcProfessionEntry;

enum class EventDialogActionKind
{
    None,
    HouseService,
    HouseProprietor,
    HouseExtraExit,
    HouseResident,
    NpcTopic,
    ArenaChallenge,
    NpcProfessionNews,
    NpcProfessionAction,
    NpcProfessionDescription,
    NpcHireOffer,
    NpcHireAccept,
    NpcHireDecline,
    NpcDismiss,
    NpcBtb,
    MapTransitionConfirm,
    // Enter a completed dungeon reset to its first state, harder (MAW).
    MapTransitionReset,
    MapTransitionCancel,
    RosterJoinOffer,
    RosterJoinAccept,
    RosterJoinDecline,
    MasteryTeacherOffer,
    MasteryTeacherLearn,
    GuildMembershipOffer,
    GuildMembershipJoin,
    GeneratedMercenaryJoinOffer,
    Mm9RudeTopic,
    Mm9RudeSkillTrainerOffer,
    Mm9RudeSkillTrainerLearn,
    Mm9RudeSkillTrainerBack,
    Mm9RudeTransportRoute,
    Mm9RudeTransportBack,
    // An event's choice box (AskChoiceWithAnswerSteps): id is the answer's index.
    EventChoice,
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
    Mm9Rude,
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

// How the MM9 conversation bar marks a choice (level_generation/ui/mm9_talk_dialogue_study_20261102, A): a quest row
// the party has not chosen yet, one it has, or the row that ends the talk.
enum class EventDialogChoiceMark
{
    None,
    New,
    Visited,
    Exit,
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
    EventDialogChoiceMark choiceMark = EventDialogChoiceMark::None;
    // A service row's tag on the conversation bar ("Shop", "Train · Expert").
    std::string choiceTag;
};

struct EventDialogContent
{
    bool isActive = false;
    bool isHouseDialog = false;
    uint32_t sourceId = 0;
    int32_t dialogueNodeId = 0;
    std::optional<uint32_t> sourceActorIndex;
    uint32_t participantPictureId = 0;
    EventDialogParticipantVisual participantVisual = EventDialogParticipantVisual::Portrait;
    EventDialogPresentation presentation = EventDialogPresentation::Standard;
    DialogueScenePolicy scenePolicy = DialogueScenePolicy::HouseVideo;
    bool mm9RudeExitCallbackExecuted = false;
    std::string participantTextureName;
    std::string videoName;
    std::string videoDirectory;
    std::string houseTitle;
    std::string title;
    std::vector<std::string> lines;
    // The party's sentence the reply in `lines` answers (MM9 talk): quoted above it on the conversation bar.
    std::string echo;
    std::vector<EventDialogAction> actions;
};

std::vector<uint32_t> collectSelectableResidentNpcIds(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState
);

std::string formatNpcProfessionText(
    std::string text,
    const NpcEntry &npc,
    const MergedNpcProfessionEntry &profession,
    const Party *pParty,
    int effectiveReputation = 0,
    std::optional<int> requiredReputation = std::nullopt,
    float currentGameMinutes = 0.0f);

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
