#include "doctest/doctest.h"
#include "engine/TextTable.h"
#include "game/items/AlchemyBenchRuntime.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/PotionEffectTable.h"
#include "tests/RegressionGameData.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

// MAW's potions (devdocs/maw/CLASSES_SPELLS_SPEC.md §7): rulesets/maw/content/potion_effects.yml and the drink path.
namespace
{
PotionEffectTable mawPotionEffects()
{
    std::ifstream input(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/content/potion_effects.yml");
    std::ostringstream text;
    text << input.rdbuf();
    PotionEffectTable effects;
    std::string error;
    REQUIRE_MESSAGE(effects.loadFromYaml(text.str(), error), error);
    return effects;
}

Party mawParty(const MawRules &rules)
{
    Character member = {};
    member.name = "Drinker";
    member.level = 50;
    member.maxHealth = 100000;
    member.health = 1;
    member.maxSpellPoints = 100000;
    member.spellPoints = 0;
    member.birthYear = CharacterAgeReferenceYear - 30;
    PartySeed seed = {};
    seed.members = {member, member};
    Party party = {};
    party.seed(seed);
    party.setRules(&rules.gameRules());
    return party;
}

struct Drink
{
    InventoryItemUseResult result;
    InventoryItem potion;
};

Drink drink(Party &party, const MergedPotionSettingTable &potions, uint32_t itemId, int power, uint16_t charges = 0,
    bool enemiesNear = false)
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    Drink drink;
    drink.potion.objectDescriptionId = itemId;
    drink.potion.standardEnchantPower = uint16_t(power);
    drink.potion.currentCharges = charges;
    InventoryItemUseContext context;
    context.enemiesNear = enemiesNear;
    drink.result = InventoryItemUseRuntime::useItemOnMember(
        party, 0, drink.potion, gameData.itemTable, &gameData.readableScrollTable, &potions, nullptr, context);
    return drink;
}
}

TEST_CASE("MAW potion effects load with MAW's drinking rules")
{
    const PotionEffectTable effects = mawPotionEffects();
    CHECK_EQ(effects.powerCap(), 500);
    CHECK_EQ(effects.timedSecondsPerPower(), 0.0f);
    CHECK_EQ(effects.fixedDurationSeconds(), 6 * 3600.0f);
    CHECK_EQ(effects.grandmasterAlchemySecondsPerSkill(), 360.0f);
    CHECK_EQ(effects.soloDurationSeconds(), 24 * 3600.0f);
    CHECK_EQ(effects.combatRecoveryTicks(), 60.0f);
    CHECK(effects.combatRecoveryOnlyNearEnemies());
    CHECK(effects.allRecipesKnown());
    REQUIRE(effects.find(231) != nullptr);
    CHECK_EQ(effects.find(231)->minimumPower, 20);
    CHECK_EQ(effects.find(231)->charges, 5);
    CHECK(effects.find(231)->rechargeable);
    CHECK_FALSE(effects.find(228)->rechargeable);
    CHECK(effects.find(238)->itemAction == PotionItemAction::Crafting);
    CHECK(effects.find(221) == nullptr);
    CHECK(effects.find(264) == nullptr);
}

