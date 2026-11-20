// Host-side texture cooker: encodes source images into cooked .oytex files with the runtime's own mip filtering.
// Driven by tools/cook_models.py, tools/terrain_materials.py and tools/cook_surface_textures.py, which own the cook
// decisions; this tool only executes them.
//   openyamm_model_texture_cook <jobs.tsv>     one job per line, tab-separated:
//       input.png  output.oytex  codec  semantic(linear|srgb|normal)  alpha_cutoff  mips(0|1)  max_size
//       linear_channels(0|1)  source_hash(hex)  [kind(model|surface|ui|ui_atlas|effect_atlas|terrain_material)
//       [mip_sharpening]]
//     A model job with mip_sharpening (a strength > 0, colour and linear semantics only) sharpens its mips below the
//     first like terrain materials, with clamped neighbours (atlases do not tile) and alpha left as filtered.
//     A surface job (world BLV/ODM face texture, PNG or BMP) decodes as the map loader does: the magenta colour key
//     becomes transparent, and the source size is kept exactly (UVs depend on it); a non-power-of-two surface fails.
//     A ui job (HUD art) decodes and edge-bleeds as the HUD does and pads by edge replication, to whole 4x4 blocks
//     (power-of-two sides when mipped), recording the content size. A ui_atlas job's input lists frames (see buildUiAtlas), packed into block-aligned cells of one texture.
//     An effect_atlas job's input lists effect sprite frames (see buildEffectAtlas), packed as the effect renderer packs
//     them at load and edge-bled as its Billboard upload does.
//     A terrain_material job decodes as a model texture and sharpens its tiling mips (sharpenMips).
//   openyamm_model_texture_cook --verify <file.oytex>...   prints each file's header (path, codec, semantic, cutoff,
//       width, height, levels, source hash, alpha use or "-" for version 1); fails on any invalid file
//   openyamm_model_texture_cook --preview <in.oytex> <out.rgba> [level]   decodes one mip level (default the
//       largest) to raw RGBA8 and prints "width height", for reviewing encoding artefacts
//   openyamm_model_texture_cook --rewrap <list.txt>   migration: rewrites each listed version 2 .oytex (one path per
//       line) as the current version without re-encoding its blocks, after checking the version 2 content hash; prints
//       "rewrapped<TAB>path" or "current<TAB>path" (already current) per file and fails on any invalid file
//   openyamm_model_texture_cook --geometry <request> <response>   the model cook's geometry passes (hidden back faces,
//       vertex cache order); see tools/CookModelGeometry.cpp
#include "engine/ImageAssetLoader.h"
#include "engine/ImageMipmaps.h"
#include "engine/render/CookedTexture.h"
#include "tools/TextureBlockEncode.h"
#include "tools/CookModelGeometry.h"

#include <Decode.hpp>
#include <bcdec.h>
#include <zstd.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cctype>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <thread>
#include <utility>

namespace
{
using namespace OpenYAMM;

enum class JobKind
{
    Model,
    Surface,
    Ui,
    UiAtlas,
    EffectAtlas,
    TerrainMaterial,
};

struct Job
{
    std::filesystem::path input;
    std::filesystem::path output;
    Engine::TextureBlockCodec codec = Engine::TextureBlockCodec::Bc7;
    Engine::ImageMipSemantic semantic = Engine::ImageMipSemantic::Linear;
    uint8_t alphaCutoff = 0;
    bool mips = true;
    int maxSize = Engine::CookedTextureSizeLimit;
    bool linearChannels = false;
    uint64_t sourceHash = 0;
    JobKind kind = JobKind::Model;
    float mipSharpening = 0.0f;
};

std::vector<uint8_t> read(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file || file.tellg() <= 0)
    {
        throw std::runtime_error("Missing or empty file: " + path.string());
    }
    std::vector<uint8_t> bytes(size_t(file.tellg()));
    file.seekg(0);
    if (!file.read(reinterpret_cast<char *>(bytes.data()), std::streamsize(bytes.size())))
    {
        throw std::runtime_error("Incomplete read: " + path.string());
    }
    return bytes;
}

void writeAtomically(const std::filesystem::path &path, const std::vector<uint8_t> &bytes)
{
    std::filesystem::create_directories(path.parent_path());
    const std::filesystem::path temporary = path.string() + ".tmp";
    {
        std::ofstream file(temporary, std::ios::binary | std::ios::trunc);
        if (!file.write(reinterpret_cast<const char *>(bytes.data()), std::streamsize(bytes.size())))
        {
            throw std::runtime_error("Cannot write " + temporary.string());
        }
    }
    std::filesystem::rename(temporary, path);
}

Engine::ImageMipSemantic parseSemantic(const std::string &name)
{
    if (name == "linear")
    {
        return Engine::ImageMipSemantic::Linear;
    }
    if (name == "srgb")
    {
        return Engine::ImageMipSemantic::Srgb;
    }
    if (name == "normal")
    {
        return Engine::ImageMipSemantic::Normal;
    }
    throw std::runtime_error("Unknown semantic: " + name);
}

