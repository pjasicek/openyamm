#pragma once

#include "engine/ImageMipmaps.h"
#include "engine/render/TextureBlockCodec.h"

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace OpenYAMM::Engine
{
// A cooked model texture (.oytex): one GPU block-compressed image with its mip chain, prepared offline by
// tools/cook_models.py from a source PNG with the runtime's own mip filtering (prepareBgraMipChain). The semantic and
// alpha cutoff it was filtered with are recorded, so a model can only use it the way it was cooked.
constexpr uint32_t CookedTextureVersion = 1;
constexpr size_t CookedTextureHeaderBytes = 96;
constexpr int CookedTextureSizeLimit = 8192;

struct CookedTexture
{
    TextureBlockCodec codec = TextureBlockCodec::Bc7;
    ImageMipSemantic semantic = ImageMipSemantic::Linear;
    uint8_t alphaCutoff = 0;
    uint16_t width = 0;
    uint16_t height = 0;
    // 1 (no mips) or the full chain down to 1x1, as bgfx expects for a mipped texture.
    uint8_t levels = 1;
    // Identity of the source image and cook decision (for receipts and diagnostics; not checked at runtime).
    uint64_t sourceHash = 0;
    // Every level's blocks, largest first, each textureBlockBytes(codec, level width, level height) long.
    std::vector<uint8_t> blocks;
};

bool hasCookedTextureSignature(std::span<const uint8_t> bytes);
uint8_t cookedTextureFullChainLevels(uint16_t width, uint16_t height);
size_t cookedTextureBlockBytes(TextureBlockCodec codec, uint16_t width, uint16_t height, uint8_t levels);
std::vector<uint8_t> encodeCookedTexture(const CookedTexture &texture);
// Throws on a truncated, corrupt, oversized or incompatible file. Never repairs or re-encodes.
CookedTexture decodeCookedTexture(std::span<const uint8_t> bytes);
}
