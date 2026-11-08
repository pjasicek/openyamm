#pragma once

#include "game/maps/MapDeltaData.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
// A map's layout identity (devdocs/SAVED_MAP_STATE_IDENTITY.md): a hash of what its saved state is laid out against,
// computed from the loaded map (MapAssetInfo::layoutIdentity) and recorded with the map's state in a save. Geometry
// (vertex positions, faces with their vertex lists, flags and event cogs, sectors, outlines), doors and movers,
// destructibles, decorations, spawns, outdoor mechanisms and the counts of placed actors, chests and floor items.
// Texture names, lighting, terrain heights, scripts and actor stats are not part of it: changing them keeps saves.
// Never 0, which a save without identities reads as.
uint64_t computeIndoorMapLayoutIdentity(const IndoorMapData &map, const std::optional<MapDeltaData> &initialState);
uint64_t computeOutdoorMapLayoutIdentity(const OutdoorMapData &map, const std::optional<MapDeltaData> &initialState);

enum class SavedMapStateVerdict
{
    Keep,
    // Saved against another layout of the map: its state is reset.
    ResetChanged,
    // A save from before identities (version 160) of a map whose world rebuilds its maps: its state is reset.
    ResetUnknown,
};

// What happens to a map's saved state when the map is entered. A state without identity (savedIdentity 0, saves
// before version 160) is kept for the native MM6-MM8 worlds, whose maps are the original games' and did not change,
// and reset for every other world (MM9 and newer), whose maps were rebuilt since.
SavedMapStateVerdict judgeSavedMapState(uint64_t savedIdentity, uint64_t currentIdentity, const std::string &worldId);
}
