#pragma once

#include "game/arcomage/ArcomageTypes.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/tables/MapStats.h"

#include <optional>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

inline GameplayDialogController::Context buildGameplayDialogContext(
    GameplayUiController &uiController,
    EventRuntimeState &eventRuntimeState,
    EventDialogContent &activeEventDialog,
    size_t &selectionIndex,
    Party *pParty,
    IGameplayWorldRuntime *pWorldRuntime,
    const std::optional<ScriptedEventProgram> *pGlobalEventProgram,
    const HouseTable *pHouseTable,
    const ClassSkillTable *pClassSkillTable,
    const NpcDialogTable *pNpcDialogTable,
    const MapStatsEntry *pCurrentMap,
    const std::vector<MapStatsEntry> *pMapEntries,
    const RosterTable *pRosterTable,
    const ArcomageLibrary *pArcomageLibrary,
    bool dialogueHudActive,
    GameplayScreenRuntime *pScreenRuntime)
{
    GameplayDialogController::Context context = {
        uiController,
        eventRuntimeState,
        activeEventDialog,
        selectionIndex,
        pScreenRuntime,
        pParty,
        pWorldRuntime,
        pGlobalEventProgram,
        pHouseTable,
        pClassSkillTable,
        pNpcDialogTable,
        pCurrentMap,
        pMapEntries,
        pRosterTable,
        pArcomageLibrary,
        dialogueHudActive
    };
    return context;
}
} // namespace OpenYAMM::Game
