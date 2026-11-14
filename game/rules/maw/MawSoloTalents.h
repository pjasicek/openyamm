#pragma once

#include "game/party/CharacterState.h"

#include <cstddef>

namespace OpenYAMM::Game
{
struct Character;
class Party;

// The talents' effects inside MAW's rules (devdocs/solo_action/TALENTS.md). Every function is a no-op for a character
// with no talents; the callers check that the game is a solo run (MawRules::options().soloRun) first.
namespace MawSoloTalents
{
// The passives' stat and resistance shares (Weapon Training, Marksman, Attunement, Resolve, Steady Aim while still),
// added to the magical bonuses after the class bonuses.
void applyPassives(Character &member);
// Ticks cooldowns and timed effects, Mana Font's spell points and Steady Aim's stillness; refreshes the stats when
// Steady Aim turns on or off.
void update(Party &party, float partyX, float partyY, float deltaSeconds);
// Frenzy: the share of the normal attack recovery (1: none).
float attackRecoveryScale(const Character &member);
// Shield Wall: the damage left after the cut.
int absorbDamage(const Character &member, int damage);
// Attunement and a surging spell: the damage and healing multipliers.
double spellDamageScale(const Character &caster);
double healScale(const Character &caster);
// Spell Surge armed: the next spell is free.
bool nextSpellFree(const Character &caster);
// A cast spends an armed surge (its damage window opens).
void spendSurge(Character &caster);
// Purify's immunity holds this condition off.
bool blocksCondition(const Character &member, CharacterCondition condition);
}
}