TEST_CASE("MAW potion auras cast at the strength of CLASSES_SPELLS_SPEC §7.4")
{
    // Power 10: f 0.79, skill -10.6, level 3.9; Haste 7.9 %, Stone Skin 16.5 AC.
    CHECK(mawPotionAuraSkill(5, 10) == doctest::Approx(-10.625));
    CHECK(mawPotionAuraLevel(10) == doctest::Approx(3.9375));
    CHECK(mawBuffMultiplier(5, mawPotionAuraSkill(5, 10)) == doctest::Approx(0.07875));
    CHECK(mawAuraFlat(20, 2, mawPotionAuraLevel(10), mawPotionAuraSkill(38, 10))
        == doctest::Approx(16.5).epsilon(0.01));
    // Power 100: Stone Skin 38.3; Heroism 16.9 %. Day of Protection: wide span, skill / 1.4, at the live buffPower
    // base of 20 (zzMaw_Mapping.lua replaces the base of 10 in zzMaw-Spells.lua on every map load, which the spec's
    // 27.1 used).
    CHECK(mawAuraFlat(20, 2, mawPotionAuraLevel(100), mawPotionAuraSkill(38, 100))
        == doctest::Approx(38.3).epsilon(0.01));
    CHECK(mawBuffMultiplier(51, mawPotionAuraSkill(51, 100)) == doctest::Approx(0.16875));
    CHECK(mawAuraFlat(20, 2, mawPotionAuraLevel(100), mawPotionAuraSkill(85, 100) / 1.4)
        == doctest::Approx(38.3).epsilon(0.01));
    // Power 200 and above: skill 25 (multipliers stop), the level keeps growing (flat buffs do not).
    CHECK(mawPotionAuraSkill(5, 500) == doctest::Approx(25));
    CHECK(mawAuraFlat(20, 2, mawPotionAuraLevel(500), mawPotionAuraSkill(38, 500))
        == doctest::Approx(170.6).epsilon(0.01));
}

TEST_CASE("a MAW potion aura and the party's aura never add: the stronger counts")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character drinker;
    drinker.rulesetState.potionEffects.push_back({TimedPotionEffect::Kind::Aura, 5, 100, 600});
    Character other;

    // No party aura: the drinker alone hastes at the potion's skill.
    CHECK(rules.auraSkill(5, &drinker).value_or(-99) == doctest::Approx(mawPotionAuraSkill(5, 100)));
    CHECK_FALSE(rules.auraSkill(5, &other).has_value());

    // A party aura at skill 20 beats a power-100 potion (skill 6.25), and a power-200 potion (25) beats it.
    MawAuraSource aura;
    aura.skill = 20;
    aura.mastery = 4;
    aura.level = 60;
    rules.setActiveAuras({{5, aura}});
    CHECK(rules.auraSkill(5, &drinker).value_or(0) == doctest::Approx(20));
    drinker.rulesetState.potionEffects.front().amount = 200;
    CHECK(rules.auraSkill(5, &drinker).value_or(0) == doctest::Approx(25));
    CHECK(rules.auraSkill(5, &other).value_or(0) == doctest::Approx(20));
}

