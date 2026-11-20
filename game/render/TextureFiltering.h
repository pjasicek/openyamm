#pragma once

#include "engine/ImageMipmaps.h"
#include "engine/render/CookedTexture.h"

#include <bgfx/bgfx.h>

#include <cstdint>
#include <span>
#include <vector>

namespace OpenYAMM::Game
{
enum class TextureFilterProfile
{
    Terrain,
    BModel,
    Lightmap,
    Sky,
    Billboard,
    Ui,
    UiIllustration,
    Text,
    SmoothText,
};

enum class TextureFilterMode
{
    Nearest,
    Linear,
    Anisotropic,
};

enum class BgraTexturePixelPreparation
{
    Required,
    AlreadyPrepared,
};

struct TextureFilteringConfig
{
    bool enabled = true;
    TextureFilterMode terrain = TextureFilterMode::Anisotropic;
    TextureFilterMode bmodel = TextureFilterMode::Anisotropic;
    TextureFilterMode sky = TextureFilterMode::Anisotropic;
    TextureFilterMode billboard = TextureFilterMode::Linear;
    TextureFilterMode ui = TextureFilterMode::Linear;
    TextureFilterMode text = TextureFilterMode::Nearest;
};

uint64_t textureFilterSamplerFlags(TextureFilterProfile profile);
bool textureFilteringEnabled();
void setTextureFilteringEnabled(bool enabled);
void setTextureFilteringConfig(const TextureFilteringConfig &config);
bool toggleTextureFilteringEnabled();
uint32_t textureBindingSamplerFlags(TextureFilterProfile profile, uint32_t extraFlags = BGFX_SAMPLER_NONE);
void bindTexture(
    uint8_t stage,
    bgfx::UniformHandle sampler,
    bgfx::TextureHandle textureHandle,
    TextureFilterProfile profile,
    uint32_t extraFlags = BGFX_SAMPLER_NONE);

bgfx::TextureFormat::Enum bgraTextureUploadFormat();
const bgfx::Memory *copyBgraTextureUploadMemory(const uint8_t *pPixels, uint32_t pixelBytes);

bool prepareBgraTexturePixelsForUploadInPlace(
    uint16_t width,
    uint16_t height,
    std::vector<uint8_t> &pixels,
    TextureFilterProfile profile);

bgfx::TextureHandle createBgraTexture2D(
    uint16_t width,
    uint16_t height,
    const uint8_t *pPixels,
    uint32_t pixelBytes,
    TextureFilterProfile profile,
    uint64_t extraFlags = BGFX_TEXTURE_NONE,
    BgraTexturePixelPreparation pixelPreparation = BgraTexturePixelPreparation::Required);

// createBgraTexture2D in two steps: the CPU work (transparent edge bleed, the profile's mip chain), safe on any
// thread, then the upload on the bgfx thread.
struct PreparedBgraTexture
{
    std::vector<Engine::BgraMipLevel> levels;
    bool mips = false;
};
PreparedBgraTexture prepareBgraTexture2D(
    uint16_t width,
    uint16_t height,
    const uint8_t *pPixels,
    uint32_t pixelBytes,
    TextureFilterProfile profile,
    BgraTexturePixelPreparation pixelPreparation = BgraTexturePixelPreparation::Required);
// Takes over the pixels instead of copying them.
PreparedBgraTexture prepareBgraTexture2D(
    uint16_t width,
    uint16_t height,
    std::vector<uint8_t> pixels,
    TextureFilterProfile profile,
    BgraTexturePixelPreparation pixelPreparation = BgraTexturePixelPreparation::Required);
bgfx::TextureHandle createPreparedBgraTexture2D(
    const PreparedBgraTexture &prepared, TextureFilterProfile profile, uint64_t extraFlags = BGFX_TEXTURE_NONE);
// Hands the prepared pixels to bgfx instead of copying them.
bgfx::TextureHandle createPreparedBgraTexture2D(
    PreparedBgraTexture &&prepared, TextureFilterProfile profile, uint64_t extraFlags = BGFX_TEXTURE_NONE);

// A cooked texture's blocks and stored mip chain as one 2D texture with the profile's sampler. Throws when the GPU
// cannot sample the codec (an asset package built for another platform's texture profile).
bgfx::TextureHandle createCookedTexture2D(
    const Engine::CookedTexture &texture, TextureFilterProfile profile, uint64_t extraFlags = BGFX_TEXTURE_NONE);

// Cooked textures of one codec, size and mip count as the layers of one 2D array texture.
bgfx::TextureHandle createCookedTexture2DArray(
    std::span<const Engine::CookedTexture *const> layers, TextureFilterProfile profile);

// A world surface texture from its cooked blocks when it has them, otherwise from its BGRA pixels.
bgfx::TextureHandle createSurfaceTexture2D(
    uint16_t width,
    uint16_t height,
    const std::vector<uint8_t> &pixels,
    const Engine::CookedTexture *pCookedTexture,
    TextureFilterProfile profile);

bgfx::TextureHandle createEmptyBgraTexture2D(
    uint16_t width,
    uint16_t height,
    TextureFilterProfile profile,
    uint64_t extraFlags = BGFX_TEXTURE_NONE);

using Engine::BgraMipLevel;
using Engine::prepareBgraMipChain;
using Engine::preserveBgraCutoutCoverage;
void updateBgraTextureArrayLayer(
    bgfx::TextureHandle texture, uint16_t layer, const std::vector<BgraMipLevel> &levels);

// Upload an independent mip chain into one array layer. Neighbouring terrain
// tiles must never contribute to this layer's lower-resolution images.
void updateBgraTextureArrayLayer(
    bgfx::TextureHandle texture,
    uint16_t layer,
    uint16_t width,
    uint16_t height,
    const std::vector<uint8_t> &pixels,
    uint8_t alphaCutoff = 0);
}
