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
    // An MM9 trainer's topic (id its RUDE row): its skills, or with one skill that skill's member rows.
    Mm9RudeSkillTrainerOffer,
    // One skill of a trainer that teaches several (id the row, secondaryId the skill): its member rows.
    Mm9RudeSkillTrainerSkill,
    // One member's lesson (id the row, secondaryId the skill, memberIndex the member).
    Mm9RudeSkillTrainerLearn,
    Mm9RudeSkillTrainerBack,
    // An MM9 dock's boat: argument its route's canonical id; secondaryId 0 for today's, else the weekday it waits for
    // plus one (a departure chosen in the Schedule popup).
    Mm9RudeTransportRoute,
    Mm9RudeTransportBack,
    // An MM9 dock's Schedule: the week's boats in the transport Schedule popup.
    Mm9RudeTransportSchedule,
    // An MM9 promoter's standing topic (Mm9PromotionService): promote the members eligible now.
    Mm9RudePromotionService,
    // An MM9 lost-item keeper's standing topic (Mm9RudeDialogueTable::isLostItemKeeper): give back a lost item.
    Mm9RudeLostItemService,
    // An MM9 racial trainer's standing topic (Mm9RacialTrainer): a racial-ability lesson row per party member.
    Mm9RudeRacialTrainerOffer,
    // One member's racial-ability lesson (memberIndex the member).
    Mm9RudeRacialTrainerLearn,
    // A ruleset's row on an MM9 person (Mm9RulesetRow): id the global event it runs.
    Mm9RudeRulesetEvent,
    // A ruleset's bounty office on an MM9 person (Mm9RulesetRow): argument the map file the hunt is on.
    Mm9RudeBountyOffice,
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
    // A row that says why it cannot be taken (an MM9 trainer's member who cannot learn): shown muted.
    Locked,
};

struct EventDialogAction
{
    EventDialogActionKind kind = EventDialogActionKind::None;
    uint32_t id = 0;
    uint32_t secondaryId = 0;
    // The party member a per-member row acts on (an MM9 trainer's lesson).
    size_t memberIndex = 0;
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
    // The rules' offer to reset the cleared dungeon on the way in (MAW): a transition shows it in a popup over the
    // scene with its MapTransitionReset action and Cancel, before the ordinary OK and Close.
    std::string resetPrompt;
};

bool transitionResetPopupOpen(const EventDialogContent &dialog);
// Cancel of the reset popup: the dialog goes on as an ordinary transition without the reset.
void dismissTransitionResetPopup(EventDialogContent &dialog);

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
