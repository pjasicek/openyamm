// S8c (devdocs/map_studio/S8_PLAN.md): the indoor code list's items 20 to 22 (rounds/NEXT_CODE_BATCH.md), from the
// user's walks through XD-02 and XD-05 and the Hive's and the Lab's rounds, and the parts of items 16 to 19 left open.
#include "doctest/doctest.h"

#include "core/Audit.h"
#include "core/EventFlow.h"
#include "core/IndoorBuild.h"
#include "core/MapLoad.h"
#include "core/Project.h"
#include "core/Reachability.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <random>
#include <string>
#include <vector>

using namespace OpenYAMM::Studio;

namespace
{
const char *S8cTheme =
    "format: 0\n"
    "themes:\n"
    "  - id: theme:plain\n"
    "    wall: {texture: wall, size: [128, 128]}\n"
    "    floor: {texture: floor, size: [128, 128]}\n"
    "    ceiling: {texture: ceil, size: [128, 128]}\n"
    "defaults: {theme: theme:plain}\n";

const char *S8cDecorations =
    "Decoration Data\t\t\tDescriptor\n"
    "#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\tSoundId\t"
    "Flags\tSpriteId\n\n"
    "1\tnull\tnull\t0\t8\t8\t0\t0\t0\t0\t0\t0\t0\n"
    "20\ttorch01\ttorch\t0\t16\t64\t0\t0\t0\t0\t0\t0\t17000\n"
    "157\tsmlbarel\tkeg\t0\t30\t40\t0\t0\t0\t0\t0\t0\t17789\n"
    "191\tstltite1\tstalagtite\t0\t64\t112\t0\t0\t0\t0\t0\t0\t17663\n";

const char *S8cSprites =
    "sprites:\n"
    "  - sprite_id: 17000\n"
    "    sprite_name: \"torch01\"\n"
    "    frames:\n"
    "      - texture_name: \"torch01a\"\n"
    "      - texture_name: \"torch01b\"\n"
    "  - sprite_id: 17663\n"
    "    sprite_name: \"stltite1\"\n"
    "    frames:\n"
    "      - texture_name: \"stltite1\"\n";

struct S8cBuilt
{
    bool built = false;
    std::vector<ProjectIssue> issues;
    std::vector<std::string> warnings;
    OpenYAMM::Game::IndoorMapData map;
    std::string lua;
    // The built map as the tools read it (scene, starting state, script).
    LoadedMap loaded;

    size_t warned(const std::string &text) const
    {
        return static_cast<size_t>(std::count_if(warnings.begin(), warnings.end(),
            [&text](const std::string &warning) { return warning.find(text) != std::string::npos; }));
    }

