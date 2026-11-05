#include "game/outdoor/OutdoorTerrainMaterials.h"

#include "engine/ImageAssetLoader.h"
#include "engine/ParallelFor.h"
#include "engine/render/CookedTexture.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorLightingData.h"
#include "game/outdoor/OutdoorMeadow.h"
#include "game/render/TextureFiltering.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <bit>
#include <cmath>
#include <filesystem>
#include <functional>
#include <limits>
#include <map>
#include <tuple>
#include <stdexcept>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MapCells = OutdoorMapData::TerrainWidth;
constexpr int GridCells = OutdoorMapData::TerrainWidth - 1;
constexpr int ChunkCells = 16;
// The material set (TerrainMaterialSet) takes stages 8, 9, 10 and 14 and the light grid 11; the liquid edge coverage,
// baked lighting and sun shadow inputs keep stages 2-7.
constexpr uint8_t CellsStage = 12;
constexpr uint8_t BakedNormalsStage = 13;
constexpr uint8_t ShoreStage = 15;
constexpr const char *CausticsPath = "engine/terrain_materials/caustics.png";
// The caustics take stage 0 (the terrain draws no tile art).
constexpr uint8_t CausticsStage = 0;
// The grass decorations' far colour (TerrainDecorationRenderer::foliageMap).
constexpr uint8_t FoliageStage = 1;

struct TerrainMaterialVertex
{
    float x;
    float y;
    float z;
    float normalX;
    float normalY;
    float normalZ;
    // 1 - normal.z of the terrain smoothed over about a cell: selects cliffs without tracing native triangles.
    float steepness;
    // The meadow field (OutdoorMeadowField): -1 lush .. +1 dry.
    float meadow;
};

// Separable box blur of a square grid, clamped at its edges.
std::vector<float> boxBlurred(const std::vector<float> &values, int side, int radius)
{
    std::vector<float> result = values;
    std::vector<float> pass(values.size());
    for (int axis = 0; axis < 2; ++axis)
    {
        for (int j = 0; j < side; ++j)
        {
            for (int i = 0; i < side; ++i)
            {
                float sum = 0.0f;
                for (int offset = -radius; offset <= radius; ++offset)
                {
                    const int a = std::clamp((axis == 0 ? i : j) + offset, 0, side - 1);
                    sum += axis == 0 ? result[size_t(j) * side + a] : result[size_t(a) * side + i];
                }
                pass[size_t(j) * side + i] = sum / float(2 * radius + 1);
            }
        }
        result.swap(pass);
    }
    return result;
}

bgfx::TextureHandle createRgbaTexture(int width, int height, const std::vector<std::vector<uint8_t>> &levels)
{
    const bool mips = levels.size() > 1;
    size_t bytes = 0;
    for (const std::vector<uint8_t> &level : levels)
    {
        bytes += level.size();
    }
    const bgfx::Memory *pMemory = bgfx::alloc(uint32_t(bytes));
    size_t offset = 0;
    for (const std::vector<uint8_t> &level : levels)
    {
        std::copy(level.begin(), level.end(), pMemory->data + offset);
        offset += level.size();
    }
    return bgfx::createTexture2D(uint16_t(width), uint16_t(height), mips, 1, bgfx::TextureFormat::RGBA8,
        BGFX_TEXTURE_NONE, pMemory);
}
}

std::optional<OutdoorTerrainMaterialConfig> loadOutdoorTerrainMaterialConfig(
    const Engine::AssetFileSystem &assets, const OutdoorMapData &map, std::string &error)
{
    error.clear();
    const std::string directory = "worlds/" + map.worldId + "/terrain_materials/";
    const std::string path = directory + std::filesystem::path(map.fileName).stem().string() + ".yml";
    const std::optional<std::string> text = assets.readTextFile(path);
    if (!text)
    {
        error = "missing " + path + " (tools/terrain_materials.py weights)";
        return std::nullopt;
    }
    return parseTerrainMaterialConfig(*text, directory, path, error);
}

struct OutdoorTerrainMaterials::SourceImages
{
    TerrainMaterialSources materials;
    // Waterline distance as stored (R8); with a shore and rendered water only.
    std::vector<uint8_t> shore;
    // The two caustic webs' mip chains, layer-major.
    std::vector<std::vector<uint8_t>> causticsLevels;
    int causticsSide = 0;
    // The first failure in task order; empty when everything loaded.
    std::string error;
};

