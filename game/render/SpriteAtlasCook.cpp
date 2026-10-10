#include "game/render/SpriteAtlasCook.h"

#include <bx/hash.h>
#include <zstd.h>

#include <algorithm>
#include <cstring>
#include <map>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint64_t Magic = 0x3153414c5441594f;

void append(std::vector<uint8_t> &bytes, uint64_t value)
{
    for (int shift = 0; shift < 64; shift += 8)
    {
        bytes.push_back(uint8_t(value >> shift));
    }
}

class Reader
{
public:
    explicit Reader(std::span<const uint8_t> bytes) : m_bytes(bytes) {}

    std::span<const uint8_t> take(size_t size)
    {
        if (size > m_bytes.size())
        {
            throw std::runtime_error("Truncated cooked sprite atlas");
        }
        const std::span<const uint8_t> result = m_bytes.first(size);
        m_bytes = m_bytes.subspan(size);
        return result;
    }

    uint64_t integer()
    {
        const std::span<const uint8_t> bytes = take(8);
        uint64_t value = 0;
        for (int i = 0; i < 8; ++i)
        {
            value |= uint64_t(bytes[i]) << (8 * i);
        }
        return value;
    }

    int bounded(int maximum)
    {
        const uint64_t value = integer();
        if (value > uint64_t(maximum))
        {
            throw std::runtime_error("Invalid cooked sprite atlas dimensions or count");
        }
        return int(value);
    }

    std::vector<uint8_t> vector(size_t size)
    {
        const std::span<const uint8_t> bytes = take(size);
        return {bytes.begin(), bytes.end()};
    }

    std::span<const uint8_t> remaining() const { return m_bytes; }

private:
    std::span<const uint8_t> m_bytes;
};
}

size_t spriteAtlasBlockBytes(Engine::TextureBlockCodec codec, int width, int height)
{
    if (width <= 0 || height <= 0 || width > SpriteAtlasCookTextureLimit || height > SpriteAtlasCookTextureLimit)
    {
        throw std::runtime_error("Invalid cooked sprite texture dimensions");
    }
    return Engine::textureBlockBytes(codec, width, height);
}

size_t cookedSpriteAtlasPreparationBytes(std::span<const uint8_t> header, size_t fileBytes)
{
    if (fileBytes <= SpriteAtlasCookHeaderBytes || fileBytes > SpriteAtlasCookByteLimit)
    {
        throw std::runtime_error("Cooked sprite atlas exceeds page byte limit");
    }
    Reader reader(header);
    if (reader.integer() != Magic || reader.integer() != SpriteAtlasCookVersion)
    {
        throw std::runtime_error("Unsupported cooked sprite atlas; recook the source package");
    }
    reader.take(5 * 8);
    const uint64_t bodySize = reader.integer();
    reader.integer();
    if (bodySize == 0 || bodySize > SpriteAtlasCookByteLimit)
    {
        throw std::runtime_error("Cooked sprite atlas exceeds decompressed byte limit");
    }
    return fileBytes + size_t(bodySize) * 2;
}

uint64_t spriteAtlasContentHash(std::span<const uint8_t> bytes)
{
    if (bytes.size() > INT32_MAX)
    {
        throw std::runtime_error("Sprite atlas input exceeds size limit");
    }
    bx::HashMurmur3_64 hash;
    hash.begin();
    hash.add(bytes.data(), int32_t(bytes.size()));
    return hash.end();
}

std::string cookedSpriteAtlasPageName(int pageIndex)
{
    return "runtime/page-" + std::to_string(pageIndex) + ".oyatlas";
}

SpriteAtlasSourcePage prepareSpriteAtlasPage(const Engine::SpriteAtlas &atlas, int pageIndex,
    const Engine::ImagePixelsBgra &base, const Engine::ImagePixelsBgra &mask, int maxTextureSize)
{
    const Engine::SpriteAtlasPage &description = atlas.pages.at(pageIndex);
    if (base.width != description.size[0] || base.height != description.size[1]
        || mask.width != base.width || mask.height != base.height)
    {
        throw std::runtime_error("Atlas source dimensions do not match the manifest");
    }
    SpriteAtlasSourcePage result;
    result.mips = buildSpriteAtlasMipPage(atlas, pageIndex, base.pixels, mask.pixels, maxTextureSize);
    for (const auto &[name, frame] : atlas.frames)
    {
        if (frame.page == pageIndex)
        {
            const std::array<int, 4> &rect = frame.rectangle;
            result.opacity[name].assignFromBgraRegion(
                base.pixels, base.width, base.height, rect[0], rect[1], rect[2], rect[3]);
        }
    }
    return result;
}

