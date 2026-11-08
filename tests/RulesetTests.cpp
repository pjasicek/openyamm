#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/TextTable.h"
#include "game/content/ContentTableComposer.h"
#include "game/content/RulesetDefinition.h"
#include "game/content/RulesetOptions.h"
#include "game/data/GameDataLoader.h"
#include "game/debug/MawTestParties.h"
#include "game/events/EventRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/items/ItemEnchantTables.h"
#include "game/maps/SaveGame.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/SpellTable.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <optional>
#include <string>
#include <unordered_set>
#include <vector>

#include <yaml-cpp/yaml.h>

using OpenYAMM::Game::RulesetChallengeMode;
using OpenYAMM::Game::RulesetDefinition;
using OpenYAMM::Game::RulesetDifficulty;
using OpenYAMM::Game::RulesetLootFilterPreset;
using OpenYAMM::Game::RulesetOptions;
using OpenYAMM::Game::RulesetProgression;
using OpenYAMM::Game::RulesetSelection;

namespace
{
using Rows = std::vector<std::vector<std::string>>;

constexpr const char *MawRulesetYaml =
    "id: maw\n"
    "name: MAW\n"
    "description: Might and Magic rebalance\n"
    "credits: [Malekith, Rawsugar]\n"
    "guide_url: https://example.org/maw-guide/\n"
    "contentSchemaVersion: 2\n"
    "options:\n"
    "  difficulties: [easy, normal, maw, hard, hell, nightmare]\n"
    "  defaultDifficulty: maw\n"
    "  progressions: [free, horizontal]\n"
    "  defaultProgression: free\n"
    "  challengeModes: [none, doom]\n"
    "  randomizer: false\n"
    "  preferences: true\n"
    "skillNames:\n"
    "  Learning: Ascension\n"
    "tables:\n"
    "  - table: class_skills.txt\n"
    "    mode: override\n"
    "    path: patches/class_skills.txt\n"
    "  - table: items.txt\n"
    "    mode: override\n"
    "    path: patches/items.txt\n"
    "    headerRow: 1\n"
    "  - table: english/potion.txt\n"
    "    mode: replace\n"
    "    path: tables/potion.txt\n"
    "  - table: class_skills.txt\n"
    "    mode: override\n"
    "    path: content/class_skills_patch.txt\n";

std::filesystem::path makeTemporaryRoot(const std::string &name)
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_" + name + "_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

Rows classSkillRows()
{
    return {
        {"", "Archer", "Cleric", "Knight"},
        {"Staff", "B", "B", "E"},
        {"Sword", "E", "-", "M"},
        {"Bow", "G", "-", "E"},
    };
}

RulesetDefinition parseMaw()
{
    std::string error;
    const std::optional<RulesetDefinition> definition =
        OpenYAMM::Game::parseRulesetDefinition(MawRulesetYaml, "maw", error);
    REQUIRE_MESSAGE(definition.has_value(), error);
    return *definition;
}

std::vector<uint8_t> readBytes(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>()};
}

void writeBytes(const std::filesystem::path &path, const std::vector<uint8_t> &bytes)
{
    std::ofstream file(path, std::ios::binary);
    file.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
}

// The layout identities of minimalSave's current outdoor and indoor states (save version 162).
constexpr uint64_t OutdoorLayoutMarker = 0x0dd0a11ce0dd0a11ull;
constexpr uint64_t IndoorLayoutMarker = 0x0bb1a5e0bb1a5e01ull;

OpenYAMM::Game::GameSaveData minimalSave()
{
    OpenYAMM::Game::GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.saveName = "ruleset check";
    save.outdoorWorld.mapLayoutIdentity = OutdoorLayoutMarker;
    save.indoorScene.mapLayoutIdentity = IndoorLayoutMarker;
    return save;
}

std::optional<OpenYAMM::Game::GameSaveData> roundTrip(const OpenYAMM::Game::GameSaveData &save, std::string &error)
{
    const std::filesystem::path path = makeTemporaryRoot("ruleset_save").replace_extension(".oysav");
    REQUIRE_MESSAGE(OpenYAMM::Game::saveGameDataToPath(path, save, error), error);
    std::optional<OpenYAMM::Game::GameSaveData> restored = OpenYAMM::Game::loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    return restored;
}
}

TEST_CASE("ruleset table overrides set cells by key and by column name or index")
{
    Rows rows = classSkillRows();
    const Rows patch = {
        {"key", "column", "value"},
        {"Sword", "Archer", "M"},
        {"Bow", "#3", "G"},
        {"Staff", "Cleric", ""},
        {"", "", ""},
    };

    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::applyTableCellOverrides(rows, patch, 0, 0, error), error);
    CHECK_EQ(rows[2][1], "M");
    CHECK_EQ(rows[3][3], "G");
    CHECK_EQ(rows[1][2], "");
    // Untouched cells and the header keep their values.
    CHECK_EQ(rows[2][3], "M");
    CHECK_EQ(rows[0], classSkillRows()[0]);
}

TEST_CASE("ruleset table overrides use the configured key column and header row")
{
    Rows rows = {
        {"", "", ""},
        {"Name", "Item #", "Value"},
        {"Longsword", "1", "100"},
        {"Dagger", "2", "40"},
    };
    const Rows patch = {{"key", "column", "value"}, {"2", "Value", "55"}, {"1", "Name", "Broadsword"}};

    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::applyTableCellOverrides(rows, patch, 1, 1, error), error);
    CHECK_EQ(rows[3][2], "55");
    CHECK_EQ(rows[2][0], "Broadsword");
}

TEST_CASE("ruleset table overrides can extend a short row")
{
    Rows rows = {{"", "A", "B", "C"}, {"x", "1"}};
    const Rows patch = {{"key", "column", "value"}, {"x", "C", "3"}};

    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::applyTableCellOverrides(rows, patch, 0, 0, error), error);
    REQUIRE_EQ(rows[1].size(), 4u);
    CHECK_EQ(rows[1][3], "3");
}

TEST_CASE("ruleset table overrides can key rows by their number and append rows")
{
    Rows rows = {{"Bonus", "Suffix"}, {"Fire", "of Fire"}, {"Note", "a note"}};
    const Rows patch = {{"key", "column", "value"}, {"2", "Suffix", "of Ice"}, {"3", "Bonus", "Air"}};

    std::string error;
    REQUIRE_MESSAGE(
        OpenYAMM::Game::applyTableCellOverrides(rows, patch, OpenYAMM::Game::RowNumberKeyColumn, 0, error), error);
    REQUIRE_EQ(rows.size(), 4u);
    CHECK_EQ(rows[2][1], "of Ice");
    CHECK_EQ(rows[3][0], "Air");
    // The header row is not a patch target.
    Rows header = {{"key", "column", "value"}, {"0", "Bonus", "x"}};
    CHECK_FALSE(OpenYAMM::Game::applyTableCellOverrides(rows, header, OpenYAMM::Game::RowNumberKeyColumn, 0, error));

    Rows keyed = {{"Id", "Name"}, {"1", "One"}};
    REQUIRE_MESSAGE(OpenYAMM::Game::appendTableRows(keyed, {{"2", "Two"}}, 0, 0, error), error);
    CHECK_EQ(keyed.back()[1], "Two");
    CHECK_FALSE(OpenYAMM::Game::appendTableRows(keyed, {{"1", "Again"}}, 0, 0, error));
}

TEST_CASE("ruleset tables can gain columns for the rows they name")
{
    Rows rows = {{"Skill", "Archer", "Knight"}, {"Staff", "B", "E"}, {"Sword", "E"}, {"Bow", "M", "B"}};
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::appendTableColumns(
        rows, {{"", "Seraphim", "Shaman"}, {"Sword", "M", "-"}, {"Staff", "E"}}, 0, 0, error), error);
    CHECK_EQ(rows[0], std::vector<std::string>{"Skill", "Archer", "Knight", "Seraphim", "Shaman"});
    CHECK_EQ(rows[1], std::vector<std::string>{"Staff", "B", "E", "E", ""});
    // A short row is padded to the header before the new cells.
    CHECK_EQ(rows[2], std::vector<std::string>{"Sword", "E", "", "M", "-"});
    CHECK_EQ(rows[3], std::vector<std::string>{"Bow", "M", "B", "", ""});

    CHECK_FALSE(OpenYAMM::Game::appendTableColumns(rows, {{"", "Knight"}}, 0, 0, error));
    CHECK_FALSE(OpenYAMM::Game::appendTableColumns(rows, {{"", "Monk"}, {"Spear", "E"}}, 0, 0, error));
    CHECK_FALSE(OpenYAMM::Game::appendTableColumns(rows, {{"", "Monk"}, {"Bow", "E"}, {"Bow", "M"}}, 0, 0, error));

    // A cell past the header would be pushed under a new column, so it fails; empty trailing cells are dropped.
    Rows wide = {{"Skill", "Archer"}, {"Staff", "B", "stray"}};
    CHECK_FALSE(OpenYAMM::Game::appendTableColumns(wide, {{"", "Monk"}, {"Staff", "E"}}, 0, 0, error));
    Rows trailing = {{"Skill", "Archer"}, {"Staff", "B", ""}};
    REQUIRE_MESSAGE(OpenYAMM::Game::appendTableColumns(trailing, {{"", "Monk"}, {"Staff", "E"}}, 0, 0, error), error);
    CHECK_EQ(trailing[1], std::vector<std::string>{"Staff", "B", "E"});
}

