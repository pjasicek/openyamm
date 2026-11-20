// S8b (devdocs/map_studio/S8_PLAN.md): terrain for new open-air BLVs. atmosphere.yml `ground` turned into the weight
// image, the material file and the scene's terrain block (core/GroundTerrain.h); the PNG writer (core/RgbaPng.h);
// build and install of an indoor project with ground.
#include "doctest/doctest.h"

#include "core/GroundTerrain.h"
#include "core/IndoorBuild.h"
#include "core/RgbaPng.h"

#include "game/render/TerrainMaterialConfig.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <filesystem>
#include <fstream>
#include <random>
#include <string>
#include <vector>

using namespace OpenYAMM::Studio;
namespace Game = OpenYAMM::Game;

namespace
{
const std::filesystem::path S8bAssets = OPENYAMM_DEV_ASSETS_DIR;
const std::filesystem::path S8bExample = std::filesystem::path(OPENYAMM_DEV_ASSETS_DIR).parent_path()
    / "openyamm-studio" / "examples" / "s8b_meadow";

bool haveMm9Terrain()
{
    return std::filesystem::is_regular_file(S8bAssets / "worlds" / "mm9" / "terrain_materials" / "world.yml")
        && std::filesystem::is_regular_file(S8bAssets / "engine" / "terrain_materials" / "library.yml");
}

std::filesystem::path s8bScratch(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s8b_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

std::string s8bRead(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::string((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
}

void s8bWrite(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

// Inflate of the streams deflateZlib writes (stored and fixed-code blocks), to read them back.
class BitReader
{
public:
    explicit BitReader(const std::vector<uint8_t> &bytes)
        : m_bytes(bytes)
    {
    }

    uint32_t bits(int count)
    {
        uint32_t value = 0;

        for (int bit = 0; bit < count; ++bit)
        {
            value |= uint32_t((m_bytes.at(m_position >> 3) >> (m_position & 7)) & 1u) << bit;
            ++m_position;
        }

        return value;
    }

    // A Huffman code's next bit, most significant first.
    uint32_t codeBits(int count)
    {
        uint32_t value = 0;

        for (int bit = 0; bit < count; ++bit)
        {
            value = (value << 1) | bits(1);
        }

        return value;
    }

private:
    const std::vector<uint8_t> &m_bytes;
    size_t m_position = 16;
};

std::vector<uint8_t> inflateFixed(const std::vector<uint8_t> &stream)
{
    static const int LengthBase[] = {3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83,
        99, 115, 131, 163, 195, 227, 258};
    static const int LengthExtra[] = {0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5,
        5, 0};
    static const int DistanceBase[] = {1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769,
        1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577};
    static const int DistanceExtra[] = {0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11,
        11, 12, 12, 13, 13};
    BitReader reader(stream);
    std::vector<uint8_t> out;
    bool last = false;

    while (!last)
    {
        last = reader.bits(1) == 1;
        const uint32_t type = reader.bits(2);
        REQUIRE(type == 1);

        while (true)
        {
            // The fixed literal/length code: 7, 8 or 9 bits.
            uint32_t code = reader.codeBits(7);
            int symbol = -1;

            if (code <= 0x17)
            {
                symbol = int(code) + 256;
            }
            else
            {
                code = (code << 1) | reader.codeBits(1);

                if (code >= 0x30 && code <= 0xbf)
                {
                    symbol = int(code) - 0x30;
                }
                else if (code >= 0xc0 && code <= 0xc7)
                {
                    symbol = int(code) - 0xc0 + 280;
                }
                else
                {
                    code = (code << 1) | reader.codeBits(1);
                    symbol = int(code) - 0x190 + 144;
                }
            }

            if (symbol < 256)
            {
                out.push_back(uint8_t(symbol));
                continue;
            }

            if (symbol == 256)
            {
                break;
            }

            const int lengthCode = symbol - 257;
            const int length = LengthBase[lengthCode] + int(reader.bits(LengthExtra[lengthCode]));
            const int distanceCode = int(reader.codeBits(5));
            const int distance = DistanceBase[distanceCode] + int(reader.bits(DistanceExtra[distanceCode]));
            REQUIRE(size_t(distance) <= out.size());

            for (int index = 0; index < length; ++index)
            {
                out.push_back(out[out.size() - size_t(distance)]);
            }
        }
    }

    return out;
}

// A map of two floors side by side 2048 wide at the frame's middle: grass (x -2048..0) and dirt (0..2048), and a
// dirt shelf 256 over the grass's west half.
Game::IndoorMapData twoFloorMap(bool shelf)
{
    Game::IndoorMapData map;

    const auto addFace = [&map](const std::vector<std::array<int, 3>> &corners, const std::string &texture)
    {
        Game::IndoorFace face;

        for (const std::array<int, 3> &corner : corners)
        {
            face.vertexIndices.push_back(uint16_t(map.vertices.size()));
            map.vertices.push_back({corner[0], corner[1], corner[2]});
        }

        face.textureName = texture;
        map.faces.push_back(face);
    };

    addFace({{-2048, -1024, 0}, {0, -1024, 0}, {0, 1024, 0}, {-2048, 1024, 0}}, "GrassTex");
    addFace({{0, -1024, 0}, {2048, -1024, 0}, {2048, 1024, 0}, {0, 1024, 0}}, "dirttex");
    addFace({{-2048, -1024, 0}, {-2048, -1024, 512}, {-2048, 1024, 512}}, "walltex");

    if (shelf)
    {
        addFace({{-2048, -512, 256}, {-1024, -512, 256}, {-1024, 512, 256}, {-2048, 512, 256}}, "dirttex");
    }

    return map;
}

GroundAssets testAssets()
{
    GroundAssets assets;
    assets.libraryText =
        "version: 1\n"
        "materials:\n"
        "  grass_meadow: {mean_color: [0.378, 0.4258, 0.1895]}\n"
        "  soil: {mean_color: [0.4, 0.3, 0.2]}\n"
        "  rock_cliff: {mean_color: [0.5, 0.5, 0.5]}\n"
        "  grass_patchy: {mean_color: [0.5979, 0.5755, 0.3435]}\n";
    assets.worldMaterialsText =
        "version: 1\n"
        "edge_softness: 110\n"
        "fringe: {strength: 1.6, scale: 2048}\n"
        "materials:\n"
        "  grass: {library: grass_meadow, repeat: 360, meadow: 1.0, variant: grass_patches, variant_amount: 0.25}\n"
        "  dirt: {library: soil, repeat: 520}\n"
        "  cliff: {library: rock_cliff, repeat: 640}\n"
        "  grass_patches: {library: grass_patchy, repeat: 640, tint_scale: [0.5, 0.5, 0.5], meadow: 0.8}\n"
        "slope: {material: cliff, start: 0.36, end: 0.56}\n";
    return assets;
}

const uint8_t *texelAt(const GroundTerrain &terrain, double x, double y)
{
    const double units = 65536.0 / terrain.size;
    const int column = int((x + 32768.0) / units);
    const int row = int((32768.0 - y) / units);
    return terrain.weights.data() + (size_t(row) * size_t(terrain.size) + size_t(column)) * 4;
}
}

TEST_CASE("S8b: the PNG writer's deflate stream reads back to its input and the same input gives the same bytes")
{
    std::mt19937 random(7);
    std::vector<uint8_t> noise(70000);

    for (uint8_t &value : noise)
    {
        value = uint8_t(random() & 0x0f);
    }

    std::vector<uint8_t> flat(300000, 0);
    flat[1234] = 9;

    for (const std::vector<uint8_t> *pData : {&noise, &flat})
    {
        const std::vector<uint8_t> stream = deflateZlib(*pData);
        CHECK(stream[0] == 0x78);
        CHECK(inflateFixed(stream) == *pData);
        CHECK(deflateZlib(*pData) == stream);
    }

    // A flat field compresses to almost nothing.
    CHECK(deflateZlib(flat).size() < 2000);
    const std::vector<uint8_t> rgba(64 * 32 * 4, 200);
    const std::vector<uint8_t> png = encodeRgbaPng(64, 32, rgba);
    CHECK(png.size() > 33);
    CHECK(png[1] == 'P');
    CHECK(png[24] == 8);   // bit depth
    CHECK(png[25] == 6);   // RGBA
}

TEST_CASE("S8b: the nearest-texel fill and the blur behave as scipy's")
{
    // Two seeds on a 16 grid: every texel takes the nearer one's layer.
    std::vector<int16_t> layers(16 * 16, -1);
    layers[2 * 16 + 2] = 0;
    layers[13 * 16 + 12] = 1;
    GroundSteps::fillNearest(layers, 16);
    CHECK(layers[0] == 0);
    CHECK(layers[15 * 16 + 15] == 1);
    CHECK(layers[4 * 16 + 5] == 0);
    CHECK(layers[10 * 16 + 11] == 1);

    // A flat field stays flat, a step softens symmetrically about its edge.
    std::vector<float> flat(32 * 32, 1.0f);
    GroundSteps::gaussianBlur(flat, 32, 3.4375);

    for (const float value : flat)
    {
        CHECK(value == doctest::Approx(1.0).epsilon(1e-6));
    }

    std::vector<float> step(32 * 32, 0.0f);

    for (int y = 0; y < 32; ++y)
    {
        for (int x = 16; x < 32; ++x)
        {
            step[size_t(y) * 32 + size_t(x)] = 1.0f;
        }
    }

    GroundSteps::gaussianBlur(step, 32, 3.4375);
    CHECK(step[10 * 32 + 15] + step[10 * 32 + 16] == doctest::Approx(1.0).epsilon(1e-6));
    CHECK(step[10 * 32 + 2] < 0.01f);
    CHECK(step[10 * 32 + 29] > 0.99f);
}

TEST_CASE("S8b: ground over a built map: the topmost face's layer per texel, the material file the game reads")
{
    const Game::IndoorMapData map = twoFloorMap(true);
    YAML::Node ground = YAML::Load(
        "layers:\n"
        "  - {material: grass, textures: [grasstex], color: [64, 72, 24]}\n"
        "  - {material: dirt, textures: [DirtTex]}\n"
        "grass: worlds/mm9/terrain_decorations/drangheim_blv.yml\n");
    GroundTerrain terrain;
    std::string errorMessage;
    REQUIRE_MESSAGE(buildGroundTerrain(ground, map, testAssets(), "testmap", GroundOptions{}, terrain, errorMessage),
        errorMessage);
    CHECK(terrain.materialsFile == "testmap_blv.yml");
    CHECK(terrain.weightsFile == "testmap_blv_weights0.png");
    CHECK(terrain.size == 2048);
    CHECK(terrain.weightedLayers == 2);
    CHECK(terrain.layers == std::vector<std::string>{"grass", "dirt", "cliff", "grass_patches"});
    CHECK(terrain.groundFaces == 3);
    CHECK(terrain.excludedFaces.empty());

    // Grass in the east of the grass floor, dirt on the dirt floor, dirt on the shelf over the grass.
    CHECK(texelAt(terrain, -512, 0)[0] == 255);
    CHECK(texelAt(terrain, 1024, 0)[1] == 255);
    CHECK(texelAt(terrain, -1536, 0)[1] == 255);
    CHECK(texelAt(terrain, -1536, 0)[2] == 0);
    // Near the floors' border both blend.
    CHECK(texelAt(terrain, 0, 0)[0] > 64);
    CHECK(texelAt(terrain, 0, 0)[1] > 64);

    // The scene block: the textures on the weighed faces, lower case, sorted; the grass file.
    CHECK(terrain.sceneTerrain["materials"].as<std::string>() == "testmap_blv.yml");
    REQUIRE(terrain.sceneTerrain["textures"].size() == 2);
    CHECK(terrain.sceneTerrain["textures"][0].as<std::string>() == "dirttex");
    CHECK(terrain.sceneTerrain["textures"][1].as<std::string>() == "grasstex");
    CHECK(terrain.sceneTerrain["grass"].as<std::string>() == "worlds/mm9/terrain_decorations/drangheim_blv.yml");

    // The material file through the game's reader: tints from the colour (no channel over the brightness ratio),
    // the variant's from its parent's, the slope layer's index.
    std::string parseError;
    const std::optional<Game::OutdoorTerrainMaterialConfig> config =
        Game::parseTerrainMaterialConfig(terrain.materialsText, "x/", "x/testmap_blv.yml", parseError);
    REQUIRE_MESSAGE(config, parseError);
    CHECK(config->weightedLayers == 2);
    CHECK(config->slopeLayer == 2);
    CHECK(config->slopeStart == doctest::Approx(0.36));
    CHECK(config->fringeStrength == doctest::Approx(1.6));
    CHECK(config->layers[0].variant == 3);
    CHECK(config->layers[0].variantAmount == doctest::Approx(0.25));
    CHECK(config->layers[0].meadow == doctest::Approx(1.0));
    const double luminance = (0.2126 * 64 + 0.7152 * 72 + 0.0722 * 24) / 255.0
        / (0.2126 * 0.378 + 0.7152 * 0.4258 + 0.0722 * 0.1895);
    CHECK(config->layers[0].tint[0] == doctest::Approx(std::min(64 / 255.0 / 0.378, luminance)).epsilon(1e-3));
    CHECK(config->layers[0].tint[2] == doctest::Approx(std::min(24 / 255.0 / 0.1895, luminance)).epsilon(1e-3));
    CHECK(config->layers[1].tint == std::array<float, 3>{1.0f, 1.0f, 1.0f});
    CHECK(config->layers[3].tint[0] == doctest::Approx(64 / 255.0 / 0.378 * 0.5).epsilon(1e-3));
    // Steep ground of the grass takes the grass colour over the cliff's mean; the dirt has no colour: none.
    CHECK(config->layers[0].cliffTint[0] == doctest::Approx(64 / 255.0 / 0.5).epsilon(1e-3));
    CHECK(config->layers[1].cliffTint == config->layers[1].tint);

    // The same input gives the same bytes.
    GroundTerrain again;
    REQUIRE(buildGroundTerrain(ground, map, testAssets(), "testmap", GroundOptions{}, again, errorMessage));
    CHECK(again.weightsPng == terrain.weightsPng);
    CHECK(again.materialsText == terrain.materialsText);
}

TEST_CASE("S8b: covered ground faces are drawn as faces; slope off; what the game would refuse is refused")
{
    // The grass floor 512 under a dirt roof over its whole west half: covered, drawn textured, out of the weights.
    Game::IndoorMapData map = twoFloorMap(false);
    Game::IndoorFace roof;

    for (const std::array<int, 3> &corner : std::vector<std::array<int, 3>>{{-2100, -1100, 512}, {100, -1100, 512},
             {100, 1100, 512}, {-2100, 1100, 512}})
    {
        roof.vertexIndices.push_back(uint16_t(map.vertices.size()));
        map.vertices.push_back({corner[0], corner[1], corner[2]});
    }

    roof.textureName = "dirttex";
    map.faces.push_back(roof);
    YAML::Node ground = YAML::Load(
        "layers:\n"
        "  - {material: grass, textures: [grasstex]}\n"
        "  - {material: dirt, textures: [dirttex]}\n"
        "slope: {off: true}\n");
    GroundTerrain terrain;
    std::string errorMessage;
    REQUIRE_MESSAGE(buildGroundTerrain(ground, map, testAssets(), "t", GroundOptions{}, terrain, errorMessage),
        errorMessage);
    CHECK(terrain.excludedFaces == std::vector<uint32_t>{0});
    CHECK(terrain.sceneTerrain["exclude_faces"][0].as<int>() == 0);
    CHECK(terrain.layers == std::vector<std::string>{"grass", "dirt", "grass_patches"});
    CHECK(terrain.materialsText.find("slope:") == std::string::npos);
    CHECK(!terrain.warnings.empty());   // the grass layer has no face left

    ground["covered"] = "terrain";
    REQUIRE(buildGroundTerrain(ground, map, testAssets(), "t", GroundOptions{}, terrain, errorMessage));
    CHECK(terrain.excludedFaces.empty());

    const auto refused = [&map](const std::string &text, const std::string &expected)
    {
        GroundTerrain result;
        std::string message;
        CHECK_FALSE(buildGroundTerrain(YAML::Load(text), map, testAssets(), "t", GroundOptions{}, result, message));
        CHECK_MESSAGE(message.find(expected) != std::string::npos, message);
    };

    refused("layers: [{material: lava, textures: [grasstex]}]", "no such material");
    refused("layers: [{material: grass, textures: [grasstex]}, {material: dirt, textures: [grasstex]}]",
        "in two ground layers");
    refused("layers: [{material: grass, textures: [nothing]}]", "no face");
    refused("layers: [{material: grass, textures: [grasstex], color: [1, 2, 3], tint: [1, 1, 1]}]", "both");
    refused("materials: [{name: odd, library: marble}]\nlayers: [{material: odd, textures: [grasstex]}]",
        "library.yml does not have");
    refused("layers: [{material: grass, textures: [grasstex]}]\nslope: {material: nowhere}", "slope material");
}

TEST_CASE("S8b: an indoor project with ground builds its weights and material file and installs them")
{
    if (!haveMm9Terrain() || !std::filesystem::is_directory(S8bExample))
    {
        return;
    }

    const std::filesystem::path scratch = s8bScratch("meadow");
    std::filesystem::copy(S8bExample, scratch / "project", std::filesystem::copy_options::recursive);
    std::filesystem::remove_all(scratch / "project" / "build");
    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(scratch / "project", project, issues));
    BuildOptions options;
    options.assetRoot = S8bAssets;
    options.outputDirectory = scratch / "build1";
    BuildResult result;
    REQUIRE_MESSAGE(buildProject(project, options, result), (result.issues.empty() ? "" : result.issues[0].message));
    CHECK(std::find(result.files.begin(), result.files.end(), "studio09_blv.yml") != result.files.end());
    CHECK(std::find(result.files.begin(), result.files.end(), "studio09_blv_weights0.png") != result.files.end());
    const YAML::Node scene = YAML::Load(s8bRead(scratch / "build1" / "studio09.scene.yml"));
    CHECK(scene["terrain"]["materials"].as<std::string>() == "studio09_blv.yml");
    CHECK(scene["terrain"]["textures"].size() == 3);
    CHECK(scene["sky"]["mode"].as<std::string>() == "open");

    // Byte-stable: a second build writes the same files.
    options.outputDirectory = scratch / "build2";
    REQUIRE(buildProject(project, options, result));

    for (const char *pFile : {"studio09_blv.yml", "studio09_blv_weights0.png", "studio09.scene.yml", "studio09.blv"})
    {
        CHECK_MESSAGE(s8bRead(scratch / "build1" / pFile) == s8bRead(scratch / "build2" / pFile), pFile);
    }

    // Install into a mount: the pair goes to worlds/mm9/terrain_materials/.
    std::vector<std::string> installed;
    std::string errorMessage;
    REQUIRE_MESSAGE(installBuildIntoMount(project, scratch / "build1", scratch / "mount", S8bAssets, installed,
                        errorMessage), errorMessage);
    CHECK(std::find(installed.begin(), installed.end(), "worlds/mm9/terrain_materials/studio09_blv.yml")
        != installed.end());
    CHECK(s8bRead(scratch / "mount/worlds/mm9/terrain_materials/studio09_blv_weights0.png")
        == s8bRead(scratch / "build1" / "studio09_blv_weights0.png"));

    // Without ground the build makes neither file and install takes the old pair away.
    s8bWrite(scratch / "project" / "atmosphere.yml", "format: 0\nopen_sky: {mode: open}\n");
    Project plain;
    REQUIRE(loadProject(scratch / "project", plain, issues));
    options.outputDirectory = scratch / "build1";
    REQUIRE(buildProject(plain, options, result));
    CHECK_FALSE(std::filesystem::exists(scratch / "build1" / "studio09_blv.yml"));
    CHECK_FALSE(YAML::Load(s8bRead(scratch / "build1" / "studio09.scene.yml"))["terrain"].IsDefined());
    REQUIRE(installBuildIntoMount(plain, scratch / "build1", scratch / "mount", S8bAssets, installed, errorMessage));
    CHECK_FALSE(std::filesystem::exists(scratch / "mount/worlds/mm9/terrain_materials/studio09_blv.yml"));

    // ground beside terrain, and ground in an overlay project, are refused.
    s8bWrite(scratch / "project" / "atmosphere.yml", "format: 0\nterrain: {materials: x.yml, textures: [a]}\n"
        "ground: {layers: [{material: grass, textures: [cgrajnkrow]}]}\n");
    Project both;
    REQUIRE(loadProject(scratch / "project", both, issues));
    CHECK_FALSE(buildProject(both, options, result));
    REQUIRE(!result.issues.empty());
    CHECK(result.issues[0].message.find("terrain and ground") != std::string::npos);
    std::filesystem::remove_all(scratch);
}
