#include "editor/viewport/EditorOutdoorViewport.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/TerrainTileData.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"

#include <imgui.h>
#include <bgfx/bgfx.h>
#include <bx/math.h>
#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <cfloat>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Editor
{
namespace
{
constexpr bgfx::ViewId EditorSceneViewId = 0;
constexpr float CameraVerticalFovDegrees = 60.0f;
constexpr float CameraNearPlane = 32.0f;
constexpr float CameraFarPlane = 131072.0f;
constexpr float CameraMouseSensitivity = 0.0035f;
constexpr float CameraMoveSpeed = 9000.0f;
constexpr float CameraFastMoveSpeedMultiplier = 4.0f;
constexpr float CameraMinPitchRadians = -1.45f;
constexpr float CameraMaxPitchRadians = 1.45f;
constexpr float CameraFocusDurationSeconds = 0.22f;
constexpr float GizmoAxisWorldLength = 1024.0f;
constexpr float GizmoCenterPickRadiusPixels = 12.0f;
constexpr float GizmoAxisPickSlackPixels = 10.0f;
constexpr float GizmoZAxisPickSlackPixels = 18.0f;
constexpr float GizmoAxisEndpointPickRadiusPixels = 14.0f;
constexpr float GizmoRotationPickSlackPixels = 12.0f;
constexpr int GizmoRotationSegments = 32;
constexpr uint16_t DecorationDescDontDraw = 0x0002;
constexpr uint16_t LevelDecorationInvisible = 0x0020;
constexpr int TerrainTextureTileSize = 128;
constexpr int TerrainTextureAtlasColumns = 16;
constexpr const char *BuiltinTerrainClayMaterialName = "Builtin/TerrainClay";
constexpr const char *BuiltinObjectGridMaterialName = "Builtin/ObjectGrid";
constexpr const char *BuiltinErrorMissingAssetMaterialName = "Builtin/ErrorMissingAsset";

struct BitmapPixelsResult
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};

struct BitmapLoadCache
{
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryEntriesByPath;
    std::unordered_map<std::string, std::optional<std::string>> bitmapPathByKey;
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> binaryFilesByPath;
    std::unordered_map<std::string, std::optional<BitmapPixelsResult>> pixelsByKey;
    std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesById;
};

struct TerrainAtlasRegion
{
    float u0 = 0.0f;
    float v0 = 0.0f;
    float u1 = 0.0f;
    float v1 = 0.0f;
    bool isValid = false;
    bool hasAssignedTexture = false;
    bool hasMissingAsset = false;
};

struct TerrainAtlasData
{
    int width = 0;
    int height = 0;
    int tileSize = 0;
    std::vector<uint8_t> pixels;
    std::array<TerrainAtlasRegion, 256> tileRegions = {};
};

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

int terrainTexturePhysicalTileSize(Engine::AssetScaleTier assetScaleTier)
{
    return TerrainTextureTileSize * Engine::assetScaleTierFactor(assetScaleTier);
}

std::optional<std::string> findBitmapPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    BitmapLoadCache &bitmapLoadCache)
{
    const std::string cacheKey = directoryPath + "|" + toLowerCopy(textureName);
    const auto cachedIt = bitmapLoadCache.bitmapPathByKey.find(cacheKey);

    if (cachedIt != bitmapLoadCache.bitmapPathByKey.end())
    {
        return cachedIt->second;
    }

    const auto directoryIt = bitmapLoadCache.directoryEntriesByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pEntries = nullptr;

    if (directoryIt != bitmapLoadCache.directoryEntriesByPath.end())
    {
        pEntries = &directoryIt->second;
    }
    else
    {
        std::vector<std::string> entries = assetFileSystem.enumerate(directoryPath);
        std::unordered_map<std::string, std::string> resolvedEntries;

        for (const std::string &entry : entries)
        {
            resolvedEntries.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pEntries = &bitmapLoadCache.directoryEntriesByPath.emplace(directoryPath, std::move(resolvedEntries)).first->second;
    }

    const std::string normalizedName = toLowerCopy(textureName) + ".bmp";
    const auto resolvedIt = pEntries->find(normalizedName);

    if (resolvedIt == pEntries->end())
    {
        bitmapLoadCache.bitmapPathByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    bitmapLoadCache.bitmapPathByKey[cacheKey] = resolvedIt->second;
    return resolvedIt->second;
}

std::optional<std::string> findDirectoryEntryPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName,
    BitmapLoadCache &bitmapLoadCache)
{
    const auto directoryIt = bitmapLoadCache.directoryEntriesByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pEntries = nullptr;

    if (directoryIt != bitmapLoadCache.directoryEntriesByPath.end())
    {
        pEntries = &directoryIt->second;
    }
    else
    {
        std::vector<std::string> entries = assetFileSystem.enumerate(directoryPath);
        std::unordered_map<std::string, std::string> resolvedEntries;

        for (const std::string &entry : entries)
        {
            resolvedEntries.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pEntries = &bitmapLoadCache.directoryEntriesByPath.emplace(directoryPath, std::move(resolvedEntries)).first->second;
    }

    const auto resolvedIt = pEntries->find(toLowerCopy(fileName));

    if (resolvedIt == pEntries->end())
    {
        return std::nullopt;
    }

    return resolvedIt->second;
}

std::optional<std::array<uint8_t, 256 * 3>> loadActPalette(
    const Engine::AssetFileSystem &assetFileSystem,
    int16_t paletteId,
    BitmapLoadCache &bitmapLoadCache)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    const auto cachedIt = bitmapLoadCache.actPalettesById.find(paletteId);

    if (cachedIt != bitmapLoadCache.actPalettesById.end())
    {
        return cachedIt->second;
    }

    char paletteFileName[32] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));
    const std::optional<std::string> palettePath =
        findDirectoryEntryPath(assetFileSystem, "Data/bitmaps", paletteFileName, bitmapLoadCache);

    if (!palettePath)
    {
        bitmapLoadCache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    std::optional<std::vector<uint8_t>> paletteBytes;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(*palettePath);

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        paletteBytes = cachedFileIt->second;
    }
    else
    {
        paletteBytes = assetFileSystem.readBinaryFile(*palettePath);
        bitmapLoadCache.binaryFilesByPath[*palettePath] = paletteBytes;
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

std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height,
    BitmapLoadCache &bitmapLoadCache)
{
    const std::string cacheKey =
        "sprite|" + toLowerCopy(textureName) + "|" + std::to_string(static_cast<int>(paletteId));
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
        findDirectoryEntryPath(assetFileSystem, "Data/sprites", textureName + ".bmp", bitmapLoadCache);

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

    SDL_Palette *pBasePalette = SDL_GetSurfacePalette(pLoadedSurface);
    const std::optional<std::array<uint8_t, 256 * 3>> overridePalette =
        loadActPalette(assetFileSystem, paletteId, bitmapLoadCache);
    const bool canApplyPalette =
        overridePalette.has_value()
        && pLoadedSurface->format == SDL_PIXELFORMAT_INDEX8
        && pBasePalette != nullptr;

    if (canApplyPalette)
    {
        width = pLoadedSurface->w;
        height = pLoadedSurface->h;
        std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);

        for (int row = 0; row < height; ++row)
        {
            const uint8_t *pSourceRow = static_cast<const uint8_t *>(pLoadedSurface->pixels)
                + static_cast<ptrdiff_t>(row * pLoadedSurface->pitch);

            for (int column = 0; column < width; ++column)
            {
                const uint8_t paletteIndex = pSourceRow[column];
                const SDL_Color sourceColor =
                    paletteIndex < pBasePalette->ncolors
                        ? pBasePalette->colors[paletteIndex]
                        : SDL_Color{0, 0, 0, 255};
                const bool isMagentaKey =
                    sourceColor.r >= 248 && sourceColor.g <= 8 && sourceColor.b >= 248;
                const bool isTealKey =
                    sourceColor.r <= 8 && sourceColor.g >= 248 && sourceColor.b >= 248;
                const size_t paletteOffset = static_cast<size_t>(paletteIndex) * 3;
                const size_t pixelOffset =
                    (static_cast<size_t>(row) * static_cast<size_t>(width) + static_cast<size_t>(column)) * 4;

                pixels[pixelOffset + 0] = (*overridePalette)[paletteOffset + 2];
                pixels[pixelOffset + 1] = (*overridePalette)[paletteOffset + 1];
                pixels[pixelOffset + 2] = (*overridePalette)[paletteOffset + 0];
                pixels[pixelOffset + 3] = (isMagentaKey || isTealKey) ? 0 : 255;
            }
        }

        SDL_DestroySurface(pLoadedSurface);
        bitmapLoadCache.pixelsByKey[cacheKey] = BitmapPixelsResult{width, height, pixels};
        return pixels;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);

    for (int row = 0; row < height; ++row)
    {
        const uint8_t *pSourceRow = static_cast<const uint8_t *>(pConvertedSurface->pixels)
            + static_cast<ptrdiff_t>(row * pConvertedSurface->pitch);
        uint8_t *pTargetRow = pixels.data() + static_cast<size_t>(row) * static_cast<size_t>(width) * 4;
        std::memcpy(pTargetRow, pSourceRow, static_cast<size_t>(width) * 4);
    }

    for (size_t pixelOffset = 0; pixelOffset < pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = pixels[pixelOffset + 0];
        const uint8_t green = pixels[pixelOffset + 1];
        const uint8_t red = pixels[pixelOffset + 2];
        const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
        const bool isTealKey = red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isTealKey)
        {
            pixels[pixelOffset + 3] = 0;
        }
    }

    SDL_DestroySurface(pConvertedSurface);
    bitmapLoadCache.pixelsByKey[cacheKey] = BitmapPixelsResult{width, height, pixels};
    return pixels;
}

std::optional<std::vector<uint8_t>> loadBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    int &width,
    int &height,
    bool forceTerrainTileSize,
    BitmapLoadCache &bitmapLoadCache)
{
    const int forcedTerrainTileSize =
        forceTerrainTileSize ? terrainTexturePhysicalTileSize(assetFileSystem.getAssetScaleTier()) : 0;
    const std::string cacheKey =
        directoryPath + "|" + toLowerCopy(textureName) + "|" + std::to_string(forcedTerrainTileSize);
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

    const std::optional<std::string> bitmapPath = findBitmapPath(assetFileSystem, directoryPath, textureName, bitmapLoadCache);

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

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;

    if (forceTerrainTileSize && (width != forcedTerrainTileSize || height != forcedTerrainTileSize))
    {
        SDL_DestroySurface(pConvertedSurface);
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    const size_t pixelCount = static_cast<size_t>(width * height * 4);
    std::vector<uint8_t> pixels(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);
    SDL_DestroySurface(pConvertedSurface);

    bitmapLoadCache.pixelsByKey[cacheKey] = BitmapPixelsResult{width, height, pixels};
    return pixels;
}

std::optional<TerrainAtlasData> buildTerrainAtlasData(
    const Engine::AssetFileSystem &assetFileSystem,
    const Game::OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache)
{
    const std::optional<std::vector<std::string>> tileTextureNames =
        Game::loadTerrainTileTextureNames(assetFileSystem, outdoorMapData);

    if (!tileTextureNames)
    {
        return std::nullopt;
    }

    const int terrainTileSize = terrainTexturePhysicalTileSize(assetFileSystem.getAssetScaleTier());
    TerrainAtlasData atlas = {};
    atlas.tileSize = terrainTileSize;
    atlas.width = TerrainTextureAtlasColumns * terrainTileSize;
    atlas.height = TerrainTextureAtlasColumns * terrainTileSize;
    atlas.pixels.resize(static_cast<size_t>(atlas.width * atlas.height * 4), 0);

    for (int tileIndex = 0; tileIndex < 256; ++tileIndex)
    {
        const std::string &textureName = (*tileTextureNames)[tileIndex];
        TerrainAtlasRegion &region = atlas.tileRegions[static_cast<size_t>(tileIndex)];

        if (textureName.empty() || textureName == "pending")
        {
            continue;
        }

        region.hasAssignedTexture = true;

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
                bitmapLoadCache);

        if (!tilePixels || textureWidth != terrainTileSize || textureHeight != terrainTileSize)
        {
            region.hasMissingAsset = true;
            continue;
        }

        const int atlasColumn = tileIndex % TerrainTextureAtlasColumns;
        const int atlasRow = tileIndex / TerrainTextureAtlasColumns;
        const int atlasX = atlasColumn * terrainTileSize;
        const int atlasY = atlasRow * terrainTileSize;

        for (int row = 0; row < terrainTileSize; ++row)
        {
            const size_t sourceOffset = static_cast<size_t>(row * terrainTileSize * 4);
            const size_t targetOffset = static_cast<size_t>(((atlasY + row) * atlas.width + atlasX) * 4);
            std::memcpy(
                atlas.pixels.data() + static_cast<ptrdiff_t>(targetOffset),
                tilePixels->data() + static_cast<ptrdiff_t>(sourceOffset),
                static_cast<size_t>(terrainTileSize * 4));
        }

        region.u0 = static_cast<float>(atlasX) / static_cast<float>(atlas.width);
        region.v0 = static_cast<float>(atlasY) / static_cast<float>(atlas.height);
        region.u1 = static_cast<float>(atlasX + terrainTileSize) / static_cast<float>(atlas.width);
        region.v1 = static_cast<float>(atlasY + terrainTileSize) / static_cast<float>(atlas.height);
        region.isValid = true;
    }

    return atlas;
}

std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName)
{
    const std::filesystem::path shaderRoot = OPENYAMM_BGFX_SHADER_DIR;

    if (rendererType == bgfx::RendererType::OpenGL)
    {
        return shaderRoot / "glsl" / (std::string(pShaderName) + ".bin");
    }

    return {};
}

std::vector<uint8_t> readBinaryFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);

    if (!file)
    {
        return {};
    }

    return std::vector<uint8_t>(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
}

bgfx::ShaderHandle loadShader(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createShader(bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size())));
}

bgfx::ProgramHandle loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadShader(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadShader(pFragmentShaderName);

    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

uint32_t makeAbgrAlpha(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

uint32_t heightColor(float normalizedHeight)
{
    const float clampedHeight = std::clamp(normalizedHeight, 0.0f, 1.0f);
    const uint8_t red = static_cast<uint8_t>(std::lround(56.0f + clampedHeight * 92.0f));
    const uint8_t green = static_cast<uint8_t>(std::lround(82.0f + clampedHeight * 110.0f));
    const uint8_t blue = static_cast<uint8_t>(std::lround(44.0f + clampedHeight * 56.0f));
    return makeAbgr(red, green, blue);
}

float squaredLength2(float x, float y)
{
    return x * x + y * y;
}

EditorBModelSourceTransform sourceTransformFromBModel(const Game::OutdoorBModel &bmodel)
{
    EditorBModelSourceTransform transform = {};

    if (bmodel.vertices.empty())
    {
        transform.originX = static_cast<float>(bmodel.boundingCenterX);
        transform.originY = static_cast<float>(bmodel.boundingCenterY);
        transform.originZ = static_cast<float>(bmodel.boundingCenterZ);
        return transform;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    transform.originX = (minX + maxX) * 0.5f;
    transform.originY = (minY + maxY) * 0.5f;
    transform.originZ = (minZ + maxZ) * 0.5f;
    return transform;
}

std::array<float, 3> rotateBasisVectorAroundAxis(
    const std::array<float, 3> &vector,
    const bx::Vec3 &axis,
    float angleRadians)
{
    const float axisLength = std::sqrt(axis.x * axis.x + axis.y * axis.y + axis.z * axis.z);

    if (axisLength <= 0.0001f)
    {
        return vector;
    }

    const bx::Vec3 normalizedAxis = {axis.x / axisLength, axis.y / axisLength, axis.z / axisLength};
    const float cosAngle = std::cos(angleRadians);
    const float sinAngle = std::sin(angleRadians);
    const float dotProduct =
        vector[0] * normalizedAxis.x
        + vector[1] * normalizedAxis.y
        + vector[2] * normalizedAxis.z;
    const bx::Vec3 crossProduct = {
        normalizedAxis.y * vector[2] - normalizedAxis.z * vector[1],
        normalizedAxis.z * vector[0] - normalizedAxis.x * vector[2],
        normalizedAxis.x * vector[1] - normalizedAxis.y * vector[0]
    };

    return {
        vector[0] * cosAngle + crossProduct.x * sinAngle + normalizedAxis.x * dotProduct * (1.0f - cosAngle),
        vector[1] * cosAngle + crossProduct.y * sinAngle + normalizedAxis.y * dotProduct * (1.0f - cosAngle),
        vector[2] * cosAngle + crossProduct.z * sinAngle + normalizedAxis.z * dotProduct * (1.0f - cosAngle)
    };
}

bx::Vec3 vecAdd(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

bx::Vec3 vecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

bx::Vec3 vecScale(const bx::Vec3 &value, float scale)
{
    return {value.x * scale, value.y * scale, value.z * scale};
}

float vecDot(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

bx::Vec3 vecCross(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
}

float vecLength(const bx::Vec3 &value)
{
    return std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
}

bx::Vec3 vecNormalize(const bx::Vec3 &value)
{
    const float length = vecLength(value);

    if (length <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {value.x / length, value.y / length, value.z / length};
}

bx::Vec3 vecLerp(const bx::Vec3 &start, const bx::Vec3 &end, float t)
{
    return {
        start.x + (end.x - start.x) * t,
        start.y + (end.y - start.y) * t,
        start.z + (end.z - start.z) * t
    };
}

float lerpFloat(float start, float end, float t)
{
    return start + (end - start) * t;
}

float easeOutCubic(float t)
{
    const float inverse = 1.0f - t;
    return 1.0f - inverse * inverse * inverse;
}

void recalculateOutdoorTileUsage(Game::OutdoorMapData &outdoorMapData)
{
    std::array<bool, 256> seenTiles = {};
    outdoorMapData.uniqueTileCount = 0;

    for (uint8_t tileId : outdoorMapData.tileMap)
    {
        if (!seenTiles[tileId])
        {
            seenTiles[tileId] = true;
            ++outdoorMapData.uniqueTileCount;
        }
    }
}

void recalculateOutdoorHeightRange(Game::OutdoorMapData &outdoorMapData)
{
    if (outdoorMapData.heightMap.empty())
    {
        outdoorMapData.minHeightSample = 0;
        outdoorMapData.maxHeightSample = 0;
        return;
    }

    const auto [minIt, maxIt] = std::minmax_element(outdoorMapData.heightMap.begin(), outdoorMapData.heightMap.end());
    outdoorMapData.minHeightSample = *minIt;
    outdoorMapData.maxHeightSample = *maxIt;
}

uint32_t terrainNoiseHash(int x, int y)
{
    uint32_t value = static_cast<uint32_t>(x) * 0x9e3779b9u;
    value ^= static_cast<uint32_t>(y) * 0x85ebca6bu;
    value ^= value >> 16;
    value *= 0x7feb352du;
    value ^= value >> 15;
    value *= 0x846ca68bu;
    value ^= value >> 16;
    return value;
}

float wrapAngleRadians(float angle)
{
    while (angle > bx::kPi)
    {
        angle -= bx::kPi2;
    }

    while (angle < -bx::kPi)
    {
        angle += bx::kPi2;
    }

    return angle;
}

float shortestAngleDelta(float from, float to)
{
    return wrapAngleRadians(to - from);
}

float bmodelRotationHandleRadius(const Game::OutdoorBModel &bmodel)
{
    const float rawRadius = std::max(static_cast<float>(bmodel.boundingRadius) * 1.15f, 768.0f);
    return std::clamp(rawRadius, 768.0f, 4096.0f);
}

void recomputeBModelBounds(Game::OutdoorBModel &bmodel)
{
    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    if (!std::isfinite(minX) || !std::isfinite(maxX))
    {
        return;
    }

    const float centerX = (minX + maxX) * 0.5f;
    const float centerY = (minY + maxY) * 0.5f;
    const float centerZ = (minZ + maxZ) * 0.5f;
    float maxRadiusSquared = 0.0f;

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float deltaX = static_cast<float>(vertex.x) - centerX;
        const float deltaY = static_cast<float>(vertex.y) - centerY;
        const float deltaZ = static_cast<float>(vertex.z) - centerZ;
        maxRadiusSquared = std::max(maxRadiusSquared, deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    }

    bmodel.minX = static_cast<int>(std::floor(minX));
    bmodel.minY = static_cast<int>(std::floor(minY));
    bmodel.minZ = static_cast<int>(std::floor(minZ));
    bmodel.maxX = static_cast<int>(std::ceil(maxX));
    bmodel.maxY = static_cast<int>(std::ceil(maxY));
    bmodel.maxZ = static_cast<int>(std::ceil(maxZ));
    bmodel.boundingCenterX = static_cast<int>(std::lround(centerX));
    bmodel.boundingCenterY = static_cast<int>(std::lround(centerY));
    bmodel.boundingCenterZ = static_cast<int>(std::lround(centerZ));
    bmodel.boundingRadius = static_cast<int>(std::ceil(std::sqrt(maxRadiusSquared)));
}

bool applyBModelYawRotation(
    Game::OutdoorBModel &bmodel,
    const std::vector<Game::OutdoorBModelVertex> &sourceVertices,
    float yawRadians)
{
    if (sourceVertices.empty() || sourceVertices.size() != bmodel.vertices.size())
    {
        return false;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : sourceVertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
    }

    if (!std::isfinite(minX) || !std::isfinite(maxX))
    {
        return false;
    }

    const float pivotX = (minX + maxX) * 0.5f;
    const float pivotY = (minY + maxY) * 0.5f;
    const float cosYaw = std::cos(yawRadians);
    const float sinYaw = std::sin(yawRadians);
    bool changed = false;

    for (size_t index = 0; index < sourceVertices.size(); ++index)
    {
        const Game::OutdoorBModelVertex &sourceVertex = sourceVertices[index];
        const float localX = static_cast<float>(sourceVertex.x) - pivotX;
        const float localY = static_cast<float>(sourceVertex.y) - pivotY;
        const float rotatedX = localX * cosYaw - localY * sinYaw;
        const float rotatedY = localX * sinYaw + localY * cosYaw;
        const int newX = static_cast<int>(std::lround(pivotX + rotatedX));
        const int newY = static_cast<int>(std::lround(pivotY + rotatedY));

        if (bmodel.vertices[index].x != newX || bmodel.vertices[index].y != newY)
        {
            changed = true;
        }

        bmodel.vertices[index].x = newX;
        bmodel.vertices[index].y = newY;
        bmodel.vertices[index].z = sourceVertex.z;
    }

    if (changed)
    {
        recomputeBModelBounds(bmodel);
    }

    return changed;
}

Game::OutdoorBModelVertex transformImportedPreviewVertex(
    const EditorBModelSourceTransform &transform,
    float localX,
    float localY,
    float localZ)
{
    Game::OutdoorBModelVertex vertex = {};
    const float worldX =
        transform.originX
        + localX * transform.basisX[0]
        + localY * transform.basisY[0]
        + localZ * transform.basisZ[0];
    const float worldY =
        transform.originY
        + localX * transform.basisX[1]
        + localY * transform.basisY[1]
        + localZ * transform.basisZ[1];
    const float worldZ =
        transform.originZ
        + localX * transform.basisX[2]
        + localY * transform.basisY[2]
        + localZ * transform.basisZ[2];
    vertex.x = static_cast<int>(std::lround(worldX));
    vertex.y = static_cast<int>(std::lround(worldY));
    vertex.z = static_cast<int>(std::lround(worldZ));
    return vertex;
}

uint8_t classifyImportedPreviewPolygonType(const ImportedModel &importedModel, const ImportedModelFace &face)
{
    if (face.vertices.size() < 3)
    {
        return 0;
    }

    const ImportedModelPosition &a = importedModel.positions[face.vertices[0].positionIndex];
    const ImportedModelPosition &b = importedModel.positions[face.vertices[1].positionIndex];
    const ImportedModelPosition &c = importedModel.positions[face.vertices[2].positionIndex];
    const float abX = b.x - a.x;
    const float abY = b.y - a.y;
    const float abZ = b.z - a.z;
    const float acX = c.x - a.x;
    const float acY = c.y - a.y;
    const float acZ = c.z - a.z;
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    const float normalLength = std::sqrt(normalX * normalX + normalY * normalY + normalZ * normalZ);

    if (normalLength <= 0.0001f)
    {
        return 0;
    }

    const float normalZNormalized = std::fabs(normalZ / normalLength);

    if (normalZNormalized >= 0.85f)
    {
        return 0x3;
    }

    if (normalZNormalized >= 0.45f)
    {
        return 0x4;
    }

    return 0;
}

float previewFaceNormalZ(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return 0.0f;
    }

    const Game::OutdoorBModelVertex &a = vertices[face.vertexIndices[0]];
    const Game::OutdoorBModelVertex &b = vertices[face.vertexIndices[1]];
    const Game::OutdoorBModelVertex &c = vertices[face.vertexIndices[2]];
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    return abX * acY - abY * acX;
}

float previewFaceOutwardDot(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return 0.0f;
    }

    const Game::OutdoorBModelVertex &a = vertices[face.vertexIndices[0]];
    const Game::OutdoorBModelVertex &b = vertices[face.vertexIndices[1]];
    const Game::OutdoorBModelVertex &c = vertices[face.vertexIndices[2]];
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    float faceCenterX = 0.0f;
    float faceCenterY = 0.0f;
    float faceCenterZ = 0.0f;

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        faceCenterX += static_cast<float>(vertices[vertexIndex].x);
        faceCenterY += static_cast<float>(vertices[vertexIndex].y);
        faceCenterZ += static_cast<float>(vertices[vertexIndex].z);
    }

    const float invVertexCount = 1.0f / static_cast<float>(face.vertexIndices.size());
    faceCenterX *= invVertexCount;
    faceCenterY *= invVertexCount;
    faceCenterZ *= invVertexCount;
    return normalX * (faceCenterX - modelCenterX)
        + normalY * (faceCenterY - modelCenterY)
        + normalZ * (faceCenterZ - modelCenterZ);
}

void reversePreviewFaceWinding(Game::OutdoorBModelFace &face)
{
    std::reverse(face.vertexIndices.begin(), face.vertexIndices.end());
}

void orientImportedPreviewFaceWinding(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    const bool shouldReverse =
        (face.polygonType == 0x3 || face.polygonType == 0x4)
        ? (previewFaceNormalZ(vertices, face) < 0.0f)
        : (previewFaceOutwardDot(vertices, face, modelCenterX, modelCenterY, modelCenterZ) < 0.0f);

    if (shouldReverse)
    {
        reversePreviewFaceWinding(face);
    }
}

std::optional<Game::OutdoorBModel> buildImportedPreviewBModel(
    const ImportedModel &importedModel,
    float importScale,
    const Game::OutdoorBModel *pPlacementTemplate,
    const EditorBModelSourceTransform *pSourceTransform,
    const bx::Vec3 *pFloorPoint)
{
    if (importScale <= 0.0f || importedModel.positions.empty() || importedModel.faces.empty())
    {
        return std::nullopt;
    }

    Game::OutdoorBModel bmodel = {};
    std::vector<Game::OutdoorBModelVertex> importedVertices;
    importedVertices.reserve(importedModel.positions.size());
    float importedMinX = std::numeric_limits<float>::max();
    float importedMinY = std::numeric_limits<float>::max();
    float importedMinZ = std::numeric_limits<float>::max();
    float importedMaxX = std::numeric_limits<float>::lowest();
    float importedMaxY = std::numeric_limits<float>::lowest();
    float importedMaxZ = std::numeric_limits<float>::lowest();

    for (const ImportedModelPosition &position : importedModel.positions)
    {
        Game::OutdoorBModelVertex vertex = {};
        vertex.x = static_cast<int>(std::lround(position.x * importScale));
        vertex.y = static_cast<int>(std::lround(position.y * importScale));
        vertex.z = static_cast<int>(std::lround(position.z * importScale));
        importedVertices.push_back(vertex);
        importedMinX = std::min(importedMinX, static_cast<float>(vertex.x));
        importedMinY = std::min(importedMinY, static_cast<float>(vertex.y));
        importedMinZ = std::min(importedMinZ, static_cast<float>(vertex.z));
        importedMaxX = std::max(importedMaxX, static_cast<float>(vertex.x));
        importedMaxY = std::max(importedMaxY, static_cast<float>(vertex.y));
        importedMaxZ = std::max(importedMaxZ, static_cast<float>(vertex.z));
    }

    const float importedCenterX = (importedMinX + importedMaxX) * 0.5f;
    const float importedCenterY = (importedMinY + importedMaxY) * 0.5f;
    const float importedCenterZ = (importedMinZ + importedMaxZ) * 0.5f;
    EditorBModelSourceTransform sourceTransform = {};
    sourceTransform.originX = importedCenterX;
    sourceTransform.originY = importedCenterY;
    sourceTransform.originZ = importedCenterZ;

    if (pSourceTransform != nullptr)
    {
        sourceTransform = *pSourceTransform;
    }
    else if (pPlacementTemplate != nullptr)
    {
        sourceTransform = sourceTransformFromBModel(*pPlacementTemplate);

        if (!pPlacementTemplate->vertices.empty())
        {
            float templateMinZ = std::numeric_limits<float>::max();

            for (const Game::OutdoorBModelVertex &vertex : pPlacementTemplate->vertices)
            {
                templateMinZ = std::min(templateMinZ, static_cast<float>(vertex.z));
            }

            sourceTransform.originZ = templateMinZ + (importedCenterZ - importedMinZ);
        }
    }
    else if (pFloorPoint != nullptr)
    {
        sourceTransform.originX = pFloorPoint->x;
        sourceTransform.originY = pFloorPoint->y;
        sourceTransform.originZ = pFloorPoint->z + (importedCenterZ - importedMinZ);
    }

    for (Game::OutdoorBModelVertex &vertex : importedVertices)
    {
        const float localX = static_cast<float>(vertex.x) - importedCenterX;
        const float localY = static_cast<float>(vertex.y) - importedCenterY;
        const float localZ = static_cast<float>(vertex.z) - importedCenterZ;
        vertex = transformImportedPreviewVertex(sourceTransform, localX, localY, localZ);
    }

    bmodel.vertices = std::move(importedVertices);

    for (const ImportedModelFace &importedFace : importedModel.faces)
    {
        Game::OutdoorBModelFace face = {};
        face.polygonType = classifyImportedPreviewPolygonType(importedModel, importedFace);

        for (const ImportedModelFaceVertex &importedVertex : importedFace.vertices)
        {
            face.vertexIndices.push_back(static_cast<uint16_t>(importedVertex.positionIndex));
        }

        orientImportedPreviewFaceWinding(
            bmodel.vertices,
            face,
            sourceTransform.originX,
            sourceTransform.originY,
            sourceTransform.originZ);
        bmodel.faces.push_back(std::move(face));
    }

    recomputeBModelBounds(bmodel);
    return bmodel;
}

bool applyBModelAxisRotation(
    Game::OutdoorBModel &bmodel,
    const std::vector<Game::OutdoorBModelVertex> &sourceVertices,
    const bx::Vec3 &pivot,
    const bx::Vec3 &axis,
    float angleRadians)
{
    if (sourceVertices.empty() || sourceVertices.size() != bmodel.vertices.size())
    {
        return false;
    }

    const bx::Vec3 normalizedAxis = vecNormalize(axis);

    if (vecLength(normalizedAxis) <= 0.0001f)
    {
        return false;
    }

    const float cosAngle = std::cos(angleRadians);
    const float sinAngle = std::sin(angleRadians);
    bool changed = false;

    for (size_t index = 0; index < sourceVertices.size(); ++index)
    {
        const Game::OutdoorBModelVertex &sourceVertex = sourceVertices[index];
        const bx::Vec3 local = {
            static_cast<float>(sourceVertex.x) - pivot.x,
            static_cast<float>(sourceVertex.y) - pivot.y,
            static_cast<float>(sourceVertex.z) - pivot.z
        };
        const bx::Vec3 axisCrossLocal = vecCross(normalizedAxis, local);
        const float axisDotLocal = vecDot(normalizedAxis, local);
        const bx::Vec3 rotated = {
            local.x * cosAngle + axisCrossLocal.x * sinAngle + normalizedAxis.x * axisDotLocal * (1.0f - cosAngle),
            local.y * cosAngle + axisCrossLocal.y * sinAngle + normalizedAxis.y * axisDotLocal * (1.0f - cosAngle),
            local.z * cosAngle + axisCrossLocal.z * sinAngle + normalizedAxis.z * axisDotLocal * (1.0f - cosAngle)
        };
        const int newX = static_cast<int>(std::lround(pivot.x + rotated.x));
        const int newY = static_cast<int>(std::lround(pivot.y + rotated.y));
        const int newZ = static_cast<int>(std::lround(pivot.z + rotated.z));

        if (bmodel.vertices[index].x != newX || bmodel.vertices[index].y != newY || bmodel.vertices[index].z != newZ)
        {
            changed = true;
        }

        bmodel.vertices[index].x = newX;
        bmodel.vertices[index].y = newY;
        bmodel.vertices[index].z = newZ;
    }

    if (changed)
    {
        recomputeBModelBounds(bmodel);
    }

    return changed;
}

bool intersectRayPlane(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const bx::Vec3 &planePoint,
    const bx::Vec3 &planeNormal,
    bx::Vec3 &intersection)
{
    const float denominator = vecDot(rayDirection, planeNormal);

    if (std::fabs(denominator) <= 0.0001f)
    {
        return false;
    }

    const bx::Vec3 planeOffset = {
        planePoint.x - rayOrigin.x,
        planePoint.y - rayOrigin.y,
        planePoint.z - rayOrigin.z
    };
    const float distance = vecDot(planeOffset, planeNormal) / denominator;

    if (distance < 0.0f)
    {
        return false;
    }

    intersection = {
        rayOrigin.x + rayDirection.x * distance,
        rayOrigin.y + rayDirection.y * distance,
        rayOrigin.z + rayDirection.z * distance
    };
    return true;
}

float signedAngleAroundAxis(const bx::Vec3 &startVector, const bx::Vec3 &endVector, const bx::Vec3 &axis)
{
    const bx::Vec3 normalizedStart = vecNormalize(startVector);
    const bx::Vec3 normalizedEnd = vecNormalize(endVector);
    const bx::Vec3 normalizedAxis = vecNormalize(axis);
    const bx::Vec3 crossProduct = vecCross(normalizedStart, normalizedEnd);
    const float sine = vecDot(normalizedAxis, crossProduct);
    const float cosine = std::clamp(vecDot(normalizedStart, normalizedEnd), -1.0f, 1.0f);
    return std::atan2(sine, cosine);
}

std::optional<bx::Vec3> bmodelPlacementCenterForFloorPoint(
    const Game::OutdoorMapData &outdoorMapData,
    size_t bmodelIndex,
    const bx::Vec3 &floorPoint)
{
    if (bmodelIndex >= outdoorMapData.bmodels.size())
    {
        return std::nullopt;
    }

    const Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];
    float minZ = std::numeric_limits<float>::max();
    float centerX = 0.0f;
    float centerY = 0.0f;
    float centerZ = 0.0f;
    int vertexCount = 0;

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        centerX += static_cast<float>(vertex.x);
        centerY += static_cast<float>(vertex.y);
        centerZ += static_cast<float>(vertex.z);
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        ++vertexCount;
    }

    if (vertexCount == 0 || !std::isfinite(minZ))
    {
        return std::nullopt;
    }

    const float scale = 1.0f / static_cast<float>(vertexCount);
    centerX *= scale;
    centerY *= scale;
    centerZ *= scale;
    const float terrainZ = Game::sampleOutdoorTerrainHeight(outdoorMapData, floorPoint.x, floorPoint.y);
    const float baseOffsetZ = centerZ - minZ;
    return bx::Vec3{floorPoint.x, floorPoint.y, terrainZ + baseOffsetZ};
}

const char *placementKindLabel(EditorSelectionKind kind)
{
    switch (kind)
    {
    case EditorSelectionKind::Terrain:
        return "Terrain";

    case EditorSelectionKind::BModel:
        return "BModel";

    case EditorSelectionKind::InteractiveFace:
        return "Face";

    case EditorSelectionKind::Entity:
        return "Entity";

    case EditorSelectionKind::Spawn:
        return "Spawn";

    case EditorSelectionKind::Actor:
        return "Actor";

    case EditorSelectionKind::SpriteObject:
        return "Sprite Object";

    default:
        return "Select";
    }
}

size_t flattenTerrainCellIndex(int cellX, int cellY)
{
    return static_cast<size_t>(cellY) * Game::OutdoorMapData::TerrainWidth + static_cast<size_t>(cellX);
}

bx::Vec3 applySymmetricMatrix(
    const std::array<float, 6> &covariance,
    const bx::Vec3 &vector)
{
    const float xx = covariance[0];
    const float xy = covariance[1];
    const float xz = covariance[2];
    const float yy = covariance[3];
    const float yz = covariance[4];
    const float zz = covariance[5];
    return {
        xx * vector.x + xy * vector.y + xz * vector.z,
        xy * vector.x + yy * vector.y + yz * vector.z,
        xz * vector.x + yz * vector.y + zz * vector.z};
}

bx::Vec3 powerIterationAxis(
    const std::array<float, 6> &covariance,
    bx::Vec3 vector,
    const std::optional<bx::Vec3> &orthogonalTo)
{
    for (int iteration = 0; iteration < 10; ++iteration)
    {
        vector = applySymmetricMatrix(covariance, vector);

        if (orthogonalTo)
        {
            vector = vecSubtract(vector, vecScale(*orthogonalTo, vecDot(vector, *orthogonalTo)));
        }

        if (vecLength(vector) <= 0.0001f)
        {
            break;
        }

        vector = vecNormalize(vector);
    }

    if (vecLength(vector) <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return vecNormalize(vector);
}

void computeBModelLocalBasis(
    const Game::OutdoorBModel &bmodel,
    bx::Vec3 &xAxis,
    bx::Vec3 &yAxis,
    bx::Vec3 &zAxis)
{
    if (bmodel.vertices.size() < 3)
    {
        xAxis = {1.0f, 0.0f, 0.0f};
        yAxis = {0.0f, 1.0f, 0.0f};
        zAxis = {0.0f, 0.0f, 1.0f};
        return;
    }

    bx::Vec3 center = {0.0f, 0.0f, 0.0f};

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        center.x += static_cast<float>(vertex.x);
        center.y += static_cast<float>(vertex.y);
        center.z += static_cast<float>(vertex.z);
    }

    const float invCount = 1.0f / static_cast<float>(bmodel.vertices.size());
    center.x *= invCount;
    center.y *= invCount;
    center.z *= invCount;

    std::array<float, 6> covariance = {};

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float x = static_cast<float>(vertex.x) - center.x;
        const float y = static_cast<float>(vertex.y) - center.y;
        const float z = static_cast<float>(vertex.z) - center.z;
        covariance[0] += x * x;
        covariance[1] += x * y;
        covariance[2] += x * z;
        covariance[3] += y * y;
        covariance[4] += y * z;
        covariance[5] += z * z;
    }

    xAxis = powerIterationAxis(covariance, {1.0f, 0.37f, 0.21f}, std::nullopt);

    if (vecLength(xAxis) <= 0.0001f)
    {
        xAxis = {1.0f, 0.0f, 0.0f};
    }

    yAxis = powerIterationAxis(covariance, {0.19f, 1.0f, 0.41f}, xAxis);

    if (vecLength(yAxis) <= 0.0001f)
    {
        yAxis = std::fabs(xAxis.z) > 0.8f ? bx::Vec3{1.0f, 0.0f, 0.0f} : bx::Vec3{0.0f, 0.0f, 1.0f};
        yAxis = vecNormalize(vecSubtract(yAxis, vecScale(xAxis, vecDot(yAxis, xAxis))));
    }

    zAxis = vecNormalize(vecCross(xAxis, yAxis));

    if (vecLength(zAxis) <= 0.0001f)
    {
        zAxis = {0.0f, 0.0f, 1.0f};
    }

    yAxis = vecNormalize(vecCross(zAxis, xAxis));

    if (vecDot(zAxis, bx::Vec3{0.0f, 0.0f, 1.0f}) < 0.0f)
    {
        zAxis = vecScale(zAxis, -1.0f);
        yAxis = vecScale(yAxis, -1.0f);
    }
}

