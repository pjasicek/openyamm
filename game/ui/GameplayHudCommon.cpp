#include "game/ui/GameplayHudCommon.h"

#include "engine/AssetScaleTier.h"
#include "engine/ImageAssetLoader.h"
#include "engine/ParallelFor.h"
#include "engine/Utf8Text.h"
#include "game/maps/MapIdentity.h"
#include "game/render/TextureFiltering.h"
#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <optional>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;

std::string actPaletteCacheKey(int16_t paletteId, const std::string &worldId)
{
    const std::string normalizedWorldId = worldId.empty() ? std::string() : normalizeWorldId(worldId);
    return normalizedWorldId + "|" + std::to_string(static_cast<int>(paletteId));
}

std::vector<std::string> actPaletteCandidatePaths(int16_t paletteId, const std::string &worldId)
{
    char paletteFileName[32] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));

    std::vector<std::string> paths;

    if (!worldId.empty())
    {
        paths.push_back("worlds/" + normalizeWorldId(worldId) + "/textures/" + paletteFileName);
    }

    paths.push_back(std::string("Data/bitmaps/") + paletteFileName);
    return paths;
}

bool usesBlackTransparencyKey(std::string_view textureName)
{
    const std::string normalizedName = toLowerCopy(std::string(textureName));
    return normalizedName.rfind("mapdir", 0) == 0 || normalizedName.rfind("micon", 0) == 0;
}

