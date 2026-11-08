#include "game/outdoor/TerrainDecorationData.h"

#include "engine/ImageAssetLoader.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMeadow.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <limits>
#include <cmath>
#include <filesystem>
#include <optional>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
uint32_t hash(uint32_t value)
{
    value ^= value >> 16;
    value *= 0x7feb352du;
    value ^= value >> 15;
    value *= 0x846ca68bu;
    return value ^ (value >> 16);
}

float randomUnit(uint32_t &state)
{
    state = hash(state + 0x9e3779b9u);
    return float(state >> 8) / 16777216.0f;
}

float boundedFloat(const YAML::Node &node, const char *pName, float fallback, float min, float max)
{
    const float value = node[pName] ? node[pName].as<float>() : fallback;
    if (!std::isfinite(value) || value < min || value > max)
    {
        throw std::runtime_error(std::string("invalid terrain decoration ") + pName);
    }
    return value;
}

// Atlas-layer variants of a family, flowers or undergrowth (version 2 libraries).
std::vector<TerrainDecorationVariant> layerVariants(const YAML::Node &node, int layerCount, float maxHeightScale)
{
    if (!node.IsSequence() || node.size() == 0 || node.size() > 16)
    {
        throw std::runtime_error("expected 1..16 atlas variants");
    }
    std::vector<TerrainDecorationVariant> variants;
    for (const YAML::Node &variantNode : node)
    {
        TerrainDecorationVariant variant;
        variant.layer = variantNode["layer"].as<int>();
        if (variant.layer < 0 || variant.layer >= layerCount)
        {
            throw std::runtime_error("plant variant layer outside atlas");
        }
        variant.weight = boundedFloat(variantNode, "weight", 1.0f, 0.01f, 100.0f);
        // Width cannot exceed the rule's footprint used by material/building exclusions.
        variant.widthScale = boundedFloat(variantNode, "width_scale", 1.0f, 0.25f, 1.0f);
        variant.heightScale = boundedFloat(variantNode, "height_scale", 1.0f, 0.25f, maxHeightScale);
        variants.push_back(variant);
    }
    return variants;
}

std::array<float, 3> boundedColor(const YAML::Node &node, const char *pName)
{
    const std::array<float, 3> color = node[pName].as<std::array<float, 3>>();
    for (float value : color)
    {
        if (!std::isfinite(value) || value < 0.0f || value > 2.0f)
        {
            throw std::runtime_error(std::string("invalid terrain decoration ") + pName);
        }
    }
    return color;
}

bool blocked(const OutdoorMapData &map, const std::vector<std::array<bx::Vec3, 2>> &modelBounds,
    float x, float y, float z, float radius, float entityRadius = 80.0f)
{
    for (const std::array<bx::Vec3, 2> &bounds : modelBounds)
    {
        if (x >= bounds[0].x - radius && x <= bounds[1].x + radius &&
            y >= bounds[0].y - radius && y <= bounds[1].y + radius &&
            z <= bounds[1].z + 48.0f && z + 96.0f >= bounds[0].z)
        {
            return true;
        }
    }
    for (const OutdoorEntity &entity : map.entities)
    {
        const float dx = x - entity.x;
        const float dy = y - entity.y;
        if (dx * dx + dy * dy < entityRadius * entityRadius && std::abs(z - entity.z) < 128.0f)
        {
            return true;
        }
    }
    return false;
}

float smoothUnit(float value)
{
    value = std::clamp(value, 0.0f, 1.0f);
    return value * value * (3.0f - 2.0f * value);
}

float patchNoise(float x, float y, uint32_t seed)
{
    const int ix = int(std::floor(x));
    const int iy = int(std::floor(y));
    const auto sample = [&](int dx, int dy)
    {
        return float(hash(seed ^ hash(uint32_t(ix + dx)) ^ hash(uint32_t(iy + dy) + 0x517cc1b7u)) >> 8)
            / 16777216.0f;
    };
    const float u = smoothUnit(x - ix);
    const float v = smoothUnit(y - iy);
    return std::lerp(std::lerp(sample(0, 0), sample(1, 0), u),
                     std::lerp(sample(0, 1), sample(1, 1), u), v);
}

// Index of the variant at choice in [0, 1) of the variants' total weight.
size_t chooseVariant(const std::vector<TerrainDecorationVariant> &variants, float choice)
{
    float total = 0.0f;
    for (const TerrainDecorationVariant &variant : variants)
    {
        total += variant.weight;
    }
    choice *= total;
    size_t index = 0;
    while (index + 1 < variants.size() && choice >= variants[index].weight)
    {
        choice -= variants[index].weight;
        ++index;
    }
    return index;
}

std::array<float, 4> tinted(const std::array<float, 3> &tint, float shade, const std::array<float, 3> &meadow)
{
    return {tint[0] * shade * meadow[0], tint[1] * shade * meadow[1], tint[2] * shade * meadow[2], 1.0f};
}

float cellDensity(const TerrainDecorationConfig &config, float x, float y)
{
    if (config.densityMask.empty())
    {
        return 1.0f;
    }
    // Pixel centres correspond to terrain cell centres; interpolate across shared cell edges.
    x = std::clamp(x - 0.5f, 0.0f, 127.0f);
    y = std::clamp(y - 0.5f, 0.0f, 127.0f);
    const int ix = int(x);
    const int iy = int(y);
    const int nx = std::min(ix + 1, 127);
    const int ny = std::min(iy + 1, 127);
    return std::lerp(std::lerp(float(config.densityMask[iy * 128 + ix]),
                               float(config.densityMask[iy * 128 + nx]), x - ix),
                     std::lerp(float(config.densityMask[ny * 128 + ix]),
                               float(config.densityMask[ny * 128 + nx]), x - ix), y - iy) / 255.0f;
}

float materialCoverage(const TerrainDecorationRule &rule, float u, float v, bool fullFootprint = false)
{
    if (rule.coverage.empty())
    {
        return 1.0f;
    }
    // Short blades may overhang the blend; their roots must still be on grass. Stones and tall
    // clumps retain full-width clearance. A soft acceptance probability thins the grassy edge.
    const bool strict = rule.stone || rule.fullFootprint || fullFootprint;
    const float radiusWorld = strict ? rule.width * 0.65f : 4.0f;
    const int radius = std::max(1, int(std::ceil(radiusWorld * rule.maskWidth / 512.0f)));
    const int x = int(u * rule.maskWidth);
    const int y = int(v * rule.maskHeight);
    uint8_t minimum = 255;
    for (int dy = -radius; dy <= radius; ++dy)
    {
        for (int dx = -radius; dx <= radius; ++dx)
        {
            const int mx = std::clamp(x + dx, 0, rule.maskWidth - 1);
            const int my = std::clamp(y + dy, 0, rule.maskHeight - 1);
            minimum = std::min(minimum, rule.coverage[my * rule.maskWidth + mx]);
        }
    }
    return strict ? (minimum >= 240 ? 1.0f : 0.0f) : smoothUnit((float(minimum) - 128.0f) / 112.0f);
}

// The mapped area: grid corner 0 to 128 in both directions.
constexpr float MapMinimum = -float(OutdoorMapData::TerrainTileSize * 64);
constexpr float MapSize = float(OutdoorMapData::TerrainTileSize * 128);

void includeBounds(std::array<float, 3> &min, std::array<float, 3> &max, const std::array<float, 3> &otherMin,
    const std::array<float, 3> &otherMax)
{
    for (size_t axis = 0; axis < 3; ++axis)
    {
        min[axis] = std::min(min[axis], otherMin[axis]);
        max[axis] = std::max(max[axis], otherMax[axis]);
    }
}

// What an instance can cover at its largest LOD scale (vs_terrain_decoration): the card's half width (stones:
// the mesh radius, clumps: plus their lean) plus the wind sway, tilted with the ground.
void includeInstance(std::array<float, 3> &min, std::array<float, 3> &max, const TerrainDecorationInstance &instance,
    float maxScale, float clumpLean)
{
    // A clump's cards lean outward by up to clumpLean of the instance height (and start a little off its centre).
    const float reach = (instance.sizeWindRank[0] * 0.5f + instance.sizeWindRank[1] * clumpLean)
        * std::pow(maxScale, 1.5f);
    const float slope = reach * std::hypot(instance.groundNormal[0], instance.groundNormal[1])
        / std::max(instance.groundNormal[2], 0.5f);
    const float x = instance.positionYaw[0];
    const float y = instance.positionYaw[1];
    const float z = instance.positionYaw[2];
    const float sway = reach + instance.sizeWindRank[2];
    includeBounds(min, max, {x - sway, y - sway, z - slope - 8.0f},
        {x + sway, y + sway, z + instance.sizeWindRank[1] * std::sqrt(maxScale) + slope + 8.0f});
}

// Stores one mesh kind's instances as a rank quadtree (TerrainDecorationNode), depth first, children in the order
// (x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1).
void buildRankTree(const std::vector<TerrainDecorationInstance> &placed, bool stone, bool clump, float maxScale,
    float clumpLean, TerrainDecorationPlacement &result)
{
    if (placed.empty())
    {
        return;
    }
    int leaves = 1;
    int depth = 0;
    while (float(leaves) * TerrainDecorationLeafSize < MapSize)
    {
        leaves *= 2;
        ++depth;
    }
    // buckets[level][cell]: the instances whose rank falls in that level's band.
    std::vector<std::vector<std::vector<uint32_t>>> buckets(size_t(depth) + 1);
    for (int level = 0; level <= depth; ++level)
    {
        const int side = leaves >> level;
        buckets[size_t(level)].resize(size_t(side) * side);
    }
    for (uint32_t index = 0; index < placed.size(); ++index)
    {
        const TerrainDecorationInstance &instance = placed[index];
        const int leafX = std::clamp(int((instance.positionYaw[0] - MapMinimum) / TerrainDecorationLeafSize),
            0, leaves - 1);
        const int leafY = std::clamp(int((instance.positionYaw[1] - MapMinimum) / TerrainDecorationLeafSize),
            0, leaves - 1);
        int level = 0;
        float bandBegin = 0.25f;
        while (level < depth && instance.sizeWindRank[3] < bandBegin)
        {
            ++level;
            bandBegin *= 0.25f;
        }
        const int side = leaves >> level;
        buckets[size_t(level)][size_t(leafY >> level) * side + (leafX >> level)].push_back(index);
    }
    const auto build = [&](const auto &self, int level, int cellX, int cellY) -> uint32_t
    {
        const uint32_t nodeIndex = uint32_t(result.nodes.size());
        result.nodes.push_back({});
        std::vector<uint32_t> &own = buckets[size_t(level)][size_t(cellY) * (leaves >> level) + cellX];
        std::sort(own.begin(), own.end(), [&placed](uint32_t a, uint32_t b)
        {
            return placed[a].sizeWindRank[3] < placed[b].sizeWindRank[3];
        });
        TerrainDecorationNode node;
        node.range.first = uint32_t(result.instances.size());
        node.range.count = uint32_t(own.size());
        node.range.stone = stone;
        node.range.clump = clump;
        node.range.min = {1.0e9f, 1.0e9f, 1.0e9f};
        node.range.max = {-1.0e9f, -1.0e9f, -1.0e9f};
        node.rankEnd = std::pow(0.25f, float(level));
        node.rankBegin = level == depth ? 0.0f : node.rankEnd * 0.25f;
        for (uint32_t index : own)
        {
            result.instances.push_back(placed[index]);
            includeInstance(node.range.min, node.range.max, placed[index], maxScale, clumpLean);
        }
        node.regionMin = node.range.min;
        node.regionMax = node.range.max;
        if (level > 0)
        {
            for (int child = 0; child < 4; ++child)
            {
                const uint32_t childIndex = self(self, level - 1, cellX * 2 + child % 2, cellY * 2 + child / 2);
                if (childIndex != UINT32_MAX)
                {
                    node.children[node.childCount++] = childIndex;
                    includeBounds(node.regionMin, node.regionMax, result.nodes[childIndex].regionMin,
                        result.nodes[childIndex].regionMax);
                }
            }
        }
        if (node.range.count == 0 && node.childCount == 0)
        {
            result.nodes.pop_back();
            return UINT32_MAX;
        }
        result.nodes[nodeIndex] = node;
        return nodeIndex;
    };
    const uint32_t root = build(build, depth, 0, 0);
    if (root != UINT32_MAX)
    {
        result.roots.push_back(root);
    }
}
}

