// S5a5's methods of the request list (cli/Rpc.cpp): check.audit with `solve` (one walk for the audit's questions and
// the solve), compare.run, view.original_mesh, pins.tour, and the reading commands that left map_exec's command
// line (check.metrics, check.probe, project.import, project.fmt, view.render_sketch).
#include "doctest/doctest.h"

#include "cli/Rpc.h"
#include "core/View.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <fstream>
#include <random>
#include <string>

using namespace OpenYAMM::Studio;

namespace
{
const std::filesystem::path DevAssets = OPENYAMM_DEV_ASSETS_DIR;

// Two box rooms and a door, a rebuild of nothing in particular: its card names Goblinwatch as its original.
const char *CardText = "format: 0\nid: s5a5test\nname: Scorecard test\nworld: mm6\nkind: indoor\nprofile: dungeon\n"
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
const char *PinsText =
    "format: 1\ncounter: 3\npins:\n"
    "  - id: pin:p1\n    text: The door sticks.\n    on: door:ab\n    source: game\n    map: s5a5test.blv\n"
    "    world: mm6\n    author: user\n    status: open\n"
    "    pose: {position: [256, 256.5, 0], yaw_radians: 1.5708, pitch_degrees: -3, heading_yaw_units: 512}\n"
    "  - id: pin:p2\n    text: No pose.\n    at: [700, 100, 0]\n    source: studio\n    author: user\n"
    "    status: open\n"
    "  - id: pin:p3\n    text: Done.\n    on: door:ab\n    source: game\n    map: s5a5test.blv\n    world: mm6\n"
    "    author: user\n    status: accepted\n"
    "    pose: {position: [800, 256, 0], yaw_radians: 0, pitch_degrees: 0, heading_yaw_units: 0}\n";

std::filesystem::path scratchFolder(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s5a5_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

void writeText(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

std::filesystem::path writeProject(const std::string &name, bool withReference = true)
{
    const std::filesystem::path root = scratchFolder(name);
    std::string card = CardText;

    if (!withReference)
    {
        // A new map: its encounter slots in full instead of a shipped map's row (and so no original).
        card = card.substr(0, card.find("  reference:"))
            + "  slots:\n    - {monster: Rat, tier: 1, per_marker: [2, 3], weight: 100}\n";
    }

    writeText(root / "project.yml", card);
    writeText(root / "plan.yml", PlanText);
    writeText(root / "rooms.yml", RoomsText);
    writeText(root / "objects.yml", ObjectsText);
    writeText(root / "ids.lock.yml", LockText);
    writeText(root / "review" / "pins.yml", PinsText);
    return root;
}

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

bool haveAssets()
{
    if (!std::filesystem::is_directory(DevAssets / "engine"))
    {
        MESSAGE("no asset root at " << DevAssets.string() << ": skipped");
        return false;
    }

    return true;
}
}

TEST_CASE("S5a5: the new reading methods refuse without an asset root, typed")
{
    const std::filesystem::path root = writeProject("refusals");
    REQUIRE(kindOf(call("session.configure", "{}")) == "result");
    CHECK(kindOf(call("compare.run", "{\"map\":" + quoted(root) + "}")) == "no_asset_root");
    CHECK(kindOf(call("view.original_mesh", "{\"project\":" + quoted(root) + "}")) == "no_asset_root");
    CHECK(kindOf(call("check.metrics", "{\"map\":" + quoted(root) + "}")) == "no_asset_root");
    CHECK(kindOf(call("check.probe", "{\"map\":" + quoted(root) + ",\"from\":[1,2,3],\"to\":[4,5,6]}"))
        == "no_asset_root");
    CHECK(kindOf(call("project.import", "{\"project\":" + quoted(root / "imported")
                    + ",\"map\":\"6d01.blv\",\"world\":\"mm6\"}")) == "no_asset_root");
    // Params are checked against the schemas first.
    CHECK(kindOf(call("check.probe", "{\"map\":" + quoted(root) + ",\"from\":[1,2]}")) == "invalid_params");
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a5: pins.tour gives the shots at the pins' poses by status, and names the pins without one")
{
    const std::filesystem::path root = writeProject("tour");
    const YAML::Node tour = call("pins.tour", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(tour) == "result");
    CHECK(tour["result"]["map"].Scalar() == "s5a5test.blv");
    CHECK(tour["result"]["world"].Scalar() == "mm6");
    REQUIRE(tour["result"]["shots"].size() == 1);
    const YAML::Node shot = tour["result"]["shots"][0];
    CHECK(shot["pin"].Scalar() == "pin:p1");
    CHECK(shot["name"].Scalar() == "p1");
    CHECK(shot["position"][1].as<double>() == doctest::Approx(256.5));
    CHECK(shot["yaw_radians"].as<double>() == doctest::Approx(1.5708));
    // The pin keeps `loc`'s degrees; the tour takes radians.
    CHECK(shot["pitch_radians"].as<double>() == doctest::Approx(-3.0 * 3.14159265358979 / 180.0).epsilon(1e-5));
    REQUIRE(tour["result"]["skipped"].size() == 1);
    CHECK(tour["result"]["skipped"][0].Scalar() == "pin:p2");

    const YAML::Node accepted = call("pins.tour", "{\"project\":" + quoted(root) + ",\"status\":[\"accepted\"]}");
    REQUIRE(kindOf(accepted) == "result");
    REQUIRE(accepted["result"]["shots"].size() == 1);
    CHECK(accepted["result"]["shots"][0]["pin"].Scalar() == "pin:p3");

    const YAML::Node one = call("pins.tour", "{\"project\":" + quoted(root) + ",\"pins\":[\"pin:p3\"]}");
    REQUIRE(kindOf(one) == "result");
    CHECK(one["result"]["shots"].size() == 1);
    CHECK(kindOf(call("pins.tour", "{\"project\":" + quoted(root / "nothing") + "}")) == "not_a_project");
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a5: check.audit with solve gives the solve check.solve gives, from one walk")
{
    if (!haveAssets())
    {
        return;
    }

    const std::filesystem::path root = writeProject("auditsolve");
    REQUIRE(kindOf(call("session.configure", "{\"asset_root\":" + quoted(DevAssets) + "}")) == "result");
    const YAML::Node audit = call("check.audit", "{\"map\":" + quoted(root) + ",\"reach\":true,\"solve\":true}");
    REQUIRE(kindOf(audit) == "result");
    REQUIRE(audit["result"]["solve"].IsMap());
    const YAML::Node solved = call("check.solve", "{\"map\":" + quoted(root) + "}");
    REQUIRE(kindOf(solved) == "result");
    // The same answer, member for member.
    CHECK(YAML::Dump(audit["result"]["solve"]) == YAML::Dump(solved["result"]));
    CHECK(audit["result"]["solve"]["sector_rooms"]["1"].IsDefined());

    // Without `solve` the audit has no solve, and its findings are the same.
    const YAML::Node plain = call("check.audit", "{\"map\":" + quoted(root) + ",\"reach\":true}");
    REQUIRE(kindOf(plain) == "result");
    CHECK_FALSE(plain["result"]["solve"].IsDefined());
    CHECK(YAML::Dump(plain["result"]["findings"]) == YAML::Dump(audit["result"]["findings"]));
    call("session.configure", "{}");
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a5: compare.run measures a project against its original, or refuses a map without one")
{
    if (!haveAssets())
    {
        return;
    }

    const std::filesystem::path root = writeProject("compare");
    const std::filesystem::path fresh = writeProject("compare_new", false);
    REQUIRE(kindOf(call("session.configure", "{\"asset_root\":" + quoted(DevAssets) + "}")) == "result");
    const YAML::Node compared = call("compare.run", "{\"map\":" + quoted(root) + "}");
    REQUIRE(kindOf(compared) == "result");
    const YAML::Node result = compared["result"];
    CHECK(result["kind"].Scalar() == "indoor");
    CHECK(result["original"].Scalar() == "6d01.blv");
    CHECK(result["rebuilt"].Scalar() == "s5a5test.blv");
    CHECK(result["world"].Scalar() == "mm6");
    // Two box rooms are no Goblinwatch.
    CHECK(result["score"].as<double>() < 0.97);
    CHECK(result["band"]["at_least"].as<double>() == doctest::Approx(0.97));
    CHECK_FALSE(result["band"]["within"].as<bool>());
    REQUIRE(result["parts"].size() == 3);
    CHECK(result["parts"][0]["id"].Scalar() == "shape");
    CHECK(result["parts"][2]["weight"].as<double>() == 0.0);
    // The score is the parts' weighted sum.
    const double weighted = result["parts"][0]["score"].as<double>() * 0.7
        + result["parts"][1]["score"].as<double>() * 0.3;
    CHECK(result["score"].as<double>() == doctest::Approx(weighted).epsilon(0.002));
    REQUIRE(result["heat"]["points"].size() > 0);
    CHECK(result["heat"]["cell"].as<int>() == 256);
    CHECK(result["heat"]["points"][0].size() == 3);
    CHECK(result["worst"].size() <= 40);
    CHECK(result["report"]["totals"]["score"].IsDefined());

    // A new map names no original: refused unless one is given.
    const YAML::Node none = call("compare.run", "{\"map\":" + quoted(fresh) + "}");
    CHECK(kindOf(none) == "bad_request");
    const YAML::Node given = call("compare.run", "{\"map\":" + quoted(fresh) + ",\"original\":\"6d01.blv\"}");
    CHECK(kindOf(given) == "result");
    CHECK(kindOf(call("compare.run", "{\"map\":" + quoted(root) + ",\"original\":\"nothing.blv\"}"))
        == "no_such_map");
    // An outdoor original against an indoor rebuild.
    CHECK(kindOf(call("compare.run", "{\"map\":" + quoted(root) + ",\"original\":\"oute3.odm\"}")) == "bad_request");
    call("session.configure", "{}");
    std::filesystem::remove_all(root);
    std::filesystem::remove_all(fresh);
}

TEST_CASE("S5a5: view.original_mesh writes the original's mesh beside the project's views, once per map")
{
    if (!haveAssets())
    {
        return;
    }

    const std::filesystem::path root = writeProject("original");
    const std::filesystem::path fresh = writeProject("original_new", false);
    REQUIRE(kindOf(call("session.configure", "{\"asset_root\":" + quoted(DevAssets) + "}")) == "result");
    const YAML::Node mesh = call("view.original_mesh", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(mesh) == "result");
    CHECK(mesh["result"]["original"].Scalar() == "6d01.blv");
    CHECK(mesh["result"]["kind"].Scalar() == "indoor");
    const std::string file = mesh["result"]["file"].Scalar();
    CHECK(file.starts_with(".oymap/view/"));
    CHECK(file.find("-original-") != std::string::npos);
    REQUIRE(std::filesystem::is_regular_file(root / file));
    CHECK(std::filesystem::file_size(root / file) == mesh["result"]["bytes"].as<uint64_t>());
    CHECK(mesh["result"]["counts"]["faces"].as<int>() > 1000);
    // Owned by sectors, with no file.
    bool sectors = false;

    for (const YAML::Node &owner : mesh["result"]["owners"])
    {
        sectors = sectors || owner["id"].Scalar().starts_with("sector:");
        CHECK_FALSE(owner["file"].IsDefined());
    }

    CHECK(sectors);
    // A second call gives the same file (kept), and writes it again when it was removed.
    std::filesystem::remove(root / file);
    const YAML::Node again = call("view.original_mesh", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(again) == "result");
    CHECK(again["result"]["file"].Scalar() == file);
    CHECK(std::filesystem::is_regular_file(root / file));
    CHECK(kindOf(call("view.original_mesh", "{\"project\":" + quoted(fresh) + "}")) == "bad_request");
    const YAML::Node other =
        call("view.original_mesh", "{\"project\":" + quoted(fresh) + ",\"original\":\"6d16.blv\"}");
    REQUIRE(kindOf(other) == "result");
    CHECK(other["result"]["original"].Scalar() == "6d16.blv");
    call("session.configure", "{}");
    std::filesystem::remove_all(root);
    std::filesystem::remove_all(fresh);
}

TEST_CASE("S5a5: metrics, probe, import and fmt answer as their command lines do")
{
    const std::filesystem::path root = writeProject("commands");
    const YAML::Node fmt = call("project.fmt", "{\"project\":" + quoted(root) + ",\"check\":true}");
    REQUIRE(kindOf(fmt) == "result");
    CHECK(fmt["result"]["checked_only"].as<bool>());

    for (const YAML::Node &file : fmt["result"]["not_canonical"])
    {
        // Named, not rewritten.
        CHECK_FALSE(file.Scalar().empty());
    }

    const YAML::Node written = call("project.fmt", "{\"project\":" + quoted(root) + "}");
    REQUIRE(kindOf(written) == "result");
    const YAML::Node after = call("project.fmt", "{\"project\":" + quoted(root) + ",\"check\":true}");
    REQUIRE(kindOf(after) == "result");
    CHECK(after["result"]["not_canonical"].size() == 0);
    CHECK(kindOf(call("view.render_sketch", "{\"project\":" + quoted(root) + "}")) == "bad_request");

    if (!haveAssets())
    {
        std::filesystem::remove_all(root);
        return;
    }

    REQUIRE(kindOf(call("session.configure", "{\"asset_root\":" + quoted(DevAssets) + "}")) == "result");
    const YAML::Node metrics = call("check.metrics", "{\"map\":" + quoted(root) + "}");
    REQUIRE(kindOf(metrics) == "result");
    CHECK(metrics["result"]["map"].Scalar() == "s5a5test.blv");
    CHECK(metrics["result"]["metrics"]["scale"]["sector_floor_area"]["count"].as<int>() == 2);
    const YAML::Node probe =
        call("check.probe", "{\"map\":" + quoted(root) + ",\"from\":[256,256,0],\"to\":[832,256,0],\"doors_open\":true}");
    REQUIRE(kindOf(probe) == "result");
    CHECK(probe["result"]["lines"].size() > 2);
    const std::filesystem::path imported = root.string() + "_imported";
    const YAML::Node import =
        call("project.import", "{\"project\":" + quoted(imported) + ",\"map\":\"6d01.blv\",\"world\":\"mm6\"}");
    REQUIRE(kindOf(import) == "result");
    CHECK(import["result"]["map"].Scalar() == "6d01.blv");
    CHECK(std::filesystem::is_regular_file(imported / "project.yml"));
    bool namesCard = false;

    for (const YAML::Node &file : import["result"]["written"])
    {
        namesCard = namesCard || file.Scalar() == "project.yml";
    }

    CHECK(namesCard);
    // The folder holds a project now.
    CHECK(kindOf(call("project.import", "{\"project\":" + quoted(imported) + ",\"map\":\"6d01.blv\",\"world\":\"mm6\"}"))
        == "bad_request");
    call("session.configure", "{}");
    std::filesystem::remove_all(root);
    std::filesystem::remove_all(imported);
}

TEST_CASE("S5a5: a shipped indoor map's view mesh leaves out portals and invisible faces and owns faces by sector")
{
    OpenYAMM::Game::IndoorMapData map;
    map.vertices = {{0, 0, 0}, {100, 0, 0}, {100, 100, 0}, {0, 100, 0}};
    OpenYAMM::Game::IndoorFace floor;
    floor.vertexIndices = {0, 1, 2, 3};
    floor.textureUs = {0, 100, 100, 0};
    floor.textureVs = {0, 0, 100, 100};
    floor.textureName = "OFLR";
    floor.roomNumber = 3;
    OpenYAMM::Game::IndoorFace portal = floor;
    portal.isPortal = true;
    OpenYAMM::Game::IndoorFace hidden = floor;
    hidden.attributes = 0x00002000;
    map.faces = {floor, portal, hidden};
    const ViewMesh mesh = shippedIndoorViewMesh(map, LiquidTextures{});
    CHECK(mesh.faces == 1);
    CHECK(mesh.triangles == 2);
    REQUIRE(mesh.groups.size() == 1);
    CHECK(mesh.groups[0].texture == "oflr");
    REQUIRE(mesh.owners.size() == 2);
    CHECK(mesh.owners[1].id == "sector:3");
    CHECK(mesh.owners[1].file.empty());
}
