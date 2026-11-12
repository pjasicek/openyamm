#include "game/rules/maw/MawCombatRules.h"
#include "engine/Localization.h"

#include "game/StringUtils.h"
#include "game/gameplay/GameplayMonsterSpawn.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/PartyHostileAlert.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"
#include "game/party/SpellIds.h"
#include "game/party/SpellSchool.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawClassSpells.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawMonsterInspect.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSkillFormulas.h"
#include "game/rules/maw/MawSpellFormulas.h"
#include "game/tables/ItemTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <bitset>
#include <cmath>
#include <optional>
#include <random>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t FirstPlayerStyleMonsterSpell = 100;
// Recovery ticks to real seconds, as the engine converts attack recovery.
constexpr float MawRealtimeRecoveryScale = 2.133333333333333f;

int skillLevel(const Character &character, const std::string &skillName)
{
    const CharacterSkill *pSkill = character.findSkill(skillName);
    return (pSkill != nullptr ? int(pSkill->level) : 0) + character.skillBonus(skillName);
}

// The trained level alone, without item, follower or race bonuses: what MAW's class perks read (`pl.Skills`, CLS-2).
int trainedSkillLevel(const Character &character, const std::string &skillName)
{
    const CharacterSkill *pSkill = character.findSkill(skillName);
    return pSkill != nullptr ? int(pSkill->level) : 0;
}

SkillMastery skillMastery(const Character &character, const std::string &skillName)
{
    const CharacterSkill *pSkill = character.findSkill(skillName);
    return pSkill != nullptr ? pSkill->mastery : SkillMastery::None;
}

CharacterSheetSummary characterSheet(
    const Character &character,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    return GameMechanics::buildCharacterSheetSummary(
        character, pItemTable, pStandardItemEnchantTable, pSpecialItemEnchantTable);
}

bool holdsShieldAtGrandmaster(const Character &character, const ItemTable *pItemTable)
{
    const ItemDefinition *pOffHand =
        pItemTable != nullptr && character.equipment.offHand != 0 ? pItemTable->get(character.equipment.offHand)
                                                                  : nullptr;
    return pOffHand != nullptr && pOffHand->skillGroup == "Shield"
        && skillMastery(character, "Shield") >= SkillMastery::Grandmaster;
}

int monsterResistanceFor(const MonsterDamageResistances &resistances, CombatDamageType type)
{
    switch (type)
    {
        case CombatDamageType::Physical:
            return resistances.physical;
        case CombatDamageType::Fire:
            return resistances.fire;
        case CombatDamageType::Air:
            return resistances.air;
        case CombatDamageType::Water:
            return resistances.water;
        case CombatDamageType::Earth:
            return resistances.earth;
        case CombatDamageType::Spirit:
            return resistances.spirit;
        case CombatDamageType::Mind:
            return resistances.mind;
        case CombatDamageType::Body:
            return resistances.body;
        case CombatDamageType::Light:
            return resistances.light;
        case CombatDamageType::Dark:
            return resistances.dark;
        case CombatDamageType::Energy:
        case CombatDamageType::Irresistible:
            break;
    }

    return 0;
}

double resisted(double damage, int resistance, int affixBonus)
{
    return damage / mawMonsterResistanceDivisor(mawCappedMonsterResistance(resistance, affixBonus));
}

// Mass Distortion's scale (stage_massDistortion, DM:362-391): MAW divides by the root of a multiplier by its bolster
// amount (1 up to MAW, 1.4 Hard, 1.8 Hell, 3 Nightmare; for Doom and the madness modes 3.33 (1 + level / 75), twice
// (1 + level / 80) more on bosses; four times in Austerity) and grows with the target's level past 250.
double massDistortionScale(const RulesetOptions &options, const ActorRulesetFacts *pFacts)
{
    const int level = pFacts != nullptr ? pFacts->level : 0;
    // The game's stored monster level stops at 255.
    const double storedLevel = std::min(level, 255);
    double divisor = 1;
    const int bolster = mawBolsterAmount(options);

    if (bolster >= 600)
    {
        divisor = 3.33 * (1 + level / 75.0);

        if (pFacts != nullptr && pFacts->bossAffix != 0)
        {
            divisor *= 2 * (1 + storedLevel / 80);
        }
    }
    else
    {
        divisor = bolster >= 300 ? 3 : bolster >= 200 ? 1.8 : bolster >= 150 ? 1.4 : 1;
    }

    if (options.challengeMode == RulesetChallengeMode::Austerity)
    {
        divisor *= 4;
    }

    return std::max(1.0, std::pow(storedLevel / 250, 2)) / std::sqrt(divisor);
}

// Monster hits are MAW's when the ruleset sized the attacker; the others (traps, unresolved monsters) are trap hits.
// Every spawn is sized, so an unsized attacker is one the rules could not size: MAW has none, and its model damage at
// the party's level is a better fallback than Standard's stage.
bool mawMonsterHit(const CharacterDamageHit &hit)
{
    return hit.monsterAttack && hit.attackerFacts.level > 0;
}

bool hasAffix(const ActorRulesetFacts &facts, MawBossAffix affix)
{
    return mawHasBossAffix(facts, affix);
}

// A Skilled boss turns 40 % of the party's weapon hits that landed into misses (PlayerHitOrMiss,
// zzMaw-Monsters.lua:3136-3140); no draw for other monsters.
bool skilledTargetDodges(const ActorRulesetFacts &target, std::mt19937 &rng)
{
    return hasAffix(target, MawBossAffix::Skilled) && std::uniform_real_distribution<double>(0.0, 1.0)(rng) < 0.4;
}

// Whether the struck monster is hostile to the party; one the world cannot name counts as hostile.
bool targetHostile(const PartyHitOnMonster &hit)
{
    GameplayRuntimeActorState target = {};
    return hit.pWorld == nullptr || !hit.targetActorIndex
        || !hit.pWorld->actorRuntimeState(*hit.targetActorIndex, target) || target.hostileToParty;
}

bool conscious(const Character &member)
{
    return member.health > 0 && !member.conditions.test(size_t(CharacterCondition::Unconscious))
        && !member.conditions.test(size_t(CharacterCondition::Dead))
        && !member.conditions.test(size_t(CharacterCondition::Petrified))
        && !member.conditions.test(size_t(CharacterCondition::Eradicated));
}

// The party member side of calcMawDamage for this character, without the hit.
constexpr uint16_t ShieldingSpecial = 36;
// The legendary affixes combat reads (legendary_affixes.yml); EnchantDamageLegendary (19) is below.
constexpr int LegendaryKillRecovery = 11;
constexpr int LegendaryStatusImmunity = 13;
constexpr int LegendaryOvercrit = 14;
constexpr int LegendaryProtection = 15;
constexpr int LegendaryHealthDamage = 17;
constexpr int LegendaryToughness = 18;
constexpr int LegendaryCrowdDamage = 21;
constexpr int LegendaryCrowdDefense = 22;
constexpr int LegendaryCoverHeal = 23;
constexpr int LegendaryKillRestore = 24;
constexpr int LegendaryEnchantCrits = 26;
constexpr int LegendaryOverheal = 27;
constexpr int LegendaryDamageTaken = 29;
constexpr int LegendaryManaThreshold = 30;
constexpr int LegendaryManaLeech = 31;
constexpr int SparksSpell = 15;

// MAW's area spells (aoespells, SP:2094).
bool isAreaSpell(uint32_t spellId)
{
    static constexpr std::array<uint32_t, 17> AreaSpells = {
        6, 7, 8, 9, 10, 15, 22, 24, 32, 41, 43, 84, 93, 97, 98, 99, 123,
    };
    return std::find(AreaSpells.begin(), AreaSpells.end(), spellId) != AreaSpells.end();
}

double unitDraw(std::mt19937 &rng)
{
    return std::uniform_real_distribution<double>(0.0, 1.0)(rng);
}

// What a Grandmaster spear blow adds to its target's spear stack, in percent of physical damage taken: (2 + 0.02 s)
// x the blow's speed multiplier, x 1.5 with a two-handed spear (DM:546-570); 0 for any other blow.
double spearStack(const MawRules &rules, const Character &attacker, const ItemTable &itemTable);

// The swiftness specials: "of Darkness" (41) and "Swift" (59).
bool isSwift(const EquippedItemRuntimeState &state)
{
    return !state.broken && (state.specialEnchantId == 41 || state.specialEnchantId == 59);
}

MawMitigationInputs characterMitigation(
    const MawRules &rules,
    const Character &character,
    const CharacterSheetSummary &sheet,
    const ItemTable *pItemTable,
    int partyCount)
{
    // An immunity reads as MAW's 65000 resistance.
    const auto resistance = [](const CharacterSheetValue &value)
    {
        return value.infinite ? 65000 : value.actual;
    };
    MawMitigationInputs inputs;
    inputs.armorClass = std::max(0, sheet.armorClass.actual + character.armorClassModifier);
    inputs.resistances = {
        resistance(sheet.fireResistance),
        resistance(sheet.airResistance),
        resistance(sheet.waterResistance),
        resistance(sheet.earthResistance),
        resistance(sheet.mindResistance),
        resistance(sheet.bodyResistance),
    };
    const CharacterResistanceSet &items = character.itemResistanceEnchants;
    inputs.itemResistances = {items.fire, items.air, items.water, items.earth, items.mind, items.body};
    // "of Shielding": x0.85 physical damage taken (IT:3405-3418).
    inputs.shieldingEnchantment = mawWornSpecialCount(character, {ShieldingSpecial}) > 0;
    inputs.grandmasterShield = holdsShieldAtGrandmaster(character, pItemTable);
    inputs.shieldBuffSkill = rules.auraSkill(17, &character);
    inputs.buffScale = rules.buffScale();
    const MawClassDefense defense = mawClassDefense(rules, character, partyCount);
    inputs.physicalCutSkill = defense.physicalCutSkill;
    inputs.magicCutSkill = defense.magicCutSkill;
    inputs.flatReduction = defense.flatReduction;
    return inputs;
}

// A dimension map's player crit affixes (zzMaw-Stats.lua:125-130).
void addMapCritAffixes(const MawRules &rules, MawCritInputs &inputs)
{
    inputs.chancePenalty = rules.mapAffix(MawMapAffix::PlayerCriticalChance).value_or(0) / 100;
    inputs.multiplierReduction = rules.mapAffix(MawMapAffix::PlayerCriticalDamage).value_or(0) / 100;
}

// The crit factor one roll gives: the crit multiplier when `draw` is below the chance. Legendary 14's chance above
// 100 % multiplies the whole hit late in the damage pipeline instead (legendary-blows, ITM-L2).
double critFactor(const MawCrit &crit, const MawCritInputs &, double draw)
{
    return draw < crit.chance ? crit.multiplier : 1;
}

// A melee blow's crit inputs against a monster of `referenceLevel`: Luck, Accuracy, Fate, the map's affixes and the
// Master Dagger and Grandmaster Axe hands (getCritInfo, IT:4252-4300).
MawCritInputs meleeCritInputs(
    const MawRules &rules,
    const Character &character,
    const CharacterSheetSummary &sheet,
    const ItemTable &itemTable,
    int referenceLevel)
{
    MawCritInputs critInputs;
    critInputs.luck = sheet.luck.actual;
    critInputs.accuracy = sheet.accuracy.actual;
    critInputs.referenceLevel = referenceLevel;
    critInputs.fateSkill = rules.auraSkill(47);
    critInputs.buffScale = rules.buffScale();
    critInputs.madness = rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
    addMapCritAffixes(rules, critInputs);
    const std::array<uint32_t, 2> handItemIds = {character.equipment.offHand, character.equipment.mainHand};

    for (size_t handIndex = 0; handIndex < handItemIds.size(); ++handIndex)
    {
        const ItemDefinition *pItem = handItemIds[handIndex] != 0 ? itemTable.get(handItemIds[handIndex]) : nullptr;
        const std::string skill = pItem != nullptr ? mawWeaponSkill(character, *pItem) : std::string();

        if (skill == "Dagger" && skillMastery(character, skill) >= SkillMastery::Master)
        {
            critInputs.masterDaggerSkills[handIndex] = skillLevel(character, skill);
        }

        if (skill == "Axe" && critInputs.grandmasterAxeSkill == 0
            && skillMastery(character, skill) >= SkillMastery::Grandmaster)
        {
            critInputs.grandmasterAxeSkill = skillLevel(character, skill);
        }
    }

    return critInputs;
}

// A dragon-race character's breath or Flame Blast (`share` of the breath) from its ranged rows: the mean of two rolls,
// a crit against the reference level (Legendary 14's +10 % chance counted), then x (0.75 + 0.25 U + 0.25 U); the
// lowest of the monster's resistances applies where it lands (DM:629-668, CMB-11).
double dragonBreathDamage(
    const MawRules &rules,
    const Character &dragon,
    const CharacterSheetSummary &sheet,
    int minimum,
    int maximum,
    int referenceLevel,
    double share,
    std::mt19937 &rng,
    bool &critical)
{
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    std::uniform_int_distribution<int> roll(minimum, std::max(minimum, maximum));
    const int first = roll(rng);
    double damage = mawAverageOfTwoRolls(first, roll(rng)) * share;
    MawCritInputs critInputs;
    critInputs.overcrit = mawWearsLegendaryAffix(dragon, LegendaryOvercrit);
    critInputs.luck = sheet.luck.actual;
    critInputs.accuracy = sheet.accuracy.actual;
    critInputs.referenceLevel = std::max(1, referenceLevel);
    critInputs.fateSkill = rules.auraSkill(47);
    critInputs.buffScale = rules.buffScale();
    critInputs.madness = rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
    addMapCritAffixes(rules, critInputs);
    const MawCrit crit = mawCrit(critInputs);
    const double draw = unit(rng);
    damage *= critFactor(crit, critInputs, draw);
    critical = draw < crit.chance;
    return damage * (0.75 + 0.25 * unit(rng) + 0.25 * unit(rng));
}

// calcPowerVitality (COMBAT_SPEC.md §7.3) against the party's banked level: melee damage per second, and maximum HP
// (with Mana Shield's mana and Grandmaster Dodging) over the share of an average hit that gets through. The weapons'
// enchantment and aura damage is left out of the power.
std::pair<double, double> powerAndVitality(
    MawRules &rules,
    const Character &character,
    const CharacterAttackOnMonster &context,
    const CharacterSheetSummary *pSheet = nullptr)
{
    // The caller's sheet when it has one; a sheet is the costly part.
    std::optional<CharacterSheetSummary> ownSheet;

    if (pSheet == nullptr)
    {
        ownSheet = characterSheet(
            character, context.pItemTable, context.pStandardItemEnchantTable, context.pSpecialItemEnchantTable);
        pSheet = &*ownSheet;
    }

    const CharacterSheetSummary &sheet = *pSheet;
    const int reference = std::max(1, int(mawRound(rules.state().totalLevel())));
    MawBalanceModel &model = rules.model(context.partyCount);
    const CharacterStatValues stats = {sheet.might.actual, sheet.accuracy.actual, sheet.luck.actual};
    const CharacterCombatRows rows = mawCombatRows(rules, character, *context.pItemTable, stats);
    const MawAttackDelay delay = mawCharacterAttackDelay(rules, character, *context.pItemTable,
        CharacterAttackMode::Melee, sheet.speed.actual, rules.auraSkill(5, &character));

    MawCritInputs critInputs;
    critInputs.luck = sheet.luck.actual;
    critInputs.accuracy = sheet.accuracy.actual;
    critInputs.referenceLevel = reference;
    critInputs.fateSkill = rules.auraSkill(47);
    critInputs.buffScale = rules.buffScale();
    critInputs.madness = rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
    addMapCritAffixes(rules, critInputs);
    const MawCrit crit = mawCrit(critInputs);
    const double average = (rows.meleeMinimumDamage + rows.meleeMaximumDamage) / 2.0
        * (1 + std::min(crit.chance, 1.0) * (crit.multiplier - 1));
    const double power = mawRound(average / (std::max(1, delay.delay) / 60.0)
        * mawPartyHitChance(rows.meleeAttack, reference, rules.blessHitSkill(character), model)
        * delay.damageMultiplier * std::max(crit.chance, 1.0));

    double fullHealth = character.maxHealth;

    if (character.hasSkill("ManaShield") && !character.rulesetState.manaShieldDisabled)
    {
        fullHealth += character.maxSpellPoints
            * mawRound(mawManaShieldEfficiency(skillLevel(character, "ManaShield")) * 100) / 100;
    }

    // A dragon's Dodging is Scales and never dodges (zzMaw-Stats.lua:1321-1323).
    if (!mawIsDragon(character) && skillMastery(character, "Dodging") >= SkillMastery::Grandmaster)
    {
        fullHealth *= 1 + (skillLevel(character, "Dodging") + 10) / 200.0;
    }

    MawMitigationInputs inputs = characterMitigation(rules, character, sheet, context.pItemTable, context.partyCount);
    // The shares are ratios: the flat class cut stays out (ratioOnly).
    inputs.flatReduction = 0;
    inputs.damage = 10000;
    inputs.attackerLevel = reference;
    const auto share = [&inputs](CombatDamageType type)
    {
        inputs.type = type;
        return mawMitigatedDamage(inputs) / 10000;
    };
    double reduction = share(CombatDamageType::Physical) * 0.5 + share(CombatDamageType::Energy) * 0.125;

    for (const CombatDamageType type : {CombatDamageType::Fire, CombatDamageType::Air, CombatDamageType::Water,
             CombatDamageType::Earth, CombatDamageType::Mind, CombatDamageType::Body})
    {
        reduction += share(type) * 0.0625;
    }

    reduction *= mawChanceToBeHit(sheet.speed.actual, reference, model);
    return {power, mawRound(fullHealth / std::max(reduction, 0.0001))};
}

// Per-mastery tables (None, Novice, Expert, Master, Grandmaster) from zzMAW-Skills.lua; MAW reads index 0 as Novice
// where the table has no entry for it.
using MasteryRow = std::array<double, 5>;

struct WeaponSkillNumbers
{
    const char *pSkill;
    int baseRecovery;
    MasteryRow recoveryPerPoint;
};

constexpr std::array<WeaponSkillNumbers, 8> WeaponSkills = {{
    {"Bow", 100, {0, 0, 1, 1, 2}},
    {"Blaster", 40, {0, 0, 0, 0, 0}},
    {"Staff", 120, {0, 0, 0, 0, 0}},
    {"Axe", 140, {0, 0, 1, 1, 1}},
    {"Sword", 80, {0, 0, 1, 1, 2}},
    {"Spear", 120, {0, 0, 0, 0, 0}},
    {"Mace", 100, {0, 0, 0, 0, 0}},
    {"Dagger", 60, {0, 0, 0, 0, 1}},
}};
constexpr MasteryRow UnarmedRecoveryPerPoint = {0, 0, 1, 1, 2};
constexpr MasteryRow ArmsmasterSpeedPerPoint = {0, 0, 0, 1, 1};
constexpr int UnknownWeaponRecovery = 100;

const WeaponSkillNumbers *weaponSkillNumbers(const std::string &skill)
{
    for (const WeaponSkillNumbers &numbers : WeaponSkills)
    {
        if (skill == numbers.pSkill)
        {
            return &numbers;
        }
    }

    return nullptr;
}

// weaponImpair: the delay a worn armour or shield adds, in percent.
double armorImpairment(const std::string &skill, SkillMastery mastery)
{
    static constexpr std::array<std::pair<const char *, MasteryRow>, 4> Impairments = {{
        {"LeatherArmor", {10, 10, 0, 0, 0}},
        {"ChainArmor", {20, 20, 10, 0, 0}},
        {"PlateArmor", {20, 20, 10, 10, 0}},
        {"Shield", {10, 10, 0, 0, 0}},
    }};

    for (const auto &[name, row] : Impairments)
    {
        if (skill == name)
        {
            return row[size_t(mastery)];
        }
    }

    return 0;
}

double perPoint(const MasteryRow &row, const Character &character, const std::string &skill)
{
    return row[size_t(skillMastery(character, skill))] * skillLevel(character, skill);
}

// A weapon's level in combat (ItemLevel.OfItem): item power x 5, an artifact the party's total level, a Celestial item
// the level of a Primordial one at its wearer's level (ItemLevel.lua:61-66, IT:1660).
int itemLevel(const MawRules &rules, const ItemDefinition &item, const EquippedItemRuntimeState &state,
    const Character &wearer)
{
    if (rules.itemData().artifact(item.itemId) != nullptr)
    {
        return int(mawRound(rules.state().totalLevel()));
    }

    if (MawRarity(state.rulesetFields.lootRarity) == MawRarity::Celestial)
    {
        return 5 * mawItemPower(int(rules.itemRules().celestialLevel(int(wearer.level))), MawRarity::Celestial, 24);
    }

    return state.rulesetFields.itemPower * 5;
}

bool isWeapon(const ItemDefinition &item)
{
    return item.equipStat == "Weapon" || item.equipStat == "Weapon2" || item.equipStat == "Weapon1or2"
        || item.equipStat == "WeaponW";
}