    std::string issueText() const
    {
        std::string text;

        for (const ProjectIssue &issue : issues)
        {
            text += issue.path + ": " + issue.message + "\n";
        }

        return text;
    }
};

// A project of the given files (project.yml defaults to an MM7 dungeon `testmap`, rooms.yml gets the plain theme in
// front) built against an asset root holding `assets` (paths under the root), with the decoration table.
S8cBuilt buildS8c(std::map<std::string, std::string> files, const std::map<std::string, std::string> &assets = {})
{
    const std::filesystem::path root =
        std::filesystem::temp_directory_path() / ("oymap_s8c_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root / "project");

    if (!files.contains("project.yml"))
    {
        files["project.yml"] = "format: 0\nid: testmap\nworld: mm7\nkind: indoor\n";
    }

    files["rooms.yml"] = std::string(S8cTheme) + files["rooms.yml"];

    for (const std::pair<const std::string, std::string> &file : files)
    {
        std::ofstream(root / "project" / file.first, std::ios::binary) << file.second;
    }

    std::map<std::string, std::string> allAssets = assets;

    if (!allAssets.contains("engine/data_tables/decoration_data.txt"))
    {
        allAssets["engine/data_tables/decoration_data.txt"] = S8cDecorations;
    }

    for (const std::pair<const std::string, std::string> &file : allAssets)
    {
        const std::filesystem::path path = root / "assets" / file.first;
        std::filesystem::create_directories(path.parent_path());
        std::ofstream(path, std::ios::binary) << file.second;
    }

    S8cBuilt built;
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

            std::ifstream luaStream(root / "build" / "testmap.lua", std::ios::binary);
            built.lua.assign((std::istreambuf_iterator<char>(luaStream)), std::istreambuf_iterator<char>());
            std::ifstream sceneStream(root / "build" / "testmap.scene.yml", std::ios::binary);
            const std::string sceneText(
                (std::istreambuf_iterator<char>(sceneStream)), std::istreambuf_iterator<char>());
            std::string errorMessage;
            built.loaded.world = "mm7";
            built.loaded.fileName = "testmap.blv";
            built.loaded.stem = "testmap";
            built.loaded.kind = MapKind::Indoor;
            built.loaded.indoor = map;
            built.loaded.indoorScene = OpenYAMM::Game::IndoorSceneYmlLoader().loadFromText(sceneText, errorMessage);
            built.loaded.scriptText = built.lua;
            // The support script in front, as the game and oymap's map reading put it (the asset root's).
            std::ifstream supportStream(std::filesystem::path(OPENYAMM_DEV_ASSETS_DIR) / "engine" / "scripts"
                / "common" / "event_support.lua", std::ios::binary);
            const std::string support(
                (std::istreambuf_iterator<char>(supportStream)), std::istreambuf_iterator<char>());
            built.loaded.fullScriptSource = support + "\n" + built.lua;

            if (map && built.loaded.indoorScene)
            {
                OpenYAMM::Game::MapDeltaData state;

                if (OpenYAMM::Game::buildIndoorMapStateFromScene(
                        *built.loaded.indoorScene, *built.loaded.indoor, state, errorMessage))
                {
                    built.loaded.state = state;
                }
            }
        }
    }

    std::filesystem::remove_all(root);
    return built;
}

const char *PlainRoom =
    "rooms:\n"
    "  - id: room:a\n"
    "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
    "    floor: 0\n"
    "    ceiling: 512\n";
const char *PlainStart = "format: 0\nstart: {room: room:a, at: [128, 128]}\n";

bool hasVertex(const OpenYAMM::Game::IndoorMapData &map, int x, int y, int z)
{
    return std::any_of(map.vertices.begin(), map.vertices.end(), [x, y, z](const OpenYAMM::Game::IndoorVertex &vertex)
    {
        return vertex.x == x && vertex.y == y && vertex.z == z;
    });
}

const char *SlopingCave =
    "rooms:\n"
    "  - id: room:cave\n"
    "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
    "    floor: 0\n"
    "    ceiling: 512\n"
    "    ceiling_points: [[0, 0, 512], [1024, 0, 512], [1024, 1024, 768], [0, 1024, 768]]\n";
}

TEST_CASE("a block whose top follows a sloping roof by `top_heights` hangs from it (XD-05's stalactites)")
{
    // The roof rises 1 in 4 northward: at y 416 it is at 616, at 608 at 664.
    const std::string hanging = std::string(SlopingCave)
        + "    platforms:\n"
          "      - {outline: [[472, 416], [552, 416], [608, 472], [608, 552], [552, 608], [472, 608], [416, 552], "
          "[416, 472]], base: 500, rise: 96, top_heights: [116, 116, 130, 150, 164, 164, 150, 130]}\n";
    const std::string objects = "format: 0\nstart: {room: room:cave, at: [128, 128]}\n";
    const S8cBuilt built = buildS8c({{"rooms.yml", hanging}, {"objects.yml", objects}});
    INFO(built.issueText());
    REQUIRE(built.built);
    CHECK(built.warned("rests on nothing") == 0);

    // The same block 60 under the roof everywhere does hang from nothing.
    const std::string low = std::string(SlopingCave)
        + "    platforms:\n"
          "      - {outline: [[472, 416], [552, 416], [608, 472], [608, 552], [552, 608], [472, 608], [416, 552], "
          "[416, 472]], base: 440, rise: 96, top_heights: [116, 116, 130, 150, 164, 164, 150, 130]}\n";
    const S8cBuilt floating = buildS8c({{"rooms.yml", low}, {"objects.yml", objects}});
    REQUIRE(floating.built);
    CHECK(floating.warned("rests on nothing") == 1);
}

