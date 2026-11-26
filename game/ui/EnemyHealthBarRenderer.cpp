#include "game/ui/EnemyHealthBarRenderer.h"

#include "engine/Utf8Text.h"
#include "game/gameplay/ActorNameText.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/SkillRules.h"
#include "game/tables/MonsterTable.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// Whether the party's Identify Monster shows this monster's hit points (the rules' reveal at its level).
bool hitPointsRevealed(const GameplayScreenRuntime &context, size_t actorIndex, int16_t monsterId)
{
    const Party *pParty = context.partyReadOnly();
    const MonsterTable *pMonsterTable = context.monsterTable();
    const MonsterTable::MonsterStatsEntry *pStats =
        pMonsterTable != nullptr ? pMonsterTable->findStatsById(monsterId) : nullptr;

    if (pParty == nullptr || pStats == nullptr || context.worldRuntime() == nullptr)
    {
        return false;
    }

    GameplayRuntimeActorState runtimeState = {};
    const int monsterLevel = context.worldRuntime()->actorRuntimeState(actorIndex, runtimeState)
            && runtimeState.rulesetFacts.level > 0
        ? runtimeState.rulesetFacts.level
        : pStats->level;
    return gameRulesFor(pParty).skills.identifyMonsterReveal(*pParty, monsterLevel).hitPointsAndArmorClass;
}

// An effect on the actor as its icon under the bar: crowd control first, then the monster's own buffs.
struct ActorEffectIcon
{
    const char *pTexture = nullptr;
    float remainingSeconds = 0.0f;
    bool debuff = true;
};

constexpr size_t ActorEffectIconCount = 17;
static_assert(ActorEffectIconCount <= CombatActorHealthBarRuntime::EffectSlotCount);

std::array<ActorEffectIcon, ActorEffectIconCount> actorEffectIcons(const GameplayActorInspectState &actor)
{
    const char *pControl = nullptr;
    switch (actor.controlMode)
    {
        case GameplayActorControlMode::Charm: pControl = "obsidian_debuff_charm"; break;
        case GameplayActorControlMode::Berserk: pControl = "obsidian_debuff_berserk"; break;
        case GameplayActorControlMode::Enslaved: pControl = "obsidian_debuff_enslave"; break;
        case GameplayActorControlMode::ControlUndead: pControl = "obsidian_debuff_control_undead"; break;
        // A reanimated ally fights for the party for good: nothing to time.
        case GameplayActorControlMode::Reanimated:
        case GameplayActorControlMode::None: break;
    }
    return {{
        {"obsidian_debuff_stun", actor.stunRemainingSeconds},
        {"obsidian_debuff_paralyze", actor.paralyzeRemainingSeconds},
        {pControl, pControl != nullptr ? actor.controlRemainingSeconds : 0.0f},
        {"obsidian_debuff_fear", actor.fearRemainingSeconds},
        {"obsidian_debuff_slow", actor.slowRemainingSeconds},
        {"obsidian_debuff_shrink", actor.shrinkRemainingSeconds},
        {"obsidian_debuff_dark_grasp", actor.darkGraspRemainingSeconds},
        {"obsidian_buff_sbf05a", actor.hasteRemainingSeconds, false},
        {"obsidian_buff_sba06a", actor.shieldRemainingSeconds, false},
        {"obsidian_buff_sbe05a", actor.stoneskinRemainingSeconds, false},
        {"obsidian_buff_sbs02a", actor.blessRemainingSeconds, false},
        {"obsidian_buff_sbs07a", actor.heroismRemainingSeconds, false},
        {"obsidian_buff_sbl09a", actor.hourOfPowerRemainingSeconds, false},
        {"obsidian_buff_sbl08a", actor.dayOfProtectionRemainingSeconds, false},
        {"obsidian_buff_sbdk07a", actor.painReflectionRemainingSeconds, false},
        {"obsidian_buff_sbb07a", actor.hammerhandsRemainingSeconds, false},
        {"obsidian_buff_sbs03a", actor.fateRemainingSeconds, false},
    }};
}

