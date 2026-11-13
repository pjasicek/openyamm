#include "game/ui/GameplayBuffHud.h"

#include "game/party/WorldSpells.h"
#include "engine/Localization.h"
#include "game/ui/GameplayUiSkin.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/SkillData.h"
#include "game/rules/GameRules.h"
#include "game/tables/SpellTable.h"
#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
const std::array<const char *, CharacterBuffCount> GameplayPersonalBuffNames = {{
    Engine::trNoop("Bless").data(), Engine::trNoop("Fate").data(), Engine::trNoop("Preservation").data(),
    Engine::trNoop("Regeneration").data(), Engine::trNoop("Hammerhands").data(),
    Engine::trNoop("Pain Reflection").data(), Engine::trNoop("Fire Aura").data(),
    Engine::trNoop("Vampiric Weapon").data(), Engine::trNoop("Mistform").data(), Engine::trNoop("Glamour").data(),
    Engine::trNoop("Haste").data(), Engine::trNoop("Heroism").data(), Engine::trNoop("Shield").data(),
    Engine::trNoop("Stoneskin").data(), Engine::trNoop("Water Breathing").data(), Engine::trNoop("Temp Might").data(),
    Engine::trNoop("Temp Intellect").data(), Engine::trNoop("Temp Personality").data(),
    Engine::trNoop("Temp Endurance").data(), Engine::trNoop("Temp Speed").data(),
    Engine::trNoop("Temp Accuracy").data(), Engine::trNoop("Temp Luck").data(),
    Engine::trNoop("Fire Resistance").data(), Engine::trNoop("Air Resistance").data(),
    Engine::trNoop("Water Resistance").data(), Engine::trNoop("Earth Resistance").data(),
    Engine::trNoop("Mind Resistance").data(), Engine::trNoop("Body Resistance").data()
}};

std::vector<GameplayAuraLine> gameplayUnslottedAuraLines(
    const Party &party,
    const Character &member,
    const SpellTable *pSpellTable)
{
    const SpellRules &rules = gameRulesFor(&party).spells;
    std::vector<GameplayAuraLine> lines;

    for (const uint32_t spellId : rules.heldAurasWithoutBuffSlot(party))
    {
        const SpellEntry *pSpell = pSpellTable != nullptr ? pSpellTable->findById(int(spellId)) : nullptr;
        lines.push_back({pSpell != nullptr ? Engine::localize(partySpellName(&party, member, *pSpell), "spell")
                                    : Engine::tr("Aura"),
            rules.heldBuffText(party, spellId).value_or(Engine::tr("Held"))});
    }

    return lines;
}

std::vector<GameplayPotionEffectLine> gameplayPotionEffectLines(const Character &member, const SpellTable *pSpellTable)
{
    static constexpr std::array<std::string_view, size_t(CharacterCondition::Count)> ConditionNames = {
        Engine::trNoop("Curse"), Engine::trNoop("Weakness"), Engine::trNoop("Sleep"), Engine::trNoop("Fear"),
        Engine::trNoop("Drunkenness"), Engine::trNoop("Insanity"), Engine::trNoop("Poison"),
        Engine::trNoop("Disease"), Engine::trNoop("Poison"), Engine::trNoop("Disease"), Engine::trNoop("Poison"),
        Engine::trNoop("Disease"), Engine::trNoop("Paralysis"), Engine::trNoop("Unconsciousness"),
        Engine::trNoop("Death"), Engine::trNoop("Stone"), Engine::trNoop("Eradication"), Engine::trNoop("Zombie"),
    };
    std::vector<GameplayPotionEffectLine> lines;
    std::vector<std::string_view> immuneNames;
    std::string immunities;
    float immunitySeconds = 0;

    for (const TimedPotionEffect &effect : member.rulesetState.potionEffects)
    {
        if (effect.remainingSeconds <= 0)
        {
            continue;
        }

        switch (effect.kind)
        {
            case TimedPotionEffect::Kind::Immunity:
                // Poison and disease stages read as one immunity each.
                if (effect.key < ConditionNames.size()
                    && std::find(immuneNames.begin(), immuneNames.end(), ConditionNames[effect.key])
                        == immuneNames.end())
                {
                    immuneNames.push_back(ConditionNames[effect.key]);
                    immunities += (immunities.empty() ? "" : Engine::tr(", "))
                        + Engine::localize(ConditionNames[effect.key], "condition");
                }

                immunitySeconds = std::max(immunitySeconds, effect.remainingSeconds);
                break;
            case TimedPotionEffect::Kind::Aura:
            {
                const SpellEntry *pSpell = pSpellTable != nullptr ? pSpellTable->findById(int(effect.key)) : nullptr;
                const std::string effectName =
                    pSpell != nullptr ? Engine::localize(pSpell->name, "spell") : Engine::tr("Aura");
                lines.push_back({Engine::tr("{effect} (potion)", {{"effect", effectName}}),
                    effect.remainingSeconds});
                break;
            }
            case TimedPotionEffect::Kind::SkillBonus:
            {
                const std::optional<std::string> skill = skillNameForSkillId(effect.key);
                const std::string skillName =
                    skill ? Engine::localize(displaySkillName(*skill), "skill") : Engine::tr("Skill");
                lines.push_back({Engine::tr("{skill} +{amount} (potion)",
                                     {{"skill", skillName}, {"amount", int64_t(effect.amount)}}),
                    effect.remainingSeconds});
                break;
            }
            case TimedPotionEffect::Kind::Regeneration:
                lines.push_back({Engine::tr("Regeneration (potion)"), effect.remainingSeconds});
                break;
        }
    }

    if (!immunities.empty())
    {
        lines.push_back({Engine::tr("Immune to {conditions}", {{"conditions", immunities}}), immunitySeconds});
    }

    return lines;
}

