#pragma once

#include "game/tables/MonsterTable.h"

#include <array>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
struct MapStatsEntry;

// The MAW ruleset's map data (rulesets/maw/data/map_levels.yml): each map's monster level band, the horizontal
// starter maps and the Beyond Madness level of each map. Keyed by lowercase map file name.
class MawMapLevels
{
public:
    bool loadFromYaml(const std::string &text, std::string &errorMessage);
    // A world's maps from its MAW balance file (rulesets/maw/worlds/<world>/balance.yml `maps`: band,
    // horizontal_starter, madness_start, madness_level, story_bands), after map_levels.yml. A map both list is an error.
    bool loadWorldBalance(const std::string &text, std::string &errorMessage);
    // Low, mid and high B levels (some are halves); {1, 1, 1} for a map MAW does not list. A story band (a world's
    // balance file) replaces the map's band once its quest bit is reached: the last reached one listed wins.
    std::array<double, 3> band(const std::string &mapFileName) const;
    // The quest bits story bands wait for, and those the party has (MawRules::updateStoryBands); true when they
    // changed.
    std::vector<uint32_t> storyBandQBits() const;
    bool setReachedStoryQBits(std::unordered_set<uint32_t> qbits);
    // Whether a monster counts toward the map's clearing: not one its world's balance file leaves out
    // (`completion_exclude` for all its maps and a map's own), by monster row, name, picture or family (a picture
    // without its tier letter).
    bool countsForCompletion(const std::string &mapFileName, const MonsterTable::MonsterStatsEntry &stats) const;
    // The map's native families as its world's balance file names them (`natives`: pictures without the tier letter,
    // up to three), in place of the map table's encounter pictures; null where it names none.
    const std::array<std::string, 3> *natives(const std::string &mapFileName) const;
    // A world map's density factor (its balance file's `density`: the challenge mode's factor, else the difficulty's,
    // times the map's own `density`); 1 for a map no balance file lists.
    double densityFactor(const std::string &mapFileName, const std::string &difficulty,
        const std::string &challengeMode) const;
    // Whether MAW lists the map (it has a band): the maps the Journal's Progress tab counts.
    bool lists(const std::string &mapFileName) const;
    bool isHorizontalStarterMap(const std::string &mapFileName) const;
    bool isMadnessStartingMap(const std::string &mapFileName) const;
    // The fixed Beyond Madness level of a map, or 0 when it has none.
    int madnessLevel(const std::string &mapFileName) const;

private:
    struct StoryBand
    {
        uint32_t qbit = 0;
        std::array<double, 3> band = {};
    };

    std::unordered_map<std::string, std::array<double, 3>> m_bands;
    std::unordered_map<std::string, std::vector<StoryBand>> m_storyBands;
    std::unordered_map<std::string, std::array<std::string, 3>> m_natives;
    // Per balance-listed map: its own density, and its file's factors by difficulty and challenge mode.
    struct DensityFactors
    {
        double map = 1;
        std::unordered_map<std::string, double> byDifficulty;
        std::unordered_map<std::string, double> byChallengeMode;
    };
    std::unordered_map<std::string, DensityFactors> m_density;
    // Per map: the monster rows and the names, pictures or families left out of its clearing.
    std::unordered_map<std::string, std::pair<std::unordered_set<int>, std::vector<std::string>>>
        m_completionExclusions;
    std::unordered_set<uint32_t> m_reachedStoryQBits;
    std::unordered_set<std::string> m_horizontalStarterMaps;
    std::unordered_set<std::string> m_madnessStartingMaps;
    std::unordered_map<std::string, int> m_madnessLevels;
};

// What a map's monster levels depend on besides the monster table.
struct MawMonsterLevelInputs
{
    std::string mapFileName;
    // MapStats Monster1Pic..Monster3Pic.
    std::array<std::string, 3> encounterPictures;
    bool horizontalProgression = false;
    bool madness = false;
    bool austerity = false;
    // Levels banked on the other continents (getPartyLevel).
    double partyLevel = 0;
    int resetCount = 0;
    // A dimension map's power on the map: monsters sit at power x 10 + 20 over their base, without party bolster.
    std::optional<int> dimensionPower;
    // A bounty hunt's map: every monster sits at its table level plus these, whatever else applies (MON:591-593).
    std::optional<double> bountyLevel;
};

// The levels every monster of a map gains (bolsterLevel, zzMaw-Monsters.lua:417-445): the party's banked levels less
// 4 (^1.015 in Austerity), Beyond Madness's fixed map level, +20 per reset; a dimension map's power x 10 + 20. Corpse
// gold reads it too.
double mawMapBolster(const MawMapLevels &mapLevels, const MawMonsterLevelInputs &inputs);

// Every monster's level on a map under MAW (devdocs/maw/BALANCE_MODEL.md §7.1-7.4, zzMaw-Monsters.lua
// recalculateMonsterTable), by monster id. Levels are not capped at 255. The Arena (d42) and dimension maps have their
// own rules; bounty maps raise the levels of their monsters where they are spawned.
std::unordered_map<int, int> resolveMawMonsterLevels(
    const MonsterTable &monsterTable,
    const MawMapLevels &mapLevels,
    const MawMonsterLevelInputs &inputs);

// The monster rows MAW's level rules cover: its own (1-651) and every world's (from MawWorldMonsterRows, MM9's 9000+).
// MMMerge's later rows (652-906: the Reactor, the custom Crusaders and Mages) keep their table levels, as in MAW.
constexpr int MawMonsterRows = 651;
constexpr int MawWorldMonsterRows = 1000;
bool mawLevelsMonster(int monsterId);

// A monster's family: monsters come in A/B/C tiers and every level-related number reads the B row. The rows below
// MawWorldMonsterRows are triples by id (A at id % 3 == 1), as MAW reads them, and every one of them whose picture has
// a tier suffix agrees with it; a world's rows go by their picture's suffix ("MM9 Dragonfly A"), and one without a
// suffix (a townsperson, a named unique) is a family of its own at tier B.
struct MawMonsterFamily
{
    int monsterId = 0;
    uint8_t tier = 2;
    // The family's A, B and C rows; 0 for a tier the family lacks.
    std::array<int, 3> rows = {};

    // That tier's row; the B row where the family lacks it, and the monster itself where it has no B row.
    int row(int tierIndex) const;
};

// Without a monster table a world's row is a family of its own.
MawMonsterFamily mawMonsterFamily(const MonsterTable *pMonsterTable, int monsterId);

// The arenas (MAW's d42, 7d05 and zarena, and MM9's thearena: each picks its fighters by the party's level), whose
// monsters get no bolster and whose kills in Beyond Madness pay nothing.
bool mawArenaMap(const std::string &mapFileName);
}
