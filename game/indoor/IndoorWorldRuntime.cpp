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
#include "game/gameplay/GameplayProjectileService.h"
#include "game/indoor/IndoorRenderer.h"
#include "game/indoor/IndoorGameView.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/maps/MapAssetLoader.h"
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
#include <filesystem>
#include <iostream>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr uint32_t RawContainingItemSize = 0x24;
constexpr float IndoorDroppedItemForwardOffset = 64.0f;
constexpr float IndoorDroppedItemHeightOffset = 32.0f;
constexpr float IndoorMinimapWorldHalfExtent = 32768.0f;
constexpr float IndoorMinimapWorldExtent = IndoorMinimapWorldHalfExtent * 2.0f;
constexpr float TicksPerSecond = 128.0f;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr float ActorUpdateStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedActorUpdateSeconds = 0.1f;
constexpr float ActiveActorUpdateRange = 6144.0f;

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
constexpr float PartyCollisionRadius = 37.0f;
constexpr float PartyCollisionHeight = 192.0f;
constexpr uint16_t LevelDecorationInvisible = 0x0020;
constexpr float PartyTargetHeightOffset = 96.0f;
constexpr float IndoorFloorSampleRise = 96.0f;
constexpr float IndoorFloorSampleDrop = 512.0f;
constexpr float IndoorProjectileGravity = 0.0f;
constexpr float IndoorProjectileBounceFactor = 0.0f;
constexpr float IndoorProjectileBounceStopVelocity = 0.0f;
constexpr float IndoorProjectileGroundDamping = 0.0f;
constexpr std::array<std::array<int, 3>, 4> IndoorEncounterDifficultyTierWeights = {{
    {60, 30, 10},
    {30, 50, 20},
    {10, 40, 50},
    {0, 25, 75}
}};

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
    float progress = std::numeric_limits<float>::max();
    float distanceSquared = std::numeric_limits<float>::max();
};

struct IndoorEncounterSpawnDescriptor
{
    int encounterSlot = 0;
    char fixedTier = '\0';
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

bx::Vec3 calculateIndoorEncounterSpawnPosition(
    float centerX,
    float centerY,
    float centerZ,
    uint16_t spawnRadius,
    uint16_t actorRadius,
    uint32_t spawnOrdinal)
{
    if (spawnOrdinal == 0)
    {
        return {centerX, centerY, centerZ};
    }

    const uint32_t ringOrdinal = spawnOrdinal - 1;
    const uint32_t ringIndex = ringOrdinal / 8;
    const uint32_t slotIndex = ringOrdinal % 8;
    const float baseRadius = std::max(
        static_cast<float>(std::max<uint16_t>(spawnRadius, 96)),
        static_cast<float>(actorRadius) * 2.0f + 16.0f);
    const float radius = baseRadius + static_cast<float>(ringIndex) * (baseRadius * 0.75f);
    const float angle = (2.0f * Pi * static_cast<float>(slotIndex)) / 8.0f;
    return {
        centerX + std::cos(angle) * radius,
        centerY + std::sin(angle) * radius,
        centerZ
    };
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

    const uint32_t faceId = static_cast<uint32_t>(faceIndex);
    uint32_t invisibleMask = 0;
    const auto setIterator = pEventRuntimeState->facetSetMasks.find(faceId);

    if (setIterator != pEventRuntimeState->facetSetMasks.end())
    {
        invisibleMask |= setIterator->second;
    }

    const auto clearIterator = pEventRuntimeState->facetClearMasks.find(faceId);

    if (clearIterator != pEventRuntimeState->facetClearMasks.end())
    {
        invisibleMask &= ~clearIterator->second;
    }

    return hasFaceAttribute(invisibleMask, FaceAttribute::Invisible);
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
        || state.darkGraspRemainingSeconds > 0.0f
        || state.slowMoveMultiplier != 1.0f
        || state.slowRecoveryMultiplier != 1.0f
        || state.shrinkDamageMultiplier != 1.0f
        || state.shrinkArmorClassMultiplier != 1.0f;
}

bool defaultActorHostileToParty(const MapDeltaActor &actor, const MonsterTable *pMonsterTable)
{
    const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;

    return (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) != 0
        || (pMonsterTable != nullptr
            && resolvedMonsterId > 0
            && pMonsterTable->isHostileToParty(resolvedMonsterId));
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

std::optional<IndoorProjectileCollisionCandidate> findProjectileIndoorFaceHit(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    const GameplayProjectileService::ProjectileState &projectile,
    const GameplayWorldPoint &segmentStart,
    const GameplayWorldPoint &segmentEnd)
{
    constexpr float PlaneEpsilon = 0.0001f;
    const bx::Vec3 start = {segmentStart.x, segmentStart.y, segmentStart.z};
    const bx::Vec3 end = {segmentEnd.x, segmentEnd.y, segmentEnd.z};
    const bx::Vec3 segment = {end.x - start.x, end.y - start.y, end.z - start.z};
    const float collisionPadding =
        static_cast<float>(std::max<uint16_t>(std::max(projectile.radius, projectile.height), 8));
    std::optional<IndoorProjectileCollisionCandidate> bestCollision;

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(
            indoorMapData,
            vertices,
            faceIndex);

        if (pGeometry == nullptr
            || !pGeometry->hasPlane
            || pGeometry->isPortal
            || hasFaceAttribute(pGeometry->attributes, FaceAttribute::Untouchable)
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
        collision.progress = progress;

        if (!bestCollision || projectileHitSortsBefore(collision, *bestCollision))
        {
            bestCollision = collision;
        }
    }

    return bestCollision;
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
    bool hostileToParty)
{
    GameplayActorTargetPolicyState state = {};
    state.monsterId = aiState.monsterId;
    state.preciseZ = aiState.preciseZ;
    state.height = height;
    state.hostileToParty = hostileToParty;
    state.controlMode = spellEffects.controlMode;
    return state;
}

void appendIndoorConnectedSectors(
    const IndoorMapData &indoorMapData,
    int16_t sectorId,
    std::vector<uint8_t> &reachableSectorMask)
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= indoorMapData.sectors.size())
    {
        return;
    }

