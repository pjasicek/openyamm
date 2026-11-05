#pragma once

#include "game/rules/SkillRules.h"
#include "game/rules/maw/MawSkillFormulas.h"

#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class MawRules;

// MAW's skill economy (devdocs/maw/TRAINERS_SKILLS.md §2, §4): weapons, schools and the racial abilities share their
// raise cost, teachers of the horizontal skills want more skill and charge by mode and by the masteries the character
// already holds, and masteries a respec took return on their own.
class MawSkillRules : public SkillRules
{
public:
    explicit MawSkillRules(MawRules &rules);

    std::string skillDisplayName(const Character &character, const std::string &canonicalSkill) const override;
    uint32_t skillRaiseCost(const Character &character, const std::string &canonicalSkill) const override;
    // Cover at training halls, Mana Shield and Enlightenment at magic shops (skill_rules.yml `learned_at`).
    std::vector<std::string> extraHouseSkills(const std::string &houseType) const override;
    std::vector<std::pair<std::string, std::array<uint32_t, 3>>> teacherlessMasteryLadders() const override;
    // Alchemy 60, Cover 30, Mana Shield and Retaliation 50 (S:300-320).
    std::optional<uint32_t> skillLevelCap(const std::string &canonicalSkill) const override;
    // In MAW's order (S:348-364): a mastery a respec took returns, Cover at its cap teaches Retaliation, and the four
    // new skills climb their mastery ladders within the class's limit.
    std::string afterSkillRaised(
        Character &character,
        const std::string &canonicalSkill,
        const ClassSkillTable *pClassSkillTable) const override;
    uint32_t masteryRequiredLevel(const std::string &canonicalSkill, SkillMastery mastery) const override;
    int masteryTeacherCost(
        const Character &character,
        const std::string &canonicalSkill,
        SkillMastery mastery,
        int standardCost) const override;

    // 1000 gold per level of the character (R:45-50).
    std::optional<int> skillResetCost(const Character &character) const override;
    // The shared set back to 1 at what it cost to raise, every other skill but Alchemy back to 1 at its triangular
    // cost; masteries are remembered; the character keeps at least the points its level-ups gave (R:58-137).
    bool resetSkills(Character &character) const override;