void computeTransformBasis(
    const EditorDocument &document,
    const EditorSelection &selection,
    EditorOutdoorViewport::TransformSpaceMode spaceMode,
    bx::Vec3 &xAxis,
    bx::Vec3 &yAxis,
    bx::Vec3 &zAxis)
{
    xAxis = {1.0f, 0.0f, 0.0f};
    yAxis = {0.0f, 1.0f, 0.0f};
    zAxis = {0.0f, 0.0f, 1.0f};

    if (spaceMode != EditorOutdoorViewport::TransformSpaceMode::Local
        || selection.kind != EditorSelectionKind::BModel
        || selection.index >= document.outdoorGeometry().bmodels.size())
    {
        return;
    }

    computeBModelLocalBasis(document.outdoorGeometry().bmodels[selection.index], xAxis, yAxis, zAxis);
}

template<class Callback>
void rasterizeTerrainLine(int startX, int startY, int endX, int endY, Callback callback)
{
    int currentX = startX;
    int currentY = startY;
    const int deltaX = std::abs(endX - startX);
    const int deltaY = std::abs(endY - startY);
    const int stepX = startX < endX ? 1 : -1;
    const int stepY = startY < endY ? 1 : -1;
    int error = deltaX - deltaY;

    while (true)
    {
        callback(currentX, currentY);

        if (currentX == endX && currentY == endY)
        {
            break;
        }

        const int doubleError = error * 2;

        if (doubleError > -deltaY)
        {
            error -= deltaY;
            currentX += stepX;
        }

        if (doubleError < deltaX)
        {
            error += deltaX;
            currentY += stepY;
        }
    }
}

template<class Callback>
void forEachTerrainBrushCell(int centerX, int centerY, int radius, Callback callback)
{
    const int effectiveRadius = std::max(radius, 0);

    for (int offsetY = -effectiveRadius; offsetY <= effectiveRadius; ++offsetY)
    {
        for (int offsetX = -effectiveRadius; offsetX <= effectiveRadius; ++offsetX)
        {
            const int targetX = centerX + offsetX;
            const int targetY = centerY + offsetY;

            if (targetX < 0
                || targetY < 0
                || targetX >= Game::OutdoorMapData::TerrainWidth
                || targetY >= Game::OutdoorMapData::TerrainHeight)
            {
                continue;
            }

            const float distance = std::sqrt(static_cast<float>(offsetX * offsetX + offsetY * offsetY));

            if (distance > static_cast<float>(effectiveRadius))
            {
                continue;
            }

            callback(targetX, targetY, distance, effectiveRadius);
        }
    }
}

float terrainFalloffWeight(float distance, int radius, EditorTerrainFalloffMode mode)
{
    if (radius <= 0)
    {
        return 1.0f;
    }

    const float normalized = std::clamp(distance / static_cast<float>(radius + 1), 0.0f, 1.0f);

    switch (mode)
    {
    case EditorTerrainFalloffMode::Flat:
        return 1.0f;

    case EditorTerrainFalloffMode::Smooth:
    {
        const float inverse = 1.0f - normalized;
        return inverse * inverse;
    }

    case EditorTerrainFalloffMode::Linear:
    default:
        return 1.0f - normalized;
    }
}

bool applyTerrainPaintBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    uint8_t tileId,
    int edgeNoise)
{
    bool mutated = false;
    const int clampedEdgeNoise = std::clamp(edgeNoise, 0, 100);
    const float edgeNoiseStrength = static_cast<float>(clampedEdgeNoise) / 100.0f;
    const float effectiveRadius = static_cast<float>(std::max(radius, 0));
    const float edgeBandWidth = effectiveRadius > 1.0f ? std::max(1.0f, effectiveRadius * 0.4f) : 0.0f;
    const float solidRadius = std::max(0.0f, effectiveRadius - edgeBandWidth);

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.tileMap.size())
            {
                return;
            }

            if (clampedEdgeNoise > 0 && effectiveRadius > 1.0f && distance > solidRadius)
            {
                const float normalizedEdge = std::clamp((distance - solidRadius) / edgeBandWidth, 0.0f, 1.0f);
                const uint32_t hash = terrainNoiseHash(targetX, targetY);
                const float noise = static_cast<float>(hash & 0xffffu) / 65535.0f;
                const float jitter = (noise * 2.0f - 1.0f) * edgeNoiseStrength * 0.35f;
                const float coverage = 1.0f - normalizedEdge;

                if (coverage + jitter < 0.5f)
                {
                    return;
                }
            }

            if (outdoorGeometry.tileMap[sampleIndex] == tileId)
            {
                return;
            }

            outdoorGeometry.tileMap[sampleIndex] = tileId;
            mutated = true;
        });

    if (mutated)
    {
        recalculateOutdoorTileUsage(outdoorGeometry);
    }

    return mutated;
}

bool applyTerrainPaintRectangle(
    Game::OutdoorMapData &outdoorGeometry,
    int startX,
    int startY,
    int endX,
    int endY,
    uint8_t tileId)
{
    const int minX = std::clamp(std::min(startX, endX), 0, Game::OutdoorMapData::TerrainWidth - 1);
    const int maxX = std::clamp(std::max(startX, endX), 0, Game::OutdoorMapData::TerrainWidth - 1);
    const int minY = std::clamp(std::min(startY, endY), 0, Game::OutdoorMapData::TerrainHeight - 1);
    const int maxY = std::clamp(std::max(startY, endY), 0, Game::OutdoorMapData::TerrainHeight - 1);
    bool mutated = false;

    for (int y = minY; y <= maxY; ++y)
    {
        for (int x = minX; x <= maxX; ++x)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(x, y);

            if (sampleIndex >= outdoorGeometry.tileMap.size() || outdoorGeometry.tileMap[sampleIndex] == tileId)
            {
                continue;
            }

            outdoorGeometry.tileMap[sampleIndex] = tileId;
            mutated = true;
        }
    }

    if (mutated)
    {
        recalculateOutdoorTileUsage(outdoorGeometry);
    }

    return mutated;
}

bool applyTerrainPaintFill(Game::OutdoorMapData &outdoorGeometry, int startX, int startY, uint8_t tileId)
{
    if (startX < 0
        || startY < 0
        || startX >= Game::OutdoorMapData::TerrainWidth
        || startY >= Game::OutdoorMapData::TerrainHeight)
    {
        return false;
    }

    const size_t startIndex = flattenTerrainCellIndex(startX, startY);

    if (startIndex >= outdoorGeometry.tileMap.size())
    {
        return false;
    }

    const uint8_t sourceTileId = outdoorGeometry.tileMap[startIndex];

    if (sourceTileId == tileId)
    {
        return false;
    }

    std::vector<std::pair<int, int>> stack;
    stack.push_back({startX, startY});

    while (!stack.empty())
    {
        const std::pair<int, int> current = stack.back();
        stack.pop_back();
        const int x = current.first;
        const int y = current.second;

        if (x < 0
            || y < 0
            || x >= Game::OutdoorMapData::TerrainWidth
            || y >= Game::OutdoorMapData::TerrainHeight)
        {
            continue;
        }

        const size_t sampleIndex = flattenTerrainCellIndex(x, y);

        if (sampleIndex >= outdoorGeometry.tileMap.size() || outdoorGeometry.tileMap[sampleIndex] != sourceTileId)
        {
            continue;
        }

        outdoorGeometry.tileMap[sampleIndex] = tileId;
        stack.push_back({x - 1, y});
        stack.push_back({x + 1, y});
        stack.push_back({x, y - 1});
        stack.push_back({x, y + 1});
    }

    recalculateOutdoorTileUsage(outdoorGeometry);
    return true;
}

bool applyTerrainSculptBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    int signedStrength,
    EditorTerrainFalloffMode falloffMode)
{
    bool mutated = false;

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int effectiveRadius)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                return;
            }

            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            int delta = static_cast<int>(std::round(static_cast<float>(signedStrength) * falloff));

            if (delta == 0)
            {
                delta = signedStrength > 0 ? 1 : -1;
            }

            const int currentHeight = outdoorGeometry.heightMap[sampleIndex];
            const int nextHeight = std::clamp(currentHeight + delta, 0, 255);

            if (nextHeight == currentHeight)
            {
                return;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        });

    return mutated;
}

bool applyTerrainFlattenBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    int strength,
    int targetHeight,
    EditorTerrainFalloffMode falloffMode)
{
    bool mutated = false;

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int effectiveRadius)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                return;
            }

            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            int maxDelta = static_cast<int>(std::round(static_cast<float>(strength) * falloff));

            if (maxDelta <= 0)
            {
                maxDelta = 1;
            }

            const int currentHeight = outdoorGeometry.heightMap[sampleIndex];
            const int deltaToTarget = targetHeight - currentHeight;

            if (deltaToTarget == 0)
            {
                return;
            }

            const int delta = std::clamp(deltaToTarget, -maxDelta, maxDelta);
            const int nextHeight = std::clamp(currentHeight + delta, 0, 255);

            if (nextHeight == currentHeight)
            {
                return;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        });

    return mutated;
}

bool applyTerrainSmoothBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    int strength,
    EditorTerrainFalloffMode falloffMode)
{
    const std::vector<uint8_t> sourceHeights = outdoorGeometry.heightMap;
    bool mutated = false;
    const int kernelRadius = radius >= 6 ? 2 : 1;

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int effectiveRadius)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                return;
            }

            int totalHeight = 0;
            int sampleCount = 0;

            for (int offsetY = -kernelRadius; offsetY <= kernelRadius; ++offsetY)
            {
                for (int offsetX = -kernelRadius; offsetX <= kernelRadius; ++offsetX)
                {
                    const int sampleX = targetX + offsetX;
                    const int sampleY = targetY + offsetY;

                    if (sampleX < 0
                        || sampleY < 0
                        || sampleX >= Game::OutdoorMapData::TerrainWidth
                        || sampleY >= Game::OutdoorMapData::TerrainHeight)
                    {
                        continue;
                    }

                    totalHeight += sourceHeights[flattenTerrainCellIndex(sampleX, sampleY)];
                    ++sampleCount;
                }
            }

            if (sampleCount <= 0)
            {
                return;
            }

            const float averageHeight = static_cast<float>(totalHeight) / static_cast<float>(sampleCount);
            const int currentHeight = sourceHeights[sampleIndex];
            const float deltaToAverage = averageHeight - static_cast<float>(currentHeight);

            if (std::fabs(deltaToAverage) <= 0.001f)
            {
                return;
            }

            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            const float blend = std::clamp((static_cast<float>(strength) / 8.0f) * falloff, 0.0f, 1.0f);
            int nextHeight = static_cast<int>(std::lround(
                static_cast<float>(currentHeight) + deltaToAverage * blend));

            if (nextHeight == currentHeight)
            {
                nextHeight = currentHeight + (deltaToAverage > 0.0f ? 1 : -1);
            }

            nextHeight = std::clamp(nextHeight, 0, 255);

            if (nextHeight == currentHeight)
            {
                return;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        });

    return mutated;
}

bool applyTerrainNoiseBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    int strength,
    EditorTerrainFalloffMode falloffMode)
{
    bool mutated = false;

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int effectiveRadius)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                return;
            }

            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            const uint32_t hash = terrainNoiseHash(targetX, targetY);
            const float noise = (static_cast<float>(hash & 1023u) / 511.5f) - 1.0f;
            int delta = static_cast<int>(std::lround(noise * static_cast<float>(strength) * 0.5f * falloff));

            if (delta == 0 && falloff > 0.0f && std::fabs(noise) > 0.25f)
            {
                delta = noise > 0.0f ? 1 : -1;
            }

            if (delta == 0)
            {
                return;
            }

            const int currentHeight = outdoorGeometry.heightMap[sampleIndex];
            const int nextHeight = std::clamp(currentHeight + delta, 0, 255);

            if (nextHeight == currentHeight)
            {
                return;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        });

    return mutated;
}

float distanceToTerrainSegment(
    float pointX,
    float pointY,
    float startX,
    float startY,
    float endX,
    float endY,
    float &t)
{
    const float deltaX = endX - startX;
    const float deltaY = endY - startY;
    const float lengthSquared = deltaX * deltaX + deltaY * deltaY;

    if (lengthSquared <= 0.0001f)
    {
        t = 0.0f;
        const float offsetX = pointX - startX;
        const float offsetY = pointY - startY;
        return std::sqrt(offsetX * offsetX + offsetY * offsetY);
    }

    t = std::clamp(((pointX - startX) * deltaX + (pointY - startY) * deltaY) / lengthSquared, 0.0f, 1.0f);
    const float nearestX = startX + deltaX * t;
    const float nearestY = startY + deltaY * t;
    const float offsetX = pointX - nearestX;
    const float offsetY = pointY - nearestY;
    return std::sqrt(offsetX * offsetX + offsetY * offsetY);
}

bool applyTerrainRampBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int startX,
    int startY,
    int endX,
    int endY,
    int startHeight,
    int endHeight,
    int radius,
    int strength,
    EditorTerrainFalloffMode falloffMode)
{
    const int effectiveRadius = std::max(radius, 1);
    const int minX = std::clamp(std::min(startX, endX) - effectiveRadius, 0, Game::OutdoorMapData::TerrainWidth - 1);
    const int maxX = std::clamp(std::max(startX, endX) + effectiveRadius, 0, Game::OutdoorMapData::TerrainWidth - 1);
    const int minY = std::clamp(std::min(startY, endY) - effectiveRadius, 0, Game::OutdoorMapData::TerrainHeight - 1);
    const int maxY = std::clamp(std::max(startY, endY) + effectiveRadius, 0, Game::OutdoorMapData::TerrainHeight - 1);
    bool mutated = false;

    for (int targetY = minY; targetY <= maxY; ++targetY)
    {
        for (int targetX = minX; targetX <= maxX; ++targetX)
        {
            float lineT = 0.0f;
            const float distance = distanceToTerrainSegment(
                static_cast<float>(targetX),
                static_cast<float>(targetY),
                static_cast<float>(startX),
                static_cast<float>(startY),
                static_cast<float>(endX),
                static_cast<float>(endY),
                lineT);

            if (distance > static_cast<float>(effectiveRadius))
            {
                continue;
            }

            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                continue;
            }

            const int targetHeight = static_cast<int>(std::lround(lerpFloat(
                static_cast<float>(startHeight),
                static_cast<float>(endHeight),
                lineT)));
            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            int maxDelta = static_cast<int>(std::round(static_cast<float>(strength) * falloff));

            if (maxDelta <= 0)
            {
                maxDelta = 1;
            }

            const int currentHeight = outdoorGeometry.heightMap[sampleIndex];
            const int deltaToTarget = targetHeight - currentHeight;

            if (deltaToTarget == 0)
            {
                continue;
            }

            const int delta = std::clamp(deltaToTarget, -maxDelta, maxDelta);
            const int nextHeight = std::clamp(currentHeight + delta, 0, 255);

            if (nextHeight == currentHeight)
            {
                continue;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        }
    }

    return mutated;
}

size_t flattenedOutdoorFaceIndex(const Game::OutdoorMapData &outdoorMapData, size_t bmodelIndex, size_t faceIndex)
{
    size_t flattenedIndex = 0;

    for (size_t index = 0; index < bmodelIndex && index < outdoorMapData.bmodels.size(); ++index)
    {
        flattenedIndex += outdoorMapData.bmodels[index].faces.size();
    }

    return flattenedIndex + faceIndex;
}

float distancePointToSegmentSquared(
    float pointX,
    float pointY,
    float startX,
    float startY,
    float endX,
    float endY)
{
    const float deltaX = endX - startX;
    const float deltaY = endY - startY;
    const float lengthSquared = squaredLength2(deltaX, deltaY);

    if (lengthSquared <= 0.0001f)
    {
        return squaredLength2(pointX - startX, pointY - startY);
    }

    const float t = std::clamp(
        ((pointX - startX) * deltaX + (pointY - startY) * deltaY) / lengthSquared,
        0.0f,
        1.0f);
    const float closestX = startX + deltaX * t;
    const float closestY = startY + deltaY * t;
    return squaredLength2(pointX - closestX, pointY - closestY);
}

struct ScreenPoint
{
    float x = 0.0f;
    float y = 0.0f;
};

bool isPointInsideScreenPolygon(float x, float y, const std::vector<ScreenPoint> &vertices)
{
    if (vertices.size() < 3)
    {
        return false;
    }

    bool isInside = false;
    size_t previousIndex = vertices.size() - 1;

    for (size_t currentIndex = 0; currentIndex < vertices.size(); ++currentIndex)
    {
        const ScreenPoint &currentVertex = vertices[currentIndex];
        const ScreenPoint &previousVertex = vertices[previousIndex];
        const bool intersects =
            ((currentVertex.y > y) != (previousVertex.y > y))
            && (x < (previousVertex.x - currentVertex.x) * (y - currentVertex.y)
                    / ((previousVertex.y - currentVertex.y) + 0.0001f)
                + currentVertex.x);

        if (intersects)
        {
            isInside = !isInside;
        }

        previousIndex = currentIndex;
    }

    return isInside;
}

bool isPointInsideOrNearScreenPolygon(float x, float y, const std::vector<ScreenPoint> &vertices, float slackPixels)
{
    if (isPointInsideScreenPolygon(x, y, vertices))
    {
        return true;
    }

    const float slackSquared = slackPixels * slackPixels;

    for (size_t index = 0; index < vertices.size(); ++index)
    {
        const size_t nextIndex = (index + 1) % vertices.size();

        if (distancePointToSegmentSquared(
                x,
                y,
                vertices[index].x,
                vertices[index].y,
                vertices[nextIndex].x,
                vertices[nextIndex].y) <= slackSquared)
        {
            return true;
        }
    }

    return false;
}

bx::Vec3 worldPointFromTerrainGrid(int gridX, int gridY, uint8_t heightSample)
{
    return {
        Game::outdoorGridCornerWorldX(gridX),
        Game::outdoorGridCornerWorldY(gridY),
        static_cast<float>(heightSample * Game::OutdoorMapData::TerrainHeightScale)
    };
}

bx::Vec3 worldPointFromLegacyPosition(int x, int y, int z)
{
    return {
        static_cast<float>(x),
        static_cast<float>(y),
        static_cast<float>(z)
    };
}

bool projectWorldPoint(
    const bx::Vec3 &worldPoint,
    const float *pViewProjectionMatrix,
    uint16_t viewportWidth,
    uint16_t viewportHeight,
    float &screenX,
    float &screenY,
    float &clipW)
{
    clipW =
        worldPoint.x * pViewProjectionMatrix[3]
        + worldPoint.y * pViewProjectionMatrix[7]
        + worldPoint.z * pViewProjectionMatrix[11]
        + pViewProjectionMatrix[15];

    if (clipW <= 0.0001f)
    {
        return false;
    }

    const float clipX =
        worldPoint.x * pViewProjectionMatrix[0]
        + worldPoint.y * pViewProjectionMatrix[4]
        + worldPoint.z * pViewProjectionMatrix[8]
        + pViewProjectionMatrix[12];
    const float clipY =
        worldPoint.x * pViewProjectionMatrix[1]
        + worldPoint.y * pViewProjectionMatrix[5]
        + worldPoint.z * pViewProjectionMatrix[9]
        + pViewProjectionMatrix[13];
    const float inverseW = 1.0f / clipW;
    const float ndcX = clipX * inverseW;
    const float ndcY = clipY * inverseW;

    if (ndcX < -1.25f || ndcX > 1.25f || ndcY < -1.25f || ndcY > 1.25f)
    {
        return false;
    }

    screenX = ((ndcX + 1.0f) * 0.5f) * static_cast<float>(viewportWidth);
    screenY = ((1.0f - ndcY) * 0.5f) * static_cast<float>(viewportHeight);
    return true;
}

bx::Vec3 safeTriangleNormal(
    const bx::Vec3 &first,
    const bx::Vec3 &second,
    const bx::Vec3 &third,
    const bx::Vec3 &fallback)
{
    const bx::Vec3 edgeA = vecSubtract(second, first);
    const bx::Vec3 edgeB = vecSubtract(third, first);
    const bx::Vec3 normal = vecCross(edgeA, edgeB);
    const float normalLength = vecLength(normal);

    if (normalLength <= 0.0001f)
    {
        return fallback;
    }

    return vecScale(normal, 1.0f / normalLength);
}

std::array<float, 2> proceduralPreviewUv(const bx::Vec3 &localPosition, const bx::Vec3 &normal)
{
    const float absX = std::abs(normal.x);
    const float absY = std::abs(normal.y);
    const float absZ = std::abs(normal.z);

    if (absZ >= absX && absZ >= absY)
    {
        return {localPosition.x, localPosition.y};
    }

    if (absX >= absY)
    {
        return {localPosition.y, localPosition.z};
    }

    return {localPosition.x, localPosition.z};
}

