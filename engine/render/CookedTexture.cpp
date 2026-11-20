#include "engine/render/CookedTexture.h"

#include <bimg/bimg.h>
#include <bx/allocator.h>
#include <zstd.h>

#include <algorithm>
#include <cstring>
#include <stdexcept>

namespace OpenYAMM::Engine
{
namespace
{
constexpr size_t HeaderFields = CookedTextureHeaderBytes / sizeof(uint64_t);
constexpr int CompressionLevel = 19;

uint64_t packStatistics(const CookedTextureStatistics &statistics)
{
    return uint64_t(statistics.meanBgr256[0]) | (uint64_t(statistics.meanBgr256[1]) << 16)
        | (uint64_t(statistics.meanBgr256[2]) << 32);
}

// Stable on-disk semantic ids; never serialize the enum's ordinals.
uint64_t semanticId(ImageMipSemantic semantic)
{
    switch (semantic)
    {
    case ImageMipSemantic::Linear: return 1;
    case ImageMipSemantic::Srgb: return 2;
    case ImageMipSemantic::Normal: return 3;
    }
    throw std::invalid_argument("Unknown cooked texture semantic");
}

// RFC 8878: a zstd frame starts with its magic number, then the frame header descriptor, whose bit 2 is the
// Content_Checksum_flag.
bool hasZstdFrameChecksum(std::span<const uint8_t> frame)
{
    constexpr uint32_t ZstdFrameMagic = 0xFD2FB528u;
    if (frame.size() < 5)
    {
        return false;
    }
    uint32_t magic = 0;
    std::memcpy(&magic, frame.data(), sizeof(magic));
    return magic == ZstdFrameMagic && (frame[4] & 0x04) != 0;
}

ImageMipSemantic semanticFromId(uint64_t id)
{
    switch (id)
    {
    case 1: return ImageMipSemantic::Linear;
    case 2: return ImageMipSemantic::Srgb;
    case 3: return ImageMipSemantic::Normal;
    }
    throw std::runtime_error("cooked texture header names an unknown semantic");
}

}

CookedTextureStatistics measureCookedTextureStatistics(std::span<const uint8_t> bgraPixels)
{
    if (bgraPixels.empty() || bgraPixels.size() % 4 != 0)
    {
        throw std::invalid_argument("Invalid cooked texture statistics pixels");
    }
    CookedTextureStatistics statistics;
    uint64_t sums[3] = {};
    for (size_t offset = 0; offset < bgraPixels.size(); offset += 4)
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            sums[channel] += bgraPixels[offset + channel];
        }
        const uint8_t alpha = bgraPixels[offset + 3];
        if (alpha > 0 && alpha < 255)
        {
            statistics.alphaUse = CookedTextureAlphaUse::Partial;
        }
        else if (alpha == 0 && statistics.alphaUse == CookedTextureAlphaUse::Opaque)
        {
            statistics.alphaUse = CookedTextureAlphaUse::Cutout;
        }
    }
    const uint64_t texels = bgraPixels.size() / 4;
    for (size_t channel = 0; channel < 3; ++channel)
    {
        statistics.meanBgr256[channel] = uint16_t((sums[channel] * 256 + texels / 2) / texels);
    }
    return statistics;
}

uint8_t cookedTextureFullChainLevels(uint16_t width, uint16_t height)
{
    uint8_t levels = 1;
    for (uint16_t size = std::max(width, height); size > 1; size /= 2)
    {
        ++levels;
    }
    return levels;
}

size_t cookedTextureBlockBytes(TextureBlockCodec codec, uint16_t width, uint16_t height, uint8_t levels)
{
    size_t bytes = 0;
    for (uint8_t level = 0; level < levels; ++level)
    {
        bytes += textureBlockBytes(codec, std::max(1, width >> level), std::max(1, height >> level));
    }
    return bytes;
}

