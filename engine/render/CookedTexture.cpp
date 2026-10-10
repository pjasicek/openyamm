#include "engine/render/CookedTexture.h"

#include <zstd.h>

#include <algorithm>
#include <cstring>
#include <stdexcept>

namespace OpenYAMM::Engine
{
namespace
{
constexpr uint64_t Magic = 0x313030584554594full; // "OYTEX001" in file byte order.
constexpr size_t HeaderFields = CookedTextureHeaderBytes / sizeof(uint64_t);

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

uint64_t contentHash(std::span<const uint8_t> bytes)
{
    uint64_t hash = 14695981039346656037ull;
    for (uint8_t byte : bytes)
    {
        hash = (hash ^ byte) * 1099511628211ull;
    }
    return hash;
}
}

bool hasCookedTextureSignature(std::span<const uint8_t> bytes)
{
    uint64_t magic = 0;
    if (bytes.size() < sizeof(magic))
    {
        return false;
    }
    std::memcpy(&magic, bytes.data(), sizeof(magic));
    return magic == Magic;
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
        || texture.blocks.size() != cookedTextureBlockBytes(texture.codec, texture.width, texture.height,
            texture.levels))
    {
        throw std::invalid_argument("Invalid cooked texture layout");
    }
    std::vector<uint8_t> compressed(ZSTD_compressBound(texture.blocks.size()));
    const size_t size = ZSTD_compress(compressed.data(), compressed.size(), texture.blocks.data(),
        texture.blocks.size(), 19);
    if (ZSTD_isError(size))
    {
        throw std::runtime_error(ZSTD_getErrorName(size));
    }
    const uint64_t fields[HeaderFields] = {Magic, CookedTextureVersion, uint64_t(texture.codec),
        semanticId(texture.semantic), texture.alphaCutoff, texture.width, texture.height, texture.levels,
        texture.sourceHash, texture.blocks.size(), contentHash(texture.blocks), size};
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
    texture.levels = uint8_t(fields[7]);
    texture.sourceHash = fields[8];
    const size_t expected = cookedTextureBlockBytes(texture.codec, texture.width, texture.height, texture.levels);
    if (fields[9] != expected || fields[11] != bytes.size() - CookedTextureHeaderBytes)
    {
        throw std::runtime_error("cooked texture is truncated or has the wrong size");
    }
    texture.blocks.resize(expected);
    const size_t size = ZSTD_decompress(texture.blocks.data(), texture.blocks.size(),
        bytes.data() + CookedTextureHeaderBytes, bytes.size() - CookedTextureHeaderBytes);
    if (ZSTD_isError(size) || size != expected || contentHash(texture.blocks) != fields[10])
    {
        throw std::runtime_error("cooked texture payload is corrupt");
    }
    return texture;
}
}
