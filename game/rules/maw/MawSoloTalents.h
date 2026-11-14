#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
struct Character;
class Party;

// The talents' effects inside MAW's rules (devdocs/solo_action/TALENTS.md, tree v2: TALENT_TREE_V2_BUILD.md). Every
// function is a no-op for a character with no talents; the callers check that the game is a solo run
// (MawRules::options().soloRun) first.
namespace MawSoloTalents
{
// The passives' stat and resistance shares (Weapon Training, Marksman, Attunement, Resolve, Steady Aim while still),
// added to the magical bonuses after the class bonuses.
void applyPassives(Character &member);
// Ticks cooldowns and timed effects, Onslaught's stacks, Cheat Death, Steady Aim's stillness and Quickfoot's speed
// (`calm`: no yellow alert); refreshes the stats when Steady Aim turns on or off.
void update(Party &party, float partyX, float partyY, bool calm, float deltaSeconds);
// Onslaught: a kill adds a stack and refreshes them all.
void noteKill(Character &member);
// Onslaught: the share of the normal attack recovery (1: none).
float attackRecoveryScale(const Character &member);
// What is left of a blow on the member: Shield Wall, Unbroken, and Cheat Death's cut while it lasts.
int absorbDamage(const Character &member, int damage, int maximumHealth);
// Cheat Death, after everything else absorbed what it could: a blow that would kill the member (HP `currentHealth`)
// leaves 5 % of `maximumHealth` instead, and starts the cut and the cooldown.
int cheatDeath(Character &member, int damage, int currentHealth, int maximumHealth);
// Attunement and a surging spell: the damage and healing multipliers.
double spellDamageScale(const Character &caster);
double healScale(const Character &caster);
// Overload: an area spell's multiplier for the living monsters near its target (itself included).
double overloadScale(const Character &caster, int monstersNearTarget);
// Bloodthirst: the leech share added to melee, bow and spells, and the divisor of the leech floor (5 without it).
double leechBonus(const Character &member);
double leechFloorDivisor(const Character &member);
// Spell Surge armed: the next spell is free.
bool nextSpellFree(const Character &caster);
// A cast spends an armed surge (its damage window opens).
void spendSurge(Character &caster);
}
}
