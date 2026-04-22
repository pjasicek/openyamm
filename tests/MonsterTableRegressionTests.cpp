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
