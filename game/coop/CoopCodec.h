#pragma once

#include "engine/net/ByteStream.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/gameplay/PlayerId.h"
#include "game/party/PartySpellSystem.h"

#include <optional>
#include <vector>

namespace OpenYAMM::Game::CoopCodec
{
// How the values of a co-op session's messages are written and read, field by field (CoopProtocol.h). A reader that
// meets a value it cannot take (an index beyond a list's limit, a number that is no number) fails as a whole.

void writeBody(Engine::ByteWriter &writer, const GameplayPlayerBody &body);
GameplayPlayerBody readBody(Engine::ByteReader &reader);
bool finiteBody(const GameplayPlayerBody &body);

void writePose(Engine::ByteWriter &writer, const ReplicaActorPose &pose);
ReplicaActorPose readPose(Engine::ByteReader &reader);
bool finitePose(const ReplicaActorPose &pose);

// Sounds an event or the world asked for, with everything playing them needs (a save keeps less: its sounds are
// replayed by the map, not by another game).
void writeSounds(Engine::ByteWriter &writer, const std::vector<EventRuntimeState::PendingSound> &sounds);
bool readSounds(Engine::ByteReader &reader, std::vector<EventRuntimeState::PendingSound> &sounds);

// What a player pointed at in the world.
void writeWorldHit(Engine::ByteWriter &writer, const GameplayWorldHit &hit);
GameplayWorldHit readWorldHit(Engine::ByteReader &reader);

// A cast as the player's game asked for it. The party it names a member of travels as the player whose it is;
// the other players in reach are the host's to add.
void writeSpellCastRequest(
    Engine::ByteWriter &writer,
    const PartySpellCastRequest &request,
    std::optional<PlayerId> targetPlayer);
PartySpellCastRequest readSpellCastRequest(Engine::ByteReader &reader, std::optional<PlayerId> &targetPlayer);
}
