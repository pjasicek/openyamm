#include "game/rules/maw/MawBalanceModel.h"

#include "game/rules/maw/MawCombatFormulas.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
// MAW's tables are Lua tables where a missing entry reads as nil; `present` keeps that distinction for the gradual
// mastery ramp, which falls back on neighbouring entries.
struct MawBalanceModel::MasteryTable
{
    std::array<double, 5> values = {};
    std::array<bool, 5> present = {};

    double at(int index, double fallback) const
    {
        return index >= 0 && index < 5 && present[size_t(index)] ? values[size_t(index)] : fallback;
    }
};

namespace
{
using MasteryTable = MawBalanceModel::MasteryTable;

// The model caches whole levels only: callers also pass fractional ones (a member's level from their experience, the
// party's banked level), which would grow the caches with every kill (ROB-2-6).
bool wholeLevel(double level)
{
    return level == std::floor(level);
}

// {a, b, c, d}: entries 1-4, no entry 0.
MasteryTable oneBased(std::initializer_list<double> values)
{
    MasteryTable table;
    size_t index = 1;

    for (double value : values)
    {
        table.values[index] = value;
        table.present[index] = true;
        ++index;
    }

    return table;
}

// {[0] = z, a, b, c, d}.
MasteryTable zeroBased(std::initializer_list<double> values)
{
    MasteryTable table;
    size_t index = 0;

    for (double value : values)
    {
        table.values[index] = value;
        table.present[index] = true;
        ++index;
    }

    return table;
}

// zzMAW-Skills.lua tables the model reads (sword and chain stand for every weapon and armour).
const MasteryTable ArmsmasterDamage = zeroBased({0, 0, 1, 1, 1.5});
const MasteryTable ArmsmasterSpeed = zeroBased({0, 0, 0, 1, 1});
const MasteryTable ArmsmasterAttack = zeroBased({0, 1, 1, 1, 1});
const MasteryTable SwordAttack = zeroBased({0, 1, 2, 3, 4});
const MasteryTable SwordRecovery = zeroBased({0, 0, 1, 1, 2});
const MasteryTable ChainItemArmor = zeroBased({0, 3, 4, 5, 6});
const MasteryTable ChainItemResistance = zeroBased({0, 1, 2, 3, 4});
const MasteryTable BodybuildingHealth = zeroBased({0, 0.5, 1, 1.5, 2});
const MasteryTable BodybuildingFlatPerRank = oneBased({1, 2, 3});
const MasteryTable MeditationPerRank = oneBased({1, 2, 3, 5});
const MasteryTable EnlightenmentManaPerSkill = oneBased({0.5, 1, 1.5, 2});
const MasteryTable FireAuraDamage = zeroBased({0, 0.1, 0.15, 0.2, 0.25});
// Worthless at novice, phasing in across the expert band, whole from master on.
const MasteryTable CoverGate = oneBased({0, 1, 1, 1});

// Enchants on a fully geared character (ENCHANTS_PER_ITEM x TOTAL_SLOTS) and the share of them the model counts as
// a statistic (STAT_SHARE).
constexpr double EnchantsWorn = 3 * 13.75;
constexpr double EnchantStatShare = 0.2;
// How much more a covering tank survives than the member it covers (TANK_VITALITY_RATIO).
constexpr double TankVitalityRatio = 2;

constexpr double SwordSkillDamagePerPoint = 2;

// The buff table in play after the first map load (Global/zzMaw_Mapping.lua): base and per-skill scaling.
struct BuffPower
{
    int spellId;
    double base;
    double scaling;
};

constexpr std::array<BuffPower, 9> BuffPowers = {{
    {3, 20, 2},   // Fire Resistance (all six element buffs carry the same numbers)
    {5, 10, 2},   // Haste
    {17, 15, 3},  // Shield
    {38, 20, 2},  // Stone Skin
    {46, 20, 2},  // Bless
    {47, 5, 1},   // Fate
    {51, 15, 3},  // Heroism
    {83, 20, 2},  // Day of the Gods
    {86, 10, 2},  // Hour of Power
}};

const BuffPower *findBuff(int spellId)
{
    for (const BuffPower &buff : BuffPowers)
    {
        if (buff.spellId == spellId)
        {
            return &buff;
        }
    }

    return nullptr;
}

constexpr int SpellFireResistance = 3;
constexpr int SpellHaste = 5;
constexpr int SpellShield = 17;
constexpr int SpellStoneSkin = 38;
constexpr int SpellBless = 46;
constexpr int SpellFate = 47;
constexpr int SpellHeroism = 51;

double clamp01(double value)
{
    return std::min(std::max(value, 0.0), 1.0);
}

double legendaryRamp(double level)
{
    return clamp01((level - 100.0) / (420.0 - 100.0));
}

double powerFor(double itemLevel)
{
    return std::min(std::floor(std::max(itemLevel, 0.0) / 5.0), 100.0);
}

struct WeaponDamage
{
    double dice = 0;
    double flat = 0;
    double levelDamage = 0;
};

// getWeaponDamageForLevel: even points of item power buy flat damage, odd points dice. Its first return value is
// always dice + flat, so the model's (total - dice - flat) terms are 0 and left out.
WeaponDamage weaponDamageForLevel(double itemLevel, bool twoHanded, double flat)
{
    const double power = std::min(powerFor(itemLevel), 255.0);
    const double flatPower = std::floor(power / 2);
    const double powerFlat = 2 * flatPower;
    const double powerDice = 2 * 2 * (power - flatPower);
    WeaponDamage damage;
    damage.dice = 8 * 2 + powerDice;
    damage.flat = flat + powerFlat;
    damage.levelDamage = powerFlat + powerDice / 2;

    if (!twoHanded)
    {
        damage.dice /= 2;
        damage.flat /= 2;
        damage.levelDamage /= 2;
    }

    return damage;
}

double weaponFlat(double level)
{
    return std::min(level * 0.5, 16.0);
}

// Loot rarities in MAW's order (const.Rarity, 1-based).
enum Rarity
{
    Common = 1,
    Uncommon,
    Rare,
    Epic,
    Ancient,
    Primordial,
    Legendary,
    Celestial,
};

constexpr std::array<double, 10> RarityDifficultyMult = {0, 1, 1, 1, 1.1, 1.2, 1.4, 1.6, 1.8, 2};

// rarityBandMult for Epic, Rare and Uncommon by difficulty.
constexpr std::array<std::array<double, 3>, 10> RarityBandMult = {{
    {1, 1, 1},
    {1, 1, 1},
    {1, 1, 1},
    {1, 1, 1},
    {1.5, 1.4, 1.4},
    {2, 1.8, 1.6},
    {2.5, 2.2, 1.8},
    {3, 2.6, 2},
    {4, 3, 2.2},
    {5.5, 3.4, 2.4},
}};

double enchantChance(int rarity, double lootTier)
{
    switch (rarity)
    {
        case Epic:
            return std::min(5 + 0.75 * lootTier, 20.0);
        case Rare:
            return std::min(20 + 2 * lootTier, 60.0);
        case Uncommon:
            return std::min(60 + lootTier, 80.0);
        default:
            return 100;
    }
}

double rarityItemFraction(int rarity)
{
    const auto mean = [](int which)
    {
        switch (which)
        {
            case Celestial:
            case Primordial:
                return 25.0 / 20;
            case Ancient:
                return 22.5 / 20;
            case Legendary:
                return 18.0 / 20;
            default:
                return 14.0 / 20;
        }
    };
    const double enchants = rarity == Common ? 0 : rarity == Uncommon ? 1 : rarity == Rare ? 2 : 3;
    return enchants / 3 * mean(rarity) / mean(Primordial);
}

// The chance of each rarity for one drop (GetRarityDistribution).
std::array<double, 9> rarityDistribution(double lootTier, int difficulty)
{
    std::array<double, 9> widths = {};
    double total = 0;
    double previous = 0;

    for (int rarity = Epic; rarity >= Common; --rarity)
    {
        const double threshold = enchantChance(rarity, lootTier);
        const double bandMult = rarity == Epic ? RarityBandMult[size_t(difficulty)][0]
            : rarity == Rare                   ? RarityBandMult[size_t(difficulty)][1]
            : rarity == Uncommon               ? RarityBandMult[size_t(difficulty)][2]
                                               : 1.0;
        widths[size_t(rarity)] = std::max(threshold - previous, 0.0) * bandMult;
        total += widths[size_t(rarity)];
        previous = threshold;
    }

    std::array<double, 9> distribution = {};

    for (int rarity = Common; rarity <= Epic; ++rarity)
    {
        distribution[size_t(rarity)] = total > 0 ? widths[size_t(rarity)] / total : rarity == Common ? 1 : 0;
    }

    const double epic = distribution[Epic];
    const double mult = RarityDifficultyMult[size_t(difficulty)] * enchantChance(Uncommon, lootTier) / 80;
    double left = 1;

    for (const auto &[rarity, upgrade] : {std::pair{Celestial, 0.002}, std::pair{Legendary, 0.03},
                                          std::pair{Primordial, 0.04}, std::pair{Ancient, 0.12}})
    {
        const double chance = std::min(upgrade * mult, 1.0);
        distribution[size_t(rarity)] = epic * left * chance;
        left -= left * chance;
    }

    distribution[Epic] = epic * left;
    return distribution;
}

constexpr std::array<double, 10> DropsDensityByDifficulty = {1, 0.40, 0.40, 0.40, 0.43, 0.43, 0.47, 0.59, 0.66, 0.70};

double dropsSeenPerSlot(double level, double density)
{
    return (level / (3.6 + level / 140) + 1) * density;
}

constexpr std::array<double, 10> HitsToKillCharacter = {0, 14, 10, 7, 6.5, 6, 5.5, 5, 4.5, 4};
constexpr std::array<double, 10> HitsToKillCharacterAusterity = {0, 15, 10, 5, 4, 3, 2.5, 2, 1.5, 1};
constexpr std::array<double, 10> HitsToKillMonster = {0, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5};
constexpr std::array<double, 10> HitsToKillMonsterAusterity = {0, 1, 2, 4, 5, 6, 7, 8, 9, 9.5};

// Monster group sizes (Low and Hi) by difficulty.
constexpr std::array<std::array<double, 2>, 10> MonsterDensity = {{
    {1, 3},
    {1, 3},
    {1, 3},
    {1, 3},
    {1, 4},
    {1, 4},
    {2, 4},
    {2, 5},
    {3, 5},
    {3, 6},
}};
}

