#include "game/gameplay/GameplayDialogController.h"
#include "engine/Localization.h"

#include "game/StringUtils.h"
#include "game/audio/SoundIds.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/ArenaRuntime.h"
#include "game/gameplay/BountyHuntRuntime.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/gameplay/MercenaryRecruitmentRuntime.h"
#include "game/gameplay/PartyHostileAlert.h"
#include "game/gameplay/TravelRuntime.h"
#include "game/mm9/Mm9HirelingServices.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/mm9/Mm9MapTransition.h"
#include "game/mm9/Mm9SkillTrainer.h"
#include "game/mm9/Mm9TransportRoute.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/PriceCalculator.h"
#include "game/party/PlaythroughStatistics.h"
#include "game/party/EventSpellBuffs.h"
#include "game/tables/HouseTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/SpellTable.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/rules/ExperienceRules.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/tables/RosterTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <optional>
#include <random>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t DefaultAdventurersInnHouseId = 185;
// The context of an MM9 conversation line the party says, for a text an NPC also says to the party.
constexpr std::string_view Mm9PartyLineContext = "said by the party";
constexpr uint32_t ArcomageRulesTextId = 136;
constexpr uint32_t AutoNoteVariableTag = 0x00E1u;
constexpr uint32_t HeroismEffectSoundId = 14060;
constexpr int OutdoorMapTravelFoodCost = 5;
constexpr size_t MaxNpcFollowerCount = 4;
constexpr uint32_t MaxNpcFollowerFeePercent = 100;
constexpr uint32_t NpcBegTopicId = 1766;
constexpr uint32_t NpcThreatTopicId = 1767;
constexpr uint32_t NpcBribeTopicId = 1768;
constexpr uint32_t Mm6BountyHuntTopicId = 1712;
constexpr uint32_t Mm8ThisMonthsBountyTopicId = 579;
constexpr int MaxFoodForCookFollower = 14;
constexpr int CookFollowerFoodAmount = 1;
constexpr int ChefFollowerFoodAmount = 2;
constexpr float ShopRudeSpeechDelaySeconds = 2.0f;

const char *eventDialogActionKindName(EventDialogActionKind kind)
{
    switch (kind)
    {
        case EventDialogActionKind::None:
            return "none";
        case EventDialogActionKind::HouseService:
            return "house_service";
        case EventDialogActionKind::HouseProprietor:
            return "house_proprietor";
        case EventDialogActionKind::HouseExtraExit:
            return "house_extra_exit";
        case EventDialogActionKind::HouseResident:
            return "house_resident";
        case EventDialogActionKind::NpcTopic:
            return "npc_topic";
        case EventDialogActionKind::ArenaChallenge:
            return "arena_challenge";
        case EventDialogActionKind::NpcProfessionNews:
            return "npc_profession_news";
        case EventDialogActionKind::NpcProfessionAction:
            return "npc_profession_action";
        case EventDialogActionKind::NpcProfessionDescription:
            return "npc_profession_description";
        case EventDialogActionKind::NpcHireOffer:
            return "npc_hire_offer";
        case EventDialogActionKind::NpcHireAccept:
            return "npc_hire_accept";
        case EventDialogActionKind::NpcHireDecline:
            return "npc_hire_decline";
        case EventDialogActionKind::NpcDismiss:
            return "npc_dismiss";
        case EventDialogActionKind::NpcBtb:
            return "npc_btb";
        case EventDialogActionKind::MapTransitionConfirm:
            return "map_transition_confirm";
        case EventDialogActionKind::MapTransitionReset:
            return "map_transition_reset";
        case EventDialogActionKind::MapTransitionCancel:
            return "map_transition_cancel";
        case EventDialogActionKind::RosterJoinOffer:
            return "roster_join_offer";
        case EventDialogActionKind::RosterJoinAccept:
            return "roster_join_accept";
        case EventDialogActionKind::RosterJoinDecline:
            return "roster_join_decline";
        case EventDialogActionKind::MasteryTeacherOffer:
            return "mastery_teacher_offer";
        case EventDialogActionKind::MasteryTeacherLearn:
            return "mastery_teacher_learn";
        case EventDialogActionKind::GuildMembershipOffer:
            return "guild_membership_offer";
        case EventDialogActionKind::GuildMembershipJoin:
            return "guild_membership_join";
        case EventDialogActionKind::GeneratedMercenaryJoinOffer:
            return "generated_mercenary_join_offer";
        case EventDialogActionKind::Mm9RudeTopic:
            return "mm9_rude_topic";
        case EventDialogActionKind::Mm9RudeSkillTrainerOffer:
            return "mm9_rude_skill_trainer_offer";
        case EventDialogActionKind::Mm9RudeSkillTrainerSkill:
            return "mm9_rude_skill_trainer_skill";
        case EventDialogActionKind::Mm9RudeSkillTrainerLearn:
            return "mm9_rude_skill_trainer_learn";
        case EventDialogActionKind::Mm9RudeSkillTrainerBack:
            return "mm9_rude_skill_trainer_back";
        case EventDialogActionKind::Mm9RudeTransportRoute:
            return "mm9_rude_transport_route";
        case EventDialogActionKind::Mm9RudeTransportBack:
            return "mm9_rude_transport_back";
        case EventDialogActionKind::Mm9RudeTransportSchedule:
            return "mm9_rude_transport_schedule";
        case EventDialogActionKind::Mm9RudePromotionService:
            return "mm9_rude_promotion_service";
        case EventDialogActionKind::Mm9RudeLostItemService:
            return "mm9_rude_lost_item_service";
        case EventDialogActionKind::Mm9RudeRacialTrainerOffer:
            return "mm9_rude_racial_trainer_offer";
        case EventDialogActionKind::Mm9RudeRacialTrainerLearn:
            return "mm9_rude_racial_trainer_learn";
        case EventDialogActionKind::Mm9RudeRulesetEvent:
            return "mm9_rude_ruleset_event";
        case EventDialogActionKind::Mm9RudeBountyOffice:
            return "mm9_rude_bounty_office";
        case EventDialogActionKind::EventChoice:
            return "event_choice";
    }

    return "unknown";
}

uint64_t fnv1aUpdate(uint64_t hash, const std::string &text)
{
    for (char character : text)
    {
        hash ^= static_cast<unsigned char>(character);
        hash *= 1099511628211ull;
    }

    return hash;
}

uint64_t dialogLinesHash(const EventDialogContent &dialog)
{
    uint64_t hash = 1469598103934665603ull;

    for (const std::string &line : dialog.lines)
    {
        hash = fnv1aUpdate(hash, line);
        hash = fnv1aUpdate(hash, "\n");
    }

    return hash;
}

std::string jsonEscaped(const std::string &value)
{
    std::string escaped;
    escaped.reserve(value.size() + 8);

    for (char character : value)
    {
        switch (character)
        {
            case '\\':
                escaped += "\\\\";
                break;
            case '"':
                escaped += "\\\"";
                break;
            case '\n':
                escaped += "\\n";
                break;
            case '\r':
                escaped += "\\r";
                break;
            case '\t':
                escaped += "\\t";
                break;
            default:
                escaped.push_back(character);
                break;
        }
    }

    return escaped;
}

std::string traceQuoted(const std::string &value)
{
    std::string quoted = "\"";

    for (char character : value)
    {
        if (character == '\\' || character == '"')
        {
            quoted.push_back('\\');
        }

        quoted.push_back(character);
    }

    quoted.push_back('"');
    return quoted;
}

std::string dialogActionsJson(const EventDialogContent &dialog)
{
    std::ostringstream stream;
    stream << '[';

    for (size_t index = 0; index < dialog.actions.size(); ++index)
    {
        const EventDialogAction &action = dialog.actions[index];

        if (index != 0)
        {
            stream << ',';
        }

        stream << "{\"index\":" << index
               << ",\"kind\":\"" << eventDialogActionKindName(action.kind) << '"'
               << ",\"id\":" << action.id
               << ",\"secondary_id\":" << action.secondaryId
               << ",\"enabled\":" << (action.enabled ? "true" : "false")
               << ",\"text_only\":" << (action.textOnly ? "true" : "false")
               << ",\"label\":\"" << jsonEscaped(action.label) << "\"}";
    }

    stream << ']';
    return stream.str();
}

void traceDialogState(const EventDialogContent &dialog, const std::string &reason)
{
    if (!gameplayDebugTraceEnabled() || gameplayDebugTraceSuppressed())
    {
        return;
    }

    GAMEPLAY_DEBUG_TRACE(
        "dialog_state reason=" + reason
        + " active=" + (dialog.isActive ? "true" : "false")
        + " house_dialog=" + (dialog.isHouseDialog ? "true" : "false")
        + " source_id=" + std::to_string(dialog.sourceId)
        + " title=" + traceQuoted(dialog.title)
        + " house_title=" + traceQuoted(dialog.houseTitle)
        + " line_count=" + std::to_string(dialog.lines.size())
        + " text_hash=" + std::to_string(dialogLinesHash(dialog))
        + " action_count=" + std::to_string(dialog.actions.size())
        + " actions_json=" + traceQuoted(dialogActionsJson(dialog)));
}

const char *dialogueContextKindName(DialogueContextKind kind)
{
    switch (kind)
    {
        case DialogueContextKind::None:
            return "none";
        case DialogueContextKind::MapEvent:
            return "map_event";
        case DialogueContextKind::HouseService:
            return "house_service";
        case DialogueContextKind::NpcTalk:
            return "npc_talk";
        case DialogueContextKind::NpcNews:
            return "npc_news";
        case DialogueContextKind::MapTransition:
            return "map_transition";
        case DialogueContextKind::Mm9Rude:
            return "mm9_rude";
    }

    return "unknown";
}

enum class NpcProfessionId : uint32_t
{
    Healer = 10,
    ExpertHealer = 11,
    MasterHealer = 12,
    Cook = 33,
    Chef = 34,
    WindMaster = 39,
    WaterMaster = 40,
    GateMaster = 41,
    Acolyte = 42,
    Piper = 43,
};

std::optional<SoundId> soundIdForPortraitFxEvent(PortraitFxEventKind kind)
{
    switch (kind)
    {
        case PortraitFxEventKind::AutoNote:
        case PortraitFxEventKind::QuestComplete:
        case PortraitFxEventKind::StatIncrease:
        case PortraitFxEventKind::StatBaseIncrease:
            return SoundId::Quest;

        case PortraitFxEventKind::AwardGain:
            return SoundId::Chimes;

        case PortraitFxEventKind::StatDecrease:
        case PortraitFxEventKind::Disease:
        case PortraitFxEventKind::None:
            return std::nullopt;
    }

    return std::nullopt;
}

bool isDungeonMapFileName(const std::string &mapFileName)
{
    return toLowerCopy(mapFileName).ends_with(".blv");
}

bool isOutdoorMapFileName(const std::string &mapFileName)
{
    return toLowerCopy(mapFileName).ends_with(".odm");
}

std::string mercenarySelfImpression(uint32_t level)
{
    static constexpr std::array<std::string_view, 5> Impressions = {
        Engine::trNoop("apprentice"),
        Engine::trNoop("skilled"),
        Engine::trNoop("well_known"),
        Engine::trNoop("masterful"),
        Engine::trNoop("great"),
    };
    const uint32_t bucket = std::clamp<uint32_t>((std::max<uint32_t>(1, level) + 9) / 10, 1, 5);
    return Engine::tr(Impressions[bucket - 1]);
}

std::string generatedMercenaryJoinOfferText(
    const EventRuntimeState::GeneratedMercenaryRecruit &recruit)
{
    return Engine::tr("Good tidings. I am {name}, {impression} {class}. I'd love to see the world and taste the "
                      "adventure, but it'd be foolish to go alone. Perhaps I could come with you?",
                      {{"name", recruit.character.name},
                       {"impression", mercenarySelfImpression(recruit.character.level)},
                       {"class", Engine::localize(displayClassName(recruit.character.className), "class")}});
}

int mapTransitionTravelFoodRequired(
    const GameplayDialogController::Context &context,
    const MapEdgeTransition &transition)
{
    if (context.pCurrentMap != nullptr
        && isOutdoorMapFileName(context.pCurrentMap->fileName)
        && isOutdoorMapFileName(transition.destinationMapFileName))
    {
        return OutdoorMapTravelFoodCost;
    }

    return std::max(0, transition.travelDays);
}

int outdoorMapMoveTravelDays(
    const GameplayDialogController::Context &context,
    const EventRuntimeState::PendingMapMove &move)
{
    if (context.pCurrentMap == nullptr || !move.mapName.has_value())
    {
        return 0;
    }

    const std::string currentMapFileName = toLowerCopy(context.pCurrentMap->fileName);
    const std::string destinationMapFileName = toLowerCopy(*move.mapName);

    if (currentMapFileName == destinationMapFileName
        || !isOutdoorMapFileName(currentMapFileName)
        || !isOutdoorMapFileName(destinationMapFileName))
    {
        return 0;
    }

    return OutdoorMapTravelFoodCost;
}

const Mm9MapTransition *pendingMm9PositionedTransition(
    const GameplayDialogController::Context &context,
    const EventRuntimeState::PendingDialogueContext &dialogueContext)
{
    if (context.pMm9MapTransitionTable == nullptr || context.pCurrentMap == nullptr
        || dialogueContext.kind != DialogueContextKind::MapTransition)
    {
        return nullptr;
    }
    for (const Mm9MapTransition *pTransition :
        context.pMm9MapTransitionTable->forSourceMapFile(context.pCurrentMap->fileName))
    {
        if (pTransition->sourceObjectIndex == dialogueContext.sourceId)
        {
            return pTransition;
        }
    }
    return nullptr;
}

bool isCurrentMapDungeon(const GameplayDialogController::Context &context)
{
    if (context.pWorldRuntime != nullptr && context.pWorldRuntime->isIndoorMap())
    {
        return true;
    }

    if (context.pCurrentMap != nullptr)
    {
        return isDungeonMapFileName(context.pCurrentMap->fileName);
    }

    return false;
}

std::string pendingMapMoveTraceFields(const EventRuntimeState::PendingMapMove &move)
{
    return " destination_map=\"" + move.mapName.value_or(std::string()) + "\""
        + " destination_name=\"" + move.traceDestinationName + "\""
        + " use_start_position=" + (move.useMapStartPosition ? "true" : "false")
        + " pos=(" + std::to_string(move.x)
        + "," + std::to_string(move.y)
        + "," + std::to_string(move.z) + ")"
        + " direction_degrees="
        + (move.directionDegrees.has_value() ? std::to_string(*move.directionDegrees) : std::string("none"));
}

void assignMapMoveTraceSource(
    EventRuntimeState::PendingMapMove &move,
    const std::string &sourceKind,
    uint32_t sourceId,
    uint32_t actionId,
    uint32_t eventId,
    const std::string &destinationName)
{
    move.traceSourceKind = sourceKind;
    move.traceSourceId = sourceId;
    move.traceActionId = actionId;
    move.traceEventId = eventId;
    move.traceDestinationName = destinationName;
}

EventRuntimeState::MapTransitionTrace mapTransitionTrace(
    const std::string &sourceKind,
    uint32_t sourceId,
    uint32_t actionId,
    uint32_t eventId,
    const EventRuntimeState::PendingMapMove &move,
    bool confirmationRequired)
{
    EventRuntimeState::MapTransitionTrace trace = {};
    trace.sourceKind = sourceKind;
    trace.sourceId = sourceId;
    trace.actionId = actionId;
    trace.eventId = eventId;
    trace.confirmationRequired = confirmationRequired;
    trace.destinationMap = move.mapName.value_or(std::string());
    trace.destinationName = move.traceDestinationName;
    trace.useStartPosition = move.useMapStartPosition;
    trace.x = move.x;
    trace.y = move.y;
    trace.z = move.z;
    trace.directionDegrees = move.directionDegrees;
    return trace;
}

void logMapTransitionRequested(
    EventRuntimeState &eventRuntimeState,
    const std::string &sourceKind,
    uint32_t sourceId,
    uint32_t actionId,
    uint32_t eventId,
    const EventRuntimeState::PendingMapMove &move,
    bool confirmationRequired)
{
    eventRuntimeState.lastMapTransitionRequested =
        mapTransitionTrace(sourceKind, sourceId, actionId, eventId, move, confirmationRequired);
    GAMEPLAY_DEBUG_TRACE(
        "map_transition_requested source_kind=\"" + sourceKind + "\""
        + " source_id=" + std::to_string(sourceId)
        + " action_id=" + std::to_string(actionId)
        + " event_id=" + std::to_string(eventId)
        + " confirmation_required=" + (confirmationRequired ? "true" : "false")
        + pendingMapMoveTraceFields(move));
}

void logMapTransitionConfirmed(
    EventRuntimeState &eventRuntimeState,
    const EventRuntimeState::PendingDialogueContext &context,
    const EventRuntimeState::PendingMapMove &move,
    uint32_t actionId)
{
    eventRuntimeState.lastMapTransitionConfirmed =
        mapTransitionTrace(dialogueContextKindName(context.kind), context.sourceId, actionId, 0, move, false);
    GAMEPLAY_DEBUG_TRACE(
        "map_transition_confirmed source_kind=\"" + std::string(dialogueContextKindName(context.kind)) + "\""
        + " source_id=" + std::to_string(context.sourceId)
        + " action_id=" + std::to_string(actionId)
        + pendingMapMoveTraceFields(move));
}

bool partyHasIndoorExitAlert(const GameplayDialogController::Context &context)
{
    return context.pWorldRuntime != nullptr && partyHasYellowAlert(*context.pWorldRuntime);
}

void playSpeechReaction(
    GameplayDialogController::Context &context,
    size_t memberIndex,
    SpeechId speechId,
    bool triggerFaceAnimation);

void playIndoorExitReactionIfNeeded(
    GameplayDialogController::Context &context,
    const EventRuntimeState::PendingDialogueContext &originalContext,
    bool wasDialogAlreadyActive)
{
    if (wasDialogAlreadyActive
        || originalContext.kind != DialogueContextKind::MapTransition
        || context.pParty == nullptr
        || context.pParty->activeMember() == nullptr
        || !isCurrentMapDungeon(context)
        || !partyHasIndoorExitAlert(context))
    {
        return;
    }

    playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::LeaveDungeon, true);
}

DialogueMenuId dialogueMenuIdForHouseAction(HouseActionId actionId)
{
    switch (actionId)
    {
        case HouseActionId::OpenLearnSkillsMenu:
            return DialogueMenuId::LearnSkills;

        case HouseActionId::OpenShopEquipmentMenu:
            return DialogueMenuId::ShopEquipment;

        case HouseActionId::OpenTavernArcomageMenu:
            return DialogueMenuId::TavernArcomage;

        case HouseActionId::OpenTeacherLedgerMenu:
            return DialogueMenuId::TeacherLedger;

        default:
            return DialogueMenuId::None;
    }
}

uint32_t currentDialogueHostHouseId(const EventRuntimeState &eventRuntimeState)
{
    return eventRuntimeState.dialogueState.hostHouseId;
}

bool isHouseOccupantSelectionAction(const EventDialogAction &action)
{
    return action.kind == EventDialogActionKind::HouseProprietor
        || action.kind == EventDialogActionKind::HouseExtraExit
        || action.kind == EventDialogActionKind::HouseResident;
}

void setPendingDialogueContext(
    EventRuntimeState &eventRuntimeState,
    DialogueContextKind kind,
    uint32_t sourceId,
    uint32_t hostHouseId,
    std::optional<uint32_t> sourceActorIndex = std::nullopt)
{
    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = kind;
    context.sourceId = sourceId;
    context.hostHouseId = hostHouseId;
    context.sourceActorIndex = sourceActorIndex;
    eventRuntimeState.pendingDialogueContext = std::move(context);
}

void executeNpcHook(
    GameplayDialogController::Context &context,
    EventRuntimeHookKind kind,
    uint32_t npcId,
    std::optional<uint32_t> sourceActorIndex)
{
    if (context.pWorldRuntime == nullptr || npcId == 0)
    {
        return;
    }

    EventRuntimeState::ActiveHookContext hookContext = {};
    hookContext.kind = kind;
    hookContext.npcId = npcId;
    hookContext.actorIndex = sourceActorIndex;
    hookContext.heldItemId = context.pParty != nullptr ? context.pParty->heldItemIdForQueries() : 0;
    context.eventRuntimeState.activeHookContext = std::move(hookContext);
    context.pWorldRuntime->executeEventHooks(kind);
    context.eventRuntimeState.activeHookContext.reset();
}

// What a quest pays is measured around the event that pays it: the party's gold and the first member's experience.
struct QuestRewardProbe
{
    int gold = 0;
    uint64_t experience = 0;
};

QuestRewardProbe questRewardProbe(const GameplayDialogController::Context &context)
{
    const Character *pFirst = context.pParty != nullptr ? context.pParty->member(0) : nullptr;
    return {context.pParty != nullptr ? context.pParty->gold() : 0, pFirst != nullptr ? pFirst->experience : 0};
}

// An event that paid the party gold and the first member experience was a quest's reward: the rules may add gold
// (MAW's quest gold bonus, by the levels banked on the other continents).
void payQuestGoldBonus(GameplayDialogController::Context &context, const QuestRewardProbe &before)
{
    const QuestRewardProbe after = questRewardProbe(context);

    if (context.pParty != nullptr && after.gold > before.gold && after.experience > before.experience)
    {
        context.pParty->addGold(context.pParty->rules().experience.questGoldBonus(
            after.gold - before.gold, context.eventRuntimeState.activeHistoryContinentId), GoldReason::Event);
    }
}

bool executeMm9RudeExitCallback(GameplayDialogController::Context &context)
{
    if (context.pWorldRuntime == nullptr
        || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude
        || context.activeEventDialog.mm9RudeExitCallbackExecuted
        || !context.activeEventDialog.sourceActorIndex.has_value())
    {
        return false;
    }

    const MapDeltaData *pMapDeltaData = context.pWorldRuntime->mapDeltaData();
    const uint32_t actorIndex = *context.activeEventDialog.sourceActorIndex;
    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const std::optional<uint16_t> eventId = mm9RudeExitEventIdForSourceObject(actor.mm9SourceObjectIndex);
    if (!eventId.has_value())
    {
        return false;
    }

    size_t previousMessageCount = context.eventRuntimeState.messages.size();
    EventRuntimeState::ActiveHookContext hookContext = {};
    hookContext.actorIndex = actorIndex;
    const std::optional<EventRuntimeState::ActiveHookContext> previousHookContext =
        context.eventRuntimeState.activeHookContext;
    context.eventRuntimeState.activeHookContext = std::move(hookContext);
    context.activeEventDialog.mm9RudeExitCallbackExecuted = true;
    // An MM9 talk's exit pays its quests (the map Lua's reward(key, experience, gold)), as an MM6-MM8 topic does.
    const QuestRewardProbe rewardBefore = questRewardProbe(context);
    const bool executed = context.pWorldRuntime->executeMapEvent(*eventId, previousMessageCount);
    payQuestGoldBonus(context, rewardBefore);
    context.eventRuntimeState.activeHookContext = previousHookContext;
    GAMEPLAY_DEBUG_TRACE(
        "mm9_rude_exit_callback"
        " rude_id=" + std::to_string(context.activeEventDialog.sourceId)
        + " actor_index=" + std::to_string(actorIndex)
        + " source_object_index=" + std::to_string(actor.mm9SourceObjectIndex)
        + " event_id=" + std::to_string(*eventId)
        + " executed=" + std::string(executed ? "true" : "false"));
    return executed;
}

// Ends an MM9 talk: its exit hook runs, and a dialogue the hook opens (the next talk, a travel prompt: Skraelos takes
// the party to the Afterworld, the Questioner follows him) is shown in the talk's place, where a close would drop it.
// True when the hook opened one.
bool endMm9RudeTalk(GameplayDialogController::Context &context)
{
    context.eventRuntimeState.pendingDialogueContext.reset();
    executeMm9RudeExitCallback(context);

    if (!context.eventRuntimeState.pendingDialogueContext.has_value())
    {
        return false;
    }

    context.eventRuntimeState.dialogueState = {};
    return true;
}

bool samePendingMapMove(
    const EventRuntimeState::PendingMapMove &left,
    const EventRuntimeState::PendingMapMove &right)
{
    return left.x == right.x
        && left.y == right.y
        && left.z == right.z
        && left.mapName == right.mapName
        && left.directionDegrees == right.directionDegrees
        && left.useMapStartPosition == right.useMapStartPosition
        && left.startPointName == right.startPointName
        && left.useFullscreenLoading == right.useFullscreenLoading;
}

bool samePendingMapMove(
    const std::optional<EventRuntimeState::PendingMapMove> &left,
    const std::optional<EventRuntimeState::PendingMapMove> &right)
{
    if (left.has_value() != right.has_value())
    {
        return false;
    }

    return !left.has_value() || samePendingMapMove(*left, *right);
}

