#pragma once

#include <cstdint>
#include <random>

namespace OpenYAMM::Game
{
struct Character;
struct Mm9Hireling;
struct Mm9HirelingAttack;
struct Mm9HirelingSpell;

// What an active MM9 hireling does on the Attack or quick-cast command (devdocs/mm9/MM9_HIRELINGS.md 9.2).
enum class Mm9HirelingActionKind : uint8_t
{
    // Nothing reaches: the hireling is passed over.
    None,
    // Attack 1 on the creature in melee reach, or swung at nothing (swingWithoutTarget).
    Melee,
    // Attack 2 (the retainers' Arrow) on a creature beyond reach.
    Ranged,
    // One of the casters' two spells.
    Spell,
};

struct Mm9HirelingAction
{
    Mm9HirelingActionKind kind = Mm9HirelingActionKind::None;
    const Mm9HirelingAttack *pAttack = nullptr;
    const Mm9HirelingSpell *pSpell = nullptr;
};

// MM9's choice (object@0x100b3940; chooseSpell object@0x10053210): a hireling with spells always casts, the first
// spell when spellRoll (1-100) is at most its spell1_share_percent, else the second; otherwise attack 1 on a target in
// melee reach, attack 2 on one beyond it, and nothing without a target or a fitting attack. With swingWithoutTarget
// (turn-based combat, where a hireling's turn waits for the command as a member's does) that nothing becomes attack 1
// swung at the air, so the command always spends the turn.
Mm9HirelingAction chooseMm9HirelingAction(
    const Mm9Hireling &row,
    bool hasTarget,
    bool targetInMeleeReach,
    int spellRoll,
    bool swingWithoutTarget = false);

// A hireling's blow or shot uses the monster attack rules, as its numbers are a MONSTERS row: the row's dice (with the
// party's damage buffs on the hireling, Heroism and Hammerhands), and the monster hit roll at the hireling's level
// (with Bless).
int rollMm9HirelingAttackDamage(
    const Mm9HirelingAttack &attack,
    const Character &hireling,
    bool melee,
    std::mt19937 &rng);
bool mm9HirelingAttackHits(const Character &hireling, bool melee, int targetArmorClass, std::mt19937 &rng);
}
