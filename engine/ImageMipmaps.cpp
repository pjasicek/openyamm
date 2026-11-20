#include "engine/ImageMipmaps.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <utility>

namespace OpenYAMM::Engine
{
float srgbToLinear(float value)
{
    return value <= 0.04045f ? value / 12.92f : std::pow((value + 0.055f) / 1.055f, 2.4f);
}

float linearToSrgb(float value)
{
    value = std::max(value, 0.0f);
    return value <= 0.0031308f ? value * 12.92f : 1.055f * std::pow(value, 1.0f / 2.4f) - 0.055f;
}

void preserveBgraCutoutCoverage(
    std::vector<uint8_t> &pixels, std::span<const uint8_t> referencePixels, uint8_t alphaCutoff)
{
    if (alphaCutoff == 0 || pixels.empty() || referencePixels.empty() ||
        pixels.size() % 4 != 0 || referencePixels.size() % 4 != 0)
    {
        return;
    }
    uint64_t referenceCovered = 0;
    for (size_t i = 3; i < referencePixels.size(); i += 4)
    {
        referenceCovered += referencePixels[i] >= alphaCutoff ? 1 : 0;
    }
    std::array<uint64_t, 256> histogram = {};
    for (size_t i = 3; i < pixels.size(); i += 4)
    {
        ++histogram[pixels[i]];
    }
    const uint64_t referenceCount = referencePixels.size() / 4;
    const uint64_t desired = referenceCovered * (pixels.size() / 4);
    const auto errorFor = [&](uint64_t covered)
    {
        const uint64_t actual = covered * referenceCount;
        return actual > desired ? actual - desired : desired - actual;
    };
    uint64_t covered = 0;
    for (int alpha = alphaCutoff; alpha <= 255; ++alpha)
    {
        covered += histogram[alpha];
    }
    uint64_t bestError = errorFor(covered);
    int bestThreshold = alphaCutoff;
    if (errorFor(0) < bestError)
    {
        bestError = errorFor(0);
        bestThreshold = 256;
    }
    covered = 0;
    for (int alpha = 255; alpha >= 1; --alpha)
    {
        covered += histogram[alpha];
        const uint64_t error = errorFor(covered);
        if (error < bestError)
        {
            bestError = error;
            bestThreshold = alpha;
        }
    }
    if (bestThreshold == alphaCutoff)
    {
        return;
    }
    const float scale = (float(alphaCutoff) - 0.5f) / (float(bestThreshold) - 0.5f);
    for (size_t i = 3; i < pixels.size(); i += 4)
    {
        pixels[i] = uint8_t(std::clamp(std::lround(pixels[i] * scale), 0L, 255L));
    }
}

namespace
{
// Display-space 2x2 box average, as existing world and UI consumers expect; the last row or column repeats when a
// side is odd. Integer sums round half up exactly like the float average they replace.
void downsampleLinearBgra(const BgraMipLevel &source, BgraMipLevel &target)
{
    const size_t stride = size_t(source.width) * 4;
    for (uint16_t y = 0; y < target.height; ++y)
    {
        const uint8_t *pRow0 = source.pixels.data() + std::min<size_t>(size_t(y) * 2, source.height - 1) * stride;
        const uint8_t *pRow1 = source.pixels.data() + std::min<size_t>(size_t(y) * 2 + 1, source.height - 1) * stride;
        uint8_t *pTarget = target.pixels.data() + size_t(y) * target.width * 4;
        for (uint16_t x = 0; x < target.width; ++x)
        {
            const size_t left = std::min<size_t>(size_t(x) * 2, source.width - 1) * 4;
            const size_t right = std::min<size_t>(size_t(x) * 2 + 1, source.width - 1) * 4;
            for (size_t channel = 0; channel < 4; ++channel)
            {
                const uint32_t sum = uint32_t(pRow0[left + channel]) + pRow0[right + channel]
                    + pRow1[left + channel] + pRow1[right + channel];
                pTarget[size_t(x) * 4 + channel] = uint8_t((sum + 2) / 4);
            }
        }
    }
}

// Material mips: linear-light colour or renormalized normals, averaged over every texel of non-power-of-two images.
void downsampleMaterialBgra(const BgraMipLevel &source, BgraMipLevel &target, ImageMipSemantic semantic,
    const std::array<float, 256> &srgbValues)
{
    for (uint16_t y = 0; y < target.height; ++y)
    {
        for (uint16_t x = 0; x < target.width; ++x)
        {
            const uint16_t beginX = uint32_t(x) * source.width / target.width;
            const uint16_t beginY = uint32_t(y) * source.height / target.height;
            const uint16_t endX = uint32_t(x + 1) * source.width / target.width;
            const uint16_t endY = uint32_t(y + 1) * source.height / target.height;
            std::array<float, 4> sum = {};
            uint32_t count = 0;
            for (uint16_t sy = beginY; sy < endY; ++sy)
            {
                for (uint16_t sx = beginX; sx < endX; ++sx)
                {
                    const size_t offset = (size_t(sy) * source.width + sx) * 4;
                    for (size_t channel = 0; channel < 4; ++channel)
                    {
                        float value = source.pixels[offset + channel] / 255.0f;
                        if (channel < 3 && semantic == ImageMipSemantic::Srgb)
                        {
                            value = srgbValues[source.pixels[offset + channel]];
                        }
                        else if (channel < 3 && semantic == ImageMipSemantic::Normal)
                        {
                            value = value * 2.0f - 1.0f;
                        }
                        sum[channel] += value;
                    }
                    ++count;
                }
            }
            for (float &value : sum)
            {
                value /= count;
            }
            if (semantic == ImageMipSemantic::Normal)
            {
                const float length = std::sqrt(sum[0] * sum[0] + sum[1] * sum[1] + sum[2] * sum[2]);
                if (length < 1.0e-6f)
                {
                    sum[0] = 1.0f;
                    sum[1] = sum[2] = 0.0f;
                }
                else
                {
                    for (size_t channel = 0; channel < 3; ++channel)
                    {
                        sum[channel] /= length;
                    }
                }
            }
            const size_t offset = (size_t(y) * target.width + x) * 4;
            for (size_t channel = 0; channel < 4; ++channel)
            {
                float value = sum[channel];
                if (channel < 3 && semantic == ImageMipSemantic::Srgb)
                {
                    value = linearToSrgb(value);
                }
                else if (channel < 3 && semantic == ImageMipSemantic::Normal)
                {
                    value = value * 0.5f + 0.5f;
                }
                target.pixels[offset + channel] =
                    uint8_t(std::clamp(std::lround(value * 255.0f), 0L, 255L));
            }
        }
    }
}
}

std::vector<BgraMipLevel> prepareBgraMipChain(
    uint16_t width, uint16_t height, std::span<const uint8_t> pixels, uint8_t alphaCutoff,
    ImageMipSemantic semantic)
{
    const size_t bytes = size_t(width) * height * 4;
    if (width == 0 || height == 0 || pixels.size() < bytes)
    {
        return {};
    }
    return prepareBgraMipChain(width, height, std::vector<uint8_t>(pixels.begin(), pixels.begin() + bytes),
        alphaCutoff, semantic);
}

std::vector<BgraMipLevel> prepareBgraMipChain(
    uint16_t width, uint16_t height, std::vector<uint8_t> &&pixels, uint8_t alphaCutoff,
    ImageMipSemantic semantic)
{
    const size_t bytes = size_t(width) * height * 4;
    if (width == 0 || height == 0 || pixels.size() < bytes)
    {
        return {};
    }
    pixels.resize(bytes);
    const std::array<float, 256> srgbValues = [semantic]()
    {
        std::array<float, 256> values = {};
        if (semantic == ImageMipSemantic::Srgb)
        {
            for (size_t index = 0; index < values.size(); ++index)
            {
                values[index] = srgbToLinear(float(index) / 255.0f);
            }
        }
        return values;
    }();
    std::vector<BgraMipLevel> levels;
    levels.push_back({width, height, std::move(pixels)});
    while (levels.back().width > 1 || levels.back().height > 1)
    {
        const BgraMipLevel &source = levels.back();
        BgraMipLevel target;
        target.width = std::max<uint16_t>(1, source.width / 2);
        target.height = std::max<uint16_t>(1, source.height / 2);
        target.pixels.resize(size_t(target.width) * target.height * 4);
        if (semantic == ImageMipSemantic::Linear)
        {
            downsampleLinearBgra(source, target);
        }
        else
        {
            downsampleMaterialBgra(source, target, semantic, srgbValues);
        }
        if (alphaCutoff > 0)
        {
            preserveBgraCutoutCoverage(target.pixels, levels.front().pixels, alphaCutoff);
        }
        levels.push_back(std::move(target));
    }
    return levels;
}

bool hasMixedBgraTransparency(const uint8_t *pPixels, size_t pixelCount)
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

void bleedTransparentBgraEdgeColors(uint16_t width, uint16_t height, std::vector<uint8_t> &pixels)
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
}