bool samePendingDialogueContext(
    const std::optional<EventRuntimeState::PendingDialogueContext> &left,
    const std::optional<EventRuntimeState::PendingDialogueContext> &right)
{
    if (left.has_value() != right.has_value())
    {
        return false;
    }

    if (!left.has_value())
    {
        return true;
    }

    return left->kind == right->kind
        && left->sourceId == right->sourceId
        && left->sourceActorIndex == right->sourceActorIndex
        && left->hostHouseId == right->hostHouseId
        && left->newsId == right->newsId
        && left->participantPictureId == right->participantPictureId
        && left->titleOverride == right->titleOverride
        && samePendingMapMove(left->transitionMapMove, right->transitionMapMove)
        && left->boundaryTravel == right->boundaryTravel
        && left->transitionTextId == right->transitionTextId
        && left->transitionImageId == right->transitionImageId;
}

void refreshCurrentHouseServiceDialog(GameplayDialogController::Context &context, uint32_t houseId)
{
    context.eventRuntimeState.dialogueState.hostHouseId = houseId;
    setPendingDialogueContext(
        context.eventRuntimeState,
        DialogueContextKind::HouseService,
        houseId,
        houseId);
}

void queuePortraitFxRequest(
    EventRuntimeState &eventRuntimeState,
    PortraitFxEventKind kind,
    const Party *pParty)
{
    if (pParty == nullptr || kind == PortraitFxEventKind::None)
    {
        return;
    }

    EventRuntimeState::PortraitFxRequest request = {};
    request.kind = kind;
    request.memberIndices.push_back(pParty->activeMemberIndex());
    eventRuntimeState.portraitFxRequests.push_back(std::move(request));

    if (const std::optional<SoundId> soundId = soundIdForPortraitFxEvent(kind))
    {
        const uint32_t rawSoundId = static_cast<uint32_t>(*soundId);
        const bool alreadyQueued = std::any_of(
            eventRuntimeState.pendingSounds.begin(),
            eventRuntimeState.pendingSounds.end(),
            [rawSoundId](const EventRuntimeState::PendingSound &sound)
            {
                return sound.kind == EventRuntimeState::PendingSound::Kind::PlayOneShot
                    && !sound.positional
                    && sound.soundScope == SoundScope::Engine
                    && sound.soundId == rawSoundId;
            });

        if (alreadyQueued)
        {
            return;
        }

        EventRuntimeState::PendingSound sound = {};
        sound.soundId = rawSoundId;
        sound.positional = false;
        eventRuntimeState.pendingSounds.push_back(sound);
    }
}

uint32_t continentForMap(
    const MapStatsEntry *pCurrentMap,
    const MergedBolsterMapTable *pBolsterMapTable)
{
    if (pCurrentMap == nullptr)
    {
        return 0;
    }

    if (pBolsterMapTable != nullptr)
    {
        const MergedBolsterMapEntry *pBolsterMap =
            pBolsterMapTable->findById(static_cast<uint32_t>(pCurrentMap->id));

        if (pBolsterMap != nullptr && pBolsterMap->continent != 0)
        {
            return pBolsterMap->continent;
        }
    }

    if (pCurrentMap->id >= 0 && pCurrentMap->id <= 61)
    {
        return 1;
    }

    if (pCurrentMap->id >= 62 && pCurrentMap->id <= 136)
    {
        return 2;
    }

    if (pCurrentMap->id >= 137 && pCurrentMap->id <= 203)
    {
        return 3;
    }

    return 0;
}

// Pins the teacher on the journal map. A teacher with an autonote already shows in the trainer notes and has
// queued the note effect, so its pin is only drawn on the map.
bool tryAddRuntimeMapNote(
    EventRuntimeState &eventRuntimeState,
    const MasteryTeacherTopicDefinition &teacherTopic,
    uint32_t continent,
    const MapStatsEntry *pCurrentMap,
    const IGameplayWorldRuntime *pWorldRuntime,
    Party *pParty,
    bool teacherHasAutonote = false)
{
    if (pParty == nullptr || pCurrentMap == nullptr || pCurrentMap->fileName.empty() || continent == 0)
    {
        return false;
    }

    const uint32_t noteId = continent * 1000 + teacherTopic.masteryRank * 100 + teacherTopic.skillId;
    const std::string noteMapFileName = toLowerCopy(pCurrentMap->fileName);
    const std::optional<EventRuntimeState::MapNoteSourcePoint> mapNoteSourcePoint =
        eventRuntimeState.pendingDialogueContext
            ? eventRuntimeState.pendingDialogueContext->mapNoteSourcePoint
            : std::nullopt;

    if (const JournalMapNote *pExisting = pParty->findJournalMapNote(noteMapFileName, noteId))
    {
        JournalMapNote note = *pExisting;
        note.listedWithTrainerNotes = !teacherHasAutonote;

        if (mapNoteSourcePoint)
        {
            note.x = mapNoteSourcePoint->x;
            note.y = mapNoteSourcePoint->y;
        }

        pParty->setJournalMapNote(note);
        return false;
    }

    JournalMapNote note = {};
    note.id = noteId;
    // Saved: English, as every stored text (devdocs/LOCALIZATION.md).
    note.text = displaySkillName(teacherTopic.skillName) + " - " + masteryDisplayName(teacherTopic.targetMastery);
    note.mapFileName = noteMapFileName;
    note.listedWithTrainerNotes = !teacherHasAutonote;

    if (mapNoteSourcePoint)
    {
        note.x = mapNoteSourcePoint->x;
        note.y = mapNoteSourcePoint->y;
    }
    else if (pWorldRuntime != nullptr)
    {
        note.x = static_cast<int32_t>(std::lround(pWorldRuntime->partyX()));
        note.y = static_cast<int32_t>(std::lround(pWorldRuntime->partyY()));
    }

    pParty->setJournalMapNote(note);

    if (!teacherHasAutonote)
    {
        queuePortraitFxRequest(eventRuntimeState, PortraitFxEventKind::AutoNote, pParty);
    }

    return true;
}

bool tryRegisterTrainerNote(
    EventRuntimeState &eventRuntimeState,
    uint32_t topicId,
    uint32_t npcId,
    const MergedTeacherAutonoteTable *pTeacherAutonoteTable,
    const MergedTeacherTopicTable *pTeacherTopicTable,
    const MapStatsEntry *pCurrentMap,
    const MergedBolsterMapTable *pBolsterMapTable,
    const IGameplayWorldRuntime *pWorldRuntime,
    Party *pParty)
{
    const std::optional<MasteryTeacherTopicDefinition> teacherTopic =
        resolveMasteryTeacherTopic(topicId, pTeacherTopicTable);
    const std::optional<uint32_t> autonoteId =
        pTeacherAutonoteTable != nullptr
            ? pTeacherAutonoteTable->autonoteIdForTopicAndNpc(topicId, npcId)
            : std::nullopt;

    if (!autonoteId.has_value())
    {
        if (!teacherTopic.has_value())
        {
            return false;
        }

        return tryAddRuntimeMapNote(
            eventRuntimeState,
            *teacherTopic,
            continentForMap(pCurrentMap, pBolsterMapTable),
            pCurrentMap,
            pWorldRuntime,
            pParty);
    }

    bool changed = false;

    if (pParty != nullptr)
    {
        changed = !pParty->hasAutonote(*autonoteId);
        pParty->setAutonote(*autonoteId, true);
    }
    else
    {
        const uint32_t rawId = (*autonoteId << 16) | AutoNoteVariableTag;
        const auto variableIt = eventRuntimeState.variables.find(rawId);

        if (variableIt == eventRuntimeState.variables.end() || variableIt->second == 0)
        {
            eventRuntimeState.variables[rawId] = 1;
            changed = true;
        }
    }

    if (teacherTopic.has_value())
    {
        changed =
            tryAddRuntimeMapNote(
                eventRuntimeState,
                *teacherTopic,
                continentForMap(pCurrentMap, pBolsterMapTable),
                pCurrentMap,
                pWorldRuntime,
                pParty,
                true)
            || changed;
    }

    if (changed)
    {
        queuePortraitFxRequest(eventRuntimeState, PortraitFxEventKind::AutoNote, pParty);
    }

    return changed;
}

void queueUiSound(EventRuntimeState &eventRuntimeState, uint32_t soundId)
{
    if (soundId == 0)
    {
        return;
    }

    EventRuntimeState::PendingSound request = {};
    request.soundId = soundId;
    request.positional = false;
    eventRuntimeState.pendingSounds.push_back(request);
}

bool partyHasAdventurersInnRosterMember(const Party &party, uint32_t rosterId)
{
    for (const AdventurersInnMember &member : party.adventurersInnMembers())
    {
        if (member.character.rosterId == rosterId)
        {
            return true;
        }
    }

    return false;
}

bool isAdventurersInnHouse(const GameplayDialogController::Context &context, uint32_t houseId)
{
    if (context.pHouseTable == nullptr)
    {
        return houseId == DefaultAdventurersInnHouseId;
    }

    const HouseEntry *pHouseEntry = context.pHouseTable->get(houseId);
    return pHouseEntry != nullptr && pHouseEntry->name == "The Adventurer's Inn";
}

uint32_t defaultAdventurersInnHouseId(const GameplayDialogController::Context &context)
{
    if (context.pHouseTable != nullptr)
    {
        std::optional<uint32_t> selectedHouseId;

        for (const auto &[candidateHouseId, houseEntry] : context.pHouseTable->entries())
        {
            if (houseEntry.name == "The Adventurer's Inn")
            {
                if (!selectedHouseId.has_value() || candidateHouseId < *selectedHouseId)
                {
                    selectedHouseId = candidateHouseId;
                }
            }
        }

        if (selectedHouseId.has_value())
        {
            return *selectedHouseId;
        }
    }

    return DefaultAdventurersInnHouseId;
}

void syncAvailableRosterMembersToAdventurersInn(GameplayDialogController::Context &context)
{
    if (context.pParty == nullptr || context.pRosterTable == nullptr)
    {
        return;
    }

    const std::vector<const RosterEntry *> rosterEntries = context.pRosterTable->getEntriesSortedById();

    for (const RosterEntry *pRosterEntry : rosterEntries)
    {
        if (pRosterEntry == nullptr
            || pRosterEntry->unlockQuestBitId == 0
            || !context.pParty->hasQuestBit(pRosterEntry->unlockQuestBitId)
            || context.pParty->hasRosterMember(pRosterEntry->id)
            || partyHasAdventurersInnRosterMember(*context.pParty, pRosterEntry->id))
        {
            continue;
        }

        context.pParty->addAdventurersInnMember(*pRosterEntry, 0);
    }

    if (context.pNpcDialogTable == nullptr)
    {
        return;
    }

    std::vector<uint32_t> generatedMercenaryNpcIdsToMoveToInn;

    for (const auto &[npcId, recruit] : context.eventRuntimeState.generatedMercenaryRecruitsByNpcId)
    {
        if (!isAdventurersInnHouse(context, recruit.houseId)
            || context.eventRuntimeState.unavailableNpcIds.contains(npcId)
            || context.pParty->hasRosterMember(recruit.rosterId)
            || partyHasAdventurersInnRosterMember(*context.pParty, recruit.rosterId))
        {
            continue;
        }

        context.pParty->addAdventurersInnMember(recruit.character, recruit.portraitPictureId);
        generatedMercenaryNpcIdsToMoveToInn.push_back(npcId);
    }

    for (uint32_t npcId : generatedMercenaryNpcIdsToMoveToInn)
    {
        context.eventRuntimeState.generatedMercenaryRecruitsByNpcId.erase(npcId);
        context.eventRuntimeState.unavailableNpcIds.insert(npcId);
        context.eventRuntimeState.npcHouseOverrides.erase(npcId);
        context.pParty->setNpcUnavailable(npcId, true);
        context.pParty->clearNpcHouseOverride(npcId);
    }

    for (const auto &[npcId, houseId] : context.eventRuntimeState.npcHouseOverrides)
    {
        if (!isAdventurersInnHouse(context, houseId) || context.eventRuntimeState.unavailableNpcIds.contains(npcId))
        {
            continue;
        }

        const NpcEntry *pNpcEntry = context.pNpcDialogTable->getNpc(npcId);

        if (pNpcEntry == nullptr)
        {
            continue;
        }

        for (uint32_t topicId : pNpcEntry->topicIds)
        {
            const std::optional<NpcDialogTable::RosterJoinOffer> offer =
                context.pNpcDialogTable->getRosterJoinOfferForTopic(topicId);

            if (!offer.has_value()
                || context.pParty->hasRosterMember(offer->rosterId)
                || partyHasAdventurersInnRosterMember(*context.pParty, offer->rosterId))
            {
                continue;
            }

            const RosterEntry *pRosterEntry = context.pRosterTable->get(offer->rosterId);

            if (pRosterEntry != nullptr)
            {
                context.pParty->addAdventurersInnMember(*pRosterEntry, pNpcEntry->pictureId);
            }
        }
    }
}

bool tryOpenAdventurersInnOverlay(GameplayDialogController::Context &context, uint32_t houseId)
{
    if (!isAdventurersInnHouse(context, houseId) || context.pParty == nullptr)
    {
        return false;
    }

    syncAvailableRosterMembersToAdventurersInn(context);

    context.eventRuntimeState.pendingDialogueContext.reset();
    context.eventRuntimeState.dialogueState = {};
    context.uiController.clearEventDialog();

    if (context.pParty->adventurersInnMembers().empty())
    {
        context.uiController.setStatusBarEvent(Engine::tr("The Adventurer's Inn is empty."));
        return true;
    }

    GameplayUiController::CharacterScreenState &characterScreen = context.uiController.characterScreen();
    characterScreen.open = true;
    characterScreen.dollJewelryOverlayOpen = false;
    characterScreen.adventurersInnRosterOverlayOpen = true;
    characterScreen.page = GameplayUiController::CharacterPage::Inventory;
    characterScreen.source = GameplayUiController::CharacterScreenSource::AdventurersInn;
    characterScreen.sourceIndex = 0;
    characterScreen.adventurersInnScrollOffset = 0;
    return true;
}

std::optional<uint32_t> masteryTeacherTopicIdForNpc(
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState,
    const Party *pParty,
    const MergedTeacherTopicTable *pTeacherTopicTable,
    uint32_t npcId)
{
    EventRuntimeState npcRuntimeState = eventRuntimeState;

    if (pParty != nullptr)
    {
        pParty->applyGlobalNpcStateTo(npcRuntimeState);
    }

    const auto overrideIt = npcRuntimeState.npcTopicOverrides.find(npcId);
    const std::unordered_map<uint32_t, uint32_t> *pTopicOverrides =
        overrideIt != npcRuntimeState.npcTopicOverrides.end() ? &overrideIt->second : nullptr;
    const std::vector<NpcDialogTable::ResolvedTopic> topics = npcDialogTable.getTopicsForNpc(npcId, pTopicOverrides);

    for (const NpcDialogTable::ResolvedTopic &topic : topics)
    {
        if (isMasteryTeacherTopic(topic.id, pTeacherTopicTable))
        {
            return topic.id;
        }
    }

    return std::nullopt;
}

void registerTrainerNotesForNpc(
    EventRuntimeState &eventRuntimeState,
    const NpcDialogTable &npcDialogTable,
    uint32_t npcId,
    const MergedTeacherAutonoteTable *pTeacherAutonoteTable,
    const MergedTeacherTopicTable *pTeacherTopicTable,
    const MapStatsEntry *pCurrentMap,
    const MergedBolsterMapTable *pBolsterMapTable,
    const IGameplayWorldRuntime *pWorldRuntime,
    Party *pParty)
{
    EventRuntimeState npcRuntimeState = eventRuntimeState;

    if (pParty != nullptr)
    {
        pParty->applyGlobalNpcStateTo(npcRuntimeState);
    }

    const auto overrideIt = npcRuntimeState.npcTopicOverrides.find(npcId);
    const std::unordered_map<uint32_t, uint32_t> *pTopicOverrides =
        overrideIt != npcRuntimeState.npcTopicOverrides.end() ? &overrideIt->second : nullptr;
    const std::vector<NpcDialogTable::ResolvedTopic> topics = npcDialogTable.getTopicsForNpc(npcId, pTopicOverrides);

    for (const NpcDialogTable::ResolvedTopic &topic : topics)
    {
        tryRegisterTrainerNote(
            eventRuntimeState,
            topic.id,
            npcId,
            pTeacherAutonoteTable,
            pTeacherTopicTable,
            pCurrentMap,
            pBolsterMapTable,
            pWorldRuntime,
            pParty);
    }
}

const HouseEntry *pendingHouseEntry(
    const EventRuntimeState::PendingDialogueContext &context,
    const HouseTable *pHouseTable)
{
    if (pHouseTable == nullptr)
    {
        return nullptr;
    }

    const uint32_t houseId = context.kind == DialogueContextKind::HouseService ? context.sourceId : context.hostHouseId;
    return houseId != 0 ? pHouseTable->get(houseId) : nullptr;
}

const std::optional<MapEdgeTransition> *currentMapTransitionForContext(
    const GameplayDialogController::Context &context,
    const EventRuntimeState::PendingDialogueContext &dialogueContext)
{
    if (dialogueContext.kind != DialogueContextKind::MapTransition || context.pCurrentMap == nullptr)
    {
        return nullptr;
    }

    switch (static_cast<MapBoundaryEdge>(dialogueContext.sourceId))
    {
        case MapBoundaryEdge::North:
            return &context.pCurrentMap->northTransition;

        case MapBoundaryEdge::South:
            return &context.pCurrentMap->southTransition;

        case MapBoundaryEdge::East:
            return &context.pCurrentMap->eastTransition;

        case MapBoundaryEdge::West:
            return &context.pCurrentMap->westTransition;
    }

    return nullptr;
}

int boundaryTravelHeadingDegrees(MapBoundaryEdge edge)
{
    switch (edge)
    {
        case MapBoundaryEdge::North:
            return 90;

        case MapBoundaryEdge::South:
            return 270;

        case MapBoundaryEdge::East:
            return 0;

        case MapBoundaryEdge::West:
            return 180;
    }

    return 0;
}

bool applyMapTransitionTravelSideEffects(
    GameplayDialogController::Context &context,
    const MapEdgeTransition &transition)
{
    if (context.pScreenRuntime != nullptr)
    {
        context.pScreenRuntime->stopAllAudioPlayback();
    }

    const int foodRequired = mapTransitionTravelFoodRequired(context, transition);
    return context.pParty != nullptr
        && applyTravelDaysSideEffects(
            *context.pParty,
            context.pWorldRuntime,
            hiredNpcWalkingTravelDays(transition.travelDays, context.eventRuntimeState),
            foodRequired);
}

bool applyPendingMapMoveTravelSideEffects(
    GameplayDialogController::Context &context,
    const EventRuntimeState::PendingMapMove &move)
{
    const int travelDays = hiredNpcWalkingTravelDays(
        outdoorMapMoveTravelDays(context, move), context.eventRuntimeState);

    if (travelDays <= 0)
    {
        return false;
    }

    if (context.pScreenRuntime != nullptr)
    {
        context.pScreenRuntime->stopAllAudioPlayback();
    }

    return context.pParty != nullptr
        && applyTravelDaysSideEffects(
            *context.pParty,
            context.pWorldRuntime,
            travelDays,
            OutdoorMapTravelFoodCost);
}

bool executeMapTransitionHook(
    GameplayDialogController::Context &context,
    const MapEdgeTransition &transition)
{
    if (context.pWorldRuntime == nullptr)
    {
        return false;
    }

    EventRuntimeState::ActiveHookContext hookContext = {};
    hookContext.kind = EventRuntimeHookKind::MapTransition;
    hookContext.heldItemId = context.pParty != nullptr ? context.pParty->heldItemIdForQueries() : 0;
    hookContext.destinationMapName = transition.destinationMapFileName;

    if (context.eventRuntimeState.pendingDialogueContext.has_value()
        && context.eventRuntimeState.pendingDialogueContext->kind == DialogueContextKind::MapTransition)
    {
        hookContext.boundaryEdge = context.eventRuntimeState.pendingDialogueContext->sourceId;
    }

    context.eventRuntimeState.activeHookContext = std::move(hookContext);
    context.pWorldRuntime->executeEventHooks(EventRuntimeHookKind::MapTransition);

    const bool blocked = context.eventRuntimeState.activeHookContext
        && context.eventRuntimeState.activeHookContext->blocked;
    const std::optional<std::string> statusText = context.eventRuntimeState.activeHookContext
        ? context.eventRuntimeState.activeHookContext->statusText
        : std::nullopt;
    context.eventRuntimeState.activeHookContext.reset();

    if (blocked && statusText.has_value())
    {
        context.uiController.setStatusBarEvent(*statusText);
    }

    return blocked;
}

void playSpeechReaction(
    GameplayDialogController::Context &context,
    size_t memberIndex,
    SpeechId speechId,
    bool triggerFaceAnimation)
{
    if (context.pScreenRuntime != nullptr)
    {
        context.pScreenRuntime->playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
    }
}

void playHouseSound(GameplayDialogController::Context &context, uint32_t soundId)
{
    if (context.pScreenRuntime != nullptr)
    {
        context.pScreenRuntime->playHouseSound(soundId);
    }
}

std::optional<size_t> chooseRandomActablePartyMember(const Party &party)
{
    std::vector<size_t> actableMemberIndices;
    actableMemberIndices.reserve(party.members().size());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        if (GameMechanics::canAct(party.members()[memberIndex]))
        {
            actableMemberIndices.push_back(memberIndex);
        }
    }

    if (actableMemberIndices.empty())
    {
        return std::nullopt;
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    const size_t selectedIndex =
        std::uniform_int_distribution<size_t>(0, actableMemberIndices.size() - 1)(rng);
    return actableMemberIndices[selectedIndex];
}

const char *debugBoolString(bool value)
{
    return value ? "true" : "false";
}

std::string debugShopGoodbyeSoundName(
    const HouseEntry &houseEntry,
    const std::optional<HouseSoundType> &soundType)
{
    if (!soundType.has_value())
    {
        return "none";
    }

    if (isAlchemyShop(houseEntry))
    {
        if (*soundType == HouseSoundType::AlchemyShopGoodbyeBought)
        {
            return "AlchemyShopGoodbyeBought";
        }

        if (*soundType == HouseSoundType::AlchemyShopGoodbyeRegular)
        {
            return "AlchemyShopGoodbyeRegular";
        }
    }
    else
    {
        if (*soundType == HouseSoundType::ShopGoodbyePolite)
        {
            return "ShopGoodbyePolite";
        }

        if (*soundType == HouseSoundType::ShopGoodbyeRude)
        {
            return "ShopGoodbyeRude";
        }
    }

    return "HouseSoundType(" + std::to_string(static_cast<uint32_t>(*soundType)) + ")";
}

void queueDelayedSpeechReaction(
    GameplayDialogController::Context &context,
    size_t memberIndex,
    SpeechId speechId,
    float delaySeconds)
{
    if (context.pScreenRuntime != nullptr)
    {
        context.pScreenRuntime->queueDelayedSpeechReaction(memberIndex, speechId, delaySeconds);
    }
}

void playCommonUiSound(GameplayDialogController::Context &context, SoundId soundId)
{
    if (context.pScreenRuntime != nullptr)
    {
        context.pScreenRuntime->playCommonUiSound(soundId);
    }
}

void cancelMapTransition(GameplayDialogController::Context &context)
{
    const uint32_t sourceId =
        context.eventRuntimeState.pendingDialogueContext.has_value()
            ? context.eventRuntimeState.pendingDialogueContext->sourceId
            : 0;
    const std::optional<EventRuntimeState::PendingMapMove> transitionMapMove =
        context.eventRuntimeState.pendingDialogueContext
            ? context.eventRuntimeState.pendingDialogueContext->transitionMapMove
            : std::nullopt;
    context.eventRuntimeState.lastDialogueCanceled = EventRuntimeState::DialogueCanceled{
        .kind = "map_transition",
        .sourceId = sourceId,
        .activeSourceId = context.activeEventDialog.sourceId,
        .houseDialog = context.activeEventDialog.isHouseDialog,
        .actionCount = context.activeEventDialog.actions.size(),
    };
    GAMEPLAY_DEBUG_TRACE(
        "dialogue_canceled kind=map_transition source_id=" + std::to_string(sourceId)
        + " active_source_id=" + std::to_string(context.activeEventDialog.sourceId)
        + " house_dialog=" + (context.activeEventDialog.isHouseDialog ? "true" : "false"));
    if (transitionMapMove.has_value())
    {
        context.eventRuntimeState.lastMapTransitionCanceled =
            mapTransitionTrace("map_transition", sourceId, 0, 0, *transitionMapMove, false);
    }
    GAMEPLAY_DEBUG_TRACE(
        "map_transition_canceled source_kind=map_transition"
        + std::string(" source_id=") + std::to_string(sourceId)
        + (transitionMapMove ? pendingMapMoveTraceFields(*transitionMapMove) : std::string()));

    if (context.pWorldRuntime != nullptr)
    {
        context.pWorldRuntime->cancelPendingMapTransition();
    }
}

// A topic that paid the party gold and the first member experience may pay extra gold under the rules (MAW).
bool executeNpcTopicEvent(
    GameplayDialogController::Context &context,
    uint16_t eventId,
    size_t &previousMessageCount)
{
    const QuestRewardProbe rewardBefore = questRewardProbe(context);
    const bool executed = context.pWorldRuntime != nullptr
        && context.pWorldRuntime->executeNpcTopicEvent(eventId, previousMessageCount);

    if (executed)
    {
        payQuestGoldBonus(context, rewardBefore);
    }

    return executed;
}

