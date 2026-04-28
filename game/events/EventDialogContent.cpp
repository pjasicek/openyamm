#include "game/events/EventDialogContent.h"

#include "game/events/ISceneEventContext.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *TransitionVideoDirectory = "Videos/Transitions";

const char *transitionImageName(uint32_t imageId)
{
    static constexpr std::array<const char *, 11> ImageNames = {{
        "",
        "Ticon01",
        "Ticon02",
        "Ticon03",
        "Ticon04",
        "Ticon05",
        "ISTAIRUP",
        "ITRAP",
        "Outside",
        "IDOOR",
        "ISECDOOR"
    }};

    return imageId < ImageNames.size() ? ImageNames[imageId] : "";
}

const char *defaultDungeonTransitionImageName()
{
    // TODO: Replace this with data-accurate Ticon01..Ticon05 selection per dungeon transition.
    return "Ticon01";
}

const char *defaultOutdoorTransitionImageName()
{
    return "Outside";
}

std::string lowerMapFileName(const std::string &fileName)
{
    return toLowerCopy(fileName);
}

std::string lowerTransitionTitle(const std::string &title)
{
    std::string normalized = toLowerCopy(title);
    normalized.erase(
        std::remove(normalized.begin(), normalized.end(), '"'),
        normalized.end());

    return normalized;
}

std::string transitionVideoNameForTransitionTitle(const std::string &title)
{
    const std::string normalized = lowerTransitionTitle(title);

    static constexpr std::pair<const char *, const char *> TitleVideos[] = {
        {"abandoned temple", "ab_temp"},
        {"pirate outpost", "p_outpst"},
        {"smuggler's cove", "smg_cove"},
        {"dire wolf lair", "dire_lr"},
        {"dire wolf den", "dire_lr"},
        {"merchanthouse of alvar", "mrch_hs"},
        {"merchant house of alvar", "mrch_hs"},
        {"inside the crystal", "in_cryst"},
        {"escaton's crystal", "in_cryst"},
        {"wasp nest", "wasp_nst"},
        {"ogre raiding fort", "ogre_ft"},
        {"ogre fortress", "ogre_ft"},
        {"troll tomb", "trol_tmb"},
        {"ancient troll home", "trol_tmb"},
        {"cyclops larder", "cyc_lr"},
        {"chain of fire", "ch_fire"},
        {"dragon hunter camp", "dh_camp"},
        {"dragon hunter's camp", "dh_camp"},
        {"dragon cave", "drgn_cav"},
        {"ilsingore's cave", "drgn_cav"},
        {"yaardrake's cave", "drgn_cav"},
        {"old loeb's cave", "drgn_cav"},
        {"naga vault", "naga_vlt"},
        {"temple of the sun", "tpl_sun"},
        {"abandoned druid circle", "ab_druid"},
        {"druid circle", "ab_druid"},
        {"minotaur lair", "mino_lr"},
        {"balthazar lair", "mino_lr"},
        {"barbarian fortress", "barb_frt"},
        {"pirate stronghold", "p_strong"},
        {"abandoned pirate keep", "a_p_keep"},
        {"small sub pen", "s_subpen"},
        {"hand-cranked submarine", "s_subpen"},
        {"passage under regna", "rsub"},
        {"necromancers' guild", "nec_gild"},
        {"mad necromancer's lab", "mad_lab"},
        {"castle of air", "cstl_air"},
        {"castle of fire", "cstl_fir"},
        {"war camp", "war_camp"},
        {"eschaton's palace", "esch_pal"},
        {"prison of the lord of air", "pr_elords"},
        {"prison of the lord of earth", "pr_lorde"},
        {"prison of the lord of fire", "pr_lordf"},
        {"prison of the lord of water", "pr_lordw"},
        {"gateway to the plane of air", "gw_air"},
        {"gateway to the plane of earth", "gw_earth"},
        {"gateway to the plane of fire", "gw_fire"},
        {"gateway to the plane of water", "gw_water"}
    };

    for (const std::pair<const char *, const char *> &entry : TitleVideos)
    {
        if (normalized == entry.first)
        {
            return entry.second;
        }
    }

    return {};
}

