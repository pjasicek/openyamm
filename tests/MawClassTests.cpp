#include "doctest/doctest.h"
#include "game/gameplay/GameMechanics.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawClassSpells.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawPromotions.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/SpellTable.h"
#include "game/ui/SpellbookUiLayout.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

// The class and race rules of devdocs/maw/CLASSES_SPELLS_SPEC.md §5-6.
namespace
{
Character member(const std::string &className, uint32_t level, uint32_t raceId = 0)
{
    Character character;
    character.name = className;
    character.className = className;
    character.level = level;
    character.raceId = raceId;
    return character;
}

ClassMultiplierEntry entry(const std::string &className, int baseHealth, int healthPerLevel, int baseMana,
    int manaPerLevel, ClassManaMode mode, uint32_t kind = 0, uint32_t step = 0)
{
    ClassMultiplierEntry result;
    result.className = className;
    result.baseHealth = baseHealth;
    result.healthPerLevel = healthPerLevel;
    result.baseMana = baseMana;
    result.manaPerLevel = manaPerLevel;
    result.manaMode = mode;
    result.classKind = kind;
    result.promotionStep = step;
    return result;
}
}

TEST_CASE("MAW classes take HP and SP from MAW's stat effects and Personality")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ClassRules &classes = rules.gameRules().classes;

    // Knight 10, Endurance 20 (E = 3), Bodybuilding 5 at Grandmaster (counts 5): 35 + 4 x (10 + 3 + 25).
    Character knight = member("Knight", 10);
    knight.endurance = 20;
    knight.skills["Bodybuilding"] = {"Bodybuilding", 5, SkillMastery::Grandmaster};
    const ClassMultiplierEntry knightEntry = entry("Knight", 35, 4, 0, 0, ClassManaMode::None, 6, 0);
    CHECK_EQ(classes.baseMaxHealth(knight, knightEntry).value_or(0), 35 + 4 * 38);
    CHECK_EQ(classes.baseMaxSpellPoints(knight, knightEntry).value_or(-1), 0);

    // Sorcerer 20, Intellect 50 (no SP in MAW), Personality 30 (E 6, counted twice: SPStats 2 and addMana); Meditation
    // 4 Expert adds nothing here, only to Enlightenment's base: 25 + 6 x (20 + 2 x 6) (CLS-1).
    Character sorcerer = member("ArchMage", 20);
    sorcerer.intellect = 50;
    sorcerer.personality = 30;
    sorcerer.skills["Meditation"] = {"Meditation", 4, SkillMastery::Expert};
    const ClassMultiplierEntry archMage = entry("ArchMage", 20, 4, 25, 6, ClassManaMode::Intellect, 14, 2);
    CHECK_EQ(classes.baseMaxSpellPoints(sorcerer, archMage).value_or(0), 25 + 6 * 32);

    // Two worlds' promotions make the final classes Elder (x1.25 per level), three Ultimate (x1.5).
    rules.setPromotionWorlds({{14, 2}});
    CHECK_EQ(classes.baseMaxHealth(sorcerer, archMage).value_or(0), 20 + int(5.0 * (20 + mawStatEffect(0))));
    rules.setPromotionWorlds({{14, 3}});
    CHECK_EQ(classes.baseMaxHealth(sorcerer, archMage).value_or(0), 20 + int(6.0 * (20 + mawStatEffect(0))));

    // The Elemental Adept's 2.5 HP per level is set in Lua into a byte, so it keeps 2 (CLS-5); the Dragon's pool of
    // 60 is set in Lua too.
    Character adept = member("ElementalAdept", 10);
    adept.endurance = 25;
    CHECK_EQ(classes.baseMaxHealth(adept, entry("ElementalAdept", 15, 2, 30, 6, ClassManaMode::Intellect, 20, 1))
                 .value_or(0),
        15 + 2 * 15);
    Character dragon = member("Dragon", 30, 5);
    CHECK_EQ(classes.baseMaxSpellPoints(dragon, entry("Dragon", 50, 5, 50, 0, ClassManaMode::Intellect, 4, 1))
                 .value_or(0),
        60);
    CHECK_FALSE(standardClassRules().baseMaxHealth(knight, knightEntry).has_value());

    // Death Knights take no SP from items, Assassins 10 per Assassination mastery.
    Character deathKnight = member("DeathKnight", 5);
    deathKnight.magicalBonuses.maxSpellPoints = 40;
    classes.applyClassBonuses(deathKnight);
    CHECK_EQ(deathKnight.magicalBonuses.maxSpellPoints, 0);
    Character assassin = member("Assassin", 5);
    assassin.skills["EarthMagic"] = {"EarthMagic", 10, SkillMastery::Master};
    assassin.magicalBonuses.maxSpellPoints = 40;
    classes.applyClassBonuses(assassin);
    CHECK_EQ(assassin.magicalBonuses.maxSpellPoints, 30);

    // A class without mana (Knight, Troll) keeps none: items and permanent SP cancel to a maximum of 0.
    ClassMultiplierTable classTable;
    REQUIRE(classTable.loadFromRows({{"Class", "BaseHP", "HPPerLevel", "BaseMana", "ManaPerLevel", "ManaStat"},
        {"Knight", "35", "5", "0", "0", "None"}, {"Troll", "45", "5", "0", "0", "None"}}));
    rules.setClassMultiplierTable(&classTable);

    for (const char *pClassName : {"Knight", "Troll"})
    {
        Character fighter = member(pClassName, 20);
        fighter.magicalBonuses.maxSpellPoints = 25;
        fighter.permanentBonuses.maxSpellPoints = 10;
        fighter.spellPoints = 35;
        classes.applyClassBonuses(fighter);
        CHECK_EQ(fighter.maxSpellPoints + fighter.permanentBonuses.maxSpellPoints
                + fighter.magicalBonuses.maxSpellPoints, 0);
        CHECK_EQ(fighter.spellPoints, 0);
    }

    rules.setClassMultiplierTable(nullptr);
}

