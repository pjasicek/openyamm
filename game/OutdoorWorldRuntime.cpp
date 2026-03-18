#include "game/OutdoorWorldRuntime.h"

#include "game/ItemTable.h"
#include "game/OutdoorGeometryUtils.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <iostream>
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
constexpr float MeleeRange = 307.0f;
constexpr float DetectionRange = 5120.0f;
constexpr float PeasantAggroRadius = 4096.0f;
constexpr float FleeThresholdRange = 10240.0f;
constexpr float PartyCollisionRadius = 37.0f;
constexpr float GroundSnapHeight = 1.0f;
constexpr float OeNonFlyingActorRadius = 40.0f;
constexpr float ActorUpdateStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedActorUpdateSeconds = 0.1f;
constexpr float Pi = 3.14159265358979323846f;
constexpr int DwiMapId = 1;
constexpr uint32_t DwiTestActor61 = 61;
constexpr float DwiTestActor61X = -7665.0f;
constexpr float DwiTestActor61Y = -4660.0f;
constexpr float DwiTestActor61Z = 200.0f;

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
    state.hostilityType = static_cast<uint8_t>(pStats != nullptr ? pStats->hostility : actor.hostilityType);
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
    state.typeId = spawn.typeId;
    state.index = spawn.index;
    state.group = spawn.group;

    if (spawn.typeId != 3)
    {
        return state;
    }

    int encounterSlot = 0;
    char fixedTier = '\0';

    if (spawn.index >= 1 && spawn.index <= 3)
    {
        encounterSlot = spawn.index;
    }
    else if (spawn.index >= 4 && spawn.index <= 12)
    {
        encounterSlot = static_cast<int>((spawn.index - 4) % 3) + 1;
        fixedTier = static_cast<char>('A' + (spawn.index - 4) / 3);
    }

    state.encounterSlot = encounterSlot;
    state.isFixedTier = fixedTier != '\0';
    state.fixedTier = fixedTier;

    const MapEncounterInfo *pEncounter = getEncounterInfo(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return state;
    }

    state.monsterFamilyName = pEncounter->monsterName;
    state.representativePictureName = pEncounter->pictureName.empty()
        ? pEncounter->monsterName
        : pEncounter->pictureName;

    if (fixedTier == '\0')
    {
        state.representativePictureName += " A";
    }
    else
    {
        state.representativePictureName += " ";
        state.representativePictureName.push_back(fixedTier);
    }

    const MonsterTable::MonsterStatsEntry *pStats =
        monsterTable.findStatsByPictureName(state.representativePictureName);

    if (pStats == nullptr)
    {
        return state;
    }

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

