#pragma once

#include "game/party/SkillData.h"

#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
// MAW's spell costs, cast times and heals (devdocs/maw/CLASSES_SPELLS_SPEC.md §1-2). Pure.

enum class MawSpellCategory : uint8_t
{
    // Costs and cast times follow the table.
    Other,
    // The 37 spells MAW rolls itself (spellPowers): Ascension raises their cost and cast time.
    Damage,
    // Heal, Remove Curse, Shared Life, Resurrection, Greater Heal (was Cure Disease) and Power Cure.
    Heal,
    // The 13 crowd-control spells.
    CrowdControl,
};

MawSpellCategory mawSpellCategory(uint32_t spellId);

// Personality cheapens spells: 0.99^(Personality / (10 + 0.06 x min(partyTotalLevel, 1000))) (SP:2172-2179).
double mawPersonalityCostFactor(double personality, double partyTotalLevel);

// No spell costs more than this (SP:2186, 2269-2272, 2363).
constexpr int MawMaximumManaCost = 65000;

// A cast's mana: damage ceil(base x (1 + 0.125s) x 1.04^s x (1 - 0.125m) x P), heals the same curve rounded, crowd
// control ceil(base x (1 + 0.2s) x 1.03^s x (1 - 0.125m) x P) (§1.1); s and m are the Ascension skill and mastery.
int mawSpellManaCost(
    MawSpellCategory category,
    int baseCost,
    double ascensionSkill,
    SkillMastery ascensionMastery,
    double personalityFactor);

// A crowd-control spell's cast time: round(table x 1.015^(Ascension - school skill)) (§1.3).
int mawCrowdControlDelay(int tableDelay, double ascensionSkill, double schoolSkill);

// A crowd-control spell (CCMAP, CLASSES_SPELLS_SPEC.md §4.1): its duration in game minutes at Grandmaster, its
// diminishing-returns group (1 is exempt) and its special rules.
struct MawCrowdControlSpell
{
    uint32_t spellId = 0;
    double baseMinutes = 0;
    int group = 1;
    // Shrinking Ray lasts its base at every mastery; Dragon Fear's duration follows its Dragon Ability mastery
    // without Ascension or resistance (applyCCDebuff, zzMaw-Spells.lua:1406-1414).
    bool flat = false;
    bool ignoresAscension = false;
};

// Null for a spell that is not crowd control under MAW (Stun has its own roll, mawStunChance).
const MawCrowdControlSpell *mawCrowdControlSpell(uint32_t spellId);

// A cast's duration in game minutes before diminishing returns: base x {0.5, 0.65, 0.8, 1}[mastery] x 1.015^Ascension
// / (1 + resistance / 100), twice as long for a party of one (SP:1406-1427).
double mawCrowdControlMinutes(
    const MawCrowdControlSpell &spell,
    SkillMastery mastery,
    double ascensionSkill,
    int resistance,
    bool soloParty);

// The duration multiplier of diminishing returns from the share of the last 10 game minutes the target spent under
// the group's crowd control: 0 (immune) from 0.6, 0.25 from 0.45, 0.5 from 0.3, 0.75 from 0.15 (SP:1734-1852).
double mawDiminishingReturnsMultiplier(double recentShare);

// Stun's chance: 30 / (30 + L / 4), L = max(round(((level / 4 + resistance + 30) / (1 + 0.01 x skill) - 30) x 4), 0),
// doubled on bosses (DM:334-357).
double mawStunChance(int monsterLevel, int resistance, double skill, bool boss);

// A healing spell's numbers at a mastery (§1.6), or nothing below its mastery.
struct MawHealSpell
{
    int cost = 0;
    double base = 0;
    double perPoint = 0;
};

// Road to Insanity and Beyond Madness have their own costlier table (getBaseHealingSpells, SP:2335-2343).
std::optional<MawHealSpell> mawHealSpell(uint32_t spellId, SkillMastery mastery, bool insanity);

// A heal: (round(base x (1 + 0.01s^2) x 1.015^s) + round(perPoint x (1 + 0.02s) x 1.015^s) x points) x
// (1 + Personality / min(1000 + 3 x level, 4000)); `points` is the school skill (Shared Life uses half of it).
double mawHealAmount(
    const MawHealSpell &spell,
    double points,
    double ascensionSkill,
    double personality,
    double casterLevel);
}
