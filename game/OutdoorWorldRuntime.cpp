#include "game/OutdoorWorldRuntime.h"

#include "game/ItemTable.h"
#include "game/OutdoorGeometryUtils.h"
#include "game/SkillData.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <random>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t ChestItemRecordSize = 36;
constexpr int RandomChestItemMinLevel = 1;
constexpr int RandomChestItemMaxLevel = 7;
constexpr int SpawnableItemTreasureLevels = 6;
constexpr float GameMinutesPerRealSecond = 0.5f;
constexpr uint32_t ActorInvisibleBit = 0x00010000u;
constexpr uint32_t ActorAggressorBit = 0x00080000u;
constexpr uint32_t CheckActorKilledByAny = 0;
constexpr uint32_t CheckActorKilledByGroup = 1;
constexpr uint32_t CheckActorKilledByMonsterId = 2;
constexpr uint32_t CheckActorKilledByActorIdOe = 3;
constexpr uint32_t CheckActorKilledByActorIdMm8 = 4;
constexpr float TicksPerSecond = 128.0f;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr float OeMeleeRange = 307.2f;
constexpr float HostilityCloseRange = 1024.0f;
constexpr float HostilityShortRange = 2560.0f;
constexpr float HostilityMediumRange = 5120.0f;
constexpr float HostilityLongRange = 10240.0f;
constexpr float ActiveActorUpdateRange = 6144.0f;
constexpr size_t MaxActiveActorUpdates = 48;
constexpr float PeasantAggroRadius = 4096.0f;
constexpr float FleeThresholdRange = 10240.0f;
constexpr float PartyCollisionRadius = 37.0f;
constexpr float PartyCollisionHeight = 192.0f;
constexpr float OutdoorFaceSpatialCellSize = 2048.0f;
constexpr bool DebugProjectileSpawnLogging = false;
constexpr bool DebugProjectileCollisionLogging = false;
constexpr bool DebugProjectileLifetimeLogging = false;
constexpr bool DebugProjectileImpactLogging = false;
constexpr bool DebugProjectileAoeLogging = false;
constexpr bool DebugChestPopulateLogging = false;
constexpr std::array<std::array<int, 3>, 4> EncounterDifficultyTierWeights = {{
    {{100, 0, 0}},
    {{90, 8, 2}},
    {{70, 20, 10}},
    {{50, 30, 20}},
}};
constexpr float GroundSnapHeight = 1.0f;
constexpr float OeNonFlyingActorRadius = 40.0f;
constexpr float ActorUpdateStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedActorUpdateSeconds = 0.1f;
constexpr float Pi = 3.14159265358979323846f;
constexpr float PartyTargetHeightOffset = 96.0f;
constexpr float OeTurnAwayFromWaterAngleRadians = Pi / 32.0f;
constexpr int DwiMapId = 1;
constexpr uint32_t DwiTestActor61 = 61;
constexpr float DwiTestActor61X = -7665.0f;
constexpr float DwiTestActor61Y = -4660.0f;
constexpr float DwiTestActor61Z = 200.0f;
constexpr uint32_t EventSpellSourceId = std::numeric_limits<uint32_t>::max();
constexpr uint32_t FireballSpellId = 6;
constexpr uint32_t MeteorShowerSpellId = 9;
constexpr uint32_t StarburstSpellId = 22;
constexpr uint32_t DragonBreathSpellId = 97;
constexpr float MeteorShowerSpawnBaseHeight = 2500.0f;
constexpr float MeteorShowerSpawnHeightVariance = 1000.0f;
constexpr float MeteorShowerTargetSpread = 512.0f;
constexpr float SpellImpactAoeRadius = 512.0f;

std::string debugStringOrNone(const std::string &value)
{
    if (value.empty())
    {
        return "<none>";
    }

    return value;
}

const char *monsterAttackAbilityName(OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    switch (ability)
    {
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack1:
            return "attack1";
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack2:
            return "attack2";
        case OutdoorWorldRuntime::MonsterAttackAbility::Spell1:
            return "spell1";
        case OutdoorWorldRuntime::MonsterAttackAbility::Spell2:
            return "spell2";
        default:
            return "unknown";
    }
}

const char *spellSourceKindName(OutdoorWorldRuntime::RuntimeSpellSourceKind sourceKind)
{
    switch (sourceKind)
    {
        case OutdoorWorldRuntime::RuntimeSpellSourceKind::Actor:
            return "monster";
        case OutdoorWorldRuntime::RuntimeSpellSourceKind::Event:
            return "event";
        default:
            return "unknown";
    }
}

void logProjectileSpawn(
    const char *sourceKind,
    const OutdoorWorldRuntime::ProjectileState &projectile,
    float directionX,
    float directionY,
    float directionZ,
    float speed)
{
    if (!DebugProjectileSpawnLogging)
    {
        return;
    }

    std::cout
        << "Projectile spawn kind=" << sourceKind
        << " projectile=" << projectile.projectileId
        << " source=" << projectile.sourceId
        << " ability=" << monsterAttackAbilityName(projectile.ability)
        << " object=\"" << debugStringOrNone(projectile.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(projectile.objectSpriteName) << "\""
        << " spriteId=" << projectile.objectSpriteId
        << " pos=(" << projectile.x << ", " << projectile.y << ", " << projectile.z << ")"
        << " dir=(" << directionX << ", " << directionY << ", " << directionZ << ")"
        << " speed=" << speed
        << " velocity=(" << projectile.velocityX << ", " << projectile.velocityY << ", " << projectile.velocityZ << ")"
        << " radius=" << projectile.radius
        << " height=" << projectile.height
        << " lifetimeTicks=" << projectile.lifetimeTicks
        << " spellId=" << projectile.spellId
        << '\n';
}

void logProjectileCollision(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const char *colliderKind,
    const std::string &colliderName,
    const bx::Vec3 &point)
{
    if (!DebugProjectileCollisionLogging)
    {
        return;
    }

    std::cout
        << "Projectile collision projectile=" << projectile.projectileId
        << " source=" << projectile.sourceId
        << " ability=" << monsterAttackAbilityName(projectile.ability)
        << " object=\"" << debugStringOrNone(projectile.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(projectile.objectSpriteName) << "\""
        << " collider=" << colliderKind
        << " target=\"" << debugStringOrNone(colliderName) << "\""
        << " pos=(" << point.x << ", " << point.y << ", " << point.z << ")"
        << '\n';
}

void logProjectileLifetimeExpiry(const OutdoorWorldRuntime::ProjectileState &projectile)
{
    if (!DebugProjectileLifetimeLogging)
    {
        return;
    }

    std::cout
        << "Projectile expired projectile=" << projectile.projectileId
        << " source=" << projectile.sourceId
        << " ability=" << monsterAttackAbilityName(projectile.ability)
        << " object=\"" << debugStringOrNone(projectile.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(projectile.objectSpriteName) << "\""
        << " pos=(" << projectile.x << ", " << projectile.y << ", " << projectile.z << ")"
        << " lifetimeTicks=" << projectile.lifetimeTicks
        << " ageTicks=" << projectile.timeSinceCreatedTicks
        << '\n';
}

void logProjectileImpactEffect(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const OutdoorWorldRuntime::ProjectileImpactState &effect)
{
    if (!DebugProjectileImpactLogging)
    {
        return;
    }

    std::cout
        << "Projectile impact effect projectile=" << projectile.projectileId
        << " effect=" << effect.effectId
        << " object=\"" << debugStringOrNone(effect.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(effect.objectSpriteName) << "\""
        << " spriteId=" << effect.objectSpriteId
        << " pos=(" << effect.x << ", " << effect.y << ", " << effect.z << ")"
        << '\n';
}

void logProjectileAoeHit(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const char *pTargetKind,
    const bx::Vec3 &impactPoint,
    float radius)
{
    if (!DebugProjectileAoeLogging)
    {
        return;
    }

    std::cout
        << "Projectile aoe hit projectile=" << projectile.projectileId
        << " source=" << projectile.sourceId
        << " ability=" << monsterAttackAbilityName(projectile.ability)
        << " object=\"" << debugStringOrNone(projectile.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(projectile.objectSpriteName) << "\""
        << " spellId=" << projectile.spellId
        << " target=" << pTargetKind
        << " radius=" << radius
        << " pos=(" << impactPoint.x << ", " << impactPoint.y << ", " << impactPoint.z << ")"
        << '\n';
}

float clampLength(float value, float maxValue)
{
    if (value > maxValue)
    {
        return maxValue;
    }

    if (value < -maxValue)
    {
        return -maxValue;
    }

    return value;
}

float length2d(float x, float y)
{
    return std::sqrt(x * x + y * y);
}

float length3d(float x, float y, float z)
{
    return std::sqrt(x * x + y * y + z * z);
}

float pointSegmentDistanceSquared2d(
    float pointX,
    float pointY,
    float segmentStartX,
    float segmentStartY,
    float segmentEndX,
    float segmentEndY,
    float &projectionFactor)
{
    const float segmentDeltaX = segmentEndX - segmentStartX;
    const float segmentDeltaY = segmentEndY - segmentStartY;
    const float segmentLengthSquared = segmentDeltaX * segmentDeltaX + segmentDeltaY * segmentDeltaY;

    if (segmentLengthSquared <= 0.0001f)
    {
        projectionFactor = 0.0f;
        const float deltaX = pointX - segmentStartX;
        const float deltaY = pointY - segmentStartY;
        return deltaX * deltaX + deltaY * deltaY;
    }

    projectionFactor =
        ((pointX - segmentStartX) * segmentDeltaX + (pointY - segmentStartY) * segmentDeltaY) / segmentLengthSquared;
    projectionFactor = std::clamp(projectionFactor, 0.0f, 1.0f);
    const float closestX = segmentStartX + segmentDeltaX * projectionFactor;
    const float closestY = segmentStartY + segmentDeltaY * projectionFactor;
    const float deltaX = pointX - closestX;
    const float deltaY = pointY - closestY;
    return deltaX * deltaX + deltaY * deltaY;
}

float normalizeAngleRadians(float angle)
{
    while (angle <= -Pi)
    {
        angle += 2.0f * Pi;
    }

    while (angle > Pi)
    {
        angle -= 2.0f * Pi;
    }

    return angle;
}

float shortestAngleDistanceRadians(float left, float right)
{
    return std::abs(normalizeAngleRadians(left - right));
}

float lengthSquared3d(float x, float y, float z)
{
    return x * x + y * y + z * z;
}

void faceDirection(OutdoorWorldRuntime::MapActorState &actor, float deltaX, float deltaY);

float hostilityRangeForRelation(int relation)
{
    switch (relation)
    {
        case 1:
            return HostilityCloseRange;
        case 2:
            return HostilityShortRange;
        case 3:
            return HostilityMediumRange;
        case 4:
            return HostilityLongRange;
        default:
            return 0.0f;
    }
}

float hostilityPromotionRangeForFriendlyActor(int relation)
{
    switch (relation)
    {
        case 1:
            return 0.0f;
        case 2:
            return HostilityCloseRange;
        case 3:
            return HostilityShortRange;
        case 4:
            return HostilityMediumRange;
        default:
            return -1.0f;
    }
}

bool isWithinRange3d(float x, float y, float z, float range)
{
    return range > 0.0f && lengthSquared3d(x, y, z) <= range * range;
}

float meleeRangeForCombatTarget(bool targetIsActor)
{
    return targetIsActor ? OeMeleeRange * 0.5f : OeMeleeRange;
}

bool isOutdoorLandMaskWater(const std::optional<std::vector<uint8_t>> &outdoorLandMask, float x, float y)
{
    if (!outdoorLandMask || outdoorLandMask->empty())
    {
        return false;
    }

    const float gridX = 64.0f - (x / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const float gridY = 64.0f - (y / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const int tileX = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int tileY = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    const int landMaskWidth = OutdoorMapData::TerrainWidth - 1;
    const size_t tileIndex = static_cast<size_t>(tileY * landMaskWidth + tileX);

    if (tileIndex >= outdoorLandMask->size())
    {
        return false;
    }

    return (*outdoorLandMask)[tileIndex] == 0;
}

bool isOutdoorMonsterWaterTile(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    float x,
    float y)
{
    return isOutdoorTerrainWater(outdoorMapData, x, y) || isOutdoorLandMaskWater(outdoorLandMask, x, y);
}

bool canMonsterWalkOnWater(const MonsterTable::MonsterStatsEntry *pStats)
{
    if (pStats == nullptr)
    {
        return false;
    }

    return toLowerCopy(pStats->pictureName).find("water elemental") != std::string::npos;
}

bx::Vec3 outdoorTerrainTileCenter(int tileX, int tileY)
{
    return {
        (64.0f - (static_cast<float>(tileX) + 0.5f)) * static_cast<float>(OutdoorMapData::TerrainTileSize),
        (64.0f - (static_cast<float>(tileY) + 0.5f)) * static_cast<float>(OutdoorMapData::TerrainTileSize),
        0.0f
    };
}

bool findNearbyLandDirection(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    float actorX,
    float actorY,
    float &directionX,
    float &directionY)
{
    const float gridX = 64.0f - (actorX / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const float gridY = 64.0f - (actorY / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const int tileX = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int tileY = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    float bestDistanceSquared = std::numeric_limits<float>::max();
    bool found = false;

    for (int candidateY = tileY - 1; candidateY <= tileY + 1; ++candidateY)
    {
        if (candidateY < 0 || candidateY >= OutdoorMapData::TerrainHeight - 1)
        {
            continue;
        }

        for (int candidateX = tileX - 1; candidateX <= tileX + 1; ++candidateX)
        {
            if (candidateX < 0 || candidateX >= OutdoorMapData::TerrainWidth - 1)
            {
                continue;
            }

            const bx::Vec3 center = outdoorTerrainTileCenter(candidateX, candidateY);

            if (isOutdoorMonsterWaterTile(outdoorMapData, outdoorLandMask, center.x, center.y))
            {
                continue;
            }

            const float deltaX = center.x - actorX;
            const float deltaY = center.y - actorY;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY;

            if (distanceSquared >= bestDistanceSquared || distanceSquared <= 0.01f)
            {
                continue;
            }

            bestDistanceSquared = distanceSquared;
            directionX = deltaX;
            directionY = deltaY;
            found = true;
        }
    }

    if (!found)
    {
        return false;
    }

    const float distance = length2d(directionX, directionY);

    if (distance <= 0.01f)
    {
        return false;
    }

    directionX /= distance;
    directionY /= distance;
    return true;
}

enum class OutdoorWaterRestrictionResult
{
    None,
    RedirectedToLand,
    BlockedByWater,
};

void rotateDirectionClockwise(float &directionX, float &directionY, float radians)
{
    const float cosine = std::cos(radians);
    const float sine = std::sin(radians);
    const float rotatedX = directionX * cosine + directionY * sine;
    const float rotatedY = -directionX * sine + directionY * cosine;
    directionX = rotatedX;
    directionY = rotatedY;
}

OutdoorWaterRestrictionResult applyOutdoorWaterRestriction(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const MonsterTable::MonsterStatsEntry *pStats,
    OutdoorWorldRuntime::MapActorState &actor,
    float moveSpeed,
    float &desiredMoveX,
    float &desiredMoveY,
    OutdoorWorldRuntime::ActorAiState &nextAiState,
    OutdoorWorldRuntime::ActorAnimation &nextAnimation)
{
    if (pStats == nullptr
        || pStats->canFly
        || canMonsterWalkOnWater(pStats)
        || (std::abs(desiredMoveX) <= 0.001f && std::abs(desiredMoveY) <= 0.001f))
    {
        return OutdoorWaterRestrictionResult::None;
    }

    const bool onWater = isOutdoorMonsterWaterTile(outdoorMapData, outdoorLandMask, actor.preciseX, actor.preciseY);

    if (onWater)
    {
        float shoreDirectionX = 0.0f;
        float shoreDirectionY = 0.0f;

        if (!findNearbyLandDirection(
                outdoorMapData,
                outdoorLandMask,
                actor.preciseX,
                actor.preciseY,
                shoreDirectionX,
                shoreDirectionY))
        {
            desiredMoveX = 0.0f;
            desiredMoveY = 0.0f;
            return OutdoorWaterRestrictionResult::BlockedByWater;
        }

        desiredMoveX = shoreDirectionX;
        desiredMoveY = shoreDirectionY;
        faceDirection(actor, desiredMoveX, desiredMoveY);
        nextAiState = OutdoorWorldRuntime::ActorAiState::Fleeing;
        nextAnimation = OutdoorWorldRuntime::ActorAnimation::Walking;
        return OutdoorWaterRestrictionResult::RedirectedToLand;
    }

    const float moveDeltaX = desiredMoveX * moveSpeed * ActorUpdateStepSeconds;
    const float moveDeltaY = desiredMoveY * moveSpeed * ActorUpdateStepSeconds;
    const float candidateX = actor.preciseX + moveDeltaX;
    const float candidateY = actor.preciseY + moveDeltaY;

    if (!isOutdoorMonsterWaterTile(outdoorMapData, outdoorLandMask, candidateX, candidateY))
    {
        return OutdoorWaterRestrictionResult::None;
    }

    rotateDirectionClockwise(desiredMoveX, desiredMoveY, OeTurnAwayFromWaterAngleRadians);
    const float rotatedLength = length2d(desiredMoveX, desiredMoveY);

    if (rotatedLength > 0.01f)
    {
        desiredMoveX /= rotatedLength;
        desiredMoveY /= rotatedLength;
    }
    else
    {
        desiredMoveX = 0.0f;
        desiredMoveY = 0.0f;
    }

    const float rotatedCandidateX = actor.preciseX + desiredMoveX * moveSpeed * ActorUpdateStepSeconds;
    const float rotatedCandidateY = actor.preciseY + desiredMoveY * moveSpeed * ActorUpdateStepSeconds;

    if (length2d(desiredMoveX, desiredMoveY) <= 0.001f
        || isOutdoorMonsterWaterTile(outdoorMapData, outdoorLandMask, rotatedCandidateX, rotatedCandidateY))
    {
        desiredMoveX = 0.0f;
        desiredMoveY = 0.0f;
        return OutdoorWaterRestrictionResult::BlockedByWater;
    }

    faceDirection(actor, desiredMoveX, desiredMoveY);
    nextAiState = OutdoorWorldRuntime::ActorAiState::Fleeing;
    nextAnimation = OutdoorWorldRuntime::ActorAnimation::Walking;
    return OutdoorWaterRestrictionResult::RedirectedToLand;
}

void faceDirection(OutdoorWorldRuntime::MapActorState &actor, float deltaX, float deltaY)
{
    if (std::abs(deltaX) <= 0.01f && std::abs(deltaY) <= 0.01f)
    {
        return;
    }

    actor.yawRadians = std::atan2(deltaY, deltaX);
}

float monsterRecoverySeconds(int recoveryTicks)
{
    return std::max(0.3f, static_cast<float>(recoveryTicks) / TicksPerSecond * OeRealtimeRecoveryScale);
}

bool isProjectileSpellName(const std::string &spellName)
{
    static const std::vector<std::string> projectileSpellNames = {
        "fire bolt",
        "fireball",
        "incinerate",
        "lightning bolt",
        "ice bolt",
        "acid burst",
        "blades",
        "rock blast",
        "mind blast",
        "psychic shock",
        "harm",
        "light bolt",
        "toxic cloud",
        "dragon breath",
    };

    return std::find(projectileSpellNames.begin(), projectileSpellNames.end(), toLowerCopy(spellName))
        != projectileSpellNames.end();
}

bool resolveProjectileDefinition(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability,
    const MonsterProjectileTable &projectileTable,
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    OutdoorWorldRuntime::ResolvedProjectileDefinition &definition)
{
    definition = {};

    if (ability == OutdoorWorldRuntime::MonsterAttackAbility::Attack1
        || ability == OutdoorWorldRuntime::MonsterAttackAbility::Attack2)
    {
        const std::string &projectileToken =
            ability == OutdoorWorldRuntime::MonsterAttackAbility::Attack1
                ? stats.attack1MissileType
                : stats.attack2MissileType;
        const MonsterProjectileEntry *pProjectileEntry = projectileTable.findByToken(projectileToken);

        if (pProjectileEntry == nullptr)
        {
            return false;
        }

        const ObjectEntry *pObjectEntry = objectTable.findByObjectId(static_cast<int16_t>(pProjectileEntry->objectId));

        if (pObjectEntry == nullptr)
        {
            return false;
        }

        const std::optional<uint16_t> objectDescriptionId =
            objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pProjectileEntry->objectId));

        if (!objectDescriptionId)
        {
            return false;
        }

        definition.objectDescriptionId = *objectDescriptionId;
        definition.objectSpriteId = pObjectEntry->spriteId;
        definition.radius = static_cast<uint16_t>(std::max<int>(pObjectEntry->radius, 16));
        definition.height = static_cast<uint16_t>(std::max<int>(pObjectEntry->height, 16));
        definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pObjectEntry->lifetimeTicks, 64));
        definition.speed = static_cast<float>(std::max<int>(pObjectEntry->speed, 2000));
        definition.objectName = pObjectEntry->internalName;
        definition.objectSpriteName = pObjectEntry->spriteName;

        if (pProjectileEntry->impactObjectId > 0)
        {
            const ObjectEntry *pImpactEntry =
                objectTable.findByObjectId(static_cast<int16_t>(pProjectileEntry->impactObjectId));
            const std::optional<uint16_t> impactDescriptionId =
                objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pProjectileEntry->impactObjectId));

            if (pImpactEntry != nullptr && impactDescriptionId)
            {
                definition.impactObjectDescriptionId = *impactDescriptionId;
                definition.impactObjectSpriteId = pImpactEntry->spriteId;
                definition.impactObjectName = pImpactEntry->internalName;
                definition.impactObjectSpriteName = pImpactEntry->spriteName;
            }
        }

        return true;
    }

    const std::string &spellName =
        ability == OutdoorWorldRuntime::MonsterAttackAbility::Spell1 ? stats.spell1Name : stats.spell2Name;

    if (!isProjectileSpellName(spellName))
    {
        return false;
    }

    const SpellEntry *pSpellEntry = spellTable.findByName(spellName);

    if (pSpellEntry == nullptr || pSpellEntry->displayObjectId <= 0)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = objectTable.findByObjectId(static_cast<int16_t>(pSpellEntry->displayObjectId));
    const std::optional<uint16_t> objectDescriptionId =
        objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pSpellEntry->displayObjectId));

    if (pObjectEntry == nullptr || !objectDescriptionId)
    {
        return false;
    }

    definition.objectDescriptionId = *objectDescriptionId;
    definition.objectSpriteId = pObjectEntry->spriteId;
    definition.radius = static_cast<uint16_t>(std::max<int>(pObjectEntry->radius, 16));
    definition.height = static_cast<uint16_t>(std::max<int>(pObjectEntry->height, 16));
    definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pObjectEntry->lifetimeTicks, 64));
    definition.speed = static_cast<float>(std::max<int>(pObjectEntry->speed, 2000));
    definition.spellId = pSpellEntry->id;
    definition.effectSoundId = pSpellEntry->effectSoundId;
    definition.objectName = pObjectEntry->internalName;
    definition.objectSpriteName = pObjectEntry->spriteName;

    if (pSpellEntry->impactDisplayObjectId > 0)
    {
        const ObjectEntry *pImpactEntry =
            objectTable.findByObjectId(static_cast<int16_t>(pSpellEntry->impactDisplayObjectId));
        const std::optional<uint16_t> impactDescriptionId =
            objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pSpellEntry->impactDisplayObjectId));

        if (pImpactEntry != nullptr && impactDescriptionId)
        {
            definition.impactObjectDescriptionId = *impactDescriptionId;
            definition.impactObjectSpriteId = pImpactEntry->spriteId;
            definition.impactObjectName = pImpactEntry->internalName;
            definition.impactObjectSpriteName = pImpactEntry->spriteName;
        }
    }

    return true;
}

