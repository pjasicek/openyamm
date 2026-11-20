// S8g (devdocs/map_studio/S8_PLAN.md): the studio defects the Xeen map agents of Act II hit (devdocs/xeen/ACT2_BUILD.md,
// the maps' NOTES.md): sounds of the engine's audio, `--mount` for validate and build, two wiring events of one id, a
// wall's own surface over the room's bands, rules.no_spells, an indoor map's bolster row, and installs into one mount
// that keep each other's table rows. The travel table's arrival words are tested beside the other travel tests
// (OutdoorTests.cpp).
#include "doctest/doctest.h"

#include "core/IndoorBuild.h"
#include "core/OutdoorBuild.h"
#include "core/Project.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <optional>
#include <random>
#include <set>
#include <string>
#include <vector>

using namespace OpenYAMM::Studio;

namespace
{
const char *S8gTheme =
    "format: 0\n"
    "themes:\n"
    "  - id: theme:plain\n"
    "    wall: {texture: wall, size: [128, 128]}\n"
    "    floor: {texture: floor, size: [128, 128]}\n"
    "    ceiling: {texture: ceil, size: [128, 128]}\n"
    "defaults: {theme: theme:plain}\n";

const char *S8gRoom =
    "rooms:\n"
    "  - id: room:a\n"
    "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
    "    floor: 0\n"
    "    ceiling: 512\n";

std::filesystem::path s8gScratch(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s8g_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

void s8gWrite(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

std::string s8gRead(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::string((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
}

struct S8gBuilt
{
    bool built = false;
    std::vector<ProjectIssue> issues;
    std::optional<OpenYAMM::Game::IndoorMapData> map;
    std::optional<OpenYAMM::Game::IndoorSceneData> scene;
    std::string sceneText;

    bool issued(const std::string &text) const
    {
        return std::any_of(issues.begin(), issues.end(),
            [&text](const ProjectIssue &issue) { return issue.message.find(text) != std::string::npos; });
    }
};

// An MM7 dungeon `testmap` of the given files (rooms.yml gets the plain theme in front) built against an asset root
// holding `assets` and, when given, a mount holding `mount` (paths under each, file contents).
S8gBuilt buildS8g(std::map<std::string, std::string> files, const std::map<std::string, std::string> &assets = {},
    const std::map<std::string, std::string> &mount = {})
{
    const std::filesystem::path root = s8gScratch("build");

    if (!files.contains("project.yml"))
    {
        files["project.yml"] = "format: 0\nid: testmap\nworld: mm7\nkind: indoor\n";
    }

    files["rooms.yml"] = std::string(S8gTheme) + files["rooms.yml"];

    for (const std::pair<const std::string, std::string> &file : files)
    {
        s8gWrite(root / "project" / file.first, file.second);
    }

    for (const std::pair<const std::string, std::string> &file : assets)
    {
        s8gWrite(root / "assets" / file.first, file.second);
    }

    for (const std::pair<const std::string, std::string> &file : mount)
    {
        s8gWrite(root / "mount" / file.first, file.second);
    }

    std::filesystem::create_directories(root / "assets");
    S8gBuilt built;
    Project project;

    if (loadProject(root / "project", project, built.issues))
    {
        BuildOptions options;
        options.outputDirectory = root / "build";
        options.assetRoot = root / "assets";
        options.mountRoot = mount.empty() ? std::filesystem::path() : root / "mount";
        BuildResult result;
        built.built = buildProject(project, options, result);
        built.issues = result.issues;

        if (built.built)
        {
            const std::string bytes = s8gRead(root / "build" / "testmap.blv");
            built.map = OpenYAMM::Game::IndoorMapDataLoader().loadFromBytes(
                std::vector<uint8_t>(bytes.begin(), bytes.end()));
            built.sceneText = s8gRead(root / "build" / "testmap.scene.yml");
            std::string errorMessage;
            built.scene = OpenYAMM::Game::IndoorSceneYmlLoader().loadFromText(built.sceneText, errorMessage);
        }
    }

    std::filesystem::remove_all(root);
    return built;
}

std::string soundObjects(const std::string &sound)
{
    return "format: 0\nstart: {room: room:a, at: [128, 128]}\nsounds:\n"
        "  - {id: sound:a, room: room:a, at: [512, 512], sound: \"" + sound + "\", radius: 800}\n";
}
}

TEST_CASE("S8g: a placed sound may be one of the engine's audio, or of the mount in front of the root")
{
    const std::map<std::string, std::string> assets = {
        {"worlds/mm7/audio/7campfire.wav", "RIFF"},
        {"engine/audio/rushing water loop.wav", "RIFF"},
        {"engine/audio/weather/Rain01.wav", "RIFF"},
        {"engine/audio/readme.txt", "not a sound"}};

    // The world's own, the engine's (by name, with .wav, in any case, in a subfolder by its bare name or its path).
    for (const char *pSound : {"7campfire.wav", "7campfire", "rushing water loop", "Rushing Water Loop.wav",
             "rain01", "weather/rain01.wav"})
    {
        const S8gBuilt built = buildS8g({{"rooms.yml", S8gRoom}, {"objects.yml", soundObjects(pSound)}}, assets);
        INFO(pSound);
        CHECK(built.built);
    }

    // No such sound, and a file that is no .wav.
    for (const char *pSound : {"drip99", "readme.txt", "readme"})
    {
        const S8gBuilt built = buildS8g({{"rooms.yml", S8gRoom}, {"objects.yml", soundObjects(pSound)}}, assets);
        INFO(pSound);
        CHECK_FALSE(built.built);
        CHECK(built.issued("has no sound file"));
    }

    // A sound that only the mount holds: refused without it, built with it.
    CHECK_FALSE(buildS8g({{"rooms.yml", S8gRoom}, {"objects.yml", soundObjects("bubbling")}}, assets).built);
    CHECK(buildS8g({{"rooms.yml", S8gRoom}, {"objects.yml", soundObjects("bubbling")}}, assets,
        {{"worlds/mm7/audio/bubbling.wav", "RIFF"}}).built);
    CHECK(buildS8g({{"rooms.yml", S8gRoom}, {"objects.yml", soundObjects("chant")}}, assets,
        {{"engine/audio/chant.wav", "RIFF"}}).built);
}

TEST_CASE("S8g: two wiring events of one id are refused, not built as one handler")
{
    const std::string objects =
        "format: 0\nstart: {room: room:a, at: [128, 128]}\n"
        "plates:\n  - {id: plate:a, room: room:a, at: [512, 256], size: [128, 128]}\n"
        "  - {id: plate:b, room: room:a, at: [512, 768], size: [128, 128]}\n";
    const std::string twice =
        "format: 0\nevents:\n"
        "  - {id: evt:guardroom, preset: script, trigger: step, source: plate:b, effects: [{text: Chest}]}\n"
        "  - {id: evt:guardroom, preset: script, trigger: step, source: plate:a, effects: [{text: Door}]}\n";
    const S8gBuilt built = buildS8g({{"rooms.yml", S8gRoom}, {"objects.yml", objects}, {"wiring.yml", twice}});
    CHECK_FALSE(built.built);
    CHECK(built.issued("the id evt:guardroom is used by an earlier event"));

    std::string renamed = twice;
    renamed.replace(renamed.rfind("evt:guardroom"), 13, "evt:plate");
    CHECK(buildS8g({{"rooms.yml", S8gRoom}, {"objects.yml", objects}, {"wiring.yml", renamed}}).built);
}

TEST_CASE("S8g: a wall's own surface runs over the room's bands with `bands: false`, above them without")
{
    // The north wall's textures, and the faces of the band texture on the whole map.
    const auto wallTextures = [](const std::string &wallEntry, std::set<std::string> &north, size_t &bandFaces)
    {
        const std::string rooms = std::string(S8gRoom)
            + "    bands:\n      - {height: 128, surface: {texture: band, size: [128, 128]}}\n"
              "    walls:\n      - " + wallEntry + "\n";
        const S8gBuilt built =
            buildS8g({{"rooms.yml", rooms}, {"objects.yml", "format: 0\nstart: {room: room:a, at: [128, 128]}\n"}});
        REQUIRE(built.built);
        REQUIRE(built.map);

        for (const OpenYAMM::Game::IndoorFace &face : built.map->faces)
        {
            bool onNorth = !face.vertexIndices.empty();

            for (const uint16_t index : face.vertexIndices)
            {
                onNorth = onNorth && built.map->vertices[index].y == 1024;
            }

            if (onNorth && face.textureName != "floor" && face.textureName != "ceil")
            {
                north.insert(face.textureName);
            }

            bandFaces += face.textureName == "band" ? 1 : 0;
        }
    };

    // As before: the band below 128, the wall's surface above it (MM6's Hive: hvwl5a and a trim under the dome).
    std::set<std::string> north;
    size_t bandFaces = 0;
    wallTextures("{wall: north, surface: {texture: special, size: [128, 128]}}", north, bandFaces);
    CHECK(north == std::set<std::string>{"band", "special"});
    const size_t withBand = bandFaces;

    // `bands: false`: the whole wall is the wall's surface; the other three walls keep their band.
    north.clear();
    bandFaces = 0;
    wallTextures("{wall: north, surface: {texture: special, size: [128, 128]}, bands: false}", north, bandFaces);
    CHECK(north == std::set<std::string>{"special"});
    CHECK(bandFaces >= 3);
    CHECK(bandFaces < withBand);
}

TEST_CASE("S8g: rules.no_spells writes the scene's runtime restriction, and only when asked")
{
    const std::string objects = "format: 0\nstart: {room: room:a, at: [128, 128]}\n";
    const S8gBuilt plain = buildS8g({{"rooms.yml", S8gRoom}, {"objects.yml", objects}});
    REQUIRE(plain.built);
    REQUIRE(plain.scene);
    CHECK(plain.sceneText.find("runtime_restrictions") == std::string::npos);
    CHECK(plain.scene->runtimeRestrictions.allowSpellcasting);

    const S8gBuilt warded = buildS8g({{"project.yml", "format: 0\nid: testmap\nworld: mm7\nkind: indoor\n"
                                                      "rules: {no_spells: true}\n"},
        {"rooms.yml", S8gRoom}, {"objects.yml", objects}});
    REQUIRE(warded.built);
    REQUIRE(warded.scene);
    CHECK_FALSE(warded.scene->runtimeRestrictions.allowSpellcasting);
    CHECK(warded.scene->runtimeRestrictions.allowRest);
    CHECK(warded.scene->runtimeRestrictions.allowSaveGame);
    CHECK(warded.sceneText.find("runtime_restrictions:\n  allow_spellcasting: false\n") != std::string::npos);
}

TEST_CASE("S8g: an indoor map's bolster row is written when map_stats.bolster asks for it")
{
    const std::filesystem::path tables = s8gScratch("bolster");
    s8gWrite(tables / "map_stats.txt", "#\tName\tFile\n64\tErathia\t7out03.odm\n78\tThe Temple of Baa\t7d04.blv\n");
    s8gWrite(tables / "bolster_maps.txt",
        "#\tNote\tContinent\tBolster kind\tSpells\tSummons\tWeather\tBolster extra\tProfs max rarity\tCustom sky\t"
        "Rain\tSnow\r\n"
        "64\tErathia\t2\tLowerToEqual\tx\t-\tx\t0\t30\t\t\tx\r\n"
        "78\tThe Temple of Baa\t2\tLowerToEqual\tx\t-\t-\t0\t0\t\r\n");
    Project project;
    ProjectFile &card = project.files["project.yml"];
    card.name = "project.yml";
    std::vector<std::string> changes;
    std::string errorMessage;

    // Without the word an indoor map gets no row (as before).
    card.document = YAML::Load("format: 0\nid: xeen_xd21\nworld: mm7\nkind: indoor\nname: Robbers' Den\n"
        "map_stats: {id: 9137, slots: []}\n");
    CHECK_FALSE(outdoorWeatherRow(project).written);

    // With it: a plain row on the world's continent, LowerToEqual, new spells, as the shipped dungeons.
    card.document = YAML::Load("format: 0\nid: xeen_xd21\nworld: mm7\nkind: indoor\nname: Robbers' Den\n"
        "map_stats: {id: 9137, slots: [], bolster: LowerToEqual}\n");
    REQUIRE(outdoorWeatherRow(project).written);
    REQUIRE(upsertOutdoorWeatherRow(project, tables, changes, errorMessage));
    CHECK(s8gRead(tables / "bolster_maps.txt").find("\r\n9137\tRobbers' Den\t2\tLowerToEqual\tx\t-\t-\t0\t\t\r\n")
        != std::string::npos);
    REQUIRE(changes.size() == 1);
    CHECK(changes[0].find("a plain row, bolster LowerToEqual") != std::string::npos);

    // With a reference: the reference's row under the map's number, the kind as asked; `none` writes 0.
    card.document = YAML::Load("format: 0\nid: xeen_xd21\nworld: mm7\nkind: indoor\nname: Robbers' Den\n"
        "map_stats: {id: 9137, reference: 7d04.blv, bolster: none}\n");
    REQUIRE(upsertOutdoorWeatherRow(project, tables, changes, errorMessage));
    CHECK(s8gRead(tables / "bolster_maps.txt").find("\r\n9137\tRobbers' Den\t2\t0\tx\t-\t-\t0\t0\t\r\n")
        != std::string::npos);

    // An outdoor map keeps its row as before; the word changes only the kind.
    card.document = YAML::Load("format: 0\nid: xeen_x1\nworld: mm7\nkind: outdoor\nname: Vertigo Meadows\n"
        "map_stats: {id: 9130, slots: [], bolster: LowerToEqual}\n");
    REQUIRE(upsertOutdoorWeatherRow(project, tables, changes, errorMessage));
    CHECK(s8gRead(tables / "bolster_maps.txt").find("\r\n9130\tVertigo Meadows\t2\tLowerToEqual\tx\t-\t-\t0\t\t\r\n")
        != std::string::npos);
    card.document = YAML::Load("format: 0\nid: xeen_x2\nworld: mm7\nkind: outdoor\nname: Rivercity\n"
        "map_stats: {id: 9136, reference: 7out03.odm, bolster: AllToEqual}\n");
    REQUIRE(upsertOutdoorWeatherRow(project, tables, changes, errorMessage));
    CHECK(s8gRead(tables / "bolster_maps.txt").find("\r\n9136\tRivercity\t2\tAllToEqual\tx\t-\tx\t0\t30\t\t\tx\r\n")
        != std::string::npos);
    std::filesystem::remove_all(tables);
}

TEST_CASE("S8g: maps installed into one mount keep each other's rows, and the mount gains the root's new rows")
{
    const std::filesystem::path scratch = s8gScratch("mount");
    const std::filesystem::path assets = scratch / "assets";
    const std::filesystem::path mount = scratch / "mount";
    const std::string travelHeading = "Key map\tUp\tSide\tDays\tDown\tSide\tDays\tLeft\tSide\tDays\tRight\tSide\tDays\t"
        "StraightTravel\tNotes\r\n";
    s8gWrite(assets / "engine" / "data_tables" / "map_stats.txt",
        "#\tName\tFile\r\n64\tErathia\t7out03.odm\r\n\r\n");
    s8gWrite(assets / "engine" / "data_tables" / "outdoor_travels.txt",
        travelHeading + "7out03.odm\t\t\t\t\t\t\t7out13.odm\tleft\t5\t7out02.odm\tright\t5\t\tErathia\r\n");
    std::filesystem::create_directories(assets / "worlds" / "mm7");

    // Two new outdoor maps side by side, each with a fake build: the hub west of the meadow.
    const auto project = [&scratch](const std::string &id, const std::string &card) -> Project
    {
        s8gWrite(scratch / id / "project.yml", card);
        s8gWrite(scratch / (id + "_build") / (id + ".odm"), "odm");
        s8gWrite(scratch / (id + "_build") / (id + ".scene.yml"), "scene");
        s8gWrite(scratch / (id + "_build") / (id + ".lua"), "lua");
        Project loaded;
        std::vector<ProjectIssue> issues;
        loadProject(scratch / id, loaded, issues);
        return loaded;
    };
    const Project meadow = project("xeen_x1", "format: 0\nid: xeen_x1\nworld: mm7\nkind: outdoor\nname: Meadow\n"
        "map_stats: {id: 9130, slots: []}\n"
        "neighbours:\n  - {id: edge:west, to: xeen_x2.odm, kind: edge, side: west, days: 3}\n");
    const Project hub = project("xeen_x2", "format: 0\nid: xeen_x2\nworld: mm7\nkind: outdoor\nname: Hub\n"
        "map_stats: {id: 9136, reference: 7out03.odm}\n"
        "neighbours:\n  - {id: edge:east, to: xeen_x1.odm, kind: edge, side: east, days: 3}\n"
        "  - {id: edge:west, to: 7out03.odm, kind: edge, side: west, days: 5, one_way: true}\n");
    std::vector<std::string> installed;
    std::string errorMessage;
    REQUIRE_MESSAGE(installBuildIntoMount(meadow, scratch / "xeen_x1_build", mount, assets, installed, errorMessage),
        errorMessage);
    // A map installed into the root after the mount took its copy.
    s8gWrite(assets / "engine" / "data_tables" / "map_stats.txt",
        "#\tName\tFile\r\n64\tErathia\t7out03.odm\r\n9137\tRobbers' Den\txeen_xd21.blv\r\n\r\n");
    REQUIRE_MESSAGE(installBuildIntoMount(hub, scratch / "xeen_x2_build", mount, assets, installed, errorMessage),
        errorMessage);

    const std::string travels = s8gRead(mount / "engine" / "data_tables" / "outdoor_travels.txt");
    INFO(travels);
    // The meadow's row stands after the hub's install: west to the hub's east start ("left"); the hub's east to the
    // meadow's west start ("right"); the hub's west to Erathia's east start, one way.
    CHECK(travels.find("xeen_x1.odm\t\t\t\t\t\t\txeen_x2.odm\tleft\t3\t\t\t\t\tMeadow") != std::string::npos);
    CHECK(travels.find("xeen_x2.odm\t\t\t\t\t\t\t7out03.odm\tleft\t5\txeen_x1.odm\tright\t3\t\tHub")
        != std::string::npos);
    CHECK(travels.find("7out03.odm\t\t\t\t\t\t\t7out13.odm\tleft\t5\t7out02.odm\tright\t5\t\tErathia\r\n")
        != std::string::npos);

    const std::string stats = s8gRead(mount / "engine" / "data_tables" / "map_stats.txt");
    INFO(stats);
    CHECK(stats.find("\r\n9130\tMeadow\txeen_x1.odm") != std::string::npos);
    CHECK(stats.find("\r\n9136\tHub\txeen_x2.odm") != std::string::npos);
    CHECK(stats.find("\r\n9137\tRobbers' Den\txeen_xd21.blv\r\n") != std::string::npos);
    CHECK(stats.find("Erathia") != std::string::npos);
    // One row each, again after a second install of the meadow.
    REQUIRE(installBuildIntoMount(meadow, scratch / "xeen_x1_build", mount, assets, installed, errorMessage));
    const std::string again = s8gRead(mount / "engine" / "data_tables" / "map_stats.txt");
    CHECK(again.find("xeen_x1.odm") == again.rfind("xeen_x1.odm"));
    CHECK(again.find("xeen_xd21.blv") == again.rfind("xeen_xd21.blv"));
    CHECK(again.find("xeen_x2.odm") != std::string::npos);
    std::filesystem::remove_all(scratch);
}
