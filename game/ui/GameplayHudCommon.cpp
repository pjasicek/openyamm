#include "game/ui/GameplayHudCommon.h"

#include "engine/ImageAssetLoader.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;

struct ParsedHudFontGlyphMetrics
{
    int leftSpacing = 0;
    int width = 0;
    int rightSpacing = 0;
};

struct ParsedHudBitmapFont
{
    int firstChar = 0;
    int lastChar = 0;
    int fontHeight = 0;
    std::array<ParsedHudFontGlyphMetrics, 256> glyphMetrics = {{}};
    std::array<uint32_t, 256> glyphOffsets = {{}};
    std::vector<uint8_t> pixels;
};

int32_t readInt32Le(const uint8_t *pBytes)
{
    return static_cast<int32_t>(
        static_cast<uint32_t>(pBytes[0])
        | (static_cast<uint32_t>(pBytes[1]) << 8)
        | (static_cast<uint32_t>(pBytes[2]) << 16)
        | (static_cast<uint32_t>(pBytes[3]) << 24));
}

uint32_t readUint32Le(const uint8_t *pBytes)
{
    return static_cast<uint32_t>(
        static_cast<uint32_t>(pBytes[0])
        | (static_cast<uint32_t>(pBytes[1]) << 8)
        | (static_cast<uint32_t>(pBytes[2]) << 16)
        | (static_cast<uint32_t>(pBytes[3]) << 24));
}

bool validateParsedHudBitmapFont(
    const ParsedHudBitmapFont &font,
    const std::vector<uint8_t> &pixels)
{
    if (font.firstChar < 0
        || font.firstChar > 255
        || font.lastChar < 0
        || font.lastChar > 255
        || font.firstChar > font.lastChar
        || font.fontHeight <= 0)
    {
        return false;
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const ParsedHudFontGlyphMetrics &metrics = font.glyphMetrics[glyphIndex];

        if (glyphIndex < font.firstChar || glyphIndex > font.lastChar)
        {
            continue;
        }

        if (metrics.width < 0 || metrics.width > 1024 || metrics.leftSpacing < -512 || metrics.leftSpacing > 512
            || metrics.rightSpacing < -512 || metrics.rightSpacing > 512)
        {
            return false;
        }

        const uint64_t glyphSize = static_cast<uint64_t>(font.fontHeight) * static_cast<uint64_t>(metrics.width);
        const uint64_t glyphEnd = static_cast<uint64_t>(font.glyphOffsets[glyphIndex]) + glyphSize;

        if (glyphEnd > pixels.size())
        {
            return false;
        }
    }

    return true;
}

std::optional<ParsedHudBitmapFont> parseHudBitmapFont(const std::vector<uint8_t> &bytes)
{
    constexpr size_t FontHeaderSize = 32;
    constexpr size_t Mm7AtlasSize = 4096;
    constexpr size_t MmxAtlasSize = 1280;

    if (bytes.size() < FontHeaderSize + MmxAtlasSize)
    {
        return std::nullopt;
    }

    const uint8_t *pBytes = bytes.data();

    if (pBytes[2] != 8 || pBytes[3] != 0 || pBytes[4] != 0 || pBytes[6] != 0 || pBytes[7] != 0)
    {
        return std::nullopt;
    }

    ParsedHudBitmapFont mm7Font = {};
    mm7Font.firstChar = pBytes[0];
    mm7Font.lastChar = pBytes[1];
    mm7Font.fontHeight = pBytes[5];

    if (bytes.size() >= FontHeaderSize + Mm7AtlasSize)
    {
        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t metricOffset = FontHeaderSize + static_cast<size_t>(glyphIndex) * 12;
            mm7Font.glyphMetrics[glyphIndex].leftSpacing = readInt32Le(&pBytes[metricOffset]);
            mm7Font.glyphMetrics[glyphIndex].width = readInt32Le(&pBytes[metricOffset + 4]);
            mm7Font.glyphMetrics[glyphIndex].rightSpacing = readInt32Le(&pBytes[metricOffset + 8]);
        }

        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t offsetPosition = FontHeaderSize + 256 * 12 + static_cast<size_t>(glyphIndex) * 4;
            mm7Font.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
        }

        mm7Font.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(FontHeaderSize + Mm7AtlasSize), bytes.end());

        if (validateParsedHudBitmapFont(mm7Font, mm7Font.pixels))
        {
            return mm7Font;
        }
    }

    ParsedHudBitmapFont mmxFont = {};
    mmxFont.firstChar = pBytes[0];
    mmxFont.lastChar = pBytes[1];
    mmxFont.fontHeight = pBytes[5];

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        mmxFont.glyphMetrics[glyphIndex].width = pBytes[FontHeaderSize + glyphIndex];
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const size_t offsetPosition = FontHeaderSize + 256 + static_cast<size_t>(glyphIndex) * 4;
        mmxFont.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
    }

    mmxFont.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(FontHeaderSize + MmxAtlasSize), bytes.end());

    if (!validateParsedHudBitmapFont(mmxFont, mmxFont.pixels))
    {
        return std::nullopt;
    }

    return mmxFont;
}

bool usesBlackTransparencyKey(std::string_view textureName)
{
    const std::string normalizedName = toLowerCopy(std::string(textureName));
    return normalizedName.rfind("mapdir", 0) == 0 || normalizedName.rfind("micon", 0) == 0;
}
} // namespace

GameplayUiViewportRect GameplayHudCommon::computeUiViewportRect(int screenWidth, int screenHeight)
{
    GameplayUiViewportRect viewport = {};
    viewport.width = static_cast<float>(screenWidth);
    viewport.height = static_cast<float>(screenHeight);

    if (screenHeight > 0)
    {
        const float maxWidthForHeight = viewport.height * MaxUiViewportAspect;

        if (viewport.width > maxWidthForHeight)
        {
            viewport.width = maxWidthForHeight;
            viewport.x = (static_cast<float>(screenWidth) - viewport.width) * 0.5f;
        }
    }

    return viewport;
}

