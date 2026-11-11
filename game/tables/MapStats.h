#pragma once

#include "game/maps/MapRuntimeRestrictions.h"
#include "game/maps/MapArenaDefinition.h"

#include <cstdint>
#include <optional>
#include <string>
#include <utility>
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
    // The side of the destination the party enters: its "<side> start" decoration, or the mirrored crossing point
    // for straight travel.
    std::optional<MapBoundaryEdge> arrivalSide;
    MapTransitionSurfaceRequirement requiredOriginSurface = MapTransitionSurfaceRequirement::Land;
    std::vector<uint32_t> requiredQuestBitsAny;
};

struct MapStatsEntry
{
    int id;
    std::string worldId;
    bool explicitWorldId = false;
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
    int redbookTrack;
    std::string environmentName;
    int areaId = 0;
    uint32_t mergedContinentId = 1;
    bool isTopLevelArea;
    MapBounds outdoorBounds = {};
    std::optional<MapEdgeTransition> northTransition;
    std::optional<MapEdgeTransition> southTransition;
    std::optional<MapEdgeTransition> eastTransition;
    std::optional<MapEdgeTransition> westTransition;
    MapRuntimeRestrictions runtimeRestrictions = {};
    std::optional<MapArenaDefinition> arena;
    // A BLV its world declares open to the sky (world.yml openAirMaps): spells follow the outdoor rules there
    // (IGameplayWorldRuntime::isOpenAirMap). False for every other map.
    bool openAir = false;
    // Town Portal and Lloyd's Beacon fail here (world.yml noTeleportMaps). False for every other map.
    bool noTeleport = false;

    const std::optional<MapEdgeTransition> *edgeTransition(MapBoundaryEdge edge) const;
    std::optional<MapEdgeTransition> *edgeTransition(MapBoundaryEdge edge);
};

// The start decoration a party entering from the given side uses ("north start", ...); empty without a side.
std::string mapStartPointName(std::optional<MapBoundaryEdge> side);

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
    // Assigns each map without an explicit world column to the world package that ships its file
    // (pairs of world id and file name found under worlds/<world>/maps). A file shipped by two worlds is an error.
    bool applyWorldOwnership(const std::vector<std::pair<std::string, std::string>> &worldMapFiles);
    // Marks the world's maps open to the sky (world.yml openAirMaps). A name that is no BLV of that world is an error.
    bool applyOpenAirMaps(const std::string &worldId, const std::vector<std::string> &fileNames);
    // Marks the world's maps where Town Portal and Lloyd's Beacon fail (world.yml noTeleportMaps). A name that is no
    // map of that world is an error.
    bool applyNoTeleportMaps(const std::string &worldId, const std::vector<std::string> &fileNames);
    // Canonical ids that older saves used for maps whose world is now resolved differently (legacy, current).
    std::vector<std::pair<std::string, std::string>> legacyCanonicalIdRenames() const;
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
