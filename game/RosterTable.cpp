#include "game/RosterTable.h"

#include <cstdlib>

namespace OpenYAMM::Game
{
namespace
{
bool parseUnsigned(const std::string &text, uint32_t &value)
{
    if (text.empty() || text[0] == '#')
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(text.c_str(), &pEnd, 10);

    if (pEnd == text.c_str() || *pEnd != '\0')
    {
        return false;
    }

    value = static_cast<uint32_t>(parsed);
    return true;
}
}

bool RosterTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    std::vector<std::string> skillColumns;

    if (rows.size() > 1)
    {
        const std::vector<std::string> &headerRow = rows[1];

        for (size_t columnIndex = 22; columnIndex < headerRow.size(); columnIndex += 2)
        {
            skillColumns.push_back(canonicalSkillName(headerRow[columnIndex]));
        }
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 21)
        {
            continue;
        }

        uint32_t id = 0;

        if (!parseUnsigned(row[0], id) || id == 0)
        {
            continue;
        }

        RosterEntry entry = {};
        entry.id = id;
        entry.name = row[1];
        entry.className = row[2];

        if (entry.name.empty() || entry.name == "Placeholder")
        {
            continue;
        }

        parseUnsigned(row[4], entry.pictureId);
        parseUnsigned(row[7], entry.level);
        parseUnsigned(row[8], entry.might);
        parseUnsigned(row[9], entry.intellect);
        parseUnsigned(row[10], entry.personality);
        parseUnsigned(row[11], entry.endurance);
        parseUnsigned(row[12], entry.speed);
        parseUnsigned(row[13], entry.accuracy);
        parseUnsigned(row[14], entry.luck);
        parseUnsigned(row[21], entry.skillPoints);
        entry.level = std::max<uint32_t>(1, entry.level);

        for (size_t skillIndex = 0; skillIndex < skillColumns.size(); ++skillIndex)
        {
            const size_t masteryColumn = 22 + skillIndex * 2;
            const size_t levelColumn = masteryColumn + 1;

            if (levelColumn >= row.size() || skillColumns[skillIndex].empty())
            {
                continue;
            }

            const SkillMastery mastery = parseSkillMasteryToken(row[masteryColumn]);
            uint32_t level = 0;

            if (mastery == SkillMastery::None || !parseUnsigned(row[levelColumn], level) || level == 0)
            {
                continue;
            }

            CharacterSkill skill = {};
            skill.name = skillColumns[skillIndex];
            skill.level = level;
            skill.mastery = mastery;
            entry.skills[skill.name] = std::move(skill);
        }

        m_entries[entry.id] = std::move(entry);
    }

    return !m_entries.empty();
}

const RosterEntry *RosterTable::get(uint32_t rosterId) const
{
    const std::unordered_map<uint32_t, RosterEntry>::const_iterator it = m_entries.find(rosterId);

    if (it == m_entries.end())
    {
        return nullptr;
    }

    return &it->second;
}
}
