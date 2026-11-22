#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"

#include <cstdint>
#include <span>
#include <vector>

namespace OpenYAMM::Game::ReplicaWorldCalls
{
// What a guest's own game does to the host's map. A guest's game resolves its player's blows, shots and talents
// itself, with the screen, the aim and the battle orders it has ("The replica as built" in
// devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md); where that would change the map, its replica makes one
// of these calls instead and keeps it for the host (IGameplayWorldRuntime::takeReplicaWorldCalls). The host runs
// each on its map for that player
// (execute), where the monster's death, its loot and the experience are worked out as for any blow.
//
// Each function writes one call. They mirror the world runtime's own functions of the same purpose.
std::vector<uint8_t> meleeDamage(
    size_t actorIndex,
    int damage,
    const GameplayWorldPoint &source,
    ShieldAttackTier shieldTier,
    const ShieldHitModifiers &shieldModifiers,
    bool critical,
    bool hitReaction);
std::vector<uint8_t> meleeEffects(
    size_t actorIndex,
    const CharacterAttackResult &attack,
    const GameplayWorldPoint &source);
std::vector<uint8_t> meleeBModelDamage(size_t bModelIndex, int damage);
std::vector<uint8_t> meleeEntityDamage(size_t entityIndex, int damage);
std::vector<uint8_t> attackProjectile(const GameplayPartyAttackProjectileRequest &request);
std::vector<uint8_t> attackSpell(const GameplayPartyAttackSpellRequest &request);
std::vector<uint8_t> spellProjectile(const GameplayPartySpellProjectileRequest &request);
std::vector<uint8_t> attackResult(std::optional<size_t> actorIndex, bool attacked, bool actionPerformed, bool missed);
std::vector<uint8_t> stunActor(size_t actorIndex, float seconds);
std::vector<uint8_t> debuffActor(size_t actorIndex, GameplayActorHitDebuff debuff, float seconds, float power);
std::vector<uint8_t> healActor(size_t actorIndex, int amount);
std::vector<uint8_t> reflectedDamage(uint32_t actorId, int damage, CombatDamageType damageType, uint32_t memberIndex);
std::vector<uint8_t> pushActor(size_t actorIndex, float directionX, float directionY, float distance);
std::vector<uint8_t> suspendActorShield(size_t actorIndex, float seconds);
std::vector<uint8_t> restoreActorShield(size_t actorIndex);
std::vector<uint8_t> actorHitMarks(size_t actorIndex, const ActorHitMarks &marks);
std::vector<uint8_t> revealActorsAround(size_t actorIndex, float radius);
std::vector<uint8_t> scareNearbyPeasants(float radius, float seconds);
std::vector<uint8_t> dropHeldItem(const GameplayHeldItemDropRequest &request);

// The host's side: runs a call on the map, for the party the map acts with (the calling player's). False for a call
// that cannot be read or names what the map has not.
bool execute(IGameplayWorldRuntime &worldRuntime, std::span<const uint8_t> call);
// Whether the call is one half of a change whose other half is in the player's character (the item dropped from the
// cursor): the host does both or neither.
bool goesWithCharacterChange(std::span<const uint8_t> call);
}