std::string semanticName(Engine::ImageMipSemantic semantic)
{
    switch (semantic)
    {
    case Engine::ImageMipSemantic::Linear: return "linear";
    case Engine::ImageMipSemantic::Srgb: return "srgb";
    case Engine::ImageMipSemantic::Normal: return "normal";
    }
    return "unknown";
}

std::vector<Job> parseJobs(const std::filesystem::path &path)
{
    std::ifstream file(path);
    if (!file)
    {
        throw std::runtime_error("Cannot open job list: " + path.string());
    }
    std::vector<Job> jobs;
    std::string line;
    while (std::getline(file, line))
    {
        if (line.empty())
        {
            continue;
        }
        std::vector<std::string> fields;
        std::stringstream stream(line);
        for (std::string field; std::getline(stream, field, '\t');)
        {
            fields.push_back(field);
        }
        if (fields.size() < 9 || fields.size() > 11)
        {
            throw std::runtime_error("Job needs nine to eleven tab-separated fields: " + line);
        }
        static const std::array<std::pair<std::string_view, JobKind>, 6> kinds = {{{"model", JobKind::Model},
            {"surface", JobKind::Surface}, {"ui", JobKind::Ui}, {"ui_atlas", JobKind::UiAtlas},
            {"effect_atlas", JobKind::EffectAtlas}, {"terrain_material", JobKind::TerrainMaterial}}};
        const auto kind = std::find_if(kinds.begin(), kinds.end(), [&](const auto &entry)
        {
            return fields.size() >= 10 && entry.first == fields[9];
        });
        if (fields.size() >= 10 && kind == kinds.end())
        {
            throw std::runtime_error("Unknown job kind: " + fields[9]);
        }
        Job job;
        job.input = fields[0];
        job.output = fields[1];
        const std::optional<Engine::TextureBlockCodec> codec = Engine::parseTextureBlockCodec(fields[2]);
        if (!codec)
        {
            throw std::runtime_error("Unknown codec: " + fields[2]);
        }
        job.codec = *codec;
        job.semantic = parseSemantic(fields[3]);
        job.alphaCutoff = uint8_t(std::stoi(fields[4]));
        job.mips = fields[5] == "1";
        job.maxSize = std::stoi(fields[6]);
        job.linearChannels = fields[7] == "1";
        job.sourceHash = std::stoull(fields[8], nullptr, 16);
        job.kind = kind == kinds.end() ? JobKind::Model : kind->second;
        if (fields.size() == 11)
        {
            job.mipSharpening = std::stof(fields[10]);
            if (job.kind != JobKind::Model || job.semantic == Engine::ImageMipSemantic::Normal
                || !(job.mipSharpening > 0.0f && job.mipSharpening <= 4.0f))
            {
                throw std::runtime_error("Mip sharpening needs a colour or linear model job and a strength in (0, 4]: "
                    + line);
            }
        }
        if (job.maxSize < 1 || job.maxSize > Engine::CookedTextureSizeLimit)
        {
            throw std::runtime_error("Invalid max size in job: " + line);
        }
        jobs.push_back(std::move(job));
    }
    return jobs;
}

int powerOfTwoAtMost(int size)
{
    int result = 1;
    while (result * 2 <= size)
    {
        result *= 2;
    }
    return result;
}

// Area-weighted downscale of one axis: each target texel averages the source span it covers.
std::vector<float> resampleAxis(const std::vector<float> &source, int width, int height, int targetWidth)
{
    std::vector<float> target(size_t(targetWidth) * height * 4, 0.0f);
    const double scale = double(width) / targetWidth;
    for (int x = 0; x < targetWidth; ++x)
    {
        const double begin = x * scale;
        const double end = begin + scale;
        for (int sx = int(begin); sx < width && sx < end; ++sx)
        {
            const float weight = float((std::min(end, sx + 1.0) - std::max(begin, double(sx))) / scale);
            for (int y = 0; y < height; ++y)
            {
                for (int channel = 0; channel < 4; ++channel)
                {
                    target[(size_t(y) * targetWidth + x) * 4 + channel]
                        += weight * source[(size_t(y) * width + sx) * 4 + channel];
                }
            }
        }
    }
    return target;
}

std::vector<float> transpose(const std::vector<float> &source, int width, int height)
{
    std::vector<float> target(source.size());
    for (int y = 0; y < height; ++y)
    {
        for (int x = 0; x < width; ++x)
        {
            std::copy_n(source.begin() + (size_t(y) * width + x) * 4, 4, target.begin() + (size_t(x) * height + y) * 4);
        }
    }
    return target;
}

