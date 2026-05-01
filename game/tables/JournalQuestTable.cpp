#include "game/tables/JournalQuestTable.h"

#include <algorithm>
#include <cstdlib>

namespace OpenYAMM::Game
{
namespace
{
std::string getCell(const std::vector<std::string> &row, size_t index)
{
    return index < row.size() ? row[index] : "";
}
}

bool JournalQuestTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty() || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }

        char *pEnd = nullptr;
        const unsigned long parsedId = std::strtoul(row[0].c_str(), &pEnd, 10);

        if (pEnd == row[0].c_str() || *pEnd != '\0')
        {
            continue;
        }

        JournalQuestEntry entry = {};
        entry.qbitId = static_cast<uint32_t>(parsedId);
        entry.text = getCell(row, 1);
        entry.notes = getCell(row, 2);
        entry.owner = getCell(row, 3);

        if (entry.text.empty())
        {
            continue;
        }

        m_entries.push_back(std::move(entry));
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
}
