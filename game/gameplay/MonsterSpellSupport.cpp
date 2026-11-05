#include "game/gameplay/MonsterSpellSupport.h"

#include "game/StringUtils.h"
#include "game/gameplay/GameMechanics.h"
#include "game/party/SpellIds.h"
#include "game/tables/MonsterModifiers.h"

#include <algorithm>
#include <cmath>
#include <unordered_set>

namespace OpenYAMM::Game
{
bool isMonsterProjectileSpellName(const std::string &spellName)
{
    static const std::unordered_set<std::string> ProjectileSpellNames = {
        "fire bolt", "fireball", "incinerate", "lightning bolt", "implosion", "meteor shower",
        "ice bolt", "icebolt", "ice blast", "iceblast", "acid burst", "deadly swarm", "blades",
        "rock blast", "mass distortion", "sparks", "mind blast", "psychic shock", "psychic shockt",
        "harm", "flying fist", "light bolt", "spirit lash", "toxic cloud", "shrapmetal", "dark grasp",
        "dragon breath", "poison spray"};

    const std::string lowered = toLowerCopy(spellName);
    return ProjectileSpellNames.find(lowered) != ProjectileSpellNames.end();
}

bool isMonsterSelfBuffSpellName(const std::string &spellName)
{
    static const std::unordered_set<std::string> SelfBuffSpellNames = {
        "bless", "day of protection", "fate", "hammerhands", "haste", "heroism", "hour of power",
        "pain reflection", "shield", "stone skin", "stoneskin"};

    const std::string lowered = toLowerCopy(spellName);
    return SelfBuffSpellNames.find(lowered) != SelfBuffSpellNames.end();
}

bool isMonsterSelfActionSpellName(const std::string &spellName)
{
    static const std::unordered_set<std::string> SelfActionSpellNames = {
        "heal", "power cure", "dispel magic", "bless", "day of protection", "fate", "hammerhands",
        "haste", "heroism", "hour of power", "pain reflection", "shield", "stone skin", "stoneskin"};

    const std::string lowered = toLowerCopy(spellName);
    return SelfActionSpellNames.find(lowered) != SelfActionSpellNames.end();
}

bool isKnownUnsupportedMonsterSpellName(const std::string &spellName)
{
    static const std::unordered_set<std::string> UnsupportedMonsterSpellNames = {
        "day-o-gods",
        "day of the gods",
        "fear",
        "finger of death",
        "mass curse",
        "paralyze",
    };

    const std::string lowered = toLowerCopy(spellName);
    return UnsupportedMonsterSpellNames.find(lowered) != UnsupportedMonsterSpellNames.end();
}

bool isMonsterConditionSpellName(const std::string &spellName)
{
    const std::string lowered = toLowerCopy(spellName);
    return lowered == "paralyze" || lowered == "fear";
}

bool isMonsterConditionSpellId(int spellId)
{
    return spellId > 0
        && (isSpellId(uint32_t(spellId), SpellId::Paralyze) || isSpellId(uint32_t(spellId), SpellId::Fear));
}

bool monsterConditionSpellCastSupported(
    const std::string &spellName,
    const MonsterModifierSet *pModifiers,
    int spellSlot)
{
    if (pModifiers == nullptr || !pModifiers->spellConditions || !isMonsterConditionSpellName(spellName))
    {
        return false;
    }

    const MonsterSpecialAttackKind condition =
        spellSlot == 1 ? pModifiers->spellConditions->spell1 : pModifiers->spellConditions->spell2;
    return condition != MonsterSpecialAttackKind::None;
}

uint32_t monsterSpellProjectileCount(uint32_t spellId, SkillMastery mastery)
{
    if (!isSpellId(spellId, SpellId::Sparks))
    {
        return 1;
    }

    switch (mastery)
    {
        case SkillMastery::Expert:
            return 5;
        case SkillMastery::Master:
            return 7;
        case SkillMastery::Grandmaster:
            return 9;
        case SkillMastery::None:
        case SkillMastery::Normal:
            break;
    }

    return 3;
}

std::array<float, 3> monsterSpellVolleyTarget(
    const std::array<float, 3> &source,
    const std::array<float, 3> &target,
    uint32_t projectileCount,
    uint32_t projectileIndex)
{
    if (projectileCount <= 1)
    {
        return target;
    }

    constexpr float VolleyArcRadians = 3.14159265f / 3.0f;
    const float deltaX = target[0] - source[0];
    const float deltaY = target[1] - source[1];
    const float distance = std::max(512.0f, std::sqrt(deltaX * deltaX + deltaY * deltaY));
    const float yaw = std::atan2(deltaY, deltaX)
        + GameMechanics::projectileFanYawOffsetRadians(projectileCount, projectileIndex, VolleyArcRadians);
    return {source[0] + std::cos(yaw) * distance, source[1] + std::sin(yaw) * distance, target[2]};
}
}
