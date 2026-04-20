#include "game/ui/HudUiService.h"

#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayOverlayContext.h"

namespace OpenYAMM::Game
{
const UiLayoutManager::LayoutElement *HudUiService::findHudLayoutElement(
    const GameplayOverlayContext &view,
    const std::string &layoutId)
{
    return view.findHudLayoutElement(layoutId);
}

std::vector<std::string> HudUiService::sortedHudLayoutIdsForScreen(
    const GameplayOverlayContext &view,
    const std::string &screen)
{
    return view.sortedHudLayoutIdsForScreen(screen);
}

std::optional<GameplayHudFontHandle> HudUiService::findHudFont(
    const GameplayOverlayContext &view,
    const std::string &fontName)
{
    return view.findHudFont(fontName);
}

float HudUiService::measureHudTextWidth(
    const GameplayOverlayContext &view,
    const GameplayHudFontHandle &font,
    const std::string &text)
{
    return view.measureHudTextWidth(font, text);
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
    const GameplayOverlayContext &view,
    const GameplayHudFontHandle &font,
    uint32_t colorAbgr)
{
    return view.ensureHudFontMainTextureColor(font, colorAbgr);
}

bgfx::TextureHandle HudUiService::ensureHudTextureColor(
    const GameplayOverlayContext &view,
    const GameplayHudTextureHandle &texture,
    uint32_t colorAbgr)
{
    return view.ensureHudTextureColor(texture, colorAbgr);
}

void HudUiService::renderLayoutLabel(
    const GameplayOverlayContext &view,
    const UiLayoutManager::LayoutElement &layout,
    const GameplayResolvedHudLayoutElement &resolved,
    const std::string &label)
{
    view.renderLayoutLabel(layout, resolved, label);
}

std::optional<GameplayHudTextureHandle> HudUiService::ensureHudTextureLoaded(
    GameplayOverlayContext &view,
    const std::string &textureName)
{
    return view.ensureHudTextureLoaded(textureName);
}

std::optional<GameplayHudTextureHandle> HudUiService::ensureSolidHudTextureLoaded(
    GameplayOverlayContext &view,
    const std::string &textureName,
    uint32_t abgrColor)
{
    return view.ensureSolidHudTextureLoaded(textureName, abgrColor);
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

    const std::optional<GameplayHudTextureHandle> texture = view.ensureHudTextureLoaded(textureName);

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
