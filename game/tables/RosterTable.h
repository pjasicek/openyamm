#pragma once

#include "game/party/CharacterState.h"
#include "game/party/SkillData.h"

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
    std::string blurb;
    uint32_t birthYear = 0;
    uint32_t pictureId = 0;
    int32_t voiceId = -1;
    uint32_t experience = 0;
    uint32_t level = 1;
    uint32_t might = 0;
    uint32_t intellect = 0;
    uint32_t personality = 0;
    uint32_t endurance = 0;
    uint32_t speed = 0;
    uint32_t accuracy = 0;
    uint32_t luck = 0;
    CharacterResistanceSet baseResistances = {};
    uint32_t skillPoints = 0;
    std::unordered_map<std::string, CharacterSkill> skills;
    std::unordered_map<std::string, uint32_t> knownSpellCounts;
    std::vector<uint32_t> startingInventoryItemIds;
};

class RosterTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);

    const RosterEntry *get(uint32_t rosterId) const;
    const RosterEntry *findByName(const std::string &name) const;
    std::vector<const RosterEntry *> getEntriesSortedById() const;

private:
    std::unordered_map<uint32_t, RosterEntry> m_entries;
};
}
