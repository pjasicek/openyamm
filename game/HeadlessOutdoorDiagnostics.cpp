#include "game/ActorNameResolver.h"
#include "game/HeadlessOutdoorDiagnostics.h"

#include "engine/AssetFileSystem.h"
#include "game/EventDialogContent.h"
#include "game/EventRuntime.h"
#include "game/GameDataLoader.h"
#include "game/GenericActorDialog.h"
#include "game/HouseInteraction.h"
#include "game/MasteryTeacherDialog.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/Party.h"

#include <algorithm>
#include <iostream>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t AdventurersInnHouseId = 185;

std::optional<uint32_t> singleSelectableResidentNpcId(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState
)
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

    std::optional<uint32_t> residentNpcId;

    for (uint32_t candidateNpcId : residentNpcIds)
    {
        if (residentNpcId)
        {
            return std::nullopt;
        }

        residentNpcId = candidateNpcId;
    }

    return residentNpcId;
}

void printChestSummary(const OutdoorWorldRuntime::ChestViewState &chestView, const ItemTable &itemTable)
{
    std::cout << "Headless diagnostic: active chest #" << chestView.chestId
              << " type=" << chestView.chestTypeId
              << " flags=0x" << std::hex << chestView.flags << std::dec
              << " entries=" << chestView.items.size()
              << '\n';

    for (size_t itemIndex = 0; itemIndex < chestView.items.size(); ++itemIndex)
    {
        const OutdoorWorldRuntime::ChestItemState &item = chestView.items[itemIndex];
        std::cout << "  [" << itemIndex << "] ";

        if (item.isGold)
        {
            std::cout << "gold=" << item.goldAmount;

            if (item.goldRollCount > 1)
            {
                std::cout << " rolls=" << item.goldRollCount;
            }
        }
        else
        {
            const ItemDefinition *pItemDefinition = itemTable.get(item.itemId);
            std::cout << "item=" << item.itemId;

            if (pItemDefinition != nullptr && !pItemDefinition->name.empty())
            {
                std::cout << " \"" << pItemDefinition->name << "\"";
            }

            std::cout << " quantity=" << item.quantity;
        }

        std::cout << '\n';
    }
}

void printDialogSummary(const EventDialogContent &dialog)
{
    if (!dialog.isActive)
    {
        std::cout << "Headless diagnostic: no active dialog\n";
        return;
    }

    std::cout << "Headless diagnostic: dialog title=\"" << dialog.title << "\"\n";

    for (size_t lineIndex = 0; lineIndex < dialog.lines.size(); ++lineIndex)
    {
        std::cout << "  dialog[" << lineIndex << "] " << dialog.lines[lineIndex] << '\n';
    }

    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        const EventDialogAction &action = dialog.actions[actionIndex];
        std::cout << "  action[" << actionIndex << "] " << action.label
                  << " kind=" << static_cast<int>(action.kind)
                  << " id=" << action.id
                  << " enabled=" << (action.enabled ? "1" : "0");

        if (!action.disabledReason.empty())
        {
            std::cout << " reason=\"" << action.disabledReason << "\"";
        }

        std::cout << '\n';
    }
}

void promoteSingleResidentHouseContext(
    EventRuntimeState &eventRuntimeState,
    const HouseTable &houseTable,
    const NpcDialogTable &npcDialogTable,
    int currentHour
)
{
    if (!eventRuntimeState.pendingDialogueContext
        || eventRuntimeState.pendingDialogueContext->kind != DialogueContextKind::HouseService)
    {
        return;
    }

    const HouseEntry *pHouseEntry = houseTable.get(eventRuntimeState.pendingDialogueContext->sourceId);

    if (pHouseEntry == nullptr)
    {
        return;
    }

    const std::vector<HouseActionOption> houseActions = buildHouseActionOptions(*pHouseEntry, nullptr, currentHour);
    const std::optional<uint32_t> residentNpcId = singleSelectableResidentNpcId(
        *pHouseEntry,
        npcDialogTable,
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

EventDialogContent buildHeadlessDialog(
    EventRuntimeState &eventRuntimeState,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const std::optional<EventIrProgram> &globalEventIrProgram,
    const GameDataLoader &gameDataLoader,
    Party *pParty,
    int currentHour
)
{
    promoteSingleResidentHouseContext(
        eventRuntimeState,
        gameDataLoader.getHouseTable(),
        gameDataLoader.getNpcDialogTable(),
        currentHour
    );

    return buildEventDialogContent(
        eventRuntimeState,
        previousMessageCount,
        allowNpcFallbackContent,
        &globalEventIrProgram,
        &gameDataLoader.getHouseTable(),
        &gameDataLoader.getClassSkillTable(),
        &gameDataLoader.getNpcDialogTable(),
        pParty,
        currentHour
    );
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    std::transform(
        result.begin(),
        result.end(),
        result.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        }
    );

    return result;
}

std::optional<size_t> findActionIndexByLabel(const EventDialogContent &dialog, const std::string &label)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label == label)
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

