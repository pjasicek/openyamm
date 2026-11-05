#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplayActorShields.h"

#include "game/audio/SoundIds.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/fx/ParticleRecipes.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/MonsterSpellSupport.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/party/Party.h"
#include "game/SpriteObjectDefs.h"
#include "game/party/SkillData.h"
#include "game/rules/GameRules.h"
#include "game/StringUtils.h"
#include "game/party/SpellIds.h"
#include "game/tables/ObjectTable.h"
#include "game/tables/SpellTable.h"
#include "game/tables/SpriteTables.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <random>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ProjectileTicksPerSecond = 128.0f;
constexpr float SpellImpactAoeRadius = 512.0f;
constexpr float Pi = 3.14159265358979323846f;
constexpr uint32_t DeathBlossomFalloutShardCount = 8;
constexpr float DeathBlossomFalloutSourceHeightOffset = 16.0f;
constexpr float DeathBlossomFalloutYawJitter = 0.22f;
// The original launches each shard level, at a random 5-500 units per second, and lets it fall.
constexpr float DeathBlossomFalloutMinSpeed = 5.0f;
constexpr float DeathBlossomFalloutMaxSpeed = 500.0f;
constexpr float MeteorShowerSpawnBaseHeight = 2500.0f;
constexpr float MeteorShowerSpawnHeightVariance = 1000.0f;
constexpr float MeteorShowerTargetSpread = 512.0f;
constexpr uint32_t StarburstProjectileCount = 20;
constexpr float StarburstSpawnBaseHeight = 2500.0f;
constexpr float StarburstSpawnHeightVariance = 1000.0f;
constexpr float StarburstTargetSpread = 512.0f;

const char *projectileSourceKindTraceName(GameplayProjectileService::ProjectileState::SourceKind kind)
{
    switch (kind)
    {
        case GameplayProjectileService::ProjectileState::SourceKind::Actor:
            return "actor";
        case GameplayProjectileService::ProjectileState::SourceKind::Event:
            return "event";
        case GameplayProjectileService::ProjectileState::SourceKind::Party:
            return "party";
    }

    return "unknown";
}

const char *projectileCollisionKindTraceName(GameplayProjectileService::ProjectileFrameCollisionKind kind)
{
    switch (kind)
    {
        case GameplayProjectileService::ProjectileFrameCollisionKind::None:
            return "none";
        case GameplayProjectileService::ProjectileFrameCollisionKind::Party:
            return "party";
        case GameplayProjectileService::ProjectileFrameCollisionKind::Actor:
            return "actor";
        case GameplayProjectileService::ProjectileFrameCollisionKind::World:
            return "world";
    }

    return "unknown";
}

void appendProjectileTracePoint(std::ostream &out, const char *pName, float x, float y, float z)
{
    out << ' ' << pName << "=(" << x << "," << y << "," << z << ")";
}

void appendProjectileTraceSummary(
    std::ostream &out,
    const GameplayProjectileService::ProjectileState &projectile)
{
    out
        << " id=" << projectile.projectileId
        << " source_kind=" << projectileSourceKindTraceName(projectile.sourceKind)
        << " source_id=" << projectile.sourceId
        << " party_member=" << projectile.sourcePartyMemberIndex
        << " spell_id=" << projectile.spellId
        << " object_id=" << projectile.objectDescriptionId
        << " sprite_id=" << projectile.objectSpriteId
        << " object=\"" << projectile.objectName << "\""
        << " sprite=\"" << projectile.objectSpriteName << "\""
        << " flags=" << projectile.objectFlags
        << " radius=" << projectile.radius
        << " height=" << projectile.height
        << " sector=" << projectile.sectorId
        << " age_ticks=" << projectile.timeSinceCreatedTicks
        << " lifetime_ticks=" << projectile.lifetimeTicks
        << " expired=" << projectile.isExpired
        << " settled=" << projectile.isSettled;
    appendProjectileTracePoint(out, "pos", projectile.x, projectile.y, projectile.z);
    appendProjectileTracePoint(out, "vel", projectile.velocityX, projectile.velocityY, projectile.velocityZ);
}

void traceProjectileSpawnRequest(
    const GameplayProjectileService::ProjectileSpawnRequest &request,
    const char *pReason)
{
    GAMEPLAY_PROJECTILE_TRACE_BLOCK(
        std::ostringstream trace;
        trace
            << "projectile_spawn_failed reason=" << pReason
            << " source_kind=" << projectileSourceKindTraceName(request.sourceKind)
            << " source_id=" << request.sourceId
            << " spell_id=" << request.definition.spellId
            << " object_id=" << request.definition.objectDescriptionId
            << " sprite_id=" << request.definition.objectSpriteId
            << " object=\"" << request.definition.objectName << "\""
            << " sprite=\"" << request.definition.objectSpriteName << "\"";
        appendProjectileTracePoint(trace, "source", request.sourceX, request.sourceY, request.sourceZ);
        appendProjectileTracePoint(trace, "target", request.targetX, request.targetY, request.targetZ);
        gameplayProjectileTraceWrite(trace.str());
    );
}

void traceProjectileSpawnResult(
    const char *pKind,
    const GameplayProjectileService::ProjectileState &projectile,
    float directionX,
    float directionY,
    float directionZ,
    float speed)
{
    GAMEPLAY_PROJECTILE_TRACE_BLOCK(
        std::ostringstream trace;
        trace << "projectile_spawn kind=" << pKind;
        appendProjectileTraceSummary(trace, projectile);
        appendProjectileTracePoint(trace, "source", projectile.sourceX, projectile.sourceY, projectile.sourceZ);
        appendProjectileTracePoint(trace, "dir", directionX, directionY, directionZ);
        trace << " speed=" << speed;
        gameplayProjectileTraceWrite(trace.str());
    );
}

void traceProjectileNoCollision(
    const GameplayProjectileService::ProjectileState &projectile,
    const GameplayProjectileService::ProjectileFrameFacts &facts,
    const GameplayProjectileService::ProjectileMotionSegment &motion)
{
    GAMEPLAY_PROJECTILE_TRACE_BLOCK(
        std::ostringstream trace;
        trace << "projectile_frame result=no_collision dt=" << facts.deltaSeconds << " gravity=" << facts.gravity;
        appendProjectileTraceSummary(trace, projectile);
        appendProjectileTracePoint(trace, "motion_start", motion.startX, motion.startY, motion.startZ);
        appendProjectileTracePoint(trace, "motion_end", motion.endX, motion.endY, motion.endZ);
        gameplayProjectileTraceWrite(trace.str());
    );
}

void traceProjectileLifetimeExpired(const GameplayProjectileService::ProjectileState &projectile)
{
    GAMEPLAY_PROJECTILE_TRACE_BLOCK(
        std::ostringstream trace;
        trace << "projectile_frame result=lifetime_expired";
        appendProjectileTraceSummary(trace, projectile);
        gameplayProjectileTraceWrite(trace.str());
    );
}

void traceProjectileCollisionDecision(
    const GameplayProjectileService::ProjectileState &projectile,
    const GameplayProjectileService::ProjectileFrameFacts &facts,
    const GameplayProjectileService::ProjectileMotionSegment &motion,
    bool worldCollisionContinues,
    bool objectCanBounce,
    bool downwardVelocityOk,
    bool fastEnoughToBounce,
    bool canBounce)
{
    GAMEPLAY_PROJECTILE_TRACE_BLOCK(
        const GameplayProjectileService::ProjectileFrameCollisionFacts &collision = facts.collision;
        const GameplayProjectileService::ProjectileBounceSurfaceFacts &surface = collision.bounceSurface;
        std::ostringstream trace;
        trace
            << "projectile_collision_decision"
            << " kind=" << projectileCollisionKindTraceName(collision.kind)
            << " collider=\"" << collision.colliderName << "\""
            << " world_face=" << collision.worldFaceIndex
            << " actor_index=" << collision.actorIndex
            << " actor_id=" << collision.actorId
            << " water=" << collision.waterTerrainImpact
            << " surface_can_bounce=" << surface.canBounce
            << " oe_world_continue=" << worldCollisionContinues
            << " object_can_bounce=" << objectCanBounce
            << " requires_downward_velocity=" << surface.requiresDownwardVelocity
            << " downward_velocity_ok=" << downwardVelocityOk
            << " fast_enough=" << fastEnoughToBounce
            << " bounce_stop_velocity=" << facts.bounceStopVelocity
            << " bounce_factor=" << facts.bounceFactor
            << " ground_damping=" << facts.groundDamping
            << " result=" << (canBounce ? "bounce" : "impact");
        appendProjectileTraceSummary(trace, projectile);
        appendProjectileTracePoint(trace, "motion_start", motion.startX, motion.startY, motion.startZ);
        appendProjectileTracePoint(trace, "motion_end", motion.endX, motion.endY, motion.endZ);
        appendProjectileTracePoint(trace, "collision", collision.point.x, collision.point.y, collision.point.z);
        appendProjectileTracePoint(trace, "normal", surface.normalX, surface.normalY, surface.normalZ);
        gameplayProjectileTraceWrite(trace.str());
    );
}

bool isPrimaryDeathBlossomProjectile(const GameplayProjectileService::ProjectileState &projectile)
{
    return spellIdFromValue(static_cast<uint32_t>(projectile.spellId)) == SpellId::DeathBlossom
        && toLowerCopy(projectile.objectName) != "shard";
}

bool projectileContinuesAfterOeWorldImpact(const GameplayProjectileService::ProjectileState &projectile)
{
    switch (spellIdFromValue(static_cast<uint32_t>(projectile.spellId)))
    {
        case SpellId::FireSpike:
        case SpellId::Sparks:
        case SpellId::RockBlast:
        case SpellId::ToxicCloud:
            return true;

        default:
            return false;
    }
}

int rollDice(uint32_t rollCount, int diceSides)
{
    if (rollCount == 0 || diceSides <= 0)
    {
        return 0;
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<int> distribution(1, diceSides);
    int result = 0;

    for (uint32_t rollIndex = 0; rollIndex < rollCount; ++rollIndex)
    {
        result += distribution(rng);
    }

    return result;
}

int rollMonsterProjectileDamage(const GameplayProjectileService::MonsterProjectileDamageProfile &profile)
{
    if (profile.diceRolls <= 0 || profile.diceSides <= 0)
    {
        return std::max(0, profile.bonus);
    }

    return std::max(0, profile.bonus) + rollDice(static_cast<uint32_t>(profile.diceRolls), profile.diceSides);
}

int rollMonsterSpellDamage(
    int spellId,
    const GameplayProjectileService::MonsterSpellDamageProfile &profile)
{
    if (profile.skillLevel == 0)
    {
        return std::max(0, profile.baseDamage);
    }

    const SpellId typedSpellId = spellIdFromValue(static_cast<uint32_t>(spellId));

    if (typedSpellId == SpellId::FireSpike)
    {
        int diceSides = 0;

        switch (profile.skillMastery)
        {
            case SkillMastery::Normal:
            case SkillMastery::Expert:
                diceSides = 6;
                break;
            case SkillMastery::Master:
                diceSides = 8;
                break;
            case SkillMastery::Grandmaster:
                diceSides = 10;
                break;
            case SkillMastery::None:
                return 0;
        }

        return rollDice(profile.skillLevel, diceSides);
    }

    if (typedSpellId == SpellId::DeathBlossom && profile.skillMastery == SkillMastery::Grandmaster)
    {
        return std::max(0, profile.baseDamage + static_cast<int>(profile.skillLevel) * 2);
    }

    if (typedSpellId == SpellId::SpiritLash)
    {
        return std::max(
            0,
            profile.baseDamage
            + static_cast<int>(profile.skillLevel)
            + rollDice(profile.skillLevel, std::max(1, profile.diceSides - 1)));
    }

    return std::max(0, profile.baseDamage + rollDice(profile.skillLevel, std::max(1, profile.diceSides)));
}

int resolveEventProjectileDamage(int spellId, uint32_t skillLevel)
{
    if (isSpellId(static_cast<uint32_t>(spellId), SpellId::MeteorShower))
    {
        return 8 + static_cast<int>(skillLevel);
    }

    return std::max(1, static_cast<int>(skillLevel) * 2);
}

bool pointWithinExpandedCylinder(
    float pointX,
    float pointY,
    float pointCenterZ,
    float pointRadius,
    float impactX,
    float impactY,
    float impactZ,
    float impactRadius)
{
    if (impactRadius <= 0.0f)
    {
        return false;
    }

    const float deltaX = impactX - pointX;
    const float deltaY = impactY - pointY;
    const float deltaZ = impactZ - pointCenterZ;
    const float totalRadius = impactRadius + pointRadius;
    return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ <= totalRadius * totalRadius;
}

uint16_t resolveProjectileSpriteFrameIndex(
    const SpriteFrameTable *pSpriteFrameTable,
    uint16_t spriteId,
    const std::string &spriteName)
{
    if (pSpriteFrameTable != nullptr && !spriteName.empty())
    {
        const std::optional<uint16_t> frameIndex = pSpriteFrameTable->findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            return *frameIndex;
        }
    }

    return spriteId;
}

