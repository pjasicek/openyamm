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
    // A detonate modifier's blast (MonsterModifierSet::detonate) rather than MM8's death blast: its own radius, the
    // party's roll scaled (or a fixed damage), and other actors struck with the party's damage only when it says so.
    bool detonation = false;
    float radius = MonsterDeathExplosionRadius;
    float partyDamageScale = 1.0f;
    int fixedPartyDamage = 0;
    bool detonationHitsActors = false;
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

// The blast of a detonate modifier's actor actorIndex as its charge ends (its body's middle, its own Attack1 dice:
// Attack2's when Attack1 fires a missile and Attack2 does not, as a charge's hit); none without the modifier.
std::optional<PendingMonsterDeathExplosion> monsterDetonationFor(
    const IGameplayWorldRuntime &world,
    size_t actorIndex);

// The damage of the blast to a party standing at this place, rolled; none when it is out of range or out of
// sight. The world's own party is in resolveMonsterDeathExplosion's result; this is for the other players of a
// co-op session.
std::optional<int> monsterDeathExplosionDamageAt(
    const ISceneEventContext &scene,
    const PendingMonsterDeathExplosion &pending,
    float x,
    float y,
    float footZ,
    float eyeZ,
    std::mt19937 &rng);

MonsterDeathExplosion resolveMonsterDeathExplosion(
    const IGameplayWorldRuntime &world,
    const ISceneEventContext &scene,
    const GameplayActorService &actorService,
    const PendingMonsterDeathExplosion &pending,
    std::mt19937 &rng);
}
