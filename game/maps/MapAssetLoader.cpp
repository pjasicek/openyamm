#include "game/data/ActorNameResolver.h"
#include "game/maps/MapAssetLoader.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/SpriteObjectDefs.h"
#include "game/StringUtils.h"
#include "engine/TextTable.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <limits>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t TileDescriptorNameLength = 20;
constexpr size_t TileDescriptorRecordSize = 26;
constexpr uint8_t WaterTileName[] = {'w', 't', 'r', 't', 'y', 'l', 0};
constexpr int TerrainTextureTileSize = 128;
constexpr int TerrainTextureAtlasColumns = 16;
constexpr uint16_t DecorationDescMoveThrough = 0x0001;
constexpr uint16_t DecorationDescDontDraw = 0x0002;
constexpr uint16_t LevelDecorationInvisible = 0x0020;

std::optional<std::string> resolveMonsterNameForSpawn(const MapStatsEntry &map, uint16_t typeId, uint16_t index);

std::string trimAsciiWhitespace(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

template <typename EntityType>
const DecorationEntry *resolveDecorationEntry(
    const DecorationTable &decorationTable,
    const EntityType &entity)
{
    const DecorationEntry *pDecoration = decorationTable.get(entity.decorationListId);

    if ((pDecoration == nullptr || pDecoration->spriteId == 0) && !entity.name.empty())
    {
        pDecoration = decorationTable.findByInternalName(entity.name);
    }

    return pDecoration;
}

template <typename EntityType>
bool shouldSkipDecorationCollision(const EntityType &entity, const DecorationEntry &decoration)
{
    if ((entity.aiAttributes & LevelDecorationInvisible) != 0)
    {
        return true;
    }

    if ((decoration.flags & (DecorationDescMoveThrough | DecorationDescDontDraw)) != 0)
    {
        return true;
    }

    // Entries like "smoke" are effect emitters with no base sprite and should not block movement.
    if (decoration.spriteId == 0)
    {
        return true;
    }

    if (decoration.internalName.rfind("plant", 0) == 0)
    {
        return true;
    }

    return decoration.radius <= 0 || decoration.height == 0;
}

bool shouldSkipSpriteObjectCollision(const MapDeltaSpriteObject &spriteObject, const ObjectEntry &objectEntry)
{
    if (spriteObject.objectDescriptionId == 0)
    {
        return true;
    }

    if (objectEntry.radius <= 0 || objectEntry.height <= 0)
    {
        return true;
    }

    if ((objectEntry.flags & ObjectDescNoCollision) != 0)
    {
        return true;
    }

    if ((spriteObject.attributes & (SpriteAttrTemporary | SpriteAttrMissile | SpriteAttrRemoved)) != 0)
    {
        return true;
    }

    if ((objectEntry.flags & (ObjectDescTemporary | ObjectDescTrailParticle | ObjectDescTrailFire | ObjectDescTrailLine))
        != 0)
    {
        return true;
    }

    if (spriteObject.spellId != 0)
    {
        return true;
    }

    if (hasContainingItemPayload(spriteObject.rawContainingItem) && (objectEntry.flags & ObjectDescUnpickable) == 0)
    {
        return true;
    }

    return false;
}

bool loadDecorationDisplayRows(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<std::vector<std::string>> &rows)
{
    rows.clear();

    const std::optional<std::string> contents = assetFileSystem.readTextFile("Data/EnglishT/DECLIST.TXT");

    if (!contents)
    {
        return false;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*contents);

    if (!parsedTable)
    {
        return false;
    }

    rows.reserve(parsedTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsedTable->getRow(rowIndex));
    }

    return true;
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    const uint8_t alpha = 255;

    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

bool containsCaseInsensitive(const std::string &value, const std::string &needle)
{
    return value.find(needle) != std::string::npos;
}

uint32_t colorFromTextureName(const std::string &textureName)
{
    const std::string loweredName = toLowerCopy(textureName);

    if (containsCaseInsensitive(loweredName, "wtr") || containsCaseInsensitive(loweredName, "wat"))
    {
        return makeAbgr(48, 86, 158);
    }

    if (containsCaseInsensitive(loweredName, "gras")
        || containsCaseInsensitive(loweredName, "gr")
        || containsCaseInsensitive(loweredName, "swmp"))
    {
        return makeAbgr(82, 118, 54);
    }

    if (containsCaseInsensitive(loweredName, "drt") || containsCaseInsensitive(loweredName, "dirt"))
    {
        return makeAbgr(118, 88, 52);
    }

    if (containsCaseInsensitive(loweredName, "sn") || containsCaseInsensitive(loweredName, "snow"))
    {
        return makeAbgr(218, 222, 228);
    }

    if (containsCaseInsensitive(loweredName, "lav") || containsCaseInsensitive(loweredName, "vol"))
    {
        return makeAbgr(188, 86, 34);
    }

    if (containsCaseInsensitive(loweredName, "rk") || containsCaseInsensitive(loweredName, "rock"))
    {
        return makeAbgr(124, 124, 124);
    }

    uint32_t hash = 2166136261u;

    for (const char character : loweredName)
    {
        hash ^= static_cast<uint8_t>(character);
        hash *= 16777619u;
    }

    const uint8_t red = static_cast<uint8_t>(96 + (hash & 0x3f));
    const uint8_t green = static_cast<uint8_t>(96 + ((hash >> 6) & 0x3f));
    const uint8_t blue = static_cast<uint8_t>(96 + ((hash >> 12) & 0x3f));
    return makeAbgr(red, green, blue);
}

std::string buildTileDescriptorPath(uint8_t masterTile)
{
    if (masterTile == 1)
    {
        return "Data/EnglishT/dtile2.bin";
    }

    if (masterTile == 2)
    {
        return "Data/EnglishT/dtile3.bin";
    }

    return "Data/EnglishT/dtile.bin";
}

std::optional<std::vector<std::string>> loadTileTextureNames(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData
)
{
    const std::optional<std::vector<uint8_t>> descriptorBytes =
        assetFileSystem.readBinaryFile(buildTileDescriptorPath(outdoorMapData.masterTile));

    if (!descriptorBytes || descriptorBytes->size() < sizeof(int32_t))
    {
        return std::nullopt;
    }

    int descriptorCount = 0;
    std::memcpy(&descriptorCount, descriptorBytes->data(), sizeof(descriptorCount));

    if (descriptorCount <= 0)
    {
        return std::nullopt;
    }

    const size_t expectedSize = sizeof(int32_t) + static_cast<size_t>(descriptorCount) * TileDescriptorRecordSize;

    if (descriptorBytes->size() < expectedSize)
    {
        return std::nullopt;
    }

    std::vector<std::string> tileTextureNames(256);

    for (int tileIndex = 0; tileIndex < 256; ++tileIndex)
    {
        int descriptorIndex = 0;

        if (tileIndex >= 0xc6)
        {
            descriptorIndex = tileIndex - 0xc6 + outdoorMapData.tileSetLookupIndices[3];
        }
        else if (tileIndex < 0x5a)
        {
            descriptorIndex = tileIndex;
        }
        else
        {
            const int bandIndex = (tileIndex - 0x5a) / 0x24;
            descriptorIndex = static_cast<int>(outdoorMapData.tileSetLookupIndices[bandIndex]) - (bandIndex * 0x24);
            descriptorIndex += tileIndex - 0x5a;
        }

        if (descriptorIndex < 0 || descriptorIndex >= descriptorCount)
        {
            return std::nullopt;
        }

        const size_t descriptorOffset = sizeof(int32_t) + static_cast<size_t>(descriptorIndex) * TileDescriptorRecordSize;
        const char *pName = reinterpret_cast<const char *>(descriptorBytes->data() + descriptorOffset);
        const size_t rawNameLength = strnlen(pName, TileDescriptorNameLength);

        if (rawNameLength == 0)
        {
            tileTextureNames[tileIndex] = "pending";
        }
        else
        {
            tileTextureNames[tileIndex] = std::string(pName, rawNameLength);
        }
    }

    return tileTextureNames;
}

void appendTextureNameIfMissing(std::vector<std::string> &textureNames, const std::string &textureName)
{
    if (std::find(textureNames.begin(), textureNames.end(), textureName) == textureNames.end())
    {
        textureNames.push_back(textureName);
    }
}

struct BitmapTextureRequest
{
    std::string textureName;
    int16_t paletteId = 0;
};

struct BitmapPixelsResult
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};

struct IndexedBitmapData
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> indices;
    std::array<SDL_Color, 256> palette = {};
    int paletteColorCount = 0;
};