MawModelConfig mawModelConfig(const RulesetOptions &options, int partyCount)
{
    MawModelConfig config;
    config.partyCount = partyCount;
    config.difficulty = int(options.difficulty) + 1;
    // True Nightmare is the chosen difficulty only: the Doom modes play at Nightmare (rulesetChallengeModeDifficulty) but
    // MAW runs them at bolster 600 with its True Nightmare flag off.
    config.trueNightmare = options.difficulty == RulesetDifficulty::Nightmare
        && !rulesetChallengeModeDifficulty(options.challengeMode).has_value();
    config.austerity = options.challengeMode == RulesetChallengeMode::Austerity;

    switch (options.challengeMode)
    {
        case RulesetChallengeMode::Doom:
            config.difficulty = 7;
            config.doomMode = true;
            break;
        case RulesetChallengeMode::RoadToInsanity:
            config.difficulty = 8;
            config.doomMode = config.insanityMode = true;
            break;
        case RulesetChallengeMode::BeyondMadness:
            config.difficulty = 9;
            config.doomMode = config.insanityMode = config.madnessMode = true;
            break;
        default:
            break;
    }

    return config;
}

MawBalanceModel::MawBalanceModel(const MawModelConfig &config)
    : m_config(config)
{
    m_config.difficulty = std::clamp(m_config.difficulty, 1, 9);
}

