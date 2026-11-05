#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
// What a ruleset resolved for one monster when it spawned (devdocs/maw/HANDOFF.md phase 3); empty under Standard,
// whose numbers live in the actor's own fields. Saved with the actor, so random rolls (bosses) survive a reload and a
// difficulty change can re-resolve the numbers from the same level and rolls.
struct ActorRulesetFacts
{
    // The actor's level (not capped at 255), its family's B-tier level and its tier (1-3 for A-C, 0 when unknown).
    int level = 0;
    int familyLevel = 0;
    uint8_t tier = 0;
    // A boss's affix (0 for none) and the multipliers it rolled; the health one also carries a script's health scale.
    uint8_t bossAffix = 0;
    float bossHealthMultiplier = 1.0f;
    float bossDamageMultiplier = 1.0f;
    // A boss's draw for its level inside its band (MON:311-335), 0-1.
    float bossLevelDraw = 0.0f;
    // Base damage of attacks 1 and 2 before the ruleset's damage stages roll and mitigate it; monster spells deal
    // attack 1's damage times the spell's multiplier.
    float attack1Damage = 0.0f;
    float attack2Damage = 0.0f;
    uint32_t experience = 0;
    // The maximum HP these facts resolved to, so a re-resolve keeps the share of health the actor has left.
    int maxHp = 0;
    // Raised from the dead by the rules (MAW's Nightmare): named "Resurrected".
    bool risen = false;
    // Percent more physical damage the actor takes from a Grandmaster spear's blows (MAW's spearDamageIncrease).
    float spearDamageTaken = 0.0f;
    // Percent more damage of every kind the actor takes from the blows of a legendary 29 wearer.
    float legendaryDamageTaken = 0.0f;
    // One of the map's unique monsters (place_mon names 1-219): MAW levels it with the party, not the map.
    bool unique = false;
    // The special attack (a MonsterSpecialAttackKind, 0 for none) the Doom modes gave it on the map's fill, in place of
    // its own.
    uint8_t doomSpecialAttack = 0;
    // The party's hits on a Regenerating boss: it regenerates once hit, slower with each (MAW's mapvars.regenerating).
    uint16_t regeneratingHits = 0;
    // A Cryptic boss's hidden affix, the one it fights with (MAW's bossData Skills); 0 for every other boss, whose
    // bossAffix is its own.
    uint8_t crypticAffix = 0;

    bool empty() const
    {
        return *this == ActorRulesetFacts{};
    }

    bool operator==(const ActorRulesetFacts &) const = default;
};
}