struct BitmapLoadCache
{
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryAssetPathsByPath;
    std::unordered_map<std::string, std::optional<std::string>> bitmapPathByKey;
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> binaryFilesByPath;
    std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesById;
    std::unordered_map<std::string, std::optional<IndexedBitmapData>> indexedBitmapsByPath;
    std::unordered_map<std::string, std::optional<BitmapPixelsResult>> pixelsByKey;
};

std::optional<std::string> findBitmapPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    BitmapLoadCache &bitmapLoadCache
)
{
    const std::string cacheKey = directoryPath + "|" + toLowerCopy(textureName);
    const auto cachedPathIt = bitmapLoadCache.bitmapPathByKey.find(cacheKey);

    if (cachedPathIt != bitmapLoadCache.bitmapPathByKey.end())
    {
        return cachedPathIt->second;
    }

    const auto directoryAssetPathsIt = bitmapLoadCache.directoryAssetPathsByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pAssetPaths = nullptr;

    if (directoryAssetPathsIt != bitmapLoadCache.directoryAssetPathsByPath.end())
    {
        pAssetPaths = &directoryAssetPathsIt->second;
    }
    else
    {
        std::vector<std::string> bitmapEntries = assetFileSystem.enumerate(directoryPath);
        std::unordered_map<std::string, std::string> assetPaths;

        for (const std::string &entry : bitmapEntries)
        {
            assetPaths.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pAssetPaths = &bitmapLoadCache.directoryAssetPathsByPath.emplace(directoryPath, std::move(assetPaths)).first->second;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName) + ".bmp";
    const auto resolvedPathIt = pAssetPaths->find(normalizedTextureName);

    if (resolvedPathIt != pAssetPaths->end())
    {
        const std::optional<std::string> resolvedPath = resolvedPathIt->second;
        bitmapLoadCache.bitmapPathByKey[cacheKey] = resolvedPath;
        return resolvedPath;
    }

    bitmapLoadCache.bitmapPathByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

std::optional<std::string> findAssetPathCaseInsensitive(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName,
    BitmapLoadCache &bitmapLoadCache
)
{
    const std::string cacheKey = directoryPath + "|" + toLowerCopy(fileName);
    const auto cachedPathIt = bitmapLoadCache.bitmapPathByKey.find(cacheKey);

    if (cachedPathIt != bitmapLoadCache.bitmapPathByKey.end())
    {
        return cachedPathIt->second;
    }

    const auto directoryAssetPathsIt = bitmapLoadCache.directoryAssetPathsByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pAssetPaths = nullptr;

    if (directoryAssetPathsIt != bitmapLoadCache.directoryAssetPathsByPath.end())
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

        pAssetPaths = &bitmapLoadCache.directoryAssetPathsByPath.emplace(directoryPath, std::move(assetPaths)).first->second;
    }

    const std::string normalizedFileName = toLowerCopy(fileName);
    const auto resolvedPathIt = pAssetPaths->find(normalizedFileName);

    if (resolvedPathIt != pAssetPaths->end())
    {
        const std::optional<std::string> resolvedPath = resolvedPathIt->second;
        bitmapLoadCache.bitmapPathByKey[cacheKey] = resolvedPath;
        return resolvedPath;
    }

    bitmapLoadCache.bitmapPathByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

void appendBitmapTextureRequestIfMissing(
    std::vector<BitmapTextureRequest> &textureRequests,
    const std::string &textureName,
    int16_t paletteId
)
{
    const auto requestIt = std::find_if(
        textureRequests.begin(),
        textureRequests.end(),
        [&](const BitmapTextureRequest &request)
        {
            return request.textureName == textureName && request.paletteId == paletteId;
        }
    );

    if (requestIt == textureRequests.end())
    {
        BitmapTextureRequest request = {};
        request.textureName = textureName;
        request.paletteId = paletteId;
        textureRequests.push_back(std::move(request));
    }
}

std::optional<std::array<uint8_t, 256 * 3>> loadActPalette(
    const Engine::AssetFileSystem &assetFileSystem,
    int16_t paletteId,
    BitmapLoadCache &bitmapLoadCache
)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    const auto cachedPaletteIt = bitmapLoadCache.actPalettesById.find(paletteId);

    if (cachedPaletteIt != bitmapLoadCache.actPalettesById.end())
    {
        return cachedPaletteIt->second;
    }

    char paletteFileName[16] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));
    const std::optional<std::string> palettePath =
        findAssetPathCaseInsensitive(assetFileSystem, "Data/bitmaps", paletteFileName, bitmapLoadCache);

    if (!palettePath)
    {
        bitmapLoadCache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    const std::string &palettePathString = *palettePath;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(palettePathString);
    std::optional<std::vector<uint8_t>> paletteBytes;

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        paletteBytes = cachedFileIt->second;
    }
    else
    {
        paletteBytes = assetFileSystem.readBinaryFile(palettePathString);
        bitmapLoadCache.binaryFilesByPath[palettePathString] = paletteBytes;
    }

    if (!paletteBytes || paletteBytes->size() < 256 * 3)
    {
        bitmapLoadCache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    std::array<uint8_t, 256 * 3> palette = {};
    std::memcpy(palette.data(), paletteBytes->data(), palette.size());
    bitmapLoadCache.actPalettesById[paletteId] = palette;
    return palette;
}

std::optional<IndexedBitmapData> loadIndexedBitmapData(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &bitmapPath,
    BitmapLoadCache &bitmapLoadCache
)
{
    const auto cachedBitmapIt = bitmapLoadCache.indexedBitmapsByPath.find(bitmapPath);

    if (cachedBitmapIt != bitmapLoadCache.indexedBitmapsByPath.end())
    {
        return cachedBitmapIt->second;
    }

    std::optional<std::vector<uint8_t>> bitmapBytes;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(bitmapPath);

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        bitmapBytes = cachedFileIt->second;
    }
    else
    {
        bitmapBytes = assetFileSystem.readBinaryFile(bitmapPath);
        bitmapLoadCache.binaryFilesByPath[bitmapPath] = bitmapBytes;
    }

    if (!bitmapBytes || bitmapBytes->empty())
    {
        bitmapLoadCache.indexedBitmapsByPath[bitmapPath] = std::nullopt;
        return std::nullopt;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

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
    const bool canApplyPalette = pLoadedSurface->format == SDL_PIXELFORMAT_INDEX8 && pBasePalette != nullptr;

    if (!canApplyPalette)
    {
        SDL_DestroySurface(pLoadedSurface);
        bitmapLoadCache.indexedBitmapsByPath[bitmapPath] = std::nullopt;
        return std::nullopt;
    }

    IndexedBitmapData indexedBitmap = {};
    indexedBitmap.width = pLoadedSurface->w;
    indexedBitmap.height = pLoadedSurface->h;
    indexedBitmap.paletteColorCount = pBasePalette->ncolors;
    indexedBitmap.indices.resize(static_cast<size_t>(indexedBitmap.width * indexedBitmap.height));

    for (int paletteIndex = 0; paletteIndex < std::min(256, pBasePalette->ncolors); ++paletteIndex)
    {
        indexedBitmap.palette[static_cast<size_t>(paletteIndex)] = pBasePalette->colors[paletteIndex];
    }

    for (int row = 0; row < indexedBitmap.height; ++row)
    {
        const uint8_t *pSourceRow = static_cast<const uint8_t *>(pLoadedSurface->pixels) + row * pLoadedSurface->pitch;
        uint8_t *pTargetRow = indexedBitmap.indices.data()
            + static_cast<ptrdiff_t>(row * indexedBitmap.width);
        std::memcpy(pTargetRow, pSourceRow, static_cast<size_t>(indexedBitmap.width));
    }

    SDL_DestroySurface(pLoadedSurface);
    bitmapLoadCache.indexedBitmapsByPath[bitmapPath] = indexedBitmap;
    return indexedBitmap;
}

