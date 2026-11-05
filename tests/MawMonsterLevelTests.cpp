#include "doctest/doctest.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/gameplay/GameMechanics.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawMonsterLevels.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/MapStats.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
std::vector<std::string> monsterRow(int id, const std::string &picture, int level)
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = picture;
    row[2] = picture;
    row[3] = std::to_string(level);
    row[4] = "100";
    row[10] = "Short";
    row[11] = "Normal";
    row[17] = "Phys";
    row[18] = "1d6";
    return row;
}

// The families of BALANCE_MODEL.md §7.7 with MAW's base levels.
MonsterTable exampleMonsters()
{
    std::vector<std::vector<std::string>> rows;
    const auto family = [&rows](int firstId, const std::string &picture, int a, int b, int c)
    {
        rows.push_back(monsterRow(firstId, picture + " A", a));
        rows.push_back(monsterRow(firstId + 1, picture + " B", b));
        rows.push_back(monsterRow(firstId + 2, picture + " C", c));
    };
    family(85, "Dire Wolf", 9, 14, 19);
    family(100, "Centaur", 11, 14, 18);
    family(193, "Human Mercenary", 10, 17, 24);
    family(538, "FighterLeath", 14, 20, 26);
    family(637, "BThief", 8, 12, 18);
    MonsterTable table;
    REQUIRE(table.loadStatsFromRows(rows));
    return table;
}

MawMapLevels exampleMapLevels()
{
    MawMapLevels mapLevels;
    std::string error;
    REQUIRE_MESSAGE(
        mapLevels.loadFromYaml(
            "bands:\n  out02.odm: [14, 14, 17]\n  6d03.blv: [11, 13, 15]\n"
            "horizontal_starter_maps: [out01.odm]\n"
            "madness:\n  starting_maps: [out01.odm]\n  levels:\n    6d03.blv: 43\n",
            error),
        error);
    return mapLevels;
}

std::vector<int> levelsOf(const std::unordered_map<int, int> &levels, const std::vector<int> &ids)
{
    std::vector<int> result;

    for (int id : ids)
    {
        result.push_back(levels.at(id));
    }

    return result;
}
}

TEST_CASE("MAW monster levels follow the Ravenshore worked example")
{
    const MonsterTable monsters = exampleMonsters();
    const MawMapLevels mapLevels = exampleMapLevels();
    MawMonsterLevelInputs inputs;
    inputs.mapFileName = "out02.odm";
    inputs.mapName = "Ravenshore";
    inputs.encounterPictures = {"Human Mercenary", "Centaur", "Dire Wolf"};
    const std::vector<int> ids = {85, 86, 87, 100, 101, 102, 193, 194, 195};

    CHECK_EQ(levelsOf(resolveMawMonsterLevels(monsters, mapLevels, inputs), ids),
             std::vector<int>{9, 14, 19, 11, 14, 18, 10, 17, 24});

    inputs.partyLevel = 100;
    CHECK_EQ(levelsOf(resolveMawMonsterLevels(monsters, mapLevels, inputs), ids),
             std::vector<int>{105, 110, 114, 107, 110, 113, 106, 112, 118});

    inputs.partyLevel = 0;
    inputs.horizontalProgression = true;
    CHECK_EQ(levelsOf(resolveMawMonsterLevels(monsters, mapLevels, inputs), ids),
             std::vector<int>{23, 28, 33, 25, 28, 32, 24, 31, 38});

    inputs.resetCount = 1;
    CHECK_EQ(levelsOf(resolveMawMonsterLevels(monsters, mapLevels, inputs), ids),
             std::vector<int>{43, 48, 53, 45, 48, 52, 44, 51, 58});
}

TEST_CASE("MAW monster levels on a Beyond Madness fixed-level map")
{
    MawMonsterLevelInputs inputs;
    inputs.mapFileName = "6d03.blv";
    inputs.mapName = "Shadow Guild Hideout";
    inputs.encounterPictures = {"BThief", "FighterLeath", "0"};
    inputs.horizontalProgression = true;
    inputs.madness = true;

    // BALANCE_MODEL.md §7.7: Thief 31, Burglar 39, Rogue 51, Thug 35, Ruffian 47, Brigand 59 (its text gives the band
    // as 11/15/15; map_levels.yml and these levels use 11/13/15).
    CHECK_EQ(levelsOf(resolveMawMonsterLevels(exampleMonsters(), exampleMapLevels(), inputs),
                      {637, 638, 639, 538, 539, 540}),
             std::vector<int>{31, 39, 51, 35, 47, 59});
    CHECK_EQ(mawFamilyBId(637), 638);
    CHECK_EQ(mawFamilyBId(639), 638);
}

