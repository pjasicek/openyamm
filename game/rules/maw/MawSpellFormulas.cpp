#include "game/rules/maw/MawSpellFormulas.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<uint32_t, 37> DamageSpells = {
    2, 6, 7, 8, 9, 10, 11, 15, 18, 20, 22, 24, 26, 29, 32, 37, 39, 41, 43,
    44, 52, 59, 65, 70, 76, 78, 79, 84, 87, 90, 93, 97, 98, 99, 103, 111, 123,
};
constexpr std::array<uint32_t, 6> HealSpells = {49, 54, 55, 68, 74, 77};
constexpr std::array<uint32_t, 13> CrowdControlSpells = {34, 35, 48, 60, 62, 63, 66, 81, 92, 94, 96, 113, 122};

template <size_t Size>
bool contains(const std::array<uint32_t, Size> &list, uint32_t spellId)
{
    return std::find(list.begin(), list.end(), spellId) != list.end();
}

double masteryCostFactor(SkillMastery mastery)
{
    return 1 - 0.125 * std::clamp(int(mastery), 0, 4);
}
}

MawSpellCategory mawSpellCategory(uint32_t spellId)
{
    if (contains(DamageSpells, spellId))
    {
        return MawSpellCategory::Damage;
    }

    if (contains(HealSpells, spellId))
    {
        return MawSpellCategory::Heal;
    }

    return contains(CrowdControlSpells, spellId) ? MawSpellCategory::CrowdControl : MawSpellCategory::Other;
}

double mawPersonalityCostFactor(double personality, double partyTotalLevel)
{
    return std::pow(0.99, std::max(personality, 0.0) / (10 + 0.06 * std::min(partyTotalLevel, 1000.0)));
}

int mawSpellManaCost(
    MawSpellCategory category,
    int baseCost,
    double ascensionSkill,
    SkillMastery ascensionMastery,
    double personalityFactor)
{
    const double s = std::max(ascensionSkill, 0.0);
    const double mastery = masteryCostFactor(ascensionMastery);

    switch (category)
    {
        case MawSpellCategory::Damage:
            return int(std::min(std::ceil(baseCost * (1 + 0.125 * s) * std::pow(1.04, s) * mastery * personalityFactor),
                double(MawMaximumManaCost)));
        case MawSpellCategory::Heal:
            return int(std::min(std::floor(baseCost * (1 + 0.125 * s) * std::pow(1.04, s) * mastery * personalityFactor
                                           + 0.5),
                double(MawMaximumManaCost)));
        case MawSpellCategory::CrowdControl:
            return int(std::min(std::ceil(baseCost * (1 + 0.2 * s) * std::pow(1.03, s) * mastery * personalityFactor),
                double(MawMaximumManaCost)));
        default:
            return baseCost;
    }
}

int mawCrowdControlDelay(int tableDelay, double ascensionSkill, double schoolSkill)
{
    return int(std::floor(tableDelay * std::pow(1.015, ascensionSkill - schoolSkill) + 0.5));
}

const MawCrowdControlSpell *mawCrowdControlSpell(uint32_t spellId)
{
    static constexpr std::array<MawCrowdControlSpell, 12> Spells = {{
        {35, 6, 1},
        {60, 10, 2},
        {113, 10, 2},
        {62, 4.5, 2},
        {63, 3, 2},
        {122, 4, 2, false, true},
        {66, 5, 2},
        {81, 3, 3},
        {92, 4, 1, true},
        {96, 6, 1},
        {48, 5, 2},
        {94, 10, 2},
    }};

    for (const MawCrowdControlSpell &spell : Spells)
    {
        if (spell.spellId == spellId)
        {
            return &spell;
        }
    }

    return nullptr;
}

