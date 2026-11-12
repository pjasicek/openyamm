#include "game/rules/maw/MawCharacterSheet.h"

#include "game/party/Party.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using MasteryRow = std::array<double, 5>;

// Per point by mastery none, N, E, M, G (zzMAW-Skills.lua :45-138, COMBAT_SPEC §1.2).
constexpr MasteryRow WeaponAttack = {0, 1, 2, 3, 4};
constexpr MasteryRow SpearAttack = {0, 2, 4, 6, 8};
constexpr MasteryRow UnarmedAttack = {0, 2, 2, 3, 3};
constexpr MasteryRow StaffArmor = {0, 0, 2, 3, 4};
constexpr MasteryRow SwordArmor = {0, 0, 0, 1, 2};
constexpr MasteryRow SpearArmor = {0, 0, 4, 6, 8};
constexpr MasteryRow DodgingArmor = {0, 4, 5, 6, 6};
constexpr MasteryRow BodyArmorPercent = {0, 3, 4, 5, 6};
constexpr MasteryRow ShieldArmorPercent = {0, 4, 6, 8, 10};
constexpr MasteryRow LeatherResistancePercent = {0, 2, 3, 4, 5};
constexpr MasteryRow ChainResistancePercent = {0, 1, 2, 3, 4};
constexpr MasteryRow PlateResistancePercent = {0, 0, 1, 2, 3};
constexpr MasteryRow ShieldResistancePercent = {0, 4, 6, 8, 10};
// Armsmaster damage per point by mastery none, N, E, M, G, Supreme.
constexpr std::array<double, 6> ArmsmasterDamage = {0, 0, 1, 1, 1.5, 2};

struct Skill
{
    double level = 0;
    int mastery = 0;
};

Skill skillOf(const Character &character, const std::string &name)
{
    const CharacterSkill *pSkill = character.findSkill(name);
    Skill skill;
    skill.level = (pSkill != nullptr ? double(pSkill->level) : 0.0) + character.skillBonus(name);
    skill.mastery = pSkill != nullptr ? int(pSkill->mastery) : 0;
    return skill;
}

double row(const MasteryRow &values, int mastery)
{
    return values[size_t(std::clamp(mastery, 0, 4))];
}

bool isMeleeWeaponSkill(const std::string &skill)
{
    static const std::array<const char *, 8> Skills = {
        "Staff", "Sword", "Dagger", "Axe", "Spear", "Mace", "Blaster", "Club",
    };
    return std::find(Skills.begin(), Skills.end(), skill) != Skills.end();
}

// Supreme Armsmaster reads as a fifth mastery rank, from the effective level (SKL-3).
int armsmasterMastery(const MawRules &rules, const Character &character)
{
    const CharacterSkill *pSkill = character.findSkill("Armsmaster");
    return pSkill == nullptr ? 0 : mawSupremeArmsmaster(rules, character, true) ? 5 : int(pSkill->mastery);
}

// A dragon's level for its fangs, breath and scales: its own; when over 1.2 times the party's banked level plus one,
// half its own or that, whichever is lower; at most 600 (900 in Beyond Madness; MCC:707-741).
double dragonLevel(const MawRules &rules, const Character &character)
{
    // MAW's getPartyLevel(4): every continent's bank (MCC:730-741, CLS-10; MMMerge's fourth bank held nothing).
    const double party = std::max(1.0, rules.state().totalLevel()) + 1;
    double level = character.level;

    if (level / party > 1.2)
    {
        level = std::min(level / 2, party);
    }

    return std::min(level, rules.options().challengeMode == RulesetChallengeMode::BeyondMadness ? 900.0 : 600.0);
}