// Cooked textures are power-of-two: an OpenGL driver (NVIDIA, GL 3.3) leaves non-power-of-two sRGB block textures
// with mips incomplete, so they sample black, and several GLES drivers restrict them too. A non-power-of-two source
// is area-downscaled to the next smaller power of two in each axis (UVs are normalized, so the mapping is
// unchanged): colour in linear light, normals renormalized, cutout alpha keeping the source's coverage.
void resampleToPowerOfTwo(Engine::ImagePixelsBgra &image, Engine::ImageMipSemantic semantic, uint8_t alphaCutoff)
{
    const int targetWidth = powerOfTwoAtMost(image.width);
    const int targetHeight = powerOfTwoAtMost(image.height);
    if (targetWidth == image.width && targetHeight == image.height)
    {
        return;
    }
    std::vector<float> values(image.pixels.size());
    for (size_t i = 0; i < values.size(); ++i)
    {
        const float value = image.pixels[i] / 255.0f;
        const bool colour = i % 4 != 3;
        values[i] = colour && semantic == Engine::ImageMipSemantic::Srgb ? Engine::srgbToLinear(value)
            : colour && semantic == Engine::ImageMipSemantic::Normal ? value * 2.0f - 1.0f : value;
    }
    values = resampleAxis(values, image.width, image.height, targetWidth);
    values = transpose(resampleAxis(transpose(values, targetWidth, image.height), image.height, targetWidth,
        targetHeight), targetHeight, targetWidth);
    std::vector<uint8_t> pixels(size_t(targetWidth) * targetHeight * 4);
    for (size_t texel = 0; texel < pixels.size() / 4; ++texel)
    {
        float *pValue = values.data() + texel * 4;
        if (semantic == Engine::ImageMipSemantic::Normal)
        {
            const float length = std::sqrt(pValue[0] * pValue[0] + pValue[1] * pValue[1] + pValue[2] * pValue[2]);
            for (int channel = 0; channel < 3; ++channel)
            {
                pValue[channel] = (length > 0.0f ? pValue[channel] / length : 0.0f) * 0.5f + 0.5f;
            }
        }
        else if (semantic == Engine::ImageMipSemantic::Srgb)
        {
            for (int channel = 0; channel < 3; ++channel)
            {
                pValue[channel] = Engine::linearToSrgb(pValue[channel]);
            }
        }
        for (int channel = 0; channel < 4; ++channel)
        {
            pixels[texel * 4 + channel] = uint8_t(std::clamp(std::lround(pValue[channel] * 255.0f), 0L, 255L));
        }
    }
    Engine::preserveBgraCutoutCoverage(pixels, image.pixels, alphaCutoff);
    image.width = targetWidth;
    image.height = targetHeight;
    image.pixels = std::move(pixels);
}

std::string lowerStem(const std::filesystem::path &path)
{
    std::string name = path.stem().string();
    std::transform(name.begin(), name.end(), name.begin(), [](unsigned char c) { return char(std::tolower(c)); });
    return name;
}

Engine::ImagePixelsBgra decodeSource(const std::filesystem::path &path, const Engine::ImageDecodeOptions &options)
{
    std::optional<Engine::ImagePixelsBgra> decoded = Engine::decodeImagePixelsBgra(read(path), path.string(), options);
    if (!decoded || decoded->width <= 0 || decoded->height <= 0 || decoded->width > 65535 || decoded->height > 65535)
    {
        throw std::runtime_error("Cannot decode source image: " + path.string());
    }
    return std::move(*decoded);
}

// The HUD's decode (GameplayHudCommon::loadHudBitmapPixelsBgraCached, colour-key mode) and upload preparation
// (createBgraTexture2D, Ui profiles): magenta and teal keys, black for map arrows and minimap icons, then transparent
// texels take the nearest visible colour.
Engine::ImagePixelsBgra decodeUiSource(const std::filesystem::path &path)
{
    Engine::ImageDecodeOptions options = {};
    options.applyMagentaTransparencyKey = true;
    options.applyTealTransparencyKey = true;
    const std::string name = lowerStem(path);
    options.applyBlackTransparencyKey = name.starts_with("mapdir") || name.starts_with("micon");
    Engine::ImagePixelsBgra image = decodeSource(path, options);
    if (Engine::hasMixedBgraTransparency(image.pixels.data(), image.pixels.size() / 4))
    {
        Engine::bleedTransparentBgraEdgeColors(uint16_t(image.width), uint16_t(image.height), image.pixels);
    }
    return image;
}

int wholeBlocks(int size)
{
    return (size + 3) / 4 * 4;
}

int powerOfTwoAtLeast(int size)
{
    int result = 4;
    while (result < size)
    {
        result *= 2;
    }
    return result;
}

// Copies image into target at (left, top), replicating its last column and row over a cellWidth x cellHeight cell, so
// clamp sampling within the image's own extent matches the source.
void placePadded(const Engine::ImagePixelsBgra &image, std::vector<uint8_t> &target, int targetWidth, int left, int top,
    int cellWidth, int cellHeight)
{
    for (int y = 0; y < cellHeight; ++y)
    {
        const int sourceY = std::min(y, image.height - 1);
        for (int x = 0; x < cellWidth; ++x)
        {
            const int sourceX = std::min(x, image.width - 1);
            std::memcpy(target.data() + (size_t(top + y) * targetWidth + left + x) * 4,
                image.pixels.data() + (size_t(sourceY) * image.width + sourceX) * 4, 4);
        }
    }
}