std::vector<uint8_t> encodeCookedTexture(const CookedTexture &texture)
{
    if (texture.width == 0 || texture.height == 0 || texture.width > CookedTextureSizeLimit
        || texture.height > CookedTextureSizeLimit
        || (texture.levels != 1 && texture.levels != cookedTextureFullChainLevels(texture.width, texture.height))
        || (texture.levels != 1 && (texture.width < 4 || texture.height < 4))
        || texture.blocks.size() != cookedTextureBlockBytes(texture.codec, texture.width, texture.height,
            texture.levels))
    {
        throw std::invalid_argument("Invalid cooked texture layout");
    }
    std::vector<uint8_t> compressed(ZSTD_compressBound(texture.blocks.size()));
    ZSTD_CCtx *pContext = ZSTD_createCCtx();
    if (pContext == nullptr)
    {
        throw std::runtime_error("Cannot create a zstd compression context");
    }
    // The frame checksum (XXH64) is the payload's integrity check; the decoder verifies it while decompressing.
    ZSTD_CCtx_setParameter(pContext, ZSTD_c_compressionLevel, CompressionLevel);
    ZSTD_CCtx_setParameter(pContext, ZSTD_c_checksumFlag, 1);
    const size_t size = ZSTD_compress2(pContext, compressed.data(), compressed.size(), texture.blocks.data(),
        texture.blocks.size());
    ZSTD_freeCCtx(pContext);
    if (ZSTD_isError(size))
    {
        throw std::runtime_error(ZSTD_getErrorName(size));
    }
    if (!texture.statistics)
    {
        throw std::invalid_argument("A cooked texture needs its source statistics");
    }
    if (texture.contentWidth > texture.width || texture.contentHeight > texture.height
        || (texture.contentWidth == 0) != (texture.contentHeight == 0))
    {
        throw std::invalid_argument("Invalid cooked texture content size");
    }
    const uint64_t fields[HeaderFields] = {CookedTextureMagic, CookedTextureVersion, uint64_t(texture.codec),
        semanticId(texture.semantic), texture.alphaCutoff, texture.width, texture.height, texture.levels,
        texture.sourceHash, texture.blocks.size(), 0 /* the version 2 content hash, unused */, size,
        uint64_t(texture.statistics->alphaUse), packStatistics(*texture.statistics),
        uint64_t(texture.contentWidth) | (uint64_t(texture.contentHeight) << 16)};
    std::vector<uint8_t> result(CookedTextureHeaderBytes + size);
    std::memcpy(result.data(), fields, CookedTextureHeaderBytes);
    std::memcpy(result.data() + CookedTextureHeaderBytes, compressed.data(), size);
    return result;
}

CookedTexture decodeCookedTexture(std::span<const uint8_t> bytes)
{
    if (bytes.size() < CookedTextureHeaderBytes || !hasCookedTextureSignature(bytes))
    {
        throw std::runtime_error("not a cooked texture");
    }
    uint64_t fields[HeaderFields] = {};
    std::memcpy(fields, bytes.data(), CookedTextureHeaderBytes);
    if (fields[1] != CookedTextureVersion)
    {
        throw std::runtime_error("cooked texture version " + std::to_string(fields[1]) + " is not "
            + std::to_string(CookedTextureVersion) + "; re-cook it");
    }
    const size_t headerBytes = CookedTextureHeaderBytes;
    CookedTexture texture;
    texture.codec = TextureBlockCodec(fields[2]);
    textureBlockFormat(texture.codec);
    if (fields[4] > 255 || fields[5] == 0 || fields[6] == 0
        || fields[5] > CookedTextureSizeLimit || fields[6] > CookedTextureSizeLimit)
    {
        throw std::runtime_error("cooked texture header is invalid");
    }
    texture.semantic = semanticFromId(fields[3]);
    texture.alphaCutoff = uint8_t(fields[4]);
    texture.width = uint16_t(fields[5]);
    texture.height = uint16_t(fields[6]);
    if (fields[7] != 1 && fields[7] != cookedTextureFullChainLevels(texture.width, texture.height))
    {
        throw std::runtime_error("cooked texture mip chain is incomplete");
    }
    // bgfx counts a block-compressed texture's mips from its size rounded up to whole 4x4 blocks, so a smaller
    // mipped texture would be read past its end; the cooker never writes one.
    if (fields[7] != 1 && (texture.width < 4 || texture.height < 4))
    {
        throw std::runtime_error("cooked texture is mipped but smaller than one 4x4 block; cook it again");
    }
    texture.levels = uint8_t(fields[7]);
    texture.sourceHash = fields[8];
    if (fields[12] > uint64_t(CookedTextureAlphaUse::Partial) || (fields[13] >> 48) != 0)
    {
        throw std::runtime_error("cooked texture statistics are invalid");
    }
    CookedTextureStatistics statistics;
    statistics.alphaUse = CookedTextureAlphaUse(fields[12]);
    for (size_t channel = 0; channel < 3; ++channel)
    {
        statistics.meanBgr256[channel] = uint16_t(fields[13] >> (16 * channel));
    }
    texture.statistics = statistics;
    texture.contentWidth = uint16_t(fields[14]);
    texture.contentHeight = uint16_t(fields[14] >> 16);
    if ((fields[14] >> 32) != 0 || texture.contentWidth > texture.width || texture.contentHeight > texture.height
        || (texture.contentWidth == 0) != (texture.contentHeight == 0))
    {
        throw std::runtime_error("cooked texture content size is invalid");
    }
    const size_t expected = cookedTextureBlockBytes(texture.codec, texture.width, texture.height, texture.levels);
    if (fields[9] != expected || fields[11] != bytes.size() - headerBytes)
    {
        throw std::runtime_error("cooked texture is truncated or has the wrong size");
    }
    // Without the frame checksum the payload would go unverified.
    if (!hasZstdFrameChecksum(bytes.subspan(headerBytes)))
    {
        throw std::runtime_error("cooked texture payload has no zstd frame checksum");
    }
    texture.blocks.resize(expected);
    const size_t size = ZSTD_decompress(texture.blocks.data(), texture.blocks.size(),
        bytes.data() + headerBytes, bytes.size() - headerBytes);
    if (ZSTD_isError(size) || size != expected)
    {
        throw std::runtime_error("cooked texture payload is corrupt");
    }
    return texture;
}

