#include "game/tables/RaceStartingStatsTable.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game
{
std::string RaceStartingStatsTable::canonicalRaceName(const std::string &raceName)
{
    std::string canonical;
    canonical.reserve(raceName.size());

    for (char character : raceName)
    {
        if (std::isalnum(static_cast<unsigned char>(character)) == 0)
        {
            continue;
        }

        canonical.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return canonical;
}

bool RaceStartingStatsTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    if (rows.size() < 2)
    {
        return false;
    }

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 8)
        {
            continue;
        }

        Entry entry = {};
        entry.raceName = row[0];
        const std::string canonicalName = canonicalRaceName(entry.raceName);

        if (canonicalName.empty())
        {
            continue;
        }

        bool valid = true;

        for (size_t statIndex = 0; statIndex < entry.stats.size(); ++statIndex)
        {
            try
            {
                entry.stats[statIndex] = std::stoi(row[statIndex + 1]);
            }
            catch (...)
            {
                valid = false;
                break;
            }
        }

        if (!valid)
        {
            continue;
        }

        m_entries[canonicalName] = std::move(entry);
    }

    return !m_entries.empty();
}

const RaceStartingStatsTable::Entry *RaceStartingStatsTable::get(const std::string &raceName) const
{
    const std::unordered_map<std::string, Entry>::const_iterator it = m_entries.find(canonicalRaceName(raceName));

    if (it == m_entries.end())
    {
        return nullptr;
    }

    return &it->second;
}
}
