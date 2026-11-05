#include "doctest/doctest.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSkillFormulas.h"
#include "game/rules/maw/MawSpellFormulas.h"
#include "game/rules/maw/MawTexts.h"
#include "game/tables/SpellTable.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "tests/PartySpellTestHarness.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <memory>
#include <random>
#include <sstream>
#include <string>
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

// The tables of devdocs/maw/CLASSES_SPELLS_SPEC.md §1-4.
TEST_CASE("MAW Ascension grows Fire Bolt as the worked example shows")
{
    struct Step
    {
        double ascension;
        SkillMastery mastery;
        int diceMax;
        int add;
        int cost;
        int delay;
    };
    // Fire Bolt (8 + 1-2 per point) at Fire 20 GM, cost 2, delay 90, Personality ignored (§2.4).
    const std::array<Step, 6> steps = {{
        {0, SkillMastery::None, 1, 6, 2, 90},
        {5, SkillMastery::Normal, 2, 8, 4, 97},
        {10, SkillMastery::Expert, 2, 14, 5, 104},
        {20, SkillMastery::Grandmaster, 3, 42, 8, 121},
        {30, SkillMastery::Grandmaster, 4, 101, 16, 141},
        {50, SkillMastery::Grandmaster, 8, 392, 52, 189},
    }};

    for (const Step &step : steps)
    {
        CAPTURE(step.ascension);
        const MawSpellDice dice = mawAscendedSpellDice({1, 2, 8}, step.ascension);
        CHECK_EQ(dice.diceMax, step.diceMax);
        CHECK_EQ(dice.add, step.add);
        CHECK_EQ(mawSpellManaCost(MawSpellCategory::Damage, 2, step.ascension, step.mastery, 1.0), step.cost);
        MawSpellDelayInputs delay;
        delay.tableDelay = 90;
        delay.ascensionSkill = step.ascension;
        CHECK_EQ(mawSpellDelay(delay), step.delay);
    }

    // Personality cheapens spells against the party's banked level (§1.1).
    CHECK(mawPersonalityCostFactor(100, 100) == doctest::Approx(0.939).epsilon(0.001));
    CHECK(mawPersonalityCostFactor(300, 200) == doctest::Approx(0.872).epsilon(0.001));
    CHECK(mawPersonalityCostFactor(1000, 1000) == doctest::Approx(0.866).epsilon(0.001));
    CHECK(mawPersonalityCostFactor(2000, 1000) == doctest::Approx(0.750).epsilon(0.001));
}

TEST_CASE("MAW heals match the healing examples")
{
    // Heal GM at Body 20: 136, 197, 328 and 550 HP at Ascension 0, 10, 20 and 30, costing 8, 20, 31 and 62 (§1.6).
    const std::optional<MawHealSpell> heal = mawHealSpell(68, SkillMastery::Grandmaster, false);
    REQUIRE(heal);
    const std::array<double, 4> ascension = {0, 10, 20, 30};
    const std::array<SkillMastery, 4> masteries = {
        SkillMastery::None, SkillMastery::Expert, SkillMastery::Grandmaster, SkillMastery::Grandmaster};
    const std::array<int, 4> amounts = {136, 197, 328, 550};
    const std::array<int, 4> costs = {8, 20, 31, 62};

    for (size_t step = 0; step < ascension.size(); ++step)
    {
        CAPTURE(ascension[step]);
        CHECK_EQ(int(std::round(mawHealAmount(*heal, 20, ascension[step], 0, 100))), amounts[step]);
        CHECK_EQ(mawSpellManaCost(MawSpellCategory::Heal, heal->cost, ascension[step], masteries[step], 1.0),
            costs[step]);
    }

    // Greater Heal GM at Body 30.
    const std::optional<MawHealSpell> greaterHeal = mawHealSpell(74, SkillMastery::Grandmaster, false);
    REQUIRE(greaterHeal);
    const std::array<int, 4> greaterAmounts = {340, 513, 839, 1375};

    for (size_t step = 0; step < ascension.size(); ++step)
    {
        CHECK_EQ(int(std::round(mawHealAmount(*greaterHeal, 30, ascension[step], 0, 100))), greaterAmounts[step]);
    }

    // Personality multiplies the heal: 200 at level 100 x1.154, 1000 at 500 x1.40, 2000 at 1000 x1.50.
    const MawHealSpell flat = {0, 1000, 0};
    CHECK(mawHealAmount(flat, 0, 0, 200, 100) == doctest::Approx(1153.8).epsilon(0.001));
    CHECK(mawHealAmount(flat, 0, 0, 1000, 500) == doctest::Approx(1400));
    CHECK(mawHealAmount(flat, 0, 0, 2000, 1000) == doctest::Approx(1500));
    CHECK_FALSE(mawHealSpell(74, SkillMastery::Expert, false));
}

