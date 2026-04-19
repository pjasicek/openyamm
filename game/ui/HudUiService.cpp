#include "game/ui/HudUiService.h"

#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayOverlayContext.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/render/TextureFiltering.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <array>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t HudViewId = 2;
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

const UiLayoutManager::LayoutElement *HudUiService::findHudLayoutElement(
    const GameplayOverlayContext &view,
    const std::string &layoutId)
{
    return view.findHudLayoutElement(layoutId);
}

std::vector<std::string> HudUiService::sortedHudLayoutIdsForScreen(
    const OutdoorGameView &view,
    const std::string &screen)
{
    return view.m_uiLayoutManager.sortedLayoutIdsForScreen(screen);
}

std::vector<std::string> HudUiService::sortedHudLayoutIdsForScreen(
    const GameplayOverlayContext &view,
    const std::string &screen)
{
    return view.sortedHudLayoutIdsForScreen(screen);
}

const std::vector<std::string> &HudUiService::sortedHudLayoutIdsForScreenCached(
    const OutdoorGameView &view,
    const std::string &screen)
{
    return view.m_uiLayoutManager.sortedLayoutIdsForScreenCached(screen);
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
    if (const OutdoorGameView::HudFontHandle *pLoadedFont =
            GameplayHudCommon::findHudFont(view.m_hudFontHandles, fontName))
    {
        return pLoadedFont;
    }

    if (!fontName.empty() && view.m_pAssetFileSystem != nullptr)
    {
        OutdoorGameView &mutableView = const_cast<OutdoorGameView &>(view);

        if (mutableView.loadHudFont(*view.m_pAssetFileSystem, fontName))
        {
            if (const OutdoorGameView::HudFontHandle *pReloadedFont =
                    GameplayHudCommon::findHudFont(view.m_hudFontHandles, fontName))
            {
                static std::unordered_set<std::string> lazyReloadLogs;
                const std::string normalizedFontName = toLowerCopy(fontName);
                const std::string logKey = "lazy-font:" + normalizedFontName;

                if (!lazyReloadLogs.contains(logKey))
                {
                    std::cout << "HUD font lazy-reloaded: font=\"" << fontName << "\"\n";
                    lazyReloadLogs.insert(logKey);
                }

                return pReloadedFont;
            }
        }
    }

    return nullptr;
}

std::optional<GameplayHudFontHandle> HudUiService::findHudFont(
    const GameplayOverlayContext &view,
    const std::string &fontName)
{
    return view.findHudFont(fontName);
}

float HudUiService::measureHudTextWidth(
    const OutdoorGameView &view,
    const OutdoorGameView::HudFontHandle &font,
    const std::string &text)
{
    (void)view;
    return GameplayHudCommon::measureHudTextWidth(font, text);
}

float HudUiService::measureHudTextWidth(
    const GameplayOverlayContext &view,
    const GameplayHudFontHandle &font,
    const std::string &text)
{
    return view.measureHudTextWidth(font, text);
}

std::string HudUiService::clampHudTextToWidth(
    const OutdoorGameView &view,
    const OutdoorGameView::HudFontHandle &font,
    const std::string &text,
    float maxWidth)
{
    (void)view;
    return GameplayHudCommon::clampHudTextToWidth(font, text, maxWidth);
}

std::vector<std::string> HudUiService::wrapHudTextToWidth(
    const OutdoorGameView &view,
    const OutdoorGameView::HudFontHandle &font,
    const std::string &text,
    float maxWidth)
{
    (void)view;
    return GameplayHudCommon::wrapHudTextToWidth(font, text, maxWidth);
}

std::vector<std::string> HudUiService::wrapHudTextToWidth(
    const GameplayOverlayContext &view,
    const GameplayHudFontHandle &font,
    const std::string &text,
    float maxWidth)
{
    return view.wrapHudTextToWidth(font, text, maxWidth);
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
    GameplayHudCommon::renderHudFontLayer(
        font,
        textureHandle,
        text,
        textX,
        textY,
        fontScale,
        [&view](bgfx::TextureHandle submittedTextureHandle,
                float x,
                float y,
                float quadWidth,
                float quadHeight,
                float u0,
                float v0,
                float u1,
                float v1,
                TextureFilterProfile filterProfile)
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::TransientIndexBuffer transientIndexBuffer = {};

            if (!bgfx::allocTransientBuffers(
                    &transientVertexBuffer,
                    OutdoorGameView::TexturedTerrainVertex::ms_layout,
                    4,
                    &transientIndexBuffer,
                    6))
            {
                return;
            }

            auto *pVertices =
                reinterpret_cast<OutdoorGameView::TexturedTerrainVertex *>(transientVertexBuffer.data);
            pVertices[0] = {x, y, 0.0f, u0, v0};
            pVertices[1] = {x + quadWidth, y, 0.0f, u1, v0};
            pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
            pVertices[3] = {x, y + quadHeight, 0.0f, u0, v1};

            uint16_t *pIndices = reinterpret_cast<uint16_t *>(transientIndexBuffer.data);
            pIndices[0] = 0;
            pIndices[1] = 1;
            pIndices[2] = 2;
            pIndices[3] = 0;
            pIndices[4] = 2;
            pIndices[5] = 3;

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setIndexBuffer(&transientIndexBuffer);
            bindTexture(0, view.m_terrainTextureSamplerHandle, submittedTextureHandle, filterProfile);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, view.m_texturedTerrainProgramHandle);
        });
}

