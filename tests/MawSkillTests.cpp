#include "doctest/doctest.h"
#include "game/gameplay/GameMechanics.h"
#include "game/items/PriceCalculator.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSkillFormulas.h"
#include "tests/RegressionGameData.h"
#include "game/rules/maw/MawTexts.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/PortraitFxEventTable.h"

#include <cstdio>
#include <random>
#include <sstream>
#include <fstream>
#include <iterator>
#include <filesystem>
#include <string>
#include <utility>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
// A text without Might and Magic's inline colour codes ("\f" and five digits).
std::string withoutColor(std::string text)
{
    for (size_t found = text.find('\f'); found != std::string::npos; found = text.find('\f'))
    {
        text.erase(found, 6);
    }

    return text;
}
}

// The worked examples of devdocs/maw/TRAINERS_SKILLS.md §2-4.
namespace
{
Character characterWith(const std::string &className, const std::vector<std::pair<std::string, uint32_t>> &skills)
{
    Character character;
    character.className = className;

    for (const auto &[name, level] : skills)
    {
        character.skills[name] = CharacterSkill{name, level, SkillMastery::Normal};
    }

    return character;
}

// Points to raise every skill from 1 to its target, one point at a time, in the order given.
uint32_t raiseCost(const SkillRules &rules, const std::vector<std::pair<std::string, uint32_t>> &targets)
{
    std::vector<std::pair<std::string, uint32_t>> start;

    for (const auto &[name, level] : targets)
    {
        start.emplace_back(name, 1);
    }

    Character character = characterWith("Sorcerer", start);
    uint32_t total = 0;
    bool raised = true;

    while (raised)
    {
        raised = false;

        for (const auto &[name, level] : targets)
        {
            CharacterSkill &skill = character.skills[name];

            if (skill.level < level)
            {
                total += rules.skillRaiseCost(character, name);
                skill.level += 1;
                raised = true;
            }
        }
    }

    return total;
}
}

TEST_CASE("MAW shares raise costs between weapons, schools and racial abilities")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SkillRules &skills = rules.gameRules().skills;

    Character character = characterWith("Sorcerer", {{"FireMagic", 9}, {"AirMagic", 10}, {"WaterMagic", 12}});
    CHECK_EQ(skills.skillRaiseCost(character, "FireMagic"), 4u);
    character.skills["EarthMagic"] = CharacterSkill{"EarthMagic", 1, SkillMastery::Normal};
    character.skills["FireMagic"].level = 10;
    CHECK_EQ(skills.skillRaiseCost(character, "EarthMagic"), 1u);
    // Outside the set the raise costs the new level.
    character.skills["Meditation"] = CharacterSkill{"Meditation", 9, SkillMastery::Normal};
    CHECK_EQ(skills.skillRaiseCost(character, "Meditation"), 10u);
    CHECK_EQ(standardSkillRules().skillRaiseCost(character, "FireMagic"), 11u);

    // The order does not matter: Fire 12, Air 12, Water 8, Dagger 6 cost 139 (209 at full price).
    const std::vector<std::pair<std::string, uint32_t>> build = {
        {"FireMagic", 12}, {"AirMagic", 12}, {"WaterMagic", 8}, {"Dagger", 6}};
    const std::vector<std::pair<std::string, uint32_t>> reversed(build.rbegin(), build.rend());
    CHECK_EQ(raiseCost(skills, build), 139u);
    CHECK_EQ(raiseCost(skills, reversed), 139u);
    CHECK_EQ(raiseCost(standardSkillRules(), build), 209u);
    CHECK_EQ(mawSharedSetRefund({12, 12, 8, 6}), 139u);

    // Hybrid classes share only magic.
    Character shaman = characterWith("Shaman", {{"Dagger", 9}, {"Axe", 10}});
    CHECK_EQ(skills.skillRaiseCost(shaman, "Dagger"), 10u);
}