TEST_CASE("MAW races add skill bonuses, resistances and skill limits")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ClassRules &classes = rules.gameRules().classes;

    // +3 and +1 per 10 base levels, learned or not.
    Character human = member("Knight", 20, 0);
    human.skills["PlateArmor"] = {"PlateArmor", 25, SkillMastery::Expert};
    classes.applyClassBonuses(human);
    CHECK_EQ(human.itemSkillBonuses["PlateArmor"], 5);
    CHECK_EQ(human.itemSkillBonuses["Shield"], 3);
    CHECK_EQ(human.magicalBonuses.resistances.fire, 0);

    Character elf = member("Archer", 30, 7);
    classes.applyClassBonuses(elf);
    CHECK_EQ(elf.magicalBonuses.resistances.fire, 55);
    CHECK_EQ(elf.magicalBonuses.resistances.mind, 0);
    Character dragon = member("Dragon", 30, 5);
    classes.applyClassBonuses(dragon);
    CHECK_EQ(dragon.magicalBonuses.resistances.fire, 160);
    Character vampire = member("Vampire", 10, 1);
    classes.applyClassBonuses(vampire);
    CHECK(vampire.magicalImmunities.mind);

    // Race Skillz: a shift that works without a class cap, a maximum that forbids, a minimum.
    ClassSkillTable skills;
    REQUIRE(skills.loadCapsFromRows({{"", "Knight", "Sorcerer"}, {"Sword", "M", "-"}, {"Merchant", "-", "E"},
        {"VampireAbility", "-", "-"}, {"Axe", "B", "-"}}));
    MergedRaceSkillTable races;
    std::string error;
    REQUIRE_MESSAGE(races.loadFromYaml("version: 1\nshift_without_class_cap: true\nrules:\n"
                                       "  - {race: Human, race_id: 0, skill: Merchant, add: 1}\n"
                                       "  - {race: Dragon, race_id: 5, skill: Sword, max_mastery: none}\n"
                                       "  - {race: Vampire, race_id: 1, skill: VampireAbility, min_mastery: master}\n"
                                       "  - {race: Minotaur, race_id: 3, skill: Axe, min_mastery: expert}\n",
                        error),
        error);
    REQUIRE(skills.applyRaceSkillOverrides(races));
    CHECK_EQ(skills.getEffectiveCap("Knight", 0, "Merchant"), SkillMastery::Normal);
    CHECK_EQ(skills.getEffectiveCap("Sorcerer", 0, "Merchant"), SkillMastery::Master);
    CHECK_EQ(skills.getEffectiveCap("Knight", 5, "Sword"), SkillMastery::None);
    CHECK_EQ(skills.getEffectiveCap("Knight", 0, "Sword"), SkillMastery::Master);
    CHECK_EQ(skills.getEffectiveCap("Sorcerer", 1, "VampireAbility"), SkillMastery::Master);
    CHECK_EQ(skills.getEffectiveCap("Knight", 3, "Axe"), SkillMastery::Expert);
}