void HudUiService::renderHudFontLayer(
    const GameplayOverlayContext &view,
    const GameplayHudFontHandle &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale)
{
    view.renderHudFontLayer(font, textureHandle, text, textX, textY, fontScale);
}

bgfx::TextureHandle HudUiService::ensureHudFontMainTextureColor(
    const OutdoorGameView &view,
    const OutdoorGameView::HudFontHandle &font,
    uint32_t colorAbgr)
{
    return GameplayHudCommon::ensureHudFontMainTextureColor(
        font,
        colorAbgr,
        view.m_hudFontColorTextureHandles);
}

bgfx::TextureHandle HudUiService::ensureHudFontMainTextureColor(
    const GameplayOverlayContext &view,
    const GameplayHudFontHandle &font,
    uint32_t colorAbgr)
{
    return view.ensureHudFontMainTextureColor(font, colorAbgr);
}

bgfx::TextureHandle HudUiService::ensureHudTextureColor(
    const OutdoorGameView &view,
    const OutdoorGameView::HudTextureHandle &texture,
    uint32_t colorAbgr)
{
    return GameplayHudCommon::ensureHudTextureColor(
        texture,
        colorAbgr,
        view.m_hudTextureColorTextureHandles);
}

bgfx::TextureHandle HudUiService::ensureHudTextureColor(
    const GameplayOverlayContext &view,
    const GameplayHudTextureHandle &texture,
    uint32_t colorAbgr)
{
    return view.ensureHudTextureColor(texture, colorAbgr);
}

void HudUiService::renderLayoutLabel(
    const OutdoorGameView &view,
    const OutdoorGameView::HudLayoutElement &layout,
    const OutdoorGameView::ResolvedHudLayoutElement &resolved,
    const std::string &label)
{
    GameplayHudCommon::renderLayoutLabel(
        layout,
        resolved,
        label,
        [&view](const std::string &fontName) -> const GameplayHudFontData *
        {
            return HudUiService::findHudFont(view, fontName);
        },
        [&view](const GameplayHudFontData &font, uint32_t colorAbgr) -> bgfx::TextureHandle
        {
            return HudUiService::ensureHudFontMainTextureColor(view, font, colorAbgr);
        },
        [&view](const GameplayHudFontData &font,
                bgfx::TextureHandle textureHandle,
                const std::string &text,
                float textX,
                float textY,
                float fontScale)
        {
            HudUiService::renderHudFontLayer(view, font, textureHandle, text, textX, textY, fontScale);
        });
}

void HudUiService::renderLayoutLabel(
    const GameplayOverlayContext &view,
    const UiLayoutManager::LayoutElement &layout,
    const GameplayResolvedHudLayoutElement &resolved,
    const std::string &label)
{
    view.renderLayoutLabel(layout, resolved, label);
}

const OutdoorGameView::HudTextureHandle *HudUiService::findHudTexture(
    const OutdoorGameView &view,
    const std::string &textureName)
{
    return GameplayHudCommon::findHudTexture(view.m_hudTextureHandles, view.m_hudTextureIndexByName, textureName);
}

const OutdoorGameView::HudTextureHandle *HudUiService::ensureHudTextureLoaded(
    OutdoorGameView &view,
    const std::string &textureName)
{
    if (textureName.empty())
    {
        return nullptr;
    }

    if (view.m_pAssetFileSystem == nullptr)
    {
        return nullptr;
    }

    if (!GameplayHudCommon::loadHudTexture(
            view.m_pAssetFileSystem,
            view.m_spriteLoadCache,
            textureName,
            view.m_hudTextureHandles,
            view.m_hudTextureIndexByName))
    {
        return nullptr;
    }

    return GameplayHudCommon::findHudTexture(view.m_hudTextureHandles, view.m_hudTextureIndexByName, textureName);
}

std::optional<GameplayHudTextureHandle> HudUiService::ensureHudTextureLoaded(
    GameplayOverlayContext &view,
    const std::string &textureName)
{
    return view.ensureHudTextureLoaded(textureName);
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
    textureHandle.textureHandle = createBgraTexture2D(
        1,
        1,
        pixel.data(),
        uint32_t(pixel.size()),
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
    );

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        return nullptr;
    }

    const size_t index = view.m_hudTextureHandles.size();
    view.m_hudTextureHandles.push_back(std::move(textureHandle));
    view.m_hudTextureIndexByName[view.m_hudTextureHandles.back().textureName] = index;
    return &view.m_hudTextureHandles.back();
}