bool resolveSpellDefinition(
    const SpellEntry &spell,
    const ObjectTable &objectTable,
    OutdoorWorldRuntime::ResolvedProjectileDefinition &definition)
{
    definition = {};

    if (spell.displayObjectId <= 0)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = objectTable.findByObjectId(static_cast<int16_t>(spell.displayObjectId));
    const std::optional<uint16_t> objectDescriptionId =
        objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(spell.displayObjectId));

    if (pObjectEntry == nullptr || !objectDescriptionId)
    {
        return false;
    }

    definition.objectDescriptionId = *objectDescriptionId;
    definition.objectSpriteId = pObjectEntry->spriteId;
    definition.radius = static_cast<uint16_t>(std::max<int>(pObjectEntry->radius, 16));
    definition.height = static_cast<uint16_t>(std::max<int>(pObjectEntry->height, 16));
    definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pObjectEntry->lifetimeTicks, 64));
    definition.speed = static_cast<float>(std::max<int>(pObjectEntry->speed, 2000));
    definition.spellId = spell.id;
    definition.effectSoundId = spell.effectSoundId;
    definition.objectName = pObjectEntry->internalName;
    definition.objectSpriteName = pObjectEntry->spriteName;

    if (spell.impactDisplayObjectId > 0)
    {
        const ObjectEntry *pImpactEntry =
            objectTable.findByObjectId(static_cast<int16_t>(spell.impactDisplayObjectId));
        const std::optional<uint16_t> impactDescriptionId =
            objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(spell.impactDisplayObjectId));

        if (pImpactEntry != nullptr && impactDescriptionId)
        {
            definition.impactObjectDescriptionId = *impactDescriptionId;
            definition.impactObjectSpriteId = pImpactEntry->spriteId;
            definition.impactObjectName = pImpactEntry->internalName;
            definition.impactObjectSpriteName = pImpactEntry->spriteName;
        }
    }

    return true;
}

uint32_t meteorShowerCountForMastery(uint32_t skillMastery)
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
            return 8;
        case SkillMastery::None:
        default:
            return 8;
    }
}

int resolveMonsterAbilityDamage(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    auto averageDamage = [](const MonsterTable::MonsterStatsEntry::DamageProfile &profile)
    {
        if (profile.diceRolls <= 0 || profile.diceSides <= 0)
        {
            return std::max(0, profile.bonus);
        }

        return profile.diceRolls * (profile.diceSides + 1) / 2 + profile.bonus;
    };

    const int fallbackAttackDamage = std::max(1, stats.level / 2);
    const int fallbackSpellDamage = std::max(2, stats.level);

    switch (ability)
    {
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack2:
        {
            const int damage = averageDamage(stats.attack2Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
        case OutdoorWorldRuntime::MonsterAttackAbility::Spell1:
        case OutdoorWorldRuntime::MonsterAttackAbility::Spell2:
            return fallbackSpellDamage;
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack1:
        default:
        {
            const int damage = averageDamage(stats.attack1Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
    }
}

int resolveEventSpellDamage(uint32_t spellId, uint32_t skillLevel)
{
    if (spellId == MeteorShowerSpellId)
    {
        return 8 + static_cast<int>(skillLevel);
    }

    return std::max(1, static_cast<int>(skillLevel) * 2);
}

float spellImpactDamageRadius(uint32_t spellId)
{
    switch (spellId)
    {
        case FireballSpellId:
        case MeteorShowerSpellId:
        case StarburstSpellId:
        case DragonBreathSpellId:
            return SpellImpactAoeRadius;
        default:
            return 0.0f;
    }
}

bool isPartyWithinImpactRadius(
    const bx::Vec3 &impactPoint,
    float radius,
    float partyX,
    float partyY,
    float partyZ)
{
    if (radius <= 0.0f)
    {
        return false;
    }

    const float partyCenterZ = partyZ + PartyCollisionHeight * 0.5f;
    const float deltaX = impactPoint.x - partyX;
    const float deltaY = impactPoint.y - partyY;
    const float deltaZ = impactPoint.z - partyCenterZ;
    const float totalRadius = radius + PartyCollisionRadius;
    return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ <= totalRadius * totalRadius;
}

int resolveProjectilePartyImpactDamage(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const MonsterTable *pMonsterTable,
    const std::vector<OutdoorWorldRuntime::MapActorState> &mapActors)
{
    if (projectile.sourceId == EventSpellSourceId)
    {
        return resolveEventSpellDamage(projectile.spellId, projectile.skillLevel);
    }

    if (pMonsterTable == nullptr)
    {
        return 1;
    }

    if (projectile.sourceMonsterId != 0)
    {
        const MonsterTable::MonsterStatsEntry *pStats = pMonsterTable->findStatsById(projectile.sourceMonsterId);
        return pStats != nullptr ? resolveMonsterAbilityDamage(*pStats, projectile.ability) : 1;
    }

    for (const OutdoorWorldRuntime::MapActorState &actor : mapActors)
    {
        if (actor.actorId != projectile.sourceId)
        {
            continue;
        }

        const MonsterTable::MonsterStatsEntry *pStats = pMonsterTable->findStatsById(actor.monsterId);
        return pStats != nullptr ? resolveMonsterAbilityDamage(*pStats, projectile.ability) : 1;
    }

    return 1;
}

float resolveActorGroundZ(
    const OutdoorMapData *pOutdoorMapData,
    const MonsterTable::MonsterStatsEntry *pStats,
    uint16_t radius,
    float x,
    float y,
    float currentZ
)
{
    if (pOutdoorMapData == nullptr)
    {
        return currentZ;
    }

    const float floorZ = sampleOutdoorSupportFloor(
        *pOutdoorMapData,
        x,
        y,
        currentZ,
        5.0f,
        std::max(5.0f, static_cast<float>(radius))).height;

    if (pStats != nullptr && pStats->canFly)
    {
        return std::max(currentZ, floorZ);
    }

    return floorZ;
}

void applyTestActorOverrides(
    int mapId,
    const OutdoorMapData *pOutdoorMapData,
    const MonsterTable::MonsterStatsEntry *pStats,
    uint32_t actorId,
    OutdoorWorldRuntime::MapActorState &state
)
{
    if (mapId == DwiMapId && actorId == DwiTestActor61)
    {
        state.preciseX = DwiTestActor61X;
        state.preciseY = DwiTestActor61Y;
        state.preciseZ = resolveActorGroundZ(
            pOutdoorMapData,
            pStats,
            state.radius,
            DwiTestActor61X,
            DwiTestActor61Y,
            DwiTestActor61Z);
        state.x = static_cast<int>(std::lround(state.preciseX));
        state.y = static_cast<int>(std::lround(state.preciseY));
        state.z = static_cast<int>(std::lround(state.preciseZ));
        state.homePreciseX = state.preciseX;
        state.homePreciseY = state.preciseY;
        state.homePreciseZ = state.preciseZ;
        state.homeX = state.x;
        state.homeY = state.y;
        state.homeZ = state.z;
    }
}

float resolveInitialActorGroundZ(
    const OutdoorMapData *pOutdoorMapData,
    const MonsterTable::MonsterStatsEntry *pStats,
    uint16_t radius,
    float x,
    float y,
    float currentZ
)
{
    if (pOutdoorMapData == nullptr)
    {
        return currentZ;
    }

    const float floorZ = sampleOutdoorSupportFloor(
        *pOutdoorMapData,
        x,
        y,
        currentZ,
        std::numeric_limits<float>::max(),
        std::max(5.0f, static_cast<float>(radius))).height;

    if (pStats != nullptr && pStats->canFly)
    {
        return std::max(currentZ, floorZ);
    }

    return floorZ;
}

float actorCollisionRadius(
    const OutdoorWorldRuntime::MapActorState &actor,
    const MonsterTable::MonsterStatsEntry *pStats)
{
    if (pStats != nullptr && !pStats->canFly)
    {
        return OeNonFlyingActorRadius;
    }

    if (actor.radius > 0)
    {
        return static_cast<float>(actor.radius);
    }

    return OeNonFlyingActorRadius;
}

float actorCollisionHeight(
    const OutdoorWorldRuntime::MapActorState &actor,
    float collisionRadius)
{
    if (actor.height > 0)
    {
        return std::max(static_cast<float>(actor.height), collisionRadius * 2.0f + 2.0f);
    }

    return collisionRadius * 2.0f + 2.0f;
}

bool isActorUnavailableForCombat(const OutdoorWorldRuntime::MapActorState &actor);

std::vector<OutdoorActorCollision> buildNearbyActorMovementColliders(
    const std::vector<OutdoorWorldRuntime::MapActorState> &mapActors,
    const std::vector<bool> &activeActorMask,
    const MonsterTable &monsterTable)
{
    std::vector<OutdoorActorCollision> colliders;

    if (mapActors.empty())
    {
        return colliders;
    }

    colliders.reserve(mapActors.size());

    for (size_t actorIndex = 0; actorIndex < mapActors.size(); ++actorIndex)
    {
        if (actorIndex >= activeActorMask.size() || !activeActorMask[actorIndex])
        {
            continue;
        }

        const OutdoorWorldRuntime::MapActorState &actor = mapActors[actorIndex];

        if (isActorUnavailableForCombat(actor))
        {
            continue;
        }

        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actor.monsterId);
        const float collisionRadius = actorCollisionRadius(actor, pStats);
        const float collisionHeight = actorCollisionHeight(actor, collisionRadius);

        if (collisionRadius <= 0.0f || collisionHeight <= 0.0f)
        {
            continue;
        }

        OutdoorActorCollision collider = {};
        collider.source = OutdoorActorCollisionSource::MapDelta;
        collider.sourceIndex = actorIndex;
        collider.radius = static_cast<uint16_t>(std::lround(collisionRadius));
        collider.height = static_cast<uint16_t>(std::lround(collisionHeight));
        collider.worldX = static_cast<int>(std::lround(actor.preciseX));
        collider.worldY = static_cast<int>(std::lround(actor.preciseY));
        collider.worldZ = static_cast<int>(std::lround(actor.preciseZ + GroundSnapHeight));
        collider.group = actor.group;
        collider.name = actor.displayName;
        colliders.push_back(std::move(collider));
    }

    return colliders;
}

void syncActorFromMovementState(OutdoorWorldRuntime::MapActorState &actor)
{
    actor.preciseX = actor.movementState.x;
    actor.preciseY = actor.movementState.y;
    actor.preciseZ = actor.movementState.footZ - GroundSnapHeight;
    actor.x = static_cast<int>(std::lround(actor.preciseX));
    actor.y = static_cast<int>(std::lround(actor.preciseY));
    actor.z = static_cast<int>(std::lround(actor.preciseZ));
}

bool tryMoveActorInWorld(
    OutdoorWorldRuntime::MapActorState &actor,
    const OutdoorMapData &outdoorMapData,
    const std::vector<OutdoorFaceGeometryData> &faces,
    const MonsterTable::MonsterStatsEntry *pStats,
    float deltaX,
    float deltaY
)
{
    const float candidateX = actor.preciseX + deltaX;
    const float candidateY = actor.preciseY + deltaY;
    const bool canFly = pStats != nullptr && pStats->canFly;

    if (!canFly && outdoorTerrainSlopeTooHigh(outdoorMapData, candidateX, candidateY))
    {
        const float terrainHeight = sampleOutdoorTerrainHeight(outdoorMapData, candidateX, candidateY);

        if (terrainHeight > actor.preciseZ + 8.0f)
        {
            return false;
        }
    }

    const float candidateZ = resolveActorGroundZ(
        &outdoorMapData,
        pStats,
        actor.radius,
        candidateX,
        candidateY,
        actor.preciseZ);
    const float radius = static_cast<float>(actor.radius > 0 ? actor.radius : 40);
    const float height = static_cast<float>(actor.height > 0 ? actor.height : 120);

    for (const OutdoorFaceGeometryData &face : faces)
    {
        if (face.isWalkable)
        {
            continue;
        }

        if (isOutdoorCylinderBlockedByFace(face, candidateX, candidateY, candidateZ, radius, height))
        {
            return false;
        }
    }

    actor.preciseX = candidateX;
    actor.preciseY = candidateY;
    actor.preciseZ = candidateZ;
    return true;
}

bool segmentMayTouchFaceBounds(
    const bx::Vec3 &segmentStart,
    const bx::Vec3 &segmentEnd,
    const OutdoorFaceGeometryData &face,
    float padding)
{
    const float segmentMinX = std::min(segmentStart.x, segmentEnd.x) - padding;
    const float segmentMaxX = std::max(segmentStart.x, segmentEnd.x) + padding;
    const float segmentMinY = std::min(segmentStart.y, segmentEnd.y) - padding;
    const float segmentMaxY = std::max(segmentStart.y, segmentEnd.y) + padding;
    const float segmentMinZ = std::min(segmentStart.z, segmentEnd.z) - padding;
    const float segmentMaxZ = std::max(segmentStart.z, segmentEnd.z) + padding;

    if (segmentMaxX < face.minX || segmentMinX > face.maxX)
    {
        return false;
    }

    if (segmentMaxY < face.minY || segmentMinY > face.maxY)
    {
        return false;
    }

    if (segmentMaxZ < face.minZ || segmentMinZ > face.maxZ)
    {
        return false;
    }

    return true;
}

std::vector<int> parseCsvIntegers(const std::optional<std::string> &note)
{
    std::vector<int> values;

    if (!note || note->empty())
    {
        return values;
    }

    std::istringstream stream(*note);
    std::string token;

    while (std::getline(stream, token, ','))
    {
        if (token.empty())
        {
            values.push_back(0);
            continue;
        }

        try
        {
            values.push_back(std::stoi(token));
        }
        catch (...)
        {
            values.push_back(0);
        }
    }

    return values;
}

void appendTimersFromProgram(
    const std::optional<EventIrProgram> &program,
    std::vector<OutdoorWorldRuntime::TimerState> &timers
)
{
    if (!program)
    {
        return;
    }

    for (const EventIrEvent &event : program->getEvents())
    {
        for (const EventIrInstruction &instruction : event.instructions)
        {
            if (instruction.operation != EventIrOperation::TriggerOnTimer)
            {
                continue;
            }

            const std::vector<int> values = parseCsvIntegers(instruction.note);
            OutdoorWorldRuntime::TimerState timer = {};
            timer.eventId = event.eventId;

            if (values.size() > 6 && values[6] > 0)
            {
                timer.repeating = true;
                timer.intervalGameMinutes = static_cast<float>(values[6]) * 0.5f;
                timer.remainingGameMinutes = timer.intervalGameMinutes;
                timers.push_back(timer);
                break;
            }

            if (values.size() > 3 && values[3] > 0)
            {
                timer.repeating = false;
                timer.targetHour = values[3];
                timer.intervalGameMinutes = static_cast<float>(values[3]) * 60.0f;
                timer.remainingGameMinutes = timer.intervalGameMinutes - 9.0f * 60.0f;

                if (timer.remainingGameMinutes < 0.0f)
                {
                    timer.remainingGameMinutes += 24.0f * 60.0f;
                }

                timers.push_back(timer);
                break;
            }
        }
    }
}

const MapEncounterInfo *getEncounterInfo(const MapStatsEntry &map, int encounterSlot)
{
    if (encounterSlot == 1)
    {
        return &map.encounter1;
    }

    if (encounterSlot == 2)
    {
        return &map.encounter2;
    }

    if (encounterSlot == 3)
    {
        return &map.encounter3;
    }

    return nullptr;
}

int16_t resolveMapActorMonsterId(const MapDeltaActor &actor)
{
    if (actor.monsterInfoId > 0)
    {
        return actor.monsterInfoId;
    }

    if (actor.monsterId > 0)
    {
        return actor.monsterId;
    }

    return 0;
}

const MonsterEntry *resolveMonsterEntry(
    const MonsterTable &monsterTable,
    int16_t monsterId,
    const MonsterTable::MonsterStatsEntry *pStats
)
{
    if (pStats != nullptr && !pStats->pictureName.empty())
    {
        if (const MonsterEntry *pEntry = monsterTable.findByInternalName(pStats->pictureName))
        {
            return pEntry;
        }
    }

    return monsterTable.findById(monsterId);
}

OutdoorWorldRuntime::MapActorState buildMapActorState(
    const MonsterTable &monsterTable,
    const MapDeltaActor &actor,
    uint32_t actorId,
    const OutdoorMapData *pOutdoorMapData,
    float attackAnimationSeconds
)
{
    OutdoorWorldRuntime::MapActorState state = {};
    state.actorId = actorId;
    state.monsterId = resolveMapActorMonsterId(actor);
    state.group = actor.group;

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(state.monsterId);
    const MonsterEntry *pMonsterEntry = resolveMonsterEntry(monsterTable, state.monsterId, pStats);
    state.displayName = pStats != nullptr ? pStats->name : actor.name;
    state.maxHp = pStats != nullptr ? pStats->hitPoints : std::max(0, static_cast<int>(actor.hp));
    state.currentHp = actor.hp > 0 ? actor.hp : state.maxHp;
    state.x = -actor.x;
    state.y = actor.y;
    state.z = actor.z;
    state.preciseX = static_cast<float>(-actor.x);
    state.preciseY = static_cast<float>(actor.y);
    state.preciseZ = static_cast<float>(actor.z);
    state.homeX = -actor.x;
    state.homeY = actor.y;
    state.homeZ = actor.z;
    state.homePreciseX = static_cast<float>(-actor.x);
    state.homePreciseY = static_cast<float>(actor.y);
    state.homePreciseZ = static_cast<float>(actor.z);
    state.radius = actor.radius;
    state.height = actor.height;
    state.moveSpeed = pMonsterEntry != nullptr ? pMonsterEntry->movementSpeed : 0;
    state.hostileToParty =
        (actor.attributes & ActorAggressorBit) != 0 || monsterTable.isHostileToParty(state.monsterId);
    state.hostilityType = actor.hostilityType;

    if (state.hostilityType == 0 && state.hostileToParty && pStats != nullptr)
    {
        state.hostilityType = static_cast<uint8_t>(pStats->hostility);
    }

    state.isInvisible = (actor.attributes & ActorInvisibleBit) != 0;
    state.animation = actor.hp <= 0 ? OutdoorWorldRuntime::ActorAnimation::Dead
        : static_cast<OutdoorWorldRuntime::ActorAnimation>(std::clamp<int>(actor.currentActionAnimation, 0, 7));
    state.aiState = actor.hp <= 0 ? OutdoorWorldRuntime::ActorAiState::Dead : OutdoorWorldRuntime::ActorAiState::Standing;
    state.recoverySeconds = monsterRecoverySeconds(pStats != nullptr ? pStats->recovery : 100);
    state.attackAnimationSeconds = std::max(0.1f, attackAnimationSeconds);
    state.attackCooldownSeconds = state.recoverySeconds;
    state.idleDecisionSeconds = 0.5f + static_cast<float>(actorId % 5) * 0.2f;

    state.preciseZ = resolveInitialActorGroundZ(
        pOutdoorMapData,
        pStats,
        state.radius,
        state.preciseX,
        state.preciseY,
        state.preciseZ);
    state.z = static_cast<int>(std::lround(state.preciseZ));
    state.homePreciseZ = state.preciseZ;
    state.homeZ = state.z;

    return state;
}

float attackAnimationSecondsForBillboard(
    const ActorPreviewBillboardSet &billboardSet,
    const ActorPreviewBillboard &billboard)
{
    uint16_t attackFrameIndex =
        billboard.actionSpriteFrameIndices[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::AttackMelee)];

    if (attackFrameIndex == 0)
    {
        attackFrameIndex =
            billboard.actionSpriteFrameIndices[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::AttackRanged)];
    }

    if (attackFrameIndex == 0)
    {
        return 0.3f;
    }

    const SpriteFrameEntry *pAttackFrame = billboardSet.spriteFrameTable.getFrame(attackFrameIndex, 0);

    if (pAttackFrame == nullptr || pAttackFrame->animationLengthTicks <= 0)
    {
        return 0.3f;
    }

    return static_cast<float>(pAttackFrame->animationLengthTicks) / TicksPerSecond;
}

float animationSecondsForSpriteFrame(
    const SpriteFrameTable *pSpriteFrameTable,
    uint16_t spriteFrameIndex,
    float fallbackSeconds)
{
    if (pSpriteFrameTable == nullptr || spriteFrameIndex == 0)
    {
        return fallbackSeconds;
    }

    const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteFrameIndex, 0);

    if (pFrame == nullptr || pFrame->animationLengthTicks <= 0)
    {
        return fallbackSeconds;
    }

    return std::max(0.05f, static_cast<float>(pFrame->animationLengthTicks) / TicksPerSecond);
}

float actorAnimationSeconds(
    const SpriteFrameTable *pSpriteFrameTable,
    const OutdoorWorldRuntime::MapActorState &actor,
    OutdoorWorldRuntime::ActorAnimation animation,
    float fallbackSeconds)
{
    const size_t animationIndex = static_cast<size_t>(animation);

    if (animationIndex >= actor.actionSpriteFrameIndices.size())
    {
        return fallbackSeconds;
    }

    return animationSecondsForSpriteFrame(
        pSpriteFrameTable,
        actor.actionSpriteFrameIndices[animationIndex],
        fallbackSeconds);
}

bool isActorUnavailableForCombat(const OutdoorWorldRuntime::MapActorState &actor)
{
    return actor.isInvisible
        || actor.isDead
        || actor.currentHp <= 0
        || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dying
        || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead;
}

bool canEnterHitReaction(const OutdoorWorldRuntime::MapActorState &actor)
{
    return !isActorUnavailableForCombat(actor)
        && actor.aiState != OutdoorWorldRuntime::ActorAiState::Stunned
        && actor.aiState != OutdoorWorldRuntime::ActorAiState::Attacking;
}