    std::vector<int16_t> pendingSectorIds;
    pendingSectorIds.push_back(sectorId);

    while (!pendingSectorIds.empty())
    {
        const int16_t currentSectorId = pendingSectorIds.back();
        pendingSectorIds.pop_back();

        if (currentSectorId < 0
            || static_cast<size_t>(currentSectorId) >= indoorMapData.sectors.size()
            || reachableSectorMask[currentSectorId] != 0)
        {
            continue;
        }

        reachableSectorMask[currentSectorId] = 1;
        const IndoorSector &sector = indoorMapData.sectors[currentSectorId];

        auto appendConnectedSector = [&](uint16_t faceId)
        {
            if (faceId >= indoorMapData.faces.size())
            {
                return;
            }

            const IndoorFace &face = indoorMapData.faces[faceId];
            uint16_t connectedSectorId = std::numeric_limits<uint16_t>::max();

            if (face.roomNumber == currentSectorId)
            {
                connectedSectorId = face.roomBehindNumber;
            }
            else if (face.roomBehindNumber == currentSectorId)
            {
                connectedSectorId = face.roomNumber;
            }

            if (connectedSectorId < indoorMapData.sectors.size()
                && reachableSectorMask[connectedSectorId] == 0)
            {
                pendingSectorIds.push_back(static_cast<int16_t>(connectedSectorId));
            }
        };

        for (uint16_t faceId : sector.portalFaceIds)
        {
            appendConnectedSector(faceId);
        }

        for (uint16_t faceId : sector.faceIds)
        {
            appendConnectedSector(faceId);
        }
    }
}

std::vector<uint8_t> buildIndoorReachableSectorMask(const IndoorMapData *pIndoorMapData, int16_t sectorId)
{
    std::vector<uint8_t> reachableSectorMask;

    if (pIndoorMapData == nullptr)
    {
        return reachableSectorMask;
    }

    reachableSectorMask.assign(pIndoorMapData->sectors.size(), 0);
    appendIndoorConnectedSectors(*pIndoorMapData, sectorId, reachableSectorMask);
    return reachableSectorMask;
}

bool indoorSectorReachable(const std::vector<uint8_t> &reachableSectorMask, int16_t sectorId)
{
    return sectorId >= 0
        && static_cast<size_t>(sectorId) < reachableSectorMask.size()
        && reachableSectorMask[sectorId] != 0;
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
    const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
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
    state.hostileToParty = hostileToParty;
    state.hasDetectedParty = defaultActorHasDetectedParty(actor, hostileToParty);
    state.motionState = actor.hp <= 0 ? ActorAiMotionState::Dead : ActorAiMotionState::Standing;
    state.animationState = actor.hp <= 0 ? ActorAiAnimationState::Dead : actorAiAnimationStateFromIndoor(actor);
    state.spellEffects.hostileToParty = hostileToParty;
    state.spellEffects.hasDetectedParty = state.hasDetectedParty;
    state.preciseX = static_cast<float>(actor.x);
    state.preciseY = static_cast<float>(actor.y);
    state.preciseZ = static_cast<float>(actor.z);
    state.homePreciseX = state.preciseX;
    state.homePreciseY = state.preciseY;
    state.homePreciseZ = state.preciseZ;
    state.recoverySeconds = recoverySeconds;
    state.meleeAttackAnimationSeconds =
        actorAnimationSeconds(pActorSpriteFrameTable, pMonsterEntry, ActorAiAnimationState::AttackMelee, 0.3f);
    state.rangedAttackAnimationSeconds =
        actorAnimationSeconds(pActorSpriteFrameTable, pMonsterEntry, ActorAiAnimationState::AttackRanged, 0.3f);
    state.attackAnimationSeconds =
        std::max(state.meleeAttackAnimationSeconds, state.rangedAttackAnimationSeconds);
    state.attackCooldownSeconds =
        pActorService->initialAttackCooldownSeconds(state.actorId, state.recoverySeconds);
    state.idleDecisionSeconds = pActorService->initialIdleDecisionSeconds(state.actorId);
    return state;
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
    m_actorUpdateAccumulatorSeconds = 0.0f;
    materializeInitialMonsterSpawns();
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
    m_actorUpdateAccumulatorSeconds = 0.0f;
    materializeInitialMonsterSpawns();
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

void IndoorWorldRuntime::syncMapActorAiStates()
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();
    const size_t actorCount = pMapDeltaData != nullptr ? pMapDeltaData->actors.size() : 0;

    if (m_mapActorAiStates.size() > actorCount)
    {
        m_mapActorAiStates.resize(actorCount);
    }

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    for (size_t actorIndex = m_mapActorAiStates.size(); actorIndex < actorCount; ++actorIndex)
    {
        m_mapActorAiStates.push_back(
            buildIndoorMapActorAiState(
                pMapDeltaData->actors[actorIndex],
                actorIndex,
                m_pMonsterTable,
                m_pGameplayActorService,
                m_pActorSpriteFrameTable));
    }
}

