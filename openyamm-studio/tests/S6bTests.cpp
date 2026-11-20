// S6, the second run (devdocs/map_studio/S6_PLAN.md, "what remains"): leaning ladders (item L), mod.pack and mod.list
// in the request list with map numbers proposed from the declared ranges (item M), the world view (2.9), terrain for
// new open-air maps (item S) and the Overlay tab's own tools' operations (item O).
#include "doctest/doctest.h"

#include "cli/Rpc.h"
#include "game/FaceEnums.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <random>
#include <string>
#include <optional>
#include <vector>

using namespace OpenYAMM::Studio;
namespace Game = OpenYAMM::Game;

namespace
{
const std::filesystem::path S6bAssets = OPENYAMM_DEV_ASSETS_DIR;

bool haveMm6Root()
{
    return std::filesystem::is_regular_file(S6bAssets / "worlds" / "mm6" / "world.yml");
}

std::filesystem::path s6bScratch(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s6b_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

void s6bWrite(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

std::vector<uint8_t> s6bBytes(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::vector<uint8_t>((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
}

std::string s6bRead(const std::filesystem::path &path)
{
    const std::vector<uint8_t> bytes = s6bBytes(path);
    return std::string(bytes.begin(), bytes.end());
}

// A request-list call; the answer's `result` (undefined on a refusal, whose error is in `error`).
YAML::Node s6bCall(const std::string &method, const std::string &params, YAML::Node *pError = nullptr)
{
    const YAML::Node answer = YAML::Load(callRpcMethod(method, params));

    if (pError != nullptr && answer["error"])
    {
        *pError = answer["error"];
    }

    return answer["result"];
}

std::string quoted(const std::filesystem::path &path)
{
    return "\"" + path.generic_string() + "\"";
}

// A hall with a loft 256 up along its north side (y 768 to 1024), and a ladder of `ladder`'s words up to it.
std::filesystem::path loftProject(const std::string &name, const std::string &ladder, int statsId = 9471,
    const std::string &id = "lofttest")
{
    const std::filesystem::path root = s6bScratch(name);
    s6bWrite(root / "project.yml", "format: 0\nid: " + id + "\nname: Loft test\nworld: mm6\nkind: indoor\nprofile: "
        "dungeon\nmap_stats:\n  id: " + std::to_string(statsId) + "\n  reference: 6d01.blv\n");
    s6bWrite(root / "plan.yml", "format: 0\nspaces:\n  - {id: room:hall, name: Hall, kind: room, size: M}\n");
    s6bWrite(root / "rooms.yml",
        "format: 0\n"
        "themes:\n"
        "  - id: theme:plain\n"
        "    wall: {texture: t1w11a, size: [128, 256]}\n"
        "    floor: {texture: oflr, size: [128, 128]}\n"
        "    ceiling: {texture: d2ceil4, size: [256, 256]}\n"
        "defaults: {theme: theme:plain}\n"
        "rooms:\n"
        "  - id: room:hall\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 640\n"
        "    platforms:\n"
        "      - {at: [512, 896], size: [1024, 256], rise: 256}\n");
    s6bWrite(root / "objects.yml", "format: 0\nstart: {room: room:hall, at: [512, 300], facing: n}\nladders:\n  - "
        + ladder + "\n");
    return root;
}

YAML::Node buildRun(const std::filesystem::path &root)
{
    s6bCall("session.configure", "{\"asset_root\":" + quoted(S6bAssets) + "}");
    YAML::Node error;
    const YAML::Node built = s6bCall("build.run", "{\"project\":" + quoted(root) + ",\"dry_run\":false}", &error);
    INFO((error.IsDefined() ? YAML::Dump(error) : std::string()));
    CHECK(error.IsNull());
    return built;
}
}

TEST_CASE("S6 L: a leaning ladder: its top on the plan, its exit beyond the top, rails along the line")
{
    if (!haveMm6Root())
    {
        MESSAGE("no MM6 world in the development assets: skipped");
        return;
    }

    // Upright first: the top straight over the foot (what every project without `top_at` keeps).
    const std::filesystem::path upright =
        loftProject("upright", "{id: ladder:loft, room: room:hall, at: [512, 704], facing: n, height: 256}");
    REQUIRE(buildRun(upright).IsDefined());
    const YAML::Node uprightScene = YAML::LoadFile((upright / "build" / "lofttest.scene.yml").string());
    CHECK(uprightScene["ladders"][0]["top"][1].as<int>() == 704);

    // Leaning: the foot 120 out from the loft's edge, the top against it; the exit 64 beyond the top.
    const std::filesystem::path root = loftProject("leaning",
        "{id: ladder:loft, room: room:hall, at: [512, 640], top_at: [512, 760], facing: n, height: 256}");
    REQUIRE(buildRun(root).IsDefined());
    const YAML::Node scene = YAML::LoadFile((root / "build" / "lofttest.scene.yml").string());
    const YAML::Node ladder = scene["ladders"][0];
    CHECK(ladder["bottom"][1].as<int>() == 640);
    CHECK(ladder["bottom"][2].as<int>() == 0);
    CHECK(ladder["top"][0].as<int>() == 512);
    CHECK(ladder["top"][1].as<int>() == 760);
    CHECK(ladder["top"][2].as<int>() == 256);
    CHECK(ladder["top_exit"][1].as<int>() == 824);

    // The game's own reader takes the leaning top (its ladder rules climb along the line: the scenario of
    // output/studio_s6b/ climbs it in the game).
    std::string error;
    const std::optional<Game::IndoorSceneData> parsed =
        Game::IndoorSceneYmlLoader().loadFromText(s6bRead(root / "build" / "lofttest.scene.yml"), error);
    REQUIRE_MESSAGE(parsed.has_value(), error);
    REQUIRE(parsed->ladders.size() == 1);
    CHECK(parsed->ladders[0].top == std::array<float, 3>{512.0f, 760.0f, 256.0f});

    // The rails lean with it: their faces (drawn, not solid) reach from the foot's line out to the top's.
    const std::optional<Game::IndoorMapData> map =
        Game::IndoorMapDataLoader().loadFromBytes(s6bBytes(root / "build" / "lofttest.blv"));
    REQUIRE(map.has_value());
    const uint32_t untouchable = Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
    int nearest = 100000;
    int furthest = -100000;
    size_t faces = 0;

    for (const Game::IndoorFace &face : map->faces)
    {
        if ((face.attributes & untouchable) == 0)
        {
            continue;
        }

        ++faces;

        for (const uint16_t vertex : face.vertexIndices)
        {
            nearest = std::min<int>(nearest, map->vertices[vertex].y);
            furthest = std::max<int>(furthest, map->vertices[vertex].y);
        }
    }

    // Two rails and eight rungs, six faces each, as an upright ladder has.
    CHECK(faces == 60);
    CHECK(nearest >= 640 - 16);
    CHECK(nearest <= 640);
    CHECK(furthest >= 760 - 8);
    CHECK(furthest <= 760 + 8);

    // A ladder may lean 45 degrees at most.
    const std::filesystem::path steep = loftProject("steep",
        "{id: ladder:loft, room: room:hall, at: [512, 400], top_at: [512, 760], facing: n, height: 256}");
    s6bCall("session.configure", "{\"asset_root\":" + quoted(S6bAssets) + "}");
    const YAML::Node refused = s6bCall("check.validate", "{\"project\":" + quoted(steep) + "}");
    REQUIRE(refused.IsDefined());
    bool said = false;

    for (const YAML::Node &issue : refused["issues"])
    {
        said = said || issue["message"].Scalar().find("a ladder leans 45 degrees at most") != std::string::npos;
    }

    CHECK(said);
    std::filesystem::remove_all(upright);
    std::filesystem::remove_all(root);
    std::filesystem::remove_all(steep);
}

TEST_CASE("S6 M: mod.pack builds and packs projects with the mod's map range; mod.list; mod.map_number proposes")
{
    if (!haveMm6Root())
    {
        MESSAGE("no MM6 world in the development assets: skipped");
        return;
    }

    const std::string ladder = "{id: ladder:loft, room: room:hall, at: [512, 704], facing: n, height: 256}";
    const std::filesystem::path first = loftProject("mod_first", ladder, 9470, "modloft_a");
    const std::filesystem::path second = loftProject("mod_second", ladder, 9490, "modloft_b");
    const std::filesystem::path mods = s6bScratch("mods");
    s6bCall("session.configure", "{\"asset_root\":" + quoted(S6bAssets) + "}");

    // Packed with a build of each (none was built before) and the range 9470 to 9479: the second map lies outside.
    YAML::Node error;
    const YAML::Node packed = s6bCall("mod.pack", "{\"projects\":[" + quoted(first) + "," + quoted(second)
        + "],\"id\":\"lofts\",\"out\":" + quoted(mods) + ",\"name\":\"The lofts\",\"maps\":[9470,9479]}", &error);
    REQUIRE_MESSAGE(packed.IsDefined(), (error.IsNull() ? std::string() : YAML::Dump(error)));
    CHECK(packed["id"].Scalar() == "lofts");
    CHECK(packed["files"][0].Scalar() == "mod.yml");
    REQUIRE(packed["maps"].size() == 2);
    CHECK(packed["maps"][0]["file"].Scalar() == "modloft_a.blv");
    CHECK(packed["maps"][0]["kind"].Scalar() == "new");
    CHECK(packed["maps"][0]["map_number"].as<int>() == 9470);
    CHECK(packed["tables"][0].Scalar() == "map_stats.txt");
    REQUIRE(packed["warnings"].size() >= 1);
    CHECK(packed["warnings"][0].Scalar().find("modloft_b: its map number 9490 lies outside the mod's range 9470 to 9479")
        != std::string::npos);
    const YAML::Node manifest = YAML::LoadFile((mods / "lofts" / "mod.yml").string());
    CHECK(manifest["idRanges"]["maps"]["begin"].as<int>() == 9470);
    CHECK(manifest["idRanges"]["maps"]["end"].as<int>() == 9479);
    CHECK(std::filesystem::is_regular_file(mods / "lofts" / "worlds" / "mm6" / "maps" / "modloft_b.blv"));
    CHECK(s6bRead(mods / "lofts" / "tables" / "map_stats.txt.append.txt").find("\n9490\t") != std::string::npos);

    // The mods folder lists the packed mod as a named one, with its numbers and range.
    const YAML::Node listed = s6bCall("mod.list", "{\"mods\":" + quoted(mods) + "}");
    REQUIRE(listed["named"].size() == 1);
    CHECK(listed["merged"].size() == 0);
    CHECK(listed["named"][0]["id"].Scalar() == "lofts");
    CHECK(listed["named"][0]["maps"].as<int>() == 2);
    CHECK(listed["named"][0]["map_numbers"][1].as<int>() == 9490);
    CHECK(listed["named"][0]["map_range"][0].as<int>() == 9470);
    CHECK_FALSE(listed["named"][0]["enabled"].as<bool>());

    // A new map of the mod: the first number of its range no map takes (9470 is the first project's).
    const YAML::Node ofMod = s6bCall("mod.map_number", "{\"world\":\"mm6\",\"mods\":" + quoted(mods)
        + ",\"mod\":\"lofts\"}");
    CHECK(ofMod["number"].as<int>() == 9471);
    CHECK(ofMod["from"].Scalar() == "mod:lofts");
    CHECK(ofMod["taken"].as<int>() == 1);
    CHECK(ofMod["warnings"].size() == 0);

    // Without a mod: MM6 declares no map range, so the studio's band, past the numbers projects take.
    const YAML::Node studio = s6bCall("mod.map_number", "{\"world\":\"mm6\",\"projects\":[" + quoted(first) + "]}");
    CHECK(studio["from"].Scalar() == "studio");
    CHECK(studio["range"][0].as<int>() == 9400);
    CHECK(studio["number"].as<int>() >= 9400);
    CHECK(studio["number"].as<int>() != 9470);

    // A second mod whose range overlaps the first's is warned of; a mod without a range is refused; so is a full range.
    const std::filesystem::path third = loftProject("mod_third", ladder, 9476, "modloft_c");
    REQUIRE(s6bCall("mod.pack", "{\"projects\":[" + quoted(third) + "],\"id\":\"cellar\",\"out\":" + quoted(mods)
        + ",\"maps\":[9475,9476]}").IsDefined());
    const YAML::Node overlapping = s6bCall("mod.map_number", "{\"world\":\"mm6\",\"mods\":" + quoted(mods)
        + ",\"mod\":\"cellar\"}");
    CHECK(overlapping["number"].as<int>() == 9475);
    REQUIRE(overlapping["warnings"].size() == 1);
    CHECK(overlapping["warnings"][0].Scalar() == "the mod cellar's map numbers (9475 to 9476) overlap the mod lofts's "
        "(9470 to 9479)");
    REQUIRE(s6bCall("mod.pack", "{\"projects\":[" + quoted(third) + "],\"id\":\"plain\",\"out\":" + quoted(mods)
        + ",\"build\":false}").IsDefined());
    s6bCall("mod.map_number", "{\"world\":\"mm6\",\"mods\":" + quoted(mods) + ",\"mod\":\"plain\"}", &error);
    CHECK(error["data"]["kind"].Scalar() == "bad_request");
    CHECK(error["message"].Scalar().find("declares no map numbers") != std::string::npos);
    const std::filesystem::path full = loftProject("mod_full", ladder, 9475, "modloft_d");
    REQUIRE(s6bCall("mod.pack", "{\"projects\":[" + quoted(third) + "," + quoted(full) + "],\"id\":\"cellar\",\"out\":"
        + quoted(mods) + ",\"maps\":[9475,9476]}").IsDefined());
    s6bCall("mod.map_number", "{\"world\":\"mm6\",\"mods\":" + quoted(mods) + ",\"mod\":\"cellar\"}", &error);
    CHECK(error["message"].Scalar() == "every map number from 9475 to 9476 (mod:cellar) is taken");

    // A project that does not build is named, without its folder.
    const std::filesystem::path broken = loftProject("mod_broken",
        "{id: ladder:loft, room: room:nowhere, at: [512, 704], facing: n, height: 256}", 9477, "modloft_e");
    s6bCall("mod.pack", "{\"projects\":[" + quoted(broken) + "],\"id\":\"broken\",\"out\":" + quoted(mods) + "}", &error);
    CHECK(error["data"]["kind"].Scalar() == "bad_request");
    CHECK(error["message"].Scalar().find("modloft_e does not build") != std::string::npos);
    CHECK(error["message"].Scalar().find(broken.generic_string()) == std::string::npos);

    for (const std::filesystem::path &folder : {first, second, third, full, broken, mods})
    {
        std::filesystem::remove_all(folder);
    }
}

TEST_CASE("S6 2.9: world.view: projects by world, links by their cards' neighbours, rebuilds standing for originals")
{
    // A rebuilt outdoor map with a dungeon of its own, a map edge to a shipped map and a building that leads where no
    // neighbour says; the dungeon's exit leads back to the original's file; an overlay; a card that does not read.
    const std::filesystem::path root = s6bScratch("world");
    s6bWrite(root / "town" / "project.yml",
        "format: 0\nid: calib_town\nname: The Town\nworld: mm6\nkind: outdoor\nmap_stats: {id: 9601, reference: oute3.odm}\n"
        "neighbours:\n"
        "  - {id: door:crypt, to: crypt01.blv, kind: door}\n"
        "  - {id: edge:west, to: outd3.odm, kind: edge, side: west, days: 5}\n");
    s6bWrite(root / "town" / "sketch.yml",
        "format: 0\nstructures:\n"
        "  - {id: thing:crypt_door, kind: building, doors: [{into: {map: crypt01.blv, at: [0, 0, 0]}}]}\n"
        "  - {id: thing:inn, kind: building, doors: [{into: {map: 6t1.blv, at: [0, 0, 0]}}]}\n"
        "  - {id: thing:boat, kind: building, doors: [{into: {map: oute3.odm, at: [0, 0, 0]}}]}\n"
        "entrances:\n  - {id: entrance:west, at: [1, 1], neighbour: edge:west}\n");
    s6bWrite(root / "crypt" / "project.yml",
        "format: 0\nid: crypt01\nname: The Crypt\nworld: mm6\nkind: indoor\nmap_stats: {id: 9602}\n"
        "neighbours:\n  - {id: exit:town, to: oute3.odm, kind: door}\n");
    s6bWrite(root / "crypt" / "objects.yml", "format: 1\nexits:\n  - {id: exit:way_out, room: room:a, to: exit:town}\n");
    s6bWrite(root / "overlay" / "project.yml", "format: 0\nid: goblinwatch_lights\nname: Goblinwatch's lights\nworld: mm6\n"
        "kind: indoor\nbase: 6d01.blv\nneighbours:\n  - {id: exit:town, to: \"oute3.odm at -18400, -14982\", kind: door}\n");
    s6bWrite(root / "other" / "project.yml", "format: 0\nid: elsewhere\nname: Elsewhere\nworld: mm7\nkind: indoor\n");
    s6bWrite(root / "broken" / "project.yml", "format: 0\nid: [\n");

    const std::string projects = "[" + quoted(root / "town") + "," + quoted(root / "crypt") + "," + quoted(root / "overlay")
        + "," + quoted(root / "other") + "," + quoted(root / "broken") + "]";
    s6bCall("session.configure", "{\"asset_root\":" + quoted(S6bAssets) + "}");
    const YAML::Node view = s6bCall("world.view", "{\"projects\":" + projects + "}");
    REQUIRE(view.IsDefined());
    REQUIRE(view["worlds"].size() == 2);
    const YAML::Node mm6 = view["worlds"][0];
    CHECK(mm6["world"].Scalar() == "mm6");
    CHECK(view["worlds"][1]["world"].Scalar() == "mm7");
    REQUIRE(view["skipped"].size() == 1);
    CHECK(view["skipped"][0]["project"].as<int>() == 4);

    std::map<std::string, YAML::Node> maps;
    std::vector<std::string> names;

    for (const YAML::Node &map : mm6["maps"])
    {
        maps[map["map"].Scalar()] = map;
        names.push_back(map["map"].Scalar());
    }

    CHECK(maps["calib_town.odm"]["role"].Scalar() == "rebuild");
    CHECK(maps["calib_town.odm"]["stands_for"].Scalar() == "oute3.odm");
    CHECK(maps["crypt01.blv"]["role"].Scalar() == "new");
    CHECK(maps["6d01.blv"]["role"].Scalar() == "overlay");
    CHECK(maps["6d01.blv"]["project"].as<int>() == 2);
    // Shipped maps the links reach, named from the asset root's map_stats when it has them.
    REQUIRE(maps.contains("outd3.odm"));
    CHECK(maps["outd3.odm"]["role"].Scalar() == "shipped");
    CHECK_FALSE(maps["outd3.odm"]["project"]);
    REQUIRE(maps.contains("6t1.blv"));

    const auto indexOf = [&names](const std::string &map)
    {
        return static_cast<int>(std::find(names.begin(), names.end(), map) - names.begin());
    };
    const auto linkOf = [&mm6](int from, int to) -> YAML::Node
    {
        for (const YAML::Node &link : mm6["links"])
        {
            if (link["from"].as<int>() == from && link["to"].as<int>() == to)
            {
                return link;
            }
        }

        return YAML::Node(YAML::NodeType::Undefined);
    };
    // The town's door to the crypt, used by the building whose way in names the crypt's map.
    const YAML::Node toCrypt = linkOf(indexOf("calib_town.odm"), indexOf("crypt01.blv"));
    REQUIRE(toCrypt.IsDefined());
    CHECK(toCrypt["id"].Scalar() == "door:crypt");
    CHECK_FALSE(toCrypt["via_original"].as<bool>());
    CHECK(toCrypt["exits"][0].Scalar() == "thing:crypt_door");
    // The crypt's exit names the original's file: it reaches the rebuild; its exit object uses it.
    const YAML::Node back = linkOf(indexOf("crypt01.blv"), indexOf("calib_town.odm"));
    REQUIRE(back.IsDefined());
    CHECK(back["via_original"].as<bool>());
    CHECK(back["target"].Scalar() == "oute3.odm");
    CHECK(back["exits"][0].Scalar() == "exit:way_out");
    // The map edge, with its side and days and the entrance that uses it.
    const YAML::Node west = linkOf(indexOf("calib_town.odm"), indexOf("outd3.odm"));
    CHECK(west["side"].Scalar() == "west");
    CHECK(west["days"].as<int>() == 5);
    CHECK(west["exits"][0].Scalar() == "entrance:west");
    // The inn no neighbour names: undeclared; the boat to the map itself is no link.
    const YAML::Node inn = linkOf(indexOf("calib_town.odm"), indexOf("6t1.blv"));
    CHECK(inn["kind"].Scalar() == "undeclared");
    CHECK(inn["exits"][0].Scalar() == "thing:inn");
    CHECK_FALSE(linkOf(indexOf("calib_town.odm"), indexOf("calib_town.odm")).IsDefined());
    // An imported card's `to` with words after the file still names the file.
    CHECK(linkOf(indexOf("6d01.blv"), indexOf("calib_town.odm"))["via_original"].as<bool>());

    // One world only.
    const YAML::Node only = s6bCall("world.view", "{\"projects\":" + projects + ",\"world\":\"mm7\"}");
    REQUIRE(only["worlds"].size() == 1);
    CHECK(only["worlds"][0]["maps"][0]["map"].Scalar() == "elsewhere.blv");
    std::filesystem::remove_all(root);
}
