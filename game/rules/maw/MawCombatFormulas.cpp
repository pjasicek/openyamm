#include "game/rules/maw/MawCombatFormulas.h"

#include "game/rules/maw/MawBalanceModel.h"

#include <algorithm>
#include <cmath>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
struct BuffPower
{
    int spellId;
    double base;
    double scaling;
};

// The live buffPower table (Global/zzMaw_Mapping.lua): equal at every mastery.
constexpr std::array<BuffPower, 19> BuffPowers = {{
    {3, 20, 2},   // Fire Resistance
    {5, 10, 2},   // Haste
    {14, 20, 2},  // Air Resistance
    {17, 15, 3},  // Shield
    {25, 20, 2},  // Water Resistance
    {28, 15, 3},  // Empower Magic
    {36, 20, 2},  // Earth Resistance
    {38, 20, 2},  // Stone Skin
    {46, 20, 2},  // Bless
    {47, 5, 1},   // Fate
    {51, 15, 3},  // Heroism
    {56, 10, 2},  // Meditation
    {58, 20, 2},  // Mind Resistance
    {69, 20, 2},  // Body Resistance
    {71, 5, 2},   // Regeneration
    {73, 15, 3},  // Hammerhands
    {83, 20, 2},  // Day of the Gods
    {85, 20, 2},  // Day of Protection
    {86, 10, 2},  // Hour of Power
}};

constexpr int SpellHaste = 5;
constexpr int SpellShield = 17;
constexpr int SpellFate = 47;

// monsterSpellMultiplierList (General/zzMaw-Monsters.lua). Ice Blast is listed twice there; the later 0.75 is the
// value MAW plays with.
constexpr std::array<std::pair<uint32_t, double>, 22> MonsterSpellMultipliers = {{
    {2, 0.75},   // Fire Bolt
    {6, 0.5},    // Fireball
    {9, 0.3},    // Meteor Shower
    {11, 1.35},  // Incinerate
    {15, 0.5},   // Sparks
    {18, 0.95},  // Lightning Bolt
    {20, 0.8},   // Implosion
    {24, 0.5},   // Poison Spray
    {29, 1.15},  // Acid Burst
    {32, 0.75},  // Ice Blast
    {37, 0.85},  // Deadly Swarm
    {39, 1.1},   // Blades
    {41, 0.6},   // Rock Blast
    {44, 0.4},   // Mass Distortion
    {52, 0.65},  // Spirit Lash
    {59, 0.8},   // Mind Blast
    {65, 1.25},  // Psychic Shock
    {70, 0.75},  // Harm
    {78, 1.1},   // Light Bolt
    {90, 1.15},  // Toxic Cloud
    {93, 0.4},   // Shrapmetal
    {97, 0.7},   // Dragon Breath
}};

constexpr size_t FireResistance = 0;
constexpr size_t AirResistance = 1;
constexpr size_t WaterResistance = 2;
constexpr size_t EarthResistance = 3;
constexpr size_t MindResistance = 4;
constexpr size_t BodyResistance = 5;
// A base resistance this high is an immunity (Lich and Vampire races).
constexpr int ImmuneResistance = 65000;

// damageKindResistance: which player resistances a damage type is measured against; the weakest one counts.
std::vector<size_t> resistancesAgainst(CombatDamageType type)
{
    switch (type)
    {
        case CombatDamageType::Fire:
            return {FireResistance};
        case CombatDamageType::Air:
            return {AirResistance};
        case CombatDamageType::Water:
            return {WaterResistance};
        case CombatDamageType::Earth:
            return {EarthResistance};
        case CombatDamageType::Spirit:
        case CombatDamageType::Mind:
            return {MindResistance};
        case CombatDamageType::Body:
            return {BodyResistance};
        case CombatDamageType::Light:
            return {MindResistance, BodyResistance};
        case CombatDamageType::Dark:
            return {FireResistance, AirResistance, WaterResistance, EarthResistance};
        case CombatDamageType::Energy:
            return {FireResistance, AirResistance, WaterResistance, EarthResistance, MindResistance, BodyResistance};
        case CombatDamageType::Physical:
        case CombatDamageType::Irresistible:
            break;
    }

    return {};
}
}

