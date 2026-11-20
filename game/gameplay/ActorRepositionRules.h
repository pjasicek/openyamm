#pragma once

#include "game/gameplay/GameplayActorAiTypes.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>

namespace OpenYAMM::Game
{
// The reposition modifier's rules (RepositionModifier, devdocs/MONSTER_MODIFIERS.md; an OpenYAMM addition to MM9's
// ranged holders, devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "Repositioning casters") as pure functions. The AI
// (GameplayActorAiSystem) picks the candidate spots and when to look; the world only tests the spots it is given
// (ActorRepositionQuery) and answers in ActorMm9WorldFacts. Distances are ours, times seconds.

// A spot this close to where it stands is no move; it has arrived within this of a spot.
inline constexpr float RepositionMinimumMove = 96.0f;
inline constexpr float RepositionArrivalDistance = 8.0f;
// A query the world has not answered after this long is dropped (the actor left the world's active set).
inline constexpr float RepositionQueryTimeoutSeconds = 0.5f;
// A back-off direction is straight away from the target, else turned this far to either side, then twice as far.
inline constexpr float RepositionBackOffTurnRadians = 0.5235988f;
// A back-off spot must end at least this share of the back-off farther from the target than where it starts.
inline constexpr float RepositionBackOffMinGainShare = 0.5f;

inline float repositionDistance2d(const GameplayWorldPoint &from, const GameplayWorldPoint &to)
{
    return std::hypot(to.x - from.x, to.y - from.y);
}

// The point pulled inside the leash circle of radius leash around post (unchanged within it).
inline GameplayWorldPoint repositionWithinLeash(const GameplayWorldPoint &point, const GameplayWorldPoint &post,
    float leash)
{
    const float distance = repositionDistance2d(post, point);

    if (distance <= leash || distance <= 0.0f)
    {
        return point;
    }

    const float share = leash / distance;
    return {post.x + (point.x - post.x) * share, post.y + (point.y - post.y) * share, point.z};
}

// It has seen nothing of its target for long enough to look for a spot.
inline bool repositionLostSight(const RepositionModifier &settings, float unseenSeconds)
{
    return unseenSeconds >= settings.lostSightSeconds;
}

// How fast the target closes on the actor: its velocity along the line from it to the actor (negative: moving away).
inline float repositionClosingSpeed(const GameplayWorldPoint &actor, const GameplayWorldPoint &target,
    float targetVelocityX, float targetVelocityY)
{
    const float distance = repositionDistance2d(target, actor);

    if (distance <= 0.01f)
    {
        return 0.0f;
    }

    return (targetVelocityX * (actor.x - target.x) + targetVelocityY * (actor.y - target.y)) / distance;
}

// The target rushes it: outside its reach, within the trigger distance (edge to edge), closing fast enough.
inline bool repositionRushed(const RepositionModifier &settings, float edgeDistance, float attackReach,
    float closingSpeed)
{
    return edgeDistance > attackReach && edgeDistance <= settings.backOffTriggerDistance
        && closingSpeed > 0.0f && closingSpeed >= settings.backOffClosingSpeed;
}

// The spots a search tries, in order: settings.candidates points around `from`, alternately on the ring of half and
// of all its search distance, at bearings spread evenly round the circle and turned by unit (a seeded roll in
// [0, 1)); each is pulled inside the leash around post, one that ends nearer than RepositionMinimumMove to `from` is
// dropped, and the rest are ordered nearest first (the shortest move that sees wins). Returns how many it wrote.
inline size_t repositionCandidates(const GameplayWorldPoint &from, const GameplayWorldPoint &post,
    const RepositionModifier &settings, float unit, std::array<GameplayWorldPoint, ActorRepositionMaxCandidates> &out)
{
    constexpr float TwoPi = 6.2831853f;
    const size_t count = std::min(size_t(std::max(settings.candidates, 0)), ActorRepositionMaxCandidates);
    size_t written = 0;

    for (size_t index = 0; index < count; ++index)
    {
        const float radius = (index % 2 == 0 ? 0.5f : 1.0f) * settings.searchDistance;
        const float bearing = (unit + float(index) / float(count)) * TwoPi;
        const GameplayWorldPoint ring = {from.x + std::cos(bearing) * radius, from.y + std::sin(bearing) * radius,
            from.z};
        const GameplayWorldPoint spot = repositionWithinLeash(ring, post, settings.leashRadius);

        if (repositionDistance2d(from, spot) >= RepositionMinimumMove)
        {
            out[written++] = spot;
        }
    }

    std::stable_sort(out.begin(), out.begin() + std::ptrdiff_t(written),
        [&from](const GameplayWorldPoint &left, const GameplayWorldPoint &right)
        {
            return repositionDistance2d(from, left) < repositionDistance2d(from, right);
        });
    return written;
}

// The spots a back-off tries, in order: settings.backOffDistance straight away from the target, then turned 30 and 60
// degrees to either side (side first by sideSign), each pulled inside the leash around post; a spot that would not
// take it at least half the back-off farther from the target is dropped. Returns how many it wrote.
inline size_t repositionBackOffCandidates(const GameplayWorldPoint &from, const GameplayWorldPoint &target,
    const GameplayWorldPoint &post, const RepositionModifier &settings, float sideSign,
    std::array<GameplayWorldPoint, ActorRepositionMaxCandidates> &out)
{
    const float away = std::atan2(from.y - target.y, from.x - target.x);
    const float side = sideSign < 0.0f ? -1.0f : 1.0f;
    const float turns[] = {0.0f, side, -side, 2.0f * side, -2.0f * side};
    const float startDistance = repositionDistance2d(target, from);
    size_t written = 0;

    for (const float turn : turns)
    {
        const float bearing = away + turn * RepositionBackOffTurnRadians;
        const GameplayWorldPoint step = {from.x + std::cos(bearing) * settings.backOffDistance,
            from.y + std::sin(bearing) * settings.backOffDistance, from.z};
        const GameplayWorldPoint spot = repositionWithinLeash(step, post, settings.leashRadius);

        if (repositionDistance2d(target, spot)
            >= startDistance + RepositionBackOffMinGainShare * settings.backOffDistance)
        {
            out[written++] = spot;
        }
    }

    return written;
}

// The longest a walk to a spot may take before it gives up on it: twice the walk at its pace, and a second.
inline float repositionWalkLimitSeconds(float distance, float speed)
{
    return 2.0f * distance / std::max(speed, 1.0f) + 1.0f;
}
}
