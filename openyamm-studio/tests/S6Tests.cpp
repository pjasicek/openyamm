// S6 (devdocs/map_studio/S6_PLAN.md): MM9 profiles and extras. Item O: overlay projects that change a shipped map's
// scene (objects.yml `scene`, atmosphere.yml's scene blocks), written as the indoor scene overlay the game applies over
// the base scene; import of the base map's scene things into ids.lock.yml; view.overlay.
#include "doctest/doctest.h"

#include "cli/Rpc.h"
#include "core/Import.h"
#include "core/IndoorBuild.h"
#include "core/MapLoad.h"
#include "core/Mods.h"
#include "core/SceneOverlay.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <fstream>
#include <random>
#include <string>
#include <vector>

using namespace OpenYAMM::Studio;
namespace Game = OpenYAMM::Game;

namespace
{
const std::filesystem::path S6Assets = OPENYAMM_DEV_ASSETS_DIR;

bool haveMm9()
{
    return std::filesystem::is_regular_file(S6Assets / "worlds" / "mm9" / "maps" / "isleofashes.scene.yml");
}

std::filesystem::path s6Scratch(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s6_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

void s6Write(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

std::string s6Read(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

Project memoryProject(const std::vector<std::pair<std::string, std::string>> &texts)
{
    Project project;

    for (const std::pair<std::string, std::string> &entry : texts)
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

// A base scene as the game reads one: two pulsing lights, two sounds, a destructible on cog 7, a water volume and
// two spawn points.
const char *BaseScene = R"(format_version: 1
kind: indoor_scene
source: {geometry_file: tiny.blv}
environment:
  sky_texture: ""
  day_bits_raw: 0
  map_extra_bits_raw: 0
  ceiling: 0
  flags: {foggy: false, raining: false, snowing: false, underwater: false, no_terrain: false, always_dark: false,
    always_light: false, always_foggy: false, red_fog: false}
  fog: {weak_distance: 0, strong_distance: 0}
initial_state:
  location: {respawn_count: 0, last_respawn_day: 0, reputation: 0, alert_status: 0}
  visible_outlines: {bitset_hex: "@OUTLINES@"}
  face_attribute_overrides: []
  decoration_flags: []
  actors: []
  sprite_objects: []
  chests: []
  doors: []
  variables: {map: [@MAPVARS@], decor: [@DECORVARS@]}
spawns:
  - {spawn_index: 0, position: {x: 100, y: 200, z: 0}, radius: 32, type_id: 3, index: 1, attributes: 0, group: 0}
  - {spawn_index: 1, position: {x: 300, y: 400, z: 0}, radius: 32, type_id: 2, index: 2, attributes: 0, group: 0}
pulsing_lights:
  - {key: 40001, position: [10, 20, 30], color: [255, 0, 0], intensity: [0.3, 1, 2, 0], radius: [128, 512, 2, 0], start_on: true}
  - {key: 40002, position: [40, 50, 60], color: [0, 255, 0], intensity: [1, 1, 0, 0], radius: [256, 256, 0, 0], start_on: false}
ambient_sounds:
  - {key: 7, sound: ambient/bell.wav, position: [0, 0, 64], inner_radius: 100, outer_radius: 400, volume: 0.5}
  - {key: 8, sound: ambient/bell.wav, position: [9, 9, 64], inner_radius: 100, outer_radius: 400}
destructibles:
  - {id: 7, name: Wall, cog: 7, hp: 1, damage_enabled: true, trigger_destroy_only: true, center: [0, 0, 0]}
water_volumes:
  - id: Pool
    liquid: water
    pieces:
      - {polygon: [[0, 0], [100, 0], [100, 100], [0, 100]], bottom: -100, top: 0}
)";

// The base scene with the lists the game's reader wants at their lengths.
std::string baseSceneText()
{
    std::string text = BaseScene;
    text.replace(text.find("@OUTLINES@"), 10, std::string(1750, '0'));
    const auto zeros = [](size_t count)
    {
        std::string list = "0";

        for (size_t index = 1; index < count; ++index)
        {
            list += ", 0";
        }

        return list;
    };
    text.replace(text.find("@MAPVARS@"), 9, zeros(75));
    text.replace(text.find("@DECORVARS@"), 11, zeros(125));
    return text;
}

const char *OverlayCard = "format: 0\nid: tweak\nworld: mm9\nkind: indoor\nprofile: region\nbase: tiny.blv\n";
const char *OverlayLock = "format: 0\nevents:\n  evt:e30: 30\nlights:\n  light:k40001: 40001\n  light:k40002: 40002\n"
                          "sounds:\n  sound:a7: 7\n  sound:a8: 8\ndestructibles:\n  destructible:k7: 7\n"
                          "water:\n  water:pool: 0\nspawns:\n  spawn:s0: 0\n  spawn:s1: 1\n";

// The base map's geometry the overlay needs: a quad of cog 7 and one of cog 9.
Game::IndoorMapData tinyMap()
{
    Game::IndoorMapData map;

    for (const std::array<int, 3> &point : std::vector<std::array<int, 3>>{{0, 0, 0}, {200, 0, 0}, {200, 0, 100},
             {0, 0, 100}, {500, 0, 0}, {600, 0, 0}, {600, 0, 50}})
    {
        Game::IndoorVertex vertex;
        vertex.x = static_cast<int16_t>(point[0]);
        vertex.y = static_cast<int16_t>(point[1]);
        vertex.z = static_cast<int16_t>(point[2]);
        map.vertices.push_back(vertex);
    }

    Game::IndoorFace wall;
    wall.vertexIndices = {0, 1, 2, 3};
    wall.cogNumber = 7;
    map.faces.push_back(wall);
    Game::IndoorFace other;
    other.vertexIndices = {4, 5, 6};
    other.cogNumber = 9;
    map.faces.push_back(other);
    return map;
}
}

TEST_CASE("S6 O: the scene overlay keeps the base lists, applies changes and removals, appends additions")
{
    const Project project = memoryProject({{"project.yml", OverlayCard}, {"ids.lock.yml", OverlayLock},
        {"objects.yml",
            "format: 1\nscene:\n"
            "  lights:\n    - {id: light:beacon, position: [1, 2, 3], color: [255, 150, 60], intensity: [0.5, 1],"
            " radius: [600, 1200], frequency: 0.5, phase: 0.25}\n"
            "  sounds:\n    - {id: sound:surf, position: [5, 6, 7], sound: ambient/beachlight.wav, radius: 800,"
            " wait: [2, 4], night_only: true}\n"
            "  spawns:\n    - {id: spawn:camp, position: [700, 800, 9], slot: 2, tier: b, radius: 200}\n"
            "  destructibles:\n    - {id: destructible:boards, cog: 9, hp: 12, material: wood}\n"
            "  water:\n    - id: water:pond\n      pieces:\n        - {polygon: [[0, 0], [10, 0], [10, 10]], bottom: -5,"
            " top: 0}\n      tint: [0, 0.4, 0.5]\n"
            "  changes:\n    - {of: light:k40002, on: true, color: [1, 2, 3], radius: [300, 400]}\n"
            "    - {of: sound:a7, volume: 0.1, sound_radius: 900}\n"
            "    - {of: destructible:k7, hp: 40, trigger_only: false, destroyed_event: evt:e30}\n"
            "    - {of: water:pool, current: [10, 0, 0]}\n"
            "  removals: [sound:a8, spawn:s1, light:k40001]\n"},
        {"atmosphere.yml", "format: 0\nscene_fog: {color_rgb: [10, 20, 30], near_distance: 100, far_distance: 900}\n"}});

    std::vector<ProjectIssue> issues;
    checkSceneOverlayWords(project, issues);
    REQUIRE(issues.empty());
    IdsLock lock = IdsLock::fromDocument(project.document("ids.lock.yml"));
    SceneOverlayText overlay;
    std::vector<std::string> warnings;
    const Game::IndoorMapData map = tinyMap();
    REQUIRE(
        buildSceneOverlayText(project, baseSceneText(), map, LoweredIndoorMap(), lock, overlay, issues, warnings));
    CHECK(issues.empty());
    CHECK(overlay.added == 5);
    CHECK(overlay.changed == 4);
    CHECK(overlay.removed == 3);

    const YAML::Node written = YAML::Load(overlay.text);
    CHECK(written["kind"].Scalar() == "indoor_scene_overlay");
    // Lights: the removed one gone, the changed one first, the new one with the first overlay key.
    REQUIRE(written["pulsing_lights"].size() == 2);
    CHECK(written["pulsing_lights"][0]["key"].as<int>() == 40002);
    CHECK(written["pulsing_lights"][0]["start_on"].as<bool>());
    CHECK(written["pulsing_lights"][0]["radius"][1].as<int>() == 400);
    CHECK(written["pulsing_lights"][1]["key"].as<int>() == 49001);
    CHECK(written["pulsing_lights"][1]["intensity"][2].as<double>() == doctest::Approx(0.5));
    CHECK(written["pulsing_lights"][1]["radius"][3].as<double>() == doctest::Approx(0.25));
    CHECK(lock.lights.at("light:beacon") == 49001);
    // Sounds: a8 removed, a7 changed, the new one numbered from 60001.
    REQUIRE(written["ambient_sounds"].size() == 2);
    CHECK(written["ambient_sounds"][0]["volume"].as<double>() == doctest::Approx(0.1));
    CHECK(written["ambient_sounds"][0]["outer_radius"].as<int>() == 900);
    CHECK(written["ambient_sounds"][1]["key"].as<int>() == 60001);
    CHECK(written["ambient_sounds"][1]["inner_radius"].as<int>() == 200);
    CHECK(written["ambient_sounds"][1]["night_only"].as<bool>());
    // Destructibles: the base wall changed, the boards on cog 9 at their faces' middle with wood's sound.
    REQUIRE(written["destructibles"].size() == 2);
    CHECK(written["destructibles"][0]["hp"].as<int>() == 40);
    CHECK_FALSE(written["destructibles"][0]["trigger_destroy_only"].as<bool>());
    CHECK(written["destructibles"][0]["destroyed_event"].as<int>() == 30);
    CHECK(written["destructibles"][1]["id"].as<int>() == 60001);
    CHECK(written["destructibles"][1]["cog"].as<int>() == 9);
    CHECK(written["destructibles"][1]["center"][0].as<int>() == 550);
    CHECK(written["destructibles"][1]["sound"].Scalar() == "Events/shatterwood02.wav");
    CHECK(written["destructibles"][1]["effect"].Scalar() == "openyamm:fx/destructible/wood");
    // Water: the base pool with its current, the new pond.
    REQUIRE(written["water_volumes"].size() == 2);
    CHECK(written["water_volumes"][0]["current"][0].as<int>() == 10);
    CHECK(written["water_volumes"][1]["id"].Scalar() == "pond");
    // Spawns: the new one as authored content (slot 2, tier b: index 8), the removed one by its place and index.
    REQUIRE(written["authored_content"]["spawns"].size() == 1);
    CHECK(written["authored_content"]["spawns"][0]["index"].as<int>() == 8);
    CHECK(written["authored_content"]["spawns"][0]["type_id"].as<int>() == 3);
    REQUIRE(written["removals"]["spawns"].size() == 1);
    CHECK(written["removals"]["spawns"][0]["position"][0].as<int>() == 300);
    CHECK(written["removals"]["spawns"][0]["index"].as<int>() == 2);
    // The scene's fog from atmosphere.yml.
    CHECK(written["fog"]["far_distance"].as<int>() == 900);

    // The game's own overlay reader takes it over the base scene.
    const Game::IndoorSceneYmlLoader loader;
    std::string error;
    const std::string baseText = baseSceneText();
    std::optional<Game::IndoorSceneData> scene = loader.loadFromText(baseText, error);
    REQUIRE_MESSAGE(scene, error);
    REQUIRE_MESSAGE(loader.applyOverlayFromText(*scene, overlay.text, error), error);
    CHECK(scene->pulsingLights.size() == 2);
    CHECK(scene->ambientSounds.size() == 2);
    CHECK(scene->destructibles.size() == 2);
    CHECK(scene->waterVolumes.size() == 2);
    CHECK(scene->fog.enabled);
    size_t standing = 0;

    for (const Game::IndoorSceneSpawn &spawn : scene->spawns)
    {
        standing += spawn.spawn.typeId != 0 ? 1 : 0;
    }

    CHECK(standing == 2);

    // A second build keeps the numbers the lock gave.
    IdsLock again = lock;
    SceneOverlayText second;
    REQUIRE(buildSceneOverlayText(project, baseSceneText(), map, LoweredIndoorMap(), again, second, issues, warnings));
    CHECK(second.text == overlay.text);
}

TEST_CASE("S6 O: the overlay's words are checked: kinds of changes, base ids, overlay-only `scene`")
{
    {
        const Project project = memoryProject({{"project.yml", OverlayCard}, {"ids.lock.yml", OverlayLock},
            {"objects.yml", "format: 1\nscene:\n  changes:\n    - {of: light:k40001, hp: 3}\n"
                            "    - {of: sound:a7, volume: 0.2}\n    - {of: sound:a7, loop: false}\n"
                            "    - {of: spawn:s0, radius: 3}\n  removals: [sound:a7, sound:a99]\n"
                            "  lights:\n    - {id: light:k40002, position: [0, 0, 0]}\n"}});
        std::vector<ProjectIssue> issues;
        checkSceneOverlayWords(project, issues);
        std::string all;

        for (const ProjectIssue &issue : issues)
        {
            all += issue.path + ": " + issue.message + "\n";
        }

        CHECK(all.find("`hp` does not change a light") != std::string::npos);
        CHECK(all.find("sound:a7 is changed twice") != std::string::npos);
        CHECK(all.find("sound:a7 is both changed and removed") != std::string::npos);
        CHECK(all.find("sound:a99 is no base thing") != std::string::npos);
        CHECK(all.find("spawn:s0 is no base thing an overlay changes") != std::string::npos);
        CHECK(all.find("light:k40002 is a base thing's id") != std::string::npos);
    }

    {
        // A new map places its things in rooms: `scene` is refused there.
        const Project project = memoryProject({{"project.yml", "format: 0\nid: crypt\nworld: mm6\nkind: indoor\n"},
            {"objects.yml", "format: 1\nscene:\n  removals: [spawn:s0]\n"}});
        std::vector<ProjectIssue> issues;
        checkSceneOverlayWords(project, issues);
        REQUIRE(issues.size() == 1);
        CHECK(issues[0].message.find("overlay projects") != std::string::npos);
    }

    {
        // A destructible on a cog no face has, and on no faces at all.
        const Project project = memoryProject({{"project.yml", OverlayCard}, {"ids.lock.yml", OverlayLock},
            {"objects.yml", "format: 1\nscene:\n  destructibles:\n    - {id: destructible:x, cog: 77, hp: 1}\n"
                            "    - {id: destructible:y, hp: 1}\n"}});
        IdsLock lock = IdsLock::fromDocument(project.document("ids.lock.yml"));
        SceneOverlayText overlay;
        std::vector<ProjectIssue> issues;
        std::vector<std::string> warnings;
        CHECK_FALSE(buildSceneOverlayText(project, baseSceneText(), tinyMap(), LoweredIndoorMap(), lock, overlay,
            issues, warnings));
        REQUIRE(issues.size() == 2);
        CHECK(issues[0].message.find("no face of the base map has cog 77") != std::string::npos);
        CHECK(issues[1].message.find("is made of the base map's faces") != std::string::npos);
    }
}

TEST_CASE("S6 O: an MM9 region imports with its scene things, builds an overlay, installs it and is described")
{
    if (!haveMm9())
    {
        MESSAGE("no MM9 world in the development assets: skipped");
        return;
    }

    const std::filesystem::path root = s6Scratch("isle");
    const std::filesystem::path project = root / "isle";
    std::string error;

    {
        AssetSession session;
        LoadedMap map;
        REQUIRE(session.open(S6Assets, "mm9", error));
        REQUIRE(loadMap(session, "isleofashes.blv", map, error));
        std::filesystem::create_directories(project);
        std::vector<std::string> written;
        REQUIRE(importMapAsProject(map, project, written, error));
    }

    const YAML::Node card = YAML::Load(s6Read(project / "project.yml"));
    CHECK(card["profile"].Scalar() == "region");
    const YAML::Node lock = YAML::Load(s6Read(project / "ids.lock.yml"));
    CHECK(lock["destructibles"]["destructible:k7"].as<int>() == 7);
    CHECK(lock["water"]["water:bluewater0"].as<int>() == 0);
    CHECK(lock["spawns"]["spawn:s6"].as<int>() == 6);
    CHECK(lock["sounds"].size() > 100);

    std::string cardText = s6Read(project / "project.yml");
    cardText.replace(cardText.find("id: isleofashes"), 15, "id: s6_test");
    s6Write(project / "project.yml", cardText);
    s6Write(project / "objects.yml",
        "format: 1\nscene:\n  lights:\n    - {id: light:beacon, position: [1400, 4800, 1000], color: [255, 150, 60]}\n"
        "  changes:\n    - {of: destructible:k520, hp: 40}\n  removals: [spawn:s6]\n");

    Project loaded;
    std::vector<ProjectIssue> loadIssues;
    REQUIRE(loadProject(project, loaded, loadIssues));
    BuildOptions options;
    options.assetRoot = S6Assets;
    BuildResult result;
    const bool built = buildProject(loaded, options, result);
    std::string problems;

    for (const ProjectIssue &issue : result.issues)
    {
        problems += issue.file + " " + issue.path + ": " + issue.message + "\n";
    }

    REQUIRE_MESSAGE(built, problems);
    // Only the scene changes: no script, the scene overlay and the build record.
    CHECK(result.files == std::vector<std::string>{"isleofashes_s6_test.scene.yml", "build.json"});
    CHECK(result.lockChanged);
    CHECK(YAML::Load(s6Read(project / "ids.lock.yml"))["lights"]["light:beacon"].as<int>() == 49001);
    const YAML::Node buildJson = YAML::Load(s6Read(project / "build" / "build.json"));
    CHECK(buildJson["counts"]["scene_added"].as<int>() == 1);
    CHECK(buildJson["counts"]["scene_changed"].as<int>() == 1);
    CHECK(buildJson["counts"]["scene_removed"].as<int>() == 1);

    // Installed into a mount: the overlay beside the base map, no script; the base map's files untouched.
    const std::filesystem::path mount = root / "mount";
    Project reloaded;
    REQUIRE(loadProject(project, reloaded, loadIssues));
    std::vector<std::string> installed;
    REQUIRE_MESSAGE(installBuildIntoMount(reloaded, project / "build", mount, S6Assets, installed, error), error);
    CHECK(std::filesystem::is_regular_file(mount / "worlds/mm9/maps/isleofashes_s6_test.scene.yml"));
    CHECK_FALSE(std::filesystem::exists(mount / "worlds/mm9/events/maps/isleofashes_s6_test.lua"));
    CHECK_FALSE(std::filesystem::exists(mount / "worlds/mm9/maps/isleofashes.blv"));

    // The game reads the region with the overlay from the mount.
    {
        AssetSession::setExtraMount(mount);
        AssetSession session;
        LoadedMap map;
        REQUIRE(session.open(S6Assets, "mm9", error));
        REQUIRE(loadMap(session, "isleofashes.blv", map, error));
        AssetSession::setExtraMount({});
        REQUIRE(map.indoorScene);
        CHECK(map.sceneOverlayPaths.size() >= 1);
        bool beacon = false;

        for (const Game::IndoorPulsingLight &light : map.indoorScene->pulsingLights)
        {
            beacon = beacon || light.lightKey == 49001;
        }

        CHECK(beacon);
    }

    // view.overlay: the base things with their states, the addition at its place.
    REQUIRE(callRpcMethod("session.configure", "{\"asset_root\":\"" + S6Assets.string() + "\"}").find("error")
        == std::string::npos);
    const YAML::Node answer = YAML::Load(callRpcMethod("view.overlay", "{\"project\":\"" + project.string() + "\"}"));
    REQUIRE(answer["result"]);
    CHECK(answer["result"]["profile"].Scalar() == "region");
    int removed = 0;
    int changed = 0;
    int added = 0;

    for (const YAML::Node &thing : answer["result"]["things"])
    {
        removed += thing["state"].Scalar() == "removed" ? 1 : 0;
        changed += thing["state"].Scalar() == "changed" ? 1 : 0;

        if (thing["state"].Scalar() == "added")
        {
            ++added;
            CHECK(thing["id"].Scalar() == "light:beacon");
            CHECK(thing["at"][2].as<int>() == 1000);
        }
    }

    CHECK(removed == 1);
    CHECK(changed == 1);
    CHECK(added == 1);
    // A project that is no overlay is refused.
    CHECK(YAML::Load(callRpcMethod("view.overlay", "{\"project\":\"" + project.string() + "/nothing\"}"))["error"]);

    // Taking the scene words out again: the build makes the script only and install takes the overlay away.
    s6Write(project / "objects.yml", "format: 1\n");
    s6Write(project / "wiring.yml", "format: 0\nevents:\n  - {id: evt:stone, preset: text, replaces: evt:e390, "
                                    "text: Hum.}\n");
    Project plain;
    REQUIRE(loadProject(project, plain, loadIssues));
    BuildResult second;
    REQUIRE(buildProject(plain, options, second));
    CHECK(second.files == std::vector<std::string>{"isleofashes_s6_test.lua", "build.json"});
    REQUIRE(installBuildIntoMount(plain, project / "build", mount, S6Assets, installed, error));
    CHECK_FALSE(std::filesystem::exists(mount / "worlds/mm9/maps/isleofashes_s6_test.scene.yml"));
    CHECK(std::filesystem::is_regular_file(mount / "worlds/mm9/events/maps/isleofashes_s6_test.lua"));
    std::filesystem::remove_all(root);
}

namespace
{
const std::filesystem::path BreakwaterExample = std::filesystem::path(OPENYAMM_DEV_ASSETS_DIR).parent_path()
    / "openyamm-studio" / "examples" / "s6_breakwater";

bool haveMm6()
{
    return std::filesystem::is_directory(S6Assets / "worlds" / "mm6");
}

// A copy of the S6 test map with `objects` and `wiring` changed by text replacement.
std::filesystem::path breakwaterCopy(const std::string &name,
    const std::vector<std::pair<std::string, std::pair<std::string, std::string>>> &changes = {})
{
    const std::filesystem::path root = s6Scratch(name) / "breakwater";
    std::filesystem::create_directories(root);

    for (const char *pFile : {"project.yml", "plan.yml", "rooms.yml", "objects.yml", "wiring.yml"})
    {
        std::string text = s6Read(BreakwaterExample / pFile);

        for (const auto &change : changes)
        {
            if (change.first == pFile)
            {
                const size_t at = text.find(change.second.first);
                REQUIRE_MESSAGE(at != std::string::npos, change.second.first);
                text.replace(at, change.second.first.size(), change.second.second);
            }
        }

        s6Write(root / pFile, text);
    }

    return root;
}

std::string issueText(const std::vector<ProjectIssue> &issues)
{
    std::string all;

    for (const ProjectIssue &issue : issues)
    {
        all += issue.file + " " + issue.path + ": " + issue.message + "\n";
    }

    return all;
}

bool buildCopy(const std::filesystem::path &root, BuildResult &result)
{
    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(root, project, issues));
    BuildOptions options;
    options.assetRoot = S6Assets;
    return buildProject(project, options, result);
}
}

TEST_CASE("S6 D, W, L, C: the test map's destructibles, water, ladder, sounds and cinematic in its scene and files")
{
    if (!haveMm6())
    {
        MESSAGE("no MM6 world in the development assets: skipped");
        return;
    }

    const std::filesystem::path root = breakwaterCopy("all");
    BuildResult result;
    REQUIRE_MESSAGE(buildCopy(root, result), issueText(result.issues));
    CHECK(result.warnings.empty());
    CHECK(std::find(result.files.begin(), result.files.end(), "studio06.cinematics.yml") != result.files.end());

    const YAML::Node scene = YAML::LoadFile((root / "build" / "studio06.scene.yml").string());
    REQUIRE(scene["destructibles"].size() == 2);
    // The barricade: a platform's faces by their cog, its centre in the doorway; its event by number.
    CHECK(scene["destructibles"][0]["name"].Scalar() == "barricade");
    CHECK(scene["destructibles"][0]["cog"].as<int>() > 0);
    CHECK(scene["destructibles"][0]["center"][0].as<int>() == 1120);
    CHECK(scene["destructibles"][0]["destroyed_event"].as<int>() > 0);
    CHECK(scene["destructibles"][0]["effect"].Scalar() == "openyamm:fx/destructible/wood");
    // The barrel: a decoration by its sprite key.
    CHECK(scene["destructibles"][1]["decoration_cog"].as<int>() > 0);
    CHECK_FALSE(scene["destructibles"][1]["cog"]);
    // The pool: one prism over the level from its bed to the surface.
    REQUIRE(scene["water_volumes"].size() == 1);
    CHECK(scene["water_volumes"][0]["id"].Scalar() == "pool");
    CHECK(scene["water_volumes"][0]["pieces"][0]["bottom"].as<int>() == -192);
    CHECK(scene["water_volumes"][0]["pieces"][0]["top"].as<int>() == -16);
    CHECK(scene["water_volumes"][0]["pieces"][0]["polygon"].size() == 4);
    CHECK_FALSE(scene["water_volumes"][0]["fog"]);
    // A night sound; a ladder that is taken only from the ground.
    CHECK(scene["ambient_sounds"][0]["night_only"].as<bool>());
    CHECK_FALSE(scene["ladders"][0]["grab_in_air"]);

    const YAML::Node lock = YAML::LoadFile((root / "ids.lock.yml").string());
    CHECK(lock["destructibles"]["destructible:barricade"].as<int>() == 1);
    CHECK(lock["destructibles"]["destructible:barrel"].as<int>() == 2);

    // The cinematic: the barrel's place as the first shot's aim, a moving second shot, the event cue by number, and
    // the load event playing it with its done event.
    const YAML::Node cinematics = YAML::LoadFile((root / "build" / "studio06.cinematics.yml").string());
    const YAML::Node arrival = cinematics["cinematics"]["arrival"];
    REQUIRE(arrival["shots"].size() == 3);
    CHECK(arrival["shots"][0]["look_at"][0].as<int>() == 880);
    CHECK(arrival["shots"][1]["keys"].size() == 2);
    CHECK(arrival["shots"][1]["keys"][1]["at"].as<int>() == 3);
    CHECK(arrival["shots"][2]["party"].as<bool>());
    CHECK(arrival["cues"][2]["event"].as<int>() == lock["events"]["evt:arrival_lamp"].as<int>());
    const std::string lua = s6Read(root / "build" / "studio06.lua");
    CHECK(lua.find("evt.PlayCinematic(\"arrival\", " + std::to_string(lock["events"]["evt:arrival_done"].as<int>())
        + ")") != std::string::npos);

    // Effects and the condition on destructibles.
    const std::filesystem::path wired = breakwaterCopy("wired", {{"wiring.yml", {"      - gold: 25\n",
        "      - gold: 25\n      - destroy: destructible:barricade\n      - unbreakable: destructible:barrel\n"
        "      - damage_destructible: {of: destructible:barricade, amount: 7}\n"
        "    condition: {not: {destroyed: destructible:barricade}}\n"}}});
    BuildResult wiredResult;
    REQUIRE_MESSAGE(buildCopy(wired, wiredResult), issueText(wiredResult.issues));
    const std::string wiredLua = s6Read(wired / "build" / "studio06.lua");
    CHECK(wiredLua.find("evt.DestroyDestructible(1)") != std::string::npos);
    CHECK(wiredLua.find("evt.SetDestructibleDamage(2, false)") != std::string::npos);
    CHECK(wiredLua.find("evt.DamageDestructible(1, 7)") != std::string::npos);
    CHECK(wiredLua.find("evt.IsDestructibleDestroyed(1)") != std::string::npos);

    // The pool's own fog under water (A6, P4) goes into its volume as given; one the game refuses is said.
    const std::filesystem::path fogged = breakwaterCopy("fogged", {{"objects.yml", {"tint: [0.1, 0.4, 0.6]}",
        "tint: [0.1, 0.4, 0.6], fog: {color_rgb: [20, 70, 80], near_distance: 64, far_distance: 1200, sky: 1}}"}}});
    BuildResult foggedResult;
    REQUIRE_MESSAGE(buildCopy(fogged, foggedResult), issueText(foggedResult.issues));
    const YAML::Node foggedScene = YAML::LoadFile((fogged / "build" / "studio06.scene.yml").string());
    REQUIRE(foggedScene["water_volumes"][0]["fog"]);
    CHECK(foggedScene["water_volumes"][0]["fog"]["color_rgb"][1].as<int>() == 70);
    CHECK(foggedScene["water_volumes"][0]["fog"]["far_distance"].as<int>() == 1200);
    const std::filesystem::path badFog = breakwaterCopy("badfog", {{"objects.yml", {"tint: [0.1, 0.4, 0.6]}",
        "tint: [0.1, 0.4, 0.6], fog: {color_rgb: [20, 70, 80], near_distance: 900, far_distance: 100}}"}}});
    BuildResult badFogResult;
    CHECK_FALSE(buildCopy(badFog, badFogResult));
    CHECK(issueText(badFogResult.issues).find("water[0].fog: the game refuses this fog") != std::string::npos);

    // A barrel, a light and a sound in a room with a liquid floor: their markers take the floor's surface and are no
    // faces of the compiled map, so they are no missing liquid faces (A6, P1 and P2's false warning).
    const std::filesystem::path liquidYard = breakwaterCopy("liquidyard", {{"rooms.yml",
        {"    floor: {texture: oflr, size: [128, 128]}\n    ceiling: {texture: d2ceil4, size: [256, 256], sky: true}",
            "    floor: {texture: oflr, size: [128, 128], liquid: water}\n"
            "    ceiling: {texture: d2ceil4, size: [256, 256], sky: true}"}}});
    BuildResult liquidResult;
    REQUIRE_MESSAGE(buildCopy(liquidYard, liquidResult), issueText(liquidResult.issues));
    for (const std::string &warning : liquidResult.warnings)
    {
        CHECK_MESSAGE(!warning.starts_with("liquid and flow"), warning);
    }

    // A build without cinematics leaves no file of them behind.
    const std::filesystem::path plain = breakwaterCopy("plain", {{"wiring.yml", {"      - cinematic: {id: "
        "cinematic:arrival, then: evt:arrival_done}\n", ""}}});
    {
        std::string text = s6Read(plain / "wiring.yml");
        text = text.substr(0, text.find("cinematics:"));
        s6Write(plain / "wiring.yml", text);
    }
    BuildResult plainResult;
    REQUIRE_MESSAGE(buildCopy(plain, plainResult), issueText(plainResult.issues));
    CHECK_FALSE(std::filesystem::exists(plain / "build" / "studio06.cinematics.yml"));
    std::filesystem::remove_all(root.parent_path());
    std::filesystem::remove_all(wired.parent_path());
    std::filesystem::remove_all(plain.parent_path());
}

TEST_CASE("S6 D, W, C: what the build refuses")
{
    if (!haveMm6())
    {
        MESSAGE("no MM6 world in the development assets: skipped");
        return;
    }

    const std::vector<std::pair<std::string, std::pair<std::string, std::pair<std::string, std::string>>>> cases = {
        {"is none of them", {"objects.yml", {"of: platform:barricade", "of: room:yard"}}},
        {"is no event of wiring.yml", {"objects.yml", {"on_destroyed: evt:barricade_down", "on_destroyed: evt:nope"}}},
        {"is no destructible", {"wiring.yml", {"      - gold: 25\n", "      - gold: 25\n      - destroy: deco:barrel\n"}}},
        {"is no room or level", {"objects.yml", {"of: level:pool, top: -16", "of: deco:barrel, top: -16"}}},
        {"at or under its bottom", {"objects.yml", {"of: level:pool, top: -16", "of: level:pool, top: -300"}}},
        {"looks at one thing", {"wiring.yml", {"look_at: deco:barrel, fov: 70", "look_at: deco:barrel, yaw: 3, "
            "pitch: 0, fov: 70"}}},
        {"is no point and nothing the map placed", {"wiring.yml", {"look_at: deco:barrel", "look_at: deco:none"}}},
        {"fov", {"wiring.yml", {"fov: 70", "fov: 150"}}},
        {"within the shot", {"wiring.yml", {"{seconds: 3, at: [960", "{seconds: 4, at: [960"}}},
        {"a subtitle stays its `seconds`", {"wiring.yml", {", seconds: 2.5}", "}"}}},
        {"is no cinematic of wiring.yml", {"wiring.yml", {"cinematic: {id: cinematic:arrival,", "cinematic: {id: "
            "cinematic:other,"}}},
        {"a cue does one thing", {"wiring.yml", {"{at: 5, shake: 0.3, seconds: 1}", "{at: 5, shake: 0.3, sound: "
            "x.wav}"}}},
        // Past the studio's rules, the game's own parser (G4): a shot longer than the format's hour.
        {"the game refuses the cinematics file", {"wiring.yml", {"{seconds: 1, party: true}", "{seconds: 4000, "
            "party: true}"}}},
    };

    for (const auto &entry : cases)
    {
        CAPTURE(entry.first);
        const std::filesystem::path root = breakwaterCopy("refuse", {entry.second});
        BuildResult result;
        CHECK_FALSE(buildCopy(root, result));
        CHECK(issueText(result.issues).find(entry.first) != std::string::npos);
        std::filesystem::remove_all(root.parent_path());
    }
}

TEST_CASE("S6 M: a table's rows: changed cells and added rows found, and applied over another base")
{
    const std::string base = "header\tname\tfile\r\nkey\tname\tfile\r\n1\tOne\tone.blv\r\n2\tTwo\ttwo.blv\r\n";
    const std::string changed = "header\tname\tfile\r\nkey\tname\tfile\r\n1\tOne\tone.blv\r\n2\tSecond\ttwo.blv\r\n"
                                "9306\tStore\tstudio06.blv\r\n";
    std::string overrideText;
    std::string appendText;
    diffTableRows(base, changed, overrideText, appendText);
    CHECK(overrideText == "key\tcolumn\tvalue\n2\t#1\tSecond\n");
    CHECK(appendText == "9306\tStore\tstudio06.blv\n");
    // Applied over the base it gives the changed table, line endings kept.
    CHECK(applyTableRows(base, overrideText, appendText) == changed);
    // Over a base another mod changed first: both mods' rows; the same row twice is one row.
    const std::string other = applyTableRows(base, "", "9400\tOther\tother.blv\n");
    const std::string both = applyTableRows(other, overrideText, appendText);
    CHECK(both.find("9400\tOther") != std::string::npos);
    CHECK(both.find("9306\tStore") != std::string::npos);
    CHECK(applyTableRows(both, "", appendText) == both);
}

TEST_CASE("S6 M: a mod packed from two projects, installed merged, switched off and on; named installs")
{
    if (!haveMm6() || !haveMm9())
    {
        MESSAGE("no MM6 or MM9 world in the development assets: skipped");
        return;
    }

    const std::filesystem::path map = breakwaterCopy("mod");
    BuildResult built;
    REQUIRE_MESSAGE(buildCopy(map, built), issueText(built.issues));
    const std::filesystem::path root = map.parent_path();

    ModPackRequest request;
    request.projects = {map};
    request.assetRoot = S6Assets;
    request.out = root / "out";
    request.id = "s6_test";
    request.name = "S6 test";
    ModPackResult packed;
    std::string error;
    REQUIRE_MESSAGE(packMod(request, packed, error), error);
    const YAML::Node manifest = YAML::LoadFile((packed.folder / "mod.yml").string());
    CHECK(manifest["id"].Scalar() == "s6_test");
    CHECK(manifest["maps"][0]["kind"].Scalar() == "new");
    CHECK(manifest["map_numbers"][0].as<int>() == 9306);
    CHECK(manifest["tables"][0]["table"].Scalar() == "map_stats.txt");
    CHECK(std::filesystem::is_regular_file(packed.folder / "worlds/mm6/maps/studio06.blv"));
    CHECK(std::filesystem::is_regular_file(packed.folder / "worlds/mm6/maps/studio06.cinematics.yml"));
    CHECK_FALSE(std::filesystem::exists(packed.folder / "worlds/mm6/maps/studio06.studio.yml"));
    CHECK(s6Read(packed.folder / "tables/map_stats.txt.append.txt").rfind("9306\t", 0) == 0);

    const std::filesystem::path mods = root / "install" / "mods";
    ModInstallResult installed;
    REQUIRE_MESSAGE(installMod(packed.folder, mods, S6Assets, "merged", installed, error), error);
    CHECK(std::filesystem::is_regular_file(mods / "worlds/mm6/maps/studio06.blv"));
    const std::string table = s6Read(mods / "engine/data_tables/map_stats.txt");
    CHECK(table.find("9306\tThe Breakwater Store") != std::string::npos);
    // The rest of the table is the asset root's.
    CHECK(table.size() > s6Read(S6Assets / "engine/data_tables/map_stats.txt").size());

    ModInstallResult off;
    REQUIRE(setModEnabled("s6_test", false, mods, S6Assets, off, error));
    CHECK_FALSE(std::filesystem::exists(mods / "worlds/mm6/maps/studio06.blv"));
    CHECK_FALSE(std::filesystem::exists(mods / "engine/data_tables/map_stats.txt"));
    JsonWriter list;
    list.beginObject();
    writeModList(mods, list);
    list.endObject();
    const YAML::Node listed = YAML::Load(list.take());
    CHECK_FALSE(listed["merged"][0]["enabled"].as<bool>());

    ModInstallResult on;
    REQUIRE(setModEnabled("s6_test", true, mods, S6Assets, on, error));
    CHECK(std::filesystem::is_regular_file(mods / "worlds/mm6/maps/studio06.blv"));
    CHECK(s6Read(mods / "engine/data_tables/map_stats.txt") == table);
    CHECK_FALSE(setModEnabled("nothing", false, mods, S6Assets, on, error));

    // Named: the folder under its id and the enabled list; the game does not read it yet (said).
    const std::filesystem::path named = root / "named" / "mods";
    ModInstallResult namedResult;
    REQUIRE(installMod(packed.folder, named, S6Assets, "named", namedResult, error));
    CHECK(std::filesystem::is_regular_file(named / "s6_test" / "mod.yml"));
    CHECK(YAML::LoadFile((named / "enabled.yml").string())["enabled"][0].Scalar() == "s6_test");
    CHECK(namedResult.warnings.size() == 1);
    std::filesystem::remove_all(root);
}