std::vector<bool> IndoorWorldRuntime::selectIndoorActiveActors(const ActorPartyFacts &partyFacts) const
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
            || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0
            || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::FullAi)) == 0)
        {
            continue;
        }

        const float deltaX = partyFacts.position.x - pAiState->preciseX;
        const float deltaY = partyFacts.position.y - pAiState->preciseY;
        const float deltaZ = partyFacts.position.z - pAiState->preciseZ;
        const float distanceToParty =
            std::max(0.0f, length3d(deltaX, deltaY, deltaZ) - static_cast<float>(actor.radius));

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

    int16_t partySectorId = -1;

    if (m_pPartyRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
        facts.party.position = GameplayWorldPoint{moveState.x, moveState.y, moveState.footZ};
        partySectorId = moveState.sectorId;
    }

    const std::vector<bool> activeActorMask = selectIndoorActiveActors(facts.party);
    const std::vector<uint8_t> partyReachableSectorMask =
        buildIndoorReachableSectorMask(m_pIndoorMapData, partySectorId);
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return facts;
    }

    std::vector<IndoorVertex> vertices;
    IndoorFaceGeometryCache geometryCache;

    if (m_pIndoorMapData != nullptr)
    {
        vertices = buildIndoorMechanismAdjustedVertices(*m_pIndoorMapData, mapDeltaData(), eventRuntimeState());
        geometryCache.reset(m_pIndoorMapData->faces.size());
    }

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        const bool active = actorIndex < activeActorMask.size() && activeActorMask[actorIndex];
        const std::optional<ActorAiFacts> actorFacts =
            collectIndoorActorAiFacts(
                actorIndex,
                active,
                facts.party,
                partyReachableSectorMask,
                vertices,
                geometryCache);

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

    if (pMapDeltaData == nullptr)
    {
        return spellEffectsAppliedMask;
    }

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

            if (*update.state.hasDetectedParty)
            {
                actor.attributes |= static_cast<uint32_t>(EvtActorAttribute::Nearby);
            }
        }

        if (update.state.bloodSplatSpawned)
        {
            aiState.bloodSplatSpawned = *update.state.bloodSplatSpawned;
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

        if (update.movementIntent.clearVelocity)
        {
            aiState.velocityX = 0.0f;
            aiState.velocityY = 0.0f;
            aiState.velocityZ = 0.0f;
        }

        if (update.movementIntent.applyMovement)
        {
            applyIndoorActorMovementIntegration(update.actorIndex, update, actorAiSystem);
        }

        if (update.attackRequest)
        {
            const ActorAttackRequest &attackRequest = *update.attackRequest;

            if (attackRequest.kind == ActorAiAttackRequestKind::PartyMelee
                && m_pParty != nullptr)
            {
                m_pParty->applyDamageToActiveMember(attackRequest.damage, "monster attack");
            }
            else if (attackRequest.kind == ActorAiAttackRequestKind::ActorMelee
                && attackRequest.targetActorIndex < actorCount)
            {
                MapDeltaActor &targetActor = pMapDeltaData->actors[attackRequest.targetActorIndex];

                if (targetActor.hp > 0 && attackRequest.damage > 0)
                {
                    targetActor.hp =
                        static_cast<int16_t>(std::max(0, static_cast<int>(targetActor.hp) - attackRequest.damage));
                }
            }
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
            m_mapActorAiStates[fxRequest.actorIndex].bloodSplatSpawned = true;
        }
        else if (fxRequest.kind == ActorAiFxRequestKind::Hit || fxRequest.kind == ActorAiFxRequestKind::Spell)
        {
            triggerProjectileImpactVisual(fxRequest.actorIndex, fxRequest.spellId);
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
    spawnRequest.sourceX = projectileRequest.source.x;
    spawnRequest.sourceY = projectileRequest.source.y;
    spawnRequest.sourceZ = projectileRequest.source.z;
    spawnRequest.targetX = projectileRequest.target.x;
    spawnRequest.targetY = projectileRequest.target.y;
    spawnRequest.targetZ = projectileRequest.target.z;
    spawnRequest.spawnForwardOffset =
        static_cast<float>(std::max<uint16_t>(pMapDeltaData->actors[projectileRequest.sourceActorIndex].radius, 8))
        + 8.0f;
    spawnRequest.allowInstantImpact = true;

    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        m_pGameplayProjectileService->spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        m_pGameplayProjectileService->buildProjectileSpawnEffects(spawnResult);

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
        triggerProjectileImpactVisualAt(
            {spawnEffects.impactX, spawnEffects.impactY, spawnEffects.impactZ},
            static_cast<uint32_t>(definition.spellId));
    }

    return true;
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
    const uint32_t deltaTicks = GameplayProjectileService::ticksFromDeltaSeconds(deltaSeconds);
    const bool lifetimeExpired =
        m_pGameplayProjectileService->advanceProjectileLifetime(predictedProjectile, deltaTicks);

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
                    projectileVertices,
                    projectileGeometryCache,
                    projectile,
                    segmentStart,
                    segmentEnd);
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
                bestCollision = *partyHit;
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
                std::optional<IndoorProjectileCollisionCandidate> actorHit =
                    findProjectileCylinderHit(
                        segmentStart,
                        segmentEnd,
                        actorCenter,
                        static_cast<float>(actorState.radius) + static_cast<float>(projectile.radius),
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
            facts.hasCollision = true;
            facts.collision.kind = bestCollision->kind;
            facts.collision.point = bestCollision->point;
            facts.collision.actorIndex = bestCollision->actorIndex;

            if (bestCollision->kind == GameplayProjectileService::ProjectileFrameCollisionKind::World)
            {
                facts.collision.colliderName = "indoor face";
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
    const GameplayProjectileService::ProjectileFrameResult &frameResult)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (frameResult.directPartyDamage && m_pParty != nullptr)
    {
        m_pParty->applyDamageToActiveMember(*frameResult.directPartyDamage, "monster projectile");
    }

    if (frameResult.directActorImpact
        && frameResult.directActorImpact->actorIndex < mapActorCount()
        && pMapDeltaData != nullptr)
    {
        const GameplayProjectileService::ProjectileDirectActorImpact &impact =
            *frameResult.directActorImpact;

        if (impact.applyPartyProjectileDamage)
        {
            applyPartyAttackMeleeDamage(
                impact.actorIndex,
                impact.damage,
                {projectile.sourceX, projectile.sourceY, projectile.sourceZ});
        }
        else if (impact.applyNonPartyProjectileDamage && impact.damage > 0)
        {
            MapDeltaActor &targetActor = pMapDeltaData->actors[impact.actorIndex];
            targetActor.hp = static_cast<int16_t>(
                std::max(0, static_cast<int>(targetActor.hp) - impact.damage));
        }
    }

    if (frameResult.areaImpact)
    {
        const GameplayProjectileService::ProjectileFrameAreaImpactResult &areaImpact = *frameResult.areaImpact;

        if (areaImpact.impact.hitParty && m_pParty != nullptr)
        {
            m_pParty->applyDamageToActiveMember(areaImpact.impact.partyDamage, "projectile splash");
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

                if (targetActor.hp > 0 && actorHit.damage > 0)
                {
                    targetActor.hp =
                        static_cast<int16_t>(std::max(0, static_cast<int>(targetActor.hp) - actorHit.damage));
                }
            }
        }
    }

    if (frameResult.fxRequest)
    {
        triggerProjectileImpactVisualAt(
            frameResult.fxRequest->point,
            static_cast<uint32_t>(std::max(projectile.spellId, 0)));
    }

    if (frameResult.audioRequest)
    {
        pushIndoorProjectileAudioEvent(*frameResult.audioRequest);
    }

    for (const GameplayProjectileService::ProjectileSpawnRequest &spawnRequest : frameResult.spawnedProjectiles)
    {
        m_pGameplayProjectileService->spawnProjectile(spawnRequest);
    }

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
    }

    if (frameResult.applyMotionEnd)
    {
        m_pGameplayProjectileService->applyProjectileMotionEnd(projectile, frameResult.motion);
    }

    if (frameResult.expireProjectile)
    {
        m_pGameplayProjectileService->expireProjectile(projectile);
    }
}

