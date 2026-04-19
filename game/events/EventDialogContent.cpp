#include "game/events/EventDialogContent.h"

#include "game/events/ISceneEventContext.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/StringUtils.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
const MapStatsEntry *findMapEntryByFileName(
    const std::vector<MapStatsEntry> *pMapEntries,
    const std::string &fileName)
{
    if (pMapEntries == nullptr)
    {
        return nullptr;
    }

    const std::string normalizedFileName = toLowerCopy(fileName);

    for (const MapStatsEntry &entry : *pMapEntries)
    {
        if (toLowerCopy(entry.fileName) == normalizedFileName)
        {
            return &entry;
        }
    }

    return nullptr;
}

const std::optional<MapEdgeTransition> *currentMapTransitionForContext(
    const EventRuntimeState::PendingDialogueContext &context,
    const MapStatsEntry *pCurrentMap)
{
    if (context.kind != DialogueContextKind::MapTransition || pCurrentMap == nullptr)
    {
        return nullptr;
    }

    switch (static_cast<MapBoundaryEdge>(context.sourceId))
    {
        case MapBoundaryEdge::North:
            return &pCurrentMap->northTransition;

        case MapBoundaryEdge::South:
            return &pCurrentMap->southTransition;

        case MapBoundaryEdge::East:
            return &pCurrentMap->eastTransition;

        case MapBoundaryEdge::West:
            return &pCurrentMap->westTransition;
    }

    return nullptr;
}

std::vector<std::string> wrapDialogText(const std::string &text, size_t width)
{
    if (text.empty() || width == 0)
    {
        return {};
    }

    std::vector<std::string> lines;
    std::string currentLine;

    for (char character : text)
    {
        if (character == '\r')
        {
            continue;
        }

        if (character == '\n')
        {
            lines.push_back(currentLine);
            currentLine.clear();
            continue;
        }

        currentLine.push_back(character);
    }

    if (!currentLine.empty() || lines.empty())
    {
        lines.push_back(currentLine);
    }

    return lines;
}

bool shouldDisplayHouseType(const std::string &houseType)
{
    return houseType == "Weapon Shop"
        || houseType == "Armor Shop"
        || houseType == "Magic Shop"
        || houseType == "Alchemist"
        || houseType == "Stables"
        || houseType == "Boats"
        || houseType == "Temple"
        || houseType == "Training"
        || houseType == "Town Hall"
        || houseType == "Tavern"
        || houseType == "Bank"
        || houseType == "Spell Shop"
        || houseType.find("Guild") != std::string::npos;
}

std::string buildHouseParticipantTitle(const HouseEntry &houseEntry)
{
    std::string title;

    if (!houseEntry.proprietorName.empty() && houseEntry.proprietorName != "Placeholder")
    {
        title = houseEntry.proprietorName;
    }
    else
    {
        title = houseEntry.name;
    }

    if (!houseEntry.proprietorTitle.empty() && houseEntry.proprietorTitle != "Placeholder")
    {
        title += ", " + houseEntry.proprietorTitle;
    }

    return title;
}

DialogueMenuId currentDialogueMenuId(const EventRuntimeState &eventRuntimeState)
{
    if (eventRuntimeState.dialogueState.menuStack.empty())
    {
        return DialogueMenuId::None;
    }

    return eventRuntimeState.dialogueState.menuStack.back();
}

std::vector<uint32_t> collectSelectableResidentNpcIdsImpl(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState);

std::optional<uint32_t> singleSelectableResidentNpcId(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState
)
{
    const std::vector<uint32_t> residentNpcIdsForHouse =
        collectSelectableResidentNpcIdsImpl(houseEntry, npcDialogTable, eventRuntimeState);

    std::optional<uint32_t> residentNpcId;

    for (uint32_t candidateNpcId : residentNpcIdsForHouse)
    {
        if (residentNpcId)
        {
            return std::nullopt;
        }

        residentNpcId = candidateNpcId;
    }

    return residentNpcId;
}

