#pragma once

#include "game/rules/ExperienceRules.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class MapStats;
class MonsterTable;
class Party;
struct EventRuntimeState;

// How far the party got on a map, as the Journal's Progress tab lists it.
enum class RulesetMapProgressState : uint8_t
{
    NotVisited,
    InProgress,
    Cleared,
};

struct RulesetProgressMap
{
    std::string fileName;
    std::string name;
    // Its monsters' level now, and the part of it its resets add.
    int level = 0;
    int levelFromResets = 0;
    int resets = 0;
    RulesetMapProgressState state = RulesetMapProgressState::NotVisited;
    // Slain of the monsters that count (0-1); cleared since its last refill, and its completion reward paid once.
    double slainShare = 0;
    bool clearedSinceRefill = false;
    bool completedOnce = false;
    // Game days until its monsters refill (none: never, or not visited).
    std::optional<int> refillInDays;
    // The reset its entrance dialog offers, if any.
    std::optional<std::string> resetOffer;
    // The party is on it; this month's town bounty target is on it; a dimension run is open on it.
    bool current = false;
    bool bountyTarget = false;
    bool dimensionRun = false;
};

struct RulesetProgressContinent
{
    std::string name;
    std::string world;
    int levelLow = 0;
    int levelHigh = 0;
    double levelsBanked = 0;
    int mapsCleared = 0;
    // The continent's maps by level.
    std::vector<RulesetProgressMap> maps;
};

// The Journal's Progress tab (MAW): the game's settings, each continent with its maps, and the dimension and bounty
// records.
struct RulesetProgressSummary
{
    std::string difficulty;
    std::string progression;
    std::string challengeMode;
    int totalLevel = 0;
    // Beyond Madness's deaths.
    std::optional<int> deaths;
    std::vector<RulesetProgressContinent> continents;
    std::string dimensionQuest;
    int dimensionRunsCleared = 0;
    std::string currentRun;
    int bountiesClaimed = 0;
    int bountyGold = 0;
};

struct RulesetProgressQuery
{
    const MapStats *pMapTable = nullptr;
    const MonsterTable *pMonsterTable = nullptr;
    const Party *pParty = nullptr;
    // The town bounties (MMerge.BountyHunt.<map name>.* global variables).
    const EventRuntimeState *pEventState = nullptr;
    float gameMinutes = 0;
    // The map the party is on and how far it is cleared now (its saved record is from the last time it was left).
    std::optional<MapKillProgress> currentMap;
};
}
