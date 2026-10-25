#include "game/ui/GameplayHudGeometry.h"
#include "game/ui/GameplayUiSkin.h"
#include "game/ui/GameplayPortraitGems.h"
#include "game/ui/GameplayBuffHud.h"
#include "game/ui/GameplayClock.h"
#include "game/ui/GameplayMapProgressBar.h"
#include "game/ui/GameplayQuickItems.h"
#include "game/ui/GameplayUiRenderer.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/rules/ClassRules.h"
#include "game/rules/GameRules.h"
#include "game/StringUtils.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <initializer_list>
#include <limits>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float OeMeleeAlertDistance = 307.2f;
constexpr float OeYellowAlertDistance = 5120.0f;
constexpr int EventNpcPortraitNativeWidth = 63;
constexpr int EventNpcPortraitNativeHeight = 73;
constexpr float EventNpcPortraitUvCropX = 2.0f;
constexpr float EventNpcPortraitUvCropY = 2.0f;
constexpr uint32_t MistformPortraitModulationAbgr = 0x80ffffffu;

enum class PortraitAggroIndicator
{
    Hidden,
    Black,
    Green,
    Yellow,
    Red,
};


struct PointerRenderInput
{
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    bool isLeftMousePressed = false;
};

PointerRenderInput pointerRenderInput(const GameplayScreenRuntime &context)
{
    PointerRenderInput input = {};
    const GameplayInputFrame *pInputFrame = context.currentGameplayInputFrame();

    if (pInputFrame == nullptr)
    {
        return input;
    }

    input.mouseX = pInputFrame->pointerX;
    input.mouseY = pInputFrame->pointerY;
    input.isLeftMousePressed = pInputFrame->leftMouseButton.held;
    return input;
}

std::string npcPortraitTextureName(uint32_t pictureId)
{
    if (pictureId == 0)
    {
        return {};
    }

    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "npc%04u", pictureId);
    return buffer;
}

std::optional<size_t> followerPortraitSlotIndex(const std::string &normalizedLayoutId)
{
    constexpr std::string_view prefix = "outdoorfollowerportrait_";

    if (normalizedLayoutId.rfind(prefix, 0) != 0 || normalizedLayoutId.size() != prefix.size() + 1)
    {
        return std::nullopt;
    }

    const char slot = normalizedLayoutId[prefix.size()];
    if (slot < '1' || slot > '3')
    {
        return std::nullopt;
    }

    return static_cast<size_t>(slot - '1');
}

bool isOverlayHudState(GameplayHudScreenState hudScreenState)
{
    return hudScreenState == GameplayHudScreenState::Dialogue
        || hudScreenState == GameplayHudScreenState::Character
        || hudScreenState == GameplayHudScreenState::Chest
        || hudScreenState == GameplayHudScreenState::Spellbook
        || hudScreenState == GameplayHudScreenState::Rest
        || hudScreenState == GameplayHudScreenState::Menu
        || hudScreenState == GameplayHudScreenState::Controls
        || hudScreenState == GameplayHudScreenState::Keyboard
        || hudScreenState == GameplayHudScreenState::VideoOptions
        || hudScreenState == GameplayHudScreenState::SaveGame
        || hudScreenState == GameplayHudScreenState::LoadGame
        || hudScreenState == GameplayHudScreenState::Journal
        || hudScreenState == GameplayHudScreenState::QuickReference;
}

int outdoorMinimapArrowIndex(float yawRadians)
{
    float normalizedYaw = std::fmod(yawRadians, Pi * 2.0f);

    if (normalizedYaw < 0.0f)
    {
        normalizedYaw += Pi * 2.0f;
    }

    const int octant = static_cast<int>(std::floor((normalizedYaw + Pi * 0.125f) / (Pi * 0.25f))) % 8;
    return (octant + 7) % 8;
}

float nearestHostileActorDistanceToParty(const IGameplayWorldRuntime *pWorldRuntime)
{
    if (pWorldRuntime == nullptr)
    {
        return std::numeric_limits<float>::max();
    }

    const float partyX = pWorldRuntime->partyX();
    const float partyY = pWorldRuntime->partyY();
    const float partyFootZ = pWorldRuntime->partyFootZ();
    float nearestHostileDistance = std::numeric_limits<float>::max();

    for (size_t actorIndex = 0; actorIndex < pWorldRuntime->mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!pWorldRuntime->actorRuntimeState(actorIndex, actorState)
            || actorState.isDead
            || actorState.isInvisible
            || !actorState.hostileToParty)
        {
            continue;
        }

        const float deltaX = actorState.preciseX - partyX;
        const float deltaY = actorState.preciseY - partyY;
        const float deltaZ = actorState.preciseZ - partyFootZ;
        const float centerDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
        const float edgeDistance = std::max(0.0f, centerDistance - static_cast<float>(actorState.radius));
        nearestHostileDistance = std::min(nearestHostileDistance, edgeDistance);
    }

    return nearestHostileDistance;
}

PortraitAggroIndicator classifyPortraitAggroIndicator(
    const Character &member,
    float nearestHostileDistance,
    float partyEngagementRange)
{
    if (!GameMechanics::canAct(member))
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (member.recoverySecondsRemaining > 0.0f)
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (nearestHostileDistance >= partyEngagementRange)
    {
        return PortraitAggroIndicator::Green;
    }

    if (nearestHostileDistance < OeMeleeAlertDistance)
    {
        return PortraitAggroIndicator::Red;
    }

    if (nearestHostileDistance < OeYellowAlertDistance)
    {
        return PortraitAggroIndicator::Yellow;
    }

    return PortraitAggroIndicator::Green;
}

std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolveLayout(
    GameplayScreenRuntime &context,
    const std::string &layoutId,
    float fallbackWidth,
    float fallbackHeight,
    int screenWidth,
    int screenHeight)
{
    return context.resolveHudLayoutElement(layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight);
}

void submitQuad(
    std::vector<GameplayHudBatchQuad> &queuedHudQuads,
    const GameplayHudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight)
{
    if (!bgfx::isValid(texture.textureHandle) || quadWidth <= 0.0f || quadHeight <= 0.0f)
    {
        return;
    }

    GameplayHudBatchQuad quad = {};
    quad.textureHandle = texture.textureHandle;
    quad.x = x;
    quad.y = y;
    quad.width = quadWidth;
    quad.height = quadHeight;
    queuedHudQuads.push_back(quad);
}

