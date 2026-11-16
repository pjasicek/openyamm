// What S5b1 carried to S5b2 (devdocs/map_studio/S5.md "S5b1 part two and S5b1 exit"; S5_BROWSER_EDITOR.md 3.5, 3.10,
// 3.12): check.validate's fixes beyond the first five kinds, geometry among them (an outline that runs clockwise or
// repeats a point, a path's repeated point, a height point given twice, an opening wider than its wall, a thing outside
// its room, a missing id with one obvious target, a word on the wrong kind in the sketch), each applied making its
// issue go; view.layout's travel of doors, lifts and movers for the 3D view's scrubber; and view.layout_at for outdoor
// projects (History's ghost of the land and the models).
#include "doctest/doctest.h"

#include "cli/Rpc.h"

#include <yaml-cpp/yaml.h>

#include <cmath>
#include <filesystem>
#include <fstream>
#include <map>
#include <random>
#include <string>
#include <vector>

namespace
{
const char *CardText = "format: 0\nid: carried\nname: Carried\nworld: mm6\nkind: indoor\nprofile: dungeon\n";
const char *ThemeText =
    "format: 1\n"
    "themes:\n"
    "  - id: theme:plain\n"
    "    wall: {texture: t1w11a, size: [128, 256]}\n"
    "    floor: {texture: oflr, size: [128, 128]}\n"
    "    ceiling: {texture: d2ceil4, size: [256, 256]}\n"
    "    door: {texture: t1d2, size: [256, 256], fit: true}\n"
    "defaults: {theme: theme:plain}\n";
const char *TwoRooms =
    "rooms:\n"
    "  - id: room:a\n"
    "    outline: [[0, 0], [768, 0], [768, 640], [0, 640]]\n"
    "    floor: 0\n"
    "    ceiling: 384\n"
    "  - {id: room:b, outline: [[768, 0], [1280, 0], [1280, 512], [768, 512]], floor: 0, ceiling: 384}\n"
    "openings:\n"
    "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
const char *ObjectsText = "format: 1\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab}\n";

std::filesystem::path scratchFolder(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s5b2c_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

void writeText(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

std::filesystem::path writeProject(const std::string &name, const std::string &rooms,
    const std::string &objects = ObjectsText, const std::string &wiring = "format: 0\nevents: []\n")
{
    const std::filesystem::path root = scratchFolder(name);
    writeText(root / "project.yml", CardText);
    writeText(root / "rooms.yml", std::string(ThemeText) + rooms);
    writeText(root / "objects.yml", objects);
    writeText(root / "wiring.yml", wiring);
    return root;
}

YAML::Node call(const std::string &method, const std::string &params)
{
    return YAML::Load(OpenYAMM::Studio::callRpcMethod(method, params));
}

std::string quoted(const std::filesystem::path &path)
{
    return "\"" + path.string() + "\"";
}

std::string kindOf(const YAML::Node &answer)
{
    return answer["error"] ? answer["error"]["data"]["kind"].Scalar() : std::string("result");
}

YAML::Node applyOps(const std::filesystem::path &root, const std::string &ops)
{
    return call("edit.apply", "{\"project\":" + quoted(root) + ",\"ops\":" + ops
        + ",\"allow_errors\":true,\"author\":\"user\",\"label\":\"test\"}");
}

// The issues of check.validate (with their fixes) whose message contains `part`.
std::vector<YAML::Node> issuesWith(const std::filesystem::path &root, const std::string &part)
{
    std::vector<YAML::Node> found;
    const YAML::Node answer = call("check.validate", "{\"project\":" + quoted(root) + ",\"use_assets\":false}");
    REQUIRE(kindOf(answer) == "result");

    for (const YAML::Node &issue : answer["result"]["issues"])
    {
        if (issue["message"].Scalar().find(part) != std::string::npos)
        {
            found.push_back(issue);
        }
    }

    return found;
}

std::string fixLabel(const YAML::Node &issue, size_t index = 0)
{
    return issue["fixes"] && issue["fixes"].size() > index ? issue["fixes"][index]["label"].Scalar() : std::string();
}

// A node read from a JSON answer written back as JSON: a quoted scalar (tag "!") stays a string, a plain one is the
// number, true, false or null it was.
std::string jsonOf(const YAML::Node &node)
{
    if (node.IsSequence())
    {
        std::string out = "[";

        for (size_t index = 0; index < node.size(); ++index)
        {
            out += (index > 0 ? "," : "") + jsonOf(node[index]);
        }

        return out + "]";
    }

    if (node.IsMap())
    {
        std::string out = "{";

        for (YAML::const_iterator field = node.begin(); field != node.end(); ++field)
        {
            out += (out.size() > 1 ? "," : "") + std::string("\"") + field->first.Scalar() + "\":"
                + jsonOf(field->second);
        }

        return out + "}";
    }

    if (node.IsNull())
    {
        return "null";
    }

    if (node.Tag() != "!")
    {
        return node.Scalar();
    }

    std::string out = "\"";

    for (const char character : node.Scalar())
    {
        out += character == '"' || character == '\\' ? std::string("\\") + character : std::string(1, character);
    }

    return out + "\"";
}

YAML::Node applyFix(const std::filesystem::path &root, const YAML::Node &issue, size_t index = 0)
{
    REQUIRE(issue["fixes"]);
    REQUIRE(issue["fixes"].size() > index);
    return applyOps(root, jsonOf(issue["fixes"][index]["ops"]));
}

YAML::Node roomOf(const std::filesystem::path &root, const std::string &id)
{
    for (const YAML::Node &room : YAML::LoadFile((root / "rooms.yml").string())["rooms"])
    {
        if (room["id"].Scalar() == id)
        {
            return room;
        }
    }

    return YAML::Node(YAML::NodeType::Undefined);
}

// One issue with `part` and its fix at `index` labelled as `label` starts; applied, no issue with `part` is left.
void fixTakesIssueAway(const std::filesystem::path &root, const std::string &part, const std::string &label,
    size_t index = 0)
{
    std::vector<YAML::Node> issues = issuesWith(root, part);
    REQUIRE(issues.size() == 1);
    INFO(issues[0]["message"].Scalar());
    CHECK(fixLabel(issues[0], index).rfind(label, 0) == 0);
    const YAML::Node applied = applyFix(root, issues[0], index);
    const std::string refusal = applied["error"] ? applied["error"]["message"].Scalar() : std::string();
    INFO(refusal);
    REQUIRE(kindOf(applied) == "result");
    CHECK(issuesWith(root, part).empty());
}
}

TEST_CASE("S5b2 carried: a room outline that runs clockwise is reversed; one that repeats a point loses the repeat")
{
    const std::filesystem::path clockwise = writeProject("clockwise",
        "rooms:\n  - {id: room:a, outline: [[0, 0], [0, 640], [768, 640], [768, 0]], floor: 0, ceiling: 384}\n");
    fixTakesIssueAway(clockwise, "the outline runs clockwise", "reverse the outline's points");
    const YAML::Node outline = roomOf(clockwise, "room:a")["outline"];
    REQUIRE(outline.size() == 4);
    CHECK(outline[0][0].as<int>() == 0);
    CHECK(outline[1][0].as<int>() == 768);
    CHECK(outline[1][1].as<int>() == 0);

    // The first corner given again at the end, and a corner given twice in a row.
    const std::filesystem::path repeated = writeProject("repeated",
        "rooms:\n  - {id: room:a, outline: [[0, 0], [768, 0], [768, 0], [768, 640], [0, 640], [0, 0]], floor: 0, "
        "ceiling: 384}\n");
    fixTakesIssueAway(repeated, "repeats a point", "drop the 2 repeated points of the outline");
    CHECK(roomOf(repeated, "room:a")["outline"].size() == 4);

    // Both at once: repeated and clockwise.
    const std::filesystem::path both = writeProject("both",
        "rooms:\n  - {id: room:a, outline: [[0, 0], [0, 640], [0, 640], [768, 640], [768, 0]], floor: 0, "
        "ceiling: 384}\n");
    fixTakesIssueAway(both, "the outline", "drop the repeated point and reverse the outline");

    // A bow tie is not one change away from standing: no fix.
    const std::filesystem::path bowTie = writeProject("bowtie",
        "rooms:\n  - {id: room:a, outline: [[0, 0], [768, 640], [768, 0], [0, 640]], floor: 0, ceiling: 384}\n");
    const std::vector<YAML::Node> crossed = issuesWith(bowTie, "the outline");
    REQUIRE(crossed.size() == 1);
    CHECK(!crossed[0]["fixes"]);
}

TEST_CASE("S5b2 carried: a block's and a ceiling level's clockwise outline are reversed")
{
    const std::filesystem::path root = writeProject("blocks",
        "rooms:\n  - id: room:a\n    outline: [[0, 0], [768, 0], [768, 640], [0, 640]]\n"
        "    floor: 0\n    ceiling: 384\n"
        "    platforms:\n      - {key: dais, outline: [[100, 100], [100, 300], [300, 300], [300, 100]], rise: 48}\n");
    fixTakesIssueAway(root, "points counter-clockwise", "reverse the outline's points");
    const std::filesystem::path ceiling = writeProject("ceilinglevel",
        "rooms:\n  - id: room:a\n    outline: [[0, 0], [768, 0], [768, 640], [0, 640]]\n    floor: 0\n"
        "    ceiling: 384\n    ceiling_levels:\n"
        "      - {key: vault, outline: [[100, 100], [100, 300], [300, 300], [300, 100]], ceiling: 512}\n");
    fixTakesIssueAway(ceiling, "a ceiling level is a simple counter-clockwise outline", "reverse the outline's points");
}

TEST_CASE("S5b2 carried: a corridor's repeated point and a height point given twice are dropped")
{
    const std::filesystem::path path = writeProject("path",
        "rooms:\n  - {id: room:a, path: [[0, 0], [512, 0], [512, 0], [512, 512]], width: 192, floor: 0, "
        "ceiling: 256}\n");
    fixTakesIssueAway(path, "the path repeats a point", "drop the repeated point of the path");
    CHECK(roomOf(path, "room:a")["path"].size() == 3);

    const std::filesystem::path points = writeProject("points",
        "rooms:\n  - id: room:a\n    outline: [[0, 0], [768, 0], [768, 640], [0, 640]]\n"
        "    floor: 0\n    ceiling: 384\n"
        "    floor_points: [[384, 320, 16], [200, 200, 8], [384, 320, 24]]\n");
    fixTakesIssueAway(points, "has the point", "drop the repeated point");
    CHECK(roomOf(points, "room:a")["floor_points"].size() == 2);
}

TEST_CASE("S5b2 carried: an opening wider than the wall its rooms share is narrowed, or made full")
{
    const std::string wide = std::string(TwoRooms);
    const std::string tooWide = wide.substr(0, wide.find("width: 128")) + "width: 640, height: 256}\n";
    const std::filesystem::path narrow = writeProject("narrow", tooWide);
    fixTakesIssueAway(narrow, "wide but the two rooms share only", "narrow it to 480");
    const std::filesystem::path full = writeProject("full", tooWide);
    fixTakesIssueAway(full, "wide but the two rooms share only", "make it `width: full`", 1);
}

TEST_CASE("S5b2 carried: a thing outside its room is given the room it stands in, or moved inside its own")
{
    const std::string objects = std::string(ObjectsText)
        + "chests:\n  - {id: chest:a, room: room:a, at: [1000, 200], kind: ch1}\n";
    const std::filesystem::path other = writeProject("otherroom", TwoRooms, objects);
    fixTakesIssueAway(other, "is not inside room room:a", "give chest:a the room it stands in (room:b)");

    const std::filesystem::path inside = writeProject("moveinside", TwoRooms, objects);
    fixTakesIssueAway(inside, "is not inside room room:a", "move chest:a inside room:a", 1);
    const YAML::Node chest = YAML::LoadFile((inside / "objects.yml").string())["chests"][0];
    CHECK(chest["at"][0].as<int>() == 736);
    CHECK(chest["at"][1].as<int>() == 200);

    // Outside every room: only the move is offered.
    const std::string nowhere = std::string(ObjectsText)
        + "lights:\n  - {id: light:a, room: room:a, offset: [2000, 0], radius: 256}\n";
    const std::filesystem::path far = writeProject("nowhere", TwoRooms, nowhere);
    fixTakesIssueAway(far, "is not inside room room:a", "move light:a inside room:a");
}

TEST_CASE("S5b2 carried: a reference to a missing id names the obvious one instead")
{
    // A near spelling.
    const std::filesystem::path near = writeProject("near", TwoRooms, ObjectsText,
        "format: 0\nevents:\n  - {id: evt:shut, preset: text, source: door:ac, text: shut}\n");
    std::vector<YAML::Node> found = issuesWith(near, "nothing in the project has the id door:ac");
    REQUIRE(found.size() == 1);
    CHECK(fixLabel(found[0]) == "name door:ab instead (a near spelling)");
    // Taking the reference out is still offered after it.
    CHECK(found[0]["fixes"].size() >= 2);
    fixTakesIssueAway(near, "nothing in the project has the id door:ac", "name door:ab instead");
    CHECK(YAML::LoadFile((near / "wiring.yml").string())["events"][0]["source"].Scalar() == "door:ab");

    // Far from every door, but the only door.
    const std::filesystem::path only = writeProject("only", TwoRooms, ObjectsText,
        "format: 0\nevents:\n  - {id: evt:shut, preset: text, source: door:portcullis, text: shut}\n");
    fixTakesIssueAway(only, "nothing in the project has the id door:portcullis",
        "name door:ab instead (the only door of the project)");

    // Two doors, neither near: no obvious one.
    const std::filesystem::path two = writeProject("two",
        std::string(TwoRooms) + "  - {id: open:ab2, from: room:a, to: room:b, along: 0.1, width: 64, height: 128}\n",
        std::string(ObjectsText) + "  - {id: door:zz, opening: open:ab2}\n",
        "format: 0\nevents:\n  - {id: evt:shut, preset: text, source: door:portcullis, text: shut}\n");
    found = issuesWith(two, "nothing in the project has the id door:portcullis");
    REQUIRE(found.size() == 1);
    CHECK(fixLabel(found[0]).rfind("name ", 0) != 0);

    // Two doors as near as each other (door:ab and door:zz, one letter each from door:az): no obvious one either.
    REQUIRE(kindOf(applyOps(two, "[{\"op\":\"set\",\"id\":\"evt:shut\",\"file\":\"wiring.yml\","
        "\"fields\":{\"source\":\"door:az\"}}]")) == "result");
    found = issuesWith(two, "nothing in the project has the id door:az");
    REQUIRE(found.size() == 1);
    CHECK(fixLabel(found[0]).rfind("name ", 0) != 0);

    // Three letters off is not near (door:ab from door:abcde; door:zz five): no near spelling, and with two doors no
    // "only" one either.
    REQUIRE(kindOf(applyOps(two, "[{\"op\":\"set\",\"id\":\"evt:shut\",\"file\":\"wiring.yml\","
        "\"fields\":{\"source\":\"door:abcde\"}}]")) == "result");
    found = issuesWith(two, "nothing in the project has the id door:abcde");
    REQUIRE(found.size() == 1);
    CHECK(fixLabel(found[0]).rfind("name ", 0) != 0);
}

TEST_CASE("S5b2 carried: a word on the wrong kind in the sketch is dropped by its fix")
{
    const std::filesystem::path root = scratchFolder("sketchkind");
    writeText(root / "project.yml", "format: 0\nid: sketchkind\nworld: mm8\nkind: outdoor\n");
    writeText(root / "plan.yml", "format: 0\nspaces:\n  - {id: zone:land, kind: zone}\nentrances:\n"
        "  - {id: entrance:north, kind: arrival, space: zone:land, facing: s}\n"
        "height_bands:\n  - {id: band:low, range: [576, 704]}\n");
    writeText(root / "sketch.yml", "format: 0\npoints:\n  - {id: entrance:north, at: [100, 50], facing: s}\n"
        "heights:\n  bands:\n    - {band: band:low, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n"
        "structures:\n"
        "  - {id: thing:span, kind: bridge, line: [[70, 60], [76, 60]], height: 64, pier_radius: 48}\n");
    fixTakesIssueAway(root, "the word `pier_radius` does not apply to kind bridge", "drop `pier_radius`");
    CHECK(!YAML::LoadFile((root / "sketch.yml").string())["structures"][0]["pier_radius"]);

    // A sketch outline with its first point repeated at the end loses the repeat (sketch outlines may run either way).
    writeText(root / "sketch.yml", "format: 0\npoints:\n  - {id: entrance:north, at: [100, 50], facing: s}\n"
        "heights:\n  bands:\n    - {band: band:low, polygon: [[0, 0], [0, 128], [128, 128], [128, 0], [0, 0]]}\n");
    fixTakesIssueAway(root, "is given twice", "drop the repeated point of the outline");
}

TEST_CASE("S5b2 carried: view.layout gives the travel of doors, lifts and movers for the scrubber")
{
    // Rooms 32 apart (a door needs a wall to stand in), room:a high enough for the lift's travel.
    const std::filesystem::path root = writeProject("travel",
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [768, 0], [768, 640], [0, 640]], floor: 0, ceiling: 640}\n"
        "  - {id: room:b, outline: [[800, 0], [1312, 0], [1312, 512], [800, 512]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n"
        "  - {id: open:ab2, from: room:a, to: room:b, along: 0.15, width: 96, height: 192}\n",
        std::string(ObjectsText)
            + "  - {id: door:swing, opening: open:ab2, kind: hinged}\n"
              "lifts:\n  - {id: lift:a, room: room:a, at: [160, 480], size: [128, 128], travel: 256}\n"
              "movers:\n  - {id: mover:a, room: room:a, at: [512, 160], size: [128, 128], height: 32, "
              "travel: [0, 192, 0], state: end}\n");
    const YAML::Node layout = call("view.layout", "{\"project\":" + quoted(root) + "}");