OutdoorTerrainMaterials::SourceImages OutdoorTerrainMaterials::loadSourceImages(const Engine::AssetFileSystem &assets,
    const OutdoorTerrainMaterialConfig &config, bool renderedWater)
{
    SourceImages images;
    // Each task fills its own slot; the BGRA images become RGBA (and their mip chains) on the workers too.
    std::vector<std::function<void(std::string &)>> tasks;
    if (!TerrainMaterialSet::appendLoadTasks(assets, config, images.materials, tasks, images.error))
    {
        return images;
    }
    const int size = MapCells * config.texelsPerCell;
    if (config.shore && renderedWater)
    {
        const std::string path = config.directory + config.shore->file;
        tasks.push_back([&assets, &images, path, size](std::string &error)
        {
            Engine::BinaryAssetCache cache;
            const std::optional<Engine::ImagePixelsBgra> image = Engine::loadImageAssetPixelsBgra(assets, path, cache);
            if (!image || image->width != size || image->height != size)
            {
                error = "terrain shore distance must be " + std::to_string(size) + " pixels square: " + path;
                return;
            }
            images.shore.resize(size_t(size) * size);
            for (size_t index = 0; index < images.shore.size(); ++index)
            {
                // Grayscale images decode with their intensity in red.
                images.shore[index] = image->pixels[index * 4 + 2];
            }
        });
        // The caustic webs, stacked vertically in one image: one array layer each, with their own mip chains.
        tasks.push_back([&assets, &images](std::string &error)
        {
            Engine::BinaryAssetCache cache;
            const std::optional<Engine::ImagePixelsBgra> caustics =
                Engine::loadImageAssetPixelsBgra(assets, CausticsPath, cache);
            const int side = caustics ? caustics->width : 0;
            if (!caustics || side < 1 || (side & (side - 1)) != 0 || caustics->height != side * 2)
            {
                error = std::string("caustics must be two power-of-two squares stacked vertically: ") + CausticsPath;
                return;
            }
            const size_t layerBytes = size_t(side) * side * 4;
            for (int layer = 0; layer < 2; ++layer)
            {
                std::vector<uint8_t> rgba(caustics->pixels.begin() + std::ptrdiff_t(layerBytes * layer),
                    caustics->pixels.begin() + std::ptrdiff_t(layerBytes * (layer + 1)));
                for (size_t offset = 0; offset < rgba.size(); offset += 4)
                {
                    std::swap(rgba[offset], rgba[offset + 2]);
                }
                for (std::vector<uint8_t> &level : terrainRgbaMipChain(std::move(rgba), side))
                {
                    images.causticsLevels.push_back(std::move(level));
                }
            }
            images.causticsSide = side;
        });
    }
    std::vector<std::string> errors(tasks.size());
    Engine::parallelFor(tasks.size(), [&tasks, &errors](size_t index)
    {
        try
        {
            tasks[index](errors[index]);
        }
        catch (const std::exception &exception)
        {
            errors[index] = exception.what();
        }
    });
    for (const std::string &error : errors)
    {
        if (!error.empty())
        {
            images.error = error;
            return images;
        }
    }
    TerrainMaterialSet::validateSources(images.materials, images.error);
    return images;
}

bool OutdoorTerrainMaterials::initialize(const Engine::AssetFileSystem &assets, const OutdoorMapData &map,
    const OutdoorTerrainMaterialConfig &config, const std::array<OutdoorTerrainTile, 256> &tiles,
    uint32_t subdivision, const OutdoorLightingData *pBakedLighting, bool renderedWater,
    bgfx::ProgramHandle program, bgfx::ProgramHandle shadowProgram, bgfx::ProgramHandle singleProgram,
    bgfx::ProgramHandle singleShadowProgram, std::string &error)
{
    shutdown();
    m_program = program;
    m_shadowProgram = shadowProgram;
    m_singleProgram = singleProgram;
    m_singleShadowProgram = singleShadowProgram;
    if (!bgfx::isValid(m_program) || !bgfx::isValid(m_shadowProgram) || !bgfx::isValid(m_singleProgram)
        || !bgfx::isValid(m_singleShadowProgram))
    {
        error = "terrain material programs are unavailable";
        shutdown();
        return false;
    }
    if ((bgfx::getCaps()->supported & BGFX_CAPS_TEXTURE_2D_ARRAY) == 0)
    {
        error = "terrain materials require texture array support";
        shutdown();
        return false;
    }
    if (map.heightMap.size() != size_t(MapCells * MapCells) || map.tileMap.size() != size_t(MapCells * MapCells))
    {
        error = "terrain materials require a terrain height and tile map";
        shutdown();
        return false;
    }
    m_stats = {};
    const SourceImages images = loadSourceImages(assets, config, renderedWater);
    error = images.error;
    if (!error.empty() || !m_materials.create(images.materials, config, error)
        || !createCellTextures(map, tiles) || !createBakedNormals(map, pBakedLighting)
        || !createShore(images, config, renderedWater, error)
        || !createMesh(map, tiles, config, subdivision,
            m_shoreDistance.empty() ? std::nullopt : config.shore))
    {
        if (error.empty())
        {
            error = "cannot allocate terrain material resources";
        }
        shutdown();
        return false;
    }
    m_stats.gpuBytes += m_materials.gpuBytes();
    const char *samplerNames[] = {"s_terrainCells", "s_terrainBakedNormals", "s_terrainShore"};
    for (size_t index = 0; index < m_samplers.size(); ++index)
    {
        m_samplers[index] = bgfx::createUniform(samplerNames[index], bgfx::UniformType::Sampler);
    }
    m_light = bgfx::createUniform("u_terrainMaterialLight", bgfx::UniformType::Vec4);
    m_shoreUniform = bgfx::createUniform("u_terrainShore", bgfx::UniformType::Vec4);
    m_foliageSampler = bgfx::createUniform("s_terrainFoliage", bgfx::UniformType::Sampler);
    m_foliageUniform = bgfx::createUniform("u_terrainFoliage", bgfx::UniformType::Vec4, 2);
    const std::array<uint16_t, 4> noFoliage = {};
    m_noFoliage = bgfx::createTexture2D(1, 1, false, 1, bgfx::TextureFormat::RGBA16F,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP, bgfx::copy(noFoliage.data(), sizeof(noFoliage)));
    m_smoothing = config.smoothing;
    // z: waterline distance past which the seabed is plain (detail depth on the seabed slope), w: its layer.
    m_shoreValues = {config.shore ? config.shore->range : 1.0f, seabed() ? 1.0f : 0.0f,
        config.shore ? config.shore->detailDepth / config.shore->seabedSlope : 0.0f,
        config.shore ? float(config.shore->layer) : -1.0f};
    m_shoreDistance.clear();
    m_shoreDistance.shrink_to_fit();
    m_materials.releaseWeightLayers();
    return true;
}

