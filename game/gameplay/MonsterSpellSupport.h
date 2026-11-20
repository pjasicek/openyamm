#pragma once

#include "game/party/SkillData.h"

#include <array>
#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
struct MonsterModifierSet;

bool isMonsterProjectileSpellName(const std::string &spellName);
bool isMonsterSelfBuffSpellName(const std::string &spellName);
bool isMonsterSelfActionSpellName(const std::string &spellName);
bool isKnownUnsupportedMonsterSpellName(const std::string &spellName);
// Paralyze and Fear: debuffs with no damage of their own. A monster casts one only as the carrier of its
// spell_conditions condition (a projectile that deals no damage); without a condition for that spell slot it stays
// unsupported, as for the MM6-MM8 rows that list Paralyze.
bool isMonsterConditionSpellName(const std::string &spellName);
bool isMonsterConditionSpellId(int spellId);
// The projectiles one monster cast fires: Sparks a volley by its mastery (3 Normal, 5 Expert, 7 Master, 9 Grandmaster,
// as MM6-MM8 monsters cast it; none counts as Normal), every other spell one.
uint32_t monsterSpellProjectileCount(uint32_t spellId, SkillMastery mastery);
// Where shot projectileIndex of a volley of projectileCount flies: the volley spreads evenly over a 60 degree fan
// centred on the line from source to target (MM6-MM8's monster Sparks), at the target's distance (at least 512) and
// height. A single shot flies at the target itself.
std::array<float, 3> monsterSpellVolleyTarget(
    const std::array<float, 3> &source,
    const std::array<float, 3> &target,
    uint32_t projectileCount,
    uint32_t projectileIndex);
// The spell of slot 1 or 2 is a condition spell and the monster's spell_conditions gives that slot a condition.
bool monsterConditionSpellCastSupported(
    const std::string &spellName,
    const MonsterModifierSet *pModifiers,
    int spellSlot);
}