TEST_CASE("ruleset table overrides reject what they cannot place exactly")
{
    const auto fails = [](Rows rows, const Rows &patch)
    {
        std::string error;
        const bool applied = OpenYAMM::Game::applyTableCellOverrides(rows, patch, 0, 0, error);
        CHECK_FALSE(error.empty());
        return !applied;
    };

    // Missing header, unknown key, unknown column, the key column itself, a cell patched twice.
    CHECK(fails(classSkillRows(), {{"Sword", "Archer", "M"}}));
    CHECK(fails(classSkillRows(), {{"key", "column", "value"}, {"Spear", "Archer", "M"}}));
    CHECK(fails(classSkillRows(), {{"key", "column", "value"}, {"Sword", "Paladin", "M"}}));
    CHECK(fails(classSkillRows(), {{"key", "column", "value"}, {"Sword", "#0", "Axe"}}));
    CHECK(fails(classSkillRows(), {{"key", "column", "value"}, {"Sword", "Archer", "M"}, {"Sword", "#1", "G"}}));

    // A key on two rows, a column name twice in the header.
    Rows repeatedKey = classSkillRows();
    repeatedKey.push_back({"Sword", "B", "B", "B"});
    CHECK(fails(repeatedKey, {{"key", "column", "value"}, {"Sword", "Archer", "M"}}));
    Rows repeatedColumn = classSkillRows();
    repeatedColumn[0][3] = "Archer";
    CHECK(fails(repeatedColumn, {{"key", "column", "value"}, {"Sword", "Archer", "M"}}));
    // The repeated column stays reachable by index.
    std::string error;
    CHECK(OpenYAMM::Game::applyTableCellOverrides(
        repeatedColumn, {{"key", "column", "value"}, {"Sword", "#3", "G"}}, 0, 0, error));
}

TEST_CASE("ruleset definitions parse choices, credits and tables")
{
    const RulesetDefinition maw = parseMaw();
    CHECK_EQ(maw.id, "maw");
    CHECK_EQ(maw.name, "MAW");
    CHECK_EQ(maw.contentSchemaVersion, 2u);
    CHECK_EQ(maw.credits.size(), 2u);
    CHECK_EQ(maw.guideUrl, "https://example.org/maw-guide/");
    CHECK(OpenYAMM::Game::standardRulesetDefinition().guideUrl.empty());
    CHECK_EQ(maw.choices.difficulties.size(), 6u);
    CHECK(maw.choices.defaultDifficulty == RulesetDifficulty::Maw);
    CHECK_EQ(maw.choices.progressions.size(), 2u);
    CHECK_EQ(maw.choices.challengeModes.size(), 2u);
    CHECK_FALSE(maw.choices.randomizer);
    CHECK(maw.choices.preferences);
    REQUIRE_EQ(maw.tables.size(), 4u);
    REQUIRE_EQ(maw.skillNames.size(), 1u);
    CHECK_EQ(maw.skillNames.at("Learning"), "Ascension");

    const std::vector<const OpenYAMM::Game::RulesetTableContribution *> items =
        maw.findTables("engine/data_tables/items.txt");
    REQUIRE_EQ(items.size(), 1u);
    CHECK(items.front()->mode == OpenYAMM::Game::TableContributionMode::Override);
    CHECK_EQ(items.front()->headerRow, 1u);
    const std::vector<const OpenYAMM::Game::RulesetTableContribution *> potions =
        maw.findTables("engine/data_tables/english/potion.txt");
    REQUIRE_EQ(potions.size(), 1u);
    CHECK(potions.front()->mode == OpenYAMM::Game::TableContributionMode::Replace);
    // A table's contributions apply in the order listed.
    const std::vector<const OpenYAMM::Game::RulesetTableContribution *> classSkills =
        maw.findTables("engine/data_tables/class_skills.txt");
    REQUIRE_EQ(classSkills.size(), 2u);
    CHECK_EQ(classSkills.front()->path, "patches/class_skills.txt");
    CHECK_EQ(classSkills.back()->path, "content/class_skills_patch.txt");
    CHECK(maw.findTables("engine/data_tables/spells.txt").empty());
    CHECK(maw.findTables("worlds/mm8/data_tables/items.txt").empty());
}

TEST_CASE("ruleset definitions reject invalid packages")
{
    const auto rejects = [](const std::string &yaml, const std::string &expectedId)
    {
        std::string error;
        const bool parsed = OpenYAMM::Game::parseRulesetDefinition(yaml, expectedId, error).has_value();
        CHECK_FALSE(error.empty());
        return !parsed;
    };

    CHECK(rejects("id: maw\nname: MAW\n", "other"));
    CHECK(rejects("id: mmerge\nname: Standard\n", "mmerge"));
    CHECK(rejects("id: Maw\nname: MAW\n", "Maw"));
    CHECK(rejects("id: maw\n", "maw"));
    CHECK(rejects("id: maw\nname: MAW\noptions:\n  difficulties: [easy]\n  defaultDifficulty: hell\n", "maw"));
    CHECK(rejects("id: maw\nname: MAW\noptions:\n  difficulties: [easy, easy]\n", "maw"));
    CHECK(rejects("id: maw\nname: MAW\noptions:\n  challengeModes: [doom, none]\n", "maw"));
    CHECK(rejects("id: maw\nname: MAW\ntables:\n  - {table: items.txt, mode: append, path: a.txt}\n", "maw"));
    CHECK(rejects("id: maw\nname: MAW\nskillNames:\n  Juggling: Ascension\n", "maw"));
    CHECK(rejects("id: maw\nname: MAW\ntables:\n  - {table: ../items.txt, mode: replace, path: a.txt}\n", "maw"));
    CHECK(rejects(
        "id: maw\nname: MAW\ntables:\n  - {table: a.txt, mode: override, path: b.txt}\n"
        "  - {table: a.txt, mode: override, path: b.txt}\n",
        "maw"));
}

TEST_CASE("rulesets offer only their listed options")
{
    const RulesetDefinition maw = parseMaw();
    const RulesetOptions defaults = maw.defaultOptions();
    CHECK(defaults.difficulty == RulesetDifficulty::Maw);
    CHECK(defaults.progression == RulesetProgression::Free);
    CHECK(maw.offers(defaults));

    RulesetOptions options = defaults;
    options.difficulty = RulesetDifficulty::Nightmare;
    options.progression = RulesetProgression::Horizontal;
    options.challengeMode = RulesetChallengeMode::Doom;
    options.preferences.lootFilter = OpenYAMM::Game::rulesetLootFilterWithPreset(RulesetLootFilterPreset::Strict);
    CHECK(maw.offers(options));
    options.challengeMode = RulesetChallengeMode::Austerity;
    CHECK_FALSE(maw.offers(options));
    options.challengeMode = RulesetChallengeMode::None;
    options.randomizer = true;
    CHECK_FALSE(maw.offers(options));

    // Standard offers nothing but its defaults.
    const RulesetDefinition standard = OpenYAMM::Game::standardRulesetDefinition();
    CHECK(standard.isStandard());
    CHECK(standard.offers(standard.defaultOptions()));
    RulesetOptions hell = standard.defaultOptions();
    hell.difficulty = RulesetDifficulty::Hell;
    CHECK_FALSE(standard.offers(hell));
}

TEST_CASE("ruleset difficulty locks and the load-screen badge")
{
    RulesetSelection selection;
    CHECK(selection.isStandard());
    CHECK(OpenYAMM::Game::describeRulesetSelection(selection, "Standard").empty());

    selection.id = "maw";
    selection.options.difficulty = RulesetDifficulty::Hell;
    selection.options.progression = RulesetProgression::Horizontal;
    CHECK_FALSE(selection.options.difficultyLocked());
    CHECK_EQ(OpenYAMM::Game::describeRulesetSelection(selection, "MAW"), "MAW · Hell difficulty · Horizontal progression");

    selection.options.difficulty = RulesetDifficulty::Nightmare;
    CHECK(selection.options.difficultyLocked());
    selection.options.difficulty = RulesetDifficulty::Easy;
    selection.options.challengeMode = RulesetChallengeMode::RoadToInsanity;
    CHECK(selection.options.difficultyLocked());
    CHECK_EQ(
        OpenYAMM::Game::describeRulesetSelection(selection, ""),
        "maw · Easy difficulty · Horizontal progression · Road to Insanity");
}

TEST_CASE("ruleset option ids parse back to their values")
{
    for (const RulesetDifficulty difficulty :
         {RulesetDifficulty::Easy, RulesetDifficulty::Normal, RulesetDifficulty::Maw, RulesetDifficulty::Hard,
          RulesetDifficulty::Hell, RulesetDifficulty::Nightmare})
    {
        CHECK(OpenYAMM::Game::parseRulesetDifficulty(OpenYAMM::Game::rulesetDifficultyId(difficulty)) == difficulty);
    }

    CHECK(OpenYAMM::Game::parseRulesetChallengeMode("beyond_madness") == RulesetChallengeMode::BeyondMadness);
    CHECK(OpenYAMM::Game::parseRulesetLootFilterPreset("very_strict") == RulesetLootFilterPreset::VeryStrict);
    CHECK_FALSE(OpenYAMM::Game::parseRulesetProgression("vertical").has_value());
}

