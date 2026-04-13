#include "game/ui/HudUiService.h"

#include "game/outdoor/OutdoorGameView.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr uint16_t HudViewId = 2;
struct UiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

int scaleOpaqueMaxToLogical(int physicalMax, Engine::AssetScaleTier assetScaleTier)
{
    if (physicalMax < 0)
    {
        return -1;
    }

    return Engine::scalePhysicalPixelsToLogical(physicalMax + 1, assetScaleTier) - 1;
}

float snappedHudFontScale(float scale)
{
    const float roundedScale = std::round(scale);

    if (std::abs(scale - roundedScale) <= HudFontIntegerSnapThreshold)
    {
        return std::max(1.0f, roundedScale);
    }

    return std::max(1.0f, scale);
}

UiViewportRect computeUiViewportRect(int screenWidth, int screenHeight)
{
    UiViewportRect viewport = {};
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

} // namespace

bool HudUiService::loadHudLayout(OutdoorGameView &view, const Engine::AssetFileSystem &assetFileSystem)
{
    view.m_uiLayoutManager.clear();

    return view.m_gameplayUiController.loadGameplayLayouts(
        assetFileSystem,
        [&view, &assetFileSystem](const std::string &path) -> bool
        {
            return view.m_uiLayoutManager.loadLayoutFile(assetFileSystem, path);
        });
}

const OutdoorGameView::HudLayoutElement *HudUiService::findHudLayoutElement(
    const OutdoorGameView &view,
    const std::string &layoutId)
{
    return view.m_uiLayoutManager.findElement(layoutId);
}

std::vector<std::string> HudUiService::sortedHudLayoutIdsForScreen(
    const OutdoorGameView &view,
    const std::string &screen)
{
    return view.m_uiLayoutManager.sortedLayoutIdsForScreen(screen);
}

int HudUiService::maxHudLayoutZIndexForScreen(const OutdoorGameView &view, const std::string &screen)
{
    return view.m_uiLayoutManager.maxZIndexForScreen(screen);
}

int HudUiService::defaultHudLayoutZIndexForScreen(const std::string &screen)
{
    return UiLayoutManager::defaultZIndexForScreen(screen);
}

const OutdoorGameView::HudFontHandle *HudUiService::findHudFont(
    const OutdoorGameView &view,
    const std::string &fontName)
{
    const std::string normalizedFontName = toLowerCopy(fontName);

    for (const OutdoorGameView::HudFontHandle &fontHandle : view.m_hudFontHandles)
    {
        if (fontHandle.fontName == normalizedFontName)
        {
            return &fontHandle;
        }
    }

    return nullptr;
}

float HudUiService::measureHudTextWidth(
    const OutdoorGameView &view,
    const OutdoorGameView::HudFontHandle &font,
    const std::string &text)
{
    (void)view;

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

        const OutdoorGameView::HudFontGlyphMetrics &glyphMetrics = font.glyphMetrics[character];
        widthPixels += static_cast<float>(
            glyphMetrics.leftSpacing
            + glyphMetrics.width
            + glyphMetrics.rightSpacing);
    }

    return std::max(0.0f, widthPixels);
}

std::string HudUiService::clampHudTextToWidth(
    const OutdoorGameView &view,
    const OutdoorGameView::HudFontHandle &font,
    const std::string &text,
    float maxWidth)
{
    std::string clampedText = text;

    while (!clampedText.empty() && measureHudTextWidth(view, font, clampedText) > maxWidth)
    {
        clampedText.pop_back();
    }

    return clampedText;
}

