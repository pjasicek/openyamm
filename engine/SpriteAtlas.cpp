#include "engine/SpriteAtlas.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace OpenYAMM::Engine
{
namespace
{
bool isIdentifier(const std::string &value)
{
    return !value.empty() && value.size() <= 128
        && std::all_of(value.begin(), value.end(), [](char c)
        {
            return (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '-';
        });
}

void require(bool condition, const char *pMessage)
{
    if (!condition)
    {
        throw std::runtime_error(pMessage);
    }
}

template<class T, size_t Count>
std::array<T, Count> readArray(const YAML::Node &node)
{
    require(node.IsSequence() && node.size() == Count, "Invalid atlas array length");
    std::array<T, Count> result = {};
    for (size_t i = 0; i < Count; ++i)
    {
        result[i] = node[i].as<T>();
    }
    return result;
}

bool isPagePath(const std::string &path)
{
    return path.starts_with("atlas/") && path.ends_with(".png")
        && isIdentifier(path.substr(6, path.size() - 10));
}
}

std::optional<SpriteAtlasReference> parseSpriteAtlasReference(const std::string &name)
{
    if (!name.starts_with("atlas:"))
    {
        return std::nullopt;
    }
    const size_t slash = name.find('/', 6);
    if (slash == std::string::npos)
    {
        return std::nullopt;
    }
    SpriteAtlasReference reference = {name.substr(6, slash - 6), name.substr(slash + 1)};
    return isIdentifier(reference.package) && isIdentifier(reference.frame)
        ? std::optional<SpriteAtlasReference>(reference) : std::nullopt;
}

std::optional<SpriteAtlas> SpriteAtlas::parse(const std::string &text, std::string &error)
{
    error.clear();
    try
    {
        const YAML::Node root = YAML::Load(text);
        require(root["schema_version"].as<int>() == 1, "Unsupported sprite atlas schema");
        const std::string recolorModel = root["recolor_model"].as<std::string>();
        const bool useSingleLut = recolorModel == "masked_luminance_lut_v1";
        const bool useMultiLut = recolorModel == "multi_mask_luminance_lut_v1";
        const bool useRgbLut = recolorModel == "masked_native_rgb_displacement_lut_v1";
        const bool useLookup = useSingleLut || useMultiLut || useRgbLut;
        const bool useFourRegions = recolorModel == "multi_mask_luminance_rgb_v1" || useMultiLut;
        const bool useRegions = recolorModel == "masked_regions_luminance_rgb_v1" || useFourRegions;
        require(recolorModel == "green_chroma_srgb_v1" || recolorModel == "masked_luminance_rgb_v1"
            || useRegions || useLookup,
            "Unsupported recolor model");
        const bool useLuminance = recolorModel == "masked_luminance_rgb_v1";
        SpriteAtlas atlas;
        atlas.maskChannels = useFourRegions ? 4 : (useRegions ? 2 : 1);
        atlas.pixelsPerLogicalPixel = root["pixels_per_logical_pixel"].as<float>();
        require(std::isfinite(atlas.pixelsPerLogicalPixel) && atlas.pixelsPerLogicalPixel > 0
            && atlas.pixelsPerLogicalPixel <= 16, "Invalid sprite pixel scale");
        atlas.logicalCanvas = readArray<int, 2>(root["logical_canvas"]);
        atlas.logicalPivot = readArray<float, 2>(root["logical_pivot"]);
        for (size_t i = 0; i < 2; ++i)
        {
            require(atlas.logicalCanvas[i] > 0 && atlas.logicalCanvas[i] <= 8192, "Invalid logical canvas");
            require(std::isfinite(atlas.logicalPivot[i]), "Invalid logical pivot");
        }
        require(root["pages"].IsSequence() && root["pages"].size() > 0 && root["pages"].size() <= 64,
            "Invalid atlas page count");
        for (const YAML::Node &node : root["pages"])
        {
            SpriteAtlasPage page;
            page.base = node["base"].as<std::string>();
            page.mask = node["mask"].as<std::string>();
            page.size = readArray<int, 2>(node["size"]);
            require(isPagePath(page.base) && isPagePath(page.mask), "Invalid atlas page path");
            require(page.size[0] > 0 && page.size[1] > 0 && page.size[0] <= 8192 && page.size[1] <= 8192,
                "Invalid atlas page dimensions");
            atlas.pages.push_back(std::move(page));
        }
        require(root["frames"].IsMap() && root["frames"].size() > 0 && root["frames"].size() <= 16384,
            "Invalid atlas frame count");
        for (const auto &entry : root["frames"])
        {
            const std::string name = entry.first.as<std::string>();
            require(isIdentifier(name), "Invalid atlas frame name");
            const YAML::Node node = entry.second;
            SpriteAtlasFrame frame;
            frame.page = node["page"].as<int>();
            frame.rectangle = readArray<int, 4>(node["atlas_xywh"]);
            frame.cropOrigin = readArray<int, 2>(node["crop_origin_px"]);
            require(frame.page >= 0 && size_t(frame.page) < atlas.pages.size(), "Invalid frame page");
            const std::array<int, 2> &size = atlas.pages[frame.page].size;
            const std::array<int, 4> &rect = frame.rectangle;
            require(rect[0] >= 0 && rect[1] >= 0 && rect[2] > 0 && rect[3] > 0
                && rect[2] <= size[0] && rect[3] <= size[1]
                && rect[0] <= size[0] - rect[2] && rect[1] <= size[1] - rect[3], "Frame outside atlas page");
            require(std::abs(double(frame.cropOrigin[0])) <= 131072
                && std::abs(double(frame.cropOrigin[1])) <= 131072, "Unbounded crop origin");
            require(atlas.frames.emplace(name, frame).second, "Duplicate atlas frame");
        }
        require(root["variants"].IsMap() && root["variants"].size() > 0, "Missing sprite variants");
        for (const auto &entry : root["variants"])
        {
            const int id = entry.first.as<int>();
            require(id >= 0 && id <= 32767, "Invalid sprite variant id");
            SpriteAtlasVariant variant;
            if (!entry.second["exact_base_bypass"].as<bool>(false) && useLookup)
            {
                variant.lookup = entry.second["lookup"].as<std::string>();
                const std::string suffix = ".rgba32f";
                require(variant.lookup.starts_with("atlas/") && variant.lookup.ends_with(suffix)
                    && isIdentifier(variant.lookup.substr(6, variant.lookup.size() - 6 - suffix.size())),
                    "Invalid sprite lookup path");
                variant.lookupSize = readArray<int, 2>(entry.second["lookup_size"]);
                const std::array<int, 2> expected = useRgbLut ? std::array<int, 2>{1089, 33}
                    : std::array<int, 2>{256, useMultiLut ? 4 : 1};
                require(variant.lookupSize == expected, "Invalid sprite lookup dimensions");
                variant.chroma[3] = useRgbLut ? 7 : (useMultiLut ? 6 : 5);
            }
            else if (!entry.second["exact_base_bypass"].as<bool>(false) && useRegions)
            {
                const YAML::Node ramps = entry.second["region_luminance_vectors"];
                require(ramps.IsSequence() && ramps.size() == size_t(atlas.maskChannels),
                    "Sprite region ramp count must match mask channels");
                const std::array<std::array<float, 4> *, 4> targets = {
                    &variant.chroma, &variant.secondChroma, &variant.thirdChroma, &variant.fourthChroma};
                for (size_t region = 0; region < size_t(atlas.maskChannels); ++region)
                {
                    const std::array<float, 3> ramp = readArray<float, 3>(ramps[region]);
                    std::array<float, 4> &target = *targets[region];
                    for (size_t i = 0; i < 3; ++i)
                    {
                        require(std::isfinite(ramp[i]) && ramp[i] >= 0 && ramp[i] <= 4,
                            "Invalid sprite region ramp");
                        target[i] = ramp[i];
                    }
                }
                variant.chroma[3] = useFourRegions ? 4 : 3;
            }
            else if (!entry.second["exact_base_bypass"].as<bool>(false))
            {
                const std::array<float, 3> ramp = readArray<float, 3>(
                    entry.second[useLuminance ? "luminance_vector" : "chroma_vector"]);
                for (size_t i = 0; i < 3; ++i)
                {
                    require(std::isfinite(ramp[i]) && ramp[i] >= 0 && ramp[i] <= 4, "Invalid sprite chroma ramp");
                    variant.chroma[i] = ramp[i];
                }
                variant.chroma[3] = useLuminance ? 2 : 1;
            }
            require(atlas.variants.emplace(id, variant).second, "Duplicate sprite variant");
        }
        return atlas;
    }
    catch (const std::exception &exception)
    {
        error = exception.what();
        return std::nullopt;
    }
}
}