std::optional<TerrainDecorationConfig> loadTerrainDecorationConfig(
    const Engine::AssetFileSystem &assets, const OutdoorMapData &map, std::string &error)
{
    return loadTerrainDecorationConfigFile(assets,
        "worlds/" + map.worldId + "/terrain_decorations/" + std::filesystem::path(map.fileName).stem().string()
            + ".yml",
        error);
}

std::optional<TerrainDecorationConfig> loadTerrainDecorationConfigFile(
    const Engine::AssetFileSystem &assets, const std::string &path, std::string &error)
{
    error.clear();
    // Its masks are beside it; its family file too, or at a virtual path (another world's library, as an open-air
    // BLV's region file names New Sorpigal's), with the tuft atlas beside the family file.
    const std::string directory = path.substr(0, path.find_last_of('/') + 1);
    std::string libraryDirectory = directory;
    const std::optional<std::string> text = assets.readTextFile(path);
    if (!text)
    {
        return std::nullopt;
    }
    try
    {
        const YAML::Node root = YAML::Load(*text);
        const int version = root["version"].as<int>();
        if (version != 1 && version != 2)
        {
            throw std::runtime_error("expected terrain decoration version 1 or 2");
        }
        if (version == 2 && !root["enabled"].as<bool>(true))
        {
            return std::nullopt;
        }
        if (!root["rules"].IsSequence() || root["rules"].size() > 256)
        {
            throw std::runtime_error("expected at most 256 terrain decoration rules");
        }
        YAML::Node library = root;
        if (version == 2)
        {
            const std::string file = root["families_file"].as<std::string>();
            const bool local = std::filesystem::path(file).filename().string() == file;
            if (file.empty() || file.find("..") != std::string::npos || file.front() == '/'
                || (!local && file.rfind("worlds/", 0) != 0 && file.rfind("engine/", 0) != 0))
            {
                throw std::runtime_error("families_file must be a local filename or a worlds/ or engine/ path");
            }
            const std::string familyPath = local ? directory + file : file;
            libraryDirectory = familyPath.substr(0, familyPath.find_last_of('/') + 1);
            const std::optional<std::string> familyText = assets.readTextFile(familyPath);
            if (!familyText)
            {
                throw std::runtime_error("missing terrain decoration family file: " + file);
            }
            library.reset(YAML::Load(*familyText));
            if (library["version"].as<int>() != 2 || !library["families"].IsMap())
            {
                throw std::runtime_error("invalid terrain decoration family library");
            }
        }
        TerrainDecorationConfig config;
        config.seed = root["seed"].as<uint32_t>(1);
        if (root["distance"])
        {
            throw std::runtime_error("distance was replaced by near_distance and far_distance (GRASS_LOD.md)");
        }
        config.lod.nearDistance = boundedFloat(root, "near_distance", config.lod.nearDistance, 256.0f, 16384.0f);
        config.lod.farDistance = boundedFloat(root, "far_distance", config.lod.farDistance,
            config.lod.nearDistance, 65536.0f);
        config.lod.maxScale = boundedFloat(root, "lod_max_scale", config.lod.maxScale, 1.0f, 4.0f);
        config.stoneDistance = boundedFloat(root, "stone_distance", config.stoneDistance, 256.0f, 16384.0f);
        config.foliageTint = boundedFloat(root, "foliage_tint", config.foliageTint, 0.0f, 1.0f);
        config.minimumNormalZ = boundedFloat(root, "minimum_normal_z", 0.85f, 0.5f, 1.0f);
        config.densityVariation = boundedFloat(root, "density_variation", 0.0f, 0.0f, 1.0f);
        config.patchSize = boundedFloat(root, "patch_size", 768.0f, 128.0f, 8192.0f);
        config.tallGrassChance = boundedFloat(root, "tall_grass_chance", 0.0f, 0.0f, 0.25f);
        config.tallGrassScale = boundedFloat(root, "tall_grass_scale", 1.8f, 1.0f, 2.0f);
        config.tuftTexture = libraryDirectory + library["tuft_texture"].as<std::string>();
        if (library["tuft_atlas_grid"])
        {
            config.tuftAtlasGrid = library["tuft_atlas_grid"].as<std::array<int, 2>>();
        }
        if (config.tuftAtlasGrid[0] < 1 || config.tuftAtlasGrid[0] > 4 ||
            config.tuftAtlasGrid[1] < 1 || config.tuftAtlasGrid[1] > 4)
        {
            throw std::runtime_error("tuft atlas grid dimensions must be 1..4");
        }
        if (root["tuft_variants"])
        {
            if (!root["tuft_variants"].IsSequence() || root["tuft_variants"].size() > 16)
            {
                throw std::runtime_error("tuft_variants must be a sequence of at most 16 variants");
            }
            config.tuftVariants.clear();
            for (const YAML::Node &variantNode : root["tuft_variants"])
            {
                TerrainDecorationVariant variant;
                variant.weight = boundedFloat(variantNode, "weight", 1.0f, 0.01f, 100.0f);
                // Width cannot exceed the rule's footprint used by material/building exclusions.
                variant.widthScale = boundedFloat(variantNode, "width_scale", 1.0f, 0.25f, 1.0f);
                variant.heightScale = boundedFloat(variantNode, "height_scale", 1.0f, 0.25f, 1.5f);
                config.tuftVariants.push_back(variant);
            }
        }
        const int layerCount = config.tuftAtlasGrid[0] * config.tuftAtlasGrid[1];
        if (version == 1 && config.tuftVariants.size() != size_t(layerCount))
        {
            throw std::runtime_error("tuft variant count must equal atlas cell count");
        }
        // Library-wide plant behaviour; a map file may replace any of these blocks.
        const auto block = [&](const char *pName)
        {
            return root[pName] ? root[pName] : library[pName];
        };
        if (const YAML::Node meadow = block("meadow"))
        {
            config.meadow.dryTint = boundedColor(meadow, "dry_tint");
            config.meadow.lushTint = boundedColor(meadow, "lush_tint");
            config.meadow.density = boundedFloat(meadow, "density", 0.0f, 0.0f, 0.9f);
            config.meadow.height = boundedFloat(meadow, "height", 0.0f, 0.0f, 0.9f);
        }
        if (const YAML::Node flowers = block("flowers"))
        {
            config.flowers.coverage = boundedFloat(flowers, "coverage", 0.0f, 0.0f, 1.0f);
            config.flowers.clusterSize = boundedFloat(flowers, "cluster_size", 900.0f, 64.0f, 16384.0f);
            config.flowers.chance = boundedFloat(flowers, "chance", 0.0f, 0.0f, 1.0f);
            if (flowers["tint"])
            {
                config.flowers.tint = boundedColor(flowers, "tint");
            }
            config.flowers.variants = layerVariants(flowers["variants"], layerCount, 1.5f);
        }
        if (const YAML::Node verges = block("verges"))
        {
            config.verges.distance = boundedFloat(verges, "distance", 0.0f, 0.0f, 1024.0f);
            config.verges.tallChance = boundedFloat(verges, "tall_chance", 0.0f, 0.0f, 1.0f);
        }
        if (const YAML::Node overhead = block("overhead_fade"))
        {
            for (const YAML::Node &layer : overhead["layers"])
            {
                const int index = layer.as<int>();
                if (index < 0 || index >= layerCount)
                {
                    throw std::runtime_error("overhead_fade layer outside the tuft atlas");
                }
                config.overhead.layerMask |= 1u << index;
            }
            config.overhead.start = boundedFloat(overhead, "start", 250.0f, 0.0f, 4096.0f);
            config.overhead.end = boundedFloat(overhead, "end", 600.0f, config.overhead.start + 1.0f, 8192.0f);
            config.overhead.ground = boundedFloat(overhead, "ground", 0.0f, 0.0f, 1.0f);
        }
        if (const YAML::Node shade = block("ground_shade"))
        {
            config.groundShade = std::clamp(shade.as<float>(), 0.0f, 0.8f);
        }
        if (const YAML::Node clump = block("clump"))
        {
            for (const YAML::Node &layer : clump["layers"])
            {
                const int index = layer.as<int>();
                if (index < 0 || index >= layerCount)
                {
                    throw std::runtime_error("clump layer outside the tuft atlas");
                }
                config.clump.layerMask |= 1u << index;
            }
            config.clump.cards = std::clamp(clump["cards"].as<int>(5), 2, TerrainDecorationMaxClumpCards);
            config.clump.leanDegrees = boundedFloat(clump, "lean", 25.0f, 0.0f, 60.0f);
            config.clump.cardScale = boundedFloat(clump, "card_scale", 0.75f, 0.25f, 1.0f);
            config.clump.distance = boundedFloat(clump, "distance", 1500.0f, 64.0f, 65536.0f);
        }
        if (const YAML::Node bushes = block("bushes"))
        {
            TerrainDecorationBushes &result = config.bushes;
            for (const YAML::Node &model : bushes["models"])
            {
                result.models.push_back({model["model"].as<std::string>(),
                    boundedFloat(model, "height", 120.0f, 16.0f, 1024.0f), boundedFloat(model, "weight", 1.0f, 0.01f, 100.0f)});
            }
            if (result.models.size() > 16)
            {
                throw std::runtime_error("at most 16 bush models");
            }
            result.heightJitter = boundedFloat(bushes, "height_jitter", 0.2f, 0.0f, 0.5f);
            result.spacing = boundedFloat(bushes, "spacing", 640.0f, 128.0f, 8192.0f);
            result.meadowChance = boundedFloat(bushes, "meadow_chance", 0.02f, 0.0f, 1.0f);
            result.lushChance = boundedFloat(bushes, "lush_chance", 0.3f, 0.0f, 1.0f);
            result.lushBelow = boundedFloat(bushes, "lush_below", -0.3f, -1.0f, 1.0f);
            result.vergeChance = boundedFloat(bushes, "verge_chance", 0.35f, 0.0f, 1.0f);
            result.vergeDistance = boundedFloat(bushes, "verge_distance", 260.0f, 0.0f, 2048.0f);
            result.edgeChance = boundedFloat(bushes, "edge_chance", 0.4f, 0.0f, 1.0f);
            if (bushes["edge_radius"])
            {
                result.edgeRadius = bushes["edge_radius"].as<std::array<float, 2>>();
            }
            result.groupMax = std::clamp(bushes["group_max"].as<int>(3), 1, 8);
            result.groupSpread = boundedFloat(bushes, "group_spread", 150.0f, 0.0f, 1024.0f);
            result.radius = boundedFloat(bushes, "radius", 90.0f, 8.0f, 512.0f);
            result.clearance = boundedFloat(bushes, "clearance", 60.0f, 0.0f, 1024.0f);
            result.minimumNormalZ = boundedFloat(bushes, "minimum_normal_z", 0.8f, 0.5f, 1.0f);
            result.maxCount = std::clamp(bushes["max_count"].as<int>(600), 0, 4096);
            if (bushes["fade_distance"])
            {
                result.fadeDistance = bushes["fade_distance"].as<std::array<float, 2>>();
            }
            if (result.edgeRadius[0] < 0.0f || result.edgeRadius[1] < result.edgeRadius[0]
                || result.fadeDistance[0] <= 0.0f || result.fadeDistance[1] <= result.fadeDistance[0])
            {
                throw std::runtime_error("bush edge_radius and fade_distance must be increasing ranges");
            }
        }
        if (const YAML::Node undergrowth = block("undergrowth"))
        {
            config.undergrowth.decorations = undergrowth["decorations"].as<std::vector<std::string>>();
            config.undergrowth.innerRadius = boundedFloat(undergrowth, "inner_radius", 90.0f, 0.0f, 1024.0f);
            config.undergrowth.outerRadius = boundedFloat(undergrowth, "outer_radius", 260.0f,
                config.undergrowth.innerRadius, 2048.0f);
            config.undergrowth.candidates = undergrowth["candidates"].as<int>(0);
            if (config.undergrowth.candidates < 0 || config.undergrowth.candidates > 64)
            {
                throw std::runtime_error("undergrowth candidates must be 0..64");
            }
            config.undergrowth.variants = layerVariants(undergrowth["variants"], layerCount, 2.5f);
        }
        Engine::BinaryAssetCache cache;
        if (root["density_mask"])
        {
            const std::string maskPath = directory + root["density_mask"].as<std::string>();
            const std::optional<Engine::ImagePixelsBgra> mask =
                Engine::loadImageAssetPixelsBgra(assets, maskPath, cache);
            if (!mask || mask->width != 128 || mask->height != 128)
            {
                throw std::runtime_error("terrain density mask must be 128x128: " + maskPath);
            }
            for (size_t i = 0; i < mask->pixels.size(); i += 4)
            {
                config.densityMask.push_back(mask->pixels[i + 2]);
            }
        }
        for (const YAML::Node &mapRule : root["rules"])
        {
            TerrainDecorationRule rule;
            YAML::Node node = YAML::Clone(mapRule);
            if (version == 2)
            {
                rule.family = mapRule["family"].as<std::string>();
                const YAML::Node definition = library["families"][rule.family];
                if (!definition.IsMap())
                {
                    throw std::runtime_error("unknown terrain decoration family: " + rule.family);
                }
                node.reset(YAML::Clone(definition));
                for (const auto &entry : mapRule)
                {
                    node[entry.first.as<std::string>()] = YAML::Clone(entry.second);
                }
            }
            rule.texture = node["texture"].as<std::string>();
            const std::string kind = node["kind"].as<std::string>();
            if (kind != "grass" && kind != "stone")
            {
                throw std::runtime_error("terrain decoration kind must be grass or stone");
            }
            rule.stone = kind == "stone";
            rule.candidates = node["candidates"].as<int>();
            if (rule.texture.empty() || rule.candidates < 1 || rule.candidates > 128)
            {
                throw std::runtime_error("terrain decoration requires a texture and 1..128 candidates per cell");
            }
            rule.width = boundedFloat(node, "width", 40.0f, 2.0f, 256.0f);
            rule.density = boundedFloat(node, "density", 1.0f, 0.0f, 2.0f);
            rule.height = boundedFloat(node, "height", 28.0f, 2.0f, 256.0f);
            rule.fullFootprint = node["full_footprint"].as<bool>(false);
            rule.windStrength = boundedFloat(node, "wind_strength", 2.5f, 0.0f, 4.0f);
            if (version == 2 && !rule.stone)
            {
                rule.variants = layerVariants(node["variants"], layerCount, 1.5f);
                if (node["tall_variants"])
                {
                    rule.tallVariants = layerVariants(node["tall_variants"], layerCount, 2.5f);
                }
                rule.flowers = node["flowers"].as<bool>(false);
            }
            if (node["tint"])
            {
                rule.tint = node["tint"].as<std::array<float, 3>>();
                for (float value : rule.tint)
                {
                    if (!std::isfinite(value) || value < 0.0f || value > 2.0f)
                    {
                        throw std::runtime_error("invalid terrain decoration tint");
                    }
                }
            }
            if (node["mask"])
            {
                const std::string maskPath = directory + node["mask"].as<std::string>();
                const std::optional<Engine::ImagePixelsBgra> mask =
                    Engine::loadImageAssetPixelsBgra(assets, maskPath, cache);
                if (!mask || mask->width < 1 || mask->height < 1 || mask->width > 128 || mask->height > 128)
                {
                    throw std::runtime_error("invalid terrain decoration coverage mask: " + maskPath);
                }
                rule.maskWidth = mask->width;
                rule.maskHeight = mask->height;
                rule.coverage.reserve(mask->width * mask->height);
                const bool invert = node["invert_mask"].as<bool>(false);
                for (size_t i = 0; i < mask->pixels.size(); i += 4)
                {
                    // bimg expands grayscale PNGs from R8: intensity is in red, while blue/green
                    // remain zero. Red also holds intensity for ordinary RGB grayscale masks.
                    const uint8_t intensity = mask->pixels[i + 2];
                    rule.coverage.push_back(invert ? 255 - intensity : intensity);
                }
            }
            config.rules.push_back(std::move(rule));
        }
        return config;
    }
    catch (const std::exception &exception)
    {
        error = path + ": " + exception.what();
        return std::nullopt;
    }
}

