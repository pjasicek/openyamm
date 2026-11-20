#include "tools/TextureBlockEncode.h"

#include <ProcessDxtc.hpp>
#include <ProcessRGB.hpp>
#include <astcenc.h>
#include <bc7enc.h>
#include <EtcImage.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cstring>
#include <mutex>
#include <stdexcept>
#include <thread>

namespace OpenYAMM::Tools
{
using Engine::TextureBlockCodec;

namespace
{
// etcpak can quantize both BC1 endpoints of a nearly uniform block to the same colour. c0 <= c1 selects BC1's
// three-colour mode, where index 3 is transparent black, so such blocks would decode with black holes (opaque
// sources never ask for transparency). Every block is rewritten in four-colour form (c0 > c1).
void forceOpaqueBc1(std::vector<uint64_t> &blocks)
{
    for (uint64_t &block : blocks)
    {
        const uint16_t c0 = uint16_t(block);
        const uint16_t c1 = uint16_t(block >> 16);
        if (c0 > c1)
        {
            continue;
        }
        if (c0 == c1)
        {
            // One colour: keep it as c0 with c1 one step below and every index 0, which decodes exactly c0. Black
            // instead becomes c1 (c0 one blue step above) with every index 1.
            block = c0 != 0 ? uint64_t(c0) | (uint64_t(c0 - 1) << 16) : 1ull | (0x55555555ull << 32);
            continue;
        }
        // c0 < c1: swap the endpoints (indices 0 <-> 1). The midpoint, and any transparent index, takes the third
        // nearer the old c0; both thirds are equally far from the midpoint.
        const uint32_t indices = uint32_t(block >> 32);
        uint32_t remapped = 0;
        for (int texel = 0; texel < 16; ++texel)
        {
            const uint32_t index = (indices >> (texel * 2)) & 3;
            remapped |= (index == 0 ? 1u : index == 1 ? 0u : 3u) << (texel * 2);
        }
        block = uint64_t(c1) | (uint64_t(c0) << 16) | (uint64_t(remapped) << 32);
    }
}
}

std::vector<uint8_t> encodeTextureBlocks(std::span<const uint8_t> rgba, int width, int height,
    TextureBlockCodec codec, const TextureBlockEncodeOptions &options)
{
    if (width <= 0 || height <= 0 || rgba.size() < size_t(width) * height * 4)
    {
        throw std::invalid_argument("Texture block input is smaller than its dimensions");
    }
    static std::once_flag initialize;
    std::call_once(initialize, bc7enc_compress_block_init);
    const int paddedWidth = (width + 3) / 4 * 4;
    const int paddedHeight = (height + 3) / 4 * 4;
    // etcpak's EAC input is BGRA; BC and Etc2Comp input is RGBA.
    const bool bgra = codec == TextureBlockCodec::EacR || codec == TextureBlockCodec::EacRg;
    std::vector<uint32_t> pixels(size_t(paddedWidth) * paddedHeight);
    for (int y = 0; y < paddedHeight; ++y)
    {
        for (int x = 0; x < paddedWidth; ++x)
        {
            const size_t source = (size_t(std::min(y, height - 1)) * width + std::min(x, width - 1)) * 4;
            std::array<uint8_t, 4> texel = {rgba[source], rgba[source + 1], rgba[source + 2], rgba[source + 3]};
            if (bgra)
            {
                std::swap(texel[0], texel[2]);
            }
            std::memcpy(&pixels[size_t(y) * paddedWidth + x], texel.data(), 4);
        }
    }
    const size_t bytes = Engine::textureBlockBytes(codec, paddedWidth, paddedHeight);
    const unsigned workers = options.workers != 0 ? options.workers
        : std::clamp(std::thread::hardware_concurrency(), 1u, 8u);
    if (codec == TextureBlockCodec::Astc4x4)
    {
        // Arm's reference encoder (bimg's copy), LDR profile on raw texel values: the same sampling as BGRA8/BC7.
        astcenc_config config = {};
        // The default error metric weighs the four channels independently, as data channels need.
        if (astcenc_config_init(ASTCENC_PRF_LDR, 4, 4, 1, ASTCENC_PRE_MEDIUM, 0, &config) != ASTCENC_SUCCESS)
        {
            throw std::runtime_error("ASTC encoder configuration failed");
        }
        astcenc_context *pContext = nullptr;
        if (astcenc_context_alloc(&config, workers, &pContext) != ASTCENC_SUCCESS)
        {
            throw std::runtime_error("ASTC encoder allocation failed");
        }
        void *pSlices[1] = {pixels.data()};
        astcenc_image image = {};
        image.dim_x = unsigned(paddedWidth);
        image.dim_y = unsigned(paddedHeight);
        image.dim_z = 1;
        image.data_type = ASTCENC_TYPE_U8;
        image.data = pSlices;
        const astcenc_swizzle swizzle = {ASTCENC_SWZ_R, ASTCENC_SWZ_G, ASTCENC_SWZ_B, ASTCENC_SWZ_A};
        std::vector<uint8_t> result(bytes);
        std::atomic<bool> failed = false;
        // std::thread rather than std::jthread: libc++ (Android's NDK, Apple's Xcode) keeps jthread behind its
        // experimental flag.
        std::vector<std::thread> threads;
        for (unsigned thread = 0; thread < workers; ++thread)
        {
            threads.emplace_back([&, thread]()
            {
                if (astcenc_compress_image(pContext, &image, &swizzle, result.data(), result.size(), thread)
                    != ASTCENC_SUCCESS)
                {
                    failed = true;
                }
            });
        }
        for (std::thread &thread : threads)
        {
            thread.join();
        }
        astcenc_context_free(pContext);
        if (failed)
        {
            throw std::runtime_error("ASTC texture encoding failed");
        }
        return result;
    }
    if (codec == TextureBlockCodec::Etc2Rgba || codec == TextureBlockCodec::Etc2Rgb)
    {
        std::vector<float> channels(pixels.size() * 4);
        const uint8_t *pBytes = reinterpret_cast<const uint8_t *>(pixels.data());
        for (size_t i = 0; i < channels.size(); ++i)
        {
            channels[i] = pBytes[i] / 255.0f;
        }
        const Etc::ErrorMetric metric = options.linearChannels || codec == TextureBlockCodec::Etc2Rgb
            ? Etc::ErrorMetric::RGBX : Etc::ErrorMetric::RGBA;
        const Etc::Image::Format format = codec == TextureBlockCodec::Etc2Rgba ? Etc::Image::Format::RGBA8
            : Etc::Image::Format::RGB8;
        Etc::Image image(channels.data(), paddedWidth, paddedHeight, metric);
        const Etc::Image::EncodingStatus status = image.Encode(format, metric, 80, workers, workers);
        if (status >= Etc::Image::ERROR_THRESHOLD || image.GetEncodingBitsBytes() != bytes)
        {
            throw std::runtime_error("ETC2 texture encoding failed");
        }
        return {image.GetEncodingBits(), image.GetEncodingBits() + bytes};
    }
    std::vector<uint64_t> blocks(bytes / 8);
    bc7enc_compress_block_params parameters;
    bc7enc_compress_block_params_init(&parameters);
    parameters.m_uber_level = 2;
    if (options.linearChannels)
    {
        bc7enc_compress_block_params_init_linear_weights(&parameters);
    }
    else
    {
        // Preserve silhouette/soft coverage as carefully as luminance.
        parameters.m_weights[3] = 128;
    }
    const int rows = paddedHeight / 4;
    std::atomic<int> next = 0;
    std::vector<std::thread> threads;
    for (size_t i = 0; i < std::min(size_t(rows), size_t(workers)); ++i)
    {
        threads.emplace_back([&]()
        {
            for (int row = next.fetch_add(1); row < rows; row = next.fetch_add(1))
            {
                const uint32_t *pSource = pixels.data() + size_t(row) * paddedWidth * 4;
                uint64_t *pTarget = blocks.data() + size_t(row) * (blocks.size() / rows);
                const uint32_t count = uint32_t(paddedWidth / 4);
                switch (codec)
                {
                case TextureBlockCodec::Bc7: CompressBc7(pSource, pTarget, count, paddedWidth, &parameters); break;
                case TextureBlockCodec::Bc4: CompressBc4(pSource, pTarget, count, paddedWidth); break;
                case TextureBlockCodec::Bc5: CompressBc5(pSource, pTarget, count, paddedWidth); break;
                case TextureBlockCodec::Bc1: CompressBc1(pSource, pTarget, count, paddedWidth); break;
                case TextureBlockCodec::EacR: CompressEacR(pSource, pTarget, count, paddedWidth); break;
                case TextureBlockCodec::EacRg: CompressEacRg(pSource, pTarget, count, paddedWidth); break;
                case TextureBlockCodec::Etc2Rgba:
                case TextureBlockCodec::Etc2Rgb:
                case TextureBlockCodec::Astc4x4: break; // Encoded above with their own encoders.
                }
            }
        });
    }
    for (std::thread &thread : threads)
    {
        thread.join();
    }
    if (codec == TextureBlockCodec::Bc1)
    {
        forceOpaqueBc1(blocks);
    }
    std::vector<uint8_t> result(bytes);
    std::memcpy(result.data(), blocks.data(), bytes);
    return result;
}
}