TEST_CASE("MAW class perks feed the combat numbers")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});

    // Death Knight Frost and Unholy ramp {0.5, 0.75, 1, 1} per point between the mastery thresholds (§5.3).
    const auto deathKnightFlat = [&rules](uint32_t level, SkillMastery mastery)
    {
        Character character = member("DeathKnight", 20);
        character.skills["WaterMagic"] = {"WaterMagic", level, mastery};
        return mawClassMeleeFlatDamage(rules, character);
    };
    CHECK(deathKnightFlat(3, SkillMastery::Normal) == doctest::Approx(1.1).epsilon(0.03));
    CHECK(deathKnightFlat(5, SkillMastery::Expert) == doctest::Approx(2.9).epsilon(0.02));
    CHECK(deathKnightFlat(8, SkillMastery::Master) == doctest::Approx(6.7).epsilon(0.01));
    CHECK(deathKnightFlat(10, SkillMastery::Grandmaster) == doctest::Approx(10));
    CHECK(deathKnightFlat(50, SkillMastery::Grandmaster) == doctest::Approx(50));

    Character seraphim = member("Seraphim", 20);
    seraphim.skills["MindMagic"] = {"MindMagic", 10, SkillMastery::Expert};
    seraphim.skills["LightMagic"] = {"LightMagic", 8, SkillMastery::Master};
    CHECK(mawClassMeleeFlatDamage(rules, seraphim) == doctest::Approx(15));
    CHECK(mawClassAttackSpeedPercent(seraphim) == doctest::Approx(12));

    Character shaman = member("Shaman", 20);
    shaman.skills["SpiritMagic"] = {"SpiritMagic", 20, SkillMastery::Master};
    shaman.skills["AirMagic"] = {"AirMagic", 30, SkillMastery::Master};
    shaman.skills["FireMagic"] = {"FireMagic", 10, SkillMastery::Expert};
    CHECK(mawClassMeleeMultiplier(shaman) == doctest::Approx(1.2));
    CHECK(mawClassDefense(rules, shaman, 1).physicalCutSkill == doctest::Approx(30));
    CHECK(mawShamanSchoolSum(shaman) == doctest::Approx(60));
    const MawAscension shamanCost = mawAscension(shaman, MawAscensionUse::Cost);
    CHECK(shamanCost.skill == doctest::Approx(60.0 / 7));
    CHECK_EQ(shamanCost.mastery, SkillMastery::Grandmaster);
    CHECK(mawAscension(shaman, MawAscensionUse::Damage).skill == doctest::Approx(0));

    Character elementalist = member("Elementalist", 20);
    elementalist.skills["FireMagic"] = {"FireMagic", 9, SkillMastery::Expert};
    elementalist.skills["AirMagic"] = {"AirMagic", 4, SkillMastery::Normal};
    CHECK(mawAscension(elementalist, MawAscensionUse::Damage).skill == doctest::Approx(3.25));
    CHECK(mawAscension(elementalist, MawAscensionUse::CastTime).skill == doctest::Approx(3));
    CHECK(mawAscension(member("DeathKnight", 5), MawAscensionUse::Cost).skill == doctest::Approx(0));

    // Leech: the Vampire race, doubled for the Vampire classes; Death Knights' Blood.
    Character nosferatu = member("Nosferatu", 20, 1);
    CHECK(mawLeech(rules, nosferatu, nullptr).melee == doctest::Approx(0.10));
    CHECK(mawLeech(rules, member("DeathKnight", 20), nullptr).melee == doctest::Approx(0.10));
    CHECK(mawLeech(rules, member("Knight", 20), nullptr).melee == doctest::Approx(0));

    // An immune member takes nothing; a Death Knight's Blood divides physical hits.
    MawMitigationInputs hit;
    hit.damage = 1000;
    hit.attackerLevel = 50;
    hit.physicalCutSkill = 50;
    CHECK(mawMitigatedDamage(hit) == doctest::Approx(667).epsilon(0.001));
}

TEST_CASE("MAW wield rules: Seraphim swords, Dwarf and Minotaur axes")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ItemRules &items = rules.gameRules().items;
    ItemDefinition greatSword;
    greatSword.skillGroup = "Sword";
    greatSword.equipStat = "Weapon2";
    ItemDefinition sword;
    sword.skillGroup = "Sword";
    sword.equipStat = "Weapon";
    ItemDefinition axe;
    axe.skillGroup = "Axe";
    axe.equipStat = "Weapon";
    ItemDefinition greatAxe;
    greatAxe.skillGroup = "Axe";
    greatAxe.equipStat = "Weapon2";

    Character seraphim = member("Seraphim", 10);
    seraphim.skills["Sword"] = {"Sword", 10, SkillMastery::Master};
    CHECK_FALSE(items.wield(seraphim, greatSword).twoHanded);
    CHECK_FALSE(items.wield(seraphim, sword).offHand);
    Character knight = member("Knight", 10);
    knight.skills["Sword"] = {"Sword", 10, SkillMastery::Master};
    CHECK(items.wield(knight, greatSword).twoHanded);
    CHECK(items.wield(knight, sword).offHand);
    CHECK(standardGameRules().items.wield(knight, sword).offHand);

    Character minotaur = member("Minotaur", 10, 3);
    minotaur.skills["Axe"] = {"Axe", 10, SkillMastery::Expert};
    CHECK(items.wield(minotaur, axe).offHand);
    CHECK_FALSE(items.wield(minotaur, greatAxe).twoHanded);
    CHECK_FALSE(items.wield(minotaur, greatAxe).offHand);
    minotaur.skills["Axe"].mastery = SkillMastery::Master;
    CHECK(items.wield(minotaur, greatAxe).offHand);
    Character dwarf = member("Knight", 10, 9);
    dwarf.skills["Axe"] = {"Axe", 10, SkillMastery::Master};
    CHECK(items.wield(dwarf, greatAxe).twoHanded);
    CHECK(items.wield(dwarf, axe).offHand);
    CHECK_FALSE(items.wield(knight, axe).offHand);
}