TEST_CASE("MAW teachers want more skill and charge by the masteries already held")
{
    RulesetOptions options;
    MawRules rules(options, MawMapLevels{});
    const SkillRules &skills = rules.gameRules().skills;
    CHECK_EQ(skills.masteryRequiredLevel("Sword", SkillMastery::Expert), 4u);
    options.progression = RulesetProgression::Horizontal;
    rules.setOptions(options);
    CHECK_EQ(skills.masteryRequiredLevel("Sword", SkillMastery::Expert), 6u);
    CHECK_EQ(skills.masteryRequiredLevel("Sword", SkillMastery::Grandmaster), 20u);
    // Non-horizontal skills keep Standard's 4/7/10.
    CHECK_EQ(skills.masteryRequiredLevel("Merchant", SkillMastery::Master), 7u);

    Character character = characterWith("Knight", {{"Sword", 10}, {"Axe", 6}, {"Mace", 6}, {"Spear", 6}});
    CHECK_EQ(skills.masteryTeacherCost(character, "Sword", SkillMastery::Expert, 2000), 1000);
    character.skills["Axe"].mastery = SkillMastery::Expert;
    character.skills["Mace"].mastery = SkillMastery::Expert;
    character.skills["Spear"].mastery = SkillMastery::Master;
    CHECK_EQ(skills.masteryTeacherCost(character, "Sword", SkillMastery::Expert, 2000), 4000);
    // A remembered mastery counts as held.
    character.skills["Bow"] = CharacterSkill{"Bow", 1, SkillMastery::Normal};
    character.rulesetState.rememberedMasteries["Bow"] = SkillMastery::Expert;
    CHECK_EQ(skills.masteryTeacherCost(character, "Sword", SkillMastery::Expert, 2000), 5000);

    Character knight = characterWith("Knight", {{"Sword", 20}, {"PlateArmor", 20}, {"Shield", 20}});
    knight.skills["PlateArmor"].mastery = SkillMastery::Grandmaster;
    knight.skills["Shield"].mastery = SkillMastery::Grandmaster;
    CHECK_EQ(skills.masteryTeacherCost(knight, "Sword", SkillMastery::Grandmaster, 10000), 60000);
    // Non-horizontal skills keep their price.
    CHECK_EQ(skills.masteryTeacherCost(knight, "Merchant", SkillMastery::Expert, 500), 500);
}

TEST_CASE("MAW respec refunds what the skills cost and remembers their masteries")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SkillRules &skills = rules.gameRules().skills;
    Character sorcerer = characterWith(
        "Sorcerer",
        {{"FireMagic", 12}, {"AirMagic", 12}, {"WaterMagic", 8}, {"Dagger", 6}, {"Meditation", 10}, {"Alchemy", 5}});
    sorcerer.level = 30;
    sorcerer.skillPoints = 3;
    sorcerer.skills["FireMagic"].mastery = SkillMastery::Master;
    sorcerer.skills["AirMagic"].mastery = SkillMastery::Master;
    sorcerer.skills["WaterMagic"].mastery = SkillMastery::Expert;
    sorcerer.skills["Dagger"].mastery = SkillMastery::Expert;
    sorcerer.skills["Meditation"].mastery = SkillMastery::Master;
    sorcerer.skills["Alchemy"].mastery = SkillMastery::Expert;

    CHECK_EQ(skills.skillResetCost(sorcerer).value_or(0), 30000);
    REQUIRE(skills.resetSkills(sorcerer));
    CHECK_EQ(sorcerer.skillPoints, 196u);
    CHECK_EQ(sorcerer.skills["FireMagic"].level, 1u);
    CHECK_EQ(sorcerer.skills["FireMagic"].mastery, SkillMastery::Normal);
    CHECK_EQ(sorcerer.skills["Alchemy"].level, 5u);
    CHECK_EQ(sorcerer.skills["Alchemy"].mastery, SkillMastery::Expert);
    CHECK_EQ(sorcerer.rulesetState.rememberedMasteries["FireMagic"], SkillMastery::Master);
    CHECK_EQ(sorcerer.rulesetState.rememberedMasteries["WaterMagic"], SkillMastery::Expert);
    CHECK_EQ(mawLevelUpPoints(30), 178u);

    // Expert comes back on the raise to 4, Master on the raise to 7.
    for (uint32_t level = 2; level <= 7; ++level)
    {
        sorcerer.skills["FireMagic"].level = level;
        const std::string status = skills.afterSkillRaised(sorcerer, "FireMagic", nullptr);
        const SkillMastery expected = level >= 7 ? SkillMastery::Master
            : level >= 4                         ? SkillMastery::Expert
                                                 : SkillMastery::Normal;
        INFO("level ", level);
        CHECK_EQ(sorcerer.skills["FireMagic"].mastery, expected);
        CHECK_EQ(!status.empty(), level == 4 || level == 7);
    }

    CHECK_FALSE(sorcerer.rulesetState.rememberedMasteries.contains("FireMagic"));
    CHECK_FALSE(standardSkillRules().skillResetCost(sorcerer).has_value());
}

TEST_CASE("MAW training halls train further and faster")
{
    CHECK_EQ(mawTrainingHallCap(5, false), 20);
    CHECK_EQ(mawTrainingHallCap(15, false), 30);
    CHECK_EQ(mawTrainingHallCap(25, false), 60);
    CHECK_EQ(mawTrainingHallCap(60, false), 230);
    CHECK_EQ(mawTrainingHallCap(200, false), 1410);
    CHECK_EQ(mawTrainingHallCap(200, true), 2830);
    CHECK_EQ(mawTrainingHallCap(-1, false), 72110);

    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_EQ(rules.gameRules().experience.trainingLevelCap(25), 60);
    CHECK_EQ(rules.gameRules().experience.trainingLevelCap(0), 0);
    CHECK(rules.gameRules().experience.trainingDurationMinutes(12000.0f) == doctest::Approx(2880.0f));
    CHECK_EQ(standardExperienceRules().trainingLevelCap(25), 25);
}

