#pragma once

#include "engine/AssetFileSystem.h"
#include "engine/render/CookedTexture.h"
#include "game/render/TerrainMaterialConfig.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The decoded inputs of a terrain material set, filled by its load tasks on the load workers.
struct TerrainMaterialSources
{
    // albedo_height and normal_ao_rough: one cooked layer per configured material, in configuration order.
    std::array<std::vector<Engine::CookedTexture>, 2> materialLayers;
    // RGBA mip chains, one per configured weight file.
    std::array<std::vector<std::vector<uint8_t>>, 2> weightLevels;
    std::vector<std::vector<uint8_t>> macroLevels;
    int macroSize = 0;
    // Per configured material: the library's ground highlight strength (0: none) and rain-wet sheen share (1: full).
    std::vector<float> layerSpecular;
    std::vector<float> layerWetSheen;
    // Per configured material: the library's emissive glow (rgb, 0: none) and its start (w); see library.yml.
    std::vector<std::array<float, 4>> layerEmissive;
};

// RGBA8 mip chain of a square image by 2x2 averaging.
std::vector<std::vector<uint8_t>> terrainRgbaMipChain(std::vector<uint8_t> pixels, int size);

// Blended ground materials on the GPU (terrain_material_layers.sh): the library layers of a material file in two
// texture arrays (stages 8 and 9), its layer weights over the 65 536-unit map frame (stage 10), the macro variation
// noise (stage 14) and the per-layer uniforms. The outdoor terrain (OutdoorTerrainMaterials) and the terrain faces of
// open-air BLVs (IndoorRenderer) draw with it.
class TerrainMaterialSet
{
public:
    static constexpr uint8_t AlbedoHeightStage = 8;
    static constexpr uint8_t NormalAoRoughStage = 9;
    static constexpr uint8_t WeightsStage = 10;
    static constexpr uint8_t MacroStage = 14;

    // Appends the tasks that decode the config's library layers, weight images and macro noise into sources (run
    // them on the load workers, each with its own error string); false with error when the library is unreadable.
    static bool appendLoadTasks(const Engine::AssetFileSystem &assets, const OutdoorTerrainMaterialConfig &config,
        TerrainMaterialSources &sources, std::vector<std::function<void(std::string &)>> &tasks, std::string &error);
    // After the tasks: the library layers of one set must share codec and size.
    static bool validateSources(const TerrainMaterialSources &sources, std::string &error);

    bool create(const TerrainMaterialSources &sources, const OutdoorTerrainMaterialConfig &config,
        std::string &error);
    // Without a live renderer the handles are only forgotten.
    void destroy(bool destroyResources = true);
    bool ready() const
    {
        return bgfx::isValid(m_albedoHeight);
    }
    // Binds stages 8, 9, 10 and 14 and the layer uniforms. antiTiling: the second, rotated projection of every layer;
    // specularStrength: the ground highlight (0: none).
    void bind(bool antiTiling, float specularStrength) const;

    // Per weight texel (side weightSize(), rows from the map's north-west corner), a bit for every ground layer with
    // weight there; kept until releaseWeightLayers.
    const std::vector<uint8_t> &weightLayers() const
    {
        return m_weightLayers;
    }
    int weightSize() const
    {
        return m_weightSize;
    }
    void releaseWeightLayers();
    size_t gpuBytes() const
    {
        return m_gpuBytes;
    }

private:
    bool createMaterialArrays(const TerrainMaterialSources &sources, std::string &error);
    bool createWeights(const TerrainMaterialSources &sources, const OutdoorTerrainMaterialConfig &config,
        std::string &error);

    bgfx::TextureHandle m_albedoHeight = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_normalAoRough = BGFX_INVALID_HANDLE;
    // Ground layer weights: array layer 0 holds layers 0-3, array layer 1 layers 4-7.
    bgfx::TextureHandle m_weights = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_macro = BGFX_INVALID_HANDLE;
    std::array<bgfx::UniformHandle, 4> m_samplers = {{BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE,
        BGFX_INVALID_HANDLE}};
    bgfx::UniformHandle m_layerParams = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_layerTints = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_layerCliffTints = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_layerMacro = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_layerVariants = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_layerEmissive = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_control = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_misc = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_meadow = BGFX_INVALID_HANDLE;
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerParamValues = {};
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerTintValues = {};
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerCliffValues = {};
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerMacroValues = {};
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerVariantValues = {};
    // Per layer: rgb = glow colour of the material's emissive texels (0: none), w = where the glow starts.
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerEmissiveValues = {};
    std::array<float, 4> m_controlValues = {};
    std::array<float, 4> m_miscValues = {};
    std::array<std::array<float, 4>, 2> m_meadowValues = {};
    std::vector<uint8_t> m_weightLayers;
    int m_weightSize = 0;
    size_t m_gpuBytes = 0;
};
} // namespace OpenYAMM::Game