uint32_t areaSpellProjectileSeed(
    SpellId spellId,
    uint32_t nextProjectileId,
    float targetX,
    float targetY,
    float targetZ)
{
    uint32_t seed = static_cast<uint32_t>(spellId) * 1315423911u;
    seed ^= static_cast<uint32_t>(std::lround(std::abs(targetX)));
    seed ^= static_cast<uint32_t>(std::lround(std::abs(targetY))) << 1;
    seed ^= static_cast<uint32_t>(std::lround(std::abs(targetZ))) << 2;
    seed ^= nextProjectileId;
    return seed;
}

uint32_t meteorShowerProjectileCountForMastery(uint32_t skillMastery)
{
    const SkillMastery mastery = static_cast<SkillMastery>(skillMastery);

    switch (mastery)
    {
        case SkillMastery::Grandmaster:
            return 20;
        case SkillMastery::Master:
            return 16;
        case SkillMastery::Expert:
            return 12;
        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            return 8;
    }
}

int fireSpikeDamageDiceSidesForMastery(uint32_t skillMastery)
{
    switch (static_cast<SkillMastery>(skillMastery))
    {
        case SkillMastery::Grandmaster:
            return 10;
        case SkillMastery::Master:
            return 8;
        case SkillMastery::Expert:
        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            return 6;
    }
}

int rollFireSpikeDamage(uint32_t skillLevel, uint32_t skillMastery, uint32_t seed)
{
    const int diceSides = fireSpikeDamageDiceSidesForMastery(skillMastery);
    const uint32_t diceCount = std::max<uint32_t>(1, skillLevel);
    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> distribution(1, diceSides);
    int damage = 0;

    for (uint32_t dieIndex = 0; dieIndex < diceCount; ++dieIndex)
    {
        damage += distribution(rng);
    }

    return damage;
}
}

void GameplayProjectileService::clear()
{
    m_nextProjectileId = 1;
    m_nextProjectileImpactId = 1;
    m_nextFireSpikeTrapId = 1;
    m_projectiles.clear();
    m_projectileImpacts.clear();
    m_endedProjectiles.clear();
    m_recentHomingEnds.clear();
}

GameplayProjectileService::Snapshot GameplayProjectileService::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.nextProjectileId = m_nextProjectileId;
    snapshot.nextProjectileImpactId = m_nextProjectileImpactId;
    snapshot.nextFireSpikeTrapId = m_nextFireSpikeTrapId;
    snapshot.projectiles = m_projectiles;
    snapshot.projectileImpacts = m_projectileImpacts;
    return snapshot;
}

void GameplayProjectileService::restoreSnapshot(const Snapshot &snapshot)
{
    m_nextProjectileId = snapshot.nextProjectileId;
    m_nextProjectileImpactId = snapshot.nextProjectileImpactId;
    m_nextFireSpikeTrapId = snapshot.nextFireSpikeTrapId;
    m_projectiles = snapshot.projectiles;
    m_projectileImpacts = snapshot.projectileImpacts;
}

void GameplayProjectileService::clearActiveProjectiles()
{
    m_projectiles.clear();
    m_projectileImpacts.clear();
    m_endedProjectiles.clear();
}

uint32_t GameplayProjectileService::nextProjectileId() const
{
    return m_nextProjectileId;
}

uint32_t GameplayProjectileService::allocateProjectileId()
{
    return m_nextProjectileId++;
}

uint32_t GameplayProjectileService::allocateProjectileImpactId()
{
    return m_nextProjectileImpactId++;
}

uint32_t GameplayProjectileService::allocateFireSpikeTrapId()
{
    return m_nextFireSpikeTrapId++;
}

uint32_t GameplayProjectileService::ticksFromDeltaSeconds(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return 0;
    }

    return std::max<uint32_t>(
        1,
        static_cast<uint32_t>(std::lround(deltaSeconds * ProjectileTicksPerSecond)));
}

GameplayProjectileService::ProjectileSpawnResult GameplayProjectileService::spawnProjectile(
    const ProjectileSpawnRequest &request)
{
    ProjectileSpawnResult result = {};

    const float deltaX = request.targetX - request.sourceX;
    const float deltaY = request.targetY - request.sourceY;
    const float deltaZ = request.targetZ - request.sourceZ;
    const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);

    if (distance <= 0.01f)
    {
        if (!request.allowInstantImpact)
        {
            traceProjectileSpawnRequest(request, "zero_distance");
            return result;
        }

        ProjectileState projectile = {};
        projectile.projectileId = allocateProjectileId();
        projectile.sourceKind = request.sourceKind;
        projectile.sourceId = request.sourceId;
        projectile.sourcePartyMemberIndex = request.sourcePartyMemberIndex;
        projectile.sourceMonsterId = request.sourceMonsterId;
        projectile.fromSummonedMonster = request.fromSummonedMonster;
        projectile.ability = request.ability;
        projectile.objectDescriptionId = request.definition.objectDescriptionId;
        projectile.objectSpriteId = request.definition.objectSpriteId;
        projectile.objectSpriteFrameIndex = request.definition.objectSpriteFrameIndex;
        projectile.impactObjectDescriptionId = request.definition.impactObjectDescriptionId;
        projectile.objectFlags = request.definition.objectFlags;
        projectile.visualMode = request.definition.visualMode;
        projectile.radius = request.definition.radius;
        projectile.height = request.definition.height;
        projectile.spellId = request.definition.spellId;
        projectile.effectSoundId = request.definition.effectSoundId;
        projectile.impactSoundIdOverride = request.impactSoundIdOverride;
        projectile.skillLevel = request.skillLevel;
        projectile.skillMastery = request.skillMastery;
        projectile.objectName = request.definition.objectName;
        projectile.objectSpriteName = request.definition.objectSpriteName;
        projectile.sourceX = request.sourceX;
        projectile.sourceY = request.sourceY;
        projectile.sourceZ = request.sourceZ;
        projectile.x = request.sourceX;
        projectile.y = request.sourceY;
        projectile.z = request.sourceZ;
        projectile.damage = request.damage;
        projectile.attackBonus = request.attackBonus;
        projectile.damageType = request.damageType;
        projectile.shieldTier = request.shieldTier;
        projectile.shieldModifiers = request.shieldModifiers;
        projectile.weakerOfPhysicalAndFire = request.weakerOfPhysicalAndFire;
        projectile.explosionRadius = request.explosionRadius;
        projectile.critical = request.critical;
        projectile.useActorHitChance = request.useActorHitChance;
        projectile.turnBasedPendingAction = request.turnBasedPendingAction;
        projectile.lifetimeTicks = request.definition.lifetimeTicks;
        projectile.sectorId = request.sectorId;

        result.kind = ProjectileSpawnResult::Kind::InstantImpact;
        result.projectile = std::move(projectile);
        result.speed = request.definition.speed;
        traceProjectileSpawnResult("instant_impact", result.projectile, 0.0f, 0.0f, 0.0f, result.speed);
        return result;
    }

    const float directionX = deltaX / distance;
    const float directionY = deltaY / distance;
    const float directionZ = deltaZ / distance;
    const float spawnForwardOffset = std::clamp(request.spawnForwardOffset, 0.0f, distance);

    ProjectileState projectile = {};
    projectile.projectileId = allocateProjectileId();
    projectile.sourceKind = request.sourceKind;
    projectile.sourceId = request.sourceId;
    projectile.sourcePartyMemberIndex = request.sourcePartyMemberIndex;
    projectile.sourceMonsterId = request.sourceMonsterId;
    projectile.fromSummonedMonster = request.fromSummonedMonster;
    projectile.ability = request.ability;
    projectile.objectDescriptionId = request.definition.objectDescriptionId;
    projectile.objectSpriteId = request.definition.objectSpriteId;
    projectile.objectSpriteFrameIndex = request.definition.objectSpriteFrameIndex;
    projectile.impactObjectDescriptionId = request.definition.impactObjectDescriptionId;
    projectile.objectFlags = request.definition.objectFlags;
    projectile.visualMode = request.definition.visualMode;
    projectile.radius = request.definition.radius;
    projectile.height = request.definition.height;
    projectile.spellId = request.definition.spellId;
    projectile.effectSoundId = request.definition.effectSoundId;
    projectile.impactSoundIdOverride = request.impactSoundIdOverride;
    projectile.skillLevel = request.skillLevel;
    projectile.skillMastery = request.skillMastery;
    projectile.objectName = request.definition.objectName;
    projectile.objectSpriteName = request.definition.objectSpriteName;
    projectile.sourceX = request.sourceX;
    projectile.sourceY = request.sourceY;
    projectile.sourceZ = request.sourceZ;
    projectile.x = request.sourceX + directionX * spawnForwardOffset;
    projectile.y = request.sourceY + directionY * spawnForwardOffset;
    projectile.z = request.sourceZ + directionZ * spawnForwardOffset;
    float speed = request.definition.speed;
    projectile.lifetimeTicks = request.definition.lifetimeTicks;

    if (request.eventMissile)
    {
        // Whole ticks of flight, the speed fitted to them, so the flight ends on the target.
        const float flightDistance = distance - spawnForwardOffset;
        const float flightSeconds =
            request.flightSeconds > 0.0f ? request.flightSeconds : flightDistance / std::max(speed, 1.0f);
        projectile.lifetimeTicks = std::max<uint32_t>(1, uint32_t(std::ceil(flightSeconds * ProjectileTicksPerSecond)));
        speed = flightDistance * ProjectileTicksPerSecond / float(projectile.lifetimeTicks);
        projectile.eventMissile = true;
        projectile.targetX = request.targetX;
        projectile.targetY = request.targetY;
        projectile.targetZ = request.targetZ;
    }

    projectile.velocityX = directionX * speed;
    projectile.velocityY = directionY * speed;
    projectile.velocityZ = directionZ * speed;
    projectile.damage = request.damage;
    projectile.attackBonus = request.attackBonus;
    projectile.damageType = request.damageType;
    projectile.shieldTier = request.shieldTier;
    projectile.shieldModifiers = request.shieldModifiers;
    projectile.weakerOfPhysicalAndFire = request.weakerOfPhysicalAndFire;
    projectile.explosionRadius = request.explosionRadius;
    projectile.critical = request.critical;
    projectile.useActorHitChance = request.useActorHitChance;
    projectile.turnBasedPendingAction = request.turnBasedPendingAction;
    projectile.sectorId = request.sectorId;

    m_projectiles.push_back(std::move(projectile));

    result.kind = ProjectileSpawnResult::Kind::SpawnedProjectile;
    result.projectile = m_projectiles.back();
    result.directionX = directionX;
    result.directionY = directionY;
    result.directionZ = directionZ;
    result.speed = speed;
    traceProjectileSpawnResult("spawned", result.projectile, directionX, directionY, directionZ, result.speed);
    return result;
}

