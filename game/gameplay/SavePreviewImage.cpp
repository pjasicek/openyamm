#include "game/gameplay/SavePreviewImage.h"

#include <algorithm>
#include <cstddef>
#include <cstdlib>
#include <cstring>

namespace OpenYAMM::Game::SavePreviewImage
{
std::vector<uint8_t> cropAndScaleBgraPreview(
    const std::vector<uint8_t> &sourcePixels,
    int sourceWidth,
    int sourceHeight,
    int targetWidth,
    int targetHeight)
{
    if (sourceWidth <= 0
        || sourceHeight <= 0
        || targetWidth <= 0
        || targetHeight <= 0
        || sourcePixels.size() != static_cast<size_t>(sourceWidth) * static_cast<size_t>(sourceHeight) * 4)
    {
        return {};
    }

    int cropX = 0;
    int cropY = 0;
    int cropWidth = sourceWidth;
    int cropHeight = sourceHeight;

    if (sourceWidth * 3 > sourceHeight * 4)
    {
        cropWidth = (sourceHeight * 4) / 3;
        cropX = (sourceWidth - cropWidth) / 2;
    }
    else if (sourceWidth * 3 < sourceHeight * 4)
    {
        cropHeight = (sourceWidth * 3) / 4;
        cropY = (sourceHeight - cropHeight) / 2;
    }

    std::vector<uint8_t> scaledPixels(static_cast<size_t>(targetWidth) * static_cast<size_t>(targetHeight) * 4, 0);

    for (int y = 0; y < targetHeight; ++y)
    {
        const int sourceY = cropY + (y * cropHeight) / targetHeight;

        for (int x = 0; x < targetWidth; ++x)
        {
            const int sourceX = cropX + (x * cropWidth) / targetWidth;
            const size_t sourceIndex =
                (static_cast<size_t>(sourceY) * static_cast<size_t>(sourceWidth) + static_cast<size_t>(sourceX)) * 4;
            const size_t targetIndex =
                (static_cast<size_t>(y) * static_cast<size_t>(targetWidth) + static_cast<size_t>(x)) * 4;

            scaledPixels[targetIndex + 0] = sourcePixels[sourceIndex + 0];
            scaledPixels[targetIndex + 1] = sourcePixels[sourceIndex + 1];
            scaledPixels[targetIndex + 2] = sourcePixels[sourceIndex + 2];
            scaledPixels[targetIndex + 3] = sourcePixels[sourceIndex + 3];
        }
    }

    return scaledPixels;
}

bool decodeBmpBytesToBgra(
    const std::vector<uint8_t> &bmpBytes,
    int &width,
    int &height,
    std::vector<uint8_t> &pixels)
{
    width = 0;
    height = 0;
    pixels.clear();

    if (bmpBytes.size() < 54 || bmpBytes[0] != 'B' || bmpBytes[1] != 'M')
    {
        return false;
    }

    const auto readUint32Le =
        [&bmpBytes](size_t offset) -> uint32_t
        {
            return static_cast<uint32_t>(bmpBytes[offset])
                | (static_cast<uint32_t>(bmpBytes[offset + 1]) << 8)
                | (static_cast<uint32_t>(bmpBytes[offset + 2]) << 16)
                | (static_cast<uint32_t>(bmpBytes[offset + 3]) << 24);
        };
    const auto readInt32Le =
        [&readUint32Le](size_t offset) -> int32_t
        {
            return static_cast<int32_t>(readUint32Le(offset));
        };

    const uint32_t pixelOffset = readUint32Le(10);
    const int32_t signedWidth = readInt32Le(18);
    const int32_t signedHeight = readInt32Le(22);
    const uint16_t bitsPerPixel =
        static_cast<uint16_t>(bmpBytes[28]) | (static_cast<uint16_t>(bmpBytes[29]) << 8);
    const bool topDown = signedHeight < 0;
    width = std::abs(signedWidth);
    height = std::abs(signedHeight);

    if (width <= 0 || height <= 0 || (bitsPerPixel != 24 && bitsPerPixel != 32))
    {
        return false;
    }

    const size_t bytesPerPixel = bitsPerPixel / 8u;
    const size_t rowStride = ((static_cast<size_t>(width) * bytesPerPixel) + 3u) & ~3u;

    if (pixelOffset + rowStride * static_cast<size_t>(height) > bmpBytes.size())
    {
        return false;
    }

    pixels.resize(static_cast<size_t>(width) * static_cast<size_t>(height) * 4u);

    for (int y = 0; y < height; ++y)
    {
        const int sourceY = topDown ? y : (height - 1 - y);
        const size_t sourceRow = pixelOffset + rowStride * static_cast<size_t>(sourceY);

        for (int x = 0; x < width; ++x)
        {
            const size_t sourceIndex = sourceRow + static_cast<size_t>(x) * bytesPerPixel;
            const size_t targetIndex =
                (static_cast<size_t>(y) * static_cast<size_t>(width) + static_cast<size_t>(x)) * 4u;
            pixels[targetIndex + 0] = bmpBytes[sourceIndex + 0];
            pixels[targetIndex + 1] = bmpBytes[sourceIndex + 1];
            pixels[targetIndex + 2] = bmpBytes[sourceIndex + 2];
            pixels[targetIndex + 3] = bitsPerPixel == 32 ? bmpBytes[sourceIndex + 3] : 255u;
        }
    }

    return true;
}

std::vector<uint8_t> encodeBgraToBmp(int width, int height, const std::vector<uint8_t> &pixels)
{
    if (width <= 0
        || height <= 0
        || pixels.size() != static_cast<size_t>(width) * static_cast<size_t>(height) * 4)
    {
        return {};
    }

    const uint32_t pixelBytes = static_cast<uint32_t>(pixels.size());
    const uint32_t fileSize = 54u + pixelBytes;
    std::vector<uint8_t> bmp(fileSize, 0);
    bmp[0] = 'B';
    bmp[1] = 'M';

    const auto writeU32 = [&bmp](size_t offset, uint32_t value)
    {
        bmp[offset + 0] = static_cast<uint8_t>(value & 0xffu);
        bmp[offset + 1] = static_cast<uint8_t>((value >> 8) & 0xffu);
        bmp[offset + 2] = static_cast<uint8_t>((value >> 16) & 0xffu);
        bmp[offset + 3] = static_cast<uint8_t>((value >> 24) & 0xffu);
    };
    const auto writeU16 = [&bmp](size_t offset, uint16_t value)
    {
        bmp[offset + 0] = static_cast<uint8_t>(value & 0xffu);
        bmp[offset + 1] = static_cast<uint8_t>((value >> 8) & 0xffu);
    };

    writeU32(2, fileSize);
    writeU32(10, 54);
    writeU32(14, 40);
    writeU32(18, static_cast<uint32_t>(width));
    writeU32(22, static_cast<uint32_t>(-height));
    writeU16(26, 1);
    writeU16(28, 32);
    writeU32(34, pixelBytes);
    writeU32(38, 2835);
    writeU32(42, 2835);

    std::memcpy(bmp.data() + 54, pixels.data(), pixels.size());
    return bmp;
}
} // namespace OpenYAMM::Game::SavePreviewImage