TEST_CASE("MAW potions: power cap and requirement, charges, combat recovery and best steps")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    MergedPotionSettingTable potions = OpenYAMM::Tests::regressionGameData().mergedPotionSettingTable;
    potions.setEffects(mawPotionEffects());
    Party party = mawParty(rules);

    // Stone to Flesh needs power 20: refused and kept below it.
    Drink weak = drink(party, potions, 239, 19);
    CHECK_FALSE(weak.result.consumed);
    CHECK_EQ(weak.result.statusText, "This potion has not enough power");

    // Haste: five drinks per bottle, its aura for six hours at the power drunk.
    Drink haste = drink(party, potions, 228, 120);
    CHECK(haste.result.handled);
    CHECK_FALSE(haste.result.consumed);
    CHECK_EQ(haste.result.potionUsesLeft.value_or(0), 4u);
    CHECK_EQ(party.members()[0].rulesetState.potionEffect(TimedPotionEffect::Kind::Aura, 5), 120);
    CHECK_EQ(party.members()[0].rulesetState.potionEffects.front().remainingSeconds, 6 * 3600.0f);
    CHECK_EQ(party.members()[1].rulesetState.potionEffect(TimedPotionEffect::Kind::Aura, 5), 0);
    Drink last = drink(party, potions, 228, 120, 1);
    CHECK(last.result.consumed);
    // A one-drink potion mixed from a bottle of several keeps no drinks of its own (audit ALC-5).
    Drink mixed = drink(party, potions, 225, 10, 4);
    CHECK(mixed.result.consumed);

    // The power is capped at 500.
    drink(party, potions, 229, 900);
    CHECK_EQ(party.members()[0].rulesetState.potionEffect(TimedPotionEffect::Kind::Aura, 51), 500);

    // Antidote: cures and keeps poison and disease away for the duration.
    party.applyMemberCondition(0, CharacterCondition::PoisonMedium);
    drink(party, potions, 225, 10);
    CHECK_FALSE(party.members()[0].conditions.test(size_t(CharacterCondition::PoisonMedium)));
    party.applyMemberCondition(0, CharacterCondition::DiseaseSevere);
    CHECK_FALSE(party.members()[0].conditions.test(size_t(CharacterCondition::DiseaseSevere)));

    // Near monsters a drink costs the drinker recovery; out of combat it is free.
    drink(party, potions, 227, 10);
    CHECK_EQ(party.members()[0].recoverySecondsRemaining, 0.0f);
    drink(party, potions, 227, 10, 0, true);
    CHECK_GT(party.members()[0].recoverySecondsRemaining, 0.0f);

    // A recovering drinker is fed by the next ready member, who pays the recovery.
    drink(party, potions, 227, 10, 0, true);
    CHECK_GT(party.members()[1].recoverySecondsRemaining, 0.0f);

    // Nobody ready: no drink.
    Drink nobody = drink(party, potions, 227, 10, 0, true);
    CHECK_FALSE(nobody.result.consumed);
    CHECK_EQ(nobody.result.statusText, "Player must be active to consume the potion");

    // A drink always needs a ready member (A4.7): the party recovers before the next drinks.
    party.member(0)->recoverySecondsRemaining = 0;
    party.member(1)->recoverySecondsRemaining = 0;

    // Pure Power: +20 Might and Accuracy per 50 power, only the gain over the best step drunk.
    const int mightBefore = party.members()[0].permanentBonuses.might;
    Drink step2 = drink(party, potions, 252, 120);
    CHECK(step2.result.consumed);
    CHECK_EQ(party.members()[0].permanentBonuses.might, mightBefore + 40);
    Drink same = drink(party, potions, 252, 140);
    CHECK_FALSE(same.result.consumed);
    CHECK_EQ(same.result.statusText, "Can't benefit anymore");
    drink(party, potions, 252, 250);
    CHECK_EQ(party.members()[0].permanentBonuses.might, mightBefore + 100);
    CHECK_EQ(party.members()[0].permanentBonuses.accuracy, 100);

    // Transcendence: 5k^2 + 15k skill points for step k, the gain over the best step.
    const uint32_t pointsBefore = party.members()[0].skillPoints;
    drink(party, potions, 259, 100);
    CHECK_EQ(party.members()[0].skillPoints, pointsBefore + 50);
    drink(party, potions, 259, 200);
    CHECK_EQ(party.members()[0].skillPoints, pointsBefore + 140);

    // Dawn sets the age to 20.
    party.member(0)->ageModifier = 7;
    drink(party, potions, 260, 1);
    CHECK_EQ(CharacterAgeReferenceYear - int(party.members()[0].birthYear) + party.members()[0].ageModifier, 20);
}

TEST_CASE("a solo run's potions last a game day")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    MergedPotionSettingTable potions = OpenYAMM::Tests::regressionGameData().mergedPotionSettingTable;
    potions.setEffects(mawPotionEffects());
    Party party = mawParty(rules);
    party.setSoloRun(true);

    drink(party, potions, 228, 120);
    REQUIRE_FALSE(party.members()[0].rulesetState.potionEffects.empty());
    CHECK_EQ(party.members()[0].rulesetState.potionEffects.front().remainingSeconds, 24 * 3600.0f);
}