bool executeBuiltInNpcTopic(
    GameplayDialogController::Context &context,
    uint32_t topicId)
{
    if (topicId != Mm6BountyHuntTopicId && topicId != Mm8ThisMonthsBountyTopicId)
    {
        return false;
    }

    if (context.pWorldRuntime == nullptr)
    {
        context.eventRuntimeState.messages.push_back(Engine::tr("The bounty office is unavailable right now."));
        return true;
    }

    const BountyHuntInteractionResult result =
        performBountyHuntInteraction(
            *context.pWorldRuntime,
            context.pParty,
            true,
            context.pNpcDialogTable);

    for (const std::string &message : result.messages)
    {
        context.eventRuntimeState.messages.push_back(message);
        context.uiController.setStatusBarEvent(message);
    }

    return true;
}

std::optional<NpcEntry> runtimeNpcEntry(
    const NpcDialogTable *pNpcDialogTable,
    const EventRuntimeState &eventRuntimeState,
    uint32_t npcId);

bool npcCanOfferProfessionHire(
    const NpcEntry &npc,
    const MergedNpcProfessionEntry &profession,
    bool allowProfessionBasedHire)
{
    return npc.joins || (allowProfessionBasedHire && profession.joins);
}

int currentMaximumHealth(const Character &member)
{
    return Party::effectiveMaximumHealth(member);
}

int currentMaximumSpellPoints(const Character &member)
{
    return Party::effectiveMaximumSpellPoints(member);
}

void restorePartyHealth(Party &party)
{
    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        Character *pMember = party.member(memberIndex);

        if (pMember != nullptr)
        {
            pMember->health = currentMaximumHealth(*pMember);
        }
    }
}

void clearPartyCondition(Party &party, CharacterCondition condition)
{
    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        party.clearMemberCondition(memberIndex, condition);
    }
}

void restorePartyMana(Party &party)
{
    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        Character *pMember = party.member(memberIndex);

        if (pMember != nullptr)
        {
            pMember->spellPoints = currentMaximumSpellPoints(*pMember);
        }
    }
}

void clearAllPartyConditions(Party &party)
{
    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        Character *pMember = party.member(memberIndex);

        if (pMember != nullptr)
        {
            pMember->conditions.reset();
            pMember->conditionStartGameMinutes.fill(0.0f);
        }
    }
}

void markNpcProfessionActionUsed(
    EventRuntimeState &eventRuntimeState,
    uint32_t npcId,
    const IGameplayWorldRuntime *pWorldRuntime,
    Party *pParty)
{
    const uint32_t usedDay = npcProfessionActionCooldownDay(
        pWorldRuntime != nullptr ? pWorldRuntime->gameMinutes() : -1.0f);

    for (EventRuntimeState::HiredNpcFollower &follower : eventRuntimeState.hiredNpcFollowers)
    {
        if (follower.npcId == npcId)
        {
            follower.abilityUsedDay = usedDay;
            break;
        }
    }

    if (pParty != nullptr)
    {
        pParty->setHiredNpcFollowerAbilityUsedDay(npcId, usedDay);
    }

    eventRuntimeState.variables[npcProfessionActionCooldownVariableKey(npcId)] = static_cast<int32_t>(usedDay);
}

std::vector<size_t> allPartyMemberIndices(const Party &party)
{
    std::vector<size_t> memberIndices;
    memberIndices.reserve(party.members().size());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        memberIndices.push_back(memberIndex);
    }

    return memberIndices;
}

const SpellEntry *npcFollowerSpellEntry(
    const GameplayDialogController::Context &context,
    uint32_t spellId)
{
    return context.pSpellTable != nullptr ? context.pSpellTable->findById(static_cast<int>(spellId)) : nullptr;
}

void queueNpcFollowerSpellFeedback(
    GameplayDialogController::Context &context,
    uint32_t spellId)
{
    if (context.pParty != nullptr)
    {
        EventRuntimeState::SpellFxRequest spellFxRequest = {};
        spellFxRequest.spellId = spellId;
        spellFxRequest.memberIndices = allPartyMemberIndices(*context.pParty);
        context.eventRuntimeState.spellFxRequests.push_back(std::move(spellFxRequest));
    }

    const SpellEntry *pSpellEntry = npcFollowerSpellEntry(context, spellId);

    if (pSpellEntry != nullptr && pSpellEntry->effectSoundId > 0)
    {
        EventRuntimeState::PendingSound sound = {};
        sound.soundScope = SoundScope::Engine;
        sound.soundId = pSpellEntry->effectSoundId;
        context.eventRuntimeState.pendingSounds.push_back(sound);
    }
}

bool castNpcFollowerPartySpell(
    GameplayDialogController::Context &context,
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t rawSkillMastery)
{
    if (context.pParty == nullptr)
    {
        return false;
    }

    const float durationSeconds = spellId == spellIdValue(SpellId::Bless) || spellId == spellIdValue(SpellId::Heroism)
        ? 7200.0f : 0.0f;
    if (!tryApplyEventSpellBuffs(
            *context.pParty, spellId, skillLevel, rawSkillMastery, durationSeconds, BuffSource::Hireling))
    {
        return false;
    }

    if (context.pWorldRuntime != nullptr)
    {
        context.pWorldRuntime->syncSpellMovementStatesFromPartyBuffs();
    }

    queueNpcFollowerSpellFeedback(context, spellId);
    return true;
}

struct NpcProfessionActionExecution
{
    bool handled = false;
    bool closeDialog = false;
};

NpcProfessionActionExecution executeNpcFollowerProfessionAction(
    GameplayDialogController::Context &context,
    uint32_t topicId)
{
    NpcProfessionActionExecution execution = {};

    if (!npcProfessionActionTopicHasDailyCooldown(topicId))
    {
        return execution;
    }

    execution.handled = true;

    if (context.pParty == nullptr || context.pNpcDialogTable == nullptr)
    {
        context.eventRuntimeState.messages.push_back(Engine::tr("That topic does not have an event yet."));
        return execution;
    }

    const uint32_t npcId = context.activeEventDialog.sourceId;
    const std::optional<NpcEntry> npc = runtimeNpcEntry(
        context.pNpcDialogTable,
        context.eventRuntimeState,
        npcId);
    const NpcProfessionId professionId = static_cast<NpcProfessionId>(npc ? npc->professionId : 0u);

    if (npcProfessionActionUsedToday(
            context.eventRuntimeState,
            npcId,
            context.pWorldRuntime != nullptr ? context.pWorldRuntime->gameMinutes() : -1.0f))
    {
        context.eventRuntimeState.messages.push_back(Engine::tr("Sorry, come back another day"));
        return execution;
    }

    bool applied = false;

    switch (topicId)
    {
        case static_cast<uint32_t>(NpcFollowerActionTopicId::HealParty):
            if (professionId == NpcProfessionId::Healer
                || professionId == NpcProfessionId::ExpertHealer
                || professionId == NpcProfessionId::MasterHealer)
            {
                restorePartyHealth(*context.pParty);

                if (professionId == NpcProfessionId::ExpertHealer)
                {
                    for (uint32_t condition = 0; condition < static_cast<uint32_t>(CharacterCondition::Dead);
                         ++condition)
                    {
                        clearPartyCondition(*context.pParty, static_cast<CharacterCondition>(condition));
                    }
                }
                else if (professionId == NpcProfessionId::MasterHealer)
                {
                    clearAllPartyConditions(*context.pParty);
                    restorePartyMana(*context.pParty);
                }

                applied = true;
            }
            break;

        case static_cast<uint32_t>(NpcFollowerActionTopicId::MakeFood):
            if (professionId == NpcProfessionId::Cook || professionId == NpcProfessionId::Chef)
            {
                if (context.pParty->food() >= MaxFoodForCookFollower)
                {
                    context.eventRuntimeState.messages.push_back(Engine::tr("Your packs are already full!"));
                    return execution;
                }

                const int amount = professionId == NpcProfessionId::Chef
                    ? ChefFollowerFoodAmount : CookFollowerFoodAmount;
                context.pParty->addFood(std::min(amount, MaxFoodForCookFollower - context.pParty->food()));
                applied = true;
            }
            break;

        case static_cast<uint32_t>(NpcFollowerActionTopicId::CastFly):
            applied = professionId == NpcProfessionId::WindMaster
                && castNpcFollowerPartySpell(context, spellIdValue(SpellId::Fly), 2, 4);
            break;

        case static_cast<uint32_t>(NpcFollowerActionTopicId::CastWaterWalk):
            applied = professionId == NpcProfessionId::WaterMaster
                && castNpcFollowerPartySpell(context, spellIdValue(SpellId::WaterWalk), 3, 4);
            break;

        case static_cast<uint32_t>(NpcFollowerActionTopicId::CastTownPortal):
            if (professionId == NpcProfessionId::GateMaster)
            {
                if (partyHasIndoorExitAlert(context))
                {
                    context.eventRuntimeState.messages.push_back(Engine::tr("There are hostile creatures nearby!"));
                    return execution;
                }
                markNpcProfessionActionUsed(context.eventRuntimeState, npcId, context.pWorldRuntime, context.pParty);

                const size_t casterMemberIndex =
                    context.pParty->members().empty() ? 0u : context.pParty->activeMemberIndex();
                context.uiController.openUtilitySpellOverlay(
                    GameplayUiController::UtilitySpellOverlayMode::TownPortal,
                    spellIdValue(SpellId::TownPortal),
                    casterMemberIndex);
                GameplayUiController::UtilitySpellOverlayState &overlay =
                    context.uiController.utilitySpellOverlay();
                // MMerge's Gate Master casts at Grandmaster, which ignores hostiles that wander in later.
                overlay.skillLevelOverride = 10;
                overlay.skillMasteryOverride = SkillMastery::Grandmaster;
                overlay.spendMana = false;
                overlay.applyRecovery = false;
                overlay.bypassGameplayCasterValidation = true;

                execution.closeDialog = true;
                return execution;
            }
            break;

        case static_cast<uint32_t>(NpcFollowerActionTopicId::CastBless):
            applied = professionId == NpcProfessionId::Acolyte
                && castNpcFollowerPartySpell(context, spellIdValue(SpellId::Bless), 5, 3);
            break;

        case static_cast<uint32_t>(NpcFollowerActionTopicId::CastHeroism):
            applied = professionId == NpcProfessionId::Piper
                && castNpcFollowerPartySpell(context, spellIdValue(SpellId::Heroism), 5, 3);
            break;

        default:
            break;
    }

    if (!applied)
    {
        context.eventRuntimeState.messages.push_back(Engine::tr("That topic does not have an event yet."));
        return execution;
    }

    markNpcProfessionActionUsed(context.eventRuntimeState, npcId, context.pWorldRuntime, context.pParty);
    context.eventRuntimeState.messages.push_back(Engine::tr("Done!"));
    return execution;
}

uint32_t guildMembershipVariableKey(uint32_t guildType)
{
    constexpr uint32_t GuildMembershipVariableBase = 0x80000000u;
    return GuildMembershipVariableBase | guildType;
}

uint16_t guildMembershipPartyVariableId(uint32_t guildType)
{
    constexpr uint16_t GuildMembershipPartyVariableBase = 0x8000u;
    return static_cast<uint16_t>(GuildMembershipPartyVariableBase | static_cast<uint16_t>(guildType));
}

uint32_t autonoteVariableKey(uint32_t autonoteId)
{
    return (autonoteId << 16) | AutoNoteVariableTag;
}

bool hasGuildMembership(const EventRuntimeState &runtimeState, const Party *pParty, uint32_t guildType)
{
    if (pParty != nullptr && pParty->eventVariableValue(guildMembershipPartyVariableId(guildType)) != 0)
    {
        return true;
    }

    const auto membershipIt = runtimeState.variables.find(guildMembershipVariableKey(guildType));
    return membershipIt != runtimeState.variables.end() && membershipIt->second != 0;
}

void grantGuildMembership(
    EventRuntimeState &runtimeState,
    Party *pParty,
    const NpcDialogTable::GuildMembershipOffer &offer)
{
    runtimeState.variables[guildMembershipVariableKey(offer.guildType)] = 1;

    if (pParty != nullptr)
    {
        pParty->setEventVariableValue(guildMembershipPartyVariableId(offer.guildType), 1);
    }

    if (offer.autonoteId != 0)
    {
        if (pParty != nullptr)
        {
            pParty->setAutonote(offer.autonoteId, true);
        }
        else
        {
            runtimeState.variables[autonoteVariableKey(offer.autonoteId)] = 1;
        }
    }
}

std::string npcTextOrFallback(const NpcDialogTable *pNpcDialogTable, uint32_t textId, const std::string &fallback)
{
    if (pNpcDialogTable == nullptr)
    {
        return fallback;
    }

    const std::optional<std::string> text = pNpcDialogTable->getText(textId);
    return text && !text->empty() ? Engine::localize(*text) : fallback;
}

std::optional<NpcEntry> runtimeNpcEntry(
    const NpcDialogTable *pNpcDialogTable,
    const EventRuntimeState &eventRuntimeState,
    uint32_t npcId)
{
    if (pNpcDialogTable == nullptr)
    {
        return std::nullopt;
    }

    const NpcEntry *pBaseNpc = pNpcDialogTable->getNpc(npcId);
    const bool hasRuntimeNpc =
        eventRuntimeState.npcNameOverrides.contains(npcId)
        || eventRuntimeState.npcPictureOverrides.contains(npcId)
        || eventRuntimeState.npcProfessionOverrides.contains(npcId);

    if (pBaseNpc == nullptr && !hasRuntimeNpc)
    {
        return std::nullopt;
    }

    NpcEntry entry = pBaseNpc != nullptr ? *pBaseNpc : NpcEntry{};
    entry.id = npcId;

    const std::unordered_map<uint32_t, std::string>::const_iterator nameIt =
        eventRuntimeState.npcNameOverrides.find(npcId);
    if (nameIt != eventRuntimeState.npcNameOverrides.end())
    {
        entry.name = nameIt->second;
    }

    const std::unordered_map<uint32_t, uint32_t>::const_iterator pictureIt =
        eventRuntimeState.npcPictureOverrides.find(npcId);
    if (pictureIt != eventRuntimeState.npcPictureOverrides.end())
    {
        entry.pictureId = pictureIt->second;
    }

    const std::unordered_map<uint32_t, uint32_t>::const_iterator professionIt =
        eventRuntimeState.npcProfessionOverrides.find(npcId);
    if (professionIt != eventRuntimeState.npcProfessionOverrides.end())
    {
        entry.professionId = professionIt->second;
    }

    return entry;
}

int effectiveReputationForContext(const GameplayDialogController::Context &context)
{
    return context.pWorldRuntime != nullptr
        ? effectivePartyReputation(
            context.pWorldRuntime->currentLocationReputation(),
            context.pWorldRuntime->eventRuntimeState())
        : 0;
}

int mm9TransportPrice(
    const Mm9TransportRoute &route,
    const Party &party,
    const GameplayDialogController::Context &context)
{
    return mm9TransportFare(route, party, context.pWorldRuntime);
}

int requiredNpcReputationForBtb(const MergedNpcBtbEntry &btbEntry)
{
    const std::string creed = toLowerCopy(btbEntry.creed);
    return creed == "dark"
        ? static_cast<int>(btbEntry.requiredReputation)
        : -static_cast<int>(btbEntry.requiredReputation);
}

bool hasHiredNpcFollower(const EventRuntimeState &eventRuntimeState, uint32_t npcId)
{
    return std::find_if(
        eventRuntimeState.hiredNpcFollowers.begin(),
        eventRuntimeState.hiredNpcFollowers.end(),
        [npcId](const EventRuntimeState::HiredNpcFollower &follower)
        {
            return follower.npcId == npcId;
        }) != eventRuntimeState.hiredNpcFollowers.end();
}

bool continentAllowsNpcFollowers(
    const MapStatsEntry *pCurrentMap,
    const MergedContinentSettingTable *pContinentSettingTable)
{
    if (pCurrentMap == nullptr || pContinentSettingTable == nullptr)
    {
        return true;
    }

    const MergedContinentSettingEntry *pContinentSetting =
        pContinentSettingTable->findById(pCurrentMap->mergedContinentId);

    return pContinentSetting == nullptr || pContinentSetting->npcFollowers;
}

uint32_t hiredNpcFollowerFeePercent(const EventRuntimeState &eventRuntimeState)
{
    uint32_t total = 0;

    for (const EventRuntimeState::HiredNpcFollower &follower : eventRuntimeState.hiredNpcFollowers)
    {
        total += follower.weeklyCost / 100u;
    }

    return total;
}

// A service row's tag on the conversation bar.
std::string mm9RudeServiceTag(int32_t opcode)
{
    switch (opcode)
    {
        case -2: return Engine::tr("Shop");
        case -3: return Engine::tr("Training");
        case -4: return Engine::tr("Train");
        case -5: return Engine::tr("Travel");
        case -6: return Engine::tr("Bank");
        case -7: return Engine::tr("Inn");
        case -8: return Engine::tr("Healer");
        case -10: return Engine::tr("Hire");
        case -11: return Engine::tr("Dismiss");
        case -13: return Engine::tr("Combine");
        case -14: return Engine::tr("Quest");
        case -15: return Engine::tr("Service");
        case -16: return Engine::tr("Donate");
        default: return {};
    }
}

// How the conversation bar marks a row: the row that ends the talk, a quest row (one that needs keys) not chosen
// yet, or one the party has chosen before.
EventDialogChoiceMark mm9RudeChoiceMark(const Mm9RudeRow &row, const Party &party)
{
    if (row.next == -1)
    {
        return EventDialogChoiceMark::Exit;
    }

    if (party.hasChosenMm9RudeRow(uint32_t(row.rudeId), row.rowIndex))
    {
        return EventDialogChoiceMark::Visited;
    }

    return row.requiredRawKeys.empty() ? EventDialogChoiceMark::None : EventDialogChoiceMark::New;
}

// A racial trainer's lesson for a member: the racial ability they know, at the mastery after theirs but no higher than
// the trainer teaches (at that mastery already, the shared evaluation says so). Empty for a member who knows none.
std::optional<SkillMasteryTrainingRequest> mm9RacialLesson(
    const Character &member,
    const Mm9RacialTrainer &trainer,
    const std::vector<std::string> &racialSkills)
{
    for (const std::string &skillName : racialSkills)
    {
        const CharacterSkill *pSkill = member.findSkill(skillName);

        if (pSkill != nullptr && pSkill->mastery != SkillMastery::None)
        {
            const SkillMastery nextMastery = SkillMastery(std::min(int(pSkill->mastery) + 1, int(trainer.maxMastery)));
            return SkillMasteryTrainingRequest{.skillName = skillName, .targetMastery = nextMastery};
        }
    }

    return std::nullopt;
}

EventDialogContent buildMm9RudeContent(
    const Mm9RudeDialogueTable &table,
    const Mm9SkillTrainerTable *pSkillTrainerTable,
    Party &party,
    uint32_t rudeId,
    int32_t nodeId,
    const std::optional<std::string> &response,
    std::optional<uint32_t> sourceActorIndex)
{
    EventDialogContent content = {};
    content.isActive = true;
    content.sourceId = rudeId;
    discoverActorTeacher(party, rudeId);
    content.dialogueNodeId = nodeId;
    content.sourceActorIndex = sourceActorIndex;
    content.presentation = EventDialogPresentation::Mm9Rude;
    // MM9's dialogue tables stay English; the interface language's text is looked up where it is shown.
    content.title = Engine::localize(table.npcName(rudeId));
    if (content.title.empty())
    {
        content.title = Engine::tr("NPC {id}", {{"id", rudeId}});
    }

    if (response.has_value())
    {
        if (!response->empty())
        {
            content.lines.push_back(Engine::localize(*response));
        }
    }
    else
    {
        const std::string blurb = table.topBlurb(rudeId);
        if (!blurb.empty())
        {
            content.lines.push_back(Engine::localize(blurb));
        }
    }

    const std::vector<const Mm9RudeRow *> visibleRows = table.visibleRows(rudeId, nodeId, party);
    for (const Mm9RudeRow *pRow : visibleRows)
    {
        const Mm9SkillTrainerService *pTrainerService = pSkillTrainerTable != nullptr
            ? pSkillTrainerTable->find(static_cast<uint32_t>(pRow->rudeId), pRow->rowIndex)
            : nullptr;
        if (pTrainerService != nullptr)
        {
            EventDialogAction action = {};
            action.kind = EventDialogActionKind::Mm9RudeSkillTrainerOffer;
            action.id = static_cast<uint32_t>(pRow->rowIndex);
            action.label = Engine::localize(pRow->prompt, Mm9PartyLineContext);
            action.argument = "trainer=" + std::to_string(pTrainerService->topic.rawTrainerId)
                + ";source_line=" + std::to_string(pRow->sourceLine);
            action.choiceMark = mm9RudeChoiceMark(*pRow, party);
            action.choiceTag = Engine::tr("Train \xC2\xB7 {mastery}",
                {{"mastery", Engine::localize(masteryDisplayName(pTrainerService->topic.targetMastery), "mastery")}});
            content.actions.push_back(std::move(action));
            continue;
        }

        EventDialogAction action = {};
        action.kind = EventDialogActionKind::Mm9RudeTopic;
        action.id = static_cast<uint32_t>(pRow->rowIndex);
        action.secondaryId = static_cast<uint32_t>(pRow->sourceLine);
        action.label = Engine::localize(pRow->prompt, Mm9PartyLineContext);
        action.argument = "choice=" + std::to_string(pRow->choiceSlot)
            + ";next=" + std::to_string(pRow->next);
        action.choiceMark = mm9RudeChoiceMark(*pRow, party);
        action.choiceTag = pRow->next < -1 ? mm9RudeServiceTag(pRow->next) : std::string();
        content.actions.push_back(std::move(action));
    }

    // A promotion quest done, its promoter's first page keeps offering the promotion to the members eligible now
    // (before the row that ends the talk).
    const Mm9PromotionService *pPromotion = table.promotionService(rudeId);
    if (pPromotion != nullptr && nodeId == int32_t(rudeId)
        && party.hasQuestBit(*mm9QBitForRawQuestKey(pPromotion->doneRawKey)))
    {
        EventDialogAction action = {};
        action.kind = EventDialogActionKind::Mm9RudePromotionService;
        action.label = Engine::tr("Promote our eligible characters.");
        action.choiceTag = Engine::tr("Promotion");
        const auto exitRow = std::find_if(content.actions.begin(), content.actions.end(),
            [](const EventDialogAction &existing) { return existing.choiceMark == EventDialogChoiceMark::Exit; });
        content.actions.insert(exitRow, std::move(action));
    }

    // A racial trainer's first page offers the members' racial-ability lessons (dialogue/racial_trainers.yml).
    if (table.racialTrainer(rudeId) != nullptr && nodeId == int32_t(rudeId))
    {
        EventDialogAction action = {};
        action.kind = EventDialogActionKind::Mm9RudeRacialTrainerOffer;
        action.label = Engine::tr("We want to train our racial abilities.");
        action.choiceTag = Engine::tr("Train");
        const auto exitRow = std::find_if(content.actions.begin(), content.actions.end(),
            [](const EventDialogAction &existing) { return existing.choiceMark == EventDialogChoiceMark::Exit; });
        content.actions.insert(exitRow, std::move(action));
    }

    // A lost-item keeper's first page offers to give back a lost quest item (dialogue/lost_items.yml).
    if (table.isLostItemKeeper(rudeId) && nodeId == int32_t(rudeId))
    {
        EventDialogAction action = {};
        action.kind = EventDialogActionKind::Mm9RudeLostItemService;
        action.label = Engine::tr("We've lost something.");
        const auto exitRow = std::find_if(content.actions.begin(), content.actions.end(),
            [](const EventDialogAction &existing) { return existing.choiceMark == EventDialogChoiceMark::Exit; });
        content.actions.insert(exitRow, std::move(action));
    }

    // The ruleset's rows on this person's first page (rulesets/<id>/worlds/mm9/dialogue.yml: MAW's skill reset and
    // Dimensional Maps on Hjordisa the Hag, the Jarls' bounties).
    if (nodeId == int32_t(rudeId))
    {
        for (const Mm9RulesetRow *pRow : table.rulesetRows(rudeId))
        {
            EventDialogAction action = {};
            if (pRow->bountyMapFileName.empty())
            {
                action.kind = EventDialogActionKind::Mm9RudeRulesetEvent;
                action.id = pRow->eventId;
                action.label = Engine::localize(pRow->label);
            }
            else
            {
                action.kind = EventDialogActionKind::Mm9RudeBountyOffice;
                action.argument = pRow->bountyMapFileName;
                action.label = Engine::tr("Bounty hunt");
                action.choiceTag = Engine::tr("Bounty");
            }
            const auto exitRow = std::find_if(content.actions.begin(), content.actions.end(),
                [](const EventDialogAction &existing) { return existing.choiceMark == EventDialogChoiceMark::Exit; });
            content.actions.insert(exitRow, std::move(action));
        }
    }

    return content;
}

