#pragma once

#include "game/tables/MapStats.h"
#include "game/ui/GameplayUiController.h"

#include <string>
#include <vector>

namespace OpenYAMM::Game
{
constexpr size_t GameplaySaveLoadVisibleSlotCount = 10;

std::string resolveSaveLocationName(const std::vector<MapStatsEntry> &mapEntries, const std::string &mapFileName);
void refreshSaveGameSlots(
    GameplayUiController::SaveGameScreenState &saveGameScreen,
    const std::vector<MapStatsEntry> &mapEntries);
void refreshLoadGameSlots(
    GameplayUiController::LoadGameScreenState &loadGameScreen,
    const std::vector<MapStatsEntry> &mapEntries);
} // namespace OpenYAMM::Game