// Dragons fight with Fangs (Unarmed) and breathe with Dragon Ability instead of weapons; Scales (Dodging) give armour
// and resistances by their level (MCC:749-815, race_bonuses.yml dragon).
void applyDragonRows(const MawRules &rules, const Character &character, const CharacterStatValues &stats,
    CharacterCombatRows &rows)
{
    static constexpr std::array<double, 5> FangDamage = {0, 4, 6, 8, 10};
    static constexpr std::array<double, 5> FangAttack = {0, 2, 3, 4, 5};
    static constexpr std::array<double, 5> BreathDamage = {0, 3, 4, 5, 6};
    static constexpr std::array<double, 5> ScalesArmor = {0, 2, 3, 3, 4};
    static constexpr std::array<double, 5> ScalesResistance = {0, 1, 1, 2, 3};
    const double level = dragonLevel(rules, character);
    const double might = stats.might;
    const double mightEffect = mawStatEffect(stats.might);
    const Skill fangs = skillOf(character, "Unarmed");
    const Skill breath = skillOf(character, "DragonAbility");
    const Skill scales = skillOf(character, "Dodging");
    const auto rank = [](const Skill &skill)
    {
        return size_t(std::clamp(skill.mastery, 0, 4));
    };

    const double bite = (1 + FangDamage[rank(fangs)] * fangs.level / 100) * (2 * level + 30);
    const double biteRoll = (bite * (1 + might / 1000) + mightEffect * might / 1000) * (1 + 0.015 * fangs.level);
    // The bite is an item bonus on top of the engine's melee base, which carries Might's effect (CL:765-772).
    rows.meleeMinimumDamage = int(mawRound(biteRoll * 0.75) + mightEffect);
    rows.meleeMaximumDamage = int(mawRound(biteRoll * 1.25) + mightEffect);
    rows.meleeAttack = mawStatEffect(stats.accuracy) + int(FangAttack[rank(fangs)] * fangs.level + 10);

    const double flame = ((1 + BreathDamage[rank(breath)] * breath.level / 100) * (20 + 2 * level) + mightEffect)
        * (1 + might / 1000) * (1 + 0.015 * breath.level);
    rows.rangedMinimumDamage = int(mawRound(flame * 0.75));
    rows.rangedMaximumDamage = int(mawRound(flame * 1.25));
    rows.rangedAttack = mawStatEffect(stats.accuracy) + int(breath.level);

    // Scales replace Dodging's own armour.
    rows.armorClass += int(mawRound((1 + ScalesArmor[rank(scales)] / 100 * scales.level) * (level + 40)
        - row(DodgingArmor, scales.mastery) * scales.level));
    const int resistance = int(mawRound(ScalesResistance[rank(scales)] / 100 * scales.level * (level + 40)));

    for (int *pResistance : {&rows.resistances.fire, &rows.resistances.air, &rows.resistances.water,
             &rows.resistances.earth, &rows.resistances.mind, &rows.resistances.body})
    {
        *pResistance += resistance;
    }
}

struct HeldWeapon
{
    const ItemDefinition *pDefinition = nullptr;
    const EquippedItemRuntimeState *pState = nullptr;
    std::string skill;
    bool bow = false;
};
}