namespace
{
bool undergrowthDecoration(const TerrainDecorationUndergrowth &undergrowth, const std::string &name)
{
    std::string lower = name;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c)
    {
        return char(std::tolower(c));
    });
    return std::any_of(undergrowth.decorations.begin(), undergrowth.decorations.end(),
        [&lower](const std::string &part)
        {
            return lower.find(part) != std::string::npos;
        });
}

// The ground queries of the undergrowth and the bushes, from an outdoor map's tiles or an open-air BLV's surface.
struct PlantGround
{
    // Whether grass grows at the point; around: at the point and at six points radius away.
    std::function<bool(float x, float y)> grassGrows;
    std::function<bool(float x, float y, float radius)> grassAround;
    std::function<float(float x, float y)> height;
    std::function<bx::Vec3(float x, float y)> normal;
    // Whether a building, wall or decoration stands near the point (radius; entityRadius for decorations).
    std::function<bool(float x, float y, float z, float radius, float entityRadius)> blocked;
    std::function<float(float x, float y)> moisture;
    // The grass rule growing at the point with its full footprint; nullptr where none does.
    std::function<const TerrainDecorationRule *(float x, float y)> undergrowthRule;
};

// Ferns and uncut grass in a ring around each matching decoration (a tree trunk), on the grass that grows there.
void placeUndergrowth(const TerrainDecorationConfig &config,
    const std::vector<TerrainDecorationSurfaceEntity> &entities, const PlantGround &ground,
    std::vector<TerrainDecorationInstance> &placed)
{
    const TerrainDecorationUndergrowth &undergrowth = config.undergrowth;
    if (undergrowth.candidates == 0 || undergrowth.variants.empty())
    {
        return;
    }
    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const TerrainDecorationSurfaceEntity &entity = entities[entityIndex];
        if (!undergrowthDecoration(undergrowth, entity.name))
        {
            continue;
        }
        uint32_t state = hash(config.seed ^ hash(uint32_t(entityIndex) + 0x632be5abu));
        for (int candidate = 0; candidate < undergrowth.candidates; ++candidate)
        {
            const float angle = randomUnit(state) * 6.2831853f;
            // Uniform over the ring's area.
            const float inner = undergrowth.innerRadius * undergrowth.innerRadius;
            const float outer = undergrowth.outerRadius * undergrowth.outerRadius;
            const float radius = std::sqrt(inner + (outer - inner) * randomUnit(state));
            const float px = entity.position[0] + std::cos(angle) * radius;
            const float py = entity.position[1] + std::sin(angle) * radius;
            const float scale = 0.75f + 0.5f * randomUnit(state);
            const float yaw = randomUnit(state) * 6.2831853f;
            const float shade = 0.9f + 0.15f * randomUnit(state);
            const float choice = randomUnit(state);
            const float rank = randomUnit(state);
            const TerrainDecorationRule *pRule = ground.undergrowthRule(px, py);
            if (pRule == nullptr)
            {
                continue;
            }
            const float z = ground.height(px, py);
            const bx::Vec3 normal = ground.normal(px, py);
            // Clear of buildings; the trunk itself is inside the inner radius.
            if (normal.z < config.minimumNormalZ
                || ground.blocked(px, py, z, pRule->width * 0.5f + 32.0f, undergrowth.innerRadius * 0.9f))
            {
                continue;
            }
            const TerrainDecorationVariant &variant = undergrowth.variants[chooseVariant(undergrowth.variants, choice)];
            const float moisture = ground.moisture(px, py);
            placed.push_back({{px, py, z - 3.0f, yaw},
                {pRule->width * scale * variant.widthScale,
                 pRule->height * scale * variant.heightScale * (1.0f - moisture * config.meadow.height),
                 pRule->windStrength, rank},
                tinted(pRule->tint, shade,
                    outdoorMeadowTint(moisture, config.meadow.dryTint, config.meadow.lushTint)),
                {normal.x, normal.y, normal.z, float(variant.layer)}});
        }
    }
}