std::string transitionVideoNameForMap(const std::string &mapFileName)
{
    const std::string normalized = lowerMapFileName(mapFileName);

    static constexpr std::pair<const char *, const char *> MapVideos[] = {
        {"d05.blv", "ab_temp"},
        {"d06.blv", "p_outpst"},
        {"d07.blv", "smg_cove"},
        {"d08.blv", "dire_lr"},
        {"d09.blv", "mrch_hs"},
        {"d10.blv", "in_cryst"},
        {"d11.blv", "wasp_nst"},
        {"d12.blv", "ogre_ft"},
        {"d13.blv", "trol_tmb"},
        {"d14.blv", "cyc_lr"},
        {"d15.blv", "ch_fire"},
        {"d16.blv", "dh_camp"},
        {"d17.blv", "drgn_cav"},
        {"d18.blv", "naga_vlt"},
        {"d19.blv", "nec_gild"},
        {"d20.blv", "mad_lab"},
        {"d22.blv", "tpl_sun"},
        {"d23.blv", "ab_druid"},
        {"d24.blv", "mino_lr"},
        {"d25.blv", "barb_frt"},
        {"d27.blv", "cstl_air"},
        {"d29.blv", "cstl_fir"},
        {"d30.blv", "war_camp"},
        {"d31.blv", "p_strong"},
        {"d32.blv", "a_p_keep"},
        {"d33.blv", "rsub"},
        {"d34.blv", "s_subpen"},
        {"d35.blv", "esch_pal"},
        {"d36.blv", "pr_elords"},
        {"d37.blv", "pr_lordf"},
        {"d38.blv", "pr_lordw"},
        {"d39.blv", "pr_lorde"},
        {"d43.blv", "trol_tmb"},
        {"d47.blv", "drgn_cav"},
        {"d48.blv", "drgn_cav"},
        {"d49.blv", "drgn_cav"},
        {"elema.odm", "gw_air"},
        {"eleme.odm", "gw_earth"},
        {"elemf.odm", "gw_fire"},
        {"elemw.odm", "gw_water"}
    };

    for (const std::pair<const char *, const char *> &entry : MapVideos)
    {
        if (normalized == entry.first)
        {
            return entry.second;
        }
    }

    return {};
}

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
    const TransitionTable *pTransitionTable,
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
        const std::optional<MapEdgeTransition> *pTransition = context.transitionMapMove.has_value()
            ? nullptr
            : currentMapTransitionForContext(context, pCurrentMap);
        const std::string transitionMapName =
            context.transitionMapMove.has_value() && context.transitionMapMove->mapName.has_value()
                ? *context.transitionMapMove->mapName
                : ((pTransition != nullptr && pTransition->has_value())
                    ? (*pTransition)->destinationMapFileName
                    : std::string());
        const std::string currentMapName = pCurrentMap != nullptr ? pCurrentMap->fileName : std::string();
        const bool destinationIsDungeon =
            !transitionMapName.empty() && lowerMapFileName(transitionMapName).find(".blv") != std::string::npos;
        const bool currentMapIsDungeon =
            !currentMapName.empty() && lowerMapFileName(currentMapName).find(".blv") != std::string::npos;
        const bool isDungeonTransition = destinationIsDungeon || currentMapIsDungeon;
        dialog.participantTextureName =
            context.transitionImageId != 0
                ? transitionImageName(context.transitionImageId)
                : (isDungeonTransition
                    ? defaultDungeonTransitionImageName()
                    : defaultOutdoorTransitionImageName());
        const MapStatsEntry *pDestinationMap =
            !transitionMapName.empty()
                ? findMapEntryByFileName(pMapEntries, transitionMapName)
                : nullptr;
        const bool leavingCurrentDungeon = currentMapIsDungeon && !destinationIsDungeon;
        const TransitionEntry *pTransitionText =
            pTransitionTable != nullptr && context.transitionTextId != 0
                ? pTransitionTable->get(context.transitionTextId)
                : nullptr;

        if (leavingCurrentDungeon && pCurrentMap != nullptr && !pCurrentMap->name.empty())
        {
            dialog.title = pCurrentMap->name;
        }
        else if (pDestinationMap != nullptr)
        {
            dialog.title = pDestinationMap->name;
        }
        else if (context.titleOverride.has_value())
        {
            dialog.title = *context.titleOverride;
        }
        else if (pTransitionText != nullptr && !pTransitionText->title.empty())
        {
            dialog.title = pTransitionText->title;
        }
        else
        {
            dialog.title = !transitionMapName.empty() ? transitionMapName : "Travel";
        }

        dialog.videoName = pTransitionText != nullptr && !pTransitionText->title.empty()
            ? transitionVideoNameForTransitionTitle(pTransitionText->title)
            : std::string();
        if (dialog.videoName.empty() && !dialog.title.empty())
        {
            dialog.videoName = transitionVideoNameForTransitionTitle(dialog.title);
        }
        if (dialog.videoName.empty())
        {
            dialog.videoName = transitionVideoNameForMap(transitionMapName);
        }
        dialog.videoDirectory = !dialog.videoName.empty() ? TransitionVideoDirectory : std::string();

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

        if (pTransitionText != nullptr && !pTransitionText->description.empty())
        {
            dialog.lines.push_back(pTransitionText->description);
        }
        else if (leavingCurrentDungeon)
        {
            dialog.lines.push_back("Do you wish to leave " + dialog.title + "?");
        }
        else if (context.transitionMapMove.has_value())
        {
            dialog.lines.push_back("Do you wish to enter " + dialog.title + "?");
        }
        else if (pCurrentMap != nullptr && !pCurrentMap->name.empty())
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
        if (!dialog.isHouseDialog)
        {
            dialog.lines.push_back("NPC interaction UI is not implemented yet.");
        }
    }

    return dialog;
}
}