CharacterCombatRows mawCombatRows(
    const MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    const CharacterStatValues &stats)
{
    const MawItemRules &itemRules = rules.itemRules();
    const int wearerLevel = int(character.level);
    const auto equipped = [&itemTable](uint32_t itemId) -> const ItemDefinition *
    {
        return itemId != 0 ? itemTable.get(itemId) : nullptr;
    };
    const ItemDefinition *pOffHand = character.equipmentRuntime.offHand.broken ? nullptr
                                                                               : equipped(character.equipment.offHand);
    const ItemDefinition *pMainHand =
        character.equipmentRuntime.mainHand.broken ? nullptr : equipped(character.equipment.mainHand);
    const ItemDefinition *pBow = character.equipmentRuntime.bow.broken ? nullptr : equipped(character.equipment.bow);
    const bool shieldInOffHand = pOffHand != nullptr && canonicalSkillName(pOffHand->skillGroup) == "Shield";
    const std::string mainSkill = pMainHand != nullptr ? canonicalSkillName(pMainHand->skillGroup) : std::string();

    std::vector<HeldWeapon> weapons;
    const auto addWeapon = [&](const ItemDefinition *pItem, const EquippedItemRuntimeState &state, bool bow)
    {
        if (pItem == nullptr)
        {
            return;
        }

        const std::string skill = mawWeaponSkill(character, *pItem);

        if ((bow && skill == "Bow") || (!bow && isMeleeWeaponSkill(skill)))
        {
            weapons.push_back({pItem, &state, skill, bow});
        }
    };
    addWeapon(pOffHand, character.equipmentRuntime.offHand, false);
    addWeapon(pMainHand, character.equipmentRuntime.mainHand, false);
    addWeapon(pBow, character.equipmentRuntime.bow, true);

    // A blaster in the main hand puts every other weapon away, the bow too (IT:2816-2819).
    if (mainSkill == "Blaster")
    {
        std::erase_if(
            weapons,
            [](const HeldWeapon &weapon)
            {
                return weapon.skill != "Blaster";
            });
    }

    // Two axes in the hands lose 10 % of their damage per two-handed one; a halberd counts as a two-handed axe,
    // whichever skill wields it (IT:2858-2875).
    int twoHandedAxes = 0;
    int heldAxes = 0;

    for (const HeldWeapon &weapon : weapons)
    {
        const bool halberd = mawIsHalberd(weapon.pDefinition->itemId);

        if (!weapon.bow && (canonicalSkillName(weapon.pDefinition->skillGroup) == "Axe" || halberd))
        {
            ++heldAxes;
            twoHandedAxes += weapon.pDefinition->equipStat == "Weapon2" || halberd ? 1 : 0;
        }
    }

    double meleeAttackRow = 0;
    double meleeMinimumRow = 0;
    double meleeMaximumRow = 0;
    double rangedAttackRow = 0;
    double rangedMinimumRow = 0;
    double rangedMaximumRow = 0;
    std::vector<std::string> flooredSkills;
    const Skill armsmaster = {skillOf(character, "Armsmaster").level, armsmasterMastery(rules, character)};
    const double classFlat = mawClassMeleeFlatDamage(rules, character);
    const Skill unarmed = skillOf(character, "Unarmed");
    const Skill staff = skillOf(character, "Staff");

    for (const HeldWeapon &weapon : weapons)
    {
        const std::optional<MawWeaponDamage> damage =
            itemRules.weaponDamage(*weapon.pDefinition, weapon.pState->rulesetFields, wearerLevel);

        if (!damage)
        {
            continue;
        }

        const Skill weaponSkill = skillOf(character, weapon.skill);
        double bonus = damage->bonus;
        const double sides = damage->sides;
        const int dice = damage->diceCount;
        Skill arms = armsmaster;

        if (weapon.bow)
        {
            bonus += weaponSkill.level;
        }

        // Staves never get Armsmaster; a Grandmaster staff gets half of Unarmed in its place.
        if (weapon.skill == "Staff")
        {
            arms = staff.mastery >= 4 ? Skill{unarmed.level / 2, unarmed.mastery} : Skill{};
        }

        const double percent = weapon.skill == "Bow" || weapon.skill == "Blaster" ? 4 : 2;
        const double multiplier = 1 + weaponSkill.level * percent / 100;
        double side = sides * multiplier;
        double add = bonus * multiplier;
        double armsDamage = ArmsmasterDamage[size_t(std::clamp(arms.mastery, 0, 5))] * arms.level * multiplier;

        if (!weapon.bow && heldAxes >= 2)
        {
            side *= 1 - 0.1 * twoHandedAxes;
            add *= 1 - 0.1 * twoHandedAxes;
        }

        if (weapon.skill == "Staff")
        {
            armsDamage = 2 * arms.level * multiplier;
        }

        if (!weapon.bow)
        {
            armsDamage += classFlat * multiplier;
        }

        if (!weapon.bow && pOffHand != nullptr && !shieldInOffHand)
        {
            armsDamage /= 2;
        }

        if (weapon.skill == "Blaster")
        {
            armsDamage = 0;
        }

        // Each skill point is worth at least one point of damage, once per weapon skill.
        if (std::find(flooredSkills.begin(), flooredSkills.end(), weapon.skill) == flooredSkills.end())
        {
            flooredSkills.push_back(weapon.skill);
            add += std::max(weaponSkill.level - (bonus + sides * dice / 2 + armsDamage / multiplier) * (multiplier - 1),
                0.0);
        }

        const double total = armsDamage + add;

        if (weapon.bow)
        {
            rangedAttackRow += mawRound(bonus);
            rangedMinimumRow += dice + add;
            rangedMaximumRow += mawRound(side) * dice + add;
        }
        else
        {
            meleeAttackRow += mawRound(bonus);
            meleeMinimumRow += dice + mawRound(total);
            meleeMaximumRow += mawRound(side) * dice + mawRound(total);
        }
    }

    // Attack: the best melee weapon skill counts once, the bow's goes to shooting.
    double bestMeleeAttack = 0;

    for (const HeldWeapon &weapon : weapons)
    {
        const Skill weaponSkill = skillOf(character, weapon.skill);
        const double attack = row(weapon.skill == "Spear" ? SpearAttack : WeaponAttack, weaponSkill.mastery)
            * weaponSkill.level;

        if (weapon.bow)
        {
            rangedAttackRow += attack;

            // A Grandmaster bow takes back the unmultiplied skill bonus (zzMaw-Items.lua:3168-3171).
            if (weaponSkill.mastery >= 4)
            {
                rangedMinimumRow -= weaponSkill.level;
                rangedMaximumRow -= weaponSkill.level;
            }
        }
        else
        {
            bestMeleeAttack = std::max(bestMeleeAttack, attack);
        }
    }

    meleeAttackRow += bestMeleeAttack;

    if (armsmaster.mastery > 0 && pMainHand != nullptr && mainSkill != "Staff")
    {
        meleeAttackRow += armsmaster.level;
    }

    // Bare hands, or a Grandmaster staff, fight with Unarmed too.
    const bool emptyHands = pOffHand == nullptr && pMainHand == nullptr;

    const bool unarmedRows = unarmed.mastery >= 1 && (emptyHands || (mainSkill == "Staff" && staff.mastery >= 4));

    if (unarmedRows)
    {
        meleeAttackRow += row(UnarmedAttack, unarmed.mastery) * unarmed.level;
        meleeMinimumRow += 2 * unarmed.level;
        meleeMaximumRow += 2 * unarmed.level;
    }

    // Might multiplies physical damage, the engine adding its effect to melee damage before that; the Heroism aura
    // multiplies melee damage, Hammerhands unarmed damage (applyDamageMultipliers).
    const double mightEffect = mawStatEffect(stats.might);
    const double mightMultiplier = 1 + stats.might / 1000.0;
    const std::optional<double> heroism = rules.auraSkill(51, &character);
    const std::optional<double> hammerhands = unarmedRows ? rules.auraSkill(73) : std::nullopt;
    const double buffScale = rules.buffScale();
    const double meleeMultiplier = mightMultiplier * (1 + (heroism ? mawBuffMultiplier(51, *heroism, buffScale) : 0))
        * (1 + (hammerhands ? mawBuffMultiplier(73, *hammerhands, buffScale) : 0)) * mawClassMeleeMultiplier(character);
    CharacterCombatRows rows;
    rows.meleeAttack = mawStatEffect(stats.accuracy) + int(meleeAttackRow);
    rows.meleeMinimumDamage = std::max(1, int((meleeMinimumRow + mightEffect) * meleeMultiplier));
    rows.meleeMaximumDamage =
        std::max(rows.meleeMinimumDamage, int((meleeMaximumRow + mightEffect) * meleeMultiplier));
    rows.rangedAttack = mawStatEffect(stats.accuracy) + int(rangedAttackRow);
    rows.rangedMinimumDamage =
        std::max(0, int(rangedMinimumRow + (rangedMinimumRow + mightEffect) * (mightMultiplier - 1)));
    rows.rangedMaximumDamage = std::max(rows.rangedMinimumDamage,
        int(rangedMaximumRow + (rangedMaximumRow + mightEffect) * (mightMultiplier - 1)));

    // A blaster shot rolls the melee rows (DM:462-474).
    if (std::any_of(weapons.begin(), weapons.end(), [](const HeldWeapon &weapon) { return weapon.skill == "Blaster"; }))
    {
        rows.blasterDamage = std::pair(rows.meleeMinimumDamage, rows.meleeMaximumDamage);
    }

    // Armour: the pieces, the body-armour skill's percent of all of them and the Shield skill's of the shield.
    // Legendary 28: the pieces' own armour counts half again; the armour skills read it unmultiplied (IT:2708-2716).
    const MawArmorBreakdown armor = mawArmorBreakdown(rules, character, itemTable);
    double armorClass = (armor.pieces + armor.shield) * (mawWearsLegendaryAffix(character, 28) ? 1.5 : 1)
        + armor.bodySkillArmor + armor.shieldSkillArmor;
    double resistance = armor.bodySkillResistance + armor.shieldSkillResistance;
    const ItemDefinition *pBodyArmor =
        character.equipmentRuntime.armor.broken ? nullptr : equipped(character.equipment.armor);
    const std::string bodySkill = pBodyArmor != nullptr ? canonicalSkillName(pBodyArmor->skillGroup) : std::string();

    // A dragon-race character's armour pieces and armour skills count three times (zzMaw-Items.lua:3002-3014).
    if (mawIsDragon(character))
    {
        armorClass *= 3;
        resistance *= 3;
    }

    // Staff, Sword and Spear guard by the weapon's guard, counting ten more points of skill.
    for (const HeldWeapon &weapon : weapons)
    {
        if (const std::optional<MawWeaponGuard> guard =
                mawWeaponGuard(rules, character, *weapon.pDefinition, weapon.pState->rulesetFields))
        {
            armorClass += guard->armorClass;
        }
    }

    // Every staff in the party resists for everyone, its holder included (mawStaffPartyResistance).
    resistance += rules.partyStaffResistance();

    // Dodging works without body armour, and from Master in leather.
    const Skill dodging = skillOf(character, "Dodging");

    if (pBodyArmor == nullptr || (bodySkill == "LeatherArmor" && dodging.mastery >= 3))
    {
        armorClass += row(DodgingArmor, dodging.mastery) * dodging.level;
    }

    rows.armorClass = int(armorClass);
    const int allResistances = int(resistance) + mawStatEffect(stats.luck);
    rows.resistances.fire = allResistances;
    rows.resistances.air = allResistances;
    rows.resistances.water = allResistances;
    rows.resistances.earth = allResistances;
    rows.resistances.mind = allResistances;
    rows.resistances.body = allResistances;

    if (mawIsDragon(character))
    {
        applyDragonRows(rules, character, stats, rows);
    }

    return rows;
}

