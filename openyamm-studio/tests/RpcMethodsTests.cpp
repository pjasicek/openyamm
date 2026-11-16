// The request list's methods of the MCP tools that ran command lines until S5a3 (cli/Rpc.cpp): project.new,
// project.query, edit.undo and edit.redo, session.schema, the reading methods (check.audit, check.solve,
// check.flow_event, view.render), assets.*, build.install, and host methods the core does not serve.
#include "doctest/doctest.h"

#include "cli/Rpc.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <random>
#include <string>

using namespace OpenYAMM::Studio;

namespace
{
const char *CardText = "format: 0\nid: rpctest\nname: Rpc test\nworld: mm6\nkind: indoor\nprofile: dungeon\n"
                       "map_stats:\n  id: 9400\n  reference: 6d01.blv\n";
const char *PlanText =
    "format: 0\nspaces:\n  - {id: room:a, name: A, kind: room, size: M}\n  - {id: room:b, name: B, kind: room, size: M}\n";
const char *RoomsText =
    "format: 0\n"
    "themes:\n"
    "  - id: theme:plain\n"
    "    wall: {texture: t1w11a, size: [128, 256]}\n"
    "    floor: {texture: oflr, size: [128, 128]}\n"
    "    ceiling: {texture: d2ceil4, size: [256, 256]}\n"
    "defaults: {theme: theme:plain}\n"
    "rooms:\n"
    "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
    "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 384}\n"
    "openings:\n"
    "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
const char *ObjectsText =
    "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, speed: 96}\n";
const char *LockText = "format: 0\ndoors:\n  door:ab: 1\n";

std::filesystem::path scratchFolder(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s5a3_rpc_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

void writeText(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

std::filesystem::path writeProject(const std::string &name)
{
    const std::filesystem::path root = scratchFolder(name);
    writeText(root / "project.yml", CardText);
    writeText(root / "plan.yml", PlanText);
    writeText(root / "rooms.yml", RoomsText);
    writeText(root / "objects.yml", ObjectsText);
    writeText(root / "ids.lock.yml", LockText);
    return root;
}

// One call; the answer as a tree ({result} or {error}).
YAML::Node call(const std::string &method, const std::string &params)
{
    return YAML::Load(callRpcMethod(method, params));
}

std::string quoted(const std::filesystem::path &path)
{
    return "\"" + path.string() + "\"";
}

std::string kindOf(const YAML::Node &answer)
{
    return answer["error"] ? answer["error"]["data"]["kind"].Scalar() : std::string("result");
}

const std::filesystem::path DevAssets = OPENYAMM_DEV_ASSETS_DIR;
}

TEST_CASE("S5a3: project.new makes a project project.query reads; a second one in the folder is refused")
{
    const std::filesystem::path root = scratchFolder("new") / "crypt";
    const YAML::Node made = call("project.new",
        "{\"project\":" + quoted(root) + ",\"id\":\"crypt01\",\"name\":\"The Crypt\",\"stats_id\":9401}");
    REQUIRE(kindOf(made) == "result");
    CHECK(made["result"]["files"].size() == 5);
    CHECK(made["result"]["revision"].Scalar().size() == 32);
    CHECK(std::filesystem::is_regular_file(root / "rooms.yml"));

    const YAML::Node summary = call("project.query", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(summary) == "result");
    CHECK(summary["result"]["revision"].Scalar() == made["result"]["revision"].Scalar());
    CHECK(summary["result"]["card"]["id"].Scalar() == "crypt01");
    CHECK(summary["result"]["card"]["name"].Scalar() == "The Crypt");
    CHECK(summary["result"]["files"]["rooms.yml"]["themes"][0].Scalar() == "theme:masonry");

    const YAML::Node again = call("project.new",
        "{\"project\":" + quoted(root) + ",\"id\":\"crypt02\",\"name\":\"Another\"}");
    CHECK(kindOf(again) == "bad_request");
    // The refusal names no path.
    CHECK(again["error"]["message"].Scalar().find(root.string()) == std::string::npos);
    CHECK(kindOf(call("project.new", "{\"project\":" + quoted(root) + ",\"id\":\"Bad Id\",\"name\":\"x\"}"))
        == "invalid_params");
    std::filesystem::remove_all(root.parent_path());
}

TEST_CASE("S5a3: project.query reads an object with its engine number, a list, and needs the file of a shared id")
{
    const std::filesystem::path root = writeProject("query");
    const std::string project = "\"project\":" + quoted(root);

    const YAML::Node door = call("project.query", "{" + project + ",\"id\":\"door:ab\"}");
    REQUIRE(kindOf(door) == "result");
    CHECK(door["result"]["file"].Scalar() == "objects.yml");
    CHECK(door["result"]["list"].Scalar() == "doors");
    CHECK(door["result"]["object"]["speed"].as<int>() == 96);
    CHECK(door["result"]["number"].as<int>() == 1);
    CHECK(door["result"]["number_of"].Scalar() == "doors");

    // room:a is a plan space and a room: ids are unique per file.
    CHECK(kindOf(call("project.query", "{" + project + ",\"id\":\"room:a\"}")) == "bad_request");
    const YAML::Node room = call("project.query", "{" + project + ",\"id\":\"room:a\",\"file\":\"rooms.yml\"}");
    REQUIRE(kindOf(room) == "result");
    CHECK(room["result"]["object"]["ceiling"].as<int>() == 384);
    CHECK_FALSE(room["result"]["number"]);

    const YAML::Node rooms = call("project.query", "{" + project + ",\"list\":\"rooms\"}");
    REQUIRE(kindOf(rooms) == "result");
    CHECK(rooms["result"]["items"].size() == 2);

    CHECK(kindOf(call("project.query", "{" + project + ",\"id\":\"door:nothing\"}")) == "no_such_object");
    CHECK(kindOf(call("project.query", "{" + project + ",\"list\":\"nothing\"}")) == "no_such_object");
    CHECK(kindOf(call("project.query", "{" + project + ",\"id\":\"door:ab\",\"list\":\"doors\"}")) == "bad_request");
    CHECK(kindOf(call("project.query", "{\"project\":" + quoted(root / "nothing") + "}")) == "not_a_project");
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a3: edit.undo and edit.redo step the history, refuse at its ends and leave no edit outside the tool")
{
    const std::filesystem::path root = writeProject("undo");
    const std::string project = "\"project\":" + quoted(root);
    const std::string before = call("project.status", "{" + project + "}")["result"]["revision"].Scalar();
    CHECK(kindOf(call("edit.undo", "{" + project + "}")) == "nothing_to_undo");

    const YAML::Node edited = call("edit.apply", "{" + project
        + ",\"ops\":[{\"op\":\"set\",\"id\":\"door:ab\",\"fields\":{\"speed\":64}}]}");
    REQUIRE(kindOf(edited) == "result");
    const std::string after = edited["result"]["revision_after"].Scalar();
    CHECK(after != before);

    const YAML::Node undone = call("edit.undo", "{" + project + "}");
    REQUIRE(kindOf(undone) == "result");
    CHECK(undone["result"]["revision"].Scalar() == before);
    REQUIRE(undone["result"]["changes"].size() == 1);
    // An undo is an entry of its own that reverts the edit (S5b1): its change is the way back.
    CHECK(undone["result"]["changes"][0].Scalar() == "undone: objects.yml: door:ab changed speed (64 -> 96)");
    CHECK(call("project.query", "{" + project + ",\"id\":\"door:ab\"}")["result"]["object"]["speed"].as<int>() == 96);

    const YAML::Node redone = call("edit.redo", "{" + project + "}");
    REQUIRE(kindOf(redone) == "result");
    CHECK(redone["result"]["revision"].Scalar() == after);
    CHECK(kindOf(call("edit.redo", "{" + project + "}")) == "nothing_to_undo");

    // The steps are the core's own: the history head is at them, so nothing is recorded as an outside edit.
    const YAML::Node status = call("project.status", "{" + project + "}");
    CHECK(status["result"]["outside_changes"].size() == 0);
    CHECK(kindOf(call("edit.undo", "{\"project\":" + quoted(root / "nothing") + "}")) == "not_a_project");
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a3: session.schema lists the format's schemas and returns one; host methods are not the core's")
{
    const YAML::Node list = call("session.schema", "{}");
    REQUIRE(kindOf(list) == "result");
    bool rooms = false;

    for (const YAML::Node &schema : list["result"]["schemas"])
    {
        rooms = rooms || schema["name"].Scalar() == "rooms.schema.json";
    }

    CHECK(rooms);
    const YAML::Node pins = call("session.schema", "{\"name\":\"pins\"}");
    REQUIRE(kindOf(pins) == "result");
    CHECK(pins["result"]["name"].Scalar() == "pins.schema.json");
    CHECK(pins["result"]["schema"]["properties"]["pins"]["type"].Scalar() == "array");
    CHECK(kindOf(call("session.schema", "{\"name\":\"nothing\"}")) == "bad_request");

    // game.playtest is answered by the host: the core neither lists nor serves it.
    CHECK(kindOf(call("game.playtest", "{\"scenario\":\"x.yml\",\"world\":\"mm6\"}")) == "unknown_method");
    bool listed = false;

    for (const YAML::Node &method : call("session.hello", "{}")["result"]["methods"])
    {
        listed = listed || method.Scalar() == "game.playtest";
    }

    CHECK_FALSE(listed);
}

TEST_CASE("S5a3: the reading methods and install refuse without an asset root or a mount, typed")
{
    const std::filesystem::path root = writeProject("refusals");
    REQUIRE(kindOf(call("session.configure", "{}")) == "result");

    for (const char *pMethod : {"check.audit", "check.solve", "view.render"})
    {
        CHECK(kindOf(call(pMethod, "{\"map\":" + quoted(root) + "}")) == "no_asset_root");
    }

    CHECK(kindOf(call("check.flow_event", "{\"map\":" + quoted(root) + ",\"event\":1}")) == "no_asset_root");
    CHECK(kindOf(call("assets.search", "{\"query\":\"torch\"}")) == "no_asset_root");
    CHECK(kindOf(call("assets.script_reference", "{}")) == "no_asset_root");
    CHECK(kindOf(call("build.install", "{\"project\":" + quoted(root) + "}")) == "no_asset_root");

    if (std::filesystem::is_directory(DevAssets / "engine"))
    {
        REQUIRE(kindOf(call("session.configure", "{\"asset_root\":" + quoted(DevAssets) + "}")) == "result");
        CHECK(kindOf(call("build.install", "{\"project\":" + quoted(root) + "}")) == "no_mount");
        CHECK(kindOf(call("check.audit", "{\"map\":" + quoted(root) + ",\"built\":true}")) == "no_mount");
        const YAML::Node missing = call("check.solve", "{\"map\":\"nothing.blv\",\"world\":\"mm6\"}");
        CHECK(kindOf(missing) == "no_such_map");
        const YAML::Node world = call("check.solve", "{\"map\":\"6d01.blv\",\"world\":\"mm77\"}");
        CHECK(kindOf(world) == "bad_request");
        // Messages name the asset root in words, not by its path.
        CHECK(world["error"]["message"].Scalar().find(DevAssets.string()) == std::string::npos);
        call("session.configure", "{}");
    }

    std::filesystem::remove_all(root);
}

TEST_CASE("S5a3: flow, solve, render and install read a project built privately, and the mount is the session's")
{
    if (!std::filesystem::is_directory(DevAssets / "engine"))
    {
        MESSAGE("no asset root at " << DevAssets.string() << ": skipped");
        return;
    }

    const std::filesystem::path root = writeProject("reading");
    const std::filesystem::path mount = root.string() + "_mount";
    REQUIRE(kindOf(call("session.configure", "{\"asset_root\":" + quoted(DevAssets) + "}")) == "result");

    const YAML::Node solved = call("check.solve", "{\"map\":" + quoted(root) + "}");
    REQUIRE(kindOf(solved) == "result");
    CHECK(solved["result"]["map"].Scalar() == "rpctest.blv");
    CHECK(solved["result"]["sector_rooms"]["1"].IsDefined());

    // The project has no handlers: the flow of any event is refused, typed.
    CHECK(kindOf(call("check.flow_event", "{\"map\":" + quoted(root) + ",\"event\":1}")) == "no_such_object");

    const YAML::Node picture = call("view.render", "{\"map\":" + quoted(root) + ",\"size\":128}");
    REQUIRE(kindOf(picture) == "result");
    CHECK(picture["result"]["map"].Scalar() == "rpctest.blv");
    CHECK(picture["result"]["png_base64"].Scalar().starts_with("iVBORw0KGgo"));
    CHECK(std::max(picture["result"]["width"].as<int>(), picture["result"]["height"].as<int>()) == 128);

    // Install needs the project's build and the session's mount; the reading methods then find the map with
    // `built` only.
    REQUIRE(kindOf(call("build.run", "{\"project\":" + quoted(root) + ",\"dry_run\":false}")) == "result");
    REQUIRE(kindOf(call("session.configure",
                "{\"asset_root\":" + quoted(DevAssets) + ",\"mount\":" + quoted(mount) + "}")) == "result");
    const YAML::Node installed = call("build.install", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(installed) == "result");
    CHECK(std::filesystem::is_regular_file(mount / "worlds" / "mm6" / "maps" / "rpctest.blv"));
    const YAML::Node audit = call("check.audit", "{\"map\":\"rpctest.blv\",\"world\":\"mm6\",\"built\":true}");
    REQUIRE(kindOf(audit) == "result");
    CHECK(audit["result"]["overview"]["doors"].as<int>() == 1);
    CHECK(kindOf(call("check.audit", "{\"map\":\"rpctest.blv\",\"world\":\"mm6\"}")) == "no_such_map");

    call("session.configure", "{}");
    std::filesystem::remove_all(root);
    std::filesystem::remove_all(mount);
}

TEST_CASE("S5c: session.release drops what the core keeps of a project; the next call reads it again")
{
    const std::filesystem::path root = writeProject("release");
    const YAML::Node opened = call("project.open", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(opened) == "result");

    const YAML::Node released = call("session.release", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(released) == "result");
    CHECK(released["result"]["released"].as<bool>());
    CHECK_FALSE(call("session.release", "{\"project\":" + quoted(root) + "}")["result"]["released"].as<bool>());

    // Nothing on disk changed: the project opens again at the same revision.
    const YAML::Node again = call("project.open", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(again) == "result");
    CHECK(again["result"]["revision"].Scalar() == opened["result"]["revision"].Scalar());
    CHECK(kindOf(call("session.release", "{}")) == "invalid_params");
    std::filesystem::remove_all(root);
}