const MawModelConfig &MawBalanceModel::config() const
{
    return m_config;
}

double MawBalanceModel::masteryThreshold(int index) const
{
    static constexpr std::array<double, 4> Normal = {0, 4, 7, 10};
    static constexpr std::array<double, 4> Insanity = {0, 8, 16, 25};
    static constexpr std::array<double, 4> Madness = {0, 10, 24, 40};
    const std::array<double, 4> &thresholds = m_config.madnessMode ? Madness
        : m_config.insanityMode                                   ? Insanity
                                                                  : Normal;
    return thresholds[size_t(std::clamp(index, 1, 4) - 1)];
}

int MawBalanceModel::masteryForSkill(double skill) const
{
    for (int mastery = 4; mastery >= 1; --mastery)
    {
        if (skill >= masteryThreshold(mastery))
        {
            return mastery;
        }
    }

    return 1;
}

double MawBalanceModel::gradualMasteryValue(const MasteryTable &table, double skill, int mastery) const
{
    mastery = std::max(mastery, 0);

    if (mastery < 1)
    {
        return table.at(0, 0);
    }

    const int index = std::min(mastery, 4);
    const double from = masteryThreshold(index);
    const double to = index < 4 ? masteryThreshold(index + 1) : from * 1.4;
    const double previous = table.at(mastery - 1, 0);
    const double current = table.at(mastery, previous);

    if (to <= from)
    {
        return current;
    }

    return previous + (current - previous) * clamp01((skill - from) / (to - from));
}

