#pragma once

#include "game/party/SkillData.h"

#include <array>
#include <cstdint>
#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct SpellEntry
{
    int id = 0;
    std::string name;
    std::string normalizedName;
    std::string schoolName;
    std::string shortName;
    std::string description;
    std::string normalText;
    std::string expertText;
    std::string masterText;
    std::string grandmasterText;
    std::string statsText;
    int normalManaCost = 0;
    int expertManaCost = 0;
    int masterManaCost = 0;
    int grandmasterManaCost = 0;
    int normalRecoveryTicks = 0;
    int expertRecoveryTicks = 0;
    int masterRecoveryTicks = 0;
    int grandmasterRecoveryTicks = 0;
    int effectSoundId = 0;
    int displayObjectId = 0;
    int impactDisplayObjectId = 0;
    int damageBase = 0;
    // Damage per skill point is a roll from damageDiceMin to damageDiceSides; equal values are a fixed amount.
    int damageDiceSides = 0;
    int damageDiceMin = 1;
    SkillMastery requiredMastery = SkillMastery::Normal;
    // Indexed by mastery, Normal to Grandmaster.
    std::array<uint32_t, 4> projectileCounts = {1, 1, 1, 1};
    // Scales the base damage and the dice of a cast at each mastery, in percent.
    std::array<int, 4> damagePercents = {100, 100, 100, 100};
};

// A spell's numbers when the party casts it at one mastery.
struct SpellMasteryNumbers
{
    int manaCost = 0;
    int recoveryTicks = 0;
    int damageBase = 0;
    int damageDiceMin = 0;
    int damageDiceMax = 0;
    uint32_t projectileCount = 1;
};

SpellMasteryNumbers spellNumbersAtMastery(const SpellEntry &entry, SkillMastery mastery);

class SpellTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const SpellEntry *findById(int id) const;
    const SpellEntry *findByName(const std::string &name) const;
    // Rows may share a name (Mind's and the Vampire's Charm): the row of that name the predicate accepts (the spell a
    // caster knows), else the one findByName returns (OY-337).
    const SpellEntry *findByName(const std::string &name, const std::function<bool(const SpellEntry &)> &prefer) const;
    const std::vector<SpellEntry> &entries() const;

private:
    std::vector<SpellEntry> m_entries;
    std::unordered_map<int, size_t> m_entryIndexById;
    std::unordered_map<std::string, size_t> m_entryIndexByNormalizedName;
    // The earlier rows of a name that a later row took over in m_entryIndexByNormalizedName.
    std::unordered_map<std::string, std::vector<size_t>> m_shadowedEntryIndicesByName;
};
}