std::optional<GameplayHudTextureHandle> HudUiService::ensureSolidHudTextureLoaded(
    GameplayOverlayContext &view,
    const std::string &textureName,
    uint32_t abgrColor)
{
    return view.ensureSolidHudTextureLoaded(textureName, abgrColor);
}

void HudUiService::renderViewportSidePanels(
    const OutdoorGameView &view,
    int screenWidth,
    int screenHeight,
    const std::string &textureName)
{
    if (screenWidth <= 0 || screenHeight <= 0)
    {
        return;
    }

    const GameplayUiViewportRect viewport = GameplayHudCommon::computeUiViewportRect(screenWidth, screenHeight);

    if (viewport.x <= 0.5f)
    {
        return;
    }

    const OutdoorGameView::HudTextureHandle *pTexture =
        ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), textureName);

    if (pTexture == nullptr)
    {
        return;
    }

    view.submitHudTexturedQuad(*pTexture, 0.0f, 0.0f, viewport.x, static_cast<float>(screenHeight));

    const float rightX = viewport.x + viewport.width;
    const float rightWidth = static_cast<float>(screenWidth) - rightX;

    if (rightWidth > 0.5f)
    {
        view.submitHudTexturedQuad(*pTexture, rightX, 0.0f, rightWidth, static_cast<float>(screenHeight));
    }
}

void HudUiService::renderViewportSidePanels(
    GameplayOverlayContext &view,
    int screenWidth,
    int screenHeight,
    const std::string &textureName)
{
    if (screenWidth <= 0 || screenHeight <= 0)
    {
        return;
    }

    const GameplayUiViewportRect viewport = GameplayHudCommon::computeUiViewportRect(screenWidth, screenHeight);

    if (viewport.x <= 0.5f)
    {
        return;
    }

    const std::optional<GameplayHudTextureHandle> texture =
        view.ensureHudTextureLoaded(textureName);

    if (!texture)
    {
        return;
    }

    view.submitHudTexturedQuad(*texture, 0.0f, 0.0f, viewport.x, static_cast<float>(screenHeight));

    const float rightX = viewport.x + viewport.width;
    const float rightWidth = static_cast<float>(screenWidth) - rightX;

    if (rightWidth > 0.5f)
    {
        view.submitHudTexturedQuad(*texture, rightX, 0.0f, rightWidth, static_cast<float>(screenHeight));
    }
}

std::optional<OutdoorGameView::ResolvedHudLayoutElement> HudUiService::resolveHudLayoutElement(
    const OutdoorGameView &view,
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight)
{
    return GameplayHudCommon::resolveHudLayoutElement(
        view.m_uiLayoutManager,
        view.m_hudLayoutRuntimeHeightOverrides,
        layoutId,
        screenWidth,
        screenHeight,
        fallbackWidth,
        fallbackHeight);
}

std::optional<GameplayResolvedHudLayoutElement> HudUiService::resolveHudLayoutElement(
    const GameplayOverlayContext &view,
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight)
{
    return view.resolveHudLayoutElement(layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight);
}

bool HudUiService::isPointerInsideResolvedElement(
    const OutdoorGameView::ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY)
{
    return GameplayHudCommon::isPointerInsideResolvedElement(resolved, pointerX, pointerY);
}

const std::string *HudUiService::resolveInteractiveAssetName(
    const OutdoorGameView::HudLayoutElement &layout,
    const OutdoorGameView::ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY,
    bool isLeftMousePressed)
{
    return GameplayHudCommon::resolveInteractiveAssetName(layout, resolved, pointerX, pointerY, isLeftMousePressed);
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
    const OutdoorGameView::HudTextureHandle *pTexture = ensureHudTextureLoaded(view, textureName);

    if (pTexture == nullptr)
    {
        width = 0;
        height = 0;
        opaqueMinX = -1;
        opaqueMinY = -1;
        opaqueMaxX = -1;
        opaqueMaxY = -1;
        return false;
    }

    const Engine::AssetScaleTier assetScaleTier =
        view.m_pAssetFileSystem != nullptr ? view.m_pAssetFileSystem->getAssetScaleTier() : Engine::AssetScaleTier::X1;
    return GameplayHudCommon::tryGetOpaqueHudTextureBounds(
        *pTexture,
        assetScaleTier,
        width,
        height,
        opaqueMinX,
        opaqueMinY,
        opaqueMaxX,
        opaqueMaxY);
}

bool HudUiService::tryGetOpaqueHudTextureBounds(
    GameplayOverlayContext &view,
    const std::string &textureName,
    int &width,
    int &height,
    int &opaqueMinX,
    int &opaqueMinY,
    int &opaqueMaxX,
    int &opaqueMaxY)
{
    return view.tryGetOpaqueHudTextureBounds(
        textureName,
        width,
        height,
        opaqueMinX,
        opaqueMinY,
        opaqueMaxX,
        opaqueMaxY);
}
} // namespace OpenYAMM::Game