namespace
{
void renderBuffLayer(GameplayScreenRuntime &context, const GameplayBuffHudLayer &layer,
    const GameplayResolvedHudLayoutElement &panel)
{
    const std::optional<GameplayHudTextureHandle> texture =
        context.gameplayUiRuntime().ensureHudTextureLoaded(layer.pAsset);
    if (!texture)
    {
        return;
    }
    const float scaleX = panel.width / 128;
    const float scaleY = panel.height / 128;
    context.gameplayUiRuntime().submitHudTexturedQuad(texture->textureHandle,
        panel.x + layer.placement.x * scaleX, panel.y + layer.placement.y * scaleY,
        layer.placement.width * scaleX, layer.placement.height * scaleY,
        layer.uv.x, layer.uv.y, layer.uv.x + layer.uv.width, layer.uv.y + layer.uv.height);
}

void renderBuffPanel(GameplayScreenRuntime &context, const Party &party, GameplayBuffPresentation presentation,
    int width, int height)
{
    const char *pId = gameplayBuffPanelLayoutId(presentation);
    if (pId == nullptr)
    {
        return;
    }
    const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(pId);
    const std::optional<GameplayResolvedHudLayoutElement> rect =
        context.resolveHudLayoutElement(pId, width, height, 0, 0);
    if (pLayout == nullptr || !rect)
    {
        return;
    }
    GameplayUiSkin::renderSurface(context, *rect);
    const GameplayBuffHudLayer *pBase = nullptr;
    // Light and clouds sit behind the skull; Stoneskin replaces the base without covering those effects.
    for (size_t i = 0; i < PartyBuffCount; ++i)
    {
        const GameplayBuffHudDefinition &definition = GameplayBuffHudDefinitions[i];
        // Wizard Eye's layer blinks in its last minutes (gameplayBuffIndicatorLit, OY-508).
        if (definition.presentation != presentation || !party.hasPartyBuff(static_cast<PartyBuffId>(i))
            || !gameplayBuffIndicatorLit(party, static_cast<PartyBuffId>(i)))
        {
            continue;
        }
        if (definition.pLayer != nullptr)
        {
            if (definition.pLayer->pass == GameplayBuffHudLayerPass::Underlay)
            {
                renderBuffLayer(context, *definition.pLayer, *rect);
            }
            else if (definition.pLayer->pass == GameplayBuffHudLayerPass::Base)
            {
                pBase = definition.pLayer;
            }
        }
    }
    if (pBase != nullptr)
    {
        renderBuffLayer(context, *pBase, *rect);
    }
    else
    {
        GameplayUiSkin::renderTexture(context, pLayout->primaryAsset, *rect);
    }
    for (size_t i = 0; i < PartyBuffCount; ++i)
    {
        const GameplayBuffHudDefinition &definition = GameplayBuffHudDefinitions[i];
        if (definition.presentation == presentation && definition.pLayer != nullptr
            && definition.pLayer->pass == GameplayBuffHudLayerPass::Overlay
            && party.hasPartyBuff(static_cast<PartyBuffId>(i))
            && gameplayBuffIndicatorLit(party, static_cast<PartyBuffId>(i)))
        {
            renderBuffLayer(context, *definition.pLayer, *rect);
        }
    }
    // Corner badges remain readable over the larger registered effect layers.
    for (size_t i = 0; i < PartyBuffCount; ++i)
    {
        const GameplayBuffHudDefinition &definition = GameplayBuffHudDefinitions[i];
        if (definition.presentation == presentation && definition.pLayer == nullptr && definition.cornerBadge
            && party.hasPartyBuff(static_cast<PartyBuffId>(i)))
        {
            const GameplayResolvedHudLayoutElement badge = {rect->x + definition.badgeX * rect->scale,
                rect->y + definition.badgeY * rect->scale, 12 * rect->scale, 12 * rect->scale, rect->scale};
            GameplayUiSkin::renderTexture(context, "obsidian_hud_buff_normal", badge);
            GameplayUiSkin::renderTexture(context, definition.pIcon, badge);
        }
    }
    const std::optional<GameplayHudPaletteColor> edge = context.gameplayUiRuntime().ensureHudPaletteColor(0xc46a7e88u);
    if (edge)
    {
        const float stroke = std::max(1.0f, rect->scale * 0.65f);
        const std::vector<GameplayHudBatchQuad> edges = {
            gameplayHudPaletteQuad(*edge, rect->x, rect->y, rect->width, stroke),
            gameplayHudPaletteQuad(*edge, rect->x, rect->y + rect->height - stroke, rect->width, stroke),
            gameplayHudPaletteQuad(*edge, rect->x, rect->y, stroke, rect->height),
            gameplayHudPaletteQuad(*edge, rect->x + rect->width - stroke, rect->y, stroke, rect->height)};
        context.submitHudQuadBatch(edges);
    }
}
}

