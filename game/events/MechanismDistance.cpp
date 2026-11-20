#include "game/events/MechanismDistance.h"

#include "game/events/EventRuntime.h"

#include <algorithm>

namespace OpenYAMM::Game
{
float mechanismDistanceForState(const MapDeltaDoor &door, uint16_t state, float timeSinceTriggeredMs)
{
    if (state == static_cast<uint16_t>(EvtMechanismState::Open))
    {
        return 0.0f;
    }

    const float elapsedMilliseconds = static_cast<float>(timeSinceTriggeredMs);

    if (state == static_cast<uint16_t>(EvtMechanismState::Closing))
    {
        const float closingDistance = elapsedMilliseconds * static_cast<float>(door.closeSpeed) / 1000.0f;
        return std::min(closingDistance, static_cast<float>(door.moveLength));
    }

    if (state == static_cast<uint16_t>(EvtMechanismState::Opening))
    {
        const float openingDistance = elapsedMilliseconds * static_cast<float>(door.openSpeed) / 1000.0f;
        return std::max(0.0f, static_cast<float>(door.moveLength) - openingDistance);
    }

    if (state == static_cast<uint16_t>(EvtMechanismState::Closed) || (door.attributes & 0x2) != 0)
    {
        return static_cast<float>(door.moveLength);
    }

    return 0.0f;
}

float EventRuntime::calculateMechanismDistance(
    const MapDeltaDoor &door,
    const RuntimeMechanismState &runtimeMechanism
)
{
    return mechanismDistanceForState(door, runtimeMechanism.state, runtimeMechanism.timeSinceTriggeredMs);
}
}
