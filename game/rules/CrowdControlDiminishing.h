#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <random>
#include <unordered_map>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
struct CrowdControlCast;
enum class SkillMastery;

// MAW's diminishing returns on crowd control (calcDebuffDuration, SP:1817-1852) for groups 2 (fear and control) and 3
// (paralysis): a duration is shortened by the share of the last 20 seconds the target spent under the group's
// control, 0 once it is immune, and recorded; a boss holds half of what is recorded. MAW's rules keep one for every
// monster; under Standard rules each world keeps one for its monsters with the boss modifier (MonsterModifierSet::boss,
// devdocs/MONSTER_MODIFIERS.md). Runtime only.
class CrowdControlDiminishingReturns
{
public:
    static constexpr int ControlGroup = 2;
    static constexpr int ParalyzeGroup = 3;

    // The seconds the target is held, recorded under its key; groups other than 2 and 3 pass unchanged.
    double apply(uint64_t targetKey, int group, double nowSeconds, double seconds, bool boss);
    void clear();

private:
    std::unordered_map<uint64_t, std::array<std::vector<std::pair<double, double>>, 2>> m_history;
};

// Standard rules on a boss-modifier monster (cast.pBossHistory set): MAW's durations through MAW's diminishing returns
// for Stun (MAW's chance, one game minute plus skill x mastery ticks) and MAW's group 2 and 3 crowd-control spells
// (charm, berserk, fear, enslave, turn and control undead, paralyze; no Ascension under Standard), held as a boss. A
// monster immune to the spell's school (resistance 200) stays immune. Nothing for the other spells (slow, shrinking
// ray: Standard's own roll and duration).
std::optional<float> bossCrowdControlSeconds(const CrowdControlCast &cast, std::mt19937 &rng);

// Standard rules on a boss-modifier monster: a blow's stun (Standard's Master mace) or paralysis (its Grandmaster
// mace) becomes MAW's weapon paralysis, 2 seconds at Master and 4 at Grandmaster, through Paralyze's diminishing
// returns as a boss (Damage.lua:266-305).
float bossBlowCrowdControlSeconds(CrowdControlDiminishingReturns &history, uint64_t targetKey, double nowSeconds,
    bool grandmaster);

// Standard rules on a boss-modifier monster: a blow's fear or berserk (item effects) lasts as MAW's Fear or Berserk
// spell (spellId) at the blow's mastery, without resistance or Ascension, through the control group's diminishing
// returns as a boss. 0 for a spell that is not MAW crowd control.
float bossBlowControlSeconds(CrowdControlDiminishingReturns &history, uint64_t targetKey, double nowSeconds,
    uint32_t spellId, SkillMastery mastery);
}
