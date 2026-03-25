#include "game/CharacterInspectTable.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
std::string trimCopy(const std::string &value)
{
    size_t start = 0;

    while (start < value.size() && std::isspace(static_cast<unsigned char>(value[start])))
    {
        ++start;
    }

    size_t end = value.size();

    while (end > start && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return value.substr(start, end - start);
}

std::string cellValue(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return {};
    }

    return trimCopy(row[index]);
}

std::string canonicalLookupKey(const std::string &value)
{
    std::string result;

    for (unsigned char character : trimCopy(value))
    {
        if (std::isalnum(character))
        {
            result.push_back(static_cast<char>(std::tolower(character)));
        }
    }

    return result;
}
}

std::string CharacterInspectTable::canonicalStatName(const std::string &name)
{
    const std::string key = canonicalLookupKey(name);

    if (key == "might")
    {
        return "Might";
    }

    if (key == "intellect")
    {
        return "Intellect";
    }

    if (key == "personality")
    {
        return "Personality";
    }

    if (key == "endurance")
    {
        return "Endurance";
    }

    if (key == "accuracy")
    {
        return "Accuracy";
    }

    if (key == "speed")
    {
        return "Speed";
    }

    if (key == "luck")
    {
        return "Luck";
    }

    if (key == "hitpoints")
    {
        return "HitPoints";
    }

    if (key == "spellpoints")
    {
        return "SpellPoints";
    }

    if (key == "armorclass")
    {
        return "ArmorClass";
    }

    if (key == "condition")
    {
        return "Condition";
    }

    if (key == "quickspell")
    {
        return "QuickSpell";
    }

    if (key == "age")
    {
        return "Age";
    }

    if (key == "level")
    {
        return "Level";
    }

    if (key == "experience")
    {
        return "Experience";
    }

    if (key == "attackbonus" || key == "attack")
    {
        return "Attack";
    }

    if (key == "attackdamage" || key == "meleedamage")
    {
        return "MeleeDamage";
    }

    if (key == "shootbonus" || key == "shoot")
    {
        return "Shoot";
    }

    if (key == "shootdamage" || key == "rangeddamage")
    {
        return "RangedDamage";
    }

    if (key == "fire" || key == "fireresistance")
    {
        return "FireResistance";
    }

    if (key == "air" || key == "airresistance")
    {
        return "AirResistance";
    }

    if (key == "water" || key == "waterresistance")
    {
        return "WaterResistance";
    }

    if (key == "earth" || key == "earthresistance")
    {
        return "EarthResistance";
    }

    if (key == "mind" || key == "mindresistance")
    {
        return "MindResistance";
    }

    if (key == "body" || key == "bodyresistance")
    {
        return "BodyResistance";
    }

    if (key == "skillpoints")
    {
        return "SkillPoints";
    }

    return {};
}

bool CharacterInspectTable::loadStatRows(const std::vector<std::vector<std::string>> &rows)
{
    m_stats.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const std::string name = cellValue(row, 0);
        const std::string description = cellValue(row, 1);
        const std::string canonicalName = canonicalStatName(name);

        if (canonicalName.empty() || description.empty())
        {
            continue;
        }

        StatInspectEntry entry = {};
        entry.name = name;
        entry.description = description;
        m_stats[canonicalName] = std::move(entry);
    }

    return !m_stats.empty();
}

bool CharacterInspectTable::loadSkillRows(const std::vector<std::vector<std::string>> &rows)
{
    m_skills.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const std::string canonicalSkill = canonicalSkillName(cellValue(row, 0));

        if (canonicalSkill.empty())
        {
            continue;
        }

        SkillInspectEntry entry = {};
        entry.name = displaySkillName(canonicalSkill);
        entry.description = cellValue(row, 1);
        entry.normalDescription = cellValue(row, 2);
        entry.expertDescription = cellValue(row, 3);
        entry.masterDescription = cellValue(row, 4);
        entry.grandmasterDescription = cellValue(row, 5);
        m_skills[canonicalSkill] = std::move(entry);
    }

    return !m_skills.empty();
}

const StatInspectEntry *CharacterInspectTable::getStat(const std::string &statName) const
{
    const std::string canonicalName = canonicalStatName(statName);
    const std::unordered_map<std::string, StatInspectEntry>::const_iterator it = m_stats.find(canonicalName);
    return it != m_stats.end() ? &it->second : nullptr;
}

const SkillInspectEntry *CharacterInspectTable::getSkill(const std::string &skillName) const
{
    const std::string canonicalName = canonicalSkillName(skillName);
    const std::unordered_map<std::string, SkillInspectEntry>::const_iterator it = m_skills.find(canonicalName);
    return it != m_skills.end() ? &it->second : nullptr;
}
}