std::optional<std::vector<uint8_t>> loadIndexedBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &bitmapPath,
    int16_t paletteId,
    int &width,
    int &height,
    bool applyTransparencyKey,
    BitmapLoadCache &bitmapLoadCache
)
{
    const std::optional<IndexedBitmapData> indexedBitmap =
        loadIndexedBitmapData(assetFileSystem, bitmapPath, bitmapLoadCache);
    const std::optional<std::array<uint8_t, 256 * 3>> overridePalette =
        loadActPalette(assetFileSystem, paletteId, bitmapLoadCache);

    if (!indexedBitmap || !overridePalette)
    {
        return std::nullopt;
    }

    width = indexedBitmap->width;
    height = indexedBitmap->height;
    std::vector<uint8_t> pixels(static_cast<size_t>(width * height * 4));

    for (int row = 0; row < height; ++row)
    {
        const uint8_t *pSourceRow =
            indexedBitmap->indices.data() + static_cast<ptrdiff_t>(row * indexedBitmap->width);

        for (int column = 0; column < width; ++column)
        {
            const uint8_t paletteIndex = pSourceRow[column];
            const size_t pixelOffset = static_cast<size_t>((row * width + column) * 4);
            const SDL_Color sourceColor =
                paletteIndex < indexedBitmap->paletteColorCount
                    ? indexedBitmap->palette[paletteIndex]
                    : SDL_Color{0, 0, 0, 255};
            const bool isMagentaKey = sourceColor.r >= 248 && sourceColor.g <= 8 && sourceColor.b >= 248;
            const bool isTealKey = applyTransparencyKey && sourceColor.r <= 8 && sourceColor.g >= 248 && sourceColor.b >= 248;
            const size_t paletteOffset = static_cast<size_t>(paletteIndex) * 3;

            pixels[pixelOffset + 0] = (*overridePalette)[paletteOffset + 2];
            pixels[pixelOffset + 1] = (*overridePalette)[paletteOffset + 1];
            pixels[pixelOffset + 2] = (*overridePalette)[paletteOffset + 0];
            pixels[pixelOffset + 3] = (isMagentaKey || isTealKey) ? 0 : 255;
        }
    }

    return pixels;
}

std::optional<std::vector<uint8_t>> loadBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    int &width,
    int &height,
    bool forceTerrainTileSize,
    bool applyTransparencyKey,
    BitmapLoadCache &bitmapLoadCache,
    int16_t paletteId = 0
)
{
    const std::string cacheKey =
        directoryPath + "|" + toLowerCopy(textureName)
        + "|" + std::to_string(forceTerrainTileSize ? 1 : 0)
        + "|" + std::to_string(applyTransparencyKey ? 1 : 0)
        + "|" + std::to_string(static_cast<int>(paletteId));
    const auto cachedPixelsIt = bitmapLoadCache.pixelsByKey.find(cacheKey);

    if (cachedPixelsIt != bitmapLoadCache.pixelsByKey.end())
    {
        if (!cachedPixelsIt->second)
        {
            return std::nullopt;
        }

        width = cachedPixelsIt->second->width;
        height = cachedPixelsIt->second->height;
        return cachedPixelsIt->second->pixels;
    }

    const std::optional<std::string> bitmapPath =
        findBitmapPath(assetFileSystem, directoryPath, textureName, bitmapLoadCache);

    if (!bitmapPath)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    std::optional<std::vector<uint8_t>> bitmapBytes;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(*bitmapPath);

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        bitmapBytes = cachedFileIt->second;
    }
    else
    {
        bitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);
        bitmapLoadCache.binaryFilesByPath[*bitmapPath] = bitmapBytes;
    }

    if (!bitmapBytes || bitmapBytes->empty())
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    if (paletteId > 0 && !forceTerrainTileSize)
    {
        if (const std::optional<std::vector<uint8_t>> indexedPixels = loadIndexedBitmapPixelsBgra(
                assetFileSystem,
                *bitmapPath,
                paletteId,
                width,
                height,
                applyTransparencyKey,
                bitmapLoadCache))
        {
            bitmapLoadCache.pixelsByKey[cacheKey] = BitmapPixelsResult{width, height, *indexedPixels};
            return indexedPixels;
        }
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    SDL_Surface *pSurfaceToCopy = pConvertedSurface;

    if (forceTerrainTileSize
        && (pConvertedSurface->w != TerrainTextureTileSize || pConvertedSurface->h != TerrainTextureTileSize))
    {
        SDL_Surface *pScaledSurface =
            SDL_ScaleSurface(pConvertedSurface, TerrainTextureTileSize, TerrainTextureTileSize, SDL_SCALEMODE_NEAREST);
        SDL_DestroySurface(pConvertedSurface);
        pSurfaceToCopy = pScaledSurface;

        if (pSurfaceToCopy == nullptr)
        {
            bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
            return std::nullopt;
        }
    }

    width = pSurfaceToCopy->w;
    height = pSurfaceToCopy->h;
    std::vector<uint8_t> pixels(static_cast<size_t>(width * height * 4));

    for (int row = 0; row < height; ++row)
    {
        const uint8_t *pSourceRow = static_cast<const uint8_t *>(pSurfaceToCopy->pixels) + row * pSurfaceToCopy->pitch;
        uint8_t *pTargetRow = pixels.data() + static_cast<size_t>(row * width * 4);
        std::memcpy(pTargetRow, pSourceRow, static_cast<size_t>(width * 4));
    }

    for (size_t pixelOffset = 0; pixelOffset < pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = pixels[pixelOffset + 0];
        const uint8_t green = pixels[pixelOffset + 1];
        const uint8_t red = pixels[pixelOffset + 2];

        const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
        const bool isTealKey = applyTransparencyKey && red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isTealKey)
        {
            pixels[pixelOffset + 3] = 0;
        }
    }

    SDL_DestroySurface(pSurfaceToCopy);
    bitmapLoadCache.pixelsByKey[cacheKey] = BitmapPixelsResult{width, height, pixels};
    return pixels;
}

template <typename EntityType>
std::optional<DecorationBillboardSet> buildDecorationBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<EntityType> &entities,
    BitmapLoadCache &bitmapLoadCache
)
{
    const std::optional<std::vector<uint8_t>> decorationTableBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/ddeclist.bin");
    const std::optional<std::vector<uint8_t>> spriteFrameTableBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/dsft.bin");

    if (!decorationTableBytes || !spriteFrameTableBytes)
    {
        return std::nullopt;
    }

    DecorationBillboardSet billboardSet = {};

    if (!billboardSet.decorationTable.loadFromBytes(*decorationTableBytes)
        || !billboardSet.spriteFrameTable.loadFromBytes(*spriteFrameTableBytes))
    {
        return std::nullopt;
    }

    std::vector<std::vector<std::string>> decorationRows;

    if (loadDecorationDisplayRows(assetFileSystem, decorationRows))
    {
        billboardSet.decorationTable.loadDisplayRows(decorationRows);
    }

    std::vector<std::string> textureNames;

    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const EntityType &entity = entities[entityIndex];
        const DecorationEntry *pDecoration = resolveDecorationEntry(billboardSet.decorationTable, entity);

        if (pDecoration == nullptr || pDecoration->spriteId == 0)
        {
            continue;
        }

        DecorationBillboard billboard = {};
        billboard.entityIndex = entityIndex;
        billboard.decorationId = entity.decorationListId;
        billboard.spriteId = pDecoration->spriteId;
        billboard.flags = pDecoration->flags;
        billboard.height = pDecoration->height;
        billboard.radius = pDecoration->radius;
        billboard.x = entity.x;
        billboard.y = entity.y;
        billboard.z = entity.z;
        billboard.facing = entity.facing;
        billboard.name = entity.name;
        billboardSet.billboards.push_back(std::move(billboard));

        const std::vector<std::string> billboardTextureNames =
            billboardSet.spriteFrameTable.collectTextureNames(pDecoration->spriteId);

        for (const std::string &textureName : billboardTextureNames)
        {
            if (std::find(textureNames.begin(), textureNames.end(), textureName) == textureNames.end())
            {
                textureNames.push_back(textureName);
            }
        }
    }

    if (billboardSet.billboards.empty())
    {
        return std::nullopt;
    }

    for (const std::string &textureName : textureNames)
    {
        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/sprites",
                textureName,
                textureWidth,
                textureHeight,
                false,
                true,
                bitmapLoadCache
            );

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureName;
        texture.width = textureWidth;
        texture.height = textureHeight;
        texture.pixels = *pixels;
        billboardSet.textures.push_back(std::move(texture));
    }

    return billboardSet;
}

template <typename EntityType>
std::optional<OutdoorDecorationCollisionSet> buildOutdoorDecorationCollisionSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<EntityType> &entities
)
{
    const std::optional<std::vector<uint8_t>> decorationTableBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/ddeclist.bin");

    if (!decorationTableBytes)
    {
        return std::nullopt;
    }

    DecorationTable decorationTable;

    if (!decorationTable.loadFromBytes(*decorationTableBytes))
    {
        return std::nullopt;
    }

    std::vector<std::vector<std::string>> decorationRows;

    if (loadDecorationDisplayRows(assetFileSystem, decorationRows))
    {
        decorationTable.loadDisplayRows(decorationRows);
    }

    OutdoorDecorationCollisionSet collisionSet = {};

    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const EntityType &entity = entities[entityIndex];
        const DecorationEntry *pDecoration = resolveDecorationEntry(decorationTable, entity);

        if (pDecoration == nullptr)
        {
            continue;
        }

        if (shouldSkipDecorationCollision(entity, *pDecoration))
        {
            continue;
        }

        OutdoorDecorationCollision collision = {};
        collision.entityIndex = entityIndex;
        collision.decorationId = entity.decorationListId;
        collision.descriptionFlags = pDecoration->flags;
        collision.instanceFlags = entity.aiAttributes;
        collision.radius = pDecoration->radius;
        collision.height = pDecoration->height;
        collision.worldX = -entity.x;
        collision.worldY = entity.y;
        collision.worldZ = entity.z;
        collision.name = entity.name.empty() ? pDecoration->internalName : entity.name;
        collisionSet.colliders.push_back(std::move(collision));
    }

    if (collisionSet.colliders.empty())
    {
        return std::nullopt;
    }

    return collisionSet;
}