bool isTwoHanded(const ItemDefinition &item)
{
    return item.equipStat == "Weapon2";
}

constexpr int EnchantDamageLegendary = 19;

// One weapon slot as the enchantment and aura damage read it.
struct HeldWeapon
{
    const ItemDefinition *pItem = nullptr;
    const EquippedItemRuntimeState *pState = nullptr;
    bool missile = false;
    const Character *pWearer = nullptr;
};

// The weapon's level damage (GetWeaponLevelDamage): its level, item power x 5 or for an artifact the party's total
// level, through the balance model.
double weaponLevelDamage(const MawRules &rules, const HeldWeapon &weapon, int partyCount)
{
    const double level = rules.itemData().artifact(weapon.pItem->itemId) != nullptr
        ? rules.state().totalLevel()
        : itemLevel(rules, *weapon.pItem, *weapon.pState, *weapon.pWearer);
    return rules.model(partyCount).weaponLevelDamage(level, isTwoHanded(*weapon.pItem), 0);
}

// A weapon's own pace (getItemRecovery) from the base recovery of the skill it is wielded with and its level.
int weaponRecovery(const MawRules &rules, const HeldWeapon &weapon)
{
    const WeaponSkillNumbers *pNumbers = weaponSkillNumbers(mawWeaponSkill(*weapon.pWearer, *weapon.pItem));
    return mawItemRecovery(pNumbers != nullptr ? pNumbers->baseRecovery : UnknownWeaponRecovery,
        itemLevel(rules, *weapon.pItem, *weapon.pState, *weapon.pWearer), isTwoHanded(*weapon.pItem));
}

// The weapons in the character's hands and bow slot that count for enchantment damage.
std::vector<HeldWeapon> heldWeapons(const Character &character, const ItemTable &itemTable, bool hands, bool bow)
{
    std::vector<HeldWeapon> weapons;
    const auto add = [&](uint32_t itemId, const EquippedItemRuntimeState &state, bool missile)
    {
        const ItemDefinition *pItem = itemId != 0 ? itemTable.get(itemId) : nullptr;

        if (pItem != nullptr && !state.broken && (missile ? pItem->equipStat == "Missile" : isWeapon(*pItem)))
        {
            weapons.push_back({pItem, &state, missile, &character});
        }
    };

    if (hands)
    {
        add(character.equipment.mainHand, character.equipmentRuntime.mainHand, false);
        add(character.equipment.offHand, character.equipmentRuntime.offHand, false);
    }

    if (bow)
    {
        add(character.equipment.bow, character.equipmentRuntime.bow, true);
    }

    return weapons;
}

// The hands' base pace for enchantment damage (GetPlayerBaseRecovery): a bow's own, else the mean of the melee
// weapons held, 100 bare-handed.
double enchantPace(
    const MawRules &rules, const Character &character, const ItemTable &itemTable, const HeldWeapon &weapon)
{
    if (weapon.missile)
    {
        return weaponRecovery(rules, weapon);
    }

    const std::vector<HeldWeapon> hands = heldWeapons(character, itemTable, true, false);
    double total = 0;

    for (const HeldWeapon &hand : hands)
    {
        total += weaponRecovery(rules, hand);
    }

    return hands.empty() ? 100 : total / double(hands.size());
}

// A weapon's damage enchantment on one hit before resistance (calcEnchantDamage, IT:2125-2155): a roll in its range
// (the average without a generator), x 1.5 with Legendary 19, at the hands' base pace.
std::optional<std::pair<CombatDamageType, double>> weaponEnchantDamage(
    MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    const HeldWeapon &weapon,
    bool spell,
    int partyCount,
    std::mt19937 *pRng)
{
    const MawDamageEnchant *pEnchant = mawDamageEnchant(weapon.pState->specialEnchantId);

    if (pEnchant == nullptr || (pEnchant->spellOnly && !spell) || (pEnchant->weaponOnly && spell))
    {
        return std::nullopt;
    }

    const MawEnchantRange range = mawEnchantDamageRange(weaponLevelDamage(rules, weapon, partyCount),
        pEnchant->minimum, pEnchant->maximum, pEnchant->coefficient, isTwoHanded(*weapon.pItem));
    double damage = (range.minimum + range.maximum) / 2;

    if (pRng != nullptr)
    {
        const int low = int(mawRound(range.minimum));
        damage = std::uniform_int_distribution<int>(low, std::max(low, int(mawRound(range.maximum))))(*pRng);
    }

    damage *= mawWearsLegendaryAffix(character, EnchantDamageLegendary) ? 1.5 : 1;
    return std::pair(pEnchant->type, damage * enchantPace(rules, character, itemTable, weapon) / 100);
}

// Fire Aura's fire on a weapon (calcFireAuraDamage), x 1.5 with Legendary 19, at the weapon's own pace for blows and
// arrows (not for spells); nothing without the aura.
double weaponFireAuraDamage(const MawRules &rules, const Character &character, const HeldWeapon &weapon, bool paced,
    int partyCount)
{
    const std::optional<MawAuraSource> aura = rules.memberAura(4, character);

    if (!aura)
    {
        return 0;
    }

    double damage = mawFireAuraDamage(aura->mastery, weaponLevelDamage(rules, weapon, partyCount),
                        isTwoHanded(*weapon.pItem))
        * (mawWearsLegendaryAffix(character, EnchantDamageLegendary) ? 1.5 : 1);

    if (paced)
    {
        damage *= weaponRecovery(rules, weapon) / 100.0;
    }

    return mawRound(damage);
}

// Mace and Staff paralyse from Master in place of the engine's stuns (turned off in RemoveSkillValueLimits.lua): a
// chance of skill / the expected skill at the target's level x the weapon's speed multiplier / min(1 + L / 150, 3),
// 15 % for a mace and 10 % for a staff, for 4 seconds at Grandmaster and 2 at Master, through Paralyze's diminishing
// returns (Damage.lua:266-305).
void applyWeaponStun(
    MawRules &rules,
    CharacterAttackResult &attack,
    const CharacterAttackOnMonster &context,
    double speedMultiplier,
    int targetLevel)
{
    constexpr int ParalyzeGroup = 3;
    const Character &character = *context.pCharacter;
    const double chance =
        mawWeaponStunChance(rules, character, *context.pItemTable, targetLevel, context.partyCount, speedMultiplier);

    if (chance <= 0 || std::uniform_real_distribution<double>(0.0, 1.0)(*context.pRng) >= chance
        || mawIgnoresCrowdControl(*context.pTargetFacts))
    {
        return;
    }

    const ItemDefinition *pItem = context.pItemTable->get(character.equipment.mainHand);
    const SkillMastery mastery = skillMastery(character, canonicalSkillName(pItem->skillGroup));

    const double seconds = rules.diminishedCrowdControlSeconds(context.targetKey, ParalyzeGroup,
        context.nowSeconds, mastery >= SkillMastery::Grandmaster ? 4.0 : 2.0, context.pTargetFacts->bossAffix != 0);

    if (seconds > 0)
    {
        attack.paralyzeTarget = true;
        attack.paralyzeSeconds = std::max(attack.paralyzeSeconds.value_or(0.0f), float(seconds));
    }
}

void addElement(ElementalDamageBonuses &bonuses, CombatDamageType type, int amount)
{
    switch (type)
    {
        case CombatDamageType::Fire:
            bonuses.fire += amount;
            break;
        case CombatDamageType::Air:
            bonuses.air += amount;
            break;
        case CombatDamageType::Water:
            bonuses.water += amount;
            break;
        case CombatDamageType::Body:
            bonuses.body += amount;
            break;
        case CombatDamageType::Light:
            bonuses.light += amount;
            break;
        case CombatDamageType::Dark:
            bonuses.dark += amount;
            break;
        default:
            break;
    }
}

CombatDamageType artifactHitType(const std::string &name)
{
    static const std::array<std::pair<const char *, CombatDamageType>, 9> Types = {{
        {"Fire", CombatDamageType::Fire}, {"Air", CombatDamageType::Air}, {"Water", CombatDamageType::Water},
        {"Earth", CombatDamageType::Earth}, {"Body", CombatDamageType::Body}, {"Mind", CombatDamageType::Mind},
        {"Spirit", CombatDamageType::Spirit}, {"Light", CombatDamageType::Light}, {"Dark", CombatDamageType::Dark},
    }};

    for (const auto &[pName, type] : Types)
    {
        if (name == pName)
        {
            return type;
        }
    }

    return CombatDamageType::Physical;
}

// An artifact's on-hit damage range (artifactOnHit): the reference enchantment's range at the artifact's level
// (Fire Aura's 46), times its share, at the hands' base pace (a bow's own), times its multiplier against the target's
// kind (zzzMaw_Artifacts.lua:430-470, CMB-18).
std::optional<MawEnchantRange> artifactHitRange(const MawRules &rules, const Character &character,
    const ItemTable &itemTable, const HeldWeapon &weapon, uint32_t targetKindFlags, int partyCount)
{
    const MawArtifact *pArtifact = rules.itemData().artifact(weapon.pItem->itemId);
    const MawDamageEnchant *pReference = mawDamageEnchant(46);

    if (pArtifact == nullptr || pArtifact->onHitDamage <= 0 || pReference == nullptr)
    {
        return std::nullopt;
    }

    static const std::array<std::pair<const char *, MonsterKind>, 6> Kinds = {{
        {"Undead", MonsterKind::Undead}, {"Dragon", MonsterKind::Dragon}, {"Ogre", MonsterKind::Ogre},
        {"Elemental", MonsterKind::Elemental}, {"Demon", MonsterKind::Demon}, {"Elf", MonsterKind::Elf},
    }};
    double versus = 1;

    for (const auto &[kindName, multiplier] : pArtifact->onHitVersus)
    {
        for (const auto &[pName, kind] : Kinds)
        {
            if (kindName == pName && (targetKindFlags & monsterKindFlag(kind)) != 0)
            {
                versus = std::max(versus, multiplier);
            }
        }
    }

    MawEnchantRange range = mawEnchantDamageRange(weaponLevelDamage(rules, weapon, partyCount), pReference->minimum,
        pReference->maximum, pReference->coefficient, isTwoHanded(*weapon.pItem));
    const double scale = pArtifact->onHitDamage * enchantPace(rules, character, itemTable, weapon) / 100.0 * versus;
    range.minimum *= scale;
    range.maximum *= scale;
    return range;
}

// The spells MAW rolls itself (spellPowers in zzMaw-Spells.lua, dice in the ruleset's spells.txt). Mass Distortion
// takes a share of the target's HP instead and keeps the engine's handling.
constexpr std::array<uint32_t, 36> MawDamageSpells = {
    2, 6, 7, 8, 9, 10, 11, 15, 18, 20, 22, 24, 26, 29, 32, 37, 39, 41,
    43, 52, 59, 65, 70, 76, 78, 79, 84, 87, 90, 93, 97, 98, 99, 103, 111, 123,
};

size_t masteryIndex(SkillMastery mastery)
{
    return mastery >= SkillMastery::Normal ? size_t(mastery) - 1 : 0;
}
}

int mawCappedMonsterResistance(int resistance, int affixBonus)
{
    return std::min(std::min(std::max(0, resistance) % 1000, 200) + affixBonus, 999);
}

int mawMonsterResistanceBonus(const MawRules &rules, const ActorRulesetFacts &facts)
{
    if (facts.bossAffix != 0 || facts.unique || facts.risen)
    {
        return 0;
    }

    return std::max(0, int(rules.mapAffix(MawMapAffix::MonsterResistance).value_or(0)));
}

MawCombatRules::MawCombatRules(MawRules &rules)
    : CombatRules(NoStages{})
    , m_rules(rules)
{
    m_damageToMonster.add(
        "monster-vs-monster",
        [](MonsterDamageHit &hit)
        {
            // A monster hits another for a third of what it deals the party; MAW also divides by the target's physical
            // resistance before the hit's own resistance, which we leave out (COMBAT_SPEC §13).
            if (hit.attackerFacts.level > 0 && hit.amount > 0)
            {
                hit.amount = std::max(1, int(mawRound(hit.attackerFacts.attack1Damage / 3)));
            }
        });
    m_damageToMonster.add(
        "resistance",
        [this](MonsterDamageHit &hit)
        {
            if (hit.amount <= 0)
            {
                return;
            }

            // Dimension affix 12 raises the resistances of unnamed monsters (zzMaw-Monsters.lua:600-605).
            const int bonus = mawMonsterResistanceBonus(m_rules, hit.targetFacts);

            // An Assassin's Mass Distortion, a weapon blow, takes Earth's resistance twice; stage_assassinAttack
            // replaces the result after Mass Distortion's scale, so the scale does not apply (DM:822-866, CMB-4).
            constexpr uint32_t MassDistortion = 44;

            if (hit.pMissileAttacker != nullptr && hit.missileSpellId == MassDistortion
                && mawClassSpell(hit.pMissileAttacker->className, MassDistortion) != nullptr)
            {
                const double once = resisted(hit.amount, hit.resistance, bonus);
                hit.amount = int(std::ceil(resisted(once, hit.resistances.earth, bonus)));
                return;
            }

            // A dragon's breath and Flame Blast take the monster's lowest resistance (DM:657-664).
            if (hit.pMissileAttacker != nullptr && (hit.missileSpellId == 97 || hit.missileSpellId == 123)
                && mawIsDragon(*hit.pMissileAttacker))
            {
                const MonsterDamageResistances &all = hit.resistances;
                const int lowest = std::min({all.fire, all.air, all.water, all.earth, all.spirit, all.mind, all.body,
                    all.light, all.dark, all.physical},
                    [](int left, int right)
                    {
                        return mawCappedMonsterResistance(left) < mawCappedMonsterResistance(right);
                    });
                hit.amount = int(std::ceil(resisted(hit.amount, lowest, bonus)));
                return;
            }

            if (!hit.weaponElements)
            {
                hit.amount = int(std::ceil(resisted(hit.amount, hit.resistance, bonus)));
                return;
            }

            // A weapon's elemental additions are each resisted by their own element, and join the hit after the boss
            // affixes (legendary-blows, DM:972-1000, ITM-L2).
            const ElementalDamageBonuses &elements = *hit.weaponElements;
            hit.resistedAdditions = resisted(elements.fire, hit.resistances.fire, bonus)
                + resisted(elements.air, hit.resistances.air, bonus)
                + resisted(elements.water, hit.resistances.water, bonus)
                + resisted(elements.body, hit.resistances.body, bonus)
                + resisted(elements.light, hit.resistances.light, bonus)
                + resisted(elements.dark, hit.resistances.dark, bonus);
            hit.amount = int(std::ceil(resisted(hit.amount, monsterResistanceFor(hit.resistances, hit.type), bonus)));
        });
    m_damageToMonster.add(
        "boss-affixes",
        [](MonsterDamageHit &hit)
        {
            // Adamantite shrugs off 4 x level^1.15 of every hit, down to a quarter of it (level capped at 255).
            if (hit.amount > 0 && hasAffix(hit.targetFacts, MawBossAffix::Adamantite))
            {
                const double level = std::min(hit.targetFacts.level, 255);
                hit.amount = int(mawRound(std::max(hit.amount - 4 * std::pow(level, 1.15), hit.amount / 4.0)));
            }
        });

    m_damageToMonster.add(
        "legendary-blows",
        [this](MonsterDamageHit &hit)
        {
            // The weapon's enchantments and auras join the hit here, after the boss affixes (DM:972-1000).
            if (hit.resistedAdditions > 0)
            {
                hit.amount = int(std::ceil(hit.amount + hit.resistedAdditions));
                hit.resistedAdditions = 0;
            }

            const Character *pAttacker = hit.pMeleeAttacker != nullptr ? hit.pMeleeAttacker : hit.pMissileAttacker;

            if (pAttacker == nullptr || hit.amount <= 0)
            {
                return;
            }

            // Legendary 17: a physical blow, or any missile or spell, adds 2 % of the monster's current HP through
            // its physical resistance; half for arrows and area spells; at the weapon's speed multiplier, an
            // arrow's at the bow's, a Death Knight's or Assassin's spell at the melee one, other spells x 1.015^Learning
            // (DM:1021-1044). A blaster shot (energy) counts as a spell.
            if (mawWearsLegendaryAffix(*pAttacker, LegendaryHealthDamage) && hit.pItemTable != nullptr
                && (hit.pMissileAttacker != nullptr || hit.type == CombatDamageType::Physical))
            {
                const bool arrow = hit.pMissileAttacker != nullptr && hit.missileSpellId == 0
                    && hit.type != CombatDamageType::Irresistible;
                const std::string line = mawClassLine(pAttacker->className);
                const bool meleeSpeed = hit.pMeleeAttacker != nullptr
                    || (!arrow && (line == "death_knight" || line == "assassin"));
                double extra = hit.targetCurrentHp * 0.02 / (1 + hit.resistances.physical / 100.0);

                if (arrow || isAreaSpell(hit.missileSpellId))
                {
                    extra *= 0.5;
                }

                if (meleeSpeed || arrow)
                {
                    extra *= mawCharacterAttackDelay(m_rules, *pAttacker, *hit.pItemTable,
                        arrow ? CharacterAttackMode::Bow : CharacterAttackMode::Melee, 0)
                                 .damageMultiplier;
                }
                else
                {
                    extra *= std::pow(1.015, skillLevel(*pAttacker, "Learning"));
                }

                hit.amount += int(mawRound(extra));
            }

            // Legendary 21: +5 % for each monster within 512 of the party, at most double, on melee blows as its text
            // says (DM:1063-1073 applies it to every hit; GAPS.md §11).
            if (hit.pMeleeAttacker != nullptr && mawWearsLegendaryAffix(*pAttacker, LegendaryCrowdDamage))
            {
                hit.amount = int(mawRound(hit.amount * std::min(1 + 0.05 * m_rules.nearbyMonsters(), 2.0)));
            }

            // Legendary 14: the melee crit chance above 100 % against the monster multiplies the whole hit, of every
            // kind (DM:1074-1080, ITM-L2).
            if (mawWearsLegendaryAffix(*pAttacker, LegendaryOvercrit) && hit.pItemTable != nullptr)
            {
                const CharacterSheetSummary sheet = characterSheet(*pAttacker, hit.pItemTable,
                    m_rules.standardItemEnchantTable(), m_rules.specialItemEnchantTable());
                MawCritInputs inputs =
                    meleeCritInputs(m_rules, *pAttacker, sheet, *hit.pItemTable, hit.targetFacts.level);
                inputs.overcrit = true;
                hit.amount = int(mawRound(hit.amount * std::max(mawCrit(inputs).chance, 1.0)));
            }
        });
    m_damageToMonster.add(
        "artifact-on-hit",
        [this](MonsterDamageHit &hit)
        {
            // A weapon artifact's on-hit damage, resisted by its own kind, joins after the boss affixes and the
            // legendaries, so Adamantite and legendary 21 never touch it (Damage.lua:1489-1496,
            // zzzMaw_Artifacts.lua:512-513, ITM-A7).
            const int bonus = mawMonsterResistanceBonus(m_rules, hit.targetFacts);
            double late = 0;

            for (size_t typeIndex = 0; typeIndex < hit.lateDamage.size(); ++typeIndex)
            {
                if (hit.lateDamage[typeIndex] > 0)
                {
                    late += resisted(hit.lateDamage[typeIndex],
                        monsterResistanceFor(hit.resistances, CombatDamageType(typeIndex)), bonus);
                }
            }

            hit.lateDamage = {};
            hit.amount = int(std::ceil(hit.amount + late));
        });
    m_damageToMonster.add(
        "damage-taken-stacks",
        [this](MonsterDamageHit &hit)
        {
            // Every physical hit on a monster grows by the Grandmaster spear stacks on it, and every hit by the
            // legendary 29 stacks, this blow's included, on the whole hit with every addition after the resistances
            // (DM:546-583, 1133-1138). An area spell counts only the stacks already stored: its own is stored 40 % of
            // the time afterwards (ITM-L2).
            if (hit.amount <= 0)
            {
                return;
            }

            const Character *pAttacker = hit.pMeleeAttacker != nullptr ? hit.pMeleeAttacker : hit.pMissileAttacker;
            double taken = hit.targetFacts.legendaryDamageTaken
                + (pAttacker != nullptr && mawWearsLegendaryAffix(*pAttacker, LegendaryDamageTaken)
                        && !isAreaSpell(hit.missileSpellId)
                    ? 1
                    : 0);

            if (hit.type == CombatDamageType::Physical)
            {
                taken += hit.targetFacts.spearDamageTaken
                    + (hit.pMeleeAttacker != nullptr && hit.pItemTable != nullptr
                            ? spearStack(m_rules, *hit.pMeleeAttacker, *hit.pItemTable)
                            : 0);
            }

            hit.amount = int(mawRound(hit.amount * (1 + taken / 100)));
        });
    m_damageToMonster.add(
        "map-affixes",
        [this](MonsterDamageHit &hit)
        {
            // A dimension map's cuts to the party's hits and its misses (zzMaw_Mapping.lua:16).
            if (hit.attackerFacts.level > 0 || hit.amount <= 0)
            {
                return;
            }

            const bool physical = hit.type == CombatDamageType::Physical;
            const std::optional<double> cut =
                m_rules.mapAffix(physical ? MawMapAffix::PlayerPhysicalDamage : MawMapAffix::PlayerMagicDamage);
            const std::optional<double> miss = m_rules.mapAffix(MawMapAffix::PlayerMiss);
            hit.amount = int(mawRound(hit.amount * (1 - cut.value_or(0) / 100)));

            if (miss && hit.pRng != nullptr && std::uniform_real_distribution<double>(0, 1)(*hit.pRng) < *miss / 100)
            {
                hit.amount = 0;
            }
        });

    m_damageToCharacter.add(
        "damage-recompute",
        [this](CharacterDamageHit &hit)
        {
            if (!mawMonsterHit(hit) || hit.amount <= 0)
            {
                return;
            }

            const ActorRulesetFacts &facts = hit.attackerFacts;
            double damage = hit.attack2 ? facts.attack2Damage : facts.attack1Damage;

            if (hit.spellId > 0)
            {
                // Spells from the player schools deal the monster's damage for their element times their
                // multiplier; the monster-only spells keep what they rolled.
                damage = uint32_t(hit.spellId) < FirstPlayerStyleMonsterSpell
                    ? mawMonsterBaseDamage(m_rules, facts, hit.partyCount, hit.type)
                        * mawMonsterSpellMultiplier(uint32_t(hit.spellId))
                    : hit.rolledAmount;
            }

            // A Berserker boss hits harder as its health runs out: x (2 - HP / max HP) at the blow (getMonsterDamage,
            // Estimates.lua:491-493).
            if (hasAffix(facts, MawBossAffix::Berserker) && hit.attackerMaxHp > 0)
            {
                damage *= mawBerserkerDamageMultiplier(hit.attackerCurrentHp, hit.attackerMaxHp);
            }

            std::uniform_int_distribution<int> spread(75, 125);
            const int first = spread(*hit.pRng);
            const int second = spread(*hit.pRng);
            damage = mawRound(damage) * mawMonsterDamageSpread(first, second);

            // Shrinking Ray and Dark Grasp cut what the monster deals by 30 %, together not more (DM:1575-1579,
            // 1753-1760).
            if (hit.attackerDebuffed)
            {
                damage *= 0.7;
            }

            // A personal shield took its share of the rolled hit before the rules saw it.
            if (hit.rolledAmount > 0 && hit.amount < hit.rolledAmount)
            {
                damage *= double(hit.amount) / hit.rolledAmount;
            }

            hit.amount = std::max(0, int(mawRound(damage)));
        });
    m_damageToCharacter.add(
        "map-energy",
        [this](CharacterDamageHit &hit)
        {
            // A dimension map turns monster hits to Energy now and then (MAW: always; DEVIATIONS.md). The hit is then
            // sized against resistances, as a monster's magic is (DM:1734-1736); a monster-only spell keeps its roll.
            const std::optional<double> energy = m_rules.mapAffix(MawMapAffix::EnergyDamage);

            if (!energy || !mawMonsterHit(hit)
                || std::uniform_real_distribution<double>(0, 1)(*hit.pRng) >= *energy / 100)
            {
                return;
            }

            const bool rescaled = hit.type != CombatDamageType::Energy
                && (hit.spellId <= 0 || uint32_t(hit.spellId) < FirstPlayerStyleMonsterSpell);

            if (rescaled)
            {
                const double from = mawMonsterBaseDamage(m_rules, hit.attackerFacts, hit.partyCount, hit.type);
                const double to =
                    mawMonsterBaseDamage(m_rules, hit.attackerFacts, hit.partyCount, CombatDamageType::Energy);
                hit.amount = from > 0 ? std::max(0, int(mawRound(hit.amount * to / from))) : hit.amount;
            }

            hit.type = CombatDamageType::Energy;
        });
    m_damageToCharacter.add(
        "mitigation",
        [this](CharacterDamageHit &hit)
        {
            if (!mawMonsterHit(hit))
            {
                // Traps, chest traps and event missiles: MAW's trap damage indoors and for anything but physical
                // and water hits outdoors (falls and drowning keep their own); Sparks deals a third (DM:1623-1652).
                const bool indoor = !m_rules.outdoorMap(m_rules.currentMap());

                if (indoor || (hit.type != CombatDamageType::Physical && hit.type != CombatDamageType::Water))
                {
                    hit.amount = trapDamage(*hit.pCharacter, hit.pItemTable, hit.pStandardItemEnchantTable,
                                     hit.pSpecialItemEnchantTable, hit.type, hit.partyCount)
                        / (hit.spellId == SparksSpell ? 3 : 1);
                    return;
                }

                hit.amount = GameMechanics::resolveCharacterIncomingDamage(
                    *hit.pCharacter,
                    hit.pItemTable,
                    hit.pStandardItemEnchantTable,
                    hit.pSpecialItemEnchantTable,
                    hit.amount,
                    hit.type,
                    *hit.pRng);
                return;
            }

            const Character &character = *hit.pCharacter;
            const CharacterSheetSummary sheet = characterSheet(
                character, hit.pItemTable, hit.pStandardItemEnchantTable, hit.pSpecialItemEnchantTable);
            MawMitigationInputs inputs = characterMitigation(m_rules, character, sheet, hit.pItemTable, hit.partyCount);

            // A dimension map's weaker armour and resistances (zzMaw-Stats.lua:1057-1059, 1130-1132).
            if (const std::optional<double> armor = m_rules.mapAffix(MawMapAffix::PlayerArmor))
            {
                inputs.armorClass = int(inputs.armorClass * (1 - *armor / 100));
            }

            if (const std::optional<double> resistance = m_rules.mapAffix(MawMapAffix::PlayerResistance))
            {
                for (int &value : inputs.resistances)
                {
                    value = int(value * (1 - *resistance / 100));
                }
            }

            inputs.damage = hit.amount;
            inputs.type = hit.type;
            inputs.attackerLevel = hit.attackerFacts.level;
            inputs.legendaryMultiplier = legendaryDefense(*hit.pCharacter);
            hit.amount = std::max(0, int(mawMitigatedDamage(inputs)));
        });
    m_damageToCharacter.add(
        "mist-form",
        [](CharacterDamageHit &hit)
        {
            // Only a monster's physical hit; falls and physical traps keep their damage (DM:1689-1692).
            if (mawMonsterHit(hit) && hit.type == CombatDamageType::Physical)
            {
                hit.amount = int(mawRound(hit.amount * hit.pCharacter->mistFormPhysicalShare));
            }
        });
    m_damageToCharacter.add(
        "solo-cover",
        [](CharacterDamageHit &hit)
        {
            if (hit.coverHalved)
            {
                hit.amount = int(hit.amount * 0.5);
            }
        });
    m_damageToCharacter.add(
        "disease",
        [](CharacterDamageHit &hit)
        {
            if (!mawMonsterHit(hit))
            {
                return;
            }

            const std::bitset<CharacterConditionCount> &conditions = hit.pCharacter->conditions;
            double multiplier = conditions.test(size_t(CharacterCondition::DiseaseSevere)) ? 2
                : conditions.test(size_t(CharacterCondition::DiseaseMedium))               ? 1.5
                : conditions.test(size_t(CharacterCondition::DiseaseWeak))                 ? 1.25
                                                                                            : 1;
            // A party of one takes half the extra (DM:1782-1784).
            multiplier = hit.partyCount == 1 ? (multiplier - 1) / 2 + 1 : multiplier;
            hit.amount = int(hit.amount * multiplier);
        });
    m_damageToCharacter.add(
        "boss-affixes",
        [](CharacterDamageHit &hit)
        {
            // An Exploding boss's hit is halved; applyMonsterHitEffects spreads the other half over the party.
            if (mawMonsterHit(hit) && hasAffix(hit.attackerFacts, MawBossAffix::Exploding))
            {
                hit.amount /= 2;
            }
        });
    m_damageToCharacter.add(
        "map-affixes",
        [this](CharacterDamageHit &hit)
        {
            // A dimension map's stronger monsters (zzMaw_Mapping.lua:1): more damage, a crit on any hit, and a share
            // of the victim's full HP.
            if (hit.amount <= 0)
            {
                return;
            }

            const bool monster = mawMonsterHit(hit);
            const std::optional<double> damage = m_rules.mapAffix(MawMapAffix::MonsterDamage);
            const std::optional<double> critical = m_rules.mapAffix(MawMapAffix::MonsterCritical);
            const std::optional<double> healthShare = m_rules.mapAffix(MawMapAffix::PlayerHealthDamage);
            double amount = hit.amount;

            if (monster && damage)
            {
                amount *= 1 + *damage / 100;
            }

            if (critical && std::uniform_real_distribution<double>(0, 1)(*hit.pRng) < *critical / 100)
            {
                amount *= 2;
            }

            if (monster && healthShare)
            {
                amount += hit.pCharacter->maxHealth * *healthShare / 100;
            }

            hit.amount = int(mawRound(amount));
        });
}

