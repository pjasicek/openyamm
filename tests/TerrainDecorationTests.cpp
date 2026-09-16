#include "game/outdoor/TerrainDecorationData.h"
#include "game/outdoor/TerrainDecorationRenderer.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorLightingRuntime.h"
#include "game/app/GameSettings.h"

#include <doctest/doctest.h>

#include <algorithm>
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
    map.bmodels.push_back(house);
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
        CHECK(instance.sizeWindKind[1] <= rule.height * 1.3f);
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
            instance.sizeWindKind == second.instances[i].sizeWindKind;
        taller += instance.sizeWindKind[1] > settings.rules[0].height * 1.3f;
    }
    CHECK(identical);
    CHECK(double(taller) / first.instances.size() > 0.04);
    CHECK(double(taller) / first.instances.size() < 0.12);
    uint32_t smallest = 128;
    uint32_t largest = 0;
    for (const TerrainDecorationPatch &patch : first.patches)
    {
        smallest = std::min(smallest, patch.count);
        largest = std::max(largest, patch.count);
        for (uint32_t i = patch.first; i < patch.first + patch.count; ++i)
        {
            REQUIRE(first.instances[i].positionYaw[2] + first.instances[i].sizeWindKind[1] < patch.max[2]);
        }
    }
    CHECK(smallest < 35);
    CHECK(largest > 80);
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

TEST_CASE("Terrain decoration culling retains visible patches and rejects behind distant and offscreen patches")
{
    TerrainDecorationRenderer renderer;
    TerrainDecorationPatch patch = {};
    patch.min = {480.0f, -20.0f, -20.0f};
    patch.max = {520.0f, 20.0f, 20.0f};
    const auto visible = [&](const bx::Vec3 &camera)
    {
        renderer.setView(camera, {1.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f},
                         {0.0f, 0.0f, 1.0f}, 1.3333f, 1.0472f);
        return renderer.visible(patch);
    };
    CHECK(visible({0.0f, 0.0f, 0.0f}));
    CHECK_FALSE(visible({1000.0f, 0.0f, 0.0f}));
    CHECK_FALSE(visible({-2500.0f, 0.0f, 0.0f}));
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
    write("version: 1\ntuft_texture: tuft.png\ndistance: .nan\nrules: []\n");
    CHECK_FALSE(loadTerrainDecorationConfig(assets, map, error));
    CHECK_FALSE(error.empty());
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
        CHECK(before.instances[i].sizeWindKind == after.instances[i].sizeWindKind);
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
        CHECK(instance.sizeWindKind[2] == doctest::Approx(0.4f));
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
    CHECK(first.patches.size() == original.patches.size());
    std::array<int, 4> counts = {};
    for (size_t i = 0; i < first.instances.size(); ++i)
    {
        const TerrainDecorationInstance &instance = first.instances[i];
        CHECK(instance.positionYaw == original.instances[i].positionYaw);
        CHECK(instance.groundNormal == second.instances[i].groundNormal);
        const size_t layer = size_t(instance.groundNormal[3]);
        REQUIRE(layer < counts.size());
        ++counts[layer];
        CHECK(instance.sizeWindKind[0] <= original.instances[i].sizeWindKind[0]);
    }
    for (size_t i = 0; i < counts.size(); ++i)
    {
        CHECK(float(counts[i]) / first.instances.size() ==
              doctest::Approx(varied.tuftVariants[i].weight / 100.0f).epsilon(0.12));
    }
    for (const TerrainDecorationPatch &patch : first.patches)
    {
        for (uint32_t i = patch.first; i < patch.first + patch.count; ++i)
        {
            CHECK(first.instances[i].positionYaw[2] + first.instances[i].sizeWindKind[1] < patch.max[2]);
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

TEST_CASE("Terrain decoration mixed cells keep each mesh contiguous for draw merging")
{
    OutdoorMapData map = flatMap();
    map.tileMap[64 * 128 + 65] = 1;
    TerrainDecorationConfig settings = config();
    TerrainDecorationRule stones = settings.rules[0];
    stones.stone = true;
    stones.candidates = 10;
    settings.rules.push_back(stones);
    const TerrainDecorationPlacement placement = scatterTerrainDecorations(map, textures(), settings);
    REQUIRE(placement.patches.size() == 4);
    CHECK_FALSE(placement.patches[0].stone);
    CHECK_FALSE(placement.patches[1].stone);
    CHECK(placement.patches[2].stone);
    CHECK(placement.patches[3].stone);
    uint32_t next = 0;
    for (const TerrainDecorationPatch &patch : placement.patches)
    {
        CHECK(patch.first == next);
        for (uint32_t i = patch.first; i < patch.first + patch.count; ++i)
        {
            CHECK((placement.instances[i].sizeWindKind[3] != 0.0f) == patch.stone);
        }
        next += patch.count;
    }
    CHECK(next == placement.instances.size());
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
