#include "game/ui/EnemyHealthBarRenderer.h"

#include "engine/Utf8Text.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/ui/GameplayUiSkin.h"

#include <array>

namespace OpenYAMM::Game
{
void EnemyHealthBarRenderer::preload(const GameplayScreenRuntime &context)
{
    GameplayUiRuntime &ui = context.gameplayUiRuntime();
    ui.ensureHudTextureLoaded("obsidian_enemy_health_frame");
}

void EnemyHealthBarRenderer::render(const GameplayScreenRuntime &context, const std::vector<Draw> &draws,
    uint16_t viewId, const bx::Vec3 &cameraPosition, const float *pViewMatrix, const float *pProjectionMatrix,
    int height)
{
    for (const Draw &draw : draws)
    {
        render(context, draw, viewId, cameraPosition, pViewMatrix, pProjectionMatrix, height);
    }
}

void EnemyHealthBarRenderer::render(const GameplayScreenRuntime &context, const Draw &draw, uint16_t viewId,
    const bx::Vec3 &cameraPosition, const float *pViewMatrix, const float *pProjectionMatrix, int height)
{
    const size_t actorIndex = draw.actorIndex;
    const bx::Vec3 &anchor = draw.anchor;
    const bool focused = draw.focused;
    GameplayActorInspectState actor;
    if (context.worldRuntime() == nullptr || height <= 0
        || !context.worldRuntime()->actorInspectState(actorIndex, 0, actor)
        || actor.isDead || actor.currentHp <= 0 || actor.maxHp <= 0)
    {
        return;
    }
    const bx::Vec3 forward = {-pViewMatrix[2], -pViewMatrix[6], -pViewMatrix[10]};
    const bx::Vec3 cameraToAnchor = bx::sub(anchor, cameraPosition);
    const float depth = bx::dot(cameraToAnchor, forward);
    const float actorDepth = bx::dot(bx::sub(draw.actorPosition, cameraPosition), forward);
    const float depthScale = combatActorHealthBarDepthScale(depth, actorDepth);
    if (depthScale <= 0.0f)
    {
        return;
    }
    // Scale the entire plane about the camera so its projected position and size do not change.
    const bx::Vec3 renderAnchor = bx::add(cameraPosition, bx::mul(cameraToAnchor, depthScale));
    const float worldPerPixel = 2.0f * depth * depthScale / (height * pProjectionMatrix[5]);
    const bx::Vec3 right = bx::mul(bx::Vec3{pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]}, worldPerPixel);
    const bx::Vec3 up = bx::mul(bx::Vec3{pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]}, worldPerPixel);
    const float hudScale = height / 480.0f;
    const float distanceScale = combatActorHealthBarScale(draw.distanceSquared);
    const float scale = hudScale * distanceScale;
    // Uniform meter width: HP and focus affect the fill and rim, never the bar's dimensions.
    const float width = 108.0f * scale;
    const float barHeight = 12.0f * scale;
    const float cap = 9.0f * scale;
    const float left = -width * 0.5f;
    GameplayUiRuntime &ui = context.gameplayUiRuntime();
    const std::optional<GameplayHudTextureHandle> frame = ui.ensureHudTextureLoaded("obsidian_enemy_health_frame");
    if (!frame)
    {
        return;
    }
    CombatActorHealthBarRuntime &history = context.enemyHealthBars();
    history.observe(actorIndex, actor.currentHp, actor.maxHp, draw.attackingParty);
    const float ratio = std::clamp(float(actor.currentHp) / float(actor.maxHp), 0.0f, 1.0f);
    std::array<GameplayHudBatchQuad, 128> quads;
    size_t quadCount = 0;
    TextureFilterProfile filterProfile = TextureFilterProfile::UiIllustration;
    const auto flush = [&]()
    {
        ui.submitWorldHudQuadBatch(std::span<const GameplayHudBatchQuad>(quads.data(), quadCount),
            viewId, renderAnchor, right, up, filterProfile);
        quadCount = 0;
    };
    const auto quad = [&](bgfx::TextureHandle texture, float x, float y, float w, float h,
                          float u0 = 0, float v0 = 0, float u1 = 1, float v1 = 1, uint32_t tintAbgr = 0xffffffffu)
    {
        if (bgfx::isValid(texture) && w > 0 && h > 0)
        {
            if (quadCount == quads.size())
            {
                flush();
            }
            GameplayHudBatchQuad q;
            q.textureHandle = texture;
            q.x = x;
            q.y = y;
            q.width = w;
            q.height = h;
            q.u0 = u0;
            q.v0 = v0;
            q.u1 = u1;
            q.v1 = v1;
            q.tintAbgr = tintAbgr;
            quads[quadCount++] = q;
        }
    };
    // Three slices preserve the tiny end ornaments while the trough changes width.
    const float sourceCap = 0.065f;
    const bgfx::TextureHandle frameTexture = frame->textureHandle;
    quad(frameTexture, left, -barHeight * 0.5f, cap, barHeight, 0, 0, sourceCap, 1);
    quad(frameTexture, left + cap, -barHeight * 0.5f, width - cap * 2, barHeight, sourceCap, 0, 1 - sourceCap, 1);
    quad(frameTexture, width * 0.5f - cap, -barHeight * 0.5f, cap, barHeight, 1 - sourceCap, 0, 1, 1);
    // The recessed channel begins inside each sliced end cap, before the slice boundary.
    const float channelInset = cap * 0.8f;
    const float innerX = left + channelInset;
    const float innerWidth = width - 2 * channelInset;
    const float innerHeight = barHeight * 0.52f;
    if (context.settingsSnapshot().enemyHealthBarDamageTrail)
    {
        const float trail = history.damageRatio(actorIndex, ratio);
        const std::optional<GameplayHudTextureHandle> gold =
            ui.ensureSolidHudTextureLoaded("__enemy_health_damage__", 0xff558faau);
        if (gold && trail > ratio)
        {
            quad(gold->textureHandle, innerX + innerWidth * ratio, -innerHeight * 0.5f,
                innerWidth * (trail - ratio), innerHeight);
        }
    }
    const std::optional<GameplayHudTextureHandle> fill = GameplayUiSkin::healthMeterTexture(context, ratio);
    if (fill)
    {
        quad(fill->textureHandle, innerX, -innerHeight * 0.5f, innerWidth * ratio, innerHeight);
    }
    if (focused)
    {
        const std::optional<GameplayHudTextureHandle> rim =
            ui.ensureSolidHudTextureLoaded("__enemy_health_focus__", GameplayUiSkin::Gold);
        if (rim)
        {
            quad(rim->textureHandle, left + cap, -barHeight * 0.36f, width - 2 * cap, 0.4f * scale);
            quad(rim->textureHandle, left + cap, barHeight * 0.32f, width - 2 * cap, 0.4f * scale);
        }
        const std::optional<GameplayHudTextureHandle> diamond =
            ui.ensureHudTextureLoaded("obsidian_hud_selection_diamond");
        if (diamond)
        {
            quad(diamond->textureHandle, -3.5f * scale, -barHeight * 0.5f - 3.5f * scale, 7 * scale, 7 * scale);
        }
    }
    // The rules' badges (MAW: a boss's skull left of the bar, its affix right of it).
    const std::vector<std::string> badges = context.partyReadOnly() != nullptr
        ? context.partyReadOnly()->rules().monsters.actorBadges(actor.rulesetFacts)
        : std::vector<std::string>{};
    const float badgeSize = 15.0f * scale;
    const float badgeGap = 1.0f * scale;

    for (size_t badge = 0; badge < badges.size(); ++badge)
    {
        const std::optional<GameplayHudTextureHandle> icon = ui.ensureHudTextureLoaded(badges[badge]);

        if (icon)
        {
            const float x = badge == 0 ? left - badgeGap - badgeSize
                                       : width * 0.5f + badgeGap + float(badge - 1) * (badgeSize + badgeGap);
            quad(icon->textureHandle, x, -badgeSize * 0.5f, badgeSize, badgeSize);
        }
    }

    const std::string &valuesMode = context.settingsSnapshot().enemyHealthBarValues;
    const bool showValues = valuesMode == "all" || (valuesMode == "target" && focused);
    if (focused || showValues)
    {
        const std::optional<GameplayHudFontHandle> font = ui.findHudFont(GameplayUiSkin::CombatFontName);
        if (font)
        {
            std::string label = focused ? actor.displayName : std::string();
            const std::string values = showValues
                ? std::to_string(actor.currentHp) + "/" + std::to_string(actor.maxHp) : std::string();
            const float textScale = hudScale * std::max(distanceScale, 0.6f);
            const float fontScale = 0.42f * textScale;
            // Longer names get a little caption room without widening the meter itself.
            const float textWidth = std::max(width, 144.0f * textScale);
            const float available = textWidth / fontScale - ui.measureHudTextWidth(*font, values) - 8;
            if (ui.measureHudTextWidth(*font, label) > available)
            {
                while (label.size() > 1 && ui.measureHudTextWidth(*font, label + "...") > available)
                {
                    Engine::Utf8::popBack(label);
                }
                label += "...";
            }
            if (!values.empty())
            {
                label += (label.empty() ? "" : " ") + values;
            }
            const GameplayHudFontData *pFont = GameplayHudCommon::findHudFont(ui.hudFontHandles(), font->fontName);
            if (pFont != nullptr)
            {
                flush();
                filterProfile = pFont->smooth ? TextureFilterProfile::SmoothText : TextureFilterProfile::Text;
                const float textX = -ui.measureHudTextWidth(*font, label) * fontScale * 0.5f;
                const float textY = -barHeight * 0.5f - pFont->fontHeight * fontScale - 1.5f * textScale;
                const auto addGlyph = [&](bgfx::TextureHandle texture, float x, float y, float w, float h,
                                          float u0, float v0, float u1, float v1, TextureFilterProfile,
                                          uint32_t tintAbgr)
                {
                    quad(texture, x, y, w, h, u0, v0, u1, v1, tintAbgr);
                };
                // A thin dark outline keeps the compact gold caption readable against sky and scenery.
                const bgfx::TextureHandle outline = font->shadowTextureHandle;
                const float outlineOffset = 0.5f * textScale;
                for (const bx::Vec3 offset : std::array<bx::Vec3, 4>{{
                    {-outlineOffset, 0, 0}, {outlineOffset, 0, 0},
                    {0, -outlineOffset, 0}, {0, outlineOffset, 0}}})
                {
                    GameplayHudCommon::renderHudFontLayer(*pFont, outline, label,
                        textX + offset.x, textY + offset.y, fontScale, addGlyph);
                }
                GameplayHudCommon::renderHudFontLayer(*pFont,
                    GameplayHudCommon::hudFontMainLayer(*pFont, GameplayUiSkin::Gold), label, textX, textY,
                    fontScale, addGlyph);
            }
        }
    }
    flush();
}
}