// The sweep over an effect icon: 64 frames, 8 x 8 cells of 32 px, frame n shading n/63 of the square clockwise from
// twelve o'clock (the time spent). Built once per session.
constexpr int SweepFrameSize = 32;
constexpr int SweepGrid = 8;
constexpr int SweepFrameCount = SweepGrid * SweepGrid;

std::optional<GameplayHudTextureHandle> effectSweepTexture(GameplayUiRuntime &ui)
{
    const std::string name = "__enemy_effect_sweep__";
    const std::string signature = "v2";
    if (const std::optional<GameplayHudTextureHandle> cached = ui.findCachedDynamicHudTexture(name, signature))
    {
        return cached;
    }
    const int side = SweepFrameSize * SweepGrid;
    std::vector<uint8_t> pixels(size_t(side) * side * 4, 0);
    constexpr int Samples = 4;
    constexpr float TwoPi = 6.28318530718f;
    for (int frame = 0; frame < SweepFrameCount; ++frame)
    {
        const float sweep = TwoPi * float(frame) / float(SweepFrameCount - 1);
        const int originX = (frame % SweepGrid) * SweepFrameSize;
        const int originY = (frame / SweepGrid) * SweepFrameSize;
        for (int y = 0; y < SweepFrameSize; ++y)
        {
            for (int x = 0; x < SweepFrameSize; ++x)
            {
                int covered = 0;
                for (int sample = 0; sample < Samples * Samples; ++sample)
                {
                    const float dx = x + (sample % Samples + 0.5f) / Samples - SweepFrameSize * 0.5f;
                    const float dy = y + (sample / Samples + 0.5f) / Samples - SweepFrameSize * 0.5f;
                    float angle = std::atan2(dx, -dy);
                    angle += angle < 0.0f ? TwoPi : 0.0f;
                    covered += angle < sweep ? 1 : 0;
                }
                uint8_t *pPixel = &pixels[(size_t(originY + y) * side + originX + x) * 4];
                pPixel[0] = 12;
                pPixel[1] = 8;
                pPixel[2] = 8;
                pPixel[3] = uint8_t(215 * covered / (Samples * Samples));
            }
        }
    }
    const std::optional<GameplayHudTextureHandle> texture = ui.ensureDynamicHudTexture(name, side, side, pixels);
    if (texture)
    {
        ui.setDynamicHudTextureContentSignature(name, signature);
    }
    return texture;
}
}

