#include "game/mm9/Mm9MapTransition.h"

#include "game/maps/MapRegistry.h"
#include "game/tables/MapStats.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <limits>
#include <optional>
#include <string>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t ExpectedColumnCount = 29;

std::string lowerCopy(const std::string &value)
{
    std::string result = value;
    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }
    return result;
}

bool parseInteger(const std::string &value, int &result)
{
    try
    {
        size_t consumed = 0;
        const long parsed = std::stol(value, &consumed);
        if (consumed != value.size() || parsed < std::numeric_limits<int>::min()
            || parsed > std::numeric_limits<int>::max())
        {
            return false;
        }
        result = static_cast<int>(parsed);
        return true;
    }
    catch (...)
    {
        return false;
    }
}

bool parseDouble(const std::string &value, double &result)
{
    try
    {
        size_t consumed = 0;
        result = std::stod(value, &consumed);
        return consumed == value.size() && std::isfinite(result);
    }
    catch (...)
    {
        return false;
    }
}

bool parseBoolean(const std::string &value, bool &result)
{
    if (value == "0")
    {
        result = false;
        return true;
    }
    if (value == "1")
    {
        result = true;
        return true;
    }
    return false;
}

bool mapReferenceMatches(
    const MapRegistry &mapRegistry,
    const std::string &canonicalId,
    const std::string &fileName)
{
    const std::optional<MapStatsEntry> byCanonicalId = mapRegistry.findByCanonicalId(canonicalId);
    const std::optional<MapStatsEntry> byFileName = mapRegistry.findByFileName(fileName);
    return byCanonicalId.has_value() && byFileName.has_value()
        && lowerCopy(byCanonicalId->fileName) == lowerCopy(fileName)
        && lowerCopy(byFileName->canonicalId) == lowerCopy(canonicalId);
}
}

void Mm9MapTransitionTable::clear()
{
    m_entries.clear();
    m_entryIndexByCanonicalId.clear();
    m_entryIndicesBySourceMapFile.clear();
    m_errors.clear();
}

bool Mm9MapTransitionTable::loadFromRows(
    const std::vector<std::vector<std::string>> &rows,
    const MapRegistry &mapRegistry)
{
    clear();
    std::unordered_set<std::string> sourceOwners;

    for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];
        if (row.empty() || row[0].empty() || row[0] == "CanonicalId")
        {
            continue;
        }
        const size_t rowNumber = rowIndex + 1;
        if (row.size() < ExpectedColumnCount)
        {
            addError(rowNumber, "expected 29 columns");
            continue;
        }

        Mm9MapTransition entry = {};
        entry.canonicalId = row[0];
        entry.sourceMapCanonicalId = row[1];
        entry.sourceMapFileName = row[2];
        entry.sourceName = row[4];
        entry.destinationMapCanonicalId = row[12];
        entry.destinationMapFileName = row[13];
        entry.sourceStartPointName = row[14];
        entry.resolvedStartPointName = row[15];
        entry.loadScreen = row[25];
        entry.sourceDat = row[26];
        entry.overrideId = row[27];
        entry.provenance = row[28];

        int sourceObjectIndex = 0;
        int facingYawUnits = 0;
        bool valid = parseInteger(row[3], sourceObjectIndex)
            && parseInteger(row[6], entry.centerX)
            && parseInteger(row[7], entry.centerY)
            && parseInteger(row[8], entry.centerZ)
            && parseInteger(row[9], entry.halfExtentX)
            && parseInteger(row[10], entry.halfExtentY)
            && parseInteger(row[11], entry.halfExtentZ)
            && parseInteger(row[16], entry.arrivalX)
            && parseInteger(row[17], entry.arrivalY)
            && parseInteger(row[18], entry.arrivalZ)
            && parseDouble(row[19], entry.facingDegrees)
            && parseInteger(row[20], facingYawUnits)
            && parseBoolean(row[21], entry.movePlayerToFloor)
            && parseBoolean(row[22], entry.askPlayer)
            && parseInteger(row[23], entry.travelDays);
        if (!valid || sourceObjectIndex < 0 || facingYawUnits < 0 || facingYawUnits >= 2048)
        {
            addError(rowNumber, "invalid numeric or boolean field");
            continue;
        }
        entry.sourceObjectIndex = static_cast<uint32_t>(sourceObjectIndex);
        entry.facingYawUnits = static_cast<uint16_t>(facingYawUnits);

        if (!entry.canonicalId.starts_with("mm9:transition/") || row[5] != "ExitTrigger"
            || entry.sourceName.empty() || entry.sourceStartPointName.empty()
            || entry.resolvedStartPointName.empty() || entry.sourceDat.empty() || entry.provenance.empty())
        {
            addError(rowNumber, "invalid transition identity or provenance");
            continue;
        }
        if (entry.halfExtentX <= 0 || entry.halfExtentY <= 0 || entry.halfExtentZ <= 0)
        {
            addError(rowNumber, "transition volume must have positive half extents");
            continue;
        }
        if (entry.travelDays < -1 || (entry.travelDays == -1) != (row[24] == "source_default"))
        {
            addError(rowNumber, "invalid TravelDays value or sentinel");
            continue;
        }
        entry.sourceDefaultTravelDays = entry.travelDays == -1;
        if (!mapReferenceMatches(mapRegistry, entry.sourceMapCanonicalId, entry.sourceMapFileName)
            || !mapReferenceMatches(mapRegistry, entry.destinationMapCanonicalId, entry.destinationMapFileName))
        {
            addError(rowNumber, "source or destination map reference is unresolved or inconsistent");
            continue;
        }

        const std::string normalizedId = lowerCopy(entry.canonicalId);
        const std::string sourceOwner = lowerCopy(entry.sourceMapCanonicalId)
            + "#" + std::to_string(entry.sourceObjectIndex);
        if (m_entryIndexByCanonicalId.contains(normalizedId))
        {
            addError(rowNumber, "duplicate canonical transition id");
            continue;
        }
        if (!sourceOwners.insert(sourceOwner).second)
        {
            addError(rowNumber, "duplicate source object ownership");
            continue;
        }

        const size_t entryIndex = m_entries.size();
        m_entries.push_back(std::move(entry));
        m_entryIndexByCanonicalId[normalizedId] = entryIndex;
        m_entryIndicesBySourceMapFile[lowerCopy(m_entries.back().sourceMapFileName)].push_back(entryIndex);
    }

    return !m_entries.empty() && m_errors.empty();
}