double mawCrowdControlMinutes(
    const MawCrowdControlSpell &spell,
    SkillMastery mastery,
    double ascensionSkill,
    int resistance,
    bool soloParty)
{
    static constexpr std::array<double, 4> MasterySteps = {0.5, 0.65, 0.8, 1.0};
    const double step = spell.flat ? 1 : MasterySteps[size_t(std::clamp(int(mastery), 1, 4)) - 1];
    double minutes = spell.baseMinutes * step;

    if (!spell.ignoresAscension)
    {
        minutes *= std::pow(1.015, std::max(ascensionSkill, 0.0)) / (1 + std::max(resistance, 0) / 100.0);
    }

    return minutes * (soloParty ? 2 : 1);
}

double mawDiminishingReturnsMultiplier(double recentShare)
{
    return recentShare >= 0.60 ? 0
        : recentShare >= 0.45  ? 0.25
        : recentShare >= 0.30  ? 0.5
        : recentShare >= 0.15  ? 0.75
                               : 1;
}

double mawStunChance(int monsterLevel, int resistance, double skill, bool boss)
{
    double level = std::max(
        std::floor(((monsterLevel / 4.0 + resistance + 30) / (1 + 0.01 * skill) - 30) * 4 + 0.5), 0.0);
    level *= boss ? 2 : 1;
    return 30 / (30 + level / 4);
}

std::optional<MawHealSpell> mawHealSpell(uint32_t spellId, SkillMastery mastery, bool insanity)
{
    // Cost, base and per point by mastery N/E/M/G; a zero cost means the mastery cannot cast it.
    struct Row
    {
        uint32_t spellId;
        std::array<int, 4> cost;
        std::array<double, 4> base;
        std::array<double, 4> perPoint;
    };

    static constexpr std::array<Row, 6> Rows = {{
        {68, {2, 4, 6, 8}, {4, 8, 12, 16}, {2, 3, 4, 6}},
        {49, {0, 5, 10, 20}, {0, 10, 20, 30}, {0, 4, 6, 8}},
        {74, {0, 0, 15, 25}, {0, 0, 25, 40}, {0, 0, 7, 10}},
        {54, {0, 0, 25, 40}, {0, 0, 0, 0}, {0, 0, 7, 9}},
        {55, {0, 0, 0, 100}, {0, 0, 0, 150}, {0, 0, 0, 21}},
        {77, {0, 0, 0, 30}, {0, 0, 0, 15}, {0, 0, 0, 4}},
    }};
    static constexpr std::array<Row, 6> InsanityRows = {{
        {68, {6, 15, 24, 40}, {12, 24, 36, 48}, {6, 9, 12, 15}},
        {49, {0, 15, 30, 60}, {0, 20, 40, 60}, {0, 8, 12, 16}},
        {74, {0, 0, 45, 100}, {0, 0, 50, 100}, {0, 0, 16, 25}},
        {54, {0, 0, 25, 40}, {0, 0, 0, 0}, {0, 0, 7, 9}},
        {55, {0, 0, 0, 300}, {0, 0, 0, 450}, {0, 0, 0, 50}},
        {77, {0, 0, 0, 150}, {0, 0, 0, 50}, {0, 0, 0, 12}},
    }};

    if (mastery < SkillMastery::Normal)
    {
        return std::nullopt;
    }

    const size_t index = size_t(std::min(int(mastery), 4)) - 1;

    for (const Row &row : insanity ? InsanityRows : Rows)
    {
        if (row.spellId == spellId)
        {
            return row.cost[index] > 0 ? std::optional<MawHealSpell>({row.cost[index], row.base[index],
                                                                         row.perPoint[index]})
                                       : std::nullopt;
        }
    }

    return std::nullopt;
}

double mawHealAmount(
    const MawHealSpell &spell,
    double points,
    double ascensionSkill,
    double personality,
    double casterLevel)
{
    const double s = std::max(ascensionSkill, 0.0);
    const double ascension = std::pow(1.015, s);
    // The scaled base and per-point numbers are rounded, as Ascension rounds spell dice.
    const double base = std::floor(spell.base * (1 + 0.01 * s * s) * ascension + 0.5);
    const double perPoint = std::floor(spell.perPoint * (1 + 0.02 * s) * ascension + 0.5);
    return (base + perPoint * points) * (1 + std::max(personality, 0.0) / std::min(1000 + 3 * casterLevel, 4000.0));
}
}
