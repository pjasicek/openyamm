#include "game/gameplay/PartyHostileAlert.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
// The edge distance of a living, visible hostile actor that has seen the party; none for the others.
std::optional<float> alertingActorDistance(
    const GameplayActorRulesView &actor,
    float partyX,
    float partyY,
    float partyFootZ)
{
    if (actor.isDead || actor.isInvisible || !actor.hostileToParty || !actor.hasDetectedParty)
    {
        return std::nullopt;
    }

    const float deltaX = actor.preciseX - partyX;
    const float deltaY = actor.preciseY - partyY;
    const float deltaZ = actor.preciseZ - partyFootZ;
    const float centerDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    return std::max(0.0f, centerDistance - static_cast<float>(actor.radius));
}

bool partyHasAlertWithin(const IGameplayWorldRuntime &worldRuntime, float distance)
{
    const float partyX = worldRuntime.partyX();
    const float partyY = worldRuntime.partyY();
    const float partyFootZ = worldRuntime.partyFootZ();

    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        // The rules view, not the full runtime state: this pass runs over every actor each frame.
        GameplayActorRulesView actor = {};

        if (worldRuntime.actorRulesView(actorIndex, actor))
        {
            const std::optional<float> edgeDistance = alertingActorDistance(actor, partyX, partyY, partyFootZ);

            if (edgeDistance && *edgeDistance < distance)
            {
                return true;
            }
        }
    }

    return false;
}
}

bool actorRaisesPartyYellowAlert(
    const GameplayActorRulesView &actor,
    float partyX,
    float partyY,
    float partyFootZ)
{
    const std::optional<float> edgeDistance = alertingActorDistance(actor, partyX, partyY, partyFootZ);
    return edgeDistance && *edgeDistance < PartyYellowAlertDistance;
}

bool partyHasYellowAlert(const IGameplayWorldRuntime &worldRuntime)
{
    return partyHasAlertWithin(worldRuntime, PartyYellowAlertDistance);
}

bool partyHasRedAlert(const IGameplayWorldRuntime &worldRuntime)
{
    return partyHasAlertWithin(worldRuntime, PartyRedAlertDistance);
}

float nearestHostileDistanceToParty(const IGameplayWorldRuntime &worldRuntime)
{
    const float partyX = worldRuntime.partyX();
    const float partyY = worldRuntime.partyY();
    const float partyFootZ = worldRuntime.partyFootZ();
    float nearestDistance = std::numeric_limits<float>::max();

    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        // The rules view, not the full runtime state: the HUD scans every actor each frame.
        GameplayActorRulesView actor = {};

        if (!worldRuntime.actorRulesView(actorIndex, actor) || actor.isDead || actor.isInvisible
            || !actor.hostileToParty)
        {
            continue;
        }

        const float deltaX = actor.preciseX - partyX;
        const float deltaY = actor.preciseY - partyY;
        const float deltaZ = actor.preciseZ - partyFootZ;
        const float centerDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
        nearestDistance = std::min(nearestDistance, std::max(0.0f, centerDistance - float(actor.radius)));
    }

    return nearestDistance;
}

bool partyHasGreenAlert(const IGameplayWorldRuntime &worldRuntime)
{
    return nearestHostileDistanceToParty(worldRuntime)
        >= std::min(worldRuntime.partyEngagementRange(), PartyYellowAlertDistance);
}
}