void appendProceduralTriangle(
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> &vertices,
    const bx::Vec3 &first,
    const bx::Vec3 &second,
    const bx::Vec3 &third,
    const bx::Vec3 &origin,
    const bx::Vec3 &fallbackNormal)
{
    const bx::Vec3 normal = safeTriangleNormal(first, second, third, fallbackNormal);
    const std::array<float, 2> uv0 = proceduralPreviewUv(vecSubtract(first, origin), normal);
    const std::array<float, 2> uv1 = proceduralPreviewUv(vecSubtract(second, origin), normal);
    const std::array<float, 2> uv2 = proceduralPreviewUv(vecSubtract(third, origin), normal);

    vertices.push_back({first.x, first.y, first.z, uv0[0], uv0[1], normal.x, normal.y, normal.z, 0.0f});
    vertices.push_back({second.x, second.y, second.z, uv1[0], uv1[1], normal.x, normal.y, normal.z, 0.0f});
    vertices.push_back({third.x, third.y, third.z, uv2[0], uv2[1], normal.x, normal.y, normal.z, 0.0f});
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildTerrainVertices(
    const Game::OutdoorMapData &outdoorMapData)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(Game::OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(Game::OutdoorMapData::TerrainHeight - 1)
        * 6);
    const bx::Vec3 terrainOrigin = {
        Game::outdoorGridCornerWorldX(0),
        Game::outdoorGridCornerWorldY(0),
        0.0f
    };
    const bx::Vec3 fallbackNormal = {0.0f, 0.0f, 1.0f};

    for (int gridY = 0; gridY < (Game::OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (Game::OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t topLeftIndex =
                static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex =
                static_cast<size_t>((gridY + 1) * Game::OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const bx::Vec3 topLeft = worldPointFromTerrainGrid(gridX, gridY, outdoorMapData.heightMap[topLeftIndex]);
            const bx::Vec3 topRight = worldPointFromTerrainGrid(gridX + 1, gridY, outdoorMapData.heightMap[topRightIndex]);
            const bx::Vec3 bottomLeft =
                worldPointFromTerrainGrid(gridX, gridY + 1, outdoorMapData.heightMap[bottomLeftIndex]);
            const bx::Vec3 bottomRight =
                worldPointFromTerrainGrid(gridX + 1, gridY + 1, outdoorMapData.heightMap[bottomRightIndex]);

            appendProceduralTriangle(vertices, topLeft, bottomLeft, topRight, terrainOrigin, fallbackNormal);
            appendProceduralTriangle(vertices, topRight, bottomLeft, bottomRight, terrainOrigin, fallbackNormal);
        }
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildTerrainErrorVertices(
    const Game::OutdoorMapData &outdoorMapData,
    const TerrainAtlasData &atlasData)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;
    const bx::Vec3 terrainOrigin = {
        Game::outdoorGridCornerWorldX(0),
        Game::outdoorGridCornerWorldY(0),
        0.0f
    };
    const bx::Vec3 fallbackNormal = {0.0f, 0.0f, 1.0f};

    for (int gridY = 0; gridY < (Game::OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (Game::OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex = static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const TerrainAtlasRegion &region = atlasData.tileRegions[static_cast<size_t>(rawTileId)];

            if (!region.hasMissingAsset)
            {
                continue;
            }

            const size_t topLeftIndex = tileMapIndex;
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * Game::OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const bx::Vec3 topLeft = worldPointFromTerrainGrid(gridX, gridY, outdoorMapData.heightMap[topLeftIndex]);
            const bx::Vec3 topRight = worldPointFromTerrainGrid(gridX + 1, gridY, outdoorMapData.heightMap[topRightIndex]);
            const bx::Vec3 bottomLeft =
                worldPointFromTerrainGrid(gridX, gridY + 1, outdoorMapData.heightMap[bottomLeftIndex]);
            const bx::Vec3 bottomRight =
                worldPointFromTerrainGrid(gridX + 1, gridY + 1, outdoorMapData.heightMap[bottomRightIndex]);

            appendProceduralTriangle(vertices, topLeft, bottomLeft, topRight, terrainOrigin, fallbackNormal);
            appendProceduralTriangle(vertices, topRight, bottomLeft, bottomRight, terrainOrigin, fallbackNormal);
        }
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::TexturedPreviewVertex> buildTexturedTerrainVertices(
    const Game::OutdoorMapData &outdoorMapData,
    const TerrainAtlasData &atlasData)
{
    std::vector<EditorOutdoorViewport::TexturedPreviewVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(Game::OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(Game::OutdoorMapData::TerrainHeight - 1)
        * 6);

    for (int gridY = 0; gridY < (Game::OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (Game::OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex = static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const TerrainAtlasRegion &region = atlasData.tileRegions[static_cast<size_t>(rawTileId)];

            if (!region.isValid)
            {
                continue;
            }

            const size_t topLeftIndex = tileMapIndex;
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * Game::OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;

            const bx::Vec3 topLeft = worldPointFromTerrainGrid(gridX, gridY, outdoorMapData.heightMap[topLeftIndex]);
            const bx::Vec3 topRight = worldPointFromTerrainGrid(gridX + 1, gridY, outdoorMapData.heightMap[topRightIndex]);
            const bx::Vec3 bottomLeft =
                worldPointFromTerrainGrid(gridX, gridY + 1, outdoorMapData.heightMap[bottomLeftIndex]);
            const bx::Vec3 bottomRight =
                worldPointFromTerrainGrid(gridX + 1, gridY + 1, outdoorMapData.heightMap[bottomRightIndex]);

            vertices.push_back({topLeft.x, topLeft.y, topLeft.z, region.u0, region.v0});
            vertices.push_back({bottomLeft.x, bottomLeft.y, bottomLeft.z, region.u0, region.v1});
            vertices.push_back({topRight.x, topRight.y, topRight.z, region.u1, region.v0});
            vertices.push_back({topRight.x, topRight.y, topRight.z, region.u1, region.v0});
            vertices.push_back({bottomLeft.x, bottomLeft.y, bottomLeft.z, region.u0, region.v1});
            vertices.push_back({bottomRight.x, bottomRight.y, bottomRight.z, region.u1, region.v1});
        }
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::PreviewVertex> buildBModelWireVertices(const Game::OutdoorMapData &outdoorMapData)
{
    std::vector<EditorOutdoorViewport::PreviewVertex> vertices;
    const uint32_t color = makeAbgr(255, 190, 96);

    for (const Game::OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const Game::OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.vertexIndices.size() < 2)
            {
                continue;
            }

            for (size_t vertexIndex = 0; vertexIndex < face.vertexIndices.size(); ++vertexIndex)
            {
                const uint16_t startIndex = face.vertexIndices[vertexIndex];
                const uint16_t endIndex = face.vertexIndices[(vertexIndex + 1) % face.vertexIndices.size()];

                if (startIndex >= bmodel.vertices.size() || endIndex >= bmodel.vertices.size())
                {
                    continue;
                }

                const bx::Vec3 start =
                    worldPointFromLegacyPosition(
                        bmodel.vertices[startIndex].x,
                        bmodel.vertices[startIndex].y,
                        bmodel.vertices[startIndex].z);
                const bx::Vec3 end =
                    worldPointFromLegacyPosition(
                        bmodel.vertices[endIndex].x,
                        bmodel.vertices[endIndex].y,
                        bmodel.vertices[endIndex].z);
                vertices.push_back({start.x, start.y, start.z, color});
                vertices.push_back({end.x, end.y, end.z, color});
            }
        }
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::TexturedPreviewVertex> buildTexturedBModelFaceVertices(
    const Game::OutdoorMapData &outdoorMapData,
    size_t bmodelIndex,
    size_t faceIndex,
    int textureWidth,
    int textureHeight)
{
    std::vector<EditorOutdoorViewport::TexturedPreviewVertex> vertices;

    if (textureWidth <= 0
        || textureHeight <= 0
        || bmodelIndex >= outdoorMapData.bmodels.size()
        || faceIndex >= outdoorMapData.bmodels[bmodelIndex].faces.size())
    {
        return vertices;
    }

    const Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];
    const Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];

    if (face.vertexIndices.size() < 3 || face.textureName.empty())
    {
        return vertices;
    }

    for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
    {
        const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
        EditorOutdoorViewport::TexturedPreviewVertex triangleVertices[3] = {};
        bool isTriangleValid = true;

        for (size_t triangleVertexSlot = 0; triangleVertexSlot < 3; ++triangleVertexSlot)
        {
            const size_t localTriangleVertexIndex = triangleVertexIndices[triangleVertexSlot];
            const uint16_t modelVertexIndex = face.vertexIndices[localTriangleVertexIndex];

            if (modelVertexIndex >= bmodel.vertices.size()
                || localTriangleVertexIndex >= face.textureUs.size()
                || localTriangleVertexIndex >= face.textureVs.size())
            {
                isTriangleValid = false;
                break;
            }

            const bx::Vec3 worldVertex = Game::outdoorBModelVertexToWorld(bmodel.vertices[modelVertexIndex]);
            const float normalizedU =
                static_cast<float>(face.textureUs[localTriangleVertexIndex] + face.textureDeltaU)
                / static_cast<float>(textureWidth);
            const float normalizedV =
                static_cast<float>(face.textureVs[localTriangleVertexIndex] + face.textureDeltaV)
                / static_cast<float>(textureHeight);
            triangleVertices[triangleVertexSlot] =
                {worldVertex.x, worldVertex.y, worldVertex.z, normalizedU, normalizedV};
        }

        if (!isTriangleValid)
        {
            continue;
        }

        vertices.push_back(triangleVertices[0]);
        vertices.push_back(triangleVertices[1]);
        vertices.push_back(triangleVertices[2]);
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildProceduralBModelFaceVertices(
    const Game::OutdoorBModel &bmodel,
    size_t faceIndex,
    const bx::Vec3 &origin)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;

    if (faceIndex >= bmodel.faces.size())
    {
        return vertices;
    }

    const Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];

    if (face.vertexIndices.size() < 3)
    {
        return vertices;
    }

    const bx::Vec3 fallbackNormal = {0.0f, 0.0f, 1.0f};

    for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
    {
        const size_t localIndices[3] = {0, triangleIndex, triangleIndex + 1};
        bx::Vec3 triangleVertices[3] = {
            {0.0f, 0.0f, 0.0f},
            {0.0f, 0.0f, 0.0f},
            {0.0f, 0.0f, 0.0f}
        };
        bool isTriangleValid = true;

        for (size_t vertexSlot = 0; vertexSlot < 3; ++vertexSlot)
        {
            const uint16_t modelVertexIndex = face.vertexIndices[localIndices[vertexSlot]];

            if (modelVertexIndex >= bmodel.vertices.size())
            {
                isTriangleValid = false;
                break;
            }

            triangleVertices[vertexSlot] = Game::outdoorBModelVertexToWorld(bmodel.vertices[modelVertexIndex]);
        }

        if (!isTriangleValid)
        {
            continue;
        }

        appendProceduralTriangle(
            vertices,
            triangleVertices[0],
            triangleVertices[1],
            triangleVertices[2],
            origin,
            fallbackNormal);
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildProceduralBModelFaceVertices(
    const Game::OutdoorMapData &outdoorMapData,
    size_t bmodelIndex,
    size_t faceIndex,
    const bx::Vec3 &origin)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;

    if (bmodelIndex >= outdoorMapData.bmodels.size() || faceIndex >= outdoorMapData.bmodels[bmodelIndex].faces.size())
    {
        return vertices;
    }

    return buildProceduralBModelFaceVertices(outdoorMapData.bmodels[bmodelIndex], faceIndex, origin);
}

void appendCrossMarker(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const bx::Vec3 &center,
    float halfExtent,
    float height,
    uint32_t color)
{
    vertices.push_back({center.x - halfExtent, center.y, center.z + height * 0.5f, color});
    vertices.push_back({center.x + halfExtent, center.y, center.z + height * 0.5f, color});
    vertices.push_back({center.x, center.y - halfExtent, center.z + height * 0.5f, color});
    vertices.push_back({center.x, center.y + halfExtent, center.z + height * 0.5f, color});
    vertices.push_back({center.x, center.y, center.z, color});
    vertices.push_back({center.x, center.y, center.z + height, color});
}
}

bgfx::VertexLayout EditorOutdoorViewport::PreviewVertex::ms_layout;
bgfx::VertexLayout EditorOutdoorViewport::TexturedPreviewVertex::ms_layout;
bgfx::VertexLayout EditorOutdoorViewport::ProceduralPreviewVertex::ms_layout;

EditorOutdoorViewport::EditorOutdoorViewport()
{
}

EditorOutdoorViewport::~EditorOutdoorViewport()
{
    shutdown();
}

void EditorOutdoorViewport::PreviewVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

void EditorOutdoorViewport::TexturedPreviewVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
}

void EditorOutdoorViewport::ProceduralPreviewVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord1, 4, bgfx::AttribType::Float)
        .end();
}

void EditorOutdoorViewport::shutdown()
{
    if (m_shutdownComplete)
    {
        return;
    }

    m_shutdownComplete = true;
    destroyImportedModelPreview();
    destroyGeometryBuffers();
    destroyRenderTarget();

    for (auto &[textureName, texture] : m_entityBillboardTextures)
    {
        if (bgfx::isValid(texture.textureHandle))
        {
            bgfx::destroy(texture.textureHandle);
            texture.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_entityBillboardTextures.clear();

    if (bgfx::isValid(m_programHandle))
    {
        bgfx::destroy(m_programHandle);
        m_programHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_texturedProgramHandle))
    {
        bgfx::destroy(m_texturedProgramHandle);
        m_texturedProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_proceduralPreviewProgramHandle))
    {
        bgfx::destroy(m_proceduralPreviewProgramHandle);
        m_proceduralPreviewProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_textureSamplerHandle))
    {
        bgfx::destroy(m_textureSamplerHandle);
        m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewColorAHandle))
    {
        bgfx::destroy(m_previewColorAHandle);
        m_previewColorAHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewColorBHandle))
    {
        bgfx::destroy(m_previewColorBHandle);
        m_previewColorBHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewColorCHandle))
    {
        bgfx::destroy(m_previewColorCHandle);
        m_previewColorCHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewColorDHandle))
    {
        bgfx::destroy(m_previewColorDHandle);
        m_previewColorDHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewParams0Handle))
    {
        bgfx::destroy(m_previewParams0Handle);
        m_previewParams0Handle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewParams1Handle))
    {
        bgfx::destroy(m_previewParams1Handle);
        m_previewParams1Handle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewObjectOriginHandle))
    {
        bgfx::destroy(m_previewObjectOriginHandle);
        m_previewObjectOriginHandle = BGFX_INVALID_HANDLE;
    }

    m_geometryKey.clear();
    m_cameraDocumentKey.clear();
    m_cameraInitializedForDocument = false;
}

void EditorOutdoorViewport::destroyImportedModelPreview()
{
    if (bgfx::isValid(m_importedModelPreviewBatch.vertexBufferHandle))
    {
        bgfx::destroy(m_importedModelPreviewBatch.vertexBufferHandle);
        m_importedModelPreviewBatch.vertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    m_importedModelPreviewBatch.vertexCount = 0;
    m_importedModelPreviewBatch.bmodelIndex = std::numeric_limits<size_t>::max();
    m_importedModelPreviewBatch.objectOrigin = {0.0f, 0.0f, 0.0f};
    m_importedModelPreviewKey.clear();
}

void EditorOutdoorViewport::updateAndRender(
    EditorSession &session,
    int viewportX,
    int viewportY,
    uint16_t viewportWidth,
    uint16_t viewportHeight,
    bool isHovered,
    bool isFocused,
    bool leftMouseClicked,
    bool leftMouseDown,
    float mouseX,
    float mouseY,
    float deltaSeconds)
{
    m_viewportX = viewportX;
    m_viewportY = viewportY;
    m_viewportWidth = viewportWidth;
    m_viewportHeight = viewportHeight;
    m_isHovered = isHovered;
    m_isFocused = isFocused;
    m_lastMouseX = mouseX;
    m_lastMouseY = mouseY;

    ensureRenderTarget(viewportWidth, viewportHeight);

    if (bgfx::isValid(m_frameBufferHandle))
    {
        bgfx::setViewFrameBuffer(EditorSceneViewId, m_frameBufferHandle);
    }

    bgfx::setViewRect(EditorSceneViewId, 0, 0, m_renderWidth, m_renderHeight);
    bgfx::setViewClear(EditorSceneViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x2c2217ffu, 1.0f, 0);
    bgfx::touch(EditorSceneViewId);

    if (!session.hasDocument() || session.document().kind() != EditorDocument::Kind::Outdoor)
    {
        return;
    }

    if (!ensureRenderResources())
    {
        return;
    }

    const EditorDocument &document = session.document();
    ensureGeometryBuffers(session);
    updateCamera(document, isHovered, isFocused, deltaSeconds);
    tryPick(session, leftMouseClicked, mouseX, mouseY);

    const bx::Vec3 forward = {
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    };
    const bx::Vec3 at = {
        m_cameraPosition.x + forward.x,
        m_cameraPosition.y + forward.y,
        m_cameraPosition.z + forward.z
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};

    bx::mtxLookAt(m_viewMatrix, m_cameraPosition, at, up, bx::Handedness::Right);
    bx::mtxProj(
        m_projectionMatrix,
        CameraVerticalFovDegrees,
        static_cast<float>(m_renderWidth) / static_cast<float>(std::max<uint16_t>(m_renderHeight, 1)),
        CameraNearPlane,
        CameraFarPlane,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right);
    bx::mtxMul(m_viewProjectionMatrix, m_viewMatrix, m_projectionMatrix);
    bgfx::setViewTransform(EditorSceneViewId, m_viewMatrix, m_projectionMatrix);
    ensureImportedModelPreview(session);

    if (ImGui::IsKeyPressed(ImGuiKey_Escape))
    {
        setPlacementKind(EditorSelectionKind::None);
    }

    if (isFocused && !ImGui::GetIO().WantTextInput)
    {
        if (ImGui::IsKeyPressed(ImGuiKey_W))
        {
            m_transformGizmoMode = TransformGizmoMode::Translate;
        }
        else if (ImGui::IsKeyPressed(ImGuiKey_R))
        {
            m_transformGizmoMode = TransformGizmoMode::Rotate;
        }
        else if (ImGui::IsKeyPressed(ImGuiKey_F))
        {
            focusSelection(document, session.selection());
        }
    }

    const bool selectedTerrainCell = trySelectTerrainCell(session, leftMouseClicked, mouseX, mouseY);
    const bool selectedInteractiveFace =
        !selectedTerrainCell && trySelectInteractiveFace(session, leftMouseClicked, mouseX, mouseY);
    const bool placedObject =
        !selectedTerrainCell && !selectedInteractiveFace && tryPlaceObject(session, leftMouseClicked, mouseX, mouseY);
    const bool startedGizmoDrag =
        !placedObject && tryBeginGizmoDrag(session, leftMouseClicked, mouseX, mouseY);
    updateGizmoDrag(session, leftMouseDown, mouseX, mouseY);

    if (!selectedTerrainCell
        && !selectedInteractiveFace
        && !placedObject
        && !startedGizmoDrag
        && m_activeGizmoDrag.mode == GizmoDragMode::None)
    {
        tryPick(session, leftMouseClicked, mouseX, mouseY);
    }

    submitStaticGeometry(session);
    submitEntityBillboardGeometry(session, document);
    submitMarkerGeometry(session, document, session.selection());
}

void EditorOutdoorViewport::renderOverlayUi(const EditorSession &session)
{
    std::string modeLabel = placementKindLabel(m_placementKind);

    if (m_placementKind == EditorSelectionKind::Terrain)
    {
        modeLabel += session.terrainSculptEnabled() ? " / SCULPT" : " / PAINT";
    }
    else if (m_placementKind == EditorSelectionKind::BModel)
    {
        modeLabel = "BMODEL PLACE";
    }
    else if (m_placementKind == EditorSelectionKind::Entity)
    {
        modeLabel = "ENTITY PLACE";
    }
    else if (m_placementKind == EditorSelectionKind::Spawn)
    {
        modeLabel = "SPAWN PLACE";
    }
    else if (m_placementKind == EditorSelectionKind::Actor)
    {
        modeLabel = "ACTOR PLACE";
    }
    else if (m_placementKind == EditorSelectionKind::SpriteObject)
    {
        modeLabel = "OBJECT PLACE";
    }

    ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.95f, 0.87f, 0.76f, 1.0f));
    ImGui::Text(
        "%s  ·  %s  ·  %s",
        modeLabel.c_str(),
        m_transformGizmoMode == TransformGizmoMode::Rotate ? "Rotate" : "Move",
        m_transformSpaceMode == TransformSpaceMode::Local ? "Local" : "World");
    ImGui::PopStyleColor();

    if (m_placementKind == EditorSelectionKind::Terrain)
    {
        ImGui::TextDisabled(
            "%s",
            session.terrainSculptEnabled()
                ? "LMB sculpt  ·  drag  ·  Alt+LMB sample"
                : (session.terrainPaintEnabled() ? "LMB paint  ·  drag" : "LMB select cell  ·  Esc select"));
    }
    else
    {
        ImGui::TextDisabled(
            "%s",
            m_placementKind == EditorSelectionKind::BModel
                ? "Move cursor  ·  LMB place  ·  Esc cancel"
                : "RMB look  ·  WASD move  ·  F frame");
    }

    if (m_placementKind == EditorSelectionKind::Terrain)
    {
        if (session.terrainSculptEnabled())
        {
            const char *pFalloffLabel = "Linear";

            switch (session.terrainSculptFalloffMode())
            {
            case EditorTerrainFalloffMode::Flat:
                pFalloffLabel = "Flat";
                break;

            case EditorTerrainFalloffMode::Smooth:
                pFalloffLabel = "Smooth";
                break;

            case EditorTerrainFalloffMode::Linear:
            default:
                break;
            }

            ImGui::Text(
                "%s  ·  R %d  ·  S %d  ·  %s",
                session.terrainSculptMode() == EditorTerrainSculptMode::Lower
                    ? "lower"
                    : session.terrainSculptMode() == EditorTerrainSculptMode::Flatten
                        ? "flatten"
                        : session.terrainSculptMode() == EditorTerrainSculptMode::Smooth
                            ? "smooth"
                            : session.terrainSculptMode() == EditorTerrainSculptMode::Noise
                                ? "noise"
                                : session.terrainSculptMode() == EditorTerrainSculptMode::Ramp ? "ramp" : "raise",
                session.terrainSculptRadius(),
                session.terrainSculptStrength(),
                pFalloffLabel);
        }
        else
        {
            const char *pPaintModeLabel = "Brush";

            switch (session.terrainPaintMode())
            {
            case EditorTerrainPaintMode::Rectangle:
                pPaintModeLabel = "Rectangle";
                break;

            case EditorTerrainPaintMode::Fill:
                pPaintModeLabel = "Fill";
                break;

            case EditorTerrainPaintMode::Brush:
            default:
                break;
            }

            if (session.terrainPaintMode() == EditorTerrainPaintMode::Brush)
            {
                ImGui::Text(
                    "%s  ·  Tile %u  ·  R %d  ·  Edge %d",
                    pPaintModeLabel,
                    static_cast<unsigned>(session.terrainPaintTileId()),
                    session.terrainPaintRadius(),
                    session.terrainPaintEdgeNoise());
            }
            else
            {
                ImGui::Text(
                    "%s  ·  Tile %u  ·  R %d",
                    pPaintModeLabel,
                    static_cast<unsigned>(session.terrainPaintTileId()),
                    session.terrainPaintRadius());
            }
        }
    }
    else if (session.selection().kind == EditorSelectionKind::InteractiveFace)
    {
        const size_t selectedFaceCount =
            session.selectedInteractiveFaceIndices().empty() ? 1 : session.selectedInteractiveFaceIndices().size();
        ImGui::Text("Face selection  ·  %zu selected", selectedFaceCount);
    }
    else if (session.selection().kind == EditorSelectionKind::BModel)
    {
        ImGui::TextDisabled("Selected BModel %zu", session.selection().index);
    }
    else
    {
        ImGui::TextDisabled(
            "Preview %s%s",
            m_previewMaterialMode == PreviewMaterialMode::Clay
                ? "Clay"
                : m_previewMaterialMode == PreviewMaterialMode::Grid ? "Grid" : "Textured",
            m_forcePreviewOnSelectedOnly ? "  ·  Selected" : "");
    }
}

void EditorOutdoorViewport::setPlacementKind(EditorSelectionKind kind)
{
    m_placementKind = kind;

    if (kind != EditorSelectionKind::Entity)
    {
        m_pendingEntityPlacementPreview.reset();
    }

    if (kind != EditorSelectionKind::SpriteObject)
    {
        m_pendingSpriteObjectPlacementPreview.reset();
    }
}

EditorSelectionKind EditorOutdoorViewport::placementKind() const
{
    return m_placementKind;
}

bool EditorOutdoorViewport::snapEnabled() const
{
    return m_snapEnabled;
}

void EditorOutdoorViewport::setSnapEnabled(bool enabled)
{
    m_snapEnabled = enabled;
}

int EditorOutdoorViewport::snapStep() const
{
    return m_snapStep;
}

void EditorOutdoorViewport::setSnapStep(int step)
{
    m_snapStep = std::max(step, 1);
}

bool EditorOutdoorViewport::showTerrainFill() const
{
    return m_showTerrainFill;
}

void EditorOutdoorViewport::setShowTerrainFill(bool enabled)
{
    m_showTerrainFill = enabled;
}

bool EditorOutdoorViewport::showTerrainGrid() const
{
    return m_showTerrainGrid;
}

void EditorOutdoorViewport::setShowTerrainGrid(bool enabled)
{
    m_showTerrainGrid = enabled;
}

EditorOutdoorViewport::PreviewMaterialMode EditorOutdoorViewport::previewMaterialMode() const
{
    return m_previewMaterialMode;
}

void EditorOutdoorViewport::setPreviewMaterialMode(PreviewMaterialMode mode)
{
    m_previewMaterialMode = mode;
}

bool EditorOutdoorViewport::forcePreviewOnSelectedOnly() const
{
    return m_forcePreviewOnSelectedOnly;
}

void EditorOutdoorViewport::setForcePreviewOnSelectedOnly(bool enabled)
{
    m_forcePreviewOnSelectedOnly = enabled;
}

bool EditorOutdoorViewport::showBModels() const
{
    return m_showBModels;
}

void EditorOutdoorViewport::setShowBModels(bool enabled)
{
    m_showBModels = enabled;
}

bool EditorOutdoorViewport::showBModelWireframe() const
{
    return m_showBModelWireframe;
}

void EditorOutdoorViewport::setShowBModelWireframe(bool enabled)
{
    m_showBModelWireframe = enabled;
}

bool EditorOutdoorViewport::showEntities() const
{
    return m_showEntities;
}

void EditorOutdoorViewport::setShowEntities(bool enabled)
{
    m_showEntities = enabled;
}

bool EditorOutdoorViewport::showEntityBillboards() const
{
    return m_showEntityBillboards;
}

void EditorOutdoorViewport::setShowEntityBillboards(bool enabled)
{
    m_showEntityBillboards = enabled;
}

bool EditorOutdoorViewport::showSpawns() const
{
    return m_showSpawns;
}

void EditorOutdoorViewport::setShowSpawns(bool enabled)
{
    m_showSpawns = enabled;
}

bool EditorOutdoorViewport::showActors() const
{
    return m_showActors;
}

void EditorOutdoorViewport::setShowActors(bool enabled)
{
    m_showActors = enabled;
}

bool EditorOutdoorViewport::showActorBillboards() const
{
    return m_showActorBillboards;
}

void EditorOutdoorViewport::setShowActorBillboards(bool enabled)
{
    m_showActorBillboards = enabled;
}

bool EditorOutdoorViewport::showSpriteObjects() const
{
    return m_showSpriteObjects;
}

void EditorOutdoorViewport::setShowSpriteObjects(bool enabled)
{
    m_showSpriteObjects = enabled;
}

bool EditorOutdoorViewport::showSpawnActorBillboards() const
{
    return m_showSpawnActorBillboards;
}

void EditorOutdoorViewport::setShowSpawnActorBillboards(bool enabled)
{
    m_showSpawnActorBillboards = enabled;
}

bool EditorOutdoorViewport::showEventMarkers() const
{
    return m_showEventMarkers;
}

void EditorOutdoorViewport::setShowEventMarkers(bool enabled)
{
    m_showEventMarkers = enabled;
}

bool EditorOutdoorViewport::showChestLinks() const
{
    return m_showChestLinks;
}

void EditorOutdoorViewport::setShowChestLinks(bool enabled)
{
    m_showChestLinks = enabled;
}

void EditorOutdoorViewport::setImportedModelPreviewRequest(
    const std::optional<ImportedModelPreviewRequest> &request)
{
    m_importedModelPreviewRequest = request;

    if (!m_importedModelPreviewRequest)
    {
        destroyImportedModelPreview();
    }
}

EditorOutdoorViewport::TransformGizmoMode EditorOutdoorViewport::transformGizmoMode() const
{
    return m_transformGizmoMode;
}

void EditorOutdoorViewport::setTransformGizmoMode(TransformGizmoMode mode)
{
    m_transformGizmoMode = mode;
}

EditorOutdoorViewport::TransformSpaceMode EditorOutdoorViewport::transformSpaceMode() const
{
    return m_transformSpaceMode;
}

void EditorOutdoorViewport::setTransformSpaceMode(TransformSpaceMode mode)
{
    m_transformSpaceMode = mode;
}

void EditorOutdoorViewport::focusSelection(const EditorDocument &document, const EditorSelection &selection)
{
    const std::optional<bx::Vec3> focusPoint = selectedWorldPosition(document, selection);

    if (!focusPoint)
    {
        return;
    }

    const float focusDistance = 3072.0f;
    const bx::Vec3 targetPosition = {
        focusPoint->x - focusDistance * 0.45f,
        focusPoint->y - focusDistance * 0.95f,
        focusPoint->z + focusDistance * 0.40f
    };
    const bx::Vec3 toFocus = {
        focusPoint->x - targetPosition.x,
        focusPoint->y - targetPosition.y,
        focusPoint->z - targetPosition.z
    };
    const float planarLength = std::sqrt(toFocus.x * toFocus.x + toFocus.y * toFocus.y);
    const float targetYawRadians = std::atan2(toFocus.x, toFocus.y);
    const float targetPitchRadians = std::atan2(toFocus.z, std::max(planarLength, 0.001f));

    m_activeCameraFocus.active = true;
    m_activeCameraFocus.startPosition = m_cameraPosition;
    m_activeCameraFocus.targetPosition = targetPosition;
    m_activeCameraFocus.startYawRadians = m_cameraYawRadians;
    m_activeCameraFocus.targetYawRadians = targetYawRadians;
    m_activeCameraFocus.startPitchRadians = m_cameraPitchRadians;
    m_activeCameraFocus.targetPitchRadians = std::clamp(
        targetPitchRadians,
        CameraMinPitchRadians,
        CameraMaxPitchRadians);
    m_activeCameraFocus.progressSeconds = 0.0f;
    m_activeCameraFocus.durationSeconds = CameraFocusDurationSeconds;
}

void EditorOutdoorViewport::focusBModel(const EditorDocument &document, size_t bmodelIndex)
{
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    if (bmodelIndex >= outdoorGeometry.bmodels.size())
    {
        return;
    }

    const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float x = static_cast<float>(vertex.x);
        const float y = static_cast<float>(vertex.y);
        const float z = static_cast<float>(vertex.z);
        minX = std::min(minX, x);
        minY = std::min(minY, y);
        minZ = std::min(minZ, z);
        maxX = std::max(maxX, x);
        maxY = std::max(maxY, y);
        maxZ = std::max(maxZ, z);
    }

    if (!std::isfinite(minX) || !std::isfinite(maxX))
    {
        return;
    }

    const bx::Vec3 focusPoint = {
        (minX + maxX) * 0.5f,
        (minY + maxY) * 0.5f,
        (minZ + maxZ) * 0.5f
    };
    const float extentX = maxX - minX;
    const float extentY = maxY - minY;
    const float extentZ = maxZ - minZ;
    const float extent = std::max({extentX, extentY, extentZ, static_cast<float>(bmodel.boundingRadius)});
    const float focusDistance = std::max(extent * 2.2f, 3072.0f);
    const bx::Vec3 targetPosition = {
        focusPoint.x - focusDistance * 0.45f,
        focusPoint.y - focusDistance * 0.95f,
        focusPoint.z + focusDistance * 0.40f
    };
    const bx::Vec3 toFocus = {
        focusPoint.x - targetPosition.x,
        focusPoint.y - targetPosition.y,
        focusPoint.z - targetPosition.z
    };
    const float planarLength = std::sqrt(toFocus.x * toFocus.x + toFocus.y * toFocus.y);
    const float targetYawRadians = std::atan2(toFocus.x, toFocus.y);
    const float targetPitchRadians = std::atan2(toFocus.z, std::max(planarLength, 0.001f));

    m_activeCameraFocus.active = true;
    m_activeCameraFocus.startPosition = m_cameraPosition;
    m_activeCameraFocus.targetPosition = targetPosition;
    m_activeCameraFocus.startYawRadians = m_cameraYawRadians;
    m_activeCameraFocus.targetYawRadians = targetYawRadians;
    m_activeCameraFocus.startPitchRadians = m_cameraPitchRadians;
    m_activeCameraFocus.targetPitchRadians = std::clamp(
        targetPitchRadians,
        CameraMinPitchRadians,
        CameraMaxPitchRadians);
    m_activeCameraFocus.progressSeconds = 0.0f;
    m_activeCameraFocus.durationSeconds = CameraFocusDurationSeconds;
}

