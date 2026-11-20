#include "game/maps/MistYml.h"

#include <yaml-cpp/yaml.h>

#include <cmath>
#include <exception>
#include <initializer_list>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
bool checkKeys(const YAML::Node &node, const std::string &prefix, std::initializer_list<std::string_view> known,
    std::string &errorMessage)
{
    if (!node.IsMap())
    {
        errorMessage = prefix + " must be a map";
        return false;
    }

    for (const auto &entry : node)
    {
        const std::string key = entry.first.as<std::string>();
        bool found = false;
        for (const std::string_view candidate : known)
        {
            found = found || key == candidate;
        }
        if (!found)
        {
            errorMessage = prefix + " has an unknown key " + key;
            return false;
        }
    }

    return true;
}

bool readColor(const YAML::Node &node, const std::string &prefix, std::array<float, 3> &color,
    std::string &errorMessage)
{
    const YAML::Node colorNode = node["color_rgb"];
    if (!colorNode || !colorNode.IsSequence() || colorNode.size() != 3)
    {
        errorMessage = prefix + " requires color_rgb (three numbers 0..255)";
        return false;
    }

    for (size_t channel = 0; channel < 3; ++channel)
    {
        const float value = colorNode[channel].as<float>();
        if (!(value >= 0.0f && value <= 255.0f))
        {
            errorMessage = prefix + " color_rgb must be within 0..255";
            return false;
        }
        color[channel] = value / 255.0f;
    }

    return true;
}

// An optional number that must be finite and inside [minimum, maximum].
bool readNumber(const YAML::Node &node, const char *pKey, const std::string &prefix, float minimum, float maximum,
    float &value, std::string &errorMessage)
{
    if (!node[pKey])
    {
        return true;
    }

    const float parsed = node[pKey].as<float>();
    if (!std::isfinite(parsed) || parsed < minimum || parsed > maximum)
    {
        errorMessage = prefix + " " + pKey + " is out of range";
        return false;
    }

    value = parsed;
    return true;
}

bool parseLayer(const YAML::Node &node, const std::string &prefix, MistLayer &layer, std::string &errorMessage)
{
    if (!checkKeys(node, prefix, {"color_rgb", "base_height", "depth", "falloff_height", "visibility", "max_opacity",
            "noise", "noise_size", "drift", "follow_daylight"}, errorMessage)
        || !readColor(node, prefix, layer.color, errorMessage))
    {
        return false;
    }

    if (!node["base_height"] || !node["falloff_height"] || !node["visibility"])
    {
        errorMessage = prefix + " requires base_height, falloff_height and visibility";
        return false;
    }

    constexpr float Far = 1.0e6f;
    if (!readNumber(node, "base_height", prefix, -Far, Far, layer.baseHeight, errorMessage)
        || !readNumber(node, "depth", prefix, 0.0f, Far, layer.depth, errorMessage)
        || !readNumber(node, "falloff_height", prefix, 1.0f, Far, layer.falloffHeight, errorMessage)
        || !readNumber(node, "visibility", prefix, 1.0f, Far, layer.visibility, errorMessage)
        || !readNumber(node, "max_opacity", prefix, 0.0f, 1.0f, layer.maxOpacity, errorMessage)
        || !readNumber(node, "noise", prefix, 0.0f, 1.0f, layer.noise, errorMessage)
        || !readNumber(node, "noise_size", prefix, 1.0f, Far, layer.noiseSize, errorMessage))
    {
        return false;
    }

    if (const YAML::Node driftNode = node["drift"])
    {
        if (!driftNode.IsSequence() || driftNode.size() != 2)
        {
            errorMessage = prefix + " drift must be [x, y] in world units per second";
            return false;
        }
        layer.drift = {driftNode[0].as<float>(), driftNode[1].as<float>()};
    }

    if (const YAML::Node followNode = node["follow_daylight"])
    {
        layer.followsDaylight = followNode.as<bool>();
    }

    return true;
}

bool parseVolume(const YAML::Node &node, size_t index, MistVolume &volume, std::string &errorMessage)
{
    const std::string prefix = "mist volume " + std::to_string(index);
    if (!checkKeys(node, prefix, {"position", "radius", "color_rgb", "visibility", "max_opacity", "noise",
            "follow_daylight"}, errorMessage)
        || !readColor(node, prefix, volume.color, errorMessage))
    {
        return false;
    }

    const YAML::Node positionNode = node["position"];
    const YAML::Node radiusNode = node["radius"];
    if (!positionNode || !positionNode.IsSequence() || positionNode.size() != 3 || !radiusNode
        || !node["visibility"])
    {
        errorMessage = prefix + " requires position [x, y, z], radius and visibility";
        return false;
    }

    for (size_t axis = 0; axis < 3; ++axis)
    {
        volume.position[axis] = positionNode[axis].as<float>();
    }

    if (radiusNode.IsSequence() && radiusNode.size() == 3)
    {
        for (size_t axis = 0; axis < 3; ++axis)
        {
            volume.radius[axis] = radiusNode[axis].as<float>();
        }
    }
    else if (radiusNode.IsScalar())
    {
        volume.radius.fill(radiusNode.as<float>());
    }
    else
    {
        errorMessage = prefix + " radius must be one number or [x, y, z]";
        return false;
    }

    for (const float radius : volume.radius)
    {
        if (!std::isfinite(radius) || radius < 1.0f)
        {
            errorMessage = prefix + " radius must be at least 1";
            return false;
        }
    }

    constexpr float Far = 1.0e6f;
    if (!readNumber(node, "visibility", prefix, 1.0f, Far, volume.visibility, errorMessage)
        || !readNumber(node, "max_opacity", prefix, 0.0f, 1.0f, volume.maxOpacity, errorMessage)
        || !readNumber(node, "noise", prefix, 0.0f, 1.0f, volume.noise, errorMessage))
    {
        return false;
    }

    if (const YAML::Node followNode = node["follow_daylight"])
    {
        volume.followsDaylight = followNode.as<bool>();
    }

    return true;
}

