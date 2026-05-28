#pragma once

#include "game/maps/MapRuntimeRestrictions.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class MergedOutdoorTravelTable;
class MergedBolsterMapTable;

enum class MapBoundaryEdge : uint8_t
{
    North = 0,
    South = 1,
    East = 2,
    West = 3,
};

enum class MapTransitionSurfaceRequirement : uint8_t
{
    Land = 0,
    Water = 1,
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
    bool straightTravel = false;
    std::optional<MapBoundaryEdge> straightTravelSide;
    MapTransitionSurfaceRequirement requiredOriginSurface = MapTransitionSurfaceRequirement::Land;
    std::vector<uint32_t> requiredQuestBitsAny;
};

struct MapStatsEntry
{
    int id;
    std::string worldId;
    std::string canonicalId;
    std::string name;
    std::string fileName;
    int respawnIntervalDays = 0;
    int perceptionDifficulty = 0;
    int baseStealingFine = 0;
    int disarmDifficulty = 0;
    int trapDamageD20DiceCount = 0;
    int treasureLevel;
    int encounterChance;
    MapEncounterInfo encounter1;
    MapEncounterInfo encounter2;
    MapEncounterInfo encounter3;
    MapEncounterInfo encounter4;
    int redbookTrack;
    std::string environmentName;
    int areaId = 0;
    uint32_t mergedContinentId = 1;
    bool isTopLevelArea;
    int sourceMapId = 0;
    std::string sourceFileName;
    int musicTrack = 0;
    int battleTrack = 0;
    int travelDays = 0;
    int sourceRedbookTrack = 0;
    std::string sourceAreaCode;
    int townPortalMapId = 0;
    int inTown = 0;
    MapBounds outdoorBounds = {};
    std::optional<MapEdgeTransition> northTransition;
    std::optional<MapEdgeTransition> southTransition;
    std::optional<MapEdgeTransition> eastTransition;
    std::optional<MapEdgeTransition> westTransition;
    MapRuntimeRestrictions runtimeRestrictions = {};

    const std::optional<MapEdgeTransition> *edgeTransition(MapBoundaryEdge edge) const;
    std::optional<MapEdgeTransition> *edgeTransition(MapBoundaryEdge edge);
};

class MapStats
{
public:
    bool loadFromRows(
        const std::vector<std::vector<std::string>> &rows,
        const std::string &worldId = "mm8"
    );
    bool applyMergedBolsterMaps(const MergedBolsterMapTable &bolsterMaps);
    bool applyOutdoorNavigationRows(const std::vector<std::vector<std::string>> &rows);
    bool applyMergedOutdoorTravels(const MergedOutdoorTravelTable &outdoorTravels);
    const std::vector<MapStatsEntry> &getEntries() const;
    const MapStatsEntry *findById(uint32_t id) const;
    const MapStatsEntry *findByFileName(const std::string &fileName) const;

private:
    static bool isDataRow(const std::vector<std::string> &row);
    static bool parseInteger(const std::string &value, int &result);
    static std::string normalizeFileName(const std::string &value);

    MapStatsEntry *findMutableByFileName(const std::string &fileName);

    std::vector<MapStatsEntry> m_entries;
};
}
