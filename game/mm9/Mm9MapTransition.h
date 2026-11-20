#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class MapRegistry;
struct MapStatsEntry;

// The food an MM9 walk between two regions costs, whatever its days: MM6-MM8's journey between outdoor maps.
constexpr int Mm9RegionWalkFood = 5;

struct Mm9MapTransition
{
    std::string canonicalId;
    std::string sourceMapCanonicalId;
    std::string sourceMapFileName;
    uint32_t sourceObjectIndex = 0;
    std::string sourceName;
    int centerX = 0;
    int centerY = 0;
    int centerZ = 0;
    int halfExtentX = 0;
    int halfExtentY = 0;
    int halfExtentZ = 0;
    std::string destinationMapCanonicalId;
    std::string destinationMapFileName;
    std::string sourceStartPointName;
    std::string resolvedStartPointName;
    int arrivalX = 0;
    int arrivalY = 0;
    int arrivalZ = 0;
    double facingDegrees = 0.0;
    uint16_t facingYawUnits = 0;
    bool movePlayerToFloor = false;
    bool askPlayer = false;
    int travelDays = 0;
    bool sourceDefaultTravelDays = false;
    std::string loadScreen;
    std::string sourceDat;
    std::string overrideId;
    std::string provenance;
};

// An MM9 exit is a walk between two regions (Sturmford to Drangheim at the region's border) when it has days on the
// road and both maps are top-level areas in map_stats (area 0), not a dungeon inside one (the Connecting Tunnels).
bool mm9RegionWalk(
    int travelDays,
    const std::vector<MapStatsEntry> *pMapEntries,
    const std::string &sourceMapFileName,
    const std::string &destinationMapFileName);

class Mm9MapTransitionTable
{
public:
    void clear();
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows, const MapRegistry &mapRegistry);
    const Mm9MapTransition *findByCanonicalId(const std::string &canonicalId) const;
    std::vector<const Mm9MapTransition *> forSourceMapFile(const std::string &sourceMapFileName) const;
    const std::vector<Mm9MapTransition> &entries() const;
    const std::vector<std::string> &errors() const;

private:
    void addError(size_t rowNumber, const std::string &message);

    std::vector<Mm9MapTransition> m_entries;
    std::unordered_map<std::string, size_t> m_entryIndexByCanonicalId;
    std::unordered_map<std::string, std::vector<size_t>> m_entryIndicesBySourceMapFile;
    std::vector<std::string> m_errors;
};
}