std::vector<uint8_t> encodeCookedSpriteAtlasPage(const Engine::SpriteAtlas &atlas, int pageIndex,
    uint64_t manifestHash, const PreparedSpriteAtlasPage &page)
{
    std::vector<uint8_t> body;
    const std::map<std::string, std::array<int, 4>> ordered(page.rectangles.begin(), page.rectangles.end());
    append(body, ordered.size());
    for (const auto &[name, rect] : ordered)
    {
        append(body, name.size());
        body.insert(body.end(), name.begin(), name.end());
        for (int coordinate : rect)
        {
            append(body, coordinate);
        }
        const std::vector<uint8_t> &bits = page.opacity.at(name).bits();
        append(body, bits.size());
        body.insert(body.end(), bits.begin(), bits.end());
    }
    append(body, page.levels.size());
    for (const SpriteAtlasTextureLevel &level : page.levels)
    {
        append(body, level.width);
        append(body, level.height);
        body.insert(body.end(), level.baseBlocks.begin(), level.baseBlocks.end());
        body.insert(body.end(), level.maskBlocks.begin(), level.maskBlocks.end());
    }
    if (body.size() > SpriteAtlasCookByteLimit)
    {
        throw std::runtime_error("Cooked sprite atlas exceeds decompressed byte limit");
    }
    std::vector<uint8_t> compressed(ZSTD_compressBound(body.size()));
    const size_t size = ZSTD_compress(compressed.data(), compressed.size(), body.data(), body.size(), 9);
    if (ZSTD_isError(size))
    {
        throw std::runtime_error(ZSTD_getErrorName(size));
    }
    compressed.resize(size);
    std::vector<uint8_t> result;
    result.reserve(size + SpriteAtlasCookHeaderBytes);
    for (uint64_t value : {Magic, uint64_t(SpriteAtlasCookVersion), manifestHash, uint64_t(pageIndex),
             uint64_t(atlas.maskChannels), uint64_t(page.baseCodec), uint64_t(page.maskCodec),
             uint64_t(body.size()), spriteAtlasContentHash(body)})
    {
        append(result, value);
    }
    result.insert(result.end(), compressed.begin(), compressed.end());
    return result;
}

