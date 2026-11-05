#include "game/outdoor/TerrainDecorationData.h"
#include "game/outdoor/TerrainDecorationRenderer.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorLightingRuntime.h"
#include "game/app/GameSettings.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>

using namespace OpenYAMM::Game;

namespace
{
OutdoorMapData flatMap()
{
    OutdoorMapData map;
    map.heightMap.resize(128 * 128, 0);
    map.tileMap.resize(128 * 128, 0);
    map.tileMap[64 * 128 + 64] = 1;
    return map;
}

std::array<std::string, 256> textures()
{
    std::array<std::string, 256> result;
    result[1] = "test_grass";
    return result;
}

TerrainDecorationConfig config()
{
    TerrainDecorationConfig result;
    TerrainDecorationRule rule;
    rule.texture = "test_grass";
    result.rules.push_back(rule);
    return result;
}

// Every quadtree node's own instance range.
std::vector<TerrainDecorationPatch> ranges(const TerrainDecorationPlacement &placement)
{
    std::vector<TerrainDecorationPatch> result;
    for (const TerrainDecorationNode &node : placement.nodes)
    {
        result.push_back(node.range);
    }
    return result;
}

OutdoorMapData grassField(int first, int last)
{
    OutdoorMapData map = flatMap();
    for (int y = first; y <= last; ++y)
    {
        for (int x = first; x <= last; ++x)
        {
            map.tileMap[y * 128 + x] = 1;
        }
    }
    return map;
}
}

TEST_CASE("Terrain decoration placement is deterministic and follows rendered triangle heights")
{
    OutdoorMapData map = flatMap();
    map.heightMap[65 * 128 + 65] = 2;
    const TerrainDecorationPlacement a = scatterTerrainDecorations(map, textures(), config());
    const TerrainDecorationPlacement b = scatterTerrainDecorations(map, textures(), config());
    REQUIRE_FALSE(a.instances.empty());
    CHECK(a.instances.size() <= 64);
    REQUIRE(a.instances.size() == b.instances.size());
    for (size_t i = 0; i < a.instances.size(); ++i)
    {
        CHECK(a.instances[i].positionYaw == b.instances[i].positionYaw);
        const std::array<float, 4> &p = a.instances[i].positionYaw;
        CHECK(p[0] >= 4.0f);
        CHECK(p[0] <= 512.0f - 4.0f);
        CHECK(p[1] <= 0.0f);
        CHECK(p[1] >= -512.0f);
        CHECK(p[2] == doctest::Approx(sampleOutdoorRenderedTerrainHeight(map, p[0], p[1]) - 3.0f));
    }
}

TEST_CASE("Terrain decoration masks preserve north south orientation and material exclusion")
{
    TerrainDecorationConfig settings = config();
    TerrainDecorationRule &rule = settings.rules[0];
    rule.maskWidth = 8;
    rule.maskHeight = 8;
    rule.coverage.resize(64, 0);
    std::fill(rule.coverage.begin(), rule.coverage.begin() + 32, 255);
    const TerrainDecorationPlacement placement = scatterTerrainDecorations(flatMap(), textures(), settings);
    REQUIRE_FALSE(placement.instances.empty());
    CHECK(placement.instances.size() < 64);
    for (const TerrainDecorationInstance &instance : placement.instances)
    {
        CHECK(instance.positionYaw[1] > -256.0f);
    }
    std::fill(rule.coverage.begin(), rule.coverage.end(), 0);
    CHECK(scatterTerrainDecorations(flatMap(), textures(), settings).instances.empty());
}

TEST_CASE("Larger terrain grass keeps its instance budget and contains sloped card corners in culling bounds")
{
    OutdoorMapData map = flatMap();
    map.heightMap[64 * 128 + 65] = 6;
    map.heightMap[65 * 128 + 65] = 6;
    const size_t originalCount = scatterTerrainDecorations(map, textures(), config()).instances.size();
    REQUIRE(originalCount > 0);
    for (float scale : {2.0f, 3.0f, 5.0f, 6.4f})
    {
        TerrainDecorationConfig settings = config();
        settings.rules[0].width *= scale;
        settings.rules[0].height *= scale;
        const TerrainDecorationPlacement placement = scatterTerrainDecorations(map, textures(), settings);
        REQUIRE(placement.instances.size() == originalCount);
        for (const TerrainDecorationPatch &patch : ranges(placement))
        {
            for (uint32_t index = patch.first; index < patch.first + patch.count; ++index)
            {
                const TerrainDecorationInstance &instance = placement.instances[index];
                const float c = std::cos(instance.positionYaw[3]);
                const float s = std::sin(instance.positionYaw[3]);
                const float halfWidth = instance.sizeWindRank[0] * 0.5f;
                for (const std::array<float, 2> &corner :
                    {std::array<float, 2>{-halfWidth, 0}, {halfWidth, 0}, {0, -halfWidth}, {0, halfWidth}})
                {
                    const float x = c * corner[0] - s * corner[1];
                    const float y = s * corner[0] + c * corner[1];
                    const float z = instance.positionYaw[2]
                        - (x * instance.groundNormal[0] + y * instance.groundNormal[1]) / instance.groundNormal[2];
                    const float wind = instance.sizeWindRank[2];
                    CHECK(instance.positionYaw[0] + x - wind >= patch.min[0]);
                    CHECK(instance.positionYaw[0] + x + wind <= patch.max[0]);
                    CHECK(instance.positionYaw[1] + y - wind >= patch.min[1]);
                    CHECK(instance.positionYaw[1] + y + wind <= patch.max[1]);
                    CHECK(z >= patch.min[2]);
                    CHECK(z + instance.sizeWindRank[1] <= patch.max[2]);
                }
            }
        }
    }
}

TEST_CASE("Terrain decorations exclude buildings steep slopes and absent terrain")
{
    OutdoorMapData map = flatMap();
    OutdoorBModel house;
    house.minX = -20;
    house.maxX = 532;
    house.minY = -532;
    house.maxY = 20;
    house.minZ = 0;
    house.maxZ = 500;
    house.vertices = {{-20, -532, 0}, {532, 20, 500}};
    map.bmodels.push_back(house);
    CHECK(scatterTerrainDecorations(map, textures(), config()).instances.empty());
    map.bmodels.front().minX = 10000;
    map.bmodels.front().maxX = 12000;
    CHECK(scatterTerrainDecorations(map, textures(), config()).instances.empty());
    map.bmodels.clear();
    map.heightMap[64 * 128 + 65] = 100;
    map.heightMap[65 * 128 + 65] = 100;
    CHECK(scatterTerrainDecorations(map, textures(), config()).instances.empty());
    map = flatMap();
    map.noTerrain = true;
    CHECK(scatterTerrainDecorations(map, textures(), config()).instances.empty());
    map = flatMap();
    CHECK(scatterTerrainDecorations(map, {}, config()).instances.empty());
}

