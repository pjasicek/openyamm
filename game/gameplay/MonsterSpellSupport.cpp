#include "game/gameplay/MonsterSpellSupport.h"

#include "game/StringUtils.h"

#include <algorithm>
#include <array>

namespace OpenYAMM::Game
{
bool isMonsterProjectileSpellName(const std::string &spellName)
{
    static constexpr std::array<const char *, 27> ProjectileSpellNames = {
        "fire bolt",
        "fireball",
        "incinerate",
        "lightning bolt",
        "implosion",
        "meteor shower",
        "ice bolt",
        "icebolt",
        "ice blast",
        "iceblast",
        "acid burst",
        "deadly swarm",
        "blades",
        "rock blast",
        "mass distortion",
        "sparks",
        "mind blast",
        "psychic shock",
        "psychic shockt",
        "harm",
        "flying fist",
        "light bolt",
        "spirit lash",
        "toxic cloud",
        "shrapmetal",
        "dragon breath",
        "poison spray",
    };

    const std::string lowered = toLowerCopy(spellName);
    return std::find(ProjectileSpellNames.begin(), ProjectileSpellNames.end(), lowered)
        != ProjectileSpellNames.end();
}

bool isMonsterSelfBuffSpellName(const std::string &spellName)
{
    static constexpr std::array<const char *, 11> SelfBuffSpellNames = {
        "bless",
        "day of protection",
        "fate",
        "hammerhands",
        "haste",
        "heroism",
        "hour of power",
        "pain reflection",
        "shield",
        "stone skin",
        "stoneskin",
    };

    const std::string lowered = toLowerCopy(spellName);
    return std::find(SelfBuffSpellNames.begin(), SelfBuffSpellNames.end(), lowered)
        != SelfBuffSpellNames.end();
}

bool isMonsterSelfActionSpellName(const std::string &spellName)
{
    const std::string lowered = toLowerCopy(spellName);
    return lowered == "heal"
        || lowered == "power cure"
        || lowered == "dispel magic"
        || isMonsterSelfBuffSpellName(lowered);
}
}