void emitColor(YAML::Emitter &emitter, const std::array<float, 3> &color)
{
    emitter << YAML::Key << "color_rgb" << YAML::Value << YAML::Flow << YAML::BeginSeq << color[0] * 255.0f
            << color[1] * 255.0f << color[2] * 255.0f << YAML::EndSeq;
}
}

bool parseSceneMistNode(const YAML::Node &node, MapMist &mist, std::string &errorMessage)
{
    MapMist parsed = {};

    try
    {
        if (!checkKeys(node, "mist", {"layer", "layers", "volumes"}, errorMessage))
        {
            return false;
        }

        // `layer` is one layer; `layers` a sequence of up to MaxMistLayers.
        if (node["layer"] && node["layers"])
        {
            errorMessage = "mist takes layer or layers, not both";
            return false;
        }

        if (const YAML::Node layerNode = node["layer"])
        {
            MistLayer layer = {};
            if (!parseLayer(layerNode, "mist layer", layer, errorMessage))
            {
                return false;
            }
            parsed.layers.push_back(layer);
        }

        if (const YAML::Node layersNode = node["layers"])
        {
            if (!layersNode.IsSequence() || layersNode.size() > MaxMistLayers)
            {
                errorMessage = "mist layers must be a sequence of at most " + std::to_string(MaxMistLayers);
                return false;
            }

            for (size_t index = 0; index < layersNode.size(); ++index)
            {
                MistLayer layer = {};
                if (!parseLayer(layersNode[index], "mist layer " + std::to_string(index), layer, errorMessage))
                {
                    return false;
                }
                parsed.layers.push_back(layer);
            }
        }

        if (const YAML::Node volumesNode = node["volumes"])
        {
            if (!volumesNode.IsSequence())
            {
                errorMessage = "mist volumes must be a sequence";
                return false;
            }

            for (size_t index = 0; index < volumesNode.size(); ++index)
            {
                MistVolume volume = {};
                if (!parseVolume(volumesNode[index], index, volume, errorMessage))
                {
                    return false;
                }
                parsed.volumes.push_back(volume);
            }
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse mist: ") + exception.what();
        return false;
    }

    mist = std::move(parsed);
    return true;
}

bool parseSceneMist(const std::string &yamlText, MapMist &mist, std::string &errorMessage)
{
    try
    {
        return parseSceneMistNode(YAML::Load(yamlText), mist, errorMessage);
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse mist: ") + exception.what();
        return false;
    }
}

void emitSceneMist(YAML::Emitter &emitter, const MapMist &mist)
{
    if (!mist.enabled())
    {
        return;
    }

    emitter << YAML::Key << "mist" << YAML::Value << YAML::BeginMap;
    if (!mist.layers.empty())
    {
        emitter << YAML::Key << "layers" << YAML::Value << YAML::BeginSeq;
    }
    for (const MistLayer &layer : mist.layers)
    {
        emitter << YAML::BeginMap;
        emitColor(emitter, layer.color);
        emitter << YAML::Key << "base_height" << YAML::Value << layer.baseHeight;
        if (layer.depth >= 0.0f)
        {
            emitter << YAML::Key << "depth" << YAML::Value << layer.depth;
        }
        emitter << YAML::Key << "falloff_height" << YAML::Value << layer.falloffHeight;
        emitter << YAML::Key << "visibility" << YAML::Value << layer.visibility;
        emitter << YAML::Key << "max_opacity" << YAML::Value << layer.maxOpacity;
        emitter << YAML::Key << "noise" << YAML::Value << layer.noise;
        emitter << YAML::Key << "noise_size" << YAML::Value << layer.noiseSize;
        emitter << YAML::Key << "drift" << YAML::Value << YAML::Flow << YAML::BeginSeq << layer.drift[0]
                << layer.drift[1] << YAML::EndSeq;
        emitter << YAML::Key << "follow_daylight" << YAML::Value << layer.followsDaylight;
        emitter << YAML::EndMap;
    }
    if (!mist.layers.empty())
    {
        emitter << YAML::EndSeq;
    }
    if (!mist.volumes.empty())
    {
        emitter << YAML::Key << "volumes" << YAML::Value << YAML::BeginSeq;
        for (const MistVolume &volume : mist.volumes)
        {
            emitter << YAML::BeginMap;
            emitter << YAML::Key << "position" << YAML::Value << YAML::Flow << YAML::BeginSeq << volume.position[0]
                    << volume.position[1] << volume.position[2] << YAML::EndSeq;
            emitter << YAML::Key << "radius" << YAML::Value << YAML::Flow << YAML::BeginSeq << volume.radius[0]
                    << volume.radius[1] << volume.radius[2] << YAML::EndSeq;
            emitColor(emitter, volume.color);
            emitter << YAML::Key << "visibility" << YAML::Value << volume.visibility;
            emitter << YAML::Key << "max_opacity" << YAML::Value << volume.maxOpacity;
            emitter << YAML::Key << "noise" << YAML::Value << volume.noise;
            emitter << YAML::Key << "follow_daylight" << YAML::Value << volume.followsDaylight;
            emitter << YAML::EndMap;
        }
        emitter << YAML::EndSeq;
    }
    emitter << YAML::EndMap;
}
}
