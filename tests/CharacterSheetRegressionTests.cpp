#include "doctest/doctest.h"

#include "game/gameplay/GameMechanics.h"

#include "tests/RegressionGameData.h"

#include <optional>
#include <random>

namespace
{
const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}
}

TEST_CASE("character sheet uses equipped items for combat and armor class")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};
    character.level = 5;
    character.might = 20;
    character.intellect = 10;
    character.personality = 10;
    character.endurance = 15;
    character.accuracy = 15;
    character.speed = 15;
    character.luck = 10;
    character.maxHealth = 50;
    character.health = 50;
    character.skills["Sword"] = {"Sword", 2, OpenYAMM::Game::SkillMastery::Normal};
    character.skills["Bow"] = {"Bow", 3, OpenYAMM::Game::SkillMastery::Expert};
    character.skills["Shield"] = {"Shield", 1, OpenYAMM::Game::SkillMastery::Normal};
    character.skills["PlateArmor"] = {"PlateArmor", 1, OpenYAMM::Game::SkillMastery::Normal};
    character.equipment.mainHand = 2;
    character.equipment.offHand = 99;
    character.equipment.bow = 61;
    character.equipment.armor = 94;

    const OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(character, &gameData.itemTable);

    CHECK_EQ(summary.combat.attack, 6);
    REQUIRE(summary.combat.shoot.has_value());
    CHECK_EQ(*summary.combat.shoot, 6);
    CHECK_EQ(summary.combat.meleeDamageText, "9 - 15");
    CHECK_EQ(summary.combat.rangedDamageText, "5 - 8");
    CHECK_EQ(summary.armorClass.actual, 26);
    CHECK_EQ(summary.armorClass.base, 26);
}

TEST_CASE("character sheet shows negative hit points below zero")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};
    character.level = 3;
    character.endurance = 14;
    character.maxHealth = 31;
    character.health = -20;

    OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(character, &gameData.itemTable);

    CHECK_EQ(summary.health.current, -20);

    character.health = 500;
    summary = OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(character, &gameData.itemTable);
    CHECK_EQ(summary.health.current, summary.health.maximum);
}

TEST_CASE("monster incoming attack hit chance uses armor class and monster level")
{
    std::mt19937 lowLevelRng(1234u);
    std::mt19937 highLevelRng(1234u);
    int lowLevelHits = 0;
    int highLevelHits = 0;

    for (int i = 0; i < 512; ++i)
    {
        if (OpenYAMM::Game::GameMechanics::monsterAttackHitsArmorClass(30, 1, 0, lowLevelRng))
        {
            ++lowLevelHits;
        }

        if (OpenYAMM::Game::GameMechanics::monsterAttackHitsArmorClass(30, 20, 0, highLevelRng))
        {
            ++highLevelHits;
        }
    }

    CHECK_GT(lowLevelHits, 0);
    CHECK_LT(lowLevelHits, highLevelHits);
    CHECK_LT(highLevelHits, 512);
}

TEST_CASE("dragon character sheet uses dragon ability attack and spell points")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character dragon = {};
    dragon.className = "Dragon";
    dragon.role = "Dragon";
    dragon.level = 5;
    dragon.health = 40;
    dragon.maxHealth = 40;
    dragon.skills["DragonAbility"] = {"DragonAbility", 9, OpenYAMM::Game::SkillMastery::Master};

    dragon.maxSpellPoints = OpenYAMM::Game::GameMechanics::calculateBaseCharacterMaxSpellPoints(
        dragon,
        &gameData.classMultiplierTable);
    dragon.spellPoints = dragon.maxSpellPoints;

    const OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(dragon, &gameData.itemTable);

    CHECK_EQ(dragon.maxSpellPoints, 45);
    CHECK_EQ(summary.spellPoints.maximum, 45);
    CHECK_EQ(summary.combat.attack, 9);
    CHECK_EQ(summary.armorClass.base, 39);
    CHECK_EQ(summary.armorClass.actual, 39);
    REQUIRE(summary.combat.shoot.has_value());
    CHECK_EQ(*summary.combat.shoot, 9);
    CHECK_EQ(summary.combat.meleeDamageText, "9 - 90");
    CHECK_EQ(summary.combat.rangedDamageText, "9 - 90");
}

