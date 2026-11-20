#include "game/tables/AwardTable.h"

#include <cstdlib>
#include <iostream>
#include <limits>
#include <set>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
std::string getCell(const std::vector<std::string> &row, size_t index)
{
    return index < row.size() ? row[index] : "";
}

bool parseUnsigned(const std::string &value, uint32_t &result)
{
    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(value.c_str(), &pEnd, 10);

    if (value.empty() || pEnd == value.c_str() || *pEnd != '\0' || parsed == 0 ||
        parsed > std::numeric_limits<uint32_t>::max())
    {
        return false;
    }

    result = static_cast<uint32_t>(parsed);
    return true;
}

bool parseInt(const std::string &value, int &result)
{
    char *pEnd = nullptr;
    const long parsed = std::strtol(value.c_str(), &pEnd, 10);

    if (value.empty() || pEnd == value.c_str() || *pEnd != '\0' || parsed < std::numeric_limits<int>::min() ||
        parsed > std::numeric_limits<int>::max())
    {
        return false;
    }

    result = static_cast<int>(parsed);
    return true;
}

bool parseStateKind(const std::string &value, AwardStateKind &result)
{
    if (value == "character_award")
    {
        result = AwardStateKind::CharacterAward;
        return true;
    }

    if (value == "party_qbit")
    {
        result = AwardStateKind::PartyQBit;
        return true;
    }

    if (value == "party_autonote")
    {
        result = AwardStateKind::PartyAutonote;
        return true;
    }

    if (value == "party_arcomage_win")
    {
        result = AwardStateKind::PartyArcomageWin;
        return true;
    }

    return false;
}
} // namespace

bool AwardTable::loadFromRows(const std::vector<std::vector<std::string>> &awardRows,
                              const std::vector<std::vector<std::string>> &aliasRows)
{
    m_entries.clear();
    std::set<std::string> keys;
    bool hasValidationError = false;

    for (size_t rowIndex = 0; rowIndex < awardRows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = awardRows[rowIndex];

        if (row.empty() || row[0].empty() || row[0][0] == '#' || row[0] == "A Bit")
        {
            continue;
        }

        uint32_t awardId = 0;
        int priority = 0;

        if (!parseUnsigned(row[0], awardId) || getCell(row, 1).empty() || !parseInt(getCell(row, 2), priority))
        {
            std::cerr << "Invalid awards.txt row " << (rowIndex + 1) << '\n';
            hasValidationError = true;
            continue;
        }

        AwardDisplayEntry entry = {};
        entry.key = "award." + std::to_string(awardId);
        entry.stateKind = AwardStateKind::CharacterAward;
        entry.stateId = awardId;
        entry.text = getCell(row, 1);
        entry.priority = priority;

        if (!keys.insert(entry.key).second)
        {
            std::cerr << "Duplicate award key at awards.txt row " << (rowIndex + 1) << '\n';
            hasValidationError = true;
            continue;
        }

        m_entries.push_back(std::move(entry));
    }

    for (size_t rowIndex = 0; rowIndex < aliasRows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = aliasRows[rowIndex];

        if (row.empty() || row[0].empty() || row[0][0] == '#' || row[0] == "Key")
        {
            continue;
        }

        AwardDisplayEntry entry = {};
        entry.key = row[0];

        if (!keys.insert(entry.key).second || !parseStateKind(getCell(row, 1), entry.stateKind) ||
            !parseUnsigned(getCell(row, 2), entry.stateId) || getCell(row, 3).empty() ||
            !parseInt(getCell(row, 4), entry.priority))
        {
            std::cerr << "Invalid award_display_aliases.txt row " << (rowIndex + 1) << '\n';
            hasValidationError = true;
            continue;
        }

        entry.text = getCell(row, 3);
        m_entries.push_back(std::move(entry));
    }

    if (hasValidationError || m_entries.empty())
    {
        m_entries.clear();
        return false;
    }

    return true;
}

const std::vector<AwardDisplayEntry> &AwardTable::entries() const
{
    return m_entries;
}
} // namespace OpenYAMM::Game