int mawStaffPartyResistance(const MawRules &rules, const Character &character, const ItemTable &itemTable)
{
    const ItemDefinition *pMainHand = character.equipmentRuntime.mainHand.broken || character.equipment.mainHand == 0
        ? nullptr
        : itemTable.get(character.equipment.mainHand);

    if (pMainHand == nullptr || canonicalSkillName(pMainHand->skillGroup) != "Staff")
    {
        return 0;
    }

    const std::optional<MawWeaponGuard> guard =
        mawWeaponGuard(rules, character, *pMainHand, character.equipmentRuntime.mainHand.rulesetFields);
    return guard ? guard->resistance : 0;
}

std::optional<MawWeaponGuard> mawWeaponGuard(
    const MawRules &rules,
    const Character &character,
    const ItemDefinition &weapon,
    const ItemRulesetFields &fields)
{
    const std::string skill = mawWeaponSkill(character, weapon);
    const MasteryRow *pArmorRow = skill == "Staff" ? &StaffArmor
        : skill == "Sword"                         ? &SwordArmor
        : skill == "Spear"                         ? &SpearArmor
                                                   : nullptr;
    const std::optional<int> guard =
        pArmorRow != nullptr ? rules.itemRules().weaponGuardBase(weapon, fields, int(character.level)) : std::nullopt;

    if (!guard)
    {
        return std::nullopt;
    }

    const Skill held = skillOf(character, skill);
    MawWeaponGuard result;
    result.guard = *guard;
    result.armorClass = int(mawRound(row(*pArmorRow, held.mastery) * *guard / 100 * (held.level + 10)));
    // Staff's resistance row is its Armor Class row (zzMAW-Skills.lua skillResistance).
    result.resistance = skill == "Staff" ? result.armorClass : 0;
    return result;
}

