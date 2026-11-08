#pragma once

#include "engine/AssetFileSystem.h"
#include "game/outdoor/OutdoorMapData.h"

#include <array>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorMeadowField;

struct TerrainDecorationVariant
{
    float weight = 1.0f;
    float widthScale = 1.0f;
    float heightScale = 1.0f;
    int layer = -1; // Version 1 uses the variant's position in the atlas.
};

struct TerrainDecorationRule
{
    std::string texture;
    bool stone = false;
    int candidates = 64;
    float density = 1.0f;
    float width = 40.0f;
    float height = 28.0f;
    std::array<float, 3> tint = {1.0f, 1.0f, 1.0f};
    int maskWidth = 0;
    int maskHeight = 0;
    std::vector<uint8_t> coverage;
    std::string family;
    bool fullFootprint = false;
    float windStrength = 2.5f;
    std::vector<TerrainDecorationVariant> variants;
    // Uncut grass for tall patches and verges (MEADOW.md); without them a tall instance scales a normal variant.
    std::vector<TerrainDecorationVariant> tallVariants;
    // The family grows the library's wildflower clusters.
    bool flowers = false;
};

// Ground moisture (OutdoorMeadowField): dry ground grows yellower, sparser and shorter grass, lush ground the opposite.
struct TerrainDecorationMeadow
{
    std::array<float, 3> dryTint = {1.0f, 1.0f, 1.0f};
    std::array<float, 3> lushTint = {1.0f, 1.0f, 1.0f};
    // Fractions by which full dryness (or lushness) lowers (raises) density and height.
    float density = 0.0f;
    float height = 0.0f;
};

// Single-species wildflower clusters among the grass of families with flowers.
struct TerrainDecorationFlowers
{
    // Share of the ground inside clusters, the clusters' size in world units, and the share of grass instances
    // inside a cluster that become flowers.
    float coverage = 0.0f;
    float clusterSize = 900.0f;
    float chance = 0.0f;
    std::array<float, 3> tint = {1.0f, 1.0f, 1.0f};
    std::vector<TerrainDecorationVariant> variants;
};

// Unmown grass along walls, buildings, decorations and the edges of roads and water.
struct TerrainDecorationVerges
{
    float distance = 0.0f;
    float tallChance = 0.0f;
};

// Ferns and tall grass around the trunks of the named map decorations.
struct TerrainDecorationUndergrowth
{
    std::vector<std::string> decorations; // Substrings of the decoration names.
    float innerRadius = 90.0f;
    float outerRadius = 260.0f;
    int candidates = 0;
    std::vector<TerrainDecorationVariant> variants;
};

// Low 3D bushes (static models) placed with the grass: groups at tree lines (around the undergrowth decorations),
// along buildings and walls, in lush hollows and rarely on open grass. Never on roads, rock or water: grass grows
// all around each bush.
struct TerrainDecorationBushModel
{
    std::string model; // Virtual path of the GLB.
    float height = 120.0f;
    float weight = 1.0f;
};

struct TerrainDecorationBushes
{
    std::vector<TerrainDecorationBushModel> models;
    float heightJitter = 0.2f;
    // Grid of candidate group positions for the open ground, lush hollows and verges.
    float spacing = 640.0f;
    float meadowChance = 0.02f;
    float lushChance = 0.3f;
    float lushBelow = -0.3f; // Meadow field value (-1 lush .. +1 dry).
    float vergeChance = 0.35f;
    float vergeDistance = 260.0f; // From buildings and walls.
    // A group's chance per tree line decoration, at a distance in edgeRadius.
    float edgeChance = 0.4f;
    std::array<float, 2> edgeRadius = {300.0f, 650.0f};
    int groupMax = 3;
    float groupSpread = 150.0f;
    // Grass grows all around this radius; buildings and decorations stay clearance beyond it.
    float radius = 90.0f;
    float clearance = 60.0f;
    float minimumNormalZ = 0.8f;
    int maxCount = 600;
    // Camera distance over which the bushes dissolve out.
    std::array<float, 2> fadeDistance = {5000.0f, 6500.0f};
};