void IndoorWorldRuntime::updateIndoorProjectiles(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || m_pGameplayProjectileService == nullptr)
    {
        return;
    }

    syncMapActorAiStates();

    const MapDeltaData *pMapDeltaData = mapDeltaData();
    const EventRuntimeState *pEventRuntimeState =
        m_pEventRuntimeState != nullptr && m_pEventRuntimeState->has_value() ? &m_pEventRuntimeState->value() : nullptr;
    std::vector<IndoorVertex> projectileVertices;
    IndoorFaceGeometryCache projectileGeometryCache;

    if (m_pIndoorMapData != nullptr)
    {
        projectileVertices = buildIndoorMechanismAdjustedVertices(*m_pIndoorMapData, pMapDeltaData, pEventRuntimeState);
        projectileGeometryCache.reset(m_pIndoorMapData->faces.size());
    }

    for (GameplayProjectileService::ProjectileState &projectile : m_pGameplayProjectileService->projectiles())
    {
        if (projectile.isExpired)
        {
            continue;
        }

        const GameplayProjectileService::ProjectileFrameFacts facts =
            collectIndoorProjectileFrameFacts(projectile, deltaSeconds, projectileVertices, projectileGeometryCache);
        const GameplayProjectileService::ProjectileFrameResult frameResult =
            m_pGameplayProjectileService->updateProjectileFrame(projectile, facts);
        applyIndoorProjectileFrameResult(projectile, frameResult);
    }

    m_pGameplayProjectileService->eraseExpiredProjectiles();
}

