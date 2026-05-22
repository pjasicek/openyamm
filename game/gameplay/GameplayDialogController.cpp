#include "game/gameplay/GameplayDialogController.h"

#include "game/StringUtils.h"
#include "game/audio/SoundIds.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/gameplay/MercenaryRecruitmentRuntime.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/party/EventSpellBuffs.h"
#include "game/tables/HouseTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/SpellTable.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/tables/RosterTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <optional>
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
constexpr uint32_t ArcomageRulesTextId = 136;
constexpr uint32_t AutoNoteVariableTag = 0x00E1u;
constexpr uint32_t HeroismEffectSoundId = 14060;
constexpr float MinutesPerDay = 24.0f * 60.0f;
constexpr float OeYellowAlertDistance = 5120.0f;
constexpr int OutdoorMapTravelFoodCost = 5;
constexpr size_t MaxNpcFollowerCount = 4;
constexpr uint32_t MaxNpcFollowerFeePercent = 100;
constexpr uint32_t NpcBegTopicId = 1766;
constexpr uint32_t NpcThreatTopicId = 1767;
constexpr uint32_t NpcBribeTopicId = 1768;
constexpr int MaxFoodForCookFollower = 14;
constexpr int CookFollowerFoodAmount = 1;
constexpr int ChefFollowerFoodAmount = 2;

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

const char *mercenarySelfImpression(uint32_t level)
{
    static constexpr std::array<const char *, 5> Impressions = {
        "apprentice",
        "skilled",
        "well known",
        "masterful",
        "great",
    };
    const uint32_t bucket = std::clamp<uint32_t>((std::max<uint32_t>(1, level) + 9) / 10, 1, 5);
    return Impressions[bucket - 1];
}

std::string generatedMercenaryJoinOfferText(
    const EventRuntimeState::GeneratedMercenaryRecruit &recruit)
{
    return "Good tidings. I am " + recruit.character.name
        + ", " + mercenarySelfImpression(recruit.character.level)
        + " " + displayClassName(recruit.character.className)
        + ". I'd love to see the world and taste the adventure, but it'd be foolish to go alone. "
          "Perhaps I could come with you?";
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

bool isCurrentMapDungeon(const GameplayDialogController::Context &context)
{
    if (context.pCurrentMap != nullptr)
    {
        return isDungeonMapFileName(context.pCurrentMap->fileName);
    }

    return context.pWorldRuntime != nullptr && context.pWorldRuntime->isIndoorMap();
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
    if (context.pWorldRuntime == nullptr)
    {
        return false;
    }

    const float partyX = context.pWorldRuntime->partyX();
    const float partyY = context.pWorldRuntime->partyY();
    const float partyFootZ = context.pWorldRuntime->partyFootZ();

    for (size_t actorIndex = 0; actorIndex < context.pWorldRuntime->mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!context.pWorldRuntime->actorRuntimeState(actorIndex, actorState)
            || actorState.isDead
            || actorState.isInvisible
            || !actorState.hostileToParty
            || !actorState.hasDetectedParty)
        {
            continue;
        }

        const float deltaX = actorState.preciseX - partyX;
        const float deltaY = actorState.preciseY - partyY;
        const float deltaZ = actorState.preciseZ - partyFootZ;
        const float centerDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
        const float edgeDistance = std::max(0.0f, centerDistance - static_cast<float>(actorState.radius));

        if (edgeDistance < OeYellowAlertDistance)
        {
            return true;
        }
    }

    return false;
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

bool tryAddRuntimeMapNote(
    EventRuntimeState &eventRuntimeState,
    const MasteryTeacherTopicDefinition &teacherTopic,
    uint32_t continent,
    const MapStatsEntry *pCurrentMap,
    const IGameplayWorldRuntime *pWorldRuntime,
    const Party *pParty,
    bool queueAutonoteFx = true)
{
    if (pCurrentMap == nullptr || pCurrentMap->fileName.empty() || continent == 0)
    {
        return false;
    }

    const uint32_t noteId = continent * 1000 + teacherTopic.masteryRank * 100 + teacherTopic.skillId;
    const std::string noteMapFileName = toLowerCopy(pCurrentMap->fileName);
    const std::optional<EventRuntimeState::MapNoteSourcePoint> mapNoteSourcePoint =
        eventRuntimeState.pendingDialogueContext
            ? eventRuntimeState.pendingDialogueContext->mapNoteSourcePoint
            : std::nullopt;
    const auto noteIt = eventRuntimeState.runtimeMapNotes.find(noteId);

    if (noteIt != eventRuntimeState.runtimeMapNotes.end()
        && noteIt->second.active
        && toLowerCopy(noteIt->second.mapFileName) == noteMapFileName)
    {
        if (mapNoteSourcePoint)
        {
            noteIt->second.x = mapNoteSourcePoint->x;
            noteIt->second.y = mapNoteSourcePoint->y;
        }

        return false;
    }

    EventRuntimeState::RuntimeMapNote note = {};
    note.id = noteId;
    note.text = displaySkillName(teacherTopic.skillName) + " - " + masteryDisplayName(teacherTopic.targetMastery);
    note.active = true;
    note.mapFileName = noteMapFileName;

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

    eventRuntimeState.runtimeMapNotes[noteId] = std::move(note);
    if (queueAutonoteFx)
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
    const Party *pParty)
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

    const uint32_t rawId = (*autonoteId << 16) | AutoNoteVariableTag;
    const auto variableIt = eventRuntimeState.variables.find(rawId);
    bool changed = false;

    if (variableIt == eventRuntimeState.variables.end() || variableIt->second == 0)
    {
        eventRuntimeState.variables[rawId] = 1;
        changed = true;
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
                false)
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
        context.uiController.setStatusBarEvent("The Adventurer's Inn is empty.");
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
    const Party *pParty)
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

