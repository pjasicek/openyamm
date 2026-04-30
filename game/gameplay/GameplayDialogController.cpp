#include "game/gameplay/GameplayDialogController.h"

#include "game/StringUtils.h"
#include "game/audio/SoundIds.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/tables/MapStats.h"
#include "game/tables/NpcDialogTable.h"
#include "game/party/Party.h"
#include "game/tables/RosterTable.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t AdventurersInnHouseId = 185;
constexpr uint32_t ArcomageRulesTextId = 136;
constexpr uint32_t AutoNoteVariableTag = 0x00E1u;
constexpr uint32_t ExpertTrainerTopicIdFirst = 300;
constexpr uint32_t GrandMasterTrainerTopicIdLast = 416;
constexpr uint32_t TeacherHintTopicIdFirst = 417;
constexpr uint32_t TeacherHintTopicIdLast = 530;
constexpr uint32_t TrainerAutoNoteIdFirst = 128;
constexpr uint32_t HeroismEffectSoundId = 14060;
constexpr float MinutesPerDay = 24.0f * 60.0f;
constexpr float OeYellowAlertDistance = 5120.0f;
constexpr int OutdoorMapTravelFoodCost = 5;

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

bool isCurrentMapDungeon(const GameplayDialogController::Context &context)
{
    if (context.pCurrentMap != nullptr)
    {
        return isDungeonMapFileName(context.pCurrentMap->fileName);
    }

    return context.pWorldRuntime != nullptr && context.pWorldRuntime->isIndoorMap();
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

void setPendingDialogueContext(
    EventRuntimeState &eventRuntimeState,
    DialogueContextKind kind,
    uint32_t sourceId,
    uint32_t hostHouseId)
{
    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = kind;
    context.sourceId = sourceId;
    context.hostHouseId = hostHouseId;
    eventRuntimeState.pendingDialogueContext = std::move(context);
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
        && left.useMapStartPosition == right.useMapStartPosition;
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
        && left->hostHouseId == right->hostHouseId
        && left->newsId == right->newsId
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

std::optional<uint32_t> trainerAutoNoteRawIdForTopic(uint32_t topicId)
{
    uint32_t noteId = 0;

    // MM8 keeps mastery-teacher topics and trainer-location autonotes in matching table order.
    if (topicId >= ExpertTrainerTopicIdFirst && topicId <= GrandMasterTrainerTopicIdLast)
    {
        noteId = TrainerAutoNoteIdFirst + (topicId - ExpertTrainerTopicIdFirst);
    }
    else if (topicId >= TeacherHintTopicIdFirst && topicId <= TeacherHintTopicIdLast)
    {
        noteId = TrainerAutoNoteIdFirst + (topicId - TeacherHintTopicIdFirst);
    }
    else
    {
        return std::nullopt;
    }

    return (noteId << 16) | AutoNoteVariableTag;
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
        EventRuntimeState::PendingSound sound = {};
        sound.soundId = static_cast<uint32_t>(*soundId);
        sound.positional = false;
        eventRuntimeState.pendingSounds.push_back(sound);
    }
}

bool tryUnlockTrainerAutoNote(
    EventRuntimeState &eventRuntimeState,
    uint32_t topicId,
    const Party *pParty)
{
    const std::optional<uint32_t> rawId = trainerAutoNoteRawIdForTopic(topicId);

    if (!rawId.has_value())
    {
        return false;
    }

    const auto variableIt = eventRuntimeState.variables.find(*rawId);

    if (variableIt != eventRuntimeState.variables.end() && variableIt->second != 0)
    {
        return false;
    }

    eventRuntimeState.variables[*rawId] = 1;
    queuePortraitFxRequest(eventRuntimeState, PortraitFxEventKind::AutoNote, pParty);
    return true;
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

    for (const auto &[npcId, houseId] : context.eventRuntimeState.npcHouseOverrides)
    {
        if (houseId != AdventurersInnHouseId || context.eventRuntimeState.unavailableNpcIds.contains(npcId))
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
    if (houseId != AdventurersInnHouseId || context.pParty == nullptr)
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
    uint32_t npcId)
{
    const auto overrideIt = eventRuntimeState.npcTopicOverrides.find(npcId);
    const std::unordered_map<uint32_t, uint32_t> *pTopicOverrides =
        overrideIt != eventRuntimeState.npcTopicOverrides.end() ? &overrideIt->second : nullptr;
    const std::vector<NpcDialogTable::ResolvedTopic> topics = npcDialogTable.getTopicsForNpc(npcId, pTopicOverrides);

    for (const NpcDialogTable::ResolvedTopic &topic : topics)
    {
        if (topic.specialKind == NpcTopicEntry::SpecialKind::MasteryTeacherOffer)
        {
            return topic.id;
        }
    }

    return std::nullopt;
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

void applyTravelFoodAndFatigue(Party &party, int foodRequired)
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

        party.applyMemberCondition(memberIndex, CharacterCondition::Weak);
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

    if (context.pWorldRuntime != nullptr)
    {
        context.pWorldRuntime->requestTravelAutosave();
    }

    if (context.pWorldRuntime != nullptr && transition.travelDays > 0)
    {
        context.pWorldRuntime->advanceGameMinutes(static_cast<float>(transition.travelDays) * MinutesPerDay);
    }

    if (context.pParty != nullptr)
    {
        context.pParty->restAndHealAll();
        applyTravelFoodAndFatigue(*context.pParty, mapTransitionTravelFoodRequired(context, transition));
    }
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
        if (!context.eventRuntimeState.pendingDialogueContext.has_value())
        {
            result.shouldCloseActiveDialog = true;
            return result;
        }

        if (context.eventRuntimeState.pendingDialogueContext->transitionMapMove.has_value())
        {
            if (context.pScreenRuntime != nullptr)
            {
                context.pScreenRuntime->stopAllAudioPlayback();
            }

            if (context.pWorldRuntime != nullptr)
            {
                context.pWorldRuntime->requestTravelAutosave();
            }

            context.eventRuntimeState.pendingMapMove =
                *context.eventRuntimeState.pendingDialogueContext->transitionMapMove;
            result.shouldCloseActiveDialog = false;
            return result;
        }

        const std::optional<MapEdgeTransition> *pTransition =
            currentMapTransitionForContext(context, *context.eventRuntimeState.pendingDialogueContext);

        if (pTransition == nullptr || !pTransition->has_value())
        {
            result.shouldCloseActiveDialog = true;
            return result;
        }

        applyMapTransitionTravelSideEffects(context, **pTransition);

        EventRuntimeState::PendingMapMove pendingMapMove = {};
        pendingMapMove.mapName = (*pTransition)->destinationMapFileName;
        pendingMapMove.directionDegrees = (*pTransition)->directionDegrees;
        pendingMapMove.useMapStartPosition = (*pTransition)->useMapStartPosition;

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

        context.eventRuntimeState.pendingMapMove = std::move(pendingMapMove);
        result.shouldCloseActiveDialog = false;
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

            if (houseResult.succeeded && option.id == HouseActionId::TempleHeal)
            {
                playCommonUiSound(context, SoundId::Heal);

                playSpeechReaction(
                    context,
                    context.pParty->activeMemberIndex(),
                    SpeechId::TempleHeal,
                    true);
            }

            if (houseResult.succeeded
                && option.id == HouseActionId::TempleDonate)
            {
                playSpeechReaction(
                    context,
                    context.pParty->activeMemberIndex(),
                    SpeechId::TempleDonate,
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
            || context.pParty == nullptr
            || context.pRosterTable == nullptr)
        {
            return result;
        }

        const EventRuntimeState::DialogueOfferState invite = *context.eventRuntimeState.dialogueState.currentOffer;
        context.eventRuntimeState.dialogueState.currentOffer.reset();

        const RosterEntry *pRosterEntry = context.pRosterTable->get(invite.rosterId);

        if (context.pParty->isFull())
        {
            if (pRosterEntry != nullptr && !context.pParty->hasRosterMember(invite.rosterId))
            {
                const NpcEntry *pNpcEntry =
                    context.pNpcDialogTable != nullptr ? context.pNpcDialogTable->getNpc(invite.npcId) : nullptr;
                const uint32_t portraitPictureId = pNpcEntry != nullptr ? pNpcEntry->pictureId : 0;
                context.pParty->addAdventurersInnMember(*pRosterEntry, portraitPictureId);
            }

            context.eventRuntimeState.npcHouseOverrides[invite.npcId] = AdventurersInnHouseId;
            context.pParty->setNpcHouseOverride(invite.npcId, AdventurersInnHouseId);

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
        tryUnlockTrainerAutoNote(context.eventRuntimeState, action.id, context.pParty);

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
                message))
        {
            if (!message.empty())
            {
                context.uiController.setStatusBarEvent(message);
            }

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
                *context.pNpcDialogTable
            );

            if (evaluation && !evaluation->displayText.empty())
            {
                context.uiController.setStatusBarEvent(evaluation->displayText);
            }

            result.shouldOpenPendingEventDialog = true;
        }

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
                tryUnlockTrainerAutoNote(context.eventRuntimeState, topic->id, context.pParty);
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
        context.pWorldRuntime != nullptr ? context.pWorldRuntime->gameMinutes() : -1.0f
    ));

    if (context.eventRuntimeState.pendingDialogueContext.has_value()
        && context.eventRuntimeState.pendingDialogueContext->kind == DialogueContextKind::NpcTalk
        && context.pNpcDialogTable != nullptr
        && context.pParty != nullptr)
    {
        const std::optional<uint32_t> masteryTopicId = masteryTeacherTopicIdForNpc(
            *context.pNpcDialogTable,
            context.eventRuntimeState,
            context.eventRuntimeState.pendingDialogueContext->sourceId);

        if (masteryTopicId.has_value())
        {
            tryUnlockTrainerAutoNote(context.eventRuntimeState, *masteryTopicId, context.pParty);
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
    uint32_t hostHouseId) const
{
    Result result = {};
    result.previousMessageCount = context.eventRuntimeState.messages.size();

    if (npcId == 0)
    {
        return result;
    }

    context.eventRuntimeState.dialogueState.hostHouseId = hostHouseId;
    setPendingDialogueContext(context.eventRuntimeState, DialogueContextKind::NpcTalk, npcId, hostHouseId);
    result.shouldOpenPendingEventDialog = true;
    return result;
}

GameplayDialogController::Result GameplayDialogController::openNpcNews(
    Context &context,
    uint32_t npcId,
    uint32_t newsId,
    const std::string &titleOverride,
    const std::string &newsText) const
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
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseResident;
            });
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
        && hostResidentNpcIds.size() > 1)
    {
        setPendingDialogueContext(context.eventRuntimeState, DialogueContextKind::HouseService, hostHouseId, hostHouseId);
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
    }

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