TEST_CASE("the installed MAW map levels load")
{
    MawMapLevels mapLevels;
    std::string error;
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/map_levels.yml");
    const std::string text{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
    REQUIRE_MESSAGE(mapLevels.loadFromYaml(text, error), error);
    CHECK_EQ(mapLevels.band("OUT02.ODM"), std::array<double, 3>{14, 14, 17});
    CHECK_EQ(mapLevels.band("7out02.odm")[1], 11.5);
    CHECK_EQ(mapLevels.band("d22.blv"), std::array<double, 3>{40, 40, 40});
    CHECK(mapLevels.isHorizontalStarterMap("oute3.odm"));
    CHECK_EQ(mapLevels.madnessLevel("d37.blv"), 500);
    CHECK_EQ(mapLevels.madnessLevel("out02.odm"), 26);
    CHECK_EQ(mapLevels.madnessLevel("no_such_map.odm"), 0);
}

TEST_CASE("MAW monster rules size a spawn from its family's B level")
{
    const MonsterTable monsters = exampleMonsters();
    MawRules rules(RulesetOptions{}, exampleMapLevels());
    MapStatsEntry map = {};
    map.fileName = "out02.odm";
    map.name = "Ravenshore";
    map.encounter1.pictureName = "Human Mercenary";
    map.encounter2.pictureName = "Centaur";
    map.encounter3.pictureName = "Dire Wolf";
    map.mergedContinentId = 1;
    GameplayBolsterRuntimeContext context = {};
    context.pMap = &map;
    context.pMonsterTable = &monsters;
    const MonsterTable::MonsterStatsEntry *pStrong = monsters.findStatsById(195);
    REQUIRE(pStrong != nullptr);

    const GameplayMonsterBolsterResult strong = rules.gameRules().monsters.resolveMonster(context, *pStrong, nullptr);
    const ActorRulesetFacts &facts = strong.rulesetFacts;
    CHECK_EQ(facts.level, 24);
    CHECK_EQ(facts.familyLevel, 17);
    CHECK_EQ(facts.tier, 3);

    // Without a party the model sizes for five; every example row has the same HP, so the tier ratio is 1.
    MawBalanceModel model(mawModelConfig(RulesetOptions{}, 5));
    CHECK_EQ(strong.maxHp, int(mawRound(model.monsterHealth(17))));
    // Attack 1 is sized against the defence its damage kind meets (MAW 249b00da).
    const MawDamageClass attack1Class =
        GameMechanics::parseCombatDamageType(pStrong->attack1Type) == CombatDamageType::Physical
        ? MawDamageClass::Physical
        : MawDamageClass::Magic;
    CHECK(facts.attack1Damage == doctest::Approx(model.monsterDamage(17, attack1Class) * 1.5));
    CHECK_EQ(facts.experience, uint32_t(mawRound(24 * 20 + std::pow(24.0, 1.8))));
    CHECK_FALSE(strong.statsEnabled);

    // A reload keeps the actor's level and rolls: a boss's multipliers apply to the same family numbers.
    ActorRulesetFacts boss = facts;
    boss.bossHealthMultiplier = 3;
    boss.bossDamageMultiplier = 1.25f;
    context.pExistingFacts = &boss;
    const GameplayMonsterBolsterResult bossResult =
        rules.gameRules().monsters.resolveMonster(context, *pStrong, nullptr);
    CHECK_EQ(bossResult.rulesetFacts.level, 24);
    CHECK_EQ(bossResult.maxHp, int(mawRound(model.monsterHealth(17) * 3)));
    CHECK(bossResult.rulesetFacts.attack1Damage
        == doctest::Approx(model.monsterDamage(17, attack1Class) * 1.5 * 1.25));
}

TEST_CASE("MAW level banks follow the experience curve and the continent it was earned on")
{
    MawGameState state;
    state.addBankedExperience(1000, 1);
    CHECK(state.continentLevels[0] == doctest::Approx(2));
    state.addBankedExperience(44000, 3);
    CHECK(state.continentLevels[2] == doctest::Approx(8));
    CHECK(state.totalLevel() == doctest::Approx(10));
    CHECK(state.levelOutside(1) == doctest::Approx(8));
    CHECK(state.levelOutside(7) == doctest::Approx(10));

    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_EQ(rules.gameRules().experience.experienceForNextLevel(1), 1000u);
    CHECK_EQ(rules.gameRules().experience.experienceForNextLevel(100), 5050000u);
    CHECK_EQ(rules.gameRules().experience.experienceForNextLevel(149), 12804250u);
}

TEST_CASE("MAW monster density follows the difficulty")
{
    MapStatsEntry map = {};
    map.encounter1 = {.difficulty = 1, .minCount = 1, .maxCount = 3};
    map.encounter2 = {.difficulty = 2, .minCount = 0, .maxCount = 5};
    map.encounter3 = {.difficulty = 5, .minCount = 1, .maxCount = 1};
    const auto adjusted = [&map](RulesetDifficulty difficulty, RulesetChallengeMode mode)
    {
        RulesetOptions options;
        options.difficulty = difficulty;
        options.challengeMode = mode;
        MawRules rules(options, MawMapLevels{});
        MapStatsEntry copy = map;
        rules.gameRules().monsters.adjustMapEncounters(copy);
        return copy;
    };

    MapStatsEntry maw = adjusted(RulesetDifficulty::Maw, RulesetChallengeMode::None);
    CHECK_EQ(maw.encounter1.maxCount, 3);

    MapStatsEntry hard = adjusted(RulesetDifficulty::Hard, RulesetChallengeMode::None);
    CHECK_EQ(hard.encounter1.maxCount, 4);
    CHECK_EQ(hard.encounter2.maxCount, 5);
    CHECK_EQ(hard.encounter3.minCount, 1);

    MapStatsEntry nightmare = adjusted(RulesetDifficulty::Nightmare, RulesetChallengeMode::None);
    CHECK_EQ(nightmare.encounter1.minCount, 2);
    CHECK_EQ(nightmare.encounter1.difficulty, 2);
    CHECK_EQ(nightmare.encounter3.maxCount, 1);
    CHECK_EQ(nightmare.encounter3.difficulty, 5);

    MapStatsEntry doom = adjusted(RulesetDifficulty::Maw, RulesetChallengeMode::Doom);
    CHECK_EQ(doom.encounter2.maxCount, 7);
    CHECK_EQ(doom.encounter2.minCount, 2);
}

TEST_CASE("MAW picks bosses among a map's hostile unnamed C-tier monsters")
{
    const MonsterTable monsters = exampleMonsters();
    const MonsterTable::MonsterStatsEntry *pStrong = monsters.findStatsById(195);
    const MonsterTable::MonsterStatsEntry *pWeak = monsters.findStatsById(193);
    REQUIRE(pStrong != nullptr);
    REQUIRE(pWeak != nullptr);
    MapStatsEntry map = {};
    map.fileName = "out02.odm";
    GameplayBolsterRuntimeContext context = {};
    context.pMap = &map;
    context.pMonsterTable = &monsters;
    const auto place = [&](RulesetDifficulty difficulty, std::vector<ActorRulesetFacts> &facts)
    {
        RulesetOptions options;
        options.difficulty = difficulty;
        MawRules rules(options, MawMapLevels{});
        rules.setRandomRootSeed(1234);
        std::vector<MapMonsterPlacement> placements;
        for (size_t index = 0; index < facts.size(); ++index)
        {
            facts[index] = {.level = 24, .familyLevel = 17, .tier = 3};
            placements.push_back({index % 2 == 0 ? pStrong : pWeak, index == 0, true, &facts[index]});
        }
        return rules.gameRules().monsters.placeMapMonsters(context, placements);
    };

    std::vector<ActorRulesetFacts> facts(200);
    CHECK_FALSE(place(RulesetDifficulty::Normal, facts));

    REQUIRE(place(RulesetDifficulty::Maw, facts));
    size_t bosses = 0;
    for (size_t index = 0; index < facts.size(); ++index)
    {
        if (facts[index].bossAffix == 0)
        {
            continue;
        }
        ++bosses;
        // Only unnamed C rows: even indices hold the C row, index 0 is named.
        CHECK_EQ(index % 2, 0u);
        CHECK_NE(index, 0u);
        CHECK_EQ(facts[index].level, 2 * 24 - 17);
        CHECK(facts[index].bossHealthMultiplier >= 2.5f * (1 + 31.0f / 255));
        CHECK(facts[index].bossHealthMultiplier <= 3.75f * (1 + 31.0f / 255) + 1e-4f);
        CHECK(facts[index].bossDamageMultiplier >= 1.2f);
        CHECK(facts[index].bossDamageMultiplier <= 1.4f);
    }
    // ceil((200 - 30) / 150)
    CHECK_EQ(bosses, 2u);
}

TEST_CASE("MAW Nightmare rules: food for saving and no teleports near enemies")
{
    RulesetOptions options;
    MawRules maw(options, MawMapLevels{});
    CHECK_EQ(maw.gameRules().monsters.saveFoodCost("d08.blv", true, true), 0);
    CHECK_FALSE(maw.gameRules().monsters.teleportBlockedNearEnemies());

    options.difficulty = RulesetDifficulty::Nightmare;
    MawRules nightmare(options, MawMapLevels{});
    const MonsterRules &rules = nightmare.gameRules().monsters;
    CHECK(rules.teleportBlockedNearEnemies());
    CHECK_EQ(rules.saveFoodCost("D08.blv", true, false), 2);
    CHECK_EQ(rules.saveFoodCost("d08.blv", true, true), 10);
    CHECK_EQ(rules.saveFoodCost("out02.odm", false, false), 0);
    CHECK_EQ(rules.saveFoodCost("out02.odm", false, true), 3);
    // Free once cleared since the last refill (MON-3).
    nightmare.state().clearedSinceRefill.insert("d08.blv");
    CHECK_EQ(rules.saveFoodCost("D08.blv", true, true), 0);
}
