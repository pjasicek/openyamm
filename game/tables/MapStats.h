#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class MapBoundaryEdge : uint8_t
{
    North = 0,
    South = 1,
    East = 2,
    West = 3,
};

struct MapEncounterInfo
{
    int chance = 0;
    std::string pictureName;
    std::string monsterName;
    int difficulty = 0;
    int minCount = 0;
    int maxCount = 0;
};

struct MapBounds
{
    bool enabled = false;
    int minX = 0;
    int maxX = 0;
    int minY = 0;
    int maxY = 0;
};

struct MapEdgeTransition
{
    std::string destinationMapFileName;
    int travelDays = 0;
    std::optional<int> directionDegrees;
    bool useMapStartPosition = true;
    std::optional<int> arrivalX;
    std::optional<int> arrivalY;
    std::optional<int> arrivalZ;
};

struct MapStatsEntry
{
    int id;
    std::string name;
    std::string fileName;
    int treasureLevel;
    int encounterChance;
    MapEncounterInfo encounter1;
    MapEncounterInfo encounter2;
    MapEncounterInfo encounter3;
    int redbookTrack;
    std::string environmentName;
    bool isTopLevelArea;
    MapBounds outdoorBounds = {};
    std::optional<MapEdgeTransition> northTransition;
    std::optional<MapEdgeTransition> southTransition;
    std::optional<MapEdgeTransition> eastTransition;
    std::optional<MapEdgeTransition> westTransition;

    const std::optional<MapEdgeTransition> *edgeTransition(MapBoundaryEdge edge) const;
    std::optional<MapEdgeTransition> *edgeTransition(MapBoundaryEdge edge);
};

class MapStats
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    bool applyOutdoorNavigationRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MapStatsEntry> &getEntries() const;
    const MapStatsEntry *findByFileName(const std::string &fileName) const;

private:
    static bool isDataRow(const std::vector<std::string> &row);
    static bool parseInteger(const std::string &value, int &result);
    static std::string normalizeFileName(const std::string &value);

    MapStatsEntry *findMutableByFileName(const std::string &fileName);

    std::vector<MapStatsEntry> m_entries;
};
}
