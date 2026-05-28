#include "game/tables/MapStats.h"

#include "game/maps/MapIdentity.h"
#include "game/tables/MergedBaseTables.h"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t MapIdColumn = 0;
constexpr size_t NameColumn = 1;
constexpr size_t FileNameColumn = 2;
constexpr size_t RespawnIntervalDaysColumn = 6;
constexpr size_t PerceptionDifficultyColumn = 5;
constexpr size_t BaseStealingFineColumn = 8;
constexpr size_t DisarmDifficultyColumn = 9;
constexpr size_t TrapDamageD20DiceCountColumn = 10;
constexpr size_t NavigationMapFileNameColumn = 0;
constexpr size_t NavigationMinXColumn = 1;
constexpr size_t NavigationMaxXColumn = 2;
constexpr size_t NavigationMinYColumn = 3;
constexpr size_t NavigationMaxYColumn = 4;
constexpr size_t NavigationNorthMapColumn = 5;
constexpr size_t NavigationNorthTravelDaysColumn = 6;
constexpr size_t NavigationNorthHeadingColumn = 7;
constexpr size_t NavigationSouthMapColumn = 8;
constexpr size_t NavigationSouthTravelDaysColumn = 9;
constexpr size_t NavigationSouthHeadingColumn = 10;
constexpr size_t NavigationEastMapColumn = 11;
constexpr size_t NavigationEastTravelDaysColumn = 12;
constexpr size_t NavigationEastHeadingColumn = 13;
constexpr size_t NavigationWestMapColumn = 14;
constexpr size_t NavigationWestTravelDaysColumn = 15;
constexpr size_t NavigationWestHeadingColumn = 16;
constexpr size_t NavigationNorthArrivalXColumn = 17;
constexpr size_t NavigationNorthArrivalYColumn = 18;
constexpr size_t NavigationNorthArrivalZColumn = 19;
constexpr size_t NavigationSouthArrivalXColumn = 20;
constexpr size_t NavigationSouthArrivalYColumn = 21;
constexpr size_t NavigationSouthArrivalZColumn = 22;
constexpr size_t NavigationEastArrivalXColumn = 23;
constexpr size_t NavigationEastArrivalYColumn = 24;
constexpr size_t NavigationEastArrivalZColumn = 25;
constexpr size_t NavigationWestArrivalXColumn = 26;
constexpr size_t NavigationWestArrivalYColumn = 27;
constexpr size_t NavigationWestArrivalZColumn = 28;
constexpr size_t TreasureLevelColumn = 11;
constexpr size_t EncounterChanceColumn = 12;
constexpr size_t Encounter1ChanceColumn = 13;
constexpr size_t Encounter2ChanceColumn = 14;
constexpr size_t Encounter3ChanceColumn = 15;
constexpr size_t Encounter1PictureColumn = 16;
constexpr size_t Encounter1NameColumn = 17;
constexpr size_t Encounter1DifficultyColumn = 18;
constexpr size_t Encounter1CountColumn = 19;
constexpr size_t Encounter2PictureColumn = 20;
constexpr size_t Encounter2NameColumn = 21;
constexpr size_t Encounter2DifficultyColumn = 22;
constexpr size_t Encounter2CountColumn = 23;
constexpr size_t Encounter3PictureColumn = 24;
constexpr size_t Encounter3NameColumn = 25;
constexpr size_t Encounter3DifficultyColumn = 26;
constexpr size_t Encounter3CountColumn = 27;
constexpr size_t RedbookTrackColumn = 28;
constexpr size_t EnvironmentColumn = 29;
constexpr size_t AreaIdColumn = 32;
constexpr size_t InAreaColumn = 33;
constexpr size_t WorldIdColumn = 34;
constexpr size_t SourceMapIdColumn = 35;
constexpr size_t SourceFileNameColumn = 36;
constexpr size_t MusicTrackColumn = 37;
constexpr size_t BattleTrackColumn = 38;
constexpr size_t TravelDaysColumn = 39;
constexpr size_t Encounter4PictureColumn = 40;
constexpr size_t Encounter4NameColumn = 41;
constexpr size_t Encounter4DifficultyColumn = 42;
constexpr size_t Encounter4CountColumn = 43;
constexpr size_t SourceRedbookTrackColumn = 44;
constexpr size_t SourceAreaCodeColumn = 45;
constexpr size_t TownPortalMapIdColumn = 46;
constexpr size_t InTownColumn = 47;
constexpr int MergedOutdoorBoundsMinX = -23143;
constexpr int MergedOutdoorBoundsMaxX = 23143;
constexpr int MergedOutdoorBoundsMinY = -23143;
constexpr int MergedOutdoorBoundsMaxY = 23143;

