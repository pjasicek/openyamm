#include "doctest/doctest.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawCombatFormulas.h"

#include <cmath>

using namespace OpenYAMM::Game;

// The worked examples of devdocs/maw/COMBAT_SPEC.md §11, produced by MAW's own Lua. The Champion is built from the
// MAW-difficulty balance model at levels 50 and 150 (all seven stats 89 / 279).
namespace
{
MawModelConfig difficultyConfig(int difficulty)
{
    MawModelConfig config;
    config.difficulty = difficulty;
    return config;
}

constexpr int MawDifficulty = 3;
constexpr int HellDifficulty = 5;
}

TEST_CASE("MAW crit chance and multiplier match the Champion and ArchMage examples")
{
    MawCritInputs weapon;
    weapon.luck = 89;
    weapon.accuracy = 89;
    weapon.referenceLevel = 50;
    MawCrit crit = mawCrit(weapon);
    CHECK(crit.chance == doctest::Approx(0.1687).epsilon(1e-3));
    CHECK(crit.multiplier == doctest::Approx(1.74));

    weapon.luck = 279;
    weapon.accuracy = 279;
    weapon.referenceLevel = 150;
    crit = mawCrit(weapon);
    CHECK(crit.chance == doctest::Approx(0.2732).epsilon(1e-3));
    CHECK(crit.multiplier == doctest::Approx(1.95));

    MawCritInputs spell;
    spell.kind = MawCritKind::Spell;
    spell.luck = 89;
    spell.intellect = 89;
    spell.referenceLevel = 50;
    CHECK(mawCrit(spell).multiplier == doctest::Approx(1.56));
    spell.luck = 279;
    spell.intellect = 279;
    spell.referenceLevel = 150;
    CHECK(mawCrit(spell).multiplier == doctest::Approx(1.61));
}

TEST_CASE("MAW hit chances match the Champion example at MAW and Hell")
{
    MawBalanceModel maw(difficultyConfig(MawDifficulty));
    MawBalanceModel hell(difficultyConfig(HellDifficulty));

    // MAW 8fbb48d1: the model's melee skill lost its x1.5 and its stat share fell to 0.2, so the expected attack and
    // stat are lower than in COMBAT_SPEC's ef23ee17 example.
    CHECK(mawPartyHitChance(114, 50, std::nullopt, maw) == doctest::Approx(0.6817).epsilon(2e-4));
    CHECK(mawPartyHitChance(111, 50, std::nullopt, maw) == doctest::Approx(0.6711).epsilon(2e-4));
    CHECK(mawPartyHitChance(114, 50, std::nullopt, hell) == doctest::Approx(0.6787).epsilon(2e-4));
    CHECK(mawPartyHitChance(279, 150, std::nullopt, maw) == doctest::Approx(0.6862).epsilon(2e-4));
    CHECK(mawPartyHitChance(274, 150, std::nullopt, hell) == doctest::Approx(0.6734).epsilon(2e-4));

    CHECK(mawChanceToBeHit(89, 50, maw) == doctest::Approx(0.7992).epsilon(2e-4));
    CHECK(mawChanceToBeHit(89, 50, hell) == doctest::Approx(0.8041).epsilon(2e-4));
    CHECK(mawChanceToBeHit(279, 150, maw) == doctest::Approx(0.7055).epsilon(2e-4));
    CHECK(mawChanceToBeHit(279, 150, hell) == doctest::Approx(0.7157).epsilon(2e-4));
}

TEST_CASE("MAW weapon recovery and attack delay match the Champion example")
{
    CHECK(mawItemRecovery(80, 50, true) == 90);
    CHECK(mawItemRecovery(80, 150, true) == 100);
    CHECK(mawItemRecovery(100, 50, false) == 90);
    CHECK(mawItemRecovery(100, 150, false) == 110);
    CHECK(mawSpeedRecoveryBonus(89) == 8);

    // Sword GM 17 x 2 + Armsmaster GM 11 + Speed 8.
    MawAttackDelay delay = mawAttackDelay({90, 53});
    CHECK(delay.delay == 59);
    CHECK(delay.damageMultiplier == doctest::Approx(59.0 / 65.0));
    delay = mawAttackDelay({100, 133});
    CHECK(delay.delay == 43);
    CHECK(delay.damageMultiplier == doctest::Approx(1.0));
    delay = mawAttackDelay({90, 42});
    CHECK(delay.delay == 63);
    CHECK(delay.damageMultiplier == doctest::Approx(0.9));
    delay = mawAttackDelay({110, 107});
    CHECK(delay.delay == 53);
    CHECK(delay.damageMultiplier == doctest::Approx(53.0 / 48.0));
}

TEST_CASE("MAW spell delay and ascended dice match the ArchMage example")
{
    // Fireball (GM delay 80) and Dragon Breath (100), Learning 11 / 26.
    CHECK(mawSpellDelay({80, 89, 11}) == 91);
    CHECK(mawSpellDelay({80, 279, 26}) == 104);
    CHECK(mawSpellDelay({100, 89, 11}) == 113);
    CHECK(mawSpellDelay({100, 279, 26}) == 130);

    // Growth 1.02^s and every damage spell at x0.7 (MAW fa1ff481).
    CHECK(mawAscendedSpellDice({1, 8, 0}, 11).diceMax == 8);
    CHECK(mawAscendedSpellDice({1, 28, 0}, 11).diceMax == 30);
    CHECK(mawAscendedSpellDice({1, 8, 0}, 26).diceMax == 14);
    CHECK(mawAscendedSpellDice({1, 28, 0}, 26).diceMax == 50);
    CHECK(mawAscendedSpellDice({1, 8, 0}, 26).diceMin == 1);
}

