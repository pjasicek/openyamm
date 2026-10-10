#include "tools/SpriteAtlasEncode.h"

#include "tools/TextureBlockEncode.h"

#include <array>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
std::vector<uint8_t> compress(const SpriteAtlasMipLevel &level, Engine::TextureBlockCodec codec, int channels, bool mask)
{
    std::vector<uint8_t> rgba(size_t(level.width) * level.height * 4);
    for (size_t source = 0; source < size_t(level.width) * level.height; ++source)
    {
        const std::array<uint8_t, 4> texel = mask
            ? std::array<uint8_t, 4>{level.mask[source * channels],
                channels >= 2 ? level.mask[source * channels + 1] : uint8_t(0),
                channels == 4 ? level.mask[source * channels + 2] : uint8_t(0),
                channels == 4 ? level.mask[source * channels + 3] : uint8_t(255)}
            : std::array<uint8_t, 4>{level.baseBgra[source * 4 + 2], level.baseBgra[source * 4 + 1],
                level.baseBgra[source * 4], level.baseBgra[source * 4 + 3]};
        std::copy(texel.begin(), texel.end(), rgba.begin() + source * 4);
    }
    // Mask channels are independent material weights, never coverage for one another.
    return Tools::encodeTextureBlocks(rgba, level.width, level.height, codec, {.linearChannels = mask});
}
}

PreparedSpriteAtlasPage compressSpriteAtlasPage(SpriteAtlasSourcePage source, int maskChannels,
    const std::string &profile)
{
    if ((profile != "desktop" && profile != "android") || (maskChannels != 1 && maskChannels != 2 && maskChannels != 4))
    {
        throw std::invalid_argument("Invalid sprite atlas texture profile or channels");
    }
    PreparedSpriteAtlasPage result;
    const bool desktop = profile == "desktop";
    result.baseCodec = desktop ? Engine::TextureBlockCodec::Bc7 : Engine::TextureBlockCodec::Etc2Rgba;
    result.maskCodec = maskChannels == 4 ? result.baseCodec
        : maskChannels == 2 ? (desktop ? Engine::TextureBlockCodec::Bc5 : Engine::TextureBlockCodec::EacRg)
        : (desktop ? Engine::TextureBlockCodec::Bc4 : Engine::TextureBlockCodec::EacR);
    result.rectangles = std::move(source.mips.rectangles);
    result.opacity = std::move(source.opacity);
    for (const SpriteAtlasMipLevel &level : source.mips.levels)
    {
        result.levels.push_back({level.width, level.height, compress(level, result.baseCodec, maskChannels, false),
            compress(level, result.maskCodec, maskChannels, true)});
    }
    return result;
}
}
