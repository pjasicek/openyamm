#pragma once

#include "engine/AssetFileSystem.h"
#include "game/outdoor/OutdoorTerrainMaterialConfig.h"
#include "game/maps/OutdoorTerrainTiles.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/render/LiquidKind.h"
#include "game/render/WaterRenderer.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorLightingData;

// The outdoor terrain: a subdivided smooth terrain mesh shaded from blended ground materials.
class OutdoorTerrainMaterials
{
public:
    struct Chunk
    {
        bgfx::VertexBufferHandle vertices = BGFX_INVALID_HANDLE;
        bgfx::IndexBufferHandle indices = BGFX_INVALID_HANDLE;
        // Land, shore and lava cells first, then cells of open water (drawn only without the water renderer; with a
        // shore, only those whose seabed lies entirely below the opaque water). The land starts with the triangles
        // whose pixels read one material only, drawn with the single-material program.
        uint32_t singleIndexCount = 0;
        uint32_t landIndexCount = 0;
        uint32_t waterIndexCount = 0;
        bx::Vec3 boundsMin = {0.0f, 0.0f, 0.0f};
        bx::Vec3 boundsMax = {0.0f, 0.0f, 0.0f};
    };

    struct Stats
    {
        uint32_t subdivision = 0;
        uint32_t triangles = 0;
        // Drawn with the single-material program.
        uint32_t singleTriangles = 0;
        float maximumDeviation = 0.0f;
        float meanLandDeviation = 0.0f;
        size_t gpuBytes = 0;
    };

    // Takes ownership of all programs, including on initialization failure: blended and single-material
    // (SINGLE_MATERIAL), each without and with mesh sun shadows. renderedWater: the water renderer draws the terrain
    // water, so a map with a shore gets a seabed and depth-faded water planes.
    bool initialize(const Engine::AssetFileSystem &assets, const OutdoorMapData &map,
        const OutdoorTerrainMaterialConfig &config, const std::array<OutdoorTerrainTile, 256> &tiles,
        uint32_t subdivision, const OutdoorLightingData *pBakedLighting, bool renderedWater,
        bgfx::ProgramHandle program, bgfx::ProgramHandle shadowProgram, bgfx::ProgramHandle singleProgram,
        bgfx::ProgramHandle singleShadowProgram, std::string &error);
    void shutdown(bool destroyResources = true);
    bool ready() const
    {
        return !m_chunks.empty();
    }
    const std::vector<Chunk> &chunks() const
    {
        return m_chunks;
    }
    const Stats &stats() const
    {
        return m_stats;
    }
    float smoothing() const
    {
        return m_smoothing;
    }
    // The drawn terrain's height at a world position (the smoothed surface with its beach and seabed), interpolated
    // between mesh vertices; for things resting on the visible ground.
    float renderedHeight(float x, float y) const;
    bool seabed() const
    {
        return bgfx::isValid(m_seabedHeights);
    }
    // With a seabed: the terrain water as flat planes at each water level, faded by the depth to the seabed.
    const std::vector<WaterSurfaceGeometry> &waterGeometry() const
    {
        return m_waterGeometry;
    }
    // Rendered terrain heights (R16F, one texel per mesh vertex) and the water shader's world-to-texture mapping.
    bgfx::TextureHandle seabedHeights() const
    {
        return m_seabedHeights;
    }
    const std::array<float, 4> &seabedMapping() const
    {
        return m_seabedMapping;
    }
    float opaqueWaterDepth() const
    {
        return m_opaqueWaterDepth;
    }
    bgfx::ProgramHandle program(bool sunShadows, bool singleMaterial) const
    {
        if (singleMaterial)
        {
            return sunShadows ? m_singleShadowProgram : m_singleProgram;
        }
        return sunShadows ? m_shadowProgram : m_program;
    }
    // Binds stages 8-15 and the material uniforms, and with a seabed the caustics at stage 0. directSun: the bake's
    // direct-only sun page is bound at stage 5. foliage (stage 1): the grass decorations' colour with its
    // u_terrainFoliage values (TerrainDecorationRenderer::foliageMap/foliageParams); invalid when no grass is drawn.
    // specularStrength: the restrained sun and point-light highlight on smooth and wet ground (0: none).
    void bind(const OutdoorLightingData *pBakedLighting, bool directSun, bool antiTiling,
        bgfx::TextureHandle foliage, const std::array<float, 8> &foliageParams, float specularStrength) const;

private:
    // The material layers and images, read and decoded on the load workers before any GPU resource is created.
    struct SourceImages;
    static SourceImages loadSourceImages(const Engine::AssetFileSystem &assets, const OutdoorMapData &map,
        const OutdoorTerrainMaterialConfig &config, bool renderedWater);
    bool createMesh(const OutdoorMapData &map, const std::array<OutdoorTerrainTile, 256> &tiles,
        const OutdoorTerrainMaterialConfig &config, uint32_t subdivision,
        const std::optional<OutdoorTerrainMaterialShore> &shore);
    bool createShore(const SourceImages &images, const OutdoorTerrainMaterialConfig &config, bool renderedWater,
        std::string &error);
    bool createCellTextures(const OutdoorMapData &map, const std::array<OutdoorTerrainTile, 256> &tiles);
    bool createBakedNormals(const OutdoorMapData &map, const OutdoorLightingData *pBakedLighting);
    bool createMaterialArrays(const SourceImages &images, std::string &error);
    bool createWeights(const SourceImages &images, const OutdoorTerrainMaterialConfig &config, std::string &error);