// Bush groups (TerrainDecorationBushes): tree lines first, then a jittered grid over the open ground, lush hollows and
// verges, until maxCount.
void placeBushes(const TerrainDecorationConfig &config, const std::vector<TerrainDecorationSurfaceEntity> &entities,
    const PlantGround &ground, std::vector<TerrainBushInstance> &placed)
{
    const TerrainDecorationBushes &bushes = config.bushes;
    if (bushes.models.empty() || bushes.maxCount == 0)
    {
        return;
    }
    std::vector<TerrainDecorationVariant> weights;
    for (const TerrainDecorationBushModel &model : bushes.models)
    {
        TerrainDecorationVariant weight;
        weight.weight = model.weight;
        weights.push_back(weight);
    }
    const auto tryBush = [&](float px, float py, uint32_t &state)
    {
        if (placed.size() >= size_t(bushes.maxCount) || !ground.grassAround(px, py, bushes.radius))
        {
            return;
        }
        for (const TerrainBushInstance &other : placed)
        {
            const float dx = other.position[0] - px;
            const float dy = other.position[1] - py;
            if (dx * dx + dy * dy < bushes.radius * bushes.radius * 2.56f)
            {
                return;
            }
        }
        const float z = ground.height(px, py);
        if (ground.normal(px, py).z < bushes.minimumNormalZ
            || ground.blocked(px, py, z, bushes.radius + bushes.clearance, bushes.radius + bushes.clearance))
        {
            return;
        }
        const float yaw = randomUnit(state) * 6.2831853f;
        const float heightScale = 1.0f + bushes.heightJitter * (2.0f * randomUnit(state) - 1.0f);
        placed.push_back({{px, py, z - 4.0f}, yaw, heightScale, uint32_t(chooseVariant(weights, randomUnit(state)))});
    };
    const auto group = [&](float px, float py, uint32_t &state)
    {
        const int members = 1 + std::min(int(randomUnit(state) * float(bushes.groupMax)), bushes.groupMax - 1);
        for (int member = 0; member < members; ++member)
        {
            const float angle = randomUnit(state) * 6.2831853f;
            const float distance = member == 0 ? 0.0f : bushes.groupSpread * (0.6f + 0.6f * randomUnit(state));
            tryBush(px + std::cos(angle) * distance, py + std::sin(angle) * distance, state);
        }
    };
    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const TerrainDecorationSurfaceEntity &entity = entities[entityIndex];
        uint32_t state = hash(config.seed ^ hash(uint32_t(entityIndex) + 0x1b873593u));
        if (!undergrowthDecoration(config.undergrowth, entity.name) || randomUnit(state) >= bushes.edgeChance)
        {
            continue;
        }
        const float angle = randomUnit(state) * 6.2831853f;
        const float distance = bushes.edgeRadius[0] + (bushes.edgeRadius[1] - bushes.edgeRadius[0]) * randomUnit(state);
        group(entity.position[0] + std::cos(angle) * distance, entity.position[1] + std::sin(angle) * distance, state);
    }
    const int steps = int(std::ceil(MapSize / bushes.spacing));
    for (int row = 0; row < steps; ++row)
    {
        for (int column = 0; column < steps; ++column)
        {
            uint32_t state = hash(config.seed ^ hash(uint32_t(row * steps + column) + 0x2f6b0e7du));
            const float px = MapMinimum + (float(column) + randomUnit(state)) * bushes.spacing;
            const float py = MapMinimum + (float(row) + randomUnit(state)) * bushes.spacing;
            if (!ground.grassGrows(px, py))
            {
                continue;
            }
            const float moisture = ground.moisture(px, py);
            float chance = bushes.meadowChance;
            if (moisture < bushes.lushBelow)
            {
                chance = std::max(chance, bushes.lushChance * smoothUnit((bushes.lushBelow - moisture) / 0.3f));
            }
            if (bushes.vergeChance > 0.0f && ground.blocked(px, py, ground.height(px, py),
                    bushes.radius + bushes.clearance + bushes.vergeDistance, 0.0f))
            {
                chance = std::max(chance, bushes.vergeChance);
            }
            if (randomUnit(state) < chance)
            {
                group(px, py, state);
            }
        }
    }
}
}