std::vector<GameplayBuffHudEntry> gameplayBuffHudEntries(GameplayScreenRuntime &context, int width, int height)
{
    std::vector<GameplayBuffHudEntry> result;
    const Party *pParty = context.partyReadOnly();
    if (pParty == nullptr)
    {
        return result;
    }
    const std::vector<PartyBuffId> ids = sortedGameplaySpecialBuffs(*pParty);
    const std::optional<GameplayResolvedHudLayoutElement> first =
        context.resolveHudLayoutElement("ObsidianPartyBuff1", width, height, 0, 0);
    if (!first)
    {
        return result;
    }
    for (size_t i = 0; i < std::min(ids.size(), size_t{4}); ++i)
    {
        GameplayResolvedHudLayoutElement rect = *first;
        rect.x += i * 29.333333f * rect.scale;
        result.push_back({ids[i], rect});
    }
    if (context.interactionState().partyBuffPopupOpen && ids.size() > 4)
    {
        for (size_t i = 4; i < ids.size(); ++i)
        {
            GameplayResolvedHudLayoutElement rect = *first;
            rect.x += (8.0f + (i - 4) % 6 * 29.333333f) * rect.scale;
            rect.y += (45.0f + (i - 4) / 6 * 35.0f) * rect.scale;
            result.push_back({ids[i], rect});
        }
    }
    return result;
}

void renderGameplayBuffHud(GameplayScreenRuntime &context, int width, int height)
{
    const Party *pParty = context.partyReadOnly();
    if (pParty == nullptr)
    {
        return;
    }
    renderBuffPanel(context, *pParty, GameplayBuffPresentation::Hero, width, height);
    renderBuffPanel(context, *pParty, GameplayBuffPresentation::Skull, width, height);
    const std::vector<PartyBuffId> ids = sortedGameplaySpecialBuffs(*pParty);
    const std::vector<GameplayBuffHudEntry> entries = gameplayBuffHudEntries(context, width, height);
    if (entries.empty())
    {
        context.interactionState().partyBuffPopupOpen = false;
        return;
    }
    if (entries.size() > 4)
    {
        const GameplayResolvedHudLayoutElement &first = entries.front().rect;
        GameplayUiSkin::renderPanel(context, {first.x - 3 * first.scale, first.y + 34 * first.scale,
            194 * first.scale, (25 + std::ceil((ids.size() - 4) / 6.0f) * 35) * first.scale, first.scale});
    }
    for (const GameplayBuffHudEntry &entry : entries)
    {
        const GameplayResolvedHudLayoutElement &rect = entry.rect;
        const PartyBuffState *pBuff = pParty->partyBuff(entry.id);
        GameplayUiSkin::renderTexture(context, "obsidian_hud_buff_normal", rect);
        GameplayUiSkin::renderTexture(context, GameplayBuffHudDefinitions[size_t(entry.id)].pIcon,
            {rect.x + 3.2f * rect.scale, rect.y + 1.6f * rect.scale, 19.2f * rect.scale,
                19.2f * rect.scale, rect.scale});
        const int seconds = static_cast<int>(std::ceil(pBuff->remainingSeconds));
        const std::string duration = seconds >= 3600 ? std::to_string((seconds + 3599) / 3600) + "h"
            : seconds >= 60 ? std::to_string((seconds + 59) / 60) + "m" : std::to_string(seconds) + "s";
        UiLayoutManager::LayoutElement timer;
        timer.fontName = "SMALLNUM";
        timer.textColorAbgr = seconds < 30 ? GameplayUiSkin::Low : GameplayUiSkin::Ivory;
        timer.textScale = 0.34285714f;
        timer.textAlignX = UiLayoutManager::TextAlignX::Center;
        timer.textAlignY = UiLayoutManager::TextAlignY::Middle;
        context.renderLayoutLabel(timer, {rect.x, rect.y + 22.4f * rect.scale,
            rect.width, 6.4f * rect.scale, rect.scale}, duration);
    }
    if (ids.size() > 4)
    {
        const std::optional<GameplayResolvedHudLayoutElement> rect =
            context.resolveHudLayoutElement("ObsidianPartyBuffOverflow", width, height, 0, 0);
        const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement("ObsidianPartyBuffOverflow");
        if (rect && pLayout != nullptr)
        {
            GameplayUiSkin::renderTexture(context, pLayout->primaryAsset, *rect);
            context.renderLayoutLabel(*pLayout, *rect, "+" + std::to_string(ids.size() - 4));
        }
    }
}

