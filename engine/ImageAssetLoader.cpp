#include "engine/ImageAssetLoader.h"

#include "engine/AssetScaleTier.h"
#include "engine/render/CookedTexture.h"

#include <SDL3/SDL.h>
#include <bimg/bimg.h>
#include <bimg/decode.h>
#include <bx/allocator.h>
#include <bx/error.h>

#include <algorithm>
#include <cctype>
#include <cstring>

namespace OpenYAMM::Engine
{
namespace
{
#pragma pack(push, 1)
struct PcxHeader
{
    uint8_t manufacturer = 0;
    uint8_t version = 0;
    uint8_t encoding = 0;
    uint8_t bitsPerPixel = 0;
    uint16_t xMin = 0;
    uint16_t yMin = 0;
    uint16_t xMax = 0;
    uint16_t yMax = 0;
    uint16_t horizontalDpi = 0;
    uint16_t verticalDpi = 0;
    uint8_t colorMap[48] = {};
    uint8_t reserved = 0;
    uint8_t colorPlanes = 0;
    uint16_t bytesPerLine = 0;
    uint16_t paletteType = 0;
    uint16_t horizontalScreenSize = 0;
    uint16_t verticalScreenSize = 0;
    uint8_t filler[54] = {};
};
#pragma pack(pop)

static_assert(sizeof(PcxHeader) == 128);

std::string toLowerCopy(std::string_view value)
{
    std::string result(value);

    std::transform(
        result.begin(),
        result.end(),
        result.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });

    return result;
}

bool endsWith(std::string_view value, std::string_view suffix)
{
    return value.size() >= suffix.size() && value.substr(value.size() - suffix.size()) == suffix;
}

bool hasPngSignature(const std::vector<uint8_t> &bytes)
{
    constexpr uint8_t PngSignature[] = {0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n'};
    return bytes.size() >= sizeof(PngSignature) && std::memcmp(bytes.data(), PngSignature, sizeof(PngSignature)) == 0;
}

bool hasBmpSignature(const std::vector<uint8_t> &bytes)
{
    return bytes.size() >= 2 && bytes[0] == 'B' && bytes[1] == 'M';
}

bool hasPcxSignature(const std::vector<uint8_t> &bytes)
{
    return bytes.size() >= sizeof(PcxHeader)
        && bytes[0] == 0x0a
        && bytes[2] == 1
        && bytes[3] == 8;
}

bool isTransparentKey(
    uint8_t red,
    uint8_t green,
    uint8_t blue,
    const ImageDecodeOptions &options
);

std::optional<ImagePixelsBgra> decodePngPixelsBgra(
    const std::vector<uint8_t> &imageBytes,
    const ImageDecodeOptions &options
)
{
    bx::DefaultAllocator allocator;
    bx::Error error;
    bimg::ImageContainer *pImage = bimg::imageParse(
        &allocator,
        imageBytes.data(),
        static_cast<uint32_t>(imageBytes.size()),
        bimg::TextureFormat::RGBA8,
        &error);

    if (pImage == nullptr)
    {
        return std::nullopt;
    }

    bimg::ImageMip mip = {};
    const bool gotRawData =
        bimg::imageGetRawData(*pImage, 0, 0, pImage->m_data, pImage->m_size, mip)
        && mip.m_data != nullptr
        && mip.m_width > 0
        && mip.m_height > 0
        && mip.m_bpp == 32;

    std::optional<ImagePixelsBgra> result;

    if (gotRawData)
    {
        const size_t expectedSize = static_cast<size_t>(mip.m_width) * static_cast<size_t>(mip.m_height) * 4;

        if (mip.m_size >= expectedSize)
        {
            ImagePixelsBgra pixels = {};
            pixels.width = static_cast<int>(mip.m_width);
            pixels.height = static_cast<int>(mip.m_height);
            pixels.pixels.assign(mip.m_data, mip.m_data + expectedSize);

            for (size_t pixelOffset = 0; pixelOffset < pixels.pixels.size(); pixelOffset += 4)
            {
                std::swap(pixels.pixels[pixelOffset], pixels.pixels[pixelOffset + 2]);
                const uint8_t blue = pixels.pixels[pixelOffset + 0];
                const uint8_t green = pixels.pixels[pixelOffset + 1];
                const uint8_t red = pixels.pixels[pixelOffset + 2];

                if (isTransparentKey(red, green, blue, options))
                {
                    pixels.pixels[pixelOffset + 3] = 0;
                }
            }

            result = std::move(pixels);
        }
    }

    bimg::imageFree(pImage);
    return result;
}

bool isTransparentKey(
    uint8_t red,
    uint8_t green,
    uint8_t blue,
    const ImageDecodeOptions &options
)
{
    const bool isMagentaKey =
        options.applyMagentaTransparencyKey && red >= 248 && green <= 8 && blue >= 248;
    const bool isTealKey =
        options.applyTealTransparencyKey && red <= 8 && green >= 248 && blue >= 248;
    const bool isBlackKey =
        options.applyBlackTransparencyKey && red <= 8 && green <= 8 && blue <= 8;

    return isMagentaKey || isTealKey || isBlackKey;
}

bool decodePcxScanline(const std::vector<uint8_t> &bytes, size_t &offset, std::vector<uint8_t> &scanline)
{
    size_t outputOffset = 0;

    while (outputOffset < scanline.size())
    {
        if (offset >= bytes.size())
        {
            return false;
        }

        uint8_t value = bytes[offset++];
        size_t repeatCount = 1;

        if ((value & 0xc0u) == 0xc0u)
        {
            repeatCount = value & 0x3fu;
            if (repeatCount == 0 || offset >= bytes.size())
            {
                return false;
            }
            value = bytes[offset++];
        }

        if (repeatCount > scanline.size() - outputOffset)
        {
            return false;
        }

        std::fill_n(scanline.begin() + static_cast<ptrdiff_t>(outputOffset), repeatCount, value);
        outputOffset += repeatCount;
    }

    return true;
}

std::optional<ImagePixelsBgra> decodePcxPixelsBgra(
    const std::vector<uint8_t> &imageBytes,
    const ImageDecodeOptions &options)
{
    if (!hasPcxSignature(imageBytes))
    {
        return std::nullopt;
    }

    PcxHeader header = {};
    std::memcpy(&header, imageBytes.data(), sizeof(header));

    if (header.colorPlanes != 1 && header.colorPlanes != 3)
    {
        return std::nullopt;
    }

    const int width = static_cast<int>(header.xMax) - static_cast<int>(header.xMin) + 1;
    const int height = static_cast<int>(header.yMax) - static_cast<int>(header.yMin) + 1;
    if (width <= 0 || height <= 0 || header.bytesPerLine < width)
    {
        return std::nullopt;
    }

    std::array<uint8_t, 256 * 3> sourcePalette = {};
    if (header.colorPlanes == 1)
    {
        if (imageBytes.size() < sizeof(PcxHeader) + 769 || imageBytes[imageBytes.size() - 769] != 0x0c)
        {
            return std::nullopt;
        }
        std::memcpy(sourcePalette.data(), imageBytes.data() + imageBytes.size() - 768, sourcePalette.size());
    }

    ImagePixelsBgra result = {};
    result.width = width;
    result.height = height;
    result.pixels.resize(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);
    const size_t scanlineSize = static_cast<size_t>(header.bytesPerLine) * header.colorPlanes;
    std::vector<uint8_t> scanline(scanlineSize);
    size_t sourceOffset = sizeof(PcxHeader);

    for (int y = 0; y < height; ++y)
    {
        if (!decodePcxScanline(imageBytes, sourceOffset, scanline))
        {
            return std::nullopt;
        }

        for (int x = 0; x < width; ++x)
        {
            uint8_t red = 0;
            uint8_t green = 0;
            uint8_t blue = 0;
            bool paletteZeroKey = false;

            if (header.colorPlanes == 1)
            {
                const uint8_t paletteIndex = scanline[static_cast<size_t>(x)];
                const std::array<uint8_t, 256 * 3> &palette =
                    options.overridePalette.has_value() ? *options.overridePalette : sourcePalette;
                const size_t paletteOffset = static_cast<size_t>(paletteIndex) * 3;
                red = palette[paletteOffset];
                green = palette[paletteOffset + 1];
                blue = palette[paletteOffset + 2];
                paletteZeroKey = options.applyPaletteZeroTransparencyKey && paletteIndex == 0;
            }
            else
            {
                red = scanline[static_cast<size_t>(x)];
                green = scanline[static_cast<size_t>(header.bytesPerLine) + static_cast<size_t>(x)];
                blue = scanline[static_cast<size_t>(header.bytesPerLine) * 2 + static_cast<size_t>(x)];
            }

            const size_t pixelOffset =
                (static_cast<size_t>(y) * static_cast<size_t>(width) + static_cast<size_t>(x)) * 4;
            result.pixels[pixelOffset] = blue;
            result.pixels[pixelOffset + 1] = green;
            result.pixels[pixelOffset + 2] = red;
            result.pixels[pixelOffset + 3] =
                paletteZeroKey || isTransparentKey(red, green, blue, options) ? 0 : 255;
        }
    }

    return result;
}

std::optional<ImagePixelsBgra> decodeBmpPixelsBgra(
    const std::vector<uint8_t> &imageBytes,
    const ImageDecodeOptions &options
)
{
    SDL_IOStream *pIoStream = SDL_IOFromConstMem(imageBytes.data(), imageBytes.size());

    if (pIoStream == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return std::nullopt;
    }

    SDL_Palette *pBasePalette = SDL_GetSurfacePalette(pLoadedSurface);
    const bool canUseIndexedPalette =
        pLoadedSurface->format == SDL_PIXELFORMAT_INDEX8
        && pBasePalette != nullptr
        && (options.overridePalette.has_value() || options.applyPaletteZeroTransparencyKey);

    if (canUseIndexedPalette)
    {
        ImagePixelsBgra result = {};
        result.width = pLoadedSurface->w;
        result.height = pLoadedSurface->h;
        result.pixels.resize(static_cast<size_t>(result.width) * static_cast<size_t>(result.height) * 4);

        for (int row = 0; row < result.height; ++row)
        {
            const uint8_t *pSourceRow = static_cast<const uint8_t *>(pLoadedSurface->pixels)
                + static_cast<ptrdiff_t>(row * pLoadedSurface->pitch);

            for (int column = 0; column < result.width; ++column)
            {
                const uint8_t paletteIndex = pSourceRow[column];
                const SDL_Color sourceColor =
                    paletteIndex < pBasePalette->ncolors ? pBasePalette->colors[paletteIndex] : SDL_Color{0, 0, 0, 255};
                const bool isZeroIndexKey = options.applyPaletteZeroTransparencyKey && paletteIndex == 0;
                const bool isColorKey = isTransparentKey(sourceColor.r, sourceColor.g, sourceColor.b, options);
                const size_t pixelOffset =
                    (static_cast<size_t>(row) * static_cast<size_t>(result.width) + static_cast<size_t>(column)) * 4;

                if (options.overridePalette.has_value())
                {
                    const size_t paletteOffset = static_cast<size_t>(paletteIndex) * 3;
                    result.pixels[pixelOffset + 0] = (*options.overridePalette)[paletteOffset + 2];
                    result.pixels[pixelOffset + 1] = (*options.overridePalette)[paletteOffset + 1];
                    result.pixels[pixelOffset + 2] = (*options.overridePalette)[paletteOffset + 0];
                }
                else
                {
                    result.pixels[pixelOffset + 0] = sourceColor.b;
                    result.pixels[pixelOffset + 1] = sourceColor.g;
                    result.pixels[pixelOffset + 2] = sourceColor.r;
                }

                result.pixels[pixelOffset + 3] = (isZeroIndexKey || isColorKey) ? 0 : 255;
            }
        }

        SDL_DestroySurface(pLoadedSurface);
        return result;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return std::nullopt;
    }

    ImagePixelsBgra result = {};
    result.width = pConvertedSurface->w;
    result.height = pConvertedSurface->h;
    result.pixels.resize(static_cast<size_t>(result.width) * static_cast<size_t>(result.height) * 4);

    for (int row = 0; row < result.height; ++row)
    {
        const uint8_t *pSourceRow = static_cast<const uint8_t *>(pConvertedSurface->pixels)
            + static_cast<ptrdiff_t>(row * pConvertedSurface->pitch);
        uint8_t *pTargetRow =
            result.pixels.data() + static_cast<size_t>(row) * static_cast<size_t>(result.width) * 4;
        std::memcpy(pTargetRow, pSourceRow, static_cast<size_t>(result.width) * 4);
    }

    SDL_DestroySurface(pConvertedSurface);

    for (size_t pixelOffset = 0; pixelOffset < result.pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = result.pixels[pixelOffset + 0];
        const uint8_t green = result.pixels[pixelOffset + 1];
        const uint8_t red = result.pixels[pixelOffset + 2];

        if (isTransparentKey(red, green, blue, options))
        {
            result.pixels[pixelOffset + 3] = 0;
        }
    }

    return result;
}
}

std::optional<ImagePixelsBgra> decodeImagePixelsBgra(
    const std::vector<uint8_t> &imageBytes,
    std::string_view virtualPath,
    const ImageDecodeOptions &options
)
{
    if (imageBytes.empty())
    {
        return std::nullopt;
    }

    const std::string lowerPath = toLowerCopy(virtualPath);

    if (endsWith(lowerPath, ".png") || hasPngSignature(imageBytes))
    {
        return decodePngPixelsBgra(imageBytes, options);
    }

    if (endsWith(lowerPath, ".bmp") || hasBmpSignature(imageBytes))
    {
        return decodeBmpPixelsBgra(imageBytes, options);
    }

    if (endsWith(lowerPath, ".pcx") || hasPcxSignature(imageBytes))
    {
        return decodePcxPixelsBgra(imageBytes, options);
    }

    return std::nullopt;
}

namespace
{
std::optional<ImagePixelsBgra> loadResolvedImagePixelsBgra(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    BinaryAssetCache &binaryFilesByPath,
    const ImageDecodeOptions &options
)
{
    const auto cachedFileIt = binaryFilesByPath.find(virtualPath);
    std::optional<std::vector<uint8_t>> imageBytes;

    if (cachedFileIt != binaryFilesByPath.end())
    {
        imageBytes = cachedFileIt->second;
    }
    else
    {
        imageBytes = assetFileSystem.readBinaryFile(virtualPath);
        binaryFilesByPath[virtualPath] = imageBytes;
    }

    if (!imageBytes || imageBytes->empty())
    {
        return std::nullopt;
    }

    std::optional<ImagePixelsBgra> image = decodeImagePixelsBgra(*imageBytes, virtualPath, options);
    if (image)
    {
        image->assetScaleTier = assetScaleTierFromResolvedPath(virtualPath);
    }
    return image;
}
}

std::optional<ImagePixelsBgra> loadImageAssetPixelsBgra(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    BinaryAssetCache &binaryFilesByPath,
    const ImageDecodeOptions &options)
{
    const std::optional<std::string> resolvedPath = assetFileSystem.resolveExistingFilePath(virtualPath);
    return resolvedPath ? loadResolvedImagePixelsBgra(assetFileSystem, *resolvedPath, binaryFilesByPath, options)
                        : std::nullopt;
}

std::optional<ImagePixelsBgra> loadImageAssetPixelsBgra(
    const AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey,
    BinaryAssetCache &binaryFilesByPath,
    const ImageDecodeOptions &options
)
{
    const std::optional<std::string> imagePath = findImageAssetPath(
        assetFileSystem,
        directoryPath,
        textureName,
        directoryAssetPathsByPath,
        assetPathByKey);

    if (!imagePath)
    {
        return std::nullopt;
    }

    return loadResolvedImagePixelsBgra(assetFileSystem, *imagePath, binaryFilesByPath, options);
}

std::vector<uint8_t> scalePixelsNearestBgra(
    const std::vector<uint8_t> &sourcePixels,
    int sourceWidth,
    int sourceHeight,
    int targetWidth,
    int targetHeight
)
{
    if (sourceWidth <= 0 || sourceHeight <= 0 || targetWidth <= 0 || targetHeight <= 0)
    {
        return {};
    }

    const size_t sourceSize = static_cast<size_t>(sourceWidth) * static_cast<size_t>(sourceHeight) * 4;

    if (sourcePixels.size() < sourceSize)
    {
        return {};
    }

    std::vector<uint8_t> targetPixels(static_cast<size_t>(targetWidth) * static_cast<size_t>(targetHeight) * 4);

    for (int targetY = 0; targetY < targetHeight; ++targetY)
    {
        const int sourceY = targetY * sourceHeight / targetHeight;

        for (int targetX = 0; targetX < targetWidth; ++targetX)
        {
            const int sourceX = targetX * sourceWidth / targetWidth;
            const size_t sourceOffset =
                (static_cast<size_t>(sourceY) * static_cast<size_t>(sourceWidth) + static_cast<size_t>(sourceX)) * 4;
            const size_t targetOffset =
                (static_cast<size_t>(targetY) * static_cast<size_t>(targetWidth) + static_cast<size_t>(targetX)) * 4;

            std::memcpy(targetPixels.data() + targetOffset, sourcePixels.data() + sourceOffset, 4);
        }
    }

    return targetPixels;
}
}