// A ui_atlas job's input lists "columns<TAB>N", then one frame image per line, all the same size. Frames are padded
// to whole blocks and laid out row by row, so each frame's blocks can be cut out as its own texture.
Engine::ImagePixelsBgra buildUiAtlas(const std::filesystem::path &listPath, int &contentWidth, int &contentHeight)
{
    std::ifstream file(listPath);
    std::string line;
    if (!std::getline(file, line) || !line.starts_with("columns\t"))
    {
        throw std::runtime_error("Atlas list needs a columns line: " + listPath.string());
    }
    const int columns = std::stoi(line.substr(8));
    std::vector<Engine::ImagePixelsBgra> frames;
    while (std::getline(file, line))
    {
        if (!line.empty())
        {
            frames.push_back(decodeUiSource(line));
            if (frames.back().width != frames.front().width || frames.back().height != frames.front().height)
            {
                throw std::runtime_error("Atlas frame differs in size: " + line);
            }
        }
    }
    if (frames.empty() || columns < 1)
    {
        throw std::runtime_error("Empty atlas list: " + listPath.string());
    }
    const int cellWidth = wholeBlocks(frames.front().width);
    const int cellHeight = wholeBlocks(frames.front().height);
    const int rows = (int(frames.size()) + columns - 1) / columns;
    Engine::ImagePixelsBgra atlas;
    atlas.width = cellWidth * std::min(columns, int(frames.size()));
    atlas.height = cellHeight * rows;
    atlas.pixels.assign(size_t(atlas.width) * atlas.height * 4, 0);
    for (size_t index = 0; index < frames.size(); ++index)
    {
        placePadded(frames[index], atlas.pixels, atlas.width, int(index % columns) * cellWidth,
            int(index / columns) * cellHeight, cellWidth, cellHeight);
    }
    contentWidth = atlas.width;
    contentHeight = atlas.height;
    return atlas;
}

// An effect_atlas job's input lists "columns<TAB>N", then one frame image per line, all the same size with sides in
// whole 4x4 blocks. As EffectRenderer::loadAtlas does at load: plain decode, frames row by row in cells of the frame
// size, then the Billboard upload's transparent-edge bleed over the whole atlas. The renderer derives each frame's
// UVs from the column count and frame size in the sprite descriptor.
Engine::ImagePixelsBgra buildEffectAtlas(const std::filesystem::path &listPath)
{
    std::ifstream file(listPath);
    std::string line;
    if (!std::getline(file, line) || !line.starts_with("columns\t"))
    {
        throw std::runtime_error("Atlas list needs a columns line: " + listPath.string());
    }
    const int columns = std::stoi(line.substr(8));
    std::vector<Engine::ImagePixelsBgra> frames;
    while (std::getline(file, line))
    {
        if (!line.empty())
        {
            frames.push_back(decodeSource(line, {}));
            if (frames.back().width != frames.front().width || frames.back().height != frames.front().height)
            {
                throw std::runtime_error("Atlas frame differs in size: " + line);
            }
        }
    }
    if (frames.empty() || columns < 1)
    {
        throw std::runtime_error("Empty atlas list: " + listPath.string());
    }
    const int frameWidth = frames.front().width;
    const int frameHeight = frames.front().height;
    if (frameWidth != wholeBlocks(frameWidth) || frameHeight != wholeBlocks(frameHeight))
    {
        throw std::runtime_error("Effect frames need sides in whole 4x4 blocks: " + listPath.string());
    }
    const int rows = (int(frames.size()) + columns - 1) / columns;
    Engine::ImagePixelsBgra atlas;
    atlas.width = frameWidth * std::min(columns, int(frames.size()));
    atlas.height = frameHeight * rows;
    atlas.pixels.assign(size_t(atlas.width) * atlas.height * 4, 0);
    for (size_t index = 0; index < frames.size(); ++index)
    {
        placePadded(frames[index], atlas.pixels, atlas.width, int(index % columns) * frameWidth,
            int(index / columns) * frameHeight, frameWidth, frameHeight);
    }
    if (Engine::hasMixedBgraTransparency(atlas.pixels.data(), atlas.pixels.size() / 4))
    {
        Engine::bleedTransparentBgraEdgeColors(uint16_t(atlas.width), uint16_t(atlas.height), atlas.pixels);
    }
    return atlas;
}

