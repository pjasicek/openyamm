#pragma once

#include <cstdint>
#include <string_view>

namespace OpenYAMM::Game
{
struct Character;
class Party;

// The talents' effects inside MAW's rules (devdocs/solo_action/TALENTS.md, tree v2: TALENT_TREE_V2_BUILD.md). Every
// function is a no-op for a character with no talents; the callers check that the game is a solo run
// (MawRules::options().soloRun) first.
namespace MawSoloTalents
{
// Conditioning, and Steady Aim's Luck while still: their percent of each whole stat (base, permanent bonuses, items
// and buffs), added to the magical bonuses before HP and SP are derived from the stats.
void applyStatPassives(Character &member);
// Ticks cooldowns and timed effects, Onslaught's stacks, Cheat Death, Phase, the stillness Steady Aim and Nimble read,
// Quickfoot's speed and rage's limit and drain (`calm`: no yellow alert); refreshes the stats when Steady Aim turns on
// or off.
void update(Party &party, float partyX, float partyY, bool calm, float deltaSeconds);
// A kill: Onslaught adds a stack and refreshes them all, and the talents' cooldown_per_kill comes off (Charge).
void noteKill(Character &member);
// Onslaught: the share of a normal recovery, a weapon attack's or a spell cast's (1: none).
float attackRecoveryScale(const Character &member);
// What is left of a blow on the member: Unbroken, and Cheat Death's cut while it lasts.
int absorbDamage(const Character &member, int damage, int maximumHealth);

// A hit on the member, for the solo run's own cuts of it.
struct IncomingHit
{
    bool physical = false;
    // A monster's attack (a trap or a fall is not).
    bool monsterAttack = false;
    // A monster's missile or spell, and how far the monster stood from the party when it loosed it (negative:
    // unknown).
    bool missile = false;
    float firedFromDistance = -1.0f;
    // Living hostile monsters within Outnumbered's reach (MawRules::outnumberedMonsters).
    int nearbyMonsters = 0;
};

// What the talents leave of a hit on the member (1: all of it): Spell Suppression (a hit that is not physical),
// Vanguard (a missile loosed from beyond its distance) and Outnumbered (per nearby monster), both with the melee weapon
// in the arms, Nimble (while moving) and Phase (after a Blink). They multiply, and together leave at least the table's
// damage_floor.
double incomingDamageScale(const Character &member, const IncomingHit &hit);

// Battle Frenzy: what a melee blow's damage is multiplied by for the monsters within its reach
// (MawRules::battleFrenzyMonsters).
double battleFrenzyScale(const Character &attacker, int nearbyMonsters);
// How far a pack talent (Outnumbered, Battle Frenzy) counts monsters: its `distance` in talents.yml.
float packReach(std::string_view talentId);
// Long Shot: what an arrow's damage is multiplied by for the distance it flew.
double longShotScale(const Character &shooter, float flightDistance);
// What a damage spell gains, as a fraction added to 1: Spell Surge, Overload on an area spell for the monsters its
// blast struck (itself included) and Opening Volley on a monster at full health. They add; they do not multiply.
double spellDamageBonus(const Character &caster, bool areaSpell, int blastMonsters, bool targetAtFullHealth);
// Breach: the share of a monster's resistance the caster's spells ignore (0: none).
double breachShare(const Character &caster);
// Arcane Ward: the share of the SP a Mana Shield spends for what it absorbs (1: all).
double manaShieldCostScale(const Character &member);
// Expose Weakness and Hamstring, a critical bow hit's: the percent and the seconds (0 without the talent).
float exposeWeaknessPercent(const Character &shooter);
float exposeWeaknessSeconds();
float hamstringPercent(const Character &shooter);
float hamstringSeconds();

// Rage, the Arms path's bar (no-ops for a character without it). A melee blow that hit: the share of the monster's
// full HP it took and its recovery; a hit taken: the share of the member's full HP it took.
void gainRageFromBlow(Character &member, double monsterBarShare, float recoverySeconds, bool extraBlow);
void gainRageFromHit(Character &member, double ownBarShare);
// Spell Surge's cooldown_per_cast: a damaging spell of the member's hit a monster. Once for a cast: the hits that
// follow within a moment are the same cast's.
void noteSpellHit(Character &caster);
// Cheat Death, after everything else absorbed what it could: a blow that would kill the member (HP `currentHealth`)
// leaves 5 % of `maximumHealth` instead, and starts the cut and the cooldown.
int cheatDeath(Character &member, int damage, int currentHealth, int maximumHealth);
// Bloodthirst: the leech share added to melee, bow and spells, and the divisor of the leech floor (5 without it).
double leechBonus(const Character &member);
double leechFloorDivisor(const Character &member);
// Manathirst: the share of the SP bar given back the way leech heals, and its floor divisor (5 without it).
double manaLeechShare(const Character &member);
double manaLeechFloorDivisor(const Character &member);
// Manathirst: whether an area spell's hit on one more monster still gives SP. One cast counts at most three monsters:
// the hits within a short window after the first.
bool takeAreaManaLeech(Character &member);
// Spell Surge armed: the next damaging spell is free.
bool nextSpellFree(const Character &caster);
// A damaging cast spends an armed surge (its damage window opens).
void spendSurge(Character &caster);
// The solo run's early monster cut for the character (SoloTalentTable::earlyMonsterCut; not a talent, a rule of the
// run): by the level its experience has earned, so an untrained character does not keep a larger cut.
double earlyMonsterCut(const Character &member);
// The share of the Regeneration skill's own healing a solo character without the skill in its class gets at its
// level (SoloTalentTable::earlyRegeneration; a rule of the run), by the same level as the cut.
double earlyRegeneration(const Character &member);
}
}
