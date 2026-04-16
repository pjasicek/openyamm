#pragma once

#include <bgfx/bgfx.h>

#include <cstdint>

namespace OpenYAMM::Game
{
enum class TextureFilterProfile
{
    Terrain,
    BModel,
    Billboard,
    Ui,
    Text,
};

uint64_t textureFilterSamplerFlags(TextureFilterProfile profile);
bool textureFilteringEnabled();
void setTextureFilteringEnabled(bool enabled);
bool toggleTextureFilteringEnabled();
uint32_t textureBindingSamplerFlags(TextureFilterProfile profile, uint32_t extraFlags = BGFX_SAMPLER_NONE);
void bindTexture(
    uint8_t stage,
    bgfx::UniformHandle sampler,
    bgfx::TextureHandle textureHandle,
    TextureFilterProfile profile,
    uint32_t extraFlags = BGFX_SAMPLER_NONE);

bgfx::TextureHandle createBgraTexture2D(
    uint16_t width,
    uint16_t height,
    const uint8_t *pPixels,
    uint32_t pixelBytes,
    TextureFilterProfile profile,
    uint64_t extraFlags = BGFX_TEXTURE_NONE);

bgfx::TextureHandle createEmptyBgraTexture2D(
    uint16_t width,
    uint16_t height,
    TextureFilterProfile profile,
    uint64_t extraFlags = BGFX_TEXTURE_NONE);
}