void submitQuadUv(
    std::vector<GameplayHudBatchQuad> &queuedHudQuads,
    const GameplayHudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    float u0,
    float v0,
    float u1,
    float v1)
{
    if (!bgfx::isValid(texture.textureHandle) || quadWidth <= 0.0f || quadHeight <= 0.0f)
    {
        return;
    }

    GameplayHudBatchQuad quad = {};
    quad.textureHandle = texture.textureHandle;
    quad.x = x;
    quad.y = y;
    quad.width = quadWidth;
    quad.height = quadHeight;
    quad.u0 = u0;
    quad.v0 = v0;
    quad.u1 = u1;
    quad.v1 = v1;
    queuedHudQuads.push_back(quad);
}

void submitQuadClipped(
    std::vector<GameplayHudBatchQuad> &queuedHudQuads,
    const GameplayHudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    uint16_t scissorX,
    uint16_t scissorY,
    uint16_t scissorWidth,
    uint16_t scissorHeight)
{
    if (!bgfx::isValid(texture.textureHandle) || quadWidth <= 0.0f || quadHeight <= 0.0f)
    {
        return;
    }

    GameplayHudBatchQuad quad = {};
    quad.textureHandle = texture.textureHandle;
    quad.x = x;
    quad.y = y;
    quad.width = quadWidth;
    quad.height = quadHeight;
    quad.clipped = true;
    quad.scissorX = scissorX;
    quad.scissorY = scissorY;
    quad.scissorWidth = scissorWidth;
    quad.scissorHeight = scissorHeight;
    queuedHudQuads.push_back(quad);
}

// A solid square in a palette colour (see GameplayUiRuntime::ensureHudPaletteColor), clipped like submitQuadClipped.
void submitPaletteQuadClipped(
    std::vector<GameplayHudBatchQuad> &queuedHudQuads,
    const GameplayHudPaletteColor &color,
    float x,
    float y,
    float size,
    uint16_t scissorX,
    uint16_t scissorY,
    uint16_t scissorWidth,
    uint16_t scissorHeight)
{
    if (!bgfx::isValid(color.textureHandle) || size <= 0.0f)
    {
        return;
    }

    GameplayHudBatchQuad quad = gameplayHudPaletteQuad(color, x, y, size, size);
    quad.clipped = true;
    quad.scissorX = scissorX;
    quad.scissorY = scissorY;
    quad.scissorWidth = scissorWidth;
    quad.scissorHeight = scissorHeight;
    queuedHudQuads.push_back(quad);
}

void submitLineClipped(
    std::vector<GameplayHudBatchQuad> &queuedHudQuads,
    const GameplayHudPaletteColor &color,
    float x0,
    float y0,
    float x1,
    float y1,
    float thickness,
    uint16_t scissorX,
    uint16_t scissorY,
    uint16_t scissorWidth,
    uint16_t scissorHeight)
{
    if (!bgfx::isValid(color.textureHandle) || thickness <= 0.0f)
    {
        return;
    }

    GameplayHudBatchQuad quad = {};
    quad.textureHandle = color.textureHandle;
    quad.u0 = color.u;
    quad.u1 = color.u;
    quad.v0 = color.v;
    quad.v1 = color.v;
    quad.x = x0;
    quad.y = y0;
    quad.x2 = x1;
    quad.y2 = y1;
    quad.width = thickness;
    quad.height = thickness;
    quad.line = true;
    quad.clipped = true;
    quad.scissorX = scissorX;
    quad.scissorY = scissorY;
    quad.scissorWidth = scissorWidth;
    quad.scissorHeight = scissorHeight;
    queuedHudQuads.push_back(quad);
}

} // namespace

