#pragma once

#include "engine/AssetFileSystem.h"
#include "game/maps/OutdoorTerrainTiles.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/render/LiquidKind.h"
#include "game/render/TerrainMaterialConfig.h"
#include "game/render/TerrainMaterialSet.h"
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

// The map's material file (worlds/<world>/terrain_materials/<map>.yml); every map with terrain has one.
std::optional<OutdoorTerrainMaterialConfig> loadOutdoorTerrainMaterialConfig(
    const Engine::AssetFileSystem &assets, const OutdoorMapData &map, std::string &error);

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
    // (SINGLE_MATERIAL), each without and with mesh sun shadows, and the optional depth pre-pass (TERRAIN_DEPTH_ONLY;
    // invalid: none). renderedWater: the water renderer draws the terrain water, so a map with a shore gets a seabed
    // and depth-faded water planes.
    bool initialize(const Engine::AssetFileSystem &assets, const OutdoorMapData &map,
        const OutdoorTerrainMaterialConfig &config, const std::array<OutdoorTerrainTile, 256> &tiles,
        uint32_t subdivision, const OutdoorLightingData *pBakedLighting, bool renderedWater,
        bgfx::ProgramHandle program, bgfx::ProgramHandle shadowProgram, bgfx::ProgramHandle singleProgram,
        bgfx::ProgramHandle singleShadowProgram, bgfx::ProgramHandle depthProgram, std::string &error);
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
    bgfx::ProgramHandle depthProgram() const
    {
        return m_depthProgram;
    }
    // Binds stages 8-15 and the material uniforms, and with a seabed the caustics at stage 0. directSun: the bake's
    // direct-only sun page is bound at stage 5. foliage (stage 1): the grass decorations' colour with its
    // u_terrainFoliage values (TerrainDecorationRenderer::foliageMap/foliageParams); invalid when no grass is drawn.
    // specularStrength: the restrained sun and point-light highlight on smooth and wet ground (0: none).
    void bind(const OutdoorLightingData *pBakedLighting, bool directSun, bool antiTiling,
        bgfx::TextureHandle foliage, const std::array<float, 8> &foliageParams, float specularStrength) const;
    // Binds what the depth pre-pass reads to leave out the cut pixels: the cells and the shore with its uniform (the
    // liquid edge coverage at stage 4 is the water renderer's).
    void bindDepth() const;

private:
    // The material layers and images, read and decoded on the load workers before any GPU resource is created.
    struct SourceImages;
    static SourceImages loadSourceImages(const Engine::AssetFileSystem &assets,
        const OutdoorTerrainMaterialConfig &config, bool renderedWater);
    bool createMesh(const OutdoorMapData &map, const std::array<OutdoorTerrainTile, 256> &tiles,
        const OutdoorTerrainMaterialConfig &config, uint32_t subdivision,
        const std::optional<OutdoorTerrainMaterialShore> &shore);
    bool createShore(const SourceImages &images, const OutdoorTerrainMaterialConfig &config, bool renderedWater,
        std::string &error);
    float shoreDistance(float x, float y) const;
    bool createCellTextures(const OutdoorMapData &map, const std::array<OutdoorTerrainTile, 256> &tiles);
    bool createBakedNormals(const OutdoorMapData &map, const OutdoorLightingData *pBakedLighting);

    std::vector<Chunk> m_chunks;
    Stats m_stats;
    float m_smoothing = 0.0f;
    // The mesh vertices' heights, side x side rows from the map's north-west corner, spacing apart.
    std::vector<float> m_renderedHeights;
    int m_renderedSide = 0;
    float m_renderedSpacing = 0.0f;
    // The library layers, their weights and the macro noise with the layer uniforms.
    TerrainMaterialSet m_materials;
    bgfx::TextureHandle m_cells = BGFX_INVALID_HANDLE;
    // Native triangle normals at the terrain lightmap texels (1x1 up without a bake).
    bgfx::TextureHandle m_bakedNormals = BGFX_INVALID_HANDLE;
    // Waterline distance (R8, as stored) for the wet beach and caustics; 1x1 "far inland" without a shore.
    bgfx::TextureHandle m_shore = BGFX_INVALID_HANDLE;
    // Two tileable caustic webs (main and faint finer one) as array layers, with a seabed only.
    bgfx::TextureHandle m_caustics = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_causticsSampler = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_seabedHeights = BGFX_INVALID_HANDLE;
    std::array<float, 4> m_seabedMapping = {};
    float m_opaqueWaterDepth = 0.0f;
    std::vector<WaterSurfaceGeometry> m_waterGeometry;
    // Decoded waterline distance in world units while the mesh is built.
    std::vector<float> m_shoreDistance;
    int m_shoreSize = 0;
    // Cells, baked normals and shore.
    std::array<bgfx::UniformHandle, 3> m_samplers = {{BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE}};
    bgfx::UniformHandle m_light = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_shoreUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_foliageSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_foliageUniform = BGFX_INVALID_HANDLE;
    // Bound at the foliage stage when no grass is drawn (1x1, no coverage).
    bgfx::TextureHandle m_noFoliage = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_program = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_shadowProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_singleProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_singleShadowProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_depthProgram = BGFX_INVALID_HANDLE;
    std::array<float, 4> m_shoreValues = {};
};
} // namespace OpenYAMM::Game
