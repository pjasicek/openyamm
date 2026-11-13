#pragma once

#include "game/ui/GameplayOverlayTypes.h"
#include <algorithm>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

namespace GameplayUiSkin
{
constexpr char CombatFontName[] = "alegreya_semibold";
// The floating damage numbers' face: the same Alegreya, rasterized large (CombatFloatingText).
constexpr char CombatNumberFontName[] = "combat_numbers";
constexpr uint32_t Ivory = 0xffc7dce5u;
constexpr uint32_t Gold = 0xff93c7e4u;
constexpr uint32_t Bonus = 0xff8bdf85u;
constexpr uint32_t Penalty = 0xff7582eeu;
constexpr uint32_t Low = 0xff6cc3e6u;
constexpr uint32_t Learnable = 0xfffabc8eu;
constexpr uint32_t Hover = 0xffffe0c5u;
constexpr uint32_t MapSurface = 0xff1d211bu;

inline float combatDamageTextOriginZ(float actorZ, float actorHeight)
{
    constexpr float TorsoHeightFraction = 0.65f;
    constexpr float MinimumTorsoOffset = 56.0f;
    constexpr float MaximumEffectiveActorHeight = 256.0f;
    const float effectiveHeight = std::clamp(actorHeight, 0.0f, MaximumEffectiveActorHeight);
    return actorZ + std::max(MinimumTorsoOffset, effectiveHeight * TorsoHeightFraction);
}

enum class HealthBand
{
    High,
    Middle,
    Low
};

enum class ArcMaterial
{
    HealthHigh,
    HealthMiddle,
    HealthLow,
    Mana,
    TrackEdge,
    Track,
    NormalRim,
    SelectedRim,
    Damage,
    // The personal energy shield's thin outer rim over the HP arc: charge, empty track, the flash as it breaks.
    Shield,
    ShieldDown,
    ShieldFlash
};

inline HealthBand healthBand(float fraction)
{
    return fraction >= 0.66f ? HealthBand::High : fraction > 0.33f ? HealthBand::Middle : HealthBand::Low;
}

std::optional<GameplayHudTextureHandle> healthMeterTexture(const GameplayScreenRuntime &context, float fraction,
    bool vertical = false);
inline GameplayResolvedHudLayoutElement meterSegment(const GameplayResolvedHudLayoutElement &rect,
    float begin, float end, bool vertical)
{
    begin = std::clamp(begin, 0.0f, 1.0f);
    end = std::clamp(end, begin, 1.0f);
    return vertical
        ? GameplayResolvedHudLayoutElement{rect.x, rect.y + rect.height * (1 - end),
            rect.width, rect.height * (end - begin), rect.scale}
        : GameplayResolvedHudLayoutElement{rect.x + rect.width * begin, rect.y,
            rect.width * (end - begin), rect.height, rect.scale};
}
// `pLabel` replaces the layout's label text (a live price, say).
void renderButton(GameplayScreenRuntime &context, const std::string &id, int width, int height,
    bool selected = false, bool enabled = true, const std::string *pLabel = nullptr);
void renderIconButton(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &rect,
    const std::string &icon, bool hovered, bool pressed, bool selected = false);
void renderPanel(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &rect,
    bool openBottom = false, float borderScale = 1, uint8_t surfaceAlpha = 255);
void renderArc(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &rect,
    float strokeWidth, float startDegrees, float sweepDegrees, ArcMaterial material, float begin = 0, float end = 1);
// The share of a portrait gauge held by auras: a dark hatched band from `begin` to the end of the arc (green-tinted
// on the HP arc, slate on the mana arc).
void renderReservedArc(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &rect,
    float strokeWidth, float startDegrees, float sweepDegrees, float begin, bool health);
// The gold mark across a gauge where its free pool ends, drawn over the fill.
void renderReservedMark(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &rect,
    float strokeWidth, float startDegrees, float sweepDegrees, float at);
void renderPartyBasebar(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &rect);
// Whether the frame's end ornaments carry the sockets of the potion and scroll buttons: in plain gameplay with the
// Potion and scroll buttons setting on; other screens keep the plain ornaments.
bool partyBasebarHasSockets(GameplayScreenRuntime &context);
// Where the drawn party frame ends on the left, its end ornament included.
float partyBasebarLeft(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &rect);
// The round socket of the left (scrolls) or right (potions) socketed ornament, in pixels; the buttons keep this place
// when the frame is hidden.
struct PartyBasebarSocket
{
    float x = 0;
    float y = 0;
    float radius = 0;
};
PartyBasebarSocket partyBasebarSocket(const GameplayResolvedHudLayoutElement &rect, bool right);
void renderSurface(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &rect,
    uint8_t alpha = 255);
void renderTexture(GameplayScreenRuntime &context, const std::string &asset,
    const GameplayResolvedHudLayoutElement &rect);
GameplayResolvedHudLayoutElement scrollbarThumb(const GameplayResolvedHudLayoutElement &viewport,
    float fraction, float visibleFraction);
void renderScrollbar(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &viewport,
    float fraction, float visibleFraction, bool active);
}
}