float attackActionDurationSeconds(float attackAnimationSeconds, float recoverySeconds)
{
    return std::max(std::max(0.1f, attackAnimationSeconds), std::clamp(recoverySeconds * 0.5f, 0.25f, 0.6f));
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

    std::cout << "Chest populate: chest=" << chestId
              << " type=" << chest.chestTypeId
              << " flags=0x" << std::hex << chest.flags << std::dec
              << " raw_records=" << (chest.rawItems.size() / ChestItemRecordSize)
              << '\n';

    if (chest.rawItems.empty() || chest.inventoryMatrix.empty())
    {
        std::cout << "  empty source buffers\n";
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

    std::cout << "  matrix positive=" << positiveCells
              << " negative=" << negativeCells
              << " sample=[" << matrixSample.str() << "]"
              << '\n';

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
        std::cout << "  record=" << itemIndex
                  << " raw_item_id=" << itemId
                  << " grid_ref=" << (hasGridReference ? "yes" : "no")
                  << '\n';

        if (itemId > 0)
        {
            ChestItemState item = {};
            item.itemId = static_cast<uint32_t>(itemId);
            item.quantity = 1;
            appendChestItem(view.items, item);
            std::cout << "    serialized item=" << item.itemId;

            if (m_pItemTable != nullptr && m_pItemTable->get(item.itemId) == nullptr)
            {
                std::cout << " unknown";
            }

            std::cout << '\n';
            continue;
        }

        if (itemId > -8 && itemId < 0)
        {
            const int resolvedTreasureLevel = remapTreasureLevel(-itemId, mapTreasureLevel);
            const int generatedCount = std::uniform_int_distribution<int>(1, 5)(rng);
            std::cout << "    random placeholder level=" << (-itemId)
                      << " map_treasure=" << mapTreasureLevel
                      << " resolved=" << resolvedTreasureLevel
                      << " rolls=" << generatedCount
                      << '\n';

            for (int count = 0; count < generatedCount; ++count)
            {
                const int roll = std::uniform_int_distribution<int>(0, 99)(rng);
                std::cout << "      roll=" << roll;

                if (roll < 20)
                {
                    std::cout << " -> empty\n";
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
                        std::cout << " -> gold " << gold.goldAmount << '\n';
                    }
                    else
                    {
                        std::cout << " -> gold 0 skipped\n";
                    }

                    continue;
                }

                const int generationLevel = std::min(resolvedTreasureLevel, SpawnableItemTreasureLevels);
                const uint32_t generatedItemId = generateRandomItemId(generationLevel, rng);

                if (generatedItemId == 0)
                {
                    std::cout << " -> item generation failed\n";
                    continue;
                }

                ChestItemState item = {};
                item.itemId = generatedItemId;
                item.quantity = 1;
                appendChestItem(view.items, item);
                std::cout << " -> item " << generatedItemId << '\n';
            }

            continue;
        }

        std::cout << "    unsupported negative item marker skipped\n";
    }

    std::cout << "  materialized_records=" << materializedRecords
              << " final_entries=" << view.items.size()
              << '\n';

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
    const ItemTable &itemTable,
    const std::optional<OutdoorMapData> &outdoorMapData,
    const std::optional<MapDeltaData> &outdoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet
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
    m_summonedMonsters.clear();
    m_mapActorCorpseViews.clear();
    m_summonedMonsterCorpseViews.clear();
    m_activeCorpseView.reset();
    m_pendingAudioEvents.clear();
    m_pendingCombatEvents.clear();
    m_chests = outdoorMapDeltaData ? outdoorMapDeltaData->chests : std::vector<MapDeltaChest>();
    m_openedChests.assign(outdoorMapDeltaData ? outdoorMapDeltaData->chests.size() : 0, false);
    m_materializedChestViews.assign(m_chests.size(), std::nullopt);
    m_activeChestView.reset();
    m_eventRuntimeState = eventRuntimeState;
    m_pItemTable = &itemTable;
    m_pMonsterTable = &monsterTable;
    m_pOutdoorMapData = outdoorMapData ? &*outdoorMapData : nullptr;
    m_pOutdoorMapDeltaData = outdoorMapDeltaData ? &*outdoorMapDeltaData : nullptr;
    m_outdoorFaces.clear();
    m_outdoorMovementController.reset();
    m_actorUpdateAccumulatorSeconds = 0.0f;

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
    m_nextSummonId = 1;

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
    }

    m_summonedMonsterCorpseViews.clear();

    if (outdoorMapData)
    {
        m_spawnPoints.reserve(outdoorMapData->spawns.size());

        for (const OutdoorSpawn &spawn : outdoorMapData->spawns)
        {
            m_spawnPoints.push_back(buildSpawnPointState(map, monsterTable, spawn));
        }
    }

    std::random_device randomDevice;
    const uint64_t timeSeed = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    m_sessionChestSeed = randomDevice() ^ static_cast<uint32_t>(timeSeed) ^ static_cast<uint32_t>(timeSeed >> 32);
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
        if (m_outdoorMovementController)
        {
            m_outdoorMovementController->setActorColliders({});
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
            actor.idleDecisionSeconds = std::max(0.0f, actor.idleDecisionSeconds - ActorUpdateStepSeconds);
            actor.attackCooldownSeconds = std::max(0.0f, actor.attackCooldownSeconds - ActorUpdateStepSeconds);
            actor.actionSeconds = std::max(0.0f, actor.actionSeconds - ActorUpdateStepSeconds);

        const float deltaPartyX = partyX - actor.preciseX;
        const float deltaPartyY = partyY - actor.preciseY;
        const float deltaPartyZ = partyZ - actor.preciseZ;
        const float distanceToParty = length2d(deltaPartyX, deltaPartyY);
        const float partyEdgeDistance = std::max(
            0.0f,
            distanceToParty - static_cast<float>(actor.radius) - PartyCollisionRadius);
        const float verticalDistance = std::abs(deltaPartyZ);
        const bool canSenseParty = distanceToParty <= DetectionRange && verticalDistance <= 1024.0f;
        const bool movementAllowed = pStats->movementType != MonsterTable::MonsterMovementType::Stationary;
        const bool shouldEngageParty = actor.hostileToParty && canSenseParty;

        if (shouldEngageParty && !actor.hasDetectedParty)
        {
            actor.hasDetectedParty = true;
            pushAudioEvent(pStats->awareSoundId, actor.actorId, "monster_alert");
        }
        else if (!canSenseParty)
        {
            actor.hasDetectedParty = false;
        }

        const bool shouldFlee = shouldEngageParty
            && distanceToParty <= FleeThresholdRange
            && shouldFleeForAiType(*pStats, actor);
        const bool inMeleeRange = partyEdgeDistance <= MeleeRange;
        const bool attackJustCompleted =
            actor.aiState == ActorAiState::Attacking
            && actor.actionSeconds <= 0.0f
            && !actor.attackImpactTriggered;
        const bool attackInProgress =
            actor.aiState == ActorAiState::Attacking
            && actor.actionSeconds > 0.0f;
        const bool friendlyNearParty =
            !actor.hostileToParty
            && canSenseParty
            && distanceToParty <= (static_cast<float>(actor.radius) + PartyCollisionRadius + 16.0f);
        float desiredMoveX = 0.0f;
        float desiredMoveY = 0.0f;
        ActorAiState nextAiState = ActorAiState::Standing;
        ActorAnimation nextAnimation = ActorAnimation::Standing;

        if (attackJustCompleted)
        {
            CombatEvent event = {};
            event.type = isRangedAttackAbility(*pStats, actor.queuedAttackAbility)
                ? CombatEvent::Type::MonsterRangedRelease
                : CombatEvent::Type::MonsterMeleeImpact;
            event.sourceId = actor.actorId;
            event.fromSummonedMonster = false;
            event.ability = actor.queuedAttackAbility;
            m_pendingCombatEvents.push_back(std::move(event));
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

            if (distanceToParty > 0.01f)
            {
                desiredMoveX = -deltaPartyX / distanceToParty;
                desiredMoveY = -deltaPartyY / distanceToParty;
                faceDirection(actor, desiredMoveX, desiredMoveY);
            }

            actor.moveDirectionX = desiredMoveX;
            actor.moveDirectionY = desiredMoveY;
        }
        else if (shouldEngageParty)
        {
            const MonsterAttackAbility chosenAbility = chooseAttackAbility(actor, *pStats);
            const bool chosenAbilityIsRanged = isRangedAttackAbility(*pStats, chosenAbility);
            const bool chosenAbilityIsMelee = isMeleeAttackAbility(*pStats, chosenAbility);
            const bool stationaryOrTooCloseForRangedPursuit = !movementAllowed || inMeleeRange;

            if (chosenAbilityIsRanged && actor.attackCooldownSeconds <= 0.0f)
            {
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                faceDirection(actor, deltaPartyX, deltaPartyY);
                nextAiState = ActorAiState::Attacking;
                nextAnimation = attackAnimationForAbility(*pStats, chosenAbility);
                actor.queuedAttackAbility = chosenAbility;
                actor.attackCooldownSeconds = attackCooldownDurationSeconds(
                    *pStats,
                    chosenAbility,
                    actor.attackAnimationSeconds,
                    actor.recoverySeconds);
                actor.actionSeconds = attackActionDurationSeconds(actor.attackAnimationSeconds, actor.recoverySeconds);
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
                    faceDirection(actor, deltaPartyX, deltaPartyY);
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
                                deltaPartyX,
                                deltaPartyY,
                                distanceToParty,
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
                faceDirection(actor, deltaPartyX, deltaPartyY);

                if (actor.attackCooldownSeconds <= 0.0f)
                {
                    nextAiState = ActorAiState::Attacking;
                    nextAnimation = attackAnimationForAbility(*pStats, chosenAbility);
                    actor.queuedAttackAbility = chosenAbility;
                    actor.attackCooldownSeconds = attackCooldownDurationSeconds(
                        *pStats,
                        chosenAbility,
                        actor.attackAnimationSeconds,
                        actor.recoverySeconds);
                    actor.actionSeconds = attackActionDurationSeconds(actor.attackAnimationSeconds, actor.recoverySeconds);
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

                    if (partyEdgeDistance >= 1024.0f)
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
                            deltaPartyX,
                            deltaPartyY,
                            distanceToParty,
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

            if (wanderRadius <= 0.0f)
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
                actor.velocityX = desiredMoveX * moveSpeed;
                actor.velocityY = desiredMoveY * moveSpeed;
                const float moveDeltaX = actor.velocityX * ActorUpdateStepSeconds;
                const float moveDeltaY = actor.velocityY * ActorUpdateStepSeconds;
                bool moved = false;

            if (m_outdoorMovementController && actor.movementStateInitialized)
            {
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
                moved = tryMoveActorInWorld(actor, *m_pOutdoorMapData, m_outdoorFaces, pStats, moveDeltaX, moveDeltaY);

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

        m_actorUpdateAccumulatorSeconds -= ActorUpdateStepSeconds;
    }
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

        for (SummonedMonsterState &monster : m_summonedMonsters)
        {
            if (monster.group == groupId)
            {
                monster.isInvisible = true;
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

        for (SummonedMonsterState &monster : m_summonedMonsters)
        {
            if (monster.group == groupId)
            {
                monster.isInvisible = false;
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

bool OutdoorWorldRuntime::setMapActorDead(size_t actorIndex, bool isDead)
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

            pushAudioEvent(pStats->deathSoundId, actor.actorId, "monster_death");
        }
    }

    if (wasDead && !isDead && actorIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[actorIndex].reset();
    }

    return true;
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

    if (actor.isDead || actor.isInvisible)
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
        MapActorState &otherActor = m_mapActors[otherActorIndex];

        if (otherActor.isDead || otherActor.isInvisible)
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

    if (actor.isDead || actor.isInvisible)
    {
        return false;
    }

    actor.currentHp = std::max(0, actor.currentHp - damage);
    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
    actor.aiState = ActorAiState::Standing;
    actor.animation = ActorAnimation::GotHit;
    actor.animationTimeTicks = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.actionSeconds = 0.2f;
    actor.idleDecisionSeconds = 0.2f;
    actor.attackImpactTriggered = false;

    setMapActorHostileToParty(actorIndex, partyX, partyY, partyZ, true);

    const bool died = actor.currentHp <= 0;

    if (died)
    {
        setMapActorDead(actorIndex, true);
    }
    else if (m_pMonsterTable != nullptr)
    {
        if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
        {
            pushAudioEvent(pStats->winceSoundId, actor.actorId, "monster_hit");
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

    if (actor.isDead || actor.isInvisible || actor.hostileToParty)
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

size_t OutdoorWorldRuntime::summonedMonsterCount() const
{
    return m_summonedMonsters.size();
}

const OutdoorWorldRuntime::SummonedMonsterState *OutdoorWorldRuntime::summonedMonsterState(size_t summonIndex) const
{
    if (summonIndex >= m_summonedMonsters.size())
    {
        return nullptr;
    }

    return &m_summonedMonsters[summonIndex];
}

bool OutdoorWorldRuntime::setSummonedMonsterDead(size_t summonIndex, bool isDead)
{
    if (summonIndex >= m_summonedMonsters.size())
    {
        return false;
    }

    SummonedMonsterState &monster = m_summonedMonsters[summonIndex];
    const bool wasDead = monster.isDead;
    monster.isDead = isDead;
    monster.currentHp = isDead ? 0 : monster.maxHp;

    if (!wasDead && isDead && m_pMonsterTable != nullptr)
    {
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(monster.monsterId);

        if (pStats != nullptr)
        {
            if (summonIndex >= m_summonedMonsterCorpseViews.size())
            {
                m_summonedMonsterCorpseViews.resize(summonIndex + 1);
            }

            if (!m_summonedMonsterCorpseViews[summonIndex].has_value())
            {
                CorpseViewState corpse = buildCorpseView(monster.displayName, pStats->loot, makeChestSeed(
                    m_sessionChestSeed,
                    m_mapId,
                    monster.summonId,
                    0x53554d4du));
                corpse.fromSummonedMonster = true;
                corpse.sourceIndex = static_cast<uint32_t>(summonIndex);
                m_summonedMonsterCorpseViews[summonIndex] = std::move(corpse);
            }

            pushAudioEvent(pStats->deathSoundId, monster.summonId, "monster_death");
        }
    }

    if (wasDead && !isDead && summonIndex < m_summonedMonsterCorpseViews.size())
    {
        m_summonedMonsterCorpseViews[summonIndex].reset();
    }

    return true;
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

    std::vector<std::optional<CorpseViewState>> *pStorage = m_activeCorpseView->fromSummonedMonster
        ? &m_summonedMonsterCorpseViews
        : &m_mapActorCorpseViews;

    if (m_activeCorpseView->sourceIndex < pStorage->size())
    {
        (*pStorage)[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
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

    const MapEncounterInfo *pEncounter = getEncounterInfo(m_map, static_cast<int>(typeIndexInMapStats));

    if (pEncounter == nullptr)
    {
        return false;
    }

    std::string pictureName = encounterPictureBase(*pEncounter);
    pictureName += " ";
    pictureName.push_back(tierLetterForSummonLevel(level));

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsByPictureName(pictureName);

    if (pStats == nullptr)
    {
        return false;
    }

    for (uint32_t index = 0; index < count; ++index)
    {
        SummonedMonsterState monster = {};
        monster.summonId = m_nextSummonId++;
        monster.monsterId = static_cast<int16_t>(pStats->id);
        monster.displayName = pStats->name;
        monster.group = group;
        monster.x = x;
        monster.y = y;
        monster.z = z;
        monster.uniqueNameId = uniqueNameId;
        monster.hostilityType = static_cast<uint8_t>(pStats->hostility);
        monster.maxHp = pStats->hitPoints;
        monster.currentHp = pStats->hitPoints;
        monster.hostileToParty = m_pMonsterTable->isHostileToParty(monster.monsterId);
        m_summonedMonsters.push_back(std::move(monster));
    }

    applyEventRuntimeState();
    return true;
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

    for (const SummonedMonsterState &monster : m_summonedMonsters)
    {
        bool matches = false;

        switch (checkType)
        {
            case CheckActorKilledByAny:
                matches = true;
                break;

            case CheckActorKilledByGroup:
                matches = monster.group == id;
                break;

            case CheckActorKilledByMonsterId:
                matches = monster.monsterId == static_cast<int16_t>(id);
                break;

            case CheckActorKilledByActorIdOe:
            case CheckActorKilledByActorIdMm8:
                matches = false;
                break;

            default:
                break;
        }

        countMonster(matches, monster.isDead || monster.currentHp <= 0, monster.isInvisible);
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

const EventRuntimeState *OutdoorWorldRuntime::eventRuntimeState() const
{
    if (!m_eventRuntimeState)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState;
}
}