TEST_CASE("mounted ruleset packages are listed after Standard")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot("rulesets");
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeTextFile(assetRoot / "engine" / "rulesets" / "maw" / "ruleset.yml", MawRulesetYaml);
    writeTextFile(assetRoot / "engine" / "rulesets" / "notes" / "readme.txt", "not a ruleset package\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, assetRoot, OpenYAMM::Engine::AssetScaleTier::X1, "mm8"));

        std::vector<RulesetDefinition> rulesets;
        std::string error;
        REQUIRE_MESSAGE(OpenYAMM::Game::loadAvailableRulesets(assetFileSystem, rulesets, error), error);
        REQUIRE_EQ(rulesets.size(), 2u);
        CHECK(rulesets[0].isStandard());
        CHECK_EQ(rulesets[1].id, "maw");

        CHECK(OpenYAMM::Game::loadRulesetDefinition(assetFileSystem, "mmerge", error).has_value());
        CHECK_FALSE(OpenYAMM::Game::loadRulesetDefinition(assetFileSystem, "hardcore", error).has_value());
        CHECK_FALSE(error.empty());
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("saves keep the ruleset and its options")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.ruleset.id = "maw";
    save.ruleset.options.difficulty = RulesetDifficulty::Hell;
    save.ruleset.options.progression = RulesetProgression::Horizontal;
    save.ruleset.options.challengeMode = RulesetChallengeMode::Doom;
    save.ruleset.options.randomizer = true;
    save.ruleset.options.preferences.homingProjectiles = false;
    save.ruleset.options.preferences.friendlyFire = true;
    save.ruleset.options.preferences.trainerHints = true;
    save.ruleset.options.preferences.bowDisabled = true;
    save.ruleset.options.preferences.lootFilter =
        OpenYAMM::Game::rulesetLootFilterWithPreset(RulesetLootFilterPreset::VeryStrict, true);
    save.ruleset.options.preferences.lootFilter.goldKinds |= 1u << unsigned(OpenYAMM::Game::RulesetLootKind::Gems);

    std::string error;
    const std::optional<OpenYAMM::Game::GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK(restored->ruleset == save.ruleset);
    CHECK_EQ(restored->saveName, "ruleset check");

    const std::optional<OpenYAMM::Game::GameSaveData> standard = roundTrip(minimalSave(), error);
    REQUIRE_MESSAGE(standard.has_value(), error);
    CHECK(standard->ruleset.isStandard());
    CHECK(standard->ruleset == RulesetSelection{});
}

TEST_CASE("saves with out-of-range ruleset options are refused")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.ruleset.id = "maw";
    save.ruleset.options.difficulty = RulesetDifficulty(9);

    std::string error;
    CHECK_FALSE(roundTrip(save, error).has_value());
    CHECK_FALSE(error.empty());
}

namespace
{
void eraseBytes(std::vector<uint8_t> &bytes, size_t offset, size_t count)
{
    bytes.erase(
        bytes.begin() + static_cast<std::ptrdiff_t>(offset),
        bytes.begin() + static_cast<std::ptrdiff_t>(offset + count));
}

template <typename T>
size_t findValue(const std::vector<uint8_t> &bytes, const T &value)
{
    uint8_t pattern[sizeof(T)] = {};
    std::memcpy(pattern, &value, sizeof(T));
    const auto found = std::search(bytes.begin(), bytes.end(), std::begin(pattern), std::end(pattern));
    REQUIRE(found != bytes.end());
    CHECK(std::search(found + 1, bytes.end(), std::begin(pattern), std::end(pattern)) == bytes.end());
    return static_cast<size_t>(found - bytes.begin());
}

// Saves before version 162 have no map layout identities: cuts minimalSave's two, for a save stamped older.
// Saves from version 163 end with the playthrough id and its statistics timeline: two strings, empty in these saves.
void erasePlaythroughStatistics(std::vector<uint8_t> &bytes)
{
    REQUIRE(bytes.size() >= 2 * sizeof(uint64_t));
    const size_t offset = bytes.size() - 2 * sizeof(uint64_t);
    REQUIRE(std::all_of(bytes.begin() + static_cast<std::ptrdiff_t>(offset), bytes.end(),
        [](uint8_t value) { return value == 0; }));
    eraseBytes(bytes, offset, 2 * sizeof(uint64_t));
}

// Cuts `count` empty counts or strings (a zero length each) at offset.
void eraseEmptyCounts(std::vector<uint8_t> &bytes, size_t offset, size_t count)
{
    for (size_t index = 0; index < count; ++index)
    {
        uint64_t value = 1;
        std::memcpy(&value, bytes.data() + offset + index * sizeof(uint64_t), sizeof(value));
        REQUIRE_EQ(value, 0u);
    }

    eraseBytes(bytes, offset, count * sizeof(uint64_t));
}

void eraseMapLayoutIdentities(std::vector<uint8_t> &bytes)
{
    eraseBytes(bytes, findValue(bytes, OutdoorLayoutMarker), sizeof(uint64_t));
    eraseBytes(bytes, findValue(bytes, IndoorLayoutMarker), sizeof(uint64_t));
}

// Saves from version 140 lead with the summary block (its size, the map, the time, the ruleset, the name and the
// preview); older ones keep the map after the scene kind, the time before the camera yaw, the ruleset before the
// random root seed and the name and preview at the end. Moves them back, for a save then stamped with an older version.
// Saves before version 143 end the party without its completion records; save carries one record named by marker.
void eraseWorldCompletions(std::vector<uint8_t> &bytes, const std::string &marker)
{
    const auto markerIt = std::search(bytes.begin(), bytes.end(), marker.begin(), marker.end());
    REQUIRE(markerIt != bytes.end());
    // The record count and the id's length before the id; game minutes, score, real time and the timed flag after it,
    // then the untracked flag, and the empty counts of chosen MM9 talk rows (version 146), of bought Ledgers of
    // Teachers (153), of MM9 hirelings (157) and of member formation cells (158) and the empty last outdoor map (155)
    // that follow.
    const size_t offset = static_cast<size_t>(markerIt - bytes.begin()) - 2 * sizeof(uint64_t);
    eraseBytes(bytes, offset,
        2 * sizeof(uint64_t) + marker.size() + sizeof(float) + sizeof(uint64_t) + sizeof(int64_t) + 2 * sizeof(bool)
            + 5 * sizeof(uint64_t));
}

// The party's empty count of member formation cells (version 158) and its empty last outdoor map (155), the last of
// the party, after its one completion record (named by marker), the untracked flag and the empty counts of chosen MM9
// talk rows, Ledgers of Teachers and MM9 hirelings.
void eraseMemberFormationCount(std::vector<uint8_t> &bytes, const std::string &marker)
{
    const auto markerIt = std::search(bytes.begin(), bytes.end(), marker.begin(), marker.end());
    REQUIRE(markerIt != bytes.end());
    const size_t offset = static_cast<size_t>(markerIt - bytes.begin()) + marker.size() + sizeof(float)
        + sizeof(uint64_t) + sizeof(int64_t) + 2 * sizeof(bool) + 3 * sizeof(uint64_t);
    eraseEmptyCounts(bytes, offset, 2);
}

// The party's empty count of MM9 hirelings (version 157), after its one completion record (named by marker), the
// untracked flag and the empty counts of chosen MM9 talk rows and Ledgers of Teachers; with the formation cells'
// count after it (158) and the last outdoor map (155), so the party ends as before version 155.
void eraseMm9HirelingCount(std::vector<uint8_t> &bytes, const std::string &marker)
{
    eraseMemberFormationCount(bytes, marker);
    const auto markerIt = std::search(bytes.begin(), bytes.end(), marker.begin(), marker.end());
    REQUIRE(markerIt != bytes.end());
    const size_t offset = static_cast<size_t>(markerIt - bytes.begin()) + marker.size() + sizeof(float)
        + sizeof(uint64_t) + sizeof(int64_t) + 2 * sizeof(bool) + 2 * sizeof(uint64_t);
    uint64_t count = 1;
    std::memcpy(&count, bytes.data() + offset, sizeof(count));
    REQUIRE_EQ(count, 0u);
    eraseBytes(bytes, offset, sizeof(uint64_t));
}

void moveSummaryToLegacyPlaces(
    std::vector<uint8_t> &bytes, const OpenYAMM::Game::GameSaveData &save, float yawMarker, uint64_t seedMarker)
{
    constexpr size_t HeaderSize = 8 + sizeof(uint32_t);
    uint32_t summarySize = 0;
    std::memcpy(&summarySize, bytes.data() + HeaderSize, sizeof(summarySize));
    const std::vector<uint8_t> summary(
        bytes.begin() + static_cast<std::ptrdiff_t>(HeaderSize + sizeof(summarySize)),
        bytes.begin() + static_cast<std::ptrdiff_t>(HeaderSize + sizeof(summarySize) + summarySize));
    eraseBytes(bytes, HeaderSize, sizeof(summarySize) + summarySize);

    const size_t mapSize = sizeof(uint64_t) + save.mapFileName.size();
    const size_t minutesSize = sizeof(float);
    const size_t nameAndPreviewSize =
        sizeof(uint64_t) + save.saveName.size() + sizeof(uint64_t) + save.previewBmp.size();
    REQUIRE(summary.size() > mapSize + minutesSize + nameAndPreviewSize);
    const auto piece = [&summary](size_t offset, size_t size)
    {
        return std::vector<uint8_t>(summary.begin() + static_cast<std::ptrdiff_t>(offset),
            summary.begin() + static_cast<std::ptrdiff_t>(offset + size));
    };
    const std::vector<uint8_t> map = piece(0, mapSize);
    const std::vector<uint8_t> minutes = piece(mapSize, minutesSize);
    const size_t rulesetOffset = mapSize + minutesSize;
    // Without its last two bytes, the trainer hints and bow preferences of versions 152 and 154, which no summary-less
    // save has.
    const std::vector<uint8_t> ruleset =
        piece(rulesetOffset, summary.size() - rulesetOffset - nameAndPreviewSize - 2 * sizeof(bool));
    const std::vector<uint8_t> nameAndPreview = piece(summary.size() - nameAndPreviewSize, nameAndPreviewSize);

    bytes.insert(bytes.end(), nameAndPreview.begin(), nameAndPreview.end());
    const size_t seedOffset = findValue(bytes, seedMarker);
    bytes.insert(bytes.begin() + static_cast<std::ptrdiff_t>(seedOffset), ruleset.begin(), ruleset.end());
    const size_t yawOffset = findValue(bytes, yawMarker);
    bytes.insert(bytes.begin() + static_cast<std::ptrdiff_t>(yawOffset), minutes.begin(), minutes.end());
    const size_t sceneKindEnd = HeaderSize + sizeof(OpenYAMM::Game::SceneKind);
    bytes.insert(bytes.begin() + static_cast<std::ptrdiff_t>(sceneKindEnd), map.begin(), map.end());
}
}