PreparedSpriteAtlasPage decodeCookedSpriteAtlasPage(std::span<const uint8_t> bytes,
    const Engine::SpriteAtlas &atlas, int pageIndex, uint64_t manifestHash, int maxTextureSize)
{
    cookedSpriteAtlasPreparationBytes(bytes, bytes.size());
    Reader header(bytes);
    if (header.integer() != Magic || header.integer() != SpriteAtlasCookVersion
        || header.integer() != manifestHash)
    {
        throw std::runtime_error("Incompatible/stale sprite atlas: recook the source package");
    }
    if (header.integer() != uint64_t(pageIndex) || header.integer() != uint64_t(atlas.maskChannels))
    {
        throw std::runtime_error("Cooked sprite atlas page/channel mismatch");
    }
    PreparedSpriteAtlasPage result;
    result.baseCodec = Engine::TextureBlockCodec(header.integer());
    result.maskCodec = Engine::TextureBlockCodec(header.integer());
    const bool desktop = atlas.textureProfile == "desktop";
    const Engine::TextureBlockCodec expectedMask = atlas.maskChannels == 4
        ? (desktop ? Engine::TextureBlockCodec::Bc7 : Engine::TextureBlockCodec::Etc2Rgba)
        : atlas.maskChannels == 2 ? (desktop ? Engine::TextureBlockCodec::Bc5 : Engine::TextureBlockCodec::EacRg)
        : (desktop ? Engine::TextureBlockCodec::Bc4 : Engine::TextureBlockCodec::EacR);
    if (atlas.schemaVersion != 2 || (atlas.textureProfile != "desktop" && atlas.textureProfile != "android")
        || result.baseCodec != (desktop ? Engine::TextureBlockCodec::Bc7 : Engine::TextureBlockCodec::Etc2Rgba)
        || result.maskCodec != expectedMask)
    {
        throw std::runtime_error("Cooked sprite atlas texture profile mismatch");
    }
    const size_t bodySize = size_t(header.integer());
    const uint64_t hash = header.integer();
    const std::span<const uint8_t> compressed = header.remaining();
    if (ZSTD_getFrameContentSize(compressed.data(), compressed.size()) != bodySize
        || ZSTD_findFrameCompressedSize(compressed.data(), compressed.size()) != compressed.size())
    {
        throw std::runtime_error("Invalid cooked sprite atlas Zstandard frame");
    }
    std::vector<uint8_t> body(bodySize);
    const size_t size = ZSTD_decompress(body.data(), body.size(), compressed.data(), compressed.size());
    if (ZSTD_isError(size) || size != bodySize || spriteAtlasContentHash(body) != hash)
    {
        throw std::runtime_error("Corrupt cooked sprite atlas payload");
    }
    Reader reader(body);
    const int frameCount = reader.bounded(int(atlas.frames.size()));
    size_t expectedFrames = 0;
    for (const auto &[name, frame] : atlas.frames)
    {
        expectedFrames += frame.page == pageIndex;
    }
    if (size_t(frameCount) != expectedFrames || frameCount == 0)
    {
        throw std::runtime_error("Cooked sprite atlas frame count mismatch");
    }
    for (int i = 0; i < frameCount; ++i)
    {
        const int length = reader.bounded(1024);
        const std::span<const uint8_t> nameBytes = reader.take(length);
        const std::string name(nameBytes.begin(), nameBytes.end());
        const auto frame = atlas.frames.find(name);
        if (frame == atlas.frames.end() || frame->second.page != pageIndex || result.opacity.contains(name))
        {
            throw std::runtime_error("Invalid cooked sprite atlas frame identity");
        }
        std::array<int, 4> rect;
        for (int &coordinate : rect)
        {
            coordinate = reader.bounded(maxTextureSize);
        }
        if (rect[2] != frame->second.rectangle[2] || rect[3] != frame->second.rectangle[3])
        {
            throw std::runtime_error("Cooked sprite atlas crop mismatch");
        }
        result.rectangles.emplace(name, rect);
        const size_t bitSize = (size_t(rect[2]) * rect[3] + 7) / 8;
        if (reader.integer() != bitSize || !result.opacity[name].assignBits(rect[2], rect[3], reader.vector(bitSize)))
        {
            throw std::runtime_error("Invalid cooked sprite opacity mask");
        }
    }
    if (reader.integer() != SpriteAtlasMaxMip + 1)
    {
        throw std::runtime_error("Cooked sprite atlas mip count mismatch");
    }
    for (int mip = 0; mip <= SpriteAtlasMaxMip; ++mip)
    {
        SpriteAtlasTextureLevel level;
        level.width = reader.bounded(maxTextureSize);
        level.height = reader.bounded(maxTextureSize);
        if (level.width == 0 || level.height == 0
            || (mip == 0 && (level.width % 16 != 0 || level.height % 16 != 0))
            || (mip > 0 && (level.width != result.levels.back().width / 2
                || level.height != result.levels.back().height / 2)))
        {
            throw std::runtime_error("Invalid cooked sprite atlas mip dimensions");
        }
        level.baseBlocks = reader.vector(spriteAtlasBlockBytes(result.baseCodec, level.width, level.height));
        level.maskBlocks = reader.vector(spriteAtlasBlockBytes(result.maskCodec, level.width, level.height));
        result.levels.push_back(std::move(level));
    }
    const SpriteAtlasTextureLevel &base = result.levels.front();
    for (const auto &[name, rect] : result.rectangles)
    {
        if (rect[0] < 16 || rect[1] < 16 || rect[0] + rect[2] > base.width - 16
            || rect[1] + rect[3] > base.height - 16)
        {
            throw std::runtime_error("Cooked sprite atlas crop lacks its sampling gutter");
        }
    }
    if (!reader.remaining().empty())
    {
        throw std::runtime_error("Unexpected trailing cooked sprite atlas data");
    }
    return result;
}
}