TEST_CASE("great wyrm armor class uses dragon ability level without a mastery multiplier")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character greatWyrm = {};
    greatWyrm.className = "Great Wyrm";
    greatWyrm.speed = 14;
    greatWyrm.skills["DragonAbility"] = {
        "DragonAbility",
        4,
        OpenYAMM::Game::SkillMastery::Grandmaster};

    const OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(greatWyrm, &gameData.itemTable);

    CHECK_EQ(summary.armorClass.base, 20);
    CHECK_EQ(summary.armorClass.actual, 20);
}

TEST_CASE("base resource formulas include bodybuilding and meditation skill bonuses")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character dragon = {};
    dragon.className = "Dragon";
    dragon.role = "Dragon";
    dragon.level = 5;
    dragon.endurance = 21;
    dragon.skills["Bodybuilding"] = {"Bodybuilding", 1, OpenYAMM::Game::SkillMastery::Normal};
    dragon.skills["Meditation"] = {"Meditation", 2, OpenYAMM::Game::SkillMastery::Expert};

    CHECK_EQ(OpenYAMM::Game::GameMechanics::calculateBaseCharacterMaxHealth(
        dragon,
        &gameData.classMultiplierTable), 150);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::calculateBaseCharacterMaxSpellPoints(
        dragon,
        &gameData.classMultiplierTable), 65);
}

TEST_CASE("character item skill bonus resolves canonical equipment bonus names")
{
    OpenYAMM::Game::Character character = {};
    character.itemSkillBonuses["Learning"] = 15;
    character.itemSkillBonuses["Disarm"] = 4;
    character.itemSkillBonuses["DisarmTraps"] = 3;

    CHECK_EQ(OpenYAMM::Game::GameMechanics::resolveCharacterItemSkillBonus(character, "Learning"), 15);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::resolveCharacterItemSkillBonus(character, "Disarm Traps"), 7);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::resolveCharacterItemSkillBonus(character, "Sword"), 0);
}

TEST_CASE("class multiplier table drives promoted class resource progression")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    const OpenYAMM::Game::ClassMultiplierEntry *pKnight = gameData.classMultiplierTable.get("Knight");
    const OpenYAMM::Game::ClassMultiplierEntry *pChampion = gameData.classMultiplierTable.get("Champion");
    const OpenYAMM::Game::ClassMultiplierEntry *pDragon = gameData.classMultiplierTable.get("Dragon");
    const OpenYAMM::Game::ClassMultiplierEntry *pGreatWyrm = gameData.classMultiplierTable.get("GreatWyrm");
    const OpenYAMM::Game::ClassMultiplierEntry *pDarkArchMage = gameData.classMultiplierTable.get("DarkArchMage");
    const OpenYAMM::Game::ClassMultiplierEntry *pHighPriest = gameData.classMultiplierTable.get("HighPriest");
    const OpenYAMM::Game::ClassMultiplierEntry *pMasterWizard = gameData.classMultiplierTable.get("MasterWizard");

    REQUIRE(pKnight != nullptr);
    REQUIRE(pChampion != nullptr);
    REQUIRE(pDragon != nullptr);
    REQUIRE(pGreatWyrm != nullptr);
    REQUIRE(pDarkArchMage != nullptr);
    REQUIRE(pHighPriest != nullptr);
    REQUIRE(pMasterWizard != nullptr);
    CHECK_EQ(pKnight->healthPerLevel, 5);
    CHECK_EQ(pChampion->healthPerLevel, 8);
    CHECK_EQ(pDragon->healthPerLevel, 10);
    CHECK_EQ(pGreatWyrm->healthPerLevel, 10);
    CHECK_GT(pGreatWyrm->manaPerLevel, pDragon->manaPerLevel);
    CHECK_EQ(pKnight->classKind, 6);
    CHECK_EQ(pKnight->promotionStep, 0);
    CHECK_EQ(pChampion->classKind, 6);
    CHECK_EQ(pChampion->promotionStep, 2);
    CHECK_EQ(pDragon->classKind, 4);
    CHECK_EQ(pDragon->promotionStep, 1);
    CHECK_EQ(pGreatWyrm->classKind, 4);
    CHECK_EQ(pGreatWyrm->promotionStep, 2);
    CHECK_EQ(pDarkArchMage->classKind, 14);
    CHECK_EQ(pDarkArchMage->promotionStep, 2);
    CHECK_EQ(pHighPriest->classKind, 2);
    CHECK_EQ(pHighPriest->promotionStep, 2);
    CHECK_EQ(pMasterWizard->classKind, 14);
    CHECK_EQ(pMasterWizard->promotionStep, 2);
    CHECK_EQ(gameData.classSkillTable.getHighestPromotionCap("Knight", "Sword"),
        OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_EQ(gameData.classSkillTable.getHighestPromotionCap("Sorcerer", "DarkMagic"),
        OpenYAMM::Game::SkillMastery::Grandmaster);

    OpenYAMM::Game::Character character = {};
    character.className = "Champion";
    character.role = "Champion";
    character.level = 1;
    character.endurance = 14;

    CHECK_EQ(OpenYAMM::Game::GameMechanics::calculateBaseCharacterMaxHealth(
        character,
        &gameData.classMultiplierTable), 43);
}

