#include "game/ActorNameResolver.h"
#include "game/HeadlessOutdoorDiagnostics.h"

#include "engine/AssetFileSystem.h"
#include "game/EventDialogContent.h"
#include "game/EventRuntime.h"
#include "game/GameDataLoader.h"
#include "game/GenericActorDialog.h"
#include "game/HouseInteraction.h"
#include "game/OutdoorWorldRuntime.h"

#include <iostream>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
std::optional<uint32_t> singleSelectableResidentNpcId(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable
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

    if (!gameDataLoader.load(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileName(assetFileSystem, mapFileName))
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
        nullptr
    );

    if (!executed)
    {
        std::cout << "Headless diagnostic: event " << eventId << " unresolved\n";
        return 2;
    }

    outdoorWorldRuntime.applyEventRuntimeState();

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
        if (pEventRuntimeState->pendingDialogueContext->kind == DialogueContextKind::HouseService)
        {
            const HouseEntry *pHouseEntry =
                gameDataLoader.getHouseTable().get(pEventRuntimeState->pendingDialogueContext->sourceId);

            if (pHouseEntry != nullptr)
            {
                const std::vector<HouseActionOption> houseActions = buildHouseActionOptions(
                    *pHouseEntry,
                    nullptr,
                    outdoorWorldRuntime.currentHour()
                );
                const std::optional<uint32_t> residentNpcId = singleSelectableResidentNpcId(
                    *pHouseEntry,
                    gameDataLoader.getNpcDialogTable()
                );

                if (residentNpcId && houseActions.empty())
                {
                    EventRuntimeState::PendingDialogueContext context = {};
                    context.kind = DialogueContextKind::NpcTalk;
                    context.sourceId = *residentNpcId;
                    pEventRuntimeState->pendingDialogueContext = std::move(context);
                }
            }
        }

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

    const EventDialogContent dialog = buildEventDialogContent(
        *pEventRuntimeState,
        0,
        true,
        &selectedMap->globalEventIrProgram,
        &gameDataLoader.getHouseTable(),
        &gameDataLoader.getNpcDialogTable(),
        nullptr,
        outdoorWorldRuntime.currentHour()
    );

    if (dialog.isActive)
    {
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

    if (!gameDataLoader.load(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileName(assetFileSystem, mapFileName))
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

    const EventDialogContent dialog = buildEventDialogContent(
        *pEventRuntimeState,
        0,
        true,
        &selectedMap->globalEventIrProgram,
        &gameDataLoader.getHouseTable(),
        &gameDataLoader.getNpcDialogTable(),
        nullptr,
        outdoorWorldRuntime.currentHour()
    );

    if (!dialog.isActive)
    {
        std::cout << "Headless actor diagnostic: no dialog resolved\n";
        return 3;
    }

    std::cout << "Headless actor diagnostic: dialog title=\"" << dialog.title << "\"\n";

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
                  << '\n';
    }

    return 0;
}
}