// Mips that keep the contrast of fine detail at a distance: seen from afar or at a grazing angle, a surface uses levels
// a few steps down, where a plain average flattens cracks, pebbles, scales and cloth folds into their mean colour. Each
// level below the first gets an unsharp mask (strength x the difference from the 3x3 mean), in the semantic's
// filtering space. Terrain materials tile, so their neighbours wrap; model atlases clamp at the image edge and keep
// their filtered alpha (cutout coverage). prepareBgraMipChain built every level from the unsharpened one above, so the
// sharpening never compounds.
void sharpenMips(std::vector<Engine::BgraMipLevel> &chain, Engine::ImageMipSemantic semantic, float strength,
    bool tileable)
{
    const bool srgb = semantic == Engine::ImageMipSemantic::Srgb;
    const size_t channels = tileable ? 4 : 3;
    for (size_t level = 1; level < chain.size(); ++level)
    {
        Engine::BgraMipLevel &mip = chain[level];
        const int width = mip.width;
        const int height = mip.height;
        if (width < 4 || height < 4)
        {
            break;
        }
        std::vector<float> values(mip.pixels.size());
        for (size_t index = 0; index < values.size(); ++index)
        {
            const float value = mip.pixels[index] / 255.0f;
            values[index] = srgb && index % 4 < 3 ? Engine::srgbToLinear(value) : value;
        }
        for (int y = 0; y < height; ++y)
        {
            for (int x = 0; x < width; ++x)
            {
                for (size_t channel = 0; channel < channels; ++channel)
                {
                    const auto at = [&](int dx, int dy)
                    {
                        const int column = tileable ? (x + dx + width) % width : std::clamp(x + dx, 0, width - 1);
                        const int row = tileable ? (y + dy + height) % height : std::clamp(y + dy, 0, height - 1);
                        return values[(size_t(row) * width + column) * 4 + channel];
                    };
                    float neighbours = 0.0f;
                    for (int dy = -1; dy <= 1; ++dy)
                    {
                        for (int dx = -1; dx <= 1; ++dx)
                        {
                            neighbours += at(dx, dy);
                        }
                    }
                    const float centre = at(0, 0);
                    float value = std::clamp(centre + strength * (centre - neighbours / 9.0f), 0.0f, 1.0f);
                    if (srgb && channel < 3)
                    {
                        value = Engine::linearToSrgb(value);
                    }
                    mip.pixels[(size_t(y) * width + x) * 4 + channel] =
                        uint8_t(std::clamp(std::lround(value * 255.0f), 0L, 255L));
                }
            }
        }
    }
}

size_t cook(const Job &job)
{
    Engine::ImagePixelsBgra decoded;
    int contentWidth = 0;
    int contentHeight = 0;
    switch (job.kind)
    {
    case JobKind::Model:
    case JobKind::TerrainMaterial:
        decoded = decodeSource(job.input, {});
        resampleToPowerOfTwo(decoded, job.semantic, job.alphaCutoff);
        break;
    case JobKind::Surface:
    {
        // MapAssetLoader's world texture decode: only the magenta key, no palette-zero or teal key.
        Engine::ImageDecodeOptions options = {};
        options.applyMagentaTransparencyKey = true;
        decoded = decodeSource(job.input, options);
        if ((decoded.width & (decoded.width - 1)) != 0 || (decoded.height & (decoded.height - 1)) != 0)
        {
            throw std::runtime_error("Surface texture is not a power of two: " + job.input.string());
        }
        break;
    }
    case JobKind::Ui:
    {
        const Engine::ImagePixelsBgra image = decodeUiSource(job.input);
        contentWidth = image.width;
        contentHeight = image.height;
        // With mips the padding reaches the next power of two: NVIDIA's OpenGL 3.3 driver leaves a mipped
        // non-power-of-two block texture incomplete (it samples black), linear BC7 included.
        decoded.width = job.mips ? powerOfTwoAtLeast(image.width) : wholeBlocks(image.width);
        decoded.height = job.mips ? powerOfTwoAtLeast(image.height) : wholeBlocks(image.height);
        decoded.pixels.resize(size_t(decoded.width) * decoded.height * 4);
        placePadded(image, decoded.pixels, decoded.width, 0, 0, decoded.width, decoded.height);
        break;
    }
    case JobKind::UiAtlas:
        decoded = buildUiAtlas(job.input, contentWidth, contentHeight);
        break;
    case JobKind::EffectAtlas:
        decoded = buildEffectAtlas(job.input);
        break;
    }
    if (decoded.width > Engine::CookedTextureSizeLimit || decoded.height > Engine::CookedTextureSizeLimit)
    {
        throw std::runtime_error("Source image cannot fit the cooked size limit: " + job.input.string());
    }
    const Engine::CookedTextureStatistics statistics = Engine::measureCookedTextureStatistics(decoded.pixels);
    // The runtime's own filtering (sRGB/normal-aware, cutout coverage), then the largest levels above the cap dropped.
    std::vector<Engine::BgraMipLevel> chain = Engine::prepareBgraMipChain(uint16_t(decoded.width),
        uint16_t(decoded.height), decoded.pixels, job.alphaCutoff, job.semantic);
    if (job.kind == JobKind::TerrainMaterial)
    {
        // Strength 3 kept the most detail but shimmered at mid range while moving: the sharpened heights and normals
        // feed the shader's height blends and relighting. 1 keeps about three quarters of that detail with 40 % less
        // aliasing (level_generation/terrain/materials/README.md, "Sharpened mips").
        sharpenMips(chain, job.semantic, 1.0f, true);
    }
    else if (job.mipSharpening > 0.0f)
    {
        sharpenMips(chain, job.semantic, job.mipSharpening, false);
    }
    const auto first = std::find_if(chain.begin(), chain.end(), [&](const Engine::BgraMipLevel &level)
    {
        return std::max(level.width, level.height) <= job.maxSize;
    });
    if (first != chain.begin() && contentWidth != 0)
    {
        throw std::runtime_error("A padded texture cannot drop levels: " + job.input.string());
    }
    chain.erase(chain.begin(), first);
    if (chain.empty())
    {
        throw std::runtime_error("Source image cannot fit the cooked size limit: " + job.input.string());
    }
    if (!job.mips)
    {
        chain.resize(1);
    }
    Engine::CookedTexture texture;
    texture.codec = job.codec;
    texture.semantic = job.semantic;
    texture.alphaCutoff = job.alphaCutoff;
    texture.width = chain.front().width;
    texture.height = chain.front().height;
    texture.contentWidth = uint16_t(contentWidth);
    texture.contentHeight = uint16_t(contentHeight);
    texture.levels = uint8_t(chain.size());
    texture.sourceHash = job.sourceHash;
    texture.statistics = statistics;
    for (Engine::BgraMipLevel &level : chain)
    {
        for (size_t offset = 0; offset < level.pixels.size(); offset += 4)
        {
            std::swap(level.pixels[offset], level.pixels[offset + 2]);
        }
        const std::vector<uint8_t> blocks = Tools::encodeTextureBlocks(level.pixels, level.width, level.height,
            job.codec, {.linearChannels = job.linearChannels, .workers = 1});
        texture.blocks.insert(texture.blocks.end(), blocks.begin(), blocks.end());
    }
    const std::vector<uint8_t> bytes = Engine::encodeCookedTexture(texture);
    writeAtomically(job.output, bytes);
    return bytes.size();
}