TEST_CASE("a torch on a wall without `height` hangs at the shipped height; other things stay at the floor")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 512\n";
    const auto objects = [](const std::string &decoration, const std::string &fields)
    {
        return "format: 0\nstart: {room: room:a, at: [128, 128]}\ndecorations:\n"
            "  - {id: deco:x, room: room:a, decoration: " + decoration + ", wall: n" + fields + "}\n";
    };
    const S8cBuilt torch = buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects("torch01", "")}});
    INFO(torch.issueText());
    REQUIRE(torch.built);
    REQUIRE(torch.map.entities.size() == 1);
    CHECK(torch.map.entities[0].z == 128);
    const S8cBuilt given = buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects("torch01", ", height: 176")}});
    REQUIRE(given.built);
    CHECK(given.map.entities[0].z == 176);
    const S8cBuilt keg = buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects("smlbarel", "")}});
    REQUIRE(keg.built);
    CHECK(keg.map.entities[0].z == 0);
}

TEST_CASE("a decoration the world draws nothing for is warned of: no model binds it and no sprite picture is there")
{
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 512\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\ndecorations:\n"
        "  - {id: deco:torch, room: room:a, decoration: torch01, wall: n}\n"
        "  - {id: deco:tite, room: room:a, decoration: stltite1, at: [600, 600]}\n";
    std::map<std::string, std::string> assets = {
        {"engine/rendering/sprite_frame_data_common.yml", S8cSprites}, {"engine/sprites/torch01a.bmp", "x"}};
    const S8cBuilt built = buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects}}, assets);
    INFO(built.issueText());
    REQUIRE(built.built);
    CHECK(built.warned("deco:tite (stltite1) in room:a draws nothing in this world's dungeons") == 1);
    CHECK(built.warned("deco:torch") == 0);

    // A picture of the world's own, or a model bound for every dungeon: it draws.
    std::map<std::string, std::string> withPicture = assets;
    withPicture["worlds/mm7/sprites/STLTITE1.png"] = "x";
    CHECK(buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects}}, withPicture).warned("draws nothing") == 0);
    std::map<std::string, std::string> withModel = assets;
    withModel["engine/models/indoor_decorations.yml"] =
        "decorations:\n  - {name: stltite1, model: engine/models/x.glb, height: 112}\n";
    CHECK(buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects}}, withModel).warned("draws nothing") == 0);
    // A model bound only for other maps does not count.
    std::map<std::string, std::string> elsewhere = assets;
    elsewhere["engine/models/indoor_decorations.yml"] =
        "decorations:\n  - {name: stltite1, model: engine/models/x.glb, maps: [d05.blv]}\n";
    CHECK(buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects}}, elsewhere).warned("draws nothing") == 1);
    // Without the sprite table nothing can be told.
    CHECK(buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects}}).warned("draws nothing") == 0);
}

TEST_CASE("`stalactites` hang from the roof in three narrowing blocks, the top one's top following the roof")
{
    const std::string rooms = std::string(SlopingCave)
        + "    stalactites:\n"
          "      - {at: [512, 512], radius: 96, length: 272}\n";
    const S8cBuilt built = buildS8c({{"rooms.yml", rooms}, {"objects.yml", "format: 0\nstart: {room: room:cave, "
        "at: [128, 128]}\n"}});
    INFO(built.issueText());
    REQUIRE(built.built);
    CHECK(built.warned("rests on nothing") == 0);
    CHECK(built.warned("reaches") == 0);
    // The roof at the crown's lowest corner (y 416) is at 616: the tip 272 under it, 95 + 95 + 82 long; half widths
    // 96, 67 and 35 (flat sides square to x and y: a side's middle at the half width from the middle).
    CHECK(hasVertex(built.map, 472, 416, 616));
    CHECK(hasVertex(built.map, 552, 608, 664));
    CHECK(hasVertex(built.map, 472, 416, 521));
    CHECK(hasVertex(built.map, 484, 445, 521));
    CHECK(hasVertex(built.map, 484, 445, 426));
    CHECK(hasVertex(built.map, 498, 477, 426));
    CHECK(hasVertex(built.map, 498, 477, 344));

    // One that reaches the floor, one outside the room, one in a tunnel: refused.
    const auto refused = [](const std::string &entry, const std::string &room)
    {
        return buildS8c({{"rooms.yml", room + "    stalactites:\n      - " + entry + "\n"},
            {"objects.yml", "format: 0\nstart: {room: room:cave, at: [128, 128]}\n"}}).issueText();
    };
    CHECK(refused("{at: [512, 512], length: 620}", SlopingCave).find("would reach") != std::string::npos);
    CHECK(refused("{at: [980, 512]}", SlopingCave).find("does not lie inside") != std::string::npos);
    const std::string tunnel =
        "rooms:\n"
        "  - id: room:cave\n"
        "    path: [[0, 0], [1024, 0]]\n"
        "    section: {outline: [[-64, 0], [64, 0], [128, 128], [64, 256], [-64, 256], [-128, 128]]}\n"
        "    floor: 0\n"
        "    ceiling: 256\n";
    CHECK(refused("{at: [512, 0]}", tunnel).find("takes no `stalactites`") != std::string::npos);
    const std::string vaulted =
        "rooms:\n"
        "  - id: room:cave\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 512\n"
        "    ceiling_levels:\n"
        "      - {outline: [[256, 256], [768, 256], [768, 768], [256, 768]], ceiling: 640}\n";
    CHECK(refused("{at: [512, 512]}", vaulted).find("hangs under a ceiling level") != std::string::npos);
}