TEST_CASE("MAW halberds are wielded with Spear or Axe, whichever is higher (MAW 8967ae88)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ItemRules &items = rules.gameRules().items;
    ItemDefinition halberd;
    halberd.itemId = 47;
    halberd.skillGroup = "Spear";
    halberd.equipStat = "Weapon2";
    ItemDefinition spear;
    spear.itemId = 42;
    spear.skillGroup = "Spear";
    spear.equipStat = "Weapon1or2";

    Character fighter = member("Knight", 10);
    CHECK_EQ(items.weaponSkill(fighter, halberd), "Spear");
    fighter.skills["Axe"] = {"Axe", 4, SkillMastery::Normal};
    CHECK_EQ(items.weaponSkill(fighter, halberd), "Axe");
    CHECK_EQ(items.weaponSkill(fighter, spear), "Spear");
    CHECK_EQ(standardGameRules().items.weaponSkill(fighter, halberd), "Spear");

    // Axe alone lets a character equip a halberd (tempSkillForEquip, S:1827-1830); Standard still asks for Spear.
    CHECK_FALSE(GameMechanics::canCharacterEquipItem(fighter, halberd, nullptr));
    bindGameRules(&rules.gameRules());
    CHECK(GameMechanics::canCharacterEquipItem(fighter, halberd, nullptr));
    CHECK_FALSE(GameMechanics::canCharacterEquipItem(member("Knight", 10), halberd, nullptr));
    bindGameRules(nullptr);

    // Equal levels: the higher mastery wins, Spear on a tie.
    fighter.skills["Spear"] = {"Spear", 4, SkillMastery::Normal};
    CHECK_EQ(items.weaponSkill(fighter, halberd), "Spear");
    fighter.skills["Axe"].mastery = SkillMastery::Expert;
    CHECK_EQ(items.weaponSkill(fighter, halberd), "Axe");
    fighter.skills["Spear"].level = 5;
    CHECK_EQ(items.weaponSkill(fighter, halberd), "Spear");

    // A Minotaur holds a halberd in one hand as a two-handed axe, in the off hand from Master Axe.
    Character minotaur = member("Minotaur", 10, 3);
    minotaur.skills["Axe"] = {"Axe", 10, SkillMastery::Expert};
    CHECK_FALSE(items.wield(minotaur, halberd).twoHanded);
    CHECK_FALSE(items.wield(minotaur, halberd).offHand);
    minotaur.skills["Axe"].mastery = SkillMastery::Master;
    CHECK(items.wield(minotaur, halberd).offHand);
    CHECK(items.wield(member("Knight", 10, 9), halberd).twoHanded);
}

TEST_CASE("MAW promotions follow the quest bits of every world")
{
    MawPromotionData promotions;
    std::string error;
    REQUIRE_MESSAGE(promotions.loadFromYaml("kinds:\n"
                                            "  2: {mm6: [1649, 1650], mm7: [1609, 1610], mm8: 1546, mm8_award: 31}\n"
                                            "  17: {mm6: [1649], mm7: [1609], mm8: 1546, mm8_award: 31, "
                                            "mid: [1647, 1607]}\n",
                        error),
        error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, promotions);
    ClassSkillTable classes;
    REQUIRE(classes.loadClassMetadataFromRows({{"#", "Kind", "Step", "Note"}, {"4", "2", "0", "Cleric"},
        {"5", "2", "1", "Priest"}, {"6", "2", "2", "Priest of the Light"}, {"7", "2", "2", "Priest of the Dark"},
        {"53", "17", "0", "Seraphim"}, {"54", "17", "1", "Angel"}, {"55", "17", "2", "Archangel"}}));

    PartySeed seed;
    seed.members = {member("Cleric", 5), member("Seraphim", 5)};
    Party party;
    party.seed(seed);
    party.setClassSkillTable(&classes);
    const MawClassRules &classRules = static_cast<const MawClassRules &>(rules.gameRules().classes);

    // A Seraphim's mid step comes from the first-tier bits of the Cleric line.
    party.setQuestBit(1607, true);
    classRules.updatePromotions(party);
    CHECK_EQ(party.members()[0].className, "Cleric");
    CHECK_EQ(party.members()[1].className, "Angel");

    // The Cleric kind's promotion on one world makes both final, one of the Cleric's two final classes.
    party.setQuestBit(1609, true);
    classRules.updatePromotions(party);
    const std::string cleric = party.members()[0].className;
    CHECK((cleric == "PriestLight" || cleric == "PriestDark"));
    CHECK_EQ(party.members()[1].className, "Archangel");
    CHECK_EQ(rules.promotionWorlds(2), 1);

    // The pick is fixed per character; a second world makes the final classes Elder.
    party.setQuestBit(1546, true);
    classRules.updatePromotions(party);
    CHECK_EQ(party.members()[0].className, cleric);
    CHECK_EQ(rules.promotionWorlds(2), 2);
    CHECK_EQ(rules.promotionWorlds(17), 2);

    CHECK_EQ(mawPromotionWorlds(promotions.kinds.at(2), [](uint32_t bit) { return bit == 1610; },
                 [](uint32_t award) { return award == 31; }),
        2);
}