bgfx::TextureHandle ensureHudTextureColorWithMode(
    const GameplayHudTextureData &texture,
    uint32_t colorAbgr,
    GameplayHudTextureColorMode colorMode,
    std::vector<GameplayHudTextureColorTextureData> &colorTextures)
{
    if (colorAbgr == 0xffffffffu)
    {
        return texture.textureHandle;
    }

    for (const GameplayHudTextureColorTextureData &textureHandle : colorTextures)
    {
        if (textureHandle.textureName == texture.textureName
            && textureHandle.colorAbgr == colorAbgr
            && textureHandle.colorMode == colorMode)
        {
            return textureHandle.textureHandle;
        }
    }

    const std::vector<uint8_t> &sourcePixels = GameplayHudCommon::hudTexturePixels(texture);

    if (sourcePixels.empty() || texture.physicalWidth <= 0 || texture.physicalHeight <= 0)
    {
        return BGFX_INVALID_HANDLE;
    }

    std::vector<uint8_t> tintedPixels = sourcePixels;
    const uint8_t red = static_cast<uint8_t>(colorAbgr & 0xff);
    const uint8_t green = static_cast<uint8_t>((colorAbgr >> 8) & 0xff);
    const uint8_t blue = static_cast<uint8_t>((colorAbgr >> 16) & 0xff);
    const uint8_t alpha = static_cast<uint8_t>((colorAbgr >> 24) & 0xff);

    for (size_t pixelIndex = 0; pixelIndex + 3 < tintedPixels.size(); pixelIndex += 4)
    {
        const uint8_t sourceAlpha = tintedPixels[pixelIndex + 3];

        if (colorMode == GameplayHudTextureColorMode::Modulated)
        {
            tintedPixels[pixelIndex + 0] = static_cast<uint8_t>(
                (static_cast<uint32_t>(tintedPixels[pixelIndex + 0]) * blue) / 255u);
            tintedPixels[pixelIndex + 1] = static_cast<uint8_t>(
                (static_cast<uint32_t>(tintedPixels[pixelIndex + 1]) * green) / 255u);
            tintedPixels[pixelIndex + 2] = static_cast<uint8_t>(
                (static_cast<uint32_t>(tintedPixels[pixelIndex + 2]) * red) / 255u);
        }
        else if (sourceAlpha != 0)
        {
            tintedPixels[pixelIndex + 0] = blue;
            tintedPixels[pixelIndex + 1] = green;
            tintedPixels[pixelIndex + 2] = red;
        }

        tintedPixels[pixelIndex + 3] = static_cast<uint8_t>(
            (static_cast<uint32_t>(sourceAlpha) * alpha) / 255u);
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
    tintedTextureHandle.colorMode = colorMode;
    tintedTextureHandle.textureHandle = textureHandle;
    colorTextures.push_back(std::move(tintedTextureHandle));
    return colorTextures.back().textureHandle;
}

struct ColumnSeparatedGlyphRun
{
    int startX = 0;
    int width = 0;
};

// Tinting multiplies the atlas, so coloured or black glyphs need one white copy; most atlases already are white.
void assignHudFontTintTexture(GameplayHudFontData &font, TextureFilterProfile filter, uint64_t samplerFlags = 0)
{
    const std::vector<uint8_t> &pixels = font.mainAtlasPixels;
    bool whiteGlyphs = true;

    for (size_t pixelIndex = 0; pixelIndex + 3 < pixels.size() && whiteGlyphs; pixelIndex += 4)
    {
        whiteGlyphs = pixels[pixelIndex + 3] == 0
            || (pixels[pixelIndex] == 255 && pixels[pixelIndex + 1] == 255 && pixels[pixelIndex + 2] == 255);
    }

    font.tintTextureHandle = font.mainTextureHandle;

    if (whiteGlyphs)
    {
        return;
    }

    std::vector<uint8_t> whitePixels = pixels;

    for (size_t pixelIndex = 0; pixelIndex + 3 < whitePixels.size(); pixelIndex += 4)
    {
        whitePixels[pixelIndex] = 255;
        whitePixels[pixelIndex + 1] = 255;
        whitePixels[pixelIndex + 2] = 255;
    }

    font.tintTextureHandle = createBgraTexture2D(
        static_cast<uint16_t>(font.atlasWidth),
        static_cast<uint16_t>(font.atlasHeight),
        whitePixels.data(),
        static_cast<uint32_t>(whitePixels.size()),
        filter,
        samplerFlags);
}

std::optional<GameplayHudFontData> buildColumnSeparatedHudFont(
    const Engine::ImagePixelsBgra &image,
    const std::string &fontName)
{
    constexpr int FirstPrintableCharacter = 33;
    constexpr int LastPrintableCharacter = 126;
    constexpr int PrintableCharacterCount = LastPrintableCharacter - FirstPrintableCharacter + 1;
    constexpr int DefaultAdvanceGlyphIndex = 'E' - FirstPrintableCharacter;

    const size_t expectedPixelCount = static_cast<size_t>(image.width) * static_cast<size_t>(image.height) * 4;
    if (image.width <= 0 || image.height <= 0 || image.pixels.size() < expectedPixelCount)
    {
        return std::nullopt;
    }

    std::vector<ColumnSeparatedGlyphRun> glyphRuns;
    int glyphStartX = -1;
    for (int x = 0; x <= image.width; ++x)
    {
        bool columnHasInk = false;
        if (x < image.width)
        {
            for (int y = 0; y < image.height; ++y)
            {
                const size_t pixelOffset =
                    (static_cast<size_t>(y) * static_cast<size_t>(image.width) + static_cast<size_t>(x)) * 4;
                if (image.pixels[pixelOffset + 3] != 0)
                {
                    columnHasInk = true;
                    break;
                }
            }
        }

        if (columnHasInk && glyphStartX < 0)
        {
            glyphStartX = x;
        }
        else if (!columnHasInk && glyphStartX >= 0)
        {
            glyphRuns.push_back({.startX = glyphStartX, .width = x - glyphStartX});
            glyphStartX = -1;
        }
    }

    if (glyphRuns.size() < PrintableCharacterCount)
    {
        return std::nullopt;
    }

    int atlasCellWidth = 1;
    for (size_t glyphIndex = 0; glyphIndex < PrintableCharacterCount; ++glyphIndex)
    {
        atlasCellWidth = std::max(atlasCellWidth, glyphRuns[glyphIndex].width);
    }

    const int atlasWidth = atlasCellWidth * 16;
    const int atlasHeight = image.height * 16;
    std::vector<uint8_t> atlasPixels(static_cast<size_t>(atlasWidth) * static_cast<size_t>(atlasHeight) * 4, 0);

    GameplayHudFontData font = {};
    font.fontName = toLowerCopy(fontName);
    font.firstChar = 32;
    font.lastChar = LastPrintableCharacter;
    font.fontHeight = image.height;
    font.atlasCellWidth = atlasCellWidth;
    font.atlasWidth = atlasWidth;
    font.atlasHeight = atlasHeight;

    const int defaultAdvance = glyphRuns[DefaultAdvanceGlyphIndex].width + 1;
    font.glyphMetrics[32].rightSpacing = std::max(1, defaultAdvance / 2);

    for (int character = FirstPrintableCharacter; character <= LastPrintableCharacter; ++character)
    {
        const ColumnSeparatedGlyphRun &run = glyphRuns[character - FirstPrintableCharacter];
        font.glyphMetrics[character].width = run.width;
        font.glyphMetrics[character].rightSpacing = 1;

        const int targetX = (character % 16) * atlasCellWidth;
        const int targetY = (character / 16) * image.height;
        for (int y = 0; y < image.height; ++y)
        {
            const size_t sourceOffset =
                (static_cast<size_t>(y) * static_cast<size_t>(image.width) + static_cast<size_t>(run.startX)) * 4;
            const size_t targetOffset =
                (static_cast<size_t>(targetY + y) * static_cast<size_t>(atlasWidth)
                    + static_cast<size_t>(targetX)) * 4;
            std::copy_n(
                image.pixels.begin() + static_cast<ptrdiff_t>(sourceOffset),
                static_cast<size_t>(run.width) * 4,
                atlasPixels.begin() + static_cast<ptrdiff_t>(targetOffset));
        }
    }

    font.mainAtlasPixels = atlasPixels;
    font.mainTextureHandle = createBgraTexture2D(
        static_cast<uint16_t>(atlasWidth),
        static_cast<uint16_t>(atlasHeight),
        atlasPixels.data(),
        static_cast<uint32_t>(atlasPixels.size()),
        TextureFilterProfile::Text,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    if (!bgfx::isValid(font.mainTextureHandle))
    {
        return std::nullopt;
    }

    assignHudFontTintTexture(font, TextureFilterProfile::Text, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    font.mainAtlasPixels = std::vector<uint8_t>();
    return font;
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
    const std::unordered_map<std::string, float> &runtimeWidthOverrides,
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
            const float scaleReferenceWidth = element.scaleReferenceWidth > 0.0f
                ? element.scaleReferenceWidth
                : HudReferenceWidth;
            const float scaleReferenceHeight = element.scaleReferenceHeight > 0.0f
                ? element.scaleReferenceHeight
                : HudReferenceHeight;
            const float scaleAvailableWidth = element.scaleReferenceWidth > 0.0f
                ? anchorRect.width
                : uiViewport.width;
            const float scaleAvailableHeight = element.scaleReferenceHeight > 0.0f
                ? anchorRect.height
                : uiViewport.height;
            const float baseScale = std::min(
                scaleAvailableWidth / scaleReferenceWidth,
                scaleAvailableHeight / scaleReferenceHeight);
            const auto runtimeHeightOverrideIterator = runtimeHeightOverrides.find(normalizedLayoutId);
            const auto runtimeWidthOverrideIterator = runtimeWidthOverrides.find(normalizedLayoutId);
            const float effectiveWidth = runtimeWidthOverrideIterator != runtimeWidthOverrides.end()
                ? runtimeWidthOverrideIterator->second
                : (element.width > 0.0f ? element.width : currentFallbackWidth);
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
                resolved.width = effectiveWidth * resolved.scale;
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
            resolved.width = effectiveWidth * resolved.scale;
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
    int16_t paletteId,
    const std::string &worldId)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    const std::string cacheKey = actPaletteCacheKey(paletteId, worldId);
    const auto cachedPaletteIt = cache.actPalettesByKey.find(cacheKey);

    if (cachedPaletteIt != cache.actPalettesByKey.end())
    {
        return cachedPaletteIt->second;
    }

    for (const std::string &palettePath : actPaletteCandidatePaths(paletteId, worldId))
    {
        const std::optional<std::vector<uint8_t>> paletteBytes =
            readCachedBinaryFile(pAssetFileSystem, cache, palettePath);

        if (!paletteBytes || paletteBytes->size() < 256 * 3)
        {
            continue;
        }

        std::array<uint8_t, 256 * 3> palette = {};
        std::memcpy(palette.data(), paletteBytes->data(), palette.size());
        cache.actPalettesByKey[cacheKey] = palette;
        return palette;
    }

    cache.actPalettesByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

std::optional<std::vector<uint8_t>> GameplayHudCommon::loadHudBitmapPixelsBgraCached(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &textureName,
    int &width,
    int &height,
    GameplayHudBitmapTransparencyMode transparencyMode,
    Engine::AssetScaleTier *pLoadedTier)
{
    if (pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.applyPaletteZeroTransparencyKey = transparencyMode == GameplayHudBitmapTransparencyMode::ItemIcon;
    decodeOptions.applyMagentaTransparencyKey = true;
    decodeOptions.applyTealTransparencyKey = true;
    decodeOptions.applyBlackTransparencyKey = usesBlackTransparencyKey(textureName);

    std::string directoryPath = "Data/icons";
    std::string fileName = textureName;
    const size_t separator = textureName.find_last_of('/');
    if (separator != std::string::npos)
    {
        directoryPath = textureName.substr(0, separator);
        fileName = textureName.substr(separator + 1);
    }

    const std::optional<Engine::ImagePixelsBgra> image = Engine::loadImageAssetPixelsBgra(
        *pAssetFileSystem,
        directoryPath,
        fileName,
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
    if (pLoadedTier != nullptr)
    {
        *pLoadedTier = image->assetScaleTier;
    }
    return image->pixels;
}

std::optional<std::vector<uint8_t>> GameplayHudCommon::loadSpriteBitmapPixelsBgraCached(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height,
    const std::string &worldId,
    Engine::AssetScaleTier *pLoadedTier)
{
    if (pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.overridePalette = loadCachedActPalette(pAssetFileSystem, cache, paletteId, worldId);
    decodeOptions.applyPaletteZeroTransparencyKey = true;

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
    if (pLoadedTier != nullptr)
    {
        *pLoadedTier = image->assetScaleTier;
    }
    return image->pixels;
}

const GameplayHudTextureData *GameplayHudCommon::findHudTexture(
    const std::vector<GameplayHudTextureData> &textures,
    const std::unordered_map<std::string, size_t> &textureIndexByName,
    const std::string &textureName)
{
    auto iterator = textureIndexByName.find(textureName);
    if (iterator == textureIndexByName.end())
    {
        iterator = textureIndexByName.find(toLowerCopy(textureName));
    }

    if (iterator == textureIndexByName.end() || iterator->second >= textures.size())
    {
        return nullptr;
    }

    return &textures[iterator->second];
}

namespace
{
std::shared_ptr<const Engine::CookedTexture> readCookedHudTexture(
    const Engine::AssetFileSystem &assetFileSystem, const std::string &path)
{
    const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(path);
    if (!bytes || bytes->empty())
    {
        throw std::runtime_error("Cannot read cooked HUD texture " + path);
    }
    try
    {
        return std::make_shared<const Engine::CookedTexture>(Engine::decodeCookedTexture(*bytes));
    }
    catch (const std::exception &exception)
    {
        throw std::runtime_error("Cannot load cooked HUD texture " + path + ": " + exception.what());
    }
}

// One HUD texture from a block-aligned cell of a cooked texture whose content is contentWidth x contentHeight.
GameplayHudTextureData cookedHudTextureData(
    const std::string &textureName,
    const std::shared_ptr<const Engine::CookedTexture> &cooked,
    int cellX,
    int cellY,
    int cellWidth,
    int cellHeight,
    int contentWidth,
    int contentHeight,
    Engine::AssetScaleTier tier,
    TextureFilterProfile profile)
{
    GameplayHudTextureData texture = {};
    texture.textureName = textureName;
    texture.physicalWidth = contentWidth;
    texture.physicalHeight = contentHeight;
    texture.width = Engine::scalePhysicalPixelsToLogical(contentWidth, tier);
    texture.height = Engine::scalePhysicalPixelsToLogical(contentHeight, tier);
    texture.assetScaleTier = tier;
    texture.uScale = float(contentWidth) / float(cellWidth);
    texture.vScale = float(contentHeight) / float(cellHeight);
    texture.cookedSource = cooked;
    texture.cookedCellX = cellX;
    texture.cookedCellY = cellY;
    texture.cookedCellWidth = cellWidth;
    texture.cookedCellHeight = cellHeight;
    if (cellX == 0 && cellY == 0 && cellWidth == cooked->width && cellHeight == cooked->height)
    {
        texture.textureHandle = createCookedTexture2D(*cooked, profile, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    }
    else
    {
        Engine::CookedTexture cell = {};
        cell.codec = cooked->codec;
        cell.width = uint16_t(cellWidth);
        cell.height = uint16_t(cellHeight);
        cell.blocks = Engine::cookedTextureRegionBlocks(*cooked, cellX, cellY, cellWidth, cellHeight);
        texture.textureHandle = createCookedTexture2D(cell, profile, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    }
    if (!bgfx::isValid(texture.textureHandle))
    {
        throw std::runtime_error("Cannot create cooked HUD texture " + textureName);
    }
    return texture;
}
}

const std::vector<uint8_t> &GameplayHudCommon::hudTexturePixels(const GameplayHudTextureData &texture)
{
    if (!texture.bgraPixels.empty())
    {
        return texture.bgraPixels;
    }
    std::shared_ptr<const Engine::CookedTexture> source = texture.cookedSource;
    if (source == nullptr && texture.pCookedAssetFileSystem != nullptr)
    {
        try
        {
            source = readCookedHudTexture(*texture.pCookedAssetFileSystem, texture.cookedPath);
        }
        catch (const std::exception &exception)
        {
            std::cout << "HUD texture pixels unavailable: " << exception.what() << '\n';
        }
    }
    if (source == nullptr)
    {
        return texture.bgraPixels;
    }
    const std::vector<uint8_t> cell = Engine::decodeCookedTextureRegionBgra(*source,
        texture.cookedCellX, texture.cookedCellY, texture.cookedCellWidth, texture.cookedCellHeight);
    texture.bgraPixels.resize(size_t(texture.physicalWidth) * texture.physicalHeight * 4);
    for (int y = 0; y < texture.physicalHeight; ++y)
    {
        std::memcpy(texture.bgraPixels.data() + size_t(y) * texture.physicalWidth * 4,
            cell.data() + size_t(y) * texture.cookedCellWidth * 4, size_t(texture.physicalWidth) * 4);
    }
    return texture.bgraPixels;
}

bool GameplayHudCommon::loadCookedFaceSet(
    const Engine::AssetFileSystem &assetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &normalizedName,
    std::vector<GameplayHudTextureData> &textures,
    std::unordered_map<std::string, size_t> &textureIndexByName)
{
    // Portrait frames are <set>NN or <set>-NN ("girla05", "pc01-05"); their set is faces_<set>.yml/.oytex.
    const size_t length = normalizedName.size();
    if (length < 3 || !std::isdigit(static_cast<unsigned char>(normalizedName[length - 1]))
        || !std::isdigit(static_cast<unsigned char>(normalizedName[length - 2])))
    {
        return false;
    }
    std::string set = normalizedName.substr(0, length - 2);
    if (set.ends_with('-'))
    {
        set.pop_back();
    }
    const std::optional<std::string> manifestPath = Engine::findAssetPathCaseInsensitive(assetFileSystem,
        "Data/icons", "faces_" + set + ".yml", cache.directoryAssetPathsByPath, cache.assetPathByKey);
    if (set.empty() || !manifestPath)
    {
        return false;
    }
    const std::optional<std::string> manifestText = assetFileSystem.readTextFile(*manifestPath);
    const YAML::Node manifest = manifestText ? YAML::Load(*manifestText) : YAML::Node();
    if (!manifest || manifest["schema_version"].as<int>(0) != 1 || !manifest["frames"].IsSequence())
    {
        throw std::runtime_error("Invalid portrait set manifest " + *manifestPath);
    }
    const std::vector<std::string> frames = manifest["frames"].as<std::vector<std::string>>();
    if (std::find(frames.begin(), frames.end(), normalizedName) == frames.end())
    {
        return false;
    }
    const int frameWidth = manifest["frame_width"].as<int>();
    const int frameHeight = manifest["frame_height"].as<int>();
    const int columns = manifest["columns"].as<int>();
    const int cellWidth = (frameWidth + 3) / 4 * 4;
    const int cellHeight = (frameHeight + 3) / 4 * 4;
    const std::string atlasPath = manifestPath->substr(0, manifestPath->size() - 4) + ".oytex";
    const std::shared_ptr<const Engine::CookedTexture> atlas = readCookedHudTexture(assetFileSystem, atlasPath);
    const int rows = (int(frames.size()) + columns - 1) / columns;
    if (frameWidth <= 0 || frameHeight <= 0 || columns <= 0 || atlas->width < std::min(columns, int(frames.size()))
            * cellWidth || atlas->height < rows * cellHeight)
    {
        throw std::runtime_error("Portrait set atlas " + atlasPath + " does not match its manifest");
    }
    const std::optional<std::string> resolvedAtlasPath = assetFileSystem.resolveExistingFilePath(atlasPath);
    const Engine::AssetScaleTier tier = Engine::assetScaleTierFromResolvedPath(resolvedAtlasPath.value_or(atlasPath));
    for (size_t index = 0; index < frames.size(); ++index)
    {
        if (findHudTexture(textures, textureIndexByName, frames[index]) != nullptr)
        {
            continue;
        }
        textures.push_back(cookedHudTextureData(frames[index], atlas, int(index % columns) * cellWidth,
            int(index / columns) * cellHeight, cellWidth, cellHeight, frameWidth, frameHeight, tier,
            TextureFilterProfile::Ui));
        textureIndexByName[frames[index]] = textures.size() - 1;
    }
    return true;
}

bool GameplayHudCommon::loadCookedHudImage(
    const Engine::AssetFileSystem &assetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &textureName,
    std::vector<GameplayHudTextureData> &textures,
    std::unordered_map<std::string, size_t> &textureIndexByName)
{
    std::string directoryPath = "Data/icons";
    std::string fileName = textureName;
    const size_t separator = textureName.find_last_of('/');
    if (separator != std::string::npos)
    {
        directoryPath = textureName.substr(0, separator);
        fileName = textureName.substr(separator + 1);
    }
    const std::optional<std::string> path = Engine::findCookedOrImageAssetPath(
        assetFileSystem, directoryPath, fileName, cache.directoryAssetPathsByPath, cache.assetPathByKey);
    if (!path || !toLowerCopy(*path).ends_with(".oytex"))
    {
        return false;
    }
    const std::shared_ptr<const Engine::CookedTexture> cooked = readCookedHudTexture(assetFileSystem, *path);
    const std::string normalizedName = toLowerCopy(textureName);
    textures.push_back(cookedHudTextureData(normalizedName, cooked, 0, 0, cooked->width, cooked->height,
        cooked->contentWidth != 0 ? cooked->contentWidth : cooked->width,
        cooked->contentHeight != 0 ? cooked->contentHeight : cooked->height,
        Engine::assetScaleTierFromResolvedPath(*path),
        normalizedName.starts_with("obsidian_") ? TextureFilterProfile::UiIllustration : TextureFilterProfile::Ui));
    // The GPU has the blocks; the rare CPU use (tints, opaque bounds, hover tests) reads the file again.
    textures.back().cookedSource = nullptr;
    textures.back().cookedPath = *path;
    textures.back().pCookedAssetFileSystem = &assetFileSystem;
    textureIndexByName[normalizedName] = textures.size() - 1;
    return true;
}

bool GameplayHudCommon::loadHudTexture(
    const Engine::AssetFileSystem *pAssetFileSystem,
    GameplayAssetLoadCache &cache,
    const std::string &textureName,
    std::vector<GameplayHudTextureData> &textures,
    std::unordered_map<std::string, size_t> &textureIndexByName,
    GameplayHudBitmapTransparencyMode transparencyMode)
{
    if (textureName.empty())
    {
        return false;
    }

    if (findHudTexture(textures, textureIndexByName, textureName) != nullptr)
    {
        return true;
    }

    // Cooked art (tools/cook_ui_textures.py) was prepared with the colour-key decode.
    if (pAssetFileSystem != nullptr && transparencyMode == GameplayHudBitmapTransparencyMode::HudColorKey
        && (loadCookedFaceSet(*pAssetFileSystem, cache, toLowerCopy(textureName), textures, textureIndexByName)
            || loadCookedHudImage(*pAssetFileSystem, cache, textureName, textures, textureIndexByName)))
    {
        return findHudTexture(textures, textureIndexByName, textureName) != nullptr;
    }

    int width = 0;
    int height = 0;
    Engine::AssetScaleTier loadedTier = Engine::AssetScaleTier::X1;
    const std::optional<std::vector<uint8_t>> pixels = loadHudBitmapPixelsBgraCached(
        pAssetFileSystem, cache, textureName, width, height, transparencyMode, &loadedTier);

    if (!pixels || width <= 0 || height <= 0 || pAssetFileSystem == nullptr)
    {
        return false;
    }

    GameplayHudTextureData textureHandle = {};
    textureHandle.textureName = toLowerCopy(textureName);
    textureHandle.width = Engine::scalePhysicalPixelsToLogical(width, loadedTier);
    textureHandle.height = Engine::scalePhysicalPixelsToLogical(height, loadedTier);
    textureHandle.assetScaleTier = loadedTier;
    textureHandle.physicalWidth = width;
    textureHandle.physicalHeight = height;
    textureHandle.bgraPixels = *pixels;
    textureHandle.textureHandle = createBgraTexture2D(
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        pixels->data(),
        static_cast<uint32_t>(pixels->size()),
        textureHandle.textureName.starts_with("obsidian_")
            ? TextureFilterProfile::UiIllustration : TextureFilterProfile::Ui,
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
        copyBgraTextureUploadMemory(bgraPixels.data(), static_cast<uint32_t>(bgraPixels.size())));

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

namespace
{
// Where a font comes from. A column-separated PCX font (dialogue) is complete once decoded.
struct FontSource
{
    std::string fontName;
    int pixelHeight = 0;
    bool independentFont = false;
    // A Unicode face's atlas, shared by the sizes and faces that raster the same font file and characters at the same
    // height; empty for other faces.
    std::string unicodeAtlasKey;
    // The face's baseline at that raster height: faces sharing an atlas differ only in it.
    int unicodeBaseline = 0;
    int displayHeight = 0;
    std::optional<std::vector<uint8_t>> fntBytes;
    std::optional<GameplayHudFontData> bitmapFont;
};

// A font's atlas and its textures' CPU work (mip chains, the white tint copy), ready to upload.
struct PreparedFont
{
    std::string fontName;
    int pixelHeight = 0;
    bool independentFont = false;
    std::string unicodeAtlasKey;
    int unicodeBaseline = 0;
    std::optional<Engine::FontAtlasImage> image;
    std::string error;
    PreparedBgraTexture main;
    PreparedBgraTexture shadow;
    std::optional<PreparedBgraTexture> tint;
};

std::string sharedFontKey(const std::string &fontName, int pixelHeight)
{
    const std::string name = toLowerCopy(fontName);
    return pixelHeight > 0 ? name + "|pixels:" + std::to_string(pixelHeight) : name;
}

struct SharedFontStore
{
    std::unordered_map<std::string, std::unique_ptr<GameplayHudFontData>> fonts;
    // The atlases of Unicode faces, owning their textures; the fonts that draw from one copy its handles.
    std::unordered_map<std::string, std::unique_ptr<GameplayHudFontData>> unicodeAtlases;
    std::unordered_set<std::string> failed;
};

SharedFontStore &sharedFontStore()
{
    static SharedFontStore store;
    return store;
}

void destroyFontTextures(const GameplayHudFontData &font)
{
    if (font.sharedTextures)
    {
        return;
    }
    if (bgfx::isValid(font.tintTextureHandle) && font.tintTextureHandle.idx != font.mainTextureHandle.idx)
    {
        bgfx::destroy(font.tintTextureHandle);
    }
    if (bgfx::isValid(font.shadowTextureHandle) && font.shadowTextureHandle.idx != font.mainTextureHandle.idx)
    {
        bgfx::destroy(font.shadowTextureHandle);
    }
    if (bgfx::isValid(font.mainTextureHandle))
    {
        bgfx::destroy(font.mainTextureHandle);
    }
}

// Reads the font's descriptor and its FNT or PCX; runs on the loading thread.
std::optional<FontSource> resolveFontSource(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &fontName,
    int pixelHeight)
{
    FontSource source;
    source.fontName = fontName;
    source.pixelHeight = pixelHeight;
    const std::optional<std::string> descriptorText =
        assetFileSystem.readTextFile("fonts/truetype/" + toLowerCopy(fontName) + ".yml");
    if (descriptorText)
    {
        try
        {
            const YAML::Node descriptor = YAML::Load(*descriptorText);
            source.independentFont = descriptor["metrics"].as<std::string>("legacy") == "freetype";
            if (source.independentFont && descriptor["encoding"].as<std::string>("") == "utf-8")
            {
                const int logicalHeight = descriptor["logical_height"].as<int>(0);
                const int rasterHeight = Engine::unicodeRasterHeight(
                    pixelHeight, logicalHeight, descriptor["max_raster_height"].as<int>(0));
                source.displayHeight = pixelHeight > 0 ? pixelHeight : logicalHeight;
                source.unicodeBaseline = logicalHeight > 0
                    ? int(std::lround(float(descriptor["baseline"].as<int>(0)) * rasterHeight / logicalHeight))
                    : 0;
                // The atlas's pixels depend on the font file, its characters and weight and the raster height, not
                // on the face (a CJK pack draws every face with one font). Logical and display sizes are released
                // apart (releaseRasterSizes), so they never share an atlas.
                source.unicodeAtlasKey = descriptor["file"].as<std::string>("") + "|"
                    + descriptor["characters_file"].as<std::string>("") + "|"
                    + descriptor["weight"].as<std::string>("") + "|"
                    + descriptor["glyph_scale"].as<std::string>("1") + (pixelHeight > 0 ? "|pixels|" : "|logical|")
                    + std::to_string(rasterHeight);
            }
        }
        catch (const YAML::Exception &exception)
        {
            std::cout << "Font load failed: font=\"" << fontName
                      << "\" reason=invalid-descriptor: " << exception.what() << '\n';
            return std::nullopt;
        }
    }
    if (source.independentFont)
    {
        return source;
    }

    Engine::DirectoryAssetPathCache directoryAssetPaths;
    Engine::AssetPathLookupCache assetPaths;
    // A legacy face's FNT carries its layout metrics (engine/fonts/english_text).
    const std::optional<std::string> fontPath = Engine::findAssetPathCaseInsensitive(
        assetFileSystem, "Data/EnglishT", fontName + ".fnt", directoryAssetPaths, assetPaths);

    if (!fontPath)
    {
        const std::optional<std::string> pcxFontPath = Engine::findAssetPathCaseInsensitive(
            assetFileSystem, "ui/dialogue", fontName + ".pcx", directoryAssetPaths, assetPaths);
        if (pcxFontPath)
        {
            Engine::ImageDecodeOptions decodeOptions = {};
            decodeOptions.applyTealTransparencyKey = true;
            Engine::BinaryAssetCache binaryFiles;
            const std::optional<Engine::ImagePixelsBgra> image =
                Engine::loadImageAssetPixelsBgra(assetFileSystem, *pcxFontPath, binaryFiles, decodeOptions);
            source.bitmapFont = image ? buildColumnSeparatedHudFont(*image, fontName) : std::nullopt;
            if (source.bitmapFont)
            {
                return source;
            }

            std::cout << "Font load failed: font=\"" << fontName << "\" path=\"" << *pcxFontPath
                      << "\" reason=column-separated-pcx-parse-failed\n";
            return std::nullopt;
        }

        std::cout << "Font load failed: font=\"" << fontName << "\" reason=path-not-found\n";
        return std::nullopt;
    }

    source.fntBytes = assetFileSystem.readBinaryFile(*fontPath);

    if (!source.fntBytes || source.fntBytes->empty())
    {
        std::cout << "Font load failed: font=\"" << fontName << "\" path=\"" << *fontPath
                  << "\" reason=read-failed\n";
        return std::nullopt;
    }

    return source;
}

TextureFilterProfile fontFilter(const Engine::FontAtlas &atlas, bool independentFont)
{
    return atlas.atlasScale > 1 || independentFont ? TextureFilterProfile::SmoothText : TextureFilterProfile::Text;
}

// The CPU part of a font load; safe on any thread.
PreparedFont prepareFont(const Engine::AssetFileSystem &assetFileSystem, const FontSource &source)
{
    PreparedFont font;
    font.fontName = source.fontName;
    font.pixelHeight = source.pixelHeight;
    font.independentFont = source.independentFont;
    font.unicodeAtlasKey = source.unicodeAtlasKey;
    font.unicodeBaseline = source.unicodeBaseline;
    font.image = source.independentFont
        ? Engine::loadTrueTypeFontAtlas(assetFileSystem, source.fontName, font.error, source.pixelHeight)
        : Engine::loadFontAtlas(assetFileSystem, *source.fntBytes, source.fontName, font.error);
    if (!font.image)
    {
        return font;
    }

    Engine::FontAtlas &atlas = font.image->atlas;
    const TextureFilterProfile filter = fontFilter(atlas, font.independentFont);
    const uint16_t width = static_cast<uint16_t>(atlas.atlasWidth);
    const uint16_t height = static_cast<uint16_t>(atlas.atlasHeight);
    std::vector<uint8_t> &mainPixels = atlas.mainAtlasPixels;

    // Tinting multiplies the atlas, so coloured or black glyphs need one white copy; most atlases already are white.
    bool whiteGlyphs = true;
    for (size_t pixelIndex = 0; pixelIndex + 3 < mainPixels.size() && whiteGlyphs; pixelIndex += 4)
    {
        whiteGlyphs = mainPixels[pixelIndex + 3] == 0
            || (mainPixels[pixelIndex] == 255 && mainPixels[pixelIndex + 1] == 255
                && mainPixels[pixelIndex + 2] == 255);
    }
    if (!whiteGlyphs)
    {
        std::vector<uint8_t> whitePixels = mainPixels;
        for (size_t pixelIndex = 0; pixelIndex + 3 < whitePixels.size(); pixelIndex += 4)
        {
            whitePixels[pixelIndex] = 255;
            whitePixels[pixelIndex + 1] = 255;
            whitePixels[pixelIndex + 2] = 255;
        }
        font.tint = prepareBgraTexture2D(width, height, std::move(whitePixels), filter);
    }
    // The atlas pixels only feed these textures (the outline atlases are 10-40 MB each), so they move into them.
    font.main = prepareBgraTexture2D(width, height, std::move(mainPixels), filter);
    // A Unicode atlas's shadow mask is the glyph itself, offset when drawn: it draws from the main texture.
    if (!atlas.unicode)
    {
        font.shadow = prepareBgraTexture2D(width, height, std::move(font.image->shadowPixels), filter);
    }
    return font;
}

std::optional<GameplayHudFontData> finishFont(PreparedFont &prepared)
{
    const std::string &fontName = prepared.fontName;
    if (!prepared.image)
    {
        std::cout << "Font load failed: font=\"" << fontName << "\" reason=" << prepared.error << '\n';
        return std::nullopt;
    }

    GameplayHudFontData fontHandle = {};
    static_cast<Engine::FontAtlas &>(fontHandle) = std::move(prepared.image->atlas);
    fontHandle.fontName = toLowerCopy(fontName);
    fontHandle.rasterPixelHeight = prepared.pixelHeight;
    fontHandle.smooth = fontHandle.atlasScale > 1 || prepared.independentFont;
    const TextureFilterProfile filter = fontFilter(fontHandle, prepared.independentFont);
    fontHandle.mainTextureHandle = createPreparedBgraTexture2D(std::move(prepared.main), filter);
    fontHandle.shadowTextureHandle = fontHandle.unicode
        ? fontHandle.mainTextureHandle : createPreparedBgraTexture2D(std::move(prepared.shadow), filter);
    fontHandle.unicodeBaseline = prepared.unicodeBaseline;
    fontHandle.tintTextureHandle = prepared.tint
        ? createPreparedBgraTexture2D(std::move(*prepared.tint), filter) : fontHandle.mainTextureHandle;

    if (!bgfx::isValid(fontHandle.mainTextureHandle) || !bgfx::isValid(fontHandle.shadowTextureHandle)
        || !bgfx::isValid(fontHandle.tintTextureHandle))
    {
        destroyFontTextures(fontHandle);
        std::cout << "Font load failed: font=\"" << fontName << "\" atlas=" << fontHandle.atlasWidth << "x"
                  << fontHandle.atlasHeight << " reason=texture-create-failed\n";
        return std::nullopt;
    }

    return fontHandle;
}
}

// A font that draws from a Unicode atlas at its own size and baseline: the atlas's glyphs, laid out at displayHeight.
std::unique_ptr<GameplayHudFontData> unicodeFontFromAtlas(
    const GameplayHudFontData &atlas,
    const FontSource &source)
{
    const std::string &fontName = source.fontName;
    const int pixelHeight = source.pixelHeight;
    const int displayHeight = source.displayHeight;
    auto pFont = std::make_unique<GameplayHudFontData>(atlas);
    // Another face of the same font sits its glyphs lower or higher on the line by its baseline.
    const int baselineShift = source.unicodeBaseline - atlas.unicodeBaseline;
    for (Engine::FontGlyphPlacement &placement : pFont->unicodeGlyphPlacements)
    {
        placement.top += baselineShift;
    }
    pFont->unicodeBaseline = source.unicodeBaseline;
    pFont->fontName = toLowerCopy(fontName);
    pFont->rasterPixelHeight = pixelHeight;
    pFont->fontHeight = displayHeight;
    pFont->layoutScale = float(displayHeight) / float(pFont->rasterHeight);
    pFont->sharedTextures = true;
    return pFont;
}

void SharedFontCache::ensure(const Engine::AssetFileSystem &assetFileSystem, const std::vector<Request> &requests)
{
    SharedFontStore &store = sharedFontStore();
    std::vector<FontSource> sources;
    std::unordered_set<std::string> pending;
    // Unicode fonts waiting for an atlas this call loads, by its key.
    std::unordered_map<std::string, std::vector<FontSource>> unicodeWaiting;
    for (const Request &request : requests)
    {
        const std::string key = sharedFontKey(request.fontName, request.pixelHeight);
        if (request.fontName.empty() || store.fonts.contains(key) || store.failed.contains(key)
            || !pending.insert(key).second)
        {
            continue;
        }
        std::optional<FontSource> source = resolveFontSource(assetFileSystem, request.fontName, request.pixelHeight);
        if (!source)
        {
            store.failed.insert(key);
            continue;
        }
        if (source->bitmapFont)
        {
            store.fonts.emplace(key, std::make_unique<GameplayHudFontData>(std::move(*source->bitmapFont)));
            continue;
        }
        if (!source->unicodeAtlasKey.empty())
        {
            const auto atlas = store.unicodeAtlases.find(source->unicodeAtlasKey);
            if (atlas != store.unicodeAtlases.end())
            {
                store.fonts.emplace(key, unicodeFontFromAtlas(*atlas->second, *source));
                continue;
            }
            std::vector<FontSource> &waiting = unicodeWaiting[source->unicodeAtlasKey];
            waiting.push_back(*source);
            if (waiting.size() > 1)
            {
                continue;
            }
        }
        sources.push_back(std::move(*source));
    }

    // Rasterized and mip-filtered together on the load workers, then uploaded here.
    std::vector<PreparedFont> prepared(sources.size());
    Engine::parallelFor(sources.size(), [&](size_t index)
    {
        prepared[index] = prepareFont(assetFileSystem, sources[index]);
    });
    for (PreparedFont &font : prepared)
    {
        const std::string key = sharedFontKey(font.fontName, font.pixelHeight);
        std::optional<GameplayHudFontData> finished = finishFont(font);
        if (font.unicodeAtlasKey.empty())
        {
            if (finished)
            {
                store.fonts.emplace(key, std::make_unique<GameplayHudFontData>(std::move(*finished)));
            }
            else
            {
                store.failed.insert(key);
            }
            continue;
        }
        for (const FontSource &waiting : unicodeWaiting[font.unicodeAtlasKey])
        {
            const std::string waitingKey = sharedFontKey(waiting.fontName, waiting.pixelHeight);
            if (finished)
            {
                store.fonts.emplace(waitingKey,
                    unicodeFontFromAtlas(*finished, waiting));
            }
            else
            {
                store.failed.insert(waitingKey);
            }
        }
        if (finished)
        {
            store.unicodeAtlases.emplace(font.unicodeAtlasKey, std::make_unique<GameplayHudFontData>(std::move(*finished)));
        }
    }
}

const GameplayHudFontData *SharedFontCache::find(const std::string &fontName, int pixelHeight)
{
    const SharedFontStore &store = sharedFontStore();
    const auto found = store.fonts.find(sharedFontKey(fontName, pixelHeight));
    return found != store.fonts.end() ? found->second.get() : nullptr;
}

void SharedFontCache::releaseRasterSizes()
{
    std::erase_if(sharedFontStore().fonts, [](const auto &entry)
    {
        if (entry.second->rasterPixelHeight == 0)
        {
            return false;
        }
        destroyFontTextures(*entry.second);
        return true;
    });
    std::erase_if(sharedFontStore().unicodeAtlases, [](const auto &entry)
    {
        if (entry.second->rasterPixelHeight == 0)
        {
            return false;
        }
        destroyFontTextures(*entry.second);
        return true;
    });
}

void SharedFontCache::release(bool destroyGpu)
{
    SharedFontStore &store = sharedFontStore();
    if (destroyGpu)
    {
        for (const auto &[key, pFont] : store.fonts)
        {
            destroyFontTextures(*pFont);
        }
        for (const auto &[key, pAtlas] : store.unicodeAtlases)
        {
            destroyFontTextures(*pAtlas);
        }
    }
    store.fonts.clear();
    store.unicodeAtlases.clear();
    store.failed.clear();
}

bool GameplayHudCommon::loadHudFont(
    const Engine::AssetFileSystem *pAssetFileSystem,
    const std::string &fontName,
    std::vector<GameplayHudFontData> &fonts)
{
    return loadHudFonts(pAssetFileSystem, {fontName}, fonts);
}

bool GameplayHudCommon::loadHudFonts(
    const Engine::AssetFileSystem *pAssetFileSystem,
    const std::vector<std::string> &fontNames,
    std::vector<GameplayHudFontData> &fonts)
{
    std::vector<SharedFontCache::Request> requests;
    for (const std::string &fontName : fontNames)
    {
        if (!fontName.empty() && findHudFont(fonts, fontName) == nullptr)
        {
            requests.push_back({fontName, 0});
        }
    }
    if (requests.empty())
    {
        return true;
    }
    SharedFontCache::ensure(*pAssetFileSystem, requests);
    bool loaded = true;
    for (const SharedFontCache::Request &request : requests)
    {
        if (findHudFont(fonts, request.fontName) != nullptr)
        {
            continue;
        }
        const GameplayHudFontData *pFont = SharedFontCache::find(request.fontName);
        if (pFont == nullptr)
        {
            loaded = false;
            continue;
        }
        fonts.push_back(*pFont);
    }
    return loaded;
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
    const std::vector<uint8_t> &pixels = hudTexturePixels(texture);

    if (texture.physicalWidth <= 0 || texture.physicalHeight <= 0 || pixels.empty())
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

            if (pixelOffset + 3 >= pixels.size() || pixels[pixelOffset + 3] == 0)
            {
                continue;
            }

            opaqueMinX = std::min(opaqueMinX, x / Engine::assetScaleTierFactor(assetScaleTier));
            opaqueMinY = std::min(opaqueMinY, y / Engine::assetScaleTierFactor(assetScaleTier));
            opaqueMaxX = std::max(opaqueMaxX, x / Engine::assetScaleTierFactor(assetScaleTier));
            opaqueMaxY = std::max(opaqueMaxY, y / Engine::assetScaleTierFactor(assetScaleTier));
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
    return ensureHudTextureColorWithMode(
        texture,
        colorAbgr,
        GameplayHudTextureColorMode::Solid,
        colorTextures);
}

bgfx::TextureHandle GameplayHudCommon::ensureHudTextureColorModulated(
    const GameplayHudTextureData &texture,
    uint32_t colorAbgr,
    std::vector<GameplayHudTextureColorTextureData> &colorTextures)
{
    return ensureHudTextureColorWithMode(
        texture,
        colorAbgr,
        GameplayHudTextureColorMode::Modulated,
        colorTextures);
}

GameplayHudFontLayer GameplayHudCommon::hudFontMainLayer(const GameplayHudFontData &font, uint32_t colorAbgr)
{
    // Text ignores the colour's alpha, as tinted atlases always did.
    return colorAbgr == 0xffffffffu
        ? GameplayHudFontLayer(font.mainTextureHandle)
        : GameplayHudFontLayer(font.tintTextureHandle, colorAbgr | 0xff000000u);
}

bool GameplayHudCommon::readTextColorCode(const std::string &text, size_t index, std::optional<uint32_t> &colorAbgr)
{
    if (index + TextColorCodeLength > text.size() || text[index] != '\f')
    {
        return false;
    }

    uint32_t value = 0;

    for (size_t digit = index + 1; digit < index + TextColorCodeLength; ++digit)
    {
        if (!std::isdigit(static_cast<unsigned char>(text[digit])))
        {
            return false;
        }

        value = value * 10 + uint32_t(text[digit] - '0');
    }

    if (value == 0)
    {
        colorAbgr.reset();
        return true;
    }

    const uint32_t red = ((value >> 11) & 31u) * 255u / 31u;
    const uint32_t green = ((value >> 5) & 63u) * 255u / 63u;
    const uint32_t blue = (value & 31u) * 255u / 31u;
    colorAbgr = 0xff000000u | (blue << 16) | (green << 8) | red;
    return true;
}

namespace
{
// Walks a line of text to its first line break, character by character in UTF-8 with colour codes skipped: draw gets
// each glyph the font has with its pen position (the glyph's origin) and colour run, in the font's raster pixels. A
// character with no glyph advances a cell. Returns the line's advance.
template <typename DrawGlyph>
float walkHudLine(const GameplayHudFontData &font, const std::string &text, const DrawGlyph &drawGlyph)
{
    float pen = 0.0f;
    uint32_t previous = 0;
    std::optional<uint32_t> runColor;

    for (size_t index = 0; index < text.size();)
    {
        if (GameplayHudCommon::readTextColorCode(text, index, runColor))
        {
            index += GameplayHudCommon::TextColorCodeLength;
            continue;
        }

        const uint32_t character = Engine::Utf8::next(text, index);

        if (character == '\r' || character == '\n')
        {
            break;
        }

        const int glyph = font.glyphIndex(character);

        if (glyph < 0)
        {
            pen += static_cast<float>(font.atlasCellWidth);
            continue;
        }

        pen += font.kerning(previous, character);
        drawGlyph(glyph, pen, runColor);
        pen += font.glyph(glyph).advance();
        previous = character;
    }

    return pen;
}
}

float GameplayHudCommon::measureHudTextWidth(const GameplayHudFontData &font, const std::string &text)
{
    const float width = walkHudLine(font, text, [](int, float, const std::optional<uint32_t> &) {});
    return std::max(0.0f, width * font.layoutScale);
}

std::string GameplayHudCommon::clampHudTextToWidth(
    const GameplayHudFontData &font,
    const std::string &text,
    float maxWidth)
{
    std::string clampedText = text;

    while (!clampedText.empty() && measureHudTextWidth(font, clampedText) > maxWidth)
    {
        Engine::Utf8::popBack(clampedText);
    }

    return clampedText;
}

std::vector<std::string> GameplayHudCommon::wrapHudTextToWidth(
    const GameplayHudFontData &font,
    const std::string &text,
    float maxWidth)
{
    std::vector<std::string> lines = Engine::Utf8::wrap(text, maxWidth,
        [&font](const std::string &line)
        {
            return measureHudTextWidth(font, line);
        });
    carryTextColorsAcrossLines(lines);
    return lines;
}

void GameplayHudCommon::carryTextColorsAcrossLines(std::vector<std::string> &lines)
{
    std::optional<uint32_t> openColor;
    std::string openCode;

    for (std::string &line : lines)
    {
        if (!openCode.empty())
        {
            line.insert(0, openCode);
        }

        for (size_t index = 0; index < line.size(); ++index)
        {
            if (readTextColorCode(line, index, openColor))
            {
                openCode = openColor ? line.substr(index, TextColorCodeLength) : std::string();
                index += TextColorCodeLength - 1;
            }
        }
    }
}

void GameplayHudCommon::renderHudFontLayer(
    const GameplayHudFontData &font,
    const GameplayHudFontLayer &layer,
    const std::string &text,
    float textX,
    float textY,
    float fontScale,
    const SubmitTexturedQuadFn &submitTexturedQuad)
{
    if (!bgfx::isValid(layer.textureHandle))
    {
        return;
    }

    // Glyph geometry is in raster pixels; a Unicode face's raster differs from its layout height.
    const float scale = fontScale * font.layoutScale;
    const float atlasWidth = static_cast<float>(font.atlasWidth / font.atlasScale);
    const float atlasHeight = static_cast<float>(font.atlasHeight / font.atlasScale);
    // Colour codes recolour the main layer through the tint atlas; the shadow stays as it is.
    const bool shadow = layer.textureHandle.idx == font.shadowTextureHandle.idx;

    walkHudLine(font, text,
        [&](int glyph, float pen, const std::optional<uint32_t> &runColor)
        {
            const GameplayHudFontGlyphMetricsData &metrics = font.glyph(glyph);

            if (metrics.width <= 0)
            {
                return;
            }

            const Engine::FontGlyphPlacement place = font.placement(glyph);
            const bool recolored = runColor && !shadow && bgfx::isValid(font.tintTextureHandle);
            submitTexturedQuad(
                recolored ? font.tintTextureHandle : layer.textureHandle,
                textX + (pen + metrics.leftSpacing - font.atlasPadding) * scale,
                textY + place.top * scale,
                static_cast<float>(place.width) * scale,
                static_cast<float>(place.height) * scale,
                static_cast<float>(place.x) / atlasWidth,
                static_cast<float>(place.y) / atlasHeight,
                static_cast<float>(place.x + place.width) / atlasWidth,
                static_cast<float>(place.y + place.height) / atlasHeight,
                font.smooth ? TextureFilterProfile::SmoothText : TextureFilterProfile::Text,
                recolored ? *runColor : layer.tintAbgr);
        });
}

void GameplayHudCommon::renderLayoutLabel(
    const UiLayoutManager::LayoutElement &layout,
    const GameplayResolvedHudLayoutElement &resolved,
    const std::string &label,
    const FindHudFontFn &findHudFontFn,
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

    if (!pFont->smooth && fontScale >= 1.0f)
    {
        fontScale = snappedHudFontScale(fontScale);
    }

    const float labelHeightPixels = static_cast<float>(pFont->fontHeight) * fontScale;
    const float maxLabelWidth = std::max(0.0f, resolved.width - std::abs(layout.textPadX * fontScale) * 2.0f);
    std::string clampedLabel = clampHudTextToWidth(*pFont, label, maxLabelWidth / fontScale);

    if (clampedLabel.empty())
    {
        const GameplayHudFontData *pFallbackFont = findHudFontFn("Lucida");

        if (pFallbackFont != nullptr)
        {
            pFont = pFallbackFont;
            clampedLabel = clampHudTextToWidth(*pFont, label, maxLabelWidth / fontScale);
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

    renderHudFontLayerFn(*pFont, pFont->shadowTextureHandle, clampedLabel, textX, textY, fontScale);
    renderHudFontLayerFn(*pFont, hudFontMainLayer(*pFont, layout.textColorAbgr), clampedLabel, textX, textY,
        fontScale);
}
} // namespace OpenYAMM::Game
