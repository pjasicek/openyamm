#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
struct MapDeltaDoor;

// How far a door stands from its open pose: 0 when open, its move length when closed, in between while it moves.
// In its own file, with EventRuntime::calculateMechanismDistance, so that code which only needs a door's pose
// (movement, collision, tools) links without the event runtime.
float mechanismDistanceForState(const MapDeltaDoor &door, uint16_t state, float timeSinceTriggeredMs);
}