GameplayUiViewportRect GameplayHudCommon::computeAnchorRect(
    UiLayoutManager::LayoutAnchorSpace anchorSpace,
    int screenWidth,
    int screenHeight)
{
    if (anchorSpace == UiLayoutManager::LayoutAnchorSpace::Screen)
    {
        GameplayUiViewportRect rect = {};
        rect.width = static_cast<float>(screenWidth);
        rect.height = static_cast<float>(screenHeight);
        return rect;
    }

    return computeUiViewportRect(screenWidth, screenHeight);
}

float GameplayHudCommon::snappedHudFontScale(float scale)
{
    const float roundedScale = std::round(scale);

    if (std::abs(scale - roundedScale) <= HudFontIntegerSnapThreshold)
    {
        return std::max(1.0f, roundedScale);
    }

    return std::max(1.0f, scale);
}

GameplayResolvedHudLayoutElement GameplayHudCommon::resolveAttachedHudLayoutRect(
    UiLayoutManager::LayoutAttachMode attachTo,
    const GameplayResolvedHudLayoutElement &parent,
    float width,
    float height,
    float gapX,
    float gapY,
    float scale)
{
    GameplayResolvedHudLayoutElement resolved = {};
    resolved.width = width;
    resolved.height = height;
    resolved.scale = scale;

    switch (attachTo)
    {
    case UiLayoutManager::LayoutAttachMode::None:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::RightOf:
        resolved.x = parent.x + parent.width + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::LeftOf:
        resolved.x = parent.x - resolved.width + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::Above:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::Below:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + parent.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::CenterAbove:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::CenterBelow:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + parent.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideLeft:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideRight:
        resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
        resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideTopCenter:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideTopLeft:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideTopRight:
        resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideBottomLeft:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideBottomCenter:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideBottomRight:
        resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
        resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::CenterIn:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
        break;
    }

    return resolved;
}

std::optional<GameplayResolvedHudLayoutElement> GameplayHudCommon::resolveHudLayoutElement(
    const UiLayoutManager &layoutManager,
    const std::unordered_map<std::string, float> &runtimeHeightOverrides,
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight)
{
    std::unordered_set<std::string> visited;

    std::function<std::optional<GameplayResolvedHudLayoutElement>(
        const std::string &,
        float,
        float)> resolveRecursive;
    resolveRecursive =
        [&](const std::string &currentLayoutId, float currentFallbackWidth, float currentFallbackHeight)
        -> std::optional<GameplayResolvedHudLayoutElement>
        {
            const std::string normalizedLayoutId = toLowerCopy(currentLayoutId);

            if (visited.contains(normalizedLayoutId))
            {
                std::cerr << "HUD layout cycle detected at element: " << currentLayoutId << '\n';
                return std::nullopt;
            }

            visited.insert(normalizedLayoutId);
            const UiLayoutManager::LayoutElement *pElement = layoutManager.findElement(currentLayoutId);

            if (pElement == nullptr)
            {
                visited.erase(normalizedLayoutId);
                return std::nullopt;
            }

            const UiLayoutManager::LayoutElement &element = *pElement;
            const GameplayUiViewportRect uiViewport = computeUiViewportRect(screenWidth, screenHeight);
            const GameplayUiViewportRect anchorRect = computeAnchorRect(element.anchorSpace, screenWidth, screenHeight);
            const float baseScale = std::min(
                uiViewport.width / HudReferenceWidth,
                uiViewport.height / HudReferenceHeight);
            const auto runtimeHeightOverrideIterator = runtimeHeightOverrides.find(normalizedLayoutId);
            const float effectiveHeight = runtimeHeightOverrideIterator != runtimeHeightOverrides.end()
                ? runtimeHeightOverrideIterator->second
                : (element.height > 0.0f ? element.height : currentFallbackHeight);

            GameplayResolvedHudLayoutElement resolved = {};

            if (!element.parentId.empty() && element.attachTo != UiLayoutManager::LayoutAttachMode::None)
            {
                const UiLayoutManager::LayoutElement *pParent = layoutManager.findElement(element.parentId);

                if (pParent == nullptr)
                {
                    visited.erase(normalizedLayoutId);
                    return std::nullopt;
                }

                const std::optional<GameplayResolvedHudLayoutElement> parent =
                    resolveRecursive(element.parentId, pParent->width, pParent->height);

                if (!parent)
                {
                    visited.erase(normalizedLayoutId);
                    return std::nullopt;
                }

                resolved.scale = element.hasExplicitScale
                    ? std::clamp(baseScale, element.minScale, element.maxScale)
                    : parent->scale;
                resolved.width = (element.width > 0.0f ? element.width : currentFallbackWidth) * resolved.scale;
                resolved.height = effectiveHeight * resolved.scale;
                resolved = resolveAttachedHudLayoutRect(
                    element.attachTo,
                    *parent,
                    resolved.width,
                    resolved.height,
                    element.gapX,
                    element.gapY,
                    resolved.scale);

                if (!element.bottomToId.empty())
                {
                    const UiLayoutManager::LayoutElement *pBottomTo = layoutManager.findElement(element.bottomToId);

                    if (pBottomTo != nullptr)
                    {
                        const std::optional<GameplayResolvedHudLayoutElement> bottomTo =
                            resolveRecursive(element.bottomToId, pBottomTo->width, pBottomTo->height);

                        if (bottomTo)
                        {
                            resolved.height =
                                std::max(0.0f, bottomTo->y + element.bottomGap * resolved.scale - resolved.y);
                        }
                    }
                }

                visited.erase(normalizedLayoutId);
                return resolved;
            }

            resolved.scale = std::clamp(baseScale, element.minScale, element.maxScale);
            resolved.width = (element.width > 0.0f ? element.width : currentFallbackWidth) * resolved.scale;
            resolved.height = effectiveHeight * resolved.scale;

            switch (element.anchor)
            {
            case UiLayoutManager::LayoutAnchor::TopLeft:
                resolved.x = anchorRect.x + element.offsetX * resolved.scale;
                resolved.y = anchorRect.y + element.offsetY * resolved.scale;
                break;

            case UiLayoutManager::LayoutAnchor::TopCenter:
                resolved.x =
                    anchorRect.x + anchorRect.width * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
                resolved.y = anchorRect.y + element.offsetY * resolved.scale;
                break;

            case UiLayoutManager::LayoutAnchor::TopRight:
                resolved.x = anchorRect.x + anchorRect.width - resolved.width + element.offsetX * resolved.scale;
                resolved.y = anchorRect.y + element.offsetY * resolved.scale;
                break;

            case UiLayoutManager::LayoutAnchor::Left:
                resolved.x = anchorRect.x + element.offsetX * resolved.scale;
                resolved.y =
                    anchorRect.y + anchorRect.height * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
                break;

            case UiLayoutManager::LayoutAnchor::Center:
                resolved.x =
                    anchorRect.x + anchorRect.width * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
                resolved.y =
                    anchorRect.y + anchorRect.height * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
                break;

            case UiLayoutManager::LayoutAnchor::Right:
                resolved.x = anchorRect.x + anchorRect.width - resolved.width + element.offsetX * resolved.scale;
                resolved.y =
                    anchorRect.y + anchorRect.height * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
                break;

            case UiLayoutManager::LayoutAnchor::BottomLeft:
                resolved.x = anchorRect.x + element.offsetX * resolved.scale;
                resolved.y = anchorRect.y + anchorRect.height - resolved.height + element.offsetY * resolved.scale;
                break;

            case UiLayoutManager::LayoutAnchor::BottomCenter:
                resolved.x =
                    anchorRect.x + anchorRect.width * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
                resolved.y = anchorRect.y + anchorRect.height - resolved.height + element.offsetY * resolved.scale;
                break;

            case UiLayoutManager::LayoutAnchor::BottomRight:
                resolved.x = anchorRect.x + anchorRect.width - resolved.width + element.offsetX * resolved.scale;
                resolved.y = anchorRect.y + anchorRect.height - resolved.height + element.offsetY * resolved.scale;
                break;
            }

            if (!element.bottomToId.empty())
            {
                const UiLayoutManager::LayoutElement *pBottomTo = layoutManager.findElement(element.bottomToId);

                if (pBottomTo != nullptr)
                {
                    const std::optional<GameplayResolvedHudLayoutElement> bottomTo =
                        resolveRecursive(element.bottomToId, pBottomTo->width, pBottomTo->height);

                    if (bottomTo)
                    {
                        resolved.height =
                            std::max(0.0f, bottomTo->y + element.bottomGap * resolved.scale - resolved.y);
                    }
                }
            }

            visited.erase(normalizedLayoutId);
            return resolved;
        };

    return resolveRecursive(layoutId, fallbackWidth, fallbackHeight);
}