void applyTravelFoodAndFatigue(Party &party, int foodRequired, float gameMinutes)
{
    if (foodRequired <= 0)
    {
        return;
    }

    const int availableFood = party.food();

    if (availableFood > 0)
    {
        party.addFood(-foodRequired);
    }

    if (availableFood >= foodRequired)
    {
        return;
    }

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const Character *pMember = party.member(memberIndex);

        if (pMember == nullptr || pMember->health <= 0)
        {
            continue;
        }

        party.applyMemberCondition(memberIndex, CharacterCondition::Weak, gameMinutes);
    }
}

void applyMapTransitionTravelSideEffects(
    GameplayDialogController::Context &context,
    const MapEdgeTransition &transition)
{
    if (context.pScreenRuntime != nullptr)
    {
        context.pScreenRuntime->stopAllAudioPlayback();
    }

    if (context.pWorldRuntime != nullptr && transition.travelDays > 0)
    {
        const float travelMinutes = static_cast<float>(transition.travelDays) * MinutesPerDay;
        const float beforeGameMinutes = context.pWorldRuntime->gameMinutes();
        context.pWorldRuntime->advanceGameMinutes(travelMinutes);
        if (context.pParty != nullptr)
        {
            context.pParty->advanceTimedStates(travelMinutes * 60.0f);
        }
        const float afterGameMinutes = context.pWorldRuntime->gameMinutes();
        GAMEPLAY_DEBUG_TRACE(
            "game_time_advanced source=map_transition"
            " minutes=" + std::to_string(travelMinutes)
            + " before_game_minutes=" + std::to_string(beforeGameMinutes)
            + " after_game_minutes=" + std::to_string(afterGameMinutes)
            + " game_minutes=" + std::to_string(afterGameMinutes));
    }

    const int foodRequired = mapTransitionTravelFoodRequired(context, transition);
    const bool appliesTravelRecovery = transition.travelDays > 0 || foodRequired > 0;

    if (context.pParty != nullptr && appliesTravelRecovery)
    {
        context.pParty->restAndHealAll();
        const float gameMinutes = context.pWorldRuntime != nullptr ? context.pWorldRuntime->gameMinutes() : 0.0f;
        applyTravelFoodAndFatigue(*context.pParty, foodRequired, gameMinutes);
    }
}