void beginHitReaction(
    OutdoorWorldRuntime::MapActorState &actor,
    const SpriteFrameTable *pSpriteFrameTable)
{
    actor.aiState = OutdoorWorldRuntime::ActorAiState::Stunned;
    actor.animation = OutdoorWorldRuntime::ActorAnimation::GotHit;
    actor.animationTimeTicks = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.actionSeconds = actorAnimationSeconds(
        pSpriteFrameTable,
        actor,
        OutdoorWorldRuntime::ActorAnimation::GotHit,
        0.25f);
    actor.idleDecisionSeconds = std::max(actor.idleDecisionSeconds, actor.actionSeconds);
    actor.attackImpactTriggered = false;
}

void beginDyingState(
    OutdoorWorldRuntime::MapActorState &actor,
    const SpriteFrameTable *pSpriteFrameTable)
{
    actor.currentHp = 0;
    actor.aiState = OutdoorWorldRuntime::ActorAiState::Dying;
    actor.animation = OutdoorWorldRuntime::ActorAnimation::Dying;
    actor.animationTimeTicks = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.actionSeconds = actorAnimationSeconds(
        pSpriteFrameTable,
        actor,
        OutdoorWorldRuntime::ActorAnimation::Dying,
        0.35f);
    actor.idleDecisionSeconds = 0.0f;
    actor.attackImpactTriggered = false;
}

std::array<uint16_t, 8> buildMonsterActionSpriteFrameIndices(
    const SpriteFrameTable &spriteFrameTable,
    const MonsterEntry *pMonsterEntry)
{
    std::array<uint16_t, 8> spriteFrameIndices = {};

    if (pMonsterEntry == nullptr)
    {
        return spriteFrameIndices;
    }

    for (size_t actionIndex = 0; actionIndex < spriteFrameIndices.size(); ++actionIndex)
    {
        const std::string &spriteName = pMonsterEntry->spriteNames[actionIndex];

        if (spriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            spriteFrameIndices[actionIndex] = *frameIndex;
        }
    }

    return spriteFrameIndices;
}

OutdoorWorldRuntime::MonsterVisualState buildMonsterVisualState(
    const SpriteFrameTable &spriteFrameTable,
    const MonsterEntry *pMonsterEntry)
{
    OutdoorWorldRuntime::MonsterVisualState state = {};

    if (pMonsterEntry == nullptr)
    {
        return state;
    }

    for (const std::string &spriteName : pMonsterEntry->spriteNames)
    {
        if (spriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            state.spriteFrameIndex = *frameIndex;
            break;
        }
    }

    state.actionSpriteFrameIndices = buildMonsterActionSpriteFrameIndices(spriteFrameTable, pMonsterEntry);
    return state;
}

void applyMonsterVisualState(
    OutdoorWorldRuntime::MapActorState &actor,
    const OutdoorWorldRuntime::MonsterVisualState &visualState)
{
    actor.spriteFrameIndex = visualState.spriteFrameIndex;
    actor.actionSpriteFrameIndices = visualState.actionSpriteFrameIndices;
    actor.useStaticSpriteFrame = visualState.useStaticFrame;
}

bool monsterIdsAreFriendly(const MonsterTable &monsterTable, int16_t leftMonsterId, int16_t rightMonsterId)
{
    return monsterTable.getRelationBetweenMonsters(leftMonsterId, rightMonsterId) <= 0;
}

uint16_t resolveRuntimeSpriteFrameIndex(
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

bool monsterIdsAreHostile(const MonsterTable &monsterTable, int16_t leftMonsterId, int16_t rightMonsterId)
{
    return monsterTable.getRelationBetweenMonsters(leftMonsterId, rightMonsterId) > 0;
}

struct EncounterSpawnDescriptor
{
    int encounterSlot = 0;
    char fixedTier = '\0';
};

std::string encounterPictureBase(const MapEncounterInfo &encounter);

EncounterSpawnDescriptor resolveEncounterSpawnDescriptor(uint16_t index)
{
    EncounterSpawnDescriptor descriptor = {};

    if (index >= 1 && index <= 3)
    {
        descriptor.encounterSlot = index;
        return descriptor;
    }

    if (index >= 4 && index <= 12)
    {
        descriptor.encounterSlot = static_cast<int>((index - 4) % 3) + 1;
        descriptor.fixedTier = static_cast<char>('A' + (index - 4) / 3);
    }

    return descriptor;
}

const MonsterTable::MonsterStatsEntry *resolveEncounterMonsterStats(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    int encounterSlot,
    char tierLetter
)
{
    const MapEncounterInfo *pEncounter = getEncounterInfo(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return nullptr;
    }

    std::string pictureName = encounterPictureBase(*pEncounter);

    if (pictureName.empty())
    {
        return nullptr;
    }

    pictureName += " ";
    pictureName.push_back(tierLetter);
    return monsterTable.findStatsByPictureName(pictureName);
}

char resolveEncounterTierLetter(
    const MapStatsEntry &map,
    int encounterSlot,
    char fixedTier,
    uint32_t seed)
{
    if (fixedTier != '\0')
    {
        return fixedTier;
    }

    const MapEncounterInfo *pEncounter = getEncounterInfo(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return 'A';
    }

    const int difficulty = std::clamp(pEncounter->difficulty, 0, 3);
    const std::array<int, 3> &weights = EncounterDifficultyTierWeights[difficulty];
    const int aWeight = weights[0];
    const int bWeight = weights[1];
    const int totalWeight = std::max(1, aWeight + bWeight + weights[2]);
    std::mt19937 rng(seed);
    const int roll = std::uniform_int_distribution<int>(0, totalWeight - 1)(rng);

    if (roll < aWeight)
    {
        return 'A';
    }

    if (roll < aWeight + bWeight)
    {
        return 'B';
    }

    return 'C';
}

uint32_t resolveEncounterSpawnCount(
    const MapStatsEntry &map,
    int encounterSlot,
    uint32_t countOverride,
    uint32_t sessionSeed,
    uint32_t salt
)
{
    if (countOverride > 0)
    {
        return countOverride;
    }

    const MapEncounterInfo *pEncounter = getEncounterInfo(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return 0;
    }

    const int minCount = std::max(0, std::min(pEncounter->minCount, pEncounter->maxCount));
    const int maxCount = std::max(0, std::max(pEncounter->minCount, pEncounter->maxCount));

    if (maxCount <= 0)
    {
        return 0;
    }

    if (minCount == maxCount)
    {
        return static_cast<uint32_t>(maxCount);
    }

    std::mt19937 rng(sessionSeed ^ salt ^ static_cast<uint32_t>(encounterSlot * 2654435761u));
    return static_cast<uint32_t>(std::uniform_int_distribution<int>(minCount, maxCount)(rng));
}

bx::Vec3 calculateEncounterSpawnPosition(
    float centerX,
    float centerY,
    float centerZ,
    uint16_t spawnRadius,
    uint16_t actorRadius,
    uint32_t spawnOrdinal
)
{
    if (spawnOrdinal == 0)
    {
        return {centerX, centerY, centerZ};
    }

    const uint32_t ringOrdinal = spawnOrdinal - 1;
    const uint32_t ringIndex = ringOrdinal / 8;
    const uint32_t slotIndex = ringOrdinal % 8;
    const float baseRadius = std::max(
        static_cast<float>(std::max<uint16_t>(spawnRadius, static_cast<uint16_t>(96))),
        static_cast<float>(actorRadius) * 2.0f + 16.0f);
    const float radius = baseRadius + static_cast<float>(ringIndex) * (baseRadius * 0.75f);
    const float angle = (2.0f * Pi * static_cast<float>(slotIndex)) / 8.0f;
    return {
        centerX + std::cos(angle) * radius,
        centerY + std::sin(angle) * radius,
        centerZ
    };
}

OutdoorWorldRuntime::MapActorState buildSpawnedMapActorState(
    const MonsterTable &monsterTable,
    const OutdoorMapData *pOutdoorMapData,
    const MonsterTable::MonsterStatsEntry &stats,
    uint32_t actorId,
    uint32_t uniqueNameId,
    bool fromSpawnPoint,
    size_t spawnPointIndex,
    uint32_t group,
    uint16_t attributes,
    float x,
    float y,
    float z
)
{
    OutdoorWorldRuntime::MapActorState state = {};
    state.actorId = actorId;
    state.monsterId = static_cast<int16_t>(stats.id);
    state.displayName = stats.name;
    state.uniqueNameId = uniqueNameId;
    state.spawnedAtRuntime = true;
    state.fromSpawnPoint = fromSpawnPoint;
    state.spawnPointIndex = spawnPointIndex;
    state.group = group;
    state.hostilityType = static_cast<uint8_t>(stats.hostility);
    state.maxHp = stats.hitPoints;
    state.currentHp = stats.hitPoints;
    state.x = static_cast<int>(std::lround(x));
    state.y = static_cast<int>(std::lround(y));
    state.z = static_cast<int>(std::lround(z));
    state.preciseX = x;
    state.preciseY = y;
    state.preciseZ = z;
    state.homeX = state.x;
    state.homeY = state.y;
    state.homeZ = state.z;
    state.homePreciseX = state.preciseX;
    state.homePreciseY = state.preciseY;
    state.homePreciseZ = state.preciseZ;

    const MonsterEntry *pMonsterEntry = resolveMonsterEntry(monsterTable, state.monsterId, &stats);
    state.radius = pMonsterEntry != nullptr ? pMonsterEntry->radius : 32;
    state.height = pMonsterEntry != nullptr ? pMonsterEntry->height : 128;
    state.moveSpeed = pMonsterEntry != nullptr ? pMonsterEntry->movementSpeed : 0;
    state.hostileToParty =
        (attributes & ActorAggressorBit) != 0 || monsterTable.isHostileToParty(state.monsterId);
    state.isInvisible = (attributes & ActorInvisibleBit) != 0;
    state.animation = OutdoorWorldRuntime::ActorAnimation::Standing;
    state.aiState = OutdoorWorldRuntime::ActorAiState::Standing;
    state.recoverySeconds = monsterRecoverySeconds(stats.recovery);
    state.attackAnimationSeconds = 0.3f;
    state.attackCooldownSeconds = state.recoverySeconds;
    state.idleDecisionSeconds = 0.5f + static_cast<float>(actorId % 5) * 0.2f;

    state.preciseZ = resolveInitialActorGroundZ(
        pOutdoorMapData,
        &stats,
        state.radius,
        state.preciseX,
        state.preciseY,
        state.preciseZ);
    state.z = static_cast<int>(std::lround(state.preciseZ));
    state.homePreciseZ = state.preciseZ;
    state.homeZ = state.z;
    return state;
}

enum class CombatTargetKind
{
    None,
    Party,
    Actor,
};

struct CombatTargetInfo
{
    CombatTargetKind kind = CombatTargetKind::None;
    size_t actorIndex = static_cast<size_t>(-1);
    int relationToTarget = 0;
    float targetX = 0.0f;
    float targetY = 0.0f;
    float targetZ = 0.0f;
    float deltaX = 0.0f;
    float deltaY = 0.0f;
    float deltaZ = 0.0f;
    float horizontalDistanceToTarget = 0.0f;
    float distanceToTarget = 0.0f;
    float edgeDistance = 0.0f;
    bool canSense = false;
};

float targetDistanceSquared(const CombatTargetInfo &target)
{
    return lengthSquared3d(target.deltaX, target.deltaY, target.deltaZ);
}

const char *combatTargetKindName(CombatTargetKind targetKind)
{
    switch (targetKind)
    {
        case CombatTargetKind::Party:
            return "party";
        case CombatTargetKind::Actor:
            return "actor";
        default:
            return "none";
    }
}

template <typename VisibilityFn>
CombatTargetInfo selectCombatTarget(
    const OutdoorWorldRuntime::MapActorState &actor,
    size_t actorIndex,
    const std::vector<OutdoorWorldRuntime::MapActorState> &mapActors,
    const MonsterTable &monsterTable,
    float partyX,
    float partyY,
    float partyZ,
    VisibilityFn &&hasClearOutdoorLineOfSight)
{
    CombatTargetInfo target = {};
    float bestPriorityDistanceSquared = std::numeric_limits<float>::max();
    const float actorTargetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    const int relationToParty = monsterTable.getRelationToParty(actor.monsterId);
    float partyEngagementRange = actor.hostileToParty
        ? HostilityLongRange
        : hostilityRangeForRelation(relationToParty);

    if (partyEngagementRange > 0.0f)
    {
        const float deltaPartyX = partyX - actor.preciseX;
        const float deltaPartyY = partyY - actor.preciseY;
        const float partyTargetZ = partyZ + PartyTargetHeightOffset;
        const float deltaPartyZ = partyTargetZ - actorTargetZ;
        const bool canSenseParty =
            std::abs(deltaPartyX) <= partyEngagementRange
            && std::abs(deltaPartyY) <= partyEngagementRange
            && std::abs(deltaPartyZ) <= partyEngagementRange
            && isWithinRange3d(deltaPartyX, deltaPartyY, deltaPartyZ, partyEngagementRange);

        if (canSenseParty)
        {
            const float horizontalDistanceToParty = length2d(deltaPartyX, deltaPartyY);
            const float distanceToParty = length3d(deltaPartyX, deltaPartyY, deltaPartyZ);
            const float edgeDistanceToParty = std::max(
                0.0f,
                distanceToParty - static_cast<float>(actor.radius) - PartyCollisionRadius);
            target.kind = CombatTargetKind::Party;
            target.targetX = partyX;
            target.targetY = partyY;
            target.targetZ = partyTargetZ;
            target.deltaX = deltaPartyX;
            target.deltaY = deltaPartyY;
            target.deltaZ = deltaPartyZ;
            target.horizontalDistanceToTarget = horizontalDistanceToParty;
            target.distanceToTarget = distanceToParty;
            target.edgeDistance = edgeDistanceToParty;
            target.canSense = true;
            bestPriorityDistanceSquared = distanceToParty * distanceToParty;
        }
    }

    for (size_t otherActorIndex = 0; otherActorIndex < mapActors.size(); ++otherActorIndex)
    {
        if (otherActorIndex == actorIndex)
        {
            continue;
        }

        const OutdoorWorldRuntime::MapActorState &otherActor = mapActors[otherActorIndex];

        if (isActorUnavailableForCombat(otherActor))
        {
            continue;
        }

        if (!monsterIdsAreHostile(monsterTable, actor.monsterId, otherActor.monsterId))
        {
            continue;
        }

        const float deltaX = otherActor.preciseX - actor.preciseX;
        const float deltaY = otherActor.preciseY - actor.preciseY;
        const float otherActorTargetZ =
            otherActor.preciseZ + std::max(24.0f, static_cast<float>(otherActor.height) * 0.7f);
        const float deltaZ = otherActorTargetZ - actorTargetZ;
        const float distanceSquaredToOtherActor = lengthSquared3d(deltaX, deltaY, deltaZ);
        const int relationToOtherActor = monsterTable.getRelationBetweenMonsters(actor.monsterId, otherActor.monsterId);
        const float engagementRange = hostilityRangeForRelation(relationToOtherActor);

        if (!isWithinRange3d(deltaX, deltaY, deltaZ, engagementRange))
        {
            continue;
        }

        if (!hasClearOutdoorLineOfSight(
                bx::Vec3{actor.preciseX, actor.preciseY, actorTargetZ},
                bx::Vec3{otherActor.preciseX, otherActor.preciseY, otherActorTargetZ}))
        {
            continue;
        }

        if (distanceSquaredToOtherActor >= bestPriorityDistanceSquared)
        {
            continue;
        }

        const float horizontalDistanceToOtherActor = length2d(deltaX, deltaY);
        const float distanceToOtherActor = length3d(deltaX, deltaY, deltaZ);
        const float edgeDistance = std::max(
            0.0f,
            distanceToOtherActor - static_cast<float>(actor.radius) - static_cast<float>(otherActor.radius));
        target.kind = CombatTargetKind::Actor;
        target.actorIndex = otherActorIndex;
        target.relationToTarget = relationToOtherActor;
        target.targetX = otherActor.preciseX;
        target.targetY = otherActor.preciseY;
        target.targetZ = otherActorTargetZ;
        target.deltaX = deltaX;
        target.deltaY = deltaY;
        target.deltaZ = deltaZ;
        target.horizontalDistanceToTarget = horizontalDistanceToOtherActor;
        target.distanceToTarget = distanceToOtherActor;
        target.edgeDistance = edgeDistance;
        target.canSense = true;
        bestPriorityDistanceSquared = distanceSquaredToOtherActor;
    }

    return target;
}

void beginStandAwhile(OutdoorWorldRuntime::MapActorState &actor, bool bored)
{
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.attackImpactTriggered = false;
    actor.actionSeconds = bored ? 2.0f : 1.5f;
    actor.idleDecisionSeconds = actor.actionSeconds;
    actor.animation = bored
        ? OutdoorWorldRuntime::ActorAnimation::Bored
        : OutdoorWorldRuntime::ActorAnimation::Standing;
    actor.animationTimeTicks = 0.0f;
}

bool beginIdleWander(
    OutdoorWorldRuntime::MapActorState &actor,
    uint32_t decisionSeed,
    float wanderRadius,
    float moveSpeed
)
{
    const float deltaHomeX = actor.homePreciseX - actor.preciseX;
    const float deltaHomeY = actor.homePreciseY - actor.preciseY;
    float homeAngle = std::atan2(deltaHomeY, deltaHomeX);

    if (std::abs(deltaHomeX) <= 0.01f && std::abs(deltaHomeY) <= 0.01f)
    {
        homeAngle = actor.yawRadians;
    }

    const float randomAngleOffset =
        ((static_cast<int>(decisionSeed % 257u) - 128) / 256.0f) * (Pi / 4.0f);
    const float proposedYaw = normalizeAngleRadians(homeAngle + randomAngleOffset);

    if (shortestAngleDistanceRadians(proposedYaw, actor.yawRadians) > (Pi / 4.0f)
        && actor.animation != OutdoorWorldRuntime::ActorAnimation::Walking)
    {
        actor.yawRadians = proposedYaw;
        beginStandAwhile(actor, false);
        return false;
    }

    actor.yawRadians = proposedYaw;
    actor.moveDirectionX = std::cos(actor.yawRadians);
    actor.moveDirectionY = std::sin(actor.yawRadians);
    actor.attackImpactTriggered = false;
    const float weightedDistance = std::max(std::abs(deltaHomeX), std::abs(deltaHomeY))
        + 0.5f * std::min(std::abs(deltaHomeX), std::abs(deltaHomeY))
        + static_cast<float>(decisionSeed % 16u) * (wanderRadius / 16.0f);
    actor.actionSeconds = moveSpeed > 0.0f ? std::max(0.25f, weightedDistance / (4.0f * moveSpeed)) : 0.0f;
    actor.idleDecisionSeconds = 0.0f;
    actor.animationTimeTicks = 0.0f;
    return actor.actionSeconds > 0.0f;
}

char tierLetterForSummonLevel(uint32_t level)
{
    const uint32_t clampedLevel = std::clamp(level, 1u, 3u);
    return static_cast<char>('A' + (clampedLevel - 1u));
}

std::string encounterPictureBase(const MapEncounterInfo &encounter)
{
    return encounter.pictureName.empty() ? encounter.monsterName : encounter.pictureName;
}

bool itemMatchesLootKind(const ItemDefinition &item, MonsterTable::LootItemKind kind)
{
    switch (kind)
    {
        case MonsterTable::LootItemKind::None:
            return false;

        case MonsterTable::LootItemKind::Any:
            return true;

        case MonsterTable::LootItemKind::Gem:
            return item.equipStat == "Gem";

        case MonsterTable::LootItemKind::Ring:
            return item.equipStat == "Ring";

        case MonsterTable::LootItemKind::Amulet:
            return item.equipStat == "Amulet";

        case MonsterTable::LootItemKind::Boots:
            return item.equipStat == "Boots";

        case MonsterTable::LootItemKind::Gauntlets:
            return item.equipStat == "Gauntlets";

        case MonsterTable::LootItemKind::Cloak:
            return item.equipStat == "Cloak";

        case MonsterTable::LootItemKind::Wand:
            return item.name.find("Wand") != std::string::npos;

        case MonsterTable::LootItemKind::Ore:
            return item.equipStat == "Ore";

        case MonsterTable::LootItemKind::Scroll:
            return item.equipStat == "Sscroll";

        case MonsterTable::LootItemKind::Sword:
            return item.skillGroup == "Sword";

        case MonsterTable::LootItemKind::Dagger:
            return item.skillGroup == "Dagger";

        case MonsterTable::LootItemKind::Spear:
            return item.skillGroup == "Spear";

        case MonsterTable::LootItemKind::Chain:
            return item.skillGroup == "Chain";

        case MonsterTable::LootItemKind::Plate:
            return item.skillGroup == "Plate";

        case MonsterTable::LootItemKind::Club:
            return item.skillGroup == "Club";

        case MonsterTable::LootItemKind::Staff:
            return item.skillGroup == "Staff";

        case MonsterTable::LootItemKind::Bow:
            return item.skillGroup == "Bow";
    }

    return false;
}

OutdoorWorldRuntime::SpawnPointState buildSpawnPointState(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const OutdoorSpawn &spawn
)
{
    OutdoorWorldRuntime::SpawnPointState state = {};
    state.x = spawn.x;
    state.y = spawn.y;
    state.z = spawn.z;
    state.radius = spawn.radius;
    state.typeId = spawn.typeId;
    state.index = spawn.index;
    state.attributes = spawn.attributes;
    state.group = spawn.group;

    if (spawn.typeId != 3)
    {
        return state;
    }

    const EncounterSpawnDescriptor descriptor = resolveEncounterSpawnDescriptor(spawn.index);
    state.encounterSlot = descriptor.encounterSlot;
    state.isFixedTier = descriptor.fixedTier != '\0';
    state.fixedTier = descriptor.fixedTier;

    const MapEncounterInfo *pEncounter = getEncounterInfo(map, descriptor.encounterSlot);

    if (pEncounter == nullptr)
    {
        return state;
    }

    state.minCount = pEncounter->minCount;
    state.maxCount = pEncounter->maxCount;
    state.monsterFamilyName = pEncounter->monsterName;

    const MonsterTable::MonsterStatsEntry *pStats =
        resolveEncounterMonsterStats(
            map,
            monsterTable,
            descriptor.encounterSlot,
            descriptor.fixedTier != '\0' ? descriptor.fixedTier : 'A');

    if (pStats == nullptr)
    {
        return state;
    }

    state.representativePictureName = pStats->pictureName;
    state.representativeMonsterId = static_cast<int16_t>(pStats->id);
    state.hostilityType = static_cast<uint8_t>(pStats->hostility);
    state.hostileToParty = monsterTable.isHostileToParty(state.representativeMonsterId);
    return state;
}

float wanderRadiusForMovementType(MonsterTable::MonsterMovementType movementType)
{
    switch (movementType)
    {
        case MonsterTable::MonsterMovementType::Short:
            return 1024.0f;

        case MonsterTable::MonsterMovementType::Medium:
            return 2560.0f;

        case MonsterTable::MonsterMovementType::Long:
            return 5120.0f;

        case MonsterTable::MonsterMovementType::Global:
        case MonsterTable::MonsterMovementType::Free:
            return 10240.0f;

        case MonsterTable::MonsterMovementType::Stationary:
            return 0.0f;
    }

    return 0.0f;
}

bool shouldFleeForAiType(const MonsterTable::MonsterStatsEntry &stats, const OutdoorWorldRuntime::MapActorState &actor)
{
    if (stats.aiType == MonsterTable::MonsterAiType::Wimp)
    {
        return true;
    }

    if (actor.maxHp <= 0)
    {
        return false;
    }

    if (stats.aiType == MonsterTable::MonsterAiType::Normal)
    {
        return static_cast<float>(actor.currentHp) < static_cast<float>(actor.maxHp) * 0.2f;
    }

    if (stats.aiType == MonsterTable::MonsterAiType::Aggressive)
    {
        return static_cast<float>(actor.currentHp) < static_cast<float>(actor.maxHp) * 0.1f;
    }

    return false;
}

bool isRangedAttackAbility(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    switch (ability)
    {
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack1:
            return stats.attack1HasMissile;

        case OutdoorWorldRuntime::MonsterAttackAbility::Attack2:
            return stats.attack2HasMissile;

        case OutdoorWorldRuntime::MonsterAttackAbility::Spell1:
        case OutdoorWorldRuntime::MonsterAttackAbility::Spell2:
            return true;
    }

    return false;
}

OutdoorWorldRuntime::ActorAnimation attackAnimationForAbility(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    return isRangedAttackAbility(stats, ability)
        ? OutdoorWorldRuntime::ActorAnimation::AttackRanged
        : OutdoorWorldRuntime::ActorAnimation::AttackMelee;
}

float attackActionDurationSeconds(float attackAnimationSeconds)
{
    return std::max(0.1f, attackAnimationSeconds);
}

float attackCooldownDurationSeconds(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability,
    float attackAnimationSeconds,
    float recoverySeconds)
{
    if (isRangedAttackAbility(stats, ability))
    {
        return recoverySeconds + std::max(0.1f, attackAnimationSeconds);
    }

    return recoverySeconds;
}

enum class PursueActionMode
{
    OffsetShort,
    Direct,
    OffsetWide,
};

OutdoorWorldRuntime::MonsterAttackAbility chooseAttackAbility(
    OutdoorWorldRuntime::MapActorState &actor,
    const MonsterTable::MonsterStatsEntry &stats)
{
    const uint32_t baseSeed =
        static_cast<uint32_t>(actor.actorId + 1) * 1103515245u
        + actor.attackDecisionCount * 2654435761u
        + 0x7f4a7c15u;
    ++actor.attackDecisionCount;

    auto passesChance =
        [&](int chance, uint32_t salt)
        {
            if (chance <= 0)
            {
                return false;
            }

            return ((baseSeed ^ salt) % 100u) < static_cast<uint32_t>(chance);
        };

    if (stats.hasSpell1 && passesChance(stats.spell1UseChance, 0x13579bdfu))
    {
        return OutdoorWorldRuntime::MonsterAttackAbility::Spell1;
    }

    if (stats.hasSpell2 && passesChance(stats.spell2UseChance, 0x2468ace0u))
    {
        return OutdoorWorldRuntime::MonsterAttackAbility::Spell2;
    }

    if (passesChance(stats.attack2Chance, 0x55aa55aau))
    {
        return OutdoorWorldRuntime::MonsterAttackAbility::Attack2;
    }

    return OutdoorWorldRuntime::MonsterAttackAbility::Attack1;
}

bool beginPursueAction(
    OutdoorWorldRuntime::MapActorState &actor,
    float deltaTargetX,
    float deltaTargetY,
    float distanceToTarget,
    float moveSpeed,
    PursueActionMode mode,
    uint32_t decisionSeed
)
{
    if (distanceToTarget <= 0.01f || moveSpeed <= 0.0f)
    {
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
        actor.actionSeconds = 0.0f;
        return false;
    }

    float yaw = std::atan2(deltaTargetY, deltaTargetX);
    float durationSeconds = distanceToTarget / moveSpeed;

    if (mode == PursueActionMode::OffsetShort)
    {
        const float offset = (decisionSeed & 1u) == 0u ? (Pi / 64.0f) : (-Pi / 64.0f);
        yaw = normalizeAngleRadians(yaw + offset);
        durationSeconds = 0.5f;
    }
    else if (mode == PursueActionMode::Direct)
    {
        durationSeconds = std::min(durationSeconds, 32.0f / TicksPerSecond);
    }
    else
    {
        const float offset = (decisionSeed & 1u) == 0u ? (Pi / 4.0f) : (-Pi / 4.0f);
        yaw = normalizeAngleRadians(yaw + offset);
        durationSeconds = std::min(durationSeconds, 128.0f / TicksPerSecond);
    }

    actor.yawRadians = yaw;
    actor.moveDirectionX = std::cos(yaw);
    actor.moveDirectionY = std::sin(yaw);
    actor.attackImpactTriggered = false;
    actor.actionSeconds = std::max(0.05f, durationSeconds);
    return true;
}

bool isMeleeAttackAbility(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    return !isRangedAttackAbility(stats, ability);
}

bool shouldMaterializeEncounterSpawnsOnInitialize(const std::optional<MapDeltaData> &outdoorMapDeltaData)
{
    return outdoorMapDeltaData.has_value() && outdoorMapDeltaData->locationInfo.lastRespawnDay == 0;
}
}