TerrainDecorationPlacement scatterTerrainDecorations(const OutdoorMapData &map,
    const std::array<std::string, 256> &textures, const TerrainDecorationConfig &config, float terrainSmoothing)
{
    TerrainDecorationPlacement result;
    constexpr int width = OutdoorMapData::TerrainWidth;
    constexpr int height = OutdoorMapData::TerrainHeight;
    if (map.noTerrain || map.heightMap.size() != width * height || map.tileMap.size() != width * height)
    {
        return result;
    }
    std::vector<std::array<bx::Vec3, 2>> modelBounds;
    modelBounds.reserve(map.bmodels.size());
    for (const OutdoorBModel &model : map.bmodels)
    {
        if (model.vertices.empty())
        {
            continue;
        }
        bx::Vec3 min = {float(model.vertices.front().x), float(model.vertices.front().y),
            float(model.vertices.front().z)};
        bx::Vec3 max = min;
        for (const OutdoorBModelVertex &vertex : model.vertices)
        {
            min = {std::min(min.x, float(vertex.x)), std::min(min.y, float(vertex.y)),
                std::min(min.z, float(vertex.z))};
            max = {std::max(max.x, float(vertex.x)), std::max(max.y, float(vertex.y)),
                std::max(max.z, float(vertex.z))};
        }
        modelBounds.push_back({min, max});
    }
    std::array<std::vector<const TerrainDecorationRule *>, 256> rulesByTile;
    for (size_t tile = 0; tile < textures.size(); ++tile)
    {
        for (const TerrainDecorationRule &rule : config.rules)
        {
            if (textures[tile] == rule.texture)
            {
                rulesByTile[tile].push_back(&rule);
            }
        }
    }
    const auto footprintFits = [&](int cellX, int cellY, float u, float v,
                                   const TerrainDecorationRule &rule, bool fullFootprint = false)
    {
        if (materialCoverage(rule, u, v, fullFootprint) <= 0.0f)
        {
            return false;
        }
        const float radius = (rule.stone || rule.fullFootprint || fullFootprint ? rule.width * 0.65f : 4.0f)
            / OutdoorMapData::TerrainTileSize;
        for (int dy = -1; dy <= 1; ++dy)
        {
            for (int dx = -1; dx <= 1; ++dx)
            {
                const float gx = cellX + u + dx * radius;
                const float gy = cellY + v + dy * radius;
                const int tx = int(std::floor(gx));
                const int ty = int(std::floor(gy));
                if (tx == cellX && ty == cellY)
                {
                    continue;
                }
                if (tx < 0 || ty < 0 || tx >= width - 1 || ty >= height - 1)
                {
                    return false;
                }
                bool allowed = false;
                for (const TerrainDecorationRule *pNeighbor : rulesByTile[map.tileMap[ty * width + tx]])
                {
                    if (pNeighbor->stone == rule.stone && pNeighbor->family == rule.family &&
                        materialCoverage(*pNeighbor, gx - tx, gy - ty, fullFootprint) > 0.0f)
                    {
                        allowed = true;
                        break;
                    }
                }
                if (!allowed)
                {
                    return false;
                }
            }
        }
        return true;
    };
    const OutdoorMeadowField meadowField = buildOutdoorMeadowField(map);
    // Whether any grass grows at a grid position (verges look across family borders).
    const auto grassGrows = [&](float gridX, float gridY)
    {
        const int tx = int(std::floor(gridX));
        const int ty = int(std::floor(gridY));
        if (tx < 0 || ty < 0 || tx >= width - 1 || ty >= height - 1)
        {
            return false;
        }
        for (const TerrainDecorationRule *pRule : rulesByTile[map.tileMap[ty * width + tx]])
        {
            if (!pRule->stone && materialCoverage(*pRule, gridX - tx, gridY - ty) > 0.0f)
            {
                return true;
            }
        }
        return false;
    };
    // The undergrowth's and the bushes' ground: the map's tiles and decorations.
    std::vector<TerrainDecorationSurfaceEntity> entities;
    entities.reserve(map.entities.size());
    for (const OutdoorEntity &entity : map.entities)
    {
        entities.push_back({entity.name, {float(entity.x), float(entity.y), float(entity.z)}});
    }
    PlantGround plantGround;
    plantGround.grassGrows = [&](float px, float py)
    {
        return grassGrows(outdoorWorldToGridXFloat(px), outdoorWorldToGridYFloat(py));
    };
    plantGround.grassAround = [&](float px, float py, float radius)
    {
        const float gridX = outdoorWorldToGridXFloat(px);
        const float gridY = outdoorWorldToGridYFloat(py);
        if (!grassGrows(gridX, gridY))
        {
            return false;
        }
        const float reach = radius / OutdoorMapData::TerrainTileSize;
        for (int direction = 0; direction < 6; ++direction)
        {
            const float angle = float(direction) * 1.0471976f;
            if (!grassGrows(gridX + std::cos(angle) * reach, gridY + std::sin(angle) * reach))
            {
                return false;
            }
        }
        return true;
    };
    plantGround.height = [&](float px, float py)
    {
        return terrainSmoothing > 0.0f ? outdoorSmoothedTerrainHeight(map, outdoorWorldToGridXFloat(px),
            outdoorWorldToGridYFloat(py), terrainSmoothing) : sampleOutdoorRenderedTerrainHeight(map, px, py);
    };
    plantGround.normal = [&](float px, float py)
    {
        return sampleOutdoorRenderedTerrainNormal(map, px, py);
    };
    plantGround.blocked = [&](float px, float py, float z, float radius, float entityRadius)
    {
        return blocked(map, modelBounds, px, py, z, radius, entityRadius);
    };
    plantGround.moisture = [&](float px, float py)
    {
        return meadowField.sample(px, py);
    };
    plantGround.undergrowthRule = [&](float px, float py) -> const TerrainDecorationRule *
    {
        const float gridX = outdoorWorldToGridXFloat(px);
        const float gridY = outdoorWorldToGridYFloat(py);
        const int x = int(std::floor(gridX));
        const int y = int(std::floor(gridY));
        if (x < 0 || y < 0 || x >= width - 1 || y >= width - 1)
        {
            return nullptr;
        }
        const float u = gridX - float(x);
        const float v = gridY - float(y);
        for (const TerrainDecorationRule *pCandidate : rulesByTile[map.tileMap[size_t(y) * width + x]])
        {
            if (!pCandidate->stone && materialCoverage(*pCandidate, u, v, true) > 0.0f)
            {
                return footprintFits(x, y, u, v, *pCandidate, true) ? pCandidate : nullptr;
            }
        }
        return nullptr;
    };
    // Unmown verges: near walls and buildings, or where the grass ends at a road, rock or water (decorations that
    // are trees get undergrowth instead).
    const auto onVerge = [&](float gridX, float gridY, float px, float py, float z, float clearance)
    {
        if (config.verges.distance <= 0.0f)
        {
            return false;
        }
        if (blocked(map, modelBounds, px, py, z, clearance + config.verges.distance, 0.0f))
        {
            return true;
        }
        const float reach = config.verges.distance / OutdoorMapData::TerrainTileSize;
        for (int direction = 0; direction < 6; ++direction)
        {
            const float angle = float(direction) * 1.0471976f;
            if (!grassGrows(gridX + std::cos(angle) * reach, gridY + std::sin(angle) * reach))
            {
                return true;
            }
        }
        return false;
    };
    // Placement is static; no scattering or uploads occur during frames. Each mesh kind gets its own rank quadtree.
    for (bool stone : {false, true})
    {
        std::vector<TerrainDecorationInstance> placed;
        for (int y = 0; y < height - 1; ++y)
        {
            for (int x = 0; x < width - 1; ++x)
            {
                const uint32_t cell = y * width + x;
                for (const TerrainDecorationRule *pRule : rulesByTile[map.tileMap[cell]])
                {
                    const TerrainDecorationRule &rule = *pRule;
                    if (rule.stone != stone)
                    {
                        continue;
                    }
                    const std::vector<TerrainDecorationVariant> &variants =
                        rule.variants.empty() ? config.tuftVariants : rule.variants;
                    uint32_t state = hash(config.seed ^ cell ^ (rule.stone ? 0x517cc1b7u : 0u));
                    const float variation = rule.stone ? 0.0f : config.densityVariation;
                    // Lush ground may raise the density by up to meadow.density.
                    const float maximumDensity = rule.density * (1.0f + variation)
                        * (rule.stone ? 1.0f : 1.0f + config.meadow.density);
                    const int attempts = int(std::ceil(rule.candidates * maximumDensity));
                    for (int i = 0; i < attempts; ++i)
                    {
                        const float u = randomUnit(state);
                        const float v = randomUnit(state);
                        const float px = outdoorGridCornerWorldX(x) + u * 512.0f;
                        const float py = outdoorGridCornerWorldY(y) - v * 512.0f;
                        const float z = terrainSmoothing > 0.0f
                            ? outdoorSmoothedTerrainHeight(map, float(x) + u, float(y) + v, terrainSmoothing)
                            : sampleOutdoorRenderedTerrainHeight(map, px, py);
                        const float scale = 0.7f + 0.6f * randomUnit(state);
                        const float yaw = randomUnit(state) * 6.2831853f;
                        const float shade = 0.9f + 0.15f * randomUnit(state);
                        const float noise = patchNoise(px / config.patchSize, py / config.patchSize, config.seed);
                        const float moisture = rule.stone ? 0.0f : meadowField.sample(px, py);
                        const float density = rule.density * (1.0f + variation * (2.0f * noise - 1.0f))
                            * cellDensity(config, x + u, y + v) * (1.0f - moisture * config.meadow.density);
                        uint32_t detailState = hash(state ^ 0x9a372f51u);
                        const float acceptance = density * rule.candidates / attempts * materialCoverage(rule, u, v);
                        if (randomUnit(detailState) >= acceptance)
                        {
                            continue;
                        }
                        const bx::Vec3 normal = sampleOutdoorRenderedTerrainNormal(map, px, py);
                        const float clearance = rule.width * 0.65f + 32.0f;
                        // Plants thin out over the last 0.1 of the normal before the steepest ground they take.
                        uint32_t slopeState = hash(state ^ 0x3c6ef372u);
                        const float slopeKeep = smoothUnit((normal.z - config.minimumNormalZ) / 0.1f);
                        if (!footprintFits(x, y, u, v, rule) || randomUnit(slopeState) >= slopeKeep ||
                            blocked(map, modelBounds, px, py, z, clearance))
                        {
                            continue;
                        }
                        if (rule.stone)
                        {
                            uint32_t rankState = hash(state ^ 0xc2b2ae35u);
                            placed.push_back({{px, py, z - 1.5f, yaw},
                                {rule.width * scale, rule.height * scale, 0.0f, randomUnit(rankState)},
                                tinted(rule.tint, shade, {1.0f, 1.0f, 1.0f}), {normal.x, normal.y, normal.z, 0.0f}});
                            continue;
                        }
                        // Wildflowers in single-species clusters: the species follows a coarser noise than the
                        // clusters, so neighbouring clusters mostly share it.
                        uint32_t flowerState = hash(state ^ 0x27d4eb2fu);
                        bool flower = false;
                        if (rule.flowers && !config.flowers.variants.empty())
                        {
                            const float threshold = 1.0f - config.flowers.coverage;
                            const float cluster = patchNoise(px / config.flowers.clusterSize,
                                py / config.flowers.clusterSize, config.seed ^ 0x2545f491u);
                            flower = cluster > threshold && randomUnit(flowerState)
                                < config.flowers.chance * smoothUnit((cluster - threshold) / 0.08f);
                        }
                        // Uncut grass. With tall variants it fills whole patches where the patch noise is highest:
                        // tallGrassChance is about the share of the ground in them (the noise exceeds 0.93 - 1.2 x
                        // share on that share of the ground), more on lush ground. Otherwise single tall clumps
                        // scatter over the denser half.
                        float tallChance = 0.0f;
                        if (!rule.tallVariants.empty() && config.tallGrassChance > 0.0f)
                        {
                            const float threshold = 0.93f - 1.2f * config.tallGrassChance + 0.08f * moisture;
                            tallChance = 0.7f * smoothUnit((noise - threshold) / 0.05f);
                        }
                        else if (rule.tallVariants.empty())
                        {
                            tallChance = config.tallGrassChance * 2.0f * smoothUnit((noise - 0.35f) / 0.4f);
                        }
                        if (!flower && onVerge(float(x) + u, float(y) + v, px, py, z, clearance))
                        {
                            tallChance = std::max(tallChance, config.verges.tallChance);
                        }
                        const bool tall = !flower && randomUnit(detailState) < tallChance &&
                            footprintFits(x, y, u, v, rule, true) &&
                            (!rule.tallVariants.empty() || !blocked(map, modelBounds, px, py, z, 144.0f));
                        // A separate random stream preserves the placement and rotation choices.
                        uint32_t variantState = hash(state ^ 0x85ebca6bu);
                        const std::vector<TerrainDecorationVariant> *pChoices = &variants;
                        float choice = randomUnit(variantState);
                        std::array<float, 3> tint = rule.tint;
                        if (flower)
                        {
                            pChoices = &config.flowers.variants;
                            choice = std::clamp(patchNoise(px / (config.flowers.clusterSize * 1.7f),
                                py / (config.flowers.clusterSize * 1.7f), config.seed ^ 0x68e31da4u), 0.0f, 0.999f);
                            tint = config.flowers.tint;
                        }
                        else if (tall && !rule.tallVariants.empty())
                        {
                            pChoices = &rule.tallVariants;
                        }
                        const size_t choiceIndex = chooseVariant(*pChoices, choice);
                        const TerrainDecorationVariant &variant = (*pChoices)[choiceIndex];
                        // A tall instance without tall variants stretches a normal one.
                        const float heightScale = tall && pChoices == &variants
                            ? std::max(variant.heightScale, config.tallGrassScale) : variant.heightScale;
                        // Version 1 atlases use the variant's position.
                        const size_t layer = variant.layer >= 0 ? size_t(variant.layer) : choiceIndex;
                        const float instanceHeight = rule.height * scale * heightScale
                            * (1.0f - moisture * config.meadow.height);
                        const std::array<float, 3> meadowTint = outdoorMeadowTint(moisture, config.meadow.dryTint,
                            config.meadow.lushTint, flower ? 0.4f : 1.0f);
                        // The thinning order, from its own stream so placements are unchanged.
                        uint32_t rankState = hash(state ^ 0xc2b2ae35u);
                        placed.push_back({{px, py, z - 3.0f, yaw},
                            {rule.width * scale * variant.widthScale, instanceHeight, rule.windStrength,
                             randomUnit(rankState)},
                            tinted(tint, shade, meadowTint), {normal.x, normal.y, normal.z, float(layer)}});
                    }
                }
            }
        }
        if (!stone)
        {
            placeUndergrowth(config, entities, plantGround, placed);
        }
        if (stone)
        {
            buildRankTree(placed, true, false, 1.0f, 0.0f, result);
            continue;
        }
        // Clump layers get their own tree: they draw with the clump mesh.
        std::vector<TerrainDecorationInstance> clumps;
        std::erase_if(placed, [&](const TerrainDecorationInstance &instance)
        {
            const bool clump = (config.clump.layerMask >> uint32_t(instance.groundNormal[3])) & 1u;
            if (clump)
            {
                clumps.push_back(instance);
            }
            return clump;
        });
        buildRankTree(placed, false, false, config.lod.maxScale, 0.0f, result);
        const float lean = std::sin(config.clump.leanDegrees * 0.017453293f) * config.clump.cardScale + 0.1f;
        buildRankTree(clumps, false, true, config.lod.maxScale, lean, result);
    }
    placeBushes(config, entities, plantGround, result.bushes);
    return result;
}

namespace
{
// The surface queries' grid: 32 world units a cell over the ground's bounds.
constexpr float SurfaceCellSize = 32.0f;
constexpr float NoSurface = -std::numeric_limits<float>::infinity();

class SurfaceGrid
{
public:
    explicit SurfaceGrid(const std::vector<TerrainDecorationSurfaceTriangle> &ground)
    {
        float minimumX = std::numeric_limits<float>::max();
        float minimumY = std::numeric_limits<float>::max();
        float maximumX = std::numeric_limits<float>::lowest();
        float maximumY = std::numeric_limits<float>::lowest();
        for (const TerrainDecorationSurfaceTriangle &triangle : ground)
        {
            for (const std::array<float, 3> &point : triangle.points)
            {
                minimumX = std::min(minimumX, point[0]);
                minimumY = std::min(minimumY, point[1]);
                maximumX = std::max(maximumX, point[0]);
                maximumY = std::max(maximumY, point[1]);
            }
        }
        if (ground.empty())
        {
            return;
        }
        // A margin of cells round the ground, so the clearance and the verges reach past its edge.
        constexpr float Margin = 512.0f;
        m_originX = std::max(minimumX - Margin, MapMinimum);
        m_originY = std::max(minimumY - Margin, MapMinimum);
        const float limitX = std::min(maximumX + Margin, MapMinimum + MapSize);
        const float limitY = std::min(maximumY + Margin, MapMinimum + MapSize);
        m_width = int(std::ceil((limitX - m_originX) / SurfaceCellSize)) + 1;
        m_height = int(std::ceil((limitY - m_originY) / SurfaceCellSize)) + 1;
        m_top.assign(size_t(m_width) * size_t(m_height), NoSurface);
        m_normal.assign(m_top.size(), {0, 0, 0});
        for (const TerrainDecorationSurfaceTriangle &triangle : ground)
        {
            rasterise(triangle.points, false, [&](size_t cell, float z)
            {
                if (z > m_top[cell])
                {
                    m_top[cell] = z;
                    m_normal[cell] = {int8_t(std::lround(std::clamp(triangle.normal[0], -1.0f, 1.0f) * 127.0f)),
                        int8_t(std::lround(std::clamp(triangle.normal[1], -1.0f, 1.0f) * 127.0f)),
                        int8_t(std::lround(std::clamp(triangle.normal[2], -1.0f, 1.0f) * 127.0f))};
                }
            });
        }
    }

    bool empty() const
    {
        return m_top.empty();
    }

    // The topmost ground at the point: bilinear between cell centres where all four have ground, else its cell's.
    bool groundAt(float x, float y, float &z) const
    {
        const float u = (x - m_originX) / SurfaceCellSize - 0.5f;
        const float v = (y - m_originY) / SurfaceCellSize - 0.5f;
        const int column = int(std::floor(u));
        const int row = int(std::floor(v));
        if (column >= 0 && row >= 0 && column + 1 < m_width && row + 1 < m_height)
        {
            const float a = m_top[index(column, row)];
            const float b = m_top[index(column + 1, row)];
            const float c = m_top[index(column, row + 1)];
            const float d = m_top[index(column + 1, row + 1)];
            if (a != NoSurface && b != NoSurface && c != NoSurface && d != NoSurface)
            {
                const float fu = u - float(column);
                const float fv = v - float(row);
                z = std::lerp(std::lerp(a, b, fu), std::lerp(c, d, fu), fv);
                return true;
            }
        }
        const std::optional<size_t> cell = cellAt(x, y);
        if (!cell || m_top[*cell] == NoSurface)
        {
            return false;
        }
        z = m_top[*cell];
        return true;
    }

