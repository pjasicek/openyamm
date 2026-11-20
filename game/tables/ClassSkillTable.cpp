#include "game/tables/ClassSkillTable.h"

#include "game/tables/MergedBaseTables.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
bool parseUnsigned(const std::string &text, uint32_t &value)
{
    if (text.empty())
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

std::string trimCopy(const std::string &text)
{
    size_t begin = 0;

    while (begin < text.size() && std::isspace(static_cast<unsigned char>(text[begin])) != 0)
    {
        ++begin;
    }

    size_t end = text.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(text[end - 1])) != 0)
    {
        --end;
    }

    return text.substr(begin, end - begin);
}

std::string normalizedToken(const std::string &text)
{
    std::string result;

    for (unsigned char character : trimCopy(text))
    {
        if (std::isalnum(character))
        {
            result.push_back(static_cast<char>(std::tolower(character)));
        }
    }

    return result;
}

uint32_t manaModeCodeFromToken(const std::string &text)
{
    const std::string token = normalizedToken(text);

    if (token == "intellect" || token == "intelligence")
    {
        return 1;
    }

    if (token == "personality")
    {
        return 2;
    }

    if (token == "mixed")
    {
        return 3;
    }

    if (token == "level")
    {
        return 4;
    }

    return 0;
}

SkillMastery clampSkillMastery(int32_t mastery)
{
    if (mastery <= 0)
    {
        return SkillMastery::None;
    }

    if (mastery >= 4)
    {
        return SkillMastery::Grandmaster;
    }

    return static_cast<SkillMastery>(mastery);
}
}

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

bool ClassSkillTable::loadClassMetadataFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_classMetadata.clear();
    m_classNamesById.clear();

    if (rows.size() < 2)
    {
        return false;
    }

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 4)
        {
            continue;
        }

        ClassMetadataEntry entry = {};

        if (!parseUnsigned(row[0], entry.classId)
            || !parseUnsigned(row[1], entry.classKind)
            || !parseUnsigned(row[2], entry.promotionStep))
        {
            continue;
        }

        entry.className = canonicalClassName(row[3]);

        if (entry.className.empty())
        {
            continue;
        }

        m_classNamesById[entry.classId] = entry.className;

        if (entry.classKind == 0)
        {
            continue;
        }

        m_classMetadata[entry.className] = std::move(entry);
    }

    return !m_classNamesById.empty();
}

bool ClassSkillTable::loadClassSpellPointMetadataFromRows(const std::vector<std::vector<std::string>> &rows)
{
    if (rows.size() < 2)
    {
        return false;
    }

    bool appliedAny = false;

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 6)
        {
            continue;
        }

        const std::string className = canonicalClassName(row[0]);

        if (className.empty())
        {
            continue;
        }

        ClassMetadataEntry &entry = m_classMetadata[className];
        entry.className = className;
        entry.manaMode = manaModeCodeFromToken(row[5]);
        appliedAny = true;
    }

    return appliedAny;
}

bool ClassSkillTable::applyRaceSkillOverrides(const MergedRaceSkillTable &raceSkillTable)
{
    m_raceSkillRules.clear();
    m_raceShiftWithoutClassCap = raceSkillTable.shiftWithoutClassCap();

    for (const MergedRaceSkillOverride &entry : raceSkillTable.overrides())
    {
        if (!entry.raceId)
        {
            continue;
        }

        RaceSkillRule rule = {};
        rule.raceId = *entry.raceId;
        rule.skillName = canonicalSkillName(entry.skillName);
        rule.minMastery = clampSkillMastery(static_cast<int32_t>(entry.minMastery));
        rule.maxMastery = entry.maxMastery
            ? std::optional<SkillMastery>(clampSkillMastery(static_cast<int32_t>(*entry.maxMastery)))
            : std::nullopt;
        rule.add = entry.add;
        rule.exceptionCode = entry.exceptionCode;

        if (rule.skillName.empty())
        {
            continue;
        }

        if (!entry.classKind.empty())
        {
            uint32_t classKind = 0;

            if (!parseUnsigned(entry.classKind, classKind))
            {
                const std::string className = canonicalClassName(entry.classKind);
                const ClassMetadataEntry *pMetadata = metadataForClass(className);

                if (pMetadata != nullptr)
                {
                    classKind = pMetadata->classKind;
                }
            }

            if (classKind == 0)
            {
                continue;
            }

            rule.classKind = classKind;
            rule.hasClassKind = true;
        }

        m_raceSkillRules.push_back(std::move(rule));
    }

    return true;
}