TEST_CASE("`bend_radius` rounds a path's bends into arcs; the stretches keep their line")
{
    const auto corridor = [](const std::string &extra)
    {
        return "rooms:\n"
               "  - id: room:a\n"
               "    path: [[0, 0], [1024, 0], [1024, 1024]]\n"
               "    width: 256\n"
               "    floor: 0\n"
               "    ceiling: 256\n" + extra;
    };
    const std::string objects = "format: 0\nstart: {room: room:a, at: [64, 0]}\n";
    const S8cBuilt sharp = buildS8c({{"rooms.yml", corridor("")}, {"objects.yml", objects}});
    INFO(sharp.issueText());
    REQUIRE(sharp.built);
    // The mitred bend's outer corner.
    CHECK(hasVertex(sharp.map, 1152, -128, 0));
    const S8cBuilt round = buildS8c({{"rooms.yml", corridor("    bend_radius: 256\n")}, {"objects.yml", objects}});
    INFO(round.issueText());
    REQUIRE(round.built);
    CHECK_FALSE(hasVertex(round.map, 1152, -128, 0));
    // Four pieces round the bend: four more wall faces on each side of the way.
    CHECK(round.map.faces.size() > sharp.map.faces.size());
    CHECK(buildS8c({{"rooms.yml", corridor("    bend_radius: 8\n")}, {"objects.yml", objects}}).issueText().find(
        "bend_radius") != std::string::npos);
}

TEST_CASE("a new dungeon without an arrival text is warned of; a timer's window or a load's status line answers it")
{
    const std::string rooms = PlainRoom;
    const auto card = [](const std::string &extra)
    {
        return "format: 0\nid: testmap\nworld: mm7\nkind: indoor\n" + extra;
    };
    const auto warned = [&rooms](const std::string &cardText, const std::string &wiring)
    {
        std::map<std::string, std::string> files = {
            {"project.yml", cardText}, {"rooms.yml", rooms}, {"objects.yml", PlainStart}};

        if (!wiring.empty())
        {
            files["wiring.yml"] = wiring;
        }

        const S8cBuilt built = buildS8c(files);
        REQUIRE(built.built);
        return built.warned("is a new dungeon");
    };
    // A rebuild (no mark) is not judged; a map with a map code or `new: true` is.
    CHECK(warned(card(""), "") == 0);
    CHECK(warned(card("map_code: XD-09\n"), "") == 1);
    CHECK(warned(card("new: true\n"), "") == 1);
    CHECK(warned(card("map_code: XD-09\nnew: false\n"), "") == 0);
    const std::string timer = "format: 0\nevents:\n  - {id: evt:arrive, preset: script, trigger: timer, every: 1, "
                              "once: true, effects: [{message: \"The mayor sent you here.\"}]}\n";
    CHECK(warned(card("map_code: XD-09\n"), timer) == 0);
    const std::string loadStatus =
        "format: 0\nevents:\n  - {id: evt:arrive, preset: text, trigger: load, once: true, text: Hot air rises.}\n";
    CHECK(warned(card("map_code: XD-09\n"), loadStatus) == 0);
    // A load event's message window is not shown in the game.
    const std::string loadWindow = "format: 0\nevents:\n  - {id: evt:arrive, preset: script, trigger: load, "
                                   "effects: [{message: \"The mayor sent you here.\"}]}\n";
    CHECK(warned(card("map_code: XD-09\n"), loadWindow) == 1);
}

