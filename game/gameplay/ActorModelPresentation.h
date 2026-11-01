#pragma once

#include <algorithm>
#include <array>
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

// The distance a gait advances by this frame: what the body travelled, kept between what the clip covers at minRate
// and at maxRate (0: no cap) times its authored rate. By default the clip follows the distance exactly, so feet do not
// slide (unless collision hinders the body: actorModelGaitSpeed): a clip that scurries or crawls at the game's speed is
// fixed in the clip (stride), not by capping its rate.
// actors.yml `animation.gait_rate: [min, max]` sets the range for bodies without foot contact: fliers and swimmers
// keep beating at a minimum rate when they drift slowly.
inline float actorModelGaitDistance(float distance, float cycleDistance, float deltaSeconds, float clipSeconds,
    float minRate = 0.0f, float maxRate = 0.0f)
{
    if (!(clipSeconds > 0.0f))
    {
        return distance;
    }
    const float authoredDistance = cycleDistance * std::max(deltaSeconds, 0.0f) / clipSeconds;
    const float atMost = maxRate > 0.0f ? std::min(distance, authoredDistance * maxRate) : distance;
    return std::max(atMost, authoredDistance * minRate);
}

// The share of the speed its AI asked for that a moving 3D actor's gait keeps while a wall, slope or crowd slows its
// body: the feet slip a little as it pushes, instead of the clip crawling in slow motion or freezing head-on.
inline constexpr float ActorModelHinderedGaitShare = 0.6f;

// The speed a moving 3D actor's gait presents: what its body moves at, or ActorModelHinderedGaitShare of the speed its
// AI asked for (0 when it is not trying to move) when collision slows it more than that.
inline float actorModelGaitSpeed(float speed, float intendedSpeed)
{
    return std::max(speed, ActorModelHinderedGaitShare * intendedSpeed);
}

// Whether a walking 3D actor faces where it actually moves instead of the AI's yaw: one sliding along a wall turns
// along it, as MM's actors do, rather than stepping sideways while facing the wall. Moving against its yaw (backing
// away) it keeps the AI's yaw and plays its gait backwards. facingMovement, the current choice, holds across the same
// margin as the backwards gait so neither flickers.
inline bool actorModelFacesMovement(float aiYaw, float velocityX, float velocityY, bool facingMovement)
{
    const float speed = std::hypot(velocityX, velocityY);
    return speed > 0.0f
        && velocityX * std::cos(aiYaw) + velocityY * std::sin(aiYaw) >= (facingMovement ? -0.35f : -0.15f) * speed;
}

// How badly a locomotion clip authored for clipSpeed suits a body moving at speed: the log of the rate it would play at,
// doubled when that is slower than authored, since a crawling run reads worse than a quick walk.
inline float actorModelGaitMisfit(float speed, float clipSpeed)
{
    const float rate = std::log(speed / clipSpeed);
    return rate >= 0.0f ? rate : -2.0f * rate;
}

// Locomotion clips of a 3D actor: its walk, its run and an optional sprint (actors.yml `sprint`), each authored for a
// speed (its stride over its length).
enum class ActorModelGait : uint8_t
{
    Walk,
    Run,
    Sprint
};

// Highest playback rate of a locomotion clip over its authored speed, unless its binding's `gait_rate` sets another
// (max 0: uncapped). Faster bodies slide their feet a little rather than pedalling: people and animals go faster mostly
// by longer strides, so a clip far above its rate reads as frantic skipping. A body meant to go much faster needs a
// longer-strided clip (its sprint), not a quicker one.
inline constexpr float ActorModelDefaultMaxGaitRate = 2.0f;

// The locomotion clip that suits a moving 3D actor's speed best (actorModelGaitMisfit), with a small preference from
// what the AI is doing (hurrying, pursuing or fleeing at its doubled speed: run or sprint; wandering: walk). So a chaser
// whose run would play in slow motion walks, a small fast wanderer trots instead of scurrying, and a chaser too fast
// for its run sprints. The clip playing now keeps an 8 % margin, so a speed near a boundary does not flicker. Speeds
// are in model units per second; clipSpeeds are walk, run and sprint (0: the model has no such clip).
inline ActorModelGait actorModelGait(float speed, const std::array<float, 3> &clipSpeeds, bool hurrying,
    ActorModelGait current)
{
    if (!(speed > 0.0f) || !(clipSpeeds[0] > 0.0f) || !(clipSpeeds[1] > 0.0f))
    {
        return hurrying ? ActorModelGait::Run : ActorModelGait::Walk;
    }
    const float preference = std::log(1.25f);
    const float hold = std::log(1.08f);
    ActorModelGait best = ActorModelGait::Walk;
    float bestMisfit = 0.0f;
    for (size_t index = 0; index < clipSpeeds.size(); ++index)
    {
        if (!(clipSpeeds[index] > 0.0f))
        {
            continue;
        }
        const ActorModelGait gait = ActorModelGait(index);
        const bool suitsHurry = (gait != ActorModelGait::Walk) == hurrying;
        const float misfit = actorModelGaitMisfit(speed, clipSpeeds[index]) - (suitsHurry ? preference : 0.0f)
            - (gait == current ? hold : 0.0f);
        if (index == 0 || misfit < bestMisfit)
        {
            best = gait;
            bestMisfit = misfit;
        }
    }
    return best;
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
