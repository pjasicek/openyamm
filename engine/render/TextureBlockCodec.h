#pragma once

#include <bgfx/bgfx.h>

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace OpenYAMM::Engine
{
// GPU block-compressed texture encodings of cooked runtime files (sprite atlas pages, model textures).
// Stable on-disk ids; never serialize bgfx's enum ordinals.
enum class TextureBlockCodec : uint64_t
{
    Bc7 = 1,
    Bc4 = 2,
    Bc5 = 3,
    Etc2Rgba = 4,
    EacR = 5,
    EacRg = 6,
    Bc1 = 7,
    Etc2Rgb = 8
};

// Throws for an unknown codec id.
bgfx::TextureFormat::Enum textureBlockFormat(TextureBlockCodec codec);
// Bytes of one level: whole 4x4 blocks, so a 1x1 or 2x2 level still takes one block.
size_t textureBlockBytes(TextureBlockCodec codec, int width, int height);
std::string_view textureBlockCodecName(TextureBlockCodec codec);
std::optional<TextureBlockCodec> parseTextureBlockCodec(std::string_view name);
}