struct TerrainBushInstance
{
    std::array<float, 3> position;
    float yaw = 0.0f;
    float heightScale = 1.0f; // Of the model's height.
    uint32_t model = 0;
};

// Short grass drawn as a clump of cards in a star, each leaning outward, instead of one camera-facing card
// (vs_terrain_decoration.sc): it reads as a tuft from the side, at a raised angle and from above.
constexpr int TerrainDecorationMaxClumpCards = 8;

struct TerrainDecorationClump
{
    uint32_t layerMask = 0; // Bit n: atlas layer n is drawn as a clump.
    int cards = 5;
    float leanDegrees = 25.0f;
    float cardScale = 0.75f; // Of the instance's width and height.
    // Camera distance where a clump is down to its first card (the others thin out over the last quarter).
    float distance = 1500.0f;
};

// Plants that fade out as the camera flies (vs_terrain_decoration.sc): short mats seen from above are slivers, and the
// terrain under them already has their colour.
struct TerrainDecorationOverhead
{
    uint32_t layerMask = 0; // Bit n: atlas layer n fades.
    float start = 250.0f; // Camera height above the ground under it where the fade begins and ends.
    float end = 600.0f;
    // How strongly the terrain takes the plants' colour from the foliage map when seen from above.
    float ground = 0.0f;
};

// Distance level of detail (level_generation/terrain/GRASS_LOD.md), mirrored by vs_terrain_decoration.sc.
struct TerrainDecorationLod
{
    float nearDistance = 2048.0f;
    float farDistance = 16384.0f;
    float maxScale = 2.0f;
};

struct TerrainDecorationConfig
{
    uint32_t seed = 1;
    // Grass thins beyond lod.nearDistance; stones keep their count to stoneDistance and then fade.
    TerrainDecorationLod lod;
    float stoneDistance = 2048.0f;
    // Strength of the terrain's grass colour where the tufts have thinned out (0 = none).
    float foliageTint = 1.0f;
    // How much darker the ground is under dense grass while the grass is drawn (its shade between the tufts).
    float groundShade = 0.0f;
    float minimumNormalZ = 0.85f;
    float densityVariation = 0.0f;
    float patchSize = 768.0f;
    float tallGrassChance = 0.0f;
    float tallGrassScale = 1.8f;
    TerrainDecorationMeadow meadow;
    TerrainDecorationFlowers flowers;
    TerrainDecorationVerges verges;
    TerrainDecorationUndergrowth undergrowth;
    TerrainDecorationOverhead overhead;
    TerrainDecorationClump clump;
    TerrainDecorationBushes bushes;
    // Optional 128x128 cell-centred grayscale control: black = none, white = full density.
    std::vector<uint8_t> densityMask;
    std::string tuftTexture;
    std::array<int, 2> tuftAtlasGrid = {1, 1};
    std::vector<TerrainDecorationVariant> tuftVariants = {TerrainDecorationVariant{}};
    std::vector<TerrainDecorationRule> rules;
};

// Four vec4s, matching i_data0..3 in the instanced vertex shader.
struct TerrainDecorationInstance
{
    std::array<float, 4> positionYaw;
    // w = rank in [0, 1): the instance is drawn while its rank is below terrainDecorationKeep.
    std::array<float, 4> sizeWindRank;
    std::array<float, 4> color;
    std::array<float, 4> groundNormal; // xyz = surface normal; w = tuft texture layer.
};

struct TerrainDecorationPatch
{
    uint32_t first = 0;
    uint32_t count = 0;
    bool stone = false;
    bool clump = false; // Grass drawn with the clump mesh (TerrainDecorationClump).
    std::array<float, 3> min;
    std::array<float, 3> max;
};