double mawAssassinationBonus(const MawRules &rules, const Character &character, const ItemTable &itemTable)
{
    if (mawClassLine(character.className) != "assassin")
    {
        return 0;
    }

    // The main hand's weapon, else the off hand's, multiplies the bonus by its skill's 2 % a point; a staff takes
    // half of Unarmed as its Armsmaster at Grandmaster.
    const ItemDefinition *pWeapon = nullptr;

    for (const auto &[itemId, pState] : {std::pair{character.equipment.mainHand, &character.equipmentRuntime.mainHand},
             std::pair{character.equipment.offHand, &character.equipmentRuntime.offHand}})
    {
        const ItemDefinition *pItem = itemId != 0 && !pState->broken ? itemTable.get(itemId) : nullptr;

        if (pWeapon == nullptr && pItem != nullptr && isMeleeWeaponSkill(canonicalSkillName(pItem->skillGroup)))
        {
            pWeapon = pItem;
        }
    }

    // Bare hands carry no Assassination bonus in the rows, so none comes off.
    if (pWeapon == nullptr)
    {
        return 0;
    }

    const std::string skill = mawWeaponSkill(character, *pWeapon);
    const double multiplier = 1 + skillOf(character, skill).level * 2.0 / 100;
    Skill arms = {skillOf(character, "Armsmaster").level, armsmasterMastery(rules, character)};

    if (skill == "Staff")
    {
        const Skill unarmed = skillOf(character, "Unarmed");
        arms = skillOf(character, "Staff").mastery >= 4 ? Skill{unarmed.level / 2, unarmed.mastery} : Skill{};
    }

    const double bonus = (ArmsmasterDamage[size_t(std::clamp(arms.mastery, 0, 5))] * arms.level
                             + mawClassMeleeFlatDamage(rules, character))
        * multiplier;
    const std::optional<double> heroism = rules.auraSkill(51, &character);
    return bonus * (1 + (heroism ? mawBuffMultiplier(51, *heroism, rules.buffScale()) : 0));
}