void OutdoorTerrainMaterials::shutdown(bool destroyResources)
{
    // Without a live renderer the handles are only forgotten.
    const auto release = [destroyResources](auto &handle)
    {
        if (destroyResources && bgfx::isValid(handle))
        {
            bgfx::destroy(handle);
        }
        handle.idx = bgfx::kInvalidHandle;
    };
    for (Chunk &chunk : m_chunks)
    {
        release(chunk.vertices);
        release(chunk.indices);
    }
    m_chunks.clear();
    m_materials.destroy(destroyResources);
    release(m_cells);
    release(m_bakedNormals);
    release(m_shore);
    release(m_caustics);
    release(m_causticsSampler);
    release(m_seabedHeights);
    m_seabedMapping = {};
    m_opaqueWaterDepth = 0.0f;
    m_waterGeometry.clear();
    m_shoreDistance.clear();
    m_shoreSize = 0;
    for (bgfx::UniformHandle &handle : m_samplers)
    {
        release(handle);
    }
    release(m_light);
    release(m_shoreUniform);
    release(m_foliageSampler);
    release(m_foliageUniform);
    release(m_noFoliage);
    release(m_program);
    release(m_shadowProgram);
    release(m_singleProgram);
    release(m_singleShadowProgram);
    m_stats = {};
    m_smoothing = 0.0f;
    m_renderedHeights.clear();
    m_renderedHeights.shrink_to_fit();
    m_renderedSide = 0;
    m_renderedSpacing = 0.0f;
}

float OutdoorTerrainMaterials::renderedHeight(float x, float y) const
{
    if (m_renderedSide < 2)
    {
        return 0.0f;
    }
    const float last = float(m_renderedSide - 1);
    const float u = std::clamp((x + 32768.0f) / m_renderedSpacing, 0.0f, last);
    const float v = std::clamp((32768.0f - y) / m_renderedSpacing, 0.0f, last);
    const int u0 = std::min(int(u), m_renderedSide - 2);
    const int v0 = std::min(int(v), m_renderedSide - 2);
    const auto at = [&](int column, int row)
    {
        return m_renderedHeights[size_t(row) * size_t(m_renderedSide) + size_t(column)];
    };
    return std::lerp(std::lerp(at(u0, v0), at(u0 + 1, v0), u - float(u0)),
        std::lerp(at(u0, v0 + 1), at(u0 + 1, v0 + 1), u - float(u0)), v - float(v0));
}

void OutdoorTerrainMaterials::bind(const OutdoorLightingData *pBakedLighting, bool directSun, bool antiTiling,
    bgfx::TextureHandle foliage, const std::array<float, 8> &foliageParams, float specularStrength) const
{
    const uint32_t clamp = BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP;
    const uint32_t point = clamp | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT;
    // Stages 8, 9, 10 and 14; stage 11 holds the light grid (light_grid.sh).
    m_materials.bind(antiTiling, specularStrength);
    bgfx::setTexture(CellsStage, m_samplers[0], m_cells, point);
    bgfx::setTexture(BakedNormalsStage, m_samplers[1], m_bakedNormals, clamp);
    bgfx::setTexture(ShoreStage, m_samplers[2], m_shore, clamp);
    if (bgfx::isValid(m_caustics))
    {
        bindTexture(CausticsStage, m_causticsSampler, m_caustics, TextureFilterProfile::Terrain);
    }
    bgfx::setUniform(m_shoreUniform, m_shoreValues.data());
    const bool grass = bgfx::isValid(foliage);
    bgfx::setTexture(FoliageStage, m_foliageSampler, grass ? foliage : m_noFoliage, clamp);
    const std::array<float, 8> noFoliageParams = {0.0f, 1.0f, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f};
    bgfx::setUniform(m_foliageUniform, grass ? foliageParams.data() : noFoliageParams.data(), 2);
    std::array<float, 4> light = {0.0f, 0.0f, 1.0f, directSun ? 1.0f : 0.0f};
    if (pBakedLighting != nullptr)
    {
        light[0] = pBakedLighting->sunDirection[0];
        light[1] = pBakedLighting->sunDirection[1];
        light[2] = pBakedLighting->sunDirection[2];
    }
    bgfx::setUniform(m_light, light.data());
}

bool OutdoorTerrainMaterials::createShore(const SourceImages &images, const OutdoorTerrainMaterialConfig &config,
    bool renderedWater, std::string &error)
{
    // Without a shore (or without rendered water) every texel reads as far inland.
    std::vector<uint8_t> encoded = {255};
    int size = 1;
    if (config.shore && renderedWater)
    {
        size = MapCells * config.texelsPerCell;
        encoded = images.shore;
        m_shoreDistance.resize(encoded.size());
        for (size_t index = 0; index < encoded.size(); ++index)
        {
            m_shoreDistance[index] = (float(encoded[index]) - 128.0f) / 127.0f * config.shore->range;
        }
        m_shoreSize = size;
        const int side = images.causticsSide;
        const std::vector<std::vector<uint8_t>> &levels = images.causticsLevels;
        size_t bytes = 0;
        for (const std::vector<uint8_t> &level : levels)
        {
            bytes += level.size();
        }
        // Layer-major: every mip of the first layer, then of the second.
        const bgfx::Memory *pMemory = bgfx::alloc(uint32_t(bytes));
        size_t offset = 0;
        for (const std::vector<uint8_t> &level : levels)
        {
            std::copy(level.begin(), level.end(), pMemory->data + offset);
            offset += level.size();
        }
        m_caustics = bgfx::createTexture2D(uint16_t(side), uint16_t(side), true, 2, bgfx::TextureFormat::RGBA8,
            BGFX_TEXTURE_NONE, pMemory);
        if (!bgfx::isValid(m_caustics))
        {
            error = "cannot allocate the terrain caustics";
            return false;
        }
        m_stats.gpuBytes += bytes;
        m_causticsSampler = bgfx::createUniform("s_terrainCaustics", bgfx::UniformType::Sampler);
    }
    m_shore = bgfx::createTexture2D(uint16_t(size), uint16_t(size), false, 1, bgfx::TextureFormat::R8,
        BGFX_TEXTURE_NONE, bgfx::copy(encoded.data(), uint32_t(encoded.size())));
    m_stats.gpuBytes += encoded.size();
    return bgfx::isValid(m_shore);
}