// A rank quadtree node. Leaves are TerrainDecorationLeafSize squares; a node j levels above the leaves holds the
// ranks [4^-(j+1), 4^-j) of its area (the root everything below), sorted ascending, so a draw is a prefix of range.
struct TerrainDecorationNode
{
    TerrainDecorationPatch range; // Own instances, with bounds that include the largest LOD scale and wind.
    float rankBegin = 0.0f;
    float rankEnd = 1.0f; // Children hold the ranks from rankEnd up.
    std::array<float, 3> regionMin; // Bounds of the whole subtree.
    std::array<float, 3> regionMax;
    std::array<uint32_t, 4> children = {};
    uint32_t childCount = 0;
};

constexpr float TerrainDecorationLeafSize = 2048.0f;

struct TerrainDecorationPlacement
{
    std::vector<TerrainDecorationInstance> instances;
    // One quadtree per mesh kind, depth first: a node's instances directly precede its first child's.
    std::vector<TerrainDecorationNode> nodes;
    std::vector<uint32_t> roots;
    std::vector<TerrainBushInstance> bushes;
};

// Share of an area's instances drawn at a camera distance: all within nearDistance, then (near / distance)^2, which
// keeps the count per screen area constant, falling to none over the last 15 % of farDistance.
float terrainDecorationKeep(const TerrainDecorationLod &lod, float distance);
// Footprint scale that keeps the thinned coverage (keep * scale^2 = 1), at most lod.maxScale; ignores the end fade.
float terrainDecorationScale(const TerrainDecorationLod &lod, float distance);
// Number of a node's leading instances (sorted by rank) whose rank is below keep; ranks holds every instance's rank.
uint32_t terrainDecorationPrefix(const std::vector<float> &ranks, const TerrainDecorationPatch &range, float keep);

// Grass shading by height (vs_terrain_decoration.sc): rise 0 at the card's bottom row, 1 at its top. Root to tip
// brightness, times the dry tips of some tufts (amount uniform squared, so a third on average).
struct TerrainDecorationShade
{
    static constexpr float Root = 0.72f;
    static constexpr float Tip = 1.28f;
    static constexpr std::array<float, 3> DryTip = {1.15f, 1.1f, 0.85f};
    // The average multiplier of a texel at this rise over all tufts.
    static std::array<float, 3> average(float rise)
    {
        const float brightness = Root + (Tip - Root) * rise;
        return {brightness * (1.0f + (DryTip[0] - 1.0f) * rise / 3.0f),
            brightness * (1.0f + (DryTip[1] - 1.0f) * rise / 3.0f),
            brightness * (1.0f + (DryTip[2] - 1.0f) * rise / 3.0f)};
    }
};

// Average colour and filled share of one tuft atlas layer, for the foliage map.
struct TerrainFoliageLayer
{
    std::array<float, 3> color = {0.0f, 0.0f, 0.0f};
    float fill = 0.0f;
};

// 64 world units per texel: fine enough for the uncut patches and flower clusters seen from above.
constexpr int TerrainFoliageMapSize = 1024;
// Largest optical depth the encoded foliage map holds (alpha 1).
constexpr float TerrainFoliageDepthRange = 4.0f;

// The terrain's grass colour: RGBA over the whole map (row 0 at the north edge, like the terrain weights),
// rgb = average tuft colour premultiplied by a, a = optical depth of the grass cards (card area per ground area).
// Grass instances only.
// clump: a clump instance's cards cover clumpArea(clump) times one card's area.
std::vector<float> buildTerrainFoliageMap(const TerrainDecorationPlacement &placement,
    const std::vector<TerrainFoliageLayer> &layers, const TerrainDecorationClump &clump = {});
// Card area of a clump relative to one card of the instance's size, seen from a random horizontal direction.
float terrainDecorationClumpArea(const TerrainDecorationClump &clump);
// The foliage map as RGBA8 with its full mip chain: rgb = average tuft colour (not premultiplied), a = optical depth
// / TerrainFoliageDepthRange. Each level averages the premultiplied values of the one above.
std::vector<uint8_t> encodeTerrainFoliageMap(const std::vector<float> &foliage);

