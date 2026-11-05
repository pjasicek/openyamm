#pragma once

#include "game/party/SkillData.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// MAW's skill economy (devdocs/maw/TRAINERS_SKILLS.md §2-4, data/mastery_requirements.yml). Pure.

// Which row of MAW's requirement and price tables a game uses.
enum class MawSkillMode : uint8_t
{
    // Normal or Austerity with free progression.
    Normal,
    // Horizontal progression, or Doom in either progression.
    Horizontal,
    RoadToInsanity,
    BeyondMadness,
};

// MAW's four skills of its own (50-53: Cover, Mana Shield, Enlightenment, Retaliation).
bool mawIsAddedSkill(const std::string &canonicalSkill);
// The skills whose teacher requirement and price MAW rewrites; the rest keep Standard's (S:219).
bool mawIsHorizontalSkill(const std::string &canonicalSkill);

// The base skill level a teacher wants for a mastery (Expert 4/6/8/10, Master 7/12/16/24, GM 10/20/25/40).
uint32_t mawMasteryRequiredLevel(MawSkillMode mode, SkillMastery mastery);
// The highest base level of Alchemy (60), Cover (30), Mana Shield and Retaliation (50); nothing for the rest
// (S:162-167).
std::optional<uint32_t> mawSkillLevelCap(const std::string &canonicalSkill);
// Cover's chance to take a hit: 10 % + 1 % per point, at most 40 %, plus 15 % once after a Grandmaster's own melee hit
// (COMBAT_SPEC.md §7.3).
double mawCoverChance(double coverSkill, bool hitBonus);
// The mastery Cover needs to take a hit: Novice for physical attacks, Expert for other attacks, Master for spells.
SkillMastery mawCoverRequiredMastery(bool spell, bool physical);
// Damage one spell point absorbs: 1 + min(s, 50)^1.4 / 60, 5 at 50 (LG:92-101).
double mawManaShieldEfficiency(double manaShieldSkill);
// The share of each hit Mana Shield takes: 25/50/75/100 % by mastery.
double mawManaShieldAbsorbFraction(SkillMastery mastery);

struct MawManaShieldResult
{
    int damage = 0;
    int spellPointsSpent = 0;
};

// A hit after Mana Shield, and the spell points it took (calcManaShield, COMBAT_SPEC.md §7.6).
MawManaShieldResult mawManaShield(int damage, int spellPoints, double manaShieldSkill, SkillMastery mastery);

// The utility skills a party of one masters by base level alone (1, 4, 7 and 10), whatever the class allows
// (MAW's partySharedSkills, S:2126-2168).
inline constexpr std::array<const char *, 7> MawSoloMasterySkills = {
    "IdentifyItem", "Merchant", "RepairItem", "Perception", "DisarmTraps", "IdentifyMonster", "Alchemy",
};
bool mawIsSoloMasterySkill(const std::string &canonicalSkill);

// The base levels at which Cover, Mana Shield, Enlightenment and Retaliation become Expert, Master and Grandmaster on
// their own (S:176-181, 322-335); nothing for every other skill.
std::optional<std::array<uint32_t, 3>> mawSkillMasteryLadder(const std::string &canonicalSkill, MawSkillMode mode);

// A teacher's price before escalation: Normal and Austerity 1000/4000/20000, Doom 2000/10000/50000, Road to Insanity
// 10000/50000/250000, Beyond Madness 15000/300000/1250000.
enum class MawPriceMode : uint8_t
{
    Normal,
    Doom,
    RoadToInsanity,
    BeyondMadness,
};

int mawTeacherBasePrice(MawPriceMode mode, SkillMastery mastery);

// Raising a skill of the shared set from `newLevel - 1` to `newLevel` costs ceil(newLevel / (1 + n)), n being the
// other skills of the set at newLevel or above (S:238-262); raises over 1000 points are not discounted.
uint32_t mawSharedRaiseCost(uint32_t newLevel, uint32_t otherSkillsAtOrAbove);

// The skills of the shared set: weapons, the nine schools and the Dark Elf and Vampire abilities; hybrid classes
// (Shaman, Seraphim, Death Knight, Assassin lines) share only the schools and abilities.
bool mawIsSharedCostSkill(const std::string &canonicalSkill, bool hybridClass);

// What a respec gives back for the shared set: repeatedly lower the highest skill (the first on ties) by one,
// refunding ceil(level / skills at that level), until all are at 1 (R:58-123). Equals what raising them cost.
uint32_t mawSharedSetRefund(std::vector<uint32_t> levels);

// The points level-ups paid from level 2 to `level`: sum of 5 + floor(i / 10).
uint32_t mawLevelUpPoints(uint32_t level);

// Regeneration's HP per second: {5, 7.5, 10, 10} % x sqrt(estimated HP x full HP), the estimate being the expected
// character's HP at level skill^1.4; Grandmaster x (1 + (1 - HP / full)^2) (F:185-194, S:1353-1356).
double mawRegenerationHealthPerSecond(
    SkillMastery mastery,
    double estimatedHealth,
    double fullHealth,
    double health);

// Meditation's SP per second: {2, 2.5, 3, 4} % x sqrt(estimated mana x pool), the estimate being the expected
// character's mana at level skill^1.4 / 2 (F:196-205).
double mawMeditationSpellPerSecond(SkillMastery mastery, double estimatedMana, double pool);

// The Regeneration aura's HP per second: sqrt(full HP) x (level^0.65 x (1 + 0.05 x skill))^1.25 x 0.005, level and
// skill the holder's (SK:1363-1374).
double mawRegenerationAuraHealthPerSecond(
    double fullHealth, double holderLevel, double holderSkill, double buffScale = 1);
// A Regeneration potion's HP per second at its skill (floor(power / 2)), at Grandmaster: sqrt(full HP) x skill^1.25 x
// 5 / 1000 (Formulas.hpRegenBuffPerSec).
double mawRegenerationPotionHealthPerSecond(double fullHealth, double skill);

// The Meditation aura's SP per second: (0.01 x pool^0.35 x estimatedSkill^1.4 + 1) x (1 + 0.02 x skill), the estimate
// being the expected character's skill at the holder's level (SK:1466-1470).
double mawMeditationAuraSpellPerSecond(double pool, double estimatedSkill, double holderSkill, double buffScale = 1);

// The mana pool Meditation refills from while auras reserve part of it: ceil(full x (1 - reserved share)^0.5).
double mawMeditationPool(double fullSpellPoints, double reservedSpellPoints);

// Both regenerate twice as fast 20 seconds after the last HP lost, and four times as fast again with no enemy near.
double mawRegenerationMultiplier(bool recentHealthLoss, bool enemiesNear);

// A training hall's level cap under MAW: round(base^1.5 / 20) x 10 (Beyond Madness / 10), unlimited halls 2750 first,
// at least 10 (S:1627-1675).
int mawTrainingHallCap(int baseCap, bool madness);
}