double mawDragonPushDistance(int fang, int monsterLevel)
{
    const double mult = double(fang) / std::pow(double(std::max(1, monsterLevel)), 0.75);
    return std::min(2048.0, 400.0 * std::pow(mult, 1.5));
}

bool mawFlightMap(const std::string &mapFileName)
{
    static const std::array<const char *, 11> FlightMaps = {
        "elema.odm", "elemf.odm", "elemw.odm", "out12.odm", "outa1.odm", "outa2.odm", "outa3.odm", "outb2.odm",
        "outb3.odm", "out05.odm", "out07.odm",
    };
    return std::find(FlightMaps.begin(), FlightMaps.end(), mapFileName) != FlightMaps.end();
}

bool mawAttackingEndsFly(const RulesetOptions &options, const std::string &mapFileName)
{
    return (options.difficulty >= RulesetDifficulty::Hard || options.challengeMode == RulesetChallengeMode::Austerity)
        && !mawFlightMap(mapFileName);
}

namespace
{
// Map affix 26 slows every attack the delay is read for: real attacks, the leech floor and the class spell delays
// (Global/zzMaw_Mapping.lua:19-23, CMB-6).
int mawMapAffixAttackDelay(const MawRules &rules, int delay)
{
    const std::optional<double> slower = rules.mapAffix(MawMapAffix::PlayerAttackSpeed);
    return slower ? int(mawRound(delay / (1 - *slower / 100))) : delay;
}
}

MawAttackDelay mawCharacterAttackDelay(
    const MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    CharacterAttackMode mode,
    double speed,
    std::optional<double> hasteSkill)
{
    // A broken weapon is no active item: it attacks at bare-hand pace (S:452-588, SKL-7).
    const auto equipped = [&itemTable](uint32_t itemId, const EquippedItemRuntimeState &state) -> const ItemDefinition *
    {
        return itemId != 0 && !state.broken ? itemTable.get(itemId) : nullptr;
    };
    const ItemDefinition *pOffHand = equipped(character.equipment.offHand, character.equipmentRuntime.offHand);
    const ItemDefinition *pMainHand = equipped(character.equipment.mainHand, character.equipmentRuntime.mainHand);
    const ItemDefinition *pBow = equipped(character.equipment.bow, character.equipmentRuntime.bow);
    MawAttackDelayInputs inputs;
    std::vector<int> handRecoveries;

    // With the Bow preference off, a ranged attack takes the melee delay (S:614-616; the tooltip's too, S:561-564).
    if ((mode == CharacterAttackMode::Bow || mode == CharacterAttackMode::DragonBreath)
        && rules.options().preferences.bowDisabled)
    {
        mode = CharacterAttackMode::Melee;
    }

    if (mode == CharacterAttackMode::Blaster
        || (pMainHand != nullptr && pMainHand->skillGroup == "Blaster")
        || (pOffHand != nullptr && pOffHand->skillGroup == "Blaster"))
    {
        return {mawMapAffixAttackDelay(rules, 40), 0.4};
    }

    if (mode == CharacterAttackMode::DragonBreath)
    {
        // A ranged attack without a bow starts from 100 (S:451-466).
        inputs.baseRecovery = 100;
    }
    else if (mode == CharacterAttackMode::Bow && pBow != nullptr)
    {
        const WeaponSkillNumbers *pNumbers = weaponSkillNumbers(canonicalSkillName(pBow->skillGroup));
        inputs.baseRecovery = mawItemRecovery(
            pNumbers != nullptr ? pNumbers->baseRecovery : UnknownWeaponRecovery,
            itemLevel(rules, *pBow, character.equipmentRuntime.bow, character),
            false);
        inputs.bonusPercent = pNumbers != nullptr
            ? perPoint(pNumbers->recoveryPerPoint, character, canonicalSkillName(pBow->skillGroup))
            : 0;

        if (isSwift(character.equipmentRuntime.bow))
        {
            inputs.swiftness += 0.3;
        }
    }
    else
    {
        std::vector<std::string> paidSkills;
        bool unarmedPaid = false;
        const std::array<std::pair<const ItemDefinition *, const EquippedItemRuntimeState *>, 2> hands = {{
            {pOffHand, &character.equipmentRuntime.offHand},
            {pMainHand, &character.equipmentRuntime.mainHand},
        }};

        for (size_t handIndex = 0; handIndex < hands.size(); ++handIndex)
        {
            const auto [pItem, pRuntime] = hands[handIndex];

            if (pItem == nullptr || !isWeapon(*pItem))
            {
                continue;
            }

            const std::string skill = mawWeaponSkill(character, *pItem);
            const WeaponSkillNumbers *pNumbers = weaponSkillNumbers(skill);
            handRecoveries.push_back(mawItemRecovery(
                pNumbers != nullptr ? pNumbers->baseRecovery : UnknownWeaponRecovery,
                itemLevel(rules, *pItem, *pRuntime, character),
                isTwoHanded(*pItem)));
            // A Minotaur's two-handed axe or halberd in the off hand pays no skill speed (S:482).
            const bool offHandTwoHandedAxe = handIndex == 0 && isTwoHanded(*pItem)
                && (canonicalSkillName(pItem->skillGroup) == "Axe" || mawIsHalberd(pItem->itemId));

            // Swiftness (41, 59): +0.3 for a two-hander, +0.15 for each one-handed weapon (S:464, 495-497).
            if (isSwift(*pRuntime))
            {
                inputs.swiftness += isTwoHanded(*pItem) ? 0.3 : 0.15;
            }

            if (pNumbers != nullptr && !offHandTwoHandedAxe
                && std::find(paidSkills.begin(), paidSkills.end(), skill) == paidSkills.end())
            {
                inputs.bonusPercent += perPoint(pNumbers->recoveryPerPoint, character, skill);
                paidSkills.push_back(skill);
            }

            if (skill == "Staff" && skillMastery(character, "Staff") >= SkillMastery::Grandmaster && !unarmedPaid)
            {
                inputs.bonusPercent += perPoint(UnarmedRecoveryPerPoint, character, "Unarmed");
                unarmedPaid = true;
            }
        }

        // Bare hands speed up with Unarmed, a dragon's Fangs excepted (S:508-513).
        if (pMainHand == nullptr && !unarmedPaid && !mawIsDragon(character))
        {
            inputs.bonusPercent += perPoint(UnarmedRecoveryPerPoint, character, "Unarmed");
        }

        int recoverySum = 0;

        for (int recovery : handRecoveries)
        {
            recoverySum += recovery;
        }

        // Two weapons average their recoveries; only the delay is rounded (S:514-524, 595).
        inputs.baseRecovery = handRecoveries.empty() ? 100 : double(recoverySum) / handRecoveries.size();

        // Armsmaster speeds every weapon but a staff, and never bare hands.
        if (pMainHand != nullptr && isWeapon(*pMainHand) && canonicalSkillName(pMainHand->skillGroup) != "Staff")
        {
            inputs.bonusPercent += perPoint(ArmsmasterSpeedPerPoint, character, "Armsmaster");
        }
    }

    // An Assassin's Subtlety stacks speed every reader of the delay up by s x stacks / 2 percent: blows, the leech
    // floor and the spell delays (S:540-550, CMB-19).
    const double subtlety = mawClassLine(character.className) == "assassin"
        ? trainedSkillLevel(character, "AirMagic") * rules.classRuntime(character).subtletyStacks / 2
        : 0;
    inputs.bonusPercent += mawSpeedRecoveryBonus(speed) + mawClassAttackSpeedPercent(character) + subtlety;

    inputs.armorImpairmentPercent = mawCharacterArmorImpairment(character, itemTable);
    inputs.hasteSkill = hasteSkill;
    inputs.buffScale = rules.buffScale();
    MawAttackDelay delay = mawAttackDelay(inputs);
    delay.delay = int(mawRound(delay.delay * mawArtifactAttackDelayMultiplier(rules, character)));

    // A dragon's bite slows with Fangs, any ranged delay (its breath; the Shoot readouts ask for a bow's) with Dragon
    // Ability: x (1 + 0.015 s) (CL:805-818).
    if (mode == CharacterAttackMode::Melee && mawIsDragon(character))
    {
        delay.delay = int(mawRound(delay.delay * (1 + 0.015 * skillLevel(character, "Unarmed"))));
    }
    else if ((mode == CharacterAttackMode::DragonBreath || mode == CharacterAttackMode::Bow
                 || mode == CharacterAttackMode::Wand)
        && mawIsDragon(character))
    {
        delay.delay = int(mawRound(delay.delay * (1 + 0.015 * skillLevel(character, "DragonAbility"))));
    }

    delay.delay = mawMapAffixAttackDelay(rules, delay.delay);
    return delay;
}

double mawCharacterArmorImpairment(const Character &character, const ItemTable &itemTable)
{
    // A broken shield or armour is no active item and slows nothing (S:452-588, SKL-7).
    const auto active = [&itemTable](uint32_t itemId, const EquippedItemRuntimeState &state) -> const ItemDefinition *
    {
        return itemId != 0 && !state.broken ? itemTable.get(itemId) : nullptr;
    };
    const ItemDefinition *pOffHand = active(character.equipment.offHand, character.equipmentRuntime.offHand);
    const ItemDefinition *pArmor = active(character.equipment.armor, character.equipmentRuntime.armor);
    double impairment = 0;

    if (pOffHand != nullptr && pOffHand->skillGroup == "Shield")
    {
        impairment += armorImpairment("Shield", skillMastery(character, "Shield"));
    }

    if (pArmor != nullptr)
    {
        const std::string armorSkill = canonicalSkillName(pArmor->skillGroup);
        impairment += armorImpairment(armorSkill, skillMastery(character, armorSkill));
    }

    return impairment;
}

namespace
{
double spearStack(const MawRules &rules, const Character &attacker, const ItemTable &itemTable)
{
    const ItemDefinition *pMainHand = attacker.equipment.mainHand != 0 ? itemTable.get(attacker.equipment.mainHand)
                                                                         : nullptr;

    if (pMainHand == nullptr || attacker.equipmentRuntime.mainHand.broken
        || mawWeaponSkill(attacker, *pMainHand) != "Spear"
        || skillMastery(attacker, "Spear") < SkillMastery::Grandmaster)
    {
        return 0;
    }

    return mawSpearStackPercent(rules, attacker, itemTable);
}
}

int mawFireAuraOnWeapon(
    const MawRules &rules, const Character &wearer, const ItemDefinition &weapon, const InventoryItem &item)
{
    EquippedItemRuntimeState state;
    state.specialEnchantId = item.specialEnchantId;
    state.rulesetFields = item.rulesetFields;
    const HeldWeapon held = {&weapon, &state, weapon.equipStat == "Missile", &wearer};
    return int(weaponFireAuraDamage(rules, wearer, held, false, 5));
}

std::optional<std::pair<int, int>> mawArtifactHitOnWeapon(
    const MawRules &rules, const Character &wearer, const ItemDefinition &weapon, const InventoryItem &item)
{
    if (rules.itemTable() == nullptr)
    {
        return std::nullopt;
    }

    EquippedItemRuntimeState state;
    state.specialEnchantId = item.specialEnchantId;
    state.rulesetFields = item.rulesetFields;
    const HeldWeapon held = {&weapon, &state, weapon.equipStat == "Missile", &wearer};
    const std::optional<MawEnchantRange> range = artifactHitRange(rules, wearer, *rules.itemTable(), held, 0, 5);

    if (!range)
    {
        return std::nullopt;
    }

    // As a blow rolls it (MawCombatRules::meleeAttack).
    const int minimum = int(mawRound(range->minimum));
    return std::pair(minimum, std::max(minimum, int(mawRound(range->maximum))));
}

double mawSpearStackPercent(const MawRules &rules, const Character &attacker, const ItemTable &itemTable)
{
    const ItemDefinition *pMainHand = attacker.equipment.mainHand != 0 ? itemTable.get(attacker.equipment.mainHand)
                                                                         : nullptr;
    const bool halberd = pMainHand != nullptr && mawWeaponSkill(attacker, *pMainHand) == "Spear"
        && isTwoHanded(*pMainHand);
    const double multiplier = mawCharacterAttackDelay(
        rules, attacker, itemTable, CharacterAttackMode::Melee, 0).damageMultiplier;
    return (2 + 0.02 * skillLevel(attacker, "Spear")) * multiplier * (halberd ? 1.5 : 1);
}

