#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <random>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayActorService;
class ISceneEventContext;

// MM8's death blast of a monster whose Special is "explode" (MonsterStatsEntry::explodesOnDeath): object 600 at three
// quarters of its height bursts at once (MM8 0x404a90, impact 0x46c002) and hits everything within 512 (0x46c058).
constexpr float MonsterDeathExplosionRadius = 512.0f;
// Object 601, "explosion": the burst's visual (the fireball's impact effect).
constexpr uint16_t MonsterDeathExplosionObjectId = 601;

// A death recorded when the monster died; the world detonates it on its next update, so a blast that kills never runs
// inside the damage pass that killed its source.
struct PendingMonsterDeathExplosion
{
    uint32_t actorId = 0;
    int16_t monsterId = 0;
    bool hostileToParty = false;
    GameplayWorldPoint point = {};
    MonsterTable::MonsterStatsEntry::DamageProfile partyDamage = {};
    CombatDamageType partyDamageType = CombatDamageType::Physical;
};

struct MonsterDeathExplosionActorHit
{
    size_t actorIndex = 0;
    int damage = 0;
};

struct MonsterDeathExplosion
{
    // The party in range and in sight: every member takes the monster's Attack 1 (MM8 passes ability 0 for the
    // party, 0x43774f), as one area hit.
    bool hitsParty = false;
    int partyDamage = 0;
    CombatDamageType partyDamageType = CombatDamageType::Physical;
    // Actors in range and in sight that are not friendly to it take the explode dice (the object's ability 4,
    // 0x437880), each rolled.
    std::vector<MonsterDeathExplosionActorHit> actorHits;
    CombatDamageType actorDamageType = CombatDamageType::Physical;
};

// The blast of actor actorIndex, which has just died; none when its monster does not explode.
std::optional<PendingMonsterDeathExplosion> monsterDeathExplosionFor(
    const IGameplayWorldRuntime &world,
    size_t actorIndex);

MonsterDeathExplosion resolveMonsterDeathExplosion(
    const IGameplayWorldRuntime &world,
    const ISceneEventContext &scene,
    const GameplayActorService &actorService,
    const PendingMonsterDeathExplosion &pending,
    std::mt19937 &rng);
}
