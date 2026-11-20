// S8a (devdocs/map_studio/S8_PLAN.md): overlay projects that write what the game's G1, G2 and G5 read: ladders in a
// scene overlay (the base list with changes, removals and additions), monsters and floor items appended after the base
// map's (their actor numbers following the base scene's), and cinematics overlays merged by name.
#include "doctest/doctest.h"

#include "cli/Rpc.h"
#include "core/Import.h"
#include "core/IndoorBuild.h"
#include "core/MapLoad.h"
#include "core/SceneOverlay.h"

#include "game/gameplay/CinematicLibrary.h"

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
const std::filesystem::path S8aAssets = OPENYAMM_DEV_ASSETS_DIR;

bool haveMm9Maps()
{
    return std::filesystem::is_regular_file(S8aAssets / "worlds" / "mm9" / "maps" / "bathhouse.scene.yml")
        && std::filesystem::is_regular_file(S8aAssets / "worlds" / "mm9" / "maps" / "isleofashes.cinematics.yml");
}

std::filesystem::path s8aScratch(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s8a_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

void s8aWrite(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

std::string s8aRead(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

// Imports a shipped MM9 map into <root>/<name> as an overlay project with the id `id`.
std::filesystem::path importMm9(const std::filesystem::path &root, const std::string &map, const std::string &id)
{
    const std::filesystem::path project = root / id;
    std::string error;
    AssetSession session;
    LoadedMap loaded;
    REQUIRE(session.open(S8aAssets, "mm9", error));
    REQUIRE(loadMap(session, map, loaded, error));
    std::filesystem::create_directories(project);
    std::vector<std::string> written;
    REQUIRE(importMapAsProject(loaded, project, written, error));
    std::string card = s8aRead(project / "project.yml");
    const std::string stem = std::filesystem::path(map).stem().string();
    card.replace(card.find("id: " + stem), 4 + stem.size(), "id: " + id);
    s8aWrite(project / "project.yml", card);
    return project;
}

bool buildAt(const std::filesystem::path &projectRoot, BuildResult &result, std::string &problems)
{
    Project project;
    std::vector<ProjectIssue> loadIssues;
    REQUIRE(loadProject(projectRoot, project, loadIssues));
    BuildOptions options;
    options.assetRoot = S8aAssets;
    const bool built = buildProject(project, options, result);

    for (const ProjectIssue &issue : result.issues)
    {
        problems += issue.file + " " + issue.path + ": " + issue.message + "\n";
    }

    return built;
}

// The base scene of a shipped MM9 map with the overlay text applied by the game's own reader.
Game::IndoorSceneData sceneWithOverlay(const std::string &stem, const std::string &overlayText, size_t &baseActors,
    size_t &baseItems)
{
    std::string error;
    AssetSession session;
    REQUIRE(session.open(S8aAssets, "mm9", error));
    const std::optional<std::string> base = session.files().readTextFile("Data/games/" + stem + ".scene.yml");
    REQUIRE(base);
    const Game::IndoorSceneYmlLoader loader;
    std::optional<Game::IndoorSceneData> scene = loader.loadFromText(*base, error);
    REQUIRE_MESSAGE(scene, error);
    baseActors = scene->initialState.actors.size();
    baseItems = scene->initialState.spriteObjects.size();
    REQUIRE_MESSAGE(loader.applyOverlayFromText(*scene, overlayText, error), error);
    return *scene;
}
}

TEST_CASE("S8a: an overlay changes, removes and adds ladders, adds a monster and an item, and writes its cinematics")
{
    if (!haveMm9Maps())
    {
        MESSAGE("no MM9 maps in the development assets: skipped");
        return;
    }

    const std::filesystem::path root = s8aScratch("bath");
    const std::filesystem::path project = importMm9(root, "bathhouse.blv", "s8a_test");
    const YAML::Node lock = YAML::Load(s8aRead(project / "ids.lock.yml"));
    // The base ladder and cinematic under stable ids (`oymap import`).
    REQUIRE(lock["ladders"]["ladder:ladder0"]);
    CHECK(lock["ladders"]["ladder:ladder0"].as<int>() == 0);
    CHECK(lock["cinematics"]["cinematic:ebora_escape"].as<int>() == 0);
    const std::string replaced = lock["events"].begin()->first.Scalar();

    s8aWrite(project / "objects.yml", "format: 1\nscene:\n"
        "  ladders:\n    - {id: ladder:pole, position: [9000, 296, -1256], facing: e, height: 200, grab_in_air: true}\n"
        "  monsters:\n    - {id: monster:guard, position: [9000, 296.96, -1256.96], monster: 9183, immobile: true}\n"
        "  items:\n    - {id: item:sword, position: [9050, 296.96, -1256.96], item: 1}\n"
        "  changes:\n    - {of: ladder:ladder0, offset: [10, 0, 0], facing: n, grab_in_air: true}\n");
    s8aWrite(project / "wiring.yml", "format: 0\nevents:\n  - {id: evt:test, replaces: " + replaced
        + ", preset: text, condition: {kills: {monster: monster:guard}}, text: Dead.}\n"
        "cinematics:\n  - id: cinematic:look\n    shots:\n"
        "      - {seconds: 1, at: [9000, 0, -1000], look_at: monster:guard}\n"
        "    cues:\n      - {at: 0.5, monster: monster:guard, action: face, look_at: [9154, 296, -1256]}\n"
        "  - id: cinematic:ebora_escape\n    shots:\n      - {seconds: 2, at: [9000, 0, -1000], yaw: 90, pitch: 0}\n");
    BuildResult result;
    std::string problems;
    REQUIRE_MESSAGE(buildAt(project, result, problems), problems);
    CHECK(result.files == std::vector<std::string>{"bathhouse_s8a_test.lua", "bathhouse_s8a_test.scene.yml",
        "bathhouse_s8a_test.cinematics.yml", "build.json"});
    const YAML::Node buildJson = YAML::Load(s8aRead(project / "build" / "build.json"));
    CHECK(buildJson["counts"]["cinematics_added"].as<int>() == 1);
    CHECK(buildJson["counts"]["cinematics_replaced"].as<int>() == 1);
    CHECK(buildJson["counts"]["scene_added"].as<int>() == 3);
    CHECK(buildJson["counts"]["scene_changed"].as<int>() == 1);

    // The game's reader: the base ladder moved and turned, the new one after it; the actor and the item appended.
    size_t baseActors = 0;
    size_t baseItems = 0;
    const std::string overlayText = s8aRead(project / "build" / "bathhouse_s8a_test.scene.yml");
    const Game::IndoorSceneData scene = sceneWithOverlay("bathhouse", overlayText, baseActors, baseItems);
    REQUIRE(scene.ladders.size() == 2);
    CHECK(scene.ladders[0].id == "Ladder0");
    CHECK(scene.ladders[0].bottom[0] == doctest::Approx(9164.56));
    CHECK(scene.ladders[0].topExit[0] == doctest::Approx(9287.44));
    CHECK(scene.ladders[0].facingDegrees == doctest::Approx(90.0));
    CHECK(scene.ladders[0].grabInAir);
    CHECK(scene.ladders[1].id == "pole");
    CHECK(scene.ladders[1].top[2] == doctest::Approx(-1056.0));
    CHECK(scene.ladders[1].topExit[0] == doctest::Approx(9064.0));
    CHECK(scene.ladders[1].grabInAir);
    REQUIRE(baseActors > 0);
    REQUIRE(scene.initialState.actors.size() == baseActors + 1);
    CHECK(scene.initialState.overlayActorCount == 1);
    CHECK(scene.initialState.actors.back().monsterInfoId == 9183);
    CHECK(scene.initialState.actors.back().immobile);
    CHECK(scene.initialState.actors.back().sectorId > 0);
    REQUIRE(scene.initialState.spriteObjects.size() == baseItems + 1);
    CHECK(scene.initialState.spriteObjects.back().x == 9050);

    // What names the monster names it by its number after the base map's actors: the kill check and the cinematic.
    const std::string lua = s8aRead(project / "build" / "bathhouse_s8a_test.lua");
    CHECK(lua.find("ActorKillCheck.ActorIdOe, " + std::to_string(baseActors) + ",") != std::string::npos);
    std::string error;
    const std::optional<Game::CinematicLibrary> overlay =
        Game::parseCinematicLibrary(s8aRead(project / "build" / "bathhouse_s8a_test.cinematics.yml"), error);
    REQUIRE_MESSAGE(overlay, error);
    const Game::CinematicDefinition *pLook = overlay->find("look");
    REQUIRE(pLook != nullptr);
    CHECK(pLook->shots[0].keys[0].aim == Game::CinematicAim::Actor);
    CHECK(pLook->shots[0].keys[0].actorIndex == baseActors);
    // (The cue among the letterbox's own.)
    bool faced = false;

    for (const Game::CinematicCue &cue : pLook->cues)
    {
        faced = faced || (cue.kind == Game::CinematicCueKind::ActorFace && cue.actorIndex == baseActors);
    }

    CHECK(faced);

    // Merged over the map's own as the game merges it: ebora_escape replaced in its place, look added after it.
    std::optional<Game::CinematicLibrary> library = Game::parseCinematicLibrary(
        s8aRead(S8aAssets / "worlds" / "mm9" / "maps" / "bathhouse.cinematics.yml"), error);
    REQUIRE(library);
    const size_t shipped = library->cinematics.size();
    Game::mergeCinematicLibrary(*library, Game::CinematicLibrary(*overlay));
    CHECK(library->cinematics.size() == shipped + 1);
    CHECK(library->cinematics[0].id == "ebora_escape");
    CHECK(library->cinematics[0].durationSeconds == doctest::Approx(2.0));

    // Installed into a mount beside the map; a rebuild without cinematics takes the old file away.
    const std::filesystem::path mount = root / "mount";
    Project loaded;
    std::vector<ProjectIssue> loadIssues;
    REQUIRE(loadProject(project, loaded, loadIssues));
    std::vector<std::string> installed;
    REQUIRE_MESSAGE(installBuildIntoMount(loaded, project / "build", mount, S8aAssets, installed, error), error);
    CHECK(std::filesystem::is_regular_file(mount / "worlds/mm9/maps/bathhouse_s8a_test.cinematics.yml"));
    CHECK(std::filesystem::is_regular_file(mount / "worlds/mm9/maps/bathhouse_s8a_test.scene.yml"));

    // Taking the base ladder out: only the overlay's own stays in the list.
    s8aWrite(project / "objects.yml", "format: 1\nscene:\n"
        "  ladders:\n    - {id: ladder:pole, position: [9000, 296, -1256], facing: e, height: 200}\n"
        "  monsters:\n    - {id: monster:guard, position: [9000, 296.96, -1256.96], monster: 9183}\n"
        "  removals: [ladder:ladder0]\n");
    s8aWrite(project / "wiring.yml", "format: 0\nevents:\n  - {id: evt:test, replaces: " + replaced
        + ", preset: text, condition: {kills: {monster: monster:guard}}, text: Dead.}\n");
    BuildResult second;
    problems.clear();
    REQUIRE_MESSAGE(buildAt(project, second, problems), problems);
    CHECK_FALSE(std::filesystem::exists(project / "build" / "bathhouse_s8a_test.cinematics.yml"));
    const Game::IndoorSceneData without =
        sceneWithOverlay("bathhouse", s8aRead(project / "build" / "bathhouse_s8a_test.scene.yml"), baseActors,
            baseItems);
    REQUIRE(without.ladders.size() == 1);
    CHECK(without.ladders[0].id == "pole");
    Project reloaded;
    REQUIRE(loadProject(project, reloaded, loadIssues));
    REQUIRE_MESSAGE(installBuildIntoMount(reloaded, project / "build", mount, S8aAssets, installed, error), error);
    CHECK_FALSE(std::filesystem::exists(mount / "worlds/mm9/maps/bathhouse_s8a_test.cinematics.yml"));

    // view.overlay: the base ladder taken out, the project's things added, the map's cinematic kept.
    REQUIRE(callRpcMethod("session.configure", "{\"asset_root\":\"" + S8aAssets.string() + "\"}").find("error")
        == std::string::npos);
    const YAML::Node answer = YAML::Load(callRpcMethod("view.overlay", "{\"project\":\"" + project.string() + "\"}"));
    REQUIRE(answer["result"]);
    std::map<std::string, std::string> states;

    for (const YAML::Node &thing : answer["result"]["things"])
    {
        states[thing["id"].Scalar()] = thing["state"].Scalar();
    }

    CHECK(states["ladder:ladder0"] == "removed");
    CHECK(states["ladder:pole"] == "added");
    CHECK(states["monster:guard"] == "added");
    REQUIRE(answer["result"]["cinematics"]);
    CHECK(answer["result"]["cinematics"][0]["id"].Scalar() == "cinematic:ebora_escape");
    CHECK(answer["result"]["cinematics"][0]["state"].Scalar() == "kept");
    std::filesystem::remove_all(root);
}

TEST_CASE("S8a: what an overlay's ladders, monsters, items and cinematics may not say")
{
    if (!haveMm9Maps())
    {
        MESSAGE("no MM9 maps in the development assets: skipped");
        return;
    }

    const std::filesystem::path root = s8aScratch("words");
    const std::filesystem::path project = importMm9(root, "bathhouse.blv", "s8a_words");
    const auto issuesOf = [&project](const std::string &objects, const std::string &wiring)
    {
        s8aWrite(project / "objects.yml", objects);
        s8aWrite(project / "wiring.yml", wiring);
        BuildResult result;
        std::string problems;
        buildAt(project, result, problems);
        return problems;
    };

    // A word that changes no ladder, a base ladder's id for a new one, a ladder the base map does not have.
    const std::string words = issuesOf("format: 1\nscene:\n  changes:\n    - {of: ladder:ladder0, hp: 3}\n"
        "  ladders:\n    - {id: ladder:ladder0, position: [9000, 296, -1256], facing: e, height: 200}\n"
        "  removals: [ladder:nothing]\n", "format: 0\n");
    CHECK(words.find("`hp` does not change a ladder") != std::string::npos);
    CHECK(words.find("ladder:ladder0 is a base thing's id") != std::string::npos);
    CHECK(words.find("ladder:nothing is no base thing an overlay removes") != std::string::npos);

    // A ladder leaning more than 45 degrees; a peaceful monster (no load event in an overlay); a monster outside every
    // sector of the base map.
    const std::string placed = issuesOf("format: 1\nscene:\n"
        "  ladders:\n"
        "    - {id: ladder:steep, position: [9000, 296, -1256], facing: e, height: 100, top_at: [9300, 296]}\n"
        "  monsters:\n    - {id: monster:calm, position: [9000, 296, -1256], monster: 9183, hostile: false}\n"
        "    - {id: monster:lost, position: [30000, 30000, 9000], monster: 9183}\n", "format: 0\n");
    CHECK(placed.find("leans 45 degrees at most") != std::string::npos);
    CHECK(placed.find("cannot make a monster peaceful") != std::string::npos);

    const std::string lost = issuesOf("format: 1\nscene:\n"
        "  monsters:\n    - {id: monster:lost, position: [30000, 30000, 9000], monster: 9183}\n", "format: 0\n");
    CHECK(lost.find("is in no sector of the base map") != std::string::npos);

    // A cue that names neither one of the overlay's events nor one of the base map's; the base map's events are named
    // by their lock ids, the base map's cinematics may be played by theirs.
    const std::string event = YAML::Load(s8aRead(project / "ids.lock.yml"))["events"].begin()->first.Scalar();
    const std::string shot = "format: 0\ncinematics:\n  - id: cinematic:c\n    shots:\n"
        "      - {seconds: 1, at: [9000, 0, -1000], yaw: 0, pitch: 0}\n    cues:\n";
    const std::string unknown = issuesOf("format: 1\n", shot + "      - {at: 0, event: evt:e99999}\n");
    CHECK(unknown.find("nothing in the project has the id evt:e99999") != std::string::npos);
    CHECK(issuesOf("format: 1\n", shot + "      - {at: 0, event: " + event + "}\n").empty());
    const std::string cinematics = s8aRead(project / "build" / "bathhouse_s8a_words.cinematics.yml");
    CHECK(cinematics.find("event: " + event.substr(5)) != std::string::npos);
    const std::string play = issuesOf("format: 1\n", "format: 0\nevents:\n  - {id: evt:p, replaces: " + event
        + ", preset: text, text: x, effects: [{cinematic: cinematic:ebora_escape}]}\n");
    CHECK(play.empty());
    std::filesystem::remove_all(root);
}

TEST_CASE("S8a: the Isle of Ashes example overlay builds its ladder, monster, item and cinematics")
{
    const std::filesystem::path example = std::filesystem::path(OPENYAMM_DEV_ASSETS_DIR).parent_path()
        / "openyamm-studio" / "examples" / "s8a_isle_extras";

    if (!haveMm9Maps() || !std::filesystem::is_directory(example))
    {
        MESSAGE("no MM9 maps or no example: skipped");
        return;
    }

    const std::filesystem::path root = s8aScratch("isle");
    std::filesystem::copy(example, root / "isle", std::filesystem::copy_options::recursive);
    std::filesystem::remove_all(root / "isle" / "build");
    BuildResult result;
    std::string problems;
    REQUIRE_MESSAGE(buildAt(root / "isle", result, problems), problems);
    CHECK(result.cinematicsAdded == 1);
    CHECK(result.cinematicsReplaced == 1);
    size_t baseActors = 0;
    size_t baseItems = 0;
    const Game::IndoorSceneData scene = sceneWithOverlay("isleofashes",
        s8aRead(root / "isle" / "build" / "isleofashes_s8a_extras.scene.yml"), baseActors, baseItems);
    CHECK(baseActors == 77);
    CHECK(scene.initialState.actors.size() == 78);
    CHECK(scene.ladders.size() == 1);
    CHECK(s8aRead(root / "isle" / "build" / "isleofashes_s8a_extras.lua").find("ActorIdOe, 77,") != std::string::npos);
    std::filesystem::remove_all(root);
}