std::optional<int> MawCombatRules::characterAttackRecoveryTicks(
    const Character &character,
    CharacterAttackMode mode,
    const ItemTable &itemTable,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable) const
{
    const CharacterSheetSummary sheet = characterSheet(character, &itemTable, pStandardTable, pSpecialTable);
    return mawCharacterAttackDelay(
        m_rules, character, itemTable, mode, sheet.speed.actual, m_rules.auraSkill(5, &character))
        .delay;
}

void MawCombatRules::resolveCharacterAttack(
    CharacterAttackResult &attack,
    const CharacterAttackOnMonster &context) const
{
    const bool weaponAttack = attack.mode == CharacterAttackMode::Melee || attack.mode == CharacterAttackMode::Bow
        || attack.mode == CharacterAttackMode::Blaster;

    // A dragon's breath goes through MAW's attack too: its own delay, crit and spread (DM:629-668, CL:805-818).
    if (attack.canAttack && attack.mode == CharacterAttackMode::DragonBreath && context.pItemTable != nullptr
        && mawIsDragon(*context.pCharacter))
    {
        const Character &dragon = *context.pCharacter;
        const CharacterSheetSummary sheet = characterSheet(
            dragon, context.pItemTable, context.pStandardItemEnchantTable, context.pSpecialItemEnchantTable);
        const MawAttackDelay delay = mawCharacterAttackDelay(m_rules, dragon, *context.pItemTable, attack.mode,
            sheet.speed.actual, m_rules.auraSkill(5, &dragon));
        attack.recoverySeconds = float(delay.delay) / 128.0f * MawRealtimeRecoveryScale;
        const int referenceLevel = context.pTargetFacts != nullptr && context.pTargetFacts->level > 0
            ? context.pTargetFacts->level
            : int(mawRound(m_rules.state().totalLevel()));
        bool critical = false;
        attack.damage = std::max(0, int(mawRound(dragonBreathDamage(m_rules, dragon, sheet, context.minimumDamage,
            context.maximumDamage, referenceLevel, 1.0, *context.pRng, critical))));
        attack.criticalDamage = critical;
        return;
    }

    if (!attack.canAttack || !weaponAttack || context.pItemTable == nullptr)
    {
        return;
    }

    const Character &character = *context.pCharacter;
    const CharacterSheetSummary sheet = characterSheet(
        character, context.pItemTable, context.pStandardItemEnchantTable, context.pSpecialItemEnchantTable);
    const MawAttackDelay delay = mawCharacterAttackDelay(m_rules, character, *context.pItemTable, attack.mode,
        sheet.speed.actual, m_rules.auraSkill(5, &character));
    attack.recoverySeconds = float(delay.delay) / 128.0f * MawRealtimeRecoveryScale;

    // Weapon crits scale against the target; without one (a missile in flight) against the party's banked level.
    const int targetLevel = context.pTargetFacts != nullptr && context.pTargetFacts->level > 0
        ? context.pTargetFacts->level
        : std::max(1, int(mawRound(m_rules.state().totalLevel())));
    std::uniform_real_distribution<double> unit(0.0, 1.0);

    // Melee hits are decided now; a missile's hit is rolled where it lands.
    if (attack.mode == CharacterAttackMode::Melee && context.pTargetFacts != nullptr)
    {
        attack.hit = mawPartyHitChance(attack.attackBonus, targetLevel, m_rules.blessHitSkill(character),
                         m_rules.model(context.partyCount))
                >= unit(*context.pRng)
            && !skilledTargetDodges(*context.pTargetFacts, *context.pRng);

        if (!attack.hit)
        {
            attack.voiceHook = "attack_miss";
            return;
        }
    }

    const int minimum = std::max(0, context.minimumDamage);
    const int maximum = std::max(minimum, context.maximumDamage);
    std::uniform_int_distribution<int> roll(minimum, maximum);
    const int first = roll(*context.pRng);
    const int second = roll(*context.pRng);
    double damage = mawAverageOfTwoRolls(first, second);

    // An Assassin's Assassination bonus is for isolated targets: each other monster within 384 of the target takes a
    // fifth of it back, at most four fifths, and a blow the energy cannot pay, or on a monster that is not hostile,
    // loses all of it (MCC:365-431, FCOR-2-21).
    if (attack.mode == CharacterAttackMode::Melee && context.monstersNearTarget > 0
        && mawClassLine(character.className) == "assassin")
    {
        const int cost = 50 - 5 * int(skillMastery(character, "FireMagic"));
        const bool paid = character.spellPoints >= cost && context.targetHostile;
        const double share = paid ? std::min(0.8, 0.2 * (context.monstersNearTarget - 1)) : 1.0;
        damage -= mawAssassinationBonus(m_rules, character, *context.pItemTable) * share;
    }

    damage *= delay.damageMultiplier;

    MawCritInputs critInputs = meleeCritInputs(m_rules, character, sheet, *context.pItemTable, targetLevel);
    critInputs.overcrit = mawWearsLegendaryAffix(character, LegendaryOvercrit);
    const MawCrit crit = mawCrit(critInputs);
    const double critDraw = unit(*context.pRng);
    damage *= critFactor(crit, critInputs, critDraw);
    attack.criticalDamage = critDraw < crit.chance;
    // Legendary 26: each enchantment and aura rolls its own crit (IT:2130-2145, 4290-4300).
    const auto enchantCrit = [&]()
    {
        return mawWearsLegendaryAffix(character, LegendaryEnchantCrits) && unit(*context.pRng) < crit.chance
            ? crit.multiplier
            : 1.0;
    };

    // Weak halves every weapon hit, a dragon's bite too (DM:493; COMBAT_SPEC §13 item 8); a missile's own roll is
    // halved below, before the bow's add-ons.
    const double weakness = character.conditions.test(size_t(CharacterCondition::Weak)) ? 0.5 : 1;

    if (attack.mode == CharacterAttackMode::Melee)
    {
        damage *= weakness;
    }

    attack.damage = std::max(0, int(mawRound(damage)));

    if (attack.mode == CharacterAttackMode::Melee && context.pTargetFacts != nullptr)
    {
        // A Shaman's Fire burns a thousandth of the target's health per point, an Assassin's Poisons likewise as
        // water, at least the skill (DM:1047-1062).
        const std::string line = mawClassLine(character.className);
        const auto healthShare = [&](const char *pSkill)
        {
            const double skill = trainedSkillLevel(character, pSkill);
            return skill > 0 ? int(std::max(0.001 * skill * context.targetCurrentHp, skill)) : 0;
        };

        if (line == "shaman")
        {
            attack.rulesElementalDamage.fire += healthShare("FireMagic");
        }
        else if (line == "assassin")
        {
            attack.rulesElementalDamage.water += healthShare("WaterMagic");
        }

        // Each hand's damage enchantment and Fire Aura, each resisted by its own element (Damage.lua stage 27); they
        // replace the table's elemental weapon damage.
        attack.rulesWeaponElements = true;

        for (const HeldWeapon &weapon : heldWeapons(character, *context.pItemTable, true, false))
        {
            if (const std::optional<std::pair<CombatDamageType, double>> enchant = weaponEnchantDamage(
                    m_rules, character, *context.pItemTable, weapon, false, context.partyCount, context.pRng))
            {
                addElement(attack.rulesElementalDamage, enchant->first, int(enchant->second * enchantCrit()));
            }

            attack.rulesElementalDamage.fire +=
                int(weaponFireAuraDamage(m_rules, character, weapon, true, context.partyCount) * enchantCrit());

            if (const std::optional<MawEnchantRange> range = artifactHitRange(
                    m_rules, character, *context.pItemTable, weapon, context.targetKindFlags, context.partyCount))
            {
                // Resisted by its own kind after the boss affixes and the legendaries ("artifact-on-hit").
                const MawArtifact &artifact = *m_rules.itemData().artifact(weapon.pItem->itemId);
                const int roll = std::uniform_int_distribution<int>(int(mawRound(range->minimum)),
                    std::max(int(mawRound(range->minimum)), int(mawRound(range->maximum))))(*context.pRng);
                attack.rulesLateDamage[size_t(artifactHitType(artifact.onHitType))] += roll;
            }
        }

        attack.stunTarget = attack.itemStunTarget && !mawIgnoresCrowdControl(*context.pTargetFacts);
        attack.paralyzeTarget = false;
        applyWeaponStun(m_rules, attack, context, delay.damageMultiplier, targetLevel);
        applyRetaliation(attack, context);

        if (skillMastery(character, "Cover") >= SkillMastery::Grandmaster)
        {
            character.rulesetState.runtime.coverBonus = true;
        }
    }

    // A Grandmaster bow shoots fire arrows (MON:3865-3877, DM:529-541).
    if (attack.mode == CharacterAttackMode::Bow && character.equipment.bow != 0)
    {
        const ItemDefinition *pBow = context.pItemTable->get(character.equipment.bow);
        attack.fireArrow = pBow != nullptr && canonicalSkillName(pBow->skillGroup) == "Bow"
            && skillMastery(character, "Bow") >= SkillMastery::Grandmaster;
    }

    // Each fanned arrow rolls its own damage from the range, at the weapon's speed multiplier. Weak halves and a
    // Carnage arrow quarters the shot's own roll, on every hit, the one it strikes and each in the explosion; the bow's
    // aura, enchantment and artifact are added after, whole (stage_weaponRecompute, DM:439-459, 1003-1015,
    // ART:528-541; Carnage's text says half, GAPS.md D.5; CMB-16).
    if (attack.mode != CharacterAttackMode::Melee)
    {
        const double carnage = attack.explosiveArrow ? 0.25 : 1;
        attack.damage = int(mawRound(attack.damage * weakness * carnage));
        attack.minimumDamage = int(mawRound(minimum * delay.damageMultiplier * weakness * carnage));
        attack.maximumDamage = int(mawRound(maximum * delay.damageMultiplier * weakness * carnage));

        // The bow slot's damage enchantment and Fire Aura ride on every arrow or shot; a missile carries one damage
        // type, so they count as physical (DEVIATIONS 46).
        for (const HeldWeapon &weapon : heldWeapons(character, *context.pItemTable, false, true))
        {
            const MawDamageEnchant *pEnchant = mawDamageEnchant(weapon.pState->specialEnchantId);
            // Legendary 26 crits the aura and the enchantment of the shot together.
            const double crits = enchantCrit();
            double lowAdd = weaponFireAuraDamage(m_rules, character, weapon, true, context.partyCount) * crits;
            double highAdd = lowAdd;

            if (pEnchant != nullptr && !pEnchant->spellOnly)
            {
                const MawEnchantRange range = mawEnchantDamageRange(
                    weaponLevelDamage(m_rules, weapon, context.partyCount),
                    pEnchant->minimum,
                    pEnchant->maximum,
                    pEnchant->coefficient,
                    isTwoHanded(*weapon.pItem));
                const double scale = (mawWearsLegendaryAffix(character, EnchantDamageLegendary) ? 1.5 : 1)
                    * enchantPace(m_rules, character, *context.pItemTable, weapon) / 100 * crits;
                lowAdd += range.minimum * scale;
                highAdd += range.maximum * scale;
            }

            // A bow artifact's on-hit damage rides on its arrows as well.
            if (const std::optional<MawEnchantRange> range = artifactHitRange(
                    m_rules, character, *context.pItemTable, weapon, context.targetKindFlags, context.partyCount))
            {
                lowAdd += range->minimum;
                highAdd += range->maximum;
            }

            attack.minimumDamage += int(mawRound(lowAdd));
            attack.maximumDamage += int(mawRound(highAdd));
            attack.damage += int(mawRound((lowAdd + highAdd) / 2));
        }
    }
}

double mawDamageTakenPercent(
    const MawRules &rules,
    const Character &character,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    CombatDamageType type,
    int attackerLevel)
{
    return mawDamageTakenPercents(rules, character, pItemTable, pStandardItemEnchantTable, pSpecialItemEnchantTable,
        {type}, attackerLevel)[0];
}

std::vector<double> mawDamageTakenPercents(
    const MawRules &rules,
    const Character &character,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    const std::vector<CombatDamageType> &types,
    int attackerLevel)
{
    const CharacterSheetSummary sheet =
        characterSheet(character, pItemTable, pStandardItemEnchantTable, pSpecialItemEnchantTable);
    MawMitigationInputs inputs = characterMitigation(rules, character, sheet, pItemTable, 1);
    inputs.flatReduction = 0;
    inputs.damage = 10000;
    inputs.attackerLevel = attackerLevel;
    std::vector<double> percents;

    for (CombatDamageType type : types)
    {
        inputs.type = type;
        percents.push_back(mawMitigatedDamage(inputs) / 100);
    }

    return percents;
}

MawPowerReport mawPowerReport(
    MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    int partyCount,
    const std::string *pSpellName)
{
    CharacterAttackOnMonster context;
    context.pCharacter = &character;
    context.pItemTable = &itemTable;
    context.pStandardItemEnchantTable = pStandardItemEnchantTable;
    context.pSpecialItemEnchantTable = pSpecialItemEnchantTable;
    context.partyCount = partyCount;
    MawPowerReport report;
    const CharacterSheetSummary sheet =
        characterSheet(character, &itemTable, pStandardItemEnchantTable, pSpecialItemEnchantTable);
    report.vitality = powerAndVitality(rules, character, context, &sheet).second;
    const int reference = std::max(1, int(mawRound(rules.state().totalLevel())));
    MawBalanceModel &model = rules.model(partyCount);
    const CharacterCombatRows rows =
        mawCombatRows(rules, character, itemTable, {sheet.might.actual, sheet.accuracy.actual, sheet.luck.actual});
    MawCritInputs critInputs;
    critInputs.luck = sheet.luck.actual;
    critInputs.accuracy = sheet.accuracy.actual;
    critInputs.referenceLevel = reference;
    critInputs.fateSkill = rules.auraSkill(47);
    critInputs.buffScale = rules.buffScale();
    critInputs.madness = rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
    addMapCritAffixes(rules, critInputs);
    const MawCrit crit = mawCrit(critInputs);

    // (average x the crit's expected gain + enchantment damage) per second x hit chance x the class's multiplier.
    const auto blowPower = [&](double minimum, double maximum, int attack, const MawAttackDelay &delay, double extra)
    {
        const double average = (minimum + maximum) / 2 * (1 + std::min(crit.chance, 1.0) * (crit.multiplier - 1));
        return mawRound((average + extra) / (std::max(1, delay.delay) / 60.0)
            * mawPartyHitChance(attack, reference, rules.blessHitSkill(character), model) * delay.damageMultiplier
            * std::max(crit.chance, 1.0));
    };
    const auto weaponExtra = [&](const std::vector<HeldWeapon> &weapons)
    {
        double damage = 0;

        for (const HeldWeapon &weapon : weapons)
        {
            damage += weaponFireAuraDamage(rules, character, weapon, true, partyCount);

            if (const std::optional<std::pair<CombatDamageType, double>> enchant =
                    weaponEnchantDamage(rules, character, itemTable, weapon, false, partyCount, nullptr))
            {
                damage += enchant->second;
            }

            if (const std::optional<MawEnchantRange> range = artifactHitRange(
                    rules, character, itemTable, weapon, 0, partyCount))
            {
                damage += (range->minimum + range->maximum) / 2;
            }
        }

        return damage;
    };

    report.melee = blowPower(rows.meleeMinimumDamage, rows.meleeMaximumDamage, rows.meleeAttack,
        mawCharacterAttackDelay(rules, character, itemTable, CharacterAttackMode::Melee, sheet.speed.actual,
            rules.auraSkill(5, &character)),
        weaponExtra(heldWeapons(character, itemTable, true, false)));

    // A Master bowman looses two arrows.
    const double arrows = skillMastery(character, "Bow") >= SkillMastery::Master ? 2 : 1;
    report.ranged = blowPower(rows.rangedMinimumDamage * arrows, rows.rangedMaximumDamage * arrows, rows.rangedAttack,
        mawCharacterAttackDelay(rules, character, itemTable, CharacterAttackMode::Bow, sheet.speed.actual,
            rules.auraSkill(5, &character)),
        weaponExtra(heldWeapons(character, itemTable, false, true)));

    // The first spell of the battle orders, else the quick spell: its average with Intellect or Personality, the
    // Shaman's schools and the spell crit, plus the weapons' enchantments and Fire Aura as a spell carries them, per its
    // recovery.
    const std::string &spellName = pSpellName != nullptr ? *pSpellName : mawPowerSpellName(character);
    const SpellEntry *pSpell = rules.spellTable() != nullptr && !spellName.empty()
        ? rules.spellTable()->findByName(spellName)
        : nullptr;
    const std::optional<MawSpellDice> dice =
        pSpell != nullptr ? mawCasterSpellDice(rules, character, *pSpell) : std::nullopt;
    const std::optional<std::string> school =
        pSpell != nullptr ? resolveMagicSkillName(uint32_t(pSpell->id)) : std::nullopt;

    if (dice && school)
    {
        const SkillMastery mastery = std::max(skillMastery(character, *school), SkillMastery::Normal);
        double damage = (dice->add + skillLevel(character, *school) * (dice->diceMin + dice->diceMax) / 2.0)
            * pSpell->damagePercents[masteryIndex(mastery)] / 100
            * (1 + std::max(sheet.intellect.actual, sheet.personality.actual) / 1000.0);

        if (pSpell->id != 44 && pSpell->id < 99)
        {
            damage *= 1 + mawShamanSchoolSum(character) / 200;
        }

        MawCritInputs spellCritInputs = critInputs;
        spellCritInputs.kind = MawCritKind::Spell;
        spellCritInputs.intellect = sheet.intellect.actual;
        spellCritInputs.overcrit = mawWearsLegendaryAffix(character, LegendaryOvercrit);
        const MawCrit spellCrit = mawCrit(spellCritInputs);
        double extra = 0;

        for (const HeldWeapon &weapon : heldWeapons(character, itemTable, true, true))
        {
            extra += weaponFireAuraDamage(rules, character, weapon, false, partyCount);

            if (const std::optional<std::pair<CombatDamageType, double>> enchant =
                    weaponEnchantDamage(rules, character, itemTable, weapon, true, partyCount, nullptr))
            {
                extra += enchant->second;
            }
        }

        extra *= std::pow(1.02, mawAscension(character, MawAscensionUse::Damage).skill)
            / (isAreaSpell(uint32_t(pSpell->id)) ? 2.5 : 1);
        CharacterSpellCast cast;
        cast.pCaster = &character;
        cast.pItemTable = &itemTable;
        cast.pStandardItemEnchantTable = pStandardItemEnchantTable;
        cast.pSpecialItemEnchantTable = pSpecialItemEnchantTable;
        cast.pSpell = pSpell;
        cast.mastery = mastery;
        cast.skillLevel = uint32_t(skillLevel(character, *school));
        cast.partyCount = partyCount;
        const int recovery =
            rules.gameRules().spells.recoveryTicks(cast, spellNumbersAtMastery(*pSpell, mastery).recoveryTicks);
        report.spell = mawRound(
            (damage * (1 + std::min(spellCrit.chance, 1.0) * (spellCrit.multiplier - 1)) + extra)
            / (std::max(1, recovery) / 60.0) * std::max(spellCrit.chance, 1.0));
    }
    else if (const std::optional<MawHealSpell> heal = pSpell != nullptr && school
                 ? mawHealSpell(uint32_t(pSpell->id),
                       std::max(skillMastery(character, *school), SkillMastery::Normal),
                       mawModelConfig(rules.options(), partyCount).insanityMode)
                 : std::nullopt)
    {
        // A heal shows its healing per second: base + skill x per point, raised by Personality, plus the weapons'
        // enchantments as a spell carries them; heals do not crit here (calcPowerVitality's healingSpells branch).
        const SkillMastery mastery = std::max(skillMastery(character, *school), SkillMastery::Normal);
        const double healing = (heal->base + skillLevel(character, *school) * heal->perPoint)
            * (1 + sheet.personality.actual / std::min(1000.0 + 3 * character.level, 4000.0));
        double extra = 0;

        for (const HeldWeapon &weapon : heldWeapons(character, itemTable, true, true))
        {
            extra += weaponFireAuraDamage(rules, character, weapon, false, partyCount);

            if (const std::optional<std::pair<CombatDamageType, double>> enchant =
                    weaponEnchantDamage(rules, character, itemTable, weapon, true, partyCount, nullptr))
            {
                extra += enchant->second;
            }
        }

        extra *= std::pow(1.02, mawAscension(character, MawAscensionUse::Damage).skill);
        CharacterSpellCast cast;
        cast.pCaster = &character;
        cast.pItemTable = &itemTable;
        cast.pStandardItemEnchantTable = pStandardItemEnchantTable;
        cast.pSpecialItemEnchantTable = pSpecialItemEnchantTable;
        cast.pSpell = pSpell;
        cast.mastery = mastery;
        cast.skillLevel = uint32_t(skillLevel(character, *school));
        cast.partyCount = partyCount;
        const int recovery =
            rules.gameRules().spells.recoveryTicks(cast, spellNumbersAtMastery(*pSpell, mastery).recoveryTicks);
        report.spell = mawRound((healing + extra) / (std::max(1, recovery) / 60.0));
    }

    return report;
}