int preview(const std::filesystem::path &input, const std::filesystem::path &output, int level)
{
    Engine::CookedTexture texture = Engine::decodeCookedTexture(read(input));
    if (level < 0 || level >= texture.levels)
    {
        throw std::runtime_error("No such mip level");
    }
    size_t offset = 0;
    for (int index = 0; index < level; ++index)
    {
        offset += Engine::textureBlockBytes(texture.codec, std::max(1, texture.width >> index),
            std::max(1, texture.height >> index));
    }
    texture.width = uint16_t(std::max(1, texture.width >> level));
    texture.height = uint16_t(std::max(1, texture.height >> level));
    const int width = (texture.width + 3) / 4 * 4;
    const int height = (texture.height + 3) / 4 * 4;
    std::vector<uint64_t> blocks(Engine::textureBlockBytes(texture.codec, width, height) / 8);
    std::memcpy(blocks.data(), texture.blocks.data() + offset, blocks.size() * 8);
    std::vector<uint32_t> pixels(size_t(width) * height, 0xff000000u);
    if (texture.codec == Engine::TextureBlockCodec::Astc4x4)
    {
        // bimg's decoder through the engine (BGRA out).
        Engine::CookedTexture level = texture;
        level.width = uint16_t(width);
        level.height = uint16_t(height);
        level.blocks.assign(reinterpret_cast<const uint8_t *>(blocks.data()),
            reinterpret_cast<const uint8_t *>(blocks.data()) + blocks.size() * 8);
        const std::vector<uint8_t> bgra = Engine::decodeCookedTextureRegionBgra(level, 0, 0, width, height);
        for (size_t texel = 0; texel < pixels.size(); ++texel)
        {
            pixels[texel] = uint32_t(bgra[texel * 4 + 2]) | (uint32_t(bgra[texel * 4 + 1]) << 8)
                | (uint32_t(bgra[texel * 4]) << 16) | (uint32_t(bgra[texel * 4 + 3]) << 24);
        }
    }
    else switch (texture.codec)
    {
    case Engine::TextureBlockCodec::Etc2Rgb: DecodeRGB(blocks.data(), pixels.data(), width, height); break;
    case Engine::TextureBlockCodec::Etc2Rgba: DecodeRGBA(blocks.data(), pixels.data(), width, height); break;
    case Engine::TextureBlockCodec::EacR: DecodeR(blocks.data(), pixels.data(), width, height); break;
    case Engine::TextureBlockCodec::EacRg: DecodeRG(blocks.data(), pixels.data(), width, height); break;
    default:
    {
        // BC blocks through bcdec, which follows the format's endpoint-order rules as GPUs do.
        const size_t blockBytes = Engine::textureBlockBytes(texture.codec, 4, 4);
        const uint8_t *pBlock = reinterpret_cast<const uint8_t *>(blocks.data());
        for (int y = 0; y < height; y += 4)
        {
            for (int x = 0; x < width; x += 4, pBlock += blockBytes)
            {
                uint32_t *pTarget = pixels.data() + size_t(y) * width + x;
                std::array<uint8_t, 4 * 4 * 2> channels = {};
                switch (texture.codec)
                {
                case Engine::TextureBlockCodec::Bc1: bcdec_bc1(pBlock, pTarget, width * 4); break;
                case Engine::TextureBlockCodec::Bc7: bcdec_bc7(pBlock, pTarget, width * 4); break;
                case Engine::TextureBlockCodec::Bc4: bcdec_bc4(pBlock, channels.data(), 4); break;
                case Engine::TextureBlockCodec::Bc5: bcdec_bc5(pBlock, channels.data(), 4 * 2); break;
                default: break;
                }
                if (texture.codec == Engine::TextureBlockCodec::Bc4 || texture.codec == Engine::TextureBlockCodec::Bc5)
                {
                    const bool two = texture.codec == Engine::TextureBlockCodec::Bc5;
                    for (int texel = 0; texel < 16; ++texel)
                    {
                        const uint32_t red = channels[texel * (two ? 2 : 1)];
                        const uint32_t green = two ? channels[texel * 2 + 1] : 0;
                        pTarget[size_t(texel / 4) * width + texel % 4] = red | (green << 8) | 0xff000000u;
                    }
                }
            }
        }
        break;
    }
    }
    std::vector<uint8_t> rgba(size_t(texture.width) * texture.height * 4);
    for (int y = 0; y < texture.height; ++y)
    {
        std::memcpy(rgba.data() + size_t(y) * texture.width * 4, pixels.data() + size_t(y) * width,
            size_t(texture.width) * 4);
    }
    writeAtomically(output, rgba);
    std::cout << texture.width << ' ' << texture.height << '\n';
    return 0;
}