TEST_CASE("Terrain decoration short grass tapers into blends while stones and tall clumps stay clear")
{
    TerrainDecorationConfig settings = config();
    TerrainDecorationRule &rule = settings.rules[0];
    rule.maskWidth = 64;
    rule.maskHeight = 64;
    rule.coverage.resize(64 * 64, 255);
    const size_t fullCount = scatterTerrainDecorations(flatMap(), textures(), settings).instances.size();
    std::fill(rule.coverage.begin(), rule.coverage.end(), 192);
    settings.tallGrassChance = 0.25f;
    settings.tallGrassScale = 2.0f;
    const TerrainDecorationPlacement blended = scatterTerrainDecorations(flatMap(), textures(), settings);
    CHECK(blended.instances.size() > fullCount / 4);
    CHECK(blended.instances.size() < fullCount * 3 / 4);
    for (const TerrainDecorationInstance &instance : blended.instances)
    {
        CHECK(instance.sizeWindRank[1] <= rule.height * 1.3f);
    }
    rule.stone = true;
    CHECK(scatterTerrainDecorations(flatMap(), textures(), settings).instances.empty());
    rule.stone = false;
    std::fill(rule.coverage.begin(), rule.coverage.end(), 128);
    CHECK(scatterTerrainDecorations(flatMap(), textures(), settings).instances.empty());
}

TEST_CASE("Terrain decoration patch variation keeps a bounded budget and deterministic taller clumps")
{
    OutdoorMapData map = flatMap();
    for (int y = 40; y < 80; ++y)
    {
        for (int x = 40; x < 80; ++x)
        {
            map.tileMap[y * 128 + x] = 1;
        }
    }
    TerrainDecorationConfig settings = config();
    settings.rules[0].candidates = 60;
    const TerrainDecorationPlacement uniform = scatterTerrainDecorations(map, textures(), settings);
    settings.densityVariation = 0.8f;
    settings.tallGrassChance = 0.08f;
    const TerrainDecorationPlacement first = scatterTerrainDecorations(map, textures(), settings);
    const TerrainDecorationPlacement second = scatterTerrainDecorations(map, textures(), settings);
    CHECK(double(first.instances.size()) / uniform.instances.size() == doctest::Approx(1.0).epsilon(0.06));
    REQUIRE(first.instances.size() == second.instances.size());
    size_t taller = 0;
    bool identical = true;
    for (size_t i = 0; i < first.instances.size(); ++i)
    {
        const TerrainDecorationInstance &instance = first.instances[i];
        identical &= instance.positionYaw == second.instances[i].positionYaw &&
            instance.sizeWindRank == second.instances[i].sizeWindRank;
        taller += instance.sizeWindRank[1] > settings.rules[0].height * 1.3f;
    }
    CHECK(identical);
    CHECK(double(taller) / first.instances.size() > 0.04);
    CHECK(double(taller) / first.instances.size() < 0.12);
    std::vector<uint32_t> cellCounts(128 * 128, 0);
    for (const TerrainDecorationInstance &instance : first.instances)
    {
        const int x = int(std::floor(instance.positionYaw[0] / 512.0f)) + 64;
        const int y = 64 - int(std::ceil(instance.positionYaw[1] / 512.0f));
        ++cellCounts[size_t(y) * 128 + x];
    }
    uint32_t smallest = 128;
    uint32_t largest = 0;
    for (int y = 40; y < 80; ++y)
    {
        for (int x = 40; x < 80; ++x)
        {
            smallest = std::min(smallest, cellCounts[size_t(y) * 128 + x]);
            largest = std::max(largest, cellCounts[size_t(y) * 128 + x]);
        }
    }
    CHECK(smallest < 35);
    CHECK(largest > 80);
    for (const TerrainDecorationPatch &patch : ranges(first))
    {
        for (uint32_t i = patch.first; i < patch.first + patch.count; ++i)
        {
            REQUIRE(first.instances[i].positionYaw[2] + first.instances[i].sizeWindRank[1] < patch.max[2]);
        }
    }
    settings.densityMask.resize(128 * 128, 255);
    CHECK(scatterTerrainDecorations(map, textures(), settings).instances.size() == first.instances.size());
    std::fill(settings.densityMask.begin(), settings.densityMask.end(), 0);
    CHECK(scatterTerrainDecorations(map, textures(), settings).instances.empty());
    std::fill(settings.densityMask.begin(), settings.densityMask.end(), 128);
    CHECK(double(scatterTerrainDecorations(map, textures(), settings).instances.size()) / first.instances.size()
        == doctest::Approx(0.5).epsilon(0.04));
    settings.densityMask.clear();
    settings.rules[0].density = 0.0f;
    CHECK(scatterTerrainDecorations(map, textures(), settings).instances.empty());
}

TEST_CASE("Terrain decoration authored New Sorpigal masks admit grass in every transition direction")
{
    const std::filesystem::path root = std::filesystem::path(__FILE__).parent_path().parent_path();
    OpenYAMM::Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    OutdoorMapData map = flatMap();
    map.worldId = "mm6";
    map.fileName = "oute3.odm";
    std::string error;
    const std::optional<TerrainDecorationConfig> authored = loadTerrainDecorationConfig(assets, map, error);
    REQUIRE_MESSAGE(authored, error);
    int checked = 0;
    for (const TerrainDecorationRule &source : authored->rules)
    {
        if (source.stone || source.coverage.empty())
        {
            continue;
        }
        CAPTURE(source.texture);
        TerrainDecorationConfig settings = config();
        settings.rules[0] = source;
        settings.rules[0].texture = "test_grass";
        settings.rules[0].candidates = 128;
        const TerrainDecorationPlacement placement = scatterTerrainDecorations(map, textures(), settings);
        REQUIRE_FALSE(placement.instances.empty());
        for (const TerrainDecorationInstance &instance : placement.instances)
        {
            const int x = int(instance.positionYaw[0] / 512.0f * source.maskWidth);
            const int y = int(-instance.positionYaw[1] / 512.0f * source.maskHeight);
            CHECK(source.coverage[y * source.maskWidth + x] > 128);
        }
        ++checked;
    }
    CHECK(checked == 12);
    assets.shutdown();
}

