#pragma once

#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class HouseTable;
class MapStats;
class Party;
class TrainerDirectory;

// The Journal's Arcomage notes: per continent (the new-game cards' continents in the cards' order, from the trainer
// directory; Elsewhere last), how many of its taverns the party has beaten, then each tavern with its town and whether
// it is won.
std::vector<std::string> buildArcomageTavernTexts(const HouseTable &houseTable, const MapStats &mapStats,
    const TrainerDirectory *pDirectory, const Party &party);
} // namespace OpenYAMM::Game