void applyPendingMapMoveTravelSideEffects(
    GameplayDialogController::Context &context,
    const EventRuntimeState::PendingMapMove &move)
{
    const int travelDays = outdoorMapMoveTravelDays(context, move);

    if (travelDays <= 0)
    {
        return;
    }

    if (context.pScreenRuntime != nullptr)
    {
        context.pScreenRuntime->stopAllAudioPlayback();
    }

    if (context.pWorldRuntime != nullptr)
    {
        const float travelMinutes = static_cast<float>(travelDays) * MinutesPerDay;
        const float beforeGameMinutes = context.pWorldRuntime->gameMinutes();
        context.pWorldRuntime->advanceGameMinutes(travelMinutes);
        if (context.pParty != nullptr)
        {
            context.pParty->advanceTimedStates(travelMinutes * 60.0f);
        }
        const float afterGameMinutes = context.pWorldRuntime->gameMinutes();
        GAMEPLAY_DEBUG_TRACE(
            "game_time_advanced source=event_map_transition"
            " minutes=" + std::to_string(travelMinutes)
            + " before_game_minutes=" + std::to_string(beforeGameMinutes)
            + " after_game_minutes=" + std::to_string(afterGameMinutes)
            + " game_minutes=" + std::to_string(afterGameMinutes));
    }

    if (context.pParty != nullptr)
    {
        context.pParty->restAndHealAll();
        const float gameMinutes = context.pWorldRuntime != nullptr ? context.pWorldRuntime->gameMinutes() : 0.0f;
        applyTravelFoodAndFatigue(*context.pParty, OutdoorMapTravelFoodCost, gameMinutes);
    }
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

bool executeNpcTopicEvent(
    GameplayDialogController::Context &context,
    uint16_t eventId,
    size_t &previousMessageCount)
{
    return context.pWorldRuntime != nullptr
        && context.pWorldRuntime->executeNpcTopicEvent(eventId, previousMessageCount);
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

    if (!tryApplyEventSpellBuffs(*context.pParty, spellId, skillLevel, rawSkillMastery))
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
        context.eventRuntimeState.messages.push_back("That topic does not have an event yet.");
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
        context.eventRuntimeState.messages.push_back("Sorry, come back another day");
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
                    clearPartyCondition(*context.pParty, CharacterCondition::PoisonWeak);
                    clearPartyCondition(*context.pParty, CharacterCondition::PoisonMedium);
                    clearPartyCondition(*context.pParty, CharacterCondition::PoisonSevere);
                    clearPartyCondition(*context.pParty, CharacterCondition::DiseaseWeak);
                    clearPartyCondition(*context.pParty, CharacterCondition::DiseaseMedium);
                    clearPartyCondition(*context.pParty, CharacterCondition::DiseaseSevere);
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
                if (context.pParty->food() > MaxFoodForCookFollower)
                {
                    context.eventRuntimeState.messages.push_back("Your packs are already full!");
                    return execution;
                }

                context.pParty->addFood(
                    professionId == NpcProfessionId::Chef
                        ? ChefFollowerFoodAmount
                        : CookFollowerFoodAmount);
                applied = true;
            }
            break;

        case static_cast<uint32_t>(NpcFollowerActionTopicId::CastFly):
            applied = professionId == NpcProfessionId::WindMaster
                && castNpcFollowerPartySpell(context, spellIdValue(SpellId::Fly), 2, 3);
            break;

        case static_cast<uint32_t>(NpcFollowerActionTopicId::CastWaterWalk):
            applied = professionId == NpcProfessionId::WaterMaster
                && castNpcFollowerPartySpell(context, spellIdValue(SpellId::WaterWalk), 3, 3);
            break;

        case static_cast<uint32_t>(NpcFollowerActionTopicId::CastTownPortal):
            if (professionId == NpcProfessionId::GateMaster)
            {
                markNpcProfessionActionUsed(context.eventRuntimeState, npcId, context.pWorldRuntime, context.pParty);

                const size_t casterMemberIndex =
                    context.pParty->members().empty() ? 0u : context.pParty->activeMemberIndex();
                context.uiController.openUtilitySpellOverlay(
                    GameplayUiController::UtilitySpellOverlayMode::TownPortal,
                    spellIdValue(SpellId::TownPortal),
                    casterMemberIndex);
                GameplayUiController::UtilitySpellOverlayState &overlay =
                    context.uiController.utilitySpellOverlay();
                overlay.skillLevelOverride = 10;
                overlay.skillMasteryOverride = SkillMastery::Grandmaster;
                overlay.spendMana = false;
                overlay.applyRecovery = false;
                overlay.bypassGameplayCasterValidation = true;
                overlay.bypassTownPortalFailureChecks = true;

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
        context.eventRuntimeState.messages.push_back("That topic does not have an event yet.");
        return execution;
    }

    markNpcProfessionActionUsed(context.eventRuntimeState, npcId, context.pWorldRuntime, context.pParty);
    context.eventRuntimeState.messages.push_back("Done!");
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
        runtimeState.variables[autonoteVariableKey(offer.autonoteId)] = 1;
    }
}