void EnemyHealthBarRenderer::preload(const GameplayScreenRuntime &context)
{
    GameplayUiRuntime &ui = context.gameplayUiRuntime();
    ui.ensureHudTextureLoaded("obsidian_enemy_health_frame");
    for (const ActorEffectIcon &icon : actorEffectIcons(GameplayActorInspectState{}))
    {
        if (icon.pTexture != nullptr)
        {
            ui.ensureHudTextureLoaded(icon.pTexture);
        }
    }
    for (const char *pControl : {"obsidian_debuff_charm", "obsidian_debuff_berserk", "obsidian_debuff_enslave",
             "obsidian_debuff_control_undead"})
    {
        ui.ensureHudTextureLoaded(pControl);
    }
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
    // The badges: the rules' (MAW: a boss's skull left of the bar, its affix right of it), else a boss's skull.
    const MonsterModifierSet *pModifiers =
        context.monsterTable() != nullptr ? context.monsterTable()->findModifiers(actor.monsterId) : nullptr;
    const std::vector<std::string> badges = context.partyReadOnly() != nullptr
        ? healthBarBadges(context.partyReadOnly()->rules().monsters, actor.rulesetFacts,
            pModifiers != nullptr && pModifiers->boss)
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

    // The effects under the bar, centred: each icon on a dark tile with a rim (red for crowd control, gold for the
    // monster's buffs) and the spent time swept clockwise over it. At most as many as the bar is wide.
    if (context.settingsSnapshot().enemyHealthBarEffects)
    {
        const std::array<ActorEffectIcon, ActorEffectIconCount> effects = actorEffectIcons(actor);
        std::array<float, ActorEffectIconCount> elapsed = {};
        size_t shown = 0;
        for (size_t slot = 0; slot < effects.size(); ++slot)
        {
            elapsed[slot] = history.effectElapsed(actorIndex, slot, effects[slot].remainingSeconds);
            shown += effects[slot].pTexture != nullptr && effects[slot].remainingSeconds > 0.0f ? 1 : 0;
        }
        const float iconSize = 16.0f * scale;
        const float iconGap = 1.5f * scale;
        const size_t maximum = size_t((width + iconGap) / (iconSize + iconGap));
        shown = std::min(shown, maximum);
        const std::optional<GameplayHudTextureHandle> tile =
            shown > 0 ? ui.ensureSolidHudTextureLoaded("__enemy_effect_tile__", 0xf0302a28u) : std::nullopt;
        const std::optional<GameplayHudTextureHandle> debuffRim =
            shown > 0 ? ui.ensureSolidHudTextureLoaded("__enemy_effect_debuff_rim__", 0xff2a2aa8u) : std::nullopt;
        const std::optional<GameplayHudTextureHandle> buffRim =
            shown > 0 ? ui.ensureSolidHudTextureLoaded("__enemy_effect_buff_rim__", GameplayUiSkin::Gold)
                      : std::nullopt;
        const std::optional<GameplayHudTextureHandle> sweep =
            shown > 0 ? effectSweepTexture(ui) : std::nullopt;
        float x = -(float(shown) * iconSize + float(shown - std::min<size_t>(shown, 1)) * iconGap) * 0.5f;
        const float y = barHeight * 0.5f + 1.5f * scale;
        const float rim = std::max(0.6f * scale, 0.75f);
        size_t drawn = 0;
        for (size_t slot = 0; slot < effects.size() && drawn < shown; ++slot)
        {
            const ActorEffectIcon &effect = effects[slot];
            const std::optional<GameplayHudTextureHandle> icon = effect.pTexture != nullptr
                    && effect.remainingSeconds > 0.0f
                ? ui.ensureHudTextureLoaded(effect.pTexture)
                : std::nullopt;
            if (!icon)
            {
                continue;
            }
            const std::optional<GameplayHudTextureHandle> &rimTexture = effect.debuff ? debuffRim : buffRim;
            if (rimTexture)
            {
                quad(rimTexture->textureHandle, x, y, iconSize, iconSize);
            }
            if (tile)
            {
                quad(tile->textureHandle, x + rim, y + rim, iconSize - 2 * rim, iconSize - 2 * rim);
            }
            quad(icon->textureHandle, x + rim, y + rim, iconSize - 2 * rim, iconSize - 2 * rim);
            if (sweep && elapsed[slot] > 0.0f)
            {
                // Half a texel inside each cell, so filtering never reaches the neighbouring frame.
                const int frame = std::clamp(int(std::lround(elapsed[slot] * (SweepFrameCount - 1))), 0,
                    SweepFrameCount - 1);
                const float cell = 1.0f / SweepGrid;
                const float inset = 0.5f / float(SweepFrameSize * SweepGrid);
                const float u0 = float(frame % SweepGrid) * cell;
                const float v0 = float(frame / SweepGrid) * cell;
                quad(sweep->textureHandle, x + rim, y + rim, iconSize - 2 * rim, iconSize - 2 * rim,
                    u0 + inset, v0 + inset, u0 + cell - inset, v0 + cell - inset);
            }
            x += iconSize + iconGap;
            ++drawn;
        }
    }

    const std::string &valuesMode = context.settingsSnapshot().enemyHealthBarValues;
    // The numbers only when Identify Monster reveals hit points, as the inspect panel does (OY-245); asked only for a
    // bar that would show them.
    const bool showValues = (valuesMode == "all" || (valuesMode == "target" && focused))
        && hitPointsRevealed(context, actorIndex, actor.monsterId);
    if (focused || showValues)
    {
        const std::optional<GameplayHudFontHandle> font = ui.findHudFont(GameplayUiSkin::CombatFontName);
        if (font)
        {
            std::string label = focused ? localizedActorName(actor.displayName) : std::string();
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
                const GameplayHudFontLayer outline = font->shadowLayer();
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
