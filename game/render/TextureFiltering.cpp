#include "game/render/TextureFiltering.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
bool g_textureFilteringEnabled = true;
TextureFilteringConfig g_textureFilteringConfig = {};

bool profileUsesMipmaps(TextureFilterProfile profile)
{
    // Smooth text atlases are rasterized at four times the logical size; without mips, small labels alias.
    return profile == TextureFilterProfile::Terrain
        || profile == TextureFilterProfile::BModel
        || profile == TextureFilterProfile::Sky
        || profile == TextureFilterProfile::UiIllustration
        || profile == TextureFilterProfile::SmoothText;
}

bool profileNeedsTransparentEdgeBleed(TextureFilterProfile profile)
{
    switch (profile)
    {
        case TextureFilterProfile::Billboard:
        case TextureFilterProfile::Ui:
        case TextureFilterProfile::UiIllustration:
            return true;

        case TextureFilterProfile::Terrain:
        case TextureFilterProfile::BModel:
        case TextureFilterProfile::Lightmap:
        case TextureFilterProfile::Sky:
        case TextureFilterProfile::Text:
        case TextureFilterProfile::SmoothText:
            return false;
    }

    return false;
}

TextureFilterMode textureFilterModeForProfile(TextureFilterProfile profile)
{
    switch (profile)
    {
        case TextureFilterProfile::Terrain:
            return g_textureFilteringConfig.terrain;

        case TextureFilterProfile::BModel:
            return g_textureFilteringConfig.bmodel;

        case TextureFilterProfile::Lightmap:
            return g_textureFilteringConfig.bmodel;

        case TextureFilterProfile::Sky:
            return g_textureFilteringConfig.sky;

        case TextureFilterProfile::Billboard:
            return g_textureFilteringConfig.billboard;

        case TextureFilterProfile::Ui:
        case TextureFilterProfile::UiIllustration:
            return g_textureFilteringConfig.ui;

        case TextureFilterProfile::Text:
            return g_textureFilteringConfig.text;

        case TextureFilterProfile::SmoothText:
            return TextureFilterMode::Linear;
    }

    return TextureFilterMode::Linear;
}

uint64_t textureFilterSamplerFlagsForMode(TextureFilterMode mode)
{
    switch (mode)
    {
        case TextureFilterMode::Nearest:
            return BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT;

        case TextureFilterMode::Linear:
            return BGFX_SAMPLER_NONE;

        case TextureFilterMode::Anisotropic:
            return BGFX_SAMPLER_MIN_ANISOTROPIC | BGFX_SAMPLER_MAG_ANISOTROPIC;
    }

    return BGFX_SAMPLER_NONE;
}

std::vector<uint8_t> convertBgraToRgba(const uint8_t *pPixels, uint32_t pixelBytes)
{
    std::vector<uint8_t> rgbaPixels(pixelBytes);

    for (uint32_t byteOffset = 0; byteOffset + 3 < pixelBytes; byteOffset += 4)
    {
        rgbaPixels[byteOffset + 0] = pPixels[byteOffset + 2];
        rgbaPixels[byteOffset + 1] = pPixels[byteOffset + 1];
        rgbaPixels[byteOffset + 2] = pPixels[byteOffset + 0];
        rgbaPixels[byteOffset + 3] = pPixels[byteOffset + 3];
    }

    return rgbaPixels;
}

// Hands the pixels to bgfx instead of copying them; bgfx frees them once uploaded. Large atlases spend more time in
// the copy than in their mip chain.
const bgfx::Memory *takeBgraTextureUploadMemory(std::vector<uint8_t> &&pixels)
{
    if (pixels.empty())
    {
        return nullptr;
    }

#if defined(__ANDROID__)
    std::vector<uint8_t> rgbaPixels = convertBgraToRgba(pixels.data(), static_cast<uint32_t>(pixels.size()));
    pixels = std::move(rgbaPixels);
#endif
    std::unique_ptr<std::vector<uint8_t>> pOwned = std::make_unique<std::vector<uint8_t>>(std::move(pixels));
    const bgfx::Memory *pMemory = bgfx::makeRef(
        pOwned->data(),
        static_cast<uint32_t>(pOwned->size()),
        [](void *, void *pUserData)
        {
            std::unique_ptr<std::vector<uint8_t>>(static_cast<std::vector<uint8_t> *>(pUserData));
        },
        pOwned.get());
    pOwned.release();
    return pMemory;
}

