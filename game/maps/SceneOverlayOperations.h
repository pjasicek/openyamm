#pragma once

#include "game/maps/MapDeltaData.h"

#include <yaml-cpp/yaml.h>

#include <cmath>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// Scene overlay operations shared by outdoor and indoor overlays (rulesets that edit a map without copying it).

// initial_state.actor_overrides: per actor index, any of unique_name_index, hp, move_speed, radius, carried_item_id,
// position {x, y, z} and clear_attributes (bits removed).
bool applySceneActorOverrides(const YAML::Node &node, std::vector<MapDeltaActor> &actors, std::string &errorMessage);

// The position [x, y, z] of a removal entry.
bool readSceneRemovalPosition(const YAML::Node &node, int &x, int &y, int &z, std::string &errorMessage);

// removals.spawns: each entry's position (and index, when given) disables the spawn point there (type 0, which no
// world places), so the other spawn indices stay as they were.
template <typename SceneSpawn>
bool applySceneSpawnRemovals(const YAML::Node &node, std::vector<SceneSpawn> &spawns, std::string &errorMessage)
{
    if (!node.IsSequence())
    {
        errorMessage = "removals.spawns must be a sequence";
        return false;
    }

    for (const YAML::Node &entry : node)
    {
        int x = 0;
        int y = 0;
        int z = 0;

        if (!readSceneRemovalPosition(entry, x, y, z, errorMessage))
        {
            return false;
        }

        const int index = entry["index"] ? entry["index"].as<int>() : -1;
        bool found = false;

        for (SceneSpawn &spawn : spawns)
        {
            if (spawn.spawn.typeId != 0 && std::abs(spawn.spawn.x - x) <= 1 && std::abs(spawn.spawn.y - y) <= 1
                && std::abs(spawn.spawn.z - z) <= 1 && (index < 0 || spawn.spawn.index == index))
            {
                spawn.spawn.typeId = 0;
                found = true;
                break;
            }
        }

        if (!found)
        {
            errorMessage = "spawn removal matches no spawn at " + std::to_string(x) + ", " + std::to_string(y) + ", "
                + std::to_string(z);
            return false;
        }
    }

    return true;
}
}
