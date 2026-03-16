#include "game/HouseTable.h"

#include <cstdlib>

namespace OpenYAMM::Game
{
bool HouseTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 5 || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }

        char *pEnd = nullptr;
        const unsigned long parsedId = std::strtoul(row[0].c_str(), &pEnd, 10);

        if (pEnd == row[0].c_str() || *pEnd != '\0')
        {
            continue;
        }

        const std::string &name = row[5];

        if (name.empty())
        {
            continue;
        }

        HouseEntry entry = {};
        entry.id = static_cast<uint32_t>(parsedId);
        entry.name = name;
        m_entries[entry.id] = entry;
    }

    return !m_entries.empty();
}

std::optional<std::string> HouseTable::getName(uint32_t houseId) const
{
    const auto entryIt = m_entries.find(houseId);

    if (entryIt == m_entries.end())
    {
        return std::nullopt;
    }

    return entryIt->second.name;
}
}