bool dialogContainsText(const EventDialogContent &dialog, const std::string &fragment)
{
    for (const std::string &line : dialog.lines)
    {
        if (line.find(fragment) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

bool dialogHasActionLabel(const EventDialogContent &dialog, const std::string &label)
{
    return findActionIndexByLabel(dialog, label).has_value();
}

CharacterSkill *ensureCharacterSkill(
    Character &character,
    const std::string &skillName,
    uint32_t level,
    SkillMastery mastery
)
{
    CharacterSkill *pSkill = character.findSkill(skillName);

    if (pSkill == nullptr)
    {
        CharacterSkill skill = {};
        skill.name = canonicalSkillName(skillName);
        skill.level = level;
        skill.mastery = mastery;
        character.skills[skill.name] = skill;
        pSkill = character.findSkill(skillName);
    }

    if (pSkill != nullptr)
    {
        pSkill->level = level;
        pSkill->mastery = mastery;
    }

    return pSkill;
}

struct RegressionScenario
{
    OutdoorWorldRuntime world;
    Party party;
    EventRuntime eventRuntime;
    EventRuntimeState *pEventRuntimeState = nullptr;
};

EventDialogContent buildScenarioDialog(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t previousMessageCount,
    bool allowNpcFallbackContent
);

bool executeDialogActionInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t actionIndex,
    EventDialogContent &dialog
);

bool initializeRegressionScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario
)
{
    scenario.world.initialize(
        selectedMap.map,
        gameDataLoader.getItemTable(),
        selectedMap.outdoorMapDeltaData,
        selectedMap.eventRuntimeState
    );

    scenario.party = {};
    scenario.party.setItemTable(&gameDataLoader.getItemTable());
    scenario.party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    scenario.party.reset();
    scenario.pEventRuntimeState = scenario.world.eventRuntimeState();
    return scenario.pEventRuntimeState != nullptr;
}

EventDialogContent openNpcDialogInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint32_t npcId
)
{
    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::NpcTalk;
    context.sourceId = npcId;
    scenario.pEventRuntimeState->pendingDialogueContext = context;
    return buildScenarioDialog(gameDataLoader, selectedMap, scenario, 0, true);
}

bool openMasteryTeacherOfferInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint32_t npcId,
    const std::string &topicLabel,
    EventDialogContent &dialog
)
{
    dialog = openNpcDialogInScenario(gameDataLoader, selectedMap, scenario, npcId);
    const std::optional<size_t> offerIndex = findActionIndexByLabel(dialog, topicLabel);

    if (!offerIndex)
    {
        return false;
    }

    return executeDialogActionInScenario(gameDataLoader, selectedMap, scenario, *offerIndex, dialog);
}

bool executeLocalEventInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint16_t eventId
)
{
    if (scenario.pEventRuntimeState == nullptr)
    {
        return false;
    }

    const bool executed = scenario.eventRuntime.executeEventById(
        selectedMap.localEventIrProgram,
        selectedMap.globalEventIrProgram,
        eventId,
        *scenario.pEventRuntimeState,
        &scenario.party
    );

    if (!executed)
    {
        return false;
    }

    scenario.world.applyEventRuntimeState();
    scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);
    return true;
}

bool openActorInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t actorIndex
)
{
    if (scenario.pEventRuntimeState == nullptr || !selectedMap.outdoorMapDeltaData)
    {
        return false;
    }

    if (actorIndex >= selectedMap.outdoorMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = selectedMap.outdoorMapDeltaData->actors[actorIndex];
    const std::string actorName = resolveMapDeltaActorName(gameDataLoader.getMonsterTable(), actor);

    if (actor.npcId > 0)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = static_cast<uint32_t>(actor.npcId);
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        return true;
    }

    const std::optional<GenericActorDialogResolution> resolution = resolveGenericActorDialog(
        selectedMap.map.fileName,
        actorName,
        actor.group,
        *scenario.pEventRuntimeState,
        gameDataLoader.getNpcDialogTable()
    );

    if (!resolution)
    {
        return false;
    }

    const std::optional<std::string> newsText = gameDataLoader.getNpcDialogTable().getNewsText(resolution->newsId);

    if (!newsText)
    {
        return false;
    }

    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::NpcNews;
    context.sourceId = resolution->npcId;
    context.newsId = resolution->newsId;
    context.titleOverride = actorName;
    scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    scenario.pEventRuntimeState->messages.push_back(*newsText);
    return true;
}

EventDialogContent buildScenarioDialog(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t previousMessageCount,
    bool allowNpcFallbackContent
)
{
    return buildHeadlessDialog(
        *scenario.pEventRuntimeState,
        previousMessageCount,
        allowNpcFallbackContent,
        selectedMap.globalEventIrProgram,
        gameDataLoader,
        &scenario.party,
        scenario.world.currentHour()
    );
}