std::vector<std::string> HudUiService::wrapHudTextToWidth(
    const OutdoorGameView &view,
    const OutdoorGameView::HudFontHandle &font,
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
        [&view, &font, &currentLine, &flushLine, maxWidth](const std::string &word)
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

            if (measureHudTextWidth(view, font, candidate) <= maxWidth)
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

void HudUiService::renderHudFontLayer(
    const OutdoorGameView &view,
    const OutdoorGameView::HudFontHandle &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale)
{
    if (!bgfx::isValid(textureHandle))
    {
        return;
    }

    uint32_t glyphCount = 0;

    for (unsigned char character : text)
    {
        if (character == '\r' || character == '\n')
        {
            break;
        }

        if (character >= font.firstChar
            && character <= font.lastChar
            && font.glyphMetrics[character].width > 0)
        {
            ++glyphCount;
        }
    }

    if (glyphCount == 0)
    {
        return;
    }

    const uint32_t vertexCount = glyphCount * 6;

    if (bgfx::getAvailTransientVertexBuffer(vertexCount, OutdoorGameView::TexturedTerrainVertex::ms_layout) < vertexCount)
    {
        return;
    }

    bgfx::TransientVertexBuffer transientVertexBuffer;
    bgfx::allocTransientVertexBuffer(&transientVertexBuffer, vertexCount, OutdoorGameView::TexturedTerrainVertex::ms_layout);
    auto *pVertices = reinterpret_cast<OutdoorGameView::TexturedTerrainVertex *>(transientVertexBuffer.data);
    float penX = textX;
    uint32_t vertexIndex = 0;

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

        const OutdoorGameView::HudFontGlyphMetrics &glyphMetrics = font.glyphMetrics[character];
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

            pVertices[vertexIndex + 0] = {penX, textY, 0.0f, u0, v0};
            pVertices[vertexIndex + 1] = {penX + glyphWidth, textY, 0.0f, u1, v0};
            pVertices[vertexIndex + 2] = {penX + glyphWidth, textY + glyphHeight, 0.0f, u1, v1};
            pVertices[vertexIndex + 3] = {penX, textY, 0.0f, u0, v0};
            pVertices[vertexIndex + 4] = {penX + glyphWidth, textY + glyphHeight, 0.0f, u1, v1};
            pVertices[vertexIndex + 5] = {penX, textY + glyphHeight, 0.0f, u0, v1};
            vertexIndex += 6;
        }

        penX += static_cast<float>(glyphMetrics.width + glyphMetrics.rightSpacing) * fontScale;
    }

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer);
    bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, textureHandle);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(HudViewId, view.m_texturedTerrainProgramHandle);
}