GameplayProjectileService::ProjectileSpawnEffects
GameplayProjectileService::buildProjectileSpawnEffects(const ProjectileSpawnResult &result) const
{
    return buildProjectileSpawnEffects(result, true);
}

GameplayProjectileService::ProjectileSpawnEffects
GameplayProjectileService::buildProjectileSpawnEffects(
    const ProjectileSpawnResult &result,
    bool playReleaseAudio) const
{
    ProjectileSpawnEffects effects = {};

    if (result.kind == ProjectileSpawnResult::Kind::FailedZeroDistance)
    {
        return effects;
    }

    effects.accepted = true;

    if (result.kind == ProjectileSpawnResult::Kind::InstantImpact)
    {
        effects.spawnInstantImpact = true;
        effects.impactX = result.projectile.sourceX;
        effects.impactY = result.projectile.sourceY;
        effects.impactZ = result.projectile.sourceZ;
        return effects;
    }

    if (playReleaseAudio)
    {
        effects.releaseAudioRequest = buildProjectileReleaseAudioRequest(
            result.projectile,
            result.projectile.sourceX,
            result.projectile.sourceY,
            result.projectile.sourceZ);
        effects.playReleaseAudio = effects.releaseAudioRequest.has_value();
    }

    effects.logSpawn = true;
    return effects;
}

std::vector<GameplayProjectileService::AreaSpellProjectileShot>
GameplayProjectileService::buildMeteorShowerProjectileShots(
    uint32_t skillMastery,
    uint32_t nextProjectileId,
    float targetX,
    float targetY,
    float targetZ) const
{
    const uint32_t projectileCount = meteorShowerProjectileCountForMastery(skillMastery);
    std::mt19937 rng(areaSpellProjectileSeed(SpellId::MeteorShower, nextProjectileId, targetX, targetY, targetZ));
    std::uniform_real_distribution<float> targetOffsetDistribution(
        -MeteorShowerTargetSpread,
        MeteorShowerTargetSpread);
    std::uniform_real_distribution<float> spawnHeightDistribution(
        MeteorShowerSpawnBaseHeight,
        MeteorShowerSpawnBaseHeight + MeteorShowerSpawnHeightVariance);

    std::vector<AreaSpellProjectileShot> shots;
    shots.reserve(projectileCount);

    for (uint32_t projectileIndex = 0; projectileIndex < projectileCount; ++projectileIndex)
    {
        AreaSpellProjectileShot shot = {};
        shot.targetX = targetX + targetOffsetDistribution(rng);
        shot.targetY = targetY + targetOffsetDistribution(rng);
        shot.targetZ = targetZ;
        shot.sourceX = shot.targetX;
        shot.sourceY = shot.targetY;
        shot.sourceHeightOffset = spawnHeightDistribution(rng);
        shots.push_back(shot);
    }

    return shots;
}

std::vector<GameplayProjectileService::AreaSpellProjectileShot>
GameplayProjectileService::buildStarburstProjectileShots(
    uint32_t nextProjectileId,
    float targetX,
    float targetY,
    float targetZ) const
{
    std::mt19937 rng(areaSpellProjectileSeed(SpellId::Starburst, nextProjectileId, targetX, targetY, targetZ));
    std::uniform_real_distribution<float> targetOffsetDistribution(-StarburstTargetSpread, StarburstTargetSpread);
    std::uniform_real_distribution<float> spawnHeightDistribution(
        StarburstSpawnBaseHeight,
        StarburstSpawnBaseHeight + StarburstSpawnHeightVariance);

    std::vector<AreaSpellProjectileShot> shots;
    shots.reserve(StarburstProjectileCount);

    for (uint32_t projectileIndex = 0; projectileIndex < StarburstProjectileCount; ++projectileIndex)
    {
        AreaSpellProjectileShot shot = {};
        shot.sourceX = targetX;
        shot.sourceY = targetY;
        shot.targetX = targetX + targetOffsetDistribution(rng);
        shot.targetY = targetY + targetOffsetDistribution(rng);
        shot.targetZ = targetZ;
        shot.sourceHeightOffset = spawnHeightDistribution(rng);
        shots.push_back(shot);
    }

    return shots;
}

const GameplayProjectileService::ProjectileImpactState &GameplayProjectileService::addProjectileImpact(
    ProjectileImpactState impact)
{
    impact.effectId = allocateProjectileImpactId();
    m_projectileImpacts.push_back(std::move(impact));
    return m_projectileImpacts.back();
}

std::vector<GameplayProjectileService::ProjectileState> &GameplayProjectileService::projectiles()
{
    return m_projectiles;
}

const std::vector<GameplayProjectileService::ProjectileState> &GameplayProjectileService::projectiles() const
{
    return m_projectiles;
}

std::vector<GameplayProjectileService::ProjectileImpactState> &GameplayProjectileService::projectileImpacts()
{
    return m_projectileImpacts;
}

const std::vector<GameplayProjectileService::ProjectileImpactState> &
GameplayProjectileService::projectileImpacts() const
{
    return m_projectileImpacts;
}

GameplayProjectileVisualMode GameplayProjectileService::monsterProjectileVisualModeForObjectId(int objectId)
{
    switch (objectId)
    {
        case 500:
        case 505:
        case 510:
        case 515:
        case 520:
        case 525:
        case 530:
        case 535:
        case 540:
        case 2060:
        case 3030:
            return GameplayProjectileVisualMode::FxOnly;

        default:
            return GameplayProjectileVisualMode::SpriteBillboard;
    }
}

bool GameplayProjectileService::projectileVisualModeUsesDedicatedFxImpact(const ProjectileState &projectile)
{
    if (projectile.visualMode != GameplayProjectileVisualMode::FxOnly)
    {
        return false;
    }

    const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
        projectile.spellId,
        projectile.objectName,
        projectile.objectSpriteName,
        projectile.objectFlags);
    return FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe);
}

void GameplayProjectileService::advanceProjectileImpactLifetimes(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    for (ProjectileImpactState &impact : m_projectileImpacts)
    {
        if (impact.isExpired)
        {
            continue;
        }

        impact.lifetimeTickAccumulator += deltaSeconds * ProjectileTicksPerSecond;
        const uint32_t deltaTicks = static_cast<uint32_t>(std::floor(impact.lifetimeTickAccumulator));

        if (deltaTicks == 0)
        {
            continue;
        }

        impact.lifetimeTickAccumulator -= static_cast<float>(deltaTicks);
        impact.timeSinceCreatedTicks += deltaTicks;

        if (impact.timeSinceCreatedTicks >= impact.lifetimeTicks)
        {
            impact.isExpired = true;
        }
    }
}

void GameplayProjectileService::updateProjectileImpactPresentation(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    advanceProjectileImpactLifetimes(deltaSeconds);
    eraseExpiredProjectileImpacts();
}

bool GameplayProjectileService::advanceProjectileLifetime(
    ProjectileState &projectile,
    float deltaSeconds) const
{
    if (deltaSeconds <= 0.0f || projectile.isExpired)
    {
        return projectile.isExpired;
    }

    projectile.lifetimeTickAccumulator += deltaSeconds * ProjectileTicksPerSecond;

    const uint32_t deltaTicks = static_cast<uint32_t>(std::floor(projectile.lifetimeTickAccumulator));

    if (deltaTicks == 0)
    {
        return false;
    }

    projectile.lifetimeTickAccumulator -= static_cast<float>(deltaTicks);
    projectile.timeSinceCreatedTicks += deltaTicks;
    return projectile.timeSinceCreatedTicks >= projectile.lifetimeTicks;
}

bool GameplayProjectileService::holdsTurnBasedQueue(const ProjectileState &projectile)
{
    constexpr uint32_t TurnBasedWaitTicks = 2 * 128;
    return projectile.turnBasedPendingAction
        && !projectile.isExpired
        && !projectile.isSettled
        && projectile.timeSinceCreatedTicks < TurnBasedWaitTicks;
}

GameplayProjectileService::ProjectileMotionSegment GameplayProjectileService::advanceProjectileMotion(
    ProjectileState &projectile,
    float deltaSeconds,
    float gravity) const
{
    ProjectileMotionSegment segment = {};
    segment.startX = projectile.x;
    segment.startY = projectile.y;
    segment.startZ = projectile.z;

    if (deltaSeconds <= 0.0f || projectile.isExpired)
    {
        segment.endX = projectile.x;
        segment.endY = projectile.y;
        segment.endZ = projectile.z;
        return segment;
    }

    if ((projectile.objectFlags & ObjectDescNoGravity) == 0)
    {
        projectile.velocityZ -= gravity * deltaSeconds;
    }

    segment.endX = projectile.x + projectile.velocityX * deltaSeconds;
    segment.endY = projectile.y + projectile.velocityY * deltaSeconds;
    segment.endZ = projectile.z + projectile.velocityZ * deltaSeconds;
    return segment;
}

void GameplayProjectileService::applyProjectileMotionEnd(
    ProjectileState &projectile,
    const ProjectileMotionSegment &motionSegment) const
{
    if (projectile.isExpired)
    {
        return;
    }

    projectile.x = motionSegment.endX;
    projectile.y = motionSegment.endY;
    projectile.z = motionSegment.endZ;

    GAMEPLAY_PROJECTILE_TRACE_BLOCK(
        std::ostringstream trace;
        trace << "projectile_apply_motion_end";
        appendProjectileTraceSummary(trace, projectile);
        appendProjectileTracePoint(
            trace,
            "motion_start",
            motionSegment.startX,
            motionSegment.startY,
            motionSegment.startZ);
        appendProjectileTracePoint(trace, "motion_end", motionSegment.endX, motionSegment.endY, motionSegment.endZ);
        gameplayProjectileTraceWrite(trace.str());
    );
}

void GameplayProjectileService::applyProjectileBounce(
    ProjectileState &projectile,
    float impactX,
    float impactY,
    float impactZ,
    float normalX,
    float normalY,
    float normalZ,
    float bounceFactor,
    float stopVelocity,
    float groundDamping) const
{
    const float previousX = projectile.x;
    const float previousY = projectile.y;
    const float previousZ = projectile.z;
    const float previousVelocityX = projectile.velocityX;
    const float previousVelocityY = projectile.velocityY;
    const float previousVelocityZ = projectile.velocityZ;
    const float velocityDotNormal =
        projectile.velocityX * normalX
        + projectile.velocityY * normalY
        + projectile.velocityZ * normalZ;

    projectile.x = impactX + normalX * 2.0f;
    projectile.y = impactY + normalY * 2.0f;
    projectile.z = impactZ + normalZ * 2.0f;
    projectile.velocityX = (projectile.velocityX - 2.0f * velocityDotNormal * normalX) * bounceFactor;
    projectile.velocityY = (projectile.velocityY - 2.0f * velocityDotNormal * normalY) * bounceFactor;
    projectile.velocityZ = (projectile.velocityZ - 2.0f * velocityDotNormal * normalZ) * bounceFactor;

    if (std::abs(projectile.velocityZ) < stopVelocity)
    {
        projectile.velocityZ = 0.0f;
    }

    projectile.velocityX *= groundDamping;
    projectile.velocityY *= groundDamping;

    GAMEPLAY_PROJECTILE_TRACE_BLOCK(
        std::ostringstream trace;
        trace << "projectile_apply_bounce";
        appendProjectileTraceSummary(trace, projectile);
        appendProjectileTracePoint(trace, "previous_pos", previousX, previousY, previousZ);
        appendProjectileTracePoint(trace, "previous_vel", previousVelocityX, previousVelocityY, previousVelocityZ);
        appendProjectileTracePoint(trace, "impact", impactX, impactY, impactZ);
        appendProjectileTracePoint(trace, "normal", normalX, normalY, normalZ);
        trace
            << " velocity_dot_normal=" << velocityDotNormal
            << " bounce_factor=" << bounceFactor
            << " stop_velocity=" << stopVelocity
            << " ground_damping=" << groundDamping;
        gameplayProjectileTraceWrite(trace.str());
    );
}