    if (layout["error"])
    {
        for (const YAML::Node &issue : layout["error"]["data"]["issues"])
        {
            MESSAGE(issue["path"].Scalar() << ": " << issue["message"].Scalar());
        }
    }

    REQUIRE(kindOf(layout) == "result");
    std::map<std::string, YAML::Node> byId;

    for (const char *pList : {"doors", "lifts"})
    {
        for (const YAML::Node &entry : layout["result"][pList])
        {
            byId[entry["id"].Scalar()] = entry;
        }
    }

    REQUIRE(byId.contains("door:ab"));
    REQUIRE(byId["door:ab"]["moves"].size() == 1);
    // A sliding door rises by the opening's height.
    CHECK(byId["door:ab"]["moves"][0]["by"][2].as<int>() == 256);
    CHECK(byId["door:ab"]["starts_open"].as<bool>() == false);
    REQUIRE(byId.contains("door:swing"));
    REQUIRE(byId["door:swing"]["moves"].size() == 1);
    CHECK(byId["door:swing"]["moves"][0]["pivot"].IsSequence());
    CHECK(std::abs(byId["door:swing"]["moves"][0]["degrees"].as<int>()) == 90);
    REQUIRE(byId.contains("lift:a"));
    CHECK(byId["lift:a"]["moves"][0]["by"][2].as<int>() == 256);
    CHECK(byId["lift:a"]["moves"][0]["at"][0].as<int>() == 160);
    REQUIRE(byId.contains("mover:a"));
    CHECK(byId["mover:a"]["moves"][0]["by"][1].as<int>() == 192);
    CHECK(byId["mover:a"]["starts_open"].as<bool>() == true);
}

