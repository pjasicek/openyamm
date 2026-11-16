// S5b1 part two (devdocs/map_studio/S5_BROWSER_EDITOR.md 6.4, 3.8, 3.10, 3.12): what the hand tools read from the core
// and the new operation: op name (a sub-object's id given by the core), switches and exits in view.layout, the map
// card's slots in project.resolve, the fixes of check.validate's issues (each applied makes its issue go), the history's
// "show as it was" (view.layout_at), and assets.search's monsters, items and sounds. Also the regression that a fix
// computed by check.validate leaves the schemas as they were (a yaml-cpp assignment once wrote into them).
#include "doctest/doctest.h"

#include "cli/Rpc.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <fstream>
#include <random>
#include <string>

namespace
{
const char *CardText = "format: 0\nid: parttwo\nname: Part two\nworld: mm6\nkind: indoor\nprofile: dungeon\n"
                       "map_stats:\n  id: 9450\n  slots:\n    - {monster: Goblin, tier: 2, per_marker: [2, 4], weight: 60}\n";
const char *RoomsText =
    "format: 1\n"
    "themes:\n"
    "  - id: theme:plain\n"
    "    wall: {texture: t1w11a, size: [128, 256]}\n"
    "    floor: {texture: oflr, size: [128, 128]}\n"
    "    ceiling: {texture: d2ceil4, size: [256, 256]}\n"
    "defaults: {theme: theme:plain}\n"
    "rooms:\n"
    "  - id: room:a\n"
    "    outline: [[0, 0], [768, 0], [768, 640], [0, 640]]\n"
    "    floor: 0\n"
    "    ceiling: 384\n"
    "    platforms:\n"
    "      - {key: dais, at: [384, 320], size: [192, 128], rise: 48}\n"
    "    beams:\n"
    "      - {key: beam1, path: [[64, 64], [704, 64]], bottom: 320}\n"
    "  - {id: room:b, outline: [[832, 0], [1344, 0], [1344, 512], [832, 512]], floor: 0, ceiling: 384}\n"
    "openings:\n"
    "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
const char *ObjectsText =
    "format: 1\nstart: {room: room:a}\n"
    "doors:\n  - {id: door:ab, opening: open:ab}\n"
    "switches:\n  - {id: switch:lever, room: room:a, wall: north, along: 0.5, kind: lever}\n"
    "exits: []\n";
const char *WiringText = "format: 0\nevents:\n  - {id: evt:lever, preset: switch, source: switch:lever, toggles: [door:ab]}\n";

std::filesystem::path scratchFolder(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s5b1p2_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

void writeText(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

std::filesystem::path writeProject(const std::string &name, const std::string &objects = ObjectsText,
    const std::string &wiring = WiringText)
{
    const std::filesystem::path root = scratchFolder(name);
    writeText(root / "project.yml", CardText);
    writeText(root / "rooms.yml", RoomsText);
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

YAML::Node apply(const std::filesystem::path &root, const std::string &ops)
{
    return call("edit.apply", "{\"project\":" + quoted(root) + ",\"ops\":" + ops
        + ",\"allow_errors\":true,\"author\":\"user\",\"label\":\"test\"}");
}

YAML::Node thingOf(const YAML::Node &layout, const std::string &id)
{
    for (const YAML::Node &thing : layout["result"]["things"])
    {
        if (thing["id"].Scalar() == id)
        {
            return thing;
        }
    }

    return YAML::Node(YAML::NodeType::Undefined);
}

// The issues of check.validate (with their fixes) whose message starts with `start`.
std::vector<YAML::Node> issuesStarting(const std::filesystem::path &root, const std::string &start)
{
    std::vector<YAML::Node> found;
    const YAML::Node answer = call("check.validate", "{\"project\":" + quoted(root) + ",\"use_assets\":false}");

    for (const YAML::Node &issue : answer["result"]["issues"])
    {
        if (issue["message"].Scalar().rfind(start, 0) == 0)
        {
            found.push_back(issue);
        }
    }

    return found;
}

// Applies an issue's first fix (its ops as JSON).
YAML::Node applyFix(const std::filesystem::path &root, const YAML::Node &issue, size_t index = 0)
{
    REQUIRE(issue["fixes"]);
    REQUIRE(issue["fixes"].size() > index);
    YAML::Emitter json;
    json << YAML::DoubleQuoted << YAML::Flow << issue["fixes"][index]["ops"];
    return apply(root, json.c_str());
}
}

TEST_CASE("S5b1 part two: op name gives a platform an id of the core's; a second name and a list without ids are refused")
{
    const std::filesystem::path root = writeProject("name");
    const YAML::Node named = apply(root, "[{\"op\":\"name\",\"id\":\"room:a\",\"path\":\"/platforms/dais\"}]");
    REQUIRE(kindOf(named) == "result");
    REQUIRE(named["result"]["ids_allocated"].size() == 1);
    CHECK(named["result"]["ids_allocated"][0].Scalar() == "rooms.yml#platform:a_1");
    const YAML::Node again = apply(root, "[{\"op\":\"name\",\"id\":\"room:a\",\"path\":\"/platforms/dais\"}]");
    CHECK(kindOf(again) == "bad_operation");
    const YAML::Node beam = apply(root, "[{\"op\":\"name\",\"id\":\"room:a\",\"path\":\"/beams/beam1\"}]");
    CHECK(kindOf(beam) == "bad_operation");
    // Its undo takes the id away again.
    REQUIRE(kindOf(call("edit.undo", "{\"project\":" + quoted(root) + ",\"author\":\"user\"}")) == "result");
    std::ifstream rooms(root / "rooms.yml");
    const std::string text((std::istreambuf_iterator<char>(rooms)), std::istreambuf_iterator<char>());
    CHECK(text.find("platform:a_1") == std::string::npos);
}

TEST_CASE("S5b1 part two: view.layout places switches and exits at their faces: a lever on a wall, a plate on a block's top")
{
    const std::filesystem::path root = writeProject("layout");
    REQUIRE(kindOf(apply(root, "[{\"op\":\"name\",\"id\":\"room:a\",\"path\":\"/platforms/dais\"},"
        "{\"op\":\"add\",\"to\":\"switches\",\"value\":{\"id\":\"switch:top\",\"room\":\"room:a\",\"block\":\"platform:a_1\","
        "\"side\":\"top\",\"at\":[384,320],\"size\":[32,32]}},"
        "{\"op\":\"add\",\"to\":\"neighbours\",\"file\":\"project.yml\",\"value\":{\"id\":\"exit:out\",\"to\":\"oute3\","
        "\"kind\":\"door\",\"arrival\":[0,0,0]}},"
        "{\"op\":\"add\",\"to\":\"exits\",\"value\":{\"id\":\"exit:west\",\"room\":\"room:a\",\"wall\":\"west\",\"along\":0.5,"
        "\"to\":\"exit:out\"}}]"))
        == "result");
    const YAML::Node layout = call("view.layout", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(layout) == "result");
    const YAML::Node lever = thingOf(layout, "switch:lever");
    REQUIRE(lever.IsDefined());
    CHECK(lever["kind"].Scalar() == "switch");
    CHECK(lever["name"].Scalar() == "lever");
    CHECK(lever["at"][0].as<int>() == 384);
    CHECK(lever["at"][1].as<int>() == 640);
    // The north wall's face looks south, into the room.
    CHECK(lever["facing"].as<int>() == 270);
    const YAML::Node top = thingOf(layout, "switch:top");
    REQUIRE(top.IsDefined());
    CHECK(top["name"].Scalar() == "plate");
    CHECK(top["at"][0].as<int>() == 384);
    CHECK(top["at"][2].as<int>() >= 48);
    CHECK(!top["facing"]);
    const YAML::Node exit = thingOf(layout, "exit:west");
    REQUIRE(exit.IsDefined());
    CHECK(exit["kind"].Scalar() == "exit");
    CHECK(exit["at"][0].as<int>() == 0);
    CHECK(exit["facing"].as<int>() == 0);
}

TEST_CASE("S5b1 part two: project.resolve names a spawn point's slots, and the map card itself with card: true")
{
    const std::filesystem::path root = writeProject("slots",
        std::string(ObjectsText) + "spawns:\n  - {id: spawn:a, room: room:a, at: [200, 200], slot: 1}\n");
    const YAML::Node spawn = call("project.resolve", "{\"project\":" + quoted(root) + ",\"id\":\"spawn:a\"}");
    REQUIRE(kindOf(spawn) == "result");
    REQUIRE(spawn["result"]["slots"].size() == 1);
    CHECK(spawn["result"]["slots"][0]["monster"].Scalar() == "Goblin");
    CHECK(spawn["result"]["slots"][0]["count"].Scalar() == "2-4");
    CHECK(spawn["result"]["slots"][0]["source"].Scalar() == "written");
    const YAML::Node card = call("project.resolve", "{\"project\":" + quoted(root) + ",\"card\":true}");
    REQUIRE(kindOf(card) == "result");
    CHECK(card["result"]["file"].Scalar() == "project.yml");
    CHECK(card["result"]["fields"]["id"]["value"].as<int>() == 9450);
    CHECK(card["result"]["slots"].size() == 1);
    CHECK(kindOf(call("project.resolve", "{\"project\":" + quoted(root) + "}")) == "invalid_params");
}

TEST_CASE("S5b1 part two: check.validate offers fixes, and each fix applied takes its issue away")
{
    // A dangling reference in a list, a word on the wrong kind, an undeclared variable.
    const std::filesystem::path root = writeProject("fixes",
        std::string(ObjectsText) + "lights:\n  - {id: light:a, room: room:a, offset: [0, 0], radius: 512}\n",
        "format: 0\nevents:\n"
        "  - {id: evt:lever, preset: switch, source: switch:lever, toggles: [door:ab, door:gone]}\n"
        "  - {id: evt:use, preset: script, source: door:ab, condition: {map_var: chapel}}\n");
    std::vector<YAML::Node> dangling = issuesStarting(root, "nothing in the project has the id door:gone");
    REQUIRE(dangling.size() == 1);
    CHECK(dangling[0]["fixes"][0]["label"].Scalar().find("take door:gone out") == 0);
    REQUIRE(kindOf(applyFix(root, dangling[0])) == "result");
    CHECK(issuesStarting(root, "nothing in the project has the id door:gone").empty());

    // A required reference: the object goes.
    REQUIRE(kindOf(apply(root, "[{\"op\":\"add\",\"to\":\"events\",\"file\":\"wiring.yml\",\"value\":{\"id\":\"evt:orphan\","
        "\"preset\":\"text\",\"source\":\"switch:none\",\"text\":\"x\"}}]")) == "result");
    std::vector<YAML::Node> orphan = issuesStarting(root, "nothing in the project has the id switch:none");
    REQUIRE(orphan.size() == 1);
    const YAML::Node fixes = orphan[0]["fixes"];
    REQUIRE(fixes.size() >= 1);
    CHECK(fixes[fixes.size() - 1]["label"].Scalar().find("remove evt:orphan") == 0);
    REQUIRE(kindOf(applyFix(root, orphan[0], fixes.size() - 1)) == "result");
    CHECK(issuesStarting(root, "nothing in the project has the id switch:none").empty());

    // The undeclared variable is declared (the lowering's check runs with the lowering, without assets too).
    const YAML::Node all = call("check.validate", "{\"project\":" + quoted(root) + ",\"use_assets\":false}");
    YAML::Node undeclared;

    for (const YAML::Node &issue : all["result"]["issues"])
    {
        if (issue["message"].Scalar().find("the variable chapel is not declared") == 0)
        {
            undeclared = issue;
        }
    }

    REQUIRE(undeclared.IsDefined());
    REQUIRE(kindOf(applyFix(root, undeclared)) == "result");
    CHECK(issuesStarting(root, "the variable chapel is not declared").empty());
    const YAML::Node variables = YAML::LoadFile((root / "wiring.yml").string())["variables"];
    REQUIRE(variables.IsSequence());
    CHECK(variables[0].Scalar() == "chapel");
}

TEST_CASE("S5b1 part two: a room that realises no plan space is fixed either way; validate leaves the schemas whole")
{
    const std::filesystem::path root = writeProject("plan");
    writeText(root / "plan.yml", "format: 0\nspaces:\n  - {id: room:a, kind: room}\n  - {id: space:vault, name: Vault, kind: room}\n");
    std::vector<YAML::Node> lonely = issuesStarting(root, "the room realises no space of plan.yml (room:b");
    REQUIRE(lonely.size() == 1);
    REQUIRE(lonely[0]["fixes"].size() == 2);
    CHECK(lonely[0]["fixes"][0]["label"].Scalar() == "make room:b the room of space:vault (Vault)");
    CHECK(lonely[0]["fixes"][1]["label"].Scalar() == "add room:b to the plan as a space");
    // After the validation (and its fixes) the operations still know every list: the regression where locating an
    // issue assigned into the built-in schema's nodes.
    REQUIRE(kindOf(apply(root, "[{\"op\":\"add\",\"to\":\"rooms\",\"value\":{\"outline\":[[1408,0],[1920,0],[1920,512],[1408,512]],"
        "\"floor\":0,\"ceiling\":384,\"space\":\"space:vault\"}}]")) == "result");
    const std::vector<YAML::Node> left = issuesStarting(root, "the room realises no space of plan.yml (room:b");
    REQUIRE(left.size() == 1);
    REQUIRE(left[0]["fixes"].size() == 1);
    REQUIRE(kindOf(applyFix(root, left[0])) == "result");
    CHECK(issuesStarting(root, "the room realises no space").empty());
}

TEST_CASE("S5b1 part two: view.layout_at draws the project as it was before and after an entry")
{
    const std::filesystem::path root = writeProject("ghost");
    REQUIRE(kindOf(apply(root, "[{\"op\":\"set\",\"id\":\"room:b\",\"file\":\"rooms.yml\",\"fields\":{\"ceiling\":448}}]")) == "result");
    REQUIRE(kindOf(apply(root, "[{\"op\":\"add\",\"to\":\"rooms\",\"value\":{\"id\":\"room:c\",\"outline\":[[1408,0],[1920,0],"
        "[1920,512],[1408,512]],\"floor\":0,\"ceiling\":384}}]")) == "result");
    const YAML::Node before = call("view.layout_at", "{\"project\":" + quoted(root) + ",\"sequence\":2}");
    REQUIRE(kindOf(before) == "result");
    CHECK(before["result"]["rooms"].size() == 2);
    CHECK(before["result"]["side"].Scalar() == "before");
    const YAML::Node after = call("view.layout_at", "{\"project\":" + quoted(root) + ",\"sequence\":2,\"side\":\"after\"}");
    REQUIRE(kindOf(after) == "result");
    CHECK(after["result"]["rooms"].size() == 3);
    const YAML::Node first = call("view.layout_at", "{\"project\":" + quoted(root) + ",\"sequence\":1}");
    REQUIRE(kindOf(first) == "result");

    for (const YAML::Node &room : first["result"]["rooms"])
    {
        if (room["id"].Scalar() == "room:b")
        {
            CHECK(room["ceiling"].as<int>() == 384);
        }
    }

    CHECK(kindOf(call("view.layout_at", "{\"project\":" + quoted(root) + ",\"sequence\":9}")) == "bad_request");
}

TEST_CASE("S5b1 part two: assets.search finds monsters, items and sounds by name when asked for them")
{
    const std::filesystem::path assets = OPENYAMM_DEV_ASSETS_DIR;

    if (!std::filesystem::is_directory(assets / "engine"))
    {
        MESSAGE("no asset root: skipped");
        return;
    }

    REQUIRE(kindOf(call("session.configure", "{\"asset_root\":" + quoted(assets) + "}")) == "result");
    const YAML::Node monsters = call("assets.search", "{\"query\":\"goblin\",\"kind\":\"monster\"}");
    REQUIRE(kindOf(monsters) == "result");
    CHECK(monsters["result"]["monsters"][0]["number"].as<int>() == 271);
    CHECK(monsters["result"]["monsters"][0]["name"].Scalar() == "Goblin");
    const YAML::Node items = call("assets.search", "{\"query\":\"longsword\",\"kind\":\"item\",\"limit\":1}");
    REQUIRE(kindOf(items) == "result");
    CHECK(items["result"]["items"][0]["number"].as<int>() == 1);
    CHECK(items["result"]["matches"].as<int>() >= 1);
    const YAML::Node sounds = call("assets.search", "{\"query\":\"waterdrip\",\"kind\":\"sound\",\"world\":\"mm6\"}");
    REQUIRE(kindOf(sounds) == "result");
    CHECK(sounds["result"]["sounds"][0]["name"].Scalar() == "waterdrip");
    // Without a kind: decorations and textures only, as before.
    const YAML::Node plain = call("assets.search", "{\"query\":\"goblin\"}");
    CHECK(!plain["result"]["monsters"]);
    call("session.configure", "{}");
}