void GameplayProjectileService::settleProjectile(ProjectileState &projectile) const
{
    projectile.velocityX = 0.0f;
    projectile.velocityY = 0.0f;
    projectile.velocityZ = 0.0f;
    projectile.isSettled = true;

    GAMEPLAY_PROJECTILE_TRACE_BLOCK(
        std::ostringstream trace;
        trace << "projectile_settle";
        appendProjectileTraceSummary(trace, projectile);
        gameplayProjectileTraceWrite(trace.str());
    );
}

std::optional<GameplayProjectileService::ProjectileSpawnRequest> GameplayProjectileService::buildChainSpawnRequest(
    const ProjectileState &projectile,
    const CombatRules &rules,
    const IGameplayWorldRuntime &world,
    size_t struckActorIndex) const
{
    constexpr float ChainRange = 768.0f;
    constexpr float FallbackSpeed = 2000.0f;

    if (projectile.sourceKind != ProjectileState::SourceKind::Party || projectile.spellId == 0)
    {
        return std::nullopt;
    }

    const std::optional<SkillMastery> nextMastery =
        rules.spellChainMastery(projectile.spellId, SkillMastery(projectile.skillMastery));
    GameplayRuntimeActorState struck = {};

    if (!nextMastery || !world.actorRuntimeState(struckActorIndex, struck))
    {
        return std::nullopt;
    }

    const float fromZ = struck.preciseZ + float(struck.height) * 0.5f;
    std::optional<GameplayRuntimeActorState> target;
    float targetDistance = ChainRange;

    for (size_t actorIndex = 0; actorIndex < world.mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actor = {};

        if (actorIndex == struckActorIndex || !world.actorRuntimeState(actorIndex, actor) || actor.isDead
            || actor.currentHp <= 0 || !actor.hostileToParty)
        {
            continue;
        }

        const float distance = std::sqrt(std::pow(actor.preciseX - struck.preciseX, 2.0f)
            + std::pow(actor.preciseY - struck.preciseY, 2.0f)
            + std::pow(actor.preciseZ + float(actor.height) * 0.5f - fromZ, 2.0f));

        if (distance <= targetDistance)
        {
            target = actor;
            targetDistance = distance;
        }
    }

    if (!target)
    {
        return std::nullopt;
    }

    ProjectileSpawnRequest request = {};
    request.sourceKind = projectile.sourceKind;
    request.sourceId = projectile.sourceId;
    request.sourcePartyMemberIndex = projectile.sourcePartyMemberIndex;
    request.definition.objectDescriptionId = projectile.objectDescriptionId;
    request.definition.objectSpriteId = projectile.objectSpriteId;
    request.definition.objectSpriteFrameIndex = projectile.objectSpriteFrameIndex;
    request.definition.impactObjectDescriptionId = projectile.impactObjectDescriptionId;
    request.definition.objectFlags = projectile.objectFlags;
    request.definition.visualMode = projectile.visualMode;
    request.definition.radius = projectile.radius;
    request.definition.height = projectile.height;
    request.definition.spellId = projectile.spellId;
    request.definition.lifetimeTicks = projectile.lifetimeTicks;
    request.definition.objectName = projectile.objectName;
    request.definition.objectSpriteName = projectile.objectSpriteName;
    const float speed = std::sqrt(projectile.velocityX * projectile.velocityX
        + projectile.velocityY * projectile.velocityY + projectile.velocityZ * projectile.velocityZ);
    request.definition.speed = speed > 1.0f ? speed : FallbackSpeed;
    request.skillLevel = projectile.skillLevel;
    request.skillMastery = uint32_t(*nextMastery);
    request.damage = projectile.damage;
    request.attackBonus = projectile.attackBonus;
    request.damageType = projectile.damageType;
    request.shieldTier = projectile.shieldTier;
    request.shieldModifiers = projectile.shieldModifiers;
    request.weakerOfPhysicalAndFire = projectile.weakerOfPhysicalAndFire;
    request.explosionRadius = projectile.explosionRadius;
    request.critical = projectile.critical;
    request.sourceX = struck.preciseX;
    request.sourceY = struck.preciseY;
    request.sourceZ = fromZ;
    request.targetX = target->preciseX;
    request.targetY = target->preciseY;
    request.targetZ = target->preciseZ + float(target->height) * 0.5f;
    // Leave the struck monster before flying on.
    request.spawnForwardOffset = float(struck.radius) + float(projectile.radius) + 8.0f;
    request.sectorId = projectile.sectorId;
    request.allowInstantImpact = true;
    return request;
}

std::vector<GameplayProjectileService::ProjectileSpawnRequest>
GameplayProjectileService::buildDeathBlossomFalloutSpawnRequests(
    const ProjectileState &projectile,
    const ProjectileDefinition &shardDefinition,
    float x,
    float y,
    float z) const
{
    std::vector<ProjectileSpawnRequest> requests;
    requests.reserve(DeathBlossomFalloutShardCount);

    ProjectileDefinition definition = shardDefinition;
    definition.spellId = spellIdValue(SpellId::DeathBlossom);
    definition.effectSoundId = 0;

    std::mt19937 rng(
        projectile.projectileId
        ^ static_cast<uint32_t>(std::lround(std::abs(x)))
        ^ (static_cast<uint32_t>(std::lround(std::abs(y))) << 1));
    std::uniform_real_distribution<float> yawJitter(
        -DeathBlossomFalloutYawJitter,
        DeathBlossomFalloutYawJitter);
    std::uniform_real_distribution<float> launchSpeed(DeathBlossomFalloutMinSpeed, DeathBlossomFalloutMaxSpeed);
    const float angleStep = (2.0f * Pi) / static_cast<float>(DeathBlossomFalloutShardCount);

    for (uint32_t shardIndex = 0; shardIndex < DeathBlossomFalloutShardCount; ++shardIndex)
    {
        const float yaw = angleStep * static_cast<float>(shardIndex) + yawJitter(rng);
        // Only the direction of the target matters: the shard flies level at its own speed.
        const float distance = SpellImpactAoeRadius;

        ProjectileSpawnRequest request = {};
        request.sourceKind = projectile.sourceKind;
        request.sourceId = projectile.sourceId;
        request.sourcePartyMemberIndex = projectile.sourcePartyMemberIndex;
        request.sourceMonsterId = projectile.sourceMonsterId;
        request.fromSummonedMonster = projectile.fromSummonedMonster;
        request.ability = projectile.ability;
        request.definition = definition;
        request.definition.speed = launchSpeed(rng);
        request.skillLevel = projectile.skillLevel;
        request.skillMastery = projectile.skillMastery;
        request.damage = projectile.damage;
        request.attackBonus = projectile.attackBonus;
        request.damageType = projectile.damageType;
        request.critical = projectile.critical;
        request.sourceX = x;
        request.sourceY = y;
        request.sourceZ = z + DeathBlossomFalloutSourceHeightOffset;
        request.targetX = x + std::cos(yaw) * distance;
        request.targetY = y + std::sin(yaw) * distance;
        request.targetZ = request.sourceZ;
        request.sectorId = projectile.sectorId;
        request.allowInstantImpact = true;
        requests.push_back(std::move(request));
    }

    return requests;
}

std::vector<GameplayProjectileService::ProjectileSpawnResult>
GameplayProjectileService::spawnDeathBlossomFalloutProjectiles(
    const ProjectileState &projectile,
    const ProjectileDefinition &shardDefinition,
    float x,
    float y,
    float z)
{
    const std::vector<ProjectileSpawnRequest> requests =
        buildDeathBlossomFalloutSpawnRequests(projectile, shardDefinition, x, y, z);
    std::vector<ProjectileSpawnResult> results;
    results.reserve(requests.size());

    for (const ProjectileSpawnRequest &request : requests)
    {
        ProjectileSpawnResult result = spawnProjectile(request);

        if (result.kind == ProjectileSpawnResult::Kind::FailedZeroDistance)
        {
            continue;
        }

        results.push_back(std::move(result));
    }

    return results;
}

bool GameplayProjectileService::shouldSpawnProjectileImpactVisual(
    const ProjectileState &projectile,
    const ProjectileImpactVisualDefinition &definition) const
{
    const FxRecipes::ProjectileRecipe impactRecipe = FxRecipes::classifyProjectileRecipe(
        projectile.spellId,
        projectile.objectName,
        projectile.objectSpriteName,
        projectile.objectFlags);
    return definition.hasVisual || FxRecipes::projectileRecipeUsesDedicatedImpactFx(impactRecipe);
}

GameplayProjectileService::ProjectileImpactVisualDefinition
GameplayProjectileService::buildProjectileImpactVisualDefinition(
    uint16_t objectDescriptionId,
    const ObjectEntry &objectEntry,
    const SpriteFrameTable *pSpriteFrameTable) const
{
    ProjectileImpactVisualDefinition definition = {};
    definition.objectDescriptionId = objectDescriptionId;
    definition.objectSpriteId = objectEntry.spriteId;
    definition.objectSpriteFrameIndex =
        resolveProjectileSpriteFrameIndex(pSpriteFrameTable, objectEntry.spriteId, objectEntry.spriteName);
    definition.objectHeight = objectEntry.height;
    definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(objectEntry.lifetimeTicks, 32));
    definition.hasVisual = objectEntry.spriteId != 0 || !objectEntry.spriteName.empty();
    if (pSpriteFrameTable != nullptr && definition.objectSpriteFrameIndex != 0)
    {
        const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(definition.objectSpriteFrameIndex, 0);
        definition.centerAnchored =
            pFrame != nullptr && SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::Center);
    }
    definition.objectName = objectEntry.internalName;
    definition.objectSpriteName = objectEntry.spriteName;
    return definition;
}

std::optional<GameplayProjectileService::ProjectileImpactVisualDefinition>
GameplayProjectileService::buildProjectileImpactVisualDefinition(
    uint16_t objectDescriptionId,
    const ObjectTable *pObjectTable,
    const SpriteFrameTable *pSpriteFrameTable) const
{
    if (pObjectTable == nullptr || objectDescriptionId == 0)
    {
        return std::nullopt;
    }

    const ObjectEntry *pObjectEntry = pObjectTable->get(objectDescriptionId);

    if (pObjectEntry == nullptr)
    {
        return std::nullopt;
    }

    return buildProjectileImpactVisualDefinition(objectDescriptionId, *pObjectEntry, pSpriteFrameTable);
}

std::optional<GameplayProjectileService::ProjectileImpactVisualDefinition>
GameplayProjectileService::buildWaterSplashImpactVisualDefinition(
    const ObjectTable *pObjectTable,
    const SpriteFrameTable *pSpriteFrameTable) const
{
    if (pObjectTable == nullptr)
    {
        return std::nullopt;
    }

    const std::optional<uint16_t> objectDescriptionId =
        pObjectTable->findDescriptionIdByObjectId(waterSplashObjectId());

    if (!objectDescriptionId)
    {
        return std::nullopt;
    }

    return buildProjectileImpactVisualDefinition(*objectDescriptionId, pObjectTable, pSpriteFrameTable);
}