TEST_CASE("MAW auras reserve mana and grow as the aura tables show")
{
    // Reserved percent by class SP factor (§3.2), Enlightenment Grandmaster adding 2 to the factor.
    CHECK(mawAuraReservedPercent(60, 1, 0) == doctest::Approx(60));
    CHECK(mawAuraReservedPercent(60, 3, 0) == doctest::Approx(20));
    CHECK(mawAuraReservedPercent(75, 4, 0) == doctest::Approx(18.75));
    CHECK(mawAuraReservedPercent(90, 8, 0) == doctest::Approx(11.25));
    CHECK(mawAuraReservedPercent(200, 3, 0) == doctest::Approx(66.67).epsilon(0.001));
    CHECK(mawAuraReservedPercent(300, 6, 4) == doctest::Approx(37.5));
    CHECK(mawAuraReservedPercent(150, 6, 4) == doctest::Approx(mawAuraReservedPercent(150, 8, 0)));
    // An Arch Mage holding Haste, Shield, Stone Skin, Heroism and Fire Resistance reserves 75 %.
    double archMage = 0;

    for (const uint32_t spellId : {5u, 17u, 38u, 51u, 3u})
    {
        const MawAura *pAura = mawAura(spellId);
        REQUIRE(pAura != nullptr);
        archMage += mawAuraReservedPercent(pAura->cost, 6, 0);
    }

    CHECK(archMage == doctest::Approx(75));
    // Utility auras reserve flat mana.
    CHECK_EQ(mawUtilityAuraReservation(5, 0), 5);
    CHECK_EQ(mawUtilityAuraReservation(20, 0), 20);
    CHECK_EQ(mawUtilityAuraReservation(20, 4), 12);

    // Flat buffs: resistance (10 + L/4), armour and attack (20 + L/4), Day of Protection at skill / 1.4 (§3.3).
    CHECK(mawAuraFlat(10, 2, 40, 7) == doctest::Approx(22.8));
    CHECK(mawAuraFlat(20, 2, 40, 7) == doctest::Approx(34.2));
    CHECK(mawAuraFlat(10, 2, 40, 7 / 1.4) == doctest::Approx(22.0));
    CHECK(mawAuraFlat(10, 2, 100, 30) == doctest::Approx(56));
    CHECK(mawAuraFlat(20, 2, 400, 50) == doctest::Approx(240));
    CHECK(mawAuraFlat(10, 2, 400, 75 / 1.4) == doctest::Approx(227.9).epsilon(0.001));

    // Multiplier buffs and the stat percents at skill 0 to 50.
    const std::array<double, 6> skills = {0, 10, 20, 30, 40, 50};

    for (size_t index = 0; index < skills.size(); ++index)
    {
        CAPTURE(skills[index]);
        CHECK(mawBuffMultiplier(5, skills[index]) == doctest::Approx(0.10 + 0.02 * double(index)));
        CHECK(mawBuffMultiplier(17, skills[index]) == doctest::Approx(0.15 + 0.03 * double(index)));
        CHECK(mawBuffMultiplier(47, skills[index]) == doctest::Approx(0.05 + 0.01 * double(index)));
        CHECK(mawAuraStatPercent(skills[index], false) == doctest::Approx(10 + 2 * double(index)));
    }

    CHECK(mawAuraStatPercent(50, true) == doctest::Approx(17.14).epsilon(0.001));
}

TEST_CASE("MAW Meditation and Regeneration auras match the aura table")
{
    // Holder level 40, skill 7 (estimated skill 9.8): Meditation at max SP 300 / 1000 / 3000, Regeneration at
    // max HP 500 / 2000 / 8000; holder level 100, skill 30 (estimated skill 19.1) (§3.4).
    CHECK(mawMeditationAuraSpellPerSecond(300, 9.8, 7) == doctest::Approx(3.2).epsilon(0.02));
    CHECK(mawMeditationAuraSpellPerSecond(3000, 9.8, 7) == doctest::Approx(5.7).epsilon(0.02));
    CHECK(mawMeditationAuraSpellPerSecond(1000, 19.1, 30) == doctest::Approx(12.8).epsilon(0.02));
    CHECK(mawRegenerationAuraHealthPerSecond(500, 40, 7) == doctest::Approx(3.3).epsilon(0.02));
    CHECK(mawRegenerationAuraHealthPerSecond(8000, 40, 7) == doctest::Approx(13.0).epsilon(0.02));
    CHECK(mawRegenerationAuraHealthPerSecond(2000, 100, 30) == doctest::Approx(29.6).epsilon(0.02));
}

