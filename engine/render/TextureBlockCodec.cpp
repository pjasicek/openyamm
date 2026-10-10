#include "engine/render/TextureBlockCodec.h"

#include <array>
#include <stdexcept>
#include <utility>

namespace OpenYAMM::Engine
{
namespace
{
constexpr std::array<std::pair<TextureBlockCodec, std::string_view>, 8> CodecNames = {{
    {TextureBlockCodec::Bc7, "bc7"},
    {TextureBlockCodec::Bc4, "bc4"},
    {TextureBlockCodec::Bc5, "bc5"},
    {TextureBlockCodec::Etc2Rgba, "etc2_rgba"},
    {TextureBlockCodec::EacR, "eac_r"},
    {TextureBlockCodec::EacRg, "eac_rg"},
    {TextureBlockCodec::Bc1, "bc1"},
    {TextureBlockCodec::Etc2Rgb, "etc2_rgb"},
}};
}

bgfx::TextureFormat::Enum textureBlockFormat(TextureBlockCodec codec)
{
    switch (codec)
    {
    case TextureBlockCodec::Bc7: return bgfx::TextureFormat::BC7;
    case TextureBlockCodec::Bc4: return bgfx::TextureFormat::BC4;
    case TextureBlockCodec::Bc5: return bgfx::TextureFormat::BC5;
    case TextureBlockCodec::Etc2Rgba: return bgfx::TextureFormat::ETC2A;
    case TextureBlockCodec::EacR: return bgfx::TextureFormat::EACR11;
    case TextureBlockCodec::EacRg: return bgfx::TextureFormat::EACRG11;
    case TextureBlockCodec::Bc1: return bgfx::TextureFormat::BC1;
    case TextureBlockCodec::Etc2Rgb: return bgfx::TextureFormat::ETC2;
    }
    throw std::runtime_error("Unknown texture block codec");
}

size_t textureBlockBytes(TextureBlockCodec codec, int width, int height)
{
    textureBlockFormat(codec);
    const bool halfBlocks = codec == TextureBlockCodec::Bc4 || codec == TextureBlockCodec::EacR
        || codec == TextureBlockCodec::Bc1 || codec == TextureBlockCodec::Etc2Rgb;
    return size_t((width + 3) / 4) * size_t((height + 3) / 4) * (halfBlocks ? 8 : 16);
}

std::string_view textureBlockCodecName(TextureBlockCodec codec)
{
    for (const auto &[candidate, name] : CodecNames)
    {
        if (candidate == codec)
        {
            return name;
        }
    }
    throw std::runtime_error("Unknown texture block codec");
}

std::optional<TextureBlockCodec> parseTextureBlockCodec(std::string_view name)
{
    for (const auto &[codec, candidate] : CodecNames)
    {
        if (candidate == name)
        {
            return codec;
        }
    }
    return std::nullopt;
}
}
