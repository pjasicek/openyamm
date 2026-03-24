#include "game/RosterTable.h"

#include <cctype>
#include <cstdlib>

namespace OpenYAMM::Game
{
namespace
{
std::string normalizeName(const std::string &text)
{
    std::string normalized;
    normalized.reserve(text.size());

    bool previousWasSpace = true;

    for (char character : text)
    {
        const unsigned char unsignedCharacter = static_cast<unsigned char>(character);

        if (std::isspace(unsignedCharacter) != 0)
        {
            if (!previousWasSpace)
            {
                normalized.push_back(' ');
                previousWasSpace = true;
            }

            continue;
        }

        normalized.push_back(static_cast<char>(std::tolower(unsignedCharacter)));
        previousWasSpace = false;
    }

    if (!normalized.empty() && normalized.back() == ' ')
    {
        normalized.pop_back();
    }

    return normalized;
}

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

        parseUnsigned(row[3], entry.birthYear);
        parseUnsigned(row[4], entry.pictureId);
        parseUnsigned(row[6], entry.experience);
        parseUnsigned(row[7], entry.level);
        parseUnsigned(row[8], entry.might);
        parseUnsigned(row[9], entry.intellect);
        parseUnsigned(row[10], entry.personality);
        parseUnsigned(row[11], entry.endurance);
        parseUnsigned(row[12], entry.speed);
        parseUnsigned(row[13], entry.accuracy);
        parseUnsigned(row[14], entry.luck);
        uint32_t fireResistance = 0;
        uint32_t airResistance = 0;
        uint32_t waterResistance = 0;
        uint32_t earthResistance = 0;
        uint32_t mindResistance = 0;
        uint32_t bodyResistance = 0;
        parseUnsigned(row[15], fireResistance);
        parseUnsigned(row[16], airResistance);
        parseUnsigned(row[17], waterResistance);
        parseUnsigned(row[18], earthResistance);
        parseUnsigned(row[19], mindResistance);
        parseUnsigned(row[20], bodyResistance);
        entry.baseResistances.fire = static_cast<int>(fireResistance);
        entry.baseResistances.air = static_cast<int>(airResistance);
        entry.baseResistances.water = static_cast<int>(waterResistance);
        entry.baseResistances.earth = static_cast<int>(earthResistance);
        entry.baseResistances.mind = static_cast<int>(mindResistance);
        entry.baseResistances.body = static_cast<int>(bodyResistance);
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

        if (row.size() > 113)
        {
            for (size_t columnIndex = 113; columnIndex < std::min<size_t>(123, row.size()); ++columnIndex)
            {
                uint32_t itemId = 0;

                if (parseUnsigned(row[columnIndex], itemId) && itemId != 0)
                {
                    entry.startingInventoryItemIds.push_back(itemId);
                }
            }
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

const RosterEntry *RosterTable::findByName(const std::string &name) const
{
    const std::string normalizedName = normalizeName(name);

    if (normalizedName.empty())
    {
        return nullptr;
    }

    for (const auto &[rosterId, entry] : m_entries)
    {
        (void)rosterId;

        if (normalizeName(entry.name) == normalizedName)
        {
            return &entry;
        }
    }

    return nullptr;
}
}