TEST_CASE("Terrain decoration setting defaults off and survives saving settings")
{
    CHECK_FALSE(GameSettings{}.terrainDecorations);
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-terrain-decoration-test.ini";
    GameSettings settings;
    settings.terrainDecorations = true;
    std::string error;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE(loaded);
    CHECK(loaded->terrainDecorations);
    settings.terrainDecorations = false;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> disabled = loadGameSettings(path, error);
    REQUIRE(disabled);
    CHECK_FALSE(disabled->terrainDecorations);
    std::filesystem::remove(path);
}

TEST_CASE("Terrain decoration culling retains visible bounds and rejects behind distant and offscreen bounds")
{
    TerrainDecorationRenderer renderer;
    const std::array<float, 3> min = {480.0f, -20.0f, -20.0f};
    const std::array<float, 3> max = {520.0f, 20.0f, 20.0f};
    const auto visible = [&](const bx::Vec3 &camera, float maximumDistance = 4096.0f)
    {
        renderer.setView(camera, {1.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f},
                         {0.0f, 0.0f, 1.0f}, 1.3333f, 1.0472f);
        return renderer.visible(min, max, maximumDistance);
    };
    CHECK(visible({0.0f, 0.0f, 0.0f}));
    CHECK_FALSE(visible({1000.0f, 0.0f, 0.0f}));
    CHECK_FALSE(visible({-5000.0f, 0.0f, 0.0f}));
    CHECK(visible({-3500.0f, 0.0f, 0.0f}));
    CHECK_FALSE(visible({-3500.0f, 0.0f, 0.0f}, 2048.0f));
    CHECK_FALSE(visible({0.0f, 1000.0f, 0.0f}));
    CHECK_FALSE(visible({0.0f, 0.0f, 1000.0f}));
    CHECK(visible({500.0f, 0.0f, 0.0f}));
}