TEST_CASE("saves written before rulesets load as the Standard ruleset")
{
    // Write a save, then cut out what versions 96-98 added and stamp version 95: the ruleset block, the random root
    // seed, the absent MAW state and the held item's ruleset-fields byte. Marker values locate each.
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.ruleset.id = "rulesetmarker";
    save.ruleset.options.difficulty = RulesetDifficulty::Nightmare;
    const uint64_t seedMarker = 0x1122334455667788ull;
    save.randomRootSeed = seedMarker;
    const float heldItemMarker = 12345.678f;
    save.heldInventoryItem.temporaryBonusRemainingSeconds = heldItemMarker;
    const float yawMarker = 2.71828f;
    save.cameraYawRadians = yawMarker;
    const std::string completionMarker = "completionmarker";
    save.party.worldCompletions.push_back({completionMarker});
    const std::filesystem::path path = makeTemporaryRoot("ruleset_legacy").replace_extension(".oysav");
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::saveGameDataToPath(path, save, error), error);

    std::vector<uint8_t> bytes = readBytes(path);
    erasePlaythroughStatistics(bytes);
    eraseWorldCompletions(bytes, completionMarker);
    moveSummaryToLegacyPlaces(bytes, save, yawMarker, seedMarker);
    // The seed directly follows the ruleset and the MAW state's presence byte follows the seed, so cut them first.
    eraseBytes(bytes, findValue(bytes, seedMarker), sizeof(seedMarker) + 1);
    const std::string marker = "rulesetmarker";
    const auto markerIt = std::search(bytes.begin(), bytes.end(), marker.begin(), marker.end());
    REQUIRE(markerIt != bytes.end());
    // The id (length and text) and ten option bytes (the disintegration preference since version 113, the loot filter's
    // preset, kinds and ground flag in place of its one rarity byte since 126).
    eraseBytes(
        bytes,
        static_cast<size_t>(markerIt - bytes.begin()) - sizeof(uint64_t),
        sizeof(uint64_t) + marker.size() + 10);
    // The held item ends with the bonus timer, the hardened flag, the ruleset-fields byte and the Workshop mod (136).
    eraseBytes(bytes, findValue(bytes, heldItemMarker) + sizeof(float) + 1, 1 + sizeof(uint16_t));
    eraseMapLayoutIdentities(bytes);
    const uint32_t previousVersion = 95;
    std::memcpy(bytes.data() + 8, &previousVersion, sizeof(previousVersion));
    writeBytes(path, bytes);

    const std::optional<OpenYAMM::Game::GameSaveData> restored = OpenYAMM::Game::loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK(restored->ruleset == RulesetSelection{});
    CHECK_EQ(restored->randomRootSeed, 0u);
    CHECK_EQ(restored->heldInventoryItem.temporaryBonusRemainingSeconds, heldItemMarker);
    CHECK_EQ(restored->saveName, "ruleset check");
}

TEST_CASE("the save list reads a save's summary alone, and older saves' summary from the whole save")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.savedGameMinutes = 98765.0f;
    save.ruleset.id = "maw";
    save.ruleset.options.difficulty = RulesetDifficulty::Hell;
    save.previewBmp = {'B', 'M', 1, 2, 3};
    const float yawMarker = 2.71828f;
    save.cameraYawRadians = yawMarker;
    const uint64_t seedMarker = 0x1122334455667788ull;
    save.randomRootSeed = seedMarker;
    const std::string completionMarker = "completionmarker";
    save.party.worldCompletions.push_back({completionMarker});
    const std::filesystem::path path = makeTemporaryRoot("save_summary").replace_extension(".oysav");
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::saveGameDataToPath(path, save, error), error);

    const auto checkSummary = [&save](const std::optional<OpenYAMM::Game::GameSaveSummary> &summary)
    {
        REQUIRE(summary.has_value());
        CHECK_EQ(summary->mapFileName, save.mapFileName);
        CHECK_EQ(summary->savedGameMinutes, save.savedGameMinutes);
        CHECK(summary->ruleset == save.ruleset);
        CHECK_EQ(summary->saveName, save.saveName);
        CHECK(summary->previewBmp == save.previewBmp);
    };
    checkSummary(OpenYAMM::Game::loadGameSaveSummaryFromPath(path, error));

    const std::optional<OpenYAMM::Game::GameSaveData> restored = OpenYAMM::Game::loadGameDataFromPath(path, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK_EQ(restored->cameraYawRadians, yawMarker);
    CHECK_EQ(restored->randomRootSeed, seedMarker);
    checkSummary(OpenYAMM::Game::GameSaveSummary{restored->mapFileName, restored->savedGameMinutes,
        restored->ruleset, restored->saveName, restored->previewBmp});

    std::vector<uint8_t> bytes = readBytes(path);
    erasePlaythroughStatistics(bytes);
    eraseWorldCompletions(bytes, completionMarker);
    moveSummaryToLegacyPlaces(bytes, save, yawMarker, seedMarker);
    eraseMapLayoutIdentities(bytes);
    const uint32_t previousVersion = 139;
    std::memcpy(bytes.data() + 8, &previousVersion, sizeof(previousVersion));
    writeBytes(path, bytes);
    checkSummary(OpenYAMM::Game::loadGameSaveSummaryFromPath(path, error));

    // A summary that claims more than the file holds is refused rather than read past the end.
    bytes = readBytes(path);
    const uint32_t currentVersion = 140;
    std::memcpy(bytes.data() + 8, &currentVersion, sizeof(currentVersion));
    const uint32_t oversizedSummary = uint32_t(bytes.size());
    bytes.insert(bytes.begin() + 12, reinterpret_cast<const uint8_t *>(&oversizedSummary),
        reinterpret_cast<const uint8_t *>(&oversizedSummary) + sizeof(oversizedSummary));
    writeBytes(path, bytes);
    CHECK_FALSE(OpenYAMM::Game::loadGameSaveSummaryFromPath(path, error).has_value());
    std::filesystem::remove(path);
}

TEST_CASE("saves before the Bow preference load with the bow on")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.ruleset.id = "maw";
    save.ruleset.options.preferences.trainerHints = true;
    save.ruleset.options.preferences.bowDisabled = true;
    const std::string completionMarker = "completionmarker";
    save.party.worldCompletions.push_back({completionMarker});
    const std::filesystem::path path = makeTemporaryRoot("bow_preference").replace_extension(".oysav");
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::saveGameDataToPath(path, save, error), error);

    // The summary block holds the map, the time, the ruleset, the name and the preview; the Bow preference (version
    // 154) is the ruleset's last byte, after the trainer hints (152). Cut it and stamp version 153.
    std::vector<uint8_t> bytes = readBytes(path);
    constexpr size_t HeaderSize = 8 + sizeof(uint32_t);
    uint32_t summarySize = 0;
    std::memcpy(&summarySize, bytes.data() + HeaderSize, sizeof(summarySize));
    const size_t nameAndPreviewSize =
        sizeof(uint64_t) + save.saveName.size() + sizeof(uint64_t) + save.previewBmp.size();
    const size_t bowOffset = HeaderSize + sizeof(summarySize) + summarySize - nameAndPreviewSize - sizeof(bool);
    REQUIRE_EQ(bytes[bowOffset], 1);
    REQUIRE_EQ(bytes[bowOffset - 1], 1);
    eraseBytes(bytes, bowOffset, sizeof(bool));
    --summarySize;
    std::memcpy(bytes.data() + HeaderSize, &summarySize, sizeof(summarySize));
    eraseMm9HirelingCount(bytes, completionMarker);
    eraseMapLayoutIdentities(bytes);
    const uint32_t previousVersion = 153;
    std::memcpy(bytes.data() + 8, &previousVersion, sizeof(previousVersion));
    writeBytes(path, bytes);

    const std::optional<OpenYAMM::Game::GameSaveData> restored = OpenYAMM::Game::loadGameDataFromPath(path, error);
    const std::optional<OpenYAMM::Game::GameSaveSummary> summary =
        OpenYAMM::Game::loadGameSaveSummaryFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK_FALSE(restored->ruleset.options.preferences.bowDisabled);
    CHECK(restored->ruleset.options.preferences.trainerHints);
    CHECK_EQ(restored->saveName, "ruleset check");
    REQUIRE(summary.has_value());
    CHECK_FALSE(summary->ruleset.options.preferences.bowDisabled);
}

TEST_CASE("saves before the MM9 hirelings load with none")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.ruleset.options.preferences.bowDisabled = true;
    const std::string completionMarker = "completionmarker";
    save.party.worldCompletions.push_back({completionMarker});
    const std::filesystem::path path = makeTemporaryRoot("mm9_hirelings").replace_extension(".oysav");
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::saveGameDataToPath(path, save, error), error);

    // Cut the party's hireling count (version 157) and stamp version 154 (before the last outdoor map, 155).
    std::vector<uint8_t> bytes = readBytes(path);
    eraseMm9HirelingCount(bytes, completionMarker);
    eraseMapLayoutIdentities(bytes);
    const uint32_t previousVersion = 154;
    std::memcpy(bytes.data() + 8, &previousVersion, sizeof(previousVersion));
    writeBytes(path, bytes);

    const std::optional<OpenYAMM::Game::GameSaveData> restored = OpenYAMM::Game::loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK(restored->party.mm9Hirelings.empty());
    REQUIRE_EQ(restored->party.worldCompletions.size(), 1u);
    CHECK_EQ(restored->party.worldCompletions[0].certificateId, completionMarker);
    CHECK(restored->ruleset.options.preferences.bowDisabled);
    CHECK_EQ(restored->saveName, "ruleset check");
}

