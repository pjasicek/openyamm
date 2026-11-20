#include "game/render/TerrainMaterialSet.h"

#include "engine/ImageAssetLoader.h"
#include "game/render/TextureFiltering.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *LibraryPath = "engine/terrain_materials/library.yml";
constexpr const char *MacroVariationPath = "engine/terrain_materials/macro_variation.png";
// The weight images cover the 65 536-unit map frame: texels_per_cell texels for each of its 128 cells.
constexpr int MapCells = 128;

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

// A square RGBA image asset and its mip chain; empty with error when it is missing or fails valid.
std::vector<std::vector<uint8_t>> loadRgbaMips(const Engine::AssetFileSystem &assets, const std::string &path,
    std::string &error, const std::function<bool(const Engine::ImagePixelsBgra &)> &valid,
    const std::string &invalid, int *pWidth)
{
    Engine::BinaryAssetCache cache;
    const std::optional<Engine::ImagePixelsBgra> image = Engine::loadImageAssetPixelsBgra(assets, path, cache);
    if (!image || !valid(*image))
    {
        error = invalid + path;
        return {};
    }
    std::vector<uint8_t> rgba = image->pixels;
    for (size_t offset = 0; offset < rgba.size(); offset += 4)
    {
        std::swap(rgba[offset], rgba[offset + 2]);
    }
    if (pWidth != nullptr)
    {
        *pWidth = image->width;
    }
    return terrainRgbaMipChain(std::move(rgba), image->width);
}
}

std::vector<std::vector<uint8_t>> terrainRgbaMipChain(std::vector<uint8_t> pixels, int size)
{
    std::vector<std::vector<uint8_t>> levels;
    levels.push_back(std::move(pixels));
    while (size > 1)
    {
        const int next = size / 2;
        const std::vector<uint8_t> &source = levels.back();
        std::vector<uint8_t> level(size_t(next) * next * 4);
        for (int y = 0; y < next; ++y)
        {
            for (int x = 0; x < next; ++x)
            {
                for (int channel = 0; channel < 4; ++channel)
                {
                    const auto at = [&](int dx, int dy)
                    {
                        return int(source[(size_t(y * 2 + dy) * size + x * 2 + dx) * 4 + channel]);
                    };
                    level[(size_t(y) * next + x) * 4 + channel] =
                        uint8_t((at(0, 0) + at(1, 0) + at(0, 1) + at(1, 1) + 2) / 4);
                }
            }
        }
        levels.push_back(std::move(level));
        size = next;
    }
    return levels;
}

