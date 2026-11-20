// Walk mode (S5a4; core/Walk.h): the build's movement state, a walk on the game's indoor controller through a door
// shut and then toggled open, the same poses from the same input, and the request list's walk.* methods.
#include "cli/Rpc.h"
#include "core/Walk.h"

#include <doctest/doctest.h>
#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <fstream>
#include <iterator>
#include <random>
#include <sstream>
#include <string>
#include <vector>

using namespace OpenYAMM::Studio;

namespace
{
const std::filesystem::path WalkAssets = OPENYAMM_DEV_ASSETS_DIR;

// Two rooms side by side, a door in the opening between them.
const char *WalkCard = "format: 0\nid: walktest\nname: Walk test\nworld: mm6\nkind: indoor\nprofile: dungeon\n"
                       "map_stats:\n  id: 9401\n  reference: 6d01.blv\n";
const char *WalkPlan =
    "format: 0\nspaces:\n  - {id: room:a, name: A, kind: room, size: M}\n"
    "  - {id: room:b, name: B, kind: room, size: M}\n";
const char *WalkRooms =
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
const char *WalkObjects =
    "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, speed: 96}\n";

std::filesystem::path builtWalkProject()
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s5a4_walk_" + std::to_string(std::random_device{}()));
    const auto write = [&root](const char *pName, const char *pText)
    {
        std::filesystem::create_directories(root);
        std::ofstream(root / pName, std::ios::binary) << pText;
    };
    write("project.yml", WalkCard);
    write("plan.yml", WalkPlan);
    write("rooms.yml", WalkRooms);
    write("objects.yml", WalkObjects);
    callRpcMethod("session.configure", "{\"asset_root\":\"" + WalkAssets.string() + "\"}");
    const YAML::Node built = YAML::Load(callRpcMethod("build.run",
        "{\"project\":\"" + root.string() + "\",\"dry_run\":false}"));
    REQUIRE_MESSAGE(built["result"].IsDefined(), callRpcMethod("build.run",
        "{\"project\":\"" + root.string() + "\",\"dry_run\":true}"));
    return root;
}