void appendMapDeltaActorCollisions(
    OutdoorActorCollisionSet &collisionSet,
    const MapDeltaData &mapDeltaData,
    const OutdoorMapData *pOutdoorMapData
)
{
    for (size_t actorIndex = 0; actorIndex < mapDeltaData.actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = mapDeltaData.actors[actorIndex];

        if (actor.radius == 0 || actor.height == 0)
        {
            continue;
        }

        int actorZ = actor.z;

        if (pOutdoorMapData != nullptr)
        {
            actorZ = static_cast<int>(std::lround(sampleOutdoorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(-actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(actorZ))));
        }

        OutdoorActorCollision collision = {};
        collision.sourceIndex = actorIndex;
        collision.source = OutdoorActorCollisionSource::MapDelta;
        collision.radius = actor.radius;
        collision.height = actor.height;
        collision.worldX = -actor.x;
        collision.worldY = actor.y;
        collision.worldZ = actorZ;
        collision.attributes = actor.attributes;
        collision.group = actor.group;
        collision.name = actor.name;
        collisionSet.colliders.push_back(std::move(collision));
    }
}

template <typename SpawnType>
void appendSpawnActorCollisions(
    OutdoorActorCollisionSet &collisionSet,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const std::vector<SpawnType> &spawns,
    const OutdoorMapData *pOutdoorMapData
)
{
    for (size_t spawnIndex = 0; spawnIndex < spawns.size(); ++spawnIndex)
    {
        const SpawnType &spawn = spawns[spawnIndex];
        const std::optional<std::string> monsterName = resolveMonsterNameForSpawn(map, spawn.typeId, spawn.index);

        if (!monsterName)
        {
            continue;
        }

        const MonsterEntry *pMonsterEntry = monsterTable.findByInternalName(*monsterName);

        if (pMonsterEntry == nullptr || pMonsterEntry->radius == 0 || pMonsterEntry->height == 0)
        {
            continue;
        }

        int actorZ = spawn.z;

        if (pOutdoorMapData != nullptr)
        {
            actorZ = static_cast<int>(std::lround(sampleOutdoorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(-spawn.x),
                static_cast<float>(spawn.y),
                static_cast<float>(actorZ))));
        }

        OutdoorActorCollision collision = {};
        collision.sourceIndex = spawnIndex;
        collision.source = OutdoorActorCollisionSource::Spawn;
        collision.radius = pMonsterEntry->radius;
        collision.height = pMonsterEntry->height;
        collision.worldX = -spawn.x;
        collision.worldY = spawn.y;
        collision.worldZ = actorZ;
        collision.attributes = spawn.attributes;
        collision.group = spawn.group;
        collision.name = *monsterName;
        collisionSet.colliders.push_back(std::move(collision));
    }
}

template <typename SpawnType>
std::optional<OutdoorActorCollisionSet> buildOutdoorActorCollisionSet(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const std::optional<MapDeltaData> &mapDeltaData,
    const std::vector<SpawnType> &spawns,
    const OutdoorMapData *pOutdoorMapData
)
{
    OutdoorActorCollisionSet collisionSet = {};

    if (mapDeltaData)
    {
        appendMapDeltaActorCollisions(collisionSet, *mapDeltaData, pOutdoorMapData);
    }

    appendSpawnActorCollisions(collisionSet, map, monsterTable, spawns, pOutdoorMapData);

    if (collisionSet.colliders.empty())
    {
        return std::nullopt;
    }

    return collisionSet;
}

std::optional<DecorationBillboardSet> buildOutdoorDecorationBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache
)
{
    return buildDecorationBillboardSet(assetFileSystem, outdoorMapData.entities, bitmapLoadCache);
}

std::optional<DecorationBillboardSet> buildIndoorDecorationBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const IndoorMapData &indoorMapData,
    BitmapLoadCache &bitmapLoadCache
)
{
    return buildDecorationBillboardSet(assetFileSystem, indoorMapData.entities, bitmapLoadCache);
}

std::optional<SpriteObjectBillboardSet> buildSpriteObjectBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const ObjectTable &objectTable,
    const std::optional<MapDeltaData> &mapDeltaData,
    BitmapLoadCache &bitmapLoadCache
)
{
    if (!mapDeltaData || mapDeltaData->spriteObjects.empty())
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> spriteFrameTableBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/dsft.bin");

    if (!spriteFrameTableBytes)
    {
        return std::nullopt;
    }

    SpriteObjectBillboardSet billboardSet = {};

    if (!billboardSet.spriteFrameTable.loadFromBytes(*spriteFrameTableBytes))
    {
        return std::nullopt;
    }

    std::vector<std::string> textureNames;

    for (size_t objectIndex = 0; objectIndex < mapDeltaData->spriteObjects.size(); ++objectIndex)
    {
        const MapDeltaSpriteObject &spriteObject = mapDeltaData->spriteObjects[objectIndex];
        const ObjectEntry *pObjectEntry = objectTable.get(spriteObject.objectDescriptionId);

        if (pObjectEntry == nullptr || (pObjectEntry->flags & 0x0001) != 0 || pObjectEntry->spriteId == 0)
        {
            continue;
        }

        if (hasContainingItemPayload(spriteObject.rawContainingItem)
            && (pObjectEntry->flags & ObjectDescUnpickable) == 0)
        {
            continue;
        }

        const SpriteFrameEntry *pFrame =
            billboardSet.spriteFrameTable.getFrame(pObjectEntry->spriteId, uint32_t(spriteObject.timeSinceCreated) * 8);

        SpriteObjectBillboard billboard = {};
        billboard.index = objectIndex;
        billboard.spriteFrameIndex = pObjectEntry->spriteId;
        billboard.objectDescriptionId = spriteObject.objectDescriptionId;
        billboard.objectSpriteId = pObjectEntry->spriteId;
        billboard.attributes = spriteObject.attributes;
        billboard.soundId = spriteObject.soundId;
        billboard.x = spriteObject.x;
        billboard.y = spriteObject.y;
        billboard.z = spriteObject.z;
        billboard.radius = pObjectEntry->radius;
        billboard.height = pObjectEntry->height;
        billboard.sectorId = spriteObject.sectorId;
        billboard.temporaryLifetime = spriteObject.temporaryLifetime;
        billboard.glowRadiusMultiplier = spriteObject.glowRadiusMultiplier;
        billboard.spellId = spriteObject.spellId;
        billboard.spellLevel = spriteObject.spellLevel;
        billboard.spellSkill = spriteObject.spellSkill;
        billboard.spellCasterPid = spriteObject.spellCasterPid;
        billboard.spellTargetPid = spriteObject.spellTargetPid;
        billboard.timeSinceCreatedTicks = uint32_t(spriteObject.timeSinceCreated) * 8;
        billboard.objectName = pObjectEntry->internalName;
        billboardSet.billboards.push_back(std::move(billboard));

        if (pFrame == nullptr)
        {
            continue;
        }

        const std::vector<std::string> billboardTextureNames =
            billboardSet.spriteFrameTable.collectTextureNames(pObjectEntry->spriteId);

        for (const std::string &textureName : billboardTextureNames)
        {
            appendTextureNameIfMissing(textureNames, textureName);
        }
    }

    if (billboardSet.billboards.empty())
    {
        return std::nullopt;
    }

    for (const std::string &textureName : textureNames)
    {
        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/sprites",
                textureName,
                textureWidth,
                textureHeight,
                false,
                true,
                bitmapLoadCache
            );

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureName;
        texture.width = textureWidth;
        texture.height = textureHeight;
        texture.pixels = *pixels;
        billboardSet.textures.push_back(std::move(texture));
    }

    for (const SpriteObjectBillboard &billboard : billboardSet.billboards)
    {
        const SpriteFrameEntry *pFrame =
            billboardSet.spriteFrameTable.getFrame(billboard.objectSpriteId, billboard.timeSinceCreatedTicks);

        if (pFrame == nullptr)
        {
            ++billboardSet.missingTextureObjectCount;
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const auto textureIt = std::find_if(
            billboardSet.textures.begin(),
            billboardSet.textures.end(),
            [&resolvedTexture](const OutdoorBitmapTexture &texture)
            {
                return texture.textureName == resolvedTexture.textureName;
            }
        );

        if (textureIt == billboardSet.textures.end())
        {
            ++billboardSet.missingTextureObjectCount;
        }
        else
        {
            ++billboardSet.texturedObjectCount;
        }
    }

    return billboardSet;
}

