#include "game/party/BattleOrders.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
// The blow's reach (GameplayActionController's CharacterMeleeAttackDistance).
constexpr float MeleeReachDistance = 407.2f;

// spells.txt's names of the spells a quick or attack cast aims at a member (PartySpellSystem::
// hasQuickCastCharacterTarget); a save is read without the spell table.
constexpr std::array<std::string_view, 11> MemberSpellNames = {"Heal", "Cure Disease", "Remove Curse", "Remove Fear",
    "Cure Paralysis", "Cure Insanity", "Cure Weakness", "Cure Poison", "Raise Dead", "Resurrection", "Stone to Flesh"};
}

float battleOrderDistanceBound(uint16_t units)
{
    return units == BattleOrderMeleeReach ? MeleeReachDistance : float(units);
}

bool battleOrderDistanceHolds(const BattleOrderDistance &distance, std::optional<float> targetDistance)
{
    if (!targetDistance)
    {
        return false;
    }

    // A minimum is exclusive ("beyond melee reach"), a maximum inclusive ("in melee reach"), so the two meet exactly.
    if (distance.minimum > 0 && *targetDistance <= battleOrderDistanceBound(distance.minimum))
    {
        return false;
    }

    return distance.maximum >= BattleOrderMaximumDistance
        || *targetDistance <= battleOrderDistanceBound(distance.maximum);
}

bool battleOrderConditionsHold(const BattleOrder &order, const BattleOrderSituation &situation, uint32_t manaCost)
{
    if (order.distance && !battleOrderDistanceHolds(*order.distance, situation.targetDistance))
    {
        return false;
    }

    if (order.allyHealthBelowPercent
        && situation.lowestAllyHealthShare * 100.0f >= float(*order.allyHealthBelowPercent))
    {
        return false;
    }

    if (order.place != BattleOrderPlace::Anywhere
        && (order.place == BattleOrderPlace::Indoors) != situation.indoors)
    {
        return false;
    }

    if (order.keepSpellPointsPercent && order.kind == BattleOrderKind::Spell)
    {
        const int kept = int(std::ceil(float(situation.maximumSpellPoints) * *order.keepSpellPointsPercent / 100.0f));

        if (situation.spellPoints - int(manaCost) < kept)
        {
            return false;
        }
    }

    return true;
}

bool upkeepBuffDue(float remainingSeconds, float castSeconds, std::optional<uint16_t> renewBelowMinutes)
{
    if (remainingSeconds <= 0.0f)
    {
        return true;
    }

    return renewBelowMinutes.has_value()
        && remainingSeconds < std::min(float(*renewBelowMinutes) * 60.0f, castSeconds * 0.5f);
}

void setAttackSpell(const std::string &attackSpellName, std::vector<BattleOrder> &orders,
    BattleOrderFallback &fallback)
{
    if (attackSpellName.empty())
    {
        orders.clear();
        fallback = BattleOrderFallback::Weapon;
        return;
    }

    BattleOrder order;
    order.spellName = attackSpellName;
    orders = {order};
    bool forMember = false;

    for (const std::string_view name : MemberSpellNames)
    {
        forMember = forMember || name == attackSpellName;
    }

    fallback = forMember ? BattleOrderFallback::Hold : BattleOrderFallback::Weapon;
}

bool isAttackSpell(const std::string &attackSpellName, const std::vector<BattleOrder> &orders,
    BattleOrderFallback fallback)
{
    std::vector<BattleOrder> expectedOrders;
    BattleOrderFallback expectedFallback = BattleOrderFallback::Weapon;
    setAttackSpell(attackSpellName, expectedOrders, expectedFallback);
    return !attackSpellName.empty() && orders == expectedOrders && fallback == expectedFallback;
}
}