    // The resistance auras raise their paired stat, Bless Accuracy, by min(10 + s / 5, 20) % of it; Day of the Gods
    // every stat by min(10 + s / 7, 20) % (the stronger counts, IT:3039-3074).
    void applyStatBonuses(Character &member) const override;
    // Endurance adds its / 1000 share of the maximum HP, Bodybuilding 0.5-2 % per point; Enlightenment 0.5-2 % per
    // point of the maximum mana (IT:3097-3146).
    void applyResourceBonuses(Character &member) const override;
    std::optional<CharacterCombatRows> combatRows(
        const Character &character,
        const ItemTable *pItemTable,
        const CharacterStatValues &stats) const override;
    // MAW regenerates continuously (updateRegeneration), not by Standard's ticks.
    float regenerationHealthPerSecond(const Character &member) const override;
    int meditationSpellPointsPerTick(const Character &member) const override;
    // Every member regenerates HP by Regeneration and SP by Meditation each frame (MawRegen, COMBAT_SPEC §8.4).
    void updateRegeneration(Party &party, const IGameplayWorldRuntime &world, float deltaSeconds) const override;
    bool followerSkillBonusesStack() const override;
    // MAW's coloured stats menu (ColouredStats, on by default; zzMaw-Items.lua:1438-1451).
    std::optional<uint32_t> statLabelRgb(const std::string &statName) const override;
    // Scholar, Teacher and Instructor give Ascension +2/+4/+6, to members who have learned it (NPCFollowersSkills.lua,
    // MAW 1a0a6168, db72a6d5).
    int followerSkillBonus(uint32_t professionId, const std::string &canonicalSkill, int tableBonus) const override;
    bool followerSkillBonusNeedsSkill(const std::string &canonicalSkill) const override;
    // Any member's skill x mastery against the monster's level less the party's average level, or a Grandmaster;
    // the highest mastery decides what is shown (zzMAW-Skills.lua, CanIdentifyMonster).
    IdentifyMonsterReveal identifyMonsterReveal(const Party &party, int monsterLevel) const override;
    // MAW's skill texts (data/texts.yml, TRAINERS_SKILLS.md §7) with the character's numbers.
    SkillTooltipText skillTooltip(
        const Party &party,
        const Character &character,
        const std::string &canonicalSkill,
        const SkillTooltipText &table) const override;
    // MAW's stat popups (zzMaw-Stats.lua BuildStatInformationBox) against the party's total level.
    std::string statTooltip(
        const Party &party,
        const Character &character,
        const std::string &statName,
        const std::string &table) const override;
    // The stats page's M/R/S powers and Vitality, in four rows where Condition and Quick Spell were; "Bow off" in the
    // Shoot rows with the Bow preference off.
    std::optional<CharacterStatRowText> statRowText(
        const Party &party,
        const Character &character,
        const std::string &statName) const override;
    std::array<std::optional<CharacterStatRowText>, 4> statRows(
        const Party &party,
        const Character &character) const override;
    bool compactStatPowerRows() const override;
    // Against monsters of the party's level, as the resistance popups say; green when an item's resistance enchantment
    // raises it (vars.normalEnchantResistance).
    std::optional<CharacterResistanceCut> resistanceCut(
        const Party &party,
        const Character &character,
        const std::string &statName) const override;
    std::array<std::optional<CharacterResistanceCut>, 6> resistanceCuts(
        const Party &party,
        const Character &character) const override;
    // Numbers of 10000 or more read like MAW's (shortenNumber: 3 digits and K/M/B), so they fit the page.
    std::string statValueText(const std::string &text) const override;
    // Every number of 100 or more becomes the price; the first one equal to the vanilla requirement (4, 7, 10), else
    // the first one up to 12, becomes the requirement; a line naming both is added when either is missing
    // (S:1876-1949).
    std::string teacherSpeech(
        const std::string &text,
        const std::string &canonicalSkill,
        SkillMastery mastery,
        uint32_t requiredLevel,
        int price) const override;
    // Road to Insanity and Beyond Madness: the expected skill of the trainee's level + 4 (zzMAW-Skills.lua:1645-1660).
    float trainingPriceMultiplier(const Character &trainee, float houseMultiplier) const override;
    std::optional<SkillRaiseCost> skillRaiseCostDetail(
        const Character &character,
        const std::string &canonicalSkill) const override;

    MawSkillMode skillMode() const;
    MawPriceMode priceMode() const;

private:
    // A member's HP and SP per second from skills, auras and potions, before the out-of-combat multipliers.
    std::pair<double, double> regenerationPerSecond(const Party &party, size_t index) const;
    // A mastery a respec took comes back, one rank per raise, once the skill reaches that rank's requirement.
    std::string restoreRememberedMastery(
        Character &character,
        CharacterSkill &skill,
        const ClassSkillTable *pClassSkillTable) const;

    // A switch to horizontal progression takes the masteries of skills 0-23 their levels no longer reach; the way
    // back gives them all back (S:1976-2011).
    void applyProgressionMasteries(Party &party) const;
    // A lone character's utility skills take the mastery their base level reaches (thresholds 1, 4, 7, 10), up or
    // down and whatever the class allows; the old ones come back when the party grows (S:2126-2168).
    void applySoloMasteries(Party &party) const;

    MawRules &m_rules;
    // Runtime: whether horizontal progression was in force at the last update.
    mutable std::optional<bool> m_horizontalApplied;
    // Runtime: time since the last regeneration tick.
    mutable float m_regenerationSeconds = 0.0f;
};

// The Shaman, Seraphim, Death Knight and Thief lines share only magic raise costs.
bool mawIsHybridClass(const std::string &className);
}