double MawBalanceModel::gradualSkillValue(const std::array<double, 4> &perMastery, double skill, int mastery) const
{
    return gradualMasteryValue(oneBased({perMastery[0], perMastery[1], perMastery[2], perMastery[3]}), skill, mastery);
}

double MawBalanceModel::gradualRow(const MasteryTable &table, double skill, int mastery) const
{
    return mastery <= 1 ? table.at(1, 0) : gradualMasteryValue(table, skill, mastery);
}

double MawBalanceModel::buffRamp(double skill) const
{
    return clamp01((skill - masteryThreshold(2)) / (masteryThreshold(3) - masteryThreshold(2)));
}

double MawBalanceModel::buffFlat(int spellId, double skill, int mastery, double level, double levelDivisor) const
{
    const BuffPower *pBuff = findBuff(spellId);

    if (pBuff == nullptr)
    {
        return 0;
    }

    const double casterSkill = std::min(skill, spellId == 83 || spellId == 85 || spellId == 86 ? 75.0 : 50.0);
    const double base = gradualRow(zeroBased({0, pBuff->base, pBuff->base, pBuff->base, pBuff->base}), skill, mastery);
    const double scaling =
        gradualRow(zeroBased({0, pBuff->scaling, pBuff->scaling, pBuff->scaling, pBuff->scaling}), skill, mastery);
    return (base + level / levelDivisor) * (1 + scaling / 100 * casterSkill) * buffRamp(skill);
}

double MawBalanceModel::buffMult(int spellId, double skill, int mastery) const
{
    const BuffPower *pBuff = findBuff(spellId);

    if (pBuff == nullptr)
    {
        return 0;
    }

    const double casterSkill = std::min(skill, spellId == 83 || spellId == 85 || spellId == 86 ? 75.0 : 50.0);
    const double base = gradualRow(zeroBased({0, pBuff->base, pBuff->base, pBuff->base, pBuff->base}), skill, mastery);
    return base / 100 * buffRamp(skill) * (1 + 0.02 * casterSkill);
}

int MawBalanceModel::statisticEffect(double value)
{
    // The engine reads the stat as a whole number; MAW makes every 5 points from 25 count as 1.
    const int stat = int(value);

    if (stat >= 25)
    {
        return stat / 5;
    }

    static constexpr std::array<std::pair<int, int>, 11> Steps = {{
        {21, 4}, {19, 3}, {17, 2}, {15, 1}, {13, 0}, {11, -1}, {9, -2}, {7, -3}, {5, -4}, {3, -5}, {0, -6},
    }};

    for (const auto &[threshold, effect] : Steps)
    {
        if (stat >= threshold)
        {
            return effect;
        }
    }

    return -6;
}

double MawBalanceModel::skill(double level) const
{
    double points = 0;

    if (level >= 2)
    {
        const double tens = std::floor(level / 10);
        const double rest = level - tens * 10;
        points = 5 * (level - 1) + 5 * tens * (tens - 1) + tens * (rest + 1);
    }

    // Spread over five skills; cumulative cost s (s + 1) / 2 - 1.
    return (std::sqrt(1 + 8 * (points / 5 + 1)) - 1) / 2;
}

int MawBalanceModel::mastery(double level) const
{
    return masteryForSkill(skill(level));
}

