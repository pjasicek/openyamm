#include "game/MonsterProjectileTable.h"

#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
std::string normalizeToken(std::string value)
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
        if (!std::isdigit(static_cast<unsigned char>(character)) && character != '-')
        {
            return false;
        }
    }

    return true;
}
}

bool MonsterProjectileTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndexByNormalizedToken.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 2 || row[0].empty() || !isNumericString(row[1]))
        {
            continue;
        }

        MonsterProjectileEntry entry = {};
        entry.token = row[0];
        entry.normalizedToken = normalizeToken(entry.token);
        entry.objectId = std::stoi(row[1]);
        entry.impactObjectId = row.size() > 2 && isNumericString(row[2]) ? std::stoi(row[2]) : 0;
        m_entryIndexByNormalizedToken[entry.normalizedToken] = m_entries.size();
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const MonsterProjectileEntry *MonsterProjectileTable::findByToken(const std::string &token) const
{
    const auto entryIt = m_entryIndexByNormalizedToken.find(normalizeToken(token));

    if (entryIt == m_entryIndexByNormalizedToken.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}
}
