#include "doctest/doctest.h"

#include "game/events/EvtEnums.h"
#include "game/gameplay/ArenaRuntime.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/MonsterTable.h"

#include <optional>
#include <random>

namespace
{
std::vector<std::string> makeArenaMonsterStatsRow(int id, const std::string &name, int level)
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = name;
    row[2] = name;
    row[3] = std::to_string(level);
    row[4] = "10";
    row[5] = "0";
    row[6] = "10";
    row[7] = "0";
    row[8] = "1";
    row[10] = "short";
    row[11] = "normal";
    row[12] = "0";
    row[13] = "100";
    row[14] = "30";
    row[17] = "Physical";
    row[18] = "1d4";
    return row;
}

OpenYAMM::Game::MonsterTable makeArenaMonsterTable()
{
    OpenYAMM::Game::MonsterTable table = {};

    REQUIRE(table.loadStatsFromRows({
        makeArenaMonsterStatsRow(1, "Kind Two Brigand", 14),
        makeArenaMonsterStatsRow(2, "Kind One Rat", 5),
        makeArenaMonsterStatsRow(3, "Kind Three Ogre", 16),
        makeArenaMonsterStatsRow(5, "Kind One Bat", 10),
        makeArenaMonsterStatsRow(6, "Kind Three Veteran", 25),
        makeArenaMonsterStatsRow(8, "Kind One Spider", 4),
        makeArenaMonsterStatsRow(9, "Kind Three Ancient", 45),
        makeArenaMonsterStatsRow(12, "Kind Three Civilian", 20),
    }));

    OpenYAMM::Game::MergedBolsterMonsterTable bolsterMonsterTable = {};
    REQUIRE(bolsterMonsterTable.loadFromRows({
        {
            "#",
            "Note",
            "Type",
            "ExtraType",
            "Creed",
            "Gender",
            "Style",
            "Pref magic",
            "No bounty hunt",
            "New ranged attacks",
            "New spells",
            "Size affects HP",
            "Replicate",
            "New summons",
            "Summon Id",
            "Extra points",
            "Max HP Boost (%)",
        },
        {"1", "Kind Two Brigand", "", "", "", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
        {"2", "Kind One Rat", "", "", "", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
        {"3", "Kind Three Ogre", "", "", "", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
        {"5", "Kind One Bat", "", "", "", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
        {"6", "Kind Three Veteran", "", "", "", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
        {"8", "Kind One Spider", "", "", "", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
        {"9", "Kind Three Ancient", "", "", "", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
        {"12", "Kind Three Civilian", "", "NoArena", "", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
    }));
    REQUIRE(table.applyKindFlagsFromBolsterMonsterTable(bolsterMonsterTable));
    return table;
}

OpenYAMM::Game::Party makeArenaParty(std::initializer_list<uint32_t> levels)
{
    OpenYAMM::Game::PartySeed seed = {};

    for (uint32_t level : levels)
    {
        OpenYAMM::Game::Character member = {};
        member.name = "Arena Test";
        member.level = level;
        seed.members.push_back(member);
    }

    seed.gold = 0;
    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    return party;
}
}

TEST_CASE("mmmerge arena candidates use difficulty level bands tiers and NoArena flags")
{
    OpenYAMM::Game::MonsterTable monsterTable = makeArenaMonsterTable();

    const std::vector<int16_t> pageCandidates = OpenYAMM::Game::collectArenaMonsterCandidates(
        monsterTable,
        OpenYAMM::Game::ArenaDifficulty::Page,
        10);

    REQUIRE_FALSE(pageCandidates.empty());

    for (int16_t monsterId : pageCandidates)
    {
        const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats =
            monsterTable.findStatsById(monsterId);
        REQUIRE(pStats != nullptr);
        CHECK_FALSE(pStats->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
        CHECK_LE(pStats->level, 10);
        CHECK_EQ(3 - (monsterId % 3), 1);
    }

    const std::vector<int16_t> lordCandidates = OpenYAMM::Game::collectArenaMonsterCandidates(
        monsterTable,
        OpenYAMM::Game::ArenaDifficulty::Lord,
        30);

    REQUIRE_FALSE(lordCandidates.empty());

    for (int16_t monsterId : lordCandidates)
    {
        const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats =
            monsterTable.findStatsById(monsterId);
        REQUIRE(pStats != nullptr);
        CHECK_FALSE(pStats->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
        CHECK_GE(pStats->level, 15);
        CHECK_LE(pStats->level, 40);
        CHECK_EQ(3 - (monsterId % 3), 3);
    }

    CHECK(std::find(lordCandidates.begin(), lordCandidates.end(), 12) == lordCandidates.end());
    CHECK(std::find(lordCandidates.begin(), lordCandidates.end(), 9) == lordCandidates.end());
}

TEST_CASE("mmmerge arena candidates can be limited to the current world monster block")
{
    OpenYAMM::Game::MonsterTable monsterTable = {};
    REQUIRE(monsterTable.loadStatsFromRows({
        makeArenaMonsterStatsRow(2, "MM8 Rat", 5),
        makeArenaMonsterStatsRow(200, "MM7 Rat", 5),
        makeArenaMonsterStatsRow(476, "MM6 Rat", 5),
    }));

    CHECK(std::string(OpenYAMM::Game::mergedMonsterSourceWorldId(2)) == "mm8");
    CHECK(std::string(OpenYAMM::Game::mergedMonsterSourceWorldId(200)) == "mm7");
    CHECK(std::string(OpenYAMM::Game::mergedMonsterSourceWorldId(476)) == "mm6");
    CHECK(std::string(OpenYAMM::Game::mergedMonsterSourceWorldId(649)).empty());

    const std::vector<int16_t> mm6Candidates = OpenYAMM::Game::collectArenaMonsterCandidates(
        monsterTable,
        OpenYAMM::Game::ArenaDifficulty::Page,
        10,
        "mm6");

    REQUIRE(mm6Candidates.size() == 1u);
    CHECK(mm6Candidates[0] == 476);

    const std::vector<int16_t> allCandidates = OpenYAMM::Game::collectArenaMonsterCandidates(
        monsterTable,
        OpenYAMM::Game::ArenaDifficulty::Page,
        10);

    CHECK(allCandidates.size() == 3u);
}

TEST_CASE("arena fight plan uses OE counts rewards and placements with MMerge monster candidates")
{
    OpenYAMM::Game::MonsterTable monsterTable = makeArenaMonsterTable();
    OpenYAMM::Game::Party party = makeArenaParty({5, 12, 20, 8});
    std::mt19937 rng(12345u);

    const std::optional<OpenYAMM::Game::ArenaFightPlan> plan =
        OpenYAMM::Game::buildArenaFightPlan(
            monsterTable,
            party,
            OpenYAMM::Game::ArenaDifficulty::Knight,
            rng);

    REQUIRE(plan.has_value());
    CHECK_EQ(plan->goldReward, 4000);
    CHECK_GE(plan->spawns.size(), 10u);
    CHECK_LE(plan->spawns.size(), 20u);
    REQUIRE_FALSE(plan->spawns.empty());
    CHECK_EQ(plan->spawns[0].x, 1524.0f);
    CHECK_EQ(plan->spawns[0].y, 8332.0f);
    CHECK_EQ(plan->spawns[0].z, 1.0f);
}

TEST_CASE("arena reward increments selected difficulty counter and grants award and gold")
{
    OpenYAMM::Game::Party party = makeArenaParty({10});
    party.startArenaFight(OpenYAMM::Game::ArenaDifficulty::Knight, 2000);

    REQUIRE(OpenYAMM::Game::claimArenaReward(party));

    CHECK_EQ(
        party.eventVariableValue(static_cast<uint16_t>(OpenYAMM::Game::EvtVariable::ArenaWinsKnight)),
        1);
    CHECK(party.hasAward(90));
    CHECK_EQ(party.gold(), 2000);
    CHECK_EQ(party.arenaVisitState(), OpenYAMM::Game::ArenaVisitState::Won);
    CHECK_EQ(party.arenaDifficulty(), OpenYAMM::Game::ArenaDifficulty::Invalid);
}
