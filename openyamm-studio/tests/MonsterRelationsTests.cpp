#include "doctest/doctest.h"

#include "core/IndoorLowering.h"
#include "core/MonsterRelations.h"

#include <algorithm>

using namespace OpenYAMM::Studio;

namespace
{
// Four kinds of three tiers each: Goblin (class 1), Archer (2), Eye (3), Golem (4).
const char *const RelationMonsterText =
    "#\tName\tPicture\n"
    "1\tGoblin\tGoblin A\n2\tHobgoblin\tGoblin B\n3\tGoblin Lord\tGoblin C\n"
    "4\tArcher\tArcher A\n5\tBowman\tArcher B\n6\tElite Archer\tArcher C\n"
    "7\tFloating Eye\tEye A\n8\tGazer\tEye B\n9\tEvil Eye\tEye C\n"
    "10\tBronze Golem\tGolem A\n11\tBrass Golem\tGolem B\n12\tGold Golem\tGolem C\n";
// hostile.txt: a row per class toward which the columns' classes have that relation. The Goblins and the Eyes are the
// party's foes, the Archers and the Golems its friends; the Eyes hate the Golems (4), the Golems the Eyes a little (1).
const char *const RelationTableText =
    "\tParty\tGoblin\tArcher\tEye\tGolem\n"
    "Party\t0\t2\t0\t4\t0\n"
    "Goblin\t0\t0\t0\t0\t0\n"
    "Archer\t0\t0\t0\t0\t0\n"
    "Eye\t0\t0\t0\t0\t1\n"
    "Golem\t0\t0\t0\t4\t0\n";

std::vector<std::string> warningsOf(const MapMonsters &monsters)
{
    return monsterHostilityWarnings(
        monsters, parseTableRows(RelationMonsterText), parseTableRows(RelationTableText), "objects.yml");
}

bool anyWarning(const std::vector<std::string> &warnings, const std::string &text)
{
    return std::any_of(warnings.begin(), warnings.end(), [&text](const std::string &warning)
    {
        return warning.find(text) != std::string::npos;
    });
}

std::string joined(const std::vector<std::string> &warnings)
{
    std::string text;

    for (const std::string &warning : warnings)
    {
        text += warning + "\n";
    }

    return text;
}

MapMonsters slotsOf(const std::array<std::string, 3> &slots)
{
    MapMonsters monsters;
    monsters.slots = slots;
    return monsters;
}

std::vector<MonsterRelationRow> relationsOf(const std::string &text, std::vector<ProjectIssue> &issues)
{
    const std::vector<std::vector<std::string>> rows = parseTableRows(RelationMonsterText);
    return readMonsterRelations(YAML::Load(text), "sketch.yml",
        [&rows](const YAML::Node &value, const std::string &) -> std::optional<int>
        {
            for (const std::vector<std::string> &row : rows)
            {
                if (row[0] == value.Scalar() || row[1] == value.Scalar() || row[2] == value.Scalar())
                {
                    return std::stoi(row[0]);
                }
            }

            return std::nullopt;
        },
        issues);
}
}

TEST_CASE("a map's relations are read into the rows the game's script sets, in order")
{
    std::vector<ProjectIssue> issues;
    const std::vector<MonsterRelationRow> rows = relationsOf(
        "- {of: [Archer A, 5], toward: party, relation: hostile}\n"
        "- {of: {group: 7}, toward: Eye A, relation: friendly, both_ways: true}\n", issues);
    CHECK(issues.empty());
    CHECK(monsterRelationLines(rows) == std::vector<std::string>{"evt.SetMonsterRelation(4, 0, 4)",
        "evt.SetMonsterRelation(5, 0, 4)", "evt.SetMonsterRelation({group = 7}, 7, 0)",
        "evt.SetMonsterRelation(7, {group = 7}, 0)"});
    CHECK(rows[2].path == "relations[1]");
    // What cannot be: said with the file it is in.
    relationsOf("- {of: 4, toward: party, relation: 9}\n- {of: 4, toward: party, relation: hostile, both_ways: true}\n"
        "- {of: [[1]], toward: party, relation: 4}\n", issues);
    REQUIRE(issues.size() == 3);
    CHECK(issues[0].file == "sketch.yml");
    CHECK(issues[0].message.find("a relation is {of:") != std::string::npos);
    CHECK(issues[1].message.find("drop `both_ways`") != std::string::npos);
    CHECK(issues[2].path == "relations[2].of[0]");
}

