#include "game/gameplay/GameplayProjectileService.h"

#include "game/audio/SoundIds.h"
#include "game/fx/ParticleRecipes.h"
#include "game/gameplay/GameMechanics.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/SpriteObjectDefs.h"
#include "game/party/SkillData.h"
#include "game/StringUtils.h"
#include "game/party/SpellIds.h"
#include "game/tables/ObjectTable.h"
#include "game/tables/SpriteTables.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <random>

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
constexpr float DeathBlossomFalloutMinDistance = 220.0f;
constexpr float DeathBlossomFalloutMaxDistance = 620.0f;
constexpr float MeteorShowerSpawnBaseHeight = 2500.0f;
constexpr float MeteorShowerSpawnHeightVariance = 1000.0f;
constexpr float MeteorShowerTargetSpread = 512.0f;
constexpr uint32_t StarburstProjectileCount = 20;
constexpr float StarburstSpawnBaseHeight = 2500.0f;
constexpr float StarburstSpawnHeightVariance = 1000.0f;
constexpr float StarburstTargetSpread = 512.0f;

bool isPrimaryDeathBlossomProjectile(const GameplayProjectileService::ProjectileState &projectile)
{
    return spellIdFromValue(static_cast<uint32_t>(projectile.spellId)) == SpellId::DeathBlossom
        && toLowerCopy(projectile.objectName) != "shard";
}

int averageMonsterProjectileDamage(const GameplayProjectileService::MonsterProjectileDamageProfile &profile)
{
    if (profile.diceRolls <= 0 || profile.diceSides <= 0)
    {
        return std::max(0, profile.bonus);
    }

    return profile.diceRolls * (profile.diceSides + 1) / 2 + profile.bonus;
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
        projectile.radius = request.definition.radius;
        projectile.height = request.definition.height;
        projectile.spellId = request.definition.spellId;
        projectile.effectSoundId = request.definition.effectSoundId;
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
        projectile.useActorHitChance = request.useActorHitChance;
        projectile.lifetimeTicks = request.definition.lifetimeTicks;

        result.kind = ProjectileSpawnResult::Kind::InstantImpact;
        result.projectile = std::move(projectile);
        result.speed = request.definition.speed;
        return result;
    }

    const float directionX = deltaX / distance;
    const float directionY = deltaY / distance;
    const float directionZ = deltaZ / distance;

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
    projectile.radius = request.definition.radius;
    projectile.height = request.definition.height;
    projectile.spellId = request.definition.spellId;
    projectile.effectSoundId = request.definition.effectSoundId;
    projectile.skillLevel = request.skillLevel;
    projectile.skillMastery = request.skillMastery;
    projectile.objectName = request.definition.objectName;
    projectile.objectSpriteName = request.definition.objectSpriteName;
    projectile.sourceX = request.sourceX;
    projectile.sourceY = request.sourceY;
    projectile.sourceZ = request.sourceZ;
    projectile.x = request.sourceX + directionX * request.spawnForwardOffset;
    projectile.y = request.sourceY + directionY * request.spawnForwardOffset;
    projectile.z = request.sourceZ;
    projectile.velocityX = directionX * request.definition.speed;
    projectile.velocityY = directionY * request.definition.speed;
    projectile.velocityZ = directionZ * request.definition.speed;
    projectile.damage = request.damage;
    projectile.attackBonus = request.attackBonus;
    projectile.useActorHitChance = request.useActorHitChance;
    projectile.lifetimeTicks = request.definition.lifetimeTicks;

    m_projectiles.push_back(std::move(projectile));

    result.kind = ProjectileSpawnResult::Kind::SpawnedProjectile;
    result.projectile = m_projectiles.back();
    result.directionX = directionX;
    result.directionY = directionY;
    result.directionZ = directionZ;
    result.speed = request.definition.speed;
    return result;
}

GameplayProjectileService::ProjectileSpawnPresentationDecision
GameplayProjectileService::buildProjectileSpawnPresentationDecision(const ProjectileSpawnResult &result) const
{
    ProjectileSpawnPresentationOptions options = {};
    return buildProjectileSpawnPresentationDecision(result, options);
}

