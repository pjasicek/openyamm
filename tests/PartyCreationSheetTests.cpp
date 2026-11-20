#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/data/GameDataRepository.h"
#include "game/ui/screens/PartyCreationSheet.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <filesystem>
#include <set>

namespace
{
using namespace OpenYAMM::Game;

struct StandardData
{
    OpenYAMM::Engine::AssetFileSystem assets;
    GameDataLoader loader;
    GameDataRepository data;

    StandardData()
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
        REQUIRE(loader.loadForHeadlessGameplay(assets));
        data.bind(loader);
    }
};

RaceStatLine stat(int base, int maximum, int gain, int cost)
{
    return {base, maximum, gain, cost};
}
} // namespace

TEST_CASE("party creation sheet groups every classic and ruleset skill once")
{
    std::set<std::string> listed;

    for (const CreationSkillGroup &group : creationSkillGroups())
    {
        for (const std::string &skill : group.skills)
        {
            CHECK_MESSAGE(listed.insert(skill).second, skill);
        }
    }

    for (const std::string &skill : allCanonicalSkillNames())
    {
        CHECK_MESSAGE(listed.contains(skill) == !isTechnologySkill(skill), skill);
    }
}

TEST_CASE("party creation sheet skill states")
{
    const std::vector<std::string> fixed = {"Sword"};
    const std::vector<std::string> optional = {"Axe", "Spear"};
    const std::vector<std::string> chosen = {"Spear"};
    const CreationSkillReach learnable{SkillMastery::Normal, SkillMastery::Expert};
    const CreationSkillReach none{};

    CHECK(creationSkillState(fixed, optional, chosen, learnable, "Sword") == CreationSkillState::Fixed);
    CHECK(creationSkillState(fixed, optional, chosen, learnable, "Axe") == CreationSkillState::Option);
    CHECK(creationSkillState(fixed, optional, chosen, learnable, "Spear") == CreationSkillState::Chosen);
    CHECK(creationSkillState(fixed, optional, chosen, learnable, "Mace") == CreationSkillState::Later);
    CHECK(creationSkillState(fixed, optional, chosen, none, "FireMagic") == CreationSkillState::Never);
}

TEST_CASE("party creation sheet reads a class line from the class table")
{
    StandardData standard;
    const ClassSkillTable &table = standard.data.classSkillTable();
    const std::vector<std::vector<std::string>> line = creationClassLine(table, "Knight");

    REQUIRE(line.size() == 3);
    CHECK(line[0] == std::vector<std::string>{"Knight"});
    REQUIRE(line[1].size() == 1);
    CHECK(displayClassName(line[1][0]) == "Cavalier");
    REQUIRE(line[2].size() == 2);

    // A Human Knight: Sword Master now and Grandmaster as a Black Knight or Champion; Axe never reaches
    // Grandmaster.
    const CreationSkillReach sword = creationSkillReach(table, "Knight", 0, "Sword");
    CHECK(sword.now == SkillMastery::Master);
    CHECK(sword.best == SkillMastery::Grandmaster);
    CHECK(creationMasteryAvailability(table, "Knight", 0, "Sword", SkillMastery::Master) == 0);
    CHECK(creationMasteryAvailability(table, "Knight", 0, "Sword", SkillMastery::Grandmaster) == 1);
    CHECK(creationMasteryAvailability(table, "Knight", 0, "FireMagic", SkillMastery::Normal) == 2);

    // A Human's +1 mastery rank in Learning is the race's; Sword is the class's alone.
    CHECK(creationRaceChangesSkill(table, "Knight", 0, "Learning"));
    CHECK_FALSE(creationRaceChangesSkill(table, "Knight", 0, "Sword"));
}

TEST_CASE("party creation race card groups alike attributes and skill rules")
{
    StandardData standard;
    const ClassSkillTable &table = standard.data.classSkillTable();
    const std::array<const char *, CreationStatCount> &names = creationStatNames();

    std::array<RaceStatLine, CreationStatCount> even;
    even.fill(stat(11, 25, 1, 1));
    const std::vector<RaceCardLine> evenLines = raceCardLines(even, names, {}, 0, table, {});
    REQUIRE(evenLines.size() == 1);
    CHECK(evenLines[0].kind == RaceCardLine::Kind::Even);
    CHECK(evenLines[0].text == "Even attributes: 11 each, max 25");

    std::array<RaceStatLine, CreationStatCount> dwarf = even;
    dwarf[0] = stat(14, 30, 2, 1);
    dwarf[3] = stat(14, 30, 2, 1);
    dwarf[4] = stat(7, 20, 1, 2);
    MergedRaceSkillOverride learning;
    learning.raceId = 9;
    learning.skillName = "Learning";
    learning.add = 1;
    MergedRaceSkillOverride perception = learning;
    perception.skillName = "Perception";
    MergedRaceSkillOverride otherRace = learning;
    otherRace.raceId = 0;
    otherRace.skillName = "Merchant";
    MergedRaceSkillOverride axe;
    axe.raceId = 9;
    axe.skillName = "Axe";
    axe.minMastery = 2;
    const std::vector<RaceCardLine> lines =
        raceCardLines(dwarf, names, {learning, perception, otherRace, axe}, 9, table, {"Immune to Mind magic."});

    REQUIRE(lines.size() == 5);
    CHECK(lines[0].kind == RaceCardLine::Kind::Strong);
    CHECK(lines[0].text == "Might, Endurance 14 · +2 per point · max 30");
    CHECK(lines[1].kind == RaceCardLine::Kind::Weak);
    CHECK(lines[1].text == "Accuracy 7 · 2 points per +1 · max 20");
    CHECK(lines[2].text == "+1 mastery rank: Learning, Perception");
    CHECK(lines[3].text == "At least Expert: Axe");
    CHECK(lines[4].kind == RaceCardLine::Kind::Note);
}

TEST_CASE("party creation coverage counts what the party starts with")
{
    StandardData standard;
    const ClassSkillTable &table = standard.data.classSkillTable();
    CreationPartyMember knight;
    knight.className = "Knight";
    knight.fixedSkills = {"Sword", "LeatherArmor"};
    knight.optionalSkills = {"Axe", "Spear", "Shield"};
    knight.chosenSkills = {"Spear"};

    const CreationPartyCoverage one = creationPartyCoverage(table, {knight});
    CHECK(one.covered == 3);
    CHECK(one.reachable > one.covered);
    // Sword and Spear reach Grandmaster through the Knight's promotions; Leather Armor does not.
    CHECK(one.grandmaster == 2);

    CreationPartyMember second = knight;
    second.chosenSkills = {"Shield"};
    const CreationPartyCoverage two = creationPartyCoverage(table, {knight, second});
    CHECK(two.covered == 4);
    CHECK(two.reachable == one.reachable);
}