    std::vector<Chunk> m_chunks;
    Stats m_stats;
    float m_smoothing = 0.0f;
    // The mesh vertices' heights, side x side rows from the map's north-west corner, spacing apart.
    std::vector<float> m_renderedHeights;
    int m_renderedSide = 0;
    float m_renderedSpacing = 0.0f;
    bgfx::TextureHandle m_albedoHeight = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_normalAoRough = BGFX_INVALID_HANDLE;
    // Ground layer weights: array layer 0 holds layers 0-3, array layer 1 layers 4-7.
    bgfx::TextureHandle m_weights = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_cells = BGFX_INVALID_HANDLE;
    // Native triangle normals at the terrain lightmap texels (1x1 up without a bake).
    bgfx::TextureHandle m_bakedNormals = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_macro = BGFX_INVALID_HANDLE;
    // Waterline distance (R8, as stored) for the wet beach and caustics; 1x1 "far inland" without a shore.
    bgfx::TextureHandle m_shore = BGFX_INVALID_HANDLE;
    // Two tileable caustic webs (main and faint finer one) as array layers, with a seabed only.
    bgfx::TextureHandle m_caustics = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_causticsSampler = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_seabedHeights = BGFX_INVALID_HANDLE;
    std::array<float, 4> m_seabedMapping = {};
    float m_opaqueWaterDepth = 0.0f;
    std::vector<WaterSurfaceGeometry> m_waterGeometry;
    // While the mesh is built: per weight texel, a bit for every ground layer with weight there.
    std::vector<uint8_t> m_weightLayers;
    int m_weightSize = 0;
    std::array<bgfx::UniformHandle, 7> m_samplers = {{BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE,
        BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE}};
    bgfx::UniformHandle m_layerParams = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_layerTints = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_layerCliffTints = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_layerMacro = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_layerVariants = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_control = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_light = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_misc = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_meadow = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_shoreUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_foliageSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_foliageUniform = BGFX_INVALID_HANDLE;
    // Bound at the foliage stage when no grass is drawn (1x1, no coverage).
    bgfx::TextureHandle m_noFoliage = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_program = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_shadowProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_singleProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_singleShadowProgram = BGFX_INVALID_HANDLE;
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerParamValues = {};
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerTintValues = {};
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerCliffValues = {};
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerMacroValues = {};
    std::array<std::array<float, 4>, OutdoorTerrainMaterialConfig::MaxLayers> m_layerVariantValues = {};
    std::array<float, 4> m_controlValues = {};
    std::array<float, 4> m_miscValues = {};
    std::array<std::array<float, 4>, 2> m_meadowValues = {};
    std::array<float, 4> m_shoreValues = {};
};
} // namespace OpenYAMM::Game