float OutdoorTerrainMaterials::shoreDistance(float x, float y) const
{
    const float texelsPerUnit = float(m_shoreSize) / (float(MapCells) * float(OutdoorMapData::TerrainTileSize));
    const float u = std::clamp((x + 32768.0f) * texelsPerUnit - 0.5f, 0.0f, float(m_shoreSize - 1));
    const float v = std::clamp((32768.0f - y) * texelsPerUnit - 0.5f, 0.0f, float(m_shoreSize - 1));
    const int u0 = int(u);
    const int v0 = int(v);
    const int u1 = std::min(u0 + 1, m_shoreSize - 1);
    const int v1 = std::min(v0 + 1, m_shoreSize - 1);
    const auto at = [&](int column, int row)
    {
        return m_shoreDistance[size_t(row) * m_shoreSize + column];
    };
    return std::lerp(std::lerp(at(u0, v0), at(u1, v0), u - u0), std::lerp(at(u0, v1), at(u1, v1), u - u0), v - v0);
}

bool OutdoorTerrainMaterials::createMesh(const OutdoorMapData &map,
    const std::array<OutdoorTerrainTile, 256> &tiles, const OutdoorTerrainMaterialConfig &config,
    uint32_t subdivision, const std::optional<OutdoorTerrainMaterialShore> &shore)
{
    const int steps = int(std::clamp(subdivision, 1u, 8u));
    const int side = GridCells * steps + 1;
    const float spacing = float(OutdoorMapData::TerrainTileSize) / float(steps);
    const OutdoorMeadowField meadow = buildOutdoorMeadowField(map);
    std::vector<float> heights(size_t(side) * side);
    for (int j = 0; j < side; ++j)
    {
        for (int i = 0; i < side; ++i)
        {
            heights[size_t(j) * side + i] =
                outdoorSmoothedTerrainHeight(map, float(i) / steps, float(j) / steps, config.smoothing);
        }
    }
    const auto cellTile = [&](int cellX, int cellY) -> const OutdoorTerrainTile &
    {
        return tiles[map.tileMap[size_t(cellY * MapCells + cellX)]];
    };
    // Water level at every native vertex: the native height where an open-water cell touches it, carried over the
    // land side of shore cells and spread two cells further for shores away from open water and for the beaches.
    // Sloping rivers keep their slope.
    const float noLevel = std::numeric_limits<float>::quiet_NaN();
    std::vector<float> levels(size_t(MapCells) * MapCells, noLevel);
    const auto nativeVertex = [&](int x, int y)
    {
        return float(map.heightMap[size_t(y * MapCells + x)] * OutdoorMapData::TerrainHeightScale);
    };
    const auto cornerIndex = [](int cellX, int cellY, int corner)
    {
        return size_t((cellY + corner / 2) * MapCells + cellX + corner % 2);
    };
    // The cell's water level at (u, v) inside it, bilinear between its corners; NaN away from water.
    const auto cellLevel = [&](int cellX, int cellY, float u, float v)
    {
        std::array<float, 4> corners = {};
        float lowest = noLevel;
        for (int corner = 0; corner < 4; ++corner)
        {
            corners[size_t(corner)] = levels[cornerIndex(cellX, cellY, corner)];
            if (!std::isnan(corners[size_t(corner)]) && (std::isnan(lowest) || corners[size_t(corner)] < lowest))
            {
                lowest = corners[size_t(corner)];
            }
        }
        for (float &corner : corners)
        {
            corner = std::isnan(corner) ? lowest : corner;
        }
        return std::lerp(std::lerp(corners[0], corners[1], u), std::lerp(corners[2], corners[3], u), v);
    };
    if (shore)
    {
        for (int cellY = 0; cellY < GridCells; ++cellY)
        {
            for (int cellX = 0; cellX < GridCells; ++cellX)
            {
                const OutdoorTerrainTile &tile = cellTile(cellX, cellY);
                if (tile.valid && tile.liquid == LiquidKind::Water && !tile.transitionOverlay)
                {
                    for (int corner = 0; corner < 4; ++corner)
                    {
                        levels[cornerIndex(cellX, cellY, corner)] =
                            nativeVertex(cellX + corner % 2, cellY + corner / 2);
                    }
                }
            }
        }
        for (int cellY = 0; cellY < GridCells; ++cellY)
        {
            for (int cellX = 0; cellX < GridCells; ++cellX)
            {
                const OutdoorTerrainTile &tile = cellTile(cellX, cellY);
                if (!tile.valid || tile.liquid != LiquidKind::Water || !tile.transitionOverlay)
                {
                    continue;
                }
                float lowest = noLevel;
                for (int corner = 0; corner < 4; ++corner)
                {
                    const float level = levels[cornerIndex(cellX, cellY, corner)];
                    lowest = std::isnan(lowest) || level < lowest ? level : lowest;
                }
                // Shore cells away from open water take the nearby water's level from the spreading below.
                if (std::isnan(lowest))
                {
                    continue;
                }
                for (int corner = 0; corner < 4; ++corner)
                {
                    float &level = levels[cornerIndex(cellX, cellY, corner)];
                    level = std::isnan(level) ? lowest : level;
                }
            }
        }
        for (int pass = 0; pass < 2; ++pass)
        {
            const std::vector<float> previous = levels;
            for (int y = 0; y < MapCells; ++y)
            {
                for (int x = 0; x < MapCells; ++x)
                {
                    float &level = levels[size_t(y * MapCells + x)];
                    for (int dy = -1; dy <= 1 && std::isnan(level); ++dy)
                    {
                        for (int dx = -1; dx <= 1; ++dx)
                        {
                            const float neighbour = previous[size_t(std::clamp(y + dy, 0, MapCells - 1) * MapCells
                                + std::clamp(x + dx, 0, MapCells - 1))];
                            if (!std::isnan(neighbour) && (std::isnan(level) || neighbour < level))
                            {
                                level = neighbour;
                            }
                        }
                    }
                }
            }
        }
        // The rendered surface meets the water exactly at the waterline: a gentle beach above it and a sloping
        // seabed below. Only the render changes; collision keeps the native heights.
        for (int j = 0; j < side; ++j)
        {
            for (int i = 0; i < side; ++i)
            {
                const int cellX = std::min(i / steps, GridCells - 1);
                const int cellY = std::min(j / steps, GridCells - 1);
                const float level = cellLevel(cellX, cellY, float(i - cellX * steps) / float(steps),
                    float(j - cellY * steps) / float(steps));
                if (std::isnan(level))
                {
                    continue;
                }
                const float distance = shoreDistance(float(i) * spacing - 32768.0f, 32768.0f - float(j) * spacing);
                float &height = heights[size_t(j) * side + i];
                if (distance < 0.0f)
                {
                    height = level - std::min(-distance * shore->seabedSlope, shore->seabedDepth);
                }
                // Land well below the level lies past a drop (a high lake's rim, a waterfall), not on this shore;
                // the smoothed surface stays within 32 units of the native one.
                else if (height > level - 64.0f)
                {
                    if (distance < shore->beachBlend)
                    {
                        float blend = distance / shore->beachBlend;
                        blend = blend * blend * (3.0f - 2.0f * blend);
                        // Sea cliffs stay cliffs: the beach lowers the ground by a little at most.
                        height = std::max(std::lerp(level + distance * shore->beachSlope, height, blend),
                            height - 48.0f);
                    }
                    // Land never dips under its water (the bicubic surface undershoots at cliff feet).
                    height = std::max(height, level + std::min(distance * shore->beachSlope, 4.0f));
                }
            }
        }
    }
    capRenderedTerrainUnderBModels(map, heights, side, steps);
    const auto height = [&](int i, int j)
    {
        return heights[size_t(std::clamp(j, 0, side - 1)) * side + size_t(std::clamp(i, 0, side - 1))];
    };
    // Twice blurred over a cell: a smooth, broad slope for the cliff layer.
    const std::vector<float> broad = boxBlurred(boxBlurred(heights, side, steps), side, steps);
    const auto broadHeight = [&](int i, int j)
    {
        return broad[size_t(std::clamp(j, 0, side - 1)) * side + size_t(std::clamp(i, 0, side - 1))];
    };
    const auto steepness = [&](int i, int j)
    {
        const float broadX = (broadHeight(i + steps, j) - broadHeight(i - steps, j)) / (2.0f * spacing * steps);
        const float broadY = (broadHeight(i, j - steps) - broadHeight(i, j + steps)) / (2.0f * spacing * steps);
        return 1.0f - 1.0f / std::sqrt(broadX * broadX + broadY * broadY + 1.0f);
    };
    // Whether every pixel of the land quad with grid corner (i, j) reads one ground layer only: no other layer has
    // weight in the texels its bilinear weight samples reach (with two texels more for the coarser weight mips), and
    // the cliff layer cannot blend in (the shader's macro noise raises the steepness by 0.1 at most). Such quads draw
    // with the single-material program, which samples one layer instead of two.
    const float weightTexelsPerUnit = float(m_materials.weightSize()) / 65536.0f;
    const auto weightTexels = [&](int grid)
    {
        constexpr int MipMargin = 2;
        const float first = float(grid) * spacing * weightTexelsPerUnit - 0.5f;
        const float last = float(grid + 1) * spacing * weightTexelsPerUnit - 0.5f;
        return std::pair<int, int>(std::max(int(std::floor(first)) - MipMargin, 0),
            std::min(int(std::floor(last)) + 1 + MipMargin, m_materials.weightSize() - 1));
    };
    const auto singleMaterial = [&](int i, int j)
    {
        const auto [firstX, lastX] = weightTexels(i);
        const auto [firstY, lastY] = weightTexels(j);
        uint8_t layers = 0;
        for (int y = firstY; y <= lastY; ++y)
        {
            for (int x = firstX; x <= lastX; ++x)
            {
                layers |= m_materials.weightLayers()[size_t(y) * size_t(m_materials.weightSize()) + size_t(x)];
            }
        }
        if (config.slopeLayer >= 0
            && std::max({steepness(i, j), steepness(i + 1, j), steepness(i, j + 1), steepness(i + 1, j + 1)}) + 0.1f
                > config.slopeStart)
        {
            layers |= uint8_t(1u << config.slopeLayer);
        }
        return std::popcount(layers) == 1;
    };
    // With a shore, an open-water cell's seabed is drawn where any of its vertices lies shallower than the depth at
    // which the water turns opaque. The water's opacity follows the same rendered heights, so it is already opaque
    // wherever the seabed ends.
    const auto seabedVisible = [&](int cellX, int cellY)
    {
        for (int subY = 0; subY <= steps; ++subY)
        {
            for (int subX = 0; subX <= steps; ++subX)
            {
                const float level = cellLevel(cellX, cellY, float(subX) / float(steps), float(subY) / float(steps));
                if (std::isnan(level)
                    || level - height(cellX * steps + subX, cellY * steps + subY) < shore->opaqueDepth)
                {
                    return true;
                }
            }
        }
        return false;
    };
    double deviationSum = 0.0;
    size_t deviationCount = 0;
    for (int cellY0 = 0; cellY0 < GridCells; cellY0 += ChunkCells)
    {
        for (int cellX0 = 0; cellX0 < GridCells; cellX0 += ChunkCells)
        {
            const int cellsX = std::min(ChunkCells, GridCells - cellX0);
            const int cellsY = std::min(ChunkCells, GridCells - cellY0);
            const int columns = cellsX * steps + 1;
            const int rows = cellsY * steps + 1;
            std::vector<TerrainMaterialVertex> vertices;
            vertices.reserve(size_t(columns) * rows);
            Chunk chunk;
            chunk.boundsMin = {1.0e9f, 1.0e9f, 1.0e9f};
            chunk.boundsMax = {-1.0e9f, -1.0e9f, -1.0e9f};
            for (int row = 0; row < rows; ++row)
            {
                for (int column = 0; column < columns; ++column)
                {
                    const int i = cellX0 * steps + column;
                    const int j = cellY0 * steps + row;
                    TerrainMaterialVertex vertex = {};
                    vertex.x = float(i) * spacing - 32768.0f;
                    vertex.y = 32768.0f - float(j) * spacing;
                    vertex.z = height(i, j);
                    // World y decreases with the grid row.
                    const float slopeX = (height(i + 1, j) - height(i - 1, j)) / (2.0f * spacing);
                    const float slopeY = (height(i, j - 1) - height(i, j + 1)) / (2.0f * spacing);
                    const float length = std::sqrt(slopeX * slopeX + slopeY * slopeY + 1.0f);
                    vertex.normalX = -slopeX / length;
                    vertex.normalY = -slopeY / length;
                    vertex.normalZ = 1.0f / length;
                    vertex.steepness = steepness(i, j);
                    vertex.meadow = meadow.sample(vertex.x, vertex.y);
                    chunk.boundsMin = {std::min(chunk.boundsMin.x, vertex.x), std::min(chunk.boundsMin.y, vertex.y),
                        std::min(chunk.boundsMin.z, vertex.z)};
                    chunk.boundsMax = {std::max(chunk.boundsMax.x, vertex.x), std::max(chunk.boundsMax.y, vertex.y),
                        std::max(chunk.boundsMax.z, vertex.z)};
                    vertices.push_back(vertex);
                }
            }
            std::vector<uint16_t> single;
            std::vector<uint16_t> land;
            std::vector<uint16_t> water;
            for (int cellY = cellY0; cellY < cellY0 + cellsY; ++cellY)
            {
                for (int cellX = cellX0; cellX < cellX0 + cellsX; ++cellX)
                {
                    const OutdoorTerrainTile &tile = cellTile(cellX, cellY);
                    if (!tile.valid)
                    {
                        continue;
                    }
                    // Open liquid cells (water, tar, lava) are drawn by the liquid renderer, not the land.
                    const bool openWater = tile.water && tile.waterSurface && !tile.transitionOverlay;
                    std::vector<uint16_t> &cellTarget =
                        openWater && (tile.liquid != LiquidKind::Water || !shore || !seabedVisible(cellX, cellY))
                            ? water : land;
                    for (int subY = 0; subY < steps; ++subY)
                    {
                        for (int subX = 0; subX < steps; ++subX)
                        {
                            const int column = (cellX - cellX0) * steps + subX;
                            const int row = (cellY - cellY0) * steps + subY;
                            const uint16_t topLeft = uint16_t(row * columns + column);
                            const uint16_t topRight = uint16_t(topLeft + 1);
                            const uint16_t bottomLeft = uint16_t(topLeft + columns);
                            const uint16_t bottomRight = uint16_t(bottomLeft + 1);
                            std::vector<uint16_t> &target =
                                !tile.water && singleMaterial(cellX * steps + subX, cellY * steps + subY)
                                ? single : cellTarget;
                            target.insert(target.end(),
                                {topLeft, bottomRight, topRight, topLeft, bottomLeft, bottomRight});
                            if (!tile.water)
                            {
                                const int i = cellX * steps + subX;
                                const int j = cellY * steps + subY;
                                const float deviation = std::abs(height(i, j)
                                    - outdoorNativeTerrainHeight(map, float(i) / steps, float(j) / steps));
                                m_stats.maximumDeviation = std::max(m_stats.maximumDeviation, deviation);
                                deviationSum += deviation;
                                ++deviationCount;
                            }
                        }
                    }
                }
            }
            if (single.empty() && land.empty() && water.empty())
            {
                continue;
            }
            chunk.singleIndexCount = uint32_t(single.size());
            chunk.landIndexCount = uint32_t(single.size() + land.size());
            chunk.waterIndexCount = uint32_t(water.size());
            land.insert(land.begin(), single.begin(), single.end());
            land.insert(land.end(), water.begin(), water.end());
            bgfx::VertexLayout layout;
            layout.begin()
                .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
                .add(bgfx::Attrib::Normal, 3, bgfx::AttribType::Float)
                .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
                .end();
            chunk.vertices = bgfx::createVertexBuffer(
                bgfx::copy(vertices.data(), uint32_t(vertices.size() * sizeof(TerrainMaterialVertex))), layout);
            chunk.indices = bgfx::createIndexBuffer(bgfx::copy(land.data(), uint32_t(land.size() * sizeof(uint16_t))));
            if (!bgfx::isValid(chunk.vertices) || !bgfx::isValid(chunk.indices))
            {
                if (bgfx::isValid(chunk.vertices))
                {
                    bgfx::destroy(chunk.vertices);
                }
                if (bgfx::isValid(chunk.indices))
                {
                    bgfx::destroy(chunk.indices);
                }
                return false;
            }
            m_stats.triangles += uint32_t(land.size() / 3);
            m_stats.singleTriangles += chunk.singleIndexCount / 3;
            m_stats.gpuBytes += vertices.size() * sizeof(TerrainMaterialVertex) + land.size() * sizeof(uint16_t);
            m_chunks.push_back(chunk);
        }
    }
    m_stats.subdivision = uint32_t(steps);
    m_renderedHeights = heights;
    m_renderedSide = side;
    m_renderedSpacing = spacing;
    m_stats.meanLandDeviation = deviationCount > 0 ? float(deviationSum / double(deviationCount)) : 0.0f;
    if (shore && !m_chunks.empty())
    {
        // The rendered heights for the water's depth fade, one texel per mesh vertex.
        std::vector<uint16_t> halves(heights.size());
        for (size_t index = 0; index < heights.size(); ++index)
        {
            halves[index] = bx::halfFromFloat(heights[index]);
        }
        m_seabedHeights = bgfx::createTexture2D(uint16_t(side), uint16_t(side), false, 1, bgfx::TextureFormat::R16F,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP,
            bgfx::copy(halves.data(), uint32_t(halves.size() * sizeof(uint16_t))));
        if (!bgfx::isValid(m_seabedHeights))
        {
            return false;
        }
        m_stats.gpuBytes += halves.size() * sizeof(uint16_t);
        m_seabedMapping = {-32768.0f, 32768.0f, 1.0f / (spacing * float(side)), 0.5f / float(side)};
        m_opaqueWaterDepth = shore->opaqueDepth;
        // Water at the levels over every water and shore cell (flat unless the native water slopes); the land
        // hides it above the waterline. Tar and lava keep their per-cell liquid surfaces (see OutdoorRenderer).
        std::map<float, WaterSurfaceGeometry> planes;
        WaterSurfaceGeometry sloped;
        sloped.planar = false;
        std::map<std::tuple<float, int, int>, std::array<bx::Vec3, 2>> patches;
        const float slopedKey = std::numeric_limits<float>::lowest();
        const float size = float(OutdoorMapData::TerrainTileSize);
        // Land cells whose rendered ground dips under the water (the beach follows the smooth waterline, not the
        // cell grid) take the colour of the map's water.
        uint32_t mapWaterColor = 0;
        uint8_t mapWaterTile = 0;
        for (size_t index = 0; index < map.tileMap.size() && mapWaterColor == 0; ++index)
        {
            const OutdoorTerrainTile &tile = tiles[map.tileMap[index]];
            if (tile.valid && tile.liquid == LiquidKind::Water && !tile.transitionOverlay)
            {
                mapWaterColor = tile.waterColorAbgr;
                mapWaterTile = map.tileMap[index];
            }
        }
        // Only ground inside the waterline counts: land past a drop (outside a high lake's rim) also lies under the
        // spread level, but the water cannot reach it.
        const auto submerged = [&](int cellX, int cellY)
        {
            for (int subY = 0; subY <= steps; ++subY)
            {
                for (int subX = 0; subX <= steps; ++subX)
                {
                    const int i = cellX * steps + subX;
                    const int j = cellY * steps + subY;
                    const float level = cellLevel(cellX, cellY, float(subX) / float(steps), float(subY) / float(steps));
                    if (!std::isnan(level) && height(i, j) < level
                        && shoreDistance(float(i) * spacing - 32768.0f, 32768.0f - float(j) * spacing) < 0.0f)
                    {
                        return true;
                    }
                }
            }
            return false;
        };
        for (int cellY = 0; cellY < GridCells; ++cellY)
        {
            for (int cellX = 0; cellX < GridCells; ++cellX)
            {
                uint8_t raw = map.tileMap[size_t(cellY * MapCells + cellX)];
                const OutdoorTerrainTile &tile = tiles[raw];
                const bool water = tile.liquid == LiquidKind::Water;
                if (!tile.valid || (!water && (tile.waterSurface || !submerged(cellX, cellY))))
                {
                    continue;
                }
                const uint32_t waterColor = water ? tile.waterColorAbgr : mapWaterColor;
                raw = water ? raw : mapWaterTile;
                std::array<float, 4> corners = {};
                for (int corner = 0; corner < 4; ++corner)
                {
                    corners[size_t(corner)] = cellLevel(cellX, cellY, float(corner % 2), float(corner / 2));
                }
                if (std::isnan(corners[0]))
                {
                    continue;
                }
                const bool flat = corners[1] == corners[0] && corners[2] == corners[0] && corners[3] == corners[0];
                WaterSurfaceGeometry &surface = flat ? planes[corners[0]] : sloped;
                surface.height = corners[0];
                const float west = float(cellX) * size - 32768.0f;
                const float north = 32768.0f - float(cellY) * size;
                const auto corner = [&](int index)
                {
                    const float u = float(index % 2);
                    const float v = float(index / 2);
                    return WaterVertex{west + u * size, north - v * size, corners[size_t(index)], 0.0f, 0.0f, 1.0f, u, v,
                        float(raw), 2.0f, waterColor};
                };
                surface.vertices.insert(surface.vertices.end(), {corner(0), corner(3), corner(1), corner(0), corner(2),
                    corner(3)});
                const float low = std::min({corners[0], corners[1], corners[2], corners[3]});
                const float high = std::max({corners[0], corners[1], corners[2], corners[3]});
                const auto [iterator, inserted] = patches.try_emplace(
                    std::make_tuple(flat ? corners[0] : slopedKey, cellX / ChunkCells, cellY / ChunkCells),
                    std::array<bx::Vec3, 2>{bx::Vec3{west, north - size, low}, bx::Vec3{west + size, north, high}});
                if (!inserted)
                {
                    std::array<bx::Vec3, 2> &bounds = iterator->second;
                    bounds[0] = {std::min(bounds[0].x, west), std::min(bounds[0].y, north - size),
                        std::min(bounds[0].z, low)};
                    bounds[1] = {std::max(bounds[1].x, west + size), std::max(bounds[1].y, north),
                        std::max(bounds[1].z, high)};
                }
            }
        }
        for (const auto &[key, bounds] : patches)
        {
            (std::get<0>(key) == slopedKey ? sloped : planes[std::get<0>(key)]).patches.push_back(bounds);
        }
        for (auto &[level, plane] : planes)
        {
            m_waterGeometry.push_back(std::move(plane));
        }
        if (!sloped.vertices.empty())
        {
            m_waterGeometry.push_back(std::move(sloped));
        }
    }
    return !m_chunks.empty();
}