bool TerrainMaterialSet::appendLoadTasks(const Engine::AssetFileSystem &assets,
    const OutdoorTerrainMaterialConfig &config, TerrainMaterialSources &sources,
    std::vector<std::function<void(std::string &)>> &tasks, std::string &error)
{
    const std::optional<std::string> libraryText = assets.readTextFile(LibraryPath);
    if (!libraryText)
    {
        error = std::string("missing ") + LibraryPath;
        return false;
    }
    // Each task fills its own slot; the BGRA images become RGBA (and their mip chains) on the workers too.
    try
    {
        const YAML::Node library = YAML::Load(*libraryText)["materials"];
        sources.layerSpecular.assign(config.layers.size(), 0.0f);
        sources.layerWetSheen.assign(config.layers.size(), 1.0f);
        sources.layerEmissive.assign(config.layers.size(), {0.0f, 0.0f, 0.0f, 0.0f});
        for (size_t layer = 0; layer < config.layers.size(); ++layer)
        {
            const YAML::Node entry = library[config.layers[layer].library];
            if (entry.IsMap() && entry["specular"])
            {
                sources.layerSpecular[layer] = std::clamp(entry["specular"].as<float>(), 0.0f, 1.0f);
            }
            if (entry.IsMap() && entry["wet_sheen"])
            {
                sources.layerWetSheen[layer] = std::clamp(entry["wet_sheen"].as<float>(), 0.0f, 1.0f);
            }
            if (entry.IsMap() && entry["emissive"])
            {
                // emissive: {color: [r, g, b], threshold: t}: texels whose albedo is warmer (red minus blue) than
                // t glow in color times their albedo, whatever the light (lava veins, embers).
                const YAML::Node emissive = entry["emissive"];
                const std::array<float, 3> color = emissive["color"].as<std::array<float, 3>>();
                const float threshold = emissive["threshold"].as<float>(0.1f);
                for (float value : color)
                {
                    if (!std::isfinite(value) || value < 0.0f || value > 16.0f)
                    {
                        throw std::runtime_error("invalid terrain material emissive color");
                    }
                }
                if (!std::isfinite(threshold) || threshold < -1.0f || threshold > 1.0f)
                {
                    throw std::runtime_error("invalid terrain material emissive threshold");
                }
                sources.layerEmissive[layer] = {color[0], color[1], color[2], threshold};
            }
        }
        const std::array<const char *, 2> kinds = {"albedo_height", "normal_ao_rough"};
        for (size_t kind = 0; kind < kinds.size(); ++kind)
        {
            sources.materialLayers[kind].resize(config.layers.size());
            for (size_t layer = 0; layer < config.layers.size(); ++layer)
            {
                const YAML::Node entry = library[config.layers[layer].library];
                if (!entry.IsMap())
                {
                    error = "unknown terrain material " + config.layers[layer].library;
                    return false;
                }
                const std::string path = "engine/terrain_materials/" + entry[kinds[kind]].as<std::string>();
                tasks.push_back([&assets, &sources, kind, layer, path](std::string &taskError)
                {
                    const std::optional<std::vector<uint8_t>> bytes = assets.readBinaryFile(path);
                    if (!bytes)
                    {
                        taskError = "missing " + path;
                        return;
                    }
                    sources.materialLayers[kind][layer] = Engine::decodeCookedTexture(*bytes);
                });
            }
        }
    }
    catch (const std::exception &exception)
    {
        error = exception.what();
        return false;
    }
    const int size = MapCells * config.texelsPerCell;
    for (size_t index = 0; index < std::min(config.weightFiles.size(), sources.weightLevels.size()); ++index)
    {
        const std::string path = config.directory + config.weightFiles[index];
        tasks.push_back([&assets, &sources, index, path, size](std::string &taskError)
        {
            sources.weightLevels[index] = loadRgbaMips(assets, path, taskError,
                [size](const Engine::ImagePixelsBgra &image)
                {
                    return image.width == size && image.height == size;
                },
                "terrain material weights must be " + std::to_string(size) + " pixels square: ", nullptr);
        });
    }
    tasks.push_back([&assets, &sources](std::string &taskError)
    {
        sources.macroLevels = loadRgbaMips(assets, MacroVariationPath, taskError,
            [](const Engine::ImagePixelsBgra &image)
            {
                return image.width == image.height && image.width >= 1 && (image.width & (image.width - 1)) == 0;
            },
            "missing or non-square macro variation texture: ", &sources.macroSize);
    });
    return true;
}

bool TerrainMaterialSet::validateSources(const TerrainMaterialSources &sources, std::string &error)
{
    for (const std::vector<Engine::CookedTexture> &layers : sources.materialLayers)
    {
        for (const Engine::CookedTexture &layer : layers)
        {
            const Engine::CookedTexture &first = layers.front();
            if (layer.codec != first.codec || layer.width != first.width || layer.height != first.height
                || layer.levels != first.levels)
            {
                error = "terrain materials of one map must share codec and size";
                return false;
            }
        }
    }
    return true;
}