TEST_CASE("saves before the MM9 formation load without member cells and with neutral hireling stats")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    OpenYAMM::Game::Mm9PartyHireling hireling;
    hireling.rudeId = 42;
    hireling.character.name = "Hrolf Spearmaster";
    // The hireling's last saved field, found again in the bytes: the formation cell count follows it.
    const int32_t cellMarker = 0x7e57ce11;
    hireling.formationCell = cellMarker;
    // Its character's condition expiry times (version 159, after the formation): found by the first one's value.
    const float expiryMarker = 123456.5f;
    hireling.character.conditionExpireGameMinutes[0] = expiryMarker;
    save.party.mm9Hirelings.push_back(hireling);
    const std::filesystem::path path = makeTemporaryRoot("mm9_formation").replace_extension(".oysav");
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::saveGameDataToPath(path, save, error), error);

    // Cut the party's formation cell count (version 158) and stamp version 157.
    std::vector<uint8_t> bytes = readBytes(path);
    std::array<uint8_t, sizeof(cellMarker)> markerBytes = {};
    std::memcpy(markerBytes.data(), &cellMarker, sizeof(cellMarker));
    const auto markerIt = std::search(bytes.begin(), bytes.end(), markerBytes.begin(), markerBytes.end());
    REQUIRE(markerIt != bytes.end());
    // The party's empty last outdoor map after it (version 155) stays.
    const size_t countOffset = static_cast<size_t>(markerIt - bytes.begin()) + sizeof(cellMarker);
    eraseEmptyCounts(bytes, countOffset, 1);
    // A version 157 character has no condition expiry times either (version 159), nor the statistics identity after
    // them (163).
    std::array<uint8_t, sizeof(expiryMarker)> expiryBytes = {};
    std::memcpy(expiryBytes.data(), &expiryMarker, sizeof(expiryMarker));
    const auto expiryIt = std::search(bytes.begin(), bytes.end(), expiryBytes.begin(), expiryBytes.end());
    REQUIRE(expiryIt != bytes.end());
    eraseBytes(bytes, static_cast<size_t>(expiryIt - bytes.begin()),
        sizeof(float) * hireling.character.conditionExpireGameMinutes.size() + sizeof(uint64_t));
    erasePlaythroughStatistics(bytes);
    eraseMapLayoutIdentities(bytes);
    const uint32_t previousVersion = 157;
    std::memcpy(bytes.data() + 8, &previousVersion, sizeof(previousVersion));
    writeBytes(path, bytes);

    const std::optional<OpenYAMM::Game::GameSaveData> restored = OpenYAMM::Game::loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK(restored->party.memberFormationCells.empty());
    REQUIRE_EQ(restored->party.mm9Hirelings.size(), 1u);
    const OpenYAMM::Game::Character &character = restored->party.mm9Hirelings[0].character;
    CHECK_EQ(character.might, OpenYAMM::Game::Party::Mm9HirelingPrimaryStat);
    CHECK_EQ(character.speed, OpenYAMM::Game::Party::Mm9HirelingPrimaryStat);
    CHECK_EQ(character.luck, OpenYAMM::Game::Party::Mm9HirelingPrimaryStat);
    CHECK_EQ(restored->saveName, "ruleset check");
}

TEST_CASE("saves keep a character's experience past 32 bits")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    OpenYAMM::Game::Character member;
    member.name = "Ascended";
    member.level = 1100;
    member.experience = 4011174940ull + 123;
    member.extraQuickSpellNames = {"Fire Bolt", "", "Heal", "Meteor Shower"};
    member.quickItemSlots[0] = {222, OpenYAMM::Game::QuickItemBottleRule::Weakest};
    member.quickItemSlots[4] = {300, OpenYAMM::Game::QuickItemBottleRule::Strongest};
    save.party.members.push_back(member);

    std::string error;
    const std::optional<OpenYAMM::Game::GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    REQUIRE_EQ(restored->party.members.size(), 1u);
    CHECK_EQ(restored->party.members[0].experience, 4011174940ull + 123);
    // MMMerge's extra quick spells (save version 122).
    CHECK(restored->party.members[0].extraQuickSpellNames == member.extraQuickSpellNames);
    // The potion radial's slots (save version 125).
    CHECK(restored->party.members[0].quickItemSlots == member.quickItemSlots);
}

TEST_CASE("older saves move the MM6 maps' SetTexture swaps to the face they name")
{
    // Audit STD3-6, plan D10: the MM6 scripts name faces with a negative reference now, stored under the face key;
    // saves before version 115 kept the face number itself, which the renderer now reads as a cog.
    const uint32_t faceKey = OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(2011);
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.sourceSaveVersion = 94;
    save.indoorSceneStates["6d01.blv"].eventRuntimeState.emplace().textureOverrides[2011] = "lever_down";
    save.indoorSceneStates["7d08.blv"].eventRuntimeState.emplace().textureOverrides[1] = "cog_swap";
    const auto isMm6 = [](const std::string &mapFileName) { return mapFileName == "6d01.blv"; };

    OpenYAMM::Game::GameSaveData current = save;
    current.sourceSaveVersion = 115;
    OpenYAMM::Game::migrateLegacyMm6FaceTextureKeys(current, isMm6);
    CHECK(current.indoorSceneStates["6d01.blv"].eventRuntimeState->textureOverrides.contains(2011));

    OpenYAMM::Game::migrateLegacyMm6FaceTextureKeys(save, isMm6);
    const auto &mm6 = save.indoorSceneStates["6d01.blv"].eventRuntimeState->textureOverrides;
    CHECK_FALSE(mm6.contains(2011));
    REQUIRE(mm6.contains(faceKey));
    CHECK_EQ(mm6.at(faceKey), "lever_down");
    // MM7 and MM8 maps swap whole cogs; their keys stay.
    CHECK_EQ(save.indoorSceneStates["7d08.blv"].eventRuntimeState->textureOverrides.at(1), "cog_swap");
}

TEST_CASE("saves keep an indoor floor item whole: charges and ruleset fields")
{
    // Audit ITM-1: the MM record of an item on the floor indoors has no room for these.
    OpenYAMM::Game::InventoryItem item;
    item.objectDescriptionId = 101;
    item.rulesetFields.lootRarity = 5;
    item.currentCharges = 7;
    item.maxCharges = 20;
    item.rulesetFields.secondStandardEnchantId = 3;
    item.rulesetFields.legendaryAffixId = 17;
    item.rulesetFields.itemPower = 340;
    item.rulesetFields.dropLevel = 88;
    OpenYAMM::Game::MapDeltaSpriteObject floorItem;
    floorItem.rawContainingItem.assign(0x24, 0);
    floorItem.rawContainingItem[0] = 101;
    floorItem.heldItem = item;
    OpenYAMM::Game::MapDeltaData delta;
    delta.spriteObjects.push_back(floorItem);
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.indoorSceneStates["d01.blv"].mapDeltaData = delta;

    std::string error;
    const std::optional<OpenYAMM::Game::GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    const auto &objects = restored->indoorSceneStates.at("d01.blv").mapDeltaData->spriteObjects;
    REQUIRE_EQ(objects.size(), 1u);
    REQUIRE(objects[0].heldItem.has_value());
    CHECK(*objects[0].heldItem == item);
}

TEST_CASE("saves keep item ruleset fields and the random root seed")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.randomRootSeed = 0xfeedfacecafebeefull;
    save.heldInventoryItem.objectDescriptionId = 101;
    save.heldInventoryItem.rulesetFields.secondStandardEnchantId = 3;
    save.heldInventoryItem.rulesetFields.secondStandardEnchantPower = 12;
    save.heldInventoryItem.rulesetFields.lootRarity = 5;
    save.heldInventoryItem.rulesetFields.legendaryAffixId = 17;
    save.heldInventoryItem.rulesetFields.itemPower = 340;
    save.heldInventoryItem.rulesetFields.dropLevel = 88;
    save.heldInventoryItem.rulesetFields.qualityPercent = 73;
    save.heldInventoryItem.rulesetFields.craftSeed = 0xabcdef01u;
    save.heldInventoryItem.rulesetFields.potionCharges = 4;
    save.heldInventoryItem.rulesetFields.craftCount = 9;
    save.heldInventoryItem.rulesetFields.craftState = 19;
    save.heldInventoryItem.rulesetFields.ancientTier = 1;
    save.heldInventoryItem.currentCharges = 3;

    std::string error;
    const std::optional<OpenYAMM::Game::GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK_EQ(restored->randomRootSeed, save.randomRootSeed);
    CHECK(restored->heldInventoryItem.rulesetFields == save.heldInventoryItem.rulesetFields);
    CHECK_EQ(restored->heldInventoryItem.currentCharges, 3);
    CHECK(minimalSave().heldInventoryItem.rulesetFields.empty());
}