bool executeDialogActionInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t actionIndex,
    EventDialogContent &dialog
)
{
    if (scenario.pEventRuntimeState == nullptr || !dialog.isActive || actionIndex >= dialog.actions.size())
    {
        return false;
    }

    const EventDialogAction &action = dialog.actions[actionIndex];
    const size_t previousMessageCount = scenario.pEventRuntimeState->messages.size();

    if (action.kind == EventDialogActionKind::HouseResident)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = action.id;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::RosterJoinOffer)
    {
        const std::optional<NpcDialogTable::RosterJoinOffer> offer =
            gameDataLoader.getNpcDialogTable().getRosterJoinOfferForTopic(action.id);

        if (!offer)
        {
            return false;
        }

        const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(offer->inviteTextId);

        if (inviteText && !inviteText->empty())
        {
            scenario.pEventRuntimeState->messages.push_back(*inviteText);
        }

        EventRuntimeState::PendingRosterJoinInvite invite = {};
        invite.npcId = dialog.sourceId;
        invite.rosterId = offer->rosterId;
        invite.inviteTextId = offer->inviteTextId;
        invite.partyFullTextId = offer->partyFullTextId;
        scenario.pEventRuntimeState->pendingRosterJoinInvite = std::move(invite);

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = dialog.sourceId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::RosterJoinAccept)
    {
        if (!scenario.pEventRuntimeState->pendingRosterJoinInvite)
        {
            return false;
        }

        const EventRuntimeState::PendingRosterJoinInvite invite = *scenario.pEventRuntimeState->pendingRosterJoinInvite;
        scenario.pEventRuntimeState->pendingRosterJoinInvite.reset();

        if (scenario.party.isFull())
        {
            scenario.pEventRuntimeState->npcHouseOverrides[invite.npcId] = AdventurersInnHouseId;
            const std::optional<std::string> fullPartyText =
                gameDataLoader.getNpcDialogTable().getText(invite.partyFullTextId);

            if (fullPartyText && !fullPartyText->empty())
            {
                scenario.pEventRuntimeState->messages.push_back(*fullPartyText);
            }
        }
        else
        {
            const RosterEntry *pRosterEntry = gameDataLoader.getRosterTable().get(invite.rosterId);

            if (pRosterEntry == nullptr || !scenario.party.recruitRosterMember(*pRosterEntry))
            {
                return false;
            }

            scenario.pEventRuntimeState->unavailableNpcIds.insert(invite.npcId);
            scenario.pEventRuntimeState->npcHouseOverrides.erase(invite.npcId);
            scenario.pEventRuntimeState->messages.push_back(pRosterEntry->name + " joined the party.");
        }

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = invite.npcId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::RosterJoinDecline)
    {
        const uint32_t npcId = scenario.pEventRuntimeState->pendingRosterJoinInvite
            ? scenario.pEventRuntimeState->pendingRosterJoinInvite->npcId
            : dialog.sourceId;
        scenario.pEventRuntimeState->pendingRosterJoinInvite.reset();

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = npcId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::MasteryTeacherOffer)
    {
        EventRuntimeState::PendingMasteryTeacherOffer offer = {};
        offer.npcId = dialog.sourceId;
        offer.topicId = action.id;
        scenario.pEventRuntimeState->pendingMasteryTeacherOffer = std::move(offer);

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = dialog.sourceId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::MasteryTeacherLearn)
    {
        if (!scenario.pEventRuntimeState->pendingMasteryTeacherOffer)
        {
            return false;
        }

        std::string message;

        if (applyMasteryTeacherTopic(
                scenario.pEventRuntimeState->pendingMasteryTeacherOffer->topicId,
                scenario.party,
                gameDataLoader.getClassSkillTable(),
                gameDataLoader.getNpcDialogTable(),
                message))
        {
            if (!message.empty())
            {
                scenario.pEventRuntimeState->messages.push_back(message);
            }

            scenario.pEventRuntimeState->pendingMasteryTeacherOffer.reset();
        }
    }
    else if (action.kind == EventDialogActionKind::NpcTopic)
    {
        const bool executed = scenario.eventRuntime.executeEventById(
            std::nullopt,
            selectedMap.globalEventIrProgram,
            static_cast<uint16_t>(action.id),
            *scenario.pEventRuntimeState,
            &scenario.party
        );

        if (!executed)
        {
            return false;
        }

        scenario.world.applyEventRuntimeState();
        scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);

        if (!scenario.pEventRuntimeState->pendingDialogueContext)
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = dialog.sourceId;
            scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
    }
    else
    {
        return false;
    }

    dialog = buildScenarioDialog(
        gameDataLoader,
        selectedMap,
        scenario,
        previousMessageCount,
        action.kind != EventDialogActionKind::RosterJoinAccept
            && action.kind != EventDialogActionKind::MasteryTeacherLearn
    );
    return true;
}
}

HeadlessOutdoorDiagnostics::HeadlessOutdoorDiagnostics(const Engine::ApplicationConfig &config)
    : m_config(config)
{
}