const Mm9MapTransition *Mm9MapTransitionTable::findByCanonicalId(const std::string &canonicalId) const
{
    const auto iterator = m_entryIndexByCanonicalId.find(lowerCopy(canonicalId));
    return iterator != m_entryIndexByCanonicalId.end() ? &m_entries[iterator->second] : nullptr;
}

std::vector<const Mm9MapTransition *> Mm9MapTransitionTable::forSourceMapFile(
    const std::string &sourceMapFileName) const
{
    std::vector<const Mm9MapTransition *> result;
    const auto iterator = m_entryIndicesBySourceMapFile.find(lowerCopy(sourceMapFileName));
    if (iterator == m_entryIndicesBySourceMapFile.end())
    {
        return result;
    }
    result.reserve(iterator->second.size());
    for (size_t entryIndex : iterator->second)
    {
        result.push_back(&m_entries[entryIndex]);
    }
    return result;
}

const std::vector<Mm9MapTransition> &Mm9MapTransitionTable::entries() const
{
    return m_entries;
}

const std::vector<std::string> &Mm9MapTransitionTable::errors() const
{
    return m_errors;
}

void Mm9MapTransitionTable::addError(size_t rowNumber, const std::string &message)
{
    m_errors.push_back("row " + std::to_string(rowNumber) + ": " + message);
}

bool mm9RegionWalk(
    int travelDays,
    const std::vector<MapStatsEntry> *pMapEntries,
    const std::string &sourceMapFileName,
    const std::string &destinationMapFileName)
{
    if (travelDays <= 0 || pMapEntries == nullptr)
    {
        return false;
    }

    const auto isTopLevelArea = [pMapEntries](const std::string &mapFileName)
    {
        const std::string fileName = lowerCopy(mapFileName);
        for (const MapStatsEntry &entry : *pMapEntries)
        {
            if (lowerCopy(entry.fileName) == fileName)
            {
                return entry.areaId == 0;
            }
        }
        return false;
    };
    return isTopLevelArea(sourceMapFileName) && isTopLevelArea(destinationMapFileName);
}
}
