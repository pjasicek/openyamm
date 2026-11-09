#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// Battle orders (devdocs/BATTLE_ORDERS.md): what a member's Attack does. The orders are tried top to bottom and the
// first whose conditions all hold and that can be carried out now is done; when none can, the fallback. Set in the
// Battle Orders window (the spellbook's button, the Battle Orders key); the same in every ruleset.
enum class BattleOrderKind : uint8_t
{
    Spell,
    // A blow; only with a target in the weapon's reach.
    Melee,
    // The ranged weapon (bow, crossbow, wand, blaster; a dragon's breath); only with one.
    Shoot,
};

// What Attack does when no order applies.
enum class BattleOrderFallback : uint8_t
{
    // The weapon as before orders: a blow in reach, the ranged weapon beyond.
    Weapon,
    // Nothing: in real time the press goes to the next ready member and the holder stays ready; in turn-based mode the
    // holder passes (its melee recovery, as the Pass key).
    Hold,
};

// Distances in game units. The melee reach stands for the blow's exact reach (CharacterMeleeAttackDistance, 407.2).
constexpr uint16_t BattleOrderMeleeReach = 407;
// The ranged attack distance; as an order's maximum it means no limit.
constexpr uint16_t BattleOrderMaximumDistance = 5120;
constexpr size_t BattleOrderLimit = 6;

struct BattleOrderDistance
{
    uint16_t minimum = 0;
    uint16_t maximum = BattleOrderMaximumDistance;

    bool operator==(const BattleOrderDistance &) const = default;
};

struct BattleOrder
{
    BattleOrderKind kind = BattleOrderKind::Spell;
    // The spell's table name (BattleOrderKind::Spell).
    std::string spellName;
    // Off: skipped, its settings kept.
    bool enabled = true;
    // The target's distance from the party, in game units; no target fails it.
    std::optional<BattleOrderDistance> distance;
    // Some member (the caster included) is below this share of their HP, in percent.
    std::optional<uint8_t> allyHealthBelowPercent;
    // The cast must leave at least this share of the caster's SP, in percent.
    std::optional<uint8_t> keepSpellPointsPercent;

    bool operator==(const BattleOrder &) const = default;
};

// What the conditions are checked against at the press.
struct BattleOrderSituation
{
    // The attack's target's distance from the party (edge to edge); none without a target.
    std::optional<float> targetDistance;
    // The lowest share of HP among the members who can still be healed (0..1).
    float lowestAllyHealthShare = 1.0f;
    int spellPoints = 0;
    int maximumSpellPoints = 0;
};

// A bound as a distance: the melee reach is the blow's exact reach.
float battleOrderDistanceBound(uint16_t units);
bool battleOrderDistanceHolds(const BattleOrderDistance &distance, std::optional<float> targetDistance);
// The order's own conditions (distance, an ally's HP, SP kept after the cast's manaCost); not whether the spell or
// weapon can be used.
bool battleOrderConditionsHold(const BattleOrder &order, const BattleOrderSituation &situation, uint32_t manaCost = 0);

// The single attack spell of a save from before battle orders and of the spellbook's Attack Spell button: the orders
// become that one unconditional order, or none for an empty name (the weapon). A spell for a member (Heal, a cure)
// holds when nobody needs it, as the attack spell did (OY-190).
void setAttackSpell(const std::string &attackSpellName, std::vector<BattleOrder> &orders,
    BattleOrderFallback &fallback);
// Whether the orders and fallback are exactly what setAttackSpell makes of this spell.
bool isAttackSpell(const std::string &attackSpellName, const std::vector<BattleOrder> &orders,
    BattleOrderFallback fallback);
}