uint32_t OutdoorWorldRuntime::makeChestSeed(uint32_t sessionSeed, int mapId, uint32_t chestId, uint32_t salt)
{
    return sessionSeed
        ^ static_cast<uint32_t>(mapId) * 1315423911u
        ^ (chestId + 1u) * 2654435761u
        ^ (salt + 1u) * 2246822519u;
}

void OutdoorWorldRuntime::appendChestItem(std::vector<ChestItemState> &items, const ChestItemState &item)
{
    if (item.isGold)
    {
        for (ChestItemState &existing : items)
        {
            if (existing.isGold)
            {
                existing.goldAmount += item.goldAmount;
                existing.goldRollCount += item.goldRollCount;
                return;
            }
        }

        items.push_back(item);
        return;
    }

    for (ChestItemState &existing : items)
    {
        if (!existing.isGold && existing.itemId == item.itemId)
        {
            existing.quantity += item.quantity;
            return;
        }
    }

    items.push_back(item);
}

int OutdoorWorldRuntime::generateGoldAmount(int treasureLevel, std::mt19937 &rng)
{
    switch (treasureLevel)
    {
        case 1: return std::uniform_int_distribution<int>(50, 100)(rng);
        case 2: return std::uniform_int_distribution<int>(100, 200)(rng);
        case 3: return std::uniform_int_distribution<int>(200, 500)(rng);
        case 4: return std::uniform_int_distribution<int>(500, 1000)(rng);
        case 5: return std::uniform_int_distribution<int>(1000, 2000)(rng);
        case 6: return std::uniform_int_distribution<int>(2000, 5000)(rng);
        default: return 0;
    }
}

int OutdoorWorldRuntime::remapTreasureLevel(int itemTreasureLevel, int mapTreasureLevel)
{
    static constexpr int mapping[7][7][2] = {
        {{1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}},
        {{1, 1}, {1, 2}, {2, 2}, {2, 2}, {2, 2}, {2, 2}, {2, 2}},
        {{1, 2}, {2, 2}, {2, 3}, {3, 3}, {3, 3}, {3, 3}, {3, 3}},
        {{2, 2}, {2, 2}, {3, 3}, {3, 4}, {4, 4}, {4, 4}, {4, 4}},
        {{2, 2}, {2, 2}, {3, 4}, {4, 4}, {4, 5}, {5, 5}, {5, 5}},
        {{2, 2}, {2, 2}, {4, 4}, {4, 5}, {5, 5}, {5, 6}, {6, 6}},
        {{2, 2}, {2, 2}, {7, 7}, {7, 7}, {7, 7}, {7, 7}, {7, 7}}
    };

    const int clampedItemLevel = std::clamp(itemTreasureLevel, RandomChestItemMinLevel, RandomChestItemMaxLevel);
    const int clampedMapLevel = std::clamp(mapTreasureLevel, RandomChestItemMinLevel, RandomChestItemMaxLevel);
    const int minLevel = mapping[clampedItemLevel - 1][clampedMapLevel - 1][0];
    const int maxLevel = mapping[clampedItemLevel - 1][clampedMapLevel - 1][1];

    return (minLevel + maxLevel) / 2;
}

uint32_t OutdoorWorldRuntime::generateRandomItemId(int treasureLevel, std::mt19937 &rng) const
{
    if (m_pItemTable == nullptr)
    {
        return 0;
    }

    const int weightIndex = std::clamp(treasureLevel, 1, SpawnableItemTreasureLevels) - 1;
    int totalWeight = 0;

    for (const ItemDefinition &entry : m_pItemTable->entries())
    {
        if (entry.itemId == 0 || entry.randomTreasureWeights[weightIndex] <= 0)
        {
            continue;
        }

        totalWeight += entry.randomTreasureWeights[weightIndex];
    }

    if (totalWeight <= 0)
    {
        return 0;
    }

    const int pick = std::uniform_int_distribution<int>(1, totalWeight)(rng);
    int runningWeight = 0;

    for (const ItemDefinition &entry : m_pItemTable->entries())
    {
        if (entry.itemId == 0 || entry.randomTreasureWeights[weightIndex] <= 0)
        {
            continue;
        }

        runningWeight += entry.randomTreasureWeights[weightIndex];

        if (runningWeight >= pick)
        {
            return entry.itemId;
        }
    }

    return 0;
}

uint32_t OutdoorWorldRuntime::generateRandomLootItemId(
    int treasureLevel,
    MonsterTable::LootItemKind itemKind,
    std::mt19937 &rng
) const
{
    if (m_pItemTable == nullptr)
    {
        return 0;
    }

    const int weightIndex = std::clamp(treasureLevel, 1, SpawnableItemTreasureLevels) - 1;
    int totalWeight = 0;

    for (const ItemDefinition &entry : m_pItemTable->entries())
    {
        if (entry.itemId == 0 || entry.randomTreasureWeights[weightIndex] <= 0)
        {
            continue;
        }

        if (!itemMatchesLootKind(entry, itemKind))
        {
            continue;
        }

        totalWeight += entry.randomTreasureWeights[weightIndex];
    }

    if (totalWeight <= 0)
    {
        return itemKind == MonsterTable::LootItemKind::Any ? generateRandomItemId(treasureLevel, rng) : 0;
    }

    int targetWeight = std::uniform_int_distribution<int>(1, totalWeight)(rng);
    int runningWeight = 0;

    for (const ItemDefinition &entry : m_pItemTable->entries())
    {
        if (entry.itemId == 0 || entry.randomTreasureWeights[weightIndex] <= 0)
        {
            continue;
        }

        if (!itemMatchesLootKind(entry, itemKind))
        {
            continue;
        }

        runningWeight += entry.randomTreasureWeights[weightIndex];

        if (runningWeight >= targetWeight)
        {
            return entry.itemId;
        }
    }

    return 0;
}

OutdoorWorldRuntime::CorpseViewState OutdoorWorldRuntime::buildCorpseView(
    const std::string &title,
    const MonsterTable::LootPrototype &loot,
    uint32_t seed
) const
{
    CorpseViewState view = {};
    view.title = title;

    std::mt19937 rng(seed);

    if (loot.goldDiceRolls > 0 && loot.goldDiceSides > 0)
    {
        ChestItemState goldItem = {};
        goldItem.isGold = true;
        goldItem.goldRollCount = static_cast<uint32_t>(loot.goldDiceRolls);

        for (int roll = 0; roll < loot.goldDiceRolls; ++roll)
        {
            goldItem.goldAmount += static_cast<uint32_t>(std::uniform_int_distribution<int>(1, loot.goldDiceSides)(rng));
        }

        if (goldItem.goldAmount > 0)
        {
            view.items.push_back(goldItem);
        }
    }

    if (loot.itemChance > 0
        && loot.itemLevel > 0
        && std::uniform_int_distribution<int>(0, 99)(rng) < loot.itemChance)
    {
        const int remappedTreasureLevel = remapTreasureLevel(loot.itemLevel, m_mapTreasureLevel);
        const uint32_t itemId = generateRandomLootItemId(remappedTreasureLevel, loot.itemKind, rng);

        if (itemId != 0)
        {
            ChestItemState item = {};
            item.itemId = itemId;
            item.quantity = 1;
            view.items.push_back(item);
        }
    }

    return view;
}

void OutdoorWorldRuntime::pushAudioEvent(uint32_t soundId, uint32_t sourceId, const std::string &reason)
{
    if (soundId == 0)
    {
        return;
    }

    AudioEvent event = {};
    event.soundId = soundId;
    event.sourceId = sourceId;
    event.reason = reason;
    m_pendingAudioEvents.push_back(std::move(event));
}

OutdoorWorldRuntime::ChestViewState OutdoorWorldRuntime::buildChestView(uint32_t chestId) const
{
    ChestViewState view = {};
    view.chestId = chestId;

    if (chestId >= m_chests.size())
    {
        return view;
    }

    const MapDeltaChest &chest = m_chests[chestId];
    view.chestTypeId = chest.chestTypeId;
    view.flags = chest.flags;

    if (DebugChestPopulateLogging)
    {
        std::cout << "Chest populate: chest=" << chestId
                  << " type=" << chest.chestTypeId
                  << " flags=0x" << std::hex << chest.flags << std::dec
                  << " raw_records=" << (chest.rawItems.size() / ChestItemRecordSize)
                  << '\n';
    }

    if (chest.rawItems.empty() || chest.inventoryMatrix.empty())
    {
        if (DebugChestPopulateLogging)
        {
            std::cout << "  empty source buffers\n";
        }
        return view;
    }

    std::vector<int32_t> rawItemIds(chest.rawItems.size() / ChestItemRecordSize, 0);

    for (size_t itemIndex = 0; itemIndex < rawItemIds.size(); ++itemIndex)
    {
        std::memcpy(
            &rawItemIds[itemIndex],
            chest.rawItems.data() + itemIndex * ChestItemRecordSize,
            sizeof(int32_t)
        );
    }

    if (DebugChestPopulateLogging)
    {
        std::ostringstream rawItemSample;
        size_t nonZeroRawItems = 0;
        size_t sampledRawItems = 0;

        for (size_t itemIndex = 0; itemIndex < rawItemIds.size(); ++itemIndex)
        {
            if (rawItemIds[itemIndex] == 0)
            {
                continue;
            }

            ++nonZeroRawItems;

            if (sampledRawItems < 12)
            {
                if (sampledRawItems > 0)
                {
                    rawItemSample << ' ';
                }

                rawItemSample << itemIndex << ':' << rawItemIds[itemIndex];
                ++sampledRawItems;
            }
        }

        std::cout << "  raw nonzero=" << nonZeroRawItems
                  << " sample=[" << rawItemSample.str() << "]"
                  << '\n';
    }

    std::mt19937 rng(makeChestSeed(m_sessionChestSeed, m_mapId, chestId, 0));
    const int mapTreasureLevel = std::clamp(m_mapTreasureLevel + 1, 1, 7);
    size_t positiveCells = 0;
    size_t negativeCells = 0;
    std::ostringstream matrixSample;
    size_t sampledCells = 0;

    for (size_t cellIndex = 0; cellIndex < chest.inventoryMatrix.size(); ++cellIndex)
    {
        const int16_t cellValue = chest.inventoryMatrix[cellIndex];

        if (cellValue > 0)
        {
            ++positiveCells;
        }
        else if (cellValue < 0)
        {
            ++negativeCells;
        }

        if (cellValue != 0 && sampledCells < 12)
        {
            if (sampledCells > 0)
            {
                matrixSample << ' ';
            }

            matrixSample << cellIndex << ':' << cellValue;
            ++sampledCells;
        }
    }

    if (DebugChestPopulateLogging)
    {
        std::cout << "  matrix positive=" << positiveCells
                  << " negative=" << negativeCells
                  << " sample=[" << matrixSample.str() << "]"
                  << '\n';
    }

    size_t materializedRecords = 0;

    for (size_t itemIndex = 0; itemIndex < rawItemIds.size(); ++itemIndex)
    {
        const int32_t itemId = rawItemIds[itemIndex];

        if (itemId == 0)
        {
            continue;
        }

        const bool hasGridReference = std::find(
            chest.inventoryMatrix.begin(),
            chest.inventoryMatrix.end(),
            static_cast<int16_t>(itemIndex + 1)
        ) != chest.inventoryMatrix.end();
        materializedRecords += 1;

        if (DebugChestPopulateLogging)
        {
            std::cout << "  record=" << itemIndex
                      << " raw_item_id=" << itemId
                      << " grid_ref=" << (hasGridReference ? "yes" : "no")
                      << '\n';
        }

        if (itemId > 0)
        {
            ChestItemState item = {};
            item.itemId = static_cast<uint32_t>(itemId);
            item.quantity = 1;
            appendChestItem(view.items, item);
            if (DebugChestPopulateLogging)
            {
                std::cout << "    serialized item=" << item.itemId;

                if (m_pItemTable != nullptr && m_pItemTable->get(item.itemId) == nullptr)
                {
                    std::cout << " unknown";
                }

                std::cout << '\n';
            }
            continue;
        }

        if (itemId > -8 && itemId < 0)
        {
            const int resolvedTreasureLevel = remapTreasureLevel(-itemId, mapTreasureLevel);
            const int generatedCount = std::uniform_int_distribution<int>(1, 5)(rng);
            if (DebugChestPopulateLogging)
            {
                std::cout << "    random placeholder level=" << (-itemId)
                          << " map_treasure=" << mapTreasureLevel
                          << " resolved=" << resolvedTreasureLevel
                          << " rolls=" << generatedCount
                          << '\n';
            }

            for (int count = 0; count < generatedCount; ++count)
            {
                const int roll = std::uniform_int_distribution<int>(0, 99)(rng);

                if (DebugChestPopulateLogging)
                {
                    std::cout << "      roll=" << roll;
                }

                if (roll < 20)
                {
                    if (DebugChestPopulateLogging)
                    {
                        std::cout << " -> empty\n";
                    }
                    continue;
                }

                if (roll < 60)
                {
                    ChestItemState gold = {};
                    gold.goldAmount = static_cast<uint32_t>(generateGoldAmount(
                        std::min(resolvedTreasureLevel, SpawnableItemTreasureLevels),
                        rng
                    ));
                    gold.goldRollCount = 1;
                    gold.isGold = gold.goldAmount > 0;

                    if (gold.isGold)
                    {
                        appendChestItem(view.items, gold);
                        if (DebugChestPopulateLogging)
                        {
                            std::cout << " -> gold " << gold.goldAmount << '\n';
                        }
                    }
                    else
                    {
                        if (DebugChestPopulateLogging)
                        {
                            std::cout << " -> gold 0 skipped\n";
                        }
                    }

                    continue;
                }

                const int generationLevel = std::min(resolvedTreasureLevel, SpawnableItemTreasureLevels);
                const uint32_t generatedItemId = generateRandomItemId(generationLevel, rng);

                if (generatedItemId == 0)
                {
                    if (DebugChestPopulateLogging)
                    {
                        std::cout << " -> item generation failed\n";
                    }
                    continue;
                }

                ChestItemState item = {};
                item.itemId = generatedItemId;
                item.quantity = 1;
                appendChestItem(view.items, item);

                if (DebugChestPopulateLogging)
                {
                    std::cout << " -> item " << generatedItemId << '\n';
                }
            }

            continue;
        }

        if (DebugChestPopulateLogging)
        {
            std::cout << "    unsupported negative item marker skipped\n";
        }
    }

    if (DebugChestPopulateLogging)
    {
        std::cout << "  materialized_records=" << materializedRecords
                  << " final_entries=" << view.items.size()
                  << '\n';
    }

    return view;
}

void OutdoorWorldRuntime::activateChestView(uint32_t chestId)
{
    if (chestId >= m_chests.size())
    {
        return;
    }

    if (chestId >= m_materializedChestViews.size())
    {
        return;
    }

    if (!m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = buildChestView(chestId);
    }

    m_activeChestView = *m_materializedChestViews[chestId];
}