std::optional<OutdoorSpriteObjectCollisionSet> buildOutdoorSpriteObjectCollisionSet(
    const ObjectTable &objectTable,
    const std::optional<MapDeltaData> &mapDeltaData
)
{
    if (!mapDeltaData || mapDeltaData->spriteObjects.empty())
    {
        return std::nullopt;
    }

    OutdoorSpriteObjectCollisionSet collisionSet = {};

    for (size_t objectIndex = 0; objectIndex < mapDeltaData->spriteObjects.size(); ++objectIndex)
    {
        const MapDeltaSpriteObject &spriteObject = mapDeltaData->spriteObjects[objectIndex];
        const ObjectEntry *pObjectEntry = objectTable.get(spriteObject.objectDescriptionId);

        if (pObjectEntry == nullptr || shouldSkipSpriteObjectCollision(spriteObject, *pObjectEntry))
        {
            continue;
        }

        OutdoorSpriteObjectCollision collision = {};
        collision.sourceIndex = objectIndex;
        collision.objectDescriptionId = spriteObject.objectDescriptionId;
        collision.objectAttributes = spriteObject.attributes;
        collision.objectFlags = pObjectEntry->flags;
        collision.radius = static_cast<uint16_t>(pObjectEntry->radius);
        collision.height = static_cast<uint16_t>(pObjectEntry->height);
        collision.worldX = -spriteObject.x;
        collision.worldY = spriteObject.y;
        collision.worldZ = spriteObject.z;
        collision.spellId = spriteObject.spellId;
        collision.name = pObjectEntry->internalName;
        collisionSet.colliders.push_back(std::move(collision));
    }

    if (collisionSet.colliders.empty())
    {
        return std::nullopt;
    }

    return collisionSet;
}

std::optional<std::string> resolveMonsterNameForSpawn(const MapStatsEntry &map, uint16_t typeId, uint16_t index)
{
    if (typeId != 3)
    {
        return std::nullopt;
    }

    if (index >= 1 && index <= 3)
    {
        const MapEncounterInfo *pEncounter = nullptr;

        if (index == 1)
        {
            pEncounter = &map.encounter1;
        }
        else if (index == 2)
        {
            pEncounter = &map.encounter2;
        }
        else
        {
            pEncounter = &map.encounter3;
        }

        if (pEncounter != nullptr && !pEncounter->monsterName.empty())
        {
            return pEncounter->monsterName + " A";
        }
    }

    if (index >= 4 && index <= 12)
    {
        const int encounterSlot = ((index - 4) % 3) + 1;
        const char tierSuffix = static_cast<char>('A' + ((index - 4) / 3));
        const MapEncounterInfo *pEncounter = nullptr;

        if (encounterSlot == 1)
        {
            pEncounter = &map.encounter1;
        }
        else if (encounterSlot == 2)
        {
            pEncounter = &map.encounter2;
        }
        else
        {
            pEncounter = &map.encounter3;
        }

        if (pEncounter != nullptr && !pEncounter->monsterName.empty())
        {
            return pEncounter->monsterName + " " + std::string(1, tierSuffix);
        }
    }

    return std::nullopt;
}

int16_t resolveMapDeltaActorMonsterId(const MapDeltaActor &actor)
{
    if (actor.monsterInfoId > 0)
    {
        return actor.monsterInfoId;
    }

    if (actor.monsterId > 0)
    {
        return actor.monsterId;
    }

    return 0;
}

std::array<uint16_t, 8> buildMonsterActionSpriteFrameIndices(
    const SpriteFrameTable &spriteFrameTable,
    const MonsterEntry *pMonsterEntry
)
{
    std::array<uint16_t, 8> spriteFrameIndices = {};

    if (pMonsterEntry == nullptr)
    {
        return spriteFrameIndices;
    }

    for (size_t actionIndex = 0; actionIndex < spriteFrameIndices.size(); ++actionIndex)
    {
        const std::string &spriteName = pMonsterEntry->spriteNames[actionIndex];

        if (spriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            spriteFrameIndices[actionIndex] = *frameIndex;
        }
    }

    return spriteFrameIndices;
}

void appendSpriteFrameTextures(
    std::vector<BitmapTextureRequest> &textureRequests,
    const SpriteFrameTable &spriteFrameTable,
    uint16_t spriteFrameIndex
)
{
    if (spriteFrameIndex == 0)
    {
        return;
    }

    size_t frameIndex = spriteFrameIndex;

    while (frameIndex <= std::numeric_limits<uint16_t>::max())
    {
        const SpriteFrameEntry *pFrame = spriteFrameTable.getFrame(static_cast<uint16_t>(frameIndex), 0);

        if (pFrame == nullptr)
        {
            return;
        }

        for (int octant = 0; octant < 8; ++octant)
        {
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            appendBitmapTextureRequestIfMissing(textureRequests, resolvedTexture.textureName, pFrame->paletteId);
        }

        if (!SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::HasMore))
        {
            return;
        }

        ++frameIndex;
    }
}

void appendMonsterActionTextures(
    std::vector<BitmapTextureRequest> &textureRequests,
    const SpriteFrameTable &spriteFrameTable,
    const std::array<uint16_t, 8> &actionSpriteFrameIndices
)
{
    for (uint16_t spriteFrameIndex : actionSpriteFrameIndices)
    {
        appendSpriteFrameTextures(textureRequests, spriteFrameTable, spriteFrameIndex);
    }
}

void appendMapDeltaActors(
    ActorPreviewBillboardSet &billboardSet,
    std::vector<BitmapTextureRequest> &textureRequests,
    const MonsterTable &monsterTable,
    const MapDeltaData &mapDeltaData,
    const OutdoorMapData *pOutdoorMapData
)
{
    for (size_t actorIndex = 0; actorIndex < mapDeltaData.actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = mapDeltaData.actors[actorIndex];
        uint16_t spriteFrameIndex = 0;
        uint16_t savedSpriteFrameIndex = 0;
        const MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
            monsterTable.findDisplayEntryById(actor.monsterInfoId);
        const MonsterEntry *pMonsterEntry = nullptr;
        std::string resolvedActorName = resolveMapDeltaActorName(monsterTable, actor);

        if (pDisplayEntry != nullptr)
        {
            pMonsterEntry = monsterTable.findByInternalName(pDisplayEntry->pictureName);
        }
        else
        {
            pMonsterEntry = monsterTable.findById(actor.monsterId);
        }

        if (spriteFrameIndex == 0 && pMonsterEntry != nullptr)
        {
            for (const std::string &spriteName : pMonsterEntry->spriteNames)
            {
                if (spriteName.empty())
                {
                    continue;
                }

                const std::optional<uint16_t> frameIndex =
                    billboardSet.spriteFrameTable.findFrameIndexBySpriteName(spriteName);

                if (frameIndex)
                {
                    spriteFrameIndex = *frameIndex;
                    break;
                }
            }
        }

        const std::array<uint16_t, 8> actionSpriteFrameIndices =
            buildMonsterActionSpriteFrameIndices(billboardSet.spriteFrameTable, pMonsterEntry);

        for (const uint16_t spriteId : actor.spriteIds)
        {
            if (spriteId == 0)
            {
                continue;
            }

            const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(spriteId, 0);

            if (pFrame == nullptr)
            {
                continue;
            }

            savedSpriteFrameIndex = spriteId;
            break;
        }

        if (spriteFrameIndex == 0)
        {
            spriteFrameIndex = savedSpriteFrameIndex;
        }

        ActorPreviewBillboard billboard = {};
        billboard.spawnIndex = 0;
        billboard.runtimeActorIndex = actorIndex;
        billboard.spriteFrameIndex = spriteFrameIndex;
        billboard.actionSpriteFrameIndices = actionSpriteFrameIndices;
        billboard.npcId = actor.npcId;
        billboard.monsterId = resolveMapDeltaActorMonsterId(actor);
        billboard.x = actor.x;
        billboard.y = actor.y;
        billboard.z = actor.z;

        if (pOutdoorMapData != nullptr)
        {
            billboard.z = static_cast<int>(std::lround(sampleOutdoorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(-actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(billboard.z))));
        }

        billboard.radius = actor.radius;
        billboard.height = actor.height;
        billboard.typeId = 3;
        billboard.index = 0;
        billboard.attributes = static_cast<uint16_t>(actor.attributes & 0xffff);
        billboard.group = actor.group;
        billboard.uniqueNameIndex = actor.uniqueNameIndex;
        billboard.useStaticFrame = spriteFrameIndex != 0 && spriteFrameIndex == savedSpriteFrameIndex;
        billboard.isFriendly = true;
        billboard.source = ActorPreviewSource::Companion;
        billboard.actorName = resolvedActorName;
        billboardSet.billboards.push_back(std::move(billboard));
        ++billboardSet.mapDeltaActorCount;

        appendMonsterActionTextures(textureRequests, billboardSet.spriteFrameTable, actionSpriteFrameIndices);
        appendSpriteFrameTextures(textureRequests, billboardSet.spriteFrameTable, spriteFrameIndex);
    }
}

