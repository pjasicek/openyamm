#pragma once

#include "game/gameplay/GameplayProjectileService.h"
#include "game/maps/SaveGame.h"

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game::SaveSections
{
// Pieces of a save as bytes of their own, written and read by the save's own code in the current save version: what
// the host of a co-op session sends its guests (game/coop). Both games run the same build (the session's admission
// compares the save version), so nothing here reads an older layout.

// The version this build writes.
uint32_t saveVersion();

// A whole game, as a save file holds it.
std::vector<uint8_t> encodeGame(const GameSaveData &data);
std::optional<GameSaveData> decodeGame(std::span<const uint8_t> bytes, std::string &error);

// A party without the campaign it plays in (Party::Snapshot::campaign is left out and comes back empty), and a
// campaign by itself.
std::vector<uint8_t> encodeCharacters(const Party::Snapshot &party);
bool decodeCharacters(std::span<const uint8_t> bytes, Party::Snapshot &party);
std::vector<uint8_t> encodeCampaign(const CampaignState::Snapshot &campaign);
bool decodeCampaign(std::span<const uint8_t> bytes, CampaignState::Snapshot &campaign);

std::vector<uint8_t> encode(const InventoryItem &value);
bool decode(std::span<const uint8_t> bytes, InventoryItem &value);
std::vector<uint8_t> encode(const EventRuntimeState &value);
bool decode(std::span<const uint8_t> bytes, EventRuntimeState &value);
// Reads into the state given: what a save does not hold of it stays as it was.
std::vector<uint8_t> encode(const std::unordered_map<uint32_t, RuntimeMechanismState> &value);
bool decode(std::span<const uint8_t> bytes, std::unordered_map<uint32_t, RuntimeMechanismState> &value);
std::vector<uint8_t> encode(const MawGameState &value);
bool decode(std::span<const uint8_t> bytes, MawGameState &value);
std::vector<uint8_t> encode(const OutdoorWorldRuntime::MapActorState &value);
bool decode(std::span<const uint8_t> bytes, OutdoorWorldRuntime::MapActorState &value);
// An indoor actor is its map record and its AI state.
std::vector<uint8_t> encode(const std::pair<MapDeltaActor, IndoorWorldRuntime::MapActorAiState> &value);
bool decode(std::span<const uint8_t> bytes, std::pair<MapDeltaActor, IndoorWorldRuntime::MapActorAiState> &value);
std::vector<uint8_t> encode(const std::vector<OutdoorWorldRuntime::WorldItemState> &value);
bool decode(std::span<const uint8_t> bytes, std::vector<OutdoorWorldRuntime::WorldItemState> &value);
std::vector<uint8_t> encode(const std::vector<MapDeltaSpriteObject> &value);
bool decode(std::span<const uint8_t> bytes, std::vector<MapDeltaSpriteObject> &value);
std::vector<uint8_t> encode(const std::vector<MapDeltaDoor> &value);
bool decode(std::span<const uint8_t> bytes, std::vector<MapDeltaDoor> &value);
std::vector<uint8_t> encode(const GameplayProjectileService::ProjectileState &value);
bool decode(std::span<const uint8_t> bytes, GameplayProjectileService::ProjectileState &value);
std::vector<uint8_t> encode(const GameplayProjectileService::ProjectileImpactState &value);
bool decode(std::span<const uint8_t> bytes, GameplayProjectileService::ProjectileImpactState &value);
std::vector<uint8_t> encode(const GameplayChestViewState &value);
bool decode(std::span<const uint8_t> bytes, GameplayChestViewState &value);
std::vector<uint8_t> encode(const GameplayCorpseViewState &value);
bool decode(std::span<const uint8_t> bytes, GameplayCorpseViewState &value);
}
