#include "doctest/doctest.h"
#include "game/items/ItemEnchantTables.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/RandomStreams.h"
#include "game/tables/MonsterTable.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <array>
#include <random>
#include <string>
#include <vector>

// Table-reading fixes made before a ruleset patches the engine tables (devdocs/maw/HANDOFF.md, phase 2).
namespace
{
std::vector<std::string> monsterRow(int id, const std::string &experience, const std::string &preference)
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = "Monster " + std::to_string(id);
    row[2] = "picture";
    row[3] = "10";
    row[4] = "\" 1,080 \"";
    row[5] = "5";
    row[6] = experience;
    row[10] = "Short";
    row[11] = "Normal";
    row[12] = "0";
    row[13] = "100";
    row[14] = "100";
    row[15] = preference;
    row[17] = "Phys";
    row[18] = "1d6";
    return row;
}
}

TEST_CASE("monster rows accept spreadsheet numbers and letter attack preferences")
{
    using namespace OpenYAMM::Game;
    MonsterTable table;
    REQUIRE(table.loadStatsFromRows({
        monsterRow(1, "\"1,565\"", "CP"),
        monsterRow(2, "40", "x"),
        monsterRow(3, "40", "\"K,A\""),
        monsterRow(4, "40", "2048"),
        monsterRow(5, "40", "n"),
    }));

    const MonsterTable::MonsterStatsEntry *pFirst = table.findStatsById(1);
    REQUIRE(pFirst != nullptr);
    CHECK_EQ(pFirst->experience, 1565);
    CHECK_EQ(pFirst->hitPoints, 1080);
    CHECK_EQ(pFirst->attackPreferences, MonsterAttackPreferenceCleric | MonsterAttackPreferencePaladin);
    CHECK_EQ(table.findStatsById(2)->attackPreferences, MonsterAttackPreferenceMale);
    CHECK_EQ(table.findStatsById(3)->attackPreferences, MonsterAttackPreferenceKnight | MonsterAttackPreferenceArcher);
    CHECK_EQ(table.findStatsById(4)->attackPreferences, MonsterAttackPreferenceHuman);
    // A letter that names no preference is ignored.
    CHECK_EQ(table.findStatsById(5)->attackPreferences, 0u);
}

TEST_CASE("special enchantments end before the notes under the table")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Game::SpecialItemEnchantTable &table =
        OpenYAMM::Tests::regressionGameData().specialItemEnchantTable;

    REQUIRE_EQ(table.entries().size(), 73u);
    CHECK_EQ(table.get(73)->suffix, "of Sparking");
    CHECK(table.get(74) == nullptr);
}

TEST_CASE("damage pipelines run named stages in order, record them and stop early")
{
    struct Hit
    {
        int amount = 0;
        bool stop = false;
    };

    OpenYAMM::Game::DamagePipeline<Hit> pipeline;
    pipeline.add("double", [](Hit &hit) { hit.amount *= 2; });
    pipeline.add("cap", [](Hit &hit) { hit.amount = std::min(hit.amount, 25); hit.stop = hit.amount == 25; });
    pipeline.add("never", [](Hit &hit) { hit.amount = 0; });

    Hit hit = {};
    hit.amount = 20;
    std::vector<OpenYAMM::Game::DamageStageRecord> record;
    CHECK_EQ(pipeline.run(hit, &record), 25);
    REQUIRE_EQ(record.size(), 2u);
    CHECK_EQ(record[0].stage, "double");
    CHECK_EQ(record[0].before, 20);
    CHECK_EQ(record[0].after, 40);
    CHECK_EQ(record[1].after, 25);
}

TEST_CASE("the party carries the Standard rules until a ruleset installs its own")
{
    using namespace OpenYAMM::Game;
    Party party;
    CHECK(&party.rules() == &standardGameRules());
    CHECK(&gameRulesFor(nullptr) == &standardGameRules());
    CHECK_EQ(party.rules().experience.experienceForNextLevel(7), 28000u);
    CHECK_EQ(
        standardGameRules().combat.damageToCharacterStages().stageNames(),
        std::vector<std::string>{"missile-shield", "physical-taken", "resistance-and-armor"});
    CHECK_EQ(standardGameRules().combat.damageToMonsterStages().stageNames(), std::vector<std::string>{"resistance"});

    // A resisted hit on a monster through the Standard stages: immune at 200, untouched when irresistible.
    std::mt19937 rng(7);
    CHECK_EQ(resolveDamageToMonster(standardGameRules().combat, 40, CombatDamageType::Fire, 200, 0, rng, {}), 0);
    CHECK_EQ(resolveDamageToMonster(standardGameRules().combat, 40, CombatDamageType::Irresistible, 500, 0, rng, {}), 40);
}

TEST_CASE("random streams are reproducible from their key and independent across keys")
{
    using namespace OpenYAMM::Game;
    const uint64_t key = randomStreamKey(1234, RandomDomain::CraftDrop, 7, 3, 1);
    RandomStream first(key);
    RandomStream second(key);
    CHECK_EQ(first(), second());
    CHECK_EQ(first.uniform(1, 6), second.uniform(1, 6));
    CHECK_EQ(first.counter(), 2u);

    // Resuming from a saved counter continues the same sequence.
    RandomStream resumed(key, first.counter());
    CHECK_EQ(first(), resumed());

    CHECK_NE(
        randomStreamKey(1234, RandomDomain::CraftDrop, 7, 3, 1),
        randomStreamKey(1234, RandomDomain::CraftDrop, 7, 3, 2));
    CHECK_NE(randomStreamKey(1234, RandomDomain::CraftDrop, 7), randomStreamKey(1234, RandomDomain::CorpseLoot, 7));
    CHECK_NE(randomStreamKey(1234, RandomDomain::CraftDrop, 7), randomStreamKey(1235, RandomDomain::CraftDrop, 7));

    RandomStream dice(key);
    std::array<int, 6> counts = {};
    for (int roll = 0; roll < 6000; ++roll)
    {
        const uint32_t value = dice.uniform(1, 6);
        REQUIRE(value >= 1);
        REQUIRE(value <= 6);
        ++counts[value - 1];
    }
    for (int count : counts)
    {
        CHECK(count > 850);
        CHECK(count < 1150);
    }
}