std::optional<TerrainDecorationConfig> loadTerrainDecorationConfig(
    const Engine::AssetFileSystem &assets, const OutdoorMapData &map, std::string &error);
// The same from a file by its virtual path (an open-air BLV's `terrain: {grass}`, devdocs/INDOOR_OPEN_SKY.md).
std::optional<TerrainDecorationConfig> loadTerrainDecorationConfigFile(
    const Engine::AssetFileSystem &assets, const std::string &path, std::string &error);
// terrainSmoothing: the materials terrain's smoothing (0 = native triangles), so plants stand on the drawn ground.
TerrainDecorationPlacement scatterTerrainDecorations(const OutdoorMapData &map,
    const std::array<std::string, 256> &textures, const TerrainDecorationConfig &config,
    float terrainSmoothing = 0.0f);

// One triangle of a terrain surface that is not a heightmap (an open-air BLV's terrain faces), with the ground's
// smooth normal there (the slope test and the tufts' lean).
struct TerrainDecorationSurfaceTriangle
{
    std::array<std::array<float, 3>, 3> points = {};
    std::array<float, 3> normal = {0.0f, 0.0f, 1.0f};
};
// A placed decoration (outdoor maps and open-air BLVs): plants keep clear of it, and the trees (names matching the
// library's undergrowth list) get undergrowth and tree-line bushes.
struct TerrainDecorationSurfaceEntity
{
    std::string name;
    std::array<float, 3> position = {0.0f, 0.0f, 0.0f};
};

// An open-air BLV's ground (devdocs/INDOOR_OPEN_SKY.md "Terrain"), in the outdoor maps' 65 536-unit frame.
struct TerrainDecorationSurface
{
    std::vector<TerrainDecorationSurfaceTriangle> ground;
    // Every other solid face (walls, buildings, docks, rocks): plants keep clear of them and grow uncut beside them.
    std::vector<std::array<std::array<float, 3>, 3>> obstacles;
    std::vector<TerrainDecorationSurfaceEntity> entities;
    // 0-1: the terrain's grass layers.
    std::function<float(float x, float y)> density;
    // Whether the point lies under a water surface (none grows there); optional.
    std::function<bool(float x, float y, float z)> underWater;
    // Ground moisture (buildTerrainSurfaceMeadow); optional, neutral without it.
    const OutdoorMeadowField *pMeadow = nullptr;
};

// The grass of an open-air BLV: New Sorpigal's meadow over the terrain triangles where density(x, y) allows, from the
// config's first grass rule and plant library as scatterTerrainDecorations grows it on the tiles: tall patches,
// wildflowers, the meadow's moisture, verges (along obstacles and where the grass ends), undergrowth around the tree
// entities and the low bushes. No stones.
TerrainDecorationPlacement scatterTerrainDecorationsOnSurface(const TerrainDecorationSurface &surface,
    const TerrainDecorationConfig &config);
// The meadow field (OutdoorMeadow.h) of an open-air BLV's terrain: heights at the outdoor grid corners from the topmost
// ground triangle there (the nearest ground where there is none), water where underWater holds at the ground or a
// cell has no ground but water. Empty without ground.
OutdoorMeadowField buildTerrainSurfaceMeadow(const std::vector<TerrainDecorationSurfaceTriangle> &ground,
    const std::function<bool(float x, float y, float z)> &underWater);

// Tight card outline of one tuft texture (alpha, row-major, width x height): a convex polygon of
// TerrainDecorationCutoutVertices texture coordinates in order (u right, v down; the last vertex repeats when fewer
// are needed) enclosing every texel with alpha >= threshold plus a small margin, within [0, 1]. A card cut to it skips
// the transparent area that an alpha test would otherwise shade. An empty texture gives the full quad.
constexpr size_t TerrainDecorationCutoutVertices = 8;
std::array<std::array<float, 2>, TerrainDecorationCutoutVertices> terrainDecorationCutout(
    const std::vector<uint8_t> &alpha, int width, int height, uint8_t threshold);
} // namespace OpenYAMM::Game
