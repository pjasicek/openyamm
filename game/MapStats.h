#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct MapEncounterInfo
{
    int chance = 0;
    std::string pictureName;
    std::string monsterName;
    int difficulty = 0;
    int minCount = 0;
    int maxCount = 0;
};

struct MapStatsEntry
{
    int id;
    std::string name;
    std::string fileName;
    int encounterChance;
    MapEncounterInfo encounter1;
    MapEncounterInfo encounter2;
    MapEncounterInfo encounter3;
    int redbookTrack;
    std::string environmentName;
    bool isTopLevelArea;
};

class MapStats
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MapStatsEntry> &getEntries() const;

private:
    static bool isDataRow(const std::vector<std::string> &row);
    static bool parseInteger(const std::string &value, int &result);

    std::vector<MapStatsEntry> m_entries;
};
}