// The MM9 hirelings' RUDE services (devdocs/mm9/MM9_HIRELINGS_PLAN.md phase 7): -10 hire, -11 dismiss and -15 the
// hireling's own service, for the dialogue's RUDE id.
GameplayDialogController::Result executeMm9HirelingRudeRow(
    GameplayDialogController::Context &context,
    const Mm9RudeRow &row,
    GameplayDialogController::Result result)
{
    Party &party = *context.pParty;
    const uint32_t rudeId = context.activeEventDialog.sourceId;
    const Mm9HirelingTable *pTable = party.mm9HirelingTable();
    const Mm9Hireling *pHireling = pTable != nullptr ? pTable->find(rudeId) : nullptr;

    if (pHireling == nullptr)
    {
        // Huber Carryall's hire row: no table row, so MM9's error sound and nothing else (cshell@0x10028b0d).
        party.requestSound(SoundId::Error);
        return result;
    }

    if (row.next == -10)
    {
        const Mm9HireOutcome outcome = hireMm9Hireling(party, *pHireling);

        if (outcome == Mm9HireOutcome::Refused)
        {
            party.requestSound(SoundId::Error);
            return result;
        }

        if (outcome == Mm9HireOutcome::Declines)
        {
            if (const std::optional<FollowerHireRefusal> refusal = party.rules().classes.paidHirelingRefusal())
            {
                context.uiController.setStatusBarEvent(refusal->message);
            }

            party.requestSound(SoundId::Error);
            return result;
        }

        if (outcome == Mm9HireOutcome::NotEnoughGold)
        {
            context.uiController.setStatusBarEvent(Engine::tr("You don't have enough gold."));
            playSpeechReaction(context, party.activeMemberIndex(), SpeechId::NotEnoughGold, true);
            return result;
        }

        // The row's own keys (Forad's 29 and 371), then MM9's server hides the speaking body at once
        // (object@0x100b6bd3); the maps' scripts keep it hidden on later loads while the hire key is held.
        applyMm9RudeRowActions(row, party, &context.eventRuntimeState);
        party.recordChosenMm9RudeRow(rudeId, row.rowIndex);

        // A posed talking prop (Ake) goes as evt.SetSprite(cog, 0) hides it, kept in the map's event state.
        const std::optional<uint32_t> decorationKey =
            context.eventRuntimeState.dialogueState.mm9RudeSourceDecorationKey;

        if (context.activeEventDialog.sourceActorIndex)
        {
            hideMapActorByIndex(context.eventRuntimeState, *context.activeEventDialog.sourceActorIndex);
        }
        else if (decorationKey)
        {
            context.eventRuntimeState.spriteOverrides[*decorationKey].hidden = true;
            ++context.eventRuntimeState.indoorLightRevision;
        }

        if ((context.activeEventDialog.sourceActorIndex || decorationKey) && context.pWorldRuntime != nullptr)
        {
            context.pWorldRuntime->applyEventRuntimeState();
        }

        context.uiController.setStatusBarEvent(
            Engine::tr("{name} joins the party.", {{"name", Engine::localize(pHireling->name)}}));
        executeMm9RudeExitCallback(context);
        result.shouldCloseActiveDialog = true;
        return result;
    }

    if (row.next == -11)
    {
        applyMm9RudeRowActions(row, party, &context.eventRuntimeState);
        party.recordChosenMm9RudeRow(rudeId, row.rowIndex);

        if (dismissMm9Hireling(party, *pHireling))
        {
            context.uiController.setStatusBarEvent(
                Engine::tr("{name} leaves the party.", {{"name", Engine::localize(pHireling->name)}}));
        }

        executeMm9RudeExitCallback(context);
        result.shouldCloseActiveDialog = true;
        return result;
    }

    const Mm9HirelingServiceOutcome outcome = useMm9HirelingService(party, *pHireling);

    if (outcome == Mm9HirelingServiceOutcome::Unavailable)
    {
        party.requestSound(SoundId::Error);
        return result;
    }

    if (outcome == Mm9HirelingServiceOutcome::CoolingDown)
    {
        context.uiController.setStatusBarEvent(mm9HirelingServiceCooldownText(Engine::localize(pHireling->name)));

        if (pHireling->service != Mm9HirelingService::TownPortal)
        {
            party.requestSound(SoundId::Fizzle);
        }

        return result;
    }

    party.recordChosenMm9RudeRow(rudeId, row.rowIndex);

    if (outcome == Mm9HirelingServiceOutcome::TownPortal)
    {
        // Ehwaz casts Town Portal for the party (cshell@0x1002aee3): the spell's destination choice, free.
        const size_t casterMemberIndex = party.members().empty() ? 0u : party.activeMemberIndex();
        context.uiController.openUtilitySpellOverlay(
            GameplayUiController::UtilitySpellOverlayMode::TownPortal,
            spellIdValue(SpellId::TownPortal),
            casterMemberIndex);
        GameplayUiController::UtilitySpellOverlayState &overlay = context.uiController.utilitySpellOverlay();
        overlay.skillLevelOverride = 10;
        overlay.skillMasteryOverride = SkillMastery::Grandmaster;
        overlay.spendMana = false;
        overlay.applyRecovery = false;
        overlay.bypassGameplayCasterValidation = true;
        executeMm9RudeExitCallback(context);
        result.shouldCloseActiveDialog = true;
        return result;
    }

    // Healed: the conversation goes on with the row's response.
    const bool exitCallbackExecuted = context.activeEventDialog.mm9RudeExitCallbackExecuted;
    context.activeEventDialog = buildMm9RudeContent(
        *context.pMm9RudeDialogueTable,
        context.pMm9SkillTrainerTable,
        party,
        rudeId,
        context.activeEventDialog.dialogueNodeId,
        row.response,
        context.activeEventDialog.sourceActorIndex);
    context.activeEventDialog.mm9RudeExitCallbackExecuted = exitCallbackExecuted;
    context.activeEventDialog.echo =
        row.response.empty() ? std::string() : Engine::localize(row.prompt, Mm9PartyLineContext);
    context.selectionIndex = 0;
    context.uiController.setStatusBarEvent(
        Engine::tr("{name} heals the party.", {{"name", Engine::localize(pHireling->name)}}));
    return result;
}
}