TEST_CASE("MAW healing potions heal by the expected pool of a character of the potion's level")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    MergedPotionSettingTable potions = OpenYAMM::Tests::regressionGameData().mergedPotionSettingTable;
    potions.setEffects(mawPotionEffects());
    Party party = mawParty(rules);
    const double pool = rules.gameRules().potions.estimatedPool(PotionPool::HitPoints, 100);

    drink(party, potions, 222, 100);
    CHECK_EQ(party.members()[0].health, 1 + int(std::lround(20 + 0.25 * pool)));
    // CLASSES_SPELLS_SPEC §7.4 at power 100, MAW difficulty: 494 (the estimate of a level-100 character is 1896).
    CHECK(pool == doctest::Approx(1896).epsilon(0.03));
}

TEST_CASE("MAW knows every recipe of its mixing table from the start")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    std::ifstream input(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/tables/english/potion.txt");
    std::ostringstream text;
    text << input.rdbuf();
    const std::optional<OpenYAMM::Engine::TextTable> table = OpenYAMM::Engine::TextTable::parseTabSeparated(text.str());
    REQUIRE(table.has_value());
    std::vector<std::vector<std::string>> rows;

    for (size_t row = 0; row < table->getRowCount(); ++row)
    {
        rows.push_back(table->getRow(row));
    }

    PotionMixingTable mixing;
    REQUIRE(mixing.loadFromRows(rows));
    MergedPotionSettingTable potions = gameData.mergedPotionSettingTable;
    potions.setEffects(mawPotionEffects());
    const AlchemyBenchTables tables{
        gameData.itemTable, mixing, gameData.potionNoteTable, potions, gameData.mergedReagentSettingTable};
    const AlchemyBook book = AlchemyBenchRuntime::buildBook(tables, {}, SkillMastery::Grandmaster,
        [](uint32_t)
        {
            return false;
        });

    // The 39 potions the matrix brews (225-263), with no note unlocked, and all of them known.
    for (uint32_t potion = 225; potion <= 263; ++potion)
    {
        CAPTURE(potion);
        CHECK(std::any_of(book.entries.begin(), book.entries.end(),
            [potion](const AlchemyBookEntry &entry)
            {
                return entry.resultItemId == potion && !entry.recipes.empty();
            }));
    }

    CHECK_EQ(book.entries.size(), book.totalResultCount);
}

TEST_CASE("MAW's alchemy pouch takes bottles, reagents and MM6's herbs; crafting materials go to the crafting pouch")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ItemRules &items = rules.gameRules().items;
    const auto pouchOf = [&items](uint32_t itemId, const std::string &equipStat)
    {
        ItemDefinition definition;
        definition.itemId = itemId;
        definition.equipStat = equipStat;
        return items.pouch(definition);
    };
    CHECK(items.hasPouches());
    CHECK(pouchOf(222, "Bottle") == ItemPouch::Alchemy);
    CHECK(pouchOf(200, "Reagent") == ItemPouch::Alchemy);
    CHECK(pouchOf(1762, "Herb") == ItemPouch::Alchemy);
    CHECK(pouchOf(1050, "Misc") == ItemPouch::Crafting);
    CHECK_FALSE(pouchOf(1, "Weapon").has_value());
}

TEST_CASE("a seeded party needs its ruleset's rules back before MAW's challenge-mode start (Doom: 5000 gold)")
{
    RulesetOptions options;
    options.challengeMode = RulesetChallengeMode::Doom;
    MawRules rules(options, MawMapLevels{});
    PartySeed seed;
    seed.gold = 200;
    seed.members = {Character{}, Character{}};
    Party party;
    party.setRules(&rules.gameRules());

    // Seeding drops the rules: the start then runs Standard's (nothing), as a new game from party creation did.
    party.seed(seed);
    party.rules().experience.prepareNewParty(party);
    CHECK_EQ(party.gold(), 200);

    // GameApplication::startNewSessionFromCharacterCreation installs the session's rules after seeding.
    party.seed(seed);
    party.setRules(&rules.gameRules());
    party.rules().experience.prepareNewParty(party);
    CHECK_EQ(party.gold(), 5000);
    CHECK_EQ(party.members()[0].experience, 5000u);
    CHECK_EQ(party.members()[1].experience, 5000u);
}
