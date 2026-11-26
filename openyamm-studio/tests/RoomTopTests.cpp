// A room's step event on the tops of its low blocks (IndoorLowering's `TRIGGER_roomtop_<block>` nodes): blocks of one
// kind share a name (every parapet is PARAPET), and two of them in a room that runs a step event once left the indoor
// compiler without the node it was told of (KD's D04, 2026-11-25: "refers to a missing node: TRIGGER_roomtop_PARAPET").
#include "core/IndoorBuild.h"
#include "core/Project.h"

#include "game/indoor/IndoorMapData.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <random>
#include <string>
#include <vector>

using namespace OpenYAMM::Studio;

TEST_CASE("a room's step event runs on the tops of two low parapets in it (TRIGGER_roomtop_ nodes of one name)")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_roomtop_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    std::ofstream(root / "project.yml", std::ios::binary) << "format: 0\nid: testmap\nworld: mm6\nkind: indoor\n";
    std::ofstream(root / "rooms.yml", std::ios::binary)
        << "format: 0\n"
           "themes:\n"
           "  - id: theme:plain\n"
           "    wall: {texture: wall, size: [128, 128]}\n"
           "    floor: {texture: floor, size: [128, 128]}\n"
           "    ceiling: {texture: ceil, size: [128, 128]}\n"
           "defaults: {theme: theme:plain}\n"
           "rooms:\n"
           "  - id: room:a\n"
           "    outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]]\n"
           "    floor: 0\n"
           "    ceiling: 384\n"
           "    parapets:\n"
           "      - {path: [[128, 256], [448, 256]], height: 40}\n"
           "      - {path: [[576, 512], [896, 512]], height: 40}\n";
    std::ofstream(root / "objects.yml", std::ios::binary) << "format: 0\nstart: {room: room:a, at: [512, 64]}\n";
    std::ofstream(root / "wiring.yml", std::ios::binary)
        << "format: 0\nevents:\n  - {id: evt:e1_room, preset: text, trigger: step, source: room:a, text: Stepped.}\n";

    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(root, project, issues));
    BuildOptions options;
    options.outputDirectory = root / "build";
    BuildResult result;
    const bool built = buildProject(project, options, result);

    for (const ProjectIssue &issue : result.issues)
    {
        MESSAGE(issue.file << ": " << issue.path << ": " << issue.message);
    }

    REQUIRE(built);
    std::ifstream stream(root / "build" / "testmap.blv", std::ios::binary);
    const std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    const std::optional<OpenYAMM::Game::IndoorMapData> map = OpenYAMM::Game::IndoorMapDataLoader().loadFromBytes(bytes);
    REQUIRE(map.has_value());

    // Both parapets' tops (40 over the floor) run the room's event, as the floor does.
    size_t tops = 0;

    for (const OpenYAMM::Game::IndoorFace &face : map->faces)
    {
        const bool level = std::all_of(face.vertexIndices.begin(), face.vertexIndices.end(),
            [&map](uint16_t index)
            {
                return map->vertices[index].z == 40;
            });

        if (level && !face.vertexIndices.empty() && face.cogTriggered == 1)
        {
            ++tops;
        }
    }

    CHECK(tops >= 2);
    std::filesystem::remove_all(root);
}
