#include "game/gameplay/GameplayDialogController.h"

#include "game/HouseInteraction.h"
#include "game/MasteryTeacherDialog.h"
#include "game/NpcDialogTable.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/Party.h"
#include "game/RosterTable.h"

#include <cstdlib>
#include <optional>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t AdventurersInnHouseId = 185;

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

bool isBoatHouse(const HouseEntry &houseEntry)
{
    return houseEntry.type == "Boats";
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
                context.pOutdoorWorldRuntime
            );

            if (houseResult.soundType.has_value() && context.callbacks.playHouseSound)
            {
                const std::optional<uint32_t> soundId = deriveHouseSoundId(*pHouseEntry, *houseResult.soundType);

                if (soundId.has_value())
                {
                    context.callbacks.playHouseSound(*soundId);
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
                && option.id == HouseActionId::TrainingTrainActiveMember
                && context.callbacks.playSpeechReaction)
            {
                context.callbacks.playSpeechReaction(
                    context.pParty->activeMemberIndex(),
                    SpeechId::LevelUp,
                    true);
            }

            if (houseResult.succeeded && option.id == HouseActionId::TempleHeal)
            {
                if (context.callbacks.playCommonSound)
                {
                    context.callbacks.playCommonSound(SoundId::Heal);
                }

                if (context.callbacks.playSpeechReaction)
                {
                    context.callbacks.playSpeechReaction(
                        context.pParty->activeMemberIndex(),
                        SpeechId::TempleHeal,
                        true);
                }
            }

            if (houseResult.succeeded
                && option.id == HouseActionId::TempleDonate
                && context.callbacks.playSpeechReaction)
            {
                context.callbacks.playSpeechReaction(
                    context.pParty->activeMemberIndex(),
                    SpeechId::TempleDonate,
                    true);
            }

            if (houseResult.succeeded
                && option.id == HouseActionId::TransportRoute
                && context.callbacks.playSpeechReaction)
            {
                context.callbacks.playSpeechReaction(
                    context.pParty->activeMemberIndex(),
                    isBoatHouse(*pHouseEntry) ? SpeechId::TravelBoat : SpeechId::TravelHorse,
                    true);
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

        if (context.pParty->isFull())
        {
            context.eventRuntimeState.npcHouseOverrides[invite.npcId] = AdventurersInnHouseId;

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

        const RosterEntry *pRosterEntry = context.pRosterTable->get(invite.rosterId);

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
        context.eventRuntimeState.messages.push_back(pRosterEntry->name + " joined the party.");
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
        bool executed = false;

        if (action.textOnly && context.pNpcDialogTable != nullptr)
        {
            const std::optional<NpcDialogTable::ResolvedTopic> topic =
                context.pNpcDialogTable->getTopicById(action.secondaryId != 0 ? action.secondaryId : action.id);

            if (topic && !topic->text.empty())
            {
                context.eventRuntimeState.messages.push_back(topic->text);
                executed = true;
            }
        }
        else if (context.callbacks.executeNpcTopicEvent)
        {
            size_t executionPreviousMessageCount = result.previousMessageCount;
            executed = context.callbacks.executeNpcTopicEvent(static_cast<uint16_t>(action.id), executionPreviousMessageCount);
        }

        if (!executed)
        {
            context.eventRuntimeState.messages.push_back("That topic does not have an event yet.");
        }

        if (!context.eventRuntimeState.pendingDialogueContext)
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
        && context.pOutdoorWorldRuntime != nullptr
        && context.pParty != nullptr)
    {
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
        context.pGlobalEventIrProgram,
        context.pHouseTable,
        context.pClassSkillTable,
        context.pNpcDialogTable,
        context.pParty,
        context.pOutdoorWorldRuntime,
        context.pOutdoorWorldRuntime != nullptr ? context.pOutdoorWorldRuntime->gameMinutes() : -1.0f
    ));

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

    if (pHostHouseEntry != nullptr && context.callbacks.playHouseSound)
    {
        if (resolveHouseServiceType(*pHostHouseEntry) == HouseServiceType::Temple)
        {
            const std::optional<uint32_t> soundId =
                deriveHouseSoundId(*pHostHouseEntry, HouseSoundType::TempleGoodbye);

            if (soundId.has_value())
            {
                context.callbacks.playHouseSound(*soundId);
            }
        }
        else if (resolveHouseServiceType(*pHostHouseEntry) == HouseServiceType::Bank
                 && context.uiController.houseBankState().transactionPerformed)
        {
            const std::optional<uint32_t> soundId =
                deriveHouseSoundId(*pHostHouseEntry, HouseSoundType::BankGoodbye);

            if (soundId.has_value())
            {
                context.callbacks.playHouseSound(*soundId);
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
            if (context.callbacks.playHouseSound)
            {
                const std::optional<uint32_t> soundId =
                    deriveHouseSoundId(*pHouseEntry, HouseSoundType::GeneralNotEnoughGold);

                if (soundId.has_value())
                {
                    context.callbacks.playHouseSound(*soundId);
                }
            }

            depositedAmount = context.pParty->gold();
        }

        if (depositedAmount > 0)
        {
            context.pParty->depositGoldToBank(depositedAmount);
            houseBankState.transactionPerformed = true;

            if (context.callbacks.playSpeechReaction)
            {
                context.callbacks.playSpeechReaction(
                    context.pParty->activeMemberIndex(),
                    SpeechId::BankDeposit,
                    true);
            }
        }
    }
    else if (houseBankState.inputMode == GameplayUiController::HouseBankInputMode::Withdraw)
    {
        int withdrawnAmount = requestedAmount;

        if (withdrawnAmount > context.pParty->bankGold())
        {
            if (context.callbacks.playHouseSound)
            {
                const std::optional<uint32_t> soundId =
                    deriveHouseSoundId(*pHouseEntry, HouseSoundType::GeneralNotEnoughGold);

                if (soundId.has_value())
                {
                    context.callbacks.playHouseSound(*soundId);
                }
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
    if (context.pOutdoorWorldRuntime == nullptr
        || isHouseOpenAtGameMinute(houseEntry, context.pOutdoorWorldRuntime->gameMinutes()))
    {
        return false;
    }

    context.uiController.closeHouseShopOverlay();
    context.uiController.closeInventoryNestedOverlay();
    context.uiController.setStatusBarEvent(buildClosedStatusText(houseEntry));

    if (context.pParty != nullptr && context.callbacks.playSpeechReaction)
    {
        context.callbacks.playSpeechReaction(context.pParty->activeMemberIndex(), SpeechId::StoreClosed, true);
    }

    context.eventRuntimeState.pendingDialogueContext.reset();
    context.eventRuntimeState.dialogueState = {};
    context.uiController.clearHouseBankState();
    context.uiController.clearEventDialog();
    return true;
}
}