double mawRound(double value)
{
    return std::floor(value + 0.5);
}

int mawStatEffect(int value)
{
    if (value >= 25)
    {
        return value / 5;
    }

    // 21-24 -> 4, 19-20 -> 3, ... 3-4 -> -5, 0-2 -> -6.
    static constexpr std::array<std::pair<int, int>, 11> Table = {{
        {21, 4}, {19, 3}, {17, 2}, {15, 1}, {13, 0}, {11, -1}, {9, -2}, {7, -3}, {5, -4}, {3, -5}, {0, -6},
    }};

    for (const auto &[threshold, effect] : Table)
    {
        if (value >= threshold)
        {
            return effect;
        }
    }

    return -6;
}

int mawAverageOfTwoRolls(int first, int second)
{
    return int(mawRound((first + second) / 2.0));
}

double mawMonsterResistanceDivisor(int resistance)
{
    return std::pow(2.0, double(std::max(0, resistance) % 1000) / 100);
}

MawCrit mawCrit(const MawCritInputs &inputs)
{
    const double level = inputs.referenceLevel;
    const double diminishing = std::min(250 + 2.5 * level, inputs.madness ? 3000.0 : 2000.0);
    MawCrit crit;
    crit.chance = inputs.luck / std::min(500 + 5 * level, 3000.0) + 0.05;
    crit.multiplier = inputs.kind == MawCritKind::Spell
        ? inputs.intellect / (4 * diminishing) + 1.5
        : inputs.accuracy / diminishing + 1.5;
    crit.multiplier = mawRound(crit.multiplier * 100) / 100;

    if (inputs.kind == MawCritKind::Weapon)
    {
        for (double daggerSkill : inputs.masterDaggerSkills)
        {
            if (daggerSkill > 0)
            {
                crit.chance += 0.05 + 0.01 * daggerSkill / std::min(1 + level / 200, 4.0);
            }
        }

        crit.multiplier += 0.01 * inputs.grandmasterAxeSkill;
    }

    if (inputs.fateSkill)
    {
        crit.chance += mawBuffMultiplier(SpellFate, *inputs.fateSkill, inputs.buffScale);
    }

    crit.chance -= inputs.chancePenalty;
    crit.multiplier = (crit.multiplier - 1) * (1 - inputs.multiplierReduction) + 1;
    crit.chance = inputs.overcrit ? crit.chance + 0.1 : std::min(crit.chance, 1.0);
    return crit;
}

double mawBuffMultiplier(int spellId, double casterSkill, double buffScale)
{
    for (const BuffPower &buff : BuffPowers)
    {
        if (buff.spellId == spellId)
        {
            return (buff.base / 100 + buff.scaling * casterSkill / 1000) * buffScale;
        }
    }

    return 0;
}

double mawPartyHitChance(double attack, int monsterLevel, std::optional<double> blessSkill, MawBalanceModel &model)
{
    const double overPar = (7.5 + attack) / (model.attack(monsterLevel) + 10) - 1;
    const double blessBonus = blessSkill ? 0.05 + 0.05 * std::min(*blessSkill, 50.0) / 50 : 0;
    return std::clamp(0.75 + overPar * 0.5 + blessBonus, 0.25, 1.0);
}

double mawChanceToBeHit(double speed, int monsterLevel, MawBalanceModel &model)
{
    return 1 / (1 + speed / (100 + model.stat(monsterLevel)) * 0.5);
}

double mawGrandmasterDodgeChance(double dodgingSkill, bool grandmaster)
{
    return grandmaster ? 1 - 1 / (1 + (dodgingSkill + 10) / 200) : 0;
}