TEST_CASE("MAW crowd control lasts as the duration table shows")
{
    struct Row
    {
        uint32_t spellId;
        std::array<double, 5> seconds;
    };
    // Real seconds for a party, first cast, non-boss: N asc 0 res 0; GM asc 0 res 0; GM asc 20 res 0; GM asc 20
    // res 50; GM asc 50 res 100 (§4.2).
    const std::array<Row, 7> rows = {{
        {35, {6.0, 12.0, 16.2, 10.8, 12.6}},
        {60, {10.0, 20.0, 26.9, 18.0, 21.1}},
        {62, {4.5, 9.0, 12.1, 8.1, 9.5}},
        {63, {3.0, 6.0, 8.1, 5.4, 6.3}},
        {66, {5.0, 10.0, 13.5, 9.0, 10.5}},
        {92, {8.0, 8.0, 10.8, 7.2, 8.4}},
        {122, {4.0, 8.0, 8.0, 8.0, 8.0}},
    }};
    const std::array<SkillMastery, 5> masteries = {SkillMastery::Normal, SkillMastery::Grandmaster,
        SkillMastery::Grandmaster, SkillMastery::Grandmaster, SkillMastery::Grandmaster};
    const std::array<double, 5> ascension = {0, 0, 20, 20, 50};
    const std::array<int, 5> resistances = {0, 0, 0, 50, 100};

    for (const Row &row : rows)
    {
        const MawCrowdControlSpell *pSpell = mawCrowdControlSpell(row.spellId);
        REQUIRE(pSpell != nullptr);

        for (size_t column = 0; column < row.seconds.size(); ++column)
        {
            CAPTURE(row.spellId);
            CAPTURE(column);
            // Dragon Fear follows its mastery only, without Ascension or resistance.
            const double seconds = 2
                * mawCrowdControlMinutes(*pSpell, masteries[column], ascension[column], resistances[column], false);
            CHECK(seconds == doctest::Approx(row.seconds[column]).epsilon(0.005));
        }
    }

    // A party of one holds monsters twice as long.
    CHECK(mawCrowdControlMinutes(*mawCrowdControlSpell(35), SkillMastery::Normal, 0, 0, true) == doctest::Approx(6));
}

TEST_CASE("MAW diminishing returns shorten recasts and then make monsters immune")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    Character caster;
    caster.className = "Cleric";

    const auto cast = [&](uint64_t target, double nowSeconds, bool boss)
    {
        // Turn Undead at Master: 8 s, a group-2 crowd control.
        CrowdControlCast spell;
        spell.spellId = 48;
        spell.mastery = SkillMastery::Master;
        spell.skillLevel = 10;
        spell.pCaster = &caster;
        spell.boss = boss;
        spell.targetKey = target;
        spell.partySize = 4;
        spell.nowSeconds = nowSeconds;
        return spells.crowdControlSeconds(spell).value_or(-1);
    };

    // Recast the moment it ends: 8 s, 4 s, then immune for 9 s, then 2 s (§4.3).
    CHECK(cast(1, 0, false) == doctest::Approx(8));
    CHECK(cast(1, 8, false) == doctest::Approx(4));
    CHECK(cast(1, 12, false) == doctest::Approx(0));
    CHECK(cast(1, 20, false) == doctest::Approx(0));
    CHECK(cast(1, 21, false) == doctest::Approx(2));

    // On a boss: 4, 3, 2, 1, 1, 1 s, then immunity.
    const std::array<float, 6> bossSeconds = {4, 3, 2, 1, 1, 1};
    double now = 1000;

    for (const float expected : bossSeconds)
    {
        const float seconds = cast(2, now, true);
        CHECK(seconds == doctest::Approx(expected));
        now += seconds;
    }

    CHECK(cast(2, now, true) == doctest::Approx(0));
    // Another monster has its own history.
    CHECK(cast(3, now, false) == doctest::Approx(8));
}

