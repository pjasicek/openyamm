#pragma once

#include "engine/AssetFileSystem.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
struct ImagePixelsBgra
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};

struct ImageDecodeOptions
{
    std::optional<std::array<uint8_t, 256 * 3>> overridePalette;
    bool applyPaletteZeroTransparencyKey = false;
    bool applyMagentaTransparencyKey = false;
    bool applyTealTransparencyKey = false;
    bool applyBlackTransparencyKey = false;
};

using DirectoryAssetPathCache = std::unordered_map<std::string, std::unordered_map<std::string, std::string>>;
using AssetPathLookupCache = std::unordered_map<std::string, std::optional<std::string>>;
using BinaryAssetCache = std::unordered_map<std::string, std::optional<std::vector<uint8_t>>>;

std::optional<std::string> findAssetPathCaseInsensitive(
    const AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey
);

std::optional<std::string> findImageAssetPath(
    const AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey
);

std::optional<ImagePixelsBgra> decodeImagePixelsBgra(
    const std::vector<uint8_t> &imageBytes,
    std::string_view virtualPath,
    const ImageDecodeOptions &options = {}
);

std::optional<ImagePixelsBgra> loadImageAssetPixelsBgra(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    BinaryAssetCache &binaryFilesByPath,
    const ImageDecodeOptions &options = {}
);

std::optional<ImagePixelsBgra> loadImageAssetPixelsBgra(
    const AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey,
    BinaryAssetCache &binaryFilesByPath,
    const ImageDecodeOptions &options = {}
);

std::vector<uint8_t> scalePixelsNearestBgra(
    const std::vector<uint8_t> &sourcePixels,
    int sourceWidth,
    int sourceHeight,
    int targetWidth,
    int targetHeight
);
}