int HeadlessOutdoorDiagnostics::runOpenEvent(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    uint16_t eventId
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getItemTable(),
        selectedMap->outdoorMapDeltaData,
        selectedMap->eventRuntimeState
    );

    Party party = {};
    party.setItemTable(&gameDataLoader.getItemTable());
    party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    party.reset();

    EventRuntime eventRuntime;
    EventRuntimeState *pEventRuntimeState = outdoorWorldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        std::cerr << "Headless diagnostic failed: event runtime state is not available\n";
        return 1;
    }

    std::cout << "Headless diagnostic: map=" << selectedMap->map.fileName
              << " id=" << selectedMap->map.id
              << " event=" << eventId
              << '\n';

    const bool executed = eventRuntime.executeEventById(
        selectedMap->localEventIrProgram,
        selectedMap->globalEventIrProgram,
        eventId,
        *pEventRuntimeState,
        &party
    );

    if (!executed)
    {
        std::cout << "Headless diagnostic: event " << eventId << " unresolved\n";
        return 2;
    }

    outdoorWorldRuntime.applyEventRuntimeState();
    party.applyEventRuntimeState(*pEventRuntimeState);

    if (const EventRuntimeState::PendingMapMove *pPendingMapMove = outdoorWorldRuntime.pendingMapMove())
    {
        std::cout << "Headless diagnostic: pending map move=("
                  << pPendingMapMove->x << ","
                  << pPendingMapMove->y << ","
                  << pPendingMapMove->z << ")";

        if (pPendingMapMove->mapName && !pPendingMapMove->mapName->empty())
        {
            std::cout << " name=\"" << *pPendingMapMove->mapName << "\"";
        }

        std::cout << '\n';
    }

    if (pEventRuntimeState->pendingDialogueContext)
    {
        promoteSingleResidentHouseContext(
            *pEventRuntimeState,
            gameDataLoader.getHouseTable(),
            gameDataLoader.getNpcDialogTable(),
            outdoorWorldRuntime.currentHour()
        );

        const EventRuntimeState::PendingDialogueContext &context = *pEventRuntimeState->pendingDialogueContext;

        if (context.kind == DialogueContextKind::HouseService)
        {
            std::cout << "Headless diagnostic: pending house=" << context.sourceId << '\n';
        }
        else if (context.kind == DialogueContextKind::NpcTalk)
        {
            std::cout << "Headless diagnostic: pending npc=" << context.sourceId << '\n';
        }
        else if (context.kind == DialogueContextKind::NpcNews)
        {
            std::cout << "Headless diagnostic: pending news=" << context.newsId << '\n';
        }
    }

    const EventDialogContent dialog = buildHeadlessDialog(
        *pEventRuntimeState,
        0,
        true,
        selectedMap->globalEventIrProgram,
        gameDataLoader,
        &party,
        outdoorWorldRuntime.currentHour()
    );
    printDialogSummary(dialog);

    if (!pEventRuntimeState->grantedItemIds.empty())
    {
        std::cout << "Headless diagnostic: granted items=";

        for (size_t itemIndex = 0; itemIndex < pEventRuntimeState->grantedItemIds.size(); ++itemIndex)
        {
            if (itemIndex > 0)
            {
                std::cout << ',';
            }

            std::cout << pEventRuntimeState->grantedItemIds[itemIndex];
        }

        std::cout << '\n';
    }

    if (!pEventRuntimeState->removedItemIds.empty())
    {
        std::cout << "Headless diagnostic: removed items=";

        for (size_t itemIndex = 0; itemIndex < pEventRuntimeState->removedItemIds.size(); ++itemIndex)
        {
            if (itemIndex > 0)
            {
                std::cout << ',';
            }

            std::cout << pEventRuntimeState->removedItemIds[itemIndex];
        }

        std::cout << '\n';
    }

    if (const OutdoorWorldRuntime::ChestViewState *pActiveChestView = outdoorWorldRuntime.activeChestView())
    {
        printChestSummary(*pActiveChestView, gameDataLoader.getItemTable());
    }
    else
    {
        std::cout << "Headless diagnostic: no active chest view\n";
    }

    return 0;
}

int HeadlessOutdoorDiagnostics::runOpenActor(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
    {
        std::cerr << "Headless diagnostic failed: selected map has no outdoor actors\n";
        return 1;
    }

    if (actorIndex >= selectedMap->outdoorMapDeltaData->actors.size())
    {
        std::cerr << "Headless diagnostic failed: actor index out of range\n";
        return 2;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getItemTable(),
        selectedMap->outdoorMapDeltaData,
        selectedMap->eventRuntimeState
    );

    Party party = {};
    party.setItemTable(&gameDataLoader.getItemTable());
    party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    party.reset();

    EventRuntimeState *pEventRuntimeState = outdoorWorldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        std::cerr << "Headless diagnostic failed: event runtime state is not available\n";
        return 1;
    }

    const MapDeltaActor &actor = selectedMap->outdoorMapDeltaData->actors[actorIndex];
    const std::string actorName = resolveMapDeltaActorName(gameDataLoader.getMonsterTable(), actor);
    std::cout << "Headless actor diagnostic: index=" << actorIndex
              << " name=\"" << actorName << "\""
              << " npc=" << actor.npcId
              << " monsterInfo=" << actor.monsterInfoId
              << " monsterId=" << actor.monsterId
              << " group=" << actor.group
              << " unique=" << actor.uniqueNameIndex
              << '\n';

    if (actor.npcId > 0)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = static_cast<uint32_t>(actor.npcId);
        pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else
    {
        const std::optional<GenericActorDialogResolution> resolution = resolveGenericActorDialog(
            selectedMap->map.fileName,
            actorName,
            actor.group,
            *pEventRuntimeState,
            gameDataLoader.getNpcDialogTable()
        );

        std::cout << "  resolved_generic_npc="
                  << (resolution ? std::to_string(resolution->npcId) : "-")
                  << " resolved_news="
                  << (resolution ? std::to_string(resolution->newsId) : "0")
                  << '\n';

        if (resolution)
        {
            const std::optional<std::string> newsText =
                gameDataLoader.getNpcDialogTable().getNewsText(resolution->newsId);

            if (newsText)
            {
                EventRuntimeState::PendingDialogueContext context = {};
                context.kind = DialogueContextKind::NpcNews;
                context.sourceId = resolution->npcId;
                context.newsId = resolution->newsId;
                context.titleOverride = actorName;
                pEventRuntimeState->pendingDialogueContext = std::move(context);
                pEventRuntimeState->messages.push_back(*newsText);
            }
        }
    }

    const EventDialogContent dialog = buildHeadlessDialog(
        *pEventRuntimeState,
        0,
        true,
        selectedMap->globalEventIrProgram,
        gameDataLoader,
        &party,
        outdoorWorldRuntime.currentHour()
    );

    if (!dialog.isActive)
    {
        std::cout << "Headless actor diagnostic: no dialog resolved\n";
        return 3;
    }

    printDialogSummary(dialog);
    return 0;
}

