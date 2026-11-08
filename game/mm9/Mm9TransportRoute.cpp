#include "game/mm9/Mm9TransportRoute.h"

#include "game/maps/MapRegistry.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/party/Party.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <limits>
#include <optional>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t ExpectedColumnCount = 31;
constexpr float MinutesPerDay = 24.0f * 60.0f;
constexpr std::array<const char *, 7> DayNames = {
    "Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
};

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

bool parseFloat(const std::string &value, float &result)
{
    double parsed = 0.0;
    if (!parseDouble(value, parsed) || parsed < -std::numeric_limits<float>::max()
        || parsed > std::numeric_limits<float>::max())
    {
        return false;
    }
    result = static_cast<float>(parsed);
    return true;
}

bool parseBoolean(const std::string &value, bool &result)
{
    if (value == "0" || value == "1")
    {
        result = value == "1";
        return true;
    }
    return false;
}

bool parseRawKeys(const std::string &value, std::vector<int32_t> &result)
{
    result.clear();
    size_t begin = 0;
    while (begin < value.size())
    {
        const size_t end = value.find('|', begin);
        const std::string token = value.substr(begin, end == std::string::npos ? end : end - begin);
        int rawKey = 0;
        if (!parseInteger(token, rawKey) || rawKey <= 0 || rawKey > Mm9QuestKeyRawIdMaximum
            || std::find(result.begin(), result.end(), rawKey) != result.end())
        {
            return false;
        }
        result.push_back(rawKey);
        if (end == std::string::npos)
        {
            break;
        }
        begin = end + 1;
    }
    return true;
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

uint64_t serviceDayKey(uint32_t rudeId, uint8_t sourceDayIndex)
{
    return (static_cast<uint64_t>(rudeId) << 8) | sourceDayIndex;
}
}

void Mm9TransportRouteTable::clear()
{
    m_entries.clear();
    m_entryIndexByCanonicalId.clear();
    m_entryIndicesByService.clear();
    m_entryIndexByServiceDay.clear();
    m_errors.clear();
}

bool Mm9TransportRouteTable::loadFromRows(
    const std::vector<std::vector<std::string>> &rows,
    const MapRegistry &mapRegistry,
    const Mm9RudeDialogueTable &rudeDialogueTable)
{
    clear();
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
            addError(rowNumber, "expected 31 columns");
            continue;
        }

        Mm9TransportRoute entry = {};
        entry.canonicalId = row[0];
        entry.dockName = row[3];
        entry.serviceClassification = row[4];
        entry.destinationName = row[7];
        entry.destinationMapCanonicalId = row[8];
        entry.destinationMapFileName = row[9];
        entry.destinationStartPoint = row[10];
        entry.availableWeekday = row[17];
        entry.sourceShop = row[25];
        entry.sourceRude = row[26];
        entry.scheduleSource = row[27];
        entry.executableRva = row[28];
        entry.reviewState = row[29];
        entry.provenance = row[30];

        int dockNpcId = 0;
        int shopId = 0;
        int sourceRudeRowIndex = 0;
        int sourceLine = 0;
        int facingYawUnits = 0;
        int sourceDayIndex = 0;
        int travelDays = 0;
        int basePrice = 0;
        int routeOrder = 0;
        const bool valid = parseInteger(row[1], dockNpcId)
            && parseInteger(row[2], shopId)
            && parseInteger(row[5], sourceRudeRowIndex)
            && parseInteger(row[6], sourceLine)
            && parseInteger(row[11], entry.arrivalX)
            && parseInteger(row[12], entry.arrivalY)
            && parseInteger(row[13], entry.arrivalZ)
            && parseDouble(row[14], entry.facingDegrees)
            && parseInteger(row[15], facingYawUnits)
            && parseBoolean(row[16], entry.movePlayerToFloor)
            && parseInteger(row[18], sourceDayIndex)
            && parseInteger(row[19], travelDays)
            && parseInteger(row[20], basePrice)
            && parseFloat(row[21], entry.priceMultiplier)
            && parseRawKeys(row[22], entry.requiredRawKeys)
            && parseRawKeys(row[23], entry.forbiddenRawKeys)
            && parseInteger(row[24], routeOrder);
        if (!valid || dockNpcId <= 0 || shopId <= 0 || sourceRudeRowIndex < 0 || sourceLine <= 0
            || facingYawUnits < 0 || facingYawUnits >= 2048 || sourceDayIndex < 0 || sourceDayIndex >= 7
            || travelDays <= 0 || basePrice <= 0 || entry.priceMultiplier <= 0.0f || routeOrder < 0)
        {
            addError(rowNumber, "invalid numeric, boolean, or raw-key field");
            continue;
        }
        entry.dockNpcId = static_cast<uint32_t>(dockNpcId);
        entry.shopId = static_cast<uint32_t>(shopId);
        entry.sourceRudeRowIndex = static_cast<size_t>(sourceRudeRowIndex);
        entry.sourceLine = static_cast<size_t>(sourceLine);
        entry.facingYawUnits = static_cast<uint16_t>(facingYawUnits);
        entry.sourceDayIndex = static_cast<uint8_t>(sourceDayIndex);
        entry.travelDays = static_cast<uint32_t>(travelDays);
        entry.basePrice = static_cast<uint32_t>(basePrice);
        entry.routeOrder = static_cast<uint32_t>(routeOrder);

        if (!entry.canonicalId.starts_with("mm9:transport/") || entry.dockName.empty()
            || (entry.serviceClassification != "dock" && entry.serviceClassification != "special_passage")
            || entry.destinationName.empty() || entry.destinationStartPoint.empty() || entry.sourceShop.empty()
            || entry.sourceRude.empty() || entry.executableRva.empty() || entry.reviewState != "executable_backed"
            || entry.provenance.empty() || entry.availableWeekday != DayNames[entry.sourceDayIndex])
        {
            addError(rowNumber, "invalid route identity, weekday, classification, or provenance");
            continue;
        }
        if (!mapReferenceMatches(mapRegistry, entry.destinationMapCanonicalId, entry.destinationMapFileName))
        {
            addError(rowNumber, "destination map reference is unresolved or inconsistent");
            continue;
        }

        const Mm9RudeRow *pRudeRow = rudeDialogueTable.rowByIndex(entry.dockNpcId, entry.sourceRudeRowIndex);
        const auto routeContainsAll = [](const std::vector<int32_t> &routeKeys, const std::vector<int32_t> &rudeKeys)
        {
            return std::all_of(rudeKeys.begin(), rudeKeys.end(), [&routeKeys](int32_t key)
            {
                return std::find(routeKeys.begin(), routeKeys.end(), key) != routeKeys.end();
            });
        };
        if (pRudeRow == nullptr || pRudeRow->next != -5 || pRudeRow->sourceLine != entry.sourceLine
            || !routeContainsAll(entry.requiredRawKeys, pRudeRow->requiredRawKeys)
            || !routeContainsAll(entry.forbiddenRawKeys, pRudeRow->forbiddenRawKeys))
        {
            addError(rowNumber, "source RUDE -5 row or condition provenance does not match");
            continue;
        }

        const std::string normalizedId = lowerCopy(entry.canonicalId);
        const uint64_t owner = serviceDayKey(entry.dockNpcId, entry.sourceDayIndex);
        if (m_entryIndexByCanonicalId.contains(normalizedId))
        {
            addError(rowNumber, "duplicate canonical route id");
            continue;
        }
        if (m_entryIndexByServiceDay.contains(owner))
        {
            addError(rowNumber, "duplicate service weekday ownership");
            continue;
        }

        const size_t entryIndex = m_entries.size();
        m_entries.push_back(std::move(entry));
        m_entryIndexByCanonicalId[normalizedId] = entryIndex;
        m_entryIndicesByService[m_entries.back().dockNpcId].push_back(entryIndex);
        m_entryIndexByServiceDay[owner] = entryIndex;
    }

    for (std::pair<const uint32_t, std::vector<size_t>> &serviceRoutes : m_entryIndicesByService)
    {
        std::vector<size_t> &indices = serviceRoutes.second;
        std::sort(indices.begin(), indices.end(), [this](size_t left, size_t right)
        {
            return m_entries[left].routeOrder < m_entries[right].routeOrder;
        });
    }
    return !m_entries.empty() && m_errors.empty();
}