double MawBalanceModel::lootTier(double level) const
{
    return level / 15 + std::min(1 + level / 15, 6.0);
}

double MawBalanceModel::enchantStrengthCurve(double tier) const
{
    if (m_config.austerity)
    {
        return tier <= 30 ? tier + 2 : 32 + (tier - 30) * 2;
    }

    return tier <= 12 ? 1 + tier * 2 : 25 + std::min((tier - 12) * 3, 75.0);
}

double MawBalanceModel::maxEnchantStrength(double level) const
{
    const double extraPower = m_config.insanityMode ? 1.2
        : m_config.doomMode                         ? 1.1
        : m_config.trueNightmare                    ? 1.05
                                                    : 1.0;
    // Expected items are Primordial or Legendary: an average of 1.1 (PRIMORDIAL_ENCHANT_MULT 1.25 at 40 %).
    return enchantStrengthCurve(lootTier(level)) * extraPower * 1.1;
}

double MawBalanceModel::expectedEnchantFraction(double tier, double drops, int difficulty) const
{
    const std::array<double, 9> distribution = rarityDistribution(tier, difficulty);
    const double n = std::max(drops, 1.0);
    static constexpr std::array<int, 8> ByValue = {
        Common, Uncommon, Rare, Epic, Legendary, Ancient, Primordial, Celestial};
    double expected = 0;
    double below = 0;

    // The best of n drops: each rarity's share is P(best is at most it) - P(best is below it).
    for (int rarity : ByValue)
    {
        const double cumulative = below + distribution[size_t(rarity)];
        expected += rarityItemFraction(rarity) * (std::pow(cumulative, n) - std::pow(below, n));
        below = cumulative;
    }

    return expected;
}

size_t MawBalanceModel::cachedLevelCount() const
{
    return m_gearedCache.size() + m_statCache.size() + m_healthCache.size();
}

double MawBalanceModel::gearedFraction(double level)
{
    const bool cacheable = wholeLevel(level);

    if (const auto cached = m_gearedCache.find(level); cacheable && cached != m_gearedCache.end())
    {
        return cached->second;
    }

    // Fitted against Beyond Madness at full density; easier difficulties see fewer drops per slot.
    const double tier = lootTier(level);
    const double anchor = (level + 20) / (level + 100);
    const double geared = anchor
        * expectedEnchantFraction(
            tier, dropsSeenPerSlot(level, DropsDensityByDifficulty[size_t(m_config.difficulty)]), m_config.difficulty)
        / expectedEnchantFraction(tier, dropsSeenPerSlot(level, 1), 9);

    if (cacheable)
    {
        m_gearedCache.emplace(level, geared);
    }
    return geared;
}

double MawBalanceModel::stat(double level)
{
    const bool cacheable = wholeLevel(level);

    if (const auto cached = m_statCache.find(level); cacheable && cached != m_statCache.end())
    {
        return cached->second;
    }

    // Creation stat, black potions to level 500, a fifth of every enchant worn, the Day of the Gods aura.
    const double totalEnchantPower = EnchantsWorn * maxEnchantStrength(level);
    const double estimatedSkill = skill(level);
    const double dayOfTheGods = 1 + std::min(10 + estimatedSkill / 7, 20.0) / 100 * buffRamp(estimatedSkill);
    const double value = (17 + std::min(level, 500.0) * 0.2
                             + totalEnchantPower * EnchantStatShare * gearedFraction(level))
        * dayOfTheGods;

    if (cacheable)
    {
        m_statCache.emplace(level, value);
    }
    return value;
}

