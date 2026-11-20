#include "game/gameplay/MonsterDeathExplosion.h"

#include "game/events/ISceneEventContext.h"
#include "game/gameplay/GameplayActorService.h"

#include <cmath>

namespace OpenYAMM::Game
{
std::optional<PendingMonsterDeathExplosion> monsterDeathExplosionFor(
    const IGameplayWorldRuntime &world,
    size_t actorIndex)
{
    const MonsterTable *pMonsterTable = world.monsterTable();
    GameplayRuntimeActorState actor = {};

    if (pMonsterTable == nullptr || !world.actorRuntimeState(actorIndex, actor))
    {
        return std::nullopt;
    }

    const MonsterTable::MonsterStatsEntry *pStats = pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr || !pStats->explodesOnDeath)
    {
        return std::nullopt;
    }

    PendingMonsterDeathExplosion pending = {};
    pending.actorId = actor.actorId;
    pending.monsterId = actor.monsterId;
    pending.hostileToParty = actor.hostileToParty;
    const float height = float(actor.bodyHeight > 0 ? actor.bodyHeight : actor.height);
    pending.point = {actor.preciseX, actor.preciseY, actor.preciseZ + height * 0.75f};
    pending.partyDamage = pStats->attack1Damage;
    pending.partyDamageType = GameMechanics::parseCombatDamageType(pStats->attack1Type);

    // The actor's own Attack 1 (a bolstered monster's dice), as its inspect window shows it.
    GameplayActorInspectState inspect = {};

    if (world.actorInspectState(actorIndex, 0, inspect) && inspect.attack1Damage.diceRolls > 0)
    {
        pending.partyDamage = inspect.attack1Damage;
    }

    return pending;
}

MonsterDeathExplosion resolveMonsterDeathExplosion(
    const IGameplayWorldRuntime &world,
    const ISceneEventContext &scene,
    const GameplayActorService &actorService,
    const PendingMonsterDeathExplosion &pending,
    std::mt19937 &rng)
{
    MonsterDeathExplosion explosion = {};
    const GameplayWorldPoint &point = pending.point;
    // The party is hit within the radius plus 32 of its middle, with nothing in the way of its eyes (0x4376fc).
    const float partyMiddleZ = (world.partyFootZ() + world.partyEyeZ()) * 0.5f;
    const float partyDistance =
        std::hypot(world.partyX() - point.x, world.partyY() - point.y, partyMiddleZ - point.z);

    if (partyDistance < MonsterDeathExplosionRadius + 32.0f
        && scene.hasLineOfSight(point.x, point.y, point.z, world.partyX(), world.partyY(), world.partyEyeZ()))
    {
        explosion.hitsParty = true;
        explosion.partyDamage = GameMechanics::rollMonsterAttackDamage(
            pending.partyDamage.diceRolls,
            pending.partyDamage.diceSides,
            pending.partyDamage.bonus,
            rng);
        explosion.partyDamageType = pending.partyDamageType;
    }

    const MonsterTable *pMonsterTable = world.monsterTable();
    const MonsterTable::MonsterStatsEntry *pStats =
        pMonsterTable != nullptr ? pMonsterTable->findStatsById(pending.monsterId) : nullptr;

    if (pStats == nullptr)
    {
        return explosion;
    }

    explosion.actorDamageType = GameMechanics::parseCombatDamageType(pStats->deathExplosionType);
    const std::vector<size_t> actorIndices = world.collectMapActorIndicesWithinRadius(
        point.x,
        point.y,
        point.z,
        MonsterDeathExplosionRadius,
        true,
        point.x,
        point.y,
        point.z);

    for (size_t actorIndex : actorIndices)
    {
        GameplayRuntimeActorState actor = {};

        if (!world.actorRuntimeState(actorIndex, actor) || actor.actorId == pending.actorId)
        {
            continue;
        }

        // Its own kind on its side of the party is spared (MM8 tests the relation of the two, 0x437877).
        if (actor.hostileToParty == pending.hostileToParty
            && actorService.monsterIdsAreFriendly(pending.monsterId, actor.monsterId))
        {
            continue;
        }

        const int damage = GameMechanics::rollMonsterAttackDamage(
            pStats->deathExplosionDamage.diceRolls,
            pStats->deathExplosionDamage.diceSides,
            pStats->deathExplosionDamage.bonus,
            rng);

        if (damage > 0)
        {
            explosion.actorHits.push_back({actorIndex, damage});
        }
    }

    return explosion;
}
}