template <typename SpawnType>
void appendSpawnActors(
    ActorPreviewBillboardSet &billboardSet,
    std::vector<BitmapTextureRequest> &textureRequests,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const std::vector<SpawnType> &spawns,
    const OutdoorMapData *pOutdoorMapData
)
{
    for (size_t spawnIndex = 0; spawnIndex < spawns.size(); ++spawnIndex)
    {
        const SpawnType &spawn = spawns[spawnIndex];
        const std::optional<std::string> monsterName = resolveMonsterNameForSpawn(map, spawn.typeId, spawn.index);

        if (!monsterName)
        {
            continue;
        }

        const MonsterEntry *pMonsterEntry = monsterTable.findByInternalName(*monsterName);

        if (pMonsterEntry == nullptr)
        {
            continue;
        }

        std::string previewSpriteName;

        for (const std::string &spriteName : pMonsterEntry->spriteNames)
        {
            if (!spriteName.empty())
            {
                previewSpriteName = spriteName;
                break;
            }
        }

        if (previewSpriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex =
            billboardSet.spriteFrameTable.findFrameIndexBySpriteName(previewSpriteName);

        if (!frameIndex)
        {
            continue;
        }

        const std::array<uint16_t, 8> actionSpriteFrameIndices =
            buildMonsterActionSpriteFrameIndices(billboardSet.spriteFrameTable, pMonsterEntry);
        const MonsterTable::MonsterStatsEntry *pStats =
            monsterTable.findStatsByPictureName(*monsterName);

        ActorPreviewBillboard billboard = {};
        billboard.spawnIndex = spawnIndex;
        billboard.runtimeActorIndex = static_cast<size_t>(-1);
        billboard.spriteFrameIndex = *frameIndex;
        billboard.actionSpriteFrameIndices = actionSpriteFrameIndices;
        billboard.monsterId = pStats != nullptr ? static_cast<int16_t>(pStats->id) : 0;
        billboard.x = spawn.x;
        billboard.y = spawn.y;
        billboard.z = spawn.z;

        if (pOutdoorMapData != nullptr)
        {
            billboard.z = static_cast<int>(std::lround(sampleOutdoorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(-spawn.x),
                static_cast<float>(spawn.y),
                static_cast<float>(billboard.z))));
        }

        billboard.radius = static_cast<uint16_t>(std::max<int>(pMonsterEntry->radius, 0));
        billboard.height = static_cast<uint16_t>(std::max<int>(pMonsterEntry->height, 0));
        billboard.typeId = spawn.typeId;
        billboard.index = spawn.index;
        billboard.attributes = spawn.attributes;
        billboard.group = spawn.group;
        billboard.uniqueNameIndex = 0;
        billboard.useStaticFrame = false;
        billboard.isFriendly = true;
        billboard.source = ActorPreviewSource::Spawn;
        billboard.actorName = *monsterName;
        billboardSet.billboards.push_back(std::move(billboard));
        ++billboardSet.spawnActorCount;

        appendMonsterActionTextures(textureRequests, billboardSet.spriteFrameTable, actionSpriteFrameIndices);
        appendSpriteFrameTextures(textureRequests, billboardSet.spriteFrameTable, *frameIndex);
    }
}

template <typename SpawnType>
std::optional<ActorPreviewBillboardSet> buildActorPreviewBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const std::optional<MapDeltaData> &mapDeltaData,
    const std::vector<SpawnType> &spawns,
    BitmapLoadCache &bitmapLoadCache,
    const OutdoorMapData *pOutdoorMapData = nullptr,
    bool decodeTextures = true
)
{
    const std::optional<std::vector<uint8_t>> spriteFrameTableBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/dsft.bin");

    if (!spriteFrameTableBytes)
    {
        return std::nullopt;
    }

    ActorPreviewBillboardSet billboardSet = {};

    if (!billboardSet.spriteFrameTable.loadFromBytes(*spriteFrameTableBytes))
    {
        return std::nullopt;
    }

    std::vector<BitmapTextureRequest> textureRequests;

    if (mapDeltaData)
    {
        appendMapDeltaActors(billboardSet, textureRequests, monsterTable, *mapDeltaData, pOutdoorMapData);
    }

    appendSpawnActors(billboardSet, textureRequests, map, monsterTable, spawns, pOutdoorMapData);

    if (billboardSet.billboards.empty())
    {
        return std::nullopt;
    }

    if (decodeTextures)
    {
        for (const BitmapTextureRequest &textureRequest : textureRequests)
        {
            int textureWidth = 0;
            int textureHeight = 0;
            const std::optional<std::vector<uint8_t>> pixels =
                loadBitmapPixelsBgra(
                    assetFileSystem,
                    "Data/sprites",
                    textureRequest.textureName,
                    textureWidth,
                    textureHeight,
                    false,
                    true,
                    bitmapLoadCache,
                    textureRequest.paletteId);

            if (!pixels || textureWidth <= 0 || textureHeight <= 0)
            {
                continue;
            }

            OutdoorBitmapTexture texture = {};
            texture.textureName = textureRequest.textureName;
            texture.paletteId = textureRequest.paletteId;
            texture.width = textureWidth;
            texture.height = textureHeight;
            texture.pixels = *pixels;
            billboardSet.textures.push_back(std::move(texture));
        }
    }

    for (const ActorPreviewBillboard &billboard : billboardSet.billboards)
    {
        const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(billboard.spriteFrameIndex, 0);

        if (pFrame == nullptr)
        {
            ++billboardSet.missingTextureActorCount;
            continue;
        }

        if (!decodeTextures)
        {
            ++billboardSet.texturedActorCount;
        }
        else
        {
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
            const auto textureIt = std::find_if(
                billboardSet.textures.begin(),
                billboardSet.textures.end(),
                [&resolvedTexture, pFrame](const OutdoorBitmapTexture &texture)
                {
                    return texture.textureName == resolvedTexture.textureName && texture.paletteId == pFrame->paletteId;
                }
            );

            if (textureIt == billboardSet.textures.end())
            {
                ++billboardSet.missingTextureActorCount;
            }
            else
            {
                ++billboardSet.texturedActorCount;
            }
        }
    }

    return billboardSet;
}

std::optional<std::vector<uint8_t>> buildOutdoorLandMask(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData
)
{
    const std::optional<std::vector<std::string>> tileTextureNames = loadTileTextureNames(assetFileSystem, outdoorMapData);

    if (!tileTextureNames)
    {
        return std::nullopt;
    }

    std::vector<uint8_t> landMask(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1) * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1),
        0
    );

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex =
                static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const std::string &textureName = (*tileTextureNames)[rawTileId];
            const bool isWaterTile = textureName == reinterpret_cast<const char *>(WaterTileName);
            landMask[static_cast<size_t>(gridY * (OutdoorMapData::TerrainWidth - 1) + gridX)] = isWaterTile ? 0 : 1;
        }
    }

    return landMask;
}

std::optional<std::vector<uint32_t>> buildOutdoorTileColors(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData
)
{
    const std::optional<std::vector<std::string>> tileTextureNames = loadTileTextureNames(assetFileSystem, outdoorMapData);

    if (!tileTextureNames)
    {
        return std::nullopt;
    }

    std::vector<uint32_t> tileColors(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1) * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1),
        makeAbgr(96, 96, 96)
    );

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex =
                static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const std::string &textureName = (*tileTextureNames)[rawTileId];
            tileColors[static_cast<size_t>(gridY * (OutdoorMapData::TerrainWidth - 1) + gridX)] =
                colorFromTextureName(textureName);
        }
    }

    return tileColors;
}

