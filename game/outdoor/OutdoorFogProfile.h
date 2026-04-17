#pragma once

#include <algorithm>
#include <cstdint>

namespace OpenYAMM::Game
{
struct OutdoorFogProfile
{
    float nearOpacity = 0.0f;
    float strongOpacity = 0.0f;
    float weakDistance = 0.0f;
    float strongDistance = 1.0f;
    float farDistance = 2.0f;
};

inline OutdoorFogProfile buildOutdoorFogProfile(
    int32_t authoredWeakDistance,
    int32_t authoredStrongDistance,
    float visibleDistance,
    float nearOpacity,
    float strongOpacity)
{
    constexpr float FogLeadFraction = 0.35f;
    constexpr float FogStrongStretchFraction = 0.20f;
    constexpr float FogTailFraction = 1.50f;

    const float weakDistance = std::max(static_cast<float>(authoredWeakDistance), 0.0f);
    const float strongDistance = std::max(static_cast<float>(authoredStrongDistance), weakDistance + 1.0f);
    const float distanceSpan = std::max(strongDistance - weakDistance, 1.0f);
    const float clampedVisibleDistance = std::max(visibleDistance, strongDistance + 1.0f);
    const float softenedWeakDistance = std::max(weakDistance - distanceSpan * FogLeadFraction, 0.0f);
    const float softenedStrongDistance =
        std::max(strongDistance + distanceSpan * FogStrongStretchFraction, softenedWeakDistance + 1.0f);
    const float softenedFarDistance =
        std::max(clampedVisibleDistance + distanceSpan * FogTailFraction, softenedStrongDistance + 1.0f);

    OutdoorFogProfile profile = {};
    profile.nearOpacity = std::clamp(nearOpacity, 0.0f, 1.0f);
    profile.strongOpacity = std::clamp(strongOpacity, profile.nearOpacity, 1.0f);
    profile.weakDistance = softenedWeakDistance;
    profile.strongDistance = softenedStrongDistance;
    profile.farDistance = softenedFarDistance;
    return profile;
}
} // namespace OpenYAMM::Game
