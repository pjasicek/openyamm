#pragma once

#include "game/party/SkillData.h"

#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct StatInspectEntry
{
    std::string name;
    std::string description;
};

struct SkillInspectEntry
{
    std::string name;
    std::string description;
    std::string normalDescription;
    std::string expertDescription;
    std::string masterDescription;
    std::string grandmasterDescription;
};

struct ClassInspectEntry
{
    std::string name;
    std::string description;
};

class CharacterInspectTable
{
public:
    bool loadStatRows(const std::vector<std::vector<std::string>> &rows);
    bool loadSkillRows(const std::vector<std::vector<std::string>> &rows);
    bool loadClassRows(const std::vector<std::vector<std::string>> &rows);

    const StatInspectEntry *getStat(const std::string &statName) const;
    const SkillInspectEntry *getSkill(const std::string &skillName) const;
    const ClassInspectEntry *getClass(const std::string &className) const;

private:
    static std::string canonicalStatName(const std::string &name);

    std::unordered_map<std::string, StatInspectEntry> m_stats;
    std::unordered_map<std::string, SkillInspectEntry> m_skills;
    std::unordered_map<std::string, ClassInspectEntry> m_classes;
};
}
