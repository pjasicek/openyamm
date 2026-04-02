#include "game/tables/MapStats.h"

#include <cctype>
#include <iostream>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t MapIdColumn = 0;
constexpr size_t NameColumn = 1;
constexpr size_t FileNameColumn = 2;
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
    if (value.empty())
    {
        result = 0;
        return true;
    }

    size_t processedCharacters = 0;

    try
    {
        result = std::stoi(value, &processedCharacters);
    }
    catch (...)
    {
        return false;
    }

    return processedCharacters == value.size();
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
}

bool MapStats::loadFromRows(const std::vector<std::vector<std::string>> &rows)
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
        entry.environmentName = getColumnValue(row, EnvironmentColumn);
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

const std::vector<MapStatsEntry> &MapStats::getEntries() const
{
    return m_entries;
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
    if (value.empty())
    {
        result = 0;
        return true;
    }

    size_t processedCharacters = 0;

    try
    {
        result = std::stoi(value, &processedCharacters);
    }
    catch (...)
    {
        return false;
    }

    return processedCharacters == value.size();
}
}