void OutdoorWorldRuntime::initialize(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const MonsterProjectileTable &monsterProjectileTable,
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    const ItemTable &itemTable,
    const std::optional<OutdoorMapData> &outdoorMapData,
    const std::optional<MapDeltaData> &outdoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet,
    const std::optional<SpriteObjectBillboardSet> &outdoorSpriteObjectBillboardSet
)
{
    m_mapId = map.id;
    m_map = map;
    m_mapName = map.name;
    m_mapTreasureLevel = map.treasureLevel;
    m_gameMinutes = 9.0f * 60.0f;
    m_timers.clear();
    m_mapActors.clear();
    m_spawnPoints.clear();
    m_mapActorCorpseViews.clear();
    m_activeCorpseView.reset();
    m_pendingAudioEvents.clear();
    m_pendingCombatEvents.clear();
    m_projectiles.clear();
    m_projectileImpacts.clear();
    m_chests = outdoorMapDeltaData ? outdoorMapDeltaData->chests : std::vector<MapDeltaChest>();
    m_openedChests.assign(outdoorMapDeltaData ? outdoorMapDeltaData->chests.size() : 0, false);
    m_materializedChestViews.assign(m_chests.size(), std::nullopt);
    m_activeChestView.reset();
    m_eventRuntimeState = eventRuntimeState;
    m_pItemTable = &itemTable;
    m_pMonsterTable = &monsterTable;
    m_pMonsterProjectileTable = &monsterProjectileTable;
    m_pObjectTable = &objectTable;
    m_pOutdoorMapData = outdoorMapData ? &*outdoorMapData : nullptr;
    m_pOutdoorMapDeltaData = outdoorMapDeltaData ? &*outdoorMapDeltaData : nullptr;
    m_outdoorLandMask = outdoorLandMask;
    m_pSpellTable = &spellTable;
    m_pActorSpriteFrameTable = outdoorActorPreviewBillboardSet ? &outdoorActorPreviewBillboardSet->spriteFrameTable : nullptr;
    m_pProjectileSpriteFrameTable = outdoorSpriteObjectBillboardSet
        ? &outdoorSpriteObjectBillboardSet->spriteFrameTable
        : m_pActorSpriteFrameTable;
    m_monsterVisualsById.clear();
    m_outdoorFaces.clear();
    m_outdoorFaceGridCells.clear();
    m_outdoorFaceGridMinX = 0.0f;
    m_outdoorFaceGridMinY = 0.0f;
    m_outdoorFaceGridWidth = 0;
    m_outdoorFaceGridHeight = 0;
    m_outdoorMovementController.reset();
    m_actorUpdateAccumulatorSeconds = 0.0f;

    if (outdoorActorPreviewBillboardSet)
    {
        for (const ActorPreviewBillboard &billboard : outdoorActorPreviewBillboardSet->billboards)
        {
            if (billboard.monsterId <= 0)
            {
                continue;
            }

            MonsterVisualState &visualState = m_monsterVisualsById[billboard.monsterId];

            if (visualState.spriteFrameIndex == 0 && billboard.spriteFrameIndex != 0)
            {
                visualState.spriteFrameIndex = billboard.spriteFrameIndex;
            }

            for (size_t actionIndex = 0; actionIndex < visualState.actionSpriteFrameIndices.size(); ++actionIndex)
            {
                if (visualState.actionSpriteFrameIndices[actionIndex] == 0
                    && billboard.actionSpriteFrameIndices[actionIndex] != 0)
                {
                    visualState.actionSpriteFrameIndices[actionIndex] = billboard.actionSpriteFrameIndices[actionIndex];
                }
            }
        }
    }

    if (m_pOutdoorMapData != nullptr)
    {
        for (size_t bModelIndex = 0; bModelIndex < m_pOutdoorMapData->bmodels.size(); ++bModelIndex)
        {
            const OutdoorBModel &bModel = m_pOutdoorMapData->bmodels[bModelIndex];

            for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
            {
                OutdoorFaceGeometryData geometry = {};

                if (buildOutdoorFaceGeometry(bModel, bModelIndex, bModel.faces[faceIndex], faceIndex, geometry))
                {
                    m_outdoorFaces.push_back(std::move(geometry));
                }
            }
        }

        buildOutdoorFaceSpatialIndex();
    }

    if (outdoorMapData)
    {
        m_outdoorMovementController.emplace(
            *outdoorMapData,
            outdoorLandMask,
            outdoorDecorationCollisionSet,
            outdoorActorCollisionSet,
            outdoorSpriteObjectCollisionSet);
    }
    m_nextActorId = 0;
    m_nextProjectileId = 1;
    m_nextProjectileImpactId = 1;

    if (outdoorMapDeltaData)
    {
        std::vector<float> mapActorAttackAnimationSeconds(outdoorMapDeltaData->actors.size(), 0.3f);

        if (outdoorActorPreviewBillboardSet)
        {
            for (const ActorPreviewBillboard &billboard : outdoorActorPreviewBillboardSet->billboards)
            {
                if (billboard.source != ActorPreviewSource::Companion
                    || billboard.runtimeActorIndex >= mapActorAttackAnimationSeconds.size())
                {
                    continue;
                }

                uint16_t attackFrameIndex =
                    billboard.actionSpriteFrameIndices[static_cast<size_t>(ActorAnimation::AttackMelee)];

                if (attackFrameIndex == 0)
                {
                    attackFrameIndex =
                        billboard.actionSpriteFrameIndices[static_cast<size_t>(ActorAnimation::AttackRanged)];
                }

                if (attackFrameIndex == 0)
                {
                    continue;
                }

                const SpriteFrameEntry *pAttackFrame =
                    outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(attackFrameIndex, 0);

                if (pAttackFrame == nullptr || pAttackFrame->animationLengthTicks <= 0)
                {
                    continue;
                }

                mapActorAttackAnimationSeconds[billboard.runtimeActorIndex] =
                    static_cast<float>(pAttackFrame->animationLengthTicks) / TicksPerSecond;
            }
        }

        m_mapActors.reserve(outdoorMapDeltaData->actors.size());
        m_mapActorCorpseViews.assign(outdoorMapDeltaData->actors.size(), std::nullopt);

        for (size_t actorIndex = 0; actorIndex < outdoorMapDeltaData->actors.size(); ++actorIndex)
        {
            MapActorState actorState = buildMapActorState(
                monsterTable,
                outdoorMapDeltaData->actors[actorIndex],
                static_cast<uint32_t>(actorIndex),
                m_pOutdoorMapData,
                mapActorAttackAnimationSeconds[actorIndex]);
            const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actorState.monsterId);
            applyTestActorOverrides(map.id, m_pOutdoorMapData, pStats, actorState.actorId, actorState);

            if (outdoorActorPreviewBillboardSet)
            {
                for (const ActorPreviewBillboard &billboard : outdoorActorPreviewBillboardSet->billboards)
                {
                    if (billboard.source != ActorPreviewSource::Companion
                        || billboard.runtimeActorIndex != actorIndex)
                    {
                        continue;
                    }

                    actorState.spriteFrameIndex = billboard.spriteFrameIndex;
                    actorState.actionSpriteFrameIndices = billboard.actionSpriteFrameIndices;
                    actorState.useStaticSpriteFrame = billboard.useStaticFrame;
                    break;
                }
            }

            m_mapActors.push_back(std::move(actorState));
        }

        if (m_outdoorMovementController)
        {
            for (MapActorState &actor : m_mapActors)
            {
                const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actor.monsterId);
                const float collisionRadius = actorCollisionRadius(actor, pStats);
                actor.movementState = m_outdoorMovementController->initializeStateForBody(
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + GroundSnapHeight,
                    collisionRadius);
                actor.movementStateInitialized = true;
                syncActorFromMovementState(actor);
                actor.homePreciseZ = actor.preciseZ;
                actor.homeZ = actor.z;
            }
        }

        m_nextActorId = static_cast<uint32_t>(m_mapActors.size());
    }

    std::random_device randomDevice;
    const uint64_t timeSeed = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    m_sessionChestSeed = randomDevice() ^ static_cast<uint32_t>(timeSeed) ^ static_cast<uint32_t>(timeSeed >> 32);

    if (outdoorMapData)
    {
        m_spawnPoints.reserve(outdoorMapData->spawns.size());

        for (const OutdoorSpawn &spawn : outdoorMapData->spawns)
        {
            m_spawnPoints.push_back(buildSpawnPointState(map, monsterTable, spawn));
        }

        if (shouldMaterializeEncounterSpawnsOnInitialize(outdoorMapDeltaData))
        {
            for (size_t spawnIndex = 0; spawnIndex < m_spawnPoints.size(); ++spawnIndex)
            {
                const SpawnPointState &spawn = m_spawnPoints[spawnIndex];

                if (spawn.typeId != 3 || spawn.encounterSlot <= 0)
                {
                    continue;
                }

                const uint32_t resolvedCount = resolveEncounterSpawnCount(
                    m_map,
                    spawn.encounterSlot,
                    0,
                    m_sessionChestSeed,
                    static_cast<uint32_t>(spawnIndex));

                spawnEncounterFromResolvedData(
                    spawn.encounterSlot,
                    spawn.fixedTier,
                    resolvedCount,
                    static_cast<float>(-spawn.x),
                    static_cast<float>(spawn.y),
                    static_cast<float>(spawn.z),
                    spawn.radius,
                    spawn.attributes,
                    spawn.group,
                    0,
                    true,
                    spawnIndex,
                    false);
            }
        }
    }

    applyEventRuntimeState();
}

bool OutdoorWorldRuntime::isInitialized() const
{
    return m_mapId != 0 || !m_mapName.empty() || m_eventRuntimeState.has_value();
}

int OutdoorWorldRuntime::mapId() const
{
    return m_mapId;
}

const std::string &OutdoorWorldRuntime::mapName() const
{
    return m_mapName;
}

float OutdoorWorldRuntime::gameMinutes() const
{
    return m_gameMinutes;
}

int OutdoorWorldRuntime::currentHour() const
{
    int currentHour = static_cast<int>(m_gameMinutes / 60.0f) % 24;

    if (currentHour < 0)
    {
        currentHour += 24;
    }

    return currentHour;
}

void OutdoorWorldRuntime::advanceGameMinutes(float minutes)
{
    if (minutes <= 0.0f)
    {
        return;
    }

    m_gameMinutes += minutes;
}

void OutdoorWorldRuntime::updateMapActors(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f || m_pMonsterTable == nullptr)
    {
        return;
    }

    m_actorUpdateAccumulatorSeconds =
        std::min(m_actorUpdateAccumulatorSeconds + deltaSeconds, MaxAccumulatedActorUpdateSeconds);

    while (m_actorUpdateAccumulatorSeconds >= ActorUpdateStepSeconds)
    {
        std::vector<std::pair<size_t, float>> activeActorDistances;
        activeActorDistances.reserve(m_mapActors.size());

        for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
        {
            const MapActorState &actor = m_mapActors[actorIndex];

            if (actor.isDead || actor.isInvisible)
            {
                continue;
            }

            const float deltaX = partyX - actor.preciseX;
            const float deltaY = partyY - actor.preciseY;
            const float deltaZ = partyZ - actor.preciseZ;
            float distanceToParty = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ)
                - static_cast<float>(actor.radius);

            if (distanceToParty < 0.0f)
            {
                distanceToParty = 0.0f;
            }

            if (distanceToParty <= ActiveActorUpdateRange)
            {
                activeActorDistances.push_back({actorIndex, distanceToParty});
            }
        }

        std::stable_sort(
            activeActorDistances.begin(),
            activeActorDistances.end(),
            [](const std::pair<size_t, float> &left, const std::pair<size_t, float> &right)
            {
                return left.second < right.second;
            });

        std::vector<bool> activeActorMask(m_mapActors.size(), false);

        for (size_t index = 0; index < activeActorDistances.size() && index < MaxActiveActorUpdates; ++index)
        {
            activeActorMask[activeActorDistances[index].first] = true;
        }

        for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
        {
            MapActorState &actor = m_mapActors[actorIndex];

            if (actor.isDead)
            {
                actor.aiState = ActorAiState::Dead;
                actor.animation = ActorAnimation::Dead;
                continue;
            }

            const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

            if (pStats == nullptr)
            {
                actor.animation = ActorAnimation::Standing;
                continue;
            }

            if (!activeActorMask[actorIndex])
            {
                actor.aiState = ActorAiState::Standing;
                actor.animation = ActorAnimation::Standing;
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.velocityZ = 0.0f;
                actor.hasDetectedParty = false;
                actor.attackImpactTriggered = false;
                continue;
            }

            if (m_outdoorMovementController && !actor.movementStateInitialized)
            {
                const float collisionRadius = actorCollisionRadius(actor, pStats);
                actor.movementState = m_outdoorMovementController->initializeStateForBody(
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + GroundSnapHeight,
                    collisionRadius);
                actor.movementStateInitialized = true;
                syncActorFromMovementState(actor);
            }

            actor.animationTimeTicks += ActorUpdateStepSeconds * TicksPerSecond;

            if (actor.aiState == ActorAiState::Dying)
            {
                actor.actionSeconds = std::max(0.0f, actor.actionSeconds - ActorUpdateStepSeconds);
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.velocityZ = 0.0f;

                if (actor.actionSeconds <= 0.0f)
                {
                    setMapActorDead(actorIndex, true, false);
                }

                continue;
            }

            if (actor.aiState == ActorAiState::Stunned)
            {
                actor.actionSeconds = std::max(0.0f, actor.actionSeconds - ActorUpdateStepSeconds);
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.velocityZ = 0.0f;

                if (actor.actionSeconds <= 0.0f)
                {
                    actor.aiState = ActorAiState::Standing;
                    actor.animation = ActorAnimation::Standing;
                    actor.animationTimeTicks = 0.0f;
                }

                continue;
            }

            actor.idleDecisionSeconds = std::max(0.0f, actor.idleDecisionSeconds - ActorUpdateStepSeconds);
            actor.attackCooldownSeconds = std::max(0.0f, actor.attackCooldownSeconds - ActorUpdateStepSeconds);
            actor.actionSeconds = std::max(0.0f, actor.actionSeconds - ActorUpdateStepSeconds);

            const int relationToParty = m_pMonsterTable->getRelationToParty(actor.monsterId);
            const float partySenseRange = actor.hostileToParty
                ? HostilityLongRange
                : hostilityRangeForRelation(relationToParty);

            const float deltaPartyX = partyX - actor.preciseX;
            const float deltaPartyY = partyY - actor.preciseY;
            const float distanceToParty = length2d(deltaPartyX, deltaPartyY);
            const float actorTargetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
            const float partyTargetZ = partyZ + PartyTargetHeightOffset;
            const float deltaPartyZ = partyTargetZ - actorTargetZ;
            const bool canSenseParty =
                partySenseRange > 0.0f
                && std::abs(deltaPartyX) <= partySenseRange
                && std::abs(deltaPartyY) <= partySenseRange
                && std::abs(deltaPartyZ) <= partySenseRange
                && isWithinRange3d(deltaPartyX, deltaPartyY, deltaPartyZ, partySenseRange);
            const auto hasClearOutdoorLineOfSight =
                [this](const bx::Vec3 &start, const bx::Vec3 &end) -> bool
            {
                return this->hasClearOutdoorLineOfSight(start, end);
            };
            const bool movementAllowed = pStats->movementType != MonsterTable::MonsterMovementType::Stationary;
            const CombatTargetInfo combatTarget =
                selectCombatTarget(
                    actor,
                    actorIndex,
                    m_mapActors,
                    *m_pMonsterTable,
                    partyX,
                    partyY,
                    partyZ,
                    hasClearOutdoorLineOfSight);
            const bool hasCombatTarget = combatTarget.kind != CombatTargetKind::None;
            const bool targetIsParty = combatTarget.kind == CombatTargetKind::Party;
            const bool targetIsActor = combatTarget.kind == CombatTargetKind::Actor;
            bool shouldEngageTarget = hasCombatTarget && combatTarget.canSense;

            if (targetIsActor && actor.hostilityType == 0)
            {
                const float promotionRange = hostilityPromotionRangeForFriendlyActor(combatTarget.relationToTarget);
                const bool shouldPromoteHostility =
                    combatTarget.relationToTarget == 1
                    || isWithinRange3d(
                        combatTarget.deltaX,
                        combatTarget.deltaY,
                        combatTarget.deltaZ,
                        promotionRange);

                if (shouldPromoteHostility)
                {
                    actor.hostilityType = 4;
                }
                else
                {
                    shouldEngageTarget = false;
                }
            }

            if (targetIsParty && !actor.hasDetectedParty)
            {
                actor.hasDetectedParty = true;
                pushAudioEvent(pStats->awareSoundId, actor.actorId, "monster_alert");
            }
            else if (!targetIsParty || !canSenseParty)
            {
                actor.hasDetectedParty = false;
            }

            const bool shouldFlee = shouldEngageTarget
                && combatTarget.distanceToTarget <= FleeThresholdRange
                && shouldFleeForAiType(*pStats, actor);

            const bool inMeleeRange =
                combatTarget.edgeDistance <= meleeRangeForCombatTarget(targetIsActor);
            const bool attackJustCompleted =
                actor.aiState == ActorAiState::Attacking
                && actor.actionSeconds <= 0.0f
                && !actor.attackImpactTriggered;
            const bool attackInProgress =
                actor.aiState == ActorAiState::Attacking
                && actor.actionSeconds > 0.0f;
            const bool partyIsVeryNearActor =
                distanceToParty <= (static_cast<float>(actor.radius) + PartyCollisionRadius + 16.0f)
                && std::abs(partyZ - actor.preciseZ) <= static_cast<float>(std::max<uint16_t>(actor.height, 192));
            const bool friendlyNearParty =
                !shouldEngageTarget
                && !actor.hostileToParty
                && partyIsVeryNearActor;
            float desiredMoveX = 0.0f;
            float desiredMoveY = 0.0f;
            ActorAiState nextAiState = ActorAiState::Standing;
            ActorAnimation nextAnimation = ActorAnimation::Standing;

            if (attackJustCompleted)
            {
                const int resolvedDamage = resolveMonsterAbilityDamage(*pStats, actor.queuedAttackAbility);

                if (isRangedAttackAbility(*pStats, actor.queuedAttackAbility))
                {
                    CombatEvent event = {};
                    event.type = CombatEvent::Type::MonsterRangedRelease;
                    event.sourceId = actor.actorId;
                    event.fromSummonedMonster = false;
                    event.ability = actor.queuedAttackAbility;
                    event.damage = resolvedDamage;
                    m_pendingCombatEvents.push_back(std::move(event));

                    if (hasCombatTarget)
                    {
                        spawnProjectileFromMapActor(
                            actor,
                            *pStats,
                            actor.queuedAttackAbility,
                            combatTarget.targetX,
                            combatTarget.targetY,
                            combatTarget.targetZ);
                    }
                }
                else if (targetIsParty)
                {
                    CombatEvent event = {};
                    event.type = CombatEvent::Type::MonsterMeleeImpact;
                    event.sourceId = actor.actorId;
                    event.fromSummonedMonster = false;
                    event.ability = actor.queuedAttackAbility;
                    event.damage = resolvedDamage;
                    m_pendingCombatEvents.push_back(std::move(event));
                }
                else if (targetIsActor)
                {
                    applyMonsterAttackToMapActor(combatTarget.actorIndex, resolvedDamage, actor.actorId);
                }

                actor.attackImpactTriggered = true;
            }

            if (attackInProgress)
            {
                nextAiState = ActorAiState::Attacking;
                nextAnimation = actor.animation;
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
            }
            else if (shouldFlee)
            {
                nextAiState = ActorAiState::Fleeing;
                nextAnimation = movementAllowed ? ActorAnimation::Walking : ActorAnimation::Standing;

                if (combatTarget.horizontalDistanceToTarget > 0.01f)
                {
                    desiredMoveX = -combatTarget.deltaX / combatTarget.horizontalDistanceToTarget;
                    desiredMoveY = -combatTarget.deltaY / combatTarget.horizontalDistanceToTarget;
                    faceDirection(actor, desiredMoveX, desiredMoveY);
                }

                actor.moveDirectionX = desiredMoveX;
                actor.moveDirectionY = desiredMoveY;
            }
            else if (shouldEngageTarget)
            {
                const MonsterAttackAbility chosenAbility = chooseAttackAbility(actor, *pStats);
                const bool chosenAbilityIsRanged = isRangedAttackAbility(*pStats, chosenAbility);
                const bool chosenAbilityIsMelee = isMeleeAttackAbility(*pStats, chosenAbility);
                const bool stationaryOrTooCloseForRangedPursuit = !movementAllowed || inMeleeRange;

                if (chosenAbilityIsRanged && actor.attackCooldownSeconds <= 0.0f)
                {
                    actor.moveDirectionX = 0.0f;
                    actor.moveDirectionY = 0.0f;
                    faceDirection(actor, combatTarget.deltaX, combatTarget.deltaY);
                    nextAiState = ActorAiState::Attacking;
                    nextAnimation = attackAnimationForAbility(*pStats, chosenAbility);
                    actor.queuedAttackAbility = chosenAbility;
                    const float attackAnimationSeconds = actorAnimationSeconds(
                        m_pActorSpriteFrameTable,
                        actor,
                        nextAnimation,
                        actor.attackAnimationSeconds);
                    actor.attackCooldownSeconds = attackCooldownDurationSeconds(
                        *pStats,
                        chosenAbility,
                        attackAnimationSeconds,
                        actor.recoverySeconds);
                    actor.actionSeconds = attackActionDurationSeconds(attackAnimationSeconds);
                    actor.attackImpactTriggered = false;
                    actor.animationTimeTicks = 0.0f;
                    pushAudioEvent(pStats->attackSoundId, actor.actorId, "monster_attack");
                }
                else if (chosenAbilityIsRanged)
                {
                    if (stationaryOrTooCloseForRangedPursuit)
                    {
                        actor.moveDirectionX = 0.0f;
                        actor.moveDirectionY = 0.0f;
                        faceDirection(actor, combatTarget.deltaX, combatTarget.deltaY);
                        nextAiState = ActorAiState::Standing;
                        nextAnimation = ActorAnimation::Standing;
                    }
                    else
                    {
                        nextAiState = ActorAiState::Pursuing;
                        nextAnimation = ActorAnimation::Walking;

                        if (actor.aiState == ActorAiState::Pursuing
                            && actor.actionSeconds > 0.0f
                            && (std::abs(actor.moveDirectionX) > 0.001f || std::abs(actor.moveDirectionY) > 0.001f))
                        {
                            desiredMoveX = actor.moveDirectionX;
                            desiredMoveY = actor.moveDirectionY;
                        }
                        else
                        {
                            const uint32_t decisionSeed =
                                static_cast<uint32_t>(actor.actorId + 1) * 1103515245u
                                + actor.pursueDecisionCount * 2654435761u
                                + 0x9e3779b9u;
                            ++actor.pursueDecisionCount;

                            if (beginPursueAction(
                                    actor,
                                    combatTarget.deltaX,
                                    combatTarget.deltaY,
                                    combatTarget.horizontalDistanceToTarget,
                                    static_cast<float>(std::max(
                                        1,
                                        actor.moveSpeed > 0 ? static_cast<int>(actor.moveSpeed) : pStats->speed)),
                                    PursueActionMode::OffsetShort,
                                    decisionSeed))
                            {
                                actor.actionSeconds = std::max(actor.actionSeconds, actor.recoverySeconds);
                                desiredMoveX = actor.moveDirectionX;
                                desiredMoveY = actor.moveDirectionY;
                            }
                            else
                            {
                                nextAiState = ActorAiState::Standing;
                                nextAnimation = ActorAnimation::Standing;
                            }
                        }
                    }
                }
                else if (chosenAbilityIsMelee && inMeleeRange)
                {
                    actor.moveDirectionX = 0.0f;
                    actor.moveDirectionY = 0.0f;
                    faceDirection(actor, combatTarget.deltaX, combatTarget.deltaY);

                    if (actor.attackCooldownSeconds <= 0.0f)
                    {
                        nextAiState = ActorAiState::Attacking;
                        nextAnimation = attackAnimationForAbility(*pStats, chosenAbility);
                        actor.queuedAttackAbility = chosenAbility;
                        const float attackAnimationSeconds = actorAnimationSeconds(
                            m_pActorSpriteFrameTable,
                            actor,
                            nextAnimation,
                            actor.attackAnimationSeconds);
                        actor.attackCooldownSeconds = attackCooldownDurationSeconds(
                            *pStats,
                            chosenAbility,
                            attackAnimationSeconds,
                            actor.recoverySeconds);
                        actor.actionSeconds = attackActionDurationSeconds(attackAnimationSeconds);
                        actor.attackImpactTriggered = false;
                        actor.animationTimeTicks = 0.0f;
                        pushAudioEvent(pStats->attackSoundId, actor.actorId, "monster_attack");
                    }
                    else
                    {
                        nextAiState = ActorAiState::Standing;
                        nextAnimation = ActorAnimation::Standing;
                    }
                }
                else
                {
                    nextAiState = ActorAiState::Pursuing;
                    nextAnimation = movementAllowed ? ActorAnimation::Walking : ActorAnimation::Standing;

                    if (!movementAllowed)
                    {
                        actor.moveDirectionX = 0.0f;
                        actor.moveDirectionY = 0.0f;
                    }
                    else if (actor.aiState == ActorAiState::Pursuing
                        && actor.actionSeconds > 0.0f
                        && (std::abs(actor.moveDirectionX) > 0.001f || std::abs(actor.moveDirectionY) > 0.001f))
                    {
                        desiredMoveX = actor.moveDirectionX;
                        desiredMoveY = actor.moveDirectionY;
                    }
                    else
                    {
                        PursueActionMode pursueMode = PursueActionMode::Direct;

                        if (combatTarget.edgeDistance >= 1024.0f)
                        {
                            pursueMode = PursueActionMode::OffsetWide;
                        }

                        const uint32_t decisionSeed =
                            static_cast<uint32_t>(actor.actorId + 1) * 1103515245u
                            + actor.pursueDecisionCount * 2654435761u
                            + 0x9e3779b9u;
                        ++actor.pursueDecisionCount;

                        if (beginPursueAction(
                                actor,
                                combatTarget.deltaX,
                                combatTarget.deltaY,
                                combatTarget.horizontalDistanceToTarget,
                                static_cast<float>(std::max(
                                    1,
                                    actor.moveSpeed > 0 ? static_cast<int>(actor.moveSpeed) : pStats->speed)),
                                pursueMode,
                                decisionSeed))
                        {
                            desiredMoveX = actor.moveDirectionX;
                            desiredMoveY = actor.moveDirectionY;
                        }
                        else
                        {
                            nextAiState = ActorAiState::Standing;
                            nextAnimation = ActorAnimation::Standing;
                        }
                    }
                }
            }
            else if (friendlyNearParty)
            {
                nextAiState = ActorAiState::Standing;
                nextAnimation = ActorAnimation::Standing;
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.actionSeconds = std::max(actor.actionSeconds, 0.25f);
                actor.idleDecisionSeconds = std::max(actor.idleDecisionSeconds, 0.25f);
            }
            else
            {
                const float wanderRadius = wanderRadiusForMovementType(pStats->movementType);
                const float deltaHomeX = actor.homePreciseX - actor.preciseX;
                const float deltaHomeY = actor.homePreciseY - actor.preciseY;
                const float distanceToHome = length2d(deltaHomeX, deltaHomeY);

                if (actor.hostileToParty)
                {
                    nextAiState = ActorAiState::Standing;
                    nextAnimation = ActorAnimation::Standing;

                    if (actor.actionSeconds <= 0.0f)
                    {
                        beginStandAwhile(actor, false);
                        nextAnimation = actor.animation;
                    }

                    actor.moveDirectionX = 0.0f;
                    actor.moveDirectionY = 0.0f;
                }
                else if (wanderRadius <= 0.0f)
                {
                    nextAiState = ActorAiState::Standing;
                    nextAnimation = ActorAnimation::Standing;

                    if (actor.actionSeconds <= 0.0f)
                    {
                        beginStandAwhile(actor, false);
                        nextAnimation = actor.animation;
                    }

                    actor.moveDirectionX = 0.0f;
                    actor.moveDirectionY = 0.0f;
                }
                else if (distanceToHome > wanderRadius)
                {
                    nextAiState = ActorAiState::Wandering;
                    nextAnimation = ActorAnimation::Walking;

                    if (distanceToHome > 0.01f)
                    {
                        desiredMoveX = deltaHomeX / distanceToHome;
                        desiredMoveY = deltaHomeY / distanceToHome;
                        actor.yawRadians = std::atan2(desiredMoveY, desiredMoveX);
                    }

                    actor.moveDirectionX = desiredMoveX;
                    actor.moveDirectionY = desiredMoveY;
                }
                else if (actor.actionSeconds > 0.0f
                    && (std::abs(actor.moveDirectionX) > 0.001f || std::abs(actor.moveDirectionY) > 0.001f))
                {
                    nextAiState = ActorAiState::Wandering;
                    nextAnimation = ActorAnimation::Walking;
                    desiredMoveX = actor.moveDirectionX;
                    desiredMoveY = actor.moveDirectionY;
                }
                else if (actor.aiState == ActorAiState::Wandering)
                {
                    beginStandAwhile(actor, false);
                    nextAiState = ActorAiState::Standing;
                    nextAnimation = actor.animation;
                }
                else if (actor.actionSeconds > 0.0f)
                {
                    nextAiState = ActorAiState::Standing;
                    nextAnimation = ActorAnimation::Standing;
                }
                else
                {
                    const uint32_t decisionSeed =
                        static_cast<uint32_t>(actor.actorId + 1) * 1103515245u
                        + actor.idleDecisionCount * 2654435761u
                        + 12345u;
                    ++actor.idleDecisionCount;

                    if ((decisionSeed % 100u) < 25u)
                    {
                        beginStandAwhile(actor, false);
                        nextAiState = ActorAiState::Standing;
                        nextAnimation = actor.animation;
                    }
                    else
                    {
                        if (beginIdleWander(
                                actor,
                                decisionSeed,
                                wanderRadius,
                                static_cast<float>(std::max(
                                    1,
                                    actor.moveSpeed > 0 ? static_cast<int>(actor.moveSpeed) : pStats->speed))))
                        {
                            nextAiState = ActorAiState::Wandering;
                            nextAnimation = ActorAnimation::Walking;
                            desiredMoveX = actor.moveDirectionX;
                            desiredMoveY = actor.moveDirectionY;
                        }
                        else
                        {
                            nextAiState = ActorAiState::Standing;
                            nextAnimation = actor.animation;
                        }
                    }
                }
            }

            if (attackInProgress)
            {
                nextAnimation = actor.animation;
            }

            if (nextAnimation != actor.animation)
            {
                actor.animationTimeTicks = 0.0f;
            }

            actor.aiState = nextAiState;
            actor.animation = nextAnimation;

            actor.velocityX = 0.0f;
            actor.velocityY = 0.0f;
            actor.velocityZ = 0.0f;

            if (movementAllowed && (std::abs(desiredMoveX) > 0.001f || std::abs(desiredMoveY) > 0.001f))
            {
                const float moveSpeed = static_cast<float>(std::max(
                    1,
                    actor.moveSpeed > 0 ? static_cast<int>(actor.moveSpeed) : pStats->speed));

                if (m_pOutdoorMapData != nullptr)
                {
                    applyOutdoorWaterRestriction(
                        *m_pOutdoorMapData,
                        m_outdoorLandMask,
                        pStats,
                        actor,
                        moveSpeed,
                        desiredMoveX,
                        desiredMoveY,
                        nextAiState,
                        nextAnimation);
                }

                actor.velocityX = desiredMoveX * moveSpeed;
                actor.velocityY = desiredMoveY * moveSpeed;
                const float moveDeltaX = actor.velocityX * ActorUpdateStepSeconds;
                const float moveDeltaY = actor.velocityY * ActorUpdateStepSeconds;
                bool moved = false;

                if (m_outdoorMovementController && actor.movementStateInitialized)
                {
                    m_outdoorMovementController->setActorColliders(
                        buildNearbyActorMovementColliders(m_mapActors, activeActorMask, *m_pMonsterTable));
                    const float collisionRadius = actorCollisionRadius(actor, pStats);
                    const float collisionHeight = actorCollisionHeight(actor, collisionRadius);
                    actor.movementState = m_outdoorMovementController->resolveOutdoorActorMove(
                        actor.movementState,
                        OutdoorBodyDimensions{collisionRadius, collisionHeight},
                        actor.velocityX,
                        actor.velocityY,
                        actor.velocityZ,
                        pStats->canFly,
                        ActorUpdateStepSeconds,
                        OutdoorIgnoredActorCollider{OutdoorActorCollisionSource::MapDelta, actorIndex});
                    syncActorFromMovementState(actor);
                    actor.velocityZ = actor.movementState.verticalVelocity;
                    moved = true;
                }
                else if (m_pOutdoorMapData != nullptr)
                {
                    moved = tryMoveActorInWorld(
                        actor,
                        *m_pOutdoorMapData,
                        m_outdoorFaces,
                        pStats,
                        moveDeltaX,
                        moveDeltaY);

                    if (!moved && std::abs(moveDeltaX) > 0.001f)
                    {
                        moved = tryMoveActorInWorld(actor, *m_pOutdoorMapData, m_outdoorFaces, pStats, moveDeltaX, 0.0f);
                    }

                    if (!moved && std::abs(moveDeltaY) > 0.001f)
                    {
                        moved = tryMoveActorInWorld(actor, *m_pOutdoorMapData, m_outdoorFaces, pStats, 0.0f, moveDeltaY);
                    }
                }
                else
                {
                    actor.preciseX += moveDeltaX;
                    actor.preciseY += moveDeltaY;
                    moved = true;
                }

                if (!moved)
                {
                    actor.velocityX = 0.0f;
                    actor.velocityY = 0.0f;

                    if (actor.aiState != ActorAiState::Pursuing)
                    {
                        actor.moveDirectionX = 0.0f;
                        actor.moveDirectionY = 0.0f;
                        actor.actionSeconds = std::min(actor.actionSeconds, 0.25f);
                        actor.aiState = ActorAiState::Standing;
                        actor.animation = ActorAnimation::Standing;
                    }
                }
            }
            actor.x = static_cast<int>(std::lround(actor.preciseX));
            actor.y = static_cast<int>(std::lround(actor.preciseY));
            actor.z = static_cast<int>(std::lround(actor.preciseZ));
        }

        updateProjectiles(ActorUpdateStepSeconds, partyX, partyY, partyZ);
        m_actorUpdateAccumulatorSeconds -= ActorUpdateStepSeconds;
    }
}