bgfx::TextureHandle HudUiService::ensureHudFontMainTextureColor(
    const OutdoorGameView &view,
    const OutdoorGameView::HudFontHandle &font,
    uint32_t colorAbgr)
{
    if (colorAbgr == 0xffffffffu)
    {
        return font.mainTextureHandle;
    }

    for (const OutdoorGameView::HudFontColorTextureHandle &textureHandle : view.m_hudFontColorTextureHandles)
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

    const bgfx::TextureHandle textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(font.atlasWidth),
        static_cast<uint16_t>(font.atlasHeight),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(tintedPixels.data(), static_cast<uint32_t>(tintedPixels.size()))
    );

    if (!bgfx::isValid(textureHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    OutdoorGameView::HudFontColorTextureHandle tintedTextureHandle = {};
    tintedTextureHandle.fontName = font.fontName;
    tintedTextureHandle.colorAbgr = colorAbgr;
    tintedTextureHandle.textureHandle = textureHandle;
    view.m_hudFontColorTextureHandles.push_back(std::move(tintedTextureHandle));
    return view.m_hudFontColorTextureHandles.back().textureHandle;
}

bgfx::TextureHandle HudUiService::ensureHudTextureColor(
    const OutdoorGameView &view,
    const OutdoorGameView::HudTextureHandle &texture,
    uint32_t colorAbgr)
{
    if (colorAbgr == 0xffffffffu)
    {
        return texture.textureHandle;
    }

    for (const OutdoorGameView::HudTextureColorTextureHandle &textureHandle : view.m_hudTextureColorTextureHandles)
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

    const bgfx::TextureHandle textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(texture.physicalWidth),
        static_cast<uint16_t>(texture.physicalHeight),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(tintedPixels.data(), static_cast<uint32_t>(tintedPixels.size()))
    );

    if (!bgfx::isValid(textureHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    OutdoorGameView::HudTextureColorTextureHandle tintedTextureHandle = {};
    tintedTextureHandle.textureName = texture.textureName;
    tintedTextureHandle.colorAbgr = colorAbgr;
    tintedTextureHandle.textureHandle = textureHandle;
    view.m_hudTextureColorTextureHandles.push_back(std::move(tintedTextureHandle));
    return view.m_hudTextureColorTextureHandles.back().textureHandle;
}

void HudUiService::renderLayoutLabel(
    const OutdoorGameView &view,
    const OutdoorGameView::HudLayoutElement &layout,
    const OutdoorGameView::ResolvedHudLayoutElement &resolved,
    const std::string &label)
{
    if (label.empty())
    {
        return;
    }

    const OutdoorGameView::HudFontHandle *pFont = findHudFont(view, layout.fontName);

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
    std::string clampedLabel = clampHudTextToWidth(view, *pFont, label, maxLabelWidth);

    if (clampedLabel.empty())
    {
        const OutdoorGameView::HudFontHandle *pFallbackFont = findHudFont(view, "Lucida");

        if (pFallbackFont != nullptr)
        {
            pFont = pFallbackFont;
            clampedLabel = clampHudTextToWidth(view, *pFont, label, maxLabelWidth);
        }

        static std::unordered_set<std::string> emptyClampLogs;
        const std::string logKey = "empty-clamp:" + toLowerCopy(layout.id) + ":" + label;

        if (!emptyClampLogs.contains(logKey))
        {
            std::cout << "HUD label clamp empty: id=" << layout.id
                      << " font=\"" << layout.fontName
                      << "\" fallback_font=\"" << (pFallbackFont != nullptr ? pFallbackFont->fontName : "")
                      << "\" label=\"" << label
                      << "\" width=" << resolved.width
                      << " max_width=" << maxLabelWidth
                      << " scale=" << resolved.scale << '\n';
            emptyClampLogs.insert(logKey);
        }
    }

    if (clampedLabel.empty())
    {
        clampedLabel = label;
    }

    const float labelWidthPixels = measureHudTextWidth(view, *pFont, clampedLabel) * fontScale;
    float textX = resolved.x + layout.textPadX * resolved.scale;
    float textY = resolved.y + layout.textPadY * resolved.scale;

    switch (layout.textAlignX)
    {
    case OutdoorGameView::HudTextAlignX::Left:
        break;

    case OutdoorGameView::HudTextAlignX::Center:
        textX = resolved.x + (resolved.width - labelWidthPixels) * 0.5f + layout.textPadX * resolved.scale;
        break;

    case OutdoorGameView::HudTextAlignX::Right:
        textX = resolved.x + resolved.width - labelWidthPixels + layout.textPadX * resolved.scale;
        break;
    }

    switch (layout.textAlignY)
    {
    case OutdoorGameView::HudTextAlignY::Top:
        break;

    case OutdoorGameView::HudTextAlignY::Middle:
        textY = resolved.y + (resolved.height - labelHeightPixels) * 0.5f + layout.textPadY * resolved.scale;
        break;

    case OutdoorGameView::HudTextAlignY::Bottom:
        textY = resolved.y + resolved.height - labelHeightPixels + layout.textPadY * resolved.scale;
        break;
    }

    textX = std::round(textX);
    textY = std::round(textY);

    bgfx::TextureHandle coloredMainTextureHandle = ensureHudFontMainTextureColor(view, *pFont, layout.textColorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = pFont->mainTextureHandle;
    }

    renderHudFontLayer(view, *pFont, pFont->shadowTextureHandle, clampedLabel, textX, textY, fontScale);
    renderHudFontLayer(view, *pFont, coloredMainTextureHandle, clampedLabel, textX, textY, fontScale);
}

const OutdoorGameView::HudTextureHandle *HudUiService::findHudTexture(
    const OutdoorGameView &view,
    const std::string &textureName)
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const OutdoorGameView::HudTextureHandle &textureHandle : view.m_hudTextureHandles)
    {
        if (textureHandle.textureName == normalizedTextureName)
        {
            return &textureHandle;
        }
    }

    return nullptr;
}

