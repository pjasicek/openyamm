#include "game/maps/MechanismAudioYml.h"

#include <array>
#include <cstdint>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
std::array<std::pair<const char *, std::string MechanismAudioProfile::*>, 9> soundFields()
{
    return {{
        {"open", &MechanismAudioProfile::openSound},
        {"close", &MechanismAudioProfile::closeSound},
        {"open_start", &MechanismAudioProfile::openStartSound},
        {"open_busy", &MechanismAudioProfile::openBusySound},
        {"open_stop", &MechanismAudioProfile::openStopSound},
        {"close_start", &MechanismAudioProfile::closeStartSound},
        {"close_busy", &MechanismAudioProfile::closeBusySound},
        {"close_stop", &MechanismAudioProfile::closeStopSound},
        {"jiggle", &MechanismAudioProfile::jiggleSound},
    }};
}

bool readCoordinate(const YAML::Node &node, const char *key, int32_t &value, std::string &errorMessage)
{
    const YAML::Node child = node[key];

    if (!child || !child.IsScalar())
    {
        errorMessage = std::string("sounds.position needs a scalar ") + key;
        return false;
    }

    try
    {
        value = child.as<int32_t>();
    }
    catch (const YAML::Exception &)
    {
        errorMessage = std::string("sounds.position.") + key + " must be an integer";
        return false;
    }

    return true;
}
}

bool parseMechanismAudioProfile(const YAML::Node &node, MechanismAudioProfile &profile, std::string &errorMessage)
{
    if (!node.IsMap())
    {
        errorMessage = "mechanism sounds must be a map";
        return false;
    }

    for (const auto &[key, field] : soundFields())
    {
        const YAML::Node child = node[key];

        if (!child)
        {
            continue;
        }

        if (!child.IsScalar())
        {
            errorMessage = std::string("mechanism sounds.") + key + " must be a sound name";
            return false;
        }

        profile.*field = child.as<std::string>();
    }

    if (const YAML::Node positionNode = node["position"]; positionNode)
    {
        if (!positionNode.IsMap()
            || !readCoordinate(positionNode, "x", profile.x, errorMessage)
            || !readCoordinate(positionNode, "y", profile.y, errorMessage)
            || !readCoordinate(positionNode, "z", profile.z, errorMessage))
        {
            errorMessage = errorMessage.empty() ? "sounds.position must be a map" : errorMessage;
            return false;
        }

        profile.positional = true;
    }

    return true;
}

void emitMechanismAudioProfile(YAML::Emitter &emitter, const MechanismAudioProfile &profile)
{
    emitter << YAML::BeginMap;

    if (profile.positional)
    {
        emitter << YAML::Key << "position" << YAML::Value << YAML::Flow << YAML::BeginMap
                << YAML::Key << "x" << YAML::Value << profile.x
                << YAML::Key << "y" << YAML::Value << profile.y
                << YAML::Key << "z" << YAML::Value << profile.z << YAML::EndMap;
    }

    for (const auto &[key, field] : soundFields())
    {
        if (!(profile.*field).empty())
        {
            emitter << YAML::Key << key << YAML::Value << profile.*field;
        }
    }

    emitter << YAML::EndMap;
}
}
