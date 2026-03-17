#include "game/EventDialogContent.h"

#include "game/HouseInteraction.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
std::vector<std::string> wrapDialogText(const std::string &text, size_t width)
{
    if (text.empty() || width == 0)
    {
        return {};
    }

    std::vector<std::string> lines;
    size_t lineStart = 0;

    while (lineStart < text.size())
    {
        if (lineStart + width >= text.size())
        {
            lines.push_back(text.substr(lineStart));
            break;
        }

        size_t breakPosition = text.rfind(' ', lineStart + width);

        if (breakPosition == std::string::npos || breakPosition < lineStart)
        {
            breakPosition = lineStart + width;
        }

        lines.push_back(text.substr(lineStart, breakPosition - lineStart));
        lineStart = breakPosition;

        while (lineStart < text.size() && text[lineStart] == ' ')
        {
            ++lineStart;
        }
    }

    if (lines.empty())
    {
        lines.push_back(text);
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

std::optional<uint32_t> singleSelectableResidentNpcId(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState
)
{
    std::optional<uint32_t> residentNpcId;

    for (uint32_t candidateNpcId : houseEntry.residentNpcIds)
    {
        const NpcEntry *pResident = npcDialogTable.getNpc(candidateNpcId);

        if (pResident == nullptr || pResident->name.empty())
        {
            continue;
        }

        if (eventRuntimeState.unavailableNpcIds.contains(candidateNpcId))
        {
            continue;
        }

        if (residentNpcId)
        {
            return std::nullopt;
        }

        residentNpcId = candidateNpcId;
    }

    return residentNpcId;
}
}

EventDialogContent buildEventDialogContent(
    EventRuntimeState &eventRuntimeState,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const std::optional<EventIrProgram> *pGlobalEventIrProgram,
    const HouseTable *pHouseTable,
    const NpcDialogTable *pNpcDialogTable,
    const Party *pParty,
    int currentHour
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
                currentHour
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

    if (context.kind == DialogueContextKind::HouseService)
    {
        const HouseEntry *pHouseEntry = pHouseTable != nullptr ? pHouseTable->get(dialog.sourceId) : nullptr;
        dialog.title = pHouseEntry != nullptr ? pHouseEntry->name : ("House #" + std::to_string(dialog.sourceId));

        if (pHouseEntry != nullptr)
        {
            if (!pHouseEntry->type.empty() && shouldDisplayHouseType(pHouseEntry->type))
            {
                dialog.lines.push_back(pHouseEntry->type);
            }

            if (pNpcDialogTable != nullptr && !pHouseEntry->residentNpcIds.empty())
            {
                bool hasResidentAction = false;

                for (uint32_t residentNpcId : pHouseEntry->residentNpcIds)
                {
                    const NpcEntry *pResident = pNpcDialogTable->getNpc(residentNpcId);

                    if (pResident != nullptr && !pResident->name.empty())
                    {
                        if (eventRuntimeState.unavailableNpcIds.contains(residentNpcId))
                        {
                            continue;
                        }

                        if (!hasResidentAction)
                        {
                            dialog.lines.push_back("Residents:");
                            hasResidentAction = true;
                        }

                        EventDialogAction action = {};
                        action.kind = EventDialogActionKind::HouseResident;
                        action.id = residentNpcId;
                        action.label = pResident->name;
                        dialog.actions.push_back(std::move(action));
                    }
                }
            }

            const bool hasRealProprietorName =
                !pHouseEntry->proprietorName.empty() && pHouseEntry->proprietorName != "Placeholder";
            const bool hasRealProprietorTitle =
                !pHouseEntry->proprietorTitle.empty() && pHouseEntry->proprietorTitle != "Placeholder";

            if (hasRealProprietorName || hasRealProprietorTitle)
            {
                std::string proprietorLine;

                if (hasRealProprietorName)
                {
                    proprietorLine = pHouseEntry->proprietorName;
                }

                if (hasRealProprietorTitle)
                {
                    if (!proprietorLine.empty())
                    {
                        proprietorLine += " - ";
                    }

                    proprietorLine += pHouseEntry->proprietorTitle;
                }

                dialog.lines.push_back(proprietorLine);
            }

            if (pHouseEntry->openHour > 0 || pHouseEntry->closeHour > 0)
            {
                dialog.lines.push_back(
                    "Hours: "
                    + std::to_string(pHouseEntry->openHour)
                    + ":00 - "
                    + std::to_string(pHouseEntry->closeHour)
                    + ":00"
                );
            }

            if (!pHouseEntry->enterText.empty()
                && pHouseEntry->enterText != "0"
                && pHouseEntry->enterText != "Placeholder")
            {
                const std::vector<std::string> wrappedEnterText = wrapDialogText(pHouseEntry->enterText, MaxLineWidth);
                dialog.lines.insert(dialog.lines.end(), wrappedEnterText.begin(), wrappedEnterText.end());
            }

            const std::vector<HouseActionOption> houseActions = buildHouseActionOptions(
                *pHouseEntry,
                pParty,
                currentHour
            );

            for (const HouseActionOption &houseAction : houseActions)
            {
                EventDialogAction action = {};
                action.kind = EventDialogActionKind::HouseService;
                action.id = static_cast<uint32_t>(houseAction.id);
                action.label = houseAction.label;
                action.enabled = houseAction.enabled;
                action.disabledReason = houseAction.disabledReason;
                dialog.actions.push_back(std::move(action));
            }
        }
    }
    else
    {
        dialog.title = "NPC #" + std::to_string(dialog.sourceId);

        const NpcGreetingEntry *pGreeting = pNpcDialogTable != nullptr
            ? pNpcDialogTable->getGreetingForNpc(dialog.sourceId)
            : nullptr;
        const NpcEntry *pNpc = pNpcDialogTable != nullptr
            ? pNpcDialogTable->getNpc(dialog.sourceId)
            : nullptr;
        const bool hasPendingRosterJoinInvite =
            eventRuntimeState.pendingRosterJoinInvite
            && eventRuntimeState.pendingRosterJoinInvite->npcId == dialog.sourceId;
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

        if (context.titleOverride && !context.titleOverride->empty())
        {
            dialog.title = *context.titleOverride;
        }

        if (context.kind == DialogueContextKind::NpcTalk
            && allowNpcFallbackContent
            && !hasPendingRosterJoinInvite
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
            const std::optional<EventIrProgram> emptyGlobalProgram = std::nullopt;
            const std::optional<EventIrProgram> &globalProgram =
                pGlobalEventIrProgram != nullptr ? *pGlobalEventIrProgram : emptyGlobalProgram;
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
            else
            {
                for (const NpcDialogTable::ResolvedTopic &topic : topics)
                {
                    if (topic.topic.empty())
                    {
                        continue;
                    }

                    if (!eventRuntime.canShowTopic(
                            globalProgram,
                            static_cast<uint16_t>(topic.id),
                            eventRuntimeState,
                            pParty))
                    {
                        continue;
                    }

                    EventDialogAction action = {};
                    action.kind = topic.specialKind == NpcTopicEntry::SpecialKind::RosterJoinOffer
                        ? EventDialogActionKind::RosterJoinOffer
                        : EventDialogActionKind::NpcTopic;
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
        && eventRuntimeState.pendingRosterJoinInvite
        && eventRuntimeState.pendingRosterJoinInvite->npcId == dialog.sourceId
        && eventMessageLines.empty()
        && pNpcDialogTable != nullptr)
    {
        const std::optional<std::string> inviteText =
            pNpcDialogTable->getText(eventRuntimeState.pendingRosterJoinInvite->inviteTextId);

        if (inviteText && !inviteText->empty())
        {
            eventMessageLines = wrapDialogText(*inviteText, MaxLineWidth);
        }
    }

    dialog.lines.insert(dialog.lines.end(), eventMessageLines.begin(), eventMessageLines.end());

    if (!dialog.isHouseDialog
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