double MawBalanceModel::health(double level)
{
    const bool cacheable = wholeLevel(level);

    if (const auto cached = m_healthCache.find(level); cacheable && cached != m_healthCache.end())
    {
        return cached->second;
    }

    const double perLevel = std::min(6 * level / (m_config.madnessMode ? 330.0 : 210.0), 6.0) + 3;
    const double expectedStat = stat(level);
    const double estimatedSkill = skill(level);
    const int bodybuildingMastery = std::min(mastery(level), 3);
    // Flat HP enchants roll on their own curve: the stat share of all enchants worn, raised by the enchant strength.
    const double flatBonus = EnchantsWorn * maxEnchantStrength(level) * EnchantStatShare * gearedFraction(level)
        * (1 + std::min(maxEnchantStrength(level) / 50, 5.0));
    const double bodybuildingFlat =
        estimatedSkill * gradualRow(BodybuildingFlatPerRank, estimatedSkill, bodybuildingMastery);
    const double bodybuildingPercent =
        gradualMasteryValue(BodybuildingHealth, estimatedSkill, bodybuildingMastery);
    const double value =
        (25 + perLevel * level + (expectedStat / 5 + bodybuildingFlat) * perLevel + flatBonus)
        * (1 + bodybuildingPercent * estimatedSkill / 100) * (1 + expectedStat / 1000);

    if (cacheable)
    {
        m_healthCache.emplace(level, value);
    }
    return value;
}

double MawBalanceModel::mana(double level)
{
    const double perLevel = std::min(6 * level / (m_config.madnessMode ? 330.0 : 210.0), 6.0) + 3;
    const double estimatedSkill = skill(level);
    const int estimatedMastery = mastery(level);
    const double pool = 15
        + perLevel
            * (level + 2 * statisticEffect(stat(level))
               + estimatedSkill * gradualRow(MeditationPerRank, estimatedSkill, estimatedMastery));
    return pool * (1 + gradualRow(EnlightenmentManaPerSkill, estimatedSkill, estimatedMastery) / 100 * estimatedSkill);
}

double MawBalanceModel::wornArmor(double level)
{
    const double power = powerFor(level);
    const double charges = std::min(std::max(mawRound(power * 1.2), power + 4), 255.0);
    return (116 + 116 * charges / 40) * gearedFraction(level);
}

double MawBalanceModel::armorClass(double level)
{
    const double estimatedSkill = skill(level);
    const int estimatedMastery = mastery(level);
    const double armorMult = gradualRow(ChainItemArmor, estimatedSkill, estimatedMastery) * estimatedSkill / 100;
    return wornArmor(level) * (1 + 0.5 * legendaryRamp(level) + armorMult)
        + buffFlat(SpellStoneSkin, estimatedSkill, estimatedMastery, level, 4);
}

double MawBalanceModel::resistance(double level)
{
    const double estimatedSkill = skill(level);
    const int estimatedMastery = mastery(level);
    return wornArmor(level) * gradualRow(ChainItemResistance, estimatedSkill, estimatedMastery) * estimatedSkill / 100
        + buffFlat(SpellFireResistance, estimatedSkill, estimatedMastery, level)
        + statisticEffect(stat(level));
}

double MawBalanceModel::enchantResistance(double level) const
{
    return maxEnchantStrength(level) * 100 / 200 * (1 + 0.5 * legendaryRamp(level));
}

double MawBalanceModel::chanceToBeHit(double level)
{
    const double speed = stat(level);
    return 1 / (1 + speed / (100 + stat(level)) * 0.5);
}

double MawBalanceModel::physicalDamageTaken(double level)
{
    return std::max(1 / (armorClass(level) / mawArmorDivisor(level) + 1), 0.1);
}

double MawBalanceModel::magicDamageTaken(double level)
{
    const double estimatedSkill = skill(level);
    double taken = 1 / (resistance(level) / mawResistanceDivisor(level) + 1);
    taken *= std::max(1 - buffMult(SpellShield, estimatedSkill, mastery(level)), 0.7);
    taken *= 1 / (enchantResistance(level) / 100 + 1);
    return std::max(taken, 0.1);
}

double MawBalanceModel::legendaryDamageTaken(double level) const
{
    const double ramp = legendaryRamp(level);
    const double crowd = std::pow(1 - 0.03, 5);
    return (1 - 0.10 * ramp) * (1 - (1 - crowd) * ramp);
}

double MawBalanceModel::coverMultiplier(double level) const
{
    const double estimatedSkill = skill(level);
    const double gate = gradualRow(CoverGate, estimatedSkill, mastery(level));

    if (gate <= 0)
    {
        return 1;
    }

    const double chance = std::min(0.10 + 0.01 * estimatedSkill, 0.10 + 0.01 * 30) * gate;
    const double ratio = m_config.partyCount <= 1 ? 1 / 0.5 : TankVitalityRatio;
    return 1 / ((1 - chance) + chance / ratio);
}