TEST_CASE("a map's slots come from project.yml over its reference row; the reference's own are the shipped ones")
{
    // map_stats.txt: encounter slot n's picture in column 16 + 4 (n - 1), its name in the next.
    std::string row = "9\tVale\tvale.odm";

    for (int column = 3; column < 28; ++column)
    {
        row += column == 16 ? "\tGoblin" : column == 20 ? "\tEye" : column == 24 ? "\t0" : "\t0";
    }

    MapMonsters monsters;
    readMapSlots(YAML::Load("map_stats: {id: 9, reference: VALE.odm, slots: [{monster: Golem}]}"),
        parseTableRows(row + "\n"), monsters);
    CHECK(monsters.slots == std::array<std::string, 3>{"Golem", "Eye", ""});
    CHECK(monsters.shippedSlots == std::vector<std::string>{"Goblin", "Eye"});
}

TEST_CASE("the build warns of slot monsters the table leaves peaceful to the party, unless the project says so")
{
    MapMonsters monsters = slotsOf({"Goblin", "Archer", ""});
    monsters.spawns = {{"spawn:a", 1, '\0', 0}, {"spawn:b", 2, '\0', 0}};
    std::vector<std::string> warnings = warningsOf(monsters);
    INFO(joined(warnings));
    REQUIRE(warnings.size() == 1);
    CHECK(warnings[0].find("slot 2 (Archer) spawns Archer, Bowman and Elite Archer (4, 5, 6)") != std::string::npos);
    CHECK(warnings[0].find("add to objects.yml `relations` {of: [4, 5, 6], toward: party, relation: hostile}")
        != std::string::npos);
    // A spawn point of a fixed tier spawns that tier only.
    monsters.spawns = {{"spawn:b", 2, 'B', 0}};
    CHECK(anyWarning(warningsOf(monsters), "spawns Bowman (5)"));
    // Said: hostile or friendly toward the party.
    std::vector<ProjectIssue> issues;
    monsters.relations = relationsOf("- {of: 5, toward: party, relation: hostile}\n", issues);
    CHECK(warningsOf(monsters).empty());
    monsters.relations = relationsOf("- {of: 5, toward: party, relation: friendly}\n", issues);
    CHECK(warningsOf(monsters).empty());
    // A group made peaceful says it too.
    monsters.relations.clear();
    monsters.spawns = {{"spawn:b", 2, '\0', 40}};
    monsters.peacefulGroups = {40};
    CHECK(warningsOf(monsters).empty());
    // A rebuilt shipped map keeps its reference row's slots as shipped.
    monsters.peacefulGroups.clear();
    monsters.shippedSlots = {"archer"};
    CHECK(warningsOf(monsters).empty());
    // A group's relation toward the party does nothing in the game.
    monsters.relations = relationsOf("- {of: {group: 3}, toward: party, relation: hostile}\n", issues);
    CHECK(anyWarning(warningsOf(monsters), "a group's relation toward the party does nothing"));
    CHECK(issues.empty());
}

TEST_CASE("the build warns of placed monsters left peaceful beside hostile ones of their kind")
{
    MapMonsters monsters = slotsOf({"", "", ""});
    monsters.placed = {{"monster:camp", 4, 60, true}, {"monster:lone", 5, 0, std::nullopt}};
    const std::vector<std::string> warnings = warningsOf(monsters);
    INFO(joined(warnings));
    REQUIRE(warnings.size() == 1);
    CHECK(warnings[0].find("monster:lone (Bowman) is of a kind that engine/data_tables/hostile.txt has friendly to the "
        "party (5)") != std::string::npos);
    // Townsfolk of a friendly kind with no hostile one of it: nothing to say.
    monsters.placed = {{"monster:a", 5, 51, std::nullopt}, {"monster:b", 6, 51, std::nullopt}};
    CHECK(warningsOf(monsters).empty());
    // Said peaceful.
    monsters.placed = {{"monster:camp", 4, 60, true}, {"monster:lone", 5, 9, false}};
    monsters.peacefulGroups = {9};
    CHECK(warningsOf(monsters).empty());
}