const OutdoorGameView::HudTextureHandle *HudUiService::ensureHudTextureLoaded(
    OutdoorGameView &view,
    const std::string &textureName)
{
    if (textureName.empty())
    {
        return nullptr;
    }

    const OutdoorGameView::HudTextureHandle *pTexture = findHudTexture(view, textureName);

    if (pTexture != nullptr)
    {
        return pTexture;
    }

    if (view.m_pAssetFileSystem == nullptr)
    {
        return nullptr;
    }

    if (!view.loadHudTexture(*view.m_pAssetFileSystem, textureName))
    {
        return nullptr;
    }

    return findHudTexture(view, textureName);
}

const OutdoorGameView::HudTextureHandle *HudUiService::ensureSolidHudTextureLoaded(
    OutdoorGameView &view,
    const std::string &textureName,
    uint32_t abgrColor)
{
    if (textureName.empty())
    {
        return nullptr;
    }

    const std::string cacheTextureName =
        toLowerCopy(textureName)
        + "_"
        + std::to_string((abgrColor >> 24) & 0xffu)
        + "_"
        + std::to_string((abgrColor >> 16) & 0xffu)
        + "_"
        + std::to_string((abgrColor >> 8) & 0xffu)
        + "_"
        + std::to_string(abgrColor & 0xffu);
    const OutdoorGameView::HudTextureHandle *pTexture = findHudTexture(view, cacheTextureName);

    if (pTexture != nullptr)
    {
        return pTexture;
    }

    const std::array<uint8_t, 4> pixel = {
        static_cast<uint8_t>((abgrColor >> 16) & 0xff),
        static_cast<uint8_t>((abgrColor >> 8) & 0xff),
        static_cast<uint8_t>(abgrColor & 0xff),
        static_cast<uint8_t>((abgrColor >> 24) & 0xff)
    };

    OutdoorGameView::HudTextureHandle textureHandle = {};
    textureHandle.textureName = cacheTextureName;
    textureHandle.width = 1;
    textureHandle.height = 1;
    textureHandle.physicalWidth = 1;
    textureHandle.physicalHeight = 1;
    textureHandle.bgraPixels.assign(pixel.begin(), pixel.end());
    textureHandle.textureHandle = bgfx::createTexture2D(
        1,
        1,
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(pixel.data(), static_cast<uint32_t>(pixel.size()))
    );

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        return nullptr;
    }

    view.m_hudTextureHandles.push_back(std::move(textureHandle));
    return &view.m_hudTextureHandles.back();
}

std::optional<OutdoorGameView::ResolvedHudLayoutElement> HudUiService::resolveHudLayoutElement(
    const OutdoorGameView &view,
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight)
{
    std::unordered_set<std::string> visited;
    return resolveHudLayoutElementRecursive(view, layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight, visited);
}