TEST_CASE("MAW counts Chedian's promotion quests as a fourth world")
{
    MawPromotionData promotions;
    std::string error;
    REQUIRE_MESSAGE(promotions.loadFromYaml("kinds:\n"
                                            "  2: {mm6: [1649], mm7: [1609], mm8: 1546, mm8_award: 31, mm9: [90261]}\n"
                                            "  17: {mm6: [1649], mm7: [1609], mm8: 1546, mm8_award: 31, mm9: [90261], "
                                            "mid: [1647, 1607, 90213]}\n",
                        error),
        error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, promotions);
    ClassSkillTable classes;
    REQUIRE(classes.loadClassMetadataFromRows({{"#", "Kind", "Step", "Note"}, {"4", "2", "0", "Cleric"},
        {"5", "2", "1", "Priest"}, {"6", "2", "2", "Priest of the Light"}, {"53", "17", "0", "Seraphim"},
        {"54", "17", "1", "Angel"}, {"55", "17", "2", "Archangel"}}));
    PartySeed seed;
    seed.members = {member("Cleric", 5), member("Seraphim", 5)};
    Party party;
    party.seed(seed);
    party.setClassSkillTable(&classes);
    const MawClassRules &classRules = static_cast<const MawClassRules &>(rules.gameRules().classes);

    // MM9's Healer quest (key 213) is the Seraphim's first step, as MM6's and MM7's first tiers are.
    party.setQuestBit(90213, true);
    classRules.updatePromotions(party);
    CHECK_EQ(party.members()[1].className, "Angel");

    // MM9's Priest quest (key 261) is the Cleric kind's promotion on Chedian: both lines final, one world.
    party.setQuestBit(90261, true);
    classRules.updatePromotions(party);
    CHECK_EQ(party.members()[0].className, "PriestLight");
    CHECK_EQ(party.members()[1].className, "Archangel");
    CHECK_EQ(rules.promotionWorlds(2), 1);

    // All four worlds: Supreme, x1.75 HP and SP per level (DEVIATIONS 183); three are Ultimate's x1.5.
    ClassMultiplierEntry priest = {};
    priest.className = "PriestLight";
    priest.classKind = 2;
    priest.promotionStep = 2;
    priest.healthPerLevel = 4;
    priest.manaPerLevel = 4;
    for (uint32_t bit : {1649u, 1609u})
    {
        party.setQuestBit(bit, true);
    }
    classRules.updatePromotions(party);
    const auto perLevel = [&classRules, &priest]()
    {
        Character probe = member("PriestLight", 10);
        const int at10 = *classRules.baseMaxHealth(probe, priest);
        probe.level = 11;
        return *classRules.baseMaxHealth(probe, priest) - at10;
    };
    CHECK_EQ(rules.promotionWorlds(2), 3);
    CHECK_EQ(perLevel(), 6);
    party.setQuestBit(1546, true);
    classRules.updatePromotions(party);
    CHECK_EQ(rules.promotionWorlds(2), 4);
    CHECK_EQ(perLevel(), 7);
}

TEST_CASE("MAW Death Knights and Assassins know their own spells at fixed costs")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;

    Character deathKnight = member("DeathKnight", 10);
    deathKnight.skills["WaterMagic"] = {"WaterMagic", 5, SkillMastery::Expert};
    CHECK_EQ(mawKnownClassSpells(deathKnight), std::vector<uint32_t>{26, 27});
    deathKnight.skills["BodyMagic"] = {"BodyMagic", 1, SkillMastery::Normal};
    CHECK_EQ(mawKnownClassSpells(deathKnight), std::vector<uint32_t>{26, 27, 68});
    CHECK_EQ(std::string(mawClassSchoolName(deathKnight, "BodyMagic")), "Blood");
    CHECK_EQ(rules.gameRules().skills.skillDisplayName(deathKnight, "WaterMagic"), "Frost");
    CHECK_EQ(rules.gameRules().skills.skillDisplayName(member("Knight", 1), "WaterMagic"), "Water Magic");

    // An unskilled Assassin knows the first entries of each school.
    CHECK_EQ(mawKnownClassSpells(member("Thief", 1)), std::vector<uint32_t>{1, 12, 17, 24, 34});

    SpellEntry iceBolt;
    iceBolt.id = 26;
    iceBolt.name = "Ice Bolt";
    CharacterSpellCast cast;
    cast.pCaster = &deathKnight;
    cast.pSpell = &iceBolt;
    cast.mastery = SkillMastery::Expert;
    CHECK_EQ(spells.manaCost(cast, 4), 15);
    CHECK_EQ(spells.spellName(deathKnight, iceBolt), "Icy Touch");
    CHECK_EQ(spells.spellName(member("Sorcerer", 1), iceBolt), "Ice Bolt");
    SpellEntry heal;
    heal.id = 68;
    cast.pSpell = &heal;
    CHECK_EQ(spells.manaCost(cast, 2), 0);

    // Blood Leech is a switch.
    PartySeed seed;
    seed.members = {deathKnight, member("Thief", 1)};
    Party party;
    party.seed(seed);
    CHECK(spells.castAura(party, 0, 68) == AuraCastResult::Held);
    CHECK(party.members()[0].rulesetState.classToggleOn(68));
    CHECK(spells.castAura(party, 0, 68) == AuraCastResult::Released);
    CHECK_FALSE(party.members()[0].rulesetState.classToggleOn(68));
    // One switch at a time: Death Grasp turns Blood Leech off.
    CHECK(spells.castAura(party, 0, 68) == AuraCastResult::Held);
    CHECK(spells.castAura(party, 0, 96) == AuraCastResult::Held);
    CHECK_FALSE(party.members()[0].rulesetState.classToggleOn(68));
    CHECK(party.members()[0].rulesetState.classToggleOn(96));

    // Stun takes three combo points.
    CHECK(spells.castRefusal(party, 1, 34).has_value());
    rules.classRuntime(party.members()[1]).comboPoints = 4;
    CHECK_FALSE(spells.castRefusal(party, 1, 34).has_value());
    spells.afterCast(party, 1, 34, SpellTable{}, false, false);
    CHECK(rules.classRuntime(party.members()[1]).comboPoints == doctest::Approx(1));
    CHECK_FALSE(spells.castRefusal(party, 1, 1).has_value());
}

