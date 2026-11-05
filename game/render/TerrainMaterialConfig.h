#pragma once

#include <array>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// A terrain material file (worlds/<world>/terrain_materials/<name>.yml, tools/terrain_materials.py weights): the
// outdoor terrain's (OutdoorTerrainMaterials) and an open-air BLV's terrain faces' (IndoorTerrainMaterials).

// One material of a map's terrain: a library material with the world's tint and scale.
struct OutdoorTerrainMaterialLayer
{
    std::string name;
    std::string library;
    std::array<float, 3> tint = {1.0f, 1.0f, 1.0f};
    float repeat = 512.0f;
    float heightContrast = 0.35f;
    float normalStrength = 1.0f;
    // How much the material height darkens the albedo (0 none, 1 full).
    float cavity = 0.0f;
    // Tint of the slope layer where this layer is the dominant ground.
    std::array<float, 3> cliffTint = {1.0f, 1.0f, 1.0f};
    // Macro variation: broad brightness change and the tint of large cloudy patches (e.g. dry grass).
    float macroBrightness = 0.15f;
    std::array<float, 3> macroTint = {1.0f, 1.0f, 1.0f};
    // Layer of the material mixed into this one in macro-noise patches (-1: itself, rotated) and its coverage.
    int variant = -1;
    float variantAmount = 0.5f;
    // Scale of the edge fringe noise where this layer meets another (roads keep a clean edge).
    float fringe = 1.0f;
    // The library material holds standing water in its smoothest texels (swamp pools).
    bool pools = false;
    // How strongly the meadow field (OutdoorMeadow.h) tints this layer towards the config's dry and lush colours.
    float meadow = 0.0f;
};

// Shallow water at the coasts: the map's waterline distance image and how the rendered terrain meets the water.
struct OutdoorTerrainMaterialShore
{
    std::string file;
    // Encoding range of the distance image: 128 + distance / range * 127, positive on land.
    float range = 1024.0f;
    // The rendered terrain rises beachSlope per unit inland, blending into the native heights over beachBlend units,
    // and falls seabedSlope per unit under the water down to seabedDepth. Collision keeps the native heights.
    float beachSlope = 0.3f;
    float beachBlend = 192.0f;
    float seabedSlope = 0.5f;
    float seabedDepth = 160.0f;
    // The water turns opaque at opaqueDepth (fs_water.sc), so only the seabed shallower than that is drawn; below
    // detailDepth it is one plain sample of the shore material (layer).
    float opaqueDepth = 72.0f;
    float detailDepth = 24.0f;
    int layer = -1;
};

// worlds/<world>/terrain_materials/<map>.yml, written by tools/terrain_materials.py weights.
struct OutdoorTerrainMaterialConfig
{
    static constexpr size_t MaxLayers = 8;

    std::string directory;
    int texelsPerCell = 16;
    std::vector<std::string> weightFiles;
    // The first weightedLayers layers have a weight channel; further layers are the slope and variant materials.
    int weightedLayers = 0;
    std::vector<OutdoorTerrainMaterialLayer> layers;
    int slopeLayer = -1;
    float slopeStart = 0.3f;
    float slopeEnd = 0.5f;
    // 0 keeps the native flat triangles, 1 renders the full bicubic surface through the native heights.
    float smoothing = 1.0f;
    // Noise that frays transitions between ground layers into islands and holes: strength, and the world size of
    // one repeat of the noise texture used for it (smaller gives finer clumps).
    float fringeStrength = 0.0f;
    float fringeScale = 2048.0f;
    // Colour multipliers of the driest and lushest ground (OutdoorMeadowField), for layers with a meadow strength.
    std::array<float, 3> meadowDry = {1.0f, 1.0f, 1.0f};
    std::array<float, 3> meadowLush = {1.0f, 1.0f, 1.0f};
    std::optional<OutdoorTerrainMaterialShore> shore;
};

// Parses a material file's text; path names it in errors, directory is where its images are.
std::optional<OutdoorTerrainMaterialConfig> parseTerrainMaterialConfig(
    const std::string &text, const std::string &directory, const std::string &path, std::string &error);
} // namespace OpenYAMM::Game
