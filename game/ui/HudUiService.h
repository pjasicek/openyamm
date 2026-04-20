#pragma once

#include "game/ui/GameplayOverlayContext.h"

#include <bgfx/bgfx.h>

#include <string>

namespace OpenYAMM::Game
{
class HudUiService
{
public:
    static const UiLayoutManager::LayoutElement *findHudLayoutElement(
        const GameplayOverlayContext &view,
        const std::string &layoutId);
    static std::vector<std::string> sortedHudLayoutIdsForScreen(
        const GameplayOverlayContext &view,
        const std::string &screen);
    static std::optional<GameplayHudFontHandle> findHudFont(
        const GameplayOverlayContext &view,
        const std::string &fontName);
    static float measureHudTextWidth(
        const GameplayOverlayContext &view,
        const GameplayHudFontHandle &font,
        const std::string &text);
    static std::vector<std::string> wrapHudTextToWidth(
        const GameplayOverlayContext &view,
        const GameplayHudFontHandle &font,
        const std::string &text,
        float maxWidth);
    static void renderHudFontLayer(
        const GameplayOverlayContext &view,
        const GameplayHudFontHandle &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale);
    static bgfx::TextureHandle ensureHudFontMainTextureColor(
        const GameplayOverlayContext &view,
        const GameplayHudFontHandle &font,
        uint32_t colorAbgr);
    static bgfx::TextureHandle ensureHudTextureColor(
        const GameplayOverlayContext &view,
        const GameplayHudTextureHandle &texture,
        uint32_t colorAbgr);
    static void renderLayoutLabel(
        const GameplayOverlayContext &view,
        const UiLayoutManager::LayoutElement &layout,
        const GameplayResolvedHudLayoutElement &resolved,
        const std::string &label);

    static std::optional<GameplayHudTextureHandle> ensureHudTextureLoaded(
        GameplayOverlayContext &view,
        const std::string &textureName);
    static std::optional<GameplayHudTextureHandle> ensureSolidHudTextureLoaded(
        GameplayOverlayContext &view,
        const std::string &textureName,
        uint32_t abgrColor);
    static void renderViewportSidePanels(
        GameplayOverlayContext &view,
        int screenWidth,
        int screenHeight,
        const std::string &textureName);
    static std::optional<GameplayResolvedHudLayoutElement> resolveHudLayoutElement(
        const GameplayOverlayContext &view,
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight);
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