// The version 2 container: the version 3 header, a byte-wise FNV-1a hash of the blocks in field 10, and a zstd frame
// without a checksum.
std::vector<uint8_t> rewrapVersion2(const std::vector<uint8_t> &bytes)
{
    constexpr size_t Fields = Engine::CookedTextureHeaderBytes / sizeof(uint64_t);
    uint64_t fields[Fields] = {};
    if (bytes.size() < Engine::CookedTextureHeaderBytes || !Engine::hasCookedTextureSignature(bytes))
    {
        throw std::runtime_error("not a cooked texture");
    }
    std::memcpy(fields, bytes.data(), Engine::CookedTextureHeaderBytes);
    if (fields[1] != 2)
    {
        throw std::runtime_error("version " + std::to_string(fields[1]) + " cannot be rewrapped; re-cook it");
    }
    if (fields[11] != bytes.size() - Engine::CookedTextureHeaderBytes || fields[9] > (size_t(1) << 32))
    {
        throw std::runtime_error("truncated or wrong size");
    }
    Engine::CookedTexture texture;
    texture.blocks.resize(fields[9]);
    const size_t size = ZSTD_decompress(texture.blocks.data(), texture.blocks.size(),
        bytes.data() + Engine::CookedTextureHeaderBytes, bytes.size() - Engine::CookedTextureHeaderBytes);
    uint64_t hash = 14695981039346656037ull;
    for (uint8_t byte : texture.blocks)
    {
        hash = (hash ^ byte) * 1099511628211ull;
    }
    if (ZSTD_isError(size) || size != texture.blocks.size() || hash != fields[10])
    {
        throw std::runtime_error("payload is corrupt");
    }
    static constexpr std::array<Engine::ImageMipSemantic, 3> Semantics = {
        Engine::ImageMipSemantic::Linear, Engine::ImageMipSemantic::Srgb, Engine::ImageMipSemantic::Normal};
    if (fields[3] < 1 || fields[3] > Semantics.size())
    {
        throw std::runtime_error("unknown semantic");
    }
    texture.codec = Engine::TextureBlockCodec(fields[2]);
    texture.semantic = Semantics[fields[3] - 1];
    texture.alphaCutoff = uint8_t(fields[4]);
    texture.width = uint16_t(fields[5]);
    texture.height = uint16_t(fields[6]);
    texture.levels = uint8_t(fields[7]);
    texture.sourceHash = fields[8];
    Engine::CookedTextureStatistics statistics;
    statistics.alphaUse = Engine::CookedTextureAlphaUse(fields[12]);
    for (size_t channel = 0; channel < 3; ++channel)
    {
        statistics.meanBgr256[channel] = uint16_t(fields[13] >> (16 * channel));
    }
    texture.statistics = statistics;
    texture.contentWidth = uint16_t(fields[14]);
    texture.contentHeight = uint16_t(fields[14] >> 16);
    std::vector<uint8_t> rewrapped = Engine::encodeCookedTexture(texture);
    if (Engine::decodeCookedTexture(rewrapped).blocks != texture.blocks)
    {
        throw std::runtime_error("rewrapped blocks differ");
    }
    return rewrapped;
}