void IndoorWorldRuntime::applyIndoorActorMovementIntegration(
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
    const MonsterEntry *pMonsterEntry = resolveRuntimeMonsterEntry(*m_pMonsterTable, actor);

    if (pStats == nullptr)
    {
        return;
    }

    const float collisionRadius = indoorActorCollisionRadius(actor);
    const float collisionHeight =
        actor.height != 0
            ? indoorActorCollisionHeight(actor, collisionRadius)
            : pMonsterEntry != nullptr
                ? std::max(static_cast<float>(pMonsterEntry->height), collisionRadius * 2.0f + 2.0f)
                : indoorActorCollisionHeight(actor, collisionRadius);
    const uint16_t moveSpeed = actor.moveSpeed != 0
        ? actor.moveSpeed
        : pMonsterEntry != nullptr ? pMonsterEntry->movementSpeed : uint16_t(pStats->speed);
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

    IndoorMovementController movementController(*m_pIndoorMapData, m_pMapDeltaData, m_pEventRuntimeState);
    std::vector<IndoorActorCollision> actorColliders = actorMovementCollidersForActorMovement();

    if (m_pPartyRuntime != nullptr)
    {
        const IndoorMoveState &partyMoveState = m_pPartyRuntime->movementState();
        actorColliders.push_back(IndoorActorCollision{
            static_cast<size_t>(-1),
            partyMoveState.x,
            partyMoveState.y,
            partyMoveState.footZ,
            PartyCollisionRadius * 2.0f,
            PartyCollisionHeight,
            false});
    }

    movementController.setActorColliders(actorColliders);
    movementController.setDecorationColliders(decorationMovementColliders());
    movementController.setSpriteObjectColliders(spriteObjectMovementColliders());
    IndoorBodyDimensions body = {};
    body.radius = collisionRadius;
    body.height = collisionHeight;

    IndoorMoveState moveState =
        movementController.initializeStateFromEyePosition(oldX, oldY, oldZ + body.height, body);
    moveState.verticalVelocity = aiState.velocityZ;

    const float desiredVelocityX = update.movementIntent.desiredMoveX * effectiveMoveSpeed;
    const float desiredVelocityY = update.movementIntent.desiredMoveY * effectiveMoveSpeed;
    std::vector<size_t> contactedActorIndices;
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
            true);

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
    const std::vector<uint8_t> &partyReachableSectorMask,
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
    const MonsterEntry *pMonsterEntry = resolveRuntimeMonsterEntry(*m_pMonsterTable, actor);
    const uint16_t radius = actor.radius != 0
        ? actor.radius
        : pMonsterEntry != nullptr ? pMonsterEntry->radius : uint16_t(32);
    const uint16_t height = actor.height != 0
        ? actor.height
        : pMonsterEntry != nullptr ? pMonsterEntry->height : uint16_t(128);
    const uint16_t moveSpeed = actor.moveSpeed != 0
        ? actor.moveSpeed
        : pMonsterEntry != nullptr ? pMonsterEntry->movementSpeed : uint16_t(pStats->speed);
    const bool actorInvisible = (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0;
    const bool defaultHostile = defaultActorHostileToParty(actor, m_pMonsterTable);
    const bool hasEffectOverride = hasActiveActorSpellEffectOverride(aiState.spellEffects);
    const bool hostileToParty = hasEffectOverride
        ? aiState.spellEffects.hostileToParty
        : aiState.hostileToParty || defaultHostile;
    const bool hasDetectedParty = hasEffectOverride
        ? aiState.spellEffects.hasDetectedParty
        : aiState.hasDetectedParty || defaultActorHasDetectedParty(actor, hostileToParty);
    const GameplayActorTargetPolicyState actorPolicyState =
        buildIndoorActorTargetPolicyState(aiState, aiState.spellEffects, height, hostileToParty);
    const float actorTargetZ = aiState.preciseZ + std::max(24.0f, static_cast<float>(height) * 0.7f);
    const int16_t actorAuthoredSectorId = actor.sectorId;
    IndoorFloorSample floorSample = {};

    if (m_pIndoorMapData != nullptr && !vertices.empty())
    {
        floorSample = sampleIndoorFloor(
            *m_pIndoorMapData,
            vertices,
            aiState.preciseX,
            aiState.preciseY,
            aiState.preciseZ,
            IndoorFloorSampleRise,
            IndoorFloorSampleDrop,
            actorAuthoredSectorId >= 0 ? std::optional<int16_t>(actorAuthoredSectorId) : std::nullopt,
            nullptr,
            &geometryCache);
    }

    const int16_t actorSectorId = floorSample.hasFloor ? floorSample.sectorId : actorAuthoredSectorId;
    const int16_t partySectorId =
        m_pPartyRuntime != nullptr ? m_pPartyRuntime->movementState().sectorId : int16_t(-1);
    const std::vector<uint8_t> actorReachableSectorMask =
        buildIndoorReachableSectorMask(m_pIndoorMapData, actorSectorId);
    const bool sameSectorAsParty = actorSectorId >= 0 && actorSectorId == partySectorId;
    const bool portalPathToParty =
        sameSectorAsParty || indoorSectorReachable(actorReachableSectorMask, partySectorId);

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

    facts.runtime.motionState = actor.hp <= 0 ? ActorAiMotionState::Dead : aiState.motionState;
    facts.runtime.animationState = actor.hp <= 0 ? ActorAiAnimationState::Dead : aiState.animationState;
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
    facts.status.dead = actor.hp <= 0 || aiState.motionState == ActorAiMotionState::Dead;
    facts.status.hostileToParty = hostileToParty;
    facts.status.bloodSplatSpawned = aiState.bloodSplatSpawned;
    facts.status.hasDetectedParty = hasDetectedParty;
    facts.status.defaultHostileToParty = defaultHostile;

    const float partyTargetZ = partyFacts.position.z + PartyTargetHeightOffset;
    const float partyDeltaX = partyFacts.position.x - aiState.preciseX;
    const float partyDeltaY = partyFacts.position.y - aiState.preciseY;
    const float partyDeltaZ = partyTargetZ - actorTargetZ;
    const float partySenseRange = pActorService->partyEngagementRange(actorPolicyState);
    const bool actorCanSenseParty =
        portalPathToParty
        && std::abs(partyDeltaX) <= partySenseRange
        && std::abs(partyDeltaY) <= partySenseRange
        && std::abs(partyDeltaZ) <= partySenseRange
        && isWithinRange3d(partyDeltaX, partyDeltaY, partyDeltaZ, partySenseRange);
    facts.target.partyCanSenseActor =
        sameSectorAsParty || indoorSectorReachable(partyReachableSectorMask, actorSectorId);

    float bestTargetDistanceSquared = std::numeric_limits<float>::max();

    if (actorCanSenseParty)
    {
        const float distanceToParty = length3d(partyDeltaX, partyDeltaY, partyDeltaZ);
        facts.target.currentKind = ActorAiTargetKind::Party;
        facts.target.currentPosition = GameplayWorldPoint{partyFacts.position.x, partyFacts.position.y, partyTargetZ};
        facts.target.currentAudioPosition = facts.target.currentPosition;
        facts.target.currentDistance = distanceToParty;
        facts.target.currentEdgeDistance =
            std::max(0.0f, distanceToParty - static_cast<float>(radius) - partyFacts.collisionRadius);
        facts.target.currentCanSense = true;
        bestTargetDistanceSquared = distanceToParty * distanceToParty;
    }

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
        const bool otherDefaultHostile = defaultActorHostileToParty(otherActor, m_pMonsterTable);
        const bool otherHostileToParty =
            otherAiState.hostileToParty || otherDefaultHostile || otherAiState.spellEffects.hostileToParty;
        const GameplayActorTargetPolicyState otherPolicyState =
            buildIndoorActorTargetPolicyState(
                otherAiState,
                otherAiState.spellEffects,
                otherHeight,
                otherHostileToParty);
        const float otherTargetZ =
            otherAiState.preciseZ + std::max(24.0f, static_cast<float>(otherHeight) * 0.7f);
        const bool hasLineOfSight =
            otherActor.sectorId == actorSectorId
            || indoorSectorReachable(actorReachableSectorMask, otherActor.sectorId);

        ActorTargetCandidateFacts candidate = {};
        candidate.kind = ActorAiTargetKind::Actor;
        candidate.actorIndex = otherActorIndex;
        candidate.actorId = otherAiState.actorId;
        candidate.monsterId = otherAiState.monsterId;
        candidate.currentHp = otherActor.hp;
        candidate.policy = otherPolicyState;
        candidate.position = GameplayWorldPoint{otherAiState.preciseX, otherAiState.preciseY, otherTargetZ};
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
        bestTargetDistanceSquared = distanceSquared;
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
    facts.world.floorZ = floorSample.hasFloor ? floorSample.height : aiState.preciseZ;
    facts.world.sectorId = actorSectorId;
    facts.world.active = active;
    facts.world.activeByDistance = active;
    facts.world.sameSectorAsParty = sameSectorAsParty;
    facts.world.portalPathToParty = portalPathToParty;
    return facts;
}

const std::string &IndoorWorldRuntime::mapName() const
{
    return m_mapName;
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
        m_pPartyRuntime->setMovementSpeedMultiplier(enabled ? 2.0f : 1.0f);
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
                defaultActorHostileToParty(actor, m_pMonsterTable));
        }

        m_actorUpdateAccumulatorSeconds -= ActorUpdateStepSeconds;
    }
}