TEST_CASE("MAW spell texts fill every number for mages, Death Knights and Assassins")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/texts.yml");
    std::ostringstream yaml;
    yaml << input.rdbuf();
    MawTextData textData;
    std::string error;
    REQUIRE_MESSAGE(textData.loadFromYaml(yaml.str(), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, {}, {}, {}, textData);

    const auto member = [](const std::string &name, const std::string &className)
    {
        Character character;
        character.name = name;
        character.className = className;
        character.level = 60;
        character.maxHealth = 400;

        for (const char *pSkill : {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic",
                 "BodyMagic", "LightMagic", "DarkMagic", "DarkElf", "Vampire", "Dragon", "Learning"})
        {
            character.skills[pSkill] = CharacterSkill{pSkill, 20, SkillMastery::Grandmaster};
        }

        return character;
    };
    PartySeed seed;
    seed.members = {member("Ann", "ArchMage"), member("Bors", "DeathKnight"), member("Cid", "Assassin")};
    Party party;
    party.setItemTable(&gameData.itemTable);
    party.setClassMultiplierTable(&gameData.classMultiplierTable);
    party.seed(seed);
    party.setRules(&rules.gameRules());
    const SpellRules &spells = rules.gameRules().spells;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        for (const SpellEntry &spell : gameData.spellTable.entries())
        {
            CAPTURE(memberIndex);
            CAPTURE(spell.id);
            const SpellTooltipText text = spells.spellTooltip(party, *party.member(memberIndex), spell);
            CHECK(text.description.find('{') == std::string::npos);

            for (const std::string &line : text.masteryLines)
            {
                CHECK(line.find('{') == std::string::npos);
            }
        }
    }

    // Fire Bolt names its ascended dice; Vampiric Weapon is an aura under another name, held by nobody yet.
    const SpellTooltipText fireBolt = spells.spellTooltip(party, *party.member(0), *gameData.spellTable.findById(2));
    CHECK(fireBolt.description.find("+ 1-") != std::string::npos);
    CHECK(fireBolt.description.find("Recovery time: ") != std::string::npos);
    const SpellTooltipText vampiric = spells.spellTooltip(party, *party.member(0), *gameData.spellTable.findById(91));
    CHECK_EQ(vampiric.name, "Vampiric Aura");
    // Invisibility's durations, Fly's attack rule and Shrinking Ray's splash say MAW's rules (FSPS-2-4).
    const SpellTooltipText invisibility =
        spells.spellTooltip(party, *party.member(0), *gameData.spellTable.findById(19));
    CHECK(invisibility.masteryLines[2].find("1.5 minutes per point") != std::string::npos);
    CHECK(invisibility.masteryLines[3].find("3 minutes per point") != std::string::npos);
    CHECK(spells.spellTooltip(party, *party.member(0), *gameData.spellTable.findById(21)).description.find(
              "attacking a monster ends it") != std::string::npos);
    const SpellTooltipText shrinkingRay =
        spells.spellTooltip(party, *party.member(0), *gameData.spellTable.findById(92));
    CHECK(shrinkingRay.masteryLines[1].find("1 more monster") != std::string::npos);
    CHECK(shrinkingRay.masteryLines[3].find("3 more monsters") != std::string::npos);
    CHECK(withoutColor(vampiric.description).find("% of maximum spell points") != std::string::npos);
    CHECK(withoutColor(vampiric.description).find("Not held") != std::string::npos);
    CHECK(vampiric.masteryLines[3].empty());
    const SpellTooltipText icyTouch = spells.spellTooltip(party, *party.member(1), *gameData.spellTable.findById(26));
    CHECK_EQ(icyTouch.name, "Icy Touch");
    CHECK(withoutColor(icyTouch.description).find("120 % of your weapon damage") != std::string::npos);
    const SpellTooltipText fireball = spells.spellTooltip(party, *party.member(2), *gameData.spellTable.findById(6));
    CHECK(fireball.description.find("Needs 5 combo points.") != std::string::npos);

    // Standard keeps the table's text.
    const SpellTooltipText standard =
        standardGameRules().spells.spellTooltip(party, *party.member(0), *gameData.spellTable.findById(91));
    CHECK_EQ(standard.name, gameData.spellTable.findById(91)->name);
    CHECK_EQ(standard.description, gameData.spellTable.findById(91)->description);
}

TEST_CASE("MAW spell text placeholders scale and keep decimals")
{
    const std::unordered_map<std::string, double> values = {{"dice", 7.4}, {"percent", 12.26}};
    CHECK_EQ(mawFillText("1-{dice} {percent:1} % {dice*2} {missing}", values), "1-7 12.3 % 15 {missing}");
    CHECK_EQ(mawFillText("{percent:1}", {{"percent", 20.0}}), "20");
}