TEST_CASE("character sheet primary stats do not double count equipment bonuses")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};
    character.might = 20;
    character.equipment.mainHand = 501;
    character.magicalBonuses.might = 40;

    OpenYAMM::Game::CharacterSheetSummary summary = OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(
        character,
        &gameData.itemTable,
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable);

    CHECK_EQ(summary.might.base, 60);
    CHECK_EQ(summary.might.actual, 60);

    character.magicalBonuses.might = 47;
    summary = OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(
        character,
        &gameData.itemTable,
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable);

    CHECK_EQ(summary.might.base, 60);
    CHECK_EQ(summary.might.actual, 67);
}

TEST_CASE("character sheet uses NA for ranged combat without a bow")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};
    character.level = 1;
    character.might = 15;
    character.intellect = 10;
    character.personality = 10;
    character.endurance = 15;
    character.accuracy = 15;
    character.speed = 12;
    character.luck = 10;
    character.maxHealth = 40;
    character.health = 40;

    const OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(character, &gameData.itemTable);

    CHECK_FALSE(summary.combat.shoot.has_value());
    CHECK_EQ(summary.combat.rangedDamageText, "N/A");
    CHECK_EQ(summary.conditionText, "Good");
}

TEST_CASE("character sheet marks experience as trainable at the OE threshold")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};
    character.level = 4;
    character.experience = 9999;

    OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(character, &gameData.itemTable);

    CHECK_FALSE(summary.canTrainToNextLevel);

    character.experience = 10000;
    summary = OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(character, &gameData.itemTable);

    CHECK(summary.canTrainToNextLevel);
    CHECK_EQ(summary.experienceText, "10000");
    CHECK_EQ(summary.level.base, 4);
    CHECK_EQ(summary.level.actual, 5);
}

TEST_CASE("temporary level bonus raises displayed level and effective resources")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};
    character.className = "Cleric";
    character.role = "Cleric";
    character.level = 5;
    character.endurance = 14;
    character.personality = 14;
    character.maxHealth = OpenYAMM::Game::GameMechanics::calculateBaseCharacterMaxHealth(
        character,
        &gameData.classMultiplierTable);
    character.maxSpellPoints = OpenYAMM::Game::GameMechanics::calculateBaseCharacterMaxSpellPoints(
        character,
        &gameData.classMultiplierTable);
    const int baseHealth = character.maxHealth;
    const int baseSpellPoints = character.maxSpellPoints;

    character.levelModifier = 30;

    const OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(character, &gameData.itemTable);

    CHECK_EQ(summary.level.base, 5);
    CHECK_EQ(summary.level.actual, 35);
    CHECK_GT(summary.health.maximum, baseHealth);
    CHECK_GT(summary.spellPoints.maximum, baseSpellPoints);
}

TEST_CASE("resource refresh preserves current hp against temporary effective maximum")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};
    character.className = "Cleric";
    character.role = "Cleric";
    character.level = 5;
    character.endurance = 14;
    character.personality = 14;
    character.maxHealth = OpenYAMM::Game::GameMechanics::calculateBaseCharacterMaxHealth(
        character,
        &gameData.classMultiplierTable);
    character.maxSpellPoints = OpenYAMM::Game::GameMechanics::calculateBaseCharacterMaxSpellPoints(
        character,
        &gameData.classMultiplierTable);
    character.levelModifier = 30;
    character.magicalBonuses.endurance = 250;
    character.magicalBonuses.maxHealth = 40;
    character.magicalBonuses.maxSpellPoints = 25;

    character.health = OpenYAMM::Game::GameMechanics::calculateEffectiveCharacterMaxHealth(
        character,
        &gameData.classMultiplierTable);
    character.spellPoints = OpenYAMM::Game::GameMechanics::calculateEffectiveCharacterMaxSpellPoints(
        character,
        &gameData.classMultiplierTable);

    OpenYAMM::Game::GameMechanics::refreshCharacterBaseResources(
        character,
        false,
        &gameData.classMultiplierTable);

    CHECK_EQ(
        character.health,
        OpenYAMM::Game::GameMechanics::calculateEffectiveCharacterMaxHealth(
            character,
            &gameData.classMultiplierTable));
    CHECK_EQ(
        character.spellPoints,
        OpenYAMM::Game::GameMechanics::calculateEffectiveCharacterMaxSpellPoints(
            character,
            &gameData.classMultiplierTable));

    character.health -= 12;
    character.spellPoints -= 7;
    const int damagedHealth = character.health;
    const int damagedSpellPoints = character.spellPoints;

    OpenYAMM::Game::GameMechanics::refreshCharacterBaseResources(
        character,
        false,
        &gameData.classMultiplierTable);

    CHECK_EQ(character.health, damagedHealth);
    CHECK_EQ(character.spellPoints, damagedSpellPoints);
}

