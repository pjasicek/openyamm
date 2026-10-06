#pragma once

#include <algorithm>
#include <cmath>
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
}
