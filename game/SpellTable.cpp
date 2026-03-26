#include "game/SpellTable.h"

#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
std::string normalizeName(std::string value)
{
    for (char &character : value)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return value;
}

bool isNumericString(const std::string &value)
{
    if (value.empty())
    {
        return false;
    }

    for (char character : value)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return false;
        }
    }

    return true;
}
}

bool SpellTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndexById.clear();
    m_entryIndexByNormalizedName.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 22 || !isNumericString(row[0]))
        {
            continue;
        }

        SpellEntry entry = {};
        entry.id = std::stoi(row[0]);
        entry.name = row[2];
        entry.normalizedName = normalizeName(entry.name);
        entry.normalRecoveryTicks = row[15].empty() ? 0 : std::stoi(row[15]);
        entry.expertRecoveryTicks = row[16].empty() ? 0 : std::stoi(row[16]);
        entry.masterRecoveryTicks = row[17].empty() ? 0 : std::stoi(row[17]);
        entry.grandmasterRecoveryTicks = row[18].empty() ? 0 : std::stoi(row[18]);
        entry.effectSoundId = row[19].empty() ? 0 : std::stoi(row[19]);
        entry.displayObjectId = row[20].empty() ? 0 : std::stoi(row[20]);
        entry.impactDisplayObjectId = row[21].empty() ? 0 : std::stoi(row[21]);
        m_entryIndexById[entry.id] = m_entries.size();
        m_entryIndexByNormalizedName[entry.normalizedName] = m_entries.size();
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const SpellEntry *SpellTable::findById(int id) const
{
    const auto entryIt = m_entryIndexById.find(id);

    if (entryIt == m_entryIndexById.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}

const SpellEntry *SpellTable::findByName(const std::string &name) const
{
    const auto entryIt = m_entryIndexByNormalizedName.find(normalizeName(name));

    if (entryIt == m_entryIndexByNormalizedName.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}
}