void IndoorWorldRuntime::updateWorld(float deltaSeconds)
{
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
    (void)eventId;
    (void)previousMessageCount;
    return false;
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
    (void)skillLevel;
    (void)skillMastery;
    (void)fromX;
    (void)fromY;
    (void)fromZ;
    (void)toX;
    (void)toY;
    (void)toZ;

    if (m_pEventRuntimeState == nullptr || !*m_pEventRuntimeState || m_pParty == nullptr)
    {
        return false;
    }

    EventRuntimeState::SpellFxRequest request = {};
    request.spellId = spellId;
    request.memberIndices.reserve(m_pParty->members().size());

    for (size_t memberIndex = 0; memberIndex < m_pParty->members().size(); ++memberIndex)
    {
        request.memberIndices.push_back(memberIndex);
    }

    (*m_pEventRuntimeState)->spellFxRequests.push_back(std::move(request));

    std::cout << "IndoorWorldRuntime: event spell " << spellId
              << " queued as FX only; projectile runtime support is pending\n";
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
    const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
    const bool hostileToParty =
        (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) != 0
        || (m_pMonsterTable != nullptr
            && resolvedMonsterId > 0
            && m_pMonsterTable->isHostileToParty(resolvedMonsterId));
    const bool defaultDetectedParty = hostileToParty && isAggressive;
    const MapActorAiState *pAiState =
        actorIndex < m_mapActorAiStates.size() ? &m_mapActorAiStates[actorIndex] : nullptr;
    const GameplayActorSpellEffectState *pEffectState =
        pAiState != nullptr ? &pAiState->spellEffects : nullptr;
    const bool useEffectOverride = pEffectState != nullptr && hasActiveActorSpellEffectOverride(*pEffectState);

    state.preciseX = pAiState != nullptr ? pAiState->preciseX : static_cast<float>(actor.x);
    state.preciseY = pAiState != nullptr ? pAiState->preciseY : static_cast<float>(actor.y);
    state.preciseZ = pAiState != nullptr ? pAiState->preciseZ : static_cast<float>(actor.z);
    state.radius = actor.radius;
    state.height = actor.height;
    state.isDead = actor.hp <= 0
        || (pAiState != nullptr && pAiState->motionState == ActorAiMotionState::Dead);
    state.isInvisible = isInvisible;
    state.hostileToParty = useEffectOverride ? pEffectState->hostileToParty
        : pAiState != nullptr ? (pAiState->hostileToParty || hostileToParty) : hostileToParty;
    state.hasDetectedParty = useEffectOverride ? pEffectState->hasDetectedParty
        : pAiState != nullptr ? (pAiState->hasDetectedParty || defaultDetectedParty) : defaultDetectedParty;
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
    const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(resolvedMonsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    state.displayName = resolveMapDeltaActorName(*m_pMonsterTable, actor);
    state.monsterId = resolvedMonsterId;
    state.currentHp = std::max(0, static_cast<int>(actor.hp));
    state.maxHp = std::max(0, pStats->hitPoints);
    state.isDead = actor.hp <= 0;

    int armorClass = pStats->armorClass;
    const GameplayActorSpellEffectState *pEffectState =
        actorIndex < m_mapActorAiStates.size() ? &m_mapActorAiStates[actorIndex].spellEffects : nullptr;

    if (pEffectState != nullptr)
    {
        state.slowRemainingSeconds = pEffectState->slowRemainingSeconds;
        state.stunRemainingSeconds = pEffectState->stunRemainingSeconds;
        state.paralyzeRemainingSeconds = pEffectState->paralyzeRemainingSeconds;
        state.fearRemainingSeconds = pEffectState->fearRemainingSeconds;
        state.shrinkRemainingSeconds = pEffectState->shrinkRemainingSeconds;
        state.darkGraspRemainingSeconds = pEffectState->darkGraspRemainingSeconds;
        state.controlMode = pEffectState->controlMode;

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

    const MonsterEntry *pMonsterEntry = resolveRuntimeMonsterEntry(*m_pMonsterTable, actor);
    const uint16_t spriteFrameIndex =
        resolveRuntimeActorSpriteFrameIndex(*m_pActorSpriteFrameTable, actor, pMonsterEntry);

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

    if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(inspectState.monsterId))
    {
        info.attackPreferences = pStats->attackPreferences;
    }

    return info;
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
    spawnRequest.skillLevel = request.skillLevel;
    spawnRequest.skillMastery = static_cast<uint32_t>(request.skillMastery);
    spawnRequest.damage = request.damage;
    spawnRequest.attackBonus = 0;
    spawnRequest.useActorHitChance = false;
    spawnRequest.sourceX = request.sourceX;
    spawnRequest.sourceY = request.sourceY;
    spawnRequest.sourceZ = request.sourceZ;
    spawnRequest.targetX = request.targetX;
    spawnRequest.targetY = request.targetY;
    spawnRequest.targetZ = request.targetZ;
    spawnRequest.spawnForwardOffset = PartyCollisionRadius;
    spawnRequest.allowInstantImpact = true;

    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        m_pGameplayProjectileService->spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        m_pGameplayProjectileService->buildProjectileSpawnEffects(spawnResult);

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
        triggerProjectileImpactVisualAt(
            {spawnEffects.impactX, spawnEffects.impactY, spawnEffects.impactZ},
            request.spellId);
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
    (void)partyX;
    (void)partyY;
    (void)partyZ;
    (void)sourcePartyMemberIndex;

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

    if (actor.hp <= 0
        || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
    {
        return false;
    }

    syncMapActorAiStates();
    GameplayActorSpellEffectState &effectState = m_mapActorAiStates[actorIndex].spellEffects;
    const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
    const bool defaultHostileToParty =
        (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) != 0
        || (m_pMonsterTable != nullptr
            && resolvedMonsterId > 0
            && m_pMonsterTable->isHostileToParty(resolvedMonsterId));

    if (m_pGameplayActorService != nullptr)
    {
        const GameplayActorService::SharedSpellEffectResult effectResult =
            m_pGameplayActorService->tryApplySharedSpellEffect(
                spellId,
                skillLevel,
                skillMastery,
                m_pGameplayActorService->actorLooksUndead(resolvedMonsterId),
                defaultHostileToParty,
                effectState);

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Rejected)
        {
            return false;
        }

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Applied)
        {
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

        if (edgeDistance > radius || requireLineOfSight)
        {
            continue;
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

bool IndoorWorldRuntime::canActivateWorldHit(
    const GameplayWorldHit &hit,
    GameplayInteractionMethod interactionMethod) const
{
    (void)interactionMethod;

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

    if (actorIndex < m_mapActorAiStates.size())
    {
        MapActorAiState &aiState = m_mapActorAiStates[actorIndex];
        aiState.hostileToParty = true;
        aiState.hasDetectedParty = true;
        aiState.spellEffects.hostileToParty = true;
        aiState.spellEffects.hasDetectedParty = true;
    }

    if (previousHp > 0 && nextHp <= 0 && m_pMonsterTable != nullptr && m_pParty != nullptr)
    {
        const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(resolvedMonsterId);

        if (pStats != nullptr && pStats->experience > 0)
        {
            m_pParty->grantSharedExperience(static_cast<uint32_t>(pStats->experience));
        }
    }

    (void)source;
    return actor.hp != previousHp;
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
        triggerProjectileImpactVisual(*actorIndex, 0);
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

    if (applied)
    {
        triggerProjectileImpactVisual(*actorIndex, request.spellId);
    }

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
        .sourceX = moveState.x + std::cos(yawRadians) * IndoorDroppedItemForwardOffset,
        .sourceY = moveState.y + std::sin(yawRadians) * IndoorDroppedItemForwardOffset,
        .sourceZ = moveState.footZ + IndoorDroppedItemHeightOffset,
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
    return m_pRenderer != nullptr ? m_pRenderer->pickGameplayWorldHit(request) : GameplayWorldHit{};
}

GameplayWorldHit IndoorWorldRuntime::pickHeldItemWorldTarget(const GameplayWorldPickRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->pickGameplayWorldHit(request) : GameplayWorldHit{};
}

GameplayWorldHit IndoorWorldRuntime::pickCurrentInteractionTarget(const GameplayWorldPickRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->pickGameplayWorldHit(request) : GameplayWorldHit{};
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
        m_pRenderer->triggerPendingSpellWorldFx(castResult);
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
    spriteObject.spriteId = pObjectEntry->spriteId;
    spriteObject.objectDescriptionId = *objectDescriptionId;
    spriteObject.x = int(std::lround(request.sourceX));
    spriteObject.y = int(std::lround(request.sourceY));
    spriteObject.z = int(std::lround(request.sourceZ));
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
    state.wizardEyeShowsMasterDecorations = wizardEyeMastery >= SkillMastery::Master;
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
    std::vector<uint8_t> visibleSectorMask(m_pIndoorMapData->sectors.size(), 0);
    std::vector<int16_t> pendingSectorIds;

    if (moveState.eyeSectorId >= 0 && static_cast<size_t>(moveState.eyeSectorId) < visibleSectorMask.size())
    {
        pendingSectorIds.push_back(moveState.eyeSectorId);
    }
    else if (moveState.sectorId >= 0 && static_cast<size_t>(moveState.sectorId) < visibleSectorMask.size())
    {
        pendingSectorIds.push_back(moveState.sectorId);
    }

    while (!pendingSectorIds.empty())
    {
        const int16_t sectorId = pendingSectorIds.back();
        pendingSectorIds.pop_back();

        if (sectorId < 0 || static_cast<size_t>(sectorId) >= visibleSectorMask.size())
        {
            continue;
        }

        if (visibleSectorMask[sectorId] != 0)
        {
            continue;
        }

        visibleSectorMask[sectorId] = 1;
        const IndoorSector &sector = m_pIndoorMapData->sectors[sectorId];

        auto appendPortalConnectedSectors = [&](const std::vector<uint16_t> &faceIds)
        {
            for (uint16_t faceId : faceIds)
            {
                if (faceId >= m_pIndoorMapData->faces.size())
                {
                    continue;
                }

                const IndoorFace &face = m_pIndoorMapData->faces[faceId];

                if (!face.isPortal && !hasFaceAttribute(
                    effectiveIndoorFaceAttributes(face, pMapDeltaData, faceId),
                    FaceAttribute::IsPortal))
                {
                    continue;
                }

                if (!indoorMinimapFaceVisible(face, pMapDeltaData, pEventRuntimeState, faceId))
                {
                    continue;
                }

                int16_t connectedSectorId = -1;

                if (face.roomNumber == sectorId)
                {
                    connectedSectorId = static_cast<int16_t>(face.roomBehindNumber);
                }
                else if (face.roomBehindNumber == sectorId)
                {
                    connectedSectorId = static_cast<int16_t>(face.roomNumber);
                }

                if (connectedSectorId < 0 || static_cast<size_t>(connectedSectorId) >= visibleSectorMask.size())
                {
                    continue;
                }

                if (visibleSectorMask[connectedSectorId] == 0)
                {
                    pendingSectorIds.push_back(connectedSectorId);
                }
            }
        };

        appendPortalConnectedSectors(sector.portalFaceIds);
        appendPortalConnectedSectors(sector.faceIds);
    }

    for (size_t faceIndex = 0; faceIndex < m_pIndoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];
        const bool sectorVisible =
            (face.roomNumber < visibleSectorMask.size() && visibleSectorMask[face.roomNumber] != 0)
            || (face.roomBehindNumber < visibleSectorMask.size() && visibleSectorMask[face.roomBehindNumber] != 0);

        if (!sectorVisible || !indoorMinimapFaceVisible(face, pMapDeltaData, pEventRuntimeState, faceIndex))
        {
            continue;
        }

        if (faceIndex < pMapDeltaData->faceAttributes.size())
        {
            pMapDeltaData->faceAttributes[faceIndex] |= faceAttributeBit(FaceAttribute::SeenByParty);
        }
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

        if (!indoorMinimapFaceVisible(face1, pMapDeltaData, pEventRuntimeState, outline.face1Id)
            || !indoorMinimapFaceVisible(face2, pMapDeltaData, pEventRuntimeState, outline.face2Id))
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

        setPackedIndoorOutlineBit(pMapDeltaData->visibleOutlines, outlineIndex);
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

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!actorRuntimeState(actorIndex, actorState) || actorState.isInvisible)
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

    if (!minimapState.wizardEyeShowsExpertObjects)
    {
        return;
    }

    for (const MapDeltaSpriteObject &spriteObject : pMapDeltaData->spriteObjects)
    {
        if (!hasContainingItemPayload(spriteObject.rawContainingItem))
        {
            continue;
        }

        GameplayMinimapMarkerState marker = {};
        marker.type = GameplayMinimapMarkerType::WorldItem;
        marker.u = indoorMinimapU(static_cast<float>(spriteObject.x));
        marker.v = indoorMinimapV(static_cast<float>(spriteObject.y));
        markers.push_back(marker);
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

    if (actor.hp > 0 || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
    {
        return false;
    }

    if (actorIndex >= m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews.resize(actorIndex + 1);
    }

    if (!m_mapActorCorpseViews[actorIndex].has_value())
    {
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats == nullptr)
        {
            return false;
        }

        const std::string &title = actor.name.empty() ? pStats->name : actor.name;
        CorpseViewState corpse = buildMonsterCorpseView(title, pStats->loot, m_pItemTable, m_pParty);

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

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
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
                matches = actor.monsterId == static_cast<int16_t>(id);
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

        if (actor.hp <= 0 || (invisibleAsDead && isInvisible))
        {
            ++defeatedActors;
        }
    }

    if (count > 0)
    {
        return defeatedActors >= static_cast<int>(count);
    }

    return totalActors == defeatedActors;
}

void IndoorWorldRuntime::applyEventRuntimeState()
{
    MapDeltaData *pMapDeltaData = mapDeltaData();
    EventRuntimeState *pEventRuntimeState = eventRuntimeState();

    if (pMapDeltaData == nullptr || pEventRuntimeState == nullptr)
    {
        return;
    }

    pMapDeltaData->eventVariables.mapVars = pEventRuntimeState->mapVars;

    for (const auto &[actorId, setMask] : pEventRuntimeState->actorSetMasks)
    {
        if (actorId < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[actorId].attributes |= setMask;
        }
    }

    for (const auto &[actorId, clearMask] : pEventRuntimeState->actorClearMasks)
    {
        if (actorId < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[actorId].attributes &= ~clearMask;
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
        for (MapDeltaActor &actor : pMapDeltaData->actors)
        {
            if (actor.group == groupId)
            {
                actor.attributes |= setMask;
            }
        }
    }

    for (const auto &[groupId, clearMask] : pEventRuntimeState->actorGroupClearMasks)
    {
        for (MapDeltaActor &actor : pMapDeltaData->actors)
        {
            if (actor.group == groupId)
            {
                actor.attributes &= ~clearMask;
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

std::vector<IndoorActorCollision> IndoorWorldRuntime::actorMovementCollidersForActorMovement() const
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

        const float radius = IndoorActorContactProbeRadius;
        const float actorCollisionRadius = indoorActorCollisionRadius(actor);
        const float height = indoorActorCollisionHeight(actor, actorCollisionRadius);

        if (radius <= 0.0f || height <= 0.0f)
        {
            continue;
        }

        colliders.push_back(IndoorActorCollision{
            actorIndex,
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

        const float radius = indoorActorCollisionRadius(actor);
        const float height = indoorActorCollisionHeight(actor, radius);

        if (radius <= 0.0f || height <= 0.0f)
        {
            continue;
        }

        colliders.push_back(IndoorActorCollision{
            actorIndex,
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
    m_actorUpdateAccumulatorSeconds = snapshot.actorUpdateAccumulatorSeconds;
    syncMapActorAiStates();

    if (!snapshot.mapActorSpellEffectStates.empty())
    {
        const size_t actorCount = std::min(snapshot.mapActorSpellEffectStates.size(), m_mapActorAiStates.size());

        for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
        {
            m_mapActorAiStates[actorIndex].spellEffects = snapshot.mapActorSpellEffectStates[actorIndex];
        }
    }
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

    if (!m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = buildChestView(chestId);
    }

    m_activeChestView = *m_materializedChestViews[chestId];
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

void IndoorWorldRuntime::triggerProjectileImpactVisualAt(const GameplayWorldPoint &point, uint32_t spellId)
{
    if (m_pRenderer == nullptr)
    {
        return;
    }

    m_pRenderer->triggerProjectileImpactWorldFx(point.x, point.y, point.z, spellId);
}

void IndoorWorldRuntime::triggerProjectileImpactVisual(size_t actorIndex, uint32_t spellId)
{
    const std::optional<GameplayWorldPoint> impactPoint = actorImpactPoint(actorIndex);

    if (!impactPoint)
    {
        return;
    }

    triggerProjectileImpactVisualAt(*impactPoint, spellId);
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

    for (size_t spawnIndex = 0; spawnIndex < m_pIndoorMapData->spawns.size(); ++spawnIndex)
    {
        const IndoorSpawn &spawn = m_pIndoorMapData->spawns[spawnIndex];

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

            const uint16_t actorRadius = std::max<uint16_t>(pMonsterEntry->radius, 32);
            const bx::Vec3 spawnPosition = calculateIndoorEncounterSpawnPosition(
                static_cast<float>(spawn.x),
                static_cast<float>(spawn.y),
                static_cast<float>(spawn.z),
                spawn.radius,
                actorRadius,
                spawnOrdinal);
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
            actor.x = static_cast<int>(std::lround(spawnPosition.x));
            actor.y = static_cast<int>(std::lround(spawnPosition.y));
            actor.z = static_cast<int>(std::lround(spawnPosition.z));
            actor.group = spawn.group;
            actor.ally = hostileToParty ? 0u : spawn.group;
            pMapDeltaData->actors.push_back(std::move(actor));
        }
    }
}
}