const Mm9TransportRoute *Mm9TransportRouteTable::findByCanonicalId(const std::string &canonicalId) const
{
    const auto iterator = m_entryIndexByCanonicalId.find(lowerCopy(canonicalId));
    return iterator != m_entryIndexByCanonicalId.end() ? &m_entries[iterator->second] : nullptr;
}

const Mm9TransportRoute *Mm9TransportRouteTable::findForServiceDay(
    uint32_t rudeId,
    uint8_t sourceDayIndex) const
{
    const auto iterator = m_entryIndexByServiceDay.find(serviceDayKey(rudeId, sourceDayIndex));
    return iterator != m_entryIndexByServiceDay.end() ? &m_entries[iterator->second] : nullptr;
}

std::vector<const Mm9TransportRoute *> Mm9TransportRouteTable::forService(uint32_t rudeId) const
{
    std::vector<const Mm9TransportRoute *> result;
    const auto iterator = m_entryIndicesByService.find(rudeId);
    if (iterator == m_entryIndicesByService.end())
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

const std::vector<Mm9TransportRoute> &Mm9TransportRouteTable::entries() const
{
    return m_entries;
}

const std::vector<std::string> &Mm9TransportRouteTable::errors() const
{
    return m_errors;
}

void Mm9TransportRouteTable::addError(size_t rowNumber, const std::string &message)
{
    m_errors.push_back("row " + std::to_string(rowNumber) + ": " + message);
}

uint8_t mm9TransportDayIndex(float gameMinutes)
{
    int weekday = static_cast<int>(std::floor(gameMinutes / MinutesPerDay)) % 7;
    if (weekday < 0)
    {
        weekday += 7;
    }
    // DayNames: Monday is MM9's day 2.
    return static_cast<uint8_t>((weekday + 2) % 7);
}

int mm9TransportWeekday(const Mm9TransportRoute &route)
{
    return (int(route.sourceDayIndex) + 5) % 7;
}

bool mm9TransportRouteConditionsSatisfied(const Mm9TransportRoute &route, const Party &party)
{
    for (int32_t rawKey : route.requiredRawKeys)
    {
        const std::optional<uint32_t> qbit = mm9QBitForRawQuestKey(rawKey);
        if (!qbit.has_value() || !party.hasQuestBit(*qbit))
        {
            return false;
        }
    }
    for (int32_t rawKey : route.forbiddenRawKeys)
    {
        const std::optional<uint32_t> qbit = mm9QBitForRawQuestKey(rawKey);
        if (!qbit.has_value() || party.hasQuestBit(*qbit))
        {
            return false;
        }
    }
    return true;
}
}