    // The topmost ground's smooth normal in the point's cell (zero without ground).
    bx::Vec3 normalAt(float x, float y) const
    {
        const std::optional<size_t> cell = cellAt(x, y);
        if (!cell || m_top[*cell] == NoSurface)
        {
            return {0.0f, 0.0f, 0.0f};
        }
        const std::array<int8_t, 3> &normal = m_normal[*cell];
        return bx::normalize(bx::Vec3{float(normal[0]), float(normal[1]), float(normal[2])});
    }

    // Marks the cells next to the obstacles (other faces whose height range there reaches the ground's, or any where
    // there is no ground) and fills the distance from every cell to the nearest marked one.
    void buildClearance(const std::vector<std::array<std::array<float, 3>, 3>> &obstacles)
    {
        if (empty())
        {
            return;
        }
        std::vector<float> low(m_top.size(), std::numeric_limits<float>::max());
        std::vector<float> high(m_top.size(), std::numeric_limits<float>::lowest());
        for (const std::array<std::array<float, 3>, 3> &triangle : obstacles)
        {
            rasterise(triangle, true, [&](size_t cell, float z)
            {
                low[cell] = std::min(low[cell], z);
                high[cell] = std::max(high[cell], z);
            });
        }
        // Two-pass 3-4 chamfer distance, in cells x 3.
        constexpr uint16_t Far = std::numeric_limits<uint16_t>::max();
        m_clearance.assign(m_top.size(), Far);
        for (size_t cell = 0; cell < m_top.size(); ++cell)
        {
            // The plant test of scatterTerrainDecorations (blocked): the obstacle reaches from 96 over the ground to
            // 48 under it.
            const float top = m_top[cell];
            const bool reaches = top == NoSurface || (top <= high[cell] + 48.0f && top + 96.0f >= low[cell]);
            if (low[cell] <= high[cell] && reaches)
            {
                m_clearance[cell] = 0;
            }
        }
        const auto relax = [&](int column, int row, int dx, int dy, uint16_t cost)
        {
            const int x = column + dx;
            const int y = row + dy;
            if (x >= 0 && y >= 0 && x < m_width && y < m_height)
            {
                uint16_t &value = m_clearance[index(column, row)];
                value = uint16_t(std::min<uint32_t>(value, uint32_t(m_clearance[index(x, y)]) + cost));
            }
        };
        for (int row = 0; row < m_height; ++row)
        {
            for (int column = 0; column < m_width; ++column)
            {
                relax(column, row, -1, 0, 3);
                relax(column, row, 0, -1, 3);
                relax(column, row, -1, -1, 4);
                relax(column, row, 1, -1, 4);
            }
        }
        for (int row = m_height - 1; row >= 0; --row)
        {
            for (int column = m_width - 1; column >= 0; --column)
            {
                relax(column, row, 1, 0, 3);
                relax(column, row, 0, 1, 3);
                relax(column, row, 1, 1, 4);
                relax(column, row, -1, 1, 4);
            }
        }
    }

    // World distance from the point's cell to the nearest obstacle cell (large without obstacles).
    float clearanceAt(float x, float y) const
    {
        const std::optional<size_t> cell = cellAt(x, y);
        if (m_clearance.empty() || !cell)
        {
            return std::numeric_limits<float>::max();
        }
        return float(m_clearance[*cell]) * (SurfaceCellSize / 3.0f);
    }

private:
    size_t index(int column, int row) const
    {
        return size_t(row) * size_t(m_width) + size_t(column);
    }

    std::optional<size_t> cellAt(float x, float y) const
    {
        const int column = int(std::floor((x - m_originX) / SurfaceCellSize));
        const int row = int(std::floor((y - m_originY) / SurfaceCellSize));
        if (column < 0 || row < 0 || column >= m_width || row >= m_height)
        {
            return std::nullopt;
        }
        return index(column, row);
    }

    // Calls visit(cell, z) for each cell whose centre the triangle covers seen from above, with its height there.
    // With edges, also along its edges every half cell (walls are edge-on from above); otherwise a triangle that
    // covers no centre visits its centroid's cell.
    template <typename Visit>
    void rasterise(const std::array<std::array<float, 3>, 3> &points, bool edges, const Visit &visit) const
    {
        const float x0 = (points[0][0] - m_originX) / SurfaceCellSize;
        const float y0 = (points[0][1] - m_originY) / SurfaceCellSize;
        const float x1 = (points[1][0] - m_originX) / SurfaceCellSize;
        const float y1 = (points[1][1] - m_originY) / SurfaceCellSize;
        const float x2 = (points[2][0] - m_originX) / SurfaceCellSize;
        const float y2 = (points[2][1] - m_originY) / SurfaceCellSize;
        bool covered = false;
        const float denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2);
        if (std::abs(denominator) > 1.0e-6f)
        {
            const int firstColumn = std::max(int(std::floor(std::min({x0, x1, x2}) - 0.5f)), 0);
            const int lastColumn = std::min(int(std::ceil(std::max({x0, x1, x2}) - 0.5f)), m_width - 1);
            const int firstRow = std::max(int(std::floor(std::min({y0, y1, y2}) - 0.5f)), 0);
            const int lastRow = std::min(int(std::ceil(std::max({y0, y1, y2}) - 0.5f)), m_height - 1);
            for (int row = firstRow; row <= lastRow; ++row)
            {
                const float cy = float(row) + 0.5f;
                for (int column = firstColumn; column <= lastColumn; ++column)
                {
                    const float cx = float(column) + 0.5f;
                    const float a = ((y1 - y2) * (cx - x2) + (x2 - x1) * (cy - y2)) / denominator;
                    const float b = ((y2 - y0) * (cx - x2) + (x0 - x2) * (cy - y2)) / denominator;
                    const float c = 1.0f - a - b;
                    if (a < -1.0e-5f || b < -1.0e-5f || c < -1.0e-5f)
                    {
                        continue;
                    }
                    covered = true;
                    visit(index(column, row), a * points[0][2] + b * points[1][2] + c * points[2][2]);
                }
            }
        }
        if (edges)
        {
            for (int edge = 0; edge < 3; ++edge)
            {
                const std::array<float, 3> &from = points[size_t(edge)];
                const std::array<float, 3> &to = points[size_t((edge + 1) % 3)];
                const float length = std::hypot(to[0] - from[0], to[1] - from[1]);
                const int steps = std::max(1, int(std::ceil(length / (SurfaceCellSize * 0.5f))));
                for (int step = 0; step <= steps; ++step)
                {
                    const float t = float(step) / float(steps);
                    if (const std::optional<size_t> cell = cellAt(std::lerp(from[0], to[0], t),
                            std::lerp(from[1], to[1], t)))
                    {
                        visit(*cell, std::lerp(from[2], to[2], t));
                    }
                }
            }
        }
        else if (!covered)
        {
            const float x = (points[0][0] + points[1][0] + points[2][0]) / 3.0f;
            const float y = (points[0][1] + points[1][1] + points[2][1]) / 3.0f;
            if (const std::optional<size_t> cell = cellAt(x, y))
            {
                visit(*cell, (points[0][2] + points[1][2] + points[2][2]) / 3.0f);
            }
        }
    }

    float m_originX = 0.0f;
    float m_originY = 0.0f;
    int m_width = 0;
    int m_height = 0;
    std::vector<float> m_top;
    std::vector<std::array<int8_t, 3>> m_normal;
    std::vector<uint16_t> m_clearance;
};

// The entities near a point: buckets of 512 units over the map frame.
class SurfaceEntityIndex
{
public:
    explicit SurfaceEntityIndex(const std::vector<TerrainDecorationSurfaceEntity> &entities)
        : m_entities(entities), m_buckets(size_t(Side) * Side)
    {
        for (size_t index = 0; index < entities.size(); ++index)
        {
            m_buckets[bucket(entities[index].position[0], entities[index].position[1])].push_back(uint32_t(index));
        }
    }

    // ODM blocked's entity test: an entity within radius whose height is within 128 of z.
    bool near(float x, float y, float z, float radius) const
    {
        if (radius <= 0.0f)
        {
            return false;
        }
        const int reach = int(std::ceil(radius / BucketSize));
        const int column = std::clamp(int(std::floor((x - MapMinimum) / BucketSize)), 0, Side - 1);
        const int row = std::clamp(int(std::floor((y - MapMinimum) / BucketSize)), 0, Side - 1);
        for (int bucketY = std::max(row - reach, 0); bucketY <= std::min(row + reach, Side - 1); ++bucketY)
        {
            for (int bucketX = std::max(column - reach, 0); bucketX <= std::min(column + reach, Side - 1); ++bucketX)
            {
                for (uint32_t index : m_buckets[size_t(bucketY) * Side + size_t(bucketX)])
                {
                    const std::array<float, 3> &position = m_entities[index].position;
                    const float dx = x - position[0];
                    const float dy = y - position[1];
                    if (dx * dx + dy * dy < radius * radius && std::abs(z - position[2]) < 128.0f)
                    {
                        return true;
                    }
                }
            }
        }
        return false;
    }

private:
    static constexpr int Side = 128;
    static constexpr float BucketSize = 512.0f;

    size_t bucket(float x, float y) const
    {
        const int column = std::clamp(int(std::floor((x - MapMinimum) / BucketSize)), 0, Side - 1);
        const int row = std::clamp(int(std::floor((y - MapMinimum) / BucketSize)), 0, Side - 1);
        return size_t(row) * Side + size_t(column);
    }

    const std::vector<TerrainDecorationSurfaceEntity> &m_entities;
    std::vector<std::vector<uint32_t>> m_buckets;
};

// Where grass of the surface grows: some grass layer, ground gentle enough and out of the water.
constexpr float SurfaceGrassDensity = 0.3f;
}