const bx::Vec3 &EditorOutdoorViewport::cameraPosition() const
{
    return m_cameraPosition;
}

float EditorOutdoorViewport::cameraYawRadians() const
{
    return m_cameraYawRadians;
}

float EditorOutdoorViewport::cameraPitchRadians() const
{
    return m_cameraPitchRadians;
}

bgfx::TextureHandle EditorOutdoorViewport::viewportTextureHandle() const
{
    return m_colorTextureHandle;
}

bgfx::TextureHandle EditorOutdoorViewport::terrainTextureAtlasHandle() const
{
    return m_terrainTextureAtlasHandle;
}

bool EditorOutdoorViewport::tryGetTerrainTilePreviewUv(
    uint8_t tileId,
    float &u0,
    float &v0,
    float &u1,
    float &v1) const
{
    if (!m_terrainTilePreviewValid[static_cast<size_t>(tileId)])
    {
        return false;
    }

    const std::array<float, 4> &uvs = m_terrainTilePreviewUvs[static_cast<size_t>(tileId)];
    u0 = uvs[0];
    v0 = uvs[1];
    u1 = uvs[2];
    v1 = uvs[3];
    return true;
}

bool EditorOutdoorViewport::ensureRenderResources()
{
    if (bgfx::isValid(m_programHandle)
        && bgfx::isValid(m_texturedProgramHandle)
        && bgfx::isValid(m_proceduralPreviewProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && bgfx::isValid(m_previewColorAHandle)
        && bgfx::isValid(m_previewColorBHandle)
        && bgfx::isValid(m_previewColorCHandle)
        && bgfx::isValid(m_previewColorDHandle)
        && bgfx::isValid(m_previewParams0Handle)
        && bgfx::isValid(m_previewParams1Handle)
        && bgfx::isValid(m_previewObjectOriginHandle))
    {
        return true;
    }

    PreviewVertex::init();
    TexturedPreviewVertex::init();
    ProceduralPreviewVertex::init();
    m_programHandle = loadProgram("vs_cubes", "fs_cubes");
    m_texturedProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_shadowmaps_texture");
    m_proceduralPreviewProgramHandle = loadProgram("vs_editor_preview_material", "fs_editor_preview_material");
    m_textureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);
    m_previewColorAHandle = bgfx::createUniform("u_previewColorA", bgfx::UniformType::Vec4);
    m_previewColorBHandle = bgfx::createUniform("u_previewColorB", bgfx::UniformType::Vec4);
    m_previewColorCHandle = bgfx::createUniform("u_previewColorC", bgfx::UniformType::Vec4);
    m_previewColorDHandle = bgfx::createUniform("u_previewColorD", bgfx::UniformType::Vec4);
    m_previewParams0Handle = bgfx::createUniform("u_previewParams0", bgfx::UniformType::Vec4);
    m_previewParams1Handle = bgfx::createUniform("u_previewParams1", bgfx::UniformType::Vec4);
    m_previewObjectOriginHandle = bgfx::createUniform("u_previewObjectOrigin", bgfx::UniformType::Vec4);
    return bgfx::isValid(m_programHandle)
        && bgfx::isValid(m_texturedProgramHandle)
        && bgfx::isValid(m_proceduralPreviewProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && bgfx::isValid(m_previewColorAHandle)
        && bgfx::isValid(m_previewColorBHandle)
        && bgfx::isValid(m_previewColorCHandle)
        && bgfx::isValid(m_previewColorDHandle)
        && bgfx::isValid(m_previewParams0Handle)
        && bgfx::isValid(m_previewParams1Handle)
        && bgfx::isValid(m_previewObjectOriginHandle);
}

void EditorOutdoorViewport::destroyGeometryBuffers()
{
    if (bgfx::isValid(m_terrainVertexBufferHandle))
    {
        bgfx::destroy(m_terrainVertexBufferHandle);
        m_terrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_bmodelWireVertexBufferHandle))
    {
        bgfx::destroy(m_bmodelWireVertexBufferHandle);
        m_bmodelWireVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainErrorVertexBufferHandle))
    {
        bgfx::destroy(m_terrainErrorVertexBufferHandle);
        m_terrainErrorVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_texturedTerrainVertexBufferHandle))
    {
        bgfx::destroy(m_texturedTerrainVertexBufferHandle);
        m_texturedTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainTextureAtlasHandle))
    {
        bgfx::destroy(m_terrainTextureAtlasHandle);
        m_terrainTextureAtlasHandle = BGFX_INVALID_HANDLE;
    }

    m_terrainTilePreviewValid.fill(false);
    m_terrainTilePreviewUvs.fill({0.0f, 0.0f, 0.0f, 0.0f});

    for (TexturedBatch &batch : m_bmodelTexturedBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }

        if (bgfx::isValid(batch.textureHandle))
        {
            bgfx::destroy(batch.textureHandle);
        }
    }

    m_bmodelTexturedBatches.clear();
    for (ProceduralBatch &batch : m_bmodelAllFaceBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    for (ProceduralBatch &batch : m_bmodelUnassignedBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    for (ProceduralBatch &batch : m_bmodelMissingAssetBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    m_bmodelAllFaceBatches.clear();
    m_bmodelUnassignedBatches.clear();
    m_bmodelMissingAssetBatches.clear();

    m_terrainVertexCount = 0;
    m_terrainErrorVertexCount = 0;
    m_texturedTerrainVertexCount = 0;
    m_bmodelWireVertexCount = 0;
}

void EditorOutdoorViewport::ensureRenderTarget(uint16_t viewportWidth, uint16_t viewportHeight)
{
    const ImVec2 framebufferScale = ImGui::GetIO().DisplayFramebufferScale;
    const uint16_t renderWidth = static_cast<uint16_t>(std::max(
        1.0f,
        std::round(static_cast<float>(viewportWidth) * framebufferScale.x)));
    const uint16_t renderHeight = static_cast<uint16_t>(std::max(
        1.0f,
        std::round(static_cast<float>(viewportHeight) * framebufferScale.y)));

    if (bgfx::isValid(m_frameBufferHandle) && renderWidth == m_renderWidth && renderHeight == m_renderHeight)
    {
        return;
    }

    destroyRenderTarget();
    m_renderWidth = renderWidth;
    m_renderHeight = renderHeight;
    m_colorTextureHandle = bgfx::createTexture2D(
        renderWidth,
        renderHeight,
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    m_depthTextureHandle = bgfx::createTexture2D(
        renderWidth,
        renderHeight,
        false,
        1,
        bgfx::TextureFormat::D24S8,
        BGFX_TEXTURE_RT_WRITE_ONLY);

    if (!bgfx::isValid(m_colorTextureHandle) || !bgfx::isValid(m_depthTextureHandle))
    {
        destroyRenderTarget();
        return;
    }

    std::array<bgfx::Attachment, 2> attachments = {};
    attachments[0].init(m_colorTextureHandle);
    attachments[1].init(m_depthTextureHandle);
    m_frameBufferHandle = bgfx::createFrameBuffer(
        static_cast<uint8_t>(attachments.size()),
        attachments.data(),
        true);

    if (!bgfx::isValid(m_frameBufferHandle))
    {
        destroyRenderTarget();
    }
}

void EditorOutdoorViewport::destroyRenderTarget()
{
    if (bgfx::isValid(m_frameBufferHandle))
    {
        bgfx::destroy(m_frameBufferHandle);
        m_frameBufferHandle = BGFX_INVALID_HANDLE;
    }

    m_colorTextureHandle = BGFX_INVALID_HANDLE;
    m_depthTextureHandle = BGFX_INVALID_HANDLE;
}

void EditorOutdoorViewport::ensureGeometryBuffers(const EditorSession &session)
{
    if (!session.hasDocument() || session.assetFileSystem() == nullptr)
    {
        return;
    }

    const EditorDocument &document = session.document();
    const std::string geometryKey = documentGeometryKey(document);

    if (geometryKey == m_geometryKey)
    {
        return;
    }

    destroyGeometryBuffers();
    m_geometryKey = geometryKey;
    const Engine::AssetFileSystem &assetFileSystem = *session.assetFileSystem();
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const std::vector<ProceduralPreviewVertex> terrainVertices = buildTerrainVertices(outdoorGeometry);
    const std::vector<PreviewVertex> bmodelWireVertices = buildBModelWireVertices(outdoorGeometry);

    if (!terrainVertices.empty())
    {
        m_terrainVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                terrainVertices.data(),
                static_cast<uint32_t>(terrainVertices.size() * sizeof(ProceduralPreviewVertex))),
            ProceduralPreviewVertex::ms_layout);
        m_terrainVertexCount = static_cast<uint32_t>(terrainVertices.size());
    }

    if (!bmodelWireVertices.empty())
    {
        m_bmodelWireVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                bmodelWireVertices.data(),
                static_cast<uint32_t>(bmodelWireVertices.size() * sizeof(PreviewVertex))),
            PreviewVertex::ms_layout);
        m_bmodelWireVertexCount = static_cast<uint32_t>(bmodelWireVertices.size());
    }

    BitmapLoadCache bitmapLoadCache = {};
    const std::optional<TerrainAtlasData> atlasData = buildTerrainAtlasData(assetFileSystem, outdoorGeometry, bitmapLoadCache);

    if (atlasData && !atlasData->pixels.empty())
    {
        for (size_t tileIndex = 0; tileIndex < atlasData->tileRegions.size(); ++tileIndex)
        {
            const TerrainAtlasRegion &region = atlasData->tileRegions[tileIndex];
            m_terrainTilePreviewValid[tileIndex] = region.isValid;
            m_terrainTilePreviewUvs[tileIndex] = {region.u0, region.v0, region.u1, region.v1};
        }

        const std::vector<TexturedPreviewVertex> texturedTerrainVertices =
            buildTexturedTerrainVertices(outdoorGeometry, *atlasData);

        if (!texturedTerrainVertices.empty())
        {
            m_texturedTerrainVertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    texturedTerrainVertices.data(),
                    static_cast<uint32_t>(texturedTerrainVertices.size() * sizeof(TexturedPreviewVertex))),
                TexturedPreviewVertex::ms_layout);
            m_texturedTerrainVertexCount = static_cast<uint32_t>(texturedTerrainVertices.size());
        }

        m_terrainTextureAtlasHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(atlasData->width),
            static_cast<uint16_t>(atlasData->height),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_U_CLAMP
                | BGFX_SAMPLER_V_CLAMP
                | BGFX_SAMPLER_MIN_POINT
                | BGFX_SAMPLER_MAG_POINT
                | BGFX_SAMPLER_MIP_POINT,
            bgfx::copy(atlasData->pixels.data(), static_cast<uint32_t>(atlasData->pixels.size())));

        const std::vector<ProceduralPreviewVertex> terrainErrorVertices =
            buildTerrainErrorVertices(outdoorGeometry, *atlasData);

        if (!terrainErrorVertices.empty())
        {
            m_terrainErrorVertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    terrainErrorVertices.data(),
                    static_cast<uint32_t>(terrainErrorVertices.size() * sizeof(ProceduralPreviewVertex))),
                ProceduralPreviewVertex::ms_layout);
            m_terrainErrorVertexCount = static_cast<uint32_t>(terrainErrorVertices.size());
        }
    }

    std::unordered_map<std::string, std::vector<TexturedPreviewVertex>> batchVerticesByKey;
    std::unordered_map<std::string, std::string> textureNameByBatchKey;
    std::unordered_map<std::string, size_t> bmodelIndexByBatchKey;
    std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> allFaceVerticesByBModel;
    std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> unassignedVerticesByBModel;
    std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> missingAssetVerticesByBModel;
    std::unordered_map<size_t, bx::Vec3> previewOriginByBModel;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
        const EditorBModelSourceTransform sourceTransform = sourceTransformFromBModel(bmodel);
        const bx::Vec3 previewOrigin = {
            sourceTransform.originX,
            sourceTransform.originY,
            sourceTransform.originZ
        };
        previewOriginByBModel.emplace(bmodelIndex, previewOrigin);

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            const Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];
            std::vector<ProceduralPreviewVertex> allFaceVertices =
                buildProceduralBModelFaceVertices(outdoorGeometry, bmodelIndex, faceIndex, previewOrigin);

            if (!allFaceVertices.empty())
            {
                std::vector<ProceduralPreviewVertex> &allVertices = allFaceVerticesByBModel[bmodelIndex];

                if (allVertices.empty())
                {
                    allVertices.reserve(allFaceVertices.size() * 4);
                }

                allVertices.insert(allVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
            }

            if (face.textureName.empty())
            {
                std::vector<ProceduralPreviewVertex> &unassignedVertices = unassignedVerticesByBModel[bmodelIndex];

                if (unassignedVertices.empty())
                {
                    unassignedVertices.reserve(allFaceVertices.size() * 2);
                }

                unassignedVertices.insert(unassignedVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
                continue;
            }

            int textureWidth = 0;
            int textureHeight = 0;
            const std::optional<std::vector<uint8_t>> texturePixels =
                loadBitmapPixelsBgra(
                    assetFileSystem,
                    "Data/bitmaps",
                    face.textureName,
                    textureWidth,
                    textureHeight,
                    false,
                    bitmapLoadCache);

            if (!texturePixels || textureWidth <= 0 || textureHeight <= 0)
            {
                std::vector<ProceduralPreviewVertex> &missingVertices = missingAssetVerticesByBModel[bmodelIndex];

                if (missingVertices.empty())
                {
                    missingVertices.reserve(allFaceVertices.size() * 2);
                }

                missingVertices.insert(missingVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
                continue;
            }

            std::vector<TexturedPreviewVertex> faceVertices =
                buildTexturedBModelFaceVertices(outdoorGeometry, bmodelIndex, faceIndex, textureWidth, textureHeight);

            if (faceVertices.empty())
            {
                continue;
            }

            const std::string textureKey = toLowerCopy(face.textureName);
            const std::string batchKey = textureKey + "|" + std::to_string(bmodelIndex);
            textureNameByBatchKey[batchKey] = textureKey;
            bmodelIndexByBatchKey[batchKey] = bmodelIndex;
            std::vector<TexturedPreviewVertex> &batchVertices = batchVerticesByKey[batchKey];

            if (batchVertices.empty())
            {
                batchVertices.reserve(faceVertices.size() * 4);
            }

            batchVertices.insert(batchVertices.end(), faceVertices.begin(), faceVertices.end());
        }
    }

    for (const auto &[batchKey, vertices] : batchVerticesByKey)
    {
        if (vertices.empty())
        {
            continue;
        }

        const auto textureNameIt = textureNameByBatchKey.find(batchKey);
        const auto bmodelIndexIt = bmodelIndexByBatchKey.find(batchKey);

        if (textureNameIt == textureNameByBatchKey.end() || bmodelIndexIt == bmodelIndexByBatchKey.end())
        {
            continue;
        }

        const std::string &textureName = textureNameIt->second;
        const size_t bmodelIndex = bmodelIndexIt->second;

        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> texturePixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/bitmaps",
                textureName,
                textureWidth,
                textureHeight,
                false,
                bitmapLoadCache);

        if (!texturePixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        TexturedBatch batch = {};
        batch.vertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(TexturedPreviewVertex))),
            TexturedPreviewVertex::ms_layout);
        batch.textureHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(textureWidth),
            static_cast<uint16_t>(textureHeight),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_MIN_POINT
                | BGFX_SAMPLER_MAG_POINT
                | BGFX_SAMPLER_MIP_POINT,
            bgfx::copy(texturePixels->data(), static_cast<uint32_t>(texturePixels->size())));
        batch.vertexCount = static_cast<uint32_t>(vertices.size());
        batch.bmodelIndex = bmodelIndex;

        if (const auto originIt = previewOriginByBModel.find(bmodelIndex); originIt != previewOriginByBModel.end())
        {
            batch.objectOrigin = originIt->second;
        }

        if (bgfx::isValid(batch.vertexBufferHandle) && bgfx::isValid(batch.textureHandle))
        {
            m_bmodelTexturedBatches.push_back(batch);
        }
        else
        {
            if (bgfx::isValid(batch.vertexBufferHandle))
            {
                bgfx::destroy(batch.vertexBufferHandle);
            }

            if (bgfx::isValid(batch.textureHandle))
            {
                bgfx::destroy(batch.textureHandle);
            }
        }
    }

    const auto appendProceduralBatch =
        [](
            const std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> &verticesByBModel,
            const std::unordered_map<size_t, bx::Vec3> &originByBModel,
            std::vector<EditorOutdoorViewport::ProceduralBatch> &targetBatches)
    {
        for (const auto &[bmodelIndex, vertices] : verticesByBModel)
        {
            if (vertices.empty())
            {
                continue;
            }

            EditorOutdoorViewport::ProceduralBatch batch = {};
            batch.vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    vertices.data(),
                    static_cast<uint32_t>(vertices.size() * sizeof(EditorOutdoorViewport::ProceduralPreviewVertex))),
                EditorOutdoorViewport::ProceduralPreviewVertex::ms_layout);
            batch.vertexCount = static_cast<uint32_t>(vertices.size());
            batch.bmodelIndex = bmodelIndex;

            if (const auto originIt = originByBModel.find(bmodelIndex); originIt != originByBModel.end())
            {
                batch.objectOrigin = originIt->second;
            }

            if (bgfx::isValid(batch.vertexBufferHandle))
            {
                targetBatches.push_back(batch);
            }
        }
    };

    appendProceduralBatch(allFaceVerticesByBModel, previewOriginByBModel, m_bmodelAllFaceBatches);
    appendProceduralBatch(unassignedVerticesByBModel, previewOriginByBModel, m_bmodelUnassignedBatches);
    appendProceduralBatch(missingAssetVerticesByBModel, previewOriginByBModel, m_bmodelMissingAssetBatches);

}

void EditorOutdoorViewport::updateCamera(
    const EditorDocument &document,
    bool isHovered,
    bool isFocused,
    float deltaSeconds)
{
    const std::string cameraDocumentKey = documentCameraKey(document);

    if (cameraDocumentKey != m_cameraDocumentKey)
    {
        m_cameraDocumentKey = cameraDocumentKey;
        m_cameraInitializedForDocument = false;
        m_activeCameraFocus.active = false;
        m_activeGizmoDrag = {};
    }

    if (!m_cameraInitializedForDocument)
    {
        resetCameraToDocument(document);
    }

    if (m_activeCameraFocus.active)
    {
        m_activeCameraFocus.progressSeconds += deltaSeconds;
        const float normalizedT = std::clamp(
            m_activeCameraFocus.progressSeconds / std::max(m_activeCameraFocus.durationSeconds, 0.0001f),
            0.0f,
            1.0f);
        const float easedT = easeOutCubic(normalizedT);
        m_cameraPosition = vecLerp(m_activeCameraFocus.startPosition, m_activeCameraFocus.targetPosition, easedT);
        m_cameraYawRadians = wrapAngleRadians(
            m_activeCameraFocus.startYawRadians
            + shortestAngleDelta(m_activeCameraFocus.startYawRadians, m_activeCameraFocus.targetYawRadians) * easedT);
        m_cameraPitchRadians = lerpFloat(
            m_activeCameraFocus.startPitchRadians,
            m_activeCameraFocus.targetPitchRadians,
            easedT);

        if (normalizedT >= 1.0f)
        {
            m_activeCameraFocus.active = false;
        }
    }

    if (!isHovered && !isFocused)
    {
        return;
    }

    ImGuiIO &io = ImGui::GetIO();

    if (isHovered && ImGui::IsMouseDown(ImGuiMouseButton_Right))
    {
        m_activeCameraFocus.active = false;
        m_cameraYawRadians += io.MouseDelta.x * CameraMouseSensitivity;
        m_cameraPitchRadians -= io.MouseDelta.y * CameraMouseSensitivity;
        m_cameraPitchRadians = std::clamp(m_cameraPitchRadians, CameraMinPitchRadians, CameraMaxPitchRadians);
    }

    if (!ImGui::IsMouseDown(ImGuiMouseButton_Right))
    {
        return;
    }

    const float moveSpeed =
        CameraMoveSpeed
        * ((ImGui::IsKeyDown(ImGuiKey_LeftShift) || ImGui::IsKeyDown(ImGuiKey_RightShift))
               ? CameraFastMoveSpeedMultiplier
               : 1.0f)
        * deltaSeconds;
    const bx::Vec3 forward = {
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    };
    const bx::Vec3 right = {
        std::cos(m_cameraYawRadians),
        -std::sin(m_cameraYawRadians),
        0.0f
    };

    if (ImGui::IsKeyDown(ImGuiKey_W))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.x += forward.x * moveSpeed;
        m_cameraPosition.y += forward.y * moveSpeed;
        m_cameraPosition.z += forward.z * moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_S))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.x -= forward.x * moveSpeed;
        m_cameraPosition.y -= forward.y * moveSpeed;
        m_cameraPosition.z -= forward.z * moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_A))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.x -= right.x * moveSpeed;
        m_cameraPosition.y -= right.y * moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_D))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.x += right.x * moveSpeed;
        m_cameraPosition.y += right.y * moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_Q))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.z -= moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_E))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.z += moveSpeed;
    }
}

void EditorOutdoorViewport::ensureImportedModelPreview(const EditorSession &session)
{
    if (!m_importedModelPreviewRequest || !session.hasDocument() || session.document().kind() != EditorDocument::Kind::Outdoor)
    {
        destroyImportedModelPreview();
        return;
    }

    const ImportedModelPreviewRequest &request = *m_importedModelPreviewRequest;
    const EditorDocument &document = session.document();
    const std::string trimmedPath = request.sourcePath;

    if (trimmedPath.empty() || request.importScale <= 0.0f)
    {
        destroyImportedModelPreview();
        return;
    }

    std::string placementKey = request.sourcePath
        + "|mesh=" + request.sourceMeshName
        + "|scale=" + std::to_string(request.importScale)
        + "|merge=" + std::to_string(request.mergeCoplanarFaces ? 1 : 0)
        + "|target=" + std::to_string(static_cast<int>(request.targetMode))
        + "|doc=" + documentGeometryKey(document);
    std::optional<Game::OutdoorBModel> previewBModel;

    if (request.targetMode == ImportedModelPreviewRequest::TargetMode::ReplaceSelectedBModel)
    {
        const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();

        if (request.bmodelIndex >= outdoorGeometry.bmodels.size())
        {
            destroyImportedModelPreview();
            return;
        }

        ImportedModel importedModel = {};
        std::string errorMessage;

        if (!loadImportedModelFromFile(
                std::filesystem::absolute(trimmedPath),
                importedModel,
                errorMessage,
                request.sourceMeshName,
                request.mergeCoplanarFaces))
        {
            destroyImportedModelPreview();
            return;
        }

        const Game::OutdoorBModel &placementTemplate = outdoorGeometry.bmodels[request.bmodelIndex];
        const std::optional<EditorBModelSourceTransform> sourceTransform =
            document.outdoorBModelSourceTransform(request.bmodelIndex);
        previewBModel = buildImportedPreviewBModel(
            importedModel,
            request.importScale,
            &placementTemplate,
            sourceTransform ? &*sourceTransform : nullptr,
            nullptr);
        placementKey += "|bmodel=" + std::to_string(request.bmodelIndex);
    }
    else
    {
        ImportedModel importedModel = {};
        std::string errorMessage;

        if (!loadImportedModelFromFile(
                std::filesystem::absolute(trimmedPath),
                importedModel,
                errorMessage,
                request.sourceMeshName,
                request.mergeCoplanarFaces))
        {
            destroyImportedModelPreview();
            return;
        }

        bx::Vec3 floorPoint = {0.0f, 0.0f, 0.0f};
        const float sampleMouseX =
            m_isHovered
            ? m_lastMouseX
            : static_cast<float>(m_viewportX) + static_cast<float>(m_viewportWidth) * 0.5f;
        const float sampleMouseY =
            m_isHovered
            ? m_lastMouseY
            : static_cast<float>(m_viewportY) + static_cast<float>(m_viewportHeight) * 0.5f;

        if (!sampleTerrainWorldPosition(document, sampleMouseX, sampleMouseY, floorPoint))
        {
            destroyImportedModelPreview();
            return;
        }

        if (m_snapEnabled)
        {
            const int snapStep = std::max(m_snapStep, 1);
            floorPoint.x =
                static_cast<float>(static_cast<int>(std::lround(floorPoint.x / static_cast<float>(snapStep))) * snapStep);
            floorPoint.y =
                static_cast<float>(static_cast<int>(std::lround(floorPoint.y / static_cast<float>(snapStep))) * snapStep);
            floorPoint.z =
                static_cast<float>(static_cast<int>(std::lround(floorPoint.z / static_cast<float>(snapStep))) * snapStep);
        }

        previewBModel = buildImportedPreviewBModel(importedModel, request.importScale, nullptr, nullptr, &floorPoint);
        placementKey += "|floor=" + std::to_string(static_cast<int>(std::lround(floorPoint.x)))
            + "," + std::to_string(static_cast<int>(std::lround(floorPoint.y)))
            + "," + std::to_string(static_cast<int>(std::lround(floorPoint.z)));
    }

    if (!previewBModel)
    {
        destroyImportedModelPreview();
        return;
    }

    if (placementKey == m_importedModelPreviewKey && bgfx::isValid(m_importedModelPreviewBatch.vertexBufferHandle))
    {
        return;
    }

    destroyImportedModelPreview();
    const bx::Vec3 previewOrigin = {
        static_cast<float>(previewBModel->boundingCenterX),
        static_cast<float>(previewBModel->boundingCenterY),
        static_cast<float>(previewBModel->boundingCenterZ)
    };
    std::vector<ProceduralPreviewVertex> previewVertices;

    for (size_t faceIndex = 0; faceIndex < previewBModel->faces.size(); ++faceIndex)
    {
        std::vector<ProceduralPreviewVertex> faceVertices =
            buildProceduralBModelFaceVertices(*previewBModel, faceIndex, previewOrigin);
        previewVertices.insert(previewVertices.end(), faceVertices.begin(), faceVertices.end());
    }

    if (previewVertices.empty())
    {
        return;
    }

    m_importedModelPreviewBatch.vertexBufferHandle = bgfx::createVertexBuffer(
        bgfx::copy(
            previewVertices.data(),
            static_cast<uint32_t>(previewVertices.size() * sizeof(ProceduralPreviewVertex))),
        ProceduralPreviewVertex::ms_layout);
    m_importedModelPreviewBatch.vertexCount = static_cast<uint32_t>(previewVertices.size());
    m_importedModelPreviewBatch.objectOrigin = previewOrigin;
    m_importedModelPreviewKey = placementKey;
}

void EditorOutdoorViewport::resetCameraToDocument(const EditorDocument &document)
{
    (void) document;
    m_cameraPosition = {0.0f, 0.0f, 5000.0f};
    m_cameraYawRadians = -300.0f * bx::kPi / 180.0f;
    m_cameraPitchRadians = -0.35f;
    m_cameraInitializedForDocument = true;
}

void EditorOutdoorViewport::tryPick(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!leftMouseClicked || !m_isHovered || !session.hasDocument())
    {
        return;
    }

    const float localMouseX = mouseX - static_cast<float>(m_viewportX);
    const float localMouseY = mouseY - static_cast<float>(m_viewportY);
    const bx::Vec3 forward = vecNormalize({
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    });
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    const bx::Vec3 cameraRight = vecNormalize(vecCross(forward, worldUp));
    const bx::Vec3 cameraUp = vecNormalize(vecCross(cameraRight, forward));
    float bestScore = FLT_MAX;
    EditorSelectionKind bestKind = EditorSelectionKind::None;
    size_t bestIndex = 0;

    for (const MarkerCandidate &candidate : m_markerCandidates)
    {
        float projectedX = 0.0f;
        float projectedY = 0.0f;
        float clipW = 0.0f;

        if (!projectWorldPoint(
                candidate.worldPosition,
                m_viewProjectionMatrix,
                m_viewportWidth,
                m_viewportHeight,
                projectedX,
                projectedY,
                clipW))
        {
            continue;
        }

        bool hit = false;
        float score = FLT_MAX;

        if (candidate.hasBillboardBounds)
        {
            const float halfWidth = candidate.billboardWorldWidth * 0.5f;
            const float halfHeight = candidate.billboardWorldHeight * 0.5f;
            const bx::Vec3 right = vecScale(cameraRight, halfWidth);
            const bx::Vec3 up = vecScale(cameraUp, halfHeight);
            const std::array<bx::Vec3, 4> corners = {{
                {
                    candidate.worldPosition.x - right.x - up.x,
                    candidate.worldPosition.y - right.y - up.y,
                    candidate.worldPosition.z - right.z - up.z
                },
                {
                    candidate.worldPosition.x - right.x + up.x,
                    candidate.worldPosition.y - right.y + up.y,
                    candidate.worldPosition.z - right.z + up.z
                },
                {
                    candidate.worldPosition.x + right.x + up.x,
                    candidate.worldPosition.y + right.y + up.y,
                    candidate.worldPosition.z + right.z + up.z
                },
                {
                    candidate.worldPosition.x + right.x - up.x,
                    candidate.worldPosition.y + right.y - up.y,
                    candidate.worldPosition.z + right.z - up.z
                }
            }};

            float minX = FLT_MAX;
            float minY = FLT_MAX;
            float maxX = -FLT_MAX;
            float maxY = -FLT_MAX;
            bool validBounds = true;

            for (const bx::Vec3 &corner : corners)
            {
                float cornerX = 0.0f;
                float cornerY = 0.0f;
                float cornerW = 0.0f;

                if (!projectWorldPoint(
                        corner,
                        m_viewProjectionMatrix,
                        m_viewportWidth,
                        m_viewportHeight,
                        cornerX,
                        cornerY,
                        cornerW))
                {
                    validBounds = false;
                    break;
                }

                minX = std::min(minX, cornerX);
                minY = std::min(minY, cornerY);
                maxX = std::max(maxX, cornerX);
                maxY = std::max(maxY, cornerY);
            }

            if (validBounds)
            {
                constexpr float hitPaddingPixels = 4.0f;
                minX -= hitPaddingPixels;
                minY -= hitPaddingPixels;
                maxX += hitPaddingPixels;
                maxY += hitPaddingPixels;

                if (localMouseX >= minX && localMouseX <= maxX && localMouseY >= minY && localMouseY <= maxY)
                {
                    const float centerX = (minX + maxX) * 0.5f;
                    const float centerY = (minY + maxY) * 0.5f;
                    const float deltaX = centerX - localMouseX;
                    const float deltaY = centerY - localMouseY;
                    hit = true;
                    score = deltaX * deltaX + deltaY * deltaY + clipW * 0.01f;
                }
            }
        }

        if (!hit)
        {
            const float deltaX = projectedX - localMouseX;
            const float deltaY = projectedY - localMouseY;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY;
            const float threshold = candidate.pickRadiusPixels * candidate.pickRadiusPixels;

            if (distanceSquared > threshold)
            {
                continue;
            }

            hit = true;
            score = distanceSquared + clipW * 0.01f;
        }

        if (hit && score < bestScore)
        {
            bestScore = score;
            bestKind = candidate.selectionKind;
            bestIndex = candidate.selectionIndex;
        }
    }

    if (bestKind != EditorSelectionKind::None)
    {
        session.select(bestKind, bestIndex);
        return;
    }

    if (m_placementKind != EditorSelectionKind::None)
    {
        return;
    }

    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection))
    {
        return;
    }

    const EditorDocument &document = session.document();
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const bx::Vec3 segmentEnd = {
        rayOrigin.x + rayDirection.x * CameraFarPlane,
        rayOrigin.y + rayDirection.y * CameraFarPlane,
        rayOrigin.z + rayDirection.z * CameraFarPlane
    };
    float bestIntersectionFactor = std::numeric_limits<float>::max();
    size_t bestBModelIndex = 0;
    bool foundBModelHit = false;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            Game::OutdoorFaceGeometryData geometry = {};

            if (!Game::buildOutdoorFaceGeometry(bmodel, bmodelIndex, bmodel.faces[faceIndex], faceIndex, geometry))
            {
                continue;
            }

            float intersectionFactor = 0.0f;
            bx::Vec3 intersectionPoint = {0.0f, 0.0f, 0.0f};

            if (!Game::intersectOutdoorSegmentWithFace(
                    geometry,
                    rayOrigin,
                    segmentEnd,
                    intersectionFactor,
                    intersectionPoint))
            {
                continue;
            }

            if (!foundBModelHit || intersectionFactor < bestIntersectionFactor)
            {
                bestIntersectionFactor = intersectionFactor;
                bestBModelIndex = bmodelIndex;
                foundBModelHit = true;
            }
        }
    }

    if (foundBModelHit)
    {
        session.select(EditorSelectionKind::BModel, bestBModelIndex);
    }
}

