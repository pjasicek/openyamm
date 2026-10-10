#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iterator>
#include <numbers>

namespace OpenYAMM::Game
{
inline float advanceActorModelYaw(float current, float target, float deltaSeconds, float radiansPerSecond)
{
    const float difference = std::remainder(target - current, 2.0f * std::numbers::pi_v<float>);
    const float step = std::max(0.0f, deltaSeconds) * radiansPerSecond;
    return current + std::clamp(difference, -step, step);
}

inline float advanceActorModelGait(float phase, float distance, float cycleDistance)
{
    return std::fmod(phase + distance / cycleDistance, 1.0f);
}

// Loot satchel tier (1-6) for a corpse holding this much gold plus item value; 0 (no satchel) for an empty corpse.
// Rolled MM6-MM8 monster loot: about a fifth of corpses hold nothing, the median holds 25, the 90th percentile 830 and
// the 99th 5,000, so most satchels are small purses. Tier 5 (8,000+) is a rich hoard with a fine item or an artifact;
// tier 6 (15,000+) is reached only with an artifact or relic.
inline uint32_t corpseSatchelTier(uint32_t lootValue)
{
    constexpr uint32_t Bounds[] = {1, 100, 750, 3000, 8000, 15000};
    uint32_t tier = 0;
    while (tier < std::size(Bounds) && lootValue >= Bounds[tier])
    {
        ++tier;
    }
    return tier;
}

constexpr float CorpseRestSeconds = 0.1f;
constexpr float CorpseSinkSeconds = 0.9f;
constexpr float CorpseSatchelAppearSeconds = 0.35f;

// A slain creature's body once it has come to rest: almost at once it dissolves while sinking into the ground, and its
// loot satchel fades in at the same moment with a small overshoot.
struct CorpseSinkPresentation
{
    // Of the body's height, sunk below its resting place.
    float depthFraction = 0.0f;
    // Fraction of the body's pixels still drawn.
    float coverage = 1.0f;
    bool gone = false;
    float satchelCoverage = 0.0f;
    float satchelScale = 0.0f;
};

inline CorpseSinkPresentation corpseSinkPresentation(float secondsAtRest)
{
    CorpseSinkPresentation result;
    const float sink = std::clamp((secondsAtRest - CorpseRestSeconds) / CorpseSinkSeconds, 0.0f, 1.0f);
    const float dissolve = std::min(sink / 0.85f, 1.0f);
    result.depthFraction = sink * sink * (3.0f - 2.0f * sink);
    result.coverage = 1.0f - dissolve * dissolve * (3.0f - 2.0f * dissolve);
    result.gone = sink >= 1.0f;
    const float appear = std::clamp((secondsAtRest - CorpseRestSeconds) / CorpseSatchelAppearSeconds, 0.0f, 1.0f);
    result.satchelCoverage = appear;
    result.satchelScale = 0.75f + 0.25f * appear + 0.12f * std::sin(std::numbers::pi_v<float> * appear);
    return result;
}
}