bool GameplayHudCommon::isPointerInsideResolvedElement(
    const GameplayResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY)
{
    return pointerX >= resolved.x
        && pointerX < resolved.x + resolved.width
        && pointerY >= resolved.y
        && pointerY < resolved.y + resolved.height;
}

const std::string *GameplayHudCommon::resolveInteractiveAssetName(
    const UiLayoutManager::LayoutElement &layout,
    const GameplayResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY,
    bool isLeftMousePressed)
{
    const bool isHovered = layout.interactive && isPointerInsideResolvedElement(resolved, pointerX, pointerY);
    const bool isPressed = isHovered && isLeftMousePressed;
    const std::string *pAssetName = &layout.primaryAsset;

    if (isPressed && !layout.pressedAsset.empty())
    {
        pAssetName = &layout.pressedAsset;
    }
    else if (isHovered && !layout.hoverAsset.empty())
    {
        pAssetName = &layout.hoverAsset;
    }

    return pAssetName;
}

std::optional<std::string> GameplayHudCommon::findCachedAssetPath(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &directoryPath,
    const std::string &fileName)
{
    if (pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    const std::string cacheKey = directoryPath + "|" + toLowerCopy(fileName);
    const auto cachedPathIt = cache.assetPathByKey.find(cacheKey);

    if (cachedPathIt != cache.assetPathByKey.end())
    {
        return cachedPathIt->second;
    }

    const auto assetPathsIt = cache.directoryAssetPathsByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pAssetPaths = nullptr;

    if (assetPathsIt != cache.directoryAssetPathsByPath.end())
    {
        pAssetPaths = &assetPathsIt->second;
    }
    else
    {
        std::unordered_map<std::string, std::string> assetPaths;
        const std::vector<std::string> entries = pAssetFileSystem->enumerate(directoryPath);

        for (const std::string &entry : entries)
        {
            assetPaths.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pAssetPaths = &cache.directoryAssetPathsByPath.emplace(directoryPath, std::move(assetPaths)).first->second;
    }

    const std::string normalizedFileName = toLowerCopy(fileName);
    const auto resolvedPathIt = pAssetPaths->find(normalizedFileName);

    if (resolvedPathIt != pAssetPaths->end())
    {
        cache.assetPathByKey[cacheKey] = resolvedPathIt->second;
        return resolvedPathIt->second;
    }

    cache.assetPathByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

std::optional<std::vector<uint8_t>> GameplayHudCommon::readCachedBinaryFile(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &assetPath)
{
    if (pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    const auto cachedFileIt = cache.binaryFilesByPath.find(assetPath);

    if (cachedFileIt != cache.binaryFilesByPath.end())
    {
        return cachedFileIt->second;
    }

    const std::optional<std::vector<uint8_t>> bytes = pAssetFileSystem->readBinaryFile(assetPath);
    cache.binaryFilesByPath[assetPath] = bytes;
    return bytes;
}

std::optional<std::array<uint8_t, 256 * 3>> GameplayHudCommon::loadCachedActPalette(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    int16_t paletteId)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    const auto cachedPaletteIt = cache.actPalettesById.find(paletteId);

    if (cachedPaletteIt != cache.actPalettesById.end())
    {
        return cachedPaletteIt->second;
    }

    char paletteFileName[32] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));
    const std::optional<std::string> palettePath =
        findCachedAssetPath(pAssetFileSystem, cache, "Data/bitmaps", paletteFileName);

    if (!palettePath)
    {
        cache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> paletteBytes = readCachedBinaryFile(pAssetFileSystem, cache, *palettePath);

    if (!paletteBytes || paletteBytes->size() < 256 * 3)
    {
        cache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    std::array<uint8_t, 256 * 3> palette = {};
    std::memcpy(palette.data(), paletteBytes->data(), palette.size());
    cache.actPalettesById[paletteId] = palette;
    return palette;
}

std::optional<std::vector<uint8_t>> GameplayHudCommon::loadHudBitmapPixelsBgraCached(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &textureName,
    int &width,
    int &height)
{
    if (pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.applyMagentaTransparencyKey = true;
    decodeOptions.applyTealTransparencyKey = true;
    decodeOptions.applyBlackTransparencyKey = usesBlackTransparencyKey(textureName);

    const std::optional<Engine::ImagePixelsBgra> image = Engine::loadImageAssetPixelsBgra(
        *pAssetFileSystem,
        "Data/icons",
        textureName,
        cache.directoryAssetPathsByPath,
        cache.assetPathByKey,
        cache.binaryFilesByPath,
        decodeOptions);

    if (!image)
    {
        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    return image->pixels;
}

std::optional<std::vector<uint8_t>> GameplayHudCommon::loadSpriteBitmapPixelsBgraCached(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height)
{
    if (pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.overridePalette = loadCachedActPalette(pAssetFileSystem, cache, paletteId);
    decodeOptions.applyPaletteZeroTransparencyKey = true;
    decodeOptions.applyMagentaTransparencyKey = true;
    decodeOptions.applyTealTransparencyKey = true;

    const std::optional<Engine::ImagePixelsBgra> image = Engine::loadImageAssetPixelsBgra(
        *pAssetFileSystem,
        "Data/sprites",
        textureName,
        cache.directoryAssetPathsByPath,
        cache.assetPathByKey,
        cache.binaryFilesByPath,
        decodeOptions);

    if (!image)
    {
        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    return image->pixels;
}

const GameplayHudTextureData *GameplayHudCommon::findHudTexture(
    const std::vector<GameplayHudTextureData> &textures,
    const std::unordered_map<std::string, size_t> &textureIndexByName,
    const std::string &textureName)
{
    const std::string normalizedTextureName = toLowerCopy(textureName);
    const auto iterator = textureIndexByName.find(normalizedTextureName);

    if (iterator == textureIndexByName.end() || iterator->second >= textures.size())
    {
        return nullptr;
    }

    return &textures[iterator->second];
}

bool GameplayHudCommon::loadHudTexture(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &textureName,
    std::vector<GameplayHudTextureData> &textures,
    std::unordered_map<std::string, size_t> &textureIndexByName)
{
    if (textureName.empty())
    {
        return false;
    }

    if (findHudTexture(textures, textureIndexByName, textureName) != nullptr)
    {
        return true;
    }

    int width = 0;
    int height = 0;
    const std::optional<std::vector<uint8_t>> pixels =
        loadHudBitmapPixelsBgraCached(pAssetFileSystem, cache, textureName, width, height);

    if (!pixels || width <= 0 || height <= 0 || pAssetFileSystem == nullptr)
    {
        return false;
    }

    GameplayHudTextureData textureHandle = {};
    textureHandle.textureName = toLowerCopy(textureName);
    textureHandle.width = Engine::scalePhysicalPixelsToLogical(width, pAssetFileSystem->getAssetScaleTier());
    textureHandle.height = Engine::scalePhysicalPixelsToLogical(height, pAssetFileSystem->getAssetScaleTier());
    textureHandle.physicalWidth = width;
    textureHandle.physicalHeight = height;
    textureHandle.bgraPixels = *pixels;
    textureHandle.textureHandle = createBgraTexture2D(
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        pixels->data(),
        static_cast<uint32_t>(pixels->size()),
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        return false;
    }

    const size_t index = textures.size();
    textures.push_back(std::move(textureHandle));
    textureIndexByName[textures.back().textureName] = index;
    return true;
}

std::optional<GameplayHudTextureHandle> GameplayHudCommon::ensureDynamicHudTexture(
    const std::string &textureName,
    int width,
    int height,
    const std::vector<uint8_t> &bgraPixels,
    std::vector<GameplayHudTextureData> &textures,
    std::unordered_map<std::string, size_t> &textureIndexByName)
{
    const size_t expectedBytes = static_cast<size_t>(width) * static_cast<size_t>(height) * 4;

    if (textureName.empty() || width <= 0 || height <= 0 || bgraPixels.size() != expectedBytes)
    {
        return std::nullopt;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName);
    GameplayHudTextureData *pTexture = nullptr;
    const auto existingIterator = textureIndexByName.find(normalizedTextureName);

    if (existingIterator != textureIndexByName.end() && existingIterator->second < textures.size())
    {
        pTexture = &textures[existingIterator->second];
    }

    if (pTexture == nullptr)
    {
        GameplayHudTextureData textureData = {};
        textureData.textureName = normalizedTextureName;
        textureData.width = width;
        textureData.height = height;
        textureData.physicalWidth = width;
        textureData.physicalHeight = height;
        textureData.bgraPixels = bgraPixels;
        textureData.textureHandle = createEmptyBgraTexture2D(
            static_cast<uint16_t>(width),
            static_cast<uint16_t>(height),
            TextureFilterProfile::Ui,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_TEXTURE_BLIT_DST);

        if (!bgfx::isValid(textureData.textureHandle))
        {
            return std::nullopt;
        }

        const size_t index = textures.size();
        textures.push_back(std::move(textureData));
        textureIndexByName[normalizedTextureName] = index;
        pTexture = &textures.back();
    }
    else if (pTexture->physicalWidth != width || pTexture->physicalHeight != height)
    {
        if (bgfx::isValid(pTexture->textureHandle))
        {
            bgfx::destroy(pTexture->textureHandle);
        }

        pTexture->width = width;
        pTexture->height = height;
        pTexture->physicalWidth = width;
        pTexture->physicalHeight = height;
        pTexture->textureHandle = createEmptyBgraTexture2D(
            static_cast<uint16_t>(width),
            static_cast<uint16_t>(height),
            TextureFilterProfile::Ui,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_TEXTURE_BLIT_DST);

        if (!bgfx::isValid(pTexture->textureHandle))
        {
            pTexture->textureHandle = BGFX_INVALID_HANDLE;
            return std::nullopt;
        }
    }

    pTexture->bgraPixels = bgraPixels;
    bgfx::updateTexture2D(
        pTexture->textureHandle,
        0,
        0,
        0,
        0,
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        bgfx::copy(bgraPixels.data(), static_cast<uint32_t>(bgraPixels.size())));

    GameplayHudTextureHandle result = {};
    result.textureName = pTexture->textureName;
    result.width = pTexture->width;
    result.height = pTexture->height;
    result.textureHandle = pTexture->textureHandle;
    return result;
}

const GameplayHudFontData *GameplayHudCommon::findHudFont(
    const std::vector<GameplayHudFontData> &fonts,
    const std::string &fontName)
{
    const std::string normalizedFontName = toLowerCopy(fontName);

    for (const GameplayHudFontData &fontHandle : fonts)
    {
        if (fontHandle.fontName == normalizedFontName)
        {
            return &fontHandle;
        }
    }

    return nullptr;
}

bool GameplayHudCommon::loadHudFont(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &fontName,
    std::vector<GameplayHudFontData> &fonts)
{
    if (fontName.empty())
    {
        return true;
    }

    if (findHudFont(fonts, fontName) != nullptr)
    {
        return true;
    }

    std::optional<std::string> fontPath = findCachedAssetPath(pAssetFileSystem, cache, "Data/icons", fontName + ".fnt");

    if (!fontPath)
    {
        fontPath = findCachedAssetPath(pAssetFileSystem, cache, "Data/EnglishT", fontName + ".fnt");
    }

    if (!fontPath)
    {
        std::cout << "HUD font load failed: font=\"" << fontName << "\" reason=path-not-found\n";
        return false;
    }

    const std::optional<std::vector<uint8_t>> fontBytes = readCachedBinaryFile(pAssetFileSystem, cache, *fontPath);

    if (!fontBytes || fontBytes->empty())
    {
        std::cout << "HUD font load failed: font=\"" << fontName << "\" path=\"" << *fontPath
                  << "\" reason=read-failed\n";
        return false;
    }

    const std::optional<ParsedHudBitmapFont> parsedFont = parseHudBitmapFont(*fontBytes);

    if (!parsedFont)
    {
        std::cout << "HUD font load failed: font=\"" << fontName << "\" path=\"" << *fontPath
                  << "\" bytes=" << fontBytes->size() << " reason=parse-failed\n";
        return false;
    }

    int atlasCellWidth = 1;

    for (const ParsedHudFontGlyphMetrics &metrics : parsedFont->glyphMetrics)
    {
        atlasCellWidth = std::max(atlasCellWidth, metrics.width);
    }

    const int atlasWidth = atlasCellWidth * 16;
    const int atlasHeight = parsedFont->fontHeight * 16;

    if (atlasWidth <= 0 || atlasHeight <= 0)
    {
        std::cout << "HUD font load failed: font=\"" << fontName << "\" path=\"" << *fontPath
                  << "\" atlas=" << atlasWidth << "x" << atlasHeight << " reason=invalid-atlas\n";
        return false;
    }

    std::vector<uint8_t> mainPixels(static_cast<size_t>(atlasWidth) * atlasHeight * 4, 0);
    std::vector<uint8_t> shadowPixels(static_cast<size_t>(atlasWidth) * atlasHeight * 4, 0);

    for (int glyphIndex = parsedFont->firstChar; glyphIndex <= parsedFont->lastChar; ++glyphIndex)
    {
        const ParsedHudFontGlyphMetrics &metrics = parsedFont->glyphMetrics[glyphIndex];

        if (metrics.width <= 0)
        {
            continue;
        }

        const int cellX = (glyphIndex % 16) * atlasCellWidth;
        const int cellY = (glyphIndex / 16) * parsedFont->fontHeight;
        const size_t glyphOffset = parsedFont->glyphOffsets[glyphIndex];

        for (int y = 0; y < parsedFont->fontHeight; ++y)
        {
            for (int x = 0; x < metrics.width; ++x)
            {
                const uint8_t pixelValue =
                    parsedFont->pixels[glyphOffset + static_cast<size_t>(y) * metrics.width + x];

                if (pixelValue == 0)
                {
                    continue;
                }

                const size_t atlasPixelIndex =
                    (static_cast<size_t>(cellY + y) * atlasWidth + static_cast<size_t>(cellX + x)) * 4;
                std::vector<uint8_t> &targetPixels = (pixelValue == 1) ? shadowPixels : mainPixels;
                targetPixels[atlasPixelIndex + 0] = (pixelValue == 1) ? 0 : 255;
                targetPixels[atlasPixelIndex + 1] = (pixelValue == 1) ? 0 : 255;
                targetPixels[atlasPixelIndex + 2] = (pixelValue == 1) ? 0 : 255;
                targetPixels[atlasPixelIndex + 3] = 255;
            }
        }
    }

    GameplayHudFontData fontHandle = {};
    fontHandle.fontName = toLowerCopy(fontName);
    fontHandle.firstChar = parsedFont->firstChar;
    fontHandle.lastChar = parsedFont->lastChar;
    fontHandle.fontHeight = parsedFont->fontHeight;
    fontHandle.atlasCellWidth = atlasCellWidth;
    fontHandle.atlasWidth = atlasWidth;
    fontHandle.atlasHeight = atlasHeight;
    fontHandle.mainAtlasPixels = mainPixels;

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        fontHandle.glyphMetrics[glyphIndex].leftSpacing = parsedFont->glyphMetrics[glyphIndex].leftSpacing;
        fontHandle.glyphMetrics[glyphIndex].width = parsedFont->glyphMetrics[glyphIndex].width;
        fontHandle.glyphMetrics[glyphIndex].rightSpacing = parsedFont->glyphMetrics[glyphIndex].rightSpacing;
    }

    fontHandle.mainTextureHandle = createBgraTexture2D(
        static_cast<uint16_t>(atlasWidth),
        static_cast<uint16_t>(atlasHeight),
        mainPixels.data(),
        static_cast<uint32_t>(mainPixels.size()),
        TextureFilterProfile::Text);
    fontHandle.shadowTextureHandle = createBgraTexture2D(
        static_cast<uint16_t>(atlasWidth),
        static_cast<uint16_t>(atlasHeight),
        shadowPixels.data(),
        static_cast<uint32_t>(shadowPixels.size()),
        TextureFilterProfile::Text);

    if (!bgfx::isValid(fontHandle.mainTextureHandle) || !bgfx::isValid(fontHandle.shadowTextureHandle))
    {
        if (bgfx::isValid(fontHandle.mainTextureHandle))
        {
            bgfx::destroy(fontHandle.mainTextureHandle);
        }

        if (bgfx::isValid(fontHandle.shadowTextureHandle))
        {
            bgfx::destroy(fontHandle.shadowTextureHandle);
        }

        std::cout << "HUD font load failed: font=\"" << fontName << "\" path=\"" << *fontPath
                  << "\" atlas=" << atlasWidth << "x" << atlasHeight << " reason=texture-create-failed\n";
        return false;
    }

    fonts.push_back(std::move(fontHandle));
    return true;
}

bool GameplayHudCommon::tryGetOpaqueHudTextureBounds(
    const GameplayHudTextureData &texture,
    Engine::AssetScaleTier assetScaleTier,
    int &width,
    int &height,
    int &opaqueMinX,
    int &opaqueMinY,
    int &opaqueMaxX,
    int &opaqueMaxY)
{
    if (texture.physicalWidth <= 0 || texture.physicalHeight <= 0 || texture.bgraPixels.empty())
    {
        return false;
    }

    width = texture.width;
    height = texture.height;
    opaqueMinX = width;
    opaqueMinY = height;
    opaqueMaxX = -1;
    opaqueMaxY = -1;

    for (int y = 0; y < texture.physicalHeight; ++y)
    {
        for (int x = 0; x < texture.physicalWidth; ++x)
        {
            const size_t pixelOffset =
                (static_cast<size_t>(y) * static_cast<size_t>(texture.physicalWidth) + static_cast<size_t>(x)) * 4;

            if (pixelOffset + 3 >= texture.bgraPixels.size() || texture.bgraPixels[pixelOffset + 3] == 0)
            {
                continue;
            }

            opaqueMinX = std::min(opaqueMinX, Engine::scalePhysicalPixelsToLogical(x, assetScaleTier));
            opaqueMinY = std::min(opaqueMinY, Engine::scalePhysicalPixelsToLogical(y, assetScaleTier));
            opaqueMaxX = std::max(opaqueMaxX, Engine::scalePhysicalPixelsToLogical(x + 1, assetScaleTier) - 1);
            opaqueMaxY = std::max(opaqueMaxY, Engine::scalePhysicalPixelsToLogical(y + 1, assetScaleTier) - 1);
        }
    }

    if (opaqueMaxX < opaqueMinX || opaqueMaxY < opaqueMinY)
    {
        opaqueMinX = 0;
        opaqueMinY = 0;
        opaqueMaxX = std::max(0, width - 1);
        opaqueMaxY = std::max(0, height - 1);
    }

    return true;
}

bgfx::TextureHandle GameplayHudCommon::ensureHudTextureColor(
    const GameplayHudTextureData &texture,
    uint32_t colorAbgr,
    std::vector<GameplayHudTextureColorTextureData> &colorTextures)
{
    if (colorAbgr == 0xffffffffu)
    {
        return texture.textureHandle;
    }

    for (const GameplayHudTextureColorTextureData &textureHandle : colorTextures)
    {
        if (textureHandle.textureName == texture.textureName && textureHandle.colorAbgr == colorAbgr)
        {
            return textureHandle.textureHandle;
        }
    }

    if (texture.bgraPixels.empty() || texture.physicalWidth <= 0 || texture.physicalHeight <= 0)
    {
        return BGFX_INVALID_HANDLE;
    }

    std::vector<uint8_t> tintedPixels = texture.bgraPixels;
    const uint8_t red = static_cast<uint8_t>(colorAbgr & 0xff);
    const uint8_t green = static_cast<uint8_t>((colorAbgr >> 8) & 0xff);
    const uint8_t blue = static_cast<uint8_t>((colorAbgr >> 16) & 0xff);
    const uint8_t alpha = static_cast<uint8_t>((colorAbgr >> 24) & 0xff);

    for (size_t pixelIndex = 0; pixelIndex + 3 < tintedPixels.size(); pixelIndex += 4)
    {
        const uint8_t sourceAlpha = tintedPixels[pixelIndex + 3];

        if (sourceAlpha == 0)
        {
            continue;
        }

        tintedPixels[pixelIndex + 0] = blue;
        tintedPixels[pixelIndex + 1] = green;
        tintedPixels[pixelIndex + 2] = red;
        tintedPixels[pixelIndex + 3] = static_cast<uint8_t>((static_cast<uint32_t>(sourceAlpha) * alpha) / 255u);
    }

    const bgfx::TextureHandle textureHandle = createBgraTexture2D(
        static_cast<uint16_t>(texture.physicalWidth),
        static_cast<uint16_t>(texture.physicalHeight),
        tintedPixels.data(),
        static_cast<uint32_t>(tintedPixels.size()),
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    if (!bgfx::isValid(textureHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    GameplayHudTextureColorTextureData tintedTextureHandle = {};
    tintedTextureHandle.textureName = texture.textureName;
    tintedTextureHandle.colorAbgr = colorAbgr;
    tintedTextureHandle.textureHandle = textureHandle;
    colorTextures.push_back(std::move(tintedTextureHandle));
    return colorTextures.back().textureHandle;
}

bgfx::TextureHandle GameplayHudCommon::ensureHudFontMainTextureColor(
    const GameplayHudFontData &font,
    uint32_t colorAbgr,
    std::vector<GameplayHudFontColorTextureData> &colorTextures)
{
    if (colorAbgr == 0xffffffffu)
    {
        return font.mainTextureHandle;
    }

    for (const GameplayHudFontColorTextureData &textureHandle : colorTextures)
    {
        if (textureHandle.fontName == font.fontName && textureHandle.colorAbgr == colorAbgr)
        {
            return textureHandle.textureHandle;
        }
    }

    if (font.mainAtlasPixels.empty() || font.atlasWidth <= 0 || font.atlasHeight <= 0)
    {
        return BGFX_INVALID_HANDLE;
    }

    std::vector<uint8_t> tintedPixels = font.mainAtlasPixels;
    const uint8_t red = static_cast<uint8_t>(colorAbgr & 0xff);
    const uint8_t green = static_cast<uint8_t>((colorAbgr >> 8) & 0xff);
    const uint8_t blue = static_cast<uint8_t>((colorAbgr >> 16) & 0xff);

    for (size_t pixelIndex = 0; pixelIndex + 3 < tintedPixels.size(); pixelIndex += 4)
    {
        if (tintedPixels[pixelIndex + 3] == 0)
        {
            continue;
        }

        tintedPixels[pixelIndex + 0] = blue;
        tintedPixels[pixelIndex + 1] = green;
        tintedPixels[pixelIndex + 2] = red;
    }

    const bgfx::TextureHandle textureHandle = createBgraTexture2D(
        static_cast<uint16_t>(font.atlasWidth),
        static_cast<uint16_t>(font.atlasHeight),
        tintedPixels.data(),
        static_cast<uint32_t>(tintedPixels.size()),
        TextureFilterProfile::Text);

    if (!bgfx::isValid(textureHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    GameplayHudFontColorTextureData tintedTextureHandle = {};
    tintedTextureHandle.fontName = font.fontName;
    tintedTextureHandle.colorAbgr = colorAbgr;
    tintedTextureHandle.textureHandle = textureHandle;
    colorTextures.push_back(std::move(tintedTextureHandle));
    return colorTextures.back().textureHandle;
}

float GameplayHudCommon::measureHudTextWidth(const GameplayHudFontData &font, const std::string &text)
{
    float widthPixels = 0.0f;

    for (unsigned char character : text)
    {
        if (character == '\r' || character == '\n')
        {
            break;
        }

        if (character < font.firstChar || character > font.lastChar)
        {
            widthPixels += static_cast<float>(font.atlasCellWidth);
            continue;
        }

        const GameplayHudFontGlyphMetricsData &glyphMetrics = font.glyphMetrics[character];
        widthPixels += static_cast<float>(glyphMetrics.leftSpacing + glyphMetrics.width + glyphMetrics.rightSpacing);
    }

    return std::max(0.0f, widthPixels);
}

std::string GameplayHudCommon::clampHudTextToWidth(
    const GameplayHudFontData &font,
    const std::string &text,
    float maxWidth)
{
    std::string clampedText = text;

    while (!clampedText.empty() && measureHudTextWidth(font, clampedText) > maxWidth)
    {
        clampedText.pop_back();
    }

    return clampedText;
}

std::vector<std::string> GameplayHudCommon::wrapHudTextToWidth(
    const GameplayHudFontData &font,
    const std::string &text,
    float maxWidth)
{
    if (text.empty())
    {
        return {""};
    }

    if (maxWidth <= 0.0f)
    {
        return {text};
    }

    std::vector<std::string> lines;
    std::string currentLine;
    std::string currentWord;

    const auto flushLine =
        [&lines, &currentLine]()
        {
            lines.push_back(currentLine);
            currentLine.clear();
        };

    const auto appendWord =
        [&font, &currentLine, &flushLine, maxWidth](const std::string &word)
        {
            if (word.empty())
            {
                return;
            }

            if (currentLine.empty())
            {
                currentLine = word;
                return;
            }

            const std::string candidate = currentLine + " " + word;

            if (measureHudTextWidth(font, candidate) <= maxWidth)
            {
                currentLine = candidate;
            }
            else
            {
                flushLine();
                currentLine = word;
            }
        };

    for (char character : text)
    {
        if (character == '\r')
        {
            continue;
        }

        if (character == '\n')
        {
            appendWord(currentWord);
            currentWord.clear();
            flushLine();
            continue;
        }

        if (character == ' ')
        {
            appendWord(currentWord);
            currentWord.clear();
            continue;
        }

        currentWord.push_back(character);
    }

    appendWord(currentWord);

    if (!currentLine.empty() || lines.empty())
    {
        lines.push_back(currentLine);
    }

    return lines;
}

void GameplayHudCommon::renderHudFontLayer(
    const GameplayHudFontData &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale,
    const SubmitTexturedQuadFn &submitTexturedQuad)
{
    if (!bgfx::isValid(textureHandle))
    {
        return;
    }

    float penX = textX;

    for (unsigned char character : text)
    {
        if (character == '\r' || character == '\n')
        {
            break;
        }

        if (character < font.firstChar || character > font.lastChar)
        {
            penX += static_cast<float>(font.atlasCellWidth) * fontScale;
            continue;
        }

        const GameplayHudFontGlyphMetricsData &glyphMetrics = font.glyphMetrics[character];
        penX += static_cast<float>(glyphMetrics.leftSpacing) * fontScale;

        if (glyphMetrics.width > 0)
        {
            const int cellX = (character % 16) * font.atlasCellWidth;
            const int cellY = (character / 16) * font.fontHeight;
            const float u0 = static_cast<float>(cellX) / static_cast<float>(font.atlasWidth);
            const float v0 = static_cast<float>(cellY) / static_cast<float>(font.atlasHeight);
            const float u1 = static_cast<float>(cellX + glyphMetrics.width) / static_cast<float>(font.atlasWidth);
            const float v1 = static_cast<float>(cellY + font.fontHeight) / static_cast<float>(font.atlasHeight);
            const float glyphWidth = static_cast<float>(glyphMetrics.width) * fontScale;
            const float glyphHeight = static_cast<float>(font.fontHeight) * fontScale;

            submitTexturedQuad(
                textureHandle,
                penX,
                textY,
                glyphWidth,
                glyphHeight,
                u0,
                v0,
                u1,
                v1,
                TextureFilterProfile::Text);
        }

        penX += static_cast<float>(glyphMetrics.width + glyphMetrics.rightSpacing) * fontScale;
    }
}

void GameplayHudCommon::renderLayoutLabel(
    const UiLayoutManager::LayoutElement &layout,
    const GameplayResolvedHudLayoutElement &resolved,
    const std::string &label,
    const FindHudFontFn &findHudFontFn,
    const EnsureHudFontColorFn &ensureHudFontColorFn,
    const RenderHudFontLayerFn &renderHudFontLayerFn)
{
    if (label.empty())
    {
        return;
    }

    const GameplayHudFontData *pFont = findHudFontFn(layout.fontName);

    if (pFont == nullptr)
    {
        static std::unordered_set<std::string> missingFontLogs;
        const std::string logKey = "missing-font:" + toLowerCopy(layout.id) + ":" + toLowerCopy(layout.fontName);

        if (!missingFontLogs.contains(logKey))
        {
            std::cout << "HUD label skipped: id=" << layout.id
                      << " font=\"" << layout.fontName
                      << "\" reason=missing-font label=\"" << label << "\"\n";
            missingFontLogs.insert(logKey);
        }

        return;
    }

    float fontScale = resolved.scale * std::max(0.1f, layout.textScale);

    if (fontScale >= 1.0f)
    {
        fontScale = snappedHudFontScale(fontScale);
    }
    else
    {
        fontScale = std::max(0.5f, fontScale);
    }

    const float labelHeightPixels = static_cast<float>(pFont->fontHeight) * fontScale;
    const float maxLabelWidth = std::max(0.0f, resolved.width - std::abs(layout.textPadX * fontScale) * 2.0f);
    std::string clampedLabel = clampHudTextToWidth(*pFont, label, maxLabelWidth);

    if (clampedLabel.empty())
    {
        const GameplayHudFontData *pFallbackFont = findHudFontFn("Lucida");

        if (pFallbackFont != nullptr)
        {
            pFont = pFallbackFont;
            clampedLabel = clampHudTextToWidth(*pFont, label, maxLabelWidth);
        }
    }

    if (clampedLabel.empty())
    {
        clampedLabel = label;
    }

    const float labelWidthPixels = measureHudTextWidth(*pFont, clampedLabel) * fontScale;
    float textX = resolved.x + layout.textPadX * resolved.scale;
    float textY = resolved.y + layout.textPadY * resolved.scale;

    switch (layout.textAlignX)
    {
    case UiLayoutManager::TextAlignX::Left:
        break;

    case UiLayoutManager::TextAlignX::Center:
        textX = resolved.x + (resolved.width - labelWidthPixels) * 0.5f + layout.textPadX * resolved.scale;
        break;

    case UiLayoutManager::TextAlignX::Right:
        textX = resolved.x + resolved.width - labelWidthPixels + layout.textPadX * resolved.scale;
        break;
    }

    switch (layout.textAlignY)
    {
    case UiLayoutManager::TextAlignY::Top:
        break;

    case UiLayoutManager::TextAlignY::Middle:
        textY = resolved.y + (resolved.height - labelHeightPixels) * 0.5f + layout.textPadY * resolved.scale;
        break;

    case UiLayoutManager::TextAlignY::Bottom:
        textY = resolved.y + resolved.height - labelHeightPixels + layout.textPadY * resolved.scale;
        break;
    }

    textX = std::round(textX);
    textY = std::round(textY);

    bgfx::TextureHandle coloredMainTextureHandle = ensureHudFontColorFn(*pFont, layout.textColorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = pFont->mainTextureHandle;
    }

    renderHudFontLayerFn(*pFont, pFont->shadowTextureHandle, clampedLabel, textX, textY, fontScale);
    renderHudFontLayerFn(*pFont, coloredMainTextureHandle, clampedLabel, textX, textY, fontScale);
}
} // namespace OpenYAMM::Game