TEST_CASE("MAW Mass Distortion takes a share of the target's hit points, less on harder difficulties")
{
    SpellEntry massDistortion;
    massDistortion.id = 44;
    Character caster;
    CharacterSpellCast cast;
    cast.pCaster = &caster;
    cast.pSpell = &massDistortion;
    cast.mastery = SkillMastery::Grandmaster;
    cast.skillLevel = 10;
    ActorRulesetFacts facts;
    facts.level = 100;
    const SpellTargetState target = {10000, 20000, &facts};

    // 20 % of the current 10000 at MAW difficulty; Hell divides by the root of 1.8.
    MawRules maw(RulesetOptions{}, MawMapLevels{});
    CHECK_EQ(maw.gameRules().combat.spellDamageOnTarget(cast, target).value_or(0), 2000);
    RulesetOptions hell;
    hell.difficulty = RulesetDifficulty::Hell;
    MawRules hellRules(hell, MawMapLevels{});
    CHECK_EQ(hellRules.gameRules().combat.spellDamageOnTarget(cast, target).value_or(0), 1491);
    // Doom: 3.33 (1 + 100 / 75), and a boss twice (1 + 100 / 80) more.
    RulesetOptions doom;
    doom.challengeMode = RulesetChallengeMode::Doom;
    MawRules doomRules(doom, MawMapLevels{});
    CHECK_EQ(doomRules.gameRules().combat.spellDamageOnTarget(cast, target).value_or(0), 717);
    facts.bossAffix = 1;
    CHECK_EQ(doomRules.gameRules().combat.spellDamageOnTarget(cast, target).value_or(0), 338);

    // Other spells roll as usual; Standard takes its own 25 % + 2 % per point (45 % of 10000).
    massDistortion.id = 2;
    CHECK_FALSE(maw.gameRules().combat.spellDamageOnTarget(cast, target).has_value());
    CHECK_FALSE(standardGameRules().combat.spellDamageOnTarget(cast, target).has_value());
    massDistortion.id = 44;
    CHECK_EQ(standardGameRules().combat.spellDamageOnTarget(cast, target).value_or(0), 4500);
}

TEST_CASE("MAW Chain Lightning leaps to the nearest living hostile monster, one mastery lower")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    const auto monster = [](float x, bool hostile, bool dead)
    {
        GameplayRuntimeActorState actor;
        actor.preciseX = x;
        actor.radius = 30;
        actor.height = 100;
        actor.currentHp = dead ? 0 : 50;
        actor.isDead = dead;
        actor.hostileToParty = hostile;
        return actor;
    };
    const size_t struck = world.addActor(monster(0, true, false));
    world.addActor(monster(100, false, false));
    world.addActor(monster(150, true, true));
    world.addActor(monster(400, true, false));
    world.addActor(monster(1000, true, false));

    GameplayProjectileService service;
    GameplayProjectileService::ProjectileState bolt;
    bolt.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Party;
    bolt.spellId = 18;
    bolt.skillMastery = uint32_t(SkillMastery::Grandmaster);
    bolt.damage = 120;
    bolt.velocityX = 1500;

    // It passes the peasant and the corpse for the hostile monster at 400; 1000 is out of reach.
    const std::optional<GameplayProjectileService::ProjectileSpawnRequest> leap =
        service.buildChainSpawnRequest(bolt, rules.gameRules().combat, world, struck);
    REQUIRE(leap.has_value());
    CHECK(leap->targetX == doctest::Approx(400));
    CHECK_EQ(leap->skillMastery, uint32_t(SkillMastery::Master));
    CHECK_EQ(leap->damage, 120);
    CHECK(leap->definition.speed == doctest::Approx(1500));

    // A Novice bolt stops; other spells and Standard never leap.
    bolt.skillMastery = uint32_t(SkillMastery::Normal);
    CHECK_FALSE(service.buildChainSpawnRequest(bolt, rules.gameRules().combat, world, struck).has_value());
    bolt.skillMastery = uint32_t(SkillMastery::Grandmaster);
    CHECK_FALSE(service.buildChainSpawnRequest(bolt, standardGameRules().combat, world, struck).has_value());
    bolt.spellId = 2;
    CHECK_FALSE(service.buildChainSpawnRequest(bolt, rules.gameRules().combat, world, struck).has_value());
}