TEST_CASE("character sheet resistance split does not double count equipment bonuses")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Character character = {};
    character.baseResistances.fire = 10;
    character.equipment.mainHand = 505;
    character.magicalBonuses.resistances.fire = 40;

    OpenYAMM::Game::CharacterSheetSummary summary = OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(
        character,
        &gameData.itemTable,
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable);

    CHECK_EQ(summary.fireResistance.base, 50);
    CHECK_EQ(summary.fireResistance.actual, 50);

    character.magicalBonuses.resistances.fire = 47;
    summary = OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(
        character,
        &gameData.itemTable,
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable);

    CHECK_EQ(summary.fireResistance.base, 50);
    CHECK_EQ(summary.fireResistance.actual, 57);
}

TEST_CASE("experience inspect supplement reports shortfall and maximum trainable level")
{
    OpenYAMM::Game::Character character = {};
    character.name = "Ariel";
    character.level = 4;
    character.experience = 9500;

    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::buildExperienceInspectSupplement(character),
        "Ariel needs 500 more experience to train to level 5.");

    character.experience = 21000;

    CHECK_EQ(OpenYAMM::Game::GameMechanics::maximumTrainableLevelFromExperience(character), 7u);
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::buildExperienceInspectSupplement(character),
        "Ariel is eligible to train up to level 7. Ariel needs 7000 more experience for level 8.");
}

TEST_CASE("primary stat bonuses follow the MM8 table and report the next threshold")
{
    using OpenYAMM::Game::GameMechanics;

    CHECK_EQ(GameMechanics::primaryStatBonus(0), -6);
    CHECK_EQ(GameMechanics::primaryStatBonus(13), 0);
    CHECK_EQ(GameMechanics::primaryStatBonus(15), 1);
    CHECK_EQ(GameMechanics::primaryStatBonus(51), 9);
    CHECK_EQ(GameMechanics::primaryStatBonus(75), 10);
    CHECK_EQ(GameMechanics::primaryStatBonus(500), 30);

    CHECK_EQ(GameMechanics::nextPrimaryStatBonusValue(-4), std::optional<int>(0));
    CHECK_EQ(GameMechanics::nextPrimaryStatBonusValue(13), std::optional<int>(15));
    CHECK_EQ(GameMechanics::nextPrimaryStatBonusValue(51), std::optional<int>(75));
    CHECK_EQ(GameMechanics::nextPrimaryStatBonusValue(499), std::optional<int>(500));
    CHECK_FALSE(GameMechanics::nextPrimaryStatBonusValue(500).has_value());
}

TEST_CASE("resistance and monster effect chances average the MM8 rolls")
{
    using OpenYAMM::Game::GameMechanics;

    CHECK_EQ(GameMechanics::averageResistedDamageShare(0), doctest::Approx(0.0f));
    CHECK_EQ(GameMechanics::averageResistedDamageShare(-5), doctest::Approx(0.0f));
    // Resistance 30: each roll halves with even odds, keeping 1/2 + 1/8 + 1/32 + 1/128 + 1/256 of the hit.
    CHECK_EQ(GameMechanics::averageResistedDamageShare(30), doctest::Approx(1.0f - 0.66796875f));
    CHECK_EQ(GameMechanics::monsterEffectResistChance(0), doctest::Approx(0.0f));
    CHECK_EQ(GameMechanics::monsterEffectResistChance(10), doctest::Approx(0.25f));
    CHECK_EQ(GameMechanics::monsterEffectResistChance(30), doctest::Approx(0.5f));
}
