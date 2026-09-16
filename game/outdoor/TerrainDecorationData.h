#pragma once

#include "engine/AssetFileSystem.h"
#include "game/outdoor/OutdoorMapData.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
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
};

struct TerrainDecorationConfig
{
    uint32_t seed = 1;
    float distance = 2048.0f;
    float minimumNormalZ = 0.85f;
    float densityVariation = 0.0f;
    float patchSize = 768.0f;
    float tallGrassChance = 0.0f;
    float tallGrassScale = 1.8f;
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
    std::array<float, 4> sizeWindKind;
    std::array<float, 4> color;
    std::array<float, 4> groundNormal; // xyz = surface normal; w = tuft texture layer.
};

struct TerrainDecorationPatch
{
    uint32_t first = 0;
    uint32_t count = 0;
    bool stone = false;
    std::array<float, 3> min;
    std::array<float, 3> max;
};

struct TerrainDecorationPlacement
{
    std::vector<TerrainDecorationInstance> instances;
    std::vector<TerrainDecorationPatch> patches;
};

std::optional<TerrainDecorationConfig> loadTerrainDecorationConfig(
    const Engine::AssetFileSystem &assets, const OutdoorMapData &map, std::string &error);
TerrainDecorationPlacement scatterTerrainDecorations(
    const OutdoorMapData &map, const std::array<std::string, 256> &textures, const TerrainDecorationConfig &config);
} // namespace OpenYAMM::Game