bool TerrainMaterialSet::create(const TerrainMaterialSources &sources, const OutdoorTerrainMaterialConfig &config,
    std::string &error)
{
    destroy();
    if (!createMaterialArrays(sources, error) || !createWeights(sources, config, error))
    {
        destroy();
        return false;
    }
    const char *samplerNames[] = {"s_terrainAlbedoHeight", "s_terrainNormalAoRough", "s_terrainWeights",
        "s_terrainMacro"};
    for (size_t index = 0; index < m_samplers.size(); ++index)
    {
        m_samplers[index] = bgfx::createUniform(samplerNames[index], bgfx::UniformType::Sampler);
    }
    const uint16_t layerCount = uint16_t(OutdoorTerrainMaterialConfig::MaxLayers);
    m_layerParams = bgfx::createUniform("u_terrainLayerParams", bgfx::UniformType::Vec4, layerCount);
    m_layerTints = bgfx::createUniform("u_terrainLayerTint", bgfx::UniformType::Vec4, layerCount);
    m_layerCliffTints = bgfx::createUniform("u_terrainLayerCliff", bgfx::UniformType::Vec4, layerCount);
    m_layerMacro = bgfx::createUniform("u_terrainLayerMacro", bgfx::UniformType::Vec4, layerCount);
    m_layerVariants = bgfx::createUniform("u_terrainLayerVariant", bgfx::UniformType::Vec4, layerCount);
    m_layerEmissive = bgfx::createUniform("u_terrainLayerEmissive", bgfx::UniformType::Vec4, layerCount);
    m_control = bgfx::createUniform("u_terrainMaterialControl", bgfx::UniformType::Vec4);
    m_misc = bgfx::createUniform("u_terrainMaterialMisc", bgfx::UniformType::Vec4);
    m_meadow = bgfx::createUniform("u_terrainMeadow", bgfx::UniformType::Vec4, 2);
    m_layerParamValues = {};
    m_layerTintValues = {};
    m_layerCliffValues = {};
    m_layerMacroValues = {};
    m_layerVariantValues = {};
    m_layerEmissiveValues = {};
    for (size_t index = 0; index < config.layers.size(); ++index)
    {
        const OutdoorTerrainMaterialLayer &layer = config.layers[index];
        m_layerParamValues[index] = {1.0f / layer.repeat, layer.heightContrast, layer.normalStrength, layer.cavity};
        m_layerTintValues[index] = {layer.tint[0], layer.tint[1], layer.tint[2], layer.meadow};
        // w packs the wet sheen in quarters (integer part, 0..4) with the highlight strength (fraction).
        const float specular = index < sources.layerSpecular.size() ? sources.layerSpecular[index] : 0.0f;
        const float wetSheen = index < sources.layerWetSheen.size() ? sources.layerWetSheen[index] : 1.0f;
        m_layerCliffValues[index] = {layer.cliffTint[0], layer.cliffTint[1], layer.cliffTint[2],
            std::round(wetSheen * 4.0f) + std::min(specular, 0.999f)};
        m_layerMacroValues[index] = {layer.macroTint[0], layer.macroTint[1], layer.macroTint[2], layer.macroBrightness};
        m_layerVariantValues[index] = {float(layer.variant < 0 ? int(index) : layer.variant), layer.variantAmount,
            layer.fringe, layer.pools ? 1.0f : 0.0f};
        if (index < sources.layerEmissive.size())
        {
            m_layerEmissiveValues[index] = sources.layerEmissive[index];
        }
    }
    m_controlValues = {float(config.weightedLayers), float(config.slopeLayer), config.slopeStart, config.slopeEnd};
    m_miscValues = {config.fringeStrength, 1.0f / config.fringeScale, 1.0f, 0.0f};
    m_meadowValues = {{{config.meadowDry[0], config.meadowDry[1], config.meadowDry[2], 0.0f},
        {config.meadowLush[0], config.meadowLush[1], config.meadowLush[2], 0.0f}}};
    return true;
}

void TerrainMaterialSet::destroy(bool destroyResources)
{
    const auto release = [destroyResources](auto &handle)
    {
        if (destroyResources && bgfx::isValid(handle))
        {
            bgfx::destroy(handle);
        }
        handle.idx = bgfx::kInvalidHandle;
    };
    release(m_albedoHeight);
    release(m_normalAoRough);
    release(m_weights);
    release(m_macro);
    for (bgfx::UniformHandle &handle : m_samplers)
    {
        release(handle);
    }
    release(m_layerParams);
    release(m_layerTints);
    release(m_layerCliffTints);
    release(m_layerMacro);
    release(m_layerVariants);
    release(m_layerEmissive);
    release(m_control);
    release(m_misc);
    release(m_meadow);
    releaseWeightLayers();
    m_weightSize = 0;
    m_gpuBytes = 0;
}