std::optional<OutdoorGameView::ResolvedHudLayoutElement> HudUiService::resolveHudLayoutElementRecursive(
    const OutdoorGameView &view,
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight,
    std::unordered_set<std::string> &visited)
{
    const std::string normalizedLayoutId = toLowerCopy(layoutId);

    if (visited.contains(normalizedLayoutId))
    {
        std::cerr << "HUD layout cycle detected at element: " << layoutId << '\n';
        return std::nullopt;
    }

    visited.insert(normalizedLayoutId);
    const OutdoorGameView::HudLayoutElement *pElement = findHudLayoutElement(view, layoutId);

    if (pElement == nullptr)
    {
        return std::nullopt;
    }

    const OutdoorGameView::HudLayoutElement &element = *pElement;
    const UiViewportRect uiViewport = computeUiViewportRect(screenWidth, screenHeight);
    const float baseScale = std::min(
        uiViewport.width / HudReferenceWidth,
        uiViewport.height / HudReferenceHeight);
    const auto runtimeHeightOverrideIterator = view.m_hudLayoutRuntimeHeightOverrides.find(normalizedLayoutId);
    const float effectiveHeight = runtimeHeightOverrideIterator != view.m_hudLayoutRuntimeHeightOverrides.end()
        ? runtimeHeightOverrideIterator->second
        : (element.height > 0.0f ? element.height : fallbackHeight);

    OutdoorGameView::ResolvedHudLayoutElement resolved = {};

    if (!element.parentId.empty() && element.attachTo != OutdoorGameView::HudLayoutAttachMode::None)
    {
        const OutdoorGameView::HudLayoutElement *pParent = findHudLayoutElement(view, element.parentId);

        if (pParent == nullptr)
        {
            return std::nullopt;
        }

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> parent = resolveHudLayoutElementRecursive(
            view,
            element.parentId,
            screenWidth,
            screenHeight,
            pParent->width,
            pParent->height,
            visited);

        if (!parent)
        {
            return std::nullopt;
        }

        resolved.scale = element.hasExplicitScale
            ? std::clamp(baseScale, element.minScale, element.maxScale)
            : parent->scale;
        resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
        resolved.height = effectiveHeight * resolved.scale;

        resolved = OutdoorGameView::resolveAttachedHudLayoutRect(
            element.attachTo,
            *parent,
            resolved.width,
            resolved.height,
            element.gapX,
            element.gapY,
            resolved.scale);

        if (!element.bottomToId.empty())
        {
            const OutdoorGameView::HudLayoutElement *pBottomTo = findHudLayoutElement(view, element.bottomToId);

            if (pBottomTo != nullptr)
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bottomTo = resolveHudLayoutElementRecursive(
                    view,
                    element.bottomToId,
                    screenWidth,
                    screenHeight,
                    pBottomTo->width,
                    pBottomTo->height,
                    visited);

                if (bottomTo)
                {
                    resolved.height = std::max(0.0f, bottomTo->y + element.bottomGap * resolved.scale - resolved.y);
                }
            }
        }

        visited.erase(normalizedLayoutId);
        return resolved;
    }

    resolved.scale = std::clamp(baseScale, element.minScale, element.maxScale);
    resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
    resolved.height = effectiveHeight * resolved.scale;

    switch (element.anchor)
    {
    case OutdoorGameView::HudLayoutAnchor::TopLeft:
        resolved.x = uiViewport.x + element.offsetX * resolved.scale;
        resolved.y = uiViewport.y + element.offsetY * resolved.scale;
        break;

    case OutdoorGameView::HudLayoutAnchor::TopCenter:
        resolved.x = uiViewport.x + uiViewport.width * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
        resolved.y = uiViewport.y + element.offsetY * resolved.scale;
        break;

    case OutdoorGameView::HudLayoutAnchor::TopRight:
        resolved.x = uiViewport.x + uiViewport.width - resolved.width + element.offsetX * resolved.scale;
        resolved.y = uiViewport.y + element.offsetY * resolved.scale;
        break;

    case OutdoorGameView::HudLayoutAnchor::Left:
        resolved.x = uiViewport.x + element.offsetX * resolved.scale;
        resolved.y = uiViewport.y + uiViewport.height * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
        break;

    case OutdoorGameView::HudLayoutAnchor::Center:
        resolved.x = uiViewport.x + uiViewport.width * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
        resolved.y = uiViewport.y + uiViewport.height * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
        break;

    case OutdoorGameView::HudLayoutAnchor::Right:
        resolved.x = uiViewport.x + uiViewport.width - resolved.width + element.offsetX * resolved.scale;
        resolved.y = uiViewport.y + uiViewport.height * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
        break;

    case OutdoorGameView::HudLayoutAnchor::BottomLeft:
        resolved.x = uiViewport.x + element.offsetX * resolved.scale;
        resolved.y = uiViewport.y + uiViewport.height - resolved.height + element.offsetY * resolved.scale;
        break;

    case OutdoorGameView::HudLayoutAnchor::BottomCenter:
        resolved.x = uiViewport.x + uiViewport.width * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
        resolved.y = uiViewport.y + uiViewport.height - resolved.height + element.offsetY * resolved.scale;
        break;

    case OutdoorGameView::HudLayoutAnchor::BottomRight:
        resolved.x = uiViewport.x + uiViewport.width - resolved.width + element.offsetX * resolved.scale;
        resolved.y = uiViewport.y + uiViewport.height - resolved.height + element.offsetY * resolved.scale;
        break;
    }

    if (!element.bottomToId.empty())
    {
        const OutdoorGameView::HudLayoutElement *pBottomTo = findHudLayoutElement(view, element.bottomToId);

        if (pBottomTo != nullptr)
        {
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bottomTo = resolveHudLayoutElementRecursive(
                view,
                element.bottomToId,
                screenWidth,
                screenHeight,
                pBottomTo->width,
                pBottomTo->height,
                visited);

            if (bottomTo)
            {
                resolved.height = std::max(0.0f, bottomTo->y + element.bottomGap * resolved.scale - resolved.y);
            }
        }
    }

    visited.erase(normalizedLayoutId);
    return resolved;
}

