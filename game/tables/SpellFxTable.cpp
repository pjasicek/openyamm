#include "game/tables/SpellFxTable.h"

#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
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

bool SpellFxTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndexBySpellId.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 3 || !isNumericString(row[0]) || row[2].empty())
        {
            continue;
        }

        SpellFxEntry entry = {};
        entry.spellId = static_cast<uint32_t>(std::stoul(row[0]));
        entry.spellName = row[1];
        entry.animationName = row[2];
        m_entryIndexBySpellId[entry.spellId] = m_entries.size();
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const SpellFxEntry *SpellFxTable::findBySpellId(uint32_t spellId) const
{
    const auto entryIt = m_entryIndexBySpellId.find(spellId);

    if (entryIt == m_entryIndexBySpellId.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}
}