double mawMitigatedDamage(const MawMitigationInputs &inputs)
{
    const double input = inputs.damage;
    const double level = inputs.attackerLevel;
    // MAW applies the Grandmaster Shield cut a second time to non-physical hits (COMBAT_SPEC §13); we apply it once.
    double damage = inputs.grandmasterShield ? input * 0.85 : input;
    const auto withFloor = [&inputs, input](double value)
    {
        const double floored = std::max(value, 0.1 * input) * inputs.legendaryMultiplier;
        return inputs.flatReduction > 0 ? std::max(floored - inputs.flatReduction, 0.25 * floored) : floored;
    };

    if (inputs.type == CombatDamageType::Physical)
    {
        damage = mawRound(damage / (inputs.armorClass / mawArmorDivisor(level) + 1));
        damage /= 1 + inputs.physicalCutSkill / 100;

        if (inputs.shieldingEnchantment)
        {
            damage *= 0.85;
        }

        return withFloor(damage);
    }

    damage /= 1 + inputs.magicCutSkill / 100;

    if (inputs.shieldBuffSkill)
    {
        damage *= std::max(1 - mawBuffMultiplier(SpellShield, *inputs.shieldBuffSkill, inputs.buffScale), 0.7);
    }

    const std::vector<size_t> resistances = resistancesAgainst(inputs.type);

    if (resistances.empty())
    {
        return withFloor(mawRound(damage));
    }

    double taken = -1;
    int weakestBase = 0;

    for (size_t resistance : resistances)
    {
        const double base = inputs.resistances[resistance];
        const double item = inputs.itemResistances[resistance];
        const double candidate = 1 / (base / mawResistanceDivisor(level) + 1) / (item / 100 + 1);

        if (candidate > taken)
        {
            taken = candidate;
            weakestBase = inputs.resistances[resistance];
        }
    }

    if (weakestBase >= ImmuneResistance)
    {
        return 0;
    }

    return withFloor(mawRound(damage * taken));
}

int mawItemRecovery(int baseRecovery, int itemLevel, bool twoHanded)
{
    double recovery = mawRound(baseRecovery * (0.75 + std::min(itemLevel, 600) / 500.0) / 10) * 10;

    if (twoHanded)
    {
        recovery = mawRound(recovery * 1.25 / 10) * 10;
    }

    return int(recovery);
}

MawAttackDelay mawAttackDelay(const MawAttackDelayInputs &inputs)
{
    const double baseRecovery = inputs.baseRecovery > 0 ? inputs.baseRecovery : 100;
    double scale = 1 / ((100 + inputs.bonusPercent) / 100) / inputs.swiftness;
    scale *= 1 + inputs.armorImpairmentPercent / 100;

    if (inputs.hasteSkill)
    {
        scale /= std::max(1 + mawBuffMultiplier(SpellHaste, *inputs.hasteSkill, inputs.buffScale), 1.0);
    }

    const double before = mawRound(100 * scale);
    MawAttackDelay delay;
    delay.delay = int(mawRound(baseRecovery * scale));
    delay.damageMultiplier = before > 0 ? delay.delay / before : 1;
    return delay;
}

double mawSpeedRecoveryBonus(double speed)
{
    return speed <= 21 ? (speed - 13) / 4 : std::floor(speed / 10);
}

int mawSpellDelay(const MawSpellDelayInputs &inputs)
{
    const double haste = std::floor(inputs.speed / 20);
    const double hasteDivisor = inputs.hasteSkill
        ? std::max(1 + mawBuffMultiplier(SpellHaste, *inputs.hasteSkill, inputs.buffScale), 1.0)
        : 1;
    const double enchantment = inputs.spellSpeedEnchantment ? 1.1 : 1;
    const double armor = 1 + inputs.armorImpairmentPercent / 100;
    const double delay = mawRound(
        inputs.tableDelay / (1 + haste / 100) * std::pow(1.015, inputs.ascensionSkill) / hasteDivisor / enchantment)
        * armor;
    return int(mawRound(delay));
}

double mawSpellDiceScale(double ascensionSkill)
{
    return (1 + 0.02 * ascensionSkill) * std::pow(1.02, ascensionSkill);
}

double mawSpellAddScale(double ascensionSkill)
{
    return (1 + 0.01 * ascensionSkill * ascensionSkill) * std::pow(1.02, ascensionSkill);
}