std::string getColumnValue(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return {};
    }

    return row[index];
}

std::string trimCopy(const std::string &value)
{
    size_t start = 0;
    size_t end = value.size();

    while (start < end && std::isspace(static_cast<unsigned char>(value[start])))
    {
        ++start;
    }

    while (end > start && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return value.substr(start, end - start);
}

bool parseCountRange(const std::string &value, int &minCount, int &maxCount)
{
    const std::string trimmedValue = trimCopy(value);

    if (trimmedValue.empty())
    {
        minCount = 0;
        maxCount = 0;
        return true;
    }

    const size_t dashPosition = trimmedValue.find('-');

    if (dashPosition == std::string::npos)
    {
        try
        {
            minCount = std::stoi(trimmedValue);
            maxCount = minCount;
        }
        catch (...)
        {
            return false;
        }

        return true;
    }

    try
    {
        minCount = std::stoi(trimCopy(trimmedValue.substr(0, dashPosition)));
        maxCount = std::stoi(trimCopy(trimmedValue.substr(dashPosition + 1)));
    }
    catch (...)
    {
        return false;
    }

    return true;
}

bool parseIntegerLocal(const std::string &value, int &result)
{
    const std::string trimmedValue = trimCopy(value);

    if (trimmedValue.empty())
    {
        result = 0;
        return true;
    }

    size_t processedCharacters = 0;

    try
    {
        result = std::stoi(trimmedValue, &processedCharacters);
    }
    catch (...)
    {
        return false;
    }

    return processedCharacters == trimmedValue.size();
}

std::string lowercaseCopy(const std::string &value)
{
    std::string result = value;
    std::transform(
        result.begin(),
        result.end(),
        result.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
    return result;
}

std::vector<std::string> splitString(const std::string &value, char separator)
{
    std::vector<std::string> parts;
    std::stringstream stream(value);
    std::string part;

    while (std::getline(stream, part, separator))
    {
        parts.push_back(trimCopy(part));
    }

    return parts;
}

std::optional<MapBoundaryEdge> parseMergedOutdoorTravelSide(const std::string &value)
{
    const std::string side = lowercaseCopy(trimCopy(value));

    if (side == "up" || side == "1")
    {
        return MapBoundaryEdge::North;
    }

    if (side == "down" || side == "2")
    {
        return MapBoundaryEdge::South;
    }

    if (side == "left" || side == "3")
    {
        return MapBoundaryEdge::West;
    }

    if (side == "right" || side == "4")
    {
        return MapBoundaryEdge::East;
    }

    return std::nullopt;
}

int boundaryTravelHeadingDegrees(MapBoundaryEdge edge)
{
    switch (edge)
    {
        case MapBoundaryEdge::North:
            return 90;

        case MapBoundaryEdge::South:
            return 270;

        case MapBoundaryEdge::East:
            return 0;

        case MapBoundaryEdge::West:
            return 180;
    }

    return 0;
}

bool parseRequiredQBitsAny(const std::string &value, std::vector<uint32_t> &qbits)
{
    qbits.clear();

    for (const std::string &part : splitString(value, '|'))
    {
        if (part.empty())
        {
            continue;
        }

        int parsedQBit = 0;

        if (!parseIntegerLocal(part, parsedQBit) || parsedQBit <= 0)
        {
            return false;
        }

        qbits.push_back(static_cast<uint32_t>(parsedQBit));
    }

    return true;
}

bool applyTransitionRequirements(
    const std::string &requirements,
    MapEdgeTransition &transition,
    std::string &errorMessage)
{
    for (const std::string &part : splitString(requirements, ';'))
    {
        if (part.empty())
        {
            continue;
        }

        const size_t equalsPosition = part.find('=');

        if (equalsPosition == std::string::npos)
        {
            errorMessage = "missing '=' in transition requirement: " + part;
            return false;
        }

        const std::string key = lowercaseCopy(trimCopy(part.substr(0, equalsPosition)));
        const std::string value = trimCopy(part.substr(equalsPosition + 1));
        const std::string lowerValue = lowercaseCopy(value);

        if (key == "surface")
        {
            if (lowerValue == "land")
            {
                transition.requiredOriginSurface = MapTransitionSurfaceRequirement::Land;
            }
            else if (lowerValue == "water")
            {
                transition.requiredOriginSurface = MapTransitionSurfaceRequirement::Water;
            }
            else
            {
                errorMessage = "invalid transition surface requirement: " + value;
                return false;
            }
        }
        else if (key == "qbit" || key == "qbits")
        {
            if (!parseRequiredQBitsAny(value, transition.requiredQuestBitsAny))
            {
                errorMessage = "invalid transition qbit requirement: " + value;
                return false;
            }
        }
        else
        {
            errorMessage = "unknown transition requirement: " + key;
            return false;
        }
    }

    return true;
}

bool parseEncounterInfo(
    const std::vector<std::string> &row,
    MapEncounterInfo &encounterInfo,
    size_t chanceColumn,
    size_t pictureColumn,
    size_t nameColumn,
    size_t difficultyColumn,
    size_t countColumn
)
{
    int chance = 0;
    int difficulty = 0;
    int minCount = 0;
    int maxCount = 0;

    if (!parseIntegerLocal(getColumnValue(row, chanceColumn), chance)
        || !parseIntegerLocal(getColumnValue(row, difficultyColumn), difficulty)
        || !parseCountRange(getColumnValue(row, countColumn), minCount, maxCount))
    {
        return false;
    }

    encounterInfo.chance = chance;
    encounterInfo.pictureName = getColumnValue(row, pictureColumn);
    encounterInfo.monsterName = getColumnValue(row, nameColumn);
    encounterInfo.difficulty = difficulty;
    encounterInfo.minCount = minCount;
    encounterInfo.maxCount = maxCount;
    return true;
}

bool parseSupplementalEncounterInfo(
    const std::vector<std::string> &row,
    MapEncounterInfo &encounterInfo,
    size_t pictureColumn,
    size_t nameColumn,
    size_t difficultyColumn,
    size_t countColumn
)
{
    int difficulty = 0;
    int minCount = 0;
    int maxCount = 0;

    if (!parseIntegerLocal(getColumnValue(row, difficultyColumn), difficulty)
        || !parseCountRange(getColumnValue(row, countColumn), minCount, maxCount))
    {
        return false;
    }

    encounterInfo.chance = 0;
    encounterInfo.pictureName = getColumnValue(row, pictureColumn);
    encounterInfo.monsterName = getColumnValue(row, nameColumn);
    encounterInfo.difficulty = difficulty;
    encounterInfo.minCount = minCount;
    encounterInfo.maxCount = maxCount;
    return true;
}

std::optional<MapBoundaryEdge> parseNavigationEdgeByColumn(size_t mapColumn)
{
    switch (mapColumn)
    {
        case NavigationNorthMapColumn:
            return MapBoundaryEdge::North;

        case NavigationSouthMapColumn:
            return MapBoundaryEdge::South;

        case NavigationEastMapColumn:
            return MapBoundaryEdge::East;

        case NavigationWestMapColumn:
            return MapBoundaryEdge::West;

        default:
            return std::nullopt;
    }
}

size_t navigationTravelDaysColumn(MapBoundaryEdge edge)
{
    switch (edge)
    {
        case MapBoundaryEdge::North:
            return NavigationNorthTravelDaysColumn;

        case MapBoundaryEdge::South:
            return NavigationSouthTravelDaysColumn;

        case MapBoundaryEdge::East:
            return NavigationEastTravelDaysColumn;

        case MapBoundaryEdge::West:
            return NavigationWestTravelDaysColumn;
    }

    return NavigationNorthTravelDaysColumn;
}

size_t navigationHeadingColumn(MapBoundaryEdge edge)
{
    switch (edge)
    {
        case MapBoundaryEdge::North:
            return NavigationNorthHeadingColumn;

        case MapBoundaryEdge::South:
            return NavigationSouthHeadingColumn;

        case MapBoundaryEdge::East:
            return NavigationEastHeadingColumn;

        case MapBoundaryEdge::West:
            return NavigationWestHeadingColumn;
    }

    return NavigationNorthHeadingColumn;
}

size_t navigationArrivalXColumn(MapBoundaryEdge edge)
{
    switch (edge)
    {
        case MapBoundaryEdge::North:
            return NavigationNorthArrivalXColumn;

        case MapBoundaryEdge::South:
            return NavigationSouthArrivalXColumn;

        case MapBoundaryEdge::East:
            return NavigationEastArrivalXColumn;

        case MapBoundaryEdge::West:
            return NavigationWestArrivalXColumn;
    }

    return NavigationNorthArrivalXColumn;
}

size_t navigationArrivalYColumn(MapBoundaryEdge edge)
{
    switch (edge)
    {
        case MapBoundaryEdge::North:
            return NavigationNorthArrivalYColumn;

        case MapBoundaryEdge::South:
            return NavigationSouthArrivalYColumn;

        case MapBoundaryEdge::East:
            return NavigationEastArrivalYColumn;

        case MapBoundaryEdge::West:
            return NavigationWestArrivalYColumn;
    }

    return NavigationNorthArrivalYColumn;
}

size_t navigationArrivalZColumn(MapBoundaryEdge edge)
{
    switch (edge)
    {
        case MapBoundaryEdge::North:
            return NavigationNorthArrivalZColumn;

        case MapBoundaryEdge::South:
            return NavigationSouthArrivalZColumn;

        case MapBoundaryEdge::East:
            return NavigationEastArrivalZColumn;

        case MapBoundaryEdge::West:
            return NavigationWestArrivalZColumn;
    }

    return NavigationNorthArrivalZColumn;
}

bool applyMergedOutdoorTravelDirection(
    MapStatsEntry &entry,
    MapBoundaryEdge edge,
    const MergedOutdoorTravelDirection &direction,
    bool straightTravel)
{
    std::optional<MapEdgeTransition> *pTransition = entry.edgeTransition(edge);

    if (pTransition == nullptr)
    {
        return true;
    }

    if (direction.mapName.empty())
    {
        pTransition->reset();
        return true;
    }

    MapEdgeTransition transition = {};
    transition.destinationMapFileName = direction.mapName;
    transition.travelDays = static_cast<int>(direction.days.value_or(0));
    transition.straightTravel = straightTravel;
    transition.straightTravelSide = straightTravel ? parseMergedOutdoorTravelSide(direction.side) : std::nullopt;
    transition.useMapStartPosition = !transition.straightTravelSide.has_value();
    if (transition.straightTravelSide.has_value())
    {
        transition.directionDegrees = boundaryTravelHeadingDegrees(edge);
    }

    std::string errorMessage;

    if (!applyTransitionRequirements(direction.requirements, transition, errorMessage))
    {
        std::cerr << "merged outdoor travel row for " << entry.fileName << " has invalid requirements: "
            << errorMessage << '\n';
        return false;
    }

    *pTransition = std::move(transition);
    return true;
}
}

const std::optional<MapEdgeTransition> *MapStatsEntry::edgeTransition(MapBoundaryEdge edge) const
{
    switch (edge)
    {
        case MapBoundaryEdge::North:
            return &northTransition;

        case MapBoundaryEdge::South:
            return &southTransition;

        case MapBoundaryEdge::East:
            return &eastTransition;

        case MapBoundaryEdge::West:
            return &westTransition;
    }

    return &northTransition;
}

std::optional<MapEdgeTransition> *MapStatsEntry::edgeTransition(MapBoundaryEdge edge)
{
    switch (edge)
    {
        case MapBoundaryEdge::North:
            return &northTransition;

        case MapBoundaryEdge::South:
            return &southTransition;

        case MapBoundaryEdge::East:
            return &eastTransition;

        case MapBoundaryEdge::West:
            return &westTransition;
    }

    return &northTransition;
}

bool MapStats::loadFromRows(const std::vector<std::vector<std::string>> &rows, const std::string &worldId)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (!isDataRow(row))
        {
            continue;
        }

        MapStatsEntry entry = {};

        if (!parseInteger(row[MapIdColumn], entry.id))
        {
            std::cerr << "MapStats row has invalid map id: " << row[MapIdColumn] << '\n';
            return false;
        }

        const std::string encounterChanceValue = getColumnValue(row, EncounterChanceColumn);
        const std::string redbookTrackValue = getColumnValue(row, RedbookTrackColumn);

        if (!parseInteger(getColumnValue(row, RespawnIntervalDaysColumn), entry.respawnIntervalDays))
        {
            std::cerr << "MapStats row has invalid respawn interval for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, PerceptionDifficultyColumn), entry.perceptionDifficulty))
        {
            std::cerr << "MapStats row has invalid perception difficulty for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, BaseStealingFineColumn), entry.baseStealingFine))
        {
            std::cerr << "MapStats row has invalid base stealing fine for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, DisarmDifficultyColumn), entry.disarmDifficulty))
        {
            std::cerr << "MapStats row has invalid disarm difficulty for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, TrapDamageD20DiceCountColumn), entry.trapDamageD20DiceCount))
        {
            std::cerr << "MapStats row has invalid trap damage dice for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, TreasureLevelColumn), entry.treasureLevel))
        {
            std::cerr << "MapStats row has invalid treasure level for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(encounterChanceValue, entry.encounterChance))
        {
            std::cerr << "MapStats row has invalid encounter chance for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(redbookTrackValue, entry.redbookTrack))
        {
            std::cerr << "MapStats row has invalid redbook track for map id " << entry.id << '\n';
            return false;
        }

        if (!parseEncounterInfo(
                row,
                entry.encounter1,
                Encounter1ChanceColumn,
                Encounter1PictureColumn,
                Encounter1NameColumn,
                Encounter1DifficultyColumn,
                Encounter1CountColumn)
            || !parseEncounterInfo(
                row,
                entry.encounter2,
                Encounter2ChanceColumn,
                Encounter2PictureColumn,
                Encounter2NameColumn,
                Encounter2DifficultyColumn,
                Encounter2CountColumn)
            || !parseEncounterInfo(
                row,
                entry.encounter3,
                Encounter3ChanceColumn,
                Encounter3PictureColumn,
                Encounter3NameColumn,
                Encounter3DifficultyColumn,
                Encounter3CountColumn)
            || !parseSupplementalEncounterInfo(
                row,
                entry.encounter4,
                Encounter4PictureColumn,
                Encounter4NameColumn,
                Encounter4DifficultyColumn,
                Encounter4CountColumn))
        {
            std::cerr << "MapStats row has invalid encounter data for map id " << entry.id << '\n';
            return false;
        }

        entry.name = getColumnValue(row, NameColumn);
        entry.fileName = getColumnValue(row, FileNameColumn);
        const std::string explicitWorldId = trimCopy(getColumnValue(row, WorldIdColumn));
        entry.worldId = explicitWorldId.empty()
            ? inferWorldIdFromMapFileName(entry.fileName, worldId)
            : normalizeWorldId(explicitWorldId);
        entry.canonicalId = buildCanonicalMapId(entry.worldId, entry.fileName);
        entry.environmentName = getColumnValue(row, EnvironmentColumn);
        entry.areaId = 0;
        parseIntegerLocal(getColumnValue(row, AreaIdColumn), entry.areaId);
        entry.isTopLevelArea = !getColumnValue(row, InAreaColumn).empty();
        entry.sourceFileName = getColumnValue(row, SourceFileNameColumn);
        entry.sourceAreaCode = getColumnValue(row, SourceAreaCodeColumn);

        if (!parseInteger(getColumnValue(row, SourceMapIdColumn), entry.sourceMapId))
        {
            std::cerr << "MapStats row has invalid source map id for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, MusicTrackColumn), entry.musicTrack))
        {
            std::cerr << "MapStats row has invalid music track for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, BattleTrackColumn), entry.battleTrack))
        {
            std::cerr << "MapStats row has invalid battle track for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, TravelDaysColumn), entry.travelDays))
        {
            std::cerr << "MapStats row has invalid travel days for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, SourceRedbookTrackColumn), entry.sourceRedbookTrack))
        {
            std::cerr << "MapStats row has invalid source redbook track for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, TownPortalMapIdColumn), entry.townPortalMapId))
        {
            std::cerr << "MapStats row has invalid town portal map id for map id " << entry.id << '\n';
            return false;
        }

        if (!parseInteger(getColumnValue(row, InTownColumn), entry.inTown))
        {
            std::cerr << "MapStats row has invalid in-town flag for map id " << entry.id << '\n';
            return false;
        }

        m_entries.push_back(entry);
    }

    if (m_entries.empty())
    {
        std::cerr << "MapStats contains no typed entries.\n";
        return false;
    }

    return true;
}

bool MapStats::applyMergedBolsterMaps(const MergedBolsterMapTable &bolsterMaps)
{
    for (MapStatsEntry &entry : m_entries)
    {
        const MergedBolsterMapEntry *pBolsterMap = bolsterMaps.findById(static_cast<uint32_t>(entry.id));

        if (pBolsterMap != nullptr && pBolsterMap->continent != 0)
        {
            entry.mergedContinentId = pBolsterMap->continent;
        }
    }

    return true;
}

bool MapStats::applyOutdoorNavigationRows(const std::vector<std::vector<std::string>> &rows)
{
    for (const std::vector<std::string> &row : rows)
    {
        const std::string fileName = trimCopy(getColumnValue(row, NavigationMapFileNameColumn));

        if (fileName.empty() || fileName[0] == '/')
        {
            continue;
        }

        MapStatsEntry *pEntry = findMutableByFileName(fileName);

        if (pEntry == nullptr)
        {
            std::cerr << "Map navigation row references unknown map file: " << fileName << '\n';
            return false;
        }

        MapBounds bounds = {};
        bounds.enabled = true;

        if (!parseIntegerLocal(getColumnValue(row, NavigationMinXColumn), bounds.minX)
            || !parseIntegerLocal(getColumnValue(row, NavigationMaxXColumn), bounds.maxX)
            || !parseIntegerLocal(getColumnValue(row, NavigationMinYColumn), bounds.minY)
            || !parseIntegerLocal(getColumnValue(row, NavigationMaxYColumn), bounds.maxY))
        {
            std::cerr << "Map navigation row has invalid bounds for map file: " << fileName << '\n';
            return false;
        }

        if (bounds.minX > bounds.maxX || bounds.minY > bounds.maxY)
        {
            std::cerr << "Map navigation row has inverted bounds for map file: " << fileName << '\n';
            return false;
        }

        pEntry->outdoorBounds = bounds;

        for (size_t mapColumn : {
                 NavigationNorthMapColumn,
                 NavigationSouthMapColumn,
                 NavigationEastMapColumn,
                 NavigationWestMapColumn})
        {
            const std::optional<MapBoundaryEdge> edge = parseNavigationEdgeByColumn(mapColumn);

            if (!edge.has_value())
            {
                continue;
            }

            std::optional<MapEdgeTransition> *pTransition = pEntry->edgeTransition(*edge);

            if (pTransition == nullptr)
            {
                continue;
            }

            const std::string destinationMap = trimCopy(getColumnValue(row, mapColumn));

            if (destinationMap.empty() || destinationMap == "0")
            {
                pTransition->reset();
                continue;
            }

            MapEdgeTransition transition = {};
            transition.destinationMapFileName = destinationMap;

            int travelDays = 0;

            if (!parseIntegerLocal(getColumnValue(row, navigationTravelDaysColumn(*edge)), travelDays))
            {
                std::cerr << "Map navigation row has invalid travel days for map file: " << fileName << '\n';
                return false;
            }

            transition.travelDays = std::max(0, travelDays);
            const std::string headingValue = trimCopy(getColumnValue(row, navigationHeadingColumn(*edge)));

            if (!headingValue.empty() && headingValue != "0")
            {
                int directionDegrees = 0;

                if (!parseIntegerLocal(headingValue, directionDegrees))
                {
                    std::cerr << "Map navigation row has invalid heading for map file: " << fileName << '\n';
                    return false;
                }

                transition.directionDegrees = directionDegrees;
            }

            const std::string arrivalXValue = trimCopy(getColumnValue(row, navigationArrivalXColumn(*edge)));
            const std::string arrivalYValue = trimCopy(getColumnValue(row, navigationArrivalYColumn(*edge)));
            const std::string arrivalZValue = trimCopy(getColumnValue(row, navigationArrivalZColumn(*edge)));
            const bool hasExplicitArrivalPosition =
                !arrivalXValue.empty() || !arrivalYValue.empty() || !arrivalZValue.empty();

            if (hasExplicitArrivalPosition)
            {
                int arrivalX = 0;
                int arrivalY = 0;
                int arrivalZ = 0;

                if (!parseIntegerLocal(arrivalXValue, arrivalX)
                    || !parseIntegerLocal(arrivalYValue, arrivalY)
                    || !parseIntegerLocal(arrivalZValue, arrivalZ))
                {
                    std::cerr << "Map navigation row has invalid arrival position for map file: " << fileName << '\n';
                    return false;
                }

                transition.arrivalX = arrivalX;
                transition.arrivalY = arrivalY;
                transition.arrivalZ = arrivalZ;
                transition.useMapStartPosition = false;
            }

            *pTransition = std::move(transition);
        }
    }

    return true;
}

bool MapStats::applyMergedOutdoorTravels(const MergedOutdoorTravelTable &outdoorTravels)
{
    for (const MergedOutdoorTravelEntry &outdoorTravel : outdoorTravels.entries())
    {
        MapStatsEntry *pEntry = findMutableByFileName(outdoorTravel.keyMap);

        if (pEntry == nullptr)
        {
            std::cerr << "merged outdoor travel row references unknown map file: " << outdoorTravel.keyMap << '\n';
            return false;
        }

        MapBounds bounds = {};
        bounds.enabled = true;
        bounds.minX = MergedOutdoorBoundsMinX;
        bounds.maxX = MergedOutdoorBoundsMaxX;
        bounds.minY = MergedOutdoorBoundsMinY;
        bounds.maxY = MergedOutdoorBoundsMaxY;
        pEntry->outdoorBounds = bounds;

        if (!applyMergedOutdoorTravelDirection(
                *pEntry,
                MapBoundaryEdge::North,
                outdoorTravel.up,
                outdoorTravel.straightTravel)
            || !applyMergedOutdoorTravelDirection(
                *pEntry,
                MapBoundaryEdge::South,
                outdoorTravel.down,
                outdoorTravel.straightTravel)
            || !applyMergedOutdoorTravelDirection(
                *pEntry,
                MapBoundaryEdge::West,
                outdoorTravel.left,
                outdoorTravel.straightTravel)
            || !applyMergedOutdoorTravelDirection(
                *pEntry,
                MapBoundaryEdge::East,
                outdoorTravel.right,
                outdoorTravel.straightTravel))
        {
            return false;
        }
    }

    return true;
}

const std::vector<MapStatsEntry> &MapStats::getEntries() const
{
    return m_entries;
}

const MapStatsEntry *MapStats::findById(uint32_t id) const
{
    for (const MapStatsEntry &entry : m_entries)
    {
        if (entry.id >= 0 && static_cast<uint32_t>(entry.id) == id)
        {
            return &entry;
        }
    }

    return nullptr;
}

const MapStatsEntry *MapStats::findByFileName(const std::string &fileName) const
{
    const std::string normalizedFileName = normalizeFileName(fileName);

    for (const MapStatsEntry &entry : m_entries)
    {
        if (normalizeFileName(entry.fileName) == normalizedFileName)
        {
            return &entry;
        }
    }

    return nullptr;
}

bool MapStats::isDataRow(const std::vector<std::string> &row)
{
    if (row.empty() || row.front().empty())
    {
        return false;
    }

    for (const char character : row.front())
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return false;
        }
    }

    return true;
}

bool MapStats::parseInteger(const std::string &value, int &result)
{
    const std::string trimmedValue = trimCopy(value);

    if (trimmedValue.empty())
    {
        result = 0;
        return true;
    }

    size_t processedCharacters = 0;

    try
    {
        result = std::stoi(trimmedValue, &processedCharacters);
    }
    catch (...)
    {
        return false;
    }

    return processedCharacters == trimmedValue.size();
}

std::string MapStats::normalizeFileName(const std::string &value)
{
    std::string result = trimCopy(value);

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

MapStatsEntry *MapStats::findMutableByFileName(const std::string &fileName)
{
    const std::string normalizedFileName = normalizeFileName(fileName);

    for (MapStatsEntry &entry : m_entries)
    {
        if (normalizeFileName(entry.fileName) == normalizedFileName)
        {
            return &entry;
        }
    }

    return nullptr;
}
}
