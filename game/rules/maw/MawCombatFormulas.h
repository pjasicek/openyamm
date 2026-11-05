#pragma once

#include "game/content/RulesetOptions.h"
#include "game/gameplay/GameMechanics.h"

#include <array>
#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
class MawBalanceModel;

// MAW's per-hit formulas (devdocs/maw/COMBAT_SPEC.md §2, §4, §6.7, §7.4). Pure: every input is passed in, every
// random draw is done by the caller, so the worked examples of §11 can be checked exactly.

// MAW's `round`: halves go up.
double mawRound(double value);

// A statistic's effect (§2.1): floor(v / 5) from 25, the vanilla table below.
int mawStatEffect(int value);

// A damage roll: the mean of two draws from min to max, rounded (stage 17 and the class replacements).
int mawAverageOfTwoRolls(int first, int second);

// Monster resistances are read modulo 1000; a hit is divided by 2^(resistance / 100).
double mawMonsterResistanceDivisor(int resistance);

enum class MawCritKind
{
    Weapon,
    Spell,
};

struct MawCritInputs
{
    MawCritKind kind = MawCritKind::Weapon;
    double luck = 0;
    double accuracy = 0;
    double intellect = 0;
    // The target's level for weapon hits; spells and enchantments pass the party's total banked level.
    double referenceLevel = 0;
    bool madness = false;
    // Weapon hits: Dagger skill of each hand that holds a dagger at Master or above (0 for none).
    std::array<double, 2> masterDaggerSkills = {};
    // Weapon hits: Axe skill when the first axe-holding hand has Axe at Grandmaster (0 for none).
    double grandmasterAxeSkill = 0;
    // Fate active: the better of the Fate caster skill and the Hour of Power caster skill / 1.5.
    std::optional<double> fateSkill;
    // Dimension affix 33: buff strengths, base and per-skill scaling alike, times this (MawRules::buffScale).
    double buffScale = 1;
    // A dimension map's affixes: the chance less this, and this share off the multiplier's bonus.
    double chancePenalty = 0;
    double multiplierReduction = 0;
    // Legendary 14: +10 % and no cap at 100 % (the share above it multiplies the damage, see the callers).
    bool overcrit = false;
};

struct MawCrit
{
    double chance = 0;
    // Rounded to two decimals, as MAW does.
    double multiplier = 1;
};

// getCritInfo (§2.2).
MawCrit mawCrit(const MawCritInputs &inputs);

// A buff's strength under the buff rework: base / 100 + scaling x skill / 1000 (§2.5), with dimension affix 33's
// `buffScale` on both terms.
double mawBuffMultiplier(int spellId, double casterSkill, double buffScale = 1);

// The chance a party member's weapon or arrow hits a monster of this level (§2.3); `blessSkill` is the Bless caster
// skill when Bless is active.
double mawPartyHitChance(double attack, int monsterLevel, std::optional<double> blessSkill, MawBalanceModel &model);

// The chance a monster's attack reaches a party member with this Speed (§7.1).
double mawChanceToBeHit(double speed, int monsterLevel, MawBalanceModel &model);

// The dodge chance of a Grandmaster in Dodging (§7.4); 0 below Grandmaster.
double mawGrandmasterDodgeChance(double dodgingSkill, bool grandmaster);

// The party member side of a hit (calcMawDamage, §2.4). Resistances are by player resistance: fire, air, water,
// earth, mind, body.
struct MawMitigationInputs
{
    double damage = 0;
    CombatDamageType type = CombatDamageType::Physical;
    // The level the attacker's hit is measured against: the monster's level, or the victim's own level for traps.
    double attackerLevel = 0;
    int armorClass = 0;
    std::array<int, 6> resistances = {};
    // The best item resistance enchantment per element, by the same index (Character::itemResistanceEnchants).
    std::array<int, 6> itemResistances = {};
    bool grandmasterShield = false;
    // "of Shielding" worn: physical damage x0.85.
    bool shieldingEnchantment = false;
    // The Shield buff's caster skill when Shield is active.
    std::optional<double> shieldBuffSkill;
    double buffScale = 1;
    // Class cuts (classCut): physical hits divided by 1 + skill / 100 (Shaman Air, Death Knight Blood), other hits
    // likewise (Shaman Air, Death Knight Unholy).
    double physicalCutSkill = 0;
    double magicCutSkill = 0;
    // Legendaries 18 and 22: their cut, after the floor and before the flat reduction (applyPostMitigation,
    // ST:762-776).
    double legendaryMultiplier = 1;
    // The Seraphim's and Shaman's flat reduction after the floor; it leaves at least a quarter of the hit.
    double flatReduction = 0;
};

// The hit after armour or resistance; a float the caller truncates. 0 for an immune character.
double mawMitigatedDamage(const MawMitigationInputs &inputs);

