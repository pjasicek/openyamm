#include "game/render/TextureFiltering.h"

#include <bimg/bimg.h>
#include <bimg/encode.h>
#include <bx/allocator.h>
#include <bx/error.h>
#include <bx/readerwriter.h>

#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
bool g_textureFilteringEnabled = true;

bool profileUsesMipmaps(TextureFilterProfile profile)
{
    return profile == TextureFilterProfile::Terrain;
}

bool profileNeedsTransparentEdgeBleed(TextureFilterProfile profile)
{
    switch (profile)
    {
        case TextureFilterProfile::Billboard:
        case TextureFilterProfile::Ui:
            return true;

        case TextureFilterProfile::Terrain:
        case TextureFilterProfile::BModel:
        case TextureFilterProfile::Text:
            return false;
    }

    return false;
}

bool hasMixedTransparency(const uint8_t *pPixels, size_t pixelCount)
{
    bool foundTransparent = false;
    bool foundOpaque = false;

    for (size_t pixelIndex = 0; pixelIndex < pixelCount; ++pixelIndex)
    {
        const uint8_t alpha = pPixels[pixelIndex * 4 + 3];

        if (alpha == 0)
        {
            foundTransparent = true;
        }
        else
        {
            foundOpaque = true;
        }

        if (foundTransparent && foundOpaque)
        {
            return true;
        }
    }

    return false;
}

void bleedTransparentEdgeColors(uint16_t width, uint16_t height, std::vector<uint8_t> &pixels)
{
    const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height);

    if (pixelCount == 0 || pixels.size() < pixelCount * 4)
    {
        return;
    }

    std::vector<int32_t> owner(pixelCount, -1);
    std::vector<uint32_t> queue;
    queue.reserve(pixelCount);

    for (uint32_t pixelIndex = 0; pixelIndex < pixelCount; ++pixelIndex)
    {
        if (pixels[static_cast<size_t>(pixelIndex) * 4 + 3] != 0)
        {
            owner[pixelIndex] = static_cast<int32_t>(pixelIndex);
            queue.push_back(pixelIndex);
        }
    }

    size_t queueHead = 0;

    while (queueHead < queue.size())
    {
        const uint32_t currentIndex = queue[queueHead++];
        const uint32_t x = currentIndex % width;
        const uint32_t y = currentIndex / width;

        for (int dy = -1; dy <= 1; ++dy)
        {
            for (int dx = -1; dx <= 1; ++dx)
            {
                if (dx == 0 && dy == 0)
                {
                    continue;
                }

                const int neighborX = static_cast<int>(x) + dx;
                const int neighborY = static_cast<int>(y) + dy;

                if (neighborX < 0
                    || neighborY < 0
                    || neighborX >= static_cast<int>(width)
                    || neighborY >= static_cast<int>(height))
                {
                    continue;
                }

                const uint32_t neighborIndex =
                    static_cast<uint32_t>(neighborY) * static_cast<uint32_t>(width) + static_cast<uint32_t>(neighborX);
                const size_t neighborOffset = static_cast<size_t>(neighborIndex) * 4;

                if (pixels[neighborOffset + 3] != 0 || owner[neighborIndex] != -1)
                {
                    continue;
                }

                owner[neighborIndex] = owner[currentIndex];
                queue.push_back(neighborIndex);
            }
        }
    }

    for (size_t pixelIndex = 0; pixelIndex < pixelCount; ++pixelIndex)
    {
        const size_t pixelOffset = pixelIndex * 4;

        if (pixels[pixelOffset + 3] != 0)
        {
            continue;
        }

        const int32_t sourceIndex = owner[pixelIndex];

        if (sourceIndex < 0)
        {
            continue;
        }

        const size_t sourceOffset = static_cast<size_t>(sourceIndex) * 4;
        pixels[pixelOffset + 0] = pixels[sourceOffset + 0];
        pixels[pixelOffset + 1] = pixels[sourceOffset + 1];
        pixels[pixelOffset + 2] = pixels[sourceOffset + 2];
    }
}

