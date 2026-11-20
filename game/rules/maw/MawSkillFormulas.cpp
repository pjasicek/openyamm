#include "game/rules/maw/MawSkillFormulas.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
size_t masteryIndex(SkillMastery mastery)
{
    return size_t(std::clamp(int(mastery), int(SkillMastery::Expert), int(SkillMastery::Grandmaster))) - 2;
}

constexpr uint32_t UndiscountedRaiseCost = 1000;
constexpr int UnlimitedHallBase = 2750;
}

bool mawIsAddedSkill(const std::string &canonicalSkill)
{
    return canonicalSkill == "Cover" || canonicalSkill == "ManaShield" || canonicalSkill == "Enlightenment"
        || canonicalSkill == "Retaliation";
}

bool mawIsSoloMasterySkill(const std::string &canonicalSkill)
{
    return std::find(MawSoloMasterySkills.begin(), MawSoloMasterySkills.end(), canonicalSkill)
        != MawSoloMasterySkills.end();
}

bool mawIsHorizontalSkill(const std::string &canonicalSkill)
{
    static const std::array<const char *, 8> NonHorizontal = {
        "IdentifyItem", "Merchant", "RepairItem", "Perception", "DisarmTraps", "IdentifyMonster", "Stealing", "Alchemy",
    };
    return std::find(NonHorizontal.begin(), NonHorizontal.end(), canonicalSkill) == NonHorizontal.end();
}

double mawCoverChance(double coverSkill, bool hitBonus)
{
    return std::min(0.10 + 0.01 * coverSkill, 0.40) + (hitBonus ? 0.15 : 0.0);
}

SkillMastery mawCoverRequiredMastery(bool spell, bool physical)
{
    return spell ? SkillMastery::Master : physical ? SkillMastery::Normal : SkillMastery::Expert;
}

double mawManaShieldEfficiency(double manaShieldSkill)
{
    return manaShieldSkill >= 50 ? 5.0 : 1 + std::pow(std::max(0.0, manaShieldSkill), 1.4) / 60;
}

double mawManaShieldAbsorbFraction(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return 0.25;
        case SkillMastery::Expert:
            return 0.5;
        case SkillMastery::Master:
            return 0.75;
        case SkillMastery::Grandmaster:
            return 1;
        default:
            return 0;
    }
}

MawManaShieldResult mawManaShield(int damage, int spellPoints, double manaShieldSkill, SkillMastery mastery)
{
    const double efficiency = mawManaShieldEfficiency(manaShieldSkill);
    double absorbed = damage * mawManaShieldAbsorbFraction(mastery);
    const int cost = int(std::round(absorbed / efficiency));
    absorbed = std::min(absorbed, std::max(0, spellPoints) * efficiency);

    MawManaShieldResult result;
    result.damage = int(std::round(damage - absorbed));
    result.spellPointsSpent = std::min(std::max(0, spellPoints), cost);
    return result;
}

std::optional<uint32_t> mawSkillLevelCap(const std::string &canonicalSkill)
{
    if (canonicalSkill == "Alchemy")
    {
        return 60;
    }

    if (canonicalSkill == "Cover")
    {
        return 30;
    }

    if (canonicalSkill == "ManaShield" || canonicalSkill == "Retaliation")
    {
        return 50;
    }

    return std::nullopt;
}

std::optional<std::array<uint32_t, 3>> mawSkillMasteryLadder(const std::string &canonicalSkill, MawSkillMode mode)
{
    const bool insanity = mode == MawSkillMode::RoadToInsanity || mode == MawSkillMode::BeyondMadness;

    if (canonicalSkill == "Cover")
    {
        return insanity ? std::array<uint32_t, 3> {8, 20, 30} : std::array<uint32_t, 3> {6, 12, 20};
    }

    if (canonicalSkill == "ManaShield")
    {
        return insanity ? std::array<uint32_t, 3> {8, 20, 32} : std::array<uint32_t, 3> {6, 12, 20};
    }

    if (canonicalSkill == "Enlightenment")
    {
        return std::array<uint32_t, 3> {6, 12, 20};
    }

    if (canonicalSkill == "Retaliation")
    {
        return std::array<uint32_t, 3> {10, 24, 40};
    }

    return std::nullopt;
}

uint32_t mawMasteryRequiredLevel(MawSkillMode mode, SkillMastery mastery)
{
    static constexpr std::array<std::array<uint32_t, 3>, 4> Requirements = {{
        {4, 7, 10},
        {6, 12, 20},
        {8, 16, 25},
        {10, 24, 40},
    }};
    return Requirements[size_t(mode)][masteryIndex(mastery)];
}

int mawTeacherBasePrice(MawPriceMode mode, SkillMastery mastery)
{
    static constexpr std::array<std::array<int, 3>, 4> Prices = {{
        {1000, 4000, 20000},
        {2000, 10000, 50000},
        {10000, 50000, 250000},
        {15000, 300000, 1250000},
    }};
    return Prices[size_t(mode)][masteryIndex(mastery)];
}