TEST_CASE("MAW Death Knights and Assassins have their own spellbook pages and nobody else does")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;

    // Presentation only: Standard and every other class keep the standard book.
    CHECK(standardGameRules().spells.spellbookSkin(member("DeathKnight", 1)) == nullptr);
    CHECK(spells.spellbookSkin(member("Sorcerer", 1)) == nullptr);
    CHECK(spells.spellbookSkin(member("Elementalist", 1)) == nullptr);

    const std::filesystem::path icons = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/icons_x2";
    const auto checkBook = [&](const std::string &className, const std::vector<uint32_t> &firstSpellIds)
    {
        const SpellbookSkin *pSkin = spells.spellbookSkin(member(className, 1));
        REQUIRE(pSkin != nullptr);
        REQUIRE_EQ(pSkin->pages.size(), firstSpellIds.size());
        std::vector<uint32_t> pictured;

        for (size_t index = 0; index < firstSpellIds.size(); ++index)
        {
            const SpellbookSkinPage &page = pSkin->pages[index];
            CHECK_EQ(page.firstSpellId, firstSpellIds[index]);

            for (const char *pAsset : {page.pPageAsset, page.pTabAsset, page.pTabSelectedAsset})
            {
                CHECK_MESSAGE(std::filesystem::exists(icons / (std::string(pAsset) + ".png")), pAsset);
            }

            for (const SpellbookSkinSpell &spell : page.spells)
            {
                // Each picture is a spell of the page's school, inside the book.
                CHECK(spell.spellId >= page.firstSpellId);
                CHECK(spell.spellId < page.firstSpellId + 11);
                CHECK(spell.rect.x >= 0);
                CHECK(spell.rect.y >= 0);
                CHECK(spell.rect.x + spell.rect.width <= 640);
                CHECK(spell.rect.y + spell.rect.height <= 480);
                CHECK_MESSAGE(std::filesystem::exists(icons / (std::string(spell.pAsset) + ".png")), spell.pAsset);
                CHECK_MESSAGE(std::filesystem::exists(icons / (std::string(spell.pHighlightedAsset) + ".png")),
                    spell.pHighlightedAsset);
                pictured.push_back(spell.spellId);
            }
        }

        // Every class spell has exactly one picture.
        std::vector<uint32_t> classSpells;

        for (const MawClassSpell &spell : mawClassSpells(className))
        {
            classSpells.push_back(spell.spellId);
        }

        std::sort(pictured.begin(), pictured.end());
        std::sort(classSpells.begin(), classSpells.end());
        CHECK_EQ(pictured, classSpells);
    };

    checkBook("DeathKnight", {23, 67, 89});
    checkBook("LichKing", {23, 67, 89});
    checkBook("Thief", {1, 12, 23, 34});
    checkBook("Spy", {1, 12, 23, 34});

    // The tabs stack from the top: the class pages the member has, then any other school (a racial page).
    const SpellbookSkin &deathKnightBook = *spells.spellbookSkin(member("DeathKnight", 1));
    const std::vector<SpellbookSkinTab> tabs = spellbookSkinTabs(deathKnightBook, [](SpellbookSchool school)
        {
            return school == SpellbookSchool::Body || school == SpellbookSchool::Dark
                || school == SpellbookSchool::Vampire;
        });
    REQUIRE_EQ(tabs.size(), 3);
    CHECK(tabs[0].school == SpellbookSchool::Body);
    CHECK(tabs[0].pPage == deathKnightBook.page(67));
    CHECK(tabs[1].school == SpellbookSchool::Dark);
    CHECK(tabs[2].school == SpellbookSchool::Vampire);
    CHECK(tabs[2].pPage == nullptr);
    CHECK(tabs[0].rect.y == doctest::Approx(2));
    CHECK(tabs[2].rect.y == doctest::Approx(80));
    CHECK(tabs[2].rect.x == doctest::Approx(592));
}

TEST_CASE("MAW's Vampiric Aura and Fire Aura show on every member while held")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    Character knight = member("DeathKnight", 10);
    knight.skills["DarkMagic"] = {"DarkMagic", 5, SkillMastery::Normal};
    PartySeed seed;
    seed.members = {knight, member("Knight", 10)};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());

    REQUIRE(spells.castAura(party, 0, 91) == AuraCastResult::Held);
    spells.updateAuras(party, 0.5f);
    CHECK(party.characterBuff(0, CharacterBuffId::VampiricWeapon) != nullptr);
    CHECK(party.characterBuff(1, CharacterBuffId::VampiricWeapon) != nullptr);
    CHECK_EQ(party.characterBuff(1, CharacterBuffId::VampiricWeapon)->spellId, 91u);

    REQUIRE(spells.castAura(party, 0, 91) == AuraCastResult::Released);
    spells.updateAuras(party, 0.5f);
    CHECK(party.characterBuff(1, CharacterBuffId::VampiricWeapon) == nullptr);

    // Day of the Gods raises the stats on the update that applies it, not only when its buff is next refreshed.
    party.member(0)->might = 100;
    party.member(1)->might = 100;
    party.member(0)->skills["LightMagic"] = {"LightMagic", 200, SkillMastery::Grandmaster};
    REQUIRE(spells.castAura(party, 0, 83) == AuraCastResult::Held);
    spells.updateAuras(party, 0.5f);
    CHECK_EQ(party.members()[0].magicalBonuses.might, 20);
    CHECK_EQ(party.members()[1].magicalBonuses.might, 20);
    REQUIRE(spells.castAura(party, 0, 83) == AuraCastResult::Released);
    spells.updateAuras(party, 0.5f);
    CHECK_EQ(party.members()[1].magicalBonuses.might, 0);

    // Empower Magic has no buff slot: the rules list it while it is held.
    CHECK(spells.heldAurasWithoutBuffSlot(party).empty());
    rules.state().auraHolders[28] = 0;
    CHECK_EQ(spells.heldAurasWithoutBuffSlot(party), std::vector<uint32_t>{28});
    CHECK(standardGameRules().spells.heldAurasWithoutBuffSlot(party).empty());
}