void TerrainMaterialSet::releaseWeightLayers()
{
    m_weightLayers.clear();
    m_weightLayers.shrink_to_fit();
}

void TerrainMaterialSet::bind(bool antiTiling, float specularStrength) const
{
    const uint32_t clamp = BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP;
    bindTexture(AlbedoHeightStage, m_samplers[0], m_albedoHeight, TextureFilterProfile::Terrain);
    // The normal, occlusion and roughness array is read as often as the albedo but shows far less at grazing angles:
    // without anisotropy it takes the terrain's filter otherwise (trilinear). On the Isle of Ashes this saved about
    // half of the anisotropic filtering's cost (level_generation/terrain/materials/README.md).
    const uint32_t detailFlags = textureBindingSamplerFlags(TextureFilterProfile::Terrain)
        & ~uint32_t(BGFX_SAMPLER_MIN_ANISOTROPIC | BGFX_SAMPLER_MAG_ANISOTROPIC);
    bgfx::setTexture(NormalAoRoughStage, m_samplers[1], m_normalAoRough, detailFlags);
    bgfx::setTexture(WeightsStage, m_samplers[2], m_weights, clamp);
    bindTexture(MacroStage, m_samplers[3], m_macro, TextureFilterProfile::Terrain);
    bgfx::setUniform(m_layerParams, m_layerParamValues.data(), uint16_t(m_layerParamValues.size()));
    bgfx::setUniform(m_layerTints, m_layerTintValues.data(), uint16_t(m_layerTintValues.size()));
    bgfx::setUniform(m_layerCliffTints, m_layerCliffValues.data(), uint16_t(m_layerCliffValues.size()));
    bgfx::setUniform(m_layerMacro, m_layerMacroValues.data(), uint16_t(m_layerMacroValues.size()));
    bgfx::setUniform(m_layerVariants, m_layerVariantValues.data(), uint16_t(m_layerVariantValues.size()));
    bgfx::setUniform(m_layerEmissive, m_layerEmissiveValues.data(), uint16_t(m_layerEmissiveValues.size()));
    bgfx::setUniform(m_control, m_controlValues.data());
    const std::array<float, 4> misc = {m_miscValues[0], m_miscValues[1], antiTiling ? 1.0f : 0.0f, specularStrength};
    bgfx::setUniform(m_misc, misc.data());
    bgfx::setUniform(m_meadow, m_meadowValues.data(), uint16_t(m_meadowValues.size()));
}

bool TerrainMaterialSet::createMaterialArrays(const TerrainMaterialSources &sources, std::string &error)
{
    for (size_t kind = 0; kind < sources.materialLayers.size(); ++kind)
    {
        const std::vector<Engine::CookedTexture> &layers = sources.materialLayers[kind];
        const Engine::CookedTexture &first = layers.front();
        const bgfx::TextureFormat::Enum format = Engine::textureBlockFormat(first.codec);
        if ((bgfx::getCaps()->formats[format] & BGFX_CAPS_FORMAT_TEXTURE_2D) == 0)
        {
            error = std::string("the GPU cannot sample ") + std::string(Engine::textureBlockCodecName(first.codec))
                + " terrain materials; install the asset package built for this platform";
            return false;
        }
        size_t bytes = 0;
        for (const Engine::CookedTexture &layer : layers)
        {
            bytes += layer.blocks.size();
        }
        const bgfx::Memory *pMemory = bgfx::alloc(uint32_t(bytes));
        size_t offset = 0;
        for (const Engine::CookedTexture &layer : layers)
        {
            std::copy(layer.blocks.begin(), layer.blocks.end(), pMemory->data + offset);
            offset += layer.blocks.size();
        }
        bgfx::TextureHandle &handle = kind == 0 ? m_albedoHeight : m_normalAoRough;
        // Display-encoded like the native tiles: sampled raw, lit in the shader's existing colour space.
        handle = bgfx::createTexture2D(first.width, first.height, first.levels > 1, uint16_t(layers.size()),
            format, BGFX_TEXTURE_NONE, pMemory);
        if (!bgfx::isValid(handle))
        {
            error = "cannot allocate the terrain material array";
            return false;
        }
        m_gpuBytes += bytes;
    }
    return true;
}

