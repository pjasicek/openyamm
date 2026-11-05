#pragma once

#include "game/content/RulesetOptions.h"

#include <array>
#include <cstdint>
#include <unordered_map>

namespace OpenYAMM::Game
{
// The settings that choose MAW's numbers: its difficulty index 1-9 and the mode flags of a game
// (devdocs/maw/BALANCE_MODEL.md §2.2).
struct MawModelConfig
{
    // 1 Easy, 2 Normal, 3 MAW, 4 Hard, 5 Hell, 6 Nightmare, 7 Doom, 8 Road to Insanity, 9 Beyond Madness.
    int difficulty = 3;
    // Doom, Road to Insanity and Beyond Madness ("Mode 2"), Road to Insanity and Beyond Madness, and Beyond Madness.
    bool doomMode = false;
    bool insanityMode = false;
    bool madnessMode = false;
    bool austerity = false;
    // Nightmare chosen for good (MAW's typed "yes"; our Nightmare is always this).
    bool trueNightmare = false;
    int partyCount = 5;
};

MawModelConfig mawModelConfig(const RulesetOptions &options, int partyCount);

// What a character's armour class and resistances are divided by against an attacker of the given level
// (Formulas.armorDamageTaken / resistanceDamageTaken: AC / (200 + L), resistance / (100 + L)).
inline double mawArmorDivisor(double attackerLevel)
{
    return 200 + attackerLevel;
}

inline double mawResistanceDivisor(double attackerLevel)
{
    return 100 + attackerLevel;
}

// Which of the expected character's defences a monster's damage is sized against (getPlayerEstimatedVitality's
// damageKind): physical attacks against armour only, every other kind against resistances only, and Blended half and
// half (traps, and readings without an attack).
enum class MawDamageClass
{
    Blended,
    Physical,
    Magic,
};

// MAW's balance model (devdocs/maw/BALANCE_MODEL.md §1-3): the character a party member of a given level is expected
// to be, from the same item, skill and buff curves the MAW rules use, and the monster numbers sized against it.
// Pure: it depends only on the level and the configuration. Levels may be fractional.
class MawBalanceModel
{
public:
    explicit MawBalanceModel(const MawModelConfig &config);

    const MawModelConfig &config() const;

    // The expected character.
    double skill(double level) const;
    int mastery(double level) const;
    double stat(double level);
    double gearedFraction(double level);
    double maxEnchantStrength(double level) const;
    double health(double level);
    double mana(double level);
    double armorClass(double level);
    double resistance(double level);
    double enchantResistance(double level) const;
    double physicalDamageTaken(double level);
    double magicDamageTaken(double level);
    double chanceToBeHit(double level);
    double legendaryDamageTaken(double level) const;
    double coverMultiplier(double level) const;
    double vitality(double level, MawDamageClass damageClass = MawDamageClass::Blended);
    double attack(double level);
    double power(double level);
    double spellPower(double level);

    // A B-tier, non-boss monster of a family whose B row resolves to this level.
    double monsterHealth(double level);
    double monsterDamage(double level, MawDamageClass damageClass = MawDamageClass::Blended);
    // Experience multiplier for the difficulty's monster density.
    double monsterExperienceMultiplier() const;

    // A mastery-indexed MAW table (entries 0-4, each possibly missing).
    struct MasteryTable;

    // Shared helpers the combat rules also use.
    static int statisticEffect(double value);
    double masteryThreshold(int index) const;
    int masteryForSkill(double skill) const;
    // GetGradualMasteryValue (zzMaw-Stats.lua:1480-1495): a rank's value ramps up from the previous rank's between the
    // mastery thresholds, Grandmaster's to 1.4 x its threshold. `perMastery` holds Novice to Grandmaster.
    double gradualSkillValue(const std::array<double, 4> &perMastery, double skill, int mastery) const;
    // getWeaponLevelDamage (Estimates.lua:145-158): the average damage a weapon of this level adds, with the expected
    // Armsmaster, weapon skill and might of its level; what damage enchantments and Fire Aura scale with.
    double weaponLevelDamage(double itemLevel, bool twoHanded, double weaponFlat);

    // The levels the model keeps computed numbers for (whole levels only).
    size_t cachedLevelCount() const;

private:
    double gradualMasteryValue(const MasteryTable &table, double skill, int mastery) const;
    double gradualRow(const MasteryTable &table, double skill, int mastery) const;
    double buffRamp(double skill) const;
    double buffFlat(int spellId, double skill, int mastery, double level, double levelDivisor = 4) const;
    double buffMult(int spellId, double skill, int mastery) const;
    double lootTier(double level) const;
    double enchantStrengthCurve(double tier) const;
    double expectedEnchantFraction(double lootTier, double drops, int difficulty) const;
    double wornArmor(double level);

    MawModelConfig m_config;
    std::unordered_map<double, double> m_gearedCache;
    std::unordered_map<double, double> m_statCache;
    std::unordered_map<double, double> m_healthCache;
};
}