TEST_CASE("MAW Elementalists rotate their quick spell within the bound kind unless switched off")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    SpellTable spellTable;
    REQUIRE(spellTable.loadFromRows({
        {"2", "", "Fire Bolt", "Fire", "", ""},
        {"6", "", "Fireball", "Fire", "", ""},
        {"9", "", "Meteor Shower", "Fire", "", ""},
        {"10", "", "Inferno", "Fire", "", ""},
        {"11", "", "Incinerate", "Fire", "", ""},
    }));
    Character elementalist = member("Elementalist", 20);
    elementalist.knownSpellIds = {2, 6, 9, 10, 11};
    elementalist.quickSpellName = "Fireball";
    BattleOrder incinerate;
    incinerate.spellName = "Incinerate";
    elementalist.battleOrders = {incinerate};
    PartySeed seed;
    seed.members = {elementalist};
    Party party;
    party.seed(seed);
    Character &caster = *party.member(0);

    // Area spells stay area spells, by where they can be cast; the attack order's spell was not cast and stays.
    for (int cast = 0; cast < 20; ++cast)
    {
        const SpellEntry *pBound = spellTable.findByName(caster.quickSpellName);
        REQUIRE(pBound != nullptr);
        spells.afterCast(party, 0, uint32_t(pBound->id), spellTable, true, false);
        CHECK((caster.quickSpellName == "Fireball" || caster.quickSpellName == "Inferno"));
    }

    REQUIRE_EQ(caster.battleOrders.size(), 1);
    CHECK_EQ(caster.battleOrders.front().spellName, "Incinerate");
    CHECK_EQ(rules.classRuntime(caster).elementalStacks, 20);

    // A spell the player binds names the new kind: single target.
    caster.quickSpellName = "Incinerate";

    for (int cast = 0; cast < 10; ++cast)
    {
        const SpellEntry *pBound = spellTable.findByName(caster.quickSpellName);
        REQUIRE(pBound != nullptr);
        spells.afterCast(party, 0, uint32_t(pBound->id), spellTable, false, false);
        CHECK((caster.quickSpellName == "Fire Bolt" || caster.quickSpellName == "Incinerate"));
    }

    // Switched off: the spell stays and no stack builds.
    CHECK(spells.spellRotation(caster) == std::optional<bool>(true));
    REQUIRE(spells.toggleSpellRotation(caster) == std::optional<bool>(false));
    CHECK(spells.spellRotation(caster) == std::optional<bool>(false));
    const std::string bound = caster.quickSpellName;
    const int stacks = rules.classRuntime(caster).elementalStacks;
    spells.afterCast(party, 0, uint32_t(spellTable.findByName(bound)->id), spellTable, false, false);
    CHECK_EQ(caster.quickSpellName, bound);
    CHECK_EQ(rules.classRuntime(caster).elementalStacks, stacks);
    CHECK(spells.toggleSpellRotation(caster) == std::optional<bool>(true));

    // A spellbook cast starts the stacks over: its own is the first (A6.9).
    spells.afterCast(party, 0, 2, spellTable, false, true);
    CHECK_EQ(rules.classRuntime(caster).elementalStacks, 1);
    Character knight = member("Knight", 20);
    CHECK_FALSE(spells.spellRotation(knight).has_value());
    CHECK_FALSE(spells.toggleSpellRotation(knight).has_value());
    CHECK_FALSE(standardGameRules().spells.spellRotation(caster).has_value());
}

TEST_CASE("MAW Elementalists learn the elements by casting them")
{
    // Tier^1.5 x level^0.5 x party size^0.5, a third for area spells.
    CHECK(mawElementalistProgress(2, 25, 4, false) == doctest::Approx(std::pow(2, 1.5) * 5 * 2));
    CHECK(mawElementalistProgress(6, 25, 4, false) == doctest::Approx(std::pow(6, 1.5) * 5 * 2 / 3));
    CHECK(mawElementalistProgress(15, 25, 4, true) == doctest::Approx(std::pow(4, 1.5) * 5));
    CHECK(mawElementalistProgress(60, 25, 4, false) == doctest::Approx(0));

    Character elementalist = member("Elementalist", 10);
    elementalist.skills["FireMagic"] = {"FireMagic", 8, SkillMastery::Expert};
    // Fire Bolt, Sparks, Poison Spray and Deadly Swarm always; Torch Light (tier 1) with Novice Fire.
    CHECK_EQ(mawElementalistKnownSpells(elementalist, false), std::vector<uint32_t>{2, 15, 24, 37, 1});
    elementalist.rulesetState.elementalProgress[0] = 5000;
    // Tiers 3 to 5 come with the progress; tier 6 wants more and tier 8 a Master.
    CHECK_EQ(mawElementalistKnownSpells(elementalist, false), std::vector<uint32_t>{2, 15, 24, 37, 1, 3, 4, 5});
    CHECK(mawElementalistOffensiveSpell(11));
    CHECK_FALSE(mawElementalistOffensiveSpell(5));
}