SkillMastery ClassSkillTable::getClassCap(const std::string &className, const std::string &skillName) const
{
    const std::string canonicalClass = canonicalClassName(className);
    const std::string canonicalSkill = canonicalSkillName(skillName);

    // Technology skills are learned technology, not class talents: every class can reach Grandmaster.
    if (isTechnologySkill(canonicalSkill))
    {
        return SkillMastery::Grandmaster;
    }

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

SkillMastery ClassSkillTable::getEffectiveCap(
    const std::string &className,
    uint32_t raceId,
    const std::string &skillName
) const
{
    const SkillMastery baseCap = getClassCap(className, skillName);
    const std::string canonicalSkill = canonicalSkillName(skillName);

    if (canonicalSkill.empty())
    {
        return SkillMastery::None;
    }

    SkillMastery minMastery = SkillMastery::None;
    std::optional<SkillMastery> maxMastery;
    int32_t add = 0;

    for (const RaceSkillRule &rule : m_raceSkillRules)
    {
        if (rule.raceId != raceId
            || rule.skillName != canonicalSkill
            || !raceSkillRuleApplies(rule, className))
        {
            continue;
        }

        if (rule.minMastery > minMastery)
        {
            minMastery = rule.minMastery;
        }

        if (rule.maxMastery && (!maxMastery || *rule.maxMastery < *maxMastery))
        {
            maxMastery = rule.maxMastery;
        }

        if (rule.add > add)
        {
            add = rule.add;
        }
    }

    if (m_raceShiftWithoutClassCap)
    {
        // MAW: shift, then the race's maximum, then its minimum (SK:216-247).
        int32_t shifted = static_cast<int32_t>(baseCap) + add;

        if (maxMastery)
        {
            shifted = std::min(shifted, static_cast<int32_t>(*maxMastery));
        }

        return clampSkillMastery(std::max(shifted, static_cast<int32_t>(minMastery)));
    }

    int32_t result = std::max(static_cast<int32_t>(baseCap), static_cast<int32_t>(minMastery));

    if (baseCap != SkillMastery::None)
    {
        result += add;
    }

    return clampSkillMastery(result);
}

SkillMastery ClassSkillTable::getHighestPromotionCap(const std::string &className, const std::string &skillName) const
{
    SkillMastery bestCap = SkillMastery::None;
    std::vector<std::string> pendingClasses = promotionClassNamesFromMetadata(className);

    if (pendingClasses.empty())
    {
        pendingClasses = promotionClassNames(className);
    }

    while (!pendingClasses.empty())
    {
        const std::string promotedClass = pendingClasses.back();
        pendingClasses.pop_back();
        const SkillMastery cap = getClassCap(promotedClass, skillName);

        if (cap > bestCap)
        {
            bestCap = cap;
        }

        std::vector<std::string> nextPromotions = promotionClassNamesFromMetadata(promotedClass);

        if (nextPromotions.empty())
        {
            nextPromotions = promotionClassNames(promotedClass);
        }

        pendingClasses.insert(pendingClasses.end(), nextPromotions.begin(), nextPromotions.end());
    }

    return bestCap;
}

SkillMastery ClassSkillTable::getHighestPromotionEffectiveCap(
    const std::string &className,
    uint32_t raceId,
    const std::string &skillName
) const
{
    SkillMastery bestCap = SkillMastery::None;
    std::vector<std::string> pendingClasses = promotionClassNamesFromMetadata(className);

    if (pendingClasses.empty())
    {
        pendingClasses = promotionClassNames(className);
    }

    while (!pendingClasses.empty())
    {
        const std::string promotedClass = pendingClasses.back();
        pendingClasses.pop_back();
        const SkillMastery cap = getEffectiveCap(promotedClass, raceId, skillName);

        if (cap > bestCap)
        {
            bestCap = cap;
        }

        std::vector<std::string> nextPromotions = promotionClassNamesFromMetadata(promotedClass);

        if (nextPromotions.empty())
        {
            nextPromotions = promotionClassNames(promotedClass);
        }

        pendingClasses.insert(pendingClasses.end(), nextPromotions.begin(), nextPromotions.end());
    }

    return bestCap;
}

std::vector<std::string> ClassSkillTable::getClosestPromotionClassesWithEffectiveCap(
    const std::string &className,
    uint32_t raceId,
    const std::string &skillName,
    SkillMastery requiredMastery
) const
{
    std::vector<std::string> pendingClasses = promotionClassNamesFromMetadata(className);

    if (pendingClasses.empty())
    {
        pendingClasses = promotionClassNames(className);
    }

    while (!pendingClasses.empty())
    {
        std::vector<std::string> qualifyingClasses;
        std::vector<std::string> nextClasses;

        for (const std::string &promotedClass : pendingClasses)
        {
            if (getEffectiveCap(promotedClass, raceId, skillName) >= requiredMastery)
            {
                qualifyingClasses.push_back(promotedClass);
            }

            std::vector<std::string> promotions = promotionClassNamesFromMetadata(promotedClass);

            if (promotions.empty())
            {
                promotions = promotionClassNames(promotedClass);
            }

            nextClasses.insert(nextClasses.end(), promotions.begin(), promotions.end());
        }

        if (!qualifyingClasses.empty())
        {
            std::sort(qualifyingClasses.begin(), qualifyingClasses.end());
            qualifyingClasses.erase(
                std::unique(qualifyingClasses.begin(), qualifyingClasses.end()),
                qualifyingClasses.end());
            return qualifyingClasses;
        }

        std::sort(nextClasses.begin(), nextClasses.end());
        nextClasses.erase(std::unique(nextClasses.begin(), nextClasses.end()), nextClasses.end());
        pendingClasses = std::move(nextClasses);
    }

    return {};
}

std::vector<std::string> ClassSkillTable::promotionClassNamesFromMetadata(const std::string &className) const
{
    const std::string canonicalClass = canonicalClassName(className);
    const std::unordered_map<std::string, ClassMetadataEntry>::const_iterator classIt =
        m_classMetadata.find(canonicalClass);

    if (classIt == m_classMetadata.end())
    {
        return {};
    }

    std::vector<std::string> result;
    const ClassMetadataEntry &source = classIt->second;

    for (const auto &[candidateClassName, candidate] : m_classMetadata)
    {
        if (candidate.classKind == source.classKind
            && candidate.promotionStep == source.promotionStep + 1)
        {
            result.push_back(candidateClassName);
        }
    }

    std::sort(result.begin(), result.end());
    return result;
}

const ClassMetadataEntry *ClassSkillTable::metadataForClass(const std::string &className) const
{
    const std::unordered_map<std::string, ClassMetadataEntry>::const_iterator classIt =
        m_classMetadata.find(canonicalClassName(className));

    if (classIt == m_classMetadata.end())
    {
        return nullptr;
    }

    return &classIt->second;
}

uint32_t ClassSkillTable::classKindForClass(const std::string &className) const
{
    const ClassMetadataEntry *pMetadata = metadataForClass(className);
    return pMetadata != nullptr ? pMetadata->classKind : 0;
}

uint32_t ClassSkillTable::manaModeForClass(const std::string &className) const
{
    const ClassMetadataEntry *pMetadata = metadataForClass(className);
    return pMetadata != nullptr ? pMetadata->manaMode : 0;
}

bool ClassSkillTable::raceSkillRuleApplies(const RaceSkillRule &rule, const std::string &className) const
{
    const uint32_t classKind = classKindForClass(className);

    if (rule.hasClassKind)
    {
        return classKind != 0 && classKind == rule.classKind;
    }

    if (rule.exceptionCode > 0)
    {
        return classKind != static_cast<uint32_t>(rule.exceptionCode);
    }

    const uint32_t manaMode = manaModeForClass(className);

    switch (rule.exceptionCode)
    {
    case -1:
    case -2:
    case -3:
        return manaMode != static_cast<uint32_t>(-rule.exceptionCode);
    case -4:
        return manaMode != 0;
    case -5:
        return manaMode == 0;
    default:
        return true;
    }
}

bool ClassSkillTable::raceSkillRuleCanCreateStartingChoice(
    const RaceSkillRule &rule,
    const std::string &className,
    SkillMastery baseCap
) const
{
    return baseCap == SkillMastery::None
        && rule.minMastery != SkillMastery::None
        && raceSkillRuleApplies(rule, className);
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

StartingSkillAvailability ClassSkillTable::getEffectiveStartingSkillAvailability(
    const std::string &className,
    uint32_t raceId,
    const std::string &skillName
) const
{
    const StartingSkillAvailability baseAvailability = getStartingSkillAvailability(className, skillName);
    const SkillMastery baseCap = getClassCap(className, skillName);
    const SkillMastery effectiveCap = getEffectiveCap(className, raceId, skillName);

    if (effectiveCap == SkillMastery::None)
    {
        return StartingSkillAvailability::None;
    }

    if (baseAvailability != StartingSkillAvailability::None)
    {
        return baseAvailability;
    }

    const std::string canonicalSkill = canonicalSkillName(skillName);

    for (const RaceSkillRule &rule : m_raceSkillRules)
    {
        if (rule.raceId == raceId
            && rule.skillName == canonicalSkill
            && raceSkillRuleCanCreateStartingChoice(rule, className, baseCap))
        {
            return StartingSkillAvailability::CanLearn;
        }
    }

    return StartingSkillAvailability::None;
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

std::vector<CharacterSkill> ClassSkillTable::getDefaultSkillsForCharacter(
    const std::string &className,
    uint32_t raceId
) const
{
    std::vector<CharacterSkill> skills;

    for (const std::string &skillName : allCanonicalSkillNames())
    {
        if (getEffectiveStartingSkillAvailability(className, raceId, skillName)
            != StartingSkillAvailability::HasByDefault)
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

std::optional<uint32_t> ClassSkillTable::classIdForName(const std::string &className) const
{
    const std::string canonicalClass = canonicalClassName(className);
    const std::unordered_map<std::string, ClassMetadataEntry>::const_iterator metadataIt =
        m_classMetadata.find(canonicalClass);

    if (metadataIt != m_classMetadata.end())
    {
        return metadataIt->second.classId;
    }

    for (const auto &[classId, candidateClassName] : m_classNamesById)
    {
        if (candidateClassName == canonicalClass)
        {
            return classId;
        }
    }

    return std::nullopt;
}

std::optional<std::string> ClassSkillTable::classNameForId(uint32_t classId) const
{
    const std::unordered_map<uint32_t, std::string>::const_iterator iterator = m_classNamesById.find(classId);

    if (iterator == m_classNamesById.end())
    {
        return std::nullopt;
    }

    return iterator->second;
}

bool ClassSkillTable::classIdIsAtLeast(uint32_t currentClassId, uint32_t minimumClassId) const
{
    if (currentClassId == minimumClassId)
    {
        return true;
    }

    const std::optional<std::string> currentClassName = classNameForId(currentClassId);
    const std::optional<std::string> minimumClassName = classNameForId(minimumClassId);

    if (!currentClassName || !minimumClassName)
    {
        return false;
    }

    const ClassMetadataEntry *pCurrent = metadataForClass(*currentClassName);
    const ClassMetadataEntry *pMinimum = metadataForClass(*minimumClassName);

    return pCurrent != nullptr
        && pMinimum != nullptr
        && pMinimum->classKind != 0
        && pCurrent->classKind == pMinimum->classKind
        && pCurrent->promotionStep >= pMinimum->promotionStep;
}

bool ClassSkillTable::hasClass(const std::string &className) const
{
    return classIdForName(className).has_value();
}

const ClassMetadataEntry *ClassSkillTable::classMetadata(const std::string &className) const
{
    return metadataForClass(canonicalClassName(className));
}

std::vector<std::string> ClassSkillTable::classNamesOfKind(uint32_t classKind, uint32_t promotionStep) const
{
    std::vector<const ClassMetadataEntry *> entries;

    for (const auto &[name, entry] : m_classMetadata)
    {
        if (entry.classKind == classKind && entry.promotionStep == promotionStep)
        {
            entries.push_back(&entry);
        }
    }

    std::sort(
        entries.begin(),
        entries.end(),
        [](const ClassMetadataEntry *pLeft, const ClassMetadataEntry *pRight)
        {
            return pLeft->classId < pRight->classId;
        });
    std::vector<std::string> names;

    for (const ClassMetadataEntry *pEntry : entries)
    {
        names.push_back(pEntry->className);
    }

    return names;
}
}