int HeadlessOutdoorDiagnostics::runDialogSequence(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    uint16_t eventId,
    const std::vector<size_t> &actionIndices
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getItemTable(),
        selectedMap->outdoorMapDeltaData,
        selectedMap->eventRuntimeState
    );

    Party party = {};
    party.setItemTable(&gameDataLoader.getItemTable());
    party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    party.reset();

    EventRuntime eventRuntime;
    EventRuntimeState *pEventRuntimeState = outdoorWorldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        std::cerr << "Headless diagnostic failed: event runtime state is not available\n";
        return 1;
    }

    const bool executed = eventRuntime.executeEventById(
        selectedMap->localEventIrProgram,
        selectedMap->globalEventIrProgram,
        eventId,
        *pEventRuntimeState,
        &party
    );

    if (!executed)
    {
        std::cerr << "Headless diagnostic failed: event " << eventId << " unresolved\n";
        return 2;
    }

    outdoorWorldRuntime.applyEventRuntimeState();
    party.applyEventRuntimeState(*pEventRuntimeState);

    EventDialogContent dialog = buildHeadlessDialog(
        *pEventRuntimeState,
        0,
        true,
        selectedMap->globalEventIrProgram,
        gameDataLoader,
        &party,
        outdoorWorldRuntime.currentHour()
    );
    std::cout << "Headless diagnostic: initial dialog after event " << eventId << '\n';
    printDialogSummary(dialog);

    for (size_t sequenceIndex = 0; sequenceIndex < actionIndices.size(); ++sequenceIndex)
    {
        const size_t requestedActionIndex = actionIndices[sequenceIndex];

        if (!dialog.isActive || requestedActionIndex >= dialog.actions.size())
        {
            std::cerr << "Headless diagnostic failed: action index out of range at step " << sequenceIndex << '\n';
            return 3;
        }

        const EventDialogAction &action = dialog.actions[requestedActionIndex];
        const size_t previousMessageCount = pEventRuntimeState->messages.size();

        if (action.kind == EventDialogActionKind::HouseResident)
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = action.id;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::RosterJoinOffer)
        {
            const std::optional<NpcDialogTable::RosterJoinOffer> offer =
                gameDataLoader.getNpcDialogTable().getRosterJoinOfferForTopic(action.id);

            if (!offer)
            {
                std::cerr << "Headless diagnostic failed: missing roster join offer data\n";
                return 4;
            }

            const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(offer->inviteTextId);

            if (inviteText && !inviteText->empty())
            {
                pEventRuntimeState->messages.push_back(*inviteText);
            }

            EventRuntimeState::PendingRosterJoinInvite invite = {};
            invite.npcId = dialog.sourceId;
            invite.rosterId = offer->rosterId;
            invite.inviteTextId = offer->inviteTextId;
            invite.partyFullTextId = offer->partyFullTextId;
            pEventRuntimeState->pendingRosterJoinInvite = std::move(invite);

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = dialog.sourceId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::RosterJoinAccept)
        {
            if (!pEventRuntimeState->pendingRosterJoinInvite)
            {
                std::cerr << "Headless diagnostic failed: no pending roster invite\n";
                return 5;
            }

            const EventRuntimeState::PendingRosterJoinInvite invite = *pEventRuntimeState->pendingRosterJoinInvite;
            pEventRuntimeState->pendingRosterJoinInvite.reset();

            if (party.isFull())
            {
                pEventRuntimeState->npcHouseOverrides[invite.npcId] = AdventurersInnHouseId;

                const std::optional<std::string> fullPartyText =
                    gameDataLoader.getNpcDialogTable().getText(invite.partyFullTextId);

                if (fullPartyText && !fullPartyText->empty())
                {
                    pEventRuntimeState->messages.push_back(*fullPartyText);
                }
            }
            else
            {
                const RosterEntry *pRosterEntry = gameDataLoader.getRosterTable().get(invite.rosterId);

                if (pRosterEntry == nullptr || !party.recruitRosterMember(*pRosterEntry))
                {
                    std::cerr << "Headless diagnostic failed: recruitment failed\n";
                    return 6;
                }

                pEventRuntimeState->unavailableNpcIds.insert(invite.npcId);
                pEventRuntimeState->npcHouseOverrides.erase(invite.npcId);
                pEventRuntimeState->messages.push_back(pRosterEntry->name + " joined the party.");
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = invite.npcId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::RosterJoinDecline)
        {
            const uint32_t npcId = pEventRuntimeState->pendingRosterJoinInvite
                ? pEventRuntimeState->pendingRosterJoinInvite->npcId
                : dialog.sourceId;
            pEventRuntimeState->pendingRosterJoinInvite.reset();

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = npcId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::MasteryTeacherOffer)
        {
            EventRuntimeState::PendingMasteryTeacherOffer offer = {};
            offer.npcId = dialog.sourceId;
            offer.topicId = action.id;
            pEventRuntimeState->pendingMasteryTeacherOffer = std::move(offer);

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = dialog.sourceId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::MasteryTeacherLearn)
        {
            if (!pEventRuntimeState->pendingMasteryTeacherOffer)
            {
                std::cerr << "Headless diagnostic failed: no pending mastery teacher offer\n";
                return 7;
            }

            std::string message;

            if (applyMasteryTeacherTopic(
                    pEventRuntimeState->pendingMasteryTeacherOffer->topicId,
                    party,
                    gameDataLoader.getClassSkillTable(),
                    gameDataLoader.getNpcDialogTable(),
                    message))
            {
                if (!message.empty())
                {
                    pEventRuntimeState->messages.push_back(message);
                }

                pEventRuntimeState->pendingMasteryTeacherOffer.reset();
            }
        }
        else if (action.kind == EventDialogActionKind::NpcTopic)
        {
            const bool topicExecuted = eventRuntime.executeEventById(
                std::nullopt,
                selectedMap->globalEventIrProgram,
                static_cast<uint16_t>(action.id),
                *pEventRuntimeState,
                &party
            );

            if (!topicExecuted)
            {
                std::cerr << "Headless diagnostic failed: topic event " << action.id << " unresolved\n";
                return 8;
            }

            outdoorWorldRuntime.applyEventRuntimeState();
            party.applyEventRuntimeState(*pEventRuntimeState);

            if (!pEventRuntimeState->pendingDialogueContext)
            {
                EventRuntimeState::PendingDialogueContext context = {};
                context.kind = DialogueContextKind::NpcTalk;
                context.sourceId = dialog.sourceId;
                pEventRuntimeState->pendingDialogueContext = std::move(context);
            }
        }
        else
        {
            std::cerr << "Headless diagnostic failed: unsupported action kind in sequence\n";
            return 9;
        }

        dialog = buildHeadlessDialog(
            *pEventRuntimeState,
            previousMessageCount,
            action.kind != EventDialogActionKind::RosterJoinAccept
                && action.kind != EventDialogActionKind::MasteryTeacherLearn,
            selectedMap->globalEventIrProgram,
            gameDataLoader,
            &party,
            outdoorWorldRuntime.currentHour()
        );
        std::cout << "Headless diagnostic: dialog after action[" << requestedActionIndex
                  << "] step " << sequenceIndex << '\n';
        printDialogSummary(dialog);
    }

    std::cout << "Headless diagnostic: party members=" << party.members().size() << '\n';
    for (const Character &member : party.members())
    {
        std::cout << "  party \"" << member.name << "\" role=\"" << member.role << "\" level=" << member.level << '\n';
    }

    return 0;
}