TEST_CASE("MAW's new skills climb their ladders and stop at their caps")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SkillRules &skills = rules.gameRules().skills;
    Character knight = characterWith("Knight", {{"Cover", 1}});
    knight.skillPoints = 10000;

    // Cover becomes Expert at 6, Master at 12, Grandmaster at 20; reaching its cap of 30 teaches Retaliation.
    for (uint32_t level = 2; level <= 30; ++level)
    {
        REQUIRE(skills.canRaiseSkill(knight, "Cover"));
        knight.skills["Cover"].level = level;
        skills.afterSkillRaised(knight, "Cover", nullptr);
        const SkillMastery expected = level >= 20 ? SkillMastery::Grandmaster
            : level >= 12                         ? SkillMastery::Master
            : level >= 6                          ? SkillMastery::Expert
                                                  : SkillMastery::Normal;
        INFO("level ", level);
        CHECK_EQ(knight.skills["Cover"].mastery, expected);
        CHECK_EQ(knight.hasSkill("Retaliation"), level == 30);
    }

    CHECK_FALSE(skills.canRaiseSkill(knight, "Cover"));
    CHECK_EQ(knight.skills["Retaliation"].level, 1u);
    CHECK_EQ(skills.skillLevelCap("Alchemy").value_or(0), 60u);
    CHECK_EQ(skills.skillLevelCap("ManaShield").value_or(0), 50u);
    // Every other skill stops at MAW's base limit of 500.
    CHECK_EQ(skills.skillLevelCap("Sword").value_or(0), 500u);
    CHECK_FALSE(standardSkillRules().skillLevelCap("Cover").has_value());

    // Retaliation climbs at 10, 24 and 40; Mana Shield takes 8, 20 and 32 on Road to Insanity.
    CHECK_EQ(mawSkillMasteryLadder("Retaliation", MawSkillMode::Normal)->at(1), 24u);
    CHECK_EQ(mawSkillMasteryLadder("ManaShield", MawSkillMode::RoadToInsanity)->at(2), 32u);
    CHECK_FALSE(mawSkillMasteryLadder("FireMagic", MawSkillMode::Normal).has_value());
}

TEST_CASE("MAW's promotion grants the ladder masteries the new class allows")
{
    // Discord: Enlightenment raised to 20 before the promotion stayed Expert until one more point was bought.
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    ClassSkillTable classes;
    REQUIRE(classes.loadCapsFromRows({{"", "Cleric", "Priest"}, {"Enlightenment", "E", "G"}, {"ManaShield", "E", "M"},
        {"Cover", "M", "G"}, {"Retaliation", "-", "B"}}));
    Character cleric = characterWith("Cleric", {{"Enlightenment", 20}, {"ManaShield", 50}, {"Cover", 30}});
    cleric.skills["Enlightenment"].mastery = SkillMastery::Expert;
    cleric.skills["ManaShield"].mastery = SkillMastery::Expert;
    cleric.skills["Cover"].mastery = SkillMastery::Master;

    PartySeed seed;
    seed.members.push_back(cleric);
    Party party;
    party.seed(seed);
    party.setClassSkillTable(&classes);
    party.setRules(&rules.gameRules());

    // Mana Shield at its level cap of 50 and Cover at 30 cannot be raised again, so only the promotion can grant them.
    REQUIRE(party.setMemberClassName(0, "Priest", true));
    const Character &priest = party.members()[0];
    CHECK_EQ(priest.findSkill("Enlightenment")->mastery, SkillMastery::Grandmaster);
    CHECK_EQ(priest.findSkill("ManaShield")->mastery, SkillMastery::Master);
    CHECK_EQ(priest.findSkill("Cover")->mastery, SkillMastery::Grandmaster);
    REQUIRE(priest.hasSkill("Retaliation"));
    CHECK_EQ(priest.findSkill("Retaliation")->level, 1u);
    CHECK_EQ(priest.findSkill("Retaliation")->mastery, SkillMastery::Normal);

    // Standard rules grant nothing on a class change.
    Character standard = characterWith("Priest", {{"Enlightenment", 20}});
    standardSkillRules().afterClassChanged(standard, &classes);
    CHECK_EQ(standard.findSkill("Enlightenment")->mastery, SkillMastery::Normal);
}