void EditorOutdoorViewport::finishTerrainStroke(EditorSession &session)
{
    if (m_activeTerrainPaint.active)
    {
        if (session.hasDocument()
            && session.terrainPaintEnabled()
            && session.terrainPaintMode() == EditorTerrainPaintMode::Rectangle
            && m_activeTerrainPaint.anchorCellX != std::numeric_limits<int>::min()
            && m_activeTerrainPaint.lastCellX != std::numeric_limits<int>::min())
        {
            Game::OutdoorMapData &outdoorGeometry = session.document().mutableOutdoorGeometry();

            if (applyTerrainPaintRectangle(
                    outdoorGeometry,
                    m_activeTerrainPaint.anchorCellX,
                    m_activeTerrainPaint.anchorCellY,
                    m_activeTerrainPaint.lastCellX,
                    m_activeTerrainPaint.lastCellY,
                    session.terrainPaintTileId()))
            {
                session.document().setDirty(true);
                session.document().touchSceneRevision();
                m_geometryKey.clear();
                m_activeTerrainPaint.mutated = true;
            }
        }

        if (m_activeTerrainPaint.mutated)
        {
            session.noteDocumentMutated({});
        }

        m_activeTerrainPaint = {};
    }

    if (m_activeTerrainSculpt.active)
    {
        if (session.hasDocument()
            && session.terrainSculptEnabled()
            && session.terrainSculptMode() == EditorTerrainSculptMode::Ramp
            && m_activeTerrainSculpt.anchorSampleX != std::numeric_limits<int>::min()
            && m_activeTerrainSculpt.lastSampleX != std::numeric_limits<int>::min())
        {
            Game::OutdoorMapData &outdoorGeometry = session.document().mutableOutdoorGeometry();
            const size_t endSampleIndex =
                flattenTerrainCellIndex(m_activeTerrainSculpt.lastSampleX, m_activeTerrainSculpt.lastSampleY);

            if (endSampleIndex < outdoorGeometry.heightMap.size()
                && applyTerrainRampBrush(
                    outdoorGeometry,
                    m_activeTerrainSculpt.anchorSampleX,
                    m_activeTerrainSculpt.anchorSampleY,
                    m_activeTerrainSculpt.lastSampleX,
                    m_activeTerrainSculpt.lastSampleY,
                    m_activeTerrainSculpt.anchorHeight,
                    outdoorGeometry.heightMap[endSampleIndex],
                    std::max(session.terrainSculptRadius(), 0),
                    std::max(session.terrainSculptStrength(), 1),
                    session.terrainSculptFalloffMode()))
            {
                recalculateOutdoorHeightRange(outdoorGeometry);
                session.document().setDirty(true);
                session.document().touchSceneRevision();
                m_geometryKey.clear();
                m_activeTerrainSculpt.mutated = true;
            }
        }

        if (m_activeTerrainSculpt.mutated)
        {
            session.noteDocumentMutated({});
        }

        m_activeTerrainSculpt = {};
    }
}

bool EditorOutdoorViewport::trySelectTerrainCell(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!m_isHovered || m_placementKind != EditorSelectionKind::Terrain || !session.hasDocument())
    {
        m_hoverTerrainValid = false;
        finishTerrainStroke(session);
        return false;
    }

    const ImGuiIO &io = ImGui::GetIO();
    const bool leftMouseDown = io.MouseDown[0];

    if (!leftMouseDown && (m_activeTerrainPaint.active || m_activeTerrainSculpt.active))
    {
        finishTerrainStroke(session);
    }

    bx::Vec3 worldPosition = {0.0f, 0.0f, 0.0f};

    if (!sampleTerrainWorldPosition(session.document(), mouseX, mouseY, worldPosition))
    {
        m_hoverTerrainValid = false;
        return false;
    }

    const int cellX = std::clamp(
        static_cast<int>(std::floor(Game::outdoorWorldToGridXFloat(worldPosition.x))),
        0,
        Game::OutdoorMapData::TerrainWidth - 1);
    const int cellY = std::clamp(
        static_cast<int>(std::floor(Game::outdoorWorldToGridYFloat(worldPosition.y))),
        0,
        Game::OutdoorMapData::TerrainHeight - 1);
    const int sampleX = std::clamp(
        static_cast<int>(std::round(Game::outdoorWorldToGridXFloat(worldPosition.x))),
        0,
        Game::OutdoorMapData::TerrainWidth - 1);
    const int sampleY = std::clamp(
        static_cast<int>(std::round(Game::outdoorWorldToGridYFloat(worldPosition.y))),
        0,
        Game::OutdoorMapData::TerrainHeight - 1);
    m_hoverTerrainValid = true;
    m_hoverTerrainCellX = cellX;
    m_hoverTerrainCellY = cellY;
    const size_t flatIndex = flattenTerrainCellIndex(cellX, cellY);

    const bool sculptEnabled = session.terrainSculptEnabled();
    const bool paintEnabled = session.terrainPaintEnabled() && !sculptEnabled;
    const EditorTerrainPaintMode paintMode = session.terrainPaintMode();
    Game::OutdoorMapData &outdoorGeometry = session.document().mutableOutdoorGeometry();

    if (io.KeyAlt
        && leftMouseClicked
        && sculptEnabled
        && session.terrainSculptMode() == EditorTerrainSculptMode::Flatten)
    {
        const size_t sampleIndex = flattenTerrainCellIndex(sampleX, sampleY);

        if (sampleIndex < outdoorGeometry.heightMap.size())
        {
            session.setTerrainFlattenTargetMode(EditorTerrainFlattenTargetMode::Sampled);
            session.setTerrainFlattenSampledTargetHeight(outdoorGeometry.heightMap[sampleIndex]);
            session.select(EditorSelectionKind::Terrain, flatIndex);
        }

        return true;
    }

    if ((!paintEnabled && !sculptEnabled) || !leftMouseDown)
    {
        if (leftMouseClicked)
        {
            session.select(EditorSelectionKind::Terrain, flatIndex);
        }

        return leftMouseClicked;
    }

    session.select(EditorSelectionKind::Terrain, flatIndex);

    if (paintEnabled && paintMode == EditorTerrainPaintMode::Fill)
    {
        if (!leftMouseClicked)
        {
            return true;
        }

        session.captureUndoSnapshot();

        if (applyTerrainPaintFill(outdoorGeometry, cellX, cellY, session.terrainPaintTileId()))
        {
            session.document().setDirty(true);
            session.document().touchSceneRevision();
            m_geometryKey.clear();
            session.noteDocumentMutated({});
        }

        return true;
    }

    if (sculptEnabled)
    {
        if (!m_activeTerrainSculpt.active)
        {
            if (!leftMouseClicked)
            {
                return true;
            }

            session.captureUndoSnapshot();
            m_activeTerrainSculpt.active = true;
            m_activeTerrainSculpt.anchorSampleX = sampleX;
            m_activeTerrainSculpt.anchorSampleY = sampleY;
            const size_t anchorSampleIndex = flattenTerrainCellIndex(sampleX, sampleY);
            m_activeTerrainSculpt.anchorHeight =
                anchorSampleIndex < outdoorGeometry.heightMap.size() ? outdoorGeometry.heightMap[anchorSampleIndex] : 0;
            m_activeTerrainSculpt.lastSampleX = std::numeric_limits<int>::min();
            m_activeTerrainSculpt.lastSampleY = std::numeric_limits<int>::min();
            m_activeTerrainSculpt.hasFlattenTargetHeight = false;
            m_activeTerrainSculpt.mutated = false;
        }

        if (sampleX == m_activeTerrainSculpt.lastSampleX && sampleY == m_activeTerrainSculpt.lastSampleY)
        {
            return true;
        }

        const int radius = std::max(session.terrainSculptRadius(), 0);
        const int strength = std::max(session.terrainSculptStrength(), 1);
        bool mutated = false;
        const EditorTerrainFalloffMode falloffMode = session.terrainSculptFalloffMode();
        const EditorTerrainSculptMode sculptMode = session.terrainSculptMode();

        if (sculptMode == EditorTerrainSculptMode::Flatten && !m_activeTerrainSculpt.hasFlattenTargetHeight)
        {
            if (session.terrainFlattenTargetMode() == EditorTerrainFlattenTargetMode::Numeric)
            {
                m_activeTerrainSculpt.flattenTargetHeight = session.terrainFlattenTargetHeight();
                m_activeTerrainSculpt.hasFlattenTargetHeight = true;
            }
            else if (session.hasTerrainFlattenSampledTarget())
            {
                m_activeTerrainSculpt.flattenTargetHeight = session.terrainFlattenTargetHeight();
                m_activeTerrainSculpt.hasFlattenTargetHeight = true;
            }
            else
            {
                const size_t flattenTargetIndex = flattenTerrainCellIndex(sampleX, sampleY);

                if (flattenTargetIndex < outdoorGeometry.heightMap.size())
                {
                    m_activeTerrainSculpt.flattenTargetHeight = outdoorGeometry.heightMap[flattenTargetIndex];
                    m_activeTerrainSculpt.hasFlattenTargetHeight = true;
                    session.setTerrainFlattenSampledTargetHeight(m_activeTerrainSculpt.flattenTargetHeight);
                }
            }
        }

        if (sculptMode == EditorTerrainSculptMode::Ramp)
        {
            m_activeTerrainSculpt.lastSampleX = sampleX;
            m_activeTerrainSculpt.lastSampleY = sampleY;
            return true;
        }

        if (m_activeTerrainSculpt.lastSampleX == std::numeric_limits<int>::min())
        {
            if (sculptMode == EditorTerrainSculptMode::Flatten)
            {
                mutated = applyTerrainFlattenBrush(
                    outdoorGeometry,
                    sampleX,
                    sampleY,
                    radius,
                    strength,
                    m_activeTerrainSculpt.flattenTargetHeight,
                    falloffMode);
            }
            else if (sculptMode == EditorTerrainSculptMode::Smooth)
            {
                mutated = applyTerrainSmoothBrush(
                    outdoorGeometry,
                    sampleX,
                    sampleY,
                    radius,
                    strength,
                    falloffMode);
            }
            else if (sculptMode == EditorTerrainSculptMode::Noise)
            {
                mutated = applyTerrainNoiseBrush(
                    outdoorGeometry,
                    sampleX,
                    sampleY,
                    radius,
                    strength,
                    falloffMode);
            }
            else
            {
                const int signedStrength = sculptMode == EditorTerrainSculptMode::Lower ? -strength : strength;
                mutated = applyTerrainSculptBrush(
                    outdoorGeometry,
                    sampleX,
                    sampleY,
                    radius,
                    signedStrength,
                    falloffMode);
            }
        }
        else
        {
            rasterizeTerrainLine(
                m_activeTerrainSculpt.lastSampleX,
                m_activeTerrainSculpt.lastSampleY,
                sampleX,
                sampleY,
                [&](int stepX, int stepY)
                {
                    if (sculptMode == EditorTerrainSculptMode::Flatten)
                    {
                        mutated = applyTerrainFlattenBrush(
                            outdoorGeometry,
                            stepX,
                            stepY,
                            radius,
                            strength,
                            m_activeTerrainSculpt.flattenTargetHeight,
                            falloffMode)
                            || mutated;
                    }
                    else if (sculptMode == EditorTerrainSculptMode::Smooth)
                    {
                        mutated = applyTerrainSmoothBrush(
                            outdoorGeometry,
                            stepX,
                            stepY,
                            radius,
                            strength,
                            falloffMode)
                            || mutated;
                    }
                    else if (sculptMode == EditorTerrainSculptMode::Noise)
                    {
                        mutated = applyTerrainNoiseBrush(
                            outdoorGeometry,
                            stepX,
                            stepY,
                            radius,
                            strength,
                            falloffMode)
                            || mutated;
                    }
                    else
                    {
                        const int signedStrength = sculptMode == EditorTerrainSculptMode::Lower ? -strength : strength;
                        mutated = applyTerrainSculptBrush(
                            outdoorGeometry,
                            stepX,
                            stepY,
                            radius,
                            signedStrength,
                            falloffMode)
                            || mutated;
                    }
                });
        }

        if (mutated)
        {
            recalculateOutdoorHeightRange(outdoorGeometry);
            session.document().setDirty(true);
            session.document().touchSceneRevision();
            m_geometryKey.clear();
            m_activeTerrainSculpt.mutated = true;
        }

        m_activeTerrainSculpt.lastSampleX = sampleX;
        m_activeTerrainSculpt.lastSampleY = sampleY;
        return true;
    }

    if (!m_activeTerrainPaint.active)
    {
        if (!leftMouseClicked)
        {
            return true;
        }

        session.captureUndoSnapshot();
        m_activeTerrainPaint.active = true;
        m_activeTerrainPaint.lastFlatIndex = std::numeric_limits<size_t>::max();
        m_activeTerrainPaint.anchorCellX = cellX;
        m_activeTerrainPaint.anchorCellY = cellY;
        m_activeTerrainPaint.lastCellX = cellX;
        m_activeTerrainPaint.lastCellY = cellY;
        m_activeTerrainPaint.mutated = false;
    }

    if (paintMode == EditorTerrainPaintMode::Rectangle)
    {
        m_activeTerrainPaint.lastCellX = cellX;
        m_activeTerrainPaint.lastCellY = cellY;
        return true;
    }

    const uint8_t tileId = session.terrainPaintTileId();
    const int brushRadius = std::max(session.terrainPaintRadius(), 0);
    bool mutated = false;

    if (paintMode == EditorTerrainPaintMode::Brush)
    {
        if (m_activeTerrainPaint.lastCellX == std::numeric_limits<int>::min())
        {
            mutated = applyTerrainPaintBrush(
                outdoorGeometry,
                cellX,
                cellY,
                brushRadius,
                tileId,
                session.terrainPaintEdgeNoise());
        }
        else
        {
            rasterizeTerrainLine(
                m_activeTerrainPaint.lastCellX,
                m_activeTerrainPaint.lastCellY,
                cellX,
                cellY,
                [&](int stepX, int stepY)
                {
                    mutated = applyTerrainPaintBrush(
                                  outdoorGeometry,
                                  stepX,
                                  stepY,
                                  brushRadius,
                                  tileId,
                                  session.terrainPaintEdgeNoise())
                        || mutated;
                });
        }
    }
    else
    {
        if (flatIndex < outdoorGeometry.tileMap.size() && outdoorGeometry.tileMap[flatIndex] != tileId)
        {
            outdoorGeometry.tileMap[flatIndex] = tileId;
            recalculateOutdoorTileUsage(outdoorGeometry);
            mutated = true;
        }
    }

    if (mutated)
    {
        session.document().setDirty(true);
        session.document().touchSceneRevision();
        m_geometryKey.clear();
        m_activeTerrainPaint.mutated = true;
    }

    m_activeTerrainPaint.lastFlatIndex = flatIndex;
    m_activeTerrainPaint.lastCellX = cellX;
    m_activeTerrainPaint.lastCellY = cellY;
    return true;
}

bool EditorOutdoorViewport::trySelectInteractiveFace(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!leftMouseClicked
        || !m_isHovered
        || m_placementKind != EditorSelectionKind::InteractiveFace
        || !session.hasDocument())
    {
        return false;
    }

    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection))
    {
        return false;
    }

    const EditorDocument &document = session.document();
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const bx::Vec3 segmentEnd = {
        rayOrigin.x + rayDirection.x * CameraFarPlane,
        rayOrigin.y + rayDirection.y * CameraFarPlane,
        rayOrigin.z + rayDirection.z * CameraFarPlane
    };

    struct FacePickCandidate
    {
        size_t bmodelIndex = 0;
        size_t faceIndex = 0;
        float score = std::numeric_limits<float>::max();
        float facingScore = -std::numeric_limits<float>::max();
        bool frontFacing = false;
    };

    std::vector<FacePickCandidate> pickCandidates;
    constexpr float FacePickDistanceEpsilon = 0.001f;
    constexpr float FacePickFacingEpsilon = 0.01f;
    constexpr float FaceFrontFacingThreshold = 0.05f;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            Game::OutdoorFaceGeometryData geometry = {};

            if (!Game::buildOutdoorFaceGeometry(bmodel, bmodelIndex, bmodel.faces[faceIndex], faceIndex, geometry))
            {
                continue;
            }

            float intersectionFactor = 0.0f;
            bx::Vec3 intersectionPoint = {0.0f, 0.0f, 0.0f};

            if (!Game::intersectOutdoorSegmentWithFace(
                    geometry,
                    rayOrigin,
                    segmentEnd,
                    intersectionFactor,
                    intersectionPoint))
            {
                continue;
            }

            const float facingScore = -(geometry.normal.x * rayDirection.x
                + geometry.normal.y * rayDirection.y
                + geometry.normal.z * rayDirection.z);
            pickCandidates.push_back({
                bmodelIndex,
                faceIndex,
                intersectionFactor,
                facingScore,
                facingScore > FaceFrontFacingThreshold});
        }
    }

    if (pickCandidates.empty())
    {
        const float localMouseX = mouseX - static_cast<float>(m_viewportX);
        const float localMouseY = mouseY - static_cast<float>(m_viewportY);

        for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
        {
            const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

            for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
            {
                Game::OutdoorFaceGeometryData geometry = {};

                if (!Game::buildOutdoorFaceGeometry(bmodel, bmodelIndex, bmodel.faces[faceIndex], faceIndex, geometry))
                {
                    continue;
                }

                std::vector<ScreenPoint> projectedVertices;
                projectedVertices.reserve(geometry.vertices.size());
                float accumulatedClipW = 0.0f;
                bool allProjected = true;

                for (const bx::Vec3 &vertex : geometry.vertices)
                {
                    float projectedX = 0.0f;
                    float projectedY = 0.0f;
                    float clipW = 0.0f;

                    if (!projectWorldPoint(
                            vertex,
                            m_viewProjectionMatrix,
                            m_viewportWidth,
                            m_viewportHeight,
                            projectedX,
                            projectedY,
                            clipW))
                    {
                        allProjected = false;
                        break;
                    }

                    projectedVertices.push_back({projectedX, projectedY});
                    accumulatedClipW += clipW;
                }

                if (!allProjected || !isPointInsideOrNearScreenPolygon(localMouseX, localMouseY, projectedVertices, 6.0f))
                {
                    continue;
                }

                const float averageClipW = accumulatedClipW / static_cast<float>(projectedVertices.size());
                const float facingScore = -(geometry.normal.x * rayDirection.x
                    + geometry.normal.y * rayDirection.y
                    + geometry.normal.z * rayDirection.z);
                pickCandidates.push_back({
                    bmodelIndex,
                    faceIndex,
                    averageClipW,
                    facingScore,
                    facingScore > FaceFrontFacingThreshold});
            }
        }

        if (pickCandidates.empty())
        {
            return false;
        }
    }

    const bool hasFrontFacingCandidate = std::any_of(
        pickCandidates.begin(),
        pickCandidates.end(),
        [](const FacePickCandidate &candidate)
        {
            return candidate.frontFacing;
        });

    std::erase_if(
        pickCandidates,
        [hasFrontFacingCandidate](const FacePickCandidate &candidate)
        {
            return hasFrontFacingCandidate && !candidate.frontFacing;
        });

    std::sort(
        pickCandidates.begin(),
        pickCandidates.end(),
        [](const FacePickCandidate &left, const FacePickCandidate &right)
        {
            if (std::fabs(left.score - right.score) > FacePickDistanceEpsilon)
            {
                return left.score < right.score;
            }

            if (std::fabs(left.facingScore - right.facingScore) > FacePickFacingEpsilon)
            {
                return left.facingScore > right.facingScore;
            }

            if (left.bmodelIndex != right.bmodelIndex)
            {
                return left.bmodelIndex < right.bmodelIndex;
            }

            return left.faceIndex < right.faceIndex;
        });

    std::vector<size_t> flatCandidates;
    flatCandidates.reserve(pickCandidates.size());

    for (const FacePickCandidate &candidate : pickCandidates)
    {
        flatCandidates.push_back(
            flattenedOutdoorFaceIndex(outdoorGeometry, candidate.bmodelIndex, candidate.faceIndex));
    }

    const bool samePickRegion =
        std::fabs(mouseX - m_lastFacePickMouseX) <= 10.0f
        && std::fabs(mouseY - m_lastFacePickMouseY) <= 10.0f
        && !ImGui::GetIO().KeyCtrl;

    size_t selectedCandidateIndex = 0;

    if (samePickRegion
        && session.selection().kind == EditorSelectionKind::InteractiveFace
        && !flatCandidates.empty())
    {
        const auto currentSelectionIterator = std::find(
            flatCandidates.begin(),
            flatCandidates.end(),
            session.selection().index);

        if (currentSelectionIterator != flatCandidates.end())
        {
            selectedCandidateIndex =
                (static_cast<size_t>(std::distance(flatCandidates.begin(), currentSelectionIterator)) + 1)
                % flatCandidates.size();
        }
    }

    m_lastFacePickMouseX = mouseX;
    m_lastFacePickMouseY = mouseY;
    m_lastFacePickCandidates = flatCandidates;
    m_lastFacePickCycleIndex = selectedCandidateIndex;
    const size_t flatIndex = flatCandidates[selectedCandidateIndex];

    if (ImGui::GetIO().KeyCtrl)
    {
        session.toggleInteractiveFaceSelection(flatIndex);
    }
    else
    {
        session.replaceInteractiveFaceSelection(flatIndex);
    }

    return true;
}

bool EditorOutdoorViewport::tryPlaceObject(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!m_isHovered || m_placementKind == EditorSelectionKind::None || !session.hasDocument())
    {
        m_pendingEntityPlacementPreview.reset();
        m_pendingSpriteObjectPlacementPreview.reset();
        return false;
    }

    if (m_placementKind != EditorSelectionKind::BModel
        && m_placementKind != EditorSelectionKind::SpriteObject
        && m_placementKind != EditorSelectionKind::Entity
        && !leftMouseClicked)
    {
        m_pendingEntityPlacementPreview.reset();
        m_pendingSpriteObjectPlacementPreview.reset();
        return false;
    }

    bx::Vec3 worldPosition = {0.0f, 0.0f, 0.0f};

    const bool sampledWorldPosition =
        m_placementKind == EditorSelectionKind::BModel
            ? sampleTerrainWorldPosition(session.document(), mouseX, mouseY, worldPosition)
            : samplePlacementWorldPosition(session.document(), mouseX, mouseY, worldPosition);

    if (!sampledWorldPosition)
    {
        m_pendingEntityPlacementPreview.reset();
        m_pendingSpriteObjectPlacementPreview.reset();
        return false;
    }

    if (m_snapEnabled)
    {
        const int snapStep = std::max(m_snapStep, 1);
        const auto snapValue = [snapStep](float value)
        {
            return static_cast<float>(
                static_cast<int>(std::lround(value / static_cast<float>(snapStep))) * snapStep);
        };

        worldPosition.x = snapValue(worldPosition.x);
        worldPosition.y = snapValue(worldPosition.y);
        worldPosition.z = snapValue(worldPosition.z);
    }

    if (m_placementKind == EditorSelectionKind::BModel)
    {
        const EditorSelection selection = session.selection();

        if (selection.kind != EditorSelectionKind::BModel)
        {
            return false;
        }

        const std::optional<bx::Vec3> targetCenter =
            bmodelPlacementCenterForFloorPoint(session.document().outdoorGeometry(), selection.index, worldPosition);

        if (!targetCenter)
        {
            return false;
        }

        if (setSelectedWorldPosition(session, *targetCenter))
        {
            session.document().setDirty(true);
            session.document().touchSceneRevision();
            m_geometryKey.clear();
        }

        if (leftMouseClicked)
        {
            session.noteDocumentMutated("Placed imported bmodel");
            m_placementKind = EditorSelectionKind::None;
            return true;
        }

        return false;
    }

    if (m_placementKind == EditorSelectionKind::SpriteObject)
    {
        m_pendingSpriteObjectPlacementPreview = PendingSpriteObjectPlacementPreview{
            static_cast<int>(std::lround(worldPosition.x)),
            static_cast<int>(std::lround(worldPosition.y)),
            static_cast<int>(std::lround(worldPosition.z))
        };
    }
    else
    {
        m_pendingSpriteObjectPlacementPreview.reset();
    }

    if (m_placementKind == EditorSelectionKind::Entity)
    {
        m_pendingEntityPlacementPreview = PendingEntityPlacementPreview{
            static_cast<int>(std::lround(worldPosition.x)),
            static_cast<int>(std::lround(worldPosition.y)),
            static_cast<int>(std::lround(worldPosition.z))
        };
    }
    else
    {
        m_pendingEntityPlacementPreview.reset();
    }

    if (!leftMouseClicked)
    {
        return false;
    }

    std::string errorMessage;

    if (!session.createOutdoorObject(
            m_placementKind,
            static_cast<int>(std::lround(worldPosition.x)),
            static_cast<int>(std::lround(worldPosition.y)),
            static_cast<int>(std::lround(worldPosition.z)),
            errorMessage))
    {
        session.logError(errorMessage);
        return false;
    }

    return true;
}

std::optional<bx::Vec3> EditorOutdoorViewport::selectedWorldPosition(
    const EditorDocument &document,
    const EditorSelection &selection) const
{
    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();

    switch (selection.kind)
    {
    case EditorSelectionKind::Entity:
        if (selection.index < sceneData.entities.size())
        {
            const Game::OutdoorEntity &entity = sceneData.entities[selection.index].entity;
            return bx::Vec3{static_cast<float>(entity.x), static_cast<float>(entity.y), static_cast<float>(entity.z)};
        }
        break;

    case EditorSelectionKind::Spawn:
        if (selection.index < sceneData.spawns.size())
        {
            const Game::OutdoorSpawn &spawn = sceneData.spawns[selection.index].spawn;
            return bx::Vec3{static_cast<float>(spawn.x), static_cast<float>(spawn.y), static_cast<float>(spawn.z)};
        }
        break;

    case EditorSelectionKind::Actor:
        if (selection.index < sceneData.initialState.actors.size())
        {
            const Game::MapDeltaActor &actor = sceneData.initialState.actors[selection.index];
            return bx::Vec3{static_cast<float>(actor.x), static_cast<float>(actor.y), static_cast<float>(actor.z)};
        }
        break;

    case EditorSelectionKind::SpriteObject:
        if (selection.index < sceneData.initialState.spriteObjects.size())
        {
            const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[selection.index];
            return bx::Vec3{
                static_cast<float>(spriteObject.x),
                static_cast<float>(spriteObject.y),
                static_cast<float>(spriteObject.z)};
        }
        break;

    case EditorSelectionKind::Terrain:
    {
        int cellX = 0;
        int cellY = 0;

        if (decodeSelectedTerrainCell(selection, cellX, cellY)
            && cellX >= 0
            && cellY >= 0
            && cellX < (Game::OutdoorMapData::TerrainWidth - 1)
            && cellY < (Game::OutdoorMapData::TerrainHeight - 1))
        {
            const size_t topLeftIndex = static_cast<size_t>(cellY * Game::OutdoorMapData::TerrainWidth + cellX);
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex =
                static_cast<size_t>((cellY + 1) * Game::OutdoorMapData::TerrainWidth + cellX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const bx::Vec3 topLeft = worldPointFromTerrainGrid(cellX, cellY, outdoorGeometry.heightMap[topLeftIndex]);
            const bx::Vec3 topRight = worldPointFromTerrainGrid(cellX + 1, cellY, outdoorGeometry.heightMap[topRightIndex]);
            const bx::Vec3 bottomLeft =
                worldPointFromTerrainGrid(cellX, cellY + 1, outdoorGeometry.heightMap[bottomLeftIndex]);
            const bx::Vec3 bottomRight =
                worldPointFromTerrainGrid(cellX + 1, cellY + 1, outdoorGeometry.heightMap[bottomRightIndex]);

            return bx::Vec3{
                (topLeft.x + topRight.x + bottomLeft.x + bottomRight.x) * 0.25f,
                (topLeft.y + topRight.y + bottomLeft.y + bottomRight.y) * 0.25f,
                (topLeft.z + topRight.z + bottomLeft.z + bottomRight.z) * 0.25f};
        }

        break;
    }

    case EditorSelectionKind::BModel:
        if (selection.index < outdoorGeometry.bmodels.size())
        {
            const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[selection.index];
            float minX = std::numeric_limits<float>::max();
            float minY = std::numeric_limits<float>::max();
            float minZ = std::numeric_limits<float>::max();
            float maxX = std::numeric_limits<float>::lowest();
            float maxY = std::numeric_limits<float>::lowest();
            float maxZ = std::numeric_limits<float>::lowest();

            for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
            {
                minX = std::min(minX, static_cast<float>(vertex.x));
                minY = std::min(minY, static_cast<float>(vertex.y));
                minZ = std::min(minZ, static_cast<float>(vertex.z));
                maxX = std::max(maxX, static_cast<float>(vertex.x));
                maxY = std::max(maxY, static_cast<float>(vertex.y));
                maxZ = std::max(maxZ, static_cast<float>(vertex.z));
            }

            if (std::isfinite(minX) && std::isfinite(maxX))
            {
                return bx::Vec3{
                    (minX + maxX) * 0.5f,
                    (minY + maxY) * 0.5f,
                    (minZ + maxZ) * 0.5f};
            }
        }
        break;

    case EditorSelectionKind::InteractiveFace:
    {
        size_t bmodelIndex = 0;
        size_t faceIndex = 0;

        if (decodeSelectedInteractiveFace(document, selection, bmodelIndex, faceIndex)
            && bmodelIndex < outdoorGeometry.bmodels.size())
        {
            const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

            if (faceIndex < bmodel.faces.size())
            {
                const Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];
                bx::Vec3 center = {0.0f, 0.0f, 0.0f};
                int vertexCount = 0;

                for (size_t vertexIndex : face.vertexIndices)
                {
                    if (vertexIndex >= bmodel.vertices.size())
                    {
                        continue;
                    }

                    const Game::OutdoorBModelVertex &vertex = bmodel.vertices[vertexIndex];
                    center.x += static_cast<float>(vertex.x);
                    center.y += static_cast<float>(vertex.y);
                    center.z += static_cast<float>(vertex.z);
                    ++vertexCount;
                }

                if (vertexCount > 0)
                {
                    const float scale = 1.0f / static_cast<float>(vertexCount);
                    center.x *= scale;
                    center.y *= scale;
                    center.z *= scale;
                    return center;
                }
            }
        }

        break;
    }

    default:
        break;
    }

    return std::nullopt;
}