bool OutdoorTerrainMaterials::createCellTextures(const OutdoorMapData &map,
    const std::array<OutdoorTerrainTile, 256> &tiles)
{
    std::vector<uint8_t> cells(size_t(MapCells) * MapCells * 4, 0);
    for (int cellY = 0; cellY < GridCells; ++cellY)
    {
        for (int cellX = 0; cellX < GridCells; ++cellX)
        {
            const size_t index = size_t(cellY * MapCells + cellX);
            const uint8_t raw = map.tileMap[index];
            const OutdoorTerrainTile &tile = tiles[raw];
            uint8_t *pCell = &cells[index * 4];
            pCell[0] = raw;
            pCell[1] = tile.water ? (tile.transitionOverlay ? 2 : 1) : 0;
            // Drawn by the liquid renderer: 255 water (may show a seabed), 128 an opaque liquid (tar, lava).
            pCell[2] = tile.waterSurface ? (tile.liquid == LiquidKind::Water ? 255 : 128) : 0;
            pCell[3] = tile.valid ? 255 : 0;
        }
    }
    m_cells = createRgbaTexture(MapCells, MapCells, {cells});
    m_stats.gpuBytes += cells.size();
    return bgfx::isValid(m_cells);
}

bool OutdoorTerrainMaterials::createBakedNormals(const OutdoorMapData &map, const OutdoorLightingData *pBakedLighting)
{
    if (pBakedLighting == nullptr)
    {
        m_bakedNormals = createRgbaTexture(1, 1, {std::vector<uint8_t>{128, 128, 255, 255}});
        return bgfx::isValid(m_bakedNormals);
    }
    // The native triangle normal at every terrain lightmap texel centre, as the bake lit it. Sampled with the same
    // bilinear filter as the bake, the ratio of the two stays smooth across native triangle edges.
    const OutdoorLightmapAtlasPage &page = pBakedLighting->atlasPages[pBakedLighting->terrainPageIndex];
    const std::array<float, 4> &bounds = pBakedLighting->terrainBounds;
    const int width = int(page.width);
    const int height = int(page.height);
    std::vector<uint8_t> normals(size_t(width) * height * 4, 255);
    const auto encode = [](float value)
    {
        return uint8_t(std::lround(std::clamp(value * 0.5f + 0.5f, 0.0f, 1.0f) * 255.0f));
    };
    for (int row = 0; row < height; ++row)
    {
        for (int column = 0; column < width; ++column)
        {
            const float x = bounds[0] + bounds[2] * float(column) / float(std::max(width - 1, 1));
            const float y = bounds[1] + bounds[3] * float(row) / float(std::max(height - 1, 1));
            const bx::Vec3 normal = sampleOutdoorRenderedTerrainNormal(map, x, y);
            uint8_t *pTexel = &normals[(size_t(row) * width + column) * 4];
            pTexel[0] = encode(normal.x);
            pTexel[1] = encode(normal.y);
            pTexel[2] = encode(normal.z);
        }
    }
    m_bakedNormals = createRgbaTexture(width, height, {normals});
    m_stats.gpuBytes += normals.size();
    return bgfx::isValid(m_bakedNormals);
}
} // namespace OpenYAMM::Game