TEST_CASE("an opening's `lintel` lays the doorway's top in a surface of its own")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[1056, 256], [1568, 256], [1568, 768], [1056, 768]], floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256, reveal: {texture: jamb, size: [128, "
        "256]}, lintel: {texture: lintel, size: [128, 128]}}\n";
    const S8cBuilt built = buildS8c({{"rooms.yml", rooms}, {"objects.yml", PlainStart}});
    INFO(built.issueText());
    REQUIRE(built.built);
    size_t lintels = 0;
    size_t jambs = 0;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        bool top = !face.vertexIndices.empty();

        for (const uint16_t vertex : face.vertexIndices)
        {
            top = top && built.map.vertices[vertex].z == 256;
        }

        lintels += face.textureName == "lintel" && top ? 1 : 0;
        jambs += face.textureName == "jamb" ? 1 : 0;
    }

    CHECK(lintels == 1);
    // Two sides and the threshold.
    CHECK(jambs == 3);
    // Not in a floor's hole.
    const std::string hole =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: -512, ceiling: -64}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, in: floor, at: [512, 512], size: [128, 128], "
        "lintel: {texture: lintel, size: [128, 128]}}\n";
    CHECK(buildS8c({{"rooms.yml", hole}, {"objects.yml", PlainStart}}).issueText().find("`lintel` is the top of a "
        "doorway") != std::string::npos);
}

TEST_CASE("a platform stands on a tunnel's flat floor; one reaching over its leaning sides is refused")
{
    const auto tunnel = [](const std::string &platform)
    {
        return "rooms:\n"
               "  - id: room:a\n"
               "    path: [[0, 0, 0], [512, 0, 0], [1024, 0, 0]]\n"
               "    section: {outline: [[-64, 0], [64, 0], [128, 128], [64, 256], [-64, 256], [-128, 128]]}\n"
               "    floor: 0\n"
               "    ceiling: 256\n"
               "    platforms:\n"
               "      - " + platform + "\n";
    };
    const std::string objects = "format: 0\nstart: {room: room:a, at: [64, 0]}\n";
    const S8cBuilt pad = buildS8c({{"rooms.yml", tunnel("{at: [640, 0], size: [224, 128], rise: 16}")},
        {"objects.yml", objects}});
    INFO(pad.issueText());
    REQUIRE(pad.built);
    CHECK(hasVertex(pad.map, 528, -64, 16));
    CHECK(hasVertex(pad.map, 752, 64, 16));
    CHECK(buildS8c({{"rooms.yml", tunnel("{at: [640, 0], size: [224, 192], rise: 16}")}, {"objects.yml", objects}})
              .issueText().find("on the tunnel's flat floor") != std::string::npos);
    CHECK(buildS8c({{"rooms.yml", tunnel("{at: [640, 0], size: [224, 128], rise: 300}")}, {"objects.yml", objects}})
              .issueText().find("under its roof") != std::string::npos);
}