uint32_t mawSharedRaiseCost(uint32_t newLevel, uint32_t otherSkillsAtOrAbove)
{
    if (newLevel > UndiscountedRaiseCost)
    {
        return newLevel;
    }

    const uint32_t sharers = 1 + otherSkillsAtOrAbove;
    return (newLevel + sharers - 1) / sharers;
}

bool mawIsSharedCostSkill(const std::string &canonicalSkill, bool hybridClass)
{
    static const std::array<const char *, 8> Weapons = {
        "Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Mace", "Blaster",
    };
    static const std::array<const char *, 11> Magic = {
        "FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic", "BodyMagic",
        "LightMagic", "DarkMagic", "DarkElfAbility", "VampireAbility",
    };

    if (std::find(Magic.begin(), Magic.end(), canonicalSkill) != Magic.end())
    {
        return true;
    }

    return !hybridClass && std::find(Weapons.begin(), Weapons.end(), canonicalSkill) != Weapons.end();
}

uint32_t mawSharedSetRefund(std::vector<uint32_t> levels)
{
    uint32_t refund = 0;

    while (true)
    {
        const auto highest = std::max_element(levels.begin(), levels.end());

        if (highest == levels.end() || *highest <= 1)
        {
            return refund;
        }

        const uint32_t level = *highest;
        const uint32_t atLevel = uint32_t(std::count(levels.begin(), levels.end(), level));
        refund += (level + atLevel - 1) / atLevel;
        *highest -= 1;
    }
}

uint32_t mawLevelUpPoints(uint32_t level)
{
    uint32_t points = 0;

    for (uint32_t index = 2; index <= level; ++index)
    {
        points += 5 + index / 10;
    }

    return points;
}

double mawRegenerationHealthPerSecond(
    SkillMastery mastery,
    double estimatedHealth,
    double fullHealth,
    double health)
{
    static constexpr std::array<double, 4> Rates = {0.05, 0.075, 0.10, 0.10};

    if (mastery < SkillMastery::Normal || fullHealth <= 0)
    {
        return 0;
    }

    double perSecond =
        Rates[size_t(std::min(int(mastery), 4)) - 1] * std::sqrt(std::max(estimatedHealth, 0.0) * fullHealth);

    if (mastery >= SkillMastery::Grandmaster)
    {
        const double missing = 1 - std::max(health / fullHealth, -1.0);
        perSecond *= 1 + missing * missing;
    }

    return perSecond;
}

double mawMeditationSpellPerSecond(SkillMastery mastery, double estimatedMana, double pool)
{
    static constexpr std::array<double, 4> Rates = {0.02, 0.025, 0.03, 0.04};

    if (mastery < SkillMastery::Normal || pool <= 0)
    {
        return 0;
    }

    return Rates[size_t(std::min(int(mastery), 4)) - 1] * std::sqrt(std::max(estimatedMana, 0.0) * pool);
}

double mawRegenerationAuraHealthPerSecond(double fullHealth, double holderLevel, double holderSkill, double buffScale)
{
    // Regeneration's buff power base 5 is both terms (0.05 = 5 / 100, 0.005 = 5 / 1000); affix 33 scales it.
    return std::sqrt(std::max(fullHealth, 0.0))
        * std::pow(std::pow(std::max(holderLevel, 0.0), 0.65) * (1 + 0.05 * buffScale * holderSkill), 1.25) * 0.005
        * buffScale;
}

double mawRegenerationPotionHealthPerSecond(double fullHealth, double skill)
{
    return std::sqrt(std::max(fullHealth, 0.0)) * std::pow(std::max(skill, 0.0), 1.25) * 0.005;
}

double mawMeditationAuraSpellPerSecond(double pool, double estimatedSkill, double holderSkill, double buffScale)
{
    // Meditation's buff power base (the 0.01) and scaling (the 0.02); affix 33 scales both.
    return (0.01 * buffScale * std::pow(std::max(pool, 0.0), 0.35) * std::pow(std::max(estimatedSkill, 0.0), 1.4) + 1)
        * (1 + 0.02 * buffScale * holderSkill);
}

double mawMeditationPool(double fullSpellPoints, double reservedSpellPoints)
{
    if (fullSpellPoints <= 0)
    {
        return 0;
    }

    const double share = std::clamp(reservedSpellPoints / fullSpellPoints, 0.0, 1.0);
    return std::ceil(fullSpellPoints * std::sqrt(1 - share));
}

double mawRegenerationMultiplier(bool recentHealthLoss, bool enemiesNear)
{
    return (recentHealthLoss ? 1 : 2) * (enemiesNear ? 1 : 4);
}

int mawTrainingHallCap(int baseCap, bool madness)
{
    const double base = baseCap < 0 ? UnlimitedHallBase : std::max(baseCap, 10);
    return int(std::floor(std::pow(base, 1.5) / (madness ? 10 : 20) + 0.5)) * 10;
}
}