GameplayProjectileService::ProjectileImpactSpawnResult
GameplayProjectileService::spawnProjectileImpactVisual(
    const ProjectileState &projectile,
    const ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z,
    bool centerVertically,
    size_t targetActorIndex)
{
    ProjectileImpactSpawnResult result = {};

    if (!shouldSpawnProjectileImpactVisual(projectile, definition))
    {
        return result;
    }

    ProjectileImpactState impactState = {};
    impactState.objectDescriptionId = definition.objectDescriptionId;
    impactState.objectSpriteId = definition.objectSpriteId;
    impactState.objectSpriteFrameIndex = definition.objectSpriteFrameIndex;
    impactState.sourceObjectFlags = projectile.objectFlags;
    impactState.sourceSpellId = projectile.spellId;
    impactState.sourceMonsterId = projectile.sourceMonsterId;
    const float speed = std::sqrt(projectile.velocityX * projectile.velocityX
        + projectile.velocityY * projectile.velocityY + projectile.velocityZ * projectile.velocityZ);
    if (speed > 0.0f)
    {
        impactState.flightDirectionX = projectile.velocityX / speed;
        impactState.flightDirectionY = projectile.velocityY / speed;
        impactState.flightDirectionZ = projectile.velocityZ / speed;
    }
    impactState.objectName = definition.objectName;
    impactState.objectSpriteName = definition.objectSpriteName;
    impactState.sourceObjectName = projectile.objectName;
    impactState.sourceObjectSpriteName = projectile.objectSpriteName;
    impactState.x = x;
    impactState.y = y;
    impactState.z = centerVertically && !definition.centerAnchored
        ? z - static_cast<float>(std::max<int16_t>(definition.objectHeight, 0)) * 0.5f
        : z;
    impactState.lifetimeTicks = definition.lifetimeTicks;
    impactState.sectorId = projectile.sectorId;
    impactState.targetActorIndex = targetActorIndex;

    const ProjectileImpactState &impact = addProjectileImpact(std::move(impactState));
    result.spawned = true;
    result.pImpact = &impact;
    return result;
}

GameplayProjectileService::ProjectileImpactSpawnResult
GameplayProjectileService::spawnWaterSplashImpactVisual(
    const ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z)
{
    ProjectileImpactSpawnResult result = {};
    ProjectileImpactState impactState = {};
    impactState.objectDescriptionId = definition.objectDescriptionId;
    impactState.objectSpriteId = definition.objectSpriteId;
    impactState.objectSpriteFrameIndex = definition.objectSpriteFrameIndex;
    impactState.objectName = definition.objectName;
    impactState.objectSpriteName = definition.objectSpriteName;
    impactState.x = x;
    impactState.y = y;
    impactState.z = z;
    impactState.lifetimeTicks = definition.lifetimeTicks;

    const ProjectileImpactState &impact = addProjectileImpact(std::move(impactState));
    result.spawned = true;
    result.pImpact = &impact;
    return result;
}

GameplayProjectileService::ProjectileImpactSpawnResult
GameplayProjectileService::spawnImmediateSpellImpactVisual(
    const ProjectileImpactVisualDefinition &definition,
    int sourceSpellId,
    const std::string &sourceObjectName,
    const std::string &sourceObjectSpriteName,
    float x,
    float y,
    float z,
    bool centerVertically,
    bool freezeAnimation,
    size_t targetActorIndex)
{
    ProjectileImpactSpawnResult result = {};

    if (definition.objectDescriptionId == 0)
    {
        return result;
    }

    ProjectileImpactState impactState = {};
    impactState.objectDescriptionId = definition.objectDescriptionId;
    impactState.objectSpriteId = definition.objectSpriteId;
    impactState.objectSpriteFrameIndex = definition.objectSpriteFrameIndex;
    impactState.sourceSpellId = sourceSpellId;
    impactState.objectName = definition.objectName;
    impactState.objectSpriteName = definition.objectSpriteName;
    impactState.sourceObjectName = sourceObjectName;
    impactState.sourceObjectSpriteName = sourceObjectSpriteName;
    impactState.x = x;
    impactState.y = y;
    impactState.z = centerVertically && !definition.centerAnchored
        ? z - static_cast<float>(std::max<int16_t>(definition.objectHeight, 0)) * 0.5f
        : z;
    impactState.lifetimeTicks = definition.lifetimeTicks;
    impactState.freezeAnimation = freezeAnimation;
    impactState.targetActorIndex = targetActorIndex;

    const ProjectileImpactState &impact = addProjectileImpact(std::move(impactState));
    result.spawned = true;
    result.pImpact = &impact;
    return result;
}

std::optional<GameplayProjectileService::ProjectileAudioRequest>
GameplayProjectileService::buildProjectileReleaseAudioRequest(
    const ProjectileState &projectile,
    float x,
    float y,
    float z) const
{
    if (projectile.effectSoundId <= 0)
    {
        return std::nullopt;
    }

    ProjectileAudioRequest request = {};
    request.soundId = static_cast<uint32_t>(projectile.effectSoundId);
    request.sourceId = projectile.sourceId;
    request.x = x;
    request.y = y;
    request.z = z;

    switch (projectile.sourceKind)
    {
        case ProjectileState::SourceKind::Event:
            request.reason = "event_spell_release";
            break;

        case ProjectileState::SourceKind::Party:
            request.reason = "party_spell_release";
            break;

        case ProjectileState::SourceKind::Actor:
            request.reason = "monster_spell_release";
            break;
    }

    return request;
}

std::optional<GameplayProjectileService::ProjectileAudioRequest>
GameplayProjectileService::buildProjectileImpactAudioRequest(
    const ProjectileState &projectile,
    float x,
    float y,
    float z) const
{
    if (projectile.spellId <= 0 || projectile.effectSoundId <= 0)
    {
        if (projectile.impactSoundIdOverride == 0)
        {
            return std::nullopt;
        }
    }

    ProjectileAudioRequest request = {};
    request.soundId =
        projectile.impactSoundIdOverride != 0
            ? projectile.impactSoundIdOverride
            : static_cast<uint32_t>(projectile.effectSoundId + 1);
    request.sourceId = projectile.sourceId;
    request.x = x;
    request.y = y;
    request.z = z;

    switch (projectile.sourceKind)
    {
        case ProjectileState::SourceKind::Event:
            request.reason = "event_spell_impact";
            break;

        case ProjectileState::SourceKind::Party:
            request.reason = "party_spell_impact";
            break;

        case ProjectileState::SourceKind::Actor:
            request.reason = "monster_spell_impact";
            break;
    }

    const FxRecipes::ProjectileRecipe impactRecipe = FxRecipes::classifyProjectileRecipe(
        projectile.spellId,
        projectile.objectName,
        projectile.objectSpriteName,
        projectile.objectFlags);

    if (impactRecipe == FxRecipes::ProjectileRecipe::MeteorShower)
    {
        request.reason = "meteor_shower_impact";
    }
    else if (impactRecipe == FxRecipes::ProjectileRecipe::Starburst)
    {
        request.reason = "starburst_impact";
    }

    return request;
}

std::optional<GameplayProjectileService::ProjectileAudioRequest>
GameplayProjectileService::buildWaterSplashAudioRequest(float x, float y, float z) const
{
    ProjectileAudioRequest request = {};
    request.soundId = static_cast<uint32_t>(SoundId::Splash);
    request.reason = "water_splash";
    request.x = x;
    request.y = y;
    request.z = z;
    return request;
}