TEST_CASE("MAW party hits on a monster match the worked examples")
{
    // Generic B-tier monster: Physical 10, Fire 50, Dark 20. Draws R(a, b) return floor((a + b) / 2).
    const auto weaponHit = [](int minimum, int maximum, double multiplier, double critMultiplier)
    {
        const int roll = (minimum + maximum) / 2;
        return std::ceil(
            mawAverageOfTwoRolls(roll, roll) * multiplier * critMultiplier / mawMonsterResistanceDivisor(10));
    };

    CHECK(weaponHit(71, 120, 59.0 / 65.0, 1) == 81);
    CHECK(weaponHit(71, 120, 59.0 / 65.0, 1.74) == 140);
    CHECK(weaponHit(36, 63, 0.9, 1) == 42);
    CHECK(weaponHit(36, 63, 0.9, 1.74) == 72);
    CHECK(weaponHit(251, 424, 1, 1) == 315);
    CHECK(weaponHit(251, 424, 1, 1.95) == 614);
    CHECK(weaponHit(166, 288, 53.0 / 48.0, 1) == 234);
    CHECK(weaponHit(166, 288, 53.0 / 48.0, 1.95) == 457);

    // Fireball: 17 points of R(1, 13), x(1 + Int / 1000), Fire 50.
    const auto spellHit = [](int points, int diceMax, double intellect, double critMultiplier, int resistance)
    {
        const double roll = points * ((1 + diceMax) / 2);
        return std::ceil(roll * (1 + intellect / 1000) * critMultiplier / mawMonsterResistanceDivisor(resistance));
    };

    CHECK(spellHit(17, 13, 89, 1, 50) == 92);
    CHECK(spellHit(17, 13, 89, 1.56, 50) == 143);
    CHECK(spellHit(17, 45, 89, 1, 20) == 371);
    CHECK(spellHit(40, 23, 279, 1, 50) == 435);
    CHECK(spellHit(40, 81, 279, 1.61, 20) == 2940);
}

TEST_CASE("MAW monster hits on the Champion match the worked examples")
{
    const auto monsterHit = [](int difficulty, int level, double spellMultiplier, CombatDamageType type,
                                int armorClass, int resistance)
    {
        MawBalanceModel model(difficultyConfig(difficulty));
        MawMitigationInputs inputs;
        // Sized against the defence the damage kind meets (MAW 249b00da).
        const MawDamageClass damageClass =
            type == CombatDamageType::Physical ? MawDamageClass::Physical : MawDamageClass::Magic;
        inputs.damage =
            mawRound(model.monsterDamage(level, damageClass) * spellMultiplier) * mawMonsterDamageSpread(100, 100);
        inputs.type = type;
        inputs.attackerLevel = level;
        inputs.armorClass = armorClass;
        inputs.resistances.fill(resistance);
        return int(mawMitigatedDamage(inputs));
    };
    const double fireball = mawMonsterSpellMultiplier(6);

    // MAW 8fbb48d1: per-kind monster damage (MAW's Lua: 186.23 physical, 254.57 fire at level 50, MAW difficulty)
    // and the gentler armour and resistance divisors 200 + L and 100 + L.
    CHECK(monsterHit(MawDifficulty, 50, 1, CombatDamageType::Physical, 63, 34) == 149);
    CHECK(monsterHit(MawDifficulty, 50, fireball, CombatDamageType::Fire, 63, 34) == 104);
    CHECK(monsterHit(MawDifficulty, 150, 1, CombatDamageType::Physical, 136, 110) == 1447);
    CHECK(monsterHit(MawDifficulty, 150, fireball, CombatDamageType::Fire, 136, 110) == 1067);
    CHECK(monsterHit(HellDifficulty, 50, 1, CombatDamageType::Physical, 63, 34) == 184);
    CHECK(monsterHit(HellDifficulty, 50, fireball, CombatDamageType::Fire, 63, 34) == 127);
    CHECK(monsterHit(HellDifficulty, 150, 1, CombatDamageType::Physical, 136, 110) == 1823);
    CHECK(monsterHit(HellDifficulty, 150, fireball, CombatDamageType::Fire, 136, 110) == 1335);
}

TEST_CASE("MAW mitigation keeps a tenth of the hit and honours immunities")
{
    MawMitigationInputs inputs;
    inputs.damage = 1000;
    inputs.type = CombatDamageType::Physical;
    inputs.attackerLevel = 1;
    inputs.armorClass = 100000;
    CHECK(mawMitigatedDamage(inputs) == doctest::Approx(100));

    inputs.type = CombatDamageType::Light;
    inputs.resistances = {0, 0, 0, 0, 65000, 0};
    // Light takes the weaker of Mind and Body; Body is 0, so the hit is unchanged.
    CHECK(mawMitigatedDamage(inputs) == doctest::Approx(1000));
    inputs.resistances = {0, 0, 0, 0, 65000, 65000};
    CHECK(mawMitigatedDamage(inputs) == doctest::Approx(0));

    inputs.type = CombatDamageType::Irresistible;
    inputs.grandmasterShield = true;
    CHECK(mawMitigatedDamage(inputs) == doctest::Approx(850));
}