double MawBalanceModel::vitality(double level, MawDamageClass damageClass)
{
    double mitigation = physicalDamageTaken(level) * 0.5 + magicDamageTaken(level) * 0.5;

    if (damageClass == MawDamageClass::Physical)
    {
        mitigation = physicalDamageTaken(level);
    }
    else if (damageClass == MawDamageClass::Magic)
    {
        mitigation = magicDamageTaken(level);
    }

    const double taken = mitigation * chanceToBeHit(level) * legendaryDamageTaken(level);
    return health(level) / taken * coverMultiplier(level);
}

double MawBalanceModel::attack(double level)
{
    const double estimatedSkill = skill(level);
    const int estimatedMastery = mastery(level);
    const double meleeSkill = estimatedSkill + 10 * legendaryRamp(level);
    return weaponDamageForLevel(level, true, weaponFlat(level)).flat
        + gradualMasteryValue(SwordAttack, meleeSkill, masteryForSkill(meleeSkill)) * meleeSkill
        + gradualMasteryValue(ArmsmasterAttack, estimatedSkill, estimatedMastery) * estimatedSkill
        + statisticEffect(stat(level))
        + buffFlat(SpellBless, estimatedSkill, estimatedMastery, level);
}

double MawBalanceModel::weaponLevelDamage(double itemLevel, bool twoHanded, double flat)
{
    const double levelDamage = weaponDamageForLevel(itemLevel, twoHanded, flat).levelDamage;
    const double armsSkill = skill(itemLevel) * 1.5;
    double arms = gradualMasteryValue(ArmsmasterDamage, armsSkill, masteryForSkill(armsSkill)) * armsSkill;
    double statFlat = statisticEffect(stat(itemLevel));

    if (!twoHanded)
    {
        arms /= 2;
        statFlat /= 2;
    }

    return ((levelDamage + arms) * (1 + 0.02 * skill(itemLevel)) + statFlat) * (1 + stat(itemLevel) / 1000);
}

double MawBalanceModel::power(double level)
{
    const double estimatedSkill = skill(level);
    const int estimatedMastery = mastery(level);
    const WeaponDamage weapon = weaponDamageForLevel(level, true, weaponFlat(level));
    const double ramp = legendaryRamp(level);
    const double meleeSkill = estimatedSkill + 10 * ramp;
    const double weaponSkillMult = 1 + SwordSkillDamagePerPoint * meleeSkill / 100;
    const double armsSkill = estimatedSkill * 1.5;
    const int meleeMastery = masteryForSkill(meleeSkill);
    const int armsMastery = masteryForSkill(armsSkill);
    const double armsBase = gradualMasteryValue(ArmsmasterDamage, armsSkill, armsMastery) * armsSkill;
    const double scalable = weapon.flat + 0.5 * weapon.dice + armsBase;
    double damage = 3.0 / 2 + scalable * weaponSkillMult;
    // A weapon skill point is worth at least 1 damage.
    damage += std::max(meleeSkill - scalable * (weaponSkillMult - 1), 0.0);

    const double expectedStat = stat(level);
    damage = (damage + statisticEffect(expectedStat)) * (1 + buffMult(SpellHeroism, estimatedSkill, estimatedMastery))
        * (1 + expectedStat / 1000);

    const double speedEffect =
        (expectedStat <= 21 ? (expectedStat - 13) / 4 : std::floor(expectedStat / 10)) / 100;
    const double weaponSpeed = gradualMasteryValue(SwordRecovery, meleeSkill, meleeMastery) * meleeSkill / 100;
    const double armsSpeed = gradualMasteryValue(ArmsmasterSpeed, armsSkill, armsMastery) * armsSkill / 100;
    damage *=
        (1 + speedEffect + weaponSpeed + armsSpeed) * (1 + buffMult(SpellHaste, estimatedSkill, estimatedMastery));

    // Luck and Accuracy are the same expected stat.
    const double critChance = expectedStat / std::min(500 + level * 5, 3000.0) + 0.05 + 0.1 * ramp
        + buffMult(SpellFate, estimatedSkill, estimatedMastery);
    const double critDamage =
        expectedStat / std::min(250 + level * 2.5, m_config.madnessMode ? 3000.0 : 2000.0) + 1.5 - 1;
    const double critMult = 1 + std::min(critChance, 1.0) * critDamage;
    damage *= critMult;

    const double enchantLegendary = (1 + (1.5 - 1) * ramp) * (1 + (critMult - 1) * ramp);
    const double enchantBase = weaponLevelDamage(level, true, weaponFlat(level)) * enchantLegendary;
    damage += enchantBase * 0.5 * std::min(level / 100, 1.0);
    damage += enchantBase * gradualMasteryValue(FireAuraDamage, estimatedSkill, estimatedMastery);
    damage *= std::min(1 + 0.05 * 5 * ramp, 2.0) * (1 + 0.15 * ramp);
    damage *= std::max(critChance, 1.0);

    const double blessHit = 0.05 + 0.05 * std::min(estimatedSkill, 50.0) / 50;
    return damage * std::min(0.75 + blessHit, 1.0);
}