bool TerrainMaterialSet::createWeights(const TerrainMaterialSources &sources,
    const OutdoorTerrainMaterialConfig &config, std::string &error)
{
    const int size = MapCells * config.texelsPerCell;
    m_weightSize = size;
    m_weightLayers.assign(size_t(size) * size, 0);
    // Both weight images in one two-layer array (one sampler stage); a map with four ground layers or fewer leaves the
    // second layer empty.
    std::array<const std::vector<std::vector<uint8_t>> *, 2> layerLevels = {};
    for (size_t index = 0; index < layerLevels.size() && index < config.weightFiles.size(); ++index)
    {
        const std::vector<std::vector<uint8_t>> &levels = sources.weightLevels[index];
        const std::vector<uint8_t> &rgba = levels.front();
        for (int channel = 0; channel < 4; ++channel)
        {
            const int layer = int(index) * 4 + channel;
            for (size_t texel = 0; texel < m_weightLayers.size(); ++texel)
            {
                if (rgba[texel * 4 + size_t(channel)] != 0)
                {
                    m_weightLayers[texel] |= uint8_t(1u << layer);
                }
            }
        }
        layerLevels[index] = &levels;
    }
    std::vector<std::vector<uint8_t>> noWeights = {std::vector<uint8_t>(4, 0)};
    const int textureSize = layerLevels[0] != nullptr ? size : 1;
    if (layerLevels[0] != nullptr)
    {
        noWeights.clear();
        for (const std::vector<uint8_t> &level : *layerLevels[0])
        {
            noWeights.emplace_back(level.size(), 0);
        }
    }
    size_t bytes = 0;
    for (const std::vector<std::vector<uint8_t>> *&pLevels : layerLevels)
    {
        if (pLevels == nullptr)
        {
            pLevels = &noWeights;
        }
        for (const std::vector<uint8_t> &level : *pLevels)
        {
            bytes += level.size();
        }
    }
    if (layerLevels[1]->size() != layerLevels[0]->size()
        || layerLevels[1]->front().size() != layerLevels[0]->front().size())
    {
        error = "the terrain weight images differ in size";
        return false;
    }
    // Layer-major: every mip level of layer 0, then those of layer 1.
    const bgfx::Memory *pMemory = bgfx::alloc(uint32_t(bytes));
    size_t offset = 0;
    for (const std::vector<std::vector<uint8_t>> *pLevels : layerLevels)
    {
        for (const std::vector<uint8_t> &level : *pLevels)
        {
            std::copy(level.begin(), level.end(), pMemory->data + offset);
            offset += level.size();
        }
    }
    m_weights = bgfx::createTexture2D(uint16_t(textureSize), uint16_t(textureSize), noWeights.size() > 1, 2,
        bgfx::TextureFormat::RGBA8, BGFX_TEXTURE_NONE, pMemory);
    m_gpuBytes += bytes;
    if (!bgfx::isValid(m_weights))
    {
        error = "cannot allocate terrain material weights";
        return false;
    }
    m_macro = createRgbaTexture(sources.macroSize, sources.macroSize, sources.macroLevels);
    for (const std::vector<uint8_t> &level : sources.macroLevels)
    {
        m_gpuBytes += level.size();
    }
    if (!bgfx::isValid(m_macro))
    {
        error = "cannot allocate the terrain macro variation texture";
        return false;
    }
    return true;
}
} // namespace OpenYAMM::Game