// Consumes the levels' pixels once the texture exists.
bgfx::TextureHandle createBgraTextureWithMipChain(
    std::vector<BgraMipLevel> &mipLevels,
    TextureFilterProfile profile,
    uint64_t extraFlags)
{
    if (mipLevels.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const bgfx::TextureHandle textureHandle = bgfx::createTexture2D(
        mipLevels.front().width,
        mipLevels.front().height,
        true,
        1,
        bgraTextureUploadFormat(),
        textureFilterSamplerFlags(profile) | extraFlags);

    if (!bgfx::isValid(textureHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    for (uint8_t mipLevelIndex = 0; mipLevelIndex < mipLevels.size(); ++mipLevelIndex)
    {
        BgraMipLevel &mipLevel = mipLevels[mipLevelIndex];
        bgfx::updateTexture2D(
            textureHandle,
            0,
            mipLevelIndex,
            0,
            0,
            mipLevel.width,
            mipLevel.height,
            takeBgraTextureUploadMemory(std::move(mipLevel.pixels)));
    }

    return textureHandle;
}
}

uint64_t textureFilterSamplerFlags(TextureFilterProfile profile)
{
    return textureFilterSamplerFlagsForMode(textureFilterModeForProfile(profile));
}

bool textureFilteringEnabled()
{
    return g_textureFilteringEnabled;
}

void setTextureFilteringEnabled(bool enabled)
{
    g_textureFilteringEnabled = enabled;
    g_textureFilteringConfig.enabled = enabled;
}

void setTextureFilteringConfig(const TextureFilteringConfig &config)
{
    g_textureFilteringConfig = config;
    g_textureFilteringEnabled = config.enabled;
}

bool toggleTextureFilteringEnabled()
{
    g_textureFilteringEnabled = !g_textureFilteringEnabled;
    g_textureFilteringConfig.enabled = g_textureFilteringEnabled;
    return g_textureFilteringEnabled;
}

uint32_t textureBindingSamplerFlags(TextureFilterProfile profile, uint32_t extraFlags)
{
    uint64_t profileFlags = textureFilterSamplerFlags(profile);

    if (!g_textureFilteringEnabled)
    {
        profileFlags = BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT;
    }

    return uint32_t(profileFlags) | extraFlags;
}

bgfx::TextureFormat::Enum bgraTextureUploadFormat()
{
#if defined(__ANDROID__)
    return bgfx::TextureFormat::RGBA8;
#else
    return bgfx::TextureFormat::BGRA8;
#endif
}

const bgfx::Memory *copyBgraTextureUploadMemory(const uint8_t *pPixels, uint32_t pixelBytes)
{
    if (pPixels == nullptr || pixelBytes == 0)
    {
        return nullptr;
    }

#if defined(__ANDROID__)
    const std::vector<uint8_t> rgbaPixels = convertBgraToRgba(pPixels, pixelBytes);
    return bgfx::copy(rgbaPixels.data(), static_cast<uint32_t>(rgbaPixels.size()));
#else
    return bgfx::copy(pPixels, pixelBytes);
#endif
}

bool prepareBgraTexturePixelsForUploadInPlace(
    uint16_t width,
    uint16_t height,
    std::vector<uint8_t> &pixels,
    TextureFilterProfile profile)
{
    const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height);
    const size_t expectedPixelBytes = pixelCount * 4;

    if (!profileNeedsTransparentEdgeBleed(profile)
        || pixelCount == 0
        || pixels.size() < expectedPixelBytes
        || !Engine::hasMixedBgraTransparency(pixels.data(), pixelCount))
    {
        return false;
    }

    Engine::bleedTransparentBgraEdgeColors(width, height, pixels);
    return true;
}

void bindTexture(
    uint8_t stage,
    bgfx::UniformHandle sampler,
    bgfx::TextureHandle textureHandle,
    TextureFilterProfile profile,
    uint32_t extraFlags)
{
    bgfx::setTexture(stage, sampler, textureHandle, textureBindingSamplerFlags(profile, extraFlags));
}

bgfx::TextureHandle createBgraTexture2D(
    uint16_t width,
    uint16_t height,
    const uint8_t *pPixels,
    uint32_t pixelBytes,
    TextureFilterProfile profile,
    uint64_t extraFlags,
    BgraTexturePixelPreparation pixelPreparation)
{
    if (pPixels == nullptr || pixelBytes == 0)
    {
        return BGFX_INVALID_HANDLE;
    }

    std::vector<uint8_t> uploadPixels;

    if (pixelPreparation == BgraTexturePixelPreparation::Required
        && profileNeedsTransparentEdgeBleed(profile))
    {
        const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height);

        if (pixelBytes >= pixelCount * 4 && Engine::hasMixedBgraTransparency(pPixels, pixelCount))
        {
            uploadPixels.assign(pPixels, pPixels + pixelBytes);
            Engine::bleedTransparentBgraEdgeColors(width, height, uploadPixels);
        }
    }

    const uint8_t *pUploadPixels = uploadPixels.empty() ? pPixels : uploadPixels.data();

    if (profileUsesMipmaps(profile))
    {
        std::vector<BgraMipLevel> mipLevels =
            prepareBgraMipChain(width, height, std::span<const uint8_t>(pUploadPixels, pixelBytes));
        const bgfx::TextureHandle mipTextureHandle = createBgraTextureWithMipChain(mipLevels, profile, extraFlags);

        if (bgfx::isValid(mipTextureHandle))
        {
            return mipTextureHandle;
        }
    }

    return bgfx::createTexture2D(
        width,
        height,
        false,
        1,
        bgraTextureUploadFormat(),
        textureFilterSamplerFlags(profile) | extraFlags,
        copyBgraTextureUploadMemory(pUploadPixels, pixelBytes));
}

