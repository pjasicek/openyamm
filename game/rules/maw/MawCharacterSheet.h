#pragma once

#include "game/rules/SkillRules.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class MawRules;
class ItemTable;
struct ItemDefinition;
struct ItemRulesetFields;

// MAW's combat rows of a character (itemStats, devdocs/maw/COMBAT_SPEC.md §3.1-3.3, §3.5): every weapon's damage
// grows by its skill's percent per point, Armsmaster and the class terms add to it, each skill point is worth at
// least one damage; attack from the weapon skills, Armsmaster and Unarmed; armour class from the armour pieces, the
// armour and Shield skills' percent of them, Staff, Sword and Spear by the weapon's attack, and Dodging; the armour
// skills' resistance, and the party's staffs and Luck's effect on every resistance. Might multiplies melee damage; the
// class terms and the Heroism and Hammerhands auras add theirs.
CharacterCombatRows mawCombatRows(
    const MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    const CharacterStatValues &stats);

// A character's armour as MAW's armour popups show it (itemStats' armorAC, shieldAC and the skills' bonuses,
// zzMaw-Items.lua:2690-2998): the pieces' and the shield's own Armor Class, before Legendary 28 and the dragon
// triple, and what the body-armour skill (`bodySkill`, empty without leather, chain or plate) and Shield add.
struct MawArmorBreakdown
{
    double pieces = 0;
    double shield = 0;
    std::string bodySkill;
    int bodySkillArmor = 0;
    int bodySkillResistance = 0;
    int shieldSkillArmor = 0;
    int shieldSkillResistance = 0;
};

MawArmorBreakdown mawArmorBreakdown(const MawRules &rules, const Character &character, const ItemTable &itemTable);

// The resistance a member's staff gives every party member: Staff's percent of the weapon's attack per skill point,
// counting ten more points (zzMaw-Items.lua:3294-3316); 0 without a staff in the main hand.
int mawStaffPartyResistance(const MawRules &rules, const Character &character, const ItemTable &itemTable);

// What a Staff, Sword or Spear gives the character holding it (zzMaw-Items.lua:3700-3716): its guard (MAW's hidden
// bonusBase, MawItemRules::weaponGuardBase) and the skill's percent of it by mastery per point, counting ten more
// points, as Armor Class; a staff gives the same as resistances to the whole party. Nothing for other weapons.
struct MawWeaponGuard
{
    int guard = 0;
    int armorClass = 0;
    int resistance = 0;
};

std::optional<MawWeaponGuard> mawWeaponGuard(
    const MawRules &rules,
    const Character &character,
    const ItemDefinition &weapon,
    const ItemRulesetFields &fields);

// An Assassin's Assassination bonus in its melee damage, the share a crowd around the target takes back (MAW's
// vars.assassinDamage, zzMaw-Items.lua:2899-2911): Armsmaster's and Assassination's flat damage at the weapon's
// skill multiplier, times Heroism; 0 for every other class.
double mawAssassinationBonus(const MawRules &rules, const Character &character, const ItemTable &itemTable);
}
