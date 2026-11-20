// Where image assets are found and how large they are, read from file headers. Apart from ImageAssetLoader.cpp
// (the decoders, which need SDL and bimg) so that tools which only look images up or need their sizes link without
// either.
#include "engine/ImageAssetLoader.h"

#include "engine/AssetScaleTier.h"
#include "engine/render/CookedTextureHeader.h"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <memory>

namespace OpenYAMM::Engine
{
namespace
{
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

std::string stripKnownImageExtension(std::string_view textureName)
{
    const std::string lowerName = toLowerCopy(textureName);

    if (endsWith(lowerName, ".png") || endsWith(lowerName, ".bmp") || endsWith(lowerName, ".pcx"))
    {
        return std::string(textureName.substr(0, textureName.size() - 4));
    }

    return std::string(textureName);
}
}

std::optional<std::string> findAssetPathCaseInsensitive(
    const AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey
)
{
    const std::string cacheKey = directoryPath + "|" + toLowerCopy(fileName);
    const auto cachedPathIt = assetPathByKey.find(cacheKey);

    if (cachedPathIt != assetPathByKey.end())
    {
        return cachedPathIt->second;
    }

    const auto directoryAssetPathsIt = directoryAssetPathsByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pAssetPaths = nullptr;

    if (directoryAssetPathsIt != directoryAssetPathsByPath.end())
    {
        pAssetPaths = &directoryAssetPathsIt->second;
    }
    else
    {
        std::vector<std::string> entries = assetFileSystem.enumerate(directoryPath);
        std::unordered_map<std::string, std::string> assetPaths;

        for (const std::string &entry : entries)
        {
            assetPaths.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pAssetPaths =
            &directoryAssetPathsByPath.emplace(directoryPath, std::move(assetPaths)).first->second;
    }

    const auto resolvedPathIt = pAssetPaths->find(toLowerCopy(fileName));

    if (resolvedPathIt != pAssetPaths->end())
    {
        const std::optional<std::string> resolvedPath = resolvedPathIt->second;
        assetPathByKey[cacheKey] = resolvedPath;
        return resolvedPath;
    }

    assetPathByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

namespace
{
// The first candidate in the preferred scale tier wins; otherwise the first candidate found in any tier.
std::optional<std::string> findTieredAssetPath(
    const AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &stem,
    std::span<const std::string> candidateFileNames,
    const std::string &cacheKey,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey
)
{
    const auto cachedPathIt = assetPathByKey.find(cacheKey);

    if (cachedPathIt != assetPathByKey.end())
    {
        return cachedPathIt->second;
    }

    std::optional<std::string> fallbackPath;
    const AssetScaleTier preferredTier = assetFileSystem.getAssetScaleTierForVirtualPath(directoryPath + "/" + stem);
    for (const std::string &candidateFileName : candidateFileNames)
    {
        const std::optional<std::string> candidatePath = findAssetPathCaseInsensitive(
            assetFileSystem,
            directoryPath,
            candidateFileName,
            directoryAssetPathsByPath,
            assetPathByKey);

        if (candidatePath)
        {
            const std::optional<std::string> resolvedPath = assetFileSystem.resolveExistingFilePath(*candidatePath);
            if (!resolvedPath)
            {
                continue;
            }
            if (assetScaleTierFromResolvedPath(*resolvedPath) == preferredTier)
            {
                assetPathByKey[cacheKey] = resolvedPath;
                return resolvedPath;
            }
            if (!fallbackPath)
            {
                fallbackPath = resolvedPath;
            }
        }
    }

    assetPathByKey[cacheKey] = fallbackPath;
    return fallbackPath;
}
}

std::optional<std::string> findImageAssetPath(
    const AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey
)
{
    const std::string stem = stripKnownImageExtension(textureName);
    const std::array<std::string, 3> candidateFileNames = {stem + ".png", stem + ".bmp", stem + ".pcx"};
    return findTieredAssetPath(assetFileSystem, directoryPath, stem, candidateFileNames,
        directoryPath + "|image|" + toLowerCopy(textureName), directoryAssetPathsByPath, assetPathByKey);
}

std::optional<std::string> findCookedOrImageAssetPath(
    const AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey
)
{
    const std::string stem = stripKnownImageExtension(textureName);
    const std::array<std::string, 4> candidateFileNames = {
        stem + ".oytex", stem + ".png", stem + ".bmp", stem + ".pcx"};
    return findTieredAssetPath(assetFileSystem, directoryPath, stem, candidateFileNames,
        directoryPath + "|cooked-image|" + toLowerCopy(textureName), directoryAssetPathsByPath, assetPathByKey);
}

std::optional<std::array<int, 2>> findSurfaceTextureLogicalSize(
    const AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey
)
{
    const std::optional<std::string> path =
        findCookedOrImageAssetPath(assetFileSystem, "Data/bitmaps", textureName, directoryAssetPathsByPath,
            assetPathByKey);
    if (!path)
    {
        return std::nullopt;
    }
    const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(*path);
    if (!bytes || bytes->empty())
    {
        return std::nullopt;
    }
    // The size is in the file's header, cooked or not: nothing is decoded.
    int width = 0;
    int height = 0;
    if (hasCookedTextureSignature(*bytes))
    {
        const std::optional<std::array<int, 2>> size = readCookedTextureSize(*bytes);
        if (!size)
        {
            return std::nullopt;
        }
        width = (*size)[0];
        height = (*size)[1];
    }
    else if (const std::optional<ImageDimensions> dimensions =
                 readImageDimensions(std::span(bytes->data(), std::min<size_t>(bytes->size(), 128))))
    {
        width = dimensions->width;
        height = dimensions->height;
    }
    if (width <= 0 || height <= 0)
    {
        return std::nullopt;
    }
    const AssetScaleTier tier = assetScaleTierFromResolvedPath(*path);
    return std::array<int, 2>{scalePhysicalPixelsToLogical(width, tier), scalePhysicalPixelsToLogical(height, tier)};
}

std::optional<ImageDimensions> readImageDimensions(std::span<const uint8_t> header)
{
    const auto little = [&header](size_t offset, size_t bytes) -> uint32_t
    {
        uint32_t value = 0;
        for (size_t i = 0; i < bytes; ++i)
        {
            value |= uint32_t(header[offset + i]) << (8 * i);
        }
        return value;
    };
    const auto big = [&header](size_t offset) -> uint32_t
    {
        return uint32_t(header[offset]) << 24 | uint32_t(header[offset + 1]) << 16
            | uint32_t(header[offset + 2]) << 8 | header[offset + 3];
    };
    int64_t width = 0;
    int64_t height = 0;
    constexpr std::array<uint8_t, 8> pngSignature = {137, 80, 78, 71, 13, 10, 26, 10};
    if (header.size() >= 33 && std::equal(pngSignature.begin(), pngSignature.end(), header.begin()))
    {
        if (big(8) != 13 || big(12) != 0x49484452 || header[26] != 0 || header[27] != 0 || header[28] > 1)
        {
            return std::nullopt;
        }
        const int depth = header[24];
        const int color = header[25];
        const bool validDepth = (color == 0 && (depth == 1 || depth == 2 || depth == 4 || depth == 8 || depth == 16))
            || (color == 3 && (depth == 1 || depth == 2 || depth == 4 || depth == 8))
            || ((color == 2 || color == 4 || color == 6) && (depth == 8 || depth == 16));
        uint32_t crc = 0xffffffffu;
        for (size_t i = 12; i < 29; ++i)
        {
            crc ^= header[i];
            for (int bit = 0; bit < 8; ++bit)
            {
                crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
            }
        }
        if (!validDepth || (crc ^ 0xffffffffu) != big(29))
        {
            return std::nullopt;
        }
        width = big(16);
        height = big(20);
    }
    else if (header.size() >= 26 && header[0] == 'B' && header[1] == 'M' && little(14, 4) >= 40)
    {
        width = int32_t(little(18, 4));
        height = int32_t(little(22, 4));
        height = height < 0 ? -height : height;
    }
    else if (header.size() >= 128 && header[0] == 0x0a && header[2] == 1 && header[3] == 8
        && (header[65] == 1 || header[65] == 3))
    {
        width = int64_t(little(8, 2)) - little(4, 2) + 1;
        height = int64_t(little(10, 2)) - little(6, 2) + 1;
        if (width > little(66, 2))
        {
            return std::nullopt;
        }
    }
    if (width <= 0 || height <= 0 || width > INT32_MAX || height > INT32_MAX)
    {
        return std::nullopt;
    }
    return ImageDimensions{int(width), int(height)};
}

std::optional<ImageDimensions> loadImageDimensions(const AssetFileSystem &assets, const std::string &path)
{
    const std::unique_ptr<AssetReadStream> pStream = assets.openReadStream(path);
    if (!pStream)
    {
        return std::nullopt;
    }
    std::array<uint8_t, 128> header = {};
    const int64_t count = pStream->read(header.data(), header.size());
    return count > 0 ? readImageDimensions(std::span(header.data(), size_t(count))) : std::nullopt;
}
}
