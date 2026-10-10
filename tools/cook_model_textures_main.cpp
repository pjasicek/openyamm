// Host-side model texture cooker: encodes source PNGs into cooked .oytex files with the runtime's own mip filtering.
// Driven by tools/cook_models.py, which owns the cook decisions; this tool only executes them.
//   openyamm_model_texture_cook <jobs.tsv>     one job per line, tab-separated:
//       input.png  output.oytex  codec  semantic(linear|srgb|normal)  alpha_cutoff  mips(0|1)  max_size
//       linear_channels(0|1)  source_hash(hex)
//   openyamm_model_texture_cook --verify <file.oytex>...   prints each file's header; fails on any invalid file
//   openyamm_model_texture_cook --preview <in.oytex> <out.rgba> [level]   decodes one mip level (default the
//       largest) to raw RGBA8 and prints "width height", for reviewing encoding artefacts
#include "engine/ImageAssetLoader.h"
#include "engine/ImageMipmaps.h"
#include "engine/render/CookedTexture.h"
#include "tools/TextureBlockEncode.h"

#include <Decode.hpp>
#include <bcdec.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <thread>

namespace
{
using namespace OpenYAMM;

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
        if (fields.size() != 9)
        {
            throw std::runtime_error("Job needs nine tab-separated fields: " + line);
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

size_t cook(const Job &job)
{
    const std::vector<uint8_t> source = read(job.input);
    std::optional<Engine::ImagePixelsBgra> decoded = Engine::decodeImagePixelsBgra(source, job.input.string());
    if (!decoded || decoded->width <= 0 || decoded->height <= 0 || decoded->width > 65535 || decoded->height > 65535)
    {
        throw std::runtime_error("Cannot decode source image: " + job.input.string());
    }
    resampleToPowerOfTwo(*decoded, job.semantic, job.alphaCutoff);
    // The runtime's own filtering (sRGB/normal-aware, cutout coverage), then the largest levels above the cap dropped.
    std::vector<Engine::BgraMipLevel> chain = Engine::prepareBgraMipChain(uint16_t(decoded->width),
        uint16_t(decoded->height), decoded->pixels, job.alphaCutoff, job.semantic);
    const auto first = std::find_if(chain.begin(), chain.end(), [&](const Engine::BgraMipLevel &level)
    {
        return std::max(level.width, level.height) <= job.maxSize;
    });
    chain.erase(chain.begin(), first);
    if (chain.empty() || chain.front().width > Engine::CookedTextureSizeLimit
        || chain.front().height > Engine::CookedTextureSizeLimit)
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
    texture.levels = uint8_t(chain.size());
    texture.sourceHash = job.sourceHash;
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
    switch (texture.codec)
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
                      << '\t' << texture.height << '\t' << int(texture.levels) << '\n';
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
                     "| --preview <in.oytex> <out.rgba> [level]\n";
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
                        std::cout << "cooked\t" << jobs[index].output.string() << '\t' << bytes << '\n';
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