TEST_CASE("MAW Cover and Mana Shield follow their formulas")
{
    CHECK(mawCoverChance(0, false) == doctest::Approx(0.10));
    CHECK(mawCoverChance(30, false) == doctest::Approx(0.40));
    CHECK(mawCoverChance(45, true) == doctest::Approx(0.55));
    CHECK_EQ(mawCoverRequiredMastery(false, true), SkillMastery::Normal);
    CHECK_EQ(mawCoverRequiredMastery(false, false), SkillMastery::Expert);
    CHECK_EQ(mawCoverRequiredMastery(true, false), SkillMastery::Master);

    // At 50 points every spell point absorbs 5 damage.
    const MawManaShieldResult full = mawManaShield(100, 1000, 50, SkillMastery::Grandmaster);
    CHECK_EQ(full.damage, 0);
    CHECK_EQ(full.spellPointsSpent, 20);
    // Mana runs out: 10 SP absorb 50 of the hit.
    const MawManaShieldResult empty = mawManaShield(100, 10, 50, SkillMastery::Grandmaster);
    CHECK_EQ(empty.damage, 50);
    CHECK_EQ(empty.spellPointsSpent, 10);
    // Expert at 10 points: half the hit, 1 + 10^1.4 / 60 damage per spell point.
    const MawManaShieldResult expert = mawManaShield(100, 1000, 10, SkillMastery::Expert);
    CHECK_EQ(expert.damage, 50);
    CHECK_EQ(expert.spellPointsSpent, 35);
}

TEST_CASE("MAW Cover moves a hit to a covering member, or halves it alone")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const CombatRules &combat = rules.gameRules().combat;
    PartySeed seed;
    Character target = characterWith("Sorcerer", {});
    Character coverer = characterWith("Knight", {{"Cover", 30}});
    target.health = target.maxHealth = 50;
    coverer.health = coverer.maxHealth = 300;
    seed.members = {target, coverer};
    Party party;
    party.seed(seed);
    std::mt19937 rng(7);
    const auto covers = [&](bool spell, CombatDamageType type)
    {
        int count = 0;

        for (int trial = 0; trial < 2000; ++trial)
        {
            const std::optional<CoverOutcome> outcome =
                combat.coverMonsterAttack(party, MonsterAttackCover {0, spell, type, &rng});

            if (outcome)
            {
                CHECK_EQ(outcome->memberIndex, 1u);
                CHECK_FALSE(outcome->halved);
                ++count;
            }
        }

        return count / 2000.0;
    };

    // Novice covers physical attacks 40 % of the time at 30 points, not elemental attacks or spells.
    CHECK(covers(false, CombatDamageType::Physical) == doctest::Approx(0.40).epsilon(0.1));
    CHECK(covers(false, CombatDamageType::Fire) == doctest::Approx(0));
    CHECK(covers(true, CombatDamageType::Fire) == doctest::Approx(0));
    party.member(1)->skills["Cover"].mastery = SkillMastery::Master;
    CHECK(covers(true, CombatDamageType::Fire) == doctest::Approx(0.40).epsilon(0.1));
    party.member(1)->rulesetState.coverDisabled = true;
    CHECK(covers(false, CombatDamageType::Physical) == doctest::Approx(0));

    // Alone, a cover halves the hit.
    PartySeed soloSeed;
    soloSeed.members = {coverer};
    Party solo;
    solo.seed(soloSeed);
    bool halved = false;

    for (int trial = 0; trial < 100 && !halved; ++trial)
    {
        const std::optional<CoverOutcome> outcome =
            combat.coverMonsterAttack(solo, MonsterAttackCover {0, false, CombatDamageType::Physical, &rng});
        halved = outcome && outcome->memberIndex == 0 && outcome->halved;
    }

    CHECK(halved);

    // Mana Shield spends the member's mana on the hit.
    solo.member(0)->skills["ManaShield"] = CharacterSkill {"ManaShield", 50, SkillMastery::Grandmaster};
    solo.member(0)->spellPoints = 100;
    CHECK_EQ(combat.absorbCharacterDamage(solo, 0, 100), 0);
    CHECK_EQ(solo.member(0)->spellPoints, 80);
    solo.member(0)->rulesetState.manaShieldDisabled = true;
    CHECK_EQ(combat.absorbCharacterDamage(solo, 0, 100), 100);
    CHECK_EQ(standardGameRules().combat.absorbCharacterDamage(solo, 0, 100), 100);
}

TEST_CASE("MAW Cover and Mana Shield have skills page switches once learned")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SkillRules &skills = rules.gameRules().skills;
    Character knight = characterWith("Knight", {{"Cover", 10}, {"Sword", 4}});

    // Learned and on by default; a skill without a switch, or one not learned, has none.
    CHECK(skills.skillSwitch(knight, "Cover") == std::optional<bool>(true));
    CHECK_FALSE(skills.skillSwitch(knight, "ManaShield").has_value());
    CHECK_FALSE(skills.skillSwitch(knight, "Sword").has_value());
    CHECK_FALSE(skills.toggleSkillSwitch(knight, "ManaShield").has_value());
    CHECK_FALSE(knight.rulesetState.manaShieldDisabled);

    // Flipping it switches Cover's own flag and nothing else.
    CHECK(skills.toggleSkillSwitch(knight, "Cover") == std::optional<bool>(false));
    CHECK(knight.rulesetState.coverDisabled);
    CHECK(skills.skillSwitch(knight, "Cover") == std::optional<bool>(false));
    CHECK(skills.toggleSkillSwitch(knight, "Cover") == std::optional<bool>(true));
    CHECK_FALSE(knight.rulesetState.coverDisabled);

    knight.skills["ManaShield"] = CharacterSkill {"ManaShield", 6, SkillMastery::Expert};
    CHECK(skills.toggleSkillSwitch(knight, "ManaShield") == std::optional<bool>(false));
    CHECK(knight.rulesetState.manaShieldDisabled);
    CHECK_FALSE(knight.rulesetState.coverDisabled);

    // Standard has no switches.
    CHECK_FALSE(standardGameRules().skills.skillSwitch(knight, "Cover").has_value());
    CHECK_FALSE(standardGameRules().skills.toggleSkillSwitch(knight, "Cover").has_value());
}

