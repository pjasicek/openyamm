#pragma once

#include "game/SkillData.h"

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct RosterEntry
{
    uint32_t id = 0;
    std::string name;
    std::string className;
    uint32_t pictureId = 0;
    uint32_t level = 1;
    uint32_t might = 0;
    uint32_t intellect = 0;
    uint32_t personality = 0;
    uint32_t endurance = 0;
    uint32_t speed = 0;
    uint32_t accuracy = 0;
    uint32_t luck = 0;
    uint32_t skillPoints = 0;
    std::unordered_map<std::string, CharacterSkill> skills;
};

class RosterTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);

    const RosterEntry *get(uint32_t rosterId) const;

private:
    std::unordered_map<uint32_t, RosterEntry> m_entries;
};
}
