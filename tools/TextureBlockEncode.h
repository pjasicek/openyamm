#pragma once

#include "engine/render/TextureBlockCodec.h"

#include <cstdint>
#include <span>
#include <vector>

namespace OpenYAMM::Tools
{
struct TextureBlockEncodeOptions
{
    // Independent data channels (masks, metallic-roughness): linear BC7 weights and ETC2 alpha that is never coverage.
    // Otherwise colour: perceptual BC7 weights with alpha weighted like luminance, and ETC2 alpha as coverage.
    bool linearChannels = false;
    // Encoder threads for one image; 0 uses the hardware concurrency (at most eight).
    unsigned workers = 0;
};

// Host-only encoding of one tightly packed RGBA8 level of any size; partial blocks are padded by edge replication.
// Returns textureBlockBytes(codec, width, height) bytes. Throws when encoding fails.
std::vector<uint8_t> encodeTextureBlocks(std::span<const uint8_t> rgba, int width, int height,
    Engine::TextureBlockCodec codec, const TextureBlockEncodeOptions &options);
}
