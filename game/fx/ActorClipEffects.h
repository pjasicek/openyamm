#pragma once

#include "game/fx/EffectDefinition.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// Named effects carried on the sockets of an actor's 3D model while one of its clips plays (actors.yml
// `animation.events`): Might and Magic IX's DoFX and EndFX animation keys, which play a monster's FX0-FX2 effect
// (bluedots, redyeldots, greenyeldots) on its hands. An event names them as `effect: {...}` or as a list
// `effects: [{...}, ...]` with the keys
//   id      the named effect (it must be in the effect library);
//   socket  a name in animation.sockets, or sockets: [a, b] for one effect on each (at most four);
//   start   clip seconds when it starts (default 0);
//   end     clip seconds when it stops emitting (default: when the clip ends or another starts);
//   scale   relative to the actor's effect scale (default 1).
// The effect follows its socket while it plays; it drains (its particles finish) when it stops. An effect whose
// emitters MM9 puts on body nodes (bluedots: one on the left hand, one on the right), named on as many sockets as it
// has such nodes, gives each socket one node's emitters, in the order the effect names them (sockets: [palm_left,
// palm_right]): the hands together emit what MM9's one effect does (actorClipEffectSocketAnchor).
struct ActorClipEffect
{
    std::string effectId;
    std::vector<std::string> sockets;
    float startSeconds = 0.0f;
    // Negative: until the clip ends or changes.
    float endSeconds = -1.0f;
    float scale = 1.0f;
};

constexpr size_t ActorClipEffectMaxCount = 8;
constexpr size_t ActorClipEffectMaxSockets = 4;

// Reads an event's `effect` and list-form `effects` (a map `effects` is the ranged attack's element-keyed form, left to
// the caller). Throws std::runtime_error naming `where` for an unknown key, a missing id or socket, a socket not in
// animation.sockets (hasSocket), an effect not in the library (hasEffect), a start or end outside the clip, an end
// before its start, a bad scale, both forms at once, or more than ActorClipEffectMaxCount effects.
std::vector<ActorClipEffect> parseActorClipEffects(const YAML::Node &event, float clipSeconds,
    const std::function<bool(const std::string &)> &hasSocket,
    const std::function<bool(const std::string &)> &hasEffect, const std::string &where);

// The body anchor whose emitters the effect spawned on socket `socket` of `socketCount` keeps: the socket-th of the
// effect's distinct emitter anchors (in component order) when the effect has as many as there are sockets and more
// than one; empty (every emitter) otherwise.
std::string actorClipEffectSocketAnchor(const EffectDefinition &definition, size_t socketCount, size_t socket);

// Whether a clip effect emits at clip time timeSeconds: from its start, until its end (or for the rest of the clip).
bool actorClipEffectEmits(const ActorClipEffect &effect, float timeSeconds);

// The action role (0 melee attack, 1 ranged attack, 2 cast) whose clip `clip` is, among the roles with something to
// show (hasContent), in that order; -1 for none. Roles may share a clip (a caster that casts with its ranged gesture):
// the first wins. It names the role of a clip played by a behaviour script or a cinematic.
int actorActionRoleForClip(const std::array<uint32_t, 3> &roleClips, const std::array<bool, 3> &hasContent,
    uint32_t clip);
}
