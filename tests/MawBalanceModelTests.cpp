#include "doctest/doctest.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawExperienceCurve.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

using OpenYAMM::Game::MawBalanceModel;
using OpenYAMM::Game::MawModelConfig;

namespace
{
std::vector<std::string> splitCsv(const std::string &line)
{
    std::vector<std::string> cells;
    std::stringstream stream(line);
    std::string cell;

    while (std::getline(stream, cell, ','))
    {
        cells.push_back(cell);
    }

    return cells;
}

MawModelConfig configNamed(const std::string &name, bool austerity, int partyCount, int difficulty)
{
    MawModelConfig config;
    config.difficulty = difficulty;
    config.austerity = austerity;
    config.partyCount = partyCount;
    config.trueNightmare = name.ends_with("nightmare");
    config.doomMode = name == "doom" || name == "insanity" || name == "madness";
    config.insanityMode = name == "insanity" || name == "madness";
    config.madnessMode = name == "madness";
    return config;
}

bool close(double actual, double expected)
{
    // The golden file keeps six significant digits.
    return std::abs(actual - expected) <= std::max(std::abs(expected) * 2e-5, 1e-6);
}
}

TEST_CASE("MAW balance model matches the golden output of MAW's own code")
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "devdocs/maw/data/balance_golden.csv");
    REQUIRE(input.good());
    std::string line;
    std::getline(input, line);
    const std::vector<std::string> header = splitCsv(line);
    std::map<std::string, MawBalanceModel> models;
    size_t rows = 0;
    size_t mismatches = 0;

    while (std::getline(input, line))
    {
        const std::vector<std::string> cells = splitCsv(line);
        REQUIRE_EQ(cells.size(), header.size());
        std::map<std::string, double> golden;

        for (size_t index = 1; index < cells.size(); ++index)
        {
            golden[header[index]] = std::stod(cells[index]);
        }

        const std::string key = cells[0] + "/" + cells[1] + "/" + cells[2];
        auto model = models.find(key);

        if (model == models.end())
        {
            model = models
                        .emplace(
                            key,
                            MawBalanceModel(configNamed(
                                cells[0], golden["austerity"] != 0, int(golden["party_count"]),
                                int(golden["difficulty"]))))
                        .first;
        }

        MawBalanceModel &m = model->second;
        const double level = golden["level"];
        const std::map<std::string, double> actual = {
            {"skill", m.skill(level)},
            {"mastery", m.mastery(level)},
            {"stat", m.stat(level)},
            {"geared", m.gearedFraction(level)},
            {"max_enchant", m.maxEnchantStrength(level)},
            {"health", m.health(level)},
            {"mana", m.mana(level)},
            {"armor_class", m.armorClass(level)},
            {"resistance", m.resistance(level)},
            {"enchant_resistance", m.enchantResistance(level)},
            {"phys_taken", m.physicalDamageTaken(level)},
            {"magic_taken", m.magicDamageTaken(level)},
            {"chance_hit", m.chanceToBeHit(level)},
            {"legendary_taken", m.legendaryDamageTaken(level)},
            {"cover_mult", m.coverMultiplier(level)},
            {"vitality", m.vitality(level)},
            {"attack", m.attack(level)},
            {"power", m.power(level)},
            {"spell_power", m.spellPower(level)},
            {"monster_hp_b", m.monsterHealth(level)},
            {"monster_dmg_b", m.monsterDamage(level)},
            {"exp_mult", m.monsterExperienceMultiplier()},
        };

        for (const auto &[column, value] : actual)
        {
            if (!close(value, golden[column]) && mismatches++ < 20)
            {
                FAIL_CHECK(key << " level " << level << " " << column << ": " << value << " expected "
                               << golden[column]);
            }
        }

        ++rows;
    }

    CHECK_EQ(rows, 4920u);
    CHECK_EQ(mismatches, 0u);
}

TEST_CASE("MAW experience curve and bolstered levels match exp_curve.yml")
{
    using namespace OpenYAMM::Game;
    // exp_curve.yml samples: level -> experience required.
    for (const auto &[level, experience] : std::vector<std::pair<double, double>>{
             {2, 1000}, {10, 45000}, {100, 4950000}, {102, 5151505}, {200, 24016750}, {500, 270917000},
             {1000, 1914750750}, {2000, 14323668250}, {3000, 35323668250}})
    {
        CAPTURE(level);
        CHECK_EQ(mawExperienceForLevel(level), doctest::Approx(experience));
        CHECK_EQ(mawLevelForExperience(experience), doctest::Approx(level));
    }

    CHECK_EQ(mawLevelForExperience(0), 1);
    CHECK_EQ(mawLevelForExperience(1500), doctest::Approx(2.25));

    // exp_curve.yml leveled_bolster_helper: (floor, levels) -> level.
    CHECK_EQ(mawBolsteredLevel(0, 50), doctest::Approx(50).epsilon(1e-3));
    CHECK_EQ(mawBolsteredLevel(50, 50), doctest::Approx(100).epsilon(1e-3));
    CHECK_EQ(mawBolsteredLevel(100, 30), doctest::Approx(128.23).epsilon(1e-3));
    CHECK_EQ(mawBolsteredLevel(100, 100), doctest::Approx(185.34).epsilon(1e-3));
    CHECK_EQ(mawBolsteredLevel(200, 50), doctest::Approx(232.86).epsilon(1e-3));
    CHECK_EQ(mawBolsteredLevel(500, 100), doctest::Approx(534.47).epsilon(1e-3));
    CHECK_EQ(mawBolsteredLevel(40, -5), 35);
}