GameplayProjectileService::ProjectileSpawnPresentationDecision
GameplayProjectileService::buildProjectileSpawnPresentationDecision(
    const ProjectileSpawnResult &result,
    const ProjectileSpawnPresentationOptions &options) const
{
    ProjectileSpawnPresentationDecision decision = {};

    if (result.kind == ProjectileSpawnResult::Kind::FailedZeroDistance)
    {
        return decision;
    }

    decision.accepted = true;

    if (result.kind == ProjectileSpawnResult::Kind::InstantImpact)
    {
        decision.impactX = result.projectile.sourceX;
        decision.impactY = result.projectile.sourceY;
        decision.impactZ = result.projectile.sourceZ;
        decision.commands.push_back(ProjectileSpawnPresentationCommand::SpawnInstantImpact);
        return decision;
    }

    if (options.playReleaseAudio)
    {
        decision.releaseAudioRequest = buildProjectileReleaseAudioRequest(
            result.projectile,
            result.projectile.sourceX,
            result.projectile.sourceY,
            result.projectile.sourceZ);
        if (decision.releaseAudioRequest)
        {
            decision.commands.push_back(ProjectileSpawnPresentationCommand::PlayReleaseAudio);
        }
    }

    decision.commands.push_back(ProjectileSpawnPresentationCommand::LogSpawn);
    return decision;
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

const GameplayProjectileService::ProjectileImpactState &GameplayProjectileService::spawnProjectileImpact(
    const ProjectileImpactRequest &request)
{
    ProjectileImpactState effect = {};
    effect.effectId = allocateProjectileImpactId();
    effect.objectDescriptionId = request.objectDescriptionId;
    effect.objectSpriteId = request.objectSpriteId;
    effect.objectSpriteFrameIndex = request.objectSpriteFrameIndex;
    effect.sourceObjectFlags = request.sourceObjectFlags;
    effect.sourceSpellId = request.sourceSpellId;
    effect.objectName = request.objectName;
    effect.objectSpriteName = request.objectSpriteName;
    effect.sourceObjectName = request.sourceObjectName;
    effect.sourceObjectSpriteName = request.sourceObjectSpriteName;
    effect.x = request.x;
    effect.y = request.y;
    effect.z = request.z;
    effect.lifetimeTicks = request.lifetimeTicks;
    effect.freezeAnimation = request.freezeAnimation;

    m_projectileImpacts.push_back(std::move(effect));
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

void GameplayProjectileService::advanceProjectileImpactLifetimes(uint32_t deltaTicks)
{
    if (deltaTicks == 0)
    {
        return;
    }

    for (ProjectileImpactState &impact : m_projectileImpacts)
    {
        if (impact.isExpired)
        {
            continue;
        }

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

    const uint32_t deltaTicks = ticksFromDeltaSeconds(deltaSeconds);
    advanceProjectileImpactLifetimes(deltaTicks);
    eraseExpiredProjectileImpacts();
}

bool GameplayProjectileService::advanceProjectileLifetime(
    ProjectileState &projectile,
    uint32_t deltaTicks) const
{
    if (deltaTicks == 0 || projectile.isExpired)
    {
        return projectile.isExpired;
    }

    projectile.timeSinceCreatedTicks += deltaTicks;
    return projectile.timeSinceCreatedTicks >= projectile.lifetimeTicks;
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

GameplayProjectileService::ProjectileFrameAdvanceResult GameplayProjectileService::advanceProjectileFrame(
    ProjectileState &projectile,
    float deltaSeconds,
    float gravity) const
{
    ProjectileFrameAdvanceResult result = {};
    const uint32_t deltaTicks = ticksFromDeltaSeconds(deltaSeconds);

    if (advanceProjectileLifetime(projectile, deltaTicks))
    {
        result.kind = ProjectileFrameAdvanceKind::LifetimeExpired;
        result.lifetimeImpactDecision =
            buildProjectileImpactDecision(projectile, ProjectileImpactReason::LifetimeExpired);
        result.lifetimeExpiryDecision = buildProjectileLifetimeExpiryDecision(result.lifetimeImpactDecision);
        return result;
    }

    result.kind = ProjectileFrameAdvanceKind::Moving;
    result.motionSegment = advanceProjectileMotion(projectile, deltaSeconds, gravity);
    return result;
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
}

GameplayProjectileService::ProjectileImpactDecision GameplayProjectileService::buildProjectileImpactDecision(
    const ProjectileState &projectile,
    ProjectileImpactReason reason) const
{
    ProjectileImpactDecision decision = {};

    if (isPrimaryDeathBlossomProjectile(projectile))
    {
        decision.spawnDeathBlossomFallout = true;
        return decision;
    }

    if (reason == ProjectileImpactReason::LifetimeExpired
        && spellIdFromValue(static_cast<uint32_t>(projectile.spellId)) != SpellId::RockBlast)
    {
        return decision;
    }

    decision.impactRadius = spellImpactDamageRadius(static_cast<uint32_t>(projectile.spellId));
    decision.applyAreaDamage = decision.impactRadius > 0.0f;
    decision.spawnProjectileImpact = true;
    return decision;
}

GameplayProjectileService::ProjectileBounceDecision GameplayProjectileService::buildProjectileBounceDecision(
    const ProjectileState &projectile,
    const ProjectileBounceSurfaceFacts &surfaceFacts,
    float stopVelocity) const
{
    ProjectileBounceDecision decision = {};

    if (!surfaceFacts.canBounce || (projectile.objectFlags & ObjectDescBounce) == 0)
    {
        return decision;
    }

    if (surfaceFacts.requiresDownwardVelocity && projectile.velocityZ >= 0.0f)
    {
        return decision;
    }

    if (std::abs(projectile.velocityZ) < stopVelocity)
    {
        return decision;
    }

    decision.shouldBounce = true;
    decision.normalX = surfaceFacts.normalX;
    decision.normalY = surfaceFacts.normalY;
    decision.normalZ = surfaceFacts.normalZ;
    return decision;
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
    std::uniform_real_distribution<float> distanceScale(
        DeathBlossomFalloutMinDistance,
        DeathBlossomFalloutMaxDistance);
    const float angleStep = (2.0f * Pi) / static_cast<float>(DeathBlossomFalloutShardCount);

    for (uint32_t shardIndex = 0; shardIndex < DeathBlossomFalloutShardCount; ++shardIndex)
    {
        const float yaw = angleStep * static_cast<float>(shardIndex) + yawJitter(rng);
        const float distance = distanceScale(rng);

        ProjectileSpawnRequest request = {};
        request.sourceKind = projectile.sourceKind;
        request.sourceId = projectile.sourceId;
        request.sourcePartyMemberIndex = projectile.sourcePartyMemberIndex;
        request.sourceMonsterId = projectile.sourceMonsterId;
        request.fromSummonedMonster = projectile.fromSummonedMonster;
        request.ability = projectile.ability;
        request.definition = definition;
        request.skillLevel = projectile.skillLevel;
        request.skillMastery = projectile.skillMastery;
        request.damage = projectile.damage;
        request.attackBonus = projectile.attackBonus;
        request.sourceX = x;
        request.sourceY = y;
        request.sourceZ = z + DeathBlossomFalloutSourceHeightOffset;
        request.targetX = x + std::cos(yaw) * distance;
        request.targetY = y + std::sin(yaw) * distance;
        request.targetZ = z;
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

bool GameplayProjectileService::shouldSpawnProjectileImpactPresentation(
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

GameplayProjectileService::ProjectileImpactRequest GameplayProjectileService::buildProjectileImpactRequest(
    const ProjectileState &projectile,
    const ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z,
    bool centerVertically) const
{
    ProjectileImpactRequest request = {};
    request.objectDescriptionId = definition.objectDescriptionId;
    request.objectSpriteId = definition.objectSpriteId;
    request.objectSpriteFrameIndex = definition.objectSpriteFrameIndex;
    request.sourceObjectFlags = projectile.objectFlags;
    request.sourceSpellId = projectile.spellId;
    request.objectName = definition.objectName;
    request.objectSpriteName = definition.objectSpriteName;
    request.sourceObjectName = projectile.objectName;
    request.sourceObjectSpriteName = projectile.objectSpriteName;
    request.x = x;
    request.y = y;
    request.z = centerVertically
        ? z - static_cast<float>(std::max<int16_t>(definition.objectHeight, 0)) * 0.5f
        : z;
    request.lifetimeTicks = definition.lifetimeTicks;
    return request;
}

GameplayProjectileService::ProjectileImpactRequest GameplayProjectileService::buildWaterSplashImpactRequest(
    const ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z) const
{
    ProjectileImpactRequest request = {};
    request.objectDescriptionId = definition.objectDescriptionId;
    request.objectSpriteId = definition.objectSpriteId;
    request.objectSpriteFrameIndex = definition.objectSpriteFrameIndex;
    request.objectName = definition.objectName;
    request.objectSpriteName = definition.objectSpriteName;
    request.x = x;
    request.y = y;
    request.z = z;
    request.lifetimeTicks = definition.lifetimeTicks;
    return request;
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

GameplayProjectileService::ProjectileImpactPresentationResult
GameplayProjectileService::spawnProjectileImpactPresentation(
    const ProjectileState &projectile,
    const ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z,
    bool centerVertically)
{
    ProjectileImpactPresentationResult result = {};

    if (!shouldSpawnProjectileImpactPresentation(projectile, definition))
    {
        return result;
    }

    const ProjectileImpactRequest impactRequest =
        buildProjectileImpactRequest(projectile, definition, x, y, z, centerVertically);
    const ProjectileImpactState &impact = spawnProjectileImpact(impactRequest);
    result.spawned = true;
    result.pImpact = &impact;
    return result;
}

GameplayProjectileService::ProjectileImpactPresentationResult
GameplayProjectileService::spawnWaterSplashImpactPresentation(
    const ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z)
{
    ProjectileImpactPresentationResult result = {};
    const ProjectileImpactRequest impactRequest = buildWaterSplashImpactRequest(definition, x, y, z);
    const ProjectileImpactState &impact = spawnProjectileImpact(impactRequest);
    result.spawned = true;
    result.pImpact = &impact;
    return result;
}

GameplayProjectileService::ProjectileImpactPresentationResult
GameplayProjectileService::spawnImmediateSpellImpactPresentation(
    const ProjectileImpactVisualDefinition &definition,
    int sourceSpellId,
    const std::string &sourceObjectName,
    const std::string &sourceObjectSpriteName,
    float x,
    float y,
    float z,
    bool centerVertically,
    bool freezeAnimation)
{
    ProjectileImpactPresentationResult result = {};

    if (definition.objectDescriptionId == 0)
    {
        return result;
    }

    ProjectileImpactRequest impactRequest = {};
    impactRequest.objectDescriptionId = definition.objectDescriptionId;
    impactRequest.objectSpriteId = definition.objectSpriteId;
    impactRequest.objectSpriteFrameIndex = definition.objectSpriteFrameIndex;
    impactRequest.sourceSpellId = sourceSpellId;
    impactRequest.objectName = definition.objectName;
    impactRequest.objectSpriteName = definition.objectSpriteName;
    impactRequest.sourceObjectName = sourceObjectName;
    impactRequest.sourceObjectSpriteName = sourceObjectSpriteName;
    impactRequest.x = x;
    impactRequest.y = y;
    impactRequest.z = centerVertically
        ? z - static_cast<float>(std::max<int16_t>(definition.objectHeight, 0)) * 0.5f
        : z;
    impactRequest.lifetimeTicks = definition.lifetimeTicks;
    impactRequest.freezeAnimation = freezeAnimation;

    const ProjectileImpactState &impact = spawnProjectileImpact(impactRequest);
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
        return std::nullopt;
    }

    ProjectileAudioRequest request = {};
    request.soundId = static_cast<uint32_t>(projectile.effectSoundId + 1);
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
        return resolveEventProjectileDamage(input.spellId, input.skillLevel);
    }

    if (!input.hasMonsterFacts)
    {
        return 1;
    }

    const int fallbackAttackDamage = std::max(1, input.monsterLevel / 2);
    const int fallbackSpellDamage = std::max(2, input.monsterLevel);

    switch (input.monsterAbility)
    {
        case MonsterAttackAbility::Attack2:
        {
            const int damage = averageMonsterProjectileDamage(input.attack2Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
        case MonsterAttackAbility::Spell1:
        case MonsterAttackAbility::Spell2:
            return fallbackSpellDamage;
        case MonsterAttackAbility::Attack1:
        default:
        {
            const int damage = averageMonsterProjectileDamage(input.attack1Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
    }
}

int GameplayProjectileService::resolvePartyProjectileDamageMultiplier(
    const ProjectileState &projectile,
    const Character *pSourceMember,
    const ItemTable *pItemTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    const std::string &targetMonsterName,
    const std::string &targetMonsterPictureName) const
{
    if (projectile.sourceKind != ProjectileState::SourceKind::Party
        || projectile.damage <= 0
        || projectile.spellId != 0
        || pSourceMember == nullptr
        || pItemTable == nullptr)
    {
        return 1;
    }

    return ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
        *pSourceMember,
        CharacterAttackMode::Bow,
        pItemTable,
        pSpecialItemEnchantTable,
        targetMonsterName,
        targetMonsterPictureName);
}

GameplayProjectileService::PartyProjectileActorImpactDecision
GameplayProjectileService::buildPartyProjectileActorImpactDecision(
    const PartyProjectileActorImpactInput &input) const
{
    PartyProjectileActorImpactDecision decision = {};
    decision.damage = input.damage;

    if (input.useActorHitChance)
    {
        std::mt19937 rng(
            input.projectileId
            ^ static_cast<uint32_t>(input.targetActorId * 2654435761u));
        decision.hit = GameMechanics::characterRangedAttackHitsArmorClass(
            input.targetArmorClass,
            input.attackBonus,
            input.targetDistance,
            rng);
    }

    if (decision.hit && decision.damage > 0)
    {
        decision.damage *= input.damageMultiplier;
    }

    return decision;
}

GameplayProjectileService::ProjectileAreaImpactDecision
GameplayProjectileService::buildProjectileAreaImpactDecision(
    const ProjectileState &projectile,
    const ProjectileAreaImpactInput &input) const
{
    ProjectileAreaImpactDecision decision = {};

    if (input.impactRadius <= 0.0f)
    {
        return decision;
    }

    const int impactDamage = projectile.sourceKind == ProjectileState::SourceKind::Party
        ? std::max(1, projectile.damage)
        : input.nonPartyProjectileDamage;

    if (input.canHitParty)
    {
        const float partyCenterZ = input.partyZ + input.partyCollisionHeight * 0.5f;
        decision.hitParty = pointWithinExpandedCylinder(
            input.partyX,
            input.partyY,
            partyCenterZ,
            input.partyCollisionRadius,
            input.impactX,
            input.impactY,
            input.impactZ,
            input.impactRadius);
        decision.partyDamage = impactDamage;
    }

    decision.actorHits.reserve(input.actors.size());

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

        ProjectileAreaImpactActorDecision actorDecision = {};
        actorDecision.actorIndex = actor.actorIndex;
        actorDecision.damage = impactDamage;
        decision.actorHits.push_back(actorDecision);
    }

    return decision;
}

GameplayProjectileService::ProjectileDirectPartyImpactDecision
GameplayProjectileService::buildProjectileDirectPartyImpactDecision(
    const ProjectileState &projectile,
    const ProjectileDirectPartyImpactInput &input) const
{
    ProjectileDirectPartyImpactDecision decision = {};

    if (projectile.sourceKind == ProjectileState::SourceKind::Party)
    {
        return decision;
    }

    decision.hitParty = true;
    decision.damage = input.nonPartyProjectileDamage;
    return decision;
}

GameplayProjectileService::ProjectileDirectActorImpactDecision
GameplayProjectileService::buildProjectileDirectActorImpactDecision(
    const ProjectileState &projectile,
    const ProjectileDirectActorImpactInput &input) const
{
    ProjectileDirectActorImpactDecision decision = {};
    decision.actorIndex = input.actorIndex;
    decision.actorId = input.actorId;

    if (projectile.sourceKind == ProjectileState::SourceKind::Party)
    {
        PartyProjectileActorImpactInput partyImpactInput = {};
        partyImpactInput.projectileId = projectile.projectileId;
        partyImpactInput.targetActorId = input.actorId;
        partyImpactInput.damage = projectile.damage;
        partyImpactInput.attackBonus = projectile.attackBonus;
        partyImpactInput.targetArmorClass = input.targetArmorClass;
        partyImpactInput.damageMultiplier = input.damageMultiplier;
        partyImpactInput.targetDistance = input.targetDistance;
        partyImpactInput.useActorHitChance = projectile.useActorHitChance;

        const PartyProjectileActorImpactDecision partyDecision =
            buildPartyProjectileActorImpactDecision(partyImpactInput);

        decision.damage = partyDecision.damage;
        decision.hit = partyDecision.hit;
        decision.applyPartyProjectileDamage = partyDecision.hit && partyDecision.damage > 0;
        decision.queuePartyProjectileActorEvent = true;
        return decision;
    }

    decision.damage = input.nonPartyProjectileDamage;
    decision.applyNonPartyProjectileDamage = input.nonPartyProjectileDamage > 0;
    return decision;
}

GameplayProjectileService::ProjectileCollisionOutcomeDecision
GameplayProjectileService::buildProjectileCollisionOutcomeDecision(
    const ProjectileImpactDecision &impactDecision,
    const ProjectileCollisionOutcomeInput &input) const
{
    ProjectileCollisionOutcomeDecision decision = {};

    if (impactDecision.spawnDeathBlossomFallout)
    {
        decision.spawnDeathBlossomFallout = true;
        decision.stopAfterDeathBlossomFallout = true;
        return decision;
    }

    decision.applyDirectPartyImpact = input.directPartyImpact;
    decision.applyDirectActorImpact = input.directActorImpact;

    if (impactDecision.applyAreaDamage)
    {
        decision.applyAreaDamage = true;
        decision.areaCanHitParty = !input.directPartyImpact;
        decision.impactRadius = impactDecision.impactRadius;
        decision.hasDirectActorIndex = input.directActorImpact;
        decision.directActorIndex = input.directActorIndex;
    }

    return decision;
}

GameplayProjectileService::ProjectileLifetimeExpiryDecision
GameplayProjectileService::buildProjectileLifetimeExpiryDecision(
    const ProjectileImpactDecision &impactDecision) const
{
    ProjectileLifetimeExpiryDecision decision = {};
    decision.impactRadius = impactDecision.impactRadius;

    if (impactDecision.spawnDeathBlossomFallout)
    {
        decision.commands.push_back(ProjectileLifetimeExpiryCommand::SpawnDeathBlossomFallout);
    }

    if (impactDecision.applyAreaDamage)
    {
        decision.commands.push_back(ProjectileLifetimeExpiryCommand::ApplyAreaDamage);
    }

    if (impactDecision.spawnProjectileImpact)
    {
        decision.commands.push_back(ProjectileLifetimeExpiryCommand::SpawnProjectileImpact);
    }

    decision.commands.push_back(ProjectileLifetimeExpiryCommand::ExpireProjectile);
    return decision;
}

void GameplayProjectileService::expireProjectile(ProjectileState &projectile) const
{
    projectile.isExpired = true;
}

GameplayProjectileService::ProjectileCollisionPresentationDecision
GameplayProjectileService::buildProjectileCollisionPresentationDecision(
    const ProjectileImpactDecision &impactDecision,
    const ProjectileCollisionPresentationInput &input) const
{
    ProjectileCollisionPresentationDecision decision = {};

    if (input.waterTerrainImpact)
    {
        decision.spawnWaterSplash = true;
        decision.x = input.projectileX;
        decision.y = input.projectileY;
        decision.z = input.impactZ + 60.0f;
        return decision;
    }

    if (!impactDecision.spawnProjectileImpact)
    {
        return decision;
    }

    decision.spawnProjectileImpact = true;
    decision.x = input.impactX;
    decision.y = input.impactY;
    decision.z = input.impactZ;
    decision.centerProjectileImpactVertically = input.actorImpact;
    return decision;
}

GameplayProjectileService::ProjectileCollisionResolutionDecision
GameplayProjectileService::buildProjectileCollisionResolutionDecision(
    const ProjectileImpactDecision &impactDecision,
    const ProjectileCollisionOutcomeInput &outcomeInput,
    const ProjectileCollisionPresentationInput &presentationInput) const
{
    ProjectileCollisionResolutionDecision decision = {};
    decision.outcome = buildProjectileCollisionOutcomeDecision(impactDecision, outcomeInput);
    decision.presentation = buildProjectileCollisionPresentationDecision(impactDecision, presentationInput);

    if (decision.outcome.spawnDeathBlossomFallout)
    {
        decision.commands.push_back(ProjectileCollisionResolutionCommand::SpawnDeathBlossomFallout);
        decision.commands.push_back(ProjectileCollisionResolutionCommand::LogCollision);
        decision.commands.push_back(ProjectileCollisionResolutionCommand::ExpireProjectile);

        if (decision.outcome.stopAfterDeathBlossomFallout)
        {
            return decision;
        }
    }

    if (decision.outcome.applyDirectPartyImpact)
    {
        decision.commands.push_back(ProjectileCollisionResolutionCommand::ApplyDirectPartyImpact);
    }
    else if (decision.outcome.applyDirectActorImpact)
    {
        decision.commands.push_back(ProjectileCollisionResolutionCommand::ApplyDirectActorImpact);
    }

    if (decision.outcome.applyAreaDamage)
    {
        decision.commands.push_back(ProjectileCollisionResolutionCommand::ApplyAreaDamage);
    }

    decision.commands.push_back(ProjectileCollisionResolutionCommand::LogCollision);

    if (decision.presentation.spawnWaterSplash)
    {
        decision.commands.push_back(ProjectileCollisionResolutionCommand::SpawnWaterSplash);
    }
    else if (decision.presentation.spawnProjectileImpact)
    {
        decision.commands.push_back(ProjectileCollisionResolutionCommand::SpawnProjectileImpact);
    }

    decision.commands.push_back(ProjectileCollisionResolutionCommand::ExpireProjectile);
    return decision;
}

GameplayProjectileService::ProjectileCollisionFrameDecision
GameplayProjectileService::buildProjectileCollisionFrameDecision(
    const ProjectileState &projectile,
    const ProjectileBounceSurfaceFacts &bounceSurfaceFacts,
    const ProjectileCollisionOutcomeInput &outcomeInput,
    const ProjectileCollisionPresentationInput &presentationInput,
    float bounceStopVelocity) const
{
    ProjectileCollisionFrameDecision decision = {};
    const ProjectileImpactDecision impactDecision =
        buildProjectileImpactDecision(projectile, ProjectileImpactReason::Collision);

    decision.bounce = buildProjectileBounceDecision(
        projectile,
        bounceSurfaceFacts,
        bounceStopVelocity);

    if (decision.bounce.shouldBounce)
    {
        decision.commands.push_back(ProjectileCollisionFrameCommand::ApplyBounce);
        return decision;
    }

    decision.resolution = buildProjectileCollisionResolutionDecision(
        impactDecision,
        outcomeInput,
        presentationInput);
    decision.commands.push_back(ProjectileCollisionFrameCommand::ApplyResolution);
    return decision;
}

GameplayProjectileService::ProjectileUpdateFrameDecision
GameplayProjectileService::buildProjectileUpdateFrameDecision(
    const ProjectileState &projectile,
    const ProjectileFrameAdvanceResult &frameAdvance,
    bool collisionHit,
    const ProjectileBounceSurfaceFacts &bounceSurfaceFacts,
    const ProjectileCollisionOutcomeInput &outcomeInput,
    const ProjectileCollisionPresentationInput &presentationInput,
    float bounceStopVelocity) const
{
    ProjectileUpdateFrameDecision decision = {};
    decision.frameAdvance = frameAdvance;

    if (frameAdvance.kind == ProjectileFrameAdvanceKind::LifetimeExpired)
    {
        decision.commands.push_back(ProjectileUpdateFrameCommand::ApplyLifetimeExpiry);
        return decision;
    }

    if (collisionHit)
    {
        decision.collisionFrame = buildProjectileCollisionFrameDecision(
            projectile,
            bounceSurfaceFacts,
            outcomeInput,
            presentationInput,
            bounceStopVelocity);
        decision.commands.push_back(ProjectileUpdateFrameCommand::ApplyCollisionFrame);
        return decision;
    }

    decision.commands.push_back(ProjectileUpdateFrameCommand::ApplyMotionEnd);
    return decision;
}

bool GameplayProjectileService::canProjectileCollideWithParty(const ProjectileState &projectile) const
{
    return projectile.sourceKind != ProjectileState::SourceKind::Party;
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

bool GameplayProjectileService::canProjectileCollideWithActor(
    const ProjectileState &projectile,
    const ProjectileCollisionActorFacts &actorFacts) const
{
    if (actorFacts.dead
        || actorFacts.unavailableForCombat
        || actorFacts.actorId == projectile.sourceId)
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

uint32_t GameplayProjectileService::fireSpikeLimitForMastery(uint32_t skillMastery) const
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

GameplayProjectileService::FireSpikeTrapSpawnLimitDecision
GameplayProjectileService::buildFireSpikeTrapSpawnLimitDecision(
    const FireSpikeTrapSpawnLimitInput &input) const
{
    FireSpikeTrapSpawnLimitDecision decision = {};
    decision.activeLimit = fireSpikeLimitForMastery(input.skillMastery);

    for (const FireSpikeActiveTrapFacts &trap : input.traps)
    {
        if (trap.expired
            || trap.sourceKind != input.sourceKind
            || trap.sourcePartyMemberIndex != input.sourcePartyMemberIndex)
        {
            continue;
        }

        ++decision.activeCount;
    }

    decision.canSpawn = decision.activeCount < decision.activeLimit;
    return decision;
}

GameplayProjectileService::FireSpikeTrapSpawnDecision GameplayProjectileService::buildFireSpikeTrapSpawnDecision(
    const FireSpikeTrapSpawnLimitInput &input)
{
    const FireSpikeTrapSpawnLimitDecision limitDecision = buildFireSpikeTrapSpawnLimitDecision(input);
    FireSpikeTrapSpawnDecision decision = {};
    decision.activeLimit = limitDecision.activeLimit;
    decision.activeCount = limitDecision.activeCount;
    decision.accepted = limitDecision.canSpawn;

    if (decision.accepted)
    {
        decision.trapId = allocateFireSpikeTrapId();
    }

    return decision;
}

GameplayProjectileService::FireSpikeTrapLifetimeFrame GameplayProjectileService::advanceFireSpikeTrapLifetime(
    uint32_t timeSinceCreatedTicks,
    float deltaSeconds) const
{
    FireSpikeTrapLifetimeFrame frame = {};
    frame.timeSinceCreatedTicks = timeSinceCreatedTicks + ticksFromDeltaSeconds(deltaSeconds);
    return frame;
}

GameplayProjectileService::FireSpikeTrapTriggerDecision
GameplayProjectileService::buildFireSpikeTrapTriggerDecision(
    const FireSpikeTrapTriggerInput &input) const
{
    FireSpikeTrapTriggerDecision decision = {};
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
            decision.triggered = true;
            decision.actorIndex = actor.actorIndex;
            decision.actorId = actor.actorId;
        }
    }

    if (decision.triggered)
    {
        decision.damage = rollFireSpikeDamage(
            input.skillLevel,
            input.skillMastery,
            input.trapId ^ static_cast<uint32_t>(decision.actorId * 2654435761u));
        decision.commands.push_back(FireSpikeTrapTriggerCommand::ApplyActorImpact);
        decision.commands.push_back(FireSpikeTrapTriggerCommand::SpawnImpactPresentation);
        decision.commands.push_back(FireSpikeTrapTriggerCommand::ExpireTrap);
    }

    return decision;
}

GameplayProjectileService::ProjectileState GameplayProjectileService::buildFireSpikeTrapImpactPresentationProjectile(
    const FireSpikeTrapImpactPresentationInput &input)
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
        state.radius = projectile.radius;
        state.height = projectile.height;
        state.spellId = projectile.spellId;
        state.objectName = projectile.objectName;
        state.objectSpriteName = projectile.objectSpriteName;
        state.x = projectile.x;
        state.y = projectile.y;
        state.z = projectile.z;
        state.velocityX = projectile.velocityX;
        state.velocityY = projectile.velocityY;
        state.velocityZ = projectile.velocityZ;
        state.timeSinceCreatedTicks = projectile.timeSinceCreatedTicks;
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
        state.objectName = impact.objectName;
        state.objectSpriteName = impact.objectSpriteName;
        state.sourceObjectName = impact.sourceObjectName;
        state.sourceObjectSpriteName = impact.sourceObjectSpriteName;
        state.x = impact.x;
        state.y = impact.y;
        state.z = impact.z;
        state.timeSinceCreatedTicks = impact.timeSinceCreatedTicks;
        state.freezeAnimation = impact.freezeAnimation;
        impacts.push_back(std::move(state));
    }
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

int16_t GameplayProjectileService::waterSplashObjectId()
{
    return 800;
}
}