std::vector<uint8_t> cookedTextureRegionBlocks(const CookedTexture &texture, int x, int y, int width, int height)
{
    if (x < 0 || y < 0 || width <= 0 || height <= 0 || x % 4 != 0 || y % 4 != 0 || width % 4 != 0
        || height % 4 != 0 || x + width > (texture.width + 3) / 4 * 4 || y + height > (texture.height + 3) / 4 * 4)
    {
        throw std::invalid_argument("Cooked texture region is not block aligned or exceeds the texture");
    }
    const size_t blockBytes = textureBlockBytes(texture.codec, 4, 4);
    const size_t sourceRowBytes = size_t((texture.width + 3) / 4) * blockBytes;
    const size_t rowBytes = size_t(width / 4) * blockBytes;
    std::vector<uint8_t> blocks(rowBytes * size_t(height / 4));
    for (int row = 0; row < height / 4; ++row)
    {
        std::memcpy(blocks.data() + row * rowBytes,
            texture.blocks.data() + size_t(y / 4 + row) * sourceRowBytes + size_t(x / 4) * blockBytes, rowBytes);
    }
    return blocks;
}

std::vector<uint8_t> decodeCookedTextureRegionBgra(const CookedTexture &texture, int x, int y, int width, int height)
{
    const std::vector<uint8_t> blocks = cookedTextureRegionBlocks(texture, x, y, width, height);
    std::vector<uint8_t> pixels(size_t(width) * height * 4);
    bx::DefaultAllocator allocator;
    // bimg's formats share bgfx's ordinals.
    bimg::imageDecodeToBgra8(&allocator, pixels.data(), blocks.data(), uint32_t(width), uint32_t(height),
        uint32_t(width) * 4, bimg::TextureFormat::Enum(textureBlockFormat(texture.codec)));
    return pixels;
}

std::vector<uint8_t> decodeCookedTextureLevelBgra(const CookedTexture &texture, uint8_t level)
{
    if (level >= texture.levels)
    {
        throw std::invalid_argument("Cooked texture has no such mip level");
    }
    size_t offset = 0;
    for (uint8_t index = 0; index < level; ++index)
    {
        offset += textureBlockBytes(texture.codec, std::max(1, texture.width >> index),
            std::max(1, texture.height >> index));
    }
    const int width = std::max(1, texture.width >> level);
    const int height = std::max(1, texture.height >> level);
    // The decoder writes whole 4x4 blocks.
    const int paddedWidth = (width + 3) / 4 * 4;
    const int paddedHeight = (height + 3) / 4 * 4;
    std::vector<uint8_t> padded(size_t(paddedWidth) * paddedHeight * 4);
    bx::DefaultAllocator allocator;
    bimg::imageDecodeToBgra8(&allocator, padded.data(), texture.blocks.data() + offset, uint32_t(paddedWidth),
        uint32_t(paddedHeight), uint32_t(paddedWidth) * 4, bimg::TextureFormat::Enum(textureBlockFormat(texture.codec)));
    std::vector<uint8_t> pixels(size_t(width) * height * 4);
    for (int row = 0; row < height; ++row)
    {
        std::memcpy(pixels.data() + size_t(row) * width * 4, padded.data() + size_t(row) * paddedWidth * 4,
            size_t(width) * 4);
    }
    return pixels;
}
}