TEST_CASE("MAW Identify Monster compares the best skill with the monster's level over the party's")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SkillRules &skills = rules.gameRules().skills;
    PartySeed seed;
    Character scout = characterWith("Knight", {{"IdentifyMonster", 5}});
    Character other = characterWith("Cleric", {});
    scout.level = 20;
    other.level = 40;
    seed.members = {scout, other};
    Party party;
    party.seed(seed);

    // 5 x Normal against 60 - 30: nothing; 5 x Expert = 10 against 40 - 30: hit points, attack and damage.
    CHECK_FALSE(skills.identifyMonsterReveal(party, 60).identified());
    CHECK(skills.identifyMonsterReveal(party, 60).hasSkill);
    party.member(0)->skills["IdentifyMonster"].mastery = SkillMastery::Expert;
    const IdentifyMonsterReveal expert = skills.identifyMonsterReveal(party, 40);
    CHECK(expert.attackAndDamage);
    CHECK_FALSE(expert.spellsAndEffects);
    CHECK_FALSE(skills.identifyMonsterReveal(party, 41).identified());

    // A Grandmaster knows every monster; the level is MAW's stored one, at most 255.
    party.member(0)->skills["IdentifyMonster"].mastery = SkillMastery::Grandmaster;
    CHECK(skills.identifyMonsterReveal(party, 5000).resistances);
    party.member(0)->skills["IdentifyMonster"].mastery = SkillMastery::Master;
    CHECK_FALSE(skills.identifyMonsterReveal(party, 300).identified());
    party.member(0)->skills["IdentifyMonster"].level = 75;
    CHECK(skills.identifyMonsterReveal(party, 5000).spellsAndEffects);

    // Standard: the best member's own check against the table level.
    CHECK(standardSkillRules().identifyMonsterReveal(party, 40).identified());
}

TEST_CASE("MAW shows monster resistances as its damage reads them and held auras without a timer")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_EQ(rules.gameRules().monsters.monsterResistanceText(250, {}), "200");
    CHECK_EQ(rules.gameRules().monsters.monsterResistanceText(1040, {}), "40");
    CHECK_EQ(standardGameRules().monsters.monsterResistanceText(200, {}), "Imm");
    CHECK_EQ(standardGameRules().monsters.monsterResistanceText(40, {}), "40");

    PartySeed seed;
    Character caster = characterWith("Sorcerer", {});
    caster.name = "Ann";
    seed.members = {caster};
    Party party;
    party.seed(seed);
    CHECK_FALSE(rules.gameRules().spells.heldBuffText(party, 86).has_value());
    rules.state().auraHolders[86] = 0;
    CHECK_EQ(rules.gameRules().spells.heldBuffText(party, 86).value_or(""), "Held by Ann");
    CHECK_FALSE(standardGameRules().spells.heldBuffText(party, 86).has_value());
}

TEST_CASE("MAW's Merchant: skill x mastery, Grandmaster or 45 trades at cost, no reputation, best member counts")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ItemRules &items = rules.gameRules().items;
    Character trader = characterWith("Knight", {{"Merchant", 10}});
    trader.skills["Merchant"].mastery = SkillMastery::Expert;
    CHECK_EQ(items.merchantValue(trader).value_or(-1), 27);
    trader.merchantBonus = 8;
    CHECK_EQ(items.merchantValue(trader).value_or(-1), 35);
    trader.skills["Merchant"] = {"Merchant", 15, SkillMastery::Master};
    CHECK_EQ(items.merchantValue(trader).value_or(-1), 100);
    CHECK_EQ(items.merchantValue(characterWith("Knight", {})).value_or(-1), 7);
    CHECK_FALSE(standardGameRules().items.merchantValue(trader).has_value());

    // The best member prices the party's deals.
    PartySeed seed;
    seed.members = {characterWith("Knight", {}), trader};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    REQUIRE(PriceCalculator::rulesMerchantMember(party) != nullptr);
    CHECK_EQ(PriceCalculator::rulesMerchantMember(party), party.member(1));
    party.setRules(&standardGameRules());
    CHECK(PriceCalculator::rulesMerchantMember(party) == nullptr);
}