MawSpellDice mawAscendedSpellDice(const MawSpellDice &base, double ascensionSkill, double empowerMultiplier)
{
    MawSpellDice dice;
    dice.diceMin = int(mawRound(base.diceMin * empowerMultiplier));
    dice.diceMax = int(mawRound(
        base.diceMax * empowerMultiplier * mawSpellDiceScale(ascensionSkill) * MawSpellDamageMultiplier));
    dice.add =
        int(mawRound(base.add * empowerMultiplier * mawSpellAddScale(ascensionSkill) * MawSpellDamageMultiplier));
    return dice;
}

double mawMonsterSpellMultiplier(uint32_t spellId)
{
    for (const auto &[id, multiplier] : MonsterSpellMultipliers)
    {
        if (id == spellId)
        {
            return multiplier;
        }
    }

    return 1;
}

double mawDiceAverage(int diceRolls, int diceSides, int bonus)
{
    return bonus + diceRolls * (diceSides + 1) / 2.0;
}

double mawMonsterDamageSpread(int first, int second)
{
    return (first + second) / 200.0;
}

int mawBolsterAmount(const RulesetOptions &options)
{
    if (options.challengeMode == RulesetChallengeMode::Doom
        || options.challengeMode == RulesetChallengeMode::RoadToInsanity
        || options.challengeMode == RulesetChallengeMode::BeyondMadness)
    {
        return 600;
    }

    static constexpr std::array<int, 6> ByDifficulty = {0, 70, 100, 150, 200, 300};
    return ByDifficulty[std::min<size_t>(size_t(options.difficulty), ByDifficulty.size() - 1)];
}

double mawFireAuraDamage(int mastery, double levelDamage, bool twoHanded)
{
    static constexpr std::array<double, 5> Share = {0, 0.10, 0.15, 0.20, 0.25};
    static constexpr std::array<double, 5> Minimum = {0, 3, 6, 12, 24};
    const size_t index = size_t(std::clamp(mastery, 0, 4));
    return std::max(levelDamage * Share[index], Minimum[index] * (twoHanded ? 2 : 1));
}

MawEnchantRange mawEnchantDamageRange(
    double levelDamage,
    double tableMinimum,
    double tableMaximum,
    double coefficient,
    bool twoHanded)
{
    const double average = levelDamage * coefficient;
    const double mean = (tableMinimum + tableMaximum) / 2;
    const double floorShare = (twoHanded ? 2 : 1) * 0.5;
    MawEnchantRange range;
    range.minimum = std::max(average * tableMinimum / mean, tableMinimum * floorShare);
    range.maximum = std::max(average * tableMaximum / mean, tableMaximum * floorShare);
    return range;
}

const MawDamageEnchant *mawDamageEnchant(uint16_t special)
{
    static constexpr std::array<MawDamageEnchant, 14> Enchants = {{
        {4, 3, 4, 0.2, CombatDamageType::Water},
        {5, 9, 12, 0.3, CombatDamageType::Water},
        {6, 18, 24, 0.4, CombatDamageType::Water},
        {7, 2, 5, 0.2, CombatDamageType::Air},
        {8, 6, 15, 0.3, CombatDamageType::Air},
        {9, 12, 30, 0.4, CombatDamageType::Air},
        {10, 1, 6, 0.2, CombatDamageType::Fire},
        {11, 3, 18, 0.3, CombatDamageType::Fire},
        {12, 6, 36, 0.4, CombatDamageType::Fire},
        {13, 5, 5, 0.25, CombatDamageType::Body},
        {14, 12, 12, 0.35, CombatDamageType::Body},
        {15, 24, 24, 0.45, CombatDamageType::Body},
        {39, 20, 40, 0.5, CombatDamageType::Fire, true, false},
        {46, 20, 40, 0.5, CombatDamageType::Fire, false, true},
    }};

    for (const MawDamageEnchant &enchant : Enchants)
    {
        if (enchant.special == special)
        {
            return &enchant;
        }
    }

    return nullptr;
}
}