TEST_CASE("S5b2 carried: view.layout_at draws an outdoor project's land and models as they were")
{
    const std::filesystem::path root = scratchFolder("outdoorghost");
    writeText(root / "project.yml", "format: 0\nid: ghostland\nworld: mm8\nkind: outdoor\n");
    writeText(root / "plan.yml", "format: 0\nspaces:\n  - {id: zone:land, kind: zone}\nentrances:\n"
        "  - {id: entrance:north, kind: arrival, space: zone:land, facing: s}\n"
        "height_bands:\n  - {id: band:low, range: [576, 704]}\n  - {id: band:high, range: [1536, 1664]}\n");
    writeText(root / "sketch.yml", "format: 0\npoints:\n  - {id: entrance:north, at: [100, 50], facing: s}\n"
        "heights:\n  bands:\n    - {key: ground, band: band:low, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n"
        "structures:\n  - {id: thing:well, kind: well, at: [60, 60]}\n");
    const YAML::Node now = call("view.layout", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(now) == "result");
    // The land raised and the well moved.
    REQUIRE(kindOf(applyOps(root, "[{\"op\":\"patch\",\"file\":\"sketch.yml\",\"patch\":[{\"op\":\"replace\","
        "\"path\":\"/heights/bands/ground/band\",\"value\":\"band:high\"}]}]")) == "result");
    REQUIRE(kindOf(applyOps(root, "[{\"op\":\"set\",\"id\":\"thing:well\",\"file\":\"sketch.yml\","
        "\"fields\":{\"at\":[30,30]}}]")) == "result");
    const YAML::Node before = call("view.layout_at", "{\"project\":" + quoted(root) + ",\"sequence\":1}");
    REQUIRE(kindOf(before) == "result");
    CHECK(before["result"]["kind"].Scalar() == "outdoor");
    REQUIRE(before["result"]["land"]["heights"].size() == 128 * 128);
    const YAML::Node after = call("view.layout", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(after) == "result");
    // Before entry 1 the land was low; it is high now.
    const size_t corner = 105 * 128 + 105;
    CHECK(before["result"]["land"]["heights"][corner].as<int>() == now["result"]["land"]["heights"][corner].as<int>());
    CHECK(after["result"]["land"]["heights"][corner].as<int>() > before["result"]["land"]["heights"][corner].as<int>());
    // The models of then: as many as now, the well where it stood.
    CHECK(before["result"]["models"].size() == now["result"]["models"].size());

    if (now["result"]["models"].size() > 0)
    {
        CHECK(before["result"]["models"][0]["min"][0].as<int>() == now["result"]["models"][0]["min"][0].as<int>());
    }
}