TEST_CASE("MAW's Glamour adds its mastery times its power to Merchant; a Grandmaster Glamour trades at cost")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    PartySeed seed;
    seed.members = {characterWith("Knight", {})};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    const ItemRules &items = rules.gameRules().items;

    // A Novice Dark Elf of skill 45 casts power 25: 7 + 25, not the 45 that trades at cost.
    party.applyCharacterBuff(0, CharacterBuffId::Glamour, 600.0f, 25, 100, 45, SkillMastery::Normal, 0);
    CHECK_EQ(items.merchantValue(*party.member(0)).value_or(-1), 32);
    party.applyCharacterBuff(0, CharacterBuffId::Glamour, 600.0f, 10, 100, 15, SkillMastery::Expert, 0);
    CHECK_EQ(items.merchantValue(*party.member(0)).value_or(-1), 27);
    party.applyCharacterBuff(0, CharacterBuffId::Glamour, 600.0f, 3, 100, 1, SkillMastery::Grandmaster, 0);
    CHECK_EQ(items.merchantValue(*party.member(0)).value_or(-1), 100);
    party.clearCharacterBuff(0, CharacterBuffId::Glamour);
    CHECK_EQ(items.merchantValue(*party.member(0)).value_or(-1), 7);
}

TEST_CASE("MAW skill popups fill every number for every class line and keep the table's lines where asked")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/texts.yml");
    std::ostringstream yaml;
    yaml << input.rdbuf();
    MawTextData textData;
    std::string error;
    REQUIRE_MESSAGE(textData.loadFromYaml(yaml.str(), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, {}, {}, {}, textData);
    const SkillRules &skills = rules.gameRules().skills;
    static const std::vector<std::string> SkillNames = {
        "Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Mace", "Blaster", "Shield", "LeatherArmor",
        "ChainArmor", "PlateArmor", "FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic",
        "BodyMagic", "LightMagic", "DarkMagic", "IdentifyItem", "Merchant", "RepairItem", "Bodybuilding", "Meditation",
        "Perception", "Regeneration", "DisarmTraps", "Dodging", "Unarmed", "IdentifyMonster", "Armsmaster",
        "Stealing", "Alchemy", "Learning", "Cover", "ManaShield", "Enlightenment", "Retaliation",
    };
    PartySeed seed;

    for (const char *pClass : {"ArchMage", "DeathKnight", "Assassin", "Shaman", "Seraphim", "Elementalist"})
    {
        Character member = characterWith(pClass, {});
        member.level = 50;
        member.maxHealth = 500;

        for (const std::string &name : SkillNames)
        {
            member.skills[name] = CharacterSkill{name, 20, SkillMastery::Master};
        }

        seed.members.push_back(member);
    }

    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    const SkillTooltipText table = {"Table description.", {"N", "E", "M", "G"}};

    for (const Character &member : party.members())
    {
        for (const std::string &name : SkillNames)
        {
            CAPTURE(member.className);
            CAPTURE(name);
            const SkillTooltipText text = skills.skillTooltip(party, member, name, table);
            CHECK(text.description.find('{') == std::string::npos);

            for (const std::string &line : text.masteryLines)
            {
                CHECK(line.find('{') == std::string::npos);
            }
        }
    }

    // Every stat popup fills its numbers.
    party.setItemTable(&OpenYAMM::Tests::regressionGameData().itemTable);

    for (const char *pStat : {"Might", "Intellect", "Personality", "Endurance", "Accuracy", "Speed", "Luck",
             "HitPoints", "SpellPoints", "ArmorClass", "Attack", "Level", "FireResistance", "AirResistance",
             "WaterResistance", "EarthResistance", "MindResistance", "BodyResistance"})
    {
        CAPTURE(pStat);
        const std::string text = skills.statTooltip(party, party.members()[0], pStat, "Table.");
        CHECK(text.find('{') == std::string::npos);
        CHECK(text.size() > std::string("Table.").size());
    }

    CHECK(skills.statTooltip(party, party.members()[0], "Might", "Table.").starts_with("Table.\n\nMelee and bow"));
    CHECK(skills.statTooltip(party, party.members()[0], "Intellect", "Table.").starts_with("Intellect represents"));
    // Monsters grow with the other worlds' levels, each world's bolster level shown (TXT-2-9); spell points wait on
    // their own drops (TXT-2-10).
    CHECK(withoutColor(skills.statTooltip(party, party.members()[0], "Level", "Table.")).find("bolster level 0 in Enroth")
        != std::string::npos);
    CHECK(skills.statTooltip(party, party.members()[0], "SpellPoints", "Table.").find("spell points last dropped")
        != std::string::npos);
    // Grandmaster Unarmed has no evade under MAW (TXT-2-3).
    CHECK_EQ(skills.skillTooltip(party, party.members()[0], "Unarmed", table).masteryLines[3],
        "Attack +3, speed +2 % per point");
    // Standard adds what a primary stat's value gives; its other rows keep the table's text.
    CHECK(standardSkillRules().statTooltip(party, party.members()[0], "Might", "Table.")
              .starts_with("Table.\n\nMelee damage: "));
    CHECK_EQ(standardSkillRules().statTooltip(party, party.members()[0], "Level", "Table."), "Table.");

    // The resistance rows show their popup's share of hits taken off, green when an item raises the resistance
    // (zzMaw-Stats.lua:870-897); Standard's rows add nothing.
    {
        const std::optional<CharacterResistanceCut> plain =
            skills.resistanceCut(party, party.members()[0], "FireResistance");
        REQUIRE(plain);
        CHECK_FALSE(plain->raisedByItem);
        // The label in the element's colour (zzMaw-Stats.lua:892).
        CHECK_EQ(plain->labelRgb, 0xff4646u);
        party.member(0)->itemResistanceEnchants.fire = 10;
        const std::optional<CharacterResistanceCut> fire =
            skills.resistanceCut(party, party.members()[0], "FireResistance");
        REQUIRE(fire);
        CHECK(fire->raisedByItem);
        CHECK(fire->percent > plain->percent);
        char percent[16] = {};
        std::snprintf(percent, sizeof(percent), "%.1f", fire->percent);
        CHECK_NE(withoutColor(skills.statTooltip(party, party.members()[0], "FireResistance", "Table."))
                .find(std::string("takes ") + percent + " % off fire hits"), std::string::npos);
        party.member(0)->itemResistanceEnchants.fire = 0;
        CHECK_FALSE(skills.resistanceCut(party, party.members()[0], "Might"));
        CHECK_FALSE(standardSkillRules().resistanceCut(party, party.members()[0], "FireResistance"));
    }

    // Weapons append to the table and keep its special where asked; a Death Knight's Blood is its own text.
    const SkillTooltipText mace = skills.skillTooltip(party, party.members()[0], "Mace", table);
    CHECK(mace.description.starts_with("Table description.\n\n"));
    CHECK_EQ(mace.masteryLines[2], "Attack +3 per point; a chance to paralyse for 2 s");
    const SkillTooltipText bow = skills.skillTooltip(party, party.members()[0], "Bow", table);
    // Grandmaster bows shoot fire arrows; the table's "skill added to damage" is not MAW's (TXT-2-2).
    CHECK_EQ(bow.masteryLines[3],
        "Attack +4, speed +2 % per point; shoots fire arrows, dealing the higher of fire and physical damage");
    const SkillTooltipText blood = skills.skillTooltip(party, party.members()[1], "BodyMagic", table);
    CHECK(blood.description.starts_with("Blood, only for Death Knights"));
    CHECK(withoutColor(blood.description).find("16.7 %") != std::string::npos);
    const SkillTooltipText cover = skills.skillTooltip(party, party.members()[0], "Cover", table);
    CHECK(withoutColor(cover.description).find("Current cover chance: 30 %") != std::string::npos);
    // A skill MAW does not describe keeps the table's text, and Standard always does.
    CHECK_EQ(skills.skillTooltip(party, party.members()[0], "Stealing", table).description, table.description);
    CHECK_EQ(standardSkillRules().skillTooltip(party, party.members()[0], "Mace", table).description,
        table.description);
}

