#pragma once

#include <cstdint>
#include <vector>

namespace OpenYAMM::Game::SavePreviewImage
{
std::vector<uint8_t> cropAndScaleBgraPreview(
    const std::vector<uint8_t> &sourcePixels,
    int sourceWidth,
    int sourceHeight,
    int targetWidth,
    int targetHeight);

std::vector<uint8_t> encodeBgraToBmp(int width, int height, const std::vector<uint8_t> &pixels);
} // namespace OpenYAMM::Game::SavePreviewImage
