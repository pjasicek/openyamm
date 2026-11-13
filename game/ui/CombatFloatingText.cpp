#include "game/ui/CombatFloatingText.h"

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t opaqueAbgr(uint32_t red, uint32_t green, uint32_t blue)
{
    return 0xff000000u | (blue << 16) | (green << 8) | red;
}

// Every hit's number: a warm ivory gold, never white.
constexpr uint32_t DamageColor = opaqueAbgr(250, 226, 150);
// A hit a raised energy shield took whole, apart from body damage.
constexpr uint32_t ShieldColor = opaqueAbgr(150, 220, 255);

constexpr float HitSeconds = 0.6f;
constexpr float HitFadeSeconds = 0.225f;
constexpr float CriticalSeconds = 1.35f;
constexpr float CriticalFadeSeconds = 0.35f;
// How far a number rises over its life, in plain number cells.
constexpr float RiseCells = 1.0f;

// The room a number takes in its monster's column, in plain number cells (the digits fill about two thirds of a
// cell; the rest is the gap to the next number).
constexpr float StackLineCells = 0.78f;
// How quickly a pushed number reaches its new place (per second, exponential).
constexpr float StackEaseRate = 22.0f;

// A plain number's cell is this share of the screen height (about 37 pixels at 1080p).
constexpr float CellHeightFraction = 0.034f;
constexpr float MinimumCellPixels = 22.0f;
// The dark rim around the digits, as a share of the drawn cell.
constexpr float OutlineFraction = 0.045f;

// A critical hit's pop: it appears faint at plain size, swells to the peak, settles larger than a plain hit and holds
// there before it rises and fades.
constexpr float CriticalPeakScale = 3.2f;
constexpr float CriticalSettledScale = 1.6f;
constexpr float CriticalSwellSeconds = 0.09f;
constexpr float CriticalSettledSeconds = 0.34f;
constexpr float CriticalStartAlpha = 0.35f;

struct Pose
{
    float scale = 1.0f;
    float alpha = 1.0f;
    // 0 at the hit, RiseCells at the top of the rise.
    float riseCells = 0.0f;
};

float easeOutCubic(float t)
{
    const float u = 1.0f - std::clamp(t, 0.0f, 1.0f);
    return 1.0f - u * u * u;
}

float smoothStep(float t)
{
    t = std::clamp(t, 0.0f, 1.0f);
    return t * t * (3.0f - 2.0f * t);
}

Pose poseAt(float ageSeconds, float durationSeconds, bool critical)
{
    Pose pose;

    if (!critical)
    {
        pose.riseCells = RiseCells * std::clamp(ageSeconds / durationSeconds, 0.0f, 1.0f);
        pose.alpha = std::clamp((durationSeconds - ageSeconds) / HitFadeSeconds, 0.0f, 1.0f);
        return pose;
    }

    if (ageSeconds < CriticalSwellSeconds)
    {
        const float t = ageSeconds / CriticalSwellSeconds;
        pose.scale = 1.0f + (CriticalPeakScale - 1.0f) * easeOutCubic(t);
        pose.alpha = CriticalStartAlpha + (1.0f - CriticalStartAlpha) * t;
    }
    else if (ageSeconds < CriticalSettledSeconds)
    {
        const float t = (ageSeconds - CriticalSwellSeconds) / (CriticalSettledSeconds - CriticalSwellSeconds);
        pose.scale = CriticalPeakScale + (CriticalSettledScale - CriticalPeakScale) * smoothStep(t);
    }
    else
    {
        pose.scale = CriticalSettledScale;
    }

    pose.riseCells = RiseCells * std::clamp(
        (ageSeconds - CriticalSettledSeconds) / (durationSeconds - CriticalSettledSeconds), 0.0f, 1.0f);
    pose.alpha *= std::clamp((durationSeconds - ageSeconds) / CriticalFadeSeconds, 0.0f, 1.0f);
    return pose;
}

// A number's room in its column: a critical hit's settled size (its pop may briefly cover its neighbours).
float stackHeightCells(bool critical)
{
    return StackLineCells * (critical ? CriticalSettledScale : 1.0f);
}
}

void CombatFloatingText::preload(const GameplayScreenRuntime &screenRuntime)
{
    screenRuntime.findHudFont(GameplayUiSkin::CombatNumberFontName);
}

void CombatFloatingText::clear()
{
    m_entries.clear();
}