PreparedBgraTexture prepareBgraTexture2D(
    uint16_t width,
    uint16_t height,
    const uint8_t *pPixels,
    uint32_t pixelBytes,
    TextureFilterProfile profile,
    BgraTexturePixelPreparation pixelPreparation)
{
    if (pPixels == nullptr || pixelBytes == 0)
    {
        return {};
    }

    return prepareBgraTexture2D(
        width, height, std::vector<uint8_t>(pPixels, pPixels + pixelBytes), profile, pixelPreparation);
}

PreparedBgraTexture prepareBgraTexture2D(
    uint16_t width,
    uint16_t height,
    std::vector<uint8_t> pixels,
    TextureFilterProfile profile,
    BgraTexturePixelPreparation pixelPreparation)
{
    PreparedBgraTexture prepared;

    if (pixels.empty())
    {
        return prepared;
    }

    if (pixelPreparation == BgraTexturePixelPreparation::Required)
    {
        prepareBgraTexturePixelsForUploadInPlace(width, height, pixels, profile);
    }

    if (profileUsesMipmaps(profile))
    {
        prepared.levels = prepareBgraMipChain(width, height, std::move(pixels));
        prepared.mips = !prepared.levels.empty();
    }

    if (prepared.levels.empty())
    {
        prepared.levels.push_back({width, height, std::move(pixels)});
    }

    return prepared;
}

bgfx::TextureHandle createPreparedBgraTexture2D(
    const PreparedBgraTexture &prepared, TextureFilterProfile profile, uint64_t extraFlags)
{
    PreparedBgraTexture copy = prepared;
    return createPreparedBgraTexture2D(std::move(copy), profile, extraFlags);
}

