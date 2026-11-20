#pragma once

#include "core/Coplanar.h"

#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapDeltaData.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// The party's eye stands this far over the floor it stands on (game/indoor/IndoorMovementController.h: the party's
// body is 160 high and its eye is at the top of it).
constexpr double PartyEyeHeight = 160.0;

// A walkable top where the party's eye lies in another sector's space than the one the game draws from: the game
// takes the eye's sector from the floors under the eye (game/indoor findIndoorSectorForPoint; on arrival, the
// floor's own sector), and draws the map through the portals of that sector, so walls round the eye that belong to
// the sector the eye really is in are not drawn and the view is black (the Abandoned Temple's box top under the
// lantern, 2026-11-13).
struct EyeSectorFinding
{
    // The floor face stood on, the point on it and how many of the face's sample points have the fault.
    uint32_t face = 0;
    std::array<double, 3> foot = {};
    size_t points = 0;
    size_t sampled = 0;
    // The floor face's sector, the sector whose space the eye is in (by rays from the eye: the sector whose faces
    // most of them meet first, from that sector's side), the sector the game draws from after a step (the one it
    // finds for the eye) and the one it draws from when the party arrives or is put there (its placement's).
    int floorSector = 0;
    int eyeSector = 0;
    int drawnSector = 0;
    int arrivalSector = 0;
};

// Every walkable top (a floor face, its slope walkable, with room for the party over it) of the map as it starts,
// sampled at its middle and on a grid of 192, where the eye's sector by rays is not the one the game draws from.
std::vector<EyeSectorFinding> findEyeOutsideSector(const Game::IndoorMapData &map, const Game::MapDeltaData *pState);

// One sentence: the face (texture, room, moving part), the point, the two sectors, and what to do.
std::string describeEyeSectorFinding(
    const Game::IndoorMapData &map,
    const Game::MapDeltaData *pState,
    const EyeSectorFinding &finding,
    const CoplanarNames &names);
}