std::vector<uint8_t> prepareTexturePixelsForUpload(
    uint16_t width,
    uint16_t height,
    const uint8_t *pPixels,
    uint32_t pixelBytes,
    TextureFilterProfile profile)
{
    std::vector<uint8_t> preparedPixels(pPixels, pPixels + pixelBytes);

    if (!profileNeedsTransparentEdgeBleed(profile))
    {
        return preparedPixels;
    }

    const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height);

    if (!hasMixedTransparency(preparedPixels.data(), pixelCount))
    {
        return preparedPixels;
    }

    bleedTransparentEdgeColors(width, height, preparedPixels);
    return preparedPixels;
}

bgfx::TextureHandle createBgraTextureWithMipChain(
    uint16_t width,
    uint16_t height,
    const uint8_t *pPixels,
    uint32_t pixelBytes,
    TextureFilterProfile profile,
    uint64_t extraFlags)
{
    if (pPixels == nullptr || pixelBytes == 0)
    {
        return BGFX_INVALID_HANDLE;
    }

    bx::DefaultAllocator allocator;
    bimg::ImageContainer *pBaseImage = bimg::imageAlloc(
        &allocator,
        bimg::TextureFormat::BGRA8,
        width,
        height,
        1,
        1,
        false,
        false,
        pPixels);

    if (pBaseImage == nullptr)
    {
        return BGFX_INVALID_HANDLE;
    }

    bimg::ImageContainer *pMipImage = bimg::imageGenerateMips(&allocator, *pBaseImage);
    bimg::ImageContainer *pImage = pMipImage != nullptr ? pMipImage : pBaseImage;
    bx::MemoryBlock memoryBlock(&allocator);
    bx::MemoryWriter writer(&memoryBlock);
    bx::Error error;
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;

    if (bimg::imageWriteKtx(&writer, *pImage, pImage->m_data, pImage->m_size, &error) > 0 && error.isOk())
    {
        const void *pTextureBytes = memoryBlock.more();
        const uint32_t textureByteCount = memoryBlock.getSize();

        if (pTextureBytes != nullptr && textureByteCount > 0)
        {
            textureHandle = bgfx::createTexture(
                bgfx::copy(pTextureBytes, textureByteCount),
                textureFilterSamplerFlags(profile) | extraFlags);
        }
    }

    if (pMipImage != nullptr && pMipImage != pBaseImage)
    {
        bimg::imageFree(pMipImage);
    }

    bimg::imageFree(pBaseImage);
    return textureHandle;
}
}

uint64_t textureFilterSamplerFlags(TextureFilterProfile profile)
{
    switch (profile)
    {
        case TextureFilterProfile::Terrain:
            return BGFX_SAMPLER_MIN_ANISOTROPIC | BGFX_SAMPLER_MAG_ANISOTROPIC;

        case TextureFilterProfile::BModel:
        case TextureFilterProfile::Billboard:
        case TextureFilterProfile::Ui:
            return BGFX_SAMPLER_NONE;

        case TextureFilterProfile::Text:
            return BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT;
    }

    return BGFX_SAMPLER_NONE;
}

bool textureFilteringEnabled()
{
    return g_textureFilteringEnabled;
}

void setTextureFilteringEnabled(bool enabled)
{
    g_textureFilteringEnabled = enabled;
}

bool toggleTextureFilteringEnabled()
{
    g_textureFilteringEnabled = !g_textureFilteringEnabled;
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
    uint64_t extraFlags)
{
    if (pPixels == nullptr || pixelBytes == 0)
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::vector<uint8_t> uploadPixels = prepareTexturePixelsForUpload(width, height, pPixels, pixelBytes, profile);
    const uint8_t *pUploadPixels = uploadPixels.empty() ? pPixels : uploadPixels.data();

    if (profileUsesMipmaps(profile))
    {
        const bgfx::TextureHandle mipTextureHandle =
            createBgraTextureWithMipChain(width, height, pUploadPixels, pixelBytes, profile, extraFlags);

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
        bgfx::TextureFormat::BGRA8,
        textureFilterSamplerFlags(profile) | extraFlags,
        bgfx::copy(pUploadPixels, pixelBytes));
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
        bgfx::TextureFormat::BGRA8,
        textureFilterSamplerFlags(profile) | extraFlags);
}
}