TEST_CASE("MAW teachers say MAW's requirement and price")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SkillRules &skills = rules.gameRules().skills;
    CHECK_EQ(skills.teacherSpeech("skill level of 4 with the staff and of course there is my small fee of 2000 gold.",
                 "Staff", SkillMastery::Expert, 6, 3000),
        "skill level of 6 with the staff and of course there is my small fee of 3000 gold.");
    CHECK_EQ(skills.teacherSpeech("Skill level of 7, a Personality of 50 and pay 5000 gold.", "Staff",
                 SkillMastery::Master, 12, 9000),
        "Skill level of 12, a Personality of 50 and pay 9000 gold.");
    // A missing price or requirement is named in an added line.
    CHECK_EQ(skills.teacherSpeech("skill level of 7, I will teach you Mastery of the mace.", "Mace",
                 SkillMastery::Master, 12, 9000),
        "skill level of 12, I will teach you Mastery of the mace.\n\nYou need at least 12 skill and 9000 gold.");
    CHECK_EQ(skills.teacherSpeech("fee of 8000, I will teach you.", "Staff", SkillMastery::Grandmaster, 20, 20000),
        "fee of 20000, I will teach you.\n\nYou need at least 20 skill and 20000 gold.");
    CHECK_EQ(standardSkillRules().teacherSpeech("fee of 8000.", "Staff", SkillMastery::Grandmaster, 20, 20000),
        "fee of 8000.");
    // Only the horizontal skills' speeches are rewritten (S:1886-1889).
    CHECK_EQ(skills.teacherSpeech("fee of 8000.", "Merchant", SkillMastery::Grandmaster, 20, 20000), "fee of 8000.");
}