MawArmorBreakdown mawArmorBreakdown(const MawRules &rules, const Character &character, const ItemTable &itemTable)
{
    const MawItemRules &itemRules = rules.itemRules();
    const int wearerLevel = int(character.level);
    const auto equipped = [&itemTable](uint32_t itemId) -> const ItemDefinition *
    {
        return itemId != 0 ? itemTable.get(itemId) : nullptr;
    };
    // Rings and amulets with printed AC count as MAW's collectArmorAC counts them (ITM-A3).
    const std::array<std::pair<uint32_t, const EquippedItemRuntimeState *>, 14> armorSlots = {{
        {character.equipment.offHand, &character.equipmentRuntime.offHand},
        {character.equipment.armor, &character.equipmentRuntime.armor},
        {character.equipment.helm, &character.equipmentRuntime.helm},
        {character.equipment.belt, &character.equipmentRuntime.belt},
        {character.equipment.cloak, &character.equipmentRuntime.cloak},
        {character.equipment.gauntlets, &character.equipmentRuntime.gauntlets},
        {character.equipment.boots, &character.equipmentRuntime.boots},
        {character.equipment.amulet, &character.equipmentRuntime.amulet},
        {character.equipment.ring1, &character.equipmentRuntime.ring1},
        {character.equipment.ring2, &character.equipmentRuntime.ring2},
        {character.equipment.ring3, &character.equipmentRuntime.ring3},
        {character.equipment.ring4, &character.equipmentRuntime.ring4},
        {character.equipment.ring5, &character.equipmentRuntime.ring5},
        {character.equipment.ring6, &character.equipmentRuntime.ring6},
    }};
    MawArmorBreakdown armor;
    // Austerity: the body armour and the shield give at least round(skill x mastery) x 2 Armor Class and resistance
    // (IT:2980-2996).
    const bool austerity = rules.options().challengeMode == RulesetChallengeMode::Austerity;
    const auto austerityFloor = [](const Skill &skill)
    {
        return int(mawRound(skill.level * skill.mastery)) * 2;
    };

    for (const auto &[itemId, pState] : armorSlots)
    {
        const ItemDefinition *pItem = pState->broken ? nullptr : equipped(itemId);

        if (pItem == nullptr)
        {
            continue;
        }

        const std::optional<int> armorClass = itemRules.armorClass(*pItem, pState->rulesetFields, wearerLevel);

        if (!armorClass)
        {
            continue;
        }

        (canonicalSkillName(pItem->skillGroup) == "Shield" ? armor.shield : armor.pieces) += *armorClass;
    }

    const ItemDefinition *pBodyArmor =
        character.equipmentRuntime.armor.broken ? nullptr : equipped(character.equipment.armor);
    const std::string bodySkill = pBodyArmor != nullptr ? canonicalSkillName(pBodyArmor->skillGroup) : std::string();

    if (bodySkill == "LeatherArmor" || bodySkill == "ChainArmor" || bodySkill == "PlateArmor")
    {
        const Skill body = skillOf(character, bodySkill);
        const MasteryRow &resistancePercent = bodySkill == "LeatherArmor" ? LeatherResistancePercent
            : bodySkill == "ChainArmor"                                    ? ChainResistancePercent
                                                                           : PlateResistancePercent;
        armor.bodySkill = bodySkill;
        armor.bodySkillArmor = int(mawRound(armor.pieces * row(BodyArmorPercent, body.mastery) * body.level / 100));
        armor.bodySkillResistance =
            int(mawRound(armor.pieces * row(resistancePercent, body.mastery) * body.level / 100));

        if (austerity && armor.pieces >= 1)
        {
            armor.bodySkillArmor = std::max(armor.bodySkillArmor, austerityFloor(body));
            armor.bodySkillResistance = std::max(armor.bodySkillResistance, austerityFloor(body));
        }
    }

    if (armor.shield > 0)
    {
        const Skill shield = skillOf(character, "Shield");
        armor.shieldSkillArmor =
            int(mawRound(armor.shield * row(ShieldArmorPercent, shield.mastery) * shield.level / 100));
        armor.shieldSkillResistance =
            int(mawRound(armor.shield * row(ShieldResistancePercent, shield.mastery) * shield.level / 100));

        if (austerity && armor.shield >= 1)
        {
            armor.shieldSkillArmor = std::max(armor.shieldSkillArmor, austerityFloor(shield));
            armor.shieldSkillResistance = std::max(armor.shieldSkillResistance, austerityFloor(shield));
        }
    }

    return armor;
}
}