int rewrap(const std::filesystem::path &listPath)
{
    std::vector<std::filesystem::path> paths;
    std::ifstream list(listPath);
    for (std::string line; std::getline(list, line);)
    {
        if (!line.empty())
        {
            paths.emplace_back(line);
        }
    }
    std::atomic<size_t> next = 0;
    std::atomic<int> failures = 0;
    std::mutex output;
    {
        std::vector<std::jthread> threads;
        const unsigned workers = std::max(1u, std::thread::hardware_concurrency());
        for (unsigned worker = 0; worker < std::min<size_t>(workers, paths.size()); ++worker)
        {
            threads.emplace_back([&]()
            {
                for (size_t index = next.fetch_add(1); index < paths.size(); index = next.fetch_add(1))
                {
                    const std::filesystem::path &path = paths[index];
                    try
                    {
                        const std::vector<uint8_t> bytes = read(path);
                        uint64_t version = 0;
                        if (bytes.size() >= 16)
                        {
                            std::memcpy(&version, bytes.data() + 8, sizeof(version));
                        }
                        const bool current = version == Engine::CookedTextureVersion;
                        if (current)
                        {
                            Engine::decodeCookedTexture(bytes);
                        }
                        else
                        {
                            writeAtomically(path, rewrapVersion2(bytes));
                        }
                        const std::lock_guard lock(output);
                        std::cout << (current ? "current\t" : "rewrapped\t") << path.string() << '\n';
                    }
                    catch (const std::exception &exception)
                    {
                        const std::lock_guard lock(output);
                        std::cerr << "Cannot rewrap " << path.string() << ": " << exception.what() << '\n';
                        ++failures;
                    }
                }
            });
        }
    }
    return failures == 0 ? 0 : 1;
}

int verify(int argc, char **argv)
{
    int failures = 0;
    for (int index = 2; index < argc; ++index)
    {
        try
        {
            const Engine::CookedTexture texture = Engine::decodeCookedTexture(read(argv[index]));
            std::cout << argv[index] << '\t' << Engine::textureBlockCodecName(texture.codec) << '\t'
                      << semanticName(texture.semantic) << '\t' << int(texture.alphaCutoff) << '\t' << texture.width
                      << '\t' << texture.height << '\t' << int(texture.levels) << '\t' << std::hex
                      << texture.sourceHash << std::dec << '\t'
                      << (texture.statistics ? std::to_string(int(texture.statistics->alphaUse)) : "-") << '\n';
        }
        catch (const std::exception &exception)
        {
            std::cerr << "Invalid cooked texture " << argv[index] << ": " << exception.what() << '\n';
            ++failures;
        }
    }
    return failures == 0 ? 0 : 1;
}
}

int main(int argc, char **argv)
{
    if (argc >= 3 && std::string(argv[1]) == "--verify")
    {
        return verify(argc, argv);
    }
    if (argc == 3 && std::string(argv[1]) == "--rewrap")
    {
        return rewrap(argv[2]);
    }
    if (argc == 4 && std::string(argv[1]) == "--geometry")
    {
        return Tools::cookModelGeometry(argv[2], argv[3]);
    }
    if ((argc == 4 || argc == 5) && std::string(argv[1]) == "--preview")
    {
        try
        {
            return preview(argv[2], argv[3], argc == 5 ? std::stoi(argv[4]) : 0);
        }
        catch (const std::exception &exception)
        {
            std::cerr << "Cannot preview " << argv[2] << ": " << exception.what() << '\n';
            return 1;
        }
    }
    if (argc != 2)
    {
        std::cerr << "Usage: openyamm_model_texture_cook <jobs.tsv> | --verify <file.oytex>... "
                     "| --preview <in.oytex> <out.rgba> [level] | --rewrap <list.txt> "
                     "| --geometry <request> <response>\n";
        return 2;
    }
    try
    {
        const std::vector<Job> jobs = parseJobs(argv[1]);
        std::atomic<size_t> next = 0;
        std::atomic<int> failures = 0;
        std::mutex output;
        std::vector<std::jthread> threads;
        const unsigned workers = std::max(1u, std::thread::hardware_concurrency());
        for (unsigned worker = 0; worker < std::min<size_t>(workers, jobs.size()); ++worker)
        {
            threads.emplace_back([&]()
            {
                for (size_t index = next.fetch_add(1); index < jobs.size(); index = next.fetch_add(1))
                {
                    try
                    {
                        const size_t bytes = cook(jobs[index]);
                        const std::lock_guard lock(output);
                        // Flushed per texture: tools/cook_models.py shows progress from these lines.
                        std::cout << "cooked\t" << jobs[index].output.string() << '\t' << bytes << '\n' << std::flush;
                    }
                    catch (const std::exception &exception)
                    {
                        const std::lock_guard lock(output);
                        std::cerr << "Cannot cook " << jobs[index].input.string() << ": " << exception.what() << '\n';
                        ++failures;
                    }
                }
            });
        }
        threads.clear();
        return failures == 0 ? 0 : 1;
    }
    catch (const std::exception &exception)
    {
        std::cerr << "Model texture cook failed: " << exception.what() << '\n';
        return 1;
    }
}