GameplayDialogController::Result GameplayDialogController::executeActiveDialogAction(Context &context) const
{
    Result result = {};
    result.previousMessageCount = context.eventRuntimeState.messages.size();

    if (!context.activeEventDialog.isActive
        || (!context.actionOverride && context.selectionIndex >= context.activeEventDialog.actions.size()))
    {
        return result;
    }

    const EventDialogAction &action = context.actionOverride
        ? *context.actionOverride
        : context.activeEventDialog.actions[context.selectionIndex];
    traceDialogState(context.activeEventDialog, "before_topic_clicked");
    GAMEPLAY_DEBUG_TRACE(
        "topic_clicked kind=" + std::string(eventDialogActionKindName(action.kind))
        + " action_id=" + std::to_string(action.id)
        + " secondary_id=" + std::to_string(action.secondaryId)
        + " selection_index=" + std::to_string(context.selectionIndex)
        + " source_id=" + std::to_string(context.activeEventDialog.sourceId)
        + " house_dialog=" + (context.activeEventDialog.isHouseDialog ? "true" : "false")
        + " enabled=" + (action.enabled ? "true" : "false")
        + " label=\"" + action.label + "\"");

    context.uiController.closeHouseShopOverlay();
    context.uiController.closeTransportSchedule();

    if (context.uiController.inventoryNestedOverlay().active && context.dialogueHudActive)
    {
        context.uiController.closeInventoryNestedOverlay();
    }

    if (!action.enabled)
    {
        if (action.kind == EventDialogActionKind::HouseService)
        {
            if (!action.disabledReason.empty()
                && static_cast<HouseActionId>(action.id) != HouseActionId::TrainingTrainActiveMember)
            {
                context.uiController.setStatusBarEvent(action.disabledReason);
            }

            return result;
        }

        if (!action.disabledReason.empty())
        {
            context.eventRuntimeState.messages.push_back(action.disabledReason);
            result.shouldOpenPendingEventDialog = true;
        }

        return result;
    }

    if (action.kind == EventDialogActionKind::Mm9RudeSkillTrainerBack
        || action.kind == EventDialogActionKind::Mm9RudeTransportBack)
    {
        if (context.pMm9RudeDialogueTable == nullptr
            || context.pParty == nullptr
            || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude)
        {
            return result;
        }

        const bool exitCallbackExecuted = context.activeEventDialog.mm9RudeExitCallbackExecuted;
        context.activeEventDialog = buildMm9RudeContent(
            *context.pMm9RudeDialogueTable,
            context.pMm9SkillTrainerTable,
            *context.pParty,
            context.activeEventDialog.sourceId,
            context.activeEventDialog.dialogueNodeId,
            std::nullopt,
            context.activeEventDialog.sourceActorIndex);
        context.activeEventDialog.mm9RudeExitCallbackExecuted = exitCallbackExecuted;
        context.selectionIndex = 0;
        return result;
    }

    if (action.kind == EventDialogActionKind::Mm9RudePromotionService)
    {
        const Mm9PromotionService *pPromotion = context.pMm9RudeDialogueTable != nullptr
            ? context.pMm9RudeDialogueTable->promotionService(context.activeEventDialog.sourceId)
            : nullptr;
        if (pPromotion == nullptr || context.pParty == nullptr || context.pWorldRuntime == nullptr
            || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude)
        {
            return result;
        }

        // mm9_common.lua promotes (the one class-line table); the members whose class changed are the answer.
        std::vector<std::string> classesBefore;
        for (size_t memberIndex = 0; memberIndex < context.pParty->memberCount(); ++memberIndex)
        {
            classesBefore.push_back(context.pParty->member(memberIndex)->className);
        }

        EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.npcId = context.activeEventDialog.sourceId;
        hookContext.actorIndex = context.activeEventDialog.sourceActorIndex;
        hookContext.mm9Promotion = pPromotion->promotion;
        const std::optional<EventRuntimeState::ActiveHookContext> previousHookContext =
            context.eventRuntimeState.activeHookContext;
        context.eventRuntimeState.activeHookContext = std::move(hookContext);
        size_t previousMessageCount = context.eventRuntimeState.messages.size();
        context.pWorldRuntime->executeMapEvent(Mm9PromotionServiceEventId, previousMessageCount);
        context.eventRuntimeState.activeHookContext = previousHookContext;

        std::vector<std::string> lines;
        for (size_t memberIndex = 0; memberIndex < classesBefore.size(); ++memberIndex)
        {
            const Character *pMember = context.pParty->member(memberIndex);
            if (pMember != nullptr && pMember->className != classesBefore[memberIndex])
            {
                lines.push_back(Engine::tr("{name} is now a {class}.",
                    {{"name", pMember->name}, {"class", displayClassName(pMember->className)}}));
            }
        }
        if (lines.empty())
        {
            lines.push_back(Engine::tr("No one among you can take this promotion now."));
        }

        const bool exitCallbackExecuted = context.activeEventDialog.mm9RudeExitCallbackExecuted;
        context.activeEventDialog = buildMm9RudeContent(
            *context.pMm9RudeDialogueTable,
            context.pMm9SkillTrainerTable,
            *context.pParty,
            context.activeEventDialog.sourceId,
            context.activeEventDialog.dialogueNodeId,
            std::string(),
            context.activeEventDialog.sourceActorIndex);
        context.activeEventDialog.lines = std::move(lines);
        context.activeEventDialog.mm9RudeExitCallbackExecuted = exitCallbackExecuted;
        context.activeEventDialog.echo = Engine::tr("Promote our eligible characters.");
        context.selectionIndex = 0;
        return result;
    }

    if (action.kind == EventDialogActionKind::Mm9RudeRulesetEvent
        || action.kind == EventDialogActionKind::Mm9RudeBountyOffice)
    {
        if (context.pMm9RudeDialogueTable == nullptr || context.pParty == nullptr || context.pWorldRuntime == nullptr
            || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude)
        {
            return result;
        }

        // The event's messages (evt.SetMessage) or the bounty office's answer are the person's reply.
        std::vector<std::string> lines;
        if (action.kind == EventDialogActionKind::Mm9RudeRulesetEvent)
        {
            const size_t firstMessage = context.eventRuntimeState.messages.size();
            size_t previousMessageCount = firstMessage;
            executeNpcTopicEvent(context, uint16_t(action.id), previousMessageCount);
            lines.assign(context.eventRuntimeState.messages.begin() + std::ptrdiff_t(firstMessage),
                         context.eventRuntimeState.messages.end());
        }
        else
        {
            const MapStatsEntry *pMap = nullptr;
            for (size_t index = 0; context.pMapEntries != nullptr && index < context.pMapEntries->size(); ++index)
            {
                if (toLowerCopy((*context.pMapEntries)[index].fileName) == toLowerCopy(action.argument))
                {
                    pMap = &(*context.pMapEntries)[index];
                }
            }

            if (pMap == nullptr)
            {
                lines.push_back(Engine::tr("The bounty office is unavailable right now."));
            }
            else
            {
                const BountyHuntRemoteMap remote = {pMap->name, pMap->fileName};
                lines = performBountyHuntInteraction(
                    *context.pWorldRuntime, context.pParty, true, context.pNpcDialogTable, &remote).messages;
            }
        }

        const bool exitCallbackExecuted = context.activeEventDialog.mm9RudeExitCallbackExecuted;
        context.activeEventDialog = buildMm9RudeContent(
            *context.pMm9RudeDialogueTable,
            context.pMm9SkillTrainerTable,
            *context.pParty,
            context.activeEventDialog.sourceId,
            context.activeEventDialog.dialogueNodeId,
            std::string(),
            context.activeEventDialog.sourceActorIndex);
        context.activeEventDialog.lines = std::move(lines);
        context.activeEventDialog.mm9RudeExitCallbackExecuted = exitCallbackExecuted;
        context.activeEventDialog.echo = action.label;
        context.selectionIndex = 0;
        return result;
    }

    if (action.kind == EventDialogActionKind::Mm9RudeLostItemService)
    {
        if (context.pMm9RudeDialogueTable == nullptr || context.pParty == nullptr
            || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude)
        {
            return result;
        }

        // The first item the party has owned, holds nowhere now and has not handed in (MM9.takeItem records the
        // hand-in as the named global MM9.HandedIn.<raw>).
        Party &party = *context.pParty;
        const ItemTable *pItemTable = party.itemTable();
        std::string line = Engine::tr("You never had anything I could give back.");
        for (const Mm9LostItem &lost : context.pMm9RudeDialogueTable->lostItems())
        {
            const auto handedIn = context.eventRuntimeState.namedGlobalVars.find(
                "MM9.HandedIn." + std::to_string(lost.rawItemId));
            if (!party.hasEverOwnedItem(lost.itemId) || party.hasItemAnywhere(lost.itemId)
                || (handedIn != context.eventRuntimeState.namedGlobalVars.end() && handedIn->second != 0)
                || pItemTable == nullptr)
            {
                continue;
            }

            const InventoryItem item = ItemGenerator::makeInventoryItem(
                lost.itemId,
                *pItemTable,
                ItemGenerationMode::Generic);
            const ItemDefinition *pDefinition = pItemTable->get(lost.itemId);
            const std::string itemName = pDefinition != nullptr ? pDefinition->name : std::string();
            if (!party.tryGrantInventoryItem(item))
            {
                line = Engine::tr("I have your {item}, but your packs are full.", {{"item", itemName}});
                break;
            }

            party.requestSound(SoundId::Gold);
            line = Engine::tr("Here is your {item}. Try not to lose it again.", {{"item", itemName}});
            break;
        }

        const bool exitCallbackExecuted = context.activeEventDialog.mm9RudeExitCallbackExecuted;
        context.activeEventDialog = buildMm9RudeContent(
            *context.pMm9RudeDialogueTable,
            context.pMm9SkillTrainerTable,
            party,
            context.activeEventDialog.sourceId,
            context.activeEventDialog.dialogueNodeId,
            std::string(),
            context.activeEventDialog.sourceActorIndex);
        context.activeEventDialog.lines = {line};
        context.activeEventDialog.mm9RudeExitCallbackExecuted = exitCallbackExecuted;
        context.activeEventDialog.echo = Engine::tr("We've lost something.");
        context.selectionIndex = 0;
        return result;
    }

    if (action.kind == EventDialogActionKind::Mm9RudeTransportSchedule)
    {
        if (context.activeEventDialog.presentation == EventDialogPresentation::Mm9Rude)
        {
            context.uiController.openMm9TransportSchedule(context.activeEventDialog.sourceId);
        }

        return result;
    }

    if (action.kind == EventDialogActionKind::Mm9RudeTransportRoute)
    {
        if (context.pMm9TransportRouteTable == nullptr
            || context.pParty == nullptr
            || context.pWorldRuntime == nullptr
            || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude)
        {
            return result;
        }

        // Today's boat, or (from the Schedule) the boat of a later weekday, which the party waits for.
        const int today = (int(mm9TransportDayIndex(context.pWorldRuntime->gameMinutes())) + 5) % 7;
        const int departureDay = action.secondaryId > 0 ? int(action.secondaryId) - 1 : today;
        const Mm9TransportRoute *pRoute = context.pMm9TransportRouteTable->findByCanonicalId(action.argument);
        if (pRoute == nullptr || pRoute->dockNpcId != context.activeEventDialog.sourceId
            || departureDay < 0 || departureDay > 6 || mm9TransportWeekday(*pRoute) != departureDay
            || !mm9TransportRouteConditionsSatisfied(*pRoute, *context.pParty))
        {
            context.uiController.setStatusBarEvent(Engine::tr("That route is not available."));
            return result;
        }

        const int price = mm9TransportPrice(*pRoute, *context.pParty, context);
        if (context.pParty->gold() < price)
        {
            context.uiController.setStatusBarEvent(Engine::tr("You don't have enough gold."));
            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::NotEnoughGold, true);
            return result;
        }

        // The party eats while it waits for the departure, as at an MM6-MM8 dock.
        const int waitDays = transportWaitDays(today, departureDay);
        const int waitFood = waitDays * transportWaitFoodPerDay();
        if (context.pParty->food() < waitFood)
        {
            context.uiController.setStatusBarEvent(Engine::trn("You don't have enough food to wait {days} day.",
                "You don't have enough food to wait {days} days.", uint64_t(waitDays), {{"days", waitDays}}));
            return result;
        }

        context.pParty->addGold(-price, GoldReason::Travel);
        if (waitDays > 0)
        {
            context.pParty->addFood(-waitFood);
            const float waitMinutes = float(waitDays) * 24.0f * 60.0f;
            context.pWorldRuntime->advanceGameMinutes(waitMinutes);
            context.pParty->advanceTimedStates(waitMinutes * 60.0f);
        }
        // MM9's boats arrive at 6:00 in the morning, the route's travel days after the departure date (a two-day trip
        // that leaves on Monday arrives on Wednesday at 6:00). The party rests on board, as on any journey.
        context.pParty->restAndHealAll();
        {
            constexpr double MinutesPerDay = 24.0 * 60.0;
            constexpr double ArrivalMinuteOfDay = 6.0 * 60.0;
            const double departure = context.pWorldRuntime->gameMinutes();
            const double arrival = (std::floor(departure / MinutesPerDay) + double(pRoute->travelDays)) * MinutesPerDay
                + ArrivalMinuteOfDay;
            const float travelMinutes = float(std::max(0.0, arrival - departure));

            if (travelMinutes > 0.0f)
            {
                context.pWorldRuntime->advanceGameMinutes(travelMinutes);
                context.pParty->advanceTimedStates(travelMinutes * 60.0f);
            }
        }

        if (PlaythroughStatistics *pStatistics = context.pParty->statistics())
        {
            pStatistics->recordTravel(false, double(waitDays) + double(pRoute->travelDays));
        }

        EventRuntimeState::PendingMapMove pendingMove = {};
        pendingMove.travelTimeApplied = true;
        pendingMove.mapName = pRoute->destinationMapFileName;
        pendingMove.x = pRoute->arrivalX;
        pendingMove.y = pRoute->arrivalY;
        pendingMove.z = pRoute->arrivalZ;
        pendingMove.directionDegrees = static_cast<int32_t>(std::lround(pRoute->facingDegrees));
        pendingMove.useMapStartPosition = false;
        pendingMove.useFullscreenLoading = true;
        pendingMove.traceSourceKind = "mm9_boat_route";
        pendingMove.traceSourceId = pRoute->dockNpcId;
        pendingMove.traceActionId = static_cast<uint32_t>(action.kind);
        pendingMove.traceDestinationName = pRoute->destinationName;
        context.eventRuntimeState.lastMapTransitionRequested = EventRuntimeState::MapTransitionTrace{
            .sourceKind = pendingMove.traceSourceKind,
            .sourceId = pRoute->dockNpcId,
            .actionId = pendingMove.traceActionId,
            .routeIndex = pRoute->routeOrder,
            .confirmationRequired = false,
            .destinationMap = pRoute->destinationMapFileName,
            .destinationName = pRoute->destinationName,
            .travelDays = pRoute->travelDays,
            .useStartPosition = false,
            .x = pRoute->arrivalX,
            .y = pRoute->arrivalY,
            .z = pRoute->arrivalZ,
            .directionDegrees = pendingMove.directionDegrees,
        };
        context.eventRuntimeState.pendingMapMove = std::move(pendingMove);
        context.uiController.setStatusBarEvent(
            Engine::trn("It will take {days} day to travel to {destination}.",
                "It will take {days} days to travel to {destination}.", uint64_t(pRoute->travelDays),
                {{"days", pRoute->travelDays}, {"destination", Engine::localize(pRoute->destinationName)}}));
        executeMm9RudeExitCallback(context);
        result.shouldCloseActiveDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::Mm9RudeRacialTrainerOffer
        || action.kind == EventDialogActionKind::Mm9RudeRacialTrainerLearn)
    {
        const Mm9RacialTrainer *pTrainer = context.pMm9RudeDialogueTable != nullptr
            ? context.pMm9RudeDialogueTable->racialTrainer(context.activeEventDialog.sourceId)
            : nullptr;
        if (pTrainer == nullptr
            || context.pParty == nullptr
            || context.pClassSkillTable == nullptr
            || context.pNpcDialogTable == nullptr
            || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude)
        {
            return result;
        }

        // Each member's own racial ability at their next mastery, on a row per member like a skill trainer's: the
        // lesson and its price, or why that member cannot take it (shown muted).
        Party &party = *context.pParty;
        const std::vector<std::string> &racialSkills = context.pMm9RudeDialogueTable->racialAbilitySkills();
        const auto evaluate = [&](size_t memberIndex) -> std::optional<MasteryTeacherEvaluation>
        {
            const std::optional<SkillMasteryTrainingRequest> lesson =
                mm9RacialLesson(*party.member(memberIndex), *pTrainer, racialSkills);
            if (!lesson)
            {
                MasteryTeacherEvaluation none = {};
                none.displayText = Engine::tr("No racial ability to train.");
                return none;
            }
            // At this trainer's mastery already: a member who can go further is sent to a grandmaster; one who
            // cannot hears why (the class, or the promotion it needs).
            const Character &member = *party.member(memberIndex);
            const CharacterSkill *pSkill = member.findSkill(lesson->skillName);
            if (pSkill->mastery >= pTrainer->maxMastery && pSkill->mastery < SkillMastery::Grandmaster)
            {
                SkillMasteryTrainingRequest further = *lesson;
                further.targetMastery = SkillMastery(int(pSkill->mastery) + 1);
                if (context.pClassSkillTable->getEffectiveCap(member.className, member.raceId, lesson->skillName)
                    >= further.targetMastery)
                {
                    MasteryTeacherEvaluation beyond = {};
                    beyond.displayText = Engine::tr("Seek a grandmaster to go further in {skill}.",
                        {{"skill", Engine::localize(displaySkillName(lesson->skillName), "skill")}});
                    return beyond;
                }
                return evaluateSkillMasteryTraining(
                    further, party, memberIndex, *context.pClassSkillTable, *context.pNpcDialogTable);
            }
            return evaluateSkillMasteryTraining(
                *lesson, party, memberIndex, *context.pClassSkillTable, *context.pNpcDialogTable);
        };

        // The page: the topic quoted, the reply, then the member rows and Back in place of the talk's rows.
        const auto openPage = [&](const std::optional<std::string> &reply)
        {
            const bool exitCallbackExecuted = context.activeEventDialog.mm9RudeExitCallbackExecuted;
            context.activeEventDialog = buildMm9RudeContent(
                *context.pMm9RudeDialogueTable,
                context.pMm9SkillTrainerTable,
                party,
                context.activeEventDialog.sourceId,
                context.activeEventDialog.dialogueNodeId,
                reply,
                context.activeEventDialog.sourceActorIndex);
            context.activeEventDialog.mm9RudeExitCallbackExecuted = exitCallbackExecuted;
            context.activeEventDialog.echo = Engine::tr("We want to train our racial abilities.");
            context.activeEventDialog.actions.clear();

            std::optional<size_t> firstApproved;
            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                const std::optional<MasteryTeacherEvaluation> evaluation = evaluate(memberIndex);
                if (!evaluation || evaluation->displayText.empty())
                {
                    continue;
                }

                EventDialogAction learnAction = {};
                learnAction.kind = EventDialogActionKind::Mm9RudeRacialTrainerLearn;
                learnAction.memberIndex = memberIndex;
                learnAction.label = Engine::tr("{member}: {lesson}",
                    {{"member", party.member(memberIndex)->name}, {"lesson", evaluation->displayText}});
                if (evaluation->approved)
                {
                    learnAction.choiceTag = Engine::tr("Train \xC2\xB7 {mastery}",
                        {{"mastery", Engine::localize(masteryDisplayName(evaluation->targetMastery), "mastery")}});
                    firstApproved = firstApproved ? firstApproved : context.activeEventDialog.actions.size();
                }
                else
                {
                    learnAction.choiceMark = EventDialogChoiceMark::Locked;
                }
                context.activeEventDialog.actions.push_back(std::move(learnAction));
            }

            EventDialogAction backAction = {};
            backAction.kind = EventDialogActionKind::Mm9RudeSkillTrainerBack;
            backAction.label = Engine::tr("Back");
            backAction.choiceMark = EventDialogChoiceMark::Exit;
            context.activeEventDialog.actions.push_back(std::move(backAction));
            context.selectionIndex = firstApproved.value_or(0);
        };

        if (action.kind == EventDialogActionKind::Mm9RudeRacialTrainerOffer)
        {
            openPage(Engine::tr("Let us see what your blood allows."));
            return result;
        }

        // A member's lesson: trained, the reply says so and the rows show the new state; refused, the row says why.
        const size_t memberIndex = action.memberIndex;
        const std::optional<MasteryTeacherEvaluation> evaluation = evaluate(memberIndex);
        const std::optional<SkillMasteryTrainingRequest> lesson = memberIndex < party.members().size()
            ? mm9RacialLesson(*party.member(memberIndex), *pTrainer, racialSkills)
            : std::nullopt;
        std::string message;
        if (!evaluation || !evaluation->approved || !lesson
            || !applySkillMasteryTraining(
                *lesson, party, memberIndex, *context.pClassSkillTable, *context.pNpcDialogTable, message))
        {
            if (evaluation && !evaluation->displayText.empty())
            {
                context.uiController.setStatusBarEvent(evaluation->displayText);
            }
            return result;
        }

        context.uiController.setStatusBarEvent(message);
        playSpeechReaction(context, memberIndex, SpeechId::SkillMasteryIncreased, true);
        openPage(message);
        return result;
    }

    if (action.kind == EventDialogActionKind::Mm9RudeSkillTrainerOffer
        || action.kind == EventDialogActionKind::Mm9RudeSkillTrainerSkill
        || action.kind == EventDialogActionKind::Mm9RudeSkillTrainerLearn)
    {
        const EventDialogActionKind trainerActionKind = action.kind;
        const uint32_t trainerRowIndex = action.id;
        const uint32_t trainerSkillIndex = action.secondaryId;
        const size_t trainerMemberIndex = action.memberIndex;

        if (context.pMm9RudeDialogueTable == nullptr
            || context.pParty == nullptr
            || context.pClassSkillTable == nullptr
            || context.pNpcDialogTable == nullptr
            || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude)
        {
            return result;
        }

        const Mm9RudeRow *pRow = context.pMm9RudeDialogueTable->rowByIndex(
            context.activeEventDialog.sourceId,
            trainerRowIndex);
        const Mm9SkillTrainerService *pTrainerService =
            pRow != nullptr && context.pMm9SkillTrainerTable != nullptr
                ? context.pMm9SkillTrainerTable->find(
                    context.activeEventDialog.sourceId,
                    trainerRowIndex)
                : nullptr;
        if (pRow == nullptr
            || pRow->nodeId != context.activeEventDialog.dialogueNodeId
            || pTrainerService == nullptr
            || (trainerActionKind != EventDialogActionKind::Mm9RudeSkillTrainerOffer
                && trainerSkillIndex >= pTrainerService->topic.skillNames.size()))
        {
            context.uiController.setStatusBarEvent("MM9 skill trainer topic is no longer valid.");
            return result;
        }

        // Each skill the trainer teaches is its own lesson with the shared single-skill mastery training: its own
        // price, requirement and class/race cap (no composite MM9 skills, user decision 2026-11-05). The talk hides
        // the party, so a lesson is offered to every member on its own row (user, 2026-11-06): a trainer of several
        // skills first lists its skills, then the chosen skill's members; one of a single skill lists the members.
        Party &party = *context.pParty;
        const Mm9RudeSkillTrainerTopic &trainerTopic = pTrainerService->topic;
        const bool severalSkills = trainerTopic.skillNames.size() > 1;
        const std::string masteryName = Engine::localize(masteryDisplayName(trainerTopic.targetMastery), "mastery");
        const std::string trainTag = Engine::tr("Train \xC2\xB7 {mastery}", {{"mastery", masteryName}});
        const auto trainingRequest = [&trainerTopic](size_t skillIndex)
        {
            return SkillMasteryTrainingRequest{
                .skillName = trainerTopic.skillNames[skillIndex],
                .targetMastery = trainerTopic.targetMastery,
                .requiredGold = trainerTopic.requiredGold,
                .requiredSkill = trainerTopic.requiredSkillRank,
            };
        };
        const auto evaluate = [&](size_t skillIndex, size_t memberIndex)
        {
            return evaluateSkillMasteryTraining(
                trainingRequest(skillIndex),
                party,
                memberIndex,
                *context.pClassSkillTable,
                *context.pNpcDialogTable);
        };

        // A trainer page: the topic's sentence quoted, the reply, then rows that replace the talk's.
        const auto openPage = [&](const std::optional<std::string> &reply)
        {
            const bool exitCallbackExecuted = context.activeEventDialog.mm9RudeExitCallbackExecuted;
            context.activeEventDialog = buildMm9RudeContent(
                *context.pMm9RudeDialogueTable,
                context.pMm9SkillTrainerTable,
                party,
                context.activeEventDialog.sourceId,
                context.activeEventDialog.dialogueNodeId,
                reply,
                context.activeEventDialog.sourceActorIndex);
            context.activeEventDialog.mm9RudeExitCallbackExecuted = exitCallbackExecuted;
            context.activeEventDialog.echo = Engine::localize(pRow->prompt, Mm9PartyLineContext);
            context.activeEventDialog.actions.clear();
            context.selectionIndex = 0;
        };

        // The skill's rows, one per member in party order: the lesson and its price, or why that member cannot take
        // it (shown muted). The selection starts on the first member who can.
        const auto listMembers = [&](size_t skillIndex)
        {
            std::optional<size_t> firstApproved;

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                const std::optional<MasteryTeacherEvaluation> evaluation = evaluate(skillIndex, memberIndex);

                if (!evaluation || evaluation->displayText.empty())
                {
                    continue;
                }

                EventDialogAction learnAction = {};
                learnAction.kind = EventDialogActionKind::Mm9RudeSkillTrainerLearn;
                learnAction.id = trainerRowIndex;
                learnAction.secondaryId = static_cast<uint32_t>(skillIndex);
                learnAction.memberIndex = memberIndex;
                learnAction.label = Engine::tr("{member}: {lesson}",
                    {{"member", party.member(memberIndex)->name}, {"lesson", evaluation->displayText}});

                if (evaluation->approved)
                {
                    learnAction.choiceTag = trainTag;
                    firstApproved = firstApproved ? firstApproved : context.activeEventDialog.actions.size();
                }
                else
                {
                    learnAction.choiceMark = EventDialogChoiceMark::Locked;
                }

                context.activeEventDialog.actions.push_back(std::move(learnAction));
            }

            // Back to the skills of a trainer that has several, else to the talk.
            EventDialogAction backAction = {};
            backAction.kind = severalSkills
                ? EventDialogActionKind::Mm9RudeSkillTrainerOffer : EventDialogActionKind::Mm9RudeSkillTrainerBack;
            backAction.id = trainerRowIndex;
            backAction.label = Engine::tr("Back");
            backAction.choiceMark = EventDialogChoiceMark::Exit;
            context.activeEventDialog.actions.push_back(std::move(backAction));
            context.selectionIndex = firstApproved.value_or(0);
        };

        if (trainerActionKind == EventDialogActionKind::Mm9RudeSkillTrainerOffer)
        {
            party.recordChosenMm9RudeRow(context.activeEventDialog.sourceId, pRow->rowIndex);
            openPage(selectMm9RudeRow(*pRow).response);

            if (!severalSkills)
            {
                listMembers(0);
                return result;
            }

            // The skills, each with how many members can take its lesson now; none, and it is shown muted.
            for (size_t skillIndex = 0; skillIndex < trainerTopic.skillNames.size(); ++skillIndex)
            {
                size_t learners = 0;

                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    const std::optional<MasteryTeacherEvaluation> evaluation = evaluate(skillIndex, memberIndex);
                    learners += evaluation && evaluation->approved ? 1 : 0;
                }

                EventDialogAction skillAction = {};
                skillAction.kind = EventDialogActionKind::Mm9RudeSkillTrainerSkill;
                skillAction.id = trainerRowIndex;
                skillAction.secondaryId = static_cast<uint32_t>(skillIndex);
                skillAction.label = Engine::tr("{mastery} {skill}",
                    {{"mastery", masteryName},
                     {"skill", Engine::localize(displaySkillName(trainerTopic.skillNames[skillIndex]), "skill")}});

                if (learners > 0)
                {
                    skillAction.choiceTag = Engine::tr("{learners} of {members} can learn",
                        {{"learners", learners}, {"members", party.members().size()}});
                }
                else
                {
                    skillAction.choiceMark = EventDialogChoiceMark::Locked;
                }

                context.activeEventDialog.actions.push_back(std::move(skillAction));
            }

            EventDialogAction backAction = {};
            backAction.kind = EventDialogActionKind::Mm9RudeSkillTrainerBack;
            backAction.label = Engine::tr("Back");
            backAction.choiceMark = EventDialogChoiceMark::Exit;
            context.activeEventDialog.actions.push_back(std::move(backAction));
            return result;
        }

        if (trainerActionKind == EventDialogActionKind::Mm9RudeSkillTrainerSkill)
        {
            openPage(selectMm9RudeRow(*pRow).response);
            listMembers(trainerSkillIndex);
            return result;
        }

        // A member's lesson: trained, the reply says so and the rows show the new state; refused, the row already
        // says why.
        std::string message;
        if (!applySkillMasteryTraining(
                trainingRequest(trainerSkillIndex),
                party,
                trainerMemberIndex,
                *context.pClassSkillTable,
                *context.pNpcDialogTable,
                message))
        {
            const std::optional<MasteryTeacherEvaluation> evaluation = evaluate(trainerSkillIndex, trainerMemberIndex);
            if (evaluation && !evaluation->displayText.empty())
            {
                context.uiController.setStatusBarEvent(evaluation->displayText);
            }
            return result;
        }

        context.uiController.setStatusBarEvent(message);
        playSpeechReaction(context, trainerMemberIndex, SpeechId::SkillMasteryIncreased, true);
        openPage(message);
        listMembers(trainerSkillIndex);
        return result;
    }

    if (action.kind == EventDialogActionKind::Mm9RudeTopic)
    {
        if (context.pMm9RudeDialogueTable == nullptr
            || context.pParty == nullptr
            || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude)
        {
            return result;
        }

        const Mm9RudeRow *pRow = context.pMm9RudeDialogueTable->rowByIndex(
            context.activeEventDialog.sourceId,
            action.id);
        if (pRow == nullptr || pRow->nodeId != context.activeEventDialog.dialogueNodeId)
        {
            context.uiController.setStatusBarEvent("MM9 dialogue row is no longer valid.");
            return result;
        }

        if (pRow->next == -10 || pRow->next == -11 || pRow->next == -15)
        {
            return executeMm9HirelingRudeRow(context, *pRow, result);
        }

        applyMm9RudeRowActions(*pRow, *context.pParty, &context.eventRuntimeState);
        context.pParty->recordChosenMm9RudeRow(context.activeEventDialog.sourceId, pRow->rowIndex);
        const Mm9RudeSelection selection = selectMm9RudeRow(*pRow);
        if (selection.kind == Mm9RudeSelectionKind::Close)
        {
            const bool nextDialog = endMm9RudeTalk(context);
            result.shouldOpenPendingEventDialog = nextDialog;
            result.shouldCloseActiveDialog = !nextDialog;
            return result;
        }

        const int32_t nextNodeId = selection.kind == Mm9RudeSelectionKind::GotoNode
            ? selection.next
            : context.activeEventDialog.dialogueNodeId;
        const size_t previousSelectionIndex = context.selectionIndex;
        const bool exitCallbackExecuted = context.activeEventDialog.mm9RudeExitCallbackExecuted;
        context.activeEventDialog = buildMm9RudeContent(
            *context.pMm9RudeDialogueTable,
            context.pMm9SkillTrainerTable,
            *context.pParty,
            context.activeEventDialog.sourceId,
            nextNodeId,
            selection.response,
            context.activeEventDialog.sourceActorIndex);
        context.activeEventDialog.mm9RudeExitCallbackExecuted = exitCallbackExecuted;
        context.activeEventDialog.echo =
            selection.response.empty() ? std::string() : Engine::localize(pRow->prompt, Mm9PartyLineContext);
        context.selectionIndex = 0;

        if (selection.kind == Mm9RudeSelectionKind::Service)
        {
            if (selection.serviceOpcode == -2
                || selection.serviceOpcode == -3
                || selection.serviceOpcode == -6
                || selection.serviceOpcode == -7
                || selection.serviceOpcode == -8
                || selection.serviceOpcode == -16)
            {
                const bool isShopService = selection.serviceOpcode == -2;
                const HouseEntry *pVenue = nullptr;
                if (context.pHouseTable != nullptr)
                {
                    pVenue = isShopService
                        ? context.pHouseTable->resolvePackageSourceVendorId(
                            "mm9",
                            context.activeEventDialog.sourceId)
                        : context.pHouseTable->resolvePackageSourceServiceId(
                            "mm9",
                            context.activeEventDialog.sourceId);
                }
                if (pVenue == nullptr)
                {
                    context.uiController.setStatusBarEvent(
                        "MM9 " + mm9RudeServiceName(selection.serviceOpcode) + " "
                            + std::to_string(context.activeEventDialog.sourceId)
                            + " has no mounted service definition.");
                    return result;
                }

                const HouseServiceType serviceType = resolveHouseServiceType(*pVenue);
                const bool serviceMatches =
                    (selection.serviceOpcode == -2 && serviceType == HouseServiceType::Shop)
                    || (selection.serviceOpcode == -3 && serviceType == HouseServiceType::TrainingHall)
                    || (selection.serviceOpcode == -6 && serviceType == HouseServiceType::Bank)
                    || (selection.serviceOpcode == -7 && serviceType == HouseServiceType::Tavern)
                    || (selection.serviceOpcode == -8
                        && serviceType == HouseServiceType::Temple
                        && pVenue->templeCanHeal)
                    || (selection.serviceOpcode == -16
                        && serviceType == HouseServiceType::Temple
                        && pVenue->templeCanDonate);
                if (!serviceMatches)
                {
                    context.uiController.setStatusBarEvent(
                        "MM9 " + mm9RudeServiceName(selection.serviceOpcode) + " service definition is invalid.");
                    return result;
                }

                context.eventRuntimeState.dialogueState.suspendedMm9RudeDialogue =
                    EventRuntimeState::SuspendedMm9RudeDialogue{
                        .rudeId = context.activeEventDialog.sourceId,
                        .nodeId = nextNodeId,
                        .sourceActorIndex = context.activeEventDialog.sourceActorIndex,
                        .sourceDecorationKey = context.eventRuntimeState.dialogueState.mm9RudeSourceDecorationKey,
                        .response = selection.response,
                        .selectionIndex = static_cast<uint32_t>(previousSelectionIndex),
                        .exitCallbackExecuted = exitCallbackExecuted,
                    };
                context.eventRuntimeState.dialogueState.hostHouseId = pVenue->id;
                context.eventRuntimeState.dialogueState.menuStack.clear();
                setPendingDialogueContext(
                    context.eventRuntimeState,
                    DialogueContextKind::HouseService,
                    pVenue->id,
                    pVenue->id);
                result.shouldOpenPendingEventDialog = true;
                return result;
            }

            if (selection.serviceOpcode == -5)
            {
                context.activeEventDialog.actions.clear();
                const uint8_t dayIndex = context.pWorldRuntime != nullptr
                    ? mm9TransportDayIndex(context.pWorldRuntime->gameMinutes())
                    : 0;
                const Mm9TransportRoute *pRoute = context.pMm9TransportRouteTable != nullptr
                    ? context.pMm9TransportRouteTable->findForServiceDay(
                        context.activeEventDialog.sourceId,
                        dayIndex)
                    : nullptr;
                if (pRoute != nullptr && context.pParty != nullptr
                    && mm9TransportRouteConditionsSatisfied(*pRoute, *context.pParty))
                {
                    const int price = mm9TransportPrice(*pRoute, *context.pParty, context);
                    EventDialogAction routeAction = {};
                    routeAction.kind = EventDialogActionKind::Mm9RudeTransportRoute;
                    routeAction.id = pRoute->sourceDayIndex;
                    routeAction.label = Engine::trn("{days} day to {destination} for {price} gold",
                        "{days} days to {destination} for {price} gold", uint64_t(pRoute->travelDays),
                        {{"days", pRoute->travelDays},
                         {"destination", Engine::localize(pRoute->destinationName)},
                         {"price", price}});
                    routeAction.argument = pRoute->canonicalId;
                    context.activeEventDialog.actions.push_back(std::move(routeAction));
                }
                else
                {
                    context.activeEventDialog.lines.push_back(Engine::tr("Sorry, come back another day."));
                }

                // The week's boats, in the transport Schedule popup.
                if (context.pMm9TransportRouteTable != nullptr && context.pParty != nullptr
                    && !buildMm9TransportSchedule(*context.pMm9TransportRouteTable, context.activeEventDialog.sourceId,
                        context.pParty, context.pWorldRuntime).routes.empty())
                {
                    EventDialogAction scheduleAction = {};
                    scheduleAction.kind = EventDialogActionKind::Mm9RudeTransportSchedule;
                    scheduleAction.label = Engine::tr("Schedule");
                    context.activeEventDialog.actions.push_back(std::move(scheduleAction));
                }

                EventDialogAction backAction = {};
                backAction.kind = EventDialogActionKind::Mm9RudeTransportBack;
                backAction.label = Engine::tr("Back");
                backAction.choiceMark = EventDialogChoiceMark::Exit;
            backAction.choiceMark = EventDialogChoiceMark::Exit;
                context.activeEventDialog.actions.push_back(std::move(backAction));
                context.selectionIndex = 0;
                return result;
            }

            context.activeEventDialog.actions.clear();
            context.uiController.setStatusBarEvent(
                "MM9 " + mm9RudeServiceName(selection.serviceOpcode) + " service is not implemented yet.");
        }
        else if (selection.kind == Mm9RudeSelectionKind::Unresolved)
        {
            context.activeEventDialog.actions.clear();
            context.uiController.setStatusBarEvent("MM9 dialogue action 0 is unresolved.");
        }

        return result;
    }

    if (action.kind == EventDialogActionKind::MapTransitionConfirm
        || action.kind == EventDialogActionKind::MapTransitionReset)
    {
        if (context.pParty != nullptr)
        {
            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::Yes, true);
        }

        if (!context.eventRuntimeState.pendingDialogueContext.has_value())
        {
            result.shouldCloseActiveDialog = true;
            return result;
        }

        if (context.eventRuntimeState.pendingDialogueContext->transitionMapMove.has_value()
            && !context.eventRuntimeState.pendingDialogueContext->boundaryTravel)
        {
            const Mm9MapTransition *pMm9Transition = pendingMm9PositionedTransition(
                context,
                *context.eventRuntimeState.pendingDialogueContext);
            logMapTransitionConfirmed(
                context.eventRuntimeState,
                *context.eventRuntimeState.pendingDialogueContext,
                *context.eventRuntimeState.pendingDialogueContext->transitionMapMove,
                action.id);
            if (pMm9Transition != nullptr && context.eventRuntimeState.lastMapTransitionConfirmed)
            {
                EventRuntimeState::MapTransitionTrace &trace =
                    *context.eventRuntimeState.lastMapTransitionConfirmed;
                trace.sourceKind = "mm9_exit_trigger";
                trace.sourceId = pMm9Transition->sourceObjectIndex;
                trace.travelDays = static_cast<uint32_t>(std::max(0, pMm9Transition->travelDays));
            }

            if (context.pScreenRuntime != nullptr)
            {
                context.pScreenRuntime->stopAllAudioPlayback();
            }

            bool travelTimeApplied = false;

            if (pMm9Transition != nullptr && context.pParty != nullptr)
            {
                // A walk between two regions is MM6-MM8's journey between outdoor maps: guides shorten the road
                // and it costs five food; any other exit with days on the road costs a food a day.
                const bool regionWalk = context.pCurrentMap != nullptr
                    && mm9RegionWalk(
                        pMm9Transition->travelDays,
                        context.pMapEntries,
                        context.pCurrentMap->fileName,
                        pMm9Transition->destinationMapFileName);
                const int travelDays = regionWalk
                    ? hiredNpcWalkingTravelDays(pMm9Transition->travelDays, context.eventRuntimeState)
                    : std::max(0, pMm9Transition->travelDays);
                if (regionWalk && context.eventRuntimeState.lastMapTransitionConfirmed)
                {
                    context.eventRuntimeState.lastMapTransitionConfirmed->travelDays = uint32_t(travelDays);
                }
                travelTimeApplied = applyTravelDaysSideEffects(
                    *context.pParty,
                    context.pWorldRuntime,
                    travelDays,
                    regionWalk ? Mm9RegionWalkFood : travelDays);
            }
            else
            {
                travelTimeApplied = applyPendingMapMoveTravelSideEffects(
                    context,
                    *context.eventRuntimeState.pendingDialogueContext->transitionMapMove);
            }
            context.eventRuntimeState.pendingMapMove =
                *context.eventRuntimeState.pendingDialogueContext->transitionMapMove;
            context.eventRuntimeState.pendingMapMove->travelTimeApplied = travelTimeApplied;

            if (action.kind == EventDialogActionKind::MapTransitionReset
                && context.eventRuntimeState.pendingMapMove->mapName)
            {
                gameRulesFor(context.pParty).monsters.resetMap(*context.eventRuntimeState.pendingMapMove->mapName);
            }

            result.shouldCloseActiveDialog = true;
            return result;
        }

        const std::optional<MapEdgeTransition> *pTransition =
            currentMapTransitionForContext(context, *context.eventRuntimeState.pendingDialogueContext);

        if (pTransition == nullptr || !pTransition->has_value())
        {
            result.shouldCloseActiveDialog = true;
            return result;
        }

        if (executeMapTransitionHook(context, **pTransition))
        {
            cancelMapTransition(context);
            result.shouldCloseActiveDialog = true;
            return result;
        }

        const bool travelTimeApplied = applyMapTransitionTravelSideEffects(context, **pTransition);

        EventRuntimeState::PendingMapMove pendingMapMove = {};

        if (context.eventRuntimeState.pendingDialogueContext->transitionMapMove.has_value())
        {
            // Edge travel: the arrival was taken from where the party reached the edge.
            pendingMapMove = *context.eventRuntimeState.pendingDialogueContext->transitionMapMove;
        }
        else
        {
            pendingMapMove.mapName = (*pTransition)->destinationMapFileName;
            pendingMapMove.directionDegrees = (*pTransition)->directionDegrees;
            pendingMapMove.useMapStartPosition = (*pTransition)->useMapStartPosition;
            pendingMapMove.startPointName = mapStartPointName((*pTransition)->arrivalSide);
            assignMapMoveTraceSource(
                pendingMapMove,
                dialogueContextKindName(context.eventRuntimeState.pendingDialogueContext->kind),
                context.eventRuntimeState.pendingDialogueContext->sourceId,
                action.id,
                0,
                (*pTransition)->destinationMapFileName);

            if (context.eventRuntimeState.pendingDialogueContext->kind == DialogueContextKind::MapTransition)
            {
                pendingMapMove.directionDegrees = boundaryTravelHeadingDegrees(
                    static_cast<MapBoundaryEdge>(context.eventRuntimeState.pendingDialogueContext->sourceId));
            }

            if (!(*pTransition)->useMapStartPosition
                && (*pTransition)->arrivalX.has_value()
                && (*pTransition)->arrivalY.has_value()
                && (*pTransition)->arrivalZ.has_value())
            {
                pendingMapMove.x = *(*pTransition)->arrivalX;
                pendingMapMove.y = *(*pTransition)->arrivalY;
                pendingMapMove.z = *(*pTransition)->arrivalZ;
            }
        }

        pendingMapMove.travelTimeApplied = travelTimeApplied;

        logMapTransitionConfirmed(
            context.eventRuntimeState,
            *context.eventRuntimeState.pendingDialogueContext,
            pendingMapMove,
            action.id);
        context.eventRuntimeState.lastMapTransitionConfirmed->travelDays =
            hiredNpcWalkingTravelDays((*pTransition)->travelDays, context.eventRuntimeState);
        context.eventRuntimeState.pendingMapMove = std::move(pendingMapMove);
        result.shouldCloseActiveDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::MapTransitionCancel)
    {
        cancelMapTransition(context);
        result.shouldCloseActiveDialog = true;
        return result;
    }

    // An event's choice box: the event continues at the chosen answer's step; a new message or prompt shows in the
    // dialog, otherwise it closes.
    if (action.kind == EventDialogActionKind::EventChoice)
    {
        if (context.pWorldRuntime == nullptr || !context.eventRuntimeState.pendingInputPrompt
            || context.eventRuntimeState.pendingInputPrompt->kind != EventRuntimeState::PendingInputPrompt::Kind::Choice)
        {
            result.shouldCloseActiveDialog = true;
            return result;
        }

        const EventRuntimeState::PendingInputPrompt prompt = *context.eventRuntimeState.pendingInputPrompt;
        context.eventRuntimeState.pendingInputPrompt.reset();
        const uint8_t step = action.id < prompt.answerContinueSteps.size() && prompt.answerContinueSteps[action.id] != 0
            ? prompt.answerContinueSteps[action.id] : prompt.continueStep;
        context.eventRuntimeState.messages.clear();
        size_t previousMessageCount = 0;
        const bool executed = context.pWorldRuntime->executeMapEvent(prompt.eventId, previousMessageCount, step);

        if (executed
            && (context.eventRuntimeState.pendingInputPrompt || !context.eventRuntimeState.messages.empty()))
        {
            setPendingDialogueContext(context.eventRuntimeState, DialogueContextKind::MapEvent,
                context.activeEventDialog.sourceId, 0);
            result.previousMessageCount = 0;
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        context.eventRuntimeState.pendingDialogueContext.reset();
        result.shouldCloseActiveDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::HouseService)
    {
        if (context.pParty == nullptr || context.pHouseTable == nullptr)
        {
            return result;
        }

        const HouseEntry *pHouseEntry = context.pHouseTable->get(context.activeEventDialog.sourceId);

        if (pHouseEntry == nullptr)
        {
            return result;
        }

        if (rejectClosedHouseInteraction(context, *pHouseEntry))
        {
            return result;
        }

        const HouseActionId houseActionId = static_cast<HouseActionId>(action.id);
        const DialogueMenuId menuId = dialogueMenuIdForHouseAction(houseActionId);

        if (houseActionId == HouseActionId::ExtraExit)
        {
            if (!pHouseEntry->extraExit.has_value())
            {
                return result;
            }

            const HouseEntry::ExtraExit &extraExit = *pHouseEntry->extraExit;

            if (extraExit.requiredQuestBit != 0
                && (context.pParty == nullptr || !context.pParty->hasQuestBit(extraExit.requiredQuestBit)))
            {
                return result;
            }

            if (context.pScreenRuntime != nullptr)
            {
                context.pScreenRuntime->stopAllAudioPlayback();
            }

            GAMEPLAY_DEBUG_TRACE(
                "house_extra_exit source_id=" + std::to_string(pHouseEntry->id)
                + " action_id=" + std::to_string(action.id)
                + " label=\"" + action.label + "\""
                + " destination_map=\"" + extraExit.destinationMapFileName + "\""
                + " destination_name=\"" + extraExit.destinationName + "\""
                + " destination_map_id=" + std::to_string(extraExit.destinationMapId)
                + " required_qbit=" + std::to_string(extraExit.requiredQuestBit)
                + " use_start_position=" + (extraExit.useMapStartPosition ? "true" : "false")
                + " pos=(" + std::to_string(extraExit.x)
                + "," + std::to_string(extraExit.y)
                + "," + std::to_string(extraExit.z) + ")");

            EventRuntimeState::PendingMapMove pendingMapMove = {};
            pendingMapMove.mapName = extraExit.destinationMapFileName;
            pendingMapMove.x = extraExit.x;
            pendingMapMove.y = extraExit.y;
            pendingMapMove.z = extraExit.z;
            pendingMapMove.useMapStartPosition = extraExit.useMapStartPosition;
            assignMapMoveTraceSource(
                pendingMapMove,
                "house_extra_exit",
                pHouseEntry->id,
                action.id,
                0,
                extraExit.destinationName);
            logMapTransitionRequested(
                context.eventRuntimeState,
                "house_extra_exit",
                pHouseEntry->id,
                action.id,
                0,
                pendingMapMove,
                false);
            context.eventRuntimeState.pendingMapMove = std::move(pendingMapMove);
            result.shouldCloseActiveDialog = true;
            return result;
        }

        if (menuId != DialogueMenuId::None)
        {
            context.eventRuntimeState.dialogueState.menuStack.push_back(menuId);
        }
        else if (houseActionId == HouseActionId::TavernArcomageRules)
        {
            if (context.pNpcDialogTable != nullptr)
            {
                const std::optional<std::string> text = context.pNpcDialogTable->getText(ArcomageRulesTextId);

                if (text.has_value() && !text->empty())
                {
                    context.eventRuntimeState.messages.push_back(*text);
                }
            }

            refreshCurrentHouseServiceDialog(context, pHouseEntry->id);
            result.shouldOpenPendingEventDialog = true;
            return result;
        }
        else if (houseActionId == HouseActionId::TavernArcomageVictoryConditions)
        {
            if (context.pNpcDialogTable != nullptr && context.pArcomageLibrary != nullptr)
            {
                const ArcomageTavernRule *pRule = context.pArcomageLibrary->ruleForHouse(pHouseEntry->id);

                if (pRule != nullptr)
                {
                    const std::optional<std::string> text = context.pNpcDialogTable->getText(pRule->victoryTextId);

                    if (text.has_value() && !text->empty())
                    {
                        context.eventRuntimeState.messages.push_back(*text);
                    }
                }
            }

            refreshCurrentHouseServiceDialog(context, pHouseEntry->id);
            result.shouldOpenPendingEventDialog = true;
            return result;
        }
        else if (houseActionId == HouseActionId::TavernArcomagePlay)
        {
            if (!partyCanPlayArcomageInHouse(*pHouseEntry, context.pParty))
            {
                const std::string message = arcomageDeckRequiredMessage();
                context.eventRuntimeState.messages.push_back(message);
                context.uiController.setStatusBarEvent(message);
                refreshCurrentHouseServiceDialog(context, pHouseEntry->id);
                result.shouldOpenPendingEventDialog = true;
                return result;
            }

            EventRuntimeState::PendingArcomageGame pendingGame = {};
            pendingGame.houseId = pHouseEntry->id;
            context.eventRuntimeState.pendingArcomageGame = std::move(pendingGame);
            return result;
        }
        else if (houseActionId == HouseActionId::TransportSchedule)
        {
            context.uiController.openTransportSchedule(pHouseEntry->id);
            return result;
        }
        else if (houseActionId == HouseActionId::BankDepositAll)
        {
            context.uiController.beginHouseBankInput(pHouseEntry->id, GameplayUiController::HouseBankInputMode::Deposit);
            return result;
        }
        else if (houseActionId == HouseActionId::BankWithdrawAll)
        {
            context.uiController.beginHouseBankInput(pHouseEntry->id, GameplayUiController::HouseBankInputMode::Withdraw);
            return result;
        }
        else if (houseActionId == HouseActionId::ShopBuyStandard)
        {
            context.uiController.openHouseShopOverlay(
                pHouseEntry->id,
                GameplayUiController::HouseShopMode::BuyStandard);
            return result;
        }
        else if (houseActionId == HouseActionId::ShopBuySpecial)
        {
            context.uiController.openHouseShopOverlay(
                pHouseEntry->id,
                GameplayUiController::HouseShopMode::BuySpecial);
            return result;
        }
        else if (houseActionId == HouseActionId::GuildBuySpellbooks)
        {
            // A guild of several schools lists one shelf per school, its index in the option's argument.
            context.uiController.openHouseShopOverlay(
                pHouseEntry->id,
                GameplayUiController::HouseShopMode::BuySpellbooks,
                action.argument.empty() ? 0 : uint32_t(std::stoul(action.argument)));
            return result;
        }
        else if (houseActionId == HouseActionId::ShopSell)
        {
            context.uiController.openInventoryNestedOverlay(
                GameplayUiController::InventoryNestedOverlayMode::ShopSell,
                pHouseEntry->id);
            return result;
        }
        else if (houseActionId == HouseActionId::ShopIdentify)
        {
            context.uiController.openInventoryNestedOverlay(
                GameplayUiController::InventoryNestedOverlayMode::ShopIdentify,
                pHouseEntry->id);
            return result;
        }
        else if (houseActionId == HouseActionId::ShopRepair)
        {
            context.uiController.openInventoryNestedOverlay(
                GameplayUiController::InventoryNestedOverlayMode::ShopRepair,
                pHouseEntry->id);
            return result;
        }
        else
        {
            HouseActionOption option = {};
            option.id = houseActionId;
            option.label = action.label;
            option.argument = action.argument;
            const HouseActionResult houseResult = performHouseAction(
                option,
                *pHouseEntry,
                *context.pParty,
                context.pClassSkillTable,
                context.pWorldRuntime,
                context.pNpcDialogTable
            );

            if (houseResult.soundType.has_value())
            {
                const std::optional<uint32_t> soundId = deriveHouseSoundId(*pHouseEntry, *houseResult.soundType);

                if (soundId.has_value())
                {
                    playHouseSound(context, *soundId);
                }
            }

            const bool suppressDialogueMessages =
                option.id == HouseActionId::TrainingTrainActiveMember
                || option.id == HouseActionId::TempleDonate;

            for (const std::string &message : houseResult.messages)
            {
                if (!suppressDialogueMessages)
                {
                    context.eventRuntimeState.messages.push_back(message);
                }

                context.uiController.setStatusBarEvent(message);
            }

            if (houseResult.succeeded
                && option.id == HouseActionId::TrainingTrainActiveMember)
            {
                playSpeechReaction(
                    context,
                    context.pParty->activeMemberIndex(),
                    SpeechId::LevelUp,
                    true);
            }

            if (houseResult.speechId != SpeechId::None)
            {
                playSpeechReaction(
                    context,
                    context.pParty->activeMemberIndex(),
                    houseResult.speechId,
                    true);
            }

            for (SpeechId speechId : houseResult.additionalSpeechIds)
            {
                if (speechId != SpeechId::None)
                {
                    playSpeechReaction(context, context.pParty->activeMemberIndex(), speechId, true);
                }
            }

            // The ledger bought: back to the tavern's topics, which no longer offer it.
            std::vector<DialogueMenuId> &menuStack = context.eventRuntimeState.dialogueState.menuStack;

            if (houseResult.succeeded && option.id == HouseActionId::BuyTeacherLedger && !menuStack.empty()
                && menuStack.back() == DialogueMenuId::TeacherLedger)
            {
                menuStack.pop_back();
            }

            if (houseResult.succeeded && option.id == HouseActionId::TempleHeal)
            {
                playCommonUiSound(context, SoundId::Heal);
            }

            if (houseResult.succeeded
                && option.id == HouseActionId::TempleDonate)
            {
                playSpeechReaction(
                    context,
                    context.pParty->activeMemberIndex(),
                    SpeechId::TempleDonate,
                    true);
                playSpeechReaction(
                    context,
                    context.pParty->activeMemberIndex(),
                    SpeechId::ThankYou,
                    true);
            }

            if (houseResult.succeeded
                && (option.id == HouseActionId::TransportRoute
                    || option.id == HouseActionId::TransportScheduledTrip))
            {
                playSpeechReaction(
                    context,
                    context.pParty->activeMemberIndex(),
                    isBoatHouse(*pHouseEntry) ? SpeechId::TravelBoat : SpeechId::TravelHorse,
                    true);
            }

            if (houseResult.pendingInnRest.has_value())
            {
                result.shouldCloseActiveDialog = true;
                result.pendingInnRest = houseResult.pendingInnRest;
                return result;
            }
        }

        context.eventRuntimeState.dialogueState.hostHouseId = context.activeEventDialog.sourceId;
        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::HouseService,
            context.activeEventDialog.sourceId,
            context.activeEventDialog.sourceId);
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::HouseProprietor)
    {
        if (context.pHouseTable == nullptr)
        {
            return result;
        }

        const HouseEntry *pHouseEntry = context.pHouseTable->get(context.activeEventDialog.sourceId);

        if (pHouseEntry == nullptr)
        {
            return result;
        }

        context.eventRuntimeState.dialogueState.hostHouseId = pHouseEntry->id;
        context.eventRuntimeState.dialogueState.menuStack.push_back(DialogueMenuId::HouseServiceRoot);
        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::HouseService,
            pHouseEntry->id,
            pHouseEntry->id);
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::HouseExtraExit)
    {
        if (context.pHouseTable == nullptr)
        {
            return result;
        }

        const HouseEntry *pHouseEntry = context.pHouseTable->get(action.id);

        if (pHouseEntry == nullptr || !pHouseEntry->extraExit.has_value())
        {
            return result;
        }

        context.eventRuntimeState.dialogueState.hostHouseId = pHouseEntry->id;
        context.eventRuntimeState.dialogueState.menuStack.push_back(DialogueMenuId::HouseServiceRoot);
        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::HouseService,
            pHouseEntry->id,
            pHouseEntry->id);
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::HouseResident)
    {
        context.eventRuntimeState.dialogueState.hostHouseId = context.activeEventDialog.sourceId;
        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            action.id,
            context.activeEventDialog.sourceId);
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::GeneratedMercenaryJoinOffer)
    {
        const auto recruitIt = context.eventRuntimeState.generatedMercenaryRecruitsByNpcId.find(action.id);

        if (recruitIt == context.eventRuntimeState.generatedMercenaryRecruitsByNpcId.end())
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("That companion is not ready to join yet."));
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        EventRuntimeState::DialogueOfferState offerState = {};
        offerState.kind = DialogueOfferKind::RosterJoin;
        offerState.npcId = action.id;
        offerState.rosterId = recruitIt->second.rosterId;
        context.eventRuntimeState.dialogueState.currentOffer = std::move(offerState);
        context.eventRuntimeState.messages.push_back(generatedMercenaryJoinOfferText(recruitIt->second));

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            action.id,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::RosterJoinOffer)
    {
        if (context.pNpcDialogTable == nullptr)
        {
            return result;
        }

        const std::optional<NpcDialogTable::RosterJoinOffer> offer =
            context.pNpcDialogTable->getRosterJoinOfferForTopic(action.id);

        if (!offer)
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("That companion is not ready to join yet."));
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        const std::optional<std::string> inviteText = context.pNpcDialogTable->getText(offer->inviteTextId);

        if (inviteText && !inviteText->empty())
        {
            context.eventRuntimeState.messages.push_back(*inviteText);
        }

        EventRuntimeState::DialogueOfferState offerState = {};
        offerState.kind = DialogueOfferKind::RosterJoin;
        offerState.npcId = context.activeEventDialog.sourceId;
        offerState.topicId = action.id;
        offerState.messageTextId = offer->inviteTextId;
        offerState.rosterId = offer->rosterId;
        offerState.partyFullTextId = offer->partyFullTextId;
        context.eventRuntimeState.dialogueState.currentOffer = std::move(offerState);

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            context.activeEventDialog.sourceId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::RosterJoinAccept)
    {
        if (!context.eventRuntimeState.dialogueState.currentOffer
            || context.eventRuntimeState.dialogueState.currentOffer->kind != DialogueOfferKind::RosterJoin
            || context.pParty == nullptr)
        {
            return result;
        }

        const EventRuntimeState::DialogueOfferState invite = *context.eventRuntimeState.dialogueState.currentOffer;
        context.eventRuntimeState.dialogueState.currentOffer.reset();

        const auto generatedRecruitIt =
            context.eventRuntimeState.generatedMercenaryRecruitsByNpcId.find(invite.npcId);

        if (generatedRecruitIt != context.eventRuntimeState.generatedMercenaryRecruitsByNpcId.end())
        {
            const EventRuntimeState::GeneratedMercenaryRecruit recruit = generatedRecruitIt->second;

            if (context.pParty->isFull())
            {
                if (!partyHasAdventurersInnRosterMember(*context.pParty, recruit.rosterId))
                {
                    context.pParty->addAdventurersInnMember(recruit.character, recruit.portraitPictureId);
                }

                context.eventRuntimeState.generatedMercenaryRecruitsByNpcId.erase(invite.npcId);
                context.eventRuntimeState.unavailableNpcIds.insert(invite.npcId);
                context.eventRuntimeState.npcHouseOverrides.erase(invite.npcId);
                context.pParty->setNpcUnavailable(invite.npcId, true);
                context.pParty->clearNpcHouseOverride(invite.npcId);
                context.eventRuntimeState.messages.push_back(
                    Engine::tr("{name} waits at the Adventurer's Inn.", {{"name", recruit.character.name}}));
                setPendingDialogueContext(
                    context.eventRuntimeState,
                    DialogueContextKind::NpcTalk,
                    invite.npcId,
                    currentDialogueHostHouseId(context.eventRuntimeState));
                result.shouldOpenPendingEventDialog = true;
                result.allowNpcFallbackContent = false;
                return result;
            }

            if (!context.pParty->recruitCharacter(recruit.character))
            {
                context.eventRuntimeState.messages.push_back(Engine::tr("Recruitment is not available for this companion yet."));
                setPendingDialogueContext(
                    context.eventRuntimeState,
                    DialogueContextKind::NpcTalk,
                    invite.npcId,
                    currentDialogueHostHouseId(context.eventRuntimeState));
                result.shouldOpenPendingEventDialog = true;
                return result;
            }

            context.eventRuntimeState.generatedMercenaryRecruitsByNpcId.erase(invite.npcId);
            context.eventRuntimeState.unavailableNpcIds.insert(invite.npcId);
            context.eventRuntimeState.npcHouseOverrides.erase(invite.npcId);
            context.pParty->setNpcUnavailable(invite.npcId, true);
            context.pParty->clearNpcHouseOverride(invite.npcId);
            context.eventRuntimeState.messages.push_back(Engine::tr("{name} joined the party.", {{"name", recruit.character.name}}));
            queueUiSound(context.eventRuntimeState, HeroismEffectSoundId);
            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::HireNpc, true);
            setPendingDialogueContext(
                context.eventRuntimeState,
                DialogueContextKind::NpcTalk,
                invite.npcId,
                currentDialogueHostHouseId(context.eventRuntimeState));
            result.shouldOpenPendingEventDialog = true;
            result.allowNpcFallbackContent = false;
            return result;
        }

        if (context.pRosterTable == nullptr)
        {
            return result;
        }

        const RosterEntry *pRosterEntry = context.pRosterTable->get(invite.rosterId);

        if (context.pParty->isFull())
        {
            if (pRosterEntry != nullptr && !context.pParty->hasRosterMember(invite.rosterId))
            {
        const std::optional<NpcEntry> npcEntry =
            runtimeNpcEntry(context.pNpcDialogTable, context.eventRuntimeState, invite.npcId);
        const uint32_t portraitPictureId = npcEntry ? npcEntry->pictureId : 0;
                context.pParty->addAdventurersInnMember(*pRosterEntry, portraitPictureId);
            }

            const uint32_t adventurersInnHouseId = defaultAdventurersInnHouseId(context);
            context.eventRuntimeState.npcHouseOverrides[invite.npcId] = adventurersInnHouseId;
            context.pParty->setNpcHouseOverride(invite.npcId, adventurersInnHouseId);

            if (context.pNpcDialogTable != nullptr)
            {
                const std::optional<std::string> fullPartyText =
                    context.pNpcDialogTable->getText(invite.partyFullTextId);

                if (fullPartyText && !fullPartyText->empty())
                {
                    context.eventRuntimeState.messages.push_back(*fullPartyText);
                }
            }

            setPendingDialogueContext(
                context.eventRuntimeState,
                DialogueContextKind::NpcTalk,
                invite.npcId,
                currentDialogueHostHouseId(context.eventRuntimeState));
            result.shouldOpenPendingEventDialog = true;
            result.allowNpcFallbackContent = false;
            return result;
        }

        if (pRosterEntry == nullptr || !context.pParty->recruitRosterMember(*pRosterEntry))
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("Recruitment is not available for this companion yet."));
            setPendingDialogueContext(
                context.eventRuntimeState,
                DialogueContextKind::NpcTalk,
                invite.npcId,
                currentDialogueHostHouseId(context.eventRuntimeState));
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        context.eventRuntimeState.unavailableNpcIds.insert(invite.npcId);
        context.eventRuntimeState.npcHouseOverrides.erase(invite.npcId);
        context.pParty->setNpcUnavailable(invite.npcId, true);
        context.pParty->clearNpcHouseOverride(invite.npcId);
        context.eventRuntimeState.messages.push_back(Engine::tr("{name} joined the party.", {{"name", pRosterEntry->name}}));
        queueUiSound(context.eventRuntimeState, HeroismEffectSoundId);
        playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::HireNpc, true);
        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            invite.npcId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        result.allowNpcFallbackContent = false;
        return result;
    }

    if (action.kind == EventDialogActionKind::RosterJoinDecline)
    {
        const uint32_t npcId =
            (context.eventRuntimeState.dialogueState.currentOffer
             && context.eventRuntimeState.dialogueState.currentOffer->kind == DialogueOfferKind::RosterJoin)
            ? context.eventRuntimeState.dialogueState.currentOffer->npcId
            : context.activeEventDialog.sourceId;
        context.eventRuntimeState.dialogueState.currentOffer.reset();

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            npcId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::MasteryTeacherOffer)
    {
        tryRegisterTrainerNote(
            context.eventRuntimeState,
            action.id,
            context.activeEventDialog.sourceId,
            context.pTeacherAutonoteTable,
            context.pTeacherTopicTable,
            context.pCurrentMap,
            context.pBolsterMapTable,
            context.pWorldRuntime,
            context.pParty);

        EventRuntimeState::DialogueOfferState offer = {};
        offer.kind = DialogueOfferKind::MasteryTeacher;
        offer.npcId = context.activeEventDialog.sourceId;
        offer.topicId = action.id;
        context.eventRuntimeState.dialogueState.currentOffer = std::move(offer);

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            context.activeEventDialog.sourceId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::MasteryTeacherLearn)
    {
        if (!context.eventRuntimeState.dialogueState.currentOffer
            || context.eventRuntimeState.dialogueState.currentOffer->kind != DialogueOfferKind::MasteryTeacher
            || context.pParty == nullptr
            || context.pClassSkillTable == nullptr
            || context.pNpcDialogTable == nullptr)
        {
            return result;
        }

        std::string message;

        if (applyMasteryTeacherTopic(
                context.eventRuntimeState.dialogueState.currentOffer->topicId,
                *context.pParty,
                *context.pClassSkillTable,
                *context.pNpcDialogTable,
                context.pTeacherTopicTable,
                message))
        {
            if (!message.empty())
            {
                context.uiController.setStatusBarEvent(message);
            }

            playSpeechReaction(
                context,
                context.pParty->activeMemberIndex(),
                SpeechId::SkillMasteryIncreased,
                true);
            setPendingDialogueContext(
                context.eventRuntimeState,
                DialogueContextKind::NpcTalk,
                context.eventRuntimeState.dialogueState.currentOffer->npcId,
                currentDialogueHostHouseId(context.eventRuntimeState));
            result.shouldOpenPendingEventDialog = true;
        }
        else
        {
            const std::optional<MasteryTeacherEvaluation> evaluation = evaluateMasteryTeacherTopic(
                context.eventRuntimeState.dialogueState.currentOffer->topicId,
                *context.pParty,
                *context.pClassSkillTable,
                *context.pNpcDialogTable,
                context.pTeacherTopicTable
            );

            if (evaluation && !evaluation->displayText.empty())
            {
                context.uiController.setStatusBarEvent(evaluation->displayText);
            }

            result.shouldOpenPendingEventDialog = true;
        }

        return result;
    }

    if (action.kind == EventDialogActionKind::GuildMembershipOffer)
    {
        if (context.pNpcDialogTable == nullptr)
        {
            return result;
        }

        const std::optional<NpcDialogTable::GuildMembershipOffer> offer =
            context.pNpcDialogTable->getGuildMembershipOfferForTopic(action.id);

        if (!offer)
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("That topic does not have an event yet."));
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        if (hasGuildMembership(context.eventRuntimeState, context.pParty, offer->guildType))
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                124,
                Engine::tr("You're already a member of this guild.")));
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        const std::optional<std::string> description = context.pNpcDialogTable->getText(offer->descriptionTextId);
        if (description && !description->empty())
        {
            context.eventRuntimeState.messages.push_back(*description);
        }

        EventRuntimeState::DialogueOfferState guildOffer = {};
        guildOffer.kind = DialogueOfferKind::GuildMembership;
        guildOffer.npcId = context.activeEventDialog.sourceId;
        guildOffer.topicId = offer->topicId;
        guildOffer.messageTextId = offer->descriptionTextId;
        context.eventRuntimeState.dialogueState.currentOffer = std::move(guildOffer);

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            context.activeEventDialog.sourceId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::GuildMembershipJoin)
    {
        if (!context.eventRuntimeState.dialogueState.currentOffer
            || context.eventRuntimeState.dialogueState.currentOffer->kind != DialogueOfferKind::GuildMembership
            || context.pNpcDialogTable == nullptr
            || context.pParty == nullptr)
        {
            return result;
        }

        const EventRuntimeState::DialogueOfferState guildOffer =
            *context.eventRuntimeState.dialogueState.currentOffer;
        const std::optional<NpcDialogTable::GuildMembershipOffer> offer =
            context.pNpcDialogTable->getGuildMembershipOfferForTopic(guildOffer.topicId);

        if (!offer)
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("That topic does not have an event yet."));
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        if (hasGuildMembership(context.eventRuntimeState, context.pParty, offer->guildType))
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                124,
                Engine::tr("You're already a member of this guild.")));
        }
        else if (context.pParty->gold() < static_cast<int>(offer->cost))
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                125,
                Engine::tr("You don't have enough gold!")));
            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::NotEnoughGold, true);
        }
        else
        {
            context.pParty->addGold(-static_cast<int>(offer->cost), GoldReason::Other);
            grantGuildMembership(context.eventRuntimeState, context.pParty, *offer);
            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::JoinedGuild, true);

            const std::optional<std::string> description = context.pNpcDialogTable->getText(offer->descriptionTextId);
            if (description && !description->empty())
            {
                context.eventRuntimeState.messages.push_back(*description);
            }
        }

        context.eventRuntimeState.dialogueState.currentOffer.reset();
        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            guildOffer.npcId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::NpcHireOffer)
    {
        if (context.pNpcDialogTable == nullptr || context.pNpcProfessionTable == nullptr)
        {
            return result;
        }

        const uint32_t npcId = context.activeEventDialog.sourceId;
        const std::optional<NpcEntry> npcEntry =
            runtimeNpcEntry(context.pNpcDialogTable, context.eventRuntimeState, npcId);
        const NpcEntry *pNpc = npcEntry ? &*npcEntry : nullptr;
        const MergedNpcProfessionEntry *pProfession =
            pNpc != nullptr ? context.pNpcProfessionTable->get(pNpc->professionId) : nullptr;

        if (pNpc == nullptr
            || pProfession == nullptr
            || !npcCanOfferProfessionHire(
                *pNpc,
                *pProfession,
                currentDialogueHostHouseId(context.eventRuntimeState) == 0 || pNpc->topicIds.empty())
            || !continentAllowsNpcFollowers(context.pCurrentMap, context.pContinentSettingTable)
            || (context.pParty != nullptr && !context.pParty->npcFollowersActive()))
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("That follower is not available."));
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        std::string message = npcTextOrFallback(
            context.pNpcDialogTable,
            pProfession->joinTextId,
            Engine::tr("I will join you."));

        if (pProfession->descriptionTextId != 0)
        {
            const std::optional<std::string> description = context.pNpcDialogTable->getText(pProfession->descriptionTextId);

            if (description && !description->empty())
            {
                message += "\n(" + Engine::localize(*description) + ")";
            }
        }

        context.eventRuntimeState.messages.push_back(formatNpcProfessionText(
            message,
            *pNpc,
            *pProfession,
            context.pParty,
            effectiveReputationForContext(context)));

        EventRuntimeState::DialogueOfferState offerState = {};
        offerState.kind = DialogueOfferKind::NpcHire;
        offerState.npcId = npcId;
        offerState.topicId = pNpc->professionId;
        offerState.messageTextId = pProfession->joinTextId;
        offerState.sourceActorIndex = context.activeEventDialog.sourceActorIndex;
        context.eventRuntimeState.dialogueState.currentOffer = std::move(offerState);

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            npcId,
            currentDialogueHostHouseId(context.eventRuntimeState),
            offerState.sourceActorIndex);
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::NpcHireAccept)
    {
        if (!context.eventRuntimeState.dialogueState.currentOffer
            || context.eventRuntimeState.dialogueState.currentOffer->kind != DialogueOfferKind::NpcHire
            || context.pNpcDialogTable == nullptr
            || context.pNpcProfessionTable == nullptr
            || context.pParty == nullptr)
        {
            return result;
        }

        const EventRuntimeState::DialogueOfferState offer = *context.eventRuntimeState.dialogueState.currentOffer;
        context.eventRuntimeState.dialogueState.currentOffer.reset();
        bool hired = false;

        const std::optional<NpcEntry> npcEntry =
            runtimeNpcEntry(context.pNpcDialogTable, context.eventRuntimeState, offer.npcId);
        const NpcEntry *pNpc = npcEntry ? &*npcEntry : nullptr;
        const MergedNpcProfessionEntry *pProfession =
            pNpc != nullptr ? context.pNpcProfessionTable->get(pNpc->professionId) : nullptr;

        if (pNpc == nullptr
            || pProfession == nullptr
            || !npcCanOfferProfessionHire(
                *pNpc,
                *pProfession,
                currentDialogueHostHouseId(context.eventRuntimeState) == 0 || pNpc->topicIds.empty())
            || !continentAllowsNpcFollowers(context.pCurrentMap, context.pContinentSettingTable)
            || (context.pParty != nullptr && !context.pParty->npcFollowersActive()))
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("That follower is not available."));
        }
        else if (hasHiredNpcFollower(context.eventRuntimeState, offer.npcId))
        {
            context.eventRuntimeState.messages.push_back(
                Engine::tr("{name} is already following you.", {{"name", Engine::localize(pNpc->name)}}));
        }
        else if (context.eventRuntimeState.hiredNpcFollowers.size() >= MaxNpcFollowerCount
            || hiredNpcFollowerFeePercent(context.eventRuntimeState) >= MaxNpcFollowerFeePercent)
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                533,
                Engine::tr("You already have enough followers.")));
        }
        else if (const std::optional<FollowerHireRefusal> refusal =
                     context.pParty->rules().classes.followerHireRefusal(
                         currentDialogueHostHouseId(context.eventRuntimeState)))
        {
            context.eventRuntimeState.messages.push_back(refusal->message);
        }
        else if (context.pParty->gold() < static_cast<int>(pProfession->weeklyCost))
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                125,
                Engine::tr("You do not have enough gold.")));
        }
        else
        {
            context.pParty->addGold(-static_cast<int>(pProfession->weeklyCost), GoldReason::Other);

            EventRuntimeState::HiredNpcFollower follower = {};
            follower.npcId = offer.npcId;
            follower.professionId = pNpc->professionId;
            follower.weeklyCost = pProfession->weeklyCost;
            follower.name = pNpc->name;
            follower.pictureId = pNpc->pictureId;
            context.eventRuntimeState.hiredNpcFollowers.push_back(follower);
            context.eventRuntimeState.unavailableNpcIds.insert(offer.npcId);
            context.eventRuntimeState.npcHouseOverrides.erase(offer.npcId);
            context.pParty->addHiredNpcFollower(follower);
            context.pParty->setNpcUnavailable(offer.npcId, true);
            context.pParty->clearNpcHouseOverride(offer.npcId);
            if (offer.sourceActorIndex)
            {
                hideMapActorByIndex(context.eventRuntimeState, *offer.sourceActorIndex);
            }
            else
            {
                hideGeneratedNpcActor(context.eventRuntimeState, offer.npcId, context.pCurrentMap);
            }

            if (context.pWorldRuntime != nullptr)
            {
                context.pWorldRuntime->applyEventRuntimeState();
            }

            context.eventRuntimeState.messages.push_back(Engine::tr("{name} joined the followers.", {{"name", pNpc->name}}));
            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::HireNpc, true);
            if (context.pScreenRuntime != nullptr)
            {
                context.pScreenRuntime->interactionState().followerPanelOpen = true;
                context.pScreenRuntime->interactionState().followerPanelScrollOffset = 0;
            }
            hired = true;
        }

        if (hired)
        {
            result.shouldCloseActiveDialog = true;
            return result;
        }

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            offer.npcId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        result.allowNpcFallbackContent = false;
        return result;
    }

    if (action.kind == EventDialogActionKind::NpcHireDecline)
    {
        const uint32_t npcId =
            (context.eventRuntimeState.dialogueState.currentOffer
             && context.eventRuntimeState.dialogueState.currentOffer->kind == DialogueOfferKind::NpcHire)
            ? context.eventRuntimeState.dialogueState.currentOffer->npcId
            : context.activeEventDialog.sourceId;
        context.eventRuntimeState.dialogueState.currentOffer.reset();

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            npcId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::NpcDismiss)
    {
        const uint32_t npcId = context.activeEventDialog.sourceId;
        const std::optional<NpcEntry> npcEntry =
            runtimeNpcEntry(context.pNpcDialogTable, context.eventRuntimeState, npcId);
        const NpcEntry *pNpc = npcEntry ? &*npcEntry : nullptr;
        std::vector<EventRuntimeState::HiredNpcFollower> &followers = context.eventRuntimeState.hiredNpcFollowers;
        const auto followerIt = std::find_if(
            followers.begin(),
            followers.end(),
            [npcId](const EventRuntimeState::HiredNpcFollower &follower)
            {
                return follower.npcId == npcId;
            });

        if (followerIt != followers.end())
        {
            followers.erase(followerIt);
            context.eventRuntimeState.unavailableNpcIds.erase(npcId);

            if (context.pParty != nullptr)
            {
                context.pParty->removeHiredNpcFollower(npcId);
                context.pParty->setNpcUnavailable(npcId, false);
            }

            context.eventRuntimeState.messages.push_back(
                Engine::tr("{name} left the followers.",
                    {{"name", pNpc != nullptr && !pNpc->name.empty() ? Engine::localize(pNpc->name)
                                                                     : Engine::tr("The follower")}}));
        }

        result.shouldCloseActiveDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::NpcProfessionDescription)
    {
        if (context.pNpcDialogTable != nullptr && context.pNpcProfessionTable != nullptr && action.secondaryId != 0)
        {
            const std::optional<NpcEntry> npc = runtimeNpcEntry(
                context.pNpcDialogTable, context.eventRuntimeState, context.activeEventDialog.sourceId);
            const MergedNpcProfessionEntry *pProfession = npc
                ? context.pNpcProfessionTable->get(npc->professionId)
                : nullptr;
            const std::optional<std::string> description = context.pNpcDialogTable->getText(action.secondaryId);

            if (npc && pProfession != nullptr && description && !description->empty())
            {
                context.eventRuntimeState.messages.push_back(formatNpcProfessionText(
                    *description,
                    *npc,
                    *pProfession,
                    context.pParty,
                    effectiveReputationForContext(context),
                    std::nullopt,
                    context.pWorldRuntime != nullptr ? context.pWorldRuntime->gameMinutes() : 0.0f));
            }
        }

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            context.activeEventDialog.sourceId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::NpcBtb)
    {
        bool accepted = action.argument == "accepted";
        bool bribePaid = false;

        if (context.pNpcDialogTable != nullptr && action.secondaryId != 0)
        {
            const uint32_t npcId = context.activeEventDialog.sourceId;
            const std::optional<NpcEntry> npcEntry =
                runtimeNpcEntry(context.pNpcDialogTable, context.eventRuntimeState, npcId);
            const NpcEntry *pNpc = npcEntry ? &*npcEntry : nullptr;
            const MergedNpcProfessionEntry *pProfession =
                pNpc != nullptr && context.pNpcProfessionTable != nullptr
                    ? context.pNpcProfessionTable->get(pNpc->professionId)
                    : nullptr;
            const MergedNpcBtbEntry *pBtbEntry =
                pProfession != nullptr && context.pNpcBtbTable != nullptr
                    ? context.pNpcBtbTable->get(pProfession->personality)
                    : nullptr;
            uint32_t textId = action.secondaryId;

            if (accepted && action.id == NpcBribeTopicId)
            {
                const uint32_t bribeCost =
                    pProfession != nullptr && pProfession->weeklyCost != 0 ? pProfession->weeklyCost : 50u;

                if (context.pParty == nullptr || context.pParty->gold() <= static_cast<int>(bribeCost))
                {
                    accepted = false;
                    textId = 0;
                    context.eventRuntimeState.messages.push_back(Engine::tr("You don't have enough gold."));
                }
                else
                {
                    context.pParty->addGold(-static_cast<int>(bribeCost), GoldReason::Other);
                    bribePaid = true;
                }
            }

            const std::optional<std::string> text = context.pNpcDialogTable->getText(textId);

            if (text && !text->empty())
            {
                context.eventRuntimeState.messages.push_back(
                    pNpc != nullptr && pProfession != nullptr
                        ? formatNpcProfessionText(
                            *text,
                            *pNpc,
                            *pProfession,
                            context.pParty,
                            effectiveReputationForContext(context),
                            pBtbEntry != nullptr
                                ? std::optional<int>(requiredNpcReputationForBtb(*pBtbEntry))
                                : std::nullopt)
                        : *text);
            }
        }

        if (accepted || bribePaid)
        {
            context.eventRuntimeState.variables[npcBtbDialogueAccessVariableKey(context.activeEventDialog.sourceId)] =
                static_cast<int32_t>(npcBtbDialogueAccessDay(
                    context.pWorldRuntime != nullptr ? context.pWorldRuntime->gameMinutes() : -1.0f));
        }

        if (context.pParty != nullptr)
        {
            SpeechId speechId = SpeechId::None;

            if (action.id == NpcBegTopicId)
            {
                speechId = accepted ? SpeechId::Beg : SpeechId::BegFail;
            }
            else if (action.id == NpcThreatTopicId)
            {
                speechId = accepted ? SpeechId::Threat : SpeechId::ThreatFail;
            }
            else if (action.id == NpcBribeTopicId)
            {
                speechId = (accepted || bribePaid) ? SpeechId::Bribe : SpeechId::BribeFail;
            }

            if (speechId != SpeechId::None)
            {
                playSpeechReaction(context, context.pParty->activeMemberIndex(), speechId, true);
            }
        }

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            context.activeEventDialog.sourceId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::NpcProfessionAction)
    {
        const uint32_t npcId = context.activeEventDialog.sourceId;
        const std::optional<EventRuntimeState::PendingDialogueContext> previousPendingDialogueContext =
            context.eventRuntimeState.pendingDialogueContext;
        bool executed = false;

        const NpcProfessionActionExecution professionExecution =
            executeNpcFollowerProfessionAction(context, action.id);

        if (professionExecution.handled)
        {
            executed = true;
        }

        if (professionExecution.closeDialog)
        {
            result.shouldCloseActiveDialog = true;
            return result;
        }

        if (!executed && context.pNpcDialogTable != nullptr)
        {
            const std::optional<NpcDialogTable::ResolvedTopic> topic =
                context.pNpcDialogTable->getTopicById(action.id);

            if (topic && !topic->text.empty())
            {
                context.eventRuntimeState.messages.push_back(topic->text);
                executed = true;
            }
        }

        if (!executed)
        {
            size_t executionPreviousMessageCount = result.previousMessageCount;
            executed = executeNpcTopicEvent(context, static_cast<uint16_t>(action.id), executionPreviousMessageCount);
        }

        if (!executed)
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("That topic does not have an event yet."));
        }

        if (!context.eventRuntimeState.pendingDialogueContext
            || samePendingDialogueContext(
                context.eventRuntimeState.pendingDialogueContext,
                previousPendingDialogueContext))
        {
            setPendingDialogueContext(
                context.eventRuntimeState,
                DialogueContextKind::NpcTalk,
                npcId,
                currentDialogueHostHouseId(context.eventRuntimeState));
        }

        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::ArenaChallenge
        || (action.kind == EventDialogActionKind::NpcTopic && action.id == ArenaTopicId))
    {
        const uint32_t npcId = context.activeEventDialog.sourceId;
        if (context.pWorldRuntime == nullptr)
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("The Arena is unavailable here."));
        }
        else if (action.kind == EventDialogActionKind::ArenaChallenge)
        {
            const std::optional<EventRuntimeState::DialogueOfferState> &offer =
                context.eventRuntimeState.dialogueState.currentOffer;
            if (offer && offer->kind == DialogueOfferKind::Arena && offer->npcId == npcId)
            {
                result.shouldCloseActiveDialog = startArenaChallenge(
                    *context.pWorldRuntime, ArenaDifficulty(action.id), uint32_t(std::rand()));
            }
        }
        else
        {
            result.shouldCloseActiveDialog = interactWithArena(*context.pWorldRuntime, npcId);
        }
        if (!result.shouldCloseActiveDialog)
        {
            setPendingDialogueContext(context.eventRuntimeState, DialogueContextKind::NpcTalk,
                npcId, currentDialogueHostHouseId(context.eventRuntimeState));
            result.shouldOpenPendingEventDialog = true;
        }
        return result;
    }

    if (action.kind == EventDialogActionKind::NpcTopic)
    {
        const uint32_t npcId = context.activeEventDialog.sourceId;
        const std::optional<EventRuntimeState::PendingDialogueContext> previousPendingDialogueContext =
            context.eventRuntimeState.pendingDialogueContext;
        bool executed = executeBuiltInNpcTopic(context, action.id);

        if (!executed && action.textOnly && context.pNpcDialogTable != nullptr)
        {
            const std::optional<NpcDialogTable::ResolvedTopic> topic =
                context.pNpcDialogTable->getTopicById(action.secondaryId != 0 ? action.secondaryId : action.id);

            if (topic && !topic->text.empty())
            {
                tryRegisterTrainerNote(
                    context.eventRuntimeState,
                    topic->id,
                    npcId,
                    context.pTeacherAutonoteTable,
                    context.pTeacherTopicTable,
                    context.pCurrentMap,
                    context.pBolsterMapTable,
                    context.pWorldRuntime,
                    context.pParty);
                context.eventRuntimeState.messages.push_back(topic->text);
                executed = true;
            }
        }
        else if (!executed)
        {
            size_t executionPreviousMessageCount = result.previousMessageCount;
            executed = executeNpcTopicEvent(context, static_cast<uint16_t>(action.id), executionPreviousMessageCount);
        }

        if (!executed)
        {
            context.eventRuntimeState.messages.push_back(Engine::tr("That topic does not have an event yet."));
        }

        if (context.eventRuntimeState.pendingDimensionDoorOverlay)
        {
            result.shouldCloseActiveDialog = true;
            return result;
        }

        if (!context.eventRuntimeState.pendingDialogueContext
            || samePendingDialogueContext(
                context.eventRuntimeState.pendingDialogueContext,
                previousPendingDialogueContext))
        {
            setPendingDialogueContext(
                context.eventRuntimeState,
                DialogueContextKind::NpcTalk,
                npcId,
                currentDialogueHostHouseId(context.eventRuntimeState));
        }

        result.shouldOpenPendingEventDialog = true;
    }

    if (action.kind == EventDialogActionKind::NpcProfessionNews)
    {
        if (context.pNpcDialogTable != nullptr && action.secondaryId != 0)
        {
            const std::optional<std::string> newsText = context.pNpcDialogTable->getNewsText(action.secondaryId);

            if (newsText && !newsText->empty())
            {
                context.eventRuntimeState.messages.push_back(*newsText);
            }
        }

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            context.activeEventDialog.sourceId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
    }

    return result;
}

