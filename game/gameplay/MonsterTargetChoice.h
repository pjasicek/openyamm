#pragma once

#include "game/gameplay/PlayerId.h"

#include <limits>
#include <optional>
#include <span>

namespace OpenYAMM::Game
{
// One player's party as a monster weighs it when it picks whom to fight (a co-op host's game).
struct MonsterTargetCandidate
{
    PlayerId player = LocalPlayer;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    bool canAct = true;
    bool invisible = false;
};

// For how long the player who last hurt a monster is the one it fights, in game minutes (six seconds of play).
constexpr float MonsterThreatGameMinutes = 3.0f;

// Whom a monster at (x, y, z) fights among several players' parties:
// - only a party that can act, and not an invisible one while a visible one stands (an invisible nearest player
//   would otherwise switch the monster off for everyone);
// - whoever last hurt it, while `threat` names that player;
// - else the nearest, in three dimensions (a player on the floor above is not near), keeping its present target
//   until another is clearly nearer (a quarter), so that two players at a like distance do not pass it to and fro.
// LocalPlayer when no party fits, as in a game of one.
inline PlayerId chooseMonsterTarget(
    float x,
    float y,
    float z,
    PlayerId current,
    std::optional<PlayerId> threat,
    std::span<const MonsterTargetCandidate> candidates)
{
    bool anyVisible = false;

    for (const MonsterTargetCandidate &candidate : candidates)
    {
        anyVisible = anyVisible || (candidate.canAct && !candidate.invisible);
    }

    constexpr float KeepFactorSquared = 1.25f * 1.25f;
    std::optional<PlayerId> nearest;
    float nearestSquared = std::numeric_limits<float>::max();
    std::optional<float> currentSquared;

    for (const MonsterTargetCandidate &candidate : candidates)
    {
        if (!candidate.canAct || (candidate.invisible && anyVisible))
        {
            continue;
        }

        if (threat && candidate.player == *threat)
        {
            return candidate.player;
        }

        const float deltaX = candidate.x - x;
        const float deltaY = candidate.y - y;
        const float deltaZ = candidate.z - z;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

        if (candidate.player == current)
        {
            currentSquared = distanceSquared;
        }

        if (distanceSquared < nearestSquared)
        {
            nearestSquared = distanceSquared;
            nearest = candidate.player;
        }
    }

    if (!nearest)
    {
        return LocalPlayer;
    }

    return currentSquared && *currentSquared <= nearestSquared * KeepFactorSquared ? current : *nearest;
}
}
