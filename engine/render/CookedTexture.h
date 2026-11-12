#pragma once

#include "engine/ImageMipmaps.h"
#include "engine/render/CookedTextureHeader.h"
#include "engine/render/TextureBlockCodec.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace OpenYAMM::Engine
{
// A cooked texture (.oytex): one GPU block-compressed image with its mip chain, prepared offline (model textures by
// tools/cook_models.py, world surface textures by tools/cook_surface_textures.py) from a source image with the
// runtime's own mip filtering (prepareBgraMipChain). The semantic and alpha cutoff it was filtered with are recorded,
// so a model can only use it the way it was cooked.
// Version 3 has the version 2 header (source statistics, content size) and verifies the payload with the zstd frame
// checksum while decompressing, instead of a byte-wise hash of the blocks; older versions are re-cooked
// (openyamm_model_texture_cook --rewrap migrates a version 2 file without re-encoding it).

enum class CookedTextureAlphaUse : uint8_t
{
    Opaque = 0,
    // Only fully transparent and fully opaque texels.
    Cutout = 1,
    // Some texels are partly transparent.
    Partial = 2,
};

// Measured on the full-size source pixels after keying, so a loader needs no pixels for them.
struct CookedTextureStatistics
{
    CookedTextureAlphaUse alphaUse = CookedTextureAlphaUse::Opaque;
    // Mean blue, green and red of all texels (alpha ignored), in 1/256 units.
    std::array<uint16_t, 3> meanBgr256 = {};
};

CookedTextureStatistics measureCookedTextureStatistics(std::span<const uint8_t> bgraPixels);

struct CookedTexture
{
    TextureBlockCodec codec = TextureBlockCodec::Bc7;
    ImageMipSemantic semantic = ImageMipSemantic::Linear;
    uint8_t alphaCutoff = 0;
    uint16_t width = 0;
    uint16_t height = 0;
    // The source image within the top level (texels [0, content) on each axis); the rest is padding up to whole 4x4
    // blocks, replicated from the content's edges, so sampling it with UVs scaled by content/size and clamp matches the
    // source. 0 means the whole level (and always for version 1).
    uint16_t contentWidth = 0;
    uint16_t contentHeight = 0;
    // 1 (no mips) or the full chain down to 1x1, as bgfx expects for a mipped texture.
    uint8_t levels = 1;
    // Identity of the source image and cook decision (for receipts and diagnostics; not checked at runtime).
    uint64_t sourceHash = 0;
    // Required by the encoder; always present in a decoded file.
    std::optional<CookedTextureStatistics> statistics;
    // Every level's blocks, largest first, each textureBlockBytes(codec, level width, level height) long.
    std::vector<uint8_t> blocks;
};

uint8_t cookedTextureFullChainLevels(uint16_t width, uint16_t height);
size_t cookedTextureBlockBytes(TextureBlockCodec codec, uint16_t width, uint16_t height, uint8_t levels);
std::vector<uint8_t> encodeCookedTexture(const CookedTexture &texture);
// Throws on a truncated, corrupt, oversized or incompatible file. Never repairs or re-encodes.
CookedTexture decodeCookedTexture(std::span<const uint8_t> bytes);
// The top level's blocks of a region whose corners lie on 4x4 block boundaries, row by row (a texture of their own).
std::vector<uint8_t> cookedTextureRegionBlocks(const CookedTexture &texture, int x, int y, int width, int height);
// The region's top-level texels decoded on the CPU to BGRA8 (for the rare CPU uses of cooked art; slow per texel).
std::vector<uint8_t> decodeCookedTextureRegionBgra(const CookedTexture &texture, int x, int y, int width, int height);
// A whole mip level decoded on the CPU to BGRA8, max(1, width >> level) by max(1, height >> level) texels.
std::vector<uint8_t> decodeCookedTextureLevelBgra(const CookedTexture &texture, uint8_t level);
}