bool OutdoorWorldRuntime::spawnProjectileFromMapActor(
    const MapActorState &actor,
    const MonsterTable::MonsterStatsEntry &stats,
    MonsterAttackAbility ability,
    float targetX,
    float targetY,
    float targetZ
)
{
    if (ability == MonsterAttackAbility::Spell1 || ability == MonsterAttackAbility::Spell2)
    {
        return castSpellFromMapActor(actor, stats, ability, targetX, targetY, targetZ);
    }

    if (m_pMonsterProjectileTable == nullptr || m_pObjectTable == nullptr || m_pSpellTable == nullptr)
    {
        std::cout
            << "Projectile spawn skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " reason=missing_runtime_tables"
            << '\n';
        return false;
    }

    ResolvedProjectileDefinition definition = {};

    if (!resolveProjectileDefinition(
            stats,
            ability,
            *m_pMonsterProjectileTable,
            *m_pObjectTable,
            *m_pSpellTable,
            definition))
    {
        const std::string projectileToken =
            ability == MonsterAttackAbility::Attack1
                ? stats.attack1MissileType
                : ability == MonsterAttackAbility::Attack2 ? stats.attack2MissileType : std::string();
        const std::string spellName =
            ability == MonsterAttackAbility::Spell1
                ? stats.spell1Name
                : ability == MonsterAttackAbility::Spell2 ? stats.spell2Name : std::string();

        std::cout
            << "Projectile spawn skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " missile=\"" << debugStringOrNone(projectileToken) << "\""
            << " spell=\"" << debugStringOrNone(spellName) << "\""
            << " reason=unresolved_definition"
            << '\n';
        return false;
    }

    const float sourceX = actor.preciseX;
    const float sourceY = actor.preciseY;
    const float sourceZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    const float aimX = targetX;
    const float aimY = targetY;
    const float aimZ = targetZ;
    const float deltaX = aimX - sourceX;
    const float deltaY = aimY - sourceY;
    const float deltaZ = aimZ - sourceZ;
    const float distance = length3d(deltaX, deltaY, deltaZ);

    if (distance <= 0.01f)
    {
        std::cout
            << "Projectile spawn skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " reason=zero_distance_target"
            << '\n';
        return false;
    }

    const float directionX = deltaX / distance;
    const float directionY = deltaY / distance;
    const float directionZ = deltaZ / distance;

    ProjectileState projectile = {};
    projectile.projectileId = m_nextProjectileId++;
    projectile.sourceId = actor.actorId;
    projectile.sourceMonsterId = actor.monsterId;
    projectile.ability = ability;
    projectile.objectDescriptionId = definition.objectDescriptionId;
    projectile.objectSpriteId = definition.objectSpriteId;
    projectile.objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    projectile.impactObjectDescriptionId = definition.impactObjectDescriptionId;
    projectile.radius = definition.radius;
    projectile.height = definition.height;
    projectile.spellId = definition.spellId;
    projectile.effectSoundId = definition.effectSoundId;
    projectile.objectName = definition.objectName;
    projectile.objectSpriteName = definition.objectSpriteName;
    projectile.x = sourceX + directionX * (static_cast<float>(actor.radius) + 8.0f);
    projectile.y = sourceY + directionY * (static_cast<float>(actor.radius) + 8.0f);
    projectile.z = sourceZ;
    projectile.velocityX = directionX * definition.speed;
    projectile.velocityY = directionY * definition.speed;
    projectile.velocityZ = directionZ * definition.speed;
    projectile.lifetimeTicks = definition.lifetimeTicks;
    m_projectiles.push_back(std::move(projectile));
    logProjectileSpawn("monster", m_projectiles.back(), directionX, directionY, directionZ, definition.speed);

    if (definition.effectSoundId > 0)
    {
        pushAudioEvent(static_cast<uint32_t>(definition.effectSoundId), actor.actorId, "monster_spell_release");
    }

    return true;
}

bool OutdoorWorldRuntime::castSpellFromMapActor(
    const MapActorState &actor,
    const MonsterTable::MonsterStatsEntry &stats,
    MonsterAttackAbility ability,
    float targetX,
    float targetY,
    float targetZ
)
{
    if (m_pSpellTable == nullptr)
    {
        std::cout
            << "Spell cast skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " reason=missing_spell_table"
            << '\n';
        return false;
    }

    const std::string &spellName =
        ability == MonsterAttackAbility::Spell1 ? stats.spell1Name : stats.spell2Name;

    if (spellName.empty())
    {
        std::cout
            << "Spell cast skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " reason=empty_spell_name"
            << '\n';
        return false;
    }

    if (!isProjectileSpellName(spellName) && spellName != "meteor shower")
    {
        std::cout
            << "Spell cast skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " spell=\"" << spellName << "\""
            << " reason=unsupported_nonprojectile_spell"
            << '\n';
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findByName(spellName);

    if (pSpellEntry == nullptr)
    {
        std::cout
            << "Spell cast skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " spell=\"" << spellName << "\""
            << " reason=spell_not_found"
            << '\n';
        return false;
    }

    SpellCastRequest request = {};
    request.sourceKind = RuntimeSpellSourceKind::Actor;
    request.sourceId = actor.actorId;
    request.sourceMonsterId = actor.monsterId;
    request.ability = ability;
    request.spellId = static_cast<uint32_t>(pSpellEntry->id);
    request.skillLevel = static_cast<uint32_t>(std::max(stats.level, 1));
    request.skillMastery = pSpellEntry->id == static_cast<int>(MeteorShowerSpellId)
        ? static_cast<uint32_t>(SkillMastery::Master)
        : static_cast<uint32_t>(SkillMastery::None);
    request.sourceX = actor.preciseX;
    request.sourceY = actor.preciseY;
    request.sourceZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    request.targetX = targetX;
    request.targetY = targetY;
    request.targetZ = targetZ;
    return castSpell(request);
}

bool OutdoorWorldRuntime::castSpell(const SpellCastRequest &request)
{
    if (m_pObjectTable == nullptr || m_pSpellTable == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(request.spellId));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    ResolvedProjectileDefinition definition = {};

    if (!resolveSpellDefinition(*pSpellEntry, *m_pObjectTable, definition))
    {
        return false;
    }

    if (request.spellId == MeteorShowerSpellId)
    {
        return castMeteorShower(request, definition);
    }

    return castDirectSpellProjectile(request, definition);
}

bool OutdoorWorldRuntime::castDirectSpellProjectile(
    const SpellCastRequest &request,
    const ResolvedProjectileDefinition &definition
)
{
    return spawnSpellProjectile(
        request,
        definition,
        request.sourceX,
        request.sourceY,
        request.sourceZ,
        request.targetX,
        request.targetY,
        request.targetZ,
        0.0f);
}

bool OutdoorWorldRuntime::castMeteorShower(
    const SpellCastRequest &request,
    const ResolvedProjectileDefinition &definition
)
{
    uint32_t meteorCount = meteorShowerCountForMastery(request.skillMastery);

    if (meteorCount == 0)
    {
        meteorCount = 1;
    }

    uint32_t seed = request.spellId * 1315423911u;
    seed ^= static_cast<uint32_t>(std::lround(std::abs(request.targetX)));
    seed ^= static_cast<uint32_t>(std::lround(std::abs(request.targetY))) << 1;
    seed ^= static_cast<uint32_t>(std::lround(std::abs(request.targetZ))) << 2;
    seed ^= m_nextProjectileId;
    std::mt19937 rng(seed);
    std::uniform_real_distribution<float> targetOffsetDistribution(-MeteorShowerTargetSpread, MeteorShowerTargetSpread);
    std::uniform_real_distribution<float> spawnHeightDistribution(
        MeteorShowerSpawnBaseHeight,
        MeteorShowerSpawnBaseHeight + MeteorShowerSpawnHeightVariance);
    bool spawnedAny = false;

    for (uint32_t meteorIndex = 0; meteorIndex < meteorCount; ++meteorIndex)
    {
        const float meteorTargetX = request.targetX + targetOffsetDistribution(rng);
        const float meteorTargetY = request.targetY + targetOffsetDistribution(rng);
        float meteorTargetZ = request.targetZ;

        if (m_pOutdoorMapData != nullptr)
        {
            meteorTargetZ = std::max(
                meteorTargetZ,
                sampleOutdoorTerrainHeight(*m_pOutdoorMapData, meteorTargetX, meteorTargetY));
        }

        const float meteorSourceZ = meteorTargetZ + spawnHeightDistribution(rng);
        spawnedAny = spawnSpellProjectile(
            request,
            definition,
            meteorTargetX,
            meteorTargetY,
            meteorSourceZ,
            meteorTargetX,
            meteorTargetY,
            meteorTargetZ,
            0.0f)
            || spawnedAny;
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::spawnSpellProjectile(
    const SpellCastRequest &request,
    const ResolvedProjectileDefinition &definition,
    float sourceX,
    float sourceY,
    float sourceZ,
    float targetX,
    float targetY,
    float targetZ,
    float spawnForwardOffset
)
{
    const float deltaX = targetX - sourceX;
    const float deltaY = targetY - sourceY;
    const float deltaZ = targetZ - sourceZ;
    const float distance = length3d(deltaX, deltaY, deltaZ);

    if (distance <= 0.01f)
    {
        ProjectileState impactSource = {};
        impactSource.projectileId = m_nextProjectileId++;
        impactSource.sourceId = request.sourceId;
        impactSource.sourceMonsterId = request.sourceMonsterId;
        impactSource.fromSummonedMonster = request.fromSummonedMonster;
        impactSource.ability = request.ability;
        impactSource.objectName = definition.objectName;
        impactSource.objectSpriteName = definition.objectSpriteName;
        impactSource.objectSpriteId = definition.objectSpriteId;
        impactSource.objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
            m_pProjectileSpriteFrameTable,
            definition.objectSpriteId,
            definition.objectSpriteName);
        impactSource.impactObjectDescriptionId = definition.impactObjectDescriptionId;
        logProjectileCollision(impactSource, "instant", "spell_zero_distance", {sourceX, sourceY, sourceZ});
        spawnProjectileImpact(impactSource, sourceX, sourceY, sourceZ);
        return true;
    }

    const float directionX = deltaX / distance;
    const float directionY = deltaY / distance;
    const float directionZ = deltaZ / distance;

    ProjectileState projectile = {};
    projectile.projectileId = m_nextProjectileId++;
    projectile.sourceId = request.sourceId;
    projectile.sourceMonsterId = request.sourceMonsterId;
    projectile.fromSummonedMonster = request.fromSummonedMonster;
    projectile.ability = request.ability;
    projectile.objectDescriptionId = definition.objectDescriptionId;
    projectile.objectSpriteId = definition.objectSpriteId;
    projectile.objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    projectile.impactObjectDescriptionId = definition.impactObjectDescriptionId;
    projectile.radius = definition.radius;
    projectile.height = definition.height;
    projectile.spellId = definition.spellId;
    projectile.effectSoundId = definition.effectSoundId;
    projectile.skillLevel = request.skillLevel;
    projectile.skillMastery = request.skillMastery;
    projectile.objectName = definition.objectName;
    projectile.objectSpriteName = definition.objectSpriteName;
    projectile.x = sourceX + directionX * spawnForwardOffset;
    projectile.y = sourceY + directionY * spawnForwardOffset;
    projectile.z = sourceZ;
    projectile.velocityX = directionX * definition.speed;
    projectile.velocityY = directionY * definition.speed;
    projectile.velocityZ = directionZ * definition.speed;
    projectile.lifetimeTicks = definition.lifetimeTicks;
    m_projectiles.push_back(std::move(projectile));
    logProjectileSpawn(
        spellSourceKindName(request.sourceKind),
        m_projectiles.back(),
        directionX,
        directionY,
        directionZ,
        definition.speed);

    if (definition.effectSoundId > 0)
    {
        const std::string reason =
            request.sourceKind == RuntimeSpellSourceKind::Event ? "event_spell_release" : "monster_spell_release";
        pushAudioEvent(static_cast<uint32_t>(definition.effectSoundId), request.sourceId, reason);
    }

    return true;
}

void OutdoorWorldRuntime::spawnProjectileImpact(const ProjectileState &projectile, float x, float y, float z)
{
    if (projectile.impactObjectDescriptionId == 0 || m_pObjectTable == nullptr)
    {
        return;
    }

    const ObjectEntry *pImpactEntry = m_pObjectTable->get(projectile.impactObjectDescriptionId);

    if (pImpactEntry == nullptr)
    {
        return;
    }

    if (pImpactEntry->spriteId == 0 && pImpactEntry->spriteName.empty())
    {
        return;
    }

    ProjectileImpactState effect = {};
    effect.effectId = m_nextProjectileImpactId++;
    effect.objectDescriptionId = projectile.impactObjectDescriptionId;
    effect.objectSpriteId = pImpactEntry->spriteId;
    effect.objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        pImpactEntry->spriteId,
        pImpactEntry->spriteName);
    effect.objectName = pImpactEntry->internalName;
    effect.objectSpriteName = pImpactEntry->spriteName;
    effect.x = x;
    effect.y = y;
    effect.z = z;
    effect.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pImpactEntry->lifetimeTicks, 32));
    m_projectileImpacts.push_back(std::move(effect));
    logProjectileImpactEffect(projectile, m_projectileImpacts.back());
}

