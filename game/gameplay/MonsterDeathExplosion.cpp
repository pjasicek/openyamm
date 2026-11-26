#include "game/gameplay/MonsterDeathExplosion.h"

#include "game/events/ISceneEventContext.h"
#include "game/gameplay/GameplayActorService.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
// The blast's damage to one party (or, from a detonation that strikes them, one actor): its dice, scaled, or fixed.
int rollPartyDamage(const PendingMonsterDeathExplosion &pending, std::mt19937 &rng)
{
    if (pending.fixedPartyDamage > 0)
    {
        return pending.fixedPartyDamage;
    }

    const int roll = GameMechanics::rollMonsterAttackDamage(
        pending.partyDamage.diceRolls, pending.partyDamage.diceSides, pending.partyDamage.bonus, rng);
    return pending.partyDamageScale == 1.0f ? roll
                                            : std::max(1, int(std::lround(float(roll) * pending.partyDamageScale)));
}
}

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

std::optional<PendingMonsterDeathExplosion> monsterDetonationFor(
    const IGameplayWorldRuntime &world,
    size_t actorIndex)
{
    const MonsterTable *pMonsterTable = world.monsterTable();
    GameplayRuntimeActorState actor = {};

    if (pMonsterTable == nullptr || !world.actorRuntimeState(actorIndex, actor))
    {
        return std::nullopt;
    }

    const MonsterModifierSet *pModifiers = pMonsterTable->findModifiers(actor.monsterId);
    const MonsterTable::MonsterStatsEntry *pStats = pMonsterTable->findStatsById(actor.monsterId);

    if (pModifiers == nullptr || !pModifiers->detonate || pStats == nullptr)
    {
        return std::nullopt;
    }

    const DetonateModifier &detonate = *pModifiers->detonate;
    PendingMonsterDeathExplosion pending = {};
    pending.actorId = actor.actorId;
    pending.monsterId = actor.monsterId;
    pending.hostileToParty = actor.hostileToParty;
    const float height = float(actor.bodyHeight > 0 ? actor.bodyHeight : actor.height);
    pending.point = {actor.preciseX, actor.preciseY, actor.preciseZ + height * 0.5f};
    pending.detonation = true;
    pending.radius = detonate.radius;
    pending.detonationHitsActors = detonate.hitsMonsters;

    // Its melee attack, as its inspect window shows it (a bolstered monster's dice).
    const bool useAttack2 = pStats->attack1HasMissile && !pStats->attack2HasMissile
        && pStats->attack2Damage.diceRolls > 0 && pStats->attack2Damage.diceSides > 0;
    pending.partyDamage = useAttack2 ? pStats->attack2Damage : pStats->attack1Damage;
    GameplayActorInspectState inspect = {};

    if (world.actorInspectState(actorIndex, 0, inspect))
    {
        const MonsterTable::MonsterStatsEntry::DamageProfile &dice =
            useAttack2 ? inspect.attack2Damage : inspect.attack1Damage;

        if (dice.diceRolls > 0)
        {
            pending.partyDamage = dice;
        }
    }

    pending.partyDamageType = detonate.damageType == "melee"
        ? GameMechanics::parseCombatDamageType(useAttack2 ? pStats->attack2Type : pStats->attack1Type)
        : GameMechanics::parseCombatDamageType(detonate.damageType);
    pending.partyDamageScale = detonate.damage > 0.0f ? 1.0f : detonate.meleeMultiplier;
    pending.fixedPartyDamage = detonate.damage > 0.0f ? std::max(1, int(std::lround(detonate.damage))) : 0;
    return pending;
}

std::optional<int> monsterDeathExplosionDamageAt(
    const ISceneEventContext &scene,
    const PendingMonsterDeathExplosion &pending,
    float x,
    float y,
    float footZ,
    float eyeZ,
    std::mt19937 &rng)
{
    const GameplayWorldPoint &point = pending.point;
    // A party is hit within the radius plus 32 of its middle, with nothing in the way of its eyes (0x4376fc).
    const float distance = std::hypot(x - point.x, y - point.y, (footZ + eyeZ) * 0.5f - point.z);

    if (distance >= pending.radius + 32.0f
        || !scene.hasLineOfSight(point.x, point.y, point.z, x, y, eyeZ))
    {
        return std::nullopt;
    }

    return rollPartyDamage(pending, rng);
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
    const std::optional<int> partyDamage = monsterDeathExplosionDamageAt(
        scene, pending, world.partyX(), world.partyY(), world.partyFootZ(), world.partyEyeZ(), rng);
    explosion.partyDamageType = pending.partyDamageType;

    if (partyDamage)
    {
        explosion.hitsParty = true;
        explosion.partyDamage = *partyDamage;
    }

    const MonsterTable *pMonsterTable = world.monsterTable();
    const MonsterTable::MonsterStatsEntry *pStats =
        pMonsterTable != nullptr ? pMonsterTable->findStatsById(pending.monsterId) : nullptr;

    // A detonation strikes other actors only when its modifier says so, with the party's damage.
    if (pStats == nullptr || (pending.detonation && !pending.detonationHitsActors))
    {
        explosion.actorDamageType = pending.detonation ? pending.partyDamageType : explosion.actorDamageType;
        return explosion;
    }

    explosion.actorDamageType = pending.detonation ? pending.partyDamageType
                                                   : GameMechanics::parseCombatDamageType(pStats->deathExplosionType);
    const std::vector<size_t> actorIndices = world.collectMapActorIndicesWithinRadius(
        point.x,
        point.y,
        point.z,
        pending.radius,
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

        const int damage = pending.detonation
            ? rollPartyDamage(pending, rng)
            : GameMechanics::rollMonsterAttackDamage(
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