std::string npcTextOrFallback(const NpcDialogTable *pNpcDialogTable, uint32_t textId, const std::string &fallback)
{
    if (pNpcDialogTable == nullptr)
    {
        return fallback;
    }

    const std::optional<std::string> text = pNpcDialogTable->getText(textId);
    return text && !text->empty() ? *text : fallback;
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

void replaceAllInPlace(std::string &text, const std::string &from, const std::string &to)
{
    if (from.empty())
    {
        return;
    }

    size_t position = 0;
    while ((position = text.find(from, position)) != std::string::npos)
    {
        text.replace(position, from.length(), to);
        position += to.length();
    }
}

std::string formatNpcProfessionText(
    std::string text,
    const NpcEntry &npc,
    const MergedNpcProfessionEntry &profession,
    const Party *pParty,
    int effectiveReputation = 0,
    std::optional<int> requiredReputation = std::nullopt)
{
    const Character *pActiveMember = nullptr;

    if (pParty != nullptr)
    {
        pActiveMember = pParty->member(pParty->activeMemberIndex());
    }

    const std::string activeMemberName = pActiveMember != nullptr && !pActiveMember->name.empty()
        ? pActiveMember->name
        : "traveler";

    replaceAllInPlace(text, "%01", npc.name);
    replaceAllInPlace(text, "%02", activeMemberName);
    replaceAllInPlace(text, "%04", std::to_string(profession.weeklyCost));
    replaceAllInPlace(text, "%11", reputationLabel(effectiveReputation));
    replaceAllInPlace(
        text,
        "%12",
        reputationLabel(requiredReputation.has_value() ? *requiredReputation : effectiveReputation));
    replaceAllInPlace(text, "%14", profession.profession);
    replaceAllInPlace(text, "%17", std::to_string(profession.weeklyCost / 100u));
    return text;
}

int effectiveReputationForContext(const GameplayDialogController::Context &context)
{
    return context.pWorldRuntime != nullptr
        ? effectivePartyReputation(
            context.pWorldRuntime->currentLocationReputation(),
            context.pWorldRuntime->eventRuntimeState())
        : 0;
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
}

GameplayDialogController::Result GameplayDialogController::executeActiveDialogAction(Context &context) const
{
    Result result = {};
    result.previousMessageCount = context.eventRuntimeState.messages.size();

    if (!context.activeEventDialog.isActive
        || context.selectionIndex >= context.activeEventDialog.actions.size())
    {
        return result;
    }

    const EventDialogAction &action = context.activeEventDialog.actions[context.selectionIndex];
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

    if (action.kind == EventDialogActionKind::MapTransitionConfirm)
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

        if (context.eventRuntimeState.pendingDialogueContext->transitionMapMove.has_value())
        {
            logMapTransitionConfirmed(
                context.eventRuntimeState,
                *context.eventRuntimeState.pendingDialogueContext,
                *context.eventRuntimeState.pendingDialogueContext->transitionMapMove,
                action.id);

            if (context.pScreenRuntime != nullptr)
            {
                context.pScreenRuntime->stopAllAudioPlayback();
            }

            applyPendingMapMoveTravelSideEffects(
                context,
                *context.eventRuntimeState.pendingDialogueContext->transitionMapMove);
            context.eventRuntimeState.pendingMapMove =
                *context.eventRuntimeState.pendingDialogueContext->transitionMapMove;
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

        applyMapTransitionTravelSideEffects(context, **pTransition);

        EventRuntimeState::PendingMapMove pendingMapMove = {};
        pendingMapMove.mapName = (*pTransition)->destinationMapFileName;
        pendingMapMove.directionDegrees = (*pTransition)->directionDegrees;
        pendingMapMove.useMapStartPosition = (*pTransition)->useMapStartPosition;
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

        logMapTransitionConfirmed(
            context.eventRuntimeState,
            *context.eventRuntimeState.pendingDialogueContext,
            pendingMapMove,
            action.id);
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
                const char *pMessage = arcomageDeckRequiredMessage();
                context.eventRuntimeState.messages.push_back(pMessage);
                context.uiController.setStatusBarEvent(pMessage);
                refreshCurrentHouseServiceDialog(context, pHouseEntry->id);
                result.shouldOpenPendingEventDialog = true;
                return result;
            }

            EventRuntimeState::PendingArcomageGame pendingGame = {};
            pendingGame.houseId = pHouseEntry->id;
            context.eventRuntimeState.pendingArcomageGame = std::move(pendingGame);
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
            context.uiController.openHouseShopOverlay(
                pHouseEntry->id,
                GameplayUiController::HouseShopMode::BuySpellbooks);
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
                context.pWorldRuntime
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
                && option.id == HouseActionId::TransportRoute)
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
            context.eventRuntimeState.messages.push_back("That companion is not ready to join yet.");
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
            context.eventRuntimeState.messages.push_back("That companion is not ready to join yet.");
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
                    recruit.character.name + " waits at the Adventurer's Inn.");
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
                context.eventRuntimeState.messages.push_back("Recruitment is not available for this companion yet.");
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
            context.eventRuntimeState.messages.push_back(recruit.character.name + " joined the party.");
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
            context.eventRuntimeState.messages.push_back("Recruitment is not available for this companion yet.");
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
        context.eventRuntimeState.messages.push_back(pRosterEntry->name + " joined the party.");
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
            context.eventRuntimeState.messages.push_back("That topic does not have an event yet.");
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        if (hasGuildMembership(context.eventRuntimeState, context.pParty, offer->guildType))
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                124,
                "You're already a member of this guild."));
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
            context.eventRuntimeState.messages.push_back("That topic does not have an event yet.");
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        if (hasGuildMembership(context.eventRuntimeState, context.pParty, offer->guildType))
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                124,
                "You're already a member of this guild."));
        }
        else if (context.pParty->gold() < static_cast<int>(offer->cost))
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                125,
                "You don't have enough gold!"));
            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::NotEnoughGold, true);
        }
        else
        {
            context.pParty->addGold(-static_cast<int>(offer->cost));
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
            || !continentAllowsNpcFollowers(context.pCurrentMap, context.pContinentSettingTable))
        {
            context.eventRuntimeState.messages.push_back("That follower is not available.");
            result.shouldOpenPendingEventDialog = true;
            return result;
        }

        std::string message = npcTextOrFallback(
            context.pNpcDialogTable,
            pProfession->joinTextId,
            "I will join you.");

        if (pProfession->descriptionTextId != 0)
        {
            const std::optional<std::string> description = context.pNpcDialogTable->getText(pProfession->descriptionTextId);

            if (description && !description->empty())
            {
                message += "\n(" + *description + ")";
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
            || !continentAllowsNpcFollowers(context.pCurrentMap, context.pContinentSettingTable))
        {
            context.eventRuntimeState.messages.push_back("That follower is not available.");
        }
        else if (hasHiredNpcFollower(context.eventRuntimeState, offer.npcId))
        {
            context.eventRuntimeState.messages.push_back(pNpc->name + " is already following you.");
        }
        else if (context.eventRuntimeState.hiredNpcFollowers.size() >= MaxNpcFollowerCount
            || hiredNpcFollowerFeePercent(context.eventRuntimeState) >= MaxNpcFollowerFeePercent)
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                533,
                "You already have enough followers."));
        }
        else if (context.pParty->gold() < static_cast<int>(pProfession->weeklyCost))
        {
            context.eventRuntimeState.messages.push_back(npcTextOrFallback(
                context.pNpcDialogTable,
                125,
                "You do not have enough gold."));
        }
        else
        {
            context.pParty->addGold(-static_cast<int>(pProfession->weeklyCost));

            EventRuntimeState::HiredNpcFollower follower = {};
            follower.npcId = offer.npcId;
            follower.professionId = pNpc->professionId;
            follower.weeklyCost = pProfession->weeklyCost;
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

            context.eventRuntimeState.messages.push_back(pNpc->name + " joined the followers.");
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
                (pNpc != nullptr && !pNpc->name.empty() ? pNpc->name : "The follower") + " left the followers.");
        }

        result.shouldCloseActiveDialog = true;
        return result;
    }

    if (action.kind == EventDialogActionKind::NpcProfessionDescription)
    {
        if (context.pNpcDialogTable != nullptr && action.secondaryId != 0)
        {
            const std::optional<std::string> description = context.pNpcDialogTable->getText(action.secondaryId);

            if (description && !description->empty())
            {
                context.eventRuntimeState.messages.push_back(*description);
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
                    context.eventRuntimeState.messages.push_back("You don't have enough gold.");
                }
                else
                {
                    context.pParty->addGold(-static_cast<int>(bribeCost));
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
            context.eventRuntimeState.messages.push_back("That topic does not have an event yet.");
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

    if (action.kind == EventDialogActionKind::NpcTopic)
    {
        const uint32_t npcId = context.activeEventDialog.sourceId;
        const std::optional<EventRuntimeState::PendingDialogueContext> previousPendingDialogueContext =
            context.eventRuntimeState.pendingDialogueContext;
        bool executed = false;

        if (action.textOnly && context.pNpcDialogTable != nullptr)
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
        else
        {
            size_t executionPreviousMessageCount = result.previousMessageCount;
            executed = executeNpcTopicEvent(context, static_cast<uint16_t>(action.id), executionPreviousMessageCount);
        }

        if (!executed)
        {
            context.eventRuntimeState.messages.push_back("That topic does not have an event yet.");
        }

        if (context.eventRuntimeState.pendingWinGame)
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

GameplayDialogController::Result GameplayDialogController::openNpcNews(
    Context &context,
    uint32_t npcId,
    uint32_t newsId,
    const std::string &titleOverride,
    const std::string &newsText,
    uint32_t participantPictureId) const
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

    if (context.eventRuntimeState.pendingDialogueContext.has_value()
        && context.eventRuntimeState.pendingDialogueContext->kind == DialogueContextKind::MapTransition)
    {
        cancelMapTransition(context);
        result.shouldCloseActiveDialog = true;
        return result;
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
                 && context.pParty != nullptr
                 && context.pWorldRuntime != nullptr
                 && effectivePartyReputation(
                        context.pWorldRuntime->currentLocationReputation(),
                        context.pWorldRuntime->eventRuntimeState()) > 10)
        {
            const std::optional<uint32_t> soundId =
                deriveHouseSoundId(*pHostHouseEntry, HouseSoundType::ShopGoodbyeRude);

            if (soundId.has_value())
            {
                playHouseSound(context, *soundId);
            }

            playSpeechReaction(context, context.pParty->activeMemberIndex(), SpeechId::ShopRude, true);
        }
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

    const std::string promptLabel =
        houseBankState.inputMode == GameplayUiController::HouseBankInputMode::Deposit ? "Deposit" : "Withdraw";
    const std::string enteredText = houseBankState.inputText.empty()
        ? (showCursor ? "_" : "")
        : (houseBankState.inputText + (showCursor ? "_" : ""));

    context.activeEventDialog.lines.clear();
    context.activeEventDialog.lines.push_back(
        "Balance: " + std::to_string(context.pParty != nullptr ? context.pParty->bankGold() : 0));
    context.activeEventDialog.lines.push_back(std::string {});
    context.activeEventDialog.lines.push_back(promptLabel);
    context.activeEventDialog.lines.push_back("How Much?");
    context.activeEventDialog.lines.push_back(std::string {});
    context.activeEventDialog.lines.push_back(enteredText);
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