TEST_CASE("an opening between rooms facing across several pairs of walls takes the thinnest that holds its width")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [1024, 0], [1024, 256], [512, 256], [512, 768], [0, 768]], floor: 0, "
        "ceiling: 384}\n"
        "  - {id: room:b, outline: [[1024, 0], [1600, 0], [1600, 1000], [704, 1000], [704, 448], [1024, 448]], "
        "floor: 0, ceiling: 384}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
    const S8cBuilt built = buildS8c({{"rooms.yml", rooms}, {"objects.yml", PlainStart}});
    INFO(built.issueText());
    REQUIRE(built.built);
    CHECK(built.warned("Taken, as the thinnest wall that holds its width: wall 1 of room:a") == 1);
    bool portalOnSharedWall = false;

    for (const OpenYAMM::Game::IndoorFace &face : built.map.faces)
    {
        if (face.isPortal)
        {
            portalOnSharedWall = std::all_of(face.vertexIndices.begin(), face.vertexIndices.end(),
                [&built](uint16_t vertex) { return built.map.vertices[vertex].x == 1024; });
        }
    }

    CHECK(portalOnSharedWall);
    // Too wide for the thin wall's 256 (with 16 of wall each side): the longest, as before (also the thinnest of
    // those that hold it here).
    std::string wide = rooms;
    wide.replace(wide.find("width: 128"), 10, "width: 240");
    const S8cBuilt longer = buildS8c({{"rooms.yml", wide}, {"objects.yml", PlainStart}});
    INFO(longer.issueText());
    REQUIRE(longer.built);
    CHECK(longer.warned("for its longest shared stretch: wall 2 of room:a") == 1);
}

TEST_CASE("solve names monsters and spawn points it never reaches, and counts items lying on the floor")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:hall, outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 768}\n"
        "  - {id: room:chute, outline: [[384, 1056], [640, 1056], [640, 1312], [384, 1312]], floor: 384, "
        "ceiling: 1024}\n"
        "openings:\n"
        "  - {id: open:chute, from: room:hall, to: room:chute, width: 192, height: 256}\n";
    const std::string card = "format: 0\nid: testmap\nworld: mm7\nkind: indoor\nmap_stats:\n  slots:\n"
                             "    - {monster: Bat, tier: 1, per_marker: [2, 4], weight: 100}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:hall, at: [200, 200]}\n"
        "spawns:\n"
        "  - {id: spawn:hall, room: room:hall, at: [600, 400], slot: 1, tier: a}\n"
        "  - {id: spawn:chute, room: room:chute, at: [512, 1184], slot: 1, tier: a}\n";
    const S8cBuilt built = buildS8c({{"project.yml", card}, {"rooms.yml", rooms}, {"objects.yml", objects}});
    INFO(built.issueText());
    REQUIRE(built.built);
    REQUIRE(built.loaded.state);
    const SolveResult solved = solveMap(built.loaded, "[]");
    REQUIRE(solved.ran);
    REQUIRE(solved.stranded.size() == 1);
    CHECK(solved.stranded[0].kind == "spawn point");
    CHECK(solved.stranded[0].at == std::array<int, 3>{512, 1184, 384});
    const std::vector<AuditFinding> findings = strandedFindings(solved, {{1, "room:chute"}});
    REQUIRE(findings.size() == 1);
    CHECK(findings[0].code == "reach.stranded");
    CHECK(findings[0].message.find("(room:chute)") != std::string::npos);
}

TEST_CASE("solve counts an item lying on the map as given by the map once its place is reached")
{
    const std::string rooms =
        "rooms:\n"
        "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
        "  - {id: room:b, outline: [[544, 128], [800, 128], [800, 384], [544, 384]], floor: 0, ceiling: 256}\n"
        "openings:\n"
        "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 192}\n";
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "doors:\n  - {id: door:ab, opening: open:ab, kind: slide_up}\n"
        "items:\n  - {id: item:key, room: room:a, at: [300, 300], item: 2110}\n";
    const std::string wiring = "format: 0\nevents:\n  - {id: evt:door, preset: door, source: door:ab, toggles: "
                               "[door:ab], condition: {item: 2110}}\n";
    // An item on the floor needs the asset root's item and object tables.
    std::map<std::string, std::string> tables;

    for (const char *pName : {"items.txt", "object_list.txt"})
    {
        std::ifstream stream(
            std::filesystem::path(OPENYAMM_DEV_ASSETS_DIR) / "engine" / "data_tables" / pName, std::ios::binary);
        tables[std::string("engine/data_tables/") + pName].assign(
            (std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    }

    S8cBuilt built = buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects}, {"wiring.yml", wiring}}, tables);
    INFO(built.issueText());
    REQUIRE(built.built);

    std::string flow;
    std::string error;
    REQUIRE(exploreEventHandlers(built.loaded, flow, error));
    const SolveResult solved = solveMap(built.loaded, flow);
    REQUIRE(solved.ran);
    CHECK(std::none_of(solved.notes.begin(), solved.notes.end(),
        [](const std::string &note) { return note.find("comes from elsewhere") != std::string::npos; }));
    CHECK(std::any_of(solved.notes.begin(), solved.notes.end(),
        [](const std::string &note) { return note.find("lies on the floor") != std::string::npos; }));
}