// Base recovery of a weapon (getItemRecovery, §4.1); `baseRecovery` is the skill's (Bow 100, Sword 80, ...).
int mawItemRecovery(int baseRecovery, int itemLevel, bool twoHanded);

struct MawAttackDelayInputs
{
    // The average base recovery of the weapons used (100 without one), unrounded: two weapons may average a half.
    double baseRecovery = 100;
    // Skill, Armsmaster, Speed and class bonuses, in percent.
    double bonusPercent = 0;
    // Swiftness (specials 41 and 59): 1 + 0.15 per one-handed and 0.3 per two-handed weapon that has it.
    double swiftness = 1;
    // Offhand and body armour impairment, in percent.
    double armorImpairmentPercent = 0;
    std::optional<double> hasteSkill;
    double buffScale = 1;
};

struct MawAttackDelay
{
    int delay = 100;
    // Slow weapons hit harder: the delay over the delay of a recovery-100 weapon.
    double damageMultiplier = 1;
};

// events.GetAttackDelay (§4.2), without the per-class terms.
MawAttackDelay mawAttackDelay(const MawAttackDelayInputs &inputs);

// The Speed bonus to attack recovery, in percent.
double mawSpeedRecoveryBonus(double speed);

struct MawSpellDelayInputs
{
    // The spell table's recovery at the caster's mastery.
    int tableDelay = 0;
    double speed = 0;
    // Ascension (Learning) skill for damage, healing and crowd-control spells, 0 for the rest.
    double ascensionSkill = 0;
    double armorImpairmentPercent = 0;
    std::optional<double> hasteSkill;
    double buffScale = 1;
    // Special 40 in any weapon slot.
    bool spellSpeedEnchantment = false;
};

// getSpellDelay (§4.3) for an ordinary spell.
int mawSpellDelay(const MawSpellDelayInputs &inputs);

struct MawSpellDice
{
    int diceMin = 0;
    int diceMax = 0;
    int add = 0;
};

// Ascension's growth of a damage spell's dice and of its flat damage (Formulas.spellDiceScale, spellAddScale).
double mawSpellDiceScale(double ascensionSkill);
double mawSpellAddScale(double ascensionSkill);

// Every damage spell's dice and flat damage are cut to this share (Formulas.spellDamageMult, MAW fa1ff481).
constexpr double MawSpellDamageMultiplier = 0.7;

// ascendSpellDamage (§6.7): the spell's dice and flat damage at an Ascension skill, with MawSpellDamageMultiplier.
// `empowerMultiplier` is 1 + the Empower Magic aura's multiplier when it is active.
MawSpellDice mawAscendedSpellDice(const MawSpellDice &base, double ascensionSkill, double empowerMultiplier = 1);

// Monster spell damage relative to the monster's attack (monsterSpellMultiplierList, §7.4); 1 for unlisted spells.
double mawMonsterSpellMultiplier(uint32_t spellId);

// A monster attack's average table damage; attack 2 deals the model damage times the ratio of the averages (§7.4).
double mawDiceAverage(int diceRolls, int diceSides, int bonus);

// The random spread on a monster's hit: (R(75, 125) + R(75, 125)) / 200.
double mawMonsterDamageSpread(int first, int second);

// MAW's Game.BolsterAmount for the options: Easy 0, Normal 70, MAW 100, Hard 150, Hell 200, Nightmare 300; Doom and
// the madness modes 600 (data/difficulty.yml).
int mawBolsterAmount(const RulesetOptions &options);

// Fire Aura's fire on one weapon before its pace and Legendary 19 (calcFireAuraDamage, IT:4287-4318): the weapon's
// level damage x 10/15/20/25 % by the holder's mastery, at least 3/6/12/24 (twice on two-handed weapons).
double mawFireAuraDamage(int mastery, double levelDamage, bool twoHanded);

// A damage enchantment's roll range (enchantDamageRange, IT:2067-2081): its average is the weapon's level damage x
// the enchantment's coefficient, shaped like its table range; the table range at half (whole for two-handed weapons)
// is a floor.
struct MawEnchantRange
{
    double minimum = 0;
    double maximum = 0;
};

MawEnchantRange mawEnchantDamageRange(
    double levelDamage,
    double tableMinimum,
    double tableMaximum,
    double coefficient,
    bool twoHanded);

// MAW's damage enchantments by special enchantment id (enchantbonusdamage, IT:2047-2061): the table range, the share of
// the weapon's level damage they deal on average, their element, and whether they work on spells only (39) or on
// weapons only (46).
struct MawDamageEnchant
{
    uint16_t special = 0;
    double minimum = 0;
    double maximum = 0;
    double coefficient = 0;
    CombatDamageType type = CombatDamageType::Fire;
    bool spellOnly = false;
    bool weaponOnly = false;
};

// Null for a special that is not a damage enchantment.
const MawDamageEnchant *mawDamageEnchant(uint16_t special);
}
