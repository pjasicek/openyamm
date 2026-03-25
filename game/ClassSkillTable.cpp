#include "game/ClassSkillTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
bool ClassSkillTable::loadCapsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_caps.clear();

    if (rows.size() < 2)
    {
        return false;
    }

    std::vector<std::string> classNames;
    const std::vector<std::string> &headerRow = rows[0];

    for (size_t columnIndex = 1; columnIndex < headerRow.size(); ++columnIndex)
    {
        classNames.push_back(canonicalClassName(headerRow[columnIndex]));
    }

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.empty())
        {
            continue;
        }

        const std::string skillName = canonicalSkillName(row[0]);

        if (skillName.empty())
        {
            continue;
        }

        for (size_t columnIndex = 1; columnIndex < row.size() && columnIndex - 1 < classNames.size(); ++columnIndex)
        {
            const std::string &className = classNames[columnIndex - 1];

            if (className.empty())
            {
                continue;
            }

            m_caps[className][skillName] = parseSkillMasteryToken(row[columnIndex]);
        }
    }

    return !m_caps.empty();
}

bool ClassSkillTable::loadStartingSkillsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_startingSkills.clear();

    if (rows.size() < 2)
    {
        return false;
    }

    std::vector<std::string> skillNames;
    const std::vector<std::string> &headerRow = rows[0];

    for (size_t columnIndex = 1; columnIndex < headerRow.size(); ++columnIndex)
    {
        skillNames.push_back(canonicalSkillName(headerRow[columnIndex]));
    }

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.empty())
        {
            continue;
        }

        const std::string className = canonicalClassName(row[0]);

        if (className.empty())
        {
            continue;
        }

        for (size_t columnIndex = 1; columnIndex < row.size() && columnIndex - 1 < skillNames.size(); ++columnIndex)
        {
            const std::string &skillName = skillNames[columnIndex - 1];

            if (skillName.empty())
            {
                continue;
            }

            m_startingSkills[className][skillName] = parseStartingSkillAvailabilityToken(row[columnIndex]);
        }
    }

    return !m_startingSkills.empty();
}

SkillMastery ClassSkillTable::getClassCap(const std::string &className, const std::string &skillName) const
{
    const std::string canonicalClass = canonicalClassName(className);
    const std::string canonicalSkill = canonicalSkillName(skillName);
    const std::unordered_map<std::string, std::unordered_map<std::string, SkillMastery>>::const_iterator classIt =
        m_caps.find(canonicalClass);

    if (classIt == m_caps.end())
    {
        return SkillMastery::None;
    }

    const std::unordered_map<std::string, SkillMastery>::const_iterator skillIt = classIt->second.find(canonicalSkill);

    if (skillIt == classIt->second.end())
    {
        return SkillMastery::None;
    }

    return skillIt->second;
}

SkillMastery ClassSkillTable::getHighestPromotionCap(const std::string &className, const std::string &skillName) const
{
    SkillMastery bestCap = SkillMastery::None;
    std::vector<std::string> pendingClasses = promotionClassNames(className);

    while (!pendingClasses.empty())
    {
        const std::string promotedClass = pendingClasses.back();
        pendingClasses.pop_back();
        const SkillMastery cap = getClassCap(promotedClass, skillName);

        if (cap > bestCap)
        {
            bestCap = cap;
        }

        const std::vector<std::string> nextPromotions = promotionClassNames(promotedClass);
        pendingClasses.insert(pendingClasses.end(), nextPromotions.begin(), nextPromotions.end());
    }

    return bestCap;
}

StartingSkillAvailability ClassSkillTable::getStartingSkillAvailability(
    const std::string &className,
    const std::string &skillName
) const
{
    const std::string canonicalClass = canonicalClassName(className);
    const std::string canonicalSkill = canonicalSkillName(skillName);
    const std::unordered_map<std::string, std::unordered_map<std::string, StartingSkillAvailability>>::const_iterator
        classIt = m_startingSkills.find(canonicalClass);

    if (classIt == m_startingSkills.end())
    {
        return StartingSkillAvailability::None;
    }

    const std::unordered_map<std::string, StartingSkillAvailability>::const_iterator skillIt =
        classIt->second.find(canonicalSkill);

    if (skillIt == classIt->second.end())
    {
        return StartingSkillAvailability::None;
    }

    return skillIt->second;
}

std::vector<CharacterSkill> ClassSkillTable::getDefaultSkillsForClass(const std::string &className) const
{
    std::vector<CharacterSkill> skills;
    const std::string canonicalClass = canonicalClassName(className);
    const std::unordered_map<std::string, std::unordered_map<std::string, StartingSkillAvailability>>::const_iterator
        classIt = m_startingSkills.find(canonicalClass);

    if (classIt == m_startingSkills.end())
    {
        return skills;
    }

    for (const auto &[skillName, availability] : classIt->second)
    {
        if (availability != StartingSkillAvailability::HasByDefault)
        {
            continue;
        }

        CharacterSkill skill = {};
        skill.name = skillName;
        skill.level = 1;
        skill.mastery = SkillMastery::Normal;
        skills.push_back(std::move(skill));
    }

    std::sort(
        skills.begin(),
        skills.end(),
        [](const CharacterSkill &left, const CharacterSkill &right)
        {
            return left.name < right.name;
        }
    );
    return skills;
}
}