int HeadlessOutdoorDiagnostics::runRegressionSuite(
    const std::filesystem::path &basePath,
    const std::string &suiteName
) const
{
    if (suiteName != "dialogue")
    {
        std::cerr << "Unknown regression suite: " << suiteName << '\n';
        return 2;
    }

    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Regression suite failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Regression suite failed: could not load game data\n";
        return 1;
    }

    const std::string mapFileName = "out01.odm";
    const std::optional<MapAssetInfo> &initialSelectedMap = gameDataLoader.getSelectedMap();
    const bool alreadyLoadedTargetMap =
        initialSelectedMap
        && toLowerCopy(std::filesystem::path(initialSelectedMap->map.fileName).filename().string()) == mapFileName;

    if (!alreadyLoadedTargetMap && !gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Regression suite failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
    {
        std::cerr << "Regression suite failed: selected map is not an outdoor map\n";
        return 1;
    }

    int passedCount = 0;
    int failedCount = 0;

    auto runCase =
        [&](const std::string &caseName, auto &&fn)
        {
            std::string failure;
            const bool passed = fn(failure);
            std::cout << "["
                      << (passed ? "PASS" : "FAIL")
                      << "] "
                      << caseName;

            if (!passed && !failure.empty())
            {
                std::cout << " - " << failure;
            }

            std::cout << '\n';

            if (passed)
            {
                ++passedCount;
            }
            else
            {
                ++failedCount;
            }
        };

    runCase(
        "dwi_actor_peasant_news",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!openActorInScenario(gameDataLoader, *selectedMap, scenario, 5))
            {
                failure = "actor open failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (dialog.title != "Lizardman Peasant")
            {
                failure = "unexpected title \"" + dialog.title + "\"";
                return false;
            }

            if (!dialogContainsText(dialog, "If the pirates make it through our warriors"))
            {
                failure = "missing peasant news text";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_actor_lookout_news",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!openActorInScenario(gameDataLoader, *selectedMap, scenario, 35))
            {
                failure = "actor open failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (!dialogContainsText(dialog, "Would you like to fire the cannons"))
            {
                failure = "missing lookout cannon prompt";
                return false;
            }

            return true;
        }
    );

    runCase(
        "single_resident_auto_open",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 37))
            {
                failure = "event 37 failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (dialog.title != "Fredrick Talimere")
            {
                failure = "unexpected title \"" + dialog.title + "\"";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Portals of Stone") || !dialogHasActionLabel(dialog, "Cataclysm"))
            {
                failure = "missing baseline Fredrick topics";
                return false;
            }

            return true;
        }
    );

    runCase(
        "multi_resident_house_selection",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 197))
            {
                failure = "event 197 failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (dialog.title != "Clan Leader's Hall")
            {
                failure = "unexpected title \"" + dialog.title + "\"";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Brekish Onefang") || !dialogHasActionLabel(dialog, "Dadeross"))
            {
                failure = "missing resident actions";
                return false;
            }

            return true;
        }
    );

    runCase(
        "brekish_topic_mutation",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 197))
            {
                failure = "event 197 failed";
                return false;
            }

            EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            const std::optional<size_t> brekishIndex = findActionIndexByLabel(dialog, "Brekish Onefang");

            if (!brekishIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *brekishIndex, dialog))
            {
                failure = "could not open Brekish";
                return false;
            }

            const std::optional<size_t> portalsIndex = findActionIndexByLabel(dialog, "Portals of Stone");

            if (!portalsIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *portalsIndex, dialog))
            {
                failure = "could not execute Portals of Stone";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Quest"))
            {
                failure = "Portals of Stone did not mutate into Quest";
                return false;
            }

            return true;
        }
    );

    runCase(
        "fredrick_topics_after_brekish_quest",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 197))
            {
                failure = "event 197 failed";
                return false;
            }

            EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            const std::optional<size_t> brekishIndex = findActionIndexByLabel(dialog, "Brekish Onefang");

            if (!brekishIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *brekishIndex, dialog))
            {
                failure = "could not open Brekish";
                return false;
            }

            const std::optional<size_t> portalsIndex = findActionIndexByLabel(dialog, "Portals of Stone");

            if (!portalsIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *portalsIndex, dialog))
            {
                failure = "could not execute Portals of Stone";
                return false;
            }

            const std::optional<size_t> questIndex = findActionIndexByLabel(dialog, "Quest");

            if (!questIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *questIndex, dialog))
            {
                failure = "could not execute Quest";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 37))
            {
                failure = "event 37 failed after quest";
                return false;
            }

            dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (!dialogHasActionLabel(dialog, "Power Stone") || !dialogHasActionLabel(dialog, "Abandoned Temple"))
            {
                failure = "Fredrick missing unlocked quest topics";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_not_enough_gold",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not select sorcerer";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr
                || ensureCharacterSkill(*pCharacter, "IdentifyItem", 7, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare Identify Item skill";
                return false;
            }

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty() || dialog.actions.front().label != "You don't have enough gold!")
            {
                failure = "missing not-enough-gold rejection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_missing_skill",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not select sorcerer";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr)
            {
                failure = "missing active character";
                return false;
            }

            pCharacter->skills.erase("IdentifyItem");

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label != "You must know the skill before you can become an expert in it!")
            {
                failure = "missing missing-skill rejection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_insufficient_skill_level",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not select sorcerer";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr
                || ensureCharacterSkill(*pCharacter, "IdentifyItem", 6, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare insufficient skill state";
                return false;
            }

            scenario.party.addGold(5000);

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label
                    != "You don't meet the requirements, and cannot be taught until you do.")
            {
                failure = "missing insufficient-requirements rejection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_wrong_class",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(0))
            {
                failure = "could not select knight";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr
                || ensureCharacterSkill(*pCharacter, "IdentifyItem", 7, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare wrong-class skill state";
                return false;
            }

            scenario.party.addGold(5000);

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label != "This skill level can not be learned by the Knight class.")
            {
                failure = "missing wrong-class rejection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_character_switch_changes_logic",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(0))
            {
                failure = "could not select knight";
                return false;
            }

            Character *pKnight = scenario.party.activeMember();

            if (pKnight == nullptr || ensureCharacterSkill(*pKnight, "IdentifyItem", 7, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare knight state";
                return false;
            }

            scenario.party.addGold(5000);

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer for knight";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label != "This skill level can not be learned by the Knight class.")
            {
                failure = "wrong-class baseline did not match";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not switch to sorcerer";
                return false;
            }

            Character *pSorcerer = scenario.party.activeMember();

            if (pSorcerer == nullptr
                || ensureCharacterSkill(*pSorcerer, "IdentifyItem", 7, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare sorcerer state";
                return false;
            }

            dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (dialog.actions.empty() || dialog.actions.front().label != "Become Master in Identify Item for 2500 gold")
            {
                failure = "dialog did not change after switching active character";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_offer_and_learn",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not select sorcerer";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr)
            {
                failure = "missing active character";
                return false;
            }

            CharacterSkill *pIdentifyItem = ensureCharacterSkill(*pCharacter, "IdentifyItem", 7, SkillMastery::Expert);

            if (pIdentifyItem == nullptr)
            {
                failure = "could not prepare Identify Item skill";
                return false;
            }

            scenario.party.addGold(5000);

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label != "Become Master in Identify Item for 2500 gold")
            {
                failure = "unexpected mastery teacher offer text";
                return false;
            }

            if (!executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, 0, dialog))
            {
                failure = "could not learn mastery";
                return false;
            }

            const Character *pUpdatedCharacter = scenario.party.activeMember();
            const CharacterSkill *pUpdatedSkill = pUpdatedCharacter != nullptr
                ? pUpdatedCharacter->findSkill("IdentifyItem")
                : nullptr;

            if (pUpdatedSkill == nullptr || pUpdatedSkill->mastery != SkillMastery::Master)
            {
                failure = "mastery was not increased";
                return false;
            }

            if (scenario.party.gold() != 2700)
            {
                failure = "gold was not deducted by trainer cost";
                return false;
            }

            if (!dialogContainsText(dialog, "Doran is now a Master in Identify Item."))
            {
                failure = "missing mastery confirmation text";
                return false;
            }

            return true;
        }
    );

    runCase(
        "synthetic_roster_join_accept",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(202);

            if (inviteText)
            {
                scenario.pEventRuntimeState->messages.push_back(*inviteText);
            }

            EventRuntimeState::PendingRosterJoinInvite invite = {};
            invite.npcId = 32;
            invite.rosterId = 2;
            invite.inviteTextId = 202;
            invite.partyFullTextId = 203;
            scenario.pEventRuntimeState->pendingRosterJoinInvite = invite;

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = 32;
            scenario.pEventRuntimeState->pendingDialogueContext = context;

            EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

            if (!yesIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *yesIndex, dialog))
            {
                failure = "could not accept roster join offer";
                return false;
            }

            if (scenario.party.members().size() != 5)
            {
                failure = "expected party size 5 after recruit";
                return false;
            }

            if (!scenario.pEventRuntimeState->unavailableNpcIds.contains(32))
            {
                failure = "Fredrick was not marked unavailable";
                return false;
            }

            if (!dialogContainsText(dialog, "joined the party"))
            {
                failure = "missing join confirmation text";
                return false;
            }

            return true;
        }
    );

    runCase(
        "synthetic_roster_join_full_party",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const RosterEntry *pExtraMember = gameDataLoader.getRosterTable().get(3);

            if (pExtraMember == nullptr || !scenario.party.recruitRosterMember(*pExtraMember))
            {
                failure = "could not fill party to 5";
                return false;
            }

            const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(202);

            if (inviteText)
            {
                scenario.pEventRuntimeState->messages.push_back(*inviteText);
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = 32;
            scenario.pEventRuntimeState->pendingDialogueContext = context;

            EventRuntimeState::PendingRosterJoinInvite invite = {};
            invite.npcId = 32;
            invite.rosterId = 2;
            invite.inviteTextId = 202;
            invite.partyFullTextId = 203;
            scenario.pEventRuntimeState->pendingRosterJoinInvite = invite;

            EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

            if (!yesIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *yesIndex, dialog))
            {
                failure = "could not accept full-party offer";
                return false;
            }

            if (scenario.party.members().size() != 5)
            {
                failure = "party size changed unexpectedly";
                return false;
            }

            if (scenario.pEventRuntimeState->unavailableNpcIds.contains(32))
            {
                failure = "Fredrick should remain available after moving to the inn";
                return false;
            }

            const auto movedHouseIt = scenario.pEventRuntimeState->npcHouseOverrides.find(32);

            if (movedHouseIt == scenario.pEventRuntimeState->npcHouseOverrides.end()
                || movedHouseIt->second != AdventurersInnHouseId)
            {
                failure = "Fredrick was not moved to the Adventurer's Inn";
                return false;
            }

            if (!dialogContainsText(dialog, "party's all full up"))
            {
                failure = "missing full-party response text";
                return false;
            }

            EventRuntimeState::PendingDialogueContext innContext = {};
            innContext.kind = DialogueContextKind::HouseService;
            innContext.sourceId = AdventurersInnHouseId;
            scenario.pEventRuntimeState->pendingDialogueContext = innContext;
            dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (!dialogHasActionLabel(dialog, "Fredrick Talimere"))
            {
                failure = "Fredrick did not appear in the Adventurer's Inn";
                return false;
            }

            return true;
        }
    );

    runCase(
        "roster_join_mapping_and_players_can_show_topic",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 9);

            if (!dialogHasActionLabel(dialog, "Dyson Leland"))
            {
                failure = "Sandro should initially expose the Dyson Leland topic";
                return false;
            }

            scenario.pEventRuntimeState->npcTopicOverrides[11][3] = 634;
            dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 11);

            const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

            if (!joinIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *joinIndex, dialog))
            {
                failure = "could not open Dyson roster join offer";
                return false;
            }

            if (!dialogContainsText(dialog, "I will gladly join you."))
            {
                failure = "missing Dyson roster join prompt text";
                return false;
            }

            const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

            if (!yesIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *yesIndex, dialog))
            {
                failure = "could not accept Dyson roster join offer";
                return false;
            }

            if (!scenario.party.hasRosterMember(34))
            {
                failure = "Dyson roster member was not added to the party";
                return false;
            }

            dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 9);

            if (dialogHasActionLabel(dialog, "Dyson Leland"))
            {
                failure = "Dyson Leland topic should hide once Dyson is in the party";
                return false;
            }

            return true;
        }
    );

    runCase(
        "empty_house_after_departure",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            scenario.pEventRuntimeState->unavailableNpcIds.insert(32);

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 37))
            {
                failure = "event 37 failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (!dialogContainsText(dialog, "The house is empty."))
            {
                failure = "missing empty-house text";
                return false;
            }

            return true;
        }
    );

    std::cout << "Regression suite summary: passed=" << passedCount << " failed=" << failedCount << '\n';
    return failedCount == 0 ? 0 : 1;
}
}