std::optional<OutdoorTerrainTextureAtlas> buildOutdoorTerrainTextureAtlas(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache
)
{
    const std::optional<std::vector<std::string>> tileTextureNames = loadTileTextureNames(assetFileSystem, outdoorMapData);

    if (!tileTextureNames)
    {
        return std::nullopt;
    }

    OutdoorTerrainTextureAtlas textureAtlas = {};
    textureAtlas.tileSize = TerrainTextureTileSize;
    textureAtlas.width = TerrainTextureAtlasColumns * TerrainTextureTileSize;
    textureAtlas.height = TerrainTextureAtlasColumns * TerrainTextureTileSize;
    textureAtlas.pixels.resize(static_cast<size_t>(textureAtlas.width * textureAtlas.height * 4), 0);

    for (int tileIndex = 0; tileIndex < 256; ++tileIndex)
    {
        const std::string &textureName = (*tileTextureNames)[tileIndex];

        if (textureName.empty() || textureName == "pending")
        {
            continue;
        }

        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> tilePixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/bitmaps",
                textureName,
                textureWidth,
                textureHeight,
                true,
                false,
                bitmapLoadCache
            );

        if (!tilePixels || textureWidth != TerrainTextureTileSize || textureHeight != TerrainTextureTileSize)
        {
            continue;
        }

        const int atlasColumn = tileIndex % TerrainTextureAtlasColumns;
        const int atlasRow = tileIndex / TerrainTextureAtlasColumns;
        const int atlasX = atlasColumn * TerrainTextureTileSize;
        const int atlasY = atlasRow * TerrainTextureTileSize;

        for (int row = 0; row < TerrainTextureTileSize; ++row)
        {
            const size_t sourceOffset = static_cast<size_t>(row * TerrainTextureTileSize * 4);
            const size_t targetOffset = static_cast<size_t>(
                ((atlasY + row) * textureAtlas.width + atlasX) * 4
            );
            std::memcpy(
                textureAtlas.pixels.data() + static_cast<ptrdiff_t>(targetOffset),
                tilePixels->data() + static_cast<ptrdiff_t>(sourceOffset),
                static_cast<size_t>(TerrainTextureTileSize * 4)
            );
        }

        OutdoorTerrainAtlasRegion region = {};
        region.u0 = static_cast<float>(atlasX) / static_cast<float>(textureAtlas.width);
        region.v0 = static_cast<float>(atlasY) / static_cast<float>(textureAtlas.height);
        region.u1 = static_cast<float>(atlasX + TerrainTextureTileSize) / static_cast<float>(textureAtlas.width);
        region.v1 = static_cast<float>(atlasY + TerrainTextureTileSize) / static_cast<float>(textureAtlas.height);
        region.isValid = true;
        region.isWater = textureName == reinterpret_cast<const char *>(WaterTileName);
        textureAtlas.tileRegions[static_cast<size_t>(tileIndex)] = region;
    }

    return textureAtlas;
}

std::optional<OutdoorBModelTextureSet> buildOutdoorBModelTextureSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache
)
{
    std::vector<std::string> textureNames;

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.textureName.empty())
            {
                continue;
            }

            const std::string normalizedName = toLowerCopy(face.textureName);

            if (std::find(textureNames.begin(), textureNames.end(), normalizedName) == textureNames.end())
            {
                textureNames.push_back(normalizedName);
            }
        }
    }

    if (textureNames.empty())
    {
        return std::nullopt;
    }

    OutdoorBModelTextureSet textureSet = {};

    for (const std::string &textureName : textureNames)
    {
        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/bitmaps",
                textureName,
                textureWidth,
                textureHeight,
                false,
                false,
                bitmapLoadCache
            );

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureName;
        texture.width = textureWidth;
        texture.height = textureHeight;
        texture.pixels = *pixels;
        textureSet.textures.push_back(std::move(texture));
    }

    if (textureSet.textures.empty())
    {
        return std::nullopt;
    }

    return textureSet;
}

std::optional<IndoorTextureSet> buildIndoorTextureSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const IndoorMapData &indoorMapData,
    BitmapLoadCache &bitmapLoadCache
)
{
    std::vector<std::string> textureNames;

    for (const IndoorFace &face : indoorMapData.faces)
    {
        if (face.isPortal || face.textureName.empty())
        {
            continue;
        }

        const std::string normalizedName = toLowerCopy(face.textureName);

        if (std::find(textureNames.begin(), textureNames.end(), normalizedName) == textureNames.end())
        {
            textureNames.push_back(normalizedName);
        }
    }

    if (textureNames.empty())
    {
        return std::nullopt;
    }

    IndoorTextureSet textureSet = {};

    for (const std::string &textureName : textureNames)
    {
        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/bitmaps",
                textureName,
                textureWidth,
                textureHeight,
                false,
                false,
                bitmapLoadCache
            );

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureName;
        texture.width = textureWidth;
        texture.height = textureHeight;
        texture.pixels = *pixels;
        textureSet.textures.push_back(std::move(texture));
    }

    if (textureSet.textures.empty())
    {
        return std::nullopt;
    }

    return textureSet;
}
}

