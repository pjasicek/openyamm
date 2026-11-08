#pragma once

#include "game/mm9/Mm9QuestMarkers.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string_view>

namespace OpenYAMM::Game
{
inline std::string_view questMarkerTextureName(Mm9QuestMarkerState state)
{
    if (state == Mm9QuestMarkerState::Available)
    {
        return "quest_marker_exclamation";
    }

    if (state == Mm9QuestMarkerState::InProgress || state == Mm9QuestMarkerState::Ready)
    {
        return "quest_marker_question";
    }

    if (state == Mm9QuestMarkerState::Trainer)
    {
        return "trainer_marker_book";
    }

    return {};
}

inline uint32_t questMarkerColorAbgr(Mm9QuestMarkerState state, uint8_t alpha)
{
    // Gold for quest work to do, grey for a quest still under way, and the interface's learnable-skill blue
    // (GameplayUiSkin::Learnable) for a trainer.
    uint8_t red = 245;
    uint8_t green = 194;
    uint8_t blue = 48;
    if (state == Mm9QuestMarkerState::InProgress)
    {
        red = 174;
        green = 182;
        blue = 190;
    }
    else if (state == Mm9QuestMarkerState::Trainer)
    {
        red = 142;
        green = 188;
        blue = 250;
    }
    return static_cast<uint32_t>(red) | (static_cast<uint32_t>(green) << 8) | (static_cast<uint32_t>(blue) << 16) |
           (static_cast<uint32_t>(alpha) << 24);
}

inline uint8_t questMarkerAlpha(float distance)
{
    constexpr float FadeBegin = 3500.0f;
    constexpr float HideDistance = 5500.0f;
    if (distance >= HideDistance)
    {
        return 0;
    }
    const float opacity = distance <= FadeBegin ? 1.0f : (HideDistance - distance) / (HideDistance - FadeBegin);
    return static_cast<uint8_t>(std::clamp(std::lround(opacity * 255.0f), 0l, 255l));
}

inline float questMarkerWorldScale(float distance)
{
    return std::clamp(42.0f + distance * 0.012f, 42.0f, 92.0f);
}

inline float questMarkerHalfExtent(float scale)
{
    return scale * 0.6f;
}

inline float questMarkerOriginOffset(float scale)
{
    // Both glyphs extend about 0.55 scale units below their origin. Keep that bottom edge just above the sprite.
    return scale * 0.55f + 6.0f;
}
} // namespace OpenYAMM::Game