const std::string &mawPowerSpellName(const Character &character)
{
    for (const BattleOrder &order : character.battleOrders)
    {
        if (order.enabled && order.kind == BattleOrderKind::Spell && !order.spellName.empty())
        {
            return order.spellName;
        }
    }

    return character.quickSpellName;
}

std::optional<std::string> mawStrongestSchoolSpell(
    const MawRules &rules, const Character &character, const std::string &canonicalSchool)
{
    if (rules.spellTable() == nullptr)
    {
        return std::nullopt;
    }

    // A school's spells run from its first to its last by level, so the highest id is the strongest.
    const SpellEntry *pBest = nullptr;

    for (const uint32_t spellId : character.knownSpellIds)
    {
        const SpellEntry *pSpell = rules.spellTable()->findById(int(spellId));

        if (pSpell != nullptr && (pBest == nullptr || pSpell->id > pBest->id)
            && resolveMagicSkillName(spellId) == canonicalSchool && mawCasterSpellDice(rules, character, *pSpell))
        {
            pBest = pSpell;
        }
    }

    return pBest != nullptr ? std::optional<std::string>(pBest->name) : std::nullopt;
}

std::optional<MawSpellDice> mawCasterSpellDice(const MawRules &rules, const Character &caster, const SpellEntry &spell)
{
    if (std::find(MawDamageSpells.begin(), MawDamageSpells.end(), uint32_t(spell.id)) == MawDamageSpells.end())
    {
        return std::nullopt;
    }

    // Ascension grows the dice and the flat damage; Empower Magic multiplies them first (MAW reads Haste's numbers for
    // it, CLASSES_SPELLS_SPEC.md §3.3).
    const std::optional<double> empowerSkill = rules.auraSkill(28);
    const double empowerMultiplier = empowerSkill ? 1 + mawBuffMultiplier(5, *empowerSkill) : 1;
    MawSpellDice dice =
        mawAscendedSpellDice({spell.damageDiceMin, spell.damageDiceSides, spell.damageBase},
            mawAscension(caster, MawAscensionUse::Damage).skill, empowerMultiplier);

    // An Elementalist's stacks grow the dice and the flat damage by a tenth each (SP:1970-1973).
    if (mawClassLine(caster.className) == "elementalist")
    {
        const double stacks = 1 + 0.1 * rules.classRuntime(caster).elementalStacks;
        dice.diceMax = int(mawRound(dice.diceMax * stacks));
        dice.add = int(mawRound(dice.add * stacks));
    }

    return dice;
}

int MawCombatRules::reflectedDamage(const Party &party, size_t memberIndex, int damage, CombatDamageType type) const
{
    // The hit comes back as an ordinary hit of its kind, mitigated the Standard way, then ^0.85 (Damage.lua stage 4,
    // 1593-1598; Pain Reflection too, FCOR-2-1).
    const Character *pMember = party.member(memberIndex);

    if (pMember == nullptr || damage <= 0)
    {
        return 0;
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    const int resisted = GameMechanics::resolveCharacterIncomingDamage(*pMember, party.itemTable(),
        party.standardItemEnchantTable(), party.specialItemEnchantTable(), damage, type, rng);
    return int(std::pow(double(std::max(0, resisted)), 0.85));
}

MonsterMissileRules MawCombatRules::monsterMissileRules(const std::string &missileToken) const
{
    // MAW swaps the elemental missiles (objects 500, 505, 510, 515, 535, 540, 555) for its own and handles their hit
    // itself; arrows (545) and Body, Mind and Spirit (520-530) keep the engine's hit roll before the pipeline's.
    const size_t first = missileToken.find_first_not_of(" \t");
    const size_t last = missileToken.find_last_not_of(" \t");
    const std::string token =
        first == std::string::npos ? std::string() : toLowerCopy(missileToken.substr(first, last - first + 1));
    MonsterMissileRules rules;

    if (token == "air" || token == "earth" || token == "fire" || token == "water" || token == "light"
        || token == "dark" || token == "ener")
    {
        rules.noSpecialAttack = true;
        rules.noPainReflection = true;
        rules.randomTarget = true;
    }
    else if (token == "arrow" || token == "body" || token == "mind" || token == "spirit")
    {
        rules.secondSpeedRoll = true;
    }

    return rules;
}

float MawCombatRules::killRecoveryScale(const Character &killer) const
{
    // Legendary 11: a killing blow's recovery is halved (DM:1099-1116, CMB-2).
    return mawWearsLegendaryAffix(killer, LegendaryKillRecovery) ? 0.5f : 1.0f;
}

bool MawCombatRules::lifedrainHealsCasterThird() const
{
    // MAW swaps Lifedrain's hit to spell 200, so the engine's third never heals; the drain leeches through
    // applyPartyHitEffects instead (SP:3781-3790, SPL-7).
    return false;
}

bool MawCombatRules::usesPartyHitEffects() const
{
    return true;
}

bool MawCombatRules::callerHalvesWeakMissile(CharacterAttackMode mode) const
{
    return mode != CharacterAttackMode::Bow && mode != CharacterAttackMode::Blaster;
}

bool MawCombatRules::monsterShieldHalvesPartyMissile(uint32_t spellId) const
{
    return spellId != 0;
}

std::optional<int> MawCombatRules::worldSpellDamage(const CharacterSpellCast &cast) const
{
    // A trap or Armageddon rolls as the spell does: MAW's dice, Ascension, Intellect, crit and enchantments
    // (SP:1895-1896, 1926, 1976-2037).
    if (cast.pCaster == nullptr || cast.pSpell == nullptr)
    {
        return std::nullopt;
    }

    return rollSpellDamage(cast);
}

bool MawCombatRules::weaponKindMultiplierApplies() const
{
    // DM:420-461 rebuilds the blow from the weapon's range; the artifacts' x2 rides on their on-hit damage
    // (artifactHitRange), and the relics and slaying enchantments have none (CMB-1).
    return false;
}

bool MawCombatRules::addsWeaponElementalDamage() const
{
    // resolveCharacterAttack adds the weapons' enchantments, Fire Auras and artifacts itself: to a blow as its
    // elements, to an arrow's own damage (stage_weaponRecompute).
    return false;
}

std::optional<int> MawCombatRules::spellDamageOnTarget(const CharacterSpellCast &cast, const SpellTargetState &target)
    const
{
    constexpr int MassDistortion = 44;

    if (cast.pSpell == nullptr || cast.pSpell->id != MassDistortion)
    {
        return std::nullopt;
    }

    // An Assassin's Mass Distortion is a weapon blow (classSpellDamage); the resistance stage scales it.
    if (mawClassSpell(cast.pCaster->className, uint32_t(MassDistortion)) != nullptr)
    {
        return std::nullopt;
    }

    const double damage = std::max(0, target.currentHp) * (0.15 + 0.005 * cast.skillLevel)
        * massDistortionScale(m_rules.options(), target.pFacts);
    return int(mawRound(damage));
}

std::optional<SkillMastery> MawCombatRules::spellChainMastery(int spellId, SkillMastery mastery) const
{
    constexpr int ChainLightning = 18;

    if (spellId != ChainLightning || mastery <= SkillMastery::Normal)
    {
        return std::nullopt;
    }

    return SkillMastery(int(mastery) - 1);
}

int MawCombatRules::rollSpellDamage(const CharacterSpellCast &cast, bool *pCritical) const
{
    bool critical = false;
    const auto reportCritical = [pCritical, &critical](int damage)
    {
        if (pCritical != nullptr)
        {
            *pCritical = critical;
        }

        return damage;
    };
    const SpellEntry &spell = *cast.pSpell;
    const MawClassSpell *pClassSpell = mawClassSpell(cast.pCaster->className, uint32_t(spell.id));

    if (pClassSpell != nullptr && pClassSpell->damage[0] > 0 && cast.pItemTable != nullptr)
    {
        const int damage = classSpellDamage(cast, *pClassSpell, critical);
        return reportCritical(damage);
    }

    // A dragon's Flame Blast is its breath at 70 % (Novice and Expert), 85 % (Master) or all of it, with the breath's
    // crit (against the party's level: the cast knows no target) and spread (DM:629-668).
    if (spell.id == 123 && mawIsDragon(*cast.pCaster) && cast.pItemTable != nullptr)
    {
        static constexpr std::array<double, 4> Share = {0.7, 0.7, 0.85, 1.0};
        const CharacterSheetSummary sheet = characterSheet(
            *cast.pCaster, cast.pItemTable, cast.pStandardItemEnchantTable, cast.pSpecialItemEnchantTable);
        const CharacterCombatRows rows = mawCombatRows(m_rules, *cast.pCaster, *cast.pItemTable,
            {sheet.might.actual, sheet.accuracy.actual, sheet.luck.actual});
        static thread_local std::mt19937 rng(std::random_device{}());
        const int damage = int(mawRound(dragonBreathDamage(m_rules, *cast.pCaster, sheet, rows.rangedMinimumDamage,
            rows.rangedMaximumDamage, int(mawRound(m_rules.state().totalLevel())),
            Share[size_t(std::clamp(int(cast.mastery), 1, 4)) - 1], rng, critical)));
        return reportCritical(damage);
    }

    const std::optional<MawSpellDice> casterDice = mawCasterSpellDice(m_rules, *cast.pCaster, spell);

    if (!casterDice)
    {
        return CombatRules::rollSpellDamage(cast, pCritical);
    }

    const Character &caster = *cast.pCaster;
    const MawSpellDice dice = *casterDice;
    static thread_local std::mt19937 rng(std::random_device{}());
    double damage = dice.add;

    if (dice.diceMin != dice.diceMax)
    {
        std::uniform_int_distribution<int> roll(dice.diceMin, std::max(dice.diceMin, dice.diceMax));

        for (uint32_t point = 0; point < cast.skillLevel; ++point)
        {
            damage += roll(rng);
        }
    }
    else
    {
        damage += double(spell.damageDiceSides) * cast.skillLevel;
    }

    damage = damage * spell.damagePercents[masteryIndex(cast.mastery)] / 100;

    const CharacterSheetSummary sheet =
        characterSheet(caster, cast.pItemTable, cast.pStandardItemEnchantTable, cast.pSpecialItemEnchantTable);
    damage *= 1 + std::max(sheet.intellect.actual, sheet.personality.actual) / 1000.0;

    // A Shaman's every school strengthens the spells but Mass Distortion (DM:1118-1128).
    if (spell.id != 44 && spell.id < 99)
    {
        damage *= 1 + mawShamanSchoolSum(caster) / 200;
    }

    // Spell crits measure against the party's banked level, not the target.
    MawCritInputs critInputs;
    critInputs.kind = MawCritKind::Spell;
    critInputs.luck = sheet.luck.actual;
    critInputs.intellect = sheet.intellect.actual;
    critInputs.fateSkill = m_rules.auraSkill(47);
    critInputs.buffScale = m_rules.buffScale();
    critInputs.referenceLevel = mawRound(m_rules.state().totalLevel());
    critInputs.madness = m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
    addMapCritAffixes(m_rules, critInputs);
    critInputs.overcrit = mawWearsLegendaryAffix(caster, LegendaryOvercrit);
    const MawCrit crit = mawCrit(critInputs);
    const double critDraw = std::uniform_real_distribution<double>(0.0, 1.0)(rng);
    damage *= critFactor(crit, critInputs, critDraw);
    critical = critDraw < crit.chance;
    const auto enchantCrit = [&]()
    {
        return mawWearsLegendaryAffix(caster, LegendaryEnchantCrits)
                && std::uniform_real_distribution<double>(0.0, 1.0)(rng) < crit.chance
            ? crit.multiplier
            : 1.0;
    };

    // Every weapon slot's damage enchantment and Fire Aura join the spell, grown by Ascension and at 40 % on area
    // spells; the spell's element resists them (SP:2021-2036).
    if (cast.pItemTable != nullptr)
    {
        const bool area = isAreaSpell(uint32_t(spell.id));
        const double ascension = std::pow(1.015, mawAscension(caster, MawAscensionUse::Damage).skill);

        for (const HeldWeapon &weapon : heldWeapons(caster, *cast.pItemTable, true, true))
        {
            double weaponDamage = weaponFireAuraDamage(m_rules, caster, weapon, false, cast.partyCount) * enchantCrit();

            if (const std::optional<std::pair<CombatDamageType, double>> enchant = weaponEnchantDamage(
                    m_rules, caster, *cast.pItemTable, weapon, true, cast.partyCount, &rng))
            {
                weaponDamage += enchant->second * enchantCrit();
            }

            damage += weaponDamage * ascension / (area ? 2.5 : 1);
        }
    }

    return reportCritical(std::max(0, int(mawRound(damage))));
}

int MawCombatRules::classSpellDamage(const CharacterSpellCast &cast, const MawClassSpell &spell, bool &critical) const
{
    // A weapon blow of the caster: its roll and crit plus both hands' Fire Aura and average enchantment damage, the
    // weapon's speed multiplier, halved when Weak, times the spell's share at its school's mastery; no Intellect or
    // spell crit (DM:695-742, 820-870).
    const Character &caster = *cast.pCaster;
    const CharacterSheetSummary sheet =
        characterSheet(caster, cast.pItemTable, cast.pStandardItemEnchantTable, cast.pSpecialItemEnchantTable);
    const CharacterStatValues stats = {sheet.might.actual, sheet.accuracy.actual, sheet.luck.actual};
    const CharacterCombatRows rows = mawCombatRows(m_rules, caster, *cast.pItemTable, stats);
    const MawAttackDelay delay = mawCharacterAttackDelay(m_rules, caster, *cast.pItemTable,
        CharacterAttackMode::Melee, sheet.speed.actual, m_rules.auraSkill(5, &caster));
    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<int> roll(rows.meleeMinimumDamage, std::max(rows.meleeMinimumDamage,
        rows.meleeMaximumDamage));
    // rollDice: the mean of two rolls (DM:32-34).
    const int first = roll(rng);
    double damage = mawAverageOfTwoRolls(first, roll(rng));

    // An Assassin's crowd takes back its share of the Assassination bonus, a spell's at half (MCC:414-427; spells
    // pay no energy for it).
    if (cast.monstersNearTarget > 0 && mawClassLine(caster.className) == "assassin")
    {
        damage -= mawAssassinationBonus(m_rules, caster, *cast.pItemTable) / 2
            * std::min(0.8, 0.2 * (cast.monstersNearTarget - 1));
    }

    MawCritInputs critInputs;
    critInputs.luck = sheet.luck.actual;
    critInputs.accuracy = sheet.accuracy.actual;
    // Against the named monster's level (A1.12), else the party's banked level.
    critInputs.referenceLevel =
        cast.targetLevel > 0 ? double(cast.targetLevel) : std::max(1.0, mawRound(m_rules.state().totalLevel()));
    critInputs.fateSkill = m_rules.auraSkill(47);
    critInputs.buffScale = m_rules.buffScale();
    critInputs.madness = m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
    addMapCritAffixes(m_rules, critInputs);
    critInputs.overcrit = mawWearsLegendaryAffix(caster, LegendaryOvercrit);
    const MawCrit crit = mawCrit(critInputs);
    const double critDraw = std::uniform_real_distribution<double>(0.0, 1.0)(rng);
    damage *= critFactor(crit, critInputs, critDraw);
    critical = critDraw < crit.chance;

    for (const HeldWeapon &weapon : heldWeapons(caster, *cast.pItemTable, true, false))
    {
        damage += weaponFireAuraDamage(m_rules, caster, weapon, false, cast.partyCount);

        if (const std::optional<std::pair<CombatDamageType, double>> enchant = weaponEnchantDamage(
                m_rules, caster, *cast.pItemTable, weapon, false, cast.partyCount, nullptr))
        {
            damage += enchant->second;
        }
    }

    damage *= delay.damageMultiplier;

    if (caster.conditions.test(size_t(CharacterCondition::Weak)))
    {
        damage *= 0.5;
    }

    damage *= spell.damage[size_t(std::clamp(int(cast.mastery), 1, 4)) - 1];
    return std::max(0, int(mawRound(damage)));
}

int MawCombatRules::environmentDamage(
    const Party &party,
    size_t memberIndex,
    int damage,
    CombatDamageType type,
    bool indoor) const
{
    const Character *pMember = party.member(memberIndex);

    if (pMember == nullptr || damage <= 0)
    {
        return damage;
    }

    int amount = damage;

    // MAW's trap damage indoors and for anything but physical and water hits outdoors (falls and drowning keep their
    // own, without the legendaries' cut; ST:761-776, CMB-14).
    if (indoor || (type != CombatDamageType::Physical && type != CombatDamageType::Water))
    {
        amount = trapDamage(*pMember, party.itemTable(), party.standardItemEnchantTable(),
            party.specialItemEnchantTable(), type, int(std::max<size_t>(1, party.members().size())));
    }

    // Dimension affix 2 doubles any hit now and then, the environment's too (DM:1934-1951, CMB-14).
    static thread_local std::mt19937 rng(std::random_device{}());
    const std::optional<double> critical = m_rules.mapAffix(MawMapAffix::MonsterCritical);

    if (amount > 0 && critical && std::uniform_real_distribution<double>(0, 1)(rng) < *critical / 100)
    {
        amount *= 2;
    }

    return amount;
}

int MawCombatRules::trapDamage(
    const Character &member,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    CombatDamageType type,
    int partyCount) const
{
    MawBalanceModel &model = m_rules.model(std::max(1, partyCount));
    const int perception = int(skillMastery(member, "Perception"));
    const CharacterSheetSummary sheet = characterSheet(member, pItemTable, pStandardTable, pSpecialTable);
    MawMitigationInputs inputs = characterMitigation(m_rules, member, sheet, pItemTable, partyCount);
    inputs.damage = model.monsterDamage(std::max(1.0, m_rules.state().totalLevel()))
        * std::min((11 - 2 * perception) / 10.0, 1.0);
    inputs.type = type;
    // A trap is measured against the victim's own level; legendaries 18 and 22 cut it before the class's flat
    // reduction, as a monster's hit (ST:761-776).
    inputs.attackerLevel = member.level;
    inputs.legendaryMultiplier = legendaryDefense(member);
    return std::max(0, int(mawMitigatedDamage(inputs)));
}

void MawCombatRules::summonBossFamilyMember(
    IGameplayWorldRuntime &world, const GameplayRuntimeActorState &summonerState, std::mt19937 &rng) const
{
    if (summonerState.monsterId <= 0)
    {
        return;
    }

    const MawMonsterFamily family = mawMonsterFamily(world.monsterTable(), summonerState.monsterId);
    const int16_t monsterId =
        int16_t(std::uniform_real_distribution<double>(0, 1)(rng) < 0.75 ? family.row(1) : family.row(2));
    // Halfway to the party, at MAW's summon speed 350.
    GameplayMonsterSpawnRequest request;
    request.monsterId = monsterId;
    request.x = (summonerState.preciseX + world.partyX()) / 2;
    request.y = (summonerState.preciseY + world.partyY()) / 2;
    request.z = (summonerState.preciseZ + world.partyFootZ()) / 2;
    request.radius = 1.0f;
    request.moveSpeed = 350;
    request.seed = rng();
    world.spawnMonsters(request);
}

float MawCombatRules::partyMissileHomingTurnRate() const
{
    // MAW turns the missile onto its target every frame; a turn this fast does the same at any frame rate.
    constexpr float HomingTurnRadiansPerSecond = 40.0f;
    return m_rules.options().preferences.homingProjectiles ? HomingTurnRadiansPerSecond : 0.0f;
}

bool MawCombatRules::bowDisabled() const
{
    return m_rules.options().preferences.bowDisabled;
}

float MawCombatRules::monsterMissileHomingLockRate(uint32_t spellId) const
{
    // MAW re-aims while the missile points within 0.5° of the party, tested once a rendered frame, so its grip grows
    // with the frame rate. Ours is the same at any frame rate and firmer, 300° a second (user, 2026-10-27): a party
    // strafing on foot or flying (768 a second) is still hit, one flying fast straight across the flight escapes.
    constexpr float LockRadiansPerSecond = 300.0f * 3.14159265f / 180.0f;
    constexpr std::array<uint32_t, 6> NeverHoming = {9, 15, 22, 24, 32, 93};

    if (std::find(NeverHoming.begin(), NeverHoming.end(), spellId) != NeverHoming.end())
    {
        return 0.0f;
    }

    return m_rules.options().preferences.homingProjectiles ? LockRadiansPerSecond : 0.0f;
}

void MawCombatRules::applyRetaliation(CharacterAttackResult &attack, const CharacterAttackOnMonster &context) const
{
    const Character &character = *context.pCharacter;
    CharacterRulesRuntime &state = character.rulesetState.runtime;

    if (state.retaliationStacks <= 0)
    {
        return;
    }

    // Below Grandmaster the stacks count as one (they cannot exceed it anyway).
    const int stacks = skillMastery(character, "Retaliation") >= SkillMastery::Grandmaster
        ? state.retaliationStacks
        : 1;
    state.retaliationStacks = 0;
    const auto [power, vitality] = powerAndVitality(m_rules, character, context);
    // The monster's resistance divides the bonus with the rest of the hit.
    attack.damage += int(mawRound(std::pow(power, 0.25)) * mawRound(std::pow(vitality, 0.25))
        * skillLevel(character, "Retaliation") * stacks);
    std::uniform_real_distribution<double> unit(0.0, 1.0);

    // Not an Unstoppable boss (stage_retaliation, DM:891).
    if (unit(*context.pRng) < 0.25 * stacks && !mawIgnoresCrowdControl(*context.pTargetFacts))
    {
        attack.paralyzeTarget = true;
        attack.paralyzeSeconds =
            std::max(attack.paralyzeSeconds.value_or(0.0f), context.pTargetFacts->bossAffix != 0 ? 1.0f : 2.0f);
    }

    attack.recoverySeconds *= float(std::max(1 - 0.3 * stacks, 0.0));
}

std::optional<CoverOutcome> MawCombatRules::coverMonsterAttack(Party &party, const MonsterAttackCover &attack) const
{
    const bool solo = party.members().size() == 1;
    const SkillMastery required = mawCoverRequiredMastery(attack.spell, attack.type == CombatDamageType::Physical);
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    std::optional<size_t> coverer;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const Character &member = party.members()[memberIndex];

        if ((memberIndex == attack.targetIndex) != solo || !member.hasSkill("Cover")
            || member.rulesetState.coverDisabled || skillMastery(member, "Cover") < required || !conscious(member))
        {
            continue;
        }

        CharacterRulesRuntime &state = member.rulesetState.runtime;
        const double chance = mawCoverChance(skillLevel(member, "Cover"), state.coverBonus);
        state.coverBonus = false;

        if (unit(*attack.pRng) < chance
            && (!coverer || member.health > party.members()[*coverer].health))
        {
            coverer = memberIndex;
        }
    }

    if (!coverer)
    {
        return std::nullopt;
    }

    const Character &member = party.members()[*coverer];

    // Legendary 23: covering an ally restores 3 % of full HP (zzMAW-Skills.lua:1294-1296).
    if (mawWearsLegendaryAffix(member, LegendaryCoverHeal))
    {
        party.healMember(*coverer, int(Party::effectiveMaximumHealth(member) * 0.03));
    }

    if (member.hasSkill("Retaliation") && unit(*attack.pRng) <= skillLevel(member, "Retaliation") / 100.0)
    {
        CharacterRulesRuntime &state = member.rulesetState.runtime;
        const int maximum = skillMastery(member, "Retaliation") >= SkillMastery::Grandmaster ? 3 : 1;
        state.retaliationStacks = std::min(state.retaliationStacks + 1, maximum);
        // Five game minutes.
        state.retaliationSeconds = 10;
    }

    return CoverOutcome {*coverer, solo};
}