TEST_CASE("the build warns of two of the map's hostile kinds the table sets on each other, unless kept apart")
{
    MapMonsters monsters = slotsOf({"Golem", "Eye", "Goblin"});
    monsters.spawns = {{"spawn:a", 1, '\0', 0}, {"spawn:b", 2, '\0', 0}, {"spawn:c", 3, '\0', 0}};
    std::vector<ProjectIssue> issues;
    // The Golems made the party's foes: now they and the Eyes are both hostile to it, and set on each other.
    monsters.relations = relationsOf("- {of: [10, 11, 12], toward: party, relation: hostile}\n", issues);
    std::vector<std::string> warnings = warningsOf(monsters);
    INFO(joined(warnings));
    REQUIRE(warnings.size() == 1);
    CHECK(warnings[0].find("Floating Eye, Gazer and Evil Eye (slot 2) and Bronze Golem, Brass Golem and Gold Golem "
        "(slot 1) are both hostile to the party") != std::string::npos);
    CHECK(warnings[0].find("(4 and 1)") != std::string::npos);
    CHECK(warnings[0].find("{of: [7, 8, 9], toward: 10, relation: friendly, both_ways: true} and the same toward 11 "
        "and 12") != std::string::npos);
    // Kept apart, every tier both ways: nothing.
    monsters.relations = relationsOf("- {of: [10, 11, 12], toward: party, relation: hostile}\n"
        "- {of: [7, 8, 9], toward: 10, relation: friendly, both_ways: true}\n"
        "- {of: [7, 8, 9], toward: 11, relation: friendly, both_ways: true}\n"
        "- {of: [7, 8, 9], toward: 12, relation: friendly, both_ways: true}\n", issues);
    CHECK(warningsOf(monsters).empty());
    // One way only: the Golems still answer the Eyes (1).
    monsters.relations = relationsOf("- {of: [10, 11, 12], toward: party, relation: hostile}\n"
        "- {of: [7, 8, 9], toward: 10, relation: friendly}\n- {of: [7, 8, 9], toward: 11, relation: friendly}\n"
        "- {of: [7, 8, 9], toward: 12, relation: friendly}\n", issues);
    CHECK(anyWarning(warningsOf(monsters), "(0 and 1)"));
    // Meant to fight: said hostile.
    monsters.relations = relationsOf("- {of: [10, 11, 12], toward: party, relation: hostile}\n"
        "- {of: [7, 8, 9], toward: 10, relation: hostile, both_ways: true}\n"
        "- {of: [7, 8, 9], toward: 11, relation: hostile, both_ways: true}\n"
        "- {of: [7, 8, 9], toward: 12, relation: hostile, both_ways: true}\n", issues);
    CHECK(warningsOf(monsters).empty());
    // One group never fights itself.
    monsters.relations = relationsOf("- {of: [10, 11, 12], toward: party, relation: hostile}\n", issues);
    monsters.spawns = {{"spawn:a", 1, '\0', 51}, {"spawn:b", 2, '\0', 51}};
    CHECK(warningsOf(monsters).empty());
    // Golems kept peaceful: the Eyes' prey, not a fight between the party's foes.
    monsters.relations = relationsOf("- {of: [10, 11, 12], toward: party, relation: friendly}\n", issues);
    monsters.spawns = {{"spawn:a", 1, '\0', 0}, {"spawn:b", 2, '\0', 0}};
    CHECK(warningsOf(monsters).empty());
    CHECK(issues.empty());
}

TEST_CASE("a world's relations.yml says what it covers: its factions toward the party and each other")
{
    // The Archers (4-6) a faction hostile to the party, the Golems (10-12) one that leaves the Eyes alone; a rule that
    // waits for a QBit is not in force in a new game.
    const WorldMonsterRelations world = readWorldMonsterRelations(
        "schema: openyamm.monsterRelations.v1\n"
        "factions:\n  archers: {monsters: [4-6]}\n  golems: {monsters: [10-12]}\n  eyes: {monsters: [7-9]}\n"
        "relations:\n"
        "  - {from: archers, to: party, relation: long}\n"
        "  - {from: archers, to: party, relation: friendly, after_qbit: 100}\n"
        "  - {from: golems, to: any, relation: short}\n"
        "  - {from: golems, to: eyes, relation: friendly}\n");
    CHECK(world.relation(5, 0) == 4);
    CHECK(world.relation(11, 8) == 0);
    CHECK(world.relation(11, 2) == 2);
    CHECK_FALSE(world.relation(11, 0).has_value());
    CHECK_FALSE(world.relation(2, 0).has_value());
    CHECK(readWorldMonsterRelations("factions: [").factionOf.empty());

    // The Archers of slot 2: hostile by the world, so no "peaceful, unsaid" warning.
    MapMonsters monsters = slotsOf({"Goblin", "Archer", ""});
    monsters.spawns = {{"spawn:a", 1, '\0', 0}, {"spawn:b", 2, '\0', 0}};
    REQUIRE(warningsOf(monsters).size() == 1);
    monsters.world = world;
    CHECK(warningsOf(monsters).empty());

    // Golems made hostile beside the Eyes: the world keeps the Golems off the Eyes, but hostile.txt still sets the
    // Eyes on the Golems (the Eyes have no rule toward them).
    MapMonsters fight = slotsOf({"Golem", "Eye", ""});
    fight.spawns = {{"spawn:a", 1, '\0', 0}, {"spawn:b", 2, '\0', 0}};
    std::vector<ProjectIssue> issues;
    fight.relations = relationsOf("- {of: [10, 11, 12], toward: party, relation: hostile}\n", issues);
    fight.world = world;
    CHECK(anyWarning(warningsOf(fight), "(4 and 0)"));
}