TEST_CASE("saves keep each character's ruleset state: toggles, elemental progress, potion effects and steps")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    OpenYAMM::Game::Character member;
    member.name = "Drinker";
    member.rulesetState.rememberedMasteries["Bow"] = OpenYAMM::Game::SkillMastery::Expert;
    member.rulesetState.classToggles = {68};
    member.rulesetState.elementalProgress = {1, 2.5, 0, 4};
    member.rulesetState.potionEffects.push_back({OpenYAMM::Game::TimedPotionEffect::Kind::Aura, 5, 120, 21600});
    member.rulesetState.potionEffects.push_back(
        {OpenYAMM::Game::TimedPotionEffect::Kind::Regeneration, 0, 60, 300.5f});
    member.rulesetState.potionSteps[252] = 3;
    member.rulesetState.progressionStoredMasteries["Sword"] = OpenYAMM::Game::SkillMastery::Master;
    member.rulesetState.soloStoredMasteries["Merchant"] = OpenYAMM::Game::SkillMastery::Expert;
    save.party.members.push_back(member);

    std::string error;
    const std::optional<OpenYAMM::Game::GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    REQUIRE_EQ(restored->party.members.size(), 1u);
    CHECK(restored->party.members[0].rulesetState == member.rulesetState);
}

TEST_CASE("saves keep the MAW level banks, loot counters and each actor's ruleset facts")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    OpenYAMM::Game::MawGameState mawState;
    mawState.continentLevels = {12.5, 3, 0, 0.25};
    mawState.bankedExperience = 98765.5;
    mawState.bankedLevel = 15.75;
    mawState.mapResetCounts["d08.blv"] = 2;
    mawState.completedMaps.insert("d08.blv");
    mawState.clearedSinceRefill.insert("d12.blv");
    mawState.celestialPity = 412.5;
    mawState.legendaryPity = 31.25;
    mawState.primordialPity = 7;
    mawState.artifactPity = 151;
    mawState.artifactDrops[533] = 2;
    mawState.legendaryAffixDrops[19] = 1;
    mawState.craftingPity[1061] = 120;
    mawState.craftingPity[1070] = 3;
    mawState.heldFood = 24;
    mawState.broodlordPity = 17;
    mawState.omnipotentPity = 140;
    // The Journal's Progress tab: the maps left, the runs cleared and the bounties claimed.
    mawState.mapVisits["d10.blv"] = {7, 20, 31};
    mawState.dimensionRunsCleared = 3;
    mawState.bountiesClaimed = 5;
    mawState.usedStatDecorations["d10.blv"] = {{3, 0}, {7, 0}};
    mawState.madnessDeaths = 4;
    save.mawState = mawState;

    OpenYAMM::Game::ActorRulesetFacts facts;
    facts.level = 412;
    facts.familyLevel = 400;
    facts.tier = 3;
    facts.bossAffix = 6;
    facts.bossHealthMultiplier = 3.25f;
    facts.bossDamageMultiplier = 1.3f;
    facts.unique = true;
    facts.attack1Damage = 1234.5f;
    facts.attack2Damage = 987.25f;
    facts.experience = 77777;
    OpenYAMM::Game::OutdoorWorldRuntime::MapActorState outdoorActor = {};
    outdoorActor.rulesetFacts = facts;
    save.outdoorWorld.mapActors.push_back(outdoorActor);
    OpenYAMM::Game::MapDeltaData indoorDelta = {};
    OpenYAMM::Game::MapDeltaActor indoorActor = {};
    // MAW monsters outgrow the 16-bit HP of the map format.
    indoorActor.hp = 123456;
    indoorActor.rulesetFacts = facts;
    indoorDelta.actors.push_back(indoorActor);
    save.indoorScene.mapDeltaData = indoorDelta;

    std::string error;
    const std::optional<OpenYAMM::Game::GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    REQUIRE(restored->mawState.has_value());
    CHECK(*restored->mawState == mawState);
    REQUIRE_EQ(restored->outdoorWorld.mapActors.size(), 1u);
    CHECK(restored->outdoorWorld.mapActors[0].rulesetFacts == facts);
    REQUIRE(restored->indoorScene.mapDeltaData.has_value());
    REQUIRE_EQ(restored->indoorScene.mapDeltaData->actors.size(), 1u);
    CHECK_EQ(restored->indoorScene.mapDeltaData->actors[0].hp, 123456);
    CHECK(restored->indoorScene.mapDeltaData->actors[0].rulesetFacts == facts);
    CHECK_FALSE(roundTrip(minimalSave(), error)->mawState.has_value());
}

TEST_CASE("ruleset option ids apply in any order")
{
    RulesetOptions options;
    CHECK(OpenYAMM::Game::applyRulesetOptionIds("horizontal:hell:randomizer:doom", options));
    // Doom sets its own difficulty over the one given.
    CHECK(options.difficulty == RulesetDifficulty::Nightmare);
    CHECK(options.progression == RulesetProgression::Horizontal);
    CHECK(options.challengeMode == RulesetChallengeMode::Doom);
    CHECK(options.randomizer);

    RulesetOptions unchanged;
    CHECK(OpenYAMM::Game::applyRulesetOptionIds("", unchanged));
    CHECK(unchanged == RulesetOptions{});
    CHECK_FALSE(OpenYAMM::Game::applyRulesetOptionIds("hell:sideways", unchanged));
}

TEST_CASE("beyond madness plays at nightmare with horizontal progression only")
{
    std::string yaml = MawRulesetYaml;
    yaml.replace(yaml.find("[none, doom]"), 12, "[none, beyond_madness]");
    std::string error;
    const std::optional<RulesetDefinition> maw = OpenYAMM::Game::parseRulesetDefinition(yaml, "maw", error);
    REQUIRE_MESSAGE(maw.has_value(), error);

    RulesetOptions options = maw->defaultOptions();
    options.challengeMode = RulesetChallengeMode::BeyondMadness;
    CHECK(options.progression == RulesetProgression::Free);
    CHECK_FALSE(maw->offers(options));
    options.progression = RulesetProgression::Horizontal;
    CHECK_FALSE(maw->offers(options));
    options.difficulty = RulesetDifficulty::Nightmare;
    CHECK(maw->offers(options));
    CHECK(OpenYAMM::Game::rulesetChallengeModeProgression(RulesetChallengeMode::BeyondMadness)
          == RulesetProgression::Horizontal);
    CHECK_FALSE(OpenYAMM::Game::rulesetChallengeModeProgression(RulesetChallengeMode::Doom).has_value());
}

TEST_CASE("ruleset definitions read the rules panel text")
{
    const std::string panel =
        "rulesPanel:\n"
        "  title: MAW Rules\n"
        "  summary: MAW rebalances monsters.\n"
        "  difficultyColumns: [Monster HP, Loot]\n"
        "  difficulties:\n"
        "    hell: {values: [x1.58, +20 %], description: As Hard., warning: Careful.}\n"
        "  progressions:\n"
        "    horizontal: Fixed map levels.\n"
        "  challengeModes:\n"
        "    beyond_madness: Restart at level 1.\n"
        "  randomizer: Shuffles quest items.\n";
    std::string error;
    const std::optional<RulesetDefinition> maw =
        OpenYAMM::Game::parseRulesetDefinition(std::string(MawRulesetYaml) + panel, "maw", error);
    REQUIRE_MESSAGE(maw.has_value(), error);
    CHECK_EQ(maw->panel.title, "MAW Rules");
    CHECK_EQ(maw->panel.summary, "MAW rebalances monsters.");
    REQUIRE_EQ(maw->panel.difficultyColumns.size(), 2u);
    const auto hell = maw->panel.difficulties.find(RulesetDifficulty::Hell);
    REQUIRE(hell != maw->panel.difficulties.end());
    CHECK_EQ(hell->second.values, std::vector<std::string>{"x1.58", "+20 %"});
    CHECK_EQ(hell->second.warning, "Careful.");
    CHECK_EQ(maw->panel.progressions.at(RulesetProgression::Horizontal), "Fixed map levels.");
    CHECK_EQ(maw->panel.challengeModes.at(RulesetChallengeMode::BeyondMadness), "Restart at level 1.");
    CHECK_EQ(maw->panel.randomizer, "Shuffles quest items.");

    const std::string tooManyValues =
        "rulesPanel:\n"
        "  difficultyColumns: [Monster HP]\n"
        "  difficulties:\n"
        "    hell: {values: [x1.58, +20 %]}\n";
    CHECK_FALSE(
        OpenYAMM::Game::parseRulesetDefinition(std::string(MawRulesetYaml) + tooManyValues, "maw", error).has_value());
    CHECK_FALSE(OpenYAMM::Game::parseRulesetDefinition(
                    std::string(MawRulesetYaml) + "rulesPanel:\n  progressions:\n    sideways: No.\n", "maw", error)
                    .has_value());
}

