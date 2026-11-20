#include "game/maps/SceneOverlayOperations.h"

namespace OpenYAMM::Game
{
bool readSceneRemovalPosition(const YAML::Node &node, int &x, int &y, int &z, std::string &errorMessage)
{
    const YAML::Node position = node.IsMap() ? node["position"] : YAML::Node();

    if (!position || !position.IsSequence() || position.size() != 3)
    {
        errorMessage = "a removal needs position: [x, y, z]";
        return false;
    }

    x = position[0].as<int>();
    y = position[1].as<int>();
    z = position[2].as<int>();
    return true;
}

bool applySceneActorOverrides(const YAML::Node &node, std::vector<MapDeltaActor> &actors, std::string &errorMessage)
{
    if (!node.IsSequence())
    {
        errorMessage = "initial_state.actor_overrides must be a sequence";
        return false;
    }

    try
    {
        for (const YAML::Node &entry : node)
        {
            const size_t actorIndex = entry["actor_index"] ? entry["actor_index"].as<size_t>() : actors.size();

            if (actorIndex >= actors.size())
            {
                errorMessage = "actor override actor_index is out of range";
                return false;
            }

            MapDeltaActor &actor = actors[actorIndex];

            if (entry["unique_name_index"])
            {
                actor.uniqueNameIndex = entry["unique_name_index"].as<int32_t>();
            }

            if (entry["hp"])
            {
                actor.hp = entry["hp"].as<int32_t>();
            }

            if (entry["move_speed"])
            {
                actor.moveSpeed = entry["move_speed"].as<uint16_t>();
            }

            if (entry["radius"])
            {
                actor.radius = entry["radius"].as<uint16_t>();
            }

            if (entry["carried_item_id"])
            {
                actor.carriedItemId = entry["carried_item_id"].as<uint32_t>();
            }

            if (entry["clear_attributes"])
            {
                actor.attributes &= ~entry["clear_attributes"].as<uint32_t>();
            }

            if (entry["position"])
            {
                int x = 0;
                int y = 0;
                int z = 0;

                if (!readSceneRemovalPosition(entry, x, y, z, errorMessage))
                {
                    return false;
                }

                actor.x = x;
                actor.y = y;
                actor.z = z;
            }
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("actor override: ") + exception.what();
        return false;
    }

    return true;
}
}