GameplayDialogController::PresentPendingDialogResult GameplayDialogController::presentPendingEventDialog(
    Context &context,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    bool showBankInputCursor) const
{
    PresentPendingDialogResult result = {};

    if (!context.eventRuntimeState.pendingDialogueContext)
    {
        return result;
    }

    const EventRuntimeState::PendingDialogueContext originalContext = *context.eventRuntimeState.pendingDialogueContext;

    if (originalContext.kind == DialogueContextKind::Mm9Rude)
    {
        result.wasDialogAlreadyActive = context.activeEventDialog.isActive;
        openMm9RudeDialogue(context, originalContext.sourceId, originalContext.sourceActorIndex);
        context.eventRuntimeState.dialogueState.mm9RudeSourceDecorationKey = originalContext.sourceDecorationKey;
        if (!context.activeEventDialog.isActive
            || context.activeEventDialog.presentation != EventDialogPresentation::Mm9Rude)
        {
            context.eventRuntimeState.pendingDialogueContext.reset();
            return result;
        }

        context.uiController.setEventDialogContent(context.activeEventDialog);
        result.dialogOpened = true;
        result.resolvedContext = originalContext;
        return result;
    }

    if (originalContext.kind == DialogueContextKind::HouseService
        && context.pHouseTable != nullptr
        && context.pWorldRuntime != nullptr
        && context.pParty != nullptr)
    {
        if (tryOpenAdventurersInnOverlay(context, originalContext.sourceId))
        {
            return result;
        }

        const HouseEntry *pHouseEntry = context.pHouseTable->get(originalContext.sourceId);

        if (pHouseEntry != nullptr && rejectClosedHouseInteraction(context, *pHouseEntry))
        {
            return result;
        }
    }

    const HouseEntry *pPendingHouseEntry = pendingHouseEntry(originalContext, context.pHouseTable);
    result.wasDialogAlreadyActive = context.activeEventDialog.isActive;

    context.uiController.setEventDialogContent(buildEventDialogContent(
        context.eventRuntimeState,
        previousMessageCount,
        allowNpcFallbackContent,
        context.pGlobalEventProgram,
        context.pHouseTable,
        context.pClassSkillTable,
        context.pNpcDialogTable,
        context.pTransitionTable,
        context.pCurrentMap,
        context.pMapEntries,
        context.pParty,
        context.pWorldRuntime,
        context.pWorldRuntime != nullptr ? context.pWorldRuntime->gameMinutes() : -1.0f,
        context.pNpcProfessionTable,
        context.pNewsProfessionTopicTable,
        context.pNpcBtbTable,
        context.pTeacherTopicTable,
        context.pContinentSettingTable
    ));

    if (context.eventRuntimeState.pendingDialogueContext.has_value()
        && context.eventRuntimeState.pendingDialogueContext->kind == DialogueContextKind::NpcTalk
        && context.pNpcDialogTable != nullptr
        && context.pParty != nullptr)
    {
        const std::optional<uint32_t> masteryTopicId = masteryTeacherTopicIdForNpc(
            *context.pNpcDialogTable,
            context.eventRuntimeState,
            context.pParty,
            context.pTeacherTopicTable,
            context.eventRuntimeState.pendingDialogueContext->sourceId);

        if (masteryTopicId.has_value())
        {
            registerTrainerNotesForNpc(
                context.eventRuntimeState,
                *context.pNpcDialogTable,
                context.eventRuntimeState.pendingDialogueContext->sourceId,
                context.pTeacherAutonoteTable,
                context.pTeacherTopicTable,
                context.pCurrentMap,
                context.pBolsterMapTable,
                context.pWorldRuntime,
                context.pParty);
        }
    }

    if (!context.activeEventDialog.isActive)
    {
        context.eventRuntimeState.pendingDialogueContext.reset();
        context.uiController.clearHouseBankState();
        return result;
    }

    if (originalContext.hostHouseId != 0)
    {
        context.eventRuntimeState.dialogueState.hostHouseId = originalContext.hostHouseId;
    }
    else if (originalContext.kind == DialogueContextKind::HouseService)
    {
        context.eventRuntimeState.dialogueState.hostHouseId = originalContext.sourceId;
    }

    if (originalContext.kind == DialogueContextKind::HouseService
        && pPendingHouseEntry != nullptr
        && resolveHouseServiceType(*pPendingHouseEntry) == HouseServiceType::Shop
        && !context.eventRuntimeState.dialogueState.menuStack.empty()
        && context.eventRuntimeState.dialogueState.menuStack.back() == DialogueMenuId::ShopEquipment)
    {
        context.uiController.openInventoryNestedOverlay(
            GameplayUiController::InventoryNestedOverlayMode::ShopDisplay,
            pPendingHouseEntry->id);
    }

    context.selectionIndex = 0;

    if (pPendingHouseEntry == nullptr || resolveHouseServiceType(*pPendingHouseEntry) != HouseServiceType::Bank)
    {
        context.uiController.clearHouseBankState();
    }
    else
    {
        context.uiController.houseBankState().houseId = pPendingHouseEntry->id;

        if (context.uiController.houseBankState().inputActive())
        {
            refreshHouseBankInputDialog(context, showBankInputCursor);
        }
    }

    result.dialogOpened = true;
    result.resolvedContext = *context.eventRuntimeState.pendingDialogueContext;
    playIndoorExitReactionIfNeeded(context, originalContext, result.wasDialogAlreadyActive);
    return result;
}