void CombatFloatingText::update(float deltaSeconds, const std::vector<GameplayCombatFeedbackEvent> &events,
    size_t actorCount, bool enabled)
{
    if (!enabled)
    {
        m_entries.clear();
        return;
    }

    const float elapsedSeconds = std::max(0.0f, deltaSeconds);

    for (Entry &entry : m_entries)
    {
        entry.ageSeconds += elapsedSeconds;
    }

    std::erase_if(m_entries,
        [](const Entry &entry)
        {
            return entry.ageSeconds >= entry.durationSeconds;
        });

    const size_t firstNew = m_entries.size();

    for (const GameplayCombatFeedbackEvent &event : events)
    {
        const int amount = event.damage > 0 ? event.damage : event.shieldDamage;

        if (event.actorIndex >= actorCount || amount <= 0)
        {
            continue;
        }

        m_entries.push_back(Entry{
            .actorIndex = event.actorIndex,
            .text = std::to_string(amount),
            .origin = {event.x, event.y, GameplayUiSkin::combatDamageTextOriginZ(event.z, event.height)},
            .ageSeconds = 0.0f,
            .durationSeconds = event.critical ? CriticalSeconds : HitSeconds,
            .colorAbgr = event.damage > 0 ? DamageColor : ShieldColor,
            .critical = event.critical,
        });
    }

    // Each monster's column, newest first: a number sits at its own rise, or just above the next newer one when
    // that is higher. New numbers take their place at once; older ones glide to theirs.
    struct ColumnTop
    {
        size_t actorIndex = 0;
        float liftCells = 0.0f;
        float heightCells = 0.0f;
    };
    std::vector<ColumnTop> columns;
    const float ease = 1.0f - std::exp(-StackEaseRate * elapsedSeconds);

    for (size_t index = m_entries.size(); index-- > 0;)
    {
        Entry &entry = m_entries[index];
        const float heightCells = stackHeightCells(entry.critical);
        float targetCells = poseAt(entry.ageSeconds, entry.durationSeconds, entry.critical).riseCells;
        const auto column = std::find_if(columns.begin(), columns.end(),
            [&entry](const ColumnTop &top)
            {
                return top.actorIndex == entry.actorIndex;
            });

        if (column != columns.end())
        {
            targetCells = std::max(targetCells, column->liftCells + (column->heightCells + heightCells) * 0.5f);
        }

        entry.liftCells = index >= firstNew ? targetCells : entry.liftCells + (targetCells - entry.liftCells) * ease;
        const ColumnTop top{entry.actorIndex, targetCells, heightCells};

        if (column != columns.end())
        {
            *column = top;
        }
        else
        {
            columns.push_back(top);
        }
    }
}

void CombatFloatingText::render(const GameplayScreenRuntime &screenRuntime, int width, int height,
    const ProjectWorldPoint &project) const
{
    if (m_entries.empty() || width <= 0 || height <= 0)
    {
        return;
    }

    const std::optional<GameplayHudFontHandle> font =
        screenRuntime.findHudFont(GameplayUiSkin::CombatNumberFontName);

    if (!font || font->fontHeight <= 0)
    {
        return;
    }

    constexpr std::array<std::array<float, 2>, 8> OutlineDirections = {{
        {-1.0f, 0.0f}, {1.0f, 0.0f}, {0.0f, -1.0f}, {0.0f, 1.0f},
        {-0.7f, -0.7f}, {0.7f, -0.7f}, {-0.7f, 0.7f}, {0.7f, 0.7f},
    }};
    const float cellHeight = std::max(MinimumCellPixels, float(height) * CellHeightFraction);

    // Plain hits first, so a critical hit's number lies over them.
    for (const bool critical : {false, true})
    {
        for (const Entry &entry : m_entries)
        {
            if (entry.critical != critical)
            {
                continue;
            }

            const Pose pose = poseAt(entry.ageSeconds, entry.durationSeconds, entry.critical);
            float screenX = 0.0f;
            float screenY = 0.0f;

            if (pose.alpha <= 0.0f || !project(entry.origin, screenX, screenY))
            {
                continue;
            }

            const float drawnHeight = cellHeight * pose.scale;
            const float fontScale = drawnHeight / float(font->fontHeight);
            const float textX = screenX - screenRuntime.measureHudTextWidth(*font, entry.text) * fontScale * 0.5f;
            const float textY = screenY - entry.liftCells * cellHeight - drawnHeight * 0.5f;
            const uint32_t alphaBits = uint32_t(std::lround(255.0f * pose.alpha)) << 24;
            const float outline = std::max(1.0f, drawnHeight * OutlineFraction);
            const GameplayHudFontLayer outlineLayer(font->shadowTextureHandle, 0x00ffffffu | alphaBits);

            for (const std::array<float, 2> &direction : OutlineDirections)
            {
                screenRuntime.renderHudFontLayer(*font, outlineLayer, entry.text,
                    textX + direction[0] * outline, textY + direction[1] * outline, fontScale);
            }

            screenRuntime.renderHudFontLayer(*font,
                screenRuntime.hudFontMainLayer(*font, (entry.colorAbgr & 0x00ffffffu) | alphaBits),
                entry.text, textX, textY, fontScale);
        }
    }
}
}