int MawCombatRules::absorbCharacterDamage(Party &party, size_t memberIndex, int damage) const
{
    Character *pMember = party.member(memberIndex);

    if (pMember == nullptr || damage <= 0)
    {
        return damage;
    }

    // Mana Shield first, then legendary 15 on what is left, then Divine Protection (DM:1866-1903).
    if (pMember->hasSkill("ManaShield") && !pMember->rulesetState.manaShieldDisabled)
    {
        const MawManaShieldResult shielded = mawManaShield(
            damage, pMember->spellPoints, skillLevel(*pMember, "ManaShield"), skillMastery(*pMember, "ManaShield"));
        pMember->spellPoints -= shielded.spellPointsSpent;
        damage = std::max(0, shielded.damage);
    }

    return divineProtection(party, memberIndex, legendaryProtection(party, memberIndex, damage));
}

int MawCombatRules::legendaryProtection(Party &party, size_t memberIndex, int damage) const
{
    // Legendary 15: a lethal hit is taken away and the member set to a quarter of full HP, once per 150 game minutes
    // (DM:1869-1886).
    Character &member = *party.member(memberIndex);
    float &readyMinutes = member.rulesetState.legendaryProtectionReadyGameMinutes;

    if (damage < member.health || !conscious(member) || !mawWearsLegendaryAffix(member, LegendaryProtection)
        || m_gameMinutes < readyMinutes)
    {
        return damage;
    }

    readyMinutes = m_gameMinutes + 150;
    member.health = Party::effectiveMaximumHealth(member) / 4;
    m_statusMessages.push_back(Engine::tr("Legendary power saves you from lethal damage"));
    return 0;
}

double MawCombatRules::legendaryDefense(const Character &character) const
{
    const double toughness = mawWearsLegendaryAffix(character, LegendaryToughness) ? 0.9 : 1;
    const double crowd = mawWearsLegendaryAffix(character, LegendaryCrowdDefense)
        ? std::max(std::pow(0.97, m_rules.nearbyMonsters()), 0.5)
        : 1;
    return toughness * crowd;
}

int MawCombatRules::divineProtection(Party &party, size_t memberIndex, int damage) const
{
    Character *pMember = party.member(memberIndex);

    if (pMember == nullptr || damage < pMember->health || !conscious(*pMember)
        || mawClassLine(pMember->className) != "seraphim")
    {
        return damage;
    }

    // Once per 150 game minutes, kept with the character (DM:1888-1903).
    float &readyMinutes = pMember->rulesetState.divineProtectionReadyGameMinutes;

    if (m_gameMinutes < readyMinutes)
    {
        return damage;
    }

    readyMinutes = m_gameMinutes + 150;
    const int maximum = pMember->maxHealth + pMember->permanentBonuses.maxHealth + pMember->magicalBonuses.maxHealth;
    pMember->health += int(mawRound(maximum * 0.25));
    m_statusMessages.push_back(Engine::tr("Divine Protection saves you from lethal damage"));
    return std::min(damage, pMember->health - 1);
}

void MawCombatRules::updateArtifacts(Party &party, IGameplayWorldRuntime &world) const
{
    const float now = world.gameMinutes();

    // The spells artifacts cast on the monsters struck since the last update, free and without recovery.
    for (const ArtifactCast &cast : std::exchange(m_artifactCasts, {}))
    {
        if (m_rules.spellTable() == nullptr || cast.memberIndex >= party.members().size())
        {
            continue;
        }

        PartySpellCastRequest request;
        request.casterMemberIndex = cast.memberIndex;
        request.spellId = cast.spellId;
        request.targetActorIndex = cast.actorIndex;
        request.skillLevelOverride = std::max(cast.skillLevel, 1u);
        request.skillMasteryOverride = std::max(cast.mastery, SkillMastery::Normal);
        request.bypassRequiredMastery = true;
        request.bypassGameplayCasterValidation = true;
        request.spendMana = false;
        request.applyRecovery = false;
        const PartySpellCastResult result = PartySpellSystem::castSpell(party, world, *m_rules.spellTable(), request);

        if (result.status == PartySpellCastStatus::Succeeded)
        {
            world.applyPendingSpellCastWorldEffects(result);
        }
    }

    // Every 2 seconds (a game minute): the Horn of Ros, carried by anyone, keeps Detect Life on the party and the Ghost
    // Ring Preservation on its wearer (zzzMaw_Artifacts.lua:728-794). The table's other buffs are Standard's powers of
    // those artifacts (half missile damage for Shield, armour class for Stoneskin, water walking).
    if (m_artifactBuffMinutes < 0 || now - m_artifactBuffMinutes >= 1 || now < m_artifactBuffMinutes)
    {
        m_artifactBuffMinutes = now;
        const bool horn = std::any_of(party.members().begin(), party.members().end(),
            [](const Character &member)
            {
                return std::any_of(member.inventory.begin(), member.inventory.end(),
                    [](const InventoryItem &item) { return item.objectDescriptionId == 2055; });
            });

        // Each tick the buff lasts at least three game minutes more, at Master power 3 unless it is stronger, so it
        // never lapses while the item is held (refreshBuff, zzzMaw_Artifacts.lua:755-762, ITM-A9).
        constexpr float BuffSeconds = 6.0f;
        constexpr int BuffPower = 3;
        const PartyBuffState *pDetectLife = party.partyBuff(PartyBuffId::DetectLife);

        if (horn && pDetectLife != nullptr && pDetectLife->active() && pDetectLife->power >= BuffPower)
        {
            const PartyBuffState held = *pDetectLife;
            party.applyPartyBuff(PartyBuffId::DetectLife, std::max(held.remainingSeconds, BuffSeconds), held.power,
                held.spellId, held.skillLevel, held.skillMastery, held.casterMemberIndex);
        }
        else if (horn)
        {
            const float remaining = pDetectLife != nullptr ? pDetectLife->remainingSeconds : 0.0f;
            party.applyPartyBuff(PartyBuffId::DetectLife, std::max(remaining, BuffSeconds), BuffPower,
                spellIdValue(SpellId::DetectLife), BuffPower, SkillMastery::Master, 0);
        }

        for (size_t index = 0; index < party.members().size(); ++index)
        {
            if (mawWornItemCount(party.members()[index], {1347}) == 0)
            {
                continue;
            }

            const CharacterBuffState *pPreservation = party.characterBuff(index, CharacterBuffId::Preservation);

            if (pPreservation != nullptr && pPreservation->active() && pPreservation->power >= BuffPower)
            {
                const CharacterBuffState held = *pPreservation;
                party.applyCharacterBuff(index, CharacterBuffId::Preservation,
                    std::max(held.remainingSeconds, BuffSeconds), held.power, held.spellId, held.skillLevel,
                    held.skillMastery, held.casterMemberIndex);
            }
            else
            {
                party.applyCharacterBuff(index, CharacterBuffId::Preservation,
                    std::max(pPreservation != nullptr ? pPreservation->remainingSeconds : 0.0f, BuffSeconds),
                    BuffPower, spellIdValue(SpellId::Preservation), BuffPower, SkillMastery::Master, uint32_t(index));
            }
        }
    }

    // The regeneration tick, every 5 game minutes (events.RegenTick): Ethric's Staff drains 3 HP from all but a Lich,
    // and Cycle of Life pulls its wearer towards the HP of those above (zzzMaw_Artifacts.lua:555-625).
    const float tick = std::floor(now / 5);

    if (m_regenerationTickMinutes < 0 || tick < m_regenerationTickMinutes)
    {
        m_regenerationTickMinutes = tick;
    }

    if (tick == m_regenerationTickMinutes)
    {
        return;
    }

    m_regenerationTickMinutes = tick;
    const auto out = [](const Character &member)
    {
        return member.conditions.test(size_t(CharacterCondition::Dead))
            || member.conditions.test(size_t(CharacterCondition::Petrified))
            || member.conditions.test(size_t(CharacterCondition::Eradicated));
    };

    // Auto-repair: the best Repair skill x mastery of the members who can act mends every broken item whose repair
    // difficulty it reaches (S:1314-1333).
    int repair = 0;

    for (const Character &member : party.members())
    {
        if (!out(member) && conscious(member) && !member.conditions.test(size_t(CharacterCondition::Paralyzed))
            && !member.conditions.test(size_t(CharacterCondition::Asleep)))
        {
            repair = std::max(repair, skillLevel(member, "RepairItem") * int(skillMastery(member, "RepairItem")));
        }
    }

    bool repaired = false;

    for (size_t index = 0; index < party.members().size() && repair > 0 && party.itemTable() != nullptr; ++index)
    {
        Character &member = *party.member(index);
        const auto mend = [&](uint32_t itemId, bool &broken)
        {
            const ItemDefinition *pItem = itemId != 0 ? party.itemTable()->get(itemId) : nullptr;

            if (broken && pItem != nullptr && pItem->identifyRepairDifficulty <= repair)
            {
                broken = false;
                repaired = true;
            }
        };

        for (InventoryItem &item : member.inventory)
        {
            mend(item.objectDescriptionId, item.broken);
        }

        CharacterEquipment &worn = member.equipment;
        CharacterEquipmentRuntimeState &states = member.equipmentRuntime;
        mend(worn.offHand, states.offHand.broken);
        mend(worn.mainHand, states.mainHand.broken);
        mend(worn.bow, states.bow.broken);
        mend(worn.armor, states.armor.broken);
        mend(worn.helm, states.helm.broken);
        mend(worn.belt, states.belt.broken);
        mend(worn.cloak, states.cloak.broken);
        mend(worn.gauntlets, states.gauntlets.broken);
        mend(worn.boots, states.boots.broken);
        mend(worn.amulet, states.amulet.broken);
        mend(worn.ring1, states.ring1.broken);
        mend(worn.ring2, states.ring2.broken);
        mend(worn.ring3, states.ring3.broken);
        mend(worn.ring4, states.ring4.broken);
        mend(worn.ring5, states.ring5.broken);
        mend(worn.ring6, states.ring6.broken);
    }

    if (repaired && world.eventRuntimeState() != nullptr)
    {
        world.eventRuntimeState()->statusMessages.push_back(Engine::tr("Repaired"));
    }

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        const Character &wearer = party.members()[index];

        if (out(wearer))
        {
            continue;
        }

        const std::string &className = wearer.className.empty() ? wearer.role : wearer.className;

        // The Lich class alone, not the Death Knights' Lich King (artifactDrain ExemptClass, ITM-A8).
        if (canonicalClassName(className) != "Lich")
        {
            party.adjustMemberHealth(index, -3 * mawWornItemCount(wearer, {1317}));
        }

        // Each worn HP regeneration special (37, 44, 50, 54) gives about 1 % of full HP, each SP one (38, 47, 55) 1 %
        // of full SP, on top of the continuous regeneration (zzMaw-Stats.lua:670-689, FCOR-2-60).
        const auto tickShare = [](int count, int full)
        {
            return int(mawRound(count * std::max(full * 0.01 - 1, 0.0)));
        };
        const int fullHealth = Party::effectiveMaximumHealth(wearer);
        const int fullMana = Party::effectiveMaximumSpellPoints(wearer);
        Character &regenerating = *party.member(index);
        regenerating.health = std::max(regenerating.health, std::min(fullHealth,
            regenerating.health + tickShare(mawWornSpecialCount(wearer, {37, 44, 50, 54}), fullHealth)));
        regenerating.spellPoints = std::max(regenerating.spellPoints, std::min(fullMana,
            regenerating.spellPoints + tickShare(mawWornSpecialCount(wearer, {38, 47, 55}), fullMana)));

        // Each Cycle of Life ring shares once; a lone wearer has no one to share with.
        for (int ring = mawWornItemCount(wearer, {543}); ring > 0 && party.members().size() > 1; --ring)
        {
            if (wearer.health >= Party::effectiveMaximumHealth(wearer))
            {
                break;
            }

            int pool = wearer.health;
            int count = 1;

            for (const Character &donor : party.members())
            {
                if (donor.health > wearer.health && !out(donor))
                {
                    pool += donor.health;
                    ++count;
                }
            }

            const int middle = int(std::floor(double(pool) / count));
            const int need = middle - wearer.health;
            const int wearerHealth = wearer.health;
            int gained = 0;

            for (size_t donorIndex = 0; donorIndex < party.members().size(); ++donorIndex)
            {
                const Character &donor = party.members()[donorIndex];

                if (donor.health > wearerHealth && !out(donor))
                {
                    const int given = std::min(std::max(donor.health - middle, 0), need) / 2;
                    party.adjustMemberHealth(donorIndex, -given);
                    gained += given;
                }
            }

            // Back above 0 HP the wearer wakes.
            party.adjustMemberHealth(index, gained);
        }
    }
}

void MawCombatRules::updateCombat(Party &party, IGameplayWorldRuntime &world, float deltaSeconds) const
{
    m_gameMinutes = world.gameMinutes();
    updateArtifacts(party, world);
    int nearbyMonsters = 0;

    for (size_t actorIndex = 0; actorIndex < world.mapActorCount(); ++actorIndex)
    {
        GameplayActorRulesView state;

        if (world.actorRulesView(actorIndex, state) && !state.isDead && state.hostileToParty
            && std::hypot(state.preciseX - world.partyX(), state.preciseY - world.partyY()) - state.radius <= 512)
        {
            ++nearbyMonsters;
        }
    }

    m_rules.setNearbyMonsters(nearbyMonsters);
    EventRuntimeState *pRuntimeState = world.eventRuntimeState();

    // Real-time poison, once a second.
    m_poisonSeconds += deltaSeconds;

    for (; m_poisonSeconds >= 1.0f; m_poisonSeconds -= 1.0f)
    {
        const MawModelConfig config = mawModelConfig(m_rules.options(), int(party.members().size()));
        double multiplier = mawBolsterAmount(m_rules.options()) / 100.0 * (config.insanityMode ? 2 : 1);
        multiplier /= party.members().size() == 1 ? 2 : 1;

        for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
        {
            Character &member = *party.member(memberIndex);
            float &seconds = member.rulesetState.poisonSeconds;
            const auto has = [&member](CharacterCondition condition)
            {
                return member.conditions.test(size_t(condition));
            };
            // The strongest poison and the share of full HP it takes.
            std::optional<std::pair<CharacterCondition, double>> poison;

            for (const auto &[condition, share] : {std::pair(CharacterCondition::PoisonWeak, 0.0025),
                     std::pair(CharacterCondition::PoisonMedium, 0.005),
                     std::pair(CharacterCondition::PoisonSevere, 0.01)})
            {
                poison = has(condition) ? std::optional(std::pair(condition, share)) : poison;
            }

            if (member.health < 1)
            {
                continue;
            }

            if (!poison)
            {
                seconds = 0;
                continue;
            }

            seconds = seconds <= 0 ? 20 : seconds;
            seconds -= 1;

            if (seconds <= 0)
            {
                seconds = 0;
                member.conditions.reset(size_t(poison->first));

                if (pRuntimeState != nullptr)
                {
                    pRuntimeState->statusMessages.push_back(
                        Engine::tr("{name}'s poison effect expired", {{"name", member.name}}));
                }

                continue;
            }

            const double loss = std::ceil(Party::effectiveMaximumHealth(member) * poison->second) * multiplier;
            member.health = std::max(1, member.health - int(mawRound(loss)));
        }
    }

    // Road to Insanity and Beyond Madness: Invisibility ends while an enemy is in melee range (the detector is red,
    // SP:3849-3857).
    if (mawModelConfig(m_rules.options(), int(party.members().size())).insanityMode
        && party.hasPartyBuff(PartyBuffId::Invisibility) && partyHasRedAlert(world))
    {
        party.clearPartyBuff(PartyBuffId::Invisibility);
    }

    // Road to Insanity and Beyond Madness, with the preference on: a member left below minus ten times their full HP
    // is dismissed, while someone else remains (DM:1923-1932). The leader cannot be dismissed and stays eradicated.
    if (mawModelConfig(m_rules.options(), int(party.members().size())).insanityMode
        && m_rules.options().preferences.disintegration)
    {
        for (size_t memberIndex = party.members().size(); memberIndex-- > 1;)
        {
            if (party.member(memberIndex)->health < -10 * deathThreshold(*party.member(memberIndex))
                && party.dismissMemberToAdventurersInn(memberIndex))
            {
                m_statusMessages.push_back(Engine::tr("Disintegrated"));
            }
        }
    }

    if (pRuntimeState != nullptr)
    {
        for (std::string &message : m_statusMessages)
        {
            pRuntimeState->statusMessages.push_back(std::move(message));
        }
    }

    m_statusMessages.clear();

    for (const Character &member : party.members())
    {
        CharacterRulesRuntime &state = member.rulesetState.runtime;
        state.retaliationSeconds = std::max(0.0f, state.retaliationSeconds - deltaSeconds);

        if (state.retaliationSeconds <= 0)
        {
            state.retaliationStacks = 0;
        }
    }
}

void MawCombatRules::characterConditionApplied(Party &party, size_t memberIndex, CharacterCondition condition) const
{
    Character *pMember = party.member(memberIndex);

    if (pMember == nullptr
        || (condition != CharacterCondition::PoisonWeak && condition != CharacterCondition::PoisonMedium
            && condition != CharacterCondition::PoisonSevere))
    {
        return;
    }

    float &seconds = pMember->rulesetState.poisonSeconds;
    seconds = seconds <= 0 ? 25 : std::min(seconds + 5, 50.0f);
}

std::optional<size_t> MawCombatRules::monsterAttackTarget(const Party &party, const ActorRulesetFacts &attacker) const
{
    if (!hasAffix(attacker, MawBossAffix::Fixator))
    {
        return std::nullopt;
    }

    // A Fixator always goes for the conscious member with the lowest maximum HP.
    std::optional<size_t> target;
    int lowestMaxHp = 0;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const Character &member = party.members()[memberIndex];

        if (conscious(member) && (!target || member.maxHealth < lowestMaxHp))
        {
            target = memberIndex;
            lowestMaxHp = member.maxHealth;
        }
    }

    return target;
}

