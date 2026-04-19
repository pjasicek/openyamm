#pragma once

#include "game/ui/GameplayOverlayContext.h"
#include "game/outdoor/OutdoorGameView.h"
#include "engine/AssetFileSystem.h"

#include <bgfx/bgfx.h>

#include <optional>
#include <string>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class HudUiService
{
public:
    static bool loadHudLayout(OutdoorGameView &view, const Engine::AssetFileSystem &assetFileSystem);

    static const OutdoorGameView::HudLayoutElement *findHudLayoutElement(
        const OutdoorGameView &view,
        const std::string &layoutId);
    static const UiLayoutManager::LayoutElement *findHudLayoutElement(
        const GameplayOverlayContext &view,
        const std::string &layoutId);
    static const std::vector<std::string> &sortedHudLayoutIdsForScreenCached(
        const OutdoorGameView &view,
        const std::string &screen);
    static std::vector<std::string> sortedHudLayoutIdsForScreen(const OutdoorGameView &view, const std::string &screen);
    static std::vector<std::string> sortedHudLayoutIdsForScreen(
        const GameplayOverlayContext &view,
        const std::string &screen);
    static int maxHudLayoutZIndexForScreen(const OutdoorGameView &view, const std::string &screen);
    static int defaultHudLayoutZIndexForScreen(const std::string &screen);

    static const OutdoorGameView::HudFontHandle *findHudFont(
        const OutdoorGameView &view,
        const std::string &fontName);
    static std::optional<GameplayHudFontHandle> findHudFont(
        const GameplayOverlayContext &view,
        const std::string &fontName);
    static float measureHudTextWidth(
        const OutdoorGameView &view,
        const OutdoorGameView::HudFontHandle &font,
        const std::string &text);
    static float measureHudTextWidth(
        const GameplayOverlayContext &view,
        const GameplayHudFontHandle &font,
        const std::string &text);
    static std::string clampHudTextToWidth(
        const OutdoorGameView &view,
        const OutdoorGameView::HudFontHandle &font,
        const std::string &text,
        float maxWidth);
    static std::vector<std::string> wrapHudTextToWidth(
        const OutdoorGameView &view,
        const OutdoorGameView::HudFontHandle &font,
        const std::string &text,
        float maxWidth);
    static std::vector<std::string> wrapHudTextToWidth(
        const GameplayOverlayContext &view,
        const GameplayHudFontHandle &font,
        const std::string &text,
        float maxWidth);
    static void renderHudFontLayer(
        const OutdoorGameView &view,
        const OutdoorGameView::HudFontHandle &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale);
    static void renderHudFontLayer(
        const GameplayOverlayContext &view,
        const GameplayHudFontHandle &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale);
    static bgfx::TextureHandle ensureHudFontMainTextureColor(
        const OutdoorGameView &view,
        const OutdoorGameView::HudFontHandle &font,
        uint32_t colorAbgr);
    static bgfx::TextureHandle ensureHudFontMainTextureColor(
        const GameplayOverlayContext &view,
        const GameplayHudFontHandle &font,
        uint32_t colorAbgr);
    static bgfx::TextureHandle ensureHudTextureColor(
        const OutdoorGameView &view,
        const OutdoorGameView::HudTextureHandle &texture,
        uint32_t colorAbgr);
    static bgfx::TextureHandle ensureHudTextureColor(
        const GameplayOverlayContext &view,
        const GameplayHudTextureHandle &texture,
        uint32_t colorAbgr);
    static void renderLayoutLabel(
        const OutdoorGameView &view,
        const OutdoorGameView::HudLayoutElement &layout,
        const OutdoorGameView::ResolvedHudLayoutElement &resolved,
        const std::string &label);
    static void renderLayoutLabel(
        const GameplayOverlayContext &view,
        const UiLayoutManager::LayoutElement &layout,
        const GameplayResolvedHudLayoutElement &resolved,
        const std::string &label);

    static const OutdoorGameView::HudTextureHandle *findHudTexture(
        const OutdoorGameView &view,
        const std::string &textureName);
    static const OutdoorGameView::HudTextureHandle *ensureHudTextureLoaded(
        OutdoorGameView &view,
        const std::string &textureName);
    static std::optional<GameplayHudTextureHandle> ensureHudTextureLoaded(
        GameplayOverlayContext &view,
        const std::string &textureName);
    static const OutdoorGameView::HudTextureHandle *ensureSolidHudTextureLoaded(
        OutdoorGameView &view,
        const std::string &textureName,
        uint32_t abgrColor);
    static std::optional<GameplayHudTextureHandle> ensureSolidHudTextureLoaded(
        GameplayOverlayContext &view,
        const std::string &textureName,
        uint32_t abgrColor);
    static void renderViewportSidePanels(
        const OutdoorGameView &view,
        int screenWidth,
        int screenHeight,
        const std::string &textureName);
    static void renderViewportSidePanels(
        GameplayOverlayContext &view,
        int screenWidth,
        int screenHeight,
        const std::string &textureName);
    static std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolveHudLayoutElement(
        const OutdoorGameView &view,
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight);
    static std::optional<GameplayResolvedHudLayoutElement> resolveHudLayoutElement(
        const GameplayOverlayContext &view,
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight);
    static bool isPointerInsideResolvedElement(
        const OutdoorGameView::ResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY);
    static const std::string *resolveInteractiveAssetName(
        const OutdoorGameView::HudLayoutElement &layout,
        const OutdoorGameView::ResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY,
        bool isLeftMousePressed);
    static bool tryGetOpaqueHudTextureBounds(
        OutdoorGameView &view,
        const std::string &textureName,
        int &width,
        int &height,
        int &opaqueMinX,
        int &opaqueMinY,
        int &opaqueMaxX,
        int &opaqueMaxY);
    static bool tryGetOpaqueHudTextureBounds(
        GameplayOverlayContext &view,
        const std::string &textureName,
        int &width,
        int &height,
        int &opaqueMinX,
        int &opaqueMinY,
        int &opaqueMaxX,
        int &opaqueMaxY);
};
} // namespace OpenYAMM::Game