bool OutdoorWorldRuntime::projectileSourceIsFriendlyToActor(
    const ProjectileState &projectile,
    const MapActorState &actor) const
{
    if (m_pMonsterTable == nullptr || projectile.sourceId == EventSpellSourceId || projectile.sourceMonsterId == 0)
    {
        return false;
    }

    return m_pMonsterTable->getRelationBetweenMonsters(projectile.sourceMonsterId, actor.monsterId) <= 0;
}

void OutdoorWorldRuntime::buildOutdoorFaceSpatialIndex()
{
    m_outdoorFaceGridCells.clear();
    m_outdoorFaceGridMinX = 0.0f;
    m_outdoorFaceGridMinY = 0.0f;
    m_outdoorFaceGridWidth = 0;
    m_outdoorFaceGridHeight = 0;

    if (m_outdoorFaces.empty())
    {
        return;
    }

    float minX = m_outdoorFaces.front().minX;
    float maxX = m_outdoorFaces.front().maxX;
    float minY = m_outdoorFaces.front().minY;
    float maxY = m_outdoorFaces.front().maxY;

    for (const OutdoorFaceGeometryData &face : m_outdoorFaces)
    {
        minX = std::min(minX, face.minX);
        maxX = std::max(maxX, face.maxX);
        minY = std::min(minY, face.minY);
        maxY = std::max(maxY, face.maxY);
    }

    m_outdoorFaceGridMinX = minX;
    m_outdoorFaceGridMinY = minY;
    m_outdoorFaceGridWidth = std::max<size_t>(
        1,
        static_cast<size_t>(std::floor((maxX - minX) / OutdoorFaceSpatialCellSize)) + 1);
    m_outdoorFaceGridHeight = std::max<size_t>(
        1,
        static_cast<size_t>(std::floor((maxY - minY) / OutdoorFaceSpatialCellSize)) + 1);
    m_outdoorFaceGridCells.assign(m_outdoorFaceGridWidth * m_outdoorFaceGridHeight, {});

    for (size_t faceIndex = 0; faceIndex < m_outdoorFaces.size(); ++faceIndex)
    {
        const OutdoorFaceGeometryData &face = m_outdoorFaces[faceIndex];
        const size_t minCellX = std::min(
            m_outdoorFaceGridWidth - 1,
            static_cast<size_t>(std::floor((face.minX - minX) / OutdoorFaceSpatialCellSize)));
        const size_t maxCellX = std::min(
            m_outdoorFaceGridWidth - 1,
            static_cast<size_t>(std::floor((face.maxX - minX) / OutdoorFaceSpatialCellSize)));
        const size_t minCellY = std::min(
            m_outdoorFaceGridHeight - 1,
            static_cast<size_t>(std::floor((face.minY - minY) / OutdoorFaceSpatialCellSize)));
        const size_t maxCellY = std::min(
            m_outdoorFaceGridHeight - 1,
            static_cast<size_t>(std::floor((face.maxY - minY) / OutdoorFaceSpatialCellSize)));

        for (size_t cellY = minCellY; cellY <= maxCellY; ++cellY)
        {
            for (size_t cellX = minCellX; cellX <= maxCellX; ++cellX)
            {
                m_outdoorFaceGridCells[cellY * m_outdoorFaceGridWidth + cellX].push_back(faceIndex);
            }
        }
    }
}

void OutdoorWorldRuntime::collectOutdoorFaceCandidates(
    float minX,
    float minY,
    float maxX,
    float maxY,
    std::vector<size_t> &indices) const
{
    indices.clear();

    if (m_outdoorFaceGridCells.empty() || m_outdoorFaceGridWidth == 0 || m_outdoorFaceGridHeight == 0)
    {
        indices.reserve(m_outdoorFaces.size());

        for (size_t faceIndex = 0; faceIndex < m_outdoorFaces.size(); ++faceIndex)
        {
            indices.push_back(faceIndex);
        }

        return;
    }

    const float clampedMinX = std::max(minX, m_outdoorFaceGridMinX);
    const float clampedMinY = std::max(minY, m_outdoorFaceGridMinY);
    const float clampedMaxX = std::max(maxX, m_outdoorFaceGridMinX);
    const float clampedMaxY = std::max(maxY, m_outdoorFaceGridMinY);
    const size_t minCellX = std::min(
        m_outdoorFaceGridWidth - 1,
        static_cast<size_t>(std::floor((clampedMinX - m_outdoorFaceGridMinX) / OutdoorFaceSpatialCellSize)));
    const size_t maxCellX = std::min(
        m_outdoorFaceGridWidth - 1,
        static_cast<size_t>(std::floor((clampedMaxX - m_outdoorFaceGridMinX) / OutdoorFaceSpatialCellSize)));
    const size_t minCellY = std::min(
        m_outdoorFaceGridHeight - 1,
        static_cast<size_t>(std::floor((clampedMinY - m_outdoorFaceGridMinY) / OutdoorFaceSpatialCellSize)));
    const size_t maxCellY = std::min(
        m_outdoorFaceGridHeight - 1,
        static_cast<size_t>(std::floor((clampedMaxY - m_outdoorFaceGridMinY) / OutdoorFaceSpatialCellSize)));
    std::vector<bool> visitedFaces(m_outdoorFaces.size(), false);

    for (size_t cellY = minCellY; cellY <= maxCellY; ++cellY)
    {
        for (size_t cellX = minCellX; cellX <= maxCellX; ++cellX)
        {
            const std::vector<size_t> &cellFaces = m_outdoorFaceGridCells[cellY * m_outdoorFaceGridWidth + cellX];

            for (size_t faceIndex : cellFaces)
            {
                if (faceIndex >= visitedFaces.size() || visitedFaces[faceIndex])
                {
                    continue;
                }

                visitedFaces[faceIndex] = true;
                indices.push_back(faceIndex);
            }
        }
    }
}

bool OutdoorWorldRuntime::hasClearOutdoorLineOfSight(const bx::Vec3 &start, const bx::Vec3 &end) const
{
    if (m_outdoorFaces.empty())
    {
        return true;
    }

    constexpr float FaceCollisionPadding = 16.0f;
    constexpr float EdgeFactorEpsilon = 0.01f;
    std::vector<size_t> candidateFaceIndices;
    collectOutdoorFaceCandidates(
        std::min(start.x, end.x) - FaceCollisionPadding,
        std::min(start.y, end.y) - FaceCollisionPadding,
        std::max(start.x, end.x) + FaceCollisionPadding,
        std::max(start.y, end.y) + FaceCollisionPadding,
        candidateFaceIndices);

    for (size_t faceIndex : candidateFaceIndices)
    {
        if (faceIndex >= m_outdoorFaces.size())
        {
            continue;
        }

        const OutdoorFaceGeometryData &face = m_outdoorFaces[faceIndex];

        if (!face.hasPlane || face.isWalkable)
        {
            continue;
        }

        if (!segmentMayTouchFaceBounds(start, end, face, FaceCollisionPadding))
        {
            continue;
        }

        float factor = 0.0f;
        bx::Vec3 point = {0.0f, 0.0f, 0.0f};

        if (intersectOutdoorSegmentWithFace(face, start, end, factor, point)
            && factor > EdgeFactorEpsilon
            && factor < 1.0f - EdgeFactorEpsilon)
        {
            return false;
        }
    }

    return true;
}

void OutdoorWorldRuntime::updateProjectiles(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    const uint32_t deltaTicks =
        std::max<uint32_t>(1, static_cast<uint32_t>(std::lround(deltaSeconds * TicksPerSecond)));

    for (ProjectileImpactState &effect : m_projectileImpacts)
    {
        effect.timeSinceCreatedTicks += deltaTicks;

        if (effect.timeSinceCreatedTicks >= effect.lifetimeTicks)
        {
            effect.isExpired = true;
        }
    }

    std::vector<size_t> candidateFaceIndices;

    for (ProjectileState &projectile : m_projectiles)
    {
        if (projectile.isExpired)
        {
            continue;
        }

        projectile.timeSinceCreatedTicks += deltaTicks;

        if (projectile.timeSinceCreatedTicks >= projectile.lifetimeTicks)
        {
            logProjectileLifetimeExpiry(projectile);
            projectile.isExpired = true;
            continue;
        }

        const bx::Vec3 segmentStart = {projectile.x, projectile.y, projectile.z};
        const bx::Vec3 segmentEnd = {
            projectile.x + projectile.velocityX * deltaSeconds,
            projectile.y + projectile.velocityY * deltaSeconds,
            projectile.z + projectile.velocityZ * deltaSeconds
        };
        float bestFactor = 2.0f;
        bx::Vec3 bestPoint = segmentEnd;
        const char *pBestColliderKind = nullptr;
        std::string bestColliderName;
        size_t bestActorIndex = static_cast<size_t>(-1);

        auto considerImpact = [&](float factor, const bx::Vec3 &point, const char *pColliderKind, std::string colliderName)
        {
            if (factor < 0.0f || factor > 1.0f)
            {
                return;
            }

            if (factor < bestFactor)
            {
                bestFactor = factor;
                bestPoint = point;
                pBestColliderKind = pColliderKind;
                bestColliderName = std::move(colliderName);
            }
        };

        {
            float projectionFactor = 0.0f;
            const float distanceSquared = pointSegmentDistanceSquared2d(
                partyX,
                partyY,
                segmentStart.x,
                segmentStart.y,
                segmentEnd.x,
                segmentEnd.y,
                projectionFactor);
            const float collisionRadius = PartyCollisionRadius + static_cast<float>(std::max<uint16_t>(projectile.radius, 8));

            if (distanceSquared <= collisionRadius * collisionRadius)
            {
                const float collisionZ = segmentStart.z + (segmentEnd.z - segmentStart.z) * projectionFactor;
                const float partyMinZ = partyZ;
                const float partyMaxZ = partyZ + PartyCollisionHeight;

                if (collisionZ >= partyMinZ - static_cast<float>(projectile.height)
                    && collisionZ <= partyMaxZ + static_cast<float>(projectile.height))
                {
                    considerImpact(
                        projectionFactor,
                        {segmentStart.x + (segmentEnd.x - segmentStart.x) * projectionFactor,
                            segmentStart.y + (segmentEnd.y - segmentStart.y) * projectionFactor,
                            collisionZ},
                        "party",
                        "party");
                }
            }
        }

        for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
        {
            const MapActorState &actor = m_mapActors[actorIndex];

            if (isActorUnavailableForCombat(actor) || actor.actorId == projectile.sourceId)
            {
                continue;
            }

            if (projectileSourceIsFriendlyToActor(projectile, actor))
            {
                continue;
            }

            float projectionFactor = 0.0f;
            const float distanceSquared = pointSegmentDistanceSquared2d(
                actor.preciseX,
                actor.preciseY,
                segmentStart.x,
                segmentStart.y,
                segmentEnd.x,
                segmentEnd.y,
                projectionFactor);
            const float collisionRadius =
                static_cast<float>(std::max<uint16_t>(actor.radius, 8))
                + static_cast<float>(std::max<uint16_t>(projectile.radius, 8));

            if (distanceSquared > collisionRadius * collisionRadius)
            {
                continue;
            }

            const float collisionZ = segmentStart.z + (segmentEnd.z - segmentStart.z) * projectionFactor;

            if (collisionZ >= actor.preciseZ - static_cast<float>(projectile.height)
                && collisionZ <= actor.preciseZ + static_cast<float>(actor.height) + static_cast<float>(projectile.height))
            {
                std::ostringstream colliderNameStream;
                colliderNameStream << actor.displayName << " #" << actor.actorId;

                if (projectionFactor < bestFactor)
                {
                    bestActorIndex = actorIndex;
                }

                considerImpact(
                    projectionFactor,
                    {segmentStart.x + (segmentEnd.x - segmentStart.x) * projectionFactor,
                        segmentStart.y + (segmentEnd.y - segmentStart.y) * projectionFactor,
                        collisionZ},
                    "actor",
                    colliderNameStream.str());
            }
        }

        const float faceCollisionPadding =
            static_cast<float>(std::max<uint16_t>(projectile.radius, projectile.height)) + 16.0f;

        collectOutdoorFaceCandidates(
            std::min(segmentStart.x, segmentEnd.x) - faceCollisionPadding,
            std::min(segmentStart.y, segmentEnd.y) - faceCollisionPadding,
            std::max(segmentStart.x, segmentEnd.x) + faceCollisionPadding,
            std::max(segmentStart.y, segmentEnd.y) + faceCollisionPadding,
            candidateFaceIndices);

        for (size_t faceIndex : candidateFaceIndices)
        {
            if (faceIndex >= m_outdoorFaces.size())
            {
                continue;
            }

            const OutdoorFaceGeometryData &face = m_outdoorFaces[faceIndex];

            if (!segmentMayTouchFaceBounds(segmentStart, segmentEnd, face, faceCollisionPadding))
            {
                continue;
            }

            float factor = 0.0f;
            bx::Vec3 point = {0.0f, 0.0f, 0.0f};

            if (intersectOutdoorSegmentWithFace(face, segmentStart, segmentEnd, factor, point))
            {
                std::ostringstream colliderNameStream;
                colliderNameStream << face.modelName << " face=" << face.faceIndex;
                considerImpact(factor, point, "bmodel", colliderNameStream.str());
            }
        }

        if (m_pOutdoorMapData != nullptr)
        {
            const float terrainZ = sampleOutdoorTerrainHeight(*m_pOutdoorMapData, segmentEnd.x, segmentEnd.y);

            if (segmentEnd.z <= terrainZ)
            {
                float factor = 1.0f;

                if (std::abs(segmentEnd.z - segmentStart.z) > 0.01f)
                {
                    factor = std::clamp(
                        (terrainZ - segmentStart.z) / (segmentEnd.z - segmentStart.z),
                        0.0f,
                        1.0f);
                }

                considerImpact(
                    factor,
                    {segmentStart.x + (segmentEnd.x - segmentStart.x) * factor,
                        segmentStart.y + (segmentEnd.y - segmentStart.y) * factor,
                        terrainZ},
                    "terrain",
                    "terrain");
            }
        }

        if (bestFactor <= 1.0f)
        {
            const bool directPartyImpact =
                pBestColliderKind != nullptr && std::strcmp(pBestColliderKind, "party") == 0;

            if (directPartyImpact)
            {
                CombatEvent event = {};
                event.type = CombatEvent::Type::PartyProjectileImpact;
                event.sourceId = projectile.sourceId;
                event.fromSummonedMonster = projectile.fromSummonedMonster;
                event.ability = projectile.ability;
                event.damage = resolveProjectilePartyImpactDamage(projectile, m_pMonsterTable, m_mapActors);
                event.spellId = projectile.spellId;
                m_pendingCombatEvents.push_back(std::move(event));
            }
            else if (pBestColliderKind != nullptr && std::strcmp(pBestColliderKind, "actor") == 0)
            {
                if (bestActorIndex < m_mapActors.size())
                {
                    applyMonsterAttackToMapActor(
                        bestActorIndex,
                        resolveProjectilePartyImpactDamage(projectile, m_pMonsterTable, m_mapActors),
                        projectile.sourceId);
                }
            }

            const float impactRadius = spellImpactDamageRadius(projectile.spellId);

            if (!directPartyImpact && isPartyWithinImpactRadius(bestPoint, impactRadius, partyX, partyY, partyZ))
            {
                CombatEvent event = {};
                event.type = CombatEvent::Type::PartyProjectileImpact;
                event.sourceId = projectile.sourceId;
                event.fromSummonedMonster = projectile.fromSummonedMonster;
                event.ability = projectile.ability;
                event.damage = resolveProjectilePartyImpactDamage(projectile, m_pMonsterTable, m_mapActors);
                event.spellId = projectile.spellId;
                m_pendingCombatEvents.push_back(std::move(event));
                logProjectileAoeHit(projectile, "party", bestPoint, impactRadius);
            }

            logProjectileCollision(
                projectile,
                pBestColliderKind != nullptr ? pBestColliderKind : "unknown",
                bestColliderName,
                bestPoint);
            spawnProjectileImpact(projectile, bestPoint.x, bestPoint.y, bestPoint.z);
            projectile.isExpired = true;
            continue;
        }

        projectile.x = segmentEnd.x;
        projectile.y = segmentEnd.y;
        projectile.z = segmentEnd.z;
    }

    std::erase_if(
        m_projectiles,
        [](const ProjectileState &projectile)
        {
            return projectile.isExpired;
        });
    std::erase_if(
        m_projectileImpacts,
        [](const ProjectileImpactState &effect)
        {
            return effect.isExpired;
        });
}

void OutdoorWorldRuntime::applyEventRuntimeState()
{
    if (!m_eventRuntimeState)
    {
        return;
    }

    for (auto &[actorId, setMask] : m_eventRuntimeState->actorSetMasks)
    {
        if (actorId < m_mapActors.size() && (setMask & ActorInvisibleBit) != 0)
        {
            m_mapActors[actorId].isInvisible = true;
        }
    }

    for (auto &[actorId, clearMask] : m_eventRuntimeState->actorClearMasks)
    {
        if (actorId < m_mapActors.size() && (clearMask & ActorInvisibleBit) != 0)
        {
            m_mapActors[actorId].isInvisible = false;
        }
    }

    for (auto &[groupId, setMask] : m_eventRuntimeState->actorGroupSetMasks)
    {
        if ((setMask & ActorInvisibleBit) == 0)
        {
            continue;
        }

        for (MapActorState &actor : m_mapActors)
        {
            if (actor.group == groupId)
            {
                actor.isInvisible = true;
            }
        }

    }

    for (auto &[groupId, clearMask] : m_eventRuntimeState->actorGroupClearMasks)
    {
        if ((clearMask & ActorInvisibleBit) == 0)
        {
            continue;
        }

        for (MapActorState &actor : m_mapActors)
        {
            if (actor.group == groupId)
            {
                actor.isInvisible = false;
            }
        }

    }

    for (uint32_t chestId : m_eventRuntimeState->openedChestIds)
    {
        if (chestId < m_openedChests.size())
        {
            m_openedChests[chestId] = true;
            activateChestView(chestId);
        }
    }
}

bool OutdoorWorldRuntime::updateTimers(
    float deltaSeconds,
    const EventRuntime &eventRuntime,
    const std::optional<EventIrProgram> &localEventIrProgram,
    const std::optional<EventIrProgram> &globalEventIrProgram
)
{
    if (!m_eventRuntimeState || deltaSeconds <= 0.0f)
    {
        return false;
    }

    if (m_timers.empty())
    {
        appendTimersFromProgram(localEventIrProgram, m_timers);
        appendTimersFromProgram(globalEventIrProgram, m_timers);
    }

    if (m_timers.empty())
    {
        return false;
    }

    const float deltaGameMinutes = deltaSeconds * GameMinutesPerRealSecond;
    m_gameMinutes += deltaGameMinutes;

    bool executedAny = false;

    for (TimerState &timer : m_timers)
    {
        if (timer.hasFired && !timer.repeating)
        {
            continue;
        }

        timer.remainingGameMinutes -= deltaGameMinutes;

        if (timer.remainingGameMinutes > 0.0f)
        {
            continue;
        }

        if (eventRuntime.executeEventById(
                localEventIrProgram,
                globalEventIrProgram,
                timer.eventId,
                *m_eventRuntimeState,
                nullptr,
                this))
        {
            executedAny = true;
            applyEventRuntimeState();
        }

        if (timer.repeating)
        {
            timer.remainingGameMinutes += std::max(0.5f, timer.intervalGameMinutes);
        }
        else
        {
            timer.hasFired = true;
        }
    }

    return executedAny;
}

bool OutdoorWorldRuntime::isChestOpened(uint32_t chestId) const
{
    return chestId < m_openedChests.size() ? m_openedChests[chestId] : false;
}

size_t OutdoorWorldRuntime::mapActorCount() const
{
    return m_mapActors.size();
}

const OutdoorWorldRuntime::MapActorState *OutdoorWorldRuntime::mapActorState(size_t actorIndex) const
{
    if (actorIndex >= m_mapActors.size())
    {
        return nullptr;
    }

    return &m_mapActors[actorIndex];
}