TEST_CASE("MAW Fire Aura and damage enchantments scale with the weapon's level damage")
{
    // Grandmaster burns a quarter of the level damage, at least 24 (48 two-handed); Novice a tenth, at least 3.
    CHECK(mawFireAuraDamage(4, 400, false) == doctest::Approx(100));
    CHECK(mawFireAuraDamage(4, 40, false) == doctest::Approx(24));
    CHECK(mawFireAuraDamage(4, 40, true) == doctest::Approx(48));
    CHECK(mawFireAuraDamage(1, 100, false) == doctest::Approx(10));
    CHECK(mawFireAuraDamage(0, 400, false) == doctest::Approx(0));

    // "of Cold" (3-4, 20 %) on level damage 70: an average of 14 split in the table's proportions.
    MawEnchantRange cold = mawEnchantDamageRange(70, 3, 4, 0.2, false);
    CHECK(cold.minimum == doctest::Approx(12));
    CHECK(cold.maximum == doctest::Approx(16));
    // A low-level weapon keeps half the table's range, all of it two-handed.
    cold = mawEnchantDamageRange(0, 3, 4, 0.2, false);
    CHECK(cold.minimum == doctest::Approx(1.5));
    CHECK(cold.maximum == doctest::Approx(2));
    cold = mawEnchantDamageRange(0, 3, 4, 0.2, true);
    CHECK(cold.minimum == doctest::Approx(3));
    CHECK(cold.maximum == doctest::Approx(4));

    RulesetOptions options;
    CHECK_EQ(mawBolsterAmount(options), 100);
    options.difficulty = RulesetDifficulty::Nightmare;
    CHECK_EQ(mawBolsterAmount(options), 300);
    options.challengeMode = RulesetChallengeMode::Doom;
    CHECK_EQ(mawBolsterAmount(options), 600);
}

TEST_CASE("MAW weapon paralysis shares Paralyze's diminishing returns and Protection from Magic keeps members up")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});

    // A four-second mace stun, recast as it ends: a fifth of the window spent paralysed cuts the next to 3 s; a
    // group-1 effect passes through and a boss takes half.
    CHECK(rules.diminishedCrowdControlSeconds(7, 3, 0, 4, false) == doctest::Approx(4));
    CHECK(rules.diminishedCrowdControlSeconds(7, 3, 4, 4, false) == doctest::Approx(3));
    CHECK(rules.diminishedCrowdControlSeconds(7, 1, 4, 4, false) == doctest::Approx(4));
    CHECK(rules.diminishedCrowdControlSeconds(8, 3, 0, 4, true) == doctest::Approx(2));

    PartySeed seed;
    Character member;
    member.className = "Knight";
    seed.members = {member};
    Party party;
    party.seed(seed);
    const CombatRules &combat = rules.gameRules().combat;
    CHECK_FALSE(combat.blocksMonsterCondition(party, CharacterCondition::Unconscious));
    party.applyPartyBuff(PartyBuffId::ProtectionFromMagic, 600, 1, 75, 10, SkillMastery::Master, 0);
    CHECK(combat.blocksMonsterCondition(party, CharacterCondition::Unconscious));
    CHECK_FALSE(combat.blocksMonsterCondition(party, CharacterCondition::Asleep));
    CHECK_FALSE(standardGameRules().combat.blocksMonsterCondition(party, CharacterCondition::Unconscious));
}

TEST_CASE("MAW Shrinking Ray and Dark Grasp cut a monster's damage by 30 percent")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character member;
    member.className = "Knight";
    const auto recomputed = [&](bool debuffed)
    {
        std::mt19937 rng(11);
        CharacterDamageHit hit;
        hit.amount = 40;
        hit.rolledAmount = 40;
        hit.pCharacter = &member;
        hit.monsterAttack = true;
        hit.attackerFacts.level = 40;
        hit.attackerFacts.attack1Damage = 200;
        hit.attackerDebuffed = debuffed;
        hit.pRng = &rng;
        std::vector<DamageStageRecord> records;
        rules.gameRules().combat.damageToCharacterStages().run(hit, &records);
        const auto stage = std::find_if(records.begin(), records.end(),
            [](const DamageStageRecord &record) { return record.stage == "damage-recompute"; });
        REQUIRE(stage != records.end());
        return stage->after;
    };

    CHECK(recomputed(true) == doctest::Approx(recomputed(false) * 0.7).epsilon(0.01));
}