int GameplayProjectileService::resolveProjectilePartyImpactDamage(
    const ProjectilePartyImpactDamageInput &input) const
{
    if (input.sourceKind == ProjectileState::SourceKind::Party)
    {
        return std::max(1, input.projectileDamage);
    }

    if (input.eventSource)
    {
        // An event's missile carries its own damage; an event's spell rolls the spell's.
        return input.spellId == 0 ? std::max(0, input.projectileDamage)
                                  : resolveEventProjectileDamage(input.spellId, input.skillLevel);
    }

    if (input.sourceKind == ProjectileState::SourceKind::Actor && input.projectileDamage > 0)
    {
        return input.projectileDamage;
    }

    if (!input.hasMonsterFacts)
    {
        return 1;
    }

    const int fallbackAttackDamage = std::max(1, input.monsterLevel / 2);

    switch (input.monsterAbility)
    {
        case MonsterAttackAbility::Attack2:
        {
            const int damage = rollMonsterProjectileDamage(input.attack2Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
        case MonsterAttackAbility::Spell1:
        case MonsterAttackAbility::Spell2:
            // Paralyze and Fear carry only their spell_conditions condition.
            if (isMonsterConditionSpellId(input.spellId))
            {
                return 0;
            }
            return std::max(1, rollMonsterSpellDamage(input.spellId,
                input.monsterAbility == MonsterAttackAbility::Spell1 ? input.spell1Damage : input.spell2Damage));
        case MonsterAttackAbility::Attack1:
        default:
        {
            const int damage = rollMonsterProjectileDamage(input.attack1Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
    }
}

int GameplayProjectileService::partyWorldSpellDamage(
    const Party *pParty,
    const SpellTable *pSpellTable,
    uint32_t sourcePartyMemberIndex,
    int spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    int trapRoll)
{
    const Character *pCaster = pParty != nullptr ? pParty->member(sourcePartyMemberIndex) : nullptr;
    const SpellEntry *pSpell = pSpellTable != nullptr ? pSpellTable->findById(spellId) : nullptr;

    if (pCaster == nullptr || pSpell == nullptr)
    {
        return trapRoll;
    }

    CharacterSpellCast cast;
    cast.pCaster = pCaster;
    cast.pItemTable = pParty->itemTable();
    cast.pStandardItemEnchantTable = pParty->standardItemEnchantTable();
    cast.pSpecialItemEnchantTable = pParty->specialItemEnchantTable();
    cast.pSpell = pSpell;
    cast.mastery = SkillMastery(skillMastery);
    cast.skillLevel = skillLevel;
    cast.partyCount = int(std::max<size_t>(1, pParty->members().size()));
    return pParty->rules().combat.worldSpellDamage(cast).value_or(trapRoll);
}

int GameplayProjectileService::resolvePartyProjectileDamageMultiplier(
    const ProjectileState &projectile,
    const Character *pSourceMember,
    const ItemTable *pItemTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    uint32_t targetMonsterKindFlags,
    const CombatRules &rules) const
{
    if (projectile.sourceKind != ProjectileState::SourceKind::Party
        || projectile.damage <= 0
        || projectile.spellId != 0
        || pSourceMember == nullptr
        || pItemTable == nullptr
        || !rules.weaponKindMultiplierApplies())
    {
        return 1;
    }

    return ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
        *pSourceMember,
        CharacterAttackMode::Bow,
        pItemTable,
        pSpecialItemEnchantTable,
        targetMonsterKindFlags);
}

GameplayProjectileService::ProjectileAreaImpact
GameplayProjectileService::buildProjectileAreaImpact(
    const ProjectileState &projectile,
    const ProjectileAreaImpactInput &input) const
{
    ProjectileAreaImpact impact = {};

    if (input.impactRadius <= 0.0f)
    {
        return impact;
    }

    const int impactDamage = projectile.sourceKind == ProjectileState::SourceKind::Party
        ? std::max(1, projectile.damage)
        : input.nonPartyProjectileDamage;

    if (input.canHitParty && !projectile.eventMissile)
    {
        const float partyCenterZ = input.partyZ + input.partyCollisionHeight * 0.5f;
        impact.hitParty = pointWithinExpandedCylinder(
            input.partyX,
            input.partyY,
            partyCenterZ,
            input.partyCollisionRadius,
            input.impactX,
            input.impactY,
            input.impactZ,
            input.impactRadius);
        impact.partyDamage = impactDamage;
    }

    impact.actorHits.reserve(input.actors.size());

    for (const ProjectileAreaImpactActorFacts &actor : input.actors)
    {
        if (actor.unavailableForCombat
            || actor.actorId == projectile.sourceId
            || actor.friendlyToProjectileSource
            || actor.directImpactActor)
        {
            continue;
        }

        const float actorCenterZ = actor.z + static_cast<float>(actor.height) * 0.5f;
        const float actorRadius = static_cast<float>(std::max<uint16_t>(actor.radius, 8));

        if (!pointWithinExpandedCylinder(
                actor.x,
                actor.y,
                actorCenterZ,
                actorRadius,
                input.impactX,
                input.impactY,
                input.impactZ,
                input.impactRadius))
        {
            continue;
        }

        ProjectileAreaImpactActorHit actorHit = {};
        actorHit.actorIndex = actor.actorIndex;
        actorHit.damage = impactDamage;
        impact.actorHits.push_back(actorHit);
    }

    return impact;
}

std::optional<int>
GameplayProjectileService::buildProjectileDirectPartyDamage(
    const ProjectileState &projectile,
    int nonPartyProjectileDamage) const
{
    if (projectile.sourceKind == ProjectileState::SourceKind::Party)
    {
        return std::nullopt;
    }

    return nonPartyProjectileDamage;
}

GameplayProjectileService::ProjectileDirectActorImpact
GameplayProjectileService::buildProjectileDirectActorImpact(
    const ProjectileState &projectile,
    const ProjectileDirectActorImpactInput &input) const
{
    ProjectileDirectActorImpact impact = {};
    impact.actorIndex = input.actorIndex;
    impact.actorId = input.actorId;

    if (projectile.sourceKind == ProjectileState::SourceKind::Party)
    {
        impact.damage = projectile.damage;
        const CombatRules &rules = input.pCombatRules != nullptr ? *input.pCombatRules : standardGameRules().combat;

        if (projectile.useActorHitChance)
        {
            std::mt19937 rng(
                projectile.projectileId
                ^ static_cast<uint32_t>(input.actorId * 2654435761u));
            impact.hit = rules.characterMissileHits(
                CharacterMissileOnMonster{
                    .attackBonus = projectile.attackBonus,
                    .targetArmorClass = input.targetArmorClass,
                    .targetDistance = input.targetDistance,
                    .targetFacts = input.targetFacts,
                    .partyCount = input.partyCount,
                    .pShooter = input.pShooter,
                    .pRng = &rng,
                });
        }

        if (impact.hit && impact.damage > 0)
        {
            impact.damage *= input.damageMultiplier;

            // A world enchantment's bonus against its monsters (Hesper's Kreegan-bane) on the shot's gun or bow.
            if (input.pShooter != nullptr && projectile.spellId == 0
                && input.pShooter->rangedWeaponEnchant.bonusAgainst(input.targetMonsterId))
            {
                impact.damage += impact.damage * input.pShooter->rangedWeaponEnchant.bonusDamagePercent / 100;
            }

            if (input.halfIncomingMissileDamage
                && rules.monsterShieldHalvesPartyMissile(uint32_t(std::max(0, projectile.spellId))))
            {
                impact.damage = std::max(1, (impact.damage + 1) / 2);
            }
        }

        impact.applyPartyProjectileDamage = impact.hit && impact.damage > 0;
        impact.queuePartyProjectileActorEvent = true;
        return impact;
    }

    impact.damage = input.nonPartyProjectileDamage;
    impact.applyNonPartyProjectileDamage = input.nonPartyProjectileDamage > 0;
    return impact;
}

void GameplayProjectileService::expireProjectile(
    ProjectileState &projectile,
    const std::optional<GameplayWorldPoint> &endPoint)
{
    if (projectile.isExpired)
    {
        return;
    }

    if (endPoint)
    {
        projectile.x = endPoint->x;
        projectile.y = endPoint->y;
        projectile.z = endPoint->z;
    }

    GAMEPLAY_PROJECTILE_TRACE_BLOCK(
        std::ostringstream trace;
        trace << "projectile_expire";
        appendProjectileTraceSummary(trace, projectile);
        gameplayProjectileTraceWrite(trace.str());
    );

    projectile.isExpired = true;
    m_endedProjectiles.push_back({projectile.projectileId, projectile.x, projectile.y, projectile.z});
}

size_t GameplayProjectileService::attachHoming(
    uint32_t firstProjectileId,
    uint32_t sourceActorId,
    const ProjectileHoming &homing)
{
    return attachHomingWhere(
        firstProjectileId,
        homing,
        [sourceActorId](const ProjectileState &projectile)
        {
            return projectile.sourceKind == ProjectileState::SourceKind::Actor && projectile.sourceId == sourceActorId;
        });
}

size_t GameplayProjectileService::attachPartyHoming(
    uint32_t firstProjectileId,
    uint32_t sourcePartyMemberIndex,
    const ProjectileHoming &homing)
{
    return attachHomingWhere(
        firstProjectileId,
        homing,
        [sourcePartyMemberIndex](const ProjectileState &projectile)
        {
            return projectile.sourceKind == ProjectileState::SourceKind::Party
                && projectile.sourcePartyMemberIndex == sourcePartyMemberIndex;
        });
}

size_t GameplayProjectileService::attachHomingWhere(
    uint32_t firstProjectileId,
    const ProjectileHoming &homing,
    const std::function<bool(const ProjectileState &)> &fromSource)
{
    size_t attached = 0;

    for (ProjectileState &projectile : m_projectiles)
    {
        if (projectile.projectileId < firstProjectileId
            || projectile.isExpired
            || projectile.isSettled
            || !fromSource(projectile))
        {
            continue;
        }

        const float speed = std::sqrt(projectile.velocityX * projectile.velocityX
            + projectile.velocityY * projectile.velocityY
            + projectile.velocityZ * projectile.velocityZ);

        if (speed <= 0.0f)
        {
            continue;
        }

        projectile.homing = homing;
        projectile.homing->speed = speed;
        projectile.homing->elapsedSeconds = 0.0f;
        projectile.homing->lost = false;
        ++attached;
    }

    return attached;
}

void GameplayProjectileService::recordHomingEnd(
    const ProjectileState &projectile,
    const ProjectileFrameResult &result)
{
    constexpr size_t MaxRecentHomingEnds = 32;

    if (!projectile.homing || !result.expireProjectile)
    {
        return;
    }

    HomingProjectileEnd end = {};
    end.projectileId = projectile.projectileId;
    end.sourceMonsterId = projectile.sourceMonsterId;
    end.stillHoming = !projectile.homing->lost;
    end.hit = result.directPartyDamage ? HomingProjectileEnd::Hit::Party
        : result.directActorImpact ? HomingProjectileEnd::Hit::Actor
        : result.wardBlock ? HomingProjectileEnd::Hit::Ward
        : result.logLifetimeExpiry ? HomingProjectileEnd::Hit::Expired
        : HomingProjectileEnd::Hit::World;
    end.point = result.endPoint.value_or(GameplayWorldPoint{projectile.x, projectile.y, projectile.z});

    if (m_recentHomingEnds.size() >= MaxRecentHomingEnds)
    {
        m_recentHomingEnds.erase(m_recentHomingEnds.begin());
    }

    m_recentHomingEnds.push_back(end);
}

bool GameplayProjectileService::steerVelocityToward(
    float &velocityX,
    float &velocityY,
    float &velocityZ,
    const GameplayWorldPoint &position,
    const GameplayWorldPoint &target,
    float speed,
    float maxTurnRadians)
{
    const float currentLength = std::sqrt(velocityX * velocityX + velocityY * velocityY + velocityZ * velocityZ);
    const float toX = target.x - position.x;
    const float toY = target.y - position.y;
    const float toZ = target.z - position.z;
    const float toLength = std::sqrt(toX * toX + toY * toY + toZ * toZ);

    if (currentLength <= 0.0001f || toLength <= 0.0001f || speed <= 0.0f)
    {
        return false;
    }

    // Unit vectors of the current heading and of the way to the target.
    const float cx = velocityX / currentLength;
    const float cy = velocityY / currentLength;
    const float cz = velocityZ / currentLength;
    const float dx = toX / toLength;
    const float dy = toY / toLength;
    const float dz = toZ / toLength;
    const float cosine = std::clamp(cx * dx + cy * dy + cz * dz, -1.0f, 1.0f);
    const float angle = std::acos(cosine);
    float nx = dx;
    float ny = dy;
    float nz = dz;

    if (angle > std::max(maxTurnRadians, 0.0f))
    {
        // Rotate the heading by maxTurnRadians about the axis perpendicular to both (any perpendicular axis when
        // the target lies straight behind).
        float ax = cy * dz - cz * dy;
        float ay = cz * dx - cx * dz;
        float az = cx * dy - cy * dx;
        float axisLength = std::sqrt(ax * ax + ay * ay + az * az);

        if (axisLength <= 0.0001f)
        {
            ax = -cy;
            ay = cx;
            az = 0.0f;
            axisLength = std::sqrt(ax * ax + ay * ay);

            if (axisLength <= 0.0001f)
            {
                ax = 1.0f;
                ay = 0.0f;
                az = 0.0f;
                axisLength = 1.0f;
            }
        }

        ax /= axisLength;
        ay /= axisLength;
        az /= axisLength;
        const float turnCosine = std::cos(maxTurnRadians);
        const float turnSine = std::sin(maxTurnRadians);
        // Rodrigues: c cos + (a x c) sin + a (a . c)(1 - cos), with a . c = 0.
        const float crossX = ay * cz - az * cy;
        const float crossY = az * cx - ax * cz;
        const float crossZ = ax * cy - ay * cx;
        nx = cx * turnCosine + crossX * turnSine;
        ny = cy * turnCosine + crossY * turnSine;
        nz = cz * turnCosine + crossZ * turnSine;
    }

    velocityX = nx * speed;
    velocityY = ny * speed;
    velocityZ = nz * speed;
    return true;
}

bool GameplayProjectileService::steerHomingProjectile(
    ProjectileState &projectile,
    const GameplayWorldPoint *pTarget,
    float deltaSeconds)
{
    if (!projectile.homing || projectile.isExpired || projectile.isSettled || deltaSeconds <= 0.0f)
    {
        return false;
    }

    ProjectileHoming &homing = *projectile.homing;

    if (homing.lost)
    {
        return false;
    }

    if (homing.maxSeconds > 0.0f && homing.elapsedSeconds >= homing.maxSeconds)
    {
        homing.lost = true;
        return homing.expireAfter;
    }

    homing.elapsedSeconds += deltaSeconds;

    if (pTarget == nullptr)
    {
        homing.lost = true;
        return false;
    }

    if (homing.lockRadiansPerSecond > 0.0f)
    {
        const float headingRadians = std::atan2(projectile.velocityY, projectile.velocityX);
        const float targetRadians = std::atan2(pTarget->y - projectile.y, pTarget->x - projectile.x);
        float offRadians = std::fabs(targetRadians - headingRadians);
        offRadians = std::min(offRadians, 2.0f * 3.14159265f - offRadians);

        if (offRadians >= homing.lockRadiansPerSecond * deltaSeconds)
        {
            return false;
        }
    }

    steerVelocityToward(
        projectile.velocityX,
        projectile.velocityY,
        projectile.velocityZ,
        {projectile.x, projectile.y, projectile.z},
        *pTarget,
        homing.speed,
        homing.turnRadiansPerSecond * deltaSeconds);
    return false;
}

GameplayProjectileService::ProjectileFrameResult GameplayProjectileService::updateProjectileFrame(
    ProjectileState &projectile,
    const ProjectileFrameFacts &facts) const
{
    ProjectileFrameResult result = {};
    if (advanceProjectileLifetime(projectile, facts.deltaSeconds))
    {
        const GameplayWorldPoint impactPoint = {projectile.x, projectile.y, projectile.z};

        if (isPrimaryDeathBlossomProjectile(projectile))
        {
            result.deathBlossomFalloutPoint = impactPoint;
        }
        else if (projectile.eventMissile
            || spellIdFromValue(static_cast<uint32_t>(projectile.spellId)) == SpellId::RockBlast)
        {
            // An event missile bursts on its target, Rock Blast where it lies.
            const GameplayWorldPoint burstPoint = projectile.eventMissile
                ? GameplayWorldPoint{projectile.targetX, projectile.targetY, projectile.targetZ}
                : impactPoint;
            const float impactRadius = projectile.eventMissile
                ? projectile.explosionRadius
                : spellImpactDamageRadius(static_cast<uint32_t>(projectile.spellId));

            if (impactRadius > 0.0f)
            {
                ProjectileAreaImpactInput areaInput = {};
                areaInput.impactX = burstPoint.x;
                areaInput.impactY = burstPoint.y;
                areaInput.impactZ = burstPoint.z;
                areaInput.impactRadius = impactRadius;
                areaInput.partyX = facts.partyPosition.x;
                areaInput.partyY = facts.partyPosition.y;
                areaInput.partyZ = facts.partyPosition.z;
                areaInput.partyCollisionRadius = facts.partyCollisionRadius;
                areaInput.partyCollisionHeight = facts.partyCollisionHeight;
                areaInput.canHitParty = facts.canHitParty;
                areaInput.nonPartyProjectileDamage = facts.nonPartyProjectileDamage;
                areaInput.actors = facts.areaActors;
                result.areaImpact = ProjectileFrameAreaImpactResult{
                    burstPoint,
                    impactRadius,
                    false,
                    buildProjectileAreaImpact(projectile, areaInput)};
            }

            result.fxRequest = ProjectileFrameFxRequest{
                ProjectileFrameFxKind::ProjectileImpact,
                burstPoint,
                false};
        }

        result.logLifetimeExpiry = true;
        result.expireProjectile = true;
        traceProjectileLifetimeExpired(projectile);
        return result;
    }

    // In turn-based mode a party shot the queue waits on is removed once it is more than 5120 from the party
    // (MM8 0x472d20; OE SpriteObject::updateObjects).
    if (facts.turnBasedActive && projectile.turnBasedPendingAction)
    {
        constexpr float TurnBasedObjectRange = 5120.0f;
        const float dx = projectile.x - facts.partyPosition.x;
        const float dy = projectile.y - facts.partyPosition.y;
        const float dz = projectile.z - facts.partyPosition.z;

        if (dx * dx + dy * dy + dz * dz > TurnBasedObjectRange * TurnBasedObjectRange)
        {
            result.expireProjectile = true;
            return result;
        }
    }

    result.motion = advanceProjectileMotion(projectile, facts.deltaSeconds, facts.gravity);

    if (facts.pWards != nullptr && !facts.pWards->empty())
    {
        float collisionFraction = 1.0f;

        if (facts.hasCollision)
        {
            const float dx = result.motion.endX - result.motion.startX;
            const float dy = result.motion.endY - result.motion.startY;
            const float dz = result.motion.endZ - result.motion.startZ;
            const float lengthSquared = dx * dx + dy * dy + dz * dz;

            if (lengthSquared > 0.0f)
            {
                collisionFraction = std::clamp(
                    ((facts.collision.point.x - result.motion.startX) * dx
                        + (facts.collision.point.y - result.motion.startY) * dy
                        + (facts.collision.point.z - result.motion.startZ) * dz) / lengthSquared,
                    0.0f,
                    1.0f);
            }
        }

        std::optional<ProjectileWardBlock> wardBlock =
            findProjectileWardBlock(projectile, result.motion, *facts.pWards, collisionFraction);

        if (wardBlock)
        {
            result.fxRequest = ProjectileFrameFxRequest{
                ProjectileFrameFxKind::ProjectileImpact,
                wardBlock->point,
                false};
            result.endPoint = wardBlock->point;
            result.wardBlock = std::move(wardBlock);
            result.expireProjectile = true;
            return result;
        }
    }

    if (!facts.hasCollision)
    {
        result.applyMotionEnd = true;
        traceProjectileNoCollision(projectile, facts, result.motion);
        return result;
    }

    const ProjectileBounceSurfaceFacts &bounceSurface = facts.collision.bounceSurface;
    const bool worldCollisionContinues =
        facts.collision.kind == ProjectileFrameCollisionKind::World
        && projectileContinuesAfterOeWorldImpact(projectile);
    const bool objectCanBounce = (projectile.objectFlags & ObjectDescBounce) != 0 || worldCollisionContinues;
    const bool downwardVelocityOk = !bounceSurface.requiresDownwardVelocity || projectile.velocityZ < 0.0f;
    const bool fastEnoughToBounce = std::abs(projectile.velocityZ) >= facts.bounceStopVelocity;
    const bool canBounce =
        bounceSurface.canBounce
        && objectCanBounce
        && downwardVelocityOk
        && fastEnoughToBounce;

    traceProjectileCollisionDecision(
        projectile,
        facts,
        result.motion,
        worldCollisionContinues,
        objectCanBounce,
        downwardVelocityOk,
        fastEnoughToBounce,
        canBounce);

    if (canBounce)
    {
        result.bounce = ProjectileFrameBounceResult{
            facts.collision.point,
            bounceSurface.normalX,
            bounceSurface.normalY,
            bounceSurface.normalZ,
            facts.bounceFactor,
            facts.bounceStopVelocity,
            facts.groundDamping};
        return result;
    }

    if (isPrimaryDeathBlossomProjectile(projectile))
    {
        result.deathBlossomFalloutPoint = facts.collision.point;
        result.endPoint = facts.collision.point;
        result.logCollision = true;
        result.expireProjectile = true;
        return result;
    }

    const bool directPartyDamage = facts.collision.kind == ProjectileFrameCollisionKind::Party;
    const bool directActorImpact = facts.collision.kind == ProjectileFrameCollisionKind::Actor;

    if (directPartyDamage)
    {
        result.directPartyDamage = buildProjectileDirectPartyDamage(projectile, facts.nonPartyProjectileDamage);
    }
    else if (directActorImpact)
    {
        ProjectileDirectActorImpactInput input = {};
        input.actorIndex = facts.collision.actorIndex;
        input.actorId = facts.collision.actorId;
        input.targetArmorClass = facts.collision.targetArmorClass;
        input.damageMultiplier = facts.collision.damageMultiplier;
        input.halfIncomingMissileDamage = facts.collision.halfIncomingMissileDamage;
        input.targetDistance = facts.collision.targetDistance;
        input.nonPartyProjectileDamage = facts.nonPartyProjectileDamage;
        input.pCombatRules = facts.collision.pCombatRules;
        input.targetFacts = facts.collision.targetFacts;
        input.partyCount = facts.collision.partyCount;
        input.pShooter = facts.collision.pShooter;
        input.targetMonsterId = facts.collision.targetMonsterId;
        result.directActorImpact = buildProjectileDirectActorImpact(projectile, input);
    }

    const float impactRadius = projectile.explosionRadius > 0.0f
        ? projectile.explosionRadius
        : spellImpactDamageRadius(static_cast<uint32_t>(projectile.spellId));

    if (impactRadius > 0.0f)
    {
        ProjectileAreaImpactInput areaInput = {};
        areaInput.impactX = facts.collision.point.x;
        areaInput.impactY = facts.collision.point.y;
        areaInput.impactZ = facts.collision.point.z;
        areaInput.impactRadius = impactRadius;
        areaInput.partyX = facts.partyPosition.x;
        areaInput.partyY = facts.partyPosition.y;
        areaInput.partyZ = facts.partyPosition.z;
        areaInput.partyCollisionRadius = facts.partyCollisionRadius;
        areaInput.partyCollisionHeight = facts.partyCollisionHeight;
        areaInput.canHitParty = facts.canHitParty && !directPartyDamage;
        areaInput.nonPartyProjectileDamage = facts.nonPartyProjectileDamage;
        areaInput.actors = facts.areaActors;
        result.areaImpact = ProjectileFrameAreaImpactResult{
            facts.collision.point,
            impactRadius,
            true,
            buildProjectileAreaImpact(projectile, areaInput)};
    }

    result.logCollision = true;

    if (facts.collision.waterTerrainImpact)
    {
        result.fxRequest = ProjectileFrameFxRequest{
            ProjectileFrameFxKind::WaterSplash,
            {projectile.x, projectile.y, facts.collision.point.z + 60.0f},
            false};
    }
    else
    {
        result.fxRequest = ProjectileFrameFxRequest{
            ProjectileFrameFxKind::ProjectileImpact,
            facts.collision.point,
            directActorImpact};
    }

    result.endPoint = facts.collision.point;
    result.expireProjectile = true;
    return result;
}

std::optional<GameplayProjectileService::ProjectileWardBlock> GameplayProjectileService::findProjectileWardBlock(
    const ProjectileState &projectile,
    const ProjectileMotionSegment &motion,
    const std::vector<ProjectileWardFacts> &wards,
    float maximumSegmentFraction)
{
    const float dx = motion.endX - motion.startX;
    const float dy = motion.endY - motion.startY;
    const float dz = motion.endZ - motion.startZ;
    const float a = dx * dx + dy * dy + dz * dz;

    if (a <= 0.0f)
    {
        return std::nullopt;
    }

    std::optional<ProjectileWardBlock> nearestBlock;
    float nearestFraction = maximumSegmentFraction;

    for (const ProjectileWardFacts &ward : wards)
    {
        const bool ownProjectile =
            projectile.sourceKind == ProjectileState::SourceKind::Actor && projectile.sourceId == ward.ownerActorId;

        if (ward.radius <= 0.0f || ownProjectile)
        {
            continue;
        }

        const float fx = motion.startX - ward.center.x;
        const float fy = motion.startY - ward.center.y;
        const float fz = motion.startZ - ward.center.z;
        const float c = fx * fx + fy * fy + fz * fz - ward.radius * ward.radius;

        if (c <= 0.0f)
        {
            continue;
        }

        const float b = 2.0f * (fx * dx + fy * dy + fz * dz);
        const float discriminant = b * b - 4.0f * a * c;

        if (discriminant < 0.0f)
        {
            continue;
        }

        const float fraction = (-b - std::sqrt(discriminant)) / (2.0f * a);

        if (fraction < 0.0f || fraction > nearestFraction)
        {
            continue;
        }

        nearestFraction = fraction;
        nearestBlock = ProjectileWardBlock{
            ward.ownerActorIndex,
            ward.ownerActorId,
            ward.wardId,
            {motion.startX + dx * fraction, motion.startY + dy * fraction, motion.startZ + dz * fraction}};
    }

    return nearestBlock;
}

bool GameplayProjectileService::canProjectileCollideWithParty(const ProjectileState &projectile) const
{
    return projectile.sourceKind != ProjectileState::SourceKind::Party && !projectile.eventMissile;
}

bool GameplayProjectileService::isProjectileSourceFriendlyToActor(
    const ProjectileState &projectile,
    const ProjectileActorRelationFacts &facts) const
{
    if (projectile.sourceKind == ProjectileState::SourceKind::Party || facts.eventSource)
    {
        return false;
    }

    if (projectile.fromSummonedMonster)
    {
        return !facts.targetHostileToParty || facts.targetPartyControlled;
    }

    if (!facts.sourceMonsterKnown)
    {
        return false;
    }

    return facts.sourceMonsterFriendlyToTarget;
}

float GameplayProjectileService::directActorProjectileHitRadius(
    const ProjectileState &projectile,
    float actorRadius)
{
    const float minimumRadius = projectile.sourceKind == ProjectileState::SourceKind::Party ? 32.0f : 8.0f;
    return std::max(actorRadius, minimumRadius);
}

bool GameplayProjectileService::canProjectileCollideWithActor(
    const ProjectileState &projectile,
    const ProjectileCollisionActorFacts &actorFacts) const
{
    if (actorFacts.dead || actorFacts.unavailableForCombat)
    {
        return false;
    }

    if (projectile.sourceKind == ProjectileState::SourceKind::Actor && actorFacts.actorId == projectile.sourceId)
    {
        return false;
    }

    if (projectile.sourceKind != ProjectileState::SourceKind::Party
        && actorFacts.friendlyToProjectileSource)
    {
        return false;
    }

    return true;
}

uint32_t GameplayProjectileService::fireSpikeLimitForMastery(uint32_t skillMastery)
{
    switch (static_cast<SkillMastery>(skillMastery))
    {
        case SkillMastery::Grandmaster:
            return 9;
        case SkillMastery::Master:
            return 7;
        case SkillMastery::Expert:
            return 5;
        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            return 3;
    }
}

GameplayProjectileService::FireSpikeTrapSpawnResult GameplayProjectileService::buildFireSpikeTrapSpawn(
    const FireSpikeTrapSpawnLimitInput &input)
{
    FireSpikeTrapSpawnResult result = {};
    result.activeLimit = fireSpikeLimitForMastery(input.skillMastery);

    for (const FireSpikeActiveTrapFacts &trap : input.traps)
    {
        if (trap.expired
            || trap.sourceKind != input.sourceKind
            || trap.sourcePartyMemberIndex != input.sourcePartyMemberIndex)
        {
            continue;
        }

        ++result.activeCount;
    }

    result.accepted = result.activeCount < result.activeLimit;

    if (result.accepted)
    {
        result.trapId = allocateFireSpikeTrapId();
    }

    return result;
}

uint32_t GameplayProjectileService::advanceFireSpikeTrapLifetime(
    uint32_t timeSinceCreatedTicks,
    float deltaSeconds) const
{
    return timeSinceCreatedTicks + ticksFromDeltaSeconds(deltaSeconds);
}

GameplayProjectileService::FireSpikeTrapTriggerResult
GameplayProjectileService::buildFireSpikeTrapTrigger(
    const FireSpikeTrapTriggerInput &input) const
{
    FireSpikeTrapTriggerResult result = {};
    float bestDistanceSquared = std::numeric_limits<float>::max();

    for (const FireSpikeTrapActorFacts &actor : input.actors)
    {
        if (actor.unavailableForCombat)
        {
            continue;
        }

        if (input.sourceKind == ProjectileState::SourceKind::Party)
        {
            if (!actor.hostileToParty)
            {
                continue;
            }
        }
        else if (actor.friendlyToTrapSource)
        {
            continue;
        }

        const float deltaX = actor.x - input.x;
        const float deltaY = actor.y - input.y;
        const float horizontalDistanceSquared = deltaX * deltaX + deltaY * deltaY;
        const float triggerRadius =
            static_cast<float>(std::max<uint16_t>(actor.radius, 24))
            + static_cast<float>(std::max<uint16_t>(input.trapRadius, 24))
            + 48.0f;

        if (horizontalDistanceSquared > triggerRadius * triggerRadius)
        {
            continue;
        }

        const float actorCenterZ = actor.z + static_cast<float>(actor.height) * 0.5f;

        if (std::abs(actorCenterZ - input.z) > static_cast<float>(std::max<uint16_t>(actor.height, 128)))
        {
            continue;
        }

        if (horizontalDistanceSquared < bestDistanceSquared)
        {
            bestDistanceSquared = horizontalDistanceSquared;
            result.triggered = true;
            result.actorIndex = actor.actorIndex;
            result.actorId = actor.actorId;
        }
    }

    if (result.triggered)
    {
        result.damage = rollFireSpikeDamage(
            input.skillLevel,
            input.skillMastery,
            input.trapId ^ static_cast<uint32_t>(result.actorId * 2654435761u));
        result.applyActorImpact = true;
        result.spawnImpactVisual = true;
        result.expireTrap = true;
    }

    return result;
}

GameplayProjectileService::ProjectileState GameplayProjectileService::buildFireSpikeTrapImpactProjectile(
    const FireSpikeTrapImpactProjectileInput &input)
{
    ProjectileState projectile = {};
    projectile.projectileId = allocateProjectileId();
    projectile.sourceKind = input.sourceKind;
    projectile.sourceId = input.sourceId;
    projectile.sourcePartyMemberIndex = input.sourcePartyMemberIndex;
    projectile.sourceMonsterId = input.sourceMonsterId;
    projectile.fromSummonedMonster = input.fromSummonedMonster;
    projectile.ability = input.ability;
    projectile.objectDescriptionId = input.objectDescriptionId;
    projectile.objectSpriteId = input.objectSpriteId;
    projectile.objectSpriteFrameIndex = input.objectSpriteFrameIndex;
    projectile.impactObjectDescriptionId = input.impactObjectDescriptionId;
    projectile.objectFlags = input.objectFlags;
    projectile.radius = input.radius;
    projectile.height = input.height;
    projectile.spellId = input.spellId;
    projectile.effectSoundId = input.effectSoundId;
    projectile.skillLevel = input.skillLevel;
    projectile.skillMastery = input.skillMastery;
    projectile.objectName = input.objectName;
    projectile.objectSpriteName = input.objectSpriteName;
    projectile.sourceX = input.x;
    projectile.sourceY = input.y;
    projectile.sourceZ = input.z;
    projectile.x = input.x;
    projectile.y = input.y;
    projectile.z = input.z;
    projectile.damage = input.damage;
    projectile.damageType = spellIdFromValue(input.spellId) == SpellId::FireSpike
        ? CombatDamageType::Fire
        : CombatDamageType::Physical;
    return projectile;
}

void GameplayProjectileService::eraseExpiredProjectilesAndImpacts()
{
    eraseExpiredProjectiles();
    eraseExpiredProjectileImpacts();
}

void GameplayProjectileService::eraseExpiredProjectiles()
{
    std::erase_if(
        m_projectiles,
        [](const ProjectileState &projectile)
        {
            return projectile.isExpired;
        });
}

void GameplayProjectileService::eraseExpiredProjectileImpacts()
{
    std::erase_if(
        m_projectileImpacts,
        [](const ProjectileImpactState &impact)
        {
            return impact.isExpired;
        });
}

size_t GameplayProjectileService::projectileCount() const
{
    return m_projectiles.size();
}

const GameplayProjectileService::ProjectileState *
GameplayProjectileService::projectileState(size_t projectileIndex) const
{
    if (projectileIndex >= m_projectiles.size())
    {
        return nullptr;
    }

    return &m_projectiles[projectileIndex];
}

size_t GameplayProjectileService::projectileImpactCount() const
{
    return m_projectileImpacts.size();
}

const GameplayProjectileService::ProjectileImpactState *
GameplayProjectileService::projectileImpactState(size_t effectIndex) const
{
    if (effectIndex >= m_projectileImpacts.size())
    {
        return nullptr;
    }

    return &m_projectileImpacts[effectIndex];
}

void GameplayProjectileService::collectProjectilePresentationState(
    std::vector<GameplayProjectilePresentationState> &projectiles,
    std::vector<GameplayProjectileImpactPresentationState> &impacts) const
{
    projectiles.clear();
    impacts.clear();
    projectiles.reserve(m_projectiles.size());
    impacts.reserve(m_projectileImpacts.size());

    for (const ProjectileState &projectile : m_projectiles)
    {
        if (projectile.isExpired)
        {
            continue;
        }

        GameplayProjectilePresentationState state = {};
        state.projectileId = projectile.projectileId;
        state.objectDescriptionId = projectile.objectDescriptionId;
        state.objectSpriteId = projectile.objectSpriteId;
        state.objectSpriteFrameIndex = projectile.objectSpriteFrameIndex;
        state.objectFlags = projectile.objectFlags;
        state.visualMode = projectile.visualMode;
        state.radius = projectile.radius;
        state.height = projectile.height;
        state.spellId = projectile.spellId;
        state.sourceMonsterId = projectile.sourceMonsterId;
        state.objectName = projectile.objectName;
        state.objectSpriteName = projectile.objectSpriteName;
        state.x = projectile.x;
        state.y = projectile.y;
        state.z = projectile.z;
        state.velocityX = projectile.velocityX;
        state.velocityY = projectile.velocityY;
        state.velocityZ = projectile.velocityZ;
        state.timeSinceCreatedTicks = projectile.timeSinceCreatedTicks;
        state.sectorId = projectile.sectorId;
        state.isSettled = projectile.isSettled;
        projectiles.push_back(std::move(state));
    }

    for (const ProjectileImpactState &impact : m_projectileImpacts)
    {
        if (impact.isExpired)
        {
            continue;
        }

        GameplayProjectileImpactPresentationState state = {};
        state.effectId = impact.effectId;
        state.objectDescriptionId = impact.objectDescriptionId;
        state.objectSpriteId = impact.objectSpriteId;
        state.objectSpriteFrameIndex = impact.objectSpriteFrameIndex;
        state.sourceObjectFlags = impact.sourceObjectFlags;
        state.sourceSpellId = impact.sourceSpellId;
        state.sourceMonsterId = impact.sourceMonsterId;
        state.flightDirectionX = impact.flightDirectionX;
        state.flightDirectionY = impact.flightDirectionY;
        state.flightDirectionZ = impact.flightDirectionZ;
        state.objectName = impact.objectName;
        state.objectSpriteName = impact.objectSpriteName;
        state.sourceObjectName = impact.sourceObjectName;
        state.sourceObjectSpriteName = impact.sourceObjectSpriteName;
        state.x = impact.x;
        state.y = impact.y;
        state.z = impact.z;
        state.timeSinceCreatedTicks = impact.timeSinceCreatedTicks;
        state.lifetimeTicks = impact.lifetimeTicks;
        state.sectorId = impact.sectorId;
        state.targetActorIndex = impact.targetActorIndex;
        state.freezeAnimation = impact.freezeAnimation;
        impacts.push_back(std::move(state));
    }
}

std::vector<GameplayProjectileEndPresentationState> GameplayProjectileService::takeEndedProjectiles()
{
    return std::exchange(m_endedProjectiles, {});
}

ShieldHitModifiers GameplayProjectileService::partyShieldModifiers(const ProjectileState &projectile,
    const Party *pParty)
{
    if (projectile.spellId > 0 && projectile.sourceKind == ProjectileState::SourceKind::Party && pParty != nullptr)
    {
        if (const Character *pCaster = pParty->member(projectile.sourcePartyMemberIndex))
        {
            return GameMechanics::spellShieldModifiers(*pCaster);
        }
    }

    return projectile.shieldModifiers;
}

ShieldAttackTier GameplayProjectileService::projectileShieldTier(const ProjectileState &projectile)
{
    if (projectile.shieldTier)
    {
        return *projectile.shieldTier;
    }

    if (projectile.spellId > 0)
    {
        return ShieldAttackTier::Spell;
    }

    return shieldAttackTierForDamageType(
        projectile.damageType,
        projectile.sourceKind == ProjectileState::SourceKind::Party);
}

float GameplayProjectileService::spellImpactDamageRadius(uint32_t spellId)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::Fireball:
        case SpellId::MeteorShower:
        case SpellId::Starburst:
        case SpellId::RockBlast:
        case SpellId::DeathBlossom:
        case SpellId::DragonBreath:
        case SpellId::FlameBlast:
            return SpellImpactAoeRadius;
        default:
            return 0.0f;
    }
}

PartyMissileSource GameplayProjectileService::partyMissileSource(
    const ProjectileState &projectile,
    const Party *pParty,
    const ItemTable *pItemTable,
    const MonsterTable::MonsterStatsEntry &targetStats,
    int targetCurrentHp)
{
    PartyMissileSource source;

    if (projectile.sourceKind == ProjectileState::SourceKind::Party && pParty != nullptr)
    {
        source.pAttacker = pParty->member(projectile.sourcePartyMemberIndex);
        source.pItemTable = pItemTable;
        source.spellId = uint32_t(std::max(projectile.spellId, 0));
        source.targetCurrentHp = targetCurrentHp;
        source.resistances = monsterDamageResistances(targetStats);
    }

    return source;
}

MonsterDamageResistances GameplayProjectileService::monsterDamageResistances(
    const MonsterTable::MonsterStatsEntry &stats)
{
    return MonsterDamageResistances{
        .fire = stats.fireResistance,
        .air = stats.airResistance,
        .water = stats.waterResistance,
        .earth = stats.earthResistance,
        .spirit = stats.spiritResistance,
        .mind = stats.mindResistance,
        .body = stats.bodyResistance,
        .light = stats.lightResistance,
        .dark = stats.darkResistance,
        .physical = stats.physicalResistance,
    };
}

int16_t GameplayProjectileService::waterSplashObjectId()
{
    return 800;
}
}