std::vector<uint8_t> readBytes(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    return std::vector<uint8_t>((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
}

std::string readText(const std::filesystem::path &path)
{
    const std::vector<uint8_t> bytes = readBytes(path);
    return std::string(bytes.begin(), bytes.end());
}

bool loadWalk(WalkSession &walk, const std::filesystem::path &build, std::string &error)
{
    return walk.load(readBytes(build / "walktest.blv"), readText(build / "walktest.walk.yml"),
        readText(WalkAssets / "engine" / "data_tables" / "decoration_data.txt"), {}, error);
}

WalkPose walkFor(WalkSession &walk, float yaw, uint32_t buttons, int frames)
{
    WalkPose pose = walk.pose();

    for (int frame = 0; frame < frames; ++frame)
    {
        pose = walk.step(yaw, buttons, 1.0f / 60.0f);
    }

    return pose;
}
}

TEST_CASE("S5a4: the build writes the walk's movement state: the studio's block, then the scene without its actors")
{
    if (!std::filesystem::is_directory(WalkAssets / "engine"))
    {
        MESSAGE("no asset root: skipped");
        return;
    }

    const std::filesystem::path root = builtWalkProject();
    const std::string text = readText(root / "build" / "walktest.walk.yml");
    REQUIRE(text.starts_with("studio_walk:\n"));
    const YAML::Node state = YAML::Load(text);
    CHECK(state["studio_walk"]["kind"].Scalar() == "indoor");
    CHECK(state["studio_walk"]["map"].Scalar() == "walktest.blv");
    CHECK(state["studio_walk"]["party"]["radius"].as<float>() == 37.0f);
    CHECK(state["studio_walk"]["party"]["eye_height"].as<float>() == 160.0f);
    REQUIRE(state["studio_walk"]["doors"].size() == 1);
    CHECK(state["studio_walk"]["doors"][0]["id"].Scalar() == "door:ab");
    CHECK(state["studio_walk"]["rooms"].size() == 2);
    // The game's scene, read by the walk with the game's own reader: its lists that movement never reads are empty.
    CHECK(state["kind"].Scalar() == "indoor_scene");
    CHECK(state["initial_state"]["actors"].size() == 0);
    CHECK(state["initial_state"]["doors"].size() == 1);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a4: the party walks into the shut door, through it once opened; the same input gives the same poses")
{
    if (!std::filesystem::is_directory(WalkAssets / "engine"))
    {
        MESSAGE("no asset root: skipped");
        return;
    }

    const std::filesystem::path root = builtWalkProject();
    const std::filesystem::path build = root / "build";
    WalkSession walk;
    std::string error;
    REQUIRE_MESSAGE(loadWalk(walk, build, error), error);
    CHECK_FALSE(walk.outdoor());
    REQUIRE(walk.doors().size() == 1);
    CHECK_FALSE(walk.doors()[0].open);

    // In room a, east toward the door: stopped short of it.
    WalkPose pose = walk.placeEye(256.0f, 256.0f, 160.0f);
    CHECK(walk.roomOfSector(pose.sector) == "room:a");
    CHECK(pose.footZ == doctest::Approx(0.0f));
    pose = walkFor(walk, 0.0f, WalkForward, 120);
    CHECK(pose.x < 512.0f);
    CHECK(pose.x > 400.0f);
    CHECK(walk.roomOfSector(pose.sector) == "room:a");

    // Opened, it lets the party through into room b.
    REQUIRE(walk.toggle("door:ab") == std::optional<bool>(true));
    pose = walkFor(walk, 0.0f, WalkForward, 120);
    CHECK(pose.x > 600.0f);
    CHECK(walk.roomOfSector(pose.sector) == "room:b");
    CHECK_FALSE(walk.toggle("door:nothing").has_value());

    // A turn, a run, a jump and a strafe, twice from the same place and once on a fresh walk with the door opened:
    // the same poses, bit for bit.
    const auto record = [](WalkSession &session)
    {
        std::string bits;
        session.placeEye(800.0f, 256.0f, 160.0f);

        for (int frame = 0; frame < 240; ++frame)
        {
            const uint32_t buttons = frame < 120 ? (WalkForward | WalkRun | (frame == 40 ? WalkJump : 0u))
                                                 : (WalkLeft | WalkBackward);
            bits += walkPoseBits(session.step(2.5f + float(frame) * 0.013f, buttons, 1.0f / 60.0f));
        }

        return bits;
    };
    const std::string first = record(walk);
    CHECK(first == record(walk));
    WalkSession again;
    REQUIRE(loadWalk(again, build, error));
    REQUIRE(again.toggle("door:ab") == std::optional<bool>(true));
    CHECK(record(again) == first);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a4: walk.* in the request list: a typed refusal before a walk, a load, a replay hash and a door")
{
    if (!std::filesystem::is_directory(WalkAssets / "engine"))
    {
        MESSAGE("no asset root: skipped");
        return;
    }

    const std::filesystem::path root = builtWalkProject();
    const std::string build = (root / "build").string();
    const std::string decorations = (WalkAssets / "engine" / "data_tables" / "decoration_data.txt").string();
    const std::string loadParams = "{\"map\":\"" + build + "/walktest.blv\",\"state\":\"" + build
        + "/walktest.walk.yml\",\"decorations\":\"" + decorations + "\"}";
    YAML::Node answer = YAML::Load(callRpcMethod("walk.load", loadParams));
    REQUIRE(answer["result"].IsDefined());
    CHECK(answer["result"]["kind"].Scalar() == "indoor");
    CHECK(answer["result"]["doors"][0]["id"].Scalar() == "door:ab");

    const std::string replay = "{\"eye\":[256,256,160],\"frames\":[[0,1,0.0166],[0,1,0.0166],[0.5,17,0.0166],"
        "[0.5,33,0.02],[1,4,0.0166]],\"toggles\":[{\"frame\":1,\"door\":\"door:ab\"}],\"trace_every\":2}";
    const YAML::Node first = YAML::Load(callRpcMethod("walk.replay", replay));
    REQUIRE(first["result"].IsDefined());
    CHECK(first["result"]["frames"].as<int>() == 5);
    CHECK(first["result"]["trace"].size() == 3);
    // The same replay on a fresh walk gives the same hash.
    REQUIRE(YAML::Load(callRpcMethod("walk.load", loadParams))["result"].IsDefined());
    const YAML::Node second = YAML::Load(callRpcMethod("walk.replay", replay));
    CHECK(second["result"]["hash"].Scalar() == first["result"]["hash"].Scalar());

    answer = YAML::Load(callRpcMethod("walk.toggle", "{\"door\":\"door:nothing\"}"));
    CHECK(answer["error"]["data"]["kind"].Scalar() == "no_such_object");
    answer = YAML::Load(callRpcMethod("walk.load",
        "{\"map\":\"" + build + "/nothing.blv\",\"state\":\"x\",\"decorations\":\"y\"}"));
    CHECK(answer["error"]["data"]["kind"].Scalar() == "bad_request");
    callRpcMethod("session.configure", "{}");
    std::filesystem::remove_all(root);
}
