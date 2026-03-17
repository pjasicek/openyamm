#pragma once

#include "game/SkillData.h"

#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class ClassSkillTable
{
public:
    bool loadCapsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadStartingSkillsFromRows(const std::vector<std::vector<std::string>> &rows);

    SkillMastery getClassCap(const std::string &className, const std::string &skillName) const;
    StartingSkillAvailability getStartingSkillAvailability(const std::string &className, const std::string &skillName)
        const;
    std::vector<CharacterSkill> getDefaultSkillsForClass(const std::string &className) const;

private:
    std::unordered_map<std::string, std::unordered_map<std::string, SkillMastery>> m_caps;
    std::unordered_map<std::string, std::unordered_map<std::string, StartingSkillAvailability>> m_startingSkills;
};
}