bool EditorOutdoorViewport::decodeSelectedTerrainCell(
    const EditorSelection &selection,
    int &cellX,
    int &cellY) const
{
    if (selection.kind != EditorSelectionKind::Terrain)
    {
        return false;
    }

    if (selection.index >= static_cast<size_t>(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight))
    {
        return false;
    }

    cellX = static_cast<int>(selection.index % Game::OutdoorMapData::TerrainWidth);
    cellY = static_cast<int>(selection.index / Game::OutdoorMapData::TerrainWidth);
    return true;
}

bool EditorOutdoorViewport::decodeSelectedInteractiveFace(
    const EditorDocument &document,
    const EditorSelection &selection,
    size_t &bmodelIndex,
    size_t &faceIndex) const
{
    if (selection.kind != EditorSelectionKind::InteractiveFace)
    {
        return false;
    }

    size_t runningIndex = 0;

    for (size_t currentBModelIndex = 0; currentBModelIndex < document.outdoorGeometry().bmodels.size(); ++currentBModelIndex)
    {
        const size_t faceCount = document.outdoorGeometry().bmodels[currentBModelIndex].faces.size();

        if (selection.index < runningIndex + faceCount)
        {
            bmodelIndex = currentBModelIndex;
            faceIndex = selection.index - runningIndex;
            return true;
        }

        runningIndex += faceCount;
    }

    return false;
}

bool EditorOutdoorViewport::computeMouseRay(float mouseX, float mouseY, bx::Vec3 &origin, bx::Vec3 &direction) const
{
    const float localMouseX = mouseX - static_cast<float>(m_viewportX);
    const float localMouseY = mouseY - static_cast<float>(m_viewportY);
    const float normalizedX = (localMouseX / static_cast<float>(std::max<uint16_t>(m_viewportWidth, 1))) * 2.0f - 1.0f;
    const float normalizedY = 1.0f - (localMouseY / static_cast<float>(std::max<uint16_t>(m_viewportHeight, 1))) * 2.0f;
    const float aspect = static_cast<float>(m_renderWidth) / static_cast<float>(std::max<uint16_t>(m_renderHeight, 1));
    const float tanHalfFovY = std::tan((CameraVerticalFovDegrees * bx::kPi / 180.0f) * 0.5f);
    const float tanHalfFovX = tanHalfFovY * aspect;
    const bx::Vec3 forward = {
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    };
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    const bx::Vec3 right = vecNormalize(vecCross(forward, worldUp));
    const bx::Vec3 up = vecNormalize(vecCross(right, forward));

    origin = m_cameraPosition;
    direction = vecNormalize({
        forward.x + right.x * normalizedX * tanHalfFovX + up.x * normalizedY * tanHalfFovY,
        forward.y + right.y * normalizedX * tanHalfFovX + up.y * normalizedY * tanHalfFovY,
        forward.z + right.z * normalizedX * tanHalfFovX + up.z * normalizedY * tanHalfFovY
    });
    return vecLength(direction) > 0.0001f;
}

bool EditorOutdoorViewport::sampleTerrainWorldPosition(
    const EditorDocument &document,
    float mouseX,
    float mouseY,
    bx::Vec3 &worldPosition) const
{
    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection))
    {
        return false;
    }

    const Game::OutdoorMapData &outdoorMapData = document.outdoorGeometry();
    constexpr float MaxDistance = 200000.0f;
    constexpr float StepDistance = 1024.0f;
    bool havePreviousSample = false;
    float previousDistance = 0.0f;
    float previousDelta = 0.0f;

    for (float distance = CameraNearPlane; distance <= MaxDistance; distance += StepDistance)
    {
        const bx::Vec3 rayPoint = {
            rayOrigin.x + rayDirection.x * distance,
            rayOrigin.y + rayDirection.y * distance,
            rayOrigin.z + rayDirection.z * distance
        };
        const float terrainHeight = Game::sampleOutdoorTerrainHeight(outdoorMapData, rayPoint.x, rayPoint.y);
        const float delta = rayPoint.z - terrainHeight;

        if (havePreviousSample && previousDelta >= 0.0f && delta <= 0.0f)
        {
            float lowDistance = previousDistance;
            float highDistance = distance;

            for (int iteration = 0; iteration < 12; ++iteration)
            {
                const float midDistance = (lowDistance + highDistance) * 0.5f;
                const bx::Vec3 midPoint = {
                    rayOrigin.x + rayDirection.x * midDistance,
                    rayOrigin.y + rayDirection.y * midDistance,
                    rayOrigin.z + rayDirection.z * midDistance
                };
                const float midTerrainHeight = Game::sampleOutdoorTerrainHeight(outdoorMapData, midPoint.x, midPoint.y);
                const float midDelta = midPoint.z - midTerrainHeight;

                if (midDelta > 0.0f)
                {
                    lowDistance = midDistance;
                }
                else
                {
                    highDistance = midDistance;
                }
            }

            const float hitDistance = highDistance;
            const bx::Vec3 hitPoint = {
                rayOrigin.x + rayDirection.x * hitDistance,
                rayOrigin.y + rayDirection.y * hitDistance,
                rayOrigin.z + rayDirection.z * hitDistance
            };
            worldPosition = {
                hitPoint.x,
                hitPoint.y,
                Game::sampleOutdoorTerrainHeight(outdoorMapData, hitPoint.x, hitPoint.y)
            };
            return true;
        }

        previousDistance = distance;
        previousDelta = delta;
        havePreviousSample = true;
    }

    return false;
}

bool EditorOutdoorViewport::samplePlacementWorldPosition(
    const EditorDocument &document,
    float mouseX,
    float mouseY,
    bx::Vec3 &worldPosition) const
{
    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection))
    {
        return false;
    }

    const Game::OutdoorMapData &outdoorMapData = document.outdoorGeometry();
    constexpr float MaxDistance = 200000.0f;
    constexpr float StepDistance = 512.0f;
    bool havePreviousSample = false;
    float previousDistance = 0.0f;
    float previousDelta = 0.0f;

    for (float distance = CameraNearPlane; distance <= MaxDistance; distance += StepDistance)
    {
        const bx::Vec3 rayPoint = {
            rayOrigin.x + rayDirection.x * distance,
            rayOrigin.y + rayDirection.y * distance,
            rayOrigin.z + rayDirection.z * distance
        };
        const float floorHeight =
            Game::sampleOutdoorPlacementFloorHeight(outdoorMapData, rayPoint.x, rayPoint.y, rayPoint.z);
        const float delta = rayPoint.z - floorHeight;

        if (havePreviousSample && previousDelta >= 0.0f && delta <= 0.0f)
        {
            float lowDistance = previousDistance;
            float highDistance = distance;

            for (int iteration = 0; iteration < 12; ++iteration)
            {
                const float midDistance = (lowDistance + highDistance) * 0.5f;
                const bx::Vec3 midPoint = {
                    rayOrigin.x + rayDirection.x * midDistance,
                    rayOrigin.y + rayDirection.y * midDistance,
                    rayOrigin.z + rayDirection.z * midDistance
                };
                const float midFloorHeight =
                    Game::sampleOutdoorPlacementFloorHeight(outdoorMapData, midPoint.x, midPoint.y, midPoint.z);
                const float midDelta = midPoint.z - midFloorHeight;

                if (midDelta > 0.0f)
                {
                    lowDistance = midDistance;
                }
                else
                {
                    highDistance = midDistance;
                }
            }

            const float hitDistance = highDistance;
            const bx::Vec3 hitPoint = {
                rayOrigin.x + rayDirection.x * hitDistance,
                rayOrigin.y + rayDirection.y * hitDistance,
                rayOrigin.z + rayDirection.z * hitDistance
            };
            worldPosition = {
                hitPoint.x,
                hitPoint.y,
                Game::sampleOutdoorPlacementFloorHeight(outdoorMapData, hitPoint.x, hitPoint.y, hitPoint.z)
            };
            return true;
        }

        previousDistance = distance;
        previousDelta = delta;
        havePreviousSample = true;
    }

    return false;
}

bool EditorOutdoorViewport::setSelectedWorldPosition(EditorSession &session, const bx::Vec3 &worldPosition)
{
    if (!session.hasDocument())
    {
        return false;
    }

    EditorDocument &document = session.document();
    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();
    Game::OutdoorMapData &outdoorGeometry = document.mutableOutdoorGeometry();
    int targetX = static_cast<int>(std::lround(worldPosition.x));
    int targetY = static_cast<int>(std::lround(worldPosition.y));
    int targetZ = static_cast<int>(std::lround(worldPosition.z));

    if (m_snapEnabled)
    {
        const int snapStep = std::max(m_snapStep, 1);
        const auto snapValue = [snapStep](int value)
        {
            return static_cast<int>(std::lround(static_cast<float>(value) / static_cast<float>(snapStep))) * snapStep;
        };

        targetX = snapValue(targetX);
        targetY = snapValue(targetY);
        targetZ = snapValue(targetZ);
    }

    bool changed = false;

    switch (session.selection().kind)
    {
    case EditorSelectionKind::Entity:
        if (session.selection().index < sceneData.entities.size())
        {
            Game::OutdoorEntity &entity = sceneData.entities[session.selection().index].entity;
            changed = entity.x != targetX || entity.y != targetY || entity.z != targetZ;
            entity.x = targetX;
            entity.y = targetY;
            entity.z = targetZ;
        }
        break;

    case EditorSelectionKind::Spawn:
        if (session.selection().index < sceneData.spawns.size())
        {
            Game::OutdoorSpawn &spawn = sceneData.spawns[session.selection().index].spawn;
            changed = spawn.x != targetX || spawn.y != targetY || spawn.z != targetZ;
            spawn.x = targetX;
            spawn.y = targetY;
            spawn.z = targetZ;
        }
        break;

    case EditorSelectionKind::Actor:
        if (session.selection().index < sceneData.initialState.actors.size())
        {
            Game::MapDeltaActor &actor = sceneData.initialState.actors[session.selection().index];
            changed = actor.x != targetX || actor.y != targetY || actor.z != targetZ;
            actor.x = targetX;
            actor.y = targetY;
            actor.z = targetZ;
        }
        break;

    case EditorSelectionKind::SpriteObject:
        if (session.selection().index < sceneData.initialState.spriteObjects.size())
        {
            Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[session.selection().index];
            changed = spriteObject.x != targetX || spriteObject.y != targetY || spriteObject.z != targetZ;
            spriteObject.x = targetX;
            spriteObject.y = targetY;
            spriteObject.z = targetZ;
        }
        break;

    case EditorSelectionKind::BModel:
        if (session.selection().index < outdoorGeometry.bmodels.size())
        {
            const size_t bmodelIndex = session.selection().index;
            const std::optional<bx::Vec3> currentCenter = selectedWorldPosition(document, session.selection());

            if (!currentCenter)
            {
                break;
            }

            const int deltaX = targetX - static_cast<int>(std::lround(currentCenter->x));
            const int deltaY = targetY - static_cast<int>(std::lround(currentCenter->y));
            const int deltaZ = targetZ - static_cast<int>(std::lround(currentCenter->z));

            changed = deltaX != 0 || deltaY != 0 || deltaZ != 0;

            if (changed)
            {
                Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
                const bool trackSourceTransform =
                    document.outdoorBModelImportSource(bmodelIndex).has_value()
                    || document.outdoorBModelSourceTransform(bmodelIndex).has_value();
                EditorBModelSourceTransform sourceTransform =
                    document.outdoorBModelSourceTransform(bmodelIndex).value_or(sourceTransformFromBModel(bmodel));

                for (Game::OutdoorBModelVertex &vertex : bmodel.vertices)
                {
                    vertex.x += deltaX;
                    vertex.y += deltaY;
                    vertex.z += deltaZ;
                }

                bmodel.positionX += deltaX;
                bmodel.positionY += deltaY;
                bmodel.positionZ += deltaZ;
                bmodel.minX += deltaX;
                bmodel.minY += deltaY;
                bmodel.minZ += deltaZ;
                bmodel.maxX += deltaX;
                bmodel.maxY += deltaY;
                bmodel.maxZ += deltaZ;
                bmodel.boundingCenterX += deltaX;
                bmodel.boundingCenterY += deltaY;
                bmodel.boundingCenterZ += deltaZ;

                if (trackSourceTransform)
                {
                    sourceTransform.originX += static_cast<float>(deltaX);
                    sourceTransform.originY += static_cast<float>(deltaY);
                    sourceTransform.originZ += static_cast<float>(deltaZ);
                    document.setOutdoorBModelSourceTransform(bmodelIndex, sourceTransform);
                }

                m_geometryKey.clear();
            }
        }
        break;

    default:
        break;
    }

    return changed;
}

bool EditorOutdoorViewport::tryBeginGizmoDrag(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!leftMouseClicked || m_activeGizmoDrag.mode != GizmoDragMode::None || !session.hasDocument())
    {
        return false;
    }

    const EditorSelection selection = session.selection();
    const std::optional<bx::Vec3> selectedPosition = selectedWorldPosition(session.document(), selection);

    if (!selectedPosition)
    {
        return false;
    }

    float centerScreenX = 0.0f;
    float centerScreenY = 0.0f;
    float centerClipW = 0.0f;

    if (!projectWorldPoint(
            *selectedPosition,
            m_viewProjectionMatrix,
            m_viewportWidth,
            m_viewportHeight,
            centerScreenX,
            centerScreenY,
            centerClipW))
    {
        return false;
    }

    const float localMouseX = mouseX - static_cast<float>(m_viewportX);
    const float localMouseY = mouseY - static_cast<float>(m_viewportY);
    bx::Vec3 xAxisWorld = {1.0f, 0.0f, 0.0f};
    bx::Vec3 yAxisWorld = {0.0f, 1.0f, 0.0f};
    bx::Vec3 zAxisWorld = {0.0f, 0.0f, 1.0f};
    computeTransformBasis(session.document(), selection, m_transformSpaceMode, xAxisWorld, yAxisWorld, zAxisWorld);
    const bx::Vec3 xAxisPoint = vecAdd(*selectedPosition, vecScale(xAxisWorld, GizmoAxisWorldLength));
    const bx::Vec3 yAxisPoint = vecAdd(*selectedPosition, vecScale(yAxisWorld, GizmoAxisWorldLength));
    const bx::Vec3 zAxisPoint = vecAdd(*selectedPosition, vecScale(zAxisWorld, GizmoAxisWorldLength));
    float xAxisScreenX = 0.0f;
    float xAxisScreenY = 0.0f;
    float yAxisScreenX = 0.0f;
    float yAxisScreenY = 0.0f;
    float zAxisScreenX = 0.0f;
    float zAxisScreenY = 0.0f;
    float axisClipW = 0.0f;
    const bool hasXAxis = projectWorldPoint(
        xAxisPoint,
        m_viewProjectionMatrix,
        m_viewportWidth,
        m_viewportHeight,
        xAxisScreenX,
        xAxisScreenY,
        axisClipW);
    const bool hasYAxis = projectWorldPoint(
        yAxisPoint,
        m_viewProjectionMatrix,
        m_viewportWidth,
        m_viewportHeight,
        yAxisScreenX,
        yAxisScreenY,
        axisClipW);
    const bool hasZAxis = projectWorldPoint(
        zAxisPoint,
        m_viewProjectionMatrix,
        m_viewportWidth,
        m_viewportHeight,
        zAxisScreenX,
        zAxisScreenY,
        axisClipW);
    const bool useRotateGizmo =
        selection.kind == EditorSelectionKind::BModel && m_transformGizmoMode == TransformGizmoMode::Rotate;
    float rotateHandleRadiusWorld = 0.0f;
    float rotatePickDistanceSquared = std::numeric_limits<float>::max();
    GizmoDragMode rotateMode = GizmoDragMode::None;
    bx::Vec3 rotateAxisWorld = {0.0f, 0.0f, 1.0f};

    if (useRotateGizmo && selection.index < session.document().outdoorGeometry().bmodels.size())
    {
        const Game::OutdoorBModel &bmodel = session.document().outdoorGeometry().bmodels[selection.index];
        rotateHandleRadiusWorld = bmodelRotationHandleRadius(bmodel);
        const auto evaluateRotationRing =
            [this,
             localMouseX,
             localMouseY,
             selectedPosition,
             rotateHandleRadiusWorld](
                const bx::Vec3 &axis,
                GizmoDragMode candidateMode,
                float &bestDistanceSquared,
                GizmoDragMode &bestMode,
                bx::Vec3 &bestAxis)
        {
            std::vector<ScreenPoint> ringPoints;
            ringPoints.reserve(GizmoRotationSegments + 1);

            for (int segmentIndex = 0; segmentIndex <= GizmoRotationSegments; ++segmentIndex)
            {
                const float angle = (static_cast<float>(segmentIndex) / static_cast<float>(GizmoRotationSegments)) * bx::kPi2;
                bx::Vec3 ringPoint = *selectedPosition;

                if (std::fabs(axis.x) > 0.5f)
                {
                    ringPoint.y += std::cos(angle) * rotateHandleRadiusWorld;
                    ringPoint.z += std::sin(angle) * rotateHandleRadiusWorld;
                }
                else if (std::fabs(axis.y) > 0.5f)
                {
                    ringPoint.x += std::cos(angle) * rotateHandleRadiusWorld;
                    ringPoint.z += std::sin(angle) * rotateHandleRadiusWorld;
                }
                else
                {
                    ringPoint.x += std::cos(angle) * rotateHandleRadiusWorld;
                    ringPoint.y += std::sin(angle) * rotateHandleRadiusWorld;
                }

                float projectedX = 0.0f;
                float projectedY = 0.0f;
                float clipW = 0.0f;

                if (!projectWorldPoint(
                        ringPoint,
                        m_viewProjectionMatrix,
                        m_viewportWidth,
                        m_viewportHeight,
                        projectedX,
                        projectedY,
                        clipW))
                {
                    return;
                }

                ringPoints.push_back({projectedX, projectedY});
            }

            for (size_t index = 1; index < ringPoints.size(); ++index)
            {
                const float distanceSquared = distancePointToSegmentSquared(
                    localMouseX,
                    localMouseY,
                    ringPoints[index - 1].x,
                    ringPoints[index - 1].y,
                    ringPoints[index].x,
                    ringPoints[index].y);

                if (distanceSquared < bestDistanceSquared)
                {
                    bestDistanceSquared = distanceSquared;
                    bestMode = candidateMode;
                    bestAxis = axis;
                }
            }
        };

        evaluateRotationRing(xAxisWorld, GizmoDragMode::RotateX, rotatePickDistanceSquared, rotateMode, rotateAxisWorld);
        evaluateRotationRing(yAxisWorld, GizmoDragMode::RotateY, rotatePickDistanceSquared, rotateMode, rotateAxisWorld);
        evaluateRotationRing(zAxisWorld, GizmoDragMode::RotateZ, rotatePickDistanceSquared, rotateMode, rotateAxisWorld);
    }

    const float xAxisDistanceSquared = hasXAxis
        ? distancePointToSegmentSquared(
            localMouseX,
            localMouseY,
            centerScreenX,
            centerScreenY,
            xAxisScreenX,
            xAxisScreenY)
        : std::numeric_limits<float>::max();
    const float yAxisDistanceSquared = hasYAxis
        ? distancePointToSegmentSquared(
            localMouseX,
            localMouseY,
            centerScreenX,
            centerScreenY,
            yAxisScreenX,
            yAxisScreenY)
        : std::numeric_limits<float>::max();
    const float zAxisDistanceSquared = hasZAxis
        ? distancePointToSegmentSquared(
            localMouseX,
            localMouseY,
            centerScreenX,
            centerScreenY,
            zAxisScreenX,
            zAxisScreenY)
        : std::numeric_limits<float>::max();
    const float zAxisEndpointDistanceSquared =
        hasZAxis ? squaredLength2(localMouseX - zAxisScreenX, localMouseY - zAxisScreenY) : std::numeric_limits<float>::max();

    GizmoDragMode mode = GizmoDragMode::None;

    if (useRotateGizmo)
    {
        if (rotatePickDistanceSquared <= GizmoRotationPickSlackPixels * GizmoRotationPickSlackPixels)
        {
            mode = rotateMode;
        }
    }
    else if (hasZAxis
        && (zAxisDistanceSquared <= GizmoZAxisPickSlackPixels * GizmoZAxisPickSlackPixels
            || zAxisEndpointDistanceSquared
                <= GizmoAxisEndpointPickRadiusPixels * GizmoAxisEndpointPickRadiusPixels))
    {
        mode = GizmoDragMode::TranslateZ;
    }
    else if (squaredLength2(localMouseX - centerScreenX, localMouseY - centerScreenY)
        <= GizmoCenterPickRadiusPixels * GizmoCenterPickRadiusPixels)
    {
        mode = GizmoDragMode::TranslatePlaneXY;
    }
    else if (hasXAxis && xAxisDistanceSquared <= GizmoAxisPickSlackPixels * GizmoAxisPickSlackPixels)
    {
        mode = GizmoDragMode::TranslateX;
    }
    else if (hasYAxis && yAxisDistanceSquared <= GizmoAxisPickSlackPixels * GizmoAxisPickSlackPixels)
    {
        mode = GizmoDragMode::TranslateY;
    }

    if (mode == GizmoDragMode::None)
    {
        return false;
    }

    session.captureUndoSnapshot();
    m_activeGizmoDrag.mode = mode;
    m_activeGizmoDrag.selection = selection;
    m_activeGizmoDrag.startWorldPosition = *selectedPosition;
    m_activeGizmoDrag.startMouseX = localMouseX;
    m_activeGizmoDrag.startMouseY = localMouseY;
    m_activeGizmoDrag.startScreenX = centerScreenX;
    m_activeGizmoDrag.startScreenY = centerScreenY;
    m_activeGizmoDrag.xAxisScreenX = xAxisScreenX;
    m_activeGizmoDrag.xAxisScreenY = xAxisScreenY;
    m_activeGizmoDrag.yAxisScreenX = yAxisScreenX;
    m_activeGizmoDrag.yAxisScreenY = yAxisScreenY;
    m_activeGizmoDrag.zAxisScreenX = zAxisScreenX;
    m_activeGizmoDrag.zAxisScreenY = zAxisScreenY;
    m_activeGizmoDrag.axisWorldLength = GizmoAxisWorldLength;
    m_activeGizmoDrag.xAxisWorld = xAxisWorld;
    m_activeGizmoDrag.yAxisWorld = yAxisWorld;
    m_activeGizmoDrag.zAxisWorld = zAxisWorld;
    m_activeGizmoDrag.rotateHandleRadiusWorld = rotateHandleRadiusWorld;
    m_activeGizmoDrag.rotateAxisWorld = rotateAxisWorld;
    m_activeGizmoDrag.startRotateVectorWorld = {1.0f, 0.0f, 0.0f};
    m_activeGizmoDrag.startBModelVertices.clear();
    m_activeGizmoDrag.hasStartSourceTransform = false;

    if ((mode == GizmoDragMode::RotateX
            || mode == GizmoDragMode::RotateY
            || mode == GizmoDragMode::RotateZ)
        && selection.kind == EditorSelectionKind::BModel
        && selection.index < session.document().outdoorGeometry().bmodels.size())
    {
        bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
        bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};
        bx::Vec3 intersection = {0.0f, 0.0f, 0.0f};

        if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection)
            || !intersectRayPlane(
                rayOrigin,
                rayDirection,
                *selectedPosition,
                rotateAxisWorld,
                intersection))
        {
            m_activeGizmoDrag = {};
            return false;
        }

        const bx::Vec3 rotateVector = {
            intersection.x - selectedPosition->x,
            intersection.y - selectedPosition->y,
            intersection.z - selectedPosition->z
        };

        if (vecLength(rotateVector) <= 1.0f)
        {
            m_activeGizmoDrag = {};
            return false;
        }

        m_activeGizmoDrag.startRotateVectorWorld = vecNormalize(rotateVector);
        m_activeGizmoDrag.startBModelVertices =
            session.document().outdoorGeometry().bmodels[selection.index].vertices;
        m_activeGizmoDrag.startSourceTransform =
            session.document().outdoorBModelSourceTransform(selection.index).value_or(
                sourceTransformFromBModel(session.document().outdoorGeometry().bmodels[selection.index]));
        m_activeGizmoDrag.hasStartSourceTransform =
            session.document().outdoorBModelImportSource(selection.index).has_value()
            || session.document().outdoorBModelSourceTransform(selection.index).has_value();
    }

    m_activeGizmoDrag.mutated = false;
    return true;
}

void EditorOutdoorViewport::updateGizmoDrag(
    EditorSession &session,
    bool leftMouseDown,
    float mouseX,
    float mouseY)
{
    if (m_activeGizmoDrag.mode == GizmoDragMode::None)
    {
        return;
    }

    if (!leftMouseDown)
    {
        if (m_activeGizmoDrag.mutated)
        {
            session.noteDocumentMutated({});
        }

        m_activeGizmoDrag = {};
        return;
    }

    if (session.selection().kind != m_activeGizmoDrag.selection.kind
        || session.selection().index != m_activeGizmoDrag.selection.index)
    {
        if (m_activeGizmoDrag.mutated)
        {
            session.noteDocumentMutated({});
        }

        m_activeGizmoDrag = {};
        return;
    }

    const float localMouseX = mouseX - static_cast<float>(m_viewportX);
    const float localMouseY = mouseY - static_cast<float>(m_viewportY);
    const float deltaMouseX = localMouseX - m_activeGizmoDrag.startMouseX;
    const float deltaMouseY = localMouseY - m_activeGizmoDrag.startMouseY;
    bx::Vec3 updatedPosition = m_activeGizmoDrag.startWorldPosition;

    switch (m_activeGizmoDrag.mode)
    {
    case GizmoDragMode::TranslateX:
    {
        const float axisScreenDeltaX = m_activeGizmoDrag.xAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float axisScreenDeltaY = m_activeGizmoDrag.xAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float axisScreenLengthSquared = squaredLength2(axisScreenDeltaX, axisScreenDeltaY);

        if (axisScreenLengthSquared > 0.0001f)
        {
            const float pixelProjection =
                (deltaMouseX * axisScreenDeltaX + deltaMouseY * axisScreenDeltaY)
                / std::sqrt(axisScreenLengthSquared);
            const float axisScreenLength = std::sqrt(axisScreenLengthSquared);
            updatedPosition = vecAdd(
                updatedPosition,
                vecScale(
                    m_activeGizmoDrag.xAxisWorld,
                    (pixelProjection / axisScreenLength) * m_activeGizmoDrag.axisWorldLength));
        }
        break;
    }

    case GizmoDragMode::TranslateY:
    {
        const float axisScreenDeltaX = m_activeGizmoDrag.yAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float axisScreenDeltaY = m_activeGizmoDrag.yAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float axisScreenLengthSquared = squaredLength2(axisScreenDeltaX, axisScreenDeltaY);

        if (axisScreenLengthSquared > 0.0001f)
        {
            const float pixelProjection =
                (deltaMouseX * axisScreenDeltaX + deltaMouseY * axisScreenDeltaY)
                / std::sqrt(axisScreenLengthSquared);
            const float axisScreenLength = std::sqrt(axisScreenLengthSquared);
            updatedPosition = vecAdd(
                updatedPosition,
                vecScale(
                    m_activeGizmoDrag.yAxisWorld,
                    (pixelProjection / axisScreenLength) * m_activeGizmoDrag.axisWorldLength));
        }
        break;
    }

    case GizmoDragMode::TranslateZ:
    {
        const float axisScreenDeltaX = m_activeGizmoDrag.zAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float axisScreenDeltaY = m_activeGizmoDrag.zAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float axisScreenLengthSquared = squaredLength2(axisScreenDeltaX, axisScreenDeltaY);

        if (axisScreenLengthSquared > 0.0001f)
        {
            const float pixelProjection =
                (deltaMouseX * axisScreenDeltaX + deltaMouseY * axisScreenDeltaY)
                / std::sqrt(axisScreenLengthSquared);
            const float axisScreenLength = std::sqrt(axisScreenLengthSquared);
            updatedPosition = vecAdd(
                updatedPosition,
                vecScale(
                    m_activeGizmoDrag.zAxisWorld,
                    (pixelProjection / axisScreenLength) * m_activeGizmoDrag.axisWorldLength));
        }
        break;
    }

    case GizmoDragMode::TranslatePlaneXY:
    {
        const float xScreenX = m_activeGizmoDrag.xAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float xScreenY = m_activeGizmoDrag.xAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float yScreenX = m_activeGizmoDrag.yAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float yScreenY = m_activeGizmoDrag.yAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float determinant = xScreenX * yScreenY - xScreenY * yScreenX;

        if (std::fabs(determinant) > 0.0001f)
        {
            const float invDeterminant = 1.0f / determinant;
            const float xCoeff = (deltaMouseX * yScreenY - deltaMouseY * yScreenX) * invDeterminant;
            const float yCoeff = (deltaMouseY * xScreenX - deltaMouseX * xScreenY) * invDeterminant;
            updatedPosition = vecAdd(
                updatedPosition,
                vecAdd(
                    vecScale(m_activeGizmoDrag.xAxisWorld, xCoeff * m_activeGizmoDrag.axisWorldLength),
                    vecScale(m_activeGizmoDrag.yAxisWorld, yCoeff * m_activeGizmoDrag.axisWorldLength)));
        }
        break;
    }

    case GizmoDragMode::RotateX:
    case GizmoDragMode::RotateY:
    case GizmoDragMode::RotateZ:
    {
        if (m_activeGizmoDrag.selection.kind == EditorSelectionKind::BModel
            && m_activeGizmoDrag.selection.index < session.document().mutableOutdoorGeometry().bmodels.size())
        {
            bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
            bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};
            bx::Vec3 intersection = {0.0f, 0.0f, 0.0f};

            if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection)
                || !intersectRayPlane(
                    rayOrigin,
                    rayDirection,
                    m_activeGizmoDrag.startWorldPosition,
                    m_activeGizmoDrag.rotateAxisWorld,
                    intersection))
            {
                return;
            }

            const bx::Vec3 currentRotateVector = {
                intersection.x - m_activeGizmoDrag.startWorldPosition.x,
                intersection.y - m_activeGizmoDrag.startWorldPosition.y,
                intersection.z - m_activeGizmoDrag.startWorldPosition.z
            };

            if (vecLength(currentRotateVector) <= 1.0f)
            {
                return;
            }

            const float deltaAngleRadians = signedAngleAroundAxis(
                m_activeGizmoDrag.startRotateVectorWorld,
                currentRotateVector,
                m_activeGizmoDrag.rotateAxisWorld);
            Game::OutdoorBModel &bmodel =
                session.document().mutableOutdoorGeometry().bmodels[m_activeGizmoDrag.selection.index];

            if (applyBModelAxisRotation(
                    bmodel,
                    m_activeGizmoDrag.startBModelVertices,
                    m_activeGizmoDrag.startWorldPosition,
                    m_activeGizmoDrag.rotateAxisWorld,
                    deltaAngleRadians))
            {
                if (m_activeGizmoDrag.hasStartSourceTransform)
                {
                    EditorBModelSourceTransform sourceTransform = m_activeGizmoDrag.startSourceTransform;
                    sourceTransform.basisX = rotateBasisVectorAroundAxis(
                        sourceTransform.basisX,
                        m_activeGizmoDrag.rotateAxisWorld,
                        deltaAngleRadians);
                    sourceTransform.basisY = rotateBasisVectorAroundAxis(
                        sourceTransform.basisY,
                        m_activeGizmoDrag.rotateAxisWorld,
                        deltaAngleRadians);
                    sourceTransform.basisZ = rotateBasisVectorAroundAxis(
                        sourceTransform.basisZ,
                        m_activeGizmoDrag.rotateAxisWorld,
                        deltaAngleRadians);
                    session.document().setOutdoorBModelSourceTransform(m_activeGizmoDrag.selection.index, sourceTransform);
                }

                session.document().setDirty(true);
                session.document().touchSceneRevision();
                m_geometryKey.clear();
                m_activeGizmoDrag.mutated = true;
            }
        }
        return;
    }

    case GizmoDragMode::None:
        break;
    }

    if (setSelectedWorldPosition(session, updatedPosition))
    {
        session.document().setDirty(true);
        m_activeGizmoDrag.mutated = true;
    }
}