TEST_CASE("Terrain decoration loader opts in per map and rejects malformed config")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "openyamm-terrain-decoration-config";
    const std::filesystem::path directory = root / "assets_dev/worlds/mm6/terrain_decorations";
    std::filesystem::create_directories(directory);
    std::filesystem::create_directories(root / "assets_dev/engine");
    OpenYAMM::Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    OutdoorMapData map;
    map.worldId = "mm6";
    map.fileName = "unconfigured.odm";
    std::string error;
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK(error.empty());
    map.fileName = "example.odm";
    const auto write = [&](const std::string &body)
    {
        std::ofstream stream(directory / "example.yml");
        stream << body;
    };
    write("version: 1\ntuft_texture: tuft.png\nrules:\n"
          "  - {texture: grass, kind: grass, candidates: 32}\n");
    const std::optional<TerrainDecorationConfig> valid = loadTerrainDecorationConfig(assets, map, error);
    REQUIRE(valid);
    CHECK(valid->rules.size() == 1);
    CHECK(error.empty());
    write("version: 1\ntuft_texture: tuft.png\nrules:\n"
          "  - {texture: grass, kind: grass, candidates: 32, width: 200, height: 250}\n");
    const std::optional<TerrainDecorationConfig> enlarged = loadTerrainDecorationConfig(assets, map, error);
    REQUIRE(enlarged);
    CHECK(enlarged->rules[0].width == 200.0f);
    CHECK(enlarged->rules[0].height == 250.0f);
    write("version: 1\ntuft_texture: tuft.png\nrules:\n"
          "  - {texture: grass, kind: grass, candidates: 32, width: 257}\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 1\ntuft_texture: tuft.png\nrules:\n"
          "  - {texture: grass, kind: grass, candidates: 32, height: 257}\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 1\ntuft_texture: tuft.png\ndensity_variation: 0.8\npatch_size: 768\n"
          "tall_grass_chance: 0.08\ntall_grass_scale: 1.8\nrules:\n"
          "  - {texture: grass, kind: grass, candidates: 60, density: 0.5}\n");
    const std::optional<TerrainDecorationConfig> patches = loadTerrainDecorationConfig(assets, map, error);
    REQUIRE(patches);
    CHECK(patches->densityVariation == doctest::Approx(0.8f));
    CHECK(patches->tallGrassChance == doctest::Approx(0.08f));
    CHECK(patches->rules[0].density == doctest::Approx(0.5f));
    write("version: 1\ntuft_texture: tuft.png\ndensity_mask: missing.png\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK_FALSE(error.empty());
    write("version: 1\ntuft_texture: tuft.png\ndensity_variation: 2\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 1\ntuft_texture: tuft.png\ntall_grass_scale: .nan\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 1\ntuft_texture: tuft.png\nnear_distance: .nan\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK_FALSE(error.empty());
    // The fixed radius was replaced by the level of detail; stale files fail instead of being reinterpreted.
    write("version: 1\ntuft_texture: tuft.png\ndistance: 4096\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 1\ntuft_texture: tuft.png\nnear_distance: 3072\nfar_distance: 2048\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 1\ntuft_texture: tuft.png\nnear_distance: 3072\nfar_distance: 20000\nlod_max_scale: 1.5\n"
          "stone_distance: 1500\nfoliage_tint: 0.5\nrules: []\n");
    const std::optional<TerrainDecorationConfig> lod = loadTerrainDecorationConfig(assets, map, error);
    REQUIRE(lod);
    CHECK(lod->lod.nearDistance == doctest::Approx(3072.0f));
    CHECK(lod->lod.farDistance == doctest::Approx(20000.0f));
    CHECK(lod->lod.maxScale == doctest::Approx(1.5f));
    CHECK(lod->stoneDistance == doctest::Approx(1500.0f));
    CHECK(lod->foliageTint == doctest::Approx(0.5f));
    write("version: 1\ntuft_texture: tuft.png\nrules:\n"
          "  - {texture: grass, kind: grass, candidates: 1000000}\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK_FALSE(error.empty());
    write("version: 1\ntuft_texture: tuft.png\nrules:\n"
          "  - {texture: grass, kind: grass, candidates: 32, mask: missing.png}\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK_FALSE(error.empty());
    write("version: 1\ntuft_texture: atlas.png\ntuft_atlas_grid: [2, 2]\ntuft_variants:\n"
          "  - {weight: 45}\n  - {weight: 35}\n  - {weight: 15, height_scale: 1.35}\n"
          "  - {weight: 5, width_scale: 0.85}\nrules: []\n");
    const std::optional<TerrainDecorationConfig> variants = loadTerrainDecorationConfig(assets, map, error);
    REQUIRE(variants);
    CHECK(variants->tuftVariants.size() == 4);
    CHECK(variants->tuftVariants[2].heightScale == doctest::Approx(1.35f));
    write("version: 1\ntuft_texture: atlas.png\ntuft_atlas_grid: [2, 2]\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK_FALSE(error.empty());
    write("version: 1\ntuft_texture: atlas.png\ntuft_variants: [{weight: 0}]\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK_FALSE(error.empty());
    {
        std::ofstream stream(directory / "families.yml");
        stream << "version: 2\ntuft_texture: plants.png\ntuft_atlas_grid: [4, 3]\nfamilies:\n"
               << "  reed:\n    kind: grass\n    candidates: 18\n    width: 24\n    height: 100\n"
               << "    full_footprint: true\n    wind_strength: 0.8\n"
               << "    variants: [{layer: 4, weight: 60}, {layer: 5, weight: 40}]\n";
    }
    write("version: 2\nfamilies_file: families.yml\nrules:\n"
          "  - {texture: marsh, family: reed, density: 0.6}\n");
    const std::optional<TerrainDecorationConfig> familyConfig = loadTerrainDecorationConfig(assets, map, error);
    REQUIRE(familyConfig);
    REQUIRE(familyConfig->rules.size() == 1);
    const TerrainDecorationRule &reed = familyConfig->rules[0];
    CHECK(reed.family == "reed");
    CHECK(reed.fullFootprint);
    CHECK(reed.height == doctest::Approx(100.0f));
    CHECK(reed.candidates == 18);
    CHECK(reed.density == doctest::Approx(0.6f));
    CHECK(reed.windStrength == doctest::Approx(0.8f));
    REQUIRE(reed.variants.size() == 2);
    CHECK(reed.variants[1].layer == 5);
    write("version: 2\nfamilies_file: families.yml\nrules: [{texture: marsh, family: missing}]\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK_FALSE(error.empty());
    write("version: 2\nfamilies_file: families.yml\nrules:\n"
          "  - {texture: marsh, family: reed, variants: [{layer: 12}]}\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 2\nfamilies_file: families.yml\nrules:\n"
          "  - {texture: marsh, family: reed, wind_strength: -1}\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 2\nfamilies_file: missing.yml\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 2\nfamilies_file: ../families.yml\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    write("version: 2\nenabled: false\nreason: underwater\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK(error.empty());
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("Terrain decoration family variants preserve legacy placement and select only their own layers")
{
    TerrainDecorationConfig legacy = config();
    legacy.tuftVariants = {{45, 1, 1}, {35, 1, 0.9f}, {15, 1, 1.35f}, {5, 0.85f, 0.85f}};
    TerrainDecorationConfig migrated = legacy;
    migrated.rules[0].variants = legacy.tuftVariants;
    for (size_t i = 0; i < migrated.rules[0].variants.size(); ++i)
    {
        migrated.rules[0].variants[i].layer = int(i);
    }
    const TerrainDecorationPlacement before = scatterTerrainDecorations(flatMap(), textures(), legacy);
    const TerrainDecorationPlacement after = scatterTerrainDecorations(flatMap(), textures(), migrated);
    REQUIRE_FALSE(before.instances.empty());
    REQUIRE(before.instances.size() == after.instances.size());
    for (size_t i = 0; i < before.instances.size(); ++i)
    {
        CHECK(before.instances[i].positionYaw == after.instances[i].positionYaw);
        CHECK(before.instances[i].sizeWindRank == after.instances[i].sizeWindRank);
        CHECK(before.instances[i].color == after.instances[i].color);
        CHECK(before.instances[i].groundNormal == after.instances[i].groundNormal);
    }
    migrated.rules[0].variants = {{1, 1, 1, 7}};
    migrated.rules[0].windStrength = 0.4f;
    const TerrainDecorationPlacement selected = scatterTerrainDecorations(flatMap(), textures(), migrated);
    REQUIRE(selected.instances.size() == before.instances.size());
    for (const TerrainDecorationInstance &instance : selected.instances)
    {
        CHECK(instance.groundNormal[3] == 7.0f);
        CHECK(instance.sizeWindRank[2] == doctest::Approx(0.4f));
    }
}

TEST_CASE("Terrain decoration strict plants keep their full footprint out of internal water channels")
{
    TerrainDecorationConfig settings = config();
    TerrainDecorationRule &rule = settings.rules[0];
    rule.candidates = 128;
    rule.width = 80;
    rule.maskWidth = rule.maskHeight = 64;
    rule.coverage.assign(64 * 64, 255);
    for (int y = 0; y < 64; ++y)
    {
        for (int x = 29; x <= 34; ++x)
        {
            rule.coverage[y * 64 + x] = 0;
        }
    }
    const TerrainDecorationPlacement roots = scatterTerrainDecorations(flatMap(), textures(), settings);
    rule.fullFootprint = true;
    const TerrainDecorationPlacement strict = scatterTerrainDecorations(flatMap(), textures(), settings);
    REQUIRE_FALSE(strict.instances.empty());
    CHECK(strict.instances.size() < roots.instances.size());
    for (const TerrainDecorationInstance &instance : strict.instances)
    {
        const float cellX = instance.positionYaw[0] - outdoorGridCornerWorldX(64);
        CHECK((cellX + 80.0f * 0.65f < 29 * 8.0f || cellX - 80.0f * 0.65f > 35 * 8.0f));
    }
}

TEST_CASE("Terrain decoration variants preserve placements and batches while weighting shapes")
{
    OutdoorMapData map = flatMap();
    for (int y = 58; y <= 68; ++y)
    {
        for (int x = 58; x <= 68; ++x)
        {
            map.tileMap[y * 128 + x] = 1;
        }
    }
    const TerrainDecorationPlacement original = scatterTerrainDecorations(map, textures(), config());
    TerrainDecorationConfig varied = config();
    varied.tuftAtlasGrid = {2, 2};
    varied.tuftVariants = {{45, 1.0f, 1.0f}, {35, 1.0f, 0.9f}, {15, 1.0f, 1.35f}, {5, 0.85f, 0.85f}};
    const TerrainDecorationPlacement first = scatterTerrainDecorations(map, textures(), varied);
    const TerrainDecorationPlacement second = scatterTerrainDecorations(map, textures(), varied);
    REQUIRE(first.instances.size() == original.instances.size());
    REQUIRE(first.instances.size() == second.instances.size());
    CHECK(first.nodes.size() == original.nodes.size());
    std::array<int, 4> counts = {};
    for (size_t i = 0; i < first.instances.size(); ++i)
    {
        const TerrainDecorationInstance &instance = first.instances[i];
        CHECK(instance.positionYaw == original.instances[i].positionYaw);
        CHECK(instance.groundNormal == second.instances[i].groundNormal);
        const size_t layer = size_t(instance.groundNormal[3]);
        REQUIRE(layer < counts.size());
        ++counts[layer];
        CHECK(instance.sizeWindRank[0] <= original.instances[i].sizeWindRank[0]);
    }
    for (size_t i = 0; i < counts.size(); ++i)
    {
        CHECK(float(counts[i]) / first.instances.size() ==
              doctest::Approx(varied.tuftVariants[i].weight / 100.0f).epsilon(0.12));
    }
    for (const TerrainDecorationPatch &patch : ranges(first))
    {
        for (uint32_t i = patch.first; i < patch.first + patch.count; ++i)
        {
            CHECK(first.instances[i].positionYaw[2] + first.instances[i].sizeWindRank[1] < patch.max[2]);
        }
    }
}

TEST_CASE("Terrain decoration batching preserves visible ranges mesh kinds and exact light uniforms")
{
    const TerrainDecorationPatch batch = {.first = 20, .count = 10};
    TerrainDecorationPatch next = {.first = 30, .count = 8};
    const OutdoorSelectedFxLights lights = {};
    OutdoorSelectedFxLights nextLights = lights;
    CHECK(TerrainDecorationRenderer::canMerge(batch, lights, next, nextLights));
    next.first = 31; // A culled instance range must not be included to bridge the gap.
    CHECK_FALSE(TerrainDecorationRenderer::canMerge(batch, lights, next, nextLights));
    next.first = 29; // Overlap would double-draw instances.
    CHECK_FALSE(TerrainDecorationRenderer::canMerge(batch, lights, next, nextLights));
    next.first = 30;
    next.stone = true;
    CHECK_FALSE(TerrainDecorationRenderer::canMerge(batch, lights, next, nextLights));
    next.stone = false;
    next.count = 0;
    CHECK_FALSE(TerrainDecorationRenderer::canMerge(batch, lights, next, nextLights));
    next.count = 8;
    CHECK_FALSE(TerrainDecorationRenderer::canMerge({}, lights, next, nextLights));
    nextLights.positions[3] = 300.0f;
    CHECK_FALSE(TerrainDecorationRenderer::canMerge(batch, lights, next, nextLights));
    nextLights = lights;
    nextLights.colors[0] = 0.5f;
    CHECK_FALSE(TerrainDecorationRenderer::canMerge(batch, lights, next, nextLights));
    nextLights = lights;
    nextLights.params[0] = 1.0f;
    CHECK_FALSE(TerrainDecorationRenderer::canMerge(batch, lights, next, nextLights));
    nextLights = lights;
    nextLights.filteredEmitterCount = 4; // Diagnostic counts do not change the actual lighting.
    CHECK(TerrainDecorationRenderer::canMerge(batch, lights, next, nextLights));
}

TEST_CASE("Terrain decoration mixed cells keep each mesh kind in its own tree")
{
    OutdoorMapData map = flatMap();
    map.tileMap[64 * 128 + 65] = 1;
    TerrainDecorationConfig settings = config();
    TerrainDecorationRule stones = settings.rules[0];
    stones.stone = true;
    stones.candidates = 10;
    settings.rules.push_back(stones);
    const TerrainDecorationPlacement placement = scatterTerrainDecorations(map, textures(), settings);
    REQUIRE(placement.roots.size() == 2);
    CHECK_FALSE(placement.nodes[placement.roots[0]].range.stone);
    CHECK(placement.nodes[placement.roots[1]].range.stone);
    uint32_t next = 0;
    size_t stoneInstances = 0;
    for (const TerrainDecorationNode &node : placement.nodes)
    {
        CHECK(node.range.first == next);
        CHECK(node.range.stone == placement.nodes[placement.roots[node.range.stone ? 1 : 0]].range.stone);
        for (uint32_t i = node.range.first; i < node.range.first + node.range.count; ++i)
        {
            // Stones have no wind.
            CHECK((placement.instances[i].sizeWindRank[2] == 0.0f) == node.range.stone);
            stoneInstances += node.range.stone;
        }
        next += node.range.count;
    }
    CHECK(next == placement.instances.size());
    CHECK(stoneInstances > 0);
}

TEST_CASE("Terrain decoration level of detail keeps a constant count per screen area and the coverage")
{
    const TerrainDecorationLod lod = {2048.0f, 16384.0f, 2.0f};
    CHECK(terrainDecorationKeep(lod, 0.0f) == doctest::Approx(1.0f));
    CHECK(terrainDecorationKeep(lod, 2048.0f) == doctest::Approx(1.0f));
    CHECK(terrainDecorationKeep(lod, 4096.0f) == doctest::Approx(0.25f));
    CHECK(terrainDecorationKeep(lod, 8192.0f) == doctest::Approx(0.0625f));
    CHECK(terrainDecorationKeep(lod, 16384.0f) == doctest::Approx(0.0f));
    CHECK(terrainDecorationKeep(lod, 20000.0f) == doctest::Approx(0.0f));
    // The end fade starts at 85 % of the range.
    CHECK(terrainDecorationKeep(lod, 13926.0f) == doctest::Approx(2048.0f * 2048.0f / (13926.0f * 13926.0f)));
    CHECK(terrainDecorationKeep(lod, 15000.0f) < 2048.0f * 2048.0f / (15000.0f * 15000.0f));
    float previous = 2.0f;
    for (float distance = 0.0f; distance <= 17000.0f; distance += 250.0f)
    {
        const float keep = terrainDecorationKeep(lod, distance);
        CHECK(keep <= previous);
        previous = keep;
        const float scale = terrainDecorationScale(lod, distance);
        CHECK(scale >= 1.0f);
        CHECK(scale <= lod.maxScale);
        if (distance <= lod.nearDistance * lod.maxScale)
        {
            // Thinned but grown: the coverage holds until the largest scale.
            CHECK(keep * scale * scale == doctest::Approx(1.0f).epsilon(0.001));
        }
        else if (distance < lod.farDistance * 0.85f)
        {
            CHECK(keep * scale * scale < 1.0f);
        }
    }
}

TEST_CASE("Terrain decoration rank quadtree nests the thinning bands depth first")
{
    const OutdoorMapData map = grassField(20, 100);
    TerrainDecorationConfig settings = config();
    const TerrainDecorationPlacement placement = scatterTerrainDecorations(map, textures(), settings);
    REQUIRE(placement.roots.size() == 1);
    REQUIRE(placement.instances.size() > 50000);
    const TerrainDecorationNode &root = placement.nodes[placement.roots[0]];
    CHECK(root.rankBegin == 0.0f);
    uint32_t next = 0;
    size_t leaves = 0;
    const auto inside = [](const std::array<float, 3> &min, const std::array<float, 3> &max,
                           const std::array<float, 3> &outerMin, const std::array<float, 3> &outerMax)
    {
        for (size_t axis = 0; axis < 3; ++axis)
        {
            if (min[axis] < outerMin[axis] || max[axis] > outerMax[axis])
            {
                return false;
            }
        }
        return true;
    };
    const auto visit = [&](const auto &self, uint32_t index) -> void
    {
        const TerrainDecorationNode &node = placement.nodes[index];
        // Depth first: a node's instances directly precede its first child's.
        CHECK(node.range.first == next);
        next += node.range.count;
        float previous = -1.0f;
        for (uint32_t i = node.range.first; i < node.range.first + node.range.count; ++i)
        {
            const TerrainDecorationInstance &instance = placement.instances[i];
            const float rank = instance.sizeWindRank[3];
            CHECK(rank >= previous);
            CHECK(rank >= node.rankBegin);
            CHECK(rank < node.rankEnd);
            previous = rank;
            CHECK(instance.positionYaw[0] - instance.sizeWindRank[0] * 0.5f * 2.82f >= node.range.min[0]);
            CHECK(instance.positionYaw[0] + instance.sizeWindRank[0] * 0.5f * 2.82f <= node.range.max[0]);
            CHECK(instance.positionYaw[2] + instance.sizeWindRank[1] * 1.41f <= node.range.max[2]);
        }
        if (node.range.count > 0)
        {
            CHECK(inside(node.range.min, node.range.max, node.regionMin, node.regionMax));
        }
        leaves += node.rankEnd == 1.0f;
        for (uint32_t child = 0; child < node.childCount; ++child)
        {
            const TerrainDecorationNode &childNode = placement.nodes[node.children[child]];
            CHECK(childNode.rankBegin == doctest::Approx(node.rankEnd));
            CHECK(inside(childNode.regionMin, childNode.regionMax, node.regionMin, node.regionMax));
            self(self, node.children[child]);
        }
    };
    visit(visit, placement.roots[0]);
    CHECK(next == placement.instances.size());
    // 81 cells of 512 cover 41472 units: 21 x 21 leaves of 2048 at most, some partly.
    CHECK(leaves >= 20 * 20);
    CHECK(leaves <= 22 * 22);
    // About three quarters of the instances are in the leaves' band.
    size_t leafInstances = 0;
    for (const TerrainDecorationNode &node : placement.nodes)
    {
        leafInstances += node.rankEnd == 1.0f ? node.range.count : 0;
    }
    CHECK(double(leafInstances) / placement.instances.size() == doctest::Approx(0.75).epsilon(0.02));
}

TEST_CASE("Terrain decoration draws thin with distance and grow only logarithmically with the range")
{
    const OutdoorMapData map = grassField(0, 126);
    TerrainDecorationConfig settings = config();
    settings.rules[0].candidates = 16;
    const TerrainDecorationPlacement placement = scatterTerrainDecorations(map, textures(), settings);
    const std::vector<TerrainDecorationInstance> instances = placement.instances;
    TerrainDecorationRenderer renderer;
    const auto drawn = [&](const TerrainDecorationLod &lod, const bx::Vec3 &camera, const bx::Vec3 &forward,
                           size_t *pDraws = nullptr)
    {
        TerrainDecorationConfig lodSettings = settings;
        lodSettings.lod = lod;
        renderer.setPlacement(lodSettings, placement);
        const bx::Vec3 right = bx::normalize(bx::cross(forward, {0.0f, 0.0f, 1.0f}));
        renderer.setView(camera, forward, right, bx::cross(right, forward), 1.7778f, 1.0472f);
        std::vector<TerrainDecorationPatch> draws;
        renderer.collectDraws(draws);
        size_t total = 0;
        uint32_t end = 0;
        size_t merged = 0;
        for (const TerrainDecorationPatch &draw : draws)
        {
            // Ascending, never overlapping; every drawn instance is within the per-instance share somewhere.
            CHECK(draw.first >= end);
            merged += draw.first != end;
            end = draw.first + draw.count;
            total += draw.count;
        }
        if (pDraws != nullptr)
        {
            *pDraws = merged;
        }
        return total;
    };
    const bx::Vec3 camera = {0.0f, 0.0f, 180.0f};
    const bx::Vec3 forward = {1.0f, 0.0f, 0.0f};
    // Every instance in view within the full density distance is drawn.
    size_t nearInView = 0;
    for (const TerrainDecorationInstance &instance : instances)
    {
        const float dx = instance.positionYaw[0] - camera.x;
        const float dy = instance.positionYaw[1] - camera.y;
        nearInView += dx > 64.0f && std::abs(dy) < dx * 0.5f && std::hypot(dx, dy) < 2048.0f;
    }
    const size_t base = drawn({2048.0f, 4096.0f, 2.0f}, camera, forward);
    CHECK(base >= nearInView);
    // Doubling the range twice costs a bounded share more, not four times the instances each time.
    size_t draws = 0;
    const size_t medium = drawn({2048.0f, 8192.0f, 2.0f}, camera, forward);
    const size_t far = drawn({2048.0f, 16384.0f, 2.0f}, camera, forward, &draws);
    CHECK(medium > base);
    CHECK(far > medium);
    CHECK(double(far) < double(base) * 3.0);
    // Contiguous full nodes merge into few separate ranges.
    CHECK(draws < 40);
    // Flying high, the grass below thins instead of vanishing.
    const size_t high = drawn({2048.0f, 16384.0f, 2.0f}, {0.0f, 0.0f, 4000.0f}, bx::normalize({1.0f, 0.0f, -0.6f}));
    CHECK(high > 0);
    CHECK(high < far);
}

TEST_CASE("Terrain decoration foliage map holds the tufts' colour and depth")
{
    const OutdoorMapData map = grassField(40, 80);
    TerrainDecorationConfig settings = config();
    settings.rules[0].tint = {0.5f, 1.0f, 0.25f};
    TerrainDecorationRule stones = settings.rules[0];
    stones.stone = true;
    settings.rules.push_back(stones);
    const TerrainDecorationPlacement placement = scatterTerrainDecorations(map, textures(), settings);
    const std::vector<TerrainFoliageLayer> layers = {{{0.4f, 0.6f, 0.8f}, 0.5f}};
    const std::vector<float> foliage = buildTerrainFoliageMap(placement, layers);
    REQUIRE(foliage.size() == size_t(TerrainFoliageMapSize) * TerrainFoliageMapSize * 4);
    // Expected depth inside the field: grass instances' card area per ground area.
    double area = 0.0;
    size_t grass = 0;
    for (const TerrainDecorationNode &node : placement.nodes)
    {
        for (uint32_t i = node.range.first; !node.range.stone && i < node.range.first + node.range.count; ++i)
        {
            area += placement.instances[i].sizeWindRank[0] * placement.instances[i].sizeWindRank[1] * 0.5;
            ++grass;
        }
    }
    REQUIRE(grass > 0);
    const double fieldArea = 41.0 * 41.0 * 512.0 * 512.0;
    const auto texel = [&](float x, float y)
    {
        const int u = int((x + 32768.0f) / (65536.0f / float(TerrainFoliageMapSize)));
        const int v = int((32768.0f - y) / (65536.0f / float(TerrainFoliageMapSize)));
        return &foliage[(size_t(v) * TerrainFoliageMapSize + u) * 4];
    };
    // The field spans cells 40..80: world x -12288..8704, y 12288..-8704.
    const float *pInside = texel(-2000.0f, 2000.0f);
    CHECK(pInside[3] == doctest::Approx(area / fieldArea).epsilon(0.25));
    const float *pOutside = texel(-20000.0f, 20000.0f);
    CHECK(pOutside[3] == 0.0f);
    // Premultiplied: the colour is the layer average times the tint (the shade varies by +-7 %).
    CHECK(pInside[0] / pInside[3] == doctest::Approx(0.4f * 0.5f * 0.975f).epsilon(0.08));
    CHECK(pInside[1] / pInside[3] == doctest::Approx(0.6f * 1.0f * 0.975f).epsilon(0.08));
    CHECK(pInside[2] / pInside[3] == doctest::Approx(0.8f * 0.25f * 0.975f).epsilon(0.08));

    // Encoded: straight colour and depth / range at the top level, then every mip level down to 1 x 1.
    const std::vector<uint8_t> encoded = encodeTerrainFoliageMap(foliage);
    size_t expected = 0;
    for (int size = TerrainFoliageMapSize; size >= 1; size /= 2)
    {
        expected += size_t(size) * size * 4;
    }
    REQUIRE(encoded.size() == expected);
    const size_t inside = size_t(pInside - foliage.data());
    CHECK(encoded[inside] == std::lround(pInside[0] / pInside[3] * 255.0f));
    CHECK(encoded[inside + 3] == std::lround(pInside[3] / TerrainFoliageDepthRange * 255.0f));
    // The last level is the whole map's average: some grass, the colour of the tufts.
    const uint8_t *pLast = &encoded[encoded.size() - 4];
    CHECK(pLast[3] > 0);
    CHECK(pLast[1] == doctest::Approx(0.6f * 0.975f * 255.0f).epsilon(0.1));
}

TEST_CASE("Terrain decoration view cache invalidates on motion projection and shutdown")
{
    TerrainDecorationRenderer renderer;
    const bx::Vec3 camera = {0.0f, 0.0f, 0.0f};
    const bx::Vec3 forward = {1.0f, 0.0f, 0.0f};
    const bx::Vec3 right = {0.0f, 1.0f, 0.0f};
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    CHECK(renderer.setView(camera, forward, right, up, 1.3333f, 1.0472f));
    CHECK_FALSE(renderer.setView(camera, forward, right, up, 1.3333f, 1.0472f));
    CHECK(renderer.setView({0.1f, 0.0f, 0.0f}, forward, right, up, 1.3333f, 1.0472f));
    CHECK(renderer.setView(camera, right, forward, up, 1.3333f, 1.0472f));
    CHECK(renderer.setView(camera, forward, right, up, 1.3333f, 1.0472f));
    CHECK(renderer.setView(camera, forward, right, up, 1.7778f, 1.0472f));
    CHECK(renderer.setView(camera, forward, right, up, 1.7778f, 0.9f));
    CHECK_FALSE(renderer.setView(camera, forward, right, up, 1.7778f, 0.9f));
    renderer.shutdown(false);
    CHECK(renderer.setView(camera, forward, right, up, 1.7778f, 0.9f));
}

TEST_CASE("Terrain decoration cutout encloses the tuft and trims transparent card area")
{
    // A tuft-like fan: a narrow base widening toward the top, inside a 64 x 48 cell.
    constexpr int Width = 64;
    constexpr int Height = 48;
    std::vector<uint8_t> alpha(size_t(Width) * Height, 0);
    for (int y = 4; y < Height - 2; ++y)
    {
        const float spread = 0.5f + 26.0f * float(Height - 2 - y) / float(Height);
        for (int x = 0; x < Width; ++x)
        {
            if (std::abs(float(x) + 0.5f - Width * 0.5f) < spread)
            {
                alpha[size_t(y) * Width + x] = 200;
            }
        }
    }
    const auto cutout = terrainDecorationCutout(alpha, Width, Height, 26);
    const auto inside = [&](float u, float v)
    {
        bool positive = false;
        bool negative = false;
        for (size_t index = 0; index < cutout.size(); ++index)
        {
            const auto &a = cutout[index];
            const auto &b = cutout[(index + 1) % cutout.size()];
            const float cross = (b[0] - a[0]) * (v - a[1]) - (b[1] - a[1]) * (u - a[0]);
            positive = positive || cross > 1.0e-6f;
            negative = negative || cross < -1.0e-6f;
        }
        return !(positive && negative);
    };
    float area = 0.0f;
    for (size_t index = 0; index < cutout.size(); ++index)
    {
        const auto &a = cutout[index];
        const auto &b = cutout[(index + 1) % cutout.size()];
        area += a[0] * b[1] - b[0] * a[1];
        CHECK(a[0] >= 0.0f);
        CHECK(a[0] <= 1.0f);
        CHECK(a[1] >= 0.0f);
        CHECK(a[1] <= 1.0f);
    }
    area = std::abs(area) * 0.5f;
    for (int y = 0; y < Height; ++y)
    {
        for (int x = 0; x < Width; ++x)
        {
            if (alpha[size_t(y) * Width + x] >= 26)
            {
                CHECK(inside((float(x) + 0.5f) / Width, (float(y) + 0.5f) / Height));
            }
        }
    }
    CHECK(area < 0.75f);
    // Nothing covered: the full card.
    const auto empty = terrainDecorationCutout(std::vector<uint8_t>(size_t(Width) * Height, 0), Width, Height, 26);
    CHECK(empty[0][0] == 0.0f);
    CHECK(empty[2][0] == 1.0f);
    CHECK(empty[2][1] == 1.0f);
}

TEST_CASE("Smoothed terrain passes through native vertices and stays near the native triangles")
{
    OutdoorMapData map = flatMap();
    // A rolling hill plus a cliff: the cliff is where unbounded bicubic smoothing would overshoot.
    for (int y = 0; y < 128; ++y)
    {
        for (int x = 0; x < 128; ++x)
        {
            const float hill = 20.0f + 18.0f * std::sin(float(x) * 0.4f) * std::cos(float(y) * 0.3f);
            map.heightMap[size_t(y * 128 + x)] = uint8_t(x >= 70 && x < 74 ? 120.0f : hill);
        }
    }
    float largestDeviation = 0.0f;
    bool smoothedSomewhere = false;
    for (int y = 2; y < 125; ++y)
    {
        for (int x = 2; x < 125; ++x)
        {
            const float vertex = float(map.heightMap[size_t(y * 128 + x)] * OutdoorMapData::TerrainHeightScale);
            CHECK(outdoorSmoothedTerrainHeight(map, float(x), float(y), 1.0f) == doctest::Approx(vertex).epsilon(0.001));
            for (float fraction : {0.25f, 0.5f, 0.75f})
            {
                const float gridX = float(x) + fraction;
                const float gridY = float(y) + 1.0f - fraction;
                const float native = outdoorNativeTerrainHeight(map, gridX, gridY);
                const float smoothed = outdoorSmoothedTerrainHeight(map, gridX, gridY, 1.0f);
                largestDeviation = std::max(largestDeviation, std::abs(smoothed - native));
                smoothedSomewhere = smoothedSomewhere || std::abs(smoothed - native) > 1.0f;
                CHECK(outdoorSmoothedTerrainHeight(map, gridX, gridY, 0.0f) == doctest::Approx(native));
            }
        }
    }
    CHECK(smoothedSomewhere);
    CHECK(largestDeviation <= 32.0f);
    // The native triangles match the rendered classic terrain everywhere.
    CHECK(outdoorNativeTerrainHeight(map, 40.3f, 50.6f)
        == doctest::Approx(sampleOutdoorRenderedTerrainHeight(map, outdoorGridCornerWorldX(40) + 0.3f * 512.0f,
            outdoorGridCornerWorldY(50) - 0.6f * 512.0f)).epsilon(0.001));
}

TEST_CASE("Rendered terrain stays under a pool cut into a hillside terrace")
{
    // Every row climbs west to east onto a flat terrace (grid columns 64-65) that the smoothed surface bulges over.
    OutdoorMapData map = flatMap();
    for (int y = 0; y < 128; ++y)
    {
        for (int x = 0; x < 128; ++x)
        {
            map.heightMap[size_t(y * 128 + x)] = uint8_t(x <= 63 ? 10 : x <= 65 ? 21 : 22);
        }
    }
    OutdoorBModel pool;
    pool.vertices = {{26, -486, 684}, {486, -486, 684}, {486, -26, 684}, {26, -26, 684}};
    OutdoorBModelFace water;
    water.planeNormalZ = 65536;
    water.vertexIndices = {0, 1, 2, 3};
    pool.faces.push_back(water);
    map.bmodels.push_back(pool);

    constexpr int Steps = 4;
    constexpr int Side = 127 * Steps + 1;
    std::vector<float> heights(size_t(Side) * Side);
    for (int j = 0; j < Side; ++j)
    {
        for (int i = 0; i < Side; ++i)
        {
            heights[size_t(j) * Side + i] =
                outdoorSmoothedTerrainHeight(map, float(i) / Steps, float(j) / Steps, 1.0f);
        }
    }
    const std::vector<float> smoothed = heights;
    capRenderedTerrainUnderBModels(map, heights, Side, Steps);

    float highestSmoothed = 0.0f;
    for (int j = 64 * Steps + 1; j < 65 * Steps; ++j)
    {
        for (int i = 64 * Steps + 1; i < 65 * Steps; ++i)
        {
            const float native = outdoorNativeTerrainHeight(map, float(i) / Steps, float(j) / Steps);
            highestSmoothed = std::max(highestSmoothed, smoothed[size_t(j) * Side + i]);
            CHECK(heights[size_t(j) * Side + i] <= 680.0f);
            CHECK(heights[size_t(j) * Side + i] >= native);
        }
    }
    CHECK(highestSmoothed > 684.0f);
    // Away from the face the smoothed surface is untouched.
    CHECK(heights[size_t(64 * Steps) * Side + 70 * Steps + 1] == smoothed[size_t(64 * Steps) * Side + 70 * Steps + 1]);
    CHECK(heights[size_t(70 * Steps) * Side + 64 * Steps + 2] == smoothed[size_t(70 * Steps) * Side + 64 * Steps + 2]);
}

TEST_CASE("Terrain grass on a surface follows its density and skips steep triangles")
{
    // Two triangles making a flat 4096 x 4096 square, and a vertical one (a cliff).
    const std::vector<TerrainDecorationSurfaceTriangle> flat = {
        {{{{0.0f, 0.0f, 100.0f}, {4096.0f, 0.0f, 100.0f}, {4096.0f, 4096.0f, 100.0f}}}, {0.0f, 0.0f, 1.0f}},
        {{{{0.0f, 0.0f, 100.0f}, {4096.0f, 4096.0f, 100.0f}, {0.0f, 4096.0f, 100.0f}}}, {0.0f, 0.0f, 1.0f}}};
    const TerrainDecorationConfig grass = config();
    const auto none = [](float, float) { return 0.0f; };
    const auto full = [](float, float) { return 1.0f; };
    const auto half = [](float x, float) { return x < 2048.0f ? 1.0f : 0.0f; };

    CHECK(scatterTerrainDecorationsOnSurface(flat, none, grass).instances.empty());
    const TerrainDecorationPlacement everywhere = scatterTerrainDecorationsOnSurface(flat, full, grass);
    // An outdoor rule's candidates are per 512 x 512 cell: 64 cells here.
    const double expected = 64.0 * double(grass.rules.front().candidates) * grass.rules.front().density;
    CHECK(double(everywhere.instances.size()) > expected * 0.9);
    CHECK(double(everywhere.instances.size()) < expected * 1.1);
    for (const TerrainDecorationInstance &instance : everywhere.instances)
    {
        CHECK(instance.positionYaw[2] == doctest::Approx(97.0f));
    }
    // Deterministic, and only where the density allows.
    CHECK(scatterTerrainDecorationsOnSurface(flat, full, grass).instances.size() == everywhere.instances.size());
    for (const TerrainDecorationInstance &instance : scatterTerrainDecorationsOnSurface(flat, half, grass).instances)
    {
        CHECK(instance.positionYaw[0] < 2048.0f);
    }
    const std::vector<TerrainDecorationSurfaceTriangle> cliff = {
        {{{{0.0f, 0.0f, 0.0f}, {4096.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 4096.0f}}}, {0.0f, -1.0f, 0.0f}}};
    CHECK(scatterTerrainDecorationsOnSurface(cliff, full, grass).instances.empty());
}
