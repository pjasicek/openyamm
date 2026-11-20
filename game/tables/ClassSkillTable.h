#pragma once

#include "game/party/SkillData.h"

#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class MergedRaceSkillTable;

struct ClassMetadataEntry
{
    uint32_t classId = 0;
    std::string className;
    uint32_t classKind = 0;
    uint32_t promotionStep = 0;
    uint32_t manaMode = 0;
};

class ClassSkillTable
{
public:
    bool loadCapsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadStartingSkillsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadClassMetadataFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadClassSpellPointMetadataFromRows(const std::vector<std::vector<std::string>> &rows);
    bool applyRaceSkillOverrides(const MergedRaceSkillTable &raceSkillTable);

    SkillMastery getClassCap(const std::string &className, const std::string &skillName) const;
    SkillMastery getEffectiveCap(const std::string &className, uint32_t raceId, const std::string &skillName) const;
    SkillMastery getHighestPromotionCap(const std::string &className, const std::string &skillName) const;
    SkillMastery getHighestPromotionEffectiveCap(
        const std::string &className,
        uint32_t raceId,
        const std::string &skillName
    ) const;
    std::vector<std::string> getClosestPromotionClassesWithEffectiveCap(
        const std::string &className,
        uint32_t raceId,
        const std::string &skillName,
        SkillMastery requiredMastery
    ) const;
    StartingSkillAvailability getStartingSkillAvailability(const std::string &className, const std::string &skillName)
        const;
    StartingSkillAvailability getEffectiveStartingSkillAvailability(
        const std::string &className,
        uint32_t raceId,
        const std::string &skillName
    ) const;
    std::vector<CharacterSkill> getDefaultSkillsForClass(const std::string &className) const;
    std::vector<CharacterSkill> getDefaultSkillsForCharacter(const std::string &className, uint32_t raceId) const;
    std::optional<uint32_t> classIdForName(const std::string &className) const;
    std::optional<std::string> classNameForId(uint32_t classId) const;
    bool classIdIsAtLeast(uint32_t currentClassId, uint32_t minimumClassId) const;
    bool hasClass(const std::string &className) const;
    // A class's id, kind and promotion step from class_extra.txt; null for a class it does not list.
    const ClassMetadataEntry *classMetadata(const std::string &className) const;
    // The classes of a kind at a promotion step, by class id.
    std::vector<std::string> classNamesOfKind(uint32_t classKind, uint32_t promotionStep) const;

private:
    struct RaceSkillRule
    {
        uint32_t raceId = 0;
        uint32_t classKind = 0;
        bool hasClassKind = false;
        std::string skillName;
        SkillMastery minMastery = SkillMastery::None;
        std::optional<SkillMastery> maxMastery;
        int32_t add = 0;
        int32_t exceptionCode = 0;
    };

    std::vector<std::string> promotionClassNamesFromMetadata(const std::string &className) const;
    const ClassMetadataEntry *metadataForClass(const std::string &className) const;
    uint32_t classKindForClass(const std::string &className) const;
    uint32_t manaModeForClass(const std::string &className) const;
    bool raceSkillRuleApplies(const RaceSkillRule &rule, const std::string &className) const;
    bool raceSkillRuleCanCreateStartingChoice(
        const RaceSkillRule &rule,
        const std::string &className,
        SkillMastery baseCap
    ) const;

    std::unordered_map<std::string, std::unordered_map<std::string, SkillMastery>> m_caps;
    std::unordered_map<std::string, std::unordered_map<std::string, StartingSkillAvailability>> m_startingSkills;
    std::unordered_map<std::string, ClassMetadataEntry> m_classMetadata;
    std::unordered_map<uint32_t, std::string> m_classNamesById;
    std::vector<RaceSkillRule> m_raceSkillRules;
    bool m_raceShiftWithoutClassCap = false;
};
}
