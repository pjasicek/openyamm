#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"

#include "core/CanonicalYaml.h"
#include "core/ChestKinds.h"
#include "core/CoreMath.h"
#include "core/IndoorBuild.h"
#include "core/IndoorLowering.h"
#include "core/Json.h"
#include "core/Ops.h"
#include "core/Polygon.h"
#include "core/Project.h"
#include "core/Schema.h"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <bit>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <random>

using namespace OpenYAMM::Studio;

namespace
{
Project projectFromTexts(const std::vector<std::pair<std::string, std::string>> &files)
{
    Project project;

    for (const std::pair<std::string, std::string> &entry : files)
    {
        ProjectFile file;
        file.name = entry.first;
        file.text = entry.second;
        file.document = YAML::Load(entry.second);

        for (const ProjectFileKind &kind : projectFileKinds())
        {
            if (file.name == kind.pName)
            {
                file.schema = kind.pSchema;
            }
        }

        project.files[file.name] = file;
    }

    return project;
}

const char *CardText = "format: 0\nid: testmap\nworld: mm6\nkind: indoor\n";
const char *ThemeText =
    "format: 0\n"
    "themes:\n"
    "  - id: theme:plain\n"
    "    wall: {texture: wall, size: [128, 128]}\n"
    "    floor: {texture: floor, size: [128, 128]}\n"
    "    ceiling: {texture: ceil, size: [128, 128]}\n"
    "defaults: {theme: theme:plain}\n";

bool hasIssue(const std::vector<ProjectIssue> &issues, const std::string &code, const std::string &fragment)
{
    return std::any_of(issues.begin(), issues.end(), [&code, &fragment](const ProjectIssue &issue)
    {
        return issue.code == code && issue.message.find(fragment) != std::string::npos;
    });
}
}

TEST_CASE("the built-in schemas load and name every project file")
{
    const SchemaSet &schemas = SchemaSet::builtIn();

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        CHECK(schemas.has(kind.pSchema));
    }
}

TEST_CASE("schema validation reports type, enum, pattern and unknown-key problems with their path")
{
    const YAML::Node document = YAML::Load(
        "format: 0\nid: Bad Id\nworld: mm6\nkind: cave\nextra: 1\nneighbours:\n  - {id: exit:a, to: x, days: many}\n");
    const std::vector<SchemaIssue> issues = SchemaSet::builtIn().validate(document, "project.schema.json");
    const auto has = [&issues](const std::string &path)
    {
        return std::any_of(issues.begin(), issues.end(), [&path](const SchemaIssue &issue)
        {
            return issue.path == path;
        });
    };
    CHECK(has("id"));
    CHECK(has("kind"));
    CHECK(has("extra"));
    CHECK(has("neighbours[0].days"));
    CHECK(issues.size() == 4);
}

TEST_CASE("canonical form orders keys by the schema, sorts id lists and is stable")
{
    const std::string messy =
        "rooms:\n"
        "  - {ceiling: 256, id: room:b, floor: 0, outline: [[0, 0], [64, 0], [64, 64], [0, 64]]}\n"
        "  - {id: room:a, outline: [[0, 0], [64, 0], [64, 64], [0, 64]], floor: 0, ceiling: 256, notes: \"a: b\"}\n"
        "format: 0\n";
    const YAML::Node document = YAML::Load(messy);
    const std::string once = writeCanonicalYaml(document, SchemaSet::builtIn(), "rooms.schema.json");
    const std::string twice = writeCanonicalYaml(YAML::Load(once), SchemaSet::builtIn(), "rooms.schema.json");
    CHECK(once == twice);
    CHECK(once.find("format: 0") == 0);
    CHECK(once.find("id: room:a") < once.find("id: room:b"));
    CHECK(once.find("notes: \"a: b\"") != std::string::npos);
    // Writing must not disturb the document it was given (yaml-cpp nodes alias their tree).
    CHECK(document["rooms"][0]["id"].Scalar() == "room:b");
    CHECK(document["rooms"][1]["id"].Scalar() == "room:a");
    CHECK(document["rooms"].size() == 2);
}

TEST_CASE("canonical form keeps text that looks like a number or null as text")
{
    YAML::Node document(YAML::NodeType::Map);
    YAML::Node digits(std::string("000"));
    digits.SetTag("!");
    YAML::Node empty(std::string{});
    empty.SetTag("!");
    document["digits"] = digits;
    document["empty"] = empty;
    document["number"] = 12.5;
    const std::string text = writeCanonicalYaml(document);
    CHECK(text == "digits: \"000\"\nempty: \"\"\nnumber: 12.5\n");
    const YAML::Node reread = YAML::Load(text);
    CHECK(classifyScalar(reread["digits"]) == ScalarKind::String);
    CHECK(classifyScalar(reread["empty"]) == ScalarKind::String);
}

TEST_CASE("JSON numbers are written in their shortest exact form")
{
    CHECK(formatNumber(3.0) == "3");
    CHECK(formatNumber(-0.5) == "-0.5");
    CHECK(formatNumber(0.1) == "0.1");
    JsonWriter writer;
    writer.beginObject();
    writer.field("a", 0.25f);
    writer.field("b", "x\"y");
    writer.endObject();
    CHECK(writer.text() == "{\"a\":0.25,\"b\":\"x\\\"y\"}");
}

TEST_CASE("the core's math functions give musl's bits on every target")
{
    // Inputs met building the 22 projects on which glibc and musl differ by an ulp (S5-0 spike 6): the core must
    // answer musl's, natively as in wasm.
    const auto bits = [](double value) { return std::bit_cast<uint64_t>(value); };
    CHECK(bits(oy::hypot(-158.82552391264107, 226.74433348054663)) == 0x40714d62fc357d14ULL);
    CHECK(bits(oy::atan2(233.39236127990148, -145.22191368515493)) == 0x400104e80200b6d2ULL);
    CHECK(bits(oy::tan(1.317247074599085)) == 0x400edf7d7792324fULL);
    CHECK(bits(oy::cos(3.7699111843077517)) == 0xbfe9e3779b97f4a8ULL);
    CHECK(bits(oy::sin(2.0943951023931957)) == 0x3febb67ae8584caaULL);
    CHECK(bits(oy::cbrt(0.3824740939811775)) == 0x3fe73a717ec14b47ULL);
    CHECK(oy::hypot(3.0, 4.0, 12.0) == 13.0);
    CHECK(oy::hypot(0.0, -0.0, 0.0) == 0.0);
    CHECK(oy::pow(10.0, 3.0) == 1000.0);
}

TEST_CASE("an opening needs facing walls, and a door needs a wall as thick as itself")
{
    const std::string rooms = std::string(ThemeText) +
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[528, 0], [1040, 0], [1040, 512], [528, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:far, outline: [[4096, 4096], [4608, 4096], [4608, 4608], [4096, 4608]], floor: 0,\n"
        "     ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n"
        "  - {id: open:afar, from: room:a, to: room:far, width: 128, height: 256}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, thickness: 32}\n";
    const Project project =
        projectFromTexts({{"project.yml", CardText}, {"rooms.yml", rooms}, {"objects.yml", objects}});
    std::vector<ProjectIssue> issues;
    validateProject(project, {}, issues);
    CHECK(hasIssue(issues, "geometry", "no facing parallel walls"));
    CHECK(hasIssue(issues, "geometry", "thick"));
}

TEST_CASE("lowering gives one node per room, portal, door and object, and keeps locked numbers")
{
    const std::string rooms = std::string(ThemeText) +
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab}\n"
        "lights:\n  - {id: light:a, room: room:a}\n";
    const std::string wiring = "format: 0\nevents:\n  - {id: evt:door, preset: door, source: door:ab}\n";
    // The lock says room:b was built first and the door event is number 7.
    const std::string lock = "format: 0\nsectors: {room:b: 1}\nevents: {evt:gone: 1, evt:door: 7}\n";
    const Project project = projectFromTexts({
        {"project.yml", CardText}, {"rooms.yml", rooms}, {"objects.yml", objects}, {"wiring.yml", wiring},
        {"ids.lock.yml", lock}});
    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    REQUIRE(lowerIndoorProject(project, {}, lowered, issues));
    CHECK(issues.empty());
    std::vector<std::string> names;

    for (const GlbNode &node : lowered.nodes)
    {
        names.push_back(node.name);
    }

    CHECK(names == std::vector<std::string>{"ROOM_b", "ROOM_a", "PORTAL_ab", "MECH_ab", "LIGHT_a"});
    CHECK(lowered.ids.sectors["room:b"] == 1);
    CHECK(lowered.ids.sectors["room:a"] == 2);
    CHECK(lowered.ids.events["evt:door"] == 7);
    CHECK(lowered.events.size() == 1);
    CHECK(lowered.events[0].body == std::vector<std::string>{"evt.SetDoorState(1, DoorAction.Trigger)"});
    // Room a: four walls, one of them cut into three pieces (left, right, over the opening), floor, ceiling and
    // the doorway's threshold, soffit and two jambs.
    CHECK(lowered.nodes[1].faces.size() == 3 + 3 + 2 + 4);
    // The floor has a corner at each side of the opening, so edges meet corner to corner.
    size_t largestFace = 0;

    for (const GlbFace &face : lowered.nodes[1].faces)
    {
        largestFace = std::max(largestFace, face.positions.size());
    }

    CHECK(largestFace == 6);
}

TEST_CASE("a condition the build cannot lower is an issue, never silently true")
{
    const std::string rooms = std::string(ThemeText) +
        "rooms:\n  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a}\nexits:\n  - {id: exit:out, room: room:a, wall: south, to: exit:x}\n";
    const std::string wiring =
        "format: 0\nevents:\n  - {id: evt:t, preset: text, source: exit:out, condition: {time: night}, text: hi}\n";
    const Project project = projectFromTexts(
        {{"project.yml", CardText}, {"rooms.yml", rooms}, {"objects.yml", objects}, {"wiring.yml", wiring}});
    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    CHECK_FALSE(lowerIndoorProject(project, {}, lowered, issues));
    CHECK(hasIssue(issues, "unsupported", "'time' condition"));
}

TEST_CASE("canonical form writes a text of several lines as a block and reads it back unchanged")
{
    YAML::Node document(YAML::NodeType::Map);
    document["diagram"]["text"] = "[a]--[b]\n  |\n[c]";
    document["note"] = "ends with a break\n";
    document["list"].push_back("one\ntwo");
    const std::string text = writeCanonicalYaml(document);
    CHECK(text == "diagram:\n  text: |-\n    [a]--[b]\n      |\n    [c]\nnote: |\n  ends with a break\nlist:\n"
                  "  - |-\n    one\n    two\n");
    const YAML::Node reread = YAML::Load(text);
    CHECK(reread["diagram"]["text"].Scalar() == "[a]--[b]\n  |\n[c]");
    CHECK(reread["note"].Scalar() == "ends with a break\n");
    CHECK(reread["list"][0].Scalar() == "one\ntwo");
    CHECK(writeCanonicalYaml(reread) == text);
}

TEST_CASE("names of items in treasure and drops must be declared on the map card")
{
    const std::string plan =
        "format: 0\nspaces:\n  - id: room:a\n    treasure: [{kind: chest, item: lost_key}]\n"
        "    population: [{actor: guard, drops: longbow}]\n";
    const std::string card = std::string(CardText) + "items: {longbow: 12}\n";
    const Project project = projectFromTexts({{"project.yml", card}, {"plan.yml", plan}});
    std::vector<ProjectIssue> issues;
    validateProject(project, {}, issues);
    CHECK(hasIssue(issues, "reference", "'lost_key'"));
    CHECK_FALSE(hasIssue(issues, "reference", "'longbow'"));
}

TEST_CASE("rooms that share space are refused, and the plan's arrival can stand in for an objects.yml start")
{
    const std::string rooms = std::string(ThemeText) +
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[256, 256], [768, 256], [768, 768], [256, 768]], floor: 0, ceiling: 384}\n"
        "  - {id: room:above, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 448, ceiling: 832}\n";
    const std::string plan =
        "format: 0\nspaces:\n  - {id: room:a}\n  - {id: room:b}\n  - {id: room:above}\n"
        "entrances:\n  - {id: entrance:in, space: room:a, kind: arrival, facing: n}\n";
    const Project project = projectFromTexts({{"project.yml", CardText}, {"rooms.yml", rooms}, {"plan.yml", plan}});
    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    CHECK_FALSE(lowerIndoorProject(project, {}, lowered, issues));
    CHECK(hasIssue(issues, "geometry", "room:a and room:b overlap"));
    CHECK_FALSE(hasIssue(issues, "geometry", "room:above"));
    CHECK_FALSE(hasIssue(issues, "project", "party start"));
}

namespace
{
// A small project on disk, in a folder of its own.
std::filesystem::path writeTestProject()
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_ops_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    const auto write = [&root](const char *pName, const std::string &text)
    {
        std::ofstream(root / pName, std::ios::binary) << text;
    };
    write("project.yml", CardText);
    write("rooms.yml", std::string(ThemeText) +
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n");
    write("objects.yml", "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, speed: 96}\n");
    return root;
}

std::string readText(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

bool hasLine(const std::vector<std::string> &lines, const std::string &fragment)
{
    return std::any_of(lines.begin(), lines.end(), [&fragment](const std::string &line)
    {
        return line.find(fragment) != std::string::npos;
    });
}
}

TEST_CASE("a transaction applies all of its operations or none, and reports a semantic diff")
{
    const std::filesystem::path root = writeTestProject();
    const std::string objectsBefore = readText(root / "objects.yml");
    TransactionResult refused;
    // The second operation names a door that does not exist: nothing is written, not even the first.
    CHECK_FALSE(applyTransaction(root, YAML::Load(
        "[{op: light.add, value: {id: light:a, room: room:a}}, {op: set, id: door:none, fields: {speed: 1}}]"),
        {}, refused));
    CHECK_FALSE(refused.applied);
    CHECK(hasLine(refused.errors, "door:none"));
    CHECK(readText(root / "objects.yml") == objectsBefore);

    // A change that introduces a validation issue is refused unless allowed.
    TransactionResult broken;
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: remove, id: open:ab}]"), {}, broken));
    CHECK_FALSE(broken.newIssues.empty());
    CHECK(readText(root / "objects.yml") == objectsBefore);

    TransactionResult applied;
    REQUIRE(applyTransaction(root, YAML::Load(
        "[{op: light.add, value: {id: light:a, room: room:a}}, {op: set, id: door:ab, fields: {speed: 64}}]"),
        {}, applied));
    CHECK(applied.applied);
    CHECK(hasLine(applied.changes, "added light:a"));
    CHECK(hasLine(applied.changes, "door:ab changed speed"));
    CHECK(applied.revisionBefore != applied.revisionAfter);

    // A transaction that expects an older revision is refused.
    TransactionOptions stale;
    stale.expectRevision = applied.revisionBefore;
    TransactionResult late;
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: remove, id: light:a}]"), stale, late));
    CHECK(hasLine(late.errors, "revision"));

    // A dry run reports and writes nothing.
    TransactionOptions dry;
    dry.dryRun = true;
    TransactionResult tried;
    const std::string objectsAfter = readText(root / "objects.yml");
    CHECK(applyTransaction(root, YAML::Load("[{op: remove, id: light:a}]"), dry, tried));
    CHECK(hasLine(tried.changes, "removed light:a"));
    CHECK(readText(root / "objects.yml") == objectsAfter);
    std::filesystem::remove_all(root);
}

TEST_CASE("ids are unique per file: an id in two files needs `file` on set and remove; add checks its own file")
{
    // The repro of S5 spike 4: in the example, room:entry is both a plan space (plan.yml) and a room (rooms.yml).
    // Before, `set` took the first file in name order (plan.yml) without a word.
    const std::filesystem::path example = std::filesystem::path(__FILE__).parent_path().parent_path()
        / "examples" / "gatehouse_cellars";
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_ids_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);

    for (const char *pName : {"project.yml", "plan.yml", "rooms.yml", "objects.yml", "wiring.yml", "ids.lock.yml"})
    {
        REQUIRE(std::filesystem::is_regular_file(example / pName));
        std::filesystem::copy_file(example / pName, root / pName);
    }

    const std::string planBefore = readText(root / "plan.yml");
    const std::string roomsBefore = readText(root / "rooms.yml");
    TransactionOptions dry;
    dry.dryRun = true;

    TransactionResult ambiguous;
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: set, id: room:entry, fields: {name: Porch}}]"), dry,
        ambiguous));
    CHECK(hasLine(ambiguous.errors, "the id room:entry is in plan.yml and rooms.yml"));
    CHECK(hasLine(ambiguous.errors, "`file`"));

    TransactionResult removeAmbiguous;
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: remove, id: room:entry}]"), dry, removeAmbiguous));
    CHECK(hasLine(removeAmbiguous.errors, "plan.yml and rooms.yml"));

    // Named, each file's object is the one changed.
    TransactionResult room;
    REQUIRE(applyTransaction(root, YAML::Load(
        "[{op: set, id: room:entry, file: rooms.yml, fields: {name: Porch}}]"), dry, room));
    REQUIRE(room.changes.size() == 1);
    CHECK(room.changes[0].rfind("rooms.yml", 0) == 0);
    CHECK(hasLine(room.changes, "room:entry changed name"));

    TransactionResult space;
    REQUIRE(applyTransaction(root, YAML::Load(
        "[{op: set, id: room:entry, file: plan.yml, fields: {name: Porch}}]"), dry, space));
    REQUIRE(space.changes.size() == 1);
    CHECK(space.changes[0].rfind("plan.yml", 0) == 0);

    // A file that does not hold the id, or is not in the project, is refused by name.
    TransactionResult wrongFile;
    CHECK_FALSE(applyTransaction(root, YAML::Load(
        "[{op: set, id: room:entry, file: objects.yml, fields: {name: Porch}}]"), dry, wrongFile));
    CHECK(hasLine(wrongFile.errors, "nothing in objects.yml has the id room:entry"));

    // An id in one file needs no `file`: door ids are only in objects.yml.
    TransactionResult single;
    REQUIRE(applyTransaction(root, YAML::Load("[{op: set, id: door:gate, fields: {speed: 64}}]"), dry, single));
    CHECK(hasLine(single.changes, "objects.yml: door:gate changed speed"));

    // add checks only its own file: a room's id may be a plan space's, never another room's.
    TransactionOptions loose = dry;
    loose.allowNewIssues = true;
    TransactionResult addSpace;
    REQUIRE(applyTransaction(root, YAML::Load(
        "[{op: room.add, value: {id: room:annex, outline: [[2000, 0], [2512, 0], [2512, 512], [2000, 512]], "
        "floor: 0, ceiling: 384}}, {op: space.add, value: {id: room:annex, name: Annex, kind: room, size: S}}]"),
        loose, addSpace));
    CHECK(hasLine(addSpace.changes, "rooms.yml: added room:annex"));
    CHECK(hasLine(addSpace.changes, "plan.yml: added room:annex"));

    TransactionResult addTwice;
    CHECK_FALSE(applyTransaction(root, YAML::Load(
        "[{op: room.add, value: {id: room:entry, outline: [[2000, 0], [2512, 0], [2512, 512]], floor: 0}}]"),
        loose, addTwice));
    CHECK(hasLine(addTwice.errors, "the id room:entry is already used in rooms.yml"));

    // A dry run wrote nothing.
    CHECK(readText(root / "plan.yml") == planBefore);
    CHECK(readText(root / "rooms.yml") == roomsBefore);
    std::filesystem::remove_all(root);
}

TEST_CASE("an edit made outside the tool between two transactions is found, described and can be undone")
{
    const std::filesystem::path root = writeTestProject();
    TransactionResult first;
    REQUIRE(applyTransaction(root, YAML::Load("[{op: set, id: door:ab, fields: {speed: 64}}]"), {}, first));

    // Someone edits the file by hand.
    std::string objects = readText(root / "objects.yml");
    const size_t speed = objects.find("speed: 64");
    REQUIRE(speed != std::string::npos);
    objects.replace(speed, 9, "speed: 200");
    std::ofstream(root / "objects.yml", std::ios::binary) << objects;

    TransactionResult second;
    REQUIRE(applyTransaction(root, YAML::Load("[{op: light.add, value: {id: light:a, room: room:a}}]"), {}, second));
    CHECK(hasLine(second.outsideChanges, "door:ab changed speed"));

    ProjectStatus status;
    std::string errorMessage;
    REQUIRE(projectStatus(root, status, errorMessage));
    REQUIRE(status.history.size() == 3);
    CHECK(status.history[0].kind == "transaction");
    CHECK(status.history[1].kind == "outside");
    CHECK(status.history[2].kind == "transaction");
    CHECK(status.outsideChanges.empty());

    // Undo twice: the light goes, then the hand edit.
    std::vector<std::string> changes;
    REQUIRE(undoProject(root, changes, errorMessage));
    REQUIRE(undoProject(root, changes, errorMessage));
    CHECK(readText(root / "objects.yml").find("speed: 64") != std::string::npos);
    CHECK(readText(root / "objects.yml").find("light:a") == std::string::npos);
    REQUIRE(redoProject(root, changes, errorMessage));
    CHECK(readText(root / "objects.yml").find("speed: 200") != std::string::npos);
    std::filesystem::remove_all(root);
}

TEST_CASE("an overlay project lowers each event under the number of the base event it replaces")
{
    const std::string card = "format: 0\nid: rewire\nworld: mm6\nkind: indoor\nbase: 6d01.blv\n";
    const std::string lock = "format: 0\nevents: {evt:e20: 20, evt:e23: 23}\ndoors: {door:d55: 55, door:d57: 57}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:key_b, preset: switch, replaces: evt:e20, title: B, condition: {not: {map_var: 2}},\n"
        "     opens: [door:d57], closes: [door:d55], sets: {map_var: 2}}\n"
        "  - {id: evt:trap, preset: script, replaces: evt:e23, lua: \"evt.MoveToMap(1, 2, 3)\"}\n";
    const Project project = projectFromTexts({{"project.yml", card}, {"wiring.yml", wiring}, {"ids.lock.yml", lock}});
    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    REQUIRE(lowerOverlayProject(project, lowered, issues));
    CHECK(issues.empty());
    CHECK(lowered.mapStem == "6d01");
    REQUIRE(lowered.events.size() == 2);
    CHECK(lowered.events[0].eventId == 20);
    CHECK(std::find(lowered.events[0].body.begin(), lowered.events[0].body.end(),
        "evt.SetDoorState(57, DoorAction.Open)") != lowered.events[0].body.end());
    CHECK(lowered.events[1].eventId == 23);
    CHECK(lowered.events[1].body == std::vector<std::string>{"evt.MoveToMap(1, 2, 3)"});

    // An event that replaces nothing the base map has, and a named map variable, are refused: an overlay has no
    // numbers of its own to give them.
    const std::string wrong =
        "format: 0\nevents:\n"
        "  - {id: evt:new, preset: switch, replaces: evt:e99, opens: [door:d57]}\n"
        "  - {id: evt:named, preset: switch, replaces: evt:e20, opens: [door:d57], sets: {map_var: opened}}\n";
    const Project broken = projectFromTexts({{"project.yml", card}, {"wiring.yml", wrong}, {"ids.lock.yml", lock}});
    issues.clear();
    CHECK_FALSE(lowerOverlayProject(broken, lowered, issues));
    CHECK(issues.size() >= 2);
}

TEST_CASE("a placeholder holds a place and a request: it is checked, not built, and reported")
{
    const std::string rooms = std::string(ThemeText) +
        "rooms:\n  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a}\nplaceholders:\n"
        "  - {id: ph:statue, room: room:a, stands_for: a statue of a kneeling knight, size: [96, 96, 256]}\n"
        "  - {id: ph:lost, room: room:none, stands_for: nothing}\n";
    const Project project =
        projectFromTexts({{"project.yml", CardText}, {"rooms.yml", rooms}, {"objects.yml", objects}});
    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    lowerIndoorProject(project, {}, lowered, issues);
    CHECK(lowered.placeholders == std::vector<std::string>{"ph:statue: a statue of a kneeling knight"});
    CHECK(hasIssue(issues, "reference", "room:none"));
}

TEST_CASE("a bent polygon is cut into convex pieces that use only its own points and cover it")
{
    // An L with an extra point in the middle of one side.
    const std::vector<Point2> outline = {{0, 0}, {512, 0}, {1024, 0}, {1024, 512}, {512, 512}, {512, 1024}, {0, 1024}};
    CHECK(polygonIsSimple(outline));
    const std::vector<std::vector<size_t>> pieces = convexPieces(outline, 20);
    REQUIRE(pieces.size() >= 2);
    double area = 0.0;
    std::vector<int> uses(outline.size(), 0);

    for (const std::vector<size_t> &piece : pieces)
    {
        std::vector<Point2> points;

        for (const size_t index : piece)
        {
            points.push_back(outline[index]);
            ++uses[index];
        }

        area += polygonDoubleArea(points);

        for (size_t corner = 0; corner < points.size(); ++corner)
        {
            const Point2 &a = points[corner];
            const Point2 &b = points[(corner + 1) % points.size()];
            const Point2 &c = points[(corner + 2) % points.size()];
            CHECK((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) >= -1.0e-6);
        }
    }

    CHECK(area == doctest::Approx(polygonDoubleArea(outline)));
    // Every point of the outline is a corner of some piece: also the one in the middle of a side.
    CHECK(std::all_of(uses.begin(), uses.end(), [](int count) { return count > 0; }));

    // A figure of eight is refused.
    CHECK_FALSE(polygonIsSimple({{0, 0}, {512, 512}, {512, 0}, {0, 512}}));
    // Inside the L's notch is outside the room; rooms that only touch do not overlap, rooms that share area do.
    CHECK_FALSE(pointInPolygon(outline, {768, 768}, 0.0));
    CHECK(pointInPolygon(outline, {256, 768}, 0.0));
    const std::vector<Point2> inNotch = {{512, 512}, {1024, 512}, {1024, 1024}, {512, 1024}};
    const std::vector<Point2> acrossBend = {{256, 256}, {768, 256}, {768, 768}, {256, 768}};
    CHECK_FALSE(polygonsOverlap(outline, inNotch));
    CHECK(polygonsOverlap(outline, acrossBend));
    // Two equal rectangles shifted along a shared side line overlap (no corner of one lies inside the other).
    CHECK(polygonsOverlap({{0, 0}, {512, 0}, {512, 256}, {0, 256}}, {{256, 0}, {768, 0}, {768, 256}, {256, 256}}));
}

TEST_CASE("a path is widened into a corridor outline with mitred bends, and a bend too tight is refused")
{
    std::string error;
    const std::vector<Point2> outline = pathOutline({{0, 0}, {512, 0}, {512, 512}}, 128, error);
    CHECK(error.empty());
    CHECK(outline == std::vector<Point2>{{0, -64}, {576, -64}, {576, 512}, {448, 512}, {448, 64}, {0, 64}});
    CHECK(polygonDoubleArea(outline) > 0.0);
    CHECK(pathOutline({{0, 0}, {512, 0}, {0, 16}}, 128, error).empty());
    CHECK_FALSE(error.empty());
}

TEST_CASE("stairs lower to treads and risers, and a doorway at their top begins at the upper floor")
{
    const std::string rooms = std::string(ThemeText) +
        "rooms:\n"
        "  - {id: room:low, outline: [[0, 0], [256, 0], [256, 256], [0, 256]], floor: 0, ceiling: 512}\n"
        "  - {id: room:stairs, outline: [[0, 320], [256, 320], [256, 832], [0, 832]], floor: 0, ceiling: 512,\n"
        "     slope: {to: 128, toward: 2, steps: 4}}\n"
        "  - {id: room:high, outline: [[0, 896], [256, 896], [256, 1152], [0, 1152]], floor: 128, ceiling: 512}\n"
        "openings:\n"
        "  - {id: open:a, from: room:low, to: room:stairs, width: 128, height: 256}\n"
        "  - {id: open:b, from: room:stairs, to: room:high, width: 128, height: 256}\n";
    const std::string objects = "format: 0\nstart: {room: room:low}\nlights:\n  - {id: light:mid, room: room:stairs}\n";
    const Project project =
        projectFromTexts({{"project.yml", CardText}, {"rooms.yml", rooms}, {"objects.yml", objects}});
    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    REQUIRE(lowerIndoorProject(project, {}, lowered, issues));
    CHECK(issues.empty());
    const GlbNode *pStairs = nullptr;

    for (const GlbNode &node : lowered.nodes)
    {
        if (node.name == "ROOM_stairs")
        {
            pStairs = &node;
        }
    }

    REQUIRE(pStairs != nullptr);
    // Flat faces by height: four treads at 0, 32, 64 and 96, the upper doorway's threshold (128) and soffit (384), and
    // the ceiling; three risers between the treads.
    std::map<int, int> flatFaces;
    int risers = 0;

    for (const GlbFace &face : pStairs->faces)
    {
        float lowest = face.positions[0][2];
        float highest = lowest;
        float lowY = face.positions[0][1];
        float highY = lowY;

        for (const std::array<float, 3> &position : face.positions)
        {
            lowest = std::min(lowest, position[2]);
            highest = std::max(highest, position[2]);
            lowY = std::min(lowY, position[1]);
            highY = std::max(highY, position[1]);
        }

        if (lowest == highest)
        {
            ++flatFaces[static_cast<int>(lowest)];
        }
        else if (lowY == highY && highest - lowest == 32.0f && lowY > 320.0f && lowY < 832.0f)
        {
            ++risers;
        }
    }

    CHECK(flatFaces == std::map<int, int>{{0, 1}, {32, 1}, {64, 1}, {96, 1}, {128, 1}, {384, 1}, {512, 1}});
    CHECK(risers == 3);
    // The doorway into the upper room starts at the upper floor: the last riser is the wall under it.
    CHECK(lowered.openings[1].bottom == 128.0);
    // A step too high for the party, and an opening in a wall the floor climbs along, are refused.
    const auto issuesOf = [](const std::string &roomsText)
    {
        std::vector<ProjectIssue> found;
        LoweredIndoorMap unused;
        lowerIndoorProject(projectFromTexts({{"project.yml", CardText}, {"rooms.yml", roomsText},
            {"objects.yml", "format: 0\nstart: {room: room:low}\n"}}), {}, unused, found);
        return found;
    };
    std::string steep = rooms;
    steep.replace(steep.find("steps: 4"), 8, "steps: 2");
    CHECK(hasIssue(issuesOf(steep), "geometry", "each step would rise"));
    const std::string side = std::string(ThemeText) +
        "rooms:\n"
        "  - {id: room:low, outline: [[320, 448], [576, 448], [576, 704], [320, 704]], floor: 0, ceiling: 512}\n"
        "  - {id: room:ramp, outline: [[0, 320], [256, 320], [256, 832], [0, 832]], floor: 0, ceiling: 512,\n"
        "     slope: {to: 128, toward: 2}}\n"
        "openings:\n"
        "  - {id: open:a, from: room:low, to: room:ramp, width: 128, height: 256}\n";
    CHECK(hasIssue(issuesOf(side), "geometry", "the floor rises along"));
}

TEST_CASE("a hole cut into a floor leaves convex pieces that cover the floor without the hole")
{
    const std::vector<Point2> room = {{0, 0}, {1024, 0}, {1024, 1024}, {0, 1024}};
    const std::vector<Point2> island = {{384, 384}, {640, 384}, {640, 640}, {384, 640}};
    const std::vector<Point2> ring = cutHole(room, island);
    REQUIRE(ring.size() == room.size() + island.size() + 2);
    const std::vector<std::vector<size_t>> pieces = convexPieces(ring, 20);
    REQUIRE_FALSE(pieces.empty());
    double area = 0.0;

    for (const std::vector<size_t> &piece : pieces)
    {
        std::vector<Point2> points;

        for (const size_t index : piece)
        {
            points.push_back(ring[index]);
        }

        area += polygonDoubleArea(points);
        // No piece covers the middle of the island.
        CHECK_FALSE(pointInPolygon(points, {512, 512}, 0.0));
    }

    CHECK(area == doctest::Approx(polygonDoubleArea(room) - polygonDoubleArea(island)));
}

TEST_CASE("an open mouth takes the whole shared wall, and rough walls only ever move into the room")
{
    const std::string rooms = std::string(ThemeText) +
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384,\n"
        "     rough: {step: 128, depth: 48}}\n"
        "  - {id: room:b, outline: [[1024, 256], [1536, 256], [1536, 768], [1024, 768]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: full, height: full}\n";
    const Project project = projectFromTexts({{"project.yml", CardText}, {"rooms.yml", rooms},
        {"objects.yml", "format: 0\nstart: {room: room:a}\n"}});
    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    REQUIRE(lowerIndoorProject(project, {}, lowered, issues));
    CHECK(issues.empty());
    CHECK(lowered.openings[0].fromHigh - lowered.openings[0].fromLow == 512.0);
    CHECK(lowered.openings[0].top == 384.0);
    bool jagged = false;

    for (const GlbNode &node : lowered.nodes)
    {
        if (node.name != "ROOM_a")
        {
            continue;
        }

        for (const GlbFace &face : node.faces)
        {
            for (const std::array<float, 3> &position : face.positions)
            {
                CHECK(position[0] >= 0.0f);
                CHECK(position[0] <= 1024.0f);
                CHECK(position[1] >= 0.0f);
                CHECK(position[1] <= 1024.0f);
                jagged = jagged || (position[0] > 0.5f && position[0] < 60.0f);
            }
        }
    }

    CHECK(jagged);
}


// ---- outdoor sketch (sketch.yml) ----

#include "core/Preview.h"
#include "core/Sketch.h"

namespace
{
const char *OutdoorCardText =
    "format: 0\nid: testland\nworld: mm6\nkind: outdoor\n"
    "neighbours:\n"
    "  - {id: edge:far_land, to: out02.odm, kind: edge, side: north}\n";
const char *OutdoorPlanText =
    "format: 0\n"
    "spaces:\n"
    "  - id: district:village\n"
    "    kind: district\n"
    "    buildings:\n"
    "      - {id: building:inn, count: 1, footprint_cells: [4, 3]}\n"
    "      - {id: building:houses, count: 2, footprint_cells: [[2, 2], [3, 1.5]]}\n"
    "    population:\n"
    "      - {id: pop:rats}\n"
    "  - {id: junction:cross, kind: junction}\n"
    "  - {id: edge:north, kind: junction}\n"
    "  - {id: water:pond, kind: water}\n"
    "links:\n"
    "  - {id: road:north, from: edge:north, to: junction:cross, kind: road}\n"
    "entrances:\n"
    "  - {id: entrance:north, space: district:village}\n"
    "points_of_interest:\n"
    "  - {id: poi:well, kind: well, space: district:village}\n"
    "landmarks:\n"
    "  - {id: landmark:tower}\n"
    "sightlines:\n"
    "  - {id: sight:arrival, from: district:village}\n"
    "height_bands:\n"
    "  - {id: band:low, range: [0, 512]}\n";

// The sketch's parts, so a test can replace one of them.
struct SketchTexts
{
    std::string heights =
        "heights:\n"
        "  points:\n"
        "    - {at: [50, 50], h: 256}\n"
        "  bands:\n"
        "    - {band: band:low, polygon: [[30, 30], [90, 30], [90, 90], [30, 90]]}\n"
        "  cliffs:\n"
        "    - {line: [[30, 95], [90, 95]], drop: 600, down: right}\n";
    std::string water =
        "water:\n"
        "  bodies:\n"
        "    - {id: water:pond, kind: pond, level: 128, polygon: [[70, 70], [80, 70], [80, 80], [70, 80]]}\n";
    std::string plots =
        "      - {building: building:inn, at: [42, 42], facing: s, door_to: road:north}\n"
        "      - {building: building:houses, index: 1, at: [50.5, 42], facing: e, door_to: district:village}\n"
        "      - {building: building:houses, index: 2, at: [54, 42], facing: w}\n";
    std::string points =
        "points:\n"
        "  - {id: edge:north, at: [60, 20]}\n"
        "  - {id: junction:cross, at: [60, 40]}\n"
        "  - {id: entrance:north, at: [60, 22], facing: s}\n"
        "  - {id: poi:well, at: [58, 50]}\n"
        "  - {id: landmark:tower, at: [44, 60]}\n";
    std::string areas =
        "areas:\n"
        "  - {id: pop:rats, circle: {at: [48, 56], r: 2}}\n"
        "  - {id: district:village, kind: keep_clear, polygon: [[56, 36], [64, 36], [64, 44], [56, 44]]}\n";

    std::string text() const
    {
        return "format: 0\ngrid: 512\n"
            "frame:\n"
            "  playable: [20, 20, 88, 88]\n"
            "  edges:\n"
            "    - {side: north, span: [50, 70], neighbour: edge:far_land}\n"
            + heights + water +
            "roads:\n"
            "  - {link: road:north, line: [[60.5, 0], [60.5, 20], [60, 40]], width: road, surface: dirt}\n"
            "districts:\n"
            "  - space: district:village\n"
            "    polygon: [[40, 40], [80, 40], [80, 66], [40, 66]]\n"
            "    plots:\n"
            + plots + points + areas +
            "views:\n"
            "  - {id: sight:arrival, at: [60, 22], height: 200, look: [44, 60], purpose: The tower.}\n"
            "ground:\n"
            "  - {material: soil, polygon: [[40, 40], [80, 40], [80, 66], [40, 66]]}\n";
    }
};

std::vector<ProjectIssue> sketchIssues(const SketchTexts &texts)
{
    const Project project = projectFromTexts({{"project.yml", OutdoorCardText}, {"plan.yml", OutdoorPlanText},
        {"sketch.yml", texts.text()}});
    std::vector<ProjectIssue> issues;
    validateProjectSchemas(project, issues);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.file << ": " << issue.path << ": " << issue.message);
    }

    REQUIRE(issues.empty());
    validateSketch(project, issues);
    return issues;
}
}

TEST_CASE("a small outdoor sketch passes its schema and checks, and draws")
{
    const SketchTexts texts;
    const std::vector<ProjectIssue> issues = sketchIssues(texts);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    CHECK(issues.empty());
    const Project project = projectFromTexts({{"project.yml", OutdoorCardText}, {"plan.yml", OutdoorPlanText},
        {"sketch.yml", texts.text()}});
    std::array<double, 4> rectangle = {0.0, 0.0, 0.0, 0.0};
    // The second house, [front 3, depth 1.5], faces west: its front runs north-south.
    REQUIRE(sketchPlotRectangle(project.document("plan.yml"),
        project.document("sketch.yml")["districts"][0]["plots"][2], rectangle));
    CHECK(rectangle == std::array<double, 4>{54.0, 42.0, 55.5, 45.0});
    SketchPreviewOptions options;
    options.size = 512;
    const Image image = renderSketch(project, options);
    CHECK(image.width == 512);
    CHECK(image.pixels.size() == 512u * 512u * 3u);
    CHECK(encodePng(image) == encodePng(renderSketch(project, options)));
}

TEST_CASE("a sketch that names an id the plan does not have is told which and where")
{
    SketchTexts texts;
    texts.points += "  - {id: poi:missing_shrine, at: [70, 60]}\n";
    std::vector<ProjectIssue> issues = sketchIssues(texts);
    REQUIRE(issues.size() == 1);
    CHECK(issues[0].code == "reference");
    CHECK(issues[0].path == "points[5].id");
    CHECK(issues[0].message.find("poi:missing_shrine") != std::string::npos);

    // An id of the wrong kind: an encounter area needs a population.
    texts = {};
    texts.areas = "areas:\n  - {id: poi:well, circle: {at: [48, 56], r: 2}}\n";
    issues = sketchIssues(texts);
    CHECK(hasIssue(issues, "reference", "point of interest"));
}

TEST_CASE("plots that overlap, leave their district or miss a building are reported")
{
    SketchTexts texts;
    // The inn covers x 42 to 46, y 42 to 45; the first house (2 by 2) now stands on its east end.
    texts.plots =
        "      - {building: building:inn, at: [42, 42], facing: s, door_to: road:north}\n"
        "      - {building: building:houses, index: 1, at: [45, 43], facing: e}\n"
        "      - {building: building:houses, index: 2, at: [54, 42], facing: w}\n";
    std::vector<ProjectIssue> issues = sketchIssues(texts);
    REQUIRE(issues.size() == 1);
    CHECK(issues[0].code == "geometry");
    CHECK(issues[0].path == "districts[0].plots[1].at");
    CHECK(issues[0].message.find("overlap") != std::string::npos);
    CHECK(issues[0].message.find("building:inn") != std::string::npos);

    // Touching along an edge is not overlapping; standing half outside the district is reported.
    texts.plots =
        "      - {building: building:inn, at: [42, 42], facing: s}\n"
        "      - {building: building:houses, index: 1, at: [46, 42], facing: e}\n"
        "      - {building: building:houses, index: 2, at: [79, 42], facing: w}\n";
    issues = sketchIssues(texts);
    REQUIRE(issues.size() == 1);
    CHECK(hasIssue(issues, "geometry", "leaves the outline of district:village"));

    // A member of the group without a plot is a coverage issue.
    texts.plots = "      - {building: building:inn, at: [42, 42], facing: s}\n"
        "      - {building: building:houses, index: 2, at: [54, 42], facing: w}\n";
    issues = sketchIssues(texts);
    REQUIRE(issues.size() == 1);
    CHECK(hasIssue(issues, "coverage", "no plot for index 1"));
}

TEST_CASE("a polygon that crosses itself is refused with the edges that cross")
{
    SketchTexts texts;
    texts.areas = "areas:\n  - {id: pop:rats, polygon: [[44, 50], [52, 58], [52, 50], [44, 58]]}\n";
    const std::vector<ProjectIssue> issues = sketchIssues(texts);
    REQUIRE(issues.size() == 1);
    CHECK(issues[0].code == "geometry");
    CHECK(issues[0].path == "areas[0].polygon");
    CHECK(issues[0].message.find("crosses or touches the edge") != std::string::npos);
}

TEST_CASE("a height grid finer than four cells is refused, by the schema and by the check")
{
    SketchTexts texts;
    texts.heights += "  grid: {step: 2, rows: [[1, 2], [3, 4]]}\n";
    const Project project = projectFromTexts({{"project.yml", OutdoorCardText}, {"plan.yml", OutdoorPlanText},
        {"sketch.yml", texts.text()}});
    std::vector<ProjectIssue> issues;
    validateProjectSchemas(project, issues);
    CHECK(hasIssue(issues, "schema", "at least 4"));
    issues.clear();
    validateSketch(project, issues);
    CHECK(hasIssue(issues, "heights", "4 cells or coarser"));

    // The right step with the wrong number of rows.
    texts = {};
    texts.heights += "  grid: {step: 64, rows: [[1, 2], [3, 4], [5, 6]]}\n";
    CHECK(hasIssue(sketchIssues(texts), "heights", "2 rows of 2 values"));
}

TEST_CASE("heights against bands and water, roads against junctions, and places the plan expects")
{
    SketchTexts texts;
    // 900 inside a band of 0 to 512; a shore point below the pond's level; the road stops short of the crossing.
    texts.heights =
        "heights:\n"
        "  points:\n"
        "    - {at: [50, 50], h: 900}\n"
        "    - {at: [69, 75], h: 64}\n"
        "  bands:\n"
        "    - {band: band:low, polygon: [[30, 30], [90, 30], [90, 90], [30, 90]]}\n";
    texts.points =
        "points:\n"
        "  - {id: edge:north, at: [60, 20]}\n"
        "  - {id: junction:cross, at: [66, 44]}\n"
        "  - {id: entrance:north, at: [60, 22]}\n"
        "  - {id: landmark:tower, at: [44, 60]}\n";
    const std::vector<ProjectIssue> issues = sketchIssues(texts);
    CHECK(issues.size() == 4);
    CHECK(hasIssue(issues, "heights", "outside the range of the band"));
    CHECK(hasIssue(issues, "heights", "above the ground on its shore"));
    CHECK(hasIssue(issues, "geometry", "misses the junction junction:cross"));
    CHECK(hasIssue(issues, "coverage", "poi:well has no place"));
}

// ---- Outdoor lowering (S4, second slice): appended by the outdoor build; needs core/OutdoorLowering.h.
#include "core/OutdoorLowering.h"

namespace
{
// Low ground in the north, high ground in the south, a cliff between them along y = 64 whose low side is the north
// (left, walking east), a height point on each side and a lake in the low ground.
const char *LoweringCardText = "format: 0\nid: lowtest\nworld: mm8\nkind: outdoor\n";
const char *LoweringPlanText =
    "format: 0\n"
    "entrances:\n"
    "  - {id: entrance:north, kind: arrival, facing: s}\n"
    "height_bands:\n"
    "  - {id: band:low, range: [0, 512]}\n"
    "  - {id: band:high, range: [1792, 2304]}\n";
const char *LoweringSketchText =
    "format: 0\n"
    "heights:\n"
    "  points:\n"
    "    - {at: [40, 30], h: 480}\n"
    "    - {at: [40, 100], h: 2304}\n"
    "  bands:\n"
    "    - {band: band:low, polygon: [[0, 0], [128, 0], [128, 64], [0, 64]]}\n"
    "    - {band: band:high, polygon: [[0, 64], [128, 64], [128, 128], [0, 128]]}\n"
    "  cliffs:\n"
    "    - {line: [[0, 64], [50, 64], [90, 64], [128, 64]], drop: 1700, down: left}\n"
    "water:\n"
    "  bodies:\n"
    "    - {id: water:lake, kind: lake, level: 128, polygon: [[70, 20], [80, 20], [80, 30], [70, 30]]}\n"
    "points:\n"
    "  - {id: entrance:north, at: [100, 50], facing: s}\n";

LoweredOutdoorMap lowerTestSketch()
{
    const Project project = projectFromTexts({{"project.yml", LoweringCardText}, {"plan.yml", LoweringPlanText},
        {"sketch.yml", LoweringSketchText}});
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    const bool ok = lowerOutdoorProject(project, lowered, issues);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.file << ": " << issue.path << ": " << issue.message);
    }

    REQUIRE(ok);
    REQUIRE(lowered.samples.size() == 128u * 128u);
    return lowered;
}
}

TEST_CASE("an outdoor sketch lowers to heights: bands give the level, points win, a cliff stays a break")
{
    const LoweredOutdoorMap lowered = lowerTestSketch();
    const auto sample = [&lowered](int x, int y)
    {
        return static_cast<int>(lowered.samples[static_cast<size_t>(y) * 128 + x]);
    };
    // The height points, in steps of 32 units.
    CHECK(sample(40, 30) == 480 / 32);
    CHECK(sample(40, 100) == 2304 / 32);
    // Far from points and water, a band's middle: 256 in the low ground, 2048 in the high.
    CHECK(sample(120, 5) == 256 / 32);
    CHECK(sample(120, 120) == 2048 / 32);
    // The cliff: the node on the line is its top, the node one cell north its foot, with nothing smoothed between.
    CHECK(sample(120, 64) == 2048 / 32);
    CHECK(sample(120, 63) == 256 / 32);
    CHECK(sample(10, 64) - sample(10, 63) >= 1700 / 32);

    // Nothing leaks through the corners of the cliff's line (at x 50 and 90) or its ends.
    for (int x = 0; x < 128; ++x)
    {
        CHECK(sample(x, 64) >= 1792 / 32);
        CHECK(sample(x, 63) <= 512 / 32);
    }

    // Away from the cliff the land has no step a party could not walk: under a cell's width per cell.
    for (int y = 1; y < 63; ++y)
    {
        CHECK(std::abs(sample(40, y) - sample(40, y - 1)) * 32 < 512);
    }

    // The party stands at its arrival on the terrain, facing south.
    REQUIRE(lowered.start.has_value());
    CHECK(lowered.start->entrance == "entrance:north");
    CHECK(lowered.start->x == doctest::Approx((100 - 64) * 512.0));
    CHECK(lowered.start->y == doctest::Approx((64 - 50) * 512.0));
    CHECK(lowered.start->z == doctest::Approx(sample(100, 50) * 32.0));
    CHECK(lowered.start->facing == 1536);
}

TEST_CASE("water cells store the water's level, their ground lies below it, and the shore runs down to it")
{
    const LoweredOutdoorMap lowered = lowerTestSketch();
    CHECK(lowered.waterCells == 100);

    for (int y = 0; y < 128; ++y)
    {
        for (int x = 0; x < 128; ++x)
        {
            const size_t cell = static_cast<size_t>(y) * 128 + x;
            const bool inLake = x >= 70 && x < 80 && y >= 20 && y < 30;
            CHECK((lowered.water[cell] != 0) == inLake);

            if (!inLake)
            {
                continue;
            }

            CHECK(lowered.waterLevel[cell] == doctest::Approx(128.0));

            // The four corners: the surface is what the ODM stores, the ground is the bed under it.
            for (const size_t corner : {cell, cell + 1, cell + 128, cell + 129})
            {
                CHECK(lowered.samples[corner] == 128 / 32);
                CHECK(lowered.ground[corner] < 128.0);
            }
        }
    }

    // One cell from the lake the land has not climbed far; at a distance it is back at the band's level.
    CHECK(lowered.samples[static_cast<size_t>(25) * 128 + 82] <= 6);
    CHECK(lowered.samples[static_cast<size_t>(25) * 128 + 110] == 8);
}

TEST_CASE("lowering the same sketch twice gives the same land, and a height the format cannot hold is a warning")
{
    const LoweredOutdoorMap first = lowerTestSketch();
    const LoweredOutdoorMap second = lowerTestSketch();
    CHECK(first.samples == second.samples);
    CHECK(first.water == second.water);
    CHECK(first.ground == second.ground);
    CHECK(first.warnings == second.warnings);
    CHECK(first.warnings.empty());

    // 9000 is above what one byte of 32-unit steps holds (8160): stored as the highest, and said.
    std::string sketch = LoweringSketchText;
    const std::string point = "    - {at: [40, 100], h: 2304}\n";
    sketch.replace(sketch.find(point), point.size(), "    - {at: [40, 100], h: 9000}\n");
    const Project project = projectFromTexts({{"project.yml", LoweringCardText}, {"plan.yml", LoweringPlanText},
        {"sketch.yml", sketch}});
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(project, lowered, issues));
    CHECK(lowered.samples[static_cast<size_t>(100) * 128 + 40] == 255);
    CHECK(std::any_of(lowered.warnings.begin(), lowered.warnings.end(), [](const std::string &warning)
    {
        return warning.find("the most an ODM stores") != std::string::npos;
    }));
}

// `oymap compare` (core/Compare): rays, and two maps against each other.

#include "core/Compare.h"
#include "core/MapLoad.h"

namespace
{
// A one-room map built from project text and read back as the game reads its BLV. `eastWall`: the room's east side.
LoadedMap buildCompareTestMap(int eastWall, int floor = 0)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_compare_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    const std::string east = std::to_string(eastWall);
    std::ofstream(root / "project.yml", std::ios::binary) << CardText;
    std::ofstream(root / "rooms.yml", std::ios::binary) << std::string(ThemeText)
        + "rooms:\n  - {id: room:a, outline: [[0, 0], [" + east + ", 0], [" + east
        + ", 768], [0, 768]], floor: " + std::to_string(floor) + ", ceiling: " + std::to_string(floor + 384) + "}\n";
    std::ofstream(root / "objects.yml", std::ios::binary) << "format: 0\nstart: {room: room:a}\n";
    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(root, project, issues));
    BuildOptions options;
    options.outputDirectory = root / "build";
    BuildResult result;
    REQUIRE(buildProject(project, options, result));
    std::ifstream stream(root / "build" / "testmap.blv", std::ios::binary);
    const std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    LoadedMap map;
    map.world = "mm6";
    map.fileName = "testmap.blv";
    map.stem = "testmap";
    map.kind = MapKind::Indoor;
    map.indoor = OpenYAMM::Game::IndoorMapDataLoader().loadFromBytes(bytes);
    REQUIRE(map.indoor.has_value());
    std::filesystem::remove_all(root);
    return map;
}
}

TEST_CASE("a ray meets a square face at the right distance, misses beside it and does not see its back")
{
    RayScene scene;
    // A square of 100 by 100 at x = 100, seen from the side of the origin.
    REQUIRE(scene.addFace({{100.0, -50.0, -50.0}, {100.0, -50.0, 50.0}, {100.0, 50.0, 50.0}, {100.0, 50.0, -50.0}},
        {-1.0, 0.0, 0.0}, 7, "Stone"));
    CHECK_FALSE(scene.addFace({{0.0, 0.0, 0.0}, {1.0, 0.0, 0.0}, {2.0, 0.0, 0.0}}, {0.0, 0.0, 0.0}, 8, "line"));
    scene.build();
    const RayHit hit = scene.cast({0.0, 0.0, 0.0}, {1.0, 0.0, 0.0}, 4096.0);
    CHECK(hit.hit);
    CHECK(hit.distance == doctest::Approx(100.0));
    CHECK(hit.sourceId == 7);
    CHECK(hit.kind == SurfaceKind::Wall);
    CHECK(hit.texture == "stone");
    // Tilted past the square's top, and turned but still inside it.
    const RayHit slanted = scene.cast({0.0, 0.0, 0.0}, {0.8, 0.0, 0.6}, 4096.0);
    CHECK_FALSE(slanted.hit);
    const RayHit inside = scene.cast({0.0, 0.0, 0.0}, {0.96, 0.28, 0.0}, 4096.0);
    CHECK(inside.hit);
    CHECK(inside.distance == doctest::Approx(100.0 / 0.96));
    const RayHit beside = scene.cast({0.0, 60.0, 0.0}, {1.0, 0.0, 0.0}, 4096.0);
    CHECK_FALSE(beside.hit);
    CHECK(beside.distance == doctest::Approx(4096.0));
    CHECK_FALSE(scene.cast({200.0, 0.0, 0.0}, {-1.0, 0.0, 0.0}, 4096.0).hit);
    CHECK_FALSE(scene.cast({0.0, 0.0, 0.0}, {1.0, 0.0, 0.0}, 50.0).hit);

    // An outline that is not convex: an L, met in its arms and missed in its notch.
    RayScene bent;
    REQUIRE(bent.addFace({{0.0, 0.0, 0.0}, {200.0, 0.0, 0.0}, {200.0, 100.0, 0.0}, {100.0, 100.0, 0.0},
        {100.0, 200.0, 0.0}, {0.0, 200.0, 0.0}}, {0.0, 0.0, 1.0}, 1, "floor"));
    bent.build();
    CHECK(bent.cast({150.0, 50.0, 64.0}, {0.0, 0.0, -1.0}, 4096.0).distance == doctest::Approx(64.0));
    CHECK(bent.cast({50.0, 150.0, 64.0}, {0.0, 0.0, -1.0}, 4096.0).kind == SurfaceKind::Floor);
    CHECK_FALSE(bent.cast({150.0, 150.0, 64.0}, {0.0, 0.0, -1.0}, 4096.0).hit);
    CHECK(bent.heightsAt(50.0, 150.0).size() == 1);
    CHECK(bent.heightsAt(150.0, 150.0).empty());
}

TEST_CASE("two maps built from one project text are 100 % alike")
{
    const LoadedMap first = buildCompareTestMap(1024);
    const LoadedMap second = buildCompareTestMap(1024);
    CompareOptions options;
    options.step = 128.0;
    CompareResult result;
    std::string errorMessage;
    REQUIRE(compareMaps(first, second, options, result, errorMessage));
    CHECK(result.points.size() >= 20);
    CHECK(result.missingFloor.empty());
    CHECK(result.extraFloor.empty());
    CHECK(result.distanceShare == doctest::Approx(1.0));
    CHECK(result.textureShare == doctest::Approx(1.0));
    CHECK(result.score == doctest::Approx(1.0));
    CHECK(result.meanFloorDelta == doctest::Approx(0.0));
    CHECK(result.meanCeilingDelta == doctest::Approx(0.0));
    REQUIRE_FALSE(result.worst.empty());
    CHECK(result.points[result.worst.front()].sentence == "agrees");
    CHECK(result.verticalOffset == doctest::Approx(0.0));
    JsonWriter writer(true);
    writeCompareJson(result, writer);
    CHECK(writer.text().find("\"score\": 1") != std::string::npos);

    // The same room drawn 320 lower is the same room, and the report says how much lower it lies.
    const LoadedMap lower = buildCompareTestMap(1024, -320);
    CompareResult shifted;
    REQUIRE(compareMaps(first, lower, options, shifted, errorMessage));
    CHECK(shifted.verticalOffset == doctest::Approx(-320.0));
    CHECK(shifted.missingFloor.empty());
    CHECK(shifted.score == doctest::Approx(1.0));
    CHECK(shifted.meanFloorDelta == doctest::Approx(0.0));
    CHECK(shifted.meanCeilingDelta == doctest::Approx(0.0));
}

TEST_CASE("a wall moved by 128 units is found, on the side it moved to")
{
    const LoadedMap original = buildCompareTestMap(1024);
    // The east wall stands 128 nearer in the rebuild.
    const LoadedMap rebuilt = buildCompareTestMap(896);
    CompareOptions options;
    options.step = 128.0;
    CompareResult result;
    std::string errorMessage;
    REQUIRE(compareMaps(original, rebuilt, options, result, errorMessage));
    CHECK(result.distanceShare < 0.95);
    CHECK(result.distanceShare > 0.5);
    // The strip the wall moved over has a floor in the original only.
    CHECK_FALSE(result.missingFloor.empty());
    CHECK(result.extraFloor.empty());

    for (const size_t index : result.missingFloor)
    {
        CHECK(result.points[index].x >= 896.0);
    }

    REQUIRE_FALSE(result.worst.empty());
    size_t named = 0;

    for (const size_t index : result.worst)
    {
        const ComparePoint &point = result.points[index];
        CHECK(point.sentence.find("west") == std::string::npos);
        CHECK(point.sentence.find("farther") == std::string::npos);

        if (point.sentence.find("the rebuild's wall to the east is") != std::string::npos
            && point.sentence.find("nearer") != std::string::npos)
        {
            ++named;
            // East is yaw 0: the shot looks at the wall that moved.
            CHECK(std::cos(point.worstYaw) > 0.7);
        }
    }

    CHECK(named == result.worst.size());

    // The other way round the wall is farther and the rebuild has floor the original lacks.
    CompareResult reverse;
    REQUIRE(compareMaps(rebuilt, original, options, reverse, errorMessage));
    CHECK(reverse.missingFloor.empty());
    CHECK_FALSE(reverse.extraFloor.empty());
    CHECK(reverse.points[reverse.worst.front()].sentence.find("farther to the east") != std::string::npos);
    CHECK_FALSE(compareShotsYaml(reverse).empty());
}

// Room shapes added on 2026-11-12: sloped ceilings, ceiling levels that narrow, raking beams, openings one above the
// other, holes in floors. Each is built all the way to a BLV, so the indoor compiler has accepted every face.

namespace
{
struct BuiltRooms
{
    bool built = false;
    std::vector<ProjectIssue> issues;
    OpenYAMM::Game::IndoorMapData map;

    // The lowest and highest point of a face.
    std::array<int, 2> heights(const OpenYAMM::Game::IndoorFace &face) const
    {
        std::array<int, 2> range = {map.vertices[face.vertexIndices[0]].z, map.vertices[face.vertexIndices[0]].z};

        for (const uint16_t vertex : face.vertexIndices)
        {
            range[0] = std::min<int>(range[0], map.vertices[vertex].z);
            range[1] = std::max<int>(range[1], map.vertices[vertex].z);
        }

        return range;
    }

    // Whether a face (seen from above) holds a point; faces are convex.
    bool holds(const OpenYAMM::Game::IndoorFace &face, double x, double y) const
    {
        bool left = false;
        bool right = false;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const OpenYAMM::Game::IndoorVertex &a = map.vertices[face.vertexIndices[index]];
            const OpenYAMM::Game::IndoorVertex &b =
                map.vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            const double side = (b.x - a.x) * (y - a.y) - (b.y - a.y) * (x - a.x);
            left = left || side > 1.0e-6;
            right = right || side < -1.0e-6;
        }

        return !(left && right);
    }

    // The heights at which level or sloping faces of one sector lie over a point: floors (`up`) or ceilings.
    std::vector<int> levelsOver(int sector, double x, double y, bool up) const
    {
        std::vector<int> found;

        for (const OpenYAMM::Game::IndoorFace &face : map.faces)
        {
            const bool isFloor = face.facetType == 3 || face.facetType == 4;
            const bool isCeiling = face.facetType == 5 || face.facetType == 6;

            if (!face.isPortal && face.roomNumber == sector && (up ? isFloor : isCeiling) && holds(face, x, y))
            {
                found.push_back(heights(face)[up ? 1 : 0]);
            }
        }

        std::sort(found.begin(), found.end());
        return found;
    }

    bool hasVertex(int x, int y, int z) const
    {
        return std::any_of(map.vertices.begin(), map.vertices.end(), [x, y, z](const OpenYAMM::Game::IndoorVertex &v)
        {
            return v.x == x && v.y == y && v.z == z;
        });
    }
};

// Rooms text (after the themes) and objects text built to a BLV and read back.
BuiltRooms buildRooms(const std::string &rooms, const std::string &objects = "format: 0\nstart: {room: room:a}\n")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_shapes_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    std::ofstream(root / "project.yml", std::ios::binary) << CardText;
    std::ofstream(root / "rooms.yml", std::ios::binary) << std::string(ThemeText) + rooms;
    std::ofstream(root / "objects.yml", std::ios::binary) << objects;
    BuiltRooms built;
    Project project;

    if (loadProject(root, project, built.issues))
    {
        BuildOptions options;
        options.outputDirectory = root / "build";
        BuildResult result;
        built.built = buildProject(project, options, result);
        built.issues = result.issues;

        if (built.built)
        {
            std::ifstream stream(root / "build" / "testmap.blv", std::ios::binary);
            const std::vector<uint8_t> bytes(
                (std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
            const std::optional<OpenYAMM::Game::IndoorMapData> map =
                OpenYAMM::Game::IndoorMapDataLoader().loadFromBytes(bytes);
            built.built = map.has_value();

            if (map)
            {
                built.map = *map;
            }
        }
    }

    std::filesystem::remove_all(root);
    return built;
}

std::string issueText(const BuiltRooms &built)
{
    std::string text;

    for (const ProjectIssue &issue : built.issues)
    {
        text += issue.path + ": " + issue.message + "\n";
    }

    return text;
}
}

TEST_CASE("a sloped ceiling is one plane, the walls rake up to it, and openings and lights take its height there")
{
    // A lean-to over a level room (512 at the west wall down to 256 at the east), with a pillar and a doorway in the
    // north wall, along which the ceiling rakes; and a ramp whose ceiling runs parallel to its floor.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 512,\n"
        "     ceiling_slope: {to: 256, toward: east}, pillars: [{at: [256, 256], size: [64, 64]}]}\n"
        "  - {id: room:b, outline: [[128, 576], [384, 576], [384, 832], [128, 832]], floor: 0, ceiling: 512}\n"
        "  - {id: room:c, outline: [[576, 128], [1088, 128], [1088, 384], [576, 384]], floor: 0, ceiling: 256,\n"
        "     slope: {to: 256, toward: east}, ceiling_slope: {to: 512, toward: east}}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n"
        "  - {id: open:ac, from: room:a, to: room:c, width: 128, height: 224}\n";
    const BuiltRooms built = buildRooms(rooms,
        "format: 0\nstart: {room: room:a, at: [64, 64]}\nlights:\n  - {id: light:east, room: room:a, at: [448, 64]}\n");
    INFO(issueText(built));
    REQUIRE(built.built);
    // The ceiling over three places of the lean-to, and the walls' top corners.
    CHECK_FALSE(built.levelsOver(1, 64, 64, false).empty());
    CHECK(built.hasVertex(0, 0, 512));
    CHECK(built.hasVertex(512, 0, 256));
    CHECK(built.hasVertex(512, 512, 256));
    // The doorway's sides in the raking north wall end the wall pieces at the ceiling's height there.
    CHECK(built.hasVertex(192, 512, 416));
    CHECK(built.hasVertex(320, 512, 352));
    // The pillar ends at the ceiling over each of its corners.
    CHECK(built.hasVertex(224, 224, 400));
    CHECK(built.hasVertex(288, 288, 368));
    CHECK_FALSE(built.hasVertex(224, 224, 512));
    // The ramp's ceiling is 256 above its floor at both ends.
    CHECK(built.hasVertex(576, 128, 256));
    CHECK(built.hasVertex(1088, 128, 512));
    CHECK(built.levelsOver(3, 832, 256, true).size() == 1);
    CHECK(built.levelsOver(3, 832, 256, false).size() == 1);
    // A light without a height hangs three quarters up under the ceiling over it (288 at x 448).
    REQUIRE(built.map.lights.size() == 1);
    CHECK(built.map.lights[0].z == 216);

    const auto refused = [&rooms](const std::string &from, const std::string &to)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = buildRooms(changed);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    // The north doorway may reach only as high as the ceiling at its lower side (352).
    CHECK(refused("to: room:b, width: 128, height: 256", "to: room:b, width: 128, height: 368")
        .find("lower ceiling of its two rooms is at 352 there (a sloped ceiling)") != std::string::npos);
    CHECK(refused("ceiling_slope: {to: 256, toward: east}", "ceiling_slope: {to: 8, toward: east}")
        .find("within 16 units of the floor") != std::string::npos);
    CHECK(refused("ceiling: 512,\n     ceiling_slope: {to: 256, toward: east}",
        "ceiling: 1536,\n     ceiling_slope: {to: 256, toward: east}").find("steeper than a ceiling can be")
        != std::string::npos);
    CHECK(refused("floor: 0, ceiling: 512,", "floor: 0, ceiling: 512, bands: [{height: 300, surface: {texture: band, "
        "size: [64, 64]}}],").find("every wall band must end at or below") != std::string::npos);

    // A room that is not a rectangle: its corners stand at heights between whole units, and the ceiling is then cut
    // into triangles the map can hold.
    const BuiltRooms bent = buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [500, 0], [700, 300], [300, 700], [0, 400]], floor: 0, ceiling: 300,\n"
        "     ceiling_slope: {to: 517, toward: 2}}\n");
    INFO(issueText(bent));
    REQUIRE(bent.built);
    CHECK(bent.levelsOver(1, 300, 300, false).size() == 1);
}

TEST_CASE("a ceiling level narrows to a point, a ridge or a smaller top, alone or as the room's whole ceiling")
{
    // A pyramid over the whole of room a (with a doorway, whose sides the roof's foot must meet), a hipped ceiling
    // over the whole of room b, and in room c a level with leaning sides and four raking ribs.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 256,\n"
        "     ceiling_levels: [{ceiling: 512, top_scale: 0}]}\n"
        "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 256], [576, 256]], floor: 0, ceiling: 256,\n"
        "     ceiling_levels: [{ceiling: 384, top_outline: [[704, 128], [960, 128], [960, 128], [704, 128]]}]}\n"
        "  - id: room:c\n"
        "    outline: [[0, 576], [512, 576], [512, 1088], [0, 1088]]\n"
        "    floor: 0\n"
        "    ceiling: 256\n"
        "    ceiling_levels:\n"
        "      - {outline: [[128, 704], [384, 704], [384, 960], [128, 960]], ceiling: 512, top_scale: 0.5}\n"
        "    beams:\n"
        "      - {path: [[128, 832], [192, 832]], width: 32, depth: 32, bottom: 224, bottom_end: 480}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n"
        "  - {id: open:ac, from: room:a, to: room:c, width: 128, height: 192}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    // The pyramid: its point, no level ceiling left, and a foot that has the doorway's sides as corners.
    CHECK(built.hasVertex(256, 256, 512));
    CHECK(built.levelsOver(1, 64, 256, false) == std::vector<int>{256});
    size_t pyramidSides = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        const std::array<int, 2> range = built.heights(face);

        if (face.roomNumber == 1 && range[0] == 256 && range[1] == 512)
        {
            ++pyramidSides;
            // The east and north sides have a doorway under them: three corners and the doorway's two sides.
            CHECK((face.vertexIndices.size() == 3 || face.vertexIndices.size() == 5));
        }

        CHECK_FALSE((face.roomNumber == 1 && range[0] == 256 && range[1] == 256));
    }

    CHECK(pyramidSides == 4);
    // The hipped ceiling: a ridge, two trapezoids and two triangles.
    CHECK(built.hasVertex(704, 128, 384));
    CHECK(built.hasVertex(960, 128, 384));
    CHECK(built.levelsOver(2, 832, 64, false).size() == 1);
    // The leaning level: a flat top half as wide, the room's ceiling round it, and the rib from 224 up to 512.
    CHECK(built.levelsOver(3, 256, 832, false) == std::vector<int>{512});
    const std::vector<int> beside = built.levelsOver(3, 50, 600, false);
    REQUIRE_FALSE(beside.empty());
    CHECK(beside.front() == 256);
    CHECK(beside.back() == 256);
    CHECK(built.hasVertex(192, 768, 512));
    CHECK(built.hasVertex(128, 816, 224));
    CHECK(built.hasVertex(192, 848, 512));

    const auto refused = [&rooms](const std::string &from, const std::string &to)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = buildRooms(changed);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    CHECK(refused("top_outline: [[704, 128], [960, 128], [960, 128], [704, 128]]",
        "top_outline: [[704, 128], [960, 128], [704, 128]]").find("one point for each point") != std::string::npos);
    CHECK(refused("top_outline: [[704, 128], [960, 128], [960, 128], [704, 128]]",
        "top_outline: [[704, 128], [1200, 128], [1200, 128], [704, 128]]").find("inside the outline or on it")
        != std::string::npos);
    CHECK(refused("{ceiling: 512, top_scale: 0}", "{ceiling: 512, top_scale: 0, top_outline: [[1, 1], [2, 1], [2, 2], "
        "[1, 2]]}").find("not both") != std::string::npos);
    CHECK(refused("ceiling_levels: [{ceiling: 512, top_scale: 0}]", "ceiling_levels: [{ceiling: 512, top_scale: 0}], "
        "pillars: [{at: [128, 128], size: [64, 64]}]").find("the room's whole ceiling") != std::string::npos);
    CHECK(refused("path: [[128, 832], [192, 832]]", "path: [[128, 832], [192, 832], [192, 900]]")
        .find("exactly two") != std::string::npos);
    CHECK(refused("outline: [[128, 704], [384, 704], [384, 960], [128, 960]]",
        "outline: [[128, 704], [384, 704], [256, 832], [384, 960], [128, 960]]").find("needs a convex outline")
        != std::string::npos);
}

TEST_CASE("two openings stand one above the other in one wall, with the wall between them built")
{
    // A tall room with a low room and, over it, a high room on its east side: a doorway into each, one above the
    // other.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 768}\n"
        "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 288}\n"
        "  - {id: room:c, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 320, ceiling: 768}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 224}\n"
        "  - {id: open:ac, from: room:a, to: room:c, width: 192, height: 256, shape: gable, apex: 320}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    size_t portals = 0;
    size_t between = 0;
    size_t above = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        portals += face.isPortal ? 1 : 0;
        const std::array<int, 2> range = built.heights(face);
        bool inEastWall = face.roomNumber == 1 && !face.isPortal;

        for (const uint16_t vertex : face.vertexIndices)
        {
            inEastWall = inEastWall && built.map.vertices[vertex].x == 512;
        }

        // The wall between the lower doorway's top (224) and the upper one's sill (320), and over the gable.
        between += inEastWall && range[0] == 224 && range[1] == 320 ? 1 : 0;
        above += inEastWall && range[0] >= 576 && range[1] == 768 ? 1 : 0;
    }

    CHECK(portals == 2);
    // Each is cut under the gable's point, and over the gable also at the lower doorway's sides.
    CHECK(between == 2);
    CHECK(above == 4);
    // The upper doorway is wider: beside the lower one the wall runs from the floor to its sill in one face.
    CHECK(built.hasVertex(512, 160, 320));
    CHECK(built.hasVertex(512, 192, 224));

    const auto refused = [](const std::string &text)
    {
        const BuiltRooms result = buildRooms(text);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    // Less than 16 units of wall between the two.
    std::string close = rooms;
    close.replace(close.find("height: 224"), 11, "height: 310");
    close.replace(close.find("ceiling: 288"), 12, "ceiling: 312");
    CHECK(refused(close).find("one above the other, 16 units between the lower one's top and the upper one's sill: "
        "here 310 and 320") != std::string::npos);
    // An opening in a wall still needs its width and height.
    std::string bare = rooms;
    bare.replace(bare.find("width: 128, height: 224"), 23, "sill: 0");
    CHECK(refused(bare).find("an opening in a wall needs `width` and `height`") != std::string::npos);
}

TEST_CASE("a hole in a floor opens onto the room below, and a stair room may be open to the room above it")
{
    // An upper room over a lower room 32 under its floor, joined by a hole; and a stair room under the upper room
    // whose whole ceiling is a hole in that floor.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]], floor: 256, ceiling: 640}\n"
        "  - {id: room:b, outline: [[64, 64], [448, 64], [448, 704], [64, 704]], floor: -64, ceiling: 224}\n"
        "  - {id: room:c, outline: [[576, 128], [832, 128], [832, 640], [576, 640]], floor: 0, ceiling: 256,\n"
        "     slope: {to: 256, toward: north, steps: 8}}\n"
        "  - {id: room:d, outline: [[576, -256], [832, -256], [832, 64], [576, 64]], floor: 0, ceiling: 224}\n"
        "openings:\n"
        "  - {id: open:hole, from: room:a, to: room:b, in: floor, at: [256, 384], size: [192, 256]}\n"
        "  - {id: open:well, from: room:a, to: room:c, in: floor}\n"
        "  - {id: open:foot, from: room:d, to: room:c, width: 128, height: 192}\n";
    const BuiltRooms built = buildRooms(rooms, "format: 0\nstart: {room: room:a, at: [512, 64]}\n");
    INFO(issueText(built));
    REQUIRE(built.built);
    // The upper floor has the hole and the stairwell cut out of it, the lower ceiling the hole.
    CHECK(built.levelsOver(1, 512, 384, true) == std::vector<int>{256});
    CHECK(built.levelsOver(1, 256, 384, true).empty());
    CHECK(built.levelsOver(1, 704, 384, true).empty());
    CHECK(built.levelsOver(2, 100, 100, false) == std::vector<int>{224});
    CHECK(built.levelsOver(2, 256, 384, false).empty());
    // The stair room has its treads and no ceiling at all.
    CHECK(built.levelsOver(3, 704, 400, true) == std::vector<int>{128});
    CHECK(built.levelsOver(3, 704, 400, false).empty());
    CHECK(built.levelsOver(3, 704, 600, true) == std::vector<int>{224});
    size_t floorPortals = 0;
    size_t shaftSides = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        const std::array<int, 2> range = built.heights(face);

        if (face.isPortal && range[0] == range[1])
        {
            ++floorPortals;
            // Level, facing up, at the lower room's ceiling, with the upper room in front.
            CHECK(face.facetType == 3);
            CHECK(face.roomNumber == 1);
            CHECK((range[0] == 224 || range[0] == 256));
            CHECK(built.holds(face, range[0] == 224 ? 256 : 704, 384));
        }

        shaftSides += !face.isPortal && face.roomNumber == 1 && range[0] == 224 && range[1] == 256 ? 1 : 0;
    }

    CHECK(floorPortals == 2);
    // The hole's four sides through the 32 units of floor; the stairwell's floor has no thickness.
    CHECK(shaftSides == 4);
    // The upper room's sector is told that portals lie in its floor.
    CHECK((built.map.sectors[1].flags & 0x8) != 0);
    CHECK((built.map.sectors[2].flags & 0x8) == 0);

    const auto refused = [&rooms](const std::string &from, const std::string &to, const std::string &objects)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = buildRooms(changed, objects);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    const std::string start = "format: 0\nstart: {room: room:a, at: [512, 64]}\n";
    CHECK(refused("from: room:a, to: room:b, in: floor", "from: room:b, to: room:a, in: floor", start)
        .find("swap `from` and `to`") != std::string::npos);
    CHECK(refused("at: [256, 384], size: [192, 256]", "at: [440, 384], size: [192, 256]", start)
        .find("at least 16 units from its walls") != std::string::npos);
    CHECK(refused("at: [256, 384], size: [192, 256]", "at: [256, 384], size: [192, 256], width: 64", start)
        .find("takes `outline`, or `at` and `size`") != std::string::npos);
    CHECK(refused("at: [256, 384], size: [192, 256]",
        "outline: [[160, 256], [352, 256], [256, 384], [352, 512], [160, 512]]", start)
        .find("must be convex") != std::string::npos);
    CHECK(refused("floor: -64, ceiling: 224}", "floor: -64, ceiling: 224, ceiling_levels: [{ceiling: 240}]}", start)
        .find("cannot take this hole") != std::string::npos);
    CHECK(refused("floor: 256, ceiling: 640}", "floor: 256, ceiling: 640, platforms: [{at: [256, 384], size: [128, "
        "128], rise: 32}]}", start).find("under a level, a platform or a flight") != std::string::npos);
    CHECK(refused("in: floor}", "in: floor}", start + "doors:\n  - {id: door:hatch, opening: open:well}\n")
        .find("a trapdoor turns on one side of its hole") != std::string::npos);
    // A stairwell (the lower room's whole ceiling) is no rectangle a leaf can fill.
    CHECK(refused("in: floor}", "in: floor}", start + "doors:\n  - {id: door:hatch, opening: open:well, hinge: west}\n")
        .find("rectangular hole") != std::string::npos);
}

TEST_CASE("the bridge to a hole keeps off the place of a hole that is cut after it")
{
    const std::vector<Point2> room = {{0, 0}, {1000, 0}, {1000, 1000}, {0, 1000}};
    // The first hole's nearest corner of the room is [0, 0], and the second hole lies on the way there.
    const std::vector<Point2> first = {{400, 400}, {500, 400}, {500, 500}, {400, 500}};
    const std::vector<Point2> second = {{150, 150}, {250, 150}, {250, 250}, {150, 250}};
    const auto floorArea = [](const std::vector<Point2> &ring)
    {
        double area = 0.0;

        for (const std::vector<size_t> &piece : convexPieces(ring, 20))
        {
            std::vector<Point2> points;

            for (const size_t index : piece)
            {
                points.push_back(ring[index]);
            }

            area += polygonDoubleArea(points) / 2.0;
        }

        return area;
    };
    // Cut blind, the first bridge runs through the second hole's place and that hole can no longer be cut.
    const std::vector<Point2> blind = cutHole(room, first);
    CHECK(floorArea(blind) == doctest::Approx(990000.0));
    CHECK(floorArea(cutHole(blind, second)) == doctest::Approx(0.0));
    // Told of the hole to come, it takes another way and both are cut.
    const std::vector<Point2> aware = cutHole(room, first, {second});
    CHECK(floorArea(aware) == doctest::Approx(990000.0));
    CHECK(floorArea(cutHole(aware, second)) == doctest::Approx(980000.0));
}

#include <set>

namespace
{
struct BuiltTriggers
{
    BuiltRooms rooms;
    std::string lua;

    // The faces of a sector that are floor over a point.
    std::vector<const OpenYAMM::Game::IndoorFace *> floorsOver(int sector, double x, double y) const
    {
        std::vector<const OpenYAMM::Game::IndoorFace *> found;

        for (const OpenYAMM::Game::IndoorFace &face : rooms.map.faces)
        {
            if (!face.isPortal && face.roomNumber == sector && (face.facetType == 3 || face.facetType == 4)
                && rooms.holds(face, x, y))
            {
                found.push_back(&face);
            }
        }

        return found;
    }
};

// Rooms (after the themes), objects and wiring built to a BLV and its script, both read back.
BuiltTriggers buildTriggers(const std::string &rooms, const std::string &objects, const std::string &wiring)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_triggers_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    std::ofstream(root / "project.yml", std::ios::binary) << CardText;
    std::ofstream(root / "rooms.yml", std::ios::binary) << std::string(ThemeText) + rooms;
    std::ofstream(root / "objects.yml", std::ios::binary) << objects;
    std::ofstream(root / "wiring.yml", std::ios::binary) << wiring;
    BuiltTriggers built;
    Project project;

    if (loadProject(root, project, built.rooms.issues))
    {
        BuildOptions options;
        options.outputDirectory = root / "build";
        BuildResult result;
        built.rooms.built = buildProject(project, options, result);
        built.rooms.issues = result.issues;

        if (built.rooms.built)
        {
            std::ifstream stream(root / "build" / "testmap.blv", std::ios::binary);
            const std::vector<uint8_t> bytes(
                (std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
            const std::optional<OpenYAMM::Game::IndoorMapData> map =
                OpenYAMM::Game::IndoorMapDataLoader().loadFromBytes(bytes);
            built.rooms.built = map.has_value();

            if (map)
            {
                built.rooms.map = *map;
            }

            std::ifstream luaStream(root / "build" / "testmap.lua", std::ios::binary);
            built.lua.assign((std::istreambuf_iterator<char>(luaStream)), std::istreambuf_iterator<char>());
        }
    }

    std::filesystem::remove_all(root);
    return built;
}

const uint32_t StepFlags = 0x04000000u | 0x00080000u;
const uint32_t ClickFlag = 0x02000000u;
const uint32_t LavaFlag = 0x40000000u;

const char *const TriggerRooms =
    "rooms:\n"
    "  - id: room:a\n"
    "    outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]]\n"
    "    floor: 0\n"
    "    ceiling: 384\n"
    "    platforms:\n"
    "      - {id: platform:dais, at: [832, 160], size: [128, 128], rise: 16}\n"
    "    levels:\n"
    "      - {id: level:pit, outline: [[96, 96], [288, 96], [288, 288], [96, 288]], floor: -32}\n"
    "      - {id: level:stage, outline: [[96, 480], [288, 480], [288, 672], [96, 672]], floor: 32}\n"
    "  - {id: room:b, outline: [[1088, 256], [1344, 256], [1344, 512], [1088, 512]], floor: 0, ceiling: 256}\n"
    "openings:\n"
    "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n";

const char *const TriggerObjects =
    "format: 0\n"
    "start: {room: room:a, at: [512, 64]}\n"
    "doors:\n"
    "  - {id: door:ab, opening: open:ab}\n"
    "plates:\n"
    "  - {id: plate:flat, room: room:a, at: [512, 384], size: [128, 128]}\n"
    "  - {id: plate:raised, room: room:a, outline: [[640, 544], [768, 544], [704, 672]], rise: 8}\n"
    "floors:\n"
    "  - {id: floor:pit, of: level:pit, kind: lava}\n"
    "  - {id: floor:b, of: room:b, kind: lava}\n";
}

TEST_CASE("a plate, a room's floor, a level and a platform run step events; a floor marked lava burns")
{
    const std::string wiring =
        "format: 0\n"
        "events:\n"
        "  - {id: evt:e1_flat, preset: switch, trigger: step, source: plate:flat, opens: [door:ab], once: true}\n"
        "  - {id: evt:e2_floor, preset: text, trigger: step, source: room:a, sources: [plate:raised], text: Floor.}\n"
        "  - {id: evt:e3_pit, preset: text, trigger: step, source: level:pit, text: Pit.}\n"
        "  - {id: evt:e4_stage, preset: text, trigger: step, source: level:stage, text: Stage.}\n"
        "  - {id: evt:e5_dais, preset: text, trigger: step, source: platform:dais, text: Dais.}\n";
    const BuiltTriggers built = buildTriggers(TriggerRooms, TriggerObjects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // Each floor is one face over its point: the plate is cut into the room's floor, not laid on it.
    const auto only = [&built](int sector, double x, double y)
    {
        const std::vector<const OpenYAMM::Game::IndoorFace *> faces = built.floorsOver(sector, x, y);
        REQUIRE(faces.size() == 1);
        return faces[0];
    };
    const OpenYAMM::Game::IndoorFace *pFlat = only(1, 512, 384);
    CHECK(pFlat->cogTriggered == 1);
    CHECK((pFlat->attributes & StepFlags) == StepFlags);
    CHECK((pFlat->attributes & ClickFlag) == 0);
    CHECK(built.rooms.heights(*pFlat) == std::array<int, 2>{0, 0});
    // The raised plate (a triangle 8 high) runs the room floor's event through `sources`.
    const OpenYAMM::Game::IndoorFace *pRaised = only(1, 704, 580);
    CHECK(pRaised->cogTriggered == 2);
    CHECK(built.rooms.heights(*pRaised) == std::array<int, 2>{8, 8});
    CHECK(pRaised->vertexIndices.size() == 3);
    const OpenYAMM::Game::IndoorFace *pFloor = only(1, 512, 700);
    CHECK(pFloor->cogTriggered == 2);
    CHECK((pFloor->attributes & (StepFlags | LavaFlag)) == StepFlags);
    // The sunken level runs its own event and burns; the raised level and the platform run theirs.
    const OpenYAMM::Game::IndoorFace *pPit = only(1, 192, 192);
    CHECK(pPit->cogTriggered == 3);
    CHECK((pPit->attributes & (StepFlags | LavaFlag)) == (StepFlags | LavaFlag));
    CHECK(built.rooms.heights(*pPit) == std::array<int, 2>{-32, -32});
    const OpenYAMM::Game::IndoorFace *pStage = only(1, 192, 576);
    CHECK(pStage->cogTriggered == 4);
    CHECK(built.rooms.heights(*pStage) == std::array<int, 2>{32, 32});
    // A platform stands on the room's floor: its top runs its event, the floor shut in under it the floor's.
    const std::vector<const OpenYAMM::Game::IndoorFace *> atDais = built.floorsOver(1, 832, 160);
    REQUIRE(atDais.size() == 2);
    const bool topFirst = built.rooms.heights(*atDais[0])[0] == 16;
    const OpenYAMM::Game::IndoorFace *pDais = atDais[topFirst ? 0 : 1];
    CHECK(pDais->cogTriggered == 5);
    CHECK(built.rooms.heights(*pDais) == std::array<int, 2>{16, 16});
    CHECK(atDais[topFirst ? 1 : 0]->cogTriggered == 2);
    // A floor that only burns has the lava flag, no event and no step or click flag.
    const OpenYAMM::Game::IndoorFace *pLava = only(2, 1216, 384);
    CHECK(pLava->cogTriggered == 0);
    CHECK((pLava->attributes & (StepFlags | ClickFlag | LavaFlag)) == LavaFlag);

    // Nothing but floors runs a step event, and every face of an event runs by step.
    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        if (face.cogTriggered != 0)
        {
            CHECK((face.attributes & StepFlags) == StepFlags);
            CHECK((face.attributes & ClickFlag) == 0);
        }
    }

    // `once` keeps a map variable; the door opens before it is set.
    CHECK(built.lua.find("RegisterEvent(1, nil, function()\n    if IsAtLeast(MapVar(0), 1) then\n        return\n"
        "    end\n    evt.SetDoorState(1, DoorAction.Open)\n    SetValue(MapVar(0), 1)\nend, nil)")
        != std::string::npos);
    CHECK(built.lua.find("SetMapMetadata({onLoad = {}, onLeave = {}, openedChestIds = {}})\n") != std::string::npos);
}

TEST_CASE("DD-11B: a room's step event runs on its low platforms that run none of their own, not on high ones")
{
    // A7's clay drop: the party lands on a heap in the room and the room's landing line must run. The named dais (16)
    // and an unnamed platform (24) take the room's; a platform higher than a step (64) and one that hangs (`base`) do
    // not (a sky map's clouds, XD-12's balcony over the fall); the stage runs its own event.
    const std::string rooms = std::string(TriggerRooms).replace(std::string(TriggerRooms).find("    levels:\n"), 0,
        "      - {at: [640, 384], size: [128, 128], rise: 24}\n"
        "      - {at: [640, 160], size: [96, 96], rise: 64}\n"
        "      - {at: [512, 576], size: [96, 96], rise: 16, base: 96}\n");
    const std::string wiring =
        "format: 0\n"
        "events:\n"
        "  - {id: evt:e1_room, preset: text, trigger: step, source: room:a, text: Landed.}\n"
        "  - {id: evt:e2_stage, preset: text, trigger: step, source: level:stage, text: Stage.}\n";
    const BuiltTriggers built = buildTriggers(rooms,
        "format: 0\nstart: {room: room:a, at: [512, 64]}\nfloors:\n  - {id: floor:pit, of: level:pit, kind: lava}\n",
        wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    const auto topAt = [&built](double x, double y, int height)
    {
        const OpenYAMM::Game::IndoorFace *pTop = nullptr;

        for (const OpenYAMM::Game::IndoorFace *pFace : built.floorsOver(1, x, y))
        {
            if (built.rooms.heights(*pFace)[0] == height)
            {
                pTop = pFace;
            }
        }

        REQUIRE(pTop != nullptr);
        return pTop;
    };
    CHECK(topAt(512, 700, 0)->cogTriggered == 1);
    const OpenYAMM::Game::IndoorFace *pDais = topAt(832, 160, 16);
    CHECK(pDais->cogTriggered == 1);
    CHECK((pDais->attributes & (StepFlags | LavaFlag)) == StepFlags);
    CHECK(topAt(640, 384, 24)->cogTriggered == 1);
    CHECK(topAt(640, 160, 64)->cogTriggered == 0);
    CHECK(topAt(512, 576, 112)->cogTriggered == 0);
    CHECK(topAt(192, 576, 32)->cogTriggered == 2);
    // A level is a place of its own: the pit burns and runs nothing.
    const OpenYAMM::Game::IndoorFace *pPit = topAt(192, 192, -32);
    CHECK(pPit->cogTriggered == 0);
    CHECK((pPit->attributes & (StepFlags | LavaFlag)) == LavaFlag);
    // The room's floor itself does not burn.
    CHECK((topAt(512, 700, 0)->attributes & LavaFlag) == 0);
}

TEST_CASE("timer and load events are written as the shipped scripts declare them, with the new effects")
{
    const std::string wiring =
        "format: 0\n"
        "variables: [on_lava]\n"
        "events:\n"
        "  - {id: evt:e1_load, preset: script, trigger: load, effects: [{set: {var: {map_var: on_lava}, value: 0}}]}\n"
        "  - id: evt:e2_burn\n"
        "    preset: script\n"
        "    trigger: timer\n"
        "    every: 2\n"
        "    condition: {map_var: on_lava}\n"
        "    effects:\n"
        "      - damage: {amount: 25, kind: fire}\n"
        "      - damage: 4\n"
        "      - damage: {amount: 1, kind: magic, who: current}\n"
        "  - id: evt:e3_bolt\n"
        "    preset: script\n"
        "    trigger: timer\n"
        "    every: 5\n"
        "    once: true\n"
        "    effects:\n"
        "      - cast: {spell: 2, from: [64, 64, 96], to: [960, 64, 96], mastery: expert}\n"
        "      - summon: {slot: 2, at: [512, 384, 0], count: 3, tier: b}\n"
        "      - teleport: {to: [1216, 384, 0], direction: 90}\n"
        "    lua: evt.StatusText(\"Done.\")\n"
        "  - {id: evt:e4_step, preset: script, trigger: step, source: room:a, sets: {map_var: on_lava}, lua: \"\"}\n";
    const BuiltTriggers built =
        buildTriggers(TriggerRooms, "format: 0\nstart: {room: room:a, at: [512, 64]}\n", wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    INFO(built.lua);
    CHECK(built.lua.find(
        "SetMapMetadata({onLoad = {1}, onLeave = {}, openedChestIds = {}, timers = {\n"
        "    { eventId = 2, sourceEventId = 2, triggerStep = 0, origin = \"legacy\", triggerKind = \"timer\", "
        "scheduleKind = \"interval\", intervalHalfMinutes = 2 },\n"
        "    { eventId = 3, sourceEventId = 3, triggerStep = 0, origin = \"legacy\", triggerKind = \"timer\", "
        "scheduleKind = \"interval\", intervalHalfMinutes = 5 },\n"
        "}})\n") != std::string::npos);
    CHECK(built.lua.find("    if not (IsAtLeast(MapVar(0), 1)) then\n        return\n    end\n"
        "    evt.DamagePlayer(Players.All, const.Damage.Fire, 25)\n"
        "    evt.DamagePlayer(Players.All, const.Damage.Physical, 4)\n"
        "    evt.DamagePlayer(Players.Current, const.Damage.Magic, 1)\n") != std::string::npos);
    CHECK(built.lua.find("    SetValue(MapVar(1), 1)\n"
        "    evt.CastSpell(2, 1, 2, 64, 64, 96, 960, 64, 96)\n"
        "    evt.SummonMonsters(2, 2, 3, 512, 384, 0, 0, 0)\n"
        "    evt.MoveToMap(1216, 384, 0, 512, 0, 0, 0, 0)\n"
        "    evt.StatusText(\"Done.\")\n") != std::string::npos);
    // Only the step event is bound to faces; the build does not ask that of a timer or a load event.
    std::set<int> bound;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        if (face.cogTriggered != 0)
        {
            bound.insert(face.cogTriggered);
        }
    }

    CHECK(bound == std::set<int>{4});
}

TEST_CASE("events without a clicked object are refused with what to change")
{
    const std::string objects = TriggerObjects;
    const auto refused = [](const std::string &objectsText, const std::string &events)
    {
        const BuiltTriggers result = buildTriggers(
            TriggerRooms, objectsText, events.empty() ? "format: 0\n" : "format: 0\nevents:\n" + events);
        CHECK_FALSE(result.rooms.built);
        return issueText(result.rooms);
    };
    const auto mentions = [](const std::string &text, const std::string &fragment)
    {
        INFO(text);
        return text.find(fragment) != std::string::npos;
    };
    CHECK(mentions(refused(objects, "  - {id: evt:a, preset: text, source: plate:flat, text: x}\n"),
        "Add `trigger: step`"));
    CHECK(mentions(refused(objects, "  - {id: evt:a, preset: text, source: room:a, text: x}\n"),
        "Add `trigger: step`"));
    CHECK(mentions(refused(objects, "  - {id: evt:a, preset: text, trigger: step, source: door:ab, text: x}\n"),
        "door:ab is a door, which is clicked"));
    CHECK(mentions(refused(objects, "  - {id: evt:a, preset: text, trigger: step, text: x}\n"),
        "a step event needs a `source`"));
    CHECK(mentions(refused(objects, "  - {id: evt:a, preset: text, trigger: timer, text: x}\n"),
        "a timer needs `every: <seconds>`"));
    CHECK(mentions(
        refused(objects, "  - {id: evt:a, preset: text, trigger: timer, every: 2, source: room:a, text: x}\n"),
        "has no `source`"));
    CHECK(mentions(refused(objects, "  - {id: evt:a, preset: text, trigger: load, every: 2, text: x}\n"),
        "`every` belongs to a timer"));
    CHECK(mentions(refused(objects, "  - {id: evt:a, preset: door, trigger: step, source: plate:flat}\n"),
        "is `preset: switch` (opens, closes, toggles), `text`, `teleport` or `script`"));
    CHECK(mentions(refused(objects,
        "  - {id: evt:a, preset: text, trigger: step, source: plate:flat, text: x}\n"
        "  - {id: evt:b, preset: text, trigger: step, source: room:a, sources: [plate:flat], text: x}\n"),
        "plate:flat already runs a step event"));
    CHECK(mentions(
        refused(objects, "  - {id: evt:a, preset: script, trigger: load, effects: [{damage: {kind: fire}}]}\n"),
        "damage is {amount"));
    CHECK(mentions(refused(objects, "  - {id: evt:a, preset: script, trigger: load, effects: [{cast: {spell: 2}}]}\n"),
        "cast is {spell"));
    CHECK(mentions(refused(objects, "  - {id: evt:a, preset: script, trigger: load, effects: [{summon: {slot: 9}}]}\n"),
        "summon is {slot"));

    // Plates that cannot be cut into a floor, and floors that are not there.
    const auto withPlate = [&refused](const std::string &plate)
    {
        return refused("format: 0\nstart: {room: room:a, at: [512, 64]}\nplates:\n  - " + plate + "\n", "");
    };
    CHECK(mentions(withPlate("{id: plate:p, room: room:a, at: [40, 384], size: [64, 64]}"),
        "at least 16 from its walls"));
    CHECK(mentions(withPlate("{id: plate:p, room: room:a, at: [192, 192], size: [64, 64]}"),
        "lies on a level, platform or flight"));
    CHECK(mentions(withPlate("{id: plate:p, room: room:a}"), "a plate needs `size: [width, depth]`"));
    CHECK(mentions(withPlate("{id: plate:p, room: room:a, at: [512, 384], size: [64, 64]}\n"
        "  - {id: plate:q, room: room:a, at: [540, 384], size: [64, 64]}"), "overlaps another plate"));
    CHECK(mentions(refused("format: 0\nstart: {room: room:a, at: [512, 64]}\nfloors:\n"
        "  - {id: floor:f, of: room:a, kind: lava}\n  - {id: floor:g, of: room:a, kind: lava}\n", ""),
        "already marked"));

    // A plate no event names builds as plain floor: one face, no event.
    const BuiltTriggers plain = buildTriggers(
        TriggerRooms, "format: 0\nstart: {room: room:a, at: [512, 64]}\nplates:\n"
        "  - {id: plate:p, room: room:a, at: [512, 384], size: [64, 64]}\n", "format: 0\n");
    INFO(issueText(plain.rooms));
    REQUIRE(plain.rooms.built);
    REQUIRE(plain.floorsOver(1, 512, 384).size() == 1);
    CHECK(plain.floorsOver(1, 512, 384)[0]->cogTriggered == 0);
    CHECK((plain.floorsOver(1, 512, 384)[0]->attributes & (StepFlags | ClickFlag)) == 0);
}

// Defects found by the rebuilds of 2026-11-12, round two: the texture of leaning ceiling sides, levels on levels,
// openings in gable ends, limits tighter than their messages, beams through ceilings, objects and flights on
// floors that lie one above the other, ceiling levels over stepped floors.

TEST_CASE("a leaning ceiling side takes the ceiling's surface, rows level and at its true size down the slope")
{
    // A frustum over the whole room: its sides lean in 128 over a rise of 256, so they are 286 long down the slope.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 256,\n"
        "     ceiling_levels: [{ceiling: 512, top_outline: [[128, 128], [384, 128], [384, 384], [128, 384]]}]}\n";
    const auto leaningSides = [](const BuiltRooms &built, const std::string &texture)
    {
        size_t sides = 0;

        for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
        {
            const std::array<int, 2> range = built.heights(face);

            if (range[0] != 256 || range[1] != 512)
            {
                continue;
            }

            ++sides;
            CHECK(face.textureName == texture);
            int footLow = 0;
            int footHigh = 0;
            int topRow = 0;
            int footRow = 0;
            bool firstFoot = true;

            for (size_t index = 0; index < face.vertexIndices.size(); ++index)
            {
                const int z = built.map.vertices[face.vertexIndices[index]].z;

                if (z == 512)
                {
                    topRow = face.textureVs[index];
                    continue;
                }

                // Rows are level: every corner of the foot lies in one row of the texture.
                CHECK((firstFoot || face.textureVs[index] == footRow));
                footRow = face.textureVs[index];
                footLow = firstFoot ? face.textureUs[index] : std::min<int>(footLow, face.textureUs[index]);
                footHigh = firstFoot ? face.textureUs[index] : std::max<int>(footHigh, face.textureUs[index]);
                firstFoot = false;
            }

            // The foot is 512 long and the side 286 down the slope: so many texels each.
            CHECK(footHigh - footLow == 512);
            CHECK(std::abs(footRow - topRow) == 286);
        }

        return sides;
    };
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(leaningSides(built, "ceil") == 4);

    std::string edged = rooms;
    edged.replace(edged.find("{ceiling: 512,"), 14, "{ceiling: 512, edge: {texture: rib, size: [128, 128]},");
    const BuiltRooms withEdge = buildRooms(edged);
    INFO(issueText(withEdge));
    REQUIRE(withEdge.built);
    CHECK(leaningSides(withEdge, "rib") == 4);

    // Upright sides stay wall.
    const BuiltRooms upright = buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 256,\n"
        "     ceiling_levels: [{outline: [[128, 128], [384, 128], [384, 384], [128, 384]], ceiling: 320}]}\n");
    REQUIRE(upright.built);

    for (const OpenYAMM::Game::IndoorFace &face : upright.map.faces)
    {
        const std::array<int, 2> range = upright.heights(face);
        CHECK((range[0] != 256 || range[1] != 320 || face.textureName == "wall"));
    }
}

TEST_CASE("a ceiling level stands on the flat top of another, to any depth, and a room above opens into such a top")
{
    // A pyramid with a flat top, a drum on the whole of that top, and a pointed cap inside the drum's top.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 256\n"
        "    ceiling_levels:\n"
        "      - {ceiling: 512, top_outline: [[256, 256], [768, 256], [768, 768], [256, 768]]}\n"
        "      - {outline: [[256, 256], [768, 256], [768, 768], [256, 768]], ceiling: 640}\n"
        "      - {outline: [[384, 384], [640, 384], [640, 640], [384, 640]], ceiling: 768, top_scale: 0}\n";
    const BuiltRooms built = buildRooms(rooms, "format: 0\nstart: {room: room:a, at: [64, 64]}\n");
    INFO(issueText(built));
    REQUIRE(built.built);
    // The pyramid's own top is the drum's foot: no ceiling at 512. The drum's top lies round the cap.
    CHECK(built.levelsOver(1, 300, 500, false) == std::vector<int>{640});
    CHECK(built.hasVertex(256, 256, 512));
    CHECK(built.hasVertex(256, 256, 640));
    CHECK(built.hasVertex(384, 384, 640));
    CHECK(built.hasVertex(512, 512, 768));
    const std::vector<int> underCap = built.levelsOver(1, 500, 420, false);
    REQUIRE(underCap.size() == 1);
    CHECK(underCap[0] == 640);

    const auto refused = [&rooms](const std::string &from, const std::string &to)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = buildRooms(changed, "format: 0\nstart: {room: room:a, at: [64, 64]}\n");
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    // Beside the whole-ceiling level there is no ceiling to cut another level into; a level on a top is higher
    // than the top, and takes all of it or lies inside it.
    CHECK(refused("{outline: [[256, 256], [768, 256], [768, 768], [256, 768]], ceiling: 640}",
        "{outline: [[32, 32], [128, 32], [128, 128], [32, 128]], ceiling: 640}")
        .find("must stand on a level's flat top") != std::string::npos);
    CHECK(refused("[256, 768]], ceiling: 640}", "[256, 768]], ceiling: 500}")
        .find("lies higher than that top (512 here)") != std::string::npos);
    CHECK(refused("{outline: [[384, 384], [640, 384], [640, 640], [384, 640]]",
        "{outline: [[256, 384], [640, 384], [640, 640], [256, 640]]").find("stands on the flat top of the level")
        != std::string::npos);

    // A lantern room standing on the pyramid's flat top, joined to the hall by a hole in its floor: the hole goes
    // through the top (512), not through the hall's `ceiling` (256).
    const BuiltRooms lantern = buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 256,\n"
        "     ceiling_levels: [{ceiling: 512, top_outline: [[256, 256], [768, 256], [768, 768], [256, 768]]}]}\n"
        "  - {id: room:b, outline: [[288, 288], [736, 288], [736, 736], [288, 736]], floor: 512, ceiling: 768}\n"
        "openings:\n"
        "  - {id: open:lantern, from: room:b, to: room:a, in: floor,\n"
        "     outline: [[400, 400], [624, 400], [624, 624], [400, 624]]}\n",
        "format: 0\nstart: {room: room:a, at: [64, 64]}\n");
    INFO(issueText(lantern));
    REQUIRE(lantern.built);
    CHECK(lantern.levelsOver(1, 300, 500, false) == std::vector<int>{512});
    CHECK(lantern.levelsOver(1, 512, 512, false).empty());
    CHECK(lantern.levelsOver(2, 512, 512, true).empty());
    size_t portals = 0;

    for (const OpenYAMM::Game::IndoorFace &face : lantern.map.faces)
    {
        if (face.isPortal)
        {
            ++portals;
            CHECK(lantern.heights(face) == std::array<int, 2>{512, 512});
        }
    }

    CHECK(portals == 1);
}

TEST_CASE("an opening rises into the gable end under a ridge, and a refused opening is not reported twice")
{
    // A tube under a ridge (eaves 224, ridge 304 over the middle 128) ends at a hall: its end wall stands to the
    // ridge, so the doorway may rise to 288.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[1056, -256], [1568, -256], [1568, 576], [1056, 576]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[0, 0], [1024, 0], [1024, 320], [0, 320]], floor: 0, ceiling: 224,\n"
        "     ceiling_levels: [{ceiling: 304, top_outline: [[0, 96], [1024, 96], [1024, 224], [0, 224]]}]}\n"
        "openings:\n"
        "  - {id: open:end, from: room:b, to: room:a, width: 128, height: 288}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [1280, 160]}\ndoors:\n  - {id: door:end, opening: open:end}\n";
    const std::string wiring =
        "format: 0\nevents:\n  - {id: evt:end, preset: door, source: door:end}\n";
    const BuiltTriggers built = buildTriggers(rooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // The doorway's top corners in the gable end, above the eaves; the gable is built round it.
    CHECK(built.rooms.hasVertex(1024, 96, 288));
    CHECK(built.rooms.hasVertex(1024, 224, 288));
    bool gableOverDoor = false;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        const std::array<int, 2> range = built.rooms.heights(face);
        gableOverDoor = gableOverDoor || (face.roomNumber == 2 && range[0] == 288 && range[1] == 304);
    }

    CHECK(gableOverDoor);

    // Higher than 16 under the ridge it is refused, once: the door and the event that name it say nothing more.
    std::string tooHigh = rooms;
    tooHigh.replace(tooHigh.find("height: 288"), 11, "height: 300");
    const BuiltTriggers refused = buildTriggers(tooHigh, objects, wiring);
    CHECK_FALSE(refused.rooms.built);
    const std::string text = issueText(refused.rooms);
    CHECK(text.find("takes an opening up to 288") != std::string::npos);
    CHECK(text.find("there is no opening") == std::string::npos);
    CHECK(text.find("there is no object") == std::string::npos);
    CHECK(refused.rooms.issues.size() == 1);

    // An id that is nowhere is still reported.
    const BuiltTriggers unknown = buildTriggers(
        rooms, objects, "format: 0\nevents:\n  - {id: evt:end, preset: door, source: door:other}\n");
    CHECK(issueText(unknown.rooms).find("there is no object door:other") != std::string::npos);
}

TEST_CASE("limits say what they hold: a hole 16 from a wall, a stairwell of twelve steps, a ceiling twice its run")
{
    // The hole's corners lie exactly 16 from the lower room's west and north walls; the stair room's whole ceiling
    // is a hole with 26 points.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]], floor: 256, ceiling: 640}\n"
        "  - {id: room:b, outline: [[64, 448], [448, 448], [448, 704], [64, 704]], floor: -64, ceiling: 224}\n"
        "  - {id: room:c, outline: [[64, 64], [448, 64], [448, 192], [64, 192]], floor: -128, ceiling: 256,\n"
        "     slope: {to: 256, toward: west, steps: 12}}\n"
        "  - {id: room:d, outline: [[480, 64], [736, 64], [736, 192], [480, 192]], floor: -128, ceiling: 96}\n"
        "openings:\n"
        "  - {id: open:hole, from: room:a, to: room:b, in: floor,\n"
        "     outline: [[80, 560], [208, 560], [208, 688], [80, 688]]}\n"
        "  - {id: open:well, from: room:a, to: room:c, in: floor}\n"
        "  - {id: open:foot, from: room:c, to: room:d, width: 96, height: 192}\n";
    const BuiltRooms built = buildRooms(rooms, "format: 0\nstart: {room: room:a, at: [800, 400]}\n");
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(built.levelsOver(1, 144, 624, true).empty());
    CHECK(built.levelsOver(1, 256, 128, true).empty());
    size_t largest = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        largest = face.isPortal ? std::max(largest, face.vertexIndices.size()) : largest;
    }

    // Four corners, two points for each of the eleven risers' ends... and the doorway's two sides.
    CHECK(largest == 28);

    std::string near = rooms;
    near.replace(near.find("[[80, 560], [208, 560], [208, 688], [80, 688]]"), 46,
        "[[79, 560], [208, 560], [208, 688], [79, 688]]");
    CHECK(issueText(buildRooms(near, "format: 0\nstart: {room: room:a, at: [800, 400]}\n"))
        .find("at least 16 units from its walls") != std::string::npos);

    // A ceiling may rise twice its run, and no more.
    const BuiltRooms steep = buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [256, 0], [256, 512], [0, 512]], floor: 0, ceiling: 640,\n"
        "     ceiling_slope: {to: 128, toward: east}}\n");
    INFO(issueText(steep));
    REQUIRE(steep.built);
    CHECK(steep.hasVertex(0, 0, 640));
    CHECK(steep.hasVertex(256, 0, 128));
    // Its texture runs down the slope at its true size: 572 texels for a slope 572 long.
    bool sloped = false;

    for (const OpenYAMM::Game::IndoorFace &face : steep.map.faces)
    {
        if (steep.heights(face) == std::array<int, 2>{128, 640} && face.textureName == "ceil")
        {
            const std::pair<std::vector<int16_t>::const_iterator, std::vector<int16_t>::const_iterator> rows =
                std::minmax_element(face.textureVs.begin(), face.textureVs.end());
            CHECK(*rows.second - *rows.first == 572);
            sloped = true;
        }
    }

    CHECK(sloped);
    const BuiltRooms steeper = buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [256, 0], [256, 512], [0, 512]], floor: 0, ceiling: 656,\n"
        "     ceiling_slope: {to: 128, toward: east}}\n");
    CHECK_FALSE(steeper.built);
    CHECK(issueText(steeper).find("at most twice the run") != std::string::npos);
}

TEST_CASE("a beam or platform that stands above the ceiling is refused with the heights; a haunch is cut level")
{
    const auto withRoom = [](const std::string &features)
    {
        return buildRooms(
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    ceiling: 512\n" + features);
    };
    // Both ends above the ceiling.
    const BuiltRooms through = withRoom(
        "    beams:\n      - {path: [[256, 512], [768, 512]], width: 128, depth: 512, bottom: 256, bottom_end: 480}\n");
    CHECK_FALSE(through.built);
    CHECK(issueText(through).find("the beam reaches 992 but the ceiling of room:a at that place is at 512")
        != std::string::npos);
    const BuiltRooms level = withRoom(
        "    beams:\n      - {path: [[256, 512], [768, 512]], width: 128, depth: 64, bottom: 480}\n");
    CHECK_FALSE(level.built);
    CHECK(issueText(level).find("the beam reaches 544") != std::string::npos);
    const BuiltRooms tall = withRoom("    platforms:\n      - {at: [512, 512], size: [128, 128], rise: 600}\n");
    CHECK_FALSE(tall.built);
    CHECK(issueText(tall).find("the platform reaches 600 but the ceiling of room:a at that place is at 512")
        != std::string::npos);

    // A raking beam that meets the ceiling with its low end is the haunch of an arch: cut level at the ceiling.
    const BuiltRooms haunch = withRoom(
        "    beams:\n      - {path: [[256, 512], [768, 512]], width: 128, depth: 256, bottom: 256, bottom_end: 448}\n");
    INFO(issueText(haunch));
    REQUIRE(haunch.built);
    CHECK(haunch.hasVertex(768, 448, 448));
    CHECK(haunch.hasVertex(768, 448, 512));

    for (const OpenYAMM::Game::IndoorVertex &vertex : haunch.map.vertices)
    {
        CHECK(vertex.z <= 512);
    }

    // Under a ceiling level a beam may stand as high as the level there.
    const BuiltRooms underLevel = withRoom(
        "    ceiling_levels:\n"
        "      - {outline: [[256, 256], [768, 256], [768, 768], [256, 768]], ceiling: 768}\n"
        "    beams:\n      - {path: [[320, 512], [704, 512]], width: 64, depth: 64, bottom: 640}\n");
    INFO(issueText(underLevel));
    CHECK(underLevel.built);
}

TEST_CASE("objects stand on the highest floor under them, and a flight ends on the platform its end point touches")
{
    // A level 704 high and a slab hanging at 640 to 704: one chest on each, one under the slab.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 1024\n"
        "    platforms:\n"
        "      - {at: [896, 896], size: [256, 256], rise: 64, base: 640}\n"
        "    levels:\n"
        "      - {outline: [[0, 0], [256, 0], [256, 256], [0, 256]], floor: 704}\n";
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a, at: [512, 512]}\n"
        "chests:\n"
        "  - {id: chest:on_level, room: room:a, at: [128, 128], facing: e, size: [72, 48, 44]}\n"
        "  - {id: chest:on_slab, room: room:a, at: [896, 896], facing: e, size: [72, 48, 44]}\n"
        "  - {id: chest:under_slab, room: room:a, at: [896, 800], facing: e, floor_height: 0, size: [72, 48, 44]}\n"
        "spawns:\n"
        "  - {id: spawn:on_slab, room: room:a, at: [960, 960], slot: 1}\n"
        "  - {id: spawn:under_slab, room: room:a, at: [832, 960], slot: 1, floor_height: 0}\n";
    const BuiltRooms built = buildRooms(rooms, objects);
    INFO(issueText(built));
    REQUIRE(built.built);
    // A chest is 72 by 48 and 44 high.
    CHECK(built.hasVertex(92, 104, 704));
    CHECK(built.hasVertex(92, 104, 748));
    CHECK_FALSE(built.hasVertex(92, 104, 44));
    CHECK(built.hasVertex(860, 872, 704));
    CHECK(built.hasVertex(860, 872, 748));
    CHECK(built.hasVertex(860, 776, 0));
    CHECK(built.hasVertex(860, 776, 44));
    REQUIRE(built.map.spawns.size() == 2);
    CHECK(built.map.spawns[0].z == 704);
    CHECK(built.map.spawns[1].z == 0);
    std::string wrong = objects;
    wrong.replace(wrong.find("floor_height: 0"), 15, "floor_height: 300");
    CHECK(issueText(buildRooms(rooms, wrong)).find("there is no floor at 300 at [896, 800] in room:a: the floors "
        "there are at 0, 704") != std::string::npos);

    // A pier (384) under a gallery (448): the flight's end touches both, and climbs to the gallery unless told
    // otherwise. Its steps hang over the floor and show their undersides.
    const std::string stacked =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 896\n"
        "    platforms:\n"
        "      - {rise: 64, base: 384, outline: [[0, 0], [256, 0], [256, 1024], [0, 1024]]}\n"
        "      - {rise: 384, outline: [[0, 384], [256, 384], [256, 640], [0, 640]]}\n"
        "      - {rise: 336, outline: [[448, 384], [704, 384], [704, 640], [448, 640]]}\n"
        "    flights:\n"
        "      - {from: [456, 512], to: [256, 512], width: 256, steps: 4}\n";
    const std::string start = "format: 0\nstart: {room: room:a, at: [800, 100]}\n";
    const BuiltRooms climbed = buildRooms(stacked, start);
    INFO(issueText(climbed));
    REQUIRE(climbed.built);
    // The last tread ends on the gallery's edge at the gallery's height, and the first has an underside at 336.
    CHECK(climbed.hasVertex(306, 384, 448));
    CHECK(climbed.levelsOver(1, 430, 512, true) == std::vector<int>{0, 364});
    CHECK(climbed.levelsOver(1, 430, 512, false).front() == 336);
    std::string lower = stacked;
    lower.replace(lower.find("steps: 4}"), 9, "steps: 4, to_height: 384}");
    const BuiltRooms toPier = buildRooms(lower, start);
    INFO(issueText(toPier));
    REQUIRE(toPier.built);
    CHECK(toPier.hasVertex(306, 384, 384));
    CHECK_FALSE(toPier.hasVertex(306, 384, 448));
    lower.replace(lower.find("to_height: 384"), 14, "to_height: 100");
    CHECK(issueText(buildRooms(lower, start)).find("there is no floor at 100 at the flight's `to` point: the floors "
        "there are at 0, 384, 448") != std::string::npos);
}

TEST_CASE("a ceiling level is built over a stepped floor, and a pillar on steps is refused")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [256, 0], [256, 512], [0, 512]], floor: 0, ceiling: 512,\n"
        "     slope: {to: 256, toward: north, steps: 8},\n"
        "     ceiling_levels: [{outline: [[64, 128], [192, 128], [192, 384], [64, 384]], ceiling: 608}]}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(built.levelsOver(1, 128, 256, false) == std::vector<int>{608});
    CHECK(built.levelsOver(1, 32, 256, false) == std::vector<int>{512});
    CHECK(built.hasVertex(64, 128, 512));
    CHECK(built.hasVertex(64, 128, 608));
    // The treads are whole under it.
    CHECK(built.levelsOver(1, 128, 240, true) == std::vector<int>{96});

    const std::string level =
        "ceiling_levels: [{outline: [[64, 128], [192, 128], [192, 384], [64, 384]], ceiling: 608}]";
    std::string pillared = rooms;
    pillared.replace(pillared.find(level), level.size(), "pillars: [{at: [128, 256], size: [64, 64]}]");
    const BuiltRooms refused = buildRooms(pillared);
    CHECK_FALSE(refused.built);
    CHECK(issueText(refused).find("a pillar cannot stand in a room with a stepped floor") != std::string::npos);
}

namespace
{
// The corners of a face.
std::vector<std::array<double, 3>> faceCorners(const BuiltRooms &built, const OpenYAMM::Game::IndoorFace &face)
{
    std::vector<std::array<double, 3>> corners;

    for (const uint16_t vertex : face.vertexIndices)
    {
        corners.push_back({
            static_cast<double>(built.map.vertices[vertex].x), static_cast<double>(built.map.vertices[vertex].y),
            static_cast<double>(built.map.vertices[vertex].z)});
    }

    return corners;
}

// A face's normal for its winding, as long as twice its area (Newell's method).
std::array<double, 3> faceNormal(const BuiltRooms &built, const OpenYAMM::Game::IndoorFace &face)
{
    const std::vector<std::array<double, 3>> corners = faceCorners(built, face);
    std::array<double, 3> normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < corners.size(); ++index)
    {
        const std::array<double, 3> &a = corners[index];
        const std::array<double, 3> &b = corners[(index + 1) % corners.size()];
        normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
        normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
        normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
    }

    return normal;
}

double faceArea(const BuiltRooms &built, const OpenYAMM::Game::IndoorFace &face)
{
    const std::array<double, 3> normal = faceNormal(built, face);
    return std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]) / 2.0;
}

// The faces of one sector that stand in the plane y = `y` (a wall along x), portals left out.
std::vector<const OpenYAMM::Game::IndoorFace *> facesOnWall(const BuiltRooms &built, int sector, int y)
{
    std::vector<const OpenYAMM::Game::IndoorFace *> found;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        bool onWall = !face.isPortal && face.roomNumber == sector;

        for (const uint16_t vertex : face.vertexIndices)
        {
            onWall = onWall && built.map.vertices[vertex].y == y;
        }

        if (onWall)
        {
            found.push_back(&face);
        }
    }

    return found;
}

// The box of a face: lowest and highest x, then lowest and highest z.
std::array<int, 4> faceBox(const BuiltRooms &built, const OpenYAMM::Game::IndoorFace &face)
{
    std::array<int, 4> box = {1 << 30, -(1 << 30), 1 << 30, -(1 << 30)};

    for (const uint16_t vertex : face.vertexIndices)
    {
        box[0] = std::min<int>(box[0], built.map.vertices[vertex].x);
        box[1] = std::max<int>(box[1], built.map.vertices[vertex].x);
        box[2] = std::min<int>(box[2], built.map.vertices[vertex].z);
        box[3] = std::max<int>(box[3], built.map.vertices[vertex].z);
    }

    return box;
}

// The area of the faces of a wall with one texture, and the box of them all.
double textureArea(
    const BuiltRooms &built, int sector, int y, const std::string &texture, std::array<int, 4> *pBox = nullptr)
{
    double area = 0.0;
    std::array<int, 4> all = {1 << 30, -(1 << 30), 1 << 30, -(1 << 30)};

    for (const OpenYAMM::Game::IndoorFace *pFace : facesOnWall(built, sector, y))
    {
        if (pFace->textureName == texture)
        {
            const std::array<int, 4> box = faceBox(built, *pFace);
            area += faceArea(built, *pFace);
            all = {std::min(all[0], box[0]), std::max(all[1], box[1]), std::min(all[2], box[2]),
                   std::max(all[3], box[3])};
        }
    }

    if (pBox != nullptr)
    {
        *pBox = all;
    }

    return area;
}

// The height of a sector's floor over a point, read from the plane of the floor face that holds it.
double floorHeightAt(const BuiltRooms &built, int sector, double x, double y)
{
    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.isPortal || face.roomNumber != sector || (face.facetType != 3 && face.facetType != 4)
            || !built.holds(face, x, y))
        {
            continue;
        }

        const std::array<double, 3> normal = faceNormal(built, face);
        const std::array<double, 3> corner = faceCorners(built, face)[0];
        return corner[2] - (normal[0] * (x - corner[0]) + normal[1] * (y - corner[1])) / normal[2];
    }

    return -1.0e9;
}
}

TEST_CASE("panels are cut into a wall beside an opening and through its bands, and strips stand at its ends")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [512, 0], [512, 512], [0, 512]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    bands:\n"
        "      - {height: 96, surface: {texture: band, size: [128, 128]}}\n"
        "    walls:\n"
        "      - wall: south\n"
        "        panels:\n"
        "          - {offset: 64, length: 128, bottom: 64, height: 128, surface: {texture: pan, size: [64, 64]}}\n"
        "          - {from: end, offset: 32, length: 64, surface: {texture: tall, size: [64, 64], fit: true}}\n"
        "      - wall: north\n"
        "        ends: {length: 32, surface: {texture: strip, size: [64, 64]}}\n"
        "  - {id: room:b, outline: [[0, -544], [512, -544], [512, -32], [0, -32]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    // The south wall is whole and nothing lies on anything else: its faces add up to the wall less the doorway.
    double wallArea = 0.0;

    for (const OpenYAMM::Game::IndoorFace *pFace : facesOnWall(built, 1, 0))
    {
        wallArea += faceArea(built, *pFace);
    }

    CHECK(wallArea == doctest::Approx(512.0 * 384.0 - 128.0 * 256.0));
    // The first panel: 64 to 192 along the wall (it ends where the doorway begins), 64 to 192 above the floor, one
    // face though the band's top (96) passes through it.
    std::array<int, 4> box = {};
    CHECK(textureArea(built, 1, 0, "pan", &box) == doctest::Approx(128.0 * 128.0));
    CHECK(box == std::array<int, 4>{64, 192, 64, 192});
    // The second, measured from the wall's end corner, over the whole height.
    CHECK(textureArea(built, 1, 0, "tall", &box) == doctest::Approx(64.0 * 384.0));
    CHECK(box == std::array<int, 4>{416, 480, 0, 384});
    // The band is left where no panel is: the wall's length less the doorway and the tall panel, and the first
    // panel's lower 32.
    CHECK(textureArea(built, 1, 0, "band") == doctest::Approx((512.0 - 128.0 - 64.0) * 96.0 - 128.0 * 32.0));
    // Strips at both ends of the north wall.
    CHECK(textureArea(built, 1, 512, "strip", &box) == doctest::Approx(2.0 * 32.0 * 384.0));
    CHECK(box == std::array<int, 4>{0, 512, 0, 384});
    CHECK(textureArea(built, 1, 512, "band") == doctest::Approx((512.0 - 64.0) * 96.0));
    // The floor has a corner at every cut of the wall.
    CHECK(built.hasVertex(64, 0, 0));
    CHECK(built.hasVertex(416, 0, 0));
    CHECK(built.hasVertex(480, 512, 384));

    const std::string first =
        "{offset: 64, length: 128, bottom: 64, height: 128, surface: {texture: pan, size: [64, 64]}}";
    std::string wrong = rooms;
    wrong.replace(
        wrong.find(first), first.size(), "{offset: 448, length: 128, surface: {texture: pan, size: [64, 64]}}");
    CHECK(issueText(buildRooms(wrong)).find("the panel would run from 448 to 576 along a wall 512 long")
        != std::string::npos);
    wrong = rooms;
    wrong.replace(
        wrong.find(first), first.size(), "{offset: 400, length: 64, surface: {texture: pan, size: [64, 64]}}");
    CHECK(issueText(buildRooms(wrong)).find("the panel overlaps another on the same wall") != std::string::npos);
    wrong = rooms;
    wrong.replace(wrong.find("ends: {length: 32,"), 18, "ends: {length: 250,");
    CHECK(issueText(buildRooms(wrong)).find("room for two strips with 16 of wall between them (at most 248 here)")
        != std::string::npos);
}

TEST_CASE("a panel on a wall with a raking top covers its whole height or stays under the rake; a door has two sides")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [512, 0], [512, 512], [0, 512]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    ceiling_slope: {to: 256, toward: east}\n"
        "    ends: {length: 32, surface: {texture: strip, size: [64, 64]}}\n"
        "    walls:\n"
        "      - wall: south\n"
        "        panels:\n"
        "          - {offset: 128, length: 128, surface: {texture: pan, size: [64, 64]}}\n"
        "          - {at: centre, offset: 96, length: 64, bottom: 32, height: 200,\n"
        "             surface: {texture: low, size: [64, 64]}}\n"
        "  - {id: room:b, outline: [[544, 0], [800, 0], [800, 512], [544, 512]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a}\ndoors:\n"
        "  - {id: door:ab, opening: open:ab, surface: {texture: front, size: [64, 64]},\n"
        "     back_surface: {texture: back, size: [64, 64]}}\n";
    const BuiltRooms built = buildRooms(rooms, objects);
    INFO(issueText(built));
    REQUIRE(built.built);
    // The south wall's top runs from 384 at x 0 to 256 at x 512: the full-height panel from 352 to 320.
    std::array<int, 4> box = {};
    CHECK(textureArea(built, 1, 0, "pan", &box) == doctest::Approx(128.0 * (352.0 + 320.0) / 2.0));
    CHECK(box == std::array<int, 4>{128, 256, 0, 352});
    CHECK(built.hasVertex(128, 0, 352));
    CHECK(built.hasVertex(256, 0, 320));
    // The level one: centred (224 to 288) and moved 96 toward the end corner.
    CHECK(textureArea(built, 1, 0, "low", &box) == doctest::Approx(64.0 * 200.0));
    CHECK(box == std::array<int, 4>{320, 384, 32, 232});
    // The room's corner strips rake with the wall: 32 long at each end of the south wall.
    CHECK(textureArea(built, 1, 0, "strip")
        == doctest::Approx(32.0 * (384.0 + 376.0) / 2.0 + 32.0 * (264.0 + 256.0) / 2.0));
    double wallArea = 0.0;

    for (const OpenYAMM::Game::IndoorFace *pFace : facesOnWall(built, 1, 0))
    {
        wallArea += faceArea(built, *pFace);
    }

    CHECK(wallArea == doctest::Approx(512.0 * (384.0 + 256.0) / 2.0));
    // The door's leaf: one face for each side.
    size_t fronts = 0;
    size_t backs = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        fronts += face.textureName == "front" ? 1 : 0;
        backs += face.textureName == "back" ? 1 : 0;
    }

    CHECK(fronts == 1);
    CHECK(backs == 1);

    // A panel on the side wall of a ramp, its ends at heights between whole units (the floor rises 100 over 512).
    const BuiltRooms ramp = buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 256], [0, 256]], floor: 0, ceiling: 384,\n"
        "     slope: {to: 100, toward: east},\n"
        "     walls: [{wall: south,\n"
        "              panels: [{offset: 100, length: 111, surface: {texture: pan, size: [64, 64]}}]}]}\n");
    INFO(issueText(ramp));
    REQUIRE(ramp.built);
    CHECK(textureArea(ramp, 1, 0, "pan", &box) > 111.0 * 340.0);
    CHECK((box[0] == 100 && box[1] == 211 && box[2] == 20 && box[3] == 384));

    // A level top inside the rake (the wall's top runs from 304 to 288 over this panel) is refused with the heights
    // that are allowed; a panel taller than the wall ends at the wall's top.
    std::string wrong = rooms;
    wrong.replace(wrong.find("height: 200"), 11, "height: 280");
    const BuiltRooms clipped = buildRooms(wrong, objects);
    REQUIRE(clipped.built);
    CHECK(textureArea(clipped, 1, 0, "low") == doctest::Approx(64.0 * (304.0 + 288.0) / 2.0 - 64.0 * 32.0));
    wrong = rooms;
    wrong.replace(wrong.find("height: 200"), 11, "height: 264");
    const BuiltRooms refused = buildRooms(wrong, objects);
    CHECK_FALSE(refused.built);
    CHECK(issueText(refused).find("the panel's top (at 296) would cut through a raking edge of the wall of room:a")
        != std::string::npos);
    CHECK(issueText(refused).find("Leave out `height`") != std::string::npos);
}

TEST_CASE("a path room climbs along its path: level across at each point, ramps between, doorways at both ends")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [512, 0], [512, 512]], width: 128, floor: 0, slope: {to: 256},\n"
        "     ceiling: 192}\n"
        "  - {id: room:b, outline: [[384, 544], [640, 544], [640, 800], [384, 800]], floor: 256, ceiling: 512}\n"
        "  - {id: room:c, outline: [[-288, -128], [-32, -128], [-32, 128], [-288, 128]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 96, height: 160}\n"
        "  - {id: open:ac, from: room:a, to: room:c, width: 96, height: 160}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    // Both sides of the corridor stand at one height at each point of the path: 0, 128 at the bend (half way
    // along), 256; the ceiling 192 above.
    CHECK(built.hasVertex(0, -64, 0));
    CHECK(built.hasVertex(0, 64, 0));
    CHECK(built.hasVertex(576, -64, 128));
    CHECK(built.hasVertex(448, 64, 128));
    CHECK(built.hasVertex(576, 512, 256));
    CHECK(built.hasVertex(448, 512, 256));
    CHECK(built.hasVertex(576, -64, 320));
    CHECK(built.hasVertex(448, 64, 320));
    CHECK(built.hasVertex(448, 512, 448));
    // Between the points the floor is a ramp: 64 half way along the first stretch's inner side.
    CHECK(floorHeightAt(built, 1, 224.0, 32.0) == doctest::Approx(64.0).epsilon(0.02));
    CHECK(floorHeightAt(built, 1, 512.0, 288.0) > 128.0);
    CHECK(floorHeightAt(built, 1, 512.0, 288.0) < 256.0);
    // Every floor face can be walked: the engine wants a normal of at least 0.71 upward.
    size_t floors = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (!face.isPortal && face.roomNumber == 1 && (face.facetType == 3 || face.facetType == 4))
        {
            const std::array<double, 3> normal = faceNormal(built, face);
            CHECK(std::abs(normal[2]) / (2.0 * faceArea(built, face)) > 0.74);
            ++floors;
        }
    }

    // Two triangles for each of the two stretches, and the thresholds of the two doorways.
    CHECK(floors == 6);
    // The doorways: at the path's end from 256, at its start from 0.
    std::vector<std::array<int, 2>> portals;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.isPortal)
        {
            portals.push_back(built.heights(face));
        }
    }

    std::sort(portals.begin(), portals.end());
    CHECK(portals == std::vector<std::array<int, 2>>{{0, 160}, {256, 416}});

    // A level ceiling over the climbing floor, and a smoothed path with heights that fall between whole units.
    const std::string level =
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [700, 0], [700, 700]], width: 160, smooth: 2, floor: 0,\n"
        "     slope: {to: 300}, ceiling: 500, ceiling_slope: {to: 500},\n"
        "     walls: [{wall: 0, panels: [{offset: 100, length: 100, surface: {texture: pan, size: [64, 64]}}]}]}\n";
    const BuiltRooms smoothed = buildRooms(level);
    INFO(issueText(smoothed));
    REQUIRE(smoothed.built);
    CHECK(smoothed.levelsOver(1, 300.0, 0.0, false) == std::vector<int>{500});
    CHECK(floorHeightAt(smoothed, 1, 20.0, 0.0) < 10.0);
    CHECK(floorHeightAt(smoothed, 1, 700.0, 690.0) > 290.0);
    // The panel's ends are corners of the raking wall and of the floor under it.
    CHECK(smoothed.hasVertex(100, -80, static_cast<int>(std::lround(floorHeightAt(smoothed, 1, 100.0, -79.0)))));

    // What is refused, and how to mend it.
    std::string wrong = rooms;
    wrong.replace(wrong.find("slope: {to: 256}"), 16, "slope: {to: 960}");
    CHECK(issueText(buildRooms(wrong)).find("too steep to walk up (keep it under 0.9)") != std::string::npos);
    wrong = rooms;
    wrong.replace(wrong.find("slope: {to: 256}"), 16, "slope: {to: 256, steps: 8}");
    CHECK(issueText(buildRooms(wrong)).find("climbs along its path") != std::string::npos);
    wrong = rooms;
    wrong.replace(wrong.find("path: [[0, 0], [512, 0], [512, 512]], width: 128"), 48,
        "outline: [[0, 0], [512, 0], [512, 512], [0, 512]]");
    CHECK(issueText(buildRooms(wrong)).find("the slope of a room with an `outline` needs `toward`")
        != std::string::npos);
    // An opening in a side wall, where the floor rises along the wall, is built since 2026-11-13 (the case "a path
    // room that climbs opens in its side" below); in the side of a ramp with `toward` it is still refused.
    wrong = rooms +
        "  - {id: open:ad, from: room:a, to: room:d, width: 96, height: 160}\n";
    wrong.replace(wrong.find("openings:\n"), 10,
        "  - {id: room:d, outline: [[128, -352], [384, -352], [384, -96], [128, -96]], floor: 0, ceiling: 256}\n"
        "openings:\n");
    CHECK(buildRooms(wrong).built);
    wrong = rooms;
    wrong.replace(wrong.find("ceiling: 192}"), 13, "ceiling: 192, pillars: [{at: [256, 0], size: [32, 32]}]}");
    CHECK(issueText(buildRooms(wrong)).find("a pillar cannot stand in a path room that climbs") != std::string::npos);
}

TEST_CASE("treads, the tops of a flight's sides and a doorway's threshold take surfaces of their own")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [512, 0], [512, 512], [0, 512]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    platforms:\n"
        "      - {at: [256, 448], size: [256, 128], rise: 96}\n"
        "    flights:\n"
        "      - {from: [256, 224], to: [256, 384], width: 128, steps: 3, tread: {texture: tread, size: [64, 64]},\n"
        "         sides: {height: 32, surface: {texture: cheek, size: [64, 64]},\n"
        "                 top_surface: {texture: cope, size: [64, 64]}}}\n"
        "  - {id: room:b, outline: [[544, 0], [928, 0], [928, 512], [544, 512]], floor: 0, ceiling: 384,\n"
        "     slope: {to: 192, toward: east, steps: 6, tread: {texture: plank, size: [64, 64]}}}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256,\n"
        "     threshold: {texture: sill, size: [64, 64]}}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    std::map<std::string, std::vector<std::array<int, 2>>> heights;
    std::map<std::string, size_t> floors;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        heights[face.textureName].push_back(built.heights(face));
        floors[face.textureName] += face.facetType == 3 || face.facetType == 4 ? 1 : 0;
    }

    // The flight's three treads, and nothing else of it, are wood; the block keeps the room's floor.
    std::sort(heights["tread"].begin(), heights["tread"].end());
    CHECK(heights["tread"] == std::vector<std::array<int, 2>>{{32, 32}, {64, 64}, {96, 96}});
    CHECK(floors["tread"] == 3);
    // The two side walls' raking tops.
    CHECK(heights["cope"] == std::vector<std::array<int, 2>>{{32, 128}, {32, 128}});
    CHECK(heights["cheek"].size() == 8);
    // The stepped room's six treads.
    CHECK(heights["plank"].size() == 6);
    CHECK(floors["plank"] == 6);
    CHECK(floors["floor"] > 0);
    // The doorway's floor, through the wall's 32.
    REQUIRE(heights["sill"].size() == 1);
    CHECK(heights["sill"][0] == std::array<int, 2>{0, 0});
    CHECK(floors["sill"] == 1);

    std::string wrong = rooms;
    wrong.replace(wrong.find("steps: 6, "), 10, "");
    CHECK(issueText(buildRooms(wrong)).find("`tread` is the surface of the steps' tops and this slope has no `steps`")
        != std::string::npos);
    wrong = rooms;
    wrong.replace(wrong.find("[[544, 0], [928, 0], [928, 512], [544, 512]]"), 44,
        "[[512, 0], [896, 0], [896, 512], [512, 512]]");
    CHECK(issueText(buildRooms(wrong)).find("its doorway has no floor to give a surface") != std::string::npos);
}

#include "core/Reachability.h"
#include "game/maps/IndoorSceneYml.h"

namespace
{
// A project with moving parts built and read back: the map, the scene's door records, the script, and the map with
// its doors as the game starts it (for walks).
struct BuiltMoving
{
    BuiltRooms rooms;
    YAML::Node doors;
    std::string lua;
    LoadedMap loaded;

    // The scene's record of the door with this number.
    YAML::Node door(int doorId) const
    {
        for (const YAML::Node &node : doors)
        {
            if (node["door_id"].as<int>() == doorId)
            {
                return node;
            }
        }

        return YAML::Node();
    }

    std::array<int, 3> direction(int doorId) const
    {
        const YAML::Node node = door(doorId);
        return {node["direction"][0].as<int>(), node["direction"][1].as<int>(), node["direction"][2].as<int>()};
    }

    bool walks(const std::array<float, 3> &from, const std::array<float, 3> &to, bool doorsOpen) const
    {
        return probeWalk(loaded, from, to, doorsOpen).find("straight walk: possible") != std::string::npos;
    }
};

BuiltMoving buildMoving(const std::string &rooms, const std::string &objects, const std::string &wiring = "")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_moving_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    std::ofstream(root / "project.yml", std::ios::binary) << CardText;
    std::ofstream(root / "rooms.yml", std::ios::binary) << std::string(ThemeText) + rooms;
    std::ofstream(root / "objects.yml", std::ios::binary) << objects;

    if (!wiring.empty())
    {
        std::ofstream(root / "wiring.yml", std::ios::binary) << wiring;
    }

    BuiltMoving built;
    Project project;

    if (loadProject(root, project, built.rooms.issues))
    {
        BuildOptions options;
        options.outputDirectory = root / "build";
        BuildResult result;
        built.rooms.built = buildProject(project, options, result);
        built.rooms.issues = result.issues;

        if (built.rooms.built)
        {
            std::ifstream stream(root / "build" / "testmap.blv", std::ios::binary);
            const std::vector<uint8_t> bytes(
                (std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
            built.loaded.world = "mm6";
            built.loaded.fileName = "testmap.blv";
            built.loaded.stem = "testmap";
            built.loaded.kind = MapKind::Indoor;
            built.loaded.indoor = OpenYAMM::Game::IndoorMapDataLoader().loadFromBytes(bytes);
            std::ifstream sceneStream(root / "build" / "testmap.scene.yml", std::ios::binary);
            const std::string sceneText(
                (std::istreambuf_iterator<char>(sceneStream)), std::istreambuf_iterator<char>());
            std::string errorMessage;
            built.loaded.indoorScene = OpenYAMM::Game::IndoorSceneYmlLoader().loadFromText(sceneText, errorMessage);
            built.rooms.built = built.loaded.indoor.has_value() && built.loaded.indoorScene.has_value();

            if (built.rooms.built)
            {
                OpenYAMM::Game::MapDeltaData state;
                built.rooms.built = OpenYAMM::Game::buildIndoorMapStateFromScene(
                    *built.loaded.indoorScene, *built.loaded.indoor, state, errorMessage);
                built.loaded.state = state;
                built.rooms.map = *built.loaded.indoor;
                const YAML::Node scene = YAML::Load(sceneText);
                const YAML::Node initialState = scene["initial_state"];
                built.doors = YAML::Clone(initialState["doors"]);
            }

            std::ifstream luaStream(root / "build" / "testmap.lua", std::ios::binary);
            built.lua.assign((std::istreambuf_iterator<char>(luaStream)), std::istreambuf_iterator<char>());
        }
    }

    std::filesystem::remove_all(root);
    return built;
}

const char *const DoorRooms =
    "rooms:\n"
    "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
    "  - {id: room:b, outline: [[544, 128], [800, 128], [800, 384], [544, 384]], floor: 0, ceiling: 256}\n"
    "openings:\n"
    "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n";

const char *const DoorWiring =
    "format: 0\nevents:\n  - {id: evt:door, preset: door, source: door:ab}\n";

std::string doorObjects(const std::string &fields)
{
    return "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, " + fields + "}\n";
}
}

TEST_CASE("a door slides sideways into the wall beside its doorway, or parts in two leaves that one event moves")
{
    // The doorway is in room a's east wall, which runs north (+y): left, seen from room a, is north.
    const BuiltMoving left = buildMoving(DoorRooms, doorObjects("kind: slide_left"), DoorWiring);
    INFO(issueText(left.rooms));
    REQUIRE(left.rooms.built);
    REQUIRE(left.doors.size() == 1);
    // The direction points from open to shut: the leaf opens toward +y and travels the doorway's width, stopping at
    // the jamb (2 further, or 2 short, the game finds no way through the open doorway: Castle Darkmoor's stair door
    // after the eighth merge, the Lincoln's door 26 on 2026-11-13); its trailing end is drawn 2 inside the leaf, out
    // of the jamb's plane.
    CHECK(left.direction(1) == std::array<int, 3>{0, -65536, 0});
    CHECK(left.door(1)["move_length"].as<int>() == 128);
    // Stored open: every vertex of the leaf stands north of the doorway (y 320 to 450), in the wall's thickness.
    for (const YAML::Node &y : left.door(1)["y_offsets"])
    {
        CHECK(y.as<int>() >= 320);
        CHECK(y.as<int>() <= 450);
    }
    // Shut it stops the walk from room to room; out of the way it does not.
    CHECK_FALSE(left.walks({256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, false));
    CHECK(left.walks({256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, true));

    const BuiltMoving right = buildMoving(DoorRooms, doorObjects("kind: slide_right"), DoorWiring);
    REQUIRE(right.rooms.built);
    CHECK(right.direction(1) == std::array<int, 3>{0, 65536, 0});

    // Two leaves that part sideways: two door records, each travelling half the width, moved by the one event.
    const BuiltMoving pair = buildMoving(DoorRooms, doorObjects("kind: slide_left, leaves: 2"), DoorWiring);
    INFO(issueText(pair.rooms));
    REQUIRE(pair.rooms.built);
    REQUIRE(pair.doors.size() == 2);
    CHECK(pair.direction(1) == std::array<int, 3>{0, -65536, 0});
    CHECK(pair.direction(2) == std::array<int, 3>{0, 65536, 0});
    CHECK(pair.door(1)["move_length"].as<int>() == 64);
    CHECK(pair.door(2)["move_length"].as<int>() == 64);
    CHECK(pair.lua.find("evt.SetDoorState(1, DoorAction.Trigger)") != std::string::npos);
    CHECK(pair.lua.find("evt.SetDoorState(2, DoorAction.Trigger)") != std::string::npos);
    CHECK_FALSE(pair.walks({256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, false));
    CHECK(pair.walks({256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, true));

    // Two leaves that part up and down: the upper half rises, the lower sinks, each half the height.
    const BuiltMoving split = buildMoving(DoorRooms, doorObjects("kind: slide_up, leaves: 2"), DoorWiring);
    INFO(issueText(split.rooms));
    REQUIRE(split.rooms.built);
    REQUIRE(split.doors.size() == 2);
    CHECK(split.direction(1) == std::array<int, 3>{0, 0, -65536});
    CHECK(split.direction(2) == std::array<int, 3>{0, 0, 65536});
    CHECK(split.door(1)["move_length"].as<int>() == 98);
    CHECK_FALSE(split.walks({256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, false));

    // One leaf sliding up builds as it always did: one record, straight down to shut.
    const BuiltMoving up = buildMoving(DoorRooms, doorObjects("kind: slide_up"), DoorWiring);
    REQUIRE(up.rooms.built);
    REQUIRE(up.doors.size() == 1);
    CHECK(up.direction(1) == std::array<int, 3>{0, 0, -65536});
    CHECK(up.door(1)["move_length"].as<int>() == 192);

    // A hinged pair (great hall doors): two rotating leaves, the left one (north, seen from room a) on the north jamb
    // and the right one on the south jamb, swinging apart; one event moves both.
    const BuiltMoving hingedPair = buildMoving(DoorRooms,
        doorObjects("kind: hinged, leaves: 2, surface: {texture: t1door, size: [64, 192]}"), DoorWiring);
    INFO(issueText(hingedPair.rooms));
    REQUIRE(hingedPair.rooms.built);
    REQUIRE(hingedPair.doors.size() == 2);
    const YAML::Node leftLeaf = hingedPair.door(1)["mover"]["rotation"];
    const YAML::Node rightLeaf = hingedPair.door(2)["mover"]["rotation"];
    REQUIRE(leftLeaf.IsMap());
    REQUIRE(rightLeaf.IsMap());
    CHECK(leftLeaf["pivot"][1].as<double>() == doctest::Approx(320.0));
    CHECK(rightLeaf["pivot"][1].as<double>() == doctest::Approx(192.0));
    CHECK(leftLeaf["open_degrees"].as<double>() == doctest::Approx(-90.0));
    CHECK(rightLeaf["open_degrees"].as<double>() == doctest::Approx(90.0));
    CHECK(hingedPair.door(2)["move_length"].as<int>() == 900);
    CHECK(hingedPair.lua.find("evt.SetDoorState(1, DoorAction.Trigger)") != std::string::npos);
    CHECK(hingedPair.lua.find("evt.SetDoorState(2, DoorAction.Trigger)") != std::string::npos);
    CHECK_FALSE(hingedPair.walks({256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, false));

    // A hinged leaf opens away from whoever opens it, so it swings through the doorway into the other room: its
    // faces are listed in both rooms (the room behind them is room b), and their kind follows their normal (facet
    // type 0), so the game draws it while only room b is seen (XD-05's gate leaves, 2026-11-24). One leaf alike.
    const BuiltMoving hingedOne = buildMoving(DoorRooms, doorObjects("kind: hinged"), DoorWiring);
    INFO(issueText(hingedOne.rooms));
    REQUIRE(hingedOne.rooms.built);

    for (const BuiltMoving *pBuilt : {&hingedPair, &hingedOne})
    {
        const OpenYAMM::Game::IndoorMapData &map = *pBuilt->loaded.indoor;

        for (const YAML::Node &door : pBuilt->doors)
        {
            for (const uint16_t faceId : door["face_ids"].as<std::vector<uint16_t>>())
            {
                const OpenYAMM::Game::IndoorFace &face = map.faces[faceId];
                CHECK(face.facetType == 0);
                REQUIRE(face.roomBehindNumber != face.roomNumber);
                REQUIRE(face.roomBehindNumber < map.sectors.size());
                const std::vector<uint16_t> &behind = map.sectors[face.roomBehindNumber].faceIds;
                const std::vector<uint16_t> &own = map.sectors[face.roomNumber].faceIds;
                CHECK(std::find(behind.begin(), behind.end(), faceId) != behind.end());
                CHECK(std::find(own.begin(), own.end(), faceId) != own.end());
            }
        }
    }

    // The wing picture lies on the left leaf as it is and mirrored on the right: the texels of the two leaves'
    // fronts run opposite ways along the wall.
    {
        const OpenYAMM::Game::IndoorMapData &map = *hingedPair.loaded.indoor;
        std::array<double, 2> uSlope = {0.0, 0.0};

        for (size_t leafIndex = 0; leafIndex < 2; ++leafIndex)
        {
            for (const uint16_t faceId : hingedPair.door(int(leafIndex) + 1)["face_ids"].as<std::vector<uint16_t>>())
            {
                const OpenYAMM::Game::IndoorFace &face = map.faces[faceId];

                // A front: a face of the leaf facing room a (-x), full height.
                if (face.vertexIndices.size() != 4 || face.textureName != "t1door" || face.textureUs.size() != 4)
                {
                    continue;
                }

                double lowY = 1e9;
                double highY = -1e9;
                double uAtLow = 0.0;
                double uAtHigh = 0.0;
                double x = 0.0;

                for (size_t corner = 0; corner < 4; ++corner)
                {
                    const OpenYAMM::Game::IndoorVertex &vertex = map.vertices[face.vertexIndices[corner]];
                    x = vertex.x;

                    if (vertex.y < lowY)
                    {
                        lowY = vertex.y;
                        uAtLow = face.textureUs[corner];
                    }

                    if (vertex.y > highY)
                    {
                        highY = vertex.y;
                        uAtHigh = face.textureUs[corner];
                    }
                }

                if (x < 528.0 && highY - lowY > 32.0)
                {
                    uSlope[leafIndex] = uAtHigh - uAtLow;
                }
            }
        }

        CHECK(uSlope[0] != doctest::Approx(0.0));
        CHECK(uSlope[0] * uSlope[1] < 0.0);
    }

    CHECK(issueText(buildMoving(DoorRooms, doorObjects("kind: hinged, leaves: 2, hinge: right"), DoorWiring).rooms)
        .find("drop `hinge`") != std::string::npos);
    CHECK(issueText(buildMoving(DoorRooms, doorObjects("kind: hinged, leaves: 2, tile: true"), DoorWiring).rooms)
        .find("is for sliding doors") != std::string::npos);
    CHECK(issueText(buildMoving(DoorRooms, doorObjects("kind: hinged, pictures: [[{texture: t1door, size: [64, 192]}]]"), DoorWiring)
        .rooms).find("is for sliding doors") != std::string::npos);
}

TEST_CASE("door pictures: a wing alone on a wide leaf, a pair of unmirrored wings, a door picture tiled")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[544, 64], [800, 64], [800, 448], [544, 448]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 256, height: 192}\n";
    const std::string wiring = "format: 0\nevents:\n  - {id: evt:door, preset: door, source: door:ab}\n";
    TextureFitData data;
    data.sizes = {{"wingl", {128, 256}}, {"wingr", {128, 256}}, {"plain", {64, 128}}};
    data.classTexts = {"textures:\n  wingl: {class: feature, door: wing, twin: wingr, mirror: 0.2}\n"
        "  wingr: {class: feature, door: wing, twin: wingl, mirror: 0.2}\n"
        "  plain: {class: feature, door: single, mirror: 0.6}\n"};
    const auto codes = [&](const std::string &fields)
    {
        const BuiltMoving built = buildMoving(rooms, doorObjects(fields), wiring);
        INFO(issueText(built.rooms));
        REQUIRE(built.rooms.built);
        std::vector<std::string> found;

        for (const AuditFinding &finding : auditDoorTextures(built.loaded, data))
        {
            found.push_back(finding.code);
        }

        return found;
    };

    // One wing stretched over the whole 256-wide opening.
    CHECK(codes("kind: slide_up, surface: {texture: wingl, size: [128, 256]}")
        == std::vector<std::string>{"doors.half_wing"});
    // A hinged pair of the wing: the right leaf mirrored, nothing to say.
    CHECK(codes("kind: hinged, leaves: 2, surface: {texture: wingl, size: [128, 256]}").empty());
    // Two leaves showing the wing the same way round.
    CHECK(codes("kind: hinged, leaves: 2, pictures: [[{texture: wingl, size: [128, 256]}, {texture: wingl, "
        "size: [128, 256]}]]") == std::vector<std::string>{"doors.wing_unmirrored"});
    // The left and right wings, one on each leaf: right.
    CHECK(codes("kind: slide_left, leaves: 2, pictures: [[{texture: wingl, size: [128, 256]}, {texture: wingr, "
        "size: [128, 256]}]]").empty());
    // A door picture laid at its own size: four times across the opening.
    CHECK(codes("kind: slide_up, tile: true, surface: {texture: plain, size: [64, 128]}")
        == std::vector<std::string>{"doors.tiled"});
}

TEST_CASE("texture fit: a window tiled or cut, a band up a wall, a tile with seams, unlike borders and walls")
{
    LoadedMap map;
    map.world = "xeen";
    map.indoor.emplace();
    OpenYAMM::Game::IndoorMapData &indoor = *map.indoor;
    // A face upright in the plane y = `y` from x0 to x1 and z0 to z1, its texels u0..u1 left to right, v0 at the top.
    const auto quad = [&indoor](int y, int x0, int x1, int z0, int z1, const std::string &texture, int u0, int u1,
                          int v0, int v1)
    {
        OpenYAMM::Game::IndoorFace face;
        const uint16_t first = static_cast<uint16_t>(indoor.vertices.size());
        indoor.vertices.push_back({x0, y, z0});
        indoor.vertices.push_back({x1, y, z0});
        indoor.vertices.push_back({x1, y, z1});
        indoor.vertices.push_back({x0, y, z1});
        face.vertexIndices = {first, uint16_t(first + 1), uint16_t(first + 2), uint16_t(first + 3)};
        face.textureUs = {int16_t(u0), int16_t(u1), int16_t(u1), int16_t(u0)};
        face.textureVs = {int16_t(v1), int16_t(v1), int16_t(v0), int16_t(v0)};
        face.textureName = texture;
        indoor.faces.push_back(face);
    };
    TextureFitData data;
    data.sizes = {{"stone", {128, 128}}, {"win", {128, 128}}, {"band", {128, 32}}, {"seamy", {128, 128}},
        {"redwin", {128, 128}}, {"grey", {128, 128}}, {"blue", {128, 128}}, {"panel", {128, 256}},
        {"eaves", {128, 256}}, {"timber", {128, 256}}};
    data.classTexts = {"textures:\n"
        "  stone: {class: tile, tiles: [true, true], border: [100, 100, 100]}\n"
        "  win: {class: feature, tiles: [true, true], border: [100, 100, 100]}\n"
        "  band: {class: trim_u, tiles: [true, false], border: [100, 100, 100]}\n"
        "  seamy: {class: tile, tiles: [false, true], border: [100, 100, 100]}\n"
        "  redwin: {class: feature, tiles: [true, true], border: [200, 0, 0]}\n"
        "  grey: {class: tile, tiles: [true, true], border: [100, 100, 100]}\n"
        "  blue: {class: tile, tiles: [true, true], border: [20, 20, 200]}\n"
        "  panel: {class: trim_u, tiles: [true, false], border: [100, 100, 100]}\n"
        "  eaves: {class: trim_u, tiles: [true, false], border: [100, 100, 100], storey_stack: edge}\n"
        "  timber: {class: trim_u, tiles: [true, false], border: [100, 100, 100], storey_stack: module}\n"};
    // A plain wall: four by two copies, nothing to say.
    quad(0, 0, 512, 0, 256, "stone", 0, 512, 0, 256);
    // A window laid along a 512-wide face: four copies.
    quad(1000, 0, 512, 0, 128, "win", 0, 512, 0, 128);
    // A window whose picture starts in its middle: two halves.
    quad(2000, 0, 128, 0, 128, "win", 64, 192, 0, 128);
    // A window split over two faces that continue its picture: whole.
    quad(3000, 0, 64, 0, 128, "win", 0, 64, 0, 128);
    quad(3000, 64, 128, 0, 128, "win", 64, 128, 0, 128);
    // A band laid up a 128-high face: four times.
    quad(4000, 0, 128, 0, 128, "band", 0, 128, 0, 128);
    // A tile whose sides do not meet laid four times across.
    quad(5000, 0, 512, 0, 128, "seamy", 0, 512, 0, 128);
    // A red-framed window between grey wall, and the grey wall meeting a blue one side by side.
    quad(6000, 0, 128, 0, 128, "grey", 0, 128, 0, 128);
    quad(6000, 128, 256, 0, 128, "redwin", 0, 128, 0, 128);
    quad(6000, 256, 384, 0, 128, "grey", 0, 128, 0, 128);
    quad(6000, 384, 512, 0, 128, "blue", 0, 128, 0, 128);
    // A storey panel stacked whole on two storeys: a warning; shifted half a storey: a band cut, an error.
    quad(7000, 0, 128, 0, 512, "panel", 0, 128, 0, 512);
    quad(8000, 0, 128, 0, 512, "panel", 0, 128, 128, 640);
    // D-41: an eaves panel stacked so is an error; a half-timber module stacked so is right.
    quad(9000, 0, 128, 0, 512, "eaves", 0, 128, 0, 512);
    quad(10000, 0, 128, 0, 512, "timber", 0, 128, 0, 512);
    std::multiset<std::string> found;
    std::multiset<std::string> stackedSeverities;

    for (const AuditFinding &finding : auditTextureFit(map, data))
    {
        INFO(finding.message);
        found.insert(finding.code);

        if (finding.code == "textures.storey_stacked")
        {
            stackedSeverities.insert(finding.severity);
        }
    }

    CHECK(stackedSeverities == std::multiset<std::string>{"warning", "error"});

    CHECK(found == std::multiset<std::string>{"textures.feature_repeated", "textures.feature_cut",
        "textures.trim_tiled", "textures.trim_tiled", "textures.tile_seams", "textures.feature_border",
        "textures.family_switch", "textures.storey_stacked", "textures.storey_stacked"});
}

TEST_CASE("an open leaf that would stand in another opening or in a room is refused with the ways out")
{
    // The Lincoln's lift doorways: one above the other in one wall, the lower one with a door.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:hall, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 896}\n"
        "  - {id: room:shaft, outline: [[-448, 384], [-192, 384], [-192, 640], [-448, 640]], floor: 0,\n"
        "     ceiling: 896}\n"
        "openings:\n"
        "  - {id: open:low, from: room:shaft, to: room:hall, width: 192, height: 256}\n"
        "  - {id: open:high, from: room:shaft, to: room:hall, width: 192, height: 256, sill: 448}\n";
    const auto objects = [](const std::string &fields)
    {
        return "format: 0\nstart: {room: room:hall}\ndoors:\n  - {id: door:low, opening: open:low, " + fields + "}\n";
    };
    const std::string refused = issueText(buildMoving(rooms, objects("kind: slide_up")).rooms);
    CHECK(refused.find("the open leaf of door:low would stand in open:high") != std::string::npos);
    CHECK(refused.find("it stands from 258 to 514") != std::string::npos);
    CHECK(refused.find("`leaves: 2`") != std::string::npos);
    // Every way out the message names builds.
    for (const char *pFields : {"kind: slide_down", "kind: slide_left", "kind: slide_up, leaves: 2"})
    {
        const BuiltMoving built = buildMoving(rooms, objects(pFields));
        INFO(pFields << "\n" << issueText(built.rooms));
        CHECK(built.rooms.built);
    }

    // A sideways leaf where the wall beside the doorway ends in another room: room c begins 16 behind room a's
    // wall, right where the leaf would stand open.
    const std::string beside =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 768], [0, 768]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[576, 128], [832, 128], [832, 320], [576, 320]], floor: 0, ceiling: 256}\n"
        "  - {id: room:c, outline: [[528, 336], [832, 336], [832, 640], [528, 640]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n"
        "  - {id: open:ac, from: room:a, to: room:c, width: 128, height: 192}\n";
    const std::string inRoom = issueText(buildMoving(beside, doorObjects("kind: slide_left")).rooms);
    CHECK(inRoom.find("the open leaf of door:ab would stand inside room:c") != std::string::npos);
    CHECK(inRoom.find("narrow the opening") != std::string::npos);
    const BuiltMoving otherWay = buildMoving(beside, doorObjects("kind: slide_right"));
    INFO(issueText(otherWay.rooms));
    CHECK(otherWay.rooms.built);
}

namespace
{
const char *const MoverRooms =
    "rooms:\n"
    "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 256], [0, 256]], floor: 0, ceiling: 384}\n";

const char *const MoverObjects =
    "format: 0\n"
    "start: {room: room:a, at: [128, 128]}\n"
    "movers:\n"
    "  - {id: mover:a_gate, room: room:a, at: [512, 128], size: [64, 256], height: 384, travel: [0, 0, -386]}\n"
    "  - {id: mover:b_slab, room: room:a, at: [256, 64], size: [128, 64], bottom: 100, height: 16,\n"
    "     travel: [0, 128, 0], speed: 64, kerbs: {height: 24, width: 16}, auto_return_seconds: 5}\n"
    "  - {id: mover:c_grow, room: room:a, at: [800, 200], size: [64, 64], bottom: 100, height: 16,\n"
    "     travel: [128, 0, 0], stretch: true, state: end}\n"
    "switches:\n"
    "  - {id: switch:lever, room: room:a, wall: south, along: 0.1}\n";

const char *const MoverWiring =
    "format: 0\nevents:\n"
    "  - {id: evt:lever, preset: switch, source: switch:lever, opens: [mover:a_gate], closes: [mover:b_slab],\n"
    "     toggles: [mover:c_grow]}\n"
    "  - {id: evt:slab, preset: switch, source: mover:b_slab, toggles: [mover:b_slab]}\n";

std::string moverIssue(const std::string &from, const std::string &to)
{
    std::string objects = MoverObjects;
    const size_t place = objects.find(from);
    REQUIRE(place != std::string::npos);
    objects.replace(place, from.size(), to);
    return issueText(buildMoving(MoverRooms, objects, MoverWiring).rooms);
}
}

TEST_CASE("a mover travels along a line: it blocks where it stands, events move it like a door, one may stretch")
{
    const BuiltMoving built = buildMoving(MoverRooms, MoverObjects, MoverWiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    REQUIRE(built.doors.size() == 3);
    const int closed = 2;
    const int open = 0;

    // The gate block: drawn standing from floor to ceiling, shut; open it has sunk 386, its top 2 under the floor.
    CHECK(built.direction(1) == std::array<int, 3>{0, 0, 65536});
    CHECK(built.door(1)["move_length"].as<int>() == 386);
    CHECK(built.door(1)["state"].as<int>() == closed);
    int highest = -10000;

    for (const YAML::Node &z : built.door(1)["z_offsets"])
    {
        highest = std::max(highest, z.as<int>());
    }

    CHECK(highest == -2);
    // It stands from wall to wall: the walk along the room stops at it and passes once it is out of the way.
    CHECK_FALSE(built.walks({128.0f, 128.0f, 0.0f}, {896.0f, 128.0f, 0.0f}, false));
    CHECK(built.walks({128.0f, 128.0f, 0.0f}, {896.0f, 128.0f, 0.0f}, true));

    // The slab slides 128 toward +y with its kerbs and returns by itself.
    CHECK(built.direction(2) == std::array<int, 3>{0, -65536, 0});
    CHECK(built.door(2)["move_length"].as<int>() == 128);
    CHECK(built.door(2)["open_speed"].as<int>() == 64);
    CHECK(built.door(2)["mover"]["auto_close_seconds"].as<double>() == doctest::Approx(5.0));
    // The kerbs stand on its top (116) along its long sides: 16 wide, 24 high, moving with it.
    CHECK(built.rooms.hasVertex(192, 48, 140));
    CHECK(built.rooms.hasVertex(320, 96, 140));
    CHECK(built.rooms.hasVertex(192, 80, 140));
    CHECK(built.door(2)["vertex_ids"].size() == 20);
    // It has an underside (100) and a top to stand on (116).
    CHECK(built.rooms.levelsOver(1, 256.0, 64.0, true) == std::vector<int>{0, 116});

    // The stretching block starts at its end: only the four corners of its east end face move, by 128.
    CHECK(built.door(3)["state"].as<int>() == open);
    CHECK(built.direction(3) == std::array<int, 3>{-65536, 0, 0});
    REQUIRE(built.door(3)["vertex_ids"].size() == 4);

    for (size_t index = 0; index < 4; ++index)
    {
        const OpenYAMM::Game::IndoorVertex &vertex =
            built.rooms.map.vertices[built.door(3)["vertex_ids"][index].as<size_t>()];
        CHECK(vertex.x == 832);
        CHECK(built.door(3)["x_offsets"][index].as<int>() == 960);
    }

    // Events name movers in the same lists as doors.
    CHECK(built.lua.find("evt.SetDoorState(1, DoorAction.Open)") != std::string::npos);
    CHECK(built.lua.find("evt.SetDoorState(2, DoorAction.Close)") != std::string::npos);
    CHECK(built.lua.find("evt.SetDoorState(3, DoorAction.Trigger)") != std::string::npos);
    CHECK(built.lua.find("evt.SetDoorState(2, DoorAction.Trigger)") != std::string::npos);

    // Refusals say what to change.
    // (Since 2026-11-13 a mover may pass into a wall or the ceiling at one end of its way; it is refused when it
    // lies wholly in its room at neither.)
    CHECK(moverIssue("at: [256, 64], size: [128, 64], bottom: 100, height: 16,\n     travel: [0, 128, 0]",
        "at: [256, 16], size: [128, 64], bottom: 100, height: 16,\n     travel: [0, 400, 0]")
        .find("a mover stays in its room") != std::string::npos);
    CHECK(moverIssue("travel: [0, 0, -386]", "travel: [0, 0, 0]").find("the travel is nothing") != std::string::npos);
    CHECK(moverIssue("travel: [0, 0, -386]", "travel: [0, 0, -384]").find("lies in the plane of the floor")
        != std::string::npos);
    CHECK(moverIssue("height: 384, travel: [0, 0, -386]", "height: 400, travel: [0, 0, 8]")
        .find("above the ceiling of room:a") != std::string::npos);
    CHECK(moverIssue("travel: [128, 0, 0], stretch: true", "travel: [128, 0, 16], stretch: true")
        .find("a stretching block grows along one of its own axes") != std::string::npos);
    CHECK(moverIssue("kerbs: {height: 24, width: 16}", "kerbs: {height: 24, width: 40}")
        .find("do not fit on a block 64 across") != std::string::npos);
    CHECK(moverIssue("at: [800, 200], size: [64, 64]", "outline: [[768, 168], [832, 168], [832, 232]]")
        .find("belong to a block given by `at` and `size`") != std::string::npos);
    std::string wiring = MoverWiring;
    wiring.replace(wiring.find("opens: [mover:a_gate]"), 21, "opens: [mover:none]");
    CHECK(issueText(buildMoving(MoverRooms, MoverObjects, wiring).rooms)
        .find("there is no door, lift or mover mover:none") != std::string::npos);
}

// What the engine draws on a sliding part's face while the map stands as drawn, against the texels the build
// stored for it: the largest difference in texels. The engine's rule (game/indoor/IndoorRenderer.cpp) lays such a
// face out from its place in the world at one texel per unit; with TextureMoveByDoor it takes the place the face has
// when the door is open and adds the face's delta. -1 where the face has no such flag.
double movingFaceTexelError(const BuiltMoving &built, const YAML::Node &door, size_t faceOffset)
{
    const OpenYAMM::Game::IndoorMapData &map = built.rooms.map;
    const OpenYAMM::Game::IndoorFace &face = map.faces[door["face_ids"][faceOffset].as<size_t>()];

    if (!face.planeNormal || (face.attributes & 0x00040000u) == 0
        || door["delta_us"][faceOffset].as<int>() != face.textureDeltaU
        || door["delta_vs"][faceOffset].as<int>() != face.textureDeltaV)
    {
        return -1.0;
    }

    const std::array<double, 3> direction = {door["direction"][0].as<int>() / 65536.0,
        door["direction"][1].as<int>() / 65536.0, door["direction"][2].as<int>() / 65536.0};
    const OpenYAMM::Game::IndoorVertex &moved = map.vertices[door["vertex_ids"][0].as<size_t>()];
    const double distance = (moved.x - door["x_offsets"][0].as<int>()) * direction[0]
        + (moved.y - door["y_offsets"][0].as<int>()) * direction[1]
        + (moved.z - door["z_offsets"][0].as<int>()) * direction[2];
    // Walls run along the wall and down, floors and ceilings along x and against y.
    const bool wall = face.facetType == 1;
    const std::array<double, 3> normal = {(*face.planeNormal)[0] / 65536.0, (*face.planeNormal)[1] / 65536.0, 0.0};
    const std::array<double, 3> axisU = wall ? std::array<double, 3>{0.0 - normal[1], normal[0], 0.0}
        : std::array<double, 3>{1.0, 0.0, 0.0};
    const std::array<double, 3> axisV = wall ? std::array<double, 3>{0.0, 0.0, -1.0}
        : std::array<double, 3>{0.0, -1.0, 0.0};
    double worst = 0.0;

    for (size_t index = 0; index < face.vertexIndices.size(); ++index)
    {
        const OpenYAMM::Game::IndoorVertex &vertex = map.vertices[face.vertexIndices[index]];
        const double drawnU = vertex.x * axisU[0] + vertex.y * axisU[1] + vertex.z * axisU[2]
            - (direction[0] * axisU[0] + direction[1] * axisU[1] + direction[2] * axisU[2]) * distance
            + face.textureDeltaU;
        const double drawnV = vertex.x * axisV[0] + vertex.y * axisV[1] + vertex.z * axisV[2]
            - (direction[0] * axisV[0] + direction[1] * axisV[1] + direction[2] * axisV[2]) * distance
            + face.textureDeltaV;
        worst = std::max(worst, std::abs(drawnU - (face.textureDeltaU + face.textureUs[index])));
        worst = std::max(worst, std::abs(drawnV - (face.textureDeltaV + face.textureVs[index])));
    }

    return worst;
}

TEST_CASE("the texture of a sliding part rides with it, where the project put it")
{
    // The gate block, the sliding slab with its kerbs and the stretching block of the mover case: every face at the
    // texture's own scale.
    const BuiltMoving built = buildMoving(MoverRooms, MoverObjects, MoverWiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    size_t faces = 0;
    size_t offGrid = 0;

    for (const YAML::Node &door : built.doors)
    {
        for (size_t faceOffset = 0; faceOffset < door["face_ids"].size(); ++faceOffset)
        {
            INFO("door " << door["door_id"].as<int>() << " face " << door["face_ids"][faceOffset].as<int>());
            const double error = movingFaceTexelError(built, door, faceOffset);
            CHECK(error >= 0.0);
            CHECK(error <= 1.0);
            const OpenYAMM::Game::IndoorFace &face =
                built.rooms.map.faces[door["face_ids"][faceOffset].as<size_t>()];
            offGrid += face.textureDeltaU % 64 != 0 || face.textureDeltaV % 64 != 0 ? 1 : 0;
            ++faces;
        }
    }

    CHECK(faces >= 18);
    // The case would also pass with every delta at nothing if the parts happened to stand on the grid.
    CHECK(offGrid > 0);
}

TEST_CASE("a lift may be a thin floor, and a lift under a hole in the floor above rises through it")
{
    // The Lincoln's pod bay: a shaft whose whole ceiling is a hole in the deck's floor.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:deck, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 512, ceiling: 896}\n"
        "  - {id: room:shaft, outline: [[384, 384], [640, 384], [640, 640], [384, 640]], floor: 0, ceiling: 512}\n"
        "openings:\n"
        "  - {id: open:well, from: room:deck, to: room:shaft, in: floor}\n";
    const auto objects = [](const std::string &fields)
    {
        return "format: 0\nstart: {room: room:deck, at: [128, 128]}\nlifts:\n"
            "  - {id: lift:shaft, room: room:shaft, size: [256, 256], travel: 512" + fields + "}\n";
    };
    // The shaft's own ceiling is 512, the deck's 896: raised 512 the lift's top has 376 above it.
    const BuiltMoving solid = buildMoving(rooms, objects(""));
    INFO(issueText(solid.rooms));
    REQUIRE(solid.rooms.built);
    CHECK(solid.direction(1) == std::array<int, 3>{0, 0, -65536});
    CHECK(solid.door(1)["move_length"].as<int>() == 512);
    // A solid lift is a block as tall as its travel, sunk under the floor.
    CHECK(solid.rooms.hasVertex(384, 384, -512));

    // A thin lift is a floor 16 thick with an underside; nothing reaches down the shaft.
    const BuiltMoving thin = buildMoving(rooms, objects(", thickness: 16"));
    INFO(issueText(thin.rooms));
    REQUIRE(thin.rooms.built);
    CHECK(thin.rooms.hasVertex(384, 384, 8));
    CHECK(thin.rooms.hasVertex(384, 384, -8));
    CHECK_FALSE(thin.rooms.hasVertex(384, 384, -512));
    CHECK(thin.door(1)["face_ids"].size() == solid.door(1)["face_ids"].size() + 1);

    // Under a hole it does not fit, the lower room's ceiling still stops it, and the message says so.
    std::string partly = rooms;
    partly.replace(partly.find("in: floor}"), 10, "in: floor, at: [512, 512], size: [128, 128]}");
    const std::string refused = issueText(buildMoving(partly, objects("")).rooms);
    CHECK(refused.find("the lift would raise the party into the ceiling of room:shaft") != std::string::npos);
    CHECK(refused.find("only partly under the hole open:well") != std::string::npos);
    // Too high for the room above as well.
    CHECK(issueText(buildMoving(rooms, objects(", speed: 50")).rooms).empty());
    std::string high = objects("");
    high.replace(high.find("travel: 512"), 11, "travel: 700");
    CHECK(issueText(buildMoving(rooms, high).rooms).find("the lift would raise the party into the ceiling")
        != std::string::npos);
}

// The measuring tools (2026-11-12): compare's stand points, floor edges, seams, shut blocks and starting poses; the
// walk of solve and audit --reach; probe; the handlers' sandbox; point lists in canonical form.

#include "core/EventFlow.h"

namespace
{
// A room 1024 by 768 and 1024 high with a ledge 640 up along its east side (the party starts on it and can drop
// off) and a panel sunk 64 into its floor; `west`: the ledge's west edge.
std::string ledgeRooms(int west, bool withLedge = true, bool withPanel = true)
{
    const std::string edge = std::to_string(west);
    return std::string("rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]]\n"
        "    floor: 0\n"
        "    ceiling: 1024\n"
        "    levels:\n")
        + (withLedge ? "      - {id: level:ledge, outline: [[" + edge + ", 128], [896, 128], [896, 384], [" + edge
                + ", 384]], floor: 640}\n" : "")
        + (withPanel ? "      - {id: level:panel, outline: [[128, 256], [384, 256], [384, 512], [128, 512]], "
                       "floor: -64}\n" : "");
}

LoadedMap builtLedgeMap(int west, bool withLedge = true, bool withPanel = true)
{
    const BuiltMoving built = buildMoving(ledgeRooms(west, withLedge, withPanel),
        std::string("format: 0\nstart: {room: room:a, at: ") + (withLedge ? "[704, 256]" : "[64, 64]") + "}\n");
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    return built.loaded;
}

// The reading of before these fixes.
CompareOptions oldCompareReading(double step)
{
    CompareOptions options;
    options.step = step;
    options.pointsOnGrid = true;
    options.exactFloorEdges = true;
    options.openSeams = true;
    options.thinBlocksOnly = true;
    options.storedPoses = true;
    return options;
}

// The event number some face of the map is bound to.
int boundEvent(const LoadedMap &map)
{
    for (const OpenYAMM::Game::IndoorFace &face : map.indoor->faces)
    {
        if (face.cogTriggered != 0)
        {
            return face.cogTriggered;
        }
    }

    return 0;
}

std::string flowOf(int eventId, const std::string &paths)
{
    return "[{\"event\": " + std::to_string(eventId) + ", \"title\": \"\", \"paths\": [" + paths + "]}]";
}

size_t sectorsReached(const SolveResult &solved)
{
    size_t reached = 0;

    for (const SolveWave &wave : solved.waves)
    {
        reached += wave.sectors.size();
    }

    return reached;
}

// A corridor with a slot across its floor from wall to wall (16 of floor left beside it, which no body passes), a
// room under the slot and a room at the corridor's far end.
SolveResult solveSlot(int slotWidth)
{
    const BuiltMoving built = buildMoving(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 256], [0, 256]], floor: 0, ceiling: 256}\n"
        "  - {id: room:b, outline: [[384, 0], [640, 0], [640, 256], [384, 256]], floor: -400, ceiling: -32}\n"
        "  - {id: room:c, outline: [[1056, 0], [1312, 0], [1312, 256], [1056, 256]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:slot, from: room:a, to: room:b, in: floor, at: [512, 128], size: ["
            + std::to_string(slotWidth) + ", 224]}\n"
        "  - {id: open:ac, from: room:a, to: room:c, width: 96, height: 192}\n",
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n");
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    return solveMap(built.loaded, "[]");
}

bool reachedSector(const SolveResult &solved, size_t sector)
{
    return std::any_of(solved.waves.begin(), solved.waves.end(), [sector](const SolveWave &wave)
    {
        return std::find(wave.sectors.begin(), wave.sectors.end(), sector) != wave.sectors.end();
    });
}
}

TEST_CASE("a ray into the seam of two faces meets one of them, and a real gap stays open")
{
    // A level ceiling and a steep one that meet along x = 0 at height 100. They are flattened on different axes, and
    // the even-odd test gives a point of the seam to neither: a look straight up from under it went through.
    RayScene scene;
    REQUIRE(scene.addFace({{-100.0, -50.0, 100.0}, {-100.0, 50.0, 100.0}, {0.0, 50.0, 100.0}, {0.0, -50.0, 100.0}},
        {0.0, 0.0, -1.0}, 1, "flat"));
    REQUIRE(scene.addFace({{0.0, -50.0, 100.0}, {0.0, 50.0, 100.0}, {60.0, 50.0, 20.0}, {60.0, -50.0, 20.0}},
        {-0.8, 0.0, -0.6}, 2, "steep"));
    scene.build();
    const RayHit seam = scene.cast({0.0, 0.0, 0.0}, {0.0, 0.0, 1.0}, 4096.0);
    CHECK(seam.hit);
    CHECK(seam.distance == doctest::Approx(100.0));
    scene.setSeamTolerance(0.0);
    CHECK_FALSE(scene.cast({0.0, 0.0, 0.0}, {0.0, 0.0, 1.0}, 4096.0).hit);

    // Two ceilings 4 apart: the slit between them is open, and so is the room beside the last edge.
    RayScene slit;
    REQUIRE(slit.addFace({{-100.0, -50.0, 100.0}, {-100.0, 50.0, 100.0}, {-2.0, 50.0, 100.0}, {-2.0, -50.0, 100.0}},
        {0.0, 0.0, -1.0}, 1, "west"));
    REQUIRE(slit.addFace({{2.0, -50.0, 100.0}, {2.0, 50.0, 100.0}, {100.0, 50.0, 100.0}, {100.0, -50.0, 100.0}},
        {0.0, 0.0, -1.0}, 2, "east"));
    slit.build();
    CHECK_FALSE(slit.cast({0.0, 0.0, 0.0}, {0.0, 0.0, 1.0}, 4096.0).hit);
    CHECK_FALSE(slit.cast({101.0, 0.0, 0.0}, {0.0, 0.0, 1.0}, 4096.0).hit);
    CHECK(slit.cast({50.0, 0.0, 0.0}, {0.0, 0.0, 1.0}, 4096.0).sourceId == 2);

    // A floor's edge is part of the floor: on the edge of a step both floors are found, as the game's walk has it.
    RayScene step;
    REQUIRE(step.addFace({{0.0, 0.0, 0.0}, {100.0, 0.0, 0.0}, {100.0, 100.0, 0.0}, {0.0, 100.0, 0.0}},
        {0.0, 0.0, 1.0}, 1, "low"));
    REQUIRE(step.addFace({{100.0, 0.0, 64.0}, {200.0, 0.0, 64.0}, {200.0, 100.0, 64.0}, {100.0, 100.0, 64.0}},
        {0.0, 0.0, 1.0}, 2, "high"));
    step.build();
    CHECK(step.heightsAt(100.0, 50.0).size() == 2);
    CHECK(step.heightsAt(100.0, 50.0, false).size() == 1);
    CHECK(step.heightsAt(100.0, 100.0).size() == 2);
    CHECK(step.heightsAt(100.0, 100.0, false).empty());
    CHECK(step.heightsAt(101.0, 50.0).size() == 1);
}

TEST_CASE("points on a ledge's or a sunken panel's edge read alike in two like maps, and a ledge that differs is found")
{
    const LoadedMap original = builtLedgeMap(512);
    CompareOptions options;
    options.step = 128.0;
    CompareResult same;
    std::string errorMessage;
    REQUIRE(compareMaps(original, builtLedgeMap(512), options, same, errorMessage));
    CHECK(same.points.size() >= 30);
    CHECK(same.missingFloor.empty());
    CHECK(same.extraFloor.empty());
    CHECK(same.meanFloorDelta == doctest::Approx(0.0));
    CHECK(same.score == doctest::Approx(1.0));
    // Grid points on the ledge's and the panel's edges were moved clear of them.
    CHECK(same.movedPoints > 0);

    // The reading before: the same two maps differed, at points exactly on the ledge's east and north edges.
    CompareResult before;
    REQUIRE(compareMaps(original, builtLedgeMap(512), oldCompareReading(128.0), before, errorMessage));
    CHECK_FALSE(before.missingFloor.empty());
    CHECK(before.score < 0.9);

    for (const size_t index : before.missingFloor)
    {
        CHECK((before.points[index].x == 896.0 || before.points[index].y == 384.0));
    }

    // A ledge that ends 128 short: the strip it lacks has no floor, and only that strip (a point exactly on the
    // shorter ledge's new edge still stands on it).
    CompareResult shorter;
    REQUIRE(compareMaps(original, builtLedgeMap(640), options, shorter, errorMessage));
    REQUIRE_FALSE(shorter.missingFloor.empty());

    for (const ComparePoint &point : shorter.points)
    {
        if (point.z == 640.0)
        {
            CHECK(point.hasFloor == (point.x >= 640.0));
        }
    }

    // No ledge at all: every point of it is missing.
    CompareResult none;
    REQUIRE(compareMaps(original, builtLedgeMap(512, false), options, none, errorMessage));
    size_t onLedge = 0;

    for (const ComparePoint &point : none.points)
    {
        onLedge += point.z == 640.0 ? 1 : 0;
        CHECK(point.hasFloor == (point.z != 640.0));
    }

    CHECK(onLedge >= 8);
    CHECK(none.missingFloor.size() == onLedge);

    // No panel: the points in it stand 64 higher, and nowhere else does a floor differ.
    CompareResult flat;
    REQUIRE(compareMaps(original, builtLedgeMap(512, true, false), options, flat, errorMessage));
    CHECK(flat.missingFloor.empty());
    size_t inPanel = 0;

    for (const ComparePoint &point : flat.points)
    {
        inPanel += point.z == -64.0 ? 1 : 0;
        CHECK(point.floorDelta == doctest::Approx(point.z == -64.0 ? 64.0 : 0.0));
    }

    CHECK(inPanel >= 1);

    // Every point that differs is written, by sector, with all that differs at it; the others are only counted.
    JsonWriter writer(true);
    writeComparePointsJson(flat, writer);
    const YAML::Node points = YAML::Load(writer.text());
    size_t differing = 0;

    for (const ComparePoint &point : flat.points)
    {
        differing += point.differences.empty() ? 0 : 1;
    }

    CHECK(differing > inPanel);
    CHECK(points["points"].as<size_t>() == flat.points.size());
    CHECK(points["differing_points"].as<size_t>() == differing);
    REQUIRE(points["sectors"].size() == 1);
    REQUIRE(points["sectors"][0]["differing"].size() == differing);
    const YAML::Node worst = points["sectors"][0]["differing"][0];
    CHECK(worst["at"].size() == 3);
    CHECK(worst["differs"].size() >= 1);
    CHECK(worst["score"].as<double>() < 1.0);
    CHECK(writer.text().find("the floor is 64 higher") != std::string::npos);
    JsonWriter missingWriter(true);
    writeComparePointsJson(none, missingWriter);
    CHECK(missingWriter.text().find("\"floor\": \"missing in the rebuild\"") != std::string::npos);
}

TEST_CASE("a stand point inside a block that is shut at the start is left out, also when the block stands askew")
{
    // A gate block set at 45 degrees across the room, shut; the walk with every door out of the way goes through
    // where it stands, and its box along the axes is 768 square: too wide for the test by boxes.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 896]}\nmovers:\n"
        "  - {id: mover:gate, room: room:a, outline: [[128, 256], [256, 128], [896, 768], [768, 896]], height: 384,\n"
        "     travel: [0, 0, -386]}\n";
    const BuiltMoving built = buildMoving(rooms, objects);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // Inside the block: between its long sides (x - y from -128 to 128) and its ends (x + y from 384 to 1664).
    const auto inside = [](const ComparePoint &point)
    {
        return std::abs(point.x - point.y) < 120.0 && point.x + point.y > 392.0 && point.x + point.y < 1656.0;
    };
    CompareOptions options;
    options.step = 64.0;
    CompareResult result;
    std::string errorMessage;
    REQUIRE(compareMaps(built.loaded, built.loaded, options, result, errorMessage));
    CHECK(result.points.size() > 100);
    CHECK(std::none_of(result.points.begin(), result.points.end(), inside));
    CHECK(result.score == doctest::Approx(1.0));
    options.thinBlocksOnly = true;
    CompareResult before;
    REQUIRE(compareMaps(built.loaded, built.loaded, options, before, errorMessage));
    CHECK(std::any_of(before.points.begin(), before.points.end(), inside));
}

TEST_CASE("moving parts are read as the map's load events leave them on a first visit")
{
    const BuiltMoving built = buildMoving(MoverRooms, MoverObjects, MoverWiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    const uint16_t open = static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Open);
    const uint16_t closed = static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Closed);
    // Event 7 runs on load: its first way through (every test answered no) opens the gate; the second does not count.
    const std::string flow =
        "[{\"event\": 7, \"title\": \"\", \"paths\": [{\"tests\": [{\"what\": \"qbit 5\", \"taken\": false}], "
        "\"effects\": [\"door 1 open\", \"door 3 toggle\"]}, {\"tests\": [{\"what\": \"qbit 5\", \"taken\": true}], "
        "\"effects\": [\"door 1 close\", \"door 2 close\"]}]},"
        " {\"event\": 8, \"title\": \"\", \"paths\": [{\"tests\": [], \"effects\": [\"door 2 close\"]}]}]";
    const OpenYAMM::Game::EventRuntimeState poses = posesAfterLoadEvents(*built.loaded.state, flow, {7});
    REQUIRE(poses.mechanisms.contains(1));
    CHECK(poses.mechanisms.at(1).state == open);
    CHECK(poses.mechanisms.at(1).currentDistance == doctest::Approx(0.0f));
    // Event 8 is no load event: the slab stays as the scene has it.
    CHECK_FALSE(poses.mechanisms.contains(2));
    // The third mover starts at its end (`state: end`): toggled, it stands at the other one.
    REQUIRE(poses.mechanisms.contains(3));
    const bool startsOpen = built.door(3)["state"].as<int>() == 0;
    CHECK(poses.mechanisms.at(3).state == (startsOpen ? closed : open));
    CHECK(posesAfterLoadEvents(*built.loaded.state, flow, {}).mechanisms.empty());
    CHECK(posesAfterLoadEvents(*built.loaded.state, flow, {8}).mechanisms.at(2).state == closed);
    CHECK(posesAfterLoadEvents(*built.loaded.state, flow, {8}).mechanisms.at(2).currentDistance
        == doctest::Approx(built.door(2)["move_length"].as<float>()));
}

TEST_CASE("solve follows a face an event makes untouchable, and shows a wave that opens more of one room")
{
    // The gate block from wall to wall of one room, and a lever on the party's side.
    const std::string wiring =
        "format: 0\nevents:\n  - {id: evt:lever, preset: switch, source: switch:lever, closes: [mover:b_slab]}\n";
    const BuiltMoving built = buildMoving(MoverRooms, MoverObjects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    const int lever = boundEvent(built.loaded);
    REQUIRE(lever != 0);
    std::string effects;

    for (const OpenYAMM::Game::MapDeltaDoor &door : built.loaded.state->doors)
    {
        for (const uint16_t faceId : door.faceIds)
        {
            if (door.doorId == 1)
            {
                effects += (effects.empty() ? "" : ", ") + std::string("\"SetFacetBit(-") + std::to_string(faceId)
                    + ", 536870912, 1)\"";
            }
        }
    }

    // Nothing moves the gate: one wave, the one room, and it is not all walked.
    const SolveResult shut = solveMap(built.loaded, "[]");
    REQUIRE(shut.ran);
    REQUIRE(shut.waves.size() == 1);
    CHECK(shut.waves[0].sectors == std::vector<size_t>{1});

    // The lever switches the block's faces off: no new sector, but clearly more of this one, and the cause is named.
    const SolveResult through =
        solveMap(built.loaded, flowOf(lever, "{\"tests\": [], \"effects\": [" + effects + "]}"));
    REQUIRE(through.waves.size() == 2);
    CHECK(through.waves[1].sectors.empty());
    REQUIRE(through.waves[1].extended.size() == 1);
    CHECK(through.waves[1].extended[0].first == 1);
    CHECK(through.waves[1].extended[0].second > 50);
    REQUIRE_FALSE(through.waves[1].causes.empty());
    CHECK(through.waves[1].causes[0].find("no longer blocks") != std::string::npos);

    // Switching the bit off again, or another bit, opens nothing.
    std::string other = effects;

    for (size_t at = other.find("536870912, 1"); at != std::string::npos; at = other.find("536870912, 1"))
    {
        other.replace(at, 12, "536870912, 0");
    }

    CHECK(solveMap(built.loaded, flowOf(lever, "{\"tests\": [], \"effects\": [" + other + "]}")).waves.size() == 1);

    // The walk with every door out of the way takes the event's faces for out of the way too.
    const ReachabilityResult reach =
        checkReachability(built.loaded, flowOf(lever, "{\"tests\": [], \"effects\": [" + effects + "]}"));
    CHECK(reach.ran);
    CHECK(reach.reachedDoorsOpen == 1);

    // Walk steps kept from the reach check for the solve, and from that solve for one over the gate left standing,
    // change nothing in what they find.
    const auto solveText = [](const SolveResult &result)
    {
        std::string text;

        for (const SolveWave &wave : result.waves)
        {
            text += "wave";

            for (const size_t sector : wave.sectors)
            {
                text += " " + std::to_string(sector);
            }

            for (const std::string &cause : wave.causes)
            {
                text += "; " + cause;
            }

            for (const std::pair<size_t, size_t> &more : wave.extended)
            {
                text += "; " + std::to_string(more.first) + "+" + std::to_string(more.second);
            }

            text += "\n";
        }

        for (const WalkStop &stop : result.stops)
        {
            text += "stop " + std::to_string(stop.fromSector) + " " + std::to_string(stop.toSector) + " "
                + stop.reason + "\n";
        }

        return text + std::to_string(result.neverReached.size()) + " " + std::to_string(result.nichesNotReached.size());
    };
    const std::string flow = flowOf(lever, "{\"tests\": [], \"effects\": [" + effects + "]}");
    WalkSteps walkSteps;
    const ReachabilityResult keptReach = checkReachability(built.loaded, flow, &walkSteps);
    CHECK(keptReach.cellsWalked == reach.cellsWalked);
    CHECK(keptReach.reachedAtStart == reach.reachedAtStart);
    CHECK(keptReach.reachedDoorsOpen == reach.reachedDoorsOpen);
    CHECK(solveText(solveMap(built.loaded, flow, &walkSteps)) == solveText(through));
    CHECK(solveText(solveMap(built.loaded, "[]", &walkSteps)) == solveText(shut));
}

TEST_CASE("solve names the opening that stops the walk, uses a door from the side its faces are not on, and waits")
{
    // Two rooms and a door as thick as the wall between them, drawn from the far room: its faces belong to that room.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[544, 64], [1056, 64], [1056, 448], [544, 448]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:b, to: room:a, width: 128, height: 192}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, thickness: 32}\n";
    BuiltMoving built = buildMoving(rooms, objects, DoorWiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    const int doorEvent = boundEvent(built.loaded);
    REQUIRE(doorEvent != 0);

    // No event moves the door: the far room is never reached, and the walk says where it stopped and at what.
    const SolveResult shut = solveMap(built.loaded, "[]");
    CHECK(shut.neverReached == std::vector<size_t>{2});
    REQUIRE(shut.stops.size() == 1);
    CHECK(shut.stops[0].fromSector == 1);
    CHECK(shut.stops[0].toSector == 2);
    CHECK(shut.stops[0].reason.find("door 1 stands in it (no event of the map moves it)") != std::string::npos);
    const ReachabilityResult reach = checkReachability(built.loaded);
    CHECK(reach.stops.empty());
    CHECK(reach.reachedDoorsOpen == 2);

    // Its event is bound to faces of the far room only; the party clicks the leaf standing in the near one: since
    // 2026-11-13 the event is filed under the room in front of the leaf's face it is clicked on.
    const SolveResult opened =
        solveMap(built.loaded, flowOf(doorEvent, "{\"tests\": [], \"effects\": [\"door 1 open\"]}"));
    REQUIRE(opened.waves.size() == 2);
    CHECK(opened.waves[1].sectors == std::vector<size_t>{2});
    REQUIRE_FALSE(opened.waves[1].causes.empty());
    CHECK(opened.waves[1].causes[0].find("in sector 1") != std::string::npos);
    CHECK(opened.stops.empty());

    // A branch that tests a map variable is taken only once an event the party can use has set it.
    const std::string conditional =
        "{\"tests\": [{\"what\": \"map_var 2 >= 1\", \"taken\": false}], \"effects\": []}, "
        "{\"tests\": [{\"what\": \"map_var 2 >= 1\", \"taken\": true}], \"effects\": [\"door 1 open\"]}";
    const SolveResult waits = solveMap(built.loaded, flowOf(doorEvent, conditional));
    CHECK(waits.neverReached == std::vector<size_t>{2});
    REQUIRE(waits.waiting.size() == 1);
    CHECK(waits.waiting[0].find("map_var 2 >= 1 (no event of the map sets it): door 1 open") != std::string::npos);

    // A second event, on the near room's floor, sets it: now the branch is taken. Set from the far room, it is not.
    for (const size_t sector : {size_t(1), size_t(2)})
    {
        for (OpenYAMM::Game::IndoorFace &face : built.loaded.indoor->faces)
        {
            if (face.cogTriggered == 99)
            {
                face.cogTriggered = 0;
            }
        }

        for (OpenYAMM::Game::IndoorFace &face : built.loaded.indoor->faces)
        {
            if (face.roomNumber == sector && !face.isPortal && face.facetType == 3 && face.cogTriggered == 0)
            {
                face.cogTriggered = 99;
                break;
            }
        }

        const std::string both = "[{\"event\": " + std::to_string(doorEvent) + ", \"title\": \"\", \"paths\": ["
            + conditional + "]}, {\"event\": 99, \"title\": \"\", \"paths\": [{\"tests\": [], \"effects\": "
              "[\"set map_var 2 = 1\"]}]}]";
        const SolveResult set = solveMap(built.loaded, both);
        CHECK(reachedSector(set, 2) == (sector == 1));

        if (sector == 2)
        {
            REQUIRE(set.waiting.size() == 1);
            CHECK(set.waiting[0].find("map_var 2 >= 1 (set only by events not used yet)") != std::string::npos);
        }
    }
}

TEST_CASE("the walk stands across a slot narrower than the body, strides a gap as the game does, falls where it fits")
{
    // 48 wide: the party walks over it to the far room and does not fall into the room below.
    const SolveResult narrow = solveSlot(48);
    CHECK(reachedSector(narrow, 3));
    CHECK_FALSE(reachedSector(narrow, 2));
    REQUIRE(narrow.stops.size() == 1);
    CHECK(narrow.stops[0].toSector == 2);
    CHECK(narrow.stops[0].reason.find("narrower than the body") != std::string::npos);
    // 112 wide: the body fits and may fall, and a party walking on gets across (144 at a walk).
    const SolveResult middling = solveSlot(112);
    CHECK(reachedSector(middling, 2));
    CHECK(reachedSector(middling, 3));
    CHECK(middling.stops.empty());
    // 176 wide: no way across; the far room is reached only in part of the corridor's sector, and the stop says so.
    const SolveResult wide = solveSlot(176);
    CHECK(reachedSector(wide, 2));
    CHECK_FALSE(reachedSector(wide, 3));
    REQUIRE(wide.stops.size() == 1);
    CHECK(wide.stops[0].reason.find("is reached only in part") != std::string::npos);
}

TEST_CASE("a cover over a hole holds the party until an event moves it, then the party gets down through the hole")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[256, 64], [768, 64], [768, 448], [256, 448]], floor: -512, ceiling: -32}\n"
        "openings:\n"
        "  - {id: open:hatch, from: room:a, to: room:b, in: floor, at: [512, 256], size: [256, 256]}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\nmovers:\n"
        "  - {id: mover:cover, room: room:a, at: [512, 256], size: [256, 256], bottom: -12, height: 16,\n"
        "     travel: [288, 0, 0]}\n"
        "switches:\n  - {id: switch:lever, room: room:a, wall: south, along: 0.1}\n";
    const std::string wiring =
        "format: 0\nevents:\n  - {id: evt:cover, preset: switch, source: switch:lever, opens: [mover:cover]}\n";
    const BuiltMoving built = buildMoving(rooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    const int lever = boundEvent(built.loaded);
    REQUIRE(lever != 0);
    const SolveResult covered = solveMap(built.loaded, "[]");
    CHECK(covered.neverReached == std::vector<size_t>{2});
    REQUIRE(covered.stops.size() == 1);
    CHECK(covered.stops[0].reason.find("covered") != std::string::npos);
    // The cover slides level and carries nothing: the party is not ridden anywhere, it drops where the cover was.
    const SolveResult moved = solveMap(built.loaded, flowOf(lever, "{\"tests\": [], \"effects\": [\"door 1 open\"]}"));
    REQUIRE(moved.waves.size() == 2);
    CHECK(moved.waves[1].sectors == std::vector<size_t>{2});
    CHECK(moved.neverReached.empty());
    // With every door out of the way the room below is reached as well.
    CHECK(checkReachability(built.loaded).reachedDoorsOpen == 2);
}

TEST_CASE("probe says whether its target is reached, not only that the planner found a route near it")
{
    const BuiltMoving built = buildMoving(DoorRooms, doorObjects("state: closed"), DoorWiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // Into the next room through the shut door: no. With the doors out of the way: yes.
    const std::string shut = probeWalk(built.loaded, {256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, false);
    CHECK(shut.find("target reached: no") != std::string::npos);
    const std::string open = probeWalk(built.loaded, {256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, true);
    CHECK(open.find("target reached: yes") != std::string::npos);
    // A target 80 behind the room's wall: within the planner's goal distance of a place it can reach, and the
    // planner calls that a route found; the probe says the route ends short and why the rest is not walked.
    const std::string wall = probeWalk(built.loaded, {256.0f, 256.0f, 0.0f}, {256.0f, 560.0f, 0.0f}, false);
    INFO(wall);
    CHECK(wall.find("target reached: no") != std::string::npos);
}

TEST_CASE("a handler that reckons with the party's size or an item count runs in the sandbox, both ways")
{
    // As 7d23's exit: every member must carry a wetsuit. The sandbox has no party; it answers four members, and a
    // count as a test, none or plenty.
    LoadedMap map;
    map.fullScriptSource =
        "evt.map[501] = function()\n"
        "    local count = evt.GetPartyMemberCount()\n"
        "    for member = 0, count - 1 do\n"
        "        if evt.PartyMemberItemCount(member, 1406) < 1 then\n"
        "            evt.StatusText(\"no\")\n"
        "            return\n"
        "        end\n"
        "    end\n"
        "    evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 0, \"out.odm\")\n"
        "end\n"
        "evt.map[502] = function()\n"
        "    local x, y, z = evt.GetPartyPosition()\n"
        "    if x + y + z + evt.CurrentGameMinutes() + evt.GetGlobalVar(\"day\", 3) == 3 then evt.OpenChest(4) end\n"
        "end\n";
    std::string json;
    std::string errorMessage;
    REQUIRE(exploreEventHandlers(map, json, errorMessage));
    CHECK(json.find("\"error\"") == std::string::npos);
    CHECK(json.find("leave to out.odm") != std::string::npos);
    CHECK(json.find("StatusText(") != std::string::npos);
    CHECK(json.find("open chest 4") != std::string::npos);
    const YAML::Node events = YAML::Load(json);
    REQUIRE(events.size() == 2);
    // No, yes-no, yes-yes-no, yes-yes-yes-no, yes four times.
    CHECK(events[0]["paths"].size() == 5);
}

TEST_CASE("a list of points stays on one line in canonical form whether its schema marks it or not")
{
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a}\n"
        "movers:\n"
        "  - id: mover:gate\n"
        "    room: room:a\n"
        "    outline:\n"
        "      - [256, 384]\n"
        "      - [384, 256]\n"
        "      - [768, 640]\n"
        "    height: 384\n"
        "    travel: [0, 0, -386]\n";
    const Project project = projectFromTexts({{"objects.yml", objects}});
    const std::string canonical = canonicalText(project.files.at("objects.yml"));
    CHECK(canonical.find("outline: [[256, 384], [384, 256], [768, 640]]") != std::string::npos);
    // And it is stable.
    const Project again = projectFromTexts({{"objects.yml", canonical}});
    CHECK(canonicalText(again.files.at("objects.yml")) == canonical);
}

namespace
{
// The area of a sector's faces standing in the plane y = `y`, portals left out.
double wallArea(const BuiltRooms &built, int sector, int y)
{
    double area = 0.0;

    for (const OpenYAMM::Game::IndoorFace *pFace : facesOnWall(built, sector, y))
    {
        area += faceArea(built, *pFace);
    }

    return area;
}

// Two halls under hipped ceilings whose ends stand upright on the wall they share (y 1024): the wall is 1024 by 288,
// the end over it rises to 768 over the middle 512. Wall and end together: 663552 square units.
std::string domeHalls(const std::string &secondFrom, const std::string &openings)
{
    return
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 288,\n"
        "     ceiling_levels: [{ceiling: 768, top_outline: [[256, 256], [768, 256], [768, 1024], [256, 1024]]}]}\n"
        "  - {id: room:b, outline: [[0, " + secondFrom + "], [1024, " + secondFrom + "], [1024, 2048], [0, 2048]],\n"
        "     floor: 0, ceiling: 288,\n"
        "     ceiling_levels: [{ceiling: 768, top_outline: [[256, " + secondFrom + "], [768, " + secondFrom
        + "], [768, 1792], [256, 1792]]}]}\n"
        "openings:\n" + openings;
}
}

TEST_CASE("a gabled mouth rises into a dome's upright end, through nested rings, and a window lies wholly in one")
{
    // A gable from 16 under the eaves to 600: its slopes climb through the ceiling line at 288.
    const BuiltRooms mouth = buildRooms(domeHalls(
        "1024", "  - {id: open:mouth, from: room:a, to: room:b, width: full, height: 272, shape: gable, apex: 600}\n"));
    INFO(issueText(mouth));
    REQUIRE(mouth.built);
    CHECK(mouth.hasVertex(512, 1024, 600));
    // What is left of each room's end wall: all of it but the mouth (1024 by 272 and the gable over it).
    const double left = 663552.0 - 1024.0 * 272.0 - 1024.0 * 328.0 / 2.0;
    CHECK(wallArea(mouth, 1, 1024) == doctest::Approx(left).epsilon(0.001));
    CHECK(wallArea(mouth, 2, 1024) == doctest::Approx(left).epsilon(0.001));

    // A gable may run up to the end's top line at any distance under it (a rectangle keeps 16 or lies on the line),
    // not above it; and a gable under a plain ceiling keeps 16.
    CHECK(buildRooms(domeHalls(
        "1024", "  - {id: open:mouth, from: room:a, to: room:b, width: 512, height: 272, shape: gable, apex: 760}\n"))
        .built);
    const std::string above = issueText(buildRooms(domeHalls(
        "1024", "  - {id: open:mouth, from: room:a, to: room:b, width: 512, height: 272, shape: gable, apex: 800}\n")));
    CHECK(above.find("the gabled opening leaves the wall of room:a") != std::string::npos);
    CHECK(above.find("stands to 768 there") != std::string::npos);
    const std::string plain = issueText(buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 288}\n"
        "  - {id: room:b, outline: [[0, 512], [512, 512], [512, 1024], [0, 1024]], floor: 0, ceiling: 288}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 256, height: 128, shape: gable, apex: 280}\n"));
    CHECK(plain.find("less than 16 under the ceiling of room:a (288): lower `apex` to 272") != std::string::npos);

    // A dome of two rings against a wall, and a gallery behind the wall that looks into the upper ring: the window
    // (850 to 1050) lies wholly in the second ring's upright side (768 to 1200).
    const auto ringed = [](const std::string &width)
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    ceiling: 288\n"
            "    ceiling_levels:\n"
            "      - {ceiling: 768, top_outline: [[256, 256], [768, 256], [768, 1024], [256, 1024]]}\n"
            "      - outline: [[256, 256], [768, 256], [768, 1024], [256, 1024]]\n"
            "        ceiling: 1200\n"
            "        top_outline: [[384, 512], [640, 512], [640, 1024], [384, 1024]]\n"
            "  - {id: room:b, outline: [[0, 1056], [1024, 1056], [1024, 1400], [0, 1400]], floor: 800, ceiling: 1150}\n"
            "openings:\n"
            "  - {id: open:window, from: room:a, to: room:b, width: " + width + ", height: 200, sill: 50}\n";
    };
    const BuiltRooms window = buildRooms(ringed("128"));
    INFO(issueText(window));
    REQUIRE(window.built);
    CHECK(window.hasVertex(448, 1024, 850));
    CHECK(window.hasVertex(576, 1024, 1050));
    // The wall, the first ring's end and the second ring's end, less the window.
    CHECK(wallArea(window, 1, 1024)
        == doctest::Approx(663552.0 + (512.0 + 256.0) / 2.0 * 432.0 - 128.0 * 200.0).epsilon(0.001));
    // Wider than the ring at its top corners, it is refused with what the end wall takes there.
    const std::string wide = issueText(buildRooms(ringed("400")));
    CHECK(wide.find("the upright end of a ceiling level") != std::string::npos);
    CHECK(wide.find("the opening reaches 1050") != std::string::npos);
}

TEST_CASE("two openings one above the other may touch as one mouth, wide below and narrower above")
{
    // Walls 32 apart: the lower part to the eaves from wall to wall, the upper a gable into the two ends.
    const auto parts = [](const std::string &lower, const std::string &upper)
    {
        return domeHalls(
            "1056",
            "  - {id: open:low, from: room:a, to: room:b, " + lower + "}\n"
            "  - {id: open:high, from: room:a, to: room:b, " + upper + "}\n");
    };
    const std::string gable = "width: 512, height: 240, sill: 288, shape: gable, apex: 440";
    const BuiltRooms mouth = buildRooms(parts("width: full, height: full", gable));
    INFO(issueText(mouth));
    REQUIRE(mouth.built);
    // The end wall less both parts: nothing is left between them.
    CHECK(wallArea(mouth, 1, 1024)
        == doctest::Approx(663552.0 - 1024.0 * 288.0 - 512.0 * 240.0 - 512.0 * 200.0 / 2.0).epsilon(0.001));
    // No soffit of the lower part and no threshold of the upper one where they meet (x 256 to 768); the lower
    // part keeps its soffit beside the upper one.
    int levelUnderUpper = 0;
    int levelBeside = 0;

    for (const OpenYAMM::Game::IndoorFace &face : mouth.map.faces)
    {
        const std::array<int, 2> range = mouth.heights(face);
        bool inWall = !face.isPortal && range[0] == 288 && range[1] == 288;

        for (const uint16_t vertex : face.vertexIndices)
        {
            inWall = inWall && mouth.map.vertices[vertex].y >= 1024 && mouth.map.vertices[vertex].y <= 1056;
        }

        levelUnderUpper += inWall && mouth.holds(face, 512, 1040) ? 1 : 0;
        levelBeside += inWall && mouth.holds(face, 128, 1040) ? 1 : 0;
    }

    CHECK(levelUnderUpper == 0);
    CHECK(levelBeside == 1);

    // With wall between them they keep 16; an upper part wider than the lower one is not one mouth.
    std::string apart = gable;
    apart.replace(apart.find("sill: 288"), 9, "sill: 296");
    CHECK(issueText(buildRooms(parts("width: full, height: full", apart))).find("as one mouth in two parts")
        != std::string::npos);
    CHECK(issueText(buildRooms(parts("width: 256, height: full", gable))).find("lies within its width")
        != std::string::npos);
}

TEST_CASE("a plate may lie exactly 16 from a wall and under a hanging platform; a refused plate is reported once")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [400, 0], [400, 2000], [0, 2000]]\n"
        "    floor: 0\n"
        "    ceiling: 600\n"
        "    platforms:\n"
        "      - {at: [200, 400], size: [128, 128], rise: 64, base: 308}\n"
        "      - {at: [200, 1600], size: [128, 128], rise: 64}\n";
    const auto objects = [](const std::string &plate)
    {
        return "format: 0\nstart: {room: room:a, at: [200, 100]}\nplates:\n  - {id: plate:p, room: room:a, " + plate
            + "}\n";
    };
    const std::string wiring =
        "format: 0\nevents:\n  - {id: evt:p, preset: text, trigger: step, source: plate:p, text: Stepped.}\n";
    // Corners at x 16 and 384: 16 from both side walls.
    const BuiltTriggers exact = buildTriggers(rooms, objects("at: [200, 1000], size: [368, 200]"), wiring);
    INFO(issueText(exact.rooms));
    REQUIRE(exact.rooms.built);
    REQUIRE(exact.floorsOver(1, 20, 1000).size() == 1);
    CHECK(exact.floorsOver(1, 20, 1000)[0]->cogTriggered == 1);
    // One unit nearer it is refused, once: the event that names it adds nothing.
    const BuiltTriggers near = buildTriggers(rooms, objects("at: [200, 1000], size: [370, 200]"), wiring);
    CHECK_FALSE(near.rooms.built);
    CHECK(near.rooms.issues.size() == 1);
    CHECK(issueText(near.rooms).find("at least 16 from its walls") != std::string::npos);
    CHECK(issueText(near.rooms).find("which is clicked") == std::string::npos);
    // Under the block that hangs 308 above the floor a plate is cut; under the one standing on the floor it is not.
    const BuiltTriggers under = buildTriggers(rooms, objects("at: [200, 400], size: [100, 100]"), wiring);
    INFO(issueText(under.rooms));
    CHECK(under.rooms.built);
    const std::string standing =
        issueText(buildTriggers(rooms, objects("at: [200, 1600], size: [100, 100]"), wiring).rooms);
    CHECK(standing.find("lies on a level, platform or flight") != std::string::npos);
    CHECK(standing.find("a plate may lie under it") != std::string::npos);
}

TEST_CASE("a twisted side of a ceiling level is built as triangles, and a face that is not flat is refused by room")
{
    // The south side is upright (its top points over its foot's); the east and west sides run from a corner that
    // stays put to one that leans in: four corners not in one plane, built as two triangles each.
    const BuiltRooms twisted = buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [6000, 0], [6000, 5000], [0, 5000]]\n"
        "    floor: 0\n"
        "    ceiling: 800\n"
        "    ceiling_levels:\n"
        "      - outline: [[100, 100], [5900, 100], [5900, 4900], [100, 4900]]\n"
        "        ceiling: 1400\n"
        "        top_outline: [[100, 100], [5900, 100], [3500, 2800], [1500, 2800]]\n",
        "format: 0\nstart: {room: room:a, at: [300, 300]}\n");
    INFO(issueText(twisted));
    REQUIRE(twisted.built);
    int eastTriangles = 0;

    for (const OpenYAMM::Game::IndoorFace &face : twisted.map.faces)
    {
        bool east = face.vertexIndices.size() == 3;

        for (const uint16_t vertex : face.vertexIndices)
        {
            const OpenYAMM::Game::IndoorVertex &corner = twisted.map.vertices[vertex];
            east = east && (corner.x == 5900 || (corner.x == 3500 && corner.y == 2800 && corner.z == 1400));
        }

        eastTriangles += east ? 1 : 0;
    }

    CHECK(eastTriangles == 2);

    // A ramp whose low and high walls are not parallel has a floor that is not flat: refused before the compiler
    // sees it, with the room and the corners.
    const BuiltRooms bent = buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1000, 0], [1100, 900], [0, 700]], floor: 0, ceiling: 600,\n"
        "     slope: {to: 200, toward: n}}\n",
        "format: 0\nstart: {room: room:a, at: [300, 300]}\n");
    CHECK_FALSE(bent.built);
    CHECK(issueText(bent).find("a face of room:a is not flat once its corners stand on whole units")
        != std::string::npos);
    CHECK(issueText(bent).find("[1100, 900, 200]") != std::string::npos);
    CHECK(issueText(bent).find("the indoor compiler refused") == std::string::npos);
}

TEST_CASE("two rooms under one ridge ceiling are open to each other over their whole section")
{
    // A tube under a ridge with a flat of 200 (eaves 150, ridge 420) going on round a bend: an arch whose shoulders
    // stand at the point's height is the end's own outline.
    const auto tube = [](const std::string &shape)
    {
        return
            "rooms:\n"
            "  - {id: room:a, outline: [[0, 0], [1000, 0], [1000, 800], [0, 800]], floor: 0, ceiling: 150,\n"
            "     ceiling_levels: [{ceiling: 420, top_outline: [[0, 300], [1000, 300], [1000, 500], [0, 500]]}]}\n"
            "  - {id: room:b, outline: [[1000, 0], [2000, -300], [2000, 500], [1000, 800]], floor: 0, ceiling: 150,\n"
            "     ceiling_levels: [{ceiling: 420, top_outline: [[1000, 300], [2000, 0], [2000, 200], [1000, 500]]}]}\n"
            "openings:\n"
            "  - {id: open:ab, from: room:a, to: room:b, width: full, height: full" + shape + "}\n";
    };
    const BuiltRooms open = buildRooms(tube(", shape: arch, apex: 420, shoulders: [[0.375, 1]]"));
    INFO(issueText(open));
    REQUIRE(open.built);
    int onJoint = 0;
    size_t portalCorners = 0;

    for (const OpenYAMM::Game::IndoorFace &face : open.map.faces)
    {
        bool joint = true;

        for (const uint16_t vertex : face.vertexIndices)
        {
            joint = joint && open.map.vertices[vertex].x == 1000;
        }

        onJoint += joint && !face.isPortal ? 1 : 0;
        portalCorners = joint && face.isPortal ? face.vertexIndices.size() : portalCorners;
    }

    // Nothing is left of either end wall; the portal is the whole section (the middle of the flat is a point of it).
    CHECK(onJoint == 0);
    CHECK(portalCorners == 7);
    // Without the shape the opening ends at the eaves and both ends stay walled above it.
    const BuiltRooms eaves = buildRooms(tube(""));
    REQUIRE(eaves.built);
    CHECK(eaves.hasVertex(1000, 300, 420));
    // A gable to the ridge stays inside the end: its point lies on the flat.
    CHECK(buildRooms(tube(", shape: gable, apex: 420")).built);
    // Higher than the ridge it leaves the wall.
    CHECK(issueText(buildRooms(tube(", shape: gable, apex: 460"))).find("the gabled opening leaves the wall of room:a")
        != std::string::npos);
}

TEST_CASE("a gallery of 24 corners and a closed parapet ring build")
{
    // The Lincoln's hall gallery: one hanging platform round three sides of the hall, 24 corners.
    const BuiltRooms gallery = buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[2432, -8160], [6272, -8160], [6272, -3296], [5248, -2272], [3456, -2272], [2432, -3296]]\n"
        "    floor: 1036\n"
        "    ceiling: 1740\n"
        "    platforms:\n"
        "      - {rise: 64, base: 384, outline: [[2432, -8160], [3200, -8160], [3200, -7392], [2688, -7392], "
        "[2688, -5472], [6016, -5472], [6016, -7392], [5504, -7392], [5504, -8160], [6272, -8160], [6272, -3296], "
        "[5248, -2272], [4864, -2272], [4864, -2528], [5248, -2528], [6016, -3296], [6016, -5216], [2688, -5216], "
        "[2688, -3296], [3456, -2528], [3840, -2528], [3840, -2272], [3456, -2272], [2432, -3296]]}\n",
        "format: 0\nstart: {room: room:a, at: [4352, -6400]}\n");
    INFO(issueText(gallery));
    REQUIRE(gallery.built);
    // Its underside (at 1420) and its top (at 1484) each cover the place under the gallery's south arm once.
    CHECK(gallery.levelsOver(1, 4352, -5344, false) == std::vector<int>{1420, 1740});
    CHECK(gallery.levelsOver(1, 4352, -5344, true) == std::vector<int>{1036, 1484});

    // A parapet whose path ends where it began: a kerb all round a well.
    const auto ring = [](const std::string &path)
    {
        return
            "rooms:\n"
            "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384,\n"
            "     parapets: [{path: " + path + ", height: 80, thickness: 64}]}\n";
    };
    const BuiltRooms kerb = buildRooms(ring("[[256, 256], [768, 256], [768, 768], [256, 768], [256, 256]]"));
    INFO(issueText(kerb));
    REQUIRE(kerb.built);

    // Its top runs all round at 80: over every side (also where the two halves meet, x 512) and every corner.
    const auto tops = [&kerb](double x, double y)
    {
        const std::vector<int> levels = kerb.levelsOver(1, x, y, true);
        return std::set<int>(levels.begin(), levels.end());
    };

    for (const std::array<double, 2> &place : std::vector<std::array<double, 2>>{
             {400, 250}, {512, 250}, {770, 512}, {400, 770}, {512, 770}, {250, 512}, {250, 250}, {770, 250},
             {770, 770}, {250, 770}})
    {
        CAPTURE(place[0]);
        CAPTURE(place[1]);
        CHECK(tops(place[0], place[1]) == std::set<int>{0, 80});
    }

    CHECK(tops(512, 512) == std::set<int>{0});
    // A path that crosses itself without closing is still refused.
    CHECK(issueText(buildRooms(ring("[[256, 256], [768, 256], [512, 300], [512, 100]]")))
        .find("rooms[0].parapets[0].path") != std::string::npos);
}

TEST_CASE("rooms stack by their true surfaces: a ramp under a ceiling that slopes with it passes under a room")
{
    // The ramp falls from 0 at its south end to -400 at its north end under a ceiling 256 above it; the upper room
    // lies over its north half with its floor at 64, 8 over the ramp's ceiling where the two come nearest (the
    // ramp's ceiling begins at 256, far above that floor, at its other end).
    const auto stacked = [](const std::string &upperFloor)
    {
        return
            "rooms:\n"
            "  - {id: room:ramp, outline: [[0, 0], [256, 0], [256, 1024], [0, 1024]], floor: 0, ceiling: 256,\n"
            "     slope: {to: -400, toward: n}, ceiling_slope: {to: -144, toward: n}}\n"
            "  - {id: room:upper, outline: [[-128, 512], [384, 512], [384, 1024], [-128, 1024]], floor: "
            + upperFloor + ", ceiling: 400}\n";
    };
    const std::string objects = "format: 0\nstart: {room: room:ramp, at: [128, 100]}\n";
    const BuiltRooms under = buildRooms(stacked("64"), objects);
    INFO(issueText(under));
    CHECK(under.built);
    // Lower by 104 the upper room's floor cuts into the ramp's ceiling at its south edge.
    const std::string cut = issueText(buildRooms(stacked("-40"), objects));
    CHECK(cut.find("rooms room:ramp and room:upper overlap") != std::string::npos);
    CHECK(cut.find("the ceiling of room:ramp is at") != std::string::npos);
    CHECK(cut.find("the floor of room:upper at -40") != std::string::npos);
}

TEST_CASE("walls a little off parallel at a joint are named as that, and a chest stands wholly in its room")
{
    // Room b's south wall runs from [0, 1000] to [1000, 1009]: half a degree off room a's north wall.
    const std::string crossing = issueText(buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1000, 0], [1000, 1004], [0, 1004]], floor: 0, ceiling: 256}\n"
        "  - {id: room:b, outline: [[0, 1000], [1000, 1009], [1000, 2000], [0, 2000]], floor: 0, ceiling: 256}\n"));
    CHECK(crossing.find("rooms room:a and room:b cross along the walls they meet at") != std::string::npos);
    CHECK(crossing.find("0.52 degrees off parallel") != std::string::npos);
    CHECK(crossing.find("the wall of room:b from [0, 1000] to [1000, 1009]") != std::string::npos);
    // Apart instead of crossing: the opening that cannot join them says why.
    const std::string apart = issueText(buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1000, 0], [1000, 1000], [0, 1000]], floor: 0, ceiling: 256}\n"
        "  - {id: room:b, outline: [[0, 1016], [1000, 1025], [1000, 2000], [0, 2000]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n"));
    CHECK(apart.find("have no facing parallel walls") != std::string::npos);
    CHECK(apart.find("face each other but are 0.52 degrees off parallel") != std::string::npos);
    // Rooms that truly share space are still said to overlap.
    CHECK(issueText(buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1000, 0], [1000, 1000], [0, 1000]], floor: 0, ceiling: 256}\n"
        "  - {id: room:b, outline: [[500, 500], [1500, 500], [1500, 1500], [500, 1500]], floor: 0, ceiling: 256}\n"))
        .find("rooms room:a and room:b overlap: two rooms cannot share space") != std::string::npos);

    // A bookcase 600 wide, its middle 40 from the south wall: turned north its width runs into the wall.
    const std::string room =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1000, 0], [1000, 1000], [0, 1000]], floor: 0, ceiling: 256}\n";
    const auto chest = [](const std::string &facing)
    {
        return "format: 0\nstart: {room: room:a}\nchests:\n  - {id: chest:case, room: room:a, at: [500, 40], "
            "size: [600, 60, 200]" + facing + "}\n";
    };
    const std::string outside = issueText(buildRooms(room, chest(", facing: n")));
    CHECK(outside.find("the chest stands partly outside room:a") != std::string::npos);
    CHECK(outside.find("its width running along its `facing` (n)") != std::string::npos);
    const BuiltRooms inside = buildRooms(room, chest(""));
    INFO(issueText(inside));
    CHECK(inside.built);
}

TEST_CASE("D-99: a chest without facing: its back to the wall by it, out of a niche, free toward the entrance")
{
    // Room a, 1000 square, with a niche (room n, 160 wide and 128 deep) off its east wall and a doorway to room b in
    // its north wall; the start in room b, so room a is entered through the north doorway.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1000, 0], [1000, 1000], [0, 1000]], floor: 0, ceiling: 256}\n"
        "  - {id: room:n, outline: [[1000, 420], [1128, 420], [1128, 580], [1000, 580]], floor: 0, ceiling: 256}\n"
        "  - {id: room:b, outline: [[0, 1000], [1000, 1000], [1000, 2000], [0, 2000]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:an, from: room:a, to: room:n, width: full, height: 192}\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:b, at: [500, 1500]}\nchests:\n"
        "  - {id: chest:south, room: room:a, at: [300, 40], kind: 7gt002}\n"
        "  - {id: chest:west, room: room:a, at: [40, 300], kind: 7gt002}\n"
        "  - {id: chest:niche, room: room:n, at: [1080, 500], kind: 7gt002}\n"
        "  - {id: chest:free, room: room:a, at: [700, 500], kind: 7gt002}\n";
    const BuiltRooms built = buildRooms(rooms, objects);
    INFO(issueText(built));
    REQUIRE(built.built);
    // Each chest's front: from its middle to its sloping lid's own picture (7gt002e), seen from above.
    const auto frontOf = [&built](double x, double y)
    {
        std::array<double, 2> sum = {0.0, 0.0};
        double count = 0.0;

        for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
        {
            if (face.textureName != "7gt002e")
            {
                continue;
            }

            std::array<double, 2> middle = {0.0, 0.0};

            for (const uint16_t vertex : face.vertexIndices)
            {
                middle[0] += built.map.vertices[vertex].x / double(face.vertexIndices.size());
                middle[1] += built.map.vertices[vertex].y / double(face.vertexIndices.size());
            }

            if (std::hypot(middle[0] - x, middle[1] - y) < 80.0)
            {
                sum = {sum[0] + middle[0] - x, sum[1] + middle[1] - y};
                count += 1.0;
            }
        }

        return count > 0.0 ? std::array<double, 2>{sum[0] / count, sum[1] / count} : std::array<double, 2>{0.0, 0.0};
    };
    // By the south wall: front north; by the west wall: front east; in the niche: front west, out of it; free in
    // the room: front north, toward the doorway from room b.
    CHECK(frontOf(300, 40)[1] > 10.0);
    CHECK(std::abs(frontOf(300, 40)[0]) < 1.0);
    CHECK(frontOf(40, 300)[0] > 10.0);
    CHECK(frontOf(1080, 500)[0] < -10.0);
    CHECK(frontOf(700, 500)[1] > 10.0);
    CHECK(std::abs(frontOf(700, 500)[0]) < 1.0);
}

TEST_CASE("D-99's checks: a chest's front to a wall, end-on, back to the entrance, in a doorway, on a walking line")
{
    // A room 1000 square; a chest 96 by 64 by its south wall (y 0).
    const std::vector<OpenYAMM::Studio::ChestWall> walls = {{{0, 0}, {1000, 0}}, {{1000, 0}, {1000, 1000}},
        {{1000, 1000}, {0, 1000}}, {{0, 1000}, {0, 0}}};
    const double north = std::numbers::pi / 2.0;
    using OpenYAMM::Studio::chestFacingFault;
    using OpenYAMM::Studio::chestGaps;
    CHECK(chestFacingFault(chestGaps(walls, {500, 40}, north, 96, 64), true, std::nullopt).empty());
    CHECK(chestFacingFault(chestGaps(walls, {500, 40}, -north, 96, 64), true, std::nullopt)
              .find("its front faces a wall") != std::string::npos);
    CHECK(chestFacingFault(chestGaps(walls, {500, 56}, 0.0, 96, 64), true, std::nullopt)
              .find("end-on") != std::string::npos);
    // MM6's chests show the same long side front and back: either long side may face the wall.
    CHECK(chestFacingFault(chestGaps(walls, {500, 40}, -north, 96, 64), false, std::nullopt).empty());
    // Free in the room: its back to the entrance is wrong, its front toward it right.
    CHECK(chestFacingFault(chestGaps(walls, {500, 500}, north, 96, 64), true, 170.0).find("back to its room's entrance")
        != std::string::npos);
    CHECK(chestFacingFault(chestGaps(walls, {500, 500}, north, 96, 64), true, 20.0).empty());
    // A doorway in the north wall from 436 to 564, one in the south wall: in front of it, on the line, clear.
    const std::vector<OpenYAMM::Studio::ChestDoorway> ways = {{{436, 1000}, {564, 1000}, "north"},
        {{436, 0}, {564, 0}, "south"}};
    using OpenYAMM::Studio::chestFootprint;
    using OpenYAMM::Studio::chestPlacementFault;
    CHECK(chestPlacementFault(chestFootprint({500, 900}, -north, 96, 64), ways, true).find("in front of north")
        != std::string::npos);
    CHECK(chestPlacementFault(chestFootprint({520, 500}, 0.0, 96, 64), ways, true).find("walking line")
        != std::string::npos);
    CHECK(chestPlacementFault(chestFootprint({900, 40}, north, 96, 64), ways, true).empty());
    // Beside a doorway along its wall: 128 clear, as in front.
    CHECK(chestPlacementFault(chestFootprint({700, 960}, -north, 96, 64), ways, true).find("beside north")
        != std::string::npos);
    CHECK(chestPlacementFault(chestFootprint({760, 960}, -north, 96, 64), ways, true).empty());
}

TEST_CASE("a floor marked water has the fluid flag and no lava flag; a floor has one kind")
{
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a, at: [512, 64]}\n"
        "floors:\n"
        "  - {id: floor:pool, of: level:pit, kind: water}\n"
        "  - {id: floor:b, of: room:b, kind: lava}\n";
    const BuiltTriggers built = buildTriggers(TriggerRooms, objects, "format: 0\nevents: []\n");
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    const uint32_t fluidFlag = 0x00000010u;
    REQUIRE(built.floorsOver(1, 192, 192).size() == 1);
    const OpenYAMM::Game::IndoorFace *pPool = built.floorsOver(1, 192, 192)[0];
    CHECK((pPool->attributes & fluidFlag) == fluidFlag);
    CHECK((pPool->attributes & (LavaFlag | StepFlags | ClickFlag)) == 0);
    CHECK(built.rooms.heights(*pPool) == std::array<int, 2>{-32, -32});
    // The room's own floor round the pool is plain; the lava floor is not water.
    REQUIRE(built.floorsOver(1, 512, 700).size() == 1);
    CHECK((built.floorsOver(1, 512, 700)[0]->attributes & (fluidFlag | LavaFlag)) == 0);
    REQUIRE(built.floorsOver(2, 1216, 384).size() == 1);
    CHECK((built.floorsOver(2, 1216, 384)[0]->attributes & (fluidFlag | LavaFlag)) == LavaFlag);
    // One floor, one kind.
    const std::string twice = issueText(buildTriggers(
        TriggerRooms, objects + "  - {id: floor:pool_too, of: level:pit, kind: lava}\n", "format: 0\nevents: []\n")
            .rooms);
    CHECK(twice.find("level:pit is already marked by another `floors` entry") != std::string::npos);
}

TEST_CASE("cast writes the skill level before the mastery, and any preset moves the doors of its lists")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 768], [0, 768]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[544, 128], [800, 128], [800, 320], [544, 320]], floor: 0, ceiling: 256}\n"
        "  - {id: room:c, outline: [[544, 448], [800, 448], [800, 640], [544, 640]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n"
        "  - {id: open:ac, from: room:a, to: room:c, width: 128, height: 192}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a}\ndoors:\n"
        "  - {id: door:ab, opening: open:ab}\n"
        "  - {id: door:ac, opening: open:ac}\n";
    const BuiltTriggers built = buildTriggers(
        rooms, objects,
        "format: 0\n"
        "events:\n"
        "  - {id: evt:e1_airlock, preset: door, source: door:ab, closes: [door:ac]}\n"
        "  - id: evt:e2_sparks\n"
        "    preset: script\n"
        "    trigger: timer\n"
        "    every: 3\n"
        "    opens: [door:ac]\n"
        "    effects:\n"
        "      - cast: {spell: 15, from: [64, 64, 96], to: [448, 64, 96], mastery: master, level: 7}\n");
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    INFO(built.lua);
    // The game's evt.CastSpell reads the spell, the skill level, the mastery, then the two points.
    CHECK(built.lua.find("    evt.SetDoorState(2, DoorAction.Open)\n"
        "    evt.CastSpell(15, 7, 3, 64, 64, 96, 448, 64, 96)\n") != std::string::npos);
    // The door's event toggles its own door and then shuts the other.
    CHECK(built.lua.find("    evt.SetDoorState(1, DoorAction.Trigger)\n    evt.SetDoorState(2, DoorAction.Close)\n")
        != std::string::npos);
}

TEST_CASE("a platform in a sunken level has its top above that level's floor, and a flight climbs to it")
{
    const auto hall = [](const std::string &flight)
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [2048, 0], [2048, 2048], [0, 2048]]\n"
            "    floor: 0\n"
            "    ceiling: 768\n"
            "    levels:\n"
            "      - {outline: [[1024, 32], [2016, 32], [2016, 2016], [512, 2016], [512, 1536], [1024, 1536]], "
            "floor: -256}\n"
            "    platforms:\n"
            "      - {at: [1500, 1000], size: [128, 128], rise: 144}\n"
            "    flights:\n"
            "      - {from: [1500, 500], to: [1500, 936], " + flight + "width: 128, steps: 9}\n";
    };
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [256, 256]}\n"
        "chests:\n  - {id: chest:top, room: room:a, at: [1500, 1000], size: [64, 48, 40]}\n";

    for (const char *pFlight : {"", "to_height: -112, "})
    {
        const BuiltRooms built = buildRooms(hall(pFlight), objects);
        INFO(pFlight << "\n" << issueText(built));
        REQUIRE(built.built);
        // The platform's top is at -112 (144 above the sunken floor), the flight's last tread level with it, and
        // the chest stands on the top (free, so D-99 turns its front west, toward the start: 48 deep along x).
        CHECK(built.hasVertex(1436, 936, -112));
        CHECK(built.hasVertex(1436, 888, -112));
        CHECK(built.hasVertex(1476, 968, -72));
        CHECK_FALSE(built.hasVertex(1436, 936, 144));
    }
}

TEST_CASE("every form of platform in a sunken level stands on that level's floor")
{
    // A spike that tapers, a slab that hangs and a plain block, all in a pit 256 deep.
    const BuiltRooms built = buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [2048, 0], [2048, 2048], [0, 2048]]\n"
        "    floor: 0\n"
        "    ceiling: 1024\n"
        "    platforms:\n"
        "      - {at: [1024, 1024], size: [16, 16], rise: 128, top_size: [2, 2]}\n"
        "      - {at: [1280, 1024], size: [16, 16], rise: 128}\n"
        "      - {at: [1536, 1024], size: [64, 64], rise: 16, base: 240}\n"
        "    levels:\n"
        "      - {outline: [[256, 256], [1792, 256], [1792, 1792], [256, 1792]], floor: -256}\n",
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n");
    INFO(issueText(built));
    REQUIRE(built.built);
    // The spike's foot on the pit's floor and its point 128 above it; the plain block the same.
    CHECK(built.hasVertex(1016, 1016, -256));
    CHECK(built.hasVertex(1023, 1023, -128));
    CHECK_FALSE(built.hasVertex(1023, 1023, 128));
    CHECK(built.hasVertex(1272, 1016, -128));
    // The slab hangs 240 above the pit's floor: its top is level with the room's.
    CHECK(built.hasVertex(1504, 992, -16));
    CHECK(built.hasVertex(1504, 992, 0));
}

TEST_CASE("an object on a wall is placed by a point or a side, measured from a named floor, as wide as its wall")
{
    // A landing hangs in the north-east corner (top at 416) and touches the north wall under the lever.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 1536\n"
        "    platforms:\n"
        "      - {at: [960, 960], size: [128, 128], rise: 32, base: 384}\n"
        "  - {id: room:b, outline: [[384, -64], [640, -64], [640, 0], [384, 0]], floor: 0, ceiling: 288}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: full, height: 256}\n";
    const auto objects = [](const std::string &lever, const std::string &exitSize)
    {
        return "format: 0\nstart: {room: room:a, at: [512, 512]}\n"
            "switches:\n  - {id: switch:high, room: room:a, " + lever + "}\n"
            "exits:\n  - {id: exit:out, room: room:b, wall: south, size: " + exitSize + ", to: exit:away}\n";
    };
    const std::string wiring =
        "format: 0\nevents:\n  - {id: evt:out, preset: exit, source: exit:out}\n";
    const std::string card = std::string(CardText)
        + "neighbours:\n  - {id: exit:away, to: oute3.odm, kind: door, arrival: [0, 0, 0], direction: 0}\n";
    const auto build = [&](const std::string &lever, const std::string &exitSize)
    {
        const std::filesystem::path root = std::filesystem::temp_directory_path()
            / ("oymap_panels_" + std::to_string(std::random_device{}()));
        std::filesystem::create_directories(root);
        std::ofstream(root / "project.yml", std::ios::binary) << card;
        std::ofstream(root / "rooms.yml", std::ios::binary) << std::string(ThemeText) + rooms;
        std::ofstream(root / "objects.yml", std::ios::binary) << objects(lever, exitSize);
        std::ofstream(root / "wiring.yml", std::ios::binary) << wiring;
        BuiltRooms built;
        Project project;

        if (loadProject(root, project, built.issues))
        {
            std::vector<ProjectIssue> issues;
            LoweredIndoorMap lowered;
            built.built = lowerIndoorProject(project, {}, lowered, issues);
            built.issues = issues;

            // The lever's plate: its lowest and highest point, kept in the vertices for the checks below.
            for (const GlbNode &node : lowered.nodes)
            {
                if (node.name != "TRIGGER_high" && node.name != "TRIGGER_out")
                {
                    continue;
                }

                for (const GlbFace &face : node.faces)
                {
                    for (const std::array<float, 3> &point : face.positions)
                    {
                        built.map.vertices.push_back({
                            static_cast<int16_t>(std::lround(point[0])), static_cast<int16_t>(std::lround(point[1])),
                            static_cast<int16_t>(std::lround(point[2]))});
                    }
                }
            }

            for (const std::string &warning : lowered.warnings)
            {
                built.issues.push_back({"warning", "", warning, "warning"});
            }
        }

        std::filesystem::remove_all(root);
        return built;
    };

    // By a point near the wall, its height from the room's own floor: 1276 above it, over the landing.
    const BuiltRooms named = build("at: [992, 1030], height: 1276, floor_height: 0", "[192, 256]");
    INFO(issueText(named));
    REQUIRE(named.built);
    CHECK(named.hasVertex(1008, 1022, 1260));
    CHECK(named.hasVertex(976, 1022, 1292));
    CHECK(issueText(named).find("Say which floor is meant") == std::string::npos);
    // Without the floor's name the height counts from the landing's top, and the build says so.
    const BuiltRooms fromLanding = build("wall: north, along: 0.0313, height: 860", "[192, 256]");
    INFO(issueText(fromLanding));
    REQUIRE(fromLanding.built);
    CHECK(fromLanding.hasVertex(1008, 1022, 1260));
    CHECK(issueText(fromLanding).find("its height is measured from the highest floor there (416)")
        != std::string::npos);
    // Too high for the room it says where it would stand; an exit as wide as its wall fits, and one that does not
    // fit is reported once.
    const std::string high = issueText(build("wall: north, along: 0.0313, height: 1276", "[256, 256]"));
    CHECK(high.find("from 1676 to 1708 in height, where the floor in front of it is at 416 and the ceiling at 1536")
        != std::string::npos);
    CHECK(build("wall: west, height: 96", "[256, 256]").built);
    const BuiltRooms wide = build("wall: west, height: 96", "[300, 256]");
    CHECK_FALSE(wide.built);
    CHECK(issueText(wide).find("along a wall 256 long") != std::string::npos);
    CHECK(issueText(wide).find("the exit leads to") == std::string::npos);
    // A wall and a point together are refused.
    CHECK(issueText(build("wall: north, at: [992, 1030]", "[192, 256]")).find("not both") != std::string::npos);
}

TEST_CASE("a step event takes a mover's top, a switch preset a door, and a chest may hold only what is listed")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 512}\n"
        "  - {id: room:b, outline: [[1056, 384], [1312, 384], [1312, 640], [1056, 640]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "doors:\n  - {id: door:ab, opening: open:ab}\n"
        "movers:\n"
        "  - {id: mover:stone, room: room:a, at: [512, 512], size: [256, 256], bottom: -128, height: 160,\n"
        "     travel: [0, 0, 128], state: end}\n"
        "chests:\n"
        "  - {id: chest:plain, room: room:a, at: [128, 896], random_items: 0, gold: 50}\n";
    const std::string wiring =
        "format: 0\n"
        "events:\n"
        "  - {id: evt:e1_sink, preset: switch, trigger: step, source: mover:stone, closes: [mover:stone]}\n"
        "  - {id: evt:e2_door, preset: switch, source: door:ab, toggles: [mover:stone]}\n";
    const BuiltMoving built = buildMoving(rooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // The stone's top (at 160 with the stone at its end) runs the step event; it is not clicked.
    int stoneTops = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        if (face.cogTriggered == 1)
        {
            CHECK((face.attributes & StepFlags) == StepFlags);
            CHECK((face.attributes & ClickFlag) == 0);
            stoneTops += built.rooms.holds(face, 512, 512) && (face.facetType == 3 || face.facetType == 4) ? 1 : 0;
        }
    }

    CHECK(stoneTops == 1);
    // The door's own click moves only what the lists name: the stone, not the door.
    CHECK(built.lua.find("RegisterEvent(2, nil, function()\n    evt.SetDoorState(2, DoorAction.Trigger)\nend")
        != std::string::npos);

    // A moving part runs one event: clicked and stepped on at once is refused.
    const std::string both = issueText(buildMoving(
        rooms, objects,
        wiring + "  - {id: evt:e3_click, preset: switch, source: mover:stone, opens: [mover:stone]}\n").rooms);
    CHECK(both.find("mover:stone already has an event") != std::string::npos);

    // No random rolls: treasure level 0 with the one record the game asks for.
    const Project project = projectFromTexts({
        {"project.yml", CardText}, {"rooms.yml", std::string(ThemeText) + rooms}, {"objects.yml", objects},
        {"wiring.yml", wiring}});
    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    REQUIRE(lowerIndoorProject(project, {}, lowered, issues));
    REQUIRE(lowered.chests.size() == 1);
    CHECK(lowered.chests[0].treasureLevel == 0);
    CHECK(lowered.chests[0].randomItems == 1);
    CHECK(lowered.chests[0].gold == 50);

    // A mover that is refused says so once: the events that name it add nothing, and nothing calls it a door.
    std::string outside = objects;
    outside.replace(outside.find("at: [512, 512]"), 14, "at: [960, 512]");
    const BuiltMoving refused = buildMoving(rooms, outside, wiring);
    CHECK_FALSE(refused.rooms.built);
    CHECK(issueText(refused.rooms).find("there is no door") == std::string::npos);
    CHECK(issueText(refused.rooms).find("which is clicked") == std::string::npos);
    CHECK(issueText(refused.rooms).find("is not inside room:a") != std::string::npos);
}

TEST_CASE("the upright side of a ceiling level that narrows is wall, its leaning sides ceiling, unless it has an edge")
{
    const std::string door = "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n";
    const BuiltRooms plain = buildRooms(domeHalls("1024", door));
    INFO(issueText(plain));
    REQUIRE(plain.built);
    // The end wall over the doorway, wall and upright end alike, is all wall; nothing of it is ceiling.
    CHECK(textureArea(plain, 1, 1024, "wall") == doctest::Approx(663552.0 - 128.0 * 192.0).epsilon(0.001));
    CHECK(textureArea(plain, 1, 1024, "ceil") == 0.0);
    // The three sides that lean keep the ceiling's surface: no face of the level but the end is wall above the eaves.
    int leaningWall = 0;

    for (const OpenYAMM::Game::IndoorFace &face : plain.map.faces)
    {
        const std::array<int, 2> range = plain.heights(face);
        bool onEnd = true;

        for (const uint16_t vertex : face.vertexIndices)
        {
            onEnd = onEnd && plain.map.vertices[vertex].y == 1024;
        }

        leaningWall += face.roomNumber == 1 && !onEnd && range[1] > 288 && face.textureName == "wall" ? 1 : 0;
    }

    CHECK(leaningWall == 0);

    // With an `edge` every side of the level, upright or leaning, has that surface.
    std::string edged = domeHalls("1024", door);
    edged.replace(
        edged.find("ceiling_levels: [{ceiling: 768,"), 31,
        "ceiling_levels: [{edge: {texture: rib, size: [64, 64]}, ceiling: 768,");
    const BuiltRooms withEdge = buildRooms(edged);
    INFO(issueText(withEdge));
    REQUIRE(withEdge.built);
    CHECK(textureArea(withEdge, 1, 1024, "rib") == doctest::Approx((1024.0 + 512.0) / 2.0 * 480.0).epsilon(0.001));
    CHECK(textureArea(withEdge, 1, 1024, "wall") == doctest::Approx(1024.0 * 288.0 - 128.0 * 192.0).epsilon(0.001));
}

namespace
{
// The Hive's tunnel cut across: a floor 128 wide, 256 wide at half height, a ceiling 128 wide at 256.
const std::string HexagonSection =
    "section: {outline: [[-64, 0], [64, 0], [128, 128], [64, 256], [-64, 256], [-128, 128]]}";

// The faces of one sector that are not portals, by facet type (1 wall, 3 and 4 floor, 5 and 6 ceiling).
std::map<int, int> facetCounts(const BuiltRooms &built, int sector)
{
    std::map<int, int> counts;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (!face.isPortal && face.roomNumber == sector)
        {
            ++counts[face.facetType];
        }
    }

    return counts;
}

// The portal faces of a map as their corner counts and height ranges, in order.
std::vector<std::array<int, 3>> portalShapes(const BuiltRooms &built)
{
    std::vector<std::array<int, 3>> shapes;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        // Each portal is stored once for each of its two rooms.
        if (face.isPortal)
        {
            const std::array<int, 2> range = built.heights(face);
            shapes.push_back({static_cast<int>(face.vertexIndices.size()), range[0], range[1]});
        }
    }

    std::sort(shapes.begin(), shapes.end());
    shapes.erase(std::unique(shapes.begin(), shapes.end()), shapes.end());
    return shapes;
}
}

TEST_CASE("a tunnel carries its section along its path: mitred at a bend, in triangles where it climbs, shut at an end")
{
    // Level, with one bend to the left.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0], [1024, 1024]], floor: 0, ceiling: 256,\n"
        "     " + HexagonSection + "}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);

    // The section at the path's first point, square to the way: the right of the way is the south.
    for (const std::array<int, 3> &corner : std::vector<std::array<int, 3>>{
             {0, 64, 0}, {0, -64, 0}, {0, -128, 128}, {0, -64, 256}, {0, 64, 256}, {0, 128, 128}})
    {
        CHECK(built.hasVertex(corner[0], corner[1], corner[2]));
    }

    // At the bend it stands on the line that halves the bend, drawn out along it (a mitre).
    for (const std::array<int, 3> &corner : std::vector<std::array<int, 3>>{
             {960, 64, 0}, {1088, -64, 0}, {1152, -128, 128}, {1088, -64, 256}, {960, 64, 256}, {896, 128, 128}})
    {
        CHECK(built.hasVertex(corner[0], corner[1], corner[2]));
    }

    // And at the last point, where the way runs north.
    CHECK(built.hasVertex(1088, 1024, 0));
    CHECK(built.hasVertex(1152, 1024, 128));
    CHECK(built.hasVertex(896, 1024, 128));
    // Two stretches of six flat sides each, and a wall of the section's shape at both ends: no face more.
    const std::map<int, int> counts = facetCounts(built, 1);
    CHECK(counts == std::map<int, int>{{1, 10}, {3, 2}, {5, 2}});
    // The floor is the flat strip alone: the Hive's lower sides rise 128 over 64 and are walls to the game.
    CHECK(built.levelsOver(1, 512.0, 0.0, true) == std::vector<int>{0});
    CHECK(built.levelsOver(1, 512.0, 100.0, true).empty());
    CHECK(built.levelsOver(1, 512.0, 0.0, false) == std::vector<int>{256});

    // The Control Center's tube: banks that rise 74 over 90 are floor the party walks up; walls and chamfers.
    const BuiltRooms tube = buildRooms(
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0]], floor: 0, ceiling: 305,\n"
        "     section: {outline: [[-64, 0], [64, 0], [154, 74], [154, 228], [64, 305], [-64, 305], [-154, 228],\n"
        "       [-154, 74]], lower: {texture: bank, size: [64, 64]}, upper: {texture: cham, size: [64, 64]}}}\n");
    INFO(issueText(tube));
    REQUIRE(tube.built);
    CHECK(facetCounts(tube, 1) == std::map<int, int>{{1, 4}, {3, 1}, {4, 2}, {5, 1}, {6, 2}});
    CHECK(tube.levelsOver(1, 512.0, 109.0, true) == std::vector<int>{74});

    for (const OpenYAMM::Game::IndoorFace &face : tube.map.faces)
    {
        if (face.facetType == 4)
        {
            // Walkable: a normal of at least 0.71 upward.
            CHECK(std::abs(faceNormal(tube, face)[2]) / (2.0 * faceArea(tube, face)) > 0.71);
            CHECK(face.textureName == "bank");
        }

        if (face.facetType == 6)
        {
            CHECK(face.textureName == "cham");
        }
    }

    // A tunnel that climbs round its bend: 0, 128 at the bend, 256; the section 256 high above the floor at each.
    std::string climbing = rooms;
    climbing.replace(climbing.find("ceiling: 256"), 12, "slope: {to: 256}, ceiling: 256");
    const BuiltRooms climbed = buildRooms(climbing);
    INFO(issueText(climbed));
    REQUIRE(climbed.built);
    CHECK(climbed.hasVertex(1088, -64, 128));
    CHECK(climbed.hasVertex(960, 64, 128));
    CHECK(climbed.hasVertex(1152, -128, 256));
    CHECK(climbed.hasVertex(960, 64, 384));
    CHECK(climbed.hasVertex(1088, 1024, 256));
    CHECK(climbed.hasVertex(1152, 1024, 384));
    CHECK(climbed.hasVertex(1088, 1024, 512));
    // Between two bends of different turn a climbing side is not flat: two triangles for each, as the Hive has
    // them. The flat floor's are walked.
    size_t floors = 0;

    for (const OpenYAMM::Game::IndoorFace &face : climbed.map.faces)
    {
        CHECK(face.vertexIndices.size() <= 6);

        if (face.textureName == "floor")
        {
            CHECK(face.vertexIndices.size() == 3);
            CHECK(std::abs(faceNormal(climbed, face)[2]) / (2.0 * faceArea(climbed, face)) > 0.74);
            ++floors;
        }
    }

    CHECK(floors == 4);
    CHECK(floorHeightAt(climbed, 1, 512.0, 0.0) == doctest::Approx(64.0).epsilon(0.1));
    CHECK(floorHeightAt(climbed, 1, 1024.0, 512.0) == doctest::Approx(192.0).epsilon(0.1));

    // A ceiling that runs to another height: the section's top follows it, its sides stay.
    std::string raised = rooms;
    raised.replace(raised.find("ceiling: 256"), 12, "ceiling: 256, ceiling_slope: {to: 384}");
    const BuiltRooms higher = buildRooms(raised);
    INFO(issueText(higher));
    REQUIRE(higher.built);
    CHECK(higher.hasVertex(1088, 1024, 384));
    CHECK(higher.hasVertex(1152, 1024, 128));
    CHECK(higher.hasVertex(1088, -64, 320));
    CHECK(higher.levelsOver(1, 512.0, 0.0, true) == std::vector<int>{0});

    // What is refused, and how to mend it.
    const auto refused = [&rooms](const std::string &from, const std::string &to, const std::string &objects)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = objects.empty() ? buildRooms(changed) : buildRooms(changed, objects);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    CHECK(refused("[[-64, 0], [64, 0], [128, 128]", "[[-64, 0], [64, 0], [32, 128]", "")
        .find("a section's outline is the tunnel cut across its way") != std::string::npos);
    CHECK(refused("[[-64, 0], [64, 0], [128, 128]", "[[-64, 8], [64, 0], [128, 128]", "")
        .find("It begins with the flat floor") != std::string::npos);
    CHECK(refused("ceiling: 256", "ceiling: 300", "").find("the section is 256 high, so with `floor` 0 the tunnel's "
        "`ceiling` (its height at the path's first point) is 256, not 300") != std::string::npos);
    CHECK(refused("floor: 0", "width: 256, floor: 0", "").find("takes no `width`: the section's own points give "
        "its width") != std::string::npos);
    // (Since S8c a platform stands on the flat floor: tests/S8cTests.cpp.)
    CHECK(refused("floor: 0", "floor: 0, pillars: [{at: [512, 0], size: [64, 64]}]", "")
        .find("a tunnel (a `path` room with a `section`) takes no `pillars`") != std::string::npos);
    CHECK(refused("ceiling: 256", "ceiling: 256, ceiling_slope: {to: 140}", "")
        .find("comes within 16 units of the section's sides, which stand to 128 there") != std::string::npos);
    CHECK(refused("path: [[0, 0], [1024, 0], [1024, 1024]]", "outline: [[0, 0], [512, 0], [512, 512], [0, 512]]", "")
        .find("a `section` is the cross-section of a `path` room") != std::string::npos);
    // What stands on a floor stands on the flat floor, not over a leaning side.
    CHECK(refused("floor: 0", "floor:  0", "format: 0\nstart: {room: room:a, at: [512, 100]}\n")
        .find("lies over a leaning side of the tunnel room:a, not on its flat floor") != std::string::npos);
}

TEST_CASE("a tunnel's mouth has its section's shape: into a room's wall, through a thick wall, tunnel to tunnel")
{
    // Tunnel c runs into tunnel a end to end; a opens into hall b through a wall without thickness and tunnel d
    // into the same hall through a wall 64 thick.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0]], floor: 0, ceiling: 256, " + HexagonSection + "}\n"
        "  - {id: room:b, outline: [[1024, -256], [1536, -256], [1536, 256], [1024, 256]], floor: 0, ceiling: 384}\n"
        "  - {id: room:c, path: [[-1024, 0], [0, 0]], floor: 0, ceiling: 256, " + HexagonSection + "}\n"
        "  - {id: room:d, path: [[1280, -1024], [1280, -320]], floor: 64, ceiling: 320, " + HexagonSection + "}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, shape: section}\n"
        "  - {id: open:ca, from: room:c, to: room:a, shape: section}\n"
        "  - {id: open:db, from: room:d, to: room:b, shape: section}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    // Three mouths, each one face with the section's six corners: no lintel, no jambs.
    CHECK(portalShapes(built) == std::vector<std::array<int, 3>>{{6, 0, 256}, {6, 64, 320}});
    size_t portals = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        portals += face.isPortal ? 1 : 0;
    }

    CHECK(portals == 3);
    // Tunnel a has no wall at either end and its six sides; c and d have one end wall each. Tunnel d goes on
    // through the wall's thickness with six more sides: one more floor, one more ceiling.
    CHECK(facetCounts(built, 1) == std::map<int, int>{{1, 4}, {3, 1}, {5, 1}});
    CHECK(facetCounts(built, 3) == std::map<int, int>{{1, 5}, {3, 1}, {5, 1}});
    CHECK(facetCounts(built, 4) == std::map<int, int>{{1, 9}, {3, 2}, {5, 2}});
    CHECK(built.hasVertex(1344, -256, 64));
    CHECK(built.hasVertex(1408, -256, 192));
    // The hall's west wall is cut round the mouth: whole wall at both sides, a triangle under each leaning lower
    // side, a piece over each leaning upper side and one over the ceiling. Nothing stands in the mouth.
    size_t westFaces = 0;
    size_t westTriangles = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        bool onWest = !face.isPortal && face.roomNumber == 2;

        for (const uint16_t vertex : face.vertexIndices)
        {
            onWest = onWest && built.map.vertices[vertex].x == 1024;
        }

        if (onWest)
        {
            ++westFaces;
            westTriangles += face.vertexIndices.size() == 3 ? 1 : 0;
            const std::array<int, 2> range = built.heights(face);
            bool besideMouth = true;

            for (const uint16_t vertex : face.vertexIndices)
            {
                besideMouth = besideMouth && std::abs(built.map.vertices[vertex].y) >= 64;
            }

            // A face that spans the mouth's middle lies over it.
            CHECK((besideMouth || range[0] >= 256));
        }
    }

    CHECK(westFaces == 7);
    CHECK(westTriangles == 2);
    CHECK(built.hasVertex(1024, 128, 128));
    CHECK(built.hasVertex(1024, -128, 128));

    const auto refused = [&rooms](const std::string &from, const std::string &to, const std::string &objects)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = objects.empty() ? buildRooms(changed) : buildRooms(changed, objects);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    // A plain opening in a tunnel's end, sizes on a mouth, a door in a mouth.
    CHECK(refused("to: room:b, shape: section}\n  - {id: open:ca", "to: room:b, width: 96, height: 160}\n  - {id: open:ca",
        "").find("give the opening `shape: section`") != std::string::npos);
    CHECK(refused("{id: open:ab, from: room:a, to: room:b, shape: section}",
        "{id: open:ab, from: room:a, to: room:b, shape: section, width: 128}", "")
        .find("Drop `width` (or write `full`)") != std::string::npos);
    CHECK(refused("floor: 0, ceiling: 384", "floor:  0, ceiling: 384",
        "format: 0\nstart: {room: room:b}\ndoors:\n  - {id: door:x, opening: open:db}\n")
        .find("has the shape of the tunnel's section") != std::string::npos);
    // Two tunnels that do not end in the same section; a mouth that leaves the room's wall.
    CHECK(refused("path: [[-1024, 0], [0, 0]], floor: 0, ceiling: 256", "path: [[-1024, 0], [0, 0]], floor: 32, "
        "ceiling: 288", "").find("the two tunnels do not end in one and the same section here") != std::string::npos);
    CHECK(refused("floor: 0, ceiling: 384", "floor: 0, ceiling: 200", "")
        .find("the tunnel's mouth does not lie in the wall of room:b") != std::string::npos);
    // A tunnel that ends askew: its mouth must be one flat face, so the section's points at the end stand on the
    // line of whole-unit points nearest to square across the way (here in steps of [4, -3]: 13 steps for 64, 26
    // for 128), and the room's wall runs on that line.
    const BuiltRooms askew = buildRooms(
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [600, 800]], floor: 0, ceiling: 256, " + HexagonSection + "}\n"
        "  - {id: room:b, outline: [[496, 878], [704, 722], [1304, 1522], [1096, 1678]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, shape: section}\n");
    INFO(issueText(askew));
    REQUIRE(askew.built);
    CHECK(portalShapes(askew) == std::vector<std::array<int, 3>>{{6, 0, 256}});
    CHECK(askew.hasVertex(704, 722, 128));
    CHECK(askew.hasVertex(496, 878, 128));
    CHECK(askew.hasVertex(652, 761, 0));
    CHECK(askew.hasVertex(548, 839, 256));
}

TEST_CASE("the points of a path give the floor's height each: level, a ramp and level again in one room")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0, 0], [512, 0, 0], [1024, 0, 128], [1024, 512, 128]], width: 128, floor: 0,\n"
        "     ceiling: 192}\n"
        "  - {id: room:b, outline: [[896, 544], [1152, 544], [1152, 800], [896, 800]], floor: 128, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 96, height: 160}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    // Level to the second point, a ramp to the bend, level beyond it; the ceiling 192 above the floor throughout.
    CHECK(floorHeightAt(built, 1, 256.0, 0.0) == doctest::Approx(0.0));
    CHECK(floorHeightAt(built, 1, 768.0, 0.0) == doctest::Approx(64.0).epsilon(0.1));
    CHECK(floorHeightAt(built, 1, 1024.0, 256.0) == doctest::Approx(128.0));
    CHECK(built.hasVertex(512, -64, 0));
    CHECK(built.hasVertex(512, 64, 192));
    CHECK(built.hasVertex(1088, -64, 128));
    CHECK(built.hasVertex(960, 64, 320));
    CHECK(built.hasVertex(1088, 512, 128));
    CHECK(portalShapes(built) == std::vector<std::array<int, 3>>{{4, 128, 288}});

    // In a tunnel with a section, smoothed: the heights are smoothed with the line.
    const BuiltRooms tunnel = buildRooms(
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0, 0], [1024, 0, 0], [2048, 0, 256], [2048, 1024, 256]], smooth: 1, floor: 0,\n"
        "     ceiling: 256, " + HexagonSection + "}\n");
    INFO(issueText(tunnel));
    REQUIRE(tunnel.built);
    CHECK(floorHeightAt(tunnel, 1, 256.0, 0.0) == doctest::Approx(0.0));
    CHECK(floorHeightAt(tunnel, 1, 2048.0, 900.0) == doctest::Approx(256.0));
    CHECK(floorHeightAt(tunnel, 1, 1536.0, 0.0) > 64.0);
    CHECK(floorHeightAt(tunnel, 1, 1536.0, 0.0) < 192.0);

    const auto refused = [&rooms](const std::string &from, const std::string &to)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = buildRooms(changed);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    CHECK(refused("[512, 0, 0]", "[512, 0]").find("give every point of the path a height") != std::string::npos);
    CHECK(refused("floor: 0", "floor: 0, slope: {to: 128}").find("the room takes no `slope`") != std::string::npos);
    CHECK(refused("floor: 0", "floor: 32").find("that point says 0 where `floor` says 32") != std::string::npos);
    CHECK(refused("[1024, 0, 128], [1024, 512, 128]", "[1024, 0, 600], [1024, 512, 600]")
        .find("too steep to walk up") != std::string::npos);
}

#include "core/HeightMesh.h"

TEST_CASE("a region is cut into triangles between its points and along given lines, and flat ones are joined")
{
    const std::vector<Point2> square = {{0.0, 0.0}, {1024.0, 0.0}, {1024.0, 1024.0}, {0.0, 1024.0}};
    std::vector<Point2> vertices;
    std::vector<std::array<size_t, 3>> triangles;
    std::string error;

    // A point in the middle: four triangles round it.
    REQUIRE(triangulateRegion(square, {{512.0, 512.0}}, {}, vertices, triangles, error));
    CHECK(vertices.size() == 5);
    CHECK(triangles.size() == 4);

    // Without it the square is two triangles, along the diagonal that is asked for.
    REQUIRE(triangulateRegion(square, {}, {{{{0.0, 1024.0}, {1024.0, 0.0}}}}, vertices, triangles, error));
    REQUIRE(triangles.size() == 2);

    for (const std::array<size_t, 3> &triangle : triangles)
    {
        // Neither triangle has both (0, 0) and (1024, 1024).
        CHECK((std::count(triangle.begin(), triangle.end(), size_t(0))
            + std::count(triangle.begin(), triangle.end(), size_t(2))) == 1);
    }

    // Two lines that cross are cut where they cross; a point outside the region is left out.
    REQUIRE(triangulateRegion(
        square, {{2000.0, 2000.0}},
        {{{{256.0, 256.0}, {768.0, 768.0}}}, {{{256.0, 768.0}, {768.0, 256.0}}}}, vertices, triangles, error));
    CHECK(vertices.size() == 9);
    CHECK(std::any_of(vertices.begin(), vertices.end(), [](const Point2 &vertex)
    {
        return std::abs(vertex[0] - 512.0) < 1.0e-6 && std::abs(vertex[1] - 512.0) < 1.0e-6;
    }));
    double area = 0.0;

    for (const std::array<size_t, 3> &triangle : triangles)
    {
        area += polygonDoubleArea({vertices[triangle[0]], vertices[triangle[1]], vertices[triangle[2]]}) / 2.0;
    }

    CHECK(area == doctest::Approx(1024.0 * 1024.0));

    // A grid of lines that cross nine times, a point on one of them and a line that ends on another: every pass of
    // the splitting erases edges of the set it searches (S5 spike 4: the search went on with erased iterators,
    // which crashed a long-lived wasm core; an AddressSanitizer build of this suite reports it).
    std::vector<std::array<Point2, 2>> grid;

    for (const double at : {256.0, 512.0, 768.0})
    {
        grid.push_back({Point2{128.0, at}, Point2{896.0, at}});
        grid.push_back({Point2{at, 128.0}, Point2{at, 896.0}});
    }

    grid.push_back({Point2{384.0, 0.0}, Point2{384.0, 512.0}});
    std::vector<Point2> again;
    std::vector<std::array<size_t, 3>> againTriangles;
    REQUIRE(triangulateRegion(square, {{512.0, 300.0}}, grid, vertices, triangles, error));
    REQUIRE(triangulateRegion(square, {{512.0, 300.0}}, grid, again, againTriangles, error));
    CHECK(vertices == again);
    CHECK(triangles == againTriangles);
    // 4 corners, 14 line ends (the last line's lie on the square's edge and on the line y = 512), the point on the
    // line x = 512, and 9 + 1 crossings (the last line crosses y = 256).
    CHECK(vertices.size() == 4 + 14 + 1 + 9 + 1);
    area = 0.0;

    for (const std::array<size_t, 3> &triangle : triangles)
    {
        area += polygonDoubleArea({vertices[triangle[0]], vertices[triangle[1]], vertices[triangle[2]]}) / 2.0;
    }

    CHECK(area == doctest::Approx(1024.0 * 1024.0));

    // Heights: straight between the points; flat triangles join to one face, others stay apart.
    HeightMesh mesh;
    REQUIRE(triangulateRegion(square, {{512.0, 512.0}}, {}, vertices, mesh.triangles, error));
    std::vector<std::array<int64_t, 3>> corners;

    for (const Point2 &vertex : vertices)
    {
        const double height = vertex[0] == 512.0 ? 64.0 : 0.0;
        mesh.points.push_back({vertex[0], vertex[1], height});
        corners.push_back({std::lround(vertex[0]), std::lround(vertex[1]), std::lround(height)});
    }

    CHECK(meshHeightAt(mesh, 256.0, 512.0) == doctest::Approx(32.0));
    CHECK(meshHeightAt(mesh, 512.0, 512.0) == doctest::Approx(64.0));
    CHECK(meshLowest(mesh) == 0.0);
    CHECK(meshHighest(mesh) == 64.0);
    CHECK(meshTriangleGradient(mesh, 0) == doctest::Approx(0.125));
    CHECK(meshBreaksAlong(mesh, {0.0, 512.0}, {1024.0, 512.0}) == std::vector<double>{512.0});
    CHECK(mergeFlatTriangles(corners, mesh.triangles, 20).size() == 4);

    for (std::array<int64_t, 3> &corner : corners)
    {
        corner[2] = 0;
    }

    const std::vector<std::vector<size_t>> level = mergeFlatTriangles(corners, mesh.triangles, 20);
    REQUIRE(level.size() == 1);
    CHECK(level[0].size() == 4);
}

TEST_CASE("an uneven floor runs in flat triangles between its points, and walls, openings and blocks follow it")
{
    const auto cave = [](const std::string &sill)
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    floor_points: [[1024, 1024, 128], [1024, 0, 64], [512, 512, -32]" + sill + "]\n"
            "    ceiling: 512\n"
            "    platforms:\n"
            "      - {at: [256, 512], size: [64, 64], rise: 40}\n"
            "  - id: room:b\n"
            "    outline: [[1040, 256], [1536, 256], [1536, 768], [1040, 768]]\n"
            "    floor: 64\n"
            "    ceiling: 512\n"
            "openings:\n"
            "  - {id: open:ab, from: room:a, to: room:b, width: 256, height: 256}\n";
    };
    const BuiltRooms built = buildRooms(cave(", [1024, 384, 64], [1024, 640, 64]"));
    INFO(issueText(built));
    REQUIRE(built.built);
    // The floor's own points, and the walls' feet at them.
    CHECK(built.hasVertex(512, 512, -32));
    CHECK(built.hasVertex(1024, 1024, 128));
    CHECK(built.hasVertex(1024, 0, 64));
    CHECK(built.hasVertex(0, 1024, 0));
    // The doorway stands on its level sill at 64, 256 high.
    CHECK(built.hasVertex(1040, 384, 64));
    CHECK(built.hasVertex(1040, 640, 320));
    // The block stands 40 above the floor under its middle (-16 there) and reaches down to the lowest floor under
    // its corners.
    CHECK(built.hasVertex(224, 480, 24));
    CHECK(built.hasVertex(224, 480, -18));
    // The floor is triangles between the points (those that lie in one plane are joined to one face).
    size_t slopingFloors = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.roomNumber == 1 && (face.facetType == 3 || face.facetType == 4) && face.vertexIndices.size() == 3)
        {
            ++slopingFloors;
        }
    }

    CHECK(slopingFloors >= 3);

    // Where the floor is not level along the opening its sill rakes with it (since 2026-11-13; refused before):
    // from 88 to 104 here, the top level 256 above the sill's lowest point.
    const BuiltRooms raking = buildRooms(cave(""));
    INFO(issueText(raking));
    REQUIRE(raking.built);
    CHECK(raking.hasVertex(1040, 384, 88));
    CHECK(raking.hasVertex(1040, 640, 104));
    CHECK(raking.hasVertex(1040, 384, 344));
    CHECK(raking.hasVertex(1040, 640, 344));
}

TEST_CASE("a floor that is one plane in any direction has every corner on it, and a too steep floor is refused")
{
    const auto room = [](const std::string &floor, const std::string &ceiling = "512")
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n" + floor + "    ceiling: " + ceiling + "\n";
    };
    const BuiltRooms plane = buildRooms(room("    floor_plane: [[0, 0, 0], [512, 0, 32], [0, 512, 32]]\n"));
    INFO(issueText(plane));
    REQUIRE(plane.built);
    CHECK(plane.hasVertex(0, 0, 0));
    CHECK(plane.hasVertex(1024, 0, 64));
    CHECK(plane.hasVertex(0, 1024, 64));
    CHECK(plane.hasVertex(1024, 1024, 128));

    const auto refused = [&room](const std::string &floor, const std::string &ceiling = "512")
    {
        const BuiltRooms built = buildRooms(room(floor, ceiling));
        return built.built ? std::string("built") : issueText(built);
    };
    // 600 over 512 is too steep to walk: refused with the triangle, allowed as a rock bank, never above 2.
    const std::string steep = refused("    floor_points: [[512, 512, 600]]\n", "900");
    CHECK(steep.find("rises 1.17 for each unit of run") != std::string::npos);
    CHECK(steep.find("`steep_floor: true`") != std::string::npos);
    CHECK(refused("    floor_points: [[512, 512, 600]]\n    steep_floor: true\n", "900") == "built");
    CHECK(refused("    floor_points: [[512, 512, 1200]]\n    steep_floor: true\n", "1400")
        .find("steeper is a wall") != std::string::npos);
    CHECK(refused("    floor_points: [[2000, 0, 8]]\n").find("lies outside the outline") != std::string::npos);
    CHECK(refused("    floor_points: [[512, 512, 8]]\n    floor_lines: [[[512, 512], [700, 700]]]\n")
        .find("[700, 700] is neither") != std::string::npos);
    CHECK(refused(
        "    floor_points: [[256, 256, 8], [768, 768, 8], [256, 768, 8], [768, 256, 8]]\n"
        "    floor_lines: [[[256, 256], [768, 768]], [[256, 768], [768, 256]]]\n")
        .find("cross at [512, 512]") != std::string::npos);
    CHECK(refused("    slope: {to: 64, toward: north}\n    floor_points: [[512, 512, 8]]\n")
        .find("in place of `slope`") != std::string::npos);
    CHECK(refused("    floor_points: [[512, 512, 504]]\n    steep_floor: true\n")
        .find("at least 16 above the floor") != std::string::npos);
}

TEST_CASE("an uneven ceiling comes down to its points, and an opening reaches only as high as it does there")
{
    const BuiltRooms built = buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 448\n"
        "    ceiling_points: [[0, 0, 192], [0, 1024, 192], [640, 384, 576]]\n"
        "    pillars:\n"
        "      - {at: [640, 384], size: [64, 64]}\n"
        "  - id: room:c\n"
        "    outline: [[-512, 256], [-16, 256], [-16, 768], [-512, 768]]\n"
        "    floor: 0\n"
        "    ceiling: 300\n"
        "openings:\n"
        "  - {id: open:ac, from: room:a, to: room:c, width: 256, height: full}\n");
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(built.hasVertex(0, 0, 192));
    CHECK(built.hasVertex(0, 1024, 192));
    CHECK(built.hasVertex(1024, 0, 448));
    // The mouth is as high as the ceiling over it (192), not as the neighbour's (300).
    CHECK(built.hasVertex(-16, 384, 192));

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.isPortal)
        {
            CHECK(built.heights(face)[1] == 192);
        }
    }

    // The pillar under the crown ends at the ceiling over its corners, below the crown's 576.
    CHECK_FALSE(built.hasVertex(608, 352, 448));
    bool pillarTop = false;

    for (const OpenYAMM::Game::IndoorVertex &vertex : built.map.vertices)
    {
        pillarTop = pillarTop || (vertex.x == 608 && vertex.y == 352 && vertex.z > 500 && vertex.z < 576);
    }

    CHECK(pillarTop);
}

TEST_CASE("a level's banks slope from its floor to the room's by each side's run, and what stands on one stands there")
{
    const auto room = [](const std::string &level, const std::string &more = "")
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n" + more + "    ceiling: 512\n"
            "    platforms:\n"
            "      - {at: [512, 304], size: [32, 32], rise: 24}\n"
            "    levels:\n"
            "      - {outline: [[256, 384], [768, 384], [768, 640], [256, 640]], " + level + "}\n";
    };
    // A trench: banks on its two long sides, upright ends.
    const BuiltRooms trench = buildRooms(room("floor: -128, bank: [160, 0, 160, 0]"));
    INFO(issueText(trench));
    REQUIRE(trench.built);
    CHECK(trench.hasVertex(256, 384, -128));
    CHECK(trench.hasVertex(256, 224, 0));
    CHECK(trench.hasVertex(768, 800, 0));
    // The block on the south bank, half way down it: from -64 to -40.
    CHECK(trench.hasVertex(496, 288, -64));
    CHECK(trench.hasVertex(496, 288, -40));

    // A mound: a raised level whose foot is its outline grown by the run.
    const BuiltRooms mound = buildRooms(room("floor: 96, bank: 128"));
    INFO(issueText(mound));
    REQUIRE(mound.built);
    CHECK(mound.hasVertex(256, 384, 96));
    CHECK(mound.hasVertex(128, 256, 0));
    CHECK(mound.hasVertex(896, 768, 0));

    const auto refused = [&room](const std::string &level, const std::string &more = "")
    {
        const BuiltRooms built = buildRooms(room(level, more));
        return built.built ? std::string("built") : issueText(built);
    };
    CHECK(refused("floor: -128, bank: 100").find("Give a run of at least 143") != std::string::npos);
    CHECK(refused("floor: -128, bank: 100", "    steep_floor: true\n") == "built");
    CHECK(refused("floor: -128, bank: 60", "    steep_floor: true\n").find("it is a wall") != std::string::npos);
    CHECK(refused("floor: -128, bank: [160, 0, 160]").find("one run for each side") != std::string::npos);
}

TEST_CASE("a block's top slopes as a plane or by a height at each corner; a chest and a flight's head stand on it")
{
    const auto room = [](const std::string &blocks, const std::string &more = "")
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n" + more + "    ceiling: 512\n"
            "    platforms:\n" + blocks;
    };
    const BuiltRooms built = buildRooms(
        room(
            "      - {at: [512, 512], size: [256, 512], rise: 0, top_slope: {to: 128, toward: north}}\n"
            "      - {at: [200, 200], size: [128, 128], rise: 0, top_heights: [0, 32, 64, 16]}\n"
            "    flights:\n"
            "      - {from: [512, 960], to: [512, 768], steps: 4}\n"),
        "format: 0\nstart: {room: room:a, at: [900, 100]}\n"
        "chests:\n  - {id: chest:on, room: room:a, at: [512, 640], size: [64, 48, 40]}\n");
    INFO(issueText(built));
    REQUIRE(built.built);
    // The wedge: 0 along its south side, 128 along its north.
    CHECK(built.hasVertex(384, 768, 128));
    CHECK(built.hasVertex(640, 768, 128));
    CHECK(built.hasVertex(384, 256, 0));
    CHECK_FALSE(built.hasVertex(384, 256, 128));
    // A height at each corner.
    CHECK(built.hasVertex(264, 264, 64));
    CHECK(built.hasVertex(136, 264, 16));
    // The chest stands on the slope (96 under its middle), and the flight ends level with the wedge's high edge.
    CHECK(built.hasVertex(480, 616, 136));
    CHECK(built.hasVertex(416, 816, 128));

    const auto refused = [&room](const std::string &blocks, const std::string &more = "")
    {
        const BuiltRooms result = buildRooms(room(blocks, more));
        return result.built ? std::string("built") : issueText(result);
    };
    const std::string wedge = "      - {at: [512, 512], size: [256, 128], rise: 0, top_slope: {to: 200, toward: north}}\n";
    CHECK(refused(wedge).find("the party walks up at most 0.9") != std::string::npos);
    CHECK(refused(wedge, "    steep_floor: true\n") == "built");
    CHECK(refused("      - {at: [512, 512], size: [256, 128], rise: 0}\n")
        .find("a block's `rise` is more than 0") != std::string::npos);
}

TEST_CASE("a flight begins on the floor its from_height names, and one that is open below has a raking underside")
{
    // Two slabs one above the other and a third to climb to: the flight leaves the lower slab's edge.
    const auto tower = [](const std::string &flight)
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [2048, 0], [2048, 2048], [0, 2048]]\n"
            "    floor: 0\n"
            "    ceiling: 1024\n"
            "    platforms:\n"
            "      - {at: [1024, 512], size: [640, 256], rise: 16, base: 400}\n"
            "      - {at: [1024, 512], size: [640, 256], rise: 16, base: 912}\n"
            "      - {at: [768, 1088], size: [128, 128], rise: 16, base: 528}\n"
            "    flights:\n"
            "      - {from: [768, 640], to: [768, 1024], to_height: 544, width: 128, steps: 4" + flight + "}\n";
    };
    const BuiltRooms highest = buildRooms(tower(""));
    CHECK_FALSE(highest.built);
    CHECK(issueText(highest).find("a flight runs from a point on the lower floor") != std::string::npos);

    const BuiltRooms named = buildRooms(tower(", from_height: 416"));
    INFO(issueText(named));
    REQUIRE(named.built);
    // Four steps of 32 from 416; solid down to the slab's height and no further.
    CHECK(named.hasVertex(704, 640, 448));
    CHECK(named.hasVertex(704, 1024, 544));
    CHECK(named.hasVertex(704, 928, 416));
    CHECK_FALSE(named.hasVertex(704, 928, 480));
    CHECK(issueText(buildRooms(tower(", from_height: 300"))).find("there is no floor at 300") != std::string::npos);

    // Open below: under the third step the underside runs from 448 to 480, a slab of 32 under the steps' line.
    const BuiltRooms open = buildRooms(tower(", from_height: 416, open_below: true"));
    INFO(issueText(open));
    REQUIRE(open.built);
    CHECK(open.hasVertex(704, 928, 480));
    CHECK(open.hasVertex(704, 832, 448));
    CHECK_FALSE(open.hasVertex(704, 928, 416));
}

TEST_CASE("a tunnel's square end: its sides run from the section to a rectangle that is all doorway, with a door")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0]], floor: 0, ceiling: 256,\n"
        "     section: {outline: [[-64, 0], [64, 0], [128, 128], [64, 256], [-64, 256], [-128, 128]],\n"
        "       end: {length: 136, width: 224}}}\n"
        "  - {id: room:b, outline: [[1056, -256], [1568, -256], [1568, 256], [1056, 256]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ba, from: room:b, to: room:a, width: full, height: full}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:b}\ndoors:\n  - {id: door:x, opening: open:ba, thickness: 16}\n";
    const BuiltRooms built = buildRooms(rooms, objects);
    INFO(issueText(built));
    REQUIRE(built.built);
    // The section stands whole 136 before the end; the end is a rectangle 224 wide from floor to ceiling.
    CHECK(built.hasVertex(888, -128, 128));
    CHECK(built.hasVertex(888, 64, 0));
    CHECK(built.hasVertex(1024, -112, 0));
    CHECK(built.hasVertex(1024, 112, 256));
    CHECK_FALSE(built.hasVertex(1024, -128, 128));
    CHECK(portalShapes(built) == std::vector<std::array<int, 3>>{{4, 0, 256}});
    // Six sides over the first stretch and a wall at the start; then a floor, a ceiling and, for each side, a
    // lower triangle, an upright triangle and an upper triangle, as the Hive's tunnels end at their doors.
    size_t faces = 0;
    size_t triangles = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        bool inTunnel = !face.isPortal && face.roomNumber == 1;

        for (const uint16_t vertex : face.vertexIndices)
        {
            inTunnel = inTunnel && built.map.vertices[vertex].x <= 1024;
        }

        faces += inTunnel ? 1 : 0;
        triangles += inTunnel && face.vertexIndices.size() == 3 ? 1 : 0;
    }

    CHECK(faces == 15);
    CHECK(triangles == 6);
    CHECK(built.levelsOver(1, 960.0, 0.0, true) == std::vector<int>{0});
    CHECK(built.levelsOver(1, 960.0, 0.0, false) == std::vector<int>{256});

    const auto refused = [&rooms](const std::string &from, const std::string &to)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = buildRooms(changed);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    CHECK(refused("width: full, height: full", "width: 96, height: 160")
        .find("the square end of the tunnel room:a is all doorway: it is 224 wide and stands from 0 to 256")
        != std::string::npos);
    CHECK(refused("length: 136", "length: 1020").find("leaves at least 16 of that stretch") != std::string::npos);
    CHECK(refused("[64, 256], [-64, 256]", "[0, 256]").find("a square end needs a section with a flat ceiling")
        != std::string::npos);

    // Without `length` the sides run to the square end over the whole last stretch, from the section on the
    // bend's mitre: no point is added to the path.
    const BuiltRooms whole = buildRooms(
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0], [1024, 512]], floor: 0, ceiling: 256,\n"
        "     section: {outline: [[-64, 0], [64, 0], [128, 128], [64, 256], [-64, 256], [-128, 128]],\n"
        "       end: {width: 224}}}\n");
    INFO(issueText(whole));
    REQUIRE(whole.built);
    CHECK(whole.hasVertex(1136, 512, 0));
    CHECK(whole.hasVertex(912, 512, 256));
    CHECK(whole.hasVertex(1152, -128, 128));
    CHECK_FALSE(whole.hasVertex(1152, 512, 128));
}

TEST_CASE("a path room that climbs opens in its side: the doorway stands level on the floor at its higher side")
{
    // The corridor climbs from 0 to 256 over 1024; a doorway 128 wide in its south wall from x 448 to 576, where
    // its floor runs from 112 to 144, into a room whose floor is at 128.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0]], width: 256, floor: 0, slope: {to: 256}, ceiling: 320}\n"
        "  - {id: room:d, outline: [[384, -512], [640, -512], [640, -160], [384, -160]], floor: 128, ceiling: 448}\n"
        "openings:\n"
        "  - {id: open:ad, from: room:a, to: room:d, width: 128, height: 192}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(portalShapes(built) == std::vector<std::array<int, 3>>{{4, 144, 336}});
    // The wall under the doorway is a wedge from the raking floor up to the level sill.
    CHECK(built.hasVertex(448, -128, 112));
    CHECK(built.hasVertex(448, -128, 144));
    CHECK(built.hasVertex(576, -128, 144));
    size_t wedges = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        bool underSill = !face.isPortal && face.roomNumber == 1 && face.vertexIndices.size() == 3;

        for (const uint16_t vertex : face.vertexIndices)
        {
            underSill = underSill && built.map.vertices[vertex].y == -128 && built.map.vertices[vertex].z <= 144
                && built.map.vertices[vertex].x >= 448 && built.map.vertices[vertex].x <= 576;
        }

        wedges += underSill ? 1 : 0;
    }

    CHECK(wedges == 1);
    // The floor still runs unbroken past the doorway.
    CHECK(floorHeightAt(built, 1, 512.0, -100.0) == doctest::Approx(128.0).epsilon(0.02));

    // With a sill the doorway begins that much higher; in the side of a ramp that names a wall it is refused.
    std::string raised = rooms;
    raised.replace(raised.find("width: 128, height: 192"), 23, "width: 128, height: 192, sill: 16");
    CHECK(portalShapes(buildRooms(raised)) == std::vector<std::array<int, 3>>{{4, 160, 352}});
    const BuiltRooms ramp = buildRooms(
        "rooms:\n"
        "  - {id: room:a, outline: [[0, -128], [1024, -128], [1024, 128], [0, 128]], floor: 0,\n"
        "     slope: {to: 256, toward: east}, ceiling: 576}\n"
        "  - {id: room:d, outline: [[384, -512], [640, -512], [640, -160], [384, -160]], floor: 128, ceiling: 448}\n"
        "openings:\n"
        "  - {id: open:ad, from: room:a, to: room:d, width: 128, height: 192}\n");
    CHECK_FALSE(ramp.built);
    CHECK(issueText(ramp).find("the opening is in a wall the floor rises along") != std::string::npos);
}

TEST_CASE("a tunnel opens in its side: an upright wall with the doorway, and its leaning sides run to the jambs")
{
    // A doorway 256 wide and as high as the tunnel in its south side, from x 384 to 640, through a wall 32 thick.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0]], floor: 0, ceiling: 256, " + HexagonSection + "}\n"
        "  - {id: room:e, outline: [[256, -512], [768, -512], [768, -160], [256, -160]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ae, from: room:a, to: room:e, width: 256, height: 256}\n";
    const BuiltRooms built = buildRooms(rooms);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(portalShapes(built) == std::vector<std::array<int, 3>>{{4, 0, 256}});

    // The jambs stand on the line of the section's widest place, from the floor to the ceiling.
    for (const std::array<int, 3> &corner : std::vector<std::array<int, 3>>{
             {384, -128, 0}, {384, -128, 256}, {640, -128, 0}, {640, -128, 256}})
    {
        CHECK(built.hasVertex(corner[0], corner[1], corner[2]));
    }

    // The north side runs on unbroken (two faces); floor and ceiling strips; in the south side a lower, an upright
    // and an upper triangle before the doorway and after it, a piece of floor and of ceiling out to the doorway,
    // and the doorway's own floor, jambs and soffit through the wall; a wall at each end.
    size_t faces = 0;
    size_t triangles = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        faces += !face.isPortal && face.roomNumber == 1 ? 1 : 0;
        triangles += !face.isPortal && face.roomNumber == 1 && face.vertexIndices.size() == 3 ? 1 : 0;
    }

    CHECK(faces == 18);
    CHECK(triangles == 6);
    // The floor reaches out to the doorway between the jambs.
    CHECK(built.levelsOver(1, 512.0, -100.0, true) == std::vector<int>{0});
    CHECK(built.levelsOver(1, 200.0, -110.0, true).empty());

    // In a tunnel that climbs (0 to 128 over 1024) the jambs' feet stand at 48 and 80: the doorway begins level at
    // 80 over a wedge of wall, and ends under the ceiling at its lower jamb (304).
    const BuiltRooms climbing = buildRooms(
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0]], floor: 0, slope: {to: 128}, ceiling: 256, " + HexagonSection
        + "}\n"
        "  - {id: room:e, outline: [[256, -512], [768, -512], [768, -160], [256, -160]], floor: 64, ceiling: 320}\n"
        "openings:\n"
        "  - {id: open:ae, from: room:a, to: room:e, width: 256, height: 192}\n");
    INFO(issueText(climbing));
    REQUIRE(climbing.built);
    CHECK(portalShapes(climbing) == std::vector<std::array<int, 3>>{{4, 80, 272}});
    CHECK(climbing.hasVertex(384, -128, 48));
    CHECK(climbing.hasVertex(384, -128, 80));
    CHECK(climbing.hasVertex(640, -128, 80));
    CHECK(climbing.hasVertex(384, -128, 272));
    CHECK(climbing.hasVertex(384, -128, 304));
    CHECK(climbing.hasVertex(640, -128, 336));

    const auto refused = [&rooms](const std::string &from, const std::string &to)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = buildRooms(changed);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    // Too near a point of the path; a second doorway in the same side of the same stretch; a gable.
    CHECK(refused("[[256, -512], [768, -512], [768, -160], [256, -160]]",
        "[[0, -512], [300, -512], [300, -160], [0, -160]]").find("keep it 32 clear of both") != std::string::npos);
    CHECK(refused("width: 256, height: 256}\n", "width: 96, height: 256, along: 0.2}\n"
        "  - {id: open:ae2, from: room:a, to: room:e, width: 96, height: 256, along: 0.8}\n")
        .find("has a doorway already (open:ae)") != std::string::npos);
    CHECK(refused("width: 256, height: 256}", "width: 256, height: 128, shape: gable, apex: 200}")
        .find("a doorway in a tunnel's side is a rectangle") != std::string::npos);
}

TEST_CASE("a plate lies across the floor of a path room that climbs and of a tunnel, between two lines across the way")
{
    // A corridor 224 wide that climbs 64 over 1748 of way, with a plate over x 384 to 640 of its first stretch.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0], [1536, 512]], width: 224, floor: 0, slope: {to: 64},\n"
        "     ceiling: 256}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [100, 0]}\nplates:\n"
        "  - {id: plate:pad, room: room:a, at: [512, 0], size: [256, 128], surface: {texture: pad, size: [64, 64]}}\n";
    const BuiltRooms built = buildRooms(rooms, objects);
    INFO(issueText(built));
    REQUIRE(built.built);
    // The plate's faces cover the floor's whole width between its two lines, and nothing else of it.
    const auto padArea = [](const BuiltRooms &map)
    {
        double area = 0.0;

        for (const OpenYAMM::Game::IndoorFace &face : map.map.faces)
        {
            if (face.textureName == "pad")
            {
                CHECK((face.facetType == 3 || face.facetType == 4));
                area += faceArea(map, face);

                for (const uint16_t vertex : face.vertexIndices)
                {
                    CHECK(map.map.vertices[vertex].x >= 384);
                    CHECK(map.map.vertices[vertex].x <= 640);
                }
            }
        }

        return area;
    };
    CHECK(padArea(built) == doctest::Approx(256.0 * 224.0).epsilon(0.01));
    // The walls and the floor beside the plate have corners where its lines meet them, at the floor's height
    // there (about 14 and 23; the floor is level across only at the path's points).
    const auto cornerAt = [&built](int x, int y, int low, int high)
    {
        for (int z = low; z <= high; ++z)
        {
            if (built.hasVertex(x, y, z))
            {
                return true;
            }
        }

        return false;
    };
    CHECK(cornerAt(384, -112, 12, 16));
    CHECK(cornerAt(384, 112, 12, 16));
    CHECK(cornerAt(640, -112, 21, 26));
    CHECK(cornerAt(640, 112, 21, 26));
    CHECK(cornerAt(384, -112, 250, 290));
    CHECK(floorHeightAt(built, 1, 512.0, 0.0) == doctest::Approx(18.7).epsilon(0.05));
    CHECK(floorHeightAt(built, 1, 200.0, 0.0) == doctest::Approx(7.3).epsilon(0.1));

    // In a tunnel: the flat floor (128 wide) between the two lines; the leaning sides beside it have corners there.
    const BuiltRooms tunnel = buildRooms(
        "rooms:\n"
        "  - {id: room:a, path: [[0, 0], [1024, 0]], floor: 0, ceiling: 256, " + HexagonSection + "}\n",
        objects);
    INFO(issueText(tunnel));
    REQUIRE(tunnel.built);
    CHECK(padArea(tunnel) == doctest::Approx(256.0 * 128.0).epsilon(0.01));
    size_t sideCorners = 0;

    for (const OpenYAMM::Game::IndoorFace &face : tunnel.map.faces)
    {
        if (face.facetType == 1)
        {
            for (const uint16_t vertex : face.vertexIndices)
            {
                const OpenYAMM::Game::IndoorVertex &point = tunnel.map.vertices[vertex];
                sideCorners += (point.x == 384 || point.x == 640) && std::abs(point.y) == 64 && point.z == 0 ? 1 : 0;
            }
        }
    }

    CHECK(sideCorners == 4);

    const auto refused = [&rooms, &objects](const std::string &from, const std::string &to)
    {
        std::string changed = objects;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = buildRooms(rooms, changed);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    CHECK(refused("at: [512, 0]", "at: [120, 0]").find("which takes a plate from 16 to 962") != std::string::npos);
    CHECK(refused("size: [256, 128]", "size: [256, 128], rise: 4").find("drop `rise`") != std::string::npos);
}

// The vocabulary list of round three (2026-11-13): placed monsters and items, blocks that are clicked, things on
// moving parts, movers at a room's limits, insets, door leaves, surfaces, tunnels and uneven ground, and warnings
// that can be answered.

namespace
{
// A project built with an asset root of its own that holds only the tables a test writes: the scene the build
// wrote, read back by the game's reader, and the script.
struct BuiltPlaced
{
    bool built = false;
    std::vector<ProjectIssue> issues;
    std::vector<std::string> warnings;
    std::optional<OpenYAMM::Game::IndoorSceneData> scene;
    OpenYAMM::Game::IndoorMapData map;
    std::string lua;
};

BuiltPlaced buildPlaced(
    const std::string &rooms,
    const std::string &objects,
    const std::vector<std::pair<std::string, std::string>> &tables,
    const std::string &card = CardText,
    const std::string &wiring = "",
    const std::string &atmosphere = "")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_placed_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root / "project");
    std::filesystem::create_directories(root / "assets" / "engine" / "data_tables");
    std::ofstream(root / "project" / "project.yml", std::ios::binary) << card;
    std::ofstream(root / "project" / "rooms.yml", std::ios::binary) << std::string(ThemeText) + rooms;
    std::ofstream(root / "project" / "objects.yml", std::ios::binary) << objects;

    if (!wiring.empty())
    {
        std::ofstream(root / "project" / "wiring.yml", std::ios::binary) << wiring;
    }

    if (!atmosphere.empty())
    {
        std::ofstream(root / "project" / "atmosphere.yml", std::ios::binary) << atmosphere;
    }

    // A table's name may lead out of data_tables (`../../worlds/mm6/maps/<stem>.studio.yml`, an installed map).
    for (const std::pair<std::string, std::string> &table : tables)
    {
        const std::filesystem::path path = root / "assets" / "engine" / "data_tables" / table.first;
        std::filesystem::create_directories(path.parent_path());
        std::ofstream(path, std::ios::binary) << table.second;
    }

    BuiltPlaced built;
    Project project;

    if (loadProject(root / "project", project, built.issues))
    {
        BuildOptions options;
        options.outputDirectory = root / "build";
        options.assetRoot = root / "assets";
        BuildResult result;
        built.built = buildProject(project, options, result);
        built.issues = result.issues;
        built.warnings = result.warnings;

        if (built.built)
        {
            std::ifstream sceneStream(root / "build" / "testmap.scene.yml", std::ios::binary);
            const std::string sceneText(
                (std::istreambuf_iterator<char>(sceneStream)), std::istreambuf_iterator<char>());
            std::string errorMessage;
            built.scene = OpenYAMM::Game::IndoorSceneYmlLoader().loadFromText(sceneText, errorMessage);
            std::ifstream stream(root / "build" / "testmap.blv", std::ios::binary);
            const std::vector<uint8_t> bytes(
                (std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
            const std::optional<OpenYAMM::Game::IndoorMapData> map =
                OpenYAMM::Game::IndoorMapDataLoader().loadFromBytes(bytes);
            built.built = built.scene.has_value() && map.has_value();

            if (map)
            {
                built.map = *map;
            }

            std::ifstream luaStream(root / "build" / "testmap.lua", std::ios::binary);
            built.lua.assign((std::istreambuf_iterator<char>(luaStream)), std::istreambuf_iterator<char>());
        }
    }

    std::filesystem::remove_all(root);
    return built;
}

std::string issueText(const BuiltPlaced &built)
{
    std::string text;

    for (const ProjectIssue &issue : built.issues)
    {
        text += issue.path + ": " + issue.message + "\n";
    }

    return text;
}

// Rows as the game's tables have them: a title line, a header, then rows by number.
const char *const MonsterTableText =
    "Default Monster Data\n"
    "#\tName\tPicture\tLVL\t HP \tAC\t EXP \tTreasure\tBlood\tFly\tMove\tAI Type\tHst\tSpd\tRec\n"
    "1\tGoblin\tGoblin A\t2\t13\t4\t50\t0\t1\tN\tShort\tNormal\t4\t200\t100\n"
    "2\tGoblin\tGoblin B\t4\t26\t6\t90\t0\t1\tN\tShort\tNormal\t4\t220\t100\n"
    "7\tSwordsman\tSwordsman A\t10\t\"1,040\"\t12\t200\t0\t1\tN\tShort\tNormal\t4\t220\t100\n"
    "9\tGhost\tGhost A\t10\t40\t12\t200\t0\t1\tY\tShort\tNormal\t4\t220\t100\n";
const char *const MonsterDescriptorText =
    "Monster Descriptor Data\tDescriptor\n"
    "#\tInternalName\tHeight\tRadius\tMovementSpeed\n"
    "1\tGoblin A\t120\t40\t200\n"
    "2\tGoblin B\t120\t40\t220\n"
    "7\tSwordsman A\t176\t53\t220\n";
const char *const ItemTableText =
    "\n"
    "Item #\tPic File\tName\tValue\tEquip Stat\tSkill Group\tMod1\tMod2\tmaterial\tID/Rep/St\tNot identified name\t"
    "Sprite Index\n"
    "1\titem001\tIron Longsword\t20\tWeapon\tSword\t2d3\t0\t8\t1\tLongsword\t1\n"
    "5\titem005\tMoon Tile\t0\tMisc\tMisc\t0\t0\t0\t1\tTile\t6\n"
    "6\titem006\tKey\t0\tMisc\tMisc\t0\t0\t0\t1\tKey\t9\n"
    "8\titem008\tKey\t0\tMisc\tMisc\t0\t0\t0\t1\tKey\t9\n"
    "9\titem009\tGhost Ring\t0\tMisc\tMisc\t0\t0\t0\t1\tRing\t77\n";
const char *const ObjectTableText =
    "// Name\tSpriteName\tObjectId\tRadius\tHeight\tLifetimeTicks\tSpeed\tSpriteId\n"
    "null\tnull\t0\t32\t32\t0\t0\t0\n"
    "longsword\tobj001\t1\t64\t64\t0\t0\t2\n"
    "\n"
    "tile\tobj006\t6\t64\t64\t0\t0\t31\n"
    "key\tobj009\t9\t64\t64\t0\t0\t40\n";

const std::vector<std::pair<std::string, std::string>> PlacedTables = {
    {"monster_data.txt", MonsterTableText},
    {"monster_descriptors.txt", MonsterDescriptorText},
    {"items.txt", ItemTableText},
    {"object_list.txt", ObjectTableText}};

const char *const PlacedRooms =
    "rooms:\n"
    "  - id: room:a\n"
    "    outline: [[0, 0], [1024, 0], [1024, 512], [0, 512]]\n"
    "    floor: 0\n"
    "    ceiling: 384\n"
    "    platforms:\n"
    "      - {at: [768, 256], size: [128, 128], rise: 64}\n"
    "  - {id: room:b, outline: [[1056, 128], [1312, 128], [1312, 384], [1056, 384]], floor: 0, ceiling: 160}\n"
    "openings:\n"
    "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 128}\n";
}

TEST_CASE("a placed indoor monster writes the signed low word of a large experience reward")
{
    const std::vector<std::pair<std::string, std::string>> tables = {
        {"monster_data.txt", std::string(MonsterTableText)
            + "10049\tHive boss\tBoss\t80\t2000\t40\t100000\t0\t1\tN\tShort\tNormal\t4\t220\t100\n"},
        {"monster_descriptors.txt", std::string(MonsterDescriptorText) + "10049\tBoss\t200\t60\t220\n"}};
    const BuiltPlaced built = buildPlaced(PlacedRooms, "format: 0\nstart: {room: room:a, at: [100, 100]}\n"
        "monsters:\n  - {id: monster:boss, room: room:a, monster: 10049, at: [256, 256]}\n", tables);
    INFO(issueText(built));
    REQUIRE(built.built);
    const auto &actors = built.scene->initialState.actors;
    REQUIRE(actors.size() == 1);
    CHECK(actors[0].monsterInfoId == 10049);
    CHECK(actors[0].monsterId == -31072);
}

TEST_CASE("placed monsters and items on the floor become the scene's actors and sprite objects")
{
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [100, 100]}\n"
        "monsters:\n"
        "  - {id: monster:guard, room: room:a, monster: Swordsman, at: [256, 256], facing: n, group: 54, "
        "hostile: false}\n"
        "  - {id: monster:second, room: room:a, monster: 7, at: [256, 384], facing: 225, group: 54, hostile: false}\n"
        "  - {id: monster:wild, room: room:b, monster: Goblin B, hostile: true}\n"
        "  - {id: monster:plain, room: room:a, monster: 1, at: [768, 256], immobile: true}\n"
        "items:\n"
        "  - {id: item:tile, room: room:a, item: Moon Tile, at: [768, 200]}\n"
        "  - {id: item:sword, room: room:b, item: 1}\n"
        "  - {id: item:key, room: room:a, item: gate_key, at: [300, 100]}\n";
    const std::string card = std::string(CardText) + "items: {gate_key: 8}\n";
    const BuiltPlaced built = buildPlaced(PlacedRooms, objects, PlacedTables, card);
    INFO(issueText(built));
    REQUIRE(built.built);
    const std::vector<OpenYAMM::Game::MapDeltaActor> &actors = built.scene->initialState.actors;
    REQUIRE(actors.size() == 4);
    // objects.yml is read in the order of its file; the scene numbers the actors in that order.
    const OpenYAMM::Game::MapDeltaActor &guard = actors[0];
    CHECK(guard.monsterInfoId == 7);
    // The field the scene calls monster_id holds the kind's experience in the shipped MM6-MM8 records.
    CHECK(guard.monsterId == 200);
    CHECK(guard.hp == 1040);
    CHECK(guard.radius == 53);
    CHECK(guard.height == 176);
    CHECK(guard.moveSpeed == 220);
    CHECK(guard.x == 256);
    CHECK(guard.y == 256);
    CHECK(guard.z == 0);
    CHECK(guard.initialYawUnits == 512);
    CHECK(guard.group == 54);
    CHECK(guard.attributes == 0);
    CHECK(guard.sectorId == 1);
    CHECK(actors[1].initialYawUnits == 1280);
    // Hostile whatever the tables say: the Aggressor bit. In the second room, by its picture name.
    CHECK(actors[2].monsterInfoId == 2);
    CHECK(actors[2].attributes == 0x00080000u);
    CHECK(actors[2].sectorId == 2);
    CHECK(actors[2].x == 1184);
    // On the platform's top.
    CHECK(actors[3].z == 64);
    CHECK(actors[3].group == 0);
    CHECK(actors[3].immobile);
    CHECK_FALSE(guard.immobile);
    // The peaceful group: one event of the build's own on entering the map.
    CHECK(built.lua.find("evt.SetMonGroupBit(54, MonsterBits.Hostile, 0)") != std::string::npos);
    CHECK(built.lua.find("SetMapMetadata({onLoad = {1}") != std::string::npos);
    // Once per fill of the map (a refill clears the variable): a group an event made hostile since stays so over a
    // reload (D7's refused tolls).
    CHECK(built.lua.find("    if evt.GetMapVar(\"studio_peaceful_groups\", 0) ~= 0 then\n        return\n    end\n"
        "    evt.SetMapVar(\"studio_peaceful_groups\", 1)\n    evt.SetMonGroupBit(54") != std::string::npos);
    // Before the project's own load events, which may change a group.
    const BuiltPlaced withLoad = buildPlaced(PlacedRooms, objects, PlacedTables, card,
        "format: 0\nevents:\n  - {id: evt:angry, preset: script, trigger: load, lua: \"evt.SetMonGroupBit(54, "
        "MonsterBits.Hostile, 1)\"}\n");
    INFO(issueText(withLoad));
    REQUIRE(withLoad.built);
    CHECK(withLoad.lua.find("SetMapMetadata({onLoad = {2, 1}") != std::string::npos);

    const std::vector<OpenYAMM::Game::MapDeltaSpriteObject> &items = built.scene->initialState.spriteObjects;
    REQUIRE(items.size() == 3);
    // The moon tile: sprite index 6 is the third row of the object list (row 2 from 0; the header and the empty
    // line do not count).
    CHECK(items[0].objectDescriptionId == 2);
    CHECK(items[0].spriteId == 31);
    CHECK(items[0].x == 768);
    CHECK(items[0].y == 200);
    CHECK(items[0].z == 64);
    CHECK(items[0].sectorId == 1);
    REQUIRE(items[0].rawContainingItem.size() == 36);
    CHECK(items[0].rawContainingItem[0] == 5);
    CHECK(items[0].rawContainingItem[1] == 0);
    CHECK(items[1].objectDescriptionId == 1);
    CHECK(items[1].sectorId == 2);
    CHECK(items[1].rawContainingItem[0] == 1);
    // By a name of the project's card.
    CHECK(items[2].rawContainingItem[0] == 8);
    CHECK(items[2].objectDescriptionId == 3);

    // A project without monsters or items keeps the scene it had: both lists empty.
    const BuiltPlaced plain = buildPlaced(PlacedRooms, "format: 0\nstart: {room: room:a, at: [100, 100]}\n", {});
    REQUIRE(plain.built);
    CHECK(plain.scene->initialState.actors.empty());
    CHECK(plain.scene->initialState.spriteObjects.empty());
    CHECK(plain.lua.find("SetMapMetadata({onLoad = {}") != std::string::npos);

    const auto refused = [&objects, &card](const std::string &from, const std::string &to, bool tables = true)
    {
        std::string changed = objects;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltPlaced result = buildPlaced(
            PlacedRooms, changed, tables ? PlacedTables : std::vector<std::pair<std::string, std::string>>(), card);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    // A name two rows share lists them with the names that tell them apart; unknown names and numbers.
    CHECK(refused("monster: Swordsman,", "monster: Goblin,").find("1 (Goblin A), 2 (Goblin B)") != std::string::npos);
    CHECK(refused("monster: Swordsman,", "monster: Dragon,").find("no monster named 'Dragon'") != std::string::npos);
    CHECK(refused("monster: 7,", "monster: 70,").find("no monster number 70") != std::string::npos);
    // A monster without a descriptor row; one taller than its room; a peaceful one without a group; a group of
    // two minds.
    CHECK(refused("monster: 7,", "monster: Ghost,").find("monster_descriptors.txt has no row 9") != std::string::npos);
    CHECK(refused("monster: Goblin B,", "monster: Swordsman A,").find("176 high and the ceiling of room:b is 160")
        != std::string::npos);
    CHECK(refused("facing: n, group: 54, hostile: false", "facing: n, hostile: false")
        .find("`hostile: false` needs a `group`") != std::string::npos);
    CHECK(refused("facing: 225, group: 54, hostile: false", "facing: 225, group: 54, hostile: true")
        .find("a group is hostile or peaceful as a whole") != std::string::npos);
    // Items: a shared name, an item nothing draws on the ground, a place outside the room, no tables.
    CHECK(refused("item: Moon Tile,", "item: Key,").find("2 rows of items.txt are named 'Key': 6, 8")
        != std::string::npos);
    CHECK(refused("item: Moon Tile,", "item: Ghost Ring,").find("sprite index 77, which no row of object_list.txt")
        != std::string::npos);
    CHECK(refused("item: 1}", "item: 1, at: [5000, 0]}").find("is not inside room room:b") != std::string::npos);
    CHECK(refused("item: 1}", "item: 1}", false).find("pass --assets") != std::string::npos);
}

TEST_CASE("P4: a flyer, or a swimmer in water, starts `above_floor` over its floor")
{
    const std::string monsters = std::string(MonsterTableText)
        + "10\tOctopod\tOctopod A\t10\t40\t12\t200\t0\t1\tS\tShort\tNormal\t4\t220\t100\n";
    const std::string descriptors = std::string(MonsterDescriptorText) + "9\tGhost A\t100\t30\t200\n"
        + "10\tOctopod A\t100\t40\t200\n";
    const std::vector<std::pair<std::string, std::string>> tables = {
        {"monster_data.txt", monsters}, {"monster_descriptors.txt", descriptors}, {"items.txt", ItemTableText},
        {"object_list.txt", ObjectTableText}};
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [100, 100]}\n"
        "monsters:\n"
        "  - {id: monster:ghost, room: room:a, monster: Ghost, at: [600, 256], above_floor: 120}\n"
        "  - {id: monster:octopod, room: room:a, monster: Octopod, at: [256, 256], above_floor: 50}\n"
        "water:\n"
        "  - {id: water:pool, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], bottom: 0, top: 300}\n";
    const BuiltPlaced built = buildPlaced(PlacedRooms, objects, tables);
    INFO(issueText(built));
    REQUIRE(built.built);
    const std::vector<OpenYAMM::Game::MapDeltaActor> &actors = built.scene->initialState.actors;
    REQUIRE(actors.size() == 2);
    CHECK(actors[0].z == 120);
    CHECK(actors[1].z == 50);

    const auto refused = [&objects, &tables](const std::string &from, const std::string &to)
    {
        std::string changed = objects;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltPlaced result = buildPlaced(PlacedRooms, changed, tables);
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    // A swimmer out of the water, or with its middle over the surface; a walker; a flyer under the ceiling (384).
    CHECK(refused("at: [256, 256], above_floor: 50", "at: [900, 256], above_floor: 50").find("is in no water")
        != std::string::npos);
    CHECK(refused("at: [256, 256], above_floor: 50", "at: [256, 256], above_floor: 260").find("is in no water")
        != std::string::npos);
    CHECK(refused("monster: Ghost,", "monster: Swordsman,").find("neither flies nor swims") != std::string::npos);
    CHECK(refused("above_floor: 120", "above_floor: 300").find("100 high and the ceiling") != std::string::npos);
    refused("above_floor: 120", "above_floor: 0");
}

TEST_CASE("a click whose condition calls a world's quest hook says something when it fails (DD-06's trapdoor)")
{
    std::string rooms = PlacedRooms;
    const std::string platform = "      - {at: [768, 256], size: [128, 128], rise: 64}\n";
    REQUIRE(rooms.find(platform) != std::string::npos);
    rooms.replace(rooms.find(platform), platform.size(),
        "      - {id: platform:hatch, at: [768, 256], size: [128, 128], rise: 64}\n");
    const std::string objects = "format: 0\nstart: {room: room:a, at: [100, 100]}\n";
    const auto silent = [&rooms, &objects](const std::string &condition)
    {
        const BuiltPlaced built = buildPlaced(rooms, objects, PlacedTables, CardText,
            "format: 0\nevents:\n  - {id: evt:hatch, preset: script, source: platform:hatch, condition: " + condition
                + ", lua: \"evt.StatusText('Up')\"}\n");
        INFO(issueText(built));
        REQUIRE(built.built);
        return std::any_of(built.warnings.begin(), built.warnings.end(), [](const std::string &warning)
        {
            return warning.find("does nothing the player sees") != std::string::npos;
        });
    };
    CHECK(silent("{qbit: 5}"));
    CHECK_FALSE(silent("{all: [{lua: 'XeenQuests.hook(\"d7.roof_dd06\")'}, {qbit: 5}]}"));
}

TEST_CASE("a platform and a wall panel with an id are clicked, and a mover that does not move says so")
{
    // A podium on the floor, a block that hangs, and a sign on the north wall; a second platform stays a step
    // source.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 512\n"
        "    platforms:\n"
        "      - {id: platform:podium, at: [512, 512], size: [64, 64], rise: 112}\n"
        "      - {id: platform:cube, at: [256, 512], size: [128, 128], base: 192, rise: 64}\n"
        "      - {id: platform:step, at: [768, 256], size: [128, 128], rise: 16}\n"
        "    walls:\n"
        "      - wall: north\n"
        "        panels:\n"
        "          - {id: panel:sign, at: centre, length: 128, bottom: 64, height: 96, "
        "surface: {texture: sign, size: [128, 96]}}\n"
        "          - {offset: 64, length: 64, surface: {texture: strip, size: [64, 128]}}\n";
    const std::string objects = "format: 0\nstart: {room: room:a, at: [100, 100]}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:podium, preset: text, source: platform:podium, text: The book is destroyed}\n"
        "  - {id: evt:cube, preset: script, source: platform:cube,\n"
        "     lua: \"evt.MoveToMap(100, 100, 0, 0, 0, 0, 0, 0)\"}\n"
        "  - {id: evt:sign, preset: text, source: panel:sign, text: Keep out}\n"
        "  - {id: evt:step, preset: text, trigger: step, source: platform:step, text: A step}\n";
    const BuiltTriggers built = buildTriggers(rooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // Events are numbered as written: podium 1, cube 2, sign 3, step 4.
    std::map<int, std::vector<const OpenYAMM::Game::IndoorFace *>> byEvent;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        if (face.cogTriggered != 0)
        {
            byEvent[face.cogTriggered].push_back(&face);
            CHECK(face.roomNumber == 1);
        }
    }

    // The podium: four sides and its top; the hanging block also its underside; the sign one face of the wall.
    REQUIRE(byEvent[1].size() == 5);
    REQUIRE(byEvent[2].size() == 6);
    REQUIRE(byEvent[3].size() == 1);
    REQUIRE(byEvent[4].size() == 1);

    for (const int eventId : {1, 2, 3})
    {
        for (const OpenYAMM::Game::IndoorFace *pFace : byEvent[eventId])
        {
            CHECK((pFace->attributes & ClickFlag) == ClickFlag);
            CHECK((pFace->attributes & StepFlags) == 0);
        }
    }

    CHECK((byEvent[4].front()->attributes & (StepFlags | ClickFlag)) == StepFlags);
    CHECK(byEvent[3].front()->textureName == "sign");
    CHECK(built.rooms.heights(*byEvent[3].front()) == std::array<int, 2>{64, 160});
    CHECK(built.rooms.map.vertices[byEvent[3].front()->vertexIndices[0]].y == 1024);
    // The other panel of the wall stays part of it, and the podium is still stood on.
    size_t strips = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        strips += face.textureName == "strip" ? 1 : 0;
        CHECK((face.textureName != "strip" || face.cogTriggered == 0));
    }

    CHECK(strips >= 1);
    CHECK(built.rooms.levelsOver(1, 512.0, 512.0, true) == std::vector<int>{0, 112});
    // (A short line: the status bar, as the shipped maps show theirs.)
    CHECK(built.lua.find("RegisterEvent(1, nil, function()\n    evt.StatusText(\"The book is destroyed\")")
        != std::string::npos);

    const auto refused = [&rooms, &objects, &wiring](const std::string &from, const std::string &to,
                             const std::string &movers = "")
    {
        std::string changed = wiring;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltTriggers result = buildTriggers(rooms, objects + movers, changed);
        CHECK_FALSE(result.rooms.built);
        return issueText(result.rooms);
    };
    // A room's floor is not clicked; a chest preset needs a chest; a panel is not walked on.
    CHECK(refused("source: platform:podium", "source: room:a").find("a floor is walked on, not clicked")
        != std::string::npos);
    CHECK(refused("preset: text, source: platform:podium", "preset: chest, source: platform:podium")
        .find("a chest preset cannot have the platform") != std::string::npos);
    CHECK(refused("preset: text, source: panel:sign", "preset: text, trigger: step, source: panel:sign")
        .find("panel:sign is a wall panel, which is clicked") != std::string::npos);
    // The mover that nothing moves is told what to be.
    CHECK(refused("text: Keep out", "text: Keep out",
        "movers:\n  - {id: mover:podium, room: room:a, at: [800, 800], size: [64, 64], height: 112, "
        "travel: [0, 0, 0]}\n").find("write it in rooms.yml as a platform of its room") != std::string::npos);
}

TEST_CASE("the parts of a clicked platform (part_of) run its click and change with it")
{
    // A winch: a drum (clicked), an iron head standing on it and a bar through it (XD-02, 2026-11-24).
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 512\n"
        "    platforms:\n"
        "      - {id: platform:winch, at: [512, 512], size: [96, 96], rise: 80}\n"
        "      - {part_of: platform:winch, at: [512, 512], size: [48, 48], base: 80, rise: 28}\n"
        "    beams:\n"
        "      - {part_of: platform:winch, path: [[420, 512], [604, 512]], width: 12, depth: 12, bottom: 90}\n"
        "      - {part_of: platform:winch, path: [[512, 420], [512, 604]], width: 12, depth: 12, bottom: 96}\n";
    const std::string objects = "format: 0\nstart: {room: room:a, at: [100, 100]}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:winch, preset: text, source: platform:winch, title: Winch, text: The rope runs out}\n"
        "  - {id: evt:hide, preset: script, trigger: load, effects: [{hide: platform:winch}]}\n";
    const BuiltTriggers built = buildTriggers(rooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    size_t clicked = 0;
    std::set<int> cogs;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        if (face.cogTriggered == 1)
        {
            ++clicked;
            CHECK((face.attributes & ClickFlag) == ClickFlag);
            cogs.insert(face.cogNumber);
        }
    }

    // The drum's four sides and top, the head's four sides and top, each bar's six faces: all clicked, all
    // carrying the one face number the effect hides.
    CHECK(clicked >= 5 + 5 + 6 + 6 - 4);
    REQUIRE(cogs.size() == 1);
    CHECK(*cogs.begin() != 0);

    // A part names a platform that exists, and a platform with an id of its own is no part.
    const std::string head = "{part_of: platform:winch, at";
    std::string wrong = rooms;
    wrong.replace(wrong.find(head), head.size(), "{part_of: platform:drum, at");
    CHECK(issueText(buildTriggers(wrong, objects, wiring).rooms).find("platform:drum is none") != std::string::npos);
    std::string named = rooms;
    named.replace(named.find(head), 1, "{id: platform:head, ");
    CHECK(issueText(buildTriggers(named, objects, wiring).rooms).find("a platform with an `id` of its own is none")
        != std::string::npos);
}

namespace
{
// Whether the door record moves a vertex at this place.
bool doorMoves(const BuiltMoving &built, int doorId, int x, int y, int z)
{
    for (const YAML::Node &id : built.door(doorId)["vertex_ids"])
    {
        const OpenYAMM::Game::IndoorVertex &vertex = built.rooms.map.vertices[id.as<size_t>()];

        if (vertex.x == x && vertex.y == y && vertex.z == z)
        {
            return true;
        }
    }

    return false;
}

const char *const RiderRooms =
    "rooms:\n"
    "  - id: room:a\n"
    "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
    "    floor: 0\n"
    "    ceiling: 512\n"
    "    platforms:\n"
    "      - {id: platform:post, at: [200, 200], size: [32, 32], rise: 128}\n";

const char *const RiderObjects =
    "format: 0\n"
    "start: {room: room:a, at: [900, 100]}\n"
    "lifts:\n"
    "  - {id: lift:l, room: room:a, at: [200, 800], size: [160, 160], travel: 128}\n"
    "movers:\n"
    "  - id: mover:deck\n"
    "    room: room:a\n"
    "    at: [640, 640]\n"
    "    size: [256, 256]\n"
    "    height: 32\n"
    "    travel: [0, 0, 256]\n"
    "    parts:\n"
    "      - {at: [528, 528], size: [16, 16], height: 64}\n"
    "      - {outline: [[736, 736], [768, 736], [768, 768]], bottom: -32, height: 32}\n"
    "chests:\n"
    "  - {id: chest:on_deck, room: room:a, rides: mover:deck, at: [640, 640], size: [72, 48, 44]}\n"
    "  - {id: chest:on_lift, room: room:a, rides: lift:l, at: [200, 800], size: [72, 48, 44]}\n"
    "switches:\n"
    "  - {id: switch:deck, room: room:a, block: mover:deck, side: w, height: 16, size: [16, 16]}\n"
    "  - {id: switch:post, room: room:a, block: platform:post, side: s}\n";

const char *const RiderWiring =
    "format: 0\nevents:\n"
    "  - {id: evt:a_deck, preset: switch, source: switch:deck, toggles: [mover:deck]}\n"
    "  - {id: evt:b_post, preset: switch, source: switch:post, toggles: [lift:l]}\n"
    "  - {id: evt:c_chest, preset: chest, source: chest:on_deck}\n"
    "  - {id: evt:d_chest, preset: chest, source: chest:on_lift}\n";
}

TEST_CASE("a chest rides a lift or a mover, a switch sits on a post or a mover, and parts move with their mover")
{
    const BuiltMoving built = buildMoving(RiderRooms, RiderObjects, RiderWiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // Door 1 is the lift, door 2 the mover. The mover's record moves its own block, both parts (the post on its
    // top, the block hung beside its foot), the chest on its top and the switch plate on its west side.
    CHECK(doorMoves(built, 2, 512, 512, 0));
    CHECK(doorMoves(built, 2, 768, 768, 32));
    CHECK(doorMoves(built, 2, 520, 520, 96));
    CHECK(doorMoves(built, 2, 536, 536, 32));
    CHECK(doorMoves(built, 2, 736, 736, -32));
    CHECK(doorMoves(built, 2, 768, 768, 0));
    // The chest (72 wide along x, 48 deep, 44 high) stands on the deck's top at 32.
    CHECK(doorMoves(built, 2, 604, 616, 32));
    CHECK(doorMoves(built, 2, 676, 664, 76));
    // The switch plate: 2 in front of the west side, its middle 16 above the deck's foot.
    CHECK(doorMoves(built, 2, 510, 632, 8));
    CHECK(doorMoves(built, 2, 510, 648, 24));
    CHECK(built.door(2)["move_length"].as<int>() == 256);
    // The lift (its top 8 over the floor when down) carries its chest.
    CHECK(doorMoves(built, 1, 164, 776, 8));
    CHECK(doorMoves(built, 1, 236, 824, 52));
    CHECK_FALSE(doorMoves(built, 1, 604, 616, 32));
    // Each rider keeps its own event: the chests' faces open them, the plates run the switches.
    std::map<int, int> facesByEvent;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        facesByEvent[face.cogTriggered] += 1;
    }

    CHECK(facesByEvent[1] == 1);
    CHECK(facesByEvent[2] == 1);
    // A chest of MM6's plain kind (ch1): end, middle and end on both long sides and the top, one face each end.
    CHECK(facesByEvent[3] == 11);
    CHECK(facesByEvent[4] == 11);
    // The switch on the post: on its south side (y 184), 2 in front, its middle 96 above the post's foot.
    CHECK(built.rooms.hasVertex(184, 182, 80));
    CHECK(built.rooms.hasVertex(216, 182, 112));
    CHECK_FALSE(doorMoves(built, 2, 184, 182, 80));
    CHECK(built.lua.find("evt.OpenChest(0)") != std::string::npos);

    const auto refused = [](const std::string &from, const std::string &to)
    {
        std::string changed = RiderObjects;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltMoving result = buildMoving(RiderRooms, changed, RiderWiring);
        CHECK_FALSE(result.rooms.built);
        return issueText(result.rooms);
    };
    CHECK(refused("rides: mover:deck, at: [640, 640]", "rides: platform:post, at: [200, 200]")
        .find("a chest stands on a platform by its place alone") != std::string::npos);
    CHECK(refused("rides: mover:deck, at: [640, 640]", "rides: mover:deck, at: [760, 640]")
        .find("does not stand wholly on the top of mover:deck") != std::string::npos);
    CHECK(refused("rides: mover:deck, at: [640, 640]", "at: [640, 640], floor_height: 32")
        .find("give the chest `rides: mover:deck` in place of `floor_height`") != std::string::npos);
    CHECK(refused("travel: [0, 0, 256]", "travel: [0, 0, 460]")
        .find("riding mover:deck to its end the chest's top would be at 536") != std::string::npos);
    CHECK(refused("block: mover:deck, side: w", "block: lift:l, side: w").find("lift:l is a lift")
        != std::string::npos);
    CHECK(refused("block: platform:post, side: s", "block: platform:post").find("say which side of platform:post")
        != std::string::npos);
    CHECK(refused("block: platform:post, side: s", "block: platform:post, side: s, size: [64, 64]")
        .find("does not fit on that side of platform:post") != std::string::npos);
    CHECK(refused("block: platform:post, side: s", "block: platform:pillar, side: s").find("there is no block")
        != std::string::npos);
    CHECK(refused("{at: [528, 528], size: [16, 16], height: 64}", "{at: [528, 528], height: 64}")
        .find("a part is a block given by `at: [x, y]` and `size: [width, depth]`") != std::string::npos);
    CHECK(refused("bottom: -32, height: 32}", "bottom: 300, height: 400}").find("the part's top at its start is at 700")
        != std::string::npos);
}

TEST_CASE("parts of an uneven floor and ceiling take surfaces of their own, by steepness and by region")
{
    // A cave: a level floor at 0 inside a ring of lines, banks up to the rim at 256; the roof level at 768 inside the
    // same ring and down to 512 at the walls.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 256\n"
        "    ceiling: 512\n"
        "    steep_floor: true\n"
        "    floor_points: [[256, 256, 0], [768, 256, 0], [768, 768, 0], [256, 768, 0], [512, 512, 0]]\n"
        "    floor_lines: [[[256, 256], [768, 256], [768, 768], [256, 768], [256, 256]]]\n"
        "    floor_surfaces:\n"
        "      - {steeper_than: 0.5, surface: {texture: rock, size: [128, 128]}}\n"
        "    ceiling_points: [[256, 256, 768], [768, 256, 768], [768, 768, 768], [256, 768, 768]]\n"
        "    ceiling_lines: [[[256, 256], [768, 256], [768, 768], [256, 768], [256, 256]]]\n"
        "    ceiling_surfaces:\n"
        "      - {at: [512, 512], surface: {texture: crown, size: [128, 128]}}\n";
    const std::string objects = "format: 0\nstart: {room: room:a, at: [512, 400]}\n";
    const BuiltRooms built = buildRooms(rooms, objects);
    INFO(issueText(built));
    REQUIRE(built.built);
    // Every face of the floor that rises is rock, every level one the room's floor; the roof's flat crown has its
    // own surface and its leaning sides the room's ceiling.
    std::map<std::string, std::array<int, 2>> counts;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        const std::array<int, 2> range = built.heights(face);
        const bool level = range[0] == range[1];
        counts[face.textureName][level ? 0 : 1] += 1;

        if (face.textureName == "rock")
        {
            CHECK_FALSE(level);
            CHECK(range[0] >= 0);
            CHECK(range[1] <= 256);
        }

        if (face.textureName == "floor")
        {
            CHECK(level);
            CHECK(range[0] == 0);
        }

        if (face.textureName == "crown")
        {
            CHECK(level);
            CHECK(range[0] == 768);
        }

        if (face.textureName == "ceil")
        {
            CHECK_FALSE(level);
            CHECK(range[0] >= 512);
        }
    }

    CHECK(counts["rock"][1] >= 4);
    CHECK(counts["floor"][0] >= 1);
    CHECK(counts["crown"][0] >= 1);
    CHECK(counts["ceil"][1] >= 4);

    const auto changed = [&rooms, &objects](const std::string &from, const std::string &to)
    {
        std::string text = rooms;
        REQUIRE(text.find(from) != std::string::npos);
        text.replace(text.find(from), from.size(), to);
        return buildRooms(text, objects);
    };
    // A region wins over steepness: the level floor round the point as flagstones, the banks still rock.
    const BuiltRooms flagged = changed(
        "      - {steeper_than: 0.5, surface: {texture: rock, size: [128, 128]}}\n",
        "      - {steeper_than: 0.5, surface: {texture: rock, size: [128, 128]}}\n"
        "      - {at: [400, 400], surface: {texture: flags, size: [128, 128]}}\n");
    INFO(issueText(flagged));
    REQUIRE(flagged.built);
    size_t flags = 0;
    size_t rock = 0;

    for (const OpenYAMM::Game::IndoorFace &face : flagged.map.faces)
    {
        flags += face.textureName == "flags" ? 1 : 0;
        rock += face.textureName == "rock" ? 1 : 0;
        CHECK(face.textureName != "floor");
    }

    CHECK(flags >= 1);
    CHECK(rock == static_cast<size_t>(counts["rock"][1]));
    // Refused: a region nothing closes off, an entry of two minds, and parts of a floor that is level.
    CHECK(issueText(changed("    ceiling_lines: [[[256, 256], [768, 256], [768, 768], [256, 768], [256, 256]]]\n", ""))
        .find("the region round [512, 512] is the whole ceiling of room:a") != std::string::npos);
    CHECK(issueText(changed("{steeper_than: 0.5, surface:", "{steeper_than: 0.5, at: [300, 300], surface:"))
        .find("says which part it means in one way") != std::string::npos);
    CHECK(issueText(changed(
        "    floor_points: [[256, 256, 0], [768, 256, 0], [768, 768, 0], [256, 768, 0], [512, 512, 0]]\n"
        "    floor_lines: [[[256, 256], [768, 256], [768, 768], [256, 768], [256, 256]]]\n", ""))
        .find("this room's floor is level") != std::string::npos);
}

TEST_CASE("a mouth follows uneven floors and roofs along its wall, and a window stands over an uneven floor")
{
    // Two caves cut across their bank and the lean of their roof (the floor level at 0 north of y 384 and up to 360
    // at the south wall; the roof level at 1170 north of y 768 and down to 376 at the south wall), joined over
    // their whole section.
    const auto caves = [](const std::string &opening, const std::string &gap = "1024")
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    floor_points: [[0, 0, 360], [1024, 0, 360], [1024, 384, 0], [0, 384, 0]]\n"
            "    floor_lines: [[[0, 384], [1024, 384]]]\n"
            "    steep_floor: true\n"
            "    ceiling: 1170\n"
            "    ceiling_points: [[0, 0, 376], [1024, 0, 376], [0, 768, 1170], [1024, 768, 1170]]\n"
            "    ceiling_lines: [[[0, 768], [1024, 768]]]\n"
            "  - id: room:b\n"
            "    outline: [[" + gap + ", 0], [2048, 0], [2048, 1024], [" + gap + ", 1024]]\n"
            "    floor: 0\n"
            "    floor_points: [[" + gap + ", 0, 360], [2048, 0, 360], [2048, 384, 0], [" + gap + ", 384, 0]]\n"
            "    floor_lines: [[[" + gap + ", 384], [2048, 384]]]\n"
            "    steep_floor: true\n"
            "    ceiling: 1170\n"
            "    ceiling_points: [[" + gap + ", 0, 376], [2048, 0, 376], [" + gap + ", 768, 1170], [2048, 768, 1170]]\n"
            "    ceiling_lines: [[[" + gap + ", 768], [2048, 768]]]\n"
            "openings:\n"
            "  - {id: open:mouth, from: room:a, to: room:b, " + opening + "}\n";
    };
    const std::string objects = "format: 0\nstart: {room: room:a, at: [512, 700]}\n";
    const BuiltRooms built = buildRooms(caves("width: full, height: full"), objects);
    INFO(issueText(built));
    REQUIRE(built.built);
    // Three strips between the places where floor and roof bend (y 384 and 768): three doorways of one mouth, and
    // nothing of either room's wall left between the caves.
    std::vector<const OpenYAMM::Game::IndoorFace *> portals;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.isPortal)
        {
            portals.push_back(&face);
        }
        else
        {
            bool onJoint = true;

            for (const uint16_t vertex : face.vertexIndices)
            {
                onJoint = onJoint && built.map.vertices[vertex].x == 1024;
            }

            CHECK_FALSE(onJoint);
        }
    }

    REQUIRE(portals.size() == 3);
    std::vector<std::array<int, 2>> heights;

    for (const OpenYAMM::Game::IndoorFace *pPortal : portals)
    {
        heights.push_back(built.heights(*pPortal));
        CHECK(pPortal->vertexIndices.size() == 4);
    }

    std::sort(heights.begin(), heights.end());
    // Over the bank from 360 up to the roof at 773 there; the middle from the level floor to where the roof ends
    // its lean; the north part floor to roof.
    CHECK(heights == std::vector<std::array<int, 2>>{{0, 773}, {0, 1170}, {0, 1170}});
    CHECK(built.hasVertex(1024, 0, 360));
    CHECK(built.hasVertex(1024, 0, 376));
    CHECK(built.hasVertex(1024, 384, 773));

    // Through a wall 32 thick the way keeps the section: a sloping sill and a sloping soffit, and no reveal
    // between the strips.
    const BuiltRooms thick = buildRooms(caves("width: full, height: full", "1056"), objects);
    INFO(issueText(thick));
    REQUIRE(thick.built);
    size_t inWall = 0;

    for (const OpenYAMM::Game::IndoorFace &face : thick.map.faces)
    {
        bool between = !face.isPortal;
        bool upright = true;

        for (const uint16_t vertex : face.vertexIndices)
        {
            between = between && thick.map.vertices[vertex].x >= 1024 && thick.map.vertices[vertex].x <= 1056;
            upright = upright && thick.map.vertices[vertex].y == thick.map.vertices[face.vertexIndices[0]].y;
        }

        if (between)
        {
            ++inWall;
            // No face of the way through stands across it at y 384 or 768, where two strips meet.
            const int y = thick.map.vertices[face.vertexIndices[0]].y;
            CHECK_FALSE((upright && (y == 384 || y == 768)));
        }
    }

    // A sill and a soffit for each of the three strips, and the two ends at y 0 and 1024.
    CHECK(inWall == 8);

    // A doorway 256 wide and 300 high across the foot of the bank: its sill rakes from 120 down to the level floor,
    // its top is level 300 above the sill's lowest point.
    const BuiltRooms door = buildRooms(caves("width: 256, height: 300, along: 0.375"), objects);
    INFO(issueText(door));
    REQUIRE(door.built);
    CHECK(door.hasVertex(1024, 256, 120));
    CHECK(door.hasVertex(1024, 384, 0));
    CHECK(door.hasVertex(1024, 512, 0));
    CHECK(door.hasVertex(1024, 256, 300));
    CHECK(door.hasVertex(1024, 512, 300));

    // What such a mouth cannot take.
    CHECK(issueText(buildRooms(caves("width: full, height: full, shape: arch, apex: 1200"), objects))
        .find("Such a mouth takes no `shape`") != std::string::npos);
    CHECK(issueText(buildRooms(caves("width: 256, height: 900, along: 0.125"), objects))
        .find("write `height: full` and it follows the roof") != std::string::npos);

    // A window high over an uneven floor stands on the level floor of the room it looks from: a rectangle.
    const BuiltRooms window = buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    floor_points: [[0, 1024, 100], [512, 1024, 0], [1024, 1024, 0]]\n"
        "    ceiling: 1200\n"
        "  - {id: room:b, outline: [[0, 1072], [1024, 1072], [1024, 1600], [0, 1600]], floor: 700, ceiling: 1300}\n"
        "openings:\n"
        "  - {id: open:window, from: room:b, to: room:a, width: 512, height: 300, sill: 60}\n",
        "format: 0\nstart: {room: room:b}\n");
    INFO(issueText(window));
    REQUIRE(window.built);
    size_t windows = 0;

    for (const OpenYAMM::Game::IndoorFace &face : window.map.faces)
    {
        if (face.isPortal)
        {
            ++windows;
            CHECK(window.heights(face) == std::array<int, 2>{760, 1060});
        }
    }

    CHECK(windows == 1);
}

TEST_CASE("a slab under a sloping top hangs between two landings, and an underside takes its own surface")
{
    // A landing at 128 in the south, one at 256 in the north, and between them a ramp 16 thick that hangs free.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [512, 0], [512, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 640\n"
        "    platforms:\n"
        "      - {at: [256, 128], size: [256, 256], rise: 128}\n"
        "      - {at: [256, 896], size: [256, 256], base: 224, rise: 32,\n"
        "         bottom_surface: {texture: under, size: [64, 64]}}\n"
        "      - {at: [256, 512], size: [128, 512], rise: 128, top_slope: {to: 256, toward: north}, thickness: 16,\n"
        "         top_surface: {texture: tread, size: [64, 64]}, bottom_surface: {texture: soffit, size: [64, 64]}}\n";
    const BuiltRooms built = buildRooms(rooms, "format: 0\nstart: {room: room:a, at: [256, 128]}\n");
    INFO(issueText(built));
    REQUIRE(built.built);
    // The ramp's top runs from 128 at y 256 to 256 at y 768, and its underside 16 under it at both ends.
    CHECK(built.hasVertex(192, 256, 128));
    CHECK(built.hasVertex(320, 768, 256));
    CHECK(built.hasVertex(192, 256, 112));
    CHECK(built.hasVertex(320, 768, 240));
    // No corner of it stands on the floor: the wedge down to a level foot is gone.
    CHECK_FALSE(built.hasVertex(192, 768, 0));
    CHECK_FALSE(built.hasVertex(192, 768, 128));
    size_t soffits = 0;
    size_t unders = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.textureName == "soffit")
        {
            ++soffits;
            CHECK(built.heights(face) == std::array<int, 2>{112, 240});
            CHECK((face.facetType == 5 || face.facetType == 6));
        }

        if (face.textureName == "under")
        {
            ++unders;
            CHECK(built.heights(face) == std::array<int, 2>{224, 224});
        }
    }

    CHECK(soffits == 1);
    CHECK(unders == 1);
    // Over the ramp's middle two floors lie one above the other: the room's own, and the slope (its face reaches
    // up to 256).
    CHECK(built.levelsOver(1, 256.0, 512.0, true) == std::vector<int>{0, 256});

    const auto refused = [&rooms](const std::string &from, const std::string &to)
    {
        std::string changed = rooms;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltRooms result = buildRooms(changed, "format: 0\nstart: {room: room:a, at: [256, 128]}\n");
        CHECK_FALSE(result.built);
        return issueText(result);
    };
    CHECK(refused("thickness: 16", "thickness: 200").find("the slab's underside would lie under the floor")
        != std::string::npos);
    CHECK(refused("base: 224, rise: 32,", "base: 224, rise: 32, thickness: 8,")
        .find("`thickness` makes a slab of a block whose top slopes") != std::string::npos);
}

TEST_CASE("a warning about a changed rule is answered once in project.yml")
{
    // A platform with a base in a sunken level, and a ceiling level that narrows: both met a rule that changed on
    // 2026-11-12, and the build says so on every build until the project names the change as taken note of.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 512\n"
        "    levels:\n"
        "      - {outline: [[256, 256], [768, 256], [768, 768], [256, 768]], floor: -128}\n"
        "    ceiling_levels:\n"
        "      - {ceiling: 768, top_outline: [[0, 384], [1024, 384], [1024, 640], [0, 640]]}\n"
        "    platforms:\n"
        "      - {at: [512, 512], size: [64, 64], base: 32, rise: 32}\n";
    const std::string objects = "format: 0\nstart: {room: room:a, at: [100, 100]}\n";
    const auto warned = [](const BuiltPlaced &built, const std::string &fragment)
    {
        return std::any_of(built.warnings.begin(), built.warnings.end(), [&fragment](const std::string &warning)
        {
            return warning.find(fragment) != std::string::npos;
        });
    };
    const BuiltPlaced plain = buildPlaced(rooms, objects, {});
    INFO(issueText(plain));
    REQUIRE(plain.built);
    CHECK(warned(plain, "stands in a sunken level: it is now measured from that level's floor"));
    CHECK(warned(plain, "add `platform_in_sunken_level` to project.yml `migrated`"));
    CHECK(warned(plain, "take the room's wall surface, not the ceiling's"));

    const BuiltPlaced one = buildPlaced(
        rooms, objects, {}, std::string(CardText) + "migrated: [platform_in_sunken_level]\n");
    INFO(issueText(one));
    REQUIRE(one.built);
    CHECK_FALSE(warned(one, "stands in a sunken level"));
    CHECK(warned(one, "take the room's wall surface, not the ceiling's"));

    const BuiltPlaced both = buildPlaced(
        rooms, objects, {}, std::string(CardText) + "migrated: [platform_in_sunken_level, ceiling_level_sides]\n");
    REQUIRE(both.built);
    CHECK_FALSE(warned(both, "stands in a sunken level"));
    CHECK_FALSE(warned(both, "take the room's wall surface"));
    // Taking note changes nothing of what is built.
    CHECK(both.map.vertices.size() == plain.map.vertices.size());
    CHECK(both.map.faces.size() == plain.map.faces.size());

    // A name the build does not know is refused by the schema.
    const BuiltPlaced unknown = buildPlaced(rooms, objects, {}, std::string(CardText) + "migrated: [everything]\n");
    CHECK_FALSE(unknown.built);
}

TEST_CASE("a mover may pass into the ceiling or a wall at one end, names the floor it stands on, and keeps a half unit")
{
    // A gate in two halves: the upper rises into the ceiling, the lower sinks; a button is pushed 8 into the north
    // wall; a block under a hanging platform measures from the room's floor; a block 205 by 25 round a half unit.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 512], [0, 512]]\n"
        "    floor: 0\n"
        "    ceiling: 256\n"
        "    platforms:\n"
        "      - {at: [800, 256], size: [128, 128], base: 200, rise: 26}\n"
        "  - {id: room:b, outline: [[0, 544], [1024, 544], [1024, 800], [0, 800]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192, along: 0.9}\n";
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a, at: [100, 100]}\n"
        "movers:\n"
        "  - {id: mover:a_high, room: room:a, at: [256, 448], size: [512, 64], bottom: 128, height: 128,\n"
        "     travel: [0, 0, 128]}\n"
        "  - {id: mover:b_low, room: room:a, at: [256, 448], size: [512, 64], height: 128, travel: [0, 0, -130]}\n"
        "  - {id: mover:c_button, room: room:a, at: [600, 507], size: [32, 10], bottom: 112, height: 32,\n"
        "     travel: [0, 8, 0]}\n"
        "  - {id: mover:d_under, room: room:a, at: [800, 256], size: [64, 64], bottom: 100, height: 50,\n"
        "     travel: [0, 0, 10], floor_height: 0}\n"
        "  - {id: mover:e_half, room: room:a, at: [512.5, 100.5], size: [205, 25], height: 64, travel: [0, 0, 16]}\n";
    const BuiltMoving built = buildMoving(rooms, objects);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // The upper half rises 128 from 128..256 to 256..384, through the ceiling at 256.
    CHECK(built.direction(1) == std::array<int, 3>{0, 0, -65536});
    CHECK(built.door(1)["move_length"].as<int>() == 128);
    CHECK(doorMoves(built, 1, 0, 416, 256));
    // The button's back stands in the wall's plane (y 512) and ends 8 inside the wall.
    CHECK(built.direction(3) == std::array<int, 3>{0, -65536, 0});
    CHECK(doorMoves(built, 3, 584, 512, 112));
    CHECK(doorMoves(built, 3, 616, 502, 144));
    // Under the hanging platform, from the room's floor: 100 to 150.
    CHECK(doorMoves(built, 4, 768, 224, 100));
    CHECK(doorMoves(built, 4, 832, 288, 150));
    // Round the half unit: 410 to 615 and 88 to 113, as a platform with the same `at` and `size` stands.
    CHECK(doorMoves(built, 5, 410, 88, 0));
    CHECK(doorMoves(built, 5, 615, 113, 64));

    const auto changed = [&rooms, &objects](const std::string &from, const std::string &to)
    {
        std::string text = objects;
        REQUIRE(text.find(from) != std::string::npos);
        text.replace(text.find(from), from.size(), to);
        return buildMoving(rooms, text);
    };
    // Without `floor_height` the highest floor at the block's middle is meant, the hanging platform's top (226): the
    // block would stand from 326, through the ceiling at both ends, and the refusal names the floor.
    const BuiltMoving unnamed = changed(", floor_height: 0", "");
    CHECK_FALSE(unnamed.rooms.built);
    CHECK(issueText(unnamed.rooms).find("name the floor that is meant with `floor_height` (the room's own is at 0)")
        != std::string::npos);
    CHECK(issueText(changed("floor_height: 0", "floor_height: 64").rooms)
        .find("there is no floor at 64 at the mover's middle") != std::string::npos);
    // Pushed through the wall into the room behind it; and in the room at neither end.
    CHECK(issueText(changed("travel: [0, 8, 0]", "travel: [0, 60, 0]").rooms)
        .find("the mover at its end (after `travel`) would stand in room:b") != std::string::npos);
    CHECK(issueText(changed("bottom: 128, height: 128,\n     travel: [0, 0, 128]",
        "bottom: 200, height: 128,\n     travel: [0, 0, 128]").rooms).find("here it does so at neither")
        != std::string::npos);
}

TEST_CASE("an arch as high as a vault's end, an opening cut to its wall, a shaped mouth on uneven ground, a flight "
          "into a doorway and a tunnel with a pointed crown")
{
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\n";
    // A vaulted passage (the walls to 256, a leaning side 64 in to 320, a ridge at 352) that ends in a hall.
    const auto vault = [](const std::string &opening)
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [256, 0], [256, 448], [0, 448]]\n"
            "    floor: 0\n"
            "    ceiling: 256\n"
            "    ceiling_levels:\n"
            "      - ceiling: 320\n"
            "        top_outline: [[64, 0], [192, 0], [192, 448], [64, 448]]\n"
            "      - outline: [[64, 0], [192, 0], [192, 448], [64, 448]]\n"
            "        ceiling: 352\n"
            "        top_scale: [0, 1]\n"
            "  - {id: room:b, outline: [[-256, 480], [512, 480], [512, 1024], [-256, 1024]], floor: 0, ceiling: 512}\n"
            "openings:\n"
            "  - {id: open:mouth, from: room:a, to: room:b, " + opening + "}\n";
    };
    // Nothing of the vault's end is left over a mouth that is its whole profile.
    const auto endLeft = [](const BuiltRooms &built)
    {
        size_t left = 0;

        for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
        {
            bool inEnd = !face.isPortal;

            for (const uint16_t vertex : face.vertexIndices)
            {
                inEnd = inEnd && built.map.vertices[vertex].y == 448 && built.map.vertices[vertex].z >= 256;
            }

            left += inEnd ? 1 : 0;
        }

        return left;
    };
    const auto portalCount = [](const BuiltRooms &built)
    {
        return std::count_if(built.map.faces.begin(), built.map.faces.end(), [](const OpenYAMM::Game::IndoorFace &face)
        {
            return face.isPortal;
        });
    };

    // The arch's shoulder is written as a rounded share (0.667 of 96 is 64.03): it stands on whole units, on the
    // vault's own line, and the arch is the vault's whole profile.
    const BuiltRooms arch =
        buildRooms(vault("width: full, height: 256, shape: arch, apex: 352, shoulders: [[0.25, 0.667]]"), objects);
    INFO(issueText(arch));
    REQUIRE(arch.built);
    CHECK(portalCount(arch) == 1);
    CHECK(arch.hasVertex(64, 480, 320));
    CHECK(arch.hasVertex(128, 480, 352));
    CHECK(endLeft(arch) == 0);

    // The same mouth said without its shape: everything under the wall's own line.
    const BuiltRooms whole = buildRooms(vault("width: full, height: full, trim_to_wall: true"), objects);
    INFO(issueText(whole));
    REQUIRE(whole.built);
    CHECK(portalCount(whole) == 4);
    CHECK(whole.hasVertex(64, 480, 320));
    CHECK(whole.hasVertex(128, 480, 352));
    CHECK(endLeft(whole) == 0);
    // A rectangle 128 wide to 340 loses its two upper corners along the ridge's two sides.
    const BuiltRooms cut = buildRooms(vault("width: 192, height: 340, trim_to_wall: true"), objects);
    INFO(issueText(cut));
    REQUIRE(cut.built);
    CHECK(cut.hasVertex(32, 480, 288));
    CHECK(cut.hasVertex(104, 480, 340));
    CHECK(cut.hasVertex(152, 480, 340));
    CHECK(cut.hasVertex(224, 480, 288));
    CHECK(issueText(buildRooms(vault("width: 192, height: 340"), objects)).find("`trim_to_wall: true`")
        != std::string::npos);

    // A hipped ceiling: the west side upright, the north side leaning 128 in. A doorway in the west wall that
    // reaches the north corner is refused, and with `trim_to_wall` loses the corner under the lean.
    const auto hip = [](const std::string &opening)
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [640, 0], [640, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    ceiling: 256\n"
            "    ceiling_levels:\n"
            "      - ceiling: 384\n"
            "        top_outline: [[0, 0], [512, 0], [512, 896], [0, 896]]\n"
            "  - {id: room:b, outline: [[-600, 384], [-32, 384], [-32, 1024], [-600, 1024]], floor: 0, ceiling: 384}\n"
            "openings:\n"
            "  - {id: open:mouth, from: room:a, to: room:b, " + opening + "}\n";
    };
    CHECK(issueText(buildRooms(hip("width: full, height: 384"), objects)).find("`trim_to_wall: true`")
        != std::string::npos);
    const BuiltRooms hipped = buildRooms(hip("width: full, height: 384, trim_to_wall: true"), objects);
    INFO(issueText(hipped));
    REQUIRE(hipped.built);
    CHECK(portalCount(hipped) == 2);
    CHECK(hipped.hasVertex(-32, 896, 384));
    CHECK(hipped.hasVertex(-32, 1024, 256));
    // The corner that the opening lost is wall in the room behind: one triangle between the cut and that room's
    // ceiling.
    size_t cornerFaces = 0;

    for (const OpenYAMM::Game::IndoorFace &face : hipped.map.faces)
    {
        bool inCorner = !face.isPortal;

        for (const uint16_t vertex : face.vertexIndices)
        {
            inCorner = inCorner && hipped.map.vertices[vertex].x == -32 && hipped.map.vertices[vertex].y >= 896
                && hipped.map.vertices[vertex].z >= 256;
        }

        cornerFaces += inCorner ? 1 : 0;
    }

    CHECK(cornerFaces == 1);

    // An arch across the foot of a bank (the floor level at 0 north of y 384 and up to 360 at the south wall): it
    // stands on the raking sill, its sides ending 300 and its point 400 above the sill's lowest point.
    const auto caves = [](const std::string &opening, const std::string &surfaces = "")
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    floor_points: [[0, 0, 360], [1024, 0, 360], [1024, 384, 0], [0, 384, 0]]\n"
            "    floor_lines: [[[0, 384], [1024, 384]]]\n"
            "    steep_floor: true\n" + surfaces +
            "    ceiling: 1170\n"
            "  - id: room:b\n"
            "    outline: [[1056, 0], [2048, 0], [2048, 1024], [1056, 1024]]\n"
            "    floor: 0\n"
            "    floor_points: [[1056, 0, 360], [2048, 0, 360], [2048, 384, 0], [1056, 384, 0]]\n"
            "    floor_lines: [[[1056, 384], [2048, 384]]]\n"
            "    steep_floor: true\n"
            "    ceiling: 1170\n"
            "openings:\n"
            "  - {id: open:mouth, from: room:a, to: room:b, " + opening + "}\n";
    };
    const std::string caveObjects = "format: 0\nstart: {room: room:a, at: [512, 700]}\n";
    const BuiltRooms banked =
        buildRooms(caves("width: 512, height: 300, shape: arch, apex: 400, along: 0.375"), caveObjects);
    INFO(issueText(banked));
    REQUIRE(banked.built);
    CHECK(portalCount(banked) == 4);
    CHECK(banked.hasVertex(1056, 128, 240));
    CHECK(banked.hasVertex(1056, 128, 300));
    CHECK(banked.hasVertex(1056, 256, 120));
    CHECK(banked.hasVertex(1056, 256, 367));
    CHECK(banked.hasVertex(1056, 384, 400));
    CHECK(banked.hasVertex(1056, 640, 300));
    // A shape with `height: full` is still refused, and says what to write.
    CHECK(issueText(buildRooms(caves("width: full, height: full, shape: arch, apex: 1200"), caveObjects))
        .find("or give the shape a `height`") != std::string::npos);

    // Through the wall's thickness the sill is the floor running on: the bank's rock over the bank, the room's floor
    // over the level part.
    const BuiltRooms rocky = buildRooms(
        caves("width: full, height: full",
            "    floor_surfaces:\n      - {steeper_than: 0.5, surface: {texture: rock, size: [128, 128]}}\n"),
        caveObjects);
    INFO(issueText(rocky));
    REQUIRE(rocky.built);
    size_t rockSills = 0;
    size_t floorSills = 0;

    for (const OpenYAMM::Game::IndoorFace &face : rocky.map.faces)
    {
        bool between = !face.isPortal;
        bool low = true;

        for (const uint16_t vertex : face.vertexIndices)
        {
            between = between && rocky.map.vertices[vertex].x >= 1024 && rocky.map.vertices[vertex].x <= 1056;
            low = low && rocky.map.vertices[vertex].z <= 360;
        }

        if (between && low && face.vertexIndices.size() == 4 && rocky.heights(face)[1] > rocky.heights(face)[0])
        {
            rockSills += face.textureName == "rock" ? 1 : 0;
            CHECK(face.textureName == "rock");
        }
        else if (between && low && rocky.heights(face)[1] == 0)
        {
            floorSills += face.textureName == "floor" ? 1 : 0;
        }
    }

    CHECK(rockSills == 1);
    CHECK(floorSills == 1);

    // An arch that is the profile of a vault given by points (240 at the springing, 315 at the crown).
    const BuiltRooms pointed = buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 384], [0, 384]]\n"
        "    floor: 0\n"
        "    ceiling: 240\n"
        "    ceiling_points: [[0, 96, 294], [0, 192, 315], [0, 288, 294], [1024, 96, 294], [1024, 192, 315],\n"
        "      [1024, 288, 294]]\n"
        "    ceiling_lines: [[[0, 96], [1024, 96]], [[0, 192], [1024, 192]], [[0, 288], [1024, 288]]]\n"
        "  - {id: room:b, outline: [[1072, -200], [1600, -200], [1600, 584], [1072, 584]], floor: 0, ceiling: 600}\n"
        "openings:\n"
        "  - {id: open:mouth, from: room:a, to: room:b, width: full, height: 240, shape: arch, apex: 315,\n"
        "     shoulders: [[0.25, 0.72]]}\n",
        objects);
    INFO(issueText(pointed));
    REQUIRE(pointed.built);
    CHECK(portalCount(pointed) == 4);
    CHECK(pointed.hasVertex(1072, 96, 294));
    CHECK(pointed.hasVertex(1072, 192, 315));
    // One unit higher it leaves the vault, and the refusal names the place.
    CHECK(issueText(buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 384], [0, 384]]\n"
        "    floor: 0\n"
        "    ceiling: 240\n"
        "    ceiling_points: [[0, 192, 315], [1024, 192, 315]]\n"
        "    ceiling_lines: [[[0, 192], [1024, 192]]]\n"
        "  - {id: room:b, outline: [[1072, -200], [1600, -200], [1600, 584], [1072, 584]], floor: 0, ceiling: 600}\n"
        "openings:\n"
        "  - {id: open:mouth, from: room:a, to: room:b, width: full, height: 240, shape: gable, apex: 316}\n",
        objects)).find("the gable reaches 316 at [1024, 192]") != std::string::npos);

    // A flight from a nave at -544 into the doorway of an apse at -416: four risers, three treads in the nave, the
    // last riser in the wall under the sill.
    const auto nave = [](const std::string &apseFloor)
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [768, 0], [768, 320], [0, 320]]\n"
            "    floor: -544\n"
            "    ceiling: 96\n"
            "    flights:\n"
            "      - {from: [640, 160], to: [0, 160], to_height: -416, width: 256, steps: 4}\n"
            "  - {id: room:b, outline: [[-512, 0], [0, 0], [0, 320], [-512, 320]], floor: " + apseFloor
            + ", ceiling: 96}\n"
            "openings:\n"
            "  - {id: open:mouth, from: room:a, to: room:b, width: full, height: full}\n";
    };
    const std::string naveObjects = "format: 0\nstart: {room: room:a, at: [700, 160]}\n";
    const BuiltRooms flight = buildRooms(nave("-416"), naveObjects);
    INFO(issueText(flight));
    REQUIRE(flight.built);
    // The top tread, at -448, ends on the wall; no tread stands at the sill's height.
    CHECK(flight.hasVertex(0, 32, -448));
    CHECK(flight.hasVertex(0, 288, -448));
    CHECK(flight.hasVertex(427, 32, -512));
    CHECK_FALSE(flight.hasVertex(160, 32, -416));
    CHECK(issueText(buildRooms(nave("-400"), naveObjects)).find("that is a flight into a doorway")
        != std::string::npos);

    // A tunnel whose section has one highest point, 9 over its neighbours: a vault's crown.
    const BuiltRooms crown = buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    path: [[0, 0], [2048, 0]]\n"
        "    floor: 0\n"
        "    ceiling: 324\n"
        "    section:\n"
        "      outline: [[-192, 0], [192, 0], [192, 126], [144, 216], [96, 285], [48, 315], [0, 324], [-48, 315],\n"
        "        [-96, 285], [-144, 216], [-192, 126]]\n",
        "format: 0\nstart: {room: room:a, at: [128, 0]}\n");
    INFO(issueText(crown));
    REQUIRE(crown.built);
    CHECK(crown.hasVertex(0, 0, 324));
    CHECK(crown.hasVertex(2048, 48, 315));
}

TEST_CASE("a platform or a raised level is drawn and not solid, or solid and not drawn, and the walk knows it")
{
    // A pit 256 deep between two rooms. Over it, at the two rooms' floor height, a slab on each half: `first` the
    // southern, `second` the northern.
    const auto pit = [](const std::string &first, const std::string &second)
    {
        return
            "rooms:\n"
            "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
            "  - id: room:b\n"
            "    outline: [[528, 0], [1552, 0], [1552, 512], [528, 512]]\n"
            "    floor: -256\n"
            "    ceiling: 384\n"
            "    platforms:\n"
            "      - {at: [1040, 128], size: [1024, 256], base: 240, rise: 16" + first + "}\n"
            "      - {at: [1040, 384], size: [1024, 256], base: 240, rise: 16" + second + "}\n"
            "  - {id: room:c, outline: [[1568, 0], [2080, 0], [2080, 512], [1568, 512]], floor: 0, ceiling: 384}\n"
            "openings:\n"
            "  - {id: open:ab, from: room:a, to: room:b, width: 448, height: 256}\n"
            "  - {id: open:bc, from: room:b, to: room:c, width: 448, height: 256}\n";
    };
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 256]}\n";
    const uint32_t invisible = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible);
    const uint32_t untouchable = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Untouchable);
    // The faces of the two slabs (between -16 and 0 inside the pit's plan) and the flags they carry.
    const auto slabFlags = [invisible, untouchable](const BuiltRooms &built, bool southern)
    {
        std::set<uint32_t> flags;

        for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
        {
            bool inSlab = !face.isPortal;
            // (The two slabs' sides at y 256 lie in one plane: a face belongs to the slab it has a point off it in.)
            bool offMiddle = false;

            for (const uint16_t vertex : face.vertexIndices)
            {
                const OpenYAMM::Game::IndoorVertex &point = built.map.vertices[vertex];
                inSlab = inSlab && point.z >= -16 && point.z <= 0 && point.x >= 528 && point.x <= 1552
                    && (southern ? point.y <= 256 : point.y >= 256);
                offMiddle = offMiddle || point.y != 256;
            }

            if (inSlab && offMiddle)
            {
                flags.insert(face.attributes & (invisible | untouchable));
            }
        }

        return flags;
    };

    // A false floor on the south half, an unseen floor on the north half: the walk crosses on the unseen one.
    const BuiltMoving mixed = buildMoving(pit(", solid: false", ", visible: false"), objects);
    INFO(issueText(mixed.rooms));
    REQUIRE(mixed.rooms.built);
    CHECK(slabFlags(mixed.rooms, true) == std::set<uint32_t>{untouchable});
    CHECK(slabFlags(mixed.rooms, false) == std::set<uint32_t>{invisible});
    CHECK(solveMap(mixed.loaded, "[]").neverReached.empty());

    // Both false: the party falls into the pit and never reaches the far room.
    const BuiltMoving bothFalse = buildMoving(pit(", solid: false", ", solid: false"), objects);
    INFO(issueText(bothFalse.rooms));
    REQUIRE(bothFalse.rooms.built);
    CHECK(solveMap(bothFalse.loaded, "[]").neverReached == std::vector<size_t>{3});
    CHECK(checkReachability(bothFalse.loaded).reachedDoorsOpen == 2);

    // Plain slabs carry no flag and are walked.
    const BuiltMoving plain = buildMoving(pit("", ""), objects);
    REQUIRE(plain.rooms.built);
    CHECK(slabFlags(plain.rooms, true) == std::set<uint32_t>{0});
    CHECK(solveMap(plain.loaded, "[]").neverReached.empty());

    // Nothing stands on a slab that is not solid: a chest placed over it is on the pit's floor.
    CHECK(issueText(buildRooms(pit(", solid: false, visible: false", ""), objects))
        .find("neither seen nor touched") != std::string::npos);

    // A raised level: unseen it leaves the room's floor whole under it and is stood on; a sunken one takes
    // neither word.
    const auto dais = [](const std::string &words, const std::string &floor)
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    ceiling: 384\n"
            "    levels:\n"
            "      - {outline: [[256, 256], [768, 256], [768, 768], [256, 768]], floor: " + floor + words + "}\n";
    };
    const BuiltRooms unseen = buildRooms(dais(", visible: false", "24"), objects);
    INFO(issueText(unseen));
    REQUIRE(unseen.built);
    // The room's floor at 0 runs on under the level (no hole), and the level's top at 24 is there and flagged.
    CHECK(unseen.levelsOver(1, 512, 512, true) == std::vector<int>{0, 24});
    size_t flagged = 0;

    for (const OpenYAMM::Game::IndoorFace &face : unseen.map.faces)
    {
        flagged += (face.attributes & invisible) != 0 ? 1 : 0;
    }

    // Top and four sides.
    CHECK(flagged == 5);
    const BuiltRooms seen = buildRooms(dais("", "24"), objects);
    REQUIRE(seen.built);
    CHECK(seen.levelsOver(1, 512, 512, true) == std::vector<int>{24});
    CHECK(issueText(buildRooms(dais(", solid: false", "-64"), objects))
        .find("a sunken level is the floor itself where it lies") != std::string::npos);
}

TEST_CASE("an event switches lights on and off, by numbers the lock keeps, and a light may start dark")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 512], [0, 512]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a, at: [128, 256]}\n"
        "plates:\n"
        "  - {id: plate:on, room: room:a, at: [512, 256], size: [128, 128]}\n"
        "  - {id: plate:off, room: room:a, at: [800, 256], size: [128, 128]}\n"
        "lights:\n"
        "  - {id: light:always, room: room:a, at: [128, 128]}\n"
        "  - {id: light:dark, room: room:a, at: [512, 128], on: false}\n"
        "  - {id: light:lamp, room: room:a, at: [800, 128]}\n";
    const std::string wiring =
        "format: 0\n"
        "events:\n"
        "  - {id: evt:on, preset: script, trigger: step, source: plate:on,\n"
        "     effects: [{lights_on: light:dark}, {lights_off: [light:lamp]}]}\n"
        "  - {id: evt:off, preset: script, trigger: step, source: plate:off,\n"
        "     effects: [{lights_off: [light:dark]}, {lights_on: [light:lamp]}]}\n";
    const BuiltMoving built = buildMoving(rooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // The dark light is number 1 (it is read first), the lamp 2; the light no event names has none.
    CHECK(built.lua.find("evt.SetLight(1, 1)") != std::string::npos);
    CHECK(built.lua.find("evt.SetLight(2, 0)") != std::string::npos);
    CHECK(built.lua.find("evt.SetLight(1, 0)") != std::string::npos);
    CHECK(built.lua.find("evt.SetLight(2, 1)") != std::string::npos);
    REQUIRE(built.rooms.map.lights.size() == 3);
    std::map<int, int> attributesById;

    for (const OpenYAMM::Game::IndoorLight &light : built.rooms.map.lights)
    {
        attributesById[light.id] = light.attributes;
    }

    // Number 0: the light that is never switched. The dark one carries the engine's "switched off" bit.
    REQUIRE(attributesById.size() == 3);
    CHECK((attributesById[0] & 0x08) == 0);
    CHECK((attributesById[1] & 0x08) != 0);
    CHECK((attributesById[2] & 0x08) == 0);

    // The lock holds the numbers.
    const Project project = projectFromTexts({{"project.yml", CardText}, {"rooms.yml", std::string(ThemeText) + rooms},
        {"objects.yml", objects}, {"wiring.yml", wiring}});
    LoweredIndoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerIndoorProject(project, LoweringOptions(), lowered, issues));
    CHECK(lowered.ids.lights == std::map<std::string, int>{{"light:dark", 1}, {"light:lamp", 2}});
    CHECK(lowered.ids.toDocument()["lights"]["light:lamp"].as<int>() == 2);

    // A light that is not there, and a dark light nobody lights.
    std::string wrong = wiring;
    wrong.replace(wrong.find("light:dark"), 10, "light:none");
    CHECK(issueText(buildMoving(rooms, objects, wrong).rooms).find("there is no light light:none") != std::string::npos);
    const Project unlit = projectFromTexts({{"project.yml", CardText}, {"rooms.yml", std::string(ThemeText) + rooms},
        {"objects.yml", objects}});
    LoweredIndoorMap unlitLowered;
    std::vector<ProjectIssue> unlitIssues;
    REQUIRE(lowerIndoorProject(unlit, LoweringOptions(), unlitLowered, unlitIssues));
    CHECK(std::any_of(unlitLowered.warnings.begin(), unlitLowered.warnings.end(), [](const std::string &warning)
    {
        return warning.find("light:dark starts dark (`on: false`) and no event lights it") != std::string::npos;
    }));
}

#include "core/Metrics.h"

TEST_CASE("a texture name with a hyphen, a kill count and a Lua test as conditions, a ridge over chamfered corners, "
          "and torches counted as light sources")
{
    // `sign01-1` is a texture of the game: the name pattern takes the hyphen.
    const BuiltRooms sign = buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [512, 0], [512, 512], [0, 512]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    walls:\n"
        "      - wall: north\n"
        "        panels:\n"
        "          - {offset: 128, length: 256, bottom: 64, height: 128, surface: {texture: sign01-1, size: [256, 128]}}\n");
    INFO(issueText(sign));
    REQUIRE(sign.built);
    CHECK(std::any_of(sign.map.faces.begin(), sign.map.faces.end(), [](const OpenYAMM::Game::IndoorFace &face)
    {
        return face.textureName == "sign01-1";
    }));

    // Conditions: every monster of a group dead, one placed monster dead, so many of any kind, and a Lua
    // expression; each stands in front of what the handler does.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const auto luaOf = [&rooms](const std::string &condition, std::vector<ProjectIssue> &issues)
    {
        const std::string objects =
            "format: 0\n"
            "start: {room: room:a, at: [128, 128]}\n"
            "monsters:\n"
            "  - {id: monster:guard, room: room:a, at: [512, 512], monster: 1}\n"
            "  - {id: monster:boss, room: room:a, at: [700, 700], monster: 1, group: 2}\n";
        const std::string wiring =
            "format: 0\n"
            "events:\n"
            "  - {id: evt:dead, preset: script, trigger: timer, every: 2, once: true,\n"
            "     condition: " + condition + ", effects: [{gold: 50}]}\n";
        const Project project = projectFromTexts({{"project.yml", CardText},
            {"rooms.yml", std::string(ThemeText) + rooms}, {"objects.yml", objects}, {"wiring.yml", wiring}});
        LoweringOptions options;
        options.monsterTableText = MonsterTableText;
        options.monsterDescriptorTableText = MonsterDescriptorText;
        LoweredIndoorMap lowered;
        lowerIndoorProject(project, options, lowered, issues);
        std::string body;

        for (const LoweredEvent &event : lowered.events)
        {
            for (const std::string &line : event.body)
            {
                body += line + "\n";
            }
        }

        return body;
    };
    std::vector<ProjectIssue> issues;
    const std::string group = luaOf("{kills: {group: 2}}", issues);
    INFO(group);
    CHECK(issues.empty());
    CHECK(group.find("if not (evt.CheckMonstersKilled(ActorKillCheck.Group, 2, 0, false)) then") != std::string::npos);
    // The gold is given after the test.
    CHECK(group.find("CheckMonstersKilled") < group.find("AddValue(Gold, 50)"));
    CHECK(luaOf("{kills: {group: 2, at_least: 1}}", issues).find("ActorKillCheck.Group, 2, 1, false")
        != std::string::npos);
    // The boss is the scene's second actor: number 1.
    CHECK(luaOf("{kills: {monster: monster:boss}}", issues).find("ActorKillCheck.ActorIdOe, 1, 0, false")
        != std::string::npos);
    CHECK(luaOf("{kills: {at_least: 2}}", issues).find("ActorKillCheck.Any, 0, 2, false") != std::string::npos);
    CHECK(luaOf("{lua: \"IsAtLeast(MapVar(3), 2)\", qbit: 7}", issues)
        .find("if not ((IsAtLeast(MapVar(3), 2)) and IsQBitSet(QBit(7))) then") != std::string::npos);
    CHECK(issues.empty());
    luaOf("{kills: {group: 9}}", issues);
    REQUIRE(issues.size() == 1);
    CHECK(issues[0].message.find("no monster of objects.yml `monsters` has `group: 9`") != std::string::npos);
    issues.clear();
    luaOf("{kills: {monster: monster:none}}", issues);
    REQUIRE(issues.size() == 1);
    CHECK(issues[0].message.find("there is no monster monster:none") != std::string::npos);

    // A ridge along x over a convex room with chamfered corners: every corner rises to its own place on the ridge,
    // which has four different points on one line and no flat top.
    const BuiltRooms ridge = buildRooms(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 1216], [128, 1088], [1728, 1088], [1856, 1216], [1856, 2624], [128, 2624], [0, 2496]]\n"
        "    floor: 0\n"
        "    ceiling: 640\n"
        "    ceiling_levels:\n"
        "      - {ceiling: 1088, top_scale: [1, 0]}\n",
        "format: 0\nstart: {room: room:a, at: [512, 1500]}\n");
    INFO(issueText(ridge));
    REQUIRE(ridge.built);
    CHECK(ridge.hasVertex(0, 1856, 1088));
    CHECK(ridge.hasVertex(128, 1856, 1088));
    CHECK(ridge.hasVertex(1728, 1856, 1088));
    CHECK(ridge.hasVertex(1856, 1856, 1088));
    // No level face lies at the ridge's height.
    CHECK(ridge.levelsOver(1, 900, 1856, false).empty() == false);
    CHECK(std::none_of(ridge.map.faces.begin(), ridge.map.faces.end(), [&ridge](const OpenYAMM::Game::IndoorFace &face)
    {
        return ridge.heights(face) == std::array<int, 2>{1088, 1088};
    }));

    // Light sources: the map's own lights and the decorations whose table row has a light radius, found by the
    // row's name (a shipped map) or by its place in the list (a built one: the table's number less one).
    LoadedMap lit;
    lit.world = "mm6";
    lit.fileName = "lit.blv";
    lit.indoor = buildRooms(rooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\n").map;
    OpenYAMM::Game::IndoorEntity byName;
    byName.name = "Torch06";
    OpenYAMM::Game::IndoorEntity byPlace;
    byPlace.name = "t3";
    byPlace.decorationListId = 20;
    OpenYAMM::Game::IndoorEntity dark;
    dark.name = "barrel";
    dark.decorationListId = 4;
    lit.indoor->entities = {byName, byPlace, dark};
    lit.indoor->lights.push_back({});
    MetricsOptions metricsOptions;
    metricsOptions.decorationTableText =
        "Decoration Data\n#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\n"
        "5\tbarrel\tbarrel\t0\t8\t8\t0\n"
        "21\ttorch02\ttorch\t0\t7\t52\t512\n"
        "122\ttorch06\ttorch\t0\t8\t64\t512\n";
    JsonWriter metricsWriter(true);
    writeMetricsJson(lit, metricsOptions, metricsWriter);
    const std::string metrics = metricsWriter.take();
    INFO(metrics);
    CHECK(metrics.find("\"lights\": 1,") != std::string::npos);
    CHECK(metrics.find("\"decoration_lights\": 2,") != std::string::npos);
    CHECK(metrics.find("\"light_sources\": 3,") != std::string::npos);
}

TEST_CASE("a ladder, a pulsing light and a placed sound go into the scene as the game reads them")
{
    // A hall with a loft 256 up along its north side.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 640\n"
        "    platforms:\n"
        "      - {at: [512, 896], size: [1024, 256], rise: 256}\n";
    const auto objects = [](const std::string &ladder)
    {
        return
            "format: 0\n"
            "start: {room: room:a, at: [128, 128]}\n"
            "plates:\n"
            "  - {id: plate:on, room: room:a, at: [512, 256], size: [128, 128]}\n"
            "ladders:\n"
            "  - " + ladder + "\n"
            "sounds:\n"
            "  - {id: sound:drip, room: room:a, at: [300, 300], sound: waterdrip.wav, radius: 800, wait: [2, 6]}\n"
            "lights:\n"
            "  - {id: light:pool, room: room:a, at: [512, 300], height: 32, radius: 512, color: [80, 255, 120],\n"
            "     on: false, pulse: {intensity: [0.4, 1], radius: [384, 512], frequency: 0.5}}\n"
            "  - {id: light:plain, room: room:a, at: [128, 128]}\n";
    };
    const std::string wiring =
        "format: 0\n"
        "events:\n"
        "  - {id: evt:on, preset: script, trigger: step, source: plate:on, effects: [{lights_on: light:pool}]}\n";
    const BuiltMoving built =
        buildMoving(rooms, objects("{id: ladder:loft, room: room:a, at: [512, 768], facing: n, height: 256}"), wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    const OpenYAMM::Game::IndoorSceneData &scene = *built.loaded.indoorScene;
    // The ladder: from the hall's floor to the loft's, the party set down 64 beyond it on the loft.
    REQUIRE(scene.ladders.size() == 1);
    CHECK(scene.ladders[0].id == "loft");
    CHECK(scene.ladders[0].bottom == std::array<float, 3>{512.0f, 768.0f, 0.0f});
    CHECK(scene.ladders[0].top == std::array<float, 3>{512.0f, 768.0f, 256.0f});
    CHECK(scene.ladders[0].topExit == std::array<float, 3>{512.0f, 832.0f, 256.0f});
    CHECK(scene.ladders[0].facingDegrees == 90.0f);
    CHECK(scene.ladders[0].grabAtTop);
    // Its rails and rungs are drawn and not solid: two rails and a rung every 32, each face untouchable.
    const uint32_t untouchable = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Untouchable);
    size_t ladderFaces = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        ladderFaces += (face.attributes & untouchable) != 0 ? 1 : 0;
    }

    // Ten pieces (two rails, eight rungs), six faces each.
    CHECK(ladderFaces == 60);

    // The pulsing light is a light of the scene, dark until the plate's event lights it by its key; the plain light
    // is the map's only light record.
    REQUIRE(scene.pulsingLights.size() == 1);
    CHECK(scene.pulsingLights[0].lightKey == 40001);
    CHECK_FALSE(scene.pulsingLights[0].startOn);
    CHECK(scene.pulsingLights[0].position == std::array<float, 3>{512.0f, 300.0f, 32.0f});
    CHECK(scene.pulsingLights[0].intensity == std::array<float, 4>{0.4f, 1.0f, 0.5f, 0.0f});
    CHECK(scene.pulsingLights[0].radius == std::array<float, 4>{384.0f, 512.0f, 0.5f, 0.0f});
    CHECK(built.lua.find("evt.SetLight(40001, 1)") != std::string::npos);
    CHECK(built.rooms.map.lights.size() == 1);

    // The sound.
    REQUIRE(scene.ambientSounds.size() == 1);
    CHECK(scene.ambientSounds[0].key == 1);
    CHECK(scene.ambientSounds[0].sound == "waterdrip.wav");
    CHECK(scene.ambientSounds[0].outerRadius == 800.0f);
    CHECK(scene.ambientSounds[0].innerRadius == 200.0f);
    CHECK(scene.ambientSounds[0].waitMaxSeconds == 6.0f);

    // A ladder that ends where no floor is, and one faced away from what it climbs.
    CHECK(issueText(buildMoving(rooms,
        objects("{id: ladder:loft, room: room:a, at: [512, 768], facing: n, height: 200}"), wiring).rooms)
        .find("the ladder climbs from 0 to 200 and the party steps off at [512, 832]") != std::string::npos);
    CHECK(issueText(buildMoving(rooms,
        objects("{id: ladder:loft, room: room:a, at: [512, 300], facing: n, height: 256}"), wiring).rooms)
        .find("where the floors are at 0 (room:a)") != std::string::npos);
    CHECK(issueText(buildMoving(rooms,
        objects("{id: ladder:loft, room: room:a, at: [512, 8], facing: n, height: 256}"), wiring).rooms)
        .find("the climber stands in front of the ladder, at [512, -16], which is not inside room:a")
        != std::string::npos);
}

TEST_CASE("a placed monster takes hit points and a name of its own, as far as the scene's actor record holds them")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a, at: [128, 128]}\n"
        "monsters:\n"
        "  - {id: monster:boss, room: room:a, at: [512, 512], monster: 1, hp: 39, name: jeric whistlebone, group: 2}\n"
        "  - {id: monster:mate, room: room:a, at: [700, 700], monster: 1, name: Mrs Wobbles, group: 2}\n"
        "  - {id: monster:plain, room: room:a, at: [300, 700], monster: 1}\n";
    const Project project = projectFromTexts({{"project.yml", CardText},
        {"rooms.yml", std::string(ThemeText) + rooms}, {"objects.yml", objects}});
    LoweringOptions options;
    options.monsterTableText = MonsterTableText;
    options.monsterDescriptorTableText = MonsterDescriptorText;
    options.uniqueNameTableText = "#\tName\n1\tBlackwell Cooper\n2\tJeric Whistlebone\n";
    LoweredIndoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerIndoorProject(project, options, lowered, issues));
    REQUIRE(lowered.monsters.size() == 3);
    // Three times a Goblin's 13 hit points, and the table's own spelling of the name with its row.
    CHECK(lowered.monsters[0].hitPoints == 39);
    CHECK(lowered.monsters[0].displayName == "Jeric Whistlebone");
    CHECK(lowered.monsters[0].uniqueNameIndex == 2);
    // A name the table does not have is kept for the corpse, and the build says what it would need.
    CHECK(lowered.monsters[1].hitPoints == 13);
    CHECK(lowered.monsters[1].displayName == "Mrs Wobbles");
    CHECK(lowered.monsters[1].uniqueNameIndex == 0);
    CHECK(std::count_if(lowered.warnings.begin(), lowered.warnings.end(), [](const std::string &warning)
    {
        return warning.find("monster:mate is named \"Mrs Wobbles\"") != std::string::npos
            && warning.find("shows on the monster's corpse only") != std::string::npos;
    }) == 1);
    CHECK(lowered.monsters[2].displayName.empty());
    CHECK(lowered.monsters[2].uniqueNameIndex == 0);
}

TEST_CASE("a secret door carries the engine's secret flag on its leaf")
{
    const uint32_t secret = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::IsSecret);
    const auto secretFaces = [secret](const BuiltMoving &built)
    {
        size_t count = 0;

        for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
        {
            count += (face.attributes & secret) != 0 ? 1 : 0;
        }

        return count;
    };
    const BuiltMoving hidden = buildMoving(DoorRooms, doorObjects("secret: true"), DoorWiring);
    INFO(issueText(hidden.rooms));
    REQUIRE(hidden.rooms.built);
    // The leaf's faces, and no other face of the map; the leaf still runs its event when clicked.
    CHECK(secretFaces(hidden) >= 2);
    CHECK(boundEvent(hidden.loaded) != 0);
    const BuiltMoving plain = buildMoving(DoorRooms, doorObjects("thickness: 16"), DoorWiring);
    REQUIRE(plain.rooms.built);
    CHECK(secretFaces(plain) == 0);
    CHECK(secretFaces(buildMoving(DoorRooms, doorObjects("leaves: 2, kind: slide_left, secret: true"), DoorWiring))
        >= 4);
}

TEST_CASE("a loft stands as a level over a floor that sags")
{
    // A hall whose floor falls 48 toward a gutter along its south wall, with a loft at 256 over its north third.
    const auto hall = [](const std::string &loftFloor)
    {
        return
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    floor_points: [[0, 0, -48], [1024, 0, -48], [0, 1024, 0], [1024, 1024, 0]]\n"
            "    ceiling: 640\n"
            "    levels:\n"
            "      - {outline: [[64, 640], [960, 640], [960, 960], [64, 960]], floor: " + loftFloor + "}\n";
    };
    const std::string objects = "format: 0\nstart: {room: room:a, at: [512, 300]}\n";
    const BuiltRooms built = buildRooms(hall("256"), objects);
    INFO(issueText(built));
    REQUIRE(built.built);
    // The loft's top at 256, and the sagging floor still there under it (at y 800: -48 * 224 / 1024 = -10.5).
    const std::vector<int> floors = built.levelsOver(1, 512, 800, true);
    REQUIRE(floors.size() == 2);
    CHECK(floors.back() == 256);
    CHECK(floors.front() <= 0);
    // Its sides reach down to the floor's lowest place along its rim (y 640: -18).
    CHECK(built.hasVertex(64, 640, -18));
    CHECK(built.hasVertex(64, 640, 256));
    // A level at the floor's own height is still refused, with the rule.
    CHECK(issueText(buildRooms(hall("-5"), objects))
        .find("A level that stands higher than the floor everywhere under it") != std::string::npos);
}

TEST_CASE("a chest's top takes a surface of its own")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a, at: [128, 128]}\n"
        "chests:\n"
        "  - {id: chest:desk, room: room:a, at: [512, 512], size: [128, 64, 72],\n"
        "     surface: {texture: side, size: [128, 128]}, top_surface: {texture: top, size: [128, 128]}}\n";
    const std::string wiring = "format: 0\nevents:\n  - {id: evt:desk, preset: chest, source: chest:desk}\n";
    const BuiltMoving built = buildMoving(rooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    size_t tops = 0;
    size_t sides = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        if (face.textureName == "top")
        {
            ++tops;
            CHECK(built.rooms.heights(face) == std::array<int, 2>{72, 72});
            // Clicked like the rest of the chest.
            CHECK(face.cogTriggered != 0);
        }

        sides += face.textureName == "side" ? 1 : 0;
    }

    CHECK(tops == 1);
    CHECK(sides == 4);
}

TEST_CASE("a map variable given by a number past the 75 the game keeps is refused")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "plates:\n  - {id: plate:p, room: room:a, at: [300, 300], size: [96, 96]}\n";
    const auto wiring = [](const std::string &number)
    {
        return "format: 0\nevents:\n  - {id: evt:p, preset: script, trigger: step, source: plate:p,\n"
            "     condition: {map_var: " + number + "}, effects: [{set: {var: {map_var: " + number
            + "}, value: 2}}]}\n";
    };
    const BuiltMoving kept = buildMoving(rooms, objects, wiring("74"));
    INFO(issueText(kept.rooms));
    CHECK(kept.rooms.built);
    const BuiltMoving past = buildMoving(rooms, objects, wiring("75"));
    CHECK_FALSE(past.rooms.built);
    CHECK(issueText(past.rooms).find("the game keeps the map variables 0 to 74") != std::string::npos);
}

TEST_CASE("a leaf folds against its jamb, moves part of its way, passes its other half, and bears several pictures")
{
    // Room c stands where a leaf sliding left (north) out of the doorway would come to stand.
    const std::string rooms = std::string(DoorRooms).insert(std::string(DoorRooms).find("openings:"),
        "  - {id: room:c, outline: [[520, 400], [800, 400], [800, 640], [520, 640]], floor: 0, ceiling: 256}\n");
    CHECK(issueText(buildMoving(rooms, doorObjects("kind: slide_left"), DoorWiring).rooms)
        .find("would stand inside room:c") != std::string::npos);

    // Folding, it needs no room: only the free edge (y 192, the south side of the doorway) is in the record, and
    // open it stands 4 short of the north jamb (y 320).
    const BuiltMoving fold = buildMoving(rooms, doorObjects("kind: slide_left, fold: true"), DoorWiring);
    INFO(issueText(fold.rooms));
    REQUIRE(fold.rooms.built);
    REQUIRE(fold.doors.size() == 1);
    CHECK(fold.direction(1) == std::array<int, 3>{0, -65536, 0});
    CHECK(fold.door(1)["move_length"].as<int>() == 124);
    REQUIRE(fold.door(1)["vertex_ids"].size() >= 4);

    for (const YAML::Node &y : fold.door(1)["y_offsets"])
    {
        CHECK(y.as<int>() == 316);
    }

    // The leaf's corners at the jamb are no part of the record: they stay.
    size_t atJamb = 0;

    for (const YAML::Node &vertexId : fold.door(1)["vertex_ids"])
    {
        atJamb += fold.rooms.map.vertices[vertexId.as<size_t>()].y == 320 ? 1 : 0;
    }

    CHECK(atJamb == 0);
    CHECK_FALSE(fold.walks({256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, false));
    CHECK(fold.walks({256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, true));
    // Its picture lies at one texel to the unit and rides with the door.
    const uint32_t rides = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::TextureMoveByDoor);
    const auto span = [](const BuiltMoving &built, const std::string &texture, bool across)
    {
        int most = 0;

        for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
        {
            if (face.textureName != texture)
            {
                continue;
            }

            const std::vector<int16_t> &texels = across ? face.textureUs : face.textureVs;
            most = std::max<int>(most, *std::max_element(texels.begin(), texels.end())
                - *std::min_element(texels.begin(), texels.end()));
        }

        return most;
    };
    const std::string picture = ", surface: {texture: leaf, size: [64, 64]}";
    const BuiltMoving folded = buildMoving(rooms, doorObjects("kind: slide_left, fold: true" + picture), DoorWiring);
    REQUIRE(folded.rooms.built);
    CHECK(span(folded, "leaf", true) == 128);
    CHECK(span(folded, "leaf", false) == 192);
    size_t riding = 0;

    for (const OpenYAMM::Game::IndoorFace &face : folded.rooms.map.faces)
    {
        riding += face.textureName == "leaf" && (face.attributes & rides) != 0 ? 1 : 0;
    }

    CHECK(riding == 2);

    // `travel`: a leaf that opens part of the way, and one that cannot move farther than it is wide.
    const BuiltMoving part = buildMoving(DoorRooms, doorObjects("kind: slide_left, travel: 64"), DoorWiring);
    REQUIRE(part.rooms.built);
    CHECK(part.door(1)["move_length"].as<int>() == 64);
    CHECK(issueText(buildMoving(DoorRooms, doorObjects("kind: slide_left, travel: 200"), DoorWiring).rooms)
        .find("a leaf moves at most its own width") != std::string::npos);
    CHECK(issueText(buildMoving(DoorRooms, doorObjects("kind: slide_left, fold: true, travel: 128"), DoorWiring).rooms)
        .find("less 1 when it folds") != std::string::npos);

    // `split: across`: a lower half going left and an upper half going right, each the doorway's whole width.
    const BuiltMoving passing = buildMoving(
        rooms, doorObjects("kind: slide_left, leaves: 2, split: across, fold: true"), DoorWiring);
    INFO(issueText(passing.rooms));
    REQUIRE(passing.rooms.built);
    REQUIRE(passing.doors.size() == 2);
    CHECK(passing.direction(1) == std::array<int, 3>{0, -65536, 0});
    CHECK(passing.direction(2) == std::array<int, 3>{0, 65536, 0});
    CHECK(passing.door(1)["move_length"].as<int>() == 124);

    for (const YAML::Node &z : passing.door(1)["z_offsets"])
    {
        CHECK(z.as<int>() <= 96);
    }

    for (const YAML::Node &z : passing.door(2)["z_offsets"])
    {
        CHECK(z.as<int>() >= 96);
    }

    CHECK(issueText(buildMoving(DoorRooms, doorObjects("kind: slide_left, split: across"), DoorWiring).rooms)
        .find("`split` says how a door of two leaves is cut") != std::string::npos);

    // Pictures: two side by side on one lifting leaf, left to right as seen from each side; stretched, each over
    // its half (64 texels over 64 units), or one picture tiled over the leaf at its own size.
    const auto extent = [](const BuiltMoving &built, const std::string &texture, int x)
    {
        std::array<int, 2> range = {100000, -100000};

        for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
        {
            if (face.textureName != texture || built.rooms.map.vertices[face.vertexIndices[0]].x != x)
            {
                continue;
            }

            for (const uint16_t vertex : face.vertexIndices)
            {
                range[0] = std::min<int>(range[0], built.rooms.map.vertices[vertex].y);
                range[1] = std::max<int>(range[1], built.rooms.map.vertices[vertex].y);
            }
        }

        return range;
    };
    const std::string pair =
        "pictures: [[{texture: pa, size: [64, 192]}, {texture: pb, size: [64, 192]}]]";
    const BuiltMoving pictures = buildMoving(DoorRooms, doorObjects(pair), DoorWiring);
    INFO(issueText(pictures.rooms));
    REQUIRE(pictures.rooms.built);
    // Room a looks east at the leaf's front (x 520): its left is north. Room b looks west at the back (x 536).
    CHECK(extent(pictures, "pa", 520) == std::array<int, 2>{256, 320});
    CHECK(extent(pictures, "pb", 520) == std::array<int, 2>{192, 256});
    CHECK(extent(pictures, "pa", 536) == std::array<int, 2>{192, 256});
    CHECK(extent(pictures, "pb", 536) == std::array<int, 2>{256, 320});
    CHECK(span(pictures, "pa", true) == 64);
    const BuiltMoving stretched = buildMoving(DoorRooms, doorObjects("kind: slide_up" + picture), DoorWiring);
    const BuiltMoving tiled = buildMoving(DoorRooms, doorObjects("kind: slide_up, tile: true" + picture), DoorWiring);
    REQUIRE(stretched.rooms.built);
    REQUIRE(tiled.rooms.built);
    CHECK(span(stretched, "leaf", true) == 64);
    CHECK(span(tiled, "leaf", true) == 128);
    // Two rows of two at their own size meet in the middle of the doorway (y 256, height 96): the upper left
    // picture ends there with its last texel row and column.
    const BuiltMoving seal = buildMoving(DoorRooms, doorObjects(
        "kind: slide_left, leaves: 2, fold: true, pictures: [[{texture: qa, size: [128, 128]}, "
        "{texture: qb, size: [128, 128]}], [{texture: qc, size: [128, 128]}, {texture: qd, size: [128, 128]}]]"),
        DoorWiring);
    INFO(issueText(seal.rooms));
    REQUIRE(seal.rooms.built);
    CHECK(extent(seal, "qa", 520) == std::array<int, 2>{256, 320});
    CHECK(extent(seal, "qd", 520) == std::array<int, 2>{192, 256});

    // What cannot be built says so.
    CHECK(issueText(buildMoving(DoorRooms, doorObjects("kind: slide_left, fold: true, " + pair), DoorWiring).rooms)
        .find("folds sideways and has two pictures side by side") != std::string::npos);
    CHECK(issueText(buildMoving(DoorRooms, doorObjects(
        "kind: slide_left, fold: true, surface: {texture: leaf, size: [64, 64], scale: 2}"), DoorWiring).rooms)
        .find("one texel to the unit") != std::string::npos);
    CHECK(issueText(buildMoving(DoorRooms, doorObjects(
        "tile: true, pictures: [[{texture: pa, size: [64, 192], mirror: true}]]"), DoorWiring).rooms)
        .find("`mirror` turns over a picture that is stretched") != std::string::npos);
    CHECK(issueText(buildMoving(DoorRooms, doorObjects("kind: hinged, fold: true"), DoorWiring).rooms)
        .find("is for sliding doors") != std::string::npos);
    // A mirrored picture runs the other way across its leaf.
    const auto runsLeftToRight = [](const BuiltMoving &built)
    {
        for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
        {
            if (face.textureName != "pa" || built.rooms.map.vertices[face.vertexIndices[0]].x != 520)
            {
                continue;
            }

            int north = 0;
            int south = 0;

            for (size_t index = 0; index < face.vertexIndices.size(); ++index)
            {
                (built.rooms.map.vertices[face.vertexIndices[index]].y == 320 ? north : south) = face.textureUs[index];
            }

            // Seen from room a the leaf's left is north.
            return north < south;
        }

        return false;
    };
    const BuiltMoving plainPicture = buildMoving(
        DoorRooms, doorObjects("pictures: [[{texture: pa, size: [64, 192]}]]"), DoorWiring);
    const BuiltMoving mirrored = buildMoving(
        DoorRooms, doorObjects("pictures: [[{texture: pa, size: [64, 192], mirror: true}]]"), DoorWiring);
    REQUIRE(plainPicture.rooms.built);
    REQUIRE(mirrored.rooms.built);
    CHECK(runsLeftToRight(plainPicture));
    CHECK_FALSE(runsLeftToRight(mirrored));
}

TEST_CASE("item spawn points and fixed tiers, a chest with a level for each roll, one chest of two, a count in a "
          "condition, a draw of one item and Lua that names map variables")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a, at: [128, 128]}\n"
        "chests:\n"
        "  - {id: chest:hoard, room: room:a, at: [512, 512], items: [2053], random_levels: [6, 4, 3], trap_level: 2}\n"
        "  - {id: chest:plain, room: room:a, at: [700, 512], treasure_level: 3, random_items: 2}\n"
        "  - {id: chest:spent, box_of: chest:hoard, random_levels: [6, 5, 3, 1]}\n"
        "spawns:\n"
        "  - {id: spawn:pack, room: room:a, at: [300, 800], slot: 2}\n"
        "  - {id: spawn:captain, room: room:a, at: [400, 800], slot: 2, tier: c}\n"
        "  - {id: spawn:shelf, room: room:a, at: [600, 800], kind: item, treasure_level: 4}\n";
    const std::string wiring =
        "format: 0\n"
        "variables: [zeta, searches, hoard_seen]\n"
        "events:\n"
        "  - id: evt:hoard\n"
        "    preset: chest\n"
        "    source: chest:hoard\n"
        "    condition: {any: [{map_var: hoard_seen}, {not: {qbit: 1029}}]}\n"
        "    else_effects: [{open_chest: chest:spent}]\n"
        "    effects: [{set: {var: {map_var: hoard_seen}, value: 1}}, {qbit: 1029}]\n"
        "  - id: evt:plain\n"
        "    preset: chest\n"
        "    source: chest:plain\n"
        "    condition: {map_var: {name: searches, below: 4}}\n"
        "    effects:\n"
        "      - {add: {var: {map_var: searches}, value: 1}}\n"
        "      - {give_item: {one_of: [1961, 1973, 1976]}}\n"
        "      - {lua: \"if IsAtLeast(MapVar(searches), 4) then evt.StatusText('empty') end\"}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    // Spawn records as a shipped map has them: type 3 with the slot, 4 to 12 for a slot with a tier (c of slot 2
    // is 11), type 2 with the treasure level.
    REQUIRE(built.map.spawns.size() == 3);
    std::set<std::pair<int, int>> spawns;

    for (const OpenYAMM::Game::IndoorSpawn &spawn : built.map.spawns)
    {
        spawns.insert({spawn.typeId, spawn.index});
    }

    CHECK(spawns == std::set<std::pair<int, int>>{{3, 2}, {3, 11}, {2, 4}});
    // The chests with levels of their own are chest records of the starting state (0 the hoard, 2 its second
    // contents; 1 is the plain chest's place, left empty for its loot container): the fixed item, then one roll
    // for each level as a number below zero.
    REQUIRE(built.scene->initialState.chests.size() == 3);
    const auto things = [&built](size_t chest)
    {
        std::vector<int> found;
        const std::vector<uint8_t> &raw = built.scene->initialState.chests[chest].rawItems;

        for (size_t slot = 0; slot * 36 + 4 <= raw.size(); ++slot)
        {
            const int32_t value = static_cast<int32_t>(static_cast<uint32_t>(raw[slot * 36])
                | static_cast<uint32_t>(raw[slot * 36 + 1]) << 8 | static_cast<uint32_t>(raw[slot * 36 + 2]) << 16
                | static_cast<uint32_t>(raw[slot * 36 + 3]) << 24);

            if (value != 0)
            {
                found.push_back(value);
            }
        }

        return found;
    };
    CHECK(things(0) == std::vector<int>{2053, -6, -4, -3});
    CHECK(things(1).empty());
    CHECK(things(2) == std::vector<int>{-6, -5, -3, -1});
    CHECK(built.scene->initialState.chests[0].flags == 1);
    // One chest of two: the clicked box shows the hoard, or its second contents where the condition fails.
    const size_t orElse = built.lua.find("evt.OpenChest(2)");
    const size_t own = built.lua.find("evt.OpenChest(0)");
    REQUIRE(orElse != std::string::npos);
    REQUIRE(own != std::string::npos);
    CHECK(orElse < own);
    // A count, a draw written as one give for each item, and the variable's number in the Lua text (`searches`
    // is the lock's number, whatever the order of declaration).
    const std::string number = std::to_string(built.lua.find("not IsAtLeast(MapVar(1), 4)") != std::string::npos ? 1
        : built.lua.find("not IsAtLeast(MapVar(0), 4)") != std::string::npos ? 0 : 2);
    CHECK(built.lua.find("if not (not IsAtLeast(MapVar(" + number + "), 4)) then") != std::string::npos);
    CHECK(built.lua.find("evt.RandomBetween(1, 3)") != std::string::npos);
    CHECK(built.lua.find("GiveItem(1961)") != std::string::npos);
    CHECK(built.lua.find("GiveItem(1976)") != std::string::npos);
    CHECK(built.lua.find("if IsAtLeast(MapVar(" + number + "), 4) then evt.StatusText('empty') end")
        != std::string::npos);
    CHECK(built.lua.find("MapVar(searches)") == std::string::npos);

    // The flow shows each outcome of the draw as a way of its own.
    LoadedMap map;
    map.fullScriptSource =
        "evt.map[7] = function()\n"
        "    local drawn = evt.RandomBetween(1, 3)\n"
        "    if drawn == 1 then evt.OpenChest(1) elseif drawn == 2 then evt.OpenChest(2) else evt.OpenChest(3) end\n"
        "end\n";
    std::string json;
    std::string errorMessage;
    REQUIRE(exploreEventHandlers(map, json, errorMessage));
    CHECK(json.find("open chest 1") != std::string::npos);
    CHECK(json.find("open chest 2") != std::string::npos);
    CHECK(json.find("open chest 3") != std::string::npos);
    CHECK(json.find("random 1 to 3 is 2") != std::string::npos);
    CHECK(YAML::Load(json)[0]["paths"].size() == 3);

    // What cannot be built says so; a number that a named variable took is warned of.
    const auto refused = [&rooms](const std::string &objectsText, const std::string &wiringText)
    {
        return issueText(buildPlaced(rooms, objectsText, {}, CardText, wiringText));
    };
    const std::string start = "format: 0\nstart: {room: room:a, at: [128, 128]}\n";
    CHECK(refused(start + "spawns:\n  - {id: spawn:x, room: room:a, at: [300, 300], kind: item, slot: 1}\n", "")
        .find("it needs `treasure_level`") != std::string::npos);
    CHECK(refused(start + "spawns:\n  - {id: spawn:x, room: room:a, at: [300, 300]}\n", "")
        .find("it needs `slot`") != std::string::npos);
    CHECK(refused(start + "chests:\n  - {id: chest:x, room: room:a, at: [300, 300], gold: 50, random_levels: [3]}\n",
        "").find("holds no amount of gold") != std::string::npos);
    CHECK(refused(start + "chests:\n  - {id: chest:x, box_of: chest:none}\n", "")
        .find("there is no chest chest:none") != std::string::npos);
    CHECK(refused(start + "chests:\n  - {id: chest:b, room: room:a, at: [300, 300]}\n"
        "  - {id: chest:x, box_of: chest:b}\n",
        "format: 0\nevents:\n  - {id: evt:x, preset: chest, source: chest:x}\n")
        .find("has no box of its own") != std::string::npos);
    const BuiltPlaced numbered = buildPlaced(rooms, start + "plates:\n  - {id: plate:p, room: room:a, at: [300, 300], "
        "size: [96, 96]}\n", {}, CardText,
        "format: 0\nvariables: [count]\nevents:\n  - {id: evt:p, preset: script, trigger: step, source: plate:p,\n"
        "     condition: {lua: \"not IsAtLeast(MapVar(0), 4)\"}, effects: [{add: {var: {map_var: count}, value: 1}}]}\n");
    REQUIRE(numbered.built);
    CHECK(std::any_of(numbered.warnings.begin(), numbered.warnings.end(), [](const std::string &warning)
    {
        return warning.find("ids.lock.yml gives that number to the variable `count`") != std::string::npos;
    }));
}

TEST_CASE("the lock keeps removed ids until a prune, a chest refuses a roll written as a negative item, and a liquid "
          "needs no size")
{
    const std::string rooms = std::string(ThemeText) +
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab}\n"
        "chests:\n  - {id: chest:kept, room: room:a, at: [256, 256]}\n";
    const std::string wiring =
        "format: 0\nvariables: [count]\nevents:\n  - {id: evt:door, preset: door, source: door:ab}\n"
        "  - {id: evt:hello, preset: text, trigger: load, once: true, text: Hello}\n";
    // A lock as an earlier project left it: a chest, a door, two events and a variable it no longer has, and the
    // entries that belong to live ids (a door's second leaf, an event's `once` variable).
    const std::string lock = "format: 0\n"
        "events: {evt:door: 7, evt:gone: 3, evt:old_trap: 4}\n"
        "doors: {door:ab: 2, door:ab.leaf2: 5, door:removed: 1}\n"
        "containers: {chest:kept: 1, chest:sold: 0}\n"
        "map_vars: {count: 4, renamed: 0, once.hello: 6, once.gone: 1}\n";
    const Project project = projectFromTexts({
        {"project.yml", CardText}, {"rooms.yml", rooms}, {"objects.yml", objects}, {"wiring.yml", wiring},
        {"ids.lock.yml", lock}});
    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    REQUIRE(lowerIndoorProject(project, {}, lowered, issues));
    // A build keeps every entry (S5_BROWSER_EDITOR.md 2.4.1): an undo that brings a removed object back finds its
    // number, and no other id is given it. New ids take the lowest number no entry holds.
    CHECK(lowered.ids.events == std::map<std::string, int>{{"evt:door", 7}, {"evt:gone", 3}, {"evt:hello", 1},
        {"evt:old_trap", 4}});
    CHECK(lowered.ids.doors == std::map<std::string, int>{{"door:ab", 2}, {"door:ab.leaf2", 5}, {"door:removed", 1}});
    CHECK(lowered.ids.containers == std::map<std::string, int>{{"chest:kept", 1}, {"chest:sold", 0}});
    CHECK(lowered.ids.mapVars == std::map<std::string, int>{{"count", 4}, {"renamed", 0}, {"once.hello", 6},
        {"once.gone", 1}});

    // The prune drops what the project no longer has, by the rule of what is live. (A second leaf stays only while
    // its door has two: door:ab has one since, so its `.leaf2` goes, as Castle Darkmoor's door 5's should have.)
    IdsLock pruned = lowered.ids;
    const std::vector<std::string> retired = retiredLockEntries(project, pruned, true);
    CHECK(retired == std::vector<std::string>{"events: evt:gone 3", "events: evt:old_trap 4", "doors: door:ab.leaf2 5",
        "doors: door:removed 1", "containers: chest:sold 0", "map_vars: once.gone 1", "map_vars: renamed 0"});
    CHECK(pruned.events == std::map<std::string, int>{{"evt:door", 7}, {"evt:hello", 1}});
    CHECK(pruned.doors == std::map<std::string, int>{{"door:ab", 2}});
    CHECK(pruned.containers == std::map<std::string, int>{{"chest:kept", 1}});
    CHECK(pruned.mapVars == std::map<std::string, int>{{"count", 4}, {"once.hello", 6}});
    // Listing without dropping leaves the lock as it was.
    IdsLock listed = lowered.ids;
    CHECK(retiredLockEntries(project, listed, false).size() == 7);
    CHECK(listed.events.size() == 4);

    // A chest record's roll of level n is the item -n in a shipped map; in `items` it is refused with the word to
    // use. Item 0 too.
    for (const char *pItem : {"-2", "0"})
    {
        const Project negative = projectFromTexts({{"project.yml", CardText}, {"rooms.yml", rooms},
            {"objects.yml", "format: 0\nstart: {room: room:a}\nchests:\n  - {id: chest:c, room: room:a, at: [256, 256], "
                "items: [" + std::string(pItem) + "]}\n"}});
        std::vector<ProjectIssue> refused;
        LoweredIndoorMap notLowered;
        CHECK_FALSE(lowerIndoorProject(negative, {}, notLowered, refused));
        CHECK(hasIssue(refused, "schema", "say rolls with `random_levels`"));
    }

    // A surface without a size: a liquid of the asset root's table (by name or by prefix, in its world) is drawn
    // by the game with no picture and passes; any other texture is refused, with where to read its size.
    LoweringOptions options;
    options.liquidTableText =
        "liquids:\n"
        "  - {id: water_mm6, kind: water, applies_to: [terrain, face], match: {texture_names: [6wtrtyl], "
        "texture_prefixes: [6wtrdr]}}\n"
        "  - {id: lava_mm9, kind: lava, applies_to: [face], worlds: [mm9], match: {texture_names: [lava9]}}\n"
        "  - {id: water_terrain, kind: water, applies_to: [terrain], match: {texture_names: [tw00]}}\n";
    const auto withFloor = [&rooms](const std::string &floor)
    {
        std::string text = rooms;
        const std::string plain = "    floor: {texture: floor, size: [128, 128]}\n";
        text.replace(text.find(plain), plain.size(), "    floor: " + floor + "\n");
        return projectFromTexts({{"project.yml", CardText}, {"rooms.yml", text},
            {"objects.yml", "format: 0\nstart: {room: room:a}\n"}});
    };
    const auto sizeIssues = [&options](const Project &liquidProject)
    {
        std::vector<ProjectIssue> found;
        LoweredIndoorMap liquidLowered;
        lowerIndoorProject(liquidProject, options, liquidLowered, found);
        return std::count_if(found.begin(), found.end(), [](const ProjectIssue &issue)
        {
            return issue.message.find("needs `size`") != std::string::npos;
        });
    };
    CHECK(sizeIssues(withFloor("{texture: 6wtrtyl}")) == 0);
    CHECK(sizeIssues(withFloor("{texture: 6WTRDR03}")) == 0);
    CHECK(sizeIssues(withFloor("{texture: lava9}")) == 1);
    CHECK(sizeIssues(withFloor("{texture: tw00}")) == 1);
    CHECK(sizeIssues(withFloor("{texture: floor}")) == 1);
    CHECK(sizeIssues(withFloor("{texture: floor, size: [128, 128]}")) == 0);
    // Without the table (no asset root) nothing is checked.
    options.liquidTableText.clear();
    CHECK(sizeIssues(withFloor("{texture: floor}")) == 0);
    // One texture given two sizes in a map (the floor as the wall's texture at another size): a warning, the build
    // keeping one size per texture.
    const auto sizeWarnings = [&options](const Project &sizedProject)
    {
        std::vector<ProjectIssue> found;
        LoweredIndoorMap sizedLowered;
        lowerIndoorProject(sizedProject, options, sizedLowered, found);
        return std::count_if(sizedLowered.warnings.begin(), sizedLowered.warnings.end(), [](const std::string &text)
        {
            return text.find("is given size [64, 256] here and [128, 128]") != std::string::npos;
        });
    };
    CHECK(sizeWarnings(withFloor("{texture: wall, size: [64, 256]}")) == 1);
    CHECK(sizeWarnings(withFloor("{texture: wall, size: [128, 128]}")) == 0);
}

TEST_CASE("a monster starts hidden and carries an item, its record repeats its kind's experience, and a door runs "
          "one event from each side")
{
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [100, 100]}\n"
        "monsters:\n"
        "  - {id: monster:droid, room: room:a, monster: 2, at: [256, 256], group: 56, hidden: true, "
        "carries: Ghost Ring}\n"
        "  - {id: monster:captain, room: room:a, monster: Swordsman, at: [600, 256], carries: 1}\n"
        "doors:\n  - {id: door:ab, opening: open:ab}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:open, preset: door, source: door:ab, side: room:b}\n"
        "  - {id: evt:stuck, preset: text, source: door:ab, side: room:a, text: \"The door won't budge.\"}\n"
        "  - {id: evt:wake, preset: script, trigger: load, effects: [{show_actors: 56}]}\n";
    const BuiltPlaced built = buildPlaced(PlacedRooms, objects, PlacedTables, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    const std::vector<OpenYAMM::Game::MapDeltaActor> &actors = built.scene->initialState.actors;
    REQUIRE(actors.size() == 2);
    // The Invisible bit, the carried item (a name of items.txt or a number), the kind's experience.
    CHECK(actors[0].attributes == 0x00010000u);
    CHECK(actors[0].carriedItemId == 9);
    CHECK(actors[0].monsterInfoId == 2);
    CHECK(actors[0].monsterId == 90);
    CHECK(actors[1].attributes == 0);
    CHECK(actors[1].carriedItemId == 1);
    CHECK(built.lua.find("evt.SetMonGroupBit(56, MonsterBits.Invisible, 0)") != std::string::npos);
    CHECK(std::none_of(built.warnings.begin(), built.warnings.end(), [](const std::string &warning)
    {
        return warning.find("start hidden") != std::string::npos;
    }));

    // The door: its faces toward room:b (east, +x) run the door event, those toward room:a the text; no face runs
    // both.
    std::map<int, std::pair<int, int>> sides;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.cogTriggered == 0)
        {
            continue;
        }

        double normalX = 0.0;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const OpenYAMM::Game::IndoorVertex &current = built.map.vertices[face.vertexIndices[index]];
            const OpenYAMM::Game::IndoorVertex &next =
                built.map.vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            normalX += double(current.y - next.y) * double(current.z + next.z);
        }

        (normalX > 0.0 ? sides[face.cogTriggered].first : sides[face.cogTriggered].second) += 1;
    }

    const auto handler = [&built](const std::string &call)
    {
        const size_t at = built.lua.find(call);
        const size_t head = built.lua.rfind("RegisterEvent(", at);
        return at == std::string::npos || head == std::string::npos ? -1 : std::stoi(built.lua.substr(head + 14));
    };
    const int opens = handler("evt.SetDoorState(");
    const int stuck = handler("won't budge");
    REQUIRE(opens > 0);
    REQUIRE(stuck > 0);
    REQUIRE(sides.size() == 2);
    CHECK(sides[opens].first > 0);
    CHECK(sides[opens].second == 0);
    CHECK(sides[stuck].first == 0);
    CHECK(sides[stuck].second > 0);
    // The door is still one moving part, with the faces of both sides in its record.
    REQUIRE(built.scene->initialState.doors.size() == 1);
    const std::vector<uint16_t> &doorFaces = built.scene->initialState.doors[0].door.faceIds;

    for (const int event : {opens, stuck})
    {
        CHECK(std::any_of(doorFaces.begin(), doorFaces.end(), [&built, event](uint16_t face)
        {
            return built.map.faces[face].cogTriggered == event;
        }));
    }

    // What cannot be built says so.
    const auto refused = [](const std::string &objectsText, const std::string &wiringText)
    {
        return issueText(buildPlaced(PlacedRooms, objectsText, PlacedTables, CardText, wiringText));
    };
    const std::string start = "format: 0\nstart: {room: room:a, at: [100, 100]}\n";
    const std::string door = start + "doors:\n  - {id: door:ab, opening: open:ab}\n"
        "chests:\n  - {id: chest:c, room: room:a, at: [300, 300]}\n";
    CHECK(refused(door, "format: 0\nevents:\n  - {id: evt:a, preset: door, source: door:ab, side: room:b}\n"
        "  - {id: evt:b, preset: door, source: door:ab, side: room:b}\n").find("for the side of room:b")
        != std::string::npos);
    CHECK(refused(door, "format: 0\nevents:\n  - {id: evt:a, preset: door, source: door:ab, side: room:b}\n"
        "  - {id: evt:b, preset: door, source: door:ab}\n").find("a door one from each side") != std::string::npos);
    CHECK(refused(door, "format: 0\nevents:\n  - {id: evt:a, preset: door, source: door:ab, side: room:c}\n")
        .find("`side` is the room the door's event is used from: room:a or room:b") != std::string::npos);
    CHECK(refused(door, "format: 0\nevents:\n  - {id: evt:a, preset: chest, source: chest:c, side: room:a}\n")
        .find("binds a clicked door's event") != std::string::npos);
    CHECK(refused(start + "monsters:\n  - {id: monster:m, room: room:a, monster: 1, hidden: true}\n", "")
        .find("give it `group: <number>`") != std::string::npos);
    CHECK(refused(start + "monsters:\n  - {id: monster:m, room: room:a, monster: 1, carries: 77}\n", "")
        .find("there is no item number 77") != std::string::npos);
    CHECK(refused(start + "monsters:\n  - {id: monster:m, room: room:a, monster: 1, group: 3}\n",
        "format: 0\nevents:\n  - {id: evt:w, preset: script, trigger: load, effects: [{hide_actors: 4}]}\n")
        .find("no monster has group 4") != std::string::npos);
    const BuiltPlaced unseen = buildPlaced(PlacedRooms,
        start + "monsters:\n  - {id: monster:m, room: room:a, monster: 1, group: 3, hidden: true}\n", PlacedTables);
    REQUIRE(unseen.built);
    CHECK(std::any_of(unseen.warnings.begin(), unseen.warnings.end(), [](const std::string &warning)
    {
        return warning.find("group 3 start hidden and no event shows them") != std::string::npos;
    }));
}

TEST_CASE("solve waits for the monsters a kill test counts, steps onto and off a ramp's end, climbs a ladder, and "
          "calls a slot lower than the party a niche")
{
    // A step of 32 at a ramp's foot, which the game's party walks up and down: from either room the other is reached.
    const std::string slope =
        "rooms:\n"
        "  - {id: room:low, outline: [[0, -512], [512, -512], [512, 0], [0, 0]], floor: 0, ceiling: 512}\n"
        "  - {id: room:ramp, outline: [[0, 0], [512, 0], [512, 448], [0, 448]], floor: 256,\n"
        "     slope: {to: 32, toward: south}, ceiling: 640}\n"
        "openings:\n"
        "  - {id: open:foot, from: room:low, to: room:ramp, width: full, height: full}\n";

    for (const char *pStart : {"start: {room: room:low, at: [256, -256]}", "start: {room: room:ramp, at: [256, 300]}"})
    {
        const BuiltMoving built = buildMoving(slope, "format: 0\n" + std::string(pStart) + "\n");
        INFO(issueText(built.rooms));
        REQUIRE(built.rooms.built);
        const SolveResult solved = solveMap(built.loaded, "[]");
        CHECK(sectorsReached(solved) == 2);
        CHECK(checkReachability(built.loaded).unreachableSectors.empty());
    }

    // A loft reached only by a ladder, and a room 64 high that nothing reaches: a niche, not "never reached".
    const BuiltMoving ladder = buildMoving(
        "rooms:\n"
        "  - {id: room:pit, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 640}\n"
        "  - {id: room:loft, outline: [[528, 0], [1040, 0], [1040, 512], [528, 512]], floor: 256, ceiling: 640}\n"
        "  - {id: room:slot, outline: [[2000, 0], [2512, 0], [2512, 512], [2000, 512]], floor: 0, ceiling: 64}\n"
        "openings:\n"
        "  - {id: open:loft, from: room:pit, to: room:loft, width: 128, height: 256, sill: 0}\n",
        "format: 0\nstart: {room: room:pit, at: [96, 256]}\nladders:\n"
        "  - {id: ladder:up, room: room:pit, at: [508, 320], facing: e, height: 256, exit: [600, 256]}\n");
    INFO(issueText(ladder.rooms));
    REQUIRE(ladder.rooms.built);
    const SolveResult climbed = solveMap(ladder.loaded, "[]");
    CHECK(sectorsReached(climbed) == 2);
    CHECK(climbed.neverReached.empty());
    CHECK(climbed.nichesNotReached == std::vector<size_t>{3});
    const ReachabilityResult reach = checkReachability(ladder.loaded);
    CHECK(reach.unreachableSectors.empty());
    CHECK(reach.tooLowNotReached == std::vector<size_t>{3});

    // A door that opens once the monsters of group 5 are dead: it waits while they stand behind it, and opens at
    // once when they stand on the party's side.
    BuiltMoving door = buildMoving(DoorRooms, doorObjects("thickness: 16"), DoorWiring);
    INFO(issueText(door.rooms));
    REQUIRE(door.rooms.built);
    const int doorEvent = boundEvent(door.loaded);
    REQUIRE(doorEvent != 0);
    const std::string killFlow = flowOf(doorEvent,
        "{\"tests\": [{\"what\": \"CheckMonstersKilled(1, 5, 0, false)\", \"taken\": true}], "
        "\"effects\": [\"door 1 open\"]}");
    OpenYAMM::Game::MapDeltaActor behind;
    behind.x = 700;
    behind.y = 256;
    behind.z = 0;
    behind.group = 5;
    door.loaded.state->actors = {behind};
    const SolveResult waits = solveMap(door.loaded, killFlow);
    CHECK(sectorsReached(waits) == 1);
    CHECK(std::any_of(waits.waiting.begin(), waits.waiting.end(), [](const std::string &line)
    {
        return line.find("the monsters it counts dead") != std::string::npos;
    }));
    door.loaded.state->actors[0].x = 256;
    CHECK(sectorsReached(solveMap(door.loaded, killFlow)) == 2);
    // Another group does not count.
    door.loaded.state->actors[0].x = 700;
    door.loaded.state->actors[0].group = 6;
    CHECK(sectorsReached(solveMap(door.loaded, killFlow)) == 2);
}

TEST_CASE("a decoration is clicked, an event runs on leaving the map, effects change faces, a question is asked and "
          "a door's event may run once")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 512], [0, 512]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    platforms:\n"
        "      - {id: platform:cube, at: [768, 256], size: [128, 128], rise: 64}\n"
        "  - {id: room:b, outline: [[1056, 128], [1312, 128], [1312, 384], [1056, 384]], floor: 0, ceiling: 160}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 128}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [100, 100]}\n"
        "doors:\n  - {id: door:ab, opening: open:ab}\n"
        "chests:\n  - {id: chest:c, room: room:a, at: [500, 100]}\n"
        "decorations:\n  - {id: deco:keg, room: room:a, decoration: smlbarel, at: [300, 300]}\n";
    const std::string wiring =
        "format: 0\nvariables: [left]\nevents:\n"
        "  - {id: evt:keg, preset: script, source: deco:keg, effects: [{text: A keg.}]}\n"
        "  - {id: evt:bye, preset: script, trigger: leave, effects: [{set: {var: {map_var: left}, value: 1}}]}\n"
        "  - {id: evt:door, preset: door, source: door:ab, once: true}\n"
        "  - {id: evt:paint, preset: script, trigger: load, effects: [{set_texture: {of: platform:cube, to: cfb1}},\n"
        "     {passable: platform:cube}, {hide: door:ab}]}\n"
        "  - {id: evt:ask, preset: script, source: platform:cube, effects: [{open_chest: chest:c}],\n"
        "     question: {message: \"Open it?\", ask: \"Open (Yes/No)?\", answers: [Yes, Y], wrong_text: Not now.,\n"
        "     wrong_effects: [{lua: Xeen.wrongAnswer()}]}}\n";
    const std::vector<std::pair<std::string, std::string>> tables = {
        {"decoration_data.txt",
            "Decoration Data\t\t\tDescriptor\n"
            "#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\tSoundId\t"
            "Flags\tSpriteId\n\n"
            "1\tnull\tnull\t0\t8\t8\t0\t0\t0\t0\t0\t0\t0\n"
            "157\tsmlbarel\tkeg\t0\t30\t40\t0\t0\t0\t0\t0\t0\t17789\n"}};
    const BuiltPlaced built = buildPlaced(rooms, objects, tables, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    const auto handler = [&built](const std::string &id)
    {
        const size_t at = built.lua.find("-- " + id + "\n");
        return at == std::string::npos ? -1 : std::stoi(built.lua.substr(built.lua.find("RegisterEvent(", at) + 14));
    };
    const auto bodyOf = [&built](const std::string &id)
    {
        const size_t at = built.lua.find("-- " + id + "\n");
        return at == std::string::npos ? std::string() : built.lua.substr(at, built.lua.find("\nend", at) - at);
    };

    // The keg: the BLV entity's second event field.
    INFO(built.lua);
    REQUIRE(built.map.entities.size() == 1);
    CHECK(built.map.entities[0].eventIdSecondary == handler("evt:keg"));
    // On leaving the map.
    CHECK(built.lua.find("onLeave = {" + std::to_string(handler("evt:bye")) + "}") != std::string::npos);
    // A door's event that works once.
    CHECK(bodyOf("evt:door").find("if IsAtLeast(MapVar(") != std::string::npos);
    // Faces by their cog number: the block and the door's leaf carry one each.
    const std::string paint = bodyOf("evt:paint");
    const size_t textureAt = paint.find("evt.SetTexture(");
    REQUIRE(textureAt != std::string::npos);
    const int blockCog = std::atoi(paint.c_str() + textureAt + 15);
    CHECK(paint.find("evt.SetTexture(" + std::to_string(blockCog) + ", \"cfb1\")") != std::string::npos);
    CHECK(paint.find("evt.SetFacetBit(" + std::to_string(blockCog) + ", FaceAttribute.Untouchable, 1)")
        != std::string::npos);
    const size_t hideAt = paint.find("FaceAttribute.Invisible, 1)");
    REQUIRE(hideAt != std::string::npos);
    const int doorCog = std::atoi(paint.c_str() + paint.rfind("evt.SetFacetBit(", hideAt) + 16);
    CHECK(doorCog != blockCog);
    const auto facesWithCog = [&built](int cog)
    {
        return std::count_if(built.map.faces.begin(), built.map.faces.end(), [cog](const OpenYAMM::Game::IndoorFace &f)
        {
            return f.cogNumber == cog;
        });
    };
    CHECK(facesWithCog(blockCog) >= 5);
    CHECK(facesWithCog(doorCog) >= 2);
    // The question: the handler takes its step, opens the chest only on a right answer, and the chest is listed as
    // one this event shows.
    const std::string ask = bodyOf("evt:ask");
    const int askId = handler("evt:ask");
    CHECK(ask.find("function(continueStep)") != std::string::npos);
    CHECK(ask.find("if continueStep == 2 then\n        evt.OpenChest(") != std::string::npos);
    CHECK(ask.find("evt.StatusText(\"Not now.\")") != std::string::npos);
    // A wrong answer runs `wrong_effects` after its line, inside the wrong answer's branch.
    const size_t wrongAt = ask.find("Xeen.wrongAnswer()");
    REQUIRE(wrongAt != std::string::npos);
    CHECK(wrongAt > ask.find("if continueStep ~= nil then"));
    CHECK(wrongAt > ask.find("evt.StatusText(\"Not now.\")"));
    CHECK(wrongAt < ask.find("evt.SetMessage(\"Open it?\")"));
    CHECK(ask.find("evt.SetMessage(\"Open it?\")") != std::string::npos);
    CHECK(ask.find("evt.AskQuestion(" + std::to_string(askId) + ", 1, 0, 2, \"Open (Yes/No)?\", {\"Yes\", \"Y\"})")
        != std::string::npos);
    CHECK(built.lua.find("[" + std::to_string(askId) + "] = {") != std::string::npos);

    // The flow follows the answers: a path for each step it is continued at.
    LoadedMap map;
    map.fullScriptSource =
        "evt.map[5] = function(continueStep)\n"
        "    if continueStep == 2 then evt.OpenChest(3) return end\n"
        "    if continueStep ~= nil then return end\n"
        "    evt.AskQuestion(5, 1, 0, 2, 'Open?', {'Yes'})\n"
        "end\n";
    std::string json;
    std::string errorMessage;
    REQUIRE(exploreEventHandlers(map, json, errorMessage));
    CHECK(YAML::Load(json)[0]["paths"].size() == 3);
    CHECK(json.find("answered: continued at step 2") != std::string::npos);
    CHECK(json.find("open chest 3") != std::string::npos);

    // A Yes/No prompt's buttons (AskChoiceWithAnswerSteps, which event_support.lua's helper calls as evt.) continue it
    // the same way: the Yes branch is explored.
    map.fullScriptSource =
        "evt.map[6] = function(continueStep)\n"
        "    if continueStep == 1 then evt.OpenChest(4) return end\n"
        "    if continueStep ~= nil then return end\n"
        "    evt.AskChoiceWithAnswerSteps(6, 3, 'Open?', {{Answer = 'Yes', Step = 1}, {Answer = 'No', Step = 2}})\n"
        "end\n";
    REQUIRE(exploreEventHandlers(map, json, errorMessage));
    CHECK(YAML::Load(json)[0]["paths"].size() == 4);
    CHECK(json.find("answered: continued at step 1") != std::string::npos);
    CHECK(json.find("open chest 4") != std::string::npos);

    // What cannot be built says so.
    const auto refused = [&rooms, &objects, &tables](const std::string &wiringText)
    {
        return issueText(buildPlaced(rooms, objects, tables, CardText, "format: 0\nevents:\n" + wiringText));
    };
    CHECK(refused("  - {id: evt:c, preset: chest, source: chest:c, once: true}\n").find("`once` belongs to")
        != std::string::npos);
    // (A chest's faces are a target since merge point 25: P5's hidden chest; a decoration's are not.)
    CHECK(refused("  - {id: evt:p, preset: script, trigger: load, effects: [{passable: deco:keg}]}\n")
        .find("deco:keg is none of them") != std::string::npos);
    CHECK(refused("  - {id: evt:p, preset: script, trigger: load, effects: [{set_texture: {of: door:ab}}]}\n")
        .find("set_texture is {of:") != std::string::npos);
    CHECK(refused("  - {id: evt:q, preset: script, source: deco:keg, question: {ask: \"Why?\", answers: []}}\n")
        .find("answers") != std::string::npos);
    CHECK(refused("  - {id: evt:l, preset: text, trigger: leave, source: door:ab, text: Bye}\n")
        .find("a leave event runs by itself") != std::string::npos);
}

TEST_CASE("floor points on a rock island's corners do not count the island's inside, and a path takes 64 points")
{
    // The island's inside is never built: a point high on one of its corners is no steep floor there.
    const std::string island =
        "rooms:\n"
        "  - id: room:cave\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    floor_points: [[384, 512, 200], [480, 416, 0], [416, 640, 0], [700, 300, 0]]\n"
        "    steep_floor: true\n"
        "    ceiling: 640\n"
        "    pillars:\n"
        "      - {outline: [[256, 384], [384, 512], [480, 416], [416, 640], [256, 640]]}\n";
    const BuiltPlaced built = buildPlaced(island, "format: 0\nstart: {room: room:cave, at: [800, 800]}\n", {});
    INFO(issueText(built));
    CHECK(built.built);
    // The same points without the island: the triangle between them is floor, and too steep.
    const std::string bare = island.substr(0, island.find("    pillars:"));
    const BuiltPlaced steep = buildPlaced(bare, "format: 0\nstart: {room: room:cave, at: [800, 800]}\n", {});
    CHECK_FALSE(steep.built);
    CHECK(issueText(steep).find("rises") != std::string::npos);

    // A corridor of 40 points, which the schema refused past 24 before.
    std::string path = "[";

    for (int index = 0; index < 40; ++index)
    {
        path += std::string(index == 0 ? "" : ", ") + "[" + std::to_string(index * 256) + ", "
            + (index % 2 == 0 ? "0" : "384") + "]";
    }

    const BuiltPlaced corridor = buildPlaced(
        "rooms:\n  - {id: room:long, path: " + path + "], width: 128, floor: 0, ceiling: 256}\n",
        "format: 0\nstart: {room: room:long, at: [128, 192]}\n", {});
    INFO(issueText(corridor));
    CHECK(corridor.built);
}

TEST_CASE("consume inside any, all or not is refused, and once works on a clicked script")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "switches:\n  - {id: switch:w, room: room:a, wall: s}\n";
    const auto build = [&rooms, &objects](const std::string &event)
    {
        return buildPlaced(rooms, objects, {}, CardText, "format: 0\nevents:\n  - " + event + "\n");
    };
    CHECK(issueText(build("{id: evt:w, preset: switch, source: switch:w, condition: {any: [{qbit: 5}, "
        "{item: 7, consume: true}]}}")).find("`consume` takes the item when the event's whole condition holds")
        != std::string::npos);
    CHECK(issueText(build("{id: evt:w, preset: switch, source: switch:w, condition: {not: {item: 7, consume: true}}}"))
        .find("not inside `any`, `all` or `not`") != std::string::npos);
    const BuiltPlaced top = build("{id: evt:w, preset: switch, source: switch:w, condition: {item: 7, consume: true}}");
    INFO(issueText(top));
    REQUIRE(top.built);
    CHECK(top.lua.find("RemoveItem(7)") != std::string::npos);
    const BuiltPlaced once = build("{id: evt:w, preset: script, source: switch:w, once: true, effects: [{gold: 10}]}");
    REQUIRE(once.built);
    CHECK(once.lua.find("if IsAtLeast(MapVar(0), 1) then") != std::string::npos);
    CHECK(once.lua.find("SetValue(MapVar(0), 1)") != std::string::npos);
}

TEST_CASE("a wall without thickness is warned of only where both rooms draw wall in its plane")
{
    // A slot 64 high under a hall's wall, open over its whole side: only the hall draws wall there.
    const auto warns = [](const std::string &slot, const std::string &opening)
    {
        const std::string rooms =
            "rooms:\n"
            "  - {id: room:hall, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 1024}\n"
            "  - {id: room:slot, outline: [[1024, 0], [1280, 0], [1280, 1024], [1024, 1024]], " + slot + ",\n"
            "     walls: [{wall: 0, surface: {texture: other, size: [128, 128]}}]}\n"
            "openings:\n  - {id: open:slot, from: room:hall, to: room:slot, " + opening + "}\n";
        const BuiltPlaced built = buildPlaced(rooms, "format: 0\nstart: {room: room:hall, at: [128, 128]}\n", {});
        INFO(issueText(built));
        REQUIRE(built.built);
        return std::any_of(built.warnings.begin(), built.warnings.end(), [](const std::string &warning)
        {
            return warning.find("without thickness") != std::string::npos;
        });
    };
    CHECK_FALSE(warns("floor: 0, ceiling: 64", "width: full, height: 64"));
    // A walkway over a pit: its floor is the opening's sill, so only the pit's wall stands below it.
    CHECK_FALSE(warns("floor: -512, ceiling: 1024", "width: full, height: full"));
    // Both rooms reach above the opening, or the opening is narrower than their shared wall: wall back to back.
    CHECK(warns("floor: 0, ceiling: 512", "width: full, height: 256"));
    CHECK(warns("floor: 0, ceiling: 64", "width: 256, height: 64"));
}

#include "core/Coplanar.h"
#include "core/Things.h"

namespace
{
// A hall 1024 by 768 with a post, and the user's walk through Gharik's Forge (2026-11-13) as its objects.
const char *const HandleRooms =
    "rooms:\n"
    "  - id: room:a\n"
    "    outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]]\n"
    "    floor: 0\n"
    "    ceiling: 512\n"
    "    platforms:\n"
    "      - {id: platform:post, at: [512, 384], size: [32, 32], rise: 192}\n";

// The texture of every face the event runs from, counted.
std::map<std::string, int> texturesOfEvent(const BuiltRooms &built, int eventId)
{
    std::map<std::string, int> textures;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.cogTriggered == eventId)
        {
            textures[face.textureName] += 1;
        }
    }

    return textures;
}
}

TEST_CASE("a lever is a post and an arm that its own event moves as a door, back again where the event toggles")
{
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "lifts:\n  - {id: lift:l, room: room:a, at: [800, 600], size: [128, 128], travel: 128}\n"
        "switches:\n"
        "  - {id: switch:a_lever, room: room:a, wall: w, kind: lever}\n"
        "  - {id: switch:b_once, room: room:a, wall: e, kind: lever}\n"
        "  - {id: switch:c_button, room: room:a, wall: n, kind: button}\n"
        "  - {id: switch:d_post, room: room:a, block: platform:post, side: w, kind: lever}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:a, preset: switch, source: switch:a_lever, toggles: [lift:l]}\n"
        "  - {id: evt:b, preset: switch, source: switch:b_once, opens: [lift:l]}\n"
        "  - {id: evt:c, preset: switch, source: switch:c_button, toggles: [lift:l]}\n"
        "  - {id: evt:d, preset: switch, source: switch:d_post, opens: [lift:l]}\n";
    const BuiltMoving built = buildMoving(HandleRooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // Door 1 is the lift; 2 to 5 the four handles. A lever's arm sinks 16 at the speed of the Forge's (50).
    CHECK(built.door(2)["move_length"].as<int>() == 16);
    CHECK(built.direction(2) == std::array<int, 3>{0, 0, 65536});
    // The button is pushed 15 into the north wall (+y), to 1 short of its face.
    CHECK(built.door(4)["move_length"].as<int>() == 15);
    CHECK(built.direction(4) == std::array<int, 3>{0, -65536, 0});
    // The arm stands out of the post to 40 from the west wall, 4 to 8 under the post's top (the arm's middle at 122).
    CHECK(built.rooms.hasVertex(40, 380, 120));
    CHECK(built.rooms.hasVertex(40, 388, 124));
    CHECK(built.rooms.hasVertex(8, 380, 96));
    // A toggling event moves its own handle by Trigger (down, and up again on the next use); a one-way event to its
    // end, where it stays.
    CHECK(built.lua.find("evt.SetDoorState(2, DoorAction.Trigger)") != std::string::npos);
    CHECK(built.lua.find("evt.SetDoorState(3, DoorAction.Open)") != std::string::npos);
    CHECK(built.lua.find("evt.SetDoorState(4, DoorAction.Trigger)") != std::string::npos);
    CHECK(built.lua.find("evt.SetDoorState(5, DoorAction.Open)") != std::string::npos);
    CHECK(built.lua.find("SetTexture") == std::string::npos);
    // The lever's faces (post and arm) are clicked, in the Forge's beam texture; the button's face is MM7's.
    CHECK(texturesOfEvent(built.rooms, 1)["BemH16a"] >= 9);
    CHECK(texturesOfEvent(built.rooms, 3)["7t1butt"] == 1);
    CHECK(texturesOfEvent(built.rooms, 3)["7t1butts"] == 4);

    const auto refused = [&wiring](const std::string &from, const std::string &to)
    {
        std::string changed =
            "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
            "lifts:\n  - {id: lift:l, room: room:a, at: [800, 600], size: [128, 128], travel: 128}\n"
            "switches:\n"
            "  - {id: switch:a_lever, room: room:a, wall: w, kind: lever}\n";
        changed.replace(changed.find(from), from.size(), to);
        const BuiltMoving result = buildMoving(HandleRooms, changed, "format: 0\nevents:\n"
            "  - {id: evt:a, preset: switch, source: switch:a_lever, toggles: [lift:l]}\n");
        CHECK_FALSE(result.rooms.built);
        return issueText(result.rooms);
    };
    CHECK(refused("kind: lever}", "kind: lever, on: t1swdu}").find("shows that it was used by moving")
        != std::string::npos);
    CHECK(refused("kind: lever}", "kind: lever, reach: 10}").find("reaches at least 16") != std::string::npos);
    CHECK(refused("kind: lever}", "kind: lever, depth: 10}").find("`depth` belongs to a button")
        != std::string::npos);
}

TEST_CASE("a plate's picture follows its state: back where its event toggles, by the branch where it has else_effects")
{
    const auto lua = [](const std::string &event)
    {
        const BuiltMoving built = buildMoving(HandleRooms,
            "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
            "lifts:\n  - {id: lift:l, room: room:a, at: [800, 600], size: [128, 128], travel: 128}\n"
            "switches:\n  - {id: switch:p, room: room:a, wall: w}\n",
            "format: 0\nvariables: [flag]\nevents:\n  - {id: evt:p, preset: switch, source: switch:p, " + event
                + "}\n");
        INFO(issueText(built.rooms));
        REQUIRE(built.rooms.built);
        return built.lua;
    };
    // Toggling: a map variable of its own (toggle.p) says the state; the picture is set from it on every use, before
    // the condition (a use that the condition refuses flips it too: the plate is pushed all the same).
    const std::string toggled = lua("toggles: [lift:l], condition: {map_var: flag}");
    CHECK(toggled.find("if IsAtLeast(MapVar(0), 1) then\n        SetValue(MapVar(0), 0)\n"
        "        evt.SetTexture(1, \"t1swdd\")\n    else\n        SetValue(MapVar(0), 1)\n"
        "        evt.SetTexture(1, \"t1swdu\")\n    end\n    if not (") != std::string::npos);
    // Two states by a condition: used where it holds, unused on the other branch.
    const std::string branched = lua("condition: {map_var: flag}, effects: [{gold: 1}], else_effects: [{gold: 2}]");
    CHECK(branched.find("AddValue(Gold, 2)\n        evt.SetTexture(1, \"t1swdd\")\n        return")
        != std::string::npos);
    CHECK(branched.find("evt.SetTexture(1, \"t1swdu\")") != std::string::npos);
    // One way: used once its work is done, never back.
    const std::string once = lua("opens: [lift:l]");
    CHECK(once.find("evt.SetTexture(1, \"t1swdu\")") != std::string::npos);
    CHECK(once.find("t1swdd") == std::string::npos);
}

TEST_CASE("a chest of a kind is laid end, middle and end on its long sides and top, as the shipped chests are")
{
    const auto build = [](const std::string &chest)
    {
        return buildMoving(HandleRooms,
            "format: 0\nstart: {room: room:a, at: [128, 128]}\nchests:\n"
            "  - {id: chest:c, room: room:a, at: [256, 600], " + chest + "}\n",
            "format: 0\nevents:\n  - {id: evt:c, preset: chest, source: chest:c}\n");
    };
    const BuiltMoving mm6 = build("facing: e, kind: ch3");
    INFO(issueText(mm6.rooms));
    REQUIRE(mm6.rooms.built);
    // 96 by 64 and 64 high: both long sides ch3frLE (16), ch3frntB (64), ch3frRE (16); ch3side on the ends; the top
    // ch3topLE, ch3topB, ch3topRE.
    const std::map<std::string, int> textures = texturesOfEvent(mm6.rooms, 1);
    CHECK(textures == std::map<std::string, int>{{"ch3frle", 2}, {"ch3frntb", 2}, {"ch3frre", 2}, {"ch3side", 2},
        {"ch3topb", 1}, {"ch3tople", 1}, {"ch3topre", 1}});
    CHECK(mm6.rooms.hasVertex(208, 568, 64));
    CHECK(mm6.rooms.hasVertex(304, 632, 64));
    // MM7's chest: a lid 16 high that slopes at front and back up to a top 32 deep, 80 high in all.
    const BuiltMoving mm7 = build("facing: e, kind: 7gt002");
    REQUIRE(mm7.rooms.built);
    const std::map<std::string, int> sloped = texturesOfEvent(mm7.rooms, 1);
    CHECK(sloped.at("7gt002e") == 1);
    CHECK(sloped.at("7gt002g") == 2);
    CHECK(sloped.at("7gt002c") == 2);
    CHECK(mm7.rooms.hasVertex(208, 584, 80));
    CHECK(mm7.rooms.hasVertex(304, 616, 80));
    // A surface of the chest's own still takes the long sides' place.
    const BuiltMoving own = build("facing: e, kind: ch3, surface: {texture: bwood, size: [64, 64]}");
    REQUIRE(own.rooms.built);
    CHECK(texturesOfEvent(own.rooms, 1).at("bwood") == 2);
    CHECK(texturesOfEvent(own.rooms, 1).count("ch3frntb") == 0);
    CHECK(issueText(build("kind: ch9").rooms).find("there is no chest kind ch9") != std::string::npos);
    // A surface that is a kind's middle stretched over the chest is warned of.
    const BuiltPlaced warned = buildPlaced(HandleRooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "chests:\n  - {id: chest:c, room: room:a, at: [256, 600], surface: {texture: ch3frntB, size: [64, 64]}}\n", {});
    REQUIRE(warned.built);
    CHECK(std::any_of(warned.warnings.begin(), warned.warnings.end(), [](const std::string &warning)
    {
        return warning.find("Say `kind: ch3`") != std::string::npos;
    }));
}

TEST_CASE("a platform's fitted top is laid once over its underside too (P1's vents)")
{
    const BuiltPlaced built = buildPlaced("rooms:\n  - id: room:a\n    outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]]\n"
        "    floor: 0\n    ceiling: 512\n    platforms:\n"
        "      - {id: platform:vent, at: [512, 384], size: [192, 192], rise: 4, base: 40, "
        "top_surface: {texture: ventpic, fit: true}}\n",
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n", {});
    INFO(issueText(built));
    REQUIRE(built.built);
    int vents = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.textureName != "ventpic")
        {
            continue;
        }

        ++vents;
        const auto [lowU, highU] = std::minmax_element(face.textureUs.begin(), face.textureUs.end());
        const auto [lowV, highV] = std::minmax_element(face.textureVs.begin(), face.textureVs.end());
        CHECK(*highU - *lowU == 128);
        CHECK(*highV - *lowV == 128);
    }

    CHECK(vents >= 1);
}

TEST_CASE("a chest without a kind or surface is its style world's chest (Xeen on MM7's tiles: 7gt002)")
{
    const auto textures = [](const std::string &world, const std::string &tileset)
    {
        std::vector<std::pair<std::string, std::string>> tables;

        if (!tileset.empty())
        {
            tables.push_back({"../../worlds/" + world + "/world.yml", "terrainTileset: " + tileset + "\n"});
        }

        const BuiltPlaced built = buildPlaced(HandleRooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
            "chests:\n  - {id: chest:c, room: room:a, at: [256, 600], facing: e}\n", tables,
            "format: 0\nid: testmap\nworld: " + world + "\nkind: indoor\n",
            "format: 0\nevents:\n  - {id: evt:c, preset: chest, source: chest:c}\n");
        INFO(issueText(built));
        REQUIRE(built.built);
        std::set<std::string> names;

        for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
        {
            if (face.cogTriggered == 1)
            {
                names.insert(face.textureName);
            }
        }

        return names;
    };

    CHECK(textures("mm6", "").contains("ch1frntb"));
    CHECK(textures("mm8", "").contains("gt002a"));
    CHECK(textures("xeen", "mm7").contains("7gt002e"));
    CHECK(textures("hesper", "").contains("ch1frntb"));
}

TEST_CASE("what stands over a lift or a mover stands on its top as the part stands at the map's start")
{
    const std::string lifts =
        "lifts:\n  - {id: lift:up, room: room:a, at: [800, 600], size: [128, 128], travel: 128, state: up}\n"
        "movers:\n  - {id: mover:deck, room: room:a, at: [256, 600], size: [128, 128], height: 32, "
        "travel: [0, 0, 64]}\n";
    const auto build = [&lifts](const std::string &things)
    {
        return buildPlaced(HandleRooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\n" + lifts + things, {});
    };
    const BuiltPlaced built = build("spawns:\n  - {id: spawn:on_lift, room: room:a, at: [800, 600], slot: 1}\n"
        "  - {id: spawn:on_deck, room: room:a, at: [256, 600], slot: 1}\n"
        "  - {id: spawn:beside, room: room:a, at: [600, 200], slot: 1}\n");
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.map.spawns.size() == 3);
    // The lift starts raised: its top is 8 over the floor and 128 higher. The mover's top is 32 over the floor.
    CHECK(built.map.spawns[0].z == 136);
    CHECK(built.map.spawns[1].z == 32);
    CHECK(built.map.spawns[2].z == 0);
    // A chest there needs `rides`; a decoration, which never moves, is refused; under a raised lift's column there
    // is no room.
    CHECK(issueText(build("chests:\n  - {id: chest:c, room: room:a, at: [800, 600], size: [64, 48, 40]}\n"))
        .find("give the chest `rides: lift:up`") != std::string::npos);
    CHECK(issueText(build("spawns:\n  - {id: spawn:s, room: room:a, at: [800, 600], slot: 1, floor_height: 0}\n"))
        .find("lies inside lift:up as it stands at the map's start") != std::string::npos);
    // The start too stands on a moving part's top.
    const BuiltPlaced start =
        buildPlaced(HandleRooms, "format: 0\nstart: {room: room:a, at: [256, 600]}\n" + lifts, {});
    REQUIRE(start.built);
    REQUIRE(start.scene);
}

TEST_CASE("faces in one plane over each other are found as the map starts and with its moving parts moved")
{
    // Two platforms whose tops lie in one plane and overlap: the build warns, naming both and their room.
    const BuiltPlaced flush = buildPlaced(HandleRooms + std::string(
        "      - {at: [200, 200], size: [128, 128], rise: 32}\n"
        "      - {at: [264, 200], size: [128, 128], rise: 32}\n"), "format: 0\nstart: {room: room:a, at: [600, 600]}\n",
        {});
    INFO(issueText(flush));
    REQUIRE(flush.built);
    CHECK(std::any_of(flush.warnings.begin(), flush.warnings.end(), [](const std::string &warning)
    {
        return warning.find("faces in one plane: ") != std::string::npos && warning.find("room:a") != std::string::npos
            && warning.find("as the map starts") != std::string::npos;
    }));
    // A door leaf as thick as its wall stands 2 back from each face of the wall, and a leaf that rises goes 2 past its
    // lintel: open, it lies over no face of the wall (it used to flicker with the wall beside the doorway and with
    // the lintel). A leaf that slides sideways stops at its jamb as the shipped maps' do, its free edge in the jamb's
    // plane.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[528, 0], [1024, 0], [1024, 512], [528, 512]], floor: 0, ceiling: 384}\n"
        "openings:\n  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n";
    const BuiltMoving door = buildMoving(rooms,
        "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, kind: slide_up}\n");
    INFO(issueText(door.rooms));
    REQUIRE(door.rooms.built);
    const OpenYAMM::Game::MapDeltaData *pState = door.loaded.state ? &*door.loaded.state : nullptr;
    CHECK(OpenYAMM::Studio::findCoplanarFaces(*door.loaded.indoor, pState).empty());
    // The same map moved by hand into the old pose finds the pair: the leaf's face in the wall's plane.
    OpenYAMM::Game::IndoorMapData overlapping = *door.loaded.indoor;
    overlapping.faces.push_back(overlapping.faces.front());
    CHECK_FALSE(OpenYAMM::Studio::findCoplanarFaces(overlapping, pState).empty());
}

TEST_CASE("a thing on a wall lies wholly on one face of it, clear of corner strips and panels")
{
    const auto build = [](const std::string &along)
    {
        return buildPlaced(
            "rooms:\n  - id: room:a\n    outline: [[0, 0], [512, 0], [512, 512], [0, 512]]\n    floor: 0\n"
            "    ceiling: 384\n    walls:\n      - wall: e\n        ends: {length: 32, surface: {texture: edge, "
            "size: [32, 128]}}\n",
            "format: 0\nstart: {room: room:a, at: [128, 128]}\nswitches:\n  - {id: switch:s, room: room:a, wall: e, "
                + along + "}\n",
            {});
    };
    // The east wall runs north from (512, 0); its strips are 0 to 32 and 480 to 512 along it.
    CHECK(build("along: 0.5").built);
    const std::string refused = issueText(build("along: 0.95"));
    CHECK(refused.find("partly over the corner strip (`ends`) from 480 to 512") != std::string::npos);
    CHECK(refused.find("its middle at 464 or less along the wall") != std::string::npos);
    CHECK(build("along: 0.97, size: [16, 16]").built);
}

TEST_CASE("the interactive things of a built map: what each is, what it changes and where it is used from")
{
    const BuiltMoving built = buildMoving(HandleRooms,
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "lifts:\n  - {id: lift:l, room: room:a, at: [800, 600], size: [128, 128], travel: 128}\n"
        "switches:\n  - {id: switch:a_lever, room: room:a, wall: w, kind: lever}\n"
        "  - {id: switch:b_plate, room: room:a, wall: e}\n"
        "chests:\n  - {id: chest:c, room: room:a, at: [256, 600], facing: e, kind: ch3}\n",
        "format: 0\nevents:\n"
        "  - {id: evt:a, preset: switch, source: switch:a_lever, toggles: [lift:l]}\n"
        "  - {id: evt:b, preset: switch, source: switch:b_plate, opens: [lift:l]}\n"
        "  - {id: evt:c, preset: chest, source: chest:c}\n");
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // What `oymap flow` says the handlers do (door 1 is the lift, door 2 the lever's arm).
    const std::string flow =
        "[{\"event\": 1, \"title\": \"Lever\", \"paths\": [{\"effects\": [\"door 2 toggle\", \"door 1 toggle\"]}]},"
        " {\"event\": 2, \"title\": \"Switch\", \"paths\": [{\"effects\": [\"door 1 open\","
        " \"SetTexture(1, t1swdu)\"]}]},"
        " {\"event\": 3, \"title\": \"Chest\", \"paths\": [{\"effects\": [\"open chest 0\"]}]}]";
    const std::vector<OpenYAMM::Studio::InteractiveThing> things =
        OpenYAMM::Studio::listInteractiveThings(built.loaded, flow, {});
    REQUIRE(things.size() == 3);
    CHECK(things[0].kind == "lever");
    CHECK(things[0].safeToUse);
    CHECK(things[0].changes.size() == 2);
    CHECK(things[1].kind == "switch");
    CHECK(things[1].textures.at("t1swdd") == 1);
    CHECK(things[2].kind == "chest");
    CHECK_FALSE(things[2].safeToUse);
    // Each is used from the room's floor, in front of it, looking at it.
    for (const OpenYAMM::Studio::InteractiveThing &thing : things)
    {
        CHECK(thing.stand[2] == 0.0);
        CHECK(thing.stand[0] > 0.0);
        CHECK(thing.stand[0] < 1024.0);
        CHECK(thing.overlaps.empty());
    }
}

TEST_CASE("a liquid floor has the fluid bit and no lava flag: lava's look that does not burn")
{
    const BuiltPlaced built = buildPlaced(
        "rooms:\n  - id: room:a\n    outline: [[0, 0], [512, 0], [512, 512], [0, 512]]\n    floor: 0\n"
        "    ceiling: 384\n    levels:\n      - id: level:pool\n        outline: [[64, 64], [256, 64], [256, 256], "
        "[64, 256]]\n        floor: -16\n        surface: {texture: lavatyl, size: [128, 128]}\n",
        "format: 0\nstart: {room: room:a, at: [400, 400]}\n"
        "floors:\n  - {id: floor:pool, of: level:pool, kind: liquid}\n",
        {});
    INFO(issueText(built));
    REQUIRE(built.built);
    bool found = false;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.textureName == "lavatyl" && face.facetType != 0)
        {
            found = found || OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Fluid);
            CHECK_FALSE(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Lava));
        }
    }

    CHECK(found);
}

#include "core/EyeSector.h"

TEST_CASE("a walkable top whose party's eye rises through a floor hole is seen from the room below: the check says so")
{
    // A low room with a block under the hole of the room above, the block's top 112 under the hole (the eye 48 over
    // it). With a hole in the low room's own floor (a pit) the game counts the upper hole's portal as a floor of the
    // low room too and takes the low room's, the lower sector number, on the tie: the eye is drawn from there.
    const auto build = [](bool pit, double rise)
    {
        std::string rooms =
            "rooms:\n"
            "  - id: room:low\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    ceiling: 512\n"
            "    platforms:\n"
            "      - {at: [256, 512], size: [256, 256], rise: " + std::to_string(static_cast<int>(rise)) + "}\n"
            "  - {id: room:up, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 512, ceiling: 900}\n";

        if (pit)
        {
            rooms += "  - {id: room:pit, outline: [[640, 384], [896, 384], [896, 640], [640, 640]], floor: -384, "
                     "ceiling: -32}\n";
        }

        rooms += "openings:\n  - {id: open:hole, from: room:up, to: room:low, in: floor, at: [256, 512], "
                 "size: [384, 384]}\n";

        if (pit)
        {
            rooms += "  - {id: open:pit, from: room:low, to: room:pit, in: floor, at: [768, 512], size: [128, 128]}\n";
        }

        return buildPlaced(rooms, "format: 0\nstart: {room: room:up, at: [800, 800]}\n", {});
    };
    const auto eyeWarnings = [](const BuiltPlaced &built)
    {
        return std::count_if(built.warnings.begin(), built.warnings.end(),
            [](const std::string &warning) { return warning.find("eye outside its sector") != std::string::npos; });
    };
    const BuiltPlaced withPit = build(true, 400.0);
    INFO(issueText(withPit));
    REQUIRE(withPit.built);
    CHECK(eyeWarnings(withPit) == 1);
    const std::vector<OpenYAMM::Studio::EyeSectorFinding> findings =
        OpenYAMM::Studio::findEyeOutsideSector(withPit.map, nullptr);
    REQUIRE(findings.size() == 1);
    // The low room's floor, the upper room's space, drawn from the low room.
    CHECK(findings[0].eyeSector != findings[0].floorSector);
    CHECK(findings[0].drawnSector == findings[0].floorSector);
    CHECK(withPit.map.sectors[static_cast<size_t>(findings[0].eyeSector)].floorCount > 0);
    CHECK(std::abs(findings[0].foot[2] - 400.0) < 0.5);
    // Without the pit only the upper room counts the hole as a floor and the eye is drawn from it; a block whose top
    // keeps the eye under the hole is in its own room's space.
    CHECK(eyeWarnings(build(false, 400.0)) == 0);
    CHECK(eyeWarnings(build(true, 320.0)) == 0);
}

TEST_CASE("spawn points take the group the shipped records hold, which events may show, hide and make peaceful")
{
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [100, 100]}\n"
        "spawns:\n"
        "  - {id: spawn:plain, room: room:a, at: [300, 200], slot: 1}\n"
        "  - {id: spawn:bay, room: room:a, at: [400, 200], slot: 2, group: 51}\n"
        "  - {id: spawn:loot, room: room:a, at: [500, 200], kind: item, treasure_level: 3, group: 51}\n"
        "monsters:\n"
        "  - {id: monster:guard, room: room:a, monster: Swordsman, at: [256, 256], group: 54, hostile: false}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:wake, preset: script, trigger: load, effects: [{show_actors: 51}]}\n";
    const BuiltPlaced built = buildPlaced(PlacedRooms, objects, PlacedTables, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.map.spawns.size() == 3);
    std::map<std::pair<int, int>, uint32_t> groups;

    for (const OpenYAMM::Game::IndoorSpawn &spawn : built.map.spawns)
    {
        groups[{spawn.typeId, spawn.index}] = spawn.group;
    }

    CHECK(groups == std::map<std::pair<int, int>, uint32_t>{{{3, 1}, 0}, {{3, 2}, 51}, {{2, 3}, 51}});
    // An event may name a spawn point's group as it names placed monsters'.
    CHECK(built.lua.find("evt.SetMonGroupBit(51, MonsterBits.Invisible, 0)") != std::string::npos);
    // A group no monster and no monster spawn point has is refused; a spawn point in a peaceful group is warned of.
    CHECK(issueText(buildPlaced(PlacedRooms, objects, PlacedTables, CardText,
        "format: 0\nevents:\n  - {id: evt:x, preset: script, trigger: load, effects: [{hide_actors: 52}]}\n"))
        .find("no monster has group 52, nor any spawn point") != std::string::npos);
    const BuiltPlaced peaceful = buildPlaced(PlacedRooms,
        objects + "  - {id: monster:second, room: room:a, monster: 7, at: [256, 384], group: 51, hostile: false}\n",
        PlacedTables, CardText, wiring);
    REQUIRE(peaceful.built);
    CHECK(std::any_of(peaceful.warnings.begin(), peaceful.warnings.end(), [](const std::string &warning)
    {
        return warning.find("spawn point spawn:bay is in group 51") != std::string::npos;
    }));
}

TEST_CASE("a doorway's reveal from each side of its door, a leaf's edge with its own surface and coordinates, and a "
          "surface's offset")
{
    // Room a's east wall is 32 thick; the doorway's front half (x 512 to 528) takes `reveal` shifted by `offset`,
    // the half toward room b `back_reveal`; the folding leaf's free edge `edge_surface`, laid at its texel size.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[544, 128], [800, 128], [800, 384], [544, 384]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192,\n"
        "     reveal: {texture: trima, size: [64, 64], offset: [8, 4]},\n"
        "     back_reveal: {texture: trimb, size: [64, 64]}}\n";
    const BuiltMoving built = buildMoving(rooms,
        doorObjects("kind: slide_left, fold: true, edge_surface: {texture: edgea, size: [16, 128]}"), DoorWiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    const OpenYAMM::Game::IndoorMapData &map = built.rooms.map;
    size_t front = 0;
    size_t back = 0;
    size_t edges = 0;

    for (const OpenYAMM::Game::IndoorFace &face : map.faces)
    {
        int lowX = 100000;
        int highX = -100000;

        for (const uint16_t vertex : face.vertexIndices)
        {
            lowX = std::min<int>(lowX, map.vertices[vertex].x);
            highX = std::max<int>(highX, map.vertices[vertex].x);
        }

        if (face.textureName == "trima")
        {
            ++front;
            CHECK(lowX >= 512);
            CHECK(highX <= 528);
        }
        else if (face.textureName == "trimb")
        {
            ++back;
            CHECK(lowX >= 528);
            CHECK(highX <= 544);
        }
        else if (face.textureName == "edgea")
        {
            ++edges;
            // Across the leaf's 16 of thickness: one picture's width, no longer one flat texel.
            const auto [lowU, highU] = std::minmax_element(face.textureUs.begin(), face.textureUs.end());
            const auto [lowV, highV] = std::minmax_element(face.textureVs.begin(), face.textureVs.end());
            CHECK(*highU - *lowU == 16);
            CHECK(*highV - *lowV == 192);
        }
    }

    // Two jambs, the soffit and the threshold on each side of the middle; one free edge.
    CHECK(front == 4);
    CHECK(back == 4);
    CHECK(edges == 1);

    // The offset moves the front reveal's picture: a jamb's texels run from 8 (0 + 8) across the half's 16.
    bool shifted = false;

    for (const OpenYAMM::Game::IndoorFace &face : map.faces)
    {
        if (face.textureName == "trima" && face.facetType == 1)
        {
            const auto [lowU, highU] = std::minmax_element(face.textureUs.begin(), face.textureUs.end());
            const auto [lowV, highV] = std::minmax_element(face.textureVs.begin(), face.textureVs.end());
            shifted = shifted || (*lowU == 8 && *highU == 24 && *lowV == 4);
        }
    }

    CHECK(shifted);

    // What cannot be: a back reveal through a hole in a floor, edges on a leaf that only rises.
    const std::string upper =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 256, ceiling: 640}\n"
        "  - {id: room:b, outline: [[64, 64], [448, 64], [448, 448], [64, 448]], floor: -64, ceiling: 224}\n"
        "openings:\n"
        "  - {id: open:hole, from: room:a, to: room:b, in: floor, at: [256, 256], size: [128, 128],\n"
        "     back_reveal: {texture: trimb, size: [64, 64]}}\n";
    CHECK(issueText(buildRooms(upper, "format: 0\nstart: {room: room:a, at: [100, 100]}\n"))
        .find("and no `back_reveal`") != std::string::npos);
    CHECK(issueText(buildMoving(DoorRooms, doorObjects("edge_surface: {texture: edgea, size: [16, 128]}"),
        DoorWiring).rooms).find("shows no end, top or underside") != std::string::npos);
}

TEST_CASE("compare reads the texel a ray hits and the offset a rebuilt picture needs")
{
    // A wall 256 wide along x facing -y, its texture laid from x = 0 (u = x) and down from z = 256 (v = 256 - z).
    OpenYAMM::Studio::RayScene scene;
    const std::vector<std::array<double, 3>> wall = {{0.0, 100.0, 0.0}, {256.0, 100.0, 0.0}, {256.0, 100.0, 256.0},
        {0.0, 100.0, 256.0}};
    const std::vector<std::array<double, 2>> texels = {{0.0, 256.0}, {256.0, 256.0}, {256.0, 0.0}, {0.0, 0.0}};
    REQUIRE(scene.addFace(wall, {0.0, -1.0, 0.0}, 0, "w", &texels));
    scene.build();
    const OpenYAMM::Studio::RayHit hit = scene.cast({40.0, 0.0, 160.0}, {0.0, 1.0, 0.0}, 4096.0);
    REQUIRE(hit.hit);
    REQUIRE(hit.hasTexel);
    CHECK(std::abs(hit.texel[0] - 40.0) < 0.01);
    CHECK(std::abs(hit.texel[1] - 96.0) < 0.01);
    // The rebuild's picture lies 32 to the side and a whole repeat down: it needs [32, 0]; 4 apart is nothing.
    const std::optional<std::array<double, 2>> needed =
        OpenYAMM::Studio::offsetNeeded({40.0, 96.0}, {8.0, 224.0}, {128, 128});
    REQUIRE(needed);
    CHECK(std::abs((*needed)[0] - 32.0) < 0.01);
    CHECK(std::abs((*needed)[1]) < 0.01);
    CHECK_FALSE(OpenYAMM::Studio::offsetNeeded({40.0, 96.0}, {36.0, 96.0}, {128, 128}));
    // Across the wrap: 120 against 8 is 16 apart the short way.
    const std::optional<std::array<double, 2>> wrapped =
        OpenYAMM::Studio::offsetNeeded({8.0, 0.0}, {120.0, 0.0}, {128, 128});
    REQUIRE(wrapped);
    CHECK(std::abs((*wrapped)[0] - 16.0) < 0.01);
}

TEST_CASE("what the player sees: things in the air, squashed pictures, chests named and looking as chests, clicked "
          "things with a name, signs in a window, MM6's plate in another world")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 512\n"
        "    platforms:\n"
        "      - {at: [512, 512], size: [128, 128], rise: 64, base: 200, surface: {texture: gt001a, size: [64, 64]}}\n"
        "      - {at: [256, 768], size: [96, 64], rise: 40, surface: {texture: gt002c, size: [64, 64]}}\n"
        "      - {at: [768, 768], size: [128, 128], rise: 64}\n"
        "    walls:\n"
        "      - wall: n\n"
        "        panels:\n"
        "          - {id: panel:notice, offset: 400, length: 96, bottom: 96, height: 128, surface: {texture: sign, "
        "size: [64, 128], fit: true}}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "chests:\n"
        "  - {id: chest:desk, room: room:a, at: [512, 200], size: [224, 96, 72], surface: {texture: t1cab, "
        "size: [128, 256], fit: true}}\n"
        "switches:\n  - {id: switch:s, room: room:a, wall: e}\n"
        "decorations:\n"
        "  - {id: deco:air, room: room:a, decoration: bucket, at: [300, 300], height: 200}\n"
        "  - {id: deco:on_block, room: room:a, decoration: bucket, at: [540, 200], height: 72}\n"
        "  - {id: deco:lamp, room: room:a, decoration: lamp, at: [600, 600], height: 300}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:desk, preset: chest, source: chest:desk, title: \"Joe's desk\"}\n"
        "  - {id: evt:notice, preset: text, source: panel:notice, text: KEEP OUT, title: Sign}\n"
        "  - {id: evt:note, preset: text, source: deco:on_block, text: A note}\n"
        "  - {id: evt:switch, preset: switch, source: switch:s}\n";
    const std::vector<std::pair<std::string, std::string>> tables = {
        {"decoration_data.txt",
            "Decoration Data\t\t\tDescriptor\n"
            "#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\tSoundId\t"
            "Flags\tSpriteId\n\n"
            "1\tnull\tnull\t0\t8\t8\t0\t0\t0\t0\t0\t0\t0\n"
            "148\tBucket\tbucket\t0\t29\t40\t0\t0\t0\t0\t0\t0\t17880\n"
            "238\tlamp\tlantern\t0\t16\t180\t0\t0\t0\t0\t0\t0\t190\n"}};
    const std::string card = "format: 0\nid: testmap\nworld: mm7\nkind: indoor\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, tables, card, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    const auto warned = [&built](const std::string &text)
    {
        return std::count_if(built.warnings.begin(), built.warnings.end(),
            [&text](const std::string &warning) { return warning.find(text) != std::string::npos; });
    };
    // (a) The bucket in the air; not the one on the desk, not the lantern (it hangs by its kind); the block 200 up.
    CHECK(warned("deco:air (bucket) in room:a stands 200 over the floor") == 1);
    CHECK(warned("deco:on_block (bucket)") == 0);
    CHECK(warned("deco:lamp") == 0);
    CHECK(warned("rests on nothing over most of its footprint") == 1);
    // (b) The desk's front squashes the cabinet's drawers (0.57 across against 3.56 down).
    CHECK(warned("the picture t1cab on TRIGGER_desk is squashed") == 1);
    // (c) A chest named for whom it belongs to, not as what opens; a block wearing a chest's picture.
    CHECK(warned("and the player reads \"Joe's desk\" on it: nothing says it opens") == 1);
    CHECK(warned("wears gt002c, a chest's picture, and does not open") == 1);
    // (d, e) The plain switch gets the shipped default name; the notice, titled a sign, shows in a window; a note
    // without a name is warned of and its short line stays in the status bar.
    CHECK(built.lua.find("evt.SimpleMessage(\"KEEP OUT\")") != std::string::npos);
    CHECK(built.lua.find("evt.StatusText(\"A note\")") != std::string::npos);
    CHECK(warned("is clicked on deco:on_block and has no `title`") == 1);
    CHECK(built.lua.find(", \"Switch\")") != std::string::npos);
    // (f) MM6's plate in an MM7 dungeon.
    CHECK(warned("are MM6's: this dungeon is mm7's") == 1);
}

TEST_CASE("D7: a dungeon monster's `leash` and a decoration of the project's world's own table")
{
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [100, 100]}\n"
        "monsters:\n"
        "  - {id: monster:dragon, room: room:a, monster: 1, at: [256, 256], leash: 1024}\n"
        "  - {id: monster:free, room: room:a, monster: 1, at: [512, 384]}\n"
        "decorations:\n"
        "  - {id: deco:lamp, room: room:a, decoration: xw_lamp, at: [400, 100]}\n";
    std::vector<std::pair<std::string, std::string>> tables = PlacedTables;
    tables.push_back({"decoration_data.txt",
        "Decoration Data\t\t\tDescriptor\n"
        "#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\tSoundId\t"
        "Flags\tSpriteId\n\n"
        "1\tnull\tnull\t0\t8\t8\t0\t0\t0\t0\t0\t0\t0\n"});
    tables.push_back({"../../worlds/xw/world.yml",
        "id: xw\ntableContributions:\n"
        "  - {table: decorations, idDomain: decorations, mode: append, path: models/decoration_data.txt}\n"});
    tables.push_back({"../../worlds/xw/models/decoration_data.txt",
        "4021\txw_lamp\tgenie lamp\t0\t20\t23\t0\t0\t0\t0\t0\t0\t0\n"});
    const std::string card = "format: 0\nid: testmap\nworld: xw\nkind: indoor\n";
    const BuiltPlaced built = buildPlaced(PlacedRooms, objects, tables, card);
    INFO(issueText(built));
    REQUIRE(built.built);
    const std::vector<OpenYAMM::Game::MapDeltaActor> &actors = built.scene->initialState.actors;
    REQUIRE(actors.size() == 2);
    CHECK(actors[0].leashRadius == 1024);
    CHECK_FALSE(actors[0].immobile);
    CHECK(actors[1].leashRadius == 0);
    // The world's row 4021: the BLV stores the row less one.
    const std::vector<OpenYAMM::Game::IndoorEntity> &entities = built.map.entities;
    CHECK(std::count_if(entities.begin(), entities.end(),
        [](const OpenYAMM::Game::IndoorEntity &entity) { return entity.decorationListId == 4020; }) == 1);

    // A leash and `immobile` together hold the monster two ways: refused.
    const std::string both =
        "format: 0\nstart: {room: room:a, at: [100, 100]}\n"
        "monsters:\n"
        "  - {id: monster:dragon, room: room:a, monster: 1, at: [256, 256], leash: 1024, immobile: true}\n";
    const BuiltPlaced refused = buildPlaced(PlacedRooms, both, tables, card);
    CHECK_FALSE(refused.built);
    CHECK(issueText(refused).find("`leash` and `immobile` both hold the monster") != std::string::npos);
}

TEST_CASE("a chest's other lid, a platform's top changed alone, a decoration's picture by its id, a secret panel")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    platforms:\n"
        "      - {id: platform:podium, at: [768, 768], size: [128, 64], rise: 96, surface: {texture: deskside, "
        "size: [64, 64]}, top_surface: {texture: desktop, size: [128, 128]}}\n"
        "    walls:\n"
        "      - wall: n\n"
        "        panels:\n"
        "          - {id: panel:rock, offset: 300, length: 128, bottom: 32, height: 96, secret: true, surface: "
        "{texture: rock, size: [64, 64]}}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "chests:\n  - {id: chest:carved, room: room:a, at: [400, 400], kind: ch3, lid: v}\n"
        "decorations:\n"
        "  - {id: deco:first, room: room:a, decoration: smlbarel, at: [200, 600]}\n"
        "  - {id: deco:crystal, room: room:a, decoration: smlbarel, at: [300, 600]}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:podium, preset: script, source: platform:podium, title: Podium,\n"
        "     effects: [{set_texture: {of: platform:podium, to: deskside, face: top}},\n"
        "               {set_sprite: {of: deco:crystal, to: crysdisc}}]}\n";
    const std::vector<std::pair<std::string, std::string>> tables = {
        {"decoration_data.txt",
            "Decoration Data\t\t\tDescriptor\n"
            "#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\tSoundId\t"
            "Flags\tSpriteId\n\n"
            "1\tnull\tnull\t0\t8\t8\t0\t0\t0\t0\t0\t0\t0\n"
            "157\tsmlbarel\tkeg\t0\t30\t40\t0\t0\t0\t0\t0\t0\t17789\n"}};
    const BuiltPlaced built = buildPlaced(rooms, objects, tables, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    std::map<std::string, int> textures;
    int topCog = -1;
    int sideCog = -1;
    bool secret = false;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        ++textures[face.textureName];

        if (face.textureName == "desktop")
        {
            topCog = face.cogNumber;
        }

        if (face.textureName == "deskside")
        {
            sideCog = face.cogNumber;
        }

        if (face.textureName == "rock")
        {
            secret = secret
                || OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::IsSecret);
        }
    }

    // MM6's carved lid in the middle, its ends with it.
    CHECK(textures["ch3tpbv"] == 1);
    CHECK(textures["ch3tplev"] == 1);
    CHECK(textures["ch3tprev"] == 1);
    CHECK(textures["ch3topb"] == 0);
    // The podium's top alone carries the cog the effect names; its sides none.
    CHECK(topCog > 0);
    CHECK(sideCog == 0);
    CHECK(built.lua.find("evt.SetTexture(" + std::to_string(topCog) + ", \"deskside\")") != std::string::npos);
    // The crystal is the map's second decoration: entity 1.
    CHECK(built.lua.find("evt.SetSprite(1, 1, \"crysdisc\")") != std::string::npos);
    CHECK(secret);
    // What cannot be: a lid of a kind that has none, a face other than the top, a sprite of no decoration.
    CHECK(issueText(buildPlaced(rooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\nchests:\n"
        "  - {id: chest:c, room: room:a, at: [400, 400], kind: ch5, lid: v}\n", tables, CardText))
        .find("ch5 has none") != std::string::npos);
    CHECK(issueText(buildPlaced(rooms, objects, tables, CardText, "format: 0\nevents:\n"
        "  - {id: evt:x, preset: script, trigger: load, effects: [{set_sprite: {of: deco:none, to: crysdisc}}]}\n"))
        .find("there is no decoration deco:none") != std::string::npos);
}

TEST_CASE("F65: a clicked block's top built apart (its texture changed alone, a water floor) keeps the click")
{
    // XD-23's fire pit (`set_texture` on its top) and XD-02's pools (a water floor on the basin's top): the top is a
    // node of its own, and was built without the block's event, so only the rim clicked.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    platforms:\n"
        "      - {id: platform:pit, at: [256, 768], size: [128, 128], rise: 24, surface: {texture: pitside, "
        "size: [64, 64]}, top_surface: {texture: pittop, size: [128, 128]}}\n"
        "      - {id: platform:pool, at: [768, 768], size: [128, 128], rise: 28, surface: {texture: poolside, "
        "size: [64, 64]}, top_surface: {texture: pooltop, size: [128, 128]}}\n"
        "      - {id: platform:step, at: [768, 256], size: [128, 128], rise: 28, surface: {texture: stepside, "
        "size: [64, 64]}, top_surface: {texture: steptop, size: [128, 128]}}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "floors:\n"
        "  - {id: floor:pool, of: platform:pool, kind: water}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:pit, preset: script, source: platform:pit, title: Fire pit,\n"
        "     effects: [{set_texture: {of: platform:pit, to: pitside, face: top}}]}\n"
        "  - {id: evt:pool, preset: text, source: platform:pool, text: Cold.}\n"
        "  - {id: evt:stepon, preset: text, trigger: step, source: platform:step, text: Wet.}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    const uint32_t clickable = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Clickable);
    std::map<std::string, std::set<int>> events;
    std::map<std::string, bool> clicked;
    std::map<std::string, bool> water;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        events[face.textureName].insert(face.cogTriggered);
        clicked[face.textureName] = clicked[face.textureName] || (face.attributes & clickable) != 0;
        water[face.textureName] = water[face.textureName]
            || OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Fluid);
    }

    // The pit: sides and top run one event, and the top keeps its own cog for the texture change.
    REQUIRE(events.contains("pittop"));
    CHECK(events["pittop"].size() == 1);
    CHECK(*events["pittop"].begin() > 0);
    CHECK(events["pittop"] == events["pitside"]);
    CHECK(clicked["pittop"]);
    // The pool: its water top clicked as the basin, and still water.
    CHECK(events["pooltop"] == events["poolside"]);
    CHECK(*events["pooltop"].begin() > 0);
    CHECK(clicked["pooltop"]);
    CHECK(water["pooltop"]);
    // A platform that runs a step event (one object, one event): its top is walked onto, not clicked.
    CHECK(*events["steptop"].begin() > 0);
    CHECK_FALSE(clicked["steptop"]);
}

TEST_CASE("DD-13: a decoration with `hidden: true` starts away, and `show`/`hide` with its id bring it and take it")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "decorations:\n"
        "  - {id: deco:first, room: room:a, decoration: smlbarel, at: [200, 600]}\n"
        "  - {id: deco:heap, room: room:a, decoration: smlbarel, at: [600, 600], hidden: true}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:burn, preset: script, source: deco:first, title: Fire, effects: [{show: deco:heap}, "
        "{hide: deco:first}]}\n";
    const std::vector<std::pair<std::string, std::string>> tables = {
        {"decoration_data.txt",
            "Decoration Data\t\t\tDescriptor\n"
            "#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\tSoundId\t"
            "Flags\tSpriteId\n\n"
            "1\tnull\tnull\t0\t8\t8\t0\t0\t0\t0\t0\t0\t0\n"
            "157\tsmlbarel\tkeg\t0\t30\t40\t0\t0\t0\t0\t0\t0\t17789\n"}};
    const BuiltPlaced built = buildPlaced(rooms, objects, tables, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.map.entities.size() >= 2);
    // The heap is entity 1: the map's invisible flag on it, the first decoration without.
    size_t heap = built.map.entities.size();
    size_t first = built.map.entities.size();

    for (size_t index = 0; index < built.map.entities.size(); ++index)
    {
        if (built.map.entities[index].name == "heap")
        {
            heap = index;
        }

        if (built.map.entities[index].name == "first")
        {
            first = index;
        }
    }

    REQUIRE(heap == 1);
    REQUIRE(first == 0);
    CHECK(built.map.entities[heap].aiAttributes == 0x20);
    CHECK(built.map.entities[first].aiAttributes == 0);
    REQUIRE(built.scene);
    REQUIRE(built.scene->initialState.decorationFlags.size() == 1);
    CHECK(built.scene->initialState.decorationFlags[0].entityIndex == 1);
    CHECK(built.scene->initialState.decorationFlags[0].flag == 0x20);
    CHECK(built.lua.find("evt.SetSprite(1, 1)") != std::string::npos);
    CHECK(built.lua.find("evt.SetSprite(0, 0)") != std::string::npos);
}

TEST_CASE("P5: a chest with `hidden: true` starts away, and `show`/`hide` with its id bring it and take it whole")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "chests:\n"
        "  - {id: chest:gift, room: room:a, at: [600, 600], hidden: true, gold: 100}\n"
        "  - {id: chest:plain, room: room:a, at: [300, 600], gold: 5}\n"
        "plates:\n  - {id: plate:step, room: room:a, at: [512, 300], size: [64, 64]}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:gift, preset: chest, source: chest:gift}\n"
        "  - {id: evt:plain, preset: chest, source: chest:plain}\n"
        "  - {id: evt:step, preset: script, trigger: step, source: plate:step,\n"
        "     effects: [{show: chest:gift}, {hide: chest:plain}]}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    const uint32_t invisible = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible);
    const uint32_t untouchable = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Untouchable);
    // Each chest's faces (above the floor, within its footprint) and the flags and cogs they carry.
    const auto chestFaces = [&built, invisible, untouchable](double x)
    {
        std::set<std::pair<uint32_t, uint32_t>> flagsAndCogs;

        for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
        {
            bool inChest = !face.isPortal;
            bool raised = false;

            for (const uint16_t vertex : face.vertexIndices)
            {
                const OpenYAMM::Game::IndoorVertex &point = built.map.vertices[vertex];
                inChest = inChest && std::abs(point.x - x) <= 64 && std::abs(point.y - 600) <= 64 && point.z >= 0
                    && point.z <= 100;
                raised = raised || point.z > 0;
            }

            if (inChest && raised)
            {
                flagsAndCogs.insert({face.attributes & (invisible | untouchable), face.cogNumber});
            }
        }

        return flagsAndCogs;
    };
    const std::set<std::pair<uint32_t, uint32_t>> gift = chestFaces(600);
    const std::set<std::pair<uint32_t, uint32_t>> plain = chestFaces(300);
    REQUIRE(gift.size() == 1);
    REQUIRE(plain.size() == 1);
    CHECK(gift.begin()->first == (invisible | untouchable));
    CHECK(plain.begin()->first == 0);
    const std::string giftCog = std::to_string(gift.begin()->second);
    const std::string plainCog = std::to_string(plain.begin()->second);
    CHECK(gift.begin()->second > 0);
    CHECK(plain.begin()->second > 0);
    CHECK(built.lua.find("evt.SetFacetBit(" + giftCog + ", FaceAttribute.Invisible, 0)") != std::string::npos);
    CHECK(built.lua.find("evt.SetFacetBit(" + giftCog + ", FaceAttribute.Untouchable, 0)") != std::string::npos);
    CHECK(built.lua.find("evt.SetFacetBit(" + plainCog + ", FaceAttribute.Invisible, 1)") != std::string::npos);
    CHECK(built.lua.find("evt.SetFacetBit(" + plainCog + ", FaceAttribute.Untouchable, 1)") != std::string::npos);
    CHECK(built.lua.find("evt.OpenChest(") != std::string::npos);

    // A hidden chest no event shows is warned of.
    const BuiltPlaced unshown = buildPlaced(rooms, objects, {}, CardText,
        "format: 0\nevents:\n  - {id: evt:gift, preset: chest, source: chest:gift}\n");
    REQUIRE(unshown.built);
    CHECK(std::any_of(unshown.warnings.begin(), unshown.warnings.end(), [](const std::string &warning)
    {
        return warning.find("chest:gift starts hidden") != std::string::npos;
    }));
}

TEST_CASE("XD-19, DD-16: a `trigger: monster_damage` event is the map's damage hook, for its monsters only")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:corak, preset: script, trigger: monster_damage, monsters: [11690, 11691], "
        "effects: [{set_damage: 0}]}\n"
        "  - {id: evt:xeen, preset: script, trigger: monster_damage, monsters: [11634], effects: [{lua: "
        "\"if not (hook.attack == 'melee' and hook.weaponItemId == 12500) then evt.SetHookDamage(0) end\"}]}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(built.lua.find("RegisterMonsterDamageHook(") != std::string::npos);
    CHECK(built.lua.find("local monsters = {[11690] = true, [11691] = true}") != std::string::npos);
    CHECK(built.lua.find("if not monsters[hook.monsterId] then return end") != std::string::npos);
    CHECK(built.lua.find("evt.SetHookDamage(0)") != std::string::npos);
    CHECK(built.lua.find("hook.weaponItemId == 12500") != std::string::npos);
    CHECK(built.lua.find("RegisterEvent(") == std::string::npos);
    // A hook naming a placed monster acts on its actor index (the scene's actors in objects.yml's order).
    const std::string placedObjects = objects + "monsters:\n"
        "  - {id: monster:guard, room: room:a, at: [600, 600], monster: 1}\n"
        "  - {id: monster:xeen, room: room:a, at: [700, 700], monster: 2}\n";
    const BuiltPlaced placed = buildPlaced(rooms, placedObjects, PlacedTables, CardText, "format: 0\nevents:\n"
        "  - {id: evt:xeen, preset: script, trigger: monster_damage, actors: [monster:xeen], "
        "effects: [{set_damage: 0}]}\n");
    INFO(issueText(placed));
    CHECK(placed.lua.find("local actors = {[1] = true}") != std::string::npos);
    CHECK(placed.lua.find("if not actors[hook.actorIndex] then return end") != std::string::npos);
    // A hook has no source, and `monsters` belongs to a hook alone.
    CHECK(issueText(buildPlaced(rooms, objects, {}, CardText, "format: 0\nevents:\n"
        "  - {id: evt:x, preset: script, trigger: load, monsters: [1], effects: [{set_damage: 0}]}\n"))
        .find("`monsters` belongs to a damage hook") != std::string::npos);
}

TEST_CASE("DD-13: a door in a hole of a floor is a trapdoor that turns down about its hinge side, or up")
{
    // The floor-hole rooms above: the hole x 160-352, y 256-512 in a floor 32 thick (256 over the ceiling at 224).
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]], floor: 256, ceiling: 640}\n"
        "  - {id: room:b, outline: [[64, 64], [448, 64], [448, 704], [64, 704]], floor: -64, ceiling: 224}\n"
        "openings:\n"
        "  - {id: open:hole, from: room:a, to: room:b, in: floor, at: [256, 384], size: [192, 256]}\n";
    const std::string wiring = "format: 0\nevents:\n  - {id: evt:trap, preset: door, source: door:trap}\n";
    const auto trapdoor = [&rooms, &wiring](const std::string &fields)
    {
        return buildMoving(rooms, "format: 0\nstart: {room: room:a, at: [512, 64]}\ndoors:\n  - {id: door:trap, "
            "opening: open:hole, " + fields + "}\n", wiring);
    };
    const BuiltMoving down = trapdoor("hinge: west, surface: {texture: trapd, size: [64, 64]}");
    INFO(issueText(down.rooms));
    REQUIRE(down.rooms.built);
    REQUIRE(down.doors.size() == 1);
    const YAML::Node rotation = down.door(1)["mover"]["rotation"];
    REQUIRE(rotation.IsMap());
    // The hinge line along the west side at the leaf's underside (16 under the floor); the axis turns the free east
    // side down; the same way for whoever opens it.
    CHECK(rotation["pivot"][0].as<double>() == doctest::Approx(160.0));
    CHECK(rotation["pivot"][1].as<double>() == doctest::Approx(384.0));
    CHECK(rotation["pivot"][2].as<double>() == doctest::Approx(240.0));
    CHECK(rotation["axis"][0].as<double>() == doctest::Approx(0.0));
    CHECK(rotation["axis"][1].as<double>() == doctest::Approx(1.0));
    CHECK(rotation["axis"][2].as<double>() == doctest::Approx(0.0));
    CHECK(rotation["open_degrees"].as<double>() == doctest::Approx(90.0));
    CHECK_FALSE(rotation["open_away"].as<bool>());
    CHECK(down.door(1)["move_length"].as<int>() == 900);
    CHECK(down.lua.find("evt.SetDoorState(1, DoorAction.Trigger)") != std::string::npos);
    // The leaf: its top lies flush with the upper floor, over the whole hole, with the trapdoor's picture once.
    size_t tops = 0;

    for (const OpenYAMM::Game::IndoorFace &face : down.loaded.indoor->faces)
    {
        if (face.textureName == "trapd" && down.rooms.heights(face) == std::array<int, 2>{256, 256})
        {
            ++tops;
        }
    }

    CHECK(tops >= 1);

    // Up into the room above: about the top's edge on the east side.
    const BuiltMoving up = trapdoor("hinge: east, swing: -90");
    INFO(issueText(up.rooms));
    REQUIRE(up.rooms.built);
    const YAML::Node upRotation = up.door(1)["mover"]["rotation"];
    CHECK(upRotation["pivot"][0].as<double>() == doctest::Approx(352.0));
    CHECK(upRotation["pivot"][2].as<double>() == doctest::Approx(256.0));
    CHECK(upRotation["axis"][1].as<double>() == doctest::Approx(-1.0));
    CHECK(upRotation["open_degrees"].as<double>() == doctest::Approx(-90.0));

    // Sliding words, a leaf thicker than the floor and a swing past 120 are refused.
    CHECK(issueText(trapdoor("hinge: west, travel: 64").rooms).find("for doors in walls") != std::string::npos);
    CHECK(issueText(trapdoor("hinge: west, thickness: 48").rooms).find("only 32 thick") != std::string::npos);
    CHECK(issueText(trapdoor("hinge: west, swing: 170").rooms).find("1 to 120 degrees") != std::string::npos);
}

TEST_CASE("FD-01: a mover with `turn` is the scene's rotating mover, its parts with it, and stays in its room")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 512}\n";
    const std::string wiring =
        "format: 0\nevents:\n  - {id: evt:lever, preset: switch, source: mover:arm, opens: [mover:arm]}\n";
    const auto lever = [&rooms, &wiring](const std::string &fields)
    {
        return buildMoving(rooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\nmovers:\n  - {id: mover:arm, "
            "room: room:a, at: [512, 512], size: [32, 32], bottom: 248, height: 176, " + fields + "}\n", wiring);
    };
    // The arm stands up from its pivot with the grip on its top and is thrown over to hang down.
    const BuiltMoving thrown = lever("turn: {pivot: [512, 512, 248], axis: x, degrees: 180}, speed: 180, "
        "parts: [{at: [512, 512], size: [48, 48], height: 48}]");
    INFO(issueText(thrown.rooms));
    REQUIRE(thrown.rooms.built);
    REQUIRE(thrown.doors.size() == 1);
    const YAML::Node door = thrown.door(1);
    const YAML::Node rotation = door["mover"]["rotation"];
    REQUIRE(rotation.IsMap());
    CHECK(rotation["pivot"][0].as<double>() == doctest::Approx(512.0));
    CHECK(rotation["pivot"][1].as<double>() == doctest::Approx(512.0));
    CHECK(rotation["pivot"][2].as<double>() == doctest::Approx(248.0));
    CHECK(rotation["axis"][0].as<double>() == doctest::Approx(1.0));
    CHECK(rotation["axis"][1].as<double>() == doctest::Approx(0.0));
    CHECK(rotation["axis"][2].as<double>() == doctest::Approx(0.0));
    CHECK(rotation["open_degrees"].as<double>() == doctest::Approx(180.0));
    CHECK_FALSE(rotation["open_away"].as<bool>());
    CHECK(door["move_length"].as<int>() == 1800);
    CHECK(door["open_speed"].as<int>() == 1800);
    CHECK(door["direction"][2].as<int>() == 0);
    CHECK_FALSE(door["mover"]["carry"].IsDefined());
    // The record's pose is the drawn one (the start): arm and grip from 248 up to 472.
    int lowest = 1 << 20;
    int highest = -(1 << 20);

    for (const YAML::Node &z : door["z_offsets"])
    {
        lowest = std::min(lowest, z.as<int>());
        highest = std::max(highest, z.as<int>());
    }

    CHECK(lowest == 248);
    CHECK(highest == 472);
    // The game's own scene parser takes the record (it checks the rotating mover's numbers).
    REQUIRE(thrown.loaded.indoorScene.has_value());

    // Turned half over about a pivot at 400, the arm's foot comes to 552, above the ceiling (512); `travel` with
    // `turn`, a turn without its axis, and a ride on a turning mover are refused.
    CHECK(issueText(lever("turn: {pivot: [512, 512, 400], axis: x, degrees: 180}").rooms)
              .find("above the ceiling of room:a") != std::string::npos);
    CHECK(issueText(lever("turn: {pivot: [512, 512, 248], axis: x, degrees: 180}, travel: [0, 0, 8]").rooms)
              .find("not both") != std::string::npos);
    CHECK_FALSE(lever("turn: {pivot: [512, 512, 248], degrees: 90}").rooms.built);
    // Upright about z: a quarter turn of the arm stays in the room.
    CHECK(lever("turn: {pivot: [496, 496, 248], axis: z, degrees: -90}").rooms.built);
}

TEST_CASE("DD-16: a ladder through a hole in a floor stands at least 10 inside the hole's edge")
{
    // The hole x 160-352, y 256-512 in the floor of room:a (256) over room:b (ceiling 224).
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]], floor: 256, ceiling: 640}\n"
        "  - {id: room:b, outline: [[64, 64], [448, 64], [448, 704], [64, 704]], floor: -64, ceiling: 224}\n"
        "openings:\n"
        "  - {id: open:hole, from: room:a, to: room:b, in: floor, at: [256, 384], size: [192, 256]}\n";
    const auto warned = [&rooms](const std::string &at)
    {
        const BuiltPlaced built = buildPlaced(rooms, "format: 0\nstart: {room: room:a, at: [512, 64]}\nladders:\n"
            "  - {id: ladder:hatch, room: room:b, at: " + at + ", facing: n, height: 320}\n", {});
        INFO(issueText(built));
        REQUIRE(built.built);
        return std::any_of(built.warnings.begin(), built.warnings.end(), [](const std::string &warning)
        {
            return warning.find("ladder:hatch climbs through open:hole") != std::string::npos;
        });
    };
    // 4 outside the north edge, 6 inside it, 22 inside; a ladder 64 wide 8 from the east edge.
    CHECK(warned("[256, 516]"));
    CHECK(warned("[256, 506]"));
    CHECK_FALSE(warned("[256, 490]"));
    CHECK(warned("[312, 490], width: 64"));
}

TEST_CASE("DD-06: a wall panel over part of a doorway, or a picture meant once over a whole one, warns")
{
    // Room a's east wall (wall 1, 0 to 512 along it) has open:ab from 192 to 320, 0 to 128 high.
    const auto warned = [](const std::string &panel)
    {
        const std::string rooms =
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 512], [0, 512]]\n"
            "    floor: 0\n"
            "    ceiling: 384\n"
            "    walls: [{wall: east, panels: [" + panel + "]}]\n"
            "  - {id: room:b, outline: [[1056, 128], [1312, 128], [1312, 384], [1056, 384]], floor: 0, ceiling: 160}\n"
            "openings:\n"
            "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 128}\n";
        const BuiltPlaced built = buildPlaced(rooms, "format: 0\nstart: {room: room:a, at: [100, 100]}\n", {});
        INFO(issueText(built));
        REQUIRE(built.built);
        return std::any_of(built.warnings.begin(), built.warnings.end(), [](const std::string &warning)
        {
            return warning.find("of open:ab in wall 1 of room:a") != std::string::npos;
        });
    };
    CHECK(warned("{id: panel:gong, offset: 256, length: 128, bottom: 64, height: 96, "
        "surface: {texture: gong, size: [128, 96], fit: true}}"));
    CHECK_FALSE(warned("{offset: 336, length: 128, surface: {texture: gong, size: [128, 96]}}"));
    CHECK_FALSE(warned("{offset: 256, length: 128, bottom: 160, height: 96, surface: {texture: gong, size: [128, 96]}}"));
    CHECK_FALSE(warned("{offset: 0, length: 512, surface: {texture: hall, size: [128, 128]}}"));
    CHECK(warned("{offset: 0, length: 512, surface: {texture: hall, size: [128, 128], fit: true}}"));
}

TEST_CASE("DD-13: a covering wall panel stands 2 in front of the wall, which is built whole behind it")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384,\n"
        "     walls: [{wall: 0, panels: [{id: panel:hide, offset: 256, length: 256, bottom: 64, height: 192,\n"
        "       cover: true, surface: {texture: hide, size: [128, 128]}},\n"
        "      {offset: 640, length: 128, surface: {texture: pan, size: [64, 64]}}]}]}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [512, 512]}\n"
        "destructibles:\n  - {id: destructible:hide, of: panel:hide, hp: 5, material: wood}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {});
    INFO(issueText(built));
    REQUIRE(built.built);
    // Wall 0 runs along y = 0 and the room lies north of it. The hide's faces stand at y = 2; the wall goes on at
    // y = 0 behind them (its faces cover x 256-512 between 64 and 256); a plain panel is cut into the wall.
    size_t hideFaces = 0;
    size_t wallBehind = 0;
    size_t plainPanel = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        int minX = 1 << 20;
        int maxX = -(1 << 20);
        int minY = 1 << 20;
        int maxY = -(1 << 20);

        for (const uint16_t vertexId : face.vertexIndices)
        {
            const OpenYAMM::Game::IndoorVertex &vertex = built.map.vertices[vertexId];
            minX = std::min(minX, int(vertex.x));
            maxX = std::max(maxX, int(vertex.x));
            minY = std::min(minY, int(vertex.y));
            maxY = std::max(maxY, int(vertex.y));
        }

        if (face.textureName == "hide")
        {
            ++hideFaces;
            CHECK(minY == 2);
            CHECK(maxY == 2);
        }
        else if (face.textureName == "wall" && maxY == 0 && minX < 384 && maxX > 384)
        {
            ++wallBehind;
        }
        else if (face.textureName == "pan")
        {
            ++plainPanel;
            CHECK(maxY == 0);
        }
    }

    CHECK(hideFaces >= 1);
    CHECK(wallBehind >= 1);
    CHECK(plainPanel >= 1);
    // Without an id it cannot be a part of its own.
    std::string anonymous = rooms;
    anonymous.replace(anonymous.find("id: panel:hide, "), 16, "");
    CHECK(issueText(buildPlaced(anonymous, "format: 0\nstart: {room: room:a, at: [512, 512]}\n", {}))
        .find("a covering panel needs an `id`") != std::string::npos);
}

TEST_CASE("DD-13: a covering panel may stand in front of another panel, which stays whole behind it")
{
    // The hall wall is one whole-wall panel (the burn's set_texture target); the hide covers part of it.
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384,\n"
        "     walls: [{wall: 0, panels: [{id: panel:hall, offset: 0, length: 1024,\n"
        "       surface: {texture: hall, size: [128, 128]}},\n"
        "      {id: panel:hide, offset: 256, length: 256, bottom: 64, height: 192, cover: true,\n"
        "       surface: {texture: hide, size: [128, 128]}}]}]}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [512, 512]}\n"
        "destructibles:\n  - {id: destructible:hide, of: panel:hide, hp: 5, material: wood}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {});
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(issueText(built).find("overlaps another") == std::string::npos);
    size_t hideFaces = 0;
    size_t hallBehind = 0;
    size_t wallFaces = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        int minX = 1 << 20;
        int maxX = -(1 << 20);
        int minY = 1 << 20;
        int maxY = -(1 << 20);

        for (const uint16_t vertexId : face.vertexIndices)
        {
            const OpenYAMM::Game::IndoorVertex &vertex = built.map.vertices[vertexId];
            minX = std::min(minX, int(vertex.x));
            maxX = std::max(maxX, int(vertex.x));
            minY = std::min(minY, int(vertex.y));
            maxY = std::max(maxY, int(vertex.y));
        }

        if (face.textureName == "hide")
        {
            ++hideFaces;
            CHECK(minY == 2);
            CHECK(maxY == 2);
        }
        else if (face.textureName == "hall" && maxY == 0 && minX < 384 && maxX > 384)
        {
            ++hallBehind;
        }
        else if (face.textureName == "wall" && maxY == 0 && minY == 0 && maxX > minX)
        {
            ++wallFaces;
        }
    }

    CHECK(hideFaces >= 1);
    CHECK(hallBehind >= 1);
    // The hall panel takes the whole wall: no bare wall shows on it, behind the hide either.
    CHECK(wallFaces == 0);
    // Two covers may not share wall.
    std::string twoCovers = rooms;
    twoCovers.replace(twoCovers.find("surface: {texture: hall"), 0, "cover: true, ");
    CHECK(issueText(buildPlaced(twoCovers, objects, {})).find("overlaps another") != std::string::npos);
}

TEST_CASE("an indoor monster with `npc` talks as that NPC, and wiring Lua names a placed monster by ActorIndex")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "switches:\n  - {id: switch:call, room: room:a, wall: north}\n"
        "monsters:\n"
        "  - {id: monster:guard, room: room:a, monster: 1, at: [300, 600]}\n"
        "  - {id: monster:lacey, room: room:a, monster: 1, at: [700, 600], npc: 5320, immobile: true}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:call, preset: script, source: switch:call, title: Call,\n"
        "     effects: [{lua: \"evt.SetActorTarget(ActorIndex(\\\"monster:lacey\\\"), 0)\"}]}\n";
    const std::vector<std::pair<std::string, std::string>> &tables = PlacedTables;
    const BuiltPlaced built = buildPlaced(rooms, objects, tables, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.scene->initialState.actors.size() == 2);
    CHECK(built.scene->initialState.actors[0].npcId == 0);
    CHECK(built.scene->initialState.actors[1].npcId == 5320);
    CHECK(built.lua.find("evt.SetActorTarget(1, 0)") != std::string::npos);
    // A monster the project does not place.
    std::string wrong = wiring;
    wrong.replace(wrong.find("monster:lacey"), 13, "monster:stumpy");
    CHECK(issueText(buildPlaced(rooms, objects, tables, CardText, wrong))
        .find("names the placed monster monster:stumpy") != std::string::npos);
}

TEST_CASE("DD-13: a table top on four leg blocks rests on them; on two it still rests on nothing")
{
    const auto rooms = [](int legCount)
    {
        std::string text =
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    ceiling: 384\n"
            "    platforms:\n"
            "      - {id: platform:top, at: [512, 512], size: [256, 128], base: 64, rise: 8}\n";
        // Set in from the top's corners, as DD-13's (legs at the very corners touch its sides and say nothing).
        const std::vector<std::string> legs = {"[424, 480]", "[600, 544]", "[600, 480]", "[424, 544]"};

        for (int index = 0; index < legCount; ++index)
        {
            text += "      - {at: " + legs[size_t(index)] + ", size: [16, 16], rise: 64}\n";
        }

        return text;
    };
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\n";
    const auto restsOnNothing = [](const BuiltPlaced &built)
    {
        return std::count_if(built.warnings.begin(), built.warnings.end(), [](const std::string &warning)
        {
            return warning.find("rests on nothing") != std::string::npos;
        });
    };
    const BuiltPlaced onFour = buildPlaced(rooms(4), objects, {});
    INFO(issueText(onFour));
    REQUIRE(onFour.built);
    CHECK(restsOnNothing(onFour) == 0);
    const BuiltPlaced onNone = buildPlaced(rooms(0), objects, {});
    REQUIRE(onNone.built);
    CHECK(restsOnNothing(onNone) == 1);
    const BuiltPlaced onTwo = buildPlaced(rooms(2), objects, {});
    REQUIRE(onTwo.built);
    CHECK(restsOnNothing(onTwo) == 1);
}

TEST_CASE("indoor mist: atmosphere.yml's mist goes into the scene as the game reads it, and a bad one is refused")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\n";
    // The Mad Necromancer's Lab's two layers (d20_mist.scene.yml), one per floor.
    const std::string atmosphere =
        "format: 0\n"
        "mist:\n"
        "  layers:\n"
        "    - {color_rgb: [104, 150, 110], base_height: 30, depth: 40, falloff_height: 100, visibility: 1280,\n"
        "       max_opacity: 0.8, noise: 0.5, noise_size: 420, drift: [8, 4]}\n"
        "    - {color_rgb: [104, 150, 110], base_height: -994, depth: 40, falloff_height: 100, visibility: 1280,\n"
        "       max_opacity: 0.8, noise: 0.5, noise_size: 420, drift: [8, 4]}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, CardText, "", atmosphere);
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.scene->mist.layers.size() == 2);
    CHECK(built.scene->mist.layers[0].baseHeight == doctest::Approx(30.0));
    CHECK(built.scene->mist.layers[1].baseHeight == doctest::Approx(-994.0));
    CHECK(built.scene->mist.layers[1].depth == doctest::Approx(40.0));
    CHECK(built.scene->mist.layers[0].visibility == doctest::Approx(1280.0));
    // Without the word, no mist.
    const BuiltPlaced plain = buildPlaced(rooms, objects, {});
    REQUIRE(plain.built);
    CHECK(!plain.scene->mist.enabled());
    // A key the game does not know is said against atmosphere.yml.
    const BuiltPlaced bad = buildPlaced(rooms, objects, {}, CardText, "",
        "format: 0\nmist:\n  layer: {color_rgb: [1, 2, 3], base_height: 0, falloff_height: 10, visibility: 100, "
        "thickness: 2}\n");
    CHECK(!bad.built);
    CHECK(hasIssue(bad.issues, "atmosphere", "the game refuses this mist"));
}

TEST_CASE("an exit's screen, and leaving the map from any event")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "exits:\n  - {id: exit:out, room: room:a, wall: south, to: exit:away}\n"
        "switches:\n  - {id: switch:cart, room: room:a, wall: north}\n"
        "  - {id: switch:throne, room: room:a, wall: east}\n  - {id: switch:cloud, room: room:a, wall: west}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:out, preset: exit, source: exit:out}\n"
        "  - {id: evt:cart, preset: script, source: switch:cart, title: Cart, effects: [{leave: exit:back}]}\n"
        "  - {id: evt:throne, preset: script, source: switch:throne, title: Throne, effects: [{leave: exit:away}]}\n"
        "  - {id: evt:cloud, preset: script, source: switch:cloud, title: Cloud, effects: [{leave: exit:up}]}\n";
    // The Mad Necromancer's Lab's exit: MoveToMap(..., 0, 0, 0, 1, "out06.odm").
    const std::string card = std::string(CardText)
        + "neighbours:\n"
          "  - {id: exit:away, to: out06.odm, kind: door, arrival: [-13071, 16397, 1057], direction: 270, "
          "screen: {picture: 1}}\n"
          "  - {id: exit:back, to: oute3.odm, kind: door, arrival: [10, 20, 30], direction: 90, keep_height: true}\n"
          "  - {id: exit:up, to: d05.blv, kind: door, arrival: [1, 2, 3], direction: 0}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, card, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(built.lua.find("evt.MoveToMap(-13071, 16397, 1057, 1536, 0, 0, 0, 1, \"out06.odm\")")
        != std::string::npos);
    // `leave` moves at once (decider D-24): no screen and no "leave the dungeon?" window, to an ODM or a BLV, even
    // by a neighbour whose exit shows a screen.
    // `keep_height`: the party arrives in the air at the arrival's height and falls (XD-07's throne throw).
    CHECK(built.lua.find("evt.MoveToMap(10, 20, 30, 512, 0, 0, 0, 0, \"oute3.odm\", {direct = true, keepHeight = true})")
        != std::string::npos);
    CHECK(built.lua.find("evt.MoveToMap(-13071, 16397, 1057, 1536, 0, 0, 0, 0, \"out06.odm\", {direct = true})")
        != std::string::npos);
    CHECK(built.lua.find("evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 0, \"d05.blv\", {direct = true})") != std::string::npos);
    // A neighbour the project does not have, and a screen that is not a map.
    CHECK(issueText(buildPlaced(rooms, objects, {}, card, "format: 0\nevents:\n"
        "  - {id: evt:cart, preset: script, source: switch:cart, effects: [{leave: exit:nowhere}]}\n"))
        .find("exit:nowhere, which is not in project.yml neighbours") != std::string::npos);
    const std::string badCard = std::string(CardText)
        + "neighbours:\n  - {id: exit:away, to: out06.odm, arrival: [0, 0, 0], screen: {picture: -1}}\n";
    CHECK(!buildPlaced(rooms, objects, {}, badCard, "format: 0\nevents:\n"
        "  - {id: evt:out, preset: exit, source: exit:out}\n").built);
}

TEST_CASE("A5: an exit effect leaves through the game's window from any click (X9's gate)")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "switches:\n  - {id: switch:gate, room: room:a, wall: north}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:gate, preset: script, source: switch:gate, title: Gate, effects: [{exit: exit:away}]}\n";
    const std::string card = std::string(CardText)
        + "neighbours:\n  - {id: exit:away, to: out06.odm, kind: door, arrival: [-13071, 16397, 1057], direction: 270}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, card, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    // As the exit preset writes it: no {direct = true}, so the game asks before an outdoor map.
    CHECK(built.lua.find("evt.MoveToMap(-13071, 16397, 1057, 1536, 0, 0, 0, 0, \"out06.odm\")") != std::string::npos);
    CHECK(built.lua.find("direct = true") == std::string::npos);
    CHECK(issueText(buildPlaced(rooms, objects, {}, card, "format: 0\nevents:\n"
        "  - {id: evt:gate, preset: script, source: switch:gate, effects: [{exit: exit:nowhere}]}\n"))
        .find("exit:nowhere, which is not in project.yml neighbours") != std::string::npos);
}

#include "core/Audit.h"

TEST_CASE("F16: an exit toward a dungeon shows the standard entrance window; `screen: none` moves directly")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "exits:\n  - {id: exit:down, room: room:a, wall: south, to: exit:deeper}\n"
        "  - {id: exit:chute, room: room:a, wall: north, to: exit:chute}\n"
        "  - {id: exit:crypt, room: room:a, wall: east, to: exit:crypt}\n"
        "switches:\n  - {id: switch:drop, room: room:a, wall: west}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:down, preset: exit, source: exit:down}\n"
        "  - {id: evt:chute, preset: exit, source: exit:chute}\n"
        "  - {id: evt:crypt, preset: exit, source: exit:crypt}\n"
        "  - {id: evt:drop, preset: script, source: switch:drop, title: Drop, effects: [{leave: exit:deeper}]}\n";
    const std::string card = std::string(CardText)
        + "neighbours:\n"
          "  - {id: exit:deeper, to: d05.blv, kind: door, arrival: [1, 2, 3]}\n"
          "  - {id: exit:chute, to: d06.blv, kind: door, arrival: [4, 5, 6], screen: none}\n"
          "  - {id: exit:crypt, to: d07.blv, kind: door, arrival: [7, 8, 9], screen: {text: 5001}}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, card, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(built.lua.find("evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 1, \"d05.blv\")") != std::string::npos);
    CHECK(built.lua.find("evt.MoveToMap(4, 5, 6, 0, 0, 0, 0, 0, \"d06.blv\", {direct = true})") != std::string::npos);
    CHECK(built.lua.find("evt.MoveToMap(7, 8, 9, 0, 0, 0, 5001, 1, \"d07.blv\")") != std::string::npos);
    // `leave` stays a direct move (decider D-24).
    CHECK(built.lua.find("evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 0, \"d05.blv\", {direct = true})") != std::string::npos);
}

TEST_CASE("F16: the audit wants the entrance window into a dungeon, never a Yes/No of the map's own")
{
    OpenYAMM::Studio::LoadedMap map;
    map.world = "xeen";
    map.fileName = "xeen_x6.odm";
    map.scriptText =
        "RegisterEvent(1, \"Gate\", function()\n"
        "    evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 1, \"xeen_xd20.blv\")\nend)\n"
        "RegisterEvent(2, \"Hole\", function()\n"
        "    evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 0, \"xeen_xd21.blv\")\nend)\n"
        "RegisterEvent(3, \"Fall\", function()\n"
        "    evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 0, \"xeen_xd21.blv\", {direct = true})\nend)\n"
        "RegisterEvent(4, \"Warzone\", function(continueStep)\n"
        "    if continueStep ~= 1 then\n"
        "        AskChoiceWithAnswerSteps(eventId, 3, \"Enter the War Zone?\", {{Answer = \"Yes\", Step = 1}, "
        "{Answer = \"No\", Step = 2}})\n        return\n    end\n"
        "    evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 1, \"xeen_xd20.blv\")\nend)\n"
        "RegisterEvent(5, \"Riddle\", function()\n"
        "    if evt.AskQuestion(\"Say the word\", {\"Rosebud\"}) then\n"
        "        evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 1, \"xeen_xd20.blv\")\n    end\nend)\n"
        "RegisterEvent(6, \"Vale\", function()\n"
        "    evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 0, \"xeen_x7.odm\")\nend)\n";
    const std::vector<OpenYAMM::Studio::AuditFinding> findings = OpenYAMM::Studio::auditEntranceWindows(map);
    std::vector<std::string> found;

    for (const OpenYAMM::Studio::AuditFinding &finding : findings)
    {
        found.push_back(finding.code + " " + finding.message.substr(0, 7));
    }

    CHECK(found == std::vector<std::string>{"entrance.no_window event 2", "entrance.question event 4"});
}

TEST_CASE("D-89: a box room measures as no cave, and the audit holds a cave to the cave-shape targets")
{
    const std::string box =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const BuiltPlaced built = buildPlaced(box, "format: 0\nstart: {room: room:a, at: [128, 128]}\n", {});
    INFO(issueText(built));
    REQUIRE(built.built);
    const OpenYAMM::Studio::CaveShape shape = OpenYAMM::Studio::caveShapeOf(built.map);
    CHECK(shape.floorUnevenShare == doctest::Approx(0.0));
    CHECK(shape.ceilingSpread == doctest::Approx(0.0));
    CHECK(shape.wallRoughShare == doctest::Approx(0.0));
    REQUIRE_EQ(shape.rooms.size(), 1u);

    OpenYAMM::Studio::LoadedMap map;
    map.indoor = built.map;
    CHECK(OpenYAMM::Studio::auditCaveShape(map, "cave").size() == 3);
    CHECK(OpenYAMM::Studio::auditCaveShape(map, "castle").empty());

    // An outline off the grid: its walls are rough.
    const std::string bent =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [700, -130], [1100, 300], [900, 1000], [200, 1150]], floor: 0, "
        "ceiling: 384}\n";
    const BuiltPlaced cave = buildPlaced(bent, "format: 0\nstart: {room: room:a, at: [400, 400]}\n", {});
    INFO(issueText(cave));
    REQUIRE(cave.built);
    // (Its second side runs 47 degrees, 2 off the grid: not rough.)
    CHECK(OpenYAMM::Studio::caveShapeOf(cave.map).wallRoughShare > 0.6);
}

TEST_CASE("A7: every exit to a neighbour with a named arrival arrives with that arrival's facing")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    // XD-20's four exits to one neighbour: the first took the arrival's facing, the others faced east (0).
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "exits:\n  - {id: exit:south, room: room:a, wall: south, to: exit:town}\n"
        "  - {id: exit:north, room: room:a, wall: north, to: exit:town}\n"
        "  - {id: exit:east, room: room:a, wall: east, to: exit:town}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:south, preset: exit, source: exit:south}\n"
        "  - {id: evt:north, preset: exit, source: exit:north}\n"
        "  - {id: evt:east, preset: exit, source: exit:east}\n";
    const std::string card = std::string(CardText)
        + "neighbours:\n  - {id: exit:town, to: oute3.odm, kind: door, arrival: \"entrance:testmap\"}\n";
    const std::vector<std::pair<std::string, std::string>> installed = {{"../../worlds/mm6/maps/oute3.studio.yml",
        "arrivals:\n  - {name: \"entrance:testmap\", at: [5, 6, 7], facing: 1024}\n"}};
    const BuiltPlaced built = buildPlaced(rooms, objects, installed, card, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    const std::string move = "evt.MoveToMap(5, 6, 7, 1024, 0, 0, 0, 0, \"oute3.odm\")";
    size_t count = 0;

    for (size_t at = built.lua.find(move); at != std::string::npos; at = built.lua.find(move, at + 1))
    {
        ++count;
    }

    CHECK(count == 3);
}

TEST_CASE("once per character, a shake, a random item by level and kind")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "switches:\n  - {id: switch:wall, room: room:a, wall: north}\n  - {id: switch:torch, room: room:a, wall: east}\n";
    // The Forge's event 91: once per character (bit 59), 25 fire resistance; Warlord's Fortress's flambeau:
    // GiveItem(6, 25).
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:wall, preset: script, source: switch:wall, title: Wall, condition: {not: {player_bit: 59}},\n"
        "     locked_text: Nothing, effects: [{player_bit: 59}, {add: {var: FireResistance, value: 25}},\n"
        "     {shake: {strength: 0.5, seconds: 1.5}}, {shake: {strength: 1, seconds: 2, at: [512, 512, 0], "
        "radius: [256, 1024]}}]}\n"
        "  - {id: evt:torch, preset: script, source: switch:torch, title: Torch,\n"
        "     effects: [{give_item: {level: 6, kind: 25}}, {give_item: {level: 2}}, {clear_player_bit: 59}]}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(built.lua.find("if not (not (IsPlayerBitSet(PlayerBit(59)))) then") != std::string::npos);
    CHECK(built.lua.find("SetPlayerBit(PlayerBit(59))") != std::string::npos);
    CHECK(built.lua.find("ClearPlayerBit(PlayerBit(59))") != std::string::npos);
    CHECK(built.lua.find("evt.CameraShake(0.5, 1.5)") != std::string::npos);
    CHECK(built.lua.find("evt.CameraShake(1, 2, 512, 512, 0, 256, 1024)") != std::string::npos);
    CHECK(built.lua.find("evt.GiveItem(6, 25)") != std::string::npos);
    CHECK(built.lua.find("evt.GiveItem(2, 0)") != std::string::npos);
    // What cannot be.
    const auto refused = [&](const std::string &effect)
    {
        return issueText(buildPlaced(rooms, objects, {}, CardText, "format: 0\nevents:\n"
            "  - {id: evt:x, preset: script, source: switch:wall, title: X, effects: [" + effect + "]}\n"));
    };
    CHECK(refused("{give_item: {level: 7, kind: 25}}").find("treasure level 1 to 6") != std::string::npos);
    CHECK(refused("{give_item: {level: 2, color: red}}").find("treasure level 1 to 6") != std::string::npos);
    CHECK(refused("{shake: {strength: 1}}").find("shake is") != std::string::npos);
    CHECK(refused("{shake: {strength: 1, seconds: 1, at: [0, 0, 0]}}").find("shake is") != std::string::npos);
    CHECK(refused("{player_bit: many}").find("player_bit is") != std::string::npos);
}

TEST_CASE("a map's own monster relations are set on entering the map")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "relations:\n"
        "  - {of: [1, Swordsman], toward: party, relation: hostile}\n"
        "  - {of: {group: 5}, toward: 9, relation: 2, both_ways: true}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, PlacedTables);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(built.lua.find("evt.SetMonsterRelation(1, 0, 4)") != std::string::npos);
    CHECK(built.lua.find("evt.SetMonsterRelation(7, 0, 4)") != std::string::npos);
    CHECK(built.lua.find("evt.SetMonsterRelation({group = 5}, 9, 2)") != std::string::npos);
    CHECK(built.lua.find("evt.SetMonsterRelation(9, {group = 5}, 2)") != std::string::npos);
    // Run on entering the map, by an event no face carries.
    CHECK(built.lua.find("RegisterEvent") != std::string::npos);
    // Without relations no such event.
    CHECK(buildPlaced(rooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\n", PlacedTables).lua
        .find("SetMonsterRelation") == std::string::npos);
    // A kind the table lacks, a relation out of range, the party both ways.
    const auto refused = [&](const std::string &relation)
    {
        return issueText(buildPlaced(rooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\nrelations:\n  - "
            + relation + "\n", PlacedTables));
    };
    CHECK(refused("{of: 99, toward: party, relation: hostile}").find("no monster number 99") != std::string::npos);
    CHECK(!refused("{of: 1, toward: party, relation: 5}").empty());
    CHECK(refused("{of: 1, toward: party, relation: 4, both_ways: true}").find("drop `both_ways`")
        != std::string::npos);
}

TEST_CASE("the build warns where the monster table leaves a slot's monsters peaceful to the party")
{
    const std::string rooms =
        "rooms:\n  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n";
    const std::string card = std::string(CardText) + "map_stats: {id: 9999, slots: [{monster: Goblin}]}\n";
    // hostile.txt: the Goblins (class 1) friendly to the party.
    std::vector<std::pair<std::string, std::string>> tables = PlacedTables;
    tables.push_back({"hostile.txt", "\tParty\tGoblin\tC2\tC3\nParty\t0\t0\t0\t4\n"});
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "spawns:\n  - {id: spawn:pack, room: room:a, at: [600, 600], slot: 1}\n";
    const auto warned = [](const BuiltPlaced &built)
    {
        return std::any_of(built.warnings.begin(), built.warnings.end(), [](const std::string &warning)
        {
            return warning.find("slot 1 (Goblin) spawns Goblin and Goblin (1, 2), which engine/data_tables/hostile.txt "
                "has friendly to the party") != std::string::npos
                && warning.find("objects.yml `relations` {of: [1, 2], toward: party, relation: hostile}")
                    != std::string::npos;
        });
    };
    const BuiltPlaced built = buildPlaced(rooms, objects, tables, card);
    INFO(issueText(built));
    REQUIRE(built.built);
    CHECK(warned(built));
    // Said: no warning.
    const BuiltPlaced said = buildPlaced(rooms, objects + "relations:\n  - {of: [1, 2], toward: party, relation: "
        "hostile}\n", tables, card);
    REQUIRE(said.built);
    CHECK(!warned(said));
    CHECK(said.lua.find("evt.SetMonsterRelation(2, 0, 4)") != std::string::npos);
    // Without hostile.txt nothing is checked.
    CHECK(!warned(buildPlaced(rooms, objects, PlacedTables, card)));
}

TEST_CASE("a sideways leaf open at its jamb has no face in the jamb's plane")
{
    for (const std::string fields : {"kind: slide_left", "kind: slide_right, leaves: 2"})
    {
        const BuiltMoving built = buildMoving(DoorRooms, doorObjects(fields), DoorWiring);
        INFO(fields << "\n" << issueText(built.rooms));
        REQUIRE(built.rooms.built);
        REQUIRE(built.loaded.indoor);
        REQUIRE(built.loaded.state);
        CHECK(OpenYAMM::Studio::findCoplanarFaces(*built.loaded.indoor, &*built.loaded.state).empty());
        // And the way through the open doorway is walked.
        CHECK(built.walks({256.0f, 256.0f, 0.0f}, {672.0f, 256.0f, 0.0f}, true));
    }
}

#include "core/Audit.h"

TEST_CASE("a question's answer must be given before it, by a thing with a name; a click that shows nothing is noted")
{
    // A sign in room a (reached at the start) or in room b (behind a door the sign's room opens later) gives the
    // word the door in room a asks for.
    const auto audit = [](bool signBehindDoor)
    {
        const std::string rooms =
            "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [512, 0], [512, 512], [0, 512]]\n"
            "    floor: 0\n"
            "    ceiling: 384\n"
            "    walls:\n"
            "      - wall: w\n"
            "        panels:\n"
            "          - {id: panel:ask, offset: 64, length: 96, bottom: 64, height: 96, "
            "surface: {texture: sign, size: [64, 128]}}\n"
            "          - {id: panel:mute, offset: 300, length: 96, bottom: 64, height: 96, "
            "surface: {texture: sign, size: [64, 128]}}\n"
            "      - wall: s\n"
            "        panels:\n"
            "          - {id: panel:near_sign, offset: 64, length: 96, bottom: 64, height: 96, "
            "surface: {texture: sign, size: [64, 128]}}\n"
            "  - id: room:b\n"
            "    outline: [[544, 128], [800, 128], [800, 384], [544, 384]]\n"
            "    floor: 0\n"
            "    ceiling: 256\n"
            "    walls:\n"
            "      - wall: e\n"
            "        panels:\n"
            "          - {id: panel:far_sign, offset: 64, length: 96, bottom: 64, height: 96, "
            "surface: {texture: sign, size: [64, 128]}}\n"
            "openings:\n"
            "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n";
        const std::string sign = signBehindDoor ? "panel:far_sign" : "panel:near_sign";
        const std::string wiring =
            "format: 0\nvariables: [said]\nevents:\n"
            "  - {id: evt:door, preset: door, source: door:ab, title: Door, condition: {map_var: said}}\n"
            "  - {id: evt:ask, preset: script, source: panel:ask, title: Face, effects: [{set: {var: {map_var: said},"
            " value: 1}}],\n"
            "     question: {ask: \"The word?\", answers: [Rosebud, rosebud]}}\n"
            "  - {id: evt:sign, preset: text, source: " + sign + ", title: Sign, text: The word is ROSEBUD}\n"
            "  - {id: evt:mute, preset: script, source: panel:mute, title: Lever, effects: [{set: {var: {map_var: said},"
            " value: 2}}]}\n";
        const BuiltMoving built = buildMoving(rooms, doorObjects("kind: slide_up"), wiring);
        INFO(issueText(built.rooms));
        REQUIRE(built.rooms.built);
        LoadedMap loaded = built.loaded;
        loaded.scriptText = built.lua;
        // The events' numbers from the built script, and what `oymap flow` would say of them.
        const auto numberOf = [&built](const std::string &title)
        {
            const size_t at = built.lua.find(", \"" + title + "\", function");
            const size_t open = built.lua.rfind('(', at);
            return std::stoi(built.lua.substr(open + 1, at - open - 1));
        };
        const std::string flow = "[{\"event\": " + std::to_string(numberOf("Door")) + ", \"title\": \"Door\", "
            "\"paths\": [{\"tests\": [{\"what\": \"map_var 0 >= 1\", \"taken\": true}], \"effects\": "
            "[\"door 1 open\"]}]}, {\"event\": " + std::to_string(numberOf("Face")) + ", \"title\": \"Face\", "
            "\"paths\": [{\"tests\": [], \"effects\": [\"set map_var 0 = 1\", \"AskQuestion(1)\"]}]}, "
            "{\"event\": " + std::to_string(numberOf("Sign")) + ", \"title\": \"Sign\", \"paths\": [{\"tests\": "
            "[], \"effects\": [\"StatusText(word)\"]}]}, {\"event\": " + std::to_string(numberOf("Lever"))
            + ", \"title\": \"Lever\", \"paths\": [{\"tests\": [], \"effects\": [\"set map_var 0 = 2\"]}]}]";
        std::vector<OpenYAMM::Studio::AuditFinding> findings = OpenYAMM::Studio::auditQuestions(loaded, flow);
        const std::vector<OpenYAMM::Studio::AuditFinding> silent = OpenYAMM::Studio::auditSilentClicks(loaded, flow);
        findings.insert(findings.end(), silent.begin(), silent.end());
        return findings;
    };
    const auto has = [](const std::vector<OpenYAMM::Studio::AuditFinding> &findings, const std::string &code,
                         const std::string &severity, const std::string &text)
    {
        return std::any_of(findings.begin(), findings.end(), [&](const OpenYAMM::Studio::AuditFinding &finding)
        {
            return finding.code == code && finding.severity == severity
                && finding.message.find(text) != std::string::npos;
        });
    };
    // In the same room: given in time, by a thing with a name.
    const std::vector<OpenYAMM::Studio::AuditFinding> near = audit(false);
    std::string said;

    for (const OpenYAMM::Studio::AuditFinding &finding : near)
    {
        said += finding.code + " " + finding.severity + " " + finding.message + "\n";
    }

    INFO(said);
    CHECK(has(near, "question.answer", "info", "asks for \"rosebud\": given by event"));
    // Behind the door the answer opens: given too late.
    const std::vector<OpenYAMM::Studio::AuditFinding> far = audit(true);
    CHECK(has(far, "question.answer", "warning", "asks for \"rosebud\": given only by"));
    // The lever changes only a variable: a click on it shows nothing.
    CHECK(has(near, "click.silent", "info", "(\"Lever\"): always, a click shows nothing"));
}

TEST_CASE("secret regions of a ceiling and secret plates; an effect that sets or clears the secret flag")
{
    // A level ceiling with a region traced on it (points all at its height, a line round the region), a secret
    // plate without an event, a platform whose top an event marks.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    ceiling_points: [[0, 0, 384], [1024, 0, 384], [1024, 1024, 384], [0, 1024, 384], [256, 256, 384], "
        "[512, 256, 384], [512, 512, 384], [256, 512, 384]]\n"
        "    ceiling_lines: [[[256, 256], [512, 256], [512, 512], [256, 512], [256, 256]]]\n"
        "    ceiling_surfaces: [{at: [384, 384], id: region:trace, secret: true, surface: {texture: trace, size: "
        "[128, 128]}}]\n"
        "    platforms:\n"
        "      - {id: platform:walk, at: [768, 768], size: [128, 128], rise: 32, surface: {texture: walkside, size: "
        "[64, 64]}, top_surface: {texture: walktop, size: [128, 128]}}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "plates:\n"
        "  - {id: plate:hidden, room: room:a, at: [128, 768], size: [128, 128], secret: true, surface: {texture: "
        "hidplate, size: [128, 128]}}\n"
        "  - {id: plate:mark, room: room:a, at: [768, 256], size: [128, 128], surface: {texture: markplate, size: "
        "[128, 128]}}\n";
    const auto wiring = [](const std::string &effects)
    {
        return "format: 0\nevents:\n"
            "  - {id: evt:mark, preset: script, source: plate:mark, trigger: step, effects: [" + effects + "]}\n";
    };
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, CardText,
        wiring("{secret: {of: platform:walk, face: top}}, {clear_secret: region:trace}, {secret: plate:mark}"));
    INFO(issueText(built));
    REQUIRE(built.built);
    const auto secret = [](const OpenYAMM::Game::IndoorFace &face)
    {
        return OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::IsSecret);
    };
    std::map<std::string, int> secretFaces;
    std::map<std::string, int> faces;
    std::map<std::string, int> cogs;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        ++faces[face.textureName];
        secretFaces[face.textureName] += secret(face) ? 1 : 0;
        cogs[face.textureName] = std::max(cogs[face.textureName], static_cast<int>(face.cogNumber));
    }

    // The region's faces and the secret plate carry the flag from the start; the rest of the ceiling, the other
    // plate and the platform do not.
    CHECK(faces["trace"] >= 1);
    CHECK(secretFaces["trace"] == faces["trace"]);
    CHECK(secretFaces["hidplate"] == faces["hidplate"]);
    CHECK(faces["hidplate"] >= 1);
    CHECK(faces["ceil"] >= 1);
    CHECK(secretFaces["ceil"] == 0);
    CHECK(secretFaces["markplate"] == 0);
    CHECK(secretFaces["walktop"] == 0);
    // The faces the effects name carry cogs, and the script sets and clears the flag by them.
    REQUIRE(cogs["trace"] > 0);
    REQUIRE(cogs["walktop"] > 0);
    REQUIRE(cogs["markplate"] > 0);
    CHECK(cogs["walkside"] == 0);
    CHECK(built.lua.find("evt.SetFacetBit(" + std::to_string(cogs["walktop"]) + ", FacetBits.IsSecret, 1)")
        != std::string::npos);
    CHECK(built.lua.find("evt.SetFacetBit(" + std::to_string(cogs["trace"]) + ", FacetBits.IsSecret, 0)")
        != std::string::npos);
    CHECK(built.lua.find("evt.SetFacetBit(" + std::to_string(cogs["markplate"]) + ", FacetBits.IsSecret, 1)")
        != std::string::npos);
    // What cannot be: a face other than the top, a room, a region whose id another thing has.
    CHECK(issueText(buildPlaced(rooms, objects, {}, CardText, wiring("{secret: {of: platform:walk, face: side}}")))
        .find("`side` is no face of it") != std::string::npos);
    CHECK(issueText(buildPlaced(rooms, objects, {}, CardText, wiring("{secret: room:a}")))
        .find("room:a is none of them") != std::string::npos);
    std::string twice = rooms;
    twice.replace(twice.find("id: region:trace"), 16, "id: platform:walk");
    CHECK(issueText(buildPlaced(twice, objects, {}, CardText)).find("is used by more than one") != std::string::npos);
}

TEST_CASE("a raking beam with a level top, and a raking beam cut at a ceiling level's flat top")
{
    const auto beamHeights = [](const BuiltPlaced &built)
    {
        std::set<int> heights;

        for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
        {
            if (face.textureName != "beam")
            {
                continue;
            }

            for (const uint16_t vertex : face.vertexIndices)
            {
                heights.insert(built.map.vertices[vertex].z);
            }
        }

        return heights;
    };
    const auto room = [](const std::string &beam)
    {
        return "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    ceiling: 512\n"
            "    beams:\n"
            "      - {path: [[100, 500], [400, 500]], width: 16, bottom: 200, bottom_end: 300, " + beam
            + ", surface: {texture: beam, size: [64, 64]}}\n";
    };
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\n";
    const BuiltPlaced level = buildPlaced(room("top: 480"), objects, {});
    INFO(issueText(level));
    REQUIRE(level.built);
    // The underside rakes from 200 to 300; the top is level at 480.
    CHECK(beamHeights(level) == std::set<int>{200, 300, 480});
    CHECK(issueText(buildPlaced(room("top: 480, depth: 64"), objects, {})).find("not both") != std::string::npos);
    CHECK(issueText(buildPlaced(room("top: 250"), objects, {})).find("at least 1 over its underside")
        != std::string::npos);
    // Under a pyramid roof whose flat top is at 512: the beam's top meets it at the near end and would rise 100
    // through it at the far end; it is cut level there, with no warning.
    const BuiltPlaced cut = buildPlaced(
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 16\n"
        "    ceiling_levels: [{ceiling: 512, top_outline: [[256, 256], [768, 256], [768, 768], [256, 768]]}]\n"
        "    beams:\n"
        "      - {path: [[400, 300], [400, 600]], width: 16, bottom: 300, bottom_end: 400, depth: 212, surface: "
        "{texture: beam, size: [64, 64]}}\n",
        objects, {});
    INFO(issueText(cut));
    REQUIRE(cut.built);
    CHECK(beamHeights(cut) == std::set<int>{300, 400, 512});
    CHECK(std::none_of(cut.warnings.begin(), cut.warnings.end(), [](const std::string &warning)
    {
        return warning.find("into whatever lies above") != std::string::npos;
    }));
}

TEST_CASE("MM6's v lid is laid as the shipped chests lay it: across from the front, its end strips 64 by 16")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n";

    for (const std::string facing : {"n", "e"})
    {
        const BuiltPlaced built = buildPlaced(rooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\nchests:\n"
            "  - {id: chest:carved, room: room:a, at: [400, 400], kind: ch3, lid: v, facing: " + facing + "}\n", {});
        INFO(facing << "\n" << issueText(built));
        REQUIRE(built.built);
        // Each face's middle, and its texels along u and v (stored plus delta).
        struct Laid
        {
            std::array<double, 2> middle = {};
            int uSpan = 0;
            int vSpan = 0;
            // The middle of its corners with v = 0, and of those with u = 0.
            std::array<double, 2> rowZero = {};
            std::array<double, 2> columnZero = {};
        };
        std::map<std::string, Laid> laid;
        // The left end strips of the front and of the back.
        std::vector<std::array<double, 2>> leftEnds;

        for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
        {
            Laid entry;
            int uLow = 1 << 20;
            int uHigh = -(1 << 20);
            int vLow = 1 << 20;
            int vHigh = -(1 << 20);
            int zeros = 0;
            int columnZeros = 0;

            for (size_t index = 0; index < face.vertexIndices.size(); ++index)
            {
                const OpenYAMM::Game::IndoorVertex &vertex = built.map.vertices[face.vertexIndices[index]];
                const int u = face.textureUs[index] + face.textureDeltaU;
                const int v = face.textureVs[index] + face.textureDeltaV;
                entry.middle[0] += vertex.x / static_cast<double>(face.vertexIndices.size());
                entry.middle[1] += vertex.y / static_cast<double>(face.vertexIndices.size());
                uLow = std::min(uLow, u);
                uHigh = std::max(uHigh, u);
                vLow = std::min(vLow, v);
                vHigh = std::max(vHigh, v);

                if (v == 0)
                {
                    entry.rowZero[0] += vertex.x;
                    entry.rowZero[1] += vertex.y;
                    ++zeros;
                }

                if (u == 0)
                {
                    entry.columnZero[0] += vertex.x;
                    entry.columnZero[1] += vertex.y;
                    ++columnZeros;
                }
            }

            if (columnZeros > 0)
            {
                entry.columnZero = {entry.columnZero[0] / columnZeros, entry.columnZero[1] / columnZeros};
            }

            if (face.textureName == "ch3frle")
            {
                leftEnds.push_back(entry.middle);
            }

            entry.uSpan = uHigh - uLow;
            entry.vSpan = vHigh - vLow;

            if (zeros > 0)
            {
                entry.rowZero = {entry.rowZero[0] / zeros, entry.rowZero[1] / zeros};
            }

            laid[face.textureName] = entry;
        }

        REQUIRE(laid.contains("ch3tplev"));
        REQUIRE(laid.contains("ch3tprev"));
        REQUIRE(laid.contains("ch3tpbv"));
        // The end strips 64 across the lid and 16 along it.
        CHECK(laid["ch3tplev"].uSpan == 64);
        CHECK(laid["ch3tplev"].vSpan == 16);
        CHECK(laid["ch3tprev"].uSpan == 64);
        CHECK(laid["ch3tprev"].vSpan == 16);
        const auto distance = [](const std::array<double, 2> &first, const std::array<double, 2> &second)
        {
            return std::hypot(first[0] - second[0], first[1] - second[1]);
        };
        // The front is where the lid's pictures start across (u 0); the left strip lies over the front's left end.
        REQUIRE(leftEnds.size() == 2);
        const std::array<double, 2> frontLeft =
            distance(leftEnds[0], laid["ch3tplev"].columnZero) < distance(leftEnds[1], laid["ch3tplev"].columnZero)
            ? leftEnds[0] : leftEnds[1];
        CHECK(distance(laid["ch3tplev"].middle, frontLeft) < distance(laid["ch3tprev"].middle, frontLeft));
        // Each picture's rows start at its edge toward the left end: the left strip's at the chest's end, the right
        // strip's at the middle.
        const std::array<double, 2> centre = {400.0, 400.0};
        CHECK(distance(laid["ch3tplev"].rowZero, centre) > distance(laid["ch3tplev"].middle, centre));
        CHECK(distance(laid["ch3tprev"].rowZero, centre) < distance(laid["ch3tprev"].middle, centre));
    }
}

TEST_CASE("a build with --out keeps the project's lock: a new event keeps its number when events are added before it")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_lock_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    std::ofstream(root / "project.yml", std::ios::binary) << CardText;
    std::ofstream(root / "rooms.yml", std::ios::binary) << std::string(ThemeText)
        + "rooms:\n  - {id: room:a, outline: [[0, 0], [768, 0], [768, 768], [0, 768]], floor: 0, ceiling: 384}\n";
    std::ofstream(root / "objects.yml", std::ios::binary) << "format: 0\nstart: {room: room:a}\n";
    const auto build = [&root](const std::string &wiring, const std::string &out)
    {
        std::ofstream(root / "wiring.yml", std::ios::binary) << wiring;
        Project project;
        std::vector<ProjectIssue> issues;
        REQUIRE(loadProject(root, project, issues));
        BuildOptions options;
        options.outputDirectory = root / out;
        BuildResult result;
        REQUIRE(buildProject(project, options, result));
        std::ifstream stream(root / out / "testmap.lua", std::ios::binary);
        return std::string((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    };
    const auto numberOf = [](const std::string &lua, const std::string &title)
    {
        const size_t at = lua.find(", \"" + title + "\", function");
        REQUIRE(at != std::string::npos);
        const size_t open = lua.rfind('(', at);
        return std::stoi(lua.substr(open + 1, at - open - 1));
    };
    const std::string first = build("format: 0\nevents:\n"
        "  - {id: evt:zeta, preset: script, trigger: load, title: Zeta, effects: [{gold: 1}]}\n", "first");
    // The project's lock holds the new event, not only the copy beside the build.
    std::ifstream lockStream(root / "ids.lock.yml", std::ios::binary);
    const std::string lock((std::istreambuf_iterator<char>(lockStream)), std::istreambuf_iterator<char>());
    CHECK(lock.find("evt:zeta") != std::string::npos);
    // Events whose ids sort before it come in: it keeps its number.
    const std::string second = build("format: 0\nevents:\n"
        "  - {id: evt:alpha, preset: script, trigger: load, title: Alpha, effects: [{gold: 2}]}\n"
        "  - {id: evt:beta, preset: script, trigger: load, title: Beta, effects: [{gold: 3}]}\n"
        "  - {id: evt:zeta, preset: script, trigger: load, title: Zeta, effects: [{gold: 1}]}\n", "second");
    CHECK(numberOf(second, "Zeta") == numberOf(first, "Zeta"));
    CHECK(numberOf(second, "Alpha") != numberOf(first, "Zeta"));
    std::filesystem::remove_all(root);
}

TEST_CASE("a message window only for things to read; other texts are status lines held by their length")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    walls:\n"
        "      - wall: n\n"
        "        panels:\n"
        "          - {id: panel:cage, offset: 64, length: 96, bottom: 64, height: 96, surface: {texture: rock, "
        "size: [64, 64]}}\n"
        "          - {id: panel:notice, offset: 300, length: 96, bottom: 64, height: 96, surface: {texture: rock, "
        "size: [64, 64]}}\n"
        "          - {id: panel:vat, offset: 600, length: 96, bottom: 64, height: 96, surface: {texture: rock, "
        "size: [64, 64]}}\n"
        "          - {id: panel:lever, offset: 800, length: 96, bottom: 64, height: 96, surface: {texture: rock, "
        "size: [64, 64]}}\n";
    const std::string longText = "The cage is locked, and the goblin warden wears its key on a ring.";
    const std::string wiring = "format: 0\nevents:\n"
        "  - {id: evt:cage, preset: text, source: panel:cage, title: Cage, text: \"" + longText + "\"}\n"
        "  - {id: evt:notice, preset: text, source: panel:notice, title: Notice, text: \"" + longText + "\"}\n"
        "  - {id: evt:vat, preset: text, source: panel:vat, title: Vat, text: \"It bubbles.\"}\n"
        "  - {id: evt:lever, preset: text, source: panel:lever, title: Lever, seconds: 4, text: \"It is stuck.\"}\n";
    const BuiltPlaced built =
        buildPlaced(rooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\n", {}, CardText, wiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    // 66 characters: 2 seconds and 4 more for its 15s.
    CHECK(built.lua.find("evt.StatusText(\"" + longText + "\", 6)") != std::string::npos);
    CHECK(built.lua.find("evt.SimpleMessage(\"" + longText + "\")") != std::string::npos);
    // A short text keeps the game's 2 seconds; `seconds` says it outright.
    CHECK(built.lua.find("evt.StatusText(\"It bubbles.\")") != std::string::npos);
    CHECK(built.lua.find("evt.StatusText(\"It is stuck.\", 4)") != std::string::npos);
}

#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"

TEST_CASE("faces in one plane are found with the moving parts half way, and matched against the original's")
{
    // A lift: its top rises from the floor to 128 over its travel.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 512}\n";
    const BuiltMoving door = buildMoving(rooms, "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "lifts:\n  - {id: lift:l, room: room:a, at: [600, 600], size: [128, 128], travel: 128}\n",
        "format: 0\nevents:\n  - {id: evt:l, preset: script, trigger: load, effects: [{text: lift}]}\n");
    INFO(issueText(door.rooms));
    REQUIRE(door.rooms.built);
    REQUIRE(door.loaded.state);
    const OpenYAMM::Game::MapDeltaData &state = *door.loaded.state;
    REQUIRE_FALSE(state.doors.empty());
    const OpenYAMM::Game::MapDeltaDoor &leaf = state.doors.front();
    // The leaf half way along its travel, and a face that does not move standing exactly where its first face is
    // then: a thing the leaf passes midway (it flickers there, not at either end).
    OpenYAMM::Game::EventRuntimeState half;
    OpenYAMM::Game::RuntimeMechanismState pose;
    pose.state = static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Opening);
    pose.currentDistance = static_cast<float>(leaf.moveLength) / 2.0f;
    half.mechanisms[leaf.doorId] = pose;
    const std::vector<OpenYAMM::Game::IndoorVertex> moved =
        OpenYAMM::Game::buildIndoorMechanismAdjustedVertices(*door.loaded.indoor, &state, &half);
    OpenYAMM::Game::IndoorMapData map = *door.loaded.indoor;
    // The lift's top: level, so its plane moves with it.
    std::optional<uint16_t> top;

    for (const uint16_t faceId : leaf.faceIds)
    {
        const OpenYAMM::Game::IndoorFace &face = map.faces[faceId];
        bool level = face.vertexIndices.size() >= 3;

        for (const uint16_t vertex : face.vertexIndices)
        {
            level = level && map.vertices[vertex].z == map.vertices[face.vertexIndices.front()].z;
        }

        top = level && !top ? std::optional<uint16_t>(faceId) : top;
    }

    REQUIRE(top);
    OpenYAMM::Game::IndoorFace still = map.faces[*top];

    for (uint16_t &vertex : still.vertexIndices)
    {
        map.vertices.push_back(moved[vertex]);
        vertex = static_cast<uint16_t>(map.vertices.size() - 1);
    }

    map.faces.push_back(still);
    const std::vector<OpenYAMM::Studio::CoplanarPair> pairs = OpenYAMM::Studio::findCoplanarFaces(map, &state);
    REQUIRE(pairs.size() == 1);
    CHECK(pairs[0].pose == "half");
    CHECK(OpenYAMM::Studio::describeCoplanarPair(map, &state, pairs[0], {}).find("half their way along")
        != std::string::npos);
    // Matched against an "original" with the same pair 40 units off: as the original; against one whose pair has
    // other textures, or lies 300 away, new.
    std::vector<OpenYAMM::Studio::CoplanarPair> marked = pairs;
    std::vector<OpenYAMM::Studio::CoplanarPlace> original = OpenYAMM::Studio::coplanarPlaces(map, pairs);
    original[0].at = {original[0].at[0] + 40.0 * original[0].normal[1],
        original[0].at[1] - 40.0 * original[0].normal[0], original[0].at[2]};
    CHECK(OpenYAMM::Studio::markPairsAsOriginal(map, marked, original) == 1);
    CHECK(marked[0].asOriginal);
    std::vector<OpenYAMM::Studio::CoplanarPlace> elsewhere = OpenYAMM::Studio::coplanarPlaces(map, pairs);
    elsewhere[0].at[2] += 300.0;
    std::vector<OpenYAMM::Studio::CoplanarPair> unmarked = pairs;
    CHECK(OpenYAMM::Studio::markPairsAsOriginal(map, unmarked, elsewhere) == 0);
    std::vector<OpenYAMM::Studio::CoplanarPlace> otherTextures = OpenYAMM::Studio::coplanarPlaces(map, pairs);
    otherTextures[0].firstTexture = "zzz";
    CHECK(OpenYAMM::Studio::markPairsAsOriginal(map, unmarked, otherTextures) == 0);
}

TEST_CASE("a decoration on a wall stands where its `at` is along the wall, over its `floor_height`")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 512\n"
        "    platforms:\n"
        "      - {id: platform:shelf, at: [300, 960], size: [256, 96], rise: 128}\n";
    const std::vector<std::pair<std::string, std::string>> tables = {
        {"decoration_data.txt",
            "Decoration Data\t\t\tDescriptor\n"
            "#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\tSoundId\t"
            "Flags\tSpriteId\n\n"
            "1\tnull\tnull\t0\t8\t8\t0\t0\t0\t0\t0\t0\t0\n"
            "157\tsmlbarel\tkeg\t0\t30\t40\t0\t0\t0\t0\t0\t0\t17789\n"}};
    const auto objects = [](const std::string &fields)
    {
        return "format: 0\nstart: {room: room:a, at: [128, 128]}\ndecorations:\n"
            "  - {id: deco:torch, room: room:a, decoration: smlbarel, wall: n, height: 64, " + fields + "}\n";
    };
    const BuiltPlaced built = buildPlaced(rooms, objects("at: [300, 1000], floor_height: 128"), tables);
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.map.entities.size() == 1);
    // Over the shelf's top at 128, 64 up, at x 300 on the north wall (12 inside it).
    CHECK(built.map.entities[0].x == 300);
    CHECK(built.map.entities[0].y == 1012);
    CHECK(built.map.entities[0].z == 192);
    // Without them: the middle of the wall over the room's floor, as before.
    const BuiltPlaced plain = buildPlaced(rooms, objects("along: 0.5"), tables);
    REQUIRE(plain.built);
    CHECK(plain.map.entities[0].x == 512);
    CHECK(plain.map.entities[0].z == 64);
    // Both ways at once, or a point far from the wall: refused.
    CHECK(issueText(buildPlaced(rooms, objects("at: [300, 1000], along: 0.5"), tables)).find("not both")
        != std::string::npos);
    CHECK(issueText(buildPlaced(rooms, objects("at: [300, 500]"), tables)).find("is not beside the wall")
        != std::string::npos);
}

TEST_CASE("a heap of gold lying on the floor holds its amount in the item record, as the game reads it")
{
    std::vector<std::pair<std::string, std::string>> tables = PlacedTables;
    tables[2].second += "197\t7item187\tGold\t0\tGold\tMisc\t0\t0\t0\t1\tGold\t6\n";
    const auto objects = [](const std::string &fields)
    {
        return "format: 0\nstart: {room: room:a, at: [100, 100]}\nitems:\n"
            "  - {id: item:coins, room: room:a, item: 197, at: [300, 300]" + fields + "}\n";
    };
    const BuiltPlaced built = buildPlaced(PlacedRooms, objects(", gold: 250"), tables);
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.scene->initialState.spriteObjects.size() == 1);
    // The fourth word of the record: 250 (0xFA), as readRawItemUInt32(record, 0x0c) takes it.
    const std::vector<uint8_t> &record = built.scene->initialState.spriteObjects[0].rawContainingItem;
    REQUIRE(record.size() >= 16);
    CHECK(record[12] == 0xFA);
    CHECK(record[13] == 0);
    // A heap without an amount is said; `gold` on another item is refused.
    const BuiltPlaced empty = buildPlaced(PlacedRooms, objects(""), tables);
    CHECK(std::any_of(empty.warnings.begin(), empty.warnings.end(), [](const std::string &warning)
    {
        return warning.find("heap of gold without an amount") != std::string::npos;
    }));
    std::string ring = objects(", gold: 5");
    ring.replace(ring.find("item: 197"), 9, "item: 1");
    CHECK(issueText(buildPlaced(PlacedRooms, ring, tables)).find("no heap of gold") != std::string::npos);
}

TEST_CASE("a liquid surface carries the fluid bit and its flow; its texture without it is said; plates side by side")
{
    const auto rooms = [](const std::string &top)
    {
        return "rooms:\n"
            "  - id: room:a\n"
            "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
            "    floor: 0\n"
            "    ceiling: 384\n"
            "    platforms:\n"
            "      - {at: [600, 600], size: [256, 128], rise: 48, surface: {texture: trough, size: [64, 64]}, "
            "top_surface: " + top + "}\n"
            "      - {at: [600, 300], size: [128, 128], rise: 32, top_surface: {texture: brew, size: [128, 128]}}\n";
    };
    // Two plates that share an edge: cut into the floor as one hole.
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\nplates:\n"
        "  - {id: plate:p1, room: room:a, outline: [[100, 600], [228, 600], [228, 728], [100, 728]], secret: true}\n"
        "  - {id: plate:p2, room: room:a, outline: [[100, 728], [228, 728], [228, 856], [100, 856]], secret: true}\n";
    const BuiltPlaced built =
        buildPlaced(rooms("{texture: brew, size: [128, 128], liquid: liquid, flow: right}"), objects, {});
    INFO(issueText(built));
    REQUIRE(built.built);
    uint32_t brewBits = 0;
    size_t stillBrew = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.textureName == "brew")
        {
            const bool fluid =
                OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Fluid);
            stillBrew += fluid ? 0 : 1;
            brewBits |= face.attributes;
        }
    }

    CHECK(OpenYAMM::Game::hasFaceAttribute(brewBits, OpenYAMM::Game::FaceAttribute::Fluid));
    CHECK(OpenYAMM::Game::hasFaceAttribute(brewBits, OpenYAMM::Game::FaceAttribute::FlowRight));
    CHECK_FALSE(OpenYAMM::Game::hasFaceAttribute(brewBits, OpenYAMM::Game::FaceAttribute::Lava));
    // The second platform lays the same picture without `liquid`: said.
    CHECK(stillBrew == 1);
    CHECK(std::any_of(built.warnings.begin(), built.warnings.end(), [](const std::string &warning)
    {
        return warning.find("the liquid brew lies on 1 face(s) without the fluid bit") != std::string::npos;
    }));
    // Lava: the burning bit too.
    const BuiltPlaced lava = buildPlaced(rooms("{texture: brew, size: [128, 128], liquid: lava}"), objects, {});
    REQUIRE(lava.built);
    CHECK(std::any_of(lava.map.faces.begin(), lava.map.faces.end(), [](const OpenYAMM::Game::IndoorFace &face)
    {
        return face.textureName == "brew"
            && OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Lava);
    }));
}

TEST_CASE("a translucent surface puts its faces into the scene's translucent_faces: a paper screen, a glass block")
{
    // A door leaf of paper that breaks (XD-22's screens, D-25) and a glass block seen from both sides.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [512, 0], [512, 512], [0, 512]]\n"
        "    floor: 0\n"
        "    ceiling: 384\n"
        "    platforms:\n"
        "      - {id: platform:case, at: [200, 200], size: [64, 64], rise: 96, surface: {texture: glass, "
        "size: [64, 64], translucent: {opacity: 0.5, tint: [1, 0.9, 0.8], two_sided: true}}}\n"
        "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [100, 400]}\n"
        "doors:\n  - {id: door:screen, opening: open:ab, surface: {texture: paper, size: [128, 256], "
        "translucent: 0.6}}\n"
        "destructibles:\n  - {id: destructible:screen, of: door:screen, hp: 5, material: wood}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {});
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.scene);
    REQUIRE(built.scene->translucentFaces.size() == 2);
    std::set<uint16_t> paper;
    std::set<uint16_t> glassTops;
    size_t glass = 0;

    for (size_t faceIndex = 0; faceIndex < built.map.faces.size(); ++faceIndex)
    {
        const OpenYAMM::Game::IndoorFace &face = built.map.faces[faceIndex];
        paper.insert(face.textureName == "paper" ? static_cast<uint16_t>(faceIndex) : uint16_t(0xffff));
        glass += face.textureName == "glass" ? 1 : 0;
        glassTops.insert(face.textureName == "glass" ? static_cast<uint16_t>(faceIndex) : uint16_t(0xffff));
    }

    paper.erase(0xffff);
    glassTops.erase(0xffff);
    REQUIRE_FALSE(paper.empty());

    for (const OpenYAMM::Game::IndoorSceneTranslucentFaces &entry : built.scene->translucentFaces)
    {
        const std::set<uint16_t> faces(entry.faceIds.begin(), entry.faceIds.end());

        if (entry.translucency.twoSided)
        {
            // The block: each of its faces, at its opacity and tint.
            CHECK(faces == glassTops);
            CHECK(faces.size() == glass);
            CHECK(entry.translucency.opacity == doctest::Approx(0.5));
            CHECK(entry.translucency.tint[1] == doctest::Approx(0.9));
        }
        else
        {
            // Every face of the paper leaf, drawn from the side it looks to.
            CHECK(faces == paper);
            CHECK(entry.translucency.opacity == doctest::Approx(0.6));
            CHECK(entry.translucency.tint[0] == doctest::Approx(1.0));
        }
    }

    // The leaf still breaks as one destructible.
    REQUIRE(built.scene->destructibles.size() == 1);
    CHECK(built.map.faces[*paper.begin()].cogNumber == built.scene->destructibles[0].cog);
}

TEST_CASE("a touch event: the door's faces run it when walked into, and the scene runs touch faces")
{
    // XD-10's mirages (D-4): a door that a click or walking into it opens.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [100, 400]}\n"
        "doors:\n  - {id: door:mirage, opening: open:ab, surface: {texture: rock, size: [128, 256]}}\n";
    const std::string touchWiring = "format: 0\nevents:\n  - {id: evt:mirage, preset: door, source: door:mirage, "
        "action: open, touch: true, text: The mirage dissipates with your touch.}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, {}, CardText, touchWiring);
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.scene);
    CHECK(built.scene->partyTouchFacesRun);
    size_t rockFaces = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.textureName != "rock")
        {
            continue;
        }

        ++rockFaces;
        CHECK(face.cogTriggered != 0);
        CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::TriggerByTouch));
        CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Clickable));
        CHECK_FALSE(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::PressurePlate));
    }

    CHECK(rockFaces > 0);

    // Without `touch` the door is clicked only, and the scene leaves touch faces alone.
    const BuiltPlaced clicked = buildPlaced(rooms, objects, {}, CardText,
        "format: 0\nevents:\n  - {id: evt:mirage, preset: door, source: door:mirage, action: open}\n");
    REQUIRE(clicked.built);
    CHECK_FALSE(clicked.scene->partyTouchFacesRun);

    for (const OpenYAMM::Game::IndoorFace &face : clicked.map.faces)
    {
        const bool touched = face.textureName == "rock"
            && OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::TriggerByTouch);
        CHECK_FALSE(touched);
    }

    // `touch` is a clicked event's: a step event is refused.
    const BuiltPlaced refused = buildPlaced(rooms, objects, {}, CardText,
        "format: 0\nevents:\n  - {id: evt:mirage, preset: switch, trigger: load, touch: true, opens: [door:mirage]}\n");
    CHECK_FALSE(refused.built);
    CHECK(issueText(refused).find("touch") != std::string::npos);
}

#include "core/Audit.h"

TEST_CASE("light fixtures: a hung lamp at the ceiling, a torch on a wall, a candle on the floor; each wrong once")
{
    // Room a (0-512 by 0-512, floor 0, ceiling 384) opens east into room b through a doorway 256 wide.
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 256, height: 288}\n";
    const std::vector<std::pair<std::string, std::string>> tables = {{"decoration_data.txt",
        "Decoration Data\n"
        "#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\tSoundId\t"
        "Flags\tSpriteId\n\n"
        "1\tnull\tnull\t0\t8\t8\t0\t0\t0\t0\t0\t0\t0\n"
        "2\ttorch01\ttorch\t0\t8\t52\t512\t0\t0\t0\t0\t0\t0\n"
        "3\tchand\tchandelier\t0\t30\t100\t0\t0\t0\t0\t0\t0\t0\n"
        "4\tcndl\tcandle\t0\t16\t40\t0\t0\t0\t0\t0\t0\t0\n"}};
    const std::string objects =
        "format: 0\nstart: {room: room:b, at: [800, 100]}\n"
        "lights:\n"
        "  - {id: light:good, room: room:a, at: [256, 256], height: 200, radius: 256}\n"
        "  - {id: light:buried, room: room:a, at: [100, 100], height: 900, radius: 256}\n"
        "decorations:\n"
        "  - {id: deco:lamp, room: room:a, decoration: chand, at: [256, 256], height: 284, hangs: true}\n"
        "  - {id: deco:fallen_lamp, room: room:a, decoration: chand, at: [100, 400]}\n"
        "  - {id: deco:torch, room: room:a, decoration: torch01, wall: n, along: 0.3, height: 128}\n"
        "  - {id: deco:free_torch, room: room:a, decoration: torch01, at: [300, 380], height: 128, hangs: true}\n"
        "  - {id: deco:door_torch, room: room:b, decoration: torch01, at: [590, 256], height: 128, hangs: true}\n"
        "  - {id: deco:candle, room: room:a, decoration: cndl, at: [100, 100]}\n"
        "  - {id: deco:high_candle, room: room:a, decoration: cndl, at: [400, 100], height: 100}\n";
    const BuiltPlaced built = buildPlaced(rooms, objects, tables);
    INFO(issueText(built));
    REQUIRE(built.built);
    REQUIRE(built.map.entities.size() == 7);
    LoadedMap map;
    map.fileName = "testmap.blv";
    map.indoor = built.map;
    // The build hangs a chandelier from the ceiling by its kind: lay the fallen one on the floor by hand.
    map.indoor->entities[1].z = 0;
    LightFixtureData data;
    data.decorationTableText = tables[0].second;
    std::map<std::string, std::vector<std::string>> found;
    std::string all;


    for (const AuditFinding &finding : auditLightFixtures(map, data))
    {
        all += finding.code + ": " + finding.message + "\n";

        if (finding.severity != "info")
        {
            found[finding.code].push_back(finding.severity + " " + finding.message.substr(0, finding.message.find(
                ' ', finding.message.find(' ') + 1)));
        }
    }

    INFO(all);
    // Entities in objects.yml order: 0 lamp, 1 fallen lamp, 2 torch, 3 free torch, 4 door torch (in the doorway's
    // mouth, also far from a wall), 5 candle, 6 high.
    CHECK(found["lights.ceiling_on_floor"] == std::vector<std::string>{"error decoration 1"});
    CHECK(found["lights.wall_missing"] == std::vector<std::string>{"error decoration 3", "error decoration 4"});
    CHECK(found["lights.in_doorway"] == std::vector<std::string>{"error decoration 4"});
    CHECK(found["lights.floating"] == std::vector<std::string>{"error decoration 6"});
    CHECK(found["lights.light_in_solid"] == std::vector<std::string>{"error light 1"});
    CHECK(found["lights.ceiling_gap"].empty());
    CHECK(found["lights.in_solid"].empty());
    CHECK(found["lights.wall_height"].empty());

    // The fixture list wins over the hint: a candle listed as free is never floating.
    data.fixtureTexts = {"fixtures:\n  cndl: free\n"};
    found.clear();

    for (const AuditFinding &finding : auditLightFixtures(map, data))
    {
        found[finding.code].push_back(finding.message);
    }

    CHECK(found["lights.floating"].empty());
}

TEST_CASE("a switch plate lies on a block's sloping top in the top's plane, as Goblinwatch's console has them")
{
    // A console 64 square whose top rises from 96 at the west to 160 at the east (45 degrees), and a level block.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 512\n"
        "    steep_floor: true\n"
        "    platforms:\n"
        "      - {id: platform:console, at: [512, 512], size: [64, 64], rise: 96, top_slope: {to: 160, toward: east}}\n"
        "      - {id: platform:table, at: [200, 200], size: [64, 64], rise: 64}\n";
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a, at: [900, 100]}\n"
        "switches:\n"
        "  - {id: switch:a, room: room:a, block: platform:console, side: top, at: [536, 536], size: [16, 16], "
        "off: {texture: swoff, size: [16, 16]}, on: swon}\n"
        "  - {id: switch:b, room: room:a, block: platform:table, side: top, at: [200, 200], size: [16, 16]}\n";
    const std::string wiring =
        "format: 0\nevents:\n"
        "  - {id: evt:a, preset: switch, source: switch:a, effects: [{text: A}]}\n"
        "  - {id: evt:b, preset: switch, source: switch:b, effects: [{text: B}]}\n";
    const BuiltMoving built = buildMoving(rooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    // The plate covers x 528 to 544 and y 528 to 544 of the plan, where the top is at 144 to 160; lifted 1 up and 1
    // west (2 along the top's normal, in whole units), as the original's plates lie in their top's plane.
    CHECK(built.rooms.hasVertex(527, 528, 145));
    CHECK(built.rooms.hasVertex(543, 544, 161));
    CHECK(built.rooms.hasVertex(527, 544, 145));
    // On the level top: 2 over it at 64.
    CHECK(built.rooms.hasVertex(192, 192, 66));
    CHECK(built.rooms.hasVertex(208, 208, 66));
    bool found = false;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        if (face.textureName != "swoff")
        {
            continue;
        }

        found = true;
        CHECK(face.cogTriggered == 1);

        // The picture stretched over it: its top up the slope, its left to the north as seen from the low side.
        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const auto &vertex = built.rooms.map.vertices[face.vertexIndices[index]];
            CHECK(face.textureVs[index] == (vertex.z == 161 ? 0 : 16));
            CHECK(face.textureUs[index] == (vertex.y == 544 ? 0 : 16));
        }
    }

    CHECK(found);

    const auto refused = [&](const std::string &from, const std::string &to)
    {
        std::string changed = objects;
        REQUIRE(changed.find(from) != std::string::npos);
        changed.replace(changed.find(from), from.size(), to);
        const BuiltMoving result = buildMoving(rooms, changed, wiring);
        CHECK_FALSE(result.rooms.built);
        return issueText(result.rooms);
    };
    CHECK(refused("at: [536, 536]", "at: [540, 536]").find("does not lie wholly on platform:console's top")
        != std::string::npos);
    CHECK(refused("side: top, at: [536, 536]", "side: top").find("needs `at: [x, y]`") != std::string::npos);
    CHECK(refused("side: top, at: [536, 536]", "side: top, at: [536, 536], height: 40")
        .find("drop `wall`, `along`, `height`") != std::string::npos);
    CHECK(refused("block: platform:table, side: top", "kind: lever, block: platform:table, side: top")
        .find("only a plate (`kind: plate`) lies on a block's top") != std::string::npos);
    // A level side of the sloping block still takes no switch from the old rule's other forms: a side works.
    CHECK(refused("side: top, at: [536, 536]", "side: w").find("has a sloping top") != std::string::npos);
}

TEST_CASE("the reveal before a shut leaf standing 2 back from its wall's face takes the leaf's picture")
{
    // Two rooms 16 apart, a doorway 128 wide and 128 high, a leaf 16 thick (as thick as the wall): it stands 2
    // back from each face; the 2 in front of it on its jambs, sill and lintel were the reveal's picture (Goblinwatch's
    // lockers: a light trim line round a red door).
    const std::string rooms =
        "themes:\n"
        "  - id: theme:t\n"
        "    wall: {texture: wall, size: [128, 128]}\n"
        "    floor: {texture: floor, size: [128, 128]}\n"
        "    ceiling: {texture: ceil, size: [128, 128]}\n"
        "defaults: {theme: theme:t}\n"
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 256}\n"
        "  - {id: room:b, outline: [[528, 0], [800, 0], [800, 512], [528, 512]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 128, reveal: {texture: trim, size: [32, 32]}}\n";
    const std::string objects =
        "format: 0\n"
        "start: {room: room:a, at: [100, 100]}\n"
        "doors:\n"
        "  - {id: door:d, opening: open:ab, kind: slide_up, thickness: 16, surface: {texture: front, size: [128, 128]},"
        " back_surface: {texture: back, size: [128, 128]}}\n";
    const std::string wiring = "format: 0\nevents:\n  - {id: evt:d, preset: door, source: door:d}\n";
    const BuiltMoving built = buildMoving(rooms, objects, wiring);
    INFO(issueText(built.rooms));
    REQUIRE(built.rooms.built);
    std::map<std::string, int> strips;
    int trim = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.rooms.map.faces)
    {
        int lowX = 100000;
        int highX = -100000;

        for (const uint16_t index : face.vertexIndices)
        {
            lowX = std::min<int>(lowX, built.rooms.map.vertices[index].x);
            highX = std::max<int>(highX, built.rooms.map.vertices[index].x);
        }

        // Faces through the wall (not the leaf, which stands at one x).
        if (lowX == highX)
        {
            continue;
        }

        if (lowX == 514 && highX == 526)
        {
            ++trim;
            CHECK(face.textureName == "trim");
            CHECK(lowX == 514);
            CHECK(highX == 526);
        }
        else if (lowX == 512 && highX == 514)
        {
            strips[face.textureName] += 1;
        }
        else if (lowX == 526 && highX == 528)
        {
            strips[face.textureName + "_back"] += 1;
        }
    }

    // Jambs, sill and lintel: the leaf's front picture before it, its back picture behind, the trim between.
    CHECK(strips["front"] == 4);
    CHECK(strips["back_back"] == 4);
    CHECK(trim == 4);

    // A leaf thinner than its wall stands in its middle: the reveal shows whole, as meant.
    std::string thin = objects;
    thin.replace(thin.find("thickness: 16"), 13, "thickness: 8");
    const BuiltMoving recessed = buildMoving(rooms, thin, wiring);
    REQUIRE(recessed.rooms.built);
    int fronts = 0;

    for (const OpenYAMM::Game::IndoorFace &face : recessed.rooms.map.faces)
    {
        fronts += face.textureName == "front" ? 1 : 0;
    }

    CHECK(fronts == 1);
}

namespace
{
// An outdoor model face looking south (y falls toward its front) from x0 to x1 at y, 0 to 256 high, its picture's
// texels running u0 to u1 across.
void addSouthFace(OpenYAMM::Game::OutdoorBModel &model, double x0, double x1, double y, double u0, double u1,
    const std::string &texture, uint16_t event)
{
    const uint16_t first = static_cast<uint16_t>(model.vertices.size());

    for (const std::array<double, 2> &corner : std::vector<std::array<double, 2>>{{x0, 0.0}, {x1, 0.0}, {x1, 256.0},
             {x0, 256.0}})
    {
        OpenYAMM::Game::OutdoorBModelVertex vertex;
        vertex.x = static_cast<int>(corner[0]);
        vertex.y = static_cast<int>(y);
        vertex.z = static_cast<int>(corner[1]);
        model.vertices.push_back(vertex);
    }

    OpenYAMM::Game::OutdoorBModelFace face;
    face.vertexIndices = {first, static_cast<uint16_t>(first + 1), static_cast<uint16_t>(first + 2),
        static_cast<uint16_t>(first + 3)};
    face.textureUs = {static_cast<int16_t>(u0), static_cast<int16_t>(u1), static_cast<int16_t>(u1),
        static_cast<int16_t>(u0)};
    face.textureVs = {256, 256, 0, 0};
    face.textureName = texture;
    face.cogTriggeredNumber = event;
    model.faces.push_back(face);
}

std::vector<std::string> outdoorDoorCodes(
    const std::vector<OpenYAMM::Game::OutdoorBModel> &models, const std::string &world)
{
    LoadedMap map;
    map.world = world;
    map.outdoor.emplace();
    map.outdoor->bmodels = models;
    TextureFitData data;
    data.classTexts = {"textures:\n  wingl: {class: feature, door: wing, size: [128, 256], twin: wingr}\n"
        "  bigdoor: {class: feature, door: single, size: [256, 256]}\n"};
    std::vector<std::string> codes;

    for (const AuditFinding &finding : auditDoorTextures(map, data))
    {
        codes.push_back(finding.code + " " + finding.severity);
    }

    return codes;
}
}

TEST_CASE("F2 door rules in the audit: a lone wing, a part of a picture, a narrow pair, a door off its steps")
{
    OpenYAMM::Game::OutdoorBModel lone;
    lone.name = "building:a";
    addSouthFace(lone, 0, 128, 0, 0, 128, "wingl", 5);
    CHECK(outdoorDoorCodes({lone}, "xeen") == std::vector<std::string>{"doors.lone_wing error"});
    // The shipped maps: the same rule a warning.
    CHECK(outdoorDoorCodes({lone}, "mm8") == std::vector<std::string>{"doors.lone_wing warning"});
    // A pair of 128 leaves, the second mirrored: nothing to say.
    OpenYAMM::Game::OutdoorBModel pair;
    pair.name = "building:b";
    addSouthFace(pair, 0, 128, 0, 0, 128, "wingl", 5);
    addSouthFace(pair, 128, 256, 0, 128, 0, "wingl", 5);
    CHECK(outdoorDoorCodes({pair}, "xeen").empty());
    // Squeezed into one bay: 64 leaves.
    OpenYAMM::Game::OutdoorBModel squeezed;
    squeezed.name = "building:c";
    addSouthFace(squeezed, 0, 64, 0, 0, 128, "wingl", 5);
    addSouthFace(squeezed, 64, 128, 0, 128, 0, "wingl", 5);
    CHECK(outdoorDoorCodes({squeezed}, "xeen") == std::vector<std::string>{"doors.narrow_pair error"});
    // D-91 §3: a 256-wide door picture split half and half over a pair (the blast door before): a part of it.
    OpenYAMM::Game::OutdoorBModel split;
    split.name = "building:d";
    addSouthFace(split, 0, 256, 0, 0, 128, "bigdoor", 5);
    addSouthFace(split, 256, 512, 0, 128, 0, "bigdoor", 5);
    CHECK(outdoorDoorCodes({split}, "xeen")
        == std::vector<std::string>{"doors.part_picture error", "doors.part_picture error"});
    // Whole on each leaf: right.
    OpenYAMM::Game::OutdoorBModel whole;
    whole.name = "building:e";
    addSouthFace(whole, 0, 256, 0, 0, 256, "bigdoor", 5);
    addSouthFace(whole, 256, 512, 0, 256, 0, "bigdoor", 5);
    CHECK(outdoorDoorCodes({whole}, "xeen").empty());
    // Steps before the door (south of it, y below 0), their middle 128 east of the door's.
    OpenYAMM::Game::OutdoorBModel steps;
    steps.name = "thing:e_steps";

    for (const std::array<int, 2> &corner : std::vector<std::array<int, 2>>{{128, -96}, {512, -96}, {512, -16},
             {128, -16}})
    {
        OpenYAMM::Game::OutdoorBModelVertex vertex;
        vertex.x = corner[0];
        vertex.y = corner[1];
        steps.vertices.push_back(vertex);
    }

    CHECK(outdoorDoorCodes({whole, steps}, "xeen") == std::vector<std::string>{"doors.off_steps error"});
}

TEST_CASE("F27 in the audit: a door whose land before it rises over its sill is buried")
{
    // A whole 256-wide door at y 0 looking south, its sill at 0, on flat land at 0, then with the land before it at
    // 128 (the nodes round world [0, 0]: grid 64 and 65 each way, 32 units a step).
    OpenYAMM::Game::OutdoorBModel house;
    house.name = "building:f";
    addSouthFace(house, 0, 256, 0, 0, 256, "bigdoor", 5);
    LoadedMap map;
    map.world = "xeen";
    map.outdoor.emplace();
    map.outdoor->bmodels = {house};
    map.outdoor->heightMap.assign(static_cast<size_t>(OpenYAMM::Game::OutdoorMapData::TerrainWidth)
        * OpenYAMM::Game::OutdoorMapData::TerrainHeight, 0);
    TextureFitData data;
    data.classTexts = {"textures:\n  bigdoor: {class: feature, door: single, size: [256, 256]}\n"};
    const auto codes = [&]()
    {
        std::vector<std::string> found;

        for (const AuditFinding &finding : auditDoorTextures(map, data))
        {
            found.push_back(finding.code + " " + finding.severity);
        }

        return found;
    };
    CHECK(codes().empty());

    for (const int x : {63, 64, 65})
    {
        for (const int y : {64, 65})
        {
            map.outdoor->heightMap[static_cast<size_t>(y) * OpenYAMM::Game::OutdoorMapData::TerrainWidth + x] = 4;
        }
    }

    CHECK(codes() == std::vector<std::string>{"houses.buried_door warning"});
    // A step under the threshold (32 over the sill): nothing to say.
    std::replace(map.outdoor->heightMap.begin(), map.outdoor->heightMap.end(), uint8_t{4}, uint8_t{1});
    CHECK(codes().empty());
}

TEST_CASE("D-91 in the audit: a cave mouth that leads nowhere and is no shelter or blocked")
{
    Project project;
    ProjectFile sketch;
    sketch.text = "structures:\n"
        "  - {id: thing:den, kind: cave_mouth, at: [50, 50]}\n"
        "  - {id: thing:hall, kind: cave_mouth, at: [60, 50], into: {map: d.blv, at: [0, 0, 0]}}\n"
        "  - {id: thing:camp, kind: cave_mouth, at: [70, 50], form: shelter}\n"
        "  - {id: thing:adit, kind: cave_mouth, at: [80, 50], form: blocked}\n";
    sketch.document = YAML::Load(sketch.text);
    project.files["sketch.yml"] = sketch;
    const DressingFacts facts = projectDressingFacts(project);
    CHECK(facts.blindMouths == std::vector<std::string>{"thing:den"});
    const std::vector<AuditFinding> findings = auditBlindMouths(facts.blindMouths);
    REQUIRE(findings.size() == 1);
    CHECK(findings[0].code == "caves.blind_mouth");
    CHECK(findings[0].severity == "error");
    CHECK(studioFileDressingFacts(YAML::Load("blind_mouths: [\"thing:den\"]")).blindMouths == facts.blindMouths);
}
