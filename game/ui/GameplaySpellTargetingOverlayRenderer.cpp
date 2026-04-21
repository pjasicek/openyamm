#include "game/ui/GameplaySpellTargetingOverlayRenderer.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/party/SpellIds.h"
#include "game/ui/GameplayHudCommon.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float SpellImpactAoePreviewRadius = 448.0f;
constexpr float MeteorShowerPreviewRadius = 768.0f;

uint32_t packHudColorAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u | (uint32_t(blue) << 16) | (uint32_t(green) << 8) | uint32_t(red);
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u | (uint32_t(blue) << 16) | (uint32_t(green) << 8) | uint32_t(red);
}

uint32_t withAlpha(uint32_t abgr, uint8_t alpha)
{
    return (abgr & 0x00ffffffu) | (uint32_t(alpha) << 24);
}
} // namespace

void GameplaySpellTargetingOverlayRenderer::renderPendingSpellTargetingOverlay(
    GameplayScreenRuntime &context,
    const GameplaySpellService &spellService,
    const GameplayScreenState::PendingSpellTargetState &pendingSpellCast,
    int width,
    int height,
    float cursorX,
    float cursorY)
{
    if (!pendingSpellCast.active || width <= 0 || height <= 0)
    {
        return;
    }

    context.gameplayUiRuntime().prepareHudView(width, height);

    const GameplayUiViewportRect uiViewport = GameplayHudCommon::computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float overlayScale = std::clamp(baseScale, 0.75f, 2.0f);
    const float armLength = std::round(10.0f * overlayScale);
    const float armGap = std::round(4.0f * overlayScale);
    const float stroke = std::max(1.0f, std::round(2.0f * overlayScale));
    const uint32_t crosshairColor = packHudColorAbgr(255, 255, 155);
    const uint32_t shadowColor = 0xc0000000u;

    const std::optional<GameplayScreenRuntime::HudTextureHandle> crosshairTexture =
        context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__spell_target_crosshair__", crosshairColor);
    const std::optional<GameplayScreenRuntime::HudTextureHandle> shadowTexture =
        context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__spell_target_shadow__", shadowColor);

    if (!crosshairTexture || !shadowTexture)
    {
        return;
    }

    const auto submitCrosshairLine =
        [&context, &crosshairTexture, &shadowTexture](float x, float y, float quadWidth, float quadHeight)
        {
            context.submitHudTexturedQuad(*shadowTexture, x + 1.0f, y + 1.0f, quadWidth, quadHeight);
            context.submitHudTexturedQuad(*crosshairTexture, x, y, quadWidth, quadHeight);
        };

    submitCrosshairLine(cursorX - armGap - armLength, cursorY - stroke * 0.5f, armLength, stroke);
    submitCrosshairLine(cursorX + armGap, cursorY - stroke * 0.5f, armLength, stroke);
    submitCrosshairLine(cursorX - stroke * 0.5f, cursorY - armGap - armLength, stroke, armLength);
    submitCrosshairLine(cursorX - stroke * 0.5f, cursorY + armGap, stroke, armLength);

    const std::string prompt = spellService.pendingTargetSelectionPromptText(true);
    GameplayScreenRuntime::HudLayoutElement promptLayout = {};
    promptLayout.fontName = "arrus";
    promptLayout.textColorAbgr = crosshairColor;
    promptLayout.textAlignX = UiLayoutManager::TextAlignX::Center;
    promptLayout.textAlignY = UiLayoutManager::TextAlignY::Top;
    GameplayScreenRuntime::ResolvedHudLayoutElement promptRect = {};
    promptRect.x = uiViewport.x;
    promptRect.y = uiViewport.y + std::round(18.0f * overlayScale);
    promptRect.width = uiViewport.width;
    promptRect.height = std::round(24.0f * overlayScale);
    promptRect.scale = overlayScale;
    context.renderLayoutLabel(promptLayout, promptRect, prompt);
}

std::optional<GameplaySpellTargetingOverlayRenderer::AreaMarkerVisualPolicy>
GameplaySpellTargetingOverlayRenderer::resolveAreaMarkerVisualPolicy(
    const GameplayScreenState::PendingSpellTargetState &pendingSpellCast)
{
    if (!pendingSpellCast.active || pendingSpellCast.targetKind != PartySpellCastTargetKind::GroundPoint)
    {
        return std::nullopt;
    }

    const SpellId spellId = spellIdFromValue(pendingSpellCast.spellId);
    AreaMarkerVisualPolicy policy = {};
    policy.spellId = pendingSpellCast.spellId;

    if (spellId == SpellId::MeteorShower)
    {
        policy.radius = MeteorShowerPreviewRadius;
        policy.ringColorAbgr = withAlpha(makeAbgr(255, 176, 96), 220);
        policy.baseColorAbgr = makeAbgr(255, 132, 44);
        policy.accentColorAbgr = makeAbgr(255, 222, 148);
        policy.shaderSpeed = 5.2f;
        policy.shaderFrequency = 2.6f;
        policy.shaderPrimaryBandWidth = 0.11f;
        policy.shaderSecondaryBandWidth = 0.07f;
        return policy;
    }

    if (spellId == SpellId::Starburst)
    {
        policy.radius = SpellImpactAoePreviewRadius;
        policy.ringColorAbgr = withAlpha(makeAbgr(192, 224, 255), 220);
        policy.baseColorAbgr = makeAbgr(126, 186, 255);
        policy.accentColorAbgr = makeAbgr(232, 246, 255);
        policy.shaderSpeed = 4.3f;
        policy.shaderFrequency = 2.2f;
        policy.shaderPrimaryBandWidth = 0.09f;
        policy.shaderSecondaryBandWidth = 0.055f;
        return policy;
    }

    return std::nullopt;
}
} // namespace OpenYAMM::Game