bool HudUiService::isPointerInsideResolvedElement(
    const OutdoorGameView::ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY)
{
    return pointerX >= resolved.x
        && pointerX < resolved.x + resolved.width
        && pointerY >= resolved.y
        && pointerY < resolved.y + resolved.height;
}

const std::string *HudUiService::resolveInteractiveAssetName(
    const OutdoorGameView::HudLayoutElement &layout,
    const OutdoorGameView::ResolvedHudLayoutElement &resolved,
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

bool HudUiService::tryGetOpaqueHudTextureBounds(
    OutdoorGameView &view,
    const std::string &textureName,
    int &width,
    int &height,
    int &opaqueMinX,
    int &opaqueMinY,
    int &opaqueMaxX,
    int &opaqueMaxY)
{
    const Engine::AssetScaleTier assetScaleTier =
        view.m_pAssetFileSystem != nullptr ? view.m_pAssetFileSystem->getAssetScaleTier() : Engine::AssetScaleTier::X1;
    const std::optional<std::vector<uint8_t>> pixels = view.loadHudBitmapPixelsBgraCached(textureName, width, height);

    if (!pixels || width <= 0 || height <= 0)
    {
        return false;
    }

    opaqueMinX = width;
    opaqueMinY = height;
    opaqueMaxX = -1;
    opaqueMaxY = -1;

    for (int y = 0; y < height; ++y)
    {
        for (int x = 0; x < width; ++x)
        {
            const size_t pixelOffset =
                (static_cast<size_t>(y) * static_cast<size_t>(width) + static_cast<size_t>(x)) * 4;

            if (pixelOffset + 3 >= pixels->size() || (*pixels)[pixelOffset + 3] == 0)
            {
                continue;
            }

            opaqueMinX = std::min(opaqueMinX, x);
            opaqueMinY = std::min(opaqueMinY, y);
            opaqueMaxX = std::max(opaqueMaxX, x);
            opaqueMaxY = std::max(opaqueMaxY, y);
        }
    }

    if (opaqueMaxX < opaqueMinX || opaqueMaxY < opaqueMinY)
    {
        opaqueMinX = 0;
        opaqueMinY = 0;
        opaqueMaxX = width - 1;
        opaqueMaxY = height - 1;
    }

    const int scaleFactor = Engine::assetScaleTierFactor(assetScaleTier);
    const int physicalWidth = width;
    const int physicalHeight = height;
    width = Engine::scalePhysicalPixelsToLogical(physicalWidth, assetScaleTier);
    height = Engine::scalePhysicalPixelsToLogical(physicalHeight, assetScaleTier);
    opaqueMinX /= scaleFactor;
    opaqueMinY /= scaleFactor;
    opaqueMaxX = scaleOpaqueMaxToLogical(opaqueMaxX, assetScaleTier);
    opaqueMaxY = scaleOpaqueMaxToLogical(opaqueMaxY, assetScaleTier);
    opaqueMinX = std::clamp(opaqueMinX, 0, width - 1);
    opaqueMinY = std::clamp(opaqueMinY, 0, height - 1);
    opaqueMaxX = std::clamp(opaqueMaxX, 0, width - 1);
    opaqueMaxY = std::clamp(opaqueMaxY, 0, height - 1);
    return true;
}
} // namespace OpenYAMM::Game
