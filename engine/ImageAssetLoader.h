#pragma once

#include "engine/AssetFileSystem.h"

#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
struct ImageDimensions
{
    int width = 0;
    int height = 0;
};

// Reads PNG/BMP/PCX metadata without allocating or decoding image pixels.
std::optional<ImageDimensions> readImageDimensions(std::span<const uint8_t> header);
std::optional<ImageDimensions> loadImageDimensions(const AssetFileSystem &assets, const std::string &path);

struct ImagePixelsBgra
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
    AssetScaleTier assetScaleTier = AssetScaleTier::X1;
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

// findImageAssetPath with a cooked texture (.oytex) preferred over the images in each scale tier: world surface
// textures, whose cooked files sit beside their sources (tools/cook_surface_textures.py).
std::optional<std::string> findCookedOrImageAssetPath(
    const AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    DirectoryAssetPathCache &directoryAssetPathsByPath,
    AssetPathLookupCache &assetPathByKey
);

// A world surface texture's logical size (its native texels, the size face UVs are measured in) as the game resolves
// it through findCookedOrImageAssetPath: the cooked file or the image in the best scale tier, scaled back to the
// native tier. Empty when there is none.
std::optional<std::array<int, 2>> findSurfaceTextureLogicalSize(
    const AssetFileSystem &assetFileSystem,
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
