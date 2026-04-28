#include "game/indoor/IndoorWorldRuntime.h"

#include "game/SpriteObjectDefs.h"
#include "game/FaceEnums.h"
#include "game/audio/SoundIds.h"
#include "game/data/ActorNameResolver.h"
#include "game/events/EvtEnums.h"
#include "game/StringUtils.h"
#include "game/gameplay/ChestRuntime.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/TreasureRuntime.h"
#include "game/indoor/IndoorRenderer.h"
#include "game/indoor/IndoorGameView.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/maps/MapAssetLoader.h"
#include "game/party/EventSpellBuffs.h"
#include "game/party/SpellIds.h"
#include "game/tables/SpriteTables.h"
#include "game/tables/MonsterProjectileTable.h"
#include "game/tables/SpellTable.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float SpecialJumpAngleUnitsPerTurn = 2048.0f;
constexpr uint32_t RawContainingItemSize = 0x24;
constexpr float IndoorMinimapWorldHalfExtent = 32768.0f;
constexpr float IndoorMinimapWorldExtent = IndoorMinimapWorldHalfExtent * 2.0f;
constexpr float TicksPerSecond = 128.0f;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr float ActorUpdateStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedActorUpdateSeconds = 0.1f;
constexpr float ProjectileUpdateStepSeconds = 1.0f / 60.0f;
constexpr int MaxProjectileUpdateStepsPerFrame = 4;
constexpr float MaxAccumulatedProjectileUpdateSeconds =
    ProjectileUpdateStepSeconds * static_cast<float>(MaxProjectileUpdateStepsPerFrame);
constexpr float WorldItemUpdateStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedWorldItemUpdateSeconds = 0.1f;
constexpr uint32_t EventSpellSourceId = std::numeric_limits<uint32_t>::max();
constexpr float ActorInertiaVelocityDecay = 0.8392334f;
constexpr float ActorInertiaReferenceFrameRate = 60.0f;
constexpr float ActorStopVelocitySquared = 400.0f;
constexpr float ActorKnockbackVelocityStep = 50.0f;
constexpr int ActorMaxKnockbackSteps = 10;

float actorInertiaDecayForStep(float deltaSeconds)
{
    return std::pow(ActorInertiaVelocityDecay, deltaSeconds * ActorInertiaReferenceFrameRate);
}

float actorDamageKnockbackMagnitude(int damage, int maxHp)
{
    if (damage <= 0 || maxHp <= 0)
    {
        return 0.0f;
    }

    const int knockbackSteps =
        std::min(ActorMaxKnockbackSteps, static_cast<int>((20LL * damage) / maxHp));
    return ActorKnockbackVelocityStep * static_cast<float>(knockbackSteps);
}

bx::Vec3 actorKnockbackVelocityFromMagnitude(
    float actorX,
    float actorY,
    float actorZ,
    float sourceX,
    float sourceY,
    float sourceZ,
    float magnitude)
{
    if (magnitude <= 0.0f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    bx::Vec3 direction = {actorX - sourceX, actorY - sourceY, actorZ - sourceZ};
    const float length = std::sqrt(direction.x * direction.x + direction.y * direction.y + direction.z * direction.z);

    if (length <= 0.001f)
    {
        direction = {1.0f, 0.0f, 0.0f};
    }
    else
    {
        direction.x /= length;
        direction.y /= length;
        direction.z /= length;
    }

    return {direction.x * magnitude, direction.y * magnitude, direction.z * magnitude};
}

bx::Vec3 actorKnockbackVelocity(
    float actorX,
    float actorY,
    float actorZ,
    float sourceX,
    float sourceY,
    float sourceZ,
    int damage,
    int maxHp)
{
    return actorKnockbackVelocityFromMagnitude(
        actorX,
        actorY,
        actorZ,
        sourceX,
        sourceY,
        sourceZ,
        actorDamageKnockbackMagnitude(damage, maxHp));
}

int monsterResistanceForDamageType(
    const MonsterTable::MonsterStatsEntry &stats,
    CombatDamageType damageType)
{
    switch (damageType)
    {
        case CombatDamageType::Fire: return stats.fireResistance;
        case CombatDamageType::Air: return stats.airResistance;
        case CombatDamageType::Water: return stats.waterResistance;
        case CombatDamageType::Earth: return stats.earthResistance;
        case CombatDamageType::Spirit: return stats.spiritResistance;
        case CombatDamageType::Mind: return stats.mindResistance;
        case CombatDamageType::Body: return stats.bodyResistance;
        case CombatDamageType::Light: return stats.lightResistance;
        case CombatDamageType::Dark: return stats.darkResistance;
        case CombatDamageType::Irresistible: return 0;
        case CombatDamageType::Physical:
        default:
            return stats.physicalResistance;
    }
}

std::string formatFoundItemStatusText(const std::string &itemName)
{
    const std::string resolvedItemName = itemName.empty() ? "item" : itemName;
    return "You found an item (" + resolvedItemName + ")!";
}

std::string formatFoundGoldStatusText(int goldAmount)
{
    return "You found " + std::to_string(std::max(0, goldAmount)) + " gold!";
}
constexpr float ActiveActorUpdateRange = 10240.0f;
constexpr float IndoorActorDetectRange = 5120.0f;
constexpr int IndoorActorDetectPortalLimit = 30;
constexpr float IndoorFactionAggroRange = 4096.0f;
constexpr size_t MaxIndoorBloodSplats = 64;

int16_t legacyEventMonsterIdToStatsId(uint32_t eventMonsterId)
{
    if (eventMonsterId >= static_cast<uint32_t>(std::numeric_limits<int16_t>::max()))
    {
        return 0;
    }

    return static_cast<int16_t>(eventMonsterId + 1u);
}
constexpr size_t BloodSplatGridResolution = 10;
constexpr float BloodSplatHeightOffset = 2.0f;
constexpr float BloodSplatMinSurfaceHeightTolerance = 32.0f;

void resetIndoorActorCrowdSteeringState(IndoorWorldRuntime::MapActorAiState &aiState)
{
    aiState.crowdSideLockRemainingSeconds = 0.0f;
    aiState.crowdNoProgressSeconds = 0.0f;
    aiState.crowdLastEdgeDistance = 0.0f;
    aiState.crowdRetreatRemainingSeconds = 0.0f;
    aiState.crowdStandRemainingSeconds = 0.0f;
    aiState.crowdProbeEdgeDistance = 0.0f;
    aiState.crowdProbeElapsedSeconds = 0.0f;
    aiState.crowdEscapeAttempts = 0;
    aiState.crowdSideSign = 0;
}

constexpr size_t MaxActiveActorUpdates = 48;
constexpr float HostilityLongRange = 10240.0f;
constexpr float ActorMeleeRange = 307.2f;
constexpr float IndoorActorContactProbeRadius = 40.0f;
constexpr float IndoorActorVsActorMovementRadius = 10.0f;
constexpr float PartyCollisionRadius = 37.0f;
constexpr float PartyCollisionHeight = 192.0f;
constexpr uint16_t LevelDecorationVisibleOnMap = 0x0008;
constexpr uint16_t LevelDecorationInvisible = 0x0020;
constexpr float PartyTargetHeightOffset = 96.0f;
constexpr float IndoorFloorSampleRise = 96.0f;
constexpr float IndoorFloorSampleDrop = 512.0f;
constexpr float IndoorInitialActorFloorSampleRise = 4096.0f;

int16_t resolveIndoorPointSector(
    const IndoorMapData *pMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache *pGeometryCache,
    const bx::Vec3 &point,
    int16_t fallbackSectorId)
{
    if (pMapData == nullptr || vertices.empty())
    {
        return fallbackSectorId;
    }

    return findIndoorSectorForPoint(
        *pMapData,
        vertices,
        point,
        pGeometryCache,
        false).value_or(fallbackSectorId);
}

bool indoorPointInsideSectorBounds(
    const IndoorMapData &mapData,
    const GameplayWorldPoint &point,
    int16_t sectorId,
    float slack)
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= mapData.sectors.size())
    {
        return false;
    }

    const IndoorSector &sector = mapData.sectors[sectorId];
    return point.x >= static_cast<float>(sector.minX) - slack
        && point.x <= static_cast<float>(sector.maxX) + slack
        && point.y >= static_cast<float>(sector.minY) - slack
        && point.y <= static_cast<float>(sector.maxY) + slack
        && point.z >= static_cast<float>(sector.minZ) - slack
        && point.z <= static_cast<float>(sector.maxZ) + slack;
}

constexpr float IndoorInitialActorFloorSampleDrop = 4096.0f;
constexpr float IndoorWorldItemThrowPitchRadians = Pi * 2.0f * (184.0f / 2048.0f);
constexpr float IndoorWorldItemThrowSpeed = 200.0f;
constexpr float IndoorWorldItemGravity = 900.0f;
constexpr float IndoorProjectileGravity = IndoorWorldItemGravity;
constexpr float IndoorWorldItemBounceFactor = 0.5f;
constexpr float IndoorWorldItemGroundDamping = 0.89263916f;
constexpr float IndoorWorldItemRestingHorizontalSpeedSquared = 400.0f;
constexpr float IndoorWorldItemBounceStopVelocity = 10.0f;
constexpr float IndoorWorldItemGroundClearance = 1.0f;
constexpr float IndoorWorldItemFloorSampleRise = 128.0f;
constexpr float IndoorWorldItemFloorSampleDrop = 512.0f;

float indoorWorldHitDistance(const GameplayWorldHit &hit)
{
    if (hit.actor)
    {
        return hit.actor->distance;
    }

    if (hit.worldItem)
    {
        return hit.worldItem->distance;
    }

    if (hit.container)
    {
        return hit.container->distance;
    }

    if (hit.eventTarget)
    {
        return hit.eventTarget->distance;
    }

    if (hit.object)
    {
        return hit.object->distance;
    }

    if (hit.ground)
    {
        return hit.ground->distance;
    }

    return std::numeric_limits<float>::max();
}

int16_t clampToInt16(float value)
{
    return static_cast<int16_t>(
        std::clamp(
            std::lround(value),
            static_cast<long>(std::numeric_limits<int16_t>::min()),
            static_cast<long>(std::numeric_limits<int16_t>::max())));
}

float length3d(const bx::Vec3 &value)
{
    return std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
}

bool indoorProjectileDebugEnabled()
{
    static const bool enabled =
        []()
        {
            const char *pValue = std::getenv("OPENYAMM_INDOOR_PROJECTILE_DEBUG");
            return pValue != nullptr && pValue[0] != '\0' && std::strcmp(pValue, "0") != 0;
        }();
    return enabled;
}

const char *indoorProjectileCollisionKindName(GameplayProjectileService::ProjectileFrameCollisionKind kind)
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

const char *indoorProjectileSpawnKindName(GameplayProjectileService::ProjectileSpawnResult::Kind kind)
{
    switch (kind)
    {
        case GameplayProjectileService::ProjectileSpawnResult::Kind::FailedZeroDistance:
            return "failed_zero_distance";

        case GameplayProjectileService::ProjectileSpawnResult::Kind::SpawnedProjectile:
            return "spawned_projectile";

        case GameplayProjectileService::ProjectileSpawnResult::Kind::InstantImpact:
            return "instant_impact";
    }

    return "unknown";
}

constexpr float IndoorProjectileBounceFactor = IndoorWorldItemBounceFactor;
constexpr float IndoorProjectileBounceStopVelocity = IndoorWorldItemBounceStopVelocity;
constexpr float IndoorProjectileGroundDamping = IndoorWorldItemGroundDamping;
constexpr float IndoorProjectileSettledHorizontalSpeedSquared = IndoorWorldItemRestingHorizontalSpeedSquared;
constexpr std::array<std::array<int, 3>, 4> IndoorEncounterDifficultyTierWeights = {{
    {60, 30, 10},
    {30, 50, 20},
    {10, 40, 50},
    {0, 25, 75}
}};

bool indoorProjectileShouldSettle(const GameplayProjectileService::ProjectileState &projectile)
{
    if ((projectile.objectFlags & ObjectDescBounce) == 0)
    {
        return false;
    }

    const float horizontalSpeedSquared =
        projectile.velocityX * projectile.velocityX + projectile.velocityY * projectile.velocityY;
    return projectile.velocityZ == 0.0f && horizontalSpeedSquared <= IndoorProjectileSettledHorizontalSpeedSquared;
}

struct IndoorResolvedProjectileDefinition
{
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t impactObjectDescriptionId = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    int spellId = 0;
    int effectSoundId = 0;
    uint32_t lifetimeTicks = 0;
    float speed = 0.0f;
    std::string objectName;
    std::string objectSpriteName;
};

struct IndoorProjectileCollisionCandidate
{
    GameplayProjectileService::ProjectileFrameCollisionKind kind =
        GameplayProjectileService::ProjectileFrameCollisionKind::None;
    GameplayWorldPoint point = {};
    size_t actorIndex = static_cast<size_t>(-1);
    size_t faceIndex = static_cast<size_t>(-1);
    float normalX = 0.0f;
    float normalY = 0.0f;
    float normalZ = 1.0f;
    bool requiresDownwardVelocityToBounce = false;
    float progress = std::numeric_limits<float>::max();
    float distanceSquared = std::numeric_limits<float>::max();
};

struct IndoorEncounterSpawnDescriptor
{
    int encounterSlot = 0;
    char fixedTier = '\0';
};

struct IndoorResolvedSpawnPosition
{
    bx::Vec3 position = {0.0f, 0.0f, 0.0f};
    int16_t sectorId = -1;
};

const MapEncounterInfo *getIndoorEncounterInfo(const MapStatsEntry &map, int encounterSlot)
{
    switch (encounterSlot)
    {
        case 1:
            return &map.encounter1;
        case 2:
            return &map.encounter2;
        case 3:
            return &map.encounter3;
        default:
            return nullptr;
    }
}

IndoorEncounterSpawnDescriptor resolveIndoorEncounterSpawnDescriptor(uint16_t index)
{
    IndoorEncounterSpawnDescriptor descriptor = {};

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

char resolveIndoorEncounterTierLetter(
    const MapStatsEntry &map,
    int encounterSlot,
    char fixedTier,
    uint32_t seed)
{
    if (fixedTier != '\0')
    {
        return fixedTier;
    }

    const MapEncounterInfo *pEncounter = getIndoorEncounterInfo(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return 'A';
    }

    const int difficulty = std::clamp(pEncounter->difficulty, 0, 3);
    const std::array<int, 3> &weights = IndoorEncounterDifficultyTierWeights[difficulty];
    const int totalWeight = std::max(1, weights[0] + weights[1] + weights[2]);
    std::mt19937 rng(seed);
    const int roll = std::uniform_int_distribution<int>(0, totalWeight - 1)(rng);

    if (roll < weights[0])
    {
        return 'A';
    }

    if (roll < weights[0] + weights[1])
    {
        return 'B';
    }

    return 'C';
}

uint32_t resolveIndoorEncounterSpawnCount(
    const MapStatsEntry &map,
    int encounterSlot,
    uint32_t sessionSeed,
    uint32_t salt)
{
    const MapEncounterInfo *pEncounter = getIndoorEncounterInfo(map, encounterSlot);

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

IndoorResolvedSpawnPosition resolveIndoorEncounterSpawnPosition(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    const IndoorSpawn &spawn,
    uint32_t spawnIndex,
    uint32_t spawnOrdinal,
    uint32_t sessionSeed)
{
    constexpr float OeIndoorSpawnOffsetRadius = 64.0f;
    constexpr float SpawnFloorHeightSlack = 1024.0f;
    constexpr uint32_t MaxSpawnPositionAttempts = 100;
    const bx::Vec3 center = {
        static_cast<float>(spawn.x),
        static_cast<float>(spawn.y),
        static_cast<float>(spawn.z)
    };
    int16_t spawnSectorId =
        findIndoorSectorForPoint(indoorMapData, vertices, center, &geometryCache, false).value_or(-1);

    if (spawnSectorId < 0)
    {
        const IndoorFloorSample centerFloorSample =
            sampleIndoorFloor(
                indoorMapData,
                vertices,
                center.x,
                center.y,
                center.z,
                IndoorFloorSampleRise,
                IndoorFloorSampleDrop,
                std::nullopt,
                nullptr,
                &geometryCache);

        if (centerFloorSample.hasFloor)
        {
            spawnSectorId = centerFloorSample.sectorId;
        }
    }

    IndoorResolvedSpawnPosition fallback = {};
    fallback.position = center;
    fallback.sectorId = spawnSectorId;

    const auto resolveCandidate =
        [&](float x, float y, float z) -> std::optional<IndoorResolvedSpawnPosition>
        {
            const bx::Vec3 point = {x, y, z};
            const int16_t pointSectorId =
                findIndoorSectorForPoint(indoorMapData, vertices, point, &geometryCache, false).value_or(-1);

            if (spawnSectorId >= 0 && pointSectorId != spawnSectorId)
            {
                return std::nullopt;
            }

            const IndoorFloorSample floorSample =
                sampleIndoorFloor(
                    indoorMapData,
                    vertices,
                    x,
                    y,
                    z,
                    IndoorFloorSampleRise,
                    IndoorFloorSampleDrop,
                    spawnSectorId >= 0 ? std::optional<int16_t>(spawnSectorId) : std::nullopt,
                    nullptr,
                    &geometryCache);

            if (!floorSample.hasFloor)
            {
                return std::nullopt;
            }

            if (spawnSectorId >= 0 && floorSample.sectorId != spawnSectorId)
            {
                return std::nullopt;
            }

            if (std::abs(floorSample.height - static_cast<float>(spawn.z)) > SpawnFloorHeightSlack)
            {
                return std::nullopt;
            }

            IndoorResolvedSpawnPosition result = {};
            result.position = {x, y, floorSample.height};
            result.sectorId = floorSample.sectorId;
            return result;
        };

    if (const std::optional<IndoorResolvedSpawnPosition> centerPosition =
            resolveCandidate(center.x, center.y, center.z))
    {
        fallback = *centerPosition;

        if (spawnOrdinal == 0)
        {
            return fallback;
        }
    }

    std::mt19937 rng(
        sessionSeed
        ^ static_cast<uint32_t>((spawnIndex + 1u) * 2654435761u)
        ^ static_cast<uint32_t>((spawnOrdinal + 1u) * 2246822519u)
        ^ static_cast<uint32_t>(spawn.x)
        ^ static_cast<uint32_t>(spawn.y)
        ^ static_cast<uint32_t>(spawn.z));
    std::uniform_real_distribution<float> angleDistribution(0.0f, 2.0f * Pi);
    std::uniform_real_distribution<float> radiusDistribution(0.0f, OeIndoorSpawnOffsetRadius);

    for (uint32_t attempt = 0; attempt < MaxSpawnPositionAttempts; ++attempt)
    {
        const float angle = angleDistribution(rng);
        const float radius = radiusDistribution(rng);
        const float candidateX = center.x + std::cos(angle) * radius;
        const float candidateY = center.y + std::sin(angle) * radius;

        if (const std::optional<IndoorResolvedSpawnPosition> candidate =
                resolveCandidate(candidateX, candidateY, center.z))
        {
            return *candidate;
        }
    }

    return fallback;
}

bool shouldMaterializeIndoorSpawnsOnInitialize(const std::optional<MapDeltaData> *pMapDeltaData)
{
    return pMapDeltaData != nullptr
        && pMapDeltaData->has_value()
        && (*pMapDeltaData)->locationInfo.lastRespawnDay == 0;
}

float indoorMinimapU(float x)
{
    return std::clamp((x + IndoorMinimapWorldHalfExtent) / IndoorMinimapWorldExtent, 0.0f, 1.0f);
}

float indoorMinimapRawU(float x)
{
    return (x + IndoorMinimapWorldHalfExtent) / IndoorMinimapWorldExtent;
}

float indoorMinimapV(float y)
{
    return std::clamp((IndoorMinimapWorldHalfExtent - y) / IndoorMinimapWorldExtent, 0.0f, 1.0f);
}

float indoorMinimapRawV(float y)
{
    return (IndoorMinimapWorldHalfExtent - y) / IndoorMinimapWorldExtent;
}

bool packedIndoorOutlineBit(const std::vector<uint8_t> &bits, size_t outlineIndex)
{
    const size_t byteIndex = outlineIndex / 8;

    if (byteIndex >= bits.size())
    {
        return false;
    }

    return (bits[byteIndex] & (1u << (7u - outlineIndex % 8))) != 0;
}

void setPackedIndoorOutlineBit(std::vector<uint8_t> &bits, size_t outlineIndex)
{
    const size_t byteIndex = outlineIndex / 8;

    if (byteIndex >= bits.size())
    {
        return;
    }

    bits[byteIndex] = static_cast<uint8_t>(bits[byteIndex] | (1u << (7u - outlineIndex % 8)));
}

uint32_t effectiveIndoorFaceAttributes(const IndoorFace &face, const MapDeltaData *pMapDeltaData, size_t faceIndex)
{
    if (pMapDeltaData != nullptr && faceIndex < pMapDeltaData->faceAttributes.size())
    {
        return pMapDeltaData->faceAttributes[faceIndex];
    }

    return face.attributes;
}

bool indoorFaceHasInvisibleOverride(size_t faceIndex, const EventRuntimeState *pEventRuntimeState)
{
    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    return pEventRuntimeState->hasFacetInvisibleOverride(static_cast<uint32_t>(faceIndex));
}

bool indoorMinimapFaceVisible(
    const IndoorFace &face,
    const MapDeltaData *pMapDeltaData,
    const EventRuntimeState *pEventRuntimeState,
    size_t faceIndex)
{
    if (hasFaceAttribute(effectiveIndoorFaceAttributes(face, pMapDeltaData, faceIndex), FaceAttribute::Invisible))
    {
        return false;
    }

    return !indoorFaceHasInvisibleOverride(faceIndex, pEventRuntimeState);
}

uint64_t mixIndoorMinimapSignature(uint64_t seed, uint64_t value)
{
    seed ^= value + 0x9e3779b97f4a7c15ull + (seed << 6) + (seed >> 2);
    return seed;
}

uint64_t indoorMinimapByteVectorSignature(const std::vector<uint8_t> &values)
{
    uint64_t result = 1469598103934665603ull;

    for (uint8_t value : values)
    {
        result ^= value;
        result *= 1099511628211ull;
    }

    return result;
}

uint64_t indoorMinimapUIntVectorSignature(const std::vector<uint32_t> &values)
{
    uint64_t result = 1469598103934665603ull;

    for (uint32_t value : values)
    {
        result ^= value;
        result *= 1099511628211ull;
    }

    return result;
}

uint64_t indoorMinimapLineSignature(
    const IndoorMapData &indoorMapData,
    const MapDeltaData &mapDeltaData,
    const EventRuntimeState *pEventRuntimeState,
    float partyFootZ,
    bool showEventOutlines)
{
    uint64_t signature = 0x4f59494d4d415055ull;
    signature = mixIndoorMinimapSignature(signature, reinterpret_cast<uintptr_t>(&indoorMapData));
    signature = mixIndoorMinimapSignature(signature, indoorMapData.faces.size());
    signature = mixIndoorMinimapSignature(signature, indoorMapData.outlines.size());
    signature = mixIndoorMinimapSignature(signature, indoorMinimapByteVectorSignature(mapDeltaData.visibleOutlines));
    signature = mixIndoorMinimapSignature(signature, indoorMinimapUIntVectorSignature(mapDeltaData.faceAttributes));
    signature = mixIndoorMinimapSignature(signature, static_cast<int32_t>(std::round(partyFootZ)));
    signature = mixIndoorMinimapSignature(signature, showEventOutlines ? 1u : 0u);

    if (pEventRuntimeState != nullptr)
    {
        signature = mixIndoorMinimapSignature(signature, pEventRuntimeState->outdoorSurfaceRevision);
        signature = mixIndoorMinimapSignature(signature, pEventRuntimeState->facetSetMasks.size());
        signature = mixIndoorMinimapSignature(signature, pEventRuntimeState->facetClearMasks.size());
    }

    return signature;
}

void ensureIndoorMapRevealState(const IndoorMapData &indoorMapData, MapDeltaData &mapDeltaData)
{
    while (mapDeltaData.faceAttributes.size() < indoorMapData.faces.size())
    {
        const size_t faceIndex = mapDeltaData.faceAttributes.size();
        mapDeltaData.faceAttributes.push_back(indoorMapData.faces[faceIndex].attributes);
    }

    const size_t visibleOutlineByteCount = (indoorMapData.outlines.size() + 7) / 8;

    if (mapDeltaData.visibleOutlines.size() < visibleOutlineByteCount)
    {
        mapDeltaData.visibleOutlines.resize(visibleOutlineByteCount, 0);
    }
}

void updateIndoorJournalRevealMask(
    const IndoorMapData &indoorMapData,
    const std::vector<int16_t> &revealSectorIds,
    const EventRuntimeState *pEventRuntimeState,
    MapDeltaData &mapDeltaData)
{
    ensureIndoorMapRevealState(indoorMapData, mapDeltaData);

    const auto revealSectorFaces = [&](int16_t visibleSectorId)
    {
        if (visibleSectorId < 0 || static_cast<size_t>(visibleSectorId) >= indoorMapData.sectors.size())
        {
            return;
        }

        const IndoorSector &sector = indoorMapData.sectors[visibleSectorId];
        const auto revealFace = [&](uint16_t faceId)
        {
            if (faceId >= indoorMapData.faces.size())
            {
                return;
            }

            const IndoorFace &face = indoorMapData.faces[faceId];

            if (!indoorMinimapFaceVisible(face, &mapDeltaData, pEventRuntimeState, faceId))
            {
                return;
            }

            mapDeltaData.faceAttributes[faceId] |= faceAttributeBit(FaceAttribute::SeenByParty);
        };

        for (uint16_t faceId : sector.faceIds)
        {
            revealFace(faceId);
        }

        for (uint16_t faceId : sector.portalFaceIds)
        {
            revealFace(faceId);
        }
    };

    for (int16_t revealSectorId : revealSectorIds)
    {
        revealSectorFaces(revealSectorId);
    }

    for (size_t outlineIndex = 0; outlineIndex < indoorMapData.outlines.size(); ++outlineIndex)
    {
        const IndoorOutline &outline = indoorMapData.outlines[outlineIndex];

        if (outline.face1Id >= indoorMapData.faces.size() || outline.face2Id >= indoorMapData.faces.size())
        {
            continue;
        }

        const IndoorFace &face1 = indoorMapData.faces[outline.face1Id];
        const IndoorFace &face2 = indoorMapData.faces[outline.face2Id];

        if (!indoorMinimapFaceVisible(face1, &mapDeltaData, pEventRuntimeState, outline.face1Id)
            || !indoorMinimapFaceVisible(face2, &mapDeltaData, pEventRuntimeState, outline.face2Id))
        {
            continue;
        }

        const uint32_t face1Attributes = effectiveIndoorFaceAttributes(face1, &mapDeltaData, outline.face1Id);
        const uint32_t face2Attributes = effectiveIndoorFaceAttributes(face2, &mapDeltaData, outline.face2Id);
        const bool revealed =
            packedIndoorOutlineBit(mapDeltaData.visibleOutlines, outlineIndex)
            || hasFaceAttribute(face1Attributes, FaceAttribute::SeenByParty)
            || hasFaceAttribute(face2Attributes, FaceAttribute::SeenByParty);

        if (revealed)
        {
            setPackedIndoorOutlineBit(mapDeltaData.visibleOutlines, outlineIndex);
        }
    }
}

bool indoorFaceHasMapEvent(const IndoorFace &face)
{
    return face.cogNumber != 0 || face.cogTriggered != 0 || face.textureFrameTableCog != 0;
}

uint32_t indoorMinimapGreyLineColor(float zDelta)
{
    const int dim = std::min(100, static_cast<int>(std::abs(zDelta) / 8.0f));
    const uint8_t grey = static_cast<uint8_t>(std::max(0, 200 - dim));
    return 0xff000000u
        | (static_cast<uint32_t>(grey) << 16)
        | (static_cast<uint32_t>(grey) << 8)
        | static_cast<uint32_t>(grey);
}

float length2d(float x, float y)
{
    return std::sqrt(x * x + y * y);
}

float length3d(float x, float y, float z)
{
    return std::sqrt(x * x + y * y + z * z);
}

float lengthSquared3d(float x, float y, float z)
{
    return x * x + y * y + z * z;
}

bool isWithinRange3d(float x, float y, float z, float range)
{
    return range > 0.0f && lengthSquared3d(x, y, z) <= range * range;
}

GameplayProjectileService::MonsterAttackAbility projectileAbilityFromActorAbility(
    GameplayActorAttackAbility ability)
{
    switch (ability)
    {
        case GameplayActorAttackAbility::Attack2:
            return GameplayProjectileService::MonsterAttackAbility::Attack2;
        case GameplayActorAttackAbility::Spell1:
            return GameplayProjectileService::MonsterAttackAbility::Spell1;
        case GameplayActorAttackAbility::Spell2:
            return GameplayProjectileService::MonsterAttackAbility::Spell2;
        case GameplayActorAttackAbility::Attack1:
        default:
            return GameplayProjectileService::MonsterAttackAbility::Attack1;
    }
}

bool actorAbilityIsSpellProjectile(GameplayActorAttackAbility ability)
{
    return ability == GameplayActorAttackAbility::Spell1 || ability == GameplayActorAttackAbility::Spell2;
}

float indoorActorProjectileSourceHeightFactor(GameplayActorAttackAbility ability)
{
    return actorAbilityIsSpellProjectile(ability) ? 0.5f : 0.75f;
}

bool indoorProjectileSpellName(const std::string &spellName)
{
    static const std::vector<std::string> projectileSpellNames = {
        "fire bolt",
        "fireball",
        "incinerate",
        "lightning bolt",
        "ice bolt",
        "acid burst",
        "deadly swarm",
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

bool indoorMonsterSelfBuffSpellName(const std::string &spellName)
{
    static const std::vector<std::string> selfBuffSpellNames = {
        "bless",
        "day of protection",
        "fate",
        "hammerhands",
        "haste",
        "heroism",
        "hour of power",
        "pain reflection",
        "shield",
        "stoneskin",
    };

    return std::find(selfBuffSpellNames.begin(), selfBuffSpellNames.end(), toLowerCopy(spellName))
        != selfBuffSpellNames.end();
}

bool indoorMonsterSpellCastSupported(const std::string &spellName)
{
    return indoorProjectileSpellName(spellName) || indoorMonsterSelfBuffSpellName(spellName);
}

bool fillIndoorProjectileDefinitionFromObject(
    int objectId,
    int impactObjectId,
    const ObjectTable &objectTable,
    IndoorResolvedProjectileDefinition &definition)
{
    const ObjectEntry *pObjectEntry = objectTable.findByObjectId(static_cast<int16_t>(objectId));
    const std::optional<uint16_t> objectDescriptionId =
        objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(objectId));

    if (pObjectEntry == nullptr || !objectDescriptionId)
    {
        return false;
    }

    definition.objectDescriptionId = *objectDescriptionId;
    definition.objectSpriteId = pObjectEntry->spriteId;
    definition.objectFlags = pObjectEntry->flags;
    definition.radius = static_cast<uint16_t>(std::max<int>(pObjectEntry->radius, 16));
    definition.height = static_cast<uint16_t>(std::max<int>(pObjectEntry->height, 16));
    definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pObjectEntry->lifetimeTicks, 64));
    definition.speed = static_cast<float>(std::max<int>(pObjectEntry->speed, 2000));
    definition.objectName = pObjectEntry->internalName;
    definition.objectSpriteName = pObjectEntry->spriteName;

    if (impactObjectId <= 0)
    {
        return true;
    }

    const ObjectEntry *pImpactEntry = objectTable.findByObjectId(static_cast<int16_t>(impactObjectId));
    const std::optional<uint16_t> impactDescriptionId =
        objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(impactObjectId));

    if (pImpactEntry != nullptr && impactDescriptionId)
    {
        definition.impactObjectDescriptionId = *impactDescriptionId;
    }

    return true;
}

bool fillIndoorProjectileDefinitionFromSpell(
    const SpellEntry &spell,
    const ObjectTable &objectTable,
    IndoorResolvedProjectileDefinition &definition)
{
    definition = {};

    if (spell.displayObjectId <= 0)
    {
        return false;
    }

    if (!fillIndoorProjectileDefinitionFromObject(
            spell.displayObjectId,
            spell.impactDisplayObjectId,
            objectTable,
            definition))
    {
        return false;
    }

    definition.spellId = spell.id;
    definition.effectSoundId = spell.effectSoundId;

    if (isSpellId(static_cast<uint32_t>(std::max(spell.id, 0)), SpellId::Sparks))
    {
        definition.objectFlags |= ObjectDescBounce;
    }
    else if (isSpellId(static_cast<uint32_t>(std::max(spell.id, 0)), SpellId::RockBlast))
    {
        definition.objectFlags |= ObjectDescBounce;
        definition.objectFlags &= ~ObjectDescNoGravity;
    }

    return true;
}

bool resolveIndoorMonsterProjectileDefinition(
    const MonsterTable::MonsterStatsEntry &stats,
    GameplayProjectileService::MonsterAttackAbility ability,
    const MonsterProjectileTable &projectileTable,
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    IndoorResolvedProjectileDefinition &definition)
{
    definition = {};

    if (ability == GameplayProjectileService::MonsterAttackAbility::Attack1
        || ability == GameplayProjectileService::MonsterAttackAbility::Attack2)
    {
        const std::string &projectileToken =
            ability == GameplayProjectileService::MonsterAttackAbility::Attack1
                ? stats.attack1MissileType
                : stats.attack2MissileType;
        const MonsterProjectileEntry *pProjectileEntry = projectileTable.findByToken(projectileToken);

        if (pProjectileEntry == nullptr)
        {
            return false;
        }

        return fillIndoorProjectileDefinitionFromObject(
            pProjectileEntry->objectId,
            pProjectileEntry->impactObjectId,
            objectTable,
            definition);
    }

    const std::string &spellName =
        ability == GameplayProjectileService::MonsterAttackAbility::Spell1 ? stats.spell1Name : stats.spell2Name;

    if (!indoorProjectileSpellName(spellName))
    {
        return false;
    }

    const SpellEntry *pSpellEntry = spellTable.findByName(spellName);

    if (pSpellEntry == nullptr || pSpellEntry->displayObjectId <= 0)
    {
        return false;
    }

    if (!fillIndoorProjectileDefinitionFromObject(
            pSpellEntry->displayObjectId,
            pSpellEntry->impactDisplayObjectId,
            objectTable,
            definition))
    {
        return false;
    }

    definition.spellId = pSpellEntry->id;
    definition.effectSoundId = pSpellEntry->effectSoundId;
    return true;
}

GameplayProjectileService::ProjectileDefinition buildIndoorGameplayProjectileDefinition(
    const IndoorResolvedProjectileDefinition &definition,
    uint16_t objectSpriteFrameIndex)
{
    GameplayProjectileService::ProjectileDefinition result = {};
    result.objectDescriptionId = definition.objectDescriptionId;
    result.objectSpriteId = definition.objectSpriteId;
    result.objectSpriteFrameIndex = objectSpriteFrameIndex;
    result.impactObjectDescriptionId = definition.impactObjectDescriptionId;
    result.objectFlags = definition.objectFlags;
    result.radius = definition.radius;
    result.height = definition.height;
    result.spellId = definition.spellId;
    result.effectSoundId = definition.effectSoundId;
    result.lifetimeTicks = definition.lifetimeTicks;
    result.speed = definition.speed;
    result.objectName = definition.objectName;
    result.objectSpriteName = definition.objectSpriteName;
    return result;
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

uint32_t defaultActorAttributes(bool hostileToParty)
{
    uint32_t attributes = static_cast<uint32_t>(EvtActorAttribute::Active)
        | static_cast<uint32_t>(EvtActorAttribute::FullAi);

    if (hostileToParty)
    {
        attributes |= static_cast<uint32_t>(EvtActorAttribute::Hostile);
    }

    return attributes;
}

bool hasActiveActorSpellEffectOverride(const GameplayActorSpellEffectState &state)
{
    return state.slowRemainingSeconds > 0.0f
        || state.stunRemainingSeconds > 0.0f
        || state.paralyzeRemainingSeconds > 0.0f
        || state.fearRemainingSeconds > 0.0f
        || state.blindRemainingSeconds > 0.0f
        || state.controlRemainingSeconds > 0.0f
        || state.controlMode != GameplayActorControlMode::None
        || state.shrinkRemainingSeconds > 0.0f
        || state.armorClassHalvedRemainingSeconds > 0.0f
        || state.darkGraspRemainingSeconds > 0.0f
        || state.dayOfProtectionRemainingSeconds > 0.0f
        || state.hourOfPowerRemainingSeconds > 0.0f
        || state.painReflectionRemainingSeconds > 0.0f
        || state.hammerhandsRemainingSeconds > 0.0f
        || state.hasteRemainingSeconds > 0.0f
        || state.shieldRemainingSeconds > 0.0f
        || state.stoneskinRemainingSeconds > 0.0f
        || state.blessRemainingSeconds > 0.0f
        || state.fateRemainingSeconds > 0.0f
        || state.heroismRemainingSeconds > 0.0f
        || state.slowMoveMultiplier != 1.0f
        || state.slowRecoveryMultiplier != 1.0f
        || state.shrinkDamageMultiplier != 1.0f
        || state.shrinkArmorClassMultiplier != 1.0f;
}

bool partyHasDispellableBuffs(const Party *pParty)
{
    if (pParty == nullptr)
    {
        return false;
    }

    for (size_t buffIndex = 0; buffIndex < PartyBuffCount; ++buffIndex)
    {
        if (pParty->hasPartyBuff(static_cast<PartyBuffId>(buffIndex)))
        {
            return true;
        }
    }

    for (size_t memberIndex = 0; memberIndex < pParty->members().size(); ++memberIndex)
    {
        for (size_t buffIndex = 0; buffIndex < CharacterBuffCount; ++buffIndex)
        {
            if (pParty->hasCharacterBuff(memberIndex, static_cast<CharacterBuffId>(buffIndex)))
            {
                return true;
            }
        }
    }

    return false;
}

int16_t resolveIndoorActorStatsId(const MapDeltaActor &actor);
const MonsterEntry *resolveRuntimeMonsterEntry(const MonsterTable &monsterTable, const MapDeltaActor &actor);

bool defaultActorHostileToParty(const MapDeltaActor &actor, const MonsterTable *pMonsterTable)
{
    const int16_t resolvedMonsterId = resolveIndoorActorStatsId(actor);
    GameplayActorService actorService = {};
    const int16_t relationMonsterId = actorService.relationMonsterId(resolvedMonsterId, actor.ally);

    return (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Aggressor)) != 0
        || (pMonsterTable != nullptr
            && relationMonsterId > 0
            && pMonsterTable->isHostileToParty(relationMonsterId));
}

int16_t resolveIndoorActorStatsId(const MapDeltaActor &actor)
{
    return actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
}

const MonsterTable::MonsterStatsEntry *findIndoorActorStats(
    const MonsterTable *pMonsterTable,
    const MapDeltaActor &actor)
{
    return pMonsterTable != nullptr ? pMonsterTable->findStatsById(resolveIndoorActorStatsId(actor)) : nullptr;
}

float indoorProjectileActorHitRadius(
    const MonsterTable *pMonsterTable,
    const MapDeltaActor &actor,
    const GameplayRuntimeActorState &actorState)
{
    const MonsterEntry *pMonsterEntry =
        pMonsterTable != nullptr ? resolveRuntimeMonsterEntry(*pMonsterTable, actor) : nullptr;

    if (pMonsterEntry != nullptr && pMonsterEntry->toHitRadius > 0)
    {
        return static_cast<float>(pMonsterEntry->toHitRadius);
    }

    return static_cast<float>(actorState.radius);
}

bool defaultActorHasDetectedParty(const MapDeltaActor &actor, bool hostileToParty)
{
    constexpr uint32_t AggressiveBits =
        static_cast<uint32_t>(EvtActorAttribute::Nearby)
        | static_cast<uint32_t>(EvtActorAttribute::Aggressor);

    return hostileToParty && (actor.attributes & AggressiveBits) != 0;
}

SkillMastery normalizeRuntimeSkillMastery(uint32_t rawSkillMastery)
{
    if (rawSkillMastery > static_cast<uint32_t>(SkillMastery::Grandmaster))
    {
        return SkillMastery::None;
    }

    return static_cast<SkillMastery>(rawSkillMastery);
}

SkillMastery normalizeIndoorEventSkillMastery(uint32_t rawSkillMastery)
{
    if (rawSkillMastery >= static_cast<uint32_t>(SkillMastery::Grandmaster))
    {
        return SkillMastery::Grandmaster;
    }

    return static_cast<SkillMastery>(rawSkillMastery);
}

std::vector<size_t> buildAllIndoorPartyMemberIndices(const Party &party)
{
    std::vector<size_t> memberIndices;
    memberIndices.reserve(party.members().size());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        memberIndices.push_back(memberIndex);
    }

    return memberIndices;
}

std::optional<size_t> findActorOnAttackLine(
    const IndoorWorldRuntime &runtime,
    const GameplayWorldPoint &source,
    const GameplayWorldPoint &target,
    std::optional<size_t> ignoredActorIndex = std::nullopt)
{
    const float segmentX = target.x - source.x;
    const float segmentY = target.y - source.y;
    const float segmentZ = target.z - source.z;
    const float segmentLengthSquared =
        segmentX * segmentX + segmentY * segmentY + segmentZ * segmentZ;

    if (segmentLengthSquared <= 0.0f)
    {
        return std::nullopt;
    }

    std::optional<size_t> bestActorIndex;
    float bestLineProgress = std::numeric_limits<float>::max();
    float bestDistanceSquared = std::numeric_limits<float>::max();

    for (size_t actorIndex = 0; actorIndex < runtime.mapActorCount(); ++actorIndex)
    {
        if (ignoredActorIndex && actorIndex == *ignoredActorIndex)
        {
            continue;
        }

        GameplayRuntimeActorState actorState = {};

        if (!runtime.actorRuntimeState(actorIndex, actorState)
            || actorState.isDead
            || actorState.isInvisible)
        {
            continue;
        }

        const float targetZ =
            actorState.preciseZ + std::max(24.0f, static_cast<float>(actorState.height) * 0.6f);
        const float actorX = actorState.preciseX - source.x;
        const float actorY = actorState.preciseY - source.y;
        const float actorZ = targetZ - source.z;
        const float lineProgress =
            std::clamp(
                (actorX * segmentX + actorY * segmentY + actorZ * segmentZ) / segmentLengthSquared,
                0.0f,
                1.0f);
        const float closestX = source.x + segmentX * lineProgress;
        const float closestY = source.y + segmentY * lineProgress;
        const float closestZ = source.z + segmentZ * lineProgress;
        const float deltaX = actorState.preciseX - closestX;
        const float deltaY = actorState.preciseY - closestY;
        const float deltaZ = targetZ - closestZ;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        const float hitRadius = std::max(32.0f, static_cast<float>(actorState.radius));

        if (distanceSquared > hitRadius * hitRadius)
        {
            continue;
        }

        if (!bestActorIndex
            || lineProgress < bestLineProgress
            || (lineProgress == bestLineProgress && distanceSquared < bestDistanceSquared))
        {
            bestActorIndex = actorIndex;
            bestLineProgress = lineProgress;
            bestDistanceSquared = distanceSquared;
        }
    }

    return bestActorIndex;
}

std::optional<IndoorProjectileCollisionCandidate> findProjectileCylinderHit(
    const GameplayWorldPoint &source,
    const GameplayWorldPoint &target,
    const GameplayWorldPoint &center,
    float radius,
    float halfHeight)
{
    const float segmentX = target.x - source.x;
    const float segmentY = target.y - source.y;
    const float segmentZ = target.z - source.z;
    const float segmentLengthSquared =
        segmentX * segmentX + segmentY * segmentY + segmentZ * segmentZ;

    if (segmentLengthSquared <= 0.0f)
    {
        return std::nullopt;
    }

    const float targetX = center.x - source.x;
    const float targetY = center.y - source.y;
    const float targetZ = center.z - source.z;
    const float progress =
        std::clamp(
            (targetX * segmentX + targetY * segmentY + targetZ * segmentZ) / segmentLengthSquared,
            0.0f,
            1.0f);
    const GameplayWorldPoint closest = {
        source.x + segmentX * progress,
        source.y + segmentY * progress,
        source.z + segmentZ * progress
    };
    const float deltaX = center.x - closest.x;
    const float deltaY = center.y - closest.y;
    const float deltaZ = center.z - closest.z;
    const float horizontalDistanceSquared = deltaX * deltaX + deltaY * deltaY;
    const float verticalSlack = std::max(halfHeight, 1.0f);

    if (horizontalDistanceSquared > radius * radius || std::abs(deltaZ) > verticalSlack)
    {
        return std::nullopt;
    }

    IndoorProjectileCollisionCandidate hit = {};
    hit.point = closest;
    hit.progress = progress;
    hit.distanceSquared = horizontalDistanceSquared + deltaZ * deltaZ;
    return hit;
}

bool projectileHitSortsBefore(
    const IndoorProjectileCollisionCandidate &left,
    const IndoorProjectileCollisionCandidate &right)
{
    return left.progress < right.progress
        || (left.progress == right.progress && left.distanceSquared < right.distanceSquared);
}

float dotProduct(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

bool indoorSegmentMayTouchFaceBounds(
    const GameplayWorldPoint &segmentStart,
    const GameplayWorldPoint &segmentEnd,
    const IndoorFaceGeometryData &geometry,
    float padding)
{
    return std::max(segmentStart.x, segmentEnd.x) + padding >= geometry.minX
        && std::min(segmentStart.x, segmentEnd.x) - padding <= geometry.maxX
        && std::max(segmentStart.y, segmentEnd.y) + padding >= geometry.minY
        && std::min(segmentStart.y, segmentEnd.y) - padding <= geometry.maxY
        && std::max(segmentStart.z, segmentEnd.z) + padding >= geometry.minZ
        && std::min(segmentStart.z, segmentEnd.z) - padding <= geometry.maxZ;
}

std::vector<size_t> collectProjectileIndoorFaceCandidates(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    const GameplayWorldPoint &segmentStart,
    const GameplayWorldPoint &segmentEnd,
    float padding,
    std::optional<int16_t> sourceSectorId)
{
    std::vector<int16_t> sectorIds;

    const auto appendSectorId = [&](int16_t sectorId)
    {
        if (sectorId < 0 || static_cast<size_t>(sectorId) >= indoorMapData.sectors.size())
        {
            return;
        }

        if (std::find(sectorIds.begin(), sectorIds.end(), sectorId) != sectorIds.end())
        {
            return;
        }

        sectorIds.push_back(sectorId);
    };

    if (sourceSectorId)
    {
        appendSectorId(*sourceSectorId);
    }

    if (sectorIds.empty())
    {
        appendSectorId(
            findIndoorSectorForPoint(
                indoorMapData,
                vertices,
                {segmentStart.x, segmentStart.y, segmentStart.z},
                &geometryCache,
                false).value_or(-1));
    }

    const bool resolveEndSector =
        !sourceSectorId
        || !indoorPointInsideSectorBounds(indoorMapData, segmentEnd, *sourceSectorId, padding);

    if (resolveEndSector)
    {
        appendSectorId(
            findIndoorSectorForPoint(
                indoorMapData,
                vertices,
                {segmentEnd.x, segmentEnd.y, segmentEnd.z},
                &geometryCache,
                false).value_or(-1));
    }

    const size_t baseSectorCount = sectorIds.size();

    for (size_t index = 0; index < baseSectorCount; ++index)
    {
        const int16_t sectorId = sectorIds[index];
        const IndoorSector &sector = indoorMapData.sectors[sectorId];

        for (uint16_t faceId : sector.portalFaceIds)
        {
            const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(indoorMapData, vertices, faceId);

            if (pGeometry == nullptr
                || !indoorSegmentMayTouchFaceBounds(segmentStart, segmentEnd, *pGeometry, padding))
            {
                continue;
            }

            if (pGeometry->sectorId == static_cast<uint16_t>(sectorId))
            {
                appendSectorId(static_cast<int16_t>(pGeometry->backSectorId));
            }
            else if (pGeometry->backSectorId == static_cast<uint16_t>(sectorId))
            {
                appendSectorId(static_cast<int16_t>(pGeometry->sectorId));
            }
        }
    }

    std::vector<size_t> faceIndices;

    if (sectorIds.empty())
    {
        faceIndices.reserve(indoorMapData.faces.size());

        for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
        {
            faceIndices.push_back(faceIndex);
        }

        return faceIndices;
    }

    const auto appendFaceIds = [&faceIndices](const std::vector<uint16_t> &sectorFaceIds)
    {
        for (uint16_t faceId : sectorFaceIds)
        {
            faceIndices.push_back(faceId);
        }
    };

    for (int16_t sectorId : sectorIds)
    {
        const IndoorSector &sector = indoorMapData.sectors[sectorId];
        appendFaceIds(sector.floorFaceIds);
        appendFaceIds(sector.wallFaceIds);
        appendFaceIds(sector.ceilingFaceIds);
        appendFaceIds(sector.cylinderFaceIds);
    }

    std::sort(faceIndices.begin(), faceIndices.end());
    faceIndices.erase(std::unique(faceIndices.begin(), faceIndices.end()), faceIndices.end());
    return faceIndices;
}

std::optional<IndoorProjectileCollisionCandidate> findProjectileIndoorFaceHit(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pMapDeltaData,
    const EventRuntimeState *pEventRuntimeState,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    const GameplayProjectileService::ProjectileState &projectile,
    const GameplayWorldPoint &segmentStart,
    const GameplayWorldPoint &segmentEnd,
    std::optional<int16_t> sourceSectorId)
{
    constexpr float PlaneEpsilon = 0.0001f;
    const bx::Vec3 start = {segmentStart.x, segmentStart.y, segmentStart.z};
    const bx::Vec3 end = {segmentEnd.x, segmentEnd.y, segmentEnd.z};
    const bx::Vec3 segment = {end.x - start.x, end.y - start.y, end.z - start.z};
    const float collisionPadding =
        static_cast<float>(std::max<uint16_t>(std::max(projectile.radius, projectile.height), 8));
    std::optional<IndoorProjectileCollisionCandidate> bestCollision;
    const std::vector<size_t> candidateFaceIndices =
        collectProjectileIndoorFaceCandidates(
            indoorMapData,
            vertices,
            geometryCache,
            segmentStart,
            segmentEnd,
            collisionPadding,
            sourceSectorId);

    for (size_t faceIndex : candidateFaceIndices)
    {
        if (faceIndex >= indoorMapData.faces.size())
        {
            continue;
        }

        const IndoorFace &face = indoorMapData.faces[faceIndex];
        const uint32_t effectiveAttributes = effectiveIndoorFaceAttributes(face, pMapDeltaData, faceIndex);

        if (face.isPortal
            || hasFaceAttribute(effectiveAttributes, FaceAttribute::IsPortal)
            || hasFaceAttribute(effectiveAttributes, FaceAttribute::Invisible)
            || hasFaceAttribute(effectiveAttributes, FaceAttribute::Untouchable)
            || indoorFaceHasInvisibleOverride(faceIndex, pEventRuntimeState))
        {
            continue;
        }

        const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(
            indoorMapData,
            vertices,
            faceIndex);

        if (pGeometry == nullptr
            || !pGeometry->hasPlane
            || pGeometry->isPortal
            || !indoorSegmentMayTouchFaceBounds(segmentStart, segmentEnd, *pGeometry, collisionPadding))
        {
            continue;
        }

        const float denominator = dotProduct(segment, pGeometry->normal);

        if (std::fabs(denominator) <= PlaneEpsilon)
        {
            continue;
        }

        const bx::Vec3 planeDelta = {
            pGeometry->vertices.front().x - start.x,
            pGeometry->vertices.front().y - start.y,
            pGeometry->vertices.front().z - start.z
        };
        const float progress = dotProduct(planeDelta, pGeometry->normal) / denominator;

        if (progress < 0.0f || progress > 1.0f)
        {
            continue;
        }

        const bx::Vec3 impactPoint = {
            start.x + segment.x * progress,
            start.y + segment.y * progress,
            start.z + segment.z * progress
        };

        if (!isPointInsideIndoorPolygonProjected(impactPoint, pGeometry->vertices, pGeometry->normal))
        {
            continue;
        }

        IndoorProjectileCollisionCandidate collision = {};
        collision.kind = GameplayProjectileService::ProjectileFrameCollisionKind::World;
        collision.point = {impactPoint.x, impactPoint.y, impactPoint.z};
        collision.faceIndex = faceIndex;
        bx::Vec3 collisionNormal = pGeometry->normal;
        if (dotProduct(collisionNormal, segment) > 0.0f)
        {
            collisionNormal = {-collisionNormal.x, -collisionNormal.y, -collisionNormal.z};
        }
        collision.normalX = collisionNormal.x;
        collision.normalY = collisionNormal.y;
        collision.normalZ = collisionNormal.z;
        collision.requiresDownwardVelocityToBounce = pGeometry->kind == IndoorFaceKind::Floor;
        collision.progress = progress;
        collision.distanceSquared =
            (impactPoint.x - start.x) * (impactPoint.x - start.x)
            + (impactPoint.y - start.y) * (impactPoint.y - start.y)
            + (impactPoint.z - start.z) * (impactPoint.z - start.z);

        if (!bestCollision || projectileHitSortsBefore(collision, *bestCollision))
        {
            bestCollision = collision;
        }
    }

    return bestCollision;
}

int16_t sectorBehindPortal(const IndoorFaceGeometryData &geometry, int16_t currentSectorId);

std::vector<size_t> collectIndoorCombatLineFaceCandidates(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    const GameplayWorldPoint &segmentStart,
    const GameplayWorldPoint &segmentEnd,
    int16_t sourceSectorId,
    int16_t targetSectorId)
{
    constexpr float PlaneEpsilon = 0.0001f;
    std::vector<int16_t> sectorIds;
    const auto appendSectorId = [&sectorIds, &indoorMapData](int16_t sectorId)
    {
        if (sectorId < 0
            || static_cast<size_t>(sectorId) >= indoorMapData.sectors.size()
            || std::find(sectorIds.begin(), sectorIds.end(), sectorId) != sectorIds.end())
        {
            return;
        }

        sectorIds.push_back(sectorId);
    };

    appendSectorId(sourceSectorId);

    const bx::Vec3 start = {segmentStart.x, segmentStart.y, segmentStart.z};
    const bx::Vec3 segment = {
        segmentEnd.x - segmentStart.x,
        segmentEnd.y - segmentStart.y,
        segmentEnd.z - segmentStart.z
    };
    int16_t currentSectorId = sourceSectorId;

    for (int portalStep = 0;
         portalStep < IndoorActorDetectPortalLimit && currentSectorId != targetSectorId;
         ++portalStep)
    {
        if (currentSectorId < 0 || static_cast<size_t>(currentSectorId) >= indoorMapData.sectors.size())
        {
            break;
        }

        const IndoorSector &sector = indoorMapData.sectors[currentSectorId];
        int16_t nextSectorId = -1;

        for (uint16_t faceId : sector.portalFaceIds)
        {
            const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(indoorMapData, vertices, faceId);

            if (pGeometry == nullptr
                || !pGeometry->hasPlane
                || !pGeometry->isPortal
                || sectorBehindPortal(*pGeometry, currentSectorId) < 0
                || !indoorSegmentMayTouchFaceBounds(segmentStart, segmentEnd, *pGeometry, 0.0f))
            {
                continue;
            }

            const float denominator = dotProduct(segment, pGeometry->normal);

            if (std::fabs(denominator) <= PlaneEpsilon)
            {
                continue;
            }

            const bx::Vec3 planeDelta = {
                pGeometry->vertices.front().x - start.x,
                pGeometry->vertices.front().y - start.y,
                pGeometry->vertices.front().z - start.z
            };
            const float progress = dotProduct(planeDelta, pGeometry->normal) / denominator;

            if (progress < 0.0f || progress > 1.0f)
            {
                continue;
            }

            const bx::Vec3 portalPoint = {
                start.x + segment.x * progress,
                start.y + segment.y * progress,
                start.z + segment.z * progress
            };

            if (!isPointInsideIndoorPolygonProjected(portalPoint, pGeometry->vertices, pGeometry->normal))
            {
                continue;
            }

            nextSectorId = sectorBehindPortal(*pGeometry, currentSectorId);
            break;
        }

        if (nextSectorId < 0 || nextSectorId == currentSectorId)
        {
            break;
        }

        appendSectorId(nextSectorId);
        currentSectorId = nextSectorId;
    }

    std::vector<size_t> faceIndices;
    const auto appendFaceIds = [&faceIndices](const std::vector<uint16_t> &sectorFaceIds)
    {
        for (uint16_t faceId : sectorFaceIds)
        {
            faceIndices.push_back(faceId);
        }
    };

    for (int16_t sectorId : sectorIds)
    {
        const IndoorSector &sector = indoorMapData.sectors[sectorId];
        appendFaceIds(sector.floorFaceIds);
        appendFaceIds(sector.wallFaceIds);
        appendFaceIds(sector.ceilingFaceIds);
        appendFaceIds(sector.cylinderFaceIds);
    }

    std::sort(faceIndices.begin(), faceIndices.end());
    faceIndices.erase(std::unique(faceIndices.begin(), faceIndices.end()), faceIndices.end());
    return faceIndices;
}

bool indoorSegmentBlockedByCombatFace(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pMapDeltaData,
    const EventRuntimeState *pEventRuntimeState,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    const GameplayWorldPoint &segmentStart,
    const GameplayWorldPoint &segmentEnd,
    int16_t sourceSectorId,
    int16_t targetSectorId)
{
    constexpr float PlaneEpsilon = 0.0001f;
    constexpr float EndPointProgressSlack = 0.015f;
    constexpr float BoundsPadding = 1.0f;
    const bx::Vec3 start = {segmentStart.x, segmentStart.y, segmentStart.z};
    const bx::Vec3 end = {segmentEnd.x, segmentEnd.y, segmentEnd.z};
    const bx::Vec3 segment = {end.x - start.x, end.y - start.y, end.z - start.z};
    const std::vector<size_t> candidateFaceIndices =
        collectIndoorCombatLineFaceCandidates(
            indoorMapData,
            vertices,
            geometryCache,
            segmentStart,
            segmentEnd,
            sourceSectorId,
            targetSectorId);

    for (size_t faceIndex : candidateFaceIndices)
    {
        if (faceIndex >= indoorMapData.faces.size())
        {
            continue;
        }

        const IndoorFace &face = indoorMapData.faces[faceIndex];
        const uint32_t effectiveAttributes = effectiveIndoorFaceAttributes(face, pMapDeltaData, faceIndex);

        if (face.isPortal
            || hasFaceAttribute(effectiveAttributes, FaceAttribute::IsPortal)
            || hasFaceAttribute(effectiveAttributes, FaceAttribute::Invisible)
            || indoorFaceHasInvisibleOverride(faceIndex, pEventRuntimeState))
        {
            continue;
        }

        const IndoorFaceGeometryData *pGeometry =
            geometryCache.geometryForFace(indoorMapData, vertices, faceIndex);

        if (pGeometry == nullptr
            || !pGeometry->hasPlane
            || pGeometry->isPortal
            || !indoorSegmentMayTouchFaceBounds(segmentStart, segmentEnd, *pGeometry, BoundsPadding))
        {
            continue;
        }

        const float denominator = dotProduct(segment, pGeometry->normal);

        if (std::fabs(denominator) <= PlaneEpsilon)
        {
            continue;
        }

        const bx::Vec3 planeDelta = {
            pGeometry->vertices.front().x - start.x,
            pGeometry->vertices.front().y - start.y,
            pGeometry->vertices.front().z - start.z
        };
        const float progress = dotProduct(planeDelta, pGeometry->normal) / denominator;

        if (progress <= EndPointProgressSlack || progress >= 1.0f - EndPointProgressSlack)
        {
            continue;
        }

        const bx::Vec3 impactPoint = {
            start.x + segment.x * progress,
            start.y + segment.y * progress,
            start.z + segment.z * progress
        };

        if (isPointInsideIndoorPolygonProjected(impactPoint, pGeometry->vertices, pGeometry->normal))
        {
            return true;
        }
    }

    return false;
}

const MonsterEntry *resolveRuntimeMonsterEntry(const MonsterTable &monsterTable, const MapDeltaActor &actor)
{
    const MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
        monsterTable.findDisplayEntryById(actor.monsterInfoId);

    if (pDisplayEntry != nullptr)
    {
        const MonsterEntry *pMonsterEntry = monsterTable.findByInternalName(pDisplayEntry->pictureName);

        if (pMonsterEntry != nullptr)
        {
            return pMonsterEntry;
        }
    }

    return monsterTable.findById(actor.monsterId);
}

uint16_t resolveRuntimeActorSpriteFrameIndex(
    const SpriteFrameTable &spriteFrameTable,
    const MapDeltaActor &actor,
    const MonsterEntry *pMonsterEntry)
{
    if (pMonsterEntry != nullptr)
    {
        for (const std::string &spriteName : pMonsterEntry->spriteNames)
        {
            if (spriteName.empty())
            {
                continue;
            }

            const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

            if (frameIndex)
            {
                return *frameIndex;
            }
        }
    }

    for (uint16_t spriteId : actor.spriteIds)
    {
        if (spriteId != 0)
        {
            return spriteId;
        }
    }

    return 0;
}

uint16_t resolveRuntimeActorActionSpriteFrameIndex(
    const SpriteFrameTable *pSpriteFrameTable,
    const MonsterEntry *pMonsterEntry,
    ActorAiAnimationState animationState)
{
    if (pSpriteFrameTable == nullptr || pMonsterEntry == nullptr)
    {
        return 0;
    }

    const size_t actionIndex = static_cast<size_t>(animationState);

    if (actionIndex >= pMonsterEntry->spriteNames.size())
    {
        return 0;
    }

    const std::string &spriteName = pMonsterEntry->spriteNames[actionIndex];

    if (spriteName.empty())
    {
        return 0;
    }

    const std::optional<uint16_t> frameIndex = pSpriteFrameTable->findFrameIndexBySpriteName(spriteName);
    return frameIndex.value_or(0);
}

std::array<uint16_t, 8> buildRuntimeActorActionSpriteFrameIndices(
    const SpriteFrameTable *pSpriteFrameTable,
    const MonsterEntry *pMonsterEntry)
{
    std::array<uint16_t, 8> spriteFrameIndices = {};

    if (pSpriteFrameTable == nullptr || pMonsterEntry == nullptr)
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

        const std::optional<uint16_t> frameIndex = pSpriteFrameTable->findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            spriteFrameIndices[actionIndex] = *frameIndex;
        }
    }

    return spriteFrameIndices;
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
    const MonsterEntry *pMonsterEntry,
    ActorAiAnimationState animationState,
    float fallbackSeconds)
{
    return animationSecondsForSpriteFrame(
        pSpriteFrameTable,
        resolveRuntimeActorActionSpriteFrameIndex(pSpriteFrameTable, pMonsterEntry, animationState),
        fallbackSeconds);
}

uint16_t resolveRuntimeProjectileSpriteFrameIndex(
    const SpriteFrameTable *pSpriteFrameTable,
    uint16_t fallbackSpriteId,
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

    return fallbackSpriteId;
}

ActorAiAnimationState actorAiAnimationStateFromIndoor(const MapDeltaActor &actor)
{
    switch (std::clamp<int>(actor.currentActionAnimation, 0, 7))
    {
        case 1:
            return ActorAiAnimationState::Walking;
        case 2:
            return ActorAiAnimationState::AttackMelee;
        case 3:
            return ActorAiAnimationState::AttackRanged;
        case 4:
            return ActorAiAnimationState::GotHit;
        case 5:
            return ActorAiAnimationState::Dying;
        case 6:
            return ActorAiAnimationState::Dead;
        case 7:
            return ActorAiAnimationState::Bored;
        case 0:
        default:
            return ActorAiAnimationState::Standing;
    }
}

uint16_t indoorActionAnimationFromActorAi(ActorAiAnimationState animationState)
{
    switch (animationState)
    {
        case ActorAiAnimationState::Walking:
            return 1;
        case ActorAiAnimationState::AttackMelee:
            return 2;
        case ActorAiAnimationState::AttackRanged:
            return 3;
        case ActorAiAnimationState::GotHit:
            return 4;
        case ActorAiAnimationState::Dying:
            return 5;
        case ActorAiAnimationState::Dead:
            return 6;
        case ActorAiAnimationState::Bored:
            return 7;
        case ActorAiAnimationState::Standing:
        default:
            return 0;
    }
}

float indoorMonsterRecoverySeconds(int recoveryTicks)
{
    return std::max(0.3f, static_cast<float>(recoveryTicks) / TicksPerSecond * OeRealtimeRecoveryScale);
}

GameplayActorAiType gameplayActorAiTypeFromMonster(MonsterTable::MonsterAiType aiType)
{
    switch (aiType)
    {
        case MonsterTable::MonsterAiType::Wimp:
            return GameplayActorAiType::Wimp;

        case MonsterTable::MonsterAiType::Normal:
            return GameplayActorAiType::Normal;

        case MonsterTable::MonsterAiType::Aggressive:
            return GameplayActorAiType::Aggressive;

        case MonsterTable::MonsterAiType::Suicide:
        default:
            return GameplayActorAiType::Suicide;
    }
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

float meleeRangeForCombatTarget(bool targetIsActor)
{
    return targetIsActor ? ActorMeleeRange * 0.5f : ActorMeleeRange;
}

GameplayActorTargetPolicyState buildIndoorActorTargetPolicyState(
    const IndoorWorldRuntime::MapActorAiState &aiState,
    const GameplayActorSpellEffectState &spellEffects,
    uint16_t height,
    bool hostileToParty,
    uint32_t group,
    uint32_t ally)
{
    GameplayActorService actorService = {};
    GameplayActorTargetPolicyState state = {};
    state.monsterId = aiState.monsterId;
    state.relationMonsterId = actorService.relationMonsterId(aiState.monsterId, ally);
    state.group = group;
    state.preciseZ = aiState.preciseZ;
    state.height = height;
    state.hostileToParty = hostileToParty;
    state.controlMode = spellEffects.controlMode;
    return state;
}

int16_t sectorBehindPortal(const IndoorFaceGeometryData &geometry, int16_t currentSectorId)
{
    if (geometry.sectorId == currentSectorId)
    {
        return static_cast<int16_t>(geometry.backSectorId);
    }

    if (geometry.backSectorId == currentSectorId)
    {
        return static_cast<int16_t>(geometry.sectorId);
    }

    return -1;
}

bool indoorDetectBetweenObjects(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    const GameplayWorldPoint &from,
    int16_t fromSectorId,
    const GameplayWorldPoint &to,
    int16_t toSectorId)
{
    constexpr float PlaneEpsilon = 0.0001f;

    if (fromSectorId < 0
        || toSectorId < 0
        || static_cast<size_t>(fromSectorId) >= indoorMapData.sectors.size()
        || static_cast<size_t>(toSectorId) >= indoorMapData.sectors.size())
    {
        return false;
    }

    const float deltaX = to.x - from.x;
    const float deltaY = to.y - from.y;
    const float deltaZ = to.z - from.z;
    const float distanceSquared = lengthSquared3d(deltaX, deltaY, deltaZ);

    if (distanceSquared > IndoorActorDetectRange * IndoorActorDetectRange)
    {
        return false;
    }

    if (fromSectorId == toSectorId)
    {
        return true;
    }

    const float distance = std::sqrt(distanceSquared);

    if (distance <= PlaneEpsilon)
    {
        return false;
    }

    const bx::Vec3 start = {from.x, from.y, from.z};
    const bx::Vec3 segment = {deltaX, deltaY, deltaZ};
    int16_t currentSectorId = fromSectorId;

    for (int portalStep = 0; portalStep < IndoorActorDetectPortalLimit; ++portalStep)
    {
        if (currentSectorId < 0 || static_cast<size_t>(currentSectorId) >= indoorMapData.sectors.size())
        {
            return false;
        }

        const IndoorSector &sector = indoorMapData.sectors[currentSectorId];
        int16_t nextSectorId = -1;

        for (uint16_t faceId : sector.portalFaceIds)
        {
            const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(indoorMapData, vertices, faceId);

            if (pGeometry == nullptr
                || !pGeometry->hasPlane
                || !pGeometry->isPortal
                || sectorBehindPortal(*pGeometry, currentSectorId) < 0
                || !indoorSegmentMayTouchFaceBounds(from, to, *pGeometry, 0.0f))
            {
                continue;
            }

            const float denominator = dotProduct(segment, pGeometry->normal);

            if (std::fabs(denominator) <= PlaneEpsilon)
            {
                continue;
            }

            const bx::Vec3 planeDelta = {
                pGeometry->vertices.front().x - start.x,
                pGeometry->vertices.front().y - start.y,
                pGeometry->vertices.front().z - start.z
            };
            const float progress = dotProduct(planeDelta, pGeometry->normal) / denominator;

            if (progress < 0.0f || progress > 1.0f)
            {
                continue;
            }

            const bx::Vec3 portalPoint = {
                start.x + segment.x * progress,
                start.y + segment.y * progress,
                start.z + segment.z * progress
            };

            if (!isPointInsideIndoorPolygonProjected(portalPoint, pGeometry->vertices, pGeometry->normal))
            {
                continue;
            }

            nextSectorId = sectorBehindPortal(*pGeometry, currentSectorId);
            break;
        }

        if (nextSectorId < 0 || nextSectorId == currentSectorId)
        {
            return false;
        }

        if (nextSectorId == toSectorId)
        {
            return true;
        }

        currentSectorId = nextSectorId;
    }

    return currentSectorId == toSectorId;
}

bool indoorActorUnavailableForCombat(
    const MapDeltaActor &actor,
    const IndoorWorldRuntime::MapActorAiState &aiState,
    const GameplayActorService &actorService)
{
    const bool invisible = (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0;
    return actorService.isActorUnavailableForCombat(
        invisible,
        actor.hp <= 0 || aiState.motionState == ActorAiMotionState::Dead,
        actor.hp <= 0,
        aiState.motionState == ActorAiMotionState::Dying,
        aiState.motionState == ActorAiMotionState::Dead);
}

float indoorActorCollisionRadius(const MapDeltaActor &actor)
{
    if (actor.radius > 0)
    {
        return static_cast<float>(actor.radius);
    }

    return IndoorActorContactProbeRadius;
}

float indoorActorCollisionHeight(
    const MapDeltaActor &actor,
    float collisionRadius)
{
    if (actor.height > 0)
    {
        return std::max(static_cast<float>(actor.height), collisionRadius * 2.0f + 2.0f);
    }

    return collisionRadius * 2.0f + 2.0f;
}

IndoorWorldRuntime::MapActorAiState buildIndoorMapActorAiState(
    const MapDeltaActor &actor,
    size_t actorIndex,
    const MonsterTable *pMonsterTable,
    const GameplayActorService *pGameplayActorService,
    const SpriteFrameTable *pActorSpriteFrameTable)
{
    const int16_t resolvedMonsterId = resolveIndoorActorStatsId(actor);
    const MonsterTable::MonsterStatsEntry *pStats =
        pMonsterTable != nullptr ? pMonsterTable->findStatsById(resolvedMonsterId) : nullptr;
    const MonsterEntry *pMonsterEntry =
        pMonsterTable != nullptr ? resolveRuntimeMonsterEntry(*pMonsterTable, actor) : nullptr;
    const GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService =
        pGameplayActorService != nullptr ? pGameplayActorService : &fallbackActorService;
    const bool hostileToParty = defaultActorHostileToParty(actor, pMonsterTable);
    const float recoverySeconds = indoorMonsterRecoverySeconds(pStats != nullptr ? pStats->recovery : 100);

    IndoorWorldRuntime::MapActorAiState state = {};
    state.actorId = static_cast<uint32_t>(actorIndex);
    state.monsterId = resolvedMonsterId;
    state.displayName = pStats != nullptr ? pStats->name : actor.name;
    state.spriteFrameIndex = pActorSpriteFrameTable != nullptr
        ? resolveRuntimeActorSpriteFrameIndex(*pActorSpriteFrameTable, actor, pMonsterEntry)
        : 0;
    state.actionSpriteFrameIndices = buildRuntimeActorActionSpriteFrameIndices(pActorSpriteFrameTable, pMonsterEntry);
    state.collisionRadius = actor.radius != 0
        ? actor.radius
        : pMonsterEntry != nullptr ? pMonsterEntry->radius : uint16_t(32);
    const float fallbackCollisionHeight = pMonsterEntry != nullptr
        ? std::max(static_cast<float>(pMonsterEntry->height), static_cast<float>(state.collisionRadius) * 2.0f + 2.0f)
        : indoorActorCollisionHeight(actor, static_cast<float>(state.collisionRadius));
    state.collisionHeight = static_cast<uint16_t>(std::max(
        2.0f,
        actor.height != 0 ? indoorActorCollisionHeight(actor, static_cast<float>(state.collisionRadius))
                          : fallbackCollisionHeight));
    state.projectileHitRadius =
        pMonsterEntry != nullptr && pMonsterEntry->toHitRadius > 0
            ? static_cast<uint16_t>(pMonsterEntry->toHitRadius)
            : state.collisionRadius;
    state.movementSpeed = actor.moveSpeed != 0
        ? actor.moveSpeed
        : pMonsterEntry != nullptr ? pMonsterEntry->movementSpeed : uint16_t(pStats != nullptr ? pStats->speed : 0);
    state.hostileToParty = hostileToParty;
    state.hasDetectedParty = defaultActorHasDetectedParty(actor, hostileToParty);
    state.motionState = actor.hp <= 0 ? ActorAiMotionState::Dead : ActorAiMotionState::Standing;
    state.animationState = actor.hp <= 0 ? ActorAiAnimationState::Dead : actorAiAnimationStateFromIndoor(actor);
    state.spellEffects.hostileToParty = hostileToParty;
    state.spellEffects.hasDetectedParty = state.hasDetectedParty;
    state.preciseX = static_cast<float>(actor.x);
    state.preciseY = static_cast<float>(actor.y);
    state.preciseZ = static_cast<float>(actor.z);
    state.sectorId = actor.sectorId;
    state.eyeSectorId = actor.sectorId;
    state.homePreciseX = state.preciseX;
    state.homePreciseY = state.preciseY;
    state.homePreciseZ = state.preciseZ;
    state.recoverySeconds = recoverySeconds;
    state.meleeAttackAnimationSeconds =
        actorAnimationSeconds(pActorSpriteFrameTable, pMonsterEntry, ActorAiAnimationState::AttackMelee, 0.3f);
    state.rangedAttackAnimationSeconds =
        actorAnimationSeconds(pActorSpriteFrameTable, pMonsterEntry, ActorAiAnimationState::AttackRanged, 0.3f);
    state.dyingAnimationSeconds =
        actorAnimationSeconds(pActorSpriteFrameTable, pMonsterEntry, ActorAiAnimationState::Dying, 0.6f);
    state.attackAnimationSeconds =
        std::max(state.meleeAttackAnimationSeconds, state.rangedAttackAnimationSeconds);
    state.attackCooldownSeconds =
        pActorService->initialAttackCooldownSeconds(state.actorId, state.recoverySeconds);
    state.idleDecisionSeconds = pActorService->initialIdleDecisionSeconds(state.actorId);
    return state;
}

void refreshIndoorMapActorAiStaticFields(
    IndoorWorldRuntime::MapActorAiState &state,
    const MapDeltaActor &actor,
    size_t actorIndex,
    const MonsterTable *pMonsterTable,
    const GameplayActorService *pGameplayActorService,
    const SpriteFrameTable *pActorSpriteFrameTable)
{
    const IndoorWorldRuntime::MapActorAiState defaults =
        buildIndoorMapActorAiState(
            actor,
            actorIndex,
            pMonsterTable,
            pGameplayActorService,
            pActorSpriteFrameTable);

    state.actorId = defaults.actorId;
    state.monsterId = defaults.monsterId;
    state.displayName = defaults.displayName;
    state.spriteFrameIndex = defaults.spriteFrameIndex;
    state.actionSpriteFrameIndices = defaults.actionSpriteFrameIndices;
    state.collisionRadius = defaults.collisionRadius;
    state.collisionHeight = defaults.collisionHeight;
    state.projectileHitRadius = defaults.projectileHitRadius;
    state.movementSpeed = defaults.movementSpeed;
    state.meleeAttackAnimationSeconds = defaults.meleeAttackAnimationSeconds;
    state.rangedAttackAnimationSeconds = defaults.rangedAttackAnimationSeconds;
    state.dyingAnimationSeconds = defaults.dyingAnimationSeconds;
}

void fixIndoorInitialActorPlacement(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const MonsterTable *pMonsterTable,
    MapDeltaActor &actor,
    IndoorFaceGeometryCache &geometryCache)
{
    if (vertices.empty())
    {
        return;
    }

    const MonsterTable::MonsterStatsEntry *pStats = findIndoorActorStats(pMonsterTable, actor);
    const float queryZ = static_cast<float>(actor.z) + static_cast<float>(actor.radius);
    const IndoorFloorSample floorSample =
        sampleIndoorFloor(
            indoorMapData,
            vertices,
            static_cast<float>(actor.x),
            static_cast<float>(actor.y),
            queryZ,
            IndoorInitialActorFloorSampleRise,
            IndoorInitialActorFloorSampleDrop,
            std::nullopt,
            nullptr,
            &geometryCache);

    if (!floorSample.hasFloor)
    {
        return;
    }

    actor.sectorId = floorSample.sectorId;

    if (pStats != nullptr && pStats->canFly && static_cast<float>(actor.z) > floorSample.height + 1.0f)
    {
        return;
    }

    actor.z = static_cast<int>(std::lround(floorSample.height));
}

void writeRawItemUInt16(std::vector<uint8_t> &bytes, size_t offset, uint16_t value)
{
    if (bytes.size() >= offset + sizeof(value))
    {
        std::memcpy(bytes.data() + offset, &value, sizeof(value));
    }
}

void writeRawItemUInt32(std::vector<uint8_t> &bytes, size_t offset, uint32_t value)
{
    if (bytes.size() >= offset + sizeof(value))
    {
        std::memcpy(bytes.data() + offset, &value, sizeof(value));
    }
}

bool readRawItemUInt16(const std::vector<uint8_t> &bytes, size_t offset, uint16_t &value)
{
    if (bytes.size() < offset + sizeof(value))
    {
        return false;
    }

    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return true;
}

bool readRawItemUInt32(const std::vector<uint8_t> &bytes, size_t offset, uint32_t &value)
{
    if (bytes.size() < offset + sizeof(value))
    {
        return false;
    }

    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return true;
}

void writeIndoorHeldItemPayload(std::vector<uint8_t> &bytes, const InventoryItem &item)
{
    bytes.assign(RawContainingItemSize, 0);
    writeRawItemUInt32(bytes, 0x00, item.objectDescriptionId);
    writeRawItemUInt32(bytes, 0x04, item.quantity);

    uint8_t flags = 0;
    flags |= item.identified ? 0x01 : 0x00;
    flags |= item.broken ? 0x02 : 0x00;
    flags |= item.stolen ? 0x04 : 0x00;

    if (bytes.size() > 0x08)
    {
        bytes[0x08] = flags;
    }

    writeRawItemUInt16(bytes, 0x10, item.standardEnchantId);
    writeRawItemUInt16(bytes, 0x12, item.standardEnchantPower);
    writeRawItemUInt16(bytes, 0x14, item.specialEnchantId);
    writeRawItemUInt16(bytes, 0x16, item.artifactId);

    if (bytes.size() > 0x18)
    {
        bytes[0x18] = static_cast<uint8_t>(item.rarity);
    }

    if (bytes.size() >= 0x20)
    {
        std::memcpy(bytes.data() + 0x1c, &item.temporaryBonusRemainingSeconds, sizeof(float));
    }
}

bool readIndoorHeldItemPayload(
    const std::vector<uint8_t> &bytes,
    const ItemTable *pItemTable,
    InventoryItem &item)
{
    uint32_t itemId = 0;

    if (!readRawItemUInt32(bytes, 0x00, itemId) || itemId == 0)
    {
        return false;
    }

    item = {};
    item.objectDescriptionId = itemId;

    uint32_t quantity = 0;

    if (readRawItemUInt32(bytes, 0x04, quantity) && quantity > 0)
    {
        item.quantity = quantity;
    }

    if (bytes.size() > 0x08)
    {
        item.identified = (bytes[0x08] & 0x01) != 0;
        item.broken = (bytes[0x08] & 0x02) != 0;
        item.stolen = (bytes[0x08] & 0x04) != 0;
    }

    readRawItemUInt16(bytes, 0x10, item.standardEnchantId);
    readRawItemUInt16(bytes, 0x12, item.standardEnchantPower);
    readRawItemUInt16(bytes, 0x14, item.specialEnchantId);
    readRawItemUInt16(bytes, 0x16, item.artifactId);

    if (bytes.size() > 0x18 && bytes[0x18] <= static_cast<uint8_t>(ItemRarity::Special))
    {
        item.rarity = static_cast<ItemRarity>(bytes[0x18]);
    }

    if (bytes.size() >= 0x20)
    {
        std::memcpy(&item.temporaryBonusRemainingSeconds, bytes.data() + 0x1c, sizeof(float));
    }

    const ItemDefinition *pItemDefinition = pItemTable != nullptr ? pItemTable->get(itemId) : nullptr;

    if (pItemDefinition != nullptr)
    {
        item.width = pItemDefinition->inventoryWidth;
        item.height = pItemDefinition->inventoryHeight;
    }

    return true;
}

std::optional<uint16_t> resolveIndoorItemObjectDescriptionId(
    const InventoryItem &item,
    const ItemTable *pItemTable,
    const ObjectTable *pObjectTable)
{
    if (item.objectDescriptionId == 0 || pItemTable == nullptr || pObjectTable == nullptr)
    {
        return std::nullopt;
    }

    const ItemDefinition *pItemDefinition = pItemTable->get(item.objectDescriptionId);

    if (pItemDefinition == nullptr || pItemDefinition->spriteIndex == 0)
    {
        return std::nullopt;
    }

    return pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(pItemDefinition->spriteIndex));
}

uint16_t yawAngleFromRadians(float yawRadians)
{
    const float normalizedTurns = yawRadians / (Pi * 2.0f);
    int angle = int(std::lround(normalizedTurns * 2048.0f)) % 2048;

    if (angle < 0)
    {
        angle += 2048;
    }

    return uint16_t(angle);
}
}

void IndoorWorldRuntime::initialize(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const MonsterProjectileTable &monsterProjectileTable,
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    const ItemTable &itemTable,
    const ChestTable &chestTable,
    Party *pParty,
    IndoorPartyRuntime *pPartyRuntime,
    std::optional<MapDeltaData> *pMapDeltaData,
    std::optional<EventRuntimeState> *pEventRuntimeState,
    GameplayActorService *pGameplayActorService,
    GameplayProjectileService *pGameplayProjectileService,
    GameplayCombatController *pGameplayCombatController,
    const SpriteFrameTable *pActorSpriteFrameTable,
    const SpriteFrameTable *pProjectileSpriteFrameTable,
    const IndoorMapData *pIndoorMapData,
    const DecorationBillboardSet *pIndoorDecorationBillboardSet
)
{
    m_map = map;
    m_mapName = map.name;
    m_pMonsterTable = &monsterTable;
    m_pMonsterProjectileTable = &monsterProjectileTable;
    m_pObjectTable = &objectTable;
    m_pSpellTable = &spellTable;
    m_pItemTable = &itemTable;
    m_pChestTable = &chestTable;
    m_pParty = pParty;
    m_pPartyRuntime = pPartyRuntime;
    m_pMapDeltaData = pMapDeltaData;
    m_pEventRuntimeState = pEventRuntimeState;
    m_pGameplayActorService = pGameplayActorService;
    m_pGameplayProjectileService = pGameplayProjectileService;
    m_pGameplayCombatController = pGameplayCombatController;
    m_pActorSpriteFrameTable = pActorSpriteFrameTable;
    m_pProjectileSpriteFrameTable =
        pProjectileSpriteFrameTable != nullptr ? pProjectileSpriteFrameTable : pActorSpriteFrameTable;
    m_pIndoorMapData = pIndoorMapData;
    m_pIndoorDecorationBillboardSet = pIndoorDecorationBillboardSet;
    if (m_pGameplayProjectileService != nullptr)
    {
        m_pGameplayProjectileService->clear();
    }
    std::random_device randomDevice;
    const uint64_t timeSeed = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    m_sessionChestSeed = randomDevice() ^ uint32_t(timeSeed) ^ uint32_t(timeSeed >> 32);
    m_materializedChestViews.clear();
    m_activeChestView.reset();
    m_mapActorCorpseViews.clear();
    m_activeCorpseView.reset();
    m_mapActorAiStates.clear();
    m_bloodSplats.clear();
    ++m_bloodSplatRevision;
    m_actorUpdateAccumulatorSeconds = 0.0f;
    m_indoorJournalRevealStateValid = false;
    m_cachedGameplayMinimapLinesValid = false;
    invalidateRuntimeGeometryCache();
    materializeInitialMonsterSpawns();
    // On-load event group flags target generated spawn actors too.
    applyEventRuntimeState(true);
    syncMapActorAiStates();
}

void IndoorWorldRuntime::initialize(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const ObjectTable &objectTable,
    const ItemTable &itemTable,
    const ChestTable &chestTable,
    Party *pParty,
    IndoorPartyRuntime *pPartyRuntime,
    std::optional<MapDeltaData> *pMapDeltaData,
    std::optional<EventRuntimeState> *pEventRuntimeState,
    GameplayActorService *pGameplayActorService,
    const SpriteFrameTable *pActorSpriteFrameTable,
    const IndoorMapData *pIndoorMapData,
    const DecorationBillboardSet *pIndoorDecorationBillboardSet
)
{
    m_map = map;
    m_mapName = map.name;
    m_pMonsterTable = &monsterTable;
    m_pMonsterProjectileTable = nullptr;
    m_pObjectTable = &objectTable;
    m_pSpellTable = nullptr;
    m_pItemTable = &itemTable;
    m_pChestTable = &chestTable;
    m_pParty = pParty;
    m_pPartyRuntime = pPartyRuntime;
    m_pMapDeltaData = pMapDeltaData;
    m_pEventRuntimeState = pEventRuntimeState;
    m_pGameplayActorService = pGameplayActorService;
    m_pGameplayProjectileService = nullptr;
    m_pGameplayCombatController = nullptr;
    m_pActorSpriteFrameTable = pActorSpriteFrameTable;
    m_pProjectileSpriteFrameTable = pActorSpriteFrameTable;
    m_pIndoorMapData = pIndoorMapData;
    m_pIndoorDecorationBillboardSet = pIndoorDecorationBillboardSet;
    std::random_device randomDevice;
    const uint64_t timeSeed = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    m_sessionChestSeed = randomDevice() ^ uint32_t(timeSeed) ^ uint32_t(timeSeed >> 32);
    m_materializedChestViews.clear();
    m_activeChestView.reset();
    m_mapActorCorpseViews.clear();
    m_activeCorpseView.reset();
    m_mapActorAiStates.clear();
    m_bloodSplats.clear();
    ++m_bloodSplatRevision;
    m_actorUpdateAccumulatorSeconds = 0.0f;
    m_indoorJournalRevealStateValid = false;
    m_cachedGameplayMinimapLinesValid = false;
    invalidateRuntimeGeometryCache();
    materializeInitialMonsterSpawns();
    // On-load event group flags target generated spawn actors too.
    applyEventRuntimeState(true);
    syncMapActorAiStates();
}

void IndoorWorldRuntime::bindRenderer(IndoorRenderer *pRenderer)
{
    m_pRenderer = pRenderer;
}

void IndoorWorldRuntime::bindGameplayView(IndoorGameView *pView)
{
    m_pGameplayView = pView;
}

void IndoorWorldRuntime::bindEventExecution(
    const EventRuntime *pEventRuntime,
    const std::optional<ScriptedEventProgram> *pLocalEventProgram,
    const std::optional<ScriptedEventProgram> *pGlobalEventProgram)
{
    m_pEventRuntime = pEventRuntime;
    m_pLocalEventProgram = pLocalEventProgram;
    m_pGlobalEventProgram = pGlobalEventProgram;
}

bool IndoorWorldRuntime::executeFaceTriggeredEvent(
    size_t faceIndex,
    FaceAttribute triggerAttribute,
    bool grantItemsToInventory)
{
    EventRuntimeState *pEventRuntimeState = eventRuntimeState();
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (m_pEventRuntime == nullptr
        || pEventRuntimeState == nullptr
        || m_pIndoorMapData == nullptr
        || faceIndex >= m_pIndoorMapData->faces.size())
    {
        return false;
    }

    const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];

    if (face.cogTriggered == 0)
    {
        return false;
    }

    const uint32_t attributes = effectiveIndoorFaceAttributes(face, pMapDeltaData, faceIndex);

    if (!hasFaceAttribute(attributes, triggerAttribute))
    {
        return false;
    }

    const bool executed = m_pEventRuntime->executeEventById(
        m_pLocalEventProgram != nullptr ? *m_pLocalEventProgram : std::optional<ScriptedEventProgram>{},
        m_pGlobalEventProgram != nullptr ? *m_pGlobalEventProgram : std::optional<ScriptedEventProgram>{},
        face.cogTriggered,
        *pEventRuntimeState,
        m_pParty,
        this);

    if (!executed)
    {
        pEventRuntimeState->lastActivationResult =
            "event " + std::to_string(face.cogTriggered) + " unresolved";
        return false;
    }

    applyEventRuntimeState();

    if (m_pParty != nullptr)
    {
        m_pParty->applyEventRuntimeState(*pEventRuntimeState, grantItemsToInventory);
    }

    pEventRuntimeState->lastActivationResult =
        "event " + std::to_string(face.cogTriggered) + " executed";
    return true;
}

void IndoorWorldRuntime::invalidateRuntimeGeometryCache()
{
    m_runtimeGeometryCache.valid = false;
    m_runtimeGeometryCache.vertices.clear();
    m_runtimeGeometryCache.geometryCache = IndoorFaceGeometryCache();
}

void IndoorWorldRuntime::refreshMechanismRuntimeGeometryCache()
{
    if (!m_runtimeGeometryCache.valid || m_pIndoorMapData == nullptr)
    {
        return;
    }

    m_runtimeGeometryCache.vertices =
        buildIndoorMechanismAdjustedVertices(*m_pIndoorMapData, mapDeltaData(), eventRuntimeState());

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    for (const MapDeltaDoor &door : pMapDeltaData->doors)
    {
        for (uint16_t faceId : door.faceIds)
        {
            m_runtimeGeometryCache.geometryCache.invalidateFace(faceId);
        }
    }
}

IndoorWorldRuntime::RuntimeGeometryCache &IndoorWorldRuntime::runtimeGeometryCache() const
{
    if (m_runtimeGeometryCache.valid)
    {
        return m_runtimeGeometryCache;
    }

    m_runtimeGeometryCache.vertices.clear();
    m_runtimeGeometryCache.geometryCache = IndoorFaceGeometryCache();

    if (m_pIndoorMapData != nullptr)
    {
        m_runtimeGeometryCache.vertices =
            buildIndoorMechanismAdjustedVertices(*m_pIndoorMapData, mapDeltaData(), eventRuntimeState());
        m_runtimeGeometryCache.geometryCache.reset(m_pIndoorMapData->faces.size());
    }

    m_runtimeGeometryCache.valid = true;
    return m_runtimeGeometryCache;
}

bool IndoorWorldRuntime::hasIndoorCombatLineOfSight(
    const GameplayWorldPoint &from,
    int16_t fromSectorId,
    const GameplayWorldPoint &to,
    int16_t toSectorId) const
{
    if (m_pIndoorMapData == nullptr)
    {
        return true;
    }

    RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();

    if (runtimeGeometry.vertices.empty())
    {
        return true;
    }

    const int16_t resolvedFromSector =
        resolveIndoorPointSector(
            m_pIndoorMapData,
            runtimeGeometry.vertices,
            &runtimeGeometry.geometryCache,
            {from.x, from.y, from.z},
            fromSectorId);
    const int16_t resolvedToSector =
        resolveIndoorPointSector(
            m_pIndoorMapData,
            runtimeGeometry.vertices,
            &runtimeGeometry.geometryCache,
            {to.x, to.y, to.z},
            toSectorId);

    if (!indoorDetectBetweenObjects(
            *m_pIndoorMapData,
            runtimeGeometry.vertices,
            runtimeGeometry.geometryCache,
            from,
            resolvedFromSector,
            to,
            resolvedToSector))
    {
        return false;
    }

    return !indoorSegmentBlockedByCombatFace(
        *m_pIndoorMapData,
        mapDeltaData(),
        eventRuntimeState(),
        runtimeGeometry.vertices,
        runtimeGeometry.geometryCache,
        from,
        to,
        resolvedFromSector,
        resolvedToSector);
}

bool IndoorWorldRuntime::indoorActorCanApplyPartyMeleeImpact(size_t actorIndex) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr
        || m_pPartyRuntime == nullptr
        || actorIndex >= pMapDeltaData->actors.size()
        || actorIndex >= m_mapActorAiStates.size())
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const MapActorAiState &aiState = m_mapActorAiStates[actorIndex];

    if (actor.hp <= 0 || aiState.motionState == ActorAiMotionState::Dead)
    {
        return false;
    }

    const IndoorMoveState &partyMoveState = m_pPartyRuntime->movementState();
    const float actorTargetZ =
        aiState.preciseZ + std::max(24.0f, static_cast<float>(aiState.collisionHeight) * 0.7f);
    const GameplayWorldPoint actorTargetPoint = {aiState.preciseX, aiState.preciseY, actorTargetZ};
    const GameplayWorldPoint partyTargetPoint =
        {partyMoveState.x, partyMoveState.y, partyMoveState.footZ + PartyTargetHeightOffset};
    const float deltaX = partyTargetPoint.x - actorTargetPoint.x;
    const float deltaY = partyTargetPoint.y - actorTargetPoint.y;
    const float deltaZ = partyTargetPoint.z - actorTargetPoint.z;
    const float edgeDistance =
        std::max(
            0.0f,
            length3d(deltaX, deltaY, deltaZ)
                - static_cast<float>(aiState.collisionRadius)
                - PartyCollisionRadius);

    if (edgeDistance > ActorMeleeRange)
    {
        return false;
    }

    const int16_t actorSectorId = aiState.sectorId >= 0 ? aiState.sectorId : actor.sectorId;
    const int16_t partySectorId =
        partyMoveState.eyeSectorId >= 0 ? partyMoveState.eyeSectorId : partyMoveState.sectorId;
    return hasIndoorCombatLineOfSight(actorTargetPoint, actorSectorId, partyTargetPoint, partySectorId);
}

void IndoorWorldRuntime::syncMapActorAiStates()
{
    MapDeltaData *pMapDeltaData = mapDeltaData();
    const size_t actorCount = pMapDeltaData != nullptr ? pMapDeltaData->actors.size() : 0;

    if (m_mapActorAiStates.size() > actorCount)
    {
        m_mapActorAiStates.resize(actorCount);
    }

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    const std::vector<IndoorVertex> *pVertices = nullptr;
    IndoorFaceGeometryCache *pGeometryCache = nullptr;

    if (m_pIndoorMapData != nullptr && m_mapActorAiStates.size() < actorCount)
    {
        RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();
        pVertices = &runtimeGeometry.vertices;
        pGeometryCache = &runtimeGeometry.geometryCache;
    }

    for (size_t actorIndex = m_mapActorAiStates.size(); actorIndex < actorCount; ++actorIndex)
    {
        if (m_pIndoorMapData != nullptr && pVertices != nullptr && pGeometryCache != nullptr)
        {
            fixIndoorInitialActorPlacement(
                *m_pIndoorMapData,
                *pVertices,
                m_pMonsterTable,
                pMapDeltaData->actors[actorIndex],
                *pGeometryCache);
        }

        m_mapActorAiStates.push_back(
            buildIndoorMapActorAiState(
                pMapDeltaData->actors[actorIndex],
                actorIndex,
                m_pMonsterTable,
                m_pGameplayActorService,
                m_pActorSpriteFrameTable));
    }
}

std::vector<bool> IndoorWorldRuntime::selectIndoorActiveActors(
    const ActorPartyFacts &partyFacts,
    int16_t partySectorId,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();
    std::vector<bool> activeActorMask(pMapDeltaData != nullptr ? pMapDeltaData->actors.size() : 0, false);

    if (pMapDeltaData == nullptr || pMapDeltaData->actors.empty())
    {
        return activeActorMask;
    }

    std::vector<std::pair<size_t, float>> activeActorDistances;
    activeActorDistances.reserve(pMapDeltaData->actors.size());

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
        const MapActorAiState *pAiState =
            actorIndex < m_mapActorAiStates.size() ? &m_mapActorAiStates[actorIndex] : nullptr;

        if (pAiState == nullptr
            || actor.hp <= 0
            || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
        {
            continue;
        }

        const float actorTargetZ = pAiState->preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
        const GameplayWorldPoint actorTargetPoint = {pAiState->preciseX, pAiState->preciseY, actorTargetZ};
        const GameplayWorldPoint partyTargetPoint =
            {partyFacts.position.x, partyFacts.position.y, partyFacts.position.z + PartyTargetHeightOffset};
        const float deltaX = partyTargetPoint.x - actorTargetPoint.x;
        const float deltaY = partyTargetPoint.y - actorTargetPoint.y;
        const float deltaZ = partyTargetPoint.z - actorTargetPoint.z;
        const float distanceToParty =
            std::max(0.0f, length3d(deltaX, deltaY, deltaZ) - static_cast<float>(actor.radius));
        const bool sameSectorAsParty = actor.sectorId >= 0 && actor.sectorId == partySectorId;
        const bool previouslyDetectedParty =
            pAiState->hasDetectedParty || defaultActorHasDetectedParty(actor, pAiState->hostileToParty);
        const bool canDetectParty =
            sameSectorAsParty
            || previouslyDetectedParty
            || (m_pIndoorMapData != nullptr
                && !vertices.empty()
                && indoorDetectBetweenObjects(
                    *m_pIndoorMapData,
                    vertices,
                    geometryCache,
                    actorTargetPoint,
                    actor.sectorId,
                    partyTargetPoint,
                    partySectorId));

        if (sameSectorAsParty || (distanceToParty <= ActiveActorUpdateRange && canDetectParty))
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

    for (size_t index = 0; index < activeActorDistances.size() && index < MaxActiveActorUpdates; ++index)
    {
        activeActorMask[activeActorDistances[index].first] = true;
    }

    return activeActorMask;
}

ActorAiFrameFacts IndoorWorldRuntime::collectIndoorActorAiFrameFacts(float deltaSeconds) const
{
    ActorAiFrameFacts facts = {};
    facts.deltaSeconds = deltaSeconds;
    facts.fixedStepSeconds = ActorUpdateStepSeconds;
    facts.party.collisionRadius = PartyCollisionRadius;
    facts.party.collisionHeight = PartyCollisionHeight;
    facts.party.invisible = false;
    facts.party.hasDispellableBuffs = partyHasDispellableBuffs(m_pParty);

    int16_t partySectorId = -1;

    if (m_pPartyRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
        facts.party.position = GameplayWorldPoint{moveState.x, moveState.y, moveState.footZ};
        partySectorId = moveState.sectorId;
    }

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return facts;
    }

    std::vector<IndoorVertex> emptyVertices;
    IndoorFaceGeometryCache emptyGeometryCache;
    const std::vector<IndoorVertex> *pVertices = &emptyVertices;
    IndoorFaceGeometryCache *pGeometryCache = &emptyGeometryCache;

    if (m_pIndoorMapData != nullptr)
    {
        RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();
        pVertices = &runtimeGeometry.vertices;
        pGeometryCache = &runtimeGeometry.geometryCache;
    }

    const std::vector<bool> activeActorMask =
        selectIndoorActiveActors(facts.party, partySectorId, *pVertices, *pGeometryCache);
    const size_t activeActorCount =
        static_cast<size_t>(std::count(activeActorMask.begin(), activeActorMask.end(), true));
    facts.activeActors.reserve(activeActorCount);
    facts.backgroundActors.reserve(
        pMapDeltaData->actors.size() >= activeActorCount
            ? pMapDeltaData->actors.size() - activeActorCount
            : 0);

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        const bool active = actorIndex < activeActorMask.size() && activeActorMask[actorIndex];
        const std::optional<ActorAiFacts> actorFacts =
            collectIndoorActorAiFacts(
                actorIndex,
                active,
                facts.party,
                *pVertices,
                *pGeometryCache);

        if (!actorFacts)
        {
            continue;
        }

        if (active)
        {
            facts.activeActors.push_back(*actorFacts);
        }
        else
        {
            facts.backgroundActors.push_back(*actorFacts);
        }
    }

    return facts;
}

std::vector<bool> IndoorWorldRuntime::applyIndoorActorAiFrameResult(
    const ActorAiFrameResult &result,
    const GameplayActorAiSystem &actorAiSystem)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();
    const size_t actorCount = pMapDeltaData != nullptr ? pMapDeltaData->actors.size() : 0;
    std::vector<bool> spellEffectsAppliedMask(actorCount, false);
    struct DeferredMeleeAttackRequest
    {
        ActorAttackRequest request = {};
        uint32_t sourceActorId = 0;
    };

    std::vector<DeferredMeleeAttackRequest> deferredMeleeAttackRequests;

    if (pMapDeltaData == nullptr || m_pIndoorMapData == nullptr)
    {
        return spellEffectsAppliedMask;
    }

    IndoorMovementController movementController(*m_pIndoorMapData, m_pMapDeltaData, m_pEventRuntimeState);
    std::vector<IndoorActorCollision> actorColliders = actorMovementCollidersForActorMovement(
        result.activeActorIndices);
    const std::vector<IndoorCylinderCollision> decorationColliders = decorationMovementColliders();
    const std::vector<IndoorCylinderCollision> spriteObjectColliders = spriteObjectMovementColliders();

    if (m_pPartyRuntime != nullptr)
    {
        const IndoorMoveState &partyMoveState = m_pPartyRuntime->movementState();
        actorColliders.push_back(IndoorActorCollision{
            static_cast<size_t>(-1),
            partyMoveState.sectorId,
            partyMoveState.x,
            partyMoveState.y,
            partyMoveState.footZ,
            PartyCollisionRadius * 2.0f,
            PartyCollisionHeight,
            false});
    }

    movementController.setActorColliders(actorColliders);
    movementController.setDecorationColliders(decorationColliders);
    movementController.setSpriteObjectColliders(spriteObjectColliders);

    for (const ActorAiUpdate &update : result.actorUpdates)
    {
        if (update.actorIndex >= actorCount || update.actorIndex >= m_mapActorAiStates.size())
        {
            continue;
        }

        MapDeltaActor &actor = pMapDeltaData->actors[update.actorIndex];
        MapActorAiState &aiState = m_mapActorAiStates[update.actorIndex];

        if (update.state.spellEffects)
        {
            aiState.spellEffects = *update.state.spellEffects;
            spellEffectsAppliedMask[update.actorIndex] = true;
        }

        if (update.state.hostilityType)
        {
            actor.hostilityType = *update.state.hostilityType;
        }

        if (update.state.hostileToParty)
        {
            aiState.hostileToParty = *update.state.hostileToParty;

            if (*update.state.hostileToParty)
            {
                actor.attributes |= static_cast<uint32_t>(EvtActorAttribute::Hostile)
                    | static_cast<uint32_t>(EvtActorAttribute::Aggressor)
                    | static_cast<uint32_t>(EvtActorAttribute::Active)
                    | static_cast<uint32_t>(EvtActorAttribute::FullAi);
            }
        }

        if (update.state.hasDetectedParty)
        {
            aiState.hasDetectedParty = *update.state.hasDetectedParty;
            aiState.spellEffects.hasDetectedParty = *update.state.hasDetectedParty;

            if (*update.state.hasDetectedParty)
            {
                actor.attributes |= static_cast<uint32_t>(EvtActorAttribute::Nearby);
            }
        }

        if (update.state.bloodSplatSpawned)
        {
            if (*update.state.bloodSplatSpawned)
            {
                spawnBloodSplatForActorIfNeeded(update.actorIndex);
            }
            else
            {
                aiState.bloodSplatSpawned = false;
                removeBloodSplat(aiState.actorId);
            }
        }

        if (update.state.motionState)
        {
            aiState.motionState = *update.state.motionState;
        }

        if (update.animation.animationState)
        {
            aiState.animationState = *update.animation.animationState;
            actor.currentActionAnimation = indoorActionAnimationFromActorAi(*update.animation.animationState);
        }

        if (update.animation.animationTimeTicks)
        {
            aiState.animationTimeTicks = *update.animation.animationTimeTicks;
        }

        if (update.animation.resetAnimationTime)
        {
            aiState.animationTimeTicks = 0.0f;
        }

        if (update.state.recoverySeconds)
        {
            aiState.recoverySeconds = *update.state.recoverySeconds;
        }

        if (update.state.attackCooldownSeconds)
        {
            aiState.attackCooldownSeconds = *update.state.attackCooldownSeconds;
        }

        if (update.state.idleDecisionSeconds)
        {
            aiState.idleDecisionSeconds = *update.state.idleDecisionSeconds;
        }

        if (update.state.actionSeconds)
        {
            aiState.actionSeconds = *update.state.actionSeconds;
        }

        if (update.state.idleDecisionCount)
        {
            aiState.idleDecisionCount = *update.state.idleDecisionCount;
        }

        if (update.state.pursueDecisionCount)
        {
            aiState.pursueDecisionCount = *update.state.pursueDecisionCount;
        }

        if (update.state.crowdSideLockRemainingSeconds)
        {
            aiState.crowdSideLockRemainingSeconds = *update.state.crowdSideLockRemainingSeconds;
        }

        if (update.state.crowdNoProgressSeconds)
        {
            aiState.crowdNoProgressSeconds = *update.state.crowdNoProgressSeconds;
        }

        if (update.state.crowdLastEdgeDistance)
        {
            aiState.crowdLastEdgeDistance = *update.state.crowdLastEdgeDistance;
        }

        if (update.state.crowdRetreatRemainingSeconds)
        {
            aiState.crowdRetreatRemainingSeconds = *update.state.crowdRetreatRemainingSeconds;
        }

        if (update.state.crowdStandRemainingSeconds)
        {
            aiState.crowdStandRemainingSeconds = *update.state.crowdStandRemainingSeconds;
        }

        if (update.state.crowdProbeEdgeDistance)
        {
            aiState.crowdProbeEdgeDistance = *update.state.crowdProbeEdgeDistance;
        }

        if (update.state.crowdProbeElapsedSeconds)
        {
            aiState.crowdProbeElapsedSeconds = *update.state.crowdProbeElapsedSeconds;
        }

        if (update.state.attackDecisionCount)
        {
            aiState.attackDecisionCount = *update.state.attackDecisionCount;
        }

        if (update.state.crowdEscapeAttempts)
        {
            aiState.crowdEscapeAttempts = *update.state.crowdEscapeAttempts;
        }

        if (update.state.crowdSideSign)
        {
            aiState.crowdSideSign = *update.state.crowdSideSign;
        }

        if (update.state.attackImpactTriggered)
        {
            aiState.attackImpactTriggered = *update.state.attackImpactTriggered;
        }

        if (update.state.queuedAttackAbility)
        {
            aiState.queuedAttackAbility = *update.state.queuedAttackAbility;
        }

        if (update.movementIntent.action != ActorAiMovementAction::None)
        {
            aiState.moveDirectionX = update.movementIntent.moveDirectionX;
            aiState.moveDirectionY = update.movementIntent.moveDirectionY;
        }

        if (update.movementIntent.updateYaw)
        {
            aiState.yawRadians = update.movementIntent.yawRadians;
        }

        if (update.movementIntent.resetCrowdSteering)
        {
            resetIndoorActorCrowdSteeringState(aiState);
        }

        if (update.movementIntent.clearVelocity
            && aiState.motionState != ActorAiMotionState::Dying
            && aiState.motionState != ActorAiMotionState::Stunned)
        {
            const MonsterTable::MonsterStatsEntry *pStats =
                m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(aiState.monsterId) : nullptr;
            aiState.velocityX = 0.0f;
            aiState.velocityY = 0.0f;

            if (pStats == nullptr
                || pStats->canFly
                || aiState.grounded
                || aiState.motionState == ActorAiMotionState::Dead)
            {
                aiState.velocityZ = 0.0f;
            }
        }

        if (update.movementIntent.applyMovement)
        {
            applyIndoorActorMovementIntegration(
                movementController,
                update.actorIndex,
                update,
                actorAiSystem);
        }
        else
        {
            applyIndoorActorPhysicsStep(movementController, update.actorIndex);
        }

        if (update.attackRequest
            && (update.attackRequest->kind == ActorAiAttackRequestKind::PartyMelee
                || update.attackRequest->kind == ActorAiAttackRequestKind::ActorMelee))
        {
            DeferredMeleeAttackRequest deferredRequest = {};
            deferredRequest.request = *update.attackRequest;
            deferredRequest.sourceActorId = static_cast<uint32_t>(update.actorIndex);
            deferredMeleeAttackRequests.push_back(deferredRequest);
        }

        if (update.state.dead && *update.state.dead)
        {
            actor.hp = 0;
            aiState.motionState = ActorAiMotionState::Dead;
            aiState.animationState = ActorAiAnimationState::Dead;
            aiState.attackImpactTriggered = false;
            actor.currentActionAnimation = indoorActionAnimationFromActorAi(ActorAiAnimationState::Dead);
        }

        actor.x = static_cast<int>(std::lround(aiState.preciseX));
        actor.y = static_cast<int>(std::lround(aiState.preciseY));
        actor.z = static_cast<int>(std::lround(aiState.preciseZ));
    }

    for (const DeferredMeleeAttackRequest &deferredAttackRequest : deferredMeleeAttackRequests)
    {
        const ActorAttackRequest &attackRequest = deferredAttackRequest.request;

        if (attackRequest.kind == ActorAiAttackRequestKind::PartyMelee)
        {
            if (!indoorActorCanApplyPartyMeleeImpact(deferredAttackRequest.sourceActorId))
            {
                continue;
            }

            if (m_pGameplayCombatController != nullptr)
            {
                m_pGameplayCombatController->recordMonsterMeleeImpact(
                    deferredAttackRequest.sourceActorId,
                    attackRequest.damage,
                    attackRequest.attackBonus,
                    attackRequest.damageType,
                    attackRequest.ability);
            }
            else if (m_pParty != nullptr)
            {
                m_pParty->applyDamageToActiveMember(attackRequest.damage, "monster attack");
            }

            continue;
        }

        if (attackRequest.kind != ActorAiAttackRequestKind::ActorMelee
            || attackRequest.targetActorIndex >= actorCount)
        {
            continue;
        }

        MapDeltaActor &targetActor = pMapDeltaData->actors[attackRequest.targetActorIndex];

        if (targetActor.hp <= 0 || attackRequest.damage <= 0)
        {
            continue;
        }

        const int previousHp = targetActor.hp;
        targetActor.hp =
            static_cast<int16_t>(std::max(0, static_cast<int>(targetActor.hp) - attackRequest.damage));

        if (previousHp > 0 && targetActor.hp <= 0)
        {
            beginMapActorDyingState(attackRequest.targetActorIndex, targetActor);
        }
        else if (previousHp > 0 && targetActor.hp < previousHp)
        {
            beginMapActorHitReaction(
                attackRequest.targetActorIndex,
                targetActor,
                &attackRequest.source);
        }
    }

    for (const ActorProjectileRequest &projectileRequest : result.projectileRequests)
    {
        applyIndoorActorProjectileRequest(projectileRequest);
    }

    for (const ActorAudioRequest &audioRequest : result.audioRequests)
    {
        if (audioRequest.actorIndex >= actorCount
            || audioRequest.actorIndex >= m_mapActorAiStates.size()
            || m_pMonsterTable == nullptr
            || m_pEventRuntimeState == nullptr
            || !*m_pEventRuntimeState)
        {
            continue;
        }

        const MapActorAiState &aiState = m_mapActorAiStates[audioRequest.actorIndex];
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(aiState.monsterId);

        if (pStats == nullptr)
        {
            continue;
        }

        uint32_t soundId = 0;

        if (audioRequest.kind == ActorAiAudioRequestKind::Alert)
        {
            soundId = pStats->awareSoundId;
        }
        else if (audioRequest.kind == ActorAiAudioRequestKind::Attack)
        {
            soundId = pStats->attackSoundId;
        }
        else if (audioRequest.kind == ActorAiAudioRequestKind::Hit)
        {
            soundId = pStats->winceSoundId;
        }
        else if (audioRequest.kind == ActorAiAudioRequestKind::Death)
        {
            soundId = pStats->deathSoundId;
        }

        if (soundId == 0)
        {
            continue;
        }

        EventRuntimeState::PendingSound sound = {};
        sound.soundId = soundId;
        sound.x = static_cast<int32_t>(std::lround(audioRequest.position.x));
        sound.y = static_cast<int32_t>(std::lround(audioRequest.position.y));
        sound.positional = true;
        (*m_pEventRuntimeState)->pendingSounds.push_back(sound);
    }

    for (const ActorFxRequest &fxRequest : result.fxRequests)
    {
        if (fxRequest.actorIndex >= actorCount || fxRequest.actorIndex >= m_mapActorAiStates.size())
        {
            continue;
        }

        if (fxRequest.kind == ActorAiFxRequestKind::Death)
        {
            spawnBloodSplatForActorIfNeeded(fxRequest.actorIndex);
        }
        else if (fxRequest.kind == ActorAiFxRequestKind::Buff && m_pRenderer != nullptr)
        {
            const MapActorAiState &aiState = m_mapActorAiStates[fxRequest.actorIndex];
            const uint32_t seed =
                aiState.actorId * 2246822519u
                ^ fxRequest.spellId * 3266489917u
                ^ static_cast<uint32_t>(fxRequest.actorIndex + 1);
            m_pRenderer->worldFxSystem().spawnActorBuffFx(
                fxRequest.spellId,
                seed,
                aiState.preciseX,
                aiState.preciseY,
                aiState.preciseZ,
                static_cast<float>(aiState.collisionHeight),
                std::cos(aiState.yawRadians),
                std::sin(aiState.yawRadians));

            const SpellEntry *pSpellEntry =
                m_pSpellTable != nullptr ? m_pSpellTable->findById(static_cast<int>(fxRequest.spellId)) : nullptr;

            if (pSpellEntry != nullptr && pSpellEntry->effectSoundId > 0 && m_pEventRuntimeState != nullptr)
            {
                EventRuntimeState::PendingSound sound = {};
                sound.soundId = static_cast<uint32_t>(pSpellEntry->effectSoundId);
                sound.x = static_cast<int32_t>(std::lround(aiState.preciseX));
                sound.y = static_cast<int32_t>(std::lround(aiState.preciseY));
                sound.z = static_cast<int32_t>(
                    std::lround(aiState.preciseZ + static_cast<float>(aiState.collisionHeight) * 0.5f));
                sound.positional = true;
                sound.hasExplicitZ = true;
                (*m_pEventRuntimeState)->pendingSounds.push_back(sound);
            }
        }
        else if (fxRequest.kind == ActorAiFxRequestKind::Hit || fxRequest.kind == ActorAiFxRequestKind::Spell)
        {
            spawnImmediateSpellImpactVisual(fxRequest.actorIndex, fxRequest.spellId);
        }
    }

    return spellEffectsAppliedMask;
}

bool IndoorWorldRuntime::applyIndoorActorProjectileRequest(const ActorProjectileRequest &projectileRequest)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();
    const size_t actorCount = pMapDeltaData != nullptr ? pMapDeltaData->actors.size() : 0;

    if (pMapDeltaData == nullptr
        || m_pGameplayProjectileService == nullptr
        || m_pMonsterProjectileTable == nullptr
        || m_pObjectTable == nullptr
        || m_pSpellTable == nullptr
        || projectileRequest.sourceActorIndex >= actorCount
        || projectileRequest.sourceActorIndex >= m_mapActorAiStates.size())
    {
        return false;
    }

    if (projectileRequest.targetKind == ActorAiTargetKind::None)
    {
        return false;
    }

    const MapActorAiState &sourceState = m_mapActorAiStates[projectileRequest.sourceActorIndex];
    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(sourceState.monsterId) : nullptr;

    if (pStats == nullptr)
    {
        return false;
    }

    const GameplayProjectileService::MonsterAttackAbility ability =
        projectileAbilityFromActorAbility(projectileRequest.ability);
    IndoorResolvedProjectileDefinition definition = {};

    if (!resolveIndoorMonsterProjectileDefinition(
            *pStats,
            ability,
            *m_pMonsterProjectileTable,
            *m_pObjectTable,
            *m_pSpellTable,
            definition))
    {
        return false;
    }

    const uint16_t objectSpriteFrameIndex = resolveRuntimeProjectileSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    GameplayProjectileService::ProjectileSpawnRequest spawnRequest = {};
    spawnRequest.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Actor;
    spawnRequest.sourceId = sourceState.actorId;
    spawnRequest.sourceMonsterId = sourceState.monsterId;
    spawnRequest.fromSummonedMonster =
        sourceState.spellEffects.controlMode != GameplayActorControlMode::None;
    spawnRequest.ability = ability;
    spawnRequest.definition = buildIndoorGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    spawnRequest.damage = projectileRequest.damage;
    spawnRequest.attackBonus = projectileRequest.attackBonus;
    spawnRequest.damageType = projectileRequest.damageType;
    spawnRequest.sourceX = sourceState.preciseX;
    spawnRequest.sourceY = sourceState.preciseY;
    spawnRequest.sourceZ =
        sourceState.preciseZ
        + static_cast<float>(std::max<uint16_t>(sourceState.collisionHeight, 1))
            * indoorActorProjectileSourceHeightFactor(projectileRequest.ability);
    spawnRequest.targetX = projectileRequest.target.x;
    spawnRequest.targetY = projectileRequest.target.y;
    spawnRequest.targetZ = projectileRequest.target.z;
    spawnRequest.spawnForwardOffset =
        static_cast<float>(std::max<uint16_t>(sourceState.collisionRadius, 8)) + 8.0f;
    spawnRequest.sectorId = sourceState.sectorId;
    spawnRequest.allowInstantImpact = true;

    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        m_pGameplayProjectileService->spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        m_pGameplayProjectileService->buildProjectileSpawnEffects(spawnResult);

    if (indoorProjectileDebugEnabled())
    {
        std::cout
            << "IndoorProjectileSpawn"
            << " source=actor"
            << " actorIndex=" << projectileRequest.sourceActorIndex
            << " actorId=" << sourceState.actorId
            << " monsterId=" << sourceState.monsterId
            << " kind=" << indoorProjectileSpawnKindName(spawnResult.kind)
            << " accepted=" << (spawnEffects.accepted ? 1 : 0)
            << " projectileId=" << spawnResult.projectile.projectileId
            << " spell=" << definition.spellId
            << " object=\"" << definition.objectName << "\""
            << " sprite=\"" << definition.objectSpriteName << "\""
            << " flags=0x" << std::hex << definition.objectFlags << std::dec
            << " radius=" << definition.radius
            << " height=" << definition.height
            << " speed=" << definition.speed
            << " source=(" << spawnRequest.sourceX << "," << spawnRequest.sourceY << ","
            << spawnRequest.sourceZ << ")"
            << " target=(" << spawnRequest.targetX << "," << spawnRequest.targetY << ","
            << spawnRequest.targetZ << ")"
            << " dir=(" << spawnResult.directionX << "," << spawnResult.directionY << ","
            << spawnResult.directionZ << ")"
            << '\n';
    }

    if (!spawnEffects.accepted)
    {
        return false;
    }

    if (spawnEffects.playReleaseAudio && spawnEffects.releaseAudioRequest)
    {
        pushIndoorProjectileAudioEvent(*spawnEffects.releaseAudioRequest);
    }

    if (spawnEffects.spawnInstantImpact)
    {
        spawnIndoorProjectileImpactVisual(
            spawnResult.projectile,
            {spawnEffects.impactX, spawnEffects.impactY, spawnEffects.impactZ},
            false);
    }

    return true;
}

bool IndoorWorldRuntime::addBloodSplat(uint32_t sourceActorId, float x, float y, float z, float radius)
{
    if (radius <= 0.0f)
    {
        return false;
    }

    removeBloodSplat(sourceActorId);

    BloodSplatState splat = {};
    splat.sourceActorId = sourceActorId;
    splat.x = x;
    splat.y = y;
    splat.z = z;
    splat.radius = radius;
    bakeBloodSplatGeometry(splat);

    if (splat.vertices.empty())
    {
        return false;
    }

    if (m_bloodSplats.size() >= MaxIndoorBloodSplats)
    {
        m_bloodSplats.erase(m_bloodSplats.begin());
    }

    m_bloodSplats.push_back(std::move(splat));
    ++m_bloodSplatRevision;
    return true;
}

void IndoorWorldRuntime::bakeBloodSplatGeometry(BloodSplatState &splat) const
{
    splat.vertices.clear();

    if (splat.radius <= 0.0f || m_pIndoorMapData == nullptr)
    {
        return;
    }

    RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();

    if (runtimeGeometry.vertices.empty())
    {
        return;
    }

    const float diameter = splat.radius * 2.0f;
    const float cellSize = diameter / static_cast<float>(BloodSplatGridResolution);
    const float cellHalfSize = cellSize * 0.5f;
    const float surfaceHeightTolerance =
        std::max(BloodSplatMinSurfaceHeightTolerance, splat.radius * 0.5f);

    splat.vertices.reserve(BloodSplatGridResolution * BloodSplatGridResolution * 12);

    const auto appendVertex =
        [&splat](const bx::Vec3 &position, float u, float v)
        {
            BloodSplatState::Vertex vertex = {};
            vertex.x = position.x;
            vertex.y = position.y;
            vertex.z = position.z;
            vertex.u = u;
            vertex.v = v;
            splat.vertices.push_back(vertex);
        };

    const auto sampleWorldPoint =
        [this, &splat, &runtimeGeometry, surfaceHeightTolerance](float x, float y, bx::Vec3 &point) -> bool
        {
            const IndoorFloorSample floor = sampleIndoorFloor(
                *m_pIndoorMapData,
                runtimeGeometry.vertices,
                x,
                y,
                splat.z + 64.0f,
                128.0f,
                256.0f,
                std::nullopt,
                nullptr,
                &runtimeGeometry.geometryCache);

            if (!floor.hasFloor || std::abs(floor.height - splat.z) > surfaceHeightTolerance)
            {
                return false;
            }

            point = {x, y, floor.height + BloodSplatHeightOffset + 1.0f};
            return true;
        };

    for (size_t yIndex = 0; yIndex < BloodSplatGridResolution; ++yIndex)
    {
        const float v0 = static_cast<float>(yIndex) / static_cast<float>(BloodSplatGridResolution);
        const float v1 = static_cast<float>(yIndex + 1) / static_cast<float>(BloodSplatGridResolution);
        const float localY0 = (v0 - 0.5f) * diameter;
        const float localY1 = (v1 - 0.5f) * diameter;

        for (size_t xIndex = 0; xIndex < BloodSplatGridResolution; ++xIndex)
        {
            const float u0 = static_cast<float>(xIndex) / static_cast<float>(BloodSplatGridResolution);
            const float u1 = static_cast<float>(xIndex + 1) / static_cast<float>(BloodSplatGridResolution);
            const float localX0 = (u0 - 0.5f) * diameter;
            const float localX1 = (u1 - 0.5f) * diameter;
            const float localCenterX = (localX0 + localX1) * 0.5f;
            const float localCenterY = (localY0 + localY1) * 0.5f;
            const float nearestX = std::max(std::abs(localCenterX) - cellHalfSize, 0.0f);
            const float nearestY = std::max(std::abs(localCenterY) - cellHalfSize, 0.0f);

            if (nearestX * nearestX + nearestY * nearestY > splat.radius * splat.radius)
            {
                continue;
            }

            bx::Vec3 topLeft = {0.0f, 0.0f, 0.0f};
            bx::Vec3 topRight = {0.0f, 0.0f, 0.0f};
            bx::Vec3 bottomLeft = {0.0f, 0.0f, 0.0f};
            bx::Vec3 bottomRight = {0.0f, 0.0f, 0.0f};
            bx::Vec3 center = {0.0f, 0.0f, 0.0f};
            const float centerU = (u0 + u1) * 0.5f;
            const float centerV = (v0 + v1) * 0.5f;

            if (!sampleWorldPoint(splat.x + localX0, splat.y + localY0, topLeft)
                || !sampleWorldPoint(splat.x + localX1, splat.y + localY0, topRight)
                || !sampleWorldPoint(splat.x + localX0, splat.y + localY1, bottomLeft)
                || !sampleWorldPoint(splat.x + localX1, splat.y + localY1, bottomRight)
                || !sampleWorldPoint(splat.x + localCenterX, splat.y + localCenterY, center))
            {
                continue;
            }

            appendVertex(topLeft, u0, v0);
            appendVertex(topRight, u1, v0);
            appendVertex(center, centerU, centerV);

            appendVertex(topRight, u1, v0);
            appendVertex(bottomRight, u1, v1);
            appendVertex(center, centerU, centerV);

            appendVertex(bottomRight, u1, v1);
            appendVertex(bottomLeft, u0, v1);
            appendVertex(center, centerU, centerV);

            appendVertex(bottomLeft, u0, v1);
            appendVertex(topLeft, u0, v0);
            appendVertex(center, centerU, centerV);
        }
    }
}

void IndoorWorldRuntime::spawnBloodSplatForActorIfNeeded(size_t actorIndex)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr
        || actorIndex >= pMapDeltaData->actors.size()
        || actorIndex >= m_mapActorAiStates.size()
        || m_pMonsterTable == nullptr)
    {
        return;
    }

    MapActorAiState &aiState = m_mapActorAiStates[actorIndex];

    if (aiState.bloodSplatSpawned)
    {
        return;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(aiState.monsterId);

    if (pStats == nullptr || !pStats->bloodSplatOnDeath)
    {
        return;
    }

    float splatZ = aiState.preciseZ;

    if (m_pIndoorMapData != nullptr)
    {
        RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();
        const std::optional<int16_t> preferredSector =
            aiState.sectorId >= 0 ? std::optional<int16_t>(aiState.sectorId) : std::nullopt;

        IndoorFloorSample floor = {};

        if (aiState.supportFaceIndex != static_cast<size_t>(-1)
            && aiState.supportFaceIndex < m_pIndoorMapData->faces.size())
        {
            floor = sampleIndoorFloorOnFace(
                *m_pIndoorMapData,
                runtimeGeometry.vertices,
                aiState.supportFaceIndex,
                aiState.preciseX,
                aiState.preciseY,
                aiState.preciseZ + 64.0f,
                128.0f,
                512.0f,
                nullptr,
                &runtimeGeometry.geometryCache);
        }

        if (!floor.hasFloor)
        {
            floor = sampleIndoorFloor(
                *m_pIndoorMapData,
                runtimeGeometry.vertices,
                aiState.preciseX,
                aiState.preciseY,
                aiState.preciseZ + 64.0f,
                128.0f,
                512.0f,
                preferredSector,
                nullptr,
                &runtimeGeometry.geometryCache);
        }

        if (floor.hasFloor)
        {
            splatZ = floor.height;
        }
    }

    const float splatRadius = std::max(32.0f, static_cast<float>(aiState.collisionRadius) * 1.5f);

    if (addBloodSplat(aiState.actorId, aiState.preciseX, aiState.preciseY, splatZ, splatRadius))
    {
        aiState.bloodSplatSpawned = true;
    }
}

void IndoorWorldRuntime::removeBloodSplat(uint32_t sourceActorId)
{
    const size_t previousCount = m_bloodSplats.size();
    m_bloodSplats.erase(
        std::remove_if(
            m_bloodSplats.begin(),
            m_bloodSplats.end(),
            [sourceActorId](const BloodSplatState &splat)
            {
                return splat.sourceActorId == sourceActorId;
            }),
        m_bloodSplats.end());

    if (m_bloodSplats.size() != previousCount)
    {
        ++m_bloodSplatRevision;
    }
}

void IndoorWorldRuntime::pushIndoorProjectileAudioEvent(
    const GameplayProjectileService::ProjectileAudioRequest &audioRequest)
{
    if (audioRequest.soundId == 0 || m_pEventRuntimeState == nullptr || !*m_pEventRuntimeState)
    {
        return;
    }

    EventRuntimeState::PendingSound sound = {};
    sound.soundId = audioRequest.soundId;
    sound.x = static_cast<int32_t>(std::lround(audioRequest.x));
    sound.y = static_cast<int32_t>(std::lround(audioRequest.y));
    sound.positional = audioRequest.positional;
    (*m_pEventRuntimeState)->pendingSounds.push_back(sound);
}

bool IndoorWorldRuntime::projectileSourceIsFriendlyToActor(
    const GameplayProjectileService::ProjectileState &projectile,
    const MapActorAiState &actor) const
{
    GameplayProjectileService::ProjectileActorRelationFacts facts = {};
    facts.eventSource = projectile.sourceId == EventSpellSourceId;
    facts.targetHostileToParty = actor.spellEffects.controlMode != GameplayActorControlMode::None
        ? actor.spellEffects.hostileToParty
        : actor.hostileToParty;

    if (m_pGameplayActorService != nullptr)
    {
        facts.targetPartyControlled =
            m_pGameplayActorService->isPartyControlledActor(actor.spellEffects.controlMode);
        facts.sourceMonsterKnown = projectile.sourceMonsterId != 0;
        facts.sourceMonsterFriendlyToTarget = facts.sourceMonsterKnown
            && m_pGameplayActorService->monsterIdsAreFriendly(projectile.sourceMonsterId, actor.monsterId);
    }

    return m_pGameplayProjectileService != nullptr
        && m_pGameplayProjectileService->isProjectileSourceFriendlyToActor(projectile, facts);
}

GameplayProjectileService::ProjectileFrameFacts IndoorWorldRuntime::collectIndoorProjectileFrameFacts(
    const GameplayProjectileService::ProjectileState &projectile,
    float deltaSeconds,
    const std::vector<IndoorVertex> &projectileVertices,
    IndoorFaceGeometryCache &projectileGeometryCache) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();
    const IndoorMoveState *pPartyMoveState =
        m_pPartyRuntime != nullptr ? &m_pPartyRuntime->movementState() : nullptr;
    const GameplayWorldPoint partyPosition =
        pPartyMoveState != nullptr
            ? GameplayWorldPoint{pPartyMoveState->x, pPartyMoveState->y, pPartyMoveState->footZ}
            : GameplayWorldPoint{};

    GameplayProjectileService::ProjectileState predictedProjectile = projectile;
    const bool lifetimeExpired =
        m_pGameplayProjectileService->advanceProjectileLifetime(predictedProjectile, deltaSeconds);

    GameplayProjectileService::ProjectileFrameFacts facts = {};
    facts.deltaSeconds = deltaSeconds;
    facts.gravity = IndoorProjectileGravity;
    facts.bounceFactor = IndoorProjectileBounceFactor;
    facts.bounceStopVelocity = IndoorProjectileBounceStopVelocity;
    facts.groundDamping = IndoorProjectileGroundDamping;
    facts.partyPosition = partyPosition;
    facts.partyCollisionRadius = PartyCollisionRadius;
    facts.partyCollisionHeight = PartyCollisionHeight;
    facts.canHitParty = pPartyMoveState != nullptr;

    GameplayProjectileService::ProjectilePartyImpactDamageInput damageInput = {};
    damageInput.sourceKind = projectile.sourceKind;
    damageInput.eventSource = projectile.sourceId == EventSpellSourceId;
    damageInput.projectileDamage = projectile.damage;
    damageInput.spellId = projectile.spellId;
    damageInput.skillLevel = projectile.skillLevel;
    damageInput.monsterAbility = projectile.ability;

    if (projectile.sourceKind != GameplayProjectileService::ProjectileState::SourceKind::Party
        && m_pMonsterTable != nullptr)
    {
        const MonsterTable::MonsterStatsEntry *pStats = nullptr;

        if (projectile.sourceMonsterId != 0)
        {
            pStats = m_pMonsterTable->findStatsById(projectile.sourceMonsterId);
        }
        else
        {
            for (const MapActorAiState &aiState : m_mapActorAiStates)
            {
                if (aiState.actorId == projectile.sourceId)
                {
                    pStats = m_pMonsterTable->findStatsById(aiState.monsterId);
                    break;
                }
            }
        }

        if (pStats != nullptr)
        {
            damageInput.hasMonsterFacts = true;
            damageInput.monsterLevel = pStats->level;
            damageInput.attack1Damage.diceRolls = pStats->attack1Damage.diceRolls;
            damageInput.attack1Damage.diceSides = pStats->attack1Damage.diceSides;
            damageInput.attack1Damage.bonus = pStats->attack1Damage.bonus;
            damageInput.attack2Damage.diceRolls = pStats->attack2Damage.diceRolls;
            damageInput.attack2Damage.diceSides = pStats->attack2Damage.diceSides;
            damageInput.attack2Damage.bonus = pStats->attack2Damage.bonus;

            if (m_pSpellTable != nullptr)
            {
                if (const SpellEntry *pSpellEntry = m_pSpellTable->findByName(pStats->spell1Name))
                {
                    damageInput.spell1Damage.baseDamage = pSpellEntry->damageBase;
                    damageInput.spell1Damage.diceSides = pSpellEntry->damageDiceSides;
                    damageInput.spell1Damage.skillLevel = pStats->spell1SkillLevel;
                    damageInput.spell1Damage.skillMastery = pStats->spell1SkillMastery;
                }

                if (const SpellEntry *pSpellEntry = m_pSpellTable->findByName(pStats->spell2Name))
                {
                    damageInput.spell2Damage.baseDamage = pSpellEntry->damageBase;
                    damageInput.spell2Damage.diceSides = pSpellEntry->damageDiceSides;
                    damageInput.spell2Damage.skillLevel = pStats->spell2SkillLevel;
                    damageInput.spell2Damage.skillMastery = pStats->spell2SkillMastery;
                }
            }
        }
    }

    facts.nonPartyProjectileDamage =
        m_pGameplayProjectileService->resolveProjectilePartyImpactDamage(damageInput);

    size_t directActorIndex = static_cast<size_t>(-1);

    if (!lifetimeExpired)
    {
        facts.motion =
            m_pGameplayProjectileService->advanceProjectileMotion(
                predictedProjectile,
                deltaSeconds,
                IndoorProjectileGravity);

        const GameplayWorldPoint segmentStart = {
            facts.motion.startX,
            facts.motion.startY,
            facts.motion.startZ
        };
        const GameplayWorldPoint segmentEnd = {
            facts.motion.endX,
            facts.motion.endY,
            facts.motion.endZ
        };
        std::optional<IndoorProjectileCollisionCandidate> bestCollision;

        if (m_pIndoorMapData != nullptr)
        {
            bestCollision =
                findProjectileIndoorFaceHit(
                    *m_pIndoorMapData,
                    pMapDeltaData,
                    eventRuntimeState(),
                    projectileVertices,
                    projectileGeometryCache,
                    projectile,
                    segmentStart,
                    segmentEnd,
                    projectile.sectorId >= 0
                        ? std::optional<int16_t>(projectile.sectorId)
                        : std::nullopt);
        }

        if (facts.canHitParty && m_pGameplayProjectileService->canProjectileCollideWithParty(projectile))
        {
            const GameplayWorldPoint partyCenter = {
                partyPosition.x,
                partyPosition.y,
                partyPosition.z + PartyCollisionHeight * 0.5f
            };
            std::optional<IndoorProjectileCollisionCandidate> partyHit =
                findProjectileCylinderHit(
                    segmentStart,
                    segmentEnd,
                    partyCenter,
                    PartyCollisionRadius + static_cast<float>(projectile.radius),
                    PartyCollisionHeight * 0.5f);

            if (partyHit)
            {
                partyHit->kind = GameplayProjectileService::ProjectileFrameCollisionKind::Party;

                if (!bestCollision || projectileHitSortsBefore(*partyHit, *bestCollision))
                {
                    bestCollision = *partyHit;
                }
            }
        }

        if (pMapDeltaData != nullptr)
        {
            for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
            {
                if (actorIndex >= m_mapActorAiStates.size())
                {
                    continue;
                }

                GameplayRuntimeActorState actorState = {};
                if (!actorRuntimeState(actorIndex, actorState))
                {
                    continue;
                }

                GameplayActorService fallbackActorService = {};
                const GameplayActorService *pActorService =
                    m_pGameplayActorService != nullptr ? m_pGameplayActorService : &fallbackActorService;
                const bool unavailable =
                    indoorActorUnavailableForCombat(
                        pMapDeltaData->actors[actorIndex],
                        m_mapActorAiStates[actorIndex],
                        *pActorService);
                const GameplayProjectileService::ProjectileCollisionActorFacts actorFacts = {
                    m_mapActorAiStates[actorIndex].actorId,
                    actorState.isDead,
                    unavailable,
                    projectile.sourceKind != GameplayProjectileService::ProjectileState::SourceKind::Party
                        && projectileSourceIsFriendlyToActor(projectile, m_mapActorAiStates[actorIndex])
                };

                if (!m_pGameplayProjectileService->canProjectileCollideWithActor(projectile, actorFacts))
                {
                    continue;
                }

                const GameplayWorldPoint actorCenter = {
                    actorState.preciseX,
                    actorState.preciseY,
                    actorState.preciseZ + static_cast<float>(actorState.height) * 0.5f
                };
                const float hitRadius =
                    actorIndex < m_mapActorAiStates.size()
                        ? static_cast<float>(m_mapActorAiStates[actorIndex].projectileHitRadius)
                        : indoorProjectileActorHitRadius(
                            m_pMonsterTable,
                            pMapDeltaData->actors[actorIndex],
                            actorState);
                std::optional<IndoorProjectileCollisionCandidate> actorHit =
                    findProjectileCylinderHit(
                        segmentStart,
                        segmentEnd,
                        actorCenter,
                        hitRadius + static_cast<float>(projectile.radius),
                        static_cast<float>(std::max<uint16_t>(actorState.height, 16)) * 0.5f);

                if (!actorHit)
                {
                    continue;
                }

                actorHit->kind = GameplayProjectileService::ProjectileFrameCollisionKind::Actor;
                actorHit->actorIndex = actorIndex;

                if (!bestCollision || projectileHitSortsBefore(*actorHit, *bestCollision))
                {
                    bestCollision = *actorHit;
                }
            }
        }

        if (bestCollision)
        {
            if (indoorProjectileDebugEnabled()
                && bestCollision->kind == GameplayProjectileService::ProjectileFrameCollisionKind::World)
            {
                const IndoorFace *pFace =
                    bestCollision->faceIndex < m_pIndoorMapData->faces.size()
                        ? &m_pIndoorMapData->faces[bestCollision->faceIndex]
                        : nullptr;
                const uint32_t effectiveAttributes =
                    pFace != nullptr
                        ? effectiveIndoorFaceAttributes(*pFace, pMapDeltaData, bestCollision->faceIndex)
                        : 0u;
                const IndoorFaceGeometryData *pGeometry =
                    pFace != nullptr
                        ? projectileGeometryCache.geometryForFace(
                            *m_pIndoorMapData,
                            projectileVertices,
                            bestCollision->faceIndex)
                        : nullptr;

                std::cout
                    << "IndoorProjectileWorldHit"
                    << " id=" << projectile.projectileId
                    << " spell=" << projectile.spellId
                    << " object=\"" << projectile.objectName << "\""
                    << " sprite=\"" << projectile.objectSpriteName << "\""
                    << " face=" << bestCollision->faceIndex
                    << " point=(" << bestCollision->point.x << "," << bestCollision->point.y << ","
                    << bestCollision->point.z << ")"
                    << " progress=" << bestCollision->progress
                    << " attrs=0x" << std::hex << effectiveAttributes << std::dec
                    << " rawPortal=" << (pFace != nullptr && pFace->isPortal ? 1 : 0)
                    << " effectivePortal="
                    << (hasFaceAttribute(effectiveAttributes, FaceAttribute::IsPortal) ? 1 : 0)
                    << " invisible="
                    << (hasFaceAttribute(effectiveAttributes, FaceAttribute::Invisible) ? 1 : 0)
                    << " untouchable="
                    << (hasFaceAttribute(effectiveAttributes, FaceAttribute::Untouchable) ? 1 : 0)
                    << " kind="
                    << (pGeometry != nullptr && pGeometry->kind == IndoorFaceKind::Floor ? "floor"
                        : pGeometry != nullptr && pGeometry->kind == IndoorFaceKind::Ceiling ? "ceiling"
                        : pGeometry != nullptr && pGeometry->kind == IndoorFaceKind::Wall ? "wall"
                        : "unknown")
                    << " normal=(" << bestCollision->normalX << "," << bestCollision->normalY << ","
                    << bestCollision->normalZ << ")"
                    << " requiresDownwardBounce="
                    << (bestCollision->requiresDownwardVelocityToBounce ? 1 : 0)
                    << '\n';
            }

            facts.hasCollision = true;
            facts.collision.kind = bestCollision->kind;
            facts.collision.point = bestCollision->point;
            facts.collision.actorIndex = bestCollision->actorIndex;

            if (bestCollision->kind == GameplayProjectileService::ProjectileFrameCollisionKind::World)
            {
                facts.collision.colliderName = "indoor face";
                facts.collision.worldFaceIndex = bestCollision->faceIndex;
                facts.collision.bounceSurface.canBounce = true;
                facts.collision.bounceSurface.requiresDownwardVelocity =
                    bestCollision->requiresDownwardVelocityToBounce;
                facts.collision.bounceSurface.normalX = bestCollision->normalX;
                facts.collision.bounceSurface.normalY = bestCollision->normalY;
                facts.collision.bounceSurface.normalZ = bestCollision->normalZ;
            }

            if (bestCollision->kind == GameplayProjectileService::ProjectileFrameCollisionKind::Actor
                && bestCollision->actorIndex < mapActorCount())
            {
                GameplayActorInspectState inspectState = {};
                facts.collision.actorId =
                    bestCollision->actorIndex < m_mapActorAiStates.size()
                        ? m_mapActorAiStates[bestCollision->actorIndex].actorId
                        : static_cast<uint32_t>(bestCollision->actorIndex);
                facts.collision.targetArmorClass =
                    actorInspectState(bestCollision->actorIndex, 0, inspectState) ? inspectState.armorClass : 0;
                facts.collision.damageMultiplier = 1;
                if (bestCollision->actorIndex < m_mapActorAiStates.size())
                {
                    const GameplayActorService actorService = {};
                    facts.collision.halfIncomingMissileDamage =
                        actorService.halveIncomingMissileDamage(
                            m_mapActorAiStates[bestCollision->actorIndex].spellEffects);
                }
                facts.collision.targetDistance =
                    length3d(
                        projectile.sourceX - bestCollision->point.x,
                        projectile.sourceY - bestCollision->point.y,
                        projectile.sourceZ - bestCollision->point.z);
                directActorIndex = bestCollision->actorIndex;
            }
        }
    }

    if (pMapDeltaData != nullptr)
    {
        facts.areaActors.reserve(pMapDeltaData->actors.size());

        for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
        {
            if (actorIndex >= m_mapActorAiStates.size())
            {
                continue;
            }

            GameplayRuntimeActorState actorState = {};
            if (!actorRuntimeState(actorIndex, actorState))
            {
                continue;
            }

            GameplayProjectileService::ProjectileAreaImpactActorFacts actorFacts = {};
            actorFacts.actorIndex = actorIndex;
            actorFacts.actorId = m_mapActorAiStates[actorIndex].actorId;
            actorFacts.x = actorState.preciseX;
            actorFacts.y = actorState.preciseY;
            actorFacts.z = actorState.preciseZ;
            actorFacts.radius = actorState.radius;
            actorFacts.height = actorState.height;
            actorFacts.unavailableForCombat = actorState.isDead || actorState.isInvisible;
            actorFacts.friendlyToProjectileSource =
                projectile.sourceKind != GameplayProjectileService::ProjectileState::SourceKind::Party
                && projectileSourceIsFriendlyToActor(projectile, m_mapActorAiStates[actorIndex]);
            actorFacts.directImpactActor = actorIndex == directActorIndex;
            facts.areaActors.push_back(actorFacts);
        }
    }

    return facts;
}

void IndoorWorldRuntime::applyIndoorProjectileFrameResult(
    GameplayProjectileService::ProjectileState &projectile,
    const GameplayProjectileService::ProjectileFrameFacts &facts,
    const GameplayProjectileService::ProjectileFrameResult &frameResult)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (facts.hasCollision
        && facts.collision.kind == GameplayProjectileService::ProjectileFrameCollisionKind::World
        && facts.collision.worldFaceIndex != static_cast<size_t>(-1))
    {
        executeFaceTriggeredEvent(facts.collision.worldFaceIndex, FaceAttribute::TriggerByObject, false);
    }

    if (frameResult.directPartyDamage)
    {
        if (m_pGameplayCombatController != nullptr)
        {
            m_pGameplayCombatController->recordPartyProjectileImpact(
                projectile.sourceId,
                *frameResult.directPartyDamage,
                projectile.attackBonus,
                projectile.spellId,
                false,
                projectile.damageType);
        }
        else if (m_pParty != nullptr)
        {
            m_pParty->applyDamageToActiveMember(*frameResult.directPartyDamage, "monster projectile");
        }
    }

    if (frameResult.directActorImpact
        && frameResult.directActorImpact->actorIndex < mapActorCount()
        && pMapDeltaData != nullptr)
    {
        const GameplayProjectileService::ProjectileDirectActorImpact &impact =
            *frameResult.directActorImpact;

        if (impact.applyPartyProjectileDamage)
        {
            int appliedDamage = impact.damage;
            const MonsterTable::MonsterStatsEntry *pStats = nullptr;
            if (impact.actorIndex < pMapDeltaData->actors.size() && m_pMonsterTable != nullptr)
            {
                pStats = m_pMonsterTable->findStatsById(resolveIndoorActorStatsId(pMapDeltaData->actors[impact.actorIndex]));
            }

            if (pStats != nullptr)
            {
                std::mt19937 rng(
                    projectile.projectileId
                    ^ static_cast<uint32_t>(impact.actorId * 2654435761u)
                    ^ static_cast<uint32_t>(std::max(0, impact.damage)));
                appliedDamage = GameMechanics::resolveMonsterIncomingDamage(
                    impact.damage,
                    projectile.damageType,
                    pStats->level,
                    monsterResistanceForDamageType(*pStats, projectile.damageType),
                    rng);
            }

            const int beforeHp =
                impact.actorIndex < pMapDeltaData->actors.size() ? pMapDeltaData->actors[impact.actorIndex].hp : 0;
            applyPartyAttackMeleeDamage(
                impact.actorIndex,
                appliedDamage,
                {projectile.sourceX, projectile.sourceY, projectile.sourceZ});
            const int afterHp =
                impact.actorIndex < pMapDeltaData->actors.size() ? pMapDeltaData->actors[impact.actorIndex].hp : 0;

            if (m_pGameplayCombatController != nullptr)
            {
                m_pGameplayCombatController->recordPartyProjectileActorImpact(
                    projectile.sourceId,
                    projectile.sourcePartyMemberIndex,
                    impact.actorId,
                    appliedDamage,
                    projectile.spellId,
                    impact.hit,
                    beforeHp > 0 && afterHp <= 0);
            }
        }
        else if (impact.queuePartyProjectileActorEvent && m_pGameplayCombatController != nullptr)
        {
            m_pGameplayCombatController->recordPartyProjectileActorImpact(
                projectile.sourceId,
                projectile.sourcePartyMemberIndex,
                impact.actorId,
                impact.damage,
                projectile.spellId,
                impact.hit,
                false);
        }
        else if (impact.applyNonPartyProjectileDamage && impact.damage > 0)
        {
            MapDeltaActor &targetActor = pMapDeltaData->actors[impact.actorIndex];
            const int previousHp = targetActor.hp;
            targetActor.hp = static_cast<int16_t>(
                std::max(0, static_cast<int>(targetActor.hp) - impact.damage));

            if (previousHp > 0 && targetActor.hp <= 0)
            {
                beginMapActorDyingState(impact.actorIndex, targetActor);
            }
            else if (previousHp > 0 && targetActor.hp < previousHp)
            {
                const GameplayWorldPoint sourcePoint = {projectile.sourceX, projectile.sourceY, projectile.sourceZ};
                beginMapActorHitReaction(impact.actorIndex, targetActor, &sourcePoint);
            }
        }
    }

    if (frameResult.areaImpact)
    {
        const GameplayProjectileService::ProjectileFrameAreaImpactResult &areaImpact = *frameResult.areaImpact;
        RuntimeGeometryCache *pRuntimeGeometry = nullptr;
        int16_t impactSectorId = projectile.sectorId;

        if (m_pIndoorMapData != nullptr)
        {
            pRuntimeGeometry = &runtimeGeometryCache();

            if (impactSectorId < 0 && !pRuntimeGeometry->vertices.empty())
            {
                impactSectorId =
                    findIndoorSectorForPoint(
                        *m_pIndoorMapData,
                        pRuntimeGeometry->vertices,
                        {areaImpact.point.x, areaImpact.point.y, areaImpact.point.z},
                        &pRuntimeGeometry->geometryCache,
                        false).value_or(-1);
            }
        }

        const auto areaImpactHasLineOfSight =
            [this, pRuntimeGeometry, impactSectorId, &areaImpact](
                const GameplayWorldPoint &target,
                int16_t targetSectorId)
            {
                if (m_pIndoorMapData == nullptr || pRuntimeGeometry == nullptr || pRuntimeGeometry->vertices.empty())
                {
                    return true;
                }

                if (impactSectorId < 0 || targetSectorId < 0)
                {
                    return false;
                }

                return impactSectorId == targetSectorId
                    || indoorDetectBetweenObjects(
                        *m_pIndoorMapData,
                        pRuntimeGeometry->vertices,
                        pRuntimeGeometry->geometryCache,
                        areaImpact.point,
                        impactSectorId,
                        target,
                        targetSectorId);
            };

        if (areaImpact.impact.hitParty && m_pParty != nullptr)
        {
            const IndoorMoveState *pPartyMoveState =
                m_pPartyRuntime != nullptr ? &m_pPartyRuntime->movementState() : nullptr;
            const int16_t partySectorId =
                pPartyMoveState != nullptr
                    ? (pPartyMoveState->sectorId >= 0 ? pPartyMoveState->sectorId : pPartyMoveState->eyeSectorId)
                    : int16_t(-1);
            const GameplayWorldPoint partyTarget = {
                pPartyMoveState != nullptr ? pPartyMoveState->x : 0.0f,
                pPartyMoveState != nullptr ? pPartyMoveState->y : 0.0f,
                pPartyMoveState != nullptr ? pPartyMoveState->footZ + PartyCollisionHeight * 0.5f : 0.0f};

            if (areaImpactHasLineOfSight(partyTarget, partySectorId))
            {
                if (m_pGameplayCombatController != nullptr)
                {
                    m_pGameplayCombatController->recordPartyProjectileImpact(
                        projectile.sourceId,
                        areaImpact.impact.partyDamage,
                        projectile.attackBonus,
                        projectile.spellId,
                        true,
                        projectile.damageType);
                }
                else if (m_pParty != nullptr)
                {
                    m_pParty->applyDamageToActiveMember(areaImpact.impact.partyDamage, "projectile splash");
                }
            }
        }

        if (pMapDeltaData != nullptr)
        {
            for (const GameplayProjectileService::ProjectileAreaImpactActorHit &actorHit :
                 areaImpact.impact.actorHits)
            {
                if (actorHit.actorIndex >= pMapDeltaData->actors.size())
                {
                    continue;
                }

                MapDeltaActor &targetActor = pMapDeltaData->actors[actorHit.actorIndex];
                GameplayRuntimeActorState actorState = {};

                if (!actorRuntimeState(actorHit.actorIndex, actorState))
                {
                    continue;
                }

                int16_t actorSectorId = targetActor.sectorId;

                if (actorHit.actorIndex < m_mapActorAiStates.size()
                    && m_mapActorAiStates[actorHit.actorIndex].sectorId >= 0)
                {
                    actorSectorId = m_mapActorAiStates[actorHit.actorIndex].sectorId;
                }

                const GameplayWorldPoint actorTarget = {
                    actorState.preciseX,
                    actorState.preciseY,
                    actorState.preciseZ + std::max(24.0f, static_cast<float>(actorState.height) * 0.7f)};

                if (!areaImpactHasLineOfSight(actorTarget, actorSectorId))
                {
                    continue;
                }

                if (targetActor.hp > 0 && actorHit.damage > 0)
                {
                    if (projectile.sourceKind == GameplayProjectileService::ProjectileState::SourceKind::Party)
                    {
                        int appliedDamage = actorHit.damage;
                        const MonsterTable::MonsterStatsEntry *pStats =
                            m_pMonsterTable != nullptr
                                ? m_pMonsterTable->findStatsById(resolveIndoorActorStatsId(targetActor))
                                : nullptr;

                        if (pStats != nullptr)
                        {
                            std::mt19937 rng(
                                projectile.projectileId
                                ^ static_cast<uint32_t>((actorHit.actorIndex + 1) * 2654435761u)
                                ^ static_cast<uint32_t>(std::max(0, actorHit.damage)));
                            appliedDamage = GameMechanics::resolveMonsterIncomingDamage(
                                actorHit.damage,
                                projectile.damageType,
                                pStats->level,
                                monsterResistanceForDamageType(*pStats, projectile.damageType),
                                rng);
                        }

                        const int previousHp = targetActor.hp;
                        applyPartyAttackMeleeDamage(
                            actorHit.actorIndex,
                            appliedDamage,
                            {projectile.sourceX, projectile.sourceY, projectile.sourceZ});

                        if (m_pGameplayCombatController != nullptr)
                        {
                            const uint32_t actorId =
                                actorHit.actorIndex < m_mapActorAiStates.size()
                                    ? m_mapActorAiStates[actorHit.actorIndex].actorId
                                    : static_cast<uint32_t>(actorHit.actorIndex);
                            m_pGameplayCombatController->recordPartyProjectileActorImpact(
                                projectile.sourceId,
                                projectile.sourcePartyMemberIndex,
                                actorId,
                                appliedDamage,
                                projectile.spellId,
                                true,
                                previousHp > 0 && targetActor.hp <= 0);
                        }
                    }
                    else
                    {
                        const int previousHp = targetActor.hp;
                        targetActor.hp =
                            static_cast<int16_t>(std::max(0, static_cast<int>(targetActor.hp) - actorHit.damage));

                        if (previousHp > 0 && targetActor.hp <= 0)
                        {
                            beginMapActorDyingState(actorHit.actorIndex, targetActor);
                        }
                        else if (previousHp > 0 && targetActor.hp < previousHp)
                        {
                            const GameplayWorldPoint sourcePoint =
                                {projectile.sourceX, projectile.sourceY, projectile.sourceZ};
                            beginMapActorHitReaction(actorHit.actorIndex, targetActor, &sourcePoint);
                        }
                    }
                }
            }
        }
    }

    if (frameResult.fxRequest)
    {
        switch (frameResult.fxRequest->kind)
        {
            case GameplayProjectileService::ProjectileFrameFxKind::WaterSplash:
                spawnIndoorWaterSplashImpactVisual(frameResult.fxRequest->point);
                break;

            case GameplayProjectileService::ProjectileFrameFxKind::ProjectileImpact:
                spawnIndoorProjectileImpactVisual(
                    projectile,
                    frameResult.fxRequest->point,
                    frameResult.fxRequest->centerVertically);
                break;
        }
    }

    if (frameResult.audioRequest)
    {
        pushIndoorProjectileAudioEvent(*frameResult.audioRequest);
    }

    const auto refreshProjectileSector =
        [&]()
        {
            if (m_pIndoorMapData == nullptr)
            {
                return;
            }

            const GameplayWorldPoint projectilePoint = {projectile.x, projectile.y, projectile.z};
            const float sectorBoundsSlack =
                static_cast<float>(std::max<uint16_t>(std::max(projectile.radius, projectile.height), 8)) + 16.0f;

            if (indoorPointInsideSectorBounds(
                    *m_pIndoorMapData,
                    projectilePoint,
                    projectile.sectorId,
                    sectorBoundsSlack))
            {
                return;
            }

            RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();
            projectile.sectorId =
                resolveIndoorPointSector(
                    m_pIndoorMapData,
                    runtimeGeometry.vertices,
                    &runtimeGeometry.geometryCache,
                    {projectilePoint.x, projectilePoint.y, projectilePoint.z},
                    projectile.sectorId);
        };

    if (frameResult.bounce)
    {
        m_pGameplayProjectileService->applyProjectileBounce(
            projectile,
            frameResult.bounce->point.x,
            frameResult.bounce->point.y,
            frameResult.bounce->point.z,
            frameResult.bounce->normalX,
            frameResult.bounce->normalY,
            frameResult.bounce->normalZ,
            frameResult.bounce->bounceFactor,
            frameResult.bounce->stopVelocity,
            frameResult.bounce->groundDamping);
        refreshProjectileSector();

        if (indoorProjectileShouldSettle(projectile))
        {
            m_pGameplayProjectileService->settleProjectile(projectile);
        }
    }

    if (frameResult.applyMotionEnd)
    {
        m_pGameplayProjectileService->applyProjectileMotionEnd(projectile, frameResult.motion);
        refreshProjectileSector();
    }

    if (frameResult.expireProjectile)
    {
        m_pGameplayProjectileService->expireProjectile(projectile);
    }

    for (const GameplayProjectileService::ProjectileSpawnRequest &spawnRequest : frameResult.spawnedProjectiles)
    {
        GameplayProjectileService::ProjectileSpawnRequest childSpawnRequest = spawnRequest;

        if (childSpawnRequest.sectorId < 0)
        {
            childSpawnRequest.sectorId = projectile.sectorId;
        }

        m_pGameplayProjectileService->spawnProjectile(childSpawnRequest);
    }
}

void IndoorWorldRuntime::updateIndoorProjectiles(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || m_pGameplayProjectileService == nullptr)
    {
        return;
    }

    const bool hasActiveProjectile =
        std::any_of(
            m_pGameplayProjectileService->projectiles().begin(),
            m_pGameplayProjectileService->projectiles().end(),
            [](const GameplayProjectileService::ProjectileState &projectile)
            {
                return !projectile.isExpired;
            });
    const bool hasMovingProjectile =
        std::any_of(
            m_pGameplayProjectileService->projectiles().begin(),
            m_pGameplayProjectileService->projectiles().end(),
            [](const GameplayProjectileService::ProjectileState &projectile)
            {
                return !projectile.isExpired && !projectile.isSettled;
            });

    if (!hasActiveProjectile)
    {
        m_projectileUpdateAccumulatorSeconds = 0.0f;
        return;
    }

    if (!hasMovingProjectile)
    {
        for (GameplayProjectileService::ProjectileState &projectile : m_pGameplayProjectileService->projectiles())
        {
            if (!projectile.isExpired && projectile.isSettled
                && m_pGameplayProjectileService->advanceProjectileLifetime(projectile, deltaSeconds))
            {
                m_pGameplayProjectileService->expireProjectile(projectile);
            }
        }

        m_pGameplayProjectileService->eraseExpiredProjectiles();
        m_projectileUpdateAccumulatorSeconds = 0.0f;
        return;
    }

    syncMapActorAiStates();

    std::vector<IndoorVertex> emptyVertices;
    IndoorFaceGeometryCache emptyGeometryCache;
    const std::vector<IndoorVertex> *pProjectileVertices = &emptyVertices;
    IndoorFaceGeometryCache *pProjectileGeometryCache = &emptyGeometryCache;

    if (m_pIndoorMapData != nullptr)
    {
        RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();
        pProjectileVertices = &runtimeGeometry.vertices;
        pProjectileGeometryCache = &runtimeGeometry.geometryCache;
    }

    m_projectileUpdateAccumulatorSeconds =
        std::min(m_projectileUpdateAccumulatorSeconds + deltaSeconds, MaxAccumulatedProjectileUpdateSeconds);

    int projectileUpdateStepCount = 0;

    while (m_projectileUpdateAccumulatorSeconds >= ProjectileUpdateStepSeconds
        && projectileUpdateStepCount < MaxProjectileUpdateStepsPerFrame)
    {
        std::vector<GameplayProjectileService::ProjectileState> &projectiles =
            m_pGameplayProjectileService->projectiles();
        const size_t projectileCount = projectiles.size();

        for (size_t projectileIndex = 0;
             projectileIndex < projectileCount && projectileIndex < projectiles.size();
             ++projectileIndex)
        {
            GameplayProjectileService::ProjectileState &projectile = projectiles[projectileIndex];

            if (projectile.isExpired)
            {
                continue;
            }

            if (projectile.isSettled)
            {
                if (m_pGameplayProjectileService->advanceProjectileLifetime(projectile, ProjectileUpdateStepSeconds))
                {
                    m_pGameplayProjectileService->expireProjectile(projectile);
                }

                continue;
            }

            const GameplayProjectileService::ProjectileFrameFacts facts =
                collectIndoorProjectileFrameFacts(
                    projectile,
                    ProjectileUpdateStepSeconds,
                    *pProjectileVertices,
                    *pProjectileGeometryCache);
            const GameplayProjectileService::ProjectileFrameResult frameResult =
                m_pGameplayProjectileService->updateProjectileFrame(projectile, facts);

            if (indoorProjectileDebugEnabled())
            {
                const GameplayProjectileService::ProjectileFrameCollisionFacts &collision = facts.collision;
                const GameplayProjectileService::ProjectileBounceSurfaceFacts &bounceSurface =
                    collision.bounceSurface;
                std::cout
                    << "IndoorProjectileFrame"
                    << " id=" << projectile.projectileId
                    << " spell=" << projectile.spellId
                    << " object=\"" << projectile.objectName << "\""
                    << " sprite=\"" << projectile.objectSpriteName << "\""
                    << " flags=0x" << std::hex << projectile.objectFlags << std::dec
                    << " pos=(" << projectile.x << "," << projectile.y << "," << projectile.z << ")"
                    << " vel=(" << projectile.velocityX << "," << projectile.velocityY << ","
                    << projectile.velocityZ << ")"
                    << " gravity=" << facts.gravity
                    << " motion=(" << facts.motion.startX << "," << facts.motion.startY << ","
                    << facts.motion.startZ << ")->(" << facts.motion.endX << "," << facts.motion.endY
                    << "," << facts.motion.endZ << ")"
                    << " hasCollision=" << (facts.hasCollision ? 1 : 0)
                    << " collision=" << indoorProjectileCollisionKindName(collision.kind)
                    << " actorIndex=" << collision.actorIndex
                    << " point=(" << collision.point.x << "," << collision.point.y << ","
                    << collision.point.z << ")"
                    << " bounceSurface=" << (bounceSurface.canBounce ? 1 : 0)
                    << " requiresDownward=" << (bounceSurface.requiresDownwardVelocity ? 1 : 0)
                    << " bounceNormal=(" << bounceSurface.normalX << "," << bounceSurface.normalY << ","
                    << bounceSurface.normalZ << ")"
                    << " bounceStopVelocity=" << facts.bounceStopVelocity
                    << " resultBounce=" << (frameResult.bounce ? 1 : 0)
                    << " resultMotionEnd=" << (frameResult.applyMotionEnd ? 1 : 0)
                    << " resultExpire=" << (frameResult.expireProjectile ? 1 : 0)
                    << " resultDirectActor=" << (frameResult.directActorImpact ? 1 : 0)
                    << " resultDirectParty=" << (frameResult.directPartyDamage ? 1 : 0)
                    << " resultArea=" << (frameResult.areaImpact ? 1 : 0)
                    << " resultFx=" << (frameResult.fxRequest ? 1 : 0)
                    << '\n';
            }

            applyIndoorProjectileFrameResult(projectile, facts, frameResult);
        }

        m_projectileUpdateAccumulatorSeconds -= ProjectileUpdateStepSeconds;
        ++projectileUpdateStepCount;
    }

    m_pGameplayProjectileService->eraseExpiredProjectiles();
}

bool IndoorWorldRuntime::updateWorldItemsStep(
    float deltaSeconds,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || m_pIndoorMapData == nullptr || m_pObjectTable == nullptr)
    {
        return false;
    }

    bool changed = false;

    for (MapDeltaSpriteObject &spriteObject : pMapDeltaData->spriteObjects)
    {
        const ObjectEntry *pObjectEntry = m_pObjectTable->get(spriteObject.objectDescriptionId);

        if (pObjectEntry == nullptr
            || spriteObject.objectDescriptionId == 0
            || (spriteObject.attributes & SpriteAttrRemoved) != 0)
        {
            continue;
        }

        bx::Vec3 velocity = {
            static_cast<float>(spriteObject.velocityX),
            static_cast<float>(spriteObject.velocityY),
            static_cast<float>(spriteObject.velocityZ)
        };

        if (velocity.x == 0.0f && velocity.y == 0.0f && velocity.z == 0.0f)
        {
            continue;
        }

        if ((pObjectEntry->flags & ObjectDescNoGravity) == 0)
        {
            velocity.z -= IndoorWorldItemGravity * deltaSeconds;
        }

        const GameplayWorldPoint segmentStart = {
            static_cast<float>(spriteObject.x),
            static_cast<float>(spriteObject.y),
            static_cast<float>(spriteObject.z)
        };
        const GameplayWorldPoint segmentEnd = {
            segmentStart.x + velocity.x * deltaSeconds,
            segmentStart.y + velocity.y * deltaSeconds,
            segmentStart.z + velocity.z * deltaSeconds
        };
        GameplayWorldPoint resolvedPoint = segmentEnd;

        GameplayProjectileService::ProjectileState probe = {};
        probe.radius = static_cast<uint16_t>(std::max<uint16_t>(pObjectEntry->radius, 1));
        probe.height = static_cast<uint16_t>(std::max<uint16_t>(pObjectEntry->height, 1));

        const std::optional<IndoorProjectileCollisionCandidate> faceHit =
            findProjectileIndoorFaceHit(
                *m_pIndoorMapData,
                pMapDeltaData,
                eventRuntimeState(),
                vertices,
                geometryCache,
                probe,
                segmentStart,
                segmentEnd,
                spriteObject.sectorId);

        if (faceHit && faceHit->faceIndex < m_pIndoorMapData->faces.size())
        {
            executeFaceTriggeredEvent(faceHit->faceIndex, FaceAttribute::TriggerByObject, false);
            resolvedPoint = faceHit->point;
            const IndoorFaceGeometryData *pGeometry =
                geometryCache.geometryForFace(*m_pIndoorMapData, vertices, faceHit->faceIndex);

            if (pGeometry != nullptr)
            {
                if (pGeometry->kind == IndoorFaceKind::Floor)
                {
                    resolvedPoint.z = calculateIndoorFaceHeight(*pGeometry, resolvedPoint.x, resolvedPoint.y)
                        + IndoorWorldItemGroundClearance;

                    if ((pObjectEntry->flags & ObjectDescBounce) != 0
                        && std::abs(velocity.z) >= IndoorWorldItemBounceStopVelocity)
                    {
                        velocity.z = -velocity.z * IndoorWorldItemBounceFactor;
                    }
                    else
                    {
                        velocity.z = 0.0f;
                    }
                }
                else
                {
                    const float speed = length3d(velocity);
                    const float dotFix = std::max(std::abs(dotProduct(pGeometry->normal, velocity)), speed / 8.0f);
                    velocity.x += 2.0f * dotFix * pGeometry->normal.x;
                    velocity.y += 2.0f * dotFix * pGeometry->normal.y;

                    float zFix = dotFix * pGeometry->normal.z;

                    if (pGeometry->normal.z <= 0.48828125f)
                    {
                        zFix *= 2.0f;
                    }
                    else
                    {
                        velocity.z += zFix;
                        zFix *= 0.48828125f;
                    }

                    velocity.z += zFix;
                }

                velocity.x *= IndoorWorldItemGroundDamping;
                velocity.y *= IndoorWorldItemGroundDamping;
                velocity.z *= IndoorWorldItemGroundDamping;
            }
        }

        const IndoorFloorSample floorSample =
            sampleIndoorFloor(
                *m_pIndoorMapData,
                vertices,
                resolvedPoint.x,
                resolvedPoint.y,
                resolvedPoint.z,
                IndoorWorldItemFloorSampleRise,
                IndoorWorldItemFloorSampleDrop,
                spriteObject.sectorId,
                nullptr,
                &geometryCache);

        if (floorSample.hasFloor
            && resolvedPoint.z <= floorSample.height + IndoorWorldItemGroundClearance
            && velocity.z <= 0.0f)
        {
            resolvedPoint.z = floorSample.height + IndoorWorldItemGroundClearance;
            spriteObject.sectorId = floorSample.sectorId;

            if ((pObjectEntry->flags & ObjectDescBounce) != 0
                && std::abs(velocity.z) >= IndoorWorldItemBounceStopVelocity)
            {
                velocity.z = -velocity.z * IndoorWorldItemBounceFactor;
            }
            else
            {
                velocity.z = 0.0f;
            }

            velocity.x *= IndoorWorldItemGroundDamping;
            velocity.y *= IndoorWorldItemGroundDamping;

            const float horizontalSpeedSquared = velocity.x * velocity.x + velocity.y * velocity.y;

            if (horizontalSpeedSquared < IndoorWorldItemRestingHorizontalSpeedSquared)
            {
                velocity.x = 0.0f;
                velocity.y = 0.0f;
            }
        }
        else
        {
            const std::optional<int16_t> sectorId =
                findIndoorSectorForPoint(
                    *m_pIndoorMapData,
                    vertices,
                    {resolvedPoint.x, resolvedPoint.y, resolvedPoint.z},
                    &geometryCache);

            if (sectorId)
            {
                spriteObject.sectorId = *sectorId;
            }
        }

        const int resolvedX = static_cast<int>(std::lround(resolvedPoint.x));
        const int resolvedY = static_cast<int>(std::lround(resolvedPoint.y));
        const int resolvedZ = static_cast<int>(std::lround(resolvedPoint.z));
        const int16_t resolvedVelocityX = clampToInt16(velocity.x);
        const int16_t resolvedVelocityY = clampToInt16(velocity.y);
        const int16_t resolvedVelocityZ = clampToInt16(velocity.z);

        changed = changed
            || spriteObject.x != resolvedX
            || spriteObject.y != resolvedY
            || spriteObject.z != resolvedZ
            || spriteObject.velocityX != resolvedVelocityX
            || spriteObject.velocityY != resolvedVelocityY
            || spriteObject.velocityZ != resolvedVelocityZ;

        spriteObject.x = resolvedX;
        spriteObject.y = resolvedY;
        spriteObject.z = resolvedZ;
        spriteObject.velocityX = resolvedVelocityX;
        spriteObject.velocityY = resolvedVelocityY;
        spriteObject.velocityZ = resolvedVelocityZ;
    }

    return changed;
}

void IndoorWorldRuntime::updateWorldItems(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || m_pIndoorMapData == nullptr)
    {
        return;
    }

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    bool hasMovingObject = false;

    for (const MapDeltaSpriteObject &spriteObject : pMapDeltaData->spriteObjects)
    {
        if (spriteObject.velocityX != 0 || spriteObject.velocityY != 0 || spriteObject.velocityZ != 0)
        {
            hasMovingObject = true;
            break;
        }
    }

    if (!hasMovingObject)
    {
        m_worldItemUpdateAccumulatorSeconds = 0.0f;
        return;
    }

    RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();
    bool changed = false;

    m_worldItemUpdateAccumulatorSeconds =
        std::min(m_worldItemUpdateAccumulatorSeconds + deltaSeconds, MaxAccumulatedWorldItemUpdateSeconds);

    while (m_worldItemUpdateAccumulatorSeconds >= WorldItemUpdateStepSeconds)
    {
        changed = updateWorldItemsStep(
            WorldItemUpdateStepSeconds,
            runtimeGeometry.vertices,
            runtimeGeometry.geometryCache) || changed;
        m_worldItemUpdateAccumulatorSeconds -= WorldItemUpdateStepSeconds;
    }

    if (changed && m_pRenderer != nullptr)
    {
        m_pRenderer->clearGameplayWorldHover();
    }
}

void IndoorWorldRuntime::applyIndoorActorMovementIntegration(
    IndoorMovementController &movementController,
    size_t actorIndex,
    const ActorAiUpdate &update,
    const GameplayActorAiSystem &actorAiSystem)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr
        || m_pIndoorMapData == nullptr
        || m_pMonsterTable == nullptr
        || actorIndex >= pMapDeltaData->actors.size()
        || actorIndex >= m_mapActorAiStates.size())
    {
        return;
    }

    MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(aiState.monsterId);

    if (pStats == nullptr)
    {
        return;
    }

    const float collisionRadius = static_cast<float>(aiState.collisionRadius);
    const float collisionHeight = static_cast<float>(aiState.collisionHeight);
    const uint16_t moveSpeed = aiState.movementSpeed != 0 ? aiState.movementSpeed : uint16_t(pStats->speed);
    const GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService =
        m_pGameplayActorService != nullptr ? m_pGameplayActorService : &fallbackActorService;
    const float effectiveMoveSpeed =
        pActorService->effectiveActorMoveSpeed(
            moveSpeed,
            pStats->speed,
            aiState.spellEffects.slowMoveMultiplier,
            aiState.spellEffects.darkGraspRemainingSeconds > 0.0f);
    const float oldX = aiState.preciseX;
    const float oldY = aiState.preciseY;
    const float oldZ = aiState.preciseZ;
    IndoorBodyDimensions body = {};
    body.radius = collisionRadius;
    body.height = collisionHeight;

    IndoorMoveState moveState = {};
    moveState.x = oldX;
    moveState.y = oldY;
    moveState.footZ = oldZ;
    moveState.eyeHeight = body.height;
    moveState.verticalVelocity = aiState.velocityZ;
    moveState.sectorId = aiState.sectorId;
    moveState.eyeSectorId = aiState.eyeSectorId;
    moveState.supportFaceIndex = aiState.supportFaceIndex;
    moveState.grounded = aiState.grounded;

    if (moveState.sectorId < 0 || moveState.eyeSectorId < 0)
    {
        moveState = movementController.initializeStateFromEyePosition(oldX, oldY, oldZ + body.height, body);
        moveState.verticalVelocity = aiState.velocityZ;
    }

    const bool actorCanFly = pStats->canFly;
    if (actorCanFly)
    {
        moveState.verticalVelocity = update.movementIntent.desiredMoveZ * effectiveMoveSpeed;
    }

    const float desiredVelocityX = update.movementIntent.desiredMoveX * effectiveMoveSpeed;
    const float desiredVelocityY = update.movementIntent.desiredMoveY * effectiveMoveSpeed;
    std::vector<size_t> contactedActorIndices;
    IndoorMoveDebugInfo moveDebugInfo = {};
    const IndoorMoveState resolvedMoveState =
        movementController.resolveMove(
            moveState,
            body,
            desiredVelocityX,
            desiredVelocityY,
            false,
            ActorUpdateStepSeconds,
            &contactedActorIndices,
            actorIndex,
            true,
            &moveDebugInfo,
            actorCanFly);

    if (moveDebugInfo.primaryBlockKind == IndoorMoveBlockKind::Wall
        && moveDebugInfo.hitFaceIndex != static_cast<size_t>(-1))
    {
        executeFaceTriggeredEvent(moveDebugInfo.hitFaceIndex, FaceAttribute::TriggerByMonster, false);
    }

    IndoorMoveState finalMoveState = resolvedMoveState;
    std::sort(contactedActorIndices.begin(), contactedActorIndices.end());
    const size_t contactedActorCount =
        static_cast<size_t>(
            std::unique(contactedActorIndices.begin(), contactedActorIndices.end()) - contactedActorIndices.begin());

    const float deltaX = finalMoveState.x - oldX;
    const float deltaY = finalMoveState.y - oldY;
    const bool wantedHorizontalMove =
        std::abs(update.movementIntent.desiredMoveX) > 0.001f
        || std::abs(update.movementIntent.desiredMoveY) > 0.001f;
    const bool movedHorizontally = std::abs(deltaX) > 0.001f || std::abs(deltaY) > 0.001f;

    aiState.preciseX = finalMoveState.x;
    aiState.preciseY = finalMoveState.y;
    aiState.preciseZ = finalMoveState.footZ;
    aiState.velocityX = deltaX / ActorUpdateStepSeconds;
    aiState.velocityY = deltaY / ActorUpdateStepSeconds;
    aiState.velocityZ = finalMoveState.verticalVelocity;
    aiState.sectorId = finalMoveState.sectorId;
    aiState.eyeSectorId = finalMoveState.eyeSectorId;
    aiState.supportFaceIndex = finalMoveState.supportFaceIndex;
    aiState.grounded = finalMoveState.grounded;
    movementController.updateActorColliderPosition(
        actorIndex,
        aiState.sectorId,
        aiState.preciseX,
        aiState.preciseY,
        aiState.preciseZ);

    actor.x = static_cast<int>(std::lround(aiState.preciseX));
    actor.y = static_cast<int>(std::lround(aiState.preciseY));
    actor.z = static_cast<int>(std::lround(aiState.preciseZ));

    if (finalMoveState.sectorId >= 0)
    {
        actor.sectorId = finalMoveState.sectorId;
    }

    ActorAiFacts movementFacts = {};
    movementFacts.actorIndex = actorIndex;
    movementFacts.actorId = aiState.actorId;
    movementFacts.identity.hostilityType = actor.hostilityType;
    movementFacts.stats.canFly = pStats->canFly;
    movementFacts.runtime.motionState = aiState.motionState;
    movementFacts.runtime.actionSeconds = aiState.actionSeconds;
    movementFacts.runtime.crowdSideLockRemainingSeconds = aiState.crowdSideLockRemainingSeconds;
    movementFacts.runtime.crowdNoProgressSeconds = aiState.crowdNoProgressSeconds;
    movementFacts.runtime.crowdLastEdgeDistance = aiState.crowdLastEdgeDistance;
    movementFacts.runtime.crowdRetreatRemainingSeconds = aiState.crowdRetreatRemainingSeconds;
    movementFacts.runtime.crowdStandRemainingSeconds = aiState.crowdStandRemainingSeconds;
    movementFacts.runtime.crowdProbeEdgeDistance = aiState.crowdProbeEdgeDistance;
    movementFacts.runtime.crowdProbeElapsedSeconds = aiState.crowdProbeElapsedSeconds;
    movementFacts.runtime.pursueDecisionCount = aiState.pursueDecisionCount;
    movementFacts.runtime.crowdEscapeAttempts = aiState.crowdEscapeAttempts;
    movementFacts.runtime.crowdSideSign = aiState.crowdSideSign;
    movementFacts.movement.position =
        GameplayWorldPoint{aiState.preciseX, aiState.preciseY, aiState.preciseZ};
    movementFacts.movement.effectiveMoveSpeed = effectiveMoveSpeed;
    movementFacts.movement.contactedActorCount = contactedActorCount;

    if (!contactedActorIndices.empty())
    {
        const size_t contactedActorIndex = contactedActorIndices.front();

        if (contactedActorIndex < pMapDeltaData->actors.size() && contactedActorIndex < m_mapActorAiStates.size())
        {
            const MapDeltaActor &contactedActor = pMapDeltaData->actors[contactedActorIndex];
            const MapActorAiState &contactedAiState = m_mapActorAiStates[contactedActorIndex];
            movementFacts.movement.hasContactedActor = true;
            movementFacts.movement.contactedActorHostilityType = contactedActor.hostilityType;
            movementFacts.movement.contactedActorPosition =
                GameplayWorldPoint{contactedAiState.preciseX, contactedAiState.preciseY, contactedAiState.preciseZ};
        }
    }

    movementFacts.movement.meleePursuitActive = update.movementIntent.meleePursuitActive;
    movementFacts.movement.inMeleeRange = update.movementIntent.inMeleeRange;
    movementFacts.movement.movementBlocked = wantedHorizontalMove && !movedHorizontally;
    movementFacts.movement.allowCrowdSteering = m_pGameplayActorService != nullptr;
    movementFacts.movement.crowdSteeringTriggersOnMovementBlocked = true;
    movementFacts.movement.crowdSidestepAngleRadians = Pi / 4.0f;
    movementFacts.movement.crowdRetreatAngleRadians = Pi * 0.53f;
    movementFacts.target.currentPosition = update.movementIntent.targetPosition;
    movementFacts.target.currentEdgeDistance = update.movementIntent.targetEdgeDistance;

    const ActorAiUpdate movementUpdate = actorAiSystem.updateActorAfterWorldMovement(movementFacts);

    if (movementUpdate.movementIntent.clearVelocity)
    {
        aiState.velocityX = 0.0f;
        aiState.velocityY = 0.0f;
        aiState.velocityZ = 0.0f;
    }

    if (movementUpdate.state.pursueDecisionCount)
    {
        aiState.pursueDecisionCount = *movementUpdate.state.pursueDecisionCount;
    }

    if (movementUpdate.state.crowdSideLockRemainingSeconds)
    {
        aiState.crowdSideLockRemainingSeconds = *movementUpdate.state.crowdSideLockRemainingSeconds;
    }

    if (movementUpdate.state.crowdNoProgressSeconds)
    {
        aiState.crowdNoProgressSeconds = *movementUpdate.state.crowdNoProgressSeconds;
    }

    if (movementUpdate.state.crowdLastEdgeDistance)
    {
        aiState.crowdLastEdgeDistance = *movementUpdate.state.crowdLastEdgeDistance;
    }

    if (movementUpdate.state.crowdRetreatRemainingSeconds)
    {
        aiState.crowdRetreatRemainingSeconds = *movementUpdate.state.crowdRetreatRemainingSeconds;
    }

    if (movementUpdate.state.crowdStandRemainingSeconds)
    {
        aiState.crowdStandRemainingSeconds = *movementUpdate.state.crowdStandRemainingSeconds;
    }

    if (movementUpdate.state.crowdProbeEdgeDistance)
    {
        aiState.crowdProbeEdgeDistance = *movementUpdate.state.crowdProbeEdgeDistance;
    }

    if (movementUpdate.state.crowdProbeElapsedSeconds)
    {
        aiState.crowdProbeElapsedSeconds = *movementUpdate.state.crowdProbeElapsedSeconds;
    }

    if (movementUpdate.state.crowdEscapeAttempts)
    {
        aiState.crowdEscapeAttempts = *movementUpdate.state.crowdEscapeAttempts;
    }

    if (movementUpdate.state.crowdSideSign)
    {
        aiState.crowdSideSign = *movementUpdate.state.crowdSideSign;
    }

    if (movementUpdate.movementIntent.action == ActorAiMovementAction::Stand
        || movementUpdate.movementIntent.action == ActorAiMovementAction::Pursue
        || movementUpdate.movementIntent.action == ActorAiMovementAction::Flee)
    {
        aiState.moveDirectionX = movementUpdate.movementIntent.moveDirectionX;
        aiState.moveDirectionY = movementUpdate.movementIntent.moveDirectionY;
    }

    if (movementUpdate.movementIntent.updateYaw)
    {
        aiState.yawRadians = movementUpdate.movementIntent.yawRadians;
    }

    if (movementUpdate.state.actionSeconds)
    {
        aiState.actionSeconds = *movementUpdate.state.actionSeconds;
    }

    if (movementUpdate.state.motionState)
    {
        aiState.motionState = *movementUpdate.state.motionState;
    }

    if (movementUpdate.animation.animationState)
    {
        aiState.animationState = *movementUpdate.animation.animationState;
        actor.currentActionAnimation = indoorActionAnimationFromActorAi(*movementUpdate.animation.animationState);
    }
}

std::optional<ActorAiFacts> IndoorWorldRuntime::collectIndoorActorAiFacts(
    size_t actorIndex,
    bool active,
    const ActorPartyFacts &partyFacts,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr
        || m_pMonsterTable == nullptr
        || actorIndex >= pMapDeltaData->actors.size()
        || actorIndex >= m_mapActorAiStates.size())
    {
        return std::nullopt;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(aiState.monsterId);

    if (pStats == nullptr)
    {
        return std::nullopt;
    }

    const GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService =
        m_pGameplayActorService != nullptr ? m_pGameplayActorService : &fallbackActorService;
    const uint16_t radius = aiState.collisionRadius;
    const uint16_t height = aiState.collisionHeight;
    const uint16_t moveSpeed = aiState.movementSpeed != 0 ? aiState.movementSpeed : uint16_t(pStats->speed);
    const bool actorInvisible = (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0;
    const bool defaultHostile = defaultActorHostileToParty(actor, m_pMonsterTable);
    const bool hasEffectOverride = hasActiveActorSpellEffectOverride(aiState.spellEffects);
    const bool hostileToParty = hasEffectOverride ? aiState.spellEffects.hostileToParty : aiState.hostileToParty;
    const bool hasDetectedParty = hasEffectOverride
        ? aiState.spellEffects.hasDetectedParty
        : aiState.hasDetectedParty || defaultActorHasDetectedParty(actor, hostileToParty);
    const GameplayActorTargetPolicyState actorPolicyState =
        buildIndoorActorTargetPolicyState(
            aiState,
            aiState.spellEffects,
            height,
            hostileToParty,
            actor.group,
            actor.ally);
    const float actorTargetZ = aiState.preciseZ + std::max(24.0f, static_cast<float>(height) * 0.7f);
    const int16_t actorSectorId =
        aiState.sectorId >= 0 ? aiState.sectorId : actor.sectorId;
    int16_t partySectorId = -1;
    if (m_pPartyRuntime != nullptr)
    {
        const IndoorMoveState &partyMoveState = m_pPartyRuntime->movementState();
        partySectorId = partyMoveState.eyeSectorId >= 0 ? partyMoveState.eyeSectorId : partyMoveState.sectorId;
    }
    const bool sameSectorAsParty = actorSectorId >= 0 && actorSectorId == partySectorId;
    const GameplayWorldPoint partyTargetPoint =
        {partyFacts.position.x, partyFacts.position.y, partyFacts.position.z + PartyTargetHeightOffset};
    const GameplayWorldPoint actorTargetPoint = {aiState.preciseX, aiState.preciseY, actorTargetZ};
    const bool hasCombatLineOfSightToParty =
        active && hasIndoorCombatLineOfSight(actorTargetPoint, actorSectorId, partyTargetPoint, partySectorId);
    const bool activeCanKeepPartyTarget =
        active
        && (hasDetectedParty || hasCombatLineOfSightToParty);

    ActorAiFacts facts = {};
    facts.actorIndex = actorIndex;
    facts.actorId = aiState.actorId;

    facts.identity.actorId = aiState.actorId;
    facts.identity.monsterId = aiState.monsterId;
    facts.identity.displayName = aiState.displayName.empty() ? pStats->name : aiState.displayName;
    facts.identity.group = actor.group;
    facts.identity.ally = actor.ally;
    facts.identity.hostilityType = actor.hostilityType;
    facts.identity.targetPolicy = actorPolicyState;

    facts.stats.aiType = gameplayActorAiTypeFromMonster(pStats->aiType);
    facts.stats.monsterLevel = pStats->level;
    facts.stats.currentHp = actor.hp;
    facts.stats.maxHp = pStats->hitPoints;
    facts.stats.armorClass = pActorService->effectiveArmorClass(pStats->armorClass, aiState.spellEffects);
    facts.stats.radius = radius;
    facts.stats.height = height;
    facts.stats.moveSpeed = moveSpeed;
    facts.stats.canFly = pStats->canFly;
    facts.stats.hasSpell1 = pStats->hasSpell1;
    facts.stats.hasSpell2 = pStats->hasSpell2;
    facts.stats.spell1Name = pStats->spell1Name;
    facts.stats.spell2Name = pStats->spell2Name;
    facts.stats.attack1DamageType = GameMechanics::parseCombatDamageType(pStats->attack1Type);
    facts.stats.attack2DamageType = GameMechanics::parseCombatDamageType(pStats->attack2Type);
    facts.stats.spell1CastSupported = indoorMonsterSpellCastSupported(pStats->spell1Name);
    facts.stats.spell2CastSupported = indoorMonsterSpellCastSupported(pStats->spell2Name);
    if (m_pSpellTable != nullptr)
    {
        if (const SpellEntry *pSpellEntry = m_pSpellTable->findByName(pStats->spell1Name))
        {
            facts.stats.spell1Id = static_cast<uint32_t>(std::max(pSpellEntry->id, 0));
            facts.stats.spell1DamageType = GameMechanics::spellCombatDamageType(facts.stats.spell1Id, m_pSpellTable);
        }

        if (const SpellEntry *pSpellEntry = m_pSpellTable->findByName(pStats->spell2Name))
        {
            facts.stats.spell2Id = static_cast<uint32_t>(std::max(pSpellEntry->id, 0));
            facts.stats.spell2DamageType = GameMechanics::spellCombatDamageType(facts.stats.spell2Id, m_pSpellTable);
        }
    }
    facts.stats.spell1SkillLevel = pStats->spell1SkillLevel;
    facts.stats.spell1SkillMastery = pStats->spell1SkillMastery;
    facts.stats.spell2SkillLevel = pStats->spell2SkillLevel;
    facts.stats.spell2SkillMastery = pStats->spell2SkillMastery;
    facts.stats.spell1UseChance = pStats->spell1UseChance;
    facts.stats.spell2UseChance = pStats->spell2UseChance;
    facts.stats.attack2Chance = pStats->attack2Chance;
    facts.stats.attack1Damage.diceRolls = pStats->attack1Damage.diceRolls;
    facts.stats.attack1Damage.diceSides = pStats->attack1Damage.diceSides;
    facts.stats.attack1Damage.bonus = pStats->attack1Damage.bonus;
    facts.stats.attack2Damage.diceRolls = pStats->attack2Damage.diceRolls;
    facts.stats.attack2Damage.diceSides = pStats->attack2Damage.diceSides;
    facts.stats.attack2Damage.bonus = pStats->attack2Damage.bonus;
    facts.stats.attackConstraints.attack1IsRanged = pStats->attack1HasMissile;
    facts.stats.attackConstraints.attack2IsRanged = pStats->attack2HasMissile;
    facts.stats.attackConstraints.blindActive = aiState.spellEffects.blindRemainingSeconds > 0.0f;
    facts.stats.attackConstraints.darkGraspActive = aiState.spellEffects.darkGraspRemainingSeconds > 0.0f;
    facts.stats.attackConstraints.rangedCommitAllowed = true;

    facts.runtime.motionState = aiState.motionState;
    facts.runtime.animationState = aiState.animationState;
    facts.runtime.queuedAttackAbility = aiState.queuedAttackAbility;
    facts.runtime.animationTimeTicks = aiState.animationTimeTicks;
    facts.runtime.recoverySeconds = aiState.recoverySeconds;
    facts.runtime.attackAnimationSeconds = aiState.attackAnimationSeconds;
    facts.runtime.meleeAttackAnimationSeconds = aiState.meleeAttackAnimationSeconds;
    facts.runtime.rangedAttackAnimationSeconds = aiState.rangedAttackAnimationSeconds;
    facts.runtime.attackCooldownSeconds = aiState.attackCooldownSeconds;
    facts.runtime.idleDecisionSeconds = aiState.idleDecisionSeconds;
    facts.runtime.actionSeconds = aiState.actionSeconds;
    facts.runtime.crowdSideLockRemainingSeconds = aiState.crowdSideLockRemainingSeconds;
    facts.runtime.crowdNoProgressSeconds = aiState.crowdNoProgressSeconds;
    facts.runtime.crowdLastEdgeDistance = aiState.crowdLastEdgeDistance;
    facts.runtime.crowdRetreatRemainingSeconds = aiState.crowdRetreatRemainingSeconds;
    facts.runtime.crowdStandRemainingSeconds = aiState.crowdStandRemainingSeconds;
    facts.runtime.crowdProbeEdgeDistance = aiState.crowdProbeEdgeDistance;
    facts.runtime.crowdProbeElapsedSeconds = aiState.crowdProbeElapsedSeconds;
    facts.runtime.yawRadians = aiState.yawRadians;
    facts.runtime.idleDecisionCount = aiState.idleDecisionCount;
    facts.runtime.pursueDecisionCount = aiState.pursueDecisionCount;
    facts.runtime.attackDecisionCount = aiState.attackDecisionCount;
    facts.runtime.crowdEscapeAttempts = aiState.crowdEscapeAttempts;
    facts.runtime.crowdSideSign = aiState.crowdSideSign;
    facts.runtime.attackImpactTriggered = aiState.attackImpactTriggered;

    facts.status.spellEffects = aiState.spellEffects;
    facts.status.invisible = actorInvisible;
    facts.status.dead = aiState.motionState == ActorAiMotionState::Dead;
    facts.status.hostileToParty = hostileToParty;
    facts.status.bloodSplatSpawned = aiState.bloodSplatSpawned;
    facts.status.hasDetectedParty = hasDetectedParty;
    facts.status.defaultHostileToParty = defaultHostile;

    const float partyDeltaX = partyFacts.position.x - aiState.preciseX;
    const float partyDeltaY = partyFacts.position.y - aiState.preciseY;
    const float partyDeltaZ = partyTargetPoint.z - actorTargetZ;
    const float partySenseRange = pActorService->partyEngagementRange(actorPolicyState);
    const bool actorCanSenseParty =
        activeCanKeepPartyTarget
        && std::abs(partyDeltaX) <= partySenseRange
        && std::abs(partyDeltaY) <= partySenseRange
        && std::abs(partyDeltaZ) <= partySenseRange
        && isWithinRange3d(partyDeltaX, partyDeltaY, partyDeltaZ, partySenseRange);
    facts.target.partyCanSenseActor = actorCanSenseParty;

    float bestTargetDistanceSquared = std::numeric_limits<float>::max();

    if (active && actorCanSenseParty)
    {
        const float distanceToParty = length3d(partyDeltaX, partyDeltaY, partyDeltaZ);
        facts.target.currentKind = ActorAiTargetKind::Party;
        facts.target.currentPosition = partyTargetPoint;
        facts.target.currentAudioPosition = facts.target.currentPosition;
        facts.target.currentDistance = distanceToParty;
        facts.target.currentEdgeDistance =
            std::max(0.0f, distanceToParty - static_cast<float>(radius) - partyFacts.collisionRadius);
        facts.target.currentCanSense = true;
        facts.target.currentHasAttackLineOfSight = hasCombatLineOfSightToParty;
        bestTargetDistanceSquared = distanceToParty * distanceToParty;
    }

    if (active)
    {
        facts.target.candidates.reserve(pMapDeltaData->actors.size() > 0 ? pMapDeltaData->actors.size() - 1 : 0);

        for (size_t otherActorIndex = 0; otherActorIndex < pMapDeltaData->actors.size(); ++otherActorIndex)
        {
            if (otherActorIndex == actorIndex || otherActorIndex >= m_mapActorAiStates.size())
            {
                continue;
            }

            const MapDeltaActor &otherActor = pMapDeltaData->actors[otherActorIndex];
            const MapActorAiState &otherAiState = m_mapActorAiStates[otherActorIndex];

            if (indoorActorUnavailableForCombat(otherActor, otherAiState, *pActorService))
            {
                continue;
            }

            const float deltaX = otherAiState.preciseX - aiState.preciseX;
            const float deltaY = otherAiState.preciseY - aiState.preciseY;

            if (std::abs(deltaX) > HostilityLongRange || std::abs(deltaY) > HostilityLongRange)
            {
                continue;
            }

            const uint16_t otherRadius = otherActor.radius != 0 ? otherActor.radius : uint16_t(32);
            const uint16_t otherHeight = otherActor.height != 0 ? otherActor.height : uint16_t(128);
            const bool otherHasEffectOverride = hasActiveActorSpellEffectOverride(otherAiState.spellEffects);
            const bool otherHostileToParty =
                otherHasEffectOverride ? otherAiState.spellEffects.hostileToParty : otherAiState.hostileToParty;
            const GameplayActorTargetPolicyState otherPolicyState =
                buildIndoorActorTargetPolicyState(
                    otherAiState,
                    otherAiState.spellEffects,
                    otherHeight,
                    otherHostileToParty,
                    otherActor.group,
                    otherActor.ally);
            const float otherTargetZ =
                otherAiState.preciseZ + std::max(24.0f, static_cast<float>(otherHeight) * 0.7f);
            const GameplayWorldPoint otherTargetPoint = {otherAiState.preciseX, otherAiState.preciseY, otherTargetZ};
            const bool hasLineOfSight =
                otherActor.sectorId == actorSectorId
                || (m_pIndoorMapData != nullptr
                    && !vertices.empty()
                    && indoorDetectBetweenObjects(
                        *m_pIndoorMapData,
                        vertices,
                        geometryCache,
                        actorTargetPoint,
                        actorSectorId,
                        otherTargetPoint,
                        otherActor.sectorId));

            ActorTargetCandidateFacts candidate = {};
            candidate.kind = ActorAiTargetKind::Actor;
            candidate.actorIndex = otherActorIndex;
            candidate.actorId = otherAiState.actorId;
            candidate.monsterId = otherAiState.monsterId;
            candidate.currentHp = otherActor.hp;
            candidate.policy = otherPolicyState;
            candidate.position = otherTargetPoint;
            candidate.audioPosition =
                GameplayWorldPoint{
                    otherAiState.preciseX,
                    otherAiState.preciseY,
                    otherAiState.preciseZ + static_cast<float>(otherHeight) * 0.5f};
            candidate.radius = otherRadius;
            candidate.height = otherHeight;
            candidate.unavailable = false;
            candidate.hasLineOfSight = hasLineOfSight;
            facts.target.candidates.push_back(candidate);

            if (!hasLineOfSight)
            {
                continue;
            }

            const GameplayActorTargetPolicyResult targetPolicy =
                pActorService->resolveActorTargetPolicy(actorPolicyState, otherPolicyState);

            if (!targetPolicy.canTarget)
            {
                continue;
            }

            const float deltaZ = otherTargetZ - actorTargetZ;
            const float distanceSquared = lengthSquared3d(deltaX, deltaY, deltaZ);

            if (distanceSquared >= bestTargetDistanceSquared
                || !isWithinRange3d(deltaX, deltaY, deltaZ, targetPolicy.engagementRange))
            {
                continue;
            }

            const float distanceToTarget = std::sqrt(distanceSquared);
            facts.target.currentKind = ActorAiTargetKind::Actor;
            facts.target.currentActorIndex = otherActorIndex;
            facts.target.currentRelationToTarget = targetPolicy.relationToTarget;
            facts.target.currentHp = otherActor.hp;
            facts.target.currentPosition = candidate.position;
            facts.target.currentAudioPosition = candidate.audioPosition;
            facts.target.currentDistance = distanceToTarget;
            facts.target.currentEdgeDistance =
                std::max(0.0f, distanceToTarget - static_cast<float>(radius) - static_cast<float>(otherRadius));
            facts.target.currentCanSense = true;
            facts.target.currentHasAttackLineOfSight = true;
            bestTargetDistanceSquared = distanceSquared;
        }
    }

    if (facts.target.currentKind == ActorAiTargetKind::Party)
    {
        facts.stats.attackConstraints.rangedCommitAllowed = hasCombatLineOfSightToParty;
    }

    facts.movement.position = GameplayWorldPoint{aiState.preciseX, aiState.preciseY, aiState.preciseZ};
    facts.movement.homePosition =
        GameplayWorldPoint{aiState.homePreciseX, aiState.homePreciseY, aiState.homePreciseZ};
    facts.movement.moveDirectionX = aiState.moveDirectionX;
    facts.movement.moveDirectionY = aiState.moveDirectionY;
    facts.movement.velocityX = aiState.velocityX;
    facts.movement.velocityY = aiState.velocityY;
    facts.movement.velocityZ = aiState.velocityZ;
    facts.movement.wanderRadius = wanderRadiusForMovementType(pStats->movementType);
    facts.movement.effectiveMoveSpeed =
        pActorService->effectiveActorMoveSpeed(
            moveSpeed,
            pStats->speed,
            aiState.spellEffects.slowMoveMultiplier,
            aiState.spellEffects.darkGraspRemainingSeconds > 0.0f);
    facts.movement.distanceToParty =
        length2d(partyFacts.position.x - aiState.preciseX, partyFacts.position.y - aiState.preciseY);
    facts.movement.edgeDistanceToParty =
        std::max(0.0f, facts.movement.distanceToParty - static_cast<float>(radius) - partyFacts.collisionRadius);
    facts.movement.inMeleeRange =
        facts.target.currentCanSense
        && facts.target.currentEdgeDistance <=
            meleeRangeForCombatTarget(facts.target.currentKind == ActorAiTargetKind::Actor);
    facts.movement.allowIdleWander = m_pGameplayActorService != nullptr;
    facts.movement.movementAllowed = pStats->movementType != MonsterTable::MonsterMovementType::Stationary;
    facts.movement.movementBlocked = false;

    facts.world.targetZ = actorTargetZ;
    facts.world.floorZ = aiState.preciseZ;
    facts.world.sectorId = actorSectorId;
    facts.world.active = active;
    facts.world.activeByDistance = active;
    facts.world.sameSectorAsParty = sameSectorAsParty;
    facts.world.portalPathToParty = activeCanKeepPartyTarget;
    return facts;
}

const std::string &IndoorWorldRuntime::mapName() const
{
    return m_mapName;
}

bool IndoorWorldRuntime::isIndoorMap() const
{
    return true;
}

const std::vector<uint8_t> *IndoorWorldRuntime::journalMapFullyRevealedCells() const
{
    return nullptr;
}

const std::vector<uint8_t> *IndoorWorldRuntime::journalMapPartiallyRevealedCells() const
{
    return nullptr;
}

int IndoorWorldRuntime::restFoodRequired() const
{
    int foodRequired = 2;

    if (m_pPartyRuntime == nullptr)
    {
        return foodRequired;
    }

    constexpr uint32_t DragonRaceId = 5;
    const Party &partyState = m_pPartyRuntime->party();

    for (const Character &member : partyState.members())
    {
        if (member.raceId == DragonRaceId)
        {
            ++foodRequired;
            break;
        }
    }

    return std::max(1, foodRequired);
}

float IndoorWorldRuntime::currentGameMinutes() const
{
    return m_gameMinutes;
}

float IndoorWorldRuntime::gameMinutes() const
{
    return m_gameMinutes;
}

int IndoorWorldRuntime::currentHour() const
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(m_gameMinutes)));
    return (totalMinutes / 60) % 24;
}

void IndoorWorldRuntime::advanceGameMinutes(float minutes)
{
    if (minutes > 0.0f)
    {
        m_gameMinutes += minutes;
    }
}

int IndoorWorldRuntime::currentLocationReputation() const
{
    return m_currentLocationReputation;
}

void IndoorWorldRuntime::setCurrentLocationReputation(int reputation)
{
    m_currentLocationReputation = reputation;
}

Party *IndoorWorldRuntime::party()
{
    return m_pParty;
}

const Party *IndoorWorldRuntime::party() const
{
    return m_pParty;
}

float IndoorWorldRuntime::partyX() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyX() : 0.0f;
}

float IndoorWorldRuntime::partyY() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyY() : 0.0f;
}

float IndoorWorldRuntime::partyFootZ() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyFootZ() : 0.0f;
}

void IndoorWorldRuntime::syncSpellMovementStatesFromPartyBuffs()
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->syncSpellMovementStatesFromPartyBuffs();
    }
}

void IndoorWorldRuntime::requestPartyJump()
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->requestJump();
    }
}

void IndoorWorldRuntime::setAlwaysRunEnabled(bool enabled)
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->setAlwaysRunEnabled(enabled);
    }
}

void IndoorWorldRuntime::updateWorldMovement(
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput)
{
    if (m_pRenderer != nullptr)
    {
        m_pRenderer->updateWorldMovement(input, deltaSeconds, allowWorldInput);
    }
}

void IndoorWorldRuntime::updateActorAi(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || m_pGameplayActorService == nullptr)
    {
        return;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    syncMapActorAiStates();

    m_actorUpdateAccumulatorSeconds =
        std::min(m_actorUpdateAccumulatorSeconds + deltaSeconds, MaxAccumulatedActorUpdateSeconds);

    while (m_actorUpdateAccumulatorSeconds >= ActorUpdateStepSeconds)
    {
        const ActorAiFrameFacts actorAiFacts = collectIndoorActorAiFrameFacts(ActorUpdateStepSeconds);
        const GameplayActorAiSystem actorAiSystem = {};
        const ActorAiFrameResult actorAiResult = actorAiSystem.updateActors(actorAiFacts);
        const std::vector<bool> spellEffectsAppliedMask =
            applyIndoorActorAiFrameResult(actorAiResult, actorAiSystem);

        for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
        {
            const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
            GameplayActorSpellEffectState &effectState = m_mapActorAiStates[actorIndex].spellEffects;

            if (!hasActiveActorSpellEffectOverride(effectState)
                || (actorIndex < spellEffectsAppliedMask.size() && spellEffectsAppliedMask[actorIndex]))
            {
                continue;
            }

            m_pGameplayActorService->updateSpellEffectTimers(
                effectState,
                ActorUpdateStepSeconds,
                m_mapActorAiStates[actorIndex].hostileToParty);
        }

        m_actorUpdateAccumulatorSeconds -= ActorUpdateStepSeconds;
    }
}

void IndoorWorldRuntime::updateWorld(float deltaSeconds)
{
    updateWorldItems(deltaSeconds);
    updateIndoorProjectiles(deltaSeconds);
}

void IndoorWorldRuntime::renderWorld(
    int width,
    int height,
    const GameplayInputFrame &input,
    float deltaSeconds)
{
    if (m_pGameplayView != nullptr)
    {
        m_pGameplayView->render(width, height, input, deltaSeconds);
    }

    updateIndoorJournalRevealIfNeeded();
}

void IndoorWorldRuntime::updateIndoorJournalRevealIfNeeded()
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (m_pIndoorMapData != nullptr && m_pRenderer != nullptr && m_pPartyRuntime != nullptr && pMapDeltaData != nullptr)
    {
        const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
        const EventRuntimeState *pEventRuntimeState = eventRuntimeState();
        const uint64_t surfaceRevision =
            pEventRuntimeState != nullptr ? pEventRuntimeState->outdoorSurfaceRevision : 0;
        const bool needsRevealUpdate =
            !m_indoorJournalRevealStateValid
            || m_lastIndoorJournalRevealSectorId != moveState.sectorId
            || m_lastIndoorJournalRevealEyeSectorId != moveState.eyeSectorId
            || m_lastIndoorJournalRevealSurfaceRevision != surfaceRevision
            || m_lastIndoorJournalRevealFaceCount != m_pIndoorMapData->faces.size()
            || m_lastIndoorJournalRevealOutlineCount != m_pIndoorMapData->outlines.size();

        if (!needsRevealUpdate)
        {
            return;
        }

        const std::vector<int16_t> revealSectorIds =
            m_pRenderer->visibleIndoorMapRevealSectorIds(moveState.sectorId, moveState.eyeSectorId);
        updateIndoorJournalRevealMask(
            *m_pIndoorMapData,
            revealSectorIds,
            pEventRuntimeState,
            *pMapDeltaData);
        m_indoorJournalRevealStateValid = true;
        m_lastIndoorJournalRevealSectorId = moveState.sectorId;
        m_lastIndoorJournalRevealEyeSectorId = moveState.eyeSectorId;
        m_lastIndoorJournalRevealSurfaceRevision = surfaceRevision;
        m_lastIndoorJournalRevealFaceCount = m_pIndoorMapData->faces.size();
        m_lastIndoorJournalRevealOutlineCount = m_pIndoorMapData->outlines.size();
    }
}

void IndoorWorldRuntime::setMapActorHostilityFromEvent(size_t actorIndex, bool hostileToParty)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return;
    }

    syncMapActorAiStates();

    MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    if (hostileToParty)
    {
        actor.attributes |= static_cast<uint32_t>(EvtActorAttribute::Hostile)
            | static_cast<uint32_t>(EvtActorAttribute::Aggressor)
            | static_cast<uint32_t>(EvtActorAttribute::Active)
            | static_cast<uint32_t>(EvtActorAttribute::FullAi);
    }
    else
    {
        actor.attributes &= ~(static_cast<uint32_t>(EvtActorAttribute::Hostile)
            | static_cast<uint32_t>(EvtActorAttribute::Aggressor)
            | static_cast<uint32_t>(EvtActorAttribute::Nearby));
    }

    const bool detectedParty = hostileToParty;

    if (actorIndex < m_mapActorAiStates.size())
    {
        MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
        aiState.hostileToParty = hostileToParty;
        aiState.hasDetectedParty = detectedParty;
        aiState.spellEffects.hostileToParty = hostileToParty;
        aiState.spellEffects.hasDetectedParty = detectedParty;
    }
}

void IndoorWorldRuntime::aggroNearbyMapActorFaction(size_t actorIndex)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size() || m_pMonsterTable == nullptr)
    {
        return;
    }

    syncMapActorAiStates();

    const MapDeltaActor &victim = pMapDeltaData->actors[actorIndex];
    const int16_t victimMonsterId = resolveIndoorActorStatsId(victim);
    const float victimX =
        actorIndex < m_mapActorAiStates.size() ? m_mapActorAiStates[actorIndex].preciseX : static_cast<float>(victim.x);
    const float victimY =
        actorIndex < m_mapActorAiStates.size() ? m_mapActorAiStates[actorIndex].preciseY : static_cast<float>(victim.y);
    const float victimZ =
        actorIndex < m_mapActorAiStates.size() ? m_mapActorAiStates[actorIndex].preciseZ : static_cast<float>(victim.z);

    for (size_t otherActorIndex = 0; otherActorIndex < pMapDeltaData->actors.size(); ++otherActorIndex)
    {
        if (otherActorIndex == actorIndex)
        {
            continue;
        }

        const MapDeltaActor &otherActor = pMapDeltaData->actors[otherActorIndex];

        if (otherActor.hp <= 0
            || (otherActor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
        {
            continue;
        }

        const bool sameEventGroup = victim.group != 0 && victim.group == otherActor.group;
        const bool sameMonsterFaction =
            m_pMonsterTable->isLikelySameFaction(victimMonsterId, resolveIndoorActorStatsId(otherActor));

        if (!sameEventGroup && !sameMonsterFaction)
        {
            continue;
        }

        const float otherX = otherActorIndex < m_mapActorAiStates.size()
            ? m_mapActorAiStates[otherActorIndex].preciseX
            : static_cast<float>(otherActor.x);
        const float otherY = otherActorIndex < m_mapActorAiStates.size()
            ? m_mapActorAiStates[otherActorIndex].preciseY
            : static_cast<float>(otherActor.y);
        const float otherZ = otherActorIndex < m_mapActorAiStates.size()
            ? m_mapActorAiStates[otherActorIndex].preciseZ
            : static_cast<float>(otherActor.z);
        const float distance = length3d(otherX - victimX, otherY - victimY, otherZ - victimZ);

        if (distance > IndoorFactionAggroRange)
        {
            continue;
        }

        setMapActorHostilityFromEvent(otherActorIndex, true);
    }
}

GameplayWorldUiRenderState IndoorWorldRuntime::gameplayUiRenderState(int width, int height) const
{
    if (m_pGameplayView == nullptr)
    {
        return GameplayWorldUiRenderState{.renderGameplayHud = false};
    }

    return m_pGameplayView->gameplayUiRenderState(width, height);
}

bool IndoorWorldRuntime::requestTravelAutosave()
{
    return false;
}

void IndoorWorldRuntime::cancelPendingMapTransition()
{
}

bool IndoorWorldRuntime::executeNpcTopicEvent(uint16_t eventId, size_t &previousMessageCount)
{
    EventRuntimeState *pEventRuntimeState = eventRuntimeState();

    if (m_pEventRuntime == nullptr || pEventRuntimeState == nullptr || eventId == 0)
    {
        return false;
    }

    previousMessageCount = pEventRuntimeState->messages.size();

    const bool executed = m_pEventRuntime->executeNpcTopicEventById(
        m_pLocalEventProgram != nullptr ? *m_pLocalEventProgram : std::optional<ScriptedEventProgram>{},
        m_pGlobalEventProgram != nullptr ? *m_pGlobalEventProgram : std::optional<ScriptedEventProgram>{},
        eventId,
        *pEventRuntimeState,
        m_pParty,
        this);

    if (!executed)
    {
        return false;
    }

    applyEventRuntimeState();

    if (m_pParty != nullptr)
    {
        m_pParty->applyEventRuntimeState(*pEventRuntimeState, false);
    }

    return true;
}

const std::optional<ScriptedEventProgram> *IndoorWorldRuntime::globalEventProgram() const
{
    return m_pGlobalEventProgram;
}

bool IndoorWorldRuntime::castEventSpell(
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
    if (m_pParty != nullptr
        && tryApplyEventSpellBuffs(*m_pParty, spellId, skillLevel, skillMastery))
    {
        if (m_pEventRuntimeState != nullptr && *m_pEventRuntimeState)
        {
            EventRuntimeState::SpellFxRequest request = {};
            request.spellId = spellId;
            request.memberIndices = buildAllIndoorPartyMemberIndices(*m_pParty);
            (*m_pEventRuntimeState)->spellFxRequests.push_back(std::move(request));
        }

        return true;
    }

    if (m_pGameplayProjectileService == nullptr || m_pObjectTable == nullptr || m_pSpellTable == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    IndoorResolvedProjectileDefinition definition = {};

    if (!fillIndoorProjectileDefinitionFromSpell(*pSpellEntry, *m_pObjectTable, definition))
    {
        return false;
    }

    const uint16_t objectSpriteFrameIndex = resolveRuntimeProjectileSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    GameplayProjectileService::ProjectileSpawnRequest spawnRequest = {};
    spawnRequest.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Event;
    spawnRequest.sourceId = EventSpellSourceId;
    spawnRequest.ability = GameplayProjectileService::MonsterAttackAbility::Spell1;
    spawnRequest.definition = buildIndoorGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    spawnRequest.skillLevel = skillLevel;
    spawnRequest.skillMastery = static_cast<uint32_t>(normalizeIndoorEventSkillMastery(skillMastery));
    spawnRequest.damageType = GameMechanics::spellCombatDamageType(spellId, m_pSpellTable);
    spawnRequest.sourceX = static_cast<float>(fromX);
    spawnRequest.sourceY = static_cast<float>(fromY);
    spawnRequest.sourceZ = static_cast<float>(fromZ);
    spawnRequest.targetX = static_cast<float>(toX);
    spawnRequest.targetY = static_cast<float>(toY);
    spawnRequest.targetZ = static_cast<float>(toZ);
    if (m_pIndoorMapData != nullptr)
    {
        RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();
        spawnRequest.sectorId =
            resolveIndoorPointSector(
                m_pIndoorMapData,
                runtimeGeometry.vertices,
                &runtimeGeometry.geometryCache,
                {spawnRequest.sourceX, spawnRequest.sourceY, spawnRequest.sourceZ},
                -1);
    }
    spawnRequest.allowInstantImpact = true;

    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        m_pGameplayProjectileService->spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        m_pGameplayProjectileService->buildProjectileSpawnEffects(spawnResult);

    if (indoorProjectileDebugEnabled())
    {
        std::cout
            << "IndoorProjectileSpawn"
            << " source=event"
            << " kind=" << indoorProjectileSpawnKindName(spawnResult.kind)
            << " accepted=" << (spawnEffects.accepted ? 1 : 0)
            << " projectileId=" << spawnResult.projectile.projectileId
            << " spell=" << definition.spellId
            << " object=\"" << definition.objectName << "\""
            << " sprite=\"" << definition.objectSpriteName << "\""
            << " flags=0x" << std::hex << definition.objectFlags << std::dec
            << " radius=" << definition.radius
            << " height=" << definition.height
            << " speed=" << definition.speed
            << " source=(" << spawnRequest.sourceX << "," << spawnRequest.sourceY << ","
            << spawnRequest.sourceZ << ")"
            << " target=(" << spawnRequest.targetX << "," << spawnRequest.targetY << ","
            << spawnRequest.targetZ << ")"
            << " dir=(" << spawnResult.directionX << "," << spawnResult.directionY << ","
            << spawnResult.directionZ << ")"
            << '\n';
    }

    if (!spawnEffects.accepted)
    {
        return false;
    }

    if (spawnEffects.playReleaseAudio && spawnEffects.releaseAudioRequest)
    {
        pushIndoorProjectileAudioEvent(*spawnEffects.releaseAudioRequest);
    }

    if (spawnEffects.spawnInstantImpact)
    {
        spawnIndoorProjectileImpactVisual(
            spawnResult.projectile,
            {spawnEffects.impactX, spawnEffects.impactY, spawnEffects.impactZ},
            false);
    }

    return true;
}

bool IndoorWorldRuntime::specialJump(uint32_t encodedHorizontalVelocity, uint32_t verticalVelocity)
{
    if (m_pPartyRuntime == nullptr)
    {
        return false;
    }

    const float horizontalSpeed = static_cast<float>(encodedHorizontalVelocity >> 16);
    const float angleRadians =
        static_cast<float>(encodedHorizontalVelocity & 0xffffu) * (Pi * 2.0f / SpecialJumpAngleUnitsPerTurn);

    m_pPartyRuntime->requestSpecialJump(
        std::cos(angleRadians) * horizontalSpeed,
        std::sin(angleRadians) * horizontalSpeed,
        static_cast<float>(verticalVelocity));
    return true;
}

size_t IndoorWorldRuntime::mapActorCount() const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();
    return pMapDeltaData != nullptr ? pMapDeltaData->actors.size() : 0;
}

const IndoorWorldRuntime::MapActorAiState *IndoorWorldRuntime::mapActorAiState(size_t actorIndex) const
{
    if (actorIndex >= m_mapActorAiStates.size())
    {
        return nullptr;
    }

    return &m_mapActorAiStates[actorIndex];
}

size_t IndoorWorldRuntime::bloodSplatCount() const
{
    return m_bloodSplats.size();
}

const IndoorWorldRuntime::BloodSplatState *IndoorWorldRuntime::bloodSplatState(size_t splatIndex) const
{
    if (splatIndex >= m_bloodSplats.size())
    {
        return nullptr;
    }

    return &m_bloodSplats[splatIndex];
}

uint64_t IndoorWorldRuntime::bloodSplatRevision() const
{
    return m_bloodSplatRevision;
}

void IndoorWorldRuntime::collectProjectilePresentationState(
    std::vector<GameplayProjectilePresentationState> &projectiles,
    std::vector<GameplayProjectileImpactPresentationState> &impacts) const
{
    if (m_pGameplayProjectileService == nullptr)
    {
        projectiles.clear();
        impacts.clear();
        return;
    }

    m_pGameplayProjectileService->collectProjectilePresentationState(projectiles, impacts);
}

bool IndoorWorldRuntime::actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const bool isInvisible =
        (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0;
    const bool isAggressive =
        (actor.attributes & (static_cast<uint32_t>(EvtActorAttribute::Nearby)
            | static_cast<uint32_t>(EvtActorAttribute::Aggressor))) != 0;
    const int16_t resolvedMonsterId = resolveIndoorActorStatsId(actor);
    GameplayActorService actorService = {};
    const int16_t relationMonsterId = actorService.relationMonsterId(resolvedMonsterId, actor.ally);
    const bool hostileToParty =
        (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Aggressor)) != 0
        || (m_pMonsterTable != nullptr
            && relationMonsterId > 0
            && m_pMonsterTable->isHostileToParty(relationMonsterId));
    const bool defaultDetectedParty = hostileToParty && isAggressive;
    const MapActorAiState *pAiState =
        actorIndex < m_mapActorAiStates.size() ? &m_mapActorAiStates[actorIndex] : nullptr;
    const GameplayActorSpellEffectState *pEffectState =
        pAiState != nullptr ? &pAiState->spellEffects : nullptr;
    const bool useEffectOverride = pEffectState != nullptr && hasActiveActorSpellEffectOverride(*pEffectState);

    state.monsterId = resolvedMonsterId;
    state.preciseX = pAiState != nullptr ? pAiState->preciseX : static_cast<float>(actor.x);
    state.preciseY = pAiState != nullptr ? pAiState->preciseY : static_cast<float>(actor.y);
    state.preciseZ = pAiState != nullptr ? pAiState->preciseZ : static_cast<float>(actor.z);
    state.radius = pAiState != nullptr ? pAiState->collisionRadius : actor.radius;
    state.height = pAiState != nullptr ? pAiState->collisionHeight : actor.height;
    state.isDead = pAiState != nullptr
        ? pAiState->motionState == ActorAiMotionState::Dead
        : actor.hp <= 0;
    state.isInvisible = isInvisible;
    state.hostileToParty = useEffectOverride ? pEffectState->hostileToParty
        : pAiState != nullptr ? pAiState->hostileToParty : hostileToParty;
    state.hasDetectedParty = useEffectOverride ? pEffectState->hasDetectedParty
        : pAiState != nullptr ? pAiState->hasDetectedParty : defaultDetectedParty;
    return true;
}

bool IndoorWorldRuntime::actorInspectState(
    size_t actorIndex,
    uint32_t animationTicks,
    GameplayActorInspectState &state) const
{
    state = {};

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr
        || m_pMonsterTable == nullptr
        || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const int16_t resolvedMonsterId = resolveIndoorActorStatsId(actor);
    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(resolvedMonsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    state.displayName = resolveMapDeltaActorName(*m_pMonsterTable, actor);
    state.monsterId = resolvedMonsterId;
    state.currentHp = std::max(0, static_cast<int>(actor.hp));
    state.maxHp = std::max(0, pStats->hitPoints);
    state.isDead = actorIndex < m_mapActorAiStates.size()
        ? m_mapActorAiStates[actorIndex].motionState == ActorAiMotionState::Dead
        : actor.hp <= 0;

    int armorClass = pStats->armorClass;
    const MapActorAiState *pAiState =
        actorIndex < m_mapActorAiStates.size() ? &m_mapActorAiStates[actorIndex] : nullptr;
    const GameplayActorSpellEffectState *pEffectState =
        pAiState != nullptr ? &pAiState->spellEffects : nullptr;

    if (pEffectState != nullptr)
    {
        state.slowRemainingSeconds = pEffectState->slowRemainingSeconds;
        state.stunRemainingSeconds = pEffectState->stunRemainingSeconds;
        state.paralyzeRemainingSeconds = pEffectState->paralyzeRemainingSeconds;
        state.fearRemainingSeconds = pEffectState->fearRemainingSeconds;
        state.shrinkRemainingSeconds = pEffectState->shrinkRemainingSeconds;
        state.darkGraspRemainingSeconds = pEffectState->darkGraspRemainingSeconds;
        state.dayOfProtectionRemainingSeconds = pEffectState->dayOfProtectionRemainingSeconds;
        state.hourOfPowerRemainingSeconds = pEffectState->hourOfPowerRemainingSeconds;
        state.painReflectionRemainingSeconds = pEffectState->painReflectionRemainingSeconds;
        state.hammerhandsRemainingSeconds = pEffectState->hammerhandsRemainingSeconds;
        state.hasteRemainingSeconds = pEffectState->hasteRemainingSeconds;
        state.shieldRemainingSeconds = pEffectState->shieldRemainingSeconds;
        state.stoneskinRemainingSeconds = pEffectState->stoneskinRemainingSeconds;
        state.blessRemainingSeconds = pEffectState->blessRemainingSeconds;
        state.fateRemainingSeconds = pEffectState->fateRemainingSeconds;
        state.heroismRemainingSeconds = pEffectState->heroismRemainingSeconds;
        state.controlMode = pEffectState->controlMode;

        if (pAiState != nullptr && pAiState->motionState == ActorAiMotionState::Attacking)
        {
            std::string pendingSpellName;

            if (pAiState->queuedAttackAbility == GameplayActorAttackAbility::Spell1)
            {
                pendingSpellName = pStats->spell1Name;
            }
            else if (pAiState->queuedAttackAbility == GameplayActorAttackAbility::Spell2)
            {
                pendingSpellName = pStats->spell2Name;
            }

            if (indoorMonsterSelfBuffSpellName(pendingSpellName))
            {
                state.pendingSelfBuffName = pendingSpellName;
            }
        }

        if (m_pGameplayActorService != nullptr)
        {
            armorClass = m_pGameplayActorService->effectiveArmorClass(armorClass, *pEffectState);
        }
    }

    state.armorClass = armorClass;

    if (m_pActorSpriteFrameTable == nullptr)
    {
        return true;
    }

    const uint16_t spriteFrameIndex = m_mapActorAiStates[actorIndex].spriteFrameIndex;

    if (spriteFrameIndex == 0)
    {
        return true;
    }

    const SpriteFrameEntry *pFrame = m_pActorSpriteFrameTable->getFrame(spriteFrameIndex, animationTicks);

    if (pFrame == nullptr)
    {
        pFrame = m_pActorSpriteFrameTable->getFrame(spriteFrameIndex, 0);
    }

    if (pFrame == nullptr)
    {
        return true;
    }

    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
    state.previewTextureName = resolvedTexture.textureName;
    state.previewPaletteId = pFrame->paletteId;
    return true;
}

std::optional<GameplayCombatActorInfo> IndoorWorldRuntime::combatActorInfoById(uint32_t actorId) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorId >= pMapDeltaData->actors.size() || m_pMonsterTable == nullptr)
    {
        return std::nullopt;
    }

    const size_t actorIndex = actorId;
    GameplayActorInspectState inspectState = {};

    if (!actorInspectState(actorIndex, 0, inspectState))
    {
        return std::nullopt;
    }

    GameplayCombatActorInfo info = {};
    info.actorId = actorId;
    info.monsterId = inspectState.monsterId;
    info.maxHp = inspectState.maxHp;
    info.displayName = inspectState.displayName;
    if (actorIndex < m_mapActorAiStates.size() && m_pGameplayActorService != nullptr)
    {
        info.attackBonus = m_pGameplayActorService->effectiveAttackHitBonus(
            m_mapActorAiStates[actorIndex].spellEffects);
    }

    if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(inspectState.monsterId))
    {
        info.monsterLevel = pStats->level;
        info.attackPreferences = pStats->attackPreferences;
        info.specialAttackKind = pStats->specialAttackKind;
        info.specialAttackLevel = pStats->specialAttackLevel;
    }

    return info;
}

bool IndoorWorldRuntime::applyReflectedDamageToActor(
    uint32_t actorId,
    int damage,
    CombatDamageType damageType,
    uint32_t sourcePartyMemberIndex)
{
    (void)sourcePartyMemberIndex;

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorId >= pMapDeltaData->actors.size() || damage <= 0)
    {
        return false;
    }

    const size_t actorIndex = actorId;
    MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

    if ((actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
    {
        return false;
    }

    int appliedDamage = damage;
    const int16_t resolvedMonsterId = resolveIndoorActorStatsId(actor);
    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(resolvedMonsterId) : nullptr;

    if (pStats != nullptr)
    {
        std::mt19937 rng(
            actorId
            ^ static_cast<uint32_t>(std::max(0, damage)) * 2246822519u
            ^ static_cast<uint32_t>(damageType) * 3266489917u);
        appliedDamage = GameMechanics::resolveMonsterIncomingDamage(
            damage,
            damageType,
            pStats->level,
            monsterResistanceForDamageType(*pStats, damageType),
            rng);
    }

    const int previousHp = actor.hp;
    const int nextHp = std::max(0, previousHp - appliedDamage);
    actor.hp = static_cast<int16_t>(nextHp);

    syncMapActorAiStates();

    if (previousHp > 0 && nextHp <= 0)
    {
        beginMapActorDyingState(actorIndex, actor);
        const int maxHp = pStats != nullptr && pStats->hitPoints > 0 ? pStats->hitPoints : previousHp;
        const MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
        const bx::Vec3 knockback = actorKnockbackVelocity(
            aiState.preciseX,
            aiState.preciseY,
            aiState.preciseZ + static_cast<float>(aiState.collisionHeight) * 0.5f,
            partyX(),
            partyY(),
            partyFootZ(),
            appliedDamage,
            maxHp);
        m_mapActorAiStates[actorIndex].velocityX = knockback.x;
        m_mapActorAiStates[actorIndex].velocityY = knockback.y;
        m_mapActorAiStates[actorIndex].velocityZ = knockback.z;

        if (pStats != nullptr && pStats->experience > 0 && m_pParty != nullptr)
        {
            m_pParty->grantSharedExperience(static_cast<uint32_t>(pStats->experience));
        }
    }
    else if (previousHp > 0 && nextHp > 0)
    {
        GameplayWorldPoint source = {};
        source.x = partyX();
        source.y = partyY();
        source.z = partyFootZ();
        beginMapActorHitReaction(actorIndex, actor, &source);
    }

    return actor.hp != previousHp;
}

bool IndoorWorldRuntime::castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request)
{
    if (m_pGameplayProjectileService == nullptr || m_pObjectTable == nullptr || m_pSpellTable == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(request.spellId));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    IndoorResolvedProjectileDefinition definition = {};

    if (!fillIndoorProjectileDefinitionFromSpell(*pSpellEntry, *m_pObjectTable, definition))
    {
        return false;
    }

    const uint16_t objectSpriteFrameIndex = resolveRuntimeProjectileSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    GameplayProjectileService::ProjectileSpawnRequest spawnRequest = {};
    spawnRequest.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Party;
    spawnRequest.sourceId = request.casterMemberIndex + 1;
    spawnRequest.sourcePartyMemberIndex = request.casterMemberIndex;
    spawnRequest.definition = buildIndoorGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    if (request.effectSoundIdOverride > 0)
    {
        spawnRequest.definition.effectSoundId = static_cast<int>(request.effectSoundIdOverride);
    }
    spawnRequest.impactSoundIdOverride = request.impactSoundIdOverride;
    spawnRequest.skillLevel = request.skillLevel;
    spawnRequest.skillMastery = static_cast<uint32_t>(request.skillMastery);
    spawnRequest.damage = request.damage;
    spawnRequest.attackBonus = 0;
    spawnRequest.useActorHitChance = false;
    spawnRequest.damageType = GameMechanics::spellCombatDamageType(request.spellId, m_pSpellTable);
    spawnRequest.sourceX = request.sourceX;
    spawnRequest.sourceY = request.sourceY;
    spawnRequest.sourceZ = request.sourceZ;
    spawnRequest.targetX = request.targetX;
    spawnRequest.targetY = request.targetY;
    spawnRequest.targetZ = request.targetZ;
    if (m_pPartyRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
        spawnRequest.sectorId = moveState.eyeSectorId >= 0 ? moveState.eyeSectorId : moveState.sectorId;
    }
    spawnRequest.allowInstantImpact = true;

    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        m_pGameplayProjectileService->spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        m_pGameplayProjectileService->buildProjectileSpawnEffects(spawnResult);

    if (indoorProjectileDebugEnabled())
    {
        std::cout
            << "IndoorProjectileSpawn"
            << " source=party"
            << " caster=" << request.casterMemberIndex
            << " kind=" << indoorProjectileSpawnKindName(spawnResult.kind)
            << " accepted=" << (spawnEffects.accepted ? 1 : 0)
            << " projectileId=" << spawnResult.projectile.projectileId
            << " spell=" << definition.spellId
            << " object=\"" << definition.objectName << "\""
            << " sprite=\"" << definition.objectSpriteName << "\""
            << " flags=0x" << std::hex << definition.objectFlags << std::dec
            << " radius=" << definition.radius
            << " height=" << definition.height
            << " speed=" << definition.speed
            << " source=(" << spawnRequest.sourceX << "," << spawnRequest.sourceY << ","
            << spawnRequest.sourceZ << ")"
            << " target=(" << spawnRequest.targetX << "," << spawnRequest.targetY << ","
            << spawnRequest.targetZ << ")"
            << " dir=(" << spawnResult.directionX << "," << spawnResult.directionY << ","
            << spawnResult.directionZ << ")"
            << '\n';
    }

    if (!spawnEffects.accepted)
    {
        return false;
    }

    if (spawnEffects.playReleaseAudio && spawnEffects.releaseAudioRequest)
    {
        pushIndoorProjectileAudioEvent(*spawnEffects.releaseAudioRequest);
    }

    if (spawnEffects.spawnInstantImpact)
    {
        spawnIndoorProjectileImpactVisual(
            spawnResult.projectile,
            {spawnEffects.impactX, spawnEffects.impactY, spawnEffects.impactZ},
            false);
    }

    return true;
}

bool IndoorWorldRuntime::applyPartySpellToActor(
    size_t actorIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    int damage,
    float partyX,
    float partyY,
    float partyZ,
    uint32_t sourcePartyMemberIndex)
{
    (void)sourcePartyMemberIndex;

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const SpellId resolvedSpellId = spellIdFromValue(spellId);

    if ((actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
    {
        return false;
    }

    syncMapActorAiStates();
    if (actorIndex >= m_mapActorAiStates.size())
    {
        return false;
    }

    MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
    GameplayActorSpellEffectState &effectState = m_mapActorAiStates[actorIndex].spellEffects;
    const int16_t resolvedMonsterId = resolveIndoorActorStatsId(actor);
    const bool baselineHostileToParty = aiState.hostileToParty;
    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(resolvedMonsterId) : nullptr;
    GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService = m_pGameplayActorService;

    if (pActorService == nullptr)
    {
        fallbackActorService.bindTables(m_pMonsterTable, m_pSpellTable);
        pActorService = &fallbackActorService;
    }

    if (resolvedSpellId == SpellId::Reanimate)
    {
        if (actor.hp > 0)
        {
            return false;
        }

        const int targetMonsterLevel =
            skillMastery == SkillMastery::Grandmaster
                ? static_cast<int>(5 * skillLevel)
                : skillMastery == SkillMastery::Master
                ? static_cast<int>(4 * skillLevel)
                : skillMastery == SkillMastery::Expert
                ? static_cast<int>(3 * skillLevel)
                : static_cast<int>(2 * skillLevel);

        spawnImmediateSpellImpactVisualAt(
            {aiState.preciseX, aiState.preciseY, aiState.preciseZ + aiState.collisionHeight * 0.8f},
            spellId,
            false,
            false);

        if (pStats != nullptr && pStats->level > targetMonsterLevel)
        {
            return true;
        }

        const int hpLimit = std::max(1, targetMonsterLevel * 10);
        const int maxHp = pStats != nullptr && pStats->hitPoints > 0 ? pStats->hitPoints : hpLimit;
        actor.hp = static_cast<int16_t>(std::clamp(hpLimit, 1, maxHp));
        actor.currentActionAnimation = indoorActionAnimationFromActorAi(ActorAiAnimationState::Standing);
        actor.attributes |= static_cast<uint32_t>(EvtActorAttribute::Active)
            | static_cast<uint32_t>(EvtActorAttribute::FullAi);
        actor.attributes &= ~(static_cast<uint32_t>(EvtActorAttribute::Hostile)
            | static_cast<uint32_t>(EvtActorAttribute::Aggressor)
            | static_cast<uint32_t>(EvtActorAttribute::Nearby));
        aiState.motionState = ActorAiMotionState::Standing;
        aiState.animationState = ActorAiAnimationState::Standing;
        aiState.animationTimeTicks = 0.0f;
        aiState.actionSeconds = 0.0f;
        aiState.attackCooldownSeconds = aiState.recoverySeconds;
        aiState.hostileToParty = false;
        aiState.hasDetectedParty = false;
        pActorService->clearSpellEffects(effectState, false);
        effectState.hostileToParty = false;
        effectState.hasDetectedParty = false;
        effectState.controlMode = GameplayActorControlMode::Reanimated;
        effectState.controlRemainingSeconds = 24.0f * 60.0f * 60.0f;
        return true;
    }

    if (actor.hp <= 0)
    {
        return false;
    }

    if (pActorService != nullptr)
    {
        const GameplayActorService::DirectSpellImpactResult directImpact =
            pActorService->resolveDirectSpellImpact(
                spellId,
                skillLevel,
                damage,
                actor.hp,
                pActorService->actorLooksUndead(resolvedMonsterId));

        if (directImpact.disposition == GameplayActorService::DirectSpellImpactDisposition::Rejected)
        {
            return false;
        }

        if (directImpact.disposition == GameplayActorService::DirectSpellImpactDisposition::ApplyDamage)
        {
            int appliedDamage = directImpact.damage;
            const CombatDamageType damageType = GameMechanics::spellCombatDamageType(spellId, m_pSpellTable);

            if (pStats != nullptr)
            {
                std::mt19937 rng(
                    aiState.actorId
                    ^ spellId * 3266489917u
                    ^ static_cast<uint32_t>(std::max(0, directImpact.damage)));
                appliedDamage = GameMechanics::resolveMonsterIncomingDamage(
                    directImpact.damage,
                    damageType,
                    pStats->level,
                    monsterResistanceForDamageType(*pStats, damageType),
                    rng);
            }

            if (directImpact.visualKind == GameplayActorService::DirectSpellImpactVisualKind::ActorCenter)
            {
                spawnImmediateSpellImpactVisualAt(
                    {aiState.preciseX, aiState.preciseY, aiState.preciseZ + aiState.collisionHeight * 0.5f},
                    spellId,
                    directImpact.centerVisual,
                    directImpact.preferImpactObject);
            }
            else if (directImpact.visualKind == GameplayActorService::DirectSpellImpactVisualKind::ActorUpperBody)
            {
                spawnImmediateSpellImpactVisualAt(
                    {aiState.preciseX, aiState.preciseY, aiState.preciseZ + aiState.collisionHeight * 0.8f},
                    spellId,
                    directImpact.centerVisual,
                    directImpact.preferImpactObject);
            }

            return applyPartyAttackMeleeDamage(
                actorIndex,
                appliedDamage,
                {partyX, partyY, partyZ});
        }

        const GameplayActorService::SharedSpellEffectResult effectResult =
            pActorService->tryApplySharedSpellEffect(
                spellId,
                skillLevel,
                skillMastery,
                pActorService->actorLooksUndead(resolvedMonsterId),
                baselineHostileToParty,
                effectState);

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Rejected)
        {
            return false;
        }

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Applied)
        {
            if (effectResult.effectKind != GameplayActorService::SharedSpellEffectKind::DispelMagic
                && m_pRenderer != nullptr)
            {
                const uint32_t sequence =
                    m_pGameplayProjectileService != nullptr
                        ? m_pGameplayProjectileService->allocateProjectileImpactId()
                        : static_cast<uint32_t>(actorIndex + 1);
                const uint32_t seed =
                    aiState.actorId * 2246822519u
                    ^ spellId * 3266489917u
                    ^ sequence;
                m_pRenderer->worldFxSystem().spawnActorDebuffFx(
                    spellId,
                    seed,
                    aiState.preciseX,
                    aiState.preciseY,
                    aiState.preciseZ,
                    static_cast<float>(aiState.collisionHeight),
                    aiState.preciseX - partyX,
                    aiState.preciseY - partyY);
            }

            return true;
        }
    }

    if (damage <= 0)
    {
        return false;
    }

    const int previousHp = actor.hp;
    const int nextHp = std::clamp(
        previousHp - damage,
        static_cast<int>(std::numeric_limits<int16_t>::min()),
        previousHp);
    actor.hp = static_cast<int16_t>(nextHp);
    if (previousHp > 0 && actor.hp <= 0)
    {
        beginMapActorDyingState(actorIndex, actor);
        const int maxHp = pStats != nullptr && pStats->hitPoints > 0 ? pStats->hitPoints : previousHp;
        const bx::Vec3 knockback = actorKnockbackVelocity(
            aiState.preciseX,
            aiState.preciseY,
            aiState.preciseZ + static_cast<float>(aiState.collisionHeight) * 0.5f,
            partyX,
            partyY,
            partyZ,
            damage,
            maxHp);
        aiState.velocityX = knockback.x;
        aiState.velocityY = knockback.y;
        aiState.velocityZ = knockback.z;
    }
    else if (previousHp > 0 && actor.hp < previousHp)
    {
        const GameplayWorldPoint sourcePoint = {partyX, partyY, partyZ};
        beginMapActorHitReaction(actorIndex, actor, &sourcePoint);
    }

    return actor.hp != previousHp;
}

std::vector<size_t> IndoorWorldRuntime::collectMapActorIndicesWithinRadius(
    float centerX,
    float centerY,
    float centerZ,
    float radius,
    bool requireLineOfSight,
    float sourceX,
    float sourceY,
    float sourceZ) const
{
    (void)sourceX;
    (void)sourceY;
    (void)sourceZ;

    std::vector<size_t> result;

    if (radius <= 0.0f)
    {
        return result;
    }

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return result;
    }

    RuntimeGeometryCache *pRuntimeGeometry = nullptr;
    int16_t sourceSectorId = -1;
    const GameplayWorldPoint sourcePoint = {sourceX, sourceY, sourceZ};

    if (requireLineOfSight && m_pIndoorMapData != nullptr)
    {
        pRuntimeGeometry = &runtimeGeometryCache();

        if (!pRuntimeGeometry->vertices.empty())
        {
            sourceSectorId =
                findIndoorSectorForPoint(
                    *m_pIndoorMapData,
                    pRuntimeGeometry->vertices,
                    {sourceX, sourceY, sourceZ},
                    &pRuntimeGeometry->geometryCache,
                    false).value_or(-1);
        }

        if (sourceSectorId < 0 && m_pPartyRuntime != nullptr)
        {
            const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
            sourceSectorId = moveState.eyeSectorId >= 0 ? moveState.eyeSectorId : moveState.sectorId;
        }
    }

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!actorRuntimeState(actorIndex, actorState)
            || actorState.isDead
            || actorState.isInvisible)
        {
            continue;
        }

        const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
        const float targetZ =
            actorState.preciseZ + std::max(24.0f, static_cast<float>(actorState.height) * 0.7f);
        const float deltaX = actorState.preciseX - centerX;
        const float deltaY = actorState.preciseY - centerY;
        const float deltaZ = targetZ - centerZ;
        const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
        const float edgeDistance = std::max(0.0f, distance - static_cast<float>(actor.radius));

        if (edgeDistance > radius)
        {
            continue;
        }

        if (requireLineOfSight)
        {
            int16_t actorSectorId = actor.sectorId;

            if (actorIndex < m_mapActorAiStates.size() && m_mapActorAiStates[actorIndex].sectorId >= 0)
            {
                actorSectorId = m_mapActorAiStates[actorIndex].sectorId;
            }

            if (actorSectorId < 0
                && pRuntimeGeometry != nullptr
                && m_pIndoorMapData != nullptr
                && !pRuntimeGeometry->vertices.empty())
            {
                actorSectorId =
                    findIndoorSectorForPoint(
                        *m_pIndoorMapData,
                        pRuntimeGeometry->vertices,
                        {actorState.preciseX, actorState.preciseY, targetZ},
                        &pRuntimeGeometry->geometryCache,
                        false).value_or(-1);
            }

            const GameplayWorldPoint targetPoint = {actorState.preciseX, actorState.preciseY, targetZ};
            const bool hasLineOfSight =
                sourceSectorId >= 0
                && actorSectorId >= 0
                && (sourceSectorId == actorSectorId
                    || (pRuntimeGeometry != nullptr
                        && m_pIndoorMapData != nullptr
                        && !pRuntimeGeometry->vertices.empty()
                        && indoorDetectBetweenObjects(
                            *m_pIndoorMapData,
                            pRuntimeGeometry->vertices,
                            pRuntimeGeometry->geometryCache,
                            sourcePoint,
                            sourceSectorId,
                            targetPoint,
                            actorSectorId)));

            if (!hasLineOfSight)
            {
                continue;
            }
        }

        result.push_back(actorIndex);
    }

    return result;
}

bool IndoorWorldRuntime::spawnPartyFireSpikeTrap(
    uint32_t casterMemberIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    float x,
    float y,
    float z)
{
    (void)casterMemberIndex;
    (void)spellId;
    (void)skillLevel;
    (void)skillMastery;
    (void)x;
    (void)y;
    (void)z;
    return false;
}

bool IndoorWorldRuntime::summonFriendlyMonsterById(
    int16_t monsterId,
    uint32_t count,
    float durationSeconds,
    float x,
    float y,
    float z)
{
    (void)durationSeconds;
    if (m_pMonsterTable == nullptr || count == 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    const MonsterEntry *pMonsterEntry = m_pMonsterTable->findById(monsterId);

    if (pMonsterEntry == nullptr)
    {
        return false;
    }

    bool spawnedAny = false;

    for (uint32_t summonIndex = 0; summonIndex < count; ++summonIndex)
    {
        const float angleRadians = (Pi * 2.0f * summonIndex) / count;
        const float radius = 96.0f + 24.0f * float(summonIndex % 3u);
        MapDeltaActor actor = {};
        actor.name = pStats->name;
        actor.attributes = defaultActorAttributes(false);
        actor.hp = int16_t(std::clamp(pStats->hitPoints, 0, 32767));
        actor.hostilityType = 0;
        actor.monsterInfoId = int16_t(pStats->id);
        actor.monsterId = int16_t(pStats->id);
        actor.radius = pMonsterEntry->radius;
        actor.height = pMonsterEntry->height;
        actor.moveSpeed = pMonsterEntry->movementSpeed;
        actor.x = int(std::lround(x + std::cos(angleRadians) * radius));
        actor.y = int(std::lround(y + std::sin(angleRadians) * radius));
        actor.z = int(std::lround(z));
        actor.group = 999u;
        actor.ally = 999u;
        pMapDeltaData->actors.push_back(std::move(actor));
        spawnedAny = true;
    }

    syncMapActorAiStates();
    return spawnedAny;
}

bool IndoorWorldRuntime::tryStartArmageddon(
    size_t casterMemberIndex,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    std::string &failureText)
{
    (void)casterMemberIndex;
    (void)skillLevel;
    (void)skillMastery;
    failureText = "Spell failed";
    return false;
}

void IndoorWorldRuntime::beginMapActorDyingState(size_t actorIndex, MapDeltaActor &actor)
{
    syncMapActorAiStates();

    if (actorIndex >= m_mapActorAiStates.size())
    {
        return;
    }

    MapActorAiState &aiState = m_mapActorAiStates[actorIndex];

    if (aiState.motionState == ActorAiMotionState::Dying
        || aiState.motionState == ActorAiMotionState::Dead)
    {
        return;
    }

    aiState.motionState = ActorAiMotionState::Dying;
    aiState.animationState = ActorAiAnimationState::Dying;
    aiState.actionSeconds = aiState.dyingAnimationSeconds;
    aiState.animationTimeTicks = 0.0f;
    aiState.attackImpactTriggered = false;
    aiState.spellEffects.stunRemainingSeconds = 0.0f;
    aiState.spellEffects.paralyzeRemainingSeconds = 0.0f;
    aiState.velocityX = 0.0f;
    aiState.velocityY = 0.0f;
    aiState.velocityZ = 0.0f;
    actor.currentActionAnimation = indoorActionAnimationFromActorAi(ActorAiAnimationState::Dying);
}

void IndoorWorldRuntime::beginMapActorHitReaction(
    size_t actorIndex,
    MapDeltaActor &actor,
    const GameplayWorldPoint *pSource)
{
    syncMapActorAiStates();

    if (actorIndex >= m_mapActorAiStates.size())
    {
        return;
    }

    MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
    GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService =
        m_pGameplayActorService != nullptr ? m_pGameplayActorService : &fallbackActorService;
    const bool invisible = (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0;
    const bool canEnterHitReaction =
        pActorService->canActorEnterHitReaction(
            invisible,
            actor.hp <= 0 || aiState.motionState == ActorAiMotionState::Dead,
            actor.hp <= 0,
            aiState.motionState == ActorAiMotionState::Dying,
            aiState.motionState == ActorAiMotionState::Dead,
            aiState.motionState == ActorAiMotionState::Stunned,
            aiState.motionState == ActorAiMotionState::Attacking);

    if (!canEnterHitReaction)
    {
        return;
    }

    if (pSource != nullptr)
    {
        const float deltaX = pSource->x - aiState.preciseX;
        const float deltaY = pSource->y - aiState.preciseY;

        if (deltaX * deltaX + deltaY * deltaY > 0.0001f)
        {
            aiState.yawRadians = std::atan2(deltaY, deltaX);
        }
    }

    const MonsterEntry *pMonsterEntry =
        m_pMonsterTable != nullptr ? resolveRuntimeMonsterEntry(*m_pMonsterTable, actor) : nullptr;
    aiState.motionState = ActorAiMotionState::Stunned;
    aiState.animationState = ActorAiAnimationState::GotHit;
    aiState.animationTimeTicks = 0.0f;
    aiState.actionSeconds =
        actorAnimationSeconds(m_pActorSpriteFrameTable, pMonsterEntry, ActorAiAnimationState::GotHit, 0.25f);
    aiState.idleDecisionSeconds = std::max(aiState.idleDecisionSeconds, aiState.actionSeconds);
    aiState.attackImpactTriggered = false;
    aiState.velocityX = 0.0f;
    aiState.velocityY = 0.0f;
    aiState.velocityZ = 0.0f;
    actor.currentActionAnimation = indoorActionAnimationFromActorAi(ActorAiAnimationState::GotHit);
}

bool IndoorWorldRuntime::applyIndoorActorPhysicsStep(IndoorMovementController &movementController, size_t actorIndex)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr
        || m_pIndoorMapData == nullptr
        || m_pMonsterTable == nullptr
        || actorIndex >= pMapDeltaData->actors.size()
        || actorIndex >= m_mapActorAiStates.size())
    {
        return false;
    }

    MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(aiState.monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    const bool dying = aiState.motionState == ActorAiMotionState::Dying && actor.hp <= 0;
    const bool airborne = !pStats->canFly && !aiState.grounded;
    const bool hasVelocity =
        std::abs(aiState.velocityX) > 0.001f
        || std::abs(aiState.velocityY) > 0.001f
        || std::abs(aiState.velocityZ) > 0.001f;

    if (!dying && !airborne && !hasVelocity)
    {
        return false;
    }

    IndoorBodyDimensions body = {};
    body.radius = static_cast<float>(aiState.collisionRadius);
    body.height = static_cast<float>(aiState.collisionHeight);

    IndoorMoveState moveState = {};
    moveState.x = aiState.preciseX;
    moveState.y = aiState.preciseY;
    moveState.footZ = aiState.preciseZ;
    moveState.eyeHeight = body.height;
    moveState.verticalVelocity = aiState.velocityZ;
    moveState.sectorId = aiState.sectorId;
    moveState.eyeSectorId = aiState.eyeSectorId;
    moveState.supportFaceIndex = aiState.supportFaceIndex;
    moveState.grounded = aiState.grounded;

    const IndoorMoveState resolvedMoveState =
        movementController.resolveMove(
            moveState,
            body,
            aiState.velocityX,
            aiState.velocityY,
            false,
            ActorUpdateStepSeconds,
            nullptr,
            actorIndex,
            true,
            nullptr,
            pStats->canFly);

    const float deltaX = resolvedMoveState.x - aiState.preciseX;
    const float deltaY = resolvedMoveState.y - aiState.preciseY;
    aiState.preciseX = resolvedMoveState.x;
    aiState.preciseY = resolvedMoveState.y;
    aiState.preciseZ = resolvedMoveState.footZ;
    aiState.velocityX = deltaX / ActorUpdateStepSeconds;
    aiState.velocityY = deltaY / ActorUpdateStepSeconds;
    aiState.velocityZ = resolvedMoveState.verticalVelocity;
    const float inertiaDecay = actorInertiaDecayForStep(ActorUpdateStepSeconds);
    aiState.velocityX *= inertiaDecay;
    aiState.velocityY *= inertiaDecay;

    if (pStats->canFly)
    {
        aiState.velocityZ *= inertiaDecay;
    }

    if (aiState.velocityX * aiState.velocityX + aiState.velocityY * aiState.velocityY < ActorStopVelocitySquared)
    {
        aiState.velocityX = 0.0f;
        aiState.velocityY = 0.0f;
    }

    if (pStats->canFly && aiState.velocityZ * aiState.velocityZ < ActorStopVelocitySquared)
    {
        aiState.velocityZ = 0.0f;
    }

    aiState.sectorId = resolvedMoveState.sectorId;
    aiState.eyeSectorId = resolvedMoveState.eyeSectorId;
    aiState.supportFaceIndex = resolvedMoveState.supportFaceIndex;
    aiState.grounded = resolvedMoveState.grounded;
    movementController.updateActorColliderPosition(
        actorIndex,
        aiState.sectorId,
        aiState.preciseX,
        aiState.preciseY,
        aiState.preciseZ);

    actor.x = static_cast<int>(std::lround(aiState.preciseX));
    actor.y = static_cast<int>(std::lround(aiState.preciseY));
    actor.z = static_cast<int>(std::lround(aiState.preciseZ));
    return true;
}

bool IndoorWorldRuntime::canActivateWorldHit(
    const GameplayWorldHit &hit,
    GameplayInteractionMethod interactionMethod) const
{
    if (!hit.hasHit)
    {
        return false;
    }

    const GameSettings &settings =
        m_pGameplayView != nullptr ? m_pGameplayView->settingsSnapshot() : GameSettings::createDefault();
    const int configuredDepth = interactionMethod == GameplayInteractionMethod::Keyboard
        ? settings.keyboardInteractionDepth
        : settings.mouseInteractionDepth;
    const float interactionDepth = static_cast<float>(std::clamp(configuredDepth, 32, 4096));

    if (indoorWorldHitDistance(hit) >= interactionDepth)
    {
        return false;
    }

    if (hit.kind == GameplayWorldHitKind::Actor && hit.actor)
    {
        const MapDeltaData *pMapDeltaData = mapDeltaData();
        const size_t actorIndex = hit.actor->actorIndex;
        const MapActorAiState *pAiState =
            actorIndex < m_mapActorAiStates.size() ? &m_mapActorAiStates[actorIndex] : nullptr;

        return pMapDeltaData != nullptr
            && actorIndex < pMapDeltaData->actors.size()
            && pAiState != nullptr
            && pAiState->motionState == ActorAiMotionState::Dead
            && (pMapDeltaData->actors[actorIndex].attributes
                & static_cast<uint32_t>(EvtActorAttribute::Invisible)) == 0;
    }

    if (hit.kind == GameplayWorldHitKind::WorldItem && hit.worldItem)
    {
        const MapDeltaData *pMapDeltaData = mapDeltaData();

        return pMapDeltaData != nullptr
            && hit.worldItem->worldItemIndex < pMapDeltaData->spriteObjects.size()
            && hasContainingItemPayload(pMapDeltaData->spriteObjects[hit.worldItem->worldItemIndex].rawContainingItem);
    }

    return m_pRenderer != nullptr && m_pRenderer->canActivateGameplayWorldHit(hit);
}

bool IndoorWorldRuntime::activateWorldHit(const GameplayWorldHit &hit)
{
    if (hit.kind == GameplayWorldHitKind::Actor && hit.actor)
    {
        return autoLootMapActorCorpse(hit.actor->actorIndex);
    }

    if (hit.kind == GameplayWorldHitKind::WorldItem && hit.worldItem)
    {
        MapDeltaData *pMapDeltaData = mapDeltaData();

        if (pMapDeltaData == nullptr || hit.worldItem->worldItemIndex >= pMapDeltaData->spriteObjects.size())
        {
            return false;
        }

        MapDeltaSpriteObject &spriteObject = pMapDeltaData->spriteObjects[hit.worldItem->worldItemIndex];
        InventoryItem item = {};

        if (!readIndoorHeldItemPayload(spriteObject.rawContainingItem, m_pItemTable, item))
        {
            return false;
        }

        uint32_t goldAmount = 0;
        readRawItemUInt32(spriteObject.rawContainingItem, 0x0c, goldAmount);

        if (goldAmount > 0)
        {
            if (m_pParty == nullptr)
            {
                return false;
            }

            m_pParty->addGold(static_cast<int>(goldAmount));
            m_pParty->requestSound(SoundId::Gold);
            pMapDeltaData->spriteObjects.erase(
                pMapDeltaData->spriteObjects.begin() + std::ptrdiff_t(hit.worldItem->worldItemIndex));

            const std::string statusText = formatFoundGoldStatusText(static_cast<int>(goldAmount));

            if (m_pGameplayView != nullptr)
            {
                m_pGameplayView->setStatusBarEvent(statusText);
            }

            if (m_pEventRuntimeState != nullptr && *m_pEventRuntimeState)
            {
                (*m_pEventRuntimeState)->lastActivationResult = statusText;
            }

            return true;
        }

        size_t recipientMemberIndex = 0;

        if (m_pParty == nullptr || !m_pParty->tryGrantInventoryItem(item, &recipientMemberIndex))
        {
            return false;
        }

        const ItemDefinition *pItemDefinition =
            m_pItemTable != nullptr ? m_pItemTable->get(item.objectDescriptionId) : nullptr;
        const std::string itemName =
            pItemDefinition != nullptr && !pItemDefinition->name.empty() ? pItemDefinition->name : "item";

        pMapDeltaData->spriteObjects.erase(
            pMapDeltaData->spriteObjects.begin() + std::ptrdiff_t(hit.worldItem->worldItemIndex));
        m_pParty->requestSound(SoundId::Gold);

        if (m_pGameplayView != nullptr)
        {
            m_pGameplayView->setStatusBarEvent(formatFoundItemStatusText(itemName));
        }

        if (m_pEventRuntimeState != nullptr && *m_pEventRuntimeState)
        {
            (*m_pEventRuntimeState)->lastActivationResult = "picked up " + itemName;
        }

        (void)recipientMemberIndex;
        return true;
    }

    return m_pRenderer != nullptr && m_pRenderer->activateGameplayWorldHit(hit);
}

std::optional<GameplayPartyAttackActorFacts> IndoorWorldRuntime::partyAttackActorFacts(
    size_t actorIndex,
    bool visibleForFallback) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return std::nullopt;
    }

    GameplayRuntimeActorState runtimeState = {};
    GameplayActorInspectState inspectState = {};

    if (!actorRuntimeState(actorIndex, runtimeState) || !actorInspectState(actorIndex, 0, inspectState))
    {
        return std::nullopt;
    }

    return GameplayPartyAttackActorFacts{
        .actorIndex = actorIndex,
        .monsterId = inspectState.monsterId,
        .displayName = inspectState.displayName,
        .position =
            GameplayWorldPoint{
                .x = runtimeState.preciseX,
                .y = runtimeState.preciseY,
                .z = runtimeState.preciseZ,
            },
        .radius = runtimeState.radius,
        .height = runtimeState.height,
        .currentHp = inspectState.currentHp,
        .maxHp = inspectState.maxHp,
        .effectiveArmorClass = inspectState.armorClass,
        .isDead = runtimeState.isDead,
        .isInvisible = runtimeState.isInvisible,
        .hostileToParty = runtimeState.hostileToParty,
        .visibleForFallback = visibleForFallback,
    };
}

std::vector<GameplayPartyAttackActorFacts> IndoorWorldRuntime::collectPartyAttackFallbackActors(
    const GameplayPartyAttackFallbackQuery &query) const
{
    std::vector<GameplayPartyAttackActorFacts> actors;
    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, query.viewMatrix.data(), query.projectionMatrix.data());

    for (size_t actorIndex = 0; actorIndex < mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState runtimeState = {};

        if (!actorRuntimeState(actorIndex, runtimeState))
        {
            continue;
        }

        const bx::Vec3 projected = bx::mulH(
            {
                runtimeState.preciseX,
                runtimeState.preciseY,
                runtimeState.preciseZ + std::max(48.0f, float(runtimeState.height) * 0.6f),
            },
            viewProjectionMatrix);
        const bool visibleForFallback =
            projected.z >= 0.0f
            && projected.z <= 1.0f
            && projected.x >= -1.0f
            && projected.x <= 1.0f
            && projected.y >= -1.0f
            && projected.y <= 1.0f;
        std::optional<GameplayPartyAttackActorFacts> facts =
            partyAttackActorFacts(actorIndex, visibleForFallback);

        if (facts)
        {
            actors.push_back(*facts);
        }
    }

    return actors;
}

bool IndoorWorldRuntime::applyPartyAttackMeleeDamage(
    size_t actorIndex,
    int damage,
    const GameplayWorldPoint &source)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size() || damage <= 0)
    {
        return false;
    }

    MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

    if (actor.hp <= 0
        || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
    {
        return false;
    }

    const int previousHp = actor.hp;
    const int nextHp = std::max(0, previousHp - damage);
    actor.hp = static_cast<int16_t>(nextHp);
    actor.attributes |= static_cast<uint32_t>(EvtActorAttribute::Hostile)
        | static_cast<uint32_t>(EvtActorAttribute::Aggressor)
        | static_cast<uint32_t>(EvtActorAttribute::Active)
        | static_cast<uint32_t>(EvtActorAttribute::FullAi);

    syncMapActorAiStates();

    if (previousHp > 0 && nextHp <= 0)
    {
        beginMapActorDyingState(actorIndex, actor);
        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(resolveIndoorActorStatsId(actor)) : nullptr;
        const int maxHp = pStats != nullptr && pStats->hitPoints > 0 ? pStats->hitPoints : previousHp;
        const MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
        const bx::Vec3 knockback = actorKnockbackVelocity(
            aiState.preciseX,
            aiState.preciseY,
            aiState.preciseZ + static_cast<float>(aiState.collisionHeight) * 0.5f,
            source.x,
            source.y,
            source.z,
            damage,
            maxHp);
        m_mapActorAiStates[actorIndex].velocityX = knockback.x;
        m_mapActorAiStates[actorIndex].velocityY = knockback.y;
        m_mapActorAiStates[actorIndex].velocityZ = knockback.z;
    }

    if (actorIndex < m_mapActorAiStates.size())
    {
        MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
        if (m_pGameplayActorService != nullptr
            && m_pGameplayActorService->hasPainReflection(aiState.spellEffects)
            && m_pParty != nullptr)
        {
            m_pParty->applyDamageToActiveMember(damage, "pain reflection");
        }

        aiState.hostileToParty = true;
        aiState.hasDetectedParty = true;
        aiState.spellEffects.hostileToParty = true;
        aiState.spellEffects.hasDetectedParty = true;
    }

    if (previousHp > 0 && nextHp > 0)
    {
        beginMapActorHitReaction(actorIndex, actor, &source);
        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(resolveIndoorActorStatsId(actor)) : nullptr;
        const int maxHp = pStats != nullptr && pStats->hitPoints > 0 ? pStats->hitPoints : previousHp;
        const MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
        const bx::Vec3 knockback = actorKnockbackVelocity(
            aiState.preciseX,
            aiState.preciseY,
            aiState.preciseZ + static_cast<float>(aiState.collisionHeight) * 0.5f,
            source.x,
            source.y,
            source.z,
            damage,
            maxHp);
        m_mapActorAiStates[actorIndex].velocityX = knockback.x;
        m_mapActorAiStates[actorIndex].velocityY = knockback.y;
        m_mapActorAiStates[actorIndex].velocityZ = knockback.z;
    }

    if (previousHp > 0 && nextHp <= 0 && m_pMonsterTable != nullptr && m_pParty != nullptr)
    {
        const int16_t resolvedMonsterId = resolveIndoorActorStatsId(actor);
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(resolvedMonsterId);

        if (pStats != nullptr && pStats->experience > 0)
        {
            m_pParty->grantSharedExperience(static_cast<uint32_t>(pStats->experience));
        }
    }

    aggroNearbyMapActorFaction(actorIndex);
    return actor.hp != previousHp;
}

void IndoorWorldRuntime::applyPartyAttackMeleeEffects(
    size_t actorIndex,
    const CharacterAttackResult &attack,
    const GameplayWorldPoint &source)
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr
        || actorIndex >= pMapDeltaData->actors.size()
        || actorIndex >= m_mapActorAiStates.size()
        || (!attack.stunTarget && !attack.paralyzeTarget && !attack.halveTargetArmorClass))
    {
        return;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const MapActorAiState &aiState = m_mapActorAiStates[actorIndex];

    if (actor.hp <= 0
        || aiState.motionState == ActorAiMotionState::Dying
        || aiState.motionState == ActorAiMotionState::Dead)
    {
        return;
    }

    const uint32_t skillLevel = std::max<uint32_t>(1, attack.skillLevel);
    const float skillSeconds = static_cast<float>(skillLevel) * 60.0f;
    GameplayActorSpellEffectState &spellEffects = m_mapActorAiStates[actorIndex].spellEffects;

    if (attack.stunTarget)
    {
        spellEffects.stunRemainingSeconds =
            std::max(spellEffects.stunRemainingSeconds, 0.5f + 0.35f * static_cast<float>(skillLevel));
        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(resolveIndoorActorStatsId(actor)) : nullptr;
        const int maxHp = pStats != nullptr && pStats->hitPoints > 0 ? pStats->hitPoints : std::max<int>(1, actor.hp);
        const bx::Vec3 knockback = actorKnockbackVelocity(
            aiState.preciseX,
            aiState.preciseY,
            aiState.preciseZ + static_cast<float>(aiState.collisionHeight) * 0.5f,
            source.x,
            source.y,
            source.z,
            maxHp,
            maxHp);
        m_mapActorAiStates[actorIndex].velocityX = knockback.x;
        m_mapActorAiStates[actorIndex].velocityY = knockback.y;
        m_mapActorAiStates[actorIndex].velocityZ = knockback.z;
    }

    if (attack.paralyzeTarget)
    {
        spellEffects.paralyzeRemainingSeconds = std::max(spellEffects.paralyzeRemainingSeconds, skillSeconds);
    }

    if (attack.halveTargetArmorClass)
    {
        spellEffects.armorClassHalvedRemainingSeconds =
            std::max(spellEffects.armorClassHalvedRemainingSeconds, skillSeconds);
    }
}

bool IndoorWorldRuntime::spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request)
{
    if (request.damage <= 0)
    {
        return false;
    }

    const std::optional<size_t> actorIndex = findActorOnAttackLine(*this, request.source, request.target);

    if (!actorIndex)
    {
        return false;
    }

    const bool applied = applyPartyAttackMeleeDamage(*actorIndex, request.damage, request.source);

    if (applied)
    {
        spawnImmediateSpellImpactVisual(*actorIndex, 0);
    }

    return applied;
}

bool IndoorWorldRuntime::castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request)
{
    const std::optional<size_t> actorIndex = findActorOnAttackLine(*this, request.source, request.target);

    if (!actorIndex)
    {
        return false;
    }

    const bool applied = applyPartySpellToActor(
        *actorIndex,
        request.spellId,
        request.skillLevel,
        normalizeRuntimeSkillMastery(request.skillMastery),
        request.damage,
        request.source.x,
        request.source.y,
        request.source.z,
        static_cast<uint32_t>(request.sourcePartyMemberIndex));

    return applied;
}

void IndoorWorldRuntime::recordPartyAttackWorldResult(
    std::optional<size_t> actorIndex,
    bool attacked,
    bool actionPerformed)
{
    if (!m_pEventRuntimeState || !*m_pEventRuntimeState)
    {
        return;
    }

    if (actorIndex)
    {
        (*m_pEventRuntimeState)->lastActivationResult =
            attacked
                ? "actor " + std::to_string(*actorIndex) + " hit by party"
                : "actor " + std::to_string(*actorIndex) + " attacked by party";
        return;
    }

    (*m_pEventRuntimeState)->lastActivationResult =
        actionPerformed
            ? "party attack released"
            : "party attack failed";
}

bool IndoorWorldRuntime::worldInteractionReady() const
{
    return true;
}

bool IndoorWorldRuntime::worldInspectModeActive() const
{
    return true;
}

GameplayWorldPickRequest IndoorWorldRuntime::buildWorldPickRequest(const GameplayWorldPickRequestInput &input) const
{
    if (m_pRenderer != nullptr)
    {
        return m_pRenderer->buildGameplayWorldPickRequest(input);
    }

    GameplayWorldPickRequest request = {};
    request.screenX = input.screenX;
    request.screenY = input.screenY;
    request.viewWidth = input.screenWidth;
    request.viewHeight = input.screenHeight;
    return request;
}

std::optional<GameplayHeldItemDropRequest> IndoorWorldRuntime::buildHeldItemDropRequest() const
{
    if (m_pPartyRuntime == nullptr)
    {
        return std::nullopt;
    }

    const float yawRadians = m_pRenderer != nullptr ? m_pRenderer->cameraYawRadians() : 0.0f;
    const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
    return GameplayHeldItemDropRequest{
        .sourceX = moveState.x,
        .sourceY = moveState.y,
        .sourceZ = moveState.eyeZ(),
        .yawRadians = yawRadians,
    };
}

GameplayPartyAttackFrameInput IndoorWorldRuntime::buildPartyAttackFrameInput(
    const GameplayWorldPickRequest &pickRequest) const
{
    if (m_pPartyRuntime == nullptr)
    {
        return {};
    }

    const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
    const float attackSourceX = moveState.x;
    const float attackSourceY = moveState.y;
    const float attackSourceZ = moveState.eyeZ();
    const float yawRadians = m_pRenderer != nullptr ? m_pRenderer->cameraYawRadians() : 0.0f;

    GameplayPartyAttackFrameInput input = {};
    input.enabled = true;
    input.partyPosition =
        GameplayWorldPoint{
            .x = moveState.x,
            .y = moveState.y,
            .z = moveState.footZ,
        };
    input.rangedSource =
        GameplayWorldPoint{
            .x = attackSourceX,
            .y = attackSourceY,
            .z = attackSourceZ,
        };
    input.rangedRight =
        GameplayWorldPoint{
            .x = -std::sin(yawRadians),
            .y = std::cos(yawRadians),
            .z = 0.0f,
        };

    if (pickRequest.hasRay)
    {
        input.defaultRangedTarget =
            GameplayWorldPoint{
                .x = pickRequest.rayOrigin.x + pickRequest.rayDirection.x * 5120.0f,
                .y = pickRequest.rayOrigin.y + pickRequest.rayDirection.y * 5120.0f,
                .z = pickRequest.rayOrigin.z + pickRequest.rayDirection.z * 5120.0f,
            };
        input.rayRangedTarget = input.defaultRangedTarget;
        input.hasRayRangedTarget = true;
    }
    else
    {
        input.defaultRangedTarget =
            GameplayWorldPoint{
                .x = attackSourceX + 5120.0f,
                .y = attackSourceY,
                .z = attackSourceZ,
            };
    }

    std::copy(
        pickRequest.viewMatrix.begin(),
        pickRequest.viewMatrix.end(),
        input.fallbackQuery.viewMatrix.begin());
    std::copy(
        pickRequest.projectionMatrix.begin(),
        pickRequest.projectionMatrix.end(),
        input.fallbackQuery.projectionMatrix.begin());
    return input;
}

std::optional<size_t> IndoorWorldRuntime::spellActionHoveredActorIndex() const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayHoveredActorIndex() : std::nullopt;
}

std::optional<size_t> IndoorWorldRuntime::spellActionClosestVisibleHostileActorIndex() const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayClosestVisibleHostileActorIndex() : std::nullopt;
}

std::optional<bx::Vec3> IndoorWorldRuntime::spellActionActorTargetPoint(size_t actorIndex) const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayActorTargetPoint(actorIndex) : std::nullopt;
}

std::optional<bx::Vec3> IndoorWorldRuntime::spellActionGroundTargetPoint(float screenX, float screenY) const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayGroundTargetPoint(screenX, screenY) : std::nullopt;
}

GameplayPendingSpellWorldTargetFacts IndoorWorldRuntime::pickPendingSpellWorldTarget(
    const GameplayWorldPickRequest &request)
{
    GameplayPendingSpellWorldTargetFacts facts = {};

    if (m_pRenderer == nullptr)
    {
        return facts;
    }

    facts.worldHit = m_pRenderer->pickGameplayWorldHit(request);

    if (facts.worldHit.ground)
    {
        facts.fallbackGroundTargetPoint = facts.worldHit.ground->worldPoint;
    }
    else if (facts.worldHit.eventTarget)
    {
        facts.fallbackGroundTargetPoint = facts.worldHit.eventTarget->hitPoint;
    }
    else if (facts.worldHit.object)
    {
        facts.fallbackGroundTargetPoint = facts.worldHit.object->hitPoint;
    }
    else if (facts.worldHit.actor)
    {
        facts.fallbackGroundTargetPoint = facts.worldHit.actor->hitPoint;
    }

    return facts;
}

GameplayWorldHit IndoorWorldRuntime::pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->pickKeyboardGameplayWorldHit(request) : GameplayWorldHit{};
}

GameplayWorldHit IndoorWorldRuntime::pickHeldItemWorldTarget(const GameplayWorldPickRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->pickGameplayWorldHit(request) : GameplayWorldHit{};
}

GameplayWorldHit IndoorWorldRuntime::pickMouseInteractionTarget(const GameplayWorldPickRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->pickGameplayWorldHit(request) : GameplayWorldHit{};
}

bool IndoorWorldRuntime::worldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || worldItemIndex >= pMapDeltaData->spriteObjects.size())
    {
        return false;
    }

    const MapDeltaSpriteObject &spriteObject = pMapDeltaData->spriteObjects[worldItemIndex];
    InventoryItem item = {};

    if (!readIndoorHeldItemPayload(spriteObject.rawContainingItem, m_pItemTable, item))
    {
        return false;
    }

    uint32_t goldAmount = 0;
    readRawItemUInt32(spriteObject.rawContainingItem, 0x0c, goldAmount);

    state = {};
    state.item = item;
    state.goldAmount = goldAmount;
    state.isGold = goldAmount > 0;
    return true;
}

bool IndoorWorldRuntime::updateWorldItemInspectState(size_t worldItemIndex, const InventoryItem &item)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || worldItemIndex >= pMapDeltaData->spriteObjects.size())
    {
        return false;
    }

    MapDeltaSpriteObject &spriteObject = pMapDeltaData->spriteObjects[worldItemIndex];

    if (!hasContainingItemPayload(spriteObject.rawContainingItem))
    {
        return false;
    }

    uint32_t goldAmount = 0;
    readRawItemUInt32(spriteObject.rawContainingItem, 0x0c, goldAmount);

    if (goldAmount > 0)
    {
        return false;
    }

    writeIndoorHeldItemPayload(spriteObject.rawContainingItem, item);
    return true;
}

bool IndoorWorldRuntime::takeWorldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || worldItemIndex >= pMapDeltaData->spriteObjects.size())
    {
        return false;
    }

    if (!worldItemInspectState(worldItemIndex, state))
    {
        return false;
    }

    pMapDeltaData->spriteObjects.erase(pMapDeltaData->spriteObjects.begin() + std::ptrdiff_t(worldItemIndex));
    return true;
}

GameplayWorldHoverCacheState IndoorWorldRuntime::worldHoverCacheState() const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayWorldHoverCacheState() : GameplayWorldHoverCacheState{};
}

GameplayHoverStatusPayload IndoorWorldRuntime::refreshWorldHover(const GameplayWorldHoverRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->refreshGameplayWorldHover(request) : GameplayHoverStatusPayload{};
}

GameplayHoverStatusPayload IndoorWorldRuntime::readCachedWorldHover()
{
    return m_pRenderer != nullptr ? m_pRenderer->readCachedGameplayWorldHover() : GameplayHoverStatusPayload{};
}

void IndoorWorldRuntime::clearWorldHover()
{
    if (m_pRenderer != nullptr)
    {
        m_pRenderer->clearGameplayWorldHover();
    }
}

bool IndoorWorldRuntime::canUseHeldItemOnWorld(const GameplayWorldHit &hit) const
{
    if (hit.kind == GameplayWorldHitKind::WorldItem)
    {
        return false;
    }

    return canActivateWorldHit(hit, GameplayInteractionMethod::Mouse);
}

bool IndoorWorldRuntime::useHeldItemOnWorld(const GameplayWorldHit &hit)
{
    return activateWorldHit(hit);
}

void IndoorWorldRuntime::applyPendingSpellCastWorldEffects(const PartySpellCastResult &castResult)
{
    if (m_pRenderer != nullptr)
    {
        m_pRenderer->worldFxSystem().triggerPartySpellFx(castResult);
    }
}

bool IndoorWorldRuntime::dropHeldItemToWorld(const GameplayHeldItemDropRequest &request)
{
    if (m_pObjectTable == nullptr || m_pItemTable == nullptr || request.item.objectDescriptionId == 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    const std::optional<uint16_t> objectDescriptionId =
        resolveIndoorItemObjectDescriptionId(request.item, m_pItemTable, m_pObjectTable);

    if (!objectDescriptionId)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = m_pObjectTable->get(*objectDescriptionId);

    if (pObjectEntry == nullptr || (pObjectEntry->flags & ObjectDescNoSprite) != 0 || pObjectEntry->spriteId == 0)
    {
        return false;
    }

    MapDeltaSpriteObject spriteObject = {};
    const float directionX = std::cos(request.yawRadians);
    const float directionY = std::sin(request.yawRadians);
    const float horizontalSpeed = IndoorWorldItemThrowSpeed * std::cos(IndoorWorldItemThrowPitchRadians);
    const float verticalSpeed = IndoorWorldItemThrowSpeed * std::sin(IndoorWorldItemThrowPitchRadians);

    spriteObject.spriteId = pObjectEntry->spriteId;
    spriteObject.objectDescriptionId = *objectDescriptionId;
    spriteObject.x = int(std::lround(request.sourceX));
    spriteObject.y = int(std::lround(request.sourceY));
    spriteObject.z = int(std::lround(request.sourceZ));
    spriteObject.velocityX = clampToInt16(directionX * horizontalSpeed);
    spriteObject.velocityY = clampToInt16(directionY * horizontalSpeed);
    spriteObject.velocityZ = clampToInt16(verticalSpeed);
    spriteObject.yawAngle = yawAngleFromRadians(request.yawRadians);
    spriteObject.attributes = SpriteAttrDroppedByPlayer;
    spriteObject.sectorId = m_pPartyRuntime != nullptr ? m_pPartyRuntime->movementState().sectorId : -1;
    spriteObject.temporaryLifetime = pObjectEntry->lifetimeTicks;
    spriteObject.initialX = spriteObject.x;
    spriteObject.initialY = spriteObject.y;
    spriteObject.initialZ = spriteObject.z;
    writeIndoorHeldItemPayload(spriteObject.rawContainingItem, request.item);

    pMapDeltaData->spriteObjects.push_back(std::move(spriteObject));
    return true;
}

bool IndoorWorldRuntime::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    state = {};

    if (!m_map || m_map->fileName.empty() || m_pPartyRuntime == nullptr)
    {
        return false;
    }

    const Party *pParty = party();
    const PartyBuffState *pWizardEyeBuff = pParty != nullptr ? pParty->partyBuff(PartyBuffId::WizardEye) : nullptr;
    const SkillMastery wizardEyeMastery =
        pWizardEyeBuff != nullptr ? pWizardEyeBuff->skillMastery : SkillMastery::None;
    const IndoorMoveState &moveState = m_pPartyRuntime->movementState();

    state.textureName.clear();
    state.vectorBackground = true;
    state.backgroundColorAbgr = 0xff780000u;
    state.zoom = 1024.0f;
    state.partyU = indoorMinimapU(moveState.x);
    state.partyV = indoorMinimapV(moveState.y);
    state.wizardEyeActive = pWizardEyeBuff != nullptr;
    state.wizardEyeShowsExpertObjects = wizardEyeMastery >= SkillMastery::Expert;
    state.wizardEyeShowsDecorations = state.wizardEyeActive;
    return true;
}

void IndoorWorldRuntime::collectGameplayMinimapLines(std::vector<GameplayMinimapLineState> &lines)
{
    lines.clear();

    if (m_pIndoorMapData == nullptr || m_pPartyRuntime == nullptr)
    {
        return;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    const Party *pParty = party();
    const PartyBuffState *pWizardEyeBuff = pParty != nullptr ? pParty->partyBuff(PartyBuffId::WizardEye) : nullptr;
    const bool showEventOutlines =
        pWizardEyeBuff != nullptr && pWizardEyeBuff->skillMastery >= SkillMastery::Master;
    const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
    const EventRuntimeState *pEventRuntimeState = eventRuntimeState();
    const uint64_t signature = indoorMinimapLineSignature(
        *m_pIndoorMapData,
        *pMapDeltaData,
        pEventRuntimeState,
        moveState.footZ,
        showEventOutlines);

    if (m_cachedGameplayMinimapLinesValid && m_cachedGameplayMinimapLineSignature == signature)
    {
        lines = m_cachedGameplayMinimapLines;
        return;
    }

    std::vector<uint8_t> visibleFaceMask(m_pIndoorMapData->faces.size(), 0);

    for (size_t faceIndex = 0; faceIndex < m_pIndoorMapData->faces.size(); ++faceIndex)
    {
        visibleFaceMask[faceIndex] =
            indoorMinimapFaceVisible(
                m_pIndoorMapData->faces[faceIndex],
                pMapDeltaData,
                pEventRuntimeState,
                faceIndex)
            ? 1
            : 0;
    }

    for (size_t outlineIndex = 0; outlineIndex < m_pIndoorMapData->outlines.size(); ++outlineIndex)
    {
        const IndoorOutline &outline = m_pIndoorMapData->outlines[outlineIndex];

        if (outline.vertex1Id >= m_pIndoorMapData->vertices.size()
            || outline.vertex2Id >= m_pIndoorMapData->vertices.size()
            || outline.face1Id >= m_pIndoorMapData->faces.size()
            || outline.face2Id >= m_pIndoorMapData->faces.size())
        {
            continue;
        }

        const IndoorFace &face1 = m_pIndoorMapData->faces[outline.face1Id];
        const IndoorFace &face2 = m_pIndoorMapData->faces[outline.face2Id];
        const uint32_t face1Attributes = effectiveIndoorFaceAttributes(face1, pMapDeltaData, outline.face1Id);
        const uint32_t face2Attributes = effectiveIndoorFaceAttributes(face2, pMapDeltaData, outline.face2Id);

        if (visibleFaceMask[outline.face1Id] == 0 || visibleFaceMask[outline.face2Id] == 0)
        {
            continue;
        }

        const bool revealed =
            packedIndoorOutlineBit(pMapDeltaData->visibleOutlines, outlineIndex)
            || hasFaceAttribute(face1Attributes, FaceAttribute::SeenByParty)
            || hasFaceAttribute(face2Attributes, FaceAttribute::SeenByParty);

        if (!revealed)
        {
            continue;
        }

        const IndoorVertex &vertex1 = m_pIndoorMapData->vertices[outline.vertex1Id];
        const IndoorVertex &vertex2 = m_pIndoorMapData->vertices[outline.vertex2Id];
        const bool eventOutline =
            showEventOutlines
            && (hasFaceAttribute(face1Attributes, FaceAttribute::Clickable)
                || hasFaceAttribute(face2Attributes, FaceAttribute::Clickable))
            && (indoorFaceHasMapEvent(face1) || indoorFaceHasMapEvent(face2));

        GameplayMinimapLineState line = {};
        line.u0 = indoorMinimapRawU(vertex1.x);
        line.v0 = indoorMinimapRawV(vertex1.y);
        line.u1 = indoorMinimapRawU(vertex2.x);
        line.v1 = indoorMinimapRawV(vertex2.y);
        line.colorAbgr = eventOutline
            ? 0xffff0000u
            : indoorMinimapGreyLineColor(outline.z - moveState.footZ);
        lines.push_back(line);
    }

    m_cachedGameplayMinimapLineSignature = signature;
    m_cachedGameplayMinimapLines = lines;
    m_cachedGameplayMinimapLinesValid = true;
}

void IndoorWorldRuntime::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    markers.clear();

    GameplayMinimapState minimapState = {};

    if (!tryGetGameplayMinimapState(minimapState) || !minimapState.wizardEyeActive)
    {
        return;
    }

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    const IndoorMoveState *pMoveState =
        m_pPartyRuntime != nullptr ? &m_pPartyRuntime->movementState() : nullptr;

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!actorRuntimeState(actorIndex, actorState) || actorState.isInvisible)
        {
            continue;
        }

        const bool actorNearby = pMoveState != nullptr
            && length3d(
                actorState.preciseX - pMoveState->x,
                actorState.preciseY - pMoveState->y,
                actorState.preciseZ - pMoveState->footZ) <= ActiveActorUpdateRange;

        if (!actorState.isDead && !actorState.hasDetectedParty && !actorNearby)
        {
            continue;
        }

        GameplayMinimapMarkerState marker = {};
        marker.type = actorState.isDead
            ? GameplayMinimapMarkerType::CorpseActor
            : actorState.hostileToParty
            ? GameplayMinimapMarkerType::HostileActor
            : GameplayMinimapMarkerType::FriendlyActor;
        marker.u = indoorMinimapU(actorState.preciseX);
        marker.v = indoorMinimapV(actorState.preciseY);
        markers.push_back(marker);
    }

    if (minimapState.wizardEyeShowsExpertObjects && m_pObjectTable != nullptr)
    {
        for (const MapDeltaSpriteObject &spriteObject : pMapDeltaData->spriteObjects)
        {
            const ObjectEntry *pObjectEntry = m_pObjectTable->get(spriteObject.objectDescriptionId);

            if (pObjectEntry == nullptr
                || spriteObject.objectDescriptionId == 0
                || (spriteObject.attributes & SpriteAttrRemoved) != 0
                || (pObjectEntry->flags & ObjectDescNoSprite) != 0
                || pObjectEntry->spriteId == 0)
            {
                continue;
            }

            GameplayMinimapMarkerState marker = {};
            marker.type = (pObjectEntry->flags & ObjectDescUnpickable) != 0
                ? GameplayMinimapMarkerType::Projectile
                : GameplayMinimapMarkerType::WorldItem;
            marker.u = indoorMinimapU(static_cast<float>(spriteObject.x));
            marker.v = indoorMinimapV(static_cast<float>(spriteObject.y));
            markers.push_back(marker);
        }

        if (m_pGameplayProjectileService != nullptr)
        {
            const size_t projectileCount = m_pGameplayProjectileService->projectileCount();

            for (size_t projectileIndex = 0; projectileIndex < projectileCount; ++projectileIndex)
            {
                const GameplayProjectileService::ProjectileState *pProjectile =
                    m_pGameplayProjectileService->projectileState(projectileIndex);

                if (pProjectile == nullptr || pProjectile->isExpired)
                {
                    continue;
                }

                GameplayMinimapMarkerState marker = {};
                marker.type = GameplayMinimapMarkerType::Projectile;
                marker.u = indoorMinimapU(pProjectile->x);
                marker.v = indoorMinimapV(pProjectile->y);
                markers.push_back(marker);
            }
        }
    }

    if (minimapState.wizardEyeShowsDecorations && m_pIndoorMapData != nullptr)
    {
        for (size_t entityIndex = 0; entityIndex < m_pIndoorMapData->entities.size(); ++entityIndex)
        {
            if (entityIndex >= pMapDeltaData->decorationFlags.size()
                || (pMapDeltaData->decorationFlags[entityIndex] & LevelDecorationVisibleOnMap) == 0)
            {
                continue;
            }

            const IndoorEntity &entity = m_pIndoorMapData->entities[entityIndex];

            if (m_pEventRuntimeState != nullptr && m_pEventRuntimeState->has_value())
            {
                const uint32_t overrideKey =
                    entity.eventIdPrimary != 0 ? entity.eventIdPrimary : entity.eventIdSecondary;
                const auto overrideIterator = overrideKey != 0
                    ? (*m_pEventRuntimeState)->spriteOverrides.find(overrideKey)
                    : (*m_pEventRuntimeState)->spriteOverrides.end();

                if (overrideIterator != (*m_pEventRuntimeState)->spriteOverrides.end()
                    && overrideIterator->second.hidden)
                {
                    continue;
                }
            }

            if ((pMapDeltaData->decorationFlags[entityIndex] & LevelDecorationInvisible) != 0)
            {
                continue;
            }

            GameplayMinimapMarkerState marker = {};
            marker.type = GameplayMinimapMarkerType::Decoration;
            marker.u = indoorMinimapU(static_cast<float>(entity.x));
            marker.v = indoorMinimapV(static_cast<float>(entity.y));
            markers.push_back(marker);
        }
    }
}

IndoorWorldRuntime::ChestViewState *IndoorWorldRuntime::activeChestView()
{
    return m_activeChestView ? &*m_activeChestView : nullptr;
}

const IndoorWorldRuntime::ChestViewState *IndoorWorldRuntime::activeChestView() const
{
    return m_activeChestView ? &*m_activeChestView : nullptr;
}

void IndoorWorldRuntime::commitActiveChestView()
{
    if (!m_activeChestView)
    {
        return;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }
}


bool IndoorWorldRuntime::takeActiveChestItem(size_t itemIndex, ChestItemState &item)
{
    if (!m_activeChestView || !takeChestItem(*m_activeChestView, itemIndex, item))
    {
        return false;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

bool IndoorWorldRuntime::takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, ChestItemState &item)
{
    if (!m_activeChestView || !takeChestItemAt(*m_activeChestView, gridX, gridY, item))
    {
        return false;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

bool IndoorWorldRuntime::tryPlaceActiveChestItemAt(const ChestItemState &item, uint8_t gridX, uint8_t gridY)
{
    if (!m_activeChestView || !tryPlaceChestItemAt(*m_activeChestView, item, gridX, gridY))
    {
        return false;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

void IndoorWorldRuntime::closeActiveChestView()
{
    m_activeChestView.reset();
}

IndoorWorldRuntime::CorpseViewState *IndoorWorldRuntime::activeCorpseView()
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

const IndoorWorldRuntime::CorpseViewState *IndoorWorldRuntime::activeCorpseView() const
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

void IndoorWorldRuntime::commitActiveCorpseView()
{
    if (!m_activeCorpseView)
    {
        return;
    }

    if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
    }
}


bool IndoorWorldRuntime::openMapActorCorpseView(size_t actorIndex)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size() || m_pMonsterTable == nullptr)
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

    const MapActorAiState *pAiState =
        actorIndex < m_mapActorAiStates.size() ? &m_mapActorAiStates[actorIndex] : nullptr;

    if (actor.hp > 0
        || pAiState == nullptr
        || (pAiState->motionState != ActorAiMotionState::Dying
            && pAiState->motionState != ActorAiMotionState::Dead)
        || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
    {
        return false;
    }

    if (actorIndex >= m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews.resize(actorIndex + 1);
    }

    if (!m_mapActorCorpseViews[actorIndex].has_value())
    {
        const MonsterTable::MonsterStatsEntry *pStats = findIndoorActorStats(m_pMonsterTable, actor);

        if (pStats == nullptr)
        {
            return false;
        }

        const std::string &title = actor.name.empty() ? pStats->name : actor.name;
        CorpseViewState corpse =
            buildMonsterCorpseView(title, pStats->loot, m_pItemTable, m_pParty, actor.carriedItemId);

        if (corpse.items.empty())
        {
            return false;
        }

        corpse.fromSummonedMonster = false;
        corpse.sourceIndex = uint32_t(actorIndex);
        m_mapActorCorpseViews[actorIndex] = std::move(corpse);
    }

    m_activeCorpseView = *m_mapActorCorpseViews[actorIndex];
    return true;
}

bool IndoorWorldRuntime::autoLootMapActorCorpse(size_t actorIndex)
{
    if (!openMapActorCorpseView(actorIndex))
    {
        if (m_pGameplayView != nullptr)
        {
            m_pGameplayView->setStatusBarEvent("Nothing here");
        }

        if (m_pEventRuntimeState != nullptr && *m_pEventRuntimeState)
        {
            (*m_pEventRuntimeState)->lastActivationResult = "corpse " + std::to_string(actorIndex) + " empty";
        }

        return true;
    }

    if (m_pParty == nullptr)
    {
        closeActiveCorpseView();
        return false;
    }

    const GameplayCorpseAutoLootResult lootResult =
        autoLootActiveCorpseView(*this, *m_pParty, m_pItemTable);

    if (m_pGameplayView != nullptr && !lootResult.statusText.empty())
    {
        m_pGameplayView->setStatusBarEvent(lootResult.statusText);
    }

    if (m_pEventRuntimeState != nullptr && *m_pEventRuntimeState)
    {
        if (lootResult.lootedAny && !lootResult.firstItemName.empty())
        {
            (*m_pEventRuntimeState)->lastActivationResult =
                "corpse " + std::to_string(actorIndex) + " auto-looted item";
        }
        else if (lootResult.lootedAny)
        {
            (*m_pEventRuntimeState)->lastActivationResult =
                "corpse " + std::to_string(actorIndex) + " auto-looted gold";
        }
        else if (lootResult.blockedByInventory)
        {
            (*m_pEventRuntimeState)->lastActivationResult =
                "corpse " + std::to_string(actorIndex) + " blocked by inventory";
        }
        else
        {
            (*m_pEventRuntimeState)->lastActivationResult = "corpse " + std::to_string(actorIndex) + " empty";
        }
    }

    return lootResult.lootedAny || lootResult.blockedByInventory || lootResult.empty;
}

bool IndoorWorldRuntime::takeActiveCorpseItem(size_t itemIndex, ChestItemState &item)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (!m_activeCorpseView || pMapDeltaData == nullptr || itemIndex >= m_activeCorpseView->items.size())
    {
        return false;
    }

    item = m_activeCorpseView->items[itemIndex];
    m_activeCorpseView->items.erase(m_activeCorpseView->items.begin() + itemIndex);

    if (m_activeCorpseView->items.empty())
    {
        if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
        {
            m_mapActorCorpseViews[m_activeCorpseView->sourceIndex].reset();
        }

        if (m_activeCorpseView->sourceIndex < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[m_activeCorpseView->sourceIndex].attributes
                |= static_cast<uint32_t>(EvtActorAttribute::Invisible);
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

void IndoorWorldRuntime::closeActiveCorpseView()
{
    m_activeCorpseView.reset();
}

bool IndoorWorldRuntime::summonMonsters(
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
    if (m_pMonsterTable == nullptr || count == 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = resolveEncounterStats(typeIndexInMapStats, level);

    if (pStats == nullptr)
    {
        return false;
    }

    const MonsterEntry *pMonsterEntry = m_pMonsterTable->findById(static_cast<int16_t>(pStats->id));

    if (pMonsterEntry == nullptr)
    {
        return false;
    }

    const bool hostileToParty = m_pMonsterTable->isHostileToParty(static_cast<int16_t>(pStats->id));
    bool spawnedAny = false;

    for (uint32_t summonIndex = 0; summonIndex < count; ++summonIndex)
    {
        const float angleRadians = (Pi * 2.0f * static_cast<float>(summonIndex)) / static_cast<float>(count);
        const float radius = 96.0f + 24.0f * static_cast<float>(summonIndex % 3u);
        MapDeltaActor actor = {};
        actor.name = pStats->name;
        actor.attributes = defaultActorAttributes(hostileToParty);
        actor.hp = static_cast<int16_t>(std::clamp(pStats->hitPoints, 0, 32767));
        actor.hostilityType = static_cast<uint8_t>(std::clamp(pStats->hostility, 0, 255));
        actor.monsterInfoId = static_cast<int16_t>(pStats->id);
        actor.monsterId = static_cast<int16_t>(pStats->id);
        actor.radius = pMonsterEntry->radius;
        actor.height = pMonsterEntry->height;
        actor.moveSpeed = pMonsterEntry->movementSpeed;
        actor.x = x + static_cast<int>(std::lround(std::cos(angleRadians) * radius));
        actor.y = y + static_cast<int>(std::lround(std::sin(angleRadians) * radius));
        actor.z = z;
        actor.group = group;
        actor.ally = hostileToParty ? 0u : 999u;
        actor.uniqueNameIndex = static_cast<int32_t>(uniqueNameId);
        pMapDeltaData->actors.push_back(std::move(actor));
        spawnedAny = true;
    }

    syncMapActorAiStates();
    return spawnedAny;
}

bool IndoorWorldRuntime::summonEventItem(
    uint32_t itemId,
    int32_t x,
    int32_t y,
    int32_t z,
    int32_t speed,
    uint32_t count,
    bool randomRotate
)
{
    if (m_pObjectTable == nullptr || count == 0 || itemId == 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable != nullptr ? m_pItemTable->get(itemId) : nullptr;
    std::optional<uint16_t> objectDescriptionId =
        m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(itemId));

    if (!objectDescriptionId && pItemDefinition != nullptr)
    {
        objectDescriptionId =
            m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(pItemDefinition->spriteIndex));
    }

    if (!objectDescriptionId)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = m_pObjectTable->get(*objectDescriptionId);

    if (pObjectEntry == nullptr)
    {
        return false;
    }

    std::mt19937 rng(itemId * 2654435761u + count * 977u);
    bool spawnedAny = false;

    for (uint32_t itemIndex = 0; itemIndex < count; ++itemIndex)
    {
        MapDeltaSpriteObject spriteObject = {};
        spriteObject.spriteId = pObjectEntry->spriteId;
        spriteObject.objectDescriptionId = *objectDescriptionId;
        spriteObject.x = x;
        spriteObject.y = y;
        spriteObject.z = z;
        spriteObject.attributes = SpriteAttrTemporary;
        spriteObject.temporaryLifetime = pObjectEntry->lifetimeTicks;
        spriteObject.initialX = x;
        spriteObject.initialY = y;
        spriteObject.initialZ = z;
        spriteObject.rawContainingItem.assign(RawContainingItemSize, 0);

        if (pItemDefinition != nullptr)
        {
            const int32_t rawItemId = static_cast<int32_t>(pItemDefinition->itemId);
            std::memcpy(spriteObject.rawContainingItem.data(), &rawItemId, sizeof(rawItemId));
        }

        if (speed > 0)
        {
            const float angleRadians = randomRotate
                ? std::uniform_real_distribution<float>(0.0f, Pi * 2.0f)(rng)
                : 0.0f;
            spriteObject.velocityX = static_cast<int16_t>(std::lround(std::cos(angleRadians) * speed));
            spriteObject.velocityY = static_cast<int16_t>(std::lround(std::sin(angleRadians) * speed));
        }

        pMapDeltaData->spriteObjects.push_back(std::move(spriteObject));
        spawnedAny = true;
    }

    return spawnedAny;
}

bool IndoorWorldRuntime::checkMonstersKilled(
    uint32_t checkType,
    uint32_t id,
    uint32_t count,
    bool invisibleAsDead
) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    int totalActors = 0;
    int defeatedActors = 0;
    const bool currentAlertStatus = pMapDeltaData->locationInfo.alertStatus != 0;
    constexpr uint32_t ActorAlertStatusBit = static_cast<uint32_t>(EvtActorAttribute::AlertStatus);

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

        if (((actor.attributes & ActorAlertStatusBit) != 0) != currentAlertStatus)
        {
            continue;
        }

        bool matches = false;

        switch (static_cast<EvtActorKillCheck>(checkType))
        {
            case EvtActorKillCheck::Any:
                matches = true;
                break;

            case EvtActorKillCheck::Group:
                matches = actor.group == id;
                break;

            case EvtActorKillCheck::MonsterId:
                matches = resolveIndoorActorStatsId(actor) == legacyEventMonsterIdToStatsId(id);
                break;

            case EvtActorKillCheck::ActorIdOe:
            case EvtActorKillCheck::ActorIdMm8:
                matches = actorIndex == id;
                break;
        }

        if (!matches)
        {
            continue;
        }

        ++totalActors;
        const bool isInvisible =
            (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0;

        if (actor.hp <= 0 || isInvisible)
        {
            ++defeatedActors;
        }
    }

    (void)invisibleAsDead;

    if (count > 0)
    {
        return defeatedActors >= static_cast<int>(count);
    }

    return totalActors == defeatedActors;
}

void IndoorWorldRuntime::applyEventRuntimeState(bool syncPersistentHostilityMasks)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();
    EventRuntimeState *pEventRuntimeState = eventRuntimeState();

    invalidateRuntimeGeometryCache();

    if (pMapDeltaData == nullptr || pEventRuntimeState == nullptr)
    {
        return;
    }

    pMapDeltaData->eventVariables.mapVars = pEventRuntimeState->mapVars;
    const uint32_t hostileMask = static_cast<uint32_t>(EvtActorAttribute::Hostile);
    std::vector<bool> persistentHostilityMaskTouched(pMapDeltaData->actors.size(), false);

    for (const auto &[actorId, setMask] : pEventRuntimeState->actorSetMasks)
    {
        if (actorId < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[actorId].attributes |= setMask;
            if ((setMask & hostileMask) != 0)
            {
                persistentHostilityMaskTouched[actorId] = true;
            }
        }
    }

    for (const auto &[actorId, clearMask] : pEventRuntimeState->actorClearMasks)
    {
        if (actorId < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[actorId].attributes &= ~clearMask;
            if ((clearMask & hostileMask) != 0)
            {
                persistentHostilityMaskTouched[actorId] = true;
            }
        }
    }

    for (const auto &[actorId, groupId] : pEventRuntimeState->actorIdGroupOverrides)
    {
        if (actorId < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[actorId].group = groupId;
        }
    }

    for (const auto &[fromGroupId, toGroupId] : pEventRuntimeState->actorGroupOverrides)
    {
        for (MapDeltaActor &actor : pMapDeltaData->actors)
        {
            if (actor.group == fromGroupId)
            {
                actor.group = toGroupId;
            }
        }
    }

    for (const auto &[groupId, allyId] : pEventRuntimeState->actorGroupAllyOverrides)
    {
        for (MapDeltaActor &actor : pMapDeltaData->actors)
        {
            if (actor.group == groupId)
            {
                actor.ally = allyId;
            }
        }
    }

    for (const auto &[groupId, setMask] : pEventRuntimeState->actorGroupSetMasks)
    {
        for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
        {
            MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

            if (actor.group == groupId)
            {
                actor.attributes |= setMask;
                if ((setMask & hostileMask) != 0)
                {
                    persistentHostilityMaskTouched[actorIndex] = true;
                }
            }
        }
    }

    for (const auto &[groupId, clearMask] : pEventRuntimeState->actorGroupClearMasks)
    {
        for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
        {
            MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

            if (actor.group == groupId)
            {
                actor.attributes &= ~clearMask;
                if ((clearMask & hostileMask) != 0)
                {
                    persistentHostilityMaskTouched[actorIndex] = true;
                }
            }
        }
    }

    if (syncPersistentHostilityMasks)
    {
        for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
        {
            if (persistentHostilityMaskTouched[actorIndex])
            {
                const bool hostileToParty =
                    (pMapDeltaData->actors[actorIndex].attributes & hostileMask) != 0;
                setMapActorHostilityFromEvent(actorIndex, hostileToParty);
            }
        }
    }

    for (const auto &[actorId, hostileToParty] : pEventRuntimeState->actorHostilityRequests)
    {
        if (actorId < pMapDeltaData->actors.size())
        {
            setMapActorHostilityFromEvent(actorId, hostileToParty);
        }
    }

    for (const auto &[groupId, hostileToParty] : pEventRuntimeState->actorGroupHostilityRequests)
    {
        for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
        {
            const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

            if (actor.group == groupId)
            {
                setMapActorHostilityFromEvent(actorIndex, hostileToParty);
            }
        }
    }

    for (const auto &[chestId, setMask] : pEventRuntimeState->chestSetMasks)
    {
        if (chestId < pMapDeltaData->chests.size())
        {
            pMapDeltaData->chests[chestId].flags |= static_cast<uint16_t>(setMask);

            if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
            {
                m_materializedChestViews[chestId]->flags = pMapDeltaData->chests[chestId].flags;
            }

            if (m_activeChestView && m_activeChestView->chestId == chestId)
            {
                m_activeChestView->flags = pMapDeltaData->chests[chestId].flags;
            }
        }
    }

    for (const auto &[chestId, clearMask] : pEventRuntimeState->chestClearMasks)
    {
        if (chestId < pMapDeltaData->chests.size())
        {
            pMapDeltaData->chests[chestId].flags &= ~static_cast<uint16_t>(clearMask);

            if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
            {
                m_materializedChestViews[chestId]->flags = pMapDeltaData->chests[chestId].flags;
            }

            if (m_activeChestView && m_activeChestView->chestId == chestId)
            {
                m_activeChestView->flags = pMapDeltaData->chests[chestId].flags;
            }
        }
    }

    for (uint32_t openedChestId : pEventRuntimeState->openedChestIds)
    {
        if (openedChestId < pMapDeltaData->chests.size())
        {
            pMapDeltaData->chests[openedChestId].flags |= static_cast<uint16_t>(EvtChestFlag::Opened);
            activateChestView(openedChestId);
        }
    }
}

const MapDeltaData *IndoorWorldRuntime::mapDeltaData() const
{
    if (m_pMapDeltaData == nullptr || !*m_pMapDeltaData)
    {
        return nullptr;
    }

    return &**m_pMapDeltaData;
}

MapDeltaData *IndoorWorldRuntime::mapDeltaData()
{
    if (m_pMapDeltaData == nullptr || !*m_pMapDeltaData)
    {
        return nullptr;
    }

    return &**m_pMapDeltaData;
}

std::vector<IndoorActorCollision> IndoorWorldRuntime::actorMovementCollidersForActorMovement(
    const std::vector<size_t> &activeActorIndices) const
{
    std::vector<IndoorActorCollision> colliders;
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || m_pMonsterTable == nullptr)
    {
        return colliders;
    }

    const GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService =
        m_pGameplayActorService != nullptr ? m_pGameplayActorService : &fallbackActorService;
    colliders.reserve(activeActorIndices.size());

    for (size_t actorIndex : activeActorIndices)
    {
        if (actorIndex >= pMapDeltaData->actors.size() || actorIndex >= m_mapActorAiStates.size())
        {
            continue;
        }

        const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
        const MapActorAiState &aiState = m_mapActorAiStates[actorIndex];

        if (indoorActorUnavailableForCombat(actor, aiState, *pActorService))
        {
            continue;
        }

        const float radius = IndoorActorVsActorMovementRadius;
        const float actorCollisionRadius = indoorActorCollisionRadius(actor);
        const float height = indoorActorCollisionHeight(actor, actorCollisionRadius);

        if (radius <= 0.0f || height <= 0.0f)
        {
            continue;
        }

        colliders.push_back(IndoorActorCollision{
            actorIndex,
            aiState.sectorId,
            aiState.preciseX,
            aiState.preciseY,
            aiState.preciseZ,
            radius,
            height});
    }

    return colliders;
}

std::vector<IndoorActorCollision> IndoorWorldRuntime::actorMovementCollidersForPartyMovement() const
{
    std::vector<IndoorActorCollision> colliders;
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || m_pMonsterTable == nullptr)
    {
        return colliders;
    }

    const GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService =
        m_pGameplayActorService != nullptr ? m_pGameplayActorService : &fallbackActorService;
    colliders.reserve(pMapDeltaData->actors.size());

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        if (actorIndex >= m_mapActorAiStates.size())
        {
            continue;
        }

        const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
        const MapActorAiState &aiState = m_mapActorAiStates[actorIndex];

        if (indoorActorUnavailableForCombat(actor, aiState, *pActorService))
        {
            continue;
        }

        GameplayRuntimeActorState runtimeState = {};

        if (!actorRuntimeState(actorIndex, runtimeState) || !runtimeState.hostileToParty)
        {
            continue;
        }

        const float radius = indoorActorCollisionRadius(actor);
        const float height = indoorActorCollisionHeight(actor, radius);

        if (radius <= 0.0f || height <= 0.0f)
        {
            continue;
        }

        colliders.push_back(IndoorActorCollision{
            actorIndex,
            aiState.sectorId,
            aiState.preciseX,
            aiState.preciseY,
            aiState.preciseZ,
            radius,
            height});
    }

    return colliders;
}

std::vector<IndoorCylinderCollision> IndoorWorldRuntime::decorationMovementColliders() const
{
    std::vector<IndoorCylinderCollision> colliders;

    if (m_pIndoorDecorationBillboardSet == nullptr || m_pIndoorMapData == nullptr)
    {
        return colliders;
    }

    colliders.reserve(m_pIndoorDecorationBillboardSet->billboards.size());

    for (const DecorationBillboard &billboard : m_pIndoorDecorationBillboardSet->billboards)
    {
        if (billboard.radius <= 0 || billboard.height == 0)
        {
            continue;
        }

        if (hasDecorationFlag(billboard.flags, DecorationDescFlag::MoveThrough)
            || hasDecorationFlag(billboard.flags, DecorationDescFlag::DontDraw))
        {
            continue;
        }

        if (billboard.entityIndex < m_pIndoorMapData->entities.size())
        {
            const IndoorEntity &entity = m_pIndoorMapData->entities[billboard.entityIndex];

            if ((entity.aiAttributes & LevelDecorationInvisible) != 0)
            {
                continue;
            }
        }

        colliders.push_back(IndoorCylinderCollision{
            billboard.entityIndex,
            billboard.sectorId,
            static_cast<float>(billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z),
            static_cast<float>(billboard.radius),
            static_cast<float>(billboard.height)});
    }

    return colliders;
}

std::vector<IndoorCylinderCollision> IndoorWorldRuntime::spriteObjectMovementColliders() const
{
    std::vector<IndoorCylinderCollision> colliders;
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || m_pObjectTable == nullptr)
    {
        return colliders;
    }

    colliders.reserve(pMapDeltaData->spriteObjects.size());

    for (size_t objectIndex = 0; objectIndex < pMapDeltaData->spriteObjects.size(); ++objectIndex)
    {
        const MapDeltaSpriteObject &spriteObject = pMapDeltaData->spriteObjects[objectIndex];
        const ObjectEntry *pObjectEntry = m_pObjectTable->get(spriteObject.objectDescriptionId);

        if (pObjectEntry == nullptr || spriteObject.objectDescriptionId == 0)
        {
            continue;
        }

        if (pObjectEntry->radius <= 0 || pObjectEntry->height <= 0)
        {
            continue;
        }

        if ((pObjectEntry->flags
                & (ObjectDescNoCollision | ObjectDescTemporary | ObjectDescTrailParticle
                    | ObjectDescTrailFire | ObjectDescTrailLine)) != 0)
        {
            continue;
        }

        if ((spriteObject.attributes & (SpriteAttrTemporary | SpriteAttrMissile | SpriteAttrRemoved)) != 0
            || spriteObject.spellId != 0)
        {
            continue;
        }

        if (hasContainingItemPayload(spriteObject.rawContainingItem)
            && (pObjectEntry->flags & ObjectDescUnpickable) == 0)
        {
            continue;
        }

        colliders.push_back(IndoorCylinderCollision{
            objectIndex,
            spriteObject.sectorId,
            static_cast<float>(spriteObject.x),
            static_cast<float>(spriteObject.y),
            static_cast<float>(spriteObject.z),
            static_cast<float>(pObjectEntry->radius),
            static_cast<float>(pObjectEntry->height)});
    }

    return colliders;
}

EventRuntimeState *IndoorWorldRuntime::eventRuntimeState()
{
    if (m_pEventRuntimeState == nullptr || !*m_pEventRuntimeState)
    {
        return nullptr;
    }

    return &**m_pEventRuntimeState;
}

const EventRuntimeState *IndoorWorldRuntime::eventRuntimeState() const
{
    if (m_pEventRuntimeState == nullptr || !*m_pEventRuntimeState)
    {
        return nullptr;
    }

    return &**m_pEventRuntimeState;
}

IndoorWorldRuntime::Snapshot IndoorWorldRuntime::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.gameMinutes = m_gameMinutes;
    snapshot.currentLocationReputation = m_currentLocationReputation;
    snapshot.sessionChestSeed = m_sessionChestSeed;
    snapshot.materializedChestViews = m_materializedChestViews;
    snapshot.activeChestView = m_activeChestView;
    snapshot.mapActorCorpseViews = m_mapActorCorpseViews;
    snapshot.activeCorpseView = m_activeCorpseView;
    snapshot.mapActorAiStates = m_mapActorAiStates;
    snapshot.bloodSplats = m_bloodSplats;
    snapshot.actorUpdateAccumulatorSeconds = m_actorUpdateAccumulatorSeconds;
    return snapshot;
}

void IndoorWorldRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    m_gameMinutes = snapshot.gameMinutes;
    m_currentLocationReputation = snapshot.currentLocationReputation;
    m_sessionChestSeed = snapshot.sessionChestSeed;
    m_materializedChestViews = snapshot.materializedChestViews;
    m_activeChestView = snapshot.activeChestView;
    m_mapActorCorpseViews = snapshot.mapActorCorpseViews;
    m_activeCorpseView = snapshot.activeCorpseView;
    m_mapActorAiStates = snapshot.mapActorAiStates;
    m_bloodSplats = snapshot.bloodSplats;
    ++m_bloodSplatRevision;
    m_actorUpdateAccumulatorSeconds = snapshot.actorUpdateAccumulatorSeconds;
    m_indoorJournalRevealStateValid = false;
    m_cachedGameplayMinimapLinesValid = false;
    invalidateRuntimeGeometryCache();
    syncMapActorAiStates();

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData != nullptr)
    {
        const size_t actorCount = std::min(pMapDeltaData->actors.size(), m_mapActorAiStates.size());

        for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
        {
            refreshIndoorMapActorAiStaticFields(
                m_mapActorAiStates[actorIndex],
                pMapDeltaData->actors[actorIndex],
                actorIndex,
                m_pMonsterTable,
                m_pGameplayActorService,
                m_pActorSpriteFrameTable);
        }
    }

    if (!snapshot.mapActorSpellEffectStates.empty())
    {
        const size_t actorCount = std::min(snapshot.mapActorSpellEffectStates.size(), m_mapActorAiStates.size());

        for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
        {
            m_mapActorAiStates[actorIndex].spellEffects = snapshot.mapActorSpellEffectStates[actorIndex];
        }
    }

    applyEventRuntimeState(true);
}

IndoorWorldRuntime::ChestViewState IndoorWorldRuntime::buildChestView(uint32_t chestId) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || chestId >= pMapDeltaData->chests.size())
    {
        return {};
    }

    return buildMaterializedChestView(
        chestId,
        pMapDeltaData->chests[chestId],
        m_map ? m_map->treasureLevel : 0,
        m_map ? m_map->id : 0,
        m_sessionChestSeed,
        m_pChestTable,
        m_pItemTable,
        m_pParty);
}

void IndoorWorldRuntime::activateChestView(uint32_t chestId)
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || chestId >= pMapDeltaData->chests.size())
    {
        return;
    }

    if (chestId >= m_materializedChestViews.size())
    {
        m_materializedChestViews.resize(chestId + 1);
    }

    const bool cached = m_materializedChestViews[chestId].has_value();

    if (!cached)
    {
        m_materializedChestViews[chestId] = buildChestView(chestId);
    }

    m_activeChestView = *m_materializedChestViews[chestId];
    std::cout << "Chest activate world=indoor chest=" << chestId
              << " cached=" << (cached ? "yes" : "no")
              << " visible=" << m_activeChestView->items.size()
              << " hidden=" << m_activeChestView->hiddenItems.size()
              << '\n';
}

std::optional<GameplayWorldPoint> IndoorWorldRuntime::actorImpactPoint(size_t actorIndex) const
{
    GameplayRuntimeActorState actorState = {};

    if (!actorRuntimeState(actorIndex, actorState))
    {
        return std::nullopt;
    }

    return GameplayWorldPoint{
        .x = actorState.preciseX,
        .y = actorState.preciseY,
        .z = actorState.preciseZ + std::max(24.0f, static_cast<float>(actorState.height) * 0.6f),
    };
}

bool IndoorWorldRuntime::spawnIndoorProjectileImpactVisual(
    const GameplayProjectileService::ProjectileState &projectile,
    const GameplayWorldPoint &point,
    bool centerVertically)
{
    if (m_pGameplayProjectileService == nullptr)
    {
        return false;
    }

    if (projectile.impactSoundIdOverride != 0)
    {
        const std::optional<GameplayProjectileService::ProjectileAudioRequest> audioRequest =
            m_pGameplayProjectileService->buildProjectileImpactAudioRequest(projectile, point.x, point.y, point.z);

        if (audioRequest)
        {
            pushIndoorProjectileAudioEvent(*audioRequest);
        }
    }

    if (m_pObjectTable == nullptr || projectile.impactObjectDescriptionId == 0)
    {
        return false;
    }

    const std::optional<GameplayProjectileService::ProjectileImpactVisualDefinition> impactDefinition =
        m_pGameplayProjectileService->buildProjectileImpactVisualDefinition(
            projectile.impactObjectDescriptionId,
            m_pObjectTable,
            m_pProjectileSpriteFrameTable);

    if (!impactDefinition)
    {
        return false;
    }

    GameplayProjectileService::ProjectileState impactProjectile = projectile;

    if (m_pIndoorMapData != nullptr)
    {
        RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();
        impactProjectile.sectorId =
            resolveIndoorPointSector(
                m_pIndoorMapData,
                runtimeGeometry.vertices,
                &runtimeGeometry.geometryCache,
                {point.x, point.y, point.z},
                projectile.sectorId);
    }

    const GameplayProjectileService::ProjectileImpactSpawnResult result =
        m_pGameplayProjectileService->spawnProjectileImpactVisual(
            impactProjectile,
            *impactDefinition,
            point.x,
            point.y,
            point.z,
            centerVertically);
    return result.spawned;
}

bool IndoorWorldRuntime::spawnIndoorWaterSplashImpactVisual(const GameplayWorldPoint &point)
{
    if (m_pGameplayProjectileService == nullptr || m_pObjectTable == nullptr)
    {
        return false;
    }

    const std::optional<GameplayProjectileService::ProjectileImpactVisualDefinition> splashDefinition =
        m_pGameplayProjectileService->buildWaterSplashImpactVisualDefinition(
            m_pObjectTable,
            m_pProjectileSpriteFrameTable);

    if (!splashDefinition)
    {
        return false;
    }

    const GameplayProjectileService::ProjectileImpactSpawnResult result =
        m_pGameplayProjectileService->spawnWaterSplashImpactVisual(
            *splashDefinition,
            point.x,
            point.y,
            point.z);
    return result.spawned;
}

bool IndoorWorldRuntime::spawnImmediateSpellImpactVisualAt(
    const GameplayWorldPoint &point,
    uint32_t spellId,
    bool centerVertically,
    bool preferImpactObject)
{
    if (spellId == 0
        || m_pGameplayProjectileService == nullptr
        || m_pObjectTable == nullptr
        || m_pSpellTable == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    IndoorResolvedProjectileDefinition sourceDefinition = {};

    if (!fillIndoorProjectileDefinitionFromSpell(*pSpellEntry, *m_pObjectTable, sourceDefinition))
    {
        return false;
    }

    uint16_t impactObjectDescriptionId =
        preferImpactObject && sourceDefinition.impactObjectDescriptionId != 0
            ? sourceDefinition.impactObjectDescriptionId
            : sourceDefinition.objectDescriptionId;

    if (impactObjectDescriptionId == 0)
    {
        impactObjectDescriptionId = sourceDefinition.impactObjectDescriptionId;
    }

    const std::optional<GameplayProjectileService::ProjectileImpactVisualDefinition> impactDefinition =
        m_pGameplayProjectileService->buildProjectileImpactVisualDefinition(
            impactObjectDescriptionId,
            m_pObjectTable,
            m_pProjectileSpriteFrameTable);

    if (!impactDefinition)
    {
        return false;
    }

    const bool freezeAnimation = impactObjectDescriptionId == sourceDefinition.objectDescriptionId;
    const GameplayProjectileService::ProjectileImpactSpawnResult result =
        m_pGameplayProjectileService->spawnImmediateSpellImpactVisual(
            *impactDefinition,
            static_cast<int>(spellId),
            sourceDefinition.objectName,
            sourceDefinition.objectSpriteName,
            point.x,
            point.y,
            point.z,
            centerVertically,
            freezeAnimation);
    return result.spawned;
}

void IndoorWorldRuntime::spawnImmediateSpellImpactVisual(size_t actorIndex, uint32_t spellId)
{
    const std::optional<GameplayWorldPoint> impactPoint = actorImpactPoint(actorIndex);

    if (!impactPoint)
    {
        return;
    }

    spawnImmediateSpellImpactVisualAt(*impactPoint, spellId);
}

const MapEncounterInfo *IndoorWorldRuntime::encounterInfo(uint32_t typeIndexInMapStats) const
{
    if (!m_map || typeIndexInMapStats < 1 || typeIndexInMapStats > 3)
    {
        return nullptr;
    }

    static constexpr std::array<const MapEncounterInfo MapStatsEntry::*, 3> EncounterMembers = {{
        &MapStatsEntry::encounter1,
        &MapStatsEntry::encounter2,
        &MapStatsEntry::encounter3
    }};

    const MapStatsEntry &map = *m_map;
    return &(map.*EncounterMembers[typeIndexInMapStats - 1]);
}

const MonsterTable::MonsterStatsEntry *IndoorWorldRuntime::resolveEncounterStats(
    uint32_t typeIndexInMapStats,
    uint32_t level
) const
{
    if (m_pMonsterTable == nullptr)
    {
        return nullptr;
    }

    const MapEncounterInfo *pEncounter = encounterInfo(typeIndexInMapStats);

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
    pictureName.push_back(tierLetterForSummonLevel(level));
    return m_pMonsterTable->findStatsByPictureName(pictureName);
}

bool IndoorWorldRuntime::materializeTreasureSpawn(size_t spawnIndex, const IndoorSpawn &spawn)
{
    if (!m_map
        || m_pObjectTable == nullptr
        || m_pItemTable == nullptr
        || m_pParty == nullptr
        || m_pIndoorMapData == nullptr
        || spawn.typeId != 2)
    {
        return false;
    }

    const StandardItemEnchantTable *pStandardItemEnchantTable = m_pParty->standardItemEnchantTable();
    const SpecialItemEnchantTable *pSpecialItemEnchantTable = m_pParty->specialItemEnchantTable();

    if (pStandardItemEnchantTable == nullptr || pSpecialItemEnchantTable == nullptr)
    {
        return false;
    }

    const auto canMaterializeAsWorldItem =
        [this](const ItemDefinition &entry)
        {
            InventoryItem candidate = {};
            candidate.objectDescriptionId = entry.itemId;
            return resolveIndoorItemObjectDescriptionId(candidate, m_pItemTable, m_pObjectTable).has_value();
        };

    const std::optional<GameplayTreasureSpawnResult> treasure =
        generateTreasureSpawnItem(
            spawn.index,
            m_map->treasureLevel,
            m_sessionChestSeed,
            m_map->id,
            static_cast<uint32_t>(spawnIndex),
            *m_pItemTable,
            *pStandardItemEnchantTable,
            *pSpecialItemEnchantTable,
            m_pParty,
            canMaterializeAsWorldItem);

    if (!treasure || treasure->item.objectDescriptionId == 0)
    {
        return false;
    }

    const std::optional<uint16_t> objectDescriptionId =
        resolveIndoorItemObjectDescriptionId(treasure->item, m_pItemTable, m_pObjectTable);

    if (!objectDescriptionId)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = m_pObjectTable->get(*objectDescriptionId);

    if (pObjectEntry == nullptr || (pObjectEntry->flags & ObjectDescNoSprite) != 0 || pObjectEntry->spriteId == 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    int z = spawn.z;
    int16_t sectorId = -1;

    if (!m_pIndoorMapData->faces.empty() && !m_pIndoorMapData->vertices.empty())
    {
        RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();
        const IndoorFloorSample floorSample =
            sampleIndoorFloor(
                *m_pIndoorMapData,
                runtimeGeometry.vertices,
                static_cast<float>(spawn.x),
                static_cast<float>(spawn.y),
                static_cast<float>(spawn.z),
                IndoorFloorSampleRise,
                IndoorFloorSampleDrop,
                std::nullopt,
                nullptr,
                &runtimeGeometry.geometryCache);

        if (floorSample.hasFloor)
        {
            z = static_cast<int>(std::lround(floorSample.height));
            sectorId = floorSample.sectorId;
        }
        else
        {
            const std::optional<int16_t> pointSector =
                findIndoorSectorForPoint(
                    *m_pIndoorMapData,
                    runtimeGeometry.vertices,
                    {static_cast<float>(spawn.x), static_cast<float>(spawn.y), static_cast<float>(spawn.z)},
                    &runtimeGeometry.geometryCache);

            if (pointSector)
            {
                sectorId = *pointSector;
            }
        }
    }

    MapDeltaSpriteObject spriteObject = {};
    spriteObject.spriteId = pObjectEntry->spriteId;
    spriteObject.objectDescriptionId = *objectDescriptionId;
    spriteObject.x = spawn.x;
    spriteObject.y = spawn.y;
    spriteObject.z = z;
    spriteObject.sectorId = sectorId;
    spriteObject.initialX = spriteObject.x;
    spriteObject.initialY = spriteObject.y;
    spriteObject.initialZ = spriteObject.z;
    writeIndoorHeldItemPayload(spriteObject.rawContainingItem, treasure->item);

    if (treasure->isGold)
    {
        writeRawItemUInt32(spriteObject.rawContainingItem, 0x0c, treasure->goldAmount);
    }

    pMapDeltaData->spriteObjects.push_back(std::move(spriteObject));
    return true;
}

void IndoorWorldRuntime::materializeInitialMonsterSpawns()
{
    if (!m_map
        || m_pMonsterTable == nullptr
        || m_pIndoorMapData == nullptr
        || !shouldMaterializeIndoorSpawnsOnInitialize(m_pMapDeltaData))
    {
        return;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    RuntimeGeometryCache &runtimeGeometry = runtimeGeometryCache();

    for (size_t spawnIndex = 0; spawnIndex < m_pIndoorMapData->spawns.size(); ++spawnIndex)
    {
        const IndoorSpawn &spawn = m_pIndoorMapData->spawns[spawnIndex];

        if (spawn.typeId == 2)
        {
            materializeTreasureSpawn(spawnIndex, spawn);
            continue;
        }

        if (spawn.typeId != 3)
        {
            continue;
        }

        const IndoorEncounterSpawnDescriptor descriptor =
            resolveIndoorEncounterSpawnDescriptor(spawn.index);

        if (descriptor.encounterSlot <= 0)
        {
            continue;
        }

        const uint32_t count = resolveIndoorEncounterSpawnCount(
            *m_map,
            descriptor.encounterSlot,
            m_sessionChestSeed,
            static_cast<uint32_t>(spawnIndex));

        for (uint32_t spawnOrdinal = 0; spawnOrdinal < count; ++spawnOrdinal)
        {
            const uint32_t tierSeed = m_sessionChestSeed
                ^ static_cast<uint32_t>(descriptor.encounterSlot * 2654435761u)
                ^ static_cast<uint32_t>((spawnOrdinal + 1u) * 2246822519u)
                ^ static_cast<uint32_t>(spawn.group * 3266489917u)
                ^ static_cast<uint32_t>(spawnIndex + 1u)
                ^ static_cast<uint32_t>(spawn.x)
                ^ static_cast<uint32_t>(spawn.y)
                ^ static_cast<uint32_t>(spawn.z);
            const char tierLetter = resolveIndoorEncounterTierLetter(
                *m_map,
                descriptor.encounterSlot,
                descriptor.fixedTier,
                tierSeed);
            const MapEncounterInfo *pEncounter = getIndoorEncounterInfo(*m_map, descriptor.encounterSlot);

            if (pEncounter == nullptr)
            {
                continue;
            }

            std::string pictureName = encounterPictureBase(*pEncounter);

            if (pictureName.empty())
            {
                continue;
            }

            pictureName += " ";
            pictureName.push_back(tierLetter);
            const MonsterTable::MonsterStatsEntry *pStats =
                m_pMonsterTable->findStatsByPictureName(pictureName);

            if (pStats == nullptr)
            {
                continue;
            }

            const MonsterEntry *pMonsterEntry = m_pMonsterTable->findById(static_cast<int16_t>(pStats->id));

            if (pMonsterEntry == nullptr)
            {
                continue;
            }

            const IndoorResolvedSpawnPosition spawnPosition =
                resolveIndoorEncounterSpawnPosition(
                    *m_pIndoorMapData,
                    runtimeGeometry.vertices,
                    runtimeGeometry.geometryCache,
                    spawn,
                    static_cast<uint32_t>(spawnIndex),
                    spawnOrdinal,
                    m_sessionChestSeed);
            const bool hostileToParty = m_pMonsterTable->isHostileToParty(static_cast<int16_t>(pStats->id));
            MapDeltaActor actor = {};
            actor.name = pStats->name;
            actor.attributes = defaultActorAttributes(hostileToParty) | spawn.attributes;
            actor.hp = static_cast<int16_t>(std::clamp(pStats->hitPoints, 0, 32767));
            actor.hostilityType = static_cast<uint8_t>(std::clamp(pStats->hostility, 0, 255));
            actor.monsterInfoId = static_cast<int16_t>(pStats->id);
            actor.monsterId = static_cast<int16_t>(pStats->id);
            actor.radius = pMonsterEntry->radius;
            actor.height = pMonsterEntry->height;
            actor.moveSpeed = pMonsterEntry->movementSpeed;
            actor.x = static_cast<int>(std::lround(spawnPosition.position.x));
            actor.y = static_cast<int>(std::lround(spawnPosition.position.y));
            actor.z = static_cast<int>(std::lround(spawnPosition.position.z));
            actor.sectorId = spawnPosition.sectorId;
            actor.group = spawn.group;
            // Spawn group is AI grouping, not an ally/faction override.
            actor.ally = 0u;
            pMapDeltaData->actors.push_back(std::move(actor));
        }
    }
}
}