GameplayDialogController::Result GameplayDialogController::openNpcDialogue(
    Context &context,
    uint32_t npcId,
    uint32_t hostHouseId,
    std::optional<uint32_t> sourceActorIndex) const
{
    Result result = {};
    result.previousMessageCount = context.eventRuntimeState.messages.size();

    if (npcId == 0)
    {
        return result;
    }

    context.eventRuntimeState.dialogueState.generatedNpcGreeting.reset();
    executeNpcHook(context, EventRuntimeHookKind::NpcEnter, npcId, sourceActorIndex);
    context.eventRuntimeState.dialogueState.hostHouseId = hostHouseId;
    setPendingDialogueContext(
        context.eventRuntimeState,
        DialogueContextKind::NpcTalk,
        npcId,
        hostHouseId,
        sourceActorIndex);
    context.eventRuntimeState.lastActorDialogStarted = EventRuntimeState::ActorDialogStartedTrace{
        .kind = "npc_talk",
        .map = context.pWorldRuntime != nullptr ? context.pWorldRuntime->mapName() : std::string(),
        .npcId = npcId,
        .sourceId = npcId,
        .hostHouseId = hostHouseId,
        .actorIndex = sourceActorIndex,
    };
    GAMEPLAY_DEBUG_TRACE(
        "actor_dialog_started kind=npc_talk"
        + std::string(" map=\"") + (context.pWorldRuntime != nullptr ? context.pWorldRuntime->mapName() : "")
        + "\" npc_id=" + std::to_string(npcId)
        + " source_id=" + std::to_string(npcId)
        + " host_house_id=" + std::to_string(hostHouseId)
        + " actor_index="
        + (sourceActorIndex.has_value() ? std::to_string(*sourceActorIndex) : std::string("none"))
        + (context.pWorldRuntime != nullptr
            ? " party=(" + std::to_string(context.pWorldRuntime->partyX())
                + "," + std::to_string(context.pWorldRuntime->partyY())
                + "," + std::to_string(context.pWorldRuntime->partyFootZ()) + ")"
                + " yaw=" + std::to_string(context.pWorldRuntime->gameplayCameraYawRadians())
                + " pitch=" + std::to_string(context.pWorldRuntime->gameplayCameraPitchRadians())
            : ""));
    result.shouldOpenPendingEventDialog = true;
    return result;
}