std::optional<GameplayBuffHudEntry> gameplayMovementBuffAtPoint(GameplayScreenRuntime &context,
    int width, int height, float x, float y)
{
    const Party *pParty = context.partyReadOnly();
    if (pParty == nullptr)
    {
        return std::nullopt;
    }
    for (const GameplayMovementIndicator &indicator : gameplayMovementIndicators(*pParty))
    {
        const std::optional<GameplayResolvedHudLayoutElement> rect =
            context.resolveHudLayoutElement(indicator.pLayoutId, width, height, 0, 0);
        if (rect && GameplayHudCommon::isPointerInsideResolvedElement(*rect, x, y))
        {
            return GameplayBuffHudEntry{indicator.buff, *rect};
        }
    }
    return std::nullopt;
}

GameplayHudPointerTarget gameplayBuffHudTarget(GameplayScreenRuntime &context,
    int width, int height, float x, float y)
{
    const Party *pParty = context.partyReadOnly();
    if (pParty == nullptr)
    {
        return {};
    }
    const bool gameplay = context.currentHudScreenState() == GameplayHudScreenState::Gameplay;
    for (size_t i = 0; i < pParty->members().size(); ++i)
    {
        const std::string id = std::string(gameplay ? "ObsidianPc" : "ObsidianOverlayPc")
            + std::to_string(i + 1) + "PersonalBuffs";
        const std::optional<GameplayResolvedHudLayoutElement> rect =
            context.resolveHudLayoutElement(id, width, height, 0, 0);
        if (rect && GameplayHudCommon::isPointerInsideResolvedElement(*rect, x, y))
        {
            for (size_t b = 0; b < CharacterBuffCount; ++b)
            {
                if (pParty->hasCharacterBuff(i, static_cast<CharacterBuffId>(b)))
                {
                    return {GameplayHudPointerTargetType::PersonalBuffs, i};
                }
            }

            if (!gameplayPotionEffectLines(pParty->members()[i], nullptr).empty()
                || !gameplayUnslottedAuraLines(*pParty, pParty->members()[i], nullptr).empty())
            {
                return {GameplayHudPointerTargetType::PersonalBuffs, i};
            }
        }
    }
    if (gameplay)
    {
        const std::optional<GameplayBuffHudEntry> movement = gameplayMovementBuffAtPoint(context, width, height, x, y);
        if (movement)
        {
            return {GameplayHudPointerTargetType::PartyBuff, size_t(movement->id)};
        }
        for (GameplayBuffPresentation panel : {GameplayBuffPresentation::Hero, GameplayBuffPresentation::Skull})
        {
            const std::optional<GameplayResolvedHudLayoutElement> rect =
                context.resolveHudLayoutElement(gameplayBuffPanelLayoutId(panel), width, height, 0, 0);
            if (rect && GameplayHudCommon::isPointerInsideResolvedElement(*rect, x, y))
            {
                return {GameplayHudPointerTargetType::PartyBuffPanel, size_t(panel)};
            }
        }
        const std::vector<PartyBuffId> ids = sortedGameplaySpecialBuffs(*pParty);
        const std::optional<GameplayResolvedHudLayoutElement> rect =
            context.resolveHudLayoutElement("ObsidianPartyBuffOverflow", width, height, 0, 0);
        if (ids.size() > 4 && rect && GameplayHudCommon::isPointerInsideResolvedElement(*rect, x, y))
        {
            return {GameplayHudPointerTargetType::BuffOverflow};
        }
        for (const GameplayBuffHudEntry &entry : gameplayBuffHudEntries(context, width, height))
        {
            if (GameplayHudCommon::isPointerInsideResolvedElement(entry.rect, x, y))
            {
                return {GameplayHudPointerTargetType::PartyBuff, size_t(entry.id)};
            }
        }
    }
    return {};
}
}