TEST_CASE("MAW's challenge modes play the balance model of difficulty.yml at levels 20, 50 and 100 (phase 9 step 3)")
{
    using OpenYAMM::Game::RulesetChallengeMode;
    using OpenYAMM::Game::RulesetDifficulty;
    using OpenYAMM::Game::RulesetOptions;
    const std::filesystem::path data = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "devdocs/maw/data";
    const YAML::Node difficulties = YAML::LoadFile((data / "difficulty.yml").string());
    REQUIRE(difficulties["difficulties"]);

    // The golden run's monster HP and damage by config, party size and level.
    std::map<std::string, std::pair<double, double>> golden;
    std::ifstream input(data / "balance_golden.csv");
    REQUIRE(input.good());
    std::string line;
    std::getline(input, line);
    const std::vector<std::string> header = splitCsv(line);
    const auto column = [&header](const char *pName)
    {
        return size_t(std::find(header.begin(), header.end(), pName) - header.begin());
    };

    while (std::getline(input, line))
    {
        const std::vector<std::string> cells = splitCsv(line);
        golden[cells[0] + "/" + cells[column("party_count")] + "/" + cells[column("level")]] = {
            std::stod(cells[column("monster_hp_b")]), std::stod(cells[column("monster_dmg_b")])};
    }

    struct Mode
    {
        const char *pGolden;
        RulesetChallengeMode mode;
        RulesetDifficulty difficulty;
        int index;
    };

    const std::array<Mode, 7> modes = {{
        {"doom", RulesetChallengeMode::Doom, RulesetDifficulty::Nightmare, 7},
        {"insanity", RulesetChallengeMode::RoadToInsanity, RulesetDifficulty::Nightmare, 8},
        {"madness", RulesetChallengeMode::BeyondMadness, RulesetDifficulty::Nightmare, 9},
        {"aust_maw", RulesetChallengeMode::Austerity, RulesetDifficulty::Maw, 3},
        {"aust_hard", RulesetChallengeMode::Austerity, RulesetDifficulty::Hard, 4},
        {"aust_hell", RulesetChallengeMode::Austerity, RulesetDifficulty::Hell, 5},
        {"aust_nightmare", RulesetChallengeMode::Austerity, RulesetDifficulty::Nightmare, 6},
    }};

    for (const Mode &mode : modes)
    {
        CAPTURE(mode.pGolden);
        RulesetOptions options;
        options.challengeMode = mode.mode;
        options.difficulty = mode.difficulty;
        const bool austerity = mode.mode == RulesetChallengeMode::Austerity;
        const YAML::Node row = difficulties["difficulties"][mode.index];
        REQUIRE(row);

        for (const int partyCount : {1, 5})
        {
            CAPTURE(partyCount);
            const MawModelConfig config = OpenYAMM::Game::mawModelConfig(options, partyCount);
            const MawModelConfig expected = configNamed(
                austerity ? std::string(mode.pGolden).substr(5) : mode.pGolden, austerity, partyCount, mode.index);
            CHECK_EQ(config.difficulty, expected.difficulty);
            CHECK_EQ(config.austerity, expected.austerity);
            CHECK_EQ(config.doomMode, expected.doomMode);
            CHECK_EQ(config.insanityMode, expected.insanityMode);
            CHECK_EQ(config.madnessMode, expected.madnessMode);
            CHECK_EQ(config.trueNightmare, expected.trueNightmare);
            MawBalanceModel model(config);

            for (const int level : {20, 50, 100})
            {
                CAPTURE(level);
                // The hit tables: a monster takes monster_hp_hits of the expected hits, a member player_hits_to_die.
                CHECK(model.monsterHealth(level) / model.power(level)
                    == doctest::Approx(row[austerity ? "monster_hp_hits_aust" : "monster_hp_hits"].as<double>()));
                CHECK(model.vitality(level) / model.monsterDamage(level)
                    == doctest::Approx(row[austerity ? "player_hits_aust" : "player_hits_to_die"].as<double>()));

                const auto found = golden.find(std::string(mode.pGolden) + "/" + std::to_string(partyCount) + "/"
                    + std::to_string(level));
                REQUIRE(found != golden.end());
                CHECK(close(model.monsterHealth(level), found->second.first));
                CHECK(close(model.monsterDamage(level), found->second.second));
            }
        }
    }

    // HP and damage against MAW at level 100 and 300, party of 5 (relative_to_maw, two decimals).
    RulesetOptions mawOptions;
    MawBalanceModel maw(OpenYAMM::Game::mawModelConfig(mawOptions, 5));

    for (const Mode &mode : {modes[0], modes[1], modes[2]})
    {
        RulesetOptions options;
        options.challengeMode = mode.mode;
        options.difficulty = mode.difficulty;
        MawBalanceModel model(OpenYAMM::Game::mawModelConfig(options, 5));

        for (const int level : {100, 300})
        {
            CAPTURE(mode.pGolden);
            CAPTURE(level);
            const YAML::Node relative =
                difficulties["relative_to_maw"]["level_" + std::to_string(level)][mode.index];
            REQUIRE(relative);
            CHECK(model.monsterHealth(level) / maw.monsterHealth(level)
                == doctest::Approx(relative[0].as<double>()).epsilon(0.006));
            CHECK(model.monsterDamage(level) / maw.monsterDamage(level)
                == doctest::Approx(relative[1].as<double>()).epsilon(0.006));
        }
    }
}
