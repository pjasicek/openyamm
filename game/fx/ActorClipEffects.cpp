#include "game/fx/ActorClipEffects.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
ActorClipEffect parseOne(const YAML::Node &node, float clipSeconds,
    const std::function<bool(const std::string &)> &hasSocket,
    const std::function<bool(const std::string &)> &hasEffect, const std::string &where)
{
    if (!node.IsMap())
    {
        throw std::runtime_error("actor animation event effect must be a map: " + where);
    }
    for (const auto &key : node)
    {
        const std::string name = key.first.as<std::string>();
        if (name != "id" && name != "socket" && name != "sockets" && name != "start" && name != "end"
            && name != "scale")
        {
            throw std::runtime_error("unknown actor animation event effect key: " + where + " " + name);
        }
    }
    ActorClipEffect effect;
    effect.effectId = node["id"].as<std::string>("");
    if (effect.effectId.empty() || !hasEffect(effect.effectId))
    {
        throw std::runtime_error("actor animation event effect not found: " + where + " " + effect.effectId);
    }
    if (node["socket"] && node["sockets"])
    {
        throw std::runtime_error("actor animation event effect takes socket or sockets, not both: " + where);
    }
    if (const YAML::Node socket = node["socket"])
    {
        effect.sockets.push_back(socket.as<std::string>());
    }
    else if (const YAML::Node sockets = node["sockets"]; sockets && sockets.IsSequence())
    {
        for (const YAML::Node &socket : sockets)
        {
            effect.sockets.push_back(socket.as<std::string>());
        }
    }
    if (effect.sockets.empty() || effect.sockets.size() > ActorClipEffectMaxSockets)
    {
        throw std::runtime_error("actor animation event effect needs one to four sockets: " + where);
    }
    for (const std::string &socket : effect.sockets)
    {
        if (!hasSocket(socket))
        {
            throw std::runtime_error("actor animation event socket is not in animation.sockets: " + where + " "
                + socket);
        }
    }
    effect.startSeconds = node["start"].as<float>(0.0f);
    effect.endSeconds = node["end"].as<float>(-1.0f);
    effect.scale = node["scale"].as<float>(1.0f);
    if (!std::isfinite(effect.startSeconds) || effect.startSeconds < 0.0f || effect.startSeconds >= clipSeconds
        || (node["end"] && (!std::isfinite(effect.endSeconds) || effect.endSeconds <= effect.startSeconds
            || effect.endSeconds > clipSeconds)))
    {
        throw std::runtime_error("actor animation event effect start/end outside its clip: " + where);
    }
    if (!std::isfinite(effect.scale) || effect.scale <= 0.0f)
    {
        throw std::runtime_error("invalid actor animation event effect scale: " + where);
    }
    return effect;
}
}

std::vector<ActorClipEffect> parseActorClipEffects(const YAML::Node &event, float clipSeconds,
    const std::function<bool(const std::string &)> &hasSocket,
    const std::function<bool(const std::string &)> &hasEffect, const std::string &where)
{
    std::vector<ActorClipEffect> effects;
    const YAML::Node single = event["effect"];
    const YAML::Node list = event["effects"];
    const bool listed = list && list.IsSequence();
    if (single && listed)
    {
        throw std::runtime_error("actor animation event takes effect or a list of effects, not both: " + where);
    }
    if (single)
    {
        effects.push_back(parseOne(single, clipSeconds, hasSocket, hasEffect, where));
    }
    else if (listed)
    {
        if (list.size() == 0 || list.size() > ActorClipEffectMaxCount)
        {
            throw std::runtime_error("actor animation event effects lists one to eight effects: " + where);
        }
        for (const YAML::Node &node : list)
        {
            effects.push_back(parseOne(node, clipSeconds, hasSocket, hasEffect, where));
        }
    }
    return effects;
}

std::string actorClipEffectSocketAnchor(const EffectDefinition &definition, size_t socketCount, size_t socket)
{
    std::vector<std::string> anchors;
    for (const EffectSpriteEmitterDefinition &emitter : definition.spriteEmitters)
    {
        if (!emitter.bodyAnchor.empty()
            && std::find(anchors.begin(), anchors.end(), emitter.bodyAnchor) == anchors.end())
        {
            anchors.push_back(emitter.bodyAnchor);
        }
    }
    if (socketCount < 2 || anchors.size() != socketCount || socket >= anchors.size())
    {
        return {};
    }
    return anchors[socket];
}

bool actorClipEffectEmits(const ActorClipEffect &effect, float timeSeconds)
{
    return timeSeconds >= effect.startSeconds && (effect.endSeconds < 0.0f || timeSeconds < effect.endSeconds);
}

int actorActionRoleForClip(const std::array<uint32_t, 3> &roleClips, const std::array<bool, 3> &hasContent,
    uint32_t clip)
{
    for (size_t role = 0; role < roleClips.size(); ++role)
    {
        if (hasContent[role] && roleClips[role] == clip && clip != UINT32_MAX)
        {
            return int(role);
        }
    }
    return -1;
}
}