TerrainDecorationPlacement scatterTerrainDecorationsOnSurface(const TerrainDecorationSurface &surface,
    const TerrainDecorationConfig &config)
{
    TerrainDecorationPlacement result;
    const auto ruleIt = std::find_if(config.rules.begin(), config.rules.end(),
        [](const TerrainDecorationRule &rule) { return !rule.stone; });
    if (ruleIt == config.rules.end() || !surface.density || surface.ground.empty())
    {
        return result;
    }
    const TerrainDecorationRule &rule = *ruleIt;
    const std::vector<TerrainDecorationVariant> &variants = rule.variants.empty() ? config.tuftVariants : rule.variants;
    SurfaceGrid grid(surface.ground);
    grid.buildClearance(surface.obstacles);
    const SurfaceEntityIndex entities(surface.entities);
    const auto moistureAt = [&](float x, float y)
    {
        return surface.pMeadow != nullptr ? surface.pMeadow->sample(x, y) : 0.0f;
    };
    const auto underWater = [&](float x, float y, float z)
    {
        return surface.underWater && surface.underWater(x, y, z);
    };
    const auto blocked = [&](float x, float y, float z, float radius, float entityRadius)
    {
        return grid.clearanceAt(x, y) < radius || entities.near(x, y, z, entityRadius);
    };
    const auto grassGrows = [&](float x, float y)
    {
        float z = 0.0f;
        return grid.groundAt(x, y, z) && grid.normalAt(x, y).z >= config.minimumNormalZ
            && surface.density(x, y) > SurfaceGrassDensity && !underWater(x, y, z);
    };
    const auto grassAround = [&](float x, float y, float radius)
    {
        if (!grassGrows(x, y))
        {
            return false;
        }
        for (int direction = 0; direction < 6; ++direction)
        {
            const float angle = float(direction) * 1.0471976f;
            if (!grassGrows(x + std::cos(angle) * radius, y + std::sin(angle) * radius))
            {
                return false;
            }
        }
        return true;
    };
    // An outdoor rule's candidates are per 512 x 512 cell; lush ground may raise the density by up to meadow.density.
    const float candidatesPerArea = float(rule.candidates) / (512.0f * 512.0f);
    const float maximumDensity = std::max(rule.density * (1.0f + config.densityVariation)
        * (1.0f + config.meadow.density), 0.0001f);
    std::vector<TerrainDecorationInstance> placed;
    for (size_t index = 0; index < surface.ground.size(); ++index)
    {
        const TerrainDecorationSurfaceTriangle &triangle = surface.ground[index];
        const std::array<float, 3> &normal = triangle.normal;
        if (normal[2] < config.minimumNormalZ - 0.1f)
        {
            continue;
        }
        const std::array<float, 3> &p0 = triangle.points[0];
        const std::array<float, 3> edgeA = {triangle.points[1][0] - p0[0], triangle.points[1][1] - p0[1],
            triangle.points[1][2] - p0[2]};
        const std::array<float, 3> edgeB = {triangle.points[2][0] - p0[0], triangle.points[2][1] - p0[1],
            triangle.points[2][2] - p0[2]};
        const float crossX = edgeA[1] * edgeB[2] - edgeA[2] * edgeB[1];
        const float crossY = edgeA[2] * edgeB[0] - edgeA[0] * edgeB[2];
        const float crossZ = edgeA[0] * edgeB[1] - edgeA[1] * edgeB[0];
        const float area = 0.5f * std::sqrt(crossX * crossX + crossY * crossY + crossZ * crossZ);
        if (!(area > 0.0f))
        {
            continue;
        }
        uint32_t state = hash(config.seed ^ (uint32_t(index) * 0x9e3779b9u));
        const float expected = area * candidatesPerArea * maximumDensity;
        int attempts = int(std::floor(expected));
        if (randomUnit(state) < expected - float(attempts))
        {
            ++attempts;
        }
        for (int attempt = 0; attempt < attempts; ++attempt)
        {
            float a = randomUnit(state);
            float b = randomUnit(state);
            if (a + b > 1.0f)
            {
                a = 1.0f - a;
                b = 1.0f - b;
            }
            const float px = p0[0] + edgeA[0] * a + edgeB[0] * b;
            const float py = p0[1] + edgeA[1] * a + edgeB[1] * b;
            const float pz = p0[2] + edgeA[2] * a + edgeB[2] * b;
            const float scale = 0.7f + 0.6f * randomUnit(state);
            const float yaw = randomUnit(state) * 6.2831853f;
            const float shade = 0.9f + 0.15f * randomUnit(state);
            const float noise = patchNoise(px / config.patchSize, py / config.patchSize, config.seed);
            const float moisture = moistureAt(px, py);
            const float wanted = std::clamp(surface.density(px, py), 0.0f, 1.0f) * rule.density
                * (1.0f + config.densityVariation * (2.0f * noise - 1.0f)) * (1.0f - moisture * config.meadow.density);
            uint32_t detailState = hash(state ^ 0x9a372f51u);
            if (randomUnit(detailState) >= wanted / maximumDensity)
            {
                continue;
            }
            // Plants thin out over the last 0.1 of the normal before the steepest ground they take.
            uint32_t slopeState = hash(state ^ 0x3c6ef372u);
            const float clearance = rule.width * 0.65f + 32.0f;
            if (randomUnit(slopeState) >= smoothUnit((normal[2] - config.minimumNormalZ) / 0.1f)
                || underWater(px, py, pz) || blocked(px, py, pz, clearance, 80.0f))
            {
                continue;
            }
            uint32_t flowerState = hash(state ^ 0x27d4eb2fu);
            bool flower = false;
            if (rule.flowers && !config.flowers.variants.empty())
            {
                const float threshold = 1.0f - config.flowers.coverage;
                const float cluster = patchNoise(px / config.flowers.clusterSize, py / config.flowers.clusterSize,
                    config.seed ^ 0x2545f491u);
                flower = cluster > threshold && randomUnit(flowerState)
                    < config.flowers.chance * smoothUnit((cluster - threshold) / 0.08f);
            }
            // Uncut grass in patches (more on lush ground), and along the verges: beside walls and buildings and
            // where the grass ends (rock, roads, water), as scatterTerrainDecorations.
            float tallChance = 0.0f;
            if (!rule.tallVariants.empty() && config.tallGrassChance > 0.0f)
            {
                const float threshold = 0.93f - 1.2f * config.tallGrassChance + 0.08f * moisture;
                tallChance = 0.7f * smoothUnit((noise - threshold) / 0.05f);
            }
            else if (rule.tallVariants.empty())
            {
                tallChance = config.tallGrassChance * 2.0f * smoothUnit((noise - 0.35f) / 0.4f);
            }
            if (!flower && config.verges.distance > 0.0f
                && (blocked(px, py, pz, clearance + config.verges.distance, 0.0f)
                    || !grassAround(px, py, config.verges.distance)))
            {
                tallChance = std::max(tallChance, config.verges.tallChance);
            }
            const bool tall = !flower && randomUnit(detailState) < tallChance;
            uint32_t variantState = hash(state ^ 0x85ebca6bu);
            const std::vector<TerrainDecorationVariant> *pChoices = &variants;
            float choice = randomUnit(variantState);
            std::array<float, 3> tint = rule.tint;
            if (flower)
            {
                pChoices = &config.flowers.variants;
                choice = std::clamp(patchNoise(px / (config.flowers.clusterSize * 1.7f),
                    py / (config.flowers.clusterSize * 1.7f), config.seed ^ 0x68e31da4u), 0.0f, 0.999f);
                tint = config.flowers.tint;
            }
            else if (tall && !rule.tallVariants.empty())
            {
                pChoices = &rule.tallVariants;
            }
            const size_t choiceIndex = chooseVariant(*pChoices, choice);
            const TerrainDecorationVariant &variant = (*pChoices)[choiceIndex];
            const float heightScale = tall && pChoices == &variants
                ? std::max(variant.heightScale, config.tallGrassScale) : variant.heightScale;
            const size_t layer = variant.layer >= 0 ? size_t(variant.layer) : choiceIndex;
            const std::array<float, 3> meadowTint = outdoorMeadowTint(moisture, config.meadow.dryTint,
                config.meadow.lushTint, flower ? 0.4f : 1.0f);
            uint32_t rankState = hash(state ^ 0xc2b2ae35u);
            placed.push_back({{px, py, pz - 3.0f, yaw},
                {rule.width * scale * variant.widthScale,
                 rule.height * scale * heightScale * (1.0f - moisture * config.meadow.height), rule.windStrength,
                 randomUnit(rankState)},
                tinted(tint, shade, meadowTint), {normal[0], normal[1], normal[2], float(layer)}});
        }
    }
    PlantGround ground;
    ground.grassGrows = grassGrows;
    ground.grassAround = grassAround;
    ground.height = [&](float x, float y)
    {
        float z = 0.0f;
        grid.groundAt(x, y, z);
        return z;
    };
    ground.normal = [&](float x, float y)
    {
        return grid.normalAt(x, y);
    };
    ground.blocked = blocked;
    ground.moisture = moistureAt;
    ground.undergrowthRule = [&](float x, float y) -> const TerrainDecorationRule *
    {
        return grassGrows(x, y) ? &rule : nullptr;
    };
    placeUndergrowth(config, surface.entities, ground, placed);
    // Clump layers get their own tree: they draw with the clump mesh (as scatterTerrainDecorations).
    std::vector<TerrainDecorationInstance> clumps;
    std::erase_if(placed, [&](const TerrainDecorationInstance &instance)
    {
        const bool clump = (config.clump.layerMask >> uint32_t(instance.groundNormal[3])) & 1u;
        if (clump)
        {
            clumps.push_back(instance);
        }
        return clump;
    });
    buildRankTree(placed, false, false, config.lod.maxScale, 0.0f, result);
    const float lean = std::sin(config.clump.leanDegrees * 0.017453293f) * config.clump.cardScale + 0.1f;
    buildRankTree(clumps, false, true, config.lod.maxScale, lean, result);
    placeBushes(config, surface.entities, ground, result.bushes);
    return result;
}

OutdoorMeadowField buildTerrainSurfaceMeadow(const std::vector<TerrainDecorationSurfaceTriangle> &ground,
    const std::function<bool(float x, float y, float z)> &underWater)
{
    const SurfaceGrid grid(ground);
    if (grid.empty())
    {
        return {};
    }
    constexpr int Side = OutdoorMapData::TerrainWidth;
    std::vector<float> heights(size_t(Side) * Side, NoSurface);
    std::vector<uint8_t> water(size_t(Side) * Side, 0);
    std::vector<size_t> frontier;
    for (int y = 0; y < Side; ++y)
    {
        for (int x = 0; x < Side; ++x)
        {
            const size_t index = size_t(y) * Side + size_t(x);
            float z = 0.0f;
            if (grid.groundAt(outdoorGridCornerWorldX(x), outdoorGridCornerWorldY(y), z))
            {
                heights[index] = z;
                frontier.push_back(index);
            }
            if (x + 1 < Side && y + 1 < Side)
            {
                const float centerX = outdoorGridCornerWorldX(x) + 0.5f * OutdoorMapData::TerrainTileSize;
                const float centerY = outdoorGridCornerWorldY(y) - 0.5f * OutdoorMapData::TerrainTileSize;
                const bool hasGround = grid.groundAt(centerX, centerY, z);
                water[index] = underWater && underWater(centerX, centerY,
                    hasGround ? z : std::numeric_limits<float>::lowest()) ? 1 : 0;
            }
        }
    }
    if (frontier.empty())
    {
        return {};
    }
    // Corners without ground take the nearest ground's height (breadth first), so the relief has no cliffs to nothing.
    for (size_t next = 0; next < frontier.size(); ++next)
    {
        const size_t index = frontier[next];
        const int x = int(index % Side);
        const int y = int(index / Side);
        for (const std::array<int, 2> offset : {std::array<int, 2>{1, 0}, {-1, 0}, {0, 1}, {0, -1}})
        {
            const int nx = x + offset[0];
            const int ny = y + offset[1];
            if (nx < 0 || ny < 0 || nx >= Side || ny >= Side)
            {
                continue;
            }
            const size_t neighbour = size_t(ny) * Side + size_t(nx);
            if (heights[neighbour] == NoSurface)
            {
                heights[neighbour] = heights[index];
                frontier.push_back(neighbour);
            }
        }
    }
    return buildMeadowField(heights, water);
}