void EditorOutdoorViewport::submitStaticGeometry(const EditorSession &session) const
{
    float transform[16] = {};
    bx::mtxIdentity(transform);
    const auto submitProceduralBatch =
        [this, &transform](
            const bgfx::VertexBufferHandle vertexBufferHandle,
            uint32_t vertexCount,
            const bx::Vec3 &objectOrigin,
            const ClayPreviewSettings &settings,
            bool depthEqual) -> void
    {
        if (!bgfx::isValid(vertexBufferHandle)
            || vertexCount == 0
            || !bgfx::isValid(m_proceduralPreviewProgramHandle))
        {
            return;
        }

        const std::array<float, 4> params0 = {
            settings.slopeAccentStrength,
            settings.shadowStrength,
            settings.lightWrap,
            0.0f
        };
        const std::array<float, 4> params1 = {0.0f, 0.0f, 0.0f, 0.0f};
        const std::array<float, 4> previewOrigin = {objectOrigin.x, objectOrigin.y, objectOrigin.z, 0.0f};
        bgfx::setUniform(m_previewColorAHandle, settings.baseColor.data());
        bgfx::setUniform(m_previewParams0Handle, params0.data());
        bgfx::setUniform(m_previewParams1Handle, params1.data());
        bgfx::setUniform(m_previewObjectOriginHandle, previewOrigin.data());
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, vertexBufferHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | (depthEqual ? BGFX_STATE_DEPTH_TEST_LEQUAL : BGFX_STATE_DEPTH_TEST_LESS)
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_proceduralPreviewProgramHandle);
    };
    const auto submitGridBatch =
        [this, &transform](
            const bgfx::VertexBufferHandle vertexBufferHandle,
            uint32_t vertexCount,
            const bx::Vec3 &objectOrigin,
            const GridPreviewSettings &settings,
            float materialMode,
            bool depthEqual) -> void
    {
        if (!bgfx::isValid(vertexBufferHandle)
            || vertexCount == 0
            || !bgfx::isValid(m_proceduralPreviewProgramHandle))
        {
            return;
        }

        const std::array<float, 4> params0 = {
            settings.cellSize,
            settings.majorInterval,
            settings.lineThickness,
            settings.majorLineThickness
        };
        const std::array<float, 4> params1 = {materialMode, 0.0f, 0.0f, 0.0f};
        const std::array<float, 4> previewOrigin = {objectOrigin.x, objectOrigin.y, objectOrigin.z, 0.0f};
        bgfx::setUniform(m_previewColorAHandle, settings.baseColorA.data());
        bgfx::setUniform(m_previewColorBHandle, settings.baseColorB.data());
        bgfx::setUniform(m_previewColorCHandle, settings.minorLineColor.data());
        bgfx::setUniform(m_previewColorDHandle, settings.majorLineColor.data());
        bgfx::setUniform(m_previewParams0Handle, params0.data());
        bgfx::setUniform(m_previewParams1Handle, params1.data());
        bgfx::setUniform(m_previewObjectOriginHandle, previewOrigin.data());
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, vertexBufferHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | (depthEqual ? BGFX_STATE_DEPTH_TEST_LEQUAL : BGFX_STATE_DEPTH_TEST_LESS)
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_proceduralPreviewProgramHandle);
    };
    const bool terrainUsesClay =
        m_previewMaterialMode == PreviewMaterialMode::Clay
        || !bgfx::isValid(m_texturedTerrainVertexBufferHandle)
        || !bgfx::isValid(m_terrainTextureAtlasHandle);
    std::optional<size_t> selectedBModelIndex;
    const EditorSelection &selection = session.selection();

    if (selection.kind == EditorSelectionKind::BModel)
    {
        selectedBModelIndex = selection.index;
    }
    else if (selection.kind == EditorSelectionKind::InteractiveFace)
    {
        size_t bmodelIndex = 0;
        size_t faceIndex = 0;

        if (decodeSelectedInteractiveFace(session.document(), selection, bmodelIndex, faceIndex))
        {
            selectedBModelIndex = bmodelIndex;
        }
    }

    const auto shouldForcePreviewForBModel =
        [this, &selectedBModelIndex](size_t bmodelIndex) -> bool
    {
        if (m_previewMaterialMode == PreviewMaterialMode::Textured || !m_forcePreviewOnSelectedOnly)
        {
            return false;
        }

        return selectedBModelIndex && *selectedBModelIndex == bmodelIndex;
    };

    if (m_showTerrainFill && terrainUsesClay && m_terrainVertexCount > 0)
    {
        submitProceduralBatch(
            m_terrainVertexBufferHandle,
            m_terrainVertexCount,
            {0.0f, 0.0f, 0.0f},
            m_clayPreviewSettings,
            false);
    }
    else if (m_showTerrainFill
        && bgfx::isValid(m_texturedTerrainVertexBufferHandle)
        && bgfx::isValid(m_terrainTextureAtlasHandle)
        && bgfx::isValid(m_texturedProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && m_texturedTerrainVertexCount > 0)
    {
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, m_texturedTerrainVertexBufferHandle);
        bgfx::setTexture(0, m_textureSamplerHandle, m_terrainTextureAtlasHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_texturedProgramHandle);
    }
    else if (m_showTerrainFill && m_terrainVertexCount > 0)
    {
        submitProceduralBatch(
            m_terrainVertexBufferHandle,
            m_terrainVertexCount,
            {0.0f, 0.0f, 0.0f},
            m_clayPreviewSettings,
            false);
    }

    if (m_showTerrainFill && m_terrainErrorVertexCount > 0)
    {
        submitGridBatch(
            m_terrainErrorVertexBufferHandle,
            m_terrainErrorVertexCount,
            {0.0f, 0.0f, 0.0f},
            m_errorPreviewSettings,
            2.0f,
            true);
    }

    if (m_showBModels && bgfx::isValid(m_texturedProgramHandle) && bgfx::isValid(m_textureSamplerHandle))
    {
        for (const TexturedBatch &batch : m_bmodelTexturedBatches)
        {
            if (!bgfx::isValid(batch.vertexBufferHandle) || !bgfx::isValid(batch.textureHandle) || batch.vertexCount == 0)
            {
                continue;
            }

            if (shouldForcePreviewForBModel(batch.bmodelIndex))
            {
                continue;
            }

            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, batch.vertexBufferHandle);
            bgfx::setTexture(0, m_textureSamplerHandle, batch.textureHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LESS
                    | BGFX_STATE_MSAA);
            bgfx::submit(EditorSceneViewId, m_texturedProgramHandle);
        }
    }

    if (bgfx::isValid(m_importedModelPreviewBatch.vertexBufferHandle) && m_importedModelPreviewBatch.vertexCount > 0)
    {
        if (m_previewMaterialMode == PreviewMaterialMode::Grid)
        {
            submitGridBatch(
                m_importedModelPreviewBatch.vertexBufferHandle,
                m_importedModelPreviewBatch.vertexCount,
                m_importedModelPreviewBatch.objectOrigin,
                m_gridPreviewSettings,
                1.0f,
                false);
        }
        else
        {
            submitProceduralBatch(
                m_importedModelPreviewBatch.vertexBufferHandle,
                m_importedModelPreviewBatch.vertexCount,
                m_importedModelPreviewBatch.objectOrigin,
                m_clayPreviewSettings,
                false);
        }
    }

    if (m_showBModels)
    {
        for (const ProceduralBatch &batch : m_bmodelAllFaceBatches)
        {
            if (!shouldForcePreviewForBModel(batch.bmodelIndex))
            {
                continue;
            }

            if (m_previewMaterialMode == PreviewMaterialMode::Clay)
            {
                submitProceduralBatch(
                    batch.vertexBufferHandle,
                    batch.vertexCount,
                    batch.objectOrigin,
                    m_clayPreviewSettings,
                    false);
            }
            else
            {
                submitGridBatch(
                    batch.vertexBufferHandle,
                    batch.vertexCount,
                    batch.objectOrigin,
                    m_gridPreviewSettings,
                    1.0f,
                    false);
            }
        }

        for (const ProceduralBatch &batch : m_bmodelUnassignedBatches)
        {
            if (shouldForcePreviewForBModel(batch.bmodelIndex))
            {
                continue;
            }

            submitGridBatch(
                batch.vertexBufferHandle,
                batch.vertexCount,
                batch.objectOrigin,
                m_gridPreviewSettings,
                1.0f,
                false);
        }

        for (const ProceduralBatch &batch : m_bmodelMissingAssetBatches)
        {
            submitGridBatch(
                batch.vertexBufferHandle,
                batch.vertexCount,
                batch.objectOrigin,
                m_errorPreviewSettings,
                2.0f,
                true);
        }
    }

    if (m_showBModelWireframe && bgfx::isValid(m_bmodelWireVertexBufferHandle) && m_bmodelWireVertexCount > 0)
    {
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, m_bmodelWireVertexBufferHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }
}

void EditorOutdoorViewport::submitEntityBillboardGeometry(
    const EditorSession &session,
    const EditorDocument &document) const
{
    if ((!m_showEntities || !m_showEntityBillboards)
        && (!m_showActors || !m_showActorBillboards)
        && (!m_showSpawns || !m_showSpawnActorBillboards)
        && m_pendingEntityPlacementPreview == std::nullopt
        && !m_showSpriteObjects
        && m_pendingSpriteObjectPlacementPreview == std::nullopt
        || !bgfx::isValid(m_texturedProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle))
    {
        return;
    }

    const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();

    if (pAssetFileSystem == nullptr)
    {
        return;
    }

    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();
    const uint32_t animationTicks = currentAnimationTicks();
    const EditorSelection &selection = session.selection();
    const bx::Vec3 forward = vecNormalize({
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    });
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    const bx::Vec3 cameraRight = vecNormalize(vecCross(forward, worldUp));
    const bx::Vec3 cameraUp = vecNormalize(vecCross(cameraRight, forward));

    struct BillboardDrawItem
    {
        const SpriteBillboardTexture *pTexture = nullptr;
        bx::Vec3 center = {0.0f, 0.0f, 0.0f};
        float worldWidth = 0.0f;
        float worldHeight = 0.0f;
        float cameraDepth = 0.0f;
        bool mirrored = false;
    };

    BitmapLoadCache bitmapLoadCache = {};
    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(
        session.entityBillboardPreviews().size()
        + session.actorBillboardPreviews().size()
        + (m_pendingEntityPlacementPreview ? 1u : 0u)
        + sceneData.initialState.spriteObjects.size()
        + (m_pendingSpriteObjectPlacementPreview ? 1u : 0u));
    const auto ensureTexture =
        [this, pAssetFileSystem, &bitmapLoadCache](
            const std::string &textureName,
            int16_t paletteId) -> const SpriteBillboardTexture *
    {
        const std::string textureKey = toLowerCopy(textureName) + "|" + std::to_string(static_cast<int>(paletteId));
        const auto existingTextureIt = m_entityBillboardTextures.find(textureKey);

        if (existingTextureIt != m_entityBillboardTextures.end())
        {
            if (bgfx::isValid(existingTextureIt->second.textureHandle))
            {
                return &existingTextureIt->second;
            }

            return nullptr;
        }

        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> texturePixels =
            loadSpriteBitmapPixelsBgra(
                *pAssetFileSystem,
                textureName,
                paletteId,
                textureWidth,
                textureHeight,
                bitmapLoadCache);

        SpriteBillboardTexture texture = {};

        if (texturePixels && textureWidth > 0 && textureHeight > 0)
        {
            texture.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(textureWidth),
                static_cast<uint16_t>(textureHeight),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_U_CLAMP
                    | BGFX_SAMPLER_V_CLAMP
                    | BGFX_SAMPLER_MIN_POINT
                    | BGFX_SAMPLER_MAG_POINT
                    | BGFX_SAMPLER_MIP_POINT,
                bgfx::copy(texturePixels->data(), static_cast<uint32_t>(texturePixels->size())));
            texture.width = textureWidth;
            texture.height = textureHeight;
        }

        const auto inserted =
            m_entityBillboardTextures.emplace(textureKey, texture);
        return bgfx::isValid(inserted.first->second.textureHandle) ? &inserted.first->second : nullptr;
    };

    const auto appendSpriteObjectBillboard =
        [this, &session, &forward, &ensureTexture, &drawItems](
            uint16_t objectDescriptionId,
            uint16_t spriteId,
            int x,
            int y,
            int z,
            uint32_t animationTimeTicks)
    {
        const Game::ObjectEntry *pObjectEntry = session.objectTable().get(objectDescriptionId);

        if (pObjectEntry == nullptr || (pObjectEntry->flags & 0x0001) != 0 || spriteId == 0)
        {
            return;
        }

        const Game::SpriteFrameTable *pSpriteFrameTable = session.entityBillboardSpriteFrameTable();

        if (pSpriteFrameTable == nullptr)
        {
            return;
        }

        const float deltaX = static_cast<float>(x) - m_cameraPosition.x;
        const float deltaY = static_cast<float>(y) - m_cameraPosition.y;
        const float deltaZ = static_cast<float>(z) - m_cameraPosition.z;
        const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

        if (cameraDepth <= 0.1f)
        {
            return;
        }

        const Game::SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteId, animationTimeTicks);

        if (pFrame == nullptr)
        {
            return;
        }

        const Game::ResolvedSpriteTexture resolvedTexture = Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
        const SpriteBillboardTexture *pTexture = ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

        if (pTexture == nullptr)
        {
            return;
        }

        const float spriteScale = std::max(pFrame->scale, 0.01f);
        BillboardDrawItem drawItem = {};
        drawItem.pTexture = pTexture;
        drawItem.center = {
            static_cast<float>(x),
            static_cast<float>(y),
            static_cast<float>(z) + static_cast<float>(pTexture->height) * spriteScale * 0.5f
        };
        drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
        drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
        drawItem.cameraDepth = cameraDepth;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItems.push_back(drawItem);
    };

    if (m_showEntities && m_showEntityBillboards)
    {
        const Game::SpriteFrameTable *pEntitySpriteFrameTable = session.entityBillboardSpriteFrameTable();

        if (pEntitySpriteFrameTable != nullptr)
        {
            for (const EditorEntityBillboardPreview &preview : session.entityBillboardPreviews())
            {
                if (preview.entityIndex >= sceneData.entities.size())
                {
                    continue;
                }

                const Game::OutdoorEntity &entity = sceneData.entities[preview.entityIndex].entity;

                if ((entity.aiAttributes & LevelDecorationInvisible) != 0
                    || (preview.flags & DecorationDescDontDraw) != 0
                    || preview.spriteId == 0)
                {
                    continue;
                }

                const float deltaX = static_cast<float>(preview.x) - m_cameraPosition.x;
                const float deltaY = static_cast<float>(preview.y) - m_cameraPosition.y;
                const float deltaZ = static_cast<float>(preview.z) - m_cameraPosition.z;
                const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

                if (cameraDepth <= 0.1f)
                {
                    continue;
                }

                const uint32_t animationOffsetTicks =
                    animationTicks + static_cast<uint32_t>(std::abs(preview.x + preview.y));
                const Game::SpriteFrameEntry *pFrame =
                    pEntitySpriteFrameTable->getFrame(preview.spriteId, animationOffsetTicks);

                if (pFrame == nullptr)
                {
                    continue;
                }

                const float facingRadians = static_cast<float>(preview.facing) * bx::kPi / 180.0f;
                const float angleToCamera = std::atan2(
                    static_cast<float>(preview.y) - m_cameraPosition.y,
                    static_cast<float>(preview.x) - m_cameraPosition.x);
                const float octantAngle = facingRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
                const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
                const Game::ResolvedSpriteTexture resolvedTexture =
                    Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
                const SpriteBillboardTexture *pTexture =
                    ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

                if (pTexture == nullptr)
                {
                    continue;
                }

                const float spriteScale = std::max(pFrame->scale, 0.01f);
                BillboardDrawItem drawItem = {};
                drawItem.pTexture = pTexture;
                drawItem.center = {
                    static_cast<float>(preview.x),
                    static_cast<float>(preview.y),
                    static_cast<float>(preview.z) + static_cast<float>(pTexture->height) * spriteScale * 0.5f
                };
                drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                drawItem.cameraDepth = cameraDepth;
                drawItem.mirrored = resolvedTexture.mirrored;
                drawItems.push_back(drawItem);
            }
        }
    }

    if (m_pendingEntityPlacementPreview)
    {
        const Game::DecorationEntry *pDecoration =
            session.decorationTable().get(session.pendingEntityDecorationListId());
        const Game::SpriteFrameTable *pEntitySpriteFrameTable = session.entityBillboardSpriteFrameTable();

        if (pDecoration != nullptr
            && pEntitySpriteFrameTable != nullptr
            && (pDecoration->flags & DecorationDescDontDraw) == 0
            && pDecoration->spriteId != 0)
        {
            const float deltaX = static_cast<float>(m_pendingEntityPlacementPreview->x) - m_cameraPosition.x;
            const float deltaY = static_cast<float>(m_pendingEntityPlacementPreview->y) - m_cameraPosition.y;
            const float deltaZ = static_cast<float>(m_pendingEntityPlacementPreview->z) - m_cameraPosition.z;
            const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

            if (cameraDepth > 0.1f)
            {
                const uint32_t animationOffsetTicks =
                    animationTicks
                    + static_cast<uint32_t>(
                        std::abs(m_pendingEntityPlacementPreview->x + m_pendingEntityPlacementPreview->y));
                const Game::SpriteFrameEntry *pFrame =
                    pEntitySpriteFrameTable->getFrame(pDecoration->spriteId, animationOffsetTicks);

                if (pFrame != nullptr)
                {
                    const Game::ResolvedSpriteTexture resolvedTexture =
                        Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
                    const SpriteBillboardTexture *pTexture =
                        ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

                    if (pTexture != nullptr)
                    {
                        const float spriteScale = std::max(pFrame->scale, 0.01f);
                        BillboardDrawItem drawItem = {};
                        drawItem.pTexture = pTexture;
                        drawItem.center = {
                            static_cast<float>(m_pendingEntityPlacementPreview->x),
                            static_cast<float>(m_pendingEntityPlacementPreview->y),
                            static_cast<float>(m_pendingEntityPlacementPreview->z)
                                + static_cast<float>(pTexture->height) * spriteScale * 0.5f
                        };
                        drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                        drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                        drawItem.cameraDepth = cameraDepth;
                        drawItem.mirrored = resolvedTexture.mirrored;
                        drawItems.push_back(drawItem);
                    }
                }
            }
        }
    }

    const Game::SpriteFrameTable *pActorSpriteFrameTable = session.actorBillboardSpriteFrameTable();

    if (pActorSpriteFrameTable != nullptr
        && ((m_showActors && m_showActorBillboards) || (m_showSpawns && m_showSpawnActorBillboards)))
    {
        for (const EditorActorBillboardPreview &preview : session.actorBillboardPreviews())
        {
            const bool isActor = preview.source == EditorActorBillboardPreview::Source::Actor;

            if ((isActor && (!m_showActors || !m_showActorBillboards))
                || (!isActor && (!m_showSpawns || !m_showSpawnActorBillboards)))
            {
                continue;
            }

            const float deltaX = static_cast<float>(preview.x) - m_cameraPosition.x;
            const float deltaY = static_cast<float>(preview.y) - m_cameraPosition.y;
            const float deltaZ = static_cast<float>(preview.z) - m_cameraPosition.z;
            const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

            if (cameraDepth <= 0.1f)
            {
                continue;
            }

            const Game::SpriteFrameEntry *pFrame =
                pActorSpriteFrameTable->getFrame(preview.spriteFrameIndex, 0);

            if (pFrame == nullptr)
            {
                continue;
            }

            const float angleToCamera = std::atan2(
                static_cast<float>(preview.y) - m_cameraPosition.y,
                static_cast<float>(preview.x) - m_cameraPosition.x);
            const float octantAngle = preview.yawRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
            const Game::ResolvedSpriteTexture resolvedTexture =
                Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
            const SpriteBillboardTexture *pTexture =
                ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr)
            {
                continue;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            BillboardDrawItem drawItem = {};
            drawItem.pTexture = pTexture;
            drawItem.center = {
                static_cast<float>(preview.x),
                static_cast<float>(preview.y),
                static_cast<float>(preview.z) + static_cast<float>(pTexture->height) * spriteScale * 0.5f
            };
            drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            drawItem.cameraDepth = cameraDepth;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItems.push_back(drawItem);
        }
    }

    if (m_showSpriteObjects)
    {
        for (const Game::MapDeltaSpriteObject &spriteObject : sceneData.initialState.spriteObjects)
        {
            const Game::ObjectEntry *pObjectEntry = session.objectTable().get(spriteObject.objectDescriptionId);
            const uint16_t spriteId = pObjectEntry != nullptr ? pObjectEntry->spriteId : spriteObject.spriteId;
            appendSpriteObjectBillboard(
                spriteObject.objectDescriptionId,
                spriteId,
                spriteObject.x,
                spriteObject.y,
                spriteObject.z,
                static_cast<uint32_t>(spriteObject.timeSinceCreated) * 8u);
        }
    }

    if (m_pendingSpriteObjectPlacementPreview)
    {
        const Game::ObjectEntry *pObjectEntry =
            session.objectTable().get(session.pendingSpriteObjectDescriptionId());
        const uint16_t spriteId = pObjectEntry != nullptr ? pObjectEntry->spriteId : 0;
        appendSpriteObjectBillboard(
            session.pendingSpriteObjectDescriptionId(),
            spriteId,
            m_pendingSpriteObjectPlacementPreview->x,
            m_pendingSpriteObjectPlacementPreview->y,
            m_pendingSpriteObjectPlacementPreview->z,
            animationTicks);
    }

    std::sort(drawItems.begin(), drawItems.end(), [](const BillboardDrawItem &left, const BillboardDrawItem &right)
    {
        return left.cameraDepth > right.cameraDepth;
    });

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        if (drawItem.pTexture == nullptr || !bgfx::isValid(drawItem.pTexture->textureHandle))
        {
            continue;
        }

        if (bgfx::getAvailTransientVertexBuffer(6, TexturedPreviewVertex::ms_layout) < 6)
        {
            continue;
        }

        const float halfWidth = drawItem.worldWidth * 0.5f;
        const float halfHeight = drawItem.worldHeight * 0.5f;
        const bx::Vec3 right = vecScale(cameraRight, halfWidth);
        const bx::Vec3 up = vecScale(cameraUp, halfHeight);
        const bx::Vec3 bottomLeft = {
            drawItem.center.x - right.x - up.x,
            drawItem.center.y - right.y - up.y,
            drawItem.center.z - right.z - up.z
        };
        const bx::Vec3 topLeft = {
            drawItem.center.x - right.x + up.x,
            drawItem.center.y - right.y + up.y,
            drawItem.center.z - right.z + up.z
        };
        const bx::Vec3 topRight = {
            drawItem.center.x + right.x + up.x,
            drawItem.center.y + right.y + up.y,
            drawItem.center.z + right.z + up.z
        };
        const bx::Vec3 bottomRight = {
            drawItem.center.x + right.x - up.x,
            drawItem.center.y + right.y - up.y,
            drawItem.center.z + right.z - up.z
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
        const std::array<TexturedPreviewVertex, 6> vertices = {{
            {bottomLeft.x, bottomLeft.y, bottomLeft.z, u0, 1.0f},
            {topLeft.x, topLeft.y, topLeft.z, u0, 0.0f},
            {topRight.x, topRight.y, topRight.z, u1, 0.0f},
            {bottomLeft.x, bottomLeft.y, bottomLeft.z, u0, 1.0f},
            {topRight.x, topRight.y, topRight.z, u1, 0.0f},
            {bottomRight.x, bottomRight.y, bottomRight.z, u1, 1.0f}
        }};

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedPreviewVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedPreviewVertex)));

        float transform[16] = {};
        bx::mtxIdentity(transform);
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, 6);
        bgfx::setTexture(0, m_textureSamplerHandle, drawItem.pTexture->textureHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_BLEND_ALPHA
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_texturedProgramHandle);
    }
}

