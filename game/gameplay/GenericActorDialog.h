#pragma once

#include "game/events/EventRuntime.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class NpcDialogTable;
class MergedBolsterMapTable;
class MergedBolsterMonsterTable;
class MergedMonsterPortraitTable;
class MergedNpcNameTable;
class MergedNpcProfessionTable;
class MergedNewsTopicTable;
struct MapStatsEntry;

struct GenericActorDialogResolution
{
    uint32_t npcId = 0;
    uint32_t newsId = 0;
    uint32_t portraitPictureId = 0;
    bool opensNpcTalk = false;
    bool generatedNpc = false;
    std::string generatedActorKey;
    std::string generatedName;
    uint32_t generatedProfessionId = 0;
};

void refreshGenericActorNpcRoster(EventRuntimeState &runtimeState, float gameMinutes);

std::optional<GenericActorDialogResolution> resolveGenericActorDialog(
    const std::string &mapFileName,
    const std::string &actorName,
    uint32_t actorGroup,
    const EventRuntimeState &runtimeState,
    const NpcDialogTable &npcDialogTable,
    const MergedMonsterPortraitTable *pMonsterPortraitTable = nullptr,
    const MapStatsEntry *pCurrentMap = nullptr,
    const MergedNewsTopicTable *pNewsAreaTopicTable = nullptr,
    const MergedNewsTopicTable *pNewsContinentTopicTable = nullptr,
    const MergedNpcNameTable *pNpcNameTable = nullptr,
    const MergedNpcProfessionTable *pNpcProfessionTable = nullptr,
    const MergedBolsterMapTable *pBolsterMapTable = nullptr,
    const MergedBolsterMonsterTable *pBolsterMonsterTable = nullptr,
    uint32_t actorMonsterId = 0,
    std::optional<size_t> actorIndex = std::nullopt
);

void applyGenericActorDialogResolution(
    EventRuntimeState &runtimeState,
    const GenericActorDialogResolution &resolution
);

std::optional<std::string> generatedNpcGroupNewsText(
    const EventRuntimeState &runtimeState,
    const NpcDialogTable &npcDialogTable,
    uint32_t npcId,
    const MapStatsEntry *pCurrentMap);

bool hideGeneratedNpcActor(
    EventRuntimeState &runtimeState,
    uint32_t npcId,
    const MapStatsEntry *pCurrentMap
);

bool hideMapActorByIndex(EventRuntimeState &runtimeState, uint32_t actorIndex);
}
