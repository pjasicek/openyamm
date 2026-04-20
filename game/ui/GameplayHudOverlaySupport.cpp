#include "game/ui/GameplayHudOverlaySupport.h"

#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayOverlayContext.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr uint16_t HudViewId = 2;

uint32_t packHudColorAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u | (uint32_t(blue) << 16) | (uint32_t(green) << 8) | uint32_t(red);
}
}

bool GameplayHudOverlaySupport::tryPopulateItemInspectOverlayFromRenderedHudItems(
    GameplayOverlayContext &context,
    int width,
    int height,
    bool requireOpaqueHitTest)
{
    GameplayUiController::ItemInspectOverlayState &overlay = context.itemInspectOverlay();
    overlay = {};

    if (width <= 0
        || height <= 0
        || context.itemTable() == nullptr
        || context.currentHudScreenState() != context.renderedInspectableHudScreenState())
    {
        return false;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
    {
        return false;
    }

    for (auto it = context.renderedInspectableHudItems().rbegin();
         it != context.renderedInspectableHudItems().rend();
         ++it)
    {
        if (mouseX < it->x
            || mouseX >= it->x + it->width
            || mouseY < it->y
            || mouseY >= it->y + it->height)
        {
            continue;
        }

        if (requireOpaqueHitTest && !context.isOpaqueHudPixelAtPoint(*it, mouseX, mouseY))
        {
            continue;
        }

        overlay.active = true;
        overlay.objectDescriptionId = it->objectDescriptionId;
        overlay.hasItemState = it->hasItemState;
        overlay.itemState = it->itemState;
        overlay.sourceType = it->sourceType;
        overlay.sourceMemberIndex = it->sourceMemberIndex;
        overlay.sourceGridX = it->sourceGridX;
        overlay.sourceGridY = it->sourceGridY;
        overlay.sourceEquipmentSlot = it->equipmentSlot;
        overlay.sourceLootItemIndex = it->sourceLootItemIndex;
        overlay.hasValueOverride = it->hasValueOverride;
        overlay.valueOverride = it->valueOverride;
        overlay.sourceX = it->x;
        overlay.sourceY = it->y;
        overlay.sourceWidth = it->width;
        overlay.sourceHeight = it->height;
        return true;
    }

    return false;
}

void GameplayHudOverlaySupport::renderGameplayMouseLookOverlay(
    GameplayOverlayContext &context,
    int width,
    int height,
    bool active)
{
    if (!active || width <= 0 || height <= 0)
    {
        return;
    }

    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth);
    bgfx::setViewRect(HudViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewTransform(HudViewId, nullptr, projectionMatrix);
    bgfx::touch(HudViewId);

    const GameplayUiViewportRect uiViewport = GameplayHudCommon::computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float overlayScale = std::clamp(baseScale, 0.75f, 2.0f);
    const float centerX = std::round(static_cast<float>(width) * 0.5f);
    const float centerY = std::round(static_cast<float>(height) * 0.5f);
    const float armLength = std::round(3.0f * overlayScale);
    const float armGap = std::round(1.0f * overlayScale);
    const float stroke = std::max(1.0f, std::round(1.0f * overlayScale));
    const uint32_t dotColor = packHudColorAbgr(255, 255, 180);
    const uint32_t shadowColor = 0xc0000000u;
    const std::optional<GameplayOverlayContext::HudTextureHandle> dotTexture =
        context.ensureSolidHudTextureLoaded("__gameplay_mouse_look_marker__", dotColor);
    const std::optional<GameplayOverlayContext::HudTextureHandle> shadowTexture =
        context.ensureSolidHudTextureLoaded("__gameplay_mouse_look_marker_shadow__", shadowColor);

    if (!dotTexture || !shadowTexture)
    {
        return;
    }

    const auto submitQuad =
        [&context](const GameplayOverlayContext::HudTextureHandle &texture, float x, float y, float quadWidth, float quadHeight)
        {
            context.submitHudTexturedQuad(texture, x, y, quadWidth, quadHeight);
        };

    submitQuad(*shadowTexture, centerX - stroke * 0.5f + 1.0f, centerY - armGap - armLength + 1.0f, stroke, armLength);
    submitQuad(*shadowTexture, centerX - stroke * 0.5f + 1.0f, centerY + armGap + 1.0f, stroke, armLength);
    submitQuad(*shadowTexture, centerX - armGap - armLength + 1.0f, centerY - stroke * 0.5f + 1.0f, armLength, stroke);
    submitQuad(*shadowTexture, centerX + armGap + 1.0f, centerY - stroke * 0.5f + 1.0f, armLength, stroke);

    submitQuad(*dotTexture, centerX - stroke * 0.5f, centerY - armGap - armLength, stroke, armLength);
    submitQuad(*dotTexture, centerX - stroke * 0.5f, centerY + armGap, stroke, armLength);
    submitQuad(*dotTexture, centerX - armGap - armLength, centerY - stroke * 0.5f, armLength, stroke);
    submitQuad(*dotTexture, centerX + armGap, centerY - stroke * 0.5f, armLength, stroke);
}
} // namespace OpenYAMM::Game
