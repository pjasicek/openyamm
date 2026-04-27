#include "doctest/doctest.h"

#include "game/gameplay/GameMechanics.h"

#include "tests/RegressionGameData.h"

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
    CHECK_EQ(*summary.combat.shoot, 4);
    CHECK_EQ(summary.combat.meleeDamageText, "9 - 15");
    CHECK_EQ(summary.combat.rangedDamageText, "4 - 8");
    CHECK_EQ(summary.armorClass.actual, 29);
    CHECK_EQ(summary.armorClass.base, 29);
}

TEST_CASE("monster incoming attack hit chance uses armor class and monster level")
{
    std::mt19937 lowLevelRng(1234u);
    std::mt19937 highLevelRng(1234u);
    int lowLevelHits = 0;
    int highLevelHits = 0;

    for (int i = 0; i < 512; ++i)
    {
        if (OpenYAMM::Game::GameMechanics::monsterAttackHitsArmorClass(30, 1, lowLevelRng))
        {
            ++lowLevelHits;
        }

        if (OpenYAMM::Game::GameMechanics::monsterAttackHitsArmorClass(30, 20, highLevelRng))
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

    dragon.maxSpellPoints = OpenYAMM::Game::GameMechanics::calculateBaseCharacterMaxSpellPoints(dragon);
    dragon.spellPoints = dragon.maxSpellPoints;

    const OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(dragon, &gameData.itemTable);

    CHECK_EQ(dragon.maxSpellPoints, 15);
    CHECK_EQ(summary.spellPoints.maximum, 15);
    CHECK_EQ(summary.combat.attack, 9);
    REQUIRE(summary.combat.shoot.has_value());
    CHECK_EQ(*summary.combat.shoot, 9);
    CHECK_EQ(summary.combat.meleeDamageText, "9 - 90");
    CHECK_EQ(summary.combat.rangedDamageText, "9 - 90");
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
        "Ariel is eligible to train up to level 7.");
}