bgfx::TextureHandle createPreparedBgraTexture2D(
    PreparedBgraTexture &&prepared, TextureFilterProfile profile, uint64_t extraFlags)
{
    if (prepared.levels.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    if (prepared.mips)
    {
        const bgfx::TextureHandle mipTextureHandle =
            createBgraTextureWithMipChain(prepared.levels, profile, extraFlags);

        if (bgfx::isValid(mipTextureHandle))
        {
            return mipTextureHandle;
        }
    }

    BgraMipLevel &top = prepared.levels.front();
    return bgfx::createTexture2D(
        top.width,
        top.height,
        false,
        1,
        bgraTextureUploadFormat(),
        textureFilterSamplerFlags(profile) | extraFlags,
        takeBgraTextureUploadMemory(std::move(top.pixels)));
}

void updateBgraTextureArrayLayer(
    bgfx::TextureHandle texture, uint16_t layer, const std::vector<BgraMipLevel> &levels)
{
    if (!bgfx::isValid(texture))
    {
        return;
    }
    for (uint8_t index = 0; index < levels.size(); ++index)
    {
        const BgraMipLevel &level = levels[index];
        bgfx::updateTexture2D(texture, layer, index, 0, 0, level.width, level.height,
            copyBgraTextureUploadMemory(level.pixels.data(), level.pixels.size()));
    }
}

void updateBgraTextureArrayLayer(
    bgfx::TextureHandle texture,
    uint16_t layer,
    uint16_t width,
    uint16_t height,
    const std::vector<uint8_t> &pixels,
    uint8_t alphaCutoff)
{
    if (bgfx::isValid(texture))
    {
        updateBgraTextureArrayLayer(texture, layer, prepareBgraMipChain(width, height, pixels, alphaCutoff));
    }
}

namespace
{
bgfx::TextureFormat::Enum checkedCookedTextureFormat(const Engine::CookedTexture &texture)
{
    const bgfx::TextureFormat::Enum format = Engine::textureBlockFormat(texture.codec);
    if ((bgfx::getCaps()->formats[format] & BGFX_CAPS_FORMAT_TEXTURE_2D) == 0)
    {
        throw std::runtime_error("The GPU cannot sample " + std::string(Engine::textureBlockCodecName(texture.codec))
            + " cooked textures; install the asset package built for this platform's texture profile");
    }
    if (texture.width > bgfx::getCaps()->limits.maxTextureSize
        || texture.height > bgfx::getCaps()->limits.maxTextureSize)
    {
        throw std::runtime_error("Cooked texture exceeds the GPU size limit");
    }
    return format;
}
}

bgfx::TextureHandle createCookedTexture2D(
    const Engine::CookedTexture &texture, TextureFilterProfile profile, uint64_t extraFlags)
{
    const bgfx::TextureFormat::Enum format = checkedCookedTextureFormat(texture);
    return bgfx::createTexture2D(texture.width, texture.height, texture.levels > 1, 1, format,
        textureFilterSamplerFlags(profile) | extraFlags,
        bgfx::copy(texture.blocks.data(), uint32_t(texture.blocks.size())));
}

bgfx::TextureHandle createCookedTexture2DArray(
    std::span<const Engine::CookedTexture *const> layers, TextureFilterProfile profile)
{
    if (layers.empty())
    {
        return BGFX_INVALID_HANDLE;
    }
    const Engine::CookedTexture &first = *layers.front();
    const bgfx::TextureFormat::Enum format = checkedCookedTextureFormat(first);
    // bgfx array memory: each layer's whole mip chain in turn.
    const bgfx::Memory *pMemory = bgfx::alloc(uint32_t(first.blocks.size() * layers.size()));
    uint8_t *pTarget = pMemory->data;
    for (const Engine::CookedTexture *pLayer : layers)
    {
        if (pLayer->codec != first.codec || pLayer->width != first.width || pLayer->height != first.height
            || pLayer->levels != first.levels)
        {
            throw std::invalid_argument("Cooked array layers differ in codec, size or mips");
        }
        std::memcpy(pTarget, pLayer->blocks.data(), pLayer->blocks.size());
        pTarget += pLayer->blocks.size();
    }
    return bgfx::createTexture2D(first.width, first.height, first.levels > 1, uint16_t(layers.size()), format,
        textureFilterSamplerFlags(profile), pMemory);
}

bgfx::TextureHandle createSurfaceTexture2D(
    uint16_t width,
    uint16_t height,
    const std::vector<uint8_t> &pixels,
    const Engine::CookedTexture *pCookedTexture,
    TextureFilterProfile profile)
{
    if (pCookedTexture != nullptr)
    {
        return createCookedTexture2D(*pCookedTexture, profile);
    }
    return createBgraTexture2D(width, height, pixels.data(), uint32_t(pixels.size()), profile);
}

bgfx::TextureHandle createEmptyBgraTexture2D(
    uint16_t width,
    uint16_t height,
    TextureFilterProfile profile,
    uint64_t extraFlags)
{
    return bgfx::createTexture2D(
        width,
        height,
        false,
        1,
        bgraTextureUploadFormat(),
        textureFilterSamplerFlags(profile) | extraFlags);
}
}
