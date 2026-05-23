#include "game/outdoor/OutdoorWorldRuntime.h"

#include "game/data/ActorNameResolver.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/tables/ChestTable.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/WorldFxSystem.h"
#include "game/gameplay/BountyHuntRuntime.h"
#include "game/gameplay/ChestRuntime.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameplayBolsterRuntime.h"
#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/MonsterSpellSupport.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/gameplay/StealingRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/gameplay/TreasureRuntime.h"
#include "game/events/EventProjectileSpells.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/tables/ItemTable.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorGameplayInputController.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/party/EventSpellBuffs.h"
#include "game/party/PartySpellSystem.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/party/SpellIds.h"
#include "game/audio/SoundIds.h"
#include "game/SpriteObjectDefs.h"
#include "game/party/SkillData.h"
#include "game/tables/ObjectTable.h"
#include "game/StringUtils.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/WizardEyeMinimapRules.h"

#include <bx/math.h>

#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float GameMinutesPerRealSecond = 0.5f;
constexpr float CollisionEpsilon = 0.01f;
constexpr float OutdoorMechanismGeometryRefreshStepSeconds = 1.0f / 30.0f;

std::string resolveSpawnedMapActorName(
    const MonsterTable &monsterTable,
    const MonsterTable::MonsterStatsEntry &stats,
    uint32_t uniqueNameId)
{
    if (uniqueNameId != 0)
    {
        const std::optional<std::string> uniqueName =
            monsterTable.getUniqueName(static_cast<int32_t>(uniqueNameId));

        if (uniqueName && !uniqueName->empty())
        {
            return *uniqueName;
        }
    }

    return stats.name;
}

float outdoorMechanismOpenFraction(
    const RuntimeMechanismState &mechanism,
    const EventRuntimeState::OutdoorModelMechanismDefinition &definition)
{
    const float moveTimeMs = std::max(1.0f, static_cast<float>(definition.moveTimeMs));

    if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Open))
    {
        return 1.0f;
    }

    if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closed))
    {
        return 0.0f;
    }

    if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
    {
        return std::clamp(mechanism.timeSinceTriggeredMs / moveTimeMs, 0.0f, 1.0f);
    }

    if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
    {
        return 1.0f - std::clamp(mechanism.timeSinceTriggeredMs / moveTimeMs, 0.0f, 1.0f);
    }

    return definition.closed ? 0.0f : 1.0f;
}

OutdoorBModel translatedOutdoorBModel(
    const OutdoorBModel &bmodel,
    const EventRuntimeState *pEventRuntimeState,
    size_t bModelIndex)
{
    if (pEventRuntimeState == nullptr)
    {
        return bmodel;
    }

    for (const std::pair<const uint32_t, EventRuntimeState::OutdoorModelMechanismDefinition> &entry :
        pEventRuntimeState->outdoorModelMechanisms)
    {
        const EventRuntimeState::OutdoorModelMechanismDefinition &definition = entry.second;

        if (definition.bmodelIndex != bModelIndex)
        {
            continue;
        }

        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
            pEventRuntimeState->mechanisms.find(entry.first);

        if (mechanismIterator == pEventRuntimeState->mechanisms.end())
        {
            continue;
        }

        const float fraction = outdoorMechanismOpenFraction(mechanismIterator->second, definition);
        const int32_t offsetX = static_cast<int32_t>(std::lround(static_cast<float>(definition.dx) * fraction));
        const int32_t offsetY = static_cast<int32_t>(std::lround(static_cast<float>(definition.dy) * fraction));
        const int32_t offsetZ = static_cast<int32_t>(std::lround(static_cast<float>(definition.dz) * fraction));

        if (offsetX == 0 && offsetY == 0 && offsetZ == 0)
        {
            return bmodel;
        }

        OutdoorBModel translated = bmodel;
        translated.positionX += offsetX;
        translated.positionY += offsetY;
        translated.positionZ += offsetZ;
        translated.minX += offsetX;
        translated.maxX += offsetX;
        translated.minY += offsetY;
        translated.maxY += offsetY;
        translated.minZ += offsetZ;
        translated.maxZ += offsetZ;
        translated.boundingCenterX += offsetX;
        translated.boundingCenterY += offsetY;
        translated.boundingCenterZ += offsetZ;

        for (OutdoorBModelVertex &vertex : translated.vertices)
        {
            vertex.x += offsetX;
            vertex.y += offsetY;
            vertex.z += offsetZ;
        }

        return translated;
    }

    return bmodel;
}
constexpr int MinutesPerDay = 24 * 60;
constexpr int DaysPerMonth = 28;
constexpr uint32_t ActorInvisibleBit = static_cast<uint32_t>(EvtActorAttribute::Invisible);
constexpr uint32_t ActorAggressorBit = static_cast<uint32_t>(EvtActorAttribute::Aggressor);
constexpr uint32_t ActorHostileBit = static_cast<uint32_t>(EvtActorAttribute::Hostile);
constexpr uint32_t ActorAlertStatusBit = static_cast<uint32_t>(EvtActorAttribute::AlertStatus);
constexpr float TicksPerSecond = 128.0f;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr float HostilityCloseRange = 1024.0f;
constexpr float HostilityShortRange = 2560.0f;
constexpr float HostilityMediumRange = 5120.0f;
constexpr float HostilityLongRange = 10240.0f;

uint32_t nextInspectPreviewRandom(OutdoorWorldRuntime::ActorInspectPreviewAnimationState &state)
{
    state.randomState = state.randomState * 1664525u + 1013904223u;
    return state.randomState;
}

uint32_t randomInspectPreviewSecondsTicks(
    OutdoorWorldRuntime::ActorInspectPreviewAnimationState &state,
    uint32_t minimumSeconds,
    uint32_t maximumSeconds)
{
    const uint32_t span = maximumSeconds >= minimumSeconds ? maximumSeconds - minimumSeconds + 1u : 1u;
    return (minimumSeconds + nextInspectPreviewRandom(state) % span) * static_cast<uint32_t>(TicksPerSecond);
}

uint32_t monsterTypeGroupId(int16_t monsterId)
{
    return monsterId > 0 ? (static_cast<uint32_t>(monsterId - 1) / 3u) + 1u : 0u;
}

bool monsterInspectPreviewIsPeasant(int16_t monsterId, const std::string &displayName)
{
    const uint32_t groupId = monsterTypeGroupId(monsterId);

    if ((groupId >= 39u && groupId <= 62u) || (groupId >= 78u && groupId <= 83u))
    {
        return true;
    }

    const std::string lowercaseName = toLowerCopy(displayName);
    return lowercaseName.find("peasant") != std::string::npos
        || lowercaseName.find("farmer") != std::string::npos
        || lowercaseName.find("villager") != std::string::npos;
}

int monsterInspectPreviewYOffset(int16_t monsterId)
{
    // Copied from OE's monster_popup_y_offsets table; OE subtracts another 40 before drawing.
    // Merged MM8 ids can map past OE's MONSTER_TYPE_LAST and should not inherit the OE fallback offset.
    static constexpr std::array<int, 93> yOffsets = {{
        0, -20, 20, 0, -40, 0, 0, 0, 0, 0,
        0, -50, 20, 0, -10, -10, -20, 10, -10, 0,
        0, 0, -20, 10, -10, 0, 0, 0, -20, -10,
        0, 0, 0, -40, -20, 0, 0, 0, -50, -30,
        -30, -30, -30, -30, -30, 0, 0, 0, 0, 0,
        0, -20, -20, -20, 20, 20, 20, 10, 10, 10,
        10, 10, 10, -90, -60, -40, -20, -20, -80, -10,
        0, 0, -40, 0, 0, 0, -20, 10, 0, 0,
        0, 0, 0, 0, 0, -60, 0, 0, 0, 0,
        0, 0, 0,
    }};
    const uint32_t groupId = monsterTypeGroupId(monsterId);

    if (groupId == 0)
    {
        return -40;
    }

    if (groupId >= yOffsets.size())
    {
        return 0;
    }

    return yOffsets[groupId] - 40;
}

uint32_t spriteAnimationLengthTicks(
    const SpriteFrameTable *pSpriteFrameTable,
    uint16_t spriteFrameIndex,
    uint32_t fallbackTicks)
{
    if (pSpriteFrameTable == nullptr || spriteFrameIndex == 0)
    {
        return fallbackTicks;
    }

    const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteFrameIndex, 0);

    if (pFrame == nullptr || pFrame->animationLengthTicks <= 0)
    {
        return fallbackTicks;
    }

    return static_cast<uint32_t>(pFrame->animationLengthTicks);
}

uint16_t actorInspectPreviewSpriteFrameIndex(
    const OutdoorWorldRuntime::MapActorState &actor,
    OutdoorWorldRuntime::ActorAnimation animation)
{
    const size_t animationIndex = static_cast<size_t>(animation);

    if (animationIndex < actor.actionSpriteFrameIndices.size()
        && actor.actionSpriteFrameIndices[animationIndex] != 0)
    {
        return actor.actionSpriteFrameIndices[animationIndex];
    }

    return actor.spriteFrameIndex;
}

void resetActorInspectPreviewAnimation(
    OutdoorWorldRuntime::ActorInspectPreviewAnimationState &state,
    const OutdoorWorldRuntime::MapActorState &actor,
    uint32_t nowTicks)
{
    state.monsterId = actor.monsterId;
    state.animation = OutdoorWorldRuntime::ActorAnimation::Bored;
    state.actionTimeTicks = 0;
    state.actionLengthTicks = randomInspectPreviewSecondsTicks(state, 1, 3);
    state.lastUpdateTicks = nowTicks;
}

void advanceActorInspectPreviewAnimation(
    OutdoorWorldRuntime::ActorInspectPreviewAnimationState &state,
    const OutdoorWorldRuntime::MapActorState &actor,
    const SpriteFrameTable *pSpriteFrameTable,
    uint32_t nowTicks)
{
    if (state.monsterId != actor.monsterId)
    {
        resetActorInspectPreviewAnimation(state, actor, nowTicks);
        return;
    }

    const uint32_t elapsedTicks = nowTicks >= state.lastUpdateTicks ? nowTicks - state.lastUpdateTicks : 0u;
    state.lastUpdateTicks = nowTicks;
    state.actionTimeTicks += elapsedTicks;

    if (state.actionLengthTicks != 0 && state.actionTimeTicks <= state.actionLengthTicks)
    {
        return;
    }

    state.actionTimeTicks = 0;

    if (state.animation == OutdoorWorldRuntime::ActorAnimation::Bored
        || state.animation == OutdoorWorldRuntime::ActorAnimation::AttackMelee)
    {
        state.animation = OutdoorWorldRuntime::ActorAnimation::Standing;
        state.actionLengthTicks = randomInspectPreviewSecondsTicks(state, 1, 2);
        return;
    }

    state.animation = monsterInspectPreviewIsPeasant(actor.monsterId, actor.displayName)
        ? OutdoorWorldRuntime::ActorAnimation::Bored
        : OutdoorWorldRuntime::ActorAnimation::AttackMelee;
    state.actionLengthTicks = spriteAnimationLengthTicks(
        pSpriteFrameTable,
        actorInspectPreviewSpriteFrameIndex(actor, state.animation),
        static_cast<uint32_t>(TicksPerSecond));
}

float localRelationEngagementRange(int relation)
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

std::optional<int32_t> localMonsterRelation(
    const EventRuntimeState *pEventRuntimeState,
    uint32_t leftMonsterId,
    uint32_t rightMonsterId)
{
    if (pEventRuntimeState == nullptr)
    {
        return std::nullopt;
    }

    const auto iterator =
        pEventRuntimeState->monsterRelationOverrides.find(
            EventRuntime::monsterRelationOverrideKey(leftMonsterId, rightMonsterId));
    return iterator != pEventRuntimeState->monsterRelationOverrides.end()
        ? std::optional<int32_t>(iterator->second)
        : std::nullopt;
}

bool chestViewContainsItem(const GameplayChestViewState &view, uint32_t itemId)
{
    for (const GameplayChestItemState &item : view.items)
    {
        if (!item.isGold && (item.itemId == itemId || item.item.objectDescriptionId == itemId))
        {
            return true;
        }
    }

    for (const GameplayChestItemState &item : view.hiddenItems)
    {
        if (!item.isGold && (item.itemId == itemId || item.item.objectDescriptionId == itemId))
        {
            return true;
        }
    }

    return false;
}

std::optional<GameplayChestItemState> buildFixedChestItem(uint32_t itemId, const ItemTable *pItemTable)
{
    if (itemId == 0 || pItemTable == nullptr)
    {
        return std::nullopt;
    }

    GameplayChestItemState item = {};
    item.item = ItemGenerator::makeInventoryItem(itemId, *pItemTable, ItemGenerationMode::ChestLoot);
    item.itemId = item.item.objectDescriptionId;
    item.quantity = item.item.quantity;

    const ItemDefinition *pDefinition = pItemTable->get(item.itemId);
    item.width = pDefinition != nullptr ? std::max<uint8_t>(1, pDefinition->inventoryWidth) : 1;
    item.height = pDefinition != nullptr ? std::max<uint8_t>(1, pDefinition->inventoryHeight) : 1;
    return item;
}
constexpr float ActorMeleeRange = 307.2f;
constexpr float ActiveActorUpdateRange = 5632.0f;
constexpr size_t MaxActiveActorUpdates = 48;
constexpr float InactiveActorDecisionIntervalSeconds = 1.5f;
constexpr float InactiveActorBoredSeconds = 2.0f;
constexpr uint32_t InactiveActorFidgetChancePercent = 5u;
constexpr float TurnBasedActorStandMinSeconds = 1.0f;
constexpr float TurnBasedActorStandMaxSeconds = 2.0f;
constexpr float TurnBasedActorBoredFallbackSeconds = 2.0f;
constexpr uint32_t TurnBasedActorBoredChancePercent = 50u;
constexpr float PeasantAggroRadius = 4096.0f;
constexpr float PartyCollisionRadius = 37.0f;
constexpr float PartyCollisionHeight = 192.0f;
constexpr float OutdoorFaceSpatialCellSize = 2048.0f;
constexpr uint16_t LevelDecorationVisibleOnMap = 0x0008;
constexpr uint16_t LevelDecorationInvisible = 0x0020;
constexpr bool DebugProjectileSpawnLogging = false;
constexpr bool DebugProjectileCollisionLogging = false;
constexpr bool DebugProjectileLifetimeLogging = false;
constexpr bool DebugProjectileImpactLogging = false;
constexpr bool DebugProjectileAoeLogging = false;
constexpr float ActorInertiaVelocityDecay = 0.8392334f;
constexpr float ActorInertiaReferenceFrameRate = 60.0f;
constexpr float ActorStopVelocitySquared = 400.0f;
constexpr float ActorKnockbackVelocityStep = 50.0f;
constexpr int ActorMaxKnockbackSteps = 10;

bool blasterProjectileTraceEnabled()
{
    static const bool environmentEnabled =
        []()
        {
            const char *pValue = std::getenv("OPENYAMM_BLASTER_PROJECTILE_TRACE");
            return pValue != nullptr && pValue[0] != '\0' && std::strcmp(pValue, "0") != 0;
        }();
    return environmentEnabled || gameplayCombatTraceEnabled();
}

void writeBlasterProjectileTrace(const std::string &message)
{
    if (gameplayCombatTraceEnabled())
    {
        gameplayCombatTraceWrite(message);
        return;
    }

    gameplayDebugTraceWrite(message);
}

bool projectileLooksLikeBlasterTraceTarget(const OutdoorWorldRuntime::ProjectileState &projectile)
{
    return projectile.sourceKind == OutdoorWorldRuntime::ProjectileState::SourceKind::Party
        && (projectile.objectDescriptionId == 555
            || projectile.objectName.find("Laser") != std::string::npos
            || projectile.objectName.find("laser") != std::string::npos
            || projectile.objectSpriteName.find("lzrbolt") != std::string::npos);
}

bool outdoorActorIsTerminalCorpse(const OutdoorWorldRuntime::MapActorState &actor)
{
    return actor.isDead
        || actor.currentHp <= 0
        || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dying
        || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead;
}

bool outdoorActorCorpsePhysicsNeedsStep(const OutdoorWorldRuntime::MapActorState &actor)
{
    if (!outdoorActorIsTerminalCorpse(actor) || actor.isInvisible)
    {
        return false;
    }

    return !actor.movementStateInitialized
        || actor.movementState.airborne
        || actor.velocityX * actor.velocityX + actor.velocityY * actor.velocityY >= ActorStopVelocitySquared
        || actor.velocityZ * actor.velocityZ >= ActorStopVelocitySquared;
}

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
        case CombatDamageType::Energy: return 0;
        case CombatDamageType::Irresistible: return 0;
        case CombatDamageType::Physical:
        default:
            return stats.physicalResistance;
    }
}

int monsterHourOfPowerResistanceBonus(const OutdoorWorldRuntime::MapActorState &actor)
{
    if (actor.hourOfPowerRemainingSeconds <= 0.0f)
    {
        return 0;
    }

    return std::max(0, actor.hourOfPowerPower);
}

uint32_t monsterActorAttackSeed(
    uint32_t sourceActorId,
    uint32_t targetActorId,
    uint32_t attackDecisionCount,
    int damage,
    CombatDamageType damageType,
    uint32_t salt)
{
    return sourceActorId * 1103515245u
        ^ targetActorId * 2654435761u
        ^ attackDecisionCount * 2246822519u
        ^ static_cast<uint32_t>(std::max(0, damage)) * 3266489917u
        ^ static_cast<uint32_t>(damageType) * 668265263u
        ^ salt;
}

constexpr std::array<std::array<int, 3>, 6> EncounterDifficultyTierWeights = {{
    {{100, 0, 0}},
    {{90, 8, 2}},
    {{70, 20, 10}},
    {{50, 30, 20}},
    {{30, 40, 30}},
    {{10, 50, 40}},
}};
constexpr float GroundSnapHeight = 1.0f;
constexpr float OeNonFlyingActorRadius = 40.0f;
constexpr float ActorUpdateStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedActorUpdateSeconds = 0.1f;
constexpr float ProjectileUpdateStepSeconds = 1.0f / 60.0f;
constexpr int MaxProjectileUpdateStepsPerFrame = 4;
constexpr float MaxAccumulatedProjectileUpdateSeconds =
    ProjectileUpdateStepSeconds * static_cast<float>(MaxProjectileUpdateStepsPerFrame);
constexpr int JournalRevealWidth = 88;
constexpr int JournalRevealHeight = 88;
constexpr int JournalRevealBytesPerRow = 11;
constexpr float JournalMapWorldHalfExtent = 32768.0f;

void ensureJournalRevealMaskSize(std::vector<uint8_t> &bytes)
{
    const size_t expectedSize = JournalRevealHeight * JournalRevealBytesPerRow;

    if (bytes.size() != expectedSize)
    {
        bytes.assign(expectedSize, 0);
    }
}

void setPackedRevealBit(std::vector<uint8_t> &bytes, int cellX, int cellY)
{
    if (cellX < 0 || cellX >= JournalRevealWidth || cellY < 0 || cellY >= JournalRevealHeight)
    {
        return;
    }

    const size_t index = static_cast<size_t>(cellY * JournalRevealWidth + cellX);
    const size_t byteIndex = index / 8;

    if (byteIndex >= bytes.size())
    {
        return;
    }

    const uint8_t mask = static_cast<uint8_t>(1u << (7u - static_cast<unsigned>(index % 8)));
    bytes[byteIndex] |= mask;
}

void updateOutdoorJournalRevealMask(const OutdoorPartyRuntime &partyRuntime, MapDeltaData &outdoorMapDeltaData)
{
    ensureJournalRevealMaskSize(outdoorMapDeltaData.fullyRevealedCells);
    ensureJournalRevealMaskSize(outdoorMapDeltaData.partiallyRevealedCells);

    const OutdoorMoveState &moveState = partyRuntime.movementState();
    const float centerU = std::clamp(
        (moveState.x + JournalMapWorldHalfExtent) / (JournalMapWorldHalfExtent * 2.0f),
        0.0f,
        0.999999f);
    const float centerV = std::clamp(
        (JournalMapWorldHalfExtent - moveState.y) / (JournalMapWorldHalfExtent * 2.0f),
        0.0f,
        0.999999f);
    const int centerCellX = static_cast<int>(std::floor(centerU * static_cast<float>(JournalRevealWidth)));
    const int centerCellY = static_cast<int>(std::floor(centerV * static_cast<float>(JournalRevealHeight)));

    for (int offsetY = -10; offsetY < 10; ++offsetY)
    {
        const int cellY = centerCellY + offsetY;

        for (int offsetX = -10; offsetX < 10; ++offsetX)
        {
            const int cellX = centerCellX + offsetX;
            const int distanceSquared = offsetX * offsetX + offsetY * offsetY;

            if (distanceSquared > 100)
            {
                continue;
            }

            setPackedRevealBit(outdoorMapDeltaData.partiallyRevealedCells, cellX, cellY);

            if (distanceSquared <= 49)
            {
                setPackedRevealBit(outdoorMapDeltaData.fullyRevealedCells, cellX, cellY);
            }
        }
    }
}
constexpr float Pi = 3.14159265358979323846f;
constexpr float CameraVerticalFovRadians = Pi / 3.0f;
constexpr float SpecialJumpAngleUnitsPerTurn = 2048.0f;
constexpr float LegacyOutdoorSpecialJumpGravity = 800.0f;
constexpr float OutdoorMovementGravity = 1280.0f;

int16_t legacyEventMonsterIdToStatsId(uint32_t eventMonsterId)
{
    if (eventMonsterId >= static_cast<uint32_t>(std::numeric_limits<int16_t>::max()))
    {
        return 0;
    }

    return static_cast<int16_t>(eventMonsterId + 1u);
}
constexpr float PartyTargetHeightOffset = 96.0f;
constexpr float ChestTrapForwardDepth = 96.0f;
constexpr float ChestTrapForwardPitchScale = 0.70710678f;
constexpr float ChestTrapCenterSpriteZOffset = 32.0f;
constexpr float OeTurnAwayFromWaterAngleRadians = Pi / 32.0f;
constexpr int DaggerWoundIslandMapId = 1;
constexpr uint32_t EventSpellSourceId = std::numeric_limits<uint32_t>::max();
constexpr uint32_t GoldHeapSmallItemId = 187;
constexpr uint32_t GoldHeapLargeItemId = 189;
constexpr float WorldItemThrowPitchRadians = Pi * 2.0f * (184.0f / 2048.0f);
constexpr float WorldItemThrowSpeed = 200.0f;
constexpr int MonsterDeathDropMinThrowSpeed = 200;
constexpr int MonsterDeathDropMaxThrowSpeed = 399;
constexpr float WorldItemGravity = 900.0f;
constexpr float WorldItemBounceFactor = 0.5f;
constexpr float WorldItemGroundDamping = 0.89263916f;
constexpr float WorldItemRestingHorizontalSpeedSquared = 400.0f;
constexpr float WorldItemBounceStopVelocity = 10.0f;
constexpr float WorldItemGroundClearance = 1.0f;
constexpr float WorldItemSupportFloorProbeHeight = 96.0f;
constexpr int32_t MapWeatherFoggy = 1;
constexpr int32_t MapWeatherSnowing = 2;
constexpr int32_t MapWeatherRaining = 4;
constexpr float DefaultOutdoorVisibilityDistance = 200000.0f;
constexpr uint8_t UnderwaterFogRed = 33;
constexpr uint8_t UnderwaterFogGreen = 142;
constexpr uint8_t UnderwaterFogBlue = 90;
constexpr float ArmageddonDurationSeconds = 256.0f / TicksPerSecond;
constexpr uint32_t ArmageddonShakeStepCount = 60;
constexpr float ArmageddonShakeYawRadians = 0.035f;
constexpr float ArmageddonShakePitchRadians = 0.024f;
constexpr size_t MaxOutdoorBloodSplats = 64;
constexpr size_t BloodSplatGridResolution = 10;
constexpr float BloodSplatHeightOffset = 2.0f;
constexpr float BloodSplatMinSurfaceHeightTolerance = 32.0f;
constexpr float ReanimatedActorWanderRadius = 1024.0f;

enum class InactiveActorDeathAction : uint8_t
{
    Continue = 0,
    HoldDead = 1,
    MarkDead = 2,
    AdvanceDying = 3,
};

struct InactiveActorDeathFrame
{
    InactiveActorDeathAction action = InactiveActorDeathAction::Continue;
    float actionSeconds = 0.0f;
    bool finishedDying = false;
};

struct OutdoorActiveActorCandidate
{
    size_t actorIndex = static_cast<size_t>(-1);
    float distanceToParty = 0.0f;
    bool eligible = false;
};

InactiveActorDeathFrame resolveInactiveActorDeathFrame(
    bool dead,
    bool hpDepleted,
    bool dying,
    float actionSeconds,
    float deltaSeconds)
{
    InactiveActorDeathFrame result = {};

    if (dead)
    {
        result.action = InactiveActorDeathAction::HoldDead;
        return result;
    }

    if (!hpDepleted && !dying)
    {
        return result;
    }

    if (!dying)
    {
        result.action = InactiveActorDeathAction::MarkDead;
        return result;
    }

    result.action = InactiveActorDeathAction::AdvanceDying;
    result.actionSeconds = std::max(0.0f, actionSeconds - std::max(0.0f, deltaSeconds));
    result.finishedDying = result.actionSeconds <= 0.0f;
    return result;
}

float rainIntensityValue(OutdoorWorldRuntime::RainIntensityPreset preset)
{
    switch (preset)
    {
        case OutdoorWorldRuntime::RainIntensityPreset::Light:
            return 0.85f;
        case OutdoorWorldRuntime::RainIntensityPreset::Medium:
            return 1.65f;
        case OutdoorWorldRuntime::RainIntensityPreset::Heavy:
            return 3.65f;
        case OutdoorWorldRuntime::RainIntensityPreset::VeryHeavy:
            return 5.35f;
        case OutdoorWorldRuntime::RainIntensityPreset::Off:
        default:
            return 0.0f;
    }
}

const char *rainIntensityPresetName(OutdoorWorldRuntime::RainIntensityPreset preset)
{
    switch (preset)
    {
        case OutdoorWorldRuntime::RainIntensityPreset::Light:
            return "Light";
        case OutdoorWorldRuntime::RainIntensityPreset::Medium:
            return "Medium";
        case OutdoorWorldRuntime::RainIntensityPreset::Heavy:
            return "Heavy";
        case OutdoorWorldRuntime::RainIntensityPreset::VeryHeavy:
            return "Very Heavy";
        case OutdoorWorldRuntime::RainIntensityPreset::Off:
        default:
            return "Off";
    }
}

uint32_t makeTintedFogColor(
    uint8_t brightness,
    bool hasFogTint,
    uint8_t tintRed,
    uint8_t tintGreen,
    uint8_t tintBlue)
{
    if (!hasFogTint)
    {
        return 0xff000000u
            | (static_cast<uint32_t>(brightness) << 16)
            | (static_cast<uint32_t>(brightness) << 8)
            | static_cast<uint32_t>(brightness);
    }

    const uint8_t red =
        static_cast<uint8_t>(std::clamp(std::lround(static_cast<float>(brightness) * tintRed / 255.0f), 0l, 255l));
    const uint8_t green =
        static_cast<uint8_t>(std::clamp(std::lround(static_cast<float>(brightness) * tintGreen / 255.0f), 0l, 255l));
    const uint8_t blue =
        static_cast<uint8_t>(std::clamp(std::lround(static_cast<float>(brightness) * tintBlue / 255.0f), 0l, 255l));
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

bx::Vec3 approximateOutdoorTerrainNormal(const OutdoorMapData &outdoorMapData, float x, float y)
{
    constexpr float SampleOffset = 32.0f;
    const float heightLeft = sampleOutdoorTerrainHeight(outdoorMapData, x - SampleOffset, y);
    const float heightRight = sampleOutdoorTerrainHeight(outdoorMapData, x + SampleOffset, y);
    const float heightDown = sampleOutdoorTerrainHeight(outdoorMapData, x, y - SampleOffset);
    const float heightUp = sampleOutdoorTerrainHeight(outdoorMapData, x, y + SampleOffset);
    const bx::Vec3 normal = {
        heightLeft - heightRight,
        heightDown - heightUp,
        SampleOffset * 2.0f
    };
    const float lengthSquared = normal.x * normal.x + normal.y * normal.y + normal.z * normal.z;

    if (lengthSquared <= 0.0001f)
    {
        return {0.0f, 0.0f, 1.0f};
    }

    const float inverseLength = 1.0f / std::sqrt(lengthSquared);
    return {normal.x * inverseLength, normal.y * inverseLength, normal.z * inverseLength};
}

float worldItemFloorHeight(const OutdoorMapData &outdoorMapData, float x, float y, float z)
{
    const float supportHeight = sampleOutdoorPlacementFloorHeight(outdoorMapData, x, y, z);
    const float renderedTerrainHeight = sampleOutdoorRenderedTerrainHeight(outdoorMapData, x, y);
    return std::max(supportHeight, renderedTerrainHeight) + WorldItemGroundClearance;
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

SkillMastery normalizeEventSkillMastery(uint32_t rawSkillMastery)
{
    if (rawSkillMastery >= static_cast<uint32_t>(SkillMastery::Grandmaster))
    {
        return SkillMastery::Grandmaster;
    }

    return static_cast<SkillMastery>(rawSkillMastery);
}
std::vector<size_t> buildAllPartyMemberIndices(const Party &party)
{
    std::vector<size_t> memberIndices;
    memberIndices.reserve(party.members().size());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        memberIndices.push_back(memberIndex);
    }

    return memberIndices;
}

std::string resolveFallbackSkyTextureName(const MapStatsEntry &map, const std::optional<OutdoorMapData> &outdoorMapData)
{
    if (outdoorMapData && !outdoorMapData->skyTexture.empty())
    {
        return toLowerCopy(outdoorMapData->skyTexture);
    }

    const std::string environmentName = toLowerCopy(map.environmentName);

    if (environmentName == "plains" || environmentName == "forest" || environmentName == "city")
    {
        return "plansky3";
    }

    if (environmentName == "underwater")
    {
        return "sky01";
    }

    return "plansky1";
}

bool isGenericSkySourceTextureName(const std::string &textureName)
{
    if (textureName.empty())
    {
        return true;
    }

    if (textureName.starts_with("plansky"))
    {
        return true;
    }

    return textureName == "sky01"
        || textureName == "sky03"
        || textureName == "sky04"
        || textureName == "sky05"
        || textureName == "sky06"
        || textureName == "cloudsabove";
}

std::string resolveRenderedSkyTextureName(const std::string &sourceSkyTextureName, float minutesOfDay)
{
    const std::string normalizedSourceSkyTextureName = toLowerCopy(sourceSkyTextureName);

    if (!isGenericSkySourceTextureName(normalizedSourceSkyTextureName))
    {
        return normalizedSourceSkyTextureName;
    }

    if (minutesOfDay >= 1200.0f && minutesOfDay < 1260.0f)
    {
        return "sunsetclouds";
    }

    if (minutesOfDay >= 1260.0f || minutesOfDay < 300.0f)
    {
        return "sky6pm";
    }

    if (minutesOfDay >= 300.0f && minutesOfDay < 360.0f)
    {
        return "sunsetclouds";
    }

    if (normalizedSourceSkyTextureName.starts_with("plansky") || normalizedSourceSkyTextureName.empty())
    {
        return "sky05";
    }

    return normalizedSourceSkyTextureName;
}

int monthFromGameMinutes(float gameMinutes)
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(gameMinutes)));
    const int totalDays = totalMinutes / MinutesPerDay;
    return 1 + (totalDays / DaysPerMonth) % 12;
}

int mergedSeasonalWeatherOffset(int month)
{
    if (month < 3)
    {
        return 1;
    }

    if (month < 6)
    {
        return 2;
    }

    if (month < 9)
    {
        return 0;
    }

    return 1;
}

int mergedWeatherStateForProfile(const OutdoorWeatherProfile &profile, float gameMinutes, int mapId)
{
    if (profile.mergedSkyTextureNames.empty())
    {
        return 0;
    }

    const float minutesOfDay = std::fmod(std::max(gameMinutes, 0.0f), static_cast<float>(MinutesPerDay));
    const int hour = static_cast<int>(minutesOfDay / 60.0f);
    int weatherState = (hour > 21 || hour < 5) ? 1 : 0;
    weatherState += mergedSeasonalWeatherOffset(monthFromGameMinutes(gameMinutes));

    const int randomMax = std::max(0, static_cast<int>(profile.mergedSkyTextureNames.size()) - 2);
    const int dayIndex = std::max(0, static_cast<int>(std::floor(gameMinutes / static_cast<float>(MinutesPerDay))));
    uint32_t seed = 0x6d2b79f5u;
    seed ^= static_cast<uint32_t>(std::max(mapId, 0)) * 2246822519u;
    seed ^= static_cast<uint32_t>(dayIndex) * 3266489917u;
    std::mt19937 rng(seed);
    weatherState += std::uniform_int_distribution<int>(0, randomMax)(rng);

    return std::clamp(weatherState, 0, static_cast<int>(profile.mergedSkyTextureNames.size()) - 1);
}

std::string mergedSkyTextureNameForProfile(const OutdoorWeatherProfile &profile, int weatherState)
{
    if (!profile.mergedCustomSkyTextureName.empty())
    {
        return profile.mergedCustomSkyTextureName;
    }

    if (profile.mergedSkyTextureNames.empty())
    {
        return {};
    }

    const int skyIndex = std::clamp(weatherState, 0, static_cast<int>(profile.mergedSkyTextureNames.size()) - 1);
    return profile.mergedSkyTextureNames[static_cast<size_t>(skyIndex)];
}

struct MergedPrecipitationRoll
{
    bool snow = false;
    bool rain = false;
    OutdoorWorldRuntime::RainIntensityPreset rainIntensity = OutdoorWorldRuntime::RainIntensityPreset::Off;
};

OutdoorWorldRuntime::RainIntensityPreset mergedRainIntensityForRoll(int roll)
{
    switch (roll)
    {
        case 0:
            return OutdoorWorldRuntime::RainIntensityPreset::Medium;
        case 1:
            return OutdoorWorldRuntime::RainIntensityPreset::Heavy;
        default:
            return OutdoorWorldRuntime::RainIntensityPreset::VeryHeavy;
    }
}

MergedPrecipitationRoll mergedPrecipitationRoll(
    const OutdoorWeatherProfile &profile,
    int mapId,
    int weatherDayIndex)
{
    uint32_t seed = 0x8f3d9a15u;
    seed ^= static_cast<uint32_t>(std::max(mapId, 0)) * 2246822519u;
    seed ^= static_cast<uint32_t>(std::max(weatherDayIndex, 0)) * 3266489917u;
    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> percentDistribution(0, 99);

    MergedPrecipitationRoll result = {};

    if (profile.mergedSnowEnabled)
    {
        const int snowChance = std::clamp(profile.mergedSnowChancePercent, 0, 100);

        if (percentDistribution(rng) < snowChance)
        {
            result.snow = true;
            return result;
        }
    }

    if (profile.mergedRainEnabled)
    {
        const int rainChance = std::clamp(profile.mergedRainChancePercent, 0, 100);

        if (percentDistribution(rng) < rainChance)
        {
            result.rain = true;
            result.rainIntensity = mergedRainIntensityForRoll(std::uniform_int_distribution<int>(0, 2)(rng));
        }
    }

    return result;
}

OutdoorWorldRuntime::AtmosphereState buildAtmosphereSourceState(
    const MapStatsEntry &map,
    const std::optional<OutdoorMapData> &outdoorMapData,
    const std::optional<MapDeltaData> &outdoorMapDeltaData)
{
    OutdoorWorldRuntime::AtmosphereState result = {};

    if (outdoorMapDeltaData)
    {
        result.sourceSkyTextureName = toLowerCopy(outdoorMapDeltaData->locationTime.skyTextureName);
        result.weatherFlags = outdoorMapDeltaData->locationTime.weatherFlags;
        result.fogWeakDistance = outdoorMapDeltaData->locationTime.fogWeakDistance;
        result.fogStrongDistance = outdoorMapDeltaData->locationTime.fogStrongDistance;
    }

    if (result.sourceSkyTextureName.empty())
    {
        result.sourceSkyTextureName = resolveFallbackSkyTextureName(map, outdoorMapData);
    }

    result.skyTextureName = result.sourceSkyTextureName;

    return result;
}

bool hasConfiguredFogState(const OutdoorWorldRuntime::AtmosphereState &atmosphereState)
{
    return (atmosphereState.weatherFlags & MapWeatherFoggy) != 0
        || atmosphereState.fogWeakDistance != 0
        || atmosphereState.fogStrongDistance != 0;
}

OutdoorFogDistances fallbackFogDistancesForProfile(const OutdoorWeatherProfile &profile)
{
    if (profile.defaultFog.strongDistance > 0)
    {
        return profile.defaultFog;
    }

    if (profile.redFog)
    {
        return profile.denseFog.strongDistance > 0 ? profile.denseFog : OutdoorFogDistances{0, 2048};
    }

    if (profile.underwater)
    {
        return profile.averageFog.strongDistance > 0 ? profile.averageFog : OutdoorFogDistances{0, 4096};
    }

    return profile.averageFog.strongDistance > 0 ? profile.averageFog : OutdoorFogDistances{0, 4096};
}

void applyAlwaysFoggyProfile(
    OutdoorWorldRuntime::AtmosphereState &atmosphereState,
    const OutdoorWeatherProfile &profile)
{
    if (!profile.alwaysFoggy)
    {
        return;
    }

    const OutdoorFogDistances distances = fallbackFogDistancesForProfile(profile);
    atmosphereState.weatherFlags |= MapWeatherFoggy;
    atmosphereState.fogWeakDistance = std::max(distances.weakDistance, 0);
    atmosphereState.fogStrongDistance = std::max(distances.strongDistance, 0);
}

uint32_t underwaterFogColor()
{
    return makeAbgr(UnderwaterFogRed, UnderwaterFogGreen, UnderwaterFogBlue);
}

float normalizedAmbientBrightness(float minutesOfDay)
{
    const float ambient =
        0.15f + (std::sin(((minutesOfDay - 360.0f) * 2.0f * Pi) / 1440.0f) + 1.0f) * 0.27f;
    return std::clamp(ambient, 0.15f, 0.69f);
}

bool readInt32FromBytes(const std::vector<uint8_t> &bytes, size_t offset, int32_t &value)
{
    if (offset + sizeof(value) > bytes.size())
    {
        return false;
    }

    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return true;
}

bool isGoldHeapItemId(uint32_t itemId)
{
    return itemId >= GoldHeapSmallItemId && itemId <= GoldHeapLargeItemId;
}

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
        case OutdoorWorldRuntime::RuntimeSpellSourceKind::Party:
            return "party";
        default:
            return "unknown";
    }
}

const char *projectileSourceKindName(OutdoorWorldRuntime::ProjectileState::SourceKind sourceKind)
{
    switch (sourceKind)
    {
        case OutdoorWorldRuntime::ProjectileState::SourceKind::Actor:
            return "monster";
        case OutdoorWorldRuntime::ProjectileState::SourceKind::Event:
            return "event";
        case OutdoorWorldRuntime::ProjectileState::SourceKind::Party:
            return "party";
        default:
            return "unknown";
    }
}

GameplayProjectileService::ProjectileDefinition buildGameplayProjectileDefinition(
    const OutdoorWorldRuntime::ResolvedProjectileDefinition &definition,
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

OutdoorWorldRuntime::ProjectileState::SourceKind projectileSourceKindFromSpellSource(
    OutdoorWorldRuntime::RuntimeSpellSourceKind sourceKind)
{
    if (sourceKind == OutdoorWorldRuntime::RuntimeSpellSourceKind::Party)
    {
        return OutdoorWorldRuntime::ProjectileState::SourceKind::Party;
    }

    if (sourceKind == OutdoorWorldRuntime::RuntimeSpellSourceKind::Event)
    {
        return OutdoorWorldRuntime::ProjectileState::SourceKind::Event;
    }

    return OutdoorWorldRuntime::ProjectileState::SourceKind::Actor;
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

struct OutdoorProjectileActorProbe
{
    float progress = 0.0f;
    bx::Vec3 closest = {0.0f, 0.0f, 0.0f};
    float horizontalDistanceSquared = 0.0f;
    float collisionZ = 0.0f;
    float minZ = 0.0f;
    float maxZ = 0.0f;
    bool withinHorizontal = false;
    bool withinVertical = false;
};

OutdoorProjectileActorProbe probeOutdoorProjectileActor(
    const bx::Vec3 &segmentStart,
    const bx::Vec3 &segmentEnd,
    const OutdoorWorldRuntime::MapActorState &actor,
    float radius,
    float verticalPadding)
{
    OutdoorProjectileActorProbe probe = {};
    probe.horizontalDistanceSquared =
        pointSegmentDistanceSquared2d(
            actor.preciseX,
            actor.preciseY,
            segmentStart.x,
            segmentStart.y,
            segmentEnd.x,
            segmentEnd.y,
            probe.progress);
    probe.closest = {
        segmentStart.x + (segmentEnd.x - segmentStart.x) * probe.progress,
        segmentStart.y + (segmentEnd.y - segmentStart.y) * probe.progress,
        segmentStart.z + (segmentEnd.z - segmentStart.z) * probe.progress
    };
    probe.collisionZ = probe.closest.z;
    probe.minZ = actor.preciseZ - verticalPadding;
    probe.maxZ = actor.preciseZ + static_cast<float>(actor.height) + verticalPadding;
    probe.withinHorizontal = probe.horizontalDistanceSquared <= radius * radius;
    probe.withinVertical = probe.collisionZ >= probe.minZ && probe.collisionZ <= probe.maxZ;
    return probe;
}

bool outdoorProjectileActorProbeIsTraceWorthy(const OutdoorProjectileActorProbe &probe, float radius)
{
    const float expandedRadius = radius + 192.0f;
    return probe.horizontalDistanceSquared <= expandedRadius * expandedRadius
        && probe.collisionZ >= probe.minZ - 512.0f
        && probe.collisionZ <= probe.maxZ + 512.0f;
}

const char *outdoorProjectileTraceCollisionKindName(OutdoorWorldRuntime::ProjectileCollisionKind kind)
{
    switch (kind)
    {
        case OutdoorWorldRuntime::ProjectileCollisionKind::None: return "none";
        case OutdoorWorldRuntime::ProjectileCollisionKind::Party: return "party";
        case OutdoorWorldRuntime::ProjectileCollisionKind::Actor: return "actor";
        case OutdoorWorldRuntime::ProjectileCollisionKind::BModel: return "bmodel";
        case OutdoorWorldRuntime::ProjectileCollisionKind::Terrain: return "terrain";
    }

    return "unknown";
}

void traceOutdoorBlasterProjectileActorProbe(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const bx::Vec3 &segmentStart,
    const bx::Vec3 &segmentEnd,
    size_t actorIndex,
    const OutdoorWorldRuntime::MapActorState &actor,
    const char *pDecision,
    const OutdoorProjectileActorProbe &probe,
    float hitRadius,
    const OutdoorWorldRuntime::ProjectileCollisionFacts &bestCollision)
{
    std::ostringstream out;
    out
        << "blaster_projectile_actor_probe scene=outdoor"
        << " projectile=" << projectile.projectileId
        << " object_id=" << projectile.objectDescriptionId
        << " object=\"" << projectile.objectName << "\""
        << " sprite=\"" << projectile.objectSpriteName << "\""
        << " actor_index=" << actorIndex
        << " actor_id=" << actor.actorId
        << " monster_id=" << actor.monsterId
        << " decision=" << pDecision
        << " start=(" << segmentStart.x << "," << segmentStart.y << "," << segmentStart.z << ")"
        << " end=(" << segmentEnd.x << "," << segmentEnd.y << "," << segmentEnd.z << ")"
        << " closest=(" << probe.closest.x << "," << probe.closest.y << "," << probe.closest.z << ")"
        << " progress=" << probe.progress
        << " horizontal_distance=" << std::sqrt(probe.horizontalDistanceSquared)
        << " collision_z=" << probe.collisionZ
        << " actor_min_z=" << probe.minZ
        << " actor_max_z=" << probe.maxZ
        << " hit_radius=" << hitRadius
        << " within_horizontal=" << (probe.withinHorizontal ? 1 : 0)
        << " within_vertical=" << (probe.withinVertical ? 1 : 0);

    if (bestCollision.hit)
    {
        out
            << " current_best_kind=" << outdoorProjectileTraceCollisionKindName(bestCollision.kind)
            << " current_best_factor=" << bestCollision.factor
            << " current_best_actor=" << bestCollision.actorIndex
            << " current_best_face=" << bestCollision.faceIndex
            << " current_best_collider=\"" << bestCollision.colliderName << "\"";
    }
    else
    {
        out << " current_best_kind=none";
    }

    writeBlasterProjectileTrace(out.str());
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

uint32_t inactiveActorDecisionSeed(uint32_t actorId, uint32_t counter, uint32_t salt)
{
    return static_cast<uint32_t>(actorId + 1) * 1103515245u
        + counter * 2654435761u
        + salt;
}

float turnBasedActorStandSeconds(uint32_t decisionSeed)
{
    constexpr uint32_t Resolution = 1000u;
    const float spanSeconds = TurnBasedActorStandMaxSeconds - TurnBasedActorStandMinSeconds;
    return TurnBasedActorStandMinSeconds
        + spanSeconds * static_cast<float>(decisionSeed % (Resolution + 1u)) / static_cast<float>(Resolution);
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

bool isWithinRange3d(float x, float y, float z, float range)
{
    return range > 0.0f && lengthSquared3d(x, y, z) <= range * range;
}

bool isOutdoorLandMaskWater(const std::optional<std::vector<uint8_t>> &outdoorLandMask, float x, float y)
{
    if (!outdoorLandMask || outdoorLandMask->empty())
    {
        return false;
    }

    const float gridX = outdoorWorldToGridXFloat(x);
    const float gridY = outdoorWorldToGridYFloat(y);
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
    return pStats != nullptr && pStats->hasKind(MonsterKind::Swimmer);
}

bx::Vec3 outdoorTerrainTileCenter(int tileX, int tileY)
{
    return {
        outdoorGridCornerWorldX(tileX) + static_cast<float>(OutdoorMapData::TerrainTileSize) * 0.5f,
        outdoorGridCornerWorldY(tileY) - static_cast<float>(OutdoorMapData::TerrainTileSize) * 0.5f,
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
    return isMonsterProjectileSpellName(spellName);
}

bool outdoorMonsterSelfBuffSpellName(const std::string &spellName)
{
    return isMonsterSelfActionSpellName(spellName);
}

bool outdoorMonsterSpellCastSupported(const std::string &spellName)
{
    return isProjectileSpellName(spellName)
        || toLowerCopy(spellName) == "meteor shower"
        || toLowerCopy(spellName) == "starburst"
        || outdoorMonsterSelfBuffSpellName(spellName);
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
        definition.objectFlags = pObjectEntry->flags;
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
    definition.objectFlags = pObjectEntry->flags;
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
    definition.objectFlags = pObjectEntry->flags;
    definition.radius = static_cast<uint16_t>(std::max<int>(pObjectEntry->radius, 16));
    definition.height = static_cast<uint16_t>(std::max<int>(pObjectEntry->height, 16));
    definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pObjectEntry->lifetimeTicks, 64));
    definition.speed = static_cast<float>(std::max<int>(pObjectEntry->speed, 2000));
    definition.spellId = spell.id;
    definition.effectSoundId = spell.effectSoundId;
    definition.objectName = pObjectEntry->internalName;
    definition.objectSpriteName = pObjectEntry->spriteName;
    const SpellId resolvedSpellId = spellIdFromValue(std::max(spell.id, 0));

    if (resolvedSpellId == SpellId::Sparks)
    {
        definition.objectFlags |= ObjectDescBounce;
    }
    else if (resolvedSpellId == SpellId::RockBlast)
    {
        definition.objectFlags |= ObjectDescBounce;
        definition.objectFlags &= ~ObjectDescNoGravity;
    }

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

bool resolveObjectProjectileDefinition(
    int objectId,
    int impactObjectId,
    const ObjectTable &objectTable,
    OutdoorWorldRuntime::ResolvedProjectileDefinition &definition)
{
    definition = {};

    if (objectId <= 0)
    {
        return false;
    }

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

    if (impactObjectId > 0)
    {
        const ObjectEntry *pImpactEntry = objectTable.findByObjectId(static_cast<int16_t>(impactObjectId));
        const std::optional<uint16_t> impactDescriptionId =
            objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(impactObjectId));

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

float minutesToSeconds(float minutes)
{
    return minutes * 60.0f;
}

float hoursToSeconds(float hours)
{
    return hours * 3600.0f;
}

GameplayProjectileService::ProjectilePartyImpactDamageInput buildProjectilePartyImpactDamageInput(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const MonsterTable *pMonsterTable,
    const SpellTable *pSpellTable,
    const std::vector<OutdoorWorldRuntime::MapActorState> &mapActors)
{
    GameplayProjectileService::ProjectilePartyImpactDamageInput input = {};
    input.sourceKind = projectile.sourceKind;
    input.eventSource = projectile.sourceId == EventSpellSourceId;
    input.projectileDamage = projectile.damage;
    input.spellId = projectile.spellId;
    input.skillLevel = projectile.skillLevel;
    input.monsterAbility = projectile.ability;

    if (projectile.sourceKind == OutdoorWorldRuntime::ProjectileState::SourceKind::Party)
    {
        return input;
    }

    if (pMonsterTable == nullptr)
    {
        return input;
    }

    const MonsterTable::MonsterStatsEntry *pStats = nullptr;

    if (projectile.sourceMonsterId != 0)
    {
        pStats = pMonsterTable->findStatsById(projectile.sourceMonsterId);
    }
    else
    {
        for (const OutdoorWorldRuntime::MapActorState &actor : mapActors)
        {
            if (actor.actorId != projectile.sourceId)
            {
                continue;
            }

            pStats = pMonsterTable->findStatsById(actor.monsterId);
            break;
        }
    }

    if (pStats == nullptr)
    {
        return input;
    }

    input.hasMonsterFacts = true;
    input.monsterLevel = pStats->level;
    input.attack1Damage.diceRolls = pStats->attack1Damage.diceRolls;
    input.attack1Damage.diceSides = pStats->attack1Damage.diceSides;
    input.attack1Damage.bonus = pStats->attack1Damage.bonus;
    input.attack2Damage.diceRolls = pStats->attack2Damage.diceRolls;
    input.attack2Damage.diceSides = pStats->attack2Damage.diceSides;
    input.attack2Damage.bonus = pStats->attack2Damage.bonus;

    if (pSpellTable != nullptr)
    {
        if (const SpellEntry *pSpellEntry = pSpellTable->findByName(pStats->spell1Name))
        {
            input.spell1Damage.baseDamage = pSpellEntry->damageBase;
            input.spell1Damage.diceSides = pSpellEntry->damageDiceSides;
            input.spell1Damage.skillLevel = pStats->spell1SkillLevel;
            input.spell1Damage.skillMastery = pStats->spell1SkillMastery;
        }

        if (const SpellEntry *pSpellEntry = pSpellTable->findByName(pStats->spell2Name))
        {
            input.spell2Damage.baseDamage = pSpellEntry->damageBase;
            input.spell2Damage.diceSides = pSpellEntry->damageDiceSides;
            input.spell2Damage.skillLevel = pStats->spell2SkillLevel;
            input.spell2Damage.skillMastery = pStats->spell2SkillMastery;
        }
    }

    return input;
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

    const OutdoorSupportFloorSample supportFloor = sampleOutdoorSupportFloor(
        *pOutdoorMapData,
        x,
        y,
        currentZ,
        5.0f,
        std::max(5.0f, static_cast<float>(radius)));
    const float terrainFloorZ = sampleOutdoorRenderedTerrainHeight(*pOutdoorMapData, x, y);
    float floorZ = terrainFloorZ;

    if (supportFloor.fromBModel && currentZ + CollisionEpsilon >= supportFloor.height)
    {
        floorZ = std::max(floorZ, supportFloor.height);
    }

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

void applyResolvedActorHorizontalVelocity(
    OutdoorWorldRuntime::MapActorState &actor,
    const bx::Vec3 &resolvedVelocity,
    bool updateMoveDirection)
{
    actor.velocityX = resolvedVelocity.x;
    actor.velocityY = resolvedVelocity.y;

    if (!updateMoveDirection)
    {
        return;
    }

    const float horizontalSpeed = length2d(resolvedVelocity.x, resolvedVelocity.y);

    if (horizontalSpeed <= CollisionEpsilon)
    {
        return;
    }

    actor.moveDirectionX = resolvedVelocity.x / horizontalSpeed;
    actor.moveDirectionY = resolvedVelocity.y / horizontalSpeed;
    actor.yawRadians = std::atan2(actor.moveDirectionY, actor.moveDirectionX);
}

bool outdoorFaceBlocksMovement(const OutdoorFaceGeometryData &face)
{
    return !hasFaceAttribute(face.attributes, FaceAttribute::Untouchable);
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
        const float terrainHeight = sampleOutdoorRenderedTerrainHeight(outdoorMapData, candidateX, candidateY);

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
        if (!outdoorFaceBlocksMovement(face) || face.isWalkable)
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

void applyOeOutdoorSteepSlopeResponse(
    OutdoorWorldRuntime::MapActorState &actor,
    const OutdoorMapData &outdoorMapData,
    const MonsterTable::MonsterStatsEntry *pStats)
{
    if (pStats == nullptr || pStats->canFly)
    {
        return;
    }

    const float terrainFloorZ = sampleOutdoorRenderedTerrainHeight(
        outdoorMapData,
        actor.preciseX,
        actor.preciseY);

    if (actor.preciseZ > terrainFloorZ + GroundSnapHeight + 2.0f)
    {
        return;
    }

    if (!outdoorTerrainSlopeTooHigh(outdoorMapData, actor.preciseX, actor.preciseY))
    {
        return;
    }

    actor.preciseZ = terrainFloorZ;

    const bx::Vec3 terrainNormal = approximateOutdoorTerrainNormal(
        outdoorMapData,
        actor.preciseX,
        actor.preciseY);
    const bx::Vec3 actorVelocity = {actor.velocityX, actor.velocityY, actor.velocityZ};
    const float slopeResponse = std::abs(
        actorVelocity.x * terrainNormal.x
        + actorVelocity.y * terrainNormal.y
        + actorVelocity.z * terrainNormal.z) * 2.0f;

    actor.velocityX += slopeResponse * terrainNormal.x;
    actor.velocityY += slopeResponse * terrainNormal.y;
    actor.yawRadians -= OeTurnAwayFromWaterAngleRadians;
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
    const std::optional<ScriptedEventProgram> &program,
    std::vector<OutdoorWorldRuntime::TimerState> &timers
)
{
    if (!program)
    {
        return;
    }

    for (const ScriptedEventProgram::TimerTrigger &trigger : program->timerTriggers())
    {
        OutdoorWorldRuntime::TimerState timer = {};
        timer.eventId = trigger.eventId;
        timer.repeating = trigger.repeating;
        timer.targetHour = trigger.targetHour;
        timer.intervalGameMinutes = trigger.intervalGameMinutes;
        timer.remainingGameMinutes = trigger.remainingGameMinutes;
        timers.push_back(std::move(timer));
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

GameplayActorAiType gameplayActorAiTypeFromMonster(MonsterTable::MonsterAiType aiType);
float wanderRadiusForMovementType(MonsterTable::MonsterMovementType movementType);

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

void populateOutdoorActorStaticCombatFacts(
    OutdoorWorldRuntime::MapActorState &state,
    const MonsterTable::MonsterStatsEntry *pStats,
    const SpellTable *pSpellTable)
{
    if (pStats == nullptr)
    {
        return;
    }

    state.aiType = gameplayActorAiTypeFromMonster(pStats->aiType);
    state.canFly = pStats->canFly;
    state.attack1DamageType = GameMechanics::parseCombatDamageType(pStats->attack1Type);
    state.attack2DamageType = GameMechanics::parseCombatDamageType(pStats->attack2Type);
    state.spell1CastSupported = outdoorMonsterSpellCastSupported(pStats->spell1Name);
    state.spell2CastSupported = outdoorMonsterSpellCastSupported(pStats->spell2Name);
    state.wanderRadius = wanderRadiusForMovementType(pStats->movementType);

    if (pSpellTable != nullptr)
    {
        if (const SpellEntry *pSpellEntry = pSpellTable->findByName(pStats->spell1Name))
        {
            state.spell1Id = static_cast<uint32_t>(std::max(pSpellEntry->id, 0));
            state.spell1DamageType = GameMechanics::spellCombatDamageType(state.spell1Id, pSpellTable);
        }

        if (const SpellEntry *pSpellEntry = pSpellTable->findByName(pStats->spell2Name))
        {
            state.spell2Id = static_cast<uint32_t>(std::max(pSpellEntry->id, 0));
            state.spell2DamageType = GameMechanics::spellCombatDamageType(state.spell2Id, pSpellTable);
        }
    }
}

void applyOutdoorBolsterAbilityOverrides(
    OutdoorWorldRuntime::MapActorState &state,
    const GameplayMonsterBolsterResult &bolster,
    const SpellTable *pSpellTable)
{
    state.generatedAttack2 = bolster.generatedAttack2;
    state.generatedAttack2IsRanged = bolster.generatedAttack2IsRanged;
    state.copyAttack1DamageToAttack2 = bolster.copyAttack1DamageToAttack2;
    state.generatedAttack2MissileType = bolster.generatedAttack2MissileType;
    state.generatedAttack2Chance = bolster.generatedAttack2Chance;
    state.generatedSpell1UseChance = bolster.generatedSpell1UseChance;
    state.generatedSpell2UseChance = bolster.generatedSpell2UseChance;

    if (pSpellTable != nullptr && bolster.generatedSpell1Id != 0)
    {
        if (const SpellEntry *pSpellEntry = pSpellTable->findById(static_cast<int>(bolster.generatedSpell1Id)))
        {
            state.spell1Id = static_cast<uint32_t>(std::max(pSpellEntry->id, 0));
            state.spell1DamageType = GameMechanics::spellCombatDamageType(state.spell1Id, pSpellTable);
            state.spell1CastSupported = outdoorMonsterSpellCastSupported(pSpellEntry->name);
        }
    }

    if (pSpellTable != nullptr && bolster.generatedSpell2Id != 0)
    {
        if (const SpellEntry *pSpellEntry = pSpellTable->findById(static_cast<int>(bolster.generatedSpell2Id)))
        {
            state.spell2Id = static_cast<uint32_t>(std::max(pSpellEntry->id, 0));
            state.spell2DamageType = GameMechanics::spellCombatDamageType(state.spell2Id, pSpellTable);
            state.spell2CastSupported = outdoorMonsterSpellCastSupported(pSpellEntry->name);
        }
    }
}

OutdoorWorldRuntime::MapActorState buildMapActorState(
    const MonsterTable &monsterTable,
    const SpellTable *pSpellTable,
    const MapDeltaActor &actor,
    uint32_t actorId,
    const OutdoorMapData * /*pOutdoorMapData*/,
    float attackAnimationSeconds,
    const GameplayBolsterRuntimeContext &bolsterContext
)
{
    OutdoorWorldRuntime::MapActorState state = {};
    state.actorId = actorId;
    state.monsterId = resolveMapActorMonsterId(actor);
    state.npcId = actor.npcId;
    state.uniqueNameId = static_cast<uint32_t>(std::max(0, actor.uniqueNameIndex));
    state.group = actor.group;
    state.ally = actor.ally;
    state.specialItemId = actor.carriedItemId;

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(state.monsterId);
    const MonsterEntry *pMonsterEntry = resolveMonsterEntry(monsterTable, state.monsterId, pStats);
    const GameplayMonsterBolsterResult bolster =
        pStats != nullptr ? resolveGameplayMonsterBolster(bolsterContext, *pStats, pMonsterEntry)
                          : GameplayMonsterBolsterResult {};
    const int baseMaxHp = pStats != nullptr ? pStats->hitPoints : std::max(0, static_cast<int>(actor.hp));
    state.displayName = resolveMapDeltaActorName(monsterTable, actor);
    state.maxHp = pStats != nullptr ? bolster.maxHp : std::max(0, static_cast<int>(actor.hp));
    state.currentHp = actor.hp > 0 && actor.hp > baseMaxHp ? actor.hp : state.maxHp;
    state.bolsterRewardMultiplier = pStats != nullptr
        ? std::max(
            std::max(1.0f, actor.bolsterRewardMultiplier),
            gameplayBolsterRewardMultiplier(pStats->hitPoints, state.maxHp, bolster.statsEnabled))
        : 1.0f;
    state.x = actor.x;
    state.y = actor.y;
    state.z = actor.z;
    state.preciseX = static_cast<float>(actor.x);
    state.preciseY = static_cast<float>(actor.y);
    state.preciseZ = static_cast<float>(actor.z);
    state.homeX = actor.x;
    state.homeY = actor.y;
    state.homeZ = actor.z;
    state.homePreciseX = static_cast<float>(actor.x);
    state.homePreciseY = static_cast<float>(actor.y);
    state.homePreciseZ = static_cast<float>(actor.z);
    state.radius = actor.radius;
    state.height = actor.height;
    state.moveSpeed = static_cast<uint16_t>(pStats != nullptr ? bolster.moveSpeed : 0);
    state.armorClass = pStats != nullptr ? bolster.armorClass : 0;
    state.immobile = pStats != nullptr && bolster.immobile;
    state.attack1DamageDiceRolls = pStats != nullptr ? bolster.attack1DamageDiceRolls : 0;
    state.attack1DamageDiceSides = pStats != nullptr ? bolster.attack1DamageDiceSides : 0;
    state.attack1DamageBonus = pStats != nullptr ? bolster.attack1DamageBonus : 0;
    state.attack2DamageDiceRolls = pStats != nullptr ? bolster.attack2DamageDiceRolls : 0;
    state.attack2DamageDiceSides = pStats != nullptr ? bolster.attack2DamageDiceSides : 0;
    state.attack2DamageBonus = pStats != nullptr ? bolster.attack2DamageBonus : 0;
    state.spell1SkillLevel = pStats != nullptr ? bolster.spell1SkillLevel : 0;
    state.spell1SkillMastery = pStats != nullptr ? bolster.spell1SkillMastery : SkillMastery::None;
    state.spell2SkillLevel = pStats != nullptr ? bolster.spell2SkillLevel : 0;
    state.spell2SkillMastery = pStats != nullptr ? bolster.spell2SkillMastery : SkillMastery::None;
    populateOutdoorActorStaticCombatFacts(state, pStats, pSpellTable);
    applyOutdoorBolsterAbilityOverrides(state, bolster, pSpellTable);
    GameplayActorService actorService = {};
    const int16_t relationMonsterId = actorService.relationMonsterId(state.monsterId, state.ally);
    state.hostileToParty =
        (actor.attributes & ActorAggressorBit) != 0 || monsterTable.isHostileToParty(relationMonsterId);
    state.hostilityType = actor.hostilityType;

    if (state.hostilityType == 0 && state.hostileToParty && pStats != nullptr)
    {
        state.hostilityType = static_cast<uint8_t>(pStats->hostility);
    }

    state.isInvisible = (actor.attributes & ActorInvisibleBit) != 0;
    state.alertStatusBit = (actor.attributes & ActorAlertStatusBit) != 0;
    state.animation = actor.hp <= 0 ? OutdoorWorldRuntime::ActorAnimation::Dead
        : static_cast<OutdoorWorldRuntime::ActorAnimation>(std::clamp<int>(actor.currentActionAnimation, 0, 7));
    state.aiState = actor.hp <= 0 ? OutdoorWorldRuntime::ActorAiState::Dead : OutdoorWorldRuntime::ActorAiState::Standing;
    state.recoverySeconds = monsterRecoverySeconds(pStats != nullptr ? pStats->recovery : 100);
    state.attackAnimationSeconds = std::max(0.1f, attackAnimationSeconds);
    state.attackCooldownSeconds = actorService.initialAttackCooldownSeconds(actorId, state.recoverySeconds);
    state.idleDecisionSeconds = actorService.initialIdleDecisionSeconds(actorId);

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
    GameplayActorService actorService = {};
    return actorService.isActorUnavailableForCombat(
        actor.isInvisible,
        actor.isDead,
        actor.currentHp <= 0,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Dying,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead);
}

std::vector<bool> selectOutdoorActiveActorMask(
    const std::vector<OutdoorActiveActorCandidate> &candidates,
    size_t actorCount,
    size_t maxActiveActors,
    float activeRange)
{
    std::vector<bool> activeActorMask(actorCount, false);

    if (actorCount == 0 || maxActiveActors == 0)
    {
        return activeActorMask;
    }

    std::vector<std::pair<size_t, float>> activeActorDistances;
    activeActorDistances.reserve(candidates.size());

    for (const OutdoorActiveActorCandidate &candidate : candidates)
    {
        if (!candidate.eligible || candidate.actorIndex >= actorCount)
        {
            continue;
        }

        if (candidate.distanceToParty <= activeRange)
        {
            activeActorDistances.push_back({candidate.actorIndex, candidate.distanceToParty});
        }
    }

    std::stable_sort(
        activeActorDistances.begin(),
        activeActorDistances.end(),
        [](const std::pair<size_t, float> &left, const std::pair<size_t, float> &right)
        {
            return left.second < right.second;
        });

    for (size_t index = 0; index < activeActorDistances.size() && index < maxActiveActors; ++index)
    {
        activeActorMask[activeActorDistances[index].first] = true;
    }

    return activeActorMask;
}

bool canEnterHitReaction(const OutdoorWorldRuntime::MapActorState &actor)
{
    GameplayActorService actorService = {};
    return actorService.canActorEnterHitReaction(
        actor.isInvisible,
        actor.isDead,
        actor.currentHp <= 0,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Dying,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Stunned,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Attacking);
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
    if (!actor.movementStateInitialized || !actor.movementState.airborne)
    {
        actor.velocityZ = 0.0f;
    }
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
    actor.stunRemainingSeconds = 0.0f;
    actor.paralyzeRemainingSeconds = 0.0f;
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

bool monsterEntryHasCorpseSprite(const MonsterEntry *pMonsterEntry)
{
    const size_t actionIndex = static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::Dead);

    if (pMonsterEntry == nullptr || actionIndex >= pMonsterEntry->spriteNames.size())
    {
        return false;
    }

    const std::string spriteName = toLowerCopy(pMonsterEntry->spriteNames[actionIndex]);
    return !spriteName.empty() && spriteName != "null";
}

bool monsterStatsLeavesNoCorpse(const MonsterTable::MonsterStatsEntry *pStats)
{
    if (pStats == nullptr)
    {
        return false;
    }

    return pStats->hasKind(MonsterKind::NoCorpse);
}

bool actorShouldLeaveCorpse(const MonsterTable *pMonsterTable, const OutdoorWorldRuntime::MapActorState &actor)
{
    if (pMonsterTable == nullptr)
    {
        return true;
    }

    const MonsterTable::MonsterStatsEntry *pStats = pMonsterTable->findStatsById(actor.monsterId);

    if (monsterStatsLeavesNoCorpse(pStats))
    {
        return false;
    }

    return monsterEntryHasCorpseSprite(resolveMonsterEntry(*pMonsterTable, actor.monsterId, pStats));
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

void applyImmediateSpellVisualFallback(
    SpellId spellId,
    uint16_t &spriteId,
    std::string &spriteName)
{
    switch (spellId)
    {
        case SpellId::Slow:
            spriteId = 714;
            spriteName = "spell41";
            break;

        case SpellId::Paralyze:
            spriteId = 786;
            spriteName = "spell84";
            break;

        case SpellId::MassFear:
        case SpellId::Fear:
            spriteId = 722;
            spriteName = "spell57";
            break;

        default:
            break;
    }
}

GameplayActorControlMode gameplayActorControlModeFromOutdoor(OutdoorWorldRuntime::ActorControlMode mode)
{
    switch (mode)
    {
        case OutdoorWorldRuntime::ActorControlMode::Charm:
            return GameplayActorControlMode::Charm;

        case OutdoorWorldRuntime::ActorControlMode::Berserk:
            return GameplayActorControlMode::Berserk;

        case OutdoorWorldRuntime::ActorControlMode::Enslaved:
            return GameplayActorControlMode::Enslaved;

        case OutdoorWorldRuntime::ActorControlMode::ControlUndead:
            return GameplayActorControlMode::ControlUndead;

        case OutdoorWorldRuntime::ActorControlMode::Reanimated:
            return GameplayActorControlMode::Reanimated;

        case OutdoorWorldRuntime::ActorControlMode::None:
        default:
            return GameplayActorControlMode::None;
    }
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

enum class OutdoorTargetKind : uint8_t
{
    None = 0,
    Party = 1,
    Actor = 2,
};

ActorAiTargetKind actorAiTargetKindFromOutdoorTarget(OutdoorTargetKind kind)
{
    switch (kind)
    {
        case OutdoorTargetKind::Party:
            return ActorAiTargetKind::Party;

        case OutdoorTargetKind::Actor:
            return ActorAiTargetKind::Actor;

        case OutdoorTargetKind::None:
        default:
            return ActorAiTargetKind::None;
    }
}

ActorAiMotionState actorAiMotionStateFromOutdoor(OutdoorWorldRuntime::ActorAiState state)
{
    switch (state)
    {
        case OutdoorWorldRuntime::ActorAiState::Wandering:
            return ActorAiMotionState::Wandering;

        case OutdoorWorldRuntime::ActorAiState::Pursuing:
            return ActorAiMotionState::Pursuing;

        case OutdoorWorldRuntime::ActorAiState::Fleeing:
            return ActorAiMotionState::Fleeing;

        case OutdoorWorldRuntime::ActorAiState::Stunned:
            return ActorAiMotionState::Stunned;

        case OutdoorWorldRuntime::ActorAiState::Attacking:
            return ActorAiMotionState::Attacking;

        case OutdoorWorldRuntime::ActorAiState::Dying:
            return ActorAiMotionState::Dying;

        case OutdoorWorldRuntime::ActorAiState::Dead:
            return ActorAiMotionState::Dead;

        case OutdoorWorldRuntime::ActorAiState::Standing:
        default:
            return ActorAiMotionState::Standing;
    }
}

ActorAiAnimationState actorAiAnimationStateFromOutdoor(OutdoorWorldRuntime::ActorAnimation animation)
{
    switch (animation)
    {
        case OutdoorWorldRuntime::ActorAnimation::Walking:
            return ActorAiAnimationState::Walking;

        case OutdoorWorldRuntime::ActorAnimation::AttackMelee:
            return ActorAiAnimationState::AttackMelee;

        case OutdoorWorldRuntime::ActorAnimation::AttackRanged:
            return ActorAiAnimationState::AttackRanged;

        case OutdoorWorldRuntime::ActorAnimation::GotHit:
            return ActorAiAnimationState::GotHit;

        case OutdoorWorldRuntime::ActorAnimation::Dying:
            return ActorAiAnimationState::Dying;

        case OutdoorWorldRuntime::ActorAnimation::Dead:
            return ActorAiAnimationState::Dead;

        case OutdoorWorldRuntime::ActorAnimation::Bored:
            return ActorAiAnimationState::Bored;

        case OutdoorWorldRuntime::ActorAnimation::Standing:
        default:
            return ActorAiAnimationState::Standing;
    }
}

OutdoorWorldRuntime::ActorAiState outdoorActorAiStateFromGameplay(ActorAiMotionState state)
{
    switch (state)
    {
        case ActorAiMotionState::Wandering:
            return OutdoorWorldRuntime::ActorAiState::Wandering;

        case ActorAiMotionState::Pursuing:
            return OutdoorWorldRuntime::ActorAiState::Pursuing;

        case ActorAiMotionState::Fleeing:
            return OutdoorWorldRuntime::ActorAiState::Fleeing;

        case ActorAiMotionState::Stunned:
            return OutdoorWorldRuntime::ActorAiState::Stunned;

        case ActorAiMotionState::Attacking:
            return OutdoorWorldRuntime::ActorAiState::Attacking;

        case ActorAiMotionState::Dying:
            return OutdoorWorldRuntime::ActorAiState::Dying;

        case ActorAiMotionState::Dead:
            return OutdoorWorldRuntime::ActorAiState::Dead;

        case ActorAiMotionState::Standing:
        default:
            return OutdoorWorldRuntime::ActorAiState::Standing;
    }
}

OutdoorWorldRuntime::ActorAnimation outdoorActorAnimationFromGameplay(ActorAiAnimationState animation)
{
    switch (animation)
    {
        case ActorAiAnimationState::Walking:
            return OutdoorWorldRuntime::ActorAnimation::Walking;

        case ActorAiAnimationState::AttackMelee:
            return OutdoorWorldRuntime::ActorAnimation::AttackMelee;

        case ActorAiAnimationState::AttackRanged:
            return OutdoorWorldRuntime::ActorAnimation::AttackRanged;

        case ActorAiAnimationState::GotHit:
            return OutdoorWorldRuntime::ActorAnimation::GotHit;

        case ActorAiAnimationState::Dying:
            return OutdoorWorldRuntime::ActorAnimation::Dying;

        case ActorAiAnimationState::Dead:
            return OutdoorWorldRuntime::ActorAnimation::Dead;

        case ActorAiAnimationState::Bored:
            return OutdoorWorldRuntime::ActorAnimation::Bored;

        case ActorAiAnimationState::Standing:
        default:
            return OutdoorWorldRuntime::ActorAnimation::Standing;
    }
}

bool outdoorActorIsPartyControlled(OutdoorWorldRuntime::ActorControlMode mode)
{
    switch (mode)
    {
        case OutdoorWorldRuntime::ActorControlMode::Charm:
        case OutdoorWorldRuntime::ActorControlMode::Enslaved:
        case OutdoorWorldRuntime::ActorControlMode::ControlUndead:
        case OutdoorWorldRuntime::ActorControlMode::Reanimated:
            return true;

        default:
            return false;
    }
}

GameplayActorTargetPolicyState buildGameplayActorTargetPolicyState(const OutdoorWorldRuntime::MapActorState &actor)
{
    GameplayActorTargetPolicyState state = {};
    state.monsterId = actor.monsterId;
    GameplayActorService actorService = {};
    state.relationMonsterId = actorService.relationMonsterId(actor.monsterId, actor.ally);
    state.group = actor.group;
    state.preciseZ = actor.preciseZ;
    state.height = actor.height;
    state.controlMode = gameplayActorControlModeFromOutdoor(actor.controlMode);
    state.hostileToParty = actor.hostileToParty && !outdoorActorIsPartyControlled(actor.controlMode);
    return state;
}

OutdoorWorldRuntime::MonsterAttackAbility outdoorAttackAbilityFromGameplay(GameplayActorAttackAbility ability)
{
    switch (ability)
    {
        case GameplayActorAttackAbility::Attack2:
            return OutdoorWorldRuntime::MonsterAttackAbility::Attack2;

        case GameplayActorAttackAbility::Spell1:
            return OutdoorWorldRuntime::MonsterAttackAbility::Spell1;

        case GameplayActorAttackAbility::Spell2:
            return OutdoorWorldRuntime::MonsterAttackAbility::Spell2;

        case GameplayActorAttackAbility::Attack1:
        default:
            return OutdoorWorldRuntime::MonsterAttackAbility::Attack1;
    }
}

GameplayActorAttackAbility gameplayAttackAbilityFromOutdoor(OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    switch (ability)
    {
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack2:
            return GameplayActorAttackAbility::Attack2;

        case OutdoorWorldRuntime::MonsterAttackAbility::Spell1:
            return GameplayActorAttackAbility::Spell1;

        case OutdoorWorldRuntime::MonsterAttackAbility::Spell2:
            return GameplayActorAttackAbility::Spell2;

        case OutdoorWorldRuntime::MonsterAttackAbility::Attack1:
        default:
            return GameplayActorAttackAbility::Attack1;
    }
}

OutdoorWorldRuntime::ActorControlMode outdoorActorControlModeFromGameplay(GameplayActorControlMode mode)
{
    switch (mode)
    {
        case GameplayActorControlMode::Charm:
            return OutdoorWorldRuntime::ActorControlMode::Charm;

        case GameplayActorControlMode::Berserk:
            return OutdoorWorldRuntime::ActorControlMode::Berserk;

        case GameplayActorControlMode::Enslaved:
            return OutdoorWorldRuntime::ActorControlMode::Enslaved;

        case GameplayActorControlMode::ControlUndead:
            return OutdoorWorldRuntime::ActorControlMode::ControlUndead;

        case GameplayActorControlMode::Reanimated:
            return OutdoorWorldRuntime::ActorControlMode::Reanimated;

        case GameplayActorControlMode::None:
        default:
            return OutdoorWorldRuntime::ActorControlMode::None;
    }
}

GameplayActorSpellEffectState buildGameplayActorSpellEffectState(const OutdoorWorldRuntime::MapActorState &actor)
{
    GameplayActorSpellEffectState state = {};
    state.slowRemainingSeconds = actor.slowRemainingSeconds;
    state.slowMoveMultiplier = actor.slowMoveMultiplier;
    state.slowRecoveryMultiplier = actor.slowRecoveryMultiplier;
    state.stunRemainingSeconds = actor.stunRemainingSeconds;
    state.paralyzeRemainingSeconds = actor.paralyzeRemainingSeconds;
    state.fearRemainingSeconds = actor.fearRemainingSeconds;
    state.blindRemainingSeconds = actor.blindRemainingSeconds;
    state.controlRemainingSeconds = actor.controlRemainingSeconds;
    state.controlMode = gameplayActorControlModeFromOutdoor(actor.controlMode);
    state.shrinkRemainingSeconds = actor.shrinkRemainingSeconds;
    state.shrinkDamageMultiplier = actor.shrinkDamageMultiplier;
    state.shrinkArmorClassMultiplier = actor.shrinkArmorClassMultiplier;
    state.armorClassHalvedRemainingSeconds = actor.armorClassHalvedRemainingSeconds;
    state.darkGraspRemainingSeconds = actor.darkGraspRemainingSeconds;
    state.dayOfProtectionRemainingSeconds = actor.dayOfProtectionRemainingSeconds;
    state.dayOfProtectionPower = actor.dayOfProtectionPower;
    state.hourOfPowerRemainingSeconds = actor.hourOfPowerRemainingSeconds;
    state.hourOfPowerPower = actor.hourOfPowerPower;
    state.painReflectionRemainingSeconds = actor.painReflectionRemainingSeconds;
    state.hammerhandsRemainingSeconds = actor.hammerhandsRemainingSeconds;
    state.hammerhandsPower = actor.hammerhandsPower;
    state.hasteRemainingSeconds = actor.hasteRemainingSeconds;
    state.shieldRemainingSeconds = actor.shieldRemainingSeconds;
    state.stoneskinRemainingSeconds = actor.stoneskinRemainingSeconds;
    state.stoneskinPower = actor.stoneskinPower;
    state.blessRemainingSeconds = actor.blessRemainingSeconds;
    state.blessPower = actor.blessPower;
    state.fateRemainingSeconds = actor.fateRemainingSeconds;
    state.fatePower = actor.fatePower;
    state.heroismRemainingSeconds = actor.heroismRemainingSeconds;
    state.heroismPower = actor.heroismPower;
    state.hostileToParty = actor.hostileToParty && !outdoorActorIsPartyControlled(actor.controlMode);
    state.hasDetectedParty = actor.hasDetectedParty;
    return state;
}

bool partyHasDispellableBuffs(const Party *pParty)
{
    return pParty != nullptr && pParty->hasDispellableBuffs();
}

void queuePartySpellFx(EventRuntimeState *pEventRuntimeState, uint32_t spellId, const Party *pParty)
{
    if (pEventRuntimeState == nullptr || pParty == nullptr)
    {
        return;
    }

    EventRuntimeState::SpellFxRequest request = {};
    request.spellId = spellId;

    for (size_t memberIndex = 0; memberIndex < pParty->members().size(); ++memberIndex)
    {
        request.memberIndices.push_back(memberIndex);
    }

    pEventRuntimeState->spellFxRequests.push_back(std::move(request));
}

void applyGameplayActorSpellEffectState(
    const GameplayActorSpellEffectState &state,
    OutdoorWorldRuntime::MapActorState &actor)
{
    actor.slowRemainingSeconds = state.slowRemainingSeconds;
    actor.slowMoveMultiplier = state.slowMoveMultiplier;
    actor.slowRecoveryMultiplier = state.slowRecoveryMultiplier;
    actor.stunRemainingSeconds = state.stunRemainingSeconds;
    actor.paralyzeRemainingSeconds = state.paralyzeRemainingSeconds;
    actor.fearRemainingSeconds = state.fearRemainingSeconds;
    actor.blindRemainingSeconds = state.blindRemainingSeconds;
    actor.controlRemainingSeconds = state.controlRemainingSeconds;
    actor.controlMode = outdoorActorControlModeFromGameplay(state.controlMode);
    actor.shrinkRemainingSeconds = state.shrinkRemainingSeconds;
    actor.shrinkDamageMultiplier = state.shrinkDamageMultiplier;
    actor.shrinkArmorClassMultiplier = state.shrinkArmorClassMultiplier;
    actor.armorClassHalvedRemainingSeconds = state.armorClassHalvedRemainingSeconds;
    actor.darkGraspRemainingSeconds = state.darkGraspRemainingSeconds;
    actor.dayOfProtectionRemainingSeconds = state.dayOfProtectionRemainingSeconds;
    actor.dayOfProtectionPower = state.dayOfProtectionPower;
    actor.hourOfPowerRemainingSeconds = state.hourOfPowerRemainingSeconds;
    actor.hourOfPowerPower = state.hourOfPowerPower;
    actor.painReflectionRemainingSeconds = state.painReflectionRemainingSeconds;
    actor.hammerhandsRemainingSeconds = state.hammerhandsRemainingSeconds;
    actor.hammerhandsPower = state.hammerhandsPower;
    actor.hasteRemainingSeconds = state.hasteRemainingSeconds;
    actor.shieldRemainingSeconds = state.shieldRemainingSeconds;
    actor.stoneskinRemainingSeconds = state.stoneskinRemainingSeconds;
    actor.stoneskinPower = state.stoneskinPower;
    actor.blessRemainingSeconds = state.blessRemainingSeconds;
    actor.blessPower = state.blessPower;
    actor.fateRemainingSeconds = state.fateRemainingSeconds;
    actor.fatePower = state.fatePower;
    actor.heroismRemainingSeconds = state.heroismRemainingSeconds;
    actor.heroismPower = state.heroismPower;
    actor.hostileToParty = state.hostileToParty && !outdoorActorIsPartyControlled(actor.controlMode);
    actor.hasDetectedParty = state.hasDetectedParty;
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

    const int difficulty = std::clamp(pEncounter->difficulty, 0, 5);
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
    const SpellTable *pSpellTable,
    const OutdoorMapData * /*pOutdoorMapData*/,
    const MonsterTable::MonsterStatsEntry &stats,
    const GameplayBolsterRuntimeContext &bolsterContext,
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
    state.displayName = resolveSpawnedMapActorName(monsterTable, stats, uniqueNameId);
    state.uniqueNameId = uniqueNameId;
    state.spawnedAtRuntime = true;
    state.fromSpawnPoint = fromSpawnPoint;
    state.spawnPointIndex = spawnPointIndex;
    state.group = group;
    // Spawn group is AI grouping, not an ally/faction override.
    state.ally = 0;
    state.hostilityType = static_cast<uint8_t>(stats.hostility);
    const MonsterEntry *pMonsterEntry = resolveMonsterEntry(monsterTable, state.monsterId, &stats);
    const GameplayMonsterBolsterResult bolster =
        resolveGameplayMonsterBolster(bolsterContext, stats, pMonsterEntry);
    state.maxHp = bolster.maxHp;
    state.currentHp = bolster.maxHp;
    state.bolsterRewardMultiplier = bolster.rewardMultiplier;
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

    state.radius = pMonsterEntry != nullptr ? pMonsterEntry->radius : 32;
    state.height = pMonsterEntry != nullptr ? pMonsterEntry->height : 128;
    state.moveSpeed = bolster.moveSpeed;
    state.armorClass = bolster.armorClass;
    state.immobile = bolster.immobile;
    state.attack1DamageDiceRolls = bolster.attack1DamageDiceRolls;
    state.attack1DamageDiceSides = bolster.attack1DamageDiceSides;
    state.attack1DamageBonus = bolster.attack1DamageBonus;
    state.attack2DamageDiceRolls = bolster.attack2DamageDiceRolls;
    state.attack2DamageDiceSides = bolster.attack2DamageDiceSides;
    state.attack2DamageBonus = bolster.attack2DamageBonus;
    state.spell1SkillLevel = bolster.spell1SkillLevel;
    state.spell1SkillMastery = bolster.spell1SkillMastery;
    state.spell2SkillLevel = bolster.spell2SkillLevel;
    state.spell2SkillMastery = bolster.spell2SkillMastery;
    populateOutdoorActorStaticCombatFacts(state, &stats, pSpellTable);
    state.hostileToParty =
        (attributes & ActorAggressorBit) != 0 || monsterTable.isHostileToParty(state.monsterId);
    state.isInvisible = (attributes & ActorInvisibleBit) != 0;
    state.alertStatusBit = (attributes & ActorAlertStatusBit) != 0;
    state.animation = OutdoorWorldRuntime::ActorAnimation::Standing;
    state.aiState = OutdoorWorldRuntime::ActorAiState::Standing;
    state.recoverySeconds = monsterRecoverySeconds(stats.recovery);
    state.attackAnimationSeconds = 0.3f;
    GameplayActorService actorService = {};
    state.attackCooldownSeconds = actorService.initialAttackCooldownSeconds(actorId, state.recoverySeconds);
    state.idleDecisionSeconds = actorService.initialIdleDecisionSeconds(actorId);

    return state;
}

struct OutdoorCombatTargetCandidate
{
    size_t actorIndex = static_cast<size_t>(-1);
    GameplayActorTargetPolicyState policyState = {};
    float preciseX = 0.0f;
    float preciseY = 0.0f;
    float targetZ = 0.0f;
    uint16_t radius = 0;
    bool unavailable = false;
    bool lineOfSightChecked = false;
    bool hasLineOfSight = false;
};

struct OutdoorTargetFacts
{
    OutdoorTargetKind kind = OutdoorTargetKind::None;
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
    bool attackLineOfSight = false;
    bool partyCanSense = false;
};

struct OutdoorEngagementState
{
    bool shouldEngageTarget = false;
    bool shouldPromoteHostility = false;
    float promotionRange = 0.0f;
    bool shouldFlee = false;
    bool inMeleeRange = false;
    bool friendlyNearParty = false;
};

float meleeRangeForCombatTarget(bool targetIsActor)
{
    return targetIsActor ? ActorMeleeRange * 0.5f : ActorMeleeRange;
}

std::vector<OutdoorCombatTargetCandidate> buildCombatTargetCandidates(
    const GameplayActorService *pGameplayActorService,
    const OutdoorWorldRuntime::MapActorState &actor,
    size_t actorIndex,
    const std::vector<OutdoorWorldRuntime::MapActorState> &mapActors)
{
    std::vector<OutdoorCombatTargetCandidate> candidates;

    if (pGameplayActorService == nullptr)
    {
        return candidates;
    }

    candidates.reserve(mapActors.size() > 0 ? mapActors.size() - 1 : 0);

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

        const float deltaX = otherActor.preciseX - actor.preciseX;
        const float deltaY = otherActor.preciseY - actor.preciseY;

        if (std::abs(deltaX) > HostilityLongRange || std::abs(deltaY) > HostilityLongRange)
        {
            continue;
        }

        const float otherActorTargetZ =
            otherActor.preciseZ + std::max(24.0f, static_cast<float>(otherActor.height) * 0.7f);
        OutdoorCombatTargetCandidate candidate = {};
        candidate.actorIndex = otherActorIndex;
        candidate.policyState = buildGameplayActorTargetPolicyState(otherActor);
        candidate.preciseX = otherActor.preciseX;
        candidate.preciseY = otherActor.preciseY;
        candidate.targetZ = otherActorTargetZ;
        candidate.radius = otherActor.radius;
        candidates.push_back(candidate);
    }

    return candidates;
}

template <typename VisibilityFn>
OutdoorTargetFacts resolveOutdoorTargetFacts(
    const GameplayActorService *pGameplayActorService,
    const EventRuntimeState *pEventRuntimeState,
    const OutdoorWorldRuntime::MapActorState &actor,
    size_t actorIndex,
    std::vector<OutdoorCombatTargetCandidate> &candidates,
    float partyX,
    float partyY,
    float partyZ,
    VisibilityFn &&hasClearOutdoorLineOfSight)
{
    OutdoorTargetFacts target = {};

    if (pGameplayActorService == nullptr)
    {
        return target;
    }

    float bestPriorityDistanceSquared = std::numeric_limits<float>::max();
    const GameplayActorTargetPolicyState actorPolicyState = buildGameplayActorTargetPolicyState(actor);
    const float actorTargetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    const float partyTargetZ = partyZ + PartyTargetHeightOffset;
    const float partySenseRange = pGameplayActorService->partyEngagementRange(actorPolicyState);

    if (partySenseRange > 0.0f)
    {
        const float deltaPartyX = partyX - actor.preciseX;
        const float deltaPartyY = partyY - actor.preciseY;
        const float deltaPartyZ = partyTargetZ - actorTargetZ;
        const bool canSenseParty =
            std::abs(deltaPartyX) <= partySenseRange
            && std::abs(deltaPartyY) <= partySenseRange
            && std::abs(deltaPartyZ) <= partySenseRange
            && isWithinRange3d(deltaPartyX, deltaPartyY, deltaPartyZ, partySenseRange);

        target.partyCanSense = canSenseParty;

        if (canSenseParty)
        {
            const bool hasPartyLineOfSight =
                hasClearOutdoorLineOfSight(
                    actorIndex,
                    static_cast<size_t>(-1),
                    bx::Vec3{actor.preciseX, actor.preciseY, actorTargetZ},
                    bx::Vec3{partyX, partyY, partyTargetZ});
            const float horizontalDistanceToParty = length2d(deltaPartyX, deltaPartyY);
            const float distanceToParty = length3d(deltaPartyX, deltaPartyY, deltaPartyZ);
            const float edgeDistanceToParty =
                std::max(0.0f, distanceToParty - static_cast<float>(actor.radius) - PartyCollisionRadius);
            target.kind = OutdoorTargetKind::Party;
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
            target.attackLineOfSight = hasPartyLineOfSight;
            target.partyCanSense = true;
            bestPriorityDistanceSquared = distanceToParty * distanceToParty;
        }
    }

    for (OutdoorCombatTargetCandidate &candidate : candidates)
    {
        if (candidate.actorIndex == actorIndex || candidate.unavailable)
        {
            continue;
        }

        const float deltaX = candidate.preciseX - actor.preciseX;
        const float deltaY = candidate.preciseY - actor.preciseY;

        if (std::abs(deltaX) > HostilityLongRange || std::abs(deltaY) > HostilityLongRange)
        {
            continue;
        }

        const GameplayActorTargetPolicyResult targetPolicy =
            pGameplayActorService->resolveActorTargetPolicy(actorPolicyState, candidate.policyState);
        GameplayActorTargetPolicyResult effectiveTargetPolicy = targetPolicy;
        const uint32_t actorRelationMonsterId = actorPolicyState.relationMonsterId > 0
            ? static_cast<uint32_t>(actorPolicyState.relationMonsterId)
            : static_cast<uint32_t>(actorPolicyState.monsterId);
        const uint32_t candidateRelationMonsterId = candidate.policyState.relationMonsterId > 0
            ? static_cast<uint32_t>(candidate.policyState.relationMonsterId)
            : static_cast<uint32_t>(candidate.policyState.monsterId);
        const std::optional<int32_t> localRelationValue =
            localMonsterRelation(pEventRuntimeState, actorRelationMonsterId, candidateRelationMonsterId);

        if (!targetPolicy.canTarget && localRelationValue && *localRelationValue > 0)
        {
            effectiveTargetPolicy.canTarget = true;
            effectiveTargetPolicy.relationToTarget = *localRelationValue;
            effectiveTargetPolicy.engagementRange = localRelationEngagementRange(*localRelationValue);
        }
        else if (targetPolicy.canTarget && localRelationValue && *localRelationValue <= 0)
        {
            effectiveTargetPolicy = {};
        }

        if (!effectiveTargetPolicy.canTarget)
        {
            continue;
        }

        const float deltaZ = candidate.targetZ - actorTargetZ;
        const float distanceSquaredToCandidate = lengthSquared3d(deltaX, deltaY, deltaZ);

        if (distanceSquaredToCandidate >= bestPriorityDistanceSquared)
        {
            continue;
        }

        if (!isWithinRange3d(deltaX, deltaY, deltaZ, effectiveTargetPolicy.engagementRange))
        {
            continue;
        }

        if (!candidate.lineOfSightChecked)
        {
            candidate.hasLineOfSight =
                hasClearOutdoorLineOfSight(
                    actorIndex,
                    candidate.actorIndex,
                    bx::Vec3{actor.preciseX, actor.preciseY, actorTargetZ},
                    bx::Vec3{candidate.preciseX, candidate.preciseY, candidate.targetZ});
            candidate.lineOfSightChecked = true;
        }

        if (!candidate.hasLineOfSight)
        {
            continue;
        }

        const float horizontalDistanceToCandidate = length2d(deltaX, deltaY);
        const float distanceToCandidate = length3d(deltaX, deltaY, deltaZ);
        const float edgeDistance =
            std::max(
                0.0f,
                distanceToCandidate - static_cast<float>(actor.radius) - static_cast<float>(candidate.radius));
        target.kind = OutdoorTargetKind::Actor;
        target.actorIndex = candidate.actorIndex;
        target.relationToTarget = effectiveTargetPolicy.relationToTarget;
        target.targetX = candidate.preciseX;
        target.targetY = candidate.preciseY;
        target.targetZ = candidate.targetZ;
        target.deltaX = deltaX;
        target.deltaY = deltaY;
        target.deltaZ = deltaZ;
        target.horizontalDistanceToTarget = horizontalDistanceToCandidate;
        target.distanceToTarget = distanceToCandidate;
        target.edgeDistance = edgeDistance;
        target.canSense = true;
        target.attackLineOfSight = true;
        bestPriorityDistanceSquared = distanceSquaredToCandidate;
    }

    return target;
}

OutdoorEngagementState resolveOutdoorEngagementState(
    const GameplayActorService &actorService,
    const GameplayActorTargetPolicyState &actorPolicyState,
    const OutdoorTargetFacts &combatTarget,
    GameplayActorAiType aiType,
    uint8_t hostilityType,
    int currentHp,
    int maxHp,
    bool hostileToParty,
    bool partyIsVeryNearActor,
    bool suppressLowHealthFlee)
{
    OutdoorEngagementState engagement = {};
    const bool targetIsActor = combatTarget.kind == OutdoorTargetKind::Actor;
    const bool hasCombatTarget = combatTarget.kind != OutdoorTargetKind::None;
    engagement.shouldEngageTarget = hasCombatTarget && combatTarget.canSense;
    engagement.inMeleeRange = combatTarget.edgeDistance <= meleeRangeForCombatTarget(targetIsActor);

    if (targetIsActor && hostilityType == 0 && !actorService.isPartyControlledActor(actorPolicyState.controlMode))
    {
        engagement.promotionRange =
            actorService.hostilityPromotionRangeForFriendlyActor(combatTarget.relationToTarget);
        engagement.shouldPromoteHostility =
            combatTarget.relationToTarget == 1
            || (engagement.promotionRange >= 0.0f
                && lengthSquared3d(combatTarget.deltaX, combatTarget.deltaY, combatTarget.deltaZ)
                    <= engagement.promotionRange * engagement.promotionRange);

        if (!engagement.shouldPromoteHostility)
        {
            engagement.shouldEngageTarget = false;
        }
    }

    engagement.shouldFlee =
        engagement.shouldEngageTarget
        && combatTarget.distanceToTarget <= HostilityLongRange
        && actorService.shouldFleeForAiType(aiType, currentHp, maxHp)
        && !(suppressLowHealthFlee && aiType != GameplayActorAiType::Wimp);
    engagement.friendlyNearParty =
        !engagement.shouldEngageTarget
        && !hostileToParty
        && !actorService.isPartyControlledActor(actorPolicyState.controlMode)
        && partyIsVeryNearActor;
    return engagement;
}

void resetCrowdSteeringState(OutdoorWorldRuntime::MapActorState &actor)
{
    actor.crowdSideLockRemainingSeconds = 0.0f;
    actor.crowdNoProgressSeconds = 0.0f;
    actor.crowdLastEdgeDistance = 0.0f;
    actor.crowdRetreatRemainingSeconds = 0.0f;
    actor.crowdStandRemainingSeconds = 0.0f;
    actor.crowdProbeX = actor.preciseX;
    actor.crowdProbeY = actor.preciseY;
    actor.crowdProbeEdgeDistance = 0.0f;
    actor.crowdProbeElapsedSeconds = 0.0f;
    actor.crowdEscapeAttempts = 0;
    actor.crowdSideSign = 0;
}

void updateInactiveActorPresentation(
    OutdoorWorldRuntime::MapActorState &actor,
    float partyX,
    float partyY,
    const GameplayActorService *pGameplayActorService)
{
    if (actor.isDead || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead)
    {
        actor.aiState = OutdoorWorldRuntime::ActorAiState::Dead;
        actor.animation = OutdoorWorldRuntime::ActorAnimation::Dead;
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
        actor.actionSeconds = 0.0f;
        actor.attackImpactTriggered = false;
        return;
    }

    actor.aiState = OutdoorWorldRuntime::ActorAiState::Standing;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.hasDetectedParty = false;
    actor.attackImpactTriggered = false;

    const float deltaX = partyX - actor.preciseX;
    const float deltaY = partyY - actor.preciseY;

    if (std::abs(deltaX) > 0.01f || std::abs(deltaY) > 0.01f)
    {
        actor.yawRadians = std::atan2(deltaY, deltaX);
    }

    actor.animationTimeTicks += ActorUpdateStepSeconds * TicksPerSecond;
    actor.actionSeconds = std::max(0.0f, actor.actionSeconds - ActorUpdateStepSeconds);
    actor.idleDecisionSeconds = std::max(0.0f, actor.idleDecisionSeconds - ActorUpdateStepSeconds);

    if (actor.animation == OutdoorWorldRuntime::ActorAnimation::Bored && actor.actionSeconds > 0.0f)
    {
        return;
    }

    actor.animation = OutdoorWorldRuntime::ActorAnimation::Standing;

    if (actor.idleDecisionSeconds > 0.0f)
    {
        return;
    }

    actor.idleDecisionSeconds = InactiveActorDecisionIntervalSeconds;

    if (pGameplayActorService == nullptr)
    {
        return;
    }

    const uint32_t decisionSeed = inactiveActorDecisionSeed(actor.actorId, actor.idleDecisionCount, 0x7f4a7c15u);
    actor.idleDecisionCount += 1;

    if ((decisionSeed % 100u) < InactiveActorFidgetChancePercent)
    {
        actor.attackImpactTriggered = false;
        actor.actionSeconds = InactiveActorBoredSeconds;
        actor.idleDecisionSeconds = InactiveActorBoredSeconds;
        actor.animation = OutdoorWorldRuntime::ActorAnimation::Bored;
        actor.animationTimeTicks = 0.0f;
    }
}

void updateTurnBasedActorWaitingPresentation(
    OutdoorWorldRuntime::MapActorState &actor,
    float partyX,
    float partyY,
    float deltaSeconds,
    const SpriteFrameTable *pActorSpriteFrameTable)
{
    if (actor.isDead || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead)
    {
        actor.aiState = OutdoorWorldRuntime::ActorAiState::Dead;
        actor.animation = OutdoorWorldRuntime::ActorAnimation::Dead;
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
        actor.actionSeconds = 0.0f;
        actor.attackImpactTriggered = false;
        return;
    }

    actor.aiState = OutdoorWorldRuntime::ActorAiState::Standing;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.attackImpactTriggered = false;

    const float deltaX = partyX - actor.preciseX;
    const float deltaY = partyY - actor.preciseY;

    if (std::abs(deltaX) > 0.01f || std::abs(deltaY) > 0.01f)
    {
        actor.yawRadians = std::atan2(deltaY, deltaX);
    }

    const bool wasBored = actor.animation == OutdoorWorldRuntime::ActorAnimation::Bored;

    if (!wasBored)
    {
        if (actor.idleDecisionSeconds <= 0.0f && actor.actionSeconds <= 0.0f)
        {
            const uint32_t standSeed = inactiveActorDecisionSeed(actor.actorId, actor.idleDecisionCount, 0x95f2a5f1u);
            const float standSeconds = turnBasedActorStandSeconds(standSeed);
            actor.idleDecisionSeconds = standSeconds;
            actor.actionSeconds = standSeconds;
        }
        else
        {
            actor.idleDecisionSeconds = std::min(actor.idleDecisionSeconds, TurnBasedActorStandMaxSeconds);
            actor.actionSeconds = std::min(actor.actionSeconds, TurnBasedActorStandMaxSeconds);
        }
    }

    const float stepSeconds = std::max(0.0f, deltaSeconds);
    actor.animationTimeTicks += stepSeconds * TicksPerSecond;
    actor.actionSeconds = std::max(0.0f, actor.actionSeconds - stepSeconds);
    actor.idleDecisionSeconds = std::max(0.0f, actor.idleDecisionSeconds - stepSeconds);

    if (wasBored && actor.actionSeconds > 0.0f)
    {
        return;
    }

    actor.animation = OutdoorWorldRuntime::ActorAnimation::Standing;

    if (wasBored)
    {
        const uint32_t standSeed = inactiveActorDecisionSeed(actor.actorId, actor.idleDecisionCount, 0x95f2a5f1u);
        const float standSeconds = turnBasedActorStandSeconds(standSeed);
        actor.idleDecisionSeconds = standSeconds;
        actor.actionSeconds = standSeconds;
        actor.animationTimeTicks = 0.0f;
        return;
    }

    if (actor.idleDecisionSeconds > 0.0f)
    {
        return;
    }

    const uint32_t decisionSeed = inactiveActorDecisionSeed(actor.actorId, actor.idleDecisionCount, 0x7f4a7c15u);
    actor.idleDecisionCount += 1;

    if ((decisionSeed % 100u) < TurnBasedActorBoredChancePercent)
    {
        const float boredSeconds = actorAnimationSeconds(
            pActorSpriteFrameTable,
            actor,
            OutdoorWorldRuntime::ActorAnimation::Bored,
            TurnBasedActorBoredFallbackSeconds);
        actor.actionSeconds = boredSeconds;
        actor.idleDecisionSeconds = boredSeconds;
        actor.animation = OutdoorWorldRuntime::ActorAnimation::Bored;
        actor.animationTimeTicks = 0.0f;
        return;
    }

    const float standSeconds = turnBasedActorStandSeconds(decisionSeed >> 8u);
    actor.actionSeconds = standSeconds;
    actor.idleDecisionSeconds = standSeconds;
    actor.animationTimeTicks = 0.0f;
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

void OutdoorWorldRuntime::pushAudioEvent(
    uint32_t soundId,
    uint32_t sourceId,
    const std::string &reason,
    float x,
    float y,
    float z,
    bool positional,
    SoundScope soundScope)
{
    if (soundId == 0)
    {
        return;
    }

    AudioEvent event = {};
    event.soundScope = soundScope;
    event.soundId = soundId;
    event.sourceId = sourceId;
    event.reason = reason;
    event.x = x;
    event.y = y;
    event.z = z;
    event.positional = positional;
    m_pendingAudioEvents.push_back(std::move(event));
}

void OutdoorWorldRuntime::pushProjectileAudioEvent(
    const GameplayProjectileService::ProjectileAudioRequest &request)
{
    pushAudioEvent(
        request.soundId,
        request.sourceId,
        request.reason,
        request.x,
        request.y,
        request.z,
        request.positional);
}

OutdoorWorldRuntime::ChestViewState OutdoorWorldRuntime::buildChestView(uint32_t chestId) const
{
    if (chestId >= m_chests.size())
    {
        return {};
    }

    return buildMaterializedChestView(
        chestId,
        m_chests[chestId],
        m_mapTreasureLevel,
        m_mapId,
        m_sessionChestSeed,
        m_pChestTable,
        m_pItemTable,
        m_pParty);
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

    const bool cached = m_materializedChestViews[chestId].has_value();

    if (!cached)
    {
        m_materializedChestViews[chestId] = buildChestView(chestId);
    }

    m_activeChestView = *m_materializedChestViews[chestId];

    if (EventRuntimeState *pEventRuntimeState = eventRuntimeState())
    {
        pEventRuntimeState->lastChestOpened = EventRuntimeState::ChestOpenedTrace{
            .sceneKind = "outdoor",
            .map = mapName(),
            .chestId = chestId,
            .itemCount = m_activeChestView->items.size(),
            .hiddenItemCount = m_activeChestView->hiddenItems.size(),
        };
    }

    GAMEPLAY_DEBUG_TRACE(
        "chest_opened scene_kind=outdoor map=\"" + mapName() + "\""
        + " chest_id=" + std::to_string(chestId)
        + " item_count=" + std::to_string(m_activeChestView->items.size())
        + " hidden_item_count=" + std::to_string(m_activeChestView->hiddenItems.size()));

    for (const GameplayChestItemState &item : m_activeChestView->items)
    {
        const uint32_t itemId = item.item.objectDescriptionId != 0 ? item.item.objectDescriptionId : item.itemId;
        const bool questLike = !item.isGold && gameplayDebugTraceItemLooksQuestRelevant(itemId, m_pItemTable);

        if (!item.isGold && itemId != 0)
        {
            GAMEPLAY_DEBUG_TRACE(
                "chest_contains_item scene_kind=outdoor map=\"" + mapName() + "\""
                + " chest_id=" + std::to_string(chestId)
                + " item_id=" + std::to_string(itemId)
                + gameplayDebugTraceItemSummary(itemId, m_pItemTable)
                + " quest_like=" + (questLike ? "true" : "false")
                + " grid=(" + std::to_string(item.gridX)
                + "," + std::to_string(item.gridY) + ")");
        }

        if (questLike)
        {
            GAMEPLAY_DEBUG_TRACE(
                "chest_contains_quest_item scene_kind=outdoor map=\"" + mapName() + "\""
                + " chest_id=" + std::to_string(chestId)
                + " item_id=" + std::to_string(itemId)
                + gameplayDebugTraceItemSummary(itemId, m_pItemTable)
                + " grid=(" + std::to_string(item.gridX)
                + "," + std::to_string(item.gridY) + ")");
        }
    }

    pushAudioEvent(
        static_cast<uint32_t>(SoundId::OpenChest),
        chestId,
        "chest_open",
        0.0f,
        0.0f,
        0.0f,
        false);
}

void OutdoorWorldRuntime::setPendingEventSourcePoint(std::optional<GameplayWorldPoint> point)
{
    m_pendingEventSourcePoint = point;
}

bool OutdoorWorldRuntime::attemptOpenChest(uint32_t chestId, bool openedByTelekinesis)
{
    if (chestId >= m_chests.size() || m_pParty == nullptr)
    {
        return false;
    }

    MapDeltaChest &chest = m_chests[chestId];
    const GameplayWorldPoint sourcePoint = chestTrapSourcePoint();
    const GameplayWorldPoint visualPoint = chestTrapVisualPoint(sourcePoint);
    ChestTrapOpenContext trapContext = {};
    trapContext.trapX = visualPoint.x;
    trapContext.trapY = visualPoint.y;
    trapContext.trapZ = visualPoint.z;
    trapContext.partyX = partyX();
    trapContext.partyY = partyY();
    trapContext.openedByTelekinesis = openedByTelekinesis;

    if (m_pPartyRuntime != nullptr)
    {
        trapContext.partyZ = m_pPartyRuntime->partyFootZ() + PartyTargetHeightOffset;
    }

    trapContext.seed =
        m_sessionChestSeed
        ^ (chestId + 1u) * 2654435761u
        ^ static_cast<uint32_t>(std::lround(m_gameMinutes * TicksPerSecond));

    const ChestTrapOpenResult trapResult = resolveChestTrapOpen(
        *m_pParty,
        m_map,
        chest.flags,
        trapContext,
        m_pItemTable,
        m_pStandardItemEnchantTable,
        m_pSpecialItemEnchantTable);

    if (!trapResult.trapWasPresent)
    {
        return true;
    }

    applyChestTrapState(chestId, trapResult);
    applyChestTrapOpenResultToParty(*m_pParty, trapResult);

    if (trapResult.trapDischarged)
    {
        spawnChestTrapVisual(visualPoint, trapResult);
    }

    return trapResult.shouldOpenChest;
}

GameplayWorldPoint OutdoorWorldRuntime::chestTrapSourcePoint() const
{
    if (m_pendingEventSourcePoint)
    {
        return *m_pendingEventSourcePoint;
    }

    GameplayWorldPoint point = {};
    point.x = partyX();
    point.y = partyY();
    point.z = partyFootZ() + PartyTargetHeightOffset;
    return point;
}

GameplayWorldPoint OutdoorWorldRuntime::chestTrapVisualPoint(const GameplayWorldPoint &sourcePoint) const
{
    GameplayWorldPoint point = sourcePoint;
    const float deltaX = partyX() - sourcePoint.x;
    const float deltaY = partyY() - sourcePoint.y;
    const float length = std::sqrt(deltaX * deltaX + deltaY * deltaY);

    if (length > 1.0f)
    {
        const float depth = std::min(ChestTrapForwardDepth, length);
        const float horizontalDepth = depth * ChestTrapForwardPitchScale;
        point.x += (deltaX / length) * horizontalDepth;
        point.y += (deltaY / length) * horizontalDepth;
        point.z += depth * ChestTrapForwardPitchScale;
    }

    point.z += ChestTrapCenterSpriteZOffset;
    return point;
}

void OutdoorWorldRuntime::applyChestTrapState(uint32_t chestId, const ChestTrapOpenResult &trapResult)
{
    if (chestId >= m_chests.size())
    {
        return;
    }

    MapDeltaChest &chest = m_chests[chestId];
    chest.flags &= ~static_cast<uint16_t>(EvtChestFlag::Trapped);

    if (!trapResult.shouldOpenChest)
    {
        chest.flags &= ~static_cast<uint16_t>(EvtChestFlag::Opened);

        if (chestId < m_openedChests.size())
        {
            m_openedChests[chestId] = false;
        }
    }

    if (m_eventRuntimeState)
    {
        m_eventRuntimeState->chestSetMasks[chestId] &= ~static_cast<uint32_t>(EvtChestFlag::Trapped);
        m_eventRuntimeState->chestClearMasks[chestId] |= static_cast<uint32_t>(EvtChestFlag::Trapped);

        if (!trapResult.shouldOpenChest)
        {
            m_eventRuntimeState->chestSetMasks[chestId] &= ~static_cast<uint32_t>(EvtChestFlag::Opened);
            m_eventRuntimeState->chestClearMasks[chestId] |= static_cast<uint32_t>(EvtChestFlag::Opened);
        }
    }

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId]->flags = chest.flags;
    }

    if (m_activeChestView && m_activeChestView->chestId == chestId)
    {
        m_activeChestView->flags = chest.flags;
    }
}

void OutdoorWorldRuntime::spawnChestTrapVisual(
    const GameplayWorldPoint &point,
    const ChestTrapOpenResult &trapResult)
{
    if (trapResult.trapObjectId == 0)
    {
        return;
    }

    if (m_pObjectTable == nullptr)
    {
        return;
    }

    const std::optional<uint16_t> objectDescriptionId =
        m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(trapResult.trapObjectId));

    if (!objectDescriptionId)
    {
        return;
    }

    ProjectileState projectile = {};
    projectile.sourceKind = ProjectileState::SourceKind::Event;
    projectile.sourceId = EventSpellSourceId;
    projectile.impactObjectDescriptionId = *objectDescriptionId;
    projectile.impactSoundIdOverride = static_cast<uint32_t>(SoundId::Fireball);
    projectile.sourceX = point.x;
    projectile.sourceY = point.y;
    projectile.sourceZ = point.z;
    projectile.x = point.x;
    projectile.y = point.y;
    projectile.z = point.z;
    projectile.damageType = trapResult.damageType;

    spawnProjectileImpact(projectile, point.x, point.y, point.z, true);
}

void OutdoorWorldRuntime::initialize(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const MonsterProjectileTable &monsterProjectileTable,
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    const ItemTable &itemTable,
    Party *pParty,
    OutdoorPartyRuntime *pPartyRuntime,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const ChestTable *pChestTable,
    const std::optional<OutdoorMapData> &outdoorMapData,
    const std::optional<MapDeltaData> &outdoorMapDeltaData,
    const std::optional<OutdoorWeatherProfile> &outdoorWeatherProfile,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet,
    const std::optional<SpriteObjectBillboardSet> &outdoorSpriteObjectBillboardSet,
    GameplayActorService *pGameplayActorService,
    GameplayProjectileService *pGameplayProjectileService,
    GameplayCombatController *pGameplayCombatController,
    GameplayFxService *pGameplayFxService,
    const MergedBolsterMapTable *pMergedBolsterMapTable,
    const MergedBolsterMonsterTable *pMergedBolsterMonsterTable
)
{
    m_mapId = map.id;
    m_map = map;
    m_mapName = map.name;
    m_mapTreasureLevel = map.treasureLevel;
    m_gameMinutes = 9.0f * 60.0f;
    m_atmosphereState = buildAtmosphereSourceState(map, outdoorMapData, outdoorMapDeltaData);
    m_outdoorWeatherProfile = outdoorWeatherProfile;
    m_timers.clear();
    m_mapActors.clear();
    m_spawnPoints.clear();
    m_mapActorCorpseViews.clear();
    m_activeCorpseView.reset();
    m_actorCorpsePhysicsActorIndices.clear();
    m_pendingAudioEvents.clear();
    m_worldItems.clear();
    m_chests = outdoorMapDeltaData ? outdoorMapDeltaData->chests : std::vector<MapDeltaChest>();
    m_openedChests.assign(outdoorMapDeltaData ? outdoorMapDeltaData->chests.size() : 0, false);
    m_materializedChestViews.assign(m_chests.size(), std::nullopt);
    m_activeChestView.reset();
    m_eventRuntimeState = eventRuntimeState;
    if (m_eventRuntimeState)
    {
        m_eventRuntimeState->mapFileName = map.fileName;
        setActiveHistoryContinent(*m_eventRuntimeState, map.mergedContinentId);
    }
    m_pItemTable = &itemTable;
    m_pParty = pParty;
    if (m_eventRuntimeState && m_pParty != nullptr)
    {
        m_pParty->applyGlobalNpcStateTo(*m_eventRuntimeState);
    }
    m_pPartyRuntime = pPartyRuntime;
    m_pStandardItemEnchantTable = &standardItemEnchantTable;
    m_pSpecialItemEnchantTable = &specialItemEnchantTable;
    m_pChestTable = pChestTable;
    m_pMonsterTable = &monsterTable;
    m_pMergedBolsterMapTable = pMergedBolsterMapTable;
    m_pMergedBolsterMonsterTable = pMergedBolsterMonsterTable;
    m_pMonsterProjectileTable = &monsterProjectileTable;
    m_pObjectTable = &objectTable;
    m_pOutdoorMapData = outdoorMapData ? const_cast<OutdoorMapData *>(&*outdoorMapData) : nullptr;
    m_pOutdoorMapDeltaData = outdoorMapDeltaData ? const_cast<MapDeltaData *>(&*outdoorMapDeltaData) : nullptr;
    m_outdoorLandMask = outdoorLandMask;
    m_pSpellTable = &spellTable;
    m_pGameplayActorService = pGameplayActorService;
    m_pGameplayProjectileService = pGameplayProjectileService;
    m_pGameplayCombatController = pGameplayCombatController;
    m_pGameplayFxService = pGameplayFxService;
    projectileService().clear();
    if (m_pGameplayCombatController != nullptr)
    {
        m_pGameplayCombatController->clearPendingCombatEvents();
    }
    m_pActorSpriteFrameTable = outdoorActorPreviewBillboardSet ? &outdoorActorPreviewBillboardSet->spriteFrameTable : nullptr;
    m_pProjectileSpriteFrameTable = outdoorSpriteObjectBillboardSet
        ? &outdoorSpriteObjectBillboardSet->spriteFrameTable
        : m_pActorSpriteFrameTable;
    m_pWorldFxSystem = nullptr;
    m_monsterVisualsById.clear();
    m_outdoorFaces.clear();
    m_outdoorFaceGridCells.clear();
    m_outdoorFaceGridMinX = 0.0f;
    m_outdoorFaceGridMinY = 0.0f;
    m_outdoorFaceGridWidth = 0;
    m_outdoorFaceGridHeight = 0;
    m_outdoorMovementController.reset();
    m_actorUpdateAccumulatorSeconds = 0.0f;
    m_nextWorldItemId = 1;
    m_armageddonState = {};

    materializeMapDeltaWorldItems();
    applyInitialWeatherProfile();
    refreshAtmosphereState();

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

    rebuildOutdoorFaceGeometryCache();

    if (outdoorMapData)
    {
        m_outdoorMovementController.emplace(
            *outdoorMapData,
            outdoorLandMask,
            outdoorDecorationCollisionSet,
            outdoorActorCollisionSet,
            outdoorSpriteObjectCollisionSet);
        syncOutdoorFaceGeometryAttributesFromMapDelta();
    }
    m_nextActorId = 0;
    projectileService().clear();

    if (outdoorMapDeltaData)
    {
        const GameplayBolsterRuntimeContext bolsterContext{
            .pMap = &m_map,
            .pMonsterTable = m_pMonsterTable,
            .pBolsterMapTable = m_pMergedBolsterMapTable,
            .pBolsterMonsterTable = m_pMergedBolsterMonsterTable,
            .pParty = m_pParty,
            .bolsterMonstersEnabled = m_bolsterMonstersEnabled,
        };
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
                &spellTable,
                outdoorMapDeltaData->actors[actorIndex],
                static_cast<uint32_t>(actorIndex),
                m_pOutdoorMapData,
                mapActorAttackAnimationSeconds[actorIndex],
                bolsterContext);
            const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actorState.monsterId);

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

        for (MapActorState &actor : m_mapActors)
        {
            const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actor.monsterId);

            if (pStats != nullptr)
            {
                applyOeOutdoorActorFloorCorrection(actor, *pStats);
            }

            if (m_outdoorMovementController)
            {
                const float collisionRadius = actorCollisionRadius(actor, pStats);
                actor.movementState = m_outdoorMovementController->initializeActorStateForBodyPreservingZ(
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + GroundSnapHeight,
                    collisionRadius);
                actor.movementStateInitialized = true;
                actor.movementState.verticalVelocity = actor.velocityZ;
                syncActorFromMovementState(actor);
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

                if (spawn.typeId == 2)
                {
                    materializeTreasureSpawnFromSpawnPoint(spawnIndex);
                    continue;
                }

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
                    static_cast<float>(spawn.x),
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

    applyEventRuntimeState(true);
}

void OutdoorWorldRuntime::setWorldFxSystem(WorldFxSystem *pWorldFxSystem)
{
    m_pWorldFxSystem = pWorldFxSystem;
}

bool OutdoorWorldRuntime::resolveWorldItemVisual(
    uint32_t itemId,
    uint16_t &objectDescriptionId,
    uint16_t &objectSpriteId,
    uint16_t &objectSpriteFrameIndex,
    uint16_t &objectFlags,
    uint16_t &radius,
    uint16_t &height,
    std::string &objectName,
    std::string &objectSpriteName) const
{
    if (m_pItemTable == nullptr || m_pObjectTable == nullptr || itemId == 0)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr || pItemDefinition->spriteIndex == 0)
    {
        return false;
    }

    const std::optional<uint16_t> descriptionId =
        m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(pItemDefinition->spriteIndex));

    if (!descriptionId)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = m_pObjectTable->get(*descriptionId);

    if (pObjectEntry == nullptr || (pObjectEntry->flags & ObjectDescNoSprite) != 0 || pObjectEntry->spriteId == 0)
    {
        return false;
    }

    objectDescriptionId = *descriptionId;
    objectSpriteId = pObjectEntry->spriteId;
    objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        pObjectEntry->spriteId,
        pObjectEntry->spriteName);
    objectFlags = pObjectEntry->flags;
    radius = static_cast<uint16_t>(std::max<int16_t>(0, pObjectEntry->radius));
    height = static_cast<uint16_t>(std::max<int16_t>(0, pObjectEntry->height));
    objectName = pObjectEntry->internalName;
    objectSpriteName = pObjectEntry->spriteName;
    return true;
}

bool OutdoorWorldRuntime::materializeTreasureSpawnFromSpawnPoint(size_t spawnPointIndex)
{
    if (spawnPointIndex >= m_spawnPoints.size()
        || m_pItemTable == nullptr
        || m_pObjectTable == nullptr
        || m_pStandardItemEnchantTable == nullptr
        || m_pSpecialItemEnchantTable == nullptr)
    {
        return false;
    }

    const SpawnPointState &spawn = m_spawnPoints[spawnPointIndex];

    if (spawn.typeId != 2)
    {
        return false;
    }

    const auto canMaterializeAsWorldItem =
        [this](const ItemDefinition &entry)
        {
            uint16_t objectDescriptionId = 0;
            uint16_t objectSpriteId = 0;
            uint16_t objectSpriteFrameIndex = 0;
            uint16_t objectFlags = 0;
            uint16_t radius = 0;
            uint16_t height = 0;
            std::string objectName;
            std::string objectSpriteName;
            return resolveWorldItemVisual(
                entry.itemId,
                objectDescriptionId,
                objectSpriteId,
                objectSpriteFrameIndex,
                objectFlags,
                radius,
                height,
                objectName,
                objectSpriteName);
        };

    const std::optional<GameplayTreasureSpawnResult> treasure =
        generateTreasureSpawnItem(
            spawn.index,
            m_mapTreasureLevel,
            m_sessionChestSeed,
            m_mapId,
            static_cast<uint32_t>(spawnPointIndex),
            *m_pItemTable,
            *m_pStandardItemEnchantTable,
            *m_pSpecialItemEnchantTable,
            m_pParty,
            canMaterializeAsWorldItem);

    if (!treasure || treasure->item.objectDescriptionId == 0)
    {
        return false;
    }

    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    std::string objectName;
    std::string objectSpriteName;

    if (!resolveWorldItemVisual(
            treasure->item.objectDescriptionId,
            objectDescriptionId,
            objectSpriteId,
            objectSpriteFrameIndex,
            objectFlags,
            radius,
            height,
            objectName,
            objectSpriteName))
    {
        return false;
    }

    float worldZ = static_cast<float>(spawn.z);

    if (m_pOutdoorMapData != nullptr)
    {
        worldZ = worldItemFloorHeight(
            *m_pOutdoorMapData,
            static_cast<float>(spawn.x),
            static_cast<float>(spawn.y),
            worldZ);
    }

    WorldItemState worldItem = {};
    worldItem.worldItemId = m_nextWorldItemId++;
    worldItem.item = treasure->item;
    worldItem.goldAmount = treasure->goldAmount;
    worldItem.isGold = treasure->isGold && isGoldHeapItemId(treasure->item.objectDescriptionId);
    worldItem.objectDescriptionId = objectDescriptionId;
    worldItem.objectSpriteId = objectSpriteId;
    worldItem.objectSpriteFrameIndex = objectSpriteFrameIndex;
    worldItem.objectFlags = objectFlags;
    worldItem.radius = radius;
    worldItem.height = height;
    worldItem.attributes = spawn.attributes;
    worldItem.objectName = objectName;
    worldItem.objectSpriteName = objectSpriteName;
    worldItem.x = static_cast<float>(spawn.x);
    worldItem.y = static_cast<float>(spawn.y);
    worldItem.z = worldZ;
    worldItem.initialX = worldItem.x;
    worldItem.initialY = worldItem.y;
    worldItem.initialZ = worldItem.z;
    m_worldItems.push_back(std::move(worldItem));
    return true;
}

void OutdoorWorldRuntime::materializeMapDeltaWorldItems()
{
    if (m_pOutdoorMapDeltaData == nullptr || m_pItemTable == nullptr || m_pObjectTable == nullptr)
    {
        return;
    }

    for (const MapDeltaSpriteObject &spriteObject : m_pOutdoorMapDeltaData->spriteObjects)
    {
        if (!hasContainingItemPayload(spriteObject.rawContainingItem))
        {
            continue;
        }

        const ObjectEntry *pObjectEntry = m_pObjectTable->get(spriteObject.objectDescriptionId);

        if (pObjectEntry == nullptr || (pObjectEntry->flags & ObjectDescUnpickable) != 0)
        {
            continue;
        }

        int32_t rawItemId = 0;
        int32_t rawGoldAmount = 0;

        if (!readInt32FromBytes(spriteObject.rawContainingItem, 0x00, rawItemId)
            || !readInt32FromBytes(spriteObject.rawContainingItem, 0x0c, rawGoldAmount)
            || rawItemId <= 0)
        {
            continue;
        }

        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t objectFlags = 0;
        uint16_t radius = 0;
        uint16_t height = 0;
        std::string objectName;
        std::string objectSpriteName;

        if (!resolveWorldItemVisual(
                static_cast<uint32_t>(rawItemId),
                objectDescriptionId,
                objectSpriteId,
                objectSpriteFrameIndex,
                objectFlags,
                radius,
                height,
                objectName,
                objectSpriteName))
        {
            continue;
        }

        const ItemDefinition *pItemDefinition = m_pItemTable->get(static_cast<uint32_t>(rawItemId));

        if (pItemDefinition == nullptr)
        {
            continue;
        }

        WorldItemState worldItem = {};
        worldItem.worldItemId = m_nextWorldItemId++;
        worldItem.item.objectDescriptionId = static_cast<uint32_t>(rawItemId);
        worldItem.item.quantity = 1;
        worldItem.item.width = pItemDefinition->inventoryWidth;
        worldItem.item.height = pItemDefinition->inventoryHeight;
        worldItem.goldAmount = isGoldHeapItemId(worldItem.item.objectDescriptionId)
            ? static_cast<uint32_t>(std::max(0, rawGoldAmount))
            : 0;
        worldItem.isGold = worldItem.goldAmount > 0 && isGoldHeapItemId(worldItem.item.objectDescriptionId);
        worldItem.objectDescriptionId = objectDescriptionId;
        worldItem.objectSpriteId = objectSpriteId;
        worldItem.objectSpriteFrameIndex = objectSpriteFrameIndex;
        worldItem.objectFlags = objectFlags;
        worldItem.radius = radius;
        worldItem.height = height;
        worldItem.soundId = spriteObject.soundId;
        worldItem.attributes = spriteObject.attributes;
        worldItem.sectorId = spriteObject.sectorId;
        worldItem.objectName = objectName;
        worldItem.objectSpriteName = objectSpriteName;
        worldItem.x = static_cast<float>(spriteObject.x);
        worldItem.y = static_cast<float>(spriteObject.y);
        worldItem.z = static_cast<float>(spriteObject.z);
        worldItem.velocityX = static_cast<float>(spriteObject.velocityX);
        worldItem.velocityY = static_cast<float>(spriteObject.velocityY);
        worldItem.velocityZ = static_cast<float>(spriteObject.velocityZ);
        worldItem.initialX = static_cast<float>(spriteObject.initialX);
        worldItem.initialY = static_cast<float>(spriteObject.initialY);
        worldItem.initialZ = static_cast<float>(spriteObject.initialZ);
        worldItem.timeSinceCreatedTicks = uint32_t(spriteObject.timeSinceCreated) * 8;
        worldItem.lifetimeTicks = spriteObject.temporaryLifetime > 0
            ? uint32_t(spriteObject.temporaryLifetime) * 8
            : 0;
        m_worldItems.push_back(std::move(worldItem));
    }
}

bool OutdoorWorldRuntime::spawnWorldItem(
    const InventoryItem &item,
    float sourceX,
    float sourceY,
    float sourceZ,
    float yawRadians)
{
    if (item.objectDescriptionId == 0)
    {
        return false;
    }

    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint32_t lifetimeTicks = 0;
    std::string objectName;
    std::string objectSpriteName;

    if (!resolveWorldItemVisual(
            item.objectDescriptionId,
            objectDescriptionId,
            objectSpriteId,
            objectSpriteFrameIndex,
            objectFlags,
            radius,
            height,
            objectName,
            objectSpriteName))
    {
        return false;
    }

    const float directionX = std::cos(yawRadians);
    const float directionY = std::sin(yawRadians);
    const float horizontalSpeed = WorldItemThrowSpeed * std::cos(WorldItemThrowPitchRadians);
    const float verticalSpeed = WorldItemThrowSpeed * std::sin(WorldItemThrowPitchRadians);

    WorldItemState worldItem = {};
    worldItem.worldItemId = m_nextWorldItemId++;
    worldItem.item = item;
    worldItem.objectDescriptionId = objectDescriptionId;
    worldItem.objectSpriteId = objectSpriteId;
    worldItem.objectSpriteFrameIndex = objectSpriteFrameIndex;
    worldItem.objectFlags = objectFlags;
    worldItem.radius = radius;
    worldItem.height = height;
    worldItem.objectName = objectName;
    worldItem.objectSpriteName = objectSpriteName;
    worldItem.attributes = SpriteAttrDroppedByPlayer;
    worldItem.x = sourceX;
    worldItem.y = sourceY;
    worldItem.z = sourceZ;
    worldItem.velocityX = directionX * horizontalSpeed;
    worldItem.velocityY = directionY * horizontalSpeed;
    worldItem.velocityZ = verticalSpeed;
    worldItem.initialX = sourceX;
    worldItem.initialY = sourceY;
    worldItem.initialZ = sourceZ;
    worldItem.spawnedByPlayer = true;
    m_worldItems.push_back(std::move(worldItem));
    return true;
}

void OutdoorWorldRuntime::spawnMonsterDeathDropsForActor(size_t actorIndex, const MapActorState &actor)
{
    if (m_pMonsterTable == nullptr || m_pItemTable == nullptr)
    {
        return;
    }

    if (m_pGameplayActorService != nullptr
        && m_pGameplayActorService->isPartyControlledActor(gameplayActorControlModeFromOutdoor(actor.controlMode)))
    {
        return;
    }

    const std::vector<MonsterTable::MonsterDeathDropEntry> &drops =
        m_pMonsterTable->deathDropsForMonsterId(actor.monsterId);

    const bool leaveCorpse = actorShouldLeaveCorpse(m_pMonsterTable, actor);
    const float dropX = actor.preciseX;
    const float dropY = actor.preciseY;
    const float dropZ = actor.preciseZ + 16.0f;

    if (actor.specialItemId != 0
        && gameplayDebugTraceItemLooksQuestRelevant(actor.specialItemId, m_pItemTable))
    {
        GAMEPLAY_DEBUG_TRACE(
            "actor_quest_item_death scene_kind=outdoor map=\"" + mapName() + "\""
            + " actor_index=" + std::to_string(actorIndex)
            + " actor_id=" + std::to_string(actor.actorId)
            + " monster_id=" + std::to_string(actor.monsterId)
            + " name=\"" + actor.displayName + "\""
            + " delivery=" + std::string(leaveCorpse ? "corpse" : "world_item")
            + " pos=(" + std::to_string(actor.preciseX)
            + "," + std::to_string(actor.preciseY)
            + "," + std::to_string(actor.preciseZ) + ")"
            + " item_id=" + std::to_string(actor.specialItemId)
            + gameplayDebugTraceItemSummary(actor.specialItemId, m_pItemTable));
    }

    if (drops.empty())
    {
        if (leaveCorpse || actor.specialItemId == 0)
        {
            return;
        }
    }

    const uint32_t timeSeed = static_cast<uint32_t>(std::lround(m_gameMinutes * TicksPerSecond));

    if (!leaveCorpse && actor.specialItemId != 0)
    {
        const InventoryItem item =
            ItemGenerator::makeInventoryItem(actor.specialItemId, *m_pItemTable, ItemGenerationMode::Generic);
        spawnMonsterDeathDropWorldItem(
            item,
            dropX,
            dropY,
            dropZ,
            m_sessionChestSeed ^ actor.actorId * 2654435761u ^ actor.specialItemId * 3266489917u ^ timeSeed);
    }

    for (size_t dropIndex = 0; dropIndex < drops.size(); ++dropIndex)
    {
        const MonsterTable::MonsterDeathDropEntry &drop = drops[dropIndex];
        const uint32_t seed =
            m_sessionChestSeed
            ^ actor.actorId * 2654435761u
            ^ static_cast<uint32_t>(std::max<int>(0, actor.monsterId) * 2246822519u)
            ^ drop.itemId * 3266489917u
            ^ static_cast<uint32_t>((dropIndex + 1u) * 668265263u)
            ^ timeSeed;
        std::mt19937 rng(seed);

        if (std::uniform_int_distribution<int>(0, 99)(rng) >= drop.chancePercent)
        {
            continue;
        }

        if (gameplayDebugTraceItemLooksQuestRelevant(drop.itemId, m_pItemTable))
        {
            GAMEPLAY_DEBUG_TRACE(
                "actor_quest_item_death scene_kind=outdoor map=\"" + mapName() + "\""
                + " actor_index=" + std::to_string(actorIndex)
                + " actor_id=" + std::to_string(actor.actorId)
                + " monster_id=" + std::to_string(actor.monsterId)
                + " name=\"" + actor.displayName + "\""
                + " delivery=world_item death_drop_index=" + std::to_string(dropIndex)
                + " pos=(" + std::to_string(actor.preciseX)
                + "," + std::to_string(actor.preciseY)
                + "," + std::to_string(actor.preciseZ) + ")"
                + " item_id=" + std::to_string(drop.itemId)
                + gameplayDebugTraceItemSummary(drop.itemId, m_pItemTable));
        }

        const InventoryItem item =
            ItemGenerator::makeInventoryItem(drop.itemId, *m_pItemTable, ItemGenerationMode::Generic);
        spawnMonsterDeathDropWorldItem(
            item,
            dropX,
            dropY,
            dropZ,
            seed ^ 0x9e3779b9u);
    }
}

bool OutdoorWorldRuntime::spawnMonsterDeathDropWorldItem(
    const InventoryItem &item,
    float x,
    float y,
    float z,
    uint32_t seed)
{
    if (item.objectDescriptionId == 0)
    {
        return false;
    }

    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint32_t lifetimeTicks = 0;
    std::string objectName;
    std::string objectSpriteName;

    if (!resolveWorldItemVisual(
            item.objectDescriptionId,
            objectDescriptionId,
            objectSpriteId,
            objectSpriteFrameIndex,
            objectFlags,
            radius,
            height,
            objectName,
            objectSpriteName))
    {
        return false;
    }

    std::mt19937 rng(seed);
    const float angleRadians = std::uniform_real_distribution<float>(0.0f, Pi * 2.0f)(rng);
    const float speed = static_cast<float>(
        std::uniform_int_distribution<int>(MonsterDeathDropMinThrowSpeed, MonsterDeathDropMaxThrowSpeed)(rng));
    const float horizontalSpeed = speed * std::cos(WorldItemThrowPitchRadians);
    const float verticalSpeed = speed * std::sin(WorldItemThrowPitchRadians);

    WorldItemState worldItem = {};
    worldItem.worldItemId = m_nextWorldItemId++;
    worldItem.item = item;
    worldItem.objectDescriptionId = objectDescriptionId;
    worldItem.objectSpriteId = objectSpriteId;
    worldItem.objectSpriteFrameIndex = objectSpriteFrameIndex;
    worldItem.objectFlags = objectFlags;
    worldItem.radius = radius;
    worldItem.height = height;
    worldItem.objectName = objectName;
    worldItem.objectSpriteName = objectSpriteName;
    worldItem.x = x;
    worldItem.y = y;
    worldItem.z = z;
    worldItem.velocityX = std::cos(angleRadians) * horizontalSpeed;
    worldItem.velocityY = std::sin(angleRadians) * horizontalSpeed;
    worldItem.velocityZ = verticalSpeed;
    worldItem.initialX = x;
    worldItem.initialY = y;
    worldItem.initialZ = z;
    worldItem.lifetimeTicks = lifetimeTicks;
    m_worldItems.push_back(std::move(worldItem));

    if (gameplayDebugTraceItemLooksQuestRelevant(item.objectDescriptionId, m_pItemTable))
    {
        GAMEPLAY_DEBUG_TRACE(
            "world_item_spawned source=monster_death scene_kind=outdoor map=\"" + mapName() + "\""
            + " world_item_index=" + std::to_string(m_worldItems.size() - 1)
            + " item_id=" + std::to_string(item.objectDescriptionId)
            + gameplayDebugTraceItemSummary(item.objectDescriptionId, m_pItemTable)
            + " pos=(" + std::to_string(x)
            + "," + std::to_string(y)
            + "," + std::to_string(z) + ")");
    }

    return true;
}

bool OutdoorWorldRuntime::spawnPartyFireSpikeTrap(
    uint32_t casterMemberIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    float x,
    float y,
    float z)
{
    if (m_pSpellTable == nullptr || m_pObjectTable == nullptr || m_pParty == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr || spellIdFromValue(spellId) != SpellId::FireSpike)
    {
        return false;
    }

    ResolvedProjectileDefinition definition = {};

    if (!resolveSpellDefinition(*pSpellEntry, *m_pObjectTable, definition))
    {
        return false;
    }

    GameplayProjectileService::FireSpikeTrapSpawnLimitInput spawnLimitInput = {};
    spawnLimitInput.sourceKind = ProjectileState::SourceKind::Party;
    spawnLimitInput.sourcePartyMemberIndex = casterMemberIndex;
    spawnLimitInput.skillMastery = skillMastery;
    spawnLimitInput.traps.reserve(m_fireSpikeTraps.size());

    for (const FireSpikeTrapState &trap : m_fireSpikeTraps)
    {
        GameplayProjectileService::FireSpikeActiveTrapFacts trapFacts = {};
        trapFacts.sourceKind = trap.sourceKind;
        trapFacts.sourcePartyMemberIndex = trap.sourcePartyMemberIndex;
        trapFacts.expired = trap.isExpired;
        spawnLimitInput.traps.push_back(trapFacts);
    }

    const GameplayProjectileService::FireSpikeTrapSpawnResult spawnResult =
        projectileService().buildFireSpikeTrapSpawn(spawnLimitInput);

    if (!spawnResult.accepted)
    {
        return false;
    }

    const float supportZ = sampleSupportFloorHeight(x, y, z + 256.0f, 512.0f, 32.0f);
    FireSpikeTrapState trap = {};
    trap.trapId = spawnResult.trapId;
    trap.sourceKind = ProjectileState::SourceKind::Party;
    trap.sourceId = casterMemberIndex + 1;
    trap.sourcePartyMemberIndex = casterMemberIndex;
    trap.objectDescriptionId = definition.objectDescriptionId;
    trap.objectSpriteId = definition.objectSpriteId;
    trap.objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    trap.impactObjectDescriptionId = definition.impactObjectDescriptionId;
    trap.objectFlags = definition.objectFlags | ObjectDescBounce;
    trap.radius = definition.radius;
    trap.height = definition.height;
    trap.spellId = definition.spellId;
    trap.effectSoundId = definition.effectSoundId;
    trap.skillLevel = skillLevel;
    trap.skillMastery = skillMastery;
    trap.objectName = definition.objectName;
    trap.objectSpriteName = definition.objectSpriteName;
    trap.x = x;
    trap.y = y;
    trap.z = supportZ + 1.0f;

    ProjectileState audioSource = {};
    audioSource.sourceKind = trap.sourceKind;
    audioSource.sourceId = trap.sourceId;
    audioSource.effectSoundId = trap.effectSoundId;
    m_fireSpikeTraps.push_back(std::move(trap));

    if (const std::optional<GameplayProjectileService::ProjectileAudioRequest> audioRequest =
            projectileService().buildProjectileReleaseAudioRequest(audioSource, x, y, supportZ))
    {
        pushProjectileAudioEvent(*audioRequest);
    }

    return true;
}

void OutdoorWorldRuntime::updateWorldItems(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || m_pOutdoorMapData == nullptr)
    {
        return;
    }

    for (WorldItemState &worldItem : m_worldItems)
    {
        if (worldItem.isExpired)
        {
            continue;
        }

        worldItem.timeSinceCreatedTicks += static_cast<uint32_t>(std::lround(deltaSeconds * TicksPerSecond));

        if (worldItem.lifetimeTicks > 0 && worldItem.timeSinceCreatedTicks >= worldItem.lifetimeTicks)
        {
            worldItem.isExpired = true;
            continue;
        }

        if (worldItem.velocityX == 0.0f && worldItem.velocityY == 0.0f && worldItem.velocityZ == 0.0f)
        {
            continue;
        }

        if ((worldItem.objectFlags & ObjectDescNoGravity) == 0)
        {
            worldItem.velocityZ -= WorldItemGravity * deltaSeconds;
        }

        worldItem.x += worldItem.velocityX * deltaSeconds;
        worldItem.y += worldItem.velocityY * deltaSeconds;
        worldItem.z += worldItem.velocityZ * deltaSeconds;

        if (isOutdoorTerrainWater(*m_pOutdoorMapData, worldItem.x, worldItem.y))
        {
            worldItem.isExpired = true;
            continue;
        }

        const float terrainFloorZ =
            sampleOutdoorRenderedTerrainHeight(*m_pOutdoorMapData, worldItem.x, worldItem.y) + WorldItemGroundClearance;
        float floorZ = terrainFloorZ;

        if (worldItem.z <= terrainFloorZ + WorldItemSupportFloorProbeHeight)
        {
            const float supportFloorZ =
                sampleOutdoorSupportFloorHeight(*m_pOutdoorMapData, worldItem.x, worldItem.y, worldItem.z)
                + WorldItemGroundClearance;
            floorZ = std::max(floorZ, supportFloorZ);
        }

        if (worldItem.z <= floorZ)
        {
            worldItem.z = floorZ;

            if ((worldItem.objectFlags & ObjectDescBounce) != 0
                && std::abs(worldItem.velocityZ) >= WorldItemBounceStopVelocity)
            {
                worldItem.velocityZ = -worldItem.velocityZ * WorldItemBounceFactor;
            }
            else
            {
                worldItem.velocityZ = 0.0f;
            }

            worldItem.velocityX *= WorldItemGroundDamping;
            worldItem.velocityY *= WorldItemGroundDamping;

            const float horizontalSpeedSquared =
                worldItem.velocityX * worldItem.velocityX + worldItem.velocityY * worldItem.velocityY;

            if (horizontalSpeedSquared < WorldItemRestingHorizontalSpeedSquared)
            {
                worldItem.velocityX = 0.0f;
                worldItem.velocityY = 0.0f;
            }
        }
    }

    m_worldItems.erase(
        std::remove_if(
            m_worldItems.begin(),
            m_worldItems.end(),
            [](const WorldItemState &worldItem)
            {
                return worldItem.isExpired;
            }),
        m_worldItems.end());
}

void OutdoorWorldRuntime::updateFireSpikeTraps(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    for (FireSpikeTrapState &trap : m_fireSpikeTraps)
    {
        if (trap.isExpired)
        {
            continue;
        }

        trap.timeSinceCreatedTicks =
            projectileService().advanceFireSpikeTrapLifetime(trap.timeSinceCreatedTicks, deltaSeconds);

        if (m_pOutdoorMapData != nullptr)
        {
            trap.z = sampleSupportFloorHeight(trap.x, trap.y, trap.z + 64.0f, 128.0f, 24.0f) + 1.0f;
        }

        GameplayProjectileService::FireSpikeTrapTriggerInput triggerInput = {};
        triggerInput.sourceKind = trap.sourceKind;
        triggerInput.trapId = trap.trapId;
        triggerInput.trapRadius = trap.radius;
        triggerInput.skillLevel = trap.skillLevel;
        triggerInput.skillMastery = trap.skillMastery;
        triggerInput.x = trap.x;
        triggerInput.y = trap.y;
        triggerInput.z = trap.z;
        triggerInput.actors.reserve(m_mapActors.size());

        for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
        {
            const MapActorState &actor = m_mapActors[actorIndex];

            GameplayProjectileService::FireSpikeTrapActorFacts actorFacts = {};
            actorFacts.actorIndex = actorIndex;
            actorFacts.actorId = actor.actorId;
            actorFacts.x = actor.preciseX;
            actorFacts.y = actor.preciseY;
            actorFacts.z = actor.preciseZ;
            actorFacts.radius = actor.radius;
            actorFacts.height = actor.height;
            actorFacts.unavailableForCombat = actor.isDead || isActorUnavailableForCombat(actor);
            actorFacts.hostileToParty = actor.hostileToParty;
            actorFacts.friendlyToTrapSource = projectileSourceIsFriendlyToActor(
                ProjectileState{
                    .sourceKind = trap.sourceKind,
                    .sourceId = trap.sourceId,
                    .sourcePartyMemberIndex = trap.sourcePartyMemberIndex,
                    .sourceMonsterId = trap.sourceMonsterId,
                    .fromSummonedMonster = trap.fromSummonedMonster,
                    .ability = trap.ability},
                actor);
            triggerInput.actors.push_back(actorFacts);
        }

        const GameplayProjectileService::FireSpikeTrapTriggerResult triggerResult =
            projectileService().buildFireSpikeTrapTrigger(triggerInput);

        if (triggerResult.triggered)
        {
            applyFireSpikeTrapTriggerResult(trap, triggerResult);
        }
    }

    std::erase_if(
        m_fireSpikeTraps,
        [](const FireSpikeTrapState &trap)
        {
            return trap.isExpired;
        });
}

void OutdoorWorldRuntime::applyFireSpikeTrapTriggerResult(
    FireSpikeTrapState &trap,
    const GameplayProjectileService::FireSpikeTrapTriggerResult &result)
{
    if (!result.triggered || result.actorIndex >= m_mapActors.size())
    {
        return;
    }

    if (result.applyActorImpact)
    {
        const size_t triggeredActorIndex = result.actorIndex;
        const int damage = result.damage;
        const int beforeHp = m_mapActors[triggeredActorIndex].currentHp;

        if (trap.sourceKind == ProjectileState::SourceKind::Party)
        {
            int appliedDamage = damage;
            const MonsterTable::MonsterStatsEntry *pStats =
                m_pMonsterTable != nullptr
                    ? m_pMonsterTable->findStatsById(m_mapActors[triggeredActorIndex].monsterId)
                    : nullptr;
            const CombatDamageType damageType = GameMechanics::spellCombatDamageType(trap.spellId, m_pSpellTable);

            if (pStats != nullptr)
            {
                std::mt19937 rng(
                    trap.trapId
                    ^ static_cast<uint32_t>((triggeredActorIndex + 1) * 2654435761u)
                    ^ static_cast<uint32_t>(std::max(0, damage)));
                appliedDamage = GameMechanics::resolveMonsterIncomingDamage(
                    damage,
                    damageType,
                    monsterResistanceForDamageType(*pStats, damageType),
                    monsterHourOfPowerResistanceBonus(m_mapActors[triggeredActorIndex]),
                    rng);
            }

            applyPartyAttackToMapActor(
                triggeredActorIndex,
                appliedDamage,
                trap.x,
                trap.y,
                trap.z);

            if (m_pGameplayCombatController != nullptr)
            {
                m_pGameplayCombatController->recordPartyProjectileActorImpact(
                    trap.sourceId,
                    trap.sourcePartyMemberIndex,
                    m_mapActors[triggeredActorIndex].actorId,
                    appliedDamage,
                    trap.spellId,
                    true,
                    beforeHp > 0 && m_mapActors[triggeredActorIndex].currentHp <= 0);
            }
        }
        else
        {
            applyMonsterAttackToMapActor(triggeredActorIndex, damage, trap.sourceId);
        }
    }

    if (result.spawnImpactVisual)
    {
        GameplayProjectileService::FireSpikeTrapImpactProjectileInput impactInput = {};
        impactInput.sourceKind = trap.sourceKind;
        impactInput.sourceId = trap.sourceId;
        impactInput.sourcePartyMemberIndex = trap.sourcePartyMemberIndex;
        impactInput.sourceMonsterId = trap.sourceMonsterId;
        impactInput.fromSummonedMonster = trap.fromSummonedMonster;
        impactInput.ability = trap.ability;
        impactInput.objectDescriptionId = trap.objectDescriptionId;
        impactInput.objectSpriteId = trap.objectSpriteId;
        impactInput.objectSpriteFrameIndex = trap.objectSpriteFrameIndex;
        impactInput.impactObjectDescriptionId = trap.impactObjectDescriptionId;
        impactInput.objectFlags = trap.objectFlags;
        impactInput.radius = trap.radius;
        impactInput.height = trap.height;
        impactInput.spellId = trap.spellId;
        impactInput.effectSoundId = trap.effectSoundId;
        impactInput.skillLevel = trap.skillLevel;
        impactInput.skillMastery = trap.skillMastery;
        impactInput.objectName = trap.objectName;
        impactInput.objectSpriteName = trap.objectSpriteName;
        impactInput.x = trap.x;
        impactInput.y = trap.y;
        impactInput.z = trap.z;
        impactInput.damage = result.damage;

        const ProjectileState impactSource = projectileService().buildFireSpikeTrapImpactProjectile(impactInput);
        spawnProjectileImpact(impactSource, trap.x, trap.y, trap.z);
    }

    if (result.expireTrap)
    {
        trap.isExpired = true;
    }
}

bool OutdoorWorldRuntime::isInitialized() const
{
    return m_mapId != 0 || !m_mapName.empty() || m_eventRuntimeState.has_value();
}

void OutdoorWorldRuntime::setBolsterMonstersEnabled(bool enabled)
{
    m_bolsterMonstersEnabled = enabled;
}

void OutdoorWorldRuntime::bindInteractionView(OutdoorGameView *pView)
{
    m_pInteractionView = pView;
}

void OutdoorWorldRuntime::bindGlobalEventProgram(const std::optional<ScriptedEventProgram> *pGlobalEventProgram)
{
    m_pGlobalEventProgram = pGlobalEventProgram;
}

const std::optional<ScriptedEventProgram> *OutdoorWorldRuntime::globalEventProgram() const
{
    return m_pGlobalEventProgram;
}

void OutdoorWorldRuntime::updateWorldMovement(
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput)
{
    (void)allowWorldInput;

    if (m_pInteractionView == nullptr)
    {
        return;
    }

    OutdoorGameplayInputController::updateCameraFromInput(*m_pInteractionView, input, deltaSeconds);
}

void OutdoorWorldRuntime::updateActorAi(float deltaSeconds)
{
    if (!m_actorAiUpdateQueued)
    {
        if (deltaSeconds > 0.0f)
        {
            updateMapActors(deltaSeconds, partyX(), partyY(), partyFootZ());
        }

        return;
    }

    const float queuedDeltaSeconds = m_queuedActorAiDeltaSeconds;
    const float partyX = m_queuedActorAiPartyX;
    const float partyY = m_queuedActorAiPartyY;
    const float partyZ = m_queuedActorAiPartyZ;

    m_actorAiUpdateQueued = false;
    m_queuedActorAiDeltaSeconds = 0.0f;
    m_queuedActorAiPartyX = 0.0f;
    m_queuedActorAiPartyY = 0.0f;
    m_queuedActorAiPartyZ = 0.0f;

    updateMapActors(queuedDeltaSeconds, partyX, partyY, partyZ);
}

void OutdoorWorldRuntime::updateTurnBasedPausedActorAnimations(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    updateProjectiles(deltaSeconds, partyX(), partyY(), partyFootZ());

    const float animationTickDelta = deltaSeconds * TicksPerSecond;
    const std::vector<bool> inactiveActorMask(m_mapActors.size(), false);

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        MapActorState &actor = m_mapActors[actorIndex];
        const InactiveActorDeathFrame deathFrame = resolveInactiveActorDeathFrame(
            actor.isDead,
            actor.currentHp <= 0,
            actor.currentHp <= 0 && actor.aiState == ActorAiState::Dying,
            actor.actionSeconds,
            deltaSeconds);

        if (deathFrame.action == InactiveActorDeathAction::HoldDead)
        {
            actor.aiState = ActorAiState::Dead;
            actor.animation = ActorAnimation::Dead;
            actor.moveDirectionX = 0.0f;
            actor.moveDirectionY = 0.0f;
            actor.actionSeconds = 0.0f;
            actor.attackImpactTriggered = false;
            continue;
        }

        if (deathFrame.action == InactiveActorDeathAction::MarkDead)
        {
            setMapActorDead(actorIndex, true, false);
            continue;
        }

        if (deathFrame.action != InactiveActorDeathAction::AdvanceDying)
        {
            const bool activePresentation =
                actor.aiState == ActorAiState::Stunned
                || actor.aiState == ActorAiState::Attacking
                || actor.animation == ActorAnimation::GotHit
                || actor.animation == ActorAnimation::AttackMelee
                || actor.animation == ActorAnimation::AttackRanged;

            if (activePresentation && actor.actionSeconds > 0.0f)
            {
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.velocityZ = 0.0f;
                actor.animationTimeTicks += animationTickDelta;
                actor.actionSeconds = std::max(0.0f, actor.actionSeconds - deltaSeconds);

                if (actor.actionSeconds <= 0.0f)
                {
                    actor.aiState = ActorAiState::Standing;
                    actor.animation = ActorAnimation::Standing;
                    actor.attackImpactTriggered = false;
                }

                continue;
            }

            updateTurnBasedActorWaitingPresentation(actor, partyX(), partyY(), deltaSeconds, m_pActorSpriteFrameTable);
            continue;
        }

        spawnBloodSplatForActorIfNeeded(actorIndex);
        actor.aiState = ActorAiState::Dying;
        actor.animation = ActorAnimation::Dying;
        actor.animationTimeTicks += animationTickDelta;
        actor.actionSeconds = deathFrame.actionSeconds;
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
        actor.attackImpactTriggered = false;

        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;
        if (pStats != nullptr)
        {
            applyOutdoorActorPhysicsStep(actorIndex, *pStats, inactiveActorMask);
        }

        if (deathFrame.finishedDying)
        {
            setMapActorDead(actorIndex, true, false);
        }
    }
}

size_t OutdoorWorldRuntime::turnBasedPendingWorldActionCount() const
{
    return static_cast<size_t>(
        std::count_if(
            projectileService().projectiles().begin(),
            projectileService().projectiles().end(),
            [](const ProjectileState &projectile)
            {
                return projectile.turnBasedPendingAction && !projectile.isExpired && !projectile.isSettled;
            }));
}

bool OutdoorWorldRuntime::turnBasedActorActionInProgress() const
{
    return std::any_of(
        m_mapActors.begin(),
        m_mapActors.end(),
        [](const MapActorState &actor)
        {
            if (actor.isDead || actor.aiState == ActorAiState::Dead || actor.aiState == ActorAiState::Dying)
            {
                return false;
            }

            const bool activeAttackPresentation =
                actor.aiState == ActorAiState::Attacking
                || actor.animation == ActorAnimation::AttackMelee
                || actor.animation == ActorAnimation::AttackRanged;
            return activeAttackPresentation && actor.actionSeconds > 0.0f;
        });
}

void OutdoorWorldRuntime::stopTurnBasedActorMovement()
{
    size_t stoppedActors = 0;
    size_t skippedTerminalActors = 0;

    for (MapActorState &actor : m_mapActors)
    {
        if (actor.isDead || actor.aiState == ActorAiState::Dead || actor.aiState == ActorAiState::Dying)
        {
            ++skippedTerminalActors;
            continue;
        }

        const bool activeAttackPresentation =
            actor.aiState == ActorAiState::Attacking
            || actor.animation == ActorAnimation::AttackMelee
            || actor.animation == ActorAnimation::AttackRanged;
        if (activeAttackPresentation && actor.actionSeconds > 0.0f)
        {
            actor.moveDirectionX = 0.0f;
            actor.moveDirectionY = 0.0f;
            actor.velocityX = 0.0f;
            actor.velocityY = 0.0f;
            actor.velocityZ = 0.0f;
            ++skippedTerminalActors;
            continue;
        }

        if (actor.aiState != ActorAiState::Standing
            || actor.animation != ActorAnimation::Standing
            || actor.velocityX != 0.0f
            || actor.velocityY != 0.0f
            || actor.velocityZ != 0.0f
            || actor.moveDirectionX != 0.0f
            || actor.moveDirectionY != 0.0f
            || actor.actionSeconds != 0.0f)
        {
            ++stoppedActors;
        }

        actor.aiState = ActorAiState::Standing;
        actor.animation = ActorAnimation::Standing;
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
        actor.velocityZ = 0.0f;
        actor.actionSeconds = 0.0f;
        actor.attackImpactTriggered = false;
    }

    GAMEPLAY_DEBUG_TRACE(
        "turn_based_outdoor_stop_actor_movement actor_count=" + std::to_string(m_mapActors.size())
        + " stopped=" + std::to_string(stoppedActors)
        + " skipped_terminal=" + std::to_string(skippedTerminalActors));
}

void OutdoorWorldRuntime::updateWorld(float deltaSeconds)
{
    if (m_pOutdoorMapDeltaData != nullptr && m_pPartyRuntime != nullptr)
    {
        updateOutdoorJournalRevealMask(*m_pPartyRuntime, *m_pOutdoorMapDeltaData);
    }

    if (!m_eventRuntimeState || m_eventRuntimeState->outdoorModelMechanisms.empty())
    {
        return;
    }

    bool movedAnyMechanism = false;
    bool completedAnyMechanism = false;

    for (const std::pair<const uint32_t, EventRuntimeState::OutdoorModelMechanismDefinition> &entry :
        m_eventRuntimeState->outdoorModelMechanisms)
    {
        std::unordered_map<uint32_t, RuntimeMechanismState>::iterator mechanismIterator =
            m_eventRuntimeState->mechanisms.find(entry.first);

        if (mechanismIterator == m_eventRuntimeState->mechanisms.end())
        {
            continue;
        }

        RuntimeMechanismState &mechanism = mechanismIterator->second;
        const bool wasMoving = mechanism.isMoving;

        if (!mechanism.isMoving)
        {
            continue;
        }

        mechanism.timeSinceTriggeredMs += deltaSeconds * 1000.0f;
        const float moveTimeMs = std::max(1.0f, static_cast<float>(entry.second.moveTimeMs));

        if (mechanism.timeSinceTriggeredMs >= moveTimeMs)
        {
            const float elapsedMs = mechanism.timeSinceTriggeredMs;
            mechanism.timeSinceTriggeredMs = 0.0f;
            mechanism.isMoving = false;

            if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
            {
                mechanism.state = static_cast<uint16_t>(EvtMechanismState::Open);
            }
            else if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
            {
                mechanism.state = static_cast<uint16_t>(EvtMechanismState::Closed);
            }

            GAMEPLAY_DEBUG_TRACE(
                "mechanism_completed kind=outdoor_model id=" + std::to_string(entry.first)
                + " state=" + gameplayDebugTraceMechanismStateName(mechanism.state)
                + " elapsed_seconds=" + std::to_string(elapsedMs / 1000.0f)
                + " model=\"" + entry.second.modelName + "\""
                + " bmodel_index=" + std::to_string(entry.second.bmodelIndex)
                + " move_time_ms=" + std::to_string(entry.second.moveTimeMs)
                + " delta=(" + std::to_string(entry.second.dx) + "," + std::to_string(entry.second.dy)
                + "," + std::to_string(entry.second.dz) + ")"
                + " move_party=" + (entry.second.moveParty ? "true" : "false"));
        }

        movedAnyMechanism = true;
        completedAnyMechanism = completedAnyMechanism || (wasMoving && !mechanism.isMoving);
    }

    if (movedAnyMechanism)
    {
        m_outdoorMechanismGeometryRefreshAccumulatorSeconds += deltaSeconds;

        if (completedAnyMechanism
            || m_outdoorMechanismGeometryRefreshAccumulatorSeconds >= OutdoorMechanismGeometryRefreshStepSeconds)
        {
            refreshOutdoorModelMechanismGeometry();
            m_outdoorMechanismGeometryRefreshAccumulatorSeconds = 0.0f;
        }
    }
}

void OutdoorWorldRuntime::renderWorld(
    int width,
    int height,
    const GameplayInputFrame &input,
    float deltaSeconds)
{
    if (m_pInteractionView != nullptr)
    {
        m_pInteractionView->render(width, height, input, deltaSeconds);
    }
}

GameplayWorldUiRenderState OutdoorWorldRuntime::gameplayUiRenderState(int width, int height) const
{
    if (m_pInteractionView == nullptr)
    {
        return GameplayWorldUiRenderState{.renderGameplayHud = false};
    }

    return m_pInteractionView->gameplayUiRenderState(width, height);
}

bool OutdoorWorldRuntime::requestTravelAutosave()
{
    return m_pInteractionView != nullptr
        && OutdoorInteractionController::requestTravelAutosave(*m_pInteractionView);
}

void OutdoorWorldRuntime::presentPendingEventDialog(size_t previousMessageCount, bool allowNpcFallbackContent)
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::presentPendingEventDialog(
            *m_pInteractionView,
            previousMessageCount,
            allowNpcFallbackContent);
    }
}

void OutdoorWorldRuntime::handleDialogueCloseRequest()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::handleDialogueCloseRequest(*m_pInteractionView);
    }
}

void OutdoorWorldRuntime::executeActiveDialogAction()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::executeActiveDialogAction(*m_pInteractionView);
    }
}

void OutdoorWorldRuntime::openDebugNpcDialogue(uint32_t npcId)
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::openDebugNpcDialogue(*m_pInteractionView, npcId);
    }
}

void OutdoorWorldRuntime::applyGrantedEventItemsToHeldInventory()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(*m_pInteractionView);
    }
}

bool OutdoorWorldRuntime::tryTriggerLocalEventById(uint16_t eventId)
{
    if (m_pInteractionView == nullptr)
    {
        return false;
    }

    return OutdoorInteractionController::tryTriggerLocalEventById(*m_pInteractionView, eventId);
}

int OutdoorWorldRuntime::mapId() const
{
    return m_mapId;
}

const std::string &OutdoorWorldRuntime::mapName() const
{
    return m_mapName;
}

const MonsterTable *OutdoorWorldRuntime::monsterTable() const
{
    return m_pMonsterTable;
}

const MergedBolsterMonsterTable *OutdoorWorldRuntime::mergedBolsterMonsterTable() const
{
    return m_pMergedBolsterMonsterTable;
}

bool OutdoorWorldRuntime::isIndoorMap() const
{
    return false;
}

bool OutdoorWorldRuntime::isUnderwaterMap() const
{
    return m_outdoorWeatherProfile.has_value() && m_outdoorWeatherProfile->underwater;
}

bool OutdoorWorldRuntime::allowsLloydsBeacon() const
{
    return m_map.runtimeRestrictions.allowLloydsBeacon;
}

const std::vector<uint8_t> *OutdoorWorldRuntime::journalMapFullyRevealedCells() const
{
    return m_pOutdoorMapDeltaData != nullptr ? &m_pOutdoorMapDeltaData->fullyRevealedCells : nullptr;
}

const std::vector<uint8_t> *OutdoorWorldRuntime::journalMapPartiallyRevealedCells() const
{
    return m_pOutdoorMapDeltaData != nullptr ? &m_pOutdoorMapDeltaData->partiallyRevealedCells : nullptr;
}

int OutdoorWorldRuntime::restFoodRequired() const
{
    int foodRequired = 2;

    if (m_pPartyRuntime != nullptr)
    {
        const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();

        if (moveState.supportKind == OutdoorSupportKind::Terrain
            && !moveState.airborne
            && !moveState.supportOnWater
            && m_pOutdoorMapData != nullptr)
        {
            const std::string tilesetName = toLowerCopy(m_pOutdoorMapData->groundTilesetName);

            if (tilesetName.find("grass") != std::string::npos || tilesetName.find("gras") != std::string::npos)
            {
                foodRequired = 1;
            }
            else if (tilesetName.find("desert") != std::string::npos
                     || tilesetName.find("dsrt") != std::string::npos
                     || tilesetName.find("sand") != std::string::npos)
            {
                foodRequired = 5;
            }
            else if (tilesetName.find("snow") != std::string::npos
                     || tilesetName.find("snw") != std::string::npos
                     || tilesetName.find("ice") != std::string::npos
                     || tilesetName.find("swamp") != std::string::npos
                     || tilesetName.find("swmp") != std::string::npos)
            {
                foodRequired = 3;
            }
            else if (tilesetName.find("badland") != std::string::npos || tilesetName.find("bad") != std::string::npos)
            {
                foodRequired = 4;
            }
        }

        const Party &partyState = m_pPartyRuntime->party();

        for (const Character &member : partyState.members())
        {
            constexpr uint32_t DragonRaceId = 5;

            if (member.raceId == DragonRaceId)
            {
                ++foodRequired;
                break;
            }
        }
    }

    return std::max(1, foodRequired);
}

OutdoorWorldRuntime::Snapshot OutdoorWorldRuntime::snapshot() const
{
    Snapshot snapshot = {};
    const GameplayProjectileService::Snapshot projectileSnapshot = projectileService().snapshot();
    snapshot.gameMinutes = m_gameMinutes;
    if (m_pOutdoorMapDeltaData != nullptr)
    {
        snapshot.locationInfo = m_pOutdoorMapDeltaData->locationInfo;
    }
    snapshot.atmosphere = m_atmosphereState;
    snapshot.timers = m_timers;
    snapshot.mapActors = m_mapActors;
    snapshot.chests = m_chests;
    snapshot.materializedChestViews = m_materializedChestViews;
    snapshot.activeChestView = m_activeChestView;
    snapshot.eventRuntimeState = m_eventRuntimeState;
    if (snapshot.eventRuntimeState)
    {
        clearTransientEventRuntimeState(*snapshot.eventRuntimeState);
    }
    snapshot.actorUpdateAccumulatorSeconds = m_actorUpdateAccumulatorSeconds;
    snapshot.sessionChestSeed = m_sessionChestSeed;
    snapshot.nextActorId = m_nextActorId;
    snapshot.mapActorCorpseViews = m_mapActorCorpseViews;
    snapshot.activeCorpseView = m_activeCorpseView;
    snapshot.worldItems = m_worldItems;
    snapshot.nextWorldItemId = m_nextWorldItemId;
    snapshot.nextProjectileId = projectileSnapshot.nextProjectileId;
    snapshot.nextProjectileImpactId = projectileSnapshot.nextProjectileImpactId;
    snapshot.nextFireSpikeTrapId = projectileSnapshot.nextFireSpikeTrapId;
    snapshot.gameplayOverlayRemainingSeconds = m_gameplayOverlayRemainingSeconds;
    snapshot.gameplayOverlayDurationSeconds = m_gameplayOverlayDurationSeconds;
    snapshot.gameplayOverlayPeakAlpha = m_gameplayOverlayPeakAlpha;
    snapshot.gameplayOverlayColorAbgr = m_gameplayOverlayColorAbgr;
    snapshot.projectiles = projectileSnapshot.projectiles;
    snapshot.projectileImpacts = projectileSnapshot.projectileImpacts;
    snapshot.fireSpikeTraps = m_fireSpikeTraps;
    snapshot.armageddon = m_armageddonState;
    snapshot.hasRainIntensityOverride = m_hasRainIntensityOverride;
    snapshot.rainIntensityPreset = m_rainIntensityPreset;
    if (m_pOutdoorMapDeltaData != nullptr)
    {
        snapshot.fullyRevealedCells = m_pOutdoorMapDeltaData->fullyRevealedCells;
        snapshot.partiallyRevealedCells = m_pOutdoorMapDeltaData->partiallyRevealedCells;
    }
    snapshot.openedChestFlags.reserve(m_openedChests.size());

    for (bool opened : m_openedChests)
    {
        snapshot.openedChestFlags.push_back(opened ? 1u : 0u);
    }

    return snapshot;
}

void OutdoorWorldRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    GameplayProjectileService::Snapshot projectileSnapshot = {};
    projectileSnapshot.nextProjectileId = snapshot.nextProjectileId;
    projectileSnapshot.nextProjectileImpactId = snapshot.nextProjectileImpactId;
    projectileSnapshot.nextFireSpikeTrapId = snapshot.nextFireSpikeTrapId;
    projectileSnapshot.projectiles = snapshot.projectiles;
    projectileSnapshot.projectileImpacts = snapshot.projectileImpacts;

    m_gameMinutes = snapshot.gameMinutes;
    if (m_pOutdoorMapDeltaData != nullptr)
    {
        m_pOutdoorMapDeltaData->locationInfo = snapshot.locationInfo;
    }
    m_atmosphereState = snapshot.atmosphere;
    m_timers = snapshot.timers;
    m_mapActors = snapshot.mapActors;
    m_chests = snapshot.chests;
    m_materializedChestViews = snapshot.materializedChestViews;
    m_activeChestView = snapshot.activeChestView;
    m_eventRuntimeState = snapshot.eventRuntimeState;
    if (m_eventRuntimeState)
    {
        m_eventRuntimeState->mapFileName = m_map.fileName;
        setActiveHistoryContinent(*m_eventRuntimeState, m_map.mergedContinentId);
        clearTransientEventRuntimeState(*m_eventRuntimeState);
        if (m_pParty != nullptr)
        {
            m_pParty->applyGlobalNpcStateTo(*m_eventRuntimeState);
        }
    }
    m_actorUpdateAccumulatorSeconds = snapshot.actorUpdateAccumulatorSeconds;
    m_sessionChestSeed = snapshot.sessionChestSeed;
    m_nextActorId = snapshot.nextActorId;
    m_mapActorCorpseViews = snapshot.mapActorCorpseViews;
    m_activeCorpseView = snapshot.activeCorpseView;
    m_worldItems = snapshot.worldItems;
    m_nextWorldItemId = snapshot.nextWorldItemId;
    projectileService().restoreSnapshot(projectileSnapshot);
    m_gameplayOverlayRemainingSeconds = snapshot.gameplayOverlayRemainingSeconds;
    m_gameplayOverlayDurationSeconds = snapshot.gameplayOverlayDurationSeconds;
    m_gameplayOverlayPeakAlpha = snapshot.gameplayOverlayPeakAlpha;
    m_gameplayOverlayColorAbgr = snapshot.gameplayOverlayColorAbgr;
    m_fireSpikeTraps = snapshot.fireSpikeTraps;
    m_armageddonState = snapshot.armageddon;
    m_hasRainIntensityOverride = snapshot.hasRainIntensityOverride;
    m_rainIntensityPreset = snapshot.rainIntensityPreset;
    if (m_pOutdoorMapDeltaData != nullptr
        && (!snapshot.fullyRevealedCells.empty() || !snapshot.partiallyRevealedCells.empty()))
    {
        m_pOutdoorMapDeltaData->fullyRevealedCells = snapshot.fullyRevealedCells;
        m_pOutdoorMapDeltaData->partiallyRevealedCells = snapshot.partiallyRevealedCells;
    }
    m_openedChests.clear();
    m_openedChests.reserve(snapshot.openedChestFlags.size());

    for (uint8_t opened : snapshot.openedChestFlags)
    {
        m_openedChests.push_back(opened != 0);
    }

    m_pendingAudioEvents.clear();
    clearPendingCombatEvents();
    refreshAtmosphereState();
    applyEventRuntimeState(true);
}

void OutdoorWorldRuntime::applyMapReentryReset()
{
    for (MapActorState &actor : m_mapActors)
    {
        const bool canAct =
            actor.currentHp > 0
            && actor.aiState != ActorAiState::Dying
            && actor.aiState != ActorAiState::Dead;

        if (!canAct)
        {
            continue;
        }

        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;
        actor.preciseX = actor.homePreciseX;
        actor.preciseY = actor.homePreciseY;
        actor.preciseZ = actor.homePreciseZ;
        actor.x = actor.homeX;
        actor.y = actor.homeY;
        actor.z = actor.homeZ;
        actor.currentHp = std::max(1, actor.maxHp);
        actor.aiState = ActorAiState::Standing;
        actor.animation = ActorAnimation::Standing;
        actor.animationTimeTicks = 0.0f;
        actor.actionSeconds = 0.0f;
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
        actor.velocityZ = 0.0f;
        actor.attackImpactTriggered = false;
        resetCrowdSteeringState(actor);

        if (pStats != nullptr)
        {
            applyOeOutdoorActorFloorCorrection(actor, *pStats);
        }

        if (m_outdoorMovementController)
        {
            const float collisionRadius = actorCollisionRadius(actor, pStats);
            actor.movementState = m_outdoorMovementController->initializeActorStateForBodyPreservingZ(
                actor.preciseX,
                actor.preciseY,
                actor.preciseZ + GroundSnapHeight,
                collisionRadius);
            actor.movementStateInitialized = true;
            actor.movementState.verticalVelocity = actor.velocityZ;
            syncActorFromMovementState(actor);
            actor.velocityX = 0.0f;
            actor.velocityY = 0.0f;
        }
    }

    if (m_pGameplayProjectileService != nullptr)
    {
        m_pGameplayProjectileService->clearActiveProjectiles();
    }
    m_fireSpikeTraps.clear();

    if (m_pObjectTable != nullptr)
    {
        std::erase_if(
            m_worldItems,
            [this](const WorldItemState &worldItem)
            {
                const ObjectEntry *pObjectEntry = m_pObjectTable->get(worldItem.objectDescriptionId);
                return (worldItem.soundId & 8u) != 0
                    || pObjectEntry == nullptr
                    || (pObjectEntry->flags & ObjectDescUnpickable) != 0;
            });
    }

    if (m_outdoorMovementController && m_pMonsterTable != nullptr)
    {
        const std::vector<bool> activeActorMask(m_mapActors.size(), true);
        m_outdoorMovementController->setActorColliders(
            buildNearbyActorMovementColliders(m_mapActors, activeActorMask, *m_pMonsterTable));
    }
}

float OutdoorWorldRuntime::gameMinutes() const
{
    return m_gameMinutes;
}

float OutdoorWorldRuntime::currentGameMinutes() const
{
    return gameMinutes();
}

const OutdoorMapData *OutdoorWorldRuntime::mapData() const
{
    return m_pOutdoorMapData;
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

int OutdoorWorldRuntime::currentLocationReputation() const
{
    if (m_pOutdoorMapDeltaData == nullptr)
    {
        return 0;
    }

    return m_pOutdoorMapDeltaData->locationInfo.reputation;
}

void OutdoorWorldRuntime::setCurrentLocationReputation(int reputation)
{
    reputation = clampReputation(reputation);

    if (m_pOutdoorMapDeltaData == nullptr)
    {
        return;
    }

    m_pOutdoorMapDeltaData->locationInfo.reputation = reputation;

    if (m_eventRuntimeState)
    {
        m_eventRuntimeState->currentLocationReputation = reputation;
    }
}

const OutdoorWorldRuntime::AtmosphereState &OutdoorWorldRuntime::atmosphereState() const
{
    return m_atmosphereState;
}

OutdoorWorldRuntime::RainIntensityPreset OutdoorWorldRuntime::cycleRainIntensityPreset()
{
    m_hasRainIntensityOverride = true;

    switch (m_rainIntensityPreset)
    {
        case RainIntensityPreset::Off:
            m_rainIntensityPreset = RainIntensityPreset::Light;
            break;
        case RainIntensityPreset::Light:
            m_rainIntensityPreset = RainIntensityPreset::Medium;
            break;
        case RainIntensityPreset::Medium:
            m_rainIntensityPreset = RainIntensityPreset::Heavy;
            break;
        case RainIntensityPreset::Heavy:
            m_rainIntensityPreset = RainIntensityPreset::VeryHeavy;
            break;
        case RainIntensityPreset::VeryHeavy:
        default:
            m_rainIntensityPreset = RainIntensityPreset::Off;
            break;
    }

    refreshAtmosphereState();
    return m_rainIntensityPreset;
}

OutdoorWorldRuntime::RainIntensityPreset OutdoorWorldRuntime::rainIntensityPreset() const
{
    return m_rainIntensityPreset;
}

const char *OutdoorWorldRuntime::rainIntensityPresetName() const
{
    return ::OpenYAMM::Game::rainIntensityPresetName(m_rainIntensityPreset);
}

void OutdoorWorldRuntime::advanceGameMinutes(float minutes)
{
    if (minutes <= 0.0f)
    {
        return;
    }

    advanceGameMinutesInternal(minutes);
    refreshAtmosphereState();
}

void OutdoorWorldRuntime::advanceGameMinutesInternal(float minutes)
{
    if (minutes <= 0.0f)
    {
        return;
    }

    const int previousWeatherDay = weatherDayIndexForMinutes(m_gameMinutes);
    m_gameMinutes += minutes;
    const int currentWeatherDay = weatherDayIndexForMinutes(m_gameMinutes);

    if (currentWeatherDay > previousWeatherDay)
    {
        resetDailySpellCounters();
        applyDailyWeatherRollover(currentWeatherDay);
    }
}

void OutdoorWorldRuntime::applyInitialWeatherProfile()
{
    if (!m_outdoorWeatherProfile.has_value())
    {
        return;
    }

    if (applyMergedWeatherProfile())
    {
        return;
    }

    const OutdoorWeatherProfile &profile = *m_outdoorWeatherProfile;

    if (profile.defaultPrecipitation == OutdoorPrecipitationKind::Snow)
    {
        m_atmosphereState.weatherFlags &= ~MapWeatherRaining;
        m_atmosphereState.weatherFlags |= MapWeatherSnowing;
    }
    else if (profile.defaultPrecipitation == OutdoorPrecipitationKind::Rain)
    {
        m_atmosphereState.weatherFlags &= ~MapWeatherSnowing;
        m_atmosphereState.weatherFlags |= MapWeatherRaining;
    }
    else
    {
        m_atmosphereState.weatherFlags &= ~(MapWeatherSnowing | MapWeatherRaining);
    }

    m_atmosphereState.redFog = profile.redFog;
    m_atmosphereState.alwaysDark = profile.alwaysDark;
    m_atmosphereState.alwaysLight = profile.alwaysLight;
    m_atmosphereState.hasFogTint = profile.hasFogTint;
    m_atmosphereState.fogTintRed = profile.fogTintRgb[0];
    m_atmosphereState.fogTintGreen = profile.fogTintRgb[1];
    m_atmosphereState.fogTintBlue = profile.fogTintRgb[2];
    m_atmosphereState.underwater = profile.underwater;

    if (profile.alwaysFoggy)
    {
        applyAlwaysFoggyProfile(m_atmosphereState, profile);
        syncAtmosphereStateToMapDelta();
        return;
    }

    if (profile.fogMode == OutdoorFogMode::DailyRandom)
    {
        if (!hasConfiguredFogState(m_atmosphereState))
        {
            applyDailyWeatherRollover(weatherDayIndexForMinutes(m_gameMinutes));
            return;
        }
    }

    syncAtmosphereStateToMapDelta();
}

bool OutdoorWorldRuntime::applyMergedWeatherProfile()
{
    if (!m_outdoorWeatherProfile.has_value()
        || !m_outdoorWeatherProfile->mergedWeatherConfigured
        || m_outdoorWeatherProfile->mergedMapId != static_cast<uint32_t>(std::max(m_mapId, 0)))
    {
        return false;
    }

    const OutdoorWeatherProfile &profile = *m_outdoorWeatherProfile;
    const int weatherState = mergedWeatherStateForProfile(profile, m_gameMinutes, m_mapId);
    const std::string skyTextureName = mergedSkyTextureNameForProfile(profile, weatherState);

    if (!skyTextureName.empty())
    {
        m_atmosphereState.sourceSkyTextureName = skyTextureName;
        m_atmosphereState.skyTextureName = skyTextureName;
    }

    m_atmosphereState.redFog = profile.redFog;
    m_atmosphereState.alwaysDark = profile.alwaysDark;
    m_atmosphereState.alwaysLight = profile.alwaysLight;
    m_atmosphereState.hasFogTint = profile.hasFogTint;
    m_atmosphereState.fogTintRed = profile.fogTintRgb[0];
    m_atmosphereState.fogTintGreen = profile.fogTintRgb[1];
    m_atmosphereState.fogTintBlue = profile.fogTintRgb[2];
    m_atmosphereState.underwater = profile.underwater;

    if (!profile.mergedWeatherEnabled)
    {
        m_atmosphereState.weatherFlags &= ~(MapWeatherSnowing | MapWeatherRaining);
        m_atmosphereState.rainIntensity = 0.0f;
        applyAlwaysFoggyProfile(m_atmosphereState, profile);
        syncAtmosphereStateToMapDelta();
        return false;
    }

    const int skyCount = static_cast<int>(profile.mergedSkyTextureNames.size());
    const int fogThreshold = skyCount / 3;

    if (weatherState > fogThreshold)
    {
        const int divisor = std::max(weatherState, 1);
        m_atmosphereState.weatherFlags |= MapWeatherFoggy;
        m_atmosphereState.fogWeakDistance = (4096 / divisor) * 2;
        m_atmosphereState.fogStrongDistance = (8096 / divisor) * 2;
    }
    else
    {
        m_atmosphereState.weatherFlags &= ~MapWeatherFoggy;
        m_atmosphereState.fogWeakDistance = 0;
        m_atmosphereState.fogStrongDistance = 0;
    }

    const MergedPrecipitationRoll precipitationRoll =
        mergedPrecipitationRoll(profile, m_mapId, weatherDayIndexForMinutes(m_gameMinutes));

    if (precipitationRoll.snow)
    {
        m_atmosphereState.weatherFlags &= ~MapWeatherRaining;
        m_atmosphereState.weatherFlags |= MapWeatherSnowing;
        m_atmosphereState.rainIntensity = 0.0f;
    }
    else if (precipitationRoll.rain)
    {
        m_atmosphereState.weatherFlags &= ~MapWeatherSnowing;
        m_atmosphereState.weatherFlags |= MapWeatherRaining;
        m_atmosphereState.rainIntensity = rainIntensityValue(precipitationRoll.rainIntensity);
    }
    else
    {
        m_atmosphereState.weatherFlags &= ~(MapWeatherSnowing | MapWeatherRaining);
        m_atmosphereState.rainIntensity = 0.0f;
    }

    applyAlwaysFoggyProfile(m_atmosphereState, profile);
    syncAtmosphereStateToMapDelta();
    return true;
}

void OutdoorWorldRuntime::applyDailyWeatherRollover(int weatherDayIndex)
{
    if (!m_outdoorWeatherProfile.has_value())
    {
        return;
    }

    const OutdoorWeatherProfile &profile = *m_outdoorWeatherProfile;

    if (profile.alwaysFoggy)
    {
        applyFogDistances(fallbackFogDistancesForProfile(profile), true);
        return;
    }

    if (profile.mergedWeatherConfigured
        && profile.mergedMapId == static_cast<uint32_t>(std::max(m_mapId, 0))
        && applyMergedWeatherProfile())
    {
        return;
    }

    if (profile.fogMode != OutdoorFogMode::DailyRandom)
    {
        return;
    }

    const int clampedWeatherDayIndex = std::max(weatherDayIndex, 0);
    uint32_t seed = 0x9e3779b9u;
    seed ^= static_cast<uint32_t>(m_mapId) * 2246822519u;
    seed ^= static_cast<uint32_t>(clampedWeatherDayIndex) * 3266489917u;
    std::mt19937 rng(seed);
    const int roll = std::uniform_int_distribution<int>(0, 99)(rng);
    const int smallThreshold = std::max(profile.smallFogChance, 0);
    const int averageThreshold = smallThreshold + std::max(profile.averageFogChance, 0);
    const int denseThreshold = averageThreshold + std::max(profile.denseFogChance, 0);

    if (roll < smallThreshold)
    {
        applyFogDistances(profile.smallFog, true);
        return;
    }

    if (roll < averageThreshold)
    {
        applyFogDistances(profile.averageFog, true);
        return;
    }

    if (roll < denseThreshold)
    {
        applyFogDistances(profile.denseFog, true);
        return;
    }

    applyFogDistances({}, false);
}

void OutdoorWorldRuntime::applyFogDistances(const OutdoorFogDistances &distances, bool foggy)
{
    if (foggy)
    {
        m_atmosphereState.weatherFlags |= MapWeatherFoggy;
        m_atmosphereState.fogWeakDistance = std::max(distances.weakDistance, 0);
        m_atmosphereState.fogStrongDistance = std::max(distances.strongDistance, 0);
    }
    else
    {
        m_atmosphereState.weatherFlags &= ~MapWeatherFoggy;
        m_atmosphereState.fogWeakDistance = 0;
        m_atmosphereState.fogStrongDistance = 0;
    }

    syncAtmosphereStateToMapDelta();
}

void OutdoorWorldRuntime::syncAtmosphereStateToMapDelta()
{
    if (m_pOutdoorMapDeltaData == nullptr)
    {
        return;
    }

    m_pOutdoorMapDeltaData->locationTime.weatherFlags = m_atmosphereState.weatherFlags;
    m_pOutdoorMapDeltaData->locationTime.fogWeakDistance = m_atmosphereState.fogWeakDistance;
    m_pOutdoorMapDeltaData->locationTime.fogStrongDistance = m_atmosphereState.fogStrongDistance;
}

int OutdoorWorldRuntime::weatherDayIndexForMinutes(float gameMinutes) const
{
    const float safeGameMinutes = std::max(gameMinutes, 0.0f);
    const float shiftedMinutes = safeGameMinutes - 180.0f;
    return static_cast<int>(std::floor(shiftedMinutes / 1440.0f));
}

void OutdoorWorldRuntime::resetDailySpellCounters()
{
    if (m_pParty == nullptr)
    {
        return;
    }

    for (size_t memberIndex = 0; memberIndex < m_pParty->members().size(); ++memberIndex)
    {
        Character *pMember = m_pParty->member(memberIndex);

        if (pMember != nullptr)
        {
            pMember->armageddonCastsToday = 0;
        }
    }
}

void OutdoorWorldRuntime::refreshAtmosphereState()
{
    if (m_outdoorWeatherProfile.has_value())
    {
        m_atmosphereState.redFog = m_outdoorWeatherProfile->redFog;
        m_atmosphereState.alwaysDark = m_outdoorWeatherProfile->alwaysDark;
        m_atmosphereState.alwaysLight = m_outdoorWeatherProfile->alwaysLight;
        m_atmosphereState.hasFogTint = m_outdoorWeatherProfile->hasFogTint;
        m_atmosphereState.fogTintRed = m_outdoorWeatherProfile->fogTintRgb[0];
        m_atmosphereState.fogTintGreen = m_outdoorWeatherProfile->fogTintRgb[1];
        m_atmosphereState.fogTintBlue = m_outdoorWeatherProfile->fogTintRgb[2];
        m_atmosphereState.underwater = m_outdoorWeatherProfile->underwater;

        applyAlwaysFoggyProfile(m_atmosphereState, *m_outdoorWeatherProfile);

        if (m_outdoorWeatherProfile->mergedWeatherConfigured
            && m_outdoorWeatherProfile->mergedMapId == static_cast<uint32_t>(std::max(m_mapId, 0)))
        {
            applyMergedWeatherProfile();
        }
    }

    if (m_eventRuntimeState && m_eventRuntimeState->snowEnabled.has_value())
    {
        if (*m_eventRuntimeState->snowEnabled)
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherRaining;
            m_atmosphereState.weatherFlags |= MapWeatherSnowing;
        }
        else
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherSnowing;
        }
    }

    if (m_eventRuntimeState && m_eventRuntimeState->rainEnabled.has_value())
    {
        if (*m_eventRuntimeState->rainEnabled)
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherSnowing;
            m_atmosphereState.weatherFlags |= MapWeatherRaining;
        }
        else
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherRaining;
        }
    }

    if (m_eventRuntimeState && m_eventRuntimeState->outdoorFogWeakDistanceOverride.has_value())
    {
        m_atmosphereState.weatherFlags |= MapWeatherFoggy;
        m_atmosphereState.fogWeakDistance = *m_eventRuntimeState->outdoorFogWeakDistanceOverride;
        m_atmosphereState.fogStrongDistance =
            m_eventRuntimeState->outdoorFogStrongDistanceOverride.value_or(m_atmosphereState.fogStrongDistance);
    }

    if ((m_atmosphereState.weatherFlags & MapWeatherRaining) != 0)
    {
        if (m_atmosphereState.rainIntensity <= 0.0f)
        {
            m_atmosphereState.rainIntensity = rainIntensityValue(RainIntensityPreset::Medium);
        }
    }
    else
    {
        m_atmosphereState.rainIntensity = 0.0f;
    }

    if (m_hasRainIntensityOverride)
    {
        if (m_rainIntensityPreset != RainIntensityPreset::Off)
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherSnowing;
            m_atmosphereState.weatherFlags |= MapWeatherRaining;
            m_atmosphereState.rainIntensity = rainIntensityValue(m_rainIntensityPreset);
        }
        else
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherRaining;
            m_atmosphereState.rainIntensity = 0.0f;
        }
    }

    const float minutesOfDay = std::fmod(std::max(m_gameMinutes, 0.0f), 1440.0f);

    if (minutesOfDay < 300.0f || minutesOfDay >= 1260.0f)
    {
        m_atmosphereState.isNight = true;
        m_atmosphereState.fogDensity = 1.0f;
    }
    else if (minutesOfDay < 360.0f)
    {
        m_atmosphereState.isNight = false;
        m_atmosphereState.fogDensity = (360.0f - minutesOfDay) / 60.0f;
    }
    else if (minutesOfDay < 1200.0f)
    {
        m_atmosphereState.isNight = false;
        m_atmosphereState.fogDensity = 0.0f;
    }
    else if (minutesOfDay < 1260.0f)
    {
        m_atmosphereState.isNight = false;
        m_atmosphereState.fogDensity = (minutesOfDay - 1200.0f) / 60.0f;
    }
    else
    {
        m_atmosphereState.isNight = true;
        m_atmosphereState.fogDensity = 1.0f;
    }

    if (m_atmosphereState.alwaysLight)
    {
        m_atmosphereState.isNight = false;
        m_atmosphereState.fogDensity = 0.0f;
    }
    else if (m_atmosphereState.alwaysDark)
    {
        m_atmosphereState.isNight = true;
        m_atmosphereState.fogDensity = 1.0f;
    }

    if (m_outdoorWeatherProfile.has_value()
        && m_outdoorWeatherProfile->mergedWeatherConfigured
        && m_outdoorWeatherProfile->mergedMapId == static_cast<uint32_t>(std::max(m_mapId, 0)))
    {
        const int weatherState = mergedWeatherStateForProfile(*m_outdoorWeatherProfile, m_gameMinutes, m_mapId);
        const std::string skyTextureName = mergedSkyTextureNameForProfile(*m_outdoorWeatherProfile, weatherState);
        m_atmosphereState.skyTextureName = !skyTextureName.empty()
            ? skyTextureName
            : m_atmosphereState.sourceSkyTextureName;
    }
    else
    {
        m_atmosphereState.skyTextureName =
            resolveRenderedSkyTextureName(m_atmosphereState.sourceSkyTextureName, minutesOfDay);
    }

    if (m_mapId == DaggerWoundIslandMapId)
    {
        m_atmosphereState.skyTextureName = "sunsetclouds";
    }

    if (m_eventRuntimeState && m_eventRuntimeState->outdoorSkyTextureOverride.has_value())
    {
        m_atmosphereState.sourceSkyTextureName = *m_eventRuntimeState->outdoorSkyTextureOverride;
        m_atmosphereState.skyTextureName = *m_eventRuntimeState->outdoorSkyTextureOverride;
    }

    m_atmosphereState.ambientBrightness = normalizedAmbientBrightness(minutesOfDay);
    const float normalizedBrightness = std::clamp(
        (m_atmosphereState.ambientBrightness - 0.15f) / (0.69f - 0.15f),
        0.0f,
        1.0f);
    m_atmosphereState.darknessOverlayAlpha = (1.0f - normalizedBrightness) * 0.55f;

    if (m_atmosphereState.isNight)
    {
        m_atmosphereState.darknessOverlayColorAbgr = makeAbgr(16, 24, 52);
    }
    else
    {
        const float twilightFactor = std::clamp(m_atmosphereState.fogDensity, 0.0f, 1.0f);
        const uint8_t red = static_cast<uint8_t>(std::clamp(std::lround(92.0f * twilightFactor), 0l, 255l));
        const uint8_t green = static_cast<uint8_t>(std::clamp(std::lround(36.0f * twilightFactor), 0l, 255l));
        const uint8_t blue = static_cast<uint8_t>(std::clamp(std::lround(30.0f * twilightFactor), 0l, 255l));
        m_atmosphereState.darknessOverlayColorAbgr = makeAbgr(red, green, blue);
    }

    m_atmosphereState.gameplayOverlayAlpha = 0.0f;
    m_atmosphereState.gameplayOverlayColorAbgr = m_gameplayOverlayColorAbgr;

    if (minutesOfDay >= 300.0f && minutesOfDay < 1260.0f)
    {
        const float daylightMinutes = minutesOfDay - 300.0f;
        const float sunlightRadians = (daylightMinutes * Pi) / 960.0f;
        m_atmosphereState.sunDirectionX = std::cos(sunlightRadians);
        m_atmosphereState.sunDirectionY = 0.0f;
        m_atmosphereState.sunDirectionZ = std::sin(sunlightRadians);
    }
    else
    {
        m_atmosphereState.sunDirectionX = 0.0f;
        m_atmosphereState.sunDirectionY = 0.0f;
        m_atmosphereState.sunDirectionZ = 1.0f;
    }

    m_atmosphereState.visibilityDistance = DefaultOutdoorVisibilityDistance;

    if (m_atmosphereState.fogStrongDistance > 0 && (m_atmosphereState.weatherFlags & MapWeatherFoggy) != 0)
    {
        m_atmosphereState.visibilityDistance =
            std::min(m_atmosphereState.visibilityDistance, static_cast<float>(m_atmosphereState.fogStrongDistance) * 2.0f);
    }

    if (m_atmosphereState.fogDensity > 0.0f)
    {
        const float dayNightVisibility =
            DefaultOutdoorVisibilityDistance
            - (DefaultOutdoorVisibilityDistance - 24576.0f) * std::min(m_atmosphereState.fogDensity, 1.0f);
        m_atmosphereState.visibilityDistance = std::min(m_atmosphereState.visibilityDistance, dayNightVisibility);
    }

    m_atmosphereState.visibilityDistance = std::max(m_atmosphereState.visibilityDistance, 4096.0f);

    if ((m_atmosphereState.weatherFlags & MapWeatherFoggy) != 0)
    {
        if (m_atmosphereState.underwater)
        {
            m_atmosphereState.clearColorAbgr = underwaterFogColor();
        }
        else if (m_atmosphereState.isNight)
        {
            if (m_atmosphereState.hasFogTint)
            {
                m_atmosphereState.clearColorAbgr = makeTintedFogColor(
                    48,
                    true,
                    m_atmosphereState.fogTintRed,
                    m_atmosphereState.fogTintGreen,
                    m_atmosphereState.fogTintBlue);
            }
            else if (m_atmosphereState.redFog)
            {
                m_atmosphereState.clearColorAbgr = makeAbgr(64, 24, 24);
            }
            else
            {
                m_atmosphereState.clearColorAbgr = makeAbgr(48, 48, 56);
            }
        }
        else
        {
            const uint8_t fogLevel = static_cast<uint8_t>(std::clamp(
                std::lround((1.0f - m_atmosphereState.fogDensity) * 200.0f + m_atmosphereState.fogDensity * 31.0f),
                0l,
                255l));

            if (m_atmosphereState.hasFogTint)
            {
                m_atmosphereState.clearColorAbgr = makeTintedFogColor(
                    fogLevel,
                    true,
                    m_atmosphereState.fogTintRed,
                    m_atmosphereState.fogTintGreen,
                    m_atmosphereState.fogTintBlue);
            }
            else if (m_atmosphereState.redFog)
            {
                const uint8_t green = static_cast<uint8_t>(std::lround(static_cast<float>(fogLevel) * 0.35f));
                const uint8_t blue = static_cast<uint8_t>(std::lround(static_cast<float>(fogLevel) * 0.35f));
                m_atmosphereState.clearColorAbgr = makeAbgr(fogLevel, green, blue);
            }
            else
            {
                m_atmosphereState.clearColorAbgr = makeAbgr(fogLevel, fogLevel, fogLevel);
            }
        }
    }
    else if (m_atmosphereState.isNight)
    {
        m_atmosphereState.clearColorAbgr = makeAbgr(8, 16, 32);
    }
    else
    {
        const float skyBias = std::clamp(normalizedBrightness, 0.0f, 1.0f);
        const float twilightFactor = std::clamp(m_atmosphereState.fogDensity, 0.0f, 1.0f);
        const float dayRed = 24.0f + skyBias * 76.0f;
        const float dayGreen = 48.0f + skyBias * 96.0f;
        const float dayBlue = 84.0f + skyBias * 132.0f;
        const uint8_t red = static_cast<uint8_t>(std::clamp(
            std::lround(dayRed * (1.0f - twilightFactor) + 112.0f * twilightFactor),
            0l,
            255l));
        const uint8_t green = static_cast<uint8_t>(std::clamp(
            std::lround(dayGreen * (1.0f - twilightFactor) + 60.0f * twilightFactor),
            0l,
            255l));
        const uint8_t blue = static_cast<uint8_t>(std::clamp(
            std::lround(dayBlue * (1.0f - twilightFactor) + 72.0f * twilightFactor),
            0l,
            255l));
        m_atmosphereState.clearColorAbgr = makeAbgr(red, green, blue);
    }
}

void OutdoorWorldRuntime::updateGameplayScreenOverlay(float deltaSeconds)
{
    float overlayAlpha = 0.0f;
    uint32_t overlayColor = m_gameplayOverlayColorAbgr;

    if (m_gameplayOverlayRemainingSeconds > 0.0f && m_gameplayOverlayDurationSeconds > 0.0f)
    {
        m_gameplayOverlayRemainingSeconds = std::max(0.0f, m_gameplayOverlayRemainingSeconds - deltaSeconds);
        const float elapsedSeconds = m_gameplayOverlayDurationSeconds - m_gameplayOverlayRemainingSeconds;
        const float normalizedTime =
            std::clamp(elapsedSeconds / m_gameplayOverlayDurationSeconds, 0.0f, 1.0f);
        overlayAlpha = std::sin(normalizedTime * Pi) * m_gameplayOverlayPeakAlpha;
    }

    if (m_armageddonState.active())
    {
        const float armageddonPulse = 0.55f + 0.45f * std::sin(m_armageddonState.remainingSeconds * 12.0f);
        const float armageddonAlpha = 0.24f + 0.14f * armageddonPulse;

        if (armageddonAlpha >= overlayAlpha)
        {
            overlayAlpha = armageddonAlpha;
            overlayColor = makeAbgr(196, 18, 12);
        }
    }

    m_atmosphereState.gameplayOverlayAlpha = overlayAlpha;
    m_atmosphereState.gameplayOverlayColorAbgr = overlayColor;
}

void OutdoorWorldRuntime::updateActorFrameGlobalEffects(
    float deltaSeconds,
    float partyX,
    float partyY,
    float partyZ)
{
    updateGameplayScreenOverlay(deltaSeconds);
    updateArmageddon(deltaSeconds, partyX, partyY, partyZ);
    m_actorUpdateAccumulatorSeconds =
        std::min(m_actorUpdateAccumulatorSeconds + deltaSeconds, MaxAccumulatedActorUpdateSeconds);

}

std::vector<bool> OutdoorWorldRuntime::selectOutdoorActiveActors(float partyX, float partyY, float partyZ) const
{
    std::vector<OutdoorActiveActorCandidate> activeActorCandidates;
    activeActorCandidates.reserve(m_mapActors.size());

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const MapActorState &actor = m_mapActors[actorIndex];
        OutdoorActiveActorCandidate candidate = {};
        candidate.actorIndex = actorIndex;
        candidate.eligible = !actor.isDead && !actor.isInvisible;

        if (candidate.eligible)
        {
            const float deltaX = partyX - actor.preciseX;
            const float deltaY = partyY - actor.preciseY;
            const float deltaZ = partyZ - actor.preciseZ;
            candidate.distanceToParty = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ)
                - static_cast<float>(actor.radius);

            if (candidate.distanceToParty < 0.0f)
            {
                candidate.distanceToParty = 0.0f;
            }
        }

        activeActorCandidates.push_back(candidate);
    }

    return selectOutdoorActiveActorMask(
        activeActorCandidates,
        m_mapActors.size(),
        MaxActiveActorUpdates,
        ActiveActorUpdateRange);
}

ActorAiFrameFacts OutdoorWorldRuntime::collectOutdoorActorAiFrameFacts(
    float deltaSeconds,
    float partyX,
    float partyY,
    float partyZ,
    const std::vector<bool> &activeActorMask) const
{
    ActorAiFrameFacts facts = {};
    facts.deltaSeconds = deltaSeconds;
    facts.fixedStepSeconds = ActorUpdateStepSeconds;
    facts.party.position = GameplayWorldPoint{partyX, partyY, partyZ};
    facts.party.collisionRadius = PartyCollisionRadius;
    facts.party.collisionHeight = PartyCollisionHeight;
    facts.party.invisible = false;
    facts.party.hasDispellableBuffs = partyHasDispellableBuffs(m_pParty);

    std::vector<int8_t> actorLineOfSightCache(m_mapActors.size() * m_mapActors.size(), -1);

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const bool active = actorIndex < activeActorMask.size() && activeActorMask[actorIndex];
        const std::optional<ActorAiFacts> actorFacts =
            collectOutdoorActorAiFacts(actorIndex, active, partyX, partyY, partyZ, actorLineOfSightCache);

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

std::optional<ActorAiFacts> OutdoorWorldRuntime::collectOutdoorActorAiFacts(
    size_t actorIndex,
    bool active,
    float partyX,
    float partyY,
    float partyZ,
    std::vector<int8_t> &actorLineOfSightCache) const
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
    const size_t mapActorCount = m_mapActors.size();
    const auto hasClearOutdoorLineOfSight =
        [this, mapActorCount, &actorLineOfSightCache](
        size_t startActorIndex,
        size_t endActorIndex,
        const bx::Vec3 &start,
        const bx::Vec3 &end) -> bool
    {
        if (startActorIndex >= mapActorCount || endActorIndex >= mapActorCount)
        {
            return this->hasClearOutdoorLineOfSight(start, end);
        }

        const size_t firstActorIndex = std::min(startActorIndex, endActorIndex);
        const size_t secondActorIndex = std::max(startActorIndex, endActorIndex);
        const size_t cacheIndex = firstActorIndex * mapActorCount + secondActorIndex;

        if (cacheIndex >= actorLineOfSightCache.size())
        {
            return this->hasClearOutdoorLineOfSight(start, end);
        }

        int8_t &cachedResult = actorLineOfSightCache[cacheIndex];

        if (cachedResult >= 0)
        {
            return cachedResult != 0;
        }

        const bool hasLineOfSight = this->hasClearOutdoorLineOfSight(start, end);
        cachedResult = hasLineOfSight ? 1 : 0;
        return hasLineOfSight;
    };

    std::vector<OutdoorCombatTargetCandidate> combatCandidates;
    OutdoorTargetFacts combatTarget = {};

    if (active)
    {
        combatCandidates =
            buildCombatTargetCandidates(
                m_pGameplayActorService,
                actor,
                actorIndex,
                m_mapActors);
        combatTarget =
            resolveOutdoorTargetFacts(
                m_pGameplayActorService,
                eventRuntimeState(),
                actor,
                actorIndex,
                combatCandidates,
                partyX,
                partyY,
                partyZ,
                hasClearOutdoorLineOfSight);
    }

    ActorAiFacts facts = {};
    facts.actorIndex = actorIndex;
    facts.actorId = actor.actorId;

    facts.identity.actorId = actor.actorId;
    facts.identity.monsterId = actor.monsterId;
    facts.identity.displayName = actor.displayName;
    facts.identity.group = actor.group;
    facts.identity.ally = actor.ally;
    facts.identity.hostilityType = actor.hostilityType;
    facts.identity.targetPolicy = buildGameplayActorTargetPolicyState(actor);

    facts.stats.aiType = actor.aiType;
    facts.stats.monsterLevel = pStats->level;
    facts.stats.currentHp = actor.currentHp;
    facts.stats.maxHp = actor.maxHp;
    facts.stats.armorClass = effectiveMapActorArmorClass(actorIndex);
    facts.stats.radius = actor.radius;
    facts.stats.height = actor.height;
    facts.stats.moveSpeed = actor.moveSpeed;
    facts.stats.canFly = actor.canFly;
    facts.stats.hasSpell1 = pStats->hasSpell1 || actor.spell1Id != 0;
    facts.stats.hasSpell2 = pStats->hasSpell2 || actor.spell2Id != 0;
    facts.stats.spell1Name = pStats->spell1Name;
    facts.stats.spell2Name = pStats->spell2Name;
    if (actor.spell1Id != 0 && !pStats->hasSpell1 && m_pSpellTable != nullptr)
    {
        if (const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(actor.spell1Id)))
        {
            facts.stats.spell1Name = pSpellEntry->name;
        }
    }
    if (actor.spell2Id != 0 && !pStats->hasSpell2 && m_pSpellTable != nullptr)
    {
        if (const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(actor.spell2Id)))
        {
            facts.stats.spell2Name = pSpellEntry->name;
        }
    }
    facts.stats.attack1DamageType = actor.attack1DamageType;
    facts.stats.attack2DamageType = actor.attack2DamageType;
    facts.stats.spell1Id = actor.spell1Id;
    facts.stats.spell1DamageType = actor.spell1DamageType;
    facts.stats.spell1CastSupported = actor.spell1CastSupported;
    facts.stats.spell2Id = actor.spell2Id;
    facts.stats.spell2DamageType = actor.spell2DamageType;
    facts.stats.spell2CastSupported = actor.spell2CastSupported;
    facts.stats.spell1SkillLevel = actor.spell1SkillLevel;
    facts.stats.spell1SkillMastery = actor.spell1SkillMastery;
    facts.stats.spell2SkillLevel = actor.spell2SkillLevel;
    facts.stats.spell2SkillMastery = actor.spell2SkillMastery;
    facts.stats.spell1UseChance =
        actor.generatedSpell1UseChance > 0 ? actor.generatedSpell1UseChance : pStats->spell1UseChance;
    facts.stats.spell2UseChance =
        actor.generatedSpell2UseChance > 0 ? actor.generatedSpell2UseChance : pStats->spell2UseChance;
    facts.stats.attack2Chance =
        actor.generatedAttack2Chance > 0 ? actor.generatedAttack2Chance : pStats->attack2Chance;
    facts.stats.attack1Damage.diceRolls =
        actor.attack1DamageDiceRolls > 0 ? actor.attack1DamageDiceRolls : pStats->attack1Damage.diceRolls;
    facts.stats.attack1Damage.diceSides =
        actor.attack1DamageDiceSides > 0 ? actor.attack1DamageDiceSides : pStats->attack1Damage.diceSides;
    facts.stats.attack1Damage.bonus = actor.attack1DamageBonus;
    facts.stats.attack2Damage.diceRolls =
        actor.copyAttack1DamageToAttack2
            ? facts.stats.attack1Damage.diceRolls
            : actor.attack2DamageDiceRolls > 0 ? actor.attack2DamageDiceRolls : pStats->attack2Damage.diceRolls;
    facts.stats.attack2Damage.diceSides =
        actor.copyAttack1DamageToAttack2
            ? facts.stats.attack1Damage.diceSides
            : actor.attack2DamageDiceSides > 0 ? actor.attack2DamageDiceSides : pStats->attack2Damage.diceSides;
    facts.stats.attack2Damage.bonus = actor.attack2DamageBonus;
    facts.stats.attackConstraints.attack1IsRanged = pStats->attack1HasMissile;
    facts.stats.attackConstraints.attack2IsRanged = pStats->attack2HasMissile || actor.generatedAttack2IsRanged;
    facts.stats.attack2MissileTypeOverride = actor.generatedAttack2MissileType;
    facts.stats.attackConstraints.blindActive = actor.blindRemainingSeconds > 0.0f;
    facts.stats.attackConstraints.darkGraspActive = actor.darkGraspRemainingSeconds > 0.0f;
    facts.stats.attackConstraints.rangedCommitAllowed = combatTarget.attackLineOfSight;

    facts.runtime.motionState = actorAiMotionStateFromOutdoor(actor.aiState);
    facts.runtime.animationState = actorAiAnimationStateFromOutdoor(actor.animation);
    facts.runtime.queuedAttackAbility = gameplayAttackAbilityFromOutdoor(actor.queuedAttackAbility);
    facts.runtime.animationTimeTicks = actor.animationTimeTicks;
    facts.runtime.recoverySeconds = actor.recoverySeconds;
    facts.runtime.attackAnimationSeconds = actor.attackAnimationSeconds;
    facts.runtime.meleeAttackAnimationSeconds = actorAnimationSeconds(
        m_pActorSpriteFrameTable,
        actor,
        ActorAnimation::AttackMelee,
        actor.attackAnimationSeconds);
    facts.runtime.rangedAttackAnimationSeconds = actorAnimationSeconds(
        m_pActorSpriteFrameTable,
        actor,
        ActorAnimation::AttackRanged,
        actor.attackAnimationSeconds);
    facts.runtime.attackCooldownSeconds = actor.attackCooldownSeconds;
    facts.runtime.idleDecisionSeconds = actor.idleDecisionSeconds;
    facts.runtime.actionSeconds = actor.actionSeconds;
    facts.runtime.crowdSideLockRemainingSeconds = actor.crowdSideLockRemainingSeconds;
    facts.runtime.crowdNoProgressSeconds = actor.crowdNoProgressSeconds;
    facts.runtime.crowdLastEdgeDistance = actor.crowdLastEdgeDistance;
    facts.runtime.crowdRetreatRemainingSeconds = actor.crowdRetreatRemainingSeconds;
    facts.runtime.crowdStandRemainingSeconds = actor.crowdStandRemainingSeconds;
    facts.runtime.crowdProbeEdgeDistance = actor.crowdProbeEdgeDistance;
    facts.runtime.crowdProbeElapsedSeconds = actor.crowdProbeElapsedSeconds;
    facts.runtime.yawRadians = actor.yawRadians;
    facts.runtime.idleDecisionCount = actor.idleDecisionCount;
    facts.runtime.pursueDecisionCount = actor.pursueDecisionCount;
    facts.runtime.attackDecisionCount = actor.attackDecisionCount;
    facts.runtime.crowdEscapeAttempts = actor.crowdEscapeAttempts;
    facts.runtime.crowdSideSign = actor.crowdSideSign;
    facts.runtime.attackImpactTriggered = actor.attackImpactTriggered;

    facts.status.spellEffects = buildGameplayActorSpellEffectState(actor);
    facts.status.invisible = actor.isInvisible;
    facts.status.dead = actor.isDead;
    facts.status.hostileToParty = actor.hostileToParty;
    facts.status.bloodSplatSpawned = actor.bloodSplatSpawned;
    facts.status.hasDetectedParty = actor.hasDetectedParty;
    const int16_t actorRelationMonsterId =
        m_pGameplayActorService->relationMonsterId(actor.monsterId, actor.ally);
    facts.status.defaultHostileToParty = m_pMonsterTable->isHostileToParty(actorRelationMonsterId);
    facts.status.suppressLowHealthFlee = actor.suppressLowHealthFlee;

    facts.target.currentKind = actorAiTargetKindFromOutdoorTarget(combatTarget.kind);
    facts.target.currentActorIndex = combatTarget.actorIndex;
    facts.target.currentRelationToTarget = combatTarget.relationToTarget;
    facts.target.currentPosition = GameplayWorldPoint{combatTarget.targetX, combatTarget.targetY, combatTarget.targetZ};
    facts.target.currentAudioPosition = facts.target.currentPosition;

    const bool partyFlying =
        m_pPartyRuntime != nullptr && m_pPartyRuntime->partyMovementState().flying;
    const bool useOutdoorFlyingRangedPursuitHeight =
        combatTarget.kind == OutdoorTargetKind::Party
        && actor.canFly
        && !partyFlying
        && (facts.stats.attackConstraints.attack1IsRanged || facts.stats.attackConstraints.attack2IsRanged);

    if (useOutdoorFlyingRangedPursuitHeight)
    {
        facts.target.currentMovementPosition = facts.target.currentPosition;
        facts.target.currentMovementPosition.z = partyZ + static_cast<float>(actor.radius) + 512.0f;
        facts.target.hasCurrentMovementPosition = true;
    }

    if (combatTarget.kind == OutdoorTargetKind::Actor
        && combatTarget.actorIndex < m_mapActors.size())
    {
        const MapActorState &targetActor = m_mapActors[combatTarget.actorIndex];
        facts.target.currentHp = targetActor.currentHp;
        facts.target.currentAudioPosition =
        GameplayWorldPoint{
            targetActor.preciseX,
            targetActor.preciseY,
            targetActor.preciseZ + static_cast<float>(targetActor.height) * 0.5f};
    }

    facts.target.currentDistance = combatTarget.distanceToTarget;
    facts.target.currentEdgeDistance = combatTarget.edgeDistance;
    facts.target.currentCanSense = combatTarget.canSense;
    facts.target.currentHasAttackLineOfSight = combatTarget.attackLineOfSight;
    facts.target.partyCanSenseActor = combatTarget.partyCanSense;
    facts.target.candidates.reserve(combatCandidates.size());

    for (const OutdoorCombatTargetCandidate &combatCandidate : combatCandidates)
    {
        ActorTargetCandidateFacts candidate = {};
        candidate.kind = ActorAiTargetKind::Actor;
        candidate.actorIndex = combatCandidate.actorIndex;
        candidate.policy = combatCandidate.policyState;
        candidate.position =
        GameplayWorldPoint{combatCandidate.preciseX, combatCandidate.preciseY, combatCandidate.targetZ};
        candidate.radius = combatCandidate.radius;
        candidate.unavailable = combatCandidate.unavailable;
        candidate.hasLineOfSight = combatCandidate.hasLineOfSight;

        if (combatCandidate.actorIndex < m_mapActors.size())
        {
        const MapActorState &targetActor = m_mapActors[combatCandidate.actorIndex];
        candidate.actorId = targetActor.actorId;
        candidate.monsterId = targetActor.monsterId;
        candidate.currentHp = targetActor.currentHp;
        candidate.height = targetActor.height;
        candidate.audioPosition =
            GameplayWorldPoint{
                targetActor.preciseX,
                targetActor.preciseY,
                targetActor.preciseZ + static_cast<float>(targetActor.height) * 0.5f};
        }

        facts.target.candidates.push_back(candidate);
    }

    facts.movement.position = GameplayWorldPoint{actor.preciseX, actor.preciseY, actor.preciseZ};
    facts.movement.homePosition = GameplayWorldPoint{actor.homePreciseX, actor.homePreciseY, actor.homePreciseZ};
    facts.movement.moveDirectionX = actor.moveDirectionX;
    facts.movement.moveDirectionY = actor.moveDirectionY;
    facts.movement.velocityX = actor.velocityX;
    facts.movement.velocityY = actor.velocityY;
    facts.movement.velocityZ = actor.velocityZ;
    facts.movement.wanderRadius = actor.wanderRadius;
    if (actor.controlMode == ActorControlMode::Reanimated && facts.movement.wanderRadius > 0.0f)
    {
        facts.movement.wanderRadius = std::min(facts.movement.wanderRadius, ReanimatedActorWanderRadius);
    }
    {
        const GameplayActorService *pActorService = m_pGameplayActorService;
        GameplayActorService fallbackActorService = {};

        if (pActorService == nullptr)
        {
            pActorService = &fallbackActorService;
        }

        facts.movement.effectiveMoveSpeed =
            pActorService->effectiveActorMoveSpeed(
                actor.moveSpeed,
                pStats->speed,
                actor.slowMoveMultiplier,
                actor.darkGraspRemainingSeconds > 0.0f);
    }
    facts.movement.distanceToParty = length2d(partyX - actor.preciseX, partyY - actor.preciseY);
    facts.movement.edgeDistanceToParty =
        std::max(0.0f, facts.movement.distanceToParty - static_cast<float>(actor.radius) - PartyCollisionRadius);
    facts.movement.allowIdleWander = m_pGameplayActorService != nullptr;
    facts.movement.movementAllowed =
        pStats->movementType != MonsterTable::MonsterMovementType::Stationary
        && !actor.immobile;
    facts.movement.movementBlocked = false;
    {
        const GameplayActorService *pActorService = m_pGameplayActorService;
        GameplayActorService fallbackActorService = {};

        if (pActorService == nullptr)
        {
            pActorService = &fallbackActorService;
        }

        const bool partyIsVeryNearActor =
            pActorService->partyIsVeryNearActor(
                facts.movement.distanceToParty,
                partyZ - actor.preciseZ,
                actor.radius,
                actor.height,
                PartyCollisionRadius);
        const OutdoorEngagementState engagement =
            resolveOutdoorEngagementState(
                *pActorService,
                facts.identity.targetPolicy,
                combatTarget,
                facts.stats.aiType,
                actor.hostilityType,
                actor.currentHp,
                actor.maxHp,
                actor.hostileToParty,
                partyIsVeryNearActor,
                actor.suppressLowHealthFlee);

        facts.movement.inMeleeRange = engagement.inMeleeRange;
    }

    facts.world.targetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    facts.world.floorZ = actor.preciseZ;
    facts.world.active = active;
    facts.world.activeByDistance = active;

    return facts;
}

void OutdoorWorldRuntime::applyOutdoorActorAiFrameResult(
    const ActorAiFrameResult &result,
    const std::vector<bool> &activeActorMask,
    const GameplayActorAiSystem &actorAiSystem)
{
    std::vector<uint8_t> actorPhysicsApplied;
    if (!m_actorCorpsePhysicsActorIndices.empty())
    {
        actorPhysicsApplied.assign(m_mapActors.size(), 0);
    }

    for (const ActorAiUpdate &update : result.actorUpdates)
    {
        if (update.actorIndex >= m_mapActors.size())
        {
            continue;
        }

        MapActorState &actor = m_mapActors[update.actorIndex];
        const bool activeActor =
        update.actorIndex < activeActorMask.size()
        && activeActorMask[update.actorIndex];
        const MonsterTable::MonsterStatsEntry *pStats =
            activeActor && m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;
        const bool activeBehavior = hasOutdoorActorActiveBehaviorUpdate(update, activeActor);

        if (activeActor && pStats != nullptr)
        {
            ensureOutdoorActorMovementState(actor, *pStats);
        }

        applyOutdoorActorStateUpdate(actor, update.state, activeActor, activeBehavior);
        applyOutdoorActorAnimationUpdate(actor, update.animation, activeActor, activeBehavior);

        if (activeBehavior)
        {
            applyOutdoorActorMovementIntent(
                update.actorIndex,
                actor,
                pStats,
                update.movementIntent,
                activeActorMask,
                actorAiSystem);

            if (!actorPhysicsApplied.empty() && update.movementIntent.applyMovement && pStats != nullptr)
            {
                actorPhysicsApplied[update.actorIndex] = 1;
            }
        }

        if (activeActor)
        {
            syncOutdoorActorIntegerPosition(actor);
            applyOutdoorActorAttackRequest(actor, update.attackRequest);
        }

        applyOutdoorActorTerminalUpdate(update.actorIndex, actor, update);

        if (actorPhysicsApplied.empty() && !m_actorCorpsePhysicsActorIndices.empty())
        {
            actorPhysicsApplied.assign(m_mapActors.size(), 0);
        }

        if (!actorPhysicsApplied.empty()
            && activeBehavior
            && update.movementIntent.applyMovement
            && pStats != nullptr)
        {
            actorPhysicsApplied[update.actorIndex] = 1;
        }

        if (activeActor && pStats != nullptr && !update.movementIntent.applyMovement)
        {
            applyOutdoorActorPhysicsStep(update.actorIndex, *pStats, activeActorMask);

            if (!actorPhysicsApplied.empty())
            {
                actorPhysicsApplied[update.actorIndex] = 1;
            }
        }
    }

    applyOutdoorActorCorpsePhysicsSteps(activeActorMask, actorPhysicsApplied);
    applyOutdoorActorRequests(result, activeActorMask);
}

void OutdoorWorldRuntime::applyOutdoorActorRequests(
    const ActorAiFrameResult &result,
    const std::vector<bool> &activeActorMask)
{
    applyOutdoorActorProjectileRequests(result.projectileRequests, activeActorMask);
    applyOutdoorActorAudioRequests(result.audioRequests);
    applyOutdoorActorFxRequests(result.fxRequests);
}

void OutdoorWorldRuntime::applyOutdoorActorProjectileRequests(
    const std::vector<ActorProjectileRequest> &projectileRequests,
    const std::vector<bool> &activeActorMask)
{
    for (const ActorProjectileRequest &projectileRequest : projectileRequests)
    {
        if (projectileRequest.sourceActorIndex >= m_mapActors.size()
            || projectileRequest.sourceActorIndex >= activeActorMask.size()
            || !activeActorMask[projectileRequest.sourceActorIndex])
        {
            continue;
        }

        const MapActorState &actor = m_mapActors[projectileRequest.sourceActorIndex];
        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;

        if (pStats == nullptr)
        {
            continue;
        }

        if (m_pGameplayCombatController != nullptr)
        {
            m_pGameplayCombatController->recordMonsterRangedRelease(
                actor.actorId,
                projectileRequest.damage,
                projectileRequest.damageType);
        }

        if (isSpellId(projectileRequest.spellId, SpellId::DispelMagic)
            && projectileRequest.targetKind == ActorAiTargetKind::Party
            && m_pParty != nullptr)
        {
            const bool cleared = m_pParty->clearDispellableBuffs();
            if (cleared)
            {
                queuePartySpellFx(eventRuntimeState(), projectileRequest.spellId, m_pParty);
            }
            continue;
        }

        if (projectileRequest.targetKind != ActorAiTargetKind::None)
        {
            spawnProjectileFromMapActor(
                actor,
                *pStats,
                outdoorAttackAbilityFromGameplay(projectileRequest.ability),
                projectileRequest.target.x,
                projectileRequest.target.y,
                projectileRequest.target.z,
                projectileRequest.damage,
                projectileRequest.attackBonus,
                projectileRequest.spellId,
                projectileRequest.skillLevel,
                projectileRequest.skillMastery,
                projectileRequest.projectileTokenOverride);
        }
    }
}

void OutdoorWorldRuntime::applyOutdoorActorAudioRequests(const std::vector<ActorAudioRequest> &audioRequests)
{
    for (const ActorAudioRequest &audioRequest : audioRequests)
    {
        if (audioRequest.actorIndex >= m_mapActors.size())
        {
            continue;
        }

        const MapActorState &actor = m_mapActors[audioRequest.actorIndex];
        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;

        if (pStats == nullptr)
        {
            continue;
        }

        if (audioRequest.kind == ActorAiAudioRequestKind::Bored)
        {
            pushAudioEvent(
                pStats->boredSoundId,
                actor.actorId,
                "monster_bored",
                audioRequest.position.x,
                audioRequest.position.y,
                audioRequest.position.z,
                true,
                SoundScope::World);
        }
        else if (audioRequest.kind == ActorAiAudioRequestKind::Attack)
        {
            pushAudioEvent(
                pStats->attackSoundId,
                actor.actorId,
                "monster_attack",
                audioRequest.position.x,
                audioRequest.position.y,
                audioRequest.position.z,
                true,
                SoundScope::World);
        }
        else if (audioRequest.kind == ActorAiAudioRequestKind::Hit)
        {
            pushAudioEvent(
                pStats->winceSoundId,
                actor.actorId,
                "monster_hit",
                audioRequest.position.x,
                audioRequest.position.y,
                audioRequest.position.z,
                true,
                SoundScope::World);
        }
        else if (audioRequest.kind == ActorAiAudioRequestKind::Death)
        {
            pushAudioEvent(
                pStats->deathSoundId,
                actor.actorId,
                "monster_death",
                audioRequest.position.x,
                audioRequest.position.y,
                audioRequest.position.z,
                true,
                SoundScope::World);
        }
    }
}

void OutdoorWorldRuntime::applyOutdoorActorFxRequests(const std::vector<ActorFxRequest> &fxRequests)
{
    for (const ActorFxRequest &fxRequest : fxRequests)
    {
        if (fxRequest.kind == ActorAiFxRequestKind::Death)
        {
            spawnBloodSplatForActorIfNeeded(fxRequest.actorIndex);
        }
        else if (fxRequest.kind == ActorAiFxRequestKind::Buff
            && fxRequest.actorIndex < m_mapActors.size()
            && m_pWorldFxSystem != nullptr)
        {
            const MapActorState &actor = m_mapActors[fxRequest.actorIndex];
            const uint32_t seed =
                actor.actorId * 2246822519u
                ^ fxRequest.spellId * 3266489917u
                ^ projectileService().allocateProjectileImpactId();
            m_pWorldFxSystem->spawnActorBuffFx(
                fxRequest.spellId,
                seed,
                actor.preciseX,
                actor.preciseY,
                actor.preciseZ,
                static_cast<float>(actor.height),
                std::cos(actor.yawRadians),
                std::sin(actor.yawRadians));

            const SpellEntry *pSpellEntry =
                m_pSpellTable != nullptr ? m_pSpellTable->findById(static_cast<int>(fxRequest.spellId)) : nullptr;

            if (pSpellEntry != nullptr && pSpellEntry->effectSoundId > 0)
            {
                pushAudioEvent(
                    static_cast<uint32_t>(pSpellEntry->effectSoundId),
                    actor.actorId,
                    "monster_buff_spell",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f);
            }
        }
    }
}

bool OutdoorWorldRuntime::hasOutdoorActorActiveBehaviorUpdate(const ActorAiUpdate &update, bool activeActor) const
{
    return activeActor
        && (update.state.motionState
            || update.animation.animationState
            || update.state.queuedAttackAbility
            || update.movementIntent.action != ActorAiMovementAction::None
            || update.movementIntent.updateYaw
            || update.movementIntent.applyMovement);
}

void OutdoorWorldRuntime::ensureOutdoorActorMovementState(
    MapActorState &actor,
    const MonsterTable::MonsterStatsEntry &stats)
{
    if (!m_outdoorMovementController || actor.movementStateInitialized)
    {
        return;
    }

    const float collisionRadius = actorCollisionRadius(actor, &stats);
    actor.movementState = m_outdoorMovementController->initializeActorStateForBodyPreservingZ(
        actor.preciseX,
        actor.preciseY,
        actor.preciseZ + GroundSnapHeight,
        collisionRadius);
    actor.movementStateInitialized = true;
    actor.movementState.verticalVelocity = actor.velocityZ;
    syncActorFromMovementState(actor);
}

void OutdoorWorldRuntime::applyOeOutdoorActorFloorCorrection(
    MapActorState &actor,
    const MonsterTable::MonsterStatsEntry &stats)
{
    if (m_pOutdoorMapData == nullptr || actor.moveSpeed == 0)
    {
        return;
    }

    const float floorZ = sampleOutdoorActorPlacementFloorHeight(
        *m_pOutdoorMapData,
        actor.preciseX,
        actor.preciseY,
        actor.preciseZ,
        std::max(5.0f, static_cast<float>(actor.radius)));

    if (actor.preciseZ >= floorZ)
    {
        return;
    }

    actor.preciseZ = floorZ;
    actor.z = static_cast<int>(std::lround(actor.preciseZ));
    actor.velocityZ = stats.canFly ? 20.0f : 0.0f;

    if (m_outdoorMovementController && actor.movementStateInitialized)
    {
        const float collisionRadius = actorCollisionRadius(actor, &stats);
        actor.movementState = m_outdoorMovementController->initializeActorStateForBodyPreservingZ(
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + GroundSnapHeight,
            collisionRadius);
        actor.movementStateInitialized = true;
        actor.movementState.verticalVelocity = actor.velocityZ;
        syncActorFromMovementState(actor);
    }
}

void OutdoorWorldRuntime::applyOutdoorActorStateUpdate(
    MapActorState &actor,
    const ActorStateUpdate &state,
    bool activeActor,
    bool activeBehavior)
{
    if (state.spellEffects)
    {
        applyGameplayActorSpellEffectState(*state.spellEffects, actor);
    }

    if (state.hostilityType)
    {
        actor.hostilityType = *state.hostilityType;
    }

    if (state.hostileToParty)
    {
        actor.hostileToParty = *state.hostileToParty;
    }

    if (state.hasDetectedParty)
    {
        actor.hasDetectedParty = *state.hasDetectedParty;
    }

    if (state.bloodSplatSpawned)
    {
        actor.bloodSplatSpawned = *state.bloodSplatSpawned;
    }

    if (state.currentHp)
    {
        actor.currentHp = std::clamp(*state.currentHp, 0, std::max(1, actor.maxHp));
    }

    if (!activeActor)
    {
        return;
    }

    if (state.recoverySeconds)
    {
        actor.recoverySeconds = *state.recoverySeconds;
    }

    if (state.idleDecisionSeconds)
    {
        actor.idleDecisionSeconds = *state.idleDecisionSeconds;
    }

    if (state.attackCooldownSeconds)
    {
        actor.attackCooldownSeconds = *state.attackCooldownSeconds;
    }

    if (state.actionSeconds)
    {
        actor.actionSeconds = *state.actionSeconds;
    }

    if (state.attackDecisionCount)
    {
        actor.attackDecisionCount = *state.attackDecisionCount;
    }

    if (state.idleDecisionCount)
    {
        actor.idleDecisionCount = *state.idleDecisionCount;
    }

    if (state.pursueDecisionCount)
    {
        actor.pursueDecisionCount = *state.pursueDecisionCount;
    }

    if (state.crowdSideLockRemainingSeconds)
    {
        actor.crowdSideLockRemainingSeconds = *state.crowdSideLockRemainingSeconds;
    }

    if (state.crowdRetreatRemainingSeconds)
    {
        actor.crowdRetreatRemainingSeconds = *state.crowdRetreatRemainingSeconds;
    }

    if (state.crowdStandRemainingSeconds)
    {
        actor.crowdStandRemainingSeconds = *state.crowdStandRemainingSeconds;
    }

    if (state.attackImpactTriggered)
    {
        actor.attackImpactTriggered = *state.attackImpactTriggered;
    }

    if (!activeBehavior)
    {
        return;
    }

    if (state.motionState)
    {
        actor.aiState = outdoorActorAiStateFromGameplay(*state.motionState);
    }

    if (state.queuedAttackAbility)
    {
        actor.queuedAttackAbility = outdoorAttackAbilityFromGameplay(*state.queuedAttackAbility);
    }
}

void OutdoorWorldRuntime::applyOutdoorActorAnimationUpdate(
    MapActorState &actor,
    const ActorAnimationUpdate &animation,
    bool activeActor,
    bool activeBehavior)
{
    if (!activeActor)
    {
        return;
    }

    const ActorAnimation previousAnimation = actor.animation;

    if (activeBehavior && animation.animationState)
    {
        actor.animation = outdoorActorAnimationFromGameplay(*animation.animationState);
    }

    if (animation.resetOnAnimationChange
        && previousAnimation != actor.animation
        && actor.aiState != ActorAiState::Attacking)
    {
        actor.animationTimeTicks = 0.0f;
    }

    if (animation.animationTimeTicks)
    {
        actor.animationTimeTicks = *animation.animationTimeTicks;
    }

    if (animation.resetAnimationTime)
    {
        actor.animationTimeTicks = 0.0f;
    }
}

void OutdoorWorldRuntime::applyOutdoorActorMovementIntent(
    size_t actorIndex,
    MapActorState &actor,
    const MonsterTable::MonsterStatsEntry *pStats,
    const ActorMovementIntent &movementIntent,
    const std::vector<bool> &activeActorMask,
    const GameplayActorAiSystem &actorAiSystem)
{
    if (movementIntent.action != ActorAiMovementAction::None)
    {
        actor.moveDirectionX = movementIntent.moveDirectionX;
        actor.moveDirectionY = movementIntent.moveDirectionY;
    }

    if (movementIntent.updateYaw)
    {
        actor.yawRadians = movementIntent.yawRadians;
    }

    if (movementIntent.resetCrowdSteering)
    {
        resetCrowdSteeringState(actor);
    }

    if (movementIntent.clearVelocity
        && !outdoorActorIsTerminalCorpse(actor)
        && actor.aiState != ActorAiState::Dying
        && actor.aiState != ActorAiState::Dead
        && actor.aiState != ActorAiState::Stunned)
    {
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;

        if (pStats == nullptr
            || pStats->canFly
            || !actor.movementState.airborne
            || actor.aiState == ActorAiState::Dead)
        {
            actor.velocityZ = 0.0f;
        }
    }

    if (!movementIntent.applyMovement || pStats == nullptr)
    {
        return;
    }

    ActorAiState nextAiState = actor.aiState;
    ActorAnimation nextAnimation = actor.animation;
    float desiredMoveX = movementIntent.desiredMoveX;
    float desiredMoveY = movementIntent.desiredMoveY;

    applyOutdoorActorMovementIntegration(
        actorIndex,
        pStats,
        activeActorMask,
        movementIntent.moveSpeed,
        movementIntent.desiredMoveZ,
        movementIntent.meleePursuitActive,
        movementIntent.inMeleeRange,
        movementIntent.targetPosition,
        movementIntent.targetEdgeDistance,
        actorAiSystem,
        nextAiState,
        nextAnimation,
        desiredMoveX,
        desiredMoveY);
}

void OutdoorWorldRuntime::applyOutdoorActorAttackRequest(
    MapActorState &actor,
    const std::optional<ActorAttackRequest> &attackRequest)
{
    if (!attackRequest)
    {
        return;
    }

    if (attackRequest->kind == ActorAiAttackRequestKind::PartyMelee)
    {
        if (!outdoorActorCanApplyPartyMeleeImpact(actor))
        {
            return;
        }

        if (m_pGameplayCombatController != nullptr)
        {
            m_pGameplayCombatController->recordMonsterMeleeImpact(
                actor.actorId,
                attackRequest->damage,
                attackRequest->attackBonus,
                attackRequest->damageType,
                attackRequest->ability);
        }
    }
    else if (attackRequest->kind == ActorAiAttackRequestKind::ActorMelee)
    {
        applyMonsterActorMeleeAttackToMapActor(
            attackRequest->targetActorIndex,
            attackRequest->damage,
            actor.actorId,
            attackRequest->attackBonus,
            attackRequest->damageType);
    }
}

bool OutdoorWorldRuntime::outdoorActorCanApplyPartyMeleeImpact(const MapActorState &actor) const
{
    if (m_pPartyRuntime == nullptr || actor.isDead || actor.currentHp <= 0)
    {
        return false;
    }

    const OutdoorMoveState &partyMoveState = m_pPartyRuntime->movementState();
    const float actorTargetZ =
        actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    const float partyTargetZ = partyMoveState.footZ + PartyTargetHeightOffset;
    const float deltaX = partyMoveState.x - actor.preciseX;
    const float deltaY = partyMoveState.y - actor.preciseY;
    const float deltaZ = partyTargetZ - actorTargetZ;
    const float edgeDistance =
        std::max(
            0.0f,
            length3d(deltaX, deltaY, deltaZ)
                - static_cast<float>(actor.radius)
                - PartyCollisionRadius);

    if (edgeDistance > ActorMeleeRange)
    {
        return false;
    }

    return hasClearOutdoorLineOfSight(
        bx::Vec3{actor.preciseX, actor.preciseY, actorTargetZ},
        bx::Vec3{partyMoveState.x, partyMoveState.y, partyTargetZ});
}

void OutdoorWorldRuntime::applyOutdoorActorTerminalUpdate(
    size_t actorIndex,
    MapActorState &actor,
    const ActorAiUpdate &update)
{
    const bool terminalActor =
        actor.isDead
        || actor.currentHp <= 0
        || actor.aiState == ActorAiState::Dying
        || actor.aiState == ActorAiState::Dead;

    if (!terminalActor)
    {
        return;
    }

    resetCrowdSteeringState(actor);

    if (update.movementIntent.clearVelocity
        && actor.aiState != ActorAiState::Dying
        && actor.aiState != ActorAiState::Dead
        && actor.aiState != ActorAiState::Stunned)
    {
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
    }

    if (update.state.attackImpactTriggered)
    {
        actor.attackImpactTriggered = *update.state.attackImpactTriggered;
    }
    else
    {
        actor.attackImpactTriggered = false;
    }

    if (update.state.dead && *update.state.dead)
    {
        setMapActorDead(actorIndex, true, false);
        return;
    }

    if (update.state.motionState)
    {
        actor.aiState = outdoorActorAiStateFromGameplay(*update.state.motionState);
    }

    if (update.animation.animationState)
    {
        actor.animation = outdoorActorAnimationFromGameplay(*update.animation.animationState);
    }

    if (update.animation.animationTimeTicks)
    {
        actor.animationTimeTicks = *update.animation.animationTimeTicks;
    }

    if (update.state.actionSeconds)
    {
        actor.actionSeconds = *update.state.actionSeconds;
    }

    syncOutdoorActorIntegerPosition(actor);
}

void OutdoorWorldRuntime::syncOutdoorActorIntegerPosition(MapActorState &actor) const
{
    actor.x = static_cast<int>(std::lround(actor.preciseX));
    actor.y = static_cast<int>(std::lround(actor.preciseY));
    actor.z = static_cast<int>(std::lround(actor.preciseZ));
}

void OutdoorWorldRuntime::activateOutdoorActorCorpsePhysics(size_t actorIndex)
{
    if (actorIndex >= m_mapActors.size())
    {
        return;
    }

    MapActorState &actor = m_mapActors[actorIndex];
    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;

    if (pStats != nullptr && pStats->canFly && m_outdoorMovementController)
    {
        ensureOutdoorActorMovementState(actor, *pStats);
        actor.movementState.airborne = true;
    }

    if (std::find(
            m_actorCorpsePhysicsActorIndices.begin(),
            m_actorCorpsePhysicsActorIndices.end(),
            actorIndex)
        == m_actorCorpsePhysicsActorIndices.end())
    {
        m_actorCorpsePhysicsActorIndices.push_back(actorIndex);
    }
}

void OutdoorWorldRuntime::applyOutdoorActorCorpsePhysicsSteps(
    const std::vector<bool> &activeActorMask,
    const std::vector<uint8_t> &actorPhysicsApplied)
{
    if (m_actorCorpsePhysicsActorIndices.empty())
    {
        return;
    }

    if (m_outdoorMovementController && m_pMonsterTable != nullptr)
    {
        m_outdoorMovementController->setActorColliders(
            buildNearbyActorMovementColliders(m_mapActors, activeActorMask, *m_pMonsterTable));
    }

    size_t writeIndex = 0;

    for (size_t actorIndex : m_actorCorpsePhysicsActorIndices)
    {
        if (actorIndex >= m_mapActors.size() || m_pMonsterTable == nullptr)
        {
            continue;
        }

        MapActorState &actor = m_mapActors[actorIndex];

        if (!outdoorActorCorpsePhysicsNeedsStep(actor))
        {
            continue;
        }

        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats == nullptr)
        {
            continue;
        }

        const bool alreadyApplied =
            actorIndex < actorPhysicsApplied.size() && actorPhysicsApplied[actorIndex] != 0;

        if (!alreadyApplied)
        {
            applyOutdoorActorPhysicsStep(actorIndex, *pStats, activeActorMask, false);
        }

        if (outdoorActorCorpsePhysicsNeedsStep(actor))
        {
            m_actorCorpsePhysicsActorIndices[writeIndex] = actorIndex;
            ++writeIndex;
        }
    }

    m_actorCorpsePhysicsActorIndices.resize(writeIndex);
}

bool OutdoorWorldRuntime::applyOutdoorActorPhysicsStep(
    size_t actorIndex,
    const MonsterTable::MonsterStatsEntry &stats,
    const std::vector<bool> &activeActorMask,
    bool refreshActorColliders)
{
    if (actorIndex >= m_mapActors.size() || !m_outdoorMovementController || m_pMonsterTable == nullptr)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];
    ensureOutdoorActorMovementState(actor, stats);

    const bool terminalCorpse = outdoorActorIsTerminalCorpse(actor);
    const bool actorCanFly = stats.canFly && !terminalCorpse;
    const bool airborne = !actorCanFly && actor.movementState.airborne;
    const bool hasVelocity =
        std::abs(actor.velocityX) > 0.001f
        || std::abs(actor.velocityY) > 0.001f
        || std::abs(actor.velocityZ) > 0.001f;

    if (!airborne && !hasVelocity)
    {
        return false;
    }

    if (refreshActorColliders)
    {
        m_outdoorMovementController->setActorColliders(
            buildNearbyActorMovementColliders(m_mapActors, activeActorMask, *m_pMonsterTable));
    }
    std::vector<size_t> contactedActorIndices;
    const float collisionRadius = actorCollisionRadius(actor, &stats);
    bx::Vec3 resolvedVelocity = {actor.velocityX, actor.velocityY, actor.velocityZ};
    actor.movementState = m_outdoorMovementController->resolveOutdoorActorMove(
        actor.movementState,
        OutdoorBodyDimensions{collisionRadius, actorCollisionHeight(actor, collisionRadius)},
        actor.velocityX,
        actor.velocityY,
        actor.velocityZ,
        actorCanFly,
        ActorUpdateStepSeconds,
        &contactedActorIndices,
        OutdoorIgnoredActorCollider{OutdoorActorCollisionSource::MapDelta, actorIndex},
        &resolvedVelocity);
    syncActorFromMovementState(actor);
    applyResolvedActorHorizontalVelocity(actor, resolvedVelocity, false);
    actor.velocityZ = actor.movementState.verticalVelocity;
    const float inertiaDecay = actorInertiaDecayForStep(ActorUpdateStepSeconds);
    actor.velocityX *= inertiaDecay;
    actor.velocityY *= inertiaDecay;

    if (actorCanFly)
    {
        actor.velocityZ *= inertiaDecay;
    }

    if (actor.velocityX * actor.velocityX + actor.velocityY * actor.velocityY < ActorStopVelocitySquared)
    {
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
    }

    if ((actorCanFly || (terminalCorpse && !actor.movementState.airborne))
        && actor.velocityZ * actor.velocityZ < ActorStopVelocitySquared)
    {
        actor.velocityZ = 0.0f;
    }

    if (!terminalCorpse && actor.movementState.airborne)
    {
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
    }

    return true;
}

void OutdoorWorldRuntime::applyOutdoorActorPostMovementAiUpdate(
    MapActorState &actor,
    const ActorAiUpdate &movementUpdate,
    float &desiredMoveX,
    float &desiredMoveY)
{
    if (movementUpdate.state.pursueDecisionCount)
    {
        actor.pursueDecisionCount = *movementUpdate.state.pursueDecisionCount;
    }

    if (movementUpdate.state.crowdSideLockRemainingSeconds)
    {
        actor.crowdSideLockRemainingSeconds = *movementUpdate.state.crowdSideLockRemainingSeconds;
    }

    if (movementUpdate.state.crowdNoProgressSeconds)
    {
        actor.crowdNoProgressSeconds = *movementUpdate.state.crowdNoProgressSeconds;
    }

    if (movementUpdate.state.crowdLastEdgeDistance)
    {
        actor.crowdLastEdgeDistance = *movementUpdate.state.crowdLastEdgeDistance;
    }

    if (movementUpdate.state.crowdRetreatRemainingSeconds)
    {
        actor.crowdRetreatRemainingSeconds = *movementUpdate.state.crowdRetreatRemainingSeconds;
    }

    if (movementUpdate.state.crowdStandRemainingSeconds)
    {
        actor.crowdStandRemainingSeconds = *movementUpdate.state.crowdStandRemainingSeconds;
    }

    if (movementUpdate.state.crowdProbeEdgeDistance)
    {
        actor.crowdProbeEdgeDistance = *movementUpdate.state.crowdProbeEdgeDistance;
    }

    if (movementUpdate.state.crowdProbeElapsedSeconds)
    {
        actor.crowdProbeElapsedSeconds = *movementUpdate.state.crowdProbeElapsedSeconds;
    }

    if (movementUpdate.state.crowdEscapeAttempts)
    {
        actor.crowdEscapeAttempts = *movementUpdate.state.crowdEscapeAttempts;
    }

    if (movementUpdate.state.crowdSideSign)
    {
        actor.crowdSideSign = *movementUpdate.state.crowdSideSign;
    }

    if (movementUpdate.movementIntent.updateCrowdProbePosition)
    {
        actor.crowdProbeX = actor.preciseX;
        actor.crowdProbeY = actor.preciseY;
        desiredMoveX = movementUpdate.movementIntent.desiredMoveX;
        desiredMoveY = movementUpdate.movementIntent.desiredMoveY;
    }

    if (movementUpdate.movementIntent.clearVelocity)
    {
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
    }

    if (movementUpdate.movementIntent.action == ActorAiMovementAction::Stand
        || movementUpdate.movementIntent.action == ActorAiMovementAction::Pursue
        || movementUpdate.movementIntent.action == ActorAiMovementAction::Flee)
    {
        actor.moveDirectionX = movementUpdate.movementIntent.moveDirectionX;
        actor.moveDirectionY = movementUpdate.movementIntent.moveDirectionY;
    }

    if (movementUpdate.movementIntent.updateYaw)
    {
        actor.yawRadians = movementUpdate.movementIntent.yawRadians;
    }

    if (movementUpdate.state.actionSeconds)
    {
        actor.actionSeconds = *movementUpdate.state.actionSeconds;
    }

    if (movementUpdate.state.motionState)
    {
        actor.aiState = outdoorActorAiStateFromGameplay(*movementUpdate.state.motionState);
    }

    if (movementUpdate.animation.animationState)
    {
        actor.animation = outdoorActorAnimationFromGameplay(*movementUpdate.animation.animationState);
    }

    if (movementUpdate.animation.animationTimeTicks)
    {
        actor.animationTimeTicks = *movementUpdate.animation.animationTimeTicks;
    }

    if (movementUpdate.state.idleDecisionSeconds)
    {
        actor.idleDecisionSeconds = *movementUpdate.state.idleDecisionSeconds;
    }

    if (movementUpdate.state.attackImpactTriggered)
    {
        actor.attackImpactTriggered = *movementUpdate.state.attackImpactTriggered;
    }
}

void OutdoorWorldRuntime::applyOutdoorActorMovementIntegration(
    size_t actorIndex,
    const MonsterTable::MonsterStatsEntry *pStats,
    const std::vector<bool> &activeActorMask,
    float moveSpeed,
    float desiredMoveZ,
    bool meleePursuitActive,
    bool inMeleeRange,
    const GameplayWorldPoint &targetPosition,
    float targetEdgeDistance,
    const GameplayActorAiSystem &actorAiSystem,
    ActorAiState &nextAiState,
    ActorAnimation &nextAnimation,
    float &desiredMoveX,
    float &desiredMoveY)
{
    if (actorIndex >= m_mapActors.size() || pStats == nullptr)
    {
        return;
    }

    MapActorState &actor = m_mapActors[actorIndex];

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

    float effectiveDesiredMoveZ = desiredMoveZ;

    if (pStats->canFly && std::abs(effectiveDesiredMoveZ) <= 0.001f)
    {
        const float actorTargetZ =
            actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
        const float verticalTargetDelta = targetPosition.z - actorTargetZ;

        if (std::abs(verticalTargetDelta) > 8.0f)
        {
            const float horizontalDistance =
                length2d(targetPosition.x - actor.preciseX, targetPosition.y - actor.preciseY);
            const float distance = length3d(horizontalDistance, 0.0f, verticalTargetDelta);

            if (distance > 0.001f)
            {
                effectiveDesiredMoveZ = std::clamp(verticalTargetDelta / distance, -1.0f, 1.0f);
            }
        }
    }

    actor.velocityX = desiredMoveX * moveSpeed;
    actor.velocityY = desiredMoveY * moveSpeed;
    actor.velocityZ = pStats->canFly ? effectiveDesiredMoveZ * moveSpeed : 0.0f;

    if (m_pOutdoorMapData != nullptr)
    {
        applyOeOutdoorSteepSlopeResponse(actor, *m_pOutdoorMapData, pStats);
    }

    const float moveDeltaX = actor.velocityX * ActorUpdateStepSeconds;
    const float moveDeltaY = actor.velocityY * ActorUpdateStepSeconds;
    bool moved = false;
    size_t contactedActorCount = 0;
    std::vector<size_t> contactedActorIndices;

    if (m_outdoorMovementController && actor.movementStateInitialized && m_pMonsterTable != nullptr)
    {
        m_outdoorMovementController->setActorColliders(
            buildNearbyActorMovementColliders(m_mapActors, activeActorMask, *m_pMonsterTable));
        const float collisionRadius = actorCollisionRadius(actor, pStats);
        const float collisionHeight = actorCollisionHeight(actor, collisionRadius);
        bx::Vec3 resolvedVelocity = {actor.velocityX, actor.velocityY, actor.velocityZ};
        bool resolvedVelocityUpdatesYaw = false;
        actor.movementState = m_outdoorMovementController->resolveOutdoorActorMove(
            actor.movementState,
            OutdoorBodyDimensions{collisionRadius, collisionHeight},
            actor.velocityX,
            actor.velocityY,
            actor.velocityZ,
            pStats->canFly,
            ActorUpdateStepSeconds,
            &contactedActorIndices,
            OutdoorIgnoredActorCollider{OutdoorActorCollisionSource::MapDelta, actorIndex},
            &resolvedVelocity,
            &resolvedVelocityUpdatesYaw);
        syncActorFromMovementState(actor);
        applyResolvedActorHorizontalVelocity(actor, resolvedVelocity, resolvedVelocityUpdatesYaw);
        actor.velocityZ = actor.movementState.verticalVelocity;
        moved = true;

        std::sort(contactedActorIndices.begin(), contactedActorIndices.end());
        contactedActorCount = static_cast<size_t>(
            std::distance(
                contactedActorIndices.begin(),
                std::unique(contactedActorIndices.begin(), contactedActorIndices.end())));
    }
    else
    {
        if (m_pOutdoorMapData != nullptr)
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
            moved = tryMoveActorInWorld(
                actor,
                *m_pOutdoorMapData,
                m_outdoorFaces,
                pStats,
                moveDeltaX,
                0.0f);
        }

        if (!moved && std::abs(moveDeltaY) > 0.001f)
        {
            moved = tryMoveActorInWorld(
                actor,
                *m_pOutdoorMapData,
                m_outdoorFaces,
                pStats,
                0.0f,
                moveDeltaY);
        }
        }
        else
        {
        actor.preciseX += moveDeltaX;
        actor.preciseY += moveDeltaY;
        moved = true;
        }
    }

    ActorAiFacts movementFacts = {};
    movementFacts.actorIndex = actorIndex;
    movementFacts.actorId = actor.actorId;
    movementFacts.identity.hostilityType = actor.hostilityType;
    movementFacts.stats.canFly = pStats->canFly;
    movementFacts.runtime.motionState = actorAiMotionStateFromOutdoor(actor.aiState);
    movementFacts.runtime.actionSeconds = actor.actionSeconds;
    movementFacts.runtime.crowdNoProgressSeconds = actor.crowdNoProgressSeconds;
    movementFacts.runtime.crowdLastEdgeDistance = actor.crowdLastEdgeDistance;
    movementFacts.runtime.crowdRetreatRemainingSeconds = actor.crowdRetreatRemainingSeconds;
    movementFacts.runtime.crowdStandRemainingSeconds = actor.crowdStandRemainingSeconds;
    movementFacts.runtime.crowdProbeEdgeDistance = actor.crowdProbeEdgeDistance;
    movementFacts.runtime.crowdProbeElapsedSeconds = actor.crowdProbeElapsedSeconds;
    movementFacts.runtime.pursueDecisionCount = actor.pursueDecisionCount;
    movementFacts.runtime.crowdEscapeAttempts = actor.crowdEscapeAttempts;
    movementFacts.runtime.crowdSideSign = actor.crowdSideSign;
    movementFacts.movement.position = GameplayWorldPoint{actor.preciseX, actor.preciseY, actor.preciseZ};
    movementFacts.movement.contactedActorCount = contactedActorCount;

    if (!contactedActorIndices.empty())
    {
        const size_t contactedActorIndex = contactedActorIndices.front();

        if (contactedActorIndex < m_mapActors.size())
        {
            const MapActorState &contactedActor = m_mapActors[contactedActorIndex];
            movementFacts.movement.hasContactedActor = true;
            movementFacts.movement.contactedActorHostilityType = contactedActor.hostilityType;
            movementFacts.movement.contactedActorPosition =
                GameplayWorldPoint{contactedActor.preciseX, contactedActor.preciseY, contactedActor.preciseZ};
        }
    }

    movementFacts.movement.meleePursuitActive = meleePursuitActive;
    movementFacts.movement.inMeleeRange = inMeleeRange;
    movementFacts.movement.allowCrowdSteering = m_pGameplayActorService != nullptr;
    movementFacts.movement.crowdSteeringTriggersOnMovementBlocked = false;
    movementFacts.movement.crowdSidestepAngleRadians = Pi * 0.30555556f;
    movementFacts.movement.crowdRetreatAngleRadians = Pi * 0.53f;
    movementFacts.movement.movementBlocked = !moved;
    movementFacts.target.currentPosition = targetPosition;
    movementFacts.target.currentEdgeDistance = targetEdgeDistance;
    const ActorAiUpdate movementUpdate = actorAiSystem.updateActorAfterWorldMovement(movementFacts);
    applyOutdoorActorPostMovementAiUpdate(actor, movementUpdate, desiredMoveX, desiredMoveY);
}

void OutdoorWorldRuntime::updateOutdoorInactiveAndInvalidActors(
    float partyX,
    float partyY,
    float partyZ,
    const std::vector<bool> &activeActorMask)
{
    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        MapActorState &actor = m_mapActors[actorIndex];
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats == nullptr)
        {
            const InactiveActorDeathFrame earlyDeathFrame = resolveInactiveActorDeathFrame(
                actor.isDead,
                actor.currentHp <= 0,
                actor.currentHp <= 0 && actor.aiState == ActorAiState::Dying,
                actor.actionSeconds,
                ActorUpdateStepSeconds);

            if (earlyDeathFrame.action == InactiveActorDeathAction::HoldDead)
            {
                resetCrowdSteeringState(actor);
                actor.aiState = ActorAiState::Dead;
                actor.animation = ActorAnimation::Dead;
                continue;
            }

            if (earlyDeathFrame.action == InactiveActorDeathAction::MarkDead
                || earlyDeathFrame.action == InactiveActorDeathAction::AdvanceDying)
            {
                spawnBloodSplatForActorIfNeeded(actorIndex);
                resetCrowdSteeringState(actor);
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.attackImpactTriggered = false;

                if (earlyDeathFrame.action == InactiveActorDeathAction::AdvanceDying)
                {
                    actor.animation = ActorAnimation::Dying;
                    actor.animationTimeTicks += ActorUpdateStepSeconds * TicksPerSecond;
                    actor.actionSeconds = earlyDeathFrame.actionSeconds;

                    if (earlyDeathFrame.finishedDying)
                    {
                        setMapActorDead(actorIndex, true, false);
                    }
                }
                else
                {
                    setMapActorDead(actorIndex, true, false);
                }

                continue;
            }

            resetCrowdSteeringState(actor);
            actor.animation = ActorAnimation::Standing;
            continue;
        }

        const bool selectedForActiveUpdate = actorIndex < activeActorMask.size() && activeActorMask[actorIndex];

        if (!selectedForActiveUpdate)
        {
            resetCrowdSteeringState(actor);

            const InactiveActorDeathFrame inactiveDeathFrame = resolveInactiveActorDeathFrame(
                actor.isDead,
                actor.currentHp <= 0,
                actor.currentHp <= 0 && actor.aiState == ActorAiState::Dying,
                actor.actionSeconds,
                ActorUpdateStepSeconds);

            if (inactiveDeathFrame.action == InactiveActorDeathAction::HoldDead)
            {
                actor.aiState = ActorAiState::Dead;
                actor.animation = ActorAnimation::Dead;
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.actionSeconds = 0.0f;
                actor.attackImpactTriggered = false;
                continue;
            }

            if (inactiveDeathFrame.action == InactiveActorDeathAction::MarkDead
                || inactiveDeathFrame.action == InactiveActorDeathAction::AdvanceDying)
            {
                spawnBloodSplatForActorIfNeeded(actorIndex);
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.attackImpactTriggered = false;

                if (inactiveDeathFrame.action == InactiveActorDeathAction::AdvanceDying)
                {
                    actor.aiState = ActorAiState::Dying;
                    actor.animation = ActorAnimation::Dying;
                    actor.animationTimeTicks += ActorUpdateStepSeconds * TicksPerSecond;
                    actor.actionSeconds = inactiveDeathFrame.actionSeconds;
                    applyOutdoorActorPhysicsStep(actorIndex, *pStats, activeActorMask);

                    if (inactiveDeathFrame.finishedDying)
                    {
                        setMapActorDead(actorIndex, true, false);
                    }
                }
                else
                {
                    setMapActorDead(actorIndex, true, false);
                }

                continue;
            }

            updateInactiveActorPresentation(actor, partyX, partyY, m_pGameplayActorService);

            if (!pStats->canFly && actor.movementStateInitialized && actor.movementState.airborne)
            {
                applyOutdoorActorPhysicsStep(actorIndex, *pStats, activeActorMask);
            }
            continue;
        }
    }
}

void OutdoorWorldRuntime::applyActorFrameSideEffects(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    updateWorldItems(deltaSeconds);
    updateProjectiles(deltaSeconds, partyX, partyY, partyZ);
    updateFireSpikeTraps(deltaSeconds, partyX, partyY, partyZ);
}

void OutdoorWorldRuntime::updateMapActors(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f || m_pMonsterTable == nullptr)
    {
        return;
    }

    updateActorFrameGlobalEffects(deltaSeconds, partyX, partyY, partyZ);

    while (m_actorUpdateAccumulatorSeconds >= ActorUpdateStepSeconds)
    {
        const std::vector<bool> activeActorMask = selectOutdoorActiveActors(partyX, partyY, partyZ);
        const ActorAiFrameFacts actorAiFacts =
            collectOutdoorActorAiFrameFacts(ActorUpdateStepSeconds, partyX, partyY, partyZ, activeActorMask);
        const GameplayActorAiSystem actorAiSystem = {};
        const ActorAiFrameResult actorAiResult = actorAiSystem.updateActors(actorAiFacts);
        applyOutdoorActorAiFrameResult(actorAiResult, activeActorMask, actorAiSystem);

        updateOutdoorInactiveAndInvalidActors(partyX, partyY, partyZ, activeActorMask);
        applyActorFrameSideEffects(ActorUpdateStepSeconds, partyX, partyY, partyZ);
        m_actorUpdateAccumulatorSeconds -= ActorUpdateStepSeconds;
    }
}

void OutdoorWorldRuntime::queueActorAiUpdate(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    m_actorAiUpdateQueued = true;
    m_queuedActorAiDeltaSeconds += deltaSeconds;
    m_queuedActorAiPartyX = partyX;
    m_queuedActorAiPartyY = partyY;
    m_queuedActorAiPartyZ = partyZ;
}

bool OutdoorWorldRuntime::spawnProjectileFromMapActor(
    const MapActorState &actor,
    const MonsterTable::MonsterStatsEntry &stats,
    MonsterAttackAbility ability,
    float targetX,
    float targetY,
    float targetZ,
    int damage,
    int attackBonus,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    const std::string &projectileTokenOverride
)
{
    if (ability == MonsterAttackAbility::Spell1 || ability == MonsterAttackAbility::Spell2)
    {
        if (spellId != 0 && m_pSpellTable != nullptr)
        {
            const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

            if (pSpellEntry != nullptr)
            {
                SpellCastRequest request = {};
                request.sourceKind = RuntimeSpellSourceKind::Actor;
                request.sourceId = actor.actorId;
                request.sourceMonsterId = actor.monsterId;
                request.fromSummonedMonster =
                    m_pGameplayActorService != nullptr
                    && m_pGameplayActorService->isPartyControlledActor(
                        gameplayActorControlModeFromOutdoor(actor.controlMode));
                request.ability = ability;
                request.spellId = spellId;
                request.damageType = GameMechanics::spellCombatDamageType(request.spellId, m_pSpellTable);
                request.skillLevel = skillLevel != 0 ? skillLevel : static_cast<uint32_t>(std::max(stats.level, 1));
                request.skillMastery = static_cast<uint32_t>(skillMastery);
                request.sourceX = actor.preciseX;
                request.sourceY = actor.preciseY;
                request.sourceZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
                request.targetX = targetX;
                request.targetY = targetY;
                request.targetZ = targetZ;
                return castSpell(request);
            }
        }

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

    MonsterTable::MonsterStatsEntry projectileStats = stats;
    if (!projectileTokenOverride.empty() && ability == MonsterAttackAbility::Attack2)
    {
        projectileStats.attack2MissileType = projectileTokenOverride;
    }

    if (!resolveProjectileDefinition(
            projectileStats,
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
    const uint16_t objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    GameplayProjectileService::ProjectileSpawnRequest spawnRequest = {};
    spawnRequest.sourceKind = ProjectileState::SourceKind::Actor;
    spawnRequest.sourceId = actor.actorId;
    spawnRequest.sourceMonsterId = actor.monsterId;
    spawnRequest.fromSummonedMonster =
        m_pGameplayActorService != nullptr
        && m_pGameplayActorService->isPartyControlledActor(gameplayActorControlModeFromOutdoor(actor.controlMode));
    spawnRequest.ability = ability;
    spawnRequest.definition = buildGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    spawnRequest.damage = damage;
    spawnRequest.attackBonus = attackBonus;
    spawnRequest.damageType =
        ability == MonsterAttackAbility::Attack2
            ? GameMechanics::parseCombatDamageType(stats.attack2Type)
            : GameMechanics::parseCombatDamageType(stats.attack1Type);
    spawnRequest.sourceX = sourceX;
    spawnRequest.sourceY = sourceY;
    spawnRequest.sourceZ = sourceZ;
    spawnRequest.targetX = aimX;
    spawnRequest.targetY = aimY;
    spawnRequest.targetZ = aimZ;
    spawnRequest.spawnForwardOffset = static_cast<float>(actor.radius) + 8.0f;
    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        projectileService().spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        projectileService().buildProjectileSpawnEffects(spawnResult);

    if (!applyProjectileSpawnEffects(
            spawnResult,
            spawnEffects,
            "monster",
            "monster_projectile_zero_distance"))
    {
        std::cout
            << "Projectile spawn skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " reason=zero_distance_target"
            << '\n';
        return false;
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

    if (!isProjectileSpellName(spellName) && spellName != "meteor shower" && spellName != "starburst")
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
    request.fromSummonedMonster =
        m_pGameplayActorService != nullptr
        && m_pGameplayActorService->isPartyControlledActor(gameplayActorControlModeFromOutdoor(actor.controlMode));
    request.ability = ability;
    request.spellId = static_cast<uint32_t>(pSpellEntry->id);
    request.damageType = GameMechanics::spellCombatDamageType(request.spellId, m_pSpellTable);
    request.skillLevel = static_cast<uint32_t>(std::max(stats.level, 1));
    const SpellId resolvedSpellId = spellIdFromValue(std::max(pSpellEntry->id, 0));
    request.skillMastery = resolvedSpellId == SpellId::MeteorShower
        ? static_cast<uint32_t>(SkillMastery::Master)
        : resolvedSpellId == SpellId::Starburst
        ? static_cast<uint32_t>(SkillMastery::Grandmaster)
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
    if (request.sourceKind == RuntimeSpellSourceKind::Event)
    {
        if (const EventProjectileSpellDefinition *pEventProjectile =
                eventProjectileSpellDefinition(request.spellId))
        {
            if (m_pObjectTable == nullptr)
            {
                return false;
            }

            ResolvedProjectileDefinition definition = {};

            if (!::OpenYAMM::Game::resolveObjectProjectileDefinition(
                    pEventProjectile->objectId,
                    pEventProjectile->impactObjectId,
                    *m_pObjectTable,
                    definition))
            {
                return false;
            }

            definition.spellId = static_cast<int>(request.spellId);
            return castDirectSpellProjectile(request, definition);
        }
    }

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

    if (isSpellId(request.spellId, SpellId::MeteorShower))
    {
        return castMeteorShower(request, definition);
    }

    if (isSpellId(request.spellId, SpellId::Starburst))
    {
        return castStarburst(request, definition);
    }

    return castDirectSpellProjectile(request, definition);
}

bool OutdoorWorldRuntime::resolveObjectProjectileDefinition(
    int objectId,
    int impactObjectId,
    ResolvedProjectileDefinition &definition) const
{
    if (m_pObjectTable == nullptr)
    {
        return false;
    }

    return ::OpenYAMM::Game::resolveObjectProjectileDefinition(objectId, impactObjectId, *m_pObjectTable, definition);
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

bool OutdoorWorldRuntime::spawnDeathBlossomFalloutProjectiles(
    const ProjectileState &projectile,
    float x,
    float y,
    float z)
{
    ResolvedProjectileDefinition definition = {};

    if (!resolveObjectProjectileDefinition(4092, 4091, definition))
    {
        return false;
    }

    const uint16_t objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    const GameplayProjectileService::ProjectileDefinition projectileDefinition =
        buildGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    const std::vector<GameplayProjectileService::ProjectileSpawnResult> falloutResults =
        projectileService().spawnDeathBlossomFalloutProjectiles(projectile, projectileDefinition, x, y, z);
    bool spawnedAny = false;

    for (const GameplayProjectileService::ProjectileSpawnResult &spawnResult : falloutResults)
    {
        const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
            projectileService().buildProjectileSpawnEffects(spawnResult);

        if (applyProjectileSpawnEffects(
                spawnResult,
                spawnEffects,
                projectileSourceKindName(spawnResult.projectile.sourceKind),
                "death_blossom_fallout_zero_distance"))
        {
            spawnedAny = true;
        }
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::castMeteorShower(
    const SpellCastRequest &request,
    const ResolvedProjectileDefinition &definition
)
{
    const std::vector<GameplayProjectileService::AreaSpellProjectileShot> shots =
        projectileService().buildMeteorShowerProjectileShots(
            request.skillMastery,
            projectileService().nextProjectileId(),
            request.targetX,
            request.targetY,
            request.targetZ);
    bool spawnedAny = false;

    for (const GameplayProjectileService::AreaSpellProjectileShot &shot : shots)
    {
        float meteorTargetZ = shot.targetZ;

        if (m_pOutdoorMapData != nullptr)
        {
            meteorTargetZ = std::max(
                meteorTargetZ,
                sampleOutdoorTerrainHeight(*m_pOutdoorMapData, shot.targetX, shot.targetY));
        }

        const float meteorSourceZ = meteorTargetZ + shot.sourceHeightOffset;
        spawnedAny = spawnSpellProjectile(
            request,
            definition,
            shot.sourceX,
            shot.sourceY,
            meteorSourceZ,
            shot.targetX,
            shot.targetY,
            meteorTargetZ,
            0.0f)
            || spawnedAny;
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::castStarburst(
    const SpellCastRequest &request,
    const ResolvedProjectileDefinition &definition
)
{
    const std::vector<GameplayProjectileService::AreaSpellProjectileShot> shots =
        projectileService().buildStarburstProjectileShots(
            projectileService().nextProjectileId(),
            request.targetX,
            request.targetY,
            request.targetZ);
    bool spawnedAny = false;

    for (const GameplayProjectileService::AreaSpellProjectileShot &shot : shots)
    {
        float starTargetZ = shot.targetZ;
        float starSourceBaseZ = shot.targetZ;

        if (m_pOutdoorMapData != nullptr)
        {
            starTargetZ = std::max(
                starTargetZ,
                sampleOutdoorTerrainHeight(*m_pOutdoorMapData, shot.targetX, shot.targetY));
            starSourceBaseZ = std::max(
                starSourceBaseZ,
                sampleOutdoorTerrainHeight(*m_pOutdoorMapData, shot.sourceX, shot.sourceY));
        }

        const float starSourceZ = starSourceBaseZ + shot.sourceHeightOffset;
        spawnedAny = spawnSpellProjectile(
            request,
            definition,
            shot.sourceX,
            shot.sourceY,
            starSourceZ,
            shot.targetX,
            shot.targetY,
            starTargetZ,
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
    const uint16_t objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    GameplayProjectileService::ProjectileSpawnRequest spawnRequest = {};
    spawnRequest.sourceKind = projectileSourceKindFromSpellSource(request.sourceKind);
    spawnRequest.sourceId = request.sourceId;
    spawnRequest.sourcePartyMemberIndex = request.sourcePartyMemberIndex;
    spawnRequest.sourceMonsterId = request.sourceMonsterId;
    spawnRequest.fromSummonedMonster = request.fromSummonedMonster;
    spawnRequest.ability = request.ability;
    spawnRequest.definition = buildGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    if (request.effectSoundIdOverride > 0)
    {
        spawnRequest.definition.effectSoundId = static_cast<int>(request.effectSoundIdOverride);
    }
    spawnRequest.impactSoundIdOverride = request.impactSoundIdOverride;
    spawnRequest.skillLevel = request.skillLevel;
    spawnRequest.skillMastery = request.skillMastery;
    spawnRequest.damage = request.damage;
    spawnRequest.attackBonus = request.attackBonus;
    spawnRequest.useActorHitChance = request.useActorHitChance;
    spawnRequest.damageType = request.damageType;
    spawnRequest.turnBasedPendingAction = request.turnBasedPendingAction;
    spawnRequest.sourceX = sourceX;
    spawnRequest.sourceY = sourceY;
    spawnRequest.sourceZ = sourceZ;
    spawnRequest.targetX = targetX;
    spawnRequest.targetY = targetY;
    spawnRequest.targetZ = targetZ;
    spawnRequest.spawnForwardOffset = spawnForwardOffset;
    spawnRequest.allowInstantImpact = true;
    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        projectileService().spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        projectileService().buildProjectileSpawnEffects(spawnResult);

    return applyProjectileSpawnEffects(
        spawnResult,
        spawnEffects,
        spellSourceKindName(request.sourceKind),
        "spell_zero_distance");
}

void OutdoorWorldRuntime::spawnProjectileImpact(
    const ProjectileState &projectile,
    float x,
    float y,
    float z,
    bool centerVertically)
{
    if (const std::optional<GameplayProjectileService::ProjectileAudioRequest> audioRequest =
            projectileService().buildProjectileImpactAudioRequest(projectile, x, y, z))
    {
        pushProjectileAudioEvent(*audioRequest);
    }

    if (projectile.impactObjectDescriptionId == 0 || m_pObjectTable == nullptr)
    {
        return;
    }

    const std::optional<GameplayProjectileService::ProjectileImpactVisualDefinition> impactDefinition =
        projectileService().buildProjectileImpactVisualDefinition(
            projectile.impactObjectDescriptionId,
            m_pObjectTable,
            m_pProjectileSpriteFrameTable);

    if (!impactDefinition)
    {
        return;
    }

    const GameplayProjectileService::ProjectileImpactSpawnResult result =
        spawnProjectileImpactVisual(projectile, *impactDefinition, x, y, z, centerVertically);

    if (result.spawned && result.pImpact != nullptr)
    {
        logProjectileImpactEffect(projectile, *result.pImpact);
    }
}

bool OutdoorWorldRuntime::spawnWaterSplashImpact(float x, float y, float z)
{
    if (m_pObjectTable == nullptr || m_pProjectileSpriteFrameTable == nullptr)
    {
        return false;
    }

    const std::optional<GameplayProjectileService::ProjectileImpactVisualDefinition> splashDefinition =
        projectileService().buildWaterSplashImpactVisualDefinition(m_pObjectTable, m_pProjectileSpriteFrameTable);

    if (!splashDefinition)
    {
        return false;
    }

    spawnWaterSplashImpactVisual(*splashDefinition, x, y, z);

    if (const std::optional<GameplayProjectileService::ProjectileAudioRequest> audioRequest =
            projectileService().buildWaterSplashAudioRequest(x, y, z))
    {
        pushProjectileAudioEvent(*audioRequest);
    }
    return true;
}

bool OutdoorWorldRuntime::projectileSourceIsFriendlyToActor(
    const ProjectileState &projectile,
    const MapActorState &actor) const
{
    GameplayProjectileService::ProjectileActorRelationFacts facts = {};
    facts.eventSource = projectile.sourceId == EventSpellSourceId;
    facts.targetHostileToParty = actor.hostileToParty;

    if (m_pGameplayActorService != nullptr)
    {
        facts.targetPartyControlled = m_pGameplayActorService->isPartyControlledActor(
            gameplayActorControlModeFromOutdoor(actor.controlMode));
        facts.sourceMonsterKnown = projectile.sourceMonsterId != 0;
        facts.sourceMonsterFriendlyToTarget = facts.sourceMonsterKnown
            && m_pGameplayActorService->monsterIdsAreFriendly(projectile.sourceMonsterId, actor.monsterId);
    }

    return projectileService().isProjectileSourceFriendlyToActor(projectile, facts);
}

int OutdoorWorldRuntime::resolveProjectilePartyImpactDamage(const ProjectileState &projectile) const
{
    const GameplayProjectileService::ProjectilePartyImpactDamageInput input =
        buildProjectilePartyImpactDamageInput(projectile, m_pMonsterTable, m_pSpellTable, m_mapActors);
    return projectileService().resolveProjectilePartyImpactDamage(input);
}

GameplayProjectileService::ProjectileAreaImpactInput OutdoorWorldRuntime::buildProjectileAreaImpactInput(
    const ProjectileState &projectile,
    const bx::Vec3 &impactPoint,
    float impactRadius,
    float partyX,
    float partyY,
    float partyZ,
    bool canHitParty,
    size_t directActorIndex) const
{
    GameplayProjectileService::ProjectileAreaImpactInput input = {};
    input.impactX = impactPoint.x;
    input.impactY = impactPoint.y;
    input.impactZ = impactPoint.z;
    input.impactRadius = impactRadius;
    input.partyX = partyX;
    input.partyY = partyY;
    input.partyZ = partyZ;
    input.partyCollisionRadius = PartyCollisionRadius;
    input.partyCollisionHeight = PartyCollisionHeight;
    input.canHitParty = canHitParty;
    input.nonPartyProjectileDamage = resolveProjectilePartyImpactDamage(projectile);
    input.actors.reserve(m_mapActors.size());

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const MapActorState &actor = m_mapActors[actorIndex];

        GameplayProjectileService::ProjectileAreaImpactActorFacts actorFacts = {};
        actorFacts.actorIndex = actorIndex;
        actorFacts.actorId = actor.actorId;
        actorFacts.x = actor.preciseX;
        actorFacts.y = actor.preciseY;
        actorFacts.z = actor.preciseZ;
        actorFacts.radius = actor.radius;
        actorFacts.height = actor.height;
        actorFacts.unavailableForCombat = isActorUnavailableForCombat(actor);
        actorFacts.friendlyToProjectileSource =
            projectile.sourceKind != ProjectileState::SourceKind::Party
            && projectileSourceIsFriendlyToActor(projectile, actor);
        actorFacts.directImpactActor = actorIndex == directActorIndex;
        input.actors.push_back(actorFacts);
    }

    return input;
}

int OutdoorWorldRuntime::resolvePartyProjectileDamageMultiplier(
    const ProjectileState &projectile,
    size_t actorIndex) const
{
    if (actorIndex >= m_mapActors.size()
        || m_pParty == nullptr
        || m_pMonsterTable == nullptr)
    {
        return 1;
    }

    const Character *pSourceMember = m_pParty->member(projectile.sourcePartyMemberIndex);
    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable->findStatsById(m_mapActors[actorIndex].monsterId);

    if (pSourceMember == nullptr || pStats == nullptr)
    {
        return 1;
    }

    return projectileService().resolvePartyProjectileDamageMultiplier(
        projectile,
        pSourceMember,
        m_pItemTable,
        m_pSpecialItemEnchantTable,
        pStats->kindFlags);
}

GameplayProjectileService::ProjectileDirectActorImpactInput
OutdoorWorldRuntime::buildProjectileDirectActorImpactInput(
    const ProjectileState &projectile,
    size_t actorIndex) const
{
    GameplayProjectileService::ProjectileDirectActorImpactInput input = {};

    if (actorIndex >= m_mapActors.size())
    {
        return input;
    }

    const MapActorState &actor = m_mapActors[actorIndex];
    const float distanceToTarget = std::max(
        0.0f,
        length3d(
            actor.preciseX - projectile.sourceX,
            actor.preciseY - projectile.sourceY,
            actor.preciseZ - projectile.sourceZ)
            - static_cast<float>(actor.radius));

    input.actorIndex = actorIndex;
    input.actorId = actor.actorId;
    input.targetArmorClass = effectiveMapActorArmorClass(actorIndex);
    input.damageMultiplier = resolvePartyProjectileDamageMultiplier(projectile, actorIndex);
    input.halfIncomingMissileDamage =
        m_pGameplayActorService != nullptr
            && m_pGameplayActorService->halveIncomingMissileDamage(buildGameplayActorSpellEffectState(actor));
    input.targetDistance = distanceToTarget;
    input.nonPartyProjectileDamage = resolveProjectilePartyImpactDamage(projectile);
    return input;
}

void OutdoorWorldRuntime::buildOutdoorFaceSpatialIndex()
{
    m_outdoorFaceGridCells.clear();
    m_outdoorFaceVisitGenerations.clear();
    m_outdoorFaceVisitGenerationCounter = 1;
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
    m_outdoorFaceVisitGenerations.assign(m_outdoorFaces.size(), 0);

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

void OutdoorWorldRuntime::rebuildOutdoorFaceGeometryCache()
{
    m_outdoorFaces.clear();
    m_outdoorFaceGridCells.clear();
    m_outdoorFaceVisitGenerations.clear();

    if (m_pOutdoorMapData == nullptr)
    {
        return;
    }

    for (size_t bModelIndex = 0; bModelIndex < m_pOutdoorMapData->bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel *pBModel = &m_pOutdoorMapData->bmodels[bModelIndex];
        OutdoorBModel translatedBModel = {};

        if (m_eventRuntimeState && !m_eventRuntimeState->outdoorModelMechanisms.empty())
        {
            translatedBModel = translatedOutdoorBModel(*pBModel, &*m_eventRuntimeState, bModelIndex);
            pBModel = &translatedBModel;
        }

        for (size_t faceIndex = 0; faceIndex < pBModel->faces.size(); ++faceIndex)
        {
            OutdoorFaceGeometryData geometry = {};

            if (buildOutdoorFaceGeometry(
                    *pBModel,
                    bModelIndex,
                    pBModel->faces[faceIndex],
                    faceIndex,
                    geometry,
                    true))
            {
                m_outdoorFaces.push_back(std::move(geometry));
            }
        }
    }

    buildOutdoorFaceSpatialIndex();
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

    if (m_outdoorFaceVisitGenerations.size() != m_outdoorFaces.size())
    {
        m_outdoorFaceVisitGenerations.assign(m_outdoorFaces.size(), 0);
        m_outdoorFaceVisitGenerationCounter = 1;
    }

    if (m_outdoorFaceVisitGenerationCounter == std::numeric_limits<uint32_t>::max())
    {
        std::fill(m_outdoorFaceVisitGenerations.begin(), m_outdoorFaceVisitGenerations.end(), 0);
        m_outdoorFaceVisitGenerationCounter = 1;
    }

    const uint32_t visitGeneration = m_outdoorFaceVisitGenerationCounter++;

    for (size_t cellY = minCellY; cellY <= maxCellY; ++cellY)
    {
        for (size_t cellX = minCellX; cellX <= maxCellX; ++cellX)
        {
            const std::vector<size_t> &cellFaces = m_outdoorFaceGridCells[cellY * m_outdoorFaceGridWidth + cellX];

            for (size_t faceIndex : cellFaces)
            {
                if (faceIndex >= m_outdoorFaceVisitGenerations.size()
                    || m_outdoorFaceVisitGenerations[faceIndex] == visitGeneration)
                {
                    continue;
                }

                m_outdoorFaceVisitGenerations[faceIndex] = visitGeneration;
                indices.push_back(faceIndex);
            }
        }
    }

}

const OutdoorFaceGeometryData *OutdoorWorldRuntime::outdoorFace(size_t faceIndex) const
{
    if (faceIndex >= m_outdoorFaces.size())
    {
        return nullptr;
    }

    return &m_outdoorFaces[faceIndex];
}

void OutdoorWorldRuntime::syncOutdoorFaceGeometryAttributesFromMapDelta()
{
    if (m_pOutdoorMapData == nullptr || m_pOutdoorMapDeltaData == nullptr)
    {
        return;
    }

    std::vector<size_t> bModelFaceOffsets;
    bModelFaceOffsets.reserve(m_pOutdoorMapData->bmodels.size());
    size_t flattenedFaceIndex = 0;

    for (const OutdoorBModel &bmodel : m_pOutdoorMapData->bmodels)
    {
        bModelFaceOffsets.push_back(flattenedFaceIndex);
        flattenedFaceIndex += bmodel.faces.size();
    }

    for (OutdoorFaceGeometryData &geometry : m_outdoorFaces)
    {
        if (geometry.bModelIndex >= bModelFaceOffsets.size())
        {
            continue;
        }

        const size_t effectiveFaceIndex = bModelFaceOffsets[geometry.bModelIndex] + geometry.faceIndex;

        if (effectiveFaceIndex >= m_pOutdoorMapDeltaData->faceAttributes.size())
        {
            continue;
        }

        const uint32_t attributes = m_pOutdoorMapDeltaData->faceAttributes[effectiveFaceIndex];
        geometry.attributes = attributes;

        if (m_outdoorMovementController)
        {
            m_outdoorMovementController->setFaceAttributes(geometry.bModelIndex, geometry.faceIndex, attributes);
        }

        if (m_pPartyRuntime != nullptr)
        {
            m_pPartyRuntime->setFaceAttributes(geometry.bModelIndex, geometry.faceIndex, attributes);
        }
    }
}

void OutdoorWorldRuntime::setOutdoorFaceGeometry(const OutdoorFaceGeometryData &geometry)
{
    for (OutdoorFaceGeometryData &existingGeometry : m_outdoorFaces)
    {
        if (existingGeometry.bModelIndex == geometry.bModelIndex
            && existingGeometry.faceIndex == geometry.faceIndex)
        {
            existingGeometry = geometry;
            return;
        }
    }

    m_outdoorFaces.push_back(geometry);
}

void OutdoorWorldRuntime::refreshOutdoorModelMechanismGeometry()
{
    if (m_pOutdoorMapData == nullptr || !m_eventRuntimeState || m_eventRuntimeState->outdoorModelMechanisms.empty())
    {
        return;
    }

    std::vector<OutdoorFaceGeometryData> updatedGeometries;

    for (const std::pair<const uint32_t, EventRuntimeState::OutdoorModelMechanismDefinition> &entry :
        m_eventRuntimeState->outdoorModelMechanisms)
    {
        const EventRuntimeState::OutdoorModelMechanismDefinition &definition = entry.second;

        if (definition.bmodelIndex >= m_pOutdoorMapData->bmodels.size())
        {
            continue;
        }

        const OutdoorBModel translatedBModel = translatedOutdoorBModel(
            m_pOutdoorMapData->bmodels[definition.bmodelIndex],
            &*m_eventRuntimeState,
            definition.bmodelIndex);

        for (size_t faceIndex = 0; faceIndex < translatedBModel.faces.size(); ++faceIndex)
        {
            OutdoorFaceGeometryData geometry = {};

            if (!buildOutdoorFaceGeometry(
                    translatedBModel,
                    definition.bmodelIndex,
                    translatedBModel.faces[faceIndex],
                    faceIndex,
                    geometry,
                    true))
            {
                continue;
            }

            setOutdoorFaceGeometry(geometry);
            updatedGeometries.push_back(std::move(geometry));
        }
    }

    if (updatedGeometries.empty())
    {
        return;
    }

    buildOutdoorFaceSpatialIndex();

    if (m_outdoorMovementController)
    {
        m_outdoorMovementController->updateFaceGeometries(updatedGeometries);
    }

    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->updateFaceGeometries(updatedGeometries);
    }
}

void OutdoorWorldRuntime::setOutdoorFaceGeometryAttributes(size_t bModelIndex, size_t faceIndex, uint32_t attributes)
{
    for (OutdoorFaceGeometryData &geometry : m_outdoorFaces)
    {
        if (geometry.bModelIndex == bModelIndex && geometry.faceIndex == faceIndex)
        {
            geometry.attributes = attributes;
            break;
        }
    }

    if (m_outdoorMovementController)
    {
        m_outdoorMovementController->setFaceAttributes(bModelIndex, faceIndex, attributes);
    }

    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->setFaceAttributes(bModelIndex, faceIndex, attributes);
    }
}

bool OutdoorWorldRuntime::hasClearOutdoorLineOfSight(const bx::Vec3 &start, const bx::Vec3 &end) const
{
    if (m_pOutdoorMapData != nullptr)
    {
        constexpr float TerrainLosSampleSpacing = static_cast<float>(OutdoorMapData::TerrainTileSize) * 0.5f;
        constexpr float TerrainLosHeightSlack = 12.0f;
        const float deltaX = end.x - start.x;
        const float deltaY = end.y - start.y;
        const float deltaZ = end.z - start.z;
        const float horizontalDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY);

        if (horizontalDistance > TerrainLosSampleSpacing)
        {
            const int sampleCount = std::max(2, static_cast<int>(std::ceil(horizontalDistance / TerrainLosSampleSpacing)));

            for (int sampleIndex = 1; sampleIndex < sampleCount; ++sampleIndex)
            {
                const float factor = static_cast<float>(sampleIndex) / static_cast<float>(sampleCount);
                const float sampleX = start.x + deltaX * factor;
                const float sampleY = start.y + deltaY * factor;
                const float sampleZ = start.z + deltaZ * factor;
                const float terrainHeight = sampleOutdoorTerrainHeight(*m_pOutdoorMapData, sampleX, sampleY);

                if (terrainHeight >= sampleZ - TerrainLosHeightSlack)
                {
                    return false;
                }
            }
        }
    }

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

        if (!outdoorFaceBlocksMovement(face) || !face.hasPlane || face.isWalkable)
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

float OutdoorWorldRuntime::sampleSupportFloorHeight(float x, float y, float z, float maxRise, float xySlack) const
{
    if (m_pOutdoorMapData == nullptr)
    {
        return z;
    }

    const float terrainHeight = sampleOutdoorTerrainHeight(*m_pOutdoorMapData, x, y);
    float bestHeight = terrainHeight;
    std::vector<size_t> candidateFaceIndices;
    collectOutdoorFaceCandidates(x - xySlack, y - xySlack, x + xySlack, y + xySlack, candidateFaceIndices);

    for (size_t faceIndex : candidateFaceIndices)
    {
        if (faceIndex >= m_outdoorFaces.size())
        {
            continue;
        }

        const OutdoorFaceGeometryData &geometry = m_outdoorFaces[faceIndex];

        if (!outdoorFaceBlocksMovement(geometry)
            || !geometry.isWalkable
            || x < geometry.minX - xySlack
            || x > geometry.maxX + xySlack
            || y < geometry.minY - xySlack
            || y > geometry.maxY + xySlack
            || !isPointInsideOrNearOutdoorPolygon(x, y, geometry.vertices, xySlack))
        {
            continue;
        }

        const float faceHeight = calculateOutdoorFaceHeight(geometry, x, y);

        if (faceHeight < terrainHeight || faceHeight > z + maxRise)
        {
            continue;
        }

        if (faceHeight >= bestHeight)
        {
            bestHeight = faceHeight;
        }
    }

    return bestHeight;
}

OutdoorWorldRuntime::ProjectileCollisionFacts OutdoorWorldRuntime::buildProjectileCollisionFacts(
    const ProjectileState &projectile,
    const bx::Vec3 &segmentStart,
    const bx::Vec3 &segmentEnd,
    float partyX,
    float partyY,
    float partyZ) const
{
    ProjectileCollisionFacts best = {};
    best.point = segmentEnd;

    auto considerImpact = [&best](
        float factor,
        const bx::Vec3 &point,
        ProjectileCollisionKind kind,
        std::string colliderName,
        size_t actorIndex,
        size_t faceIndex)
    {
        if (factor < 0.0f || factor > 1.0f || factor >= best.factor)
        {
            return;
        }

        best.hit = true;
        best.factor = factor;
        best.point = point;
        best.kind = kind;
        best.colliderName = std::move(colliderName);
        best.actorIndex = actorIndex;
        best.faceIndex = faceIndex;
    };

    if (projectileService().canProjectileCollideWithParty(projectile))
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
        const float collisionRadius =
            PartyCollisionRadius + static_cast<float>(std::max<uint16_t>(projectile.radius, 8));

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
                    {
                        segmentStart.x + (segmentEnd.x - segmentStart.x) * projectionFactor,
                        segmentStart.y + (segmentEnd.y - segmentStart.y) * projectionFactor,
                        collisionZ
                    },
                    ProjectileCollisionKind::Party,
                    "party",
                    static_cast<size_t>(-1),
                    static_cast<size_t>(-1));
            }
        }
    }

    const bool traceBlasterProjectile =
        blasterProjectileTraceEnabled() && projectileLooksLikeBlasterTraceTarget(projectile);

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const MapActorState &actor = m_mapActors[actorIndex];
        const float collisionRadius =
            GameplayProjectileService::directActorProjectileHitRadius(projectile, static_cast<float>(actor.radius))
            + static_cast<float>(std::max<uint16_t>(projectile.radius, 8));
        const OutdoorProjectileActorProbe actorProbe =
            probeOutdoorProjectileActor(
                segmentStart,
                segmentEnd,
                actor,
                collisionRadius,
                static_cast<float>(projectile.height));

        const auto traceActorDecision = [&](const char *pDecision)
        {
            if (traceBlasterProjectile && outdoorProjectileActorProbeIsTraceWorthy(actorProbe, collisionRadius))
            {
                traceOutdoorBlasterProjectileActorProbe(
                    projectile,
                    segmentStart,
                    segmentEnd,
                    actorIndex,
                    actor,
                    pDecision,
                    actorProbe,
                    collisionRadius,
                    best);
            }
        };

        GameplayProjectileService::ProjectileCollisionActorFacts actorFacts = {};
        actorFacts.actorId = actor.actorId;
        actorFacts.dead = actor.isDead;
        actorFacts.unavailableForCombat = isActorUnavailableForCombat(actor);
        actorFacts.friendlyToProjectileSource =
            projectile.sourceKind != ProjectileState::SourceKind::Party
            && projectileSourceIsFriendlyToActor(projectile, actor);

        if (!projectileService().canProjectileCollideWithActor(projectile, actorFacts))
        {
            const char *pDecision =
                actorFacts.dead ? "skip_dead"
                : actorFacts.unavailableForCombat ? "skip_unavailable"
                : actorFacts.friendlyToProjectileSource ? "skip_friendly"
                : "skip_cannot_collide";
            traceActorDecision(pDecision);
            continue;
        }

        if (actorProbe.horizontalDistanceSquared > collisionRadius * collisionRadius)
        {
            traceActorDecision("skip_horizontal");
            continue;
        }

        if (!actorProbe.withinVertical)
        {
            traceActorDecision("skip_vertical");
            continue;
        }

        std::ostringstream colliderNameStream;
        colliderNameStream << actor.displayName << " #" << actor.actorId;
        traceActorDecision("hit_candidate");
        considerImpact(
            actorProbe.progress,
            {
                actorProbe.closest.x,
                actorProbe.closest.y,
                actorProbe.collisionZ
            },
            ProjectileCollisionKind::Actor,
            colliderNameStream.str(),
            actorIndex,
            static_cast<size_t>(-1));
    }

    const float faceCollisionPadding =
        static_cast<float>(std::max<uint16_t>(projectile.radius, projectile.height)) + 16.0f;
    std::vector<size_t> candidateFaceIndices;
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

        if (!outdoorFaceBlocksMovement(face)
            || !segmentMayTouchFaceBounds(segmentStart, segmentEnd, face, faceCollisionPadding))
        {
            continue;
        }

        float factor = 0.0f;
        bx::Vec3 point = {0.0f, 0.0f, 0.0f};

        if (intersectOutdoorSegmentWithFace(face, segmentStart, segmentEnd, factor, point))
        {
            std::ostringstream colliderNameStream;
            colliderNameStream << face.modelName << " face=" << face.faceIndex;
            considerImpact(
                factor,
                point,
                ProjectileCollisionKind::BModel,
                colliderNameStream.str(),
                static_cast<size_t>(-1),
                faceIndex);
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
                {
                    segmentStart.x + (segmentEnd.x - segmentStart.x) * factor,
                    segmentStart.y + (segmentEnd.y - segmentStart.y) * factor,
                    terrainZ
                },
                ProjectileCollisionKind::Terrain,
                "terrain",
                static_cast<size_t>(-1),
                static_cast<size_t>(-1));
        }
    }

    if (best.hit
        && best.kind == ProjectileCollisionKind::Terrain
        && m_pOutdoorMapData != nullptr)
    {
        best.waterTerrainImpact =
            isOutdoorTerrainWater(*m_pOutdoorMapData, best.point.x, best.point.y)
            || isOutdoorLandMaskWater(m_outdoorLandMask, best.point.x, best.point.y);
    }

    return best;
}

OutdoorWorldRuntime::ProjectileFrameWorldFacts OutdoorWorldRuntime::collectProjectileFrameFacts(
    const ProjectileState &projectile,
    float deltaSeconds,
    float partyX,
    float partyY,
    float partyZ) const
{
    ProjectileState predictedProjectile = projectile;
    const bool lifetimeExpired = projectileService().advanceProjectileLifetime(predictedProjectile, deltaSeconds);

    ProjectileFrameWorldFacts worldFacts = {};
    worldFacts.frame.deltaSeconds = deltaSeconds;
    worldFacts.frame.gravity = WorldItemGravity;
    worldFacts.frame.bounceFactor = WorldItemBounceFactor;
    worldFacts.frame.bounceStopVelocity = WorldItemBounceStopVelocity;
    worldFacts.frame.groundDamping = WorldItemGroundDamping;
    worldFacts.frame.partyPosition = {partyX, partyY, partyZ};
    worldFacts.frame.partyCollisionRadius = PartyCollisionRadius;
    worldFacts.frame.partyCollisionHeight = PartyCollisionHeight;
    worldFacts.frame.canHitParty = true;
    worldFacts.frame.nonPartyProjectileDamage = resolveProjectilePartyImpactDamage(projectile);

    size_t directActorIndex = static_cast<size_t>(-1);
    bx::Vec3 areaImpactPoint = {projectile.x, projectile.y, projectile.z};

    if (!lifetimeExpired)
    {
        worldFacts.frame.motion =
            projectileService().advanceProjectileMotion(predictedProjectile, deltaSeconds, WorldItemGravity);
        const bx::Vec3 segmentStart = {
            worldFacts.frame.motion.startX,
            worldFacts.frame.motion.startY,
            worldFacts.frame.motion.startZ
        };
        const bx::Vec3 segmentEnd = {
            worldFacts.frame.motion.endX,
            worldFacts.frame.motion.endY,
            worldFacts.frame.motion.endZ
        };

        areaImpactPoint = segmentEnd;
        worldFacts.collision =
            buildProjectileCollisionFacts(projectile, segmentStart, segmentEnd, partyX, partyY, partyZ);

        if (worldFacts.collision.hit)
        {
            areaImpactPoint = worldFacts.collision.point;
            directActorIndex = worldFacts.collision.kind == ProjectileCollisionKind::Actor
                ? worldFacts.collision.actorIndex
                : static_cast<size_t>(-1);

            worldFacts.frame.hasCollision = true;
            worldFacts.frame.collision.point = {
                worldFacts.collision.point.x,
                worldFacts.collision.point.y,
                worldFacts.collision.point.z
            };
            worldFacts.frame.collision.colliderName = worldFacts.collision.colliderName;
            worldFacts.frame.collision.actorIndex = worldFacts.collision.actorIndex;
            worldFacts.frame.collision.bounceSurface = buildProjectileBounceSurfaceFacts(worldFacts.collision);
            worldFacts.frame.collision.waterTerrainImpact = worldFacts.collision.waterTerrainImpact;

            switch (worldFacts.collision.kind)
            {
                case ProjectileCollisionKind::Party:
                    worldFacts.frame.collision.kind =
                        GameplayProjectileService::ProjectileFrameCollisionKind::Party;
                    break;

                case ProjectileCollisionKind::Actor:
                {
                    worldFacts.frame.collision.kind =
                        GameplayProjectileService::ProjectileFrameCollisionKind::Actor;

                    const GameplayProjectileService::ProjectileDirectActorImpactInput directInput =
                        buildProjectileDirectActorImpactInput(projectile, worldFacts.collision.actorIndex);
                    worldFacts.frame.collision.actorId = directInput.actorId;
                    worldFacts.frame.collision.targetArmorClass = directInput.targetArmorClass;
                    worldFacts.frame.collision.damageMultiplier = directInput.damageMultiplier;
                    worldFacts.frame.collision.targetDistance = directInput.targetDistance;
                    break;
                }

                case ProjectileCollisionKind::BModel:
                case ProjectileCollisionKind::Terrain:
                    worldFacts.frame.collision.kind =
                        GameplayProjectileService::ProjectileFrameCollisionKind::World;
                    break;

                case ProjectileCollisionKind::None:
                default:
                    worldFacts.frame.collision.kind =
                        GameplayProjectileService::ProjectileFrameCollisionKind::None;
                    break;
            }
        }
    }

    const GameplayProjectileService::ProjectileAreaImpactInput areaInput =
        buildProjectileAreaImpactInput(
            projectile,
            areaImpactPoint,
            0.0f,
            partyX,
            partyY,
            partyZ,
            true,
            directActorIndex);
    worldFacts.frame.areaActors = areaInput.actors;

    return worldFacts;
}

GameplayProjectileService::ProjectileBounceSurfaceFacts OutdoorWorldRuntime::buildProjectileBounceSurfaceFacts(
    const ProjectileCollisionFacts &collision) const
{
    GameplayProjectileService::ProjectileBounceSurfaceFacts facts = {};

    if (!collision.hit)
    {
        return facts;
    }

    if (collision.kind == ProjectileCollisionKind::Terrain && !collision.waterTerrainImpact)
    {
        bx::Vec3 surfaceNormal = {0.0f, 0.0f, 1.0f};
        if (m_pOutdoorMapData != nullptr)
        {
            surfaceNormal = approximateOutdoorTerrainNormal(*m_pOutdoorMapData, collision.point.x, collision.point.y);
        }

        facts.canBounce = true;
        facts.requiresDownwardVelocity = true;
        facts.normalX = surfaceNormal.x;
        facts.normalY = surfaceNormal.y;
        facts.normalZ = surfaceNormal.z;
        return facts;
    }

    if (collision.kind != ProjectileCollisionKind::BModel || collision.faceIndex >= m_outdoorFaces.size())
    {
        return facts;
    }

    const OutdoorFaceGeometryData &face = m_outdoorFaces[collision.faceIndex];

    if (!face.hasPlane
        || face.normal.z <= 0.35f
        || (!face.isWalkable && face.normal.z <= 0.6f))
    {
        return facts;
    }

    facts.canBounce = true;
    facts.normalX = face.normal.x;
    facts.normalY = face.normal.y;
    facts.normalZ = face.normal.z;
    return facts;
}

void OutdoorWorldRuntime::applyProjectileFrameResult(
    ProjectileState &projectile,
    const ProjectileCollisionFacts &collision,
    const GameplayProjectileService::ProjectileFrameResult &frameResult)
{
    const ProjectileState projectileSnapshot = projectile;

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
                projectile.damageType,
                gameplayAttackAbilityFromOutdoor(projectile.ability));
        }
    }

    if (frameResult.directActorImpact && frameResult.directActorImpact->actorIndex < m_mapActors.size())
    {
        const GameplayProjectileService::ProjectileDirectActorImpact &impact =
            *frameResult.directActorImpact;

        bool killed = false;
        int appliedDamage = impact.damage;
        if (impact.applyPartyProjectileDamage)
        {
            const MonsterTable::MonsterStatsEntry *pStats =
                m_pMonsterTable != nullptr
                    ? m_pMonsterTable->findStatsById(m_mapActors[impact.actorIndex].monsterId)
                    : nullptr;

            if (pStats != nullptr)
            {
                std::mt19937 rng(
                    projectile.projectileId
                    ^ static_cast<uint32_t>(impact.actorId * 2654435761u)
                    ^ static_cast<uint32_t>(std::max(0, impact.damage)));
                appliedDamage = GameMechanics::resolveMonsterIncomingDamage(
                    impact.damage,
                    projectile.damageType,
                    monsterResistanceForDamageType(*pStats, projectile.damageType),
                    monsterHourOfPowerResistanceBonus(m_mapActors[impact.actorIndex]),
                    rng);
            }

            const int beforeHp = m_mapActors[impact.actorIndex].currentHp;
            applyPartyAttackToMapActor(
                impact.actorIndex,
                appliedDamage,
                projectile.sourceX,
                projectile.sourceY,
                projectile.sourceZ);
            const OutdoorWorldRuntime::MapActorState &afterActor = m_mapActors[impact.actorIndex];
            killed = beforeHp > 0 && afterActor.currentHp <= 0;
        }

        if (impact.queuePartyProjectileActorEvent)
        {
            if (m_pGameplayCombatController != nullptr)
            {
                m_pGameplayCombatController->recordPartyProjectileActorImpact(
                    projectile.sourceId,
                    projectile.sourcePartyMemberIndex,
                    impact.actorId,
                    impact.applyPartyProjectileDamage ? appliedDamage : impact.damage,
                    projectile.spellId,
                    impact.hit,
                    killed);
            }
        }
        else if (impact.applyNonPartyProjectileDamage)
        {
            applyMonsterAttackToMapActor(
                impact.actorIndex,
                impact.damage,
                projectile.sourceId);
        }
    }

    if (frameResult.areaImpact)
    {
        const GameplayProjectileService::ProjectileFrameAreaImpactResult &areaImpact = *frameResult.areaImpact;

        if (areaImpact.impact.hitParty)
        {
            if (m_pGameplayCombatController != nullptr)
            {
                m_pGameplayCombatController->recordPartyProjectileImpact(
                    projectile.sourceId,
                    areaImpact.impact.partyDamage,
                    projectile.attackBonus,
                    projectile.spellId,
                    true,
                    projectile.damageType,
                    gameplayAttackAbilityFromOutdoor(projectile.ability));
            }

            if (areaImpact.logHits)
            {
                const bx::Vec3 impactPoint = {areaImpact.point.x, areaImpact.point.y, areaImpact.point.z};
                logProjectileAoeHit(projectile, "party", impactPoint, areaImpact.radius);
            }
        }

        for (const GameplayProjectileService::ProjectileAreaImpactActorHit &actorHit :
             areaImpact.impact.actorHits)
        {
            if (actorHit.actorIndex >= m_mapActors.size())
            {
                continue;
            }

            bool killed = false;
            if (projectile.sourceKind == ProjectileState::SourceKind::Party)
            {
                int appliedDamage = actorHit.damage;
                const MonsterTable::MonsterStatsEntry *pStats =
                    m_pMonsterTable != nullptr
                        ? m_pMonsterTable->findStatsById(m_mapActors[actorHit.actorIndex].monsterId)
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
                        monsterResistanceForDamageType(*pStats, projectile.damageType),
                        monsterHourOfPowerResistanceBonus(m_mapActors[actorHit.actorIndex]),
                        rng);
                }

                const int beforeHp = m_mapActors[actorHit.actorIndex].currentHp;
                applyPartyAttackToMapActor(
                    actorHit.actorIndex,
                    appliedDamage,
                    projectile.sourceX,
                    projectile.sourceY,
                    projectile.sourceZ);
                killed = beforeHp > 0 && m_mapActors[actorHit.actorIndex].currentHp <= 0;

                if (m_pGameplayCombatController != nullptr)
                {
                    m_pGameplayCombatController->recordPartyProjectileActorImpact(
                        projectile.sourceId,
                        projectile.sourcePartyMemberIndex,
                        m_mapActors[actorHit.actorIndex].actorId,
                        appliedDamage,
                        projectile.spellId,
                        true,
                        killed);
                }
            }
            else
            {
                applyMonsterAttackToMapActor(actorHit.actorIndex, actorHit.damage, projectile.sourceId);
            }

            if (areaImpact.logHits)
            {
                const bx::Vec3 impactPoint = {areaImpact.point.x, areaImpact.point.y, areaImpact.point.z};
                logProjectileAoeHit(projectile, "actor", impactPoint, areaImpact.radius);
            }
        }
    }

    if (frameResult.logCollision)
    {
        logProjectileCollision(
            projectile,
            projectileCollisionKindName(collision.kind),
            collision.colliderName,
            collision.point);
    }

    if (frameResult.fxRequest)
    {
        switch (frameResult.fxRequest->kind)
        {
            case GameplayProjectileService::ProjectileFrameFxKind::WaterSplash:
                spawnWaterSplashImpact(
                    frameResult.fxRequest->point.x,
                    frameResult.fxRequest->point.y,
                    frameResult.fxRequest->point.z);
                break;

            case GameplayProjectileService::ProjectileFrameFxKind::ProjectileImpact:
                spawnProjectileImpact(
                    projectile,
                    frameResult.fxRequest->point.x,
                    frameResult.fxRequest->point.y,
                    frameResult.fxRequest->point.z,
                    frameResult.fxRequest->centerVertically);
                break;
        }
    }

    if (frameResult.audioRequest)
    {
        pushProjectileAudioEvent(*frameResult.audioRequest);
    }

    if (frameResult.logLifetimeExpiry)
    {
        logProjectileLifetimeExpiry(projectile);
    }

    if (frameResult.bounce)
    {
        projectileService().applyProjectileBounce(
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
        projectileService().applyProjectileMotionEnd(projectile, frameResult.motion);
    }

    if (frameResult.expireProjectile)
    {
        projectileService().expireProjectile(projectile);
    }

    if (frameResult.deathBlossomFalloutPoint)
    {
        spawnDeathBlossomFalloutProjectiles(
            projectileSnapshot,
            frameResult.deathBlossomFalloutPoint->x,
            frameResult.deathBlossomFalloutPoint->y,
            frameResult.deathBlossomFalloutPoint->z);
    }

    for (const GameplayProjectileService::ProjectileSpawnRequest &spawnRequest : frameResult.spawnedProjectiles)
    {
        projectileService().spawnProjectile(spawnRequest);
    }
}

bool OutdoorWorldRuntime::applyProjectileSpawnEffects(
    const GameplayProjectileService::ProjectileSpawnResult &spawnResult,
    const GameplayProjectileService::ProjectileSpawnEffects &effects,
    const std::string &spawnKindName,
    const std::string &instantColliderName)
{
    if (!effects.accepted)
    {
        return false;
    }

    if (effects.spawnInstantImpact)
    {
        logProjectileCollision(
            spawnResult.projectile,
            "instant",
            instantColliderName,
            {effects.impactX, effects.impactY, effects.impactZ});
        spawnProjectileImpact(
            spawnResult.projectile,
            effects.impactX,
            effects.impactY,
            effects.impactZ);
    }

    if (effects.playReleaseAudio && effects.releaseAudioRequest)
    {
        pushProjectileAudioEvent(*effects.releaseAudioRequest);
    }

    if (effects.logSpawn)
    {
        logProjectileSpawn(
            spawnKindName.c_str(),
            spawnResult.projectile,
            spawnResult.directionX,
            spawnResult.directionY,
            spawnResult.directionZ,
            spawnResult.speed);
    }

    return true;
}

const char *OutdoorWorldRuntime::projectileCollisionKindName(ProjectileCollisionKind kind)
{
    switch (kind)
    {
        case ProjectileCollisionKind::Party:
            return "party";
        case ProjectileCollisionKind::Actor:
            return "actor";
        case ProjectileCollisionKind::BModel:
            return "bmodel";
        case ProjectileCollisionKind::Terrain:
            return "terrain";
        case ProjectileCollisionKind::None:
        default:
            return "unknown";
    }
}

void OutdoorWorldRuntime::updateProjectiles(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    const bool hasActiveProjectile =
        std::any_of(
            projectileService().projectiles().begin(),
            projectileService().projectiles().end(),
            [](const ProjectileState &projectile)
            {
                return !projectile.isExpired;
            });

    if (!hasActiveProjectile)
    {
        m_projectileUpdateAccumulatorSeconds = 0.0f;
        return;
    }

    m_projectileUpdateAccumulatorSeconds =
        std::min(m_projectileUpdateAccumulatorSeconds + deltaSeconds, MaxAccumulatedProjectileUpdateSeconds);

    int projectileUpdateStepCount = 0;

    while (m_projectileUpdateAccumulatorSeconds >= ProjectileUpdateStepSeconds
        && projectileUpdateStepCount < MaxProjectileUpdateStepsPerFrame)
    {
        std::vector<ProjectileState> &projectiles = projectileService().projectiles();
        const size_t projectileCount = projectiles.size();

        for (size_t projectileIndex = 0;
             projectileIndex < projectileCount && projectileIndex < projectiles.size();
             ++projectileIndex)
        {
            ProjectileState &projectile = projectiles[projectileIndex];

            if (projectile.isExpired)
            {
                continue;
            }

            const ProjectileFrameWorldFacts worldFacts =
                collectProjectileFrameFacts(projectile, ProjectileUpdateStepSeconds, partyX, partyY, partyZ);
            const GameplayProjectileService::ProjectileFrameResult frameResult =
                projectileService().updateProjectileFrame(projectile, worldFacts.frame);
            applyProjectileFrameResult(projectile, worldFacts.collision, frameResult);
        }

        m_projectileUpdateAccumulatorSeconds -= ProjectileUpdateStepSeconds;
        ++projectileUpdateStepCount;
    }

    projectileService().eraseExpiredProjectiles();
}

void OutdoorWorldRuntime::applyEventRuntimeState(bool syncPersistentHostilityMasks)
{
    if (!m_eventRuntimeState)
    {
        return;
    }

    if (m_pOutdoorMapDeltaData != nullptr)
    {
        const int reputation = clampReputation(m_eventRuntimeState->currentLocationReputation);
        m_eventRuntimeState->currentLocationReputation = reputation;
        m_pOutdoorMapDeltaData->locationInfo.reputation = reputation;

        std::vector<uint32_t> appliedFacetSetMasks;
        appliedFacetSetMasks.reserve(m_eventRuntimeState->facetSetMasks.size());

        for (const std::pair<const uint32_t, uint32_t> &entry : m_eventRuntimeState->facetSetMasks)
        {
            if (setFacetBit(entry.first, entry.second, true))
            {
                appliedFacetSetMasks.push_back(entry.first);
            }
        }

        for (uint32_t cogNumber : appliedFacetSetMasks)
        {
            m_eventRuntimeState->facetSetMasks.erase(cogNumber);
        }

        std::vector<uint32_t> appliedFacetClearMasks;
        appliedFacetClearMasks.reserve(m_eventRuntimeState->facetClearMasks.size());

        for (const std::pair<const uint32_t, uint32_t> &entry : m_eventRuntimeState->facetClearMasks)
        {
            if (setFacetBit(entry.first, entry.second, false))
            {
                appliedFacetClearMasks.push_back(entry.first);
            }
        }

        for (uint32_t cogNumber : appliedFacetClearMasks)
        {
            m_eventRuntimeState->facetClearMasks.erase(cogNumber);
        }
    }

    std::vector<std::optional<bool>> persistentHostilityOverrides(m_mapActors.size(), std::nullopt);
    const auto setActorHostilityFromEvent =
        [this](size_t actorIndex, bool hostileToParty)
        {
            if (actorIndex >= m_mapActors.size())
            {
                return;
            }

            MapActorState &actor = m_mapActors[actorIndex];
            if (outdoorActorIsPartyControlled(actor.controlMode))
            {
                actor.hostileToParty = false;
                actor.hasDetectedParty = false;
                return;
            }

            actor.hostileToParty = hostileToParty;
            actor.hasDetectedParty = hostileToParty;
        };

    for (auto &[actorId, setMask] : m_eventRuntimeState->actorSetMasks)
    {
        if (actorId < m_mapActors.size() && (setMask & ActorInvisibleBit) != 0)
        {
            m_mapActors[actorId].isInvisible = true;
        }

        if (actorId < m_mapActors.size()
            && (setMask & static_cast<uint32_t>(EvtActorAttribute::HasItem)) != 0)
        {
            m_mapActors[actorId].specialItemId =
                m_eventRuntimeState->actorItemOverrides.contains(actorId)
                    ? m_eventRuntimeState->actorItemOverrides.at(actorId)
                    : 0;
        }

        if (actorId < m_mapActors.size() && (setMask & ActorHostileBit) != 0)
        {
            persistentHostilityOverrides[actorId] = true;
        }
    }

    for (auto &[actorId, clearMask] : m_eventRuntimeState->actorClearMasks)
    {
        if (actorId < m_mapActors.size() && (clearMask & ActorInvisibleBit) != 0)
        {
            m_mapActors[actorId].isInvisible = false;
        }

        if (actorId < m_mapActors.size()
            && (clearMask & static_cast<uint32_t>(EvtActorAttribute::HasItem)) != 0)
        {
            m_mapActors[actorId].specialItemId = 0;
        }

        if (actorId < m_mapActors.size() && (clearMask & ActorHostileBit) != 0)
        {
            persistentHostilityOverrides[actorId] = false;
        }
    }

    for (auto &[actorId, groupId] : m_eventRuntimeState->actorIdGroupOverrides)
    {
        if (actorId < m_mapActors.size())
        {
            m_mapActors[actorId].group = groupId;
        }
    }

    for (auto &[fromGroupId, toGroupId] : m_eventRuntimeState->actorGroupOverrides)
    {
        for (MapActorState &actor : m_mapActors)
        {
            if (actor.group == fromGroupId)
            {
                actor.group = toGroupId;
            }
        }
    }

    for (auto &[groupId, allyId] : m_eventRuntimeState->actorGroupAllyOverrides)
    {
        for (MapActorState &actor : m_mapActors)
        {
            if (actor.group == groupId)
            {
                actor.ally = allyId;
            }
        }
    }

    for (auto &[groupId, setMask] : m_eventRuntimeState->actorGroupSetMasks)
    {
        if ((setMask & (ActorInvisibleBit | ActorHostileBit)) == 0)
        {
            continue;
        }

        for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
        {
            MapActorState &actor = m_mapActors[actorIndex];

            if (actor.group == groupId)
            {
                if ((setMask & ActorInvisibleBit) != 0)
                {
                    actor.isInvisible = true;
                }

                if ((setMask & ActorHostileBit) != 0)
                {
                    persistentHostilityOverrides[actorIndex] = true;
                }
            }
        }

    }

    for (auto &[groupId, clearMask] : m_eventRuntimeState->actorGroupClearMasks)
    {
        if ((clearMask & (ActorInvisibleBit | ActorHostileBit)) == 0)
        {
            continue;
        }

        for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
        {
            MapActorState &actor = m_mapActors[actorIndex];

            if (actor.group == groupId)
            {
                if ((clearMask & ActorInvisibleBit) != 0)
                {
                    actor.isInvisible = false;
                }

                if ((clearMask & ActorHostileBit) != 0)
                {
                    persistentHostilityOverrides[actorIndex] = false;
                }
            }
        }

    }

    if (syncPersistentHostilityMasks)
    {
        for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
        {
            if (persistentHostilityOverrides[actorIndex].has_value())
            {
                setActorHostilityFromEvent(actorIndex, *persistentHostilityOverrides[actorIndex]);
            }
        }
    }

    for (const auto &[actorId, hostileToParty] : m_eventRuntimeState->actorHostilityRequests)
    {
        setActorHostilityFromEvent(actorId, hostileToParty);
    }

    for (const auto &[groupId, hostileToParty] : m_eventRuntimeState->actorGroupHostilityRequests)
    {
        for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
        {
            if (m_mapActors[actorIndex].group == groupId)
            {
                setActorHostilityFromEvent(actorIndex, hostileToParty);
            }
        }
    }

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const GameplayActorTargetPolicyState policyState =
            buildGameplayActorTargetPolicyState(m_mapActors[actorIndex]);
        const uint32_t relationMonsterId = policyState.relationMonsterId > 0
            ? static_cast<uint32_t>(policyState.relationMonsterId)
            : static_cast<uint32_t>(policyState.monsterId);
        const std::optional<int32_t> partyRelation =
            localMonsterRelation(&*m_eventRuntimeState, relationMonsterId, 0);

        if (partyRelation)
        {
            setActorHostilityFromEvent(actorIndex, *partyRelation > 0);
        }
    }

    for (auto &[chestId, setMask] : m_eventRuntimeState->chestSetMasks)
    {
        if (chestId >= m_chests.size())
        {
            continue;
        }

        m_chests[chestId].flags |= static_cast<uint16_t>(setMask);

        if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
        {
            m_materializedChestViews[chestId]->flags = m_chests[chestId].flags;
        }

        if (m_activeChestView && m_activeChestView->chestId == chestId)
        {
            m_activeChestView->flags = m_chests[chestId].flags;
        }
    }

    for (auto &[chestId, clearMask] : m_eventRuntimeState->chestClearMasks)
    {
        if (chestId >= m_chests.size())
        {
            continue;
        }

        m_chests[chestId].flags &= ~static_cast<uint16_t>(clearMask);

        if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
        {
            m_materializedChestViews[chestId]->flags = m_chests[chestId].flags;
        }

        if (m_activeChestView && m_activeChestView->chestId == chestId)
        {
            m_activeChestView->flags = m_chests[chestId].flags;
        }
    }

    for (const auto &[chestId, requests] : m_eventRuntimeState->chestItemRequests)
    {
        if (chestId >= m_chests.size())
        {
            continue;
        }

        if (chestId >= m_materializedChestViews.size())
        {
            m_materializedChestViews.resize(chestId + 1);
        }

        if (!m_materializedChestViews[chestId].has_value())
        {
            m_materializedChestViews[chestId] = buildChestView(chestId);
        }

        GameplayChestViewState &view = *m_materializedChestViews[chestId];

        for (const EventRuntimeState::ChestItemRequest &request : requests)
        {
            if (chestViewContainsItem(view, request.itemId))
            {
                continue;
            }

            const std::optional<GameplayChestItemState> item = buildFixedChestItem(request.itemId, m_pItemTable);

            if (item)
            {
                tryPlaceChestItemAt(view, *item, request.gridX, request.gridY);
            }
        }

        if (m_activeChestView && m_activeChestView->chestId == chestId)
        {
            m_activeChestView = view;
        }
    }

    const std::vector<EventRuntimeState::OpenedChestRequest> openedChestRequests =
        consumeOpenedChestRequests(*m_eventRuntimeState);

    for (const EventRuntimeState::OpenedChestRequest &openedChestRequest : openedChestRequests)
    {
        const uint32_t chestId = openedChestRequest.chestId;

        if (chestId < m_openedChests.size())
        {
            if (attemptOpenChest(chestId, openedChestRequest.openedByTelekinesis))
            {
                m_openedChests[chestId] = true;
                m_chests[chestId].flags |= static_cast<uint16_t>(EvtChestFlag::Opened);
                activateChestView(chestId);
            }
        }
    }

    m_pendingEventSourcePoint.reset();
}

bool OutdoorWorldRuntime::updateTimers(
    float deltaSeconds,
    const EventRuntime &eventRuntime,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram
)
{
    if (!m_eventRuntimeState || deltaSeconds <= 0.0f)
    {
        return false;
    }

    const float deltaGameMinutes = deltaSeconds * GameMinutesPerRealSecond;
    advanceGameMinutesInternal(deltaGameMinutes);
    refreshAtmosphereState();

    if (m_timers.empty())
    {
        appendTimersFromProgram(localEventProgram, m_timers);
        appendTimersFromProgram(globalEventProgram, m_timers);
    }

    if (m_timers.empty())
    {
        return false;
    }

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

        GAMEPLAY_DEBUG_TRACE(
            "timer_event_fired world=outdoor event_id=" + std::to_string(timer.eventId)
            + " repeating=" + (timer.repeating ? std::string("true") : std::string("false"))
            + " interval_game_minutes=" + std::to_string(timer.intervalGameMinutes));

        if (eventRuntime.executeEventById(
                localEventProgram,
                globalEventProgram,
                timer.eventId,
                *m_eventRuntimeState,
                m_pParty,
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

bool OutdoorWorldRuntime::actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const
{
    const MapActorState *pActor = mapActorState(actorIndex);

    if (pActor == nullptr)
    {
        return false;
    }

    state.monsterId = pActor->monsterId;
    state.preciseX = pActor->preciseX;
    state.preciseY = pActor->preciseY;
    state.preciseZ = pActor->preciseZ;
    state.radius = pActor->radius;
    state.height = pActor->height;
    state.isDead = pActor->isDead;
    state.isInvisible = pActor->isInvisible;
    state.hostileToParty = pActor->hostileToParty;
    state.hasDetectedParty = pActor->hasDetectedParty;
    state.combatTargetingParty = pActor->hostileToParty
        && pActor->hasDetectedParty
        && (pActor->aiState == ActorAiState::Pursuing || pActor->aiState == ActorAiState::Attacking);
    return true;
}

bool OutdoorWorldRuntime::tryStealFromActor(size_t actorIndex, uint32_t successRoll, uint32_t caughtRoll)
{
    if (actorIndex >= m_mapActors.size() || m_pMonsterTable == nullptr || m_pParty == nullptr)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (actor.isDead || actor.isInvisible)
    {
        return false;
    }

    Character *pMember = m_pParty->activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    if (actorIndex >= m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews.resize(actorIndex + 1);
    }

    if (!m_mapActorCorpseViews[actorIndex].has_value())
    {
        std::vector<uint32_t> guaranteedItemIds;

        if (actor.specialItemId != 0)
        {
            guaranteedItemIds.push_back(actor.specialItemId);
        }

        if (m_eventRuntimeState)
        {
            const auto extraItemIterator =
                m_eventRuntimeState->actorExtraItemOverrides.find(static_cast<uint32_t>(actorIndex));

            if (extraItemIterator != m_eventRuntimeState->actorExtraItemOverrides.end())
            {
                guaranteedItemIds.insert(
                    guaranteedItemIds.end(),
                    extraItemIterator->second.begin(),
                    extraItemIterator->second.end());
            }
        }

        GameplayCorpseViewState corpse =
            buildMonsterCorpseView(
                actor.displayName,
                gameplayBolsterLootPrototype(pStats->loot, pStats->hitPoints, actor.bolsterRewardMultiplier),
                m_pItemTable,
                m_pParty,
                guaranteedItemIds);
        corpse.fromSummonedMonster = false;
        corpse.sourceIndex = static_cast<uint32_t>(actorIndex);
        m_mapActorCorpseViews[actorIndex] = std::move(corpse);
    }

    GameplayCorpseViewState &corpse = *m_mapActorCorpseViews[actorIndex];
    const float deltaX = partyX() - actor.preciseX;
    const float deltaY = partyY() - actor.preciseY;
    const float deltaZ = partyFootZ() - actor.preciseZ;
    const bool reputationSensitiveTarget =
        actor.group == 38
        || actor.group == 55
        || pStats->hasKind(MonsterKind::Peasant);

    StealingAttemptInput input = {};
    input.targetKind = StealingTargetKind::Monster;
    input.monsterLevel = static_cast<int>(pStats->level);
    input.distanceSquared = static_cast<int>(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    input.hasLoot = !corpse.items.empty();
    input.reputationSensitiveTarget = reputationSensitiveTarget;
    input.successRoll = successRoll;
    input.caughtRoll = caughtRoll;
    const StealingAttemptResult stealResult = resolveStealingAttempt(*pMember, input);

    applyStealingAttemptResult(*this, m_pParty, stealResult);

    if (!stealResult.handled)
    {
        if (m_pInteractionView != nullptr)
        {
            m_pInteractionView->setStatusBarEvent("You need Stealing skill.");
        }

        return true;
    }

    if (stealResult.outcome != StealingOutcomeKind::Success)
    {
        if (m_pInteractionView != nullptr)
        {
            const char *pStatusText = stealResult.outcome == StealingOutcomeKind::TooFar
                ? "Too far away."
                : stealResult.outcome == StealingOutcomeKind::NothingToSteal
                    ? "Nothing to steal."
                    : stealResult.caught
                        ? "Caught stealing!"
                        : "Failed to steal.";
            m_pInteractionView->setStatusBarEvent(pStatusText);
        }

        return true;
    }

    if (corpse.items.empty())
    {
        return true;
    }

    GameplayChestItemState stolenItem = corpse.items.front();

    if (stolenItem.isGold)
    {
        const EventRuntimeState *pEventRuntimeState = eventRuntimeState();
        const int adjustedGold = static_cast<int>(
            pEventRuntimeState != nullptr
                ? hiredNpcGoldAfterBonusAndFees(stolenItem.goldAmount, *pEventRuntimeState)
                : stolenItem.goldAmount);
        m_pParty->addGold(adjustedGold);
        corpse.items.erase(corpse.items.begin());

        if (m_pInteractionView != nullptr)
        {
            m_pInteractionView->setStatusBarEvent("You found " + std::to_string(std::max(0, adjustedGold)) + " gold!");
        }

        return true;
    }

    InventoryItem inventoryItem = stolenItem.item;

    if (inventoryItem.objectDescriptionId == 0)
    {
        inventoryItem.objectDescriptionId = stolenItem.itemId;
    }

    if (inventoryItem.quantity == 0)
    {
        inventoryItem.quantity = stolenItem.quantity;
    }

    if (inventoryItem.width == 0)
    {
        inventoryItem.width = stolenItem.width;
    }

    if (inventoryItem.height == 0)
    {
        inventoryItem.height = stolenItem.height;
    }

    if (!m_pParty->tryGrantInventoryItemStartingAt(m_pParty->activeMemberIndex(), inventoryItem))
    {
        if (m_pInteractionView != nullptr)
        {
            m_pInteractionView->setStatusBarEvent("Pack is Full!");
        }

        return true;
    }

    corpse.items.erase(corpse.items.begin());

    if (m_pInteractionView != nullptr)
    {
        const ItemDefinition *pDefinition = m_pItemTable != nullptr ? m_pItemTable->get(stolenItem.itemId) : nullptr;
        const std::string itemName =
            pDefinition != nullptr && !pDefinition->name.empty() ? pDefinition->name : "item";
        m_pInteractionView->setStatusBarEvent("You found an item (" + itemName + ")!");
    }

    return true;
}

bool OutdoorWorldRuntime::actorInspectState(
    size_t actorIndex,
    uint32_t animationTicks,
    GameplayActorInspectState &state) const
{
    const MapActorState *pActor = mapActorState(actorIndex);

    if (pActor == nullptr)
    {
        return false;
    }

    state = {};
    state.displayName = pActor->displayName;
    state.monsterId = pActor->monsterId;
    state.previewYOffset = monsterInspectPreviewYOffset(pActor->monsterId);
    state.currentHp = pActor->currentHp;
    state.maxHp = pActor->maxHp;
    state.armorClass = effectiveMapActorArmorClass(actorIndex);
    state.attack1Damage.diceRolls = pActor->attack1DamageDiceRolls;
    state.attack1Damage.diceSides = pActor->attack1DamageDiceSides;
    state.attack1Damage.bonus = pActor->attack1DamageBonus;
    state.attack2Damage.diceRolls =
        pActor->copyAttack1DamageToAttack2 ? pActor->attack1DamageDiceRolls : pActor->attack2DamageDiceRolls;
    state.attack2Damage.diceSides =
        pActor->copyAttack1DamageToAttack2 ? pActor->attack1DamageDiceSides : pActor->attack2DamageDiceSides;
    state.attack2Damage.bonus = pActor->attack2DamageBonus;
    state.attack2Chance = pActor->generatedAttack2Chance;
    state.spell1SkillLevel = pActor->spell1SkillLevel;
    state.spell1SkillMastery = pActor->spell1SkillMastery;
    state.spell2SkillLevel = pActor->spell2SkillLevel;
    state.spell2SkillMastery = pActor->spell2SkillMastery;

    if (m_pMonsterTable != nullptr)
    {
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(pActor->monsterId);

        if (pStats != nullptr)
        {
            state.attack2Chance = state.attack2Chance > 0 ? state.attack2Chance : pStats->attack2Chance;
            state.hasSpell1 = pStats->hasSpell1 || pActor->spell1Id != 0;
            state.hasSpell2 = pStats->hasSpell2 || pActor->spell2Id != 0;
            state.spell1Name = pStats->spell1Name;
            state.spell2Name = pStats->spell2Name;

            if (state.attack1Damage.diceRolls <= 0 || state.attack1Damage.diceSides <= 0)
            {
                state.attack1Damage = pStats->attack1Damage;
            }

            if (state.attack2Damage.diceRolls <= 0 || state.attack2Damage.diceSides <= 0)
            {
                state.attack2Damage = pStats->attack2Damage;
            }

            if (pActor->spell1Id != 0 && !pStats->hasSpell1 && m_pSpellTable != nullptr)
            {
                if (const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(pActor->spell1Id)))
                {
                    state.spell1Name = pSpellEntry->name;
                }
            }

            if (pActor->spell2Id != 0 && !pStats->hasSpell2 && m_pSpellTable != nullptr)
            {
                if (const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(pActor->spell2Id)))
                {
                    state.spell2Name = pSpellEntry->name;
                }
            }
        }
    }

    state.isDead = pActor->isDead;
    state.slowRemainingSeconds = pActor->slowRemainingSeconds;
    state.stunRemainingSeconds = pActor->stunRemainingSeconds;
    state.paralyzeRemainingSeconds = pActor->paralyzeRemainingSeconds;
    state.fearRemainingSeconds = pActor->fearRemainingSeconds;
    state.shrinkRemainingSeconds = pActor->shrinkRemainingSeconds;
    state.darkGraspRemainingSeconds = pActor->darkGraspRemainingSeconds;
    state.dayOfProtectionRemainingSeconds = pActor->dayOfProtectionRemainingSeconds;
    state.hourOfPowerRemainingSeconds = pActor->hourOfPowerRemainingSeconds;
    state.painReflectionRemainingSeconds = pActor->painReflectionRemainingSeconds;
    state.hammerhandsRemainingSeconds = pActor->hammerhandsRemainingSeconds;
    state.hasteRemainingSeconds = pActor->hasteRemainingSeconds;
    state.shieldRemainingSeconds = pActor->shieldRemainingSeconds;
    state.stoneskinRemainingSeconds = pActor->stoneskinRemainingSeconds;
    state.blessRemainingSeconds = pActor->blessRemainingSeconds;
    state.fateRemainingSeconds = pActor->fateRemainingSeconds;
    state.heroismRemainingSeconds = pActor->heroismRemainingSeconds;

    if (pActor->aiState == ActorAiState::Attacking && m_pMonsterTable != nullptr)
    {
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(pActor->monsterId);
        std::string pendingSpellName;

        if (pStats != nullptr && pActor->queuedAttackAbility == MonsterAttackAbility::Spell1)
        {
            pendingSpellName = pStats->spell1Name;
        }
        else if (pStats != nullptr && pActor->queuedAttackAbility == MonsterAttackAbility::Spell2)
        {
            pendingSpellName = pStats->spell2Name;
        }

        if (outdoorMonsterSelfBuffSpellName(pendingSpellName))
        {
            state.pendingSelfBuffName = pendingSpellName;
        }
    }

    switch (pActor->controlMode)
    {
        case ActorControlMode::Charm:
            state.controlMode = GameplayActorControlMode::Charm;
            break;
        case ActorControlMode::Berserk:
            state.controlMode = GameplayActorControlMode::Berserk;
            break;
        case ActorControlMode::Enslaved:
            state.controlMode = GameplayActorControlMode::Enslaved;
            break;
        case ActorControlMode::ControlUndead:
            state.controlMode = GameplayActorControlMode::ControlUndead;
            break;
        case ActorControlMode::Reanimated:
            state.controlMode = GameplayActorControlMode::Reanimated;
            break;
        case ActorControlMode::None:
            state.controlMode = GameplayActorControlMode::None;
            break;
    }

    if (m_pActorSpriteFrameTable == nullptr)
    {
        return true;
    }

    advanceActorInspectPreviewAnimation(
        m_actorInspectPreviewAnimation,
        *pActor,
        m_pActorSpriteFrameTable,
        animationTicks);

    const uint16_t spriteFrameIndex =
        actorInspectPreviewSpriteFrameIndex(*pActor, m_actorInspectPreviewAnimation.animation);

    if (spriteFrameIndex == 0)
    {
        return true;
    }

    const SpriteFrameEntry *pFrame =
        m_pActorSpriteFrameTable->getFrame(spriteFrameIndex, m_actorInspectPreviewAnimation.actionTimeTicks);

    if (pFrame == nullptr)
    {
        pFrame = m_pActorSpriteFrameTable->getFrame(spriteFrameIndex, 0);
    }

    if (pFrame == nullptr)
    {
        return true;
    }

    static constexpr int PreviewFacingOctant = 0;
    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, PreviewFacingOctant);
    state.previewTextureName = resolvedTexture.textureName;
    state.previewPaletteId = pFrame->paletteId;
    state.previewYOffset = monsterInspectPreviewYOffset(pActor->monsterId);
    return true;
}

std::vector<GameplayArpgCombatFeedbackEvent> OutdoorWorldRuntime::drainArpgModeCombatFeedbackEvents()
{
    std::vector<GameplayArpgCombatFeedbackEvent> events = std::move(m_arpgModeCombatFeedbackEvents);
    m_arpgModeCombatFeedbackEvents.clear();
    return events;
}

std::optional<GameplayCombatActorInfo> OutdoorWorldRuntime::combatActorInfoById(uint32_t actorId) const
{
    if (m_pMonsterTable == nullptr)
    {
        return std::nullopt;
    }

    for (const MapActorState &actor : m_mapActors)
    {
        if (actor.actorId != actorId)
        {
            continue;
        }

        GameplayCombatActorInfo info = {};
        info.actorId = actor.actorId;
        info.monsterId = actor.monsterId;
        info.maxHp = actor.maxHp;
        info.displayName = actor.displayName;
        if (m_pGameplayActorService != nullptr)
        {
            info.attackBonus = m_pGameplayActorService->effectiveAttackHitBonus(
                buildGameplayActorSpellEffectState(actor));
        }

        if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
        {
            const MonsterEntry *pMonsterEntry = resolveMonsterEntry(*m_pMonsterTable, actor.monsterId, pStats);
            const GameplayMonsterBolsterResult bolster =
                resolveGameplayMonsterBolster(
                    GameplayBolsterRuntimeContext{
                        .pMap = &m_map,
                        .pMonsterTable = m_pMonsterTable,
                        .pBolsterMapTable = m_pMergedBolsterMapTable,
                        .pBolsterMonsterTable = m_pMergedBolsterMonsterTable,
                        .pParty = m_pParty,
                        .bolsterMonstersEnabled = m_bolsterMonstersEnabled,
                    },
                    *pStats,
                    pMonsterEntry);
            info.monsterLevel = pStats->level;
            info.attackPreferences = pStats->attackPreferences;
            info.bolsterAffectsPlayerArmorClass = bolster.statsEnabled;
            info.specialAttackKind = pStats->specialAttackKind;
            info.specialAttackLevel = pStats->specialAttackLevel;
        }

        return info;
    }

    return std::nullopt;
}

bool OutdoorWorldRuntime::applyReflectedDamageToActor(
    uint32_t actorId,
    int damage,
    CombatDamageType damageType,
    uint32_t sourcePartyMemberIndex)
{
    (void)sourcePartyMemberIndex;

    if (damage <= 0)
    {
        return false;
    }

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        MapActorState &actor = m_mapActors[actorIndex];

        if (actor.actorId != actorId)
        {
            continue;
        }

        if (isActorUnavailableForCombat(actor))
        {
            return false;
        }

        int appliedDamage = damage;
        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;

        if (pStats != nullptr)
        {
            std::mt19937 rng(
                actor.actorId
                ^ static_cast<uint32_t>(std::max(0, damage)) * 2246822519u
                ^ static_cast<uint32_t>(damageType) * 3266489917u);
            appliedDamage = GameMechanics::resolveMonsterIncomingDamage(
                damage,
                damageType,
                monsterResistanceForDamageType(*pStats, damageType),
                monsterHourOfPowerResistanceBonus(actor),
                rng);
        }

        const int previousHp = actor.currentHp;
        actor.currentHp = std::max(0, actor.currentHp - appliedDamage);
        faceDirection(actor, partyX() - actor.preciseX, partyY() - actor.preciseY);

        if (actor.currentHp <= 0)
        {
            beginDyingState(actor, m_pActorSpriteFrameTable);
            activateOutdoorActorCorpsePhysics(actorIndex);
            spawnMonsterDeathDropsForActor(actorIndex, actor);
            const bx::Vec3 knockback = actorKnockbackVelocity(
                actor.preciseX,
                actor.preciseY,
                actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
                partyX(),
                partyY(),
                partyFootZ(),
                appliedDamage,
                actor.maxHp);
            actor.velocityX = knockback.x;
            actor.velocityY = knockback.y;
            actor.velocityZ = knockback.z;

            if (pStats != nullptr)
            {
                applyMonsterKillReputationPenalty(*this, pStats, actor.group);

                if (m_pParty != nullptr && pStats->experience > 0)
                {
                    m_pParty->grantSharedExperience(
                        gameplayBolsterExperienceReward(
                            pStats->experience,
                            pStats->hitPoints,
                            actor.bolsterRewardMultiplier));
                }

                pushAudioEvent(
                    pStats->deathSoundId,
                    actor.actorId,
                    "monster_death",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
                    true,
                    SoundScope::World);
            }
        }
        else
        {
            if (canEnterHitReaction(actor))
            {
                beginHitReaction(actor, m_pActorSpriteFrameTable);
            }

            if (pStats != nullptr)
            {
                pushAudioEvent(
                    pStats->winceSoundId,
                    actor.actorId,
                    "monster_hit",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
                    true,
                    SoundScope::World);
            }
        }

        return actor.currentHp != previousHp;
    }

    return false;
}

const OutdoorWorldRuntime::MapActorState *OutdoorWorldRuntime::mapActorState(size_t actorIndex) const
{
    if (actorIndex >= m_mapActors.size())
    {
        return nullptr;
    }

    return &m_mapActors[actorIndex];
}

std::optional<GameplayWorldPoint> OutdoorWorldRuntime::partyAttackFallbackProjectionPoint(
    size_t actorIndex) const
{
    const MapActorState *pActor = mapActorState(actorIndex);

    if (pActor == nullptr)
    {
        return std::nullopt;
    }

    return GameplayWorldPoint{
        .x = pActor->preciseX,
        .y = pActor->preciseY,
        .z = pActor->preciseZ + std::max(48.0f, static_cast<float>(pActor->height) * 0.6f),
    };
}

std::optional<GameplayPartyAttackActorFacts> OutdoorWorldRuntime::partyAttackActorFacts(
    size_t actorIndex,
    bool visibleForFallback) const
{
    const MapActorState *pActor = mapActorState(actorIndex);

    if (pActor == nullptr)
    {
        return std::nullopt;
    }

    return GameplayPartyAttackActorFacts{
        .actorIndex = actorIndex,
        .monsterId = pActor->monsterId,
        .displayName = pActor->displayName,
        .position =
            GameplayWorldPoint{
                .x = pActor->preciseX,
                .y = pActor->preciseY,
                .z = pActor->preciseZ,
            },
        .radius = pActor->radius,
        .height = pActor->height,
        .currentHp = pActor->currentHp,
        .maxHp = pActor->maxHp,
        .effectiveArmorClass = effectiveMapActorArmorClass(actorIndex),
        .hourOfPowerPower = monsterHourOfPowerResistanceBonus(*pActor),
        .isDead = pActor->isDead,
        .isInvisible = pActor->isInvisible,
        .hostileToParty = pActor->hostileToParty,
        .visibleForFallback = visibleForFallback,
    };
}

std::vector<GameplayPartyAttackActorFacts> OutdoorWorldRuntime::collectPartyAttackFallbackActors(
    const GameplayPartyAttackFallbackQuery &query) const
{
    std::vector<GameplayPartyAttackActorFacts> actors;
    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, query.viewMatrix.data(), query.projectionMatrix.data());

    for (size_t actorIndex = 0; actorIndex < mapActorCount(); ++actorIndex)
    {
        const std::optional<GameplayWorldPoint> projectionPoint = partyAttackFallbackProjectionPoint(actorIndex);

        if (!projectionPoint)
        {
            continue;
        }

        const bx::Vec3 projected = bx::mulH(
            {
                projectionPoint->x,
                projectionPoint->y,
                projectionPoint->z,
            },
            viewProjectionMatrix);
        const bool visibleForFallback =
            projected.z >= 0.0f
            && projected.z <= 1.0f
            && projected.x >= -1.0f
            && projected.x <= 1.0f
            && projected.y >= -1.0f
            && projected.y <= 1.0f;
        std::optional<GameplayPartyAttackActorFacts> facts = partyAttackActorFacts(actorIndex, visibleForFallback);

        if (facts)
        {
            actors.push_back(*facts);
        }
    }

    return actors;
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
    info.hostileToParty = actor.hostileToParty && !outdoorActorIsPartyControlled(actor.controlMode);
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

    const GameplayActorTargetPolicyState actorTargetPolicyState = buildGameplayActorTargetPolicyState(actor);
    const float partySenseRange =
        m_pGameplayActorService != nullptr
        ? m_pGameplayActorService->partyEngagementRange(actorTargetPolicyState)
        : 0.0f;
    const float deltaPartyX = partyX - actor.preciseX;
    const float deltaPartyY = partyY - actor.preciseY;
    const float distanceToParty = length2d(deltaPartyX, deltaPartyY);
    const auto hasClearOutdoorLineOfSight =
        [this](size_t, size_t, const bx::Vec3 &start, const bx::Vec3 &end) -> bool
    {
        return this->hasClearOutdoorLineOfSight(start, end);
    };
    std::vector<OutdoorCombatTargetCandidate> combatCandidates =
        buildCombatTargetCandidates(
            m_pGameplayActorService,
            actor,
            actorIndex,
            m_mapActors);
    const OutdoorTargetFacts combatTarget =
        resolveOutdoorTargetFacts(
            m_pGameplayActorService,
            eventRuntimeState(),
            actor,
            actorIndex,
            combatCandidates,
            partyX,
            partyY,
            partyZ,
            hasClearOutdoorLineOfSight);
    const bool targetIsParty = combatTarget.kind == OutdoorTargetKind::Party;
    const bool targetIsActor = combatTarget.kind == OutdoorTargetKind::Actor;
    GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService = m_pGameplayActorService;

    if (pActorService == nullptr)
    {
        pActorService = &fallbackActorService;
    }

    const bool partyIsVeryNearActor =
        pActorService->partyIsVeryNearActor(
            distanceToParty,
            partyZ - actor.preciseZ,
            actor.radius,
            actor.height,
            PartyCollisionRadius);
    const OutdoorEngagementState engagement =
        resolveOutdoorEngagementState(
            *pActorService,
            actorTargetPolicyState,
            combatTarget,
            gameplayActorAiTypeFromMonster(pStats->aiType),
            actor.hostilityType,
            actor.currentHp,
            actor.maxHp,
            actor.hostileToParty,
            partyIsVeryNearActor,
            actor.suppressLowHealthFlee);

    info.partySenseRange = partySenseRange;
    info.distanceToParty = distanceToParty;
    info.canSenseParty = combatTarget.partyCanSense;
    info.targetKind = targetIsParty
        ? DebugTargetKind::Party
        : targetIsActor ? DebugTargetKind::Actor : DebugTargetKind::None;
    info.targetActorIndex = combatTarget.actorIndex;
    info.relationToTarget = combatTarget.relationToTarget;
    info.targetDistance = combatTarget.distanceToTarget;
    info.targetEdgeDistance = combatTarget.edgeDistance;
    info.targetCanSense = combatTarget.canSense;
    info.targetHasAttackLineOfSight = combatTarget.attackLineOfSight;

    if (targetIsActor && combatTarget.actorIndex < m_mapActors.size())
    {
        info.targetMonsterId = m_mapActors[combatTarget.actorIndex].monsterId;
    }

    const bool attacking = actor.aiState == ActorAiState::Attacking;
    const bool attackInProgress = attacking && actor.actionSeconds > 0.0f;
    const bool attackJustCompleted = attacking && !attackInProgress && !actor.attackImpactTriggered;

    info.promotionRange = engagement.promotionRange;
    info.shouldPromoteHostility = engagement.shouldPromoteHostility;
    info.shouldEngageTarget = engagement.shouldEngageTarget;
    info.shouldFlee = engagement.shouldFlee;
    info.inMeleeRange = engagement.inMeleeRange;
    info.attackJustCompleted = attackJustCompleted;
    info.attackInProgress = attackInProgress;
    info.friendlyNearParty = engagement.friendlyNearParty;
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
        static_cast<float>(spawn.x),
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
    const bool leaveCorpse = !isDead || actorShouldLeaveCorpse(m_pMonsterTable, actor);
    actor.isDead = isDead;
    actor.currentHp = isDead ? 0 : actor.maxHp;
    actor.aiState = isDead ? ActorAiState::Dead : ActorAiState::Standing;
    actor.animation = isDead ? ActorAnimation::Dead : ActorAnimation::Standing;
    actor.animationTimeTicks = 0.0f;
    actor.actionSeconds = 0.0f;

    if (isDead && !leaveCorpse)
    {
        actor.isInvisible = true;
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
        actor.velocityZ = 0.0f;
        m_actorCorpsePhysicsActorIndices.erase(
            std::remove(
                m_actorCorpsePhysicsActorIndices.begin(),
                m_actorCorpsePhysicsActorIndices.end(),
                actorIndex),
            m_actorCorpsePhysicsActorIndices.end());

        if (actorIndex < m_mapActorCorpseViews.size())
        {
            m_mapActorCorpseViews[actorIndex].reset();
        }

        if (m_activeCorpseView && m_activeCorpseView->sourceIndex == actorIndex)
        {
            m_activeCorpseView.reset();
        }
    }
    else if (isDead)
    {
        activateOutdoorActorCorpsePhysics(actorIndex);
    }
    else
    {
        m_actorCorpsePhysicsActorIndices.erase(
            std::remove(
                m_actorCorpsePhysicsActorIndices.begin(),
                m_actorCorpsePhysicsActorIndices.end(),
                actorIndex),
            m_actorCorpsePhysicsActorIndices.end());
    }

    if (!wasDead && isDead && m_pMonsterTable != nullptr)
    {
        markRuntimeBountyHuntMonsterKilled(*this, actor.monsterId, m_pMonsterTable);
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats != nullptr)
        {
            if (actorIndex >= m_mapActorCorpseViews.size())
            {
                m_mapActorCorpseViews.resize(actorIndex + 1);
            }

            if (emitAudio)
            {
                pushAudioEvent(
                    pStats->deathSoundId,
                    actor.actorId,
                    "monster_death",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
                    true,
                    SoundScope::World);
            }
        }
    }

    if (wasDead && !isDead && actorIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[actorIndex].reset();
    }

    if (wasDead && !isDead)
    {
        actor.isInvisible = false;
        actor.bloodSplatSpawned = false;
        removeBloodSplat(actor.actorId);
    }

    return true;
}

bool OutdoorWorldRuntime::applyMonsterActorMeleeAttackToMapActor(
    size_t actorIndex,
    int damage,
    uint32_t sourceActorId,
    int attackBonus,
    CombatDamageType damageType)
{
    if (actorIndex >= m_mapActors.size() || damage <= 0)
    {
        return false;
    }

    MapActorState &targetActor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(targetActor))
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

    const MonsterTable::MonsterStatsEntry *pSourceStats =
        pSourceActor != nullptr && m_pMonsterTable != nullptr
            ? m_pMonsterTable->findStatsById(pSourceActor->monsterId)
            : nullptr;

    if (pSourceStats != nullptr)
    {
        std::mt19937 hitRng(
            monsterActorAttackSeed(
                sourceActorId,
                targetActor.actorId,
                pSourceActor->attackDecisionCount,
                damage,
                damageType,
                0x9e3779b9u));

        if (!GameMechanics::monsterAttackHitsArmorClass(
                effectiveMapActorArmorClass(actorIndex),
                pSourceStats->level,
                attackBonus,
                hitRng))
        {
            return false;
        }
    }

    int appliedDamage = damage;
    const MonsterTable::MonsterStatsEntry *pTargetStats =
        m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(targetActor.monsterId) : nullptr;

    if (pTargetStats != nullptr)
    {
        std::mt19937 damageRng(
            monsterActorAttackSeed(
                sourceActorId,
                targetActor.actorId,
                pSourceActor != nullptr ? pSourceActor->attackDecisionCount : 0,
                damage,
                damageType,
                0x85ebca6bu));
        appliedDamage = GameMechanics::resolveMonsterIncomingDamage(
            damage,
            damageType,
            monsterResistanceForDamageType(*pTargetStats, damageType),
            monsterHourOfPowerResistanceBonus(targetActor),
            damageRng);
    }

    return applyMonsterAttackToMapActor(actorIndex, appliedDamage, sourceActorId, false, true);
}

bool OutdoorWorldRuntime::applyMonsterAttackToMapActor(
    size_t actorIndex,
    int damage,
    uint32_t sourceActorId,
    bool emitAudio,
    bool allowZeroDamageHit)
{
    if (actorIndex >= m_mapActors.size()
        || damage < 0
        || (damage == 0 && !allowZeroDamageHit))
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

    const int previousHp = actor.currentHp;
    actor.currentHp = std::max(0, actor.currentHp - damage);

    if (pSourceActor != nullptr)
    {
        faceDirection(actor, pSourceActor->preciseX - actor.preciseX, pSourceActor->preciseY - actor.preciseY);
    }

    if (actor.currentHp <= 0)
    {
        beginDyingState(actor, m_pActorSpriteFrameTable);
        activateOutdoorActorCorpsePhysics(actorIndex);
        spawnMonsterDeathDropsForActor(actorIndex, actor);
        const float sourceX = pSourceActor != nullptr ? pSourceActor->preciseX : actor.preciseX;
        const float sourceY = pSourceActor != nullptr ? pSourceActor->preciseY : actor.preciseY;
        const float sourceZ =
            pSourceActor != nullptr
                ? pSourceActor->preciseZ + static_cast<float>(pSourceActor->height) * 0.5f
                : actor.preciseZ + static_cast<float>(actor.height) * 0.5f;
        const bx::Vec3 knockback = actorKnockbackVelocity(
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
            sourceX,
            sourceY,
            sourceZ,
            damage,
            actor.maxHp);
        actor.velocityX = knockback.x;
        actor.velocityY = knockback.y;
        actor.velocityZ = knockback.z;

        if (emitAudio && m_pMonsterTable != nullptr)
        {
            if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
            {
                pushAudioEvent(
                    pStats->deathSoundId,
                    actor.actorId,
                    "monster_death",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
                    true,
                    SoundScope::World);
            }
        }

        return true;
    }

    if (canEnterHitReaction(actor))
    {
        beginHitReaction(actor, m_pActorSpriteFrameTable);
        const float sourceX = pSourceActor != nullptr ? pSourceActor->preciseX : actor.preciseX;
        const float sourceY = pSourceActor != nullptr ? pSourceActor->preciseY : actor.preciseY;
        const float sourceZ =
            pSourceActor != nullptr
                ? pSourceActor->preciseZ + static_cast<float>(pSourceActor->height) * 0.5f
                : actor.preciseZ + static_cast<float>(actor.height) * 0.5f;
        const bx::Vec3 knockback = actorKnockbackVelocity(
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
            sourceX,
            sourceY,
            sourceZ,
            damage,
            actor.maxHp);
        actor.velocityX = knockback.x;
        actor.velocityY = knockback.y;
        actor.velocityZ = knockback.z;
    }

    if (emitAudio && m_pMonsterTable != nullptr)
    {
        if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
        {
            pushAudioEvent(
                pStats->winceSoundId,
                actor.actorId,
                "monster_hit",
                actor.preciseX,
                actor.preciseY,
                actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
                true,
                SoundScope::World);
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
            m_pSpellTable,
            m_pOutdoorMapData,
            *pStats,
            GameplayBolsterRuntimeContext{
                .pMap = &m_map,
                .pMonsterTable = m_pMonsterTable,
                .pBolsterMapTable = m_pMergedBolsterMapTable,
                .pBolsterMonsterTable = m_pMergedBolsterMonsterTable,
                .pParty = m_pParty,
                .bolsterMonstersEnabled = m_bolsterMonstersEnabled,
            },
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
        applyOeOutdoorActorFloorCorrection(actor, *pStats);

        if (m_outdoorMovementController)
        {
            const float collisionRadius = actorCollisionRadius(actor, pStats);
            actor.movementState = m_outdoorMovementController->initializeActorStateForBodyPreservingZ(
                actor.preciseX,
                actor.preciseY,
                actor.preciseZ + GroundSnapHeight,
                collisionRadius);
            actor.movementStateInitialized = true;
            actor.movementState.verticalVelocity = actor.velocityZ;
            syncActorFromMovementState(actor);
        }

        m_mapActors.push_back(std::move(actor));
        spawnedAny = true;
    }

    if (spawnedAny)
    {
        applyEventRuntimeState(true);
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
    const MonsterTable::MonsterStatsEntry *pVictimStats = m_pMonsterTable->findStatsById(victim.monsterId);

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

        const bool sameEventGroup = victim.group != 0 && victim.group == otherActor.group;
        const bool sameMonsterFaction = m_pMonsterTable->isLikelySameFaction(victim.monsterId, otherActor.monsterId);
        const MonsterTable::MonsterStatsEntry *pOtherStats = m_pMonsterTable->findStatsById(otherActor.monsterId);
        const bool sameCivilianAggression =
            actorSharesCivilianAggression(victim.group, pVictimStats, otherActor.group, pOtherStats);

        if (!sameEventGroup && !sameMonsterFaction && !sameCivilianAggression)
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
    float partyZ,
    bool allowHitReaction)
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

    if (m_pGameplayActorService != nullptr
        && m_pGameplayActorService->hasPainReflection(buildGameplayActorSpellEffectState(actor))
        && m_pParty != nullptr)
    {
        m_pParty->applyDamageToActiveMember(damage, "pain reflection");
    }

    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;
    const bool suppressLowHealthFlee =
        actor.aiState == ActorAiState::Fleeing
        && pStats != nullptr
        && gameplayActorAiTypeFromMonster(pStats->aiType) != GameplayActorAiType::Wimp;

    GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService =
        m_pGameplayActorService != nullptr ? m_pGameplayActorService : &fallbackActorService;
    GameplayActorSpellEffectState effectState = buildGameplayActorSpellEffectState(actor);
    pActorService->breakFearAndControlOnPartyDamage(effectState);
    applyGameplayActorSpellEffectState(effectState, actor);

    if (suppressLowHealthFlee)
    {
        actor.suppressLowHealthFlee = true;
        actor.aiState = ActorAiState::Standing;
        actor.animation = ActorAnimation::Standing;
        actor.actionSeconds = 0.0f;
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
    }

    const int previousHp = actor.currentHp;
    actor.currentHp = std::max(0, actor.currentHp - damage);
    const int dealtDamage = std::max(0, previousHp - actor.currentHp);
    int experienceReward = 0;
    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
    setMapActorHostileToParty(actorIndex, partyX, partyY, partyZ, false);

    const bool died = actor.currentHp <= 0;

    if (died)
    {
        beginDyingState(actor, m_pActorSpriteFrameTable);
        activateOutdoorActorCorpsePhysics(actorIndex);
        spawnMonsterDeathDropsForActor(actorIndex, actor);
        const bx::Vec3 knockback = actorKnockbackVelocity(
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
            partyX,
            partyY,
            partyZ,
            damage,
            actor.maxHp);
        actor.velocityX = knockback.x;
        actor.velocityY = knockback.y;
        actor.velocityZ = knockback.z;

        if (m_pMonsterTable != nullptr)
        {
            if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
            {
                applyMonsterKillReputationPenalty(*this, pStats, actor.group);

                if (m_pParty != nullptr && pStats->experience > 0)
                {
                    experienceReward = static_cast<int>(
                        gameplayBolsterExperienceReward(
                            pStats->experience,
                            pStats->hitPoints,
                            actor.bolsterRewardMultiplier));
                    m_pParty->grantSharedExperience(static_cast<uint32_t>(experienceReward));
                }

                pushAudioEvent(
                    pStats->deathSoundId,
                    actor.actorId,
                    "monster_death",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
                    true,
                    SoundScope::World);
            }
        }
    }
    else
    {
        if (allowHitReaction && canEnterHitReaction(actor))
        {
            faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
            beginHitReaction(actor, m_pActorSpriteFrameTable);
            const bx::Vec3 knockback = actorKnockbackVelocity(
                actor.preciseX,
                actor.preciseY,
                actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
                partyX,
                partyY,
                partyZ,
                damage,
                actor.maxHp);
            actor.velocityX = knockback.x;
            actor.velocityY = knockback.y;
            actor.velocityZ = knockback.z;
        }

        if (allowHitReaction && m_pMonsterTable != nullptr)
        {
            if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
            {
                pushAudioEvent(
                    pStats->winceSoundId,
                    actor.actorId,
                    "monster_hit",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
                    true,
                    SoundScope::World);
            }
        }
    }

    if (dealtDamage > 0)
    {
        m_arpgModeCombatFeedbackEvents.push_back(
            GameplayArpgCombatFeedbackEvent{
                .actorIndex = actorIndex,
                .damage = dealtDamage,
                .experience = experienceReward,
                .x = actor.preciseX,
                .y = actor.preciseY,
                .z = actor.preciseZ,
                .height = static_cast<float>(actor.height),
                .killed = previousHp > 0 && actor.currentHp <= 0,
            });
    }

    aggroNearbyMapActorFaction(actorIndex, partyX, partyY, partyZ);
    return true;
}

bool OutdoorWorldRuntime::applyPartyAttackMeleeDamage(
    size_t actorIndex,
    int damage,
    const GameplayWorldPoint &source)
{
    return applyPartyAttackToMapActor(actorIndex, damage, source.x, source.y, source.z);
}

bool OutdoorWorldRuntime::applyPartyChannelDamage(
    size_t actorIndex,
    int damage,
    const GameplayWorldPoint &source,
    bool allowHitReaction)
{
    return applyPartyAttackToMapActor(
        actorIndex,
        damage,
        source.x,
        source.y,
        source.z,
        allowHitReaction);
}

void OutdoorWorldRuntime::applyPartyAttackMeleeEffects(
    size_t actorIndex,
    const CharacterAttackResult &attack,
    const GameplayWorldPoint &source)
{
    if (actorIndex >= m_mapActors.size()
        || (!attack.stunTarget && !attack.paralyzeTarget && !attack.halveTargetArmorClass))
    {
        return;
    }

    const uint32_t skillLevel = std::max<uint32_t>(1, attack.skillLevel);
    const float skillSeconds = static_cast<float>(skillLevel) * 60.0f;
    MapActorState &actor = m_mapActors[actorIndex];

    if (actor.currentHp <= 0
        || actor.aiState == ActorAiState::Dying
        || actor.aiState == ActorAiState::Dead
        || actor.isDead)
    {
        return;
    }

    if (attack.stunTarget)
    {
        actor.stunRemainingSeconds =
            std::max(actor.stunRemainingSeconds, 0.5f + 0.35f * static_cast<float>(skillLevel));
        actor.aiState = ActorAiState::Stunned;
        actor.animation = ActorAnimation::GotHit;
        actor.actionSeconds = std::max(actor.actionSeconds, actor.stunRemainingSeconds);
        const bx::Vec3 knockback = actorKnockbackVelocity(
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
            source.x,
            source.y,
            source.z,
            actor.maxHp,
            actor.maxHp);
        actor.velocityX = knockback.x;
        actor.velocityY = knockback.y;
        actor.velocityZ = knockback.z;
    }

    if (attack.paralyzeTarget)
    {
        actor.paralyzeRemainingSeconds = std::max(actor.paralyzeRemainingSeconds, skillSeconds);
    }

    if (attack.halveTargetArmorClass)
    {
        actor.armorClassHalvedRemainingSeconds = std::max(actor.armorClassHalvedRemainingSeconds, skillSeconds);
    }
}

bool OutdoorWorldRuntime::spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request)
{
    PartyProjectileRequest worldRequest = {};
    worldRequest.sourcePartyMemberIndex = static_cast<uint32_t>(request.sourcePartyMemberIndex);
    worldRequest.objectId = request.objectId;
    worldRequest.impactObjectId = request.impactObjectId;
    worldRequest.damage = request.damage;
    worldRequest.attackBonus = request.attackBonus;
    worldRequest.useActorHitChance = request.useActorHitChance;
    worldRequest.damageType = request.damageType;
    worldRequest.sourceX = request.source.x;
    worldRequest.sourceY = request.source.y;
    worldRequest.sourceZ = request.source.z;
    worldRequest.targetX = request.target.x;
    worldRequest.targetY = request.target.y;
    worldRequest.targetZ = request.target.z;
    return spawnPartyProjectile(worldRequest);
}

bool OutdoorWorldRuntime::castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request)
{
    SpellCastRequest worldRequest = {};
    worldRequest.sourceKind = RuntimeSpellSourceKind::Party;
    worldRequest.sourceId = static_cast<uint32_t>(request.sourcePartyMemberIndex + 1);
    worldRequest.sourcePartyMemberIndex = static_cast<uint32_t>(request.sourcePartyMemberIndex);
    worldRequest.ability = MonsterAttackAbility::Spell1;
    worldRequest.spellId = request.spellId;
    worldRequest.skillLevel = request.skillLevel;
    worldRequest.skillMastery = request.skillMastery;
    worldRequest.damage = request.damage;
    worldRequest.attackBonus = request.attackBonus;
    worldRequest.useActorHitChance = request.useActorHitChance;
    worldRequest.sourceX = request.source.x;
    worldRequest.sourceY = request.source.y;
    worldRequest.sourceZ = request.source.z;
    worldRequest.targetX = request.target.x;
    worldRequest.targetY = request.target.y;
    worldRequest.targetZ = request.target.z;
    return castPartySpell(worldRequest);
}

void OutdoorWorldRuntime::playArpgModePartyActionAnimation(float animationSeconds, bool spellCast)
{
    if (m_pInteractionView != nullptr)
    {
        m_pInteractionView->playArpgModePartyActionAnimation(animationSeconds, spellCast);
    }
}

void OutdoorWorldRuntime::sustainArpgModePartyActionAnimation(float animationSeconds, bool spellCast)
{
    if (m_pInteractionView != nullptr)
    {
        m_pInteractionView->sustainArpgModePartyActionAnimation(animationSeconds, spellCast);
    }
}

void OutdoorWorldRuntime::cancelArpgModePartyActionAnimation()
{
    if (m_pInteractionView != nullptr)
    {
        m_pInteractionView->cancelArpgModePartyActionAnimation();
    }
}

void OutdoorWorldRuntime::faceArpgModePartyActionTarget(const PartySpellCastRequest &request)
{
    if (m_pInteractionView == nullptr || !m_pInteractionView->arpgModeEnabled())
    {
        return;
    }

    std::optional<bx::Vec3> targetPoint;

    if (request.targetActorIndex)
    {
        targetPoint = spellActionActorTargetPoint(*request.targetActorIndex);
    }
    else if (request.hasTargetPoint)
    {
        targetPoint = bx::Vec3{request.targetX, request.targetY, request.targetZ};
    }

    if (!targetPoint)
    {
        return;
    }

    m_pInteractionView->faceArpgModeTargetPoint(targetPoint->x, targetPoint->y);
}

void OutdoorWorldRuntime::addChannelBeamFx(const GameplayChannelBeamFx &beam)
{
    if (m_pWorldFxSystem == nullptr)
    {
        return;
    }

    WorldFxBeam fxBeam = {};
    fxBeam.startX = beam.start.x;
    fxBeam.startY = beam.start.y;
    fxBeam.startZ = beam.start.z;
    fxBeam.endX = beam.end.x;
    fxBeam.endY = beam.end.y;
    fxBeam.endZ = beam.end.z;
    fxBeam.radius = beam.radius;
    fxBeam.intensity = beam.intensity;
    fxBeam.phaseSeconds = beam.phaseSeconds;
    fxBeam.remainingSeconds = 0.16f;
    fxBeam.coreColorAbgr = beam.coreColorAbgr;
    fxBeam.glowColorAbgr = beam.glowColorAbgr;
    fxBeam.stableId = beam.stableId;
    m_pWorldFxSystem->addBeam(fxBeam);
}

GameplayWorldPoint OutdoorWorldRuntime::clipChannelBeamTarget(
    const GameplayWorldPoint &source,
    const GameplayWorldPoint &target) const
{
    if (m_pOutdoorMapData == nullptr)
    {
        return target;
    }

    const bx::Vec3 segmentStart = {source.x, source.y, source.z};
    const bx::Vec3 segmentEnd = {target.x, target.y, target.z};
    const float segmentX = target.x - source.x;
    const float segmentY = target.y - source.y;
    const float segmentZ = target.z - source.z;
    const float segmentLength =
        std::sqrt(segmentX * segmentX + segmentY * segmentY + segmentZ * segmentZ);
    float bestFactor = 1.0f;

    if (segmentLength <= 1.0f)
    {
        return target;
    }

    std::vector<size_t> candidateFaceIndices;
    constexpr float FaceCandidatePadding = 32.0f;
    collectOutdoorFaceCandidates(
        std::min(source.x, target.x) - FaceCandidatePadding,
        std::min(source.y, target.y) - FaceCandidatePadding,
        std::max(source.x, target.x) + FaceCandidatePadding,
        std::max(source.y, target.y) + FaceCandidatePadding,
        candidateFaceIndices);

    for (size_t candidateFaceIndex : candidateFaceIndices)
    {
        const OutdoorFaceGeometryData *pFaceGeometry = outdoorFace(candidateFaceIndex);

        if (pFaceGeometry == nullptr
            || !pFaceGeometry->hasPlane
            || hasFaceAttribute(pFaceGeometry->attributes, FaceAttribute::Invisible))
        {
            continue;
        }

        if (std::max(source.z, target.z) + FaceCandidatePadding < pFaceGeometry->minZ
            || std::min(source.z, target.z) - FaceCandidatePadding > pFaceGeometry->maxZ)
        {
            continue;
        }

        float factor = 0.0f;
        bx::Vec3 intersectionPoint = {0.0f, 0.0f, 0.0f};

        if (intersectOutdoorSegmentWithFace(
                *pFaceGeometry,
                segmentStart,
                segmentEnd,
                factor,
                intersectionPoint)
            && factor > 0.01f)
        {
            bestFactor = std::min(bestFactor, factor);
        }
    }

    const int sampleCount = std::clamp(static_cast<int>(std::ceil(segmentLength / 64.0f)), 1, 96);
    float previousFactor = 0.0f;

    for (int sampleIndex = 1; sampleIndex <= sampleCount; ++sampleIndex)
    {
        const float factor = static_cast<float>(sampleIndex) / static_cast<float>(sampleCount);

        if (factor >= bestFactor)
        {
            break;
        }

        const float x = source.x + segmentX * factor;
        const float y = source.y + segmentY * factor;
        const float z = source.z + segmentZ * factor;
        const float terrainHeight = sampleOutdoorRenderedTerrainHeight(*m_pOutdoorMapData, x, y);

        if (terrainHeight + 8.0f >= z)
        {
            float lowFactor = previousFactor;
            float highFactor = factor;

            for (int iteration = 0; iteration < 8; ++iteration)
            {
                const float midFactor = (lowFactor + highFactor) * 0.5f;
                const float midX = source.x + segmentX * midFactor;
                const float midY = source.y + segmentY * midFactor;
                const float midZ = source.z + segmentZ * midFactor;
                const float midTerrainHeight =
                    sampleOutdoorRenderedTerrainHeight(*m_pOutdoorMapData, midX, midY);

                if (midTerrainHeight + 8.0f >= midZ)
                {
                    highFactor = midFactor;
                }
                else
                {
                    lowFactor = midFactor;
                }
            }

            bestFactor = std::min(bestFactor, highFactor);
            break;
        }

        previousFactor = factor;
    }

    return GameplayWorldPoint{
        source.x + segmentX * bestFactor,
        source.y + segmentY * bestFactor,
        source.z + segmentZ * bestFactor
    };
}

void OutdoorWorldRuntime::recordPartyAttackWorldResult(
    std::optional<size_t> actorIndex,
    bool attacked,
    bool actionPerformed)
{
    if (!m_eventRuntimeState)
    {
        return;
    }

    if (actorIndex)
    {
        m_eventRuntimeState->lastActivationResult =
            attacked
                ? "actor " + std::to_string(*actorIndex) + " hit by party"
                : "actor " + std::to_string(*actorIndex) + " attacked by party";
        return;
    }

    m_eventRuntimeState->lastActivationResult =
        actionPerformed
            ? "party attack released"
            : "party attack failed";
}

bool OutdoorWorldRuntime::worldInteractionReady() const
{
    return m_pOutdoorMapData != nullptr;
}

bool OutdoorWorldRuntime::worldInspectModeActive() const
{
    return m_pInteractionView != nullptr && OutdoorInteractionController::worldInspectModeActive(*m_pInteractionView);
}

GameplayWorldPickRequest OutdoorWorldRuntime::buildWorldPickRequest(const GameplayWorldPickRequestInput &input) const
{
    if (m_pInteractionView == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::buildWorldPickRequest(*m_pInteractionView, input);
}

std::optional<GameplayHeldItemDropRequest> OutdoorWorldRuntime::buildHeldItemDropRequest() const
{
    if (m_pInteractionView == nullptr)
    {
        return std::nullopt;
    }

    return OutdoorInteractionController::buildHeldItemDropRequest(*m_pInteractionView);
}

GameplayPartyAttackFrameInput OutdoorWorldRuntime::buildPartyAttackFrameInput(
    const GameplayWorldPickRequest &pickRequest) const
{
    if (m_pInteractionView == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::buildPartyAttackFrameInput(*m_pInteractionView, pickRequest);
}

std::optional<size_t> OutdoorWorldRuntime::spellActionHoveredActorIndex() const
{
    if (m_pInteractionView == nullptr)
    {
        return std::nullopt;
    }

    return OutdoorInteractionController::resolveSpellActionHoveredActorIndex(*m_pInteractionView);
}

std::optional<size_t> OutdoorWorldRuntime::spellActionClosestVisibleHostileActorIndex() const
{
    if (m_pInteractionView == nullptr || m_pPartyRuntime == nullptr)
    {
        return std::nullopt;
    }

    const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();
    return OutdoorInteractionController::resolveClosestVisibleHostileActorIndex(
        *m_pInteractionView,
        moveState.x,
        moveState.y,
        moveState.footZ + 96.0f);
}

std::optional<bx::Vec3> OutdoorWorldRuntime::spellActionActorTargetPoint(size_t actorIndex) const
{
    if (m_pInteractionView == nullptr)
    {
        return std::nullopt;
    }

    return OutdoorInteractionController::resolveSpellActionActorTargetPoint(*m_pInteractionView, actorIndex);
}

std::optional<bx::Vec3> OutdoorWorldRuntime::spellActionGroundTargetPoint(float screenX, float screenY) const
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return std::nullopt;
    }

    return OutdoorInteractionController::resolveQuickCastCursorTargetPoint(*m_pInteractionView, screenX, screenY);
}

std::optional<bx::Vec3> OutdoorWorldRuntime::spellActionCursorPlaneTargetPoint(
    float screenX,
    float screenY,
    float planeZ,
    float fallbackDistance) const
{
    if (m_pInteractionView == nullptr)
    {
        return std::nullopt;
    }

    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!OutdoorInteractionController::buildQuickCastInspectRayForScreenPoint(
            *m_pInteractionView,
            screenX,
            screenY,
            rayOrigin,
            rayDirection))
    {
        return std::nullopt;
    }

    constexpr float RayEpsilon = 0.0001f;

    if (std::fabs(rayDirection.z) > RayEpsilon)
    {
        const float planeDistance = (planeZ - rayOrigin.z) / rayDirection.z;

        if (planeDistance > RayEpsilon)
        {
            return bx::Vec3{
                rayOrigin.x + rayDirection.x * planeDistance,
                rayOrigin.y + rayDirection.y * planeDistance,
                planeZ
            };
        }
    }

    const float horizontalLengthSquared = rayDirection.x * rayDirection.x + rayDirection.y * rayDirection.y;

    if (horizontalLengthSquared <= RayEpsilon * RayEpsilon)
    {
        return std::nullopt;
    }

    const float horizontalLength = std::sqrt(horizontalLengthSquared);
    return bx::Vec3{
        rayOrigin.x + rayDirection.x / horizontalLength * fallbackDistance,
        rayOrigin.y + rayDirection.y / horizontalLength * fallbackDistance,
        planeZ
    };
}

bool OutdoorWorldRuntime::applyDirectSpellImpactToMapActor(
    size_t actorIndex,
    uint32_t spellId,
    float partyX,
    float partyY,
    float partyZ,
    uint32_t sourcePartyMemberIndex,
    const GameplayActorService::DirectSpellImpactResult &impact)
{
    if (actorIndex >= m_mapActors.size()
        || impact.disposition != GameplayActorService::DirectSpellImpactDisposition::ApplyDamage)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (impact.visualKind == GameplayActorService::DirectSpellImpactVisualKind::ActorCenter)
    {
        spawnImmediateSpellVisual(
            spellId,
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
            impact.centerVisual,
            impact.preferImpactObject);
    }
    else if (impact.visualKind == GameplayActorService::DirectSpellImpactVisualKind::ActorUpperBody)
    {
        spawnImmediateSpellVisual(
            spellId,
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + static_cast<float>(actor.height) * 0.8f,
            impact.centerVisual,
            impact.preferImpactObject);
    }

    int appliedDamage = impact.damage;
    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;
    const CombatDamageType damageType = GameMechanics::spellCombatDamageType(spellId, m_pSpellTable);

    if (pStats != nullptr)
    {
        std::mt19937 rng(
            actor.actorId
            ^ spellId * 3266489917u
            ^ static_cast<uint32_t>(std::max(0, impact.damage)));
        appliedDamage = GameMechanics::resolveMonsterIncomingDamage(
            impact.damage,
            damageType,
            monsterResistanceForDamageType(*pStats, damageType),
            monsterHourOfPowerResistanceBonus(actor),
            rng);
    }

    const int beforeHp = actor.currentHp;
    const bool applied = applyPartyAttackToMapActor(actorIndex, appliedDamage, partyX, partyY, partyZ);

    if (applied && m_pGameplayCombatController != nullptr)
    {
        m_pGameplayCombatController->recordPartyProjectileActorImpact(
            0,
            sourcePartyMemberIndex,
            actor.actorId,
            appliedDamage,
            static_cast<int>(spellId),
            true,
            beforeHp > 0 && actor.currentHp <= 0);
    }

    return applied;
}

bool OutdoorWorldRuntime::applyPartySpellToMapActor(
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
    if (actorIndex >= m_mapActors.size() || m_pSpellTable == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];
    const std::string &spellName = pSpellEntry->normalizedName;

    if (spellName == "reanimate")
    {
        if (actor.isInvisible
            || (!actor.isDead
                && actor.currentHp > 0
                && actor.aiState != ActorAiState::Dying
                && actor.aiState != ActorAiState::Dead))
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

        spawnImmediateSpellVisual(
            spellId,
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + static_cast<float>(actor.height) * 0.8f,
            false,
            false);

        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;

        if (pStats != nullptr && pStats->level > targetMonsterLevel)
        {
            return true;
        }

        return resurrectMapActor(actorIndex, targetMonsterLevel * 10, true);
    }

    if (isActorUnavailableForCombat(actor))
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;

    const auto spawnTargetDebuffParticles = [this, spellId, &actor, partyX, partyY]()
    {
        if (m_pWorldFxSystem == nullptr)
        {
            return;
        }

        const float frontDirectionX = actor.preciseX - partyX;
        const float frontDirectionY = actor.preciseY - partyY;
        const uint32_t seed =
            actor.actorId * 2246822519u
            ^ spellId * 3266489917u
            ^ projectileService().allocateProjectileImpactId();
        m_pWorldFxSystem->spawnActorDebuffFx(
            spellId,
            seed,
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ,
            static_cast<float>(actor.height),
            frontDirectionX,
            frontDirectionY);
    };

    GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService = m_pGameplayActorService;

    if (pActorService == nullptr)
    {
        fallbackActorService.bindTables(m_pMonsterTable, m_pSpellTable);
        pActorService = &fallbackActorService;
    }

    if (pActorService != nullptr)
    {
        const GameplayActorService::DirectSpellImpactResult directImpact =
            pActorService->resolveDirectSpellImpact(
                spellId,
                skillLevel,
                damage,
                actor.currentHp,
                pActorService->actorLooksUndead(actor.monsterId));

        if (directImpact.disposition == GameplayActorService::DirectSpellImpactDisposition::Rejected)
        {
            return false;
        }

        if (directImpact.disposition == GameplayActorService::DirectSpellImpactDisposition::ApplyDamage)
        {
            return applyDirectSpellImpactToMapActor(
                actorIndex,
                spellId,
                partyX,
                partyY,
                partyZ,
                sourcePartyMemberIndex,
                directImpact);
        }

        const bool baselineHostileToParty = actor.hostileToParty;
        GameplayActorSpellEffectState effectState = buildGameplayActorSpellEffectState(actor);
        const GameplayActorService::SharedSpellEffectResult effectResult =
            pActorService->tryApplySharedSpellEffect(
                spellId,
                skillLevel,
                skillMastery,
                pActorService->actorLooksUndead(actor.monsterId),
                baselineHostileToParty,
                pStats != nullptr
                    ? monsterResistanceForDamageType(
                        *pStats,
                        GameMechanics::spellCombatDamageType(spellId, m_pSpellTable))
                    : 0,
                effectState);

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Rejected)
        {
            return false;
        }

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Applied)
        {
            applyGameplayActorSpellEffectState(effectState, actor);

            const auto resetActorMotion =
                [&actor]()
            {
                actor.aiState = ActorAiState::Standing;
                actor.animation = ActorAnimation::Standing;
                actor.animationTimeTicks = 0.0f;
                actor.actionSeconds = 0.0f;
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.velocityZ = 0.0f;
                actor.attackImpactTriggered = false;
            };

            switch (effectResult.effectKind)
            {
                case GameplayActorService::SharedSpellEffectKind::Stun:
                {
                    actor.aiState = ActorAiState::Stunned;
                    actor.animation = ActorAnimation::GotHit;
                    actor.actionSeconds = std::max(actor.actionSeconds, actor.stunRemainingSeconds);
                    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
                    break;
                }

                case GameplayActorService::SharedSpellEffectKind::Paralyze:
                case GameplayActorService::SharedSpellEffectKind::Control:
                {
                    resetActorMotion();
                    break;
                }

                case GameplayActorService::SharedSpellEffectKind::Fear:
                {
                    if (spellName == "fear")
                    {
                        const float deltaX = actor.preciseX - partyX;
                        const float deltaY = actor.preciseY - partyY;
                        const float horizontalLength = std::sqrt(deltaX * deltaX + deltaY * deltaY);

                        if (horizontalLength > 0.01f)
                        {
                            const float pushStrength = 160.0f + 8.0f * static_cast<float>(skillLevel);
                            actor.velocityX = (deltaX / horizontalLength) * pushStrength;
                            actor.velocityY = (deltaY / horizontalLength) * pushStrength;
                        }

                        actor.animation = ActorAnimation::GotHit;
                        actor.actionSeconds = std::max(actor.actionSeconds, 0.3f);
                    }
                    else
                    {
                        resetActorMotion();
                    }

                    break;
                }

                case GameplayActorService::SharedSpellEffectKind::Blind:
                {
                    actor.animation = ActorAnimation::GotHit;
                    break;
                }

                case GameplayActorService::SharedSpellEffectKind::Slow:
                case GameplayActorService::SharedSpellEffectKind::Shrink:
                case GameplayActorService::SharedSpellEffectKind::DarkGrasp:
                case GameplayActorService::SharedSpellEffectKind::DispelMagic:
                case GameplayActorService::SharedSpellEffectKind::None:
                default:
                {
                    break;
                }
            }

            if (effectResult.effectKind != GameplayActorService::SharedSpellEffectKind::DispelMagic)
            {
                spawnTargetDebuffParticles();
            }

            return true;
        }
    }

    if (spellName == "fear" || spellName == "wing buffet")
    {
        if (spellName == "fear")
        {
            actor.fearRemainingSeconds = std::max(
                actor.fearRemainingSeconds,
                skillMastery == SkillMastery::Expert
                    ? minutesToSeconds(5.0f + static_cast<float>(skillLevel))
                    : minutesToSeconds(3.0f + static_cast<float>(skillLevel)));
            actor.hasDetectedParty = false;
            spawnTargetDebuffParticles();
        }

        const float deltaX = actor.preciseX - partyX;
        const float deltaY = actor.preciseY - partyY;
        const float horizontalLength = std::sqrt(deltaX * deltaX + deltaY * deltaY);

        if (horizontalLength > 0.01f)
        {
            const float pushStrength =
                spellName == "wing buffet"
                    ? 320.0f + 24.0f * static_cast<float>(skillLevel)
                    : 160.0f + 8.0f * static_cast<float>(skillLevel);
            actor.velocityX = (deltaX / horizontalLength) * pushStrength;
            actor.velocityY = (deltaY / horizontalLength) * pushStrength;
        }

        actor.animation = ActorAnimation::GotHit;
        actor.actionSeconds = std::max(actor.actionSeconds, 0.3f);
        return true;
    }

    return false;
}

bool OutdoorWorldRuntime::spawnImmediateSpellVisual(
    uint32_t spellId,
    float x,
    float y,
    float z,
    bool centerVertically,
    bool preferImpactObject)
{
    if (m_pSpellTable == nullptr || m_pObjectTable == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    ResolvedProjectileDefinition definition = {};

    if (!resolveSpellDefinition(*pSpellEntry, *m_pObjectTable, definition))
    {
        return false;
    }

    uint16_t effectDescriptionId = preferImpactObject ? definition.impactObjectDescriptionId : definition.objectDescriptionId;
    uint16_t effectSpriteId = preferImpactObject ? definition.impactObjectSpriteId : definition.objectSpriteId;
    std::string effectObjectName = preferImpactObject ? definition.impactObjectName : definition.objectName;
    std::string effectSpriteName = preferImpactObject ? definition.impactObjectSpriteName : definition.objectSpriteName;

    if (effectDescriptionId == 0)
    {
        effectDescriptionId = preferImpactObject ? definition.objectDescriptionId : definition.impactObjectDescriptionId;
        effectSpriteId = preferImpactObject ? definition.objectSpriteId : definition.impactObjectSpriteId;
        effectObjectName = preferImpactObject ? definition.objectName : definition.impactObjectName;
        effectSpriteName = preferImpactObject ? definition.objectSpriteName : definition.impactObjectSpriteName;
    }

    if (effectDescriptionId == 0)
    {
        return false;
    }

    const SpellId resolvedSpellId = spellIdFromValue(spellId);
    uint16_t resolvedFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        effectSpriteId,
        effectSpriteName);

    if ((m_pProjectileSpriteFrameTable == nullptr
            || m_pProjectileSpriteFrameTable->getFrame(resolvedFrameIndex, 0) == nullptr)
        && !preferImpactObject)
    {
        applyImmediateSpellVisualFallback(resolvedSpellId, effectSpriteId, effectSpriteName);
        resolvedFrameIndex = resolveRuntimeSpriteFrameIndex(
            m_pProjectileSpriteFrameTable,
            effectSpriteId,
            effectSpriteName);
    }

    const ObjectEntry *pEffectEntry = m_pObjectTable->get(effectDescriptionId);

    if (pEffectEntry == nullptr)
    {
        return false;
    }

    GameplayProjectileService::ProjectileImpactVisualDefinition effectDefinition = {};
    effectDefinition.objectDescriptionId = effectDescriptionId;
    effectDefinition.objectSpriteId = effectSpriteId;
    effectDefinition.objectSpriteFrameIndex = resolvedFrameIndex;
    effectDefinition.objectHeight = pEffectEntry->height;
    effectDefinition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pEffectEntry->lifetimeTicks, 32));
    effectDefinition.hasVisual = effectSpriteId != 0 || !effectSpriteName.empty();
    effectDefinition.objectName = effectObjectName;
    effectDefinition.objectSpriteName = effectSpriteName;

    const GameplayProjectileService::ProjectileImpactSpawnResult result =
        spawnImmediateSpellImpactVisual(
            effectDefinition,
            static_cast<int>(spellId),
            definition.objectName,
            definition.objectSpriteName,
            x,
            y,
            z,
            centerVertically,
            !preferImpactObject);
    return result.spawned;
}

bool OutdoorWorldRuntime::applyPartySpellToActor(
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
    return applyPartySpellToMapActor(
        actorIndex,
        spellId,
        skillLevel,
        skillMastery,
        damage,
        partyX,
        partyY,
        partyZ,
        sourcePartyMemberIndex);
}

bool OutdoorWorldRuntime::healMapActor(size_t actorIndex, int amount)
{
    if (actorIndex >= m_mapActors.size() || amount <= 0)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (actor.isDead)
    {
        return false;
    }

    const int previousHp = actor.currentHp;
    actor.currentHp = std::clamp(actor.currentHp + amount, 0, std::max(1, actor.maxHp));
    return actor.currentHp > previousHp;
}

bool OutdoorWorldRuntime::resurrectMapActor(size_t actorIndex, int health, bool friendlyToParty)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (!actor.isDead
        && actor.currentHp > 0
        && actor.aiState != ActorAiState::Dying
        && actor.aiState != ActorAiState::Dead)
    {
        return false;
    }

    setMapActorDead(actorIndex, false, false);
    actor.currentHp = std::clamp(health, 1, std::max(1, actor.maxHp));
    actor.homePreciseX = actor.preciseX;
    actor.homePreciseY = actor.preciseY;
    actor.homePreciseZ = actor.preciseZ;
    actor.homeX = actor.x;
    actor.homeY = actor.y;
    actor.homeZ = actor.z;
    actor.aiState = ActorAiState::Standing;
    actor.animation = ActorAnimation::Standing;
    actor.animationTimeTicks = 0.0f;
    actor.actionSeconds = 0.0f;
    actor.attackCooldownSeconds = actor.recoverySeconds;
    actor.idleDecisionSeconds = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.attackImpactTriggered = false;
    GameplayActorSpellEffectState effectState = buildGameplayActorSpellEffectState(actor);
    GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService =
        m_pGameplayActorService != nullptr ? m_pGameplayActorService : &fallbackActorService;
    pActorService->clearSpellEffects(effectState, false);
    effectState.hostileToParty = false;
    effectState.hasDetectedParty = false;
    effectState.controlMode = friendlyToParty ? GameplayActorControlMode::Reanimated : GameplayActorControlMode::None;
    effectState.controlRemainingSeconds = friendlyToParty ? hoursToSeconds(24.0f) : 0.0f;
    applyGameplayActorSpellEffectState(effectState, actor);
    actor.hostilityType = friendlyToParty ? 0 : actor.hostilityType;
    actor.alertStatusBit = false;
    actor.hostileToParty = !friendlyToParty
        && m_pMonsterTable != nullptr
        && m_pGameplayActorService != nullptr
        && m_pMonsterTable->isHostileToParty(m_pGameplayActorService->relationMonsterId(actor.monsterId, actor.ally));
    actor.hasDetectedParty = false;
    return true;
}

bool OutdoorWorldRuntime::clearMapActorSpellEffects(size_t actorIndex)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    if (m_pGameplayActorService == nullptr)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];
    GameplayActorSpellEffectState effectState = buildGameplayActorSpellEffectState(actor);
    const bool baselineHostileToParty = actor.hostileToParty;
    m_pGameplayActorService->clearSpellEffects(effectState, baselineHostileToParty);
    applyGameplayActorSpellEffectState(effectState, actor);
    return true;
}

int OutdoorWorldRuntime::effectiveMapActorArmorClass(size_t actorIndex) const
{
    if (actorIndex >= m_mapActors.size())
    {
        return 0;
    }

    const MapActorState &actor = m_mapActors[actorIndex];
    const int baseArmorClass = actor.armorClass;

    if (m_pGameplayActorService == nullptr)
    {
        return std::max(0, baseArmorClass);
    }

    return m_pGameplayActorService->effectiveArmorClass(baseArmorClass, buildGameplayActorSpellEffectState(actor));
}

std::vector<size_t> OutdoorWorldRuntime::collectMapActorIndicesWithinRadius(
    float centerX,
    float centerY,
    float centerZ,
    float radius,
    bool requireLineOfSight,
    float sourceX,
    float sourceY,
    float sourceZ) const
{
    std::vector<size_t> result;

    if (radius <= 0.0f)
    {
        return result;
    }

    const bx::Vec3 source = {sourceX, sourceY, sourceZ};

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const MapActorState &actor = m_mapActors[actorIndex];

        if (isActorUnavailableForCombat(actor))
        {
            continue;
        }

        const float targetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
        const float deltaX = actor.preciseX - centerX;
        const float deltaY = actor.preciseY - centerY;
        const float deltaZ = targetZ - centerZ;
        const float edgeDistance =
            std::max(0.0f, length3d(deltaX, deltaY, deltaZ) - static_cast<float>(actor.radius));

        if (edgeDistance > radius)
        {
            continue;
        }

        if (requireLineOfSight)
        {
            const bx::Vec3 target = {actor.preciseX, actor.preciseY, targetZ};

            if (!hasClearOutdoorLineOfSight(source, target))
            {
                continue;
            }
        }

        result.push_back(actorIndex);
    }

    return result;
}

namespace
{
bool outdoorPointInsideViewCone(
    float viewX,
    float viewY,
    float viewZ,
    float viewYawRadians,
    float viewPitchRadians,
    float viewAspectRatio,
    float pointX,
    float pointY,
    float pointZ)
{
    const float cosPitch = std::cos(viewPitchRadians);
    const float sinPitch = std::sin(viewPitchRadians);
    const float cosYaw = std::cos(viewYawRadians);
    const float sinYaw = std::sin(viewYawRadians);
    const float forwardX = cosYaw * cosPitch;
    const float forwardY = sinYaw * cosPitch;
    const float forwardZ = sinPitch;
    const float rightX = -sinYaw;
    const float rightY = cosYaw;
    const float upX = -cosYaw * sinPitch;
    const float upY = -sinYaw * sinPitch;
    const float upZ = cosPitch;
    const float deltaX = pointX - viewX;
    const float deltaY = pointY - viewY;
    const float deltaZ = pointZ - viewZ;
    const float forwardDistance = deltaX * forwardX + deltaY * forwardY + deltaZ * forwardZ;

    if (forwardDistance <= 0.0f)
    {
        return false;
    }

    const float halfVerticalFovTan = std::tan(CameraVerticalFovRadians * 0.5f);
    const float halfHorizontalFovTan = halfVerticalFovTan * std::max(0.1f, viewAspectRatio);
    const float lateralDistance = std::abs(deltaX * rightX + deltaY * rightY);
    const float verticalDistance = std::abs(deltaX * upX + deltaY * upY + deltaZ * upZ);
    return lateralDistance <= forwardDistance * halfHorizontalFovTan
        && verticalDistance <= forwardDistance * halfVerticalFovTan;
}
}

std::vector<size_t> OutdoorWorldRuntime::collectVisibleMapActorIndicesWithinRadius(
    float centerX,
    float centerY,
    float centerZ,
    float radius,
    float sourceX,
    float sourceY,
    float sourceZ,
    float viewX,
    float viewY,
    float viewZ,
    float viewYawRadians,
    float viewPitchRadians,
    float viewAspectRatio) const
{
    std::vector<size_t> result;

    if (radius <= 0.0f)
    {
        return result;
    }

    const bx::Vec3 source = {sourceX, sourceY, sourceZ};

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const MapActorState &actor = m_mapActors[actorIndex];

        if (isActorUnavailableForCombat(actor))
        {
            continue;
        }

        const float targetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
        const float deltaX = actor.preciseX - centerX;
        const float deltaY = actor.preciseY - centerY;
        const float deltaZ = targetZ - centerZ;
        const float edgeDistance =
            std::max(0.0f, length3d(deltaX, deltaY, deltaZ) - static_cast<float>(actor.radius));

        if (edgeDistance > radius)
        {
            continue;
        }

        const float viewTargetZ = actor.preciseZ + std::max(48.0f, static_cast<float>(actor.height) * 0.6f);
        if (!outdoorPointInsideViewCone(
                viewX,
                viewY,
                viewZ,
                viewYawRadians,
                viewPitchRadians,
                viewAspectRatio,
                actor.preciseX,
                actor.preciseY,
                viewTargetZ))
        {
            continue;
        }

        const bx::Vec3 target = {actor.preciseX, actor.preciseY, targetZ};

        if (!hasClearOutdoorLineOfSight(source, target))
        {
            continue;
        }

        result.push_back(actorIndex);
    }

    return result;
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

OutdoorWorldRuntime::ChestViewState *OutdoorWorldRuntime::activeChestView()
{
    return m_activeChestView ? &*m_activeChestView : nullptr;
}

const OutdoorWorldRuntime::ChestViewState *OutdoorWorldRuntime::activeChestView() const
{
    if (!m_activeChestView)
    {
        return nullptr;
    }

    return &*m_activeChestView;
}

void OutdoorWorldRuntime::commitActiveChestView()
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

bool OutdoorWorldRuntime::takeActiveChestItem(size_t itemIndex, ChestItemState &item)
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


bool OutdoorWorldRuntime::takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, ChestItemState &item)
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

bool OutdoorWorldRuntime::tryPlaceActiveChestItemAt(const ChestItemState &item, uint8_t gridX, uint8_t gridY)
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

void OutdoorWorldRuntime::closeActiveChestView()
{
    m_activeChestView.reset();
}

OutdoorWorldRuntime::CorpseViewState *OutdoorWorldRuntime::activeCorpseView()
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

const OutdoorWorldRuntime::CorpseViewState *OutdoorWorldRuntime::activeCorpseView() const
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

void OutdoorWorldRuntime::commitActiveCorpseView()
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

bool OutdoorWorldRuntime::ensureMapActorCorpseView(size_t actorIndex)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    const MapActorState &actor = m_mapActors[actorIndex];

    if (!actor.isDead || actor.isInvisible || !actorShouldLeaveCorpse(m_pMonsterTable, actor))
    {
        return false;
    }

    if (actorIndex >= m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews.resize(actorIndex + 1);
    }

    if (m_mapActorCorpseViews[actorIndex].has_value())
    {
        return !m_mapActorCorpseViews[actorIndex]->items.empty();
    }

    if (!m_mapActorCorpseViews[actorIndex].has_value())
    {
        if (m_pMonsterTable == nullptr)
        {
            return false;
        }

        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats == nullptr)
        {
            return false;
        }

        std::vector<uint32_t> guaranteedItemIds;
        if (actor.specialItemId != 0)
        {
            guaranteedItemIds.push_back(actor.specialItemId);
        }

        if (m_eventRuntimeState)
        {
            const auto extraItemIterator =
                m_eventRuntimeState->actorExtraItemOverrides.find(static_cast<uint32_t>(actorIndex));

            if (extraItemIterator != m_eventRuntimeState->actorExtraItemOverrides.end())
            {
                guaranteedItemIds.insert(
                    guaranteedItemIds.end(),
                    extraItemIterator->second.begin(),
                    extraItemIterator->second.end());
            }
        }

        CorpseViewState corpse =
            buildMonsterCorpseView(
                actor.displayName,
                gameplayBolsterLootPrototype(pStats->loot, pStats->hitPoints, actor.bolsterRewardMultiplier),
                m_pItemTable,
                m_pParty,
                guaranteedItemIds);

        for (const GameplayChestItemState &item : corpse.items)
        {
            const uint32_t itemId = item.item.objectDescriptionId != 0 ? item.item.objectDescriptionId : item.itemId;

            if (!item.isGold && gameplayDebugTraceItemLooksQuestRelevant(itemId, m_pItemTable))
            {
                GAMEPLAY_DEBUG_TRACE(
                    "corpse_contains_quest_item scene_kind=outdoor map=\"" + mapName() + "\""
                    + " actor_index=" + std::to_string(actorIndex)
                    + " actor_id=" + std::to_string(actor.actorId)
                    + " monster_id=" + std::to_string(actor.monsterId)
                    + " name=\"" + actor.displayName + "\""
                    + " corpse_index=" + std::to_string(actorIndex)
                    + " item_id=" + std::to_string(itemId)
                    + gameplayDebugTraceItemSummary(itemId, m_pItemTable));
            }
        }

        if (corpse.items.empty())
        {
            corpse.fromSummonedMonster = false;
            corpse.sourceIndex = static_cast<uint32_t>(actorIndex);
            m_mapActorCorpseViews[actorIndex] = std::move(corpse);
            return false;
        }

        corpse.fromSummonedMonster = false;
        corpse.sourceIndex = static_cast<uint32_t>(actorIndex);
        m_mapActorCorpseViews[actorIndex] = std::move(corpse);
    }

    return m_mapActorCorpseViews[actorIndex].has_value();
}

bool OutdoorWorldRuntime::openMapActorCorpseView(size_t actorIndex)
{
    if (!ensureMapActorCorpseView(actorIndex))
    {
        return false;
    }

    m_activeCorpseView = *m_mapActorCorpseViews[actorIndex];
    return true;
}

std::optional<OutdoorWorldRuntime::ChestItemState> OutdoorWorldRuntime::mapActorCorpseItem(
    size_t actorIndex,
    size_t itemIndex) const
{
    if (actorIndex >= m_mapActorCorpseViews.size()
        || !m_mapActorCorpseViews[actorIndex].has_value()
        || itemIndex >= m_mapActorCorpseViews[actorIndex]->items.size())
    {
        return std::nullopt;
    }

    return m_mapActorCorpseViews[actorIndex]->items[itemIndex];
}

bool OutdoorWorldRuntime::takeMapActorCorpseItem(size_t actorIndex, size_t itemIndex, ChestItemState &item)
{
    if (actorIndex >= m_mapActorCorpseViews.size()
        || !m_mapActorCorpseViews[actorIndex].has_value()
        || itemIndex >= m_mapActorCorpseViews[actorIndex]->items.size())
    {
        return false;
    }

    CorpseViewState &corpseView = *m_mapActorCorpseViews[actorIndex];
    item = corpseView.items[itemIndex];
    corpseView.items.erase(corpseView.items.begin() + static_cast<ptrdiff_t>(itemIndex));

    if (m_activeCorpseView && m_activeCorpseView->sourceIndex == actorIndex)
    {
        m_activeCorpseView = corpseView;
    }

    if (!corpseView.items.empty())
    {
        return true;
    }

    if (m_activeCorpseView && m_activeCorpseView->sourceIndex == actorIndex)
    {
        m_activeCorpseView.reset();
    }

    return true;
}

bool OutdoorWorldRuntime::tryPlaceMapActorCorpseItemAt(size_t actorIndex, const ChestItemState &item, size_t itemIndex)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    if (actorIndex >= m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews.resize(actorIndex + 1);
    }

    if (!m_mapActorCorpseViews[actorIndex].has_value())
    {
        CorpseViewState corpseView = {};
        corpseView.fromSummonedMonster = false;
        corpseView.sourceIndex = static_cast<uint32_t>(actorIndex);
        corpseView.title = m_mapActors[actorIndex].displayName;
        m_mapActorCorpseViews[actorIndex] = std::move(corpseView);
    }

    CorpseViewState &corpseView = *m_mapActorCorpseViews[actorIndex];
    const size_t insertIndex = std::min(itemIndex, corpseView.items.size());
    corpseView.items.insert(corpseView.items.begin() + static_cast<ptrdiff_t>(insertIndex), item);

    if (actorIndex < m_mapActors.size())
    {
        m_mapActors[actorIndex].isInvisible = false;
    }

    if (m_activeCorpseView && m_activeCorpseView->sourceIndex == actorIndex)
    {
        m_activeCorpseView = corpseView;
    }

    return true;
}

std::vector<OutdoorWorldRuntime::ArpgModeCorpseLootItem> OutdoorWorldRuntime::collectArpgModeCorpseLootItems()
{
    std::vector<ArpgModeCorpseLootItem> items;

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        if (!ensureMapActorCorpseView(actorIndex))
        {
            continue;
        }

        if (actorIndex >= m_mapActorCorpseViews.size() || !m_mapActorCorpseViews[actorIndex].has_value())
        {
            continue;
        }

        const MapActorState &actor = m_mapActors[actorIndex];
        const CorpseViewState &corpseView = *m_mapActorCorpseViews[actorIndex];
        const float anchorZ = actor.preciseZ + std::max(48.0f, static_cast<float>(actor.height) * 0.45f);

        for (size_t itemIndex = 0; itemIndex < corpseView.items.size(); ++itemIndex)
        {
            items.push_back(
                ArpgModeCorpseLootItem{
                    .actorIndex = actorIndex,
                    .itemIndex = itemIndex,
                    .item = corpseView.items[itemIndex],
                    .x = actor.preciseX,
                    .y = actor.preciseY,
                    .z = anchorZ,
                });
        }
    }

    return items;
}

std::vector<OutdoorWorldRuntime::ArpgModeGoldPickup> OutdoorWorldRuntime::collectNearbyArpgModeCorpseGold(float radius)
{
    std::vector<ArpgModeGoldPickup> pickups;

    if (m_pParty == nullptr || radius <= 0.0f)
    {
        return pickups;
    }

    const float radiusSquared = radius * radius;

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        if (!ensureMapActorCorpseView(actorIndex)
            || actorIndex >= m_mapActorCorpseViews.size()
            || !m_mapActorCorpseViews[actorIndex].has_value())
        {
            continue;
        }

        const MapActorState &actor = m_mapActors[actorIndex];
        const float deltaX = partyX() - actor.preciseX;
        const float deltaY = partyY() - actor.preciseY;
        const float deltaZ = partyFootZ() - actor.preciseZ;

        if (deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ > radiusSquared)
        {
            continue;
        }

        size_t itemIndex = 0;

        while (actorIndex < m_mapActorCorpseViews.size()
            && m_mapActorCorpseViews[actorIndex].has_value()
            && itemIndex < m_mapActorCorpseViews[actorIndex]->items.size())
        {
            const ChestItemState &item = m_mapActorCorpseViews[actorIndex]->items[itemIndex];

            if (!item.isGold)
            {
                ++itemIndex;
                continue;
            }

            ChestItemState removedItem = {};

            if (!takeMapActorCorpseItem(actorIndex, itemIndex, removedItem))
            {
                break;
            }

            const uint32_t adjustedGold =
                m_eventRuntimeState
                    ? hiredNpcGoldAfterBonusAndFees(removedItem.goldAmount, *m_eventRuntimeState)
                    : removedItem.goldAmount;

            if (adjustedGold == 0)
            {
                continue;
            }

            m_pParty->addGold(static_cast<int>(adjustedGold));
            m_pParty->requestSound(SoundId::Gold);
            pickups.push_back(
                ArpgModeGoldPickup{
                    .amount = adjustedGold,
                    .x = actor.preciseX,
                    .y = actor.preciseY,
                    .z = actor.preciseZ + std::max(48.0f, static_cast<float>(actor.height) * 0.45f),
                });
            GAMEPLAY_DEBUG_TRACE(
                "gold_received destination=party source=arpg_corpse_proximity"
                " corpse_index=" + std::to_string(actorIndex)
                + " amount=" + std::to_string(adjustedGold));
        }
    }

    return pickups;
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
            m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
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
    if (m_pGameplayCombatController == nullptr)
    {
        static const std::vector<CombatEvent> EmptyEvents;
        return EmptyEvents;
    }

    return m_pGameplayCombatController->pendingCombatEvents();
}

void OutdoorWorldRuntime::clearPendingCombatEvents()
{
    if (m_pGameplayCombatController != nullptr)
    {
        m_pGameplayCombatController->clearPendingCombatEvents();
    }
}

size_t OutdoorWorldRuntime::worldItemCount() const
{
    return m_worldItems.size();
}

const OutdoorWorldRuntime::WorldItemState *OutdoorWorldRuntime::worldItemState(size_t worldItemIndex) const
{
    if (worldItemIndex >= m_worldItems.size())
    {
        return nullptr;
    }

    return &m_worldItems[worldItemIndex];
}

OutdoorWorldRuntime::WorldItemState *OutdoorWorldRuntime::worldItemStateMutable(size_t worldItemIndex)
{
    if (worldItemIndex >= m_worldItems.size())
    {
        return nullptr;
    }

    return &m_worldItems[worldItemIndex];
}

bool OutdoorWorldRuntime::takeWorldItem(size_t worldItemIndex, WorldItemState &item)
{
    if (worldItemIndex >= m_worldItems.size())
    {
        return false;
    }

    item = m_worldItems[worldItemIndex];
    m_worldItems.erase(m_worldItems.begin() + static_cast<std::ptrdiff_t>(worldItemIndex));
    return true;
}

bool OutdoorWorldRuntime::worldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state) const
{
    const WorldItemState *pWorldItem = worldItemState(worldItemIndex);

    if (pWorldItem == nullptr)
    {
        return false;
    }

    state = {};
    state.item = pWorldItem->item;
    state.goldAmount = pWorldItem->goldAmount;
    state.isGold = pWorldItem->isGold;
    return true;
}

bool OutdoorWorldRuntime::updateWorldItemInspectState(size_t worldItemIndex, const InventoryItem &item)
{
    WorldItemState *pWorldItem = worldItemStateMutable(worldItemIndex);

    if (pWorldItem == nullptr || pWorldItem->isGold)
    {
        return false;
    }

    pWorldItem->item = item;
    return true;
}

bool OutdoorWorldRuntime::takeWorldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state)
{
    const WorldItemState *pWorldItem = worldItemState(worldItemIndex);

    if (pWorldItem == nullptr)
    {
        return false;
    }

    state = {};
    state.item = pWorldItem->item;
    state.goldAmount = pWorldItem->goldAmount;
    state.isGold = pWorldItem->isGold;

    WorldItemState removedItem = {};
    return takeWorldItem(worldItemIndex, removedItem);
}

size_t OutdoorWorldRuntime::projectileCount() const
{
    return projectileService().projectileCount();
}

const OutdoorWorldRuntime::ProjectileState *OutdoorWorldRuntime::projectileState(size_t projectileIndex) const
{
    return projectileService().projectileState(projectileIndex);
}

size_t OutdoorWorldRuntime::projectileImpactCount() const
{
    return projectileService().projectileImpactCount();
}

const OutdoorWorldRuntime::ProjectileImpactState *OutdoorWorldRuntime::projectileImpactState(size_t effectIndex) const
{
    return projectileService().projectileImpactState(effectIndex);
}

size_t OutdoorWorldRuntime::fireSpikeTrapCount() const
{
    return m_fireSpikeTraps.size();
}

const OutdoorWorldRuntime::FireSpikeTrapState *OutdoorWorldRuntime::fireSpikeTrapState(size_t trapIndex) const
{
    if (trapIndex >= m_fireSpikeTraps.size())
    {
        return nullptr;
    }

    return &m_fireSpikeTraps[trapIndex];
}

size_t OutdoorWorldRuntime::bloodSplatCount() const
{
    return m_bloodSplats.size();
}

const OutdoorWorldRuntime::BloodSplatState *OutdoorWorldRuntime::bloodSplatState(size_t splatIndex) const
{
    if (splatIndex >= m_bloodSplats.size())
    {
        return nullptr;
    }

    return &m_bloodSplats[splatIndex];
}

uint64_t OutdoorWorldRuntime::bloodSplatRevision() const
{
    return m_bloodSplatRevision;
}

void OutdoorWorldRuntime::addBloodSplat(uint32_t sourceActorId, float x, float y, float z, float radius)
{
    if (radius <= 0.0f)
    {
        return;
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
        return;
    }

    if (m_bloodSplats.size() >= MaxOutdoorBloodSplats)
    {
        m_bloodSplats.erase(m_bloodSplats.begin());
    }

    m_bloodSplats.push_back(splat);
    ++m_bloodSplatRevision;
}

void OutdoorWorldRuntime::spawnBloodSplatForActorIfNeeded(size_t actorIndex)
{
    if (actorIndex >= m_mapActors.size() || m_pMonsterTable == nullptr)
    {
        return;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (actor.bloodSplatSpawned)
    {
        return;
    }

    if (!actorShouldLeaveCorpse(m_pMonsterTable, actor))
    {
        return;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr || !pStats->bloodSplatOnDeath)
    {
        return;
    }

    const float terrainZ =
        m_pOutdoorMapData != nullptr
            ? sampleOutdoorRenderedTerrainHeight(*m_pOutdoorMapData, actor.preciseX, actor.preciseY)
            : actor.preciseZ;
    const float supportZ = sampleSupportFloorHeight(
        actor.preciseX,
        actor.preciseY,
        actor.preciseZ + 256.0f,
        512.0f,
        24.0f);
    const float splatZ = std::max(terrainZ, supportZ);
    const float splatRadius = std::max(32.0f, static_cast<float>(actor.radius) * 1.5f);
    addBloodSplat(actor.actorId, actor.preciseX, actor.preciseY, splatZ, splatRadius);
    actor.bloodSplatSpawned = true;
}

void OutdoorWorldRuntime::bakeBloodSplatGeometry(BloodSplatState &splat) const
{
    splat.vertices.clear();

    if (splat.radius <= 0.0f)
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
        [this, &splat, surfaceHeightTolerance](float x, float y, bx::Vec3 &point) -> bool
        {
            const float terrainZ =
                m_pOutdoorMapData != nullptr
                    ? sampleOutdoorRenderedTerrainHeight(*m_pOutdoorMapData, x, y)
                    : splat.z;
            const float supportZ = sampleSupportFloorHeight(
                x,
                y,
                splat.z + 256.0f,
                512.0f,
                24.0f);
            const float z = std::max(terrainZ, supportZ);

            if (std::abs(z - splat.z) > surfaceHeightTolerance)
            {
                return false;
            }

            point = {x, y, z + BloodSplatHeightOffset + 1.0f};
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
            const float centerU = (u0 + u1) * 0.5f;
            const float centerV = (v0 + v1) * 0.5f;
            bx::Vec3 center = {0.0f, 0.0f, 0.0f};

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

void OutdoorWorldRuntime::removeBloodSplat(uint32_t sourceActorId)
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

GameplayProjectileService &OutdoorWorldRuntime::projectileService()
{
    if (m_pGameplayProjectileService == nullptr)
    {
        return m_fallbackGameplayProjectileService;
    }

    return *m_pGameplayProjectileService;
}

const GameplayProjectileService &OutdoorWorldRuntime::projectileService() const
{
    if (m_pGameplayProjectileService == nullptr)
    {
        return m_fallbackGameplayProjectileService;
    }

    return *m_pGameplayProjectileService;
}

GameplayProjectileService::ProjectileImpactSpawnResult
OutdoorWorldRuntime::spawnProjectileImpactVisual(
    const ProjectileState &projectile,
    const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z,
    bool centerVertically)
{
    if (m_pGameplayFxService != nullptr)
    {
        return m_pGameplayFxService->spawnProjectileImpactVisual(
            projectile,
            definition,
            x,
            y,
            z,
            centerVertically);
    }

    return projectileService().spawnProjectileImpactVisual(projectile, definition, x, y, z, centerVertically);
}

GameplayProjectileService::ProjectileImpactSpawnResult
OutdoorWorldRuntime::spawnWaterSplashImpactVisual(
    const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z)
{
    if (m_pGameplayFxService != nullptr)
    {
        return m_pGameplayFxService->spawnWaterSplashImpactVisual(definition, x, y, z);
    }

    return projectileService().spawnWaterSplashImpactVisual(definition, x, y, z);
}

GameplayProjectileService::ProjectileImpactSpawnResult
OutdoorWorldRuntime::spawnImmediateSpellImpactVisual(
    const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
    int sourceSpellId,
    const std::string &sourceObjectName,
    const std::string &sourceObjectSpriteName,
    float x,
    float y,
    float z,
    bool centerVertically,
    bool freezeAnimation)
{
    if (m_pGameplayFxService != nullptr)
    {
        return m_pGameplayFxService->spawnImmediateSpellImpactVisual(
            definition,
            sourceSpellId,
            sourceObjectName,
            sourceObjectSpriteName,
            x,
            y,
            z,
            centerVertically,
            freezeAnimation);
    }

    return projectileService().spawnImmediateSpellImpactVisual(
        definition,
        sourceSpellId,
        sourceObjectName,
        sourceObjectSpriteName,
        x,
        y,
        z,
        centerVertically,
        freezeAnimation);
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
        static_cast<float>(x),
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

bool OutdoorWorldRuntime::summonEventItem(
    uint32_t itemId,
    int32_t x,
    int32_t y,
    int32_t z,
    int32_t speed,
    uint32_t count,
    bool randomRotate
)
{
    if (m_pObjectTable == nullptr || itemId == 0 || count == 0)
    {
        return false;
    }

    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint32_t lifetimeTicks = 0;
    std::string objectName;
    std::string objectSpriteName;
    const ItemDefinition *pItemDefinition = nullptr;
    bool payloadResolved = false;

    const std::optional<uint16_t> descriptionId =
        m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(itemId));

    if (descriptionId)
    {
        const ObjectEntry *pObjectEntry = m_pObjectTable->get(*descriptionId);

        if (pObjectEntry != nullptr && (pObjectEntry->flags & ObjectDescNoSprite) == 0 && pObjectEntry->spriteId != 0)
        {
            objectDescriptionId = *descriptionId;
            objectSpriteId = pObjectEntry->spriteId;
            objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
                m_pProjectileSpriteFrameTable,
                pObjectEntry->spriteId,
                pObjectEntry->spriteName);
            objectFlags = pObjectEntry->flags;
            radius = static_cast<uint16_t>(std::max<int16_t>(0, pObjectEntry->radius));
            height = static_cast<uint16_t>(std::max<int16_t>(0, pObjectEntry->height));
            lifetimeTicks = pObjectEntry->lifetimeTicks > 0 ? pObjectEntry->lifetimeTicks : 0;
            objectName = pObjectEntry->internalName;
            objectSpriteName = pObjectEntry->spriteName;
            payloadResolved = true;

            if (m_pItemTable != nullptr)
            {
                pItemDefinition = m_pItemTable->findBySpriteIndex(static_cast<uint16_t>(itemId));
            }
        }
    }

    if (!payloadResolved && m_pItemTable != nullptr)
    {
        pItemDefinition = m_pItemTable->get(itemId);

        if (pItemDefinition != nullptr)
        {
            if (resolveWorldItemVisual(
                    itemId,
                    objectDescriptionId,
                    objectSpriteId,
                    objectSpriteFrameIndex,
                    objectFlags,
                    radius,
                    height,
                    objectName,
                    objectSpriteName))
            {
                payloadResolved = true;
            }
            else
            {
                pItemDefinition = nullptr;
            }
        }
    }

    if (!payloadResolved)
    {
        std::cout << "Event summon unresolved payload=" << itemId << '\n';
        return false;
    }

    if (lifetimeTicks == 0)
    {
        const ObjectEntry *pObjectEntry = m_pObjectTable->get(objectDescriptionId);

        if (pObjectEntry != nullptr)
        {
            lifetimeTicks = pObjectEntry->lifetimeTicks > 0 ? pObjectEntry->lifetimeTicks : 0;
        }
    }

    bool spawnedAny = false;
    const float baseX = static_cast<float>(x);
    const float baseY = static_cast<float>(y);
    const float baseZ = static_cast<float>(z);

    for (uint32_t itemIndex = 0; itemIndex < count; ++itemIndex)
    {
        WorldItemState worldItem = {};
        worldItem.worldItemId = m_nextWorldItemId++;
        worldItem.objectDescriptionId = objectDescriptionId;
        worldItem.objectSpriteId = objectSpriteId;
        worldItem.objectSpriteFrameIndex = objectSpriteFrameIndex;
        worldItem.objectFlags = objectFlags;
        worldItem.radius = radius;
        worldItem.height = height;
        worldItem.objectName = objectName;
        worldItem.objectSpriteName = objectSpriteName;
        worldItem.attributes = SpriteAttrTemporary;
        worldItem.x = baseX;
        worldItem.y = baseY;
        worldItem.z = baseZ;
        worldItem.initialX = baseX;
        worldItem.initialY = baseY;
        worldItem.initialZ = baseZ;
        worldItem.lifetimeTicks = lifetimeTicks;

        if (pItemDefinition != nullptr)
        {
            worldItem.item.objectDescriptionId = pItemDefinition->itemId;
            worldItem.item.quantity = 1;
            worldItem.item.width = pItemDefinition->inventoryWidth;
            worldItem.item.height = pItemDefinition->inventoryHeight;
            worldItem.goldAmount = isGoldHeapItemId(worldItem.item.objectDescriptionId) ? 1u : 0u;
            worldItem.isGold = worldItem.goldAmount > 0 && isGoldHeapItemId(worldItem.item.objectDescriptionId);
        }

        if (speed > 0)
        {
            const float angleRadians = randomRotate
                ? (Pi * 2.0f * static_cast<float>((itemId + itemIndex * 37u) % 2048u) / 2048.0f)
                : 0.0f;
            worldItem.velocityX = std::cos(angleRadians) * speed;
            worldItem.velocityY = std::sin(angleRadians) * speed;
            worldItem.velocityZ = 0.0f;
        }

        m_worldItems.push_back(std::move(worldItem));
        spawnedAny = true;
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::summonFriendlyMonsterById(
    int16_t monsterId,
    uint32_t count,
    float durationSeconds,
    float x,
    float y,
    float z)
{
    if (m_pMonsterTable == nullptr || count == 0)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    bool spawnedAny = false;

    for (uint32_t summonIndex = 0; summonIndex < count; ++summonIndex)
    {
        const MonsterEntry *pMonsterEntry = resolveMonsterEntry(*m_pMonsterTable, monsterId, pStats);
        const uint16_t actorRadius = pMonsterEntry != nullptr ? std::max<uint16_t>(pMonsterEntry->radius, 32) : 32;
        const bx::Vec3 spawnPosition = calculateEncounterSpawnPosition(
            x,
            y,
            z,
            128,
            actorRadius,
            summonIndex);
        MapActorState actor = buildSpawnedMapActorState(
            *m_pMonsterTable,
            m_pSpellTable,
            m_pOutdoorMapData,
            *pStats,
            GameplayBolsterRuntimeContext{
                .pMap = &m_map,
                .pMonsterTable = m_pMonsterTable,
                .pBolsterMapTable = m_pMergedBolsterMapTable,
                .pBolsterMonsterTable = m_pMergedBolsterMonsterTable,
                .pParty = m_pParty,
                .bolsterMonstersEnabled = m_bolsterMonstersEnabled,
            },
            m_nextActorId++,
            0,
            false,
            static_cast<size_t>(-1),
            0,
            0,
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

        actor.controlMode = ActorControlMode::Enslaved;
        actor.controlRemainingSeconds = std::max(durationSeconds, 1.0f);
        actor.hostileToParty = false;
        actor.hasDetectedParty = false;
        applyOeOutdoorActorFloorCorrection(actor, *pStats);
        m_mapActors.push_back(std::move(actor));
        spawnedAny = true;
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::summonHostileMonsterById(
    int16_t monsterId,
    uint32_t count,
    float x,
    float y,
    float z,
    uint32_t group)
{
    if (m_pMonsterTable == nullptr || count == 0)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    bool spawnedAny = false;

    for (uint32_t summonIndex = 0; summonIndex < count; ++summonIndex)
    {
        const MonsterEntry *pMonsterEntry = resolveMonsterEntry(*m_pMonsterTable, monsterId, pStats);
        const uint16_t actorRadius = pMonsterEntry != nullptr ? std::max<uint16_t>(pMonsterEntry->radius, 32) : 32;
        const bx::Vec3 spawnPosition =
            calculateEncounterSpawnPosition(x, y, z, 128, actorRadius, summonIndex);
        MapActorState actor = buildSpawnedMapActorState(
            *m_pMonsterTable,
            m_pSpellTable,
            m_pOutdoorMapData,
            *pStats,
            GameplayBolsterRuntimeContext{
                .pMap = &m_map,
                .pMonsterTable = m_pMonsterTable,
                .pBolsterMapTable = m_pMergedBolsterMapTable,
                .pBolsterMonsterTable = m_pMergedBolsterMonsterTable,
                .pParty = m_pParty,
                .bolsterMonstersEnabled = m_bolsterMonstersEnabled,
            },
            m_nextActorId++,
            0,
            false,
            static_cast<size_t>(-1),
            group,
            0,
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

        actor.hostileToParty = true;
        actor.hasDetectedParty = true;
        actor.hostilityType = std::max<uint8_t>(actor.hostilityType, 4);
        applyOeOutdoorActorFloorCorrection(actor, *pStats);
        m_mapActors.push_back(std::move(actor));
        spawnedAny = true;
    }

    if (spawnedAny)
    {
        applyEventRuntimeState(true);
    }

    return spawnedAny;
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
    const bool currentAlertStatus =
        m_pOutdoorMapDeltaData != nullptr && m_pOutdoorMapDeltaData->locationInfo.alertStatus != 0;

    auto countMonster =
        [&](bool matches, bool isDefeated)
        {
            if (!matches)
            {
                return;
            }

            ++totalActors;

            if (isDefeated)
            {
                ++defeatedActors;
            }
        };

    (void)invisibleAsDead;

    for (const MapActorState &actor : m_mapActors)
    {
        if (actor.alertStatusBit != currentAlertStatus)
        {
            continue;
        }

        bool matches = false;

        switch (checkType)
        {
            case static_cast<uint32_t>(EvtActorKillCheck::Any):
                matches = true;
                break;

            case static_cast<uint32_t>(EvtActorKillCheck::Group):
                matches = actor.group == id;
                break;

            case static_cast<uint32_t>(EvtActorKillCheck::MonsterId):
                matches = actor.monsterId == legacyEventMonsterIdToStatsId(id);
                break;

            case static_cast<uint32_t>(EvtActorKillCheck::ActorIdOe):
                matches = actor.actorId == id;
                break;

            case static_cast<uint32_t>(EvtActorKillCheck::UniqueNameId):
                matches = actor.uniqueNameId == id;
                break;

            default:
                break;
        }

        countMonster(matches, actor.isDead || actor.currentHp <= 0 || actor.isInvisible);
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

Party *OutdoorWorldRuntime::party()
{
    return m_pParty;
}

const Party *OutdoorWorldRuntime::party() const
{
    return m_pParty;
}

float OutdoorWorldRuntime::partyX() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyX() : 0.0f;
}

float OutdoorWorldRuntime::partyY() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyY() : 0.0f;
}

float OutdoorWorldRuntime::partyFootZ() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyFootZ() : 0.0f;
}

float OutdoorWorldRuntime::gameplayCameraYawRadians() const
{
    return m_pInteractionView != nullptr ? m_pInteractionView->cameraYawRadians() : 0.0f;
}

float OutdoorWorldRuntime::gameplayCameraPitchRadians() const
{
    return m_pInteractionView != nullptr ? m_pInteractionView->cameraPitchRadians() : 0.0f;
}

bool OutdoorWorldRuntime::partyIsAirborneForRest() const
{
    return m_pPartyRuntime != nullptr
        && (m_pPartyRuntime->movementState().airborne || m_pPartyRuntime->partyMovementState().flying);
}

bool OutdoorWorldRuntime::partyIsFlyingForEventChecks() const
{
    return m_pPartyRuntime != nullptr
        && m_pPartyRuntime->movementState().airborne
        && m_pPartyRuntime->partyMovementState().flying;
}

bool OutdoorWorldRuntime::partyIsActivelyFlyingForHud() const
{
    return m_pPartyRuntime != nullptr && m_pPartyRuntime->partyMovementState().activelyFlying;
}

void OutdoorWorldRuntime::syncSpellMovementStatesFromPartyBuffs()
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->syncSpellMovementStatesFromPartyBuffs();
    }
}

void OutdoorWorldRuntime::requestPartyJump(float verticalVelocity, float lift)
{
    if (m_pPartyRuntime != nullptr)
    {
        const std::optional<float> velocityOverride =
            verticalVelocity > 0.0f ? std::optional<float>(verticalVelocity) : std::nullopt;
        m_pPartyRuntime->requestJump(velocityOverride, lift);
    }
}

bool OutdoorWorldRuntime::specialJump(uint32_t encodedHorizontalVelocity, uint32_t verticalVelocity)
{
    if (m_pPartyRuntime == nullptr)
    {
        return false;
    }

    const float horizontalSpeed = static_cast<float>(encodedHorizontalVelocity >> 16);
    const float angleRadians =
        static_cast<float>(encodedHorizontalVelocity & 0xffffu) * (Pi * 2.0f / SpecialJumpAngleUnitsPerTurn);
    const float verticalScale = std::sqrt(OutdoorMovementGravity / LegacyOutdoorSpecialJumpGravity);

    m_pPartyRuntime->requestSpecialJump(
        std::cos(angleRadians) * horizontalSpeed,
        std::sin(angleRadians) * horizontalSpeed,
        static_cast<float>(verticalVelocity) * verticalScale);
    return true;
}

void OutdoorWorldRuntime::setAlwaysRunEnabled(bool enabled)
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->setRunning(enabled);
    }
}

void OutdoorWorldRuntime::cancelPendingMapTransition()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::cancelPendingMapTransition(*m_pInteractionView);
        return;
    }

    if (m_pOutdoorMapData == nullptr || m_pPartyRuntime == nullptr)
    {
        return;
    }

    const MapBounds &bounds = m_map.outdoorBounds;

    if (!bounds.enabled)
    {
        return;
    }

    constexpr float CancelClampInset = 1.0f;
    const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();
    const float clampedX = std::clamp(
        moveState.x,
        static_cast<float>(bounds.minX) + CancelClampInset,
        static_cast<float>(bounds.maxX) - CancelClampInset);
    const float clampedY = std::clamp(
        moveState.y,
        static_cast<float>(bounds.minY) + CancelClampInset,
        static_cast<float>(bounds.maxY) - CancelClampInset);

    if (clampedX == moveState.x && clampedY == moveState.y)
    {
        return;
    }

    m_pPartyRuntime->teleportTo(clampedX, clampedY, moveState.footZ);
}

bool OutdoorWorldRuntime::executeNpcTopicEvent(
    uint16_t eventId,
    size_t &previousMessageCount,
    std::optional<uint8_t> continueStep)
{
    return m_pInteractionView != nullptr
        && OutdoorInteractionController::executeNpcTopicEvent(
            *m_pInteractionView,
            eventId,
            previousMessageCount,
            continueStep);
}

bool OutdoorWorldRuntime::executeMapEvent(
    uint16_t eventId,
    size_t &previousMessageCount,
    std::optional<uint8_t> continueStep)
{
    return m_pInteractionView != nullptr
        && OutdoorInteractionController::executeMapEvent(
            *m_pInteractionView,
            eventId,
            previousMessageCount,
            continueStep);
}

bool OutdoorWorldRuntime::executeEventHooks(EventRuntimeHookKind kind)
{
    return m_pInteractionView != nullptr
        && m_pInteractionView->executeEventHooks(kind);
}

const MapDeltaData *OutdoorWorldRuntime::mapDeltaData() const
{
    return m_pOutdoorMapDeltaData;
}

MapDeltaData *OutdoorWorldRuntime::mapDeltaData()
{
    return m_pOutdoorMapDeltaData;
}

bool OutdoorWorldRuntime::setFacetBit(uint32_t cogNumber, uint32_t bit, bool isOn)
{
    if (cogNumber == 0 || m_pOutdoorMapData == nullptr || m_pOutdoorMapDeltaData == nullptr)
    {
        return false;
    }

    size_t totalFaceCount = 0;

    for (const OutdoorBModel &bmodel : m_pOutdoorMapData->bmodels)
    {
        totalFaceCount += bmodel.faces.size();
    }

    while (m_pOutdoorMapDeltaData->faceAttributes.size() < totalFaceCount)
    {
        size_t remainingFaceIndex = m_pOutdoorMapDeltaData->faceAttributes.size();

        for (const OutdoorBModel &bmodel : m_pOutdoorMapData->bmodels)
        {
            if (remainingFaceIndex < bmodel.faces.size())
            {
                m_pOutdoorMapDeltaData->faceAttributes.push_back(bmodel.faces[remainingFaceIndex].attributes);
                break;
            }

            remainingFaceIndex -= bmodel.faces.size();
        }
    }

    bool matchedAny = false;
    bool changedAny = false;
    size_t flattenedFaceIndex = 0;

    for (size_t bModelIndex = 0; bModelIndex < m_pOutdoorMapData->bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bmodel = m_pOutdoorMapData->bmodels[bModelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            const OutdoorBModelFace &face = bmodel.faces[faceIndex];

            if (face.cogNumber == cogNumber && flattenedFaceIndex < m_pOutdoorMapDeltaData->faceAttributes.size())
            {
                matchedAny = true;
                uint32_t &attributes = m_pOutdoorMapDeltaData->faceAttributes[flattenedFaceIndex];
                const uint32_t oldAttributes = attributes;

                if (isOn)
                {
                    attributes |= bit;
                }
                else
                {
                    attributes &= ~bit;
                }

                changedAny = changedAny || attributes != oldAttributes;
                setOutdoorFaceGeometryAttributes(bModelIndex, faceIndex, attributes);
            }

            ++flattenedFaceIndex;
        }
    }

    if (changedAny)
    {
        ++m_pOutdoorMapDeltaData->surfaceRevision;
    }

    return matchedAny;
}

bool OutdoorWorldRuntime::registerOutdoorModelMechanism(
    uint32_t mechanismId,
    const std::string &modelName,
    int32_t dx,
    int32_t dy,
    int32_t dz,
    uint32_t moveTimeMs,
    bool closed,
    bool moveParty)
{
    if (mechanismId == 0 || modelName.empty() || m_pOutdoorMapData == nullptr || !m_eventRuntimeState)
    {
        return false;
    }

    const std::string normalizedModelName = toLowerCopy(modelName);
    size_t matchedBModelIndex = static_cast<size_t>(-1);
    const uint32_t clickableBit = faceAttributeBit(FaceAttribute::Clickable);
    const uint32_t hintBit = faceAttributeBit(FaceAttribute::HasHint);

    for (size_t bModelIndex = 0; bModelIndex < m_pOutdoorMapData->bmodels.size(); ++bModelIndex)
    {
        OutdoorBModel &bmodel = m_pOutdoorMapData->bmodels[bModelIndex];

        if (toLowerCopy(bmodel.name) != normalizedModelName)
        {
            continue;
        }

        matchedBModelIndex = bModelIndex;

        for (OutdoorBModelFace &face : bmodel.faces)
        {
            face.cogTriggeredNumber = static_cast<uint16_t>(std::min<uint32_t>(mechanismId, UINT16_MAX));
            face.attributes |= clickableBit;
            face.attributes &= ~hintBit;
        }

        break;
    }

    if (matchedBModelIndex == static_cast<size_t>(-1))
    {
        return false;
    }

    if (m_pOutdoorMapDeltaData != nullptr)
    {
        size_t totalFaceCount = 0;

        for (const OutdoorBModel &bmodel : m_pOutdoorMapData->bmodels)
        {
            totalFaceCount += bmodel.faces.size();
        }

        while (m_pOutdoorMapDeltaData->faceAttributes.size() < totalFaceCount)
        {
            size_t remainingFaceIndex = m_pOutdoorMapDeltaData->faceAttributes.size();

            for (const OutdoorBModel &bmodel : m_pOutdoorMapData->bmodels)
            {
                if (remainingFaceIndex < bmodel.faces.size())
                {
                    m_pOutdoorMapDeltaData->faceAttributes.push_back(bmodel.faces[remainingFaceIndex].attributes);
                    break;
                }

                remainingFaceIndex -= bmodel.faces.size();
            }
        }

        bool changedAny = false;
        size_t flattenedFaceIndex = 0;

        for (size_t bModelIndex = 0; bModelIndex < m_pOutdoorMapData->bmodels.size(); ++bModelIndex)
        {
            const OutdoorBModel &bmodel = m_pOutdoorMapData->bmodels[bModelIndex];

            for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
            {
                if (bModelIndex == matchedBModelIndex
                    && flattenedFaceIndex < m_pOutdoorMapDeltaData->faceAttributes.size())
                {
                    const uint32_t attributes = bmodel.faces[faceIndex].attributes;
                    uint32_t &deltaAttributes = m_pOutdoorMapDeltaData->faceAttributes[flattenedFaceIndex];
                    changedAny = changedAny || deltaAttributes != attributes;
                    deltaAttributes = attributes;
                }

                ++flattenedFaceIndex;
            }
        }

        if (changedAny)
        {
            ++m_pOutdoorMapDeltaData->surfaceRevision;
        }
    }

    EventRuntimeState::OutdoorModelMechanismDefinition definition = {};
    definition.mechanismId = mechanismId;
    definition.modelName = modelName;
    definition.bmodelIndex = matchedBModelIndex;
    definition.dx = dx;
    definition.dy = dy;
    definition.dz = dz;
    definition.moveTimeMs = std::max<uint32_t>(1, moveTimeMs);
    definition.closed = closed;
    definition.moveParty = moveParty;
    m_eventRuntimeState->outdoorModelMechanisms[mechanismId] = definition;

    if (m_eventRuntimeState->mechanisms.find(mechanismId) == m_eventRuntimeState->mechanisms.end())
    {
        RuntimeMechanismState mechanism = {};
        mechanism.state = closed
            ? static_cast<uint16_t>(EvtMechanismState::Closed)
            : static_cast<uint16_t>(EvtMechanismState::Open);
        mechanism.currentDistance = closed ? 0.0f : 1.0f;
        mechanism.isMoving = false;
        m_eventRuntimeState->mechanisms[mechanismId] = mechanism;
    }

    ++m_eventRuntimeState->outdoorSurfaceRevision;
    rebuildOutdoorFaceGeometryCache();
    syncOutdoorFaceGeometryAttributesFromMapDelta();
    refreshOutdoorModelMechanismGeometry();
    m_outdoorMechanismGeometryRefreshAccumulatorSeconds = 0.0f;

    return true;
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
    if (m_pParty != nullptr
        && tryApplyEventSpellBuffs(*m_pParty, spellId, skillLevel, skillMastery))
    {
        if (m_eventRuntimeState)
        {
            EventRuntimeState::SpellFxRequest request = {};
            request.spellId = spellId;
            request.memberIndices = buildAllPartyMemberIndices(*m_pParty);
            m_eventRuntimeState->spellFxRequests.push_back(std::move(request));
        }

        return true;
    }

    SpellCastRequest request = {};
    request.sourceKind = RuntimeSpellSourceKind::Event;
    request.sourceId = EventSpellSourceId;
    request.ability = MonsterAttackAbility::Spell1;
    request.spellId = spellId;
    request.skillLevel = skillLevel;
    request.skillMastery = static_cast<uint32_t>(normalizeEventSkillMastery(skillMastery));
    request.sourceX = static_cast<float>(fromX);
    request.sourceY = static_cast<float>(fromY);
    request.sourceZ = static_cast<float>(fromZ);

    if (toX == 0 && toY == 0 && toZ == 0 && m_pPartyRuntime != nullptr)
    {
        request.targetX = partyX();
        request.targetY = partyY();
        request.targetZ = partyFootZ() + PartyTargetHeightOffset;
    }
    else
    {
        request.targetX = static_cast<float>(toX);
        request.targetY = static_cast<float>(toY);
        request.targetZ = static_cast<float>(toZ);
    }

    return castSpell(request);
}

bool OutdoorWorldRuntime::castPartySpell(const SpellCastRequest &request)
{
    if (request.sourceKind != RuntimeSpellSourceKind::Party)
    {
        return false;
    }

    return castSpell(request);
}

bool OutdoorWorldRuntime::castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request)
{
    SpellCastRequest worldRequest = {};
    worldRequest.sourceKind = RuntimeSpellSourceKind::Party;
    worldRequest.sourceId = request.casterMemberIndex + 1;
    worldRequest.sourcePartyMemberIndex = request.casterMemberIndex;
    worldRequest.ability = MonsterAttackAbility::Spell1;
    worldRequest.spellId = request.spellId;
    worldRequest.skillLevel = request.skillLevel;
    worldRequest.skillMastery = static_cast<uint32_t>(request.skillMastery);
    worldRequest.damage = request.damage;
    worldRequest.attackBonus = 0;
    worldRequest.useActorHitChance = false;
    worldRequest.sourceX = request.sourceX;
    worldRequest.sourceY = request.sourceY;
    worldRequest.sourceZ = request.sourceZ;
    worldRequest.targetX = request.targetX;
    worldRequest.targetY = request.targetY;
    worldRequest.targetZ = request.targetZ;
    worldRequest.effectSoundIdOverride = request.effectSoundIdOverride;
    worldRequest.impactSoundIdOverride = request.impactSoundIdOverride;
    worldRequest.turnBasedPendingAction = request.turnBasedPendingAction;
    return castPartySpell(worldRequest);
}

bool OutdoorWorldRuntime::spawnPartyProjectile(const PartyProjectileRequest &request)
{
    ResolvedProjectileDefinition definition = {};

    if (!resolveObjectProjectileDefinition(
            static_cast<int>(request.objectId),
            static_cast<int>(request.impactObjectId),
            definition))
    {
        return false;
    }

    const uint16_t objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    GameplayProjectileService::ProjectileSpawnRequest spawnRequest = {};
    spawnRequest.sourceKind = ProjectileState::SourceKind::Party;
    spawnRequest.sourceId = request.sourcePartyMemberIndex + 1;
    spawnRequest.sourcePartyMemberIndex = request.sourcePartyMemberIndex;
    spawnRequest.definition = buildGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    spawnRequest.damage = request.damage;
    spawnRequest.attackBonus = request.attackBonus;
    spawnRequest.useActorHitChance = request.useActorHitChance;
    spawnRequest.damageType = request.damageType;
    spawnRequest.turnBasedPendingAction = request.turnBasedPendingAction;
    spawnRequest.sourceX = request.sourceX;
    spawnRequest.sourceY = request.sourceY;
    spawnRequest.sourceZ = request.sourceZ;
    spawnRequest.targetX = request.targetX;
    spawnRequest.targetY = request.targetY;
    spawnRequest.targetZ = request.targetZ;
    spawnRequest.spawnForwardOffset = 0.0f;
    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        projectileService().spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        projectileService().buildProjectileSpawnEffects(spawnResult, false);

    if (blasterProjectileTraceEnabled() && projectileLooksLikeBlasterTraceTarget(spawnResult.projectile))
    {
        std::ostringstream out;
        out
            << "blaster_projectile_spawn scene=outdoor"
            << " source=party_attack"
            << " member=" << request.sourcePartyMemberIndex
            << " accepted=" << (spawnEffects.accepted ? 1 : 0)
            << " projectileId=" << spawnResult.projectile.projectileId
            << " object_id=" << spawnResult.projectile.objectDescriptionId
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
            << spawnResult.directionZ << ")";
        writeBlasterProjectileTrace(out.str());
    }

    return applyProjectileSpawnEffects(
        spawnResult,
        spawnEffects,
        "party",
        "party_projectile_zero_distance");
}

void OutdoorWorldRuntime::startGameplayScreenOverlay(uint32_t colorAbgr, float durationSeconds, float peakAlpha)
{
    m_gameplayOverlayColorAbgr = colorAbgr;
    m_gameplayOverlayDurationSeconds = std::max(durationSeconds, 0.0f);
    m_gameplayOverlayRemainingSeconds = m_gameplayOverlayDurationSeconds;
    m_gameplayOverlayPeakAlpha = std::clamp(peakAlpha, 0.0f, 1.0f);
    m_atmosphereState.gameplayOverlayColorAbgr = m_gameplayOverlayColorAbgr;
    m_atmosphereState.gameplayOverlayAlpha = 0.0f;
}

bool OutdoorWorldRuntime::tryStartArmageddon(
    size_t casterMemberIndex,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    std::string &failureText)
{
    failureText.clear();

    if (m_pParty == nullptr)
    {
        failureText = "Spell failed";
        return false;
    }

    if (isArmageddonActive())
    {
        failureText = "Armageddon already active";
        return false;
    }

    Character *pCaster = m_pParty->member(casterMemberIndex);

    if (pCaster == nullptr)
    {
        failureText = "Spell failed";
        return false;
    }

    const uint8_t castLimit = skillMastery == SkillMastery::Grandmaster ? 4 : 3;

    if (pCaster->armageddonCastsToday >= castLimit)
    {
        failureText = "No Armageddon casts left today";
        return false;
    }

    m_armageddonState.remainingSeconds = ArmageddonDurationSeconds;
    m_armageddonState.skillLevel = skillLevel;
    m_armageddonState.skillMastery = skillMastery;
    m_armageddonState.casterMemberIndex = static_cast<uint32_t>(casterMemberIndex);
    m_armageddonState.shakeStepsRemaining = ArmageddonShakeStepCount;
    ++m_armageddonState.shakeSequence;
    m_armageddonState.cameraShakeYawRadians = 0.0f;
    m_armageddonState.cameraShakePitchRadians = 0.0f;
    ++pCaster->armageddonCastsToday;
    return true;
}

bool OutdoorWorldRuntime::canActivateWorldHit(
    const GameplayWorldHit &hit,
    GameplayInteractionMethod interactionMethod) const
{
    if (m_pInteractionView == nullptr)
    {
        return false;
    }

    if (m_pInteractionView->arpgModeEnabled() && hit.kind == GameplayWorldHitKind::Corpse)
    {
        return false;
    }

    const OutdoorInteractionController::InteractionInputMethod outdoorMethod =
        interactionMethod == GameplayInteractionMethod::Keyboard
            ? OutdoorInteractionController::InteractionInputMethod::Keyboard
            : OutdoorInteractionController::InteractionInputMethod::Mouse;

    return OutdoorInteractionController::canDispatchWorldActivation(*m_pInteractionView, hit, outdoorMethod);
}

bool OutdoorWorldRuntime::activateWorldHit(const GameplayWorldHit &hit)
{
    if (m_pInteractionView == nullptr)
    {
        return false;
    }

    if (m_pInteractionView->arpgModeEnabled() && hit.kind == GameplayWorldHitKind::Corpse)
    {
        return false;
    }

    return OutdoorInteractionController::dispatchWorldActivation(*m_pInteractionView, hit);
}

bool OutdoorWorldRuntime::activateWorldHitFromSpell(const GameplayWorldHit &hit, uint32_t spellId)
{
    EventRuntimeState *pRuntimeState = eventRuntimeState();
    const uint32_t previousSpellId = pRuntimeState != nullptr ? pRuntimeState->activeEventSpellId : 0;

    if (pRuntimeState != nullptr)
    {
        pRuntimeState->activeEventSpellId = spellId;
    }

    const bool activated = activateWorldHit(hit);

    if (pRuntimeState != nullptr)
    {
        pRuntimeState->activeEventSpellId = previousSpellId;
    }

    return activated;
}

bool OutdoorWorldRuntime::canActivateTelekinesisTarget(const GameplayWorldHit &hit) const
{
    if (!hit.hasHit)
    {
        return false;
    }

    if (hit.kind == GameplayWorldHitKind::Chest && hit.container)
    {
        return hit.container->sourceKind == GameplayWorldContainerSourceKind::Chest
            && hit.container->sourceIndex < m_chests.size();
    }

    if (hit.kind == GameplayWorldHitKind::Corpse && hit.container)
    {
        return hit.container->sourceKind == GameplayWorldContainerSourceKind::Corpse;
    }

    if (m_pInteractionView == nullptr)
    {
        return false;
    }

    return OutdoorInteractionController::canActivateTelekinesisTarget(*m_pInteractionView, hit);
}

bool OutdoorWorldRuntime::activateTelekinesisTarget(const GameplayWorldHit &hit)
{
    if (!canActivateTelekinesisTarget(hit))
    {
        return false;
    }

    if (hit.kind == GameplayWorldHitKind::Chest && hit.container)
    {
        const uint32_t chestId = static_cast<uint32_t>(hit.container->sourceIndex);

        if (attemptOpenChest(chestId, true))
        {
            if (chestId < m_openedChests.size())
            {
                m_openedChests[chestId] = true;
            }

            if (chestId < m_chests.size())
            {
                m_chests[chestId].flags |= static_cast<uint16_t>(EvtChestFlag::Opened);
            }

            activateChestView(chestId);
            return true;
        }

        return false;
    }

    if (hit.kind == GameplayWorldHitKind::Corpse && hit.container)
    {
        if (m_pParty == nullptr || !openMapActorCorpseView(hit.container->sourceIndex))
        {
            return false;
        }

        const GameplayCorpseAutoLootResult lootResult =
            autoLootActiveCorpseView(*this, *m_pParty, m_pItemTable, nullptr);
        return lootResult.lootedAny || lootResult.blockedByInventory || lootResult.empty;
    }

    if (m_pInteractionView == nullptr)
    {
        return false;
    }

    EventRuntimeState *pEventRuntimeState = eventRuntimeState();
    const bool previousTelekinesisEvent =
        pEventRuntimeState != nullptr && pEventRuntimeState->activeEventOpenedByTelekinesis;

    if (pEventRuntimeState != nullptr)
    {
        pEventRuntimeState->activeEventOpenedByTelekinesis = true;
    }

    const bool activated = OutdoorInteractionController::dispatchTelekinesisActivation(*m_pInteractionView, hit);

    if (pEventRuntimeState != nullptr)
    {
        pEventRuntimeState->activeEventOpenedByTelekinesis = previousTelekinesisEvent;
    }

    return activated;
}

GameplayPendingSpellWorldTargetFacts OutdoorWorldRuntime::pickPendingSpellWorldTarget(
    const GameplayWorldPickRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickPendingSpellWorldTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        request);
}

GameplayWorldHit OutdoorWorldRuntime::pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickKeyboardInteractionTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        request);
}

GameplayWorldHit OutdoorWorldRuntime::pickNearbyInteractionTarget(float radius)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickNearbyInteractionTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        radius);
}

bool OutdoorWorldRuntime::tryActivateArpgModeLootPopup()
{
    return m_pInteractionView != nullptr && m_pInteractionView->tryActivateNearestArpgModeLootLabel();
}

GameplayWorldHit OutdoorWorldRuntime::pickForwardInteractionTarget(float depth)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickForwardInteractionTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        depth);
}

GameplayWorldHit OutdoorWorldRuntime::pickHeldItemWorldTarget(const GameplayWorldPickRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickHeldItemWorldTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        request);
}

GameplayWorldHit OutdoorWorldRuntime::pickMouseInteractionTarget(const GameplayWorldPickRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickCurrentInteractionTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        request);
}

GameplayWorldHoverCacheState OutdoorWorldRuntime::worldHoverCacheState() const
{
    if (m_pInteractionView == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::worldHoverCacheState(*m_pInteractionView);
}

GameplayHoverStatusPayload OutdoorWorldRuntime::refreshWorldHover(const GameplayWorldHoverRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::refreshWorldHover(*m_pInteractionView, *m_pOutdoorMapData, request);
}

GameplayHoverStatusPayload OutdoorWorldRuntime::readCachedWorldHover()
{
    if (m_pInteractionView == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::readCachedWorldHover(*m_pInteractionView);
}

void OutdoorWorldRuntime::clearWorldHover()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::clearWorldHover(*m_pInteractionView);
    }
}

bool OutdoorWorldRuntime::canUseHeldItemOnWorld(const GameplayWorldHit &hit) const
{
    return canActivateWorldHit(hit, GameplayInteractionMethod::Mouse);
}

bool OutdoorWorldRuntime::useHeldItemOnWorld(const GameplayWorldHit &hit)
{
    return activateWorldHit(hit);
}

void OutdoorWorldRuntime::applyPendingSpellCastWorldEffects(const PartySpellCastResult &castResult)
{
    if (m_pWorldFxSystem == nullptr)
    {
        return;
    }

    m_pWorldFxSystem->triggerPartySpellFx(castResult);
}

bool OutdoorWorldRuntime::dropHeldItemToWorld(const GameplayHeldItemDropRequest &request)
{
    return spawnWorldItem(
        request.item,
        request.sourceX,
        request.sourceY,
        request.sourceZ,
        request.yawRadians);
}

bool OutdoorWorldRuntime::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    state = {};

    if (m_map.fileName.empty() || m_pPartyRuntime == nullptr)
    {
        return false;
    }

    const Party &runtimeParty = m_pPartyRuntime->party();
    const PartyBuffState *pWizardEyeBuff = runtimeParty.partyBuff(PartyBuffId::WizardEye);
    const SkillMastery wizardEyeMastery =
        pWizardEyeBuff != nullptr ? pWizardEyeBuff->skillMastery : SkillMastery::None;
    const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();

    state.textureName = toLowerCopy(std::filesystem::path(m_map.fileName).stem().string());
    state.zoom = 512.0f;
    state.partyU = std::clamp((moveState.x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
    state.partyV = std::clamp((32768.0f - moveState.y) / 65536.0f, 0.0f, 1.0f);
    state.wizardEyeActive = pWizardEyeBuff != nullptr;
    state.wizardEyeShowsExpertObjects = wizardEyeMastery >= SkillMastery::Expert;
    state.wizardEyeShowsDecorations = state.wizardEyeActive;
    return true;
}

void OutdoorWorldRuntime::collectGameplayMinimapLines(std::vector<GameplayMinimapLineState> &lines)
{
    lines.clear();
}

void OutdoorWorldRuntime::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    markers.clear();

    GameplayMinimapState minimapState = {};

    if (!tryGetGameplayMinimapState(minimapState) || !minimapState.wizardEyeActive)
    {
        return;
    }

    for (size_t actorIndex = 0; actorIndex < mapActorCount(); ++actorIndex)
    {
        const MapActorState *pActor = mapActorState(actorIndex);

        if (pActor == nullptr || pActor->isInvisible)
        {
            continue;
        }

        const bool hostileToParty =
            pActor->hostileToParty && !outdoorActorIsPartyControlled(pActor->controlMode);

        if (!wizardEyeShowsActorMarker(pActor->isDead, pActor->hasDetectedParty, hostileToParty))
        {
            continue;
        }

        GameplayMinimapMarkerState marker = {};
        marker.type = pActor->isDead
            ? GameplayMinimapMarkerType::CorpseActor
            : hostileToParty ? GameplayMinimapMarkerType::HostileActor : GameplayMinimapMarkerType::FriendlyActor;
        marker.u = std::clamp((static_cast<float>(pActor->x) + 32768.0f) / 65536.0f, 0.0f, 1.0f);
        marker.v = std::clamp((32768.0f - static_cast<float>(pActor->y)) / 65536.0f, 0.0f, 1.0f);
        markers.push_back(marker);
    }

    if (minimapState.wizardEyeShowsExpertObjects)
    {
        for (size_t worldItemIndex = 0; worldItemIndex < worldItemCount(); ++worldItemIndex)
        {
            const WorldItemState *pWorldItem = worldItemState(worldItemIndex);

            if (pWorldItem == nullptr)
            {
                continue;
            }

            GameplayMinimapMarkerState marker = {};
            marker.type = GameplayMinimapMarkerType::WorldItem;
            marker.u = std::clamp((pWorldItem->x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
            marker.v = std::clamp((32768.0f - pWorldItem->y) / 65536.0f, 0.0f, 1.0f);
            markers.push_back(marker);
        }

        for (size_t projectileIndex = 0; projectileIndex < projectileCount(); ++projectileIndex)
        {
            const ProjectileState *pProjectile = projectileState(projectileIndex);

            if (pProjectile == nullptr)
            {
                continue;
            }

            GameplayMinimapMarkerState marker = {};
            marker.type = GameplayMinimapMarkerType::Projectile;
            marker.u = std::clamp((pProjectile->x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
            marker.v = std::clamp((32768.0f - pProjectile->y) / 65536.0f, 0.0f, 1.0f);
            markers.push_back(marker);
        }
    }

    if (minimapState.wizardEyeShowsDecorations
        && m_pOutdoorMapDeltaData != nullptr
        && m_pOutdoorMapData != nullptr)
    {
        for (size_t entityIndex = 0; entityIndex < m_pOutdoorMapData->entities.size(); ++entityIndex)
        {
            if (entityIndex >= m_pOutdoorMapDeltaData->decorationFlags.size())
            {
                continue;
            }

            const uint16_t decorationFlags = m_pOutdoorMapDeltaData->decorationFlags[entityIndex];

            if ((decorationFlags & LevelDecorationVisibleOnMap) == 0
                || (decorationFlags & LevelDecorationInvisible) != 0)
            {
                continue;
            }

            const OutdoorEntity &entity = m_pOutdoorMapData->entities[entityIndex];

            if (m_eventRuntimeState)
            {
                const uint32_t overrideKey = entity.spriteOverrideKey(entityIndex);
                const auto overrideIterator = m_eventRuntimeState->spriteOverrides.find(overrideKey);

                if (overrideIterator != m_eventRuntimeState->spriteOverrides.end() && overrideIterator->second.hidden)
                {
                    continue;
                }
            }

            GameplayMinimapMarkerState marker = {};
            marker.type = GameplayMinimapMarkerType::Decoration;
            marker.u = std::clamp((static_cast<float>(entity.x) + 32768.0f) / 65536.0f, 0.0f, 1.0f);
            marker.v = std::clamp((32768.0f - static_cast<float>(entity.y)) / 65536.0f, 0.0f, 1.0f);
            markers.push_back(marker);
        }
    }
}

bool OutdoorWorldRuntime::isArmageddonActive() const
{
    return m_armageddonState.active();
}

float OutdoorWorldRuntime::armageddonCameraShakeYawRadians() const
{
    return m_armageddonState.cameraShakeYawRadians;
}

float OutdoorWorldRuntime::armageddonCameraShakePitchRadians() const
{
    return m_armageddonState.cameraShakePitchRadians;
}

void OutdoorWorldRuntime::updateArmageddon(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (!m_armageddonState.active())
    {
        m_armageddonState.cameraShakeYawRadians = 0.0f;
        m_armageddonState.cameraShakePitchRadians = 0.0f;
        return;
    }

    m_armageddonState.remainingSeconds = std::max(0.0f, m_armageddonState.remainingSeconds - deltaSeconds);

    if (m_armageddonState.shakeStepsRemaining > 0)
    {
        std::mt19937 rng(
            static_cast<uint32_t>(m_mapId) * 2654435761u
            ^ (m_armageddonState.shakeSequence + 1u) * 2246822519u
            ^ m_armageddonState.shakeStepsRemaining * 3266489917u);
        std::uniform_real_distribution<float> yawDistribution(-ArmageddonShakeYawRadians, ArmageddonShakeYawRadians);
        std::uniform_real_distribution<float> pitchDistribution(-ArmageddonShakePitchRadians, ArmageddonShakePitchRadians);
        m_armageddonState.cameraShakeYawRadians = yawDistribution(rng);
        m_armageddonState.cameraShakePitchRadians = pitchDistribution(rng);
        --m_armageddonState.shakeStepsRemaining;
    }
    else
    {
        m_armageddonState.cameraShakeYawRadians = 0.0f;
        m_armageddonState.cameraShakePitchRadians = 0.0f;
    }

    if (m_armageddonState.remainingSeconds > 0.0f)
    {
        return;
    }

    resolveArmageddonDetonation(partyX, partyY, partyZ);
    m_armageddonState = {};
}

void OutdoorWorldRuntime::resolveArmageddonDetonation(float partyX, float partyY, float partyZ)
{
    if (m_pParty == nullptr)
    {
        return;
    }

    const int armageddonDamage = 50 + m_armageddonState.skillLevel;
    const uint32_t sourceMemberIndex = m_armageddonState.casterMemberIndex;

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        MapActorState &actor = m_mapActors[actorIndex];

        if (isActorUnavailableForCombat(actor))
        {
            continue;
        }

        const int beforeHp = actor.currentHp;
        const bool applied = applyPartyAttackToMapActor(actorIndex, armageddonDamage, partyX, partyY, partyZ);

        if (!applied)
        {
            continue;
        }

        if (m_pGameplayCombatController != nullptr)
        {
            m_pGameplayCombatController->recordPartyProjectileActorImpact(
                0,
                sourceMemberIndex,
                actor.actorId,
                armageddonDamage,
                spellIdValue(SpellId::Armageddon),
                true,
                beforeHp > 0 && actor.currentHp <= 0);
        }

        if (actor.currentHp > 0)
        {
            actor.stunRemainingSeconds = std::max(actor.stunRemainingSeconds, 1.0f);
            actor.aiState = ActorAiState::Stunned;
            actor.animation = ActorAnimation::GotHit;
            actor.actionSeconds = std::max(actor.actionSeconds, actor.stunRemainingSeconds);
        }
    }

    for (size_t memberIndex = 0; memberIndex < m_pParty->members().size(); ++memberIndex)
    {
        Character *pMember = m_pParty->member(memberIndex);

        if (pMember == nullptr
            || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Dead))
            || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
            || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
        {
            continue;
        }

        m_pParty->applyDamageToMember(memberIndex, armageddonDamage, "");
    }

    startGameplayScreenOverlay(makeAbgr(255, 56, 24), 0.6f, 0.72f);
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
