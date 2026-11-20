#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace OpenYAMM::Engine
{
enum class ImageMipSemantic
{
    Linear,
    Srgb,
    Normal,
};

struct BgraMipLevel
{
    uint16_t width = 0;
    uint16_t height = 0;
    std::vector<uint8_t> pixels;
};

float srgbToLinear(float value);
float linearToSrgb(float value);
void preserveBgraCutoutCoverage(
    std::vector<uint8_t> &pixels, std::span<const uint8_t> referencePixels, uint8_t alphaCutoff);
// Whether some texels are fully transparent and some are not.
bool hasMixedBgraTransparency(const uint8_t *pPixels, size_t pixelCount);
// Fully transparent texels take the colour of the nearest visible texel (alpha stays 0), so bilinear filtering and
// mips never pull a key colour or black into the visible edge.
void bleedTransparentBgraEdgeColors(uint16_t width, uint16_t height, std::vector<uint8_t> &pixels);
std::vector<BgraMipLevel> prepareBgraMipChain(
    uint16_t width, uint16_t height, std::span<const uint8_t> pixels, uint8_t alphaCutoff = 0,
    ImageMipSemantic semantic = ImageMipSemantic::Linear);
// Takes over the top level's pixels instead of copying them.
std::vector<BgraMipLevel> prepareBgraMipChain(
    uint16_t width, uint16_t height, std::vector<uint8_t> &&pixels, uint8_t alphaCutoff = 0,
    ImageMipSemantic semantic = ImageMipSemantic::Linear);
}
