#pragma once

#include "game/rules/ExperienceRules.h"

namespace OpenYAMM::Game
{
class MawRules;
struct Character;
struct MawDimensionRun;

// MAW's experience (devdocs/maw/data/exp_curve.yml): the steeper curve above level 100, kill experience scaled by how
// tough the monster is for each member, and the continent level banks that monster levels follow.
class MawExperienceRules : public ExperienceRules
{
public:
    explicit MawExperienceRules(MawRules &rules);

    uint64_t experienceForNextLevel(uint32_t level) const override;
    uint32_t grantKillExperience(Party &party, const MonsterKillReward &kill) const override;
    // Map completion (zzMaw-Monsters.lua checkMapCompletition): the first time 0.99^floor(n / 100) of a map's n
    // monsters are slain, experience, gold, a bank deposit sized by the map's level band, a Crafting Cube and gems;
    // a dimension run on a completed map gives its next map instead.
    std::string rewardMapProgress(Party &party, const MapKillProgress &progress) const override;
    // EventExperience (zzzMaw_Experience.lua:93-138): value x (1 + L / 100) + 500 L for the levels L banked outside
    // the continent (all of them in Beyond Madness), x 5 / party size for each member; each member's share / party
    // size goes to the bank.
    int64_t eventExperience(Party &party, int64_t value, uint32_t continentId) const override;
    // calculateGold (GLOBAL.lua:5-75).
    int questGoldBonus(int gold, uint32_t continentId) const override;
    // Halls train to round(cap^1.5 / 20) x 10 (/ 10 in Beyond Madness), in two days (TRAINERS_SKILLS.md §3).
    int trainingLevelCap(int tableCap) const override;
    float trainingDurationMinutes(float standardMinutes) const override;
    bool learningGrantsExperience() const override;
    uint64_t maximumExperience() const override;
    // Doom and the modes after it (MenuExtraSettings.lua:272-301, zzMaw-Items.lua:4537-4552): Beyond Madness first sets
    // everyone to level 1 with no experience or skill points and every skill at 1; then the gold becomes 5000, every
    // member gains 10000 / party size experience, and enchantable items without item power get 2 (4 from Road to
    // Insanity).
    void prepareNewParty(Party &party) const override;
    // MMMerge keeps the recruitable roster with the party's records, so MAW's start reaches them too: Beyond Madness's
    // level 1 and the Doom modes' item power, and in every MAW game Learning comes off with its points refunded
    // (zzMAW-Skills.lua:1543-1560).
    void prepareRosterCharacter(Character &character) const override;
    // Beyond Madness (zzMaw-Monsters.lua:2496-2533): "Death Count" on the character screen, the red seconds of a
    // pending death on the HUD, and a warning on loading while one is pending.
    std::optional<int> runDeaths() const override;
    std::optional<int> deathPendingSeconds(double gameMinutes) const override;
    std::optional<std::string> loadWarning() const override;

private:
    // A dimension run's map cleared again: the quest's tier counts it, and the next map drops.
    std::string completeDimensionRun(Party &party, MawDimensionRun &run) const;
    void resetForMadness(Character &character) const;
    void giveStartingItemPower(Character &character) const;

    MawRules &m_rules;
};

// What a kill gives one member (zzzMaw_Experience.lua, zzMaw-Monsters.lua:2090-2101): the share `experience` times the
// monster's HP over the HP of a monster of the member's level (their experience level, at most the party's total
// level), at most (level + 1) x 1000. The bolster bank takes the same capped award (MAW 21e29d54).
struct MawMemberKillExperience
{
    double award = 0;
};

MawMemberKillExperience mawMemberKillExperience(
    const MawRules &rules,
    const Character &member,
    int partySize,
    double experience,
    int monsterMaxHp);
}