TEST_CASE("the debug console's MAW test parties parse, and requests name a stage, a party, kits and options")
{
    using OpenYAMM::Game::MawTestPartyCatalog;
    using OpenYAMM::Game::MawTestPartyRequest;
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev" / OpenYAMM::Game::MawTestPartyCatalogPath);
    const std::string text{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
    MawTestPartyCatalog catalog;
    std::string error;
    REQUIRE_MESSAGE(catalog.loadFromYaml(text, error), error);

    for (const OpenYAMM::Game::MawTestPartyStage &stage : catalog.stages)
    {
        CHECK_MESSAGE((stage.party.empty() || catalog.party(stage.party) != nullptr), stage.id);
    }

    MawTestPartyRequest request;
    REQUIRE(OpenYAMM::Game::parseMawTestPartyRequest(
        {"mid", "newclasses", "+crafting", "hell", "horizontal"}, catalog, request, error));
    CHECK_EQ(request.pStage->id, "mid");
    CHECK_EQ(request.pParty->id, "newclasses");
    REQUIRE_EQ(request.kits.size(), 1u);
    CHECK_EQ(request.kits.front()->id, "crafting");
    CHECK_EQ(request.rulesetOptions, "hell:horizontal");

    // Without a party, the stage's own.
    REQUIRE(OpenYAMM::Game::parseMawTestPartyRequest({"early"}, catalog, request, error));
    CHECK_EQ(request.pParty->id, "classic");
    CHECK_FALSE(OpenYAMM::Game::parseMawTestPartyRequest({"nowhere"}, catalog, request, error));
    CHECK_FALSE(OpenYAMM::Game::parseMawTestPartyRequest({"mid", "+nothing"}, catalog, request, error));
}

TEST_CASE("the installed MAW ruleset parses with MAW's own defaults")
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/ruleset.yml");
    const std::string text{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
    std::string error;
    const std::optional<RulesetDefinition> maw = OpenYAMM::Game::parseRulesetDefinition(text, "maw", error);
    REQUIRE_MESSAGE(maw.has_value(), error);

    // A new MAW game starts on MAW difficulty with free progression ("monster bolster on").
    const RulesetOptions defaults = maw->defaultOptions();
    CHECK(defaults.difficulty == RulesetDifficulty::Maw);
    CHECK(defaults.progression == RulesetProgression::Free);
    CHECK(defaults.challengeMode == RulesetChallengeMode::None);
    CHECK_FALSE(defaults.randomizer);
    CHECK(defaults.preferences.homingProjectiles);
    CHECK_FALSE(defaults.preferences.friendlyFire);
    CHECK_FALSE(defaults.preferences.trainerHints);
    CHECK_FALSE(defaults.preferences.bowDisabled);
    // The loot filter starts off; a player picks a preset in Settings (OY-216).
    CHECK(defaults.preferences.lootFilter.preset == RulesetLootFilterPreset::Off);

    // Every offered difficulty has a full row in the Rules panel.
    for (const RulesetDifficulty difficulty : maw->choices.difficulties)
    {
        const auto row = maw->panel.difficulties.find(difficulty);
        REQUIRE(row != maw->panel.difficulties.end());
        CHECK_EQ(row->second.values.size(), maw->panel.difficultyColumns.size());
        CHECK_FALSE(row->second.description.empty());
    }
}

TEST_CASE("the generated MAW patches apply cleanly to the engine tables")
{
    const std::filesystem::path source = OPENYAMM_SOURCE_DIR;
    const auto readTable = [&source](const std::filesystem::path &path)
    {
        std::ifstream input(source / path, std::ios::binary);
        const std::string text{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
        const std::optional<OpenYAMM::Engine::TextTable> table = OpenYAMM::Engine::TextTable::parseTabSeparated(text);
        REQUIRE_MESSAGE(table.has_value(), path.string());
        Rows rows;

        for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
        {
            rows.push_back(table->getRow(rowIndex));
        }

        return rows;
    };

    std::ifstream manifest(source / "assets_dev/engine/rulesets/maw/ruleset.yml");
    const std::string text{std::istreambuf_iterator<char>(manifest), std::istreambuf_iterator<char>()};
    std::string error;
    const std::optional<RulesetDefinition> maw = OpenYAMM::Game::parseRulesetDefinition(text, "maw", error);
    REQUIRE_MESSAGE(maw.has_value(), error);
    REQUIRE_FALSE(maw->tables.empty());
    // A table's contributions apply in order, each on what the ones before it made.
    std::map<std::string, Rows> composed;

    for (const OpenYAMM::Game::RulesetTableContribution &table : maw->tables)
    {
        CAPTURE(table.table);
        CAPTURE(table.path);
        const std::filesystem::path package = "assets_dev/engine/rulesets/maw";

        if (table.mode == OpenYAMM::Game::TableContributionMode::Replace)
        {
            std::ifstream input(source / package / table.path, std::ios::binary);
            CHECK(input.peek() != std::ifstream::traits_type::eof());
            continue;
        }

        if (!composed.contains(table.table))
        {
            composed[table.table] = readTable(std::filesystem::path("assets_dev/engine/data_tables") / table.table);
        }

        Rows &rows = composed[table.table];
        REQUIRE_MESSAGE(
            OpenYAMM::Game::applyTableCellOverrides(
                rows, readTable(package / table.path), table.keyColumn, table.headerRow, error),
            error);

        if (!table.appendPath.empty())
        {
            REQUIRE_MESSAGE(
                OpenYAMM::Game::appendTableRows(
                    rows, readTable(package / table.appendPath), table.keyColumn, table.headerRow, error),
                error);
        }

        if (!table.appendColumnsPath.empty())
        {
            REQUIRE_MESSAGE(
                OpenYAMM::Game::appendTableColumns(
                    rows, readTable(package / table.appendColumnsPath), table.keyColumn, table.headerRow, error),
                error);
        }
    }

    const Rows &spells = composed["spells.txt"];
    const Rows &randomItems = composed["random_items.txt"];

    // MAW's specials (GAPS.md A2.1): its added and renamed rows parse and roll; Standard's "of Sparking" never rolls.
    OpenYAMM::Game::SpecialItemEnchantTable specials;
    REQUIRE(specials.load(composed["special_item_enchants.txt"]));
    REQUIRE(specials.get(80) != nullptr);
    CHECK_EQ(specials.get(39)->kind, OpenYAMM::Game::SpecialItemEnchantKind::RulesetSpecial);
    CHECK_EQ(specials.get(74)->kind, OpenYAMM::Game::SpecialItemEnchantKind::RulesetSpecial);
    CHECK_EQ(specials.get(80)->kind, OpenYAMM::Game::SpecialItemEnchantKind::RulesetSpecial);
    CHECK_EQ(specials.get(73)->kind, OpenYAMM::Game::SpecialItemEnchantKind::None);
    CHECK_EQ(specials.get(18)->name, "Disease and Curse Immunity");

    // The new classes' skill caps (class_perks.yml skill_caps.new_classes) and MAW's Supreme reading as Grandmaster.
    OpenYAMM::Game::ClassSkillTable classSkills;
    REQUIRE(classSkills.loadCapsFromRows(composed["class_skills.txt"]));
    CHECK_EQ(classSkills.getClassCap("DeathKnight", "Axe"), OpenYAMM::Game::SkillMastery::Master);
    CHECK_EQ(classSkills.getClassCap("LichKing", "DarkMagic"), OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_EQ(classSkills.getClassCap("MasterOfElements", "ManaShield"), OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_EQ(classSkills.getClassCap("Seraphim", "Cover"), OpenYAMM::Game::SkillMastery::Master);
    CHECK_EQ(classSkills.getClassCap("Shaman", "Learning"), OpenYAMM::Game::SkillMastery::None);
    CHECK_EQ(classSkills.getClassCap("Champion", "Armsmaster"), OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_EQ(classSkills.getClassCap("Knight", "Learning"), OpenYAMM::Game::SkillMastery::None);

    // MAW's Meteor Shower (devdocs/maw/CLASSES_SPELLS_SPEC.md §1.4): 40 mana, recovery 200 and 180 at GM.
    OpenYAMM::Game::SpellTable spellTable;
    REQUIRE(spellTable.loadFromRows(spells));
    const OpenYAMM::Game::SpellEntry *pMeteor = spellTable.findByName("Meteor Shower");
    REQUIRE(pMeteor != nullptr);
    CHECK_EQ(OpenYAMM::Game::spellNumbersAtMastery(*pMeteor, OpenYAMM::Game::SkillMastery::Normal).manaCost, 40);
    CHECK_EQ(
        OpenYAMM::Game::spellNumbersAtMastery(*pMeteor, OpenYAMM::Game::SkillMastery::Grandmaster).recoveryTicks, 180);

    // Costs keyed by spell id (GAPS.md A7.6, A7.7): Mind Charm 5, the vampires' Charm keeps 15; Chain Lightning and
    // Lifedrain at Master and Grandmaster.
    const auto manaAt = [&spellTable](int spellId, OpenYAMM::Game::SkillMastery mastery)
    {
        const OpenYAMM::Game::SpellEntry *pSpell = spellTable.findById(spellId);
        REQUIRE(pSpell != nullptr);
        return OpenYAMM::Game::spellNumbersAtMastery(*pSpell, mastery).manaCost;
    };
    CHECK_EQ(manaAt(60, OpenYAMM::Game::SkillMastery::Normal), 5);
    CHECK_EQ(manaAt(113, OpenYAMM::Game::SkillMastery::Normal), 15);
    CHECK_EQ(manaAt(18, OpenYAMM::Game::SkillMastery::Master), 20);
    CHECK_EQ(manaAt(18, OpenYAMM::Game::SkillMastery::Grandmaster), 30);
    CHECK_EQ(manaAt(111, OpenYAMM::Game::SkillMastery::Master), 10);
    CHECK_EQ(manaAt(111, OpenYAMM::Game::SkillMastery::Grandmaster), 15);

    // MAW's item rows (GAPS.md A2.4, A2.12, A2.13, L4.4, A4.9): two-handed halberds, book and special prices, the
    // removed potions and the black potions' art.
    const auto itemRow = [&composed](const std::string &id) -> std::vector<std::string>
    {
        for (const std::vector<std::string> &row : composed["items.txt"])
        {
            if (!row.empty() && row[0] == id)
            {
                return row;
            }
        }

        return {};
    };
    CHECK_EQ(itemRow("46").at(4), "Weapon2");
    CHECK_EQ(itemRow("1640").at(4), "Weapon2");
    CHECK_EQ(itemRow("473").at(2), "Greater Heal");
    CHECK_EQ(itemRow("516").at(3), "20000");
    CHECK_EQ(itemRow("1439").at(3), "2500");
    CHECK_EQ(itemRow("270").at(2), "Potion Deleted in MAW");
    CHECK_EQ(itemRow("270").at(16), "This potion has been removed");
    CHECK_EQ(itemRow("255").at(1), "item182");
    CHECK_NE(itemRow("290").at(2), "Potion Deleted in MAW");

    // MAW's run-time monster changes (GAPS.md A3.7): thieves break an item, only wimps flee, Zombies and Ghouls are
    // hostile to the party.
    const auto rowOf = [&composed](const std::string &table, const std::string &key) -> std::vector<std::string>
    {
        for (const std::vector<std::string> &row : composed[table])
        {
            if (!row.empty() && row[0] == key)
            {
                return row;
            }
        }

        return {};
    };
    CHECK_EQ(rowOf("monster_data.txt", "406").at(16), "BrkItemx2");
    CHECK_EQ(rowOf("monster_data.txt", "6").at(11), "Suicidal");
    CHECK_EQ(rowOf("monster_data.txt", "1").at(11), "Wimp");
    // A monster's attitude toward the party is the Party row's cell in the monster's column.
    const std::vector<std::string> &hostileHeader = composed["hostile.txt"].front();
    const std::vector<std::string> partyRelations = rowOf("hostile.txt", "Party");
    const auto partyRelationTo = [&](const std::string &faction) -> std::string
    {
        for (size_t column = 1; column < hostileHeader.size(); ++column)
        {
            if (hostileHeader[column] == faction)
            {
                return partyRelations.at(column);
            }
        }

        return {};
    };
    CHECK_EQ(partyRelationTo("Zombie"), "4");
    CHECK_EQ(partyRelationTo("Ghoul"), "4");
    // Houses that opened at 6 open at 5 (GAPS.md A5.11).
    CHECK_EQ(rowOf("house_data.txt", "1").at(18), "5");
    // Spellbook shops of types 1 and 5 sell one quality higher (GAPS.md E.5).
    REQUIRE_GT(composed["house_rules.txt"].size(), 281);
    CHECK_EQ(composed["house_rules.txt"][276].at(0), "Spellbook shops");
    CHECK_EQ(composed["house_rules.txt"][277].at(1), "5");
    CHECK_EQ(composed["house_rules.txt"][281].at(1), "6");
    CHECK_EQ(composed["house_rules.txt"][278].at(1), "7");

    // Spellbooks keep MAW's (MMMerge's) drop weights, not Standard's raised ones (audit DAT-3, decision D4): 418 and
    // 1220 drop at treasure level 5 only (columns 2-7 are levels 1-6), and books are 5 % of level 3 drops, not 13.6 %.
    std::unordered_set<std::string> books;

    for (const std::vector<std::string> &row : composed["items.txt"])
    {
        if (row.size() > 4 && row[4] == "Book")
        {
            books.insert(row[0]);
        }
    }

    REQUIRE_FALSE(books.empty());
    int levelThreeWeight = 0;
    int levelThreeBooks = 0;

    for (const std::vector<std::string> &row : randomItems)
    {
        if (!row.empty() && (row[0] == "418" || row[0] == "1220"))
        {
            CHECK_EQ(row[5], "0");
            CHECK_EQ(row[6], "1");
        }

        if (row.size() > 4 && !row[0].empty() && std::isdigit(static_cast<unsigned char>(row[0][0])) != 0
            && !row[4].empty() && std::isdigit(static_cast<unsigned char>(row[4][0])) != 0)
        {
            const int weight = std::stoi(row[4]);
            levelThreeWeight += weight;
            levelThreeBooks += books.contains(row[0]) ? weight : 0;
        }
    }

    REQUIRE_GT(levelThreeWeight, 0);
    CHECK(double(levelThreeBooks) / levelThreeWeight == doctest::Approx(0.050).epsilon(0.05));
}

TEST_CASE("the MAW ruleset declares every monster name it adds (audit CNT-13)")
{
    const std::filesystem::path package = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw";
    const YAML::Node ruleset = YAML::LoadFile((package / "ruleset.yml").string());
    const uint32_t begin = ruleset["idRanges"]["monster_names"]["begin"].as<uint32_t>();
    const uint32_t end = ruleset["idRanges"]["monster_names"]["end"].as<uint32_t>();
    std::ifstream names(package / "content/place_mon_names.txt");
    std::string line;
    size_t count = 0;

    while (std::getline(names, line))
    {
        if (line.empty() || !std::isdigit(static_cast<unsigned char>(line[0])))
        {
            continue;
        }

        const uint32_t id = uint32_t(std::stoul(line));
        CHECK(id >= begin);
        CHECK(id <= end);
        ++count;
    }

    CHECK(count > 0);
}

TEST_CASE("the MAW ruleset's every table contribution reaches a loader")
{
    // Composing the tables by hand (above) passes even when no loader reads a contribution, as map_stats.txt went
    // unread until the 2026-10-24 audit (DAT-1). This loads the game data with MAW active instead.
    const std::filesystem::path source = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(source, source / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1));
    std::vector<RulesetDefinition> rulesets;
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::loadAvailableRulesets(assetFileSystem, rulesets, error), error);
    const auto maw = std::find_if(rulesets.begin(), rulesets.end(),
        [](const RulesetDefinition &ruleset) { return ruleset.id == "maw"; });
    REQUIRE(maw != rulesets.end());

    OpenYAMM::Game::GameDataLoader data;
    data.setActiveRuleset(*maw);
    REQUIRE(data.loadForGameplay(assetFileSystem));

    for (const OpenYAMM::Game::RulesetTableContribution &table : maw->tables)
    {
        CAPTURE(table.table);
        CHECK(data.appliedRulesetContributions().contains(table.path));
    }

    // Dagger Wound Island: treasure level 0 in Standard, 6 in MAW (patches/map_stats.txt).
    const OpenYAMM::Game::MapStatsEntry *pMap = data.getMapStats().findByFileName("out01.odm");
    REQUIRE(pMap != nullptr);
    CHECK_EQ(pMap->treasureLevel, 6);

    // Behemoth A shrinks to three quarters so it gets stuck less (content/monster_descriptors_patch.txt, audit DAT-4).
    const OpenYAMM::Game::MonsterEntry *pBehemoth = data.getMonsterTable().findById(208);
    REQUIRE(pBehemoth != nullptr);
    CHECK_EQ(pBehemoth->radius, 120);
    CHECK_EQ(pBehemoth->height, 192);
}

TEST_CASE("the MAW ruleset's global events leave the base game's events alone")
{
    // MAW's hatchling and circus hooks once took ids 65310/65311, the Amethyst and Diamond crystals (audit CNT-1);
    // global hooks now need a free id.
    const std::filesystem::path source = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(source, source / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1));
    std::vector<RulesetDefinition> rulesets;
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::loadAvailableRulesets(assetFileSystem, rulesets, error), error);
    const auto maw = std::find_if(rulesets.begin(), rulesets.end(),
        [](const RulesetDefinition &ruleset) { return ruleset.id == "maw"; });
    REQUIRE(maw != rulesets.end());

    OpenYAMM::Game::GameDataLoader data;
    data.setActiveRuleset(*maw);
    REQUIRE(data.loadForHeadlessGameplay(assetFileSystem));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "out01.odm"));
    REQUIRE(data.getSelectedMap().has_value());
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> &global = data.getSelectedMap()->globalEventProgram;
    REQUIRE(global.has_value());

    for (const uint16_t crystal : {65310, 65311})
    {
        CAPTURE(crystal);
        const std::optional<std::string> summary = global->summarizeEvent(crystal);
        REQUIRE(summary.has_value());
        CHECK(summary->find("Crystals") != std::string::npos);
    }

    CHECK(global->hasEvent(65400));
    CHECK(global->hasEvent(65401));
}