std::optional<OutdoorWorldRuntime::ActorDecisionDebugInfo> OutdoorWorldRuntime::debugActorDecisionInfo(
    size_t actorIndex,
    float partyX,
    float partyY,
    float partyZ
) const
{
    if (actorIndex >= m_mapActors.size() || m_pMonsterTable == nullptr)
    {
        return std::nullopt;
    }

    const MapActorState &actor = m_mapActors[actorIndex];
    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr)
    {
        return std::nullopt;
    }

    ActorDecisionDebugInfo info = {};
    info.actorIndex = actorIndex;
    info.monsterId = actor.monsterId;
    info.hostilityType = actor.hostilityType;
    info.hostileToParty = actor.hostileToParty;
    info.hasDetectedParty = actor.hasDetectedParty;
    info.aiState = actor.aiState;
    info.animation = actor.animation;
    info.idleDecisionSeconds = actor.idleDecisionSeconds;
    info.actionSeconds = actor.actionSeconds;
    info.attackCooldownSeconds = actor.attackCooldownSeconds;
    info.idleDecisionCount = actor.idleDecisionCount;
    info.pursueDecisionCount = actor.pursueDecisionCount;
    info.attackDecisionCount = actor.attackDecisionCount;
    info.monsterAiType = static_cast<int>(pStats->aiType);
    info.movementAllowed = pStats->movementType != MonsterTable::MonsterMovementType::Stationary;

    const int relationToParty = m_pMonsterTable->getRelationToParty(actor.monsterId);
    const float partySenseRange = actor.hostileToParty
        ? HostilityLongRange
        : hostilityRangeForRelation(relationToParty);
    const float deltaPartyX = partyX - actor.preciseX;
    const float deltaPartyY = partyY - actor.preciseY;
    const float distanceToParty = length2d(deltaPartyX, deltaPartyY);
    const float actorTargetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    const float partyTargetZ = partyZ + PartyTargetHeightOffset;
    const float deltaPartyZ = partyTargetZ - actorTargetZ;
    const bool canSenseParty =
        partySenseRange > 0.0f
        && std::abs(deltaPartyX) <= partySenseRange
        && std::abs(deltaPartyY) <= partySenseRange
        && std::abs(deltaPartyZ) <= partySenseRange
        && isWithinRange3d(deltaPartyX, deltaPartyY, deltaPartyZ, partySenseRange);
    const auto hasClearOutdoorLineOfSight =
        [this](const bx::Vec3 &start, const bx::Vec3 &end) -> bool
    {
        return this->hasClearOutdoorLineOfSight(start, end);
    };
    const CombatTargetInfo combatTarget =
        selectCombatTarget(
            actor,
            actorIndex,
            m_mapActors,
            *m_pMonsterTable,
            partyX,
            partyY,
            partyZ,
            hasClearOutdoorLineOfSight);
    const bool hasCombatTarget = combatTarget.kind != CombatTargetKind::None;
    const bool targetIsParty = combatTarget.kind == CombatTargetKind::Party;
    const bool targetIsActor = combatTarget.kind == CombatTargetKind::Actor;
    bool shouldEngageTarget = hasCombatTarget && combatTarget.canSense;

    info.partySenseRange = partySenseRange;
    info.distanceToParty = distanceToParty;
    info.canSenseParty = canSenseParty;
    info.targetKind = targetIsParty
        ? DebugTargetKind::Party
        : targetIsActor ? DebugTargetKind::Actor : DebugTargetKind::None;
    info.targetActorIndex = combatTarget.actorIndex;
    info.relationToTarget = combatTarget.relationToTarget;
    info.targetDistance = combatTarget.distanceToTarget;
    info.targetEdgeDistance = combatTarget.edgeDistance;
    info.targetCanSense = combatTarget.canSense;

    if (targetIsActor && combatTarget.actorIndex < m_mapActors.size())
    {
        info.targetMonsterId = m_mapActors[combatTarget.actorIndex].monsterId;
    }

    if (targetIsActor && actor.hostilityType == 0)
    {
        info.promotionRange = hostilityPromotionRangeForFriendlyActor(combatTarget.relationToTarget);
        info.shouldPromoteHostility =
            combatTarget.relationToTarget == 1
            || targetDistanceSquared(combatTarget) <= info.promotionRange * info.promotionRange;

        if (!info.shouldPromoteHostility)
        {
            shouldEngageTarget = false;
        }
    }

    const bool shouldFlee = shouldEngageTarget
        && combatTarget.distanceToTarget <= FleeThresholdRange
        && shouldFleeForAiType(*pStats, actor);
    const bool inMeleeRange = combatTarget.edgeDistance <= meleeRangeForCombatTarget(targetIsActor);
    const bool attackJustCompleted =
        actor.aiState == ActorAiState::Attacking
        && actor.actionSeconds <= 0.0f
        && !actor.attackImpactTriggered;
    const bool attackInProgress =
        actor.aiState == ActorAiState::Attacking
        && actor.actionSeconds > 0.0f;
    const bool partyIsVeryNearActor =
        distanceToParty <= (static_cast<float>(actor.radius) + PartyCollisionRadius + 16.0f)
        && std::abs(partyZ - actor.preciseZ) <= static_cast<float>(std::max<uint16_t>(actor.height, 192));

    info.shouldEngageTarget = shouldEngageTarget;
    info.shouldFlee = shouldFlee;
    info.inMeleeRange = inMeleeRange;
    info.attackJustCompleted = attackJustCompleted;
    info.attackInProgress = attackInProgress;
    info.friendlyNearParty =
        !shouldEngageTarget
        && !actor.hostileToParty
        && partyIsVeryNearActor;
    return info;
}

bool OutdoorWorldRuntime::debugSpawnMapActorProjectile(
    size_t actorIndex,
    MonsterAttackAbility ability,
    float targetX,
    float targetY,
    float targetZ)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    const MapActorState &actor = m_mapActors[actorIndex];

    if (m_pMonsterTable == nullptr)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    return spawnProjectileFromMapActor(actor, *pStats, ability, targetX, targetY, targetZ);
}

bool OutdoorWorldRuntime::debugSpawnEncounterFromSpawnPoint(size_t spawnIndex, uint32_t countOverride)
{
    if (spawnIndex >= m_spawnPoints.size())
    {
        return false;
    }

    const SpawnPointState &spawn = m_spawnPoints[spawnIndex];
    const uint32_t resolvedCount = resolveEncounterSpawnCount(
        m_map,
        spawn.encounterSlot,
        countOverride,
        m_sessionChestSeed,
        static_cast<uint32_t>(spawnIndex));

    return spawnEncounterFromResolvedData(
        spawn.encounterSlot,
        spawn.fixedTier,
        resolvedCount,
        static_cast<float>(-spawn.x),
        static_cast<float>(spawn.y),
        static_cast<float>(spawn.z),
        spawn.radius,
        spawn.attributes,
        spawn.group,
        0,
        true,
        spawnIndex,
        false);
}

bool OutdoorWorldRuntime::setMapActorDead(size_t actorIndex, bool isDead, bool emitAudio)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];
    const bool wasDead = actor.isDead;
    actor.isDead = isDead;
    actor.currentHp = isDead ? 0 : actor.maxHp;
    actor.aiState = isDead ? ActorAiState::Dead : ActorAiState::Standing;
    actor.animation = isDead ? ActorAnimation::Dead : ActorAnimation::Standing;
    actor.animationTimeTicks = 0.0f;
    actor.actionSeconds = 0.0f;

    if (!wasDead && isDead && m_pMonsterTable != nullptr)
    {
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats != nullptr)
        {
            if (actorIndex >= m_mapActorCorpseViews.size())
            {
                m_mapActorCorpseViews.resize(actorIndex + 1);
            }

            if (!m_mapActorCorpseViews[actorIndex].has_value())
            {
                CorpseViewState corpse = buildCorpseView(actor.displayName, pStats->loot, makeChestSeed(
                    m_sessionChestSeed,
                    m_mapId,
                    static_cast<uint32_t>(actorIndex),
                    0x434f5250u));
                corpse.fromSummonedMonster = false;
                corpse.sourceIndex = static_cast<uint32_t>(actorIndex);
                m_mapActorCorpseViews[actorIndex] = std::move(corpse);
            }

            if (emitAudio)
            {
                pushAudioEvent(pStats->deathSoundId, actor.actorId, "monster_death");
            }
        }
    }

    if (wasDead && !isDead && actorIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[actorIndex].reset();
    }

    return true;
}

bool OutdoorWorldRuntime::applyMonsterAttackToMapActor(size_t actorIndex, int damage, uint32_t sourceActorId)
{
    if (actorIndex >= m_mapActors.size() || damage <= 0)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(actor))
    {
        return false;
    }

    const MapActorState *pSourceActor = nullptr;

    for (const MapActorState &candidate : m_mapActors)
    {
        if (candidate.actorId == sourceActorId)
        {
            pSourceActor = &candidate;
            break;
        }
    }

    actor.currentHp = std::max(0, actor.currentHp - damage);

    if (pSourceActor != nullptr)
    {
        faceDirection(actor, pSourceActor->preciseX - actor.preciseX, pSourceActor->preciseY - actor.preciseY);
    }

    if (actor.currentHp <= 0)
    {
        beginDyingState(actor, m_pActorSpriteFrameTable);

        if (m_pMonsterTable != nullptr)
        {
            if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
            {
                pushAudioEvent(pStats->deathSoundId, actor.actorId, "monster_death");
            }
        }

        return true;
    }

    if (canEnterHitReaction(actor))
    {
        beginHitReaction(actor, m_pActorSpriteFrameTable);
    }

    if (m_pMonsterTable != nullptr)
    {
        if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
        {
            pushAudioEvent(pStats->winceSoundId, actor.actorId, "monster_hit");
        }
    }

    return true;
}

bool OutdoorWorldRuntime::spawnEncounterFromResolvedData(
    int encounterSlot,
    char fixedTier,
    uint32_t count,
    float x,
    float y,
    float z,
    uint16_t radius,
    uint16_t attributes,
    uint32_t group,
    uint32_t uniqueNameId,
    bool fromSpawnPoint,
    size_t spawnPointIndex,
    bool aggro)
{
    if (m_pMonsterTable == nullptr || count == 0)
    {
        return false;
    }

    bool spawnedAny = false;

    for (uint32_t spawnOrdinal = 0; spawnOrdinal < count; ++spawnOrdinal)
    {
        const uint32_t tierSeed = m_sessionChestSeed
            ^ static_cast<uint32_t>(encounterSlot * 2654435761u)
            ^ static_cast<uint32_t>((spawnOrdinal + 1u) * 2246822519u)
            ^ static_cast<uint32_t>(group * 3266489917u)
            ^ static_cast<uint32_t>(uniqueNameId * 668265263u)
            ^ static_cast<uint32_t>(spawnPointIndex == static_cast<size_t>(-1) ? 0u : spawnPointIndex + 1u)
            ^ static_cast<uint32_t>(std::lround(x))
            ^ static_cast<uint32_t>(std::lround(y))
            ^ static_cast<uint32_t>(std::lround(z));
        const char resolvedTier = resolveEncounterTierLetter(m_map, encounterSlot, fixedTier, tierSeed);
        const MonsterTable::MonsterStatsEntry *pStats =
            resolveEncounterMonsterStats(m_map, *m_pMonsterTable, encounterSlot, resolvedTier);

        if (pStats == nullptr)
        {
            continue;
        }

        const MonsterEntry *pMonsterEntry =
            resolveMonsterEntry(*m_pMonsterTable, static_cast<int16_t>(pStats->id), pStats);
        const uint16_t actorRadius = pMonsterEntry != nullptr ? std::max<uint16_t>(pMonsterEntry->radius, 32) : 32;
        const bx::Vec3 spawnPosition = calculateEncounterSpawnPosition(
            x,
            y,
            z,
            radius,
            actorRadius,
            spawnOrdinal);
        MapActorState actor = buildSpawnedMapActorState(
            *m_pMonsterTable,
            m_pOutdoorMapData,
            *pStats,
            m_nextActorId++,
            uniqueNameId,
            fromSpawnPoint,
            spawnPointIndex,
            group,
            attributes,
            spawnPosition.x,
            spawnPosition.y,
            spawnPosition.z);

        const auto visualIt = m_monsterVisualsById.find(actor.monsterId);

        if (visualIt != m_monsterVisualsById.end())
        {
            applyMonsterVisualState(actor, visualIt->second);
        }
        else if (m_pActorSpriteFrameTable != nullptr)
        {
            const MonsterVisualState visualState = buildMonsterVisualState(*m_pActorSpriteFrameTable, pMonsterEntry);

            if (visualState.spriteFrameIndex != 0)
            {
                m_monsterVisualsById[actor.monsterId] = visualState;
                applyMonsterVisualState(actor, visualState);
            }
        }

        actor.hostileToParty = actor.hostileToParty || aggro;
        applyTestActorOverrides(m_mapId, m_pOutdoorMapData, pStats, actor.actorId, actor);

        if (m_outdoorMovementController)
        {
            const float collisionRadius = actorCollisionRadius(actor, pStats);
            actor.movementState = m_outdoorMovementController->initializeStateForBody(
                actor.preciseX,
                actor.preciseY,
                actor.preciseZ + GroundSnapHeight,
                collisionRadius);
            actor.movementStateInitialized = true;
            syncActorFromMovementState(actor);
            actor.homePreciseX = actor.preciseX;
            actor.homePreciseY = actor.preciseY;
            actor.homePreciseZ = actor.preciseZ;
            actor.homeX = actor.x;
            actor.homeY = actor.y;
            actor.homeZ = actor.z;
        }

        m_mapActors.push_back(std::move(actor));
        spawnedAny = true;
    }

    if (spawnedAny)
    {
        applyEventRuntimeState();
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::setMapActorHostileToParty(
    size_t actorIndex,
    float partyX,
    float partyY,
    float partyZ,
    bool resetActionState)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(actor))
    {
        return false;
    }

    actor.hostileToParty = true;
    actor.hasDetectedParty = false;
    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);

    if (!resetActionState)
    {
        return true;
    }

    actor.aiState = ActorAiState::Standing;
    actor.animation = ActorAnimation::Standing;
    actor.animationTimeTicks = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.actionSeconds = 0.0f;
    actor.idleDecisionSeconds = 0.0f;
    actor.attackImpactTriggered = false;
    return true;
}

void OutdoorWorldRuntime::aggroNearbyMapActorFaction(size_t actorIndex, float partyX, float partyY, float partyZ)
{
    if (actorIndex >= m_mapActors.size() || m_pMonsterTable == nullptr)
    {
        return;
    }

    const MapActorState &victim = m_mapActors[actorIndex];

    for (size_t otherActorIndex = 0; otherActorIndex < m_mapActors.size(); ++otherActorIndex)
    {
        if (otherActorIndex == actorIndex)
        {
            continue;
        }

        MapActorState &otherActor = m_mapActors[otherActorIndex];

        if (isActorUnavailableForCombat(otherActor))
        {
            continue;
        }

        if (!m_pMonsterTable->isLikelySameFaction(victim.monsterId, otherActor.monsterId))
        {
            continue;
        }

        const float distance = length3d(
            otherActor.preciseX - victim.preciseX,
            otherActor.preciseY - victim.preciseY,
            otherActor.preciseZ - victim.preciseZ);

        if (distance > PeasantAggroRadius)
        {
            continue;
        }

        setMapActorHostileToParty(otherActorIndex, partyX, partyY, partyZ, true);
    }
}

bool OutdoorWorldRuntime::applyPartyAttackToMapActor(
    size_t actorIndex,
    int damage,
    float partyX,
    float partyY,
    float partyZ)
{
    if (actorIndex >= m_mapActors.size() || damage <= 0)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(actor))
    {
        return false;
    }

    actor.currentHp = std::max(0, actor.currentHp - damage);
    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
    setMapActorHostileToParty(actorIndex, partyX, partyY, partyZ, false);

    const bool died = actor.currentHp <= 0;

    if (died)
    {
        beginDyingState(actor, m_pActorSpriteFrameTable);

        if (m_pMonsterTable != nullptr)
        {
            if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
            {
                pushAudioEvent(pStats->deathSoundId, actor.actorId, "monster_death");
            }
        }
    }
    else
    {
        if (canEnterHitReaction(actor))
        {
            faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
            beginHitReaction(actor, m_pActorSpriteFrameTable);
        }

        if (m_pMonsterTable != nullptr)
        {
            if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
            {
                pushAudioEvent(pStats->winceSoundId, actor.actorId, "monster_hit");
            }
        }
    }

    aggroNearbyMapActorFaction(actorIndex, partyX, partyY, partyZ);
    return true;
}

bool OutdoorWorldRuntime::notifyPartyContactWithMapActor(size_t actorIndex, float partyX, float partyY, float partyZ)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(actor) || actor.hostileToParty)
    {
        return false;
    }

    if (std::abs(partyZ - actor.preciseZ) > static_cast<float>(std::max<uint16_t>(actor.height, 192)))
    {
        return false;
    }

    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
    actor.aiState = ActorAiState::Standing;
    actor.animation = ActorAnimation::Standing;
    actor.animationTimeTicks = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.actionSeconds = std::max(actor.actionSeconds, 2.0f);
    actor.idleDecisionSeconds = std::max(actor.idleDecisionSeconds, 2.0f);
    return true;
}

size_t OutdoorWorldRuntime::spawnPointCount() const
{
    return m_spawnPoints.size();
}

const OutdoorWorldRuntime::SpawnPointState *OutdoorWorldRuntime::spawnPointState(size_t spawnIndex) const
{
    if (spawnIndex >= m_spawnPoints.size())
    {
        return nullptr;
    }

    return &m_spawnPoints[spawnIndex];
}

size_t OutdoorWorldRuntime::chestCount() const
{
    return m_openedChests.size();
}

size_t OutdoorWorldRuntime::openedChestCount() const
{
    size_t count = 0;

    for (bool isOpened : m_openedChests)
    {
        if (isOpened)
        {
            ++count;
        }
    }

    return count;
}

const OutdoorWorldRuntime::ChestViewState *OutdoorWorldRuntime::activeChestView() const
{
    if (!m_activeChestView)
    {
        return nullptr;
    }

    return &*m_activeChestView;
}

bool OutdoorWorldRuntime::takeActiveChestItem(size_t itemIndex, ChestItemState &item)
{
    if (!m_activeChestView || itemIndex >= m_activeChestView->items.size())
    {
        return false;
    }

    item = m_activeChestView->items[itemIndex];
    m_activeChestView->items.erase(m_activeChestView->items.begin() + static_cast<ptrdiff_t>(itemIndex));

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

void OutdoorWorldRuntime::closeActiveChestView()
{
    m_activeChestView.reset();
}

const OutdoorWorldRuntime::CorpseViewState *OutdoorWorldRuntime::activeCorpseView() const
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

bool OutdoorWorldRuntime::openMapActorCorpseView(size_t actorIndex)
{
    if (actorIndex >= m_mapActorCorpseViews.size() || !m_mapActorCorpseViews[actorIndex].has_value())
    {
        return false;
    }

    m_activeCorpseView = *m_mapActorCorpseViews[actorIndex];
    return true;
}

bool OutdoorWorldRuntime::takeActiveCorpseItem(size_t itemIndex, ChestItemState &item)
{
    if (!m_activeCorpseView || itemIndex >= m_activeCorpseView->items.size())
    {
        return false;
    }

    item = m_activeCorpseView->items[itemIndex];
    m_activeCorpseView->items.erase(m_activeCorpseView->items.begin() + static_cast<ptrdiff_t>(itemIndex));

    if (m_activeCorpseView->items.empty())
    {
        if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
        {
            m_mapActorCorpseViews[m_activeCorpseView->sourceIndex].reset();
        }

        if (m_activeCorpseView->sourceIndex < m_mapActors.size())
        {
            m_mapActors[m_activeCorpseView->sourceIndex].isInvisible = true;
        }

        m_activeCorpseView.reset();
        return true;
    }

    if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
    }

    return true;
}

void OutdoorWorldRuntime::closeActiveCorpseView()
{
    m_activeCorpseView.reset();
}

const std::vector<OutdoorWorldRuntime::AudioEvent> &OutdoorWorldRuntime::pendingAudioEvents() const
{
    return m_pendingAudioEvents;
}

void OutdoorWorldRuntime::clearPendingAudioEvents()
{
    m_pendingAudioEvents.clear();
}

const std::vector<OutdoorWorldRuntime::CombatEvent> &OutdoorWorldRuntime::pendingCombatEvents() const
{
    return m_pendingCombatEvents;
}

void OutdoorWorldRuntime::clearPendingCombatEvents()
{
    m_pendingCombatEvents.clear();
}

size_t OutdoorWorldRuntime::projectileCount() const
{
    return m_projectiles.size();
}

const OutdoorWorldRuntime::ProjectileState *OutdoorWorldRuntime::projectileState(size_t projectileIndex) const
{
    if (projectileIndex >= m_projectiles.size())
    {
        return nullptr;
    }

    return &m_projectiles[projectileIndex];
}

size_t OutdoorWorldRuntime::projectileImpactCount() const
{
    return m_projectileImpacts.size();
}

const OutdoorWorldRuntime::ProjectileImpactState *OutdoorWorldRuntime::projectileImpactState(size_t effectIndex) const
{
    if (effectIndex >= m_projectileImpacts.size())
    {
        return nullptr;
    }

    return &m_projectileImpacts[effectIndex];
}

bool OutdoorWorldRuntime::summonMonsters(
    uint32_t typeIndexInMapStats,
    uint32_t level,
    uint32_t count,
    int32_t x,
    int32_t y,
    int32_t z,
    uint32_t group,
    uint32_t uniqueNameId
)
{
    if (m_pMonsterTable == nullptr || typeIndexInMapStats < 1 || typeIndexInMapStats > 3 || count == 0)
    {
        return false;
    }

    return spawnEncounterFromResolvedData(
        static_cast<int>(typeIndexInMapStats),
        tierLetterForSummonLevel(level),
        count,
        static_cast<float>(-x),
        static_cast<float>(y),
        static_cast<float>(z),
        128,
        0,
        group,
        uniqueNameId,
        false,
        static_cast<size_t>(-1),
        false);
}

bool OutdoorWorldRuntime::checkMonstersKilled(
    uint32_t checkType,
    uint32_t id,
    uint32_t count,
    bool invisibleAsDead
) const
{
    int totalActors = 0;
    int defeatedActors = 0;

    auto countMonster =
        [&](bool matches, bool isDead, bool isInvisible)
        {
            if (!matches)
            {
                return;
            }

            ++totalActors;

            if (isDead || (invisibleAsDead && isInvisible))
            {
                ++defeatedActors;
            }
        };

    for (const MapActorState &actor : m_mapActors)
    {
        bool matches = false;

        switch (checkType)
        {
            case CheckActorKilledByAny:
                matches = true;
                break;

            case CheckActorKilledByGroup:
                matches = actor.group == id;
                break;

            case CheckActorKilledByMonsterId:
                matches = actor.monsterId == static_cast<int16_t>(id);
                break;

            case CheckActorKilledByActorIdOe:
            case CheckActorKilledByActorIdMm8:
                matches = actor.actorId == id;
                break;

            default:
                break;
        }

        countMonster(matches, actor.isDead || actor.currentHp <= 0, actor.isInvisible);
    }

    if (count > 0)
    {
        return defeatedActors >= static_cast<int>(count);
    }

    return totalActors == defeatedActors;
}

const EventRuntimeState::PendingMapMove *OutdoorWorldRuntime::pendingMapMove() const
{
    if (!m_eventRuntimeState || !m_eventRuntimeState->pendingMapMove)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState->pendingMapMove;
}

std::optional<EventRuntimeState::PendingMapMove> OutdoorWorldRuntime::consumePendingMapMove()
{
    if (!m_eventRuntimeState || !m_eventRuntimeState->pendingMapMove)
    {
        return std::nullopt;
    }

    std::optional<EventRuntimeState::PendingMapMove> result = std::move(m_eventRuntimeState->pendingMapMove);
    m_eventRuntimeState->pendingMapMove.reset();
    return result;
}

EventRuntimeState *OutdoorWorldRuntime::eventRuntimeState()
{
    if (!m_eventRuntimeState)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState;
}

bool OutdoorWorldRuntime::castEventSpell(
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    int32_t fromX,
    int32_t fromY,
    int32_t fromZ,
    int32_t toX,
    int32_t toY,
    int32_t toZ
)
{
    SpellCastRequest request = {};
    request.sourceKind = RuntimeSpellSourceKind::Event;
    request.sourceId = EventSpellSourceId;
    request.ability = MonsterAttackAbility::Spell1;
    request.spellId = spellId;
    request.skillLevel = skillLevel;
    request.skillMastery = skillMastery;
    request.sourceX = static_cast<float>(-fromX);
    request.sourceY = static_cast<float>(fromY);
    request.sourceZ = static_cast<float>(fromZ);
    request.targetX = static_cast<float>(-toX);
    request.targetY = static_cast<float>(toY);
    request.targetZ = static_cast<float>(toZ);
    return castSpell(request);
}

const EventRuntimeState *OutdoorWorldRuntime::eventRuntimeState() const
{
    if (!m_eventRuntimeState)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState;
}
}