TEST_CASE("MAW dragons fight with fangs, breath and scales")
{
    // The worked example's formula (CLASSES_SPELLS_SPEC.md §5.10, level 20 with the party, Fangs 10 Expert, attack
    // +40; breath at Dragon Ability 10 Expert). It leaves out Might's flat effect, which Might 13 does not have.
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    MawGameState state;
    state.continentLevels[0] = 19;
    rules.setState(state);
    Character dragon = member("Dragon", 20, 5);
    dragon.skills["Unarmed"] = {"Unarmed", 10, SkillMastery::Expert};
    dragon.skills["DragonAbility"] = {"DragonAbility", 10, SkillMastery::Expert};
    ItemTable items;
    const CharacterCombatRows rows = mawCombatRows(rules, dragon, items, {13, 0, 0});
    CHECK_EQ(rows.meleeMinimumDamage, 98);
    CHECK_EQ(rows.meleeMaximumDamage, 163);
    CHECK_EQ(rows.meleeAttack, mawStatEffect(0) + 40);
    CHECK_EQ(rows.rangedMinimumDamage, 73);
    CHECK_EQ(rows.rangedMaximumDamage, 122);

    // Far above the party, a dragon fights at half its level or the party's plus one, whichever is lower.
    Character elder = dragon;
    elder.level = 60;
    CHECK_EQ(mawCombatRows(rules, elder, items, {13, 0, 0}).meleeMinimumDamage, 98);
}

TEST_CASE("low stats of a fresh MAW character lower its HP and SP but never wrap them to zero")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ClassRules &classes = rules.gameRules().classes;

    // A level-1 Seraphim with Personality 10 (effect -2, counted twice) and Endurance 8 (-3):
    // SP 15 + 1 x (1 - 2 - 2) = 12, HP 40 + 3 x (1 - 3) = 34.
    Character seraphim = member("Seraphim", 1);
    seraphim.personality = 10;
    seraphim.endurance = 8;
    const ClassMultiplierEntry seraphimEntry = entry("Seraphim", 40, 3, 15, 1, ClassManaMode::Personality, 17, 0);
    CHECK_EQ(classes.baseMaxSpellPoints(seraphim, seraphimEntry).value_or(-1), 12);
    CHECK_EQ(classes.baseMaxHealth(seraphim, seraphimEntry).value_or(-1), 34);
}

TEST_CASE("MAW shows combo points and Elementalist stacks at the portraits and names the dragons' skills")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ClassRules &classes = rules.gameRules().classes;
    Character assassin = member("Assassin", 20);
    Character elementalist = member("Elementalist", 20);
    Character knight = member("Knight", 20);
    rules.classRuntime(assassin).comboPoints = 3.5;
    rules.classRuntime(elementalist).elementalStacks = 7;
    assassin.knownSpellIds = {34, 39, 44};
    const PortraitCounter combo = classes.portraitCounter(assassin);
    CHECK(combo.kind == PortraitCounterKind::ComboPoints);
    CHECK_EQ(combo.amount, doctest::Approx(3.5));
    CHECK_EQ(combo.pips, 5);
    REQUIRE_EQ(combo.notes.size(), 4);
    CHECK_EQ(combo.notes[0], "3.5 of 5 combo points");
    CHECK_EQ(combo.notes[1], "3 (ready): Stun, Blades");
    CHECK_EQ(combo.notes[2], "4: Mass Distortion");
    const PortraitCounter stacks = classes.portraitCounter(elementalist);
    CHECK(stacks.kind == PortraitCounterKind::Stacks);
    CHECK_EQ(stacks.amount, doctest::Approx(7));
    CHECK_EQ(stacks.pips, 10);
    CHECK(classes.portraitCounter(knight).kind == PortraitCounterKind::None);
    CHECK(standardClassRules().portraitCounter(assassin).kind == PortraitCounterKind::None);
    CHECK(standardClassRules().portraitCounter(elementalist).kind == PortraitCounterKind::None);

    const SkillRules &skills = rules.gameRules().skills;
    // The names follow the portrait's race (A6.1): a dragon-faced Knight has Fangs, a Dragon of another race not.
    Character dragon = member("Knight", 20, 5);
    CHECK_EQ(skills.skillDisplayName(dragon, "Unarmed"), "Fangs");
    CHECK_EQ(skills.skillDisplayName(dragon, "Dodging"), "Scales");
    CHECK_EQ(skills.skillDisplayName(knight, "Unarmed"), "Unarmed");
    CHECK_EQ(skills.skillDisplayName(member("Dragon", 20), "Unarmed"), "Unarmed");
}
