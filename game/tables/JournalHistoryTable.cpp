#include "game/tables/JournalHistoryTable.h"

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

bool JournalHistoryTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
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

        JournalHistoryEntry entry = {};
        entry.id = static_cast<uint32_t>(parsedId);
        entry.text = getCell(row, 1);
        entry.timeToken = getCell(row, 2);
        entry.pageTitle = getCell(row, 3);

        if (entry.text.empty())
        {
            continue;
        }

        m_entries.push_back(std::move(entry));
    }

    std::sort(
        m_entries.begin(),
        m_entries.end(),
        [](const JournalHistoryEntry &left, const JournalHistoryEntry &right)
        {
            return left.id < right.id;
        });

    return !m_entries.empty();
}

const std::vector<JournalHistoryEntry> &JournalHistoryTable::entries() const
{
    return m_entries;
}

const JournalHistoryEntry *JournalHistoryTable::get(uint32_t id) const
{
    for (const JournalHistoryEntry &entry : m_entries)
    {
        if (entry.id == id)
        {
            return &entry;
        }
    }

    return nullptr;
}
}
