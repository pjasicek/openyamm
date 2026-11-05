#include "game/render/TerrainMaterialConfig.h"

#include <yaml-cpp/yaml.h>

#include <cmath>
#include <filesystem>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
float boundedFloat(const YAML::Node &node, const char *pName, float fallback, float min, float max)
{
    const float value = node[pName] ? node[pName].as<float>() : fallback;
    if (!std::isfinite(value) || value < min || value > max)
    {
        throw std::runtime_error(std::string("invalid terrain material ") + pName);
    }
    return value;
}
}

std::optional<OutdoorTerrainMaterialConfig> parseTerrainMaterialConfig(
    const std::string &text, const std::string &directory, const std::string &path, std::string &error)
{
    error.clear();
    OutdoorTerrainMaterialConfig config;
    config.directory = directory;
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (root["version"].as<int>() != 1)
        {
            throw std::runtime_error("expected terrain material version 1");
        }
        config.texelsPerCell = root["texels_per_cell"].as<int>();
        if (config.texelsPerCell < 1 || config.texelsPerCell > 32
            || (config.texelsPerCell & (config.texelsPerCell - 1)) != 0)
        {
            throw std::runtime_error("texels_per_cell must be a power of two up to 32");
        }
        for (const YAML::Node &file : root["weights"])
        {
            const std::string name = file.as<std::string>();
            if (name.empty() || std::filesystem::path(name).filename().string() != name)
            {
                throw std::runtime_error("weight images must be local filenames");
            }
            config.weightFiles.push_back(name);
        }
        config.weightedLayers = root["weighted_layers"].as<int>();
        if (config.weightFiles.empty() || config.weightFiles.size() > 2
            || config.weightedLayers < 1 || config.weightedLayers > int(config.weightFiles.size() * 4))
        {
            throw std::runtime_error("expected one or two weight images covering the weighted layers");
        }
        const YAML::Node layers = root["layers"];
        if (!layers.IsSequence() || layers.size() < size_t(config.weightedLayers)
            || layers.size() > OutdoorTerrainMaterialConfig::MaxLayers)
        {
            throw std::runtime_error("expected the weighted layers plus an optional slope layer, at most 8");
        }
        for (const YAML::Node &node : layers)
        {
            OutdoorTerrainMaterialLayer layer;
            layer.name = node["name"].as<std::string>();
            layer.library = node["library"].as<std::string>();
            layer.tint = node["tint"].as<std::array<float, 3>>();
            layer.cliffTint = node["cliff_tint"] ? node["cliff_tint"].as<std::array<float, 3>>() : layer.tint;
            for (float value : {layer.tint[0], layer.tint[1], layer.tint[2], layer.cliffTint[0], layer.cliffTint[1],
                     layer.cliffTint[2]})
            {
                if (!std::isfinite(value) || value < 0.0f || value > 4.0f)
                {
                    throw std::runtime_error("invalid terrain material tint");
                }
            }
            layer.repeat = boundedFloat(node, "repeat", 512.0f, 32.0f, 8192.0f);
            layer.heightContrast = boundedFloat(node, "height_contrast", 0.35f, 0.01f, 1.0f);
            layer.normalStrength = boundedFloat(node, "normal_strength", 1.0f, 0.0f, 3.0f);
            layer.cavity = boundedFloat(node, "cavity", 0.0f, 0.0f, 1.0f);
            layer.macroBrightness = boundedFloat(node, "macro_brightness", 0.15f, 0.0f, 1.0f);
            layer.variant = node["variant"].as<int>(-1);
            layer.variantAmount = boundedFloat(node, "variant_amount", 0.5f, 0.0f, 1.0f);
            layer.fringe = boundedFloat(node, "fringe", 1.0f, 0.0f, 4.0f);
            layer.pools = node["pools"].as<bool>(false);
            layer.meadow = boundedFloat(node, "meadow", 0.0f, 0.0f, 2.0f);
            if (node["macro_tint"])
            {
                layer.macroTint = node["macro_tint"].as<std::array<float, 3>>();
                for (float value : layer.macroTint)
                {
                    if (!std::isfinite(value) || value < 0.0f || value > 3.0f)
                    {
                        throw std::runtime_error("invalid terrain material macro_tint");
                    }
                }
            }
            config.layers.push_back(std::move(layer));
        }
        for (const OutdoorTerrainMaterialLayer &layer : config.layers)
        {
            if (layer.variant < -1 || layer.variant >= int(config.layers.size()))
            {
                throw std::runtime_error("terrain material variant must name a layer");
            }
        }
        if (const YAML::Node slope = root["slope"])
        {
            config.slopeLayer = slope["layer"].as<int>();
            config.slopeStart = boundedFloat(slope, "start", 0.3f, 0.0f, 1.0f);
            config.slopeEnd = boundedFloat(slope, "end", 0.5f, 0.0f, 1.0f);
            if (config.slopeLayer < 0 || config.slopeLayer >= int(config.layers.size())
                || config.slopeEnd <= config.slopeStart)
            {
                throw std::runtime_error("invalid slope layer");
            }
        }
        config.smoothing = boundedFloat(root, "smoothing", 1.0f, 0.0f, 1.0f);
        if (const YAML::Node fringe = root["fringe"])
        {
            config.fringeStrength = boundedFloat(fringe, "strength", 0.0f, 0.0f, 4.0f);
            config.fringeScale = boundedFloat(fringe, "scale", 2048.0f, 256.0f, 65536.0f);
        }
        if (const YAML::Node meadow = root["meadow"])
        {
            config.meadowDry = meadow["dry"].as<std::array<float, 3>>();
            config.meadowLush = meadow["lush"].as<std::array<float, 3>>();
            for (float value : {config.meadowDry[0], config.meadowDry[1], config.meadowDry[2], config.meadowLush[0],
                     config.meadowLush[1], config.meadowLush[2]})
            {
                if (!std::isfinite(value) || value < 0.0f || value > 2.0f)
                {
                    throw std::runtime_error("invalid terrain meadow tint");
                }
            }
        }
        if (const YAML::Node shoreNode = root["shore"])
        {
            OutdoorTerrainMaterialShore shore;
            shore.file = shoreNode["file"].as<std::string>();
            if (shore.file.empty() || std::filesystem::path(shore.file).filename().string() != shore.file)
            {
                throw std::runtime_error("the shore image must be a local filename");
            }
            shore.range = boundedFloat(shoreNode, "range", 1024.0f, 64.0f, 16384.0f);
            shore.beachSlope = boundedFloat(shoreNode, "beach_slope", 0.3f, 0.0f, 2.0f);
            shore.beachBlend = boundedFloat(shoreNode, "beach_blend", 192.0f, 16.0f, 2048.0f);
            shore.seabedSlope = boundedFloat(shoreNode, "seabed_slope", 0.5f, 0.01f, 4.0f);
            shore.seabedDepth = boundedFloat(shoreNode, "seabed_depth", 160.0f, 8.0f, 2048.0f);
            shore.opaqueDepth = boundedFloat(shoreNode, "opaque_depth", 72.0f, 8.0f, 2048.0f);
            shore.detailDepth = boundedFloat(shoreNode, "detail_depth", 24.0f, 0.0f, shore.opaqueDepth);
            shore.layer = shoreNode["layer"] ? shoreNode["layer"].as<int>() : -1;
            if (shore.layer >= int(config.layers.size()))
            {
                throw std::runtime_error("shore layer out of range");
            }
            config.shore = shore;
        }
        return config;
    }
    catch (const std::exception &exception)
    {
        error = path + ": " + exception.what();
        return std::nullopt;
    }
}
} // namespace OpenYAMM::Game
