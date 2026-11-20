#include "game/mm9/Mm9HirelingCombat.h"

#include "game/gameplay/GameMechanics.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/party/Party.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
bool attackDealsDamage(const Mm9HirelingAttack &attack)
{
    return attack.present && attack.damage.diceRolls * attack.damage.diceSides + attack.damage.bonus > 0;
}
}

Mm9HirelingAction chooseMm9HirelingAction(
    const Mm9Hireling &row,
    bool hasTarget,
    bool targetInMeleeReach,
    int spellRoll,
    bool swingWithoutTarget)
{
    Mm9HirelingAction action = {};

    // A spell wins: the casters never swing their melee dice (9.2).
    if (!row.spells.empty())
    {
        action.kind = Mm9HirelingActionKind::Spell;
        action.pSpell = row.spells.size() == 1 || spellRoll <= row.spell1SharePercent ? &row.spells[0] : &row.spells[1];
        return action;
    }

    if (hasTarget && targetInMeleeReach && attackDealsDamage(row.attack1))
    {
        action.kind = Mm9HirelingActionKind::Melee;
        action.pAttack = &row.attack1;
    }
    else if (hasTarget && !targetInMeleeReach && attackDealsDamage(row.attack2))
    {
        action.kind = Mm9HirelingActionKind::Ranged;
        action.pAttack = &row.attack2;
    }
    else if (swingWithoutTarget && attackDealsDamage(row.attack1))
    {
        action.kind = Mm9HirelingActionKind::Melee;
        action.pAttack = &row.attack1;
    }

    return action;
}

int rollMm9HirelingAttackDamage(
    const Mm9HirelingAttack &attack,
    const Character &hireling,
    bool melee,
    std::mt19937 &rng)
{
    const int rolled = GameMechanics::rollMonsterAttackDamage(
        attack.damage.diceRolls, attack.damage.diceSides, attack.damage.bonus, rng);
    const int buffs = melee ? hireling.magicalBonuses.meleeDamage : hireling.magicalBonuses.rangedDamage;
    return std::max(0, rolled + buffs);
}

bool mm9HirelingAttackHits(const Character &hireling, bool melee, int targetArmorClass, std::mt19937 &rng)
{
    const int attackBonus = melee ? hireling.magicalBonuses.meleeAttack : hireling.magicalBonuses.rangedAttack;
    return GameMechanics::monsterAttackHitsArmorClass(targetArmorClass, int(hireling.level), attackBonus, rng);
}
}
