#include "game/tables/JournalQuestTable.h"

#include "game/party/Party.h"

#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <set>

namespace OpenYAMM::Game
{
namespace
{
std::string getCell(const std::vector<std::string> &row, size_t index)
{
    return index < row.size() ? row[index] : "";
}

bool parseQBitList(
    const std::string &text,
    std::vector<uint32_t> &qbitIds,
    size_t rowIndex,
    const char *pColumnName)
{
    size_t tokenBegin = 0;

    while (tokenBegin < text.size())
    {
        while (tokenBegin < text.size()
            && (text[tokenBegin] == ' ' || text[tokenBegin] == ',' || text[tokenBegin] == ';'))
        {
            ++tokenBegin;
        }

        if (tokenBegin >= text.size())
        {
            break;
        }

        size_t tokenEnd = tokenBegin;
        while (tokenEnd < text.size() && text[tokenEnd] != ',' && text[tokenEnd] != ';')
        {
            ++tokenEnd;
        }

        size_t trimmedEnd = tokenEnd;
        while (trimmedEnd > tokenBegin && text[trimmedEnd - 1] == ' ')
        {
            --trimmedEnd;
        }

        const std::string token = text.substr(tokenBegin, trimmedEnd - tokenBegin);
        char *pEnd = nullptr;
        const unsigned long parsedValue = std::strtoul(token.c_str(), &pEnd, 10);

        if (token.empty()
            || pEnd == token.c_str()
            || *pEnd != '\0'
            || parsedValue == 0
            || parsedValue > std::numeric_limits<uint32_t>::max())
        {
            std::cerr << "Invalid " << pColumnName << " QBit at quests.txt row " << (rowIndex + 1)
                      << ": " << token << '\n';
            return false;
        }

        const uint32_t qbitId = static_cast<uint32_t>(parsedValue);
        if (std::find(qbitIds.begin(), qbitIds.end(), qbitId) == qbitIds.end())
        {
            qbitIds.push_back(qbitId);
        }

        tokenBegin = tokenEnd + 1;
    }

    return true;
}
}

bool JournalQuestTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    std::set<uint32_t> seenQBitIds;
    bool hasValidationError = false;

    for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.empty() || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }

        char *pEnd = nullptr;
        const unsigned long parsedId = std::strtoul(row[0].c_str(), &pEnd, 10);

        if (pEnd == row[0].c_str() || *pEnd != '\0')
        {
            if (row[0] != "Q Bit")
            {
                std::cerr << "Invalid quests.txt QBit id at row " << (rowIndex + 1) << ": " << row[0] << '\n';
                hasValidationError = true;
            }

            continue;
        }

        if (parsedId > std::numeric_limits<uint32_t>::max())
        {
            std::cerr << "Out-of-range quests.txt QBit id at row " << (rowIndex + 1) << ": " << row[0] << '\n';
            hasValidationError = true;
            continue;
        }

        const uint32_t qbitId = static_cast<uint32_t>(parsedId);

        if (!seenQBitIds.insert(qbitId).second)
        {
            std::cerr << "Duplicate quests.txt QBit id at row " << (rowIndex + 1) << ": " << qbitId << '\n';
            hasValidationError = true;
        }

        JournalQuestEntry entry = {};
        entry.qbitId = qbitId;
        entry.text = getCell(row, 1);
        entry.notes = getCell(row, 2);
        entry.owner = getCell(row, 3);
        entry.usesExplicitConditions = row.size() >= 6;

        if (entry.usesExplicitConditions
            && (!parseQBitList(getCell(row, 4), entry.requiredQBitIds, rowIndex, "required")
                || !parseQBitList(getCell(row, 5), entry.forbiddenQBitIds, rowIndex, "forbidden")))
        {
            hasValidationError = true;
            continue;
        }

        if (entry.text.empty())
        {
            continue;
        }

        m_entries.push_back(std::move(entry));
    }

    if (hasValidationError)
    {
        m_entries.clear();
        return false;
    }

    std::sort(
        m_entries.begin(),
        m_entries.end(),
        [](const JournalQuestEntry &left, const JournalQuestEntry &right)
        {
            return left.qbitId < right.qbitId;
        });

    return !m_entries.empty();
}

const std::vector<JournalQuestEntry> &JournalQuestTable::entries() const
{
    return m_entries;
}

bool JournalQuestTable::hasQuestText(uint32_t qbitId) const
{
    const std::vector<JournalQuestEntry>::const_iterator iterator = std::lower_bound(
        m_entries.begin(),
        m_entries.end(),
        qbitId,
        [](const JournalQuestEntry &entry, uint32_t value)
        {
            return entry.qbitId < value;
        });

    return iterator != m_entries.end() && iterator->qbitId == qbitId && !iterator->text.empty();
}

bool JournalQuestTable::isVisible(const JournalQuestEntry &entry, const Party &party) const
{
    if (!entry.usesExplicitConditions)
    {
        return party.campaign().hasQuestBit(entry.qbitId);
    }

    for (uint32_t qbitId : entry.requiredQBitIds)
    {
        if (!party.campaign().hasQuestBit(qbitId))
        {
            return false;
        }
    }

    for (uint32_t qbitId : entry.forbiddenQBitIds)
    {
        if (party.campaign().hasQuestBit(qbitId))
        {
            return false;
        }
    }

    return true;
}

bool JournalQuestTable::qbitChangeRevealsQuest(
    uint32_t qbitId,
    bool wasSet,
    bool isSet,
    const Party &party) const
{
    if (wasSet == isSet)
    {
        return false;
    }

    for (const JournalQuestEntry &entry : m_entries)
    {
        if (!entry.usesExplicitConditions)
        {
            if (!wasSet && isSet && entry.qbitId == qbitId)
            {
                return true;
            }
            continue;
        }

        const std::vector<uint32_t> &revealingConditions = isSet
            ? entry.requiredQBitIds
            : entry.forbiddenQBitIds;
        if (std::find(revealingConditions.begin(), revealingConditions.end(), qbitId)
                != revealingConditions.end()
            && isVisible(entry, party))
        {
            return true;
        }
    }

    return false;
}
}
