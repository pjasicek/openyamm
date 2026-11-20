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
class Mm9RudeDialogueTable;
class Mm9MapTransitionTable;
class Mm9SkillTrainerTable;
class Mm9TransportRouteTable;

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
    const Mm9RudeDialogueTable *pMm9RudeDialogueTable,
    const Mm9MapTransitionTable *pMm9MapTransitionTable,
    const Mm9SkillTrainerTable *pMm9SkillTrainerTable,
    const Mm9TransportRouteTable *pMm9TransportRouteTable,
    const TransitionTable *pTransitionTable,
    const MapStatsEntry *pCurrentMap,
    const std::vector<MapStatsEntry> *pMapEntries,
    const RosterTable *pRosterTable,
    const ArcomageLibrary *pArcomageLibrary,
    bool dialogueHudActive,
    GameplayScreenRuntime *pScreenRuntime,
    const MergedNpcProfessionTable *pNpcProfessionTable = nullptr,
    const MergedNewsProfessionTopicTable *pNewsProfessionTopicTable = nullptr,
    const MergedNpcBtbTable *pNpcBtbTable = nullptr,
    const MergedBolsterMapTable *pBolsterMapTable = nullptr,
    const MergedContinentSettingTable *pContinentSettingTable = nullptr,
    const MergedTeacherTopicTable *pTeacherTopicTable = nullptr,
    const MergedTeacherAutonoteTable *pTeacherAutonoteTable = nullptr,
    const SpellTable *pSpellTable = nullptr)
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
        pMm9RudeDialogueTable,
        pMm9MapTransitionTable,
        pMm9SkillTrainerTable,
        pMm9TransportRouteTable,
        pTransitionTable,
        pCurrentMap,
        pMapEntries,
        pRosterTable,
        pArcomageLibrary,
        pNpcProfessionTable,
        pNewsProfessionTopicTable,
        pNpcBtbTable,
        pBolsterMapTable,
        pContinentSettingTable,
        pTeacherTopicTable,
        pTeacherAutonoteTable,
        dialogueHudActive,
        pSpellTable
    };
    return context;
}
} // namespace OpenYAMM::Game
