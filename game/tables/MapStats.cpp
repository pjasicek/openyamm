#include "game/tables/MapStats.h"

#include "game/maps/MapIdentity.h"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t MapIdColumn = 0;
constexpr size_t NameColumn = 1;
constexpr size_t FileNameColumn = 2;
constexpr size_t PerceptionDifficultyColumn = 5;
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

        if (!parseInteger(getColumnValue(row, PerceptionDifficultyColumn), entry.perceptionDifficulty))
        {
            std::cerr << "MapStats row has invalid perception difficulty for map id " << entry.id << '\n';
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
                Encounter3CountColumn))
        {
            std::cerr << "MapStats row has invalid encounter data for map id " << entry.id << '\n';
            return false;
        }

        entry.name = getColumnValue(row, NameColumn);
        entry.fileName = getColumnValue(row, FileNameColumn);
        entry.worldId = normalizeWorldId(worldId);
        entry.canonicalId = buildCanonicalMapId(entry.worldId, entry.fileName);
        entry.environmentName = getColumnValue(row, EnvironmentColumn);
        entry.areaId = 0;
        parseIntegerLocal(getColumnValue(row, AreaIdColumn), entry.areaId);
        entry.isTopLevelArea = !getColumnValue(row, InAreaColumn).empty();

        m_entries.push_back(entry);
    }

    if (m_entries.empty())
    {
        std::cerr << "MapStats contains no typed entries.\n";
        return false;
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

const std::vector<MapStatsEntry> &MapStats::getEntries() const
{
    return m_entries;
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