std::optional<MapAssetInfo> MapAssetLoader::load(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const ObjectTable &objectTable,
    MapLoadPurpose purpose
) const
{
    const auto loadStart = std::chrono::steady_clock::now();
    BitmapLoadCache bitmapLoadCache = {};
    auto logStageComplete = [&loadStart](const std::string &stageName)
    {
        const auto now = std::chrono::steady_clock::now();
        const auto elapsedMs = std::chrono::duration_cast<std::chrono::milliseconds>(now - loadStart).count();
        std::cout << "  [" << elapsedMs << " ms] " << stageName << '\n';
    };

    std::cout << "Loading map assets for " << map.fileName << "...\n";
    const std::optional<std::string> geometryPath = findAssetPath(assetFileSystem, map.fileName);

    if (!geometryPath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> geometryBytes = assetFileSystem.readBinaryFile(*geometryPath);

    if (!geometryBytes)
    {
        return std::nullopt;
    }

    logStageComplete("geometry bytes loaded");

    MapAssetInfo assetInfo = {};
    assetInfo.map = map;
    assetInfo.geometryPath = *geometryPath;
    assetInfo.geometrySize = geometryBytes->size();
    assetInfo.geometryHeader.assign(
        geometryBytes->begin(),
        geometryBytes->begin() + std::min<size_t>(geometryBytes->size(), 64)
    );

    std::optional<std::vector<uint8_t>> companionBytes;
    const std::optional<std::string> companionFileName = buildCompanionFileName(map.fileName);

    if (companionFileName)
    {
        const std::optional<std::string> companionPath = findAssetPath(assetFileSystem, *companionFileName);

        if (companionPath)
        {
            companionBytes = assetFileSystem.readBinaryFile(*companionPath);

            if (companionBytes)
            {
                assetInfo.companionPath = companionPath;
                assetInfo.companionSize = companionBytes->size();
                logStageComplete("companion bytes loaded");
            }
        }
    }

    const std::string normalizedFileName = toLowerCopy(map.fileName);

    if (normalizedFileName.ends_with(".odm"))
    {
        const OutdoorMapDataLoader outdoorMapDataLoader;
        assetInfo.outdoorMapData = outdoorMapDataLoader.loadFromBytes(*geometryBytes);
        logStageComplete("outdoor geometry parsed");

        if (assetInfo.outdoorMapData)
        {
            if (companionBytes)
            {
                const MapDeltaDataLoader mapDeltaDataLoader;
                assetInfo.outdoorMapDeltaData =
                    mapDeltaDataLoader.loadOutdoorFromBytes(*companionBytes, *assetInfo.outdoorMapData);

                if (assetInfo.outdoorMapDeltaData)
                {
                    logStageComplete("outdoor map delta parsed");
                }
            }

            if (purpose == MapLoadPurpose::Full || purpose == MapLoadPurpose::FullGameplay)
            {
                assetInfo.outdoorLandMask = buildOutdoorLandMask(assetFileSystem, *assetInfo.outdoorMapData);
                logStageComplete("outdoor land mask built");
                assetInfo.outdoorTileColors = buildOutdoorTileColors(assetFileSystem, *assetInfo.outdoorMapData);
                logStageComplete("outdoor tile colors built");
                assetInfo.outdoorTerrainTextureAtlas =
                    buildOutdoorTerrainTextureAtlas(assetFileSystem, *assetInfo.outdoorMapData, bitmapLoadCache);
                logStageComplete("outdoor terrain textures built");
                assetInfo.outdoorBModelTextureSet =
                    buildOutdoorBModelTextureSet(assetFileSystem, *assetInfo.outdoorMapData, bitmapLoadCache);
                logStageComplete("outdoor bmodel textures built");
                assetInfo.outdoorDecorationCollisionSet =
                    buildOutdoorDecorationCollisionSet(assetFileSystem, assetInfo.outdoorMapData->entities);
                logStageComplete("outdoor decoration collisions built");
                assetInfo.outdoorActorCollisionSet =
                    buildOutdoorActorCollisionSet(
                        map,
                        monsterTable,
                        assetInfo.outdoorMapDeltaData,
                        assetInfo.outdoorMapData->spawns,
                        &*assetInfo.outdoorMapData
                    );
                logStageComplete("outdoor actor collisions built");
                assetInfo.outdoorSpriteObjectCollisionSet =
                    buildOutdoorSpriteObjectCollisionSet(objectTable, assetInfo.outdoorMapDeltaData);
                logStageComplete("outdoor sprite object collisions built");
                assetInfo.outdoorDecorationBillboardSet =
                    buildOutdoorDecorationBillboardSet(assetFileSystem, *assetInfo.outdoorMapData, bitmapLoadCache);
                logStageComplete("outdoor decoration billboards built");
                assetInfo.outdoorActorPreviewBillboardSet =
                    buildActorPreviewBillboardSet(
                        assetFileSystem,
                        map,
                        monsterTable,
                        assetInfo.outdoorMapDeltaData,
                        assetInfo.outdoorMapData->spawns,
                        bitmapLoadCache,
                        &*assetInfo.outdoorMapData,
                        purpose == MapLoadPurpose::Full
                    );
                logStageComplete("outdoor actor previews built");
                assetInfo.outdoorSpriteObjectBillboardSet =
                    buildSpriteObjectBillboardSet(
                        assetFileSystem,
                        objectTable,
                        assetInfo.outdoorMapDeltaData,
                        bitmapLoadCache
                    );
                logStageComplete("outdoor sprite objects built");

                if (assetInfo.outdoorActorPreviewBillboardSet)
                {
                    const ActorPreviewBillboardSet &actorSet = *assetInfo.outdoorActorPreviewBillboardSet;
                    std::cout
                        << "  outdoor actors: total=" << actorSet.billboards.size()
                        << " map_delta=" << actorSet.mapDeltaActorCount
                        << " spawn=" << actorSet.spawnActorCount
                        << " textured=" << actorSet.texturedActorCount
                        << " missing=" << actorSet.missingTextureActorCount << '\n';
                }

                if (assetInfo.outdoorSpriteObjectBillboardSet)
                {
                    const SpriteObjectBillboardSet &objectSet = *assetInfo.outdoorSpriteObjectBillboardSet;
                    std::cout
                        << "  outdoor sprite objects: total=" << objectSet.billboards.size()
                        << " textured=" << objectSet.texturedObjectCount
                        << " missing=" << objectSet.missingTextureObjectCount << '\n';

                    for (const SpriteObjectBillboard &billboard : objectSet.billboards)
                    {
                        std::cout
                            << "    object"
                            << " name=\"" << billboard.objectName << "\""
                            << " desc=" << billboard.objectDescriptionId
                            << " sprite=" << billboard.objectSpriteId
                            << " x=" << billboard.x
                            << " y=" << billboard.y
                            << " z=" << billboard.z
                            << " h=" << billboard.height
                            << " r=" << billboard.radius
                            << " attr=0x" << std::hex << billboard.attributes << std::dec
                            << " sound=" << billboard.soundId
                            << " sector=" << billboard.sectorId
                            << " life_ticks=" << billboard.timeSinceCreatedTicks
                            << " temp=" << billboard.temporaryLifetime
                            << " glow=" << billboard.glowRadiusMultiplier
                            << " spell=" << billboard.spellId
                            << " lvl=" << billboard.spellLevel
                            << " skill=" << billboard.spellSkill
                            << " caster=" << billboard.spellCasterPid
                            << " target=" << billboard.spellTargetPid
                            << '\n';
                    }
                }
            }
            else
            {
                std::cout
                    << "  headless gameplay load: skipped outdoor render assets"
                        << '\n';
            }
        }
    }
    else if (normalizedFileName.ends_with(".blv"))
    {
        const IndoorMapDataLoader indoorMapDataLoader;
        assetInfo.indoorMapData = indoorMapDataLoader.loadFromBytes(*geometryBytes);
        logStageComplete("indoor geometry parsed");

        if (assetInfo.indoorMapData)
        {
            if (companionBytes)
            {
                const MapDeltaDataLoader mapDeltaDataLoader;
                assetInfo.indoorMapDeltaData =
                    mapDeltaDataLoader.loadIndoorFromBytes(*companionBytes, *assetInfo.indoorMapData);

                if (assetInfo.indoorMapDeltaData)
                {
                    logStageComplete("indoor map delta parsed");
                }
            }

            if (purpose == MapLoadPurpose::Full || purpose == MapLoadPurpose::FullGameplay)
            {
                assetInfo.indoorTextureSet = buildIndoorTextureSet(
                    assetFileSystem,
                    *assetInfo.indoorMapData,
                    bitmapLoadCache
                );
                logStageComplete("indoor textures built");
                assetInfo.indoorDecorationBillboardSet =
                    buildIndoorDecorationBillboardSet(assetFileSystem, *assetInfo.indoorMapData, bitmapLoadCache);
                logStageComplete("indoor decoration billboards built");
                assetInfo.indoorActorPreviewBillboardSet =
                    buildActorPreviewBillboardSet(
                        assetFileSystem,
                        map,
                        monsterTable,
                        assetInfo.indoorMapDeltaData,
                        assetInfo.indoorMapData->spawns,
                        bitmapLoadCache,
                        nullptr,
                        true
                    );
                logStageComplete("indoor actor previews built");
                assetInfo.indoorSpriteObjectBillboardSet =
                    buildSpriteObjectBillboardSet(
                        assetFileSystem,
                        objectTable,
                        assetInfo.indoorMapDeltaData,
                        bitmapLoadCache
                    );
                logStageComplete("indoor sprite objects built");

                if (assetInfo.indoorActorPreviewBillboardSet)
                {
                    const ActorPreviewBillboardSet &actorSet = *assetInfo.indoorActorPreviewBillboardSet;
                    std::cout
                        << "  indoor actors: total=" << actorSet.billboards.size()
                        << " map_delta=" << actorSet.mapDeltaActorCount
                        << " spawn=" << actorSet.spawnActorCount
                        << " textured=" << actorSet.texturedActorCount
                        << " missing=" << actorSet.missingTextureActorCount << '\n';
                }

                if (assetInfo.indoorSpriteObjectBillboardSet)
                {
                    const SpriteObjectBillboardSet &objectSet = *assetInfo.indoorSpriteObjectBillboardSet;
                    std::cout
                        << "  indoor sprite objects: total=" << objectSet.billboards.size()
                        << " textured=" << objectSet.texturedObjectCount
                        << " missing=" << objectSet.missingTextureObjectCount << '\n';

                    for (const SpriteObjectBillboard &billboard : objectSet.billboards)
                    {
                        std::cout
                            << "    object"
                            << " name=\"" << billboard.objectName << "\""
                            << " desc=" << billboard.objectDescriptionId
                            << " sprite=" << billboard.objectSpriteId
                            << " x=" << billboard.x
                            << " y=" << billboard.y
                            << " z=" << billboard.z
                            << " h=" << billboard.height
                            << " r=" << billboard.radius
                            << " attr=0x" << std::hex << billboard.attributes << std::dec
                            << " sound=" << billboard.soundId
                            << " sector=" << billboard.sectorId
                            << " life_ticks=" << billboard.timeSinceCreatedTicks
                            << " temp=" << billboard.temporaryLifetime
                            << " glow=" << billboard.glowRadiusMultiplier
                            << " spell=" << billboard.spellId
                            << " lvl=" << billboard.spellLevel
                            << " skill=" << billboard.spellSkill
                            << " caster=" << billboard.spellCasterPid
                            << " target=" << billboard.spellTargetPid
                            << '\n';
                    }
                }
            }
            else
            {
                std::cout
                    << "  headless gameplay load: skipped indoor render assets"
                        << '\n';
            }
        }
    }

    logStageComplete("map asset load complete");

    return assetInfo;
}

std::string MapAssetLoader::toLower(const std::string &value)
{
    std::string lowered = value;

    for (char &character : lowered)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return lowered;
}

std::optional<std::string> MapAssetLoader::findAssetPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &fileName
)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/games");
    const std::string normalizedFileName = toLower(fileName);

    for (const std::string &entry : entries)
    {
        if (toLower(entry) == normalizedFileName)
        {
            return std::string("Data/games/") + entry;
        }
    }

    return std::nullopt;
}

std::optional<std::string> MapAssetLoader::buildCompanionFileName(const std::string &fileName)
{
    const std::string normalized = toLower(fileName);

    if (normalized.size() < 4)
    {
        return std::nullopt;
    }

    const std::string stem = normalized.substr(0, normalized.size() - 4);
    const std::string extension = normalized.substr(normalized.size() - 4);

    if (extension == ".odm")
    {
        return stem + ".ddm";
    }

    if (extension == ".blv")
    {
        return stem + ".dlv";
    }

    return std::nullopt;
}
}
