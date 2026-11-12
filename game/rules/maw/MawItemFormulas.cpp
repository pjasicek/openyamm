#include "game/rules/maw/MawItemFormulas.h"
#include "engine/Localization.h"

#include "game/rules/maw/MawCombatFormulas.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr int TierLevels = 15;
constexpr int StrengthDivisor = 20;
constexpr int PowerCap = 100;
constexpr int PowerHardCap = 255;
constexpr double BossRollDivisor = 4;
constexpr double BossRarityMultiplier = 2;
constexpr double PityExponent = 1.38;
// rarityBandMult (Epic, Rare, Uncommon) and rarityDifficultyMult by difficulty index 1-9.
constexpr std::array<std::array<double, 3>, 10> BandMultipliers = {{
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
constexpr std::array<double, 10> UpgradeDifficultyMultipliers = {1, 1, 1, 1, 1.1, 1.2, 1.4, 1.6, 1.8, 2};

size_t difficultyIndex(int difficulty)
{
    return size_t(std::clamp(difficulty, 1, 9));
}

// Expected number of Epic rolls until an upgrade with bad-luck protection succeeds: the counter grows by the
// multiplier on every failure and the chance is multiplied by it.
double expectedPityWait(double base, double multiplier)
{
    double expected = 0;
    double survival = 1;

    for (int failures = 0; survival > 1e-15; ++failures)
    {
        expected += survival;
        const double hazard = std::min(mawPityChance(base, failures * multiplier) * multiplier, 1.0);
        survival *= 1 - hazard;
    }

    return expected;
}
}

const char *mawRarityName(MawRarity rarity)
{
    // English, translated where an item's name shows it.
    static constexpr std::array<const char *, 9> Names = {
        "", Engine::trNoop("Common").data(), Engine::trNoop("Uncommon").data(), Engine::trNoop("Rare").data(),
        Engine::trNoop("Epic").data(), Engine::trNoop("Ancient").data(), Engine::trNoop("Primordial").data(),
        Engine::trNoop("Legendary").data(), Engine::trNoop("Celestial").data(),
    };
    return size_t(rarity) < Names.size() ? Names[size_t(rarity)] : "";
}

double mawEnchantStrengthCurve(double lootTier, bool austerity)
{
    const double tier = std::max(0.0, lootTier);

    if (austerity)
    {
        return tier <= 30 ? tier + 2 : 32 + (tier - 30) * 2;
    }

    return tier <= 12 ? 1 + 2 * tier : 25 + std::min((tier - 12) * 3, 75.0);
}

MawStrengthRange mawEnchantStrengthRange(MawRarity rarity)
{
    switch (rarity)
    {
        case MawRarity::Legendary:
            return {16, 20};
        case MawRarity::Ancient:
            return {20, 25};
        case MawRarity::Primordial:
        case MawRarity::Celestial:
            return {25, 25};
        default:
            return {8, 20};
    }
}

int mawEnchantStrength(int lootTier, MawRarity rarity, int draw, const MawLootConfig &config)
{
    const double curve = mawEnchantStrengthCurve(lootTier, config.austerity);

    if (rarity <= MawRarity::Epic)
    {
        return int(std::ceil(mawRound(curve * draw / StrengthDivisor) * config.enchantPower));
    }

    return int(mawRound(std::ceil(curve * config.enchantPower) * draw / StrengthDivisor));
}

std::array<double, 4> mawRarityBands(int lootTier, int difficulty, bool boss)
{
    const double tier = std::max(0, lootTier);
    const double epic = std::min(5 + 0.75 * tier, 20.0);
    const double rare = std::min(20 + 2 * tier, 60.0);
    const double uncommon = std::min(60 + tier, 80.0);
    const std::array<double, 3> &multipliers = BandMultipliers[difficultyIndex(difficulty)];
    // Best first: Epic, Rare, Uncommon, Common.
    std::array<double, 4> widths = {
        epic * multipliers[0],
        (rare - epic) * multipliers[1],
        (uncommon - rare) * multipliers[2],
        100 - uncommon,
    };
    double total = 0;

    for (double width : widths)
    {
        total += width;
    }

    for (double &width : widths)
    {
        width = width / total * 100;
    }

    if (boss)
    {
        // A boss divides the uniform draw by 4: only the first quarter of the table, renormalised.
        double remaining = 100 / BossRollDivisor;

        for (double &width : widths)
        {
            width = std::min(width, remaining);
            remaining -= width;
        }

        for (double &width : widths)
        {
            width *= BossRollDivisor;
        }
    }

    return {widths[3], widths[2], widths[1], widths[0]};
}

double mawRarityUpgradeMultiplier(int lootTier, int difficulty, bool boss)
{
    return UpgradeDifficultyMultipliers[difficultyIndex(difficulty)] * std::min(60.0 + std::max(0, lootTier), 80.0)
        / 80 * (boss ? BossRarityMultiplier : 1);
}

double mawPityChance(double base, double failures)
{
    return base >= 1 ? 1 : std::pow(base, PityExponent - base * failures * 0.5);
}

std::array<double, 8> mawLongRunRarityShares(int lootTier, int difficulty, bool boss)
{
    const std::array<double, 4> bands = mawRarityBands(lootTier, difficulty, boss);
    const double multiplier = mawRarityUpgradeMultiplier(lootTier, difficulty, boss);
    // The cascade checks Celestial, then Legendary, then Primordial, then Ancient; each counter only sees the rolls the
    // earlier ones left (devdocs/maw/RANDOMS.md §5.1).
    const double celestial = 1 / expectedPityWait(MawCelestialChance, multiplier);
    const double legendary = (1 - celestial) / expectedPityWait(MawLegendaryChance, multiplier);
    const double primordial = (1 - celestial - legendary) / expectedPityWait(MawPrimordialChance, multiplier);
    const double ancient =
        (1 - celestial - legendary - primordial) * std::min(MawAncientChance * multiplier, 1.0);
    const double epic = bands[3];
    return {
        bands[0],
        bands[1],
        bands[2],
        epic * (1 - celestial - legendary - primordial - ancient),
        epic * ancient,
        epic * primordial,
        epic * legendary,
        epic * celestial,
    };
}

MawRarity mawRollRarity(const MawRarityRollInputs &inputs, MawRarityPity &pity, std::mt19937 &rng)
{
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    const std::array<double, 4> bands = mawRarityBands(inputs.lootTier, inputs.difficulty, inputs.boss);
    const double bandDraw = unit(rng) * 100;
    MawRarity rarity = MawRarity::Common;

    if (bandDraw < bands[3])
    {
        rarity = MawRarity::Epic;
    }
    else if (bandDraw < bands[3] + bands[2])
    {
        rarity = MawRarity::Rare;
    }
    else if (bandDraw < bands[3] + bands[2] + bands[1])
    {
        rarity = MawRarity::Uncommon;
    }

    if (rarity == MawRarity::Epic)
    {
        const double multiplier =
            mawRarityUpgradeMultiplier(inputs.lootTier, inputs.difficulty, inputs.boss) * inputs.upgradeMultiplier;
        const bool legendaryAllowed = !inputs.noLegendary && !inputs.shop;
        const bool primordialAllowed = !inputs.shop;
        const auto succeeds = [&](double chance)
        {
            return unit(rng) < std::min(chance * multiplier, 1.0);
        };

        if (legendaryAllowed && succeeds(mawPityChance(MawCelestialChance, pity.celestial)))
        {
            rarity = MawRarity::Celestial;
        }
        else if (legendaryAllowed && succeeds(mawPityChance(MawLegendaryChance, pity.legendary)))
        {
            rarity = MawRarity::Legendary;
        }
        else if (primordialAllowed && succeeds(mawPityChance(MawPrimordialChance, pity.primordial)))
        {
            rarity = MawRarity::Primordial;
        }
        else if (succeeds(inputs.shop ? MawPrimordialChance : MawAncientChance))
        {
            rarity = MawRarity::Ancient;
        }

        // A counter grows on every Epic roll that ended below its rarity and could have reached it.
        if (legendaryAllowed)
        {
            pity.celestial = rarity == MawRarity::Celestial ? 0 : pity.celestial + multiplier;
            pity.legendary = rarity == MawRarity::Legendary ? 0
                : rarity == MawRarity::Celestial            ? pity.legendary
                                                            : pity.legendary + multiplier;
        }

        if (primordialAllowed && rarity <= MawRarity::Primordial)
        {
            pity.primordial = rarity == MawRarity::Primordial ? 0 : pity.primordial + multiplier;
        }
    }

    return inputs.omnipotent ? MawRarity::Celestial : rarity;
}

double mawItemValue(const MawValueInputs &inputs)
{
    const auto enchantValue = [](int type, int strength, bool skills)
    {
        if (type == 8 || type == 9)
        {
            return 5 * (std::sqrt(2.0 * strength + 100) - 10) * 100;
        }

        if (type == 10)
        {
            return strength * 200.0;
        }

        if (skills && type >= 17 && type <= 24)
        {
            return double(strength) * strength * 100;
        }

        return strength * 100.0;
    };

    double basePriceBonus = inputs.baseValue * (inputs.itemPower / 20.0);

    if (inputs.specialValue > 0)
    {
        const double special = inputs.specialValue * (inputs.specialScales ? inputs.itemPower / 20.0 : 1);

        if (special < 11)
        {
            basePriceBonus *= special * (special == 10 ? 2.5 : 1);
        }
        else
        {
            basePriceBonus += special;
        }
    }

    double value = inputs.baseValue + basePriceBonus;
    value += inputs.enchant1Type > 0 ? enchantValue(inputs.enchant1Type, inputs.enchant1Strength, true) : 0;
    value += inputs.enchant2Type > 0 ? enchantValue(inputs.enchant2Type, inputs.enchant2Strength, false) : 0;
    return inputs.legendary ? value * 2.5 : value;
}

double mawShopBuyValue(double value, int enchantCount, bool ancientTier)
{
    const int count = enchantCount + (ancientTier ? 2 : 0);
    return std::pow(std::max(value, 1.0), 1 + 0.08 * count);
}

int mawRoundPrice(double value)
{
    const double step = value > 200000 ? 1000 : value > 50000 ? 500 : value > 1000 ? 100 : value > 100 ? 10 : 1;
    return int(std::min(mawRound(value / step) * step, 2.0e9));
}

int mawItemPowerForLevel(double level)
{
    return std::min(int(std::floor(std::max(level, 0.0) / 5)), PowerCap);
}

MawStrengthRange mawItemPowerRange(MawRarity rarity)
{
    switch (rarity)
    {
        case MawRarity::Legendary:
            return {16, 20};
        case MawRarity::Ancient:
            return {20, 24};
        case MawRarity::Primordial:
        case MawRarity::Celestial:
            return {24, 24};
        default:
            return {12, 20};
    }
}

int mawItemPower(int dropLevel, MawRarity rarity, int draw)
{
    const int power = mawItemPowerForLevel(dropLevel);
    int result = int(mawRound(power * double(draw) / StrengthDivisor));

    if (rarity == MawRarity::Ancient)
    {
        result = std::max(result, power + 2);
    }
    else if (rarity == MawRarity::Primordial || rarity == MawRarity::Celestial)
    {
        result = std::max(int(mawRound(power * 1.2)), power + 4);
    }

    return std::min(result, PowerHardCap);
}

MawWeaponDamage mawWeaponDamage(double itemLevel, bool twoHanded, double rung, int diceCount, double quality)
{
    const int power = mawItemPowerForLevel(itemLevel);
    const int flatPower = power / 2;
    double dice = 8 * 2 + 2 * 2 * (power - flatPower);
    double flat = 16 * (rung - 1) / 5 + 2 * flatPower;

    if (!twoHanded)
    {
        dice /= 2;
        flat /= 2;
    }

    MawWeaponDamage damage;
    damage.diceCount = diceCount;
    damage.bonus = flat * quality;
    damage.sides = dice / std::max(diceCount, 1) * quality;
    damage.shownBonus = int(mawRound(damage.bonus));
    damage.minimum = diceCount + damage.shownBonus;
    damage.maximum = diceCount * int(mawRound(damage.sides)) + damage.shownBonus;
    return damage;
}

int mawArmorClass(int baseArmorClass, int referenceArmorClass, int itemPower, double quality)
{
    const double armorClass =
        baseArmorClass + (itemPower > 0 ? mawRound(referenceArmorClass * itemPower / 40.0) : 0);
    return int(mawRound(armorClass * quality));
}

int mawLevelRequirement(int dropLevel, double rung, const MawLevelRequirementRules &rules)
{
    // MAW's ItemLevel.WearLevel: the ladder's tier levels raise the requirement, never above 80 % of the drop level.
    const double level = dropLevel + (rung - 1) * 3;
    double requirement = std::min(level - (10 + 0.09 * level), dropLevel * 0.8);
    requirement -= rules.nightmare ? 6 : 0;
    requirement -= rules.doom ? 3 : 0;
    requirement -= rules.insanity ? 3 : 0;
    return std::max(1, int(std::floor(requirement)));
}

int mawLootTier(int grade, double dropLevel, bool boss, bool omnipotent, int extraBonus, double fraction)
{
    const double level = std::max(0.0, dropLevel);
    const int roundUp = fraction < std::fmod(level, double(TierLevels)) / TierLevels ? 1 : 0;
    return grade + int(level / TierLevels) + extraBonus + (boss ? 1 : 0) + (omnipotent ? 1 : 0) + roundUp;
}
}