void EditorOutdoorViewport::submitMarkerGeometry(
    const EditorSession &session,
    const EditorDocument &document,
    const EditorSelection &selection)
{
    std::vector<PreviewVertex> vertices;
    std::vector<PreviewVertex> fillVertices;
    std::vector<PreviewVertex> xrayVertices;
    std::vector<PreviewVertex> xrayFillVertices;
    m_markerCandidates.clear();
    const auto tryGetCachedBillboardSize =
        [this](const std::string &textureName, int16_t paletteId, float scale, float &worldWidth, float &worldHeight)
    {
        const std::string textureKey = toLowerCopy(textureName) + "|" + std::to_string(static_cast<int>(paletteId));
        const auto textureIt = m_entityBillboardTextures.find(textureKey);

        if (textureIt == m_entityBillboardTextures.end() || !bgfx::isValid(textureIt->second.textureHandle))
        {
            return false;
        }

        worldWidth = static_cast<float>(textureIt->second.width) * scale;
        worldHeight = static_cast<float>(textureIt->second.height) * scale;
        return worldWidth > 0.0f && worldHeight > 0.0f;
    };

    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const auto appendTerrainCellOutline =
        [&vertices, &outdoorGeometry](int cellX, int cellY, float zOffset, uint32_t color)
    {
        if (cellX < 0
            || cellY < 0
            || cellX >= (Game::OutdoorMapData::TerrainWidth - 1)
            || cellY >= (Game::OutdoorMapData::TerrainHeight - 1))
        {
            return;
        }

        const size_t topLeftIndex = static_cast<size_t>(cellY * Game::OutdoorMapData::TerrainWidth + cellX);
        const size_t topRightIndex = topLeftIndex + 1;
        const size_t bottomLeftIndex = static_cast<size_t>((cellY + 1) * Game::OutdoorMapData::TerrainWidth + cellX);
        const size_t bottomRightIndex = bottomLeftIndex + 1;
        const bx::Vec3 topLeft = worldPointFromTerrainGrid(cellX, cellY, outdoorGeometry.heightMap[topLeftIndex]);
        const bx::Vec3 topRight = worldPointFromTerrainGrid(cellX + 1, cellY, outdoorGeometry.heightMap[topRightIndex]);
        const bx::Vec3 bottomLeft =
            worldPointFromTerrainGrid(cellX, cellY + 1, outdoorGeometry.heightMap[bottomLeftIndex]);
        const bx::Vec3 bottomRight =
            worldPointFromTerrainGrid(cellX + 1, cellY + 1, outdoorGeometry.heightMap[bottomRightIndex]);

        vertices.push_back({topLeft.x, topLeft.y, topLeft.z + zOffset, color});
        vertices.push_back({topRight.x, topRight.y, topRight.z + zOffset, color});
        vertices.push_back({topRight.x, topRight.y, topRight.z + zOffset, color});
        vertices.push_back({bottomRight.x, bottomRight.y, bottomRight.z + zOffset, color});
        vertices.push_back({bottomRight.x, bottomRight.y, bottomRight.z + zOffset, color});
        vertices.push_back({bottomLeft.x, bottomLeft.y, bottomLeft.z + zOffset, color});
        vertices.push_back({bottomLeft.x, bottomLeft.y, bottomLeft.z + zOffset, color});
        vertices.push_back({topLeft.x, topLeft.y, topLeft.z + zOffset, color});
    };

    if (m_showTerrainGrid)
    {
        const uint32_t terrainGridColor = makeAbgr(144, 164, 192);

        for (int gridY = 0; gridY < Game::OutdoorMapData::TerrainHeight; ++gridY)
        {
            for (int gridX = 0; gridX < (Game::OutdoorMapData::TerrainWidth - 1); ++gridX)
            {
                const size_t startIndex = static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
                const size_t endIndex = startIndex + 1;
                const bx::Vec3 start =
                    worldPointFromTerrainGrid(gridX, gridY, outdoorGeometry.heightMap[startIndex]);
                const bx::Vec3 end =
                    worldPointFromTerrainGrid(gridX + 1, gridY, outdoorGeometry.heightMap[endIndex]);
                vertices.push_back({start.x, start.y, start.z + 4.0f, terrainGridColor});
                vertices.push_back({end.x, end.y, end.z + 4.0f, terrainGridColor});
            }
        }

        for (int gridX = 0; gridX < Game::OutdoorMapData::TerrainWidth; ++gridX)
        {
            for (int gridY = 0; gridY < (Game::OutdoorMapData::TerrainHeight - 1); ++gridY)
            {
                const size_t startIndex = static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
                const size_t endIndex = startIndex + Game::OutdoorMapData::TerrainWidth;
                const bx::Vec3 start =
                    worldPointFromTerrainGrid(gridX, gridY, outdoorGeometry.heightMap[startIndex]);
                const bx::Vec3 end =
                    worldPointFromTerrainGrid(gridX, gridY + 1, outdoorGeometry.heightMap[endIndex]);
                vertices.push_back({start.x, start.y, start.z + 4.0f, terrainGridColor});
                vertices.push_back({end.x, end.y, end.z + 4.0f, terrainGridColor});
            }
        }
    }

    if (m_showEntities)
    {
        const uint32_t entityColor = makeAbgr(255, 208, 64);
        const uint32_t selectedEntityColor = makeAbgr(255, 255, 255);
        const uint32_t eventEntityColor = makeAbgr(96, 255, 255);

        for (size_t entityIndex = 0; entityIndex < sceneData.entities.size(); ++entityIndex)
        {
            const Game::OutdoorSceneEntity &entity = sceneData.entities[entityIndex];
            const bool isSelected =
                selection.kind == EditorSelectionKind::Entity && selection.index == entityIndex;
            const bx::Vec3 center =
                worldPointFromLegacyPosition(entity.entity.x, entity.entity.y, entity.entity.z);

            if (!m_showEntityBillboards || isSelected)
            {
                appendCrossMarker(vertices, center, 96.0f, 192.0f, isSelected ? selectedEntityColor : entityColor);
            }
            MarkerCandidate candidate = {};
            candidate.selectionKind = EditorSelectionKind::Entity;
            candidate.selectionIndex = entityIndex;
            candidate.worldPosition = {center.x, center.y, center.z + 96.0f};
            candidate.pickRadiusPixels = 18.0f;

            if (m_showEntityBillboards)
            {
                const Game::SpriteFrameTable *pEntitySpriteFrameTable = session.entityBillboardSpriteFrameTable();
                const EditorEntityBillboardPreview *pPreview = nullptr;

                for (const EditorEntityBillboardPreview &preview : session.entityBillboardPreviews())
                {
                    if (preview.entityIndex == entityIndex)
                    {
                        pPreview = &preview;
                        break;
                    }
                }

                if (pEntitySpriteFrameTable != nullptr
                    && pPreview != nullptr
                    && pPreview->spriteId != 0
                    && (pPreview->flags & DecorationDescDontDraw) == 0)
                {
                    const uint32_t animationTicks = currentAnimationTicks();
                    const uint32_t animationOffsetTicks =
                        animationTicks + static_cast<uint32_t>(std::abs(pPreview->x + pPreview->y));
                    const Game::SpriteFrameEntry *pFrame =
                        pEntitySpriteFrameTable->getFrame(pPreview->spriteId, animationOffsetTicks);

                    if (pFrame != nullptr)
                    {
                        const float facingRadians = static_cast<float>(pPreview->facing) * bx::kPi / 180.0f;
                        const float angleToCamera = std::atan2(
                            static_cast<float>(pPreview->y) - m_cameraPosition.y,
                            static_cast<float>(pPreview->x) - m_cameraPosition.x);
                        const float octantAngle = facingRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
                        const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
                        const Game::ResolvedSpriteTexture resolvedTexture =
                            Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
                        const float spriteScale = std::max(pFrame->scale, 0.01f);

                        if (tryGetCachedBillboardSize(
                                resolvedTexture.textureName,
                                pFrame->paletteId,
                                spriteScale,
                                candidate.billboardWorldWidth,
                                candidate.billboardWorldHeight))
                        {
                            candidate.hasBillboardBounds = true;
                        }
                    }
                }
            }

            m_markerCandidates.push_back(candidate);

            if (m_showEventMarkers && (entity.entity.eventIdPrimary != 0 || entity.entity.eventIdSecondary != 0))
            {
                const bx::Vec3 eventMarkerCenter = {center.x, center.y, center.z + 192.0f};
                appendCrossMarker(vertices, eventMarkerCenter, 48.0f, 64.0f, eventEntityColor);
            }
        }
    }

    if (m_showSpawns)
    {
        const uint32_t spawnColor = makeAbgr(96, 192, 255);
        const uint32_t actorSpawnColor = makeAbgr(96, 255, 96);
        const uint32_t selectedSpawnColor = makeAbgr(255, 255, 255);

        for (size_t spawnIndex = 0; spawnIndex < sceneData.spawns.size(); ++spawnIndex)
        {
            const Game::OutdoorSceneSpawn &spawn = sceneData.spawns[spawnIndex];
            const bool isSelected =
                selection.kind == EditorSelectionKind::Spawn && selection.index == spawnIndex;
            const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.spawn.radius, 96));
            const bx::Vec3 center = {
                static_cast<float>(spawn.spawn.x),
                static_cast<float>(spawn.spawn.y),
                std::max(
                    static_cast<float>(spawn.spawn.z),
                    Game::sampleOutdoorTerrainHeight(
                        outdoorGeometry,
                        static_cast<float>(spawn.spawn.x),
                        static_cast<float>(spawn.spawn.y)))
                    + halfExtent
            };

            const uint32_t markerColor =
                spawn.spawn.typeId == 3 ? actorSpawnColor : spawnColor;
            appendCrossMarker(
                vertices,
                center,
                halfExtent,
                halfExtent * 2.0f,
                isSelected ? selectedSpawnColor : markerColor);

            const float spawnPickRadius =
                spawn.spawn.typeId == 3 ? 34.0f : 26.0f;
            m_markerCandidates.push_back({EditorSelectionKind::Spawn, spawnIndex, center, spawnPickRadius});
        }
    }

    if (m_showActors)
    {
        const uint32_t actorColor = makeAbgr(224, 100, 80);
        const uint32_t selectedActorColor = makeAbgr(255, 255, 255);

        for (size_t actorIndex = 0; actorIndex < sceneData.initialState.actors.size(); ++actorIndex)
        {
            const Game::MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];
            const bool isSelected =
                selection.kind == EditorSelectionKind::Actor && selection.index == actorIndex;
            const float halfExtent = static_cast<float>(std::max<uint16_t>(actor.radius, 96));
            const float height = static_cast<float>(std::max<uint16_t>(actor.height, 256));
            const bx::Vec3 center = worldPointFromLegacyPosition(actor.x, actor.y, actor.z);

            appendCrossMarker(vertices, center, halfExtent, height, isSelected ? selectedActorColor : actorColor);
            MarkerCandidate candidate = {};
            candidate.selectionKind = EditorSelectionKind::Actor;
            candidate.selectionIndex = actorIndex;
            candidate.worldPosition = {center.x, center.y, center.z + height * 0.5f};
            candidate.pickRadiusPixels = 28.0f;

            if (m_showActorBillboards)
            {
                const Game::SpriteFrameTable *pActorSpriteFrameTable = session.actorBillboardSpriteFrameTable();
                const EditorActorBillboardPreview *pPreview = nullptr;

                for (const EditorActorBillboardPreview &preview : session.actorBillboardPreviews())
                {
                    if (preview.source == EditorActorBillboardPreview::Source::Actor
                        && preview.sourceIndex == actorIndex)
                    {
                        pPreview = &preview;
                        break;
                    }
                }

                if (pActorSpriteFrameTable != nullptr && pPreview != nullptr)
                {
                    const Game::SpriteFrameEntry *pFrame = pActorSpriteFrameTable->getFrame(pPreview->spriteFrameIndex, 0);

                    if (pFrame != nullptr)
                    {
                        const float angleToCamera = std::atan2(
                            static_cast<float>(pPreview->y) - m_cameraPosition.y,
                            static_cast<float>(pPreview->x) - m_cameraPosition.x);
                        const float octantAngle = pPreview->yawRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
                        const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
                        const Game::ResolvedSpriteTexture resolvedTexture =
                            Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
                        const float spriteScale = std::max(pFrame->scale, 0.01f);

                        if (tryGetCachedBillboardSize(
                                resolvedTexture.textureName,
                                pFrame->paletteId,
                                spriteScale,
                                candidate.billboardWorldWidth,
                                candidate.billboardWorldHeight))
                        {
                            candidate.hasBillboardBounds = true;
                        }
                    }
                }
            }

            m_markerCandidates.push_back(candidate);
        }
    }

    if (m_showSpriteObjects)
    {
        const uint32_t spriteObjectColor = makeAbgr(216, 96, 255);
        const uint32_t selectedSpriteObjectColor = makeAbgr(255, 255, 255);

        for (size_t objectIndex = 0; objectIndex < sceneData.initialState.spriteObjects.size(); ++objectIndex)
        {
            const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[objectIndex];
            const bool isSelected =
                selection.kind == EditorSelectionKind::SpriteObject && selection.index == objectIndex;
            const bx::Vec3 center = worldPointFromLegacyPosition(spriteObject.x, spriteObject.y, spriteObject.z);
            appendCrossMarker(
                vertices,
                center,
                72.0f,
                144.0f,
                isSelected ? selectedSpriteObjectColor : spriteObjectColor);
            MarkerCandidate candidate = {};
            candidate.selectionKind = EditorSelectionKind::SpriteObject;
            candidate.selectionIndex = objectIndex;
            candidate.worldPosition = {center.x, center.y, center.z + 72.0f};
            candidate.pickRadiusPixels = 18.0f;

            const Game::ObjectEntry *pObjectEntry = session.objectTable().get(spriteObject.objectDescriptionId);
            const uint16_t spriteId = pObjectEntry != nullptr ? pObjectEntry->spriteId : spriteObject.spriteId;
            const Game::SpriteFrameTable *pSpriteFrameTable = session.entityBillboardSpriteFrameTable();

            if (m_showSpriteObjects && pSpriteFrameTable != nullptr && spriteId != 0)
            {
                const Game::SpriteFrameEntry *pFrame =
                    pSpriteFrameTable->getFrame(spriteId, static_cast<uint32_t>(spriteObject.timeSinceCreated) * 8u);

                if (pFrame != nullptr)
                {
                    const Game::ResolvedSpriteTexture resolvedTexture =
                        Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
                    const float spriteScale = std::max(pFrame->scale, 0.01f);

                    if (tryGetCachedBillboardSize(
                            resolvedTexture.textureName,
                            pFrame->paletteId,
                            spriteScale,
                            candidate.billboardWorldWidth,
                            candidate.billboardWorldHeight))
                    {
                        candidate.hasBillboardBounds = true;
                    }
                }
            }

            m_markerCandidates.push_back(candidate);
        }
    }

    if (selection.kind == EditorSelectionKind::Terrain)
    {
        int cellX = 0;
        int cellY = 0;

        if (decodeSelectedTerrainCell(selection, cellX, cellY)
            && cellX < (Game::OutdoorMapData::TerrainWidth - 1)
            && cellY < (Game::OutdoorMapData::TerrainHeight - 1))
        {
            const uint32_t terrainSelectionColor = makeAbgr(96, 255, 255);
            appendTerrainCellOutline(cellX, cellY, 16.0f, terrainSelectionColor);
        }
    }

    if (m_hoverTerrainValid && m_placementKind == EditorSelectionKind::Terrain)
    {
        uint32_t hoverColor = makeAbgr(255, 214, 96);

        if (session.terrainSculptEnabled())
        {
            switch (session.terrainSculptMode())
            {
            case EditorTerrainSculptMode::Flatten:
                hoverColor = makeAbgr(96, 220, 255);
                break;

            case EditorTerrainSculptMode::Smooth:
                hoverColor = makeAbgr(176, 216, 255);
                break;

            case EditorTerrainSculptMode::Noise:
                hoverColor = makeAbgr(220, 196, 120);
                break;

            case EditorTerrainSculptMode::Ramp:
                hoverColor = makeAbgr(196, 156, 255);
                break;

            case EditorTerrainSculptMode::Lower:
                hoverColor = makeAbgr(255, 140, 96);
                break;

            case EditorTerrainSculptMode::Raise:
            default:
                hoverColor = makeAbgr(144, 255, 112);
                break;
            }
        }

        const bool hoverMatchesSelection =
            selection.kind == EditorSelectionKind::Terrain
            && selection.index == flattenTerrainCellIndex(m_hoverTerrainCellX, m_hoverTerrainCellY);

        if (session.terrainSculptEnabled())
        {
            const int radius = std::max(session.terrainSculptRadius(), 0);

            if (session.terrainSculptMode() == EditorTerrainSculptMode::Ramp
                && m_activeTerrainSculpt.active
                && m_activeTerrainSculpt.anchorSampleX != std::numeric_limits<int>::min())
            {
                rasterizeTerrainLine(
                    m_activeTerrainSculpt.anchorSampleX,
                    m_activeTerrainSculpt.anchorSampleY,
                    m_hoverTerrainCellX,
                    m_hoverTerrainCellY,
                    [&](int stepX, int stepY)
                    {
                        forEachTerrainBrushCell(
                            stepX,
                            stepY,
                            radius,
                            [&](int targetX, int targetY, float, int)
                            {
                                appendTerrainCellOutline(targetX, targetY, 10.0f, hoverColor);
                            });
                    });
            }
            else
            {
                for (int offsetY = -radius; offsetY <= radius; ++offsetY)
                {
                    for (int offsetX = -radius; offsetX <= radius; ++offsetX)
                    {
                        const int targetX = m_hoverTerrainCellX + offsetX;
                        const int targetY = m_hoverTerrainCellY + offsetY;
                        const float distance = std::sqrt(static_cast<float>(offsetX * offsetX + offsetY * offsetY));

                        if (distance > static_cast<float>(radius))
                        {
                            continue;
                        }

                        appendTerrainCellOutline(targetX, targetY, 10.0f, hoverColor);
                    }
                }
            }
        }
        else if (session.terrainPaintEnabled() && session.terrainPaintMode() == EditorTerrainPaintMode::Rectangle)
        {
            const int startX = m_activeTerrainPaint.active ? m_activeTerrainPaint.anchorCellX : m_hoverTerrainCellX;
            const int startY = m_activeTerrainPaint.active ? m_activeTerrainPaint.anchorCellY : m_hoverTerrainCellY;
            const int minX = std::min(startX, m_hoverTerrainCellX);
            const int maxX = std::max(startX, m_hoverTerrainCellX);
            const int minY = std::min(startY, m_hoverTerrainCellY);
            const int maxY = std::max(startY, m_hoverTerrainCellY);

            for (int targetY = minY; targetY <= maxY; ++targetY)
            {
                for (int targetX = minX; targetX <= maxX; ++targetX)
                {
                    appendTerrainCellOutline(targetX, targetY, 10.0f, hoverColor);
                }
            }
        }
        else if (session.terrainPaintEnabled() && session.terrainPaintMode() == EditorTerrainPaintMode::Brush)
        {
            const int radius = std::max(session.terrainPaintRadius(), 0);

            forEachTerrainBrushCell(
                m_hoverTerrainCellX,
                m_hoverTerrainCellY,
                radius,
                [&](int targetX, int targetY, float, int)
                {
                    appendTerrainCellOutline(targetX, targetY, 10.0f, hoverColor);
                });
        }
        else if (!hoverMatchesSelection)
        {
            appendTerrainCellOutline(m_hoverTerrainCellX, m_hoverTerrainCellY, 10.0f, hoverColor);
        }
    }

    if (selection.kind == EditorSelectionKind::BModel && selection.index < outdoorGeometry.bmodels.size())
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[selection.index];
        const uint32_t bmodelSelectionColor = makeAbgr(255, 224, 96);

        for (const Game::OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.vertexIndices.size() < 2)
            {
                continue;
            }

            for (size_t vertexIndex = 0; vertexIndex < face.vertexIndices.size(); ++vertexIndex)
            {
                const uint16_t startIndex = face.vertexIndices[vertexIndex];
                const uint16_t endIndex = face.vertexIndices[(vertexIndex + 1) % face.vertexIndices.size()];

                if (startIndex >= bmodel.vertices.size() || endIndex >= bmodel.vertices.size())
                {
                    continue;
                }

                const bx::Vec3 start = Game::outdoorBModelVertexToWorld(bmodel.vertices[startIndex]);
                const bx::Vec3 end = Game::outdoorBModelVertexToWorld(bmodel.vertices[endIndex]);
                vertices.push_back({start.x, start.y, start.z + 8.0f, bmodelSelectionColor});
                vertices.push_back({end.x, end.y, end.z + 8.0f, bmodelSelectionColor});
            }
        }

        if (const std::optional<bx::Vec3> bmodelCenter = selectedWorldPosition(document, selection))
        {
            const float radius = bmodelRotationHandleRadius(bmodel);
            bx::Vec3 xAxisWorld = {1.0f, 0.0f, 0.0f};
            bx::Vec3 yAxisWorld = {0.0f, 1.0f, 0.0f};
            bx::Vec3 zAxisWorld = {0.0f, 0.0f, 1.0f};
            computeTransformBasis(document, selection, m_transformSpaceMode, xAxisWorld, yAxisWorld, zAxisWorld);
            const auto appendRotationRing =
                [&vertices, bmodelCenter, radius](const bx::Vec3 &axis, uint32_t color)
            {
                for (int segmentIndex = 0; segmentIndex < GizmoRotationSegments; ++segmentIndex)
                {
                    const float angle0 =
                        (static_cast<float>(segmentIndex) / static_cast<float>(GizmoRotationSegments)) * bx::kPi2;
                    const float angle1 =
                        (static_cast<float>(segmentIndex + 1) / static_cast<float>(GizmoRotationSegments)) * bx::kPi2;
                    bx::Vec3 point0 = *bmodelCenter;
                    bx::Vec3 point1 = *bmodelCenter;

                    if (std::fabs(axis.x) > 0.5f)
                    {
                        point0.y += std::cos(angle0) * radius;
                        point0.z += std::sin(angle0) * radius;
                        point1.y += std::cos(angle1) * radius;
                        point1.z += std::sin(angle1) * radius;
                    }
                    else if (std::fabs(axis.y) > 0.5f)
                    {
                        point0.x += std::cos(angle0) * radius;
                        point0.z += std::sin(angle0) * radius;
                        point1.x += std::cos(angle1) * radius;
                        point1.z += std::sin(angle1) * radius;
                    }
                    else
                    {
                        point0.x += std::cos(angle0) * radius;
                        point0.y += std::sin(angle0) * radius;
                        point1.x += std::cos(angle1) * radius;
                        point1.y += std::sin(angle1) * radius;
                    }

                    vertices.push_back({point0.x, point0.y, point0.z, color});
                    vertices.push_back({point1.x, point1.y, point1.z, color});
                }
            };

            if (m_transformGizmoMode == TransformGizmoMode::Rotate)
            {
                appendRotationRing(xAxisWorld, makeAbgr(255, 96, 96));
                appendRotationRing(yAxisWorld, makeAbgr(96, 255, 96));
                appendRotationRing(zAxisWorld, makeAbgr(96, 160, 255));
            }
        }
    }

    if (m_showEventMarkers)
    {
        const uint32_t defaultEventColor = makeAbgr(96, 255, 255);
        const uint32_t explicitEventColor = makeAbgr(255, 176, 96);

        for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
        {
            const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
            const std::optional<uint16_t> defaultEventId = session.derivedBModelDefaultEventId(bmodelIndex);

            if (defaultEventId)
            {
                float centerX = 0.0f;
                float centerY = 0.0f;
                float centerZ = 0.0f;
                int vertexCount = 0;

                for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
                {
                    centerX += static_cast<float>(vertex.x);
                    centerY += static_cast<float>(vertex.y);
                    centerZ += static_cast<float>(vertex.z);
                    ++vertexCount;
                }

                if (vertexCount > 0)
                {
                    const float invCount = 1.0f / static_cast<float>(vertexCount);
                    appendCrossMarker(
                        vertices,
                        {centerX * invCount, centerY * invCount, centerZ * invCount + 96.0f},
                        72.0f,
                        96.0f,
                        defaultEventColor);
                }
            }

            for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
            {
                const uint16_t eventId = session.effectiveOutdoorFaceEventId(bmodelIndex, faceIndex);

                if (eventId == 0 || (defaultEventId && eventId == *defaultEventId))
                {
                    continue;
                }

                Game::OutdoorFaceGeometryData geometry = {};

                if (!Game::buildOutdoorFaceGeometry(bmodel, bmodelIndex, bmodel.faces[faceIndex], faceIndex, geometry)
                    || geometry.vertices.empty())
                {
                    continue;
                }

                bx::Vec3 center = {0.0f, 0.0f, 0.0f};

                for (const bx::Vec3 &vertex : geometry.vertices)
                {
                    center.x += vertex.x;
                    center.y += vertex.y;
                    center.z += vertex.z;
                }

                const float invCount = 1.0f / static_cast<float>(geometry.vertices.size());
                center.x *= invCount;
                center.y *= invCount;
                center.z *= invCount;
                appendCrossMarker(vertices, {center.x, center.y, center.z + 56.0f}, 48.0f, 64.0f, explicitEventColor);
            }
        }
    }

    const uint32_t faceSelectionColor = makeAbgr(255, 96, 255);
    const uint32_t facePrimarySelectionColor = makeAbgr(255, 255, 255);
    const uint32_t faceSelectionFillColor = makeAbgrAlpha(255, 96, 255, 72);
    const uint32_t facePrimarySelectionFillColor = makeAbgrAlpha(255, 240, 96, 84);

    for (size_t flatIndex : session.selectedInteractiveFaceIndices())
    {
        size_t bmodelIndex = 0;
        size_t faceIndex = 0;

        if (decodeSelectedInteractiveFace(document, {EditorSelectionKind::InteractiveFace, flatIndex}, bmodelIndex, faceIndex))
        {
            Game::OutdoorFaceGeometryData geometry = {};

            if (Game::buildOutdoorFaceGeometry(
                    outdoorGeometry.bmodels[bmodelIndex],
                    bmodelIndex,
                    outdoorGeometry.bmodels[bmodelIndex].faces[faceIndex],
                    faceIndex,
                    geometry))
            {
                const uint32_t color =
                    selection.kind == EditorSelectionKind::InteractiveFace && selection.index == flatIndex
                        ? facePrimarySelectionColor
                        : faceSelectionColor;
                const uint32_t fillColor =
                    selection.kind == EditorSelectionKind::InteractiveFace && selection.index == flatIndex
                        ? facePrimarySelectionFillColor
                        : faceSelectionFillColor;

                for (size_t vertexIndex = 0; vertexIndex < geometry.vertices.size(); ++vertexIndex)
                {
                    const bx::Vec3 &start = geometry.vertices[vertexIndex];
                    const bx::Vec3 &end = geometry.vertices[(vertexIndex + 1) % geometry.vertices.size()];
                    xrayVertices.push_back({start.x, start.y, start.z + 8.0f, color});
                    xrayVertices.push_back({end.x, end.y, end.z + 8.0f, color});
                }

                if (geometry.vertices.size() >= 3)
                {
                    const bx::Vec3 base = geometry.vertices[0];

                    for (size_t vertexIndex = 1; vertexIndex + 1 < geometry.vertices.size(); ++vertexIndex)
                    {
                        const bx::Vec3 &middle = geometry.vertices[vertexIndex];
                        const bx::Vec3 &end = geometry.vertices[vertexIndex + 1];
                        xrayFillVertices.push_back({base.x, base.y, base.z + 6.0f, fillColor});
                        xrayFillVertices.push_back({middle.x, middle.y, middle.z + 6.0f, fillColor});
                        xrayFillVertices.push_back({end.x, end.y, end.z + 6.0f, fillColor});
                    }
                }
            }
        }
    }

    if (m_showChestLinks && selection.kind == EditorSelectionKind::Chest)
    {
        const uint32_t chestLinkColor = makeAbgr(255, 176, 96);

        for (const EditorChestLink &link : session.findChestLinks(selection.index))
        {
            if (link.kind == EditorChestLink::Kind::Entity)
            {
                if (link.entityIndex >= sceneData.entities.size())
                {
                    continue;
                }

                const Game::OutdoorEntity &entity = sceneData.entities[link.entityIndex].entity;
                const bx::Vec3 center = worldPointFromLegacyPosition(entity.x, entity.y, entity.z);
                appendCrossMarker(vertices, {center.x, center.y, center.z + 256.0f}, 96.0f, 128.0f, chestLinkColor);
            }
            else if (link.bmodelIndex < outdoorGeometry.bmodels.size()
                && link.faceIndex < outdoorGeometry.bmodels[link.bmodelIndex].faces.size())
            {
                Game::OutdoorFaceGeometryData geometry = {};

                if (!Game::buildOutdoorFaceGeometry(
                        outdoorGeometry.bmodels[link.bmodelIndex],
                        link.bmodelIndex,
                        outdoorGeometry.bmodels[link.bmodelIndex].faces[link.faceIndex],
                        link.faceIndex,
                        geometry))
                {
                    continue;
                }

                for (size_t vertexIndex = 0; vertexIndex < geometry.vertices.size(); ++vertexIndex)
                {
                    const bx::Vec3 &start = geometry.vertices[vertexIndex];
                    const bx::Vec3 &end = geometry.vertices[(vertexIndex + 1) % geometry.vertices.size()];
                    xrayVertices.push_back({start.x, start.y, start.z + 10.0f, chestLinkColor});
                    xrayVertices.push_back({end.x, end.y, end.z + 10.0f, chestLinkColor});
                }
            }
        }
    }

    if (const std::optional<bx::Vec3> selectedPosition = selectedWorldPosition(document, selection))
    {
        const bx::Vec3 center = *selectedPosition;
        const bool showTranslateGizmo =
            selection.kind != EditorSelectionKind::BModel || m_transformGizmoMode == TransformGizmoMode::Translate;
        bx::Vec3 xAxisWorld = {1.0f, 0.0f, 0.0f};
        bx::Vec3 yAxisWorld = {0.0f, 1.0f, 0.0f};
        bx::Vec3 zAxisWorld = {0.0f, 0.0f, 1.0f};
        computeTransformBasis(document, selection, m_transformSpaceMode, xAxisWorld, yAxisWorld, zAxisWorld);

        if (showTranslateGizmo)
        {
            const uint32_t xAxisColor = makeAbgr(255, 96, 96);
            const uint32_t yAxisColor = makeAbgr(96, 255, 96);
            const uint32_t zAxisColor = makeAbgr(96, 160, 255);
            const uint32_t planeColor = makeAbgr(255, 224, 96);
            const float axisLength = GizmoAxisWorldLength;
            const bx::Vec3 xAxisEnd = vecAdd(center, vecScale(xAxisWorld, axisLength));
            const bx::Vec3 yAxisEnd = vecAdd(center, vecScale(yAxisWorld, axisLength));
            const bx::Vec3 zAxisEnd = vecAdd(center, vecScale(zAxisWorld, axisLength));
            const float planeExtent = axisLength * 0.35f;
            const bx::Vec3 planeX = vecAdd(center, vecScale(xAxisWorld, planeExtent));
            const bx::Vec3 planeY = vecAdd(center, vecScale(yAxisWorld, planeExtent));
            const bx::Vec3 planeXY = vecAdd(planeX, vecScale(yAxisWorld, planeExtent));

            vertices.push_back({center.x, center.y, center.z, xAxisColor});
            vertices.push_back({xAxisEnd.x, xAxisEnd.y, xAxisEnd.z, xAxisColor});
            vertices.push_back({center.x, center.y, center.z, yAxisColor});
            vertices.push_back({yAxisEnd.x, yAxisEnd.y, yAxisEnd.z, yAxisColor});
            vertices.push_back({center.x, center.y, center.z, zAxisColor});
            vertices.push_back({zAxisEnd.x, zAxisEnd.y, zAxisEnd.z, zAxisColor});

            vertices.push_back({center.x, center.y, center.z, planeColor});
            vertices.push_back({planeX.x, planeX.y, planeX.z, planeColor});
            vertices.push_back({planeX.x, planeX.y, planeX.z, planeColor});
            vertices.push_back({planeXY.x, planeXY.y, planeXY.z, planeColor});
            vertices.push_back({planeXY.x, planeXY.y, planeXY.z, planeColor});
            vertices.push_back({planeY.x, planeY.y, planeY.z, planeColor});
            vertices.push_back({planeY.x, planeY.y, planeY.z, planeColor});
            vertices.push_back({center.x, center.y, center.z, planeColor});
        }

        appendCrossMarker(vertices, center, 144.0f, 256.0f, makeAbgr(255, 255, 255));
    }

    if (vertices.empty() && fillVertices.empty() && xrayVertices.empty() && xrayFillVertices.empty())
    {
        return;
    }

    if (!fillVertices.empty()
        && bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(fillVertices.size()), PreviewVertex::ms_layout)
            < fillVertices.size())
    {
        return;
    }

    if (!xrayFillVertices.empty()
        && bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(xrayFillVertices.size()),
                PreviewVertex::ms_layout)
            < xrayFillVertices.size())
    {
        return;
    }

    if (!vertices.empty()
        && bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), PreviewVertex::ms_layout)
            < vertices.size())
    {
        return;
    }

    if (!xrayVertices.empty()
        && bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(xrayVertices.size()),
                PreviewVertex::ms_layout)
            < xrayVertices.size())
    {
        return;
    }

    float transform[16] = {};
    bx::mtxIdentity(transform);

    if (!fillVertices.empty())
    {
        bgfx::TransientVertexBuffer fillVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &fillVertexBuffer,
            static_cast<uint32_t>(fillVertices.size()),
            PreviewVertex::ms_layout);
        std::memcpy(fillVertexBuffer.data, fillVertices.data(), fillVertices.size() * sizeof(PreviewVertex));
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &fillVertexBuffer, 0, static_cast<uint32_t>(fillVertices.size()));
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_BLEND_ALPHA
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }

    if (!xrayFillVertices.empty())
    {
        bgfx::TransientVertexBuffer xrayFillVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &xrayFillVertexBuffer,
            static_cast<uint32_t>(xrayFillVertices.size()),
            PreviewVertex::ms_layout);
        std::memcpy(
            xrayFillVertexBuffer.data,
            xrayFillVertices.data(),
            xrayFillVertices.size() * sizeof(PreviewVertex));
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &xrayFillVertexBuffer, 0, static_cast<uint32_t>(xrayFillVertices.size()));
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_DEPTH_TEST_ALWAYS
                | BGFX_STATE_BLEND_ALPHA
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }

    if (!vertices.empty())
    {
        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            PreviewVertex::ms_layout);
        std::memcpy(transientVertexBuffer.data, vertices.data(), vertices.size() * sizeof(PreviewVertex));
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }

    if (!xrayVertices.empty())
    {
        bgfx::TransientVertexBuffer xrayVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &xrayVertexBuffer,
            static_cast<uint32_t>(xrayVertices.size()),
            PreviewVertex::ms_layout);
        std::memcpy(xrayVertexBuffer.data, xrayVertices.data(), xrayVertices.size() * sizeof(PreviewVertex));
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &xrayVertexBuffer, 0, static_cast<uint32_t>(xrayVertices.size()));
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_DEPTH_TEST_ALWAYS
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }
}

std::string EditorOutdoorViewport::documentGeometryKey(const EditorDocument &document)
{
    return document.displayName()
        + "|"
        + document.sceneVirtualPath()
        + "|"
        + std::to_string(document.sceneRevision());
}

std::string EditorOutdoorViewport::documentCameraKey(const EditorDocument &document)
{
    return document.displayName() + "|" + document.sceneVirtualPath();
}
}
