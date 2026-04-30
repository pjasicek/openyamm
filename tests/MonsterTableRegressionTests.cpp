#include "doctest/doctest.h"

#include "game/tables/MonsterTable.h"

namespace
{
std::vector<std::string> makeMonsterStatsRow(
    int id,
    const std::string &name,
    bool bloodSplat,
    const std::string &attack1Missile,
    int attack2Chance,
    const std::string &attack2Missile,
    int spell1Chance,
    const std::string &spell1Descriptor)
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = name;
    row[2] = name + "Pic";
    row[3] = "1";
    row[4] = "10";
    row[5] = "0";
    row[6] = "10";
    row[7] = "0";
    row[8] = bloodSplat ? "1" : "0";
    row[10] = "short";
    row[11] = "normal";
    row[12] = "0";
    row[13] = "100";
    row[14] = "30";
    row[17] = "Physical";
    row[18] = "1d4";
    row[19] = attack1Missile;
    row[20] = std::to_string(attack2Chance);
    row[21] = "Physical";
    row[22] = "1d4";
    row[23] = attack2Missile;
    row[24] = std::to_string(spell1Chance);
    row[25] = spell1Descriptor;
    return row;
}
}

TEST_CASE("monster stats parser preserves blood splat on death flag")
{
    OpenYAMM::Game::MonsterTable table = {};

    REQUIRE(table.loadStatsFromRows({
        makeMonsterStatsRow(1, "Lizardman", true, "", 0, "", 0, ""),
        makeMonsterStatsRow(98, "Wisp", false, "", 0, "", 0, "")
    }));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pLizardman = table.findStatsById(1);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pWisp = table.findStatsById(98);

    REQUIRE(pLizardman != nullptr);
    REQUIRE(pWisp != nullptr);
    CHECK(pLizardman->bloodSplatOnDeath);
    CHECK_FALSE(pWisp->bloodSplatOnDeath);
}

TEST_CASE("monster stats parser treats plain numeric damage like OE Nd1 damage")
{
    OpenYAMM::Game::MonsterTable table = {};
    std::vector<std::string> row = makeMonsterStatsRow(1, "FlatDamage", true, "", 0, "", 0, "");
    row[18] = "5";
    row[22] = "3";

    REQUIRE(table.loadStatsFromRows({row}));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMonster = table.findStatsById(1);

    REQUIRE(pMonster != nullptr);
    CHECK_EQ(pMonster->attack1Damage.diceRolls, 5);
    CHECK_EQ(pMonster->attack1Damage.diceSides, 1);
    CHECK_EQ(pMonster->attack1Damage.bonus, 0);
    CHECK_EQ(pMonster->attack2Damage.diceRolls, 3);
    CHECK_EQ(pMonster->attack2Damage.diceSides, 1);
    CHECK_EQ(pMonster->attack2Damage.bonus, 0);
}

TEST_CASE("monster stats parser classifies melee mixed and ranged attack styles")
{
    OpenYAMM::Game::MonsterTable table = {};

    REQUIRE(table.loadStatsFromRows({
        makeMonsterStatsRow(12, "Melee", true, "", 0, "", 0, ""),
        makeMonsterStatsRow(5, "Mixed", true, "", 35, "arrow", 0, ""),
        makeMonsterStatsRow(16, "Ranged", true, "arrow", 0, "", 0, "")
    }));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMelee = table.findStatsById(12);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMixed = table.findStatsById(5);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pRanged = table.findStatsById(16);

    REQUIRE(pMelee != nullptr);
    REQUIRE(pMixed != nullptr);
    REQUIRE(pRanged != nullptr);
    CHECK(pMelee->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::MeleeOnly);
    CHECK(pMixed->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::MixedMeleeRanged);
    CHECK(pRanged->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::Ranged);
}

TEST_CASE("monster stats parser ignores unsupported missile tokens for attack style")
{
    OpenYAMM::Game::MonsterTable table = {};

    REQUIRE(table.loadStatsFromRows({
        makeMonsterStatsRow(71, "Dragon Flightleader", true, "Cold", 0, "", 0, ""),
        makeMonsterStatsRow(72, "Great Wyrm", true, "Elec", 0, "", 0, ""),
        makeMonsterStatsRow(112, "Emerald Dragon", true, "Ener", 0, "", 0, "")
    }));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pFlightleader = table.findStatsById(71);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pGreatWyrm = table.findStatsById(72);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pEmeraldDragon = table.findStatsById(112);

    REQUIRE(pFlightleader != nullptr);
    REQUIRE(pGreatWyrm != nullptr);
    REQUIRE(pEmeraldDragon != nullptr);
    CHECK_FALSE(pFlightleader->attack1HasMissile);
    CHECK_FALSE(pGreatWyrm->attack1HasMissile);
    CHECK(pEmeraldDragon->attack1HasMissile);
    CHECK(pFlightleader->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::MeleeOnly);
    CHECK(pGreatWyrm->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::MeleeOnly);
    CHECK(pEmeraldDragon->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::Ranged);
}

TEST_CASE("monster death drop parser maps multiple drops to monster id")
{
    OpenYAMM::Game::MonsterTable table = {};

    REQUIRE(table.loadDeathDropsFromRows({
        {"MonsterID", "MonsterName", "ItemID", "ItemName", "ChancePercent", "Description"},
        {"85", "Dire Wolf Yearling", "201", "Wolf's Eye", "20", "Reagent drop"},
        {"85", "Dire Wolf Yearling", "633", "Dire Wolf Pelt", "35", "Bounty drop"},
        {"86", "Dire Wolf", "633", "Dire Wolf Pelt", "0", "Disabled drop"}
    }));

    const std::vector<OpenYAMM::Game::MonsterTable::MonsterDeathDropEntry> &drops =
        table.deathDropsForMonsterId(85);
    const std::vector<OpenYAMM::Game::MonsterTable::MonsterDeathDropEntry> &disabledDrops =
        table.deathDropsForMonsterId(86);

    REQUIRE_EQ(drops.size(), 2);
    CHECK_EQ(drops[0].itemId, 201u);
    CHECK_EQ(drops[0].chancePercent, 20);
    CHECK_EQ(drops[1].itemId, 633u);
    CHECK_EQ(drops[1].chancePercent, 35);
    CHECK(disabledDrops.empty());
}
