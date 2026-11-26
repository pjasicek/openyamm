// ODM v2 in the studio (core/OutdoorGrid, devdocs/hesper DECISIONS.md H-33): a project of another terrain side builds
// an OpenYAMM ODM v2 map the game reads back, its rim lies outside the larger walked square, things past the classic
// frame keep their coordinates and texels, and the party walks there.
#include "core/OutdoorBuild.h"
#include "core/OutdoorGrid.h"
#include "core/OutdoorLowering.h"
#include "core/OutdoorRim.h"
#include "core/Schema.h"
#include "core/Sketch.h"
#include "core/Walk.h"

#include "game/outdoor/OutdoorMapData.h"

#include <doctest/doctest.h>
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <random>
#include <string>
#include <vector>

using namespace OpenYAMM;
using namespace OpenYAMM::Studio;

namespace
{
const std::filesystem::path V2Assets = OPENYAMM_DEV_ASSETS_DIR;

const char *V2Plan =
    "format: 0\n"
    "entrances:\n  - {id: entrance:start, space: town:vale, kind: arrival, facing: s}\n"
    "height_bands:\n  - {id: band:vale, range: [576, 704]}\n"
    "spaces:\n  - id: town:vale\n    kind: town\n    buildings:\n"
    "      - {id: building:home, type: house, count: 1, footprint_cells: [[2, 1.5]]}\n";

// Level land at 640 over a map of `side` cells, a house, the start, a tower past the classic frame and the rim's
// entries.
std::string v2Sketch(int side, const std::string &rim)
{
    const std::string far = std::to_string(side);
    return "format: 0\n" + (rim.empty() ? std::string() : "frame:\n" + rim)
        + "heights:\n  bands:\n    - {band: band:vale, polygon: [[0, 0], [" + far + ", 0], [" + far + ", " + far
        + "], [0, " + far + "]]}\n"
        "districts:\n  - space: town:vale\n    polygon: [[36, 36], [64, 36], [64, 64], [36, 64]]\n    plots:\n"
        "      - {building: building:home, index: 1, at: [40, 40], facing: s, house: 904, title: Home}\n"
        "points:\n  - {id: entrance:start, at: [50, 56], facing: n}\n"
        "structures:\n"
        "  - {id: thing:far_tower, kind: obelisk, at: [" + std::to_string(side - 10) + ", " + std::to_string(side - 10)
        + "], height: 1600, sides: 8, title: Far tower}\n";
}

Project v2Project(int side, const std::string &rim = {})
{
    std::string card = "format: 0\nid: v2test\nname: V2 test\nworld: mm8\nkind: outdoor\nprofile: odm\n"
        "map_stats: {id: 9951, slots: []}\n";

    if (side != OutdoorClassicSide)
    {
        card += "terrain: {side: " + std::to_string(side) + "}\n";
    }

    Project project;

    for (const auto &[name, text] : std::vector<std::pair<std::string, std::string>>{
             {"project.yml", card}, {"plan.yml", V2Plan}, {"sketch.yml", v2Sketch(side, rim)}})
    {
        ProjectFile file;
        file.name = name;
        file.text = text;
        file.document = YAML::Load(text);

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

std::vector<uint8_t> readFileBytes(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    return std::vector<uint8_t>((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
}

std::string readFileText(const std::filesystem::path &path)
{
    const std::vector<uint8_t> bytes = readFileBytes(path);
    return std::string(bytes.begin(), bytes.end());
}

// Builds into a fresh folder under the system's temporary folder; with the dev assets when they are there.
std::filesystem::path builtV2(const Project &given, BuildResult &result)
{
    Project project = given;
    project.root = std::filesystem::temp_directory_path() / ("oymap_v2_" + std::to_string(std::random_device{}()));
    BuildOptions options;
    options.outputDirectory = project.root / "build";

    if (std::filesystem::is_directory(V2Assets / "engine"))
    {
        options.assetRoot = V2Assets;
    }

    const bool built = buildOutdoorProject(project, options, result);

    for (const ProjectIssue &issue : result.issues)
    {
        MESSAGE(issue.file << ": " << issue.path << ": " << issue.message);
    }

    REQUIRE(built);
    return project.root;
}
}

TEST_CASE("ODM v2: the grid of a side: classic at 128, the walked square grown with the side at 160")
{
    const OutdoorGrid classic = outdoorGridOfSide(128);
    CHECK(classic.side == 128);
    CHECK(classic.playableFirst == 19);
    CHECK(classic.playableLast == 109);
    CHECK(classic.partyBounds == 23143);

    const OutdoorGrid wide = outdoorGridOfSide(160);
    CHECK(wide.side == 160);
    CHECK(wide.playableFirst == 24);
    CHECK(wide.playableLast == 136);
    CHECK(wide.partyBounds == 28928);

    // A side the format cannot hold is the classic grid.
    CHECK(outdoorGridOfSide(161).side == 128);
    CHECK(outdoorGridOfSide(512).side == 128);

    CHECK(outdoorNodeCount() == 128);
    {
        const OutdoorGridScope scope(160);
        CHECK(outdoorNodeCount() == 160);
        CHECK(sketchMapCells() == 160.0);
        CHECK(outdoorGroundNodes() == 161);
        {
            const OutdoorGridScope inner(128);
            CHECK(outdoorNodeCount() == 128);
        }
        CHECK(outdoorNodeCount() == 160);
    }
    CHECK(outdoorNodeCount() == 128);

    CHECK(outdoorProjectSide(v2Project(160)) == 160);
    CHECK(outdoorProjectSide(v2Project(128)) == 128);
}

TEST_CASE("ODM v2: a 160 project builds an ODM v2 the game reads back, with a tower past the classic frame")
{
    BuildResult result;
    const std::filesystem::path root = builtV2(v2Project(160), result);
    const std::vector<uint8_t> bytes = readFileBytes(root / "build" / "v2test.odm");
    REQUIRE(bytes.size() > 0x60);
    CHECK(std::string(reinterpret_cast<const char *>(bytes.data()) + 0x40) == "OpenYAMM ODM v2");
    CHECK(bytes[0x50] == 160);
    CHECK(bytes[0x51] == 0);

    const std::optional<Game::OutdoorMapData> map = Game::OutdoorMapDataLoader().loadFromBytes(bytes);
    REQUIRE(map.has_value());
    CHECK(map->terrainSide == 160);
    CHECK(map->heightMap.size() == 160u * 160u);
    CHECK(map->tileMap.size() == 160u * 160u);
    // Level land at 640 (20 steps of 32) everywhere, the far corner too.
    CHECK(map->heightMap[0] == 20);
    CHECK(map->heightMap[160u * 160u - 1] == 20);

    // The tower at cells (150, 150): (150 - 80) * 512 = 35 840 east and south, past the classic frame's 32 768; its
    // faces keep their coordinates and their texels fit the format without being clamped to its ends.
    const auto tower = std::find_if(map->bmodels.begin(), map->bmodels.end(), [](const Game::OutdoorBModel &model)
    {
        return model.name == "thing:far_tower";
    });
    REQUIRE(tower != map->bmodels.end());
    CHECK(tower->minX > 32768);
    CHECK(tower->maxY < -32768);

    for (const Game::OutdoorBModelFace &face : tower->faces)
    {
        for (const int16_t texel : face.textureUs)
        {
            CHECK(texel > -32768);
            CHECK(texel < 32767);
        }
    }

    const YAML::Node build = YAML::Load(readFileText(root / "build" / "build.json"));
    CHECK(build["terrain_side"].as<int>() == 160);
    CHECK(build["outdoor_bounds"][1].as<int>() == 28928);
    CHECK(build["counts"]["height_samples"].as<int>() == 25600);
    std::filesystem::remove_all(root);

    // The classic project writes no side.
    BuildResult classic;
    const std::filesystem::path classicRoot = builtV2(v2Project(128), classic);
    const YAML::Node classicBuild = YAML::Load(readFileText(classicRoot / "build" / "build.json"));
    CHECK_FALSE(classicBuild["terrain_side"].IsDefined());
    const std::vector<uint8_t> classicBytes = readFileBytes(classicRoot / "build" / "v2test.odm");
    REQUIRE(classicBytes.size() > 0x60);
    CHECK(std::string(reinterpret_cast<const char *>(classicBytes.data()) + 0x40) != "OpenYAMM ODM v2");
    std::filesystem::remove_all(classicRoot);
}

TEST_CASE("ODM v2: the rim of a 160 map lies outside nodes 24 to 136; a ridge's crest stands 15 out by default")
{
    const std::string rim = "  playable: [24, 24, 112, 112]\n  rim:\n"
        "    - {side: north, form: ridge, height: [2400, 2400], floor: 640}\n"
        "    - {side: south, form: level, height: 1600, meet: 4}\n";
    LoweredOutdoorMap plain;
    LoweredOutdoorMap shaped;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(v2Project(160), plain, issues));
    REQUIRE(lowerOutdoorProject(v2Project(160, rim), shaped, issues));
    REQUIRE(issues.empty());
    REQUIRE(shaped.samples.size() == 160u * 160u);
    const auto at = [](const LoweredOutdoorMap &lowered, int x, int y)
    {
        return lowered.samples[static_cast<size_t>(y) * 160 + x] * 32;
    };

    // The walked square is the land of the heights alone.
    for (int y = 24; y <= 136; y += 4)
    {
        for (int x = 24; x <= 136; x += 4)
        {
            CHECK(at(shaped, x, y) == at(plain, x, y));
        }
    }

    // North: the crest 15 rows out from row 24 (row 9) at the ridge's height; the land at the square's edge.
    CHECK(at(shaped, 80, 24) == 640);
    int crestRow = -1;
    int crestHeight = 0;

    for (int y = 0; y < 24; ++y)
    {
        if (at(shaped, 80, y) > crestHeight)
        {
            crestHeight = at(shaped, 80, y);
            crestRow = y;
        }
    }

    CHECK(crestHeight >= 2300);
    CHECK(crestRow >= 24 - 15 - 3);
    CHECK(crestRow <= 24 - 15 + 3);

    // South: a shelf at 1600 from 4 rows out of the square (row 140) to the map's last row (159).
    CHECK(at(shaped, 80, 145) == 1600);
    CHECK(at(shaped, 80, 159) == 1600);

    // A crest farther out than the wider rim allows is refused, one it allows is taken.
    LoweredOutdoorMap refused;
    std::vector<ProjectIssue> refusedIssues;
    CHECK_FALSE(lowerOutdoorProject(v2Project(160, "  rim:\n    - {side: north, form: ridge, height: [2000, 2400], "
        "floor: 640, crest: 21}\n"), refused, refusedIssues));
    CHECK(std::any_of(refusedIssues.begin(), refusedIssues.end(), [](const ProjectIssue &issue)
    {
        return issue.message.find("4 to 20 cells out") != std::string::npos;
    }));
    LoweredOutdoorMap far;
    std::vector<ProjectIssue> farIssues;
    CHECK(lowerOutdoorProject(v2Project(160, "  rim:\n    - {side: north, form: ridge, height: [2000, 2400], "
        "floor: 640, crest: 18}\n"), far, farIssues));
}

TEST_CASE("ODM v2: the sketch's checks read the side: cells to 160, a map_cells that is not the side is refused")
{
    std::vector<ProjectIssue> issues;
    validateSketch(v2Project(160), issues);
    CHECK(issues.empty());

    // At 128 the tower at cell 150 lies outside the map.
    Project classic = v2Project(128);
    ProjectFile &sketch = classic.files["sketch.yml"];
    sketch.text = v2Sketch(160, {});
    sketch.document = YAML::Load(sketch.text);
    validateSketch(classic, issues);
    CHECK(std::any_of(issues.begin(), issues.end(), [](const ProjectIssue &issue)
    {
        return issue.message.find("cells run from 0 to 128") != std::string::npos;
    }));

    issues.clear();
    Project wrong = v2Project(160);
    ProjectFile &wrongSketch = wrong.files["sketch.yml"];
    wrongSketch.text = "map_cells: 128\n" + wrongSketch.text;
    wrongSketch.document = YAML::Load(wrongSketch.text);
    validateSketch(wrong, issues);
    CHECK(std::any_of(issues.begin(), issues.end(), [](const ProjectIssue &issue)
    {
        return issue.path == "map_cells";
    }));
}

TEST_CASE("ODM v2: the party walks past the classic square on a 160 map, on the game's ground")
{
    if (!std::filesystem::is_directory(V2Assets / "engine"))
    {
        MESSAGE("no asset root: skipped");
        return;
    }

    BuildResult result;
    const std::filesystem::path root = builtV2(v2Project(160), result);
    const std::filesystem::path build = root / "build";
    WalkSession walk;
    std::string error;
    REQUIRE_MESSAGE(walk.load(readFileBytes(build / "v2test.odm"), readFileText(build / "v2test.walk.yml"),
        readFileText(V2Assets / "engine" / "data_tables" / "decoration_data.txt"),
        readFileBytes(build / "v2test.walk.terrain"), error), error);
    REQUIRE(walk.outdoor());

    // From 32 000 east, three seconds east: past the classic map's edge (32 768, where a classic map holds the party
    // half a cell inside), on the level land at 640.
    WalkPose pose = walk.placeEye(32000.0f, 0.0f, 640.0f + 160.0f);

    for (int frame = 0; frame < 180; ++frame)
    {
        pose = walk.step(0.0f, WalkForward, 1.0f / 60.0f);
    }

    CHECK(pose.x > 33000.0f);
    // The game holds a party on the terrain a unit over it.
    CHECK(pose.footZ >= 640.0f);
    CHECK(pose.footZ <= 642.0f);
    CHECK(pose.grounded);
    std::filesystem::remove_all(root);
}