std::vector<uint32_t> collectSelectableResidentNpcIdsImpl(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState)
{
    std::vector<uint32_t> residentNpcIds;

    auto appendNpcId = [&](uint32_t npcId)
    {
        if (std::find(residentNpcIds.begin(), residentNpcIds.end(), npcId) != residentNpcIds.end())
        {
            return;
        }

        const NpcEntry *pResident = npcDialogTable.getNpc(npcId);

        if (pResident == nullptr || pResident->name.empty())
        {
            return;
        }

        if (eventRuntimeState.unavailableNpcIds.contains(npcId))
        {
            return;
        }

        const auto overrideIt = eventRuntimeState.npcHouseOverrides.find(npcId);

        if (overrideIt != eventRuntimeState.npcHouseOverrides.end() && overrideIt->second != houseEntry.id)
        {
            return;
        }

        residentNpcIds.push_back(npcId);
    };

    for (uint32_t npcId : houseEntry.residentNpcIds)
    {
        appendNpcId(npcId);
    }

    for (uint32_t npcId : npcDialogTable.getNpcIdsForHouse(houseEntry.id, &eventRuntimeState.npcHouseOverrides))
    {
        appendNpcId(npcId);
    }

    return residentNpcIds;
}
}

std::vector<uint32_t> collectSelectableResidentNpcIds(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState)
{
    return collectSelectableResidentNpcIdsImpl(houseEntry, npcDialogTable, eventRuntimeState);
}

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
)
{
    EventDialogContent dialog = {};

    if (!eventRuntimeState.pendingDialogueContext
        || eventRuntimeState.pendingDialogueContext->kind == DialogueContextKind::None)
    {
        return dialog;
    }

    if (eventRuntimeState.pendingDialogueContext->kind == DialogueContextKind::HouseService
        && pHouseTable != nullptr
        && pNpcDialogTable != nullptr)
    {
        const HouseEntry *pHouseEntry = pHouseTable->get(eventRuntimeState.pendingDialogueContext->sourceId);

        if (pHouseEntry != nullptr)
        {
            const std::vector<HouseActionOption> houseActions = buildHouseActionOptions(
                *pHouseEntry,
                pParty,
                pClassSkillTable,
                pWorldRuntime,
                currentGameMinutes,
                currentDialogueMenuId(eventRuntimeState)
            );
            const std::optional<uint32_t> residentNpcId = singleSelectableResidentNpcId(
                *pHouseEntry,
                *pNpcDialogTable,
                eventRuntimeState
            );

            if (residentNpcId && houseActions.empty())
            {
                EventRuntimeState::PendingDialogueContext context = {};
                context.kind = DialogueContextKind::NpcTalk;
                context.sourceId = *residentNpcId;
                context.hostHouseId = pHouseEntry->id;
                eventRuntimeState.pendingDialogueContext = std::move(context);
            }
        }
    }

    const EventRuntimeState::PendingDialogueContext &context = *eventRuntimeState.pendingDialogueContext;
    dialog.isActive = true;
    dialog.isHouseDialog = context.kind == DialogueContextKind::HouseService;
    dialog.sourceId = context.sourceId;

    constexpr size_t MaxLineWidth = 58;
    std::vector<std::string> eventMessageLines;
    const EventRuntimeState::DialogueOfferState *pCurrentOffer =
        eventRuntimeState.dialogueState.currentOffer ? &*eventRuntimeState.dialogueState.currentOffer : nullptr;

    if (previousMessageCount < eventRuntimeState.messages.size())
    {
        for (
            size_t messageIndex = previousMessageCount;
            messageIndex < eventRuntimeState.messages.size();
            ++messageIndex)
        {
            const std::vector<std::string> wrappedLines =
                wrapDialogText(eventRuntimeState.messages[messageIndex], MaxLineWidth);
            eventMessageLines.insert(eventMessageLines.end(), wrappedLines.begin(), wrappedLines.end());
        }
    }

    if (context.kind == DialogueContextKind::MapTransition)
    {
        dialog.participantVisual = EventDialogParticipantVisual::MapIcon;
        dialog.presentation = EventDialogPresentation::Transition;
        dialog.participantPictureId = 0;
        const std::optional<MapEdgeTransition> *pTransition =
            currentMapTransitionForContext(context, pCurrentMap);
        const MapStatsEntry *pDestinationMap =
            (pTransition != nullptr && pTransition->has_value())
                ? findMapEntryByFileName(pMapEntries, (*pTransition)->destinationMapFileName)
                : nullptr;
        dialog.title = pDestinationMap != nullptr
            ? pDestinationMap->name
            : (context.titleOverride.has_value()
                ? *context.titleOverride
                : ((pTransition != nullptr && pTransition->has_value())
                    ? (*pTransition)->destinationMapFileName
                    : "Travel"));

        if (pTransition != nullptr && pTransition->has_value() && (*pTransition)->travelDays > 0)
        {
            const int travelDays = (*pTransition)->travelDays;
            dialog.lines.push_back(
                "It will take "
                + std::to_string(travelDays)
                + " day"
                + (travelDays == 1 ? "" : "s")
                + " to travel to "
                + dialog.title
                + ".");
        }

        if (pCurrentMap != nullptr && !pCurrentMap->name.empty())
        {
            dialog.lines.push_back("Do you wish to leave " + pCurrentMap->name + "?");
        }
        else
        {
            dialog.lines.push_back("Do you wish to leave this area?");
        }

        EventDialogAction confirmAction = {};
        confirmAction.kind = EventDialogActionKind::MapTransitionConfirm;
        confirmAction.label = "OK";
        dialog.actions.push_back(std::move(confirmAction));

        EventDialogAction cancelAction = {};
        cancelAction.kind = EventDialogActionKind::MapTransitionCancel;
        cancelAction.label = "Close";
        dialog.actions.push_back(std::move(cancelAction));
    }
    else if (context.kind == DialogueContextKind::HouseService)
    {
        const HouseEntry *pHouseEntry = pHouseTable != nullptr ? pHouseTable->get(dialog.sourceId) : nullptr;
        dialog.houseTitle = pHouseEntry != nullptr ? pHouseEntry->name : ("House #" + std::to_string(dialog.sourceId));
        dialog.title = dialog.houseTitle;
        dialog.participantPictureId = pHouseEntry != nullptr ? pHouseEntry->proprietorPictureId : 0;
        bool hasResidentActions = false;

        if (pHouseEntry != nullptr)
        {
            const std::vector<HouseActionOption> houseActions = buildHouseActionOptions(
                *pHouseEntry,
                pParty,
                pClassSkillTable,
                pWorldRuntime,
                currentGameMinutes,
                currentDialogueMenuId(eventRuntimeState)
            );

            for (const HouseActionOption &houseAction : houseActions)
            {
                EventDialogAction action = {};
                action.kind = EventDialogActionKind::HouseService;
                action.id = static_cast<uint32_t>(houseAction.id);
                action.label = houseAction.label;
                action.argument = houseAction.argument;
                action.enabled = houseAction.enabled;
                action.disabledReason = houseAction.disabledReason;
                dialog.actions.push_back(std::move(action));
            }

            if (pNpcDialogTable != nullptr)
            {
                const std::vector<uint32_t> residentNpcIds =
                    pNpcDialogTable->getNpcIdsForHouse(pHouseEntry->id, &eventRuntimeState.npcHouseOverrides);
                std::vector<uint32_t> combinedResidentNpcIds = pHouseEntry->residentNpcIds;

                for (uint32_t npcId : residentNpcIds)
                {
                    if (std::find(combinedResidentNpcIds.begin(), combinedResidentNpcIds.end(), npcId)
                        == combinedResidentNpcIds.end())
                    {
                        combinedResidentNpcIds.push_back(npcId);
                    }
                }

                for (uint32_t residentNpcId : combinedResidentNpcIds)
                {
                    const auto overrideIt = eventRuntimeState.npcHouseOverrides.find(residentNpcId);

                    if (overrideIt != eventRuntimeState.npcHouseOverrides.end() && overrideIt->second != pHouseEntry->id)
                    {
                        continue;
                    }

                    const NpcEntry *pResident = pNpcDialogTable->getNpc(residentNpcId);

                    if (pResident != nullptr && !pResident->name.empty())
                    {
                        if (eventRuntimeState.unavailableNpcIds.contains(residentNpcId))
                        {
                            continue;
                        }

                        EventDialogAction action = {};
                        action.kind = EventDialogActionKind::HouseResident;
                        action.id = residentNpcId;
                        action.label = pResident->name;
                        dialog.actions.push_back(std::move(action));
                        hasResidentActions = true;
                    }
                }
            }

            if (!hasResidentActions && resolveHouseServiceType(*pHouseEntry) != HouseServiceType::None)
            {
                dialog.title = buildHouseParticipantTitle(*pHouseEntry);
            }
        }
    }
    else
    {
        dialog.title = "NPC #" + std::to_string(dialog.sourceId);

        const uint32_t overriddenGreetingId =
            eventRuntimeState.npcGreetingOverrides.contains(dialog.sourceId)
                ? eventRuntimeState.npcGreetingOverrides.at(dialog.sourceId)
                : 0;
        const NpcGreetingEntry *pGreeting = pNpcDialogTable != nullptr
            ? (overriddenGreetingId != 0
                ? pNpcDialogTable->getGreeting(overriddenGreetingId)
                : pNpcDialogTable->getGreetingForNpc(dialog.sourceId))
            : nullptr;
        const NpcEntry *pNpc = pNpcDialogTable != nullptr
            ? pNpcDialogTable->getNpc(dialog.sourceId)
            : nullptr;
        const bool hasPendingRosterJoinInvite =
            pCurrentOffer != nullptr
            && pCurrentOffer->kind == DialogueOfferKind::RosterJoin
            && pCurrentOffer->npcId == dialog.sourceId;
        const bool hasPendingMasteryTeacherOffer =
            pCurrentOffer != nullptr
            && pCurrentOffer->kind == DialogueOfferKind::MasteryTeacher
            && pCurrentOffer->npcId == dialog.sourceId;
        const bool hasEventMessageLines = !eventMessageLines.empty();

        if (context.kind == DialogueContextKind::NpcNews && dialog.sourceId == 0)
        {
            dialog.title = "News";
        }
        else if (pNpc != nullptr && !pNpc->name.empty())
        {
            dialog.title = pNpc->name;
        }
        else if (pGreeting != nullptr && !pGreeting->owner.empty())
        {
            dialog.title = pGreeting->owner;
        }

        dialog.participantPictureId = pNpc != nullptr ? pNpc->pictureId : 0;

        if (context.titleOverride && !context.titleOverride->empty())
        {
            dialog.title = *context.titleOverride;
        }

        if (context.kind == DialogueContextKind::NpcTalk
            && allowNpcFallbackContent
            && !hasPendingRosterJoinInvite
            && !hasPendingMasteryTeacherOffer
            && !hasEventMessageLines
            && pGreeting != nullptr)
        {
            const uint32_t greetingDisplayCount = eventRuntimeState.npcGreetingDisplayCounts[dialog.sourceId];
            const std::string &greetingText =
                (greetingDisplayCount == 0 || pGreeting->greetingSecondary.empty())
                ? pGreeting->greetingPrimary
                : pGreeting->greetingSecondary;

            if (!greetingText.empty())
            {
                const std::vector<std::string> wrappedGreeting =
                    wrapDialogText(greetingText, MaxLineWidth);
                dialog.lines.insert(dialog.lines.end(), wrappedGreeting.begin(), wrappedGreeting.end());
                eventRuntimeState.npcGreetingDisplayCounts[dialog.sourceId] = greetingDisplayCount + 1;
            }
        }

        if (context.kind == DialogueContextKind::NpcTalk
            && allowNpcFallbackContent
            && pNpcDialogTable != nullptr)
        {
            const std::optional<ScriptedEventProgram> emptyGlobalProgram = std::nullopt;
            const std::optional<ScriptedEventProgram> &globalProgram =
                pGlobalEventProgram != nullptr ? *pGlobalEventProgram : emptyGlobalProgram;
            const std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>>::const_iterator overrideIt =
                eventRuntimeState.npcTopicOverrides.find(dialog.sourceId);
            const std::unordered_map<uint32_t, uint32_t> *pTopicOverrides =
                overrideIt != eventRuntimeState.npcTopicOverrides.end() ? &overrideIt->second : nullptr;
            const std::vector<NpcDialogTable::ResolvedTopic> topics =
                pNpcDialogTable->getTopicsForNpc(dialog.sourceId, pTopicOverrides);
            const EventRuntime eventRuntime = {};

            if (hasPendingRosterJoinInvite)
            {
                EventDialogAction acceptAction = {};
                acceptAction.kind = EventDialogActionKind::RosterJoinAccept;
                acceptAction.label = "Yes";
                dialog.actions.push_back(std::move(acceptAction));

                EventDialogAction declineAction = {};
                declineAction.kind = EventDialogActionKind::RosterJoinDecline;
                declineAction.label = "No";
                dialog.actions.push_back(std::move(declineAction));
            }
            else if (hasPendingMasteryTeacherOffer && pClassSkillTable != nullptr && pParty != nullptr)
            {
                const std::optional<MasteryTeacherEvaluation> evaluation = evaluateMasteryTeacherTopic(
                    pCurrentOffer->topicId,
                    *pParty,
                    *pClassSkillTable,
                    *pNpcDialogTable
                );

                if (evaluation && !evaluation->displayText.empty())
                {
                    EventDialogAction learnAction = {};
                    learnAction.kind = EventDialogActionKind::MasteryTeacherLearn;
                    learnAction.id = pCurrentOffer->topicId;
                    learnAction.label = evaluation->displayText;
                    dialog.actions.push_back(std::move(learnAction));
                }
            }
            else
            {
                for (const NpcDialogTable::ResolvedTopic &topic : topics)
                {
                    if (topic.topic.empty())
                    {
                        continue;
                    }

                    const ISceneEventContext *pSceneEventContext =
                        dynamic_cast<const ISceneEventContext *>(pWorldRuntime);

                    if (!eventRuntime.canShowTopic(
                            globalProgram,
                            static_cast<uint16_t>(topic.id),
                            eventRuntimeState,
                            pParty,
                            pSceneEventContext))
                    {
                        continue;
                    }

                    EventDialogAction action = {};
                    action.kind = EventDialogActionKind::NpcTopic;
                    action.secondaryId = topic.id;
                    action.textOnly = topic.specialKind == NpcTopicEntry::SpecialKind::TextOnly;

                    if (topic.specialKind == NpcTopicEntry::SpecialKind::RosterJoinOffer)
                    {
                        action.kind = EventDialogActionKind::RosterJoinOffer;
                    }
                    else if (topic.specialKind == NpcTopicEntry::SpecialKind::MasteryTeacherOffer)
                    {
                        action.kind = EventDialogActionKind::MasteryTeacherOffer;
                    }

                    action.id = topic.id;
                    action.label = topic.topic;
                    dialog.actions.push_back(std::move(action));
                }
            }
        }

        if (context.kind == DialogueContextKind::NpcNews
            && eventMessageLines.empty()
            && pNpcDialogTable != nullptr
            && context.newsId != 0)
        {
            const std::optional<std::string> newsText = pNpcDialogTable->getNewsText(context.newsId);

            if (newsText && !newsText->empty())
            {
                const std::vector<std::string> wrappedNews = wrapDialogText(*newsText, MaxLineWidth);
                dialog.lines.insert(dialog.lines.end(), wrappedNews.begin(), wrappedNews.end());
            }
        }
    }

    if (context.kind == DialogueContextKind::NpcTalk
        && pCurrentOffer != nullptr
        && pCurrentOffer->kind == DialogueOfferKind::MasteryTeacher
        && pCurrentOffer->npcId == dialog.sourceId
        && eventMessageLines.empty()
        && pNpcDialogTable != nullptr)
    {
        const std::optional<NpcDialogTable::ResolvedTopic> topic =
            pNpcDialogTable->getTopicById(pCurrentOffer->topicId);

        if (topic && !topic->text.empty())
        {
            eventMessageLines = wrapDialogText(topic->text, MaxLineWidth);
        }
    }

    if (context.kind == DialogueContextKind::NpcTalk
        && pCurrentOffer != nullptr
        && pCurrentOffer->kind == DialogueOfferKind::RosterJoin
        && pCurrentOffer->npcId == dialog.sourceId
        && eventMessageLines.empty()
        && pNpcDialogTable != nullptr)
    {
        const std::optional<std::string> inviteText =
            pNpcDialogTable->getText(pCurrentOffer->messageTextId);

        if (inviteText && !inviteText->empty())
        {
            eventMessageLines = wrapDialogText(*inviteText, MaxLineWidth);
        }
    }

    if (context.kind == DialogueContextKind::MapTransition)
    {
    }
    else if (context.kind == DialogueContextKind::HouseService)
    {
        dialog.lines.clear();

        if (!eventMessageLines.empty())
        {
            dialog.lines.insert(dialog.lines.end(), eventMessageLines.begin(), eventMessageLines.end());
        }
        else if (!dialog.actions.empty())
        {
            const HouseEntry *pHouseEntry = pHouseTable != nullptr ? pHouseTable->get(dialog.sourceId) : nullptr;

            if (pHouseEntry != nullptr)
            {
                const DialogueMenuId menuId = currentDialogueMenuId(eventRuntimeState);
                dialog.lines = buildHouseServiceInfoLines(*pHouseEntry, pParty, pClassSkillTable, menuId);
            }
        }
        else
        {
            dialog.lines.push_back("The house is empty.");
        }
    }
    else
    {
        if (dialog.isHouseDialog && eventMessageLines.empty() && !dialog.actions.empty())
        {
            dialog.lines.clear();
        }

        dialog.lines.insert(dialog.lines.end(), eventMessageLines.begin(), eventMessageLines.end());
    }

    if (!dialog.isHouseDialog
        && context.kind != DialogueContextKind::MapTransition
        && context.kind != DialogueContextKind::NpcNews
        && !allowNpcFallbackContent
        && eventMessageLines.empty())
    {
        return {};
    }

    if (dialog.lines.empty() && dialog.actions.empty())
    {
        if (dialog.isHouseDialog)
        {
            dialog.lines.push_back("The house is empty.");
        }
        else
        {
            dialog.lines.push_back("NPC interaction UI is not implemented yet.");
        }
    }

    return dialog;
}
}