std::array<std::array<float, 2>, TerrainDecorationCutoutVertices> terrainDecorationCutout(
    const std::vector<uint8_t> &alpha, int width, int height, uint8_t threshold)
{
    using Point = std::array<float, 2>;
    std::array<Point, TerrainDecorationCutoutVertices> result = {};
    const std::array<Point, 4> quad = {{{0.0f, 0.0f}, {0.0f, 1.0f}, {1.0f, 1.0f}, {1.0f, 0.0f}}};
    const auto fill = [&result](const std::vector<Point> &polygon)
    {
        for (size_t index = 0; index < result.size(); ++index)
        {
            result[index] = polygon[std::min(index, polygon.size() - 1)];
        }
        return result;
    };
    if (width <= 0 || height <= 0 || alpha.size() < size_t(width) * size_t(height))
    {
        return fill({quad.begin(), quad.end()});
    }
    // Corners of the leftmost and rightmost covered texel of every row bound the covered area.
    std::vector<Point> points;
    for (int y = 0; y < height; ++y)
    {
        int first = -1;
        int last = -1;
        for (int x = 0; x < width; ++x)
        {
            if (alpha[size_t(y) * width + x] >= threshold)
            {
                first = first < 0 ? x : first;
                last = x;
            }
        }
        if (first >= 0)
        {
            for (const float row : {float(y), float(y + 1)})
            {
                points.push_back({float(first) / width, row / height});
                points.push_back({float(last + 1) / width, row / height});
            }
        }
    }
    if (points.size() < 3)
    {
        return fill({quad.begin(), quad.end()});
    }
    // Convex hull (monotone chain).
    std::sort(points.begin(), points.end());
    const auto cross = [](const Point &o, const Point &a, const Point &b)
    {
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    };
    std::vector<Point> hull(points.size() * 2);
    size_t count = 0;
    for (size_t pass = 0; pass < 2; ++pass)
    {
        const size_t start = count;
        for (size_t step = 0; step < points.size(); ++step)
        {
            const Point &point = pass == 0 ? points[step] : points[points.size() - 1 - step];
            while (count >= start + 2 && cross(hull[count - 2], hull[count - 1], point) <= 0.0f)
            {
                --count;
            }
            hull[count++] = point;
        }
        --count;
    }
    hull.resize(count);
    // Fewer vertices by replacing an edge with the meeting point of its neighbours' extensions, cheapest first; the
    // polygon only grows, so it keeps enclosing the hull.
    while (hull.size() > TerrainDecorationCutoutVertices)
    {
        const size_t n = hull.size();
        float bestArea = std::numeric_limits<float>::max();
        size_t bestEdge = n;
        Point bestPoint = {};
        for (size_t edge = 0; edge < n; ++edge)
        {
            const Point &a0 = hull[(edge + n - 1) % n];
            const Point &a1 = hull[edge];
            const Point &b0 = hull[(edge + 1) % n];
            const Point &b1 = hull[(edge + 2) % n];
            const Point da = {a1[0] - a0[0], a1[1] - a0[1]};
            const Point db = {b0[0] - b1[0], b0[1] - b1[1]};
            const float denominator = da[0] * db[1] - da[1] * db[0];
            if (std::abs(denominator) < 1.0e-9f)
            {
                continue;
            }
            const float t = ((b1[0] - a0[0]) * db[1] - (b1[1] - a0[1]) * db[0]) / denominator;
            const Point meet = {a0[0] + da[0] * t, a0[1] + da[1] * t};
            if (t < 1.0f || meet[0] < 0.0f || meet[0] > 1.0f || meet[1] < 0.0f || meet[1] > 1.0f)
            {
                continue;
            }
            const float area = std::abs(cross(a1, meet, b0)) * 0.5f;
            if (area < bestArea)
            {
                bestArea = area;
                bestEdge = edge;
                bestPoint = meet;
            }
        }
        if (bestEdge == n)
        {
            return fill({quad.begin(), quad.end()});
        }
        hull[bestEdge] = bestPoint;
        hull.erase(hull.begin() + long((bestEdge + 1) % n));
    }
    // A small outward margin covers the alpha spread of the lower mip levels.
    Point centre = {};
    for (const Point &point : hull)
    {
        centre[0] += point[0] / float(hull.size());
        centre[1] += point[1] / float(hull.size());
    }
    for (Point &point : hull)
    {
        for (size_t axis = 0; axis < 2; ++axis)
        {
            point[axis] = std::clamp(centre[axis] + (point[axis] - centre[axis]) * 1.04f, 0.0f, 1.0f);
        }
    }
    return fill(hull);
}

float terrainDecorationKeep(const TerrainDecorationLod &lod, float distance)
{
    const float thinned = distance <= lod.nearDistance ? 1.0f
        : (lod.nearDistance * lod.nearDistance) / (distance * distance);
    return thinned * (1.0f - smoothUnit((distance - lod.farDistance * 0.85f) / (lod.farDistance * 0.15f)));
}

float terrainDecorationScale(const TerrainDecorationLod &lod, float distance)
{
    return std::clamp(distance / lod.nearDistance, 1.0f, lod.maxScale);
}

uint32_t terrainDecorationPrefix(const std::vector<float> &ranks, const TerrainDecorationPatch &range, float keep)
{
    const auto begin = ranks.begin() + range.first;
    return uint32_t(std::lower_bound(begin, begin + range.count, keep) - begin);
}

float terrainDecorationClumpArea(const TerrainDecorationClump &clump)
{
    // Each card faces a random horizontal direction: 2 / pi of its area on average.
    return float(clump.cards) * clump.cardScale * clump.cardScale * 0.63662f;
}

std::vector<float> buildTerrainFoliageMap(const TerrainDecorationPlacement &placement,
    const std::vector<TerrainFoliageLayer> &layers, const TerrainDecorationClump &clump)
{
    const float clumpArea = terrainDecorationClumpArea(clump);
    constexpr int size = TerrainFoliageMapSize;
    constexpr float texel = MapSize / float(size);
    std::vector<float> sums(size_t(size) * size * 4, 0.0f);
    for (const TerrainDecorationNode &node : placement.nodes)
    {
        if (node.range.stone)
        {
            continue;
        }
        for (uint32_t index = node.range.first; index < node.range.first + node.range.count; ++index)
        {
            const TerrainDecorationInstance &instance = placement.instances[index];
            const size_t layer = size_t(instance.groundNormal[3]);
            if (layer >= layers.size())
            {
                continue;
            }
            // One card turned to face the camera: its whole area; a clump its cards'.
            const float area = instance.sizeWindRank[0] * instance.sizeWindRank[1] * layers[layer].fill
                * (node.range.clump ? clumpArea : 1.0f);
            const std::array<float, 3> color = {layers[layer].color[0] * instance.color[0],
                layers[layer].color[1] * instance.color[1], layers[layer].color[2] * instance.color[2]};
            // Bilinear splat between the four nearest texel centres; row 0 is the north edge.
            const float u = (instance.positionYaw[0] - MapMinimum) / texel - 0.5f;
            const float v = (MapMinimum + MapSize - instance.positionYaw[1]) / texel - 0.5f;
            const int x0 = int(std::floor(u));
            const int y0 = int(std::floor(v));
            for (int corner = 0; corner < 4; ++corner)
            {
                const int x = x0 + corner % 2;
                const int y = y0 + corner / 2;
                if (x < 0 || y < 0 || x >= size || y >= size)
                {
                    continue;
                }
                const float weight = area * (corner % 2 ? u - x0 : 1.0f - (u - x0))
                    * (corner / 2 ? v - y0 : 1.0f - (v - y0));
                float *pTexel = &sums[(size_t(y) * size + x) * 4];
                pTexel[0] += color[0] * weight;
                pTexel[1] += color[1] * weight;
                pTexel[2] += color[2] * weight;
                pTexel[3] += weight;
            }
        }
    }
    // Per ground area, softened by a separable 3x3 tent so single tufts do not show as texels.
    const auto tent = [&](const std::vector<float> &source, int stepX, int stepY)
    {
        std::vector<float> blurred(source.size(), 0.0f);
        for (int y = 0; y < size; ++y)
        {
            for (int x = 0; x < size; ++x)
            {
                float total = 0.0f;
                std::array<float, 4> value = {};
                for (int offset = -1; offset <= 1; ++offset)
                {
                    const int sx = x + offset * stepX;
                    const int sy = y + offset * stepY;
                    if (sx < 0 || sy < 0 || sx >= size || sy >= size)
                    {
                        continue;
                    }
                    const float weight = float(2 - std::abs(offset));
                    total += weight;
                    for (size_t channel = 0; channel < 4; ++channel)
                    {
                        value[channel] += source[(size_t(sy) * size + sx) * 4 + channel] * weight;
                    }
                }
                for (size_t channel = 0; channel < 4; ++channel)
                {
                    blurred[(size_t(y) * size + x) * 4 + channel] = value[channel] / total;
                }
            }
        }
        return blurred;
    };
    std::vector<float> result = tent(tent(sums, 1, 0), 0, 1);
    for (float &value : result)
    {
        value /= texel * texel;
    }
    return result;
}

std::vector<uint8_t> encodeTerrainFoliageMap(const std::vector<float> &foliage)
{
    std::vector<uint8_t> result;
    std::vector<float> level = foliage;
    for (int size = TerrainFoliageMapSize; size >= 1; size /= 2)
    {
        for (size_t texel = 0; texel < size_t(size) * size; ++texel)
        {
            const float *pValue = &level[texel * 4];
            const float depth = pValue[3];
            for (int channel = 0; channel < 3; ++channel)
            {
                const float color = depth > 0.0f ? pValue[channel] / depth : 0.0f;
                result.push_back(uint8_t(std::lround(std::clamp(color, 0.0f, 1.0f) * 255.0f)));
            }
            result.push_back(uint8_t(std::lround(std::clamp(depth / TerrainFoliageDepthRange, 0.0f, 1.0f) * 255.0f)));
        }
        if (size == 1)
        {
            break;
        }
        // The next mip level averages the premultiplied values, so the colour follows the coverage.
        const int half = size / 2;
        std::vector<float> next(size_t(half) * half * 4, 0.0f);
        for (int y = 0; y < half; ++y)
        {
            for (int x = 0; x < half; ++x)
            {
                for (int corner = 0; corner < 4; ++corner)
                {
                    const size_t source = (size_t(y * 2 + corner / 2) * size + x * 2 + corner % 2) * 4;
                    for (size_t channel = 0; channel < 4; ++channel)
                    {
                        next[(size_t(y) * half + x) * 4 + channel] += level[source + channel] * 0.25f;
                    }
                }
            }
        }
        level.swap(next);
    }
    return result;
}
} // namespace OpenYAMM::Game