double MawBalanceModel::spellPower(double level)
{
    const double estimatedSkill = skill(level);
    const int estimatedMastery = mastery(level);
    const double expectedStat = stat(level);
    const double reference = std::min(estimatedSkill / masteryThreshold(4), 1.0);
    // Novice Fire Bolt to Grandmaster Incinerate.
    double add = 8 + (19 - 8) * reference;
    double dice = 2 + (21 - 2) * reference;
    const double baseDelay = 110 + (90 - 110) * reference;
    // MAW reads Haste here where Empower Magic is meant (BALANCE_MODEL.md §5.3).
    const double empower = 1 + buffMult(SpellHaste, estimatedSkill, estimatedMastery);
    dice *= empower * mawSpellDiceScale(estimatedSkill) * MawSpellDamageMultiplier;
    add *= empower * mawSpellAddScale(estimatedSkill) * MawSpellDamageMultiplier;
    double power = (add + estimatedSkill * 1.5 * (1 + dice) / 2) * (1 + expectedStat / 1000);

    const double ramp = legendaryRamp(level);
    const double critChance = expectedStat / std::min(500 + level * 5, 3000.0) + 0.05 + 0.1 * ramp
        + buffMult(SpellFate, estimatedSkill, estimatedMastery);
    const double critDamage =
        expectedStat / (std::min(250 + level * 2.5, m_config.madnessMode ? 3000.0 : 2000.0) * 4) + 1.5;
    const double critFactor = 1 + std::min(critChance, 1.0) * (critDamage - 1);
    power *= critFactor;

    const double enchantLegendary = (1 + (1.5 - 1) * ramp) * (1 + (critFactor - 1) * ramp);
    const double enchantBase = weaponLevelDamage(level, true, weaponFlat(level)) * enchantLegendary;
    const double enchant = enchantBase
        * (0.5 * std::min(level / 100, 1.0) + gradualMasteryValue(FireAuraDamage, estimatedSkill, estimatedMastery))
        * std::pow(1.015, estimatedSkill);
    const double delay = baseDelay / (1 + std::floor(expectedStat / 20) / 100) * std::pow(1.015, estimatedSkill)
        / (1 + buffMult(SpellHaste, estimatedSkill, estimatedMastery));
    return (power + enchant) / (delay / 100) * std::max(critChance, 1.0);
}

double MawBalanceModel::monsterHealth(double level)
{
    const std::array<double, 10> &hits = m_config.austerity ? HitsToKillMonsterAusterity : HitsToKillMonster;
    return power(level) * hits[size_t(m_config.difficulty)];
}

double MawBalanceModel::monsterDamage(double level, MawDamageClass damageClass)
{
    const std::array<double, 10> &hits = m_config.austerity ? HitsToKillCharacterAusterity : HitsToKillCharacter;
    return vitality(level, damageClass) / hits[size_t(m_config.difficulty)];
}

double MawBalanceModel::monsterExperienceMultiplier() const
{
    const auto mean = [](int difficulty)
    {
        return (MonsterDensity[size_t(difficulty)][0] + MonsterDensity[size_t(difficulty)][1]) / 2;
    };
    return std::sqrt(mean(3) / mean(m_config.difficulty));
}
}
