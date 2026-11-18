#pragma once

#include "game/rules/ClassRules.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
// A gem of a portrait class counter (level_generation/ui/maw_combo_points_20261025, option B): how much of it is
// lit, from the bottom, and whether it shows the second lap's pale gold.
struct PortraitGemFill
{
    float fill = 0;
    bool secondLap = false;

    bool operator==(const PortraitGemFill &other) const = default;
};

// One fill per pip, lit from the first (the lowest gem); a half point lights half a gem. An amount past the pips
// starts a second lap: every gem stays lit and the first (amount - pips) turn pale gold.
inline std::vector<PortraitGemFill> portraitGemFills(const PortraitCounter &counter)
{
    std::vector<PortraitGemFill> fills(size_t(std::max(0, counter.pips)));
    const double pips = double(fills.size());
    const bool secondLap = counter.amount > pips;
    const double shown = secondLap ? counter.amount - pips : counter.amount;

    for (size_t k = 0; k < fills.size(); ++k)
    {
        const float lit = float(std::clamp(shown - double(k), 0.0, 1.0));
        fills[k] = secondLap ? PortraitGemFill{1, lit > 0} : PortraitGemFill{lit, false};
    }

    return fills;
}

struct PortraitGemPlace
{
    float x = 0;
    float y = 0;
    float radius = 0;
};

// Where a counter's gems sit, in the units of the HP arc's ellipse (its centre, the radii of the stroke's centre
// line and the stroke width): on an arc just outside the HP arc's outer edge at the portrait's upper left, first gem
// lowest. Five gems are larger than ten; both stay closer to their own HP arc than to the left neighbour's mana arc.
// `radius` is the gem's outer radius, socket rim included.
inline std::vector<PortraitGemPlace> portraitGemPlaces(int pips, float centreX, float centreY, float radiusX,
    float radiusY, float stroke)
{
    constexpr float Pi = 3.14159265358979f;
    std::vector<PortraitGemPlace> places;

    if (pips <= 0)
    {
        return places;
    }

    const bool large = pips <= 5;
    const float radius = large ? 3.5f : 2.55f;
    const float offset = stroke * 0.5f + 0.15f + radius;
    const float first = large ? 162.0f : 165.0f;
    const float last = large ? 234.0f : 243.0f;

    for (int k = 0; k < pips; ++k)
    {
        const float degrees = pips > 1 ? first + (last - first) * k / float(pips - 1) : first;
        const float radians = degrees * Pi / 180;
        places.push_back({centreX + (radiusX + offset) * std::cos(radians),
            centreY + (radiusY + offset) * std::sin(radians), radius});
    }

    return places;
}

// The number badge of a counter with ten gems, `width` x `height` (logical units, around the arc's centre at 0, 0):
// its box between the first gem and the aggro diamond, its right edge just outside the HP arc's outer edge.
inline PortraitGemPlace portraitGemBadgePlace(float width, float height, float radiusX, float radiusY, float stroke)
{
    constexpr float CentreY = 21.0f;
    const float outerX = radiusX + stroke * 0.5f;
    const float outerY = radiusY + stroke * 0.5f;
    // The arc's outer edge at the badge's top, where it reaches furthest out.
    const float top = std::clamp((CentreY - height * 0.5f) / outerY, -1.0f, 1.0f);
    const float right = -outerX * std::sqrt(1 - top * top) - 0.6f;
    return {right - width * 0.5f, CentreY, height * 0.5f};
}

// A counter's gems in a row (the solo unit frame's, under its bars), first gem left, around the row's centre at
// `centreX`, `centreY` (logical units). Five gems are larger than ten.
inline std::vector<PortraitGemPlace> counterGemRowPlaces(int pips, float centreX, float centreY)
{
    std::vector<PortraitGemPlace> places;
    const bool large = pips <= 5;
    const float radius = large ? 4.4f : 3.3f;
    const float step = large ? 10.5f : 7.6f;

    for (int k = 0; k < pips; ++k)
    {
        places.push_back({centreX + (float(k) - float(pips - 1) / 2) * step, centreY, radius});
    }

    return places;
}

// The number badge of a row of ten gems, `width` wide: its centre just right of the last gem.
inline PortraitGemPlace counterGemRowBadgePlace(int pips, float width, float height, float centreX, float centreY)
{
    const std::vector<PortraitGemPlace> places = counterGemRowPlaces(pips, centreX, centreY);
    const float right = places.empty() ? centreX : places.back().x + places.back().radius;
    return {right + 1.5f + width / 2, centreY, height / 2};
}

// The counter's gems (and, for ten, the number badge in the text style of the layout element `badgeLayoutId`) around
// the HP arc of `healthArc`, its meter rectangle on screen with the arc's stroke width in logical units. Nothing for
// a counter without pips.
void renderPortraitCounterGems(GameplayScreenRuntime &context, const PortraitCounter &counter,
    const GameplayResolvedHudLayoutElement &healthArc, float strokeWidth, const std::string &badgeLayoutId);
// The screen rectangle the counter's gems cover, for the hover popup; nothing without pips.
std::optional<GameplayResolvedHudLayoutElement> portraitCounterGemBounds(const PortraitCounter &counter,
    const GameplayResolvedHudLayoutElement &healthArc, float strokeWidth);
// The counter as a row of gems (counterGemRowPlaces) centred at `centreX`, `centreY` in screen pixels, `scale` pixels
// to a logical unit; for ten, the number badge right of the row in the text style of `badgeLayoutId`.
void renderCounterGemRow(GameplayScreenRuntime &context, const PortraitCounter &counter, float centreX, float centreY,
    float scale, const std::string &badgeLayoutId);
// The screen rectangle the row and its badge cover, for the hover popup; nothing without pips.
std::optional<GameplayResolvedHudLayoutElement> counterGemRowBounds(const PortraitCounter &counter, float centreX,
    float centreY, float scale);
}