TEST_CASE("a cover flashes the Shield spell on the protected member's portrait, as MAW shows it")
{
    // MAW plays the Shield buff animation (SetPlayerBuffAnim, icon spell17) on the member the blow was meant for and
    // face animation 14 on the coverer (zzMaw-Monsters.lua:3970-3971).
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/data_tables/portrait_fx_events.txt");
    REQUIRE(file.good());
    std::vector<std::vector<std::string>> rows;

    for (std::string line; std::getline(file, line);)
    {
        std::vector<std::string> row;
        std::stringstream fields(line);

        for (std::string field; std::getline(fields, field, '\t');)
        {
            row.push_back(field);
        }

        rows.push_back(row);
    }

    PortraitFxEventTable table;
    REQUIRE(table.loadFromRows(rows));
    const PortraitFxEventEntry *pCover = table.findByKind(PortraitFxEventKind::Cover);
    REQUIRE(pCover != nullptr);
    CHECK_EQ(pCover->animationName, "spell17");
    CHECK_FALSE(pCover->faceAnimationId.has_value());
}

TEST_CASE("MAW skill popups preview what one more point does to the power rows, when the point can be bought")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    // MAW's item bases, so the sword's blows are MAW's.
    std::ifstream itemsInput(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/items.yml");
    const std::string itemsYaml((std::istreambuf_iterator<char>(itemsInput)), std::istreambuf_iterator<char>());
    MawItemData items;
    std::string error;
    REQUIRE_MESSAGE(items.loadFromYaml(itemsYaml, error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, items);
    rules.setSpellTable(&gameData.spellTable);
    rules.setItemTable(&gameData.itemTable);
    Character knight = characterWith("Knight", {{"Sword", 10}, {"Armsmaster", 10}, {"Bodybuilding", 10}});
    knight.skills["Sword"].mastery = SkillMastery::Master;
    knight.skills["Armsmaster"].mastery = SkillMastery::Expert;
    knight.skills["Bodybuilding"].mastery = SkillMastery::Expert;
    knight.level = 30;
    knight.might = knight.intellect = knight.personality = knight.endurance = 50;
    knight.accuracy = knight.speed = knight.luck = 50;
    knight.equipment.mainHand = 15;
    knight.skillPoints = 100;
    Character mage = characterWith("Sorcerer", {{"FireMagic", 10}});
    mage.skills["FireMagic"].mastery = SkillMastery::Master;
    mage.level = 30;
    mage.might = mage.intellect = mage.personality = mage.endurance = 50;
    mage.accuracy = mage.speed = mage.luck = 50;
    mage.knownSpellIds = {1, 6, 11};
    mage.skillPoints = 100;
    PartySeed seed;
    seed.members.push_back(knight);
    seed.members.push_back(mage);
    // Wired as the game wires a party (tests/PartySpellTestHarness.h), so a raise recomputes HP and the blows.
    Party party;
    party.setItemTable(&gameData.itemTable);
    party.setCharacterDollTable(&gameData.characterDollTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);
    party.setClassMultiplierTable(&gameData.classMultiplierTable);
    party.setClassSkillTable(&gameData.classSkillTable);
    party.seed(seed);
    party.setRules(&rules.gameRules());
    party.refreshMemberResources(0);
    const SkillRules &skills = rules.gameRules().skills;
    const SkillTooltipText table = {"Table.", {"N", "E", "M", "G"}};
    const auto footer = [&](const char *pSkill, size_t memberIndex = 0)
    {
        return skills.skillTooltip(party, party.members()[memberIndex], pSkill, table).footer;
    };

    // Body Building changes only Vitality; Armsmaster the melee blows.
    const std::string bodybuilding = footer("Bodybuilding");
    CAPTURE(bodybuilding);
    CHECK_NE(bodybuilding.find("With one more point:"), std::string::npos);
    CHECK_NE(bodybuilding.find("Vitality: "), std::string::npos);
    CHECK_EQ(bodybuilding.find("Melee Power"), std::string::npos);
    const std::string armsmaster = footer("Armsmaster");
    CAPTURE(armsmaster);
    CHECK_NE(armsmaster.find("Melee Power: "), std::string::npos);
    CHECK_EQ(armsmaster.find("Vitality"), std::string::npos);

    // A school's point with no spell of the school to measure assumes the strongest known damage spell (Incinerate,
    // not Fireball and never Torch Light); the member's own spell of the school is measured as it is.
    const std::string assumed = footer("FireMagic", 1);
    CAPTURE(assumed);
    CHECK_NE(assumed.find("Spell Power (Incinerate): "), std::string::npos);
    party.member(1)->quickSpellName = "Fireball";
    const std::string own = footer("FireMagic", 1);
    CAPTURE(own);
    CHECK_NE(own.find("Spell Power: "), std::string::npos);
    CHECK_EQ(own.find("Incinerate"), std::string::npos);

    // Without the points for the next raise there is no preview.
    party.member(0)->skillPoints = 0;
    CHECK_EQ(footer("Bodybuilding").find("With one more point"), std::string::npos);
}