bool GameplayDialogController::activateMm9ActorDialogue(
    Context &context,
    const Mm9ActorDialogueActivation &activation,
    const std::function<void(size_t)> &presentPendingDialog,
    const std::function<void()> &presentActiveDialog) const
{
    EventRuntimeState &eventRuntimeState = context.eventRuntimeState;
    std::optional<uint16_t> entryEventId;

    if (activation.sourceObjectIndex.has_value()
        && activation.pLocalEventProgram != nullptr
        && activation.pLocalEventProgram->has_value())
    {
        const std::optional<uint16_t> useEventId = mm9RudeUseEventIdForSourceObject(*activation.sourceObjectIndex);

        if (useEventId.has_value() && (*activation.pLocalEventProgram)->hasEvent(*useEventId))
        {
            entryEventId = useEventId;
        }
    }

    if (entryEventId.has_value())
    {
        EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.actorIndex = activation.actorIndex;
        const std::optional<EventRuntimeState::ActiveHookContext> previousHookContext =
            eventRuntimeState.activeHookContext;
        eventRuntimeState.activeHookContext = std::move(hookContext);
        size_t previousMessageCount = eventRuntimeState.messages.size();
        const bool executed = context.pWorldRuntime != nullptr
            && context.pWorldRuntime->executeMapEvent(*entryEventId, previousMessageCount);
        eventRuntimeState.activeHookContext = previousHookContext;

        if (executed && eventRuntimeState.pendingDialogueContext.has_value())
        {
            presentPendingDialog(previousMessageCount);
        }

        const bool dialogActive = context.activeEventDialog.isActive
            && context.activeEventDialog.presentation == EventDialogPresentation::Mm9Rude;
        eventRuntimeState.lastActivationResult = executed
            ? "MM9 SCR entry " + std::to_string(*entryEventId) + " executed"
            : "MM9 SCR entry " + std::to_string(*entryEventId) + " failed";
        GAMEPLAY_DEBUG_TRACE(
            "mm9_scr_activation"
            " event_id=" + std::to_string(*entryEventId)
            + " runtime_actor=" + std::to_string(activation.actorIndex)
            + " executed=" + std::string(executed ? "true" : "false")
            + " dialog_active=" + std::string(dialogActive ? "true" : "false"));
        return executed;
    }

    openMm9RudeDialogue(context, activation.rudeId, activation.actorIndex);
    presentActiveDialog();

    const bool dialogActive = context.activeEventDialog.isActive
        && context.activeEventDialog.presentation == EventDialogPresentation::Mm9Rude;
    GAMEPLAY_DEBUG_TRACE(
        "mm9_rude_activation"
        " rude_id=" + std::to_string(activation.rudeId)
        + " runtime_actor=" + std::to_string(activation.actorIndex)
        + " dialog_active=" + std::string(dialogActive ? "true" : "false")
        + " title=\"" + context.activeEventDialog.title + "\""
        + " actions=" + std::to_string(context.activeEventDialog.actions.size()));
    eventRuntimeState.lastActivationResult = dialogActive
        ? "MM9 RUDE " + std::to_string(activation.rudeId) + " engaged"
        : "MM9 RUDE " + std::to_string(activation.rudeId) + " failed";
    return dialogActive;
}

GameplayDialogController::Result GameplayDialogController::openMm9RudeDialogue(
    Context &context,
    uint32_t rudeId,
    std::optional<uint32_t> sourceActorIndex) const
{
    Result result = {};
    result.previousMessageCount = context.eventRuntimeState.messages.size();

    if (rudeId == 0
        || context.pMm9RudeDialogueTable == nullptr
        || context.pParty == nullptr
        || !context.pMm9RudeDialogueTable->hasDialogue(rudeId))
    {
        GAMEPLAY_DEBUG_TRACE(
            "actor_dialog_rejected kind=mm9_rude"
            " rude_id=" + std::to_string(rudeId)
            + " has_table=" + std::string(context.pMm9RudeDialogueTable != nullptr ? "true" : "false")
            + " has_party=" + std::string(context.pParty != nullptr ? "true" : "false")
            + " has_dialogue="
            + std::string(
                context.pMm9RudeDialogueTable != nullptr
                    && context.pMm9RudeDialogueTable->hasDialogue(rudeId)
                    ? "true"
                    : "false"));
        return result;
    }

    context.eventRuntimeState.pendingDialogueContext.reset();
    context.eventRuntimeState.dialogueState.hostHouseId = 0;
    context.eventRuntimeState.dialogueState.mm9RudeSourceDecorationKey.reset();
    context.activeEventDialog = buildMm9RudeContent(
        *context.pMm9RudeDialogueTable,
        context.pMm9SkillTrainerTable,
        *context.pParty,
        rudeId,
        static_cast<int32_t>(rudeId),
        std::nullopt,
        sourceActorIndex);
    context.selectionIndex = 0;
    context.eventRuntimeState.lastActorDialogStarted = EventRuntimeState::ActorDialogStartedTrace{
        .kind = "mm9_rude",
        .map = context.pWorldRuntime != nullptr ? context.pWorldRuntime->mapName() : std::string(),
        .npcId = 0,
        .sourceId = rudeId,
        .hostHouseId = 0,
        .actorIndex = sourceActorIndex,
    };
    GAMEPLAY_DEBUG_TRACE(
        "actor_dialog_started kind=mm9_rude"
        " map=\"" + (context.pWorldRuntime != nullptr ? context.pWorldRuntime->mapName() : std::string()) + "\""
        + " rude_id=" + std::to_string(rudeId)
        + " actor_index="
        + (sourceActorIndex.has_value() ? std::to_string(*sourceActorIndex) : std::string("none"))
        + " title=\"" + context.activeEventDialog.title + "\""
        + " actions=" + std::to_string(context.activeEventDialog.actions.size()));
    return result;
}

GameplayDialogController::Result GameplayDialogController::openNpcNews(
    Context &context,
    uint32_t npcId,
    uint32_t newsId,
    const std::string &titleOverride,
    const std::string &newsText,
    uint32_t participantPictureId,
    std::optional<uint32_t> sourceActorIndex) const
{
    Result result = {};
    result.previousMessageCount = context.eventRuntimeState.messages.size();

    if (newsId == 0 || newsText.empty())
    {
        return result;
    }

    EventRuntimeState::PendingDialogueContext pendingContext = {};
    pendingContext.kind = DialogueContextKind::NpcNews;
    pendingContext.sourceId = npcId;
    pendingContext.sourceActorIndex = sourceActorIndex;
    pendingContext.newsId = newsId;
    pendingContext.participantPictureId = participantPictureId;
    pendingContext.titleOverride = titleOverride;
    context.eventRuntimeState.pendingDialogueContext = std::move(pendingContext);
    context.eventRuntimeState.messages.push_back(newsText);
    result.shouldOpenPendingEventDialog = true;
    return result;
}

GameplayDialogController::CloseDialogRequestResult GameplayDialogController::handleDialogueCloseRequest(
    Context &context) const
{
    CloseDialogRequestResult result = {};
    result.previousMessageCount = context.eventRuntimeState.messages.size();
    traceDialogState(context.activeEventDialog, "before_dialog_close");

    if (context.activeEventDialog.presentation == EventDialogPresentation::Mm9Rude)
    {
        const bool nextDialog = endMm9RudeTalk(context);
        result.shouldOpenPendingEventDialog = nextDialog;
        result.shouldCloseActiveDialog = !nextDialog;
        return result;
    }

    if (context.eventRuntimeState.pendingDialogueContext.has_value()
        && context.eventRuntimeState.pendingDialogueContext->kind == DialogueContextKind::MapTransition)
    {
        cancelMapTransition(context);
        result.shouldCloseActiveDialog = true;
        return result;
    }

    if (context.uiController.inventoryNestedOverlay().active && context.dialogueHudActive)
    {
        const GameplayUiController::InventoryNestedOverlayState inventoryOverlay =
            context.uiController.inventoryNestedOverlay();

        switch (inventoryOverlay.mode)
        {
            case GameplayUiController::InventoryNestedOverlayMode::ShopSell:
            case GameplayUiController::InventoryNestedOverlayMode::ShopIdentify:
            case GameplayUiController::InventoryNestedOverlayMode::ShopRepair:
                context.uiController.openInventoryNestedOverlay(
                    GameplayUiController::InventoryNestedOverlayMode::ShopDisplay,
                    inventoryOverlay.houseId);
                return result;

            case GameplayUiController::InventoryNestedOverlayMode::ShopDisplay:
                context.uiController.closeInventoryNestedOverlay();
                break;

            default:
                context.uiController.closeInventoryNestedOverlay();
                return result;
        }
    }

    if (!context.eventRuntimeState.dialogueState.menuStack.empty())
    {
        uint32_t sourceId = currentDialogueHostHouseId(context.eventRuntimeState);

        if (sourceId == 0)
        {
            sourceId = context.activeEventDialog.sourceId;
        }

        context.eventRuntimeState.dialogueState.menuStack.pop_back();
        setPendingDialogueContext(context.eventRuntimeState, DialogueContextKind::HouseService, sourceId, sourceId);
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (context.eventRuntimeState.dialogueState.currentOffer
        && context.eventRuntimeState.dialogueState.currentOffer->kind != DialogueOfferKind::None)
    {
        uint32_t npcId = context.eventRuntimeState.dialogueState.currentOffer->npcId;
        context.eventRuntimeState.dialogueState.currentOffer.reset();

        if (npcId == 0)
        {
            npcId = context.activeEventDialog.sourceId;
        }

        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::NpcTalk,
            npcId,
            currentDialogueHostHouseId(context.eventRuntimeState));
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    const bool isResidentSelectionMode =
        !context.activeEventDialog.actions.empty()
        && std::all_of(
            context.activeEventDialog.actions.begin(),
            context.activeEventDialog.actions.end(),
            isHouseOccupantSelectionAction);
    const uint32_t hostHouseId = currentDialogueHostHouseId(context.eventRuntimeState);
    const HouseEntry *pHostHouseEntry = hostHouseId != 0 && context.pHouseTable != nullptr
        ? context.pHouseTable->get(hostHouseId)
        : nullptr;
    const std::vector<uint32_t> hostResidentNpcIds =
        (pHostHouseEntry != nullptr && context.pNpcDialogTable != nullptr)
        ? collectSelectableResidentNpcIds(*pHostHouseEntry, *context.pNpcDialogTable, context.eventRuntimeState)
        : std::vector<uint32_t>{};

    if (!context.activeEventDialog.isHouseDialog
        && !isResidentSelectionMode
        && pHostHouseEntry != nullptr
        && (hostResidentNpcIds.size() > 1
            || (resolveHouseServiceType(*pHostHouseEntry) != HouseServiceType::None && !hostResidentNpcIds.empty())))
    {
        setPendingDialogueContext(
            context.eventRuntimeState,
            DialogueContextKind::HouseService,
            hostHouseId,
            hostHouseId);
        result.shouldOpenPendingEventDialog = true;
        return result;
    }

    if (pHostHouseEntry != nullptr)
    {
        if (resolveHouseServiceType(*pHostHouseEntry) == HouseServiceType::Temple)
        {
            const std::optional<uint32_t> soundId =
                deriveHouseSoundId(*pHostHouseEntry, HouseSoundType::TempleGoodbye);

            if (soundId.has_value())
            {
                playHouseSound(context, *soundId);
            }
        }
        else if (resolveHouseServiceType(*pHostHouseEntry) == HouseServiceType::Bank
                 && context.uiController.houseBankState().transactionPerformed)
        {
            const std::optional<uint32_t> soundId =
                deriveHouseSoundId(*pHostHouseEntry, HouseSoundType::BankGoodbye);

            if (soundId.has_value())
            {
                playHouseSound(context, *soundId);
            }
        }
        else if (resolveHouseServiceType(*pHostHouseEntry) == HouseServiceType::Shop
                 && pHostHouseEntry->vendorStockProfile != VendorStockProfile::None)
        {
            context.uiController.clearHouseShopVisitState();
        }
        else if (resolveHouseServiceType(*pHostHouseEntry) == HouseServiceType::Shop)
        {
            const bool transactionPerformed =
                context.uiController.houseShopTransactionPerformed(pHostHouseEntry->id);
            const bool shopBanned = context.pWorldRuntime != nullptr
                && houseRefusesShopServiceForReputation(
                    *pHostHouseEntry,
                    context.pWorldRuntime,
                    context.pWorldRuntime->gameMinutes());
            const int partyGold = context.pParty != nullptr ? context.pParty->gold() : 0;
            const HouseShopGoodbyeResult goodbyeResult =
                resolveHouseShopGoodbyeResult(*pHostHouseEntry, transactionPerformed, shopBanned, partyGold);
            const std::string goodbyeSoundName =
                debugShopGoodbyeSoundName(*pHostHouseEntry, goodbyeResult.soundType);

            GAMEPLAY_DEBUG_TRACE(
                "shop_goodbye_debug decision house_id=" + std::to_string(pHostHouseEntry->id)
                + " house_name=\"" + pHostHouseEntry->name + "\""
                + " house_type=\"" + pHostHouseEntry->type + "\""
                + " transaction_performed=" + debugBoolString(transactionPerformed)
                + " shop_banned=" + debugBoolString(shopBanned)
                + " party_gold=" + std::to_string(partyGold)
                + " proprietor_line=" + goodbyeSoundName
                + " party_should_respond=" + debugBoolString(goodbyeResult.queueRudeSpeech));

            if (goodbyeResult.soundType.has_value())
            {
                const std::optional<uint32_t> soundId =
                    deriveHouseSoundId(*pHostHouseEntry, *goodbyeResult.soundType);

                if (soundId.has_value())
                {
                    GAMEPLAY_DEBUG_TRACE(
                        "shop_goodbye_debug proprietor_play house_id="
                        + std::to_string(pHostHouseEntry->id)
                        + " line=" + goodbyeSoundName
                        + " sound_id=" + std::to_string(*soundId));
                    playHouseSound(context, *soundId);
                }
                else
                {
                    GAMEPLAY_DEBUG_TRACE(
                        "shop_goodbye_debug proprietor_missing_sound house_id="
                        + std::to_string(pHostHouseEntry->id)
                        + " line=" + goodbyeSoundName);
                }
            }
            else
            {
                GAMEPLAY_DEBUG_TRACE(
                    "shop_goodbye_debug proprietor_silent house_id="
                    + std::to_string(pHostHouseEntry->id));
            }

            if (goodbyeResult.queueRudeSpeech && context.pParty != nullptr)
            {
                const std::optional<size_t> memberIndex = chooseRandomActablePartyMember(*context.pParty);

                if (memberIndex.has_value())
                {
                    queueDelayedSpeechReaction(
                        context,
                        *memberIndex,
                        SpeechId::ShopRude,
                        ShopRudeSpeechDelaySeconds);
                    GAMEPLAY_DEBUG_TRACE(
                        "shop_goodbye_debug party_response_queued house_id="
                        + std::to_string(pHostHouseEntry->id)
                        + " member_index=" + std::to_string(*memberIndex)
                        + " speech=ShopRude"
                        + " delay_seconds=" + std::to_string(ShopRudeSpeechDelaySeconds));
                }
                else
                {
                    GAMEPLAY_DEBUG_TRACE(
                        "shop_goodbye_debug party_response_skipped house_id="
                        + std::to_string(pHostHouseEntry->id)
                        + " reason=no_actable_member");
                }
            }
            else if (goodbyeResult.queueRudeSpeech)
            {
                GAMEPLAY_DEBUG_TRACE(
                    "shop_goodbye_debug party_response_skipped house_id="
                    + std::to_string(pHostHouseEntry->id)
                    + " reason=no_party");
            }
            else
            {
                GAMEPLAY_DEBUG_TRACE(
                    "shop_goodbye_debug party_response_not_needed house_id="
                    + std::to_string(pHostHouseEntry->id));
            }

            context.uiController.clearHouseShopVisitState();
        }
    }

    if (pHostHouseEntry != nullptr
        && (pHostHouseEntry->sourceVendorId != 0 || pHostHouseEntry->sourceServiceId != 0)
        && context.eventRuntimeState.dialogueState.suspendedMm9RudeDialogue.has_value()
        && context.pMm9RudeDialogueTable != nullptr
        && context.pParty != nullptr)
    {
        const EventRuntimeState::SuspendedMm9RudeDialogue suspended =
            *context.eventRuntimeState.dialogueState.suspendedMm9RudeDialogue;
        context.eventRuntimeState.pendingDialogueContext.reset();
        context.eventRuntimeState.dialogueState = {};
        context.eventRuntimeState.dialogueState.mm9RudeSourceDecorationKey = suspended.sourceDecorationKey;
        context.activeEventDialog = buildMm9RudeContent(
            *context.pMm9RudeDialogueTable,
            context.pMm9SkillTrainerTable,
            *context.pParty,
            suspended.rudeId,
            suspended.nodeId,
            suspended.response,
            suspended.sourceActorIndex);
        context.activeEventDialog.mm9RudeExitCallbackExecuted = suspended.exitCallbackExecuted;
        context.selectionIndex = std::min<size_t>(
            suspended.selectionIndex,
            context.activeEventDialog.actions.empty() ? 0 : context.activeEventDialog.actions.size() - 1);
        return result;
    }

    if (!context.activeEventDialog.isHouseDialog && context.activeEventDialog.sourceId != 0)
    {
        executeNpcHook(
            context,
            EventRuntimeHookKind::NpcExit,
            context.activeEventDialog.sourceId,
            context.activeEventDialog.sourceActorIndex);
    }

    const DialogueContextKind pendingKind =
        context.eventRuntimeState.pendingDialogueContext.has_value()
            ? context.eventRuntimeState.pendingDialogueContext->kind
            : DialogueContextKind::None;
    context.eventRuntimeState.lastDialogueCanceled = EventRuntimeState::DialogueCanceled{
        .kind = dialogueContextKindName(pendingKind),
        .activeSourceId = context.activeEventDialog.sourceId,
        .houseDialog = context.activeEventDialog.isHouseDialog,
        .actionCount = context.activeEventDialog.actions.size(),
    };
    GAMEPLAY_DEBUG_TRACE(
        "dialogue_canceled kind=" + std::string(dialogueContextKindName(pendingKind))
        + " active_source_id=" + std::to_string(context.activeEventDialog.sourceId)
        + " house_dialog=" + (context.activeEventDialog.isHouseDialog ? "true" : "false")
        + " action_count=" + std::to_string(context.activeEventDialog.actions.size()));

    result.shouldCloseActiveDialog = true;
    return result;
}

bool GameplayDialogController::refreshHouseBankInputDialog(Context &context, bool showCursor) const
{
    GameplayUiController::HouseBankState &houseBankState = context.uiController.houseBankState();

    if (!houseBankState.inputActive())
    {
        return false;
    }

    const uint32_t hostHouseId = currentDialogueHostHouseId(context.eventRuntimeState);
    const HouseEntry *pHouseEntry = hostHouseId != 0 && context.pHouseTable != nullptr
        ? context.pHouseTable->get(hostHouseId)
        : nullptr;

    if (pHouseEntry == nullptr || pHouseEntry->id != houseBankState.houseId || !context.activeEventDialog.isActive)
    {
        return false;
    }

    const std::string promptLabel = houseBankState.inputMode == GameplayUiController::HouseBankInputMode::Deposit
        ? Engine::tr("Deposit")
        : Engine::tr("Withdraw");
    context.activeEventDialog.lines.clear();
    context.activeEventDialog.lines.push_back(
        Engine::tr("Balance: {gold}", {{"gold", context.pParty != nullptr ? context.pParty->bankGold() : 0}}));
    context.activeEventDialog.lines.push_back(std::string {});
    context.activeEventDialog.lines.push_back(promptLabel);
    context.activeEventDialog.lines.push_back(Engine::tr("How Much?"));
    context.activeEventDialog.lines.push_back(std::string {});
    context.activeEventDialog.actions.clear();
    context.selectionIndex = 0;
    return true;
}

GameplayDialogController::Result GameplayDialogController::returnToHouseBankMainDialog(Context &context) const
{
    Result result = {};
    result.previousMessageCount = context.eventRuntimeState.messages.size();

    GameplayUiController::HouseBankState &houseBankState = context.uiController.houseBankState();
    const uint32_t houseId = houseBankState.houseId;
    houseBankState.inputMode = GameplayUiController::HouseBankInputMode::None;
    houseBankState.inputText.clear();

    if (houseId == 0)
    {
        return result;
    }

    context.eventRuntimeState.dialogueState.hostHouseId = houseId;
    setPendingDialogueContext(context.eventRuntimeState, DialogueContextKind::HouseService, houseId, houseId);
    result.shouldOpenPendingEventDialog = true;
    return result;
}

GameplayDialogController::Result GameplayDialogController::showHouseServiceMessage(
    Context &context,
    uint32_t houseId,
    const std::string &message) const
{
    Result result = {};
    result.previousMessageCount = context.eventRuntimeState.messages.size();

    if (houseId == 0 || currentDialogueHostHouseId(context.eventRuntimeState) != houseId)
    {
        return result;
    }

    context.eventRuntimeState.messages.push_back(message);
    refreshCurrentHouseServiceDialog(context, houseId);
    result.shouldOpenPendingEventDialog = true;
    return result;
}

GameplayDialogController::Result GameplayDialogController::confirmHouseBankInput(Context &context) const
{
    GameplayUiController::HouseBankState &houseBankState = context.uiController.houseBankState();

    if (!houseBankState.inputActive() || context.pParty == nullptr)
    {
        return returnToHouseBankMainDialog(context);
    }

    const uint32_t hostHouseId = currentDialogueHostHouseId(context.eventRuntimeState);
    const HouseEntry *pHouseEntry = hostHouseId != 0 && context.pHouseTable != nullptr
        ? context.pHouseTable->get(hostHouseId)
        : nullptr;

    if (pHouseEntry == nullptr || pHouseEntry->id != houseBankState.houseId)
    {
        return returnToHouseBankMainDialog(context);
    }

    const int requestedAmount = houseBankState.inputText.empty() ? 0 : std::atoi(houseBankState.inputText.c_str());

    if (requestedAmount <= 0)
    {
        return returnToHouseBankMainDialog(context);
    }

    if (houseBankState.inputMode == GameplayUiController::HouseBankInputMode::Deposit)
    {
        int depositedAmount = requestedAmount;

        if (depositedAmount > context.pParty->gold())
        {
            const std::optional<uint32_t> soundId =
                deriveHouseSoundId(*pHouseEntry, HouseSoundType::GeneralNotEnoughGold);

            if (soundId.has_value())
            {
                playHouseSound(context, *soundId);
            }

            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::NotEnoughGold, true);
            depositedAmount = context.pParty->gold();
        }

        if (depositedAmount > 0)
        {
            context.pParty->depositGoldToBank(depositedAmount);
            houseBankState.transactionPerformed = true;

            playSpeechReaction(
                context,
                context.pParty->activeMemberIndex(),
                SpeechId::BankDeposit,
                true);
        }
    }
    else if (houseBankState.inputMode == GameplayUiController::HouseBankInputMode::Withdraw)
    {
        int withdrawnAmount = requestedAmount;

        if (withdrawnAmount > context.pParty->bankGold())
        {
            const std::optional<uint32_t> soundId =
                deriveHouseSoundId(*pHouseEntry, HouseSoundType::GeneralNotEnoughGold);

            if (soundId.has_value())
            {
                playHouseSound(context, *soundId);
            }

            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::NotEnoughGold, true);
            withdrawnAmount = context.pParty->bankGold();
        }

        if (withdrawnAmount > 0)
        {
            context.pParty->withdrawBankGold(withdrawnAmount);
            houseBankState.transactionPerformed = true;
        }
    }

    return returnToHouseBankMainDialog(context);
}

bool GameplayDialogController::rejectClosedHouseInteraction(
    Context &context,
    const HouseEntry &houseEntry) const
{
    if (context.pWorldRuntime == nullptr
        || isHouseOpenAtGameMinute(houseEntry, context.pWorldRuntime->gameMinutes()))
    {
        return false;
    }

    context.uiController.closeHouseShopOverlay();
    context.uiController.closeInventoryNestedOverlay();
    context.uiController.setStatusBarEvent(buildClosedStatusText(houseEntry));

    if (context.pParty != nullptr)
    {
        playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::StoreClosed, true);
    }

    context.eventRuntimeState.pendingDialogueContext.reset();
    context.eventRuntimeState.dialogueState = {};
    context.uiController.clearHouseBankState();
    context.uiController.clearEventDialog();
    return true;
}
}