TEST_CASE("the faces of a sector with no floor and no portal are faces the game never meets")
{
    OpenYAMM::Game::IndoorMapData map;
    map.sectors.resize(3);
    // Sector 1 has a floor; sector 2 only two stray walls.
    map.sectors[1].floorFaceIds = {0};
    map.sectors[2].wallFaceIds = {1, 2};
    map.faces.resize(4);
    map.faces[0].roomNumber = 1;
    map.faces[1].roomNumber = 2;
    map.faces[2].roomNumber = 2;
    map.faces[2].roomBehindNumber = 1;
    map.faces[3].roomNumber = 2;
    map.faces[3].isPortal = true;
    const std::set<uint32_t> ignored = facesTheGameIgnores(map);
    CHECK(ignored == std::set<uint32_t>{1});
    // A portal into sector 2 makes its faces met.
    map.sectors[2].portalFaceIds = {3};
    CHECK(facesTheGameIgnores(map).empty());
}

TEST_CASE("a ride's switch must be in reach of its deck at both stops, facing it with nothing between")
{
    // A lift beside a gallery at its raised height: it stops beside a floor at both ends.
    const std::string rooms =
        "rooms:\n"
        "  - id: room:a\n"
        "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
        "    floor: 0\n"
        "    ceiling: 640\n"
        "    levels:\n"
        "      - {outline: [[768, 0], [1024, 0], [1024, 1024], [768, 1024]], floor: 256}\n"
        "  - {id: room:b, outline: [[-544, 384], [-32, 384], [-32, 640], [-544, 640]], floor: 0, ceiling: 384}\n";
    const auto objects = [](const std::string &switchPlace)
    {
        return "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
               "lifts:\n  - {id: lift:l, room: room:a, at: [704, 832], size: [128, 128], travel: 256}\n"
               "switches:\n  - {id: switch:s, " + switchPlace + "}\n";
    };
    const std::string wiring =
        "format: 0\nevents:\n  - {id: evt:s, preset: switch, source: switch:s, toggles: [lift:l]}\n";
    const auto rideFindings = [&](const std::string &switchPlace)
    {
        const S8cBuilt built = buildS8c({{"rooms.yml", rooms}, {"objects.yml", objects(switchPlace)},
            {"project.yml", "format: 0\nid: testmap\nworld: mm6\nkind: indoor\n"}, {"wiring.yml", wiring}});
        INFO(built.issueText());
        REQUIRE(built.built);
        std::string flow;
        std::string error;
        REQUIRE(exploreEventHandlers(built.loaded, flow, error));
        INFO(flow);
        CHECK(flow.find("door 1 toggle") != std::string::npos);
        return auditRides(built.loaded, flow);
    };
    // Behind the wall, in another room: a warning.
    const std::vector<AuditFinding> behind = rideFindings("room: room:b, at: [-34, 512]");
    REQUIRE(behind.size() == 1);
    CHECK(behind[0].code == "ride.no_switch");
    CHECK(behind[0].severity == "warning");
    // On the wall beside the lift: none.
    CHECK(rideFindings("room: room:a, at: [704, 1020]").empty());
}

TEST_CASE("a face whose event runs on a step, without the clickable bit, is no click for click.silent")
{
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
                                "plates:\n  - {id: plate:p, room: room:a, at: [512, 512], size: [128, 128]}\n";
    const std::string wiring = "format: 0\nevents:\n  - {id: evt:p, preset: script, trigger: step, source: "
                               "plate:p, effects: [{set: {var: {map_var: stepped}, value: 1}}]}\n"
                               "variables: [stepped]\n";
    const S8cBuilt built = buildS8c({{"rooms.yml", PlainRoom}, {"objects.yml", objects}, {"wiring.yml", wiring}});
    INFO(built.issueText());
    REQUIRE(built.built);
    std::string flow;
    std::string error;
    REQUIRE(exploreEventHandlers(built.loaded, flow, error));
    CHECK(auditSilentClicks(built.loaded, flow).empty());
}
