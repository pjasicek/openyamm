#pragma once

#include "core/Project.h"

#include "game/indoor/IndoorMapData.h"

#include <yaml-cpp/yaml.h>

#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Terrain for indoor maps open to the sky (S8b; devdocs/INDOOR_OPEN_SKY.md "Terrain"): atmosphere.yml `ground` turned
// into what the game's open-air BLV terrain reads: the weight image <stem>_blv_weights0.png (RGBA over the 65 536-unit
// map frame, 16 texels a 512-unit cell, a ground layer a channel), the material file <stem>_blv.yml (the format of
// tools/terrain_materials.py, parsed here by the game's own parseTerrainMaterialConfig) and the scene's `terrain`
// block. The same steps as the MM9 regions' level_generation/projects/mm9r_common/terrain_blend.py: the faces whose
// textures a layer names rasterised from above (the topmost face over a texel wins), texels no face covers given their
// nearest face's layer, each layer's field blurred by a Gaussian of `edge_softness` (scipy's gaussian_filter, mode
// nearest, truncated at four sigma), normalised and quantised; tints from a colour over the library's mean colour.

// What the build reads of the asset root.
struct GroundAssets
{
    // worlds/<world>/terrain_materials/world.yml (empty when the world has none: the project's `materials` then
    // define every material).
    std::string worldMaterialsText;
    // engine/terrain_materials/library.yml.
    std::string libraryText;
    // For the checks that the library's cooked pictures and a grass file are there; empty: not checked.
    std::filesystem::path assetRoot;
};

GroundAssets readGroundAssets(const std::filesystem::path &assetRoot, const std::string &world);

struct GroundOptions
{
    // Faces drawn as faces whatever the covered rule (the parity run: terrain_blend.py's own list).
    std::optional<std::vector<uint32_t>> excludedFaces;
    // The material file's first comment line (what wrote it).
    std::string writtenBy = "oymap build";
};

struct GroundTerrain
{
    // <stem>_blv.yml and <stem>_blv_weights0.png.
    std::string materialsFile;
    std::string weightsFile;
    std::string materialsText;
    std::vector<uint8_t> weightsPng;
    // The weight image's texels, RGBA, rows from the frame's north edge.
    int size = 0;
    std::vector<uint8_t> weights;
    // The scene's `terrain` block.
    YAML::Node sceneTerrain;
    // The material file's layers in order (the weighted first, then the slope and variant materials).
    std::vector<std::string> layers;
    size_t weightedLayers = 0;
    // Faces weighed as ground, faces with a ground texture drawn as faces, faces with no ground texture.
    size_t groundFaces = 0;
    std::vector<uint32_t> excludedFaces;
    std::vector<std::string> warnings;
};

// The map's ground from `ground` (atmosphere.yml's block) over the built map. False with `errorMessage` on what the
// game would refuse or the project contradicts (an unknown material or library, more than four layers, a texture in
// two layers, no face of any ground texture ...).
bool buildGroundTerrain(
    const YAML::Node &ground,
    const Game::IndoorMapData &map,
    const GroundAssets &assets,
    const std::string &stem,
    const GroundOptions &options,
    GroundTerrain &result,
    std::string &errorMessage);

// For buildProject: an indoor project's atmosphere.yml `ground` over its built map, or nothing when it has none.
// Issues name atmosphere.yml.
bool buildProjectGround(
    const Project &project,
    const Game::IndoorMapData &map,
    const std::filesystem::path &assetRoot,
    const std::string &stem,
    std::optional<GroundTerrain> &ground,
    std::vector<ProjectIssue> &issues);

// What buildProject refuses before it lowers: `ground` in an overlay project, `ground` beside `terrain`, `ground`
// without `open_sky`.
void checkProjectGround(const Project &project, std::vector<ProjectIssue> &issues);

// The ground's two files beside the map, or, without a ground, the old ones taken away. Adds the written names.
bool writeGroundFiles(
    const std::optional<GroundTerrain> &ground,
    const std::filesystem::path &outputDirectory,
    const std::string &stem,
    std::vector<std::string> &files,
    std::string &errorMessage);

// `oymap install`: the build's ground files into worlds/<world>/terrain_materials/ of the root or mount (an old pair
// the build no longer has is taken away). Adds the installed paths.
bool installGroundFiles(
    const std::filesystem::path &buildDirectory,
    const std::filesystem::path &assetRoot,
    const std::string &world,
    const std::string &stem,
    std::vector<std::string> &installedFiles,
    std::string &errorMessage);

// The steps, for tests and the parity run.
namespace GroundSteps
{
// Per texel the layer of the topmost face over it (-1: none) and its height there; faces are (polygon, layer).
void rasteriseTopmost(
    const std::vector<std::pair<std::vector<std::array<double, 3>>, int>> &faces,
    int size,
    std::vector<int16_t> &layerMap,
    std::vector<double> &heights);
// Texels of -1 take the layer of the nearest texel with one (scipy's distance_transform_edt feature transform).
void fillNearest(std::vector<int16_t> &layerMap, int size);
// scipy.ndimage.gaussian_filter of a float32 field (mode nearest, truncate 4).
void gaussianBlur(std::vector<float> &field, int size, double sigma);
}
}
