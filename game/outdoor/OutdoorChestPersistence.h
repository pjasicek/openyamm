#pragma once

#include "game/outdoor/OutdoorWorldRuntime.h"

namespace OpenYAMM::Game
{
// Refill starts with fresh map state. Only explicitly authored storage keeps its saved inventory.
inline void preserveOutdoorStorageChests(
    OutdoorWorldRuntime::Snapshot &freshState,
    const OutdoorWorldRuntime::Snapshot &savedState,
    const std::vector<MapDeltaChest> &definitions)
{
    freshState.materializedChestViews.resize(freshState.chests.size());
    freshState.openedChestFlags.resize(freshState.chests.size());
    for (size_t chestIndex = 0; chestIndex < definitions.size(); ++chestIndex)
    {
        if (!definitions[chestIndex].preserveOnRefill
            || chestIndex >= freshState.chests.size() || chestIndex >= savedState.chests.size())
        {
            continue;
        }

        freshState.chests[chestIndex] = savedState.chests[chestIndex];
        if (chestIndex < savedState.materializedChestViews.size())
        {
            freshState.materializedChestViews[chestIndex] = savedState.materializedChestViews[chestIndex];
        }
        if (chestIndex < savedState.openedChestFlags.size())
        {
            freshState.openedChestFlags[chestIndex] = savedState.openedChestFlags[chestIndex];
        }
    }
}

}