bool MawCombatRules::piercesConditionSave(const Party &) const
{
    static thread_local std::mt19937 rng(std::random_device{}());
    const std::optional<double> chance = m_rules.mapAffix(MawMapAffix::IgnoreStatusResistance);
    return chance && std::uniform_real_distribution<double>(0, 1)(rng) < *chance / 100;
}

bool MawCombatRules::harmsFriendlyActors() const
{
    return m_rules.options().preferences.friendlyFire;
}

float MawCombatRules::mistFormPhysicalShare() const
{
    return 0.25f;
}

std::optional<float> MawCombatRules::turnBasedWalkLimit() const
{
    const RulesetOptions &options = m_rules.options();

    if (mawBolsterAmount(options) >= 600 || options.challengeMode == RulesetChallengeMode::Austerity)
    {
        return 370.0f;
    }

    return std::nullopt;
}

CombatDamageType MawCombatRules::partySpellDamageType(uint32_t spellId, CombatDamageType tableType) const
{
    constexpr uint32_t Blades = 39;
    return spellId == Blades ? CombatDamageType::Physical : tableType;
}

bool MawCombatRules::immuneToMonsterSpecialAttacks(const Character &member) const
{
    return mawWearsLegendaryAffix(member, LegendaryStatusImmunity);
}

bool MawCombatRules::blocksMonsterCondition(const Party &party, CharacterCondition condition) const
{
    return condition == CharacterCondition::Unconscious && party.hasPartyBuff(PartyBuffId::ProtectionFromMagic);
}

void MawCombatRules::applyPartyHitEffects(Party &party, const PartyHitOnMonster &hit) const
{
    const Character *pMember = party.member(hit.memberIndex);

    if (hit.damage <= 0 || pMember == nullptr || hit.pTarget == nullptr)
    {
        return;
    }

    // A Grandmaster spear blow stacks more physical damage on its target until it dies (DM:546-583).
    if (hit.melee && hit.type == CombatDamageType::Physical && hit.pWorld != nullptr && hit.targetActorIndex
        && party.itemTable() != nullptr)
    {
        if (ActorRulesetFacts *pFacts = hit.pWorld->mutableActorRulesetFacts(*hit.targetActorIndex))
        {
            pFacts->spearDamageTaken += float(spearStack(m_rules, *pMember, *party.itemTable()));
        }
    }

    // A Regenerating boss counts the party's hits: it regenerates once hit, slower with each (Damage.lua:944-954,
    // FCOR-2-6).
    if (hasAffix(*hit.pTarget, MawBossAffix::Regenerating) && hit.pWorld != nullptr && hit.targetActorIndex)
    {
        if (ActorRulesetFacts *pFacts = hit.pWorld->mutableActorRulesetFacts(*hit.targetActorIndex))
        {
            pFacts->regeneratingHits = uint16_t(std::min(pFacts->regeneratingHits + 1, 65535));
        }
    }

    // A dragon's bite throws its target along the blow once Dragon Ability reaches Fangs: 800 × fang / level^0.75
    // falling to nothing over 60 × its root frames, about 400 × mult^1.5 units at 60 frames a second (DM:599-610, zzClasses:471-484).
    if (hit.melee && !hit.killed && mawIsDragon(*pMember) && hit.pWorld != nullptr && hit.targetActorIndex
        && hit.pTarget->level > 0)
    {
        const int fang = skillLevel(*pMember, "Unarmed");
        GameplayRuntimeActorState target = {};

        if (fang > 0 && skillLevel(*pMember, "DragonAbility") >= fang
            && hit.pWorld->actorRuntimeState(*hit.targetActorIndex, target))
        {
            const float deltaX = target.preciseX - hit.pWorld->partyX();
            const float deltaY = target.preciseY - hit.pWorld->partyY();
            const float length = std::hypot(deltaX, deltaY);

            if (length > 0.01f)
            {
                hit.pWorld->pushActor(*hit.targetActorIndex, deltaX / length, deltaY / length,
                    float(mawDragonPushDistance(fang, hit.pTarget->level)));
            }
        }
    }

    // The Doom modes, indoors: a struck monster wakes the ones within 256 units and shows them on the map (DM:217-230).
    if (hit.pWorld != nullptr && hit.targetActorIndex && !hit.pWorld->isOpenAirMap()
        && mawModelConfig(m_rules.options(), int(party.members().size())).doomMode)
    {
        hit.pWorld->revealActorsAround(*hit.targetActorIndex, 256.0f);
    }

    // Legendary 29: every attack makes the target take 1 % more damage until it dies; an area spell's only 40 % of the
    // time (DM:569-577).
    if (mawWearsLegendaryAffix(*pMember, LegendaryDamageTaken) && hit.pWorld != nullptr && hit.targetActorIndex
        && (!isAreaSpell(hit.spellId) || unitDraw(m_legendaryRng) < 0.4))
    {
        if (ActorRulesetFacts *pFacts = hit.pWorld->mutableActorRulesetFacts(*hit.targetActorIndex))
        {
            pFacts->legendaryDamageTaken += 1;
        }
    }

    // Snake and Finality cast Slow on the monster they strike, at the wielder's Sword skill (zzzMaw_Artifacts.lua:124-138).
    if (hit.melee && hit.pWorld != nullptr && hit.targetActorIndex && party.itemTable() != nullptr)
    {
        for (const HeldWeapon &weapon : heldWeapons(*pMember, *party.itemTable(), true, false))
        {
            const MawArtifact *pArtifact = m_rules.itemData().artifact(weapon.pItem->itemId);

            if (pArtifact == nullptr || !pArtifact->onHitSlow)
            {
                continue;
            }

            CrowdControlCast slow;
            slow.spellId = 35;
            slow.mastery = skillMastery(*pMember, "Sword");
            slow.skillLevel = uint32_t(skillLevel(*pMember, "Sword"));
            slow.pCaster = pMember;
            slow.targetLevel = hit.pTarget->level;
            slow.boss = hit.pTarget->bossAffix != 0;
            slow.pTargetFacts = hit.pTarget;
            slow.targetKey = mapActorKey(hit.pWorld->mapName(), *hit.targetActorIndex);
            slow.partySize = party.members().size();
            slow.nowSeconds = double(hit.pWorld->gameMinutes()) * 2.0;

            if (const std::optional<float> seconds = m_rules.gameRules().spells.crowdControlSeconds(slow);
                seconds && *seconds > 0)
            {
                hit.pWorld->debuffActor(*hit.targetActorIndex, GameplayActorHitDebuff::Slow, *seconds, 2.0f);
            }

            break;
        }
    }

    // Splitter, Thor, Percival and Hades cast a spell on the monster they strike, at the wielder's skill in the
    // weapon; Thor only when it survives (zzzMaw_Artifacts.lua:52-64, 175-271). A broken one casts nothing.
    if (hit.pWorld != nullptr && hit.targetActorIndex && hit.spellId == 0 && party.itemTable() != nullptr)
    {
        for (const HeldWeapon &weapon : heldWeapons(*pMember, *party.itemTable(), hit.melee, !hit.melee))
        {
            const uint32_t itemId = weapon.pItem->itemId;
            // Fireball, Lightning Bolt, Acid Burst.
            const uint32_t spellId = itemId == 1308 || itemId == 2025 ? 6
                : itemId == 2021                                    ? 18
                : itemId == 2035                                    ? 29
                                                                    : 0;

            if (spellId == 0 || (itemId == 2021 && hit.killed))
            {
                continue;
            }

            const std::string skill = canonicalSkillName(weapon.pItem->skillGroup);
            m_artifactCasts.push_back(ArtifactCast{hit.memberIndex, spellId, uint32_t(skillLevel(*pMember, skill)),
                skillMastery(*pMember, skill), *hit.targetActorIndex});

            // Thor also throws the monster back, as a dragon's bite does with the weapon skill for the fang
            // (knockBack, zzzMaw_Artifacts.lua:66-85).
            GameplayRuntimeActorState target = {};

            if (itemId == 2021 && hit.pTarget != nullptr && hit.pTarget->level > 0
                && hit.pWorld->actorRuntimeState(*hit.targetActorIndex, target))
            {
                const float deltaX = target.preciseX - hit.pWorld->partyX();
                const float deltaY = target.preciseY - hit.pWorld->partyY();
                const float length = std::hypot(deltaX, deltaY);

                if (length > 0.01f)
                {
                    hit.pWorld->pushActor(*hit.targetActorIndex, deltaX / length, deltaY / length,
                        float(mawDragonPushDistance(skillLevel(*pMember, skill), hit.pTarget->level)));
                }
            }
        }
    }

    if (hit.killed)
    {
        Character &killer = *party.member(hit.memberIndex);

        // Legendary 24: a kill restores 10 % of the HP pool and 5 % of the SP pool left after the auras reserve
        // theirs (DM:1083-1097, GetMaxHP / getMaxMana).
        if (mawWearsLegendaryAffix(killer, LegendaryKillRestore))
        {
            const MawSpellRules &spells = m_rules.spellRules();
            const int healthPool = std::max(
                0, Party::effectiveMaximumHealth(killer) - spells.reservedHitPoints(party, hit.memberIndex));
            const int manaPool = std::max(
                0, Party::effectiveMaximumSpellPoints(killer) - spells.reservedSpellPoints(party, hit.memberIndex));
            party.healMember(hit.memberIndex, int(healthPool * 0.10));
            killer.spellPoints = std::min(manaPool, killer.spellPoints + int(manaPool * 0.05));
        }

        // Legendary 11: a kill by a single-target spell halves the recovery the cast set (DM:1099-1116); a blow's
        // is halved before it is applied (killRecoveryScale, CMB-2).
        if (mawWearsLegendaryAffix(killer, LegendaryKillRecovery) && !hit.melee && hit.spellId != 0
            && !isAreaSpell(hit.spellId))
        {
            killer.recoverySecondsRemaining /= 2;
        }
    }

    // From Hard up, and in Austerity, a blow ends Fly: its time goes to Feather Fall, except on the maps made for
    // flying (DM:317-329).
    const PartyBuffState *pFly = party.partyBuff(PartyBuffId::Fly);

    if (pFly != nullptr && pFly->active() && mawAttackingEndsFly(m_rules.options(), m_rules.currentMap()))
    {
        const PartyBuffState fly = *pFly;
        party.clearPartyBuff(PartyBuffId::Fly);
        party.applyPartyBuff(PartyBuffId::FeatherFall, fly.remainingSeconds, fly.power,
            spellIdValue(SpellId::FeatherFall), fly.skillLevel, fly.skillMastery, fly.casterMemberIndex);
    }

    const bool physical = hit.type == CombatDamageType::Physical;
    const bool reflected = (physical && hasAffix(*hit.pTarget, MawBossAffix::Thorn))
        || (!physical && hasAffix(*hit.pTarget, MawBossAffix::Reflecting));
    const auto reflect = [&](int amount)
    {
        const int returned = reflectedDamage(party, hit.memberIndex, amount, hit.type);

        if (returned > 0)
        {
            party.applyDamageToMember(hit.memberIndex, returned, "");
        }
    };

    if (reflected)
    {
        reflect(hit.damage);
    }

    // A dimension map reflects its share of the hit (MAW returns 100 - X %; DEVIATIONS.md).
    if (const std::optional<double> share =
            m_rules.mapAffix(physical ? MawMapAffix::ReflectPhysical : MawMapAffix::ReflectMagic))
    {
        reflect(int(mawRound(hit.damage * *share / 100)));
    }

    if (!conscious(*party.member(hit.memberIndex)))
    {
        return;
    }

    applyClassHitEffects(party, hit);
    applyLeech(party, hit);
}

double MawCombatRules::leechBarShare(const Party &party, const PartyHitOnMonster &hit) const
{
    // Dealing a B-tier monster of the family its whole HP is worth the attacker's whole HP; overkill is left out.
    const Character &member = party.members()[hit.memberIndex];
    MawBalanceModel &model = m_rules.model(int(std::max<size_t>(1, party.members().size())));
    const double referenceHealth = std::max(1.0,
        model.monsterHealth(hit.pTarget->familyLevel > 0 ? hit.pTarget->familyLevel : hit.pTarget->level));
    const double counted = hit.pTarget->maxHp > 0 ? std::min(hit.damage, hit.pTarget->maxHp) : hit.damage;
    return counted / referenceHealth * Party::effectiveMaximumHealth(member);
}

std::optional<int> MawCombatRules::spellRecoveryTicks(
    const Party &party,
    const Character &caster,
    uint32_t spellId) const
{
    const SpellEntry *pSpell = m_rules.spellTable() != nullptr ? m_rules.spellTable()->findById(int(spellId)) : nullptr;
    const std::optional<std::string> school = resolveMagicSkillName(spellId);

    if (pSpell == nullptr || !school)
    {
        return std::nullopt;
    }

    const CharacterSkill *pSkill = caster.findSkill(*school);
    CharacterSpellCast cast;
    cast.pCaster = &caster;
    cast.pItemTable = party.itemTable();
    cast.pStandardItemEnchantTable = party.standardItemEnchantTable();
    cast.pSpecialItemEnchantTable = party.specialItemEnchantTable();
    cast.pSpell = pSpell;
    cast.mastery = pSkill != nullptr ? pSkill->mastery : SkillMastery::Normal;
    cast.skillLevel = uint32_t(skillLevel(caster, *school));
    cast.partyCount = int(party.members().size());
    return m_rules.gameRules().spells.recoveryTicks(cast, spellNumbersAtMastery(*pSpell, cast.mastery).recoveryTicks);
}

void MawCombatRules::applyLeech(Party &party, const PartyHitOnMonster &hit) const
{
    Character &member = *party.member(hit.memberIndex);
    const MawLeech leech = mawLeech(m_rules, member, party.itemTable());
    const bool spell = hit.spellId > 0 && hit.spellId < 132;
    double share = hit.melee ? leech.melee : spell ? leech.spell : leech.ranged;
    // The vampires' Lifedrain and Souldrinker (objects 200 and 201) heal a tenth of the bar share on top; a Dark mage's
    // Souldrinker has only the spell leech (DM:1262-1270, CMB-22).
    constexpr uint32_t VampireRace = 1;
    const bool drainSpell = hit.spellId == 111 || (hit.spellId == 99 && member.raceId == VampireRace);

    // A dragon's Regeneration adds to its bite's leech: skill / the expected skill at the monster's level x 5 %
    // (S:1494-1501).
    if (hit.melee && mawIsDragon(member))
    {
        MawBalanceModel &model = m_rules.model(int(std::max<size_t>(1, party.members().size())));
        share += skillLevel(member, "Regeneration") / std::max(1.0, model.skill(hit.pTarget->level)) * 0.05;
    }

    if ((share == 0 && leech.spell == 0 && !drainSpell) || hit.pTarget->level <= 0 || party.itemTable() == nullptr)
    {
        return;
    }

    // The heal is the share of the attacker's maximum HP the hit took of a B-tier monster of the family, overkill
    // left out; a weapon's enchantment and aura damage leeches at the spell rate. A positive heal is at least a fifth
    // of the share per 100 recovery of the attack or spell (DM:1207-1326).
    const double full = Party::effectiveMaximumHealth(member);
    const double bar = leechBarShare(party, hit);
    const double counted = hit.pTarget->maxHp > 0 ? std::min(hit.damage, hit.pTarget->maxHp) : hit.damage;
    const double elementalShare = counted > 0 ? std::min<double>(hit.elementalDamage, counted) / counted : 0;
    double heal = spell ? bar * share : bar * (1 - elementalShare) * share + bar * elementalShare * leech.spell;
    heal += drainSpell ? bar * 0.1 : 0;
    double floor = 0;

    if (!spell)
    {
        // The full Speed, items' and permanent bonuses included, as GetAttackDelay reads it (CMB-13).
        const MawAttackDelay delay = mawCharacterAttackDelay(m_rules, member, *party.itemTable(),
            hit.melee ? CharacterAttackMode::Melee : CharacterAttackMode::Bow,
            characterSheet(member, party.itemTable(), party.standardItemEnchantTable(),
                party.specialItemEnchantTable())
                .speed.actual,
            m_rules.auraSkill(5, &member));
        floor = full * share / 5 * delay.delay / 100;
    }
    else if (const std::optional<int> recovery = spellRecoveryTicks(party, member, hit.spellId))
    {
        // An area spell's floor is less: / 2.5, and / 4 for Fire Spike, Meteor Shower and Starburst.
        floor = full * share / 5 * *recovery / 100;
        floor /= isAreaSpell(hit.spellId) ? 2.5 : 1;
        floor /= hit.spellId == 9 || hit.spellId == 22 || hit.spellId == 43 ? 4 : 1;
    }

    // A dimension map's weaker leech cuts the heal before the floor, which it leaves whole (DM:1229-1230, CMB-15).
    heal *= 1 - m_rules.mapAffix(MawMapAffix::Leech).value_or(0) / 100;

    if (share > 0)
    {
        heal = std::max(heal, floor);
    }

    if (heal > 0)
    {

        // Legendary 31: half goes to mana, by the same share of the SP bar, half to HP (DM:1222-1228, 1300-1309).
        if (mawWearsLegendaryAffix(member, LegendaryManaLeech))
        {
            heal /= 2;
            const int fullMana = Party::effectiveMaximumSpellPoints(member);
            member.spellPoints = std::min(fullMana, member.spellPoints + int(std::ceil(heal / full * fullMana)));
        }

        // Legendary 27: what overheals goes to the member with the lowest share of HP, an unconscious one too; only
        // the dead and eradicated are passed over (DM:1310-1318, pickLowestPartyMember).
        const int overheal = member.health + int(std::ceil(heal)) - int(full);
        party.healMember(hit.memberIndex, int(std::ceil(heal)));

        if (overheal > 0 && mawWearsLegendaryAffix(member, LegendaryOverheal))
        {
            std::optional<size_t> lowest;
            double lowestShare = 0;

            for (size_t index = 0; index < party.members().size(); ++index)
            {
                const Character &candidate = party.members()[index];
                const double candidateShare =
                    double(candidate.health) / std::max(1, Party::effectiveMaximumHealth(candidate));

                if (!candidate.conditions.test(size_t(CharacterCondition::Dead))
                    && !candidate.conditions.test(size_t(CharacterCondition::Eradicated))
                    && (!lowest || candidateShare < lowestShare))
                {
                    lowest = index;
                    lowestShare = candidateShare;
                }
            }

            if (lowest)
            {
                party.healMember(*lowest, overheal);
            }
        }
    }
    else if (heal < 0)
    {
        party.applyDamageToMember(hit.memberIndex, int(std::ceil(-heal)), "");
    }
}