TEST_CASE("a member's timed condition keeps its end time across a save")
{
    using OpenYAMM::Game::CharacterCondition;
    constexpr size_t Paralyzed = static_cast<size_t>(CharacterCondition::Paralyzed);
    OpenYAMM::Game::GameSaveData save = minimalSave();
    OpenYAMM::Game::Character member;
    member.name = "Timed";
    member.conditions.set(Paralyzed);
    member.conditionStartGameMinutes[Paralyzed] = 600.0f;
    member.conditionExpireGameMinutes[Paralyzed] = 610.0f;
    save.party.members.push_back(member);
    std::string error;
    const std::optional<OpenYAMM::Game::GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    REQUIRE_EQ(restored->party.members.size(), 1u);
    CHECK(restored->party.members[0].conditions.test(Paralyzed));
    CHECK(restored->party.members[0].conditionExpireGameMinutes[Paralyzed] == doctest::Approx(610.0f));
}

TEST_CASE("saves keep the outdoor map the party was last on (OY-303)")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    save.party.lastOutdoorMapFileName = "oute3.odm";
    std::string error;
    const std::optional<OpenYAMM::Game::GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK_EQ(restored->party.lastOutdoorMapFileName, "oute3.odm");
}

TEST_CASE("saves keep a solo character's bag tags past the eighth bag (OY-344)")
{
    OpenYAMM::Game::GameSaveData save = minimalSave();
    OpenYAMM::Game::Character member;
    member.name = "Solo";
    member.rulesetState.craftingBags = 1u << 20;
    member.rulesetState.alchemyBags = 1u << 24;
    save.party.members.push_back(member);
    std::string error;
    const std::optional<OpenYAMM::Game::GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    REQUIRE_EQ(restored->party.members.size(), 1u);
    CHECK_EQ(restored->party.members[0].rulesetState.craftingBags, 1u << 20);
    CHECK_EQ(restored->party.members[0].rulesetState.alchemyBags, 1u << 24);
}