void GameplayUiRenderer::renderGameplayHudArt(GameplayScreenRuntime &context, int width, int height)
{
    Party *pParty = context.party();
    if (pParty == nullptr || !context.hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }
    context.prepareHudView(width, height);
    const GameplayHudScreenState hudScreenState = context.currentHudScreenState();
    const bool isLimitedOverlayHud = isOverlayHudState(hudScreenState)
        && !activeEventDialogPreservesGameplayHud(context.activeEventDialog());
    const GameplayHudLayoutMode gameplayHudLayout = isLimitedOverlayHud
        ? GameplayHudLayoutMode::Overlay : GameplayHudLayoutMode::Widescreen;
    const Party &party = *pParty;
    const std::vector<Character> &members = party.members();
    context.fxService().consumePendingEventFxRequests(context);
    const float uiScale = static_cast<float>(height) / 480.0f;
    const PointerRenderInput pointerInput = pointerRenderInput(context);
    const float characterMouseX = pointerInput.mouseX;
    const float characterMouseY = pointerInput.mouseY;
    const bool isLeftMousePressed = pointerInput.isLeftMousePressed;
    std::vector<HiredNpcFollowerView> followerViews;
    if (!isLimitedOverlayHud && context.interactionState().followerPanelOpen && context.worldRuntime() != nullptr
        && context.worldRuntime()->eventRuntimeState() != nullptr && context.npcDialogTable() != nullptr
        && context.mergedNpcProfessionTable() != nullptr)
    {
        followerViews = buildHiredNpcFollowerViews(*context.worldRuntime()->eventRuntimeState(), &party,
            *context.npcDialogTable(), *context.mergedNpcProfessionTable());
        const size_t maximumOffset = followerViews.size() > 3 ? followerViews.size() - 3 : 0;
        context.interactionState().followerPanelScrollOffset =
            std::min(context.interactionState().followerPanelScrollOffset, maximumOffset);
    }
    thread_local std::vector<GameplayHudBatchQuad> queuedHudQuads;
    queuedHudQuads.clear();
    const auto flushQueuedHudQuads = [&context, width, height]()
    {
        context.submitHudQuadBatch(queuedHudQuads);
        queuedHudQuads.clear();
    };
    const auto draw = [&](const std::string &id, const std::string &asset = std::string{})
    {
        const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(id);
        const std::optional<GameplayResolvedHudLayoutElement> rect =
            context.resolveHudLayoutElement(id, width, height, 0.0f, 0.0f);
        if (pLayout == nullptr || !rect)
        {
            return;
        }
        const std::optional<GameplayHudTextureHandle> texture = context.gameplayUiRuntime().ensureHudTextureLoaded(
            asset.empty() ? pLayout->primaryAsset : asset);
        if (texture)
        {
            context.submitHudTexturedQuad(*texture, rect->x, rect->y, rect->width, rect->height);
        }
    };
    const auto label = [&](const std::string &id, const std::string &text)
    {
        const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(id);
        const std::optional<GameplayResolvedHudLayoutElement> rect =
            context.resolveHudLayoutElement(id, width, height, 0.0f, 0.0f);
        if (pLayout != nullptr && rect)
        {
            context.renderLayoutLabel(*pLayout, *rect, text);
        }
    };
    if (isLimitedOverlayHud)
    {
        draw("OutdoorBasebar");
    }
    else if (context.settingsSnapshot().partyFrame || hudScreenState != GameplayHudScreenState::Gameplay)
    {
        // The frame setting applies to plain gameplay only; dialogues and other screens over the HUD keep it.
        const std::optional<GameplayResolvedHudLayoutElement> basebar =
            context.resolveHudLayoutElement("OutdoorGameplayBasebar", width, height, 0, 0);
        if (basebar)
        {
            GameplayUiSkin::renderPartyBasebar(context, *basebar);
        }
    }
    size_t selected = party.activeMemberIndex();
    const GameplayUiController::CharacterScreenState &characterScreen = context.characterScreenReadOnly();
    if (characterScreen.open && characterScreen.source == GameplayUiController::CharacterScreenSource::Party)
    {
        selected = characterScreen.sourceIndex;
    }
    const bool hasReadyMember = std::any_of(members.begin(), members.end(), [](const Character &member)
    {
        return GameMechanics::canAct(member) && member.recoverySecondsRemaining <= 0;
    });
    const bool showSelection = isLimitedOverlayHud || hasReadyMember;
    const float nearestHostile = nearestHostileActorDistanceToParty(context.worldRuntime());
    const float engagementRange = context.worldRuntime() != nullptr ? context.worldRuntime()->partyEngagementRange()
        : 10240.0f;
    for (size_t i = 0; i < std::min(size_t{5}, members.size()); ++i)
    {
        const Character &member = members[i];
        const std::string id = std::string(isLimitedOverlayHud ? "ObsidianOverlayPc" : "ObsidianPc")
            + std::to_string(i + 1);
        const std::optional<GameplayResolvedHudLayoutElement> face = context.resolvePartyPortraitRect(width, height, i);
        const std::optional<GameplayHudTextureHandle> portrait =
            context.gameplayUiRuntime().ensureHudTextureLoaded(context.resolvePortraitTextureName(member));
        if (portrait && face)
        {
            bgfx::TextureHandle texture = portrait->textureHandle;
            if (party.hasCharacterBuff(i, CharacterBuffId::Mistform))
            {
                texture = context.gameplayUiRuntime().ensureHudTextureColorModulated(
                    *portrait, MistformPortraitModulationAbgr);
            }
            if (!GameMechanics::canAct(member))
            {
                texture = context.gameplayUiRuntime().ensureHudTextureColorModulated(*portrait, 0xff888888u);
            }
            context.gameplayUiRuntime().submitHudTexturedEllipse(texture, face->x, face->y, face->width, face->height);
            context.renderPortraitFx(i, face->x, face->y, face->width, face->height);
        }
        const UiLayoutManager::LayoutElement *pRimLayout = context.findHudLayoutElement(id + "Rim");
        const std::optional<GameplayResolvedHudLayoutElement> rim =
            context.resolveHudLayoutElement(id + "Rim", width, height, 0, 0);
        if (pRimLayout != nullptr && pRimLayout->meterArc && rim)
        {
            const UiLayoutManager::MeterArc &arc = *pRimLayout->meterArc;
            GameplayUiSkin::renderArc(context, *rim, 2.8f, arc.startDegrees, arc.sweepDegrees,
                GameplayUiSkin::ArcMaterial::Track);
            const bool selectedRim = showSelection && i == selected;
            GameplayUiSkin::renderArc(context, *rim, selectedRim ? 1.5f : arc.strokeWidth,
                arc.startDegrees, arc.sweepDegrees, selectedRim ? GameplayUiSkin::ArcMaterial::SelectedRim
                    : GameplayUiSkin::ArcMaterial::NormalRim);
        }
        else
        {
            draw(id + "Rim", std::string(isLimitedOverlayHud ? "obsidian_hud_fullscreen_rim_"
                : "obsidian_hud_portrait_rim_") + (showSelection && i == selected ? "selected" : "normal"));
        }
        if (showSelection && i == selected)
        {
            draw(id + "Selection");
        }
        const bool canAct = GameMechanics::canAct(member);
        const PortraitAggroIndicator readiness = classifyPortraitAggroIndicator(member, nearestHostile, engagementRange);
        const char *pReadinessArt = readiness == PortraitAggroIndicator::Red ? "obsidian_aggro_combat"
            : readiness == PortraitAggroIndicator::Yellow ? "obsidian_aggro_nearby"
            : readiness == PortraitAggroIndicator::Green ? "obsidian_aggro_explore" : "obsidian_aggro_unlit";
        const std::optional<GameplayResolvedHudLayoutElement> readinessRect =
            context.resolveHudLayoutElement(id + "Readiness", width, height, 0, 0);
        const std::optional<GameplayHudTextureHandle> readinessArt =
            context.gameplayUiRuntime().ensureHudTextureLoaded(pReadinessArt);
        if (readinessRect && readinessArt)
        {
            const float unit = readinessRect->width / 22.0f;
            context.submitHudTexturedQuad(*readinessArt, readinessRect->x - 8 * unit,
                readinessRect->y - 8 * unit, 38 * unit, 41 * unit);
        }
        GameplayPortraitMeterState &meter = context.gameplayUiRuntime().portraitPresentationState().meters[i];
        if (member.recoverySecondsRemaining <= 0)
        {
            meter.recoveryMaximum = 0;
        }
        else
        {
            meter.recoveryMaximum = std::max(meter.recoveryMaximum, member.recoverySecondsRemaining);
            if (readinessRect && canAct)
            {
                const float fraction = 1 - member.recoverySecondsRemaining / meter.recoveryMaximum;
                const std::optional<GameplayHudTextureHandle> arc =
                    context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__obsidian_recovery__", 0xffc7dce5u);
                if (arc)
                {
                    const float cx = readinessRect->x + readinessRect->width * 0.5f;
                    const float cy = readinessRect->y + readinessRect->height * 0.5f;
                    const float radius = readinessRect->width * 0.65f;
                    std::vector<GameplayHudBatchQuad> ring;
                    for (int segment = 0; segment < 32 * fraction; ++segment)
                    {
                        const float angle = -Pi * 0.5f + segment * 2 * Pi / 32;
                        const float next = -Pi * 0.5f + std::min(float(segment + 1) / 32, fraction) * 2 * Pi;
                        GameplayHudBatchQuad line;
                        line.textureHandle = arc->textureHandle;
                        line.line = true;
                        line.width = std::max(1.0f, readinessRect->scale * 1.3f);
                        line.x = cx + std::cos(angle) * radius;
                        line.y = cy + std::sin(angle) * radius;
                        line.x2 = cx + std::cos(next) * radius;
                        line.y2 = cy + std::sin(next) * radius;
                        ring.push_back(line);
                    }
                    context.submitHudQuadBatch(ring);
                }
            }
        }
        bool hasPersonalBuff = false;
        for (size_t b = 0; b < CharacterBuffCount; ++b)
        {
            hasPersonalBuff |= party.hasCharacterBuff(i, static_cast<CharacterBuffId>(b));
        }
        // Potions a ruleset times on the member show as personal buffs too.
        hasPersonalBuff = hasPersonalBuff || !gameplayPotionEffectLines(member, nullptr).empty()
            || !gameplayUnslottedAuraLines(party, member, nullptr).empty();

        if (hasPersonalBuff)
        {
            draw(id + "PersonalBuffs");
        }

        // The class counter's gems beside the HP arc (MAW's combo points and Elementalist stacks).
        if (const PortraitCounter counter = party.rules().classes.portraitCounter(member);
            counter.kind != PortraitCounterKind::None)
        {
            const UiLayoutManager::LayoutElement *pHealthLayout = context.findHudLayoutElement(id + "Health");
            const std::optional<GameplayResolvedHudLayoutElement> healthArc =
                context.resolveHudLayoutElement(id + "Health", width, height, 0, 0);
            if (pHealthLayout != nullptr && pHealthLayout->meterArc && healthArc)
            {
                renderPortraitCounterGems(context, counter, *healthArc, pHealthLayout->meterArc->strokeWidth,
                    id + "Counter");
            }
        }
        const int maximumHealth = GameMechanics::calculateEffectiveCharacterMaxHealth(member);
        const int maximumMana = GameMechanics::calculateEffectiveCharacterMaxSpellPoints(member);
        const float health = std::clamp(float(member.health) / std::max(1, maximumHealth), 0.0f, 1.0f);
        const float mana = std::clamp(float(member.spellPoints) / std::max(1, maximumMana), 0.0f, 1.0f);
        const uint32_t nowTicks = context.animationTicks();
        if (meter.health >= 0 && health < meter.health)
        {
            meter.damageFrom = meter.health;
            meter.damagedTicks = nowTicks;
        }
        meter.health = health;
        const float trail = health + std::max(0.0f, meter.damageFrom - health)
            * std::max(0.0f, 1.0f - (nowTicks - meter.damagedTicks) / 96.0f);
        for (bool isHealth : {true, false})
        {
            if (!isHealth && maximumMana <= 0)
            {
                continue;
            }
            const std::string meterId = id + (isHealth ? "Health" : "Mana");
            const float amount = isHealth ? health : mana;
            const std::optional<GameplayResolvedHudLayoutElement> rect =
                context.resolveHudLayoutElement(meterId, width, height, 0, 0);
            if (!rect)
            {
                continue;
            }
            const UiLayoutManager::LayoutElement *pMeterLayout = context.findHudLayoutElement(meterId);
            if (pMeterLayout != nullptr && pMeterLayout->meterArc)
            {
                const UiLayoutManager::MeterArc &arc = *pMeterLayout->meterArc;
                using GameplayUiSkin::ArcMaterial;
                GameplayUiSkin::renderArc(context, *rect, arc.strokeWidth + 1.7f,
                    arc.startDegrees, arc.sweepDegrees, ArcMaterial::TrackEdge);
                GameplayUiSkin::renderArc(context, *rect, arc.strokeWidth + 0.5f,
                    arc.startDegrees, arc.sweepDegrees, ArcMaterial::Track);
                // The end of the gauge the member's auras hold, which the pool cannot fill.
                const int reservedPoints = isHealth ? party.rules().spells.reservedHitPoints(party, i)
                    : party.rules().spells.reservedSpellPoints(party, i);
                const float reserved = std::clamp(
                    float(reservedPoints) / std::max(1, isHealth ? maximumHealth : maximumMana), 0.0f, 1.0f);
                if (reserved > 0)
                {
                    GameplayUiSkin::renderReservedArc(context, *rect, arc.strokeWidth,
                        arc.startDegrees, arc.sweepDegrees, 1 - reserved, isHealth);
                }
                if (isHealth && trail > health)
                {
                    GameplayUiSkin::renderArc(context, *rect, arc.strokeWidth,
                        arc.startDegrees, arc.sweepDegrees, ArcMaterial::Damage, health, trail);
                }
                const GameplayUiSkin::HealthBand band = GameplayUiSkin::healthBand(health);
                const ArcMaterial material = !isHealth ? ArcMaterial::Mana
                    : band == GameplayUiSkin::HealthBand::High ? ArcMaterial::HealthHigh
                    : band == GameplayUiSkin::HealthBand::Middle ? ArcMaterial::HealthMiddle
                    : ArcMaterial::HealthLow;
                if (amount > 0)
                {
                    GameplayUiSkin::renderArc(context, *rect, arc.strokeWidth,
                        arc.startDegrees, arc.sweepDegrees, material, 0, amount);
                }
                if (reserved > 0)
                {
                    GameplayUiSkin::renderReservedMark(context, *rect, arc.strokeWidth,
                        arc.startDegrees, arc.sweepDegrees, 1 - reserved);
                }
                if (isHealth && member.personalShieldCapacity > 0)
                {
                    // The personal energy shield: a thin cyan rim just outside the HP arc; it flashes white as it
                    // breaks and stays dark while down (COMBAT.md, Party shields).
                    const float offset = (arc.strokeWidth * 0.5f + 1.5f) * rect->scale;
                    const GameplayResolvedHudLayoutElement rim = {rect->x - offset, rect->y - offset,
                        rect->width + 2.0f * offset, rect->height + 2.0f * offset, rect->scale};
                    const float shield = std::clamp(
                        member.personalShield / float(member.personalShieldCapacity), 0.0f, 1.0f);
                    const bool breaking = member.personalShieldSecondsSinceBreak >= 0.0f
                        && member.personalShieldSecondsSinceBreak < 0.4f && shield <= 0.0f;
                    GameplayUiSkin::renderArc(context, rim, 1.3f, arc.startDegrees, arc.sweepDegrees,
                        ArcMaterial::ShieldDown);
                    if (breaking)
                    {
                        GameplayUiSkin::renderArc(context, rim, 1.8f, arc.startDegrees, arc.sweepDegrees,
                            ArcMaterial::ShieldFlash);
                    }
                    else if (shield > 0.0f)
                    {
                        GameplayUiSkin::renderArc(context, rim, 1.3f, arc.startDegrees, arc.sweepDegrees,
                            ArcMaterial::Shield, 0, shield);
                    }
                }
                continue;
            }
            const bool vertical = rect->height > rect->width;
            if (vertical)
            {
                GameplayUiSkin::renderTexture(context, "obsidian_party_meter_track",
                    {rect->x - rect->scale, rect->y - rect->scale,
                        rect->width + 2 * rect->scale, rect->height + 2 * rect->scale, rect->scale});
            }
            else
            {
                draw(meterId, "obsidian_hud_meter_track");
            }
            const std::optional<GameplayHudTextureHandle> texture =
                isHealth ? GameplayUiSkin::healthMeterTexture(context, health, vertical)
                    : context.gameplayUiRuntime().ensureHudTextureLoaded(
                        vertical ? "obsidian_party_meter_sp" : "obsidian_hud_meter_sp");
            if (isHealth && trail > health)
            {
                const std::optional<GameplayHudTextureHandle> damage =
                    context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__obsidian_damage_trail__", 0xff93c7e4u);
                if (damage)
                {
                    const GameplayResolvedHudLayoutElement segment =
                        GameplayUiSkin::meterSegment(*rect, health, trail, vertical);
                    context.submitHudTexturedQuad(*damage, segment.x, segment.y, segment.width, segment.height);
                }
            }
            if (texture && amount > 0)
            {
                const GameplayResolvedHudLayoutElement segment =
                    GameplayUiSkin::meterSegment(*rect, 0, amount, vertical);
                context.gameplayUiRuntime().submitHudTexturedQuad(texture->textureHandle,
                    segment.x, segment.y, segment.width, segment.height,
                    0, vertical ? 1 - amount : 0, vertical ? 1 : amount, 1);
            }
        }
    }
    if (isLimitedOverlayHud)
    {
        for (size_t i = members.size(); i < 5; ++i)
        {
            draw("CharShield_" + std::to_string(i + 1));
        }
    }

    GameplayMinimapState minimapState = {};
    bool hasMinimapState = false;
    GameplayResolvedHudLayoutElement minimapOverlay = {};

    for (const GameplayHudLayoutEntry &entry : context.gameplayUiRuntime().gameplayHudLayoutEntries())
    {
        const UiLayoutManager::LayoutElement *pLayout = entry.pLayout;
        const std::string &layoutId = pLayout->id;
        const std::string &normalizedLayoutId = pLayout->normalizedId;
        const std::string &normalizedRoleId = entry.normalizedRoleId;
        if (!pLayout->visible || !entry.visibleIn(gameplayHudLayout, context.interactionState().followerPanelOpen))
        {
            continue;
        }

        if (normalizedRoleId.starts_with("outdoormobilebutton"))
        {
            const bool flight = normalizedRoleId == "outdoormobilebuttonflyup"
                || normalizedRoleId == "outdoormobilebuttonflydown";
            if (flight && !context.mobileFlightControlsAvailable())
            {
                continue;
            }
            const std::optional<GameplayResolvedHudLayoutElement> rect =
                resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);
            if (rect)
            {
                const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
                const bool hovered = context.isPointerInsideResolvedElement(*rect, characterMouseX, characterMouseY);
                const bool held = flight && pInput != nullptr && pInput->action(
                    normalizedRoleId == "outdoormobilebuttonflyup" ? KeyboardAction::FlyUp : KeyboardAction::FlyDown).held;
                const bool resume = normalizedRoleId == "outdoormobilebuttonpause"
                    && context.turnBasedCombatRuntime().active();
                flushQueuedHudQuads();
                GameplayUiSkin::renderIconButton(context, *rect,
                    resume ? "obsidian_action_resume" : pLayout->primaryAsset,
                    hovered, held || (hovered && isLeftMousePressed), resume);
            }
            continue;
        }

        if (normalizedRoleId == "outdoorfollowertoggle")
        {
            flushQueuedHudQuads();
            GameplayUiSkin::renderButton(context, layoutId, width, height,
                context.interactionState().followerPanelOpen);
            continue;
        }
        if (pLayout->parentId == "OutdoorFollowerToggle")
        {
            continue; // The button renderer owns its head illustration.
        }
        if (normalizedRoleId == "outdoorfollowerpanel")
        {
            const std::optional<GameplayResolvedHudLayoutElement> rect =
                resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);
            if (rect)
            {
                flushQueuedHudQuads();
                GameplayUiSkin::renderPanel(context, *rect);
            }
            continue;
        }
        if (normalizedRoleId == "outdoorfollowerscrollup" || normalizedRoleId == "outdoorfollowerscrolldown")
        {
            const size_t offset = context.interactionState().followerPanelScrollOffset;
            const bool enabled = normalizedRoleId == "outdoorfollowerscrollup"
                ? offset > 0 : offset + 3 < followerViews.size();
            flushQueuedHudQuads();
            GameplayUiSkin::renderButton(context, layoutId, width, height, false, enabled);
            continue;
        }

        if (normalizedRoleId == "outdoorminimap")
        {
            if (!context.tryGetGameplayMinimapState(minimapState) || pLayout->width <= 0.0f || pLayout->height <= 0.0f)
            {
                continue;
            }

            const std::optional<GameplayResolvedHudLayoutElement> resolved =
                resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);

            if (!resolved)
            {
                continue;
            }

            const float minimapZoomWidth = minimapState.zoomWidth > 0.0f
                ? minimapState.zoomWidth
                : minimapState.zoom;
            const float minimapZoomHeight = minimapState.zoomHeight > 0.0f
                ? minimapState.zoomHeight
                : minimapState.zoom;
            minimapState.uSpan = std::min(1.0f, pLayout->width / std::max(1.0f, minimapZoomWidth));
            minimapState.vSpan = std::min(1.0f, pLayout->height / std::max(1.0f, minimapZoomHeight));
            minimapState.u0 = std::clamp(
                minimapState.partyU - minimapState.uSpan * 0.5f,
                0.0f,
                1.0f - minimapState.uSpan);
            minimapState.v0 = std::clamp(
                minimapState.partyV - minimapState.vSpan * 0.5f,
                0.0f,
                1.0f - minimapState.vSpan);

            const std::optional<GameplayHudTextureHandle> minimapTexture = minimapState.vectorBackground
                ? context.gameplayUiRuntime().ensureSolidHudTextureLoaded(
                    "__obsidian_indoor_minimap_background__", GameplayUiSkin::MapSurface)
                : context.gameplayUiRuntime().ensureHudTextureLoaded(minimapState.textureName);
            if (minimapTexture)
            {
                flushQueuedHudQuads();
                context.gameplayUiRuntime().submitHudTexturedEllipse(minimapTexture->textureHandle,
                    resolved->x, resolved->y, resolved->width, resolved->height,
                    minimapState.u0, minimapState.v0, minimapState.u0 + minimapState.uSpan,
                    minimapState.v0 + minimapState.vSpan);
            }
            minimapOverlay = *resolved;
            hasMinimapState = true;
            continue;
        }

        const std::optional<size_t> followerSlotIndex = followerPortraitSlotIndex(normalizedRoleId);
        if (followerSlotIndex)
        {
            const size_t followerIndex = context.interactionState().followerPanelScrollOffset + *followerSlotIndex;
            if (followerIndex < followerViews.size())
            {
                const std::string textureName =
                    npcPortraitTextureName(followerViews[followerIndex].portraitPictureId);
                const std::optional<GameplayHudTextureHandle> texture =
                    !textureName.empty()
                        ? context.gameplayUiRuntime().ensureHudTextureLoaded(textureName)
                        : std::nullopt;
                const std::optional<GameplayResolvedHudLayoutElement> resolved =
                    resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);

                if (texture && resolved)
                {
                    if (texture->width == EventNpcPortraitNativeWidth
                        && texture->height == EventNpcPortraitNativeHeight)
                    {
                        submitQuadUv(
                            queuedHudQuads,
                            *texture,
                            resolved->x,
                            resolved->y,
                            resolved->width,
                            resolved->height,
                            EventNpcPortraitUvCropX / static_cast<float>(EventNpcPortraitNativeWidth),
                            EventNpcPortraitUvCropY / static_cast<float>(EventNpcPortraitNativeHeight),
                            (static_cast<float>(EventNpcPortraitNativeWidth) - EventNpcPortraitUvCropX)
                                / static_cast<float>(EventNpcPortraitNativeWidth),
                            (static_cast<float>(EventNpcPortraitNativeHeight) - EventNpcPortraitUvCropY)
                                / static_cast<float>(EventNpcPortraitNativeHeight));
                    }
                    else
                    {
                        submitQuad(
                            queuedHudQuads,
                            *texture,
                            resolved->x,
                            resolved->y,
                            resolved->width,
                            resolved->height);
                    }
                }
            }

            continue;
        }

        if (!pLayout->labelText.empty() && pLayout->labelText.find('{') == std::string::npos)
        {
            flushQueuedHudQuads();
            label(layoutId, pLayout->labelText);
        }
        std::string primaryAsset = pLayout->primaryAsset;

        const bool flyBuffIcon = normalizedRoleId == "outdoorflybufficon";
        const bool waterWalkBuffIcon = normalizedRoleId == "outdoorwaterwalkbufficon";
        if ((flyBuffIcon && !gameplayFlightBuff(party))
            || (waterWalkBuffIcon && !party.hasPartyBuff(PartyBuffId::WaterWalk)))
        {
            continue;
        }
        if (flyBuffIcon)
        {
            const IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
            const bool activelyFlying = pWorldRuntime != nullptr && pWorldRuntime->partyIsActivelyFlyingForHud();
            const std::optional<std::string> animationFrame =
                context.gameplayUiRuntime().flyBuffIconAnimationFrameTextureName(activelyFlying, 1);

            if (animationFrame)
            {
                primaryAsset = *animationFrame;
            }
        }
        else if (waterWalkBuffIcon)
        {
            const std::optional<std::string> animationFrame =
                context.gameplayUiRuntime().iconAnimationFrameTextureName("spell27");
            if (animationFrame)
            {
                primaryAsset = *animationFrame;
            }
        }

        if (primaryAsset.empty() && pLayout->hoverAsset.empty() && pLayout->pressedAsset.empty())
        {
            continue;
        }

        const std::optional<GameplayResolvedHudLayoutElement> interactiveResolved =
            resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);
        const std::string *pAssetName = interactiveResolved && !flyBuffIcon && !waterWalkBuffIcon
            ? context.resolveInteractiveAssetName(*pLayout, *interactiveResolved,
                characterMouseX, characterMouseY, isLeftMousePressed) : &primaryAsset;
        std::optional<GameplayHudTextureHandle> texture;
        if (pAssetName != nullptr && !pAssetName->empty())
        {
            texture = context.gameplayUiRuntime().ensureHudTextureLoaded(*pAssetName);
        }

        if (!texture && !primaryAsset.empty())
        {
            texture = context.gameplayUiRuntime().ensureHudTextureLoaded(primaryAsset);
        }

        if (!texture)
        {
            continue;
        }

        const std::optional<GameplayResolvedHudLayoutElement> resolved = resolveLayout(
            context,
            layoutId,
            pLayout->width > 0.0f ? pLayout->width : static_cast<float>(texture->width),
            pLayout->height > 0.0f ? pLayout->height : static_cast<float>(texture->height),
            width,
            height);

        if (!resolved)
        {
            continue;
        }

        submitQuad(queuedHudQuads, *texture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    if (hudScreenState == GameplayHudScreenState::Gameplay && hasMinimapState)
    {
        const float minimapCenterX =
            minimapOverlay.x + ((minimapState.partyU - minimapState.u0) / minimapState.uSpan) * minimapOverlay.width;
        const float minimapCenterY =
            minimapOverlay.y + ((minimapState.partyV - minimapState.v0) / minimapState.vSpan) * minimapOverlay.height;
        const float markerSize = std::max(1.5f, 2.0f * minimapOverlay.scale);
        const float worldItemMarkerSize = std::max(1.5f, 2.0f * minimapOverlay.scale);
        const float projectileMarkerSize = std::max(1.0f, 1.0f * minimapOverlay.scale);
        const float decorationMarkerSize = std::max(1.5f, 2.0f * minimapOverlay.scale);
        const float markerHalfSize = markerSize * 0.5f;
        const float worldItemMarkerHalfSize = worldItemMarkerSize * 0.5f;
        const float projectileMarkerHalfSize = projectileMarkerSize * 0.5f;
        const float decorationMarkerHalfSize = decorationMarkerSize * 0.5f;
        const float markerMargin = std::max(2.0f, 2.0f * minimapOverlay.scale);
        const float markerMinX = minimapOverlay.x + markerMargin + markerHalfSize;
        const float markerMaxX = minimapOverlay.x + minimapOverlay.width - markerMargin - markerHalfSize;
        const float markerMinY = minimapOverlay.y + markerMargin + markerHalfSize;
        const float markerMaxY = minimapOverlay.y + minimapOverlay.height - markerMargin - markerHalfSize;
        const uint16_t minimapScissorX =
            static_cast<uint16_t>(std::max(0.0f, std::floor(minimapOverlay.x + markerMargin)));
        const uint16_t minimapScissorY =
            static_cast<uint16_t>(std::max(0.0f, std::floor(minimapOverlay.y + markerMargin)));
        const uint16_t minimapScissorWidth =
            static_cast<uint16_t>(std::max(1.0f, std::ceil(minimapOverlay.width - markerMargin * 2.0f)));
        const uint16_t minimapScissorHeight =
            static_cast<uint16_t>(std::max(1.0f, std::ceil(minimapOverlay.height - markerMargin * 2.0f)));
        std::vector<GameplayMinimapLineState> minimapLines;
        context.collectGameplayMinimapLines(minimapLines);

        for (const GameplayMinimapLineState &line : minimapLines)
        {
            float lineX0 =
                minimapOverlay.x + ((line.u0 - minimapState.u0) / minimapState.uSpan) * minimapOverlay.width;
            float lineY0 =
                minimapOverlay.y + ((line.v0 - minimapState.v0) / minimapState.vSpan) * minimapOverlay.height;
            float lineX1 =
                minimapOverlay.x + ((line.u1 - minimapState.u0) / minimapState.uSpan) * minimapOverlay.width;
            float lineY1 =
                minimapOverlay.y + ((line.v1 - minimapState.v0) / minimapState.vSpan) * minimapOverlay.height;

            if (!clipHudLineToCircle(minimapOverlay.x + minimapOverlay.width * 0.5f,
                minimapOverlay.y + minimapOverlay.height * 0.5f, minimapOverlay.width * 0.5f - markerMargin,
                lineX0, lineY0, lineX1, lineY1))
            {
                continue;
            }

            const std::optional<GameplayHudPaletteColor> lineColor =
                context.gameplayUiRuntime().ensureHudPaletteColor(line.colorAbgr);

            if (!lineColor)
            {
                continue;
            }

            submitLineClipped(
                queuedHudQuads,
                *lineColor,
                lineX0,
                lineY0,
                lineX1,
                lineY1,
                std::max(1.0f, minimapOverlay.scale),
                minimapScissorX,
                minimapScissorY,
                minimapScissorWidth,
                minimapScissorHeight);
        }

        GameplayUiRuntime &uiRuntime = context.gameplayUiRuntime();
        const std::optional<GameplayHudPaletteColor> friendlyMarkerTexture =
            minimapState.wizardEyeActive ? uiRuntime.ensureHudPaletteColor(0xff00ff00u) : std::nullopt;
        const std::optional<GameplayHudPaletteColor> hostileMarkerTexture =
            minimapState.wizardEyeActive ? uiRuntime.ensureHudPaletteColor(0xff0000ffu) : std::nullopt;
        const std::optional<GameplayHudPaletteColor> corpseMarkerTexture =
            minimapState.wizardEyeActive ? uiRuntime.ensureHudPaletteColor(0xff00ffffu) : std::nullopt;
        const std::optional<GameplayHudPaletteColor> worldItemMarkerTexture =
            minimapState.wizardEyeShowsExpertObjects ? uiRuntime.ensureHudPaletteColor(0xffff0000u) : std::nullopt;
        const std::optional<GameplayHudPaletteColor> projectileMarkerTexture =
            minimapState.wizardEyeShowsExpertObjects ? uiRuntime.ensureHudPaletteColor(0xff0000ffu) : std::nullopt;
        const std::optional<GameplayHudPaletteColor> decorationMarkerTexture =
            minimapState.wizardEyeShowsDecorations ? uiRuntime.ensureHudPaletteColor(0xffffffffu) : std::nullopt;
        std::vector<GameplayMinimapMarkerState> markers;
        context.collectGameplayMinimapMarkers(markers);

        for (const GameplayMinimapMarkerState &marker : markers)
        {
            const GameplayHudPaletteColor *pTexture = nullptr;
            float markerHalfExtent = markerHalfSize;
            float markerDrawSize = markerSize;

            switch (marker.type)
            {
            case GameplayMinimapMarkerType::FriendlyActor:
                pTexture = friendlyMarkerTexture ? &*friendlyMarkerTexture : nullptr;
                break;
            case GameplayMinimapMarkerType::HostileActor:
                pTexture = hostileMarkerTexture ? &*hostileMarkerTexture : nullptr;
                break;
            case GameplayMinimapMarkerType::CorpseActor:
                pTexture = corpseMarkerTexture ? &*corpseMarkerTexture : nullptr;
                break;
            case GameplayMinimapMarkerType::WorldItem:
                pTexture = worldItemMarkerTexture ? &*worldItemMarkerTexture : nullptr;
                markerHalfExtent = worldItemMarkerHalfSize;
                markerDrawSize = worldItemMarkerSize;
                break;
            case GameplayMinimapMarkerType::Projectile:
                pTexture = projectileMarkerTexture ? &*projectileMarkerTexture : nullptr;
                markerHalfExtent = projectileMarkerHalfSize;
                markerDrawSize = projectileMarkerSize;
                break;
            case GameplayMinimapMarkerType::Decoration:
                pTexture = decorationMarkerTexture ? &*decorationMarkerTexture : nullptr;
                markerHalfExtent = decorationMarkerHalfSize;
                markerDrawSize = decorationMarkerSize;
                break;
            }

            if (pTexture == nullptr)
            {
                continue;
            }

            const float markerCenterX =
                minimapOverlay.x + ((marker.u - minimapState.u0) / minimapState.uSpan) * minimapOverlay.width;
            const float markerCenterY =
                minimapOverlay.y + ((marker.v - minimapState.v0) / minimapState.vSpan) * minimapOverlay.height;

            const float centerDx = markerCenterX - minimapOverlay.x - minimapOverlay.width * 0.5f;
            const float centerDy = markerCenterY - minimapOverlay.y - minimapOverlay.height * 0.5f;
            const float radius = minimapOverlay.width * 0.5f - markerMargin - markerHalfExtent;
            if (centerDx * centerDx + centerDy * centerDy > radius * radius)
            {
                continue;
            }

            submitPaletteQuadClipped(
                queuedHudQuads,
                *pTexture,
                markerCenterX - markerHalfExtent,
                markerCenterY - markerHalfExtent,
                markerDrawSize,
                minimapScissorX,
                minimapScissorY,
                minimapScissorWidth,
                minimapScissorHeight);
        }

        const int arrowIndex = outdoorMinimapArrowIndex(context.gameplayCameraYawRadians());
        const std::optional<GameplayHudTextureHandle> arrowTexture =
            context.gameplayUiRuntime().ensureHudTextureLoaded("MAPDIR" + std::to_string(arrowIndex + 1));

        if (arrowTexture)
        {
            const float arrowWidth = static_cast<float>(arrowTexture->width) * minimapOverlay.scale;
            const float arrowHeight = static_cast<float>(arrowTexture->height) * minimapOverlay.scale;
            submitQuadClipped(
                queuedHudQuads,
                *arrowTexture,
                minimapCenterX - arrowWidth * 0.5f,
                minimapCenterY - arrowHeight * 0.5f,
                arrowWidth,
                arrowHeight,
                minimapScissorX,
                minimapScissorY,
                minimapScissorWidth,
                minimapScissorHeight);
        }
    }

#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    if (hudScreenState == GameplayHudScreenState::Gameplay)
    {
        const GameplayInputFrame *pInputFrame = context.currentGameplayInputFrame();

        if (pInputFrame != nullptr && pInputFrame->mobileJoystickActive)
        {
            const std::optional<GameplayHudTextureHandle> joystickBase =
                context.gameplayUiRuntime().ensureHudTextureLoaded("obsidian_joystick_base");
            const std::optional<GameplayHudTextureHandle> joystickKnob =
                context.gameplayUiRuntime().ensureHudTextureLoaded("obsidian_joystick_knob");

            if (joystickBase && joystickKnob)
            {
                const float baseSize = 128.0f * uiScale;
                const float knobSize = 48.0f * uiScale;
                submitQuad(
                    queuedHudQuads,
                    *joystickBase,
                    pInputFrame->mobileJoystickBaseX - baseSize * 0.5f,
                    pInputFrame->mobileJoystickBaseY - baseSize * 0.5f,
                    baseSize,
                    baseSize);
                submitQuad(
                    queuedHudQuads,
                    *joystickKnob,
                    pInputFrame->mobileJoystickKnobX - knobSize * 0.5f,
                    pInputFrame->mobileJoystickKnobY - knobSize * 0.5f,
                    knobSize,
                    knobSize);
            }
        }
    }
#endif

    if (hudScreenState == GameplayHudScreenState::Gameplay && context.turnBasedCombatRuntime().active())
    {
        flushQueuedHudQuads();
        draw("ObsidianTurnPlate");
        const TurnBasedCombatRuntime &turn = context.turnBasedCombatRuntime();
        label("ObsidianTurnPhase", turn.stage() == TurnBasedCombatStage::Movement ? "Movement"
            : turn.stage() == TurnBasedCombatStage::Attack ? "Attack" : "Waiting");
        label("ObsidianTurnDetail", turn.stage() == TurnBasedCombatStage::Movement
            ? std::to_string(turn.movementActionPoints()) + " AP" : "Turn based");
    }

    flushQueuedHudQuads();
    if (!isLimitedOverlayHud)
    {
        renderGameplayBuffHud(context, width, height);
        if (context.worldRuntime() != nullptr)
        {
            label("ObsidianMinimapClock", formatGameplayClock(context.worldRuntime()->gameMinutes()));

            // The map progress bar in the party frame's top band, while the rules give a progress (MAW).
            if (hudScreenState == GameplayHudScreenState::Gameplay)
            {
                GameplayMapProgressBar::renderHud(context, width, height);
            }

            // The combat log's button and docked panel, while its setting is on.
            if (context.settingsSnapshot().combatLog)
            {
                // The followers' tab frame with a sword (CombatLogToggleIcon).
                flushQueuedHudQuads();
                GameplayUiSkin::renderButton(
                    context, "CombatLogToggle", width, height, context.combatLogPanel().open());

                flushQueuedHudQuads();
                context.combatLogPanel().render(context, width, height);
            }

            if (const std::optional<int> seconds =
                    party.rules().experience.deathPendingSeconds(context.worldRuntime()->gameMinutes()))
            {
                // Red while a death is pending (an R5G6B5 colour code, as the clearing share's).
                draw("ObsidianDeathTimerPlate");
                label("ObsidianDeathTimer", "\f63488" + std::to_string(*seconds));
            }
        }
    }

    // The quick item buttons at the portraits and the open ring (the potion radial), over the gameplay HUD.
    if (!isLimitedOverlayHud && hudScreenState == GameplayHudScreenState::Gameplay)
    {
        GameplayQuickItems::renderHud(context, width, height);
    }
}

void GameplayUiRenderer::renderMobileInspectButton(GameplayScreenRuntime &context, int width, int height)
{
    if (!context.hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }

    if (!context.mobileInspectControlAvailable())
    {
        return;
    }

    const UiLayoutManager::LayoutElement *pLayout =
        context.findHudLayoutElement(context.mobileInspectLayoutId());

    if (pLayout == nullptr || pLayout->primaryAsset.empty())
    {
        return;
    }

    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    const bool inspectHeld = pInput != nullptr && pInput->rightMouseButton.held;
    const bool inspectLocked = pInput != nullptr && pInput->mobileInspectLocked;
    const std::optional<GameplayResolvedHudLayoutElement> resolved = resolveLayout(
        context,
        pLayout->id,
        pLayout->width,
        pLayout->height,
        width,
        height);

    if (!resolved)
    {
        return;
    }

    context.prepareHudView(width, height);
    GameplayUiSkin::renderIconButton(
        context, *resolved, pLayout->primaryAsset, false, inspectHeld && !inspectLocked, inspectLocked);
}
} // namespace OpenYAMM::Game