void MawCombatRules::applyClassHitEffects(Party &party, const PartyHitOnMonster &hit) const
{
    Character &member = *party.member(hit.memberIndex);
    const std::string line = mawClassLine(member.className);
    // The perks read the trained level (CLS-2).
    const auto school = [&member](const char *pSkill)
    {
        const CharacterSkill *pSkillState = member.findSkill(pSkill);
        return std::pair<double, int>(pSkillState != nullptr ? double(pSkillState->level) : 0.0,
            pSkillState != nullptr ? std::min(int(pSkillState->mastery), 4) : 0);
    };
    const auto addSpellPoints = [&party, &member, &hit, this](double amount)
    {
        const int maximum = member.maxSpellPoints + member.permanentBonuses.maxSpellPoints
            + member.magicalBonuses.maxSpellPoints
            - m_rules.gameRules().spells.reservedSpellPoints(party, hit.memberIndex);
        member.spellPoints = std::max(member.spellPoints, std::min(maximum, member.spellPoints + int(amount)));
    };

    const bool meleeBlow = hit.melee && hit.type == CombatDamageType::Physical;
    const bool arrow = !hit.melee && hit.spellId == 0;

    if (line == "assassin" && (meleeBlow || arrow))
    {
        applyAssassinHit(party, hit, arrow);
        return;
    }

    // An Assassin's class spell costs and builds nothing, but its kill pays as a blow's does (MCC:376-395, CLS-3).
    if (line == "assassin" && hit.spellId != 0 && hit.killed && mawClassSpell(member.className, hit.spellId) != nullptr)
    {
        rewardAssassinKill(member);
        return;
    }

    if (line == "elementalist")
    {
        // Their own spells teach them their schools; a weapon hit spends the stacks (DM:152-209).
        if (meleeBlow || arrow)
        {
            m_rules.classRuntime(member).elementalStacks = 0;
        }
        // Any spell of the four elements that lands on a hostile monster teaches, not only the offensive ones; a
        // friendly one teaches nothing (Damage.lua:156-196, FCOR-2-5).
        else if (hit.spellId >= 1 && hit.spellId <= 44 && targetHostile(hit))
        {
            const bool insanity = m_rules.options().challengeMode == RulesetChallengeMode::RoadToInsanity
                || m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
            member.rulesetState.elementalProgress[size_t((hit.spellId - 1) / 11)] += mawElementalistProgress(
                hit.spellId, hit.pTarget->level, int(party.members().size()), insanity);
        }

        return;
    }

    if (line == "death_knight" && hit.spellId != 0)
    {
        // Death Coil heals a fifth of the share of the bar its damage took (as leech does), 30 % from Unholy Master;
        // Asphyxiate holds the target four seconds (DM:808-814, 1285-1293).
        if (hit.spellId == 90)
        {
            const double share = school("DarkMagic").second >= 3 ? 0.3 : 0.2;
            party.healMember(hit.memberIndex, int(std::ceil(leechBarShare(party, hit) * share)));
        }
        else if (hit.spellId == 76 && hit.pWorld != nullptr && hit.targetActorIndex
            && !mawIgnoresCrowdControl(*hit.pTarget))
        {
            hit.pWorld->stunActor(*hit.targetActorIndex, hit.pTarget->bossAffix != 0 ? 2.0f : 4.0f);
        }
        else if (hit.spellId == 26 && hit.pWorld != nullptr && hit.targetActorIndex)
        {
            // Icy Touch slows the target for one game minute from Frost Expert, twice as much at Grandmaster
            // (DM:793-806).
            const int mastery = school("WaterMagic").second;

            if (mastery >= 2 && !mawIgnoresCrowdControl(*hit.pTarget))
            {
                hit.pWorld->debuffActor(
                    *hit.targetActorIndex, GameplayActorHitDebuff::Slow, 2.0f, mastery >= 4 ? 4.0f : 2.0f);
            }
        }

        return;
    }

    // A Death Knight's SP, Blood Leech and Death Grasp run on every physical hit, arrows too (DM:744-789, CLS-8).
    const bool deathKnightArrow = line == "death_knight" && arrow && hit.type == CombatDamageType::Physical;

    if (!meleeBlow && !deathKnightArrow)
    {
        return;
    }

    if (line == "seraphim")
    {
        // Body heals the member with the lowest share of HP (DM:106-150).
        const int heal = mawSeraphBodyHeal(m_rules, member, party);

        if (heal <= 0)
        {
            return;
        }

        std::optional<size_t> lowest;
        double lowestShare = 0;

        for (size_t index = 0; index < party.members().size(); ++index)
        {
            const Character &candidate = party.members()[index];
            const int maximum = std::max(1, candidate.maxHealth + candidate.permanentBonuses.maxHealth
                + candidate.magicalBonuses.maxHealth);
            const double candidateShare = double(candidate.health) / maximum;

            if (!candidate.conditions.test(size_t(CharacterCondition::Dead))
                && !candidate.conditions.test(size_t(CharacterCondition::Eradicated))
                && (!lowest || candidateShare < lowestShare))
            {
                lowest = index;
                lowestShare = candidateShare;
            }
        }

        if (lowest)
        {
            party.healMember(*lowest, heal);
            Character &healed = *party.member(*lowest);

            if (healed.health > 0)
            {
                healed.conditions.reset(size_t(CharacterCondition::Unconscious));
            }
        }
    }
    else if (line == "shaman")
    {
        // Mind returns spell points, Body hit points (DM:673-693).
        if (const double spellPoints = mawShamanMindSpellPoints(member); spellPoints > 0)
        {
            addSpellPoints(spellPoints);
        }

        if (const int heal = mawShamanBodyHeal(member); heal > 0)
        {
            party.healMember(hit.memberIndex, heal);
        }
    }
    else if (line == "dragon" && mawIsDragon(member))
    {
        // A dragon's bite refills its fixed pool: 10 SP a hit, 20 for a Great Wyrm; the bite needs the race, the pool
        // the class (DM:599-627).
        addSpellPoints(canonicalClassName(member.className) == "GreatWyrm" ? 20 : 10);
    }
    else if (line == "death_knight")
    {
        // 10, 15 or 20 SP a hit by promotion, half again for a killing blow (MCC:17-21).
        const std::string className = canonicalClassName(member.className);
        const double perHit = className == "LichKing" ? 20 : className == "DeathLord" ? 15 : 10;
        addSpellPoints(perHit * (hit.killed ? 1.5 : 1));

        // Blood Leech heals max(FullHP^0.5 s^1.5 / 70 (1 + m/4), 2s) a hit for 6 SP, the Superior one twice that for
        // 12, the cost not checked against the pool (DM:743-768).
        const bool superior = member.rulesetState.classToggleOn(74);

        if (superior || member.rulesetState.classToggleOn(68))
        {
            const auto [blood, mastery] = school("BodyMagic");
            const double full = member.maxHealth + member.permanentBonuses.maxHealth + member.magicalBonuses.maxHealth;
            const double heal =
                std::max(std::sqrt(full) * std::pow(blood, 1.5) / 70 * (1 + mastery / 4.0), 2 * blood);
            member.spellPoints = std::max(0, member.spellPoints - (superior ? 12 : 6));
            party.healMember(hit.memberIndex, int(mawRound(heal * (superior ? 2 : 1))));
        }

        // Death Grasp spends 15 SP a hit while the pool has them to hold the target in Dark Grasp for one game
        // minute, refreshed on every hit (DM:770-779).
        constexpr int GraspCost = 15;

        if (member.rulesetState.classToggleOn(96) && member.spellPoints >= GraspCost && hit.pWorld != nullptr
            && hit.targetActorIndex && !mawIgnoresCrowdControl(*hit.pTarget)
            && hit.pWorld->debuffActor(*hit.targetActorIndex, GameplayActorHitDebuff::DarkGrasp, 2.0f, 1.0f))
        {
            member.spellPoints -= GraspCost;
        }
    }
}

void MawCombatRules::applyAssassinHit(Party &party, const PartyHitOnMonster &hit, bool arrow) const
{
    // A blow costs 50 - 5 x Combat mastery energy (arrows half) and may refund 15; a paid blow builds a combo point
    // and a Subtlety speed stack (arrows half of each); a kill refunds (1 + Subtlety mastery) x 5 energy and adds a
    // combo point (MCC:365-432).
    Character &member = *party.member(hit.memberIndex);
    MawClassRuntime &runtime = m_rules.classRuntime(member);
    const int combat = int(skillMastery(member, "FireMagic"));
    const double share = arrow ? 0.5 : 1;
    const int cost = int((50 - 5 * combat) * share);
    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    const int maximum =
        member.maxSpellPoints + member.permanentBonuses.maxSpellPoints + member.magicalBonuses.maxSpellPoints;

    // The 15-energy refund is rolled on every blow before the payment, so an Assassin without energy can regain it by
    // hitting (MCC:372-387, CLS-7).
    if (unit(rng) < (0.10 + 0.01 * skillLevel(member, "FireMagic")) * share)
    {
        member.spellPoints = std::min(maximum, member.spellPoints + 15);
    }

    // Only a blow on a hostile monster pays and builds (MCC:396, FCOR-2-21).
    if (member.spellPoints >= cost && targetHostile(hit))
    {
        member.spellPoints -= cost;
        runtime.comboPoints = std::min(5.0, runtime.comboPoints + share);
        runtime.subtletyStacks = std::min(5.0, runtime.subtletyStacks + share);
        // Four game minutes.
        runtime.subtletySeconds = 8;
    }

    if (hit.killed)
    {
        rewardAssassinKill(member);
    }
}

void MawCombatRules::rewardAssassinKill(Character &member) const
{
    const int maximum =
        member.maxSpellPoints + member.permanentBonuses.maxSpellPoints + member.magicalBonuses.maxSpellPoints;
    MawClassRuntime &runtime = m_rules.classRuntime(member);
    member.spellPoints = std::min(maximum, member.spellPoints + (1 + int(skillMastery(member, "AirMagic"))) * 5);
    runtime.comboPoints = std::min(5.0, runtime.comboPoints + 1);
}

void MawCombatRules::applyMonsterHitEffects(
    Party &party,
    IGameplayWorldRuntime *pWorld,
    size_t memberIndex,
    const ActorRulesetFacts &attacker,
    uint32_t attackerActorId,
    int appliedDamage,
    CombatDamageType type) const
{
    static thread_local std::mt19937 rng(std::random_device{}());
    const bool special = !immuneToMonsterSpecialAttacks(*party.combatant(memberIndex));
    std::optional<size_t> attackerIndex;
    GameplayRuntimeActorState attackerState = {};

    for (size_t actorIndex = 0; pWorld != nullptr && actorIndex < pWorld->mapActorCount(); ++actorIndex)
    {
        if (pWorld->actorRuntimeState(actorIndex, attackerState) && attackerState.actorId == attackerActorId)
        {
            attackerIndex = actorIndex;
            break;
        }
    }

    // An Omnipotent boss's hit does all of these (Damage.lua:1787-1825).
    // Every physical hit of a Summoner, and 40 % of the others, calls a weaker one of the family (75 % A, 25 % B).
    if (hasAffix(attacker, MawBossAffix::Summoner) && attackerIndex
        && (type == CombatDamageType::Physical || std::uniform_real_distribution<double>(0, 1)(rng) < 0.4))
    {
        summonBossFamilyMember(*pWorld, attackerState, rng);
    }

    if (hasAffix(attacker, MawBossAffix::Venomous) && special)
    {
        party.applyMemberCondition(memberIndex, CharacterCondition::PoisonSevere);
    }

    if (hasAffix(attacker, MawBossAffix::Plagueborn) && special)
    {
        party.applyMemberCondition(memberIndex, CharacterCondition::DiseaseSevere);
    }

    if (hasAffix(attacker, MawBossAffix::Fixator) && special)
    {
        party.applyMemberCondition(memberIndex, CharacterCondition::Weak);
    }

    if (hasAffix(attacker, MawBossAffix::Exploding))
    {
        // The halved-off share, split over every member, the target included.
        const int share = appliedDamage / int(std::max<size_t>(1, party.members().size()));

        for (size_t member = 0; member < party.members().size() && share > 0; ++member)
        {
            party.applyDamageToMember(member, share, "", true);
        }
    }

    // A Swapper trades places with the party; a Puller jumps the party at itself (evt.Jump: ZAngle 128 of a 2048-step
    // turn, speed 1000).
    if (hasAffix(attacker, MawBossAffix::Swapper) && attackerIndex)
    {
        pWorld->swapActorPlaces(*attackerIndex, std::nullopt);
        pWorld->actorRuntimeState(*attackerIndex, attackerState);
    }

    if (hasAffix(attacker, MawBossAffix::Puller) && attackerIndex)
    {
        constexpr float PullSpeed = 1000.0f;
        constexpr float PullElevation = 128.0f / 2048.0f * 2.0f * 3.14159265f;
        const float heading =
            std::atan2(attackerState.preciseY - pWorld->partyY(), attackerState.preciseX - pWorld->partyX());
        pWorld->launchParty(heading, PullSpeed * std::cos(PullElevation), PullSpeed * std::sin(PullElevation));
    }
}

bool MawCombatRules::deflectsPartyHit(IGameplayWorldRuntime &world, size_t actorIndex) const
{
    GameplayRuntimeActorState boss = {};

    if (!world.actorRuntimeState(actorIndex, boss) || !hasAffix(boss.rulesetFacts, MawBossAffix::Swapper))
    {
        return false;
    }

    // MAW swaps with every active monster on the map; ours are those in the party's engagement range.
    bool swapped = false;

    for (size_t otherIndex = 0; otherIndex < world.mapActorCount(); ++otherIndex)
    {
        GameplayRuntimeActorState other = {};

        if (otherIndex == actorIndex || !world.actorRuntimeState(otherIndex, other) || other.isDead
            || other.currentHp <= 0 || other.isInvisible || !other.hostileToParty || other.rulesetFacts.bossAffix != 0
            || std::hypot(other.preciseX - world.partyX(), other.preciseY - world.partyY())
                > world.partyEngagementRange())
        {
            continue;
        }

        swapped = world.swapActorPlaces(actorIndex, otherIndex) || swapped;
    }

    return swapped;
}

int MawCombatRules::deathThreshold(const Character &member) const
{
    // Legendary 30: the higher of full HP and full SP, times the Mana Shield efficiency, sets the threshold (MAW's
    // code, DM:1911-1916; user decision Q14).
    int fullHealth = Party::effectiveMaximumHealth(member);

    if (mawWearsLegendaryAffix(member, LegendaryManaThreshold))
    {
        const double efficiency = mawManaShieldEfficiency(skillLevel(member, "ManaShield"));
        fullHealth = int(std::max(fullHealth, Party::effectiveMaximumSpellPoints(member)) * efficiency);
    }

    return fullHealth;
}

void MawCombatRules::characterDamaged(Party &party, size_t memberIndex) const
{
    // Beyond Madness's death ledger: any hit that lands, a monster's, a trap's, a fall or burning, makes a load or quit
    // in the next minutes count as a death (Damage.lua:1568-1573, CHM-2).
    m_rules.markMadnessHit(m_gameMinutes);

    // From bolster 300 (Nightmare, the Doom family), any hit that takes a member below minus their full HP kills them
    // and empties their SP; below twice that it eradicates them (DM:1908-1925).
    Character *pMember = party.member(memberIndex);

    if (pMember == nullptr || mawBolsterAmount(m_rules.options()) < 300)
    {
        return;
    }

    const int fullHealth = deathThreshold(*pMember);

    if (pMember->health < -fullHealth)
    {
        party.applyMemberCondition(memberIndex, CharacterCondition::Dead);
        pMember->spellPoints = 0;
    }

    if (pMember->health < -2 * fullHealth)
    {
        party.applyMemberCondition(memberIndex, CharacterCondition::Eradicated);
    }
}

bool MawCombatRules::characterMissileHits(const CharacterMissileOnMonster &missile) const
{
    // A monster the ruleset did not size keeps the Standard roll.
    if (missile.targetFacts.level <= 0)
    {
        return CombatRules::characterMissileHits(missile);
    }

    std::uniform_real_distribution<double> unit(0.0, 1.0);
    return mawPartyHitChance(missile.attackBonus, missile.targetFacts.level,
               missile.pShooter != nullptr ? m_rules.blessHitSkill(*missile.pShooter) : m_rules.auraSkill(46),
               m_rules.model(missile.partyCount))
            >= unit(*missile.pRng)
        && !skilledTargetDodges(missile.targetFacts, *missile.pRng);
}

bool MawCombatRules::monsterAttackLands(const MonsterAttackOnCharacter &) const
{
    // Monster armour and level play no part: the Speed roll in characterEvades decides.
    return true;
}

bool MawCombatRules::characterEvades(const MonsterAttackOnCharacter &attack) const
{
    const Character &character = *attack.pCharacter;
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    const CharacterSheetSummary sheet = characterSheet(
        character, attack.pItemTable, attack.pStandardItemEnchantTable, attack.pSpecialItemEnchantTable);
    // A Skilled boss's attacks are never dodged: no Speed roll, no Dodging (MawRollDodge, zzMaw_MonsterHit.lua:16-18;
    // pstage_damageRecompute, DM:1673).
    const bool undodgeable =
        attack.pAttackerFacts != nullptr && hasAffix(*attack.pAttackerFacts, MawBossAffix::Skilled);
    const double chanceToBeHit = undodgeable
        ? 1
        : mawChanceToBeHit(sheet.speed.actual, std::max(1, attack.monsterLevel), m_rules.model(attack.partyCount));

    // The engine's hit roll comes first. An attack past it enters the damage pipeline, whose first stage marks Beyond
    // Madness's ledger before the Dodging and Speed rolls, so a dodged attack still counts (Damage.lua:1568-1573,
    // 1975-1987).
    if (!(chanceToBeHit >= unit(*attack.pRng)))
    {
        return true;
    }

    m_rules.markMadnessHit(m_gameMinutes);

    // Dragons cannot dodge: their Dodging is Scales (DM:1673-1675).
    const double dodge = mawIsDragon(character) || undodgeable
        ? 0
        : mawGrandmasterDodgeChance(
            skillLevel(character, "Dodging"), skillMastery(character, "Dodging") >= SkillMastery::Grandmaster);

    if (dodge >= unit(*attack.pRng))
    {
        return true;
    }

    // A missile that passes the engine's hit roll is rolled again in the pipeline (FMON-2-1).
    return monsterMissileRules(attack.missileToken).secondSpeedRoll && !(chanceToBeHit >= unit(*attack.pRng));
}
namespace
{
// The trained level and mastery (at most Grandmaster) of a class school, as the class perks read them (CLS-2).
std::pair<double, int> trainedSchool(const Character &character, const char *pSkill)
{
    const CharacterSkill *pSkillState = character.findSkill(pSkill);
    return {pSkillState != nullptr ? double(pSkillState->level) : 0.0,
        pSkillState != nullptr ? std::min(int(pSkillState->mastery), 4) : 0};
}
}

int mawSeraphBodyHeal(const MawRules &rules, const Character &seraph, const Party &party)
{
    const auto [body, mastery] = trainedSchool(seraph, "BodyMagic");

    if (body <= 0 || mastery <= 0 || party.itemTable() == nullptr)
    {
        return 0;
    }

    // The full Speed and Personality, items' and permanent bonuses included (DM:118-120, CMB-13).
    const CharacterSheetSummary sheet =
        characterSheet(seraph, party.itemTable(), party.standardItemEnchantTable(), party.specialItemEnchantTable());
    const MawAttackDelay delay = mawCharacterAttackDelay(rules, seraph, *party.itemTable(), CharacterAttackMode::Melee,
        sheet.speed.actual, rules.auraSkill(5, &seraph));
    return int(mawRound(
        std::pow(body, 1.3) * mastery * 2 * delay.damageMultiplier * (1 + sheet.personality.actual / 1000)));
}

double mawShamanMindSpellPoints(const Character &shaman)
{
    const double mind = trainedSchool(shaman, "MindMagic").first;
    return mind > 0 ? std::pow(mind, 1.25) : 0;
}

int mawShamanBodyHeal(const Character &shaman)
{
    const auto [body, mastery] = trainedSchool(shaman, "BodyMagic");

    if (body <= 0)
    {
        return 0;
    }

    const double full = shaman.maxHealth + shaman.permanentBonuses.maxHealth + shaman.magicalBonuses.maxHealth;
    return int(std::max(mawRound(std::sqrt(full) * std::pow(body, 1.5) / 70 * (0.5 + mastery / 2.0)), body));
}

double mawWeaponStunChance(
    MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    int targetLevel,
    int partyCount,
    double speedMultiplier)
{
    const ItemDefinition *pItem = character.equipment.mainHand != 0 && !character.equipmentRuntime.mainHand.broken
        ? itemTable.get(character.equipment.mainHand)
        : nullptr;
    const std::string skill = pItem != nullptr ? canonicalSkillName(pItem->skillGroup) : std::string();
    const double share = skill == "Mace" ? 0.15 : skill == "Staff" ? 0.10 : 0;

    if (share <= 0 || skillMastery(character, skill) < SkillMastery::Master)
    {
        return 0;
    }

    const double level = std::max(1, targetLevel);
    return skillLevel(character, skill) / std::max(1.0, rules.model(partyCount).skill(level)) * share
        * speedMultiplier / std::min(1 + level / 150, 3.0);
}

std::pair<double, double> mawRetaliationCoefficients(
    MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    int partyCount)
{
    CharacterAttackOnMonster context;
    context.pCharacter = &character;
    context.pItemTable = &itemTable;
    context.pStandardItemEnchantTable = pStandardItemEnchantTable;
    context.pSpecialItemEnchantTable = pSpecialItemEnchantTable;
    context.partyCount = partyCount;
    const auto [power, vitality] = powerAndVitality(rules, character, context);
    return {mawRound(std::pow(power, 0.25)), mawRound(std::pow(vitality, 0.25))};
}

std::optional<std::string> MawCombatRules::partyHitStatusText(const PartyHitStatus &status) const
{
    const SpellEntry *pSpell = status.spellId > 1 && status.spellId < 133 && m_rules.spellTable() != nullptr
        ? m_rules.spellTable()->findById(int(status.spellId))
        : nullptr;
    const bool spell = pSpell != nullptr;
    const std::string name = spell ? Engine::localize(pSpell->name, "spell") : status.attackerName;
    const std::string points = mawShortNumber(status.damage, true, 4);
    const std::string critical = status.critical ? "\f65516" + Engine::tr("(CRIT!)") + "\f00000" : "";

    if (spell && status.monstersHit >= 2)
    {
        return Engine::tr("{attacker} hits for a total of {damage} points!", {{"attacker", name}, {"damage", points}})
            + critical;
    }

    if (status.killed)
    {
        return Engine::tr("{attacker} inflicts {damage} points killing {target}!",
                   {{"attacker", name}, {"damage", points}, {"target", status.targetName}})
            + critical;
    }

    return Engine::tr(status.missile && !spell ? "{attacker} shoots {target} for {damage} points!"
                                               : "{attacker} hits {target} for {damage} points!",
               {{"attacker", name}, {"target", status.targetName}, {"damage", points}})
        + critical;
}
}
