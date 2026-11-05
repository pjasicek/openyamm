#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/ActorRepositionRules.h"
#include "game/gameplay/ActorVocalizationRules.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/Mm9ActorRules.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ActorAiTicksPerSecond = 128.0f;
constexpr float ActorAiUpdateStepSeconds = 1.0f / ActorAiTicksPerSecond;
constexpr float Pi = 3.14159265358979323846f;
constexpr float ActorCrowdSideLockSeconds = 0.22f;
constexpr float ActorCrowdRetreatAngleRadians = Pi * 0.53f;
constexpr float ActorCrowdSidestepAngleRadians = Pi / 4.0f;
constexpr float CrowdNoProgressThreshold = 8.0f;
constexpr float CrowdNoProgressStandSeconds = 1.2f;
constexpr float CrowdProbeWindowSeconds = 0.35f;
constexpr float CrowdProbeEdgeDistanceThreshold = 12.0f;
constexpr float CrowdReangleEngageRange = 1024.0f;
constexpr float ContactFleeFallbackSeconds = 0.25f;
constexpr float ActorMeleeRange = 307.2f;
// Monsters shoot and cast only at targets nearer than this; farther ones they close in on.
constexpr float MaximumRangedAttackDistance = 5120.0f;
constexpr float HostilityLongRange = GameplayActorService::MaximumPartyEngagementRange;
constexpr float IdleStandSeconds = 1.5f;
constexpr float IdleBoredSeconds = 2.0f;
// The original doubles monster speed while pursuing or fleeing (MM8 0x46fc98-0x46ff26).
constexpr float PursueMoveSpeedMultiplier = 2.0f;
constexpr float FleeMoveSpeedMultiplier = 2.0f;
// 16 of the original 2048 angle units.
constexpr float RangedOrbitStepRadians = Pi / 64.0f;
constexpr float MaxActorMoveSpeed = 1000.0f;
// The original speeds monsters up by 5/3 during the turn-based wait stage, before its 1000 cap (MM8 0x46fd09).
constexpr float TurnBasedWaitMoveSpeedMultiplier = 5.0f / 3.0f;
constexpr uint32_t IdleStandChancePercent = 25u;
// Tactics (ActorTacticsFacts): a post counts as reached within this distance of home; band moves last at most these.
constexpr float TacticPostArrivalRadius = 48.0f;
constexpr float TacticPostReturnStepSeconds = 0.5f;
constexpr float TacticBackOffSeconds = 0.4f;
// A traverse eases out of its turn: within traverse rate x this of its goal it closes the rest exponentially.
constexpr float TacticTraverseEaseSeconds = 0.1f;
// Skirmishers (ActorTacticsFacts::skirmish): MM9's BaseMelee and BaseEvade scripts
// (devdocs/mm9_rework/MM9_ACTOR_ANIMATION_BLENDING_RE.md); MM9 distances x 2.56.
// A strafe attack runs 45 degrees off the line to the target, at half speed until the blow lands.
constexpr float SkirmishStrafeAttackAngleRadians = Pi / 4.0f;
constexpr float SkirmishStrafeWindupSpeedShare = 0.5f;
// An evade backpedals straight away from the target, turned 5-35 degrees to a random side, then circles it 65 degrees
// off the line to it, picking the line again every 0.1-0.4 s; it ends early when the target is 1280 units away.
// It backpedals at walking pace (half its doubled pursuit speed): close to MM9's BackpedalRun, and a backwards run at
// the pursuit speed would slide its feet.
constexpr float SkirmishBackpedalSpeedShare = 0.5f;
constexpr float SkirmishBackpedalMinJitterRadians = Pi * 5.0f / 180.0f;
constexpr float SkirmishBackpedalMaxJitterRadians = Pi * 35.0f / 180.0f;
constexpr float SkirmishCircleAngleRadians = Pi * 65.0f / 180.0f;
constexpr float SkirmishCircleMinSeconds = 0.1f;
constexpr float SkirmishCircleMaxSeconds = 0.4f;
constexpr float SkirmishEvadeCancelDistance = 1280.0f;
// A target moving slower than this (MM9's 20 units a second) stands.
constexpr float SkirmishTargetMovingSpeed = 51.2f;
// While it strikes it runs after a moving target until within a quarter of its melee range; it steps after a standing
// one beyond 3/4 of that range and stops within half of it.
constexpr float SkirmishMovingChaseStopRangeShare = 0.25f;
constexpr float SkirmishChaseStartRangeShare = 0.75f;
constexpr float SkirmishChaseStopRangeShare = 0.5f;
// MM9's SpeedThrottle: within 0.9 of its reach it keeps 0.95x the pace of a target moving away within 45 degrees;
// beyond, its swing's lunge runs 1.25x faster.
constexpr float SkirmishThrottleRangeShare = 0.9f;
constexpr float SkirmishThrottleAngleRadians = Pi / 4.0f;
constexpr float SkirmishThrottleTargetSpeedShare = 0.95f;
constexpr float SkirmishLungeSpeedShare = 1.25f;
// An evade from a target moving away within 30 degrees circles it without backpedalling.
constexpr float SkirmishCircleAwayAngleRadians = Pi / 6.0f;
// A shot or spell is fired on the run when the target is farther than this much running away (MM9 Range.inc Type 1).
constexpr float SkirmishRunningShotMinSeconds = 1.0f;

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

float length2d(float x, float y)
{
    return std::sqrt(x * x + y * y);
}

float lengthSquared3d(float x, float y, float z)
{
    return x * x + y * y + z * z;
}

float shortestAngleDistanceRadians(float left, float right)
{
    return std::abs(normalizeAngleRadians(left - right));
}

bool isDeadOrDying(const ActorAiFacts &actor)
{
    return actor.status.dead
        || actor.stats.currentHp <= 0
        || actor.runtime.motionState == ActorAiMotionState::Dying
        || actor.runtime.motionState == ActorAiMotionState::Dead;
}

bool isStatusLocked(const ActorAiFacts &actor)
{
    return actor.runtime.motionState == ActorAiMotionState::Stunned
        || actor.status.spellEffects.stunRemainingSeconds > 0.0f
        || actor.status.spellEffects.paralyzeRemainingSeconds > 0.0f;
}

float movementSpeedForMotion(float effectiveMoveSpeed, ActorAiMotionState motionState)
{
    float moveSpeed = std::max(0.0f, effectiveMoveSpeed);

    if (motionState == ActorAiMotionState::Pursuing)
    {
        moveSpeed *= PursueMoveSpeedMultiplier;
    }
    else if (motionState == ActorAiMotionState::Fleeing)
    {
        moveSpeed *= FleeMoveSpeedMultiplier;
    }

    return std::min(moveSpeed, MaxActorMoveSpeed);
}

struct AttackDamageProfile
{
    int diceRolls = 0;
    int diceSides = 0;
    int bonus = 0;
};

struct ActorTargetState
{
    ActorAiTargetKind kind = ActorAiTargetKind::None;
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

struct ActorEngagementState
{
    bool hasCombatTarget = false;
    bool targetIsParty = false;
    bool targetIsActor = false;
    bool shouldEngageTarget = false;
    bool shouldPromoteHostility = false;
    bool shouldUpdateHostilityType = false;
    uint8_t hostilityType = 0;
    bool hasDetectedParty = false;
    float promotionRange = 0.0f;
    bool shouldFlee = false;
    bool inMeleeRange = false;
    bool friendlyNearParty = false;
};

enum class AttackImpactAction : uint8_t
{
    None = 0,
    RangedRelease = 1,
    PartyMeleeImpact = 2,
    ActorMeleeImpact = 3,
};

enum class PursueActionMode : uint8_t
{
    OffsetShort = 0,
    Direct = 1,
    OffsetWide = 2,
    RangedOrbit = 3,
};

enum class CombatEngageAction : uint8_t
{
    HoldCrowdStand = 0,
    StartRangedAttack = 1,
    StandForRangedBlock = 2,
    ContinueRangedPursuit = 3,
    StartRangedPursuit = 4,
    StartMeleeAttack = 5,
    StandForMeleeCooldown = 6,
    ContinueMeleePursuit = 7,
    StartMeleePursuit = 8,
    StartMeleePursuitWithoutMovement = 9,
};

enum class CrowdSteeringAction : uint8_t
{
    SideStep = 0,
    Retreat = 1,
    Stand = 2,
};

enum class IdleBehaviorAction : uint8_t
{
    Stand = 0,
    Wander = 1,
};

struct IdleBehaviorResult
{
    IdleBehaviorAction action = IdleBehaviorAction::Stand;
    bool bored = false;
    bool updateYaw = false;
    float yawRadians = 0.0f;
    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    float actionSeconds = 0.0f;
    float idleDecisionSeconds = 0.0f;
    uint32_t nextDecisionCount = 0;
};

struct AttackStartOutcome
{
    float attackCooldownSeconds = 0.0f;
    float actionSeconds = 0.0f;
};

struct AttackImpactOutcome
{
    AttackImpactAction action = AttackImpactAction::None;
    int damage = 0;
};

struct CrowdSteeringState
{
    float noProgressSeconds = 0.0f;
    float lastEdgeDistance = 0.0f;
    float retreatRemainingSeconds = 0.0f;
    float standRemainingSeconds = 0.0f;
    float probeEdgeDistance = 0.0f;
    float probeElapsedSeconds = 0.0f;
    uint8_t escapeAttempts = 0;
    int8_t sideSign = 0;
};

struct CrowdSteeringResult
{
    CrowdSteeringAction action = CrowdSteeringAction::SideStep;
    CrowdSteeringState state = {};
    int sideSign = 1;
    float retreatSeconds = 0.0f;
    float standSeconds = 0.0f;
    bool bored = false;
    uint32_t nextDecisionCount = 0;
};

struct CrowdSteeringEligibility
{
    size_t contactedActorCount = 0;
    bool meleePursuitActive = false;
    bool pursuing = false;
    bool actorCanFly = false;
    bool inMeleeRange = false;
    bool movementBlocked = false;
    float targetEdgeDistance = 0.0f;
};

struct RangedAbilityCommitInput
{
    uint32_t actorId = 0;
    uint32_t attackDecisionCount = 0;
    GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
    bool abilityIsRanged = false;
    bool movementAllowed = false;
    bool targetIsActor = false;
    float targetEdgeDistance = 0.0f;
    float rangedAttackReach = MaximumRangedAttackDistance;
};

struct CombatAbilityChoiceInput
{
    uint32_t actorId = 0;
    uint32_t attackDecisionCount = 0;
    bool hasSpell1 = false;
    bool spell1IsOkToCast = false;
    int spell1UseChance = 0;
    bool hasSpell2 = false;
    bool spell2IsOkToCast = false;
    int spell2UseChance = 0;
    int attack2Chance = 0;
    GameplayActorAttackConstraintState constraintState = {};
    bool movementAllowed = false;
    bool targetIsActor = false;
    float targetEdgeDistance = 0.0f;
    // The farthest target it shoots or casts at.
    float rangedAttackReach = MaximumRangedAttackDistance;
    bool inMeleeRange = false;
    bool chooseRandomAbility = true;
    bool applyAbilityConstraints = true;
    // Tactics' ranged band: a chosen ranged attack commits at any distance instead of the native distance roll.
    bool forceRangedCommit = false;
};

struct CombatAbilityChoiceResult
{
    GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
    uint32_t nextAttackDecisionCount = 0;
    bool abilityIsRanged = false;
    bool abilityIsMelee = true;
    bool stationaryOrTooCloseForRangedPursuit = false;
};

struct CombatEngagePlanInput
{
    bool abilityIsRanged = false;
    bool abilityIsMelee = false;
    bool inMeleeRange = false;
    bool attackCooldownReady = false;
    bool movementAllowed = false;
    bool stationaryOrTooCloseForRangedPursuit = false;
    bool currentlyPursuing = false;
    bool crowdStandActive = false;
    float actionSeconds = 0.0f;
    float currentMoveDirectionX = 0.0f;
    float currentMoveDirectionY = 0.0f;
    float targetEdgeDistance = 0.0f;
};

struct CombatEngagePlan
{
    CombatEngageAction action = CombatEngageAction::StartMeleePursuit;
    PursueActionMode pursueMode = PursueActionMode::Direct;
    bool meleePursuitActive = false;
    bool preserveCrowdSteering = false;
    bool useRecoveryFloorForPursuit = false;
};

struct PursueActionInput
{
    uint32_t actorId = 0;
    uint32_t pursueDecisionCount = 0;
    float deltaTargetX = 0.0f;
    float deltaTargetY = 0.0f;
    float distanceToTarget = 0.0f;
    float moveSpeed = 0.0f;
    float minimumActionSeconds = 0.0f;
    PursueActionMode mode = PursueActionMode::Direct;
};

struct PursueActionResult
{
    bool started = false;
    uint32_t nextDecisionCount = 0;
    float yawRadians = 0.0f;
    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    float actionSeconds = 0.0f;
};

AttackDamageProfile attackDamageProfileFromFacts(const ActorStatsFacts::AttackDamageFacts &facts)
{
    AttackDamageProfile profile = {};
    profile.diceRolls = facts.diceRolls;
    profile.diceSides = facts.diceSides;
    profile.bonus = facts.bonus;
    return profile;
}

CombatDamageType attackDamageTypeFromFacts(
    GameplayActorAttackAbility ability,
    const ActorStatsFacts &stats)
{
    switch (ability)
    {
        case GameplayActorAttackAbility::Attack2:
            return stats.attack2DamageType;

        case GameplayActorAttackAbility::Spell1:
            return stats.spell1DamageType;

        case GameplayActorAttackAbility::Spell2:
            return stats.spell2DamageType;

        case GameplayActorAttackAbility::Attack1:
        default:
            return stats.attack1DamageType;
    }
}

uint32_t mixActorDecisionSeed(uint32_t actorId, uint32_t counter, uint32_t salt)
{
    return static_cast<uint32_t>(actorId + 1) * 1103515245u
        + counter * 2654435761u
        + salt;
}

float actorDecisionUnitFloat(uint32_t actorId, uint32_t counter, uint32_t salt)
{
    const uint32_t seed = mixActorDecisionSeed(actorId, counter, salt);
    return static_cast<float>(seed & 0xffffu) / 65535.0f;
}

float actorDecisionRange(
    uint32_t actorId,
    uint32_t counter,
    uint32_t salt,
    float minimumValue,
    float maximumValue)
{
    return minimumValue + (maximumValue - minimumValue) * actorDecisionUnitFloat(actorId, counter, salt);
}

IdleBehaviorResult idleStandBehavior(bool bored)
{
    IdleBehaviorResult result = {};
    result.action = IdleBehaviorAction::Stand;
    result.bored = bored;
    result.actionSeconds = bored ? IdleBoredSeconds : IdleStandSeconds;
    result.idleDecisionSeconds = result.actionSeconds;
    return result;
}

IdleBehaviorResult resolveIdleBehavior(
    uint32_t actorId,
    uint32_t idleDecisionCount,
    float preciseX,
    float preciseY,
    float homePreciseX,
    float homePreciseY,
    float currentYawRadians,
    bool currentlyWalking,
    float wanderRadius,
    float moveSpeed)
{
    IdleBehaviorResult result = idleStandBehavior(actorChoosesBored(actorId, idleDecisionCount));
    result.nextDecisionCount = idleDecisionCount + 1;

    const uint32_t decisionSeed = mixActorDecisionSeed(actorId, idleDecisionCount, 12345u);

    if ((decisionSeed % 100u) < IdleStandChancePercent)
    {
        return result;
    }

    const float deltaHomeX = homePreciseX - preciseX;
    const float deltaHomeY = homePreciseY - preciseY;
    float homeAngle = std::atan2(deltaHomeY, deltaHomeX);

    if (std::abs(deltaHomeX) <= 0.01f && std::abs(deltaHomeY) <= 0.01f)
    {
        homeAngle = currentYawRadians;
    }

    const float randomAngleOffset =
        ((static_cast<int>(decisionSeed % 257u) - 128) / 256.0f) * (Pi / 4.0f);
    const float proposedYaw = normalizeAngleRadians(homeAngle + randomAngleOffset);

    if (shortestAngleDistanceRadians(proposedYaw, currentYawRadians) > (Pi / 4.0f) && !currentlyWalking)
    {
        result.updateYaw = true;
        result.yawRadians = proposedYaw;
        return result;
    }

    result.action = IdleBehaviorAction::Wander;
    result.updateYaw = true;
    result.yawRadians = proposedYaw;
    result.moveDirectionX = std::cos(proposedYaw);
    result.moveDirectionY = std::sin(proposedYaw);
    const float weightedDistance = std::max(std::abs(deltaHomeX), std::abs(deltaHomeY))
        + 0.5f * std::min(std::abs(deltaHomeX), std::abs(deltaHomeY))
        + static_cast<float>(decisionSeed % 16u) * (wanderRadius / 16.0f);
    result.actionSeconds = moveSpeed > 0.0f ? std::max(0.25f, weightedDistance / (4.0f * moveSpeed)) : 0.0f;
    result.idleDecisionSeconds = 0.0f;

    if (result.actionSeconds <= 0.0f)
    {
        result = idleStandBehavior(actorChoosesBored(actorId, idleDecisionCount));
        result.nextDecisionCount = idleDecisionCount + 1;
        result.updateYaw = true;
        result.yawRadians = proposedYaw;
    }

    return result;
}

// The damage dice of an attack. An MM9 monster's loop rolls them seeded (damageSeed: its actor and attack count, so
// the AI stays a pure function of its facts and the world's seeded hit roll, which reads the damage, follows); every
// other monster keeps the thread's free generator.
int rollAttackDamage(const AttackDamageProfile &profile, std::optional<uint32_t> damageSeed)
{
    if (damageSeed)
    {
        std::mt19937 seeded(*damageSeed);
        return GameMechanics::rollMonsterAttackDamage(profile.diceRolls, profile.diceSides, profile.bonus, seeded);
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    return GameMechanics::rollMonsterAttackDamage(profile.diceRolls, profile.diceSides, profile.bonus, rng);
}

int resolveBaseAttackImpactDamage(
    GameplayActorAttackAbility ability,
    int monsterLevel,
    const AttackDamageProfile &attack1Damage,
    const AttackDamageProfile &attack2Damage,
    std::optional<uint32_t> damageSeed)
{
    const int fallbackSpellDamage = std::max(2, monsterLevel);

    switch (ability)
    {
        case GameplayActorAttackAbility::Attack2:
            return rollAttackDamage(attack2Damage, damageSeed);
        case GameplayActorAttackAbility::Spell1:
        case GameplayActorAttackAbility::Spell2:
            return fallbackSpellDamage;
        case GameplayActorAttackAbility::Attack1:
        default:
            return rollAttackDamage(attack1Damage, damageSeed);
    }
}

AttackStartOutcome startAttack(
    uint32_t actorId,
    uint32_t attackDecisionCount,
    bool abilityIsRanged,
    float attackAnimationSeconds,
    float recoverySeconds)
{
    AttackStartOutcome result = {};

    result.actionSeconds = std::max(0.1f, attackAnimationSeconds);
    result.attackCooldownSeconds =
        abilityIsRanged
        ? recoverySeconds + result.actionSeconds
        : recoverySeconds;
    result.attackCooldownSeconds *= actorDecisionRange(
        actorId,
        attackDecisionCount,
        0x0b91f2a3u,
        0.9f,
        1.2f);

    if (!abilityIsRanged && result.attackCooldownSeconds <= result.actionSeconds)
    {
        // TODO: revisit this once actor action length and monster recovery are modelled as OE-style separate timers.
        result.attackCooldownSeconds = result.actionSeconds + 0.25f;
    }

    return result;
}

AttackImpactOutcome finishAttackImpact(
    GameplayActorAttackAbility ability,
    int monsterLevel,
    const AttackDamageProfile &attack1Damage,
    const AttackDamageProfile &attack2Damage,
    bool abilityIsRanged,
    bool abilityIsMelee,
    bool targetIsParty,
    bool targetIsActor,
    bool shrinkActive,
    float shrinkDamageMultiplier,
    bool darkGraspActive,
    int damageBonus,
    std::optional<uint32_t> damageSeed)
{
    AttackImpactOutcome result = {};
    result.damage = resolveBaseAttackImpactDamage(ability, monsterLevel, attack1Damage, attack2Damage, damageSeed)
        + std::max(0, damageBonus);

    if (shrinkActive)
    {
        const int shrinkDivisor =
            shrinkDamageMultiplier > 0.0f
                ? std::max(1, static_cast<int>(std::lround(1.0f / shrinkDamageMultiplier)))
                : 1;
        result.damage /= shrinkDivisor;
    }

    if (darkGraspActive && abilityIsMelee)
    {
        result.damage /= 2;
    }

    if (abilityIsRanged)
    {
        result.action = AttackImpactAction::RangedRelease;
        return result;
    }

    if (targetIsParty)
    {
        result.action = AttackImpactAction::PartyMeleeImpact;
    }
    else if (targetIsActor)
    {
        result.action = AttackImpactAction::ActorMeleeImpact;
    }

    return result;
}

bool attackAbilityIsRanged(
    GameplayActorAttackAbility ability,
    const GameplayActorAttackConstraintState &constraints)
{
    switch (ability)
    {
        case GameplayActorAttackAbility::Attack1:
            return constraints.attack1IsRanged;
        case GameplayActorAttackAbility::Attack2:
            return constraints.attack2IsRanged;
        case GameplayActorAttackAbility::Spell1:
        case GameplayActorAttackAbility::Spell2:
            return true;
    }

    return false;
}

bool attackAbilityIsSpell(GameplayActorAttackAbility ability)
{
    return ability == GameplayActorAttackAbility::Spell1 || ability == GameplayActorAttackAbility::Spell2;
}

float monsterBuffDurationHours(float hours)
{
    return hours * 3600.0f;
}

float monsterBuffDurationMinutes(float minutes)
{
    return minutes * 60.0f;
}

float monsterSelfBuffDurationSeconds(
    const std::string &spellName,
    uint32_t skillLevel,
    SkillMastery skillMastery)
{
    const float level = static_cast<float>(std::max<uint32_t>(1, skillLevel));

    if (spellName == "haste")
    {
        if (skillMastery == SkillMastery::Grandmaster)
        {
            return monsterBuffDurationMinutes(45.0f + 3.0f * level);
        }

        if (skillMastery == SkillMastery::Master)
        {
            return monsterBuffDurationMinutes(40.0f + 2.0f * level);
        }

        return monsterBuffDurationHours(1.0f) + monsterBuffDurationMinutes(level);
    }

    if (spellName == "shield" || spellName == "stone skin" || spellName == "stoneskin")
    {
        if (skillMastery == SkillMastery::Grandmaster)
        {
            return monsterBuffDurationHours(64.0f + level);
        }

        if (skillMastery == SkillMastery::Master)
        {
            return monsterBuffDurationHours(1.0f) + monsterBuffDurationMinutes(4.0f + 15.0f * level);
        }

        return monsterBuffDurationHours(1.0f) + monsterBuffDurationMinutes(4.0f + 5.0f * level);
    }

    if (spellName == "bless" || spellName == "heroism")
    {
        if (skillMastery == SkillMastery::Grandmaster)
        {
            return monsterBuffDurationHours(1.0f) + monsterBuffDurationMinutes(4.0f + 20.0f * level);
        }

        if (skillMastery == SkillMastery::Master)
        {
            return monsterBuffDurationHours(1.0f) + monsterBuffDurationMinutes(4.0f + 15.0f * level);
        }

        return monsterBuffDurationHours(1.0f) + monsterBuffDurationMinutes(4.0f + 5.0f * level);
    }

    if (spellName == "fate")
    {
        return monsterBuffDurationMinutes(5.0f);
    }

    if (spellName == "hammerhands")
    {
        return monsterBuffDurationHours(level);
    }

    if (spellName == "day of protection" || spellName == "hour of power")
    {
        if (skillMastery == SkillMastery::Grandmaster)
        {
            return monsterBuffDurationMinutes(64.0f + 20.0f * level);
        }

        if (skillMastery == SkillMastery::Master)
        {
            return monsterBuffDurationMinutes(64.0f + 15.0f * level);
        }

        return monsterBuffDurationMinutes(64.0f + 5.0f * level);
    }

    if (spellName == "pain reflection")
    {
        if (skillMastery == SkillMastery::Grandmaster)
        {
            return monsterBuffDurationMinutes(64.0f) + 450.0f * level;
        }

        return monsterBuffDurationMinutes(64.0f) + 150.0f * level;
    }

    return monsterBuffDurationMinutes(5.0f);
}

float *monsterSelfBuffTimer(GameplayActorSpellEffectState &state, const std::string &spellName)
{
    if (spellName == "day of protection")
    {
        return &state.dayOfProtectionRemainingSeconds;
    }

    if (spellName == "hour of power")
    {
        return &state.hourOfPowerRemainingSeconds;
    }

    if (spellName == "pain reflection")
    {
        return &state.painReflectionRemainingSeconds;
    }

    if (spellName == "hammerhands")
    {
        return &state.hammerhandsRemainingSeconds;
    }

    if (spellName == "haste")
    {
        return &state.hasteRemainingSeconds;
    }

    if (spellName == "shield")
    {
        return &state.shieldRemainingSeconds;
    }

    if (spellName == "stone skin" || spellName == "stoneskin")
    {
        return &state.stoneskinRemainingSeconds;
    }

    if (spellName == "bless")
    {
        return &state.blessRemainingSeconds;
    }

    if (spellName == "fate")
    {
        return &state.fateRemainingSeconds;
    }

    if (spellName == "heroism")
    {
        return &state.heroismRemainingSeconds;
    }

    return nullptr;
}

const float *monsterSelfBuffTimer(const GameplayActorSpellEffectState &state, const std::string &spellName)
{
    if (spellName == "day of protection")
    {
        return &state.dayOfProtectionRemainingSeconds;
    }

    if (spellName == "hour of power")
    {
        return &state.hourOfPowerRemainingSeconds;
    }

    if (spellName == "pain reflection")
    {
        return &state.painReflectionRemainingSeconds;
    }

    if (spellName == "hammerhands")
    {
        return &state.hammerhandsRemainingSeconds;
    }

    if (spellName == "haste")
    {
        return &state.hasteRemainingSeconds;
    }

    if (spellName == "shield")
    {
        return &state.shieldRemainingSeconds;
    }

    if (spellName == "stone skin" || spellName == "stoneskin")
    {
        return &state.stoneskinRemainingSeconds;
    }

    if (spellName == "bless")
    {
        return &state.blessRemainingSeconds;
    }

    if (spellName == "fate")
    {
        return &state.fateRemainingSeconds;
    }

    if (spellName == "heroism")
    {
        return &state.heroismRemainingSeconds;
    }

    return nullptr;
}

bool monsterSpellIsOkToCast(
    const std::string &spellName,
    const ActorStatsFacts &stats,
    const ActorStatusFacts &status,
    const ActorPartyFacts &party)
{
    if (spellName.empty())
    {
        return false;
    }

    if (spellName == "heal" || spellName == "power cure")
    {
        return stats.currentHp < stats.maxHp;
    }

    if (spellName == "dispel magic")
    {
        return party.hasDispellableBuffs;
    }

    const float *pSelfBuffTimer = monsterSelfBuffTimer(status.spellEffects, spellName);

    if (pSelfBuffTimer != nullptr)
    {
        return *pSelfBuffTimer <= 0.0f;
    }

    return true;
}

int monsterSelfBuffPower(
    const std::string &spellName,
    uint32_t skillLevel,
    SkillMastery skillMastery)
{
    const int level = static_cast<int>(std::max<uint32_t>(1, skillLevel));

    if (spellName == "day of protection")
    {
        return skillMastery == SkillMastery::Master ? 4 * level : 5 * level;
    }

    // Monster spell names are the lowercased table names ("stone skin"); "stoneskin" is the old spelling.
    if (spellName == "hour of power"
        || spellName == "stone skin"
        || spellName == "stoneskin"
        || spellName == "bless"
        || spellName == "heroism")
    {
        return level + 5;
    }

    if (spellName == "fate")
    {
        if (skillMastery == SkillMastery::Grandmaster)
        {
            return 120 + 6 * level;
        }

        if (skillMastery == SkillMastery::Master)
        {
            return 60 + 3 * level;
        }

        return 40 + 2 * level;
    }

    if (spellName == "hammerhands")
    {
        return level;
    }

    return 0;
}

void setMonsterSelfBuffPower(
    GameplayActorSpellEffectState &state,
    const std::string &spellName,
    int power)
{
    if (spellName == "day of protection")
    {
        state.dayOfProtectionPower = std::max(state.dayOfProtectionPower, power);
    }
    else if (spellName == "hour of power")
    {
        state.hourOfPowerPower = std::max(state.hourOfPowerPower, power);
    }
    else if (spellName == "hammerhands")
    {
        state.hammerhandsPower = std::max(state.hammerhandsPower, power);
    }
    else if (spellName == "stone skin" || spellName == "stoneskin")
    {
        state.stoneskinPower = std::max(state.stoneskinPower, power);
    }
    else if (spellName == "bless")
    {
        state.blessPower = std::max(state.blessPower, power);
    }
    else if (spellName == "fate")
    {
        state.fatePower = std::max(state.fatePower, power);
    }
    else if (spellName == "heroism")
    {
        state.heroismPower = std::max(state.heroismPower, power);
    }
}

int monsterSelfHealAmount(
    const std::string &spellName,
    uint32_t skillLevel,
    SkillMastery skillMastery)
{
    const int level = static_cast<int>(std::max<uint32_t>(1, skillLevel));

    if (spellName == "power cure")
    {
        return 10 + 5 * level;
    }

    if (spellName == "heal")
    {
        if (skillMastery == SkillMastery::Grandmaster)
        {
            return 5 + 5 * level;
        }

        if (skillMastery == SkillMastery::Master)
        {
            return 5 + 4 * level;
        }

        if (skillMastery == SkillMastery::Expert)
        {
            return 5 + 3 * level;
        }

        return 5 + 2 * level;
    }

    return 0;
}

bool applyMonsterSelfHealSpell(
    GameplayActorAttackAbility ability,
    const ActorStatsFacts &stats,
    int &nextCurrentHp)
{
    const std::string &spellName =
        ability == GameplayActorAttackAbility::Spell1
            ? stats.spell1Name
            : ability == GameplayActorAttackAbility::Spell2 ? stats.spell2Name : std::string();

    if (spellName != "heal" && spellName != "power cure")
    {
        return false;
    }

    const uint32_t skillLevel =
        ability == GameplayActorAttackAbility::Spell1 ? stats.spell1SkillLevel : stats.spell2SkillLevel;
    const SkillMastery skillMastery =
        ability == GameplayActorAttackAbility::Spell1 ? stats.spell1SkillMastery : stats.spell2SkillMastery;
    const int healAmount = monsterSelfHealAmount(spellName, skillLevel, skillMastery);
    nextCurrentHp = std::clamp(stats.currentHp + healAmount, 0, std::max(1, stats.maxHp));
    return nextCurrentHp > stats.currentHp;
}

bool applyMonsterSelfBuffSpell(
    GameplayActorAttackAbility ability,
    const ActorStatsFacts &stats,
    GameplayActorSpellEffectState &nextEffects)
{
    const std::string &spellName =
        ability == GameplayActorAttackAbility::Spell1
            ? stats.spell1Name
            : ability == GameplayActorAttackAbility::Spell2 ? stats.spell2Name : std::string();
    float *pTimer = monsterSelfBuffTimer(nextEffects, spellName);

    if (pTimer == nullptr)
    {
        return false;
    }

    const uint32_t skillLevel =
        ability == GameplayActorAttackAbility::Spell1 ? stats.spell1SkillLevel : stats.spell2SkillLevel;
    const SkillMastery skillMastery =
        ability == GameplayActorAttackAbility::Spell1 ? stats.spell1SkillMastery : stats.spell2SkillMastery;
    *pTimer = std::max(
        *pTimer,
        monsterSelfBuffDurationSeconds(spellName, skillLevel, skillMastery));
    setMonsterSelfBuffPower(nextEffects, spellName, monsterSelfBuffPower(spellName, skillLevel, skillMastery));
    return true;
}

GameplayActorAttackAbility fallbackMeleeAttackAbility(
    GameplayActorAttackAbility chosenAbility,
    const GameplayActorAttackConstraintState &constraints,
    int attack2Chance)
{
    if (chosenAbility == GameplayActorAttackAbility::Attack1 && !constraints.attack1IsRanged)
    {
        return chosenAbility;
    }

    if (!constraints.attack1IsRanged)
    {
        return GameplayActorAttackAbility::Attack1;
    }

    if (attack2Chance > 0 && !constraints.attack2IsRanged)
    {
        return GameplayActorAttackAbility::Attack2;
    }

    return chosenAbility;
}

float meleeRangeForCombatTarget(bool targetIsActor)
{
    return targetIsActor ? ActorMeleeRange * 0.5f : ActorMeleeRange;
}

// An MM9 monster on its own loop (MM9_MONSTER_AI_PLAN.md phases 2 and 3: walkers, fliers, turrets): its profile, null
// for every other actor (MM6-MM8 monsters keep the native AI).
const Mm9AiProfile *mm9LoopProfile(const ActorAiFacts &actor)
{
    return actor.tactics.mm9Profile && mm9LoopArchetype(*actor.tactics.mm9Profile) ? &*actor.tactics.mm9Profile
        : nullptr;
}

// An MM9 walker (crawler, skirmisher, ranged holder or swimmer, phase 2): its profile, null for every other actor.
const Mm9AiProfile *mm9WalkerProfile(const ActorAiFacts &actor)
{
    const Mm9AiProfile *pProfile = mm9LoopProfile(actor);
    return pProfile != nullptr && mm9WalkerArchetype(pProfile->archetype) ? pProfile : nullptr;
}

// MM9's loops run in real time only; turn-based combat keeps the native turns.
bool mm9LoopActive(const ActorAiFacts &actor, const ActorAiFrameFacts *pFrame)
{
    return pFrame != nullptr && pFrame->turnBased.mode == ActorTurnBasedMode::RealTime
        && mm9LoopProfile(actor) != nullptr;
}

bool mm9WalkerLoopActive(const ActorAiFacts &actor, const ActorAiFrameFacts *pFrame)
{
    return mm9LoopActive(actor, pFrame) && mm9WalkerProfile(actor) != nullptr;
}

bool mm9FlierLoopActive(const ActorAiFacts &actor, const ActorAiFrameFacts *pFrame)
{
    return mm9LoopActive(actor, pFrame) && actor.tactics.mm9Profile->archetype == Mm9AiArchetype::Flier;
}

bool mm9TurretLoopActive(const ActorAiFacts &actor, const ActorAiFrameFacts *pFrame)
{
    return mm9LoopActive(actor, pFrame) && actor.tactics.mm9Profile->archetype == Mm9AiArchetype::Turret;
}

// The edge distance from which its melee reaches its current target: an MM9 monster's own attack reach, else the
// native constant (halved against actors).
float meleeRangeForTarget(const ActorAiFacts &actor, const ActorAiFrameFacts *pFrame)
{
    const bool targetIsActor = actor.target.currentKind == ActorAiTargetKind::Actor;
    const Mm9AiProfile *pProfile = mm9LoopProfile(actor);

    if (pProfile != nullptr && pProfile->attackReach > 0.0f)
    {
        return mm9MeleeReach(pProfile->attackReach, targetIsActor, pFrame != nullptr ? pFrame->party.collisionRadius
            : 0.0f);
    }

    return meleeRangeForCombatTarget(targetIsActor);
}

GameplayActorAttackChoiceResult chooseAttackAbility(
    uint32_t actorId,
    uint32_t attackDecisionCount,
    bool hasSpell1,
    bool spell1IsOkToCast,
    int spell1UseChance,
    bool hasSpell2,
    bool spell2IsOkToCast,
    int spell2UseChance,
    int attack2Chance)
{
    GameplayActorAttackChoiceResult result = {};
    result.nextDecisionCount = attackDecisionCount + 1;

    const uint32_t baseSeed = mixActorDecisionSeed(actorId, attackDecisionCount, 0x7f4a7c15u);

    auto passesChance =
        [&](int chance, uint32_t salt)
        {
            if (chance <= 0)
            {
                return false;
            }

            return ((baseSeed ^ salt) % 100u) < static_cast<uint32_t>(chance);
        };

    if (hasSpell1 && spell1IsOkToCast && passesChance(spell1UseChance, 0x13579bdfu))
    {
        result.ability = GameplayActorAttackAbility::Spell1;
        return result;
    }

    if (hasSpell2 && spell2IsOkToCast && passesChance(spell2UseChance, 0x2468ace0u))
    {
        result.ability = GameplayActorAttackAbility::Spell2;
        return result;
    }

    if (passesChance(attack2Chance, 0x55aa55aau))
    {
        result.ability = GameplayActorAttackAbility::Attack2;
        return result;
    }

    result.ability = GameplayActorAttackAbility::Attack1;
    return result;
}

GameplayActorAttackAbility resolveAttackAbilityConstraints(
    GameplayActorAttackAbility chosenAbility,
    const GameplayActorAttackConstraintState &constraints,
    int attack2Chance)
{
    if (!attackAbilityIsRanged(chosenAbility, constraints))
    {
        return chosenAbility;
    }

    if (constraints.blindActive || constraints.darkGraspActive || !constraints.rangedCommitAllowed)
    {
        return fallbackMeleeAttackAbility(chosenAbility, constraints, attack2Chance);
    }

    return chosenAbility;
}

bool shouldCommitToRangedAbility(const RangedAbilityCommitInput &input)
{
    if (!input.abilityIsRanged)
    {
        return false;
    }

    if (input.targetEdgeDistance >= input.rangedAttackReach)
    {
        return false;
    }

    if (!input.movementAllowed)
    {
        return true;
    }

    const float meleeRange = meleeRangeForCombatTarget(input.targetIsActor);

    if (input.targetEdgeDistance <= meleeRange * 1.15f)
    {
        return false;
    }

    const float gapBeyondMelee = std::max(0.0f, input.targetEdgeDistance - meleeRange);
    float chancePercent = 0.0f;

    if (gapBeyondMelee < 256.0f)
    {
        chancePercent = 15.0f;
    }
    else if (gapBeyondMelee < 640.0f)
    {
        chancePercent = 30.0f;
    }
    else if (gapBeyondMelee < 1280.0f)
    {
        chancePercent = 50.0f;
    }
    else if (gapBeyondMelee < 2560.0f)
    {
        chancePercent = 72.0f;
    }
    else if (gapBeyondMelee < 4096.0f)
    {
        chancePercent = 84.0f;
    }
    else
    {
        chancePercent = 68.0f;
    }

    if (attackAbilityIsSpell(input.ability))
    {
        chancePercent = std::min(95.0f, chancePercent + 10.0f);
    }

    const uint32_t salt =
        input.ability == GameplayActorAttackAbility::Attack2 ? 0x55aa55aau
        : input.ability == GameplayActorAttackAbility::Spell1 ? 0x13579bdfu
        : input.ability == GameplayActorAttackAbility::Spell2 ? 0x2468ace0u
        : 0x7f4a7c15u;
    const float rollPercent =
        actorDecisionUnitFloat(input.actorId, input.attackDecisionCount, salt ^ 0x31415926u) * 100.0f;
    return rollPercent < chancePercent;
}

CombatAbilityChoiceResult chooseCombatAbility(const CombatAbilityChoiceInput &input)
{
    CombatAbilityChoiceResult result = {};
    result.nextAttackDecisionCount = input.attackDecisionCount;

    GameplayActorAttackAbility chosenAbility = GameplayActorAttackAbility::Attack1;

    if (input.chooseRandomAbility)
    {
        const GameplayActorAttackChoiceResult attackChoice =
            chooseAttackAbility(
                input.actorId,
                input.attackDecisionCount,
                input.hasSpell1,
                input.spell1IsOkToCast,
                input.spell1UseChance,
                input.hasSpell2,
                input.spell2IsOkToCast,
                input.spell2UseChance,
                input.attack2Chance);
        result.nextAttackDecisionCount = attackChoice.nextDecisionCount;
        chosenAbility = attackChoice.ability;
    }

    GameplayActorAttackConstraintState constraintState = input.constraintState;

    if (!input.inMeleeRange && !attackAbilityIsRanged(chosenAbility, constraintState))
    {
        if (constraintState.attack1IsRanged)
        {
            chosenAbility = GameplayActorAttackAbility::Attack1;
        }
        else if (input.attack2Chance > 0 && constraintState.attack2IsRanged)
        {
            chosenAbility = GameplayActorAttackAbility::Attack2;
        }
    }

    // Out of reach blocks a ranged ability outright: a monster with no blow to fall back on (a Great Wyrm) would
    // otherwise keep its missile and shoot from as far as it senses the party.
    const bool hardRangedAbilityBlocked =
        input.constraintState.darkGraspActive
        || input.constraintState.blindActive
        || !input.constraintState.rangedCommitAllowed
        || (!input.forceRangedCommit && input.targetEdgeDistance >= input.rangedAttackReach);

    if (attackAbilityIsRanged(chosenAbility, constraintState))
    {
        RangedAbilityCommitInput rangedCommitInput = {};
        rangedCommitInput.actorId = input.actorId;
        rangedCommitInput.attackDecisionCount = result.nextAttackDecisionCount;
        rangedCommitInput.ability = chosenAbility;
        rangedCommitInput.abilityIsRanged = true;
        rangedCommitInput.movementAllowed = input.movementAllowed;
        rangedCommitInput.targetIsActor = input.targetIsActor;
        rangedCommitInput.targetEdgeDistance = input.targetEdgeDistance;
        rangedCommitInput.rangedAttackReach = input.rangedAttackReach;

        if (!input.forceRangedCommit && !shouldCommitToRangedAbility(rangedCommitInput))
        {
            constraintState.rangedCommitAllowed = false;
        }
    }

    if (input.applyAbilityConstraints)
    {
        chosenAbility = resolveAttackAbilityConstraints(chosenAbility, constraintState, input.attack2Chance);
    }

    const bool resolvedAbilityIsRanged = attackAbilityIsRanged(chosenAbility, constraintState);
    result.ability = chosenAbility;
    result.abilityIsRanged =
        resolvedAbilityIsRanged
        && !hardRangedAbilityBlocked;
    result.abilityIsMelee = !resolvedAbilityIsRanged;
    result.stationaryOrTooCloseForRangedPursuit =
        result.abilityIsRanged
        && (!input.movementAllowed || input.inMeleeRange);
    return result;
}

ActorAiAnimationState attackAnimationStateForAbility(
    GameplayActorAttackAbility ability,
    const GameplayActorAttackConstraintState &constraints)
{
    return attackAbilityIsRanged(ability, constraints)
        ? ActorAiAnimationState::AttackRanged
        : ActorAiAnimationState::AttackMelee;
}

// A spell uses its own timing (the model's cast clip) where the world gives one, else the ranged attack's.
bool spellHasOwnTiming(const ActorAiFacts &actor, GameplayActorAttackAbility ability)
{
    return attackAbilityIsSpell(ability) && actor.runtime.spellAttackAnimationSeconds > 0.0f;
}

float attackAnimationSecondsForAbility(
    const ActorAiFacts &actor,
    GameplayActorAttackAbility ability,
    const GameplayActorAttackConstraintState &constraints)
{
    if (spellHasOwnTiming(actor, ability))
    {
        return actor.runtime.spellAttackAnimationSeconds;
    }

    return attackAbilityIsRanged(ability, constraints)
        ? actor.runtime.rangedAttackAnimationSeconds
        : actor.runtime.meleeAttackAnimationSeconds;
}

// Action time left when the attack applies. MM8 applies every attack when its sprite animation has played
// (re_mm8/ACTOR_ATTACK_TIMING.md); an attack sprite with an authored contact frame applies it as that frame appears
// and the action runs on to the end of the animation.
float attackImpactLeadSecondsForAbility(
    const ActorAiFacts &actor,
    GameplayActorAttackAbility ability,
    const GameplayActorAttackConstraintState &constraints)
{
    const float impactSeconds = spellHasOwnTiming(actor, ability) ? actor.runtime.spellAttackImpactSeconds
        : attackAbilityIsRanged(ability, constraints) ? actor.runtime.rangedAttackImpactSeconds
        : actor.runtime.meleeAttackImpactSeconds;
    return actorAttackImpactLeadSeconds(attackAnimationSecondsForAbility(actor, ability, constraints), impactSeconds);
}

// Action time left when the attack sound plays: the whole action (as the attack starts) without an authored delay.
float attackSoundLeadSecondsForAbility(
    const ActorAiFacts &actor,
    GameplayActorAttackAbility ability,
    const GameplayActorAttackConstraintState &constraints)
{
    const float delaySeconds = attackAbilityIsRanged(ability, constraints)
        ? actor.runtime.rangedAttackSoundDelaySeconds
        : actor.runtime.meleeAttackSoundDelaySeconds;
    const float actionSeconds = std::max(0.1f, attackAnimationSecondsForAbility(actor, ability, constraints));
    return actionSeconds - std::clamp(delaySeconds, 0.0f, actionSeconds);
}

ActorTargetState buildActorTargetStateFromFacts(const ActorAiFacts &actor)
{
    ActorTargetState target = {};
    target.kind = actor.target.currentKind;
    target.actorIndex = actor.target.currentActorIndex;
    target.relationToTarget = actor.target.currentRelationToTarget;
    target.targetX = actor.target.currentPosition.x;
    target.targetY = actor.target.currentPosition.y;
    target.targetZ = actor.target.currentPosition.z;
    target.deltaX = target.targetX - actor.movement.position.x;
    target.deltaY = target.targetY - actor.movement.position.y;
    target.deltaZ = target.targetZ - actor.world.targetZ;
    target.horizontalDistanceToTarget = std::sqrt(target.deltaX * target.deltaX + target.deltaY * target.deltaY);
    target.distanceToTarget = actor.target.currentDistance;
    target.edgeDistance = actor.target.currentEdgeDistance;
    target.canSense = actor.target.currentCanSense;
    target.attackLineOfSight = actor.target.currentHasAttackLineOfSight;
    target.partyCanSense = actor.target.partyCanSenseActor;

    return target;
}

GameplayWorldPoint actorMovementTargetPosition(const ActorAiFacts &actor)
{
    return actor.target.hasCurrentMovementPosition
        ? actor.target.currentMovementPosition
        : actor.target.currentPosition;
}

bool friendlyTargetShouldPromoteHostility(
    const GameplayActorService &actorService,
    const GameplayActorTargetPolicyState &actor,
    uint8_t hostilityType,
    int relationToTarget,
    float targetDistanceSquared,
    float &promotionRange)
{
    promotionRange = -1.0f;

    if (hostilityType != 0 || actorService.isPartyControlledActor(actor.controlMode))
    {
        return false;
    }

    promotionRange = actorService.hostilityPromotionRangeForFriendlyActor(relationToTarget);
    return relationToTarget == 1
        || (promotionRange >= 0.0f && targetDistanceSquared <= promotionRange * promotionRange);
}

bool resolvePartyProximity(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const GameplayActorService &actorService)
{
    return actorService.partyIsVeryNearActor(
        actor.movement.distanceToParty,
        frame.party.position.z - actor.movement.position.z,
        actor.stats.radius,
        actor.stats.height,
        frame.party.collisionRadius);
}

ActorEngagementState resolveActorEngagement(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const GameplayActorService &actorService)
{
    const bool partyIsVeryNearActor = resolvePartyProximity(actor, frame, actorService);
    const ActorTargetState combatTarget = buildActorTargetStateFromFacts(actor);

    ActorEngagementState result = {};
    result.hostilityType = actor.identity.hostilityType;
    result.hasDetectedParty = actor.status.hasDetectedParty;
    result.hasCombatTarget = combatTarget.kind != ActorAiTargetKind::None;
    result.targetIsParty = combatTarget.kind == ActorAiTargetKind::Party;
    result.targetIsActor = combatTarget.kind == ActorAiTargetKind::Actor;
    const bool invisiblePartyTarget = result.targetIsParty && frame.party.invisible;
    result.shouldEngageTarget = result.hasCombatTarget && combatTarget.canSense && !invisiblePartyTarget;
    result.inMeleeRange =
        combatTarget.edgeDistance <= meleeRangeForTarget(actor, &frame)
        && combatTarget.attackLineOfSight
        && (!result.targetIsParty || GameplayActorService::meleeReachesVertically(frame.meleeVerticalReach,
            actor.movement.position.z, float(actor.stats.height), frame.party.position.z, frame.party.collisionHeight));

    if (result.targetIsActor)
    {
        const bool shouldPromoteHostility = friendlyTargetShouldPromoteHostility(
            actorService,
            actor.identity.targetPolicy,
            actor.identity.hostilityType,
            combatTarget.relationToTarget,
            lengthSquared3d(combatTarget.deltaX, combatTarget.deltaY, combatTarget.deltaZ),
            result.promotionRange);
        result.shouldPromoteHostility = shouldPromoteHostility;

        if (shouldPromoteHostility)
        {
            result.hostilityType = 4;
            result.shouldUpdateHostilityType = result.hostilityType != actor.identity.hostilityType;
        }
        else if (actor.identity.hostilityType == 0
            && !actorService.isPartyControlledActor(actor.identity.targetPolicy.controlMode))
        {
            result.shouldEngageTarget = false;
        }
    }

    if (invisiblePartyTarget)
    {
        result.hasDetectedParty = false;
    }
    else if (result.targetIsParty && !actor.status.hasDetectedParty)
    {
        result.hasDetectedParty = true;
    }
    else if (!result.targetIsParty || !combatTarget.partyCanSense)
    {
        result.hasDetectedParty = false;
    }

    // An MM9 walker flees only by MM9's ShouldRunAway (its loop starts a flight: ActorMm9State::fleeMode, moved by
    // AI_Mm9Flee); fliers and turrets never start one.
    if (mm9LoopActive(actor, &frame))
    {
        result.shouldFlee = actor.status.forceFleeFromParty;
    }
    else
    {
        result.shouldFlee = actor.status.forceFleeFromParty
            || (result.shouldEngageTarget
                && combatTarget.distanceToTarget <= HostilityLongRange
                && actorService.shouldFleeForAiType(actor.stats.aiType, actor.stats.currentHp, actor.stats.maxHp)
                && !(actor.status.suppressLowHealthFlee && actor.stats.aiType != GameplayActorAiType::Wimp));
    }
    result.friendlyNearParty =
        !result.shouldEngageTarget
        && !actor.status.hostileToParty
        && !actorService.isPartyControlledActor(actor.identity.targetPolicy.controlMode)
        && partyIsVeryNearActor;
    return result;
}

bool hasActiveSpellEffectTimer(const GameplayActorSpellEffectState &state)
{
    return state.slowRemainingSeconds > 0.0f
        || state.stunRemainingSeconds > 0.0f
        || state.paralyzeRemainingSeconds > 0.0f
        || state.fearRemainingSeconds > 0.0f
        || state.blindRemainingSeconds > 0.0f
        || state.controlRemainingSeconds > 0.0f
        || state.shrinkRemainingSeconds > 0.0f
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
        || state.heroismRemainingSeconds > 0.0f;
}

class ActorAiCommandContext
{
public:
    explicit ActorAiCommandContext(const ActorAiFacts &actor)
        : m_pActor(&actor)
    {
        m_update.actorIndex = actor.actorIndex;
    }

    ActorAiCommandContext(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
        : ActorAiCommandContext(actor)
    {
        m_pFrame = &frame;
    }

    const ActorAiFacts &actor() const
    {
        return *m_pActor;
    }

    const ActorAiFrameFacts *frame() const
    {
        return m_pFrame;
    }

    ActorAiUpdate &update()
    {
        return m_update;
    }

    // Records the decision taken this step for the decision trace (a later one in the same step replaces it).
    ActorAiDecision &decide(ActorAiDecisionKind kind, const char *pNote = nullptr, float chance = -1.0f,
        float roll = -1.0f)
    {
        ActorAiDecision decision = {};
        decision.kind = kind;
        decision.targetKind = m_pActor->target.currentKind;
        decision.targetActorIndex = m_pActor->target.currentActorIndex;
        decision.chance = chance;
        decision.roll = roll;
        decision.pNote = pNote;
        m_update.state.decision = decision;
        return *m_update.state.decision;
    }

    void setMotionState(ActorAiMotionState motionState)
    {
        m_update.state.motionState = motionState;
    }

    void setAnimationState(ActorAiAnimationState animationState)
    {
        m_update.animation.animationState = animationState;
    }

    void setActionSeconds(float actionSeconds)
    {
        m_update.state.actionSeconds = actionSeconds;
    }

    void setRecoverySeconds(float recoverySeconds)
    {
        m_update.state.recoverySeconds = recoverySeconds;
    }

    void setAttackCooldownSeconds(float attackCooldownSeconds)
    {
        m_update.state.attackCooldownSeconds = attackCooldownSeconds;
    }

    void setAttackDecisionCount(uint32_t attackDecisionCount)
    {
        m_update.state.attackDecisionCount = attackDecisionCount;
    }

    void setPursueDecisionCount(uint32_t pursueDecisionCount)
    {
        m_update.state.pursueDecisionCount = pursueDecisionCount;
    }

    void setCrowdSideLockRemainingSeconds(float seconds)
    {
        m_update.state.crowdSideLockRemainingSeconds = seconds;
    }

    void setCrowdNoProgressSeconds(float seconds)
    {
        m_update.state.crowdNoProgressSeconds = seconds;
    }

    void setCrowdLastEdgeDistance(float distance)
    {
        m_update.state.crowdLastEdgeDistance = distance;
    }

    void setCrowdRetreatRemainingSeconds(float seconds)
    {
        m_update.state.crowdRetreatRemainingSeconds = seconds;
    }

    void setCrowdStandRemainingSeconds(float seconds)
    {
        m_update.state.crowdStandRemainingSeconds = seconds;
    }

    void setCrowdProbeEdgeDistance(float distance)
    {
        m_update.state.crowdProbeEdgeDistance = distance;
    }

    void setCrowdProbeElapsedSeconds(float seconds)
    {
        m_update.state.crowdProbeElapsedSeconds = seconds;
    }

    void setCrowdEscapeAttempts(uint8_t attempts)
    {
        m_update.state.crowdEscapeAttempts = attempts;
    }

    void setCrowdSideSign(int8_t sideSign)
    {
        m_update.state.crowdSideSign = sideSign;
    }

    void setQueuedAttackAbility(GameplayActorAttackAbility ability)
    {
        m_update.state.queuedAttackAbility = ability;
    }

    void setDead(bool dead)
    {
        m_update.state.dead = dead;
    }

    void setSpellEffects(const GameplayActorSpellEffectState &spellEffects)
    {
        m_update.state.spellEffects = spellEffects;
    }

    void setAttackImpactTriggered(bool triggered)
    {
        m_update.state.attackImpactTriggered = triggered;
    }

    void setIdleDecisionSeconds(float idleDecisionSeconds)
    {
        m_update.state.idleDecisionSeconds = idleDecisionSeconds;
    }

    void setIdleDecisionCount(uint32_t idleDecisionCount)
    {
        m_update.state.idleDecisionCount = idleDecisionCount;
    }

    void setAnimationTimeTicks(float animationTimeTicks)
    {
        m_update.animation.animationTimeTicks = animationTimeTicks;
    }

    void resetAnimationTime()
    {
        m_update.animation.resetAnimationTime = true;
    }

    void resetAnimationOnChange()
    {
        m_update.animation.resetOnAnimationChange = true;
    }

    void setMeleePursuitActive(bool active)
    {
        m_update.movementIntent.meleePursuitActive = active;
    }

    void resetCrowdSteering()
    {
        m_update.movementIntent.resetCrowdSteering = true;
    }

    void updateCrowdProbePosition()
    {
        m_update.movementIntent.updateCrowdProbePosition = true;
    }

    void faceYaw(float yawRadians)
    {
        m_update.movementIntent.updateYaw = true;
        m_update.movementIntent.yawRadians = yawRadians;
    }

    void setMovementAction(ActorAiMovementAction action)
    {
        m_update.movementIntent.action = action;
    }

    void setMoveDirection(float moveDirectionX, float moveDirectionY)
    {
        m_update.movementIntent.moveDirectionX = moveDirectionX;
        m_update.movementIntent.moveDirectionY = moveDirectionY;
    }

    void setDesiredMovement(float desiredMoveX, float desiredMoveY)
    {
        m_update.movementIntent.desiredMoveX = desiredMoveX;
        m_update.movementIntent.desiredMoveY = desiredMoveY;
        m_update.movementIntent.applyMovement = true;
    }

    void clearMovementDirection()
    {
        setMoveDirection(0.0f, 0.0f);
    }

    void clearVelocity()
    {
        m_update.movementIntent.clearVelocity = true;
    }

    void requestAttack(const ActorAttackRequest &request)
    {
        m_update.attackRequest = request;
    }

    void requestProjectileAttack(const ActorAttackRequest &request)
    {
        requestAttack(request);
    }

    void requestAudio(const ActorAudioRequest &request)
    {
        m_update.audioRequests.push_back(request);
    }

    void requestFx(const ActorFxRequest &request)
    {
        m_update.fxRequests.push_back(request);
    }

    ActorAiUpdate finish()
    {
        return m_update;
    }

    void replaceUpdate(const ActorAiUpdate &update)
    {
        m_update = update;
    }

private:
    const ActorAiFacts *m_pActor = nullptr;
    const ActorAiFrameFacts *m_pFrame = nullptr;
    ActorAiUpdate m_update = {};
};

ActorAiUpdate makeActorUpdate(const ActorAiFacts &actor)
{
    ActorAiCommandContext ai(actor);
    return ai.finish();
}

struct ActorFrameTimerAging
{
    float idleDecisionSeconds = 0.0f;
    float attackCooldownSeconds = 0.0f;
    float actionSeconds = 0.0f;
    float crowdSideLockRemainingSeconds = 0.0f;
    float crowdRetreatRemainingSeconds = 0.0f;
    float crowdStandRemainingSeconds = 0.0f;
    float skirmishSeconds = 0.0f;
};

struct ActorMovementCommit
{
    bool resetCrowdSteering = false;
    bool clearVelocity = true;
    bool applyMovement = false;
};

struct ActorMovementBlockOutcome
{
    bool zeroVelocity = false;
    bool resetMoveDirection = false;
    bool stand = false;
    bool crowdStand = false;
    bool fleeFromContact = false;
    bool faceContact = false;
    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    float yawRadians = 0.0f;
    float actionSeconds = 0.0f;
};

float contactFleeActionSeconds(const ActorAiFacts &actor, float contactDistance)
{
    if (actor.movement.effectiveMoveSpeed <= 0.01f || contactDistance <= 0.01f)
    {
        return ContactFleeFallbackSeconds;
    }

    const float actionSeconds = contactDistance / actor.movement.effectiveMoveSpeed;
    return std::clamp(actionSeconds, ContactFleeFallbackSeconds, 256.0f / ActorAiTicksPerSecond);
}

enum class ActorCombatFlowAction : uint8_t
{
    ContinueAttack = 0,
    BlindWander = 1,
    Flee = 2,
    EngageTarget = 3,
    FriendlyNearParty = 4,
    NonCombat = 5,
};

enum class ActorCombatFlowMotion : uint8_t
{
    Standing = 0,
    Attacking = 1,
    Wandering = 2,
    Fleeing = 3,
};

enum class ActorCombatFlowAnimation : uint8_t
{
    Standing = 0,
    Walking = 1,
    Current = 2,
};

struct ActorCombatFlowOutcome
{
    ActorCombatFlowMotion motion = ActorCombatFlowMotion::Standing;
    ActorCombatFlowAnimation animation = ActorCombatFlowAnimation::Standing;
    bool clearMoveDirection = false;
    bool clearVelocity = false;
    bool updateMoveDirection = false;
    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    bool updateDesiredMove = false;
    float desiredMoveX = 0.0f;
    float desiredMoveY = 0.0f;
    bool updateYaw = false;
    float yawRadians = 0.0f;
    float actionSeconds = 0.0f;
    float idleDecisionSeconds = 0.0f;
};

struct ActorAttackFrameState
{
    bool attackInProgress = false;
    bool impactDue = false;
};

enum class ActorDeathFrameAction : uint8_t
{
    Continue = 0,
    HoldDead = 1,
    MarkDead = 2,
    AdvanceDying = 3,
};

struct ActorDeathFrameOutcome
{
    ActorDeathFrameAction action = ActorDeathFrameAction::Continue;
    float actionSeconds = 0.0f;
    bool finishedDying = false;
};

enum class ActorStatusFrameAction : uint8_t
{
    Continue = 0,
    HoldStun = 1,
    RecoverFromStun = 2,
    HoldParalyze = 3,
    ForceStun = 4,
};

struct ActorStatusFrameOutcome
{
    ActorStatusFrameAction action = ActorStatusFrameAction::Continue;
    float actionSeconds = 0.0f;
};

ActorStatusFrameOutcome resolveActorStatusFrame(
    bool currentlyStunned,
    bool paralyzeActive,
    bool stunActive,
    float actionSeconds,
    float stunRemainingSeconds,
    float deltaSeconds)
{
    ActorStatusFrameOutcome result = {};
    result.actionSeconds = actionSeconds;

    if (currentlyStunned && !paralyzeActive)
    {
        result.actionSeconds = std::max(0.0f, actionSeconds - std::max(0.0f, deltaSeconds));
        result.action = result.actionSeconds <= 0.0f
            ? ActorStatusFrameAction::RecoverFromStun
            : ActorStatusFrameAction::HoldStun;
        return result;
    }

    if (paralyzeActive)
    {
        result.action = ActorStatusFrameAction::HoldParalyze;
        result.actionSeconds = 0.0f;
        return result;
    }

    if (stunActive)
    {
        result.action = ActorStatusFrameAction::ForceStun;
        result.actionSeconds = std::max(actionSeconds, stunRemainingSeconds);
        return result;
    }

    return result;
}

// The attack applies once the action has `impactLeadSeconds` or less to run: 0 applies it when the action ends.
ActorAttackFrameState buildActorAttackFrameState(
    bool attacking,
    bool impactTriggered,
    float actionSeconds,
    float impactLeadSeconds)
{
    ActorAttackFrameState result = {};

    if (!attacking)
    {
        return result;
    }

    result.attackInProgress = actionSeconds > 0.0f;
    result.impactDue = !impactTriggered && actionSeconds <= impactLeadSeconds;
    return result;
}

ActorDeathFrameOutcome resolveActorDeathFrame(
    bool dead,
    bool hpDepleted,
    bool dying,
    float actionSeconds,
    float deltaSeconds)
{
    ActorDeathFrameOutcome result = {};

    if (dead)
    {
        result.action = ActorDeathFrameAction::HoldDead;
        return result;
    }

    if (!hpDepleted && !dying)
    {
        return result;
    }

    if (!dying)
    {
        result.action = ActorDeathFrameAction::MarkDead;
        return result;
    }

    result.action = ActorDeathFrameAction::AdvanceDying;
    result.actionSeconds = std::max(0.0f, actionSeconds - std::max(0.0f, deltaSeconds));
    result.finishedDying = result.actionSeconds <= 0.0f;
    return result;
}

float actorAnimationTickDelta(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    if (actor.runtime.hitstopActive)
    {
        return 0.0f;
    }

    float tickScale = 1.0f;

    if (actor.runtime.animationState == ActorAiAnimationState::Walking
        && actor.status.spellEffects.slowRemainingSeconds > 0.0f)
    {
        tickScale = std::clamp(actor.status.spellEffects.slowMoveMultiplier, 0.125f, 1.0f);
    }

    return std::max(0.0f, frame.fixedStepSeconds * ActorAiTicksPerSecond) * tickScale;
}

ActorFrameTimerAging ageActorFrameTimers(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorFrameTimerAging result = {};
    const float deltaSeconds = std::max(0.0f, frame.fixedStepSeconds);
    const GameplayActorService actorService = {};
    const float recoveryStepSeconds =
        deltaSeconds * actorService.effectiveRecoveryProgressMultiplier(actor.status.spellEffects);
    const bool attacking = actor.runtime.motionState == ActorAiMotionState::Attacking;

    result.idleDecisionSeconds = std::max(0.0f, actor.runtime.idleDecisionSeconds - deltaSeconds);
    result.attackCooldownSeconds = std::max(0.0f,
        actor.runtime.attackCooldownSeconds - recoveryStepSeconds * actor.behavior.attackRateMultiplier);
    result.actionSeconds = std::max(
        0.0f,
        actor.runtime.actionSeconds - (attacking ? recoveryStepSeconds : deltaSeconds));
    result.crowdSideLockRemainingSeconds = std::max(
        0.0f,
        actor.runtime.crowdSideLockRemainingSeconds - deltaSeconds);
    result.crowdRetreatRemainingSeconds = std::max(
        0.0f,
        actor.runtime.crowdRetreatRemainingSeconds - deltaSeconds);
    result.crowdStandRemainingSeconds = std::max(
        0.0f,
        actor.runtime.crowdStandRemainingSeconds - deltaSeconds);
    result.skirmishSeconds = std::max(0.0f, actor.runtime.skirmishSeconds - deltaSeconds);
    return result;
}

ActorMovementCommit buildActiveMovementCommit(
    const ActorAiFacts &actor,
    const ActorAiUpdate &update,
    bool preserveCrowdSteering)
{
    ActorMovementCommit result = {};
    const GameplayWorldPoint movementTargetPosition = actorMovementTargetPosition(actor);
    const float verticalTargetDelta = movementTargetPosition.z - actor.world.targetZ;
    const bool flyingVerticalMove =
        actor.stats.canFly
        && std::abs(verticalTargetDelta) > 8.0f;

    result.resetCrowdSteering = !preserveCrowdSteering;
    result.applyMovement =
        actor.movement.movementAllowed
        && (std::abs(update.movementIntent.desiredMoveX) > 0.001f
            || std::abs(update.movementIntent.desiredMoveY) > 0.001f
            || flyingVerticalMove);
    return result;
}

ActorMovementBlockOutcome buildPostMovementBlock(const ActorAiFacts &actor)
{
    ActorMovementBlockOutcome result = {};

    // Only a skirmisher moves while it attacks (ActorTacticsFacts::skirmish): a bump or a wall stops that step, never
    // the attack.
    if (actor.runtime.motionState == ActorAiMotionState::Attacking)
    {
        result.zeroVelocity = actor.movement.contactedActorCount > 0
            || actor.movement.movementBlocked
            || actor.movement.movementSuppressedByNavigation;
        return result;
    }

    if (actor.movement.contactedActorCount > 1)
    {
        result.zeroVelocity = true;
        result.resetMoveDirection = true;
        result.stand = true;
        result.crowdStand = true;
        result.actionSeconds = std::max(actor.runtime.actionSeconds, CrowdNoProgressStandSeconds);
        return result;
    }

    if (actor.movement.contactedActorCount == 1 && actor.movement.hasContactedActor)
    {
        const bool selfFriendly = actor.identity.hostilityType == 0;
        const bool otherFriendly = actor.movement.contactedActorHostilityType == 0;
        const float deltaX = actor.movement.position.x - actor.movement.contactedActorPosition.x;
        const float deltaY = actor.movement.position.y - actor.movement.contactedActorPosition.y;
        const float distance = length2d(deltaX, deltaY);

        result.zeroVelocity = true;
        result.actionSeconds = std::max(actor.runtime.actionSeconds, contactFleeActionSeconds(actor, distance));

        if (selfFriendly && otherFriendly)
        {
            result.faceContact = true;
            result.stand = true;

            if (distance > 0.01f)
            {
                result.yawRadians = std::atan2(
                    actor.movement.contactedActorPosition.y - actor.movement.position.y,
                    actor.movement.contactedActorPosition.x - actor.movement.position.x);
            }

            return result;
        }

        if (distance > 0.01f)
        {
            result.fleeFromContact = true;
            result.moveDirectionX = deltaX / distance;
            result.moveDirectionY = deltaY / distance;
            result.yawRadians = std::atan2(result.moveDirectionY, result.moveDirectionX);
            return result;
        }

        result.resetMoveDirection = true;
        result.stand = true;
        return result;
    }

    if (actor.movement.movementSuppressedByNavigation)
    {
        result.zeroVelocity = true;
        result.resetMoveDirection = true;
        result.stand = true;
        result.actionSeconds = std::min(actor.runtime.actionSeconds, ContactFleeFallbackSeconds);
        return result;
    }

    if (!actor.movement.movementBlocked)
    {
        return result;
    }

    result.zeroVelocity = true;
    result.actionSeconds = actor.runtime.actionSeconds;

    if (actor.runtime.motionState != ActorAiMotionState::Pursuing)
    {
        result.resetMoveDirection = true;
        result.stand = true;
        result.actionSeconds = std::min(actor.runtime.actionSeconds, 0.25f);
    }

    return result;
}

bool AI_HandleMovementBlock(ActorAiCommandContext &ai)
{
    const ActorMovementBlockOutcome movementBlock = buildPostMovementBlock(ai.actor());

    if (!movementBlock.zeroVelocity && !movementBlock.resetMoveDirection && !movementBlock.stand)
    {
        return false;
    }

    if (movementBlock.zeroVelocity)
    {
        ai.clearVelocity();
    }

    if (movementBlock.fleeFromContact)
    {
        ai.setMotionState(ActorAiMotionState::Fleeing);
        ai.setAnimationState(ActorAiAnimationState::Walking);
        ai.setMovementAction(ActorAiMovementAction::Flee);
        ai.setMoveDirection(movementBlock.moveDirectionX, movementBlock.moveDirectionY);
        ai.setDesiredMovement(movementBlock.moveDirectionX, movementBlock.moveDirectionY);
        ai.faceYaw(movementBlock.yawRadians);
        ai.setActionSeconds(movementBlock.actionSeconds);
        return true;
    }

    if (movementBlock.faceContact)
    {
        ai.setMotionState(ActorAiMotionState::Standing);
        ai.setAnimationState(ActorAiAnimationState::Standing);
        ai.setMovementAction(ActorAiMovementAction::Stand);
        ai.clearMovementDirection();
        ai.faceYaw(movementBlock.yawRadians);
        ai.setActionSeconds(movementBlock.actionSeconds);
        return true;
    }

    if (movementBlock.resetMoveDirection)
    {
        ai.setMovementAction(ActorAiMovementAction::Stand);
        ai.clearMovementDirection();
        ai.setActionSeconds(movementBlock.actionSeconds);
    }

    if (movementBlock.stand)
    {
        ai.setMotionState(ActorAiMotionState::Standing);
        ai.setAnimationState(ActorAiAnimationState::Standing);
    }

    if (movementBlock.crowdStand)
    {
        ai.setCrowdStandRemainingSeconds(movementBlock.actionSeconds);
    }

    return true;
}

bool AI_ContinueFlee(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();

    if (actor.runtime.motionState != ActorAiMotionState::Fleeing
        || actor.runtime.actionSeconds <= 0.0f
        || !actor.movement.movementAllowed)
    {
        return false;
    }

    if (std::abs(actor.movement.moveDirectionX) <= 0.001f
        && std::abs(actor.movement.moveDirectionY) <= 0.001f)
    {
        return false;
    }

    ai.setMotionState(ActorAiMotionState::Fleeing);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.setMovementAction(ActorAiMovementAction::Flee);
    ai.setMoveDirection(actor.movement.moveDirectionX, actor.movement.moveDirectionY);
    ai.setDesiredMovement(actor.movement.moveDirectionX, actor.movement.moveDirectionY);
    ai.faceYaw(std::atan2(actor.movement.moveDirectionY, actor.movement.moveDirectionX));
    ai.update().movementIntent.applyMovement = true;
    return true;
}

ActorCombatFlowAction chooseCombatFlowAction(
    bool attackInProgress,
    bool blindActive,
    bool shouldFlee,
    bool fearActive,
    bool shouldEngageTarget,
    bool friendlyNearParty)
{
    if (attackInProgress)
    {
        return ActorCombatFlowAction::ContinueAttack;
    }

    if (blindActive)
    {
        return ActorCombatFlowAction::BlindWander;
    }

    if (shouldFlee || fearActive)
    {
        return ActorCombatFlowAction::Flee;
    }

    if (shouldEngageTarget)
    {
        return ActorCombatFlowAction::EngageTarget;
    }

    if (friendlyNearParty)
    {
        return ActorCombatFlowAction::FriendlyNearParty;
    }

    return ActorCombatFlowAction::NonCombat;
}

ActorCombatFlowOutcome buildCombatFlowOutcome(
    ActorCombatFlowAction action,
    bool movementAllowed,
    float currentYawRadians,
    float currentMoveDirectionX,
    float currentMoveDirectionY,
    float targetDeltaX,
    float targetDeltaY,
    float targetHorizontalDistance,
    float actionSeconds,
    float idleDecisionSeconds)
{
    ActorCombatFlowOutcome result = {};
    result.actionSeconds = actionSeconds;
    result.idleDecisionSeconds = idleDecisionSeconds;

    if (action == ActorCombatFlowAction::ContinueAttack)
    {
        result.motion = ActorCombatFlowMotion::Attacking;
        result.animation = ActorCombatFlowAnimation::Current;
        result.clearMoveDirection = true;
        return result;
    }

    if (action == ActorCombatFlowAction::BlindWander)
    {
        result.motion = ActorCombatFlowMotion::Wandering;
        result.animation = movementAllowed
            ? ActorCombatFlowAnimation::Walking
            : ActorCombatFlowAnimation::Standing;

        if (std::abs(currentMoveDirectionX) < 0.01f && std::abs(currentMoveDirectionY) < 0.01f)
        {
            result.updateMoveDirection = true;
            result.moveDirectionX = std::cos(currentYawRadians);
            result.moveDirectionY = std::sin(currentYawRadians);
        }

        return result;
    }

    if (action == ActorCombatFlowAction::Flee)
    {
        result.motion = ActorCombatFlowMotion::Fleeing;
        result.animation = movementAllowed
            ? ActorCombatFlowAnimation::Walking
            : ActorCombatFlowAnimation::Standing;

        if (targetHorizontalDistance > 0.01f)
        {
            result.updateDesiredMove = true;
            result.desiredMoveX = -targetDeltaX / targetHorizontalDistance;
            result.desiredMoveY = -targetDeltaY / targetHorizontalDistance;
            result.updateMoveDirection = true;
            result.moveDirectionX = result.desiredMoveX;
            result.moveDirectionY = result.desiredMoveY;
            result.updateYaw = true;
            result.yawRadians = std::atan2(result.desiredMoveY, result.desiredMoveX);
        }

        return result;
    }

    if (action == ActorCombatFlowAction::FriendlyNearParty)
    {
        result.motion = ActorCombatFlowMotion::Standing;
        result.animation = ActorCombatFlowAnimation::Standing;
        result.clearMoveDirection = true;
        result.clearVelocity = true;
        result.actionSeconds = std::max(actionSeconds, 0.25f);
        result.idleDecisionSeconds = std::max(idleDecisionSeconds, 0.25f);
    }

    return result;
}

ActorAiMotionState actorMotionStateFromCombatFlow(ActorCombatFlowMotion motion)
{
    switch (motion)
    {
        case ActorCombatFlowMotion::Attacking:
            return ActorAiMotionState::Attacking;
        case ActorCombatFlowMotion::Wandering:
            return ActorAiMotionState::Wandering;
        case ActorCombatFlowMotion::Fleeing:
            return ActorAiMotionState::Fleeing;
        case ActorCombatFlowMotion::Standing:
        default:
            return ActorAiMotionState::Standing;
    }
}

ActorAiAnimationState actorAnimationStateFromCombatFlow(
    ActorCombatFlowAnimation animation,
    const ActorAiFacts &actor)
{
    switch (animation)
    {
        case ActorCombatFlowAnimation::Current:
            if (actor.runtime.motionState == ActorAiMotionState::Attacking)
            {
                return attackAnimationStateForAbility(
                    actor.runtime.queuedAttackAbility,
                    actor.stats.attackConstraints);
            }

            return actor.runtime.animationState;
        case ActorCombatFlowAnimation::Walking:
            return ActorAiAnimationState::Walking;
        case ActorCombatFlowAnimation::Standing:
        default:
            return ActorAiAnimationState::Standing;
    }
}

bool combatFlowActionCanBeAppliedByShared(ActorCombatFlowAction action)
{
    return action == ActorCombatFlowAction::ContinueAttack
        || action == ActorCombatFlowAction::BlindWander
        || action == ActorCombatFlowAction::Flee
        || action == ActorCombatFlowAction::FriendlyNearParty;
}

CombatEngagePlan chooseCombatEngagePlan(const CombatEngagePlanInput &input)
{
    CombatEngagePlan result = {};
    const bool currentlyPursuingWithMoveDirection =
        input.currentlyPursuing
        && input.actionSeconds > 0.0f
        && (std::abs(input.currentMoveDirectionX) > 0.001f
            || std::abs(input.currentMoveDirectionY) > 0.001f);

    if (input.abilityIsMelee && input.crowdStandActive && !input.inMeleeRange)
    {
        result.action = CombatEngageAction::HoldCrowdStand;
        result.preserveCrowdSteering = true;
        return result;
    }

    if (input.abilityIsRanged)
    {
        if (input.attackCooldownReady)
        {
            result.action = CombatEngageAction::StartRangedAttack;
            return result;
        }

        if (input.stationaryOrTooCloseForRangedPursuit)
        {
            result.action = CombatEngageAction::StandForRangedBlock;
            return result;
        }

        if (currentlyPursuingWithMoveDirection)
        {
            result.action = CombatEngageAction::ContinueRangedPursuit;
            return result;
        }

        result.action = CombatEngageAction::StartRangedPursuit;
        result.pursueMode = PursueActionMode::RangedOrbit;
        result.useRecoveryFloorForPursuit = true;
        return result;
    }

    if (input.abilityIsMelee && input.inMeleeRange)
    {
        if (input.attackCooldownReady)
        {
            result.action = CombatEngageAction::StartMeleeAttack;
            return result;
        }

        result.action = CombatEngageAction::StandForMeleeCooldown;
        return result;
    }

    result.meleePursuitActive = input.abilityIsMelee;
    result.preserveCrowdSteering = input.abilityIsMelee;

    if (!input.movementAllowed)
    {
        result.action = CombatEngageAction::StartMeleePursuitWithoutMovement;
        return result;
    }

    if (currentlyPursuingWithMoveDirection)
    {
        result.action = CombatEngageAction::ContinueMeleePursuit;
        return result;
    }

    result.action = CombatEngageAction::StartMeleePursuit;
    result.pursueMode =
        input.targetEdgeDistance >= 1024.0f ? PursueActionMode::OffsetWide : PursueActionMode::Direct;
    return result;
}

PursueActionResult resolvePursueAction(const PursueActionInput &input)
{
    PursueActionResult result = {};
    result.nextDecisionCount = input.pursueDecisionCount + 1;

    if (input.distanceToTarget <= 0.01f || input.moveSpeed <= 0.0f)
    {
        return result;
    }

    const uint32_t decisionSeed =
        mixActorDecisionSeed(input.actorId, input.pursueDecisionCount, 0x9e3779b9u);

    result.started = true;
    result.yawRadians = std::atan2(input.deltaTargetY, input.deltaTargetX);
    result.actionSeconds = input.distanceToTarget / input.moveSpeed;

    if (input.mode == PursueActionMode::RangedOrbit)
    {
        // MM8's Pursue1: head for the point a small step further round the target's circle at the current
        // distance. Each actor keeps one side, so ranged monsters circle the party instead of closing in.
        const float sideSign = (input.actorId & 1u) == 0u ? 1.0f : -1.0f;
        const float orbitYaw =
            std::atan2(-input.deltaTargetY, -input.deltaTargetX) + sideSign * RangedOrbitStepRadians;
        const float moveX = input.deltaTargetX + std::cos(orbitYaw) * input.distanceToTarget;
        const float moveY = input.deltaTargetY + std::sin(orbitYaw) * input.distanceToTarget;
        result.yawRadians = std::atan2(moveY, moveX);
        result.actionSeconds = 0.5f;
    }
    else if (input.mode == PursueActionMode::OffsetShort)
    {
        const float offset = (decisionSeed & 1u) == 0u ? (Pi / 64.0f) : (-Pi / 64.0f);
        result.yawRadians = normalizeAngleRadians(result.yawRadians + offset);
        result.actionSeconds = 0.5f;
    }
    else if (input.mode == PursueActionMode::Direct)
    {
        result.actionSeconds = std::min(result.actionSeconds, 32.0f / ActorAiTicksPerSecond);
    }
    else
    {
        const float offset = (decisionSeed & 1u) == 0u ? (Pi / 4.0f) : (-Pi / 4.0f);
        result.yawRadians = normalizeAngleRadians(result.yawRadians + offset);
        result.actionSeconds = std::min(result.actionSeconds, 128.0f / ActorAiTicksPerSecond);
    }

    result.moveDirectionX = std::cos(result.yawRadians);
    result.moveDirectionY = std::sin(result.yawRadians);
    result.actionSeconds = std::max(std::max(0.05f, result.actionSeconds), input.minimumActionSeconds);
    return result;
}

void AI_ApplyCombatFlowOutcome(ActorAiCommandContext &ai, const ActorCombatFlowOutcome &application)
{
    const ActorAiFacts &actor = ai.actor();

    ai.setMotionState(actorMotionStateFromCombatFlow(application.motion));
    ai.setAnimationState(actorAnimationStateFromCombatFlow(application.animation, actor));
    ai.resetAnimationOnChange();
    ai.setActionSeconds(application.actionSeconds);
    ai.setIdleDecisionSeconds(application.idleDecisionSeconds);

    if (application.motion == ActorCombatFlowMotion::Attacking)
    {
        ai.setMovementAction(ActorAiMovementAction::Stand);
    }
    else if (application.motion == ActorCombatFlowMotion::Wandering)
    {
        ai.setMovementAction(ActorAiMovementAction::Wander);
    }
    else if (application.motion == ActorCombatFlowMotion::Fleeing)
    {
        ai.setMovementAction(ActorAiMovementAction::Flee);
    }
    else
    {
        ai.setMovementAction(ActorAiMovementAction::Stand);
    }

    if (application.clearMoveDirection)
    {
        ai.clearMovementDirection();
    }

    if (application.updateMoveDirection)
    {
        ai.setMoveDirection(application.moveDirectionX, application.moveDirectionY);
    }

    if (application.updateDesiredMove)
    {
        ai.setDesiredMovement(application.desiredMoveX, application.desiredMoveY);
    }

    if (application.updateYaw)
    {
        ai.faceYaw(application.yawRadians);
    }

    if (application.clearVelocity)
    {
        ai.clearVelocity();
    }
}

void AI_Flee(ActorAiCommandContext &ai, const ActorCombatFlowOutcome &application)
{
    AI_ApplyCombatFlowOutcome(ai, application);
}

void applyActiveMovementCommit(
    const ActorAiFacts &actor,
    bool preserveCrowdSteering,
    ActorAiUpdate &update)
{
    const ActorMovementCommit movementCommit =
        buildActiveMovementCommit(actor, update, preserveCrowdSteering);

    update.movementIntent.resetCrowdSteering = movementCommit.resetCrowdSteering;
    update.movementIntent.clearVelocity = movementCommit.clearVelocity;
    update.movementIntent.applyMovement = movementCommit.applyMovement;
    const ActorAiMotionState motionState = update.state.motionState.value_or(actor.runtime.motionState);
    update.movementIntent.moveSpeed = movementSpeedForMotion(actor.movement.effectiveMoveSpeed, motionState);
    const GameplayWorldPoint movementTargetPosition = actorMovementTargetPosition(actor);
    update.movementIntent.targetPosition = movementTargetPosition;
    update.movementIntent.targetEdgeDistance = actor.target.currentEdgeDistance;
    update.movementIntent.targetHasAttackLineOfSight = actor.target.currentHasAttackLineOfSight;
    update.movementIntent.inMeleeRange =
        actor.movement.inMeleeRange && actor.target.currentHasAttackLineOfSight;
    update.movementIntent.crowdSteeringActive =
        preserveCrowdSteering
        && update.movementIntent.meleePursuitActive
        && movementCommit.applyMovement
        && (update.state.crowdSideLockRemainingSeconds.value_or(actor.runtime.crowdSideLockRemainingSeconds) > 0.0f
            || update.state.crowdRetreatRemainingSeconds.value_or(actor.runtime.crowdRetreatRemainingSeconds) > 0.0f);

    if (actor.stats.canFly)
    {
        const float verticalTargetDelta =
            movementTargetPosition.z + actor.status.climbAboveTarget - actor.world.targetZ;
        const float horizontalDistance =
            std::sqrt(
                (movementTargetPosition.x - actor.movement.position.x)
                    * (movementTargetPosition.x - actor.movement.position.x)
                + (movementTargetPosition.y - actor.movement.position.y)
                    * (movementTargetPosition.y - actor.movement.position.y));
        const float distance =
            std::sqrt(horizontalDistance * horizontalDistance + verticalTargetDelta * verticalTargetDelta);

        if (distance > 0.001f && std::abs(verticalTargetDelta) > 8.0f)
        {
            update.movementIntent.desiredMoveZ = std::clamp(verticalTargetDelta / distance, -1.0f, 1.0f);
        }
    }
}

void AI_HoldIdle(ActorAiCommandContext &ai);
void AI_StartIdleStand(ActorAiCommandContext &ai);
bool AI_TacticIdleAim(ActorAiCommandContext &ai);
void AI_Stand(ActorAiCommandContext &ai);
void AI_RandomMove(ActorAiCommandContext &ai, float moveDirectionX, float moveDirectionY);

bool AI_CombatFlow(ActorAiCommandContext &ai, bool attackInProgress)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts *pFrame = ai.frame();

    if (pFrame == nullptr)
    {
        return false;
    }

    const ActorTargetState combatTarget = buildActorTargetStateFromFacts(actor);
    const GameplayActorService actorService = {};
    const ActorEngagementState engagement =
        resolveActorEngagement(actor, *pFrame, actorService);

    const ActorCombatFlowAction flowAction = chooseCombatFlowAction(
        attackInProgress,
        actor.status.spellEffects.blindRemainingSeconds > 0.0f,
        engagement.shouldFlee,
        actor.status.spellEffects.fearRemainingSeconds > 0.0f,
        engagement.shouldEngageTarget,
        engagement.friendlyNearParty);

    if (!combatFlowActionCanBeAppliedByShared(flowAction))
    {
        return false;
    }

    const float actionSeconds = std::max(
        0.0f,
        actor.runtime.actionSeconds - (actor.runtime.motionState == ActorAiMotionState::Attacking
            ? pFrame->fixedStepSeconds / std::max(1.0f, actor.status.spellEffects.slowRecoveryMultiplier)
            : pFrame->fixedStepSeconds));
    const float idleDecisionSeconds =
        std::max(0.0f, actor.runtime.idleDecisionSeconds - pFrame->fixedStepSeconds);

    const ActorCombatFlowOutcome flowOutcome = buildCombatFlowOutcome(
        flowAction,
        actor.movement.movementAllowed,
        actor.runtime.yawRadians,
        actor.movement.moveDirectionX,
        actor.movement.moveDirectionY,
        combatTarget.deltaX,
        combatTarget.deltaY,
        combatTarget.horizontalDistanceToTarget,
        actionSeconds,
        idleDecisionSeconds);

    if (flowAction == ActorCombatFlowAction::Flee)
    {
        AI_Flee(ai, flowOutcome);
        ai.decide(ActorAiDecisionKind::Flee, actor.status.spellEffects.fearRemainingSeconds > 0.0f ? "fear"
            : actor.status.forceFleeFromParty ? "forced" : mm9LoopActive(actor, pFrame) ? "run_away" : "ai_type");
        return true;
    }

    AI_ApplyCombatFlowOutcome(ai, flowOutcome);

    if (flowAction == ActorCombatFlowAction::BlindWander)
    {
        ai.decide(ActorAiDecisionKind::BlindWander);
    }
    if (flowAction == ActorCombatFlowAction::FriendlyNearParty)
    {
        // A friendly turret keeps scanning while the party walks by.
        if (AI_TacticIdleAim(ai))
        {
            return true;
        }

        if (actionSeconds <= 0.0f)
        {
            AI_StartIdleStand(ai);
        }
        else
        {
            AI_HoldIdle(ai);
            ai.setActionSeconds(actionSeconds);
            ai.setIdleDecisionSeconds(idleDecisionSeconds);
        }
    }
    return true;
}

std::optional<ActorTargetCandidateFacts> chooseTarget(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    if (actor.target.currentKind != ActorAiTargetKind::None && actor.target.currentCanSense)
    {
        ActorTargetCandidateFacts target = {};
        target.kind = actor.target.currentKind;
        target.actorIndex = actor.target.currentActorIndex;
        target.currentHp = actor.target.currentHp;
        target.position =
            actor.target.currentKind == ActorAiTargetKind::Party
            ? frame.party.position
            : actor.target.currentPosition;
        target.audioPosition = actor.target.currentAudioPosition;
        target.hasLineOfSight = actor.target.currentHasAttackLineOfSight;
        return target;
    }

    for (const ActorTargetCandidateFacts &candidate : actor.target.candidates)
    {
        if (!candidate.unavailable && candidate.hasLineOfSight)
        {
            return candidate;
        }
    }

    return std::nullopt;
}

void AI_ApplyDeathState(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts *pFrame = ai.frame();

    if (pFrame == nullptr)
    {
        return;
    }

    const ActorDeathFrameOutcome deathFrame = resolveActorDeathFrame(
        actor.status.dead || actor.runtime.motionState == ActorAiMotionState::Dead,
        actor.stats.currentHp <= 0,
        actor.runtime.motionState == ActorAiMotionState::Dying,
        actor.runtime.actionSeconds,
        pFrame->fixedStepSeconds);

    ai.setAttackImpactTriggered(false);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearVelocity();

    if (deathFrame.action == ActorDeathFrameAction::HoldDead)
    {
        ai.setMotionState(ActorAiMotionState::Dead);
        ai.setAnimationState(ActorAiAnimationState::Dead);
        return;
    }

    if (deathFrame.action == ActorDeathFrameAction::MarkDead || deathFrame.finishedDying)
    {
        ActorFxRequest deathFx = {};
        deathFx.kind = ActorAiFxRequestKind::Death;
        deathFx.actorIndex = actor.actorIndex;
        deathFx.position = actor.movement.position;
        ai.requestFx(deathFx);

        ai.setDead(true);
        ai.setMotionState(ActorAiMotionState::Dead);
        ai.setActionSeconds(0.0f);
        ai.setAnimationState(ActorAiAnimationState::Dead);
        ai.setAnimationTimeTicks(0.0f);
        return;
    }

    if (deathFrame.action == ActorDeathFrameAction::AdvanceDying)
    {
        ActorFxRequest deathFx = {};
        deathFx.kind = ActorAiFxRequestKind::Death;
        deathFx.actorIndex = actor.actorIndex;
        deathFx.position = actor.movement.position;
        ai.requestFx(deathFx);

        ai.setMotionState(ActorAiMotionState::Dying);
        ai.setActionSeconds(deathFrame.actionSeconds);
        ai.setAnimationState(ActorAiAnimationState::Dying);
        ai.setAnimationTimeTicks(actor.runtime.animationTimeTicks + actorAnimationTickDelta(actor, *pFrame));
    }
}

float ageActorAnimationTimeTicks(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    return actor.runtime.animationTimeTicks + actorAnimationTickDelta(actor, frame);
}

void applyActiveAnimationTickUpdate(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
{
    if (!actor.world.active)
    {
        return;
    }

    update.animation.animationTimeTicks = ageActorAnimationTimeTicks(actor, frame);
}

void AI_ClearMovement(ActorAiCommandContext &ai)
{
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearVelocity();
}

void applyActiveSpellTimerUpdate(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
{
    if (!actor.world.active || update.state.spellEffects || !hasActiveSpellEffectTimer(actor.status.spellEffects))
    {
        return;
    }

    GameplayActorSpellEffectState spellEffects = actor.status.spellEffects;
    const GameplayActorService actorService = {};
    actorService.updateSpellEffectTimers(spellEffects, frame.fixedStepSeconds, actor.status.defaultHostileToParty);
    update.state.spellEffects = spellEffects;
}

void applyStatusContinuationUpdate(const std::optional<ActorAiUpdate> &statusUpdate, ActorAiUpdate &update)
{
    if (!statusUpdate || !statusUpdate->state.spellEffects)
    {
        return;
    }

    update.state.spellEffects = *statusUpdate->state.spellEffects;
}

void applyActiveFrameTimerUpdate(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
{
    if (!actor.world.active)
    {
        return;
    }

    const ActorFrameTimerAging frameTimers = ageActorFrameTimers(actor, frame);

    update.state.idleDecisionSeconds = frameTimers.idleDecisionSeconds;
    update.state.attackCooldownSeconds = frameTimers.attackCooldownSeconds;
    update.state.actionSeconds = frameTimers.actionSeconds;
    update.state.crowdSideLockRemainingSeconds = frameTimers.crowdSideLockRemainingSeconds;
    update.state.crowdRetreatRemainingSeconds = frameTimers.crowdRetreatRemainingSeconds;
    update.state.crowdStandRemainingSeconds = frameTimers.crowdStandRemainingSeconds;

    if (actor.runtime.skirmishSeconds > 0.0f)
    {
        update.state.skirmishSeconds = frameTimers.skirmishSeconds;
    }
}

CrowdSteeringState buildCrowdSteeringState(const ActorAiFacts &actor)
{
    CrowdSteeringState state = {};
    state.noProgressSeconds = actor.runtime.crowdNoProgressSeconds;
    state.lastEdgeDistance = actor.runtime.crowdLastEdgeDistance;
    state.retreatRemainingSeconds = actor.runtime.crowdRetreatRemainingSeconds;
    state.standRemainingSeconds = actor.runtime.crowdStandRemainingSeconds;
    state.probeEdgeDistance = actor.runtime.crowdProbeEdgeDistance;
    state.probeElapsedSeconds = actor.runtime.crowdProbeElapsedSeconds;
    state.escapeAttempts = actor.runtime.crowdEscapeAttempts;
    state.sideSign = actor.runtime.crowdSideSign;
    return state;
}

bool shouldApplyCrowdSteering(const CrowdSteeringEligibility &eligibility)
{
    const bool hasTrigger = eligibility.contactedActorCount > 0 || eligibility.movementBlocked;

    return hasTrigger
        && eligibility.meleePursuitActive
        && eligibility.pursuing
        && !eligibility.inMeleeRange
        && eligibility.targetEdgeDistance <= CrowdReangleEngageRange;
}

CrowdSteeringResult resolveCrowdSteering(
    uint32_t actorId,
    uint32_t pursueDecisionCount,
    float targetEdgeDistance,
    float deltaSeconds,
    const CrowdSteeringState &state)
{
    CrowdSteeringResult result = {};
    result.state = state;
    result.nextDecisionCount = pursueDecisionCount;
    result.sideSign = result.state.sideSign == 0 ? 1 : result.state.sideSign;
    result.state.probeElapsedSeconds += std::max(0.0f, deltaSeconds);

    const float progressTowardTarget =
        result.state.lastEdgeDistance > 0.0f
        ? (result.state.lastEdgeDistance - targetEdgeDistance)
        : 0.0f;
    const float crowdProbeEdgeProgress =
        result.state.probeEdgeDistance > 0.0f
        ? (result.state.probeEdgeDistance - targetEdgeDistance)
        : 0.0f;

    if (result.state.sideSign == 0)
    {
        const uint32_t decisionSeed = mixActorDecisionSeed(actorId, result.nextDecisionCount, 0x4f1bbcd3u);
        ++result.nextDecisionCount;
        result.sideSign = (decisionSeed & 1u) == 0u ? 1 : -1;
        result.state.sideSign = result.sideSign;

        if (result.state.lastEdgeDistance <= 0.0f)
        {
            result.state.lastEdgeDistance = targetEdgeDistance;
        }

        result.action = CrowdSteeringAction::SideStep;
        return result;
    }

    if (progressTowardTarget > CrowdNoProgressThreshold)
    {
        result.state.noProgressSeconds = 0.0f;
        result.state.lastEdgeDistance = targetEdgeDistance;
        result.state.escapeAttempts = 0;
    }
    else
    {
        result.state.noProgressSeconds += std::max(0.0f, deltaSeconds);
    }

    const bool crowdProbeStalled =
        result.state.probeElapsedSeconds >= CrowdProbeWindowSeconds
        && crowdProbeEdgeProgress <= CrowdProbeEdgeDistanceThreshold;

    if (crowdProbeStalled && result.state.retreatRemainingSeconds <= 0.0f)
    {
        ++result.state.escapeAttempts;

        const uint32_t decisionSeed = mixActorDecisionSeed(actorId, result.nextDecisionCount, 0x7a5f18c3u);
        ++result.nextDecisionCount;
        const bool shouldStandAfterRetries =
            result.state.escapeAttempts >= 3
            && ((decisionSeed % 100u) < 45u
                || result.state.noProgressSeconds >= CrowdNoProgressStandSeconds);

        if (shouldStandAfterRetries)
        {
            result.action = CrowdSteeringAction::Stand;
            result.standSeconds = actorDecisionRange(
                actorId,
                result.nextDecisionCount,
                0x5b1d8e73u,
                0.9f,
                1.4f);
            result.bored = (decisionSeed % 100u) < 35u;
            result.state.noProgressSeconds = 0.0f;
            result.state.lastEdgeDistance = 0.0f;
            result.state.retreatRemainingSeconds = 0.0f;
            result.state.standRemainingSeconds = result.standSeconds;
            result.state.probeEdgeDistance = 0.0f;
            result.state.probeElapsedSeconds = 0.0f;
            result.state.escapeAttempts = 0;
            result.state.sideSign = 0;
            return result;
        }

        result.action = CrowdSteeringAction::Retreat;
        result.retreatSeconds = actorDecisionRange(
            actorId,
            result.nextDecisionCount,
            0x6d2c4a91u,
            0.18f,
            0.32f);
        result.state.retreatRemainingSeconds = result.retreatSeconds;
        result.state.noProgressSeconds = 0.0f;
        result.state.probeEdgeDistance = targetEdgeDistance;
        result.state.probeElapsedSeconds = 0.0f;
        return result;
    }

    if (result.state.retreatRemainingSeconds > 0.0f)
    {
        result.action = CrowdSteeringAction::Retreat;
        result.retreatSeconds = result.state.retreatRemainingSeconds;
        result.state.noProgressSeconds = 0.0f;
    }
    else
    {
        result.action = CrowdSteeringAction::SideStep;
    }

    if (result.state.probeElapsedSeconds >= CrowdProbeWindowSeconds
        && crowdProbeEdgeProgress > CrowdProbeEdgeDistanceThreshold)
    {
        result.state.probeEdgeDistance = targetEdgeDistance;
        result.state.probeElapsedSeconds = 0.0f;
    }

    return result;
}

void applyCrowdSteeringStateUpdate(ActorAiCommandContext &ai, const CrowdSteeringState &state)
{
    ai.setCrowdNoProgressSeconds(state.noProgressSeconds);
    ai.setCrowdLastEdgeDistance(state.lastEdgeDistance);
    ai.setCrowdRetreatRemainingSeconds(state.retreatRemainingSeconds);
    ai.setCrowdStandRemainingSeconds(state.standRemainingSeconds);
    ai.setCrowdProbeEdgeDistance(state.probeEdgeDistance);
    ai.setCrowdProbeElapsedSeconds(state.probeElapsedSeconds);
    ai.setCrowdEscapeAttempts(state.escapeAttempts);
    ai.setCrowdSideSign(state.sideSign);
}

void AI_Bored(ActorAiCommandContext &ai);

void AI_CrowdStand(ActorAiCommandContext &ai, const CrowdSteeringResult &crowdSteering)
{
    IdleBehaviorResult idleBehavior = idleStandBehavior(crowdSteering.bored);
    idleBehavior.actionSeconds = std::max(idleBehavior.actionSeconds, crowdSteering.standSeconds);
    idleBehavior.idleDecisionSeconds = std::max(idleBehavior.idleDecisionSeconds, crowdSteering.standSeconds);

    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setActionSeconds(idleBehavior.actionSeconds);
    ai.setIdleDecisionSeconds(idleBehavior.idleDecisionSeconds);
    ai.setAttackImpactTriggered(false);
    ai.setCrowdSideLockRemainingSeconds(0.0f);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    ai.setAnimationTimeTicks(0.0f);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();
    if (idleBehavior.bored)
    {
        AI_Bored(ai);
    }
    ai.setIdleDecisionCount(ai.actor().runtime.idleDecisionCount + 1);
}

void AI_CrowdRetreat(ActorAiCommandContext &ai, const CrowdSteeringResult &crowdSteering)
{
    const ActorAiFacts &actor = ai.actor();
    const int sideSign = crowdSteering.sideSign > 0 ? 1 : -1;
    const float angleOffset = sideSign > 0 ? ActorCrowdRetreatAngleRadians : -ActorCrowdRetreatAngleRadians;
    const GameplayWorldPoint movementTarget = actorMovementTargetPosition(actor);
    const float yaw = normalizeAngleRadians(
        std::atan2(
            movementTarget.y - actor.movement.position.y,
            movementTarget.x - actor.movement.position.x)
        + angleOffset);
    const float moveDirectionX = std::cos(yaw);
    const float moveDirectionY = std::sin(yaw);

    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setActionSeconds(crowdSteering.retreatSeconds);
    ai.setAttackImpactTriggered(false);
    ai.setCrowdSideLockRemainingSeconds(crowdSteering.retreatSeconds);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.setMovementAction(ActorAiMovementAction::Pursue);
    ai.faceYaw(yaw);
    ai.setMoveDirection(moveDirectionX, moveDirectionY);
    ai.setDesiredMovement(moveDirectionX, moveDirectionY);
    ai.update().movementIntent.crowdSteeringActive = true;
}

void AI_CrowdSidestep(ActorAiCommandContext &ai, const CrowdSteeringResult &crowdSteering)
{
    const ActorAiFacts &actor = ai.actor();
    const int sideSign = crowdSteering.sideSign > 0 ? 1 : -1;
    const float angleOffset = sideSign > 0 ? ActorCrowdSidestepAngleRadians : -ActorCrowdSidestepAngleRadians;
    const GameplayWorldPoint movementTarget = actorMovementTargetPosition(actor);
    const float yaw = normalizeAngleRadians(
        std::atan2(
            movementTarget.y - actor.movement.position.y,
            movementTarget.x - actor.movement.position.x)
        + angleOffset);
    const float moveDirectionX = std::cos(yaw);
    const float moveDirectionY = std::sin(yaw);

    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setActionSeconds(ActorCrowdSideLockSeconds);
    ai.setAttackImpactTriggered(false);
    ai.setCrowdSideLockRemainingSeconds(ActorCrowdSideLockSeconds);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.setMovementAction(ActorAiMovementAction::Pursue);
    ai.faceYaw(yaw);
    ai.setMoveDirection(moveDirectionX, moveDirectionY);
    ai.setDesiredMovement(moveDirectionX, moveDirectionY);
    ai.update().movementIntent.crowdSteeringActive = true;
}

bool AI_CrowdSteer(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();

    if (!actor.movement.allowCrowdSteering || actor.movement.movementSuppressedByNavigation)
    {
        return false;
    }

    CrowdSteeringEligibility crowdSteering = {};
    crowdSteering.contactedActorCount = actor.movement.contactedActorCount;
    crowdSteering.meleePursuitActive = actor.movement.meleePursuitActive;
    crowdSteering.pursuing = actor.runtime.motionState == ActorAiMotionState::Pursuing;
    crowdSteering.actorCanFly = actor.stats.canFly;
    crowdSteering.inMeleeRange = actor.movement.inMeleeRange;
    crowdSteering.movementBlocked = actor.movement.movementBlocked;
    crowdSteering.targetEdgeDistance = actor.target.currentEdgeDistance;

    if (!shouldApplyCrowdSteering(crowdSteering))
    {
        return false;
    }

    const CrowdSteeringResult crowdSteeringResult =
        resolveCrowdSteering(
            actor.actorId,
            actor.runtime.pursueDecisionCount,
            actor.target.currentEdgeDistance,
            ActorAiUpdateStepSeconds,
            buildCrowdSteeringState(actor));

    ai.updateCrowdProbePosition();
    ai.setPursueDecisionCount(crowdSteeringResult.nextDecisionCount);
    applyCrowdSteeringStateUpdate(ai, crowdSteeringResult.state);

    if (crowdSteeringResult.action == CrowdSteeringAction::Stand)
    {
        AI_CrowdStand(ai, crowdSteeringResult);
        return true;
    }

    if (crowdSteeringResult.action == CrowdSteeringAction::Retreat)
    {
        AI_CrowdRetreat(ai, crowdSteeringResult);
        return true;
    }

    AI_CrowdSidestep(ai, crowdSteeringResult);
    return true;
}

void applyCombatEngagementUpdate(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
{
    if (!actor.world.active)
    {
        return;
    }

    const GameplayActorService actorService = {};
    const ActorEngagementState engagement =
        resolveActorEngagement(actor, frame, actorService);

    if (engagement.shouldUpdateHostilityType)
    {
        update.state.hostilityType = engagement.hostilityType;
    }

    if (engagement.hasDetectedParty != actor.status.hasDetectedParty)
    {
        update.state.hasDetectedParty = engagement.hasDetectedParty;
    }

}

// An authored attack sound delay plays the sound once the action clock passes it.
void applyDelayedAttackSound(const ActorAiFacts &actor, ActorAiUpdate &update)
{
    if (!actor.world.active || actor.runtime.motionState != ActorAiMotionState::Attacking)
    {
        return;
    }

    const float soundLeadSeconds =
        attackSoundLeadSecondsForAbility(actor, actor.runtime.queuedAttackAbility, actor.stats.attackConstraints);
    const float actionSeconds = update.state.actionSeconds.value_or(actor.runtime.actionSeconds);

    if (actor.runtime.actionSeconds > soundLeadSeconds && actionSeconds <= soundLeadSeconds)
    {
        ActorAudioRequest attackAudio = {};
        attackAudio.kind = ActorAiAudioRequestKind::Attack;
        attackAudio.actorIndex = actor.actorIndex;
        attackAudio.position = actor.movement.position;
        update.audioRequests.push_back(attackAudio);
    }
}

// lobber.scr LaunchPod: the pod of its family (the profile's pod_launch) comes down 128 units beyond its radius toward
// its target, facing it, of its hostility and group (MM9 lobs it at the target from the launch key; OpenYAMM places
// it). The key sets the Lobber's recovery like an attack (object.lto 0x1002a1f0 -> 0x100b3bc0, type 2): it is armed
// as a released shot's (actionLeftSeconds: the clip left).
void applyMm9PodLaunch(const ActorAiFacts &actor, ActorAiUpdate &update, float actionLeftSeconds)
{
    constexpr float PodLaunchDistance = 128.0f;
    ActorMm9State state = update.state.mm9.value_or(actor.runtime.mm9);
    state.podLaunchPending = false;
    state.hitRecoveryArmed = true;
    state.hitActionLeftSeconds = actionLeftSeconds;
    update.state.mm9 = state;
    update.state.attackImpactTriggered = true;

    if (!actor.tactics.mm9Profile || actor.tactics.mm9Profile->podLaunchMonsterId == 0)
    {
        return;
    }

    float directionX = std::cos(actor.runtime.yawRadians);
    float directionY = std::sin(actor.runtime.yawRadians);
    const float deltaX = actor.target.currentPosition.x - actor.movement.position.x;
    const float deltaY = actor.target.currentPosition.y - actor.movement.position.y;
    const float distance = length2d(deltaX, deltaY);

    if (actor.target.currentKind != ActorAiTargetKind::None && distance > 0.01f)
    {
        directionX = deltaX / distance;
        directionY = deltaY / distance;
    }

    const float offset = float(actor.stats.radius) + PodLaunchDistance;
    ActorSpawnRequest request = {};
    request.sourceActorIndex = actor.actorIndex;
    request.monsterId = actor.tactics.mm9Profile->podLaunchMonsterId;
    request.position = {actor.movement.position.x + directionX * offset,
        actor.movement.position.y + directionY * offset, actor.movement.position.z};
    request.yawRadians = std::atan2(directionY, directionX);
    request.hostile = actor.status.hostileToParty;
    request.group = actor.identity.group;
    update.spawnRequest = request;
}

void applyAttackImpactOutcome(const ActorAiFacts &actor, ActorAiUpdate &update)
{
    if (!actor.world.active || actor.runtime.motionState != ActorAiMotionState::Attacking)
    {
        return;
    }

    const float actionSeconds = update.state.actionSeconds.value_or(actor.runtime.actionSeconds);
    const ActorAttackFrameState attackFrame = buildActorAttackFrameState(
        true,
        actor.runtime.attackImpactTriggered,
        actionSeconds,
        attackImpactLeadSecondsForAbility(actor, actor.runtime.queuedAttackAbility, actor.stats.attackConstraints));

    if (!attackFrame.impactDue)
    {
        return;
    }

    // A Lobber's pod launch (MM9_MONSTER_AI_PLAN.md phase 3): at the contact time the pod comes instead of a shot.
    if (actor.runtime.mm9.podLaunchPending)
    {
        applyMm9PodLaunch(actor, update, actionSeconds);
        return;
    }

    const bool abilityIsRanged =
        attackAbilityIsRanged(actor.runtime.queuedAttackAbility, actor.stats.attackConstraints);
    const bool abilityIsMelee = !abilityIsRanged;
    const GameplayActorService actorService = {};
    GameplayActorSpellEffectState spellEffects = update.state.spellEffects.value_or(actor.status.spellEffects);
    const int attackBonus =
        attackAbilityIsSpell(actor.runtime.queuedAttackAbility)
            ? 0
            : actorService.effectiveAttackHitBonus(spellEffects);
    const AttackImpactOutcome attackImpact = finishAttackImpact(
        actor.runtime.queuedAttackAbility,
        actor.stats.monsterLevel,
        attackDamageProfileFromFacts(actor.stats.attack1Damage),
        attackDamageProfileFromFacts(actor.stats.attack2Damage),
        abilityIsRanged,
        abilityIsMelee,
        actor.target.currentKind == ActorAiTargetKind::Party,
        actor.target.currentKind == ActorAiTargetKind::Actor,
        actor.status.spellEffects.shrinkRemainingSeconds > 0.0f,
        actor.status.spellEffects.shrinkDamageMultiplier,
        actor.status.spellEffects.darkGraspRemainingSeconds > 0.0f,
        actorService.effectiveAttackDamageBonus(actor.runtime.queuedAttackAbility, spellEffects),
        actor.tactics.mm9Profile ? std::optional<uint32_t>((actor.actorId + 1u) * 0x9e3779b1u
            ^ (actor.runtime.attackDecisionCount + 1u) * 0x85ebca6bu ^ actor.runtime.mm9.rollCount * 0xc2b2ae35u)
            : std::nullopt);

    update.state.attackImpactTriggered = true;

    // An MM9 monster's hit arms its recovery: a blow that connects (its target in reach), a released shot, a cast.
    if (mm9LoopProfile(actor) != nullptr && attackImpact.action != AttackImpactAction::None
        && (abilityIsRanged ? actor.target.currentHasAttackLineOfSight || attackAbilityIsSpell(
            actor.runtime.queuedAttackAbility) : actor.movement.inMeleeRange))
    {
        if (!update.state.mm9)
        {
            update.state.mm9 = actor.runtime.mm9;
        }

        update.state.mm9->hitRecoveryArmed = true;
        update.state.mm9->hitActionLeftSeconds = actionSeconds;
    }

    if (attackImpact.action == AttackImpactAction::None)
    {
        return;
    }

    if (attackImpact.action == AttackImpactAction::RangedRelease
        && !actor.target.currentHasAttackLineOfSight)
    {
        return;
    }

    if (attackBonus > 0 && spellEffects.fateRemainingSeconds > 0.0f)
    {
        spellEffects.fateRemainingSeconds = 0.0f;
        spellEffects.fatePower = 0;
        update.state.spellEffects = spellEffects;
    }

    if (attackAbilityIsSpell(actor.runtime.queuedAttackAbility))
    {
        int healedCurrentHp = actor.stats.currentHp;

        if (applyMonsterSelfHealSpell(
                actor.runtime.queuedAttackAbility,
                actor.stats,
                healedCurrentHp))
        {
            const bool spell1 = actor.runtime.queuedAttackAbility == GameplayActorAttackAbility::Spell1;
            ActorFxRequest healFx = {};
            healFx.kind = ActorAiFxRequestKind::Buff;
            healFx.actorIndex = actor.actorIndex;
            healFx.spellId = spell1 ? actor.stats.spell1Id : actor.stats.spell2Id;
            healFx.position = actor.movement.position;
            update.fxRequests.push_back(healFx);
            update.state.currentHp = healedCurrentHp;
            return;
        }

        if (applyMonsterSelfBuffSpell(
                actor.runtime.queuedAttackAbility,
                actor.stats,
                spellEffects))
        {
            const bool spell1 = actor.runtime.queuedAttackAbility == GameplayActorAttackAbility::Spell1;
            ActorFxRequest buffFx = {};
            buffFx.kind = ActorAiFxRequestKind::Buff;
            buffFx.actorIndex = actor.actorIndex;
            buffFx.spellId = spell1 ? actor.stats.spell1Id : actor.stats.spell2Id;
            buffFx.position = actor.movement.position;
            update.fxRequests.push_back(buffFx);
            update.state.spellEffects = spellEffects;
            return;
        }
    }

    ActorAttackRequest request = {};
    request.ability = actor.runtime.queuedAttackAbility;
    request.targetKind = actor.target.currentKind;
    request.targetActorIndex = actor.target.currentActorIndex;
    request.damage = attackImpact.damage;
    request.attackBonus = attackBonus;
    request.damageType = attackDamageTypeFromFacts(actor.runtime.queuedAttackAbility, actor.stats);
    request.source = actor.movement.position;
    request.target = actor.target.currentPosition;
    request.target.x += actor.tactics.aimLead.x;
    request.target.y += actor.tactics.aimLead.y;
    request.target.z += actor.tactics.aimLead.z;

    if (actor.runtime.queuedAttackAbility == GameplayActorAttackAbility::Spell1)
    {
        request.spellId = actor.stats.spell1Id;
        request.skillLevel = actor.stats.spell1SkillLevel;
        request.skillMastery = actor.stats.spell1SkillMastery;
    }
    else if (actor.runtime.queuedAttackAbility == GameplayActorAttackAbility::Spell2)
    {
        request.spellId = actor.stats.spell2Id;
        request.skillLevel = actor.stats.spell2SkillLevel;
        request.skillMastery = actor.stats.spell2SkillMastery;
    }
    else if (actor.runtime.queuedAttackAbility == GameplayActorAttackAbility::Attack2)
    {
        request.projectileTokenOverride = actor.stats.attack2MissileTypeOverride;
    }

    if (attackImpact.action == AttackImpactAction::RangedRelease)
    {
        request.kind =
            attackAbilityIsSpell(actor.runtime.queuedAttackAbility)
            ? ActorAiAttackRequestKind::SpellProjectile
            : ActorAiAttackRequestKind::RangedProjectile;
    }
    else if (attackImpact.action == AttackImpactAction::PartyMeleeImpact)
    {
        request.kind = ActorAiAttackRequestKind::PartyMelee;
    }
    else if (attackImpact.action == AttackImpactAction::ActorMeleeImpact)
    {
        request.kind = ActorAiAttackRequestKind::ActorMelee;
    }

    update.attackRequest = request;
}

void AI_Pursue(ActorAiCommandContext &ai, PursueActionMode mode, float minimumActionSeconds)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorTargetState combatTarget = buildActorTargetStateFromFacts(actor);

    PursueActionInput pursueInput = {};
    pursueInput.actorId = actor.actorId;
    pursueInput.pursueDecisionCount = actor.runtime.pursueDecisionCount;
    pursueInput.deltaTargetX = combatTarget.deltaX;
    pursueInput.deltaTargetY = combatTarget.deltaY;
    pursueInput.distanceToTarget = combatTarget.horizontalDistanceToTarget;
    pursueInput.moveSpeed = actor.movement.effectiveMoveSpeed;
    pursueInput.minimumActionSeconds = minimumActionSeconds;
    pursueInput.mode = mode;
    const PursueActionResult pursueAction = resolvePursueAction(pursueInput);
    ai.setPursueDecisionCount(pursueAction.nextDecisionCount);

    if (pursueAction.started)
    {
        if (mode == PursueActionMode::RangedOrbit)
        {
            ai.decide(ActorAiDecisionKind::Orbit);
        }
        else
        {
            ai.decide(ActorAiDecisionKind::Pursue, mode == PursueActionMode::Direct ? "direct"
                : mode == PursueActionMode::OffsetShort ? "offset_short" : "offset_wide");
        }

        ai.setMovementAction(ActorAiMovementAction::Pursue);
        ai.faceYaw(pursueAction.yawRadians);
        ai.setMoveDirection(pursueAction.moveDirectionX, pursueAction.moveDirectionY);
        ai.setDesiredMovement(pursueAction.moveDirectionX, pursueAction.moveDirectionY);
        ai.setActionSeconds(pursueAction.actionSeconds);
        ai.setAttackImpactTriggered(false);
        // MM8's Pursue3 alone occasionally uses the hit slot, independently of damage reactions.
        if (mode == PursueActionMode::OffsetWide
            && actorVocalizationRoll(actor.actorId, actor.runtime.pursueDecisionCount, 0x281da370u) < 2u)
        {
            ActorAudioRequest audio = {};
            audio.kind = ActorAiAudioRequestKind::Hit;
            audio.actorIndex = actor.actorIndex;
            audio.position = actor.movement.position;
            ai.requestAudio(audio);
        }
        return;
    }

    const GameplayWorldPoint movementTargetPosition = actorMovementTargetPosition(actor);
    const float verticalTargetDelta = movementTargetPosition.z - actor.world.targetZ;
    if (actor.stats.canFly
        && std::abs(verticalTargetDelta) > 8.0f
        && actor.movement.effectiveMoveSpeed > 0.0f)
    {
        ai.setMotionState(ActorAiMotionState::Pursuing);
        ai.setAnimationState(ActorAiAnimationState::Walking);
        ai.setMovementAction(ActorAiMovementAction::Pursue);
        ai.setActionSeconds(std::max(
            std::abs(verticalTargetDelta) / actor.movement.effectiveMoveSpeed,
            minimumActionSeconds));
        ai.setAttackImpactTriggered(false);
        return;
    }

    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
}

void AI_Pursue1(ActorAiCommandContext &ai, float minimumActionSeconds)
{
    AI_Pursue(ai, PursueActionMode::Direct, minimumActionSeconds);
}

void AI_Pursue2(ActorAiCommandContext &ai, float minimumActionSeconds)
{
    AI_Pursue(ai, PursueActionMode::OffsetShort, minimumActionSeconds);
}

void AI_Pursue3(ActorAiCommandContext &ai, float minimumActionSeconds)
{
    AI_Pursue(ai, PursueActionMode::OffsetWide, minimumActionSeconds);
}

// Skirmishers (ActorTacticsFacts::skirmish, MM9's BaseMelee AI). Every helper leaves any other actor to the native AI.
bool skirmishActive(const ActorAiFacts &actor, const ActorAiFrameFacts *pFrame)
{
    return actor.tactics.skirmish
        && pFrame != nullptr
        && pFrame->turnBased.mode == ActorTurnBasedMode::RealTime
        && actor.movement.movementAllowed
        && actor.movement.effectiveMoveSpeed > 0.0f
        && actor.target.currentKind != ActorAiTargetKind::None;
}

// The footwork as this step leaves it (a phase this step started, the time left after this step's ageing).
ActorSkirmishPhase skirmishPhase(ActorAiCommandContext &ai)
{
    return ai.update().state.skirmishPhase.value_or(ai.actor().runtime.skirmishPhase);
}

float skirmishSecondsLeft(ActorAiCommandContext &ai)
{
    return ai.update().state.skirmishSeconds.value_or(ai.actor().runtime.skirmishSeconds);
}

bool skirmishEvadePhase(ActorSkirmishPhase phase)
{
    return phase == ActorSkirmishPhase::Evade || phase == ActorSkirmishPhase::BackOff
        || phase == ActorSkirmishPhase::Circle;
}

bool skirmishEvading(ActorAiCommandContext &ai)
{
    return skirmishEvadePhase(skirmishPhase(ai)) && skirmishSecondsLeft(ai) > 0.0f;
}

bool hasMoveDirection(const ActorAiFacts &actor)
{
    return std::abs(actor.movement.moveDirectionX) > 0.001f || std::abs(actor.movement.moveDirectionY) > 0.001f;
}

void setSkirmishPhase(ActorAiCommandContext &ai, ActorSkirmishPhase phase, float seconds)
{
    ai.update().state.skirmishPhase = phase;
    ai.update().state.skirmishSeconds = seconds;
}

// The unit direction toward the target turned by angleRadians (counter-clockwise); false at the target.
bool skirmishDirection(const ActorAiFacts &actor, float angleRadians, float &directionX, float &directionY)
{
    const ActorTargetState target = buildActorTargetStateFromFacts(actor);

    if (target.horizontalDistanceToTarget <= 0.01f)
    {
        return false;
    }

    const float yaw = std::atan2(target.deltaY, target.deltaX) + angleRadians;
    directionX = std::cos(yaw);
    directionY = std::sin(yaw);
    return true;
}

// The target's horizontal velocity: the party's (ActorPartyFacts) or the target actor's.
void skirmishTargetVelocity(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, float &velocityX,
    float &velocityY)
{
    const bool party = actor.target.currentKind == ActorAiTargetKind::Party;
    velocityX = party ? frame.party.velocityX : actor.target.currentVelocityX;
    velocityY = party ? frame.party.velocityY : actor.target.currentVelocityY;
}

bool skirmishTargetMoving(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    skirmishTargetVelocity(actor, frame, velocityX, velocityY);
    return length2d(velocityX, velocityY) >= SkirmishTargetMovingSpeed;
}

// The target moves away from the actor: its velocity is within angleRadians of the line from the actor to it.
// targetSpeed: its speed (0 when it does not move).
bool skirmishTargetMovesAway(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, float angleRadians,
    float &targetSpeed)
{
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float directionX = 0.0f;
    float directionY = 0.0f;
    skirmishTargetVelocity(actor, frame, velocityX, velocityY);
    targetSpeed = length2d(velocityX, velocityY);

    if (targetSpeed < SkirmishTargetMovingSpeed || !skirmishDirection(actor, 0.0f, directionX, directionY))
    {
        targetSpeed = targetSpeed < SkirmishTargetMovingSpeed ? 0.0f : targetSpeed;
        return false;
    }

    return (velocityX * directionX + velocityY * directionY) / targetSpeed >= std::cos(angleRadians);
}

float skirmishRunSpeed(const ActorAiFacts &actor)
{
    return movementSpeedForMotion(actor.movement.effectiveMoveSpeed, ActorAiMotionState::Pursuing);
}

// One step along (directionX, directionY) at its running speed times speedShare, still facing its target: a model
// swings over its gait, or plays it backwards while it backpedals.
void AI_SkirmishMove(ActorAiCommandContext &ai, float directionX, float directionY, float speedShare)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorTargetState target = buildActorTargetStateFromFacts(actor);

    ai.setMovementAction(ActorAiMovementAction::Wander);
    ai.setMoveDirection(directionX, directionY);
    ai.setDesiredMovement(directionX, directionY);
    ai.setMeleePursuitActive(false);

    if (target.horizontalDistanceToTarget > 0.01f)
    {
        ai.faceYaw(std::atan2(target.deltaY, target.deltaX));
    }

    ai.update().movementIntent.keepYawWhileMoving = true;
    applyActiveMovementCommit(actor, false, ai.update());
    ai.update().movementIntent.moveSpeed = std::min(skirmishRunSpeed(actor) * speedShare, MaxActorMoveSpeed);
}

void AI_SkirmishStand(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorTargetState target = buildActorTargetStateFromFacts(actor);

    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();

    if (target.horizontalDistanceToTarget > 0.01f)
    {
        ai.faceYaw(std::atan2(target.deltaY, target.deltaX));
    }

    applyActiveMovementCommit(actor, false, ai.update());
}

// A value in [0, 1) from the actor, a counter and a salt. The decision seed's low bits barely move when the counter
// advances by a steady step (the frames between two strikes), so it is mixed through an integer hash first.
float skirmishUnit(uint32_t actorId, uint32_t counter, uint32_t salt)
{
    uint32_t value = mixActorDecisionSeed(actorId, counter, salt);
    value ^= value >> 16;
    value *= 0x7feb352du;
    value ^= value >> 15;
    value *= 0x846ca68bu;
    value ^= value >> 16;
    return float(value & 0xffffffu) / float(0x1000000u);
}

// A roll in [0, 1) for the decision being made now; the salt tells decisions apart.
float skirmishRoll(const ActorAiFacts &actor, uint32_t salt)
{
    return skirmishUnit(actor.actorId, actor.runtime.attackDecisionCount, salt);
}

// How long this attack's evade lasts: evadeSeconds, or a roll up to evadeSecondsMax (the same through the evade).
float skirmishEvadeSeconds(const ActorAiFacts &actor)
{
    const ActorTacticsFacts &tactics = actor.tactics;

    if (tactics.evadeSecondsMax <= tactics.evadeSeconds)
    {
        return tactics.evadeSeconds;
    }

    return tactics.evadeSeconds + (tactics.evadeSecondsMax - tactics.evadeSeconds) * skirmishRoll(actor, 0x5d1e7f43u);
}

// A random side (+1 or -1) for the decision being made now.
int8_t skirmishSide(const ActorAiFacts &actor, uint32_t salt)
{
    return skirmishRoll(actor, salt) < 0.5f ? 1 : -1;
}

// Whether it taunts now (tauntChance, when its model has a taunt to hold for).
bool skirmishTauntRoll(const ActorAiFacts &actor, uint32_t salt)
{
    return actor.tactics.tauntSeconds > 0.0f && skirmishRoll(actor, salt) < actor.tactics.tauntChance;
}

// A taunt: it stands, faces its target and holds still while its model plays its taunt script clip (the world runtimes
// present skirmishPhase Taunt as the `taunt` role).
void AI_SkirmishHoldTaunt(ActorAiCommandContext &ai)
{
    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    ai.setAttackImpactTriggered(false);
    AI_SkirmishStand(ai);
}

void AI_SkirmishStartTaunt(ActorAiCommandContext &ai)
{
    ai.decide(ActorAiDecisionKind::Taunt, nullptr, ai.actor().tactics.tauntChance);
    setSkirmishPhase(ai, ActorSkirmishPhase::Taunt, ai.actor().tactics.tauntSeconds);
    ai.resetAnimationOnChange();
    AI_SkirmishHoldTaunt(ai);
}

// Holds a taunt under way; false, with the phase cleared, once it is over (or when it is not taunting).
bool AI_SkirmishTaunt(ActorAiCommandContext &ai)
{
    if (skirmishPhase(ai) != ActorSkirmishPhase::Taunt)
    {
        return false;
    }

    if (skirmishSecondsLeft(ai) <= 0.0f)
    {
        setSkirmishPhase(ai, ActorSkirmishPhase::None, 0.0f);
        return false;
    }

    AI_SkirmishHoldTaunt(ai);
    return true;
}

// Starts backpedalling straight away from the target, turned 5-35 degrees to a random side.
void AI_SkirmishStartBackpedal(ActorAiCommandContext &ai, ActorSkirmishPhase phase, float seconds)
{
    const ActorAiFacts &actor = ai.actor();
    const float jitter = SkirmishBackpedalMinJitterRadians
        + (SkirmishBackpedalMaxJitterRadians - SkirmishBackpedalMinJitterRadians) * skirmishRoll(actor, 0x6b8b4567u);
    float directionX = 0.0f;
    float directionY = 0.0f;

    if (!skirmishDirection(actor, Pi + jitter * float(skirmishSide(actor, 0x327b23c6u)), directionX, directionY))
    {
        setSkirmishPhase(ai, ActorSkirmishPhase::None, 0.0f);
        AI_SkirmishStand(ai);
        return;
    }

    setSkirmishPhase(ai, phase, seconds);
    ai.update().state.skirmishSide = skirmishSide(actor, 0x643c9869u);
    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.resetAnimationOnChange();
    ai.setActionSeconds(seconds);
    ai.setAttackImpactTriggered(false);
    AI_SkirmishMove(ai, directionX, directionY, SkirmishBackpedalSpeedShare);
}

bool AI_SkirmishEvade(ActorAiCommandContext &ai, bool canPickLine);

// An evade from a target that moves away: it circles the target the whole time, without backpedalling.
void AI_SkirmishStartCircle(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    setSkirmishPhase(ai, ActorSkirmishPhase::Circle, skirmishEvadeSeconds(actor));
    ai.update().state.skirmishSide = skirmishSide(actor, 0x643c9869u);
    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.resetAnimationOnChange();
    ai.setActionSeconds(0.0f);
    ai.setAttackImpactTriggered(false);

    if (!AI_SkirmishEvade(ai, true))
    {
        AI_SkirmishStand(ai);
    }
}

// One step of an evade, circle or back-off: an evade backpedals for its first half, then circles the target; a
// back-off only backpedals and may end in a taunt. canPickLine: the action clock times the circling (false during a
// shot, whose clock it is). False, with the phase cleared (or a taunt begun), once it is over.
bool AI_SkirmishEvade(ActorAiCommandContext &ai, bool canPickLine)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorSkirmishPhase phase = skirmishPhase(ai);
    const float remaining = skirmishSecondsLeft(ai);

    if (!skirmishEvadePhase(phase))
    {
        return false;
    }

    if (remaining <= 0.0f || actor.target.currentEdgeDistance > SkirmishEvadeCancelDistance)
    {
        // MM9's AttackBackpedalDone: a back-off that ran its course may end in a taunt.
        if (phase == ActorSkirmishPhase::BackOff && remaining <= 0.0f && skirmishTauntRoll(actor, 0x0b5ad4ecu))
        {
            setSkirmishPhase(ai, ActorSkirmishPhase::Taunt, actor.tactics.tauntSeconds);
            ai.resetAnimationOnChange();
        }
        else
        {
            setSkirmishPhase(ai, ActorSkirmishPhase::None, 0.0f);
        }

        return false;
    }

    const float halfSeconds = skirmishEvadeSeconds(actor) * 0.5f;
    const bool backpedal = phase == ActorSkirmishPhase::BackOff
        || (phase == ActorSkirmishPhase::Evade && remaining > halfSeconds);

    if (backpedal)
    {
        if (hasMoveDirection(actor))
        {
            AI_SkirmishMove(ai, actor.movement.moveDirectionX, actor.movement.moveDirectionY,
                SkirmishBackpedalSpeedShare);
        }
        else
        {
            AI_SkirmishStand(ai);
        }

        return true;
    }

    // A circle that starts this step, or the first step past an evade's backpedal, picks its line at once.
    const bool phaseStarted = phase != actor.runtime.skirmishPhase;
    const bool startsCircling = phaseStarted || !hasMoveDirection(actor)
        || (phase == ActorSkirmishPhase::Evade && actor.runtime.skirmishSeconds > halfSeconds);
    const float actionSeconds = ai.update().state.actionSeconds.value_or(actor.runtime.actionSeconds);

    if (canPickLine && (startsCircling || actionSeconds <= 0.0f))
    {
        const int8_t side = ai.update().state.skirmishSide.value_or(actor.runtime.skirmishSide);
        float directionX = 0.0f;
        float directionY = 0.0f;

        if (!skirmishDirection(actor, SkirmishCircleAngleRadians * float(side), directionX, directionY))
        {
            setSkirmishPhase(ai, ActorSkirmishPhase::None, 0.0f);
            return false;
        }

        ai.setActionSeconds(SkirmishCircleMinSeconds + (SkirmishCircleMaxSeconds - SkirmishCircleMinSeconds)
            * skirmishUnit(actor.actorId, actor.runtime.pursueDecisionCount, 0x5a17c3e1u));
        ai.setPursueDecisionCount(actor.runtime.pursueDecisionCount + 1);
        AI_SkirmishMove(ai, directionX, directionY, 1.0f);
        return true;
    }

    if (hasMoveDirection(actor))
    {
        AI_SkirmishMove(ai, actor.movement.moveDirectionX, actor.movement.moveDirectionY, 1.0f);
    }
    else
    {
        AI_SkirmishStand(ai);
    }

    return true;
}

// Its footwork as an attack begins (after AI_StartAttack set the attack): it keeps evading and shoots or casts on the
// way; a strike may become a strafe attack when it was moving and its target stands; a shot is fired on the run at a
// distant target.
void AI_SkirmishStartAttack(ActorAiCommandContext &ai, bool abilityIsRanged, float actionSeconds)
{
    const ActorAiFacts &actor = ai.actor();

    if (skirmishEvading(ai) && AI_SkirmishEvade(ai, false))
    {
        return;
    }

    const bool wasMoving = actor.runtime.motionState == ActorAiMotionState::Pursuing && hasMoveDirection(actor);
    setSkirmishPhase(ai, ActorSkirmishPhase::None, 0.0f);

    if (!abilityIsRanged)
    {
        float directionX = 0.0f;
        float directionY = 0.0f;

        const bool strafeEligible = wasMoving && !skirmishTargetMoving(actor, *ai.frame());
        const float strafeRoll = skirmishRoll(actor, 0x1f2e3d4cu);

        if (strafeEligible && ai.update().state.decision)
        {
            ai.update().state.decision->chance = actor.tactics.strafeAttackChance;
            ai.update().state.decision->roll = strafeRoll;
        }

        if (strafeEligible && strafeRoll < actor.tactics.strafeAttackChance
            && skirmishDirection(actor, SkirmishStrafeAttackAngleRadians * float(skirmishSide(actor, 0x2545f491u)),
                directionX, directionY))
        {
            setSkirmishPhase(ai, ActorSkirmishPhase::StrafeAttack, actionSeconds);

            if (ai.update().state.decision)
            {
                ai.update().state.decision->kind = ActorAiDecisionKind::StrafeAttack;
            }

            AI_SkirmishMove(ai, directionX, directionY, SkirmishStrafeWindupSpeedShare);
            return;
        }

        AI_SkirmishStand(ai);
        return;
    }

    const ActorTargetState target = buildActorTargetStateFromFacts(actor);

    if (wasMoving && target.horizontalDistanceToTarget > skirmishRunSpeed(actor) * SkirmishRunningShotMinSeconds)
    {
        AI_SkirmishMove(ai, actor.movement.moveDirectionX, actor.movement.moveDirectionY, 1.0f);
        return;
    }

    AI_SkirmishStand(ai);
}

// Its chasing speed during a strike (MM9's SpeedThrottle), a share of its running speed: beyond 0.9 of its melee range
// it lunges 1.25x faster until the blow lands; nearer, it keeps pace (0.95x) with a target that moves away within 45
// degrees, never faster than it runs.
float skirmishChaseSpeedShare(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, float meleeRange, bool struck)
{
    // An MM9 skirmisher without SpeedThrottle (the Dagrells, profile throttle: false) runs at its own pace.
    if (actor.tactics.mm9Profile && !actor.tactics.mm9Profile->throttle)
    {
        return 1.0f;
    }

    if (actor.target.currentEdgeDistance >= meleeRange * SkirmishThrottleRangeShare)
    {
        return struck ? 1.0f : SkirmishLungeSpeedShare;
    }

    float targetSpeed = 0.0f;

    if (skirmishTargetMovesAway(actor, frame, SkirmishThrottleAngleRadians, targetSpeed))
    {
        return std::min(1.0f, SkirmishThrottleTargetSpeedShare * targetSpeed / std::max(1.0f, skirmishRunSpeed(actor)));
    }

    return 1.0f;
}

// Its footwork while an attack plays: an evade or strafe attack carries on; a shot keeps its run; a strike runs after a
// moving target until it is close, and steps after a standing one only when it leaves reach.
void AI_SkirmishAttackStep(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();

    if (skirmishEvading(ai) && AI_SkirmishEvade(ai, false))
    {
        return;
    }

    const bool struck = ai.update().state.attackImpactTriggered.value_or(actor.runtime.attackImpactTriggered);

    if (actor.runtime.skirmishPhase == ActorSkirmishPhase::StrafeAttack && hasMoveDirection(actor))
    {
        AI_SkirmishMove(ai, actor.movement.moveDirectionX, actor.movement.moveDirectionY,
            struck ? 1.0f : SkirmishStrafeWindupSpeedShare);
        return;
    }

    if (attackAbilityIsRanged(actor.runtime.queuedAttackAbility, actor.stats.attackConstraints))
    {
        if (hasMoveDirection(actor))
        {
            AI_SkirmishMove(ai, actor.movement.moveDirectionX, actor.movement.moveDirectionY, 1.0f);
        }
        else
        {
            AI_SkirmishStand(ai);
        }

        return;
    }

    const ActorAiFrameFacts &frame = *ai.frame();
    const float meleeRange = meleeRangeForTarget(actor, &frame);
    const float edgeDistance = actor.target.currentEdgeDistance;
    const bool chase = skirmishTargetMoving(actor, frame)
        ? edgeDistance > meleeRange * SkirmishMovingChaseStopRangeShare
        : edgeDistance > meleeRange * SkirmishChaseStartRangeShare
            || (hasMoveDirection(actor) && edgeDistance > meleeRange * SkirmishChaseStopRangeShare);
    float directionX = 0.0f;
    float directionY = 0.0f;

    if (chase && skirmishDirection(actor, 0.0f, directionX, directionY))
    {
        AI_SkirmishMove(ai, directionX, directionY, skirmishChaseSpeedShare(actor, frame, meleeRange, struck));
        return;
    }

    AI_SkirmishStand(ai);
}

// After an attack: a strike may end in an evade (evadeChance; it circles a target that moves away, else backpedals
// first) or, from a strafe attack, a short back-off; an evade under way carries on. False when it simply stands, as any
// other actor.
bool AI_SkirmishAttackDone(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();

    if (skirmishEvading(ai))
    {
        ai.setMotionState(ActorAiMotionState::Pursuing);
        ai.setAnimationState(ActorAiAnimationState::Walking);
        ai.resetAnimationOnChange();
        ai.setActionSeconds(0.0f);
        return AI_SkirmishEvade(ai, true);
    }

    const bool strafeAttack = actor.runtime.skirmishPhase == ActorSkirmishPhase::StrafeAttack;
    setSkirmishPhase(ai, ActorSkirmishPhase::None, 0.0f);

    if (attackAbilityIsRanged(actor.runtime.queuedAttackAbility, actor.stats.attackConstraints))
    {
        return false;
    }

    const float evadeRoll = skirmishRoll(actor, 0x7c3a9b21u);

    if (evadeRoll < actor.tactics.evadeChance)
    {
        float targetSpeed = 0.0f;

        if (skirmishTargetMovesAway(actor, *ai.frame(), SkirmishCircleAwayAngleRadians, targetSpeed))
        {
            AI_SkirmishStartCircle(ai);
        }
        else
        {
            AI_SkirmishStartBackpedal(ai, ActorSkirmishPhase::Evade, skirmishEvadeSeconds(actor));
        }

        if (skirmishPhase(ai) == ActorSkirmishPhase::Circle || skirmishPhase(ai) == ActorSkirmishPhase::Evade)
        {
            ai.decide(skirmishPhase(ai) == ActorSkirmishPhase::Circle ? ActorAiDecisionKind::Circle
                : ActorAiDecisionKind::Evade, nullptr, actor.tactics.evadeChance, evadeRoll);
        }

        return true;
    }

    if (strafeAttack && actor.tactics.backOffSeconds > 0.0f)
    {
        AI_SkirmishStartBackpedal(ai, ActorSkirmishPhase::BackOff, actor.tactics.backOffSeconds);

        if (skirmishPhase(ai) == ActorSkirmishPhase::BackOff)
        {
            ai.decide(ActorAiDecisionKind::BackOff, "after_strafe");
        }

        return true;
    }

    return false;
}

// Its footwork before it engages (AI_AttackOrPursue): a taunt or evade under way carries on (an evading actor may still
// shoot or cast: startRangedAttack); it may taunt when it first notices the party; and it holds off a chase until its
// attack will be ready as it arrives (MM9's ShouldRunAfter). False: engage as usual.
// A taunt or evade under way carries on; an evading actor may still shoot or cast (shotStarting: the evade yields this
// step). False when no footwork is under way.
bool AI_SkirmishFootworkUnderWay(ActorAiCommandContext &ai, bool shotStarting)
{
    if (AI_SkirmishTaunt(ai))
    {
        return true;
    }

    // An evade phase that just ran out still comes here to end (a back-off may end in a taunt).
    if (skirmishEvadePhase(skirmishPhase(ai)) && !shotStarting)
    {
        ai.setMotionState(ActorAiMotionState::Pursuing);
        ai.setAnimationState(ActorAiAnimationState::Walking);

        if (AI_SkirmishEvade(ai, true))
        {
            return true;
        }

        // A back-off that ends in a taunt holds from this step.
        if (AI_SkirmishTaunt(ai))
        {
            return true;
        }
    }

    return false;
}

bool AI_SkirmishBeforeEngage(ActorAiCommandContext &ai, const ActorEngagementState &engagement,
    CombatEngageAction action)
{
    const ActorAiFacts &actor = ai.actor();

    if (AI_SkirmishFootworkUnderWay(ai, action == CombatEngageAction::StartRangedAttack))
    {
        return true;
    }

    if (engagement.targetIsParty && engagement.hasDetectedParty && !actor.status.hasDetectedParty
        && skirmishTauntRoll(actor, 0x2c1b3c6du))
    {
        AI_SkirmishStartTaunt(ai);
        return true;
    }

    // It arrives once within melee range, so the run covers only the distance beyond it (none when only the height
    // or the line of sight keeps it out of reach: then it waits out its recovery and steps in).
    const float runDistance = std::max(0.0f, actor.target.currentEdgeDistance - meleeRangeForTarget(actor, ai.frame()));

    if (action == CombatEngageAction::StartMeleePursuit && actor.target.currentCanSense
        && actor.runtime.attackCooldownSeconds * skirmishRunSpeed(actor) > runDistance)
    {
        ai.decide(ActorAiDecisionKind::Throttle);
        ai.setMotionState(ActorAiMotionState::Standing);
        ai.setAnimationState(ActorAiAnimationState::Standing);
        AI_SkirmishStand(ai);
        return true;
    }

    return false;
}

void AI_StartAttack(ActorAiCommandContext &ai, const CombatAbilityChoiceResult &abilityChoice)
{
    const ActorAiFacts &actor = ai.actor();
    const float attackAnimationSeconds = attackAnimationSecondsForAbility(
        actor,
        abilityChoice.ability,
        actor.stats.attackConstraints);

    // Slow's doubled recovery is applied while the cooldown ages, through slowRecoveryMultiplier.
    const AttackStartOutcome attackStart = startAttack(
        actor.actorId,
        abilityChoice.nextAttackDecisionCount,
        abilityChoice.abilityIsRanged,
        attackAnimationSeconds,
        actor.runtime.recoverySeconds);

    ai.setMotionState(ActorAiMotionState::Attacking);
    ai.setQueuedAttackAbility(abilityChoice.ability);
    ai.setAttackCooldownSeconds(attackStart.attackCooldownSeconds);

    // An MM9 monster recovers MM9's way (section 7.2.1): from its clip's end, a cast from its cast with the spell's own
    // recovery, no random factor (real time; turn-based keeps the shared rule).
    if (mm9LoopActive(actor, ai.frame()))
    {
        const bool cast = attackAbilityIsSpell(abilityChoice.ability);
        const Mm9AiProfile &profile = *actor.tactics.mm9Profile;
        const float spellRecovery = abilityChoice.ability == GameplayActorAttackAbility::Spell1
            ? profile.spell1RecoverySeconds
            : abilityChoice.ability == GameplayActorAttackAbility::Spell2 ? profile.spell2RecoverySeconds : 0.0f;
        const float impactLead = attackImpactLeadSecondsForAbility(actor, abilityChoice.ability,
            actor.stats.attackConstraints);
        ai.setAttackCooldownSeconds(mm9AttackStartCooldown(cast, attackStart.actionSeconds,
            attackStart.actionSeconds - impactLead, cast && spellRecovery > 0.0f ? spellRecovery
                : actor.runtime.recoverySeconds));
        if (!ai.update().state.mm9)
        {
            ai.update().state.mm9 = actor.runtime.mm9;
        }

        ai.update().state.mm9->hitRecoveryArmed = false;
        ai.update().state.mm9->hitActionLeftSeconds = 0.0f;
    }
    ai.setActionSeconds(attackStart.actionSeconds);
    ai.setAttackImpactTriggered(false);
    ai.setAnimationState(attackAnimationStateForAbility(abilityChoice.ability, actor.stats.attackConstraints));
    ai.setAnimationTimeTicks(0.0f);
    const ActorAiDecisionKind attackKind = attackAbilityIsSpell(abilityChoice.ability)
        ? ActorAiDecisionKind::AttackSpell
        : abilityChoice.abilityIsRanged ? ActorAiDecisionKind::AttackRanged : ActorAiDecisionKind::AttackMelee;
    ActorAiDecision &decision = ai.decide(attackKind);
    decision.hasAbility = true;
    decision.ability = abilityChoice.ability;

    if (skirmishActive(actor, ai.frame()))
    {
        AI_SkirmishStartAttack(ai, abilityChoice.abilityIsRanged, attackStart.actionSeconds);
    }
    else
    {
        ai.setMovementAction(ActorAiMovementAction::Stand);
        ai.clearMovementDirection();
    }

    // A delayed attack sound plays later on the action clock (applyDelayedAttackSound).
    if (attackSoundLeadSecondsForAbility(actor, abilityChoice.ability, actor.stats.attackConstraints)
        >= attackStart.actionSeconds)
    {
        ActorAudioRequest attackAudio = {};
        attackAudio.kind = ActorAiAudioRequestKind::Attack;
        attackAudio.actorIndex = actor.actorIndex;
        attackAudio.position = actor.movement.position;
        ai.requestAudio(attackAudio);
    }
}

void AI_MeleeAttack(ActorAiCommandContext &ai, const CombatAbilityChoiceResult &abilityChoice)
{
    AI_StartAttack(ai, abilityChoice);
}

void AI_MissileAttack1(ActorAiCommandContext &ai, const CombatAbilityChoiceResult &abilityChoice)
{
    AI_StartAttack(ai, abilityChoice);
}

void AI_MissileAttack2(ActorAiCommandContext &ai, const CombatAbilityChoiceResult &abilityChoice)
{
    AI_StartAttack(ai, abilityChoice);
}

void AI_SpellAttack1(ActorAiCommandContext &ai, const CombatAbilityChoiceResult &abilityChoice)
{
    AI_StartAttack(ai, abilityChoice);
}

void AI_SpellAttack2(ActorAiCommandContext &ai, const CombatAbilityChoiceResult &abilityChoice)
{
    AI_StartAttack(ai, abilityChoice);
}

void AI_Attack(ActorAiCommandContext &ai, const CombatAbilityChoiceResult &abilityChoice)
{
    if (abilityChoice.ability == GameplayActorAttackAbility::Spell1)
    {
        AI_SpellAttack1(ai, abilityChoice);
        return;
    }

    if (abilityChoice.ability == GameplayActorAttackAbility::Spell2)
    {
        AI_SpellAttack2(ai, abilityChoice);
        return;
    }

    if (abilityChoice.abilityIsRanged && abilityChoice.ability == GameplayActorAttackAbility::Attack2)
    {
        AI_MissileAttack2(ai, abilityChoice);
        return;
    }

    if (abilityChoice.abilityIsRanged)
    {
        AI_MissileAttack1(ai, abilityChoice);
        return;
    }

    AI_MeleeAttack(ai, abilityChoice);
}

void AI_PursueByMode(ActorAiCommandContext &ai, PursueActionMode mode, float minimumActionSeconds)
{
    if (mode == PursueActionMode::OffsetShort)
    {
        AI_Pursue2(ai, minimumActionSeconds);
        return;
    }

    if (mode == PursueActionMode::OffsetWide)
    {
        AI_Pursue3(ai, minimumActionSeconds);
        return;
    }

    if (mode == PursueActionMode::RangedOrbit)
    {
        AI_Pursue(ai, PursueActionMode::RangedOrbit, minimumActionSeconds);
        return;
    }

    AI_Pursue1(ai, minimumActionSeconds);
}

bool actorAttackReady(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    if (frame.turnBased.mode == ActorTurnBasedMode::RealTime)
    {
        return actor.runtime.attackCooldownSeconds <= 0.0f;
    }

    // Turn-based actors attack only when the turn engine grants them their queued action.
    const std::vector<size_t> &grants = frame.turnBased.actionGrantActorIndices;
    return std::find(grants.begin(), grants.end(), actor.actorIndex) != grants.end();
}

// Tactics (ActorTacticsFacts, opt-in from world data). Without tactics every helper returns the native result.

// The yaw after one AI step toward desiredYaw: the tactic's traverse rate, easing out near the goal (so a turret
// settles on its target instead of stopping dead), or the native instant turn.
float tacticFacingYaw(const ActorAiFacts &actor, const ActorAiFrameFacts *pFrame, float desiredYaw)
{
    if (actor.tactics.traverseRadiansPerSecond <= 0.0f || pFrame == nullptr)
    {
        return desiredYaw;
    }

    const float stepSeconds = std::max(0.0f, pFrame->fixedStepSeconds);
    const float difference = normalizeAngleRadians(desiredYaw - actor.runtime.yawRadians);
    const float step = std::min(actor.tactics.traverseRadiansPerSecond * stepSeconds,
        std::abs(difference) * (1.0f - std::exp(-stepSeconds / TacticTraverseEaseSeconds)));
    return normalizeAngleRadians(actor.runtime.yawRadians + std::clamp(difference, -step, step));
}

// Toward the target, ahead of it by the tactics' lead (ActorTacticsFacts::aimLead, zero without lead_seconds).
float yawTowardTarget(const ActorAiFacts &actor)
{
    return std::atan2(
        actor.target.currentPosition.y + actor.tactics.aimLead.y - actor.movement.position.y,
        actor.target.currentPosition.x + actor.tactics.aimLead.x - actor.movement.position.x);
}

// A scanning turret (ActorTacticsFacts::scan) that does not fight: it stands, without fidgets, and turns to a target
// it senses but does not engage yet (a friendly turret tracks a drone until it comes within its hostility promotion
// range), else to the facing its scan or the hold of its last aim gives (idleAimActive). False for every other actor.
bool AI_TacticIdleAim(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const bool tracking = actor.tactics.scan.enabled() && actor.tactics.traverseRadiansPerSecond > 0.0f
        && actor.target.currentKind != ActorAiTargetKind::None && actor.target.currentCanSense;

    if (!tracking && !actor.tactics.idleAimActive)
    {
        return false;
    }

    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();
    ai.faceYaw(tacticFacingYaw(actor, ai.frame(), tracking ? yawTowardTarget(actor) : actor.tactics.idleAimYawRadians));
    return true;
}

// A post's leash: true when the actor is already at least the leash from home and the move would take it further.
bool tacticMoveLeavesLeash(const ActorAiFacts &actor, float directionX, float directionY)
{
    const float leash = actor.tactics.holdPost ? actor.tactics.postLeashRadius : 0.0f;

    if (leash <= 0.0f)
    {
        return false;
    }

    const float fromHomeX = actor.movement.position.x - actor.movement.homePosition.x;
    const float fromHomeY = actor.movement.position.y - actor.movement.homePosition.y;
    return fromHomeX * fromHomeX + fromHomeY * fromHomeY >= leash * leash
        && fromHomeX * directionX + fromHomeY * directionY > 0.0f;
}

void AI_TacticStandFacingTarget(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.faceYaw(tacticFacingYaw(actor, ai.frame(), yawTowardTarget(actor)));
    applyActiveMovementCommit(actor, false, ai.update());
}

// Tactics in an engagement, before the native plan is carried out: a turret turns to its target before it fires, a
// ranged band keeps its distance between shots and a post stays on its leash. False leaves the step to the native
// plan.
bool AI_TacticEngage(
    ActorAiCommandContext &ai,
    const CombatAbilityChoiceResult &abilityChoice,
    const CombatEngagePlan &engagePlan)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorTacticsFacts &tactics = actor.tactics;
    const CombatEngageAction action = engagePlan.action;

    if (action == CombatEngageAction::StartRangedAttack || action == CombatEngageAction::StartMeleeAttack)
    {
        if (tactics.traverseRadiansPerSecond <= 0.0f)
        {
            return false;
        }

        const float remaining = std::abs(normalizeAngleRadians(yawTowardTarget(actor) - actor.runtime.yawRadians));

        if (remaining <= std::max(0.0f, tactics.fireToleranceRadians))
        {
            return false;
        }

        AI_TacticStandFacingTarget(ai);
        return true;
    }

    const bool rangedBetweenShots = abilityChoice.abilityIsRanged
        && (action == CombatEngageAction::StandForRangedBlock
            || action == CombatEngageAction::ContinueRangedPursuit
            || action == CombatEngageAction::StartRangedPursuit);

    if (tactics.keepsRangedBand() && rangedBetweenShots && actor.movement.movementAllowed
        && actor.movement.effectiveMoveSpeed > 0.0f)
    {
        const ActorTargetState combatTarget = buildActorTargetStateFromFacts(actor);
        const float distance = combatTarget.horizontalDistanceToTarget;
        const bool hasMoveDirection =
            std::abs(actor.movement.moveDirectionX) > 0.001f || std::abs(actor.movement.moveDirectionY) > 0.001f;
        // A back-off (TacticBackOffSeconds) walks straight away from the target.
        const bool backingOff = hasMoveDirection && distance > 0.01f
            && actor.runtime.actionSeconds <= TacticBackOffSeconds
            && actor.movement.moveDirectionX * combatTarget.deltaX + actor.movement.moveDirectionY * combatTarget.deltaY
                < -0.7f * distance;
        const bool continuing = actor.runtime.actionSeconds > 0.0f
            && actor.runtime.motionState == ActorAiMotionState::Pursuing && hasMoveDirection
            && !tacticMoveLeavesLeash(actor, actor.movement.moveDirectionX, actor.movement.moveDirectionY);
        // Backing off, the actor keeps facing its target and walks (pursuit would hurry).
        const auto backOffPresentation = [&]()
        {
            ai.faceYaw(tacticFacingYaw(actor, ai.frame(), yawTowardTarget(actor)));
            ai.update().movementIntent.keepYawWhileMoving = true;
            applyActiveMovementCommit(actor, false, ai.update());
            ai.update().movementIntent.moveSpeed =
                movementSpeedForMotion(actor.movement.effectiveMoveSpeed, ActorAiMotionState::Wandering);
        };

        if (continuing)
        {
            ai.setMotionState(ActorAiMotionState::Pursuing);
            ai.setAnimationState(ActorAiAnimationState::Walking);
            ai.setMovementAction(backingOff ? ActorAiMovementAction::Wander : ActorAiMovementAction::Pursue);
            ai.setMoveDirection(actor.movement.moveDirectionX, actor.movement.moveDirectionY);
            ai.setDesiredMovement(actor.movement.moveDirectionX, actor.movement.moveDirectionY);

            if (backingOff)
            {
                backOffPresentation();
            }
            else
            {
                applyActiveMovementCommit(actor, false, ai.update());
            }

            return true;
        }

        PursueActionMode mode = PursueActionMode::RangedOrbit;

        if (actor.target.currentEdgeDistance < tactics.rangedMinDistance && distance > 0.01f)
        {
            // Too close: step back, still facing the target (a model walks backwards), at walking speed.
            const float awayX = -combatTarget.deltaX / distance;
            const float awayY = -combatTarget.deltaY / distance;

            if (!tacticMoveLeavesLeash(actor, awayX, awayY))
            {
                ai.setMotionState(ActorAiMotionState::Pursuing);
                ai.setAnimationState(ActorAiAnimationState::Walking);
                ai.resetAnimationOnChange();
                ai.setMovementAction(ActorAiMovementAction::Wander);
                ai.setMoveDirection(awayX, awayY);
                ai.setDesiredMovement(awayX, awayY);
                ai.setActionSeconds(TacticBackOffSeconds);
                ai.setAttackImpactTriggered(false);
                backOffPresentation();
                return true;
            }
        }
        else if (actor.target.currentEdgeDistance > tactics.rangedMaxDistance)
        {
            mode = PursueActionMode::Direct;
        }

        ai.setMotionState(ActorAiMotionState::Pursuing);
        ai.setAnimationState(ActorAiAnimationState::Walking);
        AI_Pursue(ai, mode, 0.0f);

        if (tacticMoveLeavesLeash(actor, ai.update().movementIntent.desiredMoveX,
                ai.update().movementIntent.desiredMoveY))
        {
            ai.update().movementIntent.desiredMoveX = 0.0f;
            ai.update().movementIntent.desiredMoveY = 0.0f;
            ai.update().movementIntent.applyMovement = false;
            ai.setActionSeconds(0.0f);
            AI_TacticStandFacingTarget(ai);
            return true;
        }

        applyActiveMovementCommit(actor, false, ai.update());
        return true;
    }

    const bool pursuing = action == CombatEngageAction::StartMeleePursuit
        || action == CombatEngageAction::ContinueMeleePursuit
        || action == CombatEngageAction::StartRangedPursuit
        || action == CombatEngageAction::ContinueRangedPursuit;

    if (pursuing && tactics.holdPost && tactics.postLeashRadius > 0.0f)
    {
        const bool continuing = action == CombatEngageAction::ContinueMeleePursuit
            || action == CombatEngageAction::ContinueRangedPursuit;
        const ActorTargetState combatTarget = buildActorTargetStateFromFacts(actor);
        const float distance = std::max(combatTarget.horizontalDistanceToTarget, 0.01f);
        const float directionX = continuing ? actor.movement.moveDirectionX : combatTarget.deltaX / distance;
        const float directionY = continuing ? actor.movement.moveDirectionY : combatTarget.deltaY / distance;

        if (tacticMoveLeavesLeash(actor, directionX, directionY))
        {
            AI_TacticStandFacingTarget(ai);
            return true;
        }
    }

    return false;
}

// MM9 walkers (mm9WalkerProfile): BaseCrawl.inc's loop with Range.inc's shots on the native movement, attacks and
// skirmisher footwork (MM9_MONSTER_AI_PLAN.md phase 2, monster_ai/MM9_AI_DATA_AND_SCRIPTS.md sections 3.1-3.4 and 3.8).
// Its decisions follow MM9's rolls (seeded per actor, ActorMm9State::rollCount); movement and collision stay native.

// Salts of its rolls.
constexpr uint32_t Mm9ShotTimerSalt = 0x3c6ef372u;
constexpr uint32_t Mm9ShotRollSalt = 0xa54ff53au;
constexpr uint32_t Mm9SpellRollSalt = 0x510e527fu;
constexpr uint32_t Mm9TauntRollSalt = 0x1f83d9abu;
constexpr uint32_t Mm9RetargetRollSalt = 0x5be0cd19u;
constexpr uint32_t Mm9FlySideSalt = 0x6a09e667u;
constexpr uint32_t Mm9SwoopAngleSalt = 0xbb67ae85u;
constexpr uint32_t Mm9SwoopSideSalt = 0x9e3779b9u;
constexpr uint32_t Mm9ScanTimerSalt = 0x243f6a88u;
constexpr uint32_t Mm9ScanAngleSalt = 0x85a308d3u;
constexpr uint32_t Mm9ScanSideSalt = 0x13198a2eu;
constexpr uint32_t Mm9WanderWaitSalt = 0xa4093822u;
constexpr uint32_t Mm9WanderTimeSalt = 0x299f31d0u;
constexpr uint32_t Mm9WanderAngleSalt = 0x082efa98u;
constexpr uint32_t Mm9WanderSideSalt = 0xec4e6c89u;
constexpr uint32_t Mm9PathMarkerSalt = 0x452821e6u;
constexpr uint32_t Mm9CowerRollSalt = 0x38d01377u;
constexpr uint32_t Mm9RunTurnSalt = 0xbe5466cfu;
constexpr uint32_t Mm9RunTickSalt = 0x34e90c6cu;
constexpr uint32_t Mm9ResurrectDelaySalt = 0xc0ac29b7u;
constexpr uint32_t Mm9SelfRaiseSalt = 0xc97c50ddu;
constexpr uint32_t Mm9RefugeSalt = 0x3f84d5b5u;
constexpr uint32_t Mm9HangFidgetSalt = 0xb5470917u;
// The idle fidget's rolls (their own counter, ActorMm9State::idleRollCount).
constexpr uint32_t Mm9IdleFidgetWaitSalt = 0x6c9e0e8bu;
constexpr uint32_t Mm9FidgetVariantSalt = 0x1b8f6e2du;
// The reposition modifier's rolls (their own counter, ActorMm9State::repositionCount: MM9's rolls keep their sequence).
constexpr uint32_t RepositionBearingSalt = 0x9216d5d9u;
constexpr uint32_t RepositionSideSalt = 0x8979fb1bu;
static_assert(Mm9GuardSearchCount == ActorMm9WorldFacts{}.refugeActorIndices.size());
// A walker that cannot reach its target tries again every 1.5 s, for half a second (MM9 re-checks CanReachTarget).
constexpr float Mm9ReachRetrySeconds = 1.5f;
// A base started late (BaseInit after a spawn-in or a dormant start) looks for a target at its next update (MM9 thinks
// at 10 Hz).
constexpr float Mm9BaseInitSearchSeconds = 0.1f;
constexpr float Mm9ReachAttemptSeconds = 0.5f;

// Its MM9 state as this step leaves it.
ActorMm9State &mm9State(ActorAiCommandContext &ai)
{
    if (!ai.update().state.mm9)
    {
        ai.update().state.mm9 = ai.actor().runtime.mm9;
    }

    return *ai.update().state.mm9;
}

float mm9Roll(const ActorAiFacts &actor, ActorMm9State &state, uint32_t salt)
{
    return mm9Unit(actor.actorId, state.rollCount++, salt);
}

ActorAiDecision mm9Decision(ActorAiDecisionKind kind, ActorAiTargetKind targetKind, size_t targetActorIndex,
    const char *pNote, float chance = -1.0f, float roll = -1.0f)
{
    ActorAiDecision decision = {};
    decision.kind = kind;
    decision.targetKind = targetKind;
    decision.targetActorIndex = targetKind == ActorAiTargetKind::Actor ? targetActorIndex : static_cast<size_t>(-1);
    decision.pNote = pNote;
    decision.chance = chance;
    decision.roll = roll;
    return decision;
}

// Its edge distance to its target as MM9 measures it: edge to edge, so the party's radius too.
float mm9EdgeDistance(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    const float partyRadius = actor.target.currentKind == ActorAiTargetKind::Party ? frame.party.collisionRadius : 0.0f;
    return std::max(0.0f, actor.target.currentEdgeDistance - partyRadius);
}

// Its blow: a melee attack (MM9 strikes with attack 1's damage; OpenYAMM keeps a thrown attack 1 ranged, so a thrower
// strikes with its second attack).
std::optional<GameplayActorAttackAbility> mm9MeleeAbility(const ActorAiFacts &actor)
{
    const GameplayActorAttackConstraintState &constraints = actor.stats.attackConstraints;

    if (!constraints.attack1IsRanged)
    {
        return GameplayActorAttackAbility::Attack1;
    }

    if (!constraints.attack2IsRanged && actor.stats.attack2Damage.diceRolls > 0)
    {
        return GameplayActorAttackAbility::Attack2;
    }

    return std::nullopt;
}

// RangeAttack (MM9_AI_NATIVE_RE.md section 7.2.2): a spell by its spell chances (mm9RangedSpellSlot, spellRoll in
// [0, 1)), else its thrown projectile, else a spell as its only ranged attack. A spell with no chance is never cast.
// None while blind, in Dark Grasp or without a line to the party.
std::optional<GameplayActorAttackAbility> mm9RangedAbility(
    const ActorAiFacts &actor, const ActorAiFrameFacts &frame, float spellRoll)
{
    const GameplayActorAttackConstraintState &constraints = actor.stats.attackConstraints;

    if (constraints.blindActive || constraints.darkGraspActive || !constraints.rangedCommitAllowed)
    {
        return std::nullopt;
    }

    const bool spell1 = actor.stats.hasSpell1 && actor.stats.spell1CastSupported && actor.stats.spell1UseChance > 0
        && monsterSpellIsOkToCast(actor.stats.spell1Name, actor.stats, actor.status, frame.party);
    const bool spell2 = actor.stats.hasSpell2 && actor.stats.spell2CastSupported && actor.stats.spell2UseChance > 0
        && monsterSpellIsOkToCast(actor.stats.spell2Name, actor.stats, actor.status, frame.party);
    const int spellSlot = mm9RangedSpellSlot(
        spell1 ? actor.stats.spell1UseChance : 0, spell2 ? actor.stats.spell2UseChance : 0, spellRoll);

    if (spellSlot == 1)
    {
        return GameplayActorAttackAbility::Spell1;
    }

    if (spellSlot == 2)
    {
        return GameplayActorAttackAbility::Spell2;
    }

    // The physical shot (kind 2) fires Projectile1 and needs attack 2's damage: a row with attack 1 alone never shoots.
    if (constraints.attack1IsRanged && actor.stats.attack2Damage.diceRolls > 0)
    {
        return GameplayActorAttackAbility::Attack1;
    }

    if (constraints.attack2IsRanged)
    {
        return GameplayActorAttackAbility::Attack2;
    }

    if (spell1)
    {
        return GameplayActorAttackAbility::Spell1;
    }

    if (spell2)
    {
        return GameplayActorAttackAbility::Spell2;
    }

    return std::nullopt;
}

bool mm9HasRangedAttack(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    const Mm9AiProfile *pProfile = mm9WalkerProfile(actor);
    return pProfile != nullptr && pProfile->ranged == Mm9AiRanged::Walker && mm9RangedAbility(actor, frame, 1.0f);
}

// Range.inc's RangeAttackRange: its placement's sight less 5 LT, within the engine's ranged reach.
float mm9ActorRangeAttackRange(const ActorAiFacts &actor)
{
    const float sight = actor.movement.mm9Placement ? actor.movement.mm9Placement->sight : Mm9AiPlacement{}.sight;
    const float reach = actor.target.currentKind == ActorAiTargetKind::Party
        ? std::max(MaximumRangedAttackDistance, actor.target.partyAttackReach) : MaximumRangedAttackDistance;
    return mm9RangeAttackRange(sight, reach);
}

// A ranged holder by placement (ranged_type 2 on a Range.inc walker) follows a target it struck; the Evil Sorcerers
// (EvilSorcerer.scr) never run after anyone.
bool mm9HolderFollowsStruckTarget(const ActorAiFacts &actor)
{
    return actor.movement.mm9Placement && actor.movement.mm9Placement->rangedType == 2;
}

// Attack in reach (MM9_AI_NATIVE_RE.md section 7.2.3): always its blow. CanAttack's Att% roll only sets a kind that
// Attack ignores, whatever its script; only a monster holding a ranged weapon prop (profile rangedWeapon) turns its
// Attack into RangeAttack, which shoots or casts by that roll (mm9RangedAbility, as out of reach). A monster without a
// blow shoots or casts.
std::optional<GameplayActorAttackAbility> mm9BlowOrShot(
    const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorMm9State &state)
{
    const std::optional<GameplayActorAttackAbility> melee = mm9MeleeAbility(actor);

    if (melee && !actor.tactics.mm9Profile->rangedWeapon)
    {
        return melee;
    }

    const std::optional<GameplayActorAttackAbility> ranged =
        mm9RangedAbility(actor, frame, mm9Roll(actor, state, Mm9SpellRollSalt));
    return ranged ? ranged : melee;
}

// SetupTarget: it holds the target and its clock restarts. A walker (BaseCrawl.inc) also restarts its shot check and
// doubles its sight and hearing once it has targeted the party; fliers (BaseFly.inc) and turrets (lobber.scr) do not.
void mm9SetUpTarget(const ActorAiFacts &actor, ActorMm9State &state, ActorAiTargetKind kind, size_t actorIndex)
{
    const Mm9AiProfile *pWalker = mm9WalkerProfile(actor);
    state.targetKind = kind;
    state.targetActorIndex = kind == ActorAiTargetKind::Actor ? actorIndex : static_cast<size_t>(-1);
    state.scriptTarget = false;
    state.chaseSeconds = 0.0f;
    state.unseenSeconds = 0.0f;
    state.hasLastSeen = false;
    state.lastSeenSearched = false;

    // DisableWandering (a walk under way stops; the path keeps its marker) and AlertStart: an alert at once, then
    // every g_nRandom seconds (BaseCrawl.inc and BaseFly.inc SetupTarget; a turret alerts by itself).
    if (state.wanderPhase != Mm9WanderPhase::Startup)
    {
        state.wanderPhase = Mm9WanderPhase::Off;
    }

    if (actor.tactics.mm9Profile && actor.tactics.mm9Profile->archetype != Mm9AiArchetype::Turret)
    {
        state.alertSeconds = 0.0f;
    }

    if (pWalker != nullptr)
    {
        state.partyContact = state.partyContact || kind == ActorAiTargetKind::Party;
        state.shotCheckSeconds = mm9ShotCheckSeconds(pWalker->archetype == Mm9AiArchetype::RangedHolder,
            mm9Roll(actor, state, Mm9ShotTimerSalt));
    }
}

// ClearTarget: a flier stops its back-off and swoop (BaseFly.inc), a turret its Aware and starts scanning again
// (lobber.scr TargetSearchOn).
void mm9ClearTarget(ActorMm9State &state)
{
    state.targetKind = ActorAiTargetKind::None;
    state.targetActorIndex = static_cast<size_t>(-1);
    state.scriptTarget = false;
    state.unseenSeconds = 0.0f;
    state.fleeSeconds = 0.0f;
    // BaseRunCancel, AlertStop and EnableWandering: the wander starts again with a wait (rolled at its next idle step).
    state.fleeMode = Mm9FleeMode::None;
    state.hidingPlace = -1;
    state.alertSeconds = -1.0f;

    if (state.wanderPhase != Mm9WanderPhase::Startup)
    {
        state.wanderPhase = Mm9WanderPhase::Waiting;
        state.wanderSeconds = -1.0f;
    }

    state.searchDelaySeconds = Mm9TargetSearchSeconds;
    state.repositionPhase = Mm9RepositionPhase::None;
    state.flightPhase = Mm9FlightPhase::None;
    state.flightSeconds = 0.0f;
    state.swoopAfterShot = false;
    state.backOffRequested = false;
    state.meleeWindowPending = false;
    state.shotChecksArmed = false;
    state.awareSeconds = 0.0f;
    state.scanArmed = false;
    state.scanTurning = false;
}

// lobber.scr FoundTarget and OnDamage: Aware, then the attack check a second after the clip.
void mm9TurretAware(ActorMm9State &state)
{
    state.awareSeconds = Mm9TurretAwareSeconds;
    state.shotCheckSeconds = Mm9TurretAwareSeconds + Mm9TurretAttackCheckSeconds;
    state.scanArmed = false;
    state.scanTurning = false;
}

void mm9StartTaunt(ActorAiFacts &actor)
{
    if (actor.tactics.tauntSeconds > 0.0f)
    {
        actor.runtime.skirmishPhase = ActorSkirmishPhase::Taunt;
        actor.runtime.skirmishSeconds = actor.tactics.tauntSeconds;
    }
}

struct Mm9PreludeResult
{
    std::optional<ActorAiDecision> decision;
    // A decision of the shared layers (a call sent or received, a flight's mode, a resurrection), traced after it.
    std::optional<ActorAiDecision> layerDecision;
    std::optional<ActorMm9Request> request;
    bool tauntStarted = false;
};

// MM9's g_nRandom after a draw: GetRandomInt low, high (inclusive) or GetRandomFloat low, high from a unit roll.
float mm9NoteRandomInt(ActorMm9State &state, float unit, int low, int high)
{
    state.scriptRandom = float(low) + std::floor(std::clamp(unit, 0.0f, 0.999999f) * float(high - low + 1));
    return state.scriptRandom;
}

float mm9NoteRandom(ActorMm9State &state, float value)
{
    state.scriptRandom = value;
    return value;
}

ActorMm9Request &mm9Request(Mm9PreludeResult &result)
{
    if (!result.request)
    {
        result.request = ActorMm9Request{};
    }

    return *result.request;
}

// A hit on a flier (BaseFly.inc OnDamageDone): with no target it takes its attacker; else it switches to whoever hit
// it, its own target too, 50 times in 101 (a switch restarts its clock). Not switching, it backs off at once if it
// cannot attack (not while its pass plays: the pass backs off when it ends). Carrying on (AggressiveStart) or backing
// off cuts a swoop short and leaves FlyRange's swoop flag set (MM9 quirk reproduced: no shot checks until a later swoop
// ends).
void mm9FlierHit(ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorMm9State &state, Mm9PreludeResult &result)
{
    const ActorMm9WorldFacts &world = actor.mm9World;

    if (state.targetKind == ActorAiTargetKind::None)
    {
        mm9SetUpTarget(actor, state, world.attackerKind, world.attackerActorIndex);
        result.decision = mm9Decision(ActorAiDecisionKind::Retarget, world.attackerKind, world.attackerActorIndex,
            "no_target");
        return;
    }

    const float chance = mm9FlierRetargetChance();
    const float roll = mm9Roll(actor, state, Mm9RetargetRollSalt);
    const bool attacking = actor.runtime.motionState == ActorAiMotionState::Attacking;
    bool carriesOn = false;

    if (roll < chance)
    {
        mm9SetUpTarget(actor, state, world.attackerKind, world.attackerActorIndex);
        result.decision = mm9Decision(ActorAiDecisionKind::Retarget, world.attackerKind, world.attackerActorIndex,
            "switch", chance, roll);
        carriesOn = true;
    }
    else
    {
        result.decision = mm9Decision(ActorAiDecisionKind::Retarget, state.targetKind, state.targetActorIndex,
            "keep", chance, roll);
        carriesOn = actorAttackReady(actor, frame);

        if (!carriesOn && !attacking)
        {
            state.backOffRequested = true;
        }
    }

    if (carriesOn && state.flightPhase == Mm9FlightPhase::Swoop)
    {
        state.flightPhase = Mm9FlightPhase::None;
        state.flightSeconds = 0.0f;
    }
}

// A hit on a turret (lobber.scr OnDamage): with no target it takes its attacker (Aware); it never switches.
void mm9TurretHit(ActorAiFacts &actor, ActorMm9State &state, Mm9PreludeResult &result)
{
    const ActorMm9WorldFacts &world = actor.mm9World;

    if (state.targetKind == ActorAiTargetKind::None)
    {
        mm9SetUpTarget(actor, state, world.attackerKind, world.attackerActorIndex);
        mm9TurretAware(state);
        result.decision = mm9Decision(ActorAiDecisionKind::Retarget, world.attackerKind, world.attackerActorIndex,
            "no_target");
        return;
    }

    result.decision = mm9Decision(ActorAiDecisionKind::Retarget, state.targetKind, state.targetActorIndex, "keep");
}

// A hit on a walker (NewTargetCheck): its attacker may become its target. A hit by its own target only counts as one,
// and a fleeing monster does not turn.
void mm9WalkerHit(ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorMm9State &state, bool holdsOffered,
    Mm9PreludeResult &result)
{
    const ActorMm9WorldFacts &world = actor.mm9World;
    const bool attackerIsTarget = world.attackerKind == state.targetKind
        && (state.targetKind != ActorAiTargetKind::Actor || world.attackerActorIndex == state.targetActorIndex);

    // PoliceMan.inc OnDamage: a guard counts the hits of its friend the party; a friend's hit is no reason to fight
    // (IsAttackerValidTarget) until the third makes the party its enemy (AddEnemy Player).
    if (actor.tactics.mm9Profile->archetype == Mm9AiArchetype::Guard
        && world.attackerKind == ActorAiTargetKind::Party && !actor.status.hostileToParty)
    {
        static constexpr std::array<const char *, 3> HitNotes = {"hit 1", "hit 2", "hit 3"};
        state.partyHits = uint8_t(std::min(255, int(state.partyHits) + 1));
        result.layerDecision = mm9Decision(ActorAiDecisionKind::TurnHostile, ActorAiTargetKind::Party,
            static_cast<size_t>(-1), HitNotes[std::min<size_t>(state.partyHits, HitNotes.size()) - 1]);

        if (!mm9GuardTurnsOnParty(state.partyHits))
        {
            return;
        }

        mm9Request(result).turnOnParty = true;
    }

    if (attackerIsTarget || state.fleeMode != Mm9FleeMode::None || state.raiseSeconds > 0.0f
        || state.castSeconds > 0.0f)
    {
        return;
    }

    if (state.targetKind == ActorAiTargetKind::None)
    {
        mm9SetUpTarget(actor, state, world.attackerKind, world.attackerActorIndex);
        result.decision = mm9Decision(ActorAiDecisionKind::Retarget, world.attackerKind,
            world.attackerActorIndex, "no_target");
        return;
    }

    const bool inRange = holdsOffered && actor.target.currentEdgeDistance <= meleeRangeForTarget(actor, &frame);
    const float targetDistance = holdsOffered ? actor.target.currentEdgeDistance : std::numeric_limits<float>::max();
    const float chance = mm9RetargetChance(inRange, targetDistance, world.attackerDistance);
    const float roll = mm9Roll(actor, state, Mm9RetargetRollSalt);
    mm9NoteRandomInt(state, roll, 0, 100);

    if (roll < chance)
    {
        mm9SetUpTarget(actor, state, world.attackerKind, world.attackerActorIndex);
        result.decision = mm9Decision(ActorAiDecisionKind::Retarget, world.attackerKind,
            world.attackerActorIndex, "switch", chance, roll);
    }
    else
    {
        result.decision = mm9Decision(ActorAiDecisionKind::Retarget, state.targetKind,
            state.targetActorIndex, "keep", chance, roll);
    }
}

// The first of its hiding places out of its target's sight (FindHidingPlace), -1 without one.
int mm9UnseenHidingPlace(const ActorAiFacts &actor)
{
    for (size_t place = 0; place < actor.movement.mm9HidingPlaces.size() && place < 8; ++place)
    {
        if ((actor.mm9World.hidingPlacesUnseen & (1u << place)) != 0)
        {
            return int(place);
        }
    }

    return -1;
}

// BaseRunAwayFace: away from its target (standing at from), turned 15-45 degrees (always to the same side: MM9 quirk
// reproduced).
void mm9AimRunAway(const ActorAiFacts &actor, ActorMm9State &state, const GameplayWorldPoint &from)
{
    const float awayX = actor.movement.position.x - from.x;
    const float awayY = actor.movement.position.y - from.y;
    const float turn = mm9RunAwayTurnRadians(mm9Roll(actor, state, Mm9RunTurnSalt));
    const float yaw = (awayX * awayX + awayY * awayY > 0.0001f ? std::atan2(awayY, awayX) : actor.runtime.yawRadians)
        + turn;
    mm9NoteRandom(state, turn * 180.0f / Pi);
    state.flightDirectionX = std::cos(yaw);
    state.flightDirectionY = std::sin(yaw);
}

// BaseRunAway: a monster with a Cower clip cowers in place 10 times in 101; else it runs to a hiding place out of its
// target's sight (BaseRunHide), a townsperson without one to a town guard (NPCBase.inc BaseRunFindHidingPlace: one at
// random of those the world found), or it runs away at an angle (BaseRunRandom) from its target standing at from,
// looking for a hiding place every 1.5 s.
void mm9StartFlight(const ActorAiFacts &actor, ActorMm9State &state, Mm9PreludeResult &result,
    const GameplayWorldPoint &from)
{
    const Mm9AiProfile &profile = *actor.tactics.mm9Profile;
    const ActorMm9WorldFacts &world = actor.mm9World;
    state.sinceFleeSeconds = 0.0f;
    state.refugeActorIndex = static_cast<size_t>(-1);
    state.wanderPhase = state.wanderPhase == Mm9WanderPhase::Startup ? Mm9WanderPhase::Startup : Mm9WanderPhase::Off;

    if (profile.cower)
    {
        const float chance = mm9CowerChance();
        const float roll = mm9Roll(actor, state, Mm9CowerRollSalt);
        mm9NoteRandomInt(state, roll, 0, 100);

        if (roll < chance)
        {
            state.fleeMode = Mm9FleeMode::Cower;
            state.fleeTickSeconds = Mm9CowerTickSeconds;
            result.layerDecision = mm9Decision(ActorAiDecisionKind::Cower, state.targetKind, state.targetActorIndex,
                "start", chance, roll);
            return;
        }
    }

    const int place = mm9UnseenHidingPlace(actor);

    if (place >= 0)
    {
        state.fleeMode = Mm9FleeMode::Hide;
        state.hidingPlace = int8_t(place);
        state.fleeTickSeconds = Mm9HideTickSeconds;
        result.layerDecision = mm9Decision(ActorAiDecisionKind::Hide, state.targetKind, state.targetActorIndex, "run");
        result.layerDecision->marker = place;
        return;
    }

    if (profile.guardRefuge && world.refugeCount > 0)
    {
        const float unit = mm9Roll(actor, state, Mm9RefugeSalt);
        const int pick = mm9PickRefuge(int(world.refugeCount), unit);
        mm9NoteRandomInt(state, unit, 0, int(world.refugeCount) - 1);
        state.fleeMode = Mm9FleeMode::Hide;
        state.hidingPlace = -1;
        state.refugeActorIndex = world.refugeActorIndices[size_t(pick)];
        state.fleeTickSeconds = Mm9HideTickSeconds;
        result.layerDecision =
            mm9Decision(ActorAiDecisionKind::Hide, state.targetKind, state.targetActorIndex, "guard");
        result.layerDecision->marker = int(state.refugeActorIndex);
        return;
    }

    state.fleeMode = Mm9FleeMode::Run;
    state.fleeTickSeconds = Mm9RunAwayFirstTickSeconds;
    state.hideSearchSeconds = Mm9HideTickSeconds;
    mm9AimRunAway(actor, state, from);
}

// BaseRunCancel: the flight ends and the target with it (ClearTarget).
void mm9EndFlight(ActorMm9State &state, Mm9PreludeResult &result, const char *pNote)
{
    result.decision = mm9Decision(ActorAiDecisionKind::GiveUp, state.targetKind, state.targetActorIndex, pNote);
    mm9ClearTarget(state);
}

// ShouldRunAway as BaseShouldRun asks it during a run (the native call, without BaseCrawl.inc's 30 s hold): a
// swimmer's land rule, else the native rule.
bool mm9StillRuns(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, bool holdsOffered)
{
    const ActorMm9WorldFacts &world = actor.mm9World;

    if (actor.tactics.mm9Profile->archetype == Mm9AiArchetype::Swimmer && world.waterKnown)
    {
        return !holdsOffered || mm9SwimmerRunsFrom(world.targetInWater);
    }

    const Mm9AiPlacement placement = actor.movement.mm9Placement.value_or(Mm9AiPlacement{});
    Mm9RunAwayInput input = {};
    input.runner = mm9IsRunner(actor.actorId, placement.runawayChance);
    input.hasHidingPlace = mm9UnseenHidingPlace(actor) >= 0;
    input.currentHp = actor.stats.currentHp;
    input.largestHit = world.largestHit;
    input.targetReachable = !world.targetUnreachable;
    input.hasRangedAttack = input.runner && input.hasHidingPlace && mm9HasRangedAttack(actor, frame);
    return mm9ShouldRunAway(input);
}

// A flight under way (BaseRun.inc): a run re-aims every 0.3-0.8 s calling for help, ends after 15 s (cowering if it
// can) or beyond 1 000 LT of its target, or when ShouldRunAway says no, and looks for a hiding place every 1.5 s; a
// hiding run calls for help and runs on every 1.5 s until it arrives (AI_Mm9Flee); a cower checks every 5 s that its
// target still sees it. A flight never loses its target (BaseRunLostTarget) nor gives up by the clock.
void mm9FlightStep(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorMm9State &state, bool holdsOffered,
    float timerStep, Mm9PreludeResult &result)
{
    state.fleeTickSeconds = std::max(0.0f, state.fleeTickSeconds - timerStep);

    if (state.targetKind == ActorAiTargetKind::None)
    {
        state.fleeMode = Mm9FleeMode::None;
        return;
    }

    if (state.fleeMode == Mm9FleeMode::Cower)
    {
        if (state.fleeTickSeconds <= 0.0f)
        {
            state.fleeTickSeconds = Mm9CowerTickSeconds;

            if (!holdsOffered || !actor.target.currentHasAttackLineOfSight)
            {
                result.layerDecision = mm9Decision(ActorAiDecisionKind::Cower, state.targetKind,
                    state.targetActorIndex, "end");
                mm9EndFlight(state, result, "fled");
            }
        }

        return;
    }

    if (state.fleeMode == Mm9FleeMode::Hide)
    {
        if (state.fleeTickSeconds <= 0.0f)
        {
            state.fleeTickSeconds = Mm9HideTickSeconds;
            ActorMm9Request &request = mm9Request(result);
            request.help = true;
            request.callTargetKind = state.targetKind;
            request.callTargetActorIndex = state.targetActorIndex;
            result.layerDecision = mm9Decision(ActorAiDecisionKind::CallHelp, state.targetKind,
                state.targetActorIndex, "hide");
        }

        return;
    }

    // A run (BaseRunRandom).
    state.hideSearchSeconds = std::max(0.0f, state.hideSearchSeconds - timerStep);

    if (state.hideSearchSeconds <= 0.0f)
    {
        state.hideSearchSeconds = Mm9HideTickSeconds;
        const int place = mm9UnseenHidingPlace(actor);

        if (place >= 0)
        {
            state.fleeMode = Mm9FleeMode::Hide;
            state.hidingPlace = int8_t(place);
            state.fleeTickSeconds = Mm9HideTickSeconds;
            result.layerDecision =
                mm9Decision(ActorAiDecisionKind::Hide, state.targetKind, state.targetActorIndex, "run");
            result.layerDecision->marker = place;
            return;
        }
    }

    if (state.fleeTickSeconds > 0.0f)
    {
        return;
    }

    if (!mm9StillRuns(actor, frame, holdsOffered))
    {
        mm9EndFlight(state, result, "fled");
        return;
    }

    if (state.sinceFleeSeconds > Mm9RunAwayMaxSeconds)
    {
        if (actor.tactics.mm9Profile->cower)
        {
            state.fleeMode = Mm9FleeMode::Cower;
            state.fleeTickSeconds = Mm9CowerTickSeconds;
            result.layerDecision =
                mm9Decision(ActorAiDecisionKind::Cower, state.targetKind, state.targetActorIndex, "start");
            return;
        }

        mm9EndFlight(state, result, "fled");
        return;
    }

    const float runAwayDistance = actor.tactics.mm9Profile->archetype == Mm9AiArchetype::Civilian
        ? Mm9CivilianRunAwayDistance : Mm9RunAwayDistance;

    if (holdsOffered && actor.target.currentDistance > runAwayDistance)
    {
        mm9EndFlight(state, result, "fled");
        return;
    }

    mm9AimRunAway(actor, state, actor.target.currentPosition);
    ActorMm9Request &request = mm9Request(result);
    request.help = true;
    request.callTargetKind = state.targetKind;
    request.callTargetActorIndex = state.targetActorIndex;
    result.layerDecision =
        mm9Decision(ActorAiDecisionKind::CallHelp, state.targetKind, state.targetActorIndex, "run");
    state.fleeTickSeconds = mm9NoteRandom(state, mm9RunAwayTickSeconds(mm9Roll(actor, state, Mm9RunTickSalt)));
}

// NPCBase.inc OnDamage: a townsperson runs from its attacker (RunAway, BaseRunAway): a hiding place of its own out of
// its attacker's sight, a town guard, else away at an angle until its first run tick asks ShouldRunAway (MM9 quirk
// reproduced: without a guard near and a hiding place it runs half a second and stops: only placed runners with a
// hiding place run on). A townsperson whose target is the party ignores the hit (OnDamage exits).
void mm9CivilianHit(ActorAiFacts &actor, ActorMm9State &state, Mm9PreludeResult &result)
{
    const ActorMm9WorldFacts &world = actor.mm9World;

    if (!mm9CivilianRunsFromHit(state.targetKind == ActorAiTargetKind::Party))
    {
        return;
    }

    state.targetKind = world.attackerKind;
    state.targetActorIndex =
        world.attackerKind == ActorAiTargetKind::Actor ? world.attackerActorIndex : static_cast<size_t>(-1);
    state.chaseSeconds = 0.0f;
    state.unseenSeconds = 0.0f;
    state.fleeMode = Mm9FleeMode::None;
    state.hidingPlace = -1;
    result.decision = mm9Decision(ActorAiDecisionKind::FleeDecision, state.targetKind, state.targetActorIndex, "hit");
    mm9StartFlight(actor, state, result, world.attackerPosition);
}

// OnAlert and OnHelp: a friend's alert (while it holds a target too) or help call (only while it holds none) offers
// it the target named. A walker runs NewTargetCheck; a flier reads the alerter, a friend, from an alert (MM9 quirk
// reproduced: it never joins on an alert) and takes a help call's target only without one of its own (BaseFly.inc
// NewTargetCheck, no alert of its own); a turret takes an alert's target without one of its own and ignores help.
void mm9ReceiveCall(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorMm9State &state, bool holdsOffered,
    Mm9PreludeResult &result)
{
    const ActorMm9WorldFacts &world = actor.mm9World;
    const Mm9AiArchetype archetype = actor.tactics.mm9Profile->archetype;
    const ActorAiDecisionKind kind = world.callIsHelp ? ActorAiDecisionKind::Help : ActorAiDecisionKind::Alert;
    const ActorAiTargetKind callKind = world.callTargetKind;
    const size_t callIndex = world.callTargetActorIndex;
    const bool hasTarget = state.targetKind != ActorAiTargetKind::None;
    const bool resurrecting = state.raiseSeconds > 0.0f || state.castSeconds > 0.0f;
    const auto decide = [&](const char *pNote, float chance = -1.0f, float roll = -1.0f)
    {
        result.layerDecision = mm9Decision(kind, callKind, callIndex, pNote, chance, roll);
    };

    // A townsperson hears no calls (NPCBase.inc registers neither OnAlert nor OnHelp).
    if (archetype == Mm9AiArchetype::Civilian)
    {
        return;
    }

    // PoliceMan.inc PoliceAlert and OnHelp: a guard ignores a monster's alert; a fellow guard's alert, or any friend's
    // help call, about its friend the party makes the party its enemy (whatever it holds), then the base runs.
    bool candidateValid = world.callTargetValid;

    if (archetype == Mm9AiArchetype::Guard)
    {
        Mm9PoliceCallInput police = {};
        police.help = world.callIsHelp;
        police.senderIsMonster = world.callFromMonster;
        police.senderIsGuard = world.callFromGuard;
        police.targetIsFriend = callKind == ActorAiTargetKind::Party && !actor.status.hostileToParty;
        const Mm9PoliceCallResult verdict = mm9PoliceCall(police);

        if (verdict.ignored)
        {
            decide("monster");
            return;
        }

        if (verdict.targetBecomesEnemy)
        {
            mm9Request(result).turnOnParty = true;
            candidateValid = true;
            result.decision = mm9Decision(ActorAiDecisionKind::TurnHostile, ActorAiTargetKind::Party,
                static_cast<size_t>(-1), world.callIsHelp ? "help" : "alert");
        }
    }

    // A help call while it holds a target, or a call naming the target it holds: nothing to do (not traced).
    const bool namesItsTarget = hasTarget && callKind == state.targetKind
        && (callKind != ActorAiTargetKind::Actor || callIndex == state.targetActorIndex);

    if ((world.callIsHelp && hasTarget) || callKind == ActorAiTargetKind::None || namesItsTarget)
    {
        return;
    }

    if (archetype == Mm9AiArchetype::Flier)
    {
        if (!world.callIsHelp || !world.callTargetValid || resurrecting)
        {
            decide("ignored");
            return;
        }

        state.targetKind = callKind;
        state.targetActorIndex = callKind == ActorAiTargetKind::Actor ? callIndex : static_cast<size_t>(-1);
        state.chaseSeconds = 0.0f;
        state.unseenSeconds = 0.0f;
        state.wanderPhase = state.wanderPhase == Mm9WanderPhase::Startup ? Mm9WanderPhase::Startup : Mm9WanderPhase::Off;
        decide("take");
        return;
    }

    if (archetype == Mm9AiArchetype::Turret)
    {
        if (world.callIsHelp || hasTarget || !world.callTargetValid)
        {
            decide("ignored");
            return;
        }

        mm9SetUpTarget(actor, state, callKind, callIndex);
        mm9TurretAware(state);
        decide("take");
        return;
    }

    Mm9NewTargetInput input = {};
    input.hasTarget = hasTarget;
    input.candidateIsTarget = namesItsTarget;
    input.candidateValid = candidateValid;
    input.fleeing = state.fleeMode != Mm9FleeMode::None;
    input.resurrecting = resurrecting;
    const Mm9NewTargetOutcome outcome = mm9NewTargetCheck(input);

    if (outcome == Mm9NewTargetOutcome::Invalid)
    {
        decide("ignored");
        return;
    }

    if (outcome == Mm9NewTargetOutcome::Take)
    {
        mm9SetUpTarget(actor, state, callKind, callIndex);
        decide("take");
        return;
    }

    const bool inRange = holdsOffered && actor.target.currentEdgeDistance <= meleeRangeForTarget(actor, &frame);
    const float targetDistance = holdsOffered ? actor.target.currentEdgeDistance : std::numeric_limits<float>::max();
    const float chance = mm9RetargetChance(inRange, targetDistance, world.callTargetDistance);
    const float roll = mm9Roll(actor, state, Mm9RetargetRollSalt);
    mm9NoteRandomInt(state, roll, 0, 100);

    if (roll < chance)
    {
        mm9SetUpTarget(actor, state, callKind, callIndex);
        decide("switch", chance, roll);
        return;
    }

    decide("keep", chance, roll);
}

// AICommon.inc for a living resurrecter: ResurrectMe (a corpse asked: unless busy or fleeing it starts 3-6 s later),
// then DoResurrection (the corpse must still lie dead; attacking or wincing it tries again 0.1 s later; then it faces
// the corpse and plays ResurrectSpell, AI_Mm9Cast) and the spell's DoResurrection key.
void mm9ResurrecterStep(const ActorAiFacts &actor, ActorMm9State &state, float stepSeconds, float timerStep,
    Mm9PreludeResult &result)
{
    const Mm9AiProfile &profile = *actor.tactics.mm9Profile;
    const ActorMm9WorldFacts &world = actor.mm9World;

    if (world.resurrectRequestSerial != state.seenResurrectRequestSerial)
    {
        state.seenResurrectRequestSerial = world.resurrectRequestSerial;

        if (state.resurrectCorpse == static_cast<size_t>(-1) && state.fleeMode == Mm9FleeMode::None
            && world.resurrectRequestCorpse != static_cast<size_t>(-1))
        {
            state.resurrectCorpse = world.resurrectRequestCorpse;
            state.resurrectSeconds =
                mm9NoteRandom(state, mm9ResurrectDelaySeconds(mm9Roll(actor, state, Mm9ResurrectDelaySalt)));
            result.layerDecision = mm9Decision(ActorAiDecisionKind::ResurrectAccept, ActorAiTargetKind::Actor,
                state.resurrectCorpse, nullptr);
            result.layerDecision->seconds = state.resurrectSeconds;
        }
    }

    if (state.castSeconds > 0.0f)
    {
        state.castSeconds = std::max(0.0f, state.castSeconds - stepSeconds);

        if (!state.castRaised && profile.resurrectSpellSeconds - state.castSeconds >= profile.resurrectKeySeconds)
        {
            state.castRaised = true;

            if (world.resurrectCorpseDead)
            {
                mm9Request(result).raiseCorpse = state.resurrectCorpse;
            }
        }

        if (state.castSeconds <= 0.0f)
        {
            state.resurrectCorpse = static_cast<size_t>(-1);
        }

        return;
    }

    if (state.resurrectCorpse == static_cast<size_t>(-1) || state.resurrectSeconds <= 0.0f)
    {
        return;
    }

    state.resurrectSeconds = std::max(0.0f, state.resurrectSeconds - timerStep);

    if (state.resurrectSeconds > 0.0f)
    {
        return;
    }

    const size_t corpse = state.resurrectCorpse;

    if (!world.resurrectCorpseDead)
    {
        state.resurrectCorpse = static_cast<size_t>(-1);
        result.layerDecision = mm9Decision(ActorAiDecisionKind::Resurrect, ActorAiTargetKind::Actor, corpse, "gone");
        return;
    }

    if (actor.runtime.motionState == ActorAiMotionState::Attacking || isStatusLocked(actor))
    {
        state.resurrectSeconds = Mm9ResurrectDelayRetrySeconds;
        return;
    }

    state.castSeconds = profile.resurrectSpellSeconds;
    state.castRaised = false;
    result.layerDecision = mm9Decision(ActorAiDecisionKind::Resurrect, ActorAiTargetKind::Actor, corpse, "cast");
}

// The start of an MM9 monster's step: its timers, the wince the world rolled, losing or giving up its target, a hit
// (the archetype's OnDamage), a friend's alert or help call, noticing a target (OnFoundTarget), a walker's
// ShouldRunAway (a swimmer's land rule first) and the flight it starts, the kill taunt, a resurrecter's request and
// spell, a raised monster's Resurrect clip and the alert tick. Door opening pauses its script timers (BaseDoor.inc
// PauseWait). It updates actor.runtime.mm9 and leaves in actor.target only the target it holds (none while it has
// none).
Mm9PreludeResult AI_Mm9Prelude(ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    Mm9PreludeResult result = {};
    ActorMm9State &state = actor.runtime.mm9;
    const ActorMm9WorldFacts &world = actor.mm9World;
    const Mm9AiProfile &profile = *actor.tactics.mm9Profile;
    const Mm9AiArchetype archetype = profile.archetype;
    const bool flier = archetype == Mm9AiArchetype::Flier;
    const bool turret = archetype == Mm9AiArchetype::Turret;
    const bool civilian = archetype == Mm9AiArchetype::Civilian;
    const bool walker = !flier && !turret && !civilian;
    const float stepSeconds = std::max(0.0f, frame.fixedStepSeconds);
    const float timerStep = state.doorSeconds > 0.0f ? 0.0f : stepSeconds;

    // GreaterDemon.scr: a spawned one (ScriptParams 1) starts hidden, plays its client effect and a second later its
    // Spawn clip, visible, facing the party, then Aware; only then its base runs (BaseInit): until then it registers no
    // handlers, so the hits and calls of the spawn-in are lost, and it looks for a target at its next update (0.1 s).
    if (state.spawnPhase == Mm9SpawnPhase::Unknown)
    {
        state.spawnPhase = profile.spawnIn && actor.movement.mm9Spawned ? Mm9SpawnPhase::Hidden : Mm9SpawnPhase::Done;
        state.spawnSeconds = Mm9SpawnInHiddenSeconds;

        if (state.spawnPhase == Mm9SpawnPhase::Hidden)
        {
            result.layerDecision =
                mm9Decision(ActorAiDecisionKind::SpawnIn, ActorAiTargetKind::None, static_cast<size_t>(-1), "hidden");
        }
    }

    if (state.spawnPhase != Mm9SpawnPhase::Done)
    {
        state.spawnSeconds = std::max(0.0f, state.spawnSeconds - stepSeconds);

        if (state.spawnSeconds <= 0.0f)
        {
            const char *pNote = "begin";

            if (state.spawnPhase == Mm9SpawnPhase::Hidden)
            {
                state.spawnPhase = Mm9SpawnPhase::Spawn;
                state.spawnSeconds = profile.spawnSeconds;
                pNote = "spawn";
            }
            else if (state.spawnPhase == Mm9SpawnPhase::Spawn)
            {
                state.spawnPhase = Mm9SpawnPhase::Aware;
                state.spawnSeconds = profile.awareSeconds;
                pNote = "aware";
            }
            else
            {
                state.spawnPhase = Mm9SpawnPhase::Done;
                state.searchDelaySeconds = Mm9BaseInitSearchSeconds;
            }

            result.decision =
                mm9Decision(ActorAiDecisionKind::SpawnIn, ActorAiTargetKind::None, static_cast<size_t>(-1), pNote);
        }

        if (state.spawnPhase != Mm9SpawnPhase::Done)
        {
            state.seenDamageSerial = world.damageSerial;
            state.seenCallSerial = world.callSerial;
            actor.target.currentKind = ActorAiTargetKind::None;
            actor.target.currentActorIndex = static_cast<size_t>(-1);
            actor.target.currentCanSense = false;
            actor.target.candidates.clear();
            return result;
        }
    }

    // A dormant start the world woke (a hit, or a trigger: evt.WakeActor) wakes now: a hanging one drops and launches
    // at its attacker (FlyingIcky.scr IckyDamage, IckyLaunch); anything else runs its base (MummyAwaken.scr WakeUp:
    // BaseInit), the hit that woke it lost (its OnDamage was WakeUp), and looks for a target at its next update.
    if (state.dormantHeld)
    {
        const bool hang = profile.dormantPose == Mm9AiDormantPose::Hang;
        state.dormantHeld = false;
        state.dormantFidgeting = false;
        state.dormantFidgetWaitSeconds = -1.0f;
        state.wakeSeconds = mm9WakeHoldSeconds(profile.dormantPose, profile.wakeSeconds, profile.wakeupSeconds);
        result.decision =
            mm9Decision(ActorAiDecisionKind::Wake, ActorAiTargetKind::None, static_cast<size_t>(-1), "woken");

        // A lying start gets up first (its Wakeup clip), then its base looks for a target.
        if (!hang)
        {
            state.seenDamageSerial = world.damageSerial;
            state.searchDelaySeconds = state.wakeSeconds + Mm9BaseInitSearchSeconds;
        }
    }

    state.wakeSeconds = std::max(0.0f, state.wakeSeconds - stepSeconds);

    // Phase 5: a behaviour script names the target it holds from now on (self:setTarget; the world offers it from the
    // next step, whatever their relation) or drops it. A passive one (a cut-scene actor), like a placement whose MM9
    // script runs no AI (profile passive), takes no target and answers no hit or call.
    const ActorMm9ScriptFacts &script = actor.behavior.mm9Script;
    const bool passive = script.passive || profile.passive;

    if (script.setTarget && script.targetKind == ActorAiTargetKind::None && state.targetKind != ActorAiTargetKind::None)
    {
        result.decision =
            mm9Decision(ActorAiDecisionKind::GiveUp, state.targetKind, state.targetActorIndex, "script");
        mm9ClearTarget(state);
    }
    else if (script.setTarget && script.targetKind != ActorAiTargetKind::None)
    {
        mm9SetUpTarget(actor, state, script.targetKind, script.targetActorIndex);
        state.scriptTarget = true;
        result.decision =
            mm9Decision(ActorAiDecisionKind::Script, script.targetKind, script.targetActorIndex, "target");
    }

    state.doorSeconds = std::max(0.0f, state.doorSeconds - stepSeconds);
    state.chaseSeconds += stepSeconds;
    state.searchDelaySeconds = std::max(0.0f, state.searchDelaySeconds - stepSeconds);
    state.shotCheckSeconds = std::max(0.0f, state.shotCheckSeconds - timerStep);
    state.sinceShotSeconds = state.sinceShotSeconds >= 0.0f ? state.sinceShotSeconds + stepSeconds : -1.0f;
    state.sinceFleeSeconds += stepSeconds;
    state.reachRetrySeconds = std::max(0.0f, state.reachRetrySeconds - timerStep);
    state.flightSeconds = std::max(0.0f, state.flightSeconds - timerStep);
    state.awareSeconds = std::max(0.0f, state.awareSeconds - stepSeconds);
    state.scanSeconds = std::max(0.0f, state.scanSeconds - timerStep);
    state.alertSeconds = state.alertSeconds > 0.0f ? std::max(0.0f, state.alertSeconds - timerStep) : state.alertSeconds;
    state.repositionSeconds = std::max(0.0f, state.repositionSeconds - stepSeconds);
    state.repositionSearchWaitSeconds = std::max(0.0f, state.repositionSearchWaitSeconds - stepSeconds);
    state.backOffWaitSeconds = std::max(0.0f, state.backOffWaitSeconds - stepSeconds);
    // Its idle this step is decided by AI_Mm9IdleStand (entering idle arms the fidget).
    state.idleLastStep = state.idleThisStep;
    state.idleThisStep = false;
    state.idleFidgetWaitSeconds = std::max(0.0f, state.idleFidgetWaitSeconds - stepSeconds);
    state.fidgetSeconds = std::max(0.0f, state.fidgetSeconds - stepSeconds);
    // A target it holds faces it: no turn back after a talk.
    state.talkTurnBack = state.talkTurnBack && state.targetKind == ActorAiTargetKind::None;

    if (state.wanderPhase == Mm9WanderPhase::Startup || state.wanderPhase == Mm9WanderPhase::Waiting
        || state.wanderPhase == Mm9WanderPhase::Walking)
    {
        state.wanderSeconds = state.wanderSeconds >= 0.0f
            ? std::max(0.0f, state.wanderSeconds - timerStep) : state.wanderSeconds;
    }

    if (world.winceSerial != state.seenWinceSerial)
    {
        state.seenWinceSerial = world.winceSerial;
        result.decision = mm9Decision(ActorAiDecisionKind::Wince, actor.target.currentKind,
            actor.target.currentActorIndex, world.winceRoll < world.winceChance ? "yes" : "no", world.winceChance,
            world.winceRoll);
    }

    const ActorAiTargetKind offeredKind =
        actor.target.currentCanSense ? actor.target.currentKind : ActorAiTargetKind::None;
    const auto holdsOffered = [&]()
    {
        return state.targetKind != ActorAiTargetKind::None && offeredKind == state.targetKind
            && (state.targetKind != ActorAiTargetKind::Actor
                || actor.target.currentActorIndex == state.targetActorIndex);
    };

    // A raised monster plays its Resurrect clip, then attacks the target it died holding (ResurrectDone).
    if (state.raiseSeconds > 0.0f)
    {
        state.raiseSeconds = std::max(0.0f, state.raiseSeconds - stepSeconds);

        if (state.raiseSeconds <= 0.0f && state.deathTargetKind != ActorAiTargetKind::None)
        {
            mm9SetUpTarget(actor, state, state.deathTargetKind, state.deathTargetActorIndex);
            result.layerDecision = mm9Decision(ActorAiDecisionKind::Raised, state.deathTargetKind,
                state.deathTargetActorIndex, "attack");
        }
    }

    // Its target died (also during a flight: OnTargetDead clears it), stayed unseen 8 s (TargetLostTime) or went 30 s
    // without an attack (MAX_CHASE_TIME; lobber.scr counts the same 30 s at its attack check). A flight neither loses
    // its target nor gives up by the clock.
    if (state.targetKind != ActorAiTargetKind::None)
    {
        const char *pReason = nullptr;

        if (world.heldTargetGone)
        {
            pReason = "dead";
        }
        else if (state.fleeMode == Mm9FleeMode::None)
        {
            const bool seen = holdsOffered() && actor.target.currentHasAttackLineOfSight;
            state.unseenSeconds = seen ? 0.0f : state.unseenSeconds + stepSeconds;

            // Where it last saw its target (the reposition modifier looks for a spot that sees there).
            if (seen)
            {
                state.hasLastSeen = true;
                state.lastSeenTarget = actor.target.currentPosition;
                state.lastSeenSearched = false;
            }
            // A script may set its own limit (YanmirBase.scr: 45 s on the party, 15 s on a bug) or none (Dragon.scr).
            const float chaseLimit = script.chaseLimitSeconds < 0.0f ? Mm9MaxChaseSeconds : script.chaseLimitSeconds;
            pReason = state.unseenSeconds >= Mm9TargetLostSeconds ? "lost"
                : chaseLimit > 0.0f && state.chaseSeconds > chaseLimit ? "chase_time" : nullptr;
        }

        if (pReason != nullptr)
        {
            result.decision =
                mm9Decision(ActorAiDecisionKind::GiveUp, state.targetKind, state.targetActorIndex, pReason);

            // OnTargetDead: a walker's own kill earns a taunt half a second later (fliers and turrets only let go).
            if (walker && world.heldTargetGone && world.killSerial != state.seenKillSerial)
            {
                state.killTauntSeconds = Mm9KillTauntDelaySeconds;
            }

            mm9ClearTarget(state);
        }
    }

    state.seenKillSerial = world.killSerial;

    if (state.fleeMode != Mm9FleeMode::None)
    {
        mm9FlightStep(actor, frame, state, holdsOffered(), timerStep, result);
    }

    // A hit (OnDamageDone, after any wince), by the archetype's own rule.
    if (world.damageSerial != state.seenDamageSerial && !isStatusLocked(actor))
    {
        state.seenDamageSerial = world.damageSerial;

        // A passive script (a cut-scene actor) takes no attacker; a turret whose script drives it (Dragon.scr
        // OnDamage) takes its attacker only without a target, plays no Aware clip and alerts no one.
        if (world.attackerKind != ActorAiTargetKind::None && !passive)
        {
            if (turret && script.drivesAttacks)
            {
                const bool none = state.targetKind == ActorAiTargetKind::None;

                if (none)
                {
                    mm9SetUpTarget(actor, state, world.attackerKind, world.attackerActorIndex);
                }

                result.decision = mm9Decision(ActorAiDecisionKind::Retarget, state.targetKind,
                    state.targetActorIndex, none ? "no_target" : "keep");
            }
            else if (civilian)
            {
                mm9CivilianHit(actor, state, result);
            }
            else if (flier)
            {
                mm9FlierHit(actor, frame, state, result);
            }
            else if (turret)
            {
                // lobber.scr OnDamage alerts its friends about any attacker that is not one.
                mm9TurretHit(actor, state, result);
                ActorMm9Request &request = mm9Request(result);
                request.alert = true;
                request.callTargetKind = world.attackerKind;
                request.callTargetActorIndex = world.attackerActorIndex;
            }
            else
            {
                mm9WalkerHit(actor, frame, state, holdsOffered(), result);
            }
        }
    }

    // A friend's alert or help call.
    if (world.callSerial != state.seenCallSerial)
    {
        state.seenCallSerial = world.callSerial;

        if (!passive && !script.ignoresCalls)
        {
            mm9ReceiveCall(actor, frame, state, holdsOffered(), result);
        }
    }

    // OnFoundTarget: the target the world found (the nearest it perceives), once a second at most, not while it
    // resurrects or rises. A walker taunts 40 % of the time, a flier always (FlyRange.inc checks a shot at once), a
    // turret plays its Aware clip and alerts its friends.
    if (!civilian && !passive && state.targetKind == ActorAiTargetKind::None
        && offeredKind != ActorAiTargetKind::None && state.searchDelaySeconds <= 0.0f && state.raiseSeconds <= 0.0f
        && state.castSeconds <= 0.0f)
    {
        mm9SetUpTarget(actor, state, offeredKind, actor.target.currentActorIndex);

        // Dragon.scr OnFoundTarget: SetupNewTarget, the script's attack wait next (no Aware clip, no alert).
        if (turret && script.drivesAttacks)
        {
            result.decision =
                mm9Decision(ActorAiDecisionKind::Detect, offeredKind, actor.target.currentActorIndex, nullptr);
        }
        else if (turret)
        {
            mm9TurretAware(state);
            result.decision = mm9Decision(ActorAiDecisionKind::TauntDetect, offeredKind,
                actor.target.currentActorIndex, "aware");
            ActorMm9Request &request = mm9Request(result);
            request.alert = true;
            request.callTargetKind = offeredKind;
            request.callTargetActorIndex = actor.target.currentActorIndex;
        }
        else if (flier)
        {
            state.shotCheckSeconds = 0.0f;
            state.shotChecksArmed = true;
            result.decision = mm9Decision(ActorAiDecisionKind::TauntDetect, offeredKind,
                actor.target.currentActorIndex, "always");
            mm9StartTaunt(actor);
            result.tauntStarted = actor.tactics.tauntSeconds > 0.0f;
        }
        else
        {
            const float roll = mm9Roll(actor, state, Mm9TauntRollSalt);
            const bool taunt = roll < Mm9AwareChance;
            mm9NoteRandomInt(state, roll, 0, 100);
            result.decision = mm9Decision(taunt ? ActorAiDecisionKind::TauntDetect : ActorAiDecisionKind::Detect,
                offeredKind, actor.target.currentActorIndex, nullptr, Mm9AwareChance, roll);

            if (taunt)
            {
                mm9StartTaunt(actor);
                result.tauntStarted = actor.tactics.tauntSeconds > 0.0f;
            }
        }
    }

    // A walker's ShouldRunAway (native, with BaseCrawl.inc's 30 s hold) while it has a target; Fear is the native
    // flight. A swimmer runs at once from a target that is not in water (BaseSwim.inc, before the 30 s hold).
    if (walker && state.targetKind != ActorAiTargetKind::None && state.fleeMode == Mm9FleeMode::None
        && state.raiseSeconds <= 0.0f && actor.status.spellEffects.fearRemainingSeconds <= 0.0f)
    {
        const Mm9AiPlacement placement = actor.movement.mm9Placement.value_or(Mm9AiPlacement{});

        if (archetype == Mm9AiArchetype::Swimmer && world.waterKnown && holdsOffered()
            && mm9SwimmerRunsFrom(world.targetInWater))
        {
            result.decision =
                mm9Decision(ActorAiDecisionKind::FleeDecision, state.targetKind, state.targetActorIndex, "land");
            mm9StartFlight(actor, state, result, actor.target.currentPosition);
        }
        else
        {
            Mm9RunAwayInput input = {};
            input.runner = mm9IsRunner(actor.actorId, placement.runawayChance);
            input.hasHidingPlace = mm9UnseenHidingPlace(actor) >= 0;
            input.currentHp = actor.stats.currentHp;
            input.largestHit = world.largestHit;
            input.targetReachable = !world.targetUnreachable;
            input.sinceLastFleeSeconds = state.sinceFleeSeconds;
            input.hasRangedAttack = input.runner && input.hasHidingPlace && mm9HasRangedAttack(actor, frame);

            if (mm9ShouldRunAway(input))
            {
                result.decision = mm9Decision(ActorAiDecisionKind::FleeDecision, state.targetKind,
                    state.targetActorIndex, input.largestHit > 0 && input.currentHp <= 2 * input.largestHit
                        ? "hurt" : "unreachable", placement.runawayChance);
                mm9StartFlight(actor, state, result, actor.target.currentPosition);
            }
        }
    }

    if (state.killTauntSeconds > 0.0f)
    {
        state.killTauntSeconds = std::max(0.0f, state.killTauntSeconds - stepSeconds);

        if (state.killTauntSeconds <= 0.0f)
        {
            result.decision = mm9Decision(ActorAiDecisionKind::TauntKill, ActorAiTargetKind::None,
                static_cast<size_t>(-1), nullptr);
            mm9StartTaunt(actor);
            result.tauntStarted = actor.tactics.tauntSeconds > 0.0f;
        }
    }

    // A townsperson never raises anyone (NPCBase.inc runs no AICommon.inc), whatever its Resurrect column says.
    if (profile.resurrecter && !civilian)
    {
        mm9ResurrecterStep(actor, state, stepSeconds, timerStep, result);
    }

    // AlertTick: while it holds a target, an alert when its wait runs out, then another after g_nRandom seconds.
    if (state.alertSeconds == 0.0f)
    {
        if (state.targetKind != ActorAiTargetKind::None)
        {
            ActorMm9Request &request = mm9Request(result);
            request.alert = true;
            request.callTargetKind = state.targetKind;
            request.callTargetActorIndex = state.targetActorIndex;
            ActorAiDecision sent =
                mm9Decision(ActorAiDecisionKind::SendAlert, state.targetKind, state.targetActorIndex, nullptr);
            const float repeat = mm9AlertRepeatSeconds(state.scriptRandom);
            state.alertSeconds = repeat > 0.0f ? repeat : -1.0f;
            sent.seconds = repeat;

            // Traced after the step's other prelude decisions (the detection or the call that set the target up).
            if (result.layerDecision && !result.decision)
            {
                result.decision = result.layerDecision;
            }

            result.layerDecision = sent;
        }
        else
        {
            state.alertSeconds = -1.0f;
        }
    }

    // This step it fights only the target it holds.
    if (!holdsOffered())
    {
        actor.target.currentKind = ActorAiTargetKind::None;
        actor.target.currentActorIndex = static_cast<size_t>(-1);
        actor.target.currentCanSense = false;
        actor.target.candidates.clear();
    }

    return result;
}

// Folds the prelude into the step's update: its state, decisions (traced before the step's own) and requests.
void mergeMm9Prelude(const ActorAiFacts &actor, const Mm9PreludeResult &prelude, ActorAiUpdate &update)
{
    if (!update.state.mm9)
    {
        update.state.mm9 = actor.runtime.mm9;
    }

    if (prelude.tauntStarted && !update.state.skirmishPhase)
    {
        update.state.skirmishPhase = actor.runtime.skirmishPhase;
        update.state.skirmishSeconds = update.state.skirmishSeconds.value_or(actor.runtime.skirmishSeconds);
    }

    if (prelude.request)
    {
        ActorMm9Request merged = update.mm9Request.value_or(ActorMm9Request{});
        const ActorMm9Request &request = *prelude.request;

        if (request.alert || request.help)
        {
            merged.alert = merged.alert || request.alert;
            merged.help = merged.help || request.help;
            merged.callTargetKind = request.callTargetKind;
            merged.callTargetActorIndex = request.callTargetActorIndex;
        }

        merged.raiseCorpse = request.raiseCorpse != static_cast<size_t>(-1) ? request.raiseCorpse : merged.raiseCorpse;
        merged.turnOnParty = merged.turnOnParty || request.turnOnParty;
        update.mm9Request = merged;
    }

    if (prelude.layerDecision && !update.state.layerDecision)
    {
        update.state.layerDecision = prelude.layerDecision;
    }

    if (!prelude.decision)
    {
        return;
    }

    if (update.state.earlierDecision && !update.state.decision)
    {
        update.state.decision = update.state.earlierDecision;
    }

    update.state.earlierDecision = prelude.decision;
}

// It stands facing its target; kind None takes no decision (it keeps the last one).
void AI_Mm9Wait(ActorAiCommandContext &ai, ActorAiDecisionKind kind, const char *pNote = nullptr)
{
    const ActorAiFacts &actor = ai.actor();

    if (kind != ActorAiDecisionKind::None)
    {
        ai.decide(kind, pNote);
    }

    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.faceYaw(tacticFacingYaw(actor, ai.frame(), yawTowardTarget(actor)));
    applyActiveMovementCommit(actor, false, ai.update());
}

bool mm9ChaseUnderWay(const ActorAiFacts &actor)
{
    return actor.runtime.motionState == ActorAiMotionState::Pursuing && actor.runtime.actionSeconds > 0.0f
        && hasMoveDirection(actor);
}

// RunTo its target (straight: MM9 runs at its target or along its rails), or a chase under way runs on.
void AI_Mm9Chase(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    ai.setMeleePursuitActive(true);
    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setAnimationState(ActorAiAnimationState::Walking);

    if (mm9ChaseUnderWay(actor))
    {
        ai.setMovementAction(ActorAiMovementAction::Pursue);
        ai.setMoveDirection(actor.movement.moveDirectionX, actor.movement.moveDirectionY);
        ai.setDesiredMovement(actor.movement.moveDirectionX, actor.movement.moveDirectionY);
    }
    else
    {
        AI_Pursue(ai, PursueActionMode::Direct, 0.0f);
    }

    applyActiveMovementCommit(actor, true, ai.update());
}

// Attack or RangeAttack: its clock restarts (g_nLastAttackTime); a blow postpones the next shot check (Range.inc
// MeleeAttack) and a shot restarts the 5 s pursuit veto. A walker (type 1) fires on the run unless its target is less
// than a second away; a holder (type 2) stops for its shot.
void AI_Mm9StartAttack(ActorAiCommandContext &ai, GameplayActorAttackAbility ability)
{
    const ActorAiFacts &actor = ai.actor();
    const Mm9AiProfile &profile = *mm9WalkerProfile(actor);
    const bool holder = profile.archetype == Mm9AiArchetype::RangedHolder;
    const bool wasMoving = actor.runtime.motionState == ActorAiMotionState::Pursuing && hasMoveDirection(actor);
    ActorMm9State &state = mm9State(ai);
    CombatAbilityChoiceResult choice = {};
    choice.ability = ability;
    choice.nextAttackDecisionCount = actor.runtime.attackDecisionCount + 1;
    choice.abilityIsRanged = attackAbilityIsRanged(ability, actor.stats.attackConstraints);
    choice.abilityIsMelee = !choice.abilityIsRanged;

    state.chaseSeconds = 0.0f;

    if (choice.abilityIsRanged)
    {
        state.sinceShotSeconds = 0.0f;
    }
    else
    {
        state.meleedTarget = true;

        if (profile.ranged == Mm9AiRanged::Walker)
        {
            state.shotCheckSeconds = mm9ShotCheckSeconds(holder, mm9Roll(actor, state, Mm9ShotTimerSalt));
        }
    }

    ai.setAttackDecisionCount(choice.nextAttackDecisionCount);
    ai.setMotionState(ActorAiMotionState::Attacking);
    ai.setAnimationState(attackAnimationStateForAbility(ability, actor.stats.attackConstraints));
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.faceYaw(tacticFacingYaw(actor, ai.frame(), yawTowardTarget(actor)));
    AI_Attack(ai, choice);

    // A skirmisher's own start (AI_SkirmishStartAttack) already fires on the run.
    if (choice.abilityIsRanged && !holder && !skirmishActive(actor, ai.frame()) && wasMoving
        && actor.target.currentEdgeDistance > skirmishRunSpeed(actor) * Mm9ShotStopSeconds)
    {
        AI_SkirmishMove(ai, actor.movement.moveDirectionX, actor.movement.moveDirectionY, 1.0f);
    }
}

// An MM9 walker's engagement (AggressiveTick and CheckRangeTick): the shot check, the blow or point-blank shot in
// range (Att% decides), the holder's place, the reach check, ShouldRunAfter with Range.inc's pursuit veto, the chase.
bool AI_Mm9Engage(ActorAiCommandContext &ai, const ActorEngagementState &engagement)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts &frame = *ai.frame();
    const Mm9AiProfile &profile = *mm9WalkerProfile(actor);
    ActorMm9State &state = mm9State(ai);
    const bool holder = profile.archetype == Mm9AiArchetype::RangedHolder;
    const bool rangeScript = profile.ranged == Mm9AiRanged::Walker;
    const bool ready = actorAttackReady(actor, frame);
    const bool lineOfSight = actor.target.currentHasAttackLineOfSight;
    const float distance = mm9EdgeDistance(actor, frame);
    const float attackRange = profile.attackReach;
    const std::optional<GameplayActorAttackAbility> melee = mm9MeleeAbility(actor);
    const bool canShoot = rangeScript && mm9RangedAbility(actor, frame, 1.0f).has_value();

    ai.setMeleePursuitActive(false);
    ai.resetAnimationOnChange();

    if (AI_SkirmishTaunt(ai))
    {
        return true;
    }

    // CheckRangeTick: every 1-2.5 s (a holder 0.2-0.4 s), outside its attack range and within its range attack range,
    // it shoots by the line to its target (EstimateRangeAttackHit: OpenYAMM knows only a clear line or a blocked one).
    if (canShoot && state.shotCheckSeconds <= 0.0f)
    {
        state.shotCheckSeconds = mm9ShotCheckSeconds(holder, mm9Roll(actor, state, Mm9ShotTimerSalt));

        if (ready && !engagement.inMeleeRange && distance <= mm9ActorRangeAttackRange(actor))
        {
            const float chance = mm9ShotChance(lineOfSight ? Mm9ShotLine::Target : Mm9ShotLine::Blocked);
            const float roll = chance > 0.0f ? mm9Roll(actor, state, Mm9ShotRollSalt) : -1.0f;
            ai.update().state.earlierDecision = mm9Decision(ActorAiDecisionKind::ShotCheck, actor.target.currentKind,
                actor.target.currentActorIndex, lineOfSight ? "clear" : "blocked", chance, roll);

            if (chance > 0.0f && roll < chance)
            {
                AI_Mm9StartAttack(ai, *mm9RangedAbility(actor, frame, mm9Roll(actor, state, Mm9SpellRollSalt)));
                return true;
            }
        }
    }

    if (skirmishActive(actor, &frame) && AI_SkirmishFootworkUnderWay(ai, false))
    {
        return true;
    }

    if (engagement.inMeleeRange)
    {
        if (ready && lineOfSight)
        {
            const std::optional<GameplayActorAttackAbility> ability = mm9BlowOrShot(actor, frame, state);

            if (ability)
            {
                AI_Mm9StartAttack(ai, *ability);
                return true;
            }
        }

        // Not ready: a RunTo under way arrives at 0.95 of its range; then it waits.
        if (!holder && mm9ChaseUnderWay(actor) && distance > attackRange * Mm9RunToRangeShare)
        {
            AI_Mm9Chase(ai);
            return true;
        }

        AI_Mm9Wait(ai, ActorAiDecisionKind::WaitCooldown);
        return true;
    }

    // A ranged holder keeps its place; one by placement follows a target it struck out to 3 x its range.
    if (holder)
    {
        if (state.meleedTarget && distance > attackRange * Mm9HolderFollowRangeMultiple)
        {
            state.meleedTarget = false;
        }

        if (!state.meleedTarget || !mm9HolderFollowsStruckTarget(actor))
        {
            AI_Mm9Wait(ai, ActorAiDecisionKind::Hold);
            return true;
        }
    }

    // CanReachTarget: it stops and waits, trying again now and then.
    if (actor.mm9World.targetUnreachable && !actor.stats.canFly)
    {
        if (state.reachRetrySeconds <= 0.0f)
        {
            state.reachRetrySeconds = Mm9ReachRetrySeconds;
        }

        if (state.reachRetrySeconds <= Mm9ReachRetrySeconds - Mm9ReachAttemptSeconds)
        {
            AI_Mm9Wait(ai, ActorAiDecisionKind::Unreachable);
            return true;
        }
    }

    // MM9's scripts see RecoveryTimeLeft 3.03 times the real time left (section 7.2.1).
    bool runAfter = mm9ShouldRunAfter(ready, mm9ScriptRecoveryTimeLeft(actor.runtime.attackCooldownSeconds), distance,
        skirmishRunSpeed(actor));
    bool vetoed = false;

    // Range.inc's ShouldRunAfter: within its range attack range, 5 s after its last shot and with a clear shot, it does
    // not run after its target (the next shot check shoots).
    if (canShoot && distance < mm9ActorRangeAttackRange(actor))
    {
        if (state.sinceShotSeconds < 0.0f)
        {
            state.sinceShotSeconds = 0.0f;
        }

        if (state.sinceShotSeconds > Mm9MaxRangeAttackIntervalSeconds && ready && lineOfSight)
        {
            runAfter = false;
            vetoed = true;
        }
    }

    if (runAfter)
    {
        AI_Mm9Chase(ai);
        return true;
    }

    // MM9 issues no new RunTo but lets one under way run on.
    if (mm9ChaseUnderWay(actor))
    {
        AI_Mm9Chase(ai);

        if (vetoed)
        {
            ai.decide(ActorAiDecisionKind::PursuitVeto, "running");
        }

        return true;
    }

    AI_Mm9Wait(ai, vetoed ? ActorAiDecisionKind::PursuitVeto : ActorAiDecisionKind::Throttle,
        vetoed ? nullptr : "arrival");
    return true;
}

// While an MM9 crawler's attack plays (BaseCrawl.inc AttackTick): a shot keeps its run; for a blow it runs after a
// moving target beyond 0.95 of its range (it re-chases a target that leaves 0.70, and its RunTo arrives at 0.95, so
// MM9 chases only beyond 0.95), and after a still target only once it is out of range.
void AI_Mm9AttackStep(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts &frame = *ai.frame();

    if (attackAbilityIsRanged(actor.runtime.queuedAttackAbility, actor.stats.attackConstraints))
    {
        if (hasMoveDirection(actor))
        {
            AI_SkirmishMove(ai, actor.movement.moveDirectionX, actor.movement.moveDirectionY, 1.0f);
        }
        else
        {
            AI_SkirmishStand(ai);
        }

        return;
    }

    const float attackRange = mm9WalkerProfile(actor)->attackReach;
    const float distance = mm9EdgeDistance(actor, frame);
    const bool chase = skirmishTargetMoving(actor, frame)
        ? distance > attackRange * Mm9RunToRangeShare
        : distance > attackRange;
    float directionX = 0.0f;
    float directionY = 0.0f;

    if (chase && skirmishDirection(actor, 0.0f, directionX, directionY))
    {
        AI_SkirmishMove(ai, directionX, directionY, 1.0f);
        return;
    }

    AI_SkirmishStand(ai);
}

// MM9 fliers (BaseFly.inc, FlyRange.inc, Banshee.scr; MM9_MONSTER_AI_PLAN.md phase 3, monster_ai/
// MM9_AI_DATA_AND_SCRIPTS.md section 3.5): passes, back-offs upward, swoops and FlyRange's shots on the native flight
// and attacks. Its height comes only from these moves, as in MM9 (no native altitude hold): the chase flies straight
// at its target, a back-off rises, a pass and a swoop fly level.

// Attack or RangeAttack for a flier or a turret: its clock restarts (g_nLastAttackTime); a FlyRange shot (shot) also
// restarts its 2 s gap (g_lastRangeAttack).
void AI_Mm9Strike(ActorAiCommandContext &ai, GameplayActorAttackAbility ability, bool shot)
{
    const ActorAiFacts &actor = ai.actor();
    ActorMm9State &state = mm9State(ai);
    CombatAbilityChoiceResult choice = {};
    choice.ability = ability;
    choice.nextAttackDecisionCount = actor.runtime.attackDecisionCount + 1;
    choice.abilityIsRanged = attackAbilityIsRanged(ability, actor.stats.attackConstraints);
    choice.abilityIsMelee = !choice.abilityIsRanged;
    state.chaseSeconds = 0.0f;

    if (shot)
    {
        state.sinceShotSeconds = 0.0f;
    }

    ai.setAttackDecisionCount(choice.nextAttackDecisionCount);
    ai.setMotionState(ActorAiMotionState::Attacking);
    ai.setAnimationState(attackAnimationStateForAbility(ability, actor.stats.attackConstraints));
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.faceYaw(tacticFacingYaw(actor, ai.frame(), yawTowardTarget(actor)));
    AI_Attack(ai, choice);
}

// One flight step: horizontally along the unit (directionX, directionY) at horizontalShare of its flight speed (its
// pursuit speed) times speedShare, rising by verticalShare of it (sinking when negative), facing faceYawRadians.
void AI_Mm9FlyMove(ActorAiCommandContext &ai, float directionX, float directionY, float horizontalShare,
    float verticalShare, float speedShare, float faceYawRadians)
{
    const ActorAiFacts &actor = ai.actor();
    ai.setMovementAction(ActorAiMovementAction::Wander);
    ai.setMoveDirection(directionX, directionY);
    ai.setDesiredMovement(directionX * horizontalShare, directionY * horizontalShare);
    ai.setMeleePursuitActive(false);
    ai.faceYaw(faceYawRadians);
    ai.update().movementIntent.keepYawWhileMoving = true;
    applyActiveMovementCommit(actor, false, ai.update());
    ai.update().movementIntent.desiredMoveZ = verticalShare;
    ai.update().movementIntent.moveSpeed = std::min(skirmishRunSpeed(actor) * speedShare, MaxActorMoveSpeed);
}

// A back-off under way (BaseFly.inc DoBackoff, re-aimed as it goes): straight away from its target, rising (a
// Banshee less), facing it. A target that flies would keep it level; the party never flies on MM9's maps.
void AI_Mm9FlierBackOffStep(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const Mm9FlierStyle style = mm9FlierStyle(*actor.tactics.mm9Profile);
    float directionX = -std::cos(actor.runtime.yawRadians);
    float directionY = -std::sin(actor.runtime.yawRadians);
    float horizontalShare = 1.0f;
    float verticalShare = 0.0f;
    skirmishDirection(actor, Pi, directionX, directionY);
    mm9FlyBackOffShares(style.backOffRise, false, horizontalShare, verticalShare);
    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    AI_Mm9FlyMove(ai, directionX, directionY, horizontalShare, verticalShare, 1.0f, yawTowardTarget(actor));
}

void AI_Mm9FlierStartBackOff(ActorAiCommandContext &ai, const char *pNote)
{
    const ActorAiFacts &actor = ai.actor();
    ActorMm9State &state = mm9State(ai);
    state.flightPhase = Mm9FlightPhase::BackOff;
    state.flightSeconds = mm9FlierStyle(*actor.tactics.mm9Profile).backOffSeconds;
    state.backOffRequested = false;
    ai.decide(ActorAiDecisionKind::BackOff, pNote);
    ai.setActionSeconds(0.0f);
    ai.setAttackImpactTriggered(false);
    ai.resetAnimationOnChange();
    AI_Mm9FlierBackOffStep(ai);
}

// A swoop under way (BaseFly.inc SwoopIn): level along its line, facing it.
void AI_Mm9FlierSwoopStep(ActorAiCommandContext &ai)
{
    const ActorMm9State &state = mm9State(ai);
    const float directionX = state.flightDirectionX;
    const float directionY = state.flightDirectionY;
    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    AI_Mm9FlyMove(ai, directionX, directionY, 1.0f, 0.0f, 1.0f, std::atan2(directionY, directionX));
}

// SwoopIn: 1 s level flight 30-50 degrees off the line to its target, to a random side. False at its target.
bool AI_Mm9FlierStartSwoop(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    ActorMm9State &state = mm9State(ai);
    const float angleUnit = mm9Roll(actor, state, Mm9SwoopAngleSalt);
    const float angle = mm9SwoopAngleRadians(angleUnit, mm9Roll(actor, state, Mm9SwoopSideSalt));
    float directionX = 0.0f;
    float directionY = 0.0f;

    if (!skirmishDirection(actor, angle, directionX, directionY))
    {
        return false;
    }

    state.flightPhase = Mm9FlightPhase::Swoop;
    state.flightSeconds = Mm9FlySwoopSeconds;
    state.flightDirectionX = directionX;
    state.flightDirectionY = directionY;
    state.swooping = true;
    ai.decide(ActorAiDecisionKind::Swoop, angle > 0.0f ? "left" : "right");
    ai.setActionSeconds(0.0f);
    ai.setAttackImpactTriggered(false);
    ai.resetAnimationOnChange();
    AI_Mm9FlierSwoopStep(ai);
    return true;
}

// FlyRange.inc ShouldRangeAttack, at a check or after a back-off (afterBackOff: its CanRangeAttack routine first wants
// 2 s since its last shot; the checks ask only the native CanRangeAttack, MM9 quirk reproduced). Rolled and traced
// only with a ranged attack at hand, its attack ready and its target within its range attack range; it shoots 61
// times in 101 with a clear shot. A shot closer than 1.1 s of flight, or after a back-off, stops for it; else it
// shoots on the way.
bool AI_Mm9FlierShotCheck(ActorAiCommandContext &ai, bool afterBackOff)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts &frame = *ai.frame();
    ActorMm9State &state = mm9State(ai);
    const float distance = mm9EdgeDistance(actor, frame);

    if (afterBackOff && state.sinceShotSeconds >= 0.0f && state.sinceShotSeconds < Mm9FlyMinShotIntervalSeconds)
    {
        return false;
    }

    if (state.swooping)
    {
        return false;
    }

    if (!actorAttackReady(actor, frame) || !mm9RangedAbility(actor, frame, 1.0f)
        || distance > mm9ActorRangeAttackRange(actor))
    {
        return false;
    }

    const float chance = mm9FlyShotChance();
    const float roll = mm9Roll(actor, state, Mm9ShotRollSalt);
    const bool lineOfSight = actor.target.currentHasAttackLineOfSight;
    ai.update().state.earlierDecision = mm9Decision(ActorAiDecisionKind::ShotCheck, actor.target.currentKind,
        actor.target.currentActorIndex, roll >= chance ? "skip" : lineOfSight ? "clear" : "blocked", chance, roll);

    if (roll >= chance || !lineOfSight)
    {
        return false;
    }

    const bool moving = hasMoveDirection(actor) && actor.runtime.motionState == ActorAiMotionState::Pursuing;
    const bool stops = afterBackOff || distance < skirmishRunSpeed(actor) * Mm9FlyShotStopSeconds;
    state.flightPhase = Mm9FlightPhase::Shot;
    state.flightSeconds = 0.0f;
    state.swoopAfterShot = afterBackOff;
    state.shotChecksArmed = true;
    AI_Mm9Strike(ai, *mm9RangedAbility(actor, frame, mm9Roll(actor, state, Mm9SpellRollSalt)), true);
    float directionX = 0.0f;
    float directionY = 0.0f;

    if (moving && !stops && skirmishDirection(actor, 0.0f, directionX, directionY))
    {
        AI_SkirmishMove(ai, directionX, directionY, 1.0f);
    }

    return true;
}

// A pass under way (BaseFly.inc AttackTick until its blow lands, then on along its line): 45 degrees past its target,
// level, facing it, at 0.8 of its speed (at most 200 LT a second) past a still target; a moving target out of its
// attack range it flies straight at (RunTo).
void AI_Mm9FlierPassStep(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts &frame = *ai.frame();
    const ActorMm9State &state = mm9State(ai);
    const bool moving = skirmishTargetMoving(actor, frame);
    const float speedShare = mm9FlyPassSpeedShare(moving, skirmishRunSpeed(actor));
    const bool struck = ai.update().state.attackImpactTriggered.value_or(actor.runtime.attackImpactTriggered);
    float directionX = 0.0f;
    float directionY = 0.0f;

    if (struck && hasMoveDirection(actor))
    {
        AI_Mm9FlyMove(ai, actor.movement.moveDirectionX, actor.movement.moveDirectionY, 1.0f, 0.0f, speedShare,
            yawTowardTarget(actor));
        return;
    }

    if (!struck && moving && mm9EdgeDistance(actor, frame) >= actor.tactics.mm9Profile->attackReach
        && skirmishDirection(actor, 0.0f, directionX, directionY))
    {
        AI_SkirmishMove(ai, directionX, directionY, 1.0f);
        return;
    }

    if (skirmishDirection(actor, float(state.flightSide) * Mm9FlyPassAngleDegrees * Pi / 180.0f, directionX,
            directionY))
    {
        AI_Mm9FlyMove(ai, directionX, directionY, 1.0f, 0.0f, speedShare, yawTowardTarget(actor));
        return;
    }

    AI_SkirmishStand(ai);
}

// BaseFlyAttack: an attack pass 45 degrees past its target to a random side, with the blow, or by Att% a point-blank
// shot or spell (CanAttack, as the walkers'). A Banshee is undead during it (Banshee.scr GoUndead, traced as its
// melee window; OpenYAMM gives the window no effect).
void AI_Mm9FlierStartPass(ActorAiCommandContext &ai, GameplayActorAttackAbility ability)
{
    const ActorAiFacts &actor = ai.actor();
    ActorMm9State &state = mm9State(ai);
    state.flightSide = mm9Roll(actor, state, Mm9FlySideSalt) < 0.5f ? int8_t(-1) : int8_t(1);
    state.flightPhase = Mm9FlightPhase::Pass;
    state.flightSeconds = 0.0f;
    state.meleeWindowPending = actor.tactics.mm9Profile->meleeWindowSeconds > 0.0f;
    ai.update().state.earlierDecision = mm9Decision(ActorAiDecisionKind::FlyPass, actor.target.currentKind,
        actor.target.currentActorIndex, state.flightSide > 0 ? "left" : "right");
    AI_Mm9Strike(ai, ability, false);
    AI_Mm9FlierPassStep(ai);
}

// While its attack plays: a pass flies on (a Banshee's melee window traced), a shot on its way or holding still.
void AI_Mm9FlierAttackStep(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    ActorMm9State &state = mm9State(ai);

    if (state.meleeWindowPending)
    {
        state.meleeWindowPending = false;
        ai.decide(ActorAiDecisionKind::MeleeWindow, "undead");
    }

    if (state.flightPhase == Mm9FlightPhase::Pass)
    {
        AI_Mm9FlierPassStep(ai);
        return;
    }

    float directionX = 0.0f;
    float directionY = 0.0f;

    if (state.flightPhase == Mm9FlightPhase::Shot && hasMoveDirection(actor)
        && skirmishDirection(actor, 0.0f, directionX, directionY))
    {
        AI_SkirmishMove(ai, directionX, directionY, 1.0f);
        return;
    }

    AI_SkirmishStand(ai);
}

// Its attack is over: a pass backs off (BaseFlyAttackDone; a Banshee is no longer undead), a shot after a back-off
// swoops in (RangeAttackDone), and FlyRange's check restarts after a shot. False when it simply carries on.
bool AI_Mm9FlierAttackDone(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    ActorMm9State &state = mm9State(ai);
    const Mm9FlightPhase phase = state.flightPhase;
    state.flightPhase = Mm9FlightPhase::None;
    state.meleeWindowPending = false;

    if (phase == Mm9FlightPhase::Pass)
    {
        ai.setMotionState(ActorAiMotionState::Pursuing);
        AI_Mm9FlierStartBackOff(ai, "up");
        return true;
    }

    if (phase != Mm9FlightPhase::Shot)
    {
        return false;
    }

    state.shotCheckSeconds = mm9FlyShotCheckSeconds(mm9Roll(actor, state, Mm9ShotTimerSalt));

    if (!state.swoopAfterShot)
    {
        return false;
    }

    state.swoopAfterShot = false;
    ai.setMotionState(ActorAiMotionState::Pursuing);

    // RangeAttackDone's SwoopIn: a Banshee's goes straight to SwoopDone (its swoop flag clears).
    if (!mm9FlierStyle(*actor.tactics.mm9Profile).swoops)
    {
        state.swooping = false;
        return false;
    }

    return AI_Mm9FlierStartSwoop(ai);
}

// A flier's step with its target (BaseFly.inc AggressiveTick, FlyRange.inc's checks): its back-off and swoop under
// way, then in its attack range a pass when its attack is ready, else a back-off (its clock restarts: MM9 quirk
// reproduced, a flier waiting in range never gives up), else the chase straight at its target.
bool AI_Mm9FlierEngage(ActorAiCommandContext &ai, const ActorEngagementState &engagement)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts &frame = *ai.frame();
    const Mm9AiProfile &profile = *actor.tactics.mm9Profile;
    const Mm9FlierStyle style = mm9FlierStyle(profile);
    const bool rangeScript = profile.ranged == Mm9AiRanged::Flier;
    ActorMm9State &state = mm9State(ai);

    ai.setMeleePursuitActive(false);
    ai.resetAnimationOnChange();

    if (AI_SkirmishTaunt(ai))
    {
        return true;
    }

    // A pass or shot cut short (a stun, a status) is over.
    if (state.flightPhase == Mm9FlightPhase::Pass || state.flightPhase == Mm9FlightPhase::Shot)
    {
        state.flightPhase = Mm9FlightPhase::None;
        state.meleeWindowPending = false;
    }

    // A hit while it could not attack backs it off at once (Backoff), cutting a swoop short (its flag stays set).
    if (state.backOffRequested)
    {
        AI_Mm9FlierStartBackOff(ai, "up hit");
        return true;
    }

    // FlyRange's check every 0.3-1.3 s once armed (MM9 quirk reproduced: a flier that took its target from a hit checks
    // none until its first swoop ends), never while its swoop flag is set or it backs off.
    if (rangeScript && state.shotChecksArmed && state.shotCheckSeconds <= 0.0f)
    {
        state.shotCheckSeconds = mm9FlyShotCheckSeconds(mm9Roll(actor, state, Mm9ShotTimerSalt));

        if (state.flightPhase != Mm9FlightPhase::BackOff && AI_Mm9FlierShotCheck(ai, false))
        {
            return true;
        }
    }

    if (state.flightPhase == Mm9FlightPhase::BackOff)
    {
        if (state.flightSeconds > 0.0f)
        {
            AI_Mm9FlierBackOffStep(ai);
            return true;
        }

        // BackoffDone: FlyRange may shoot first (and swoop after); else it swoops in (alerting its friends first:
        // phase 4), a Banshee straight back to its aggressive tick.
        state.flightPhase = Mm9FlightPhase::None;

        if (rangeScript && AI_Mm9FlierShotCheck(ai, true))
        {
            return true;
        }

        if (style.swoops && AI_Mm9FlierStartSwoop(ai))
        {
            return true;
        }

        // SwoopDone at once (a Banshee's SwoopIn): its swoop flag clears and FlyRange's check restarts.
        state.swooping = false;

        if (rangeScript)
        {
            state.shotCheckSeconds = mm9FlyShotCheckSeconds(mm9Roll(actor, state, Mm9ShotTimerSalt));
            state.shotChecksArmed = true;
        }
    }

    if (state.flightPhase == Mm9FlightPhase::Swoop)
    {
        if (state.flightSeconds > 0.0f)
        {
            AI_Mm9FlierSwoopStep(ai);
            return true;
        }

        // SwoopDone: aggressive again; FlyRange's check restarts.
        state.flightPhase = Mm9FlightPhase::None;
        state.swooping = false;

        if (rangeScript)
        {
            state.shotCheckSeconds = mm9FlyShotCheckSeconds(mm9Roll(actor, state, Mm9ShotTimerSalt));
            state.shotChecksArmed = true;
        }
    }

    if (engagement.inMeleeRange)
    {
        if (actorAttackReady(actor, frame))
        {
            const std::optional<GameplayActorAttackAbility> ability = mm9BlowOrShot(actor, frame, state);

            if (ability)
            {
                AI_Mm9FlierStartPass(ai, *ability);
                return true;
            }
        }

        state.chaseSeconds = 0.0f;
        AI_Mm9FlierStartBackOff(ai, "up not_ready");
        return true;
    }

    AI_Mm9Chase(ai);
    return true;
}

// MM9 turrets (lobber.scr: the Lobbers; MM9_MONSTER_AI_PLAN.md phase 3): rooted, they scan by turning, play Aware on a
// target, then check every second: a pod while they can lob, else a shot within range.

// lobber.scr AttackCheck, every second after its Aware: a pod while it can lob (CanLob: attack ready, fewer than five
// pods alive), else, with its attack ready and its target within its range attack range, a shot (without a clear
// shot only 26 times in 101). It faces its target meanwhile.
bool AI_Mm9TurretEngage(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts &frame = *ai.frame();
    const Mm9AiProfile &profile = *actor.tactics.mm9Profile;
    ActorMm9State &state = mm9State(ai);

    ai.setMeleePursuitActive(false);
    ai.resetAnimationOnChange();

    // Between its checks it stands facing its target (its Aware clip first).
    if (state.shotCheckSeconds > 0.0f)
    {
        AI_Mm9Wait(ai, state.awareSeconds > 0.0f ? ActorAiDecisionKind::Hold : ActorAiDecisionKind::None, "aware");
        return true;
    }

    state.shotCheckSeconds = Mm9TurretAttackCheckSeconds;
    const bool ready = actorAttackReady(actor, frame);

    if (profile.podLaunchMonsterId != 0 && mm9TurretCanLob(ready, actor.mm9World.livePods))
    {
        const GameplayActorAttackAbility ability = actor.stats.attackConstraints.attack1IsRanged
            || !actor.stats.attackConstraints.attack2IsRanged ? GameplayActorAttackAbility::Attack1
            : GameplayActorAttackAbility::Attack2;
        state.podLaunchPending = true;
        AI_Mm9Strike(ai, ability, false);
        ai.decide(ActorAiDecisionKind::PodLaunch);
        return true;
    }

    if (!ready)
    {
        AI_Mm9Wait(ai, ActorAiDecisionKind::WaitCooldown);
        return true;
    }

    if (mm9EdgeDistance(actor, frame) > mm9ActorRangeAttackRange(actor))
    {
        AI_Mm9Wait(ai, ActorAiDecisionKind::Hold, "out_of_range");
        return true;
    }

    const bool lineOfSight = actor.target.currentHasAttackLineOfSight;
    const float chance = mm9TurretShotChance(lineOfSight);
    const float roll = chance < 1.0f ? mm9Roll(actor, state, Mm9ShotRollSalt) : -1.0f;
    ai.update().state.earlierDecision = mm9Decision(ActorAiDecisionKind::ShotCheck, actor.target.currentKind,
        actor.target.currentActorIndex, lineOfSight ? "clear" : "blocked", chance, roll);
    // OpenYAMM has a ranged attack at hand only with a line to its target: a blind shot finds none.
    const std::optional<GameplayActorAttackAbility> ranged =
        roll < chance ? mm9RangedAbility(actor, frame, mm9Roll(actor, state, Mm9SpellRollSalt)) : std::nullopt;

    if (!ranged)
    {
        AI_Mm9Wait(ai, ActorAiDecisionKind::Hold);
        return true;
    }

    AI_Mm9Strike(ai, *ranged, true);
    return true;
}

// Phase 5: a monster whose behaviour script picks its attacks (Dragon.scr; ActorMm9ScriptFacts::drivesAttacks). It
// holds and faces its target, turning at the script's rate (FaceObject), and starts an attack only when the script
// names one and its attack is ready (else the attack is dropped: note not_ready, and the script tries again).
bool AI_Mm9ScriptedEngage(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts &frame = *ai.frame();
    const ActorMm9ScriptFacts &script = actor.behavior.mm9Script;
    const float desiredYaw = yawTowardTarget(actor);
    const float turnStep = script.turnRadiansPerSecond * std::max(0.0f, frame.fixedStepSeconds);
    const float difference = normalizeAngleRadians(desiredYaw - actor.runtime.yawRadians);
    const float yaw = script.turnRadiansPerSecond <= 0.0f || std::abs(difference) <= turnStep ? desiredYaw
        : normalizeAngleRadians(actor.runtime.yawRadians + (difference > 0.0f ? turnStep : -turnStep));

    ai.setMeleePursuitActive(false);
    ai.resetAnimationOnChange();

    if (script.attack && actorAttackReady(actor, frame))
    {
        ai.update().state.earlierDecision = mm9Decision(ActorAiDecisionKind::Script, actor.target.currentKind,
            actor.target.currentActorIndex, "attack");
        AI_Mm9Strike(ai, *script.attack, attackAbilityIsRanged(*script.attack, actor.stats.attackConstraints));
        ai.faceYaw(yaw);
        return true;
    }

    AI_Mm9Wait(ai, script.attack ? ActorAiDecisionKind::Script : ActorAiDecisionKind::Hold,
        script.attack ? "not_ready" : "script");
    ai.faceYaw(yaw);
    return true;
}

// lobber.scr TargetSearchOn: with no target a turret waits 5-15 s, then turns 20-120 degrees to a side (at 180 degrees
// a second), and again.
void AI_Mm9TurretIdle(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts &frame = *ai.frame();
    ActorMm9State &state = mm9State(ai);

    if (!state.scanArmed)
    {
        state.scanArmed = true;
        state.scanSeconds = mm9TurretScanSeconds(mm9Roll(actor, state, Mm9ScanTimerSalt));
    }
    else if (state.scanSeconds <= 0.0f)
    {
        const float angleUnit = mm9Roll(actor, state, Mm9ScanAngleSalt);
        const float turn = mm9TurretScanTurnRadians(angleUnit, mm9Roll(actor, state, Mm9ScanSideSalt));
        state.scanYawRadians = normalizeAngleRadians(actor.runtime.yawRadians + turn);
        state.scanTurning = true;
        state.scanSeconds = mm9TurretScanSeconds(mm9Roll(actor, state, Mm9ScanTimerSalt));
        ai.decide(ActorAiDecisionKind::Scan, turn > 0.0f ? "left" : "right");
    }

    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();

    if (state.scanTurning)
    {
        const float step = Mm9TurretScanTurnRadiansPerSecond * std::max(0.0f, frame.fixedStepSeconds);
        const float difference = normalizeAngleRadians(state.scanYawRadians - actor.runtime.yawRadians);

        if (std::abs(difference) <= step)
        {
            ai.faceYaw(state.scanYawRadians);
            state.scanTurning = false;
        }
        else
        {
            ai.faceYaw(normalizeAngleRadians(actor.runtime.yawRadians + (difference > 0.0f ? step : -step)));
        }
    }

    applyActiveMovementCommit(actor, false, ai.update());
}

// The layers every MM9 archetype shares (MM9_MONSTER_AI_PLAN.md phase 4a; monster_ai/MM9_AI_DATA_AND_SCRIPTS.md
// sections 3.7-3.10): the wander layer, the flight's movement, a resurrecter's spell, a raised monster's rise, a corpse
// asking to be raised, and doors.

// A marker counts as reached within 1 LT of the edges (WalkTo range 1; MM9's markers have a 12 LT radius).
constexpr float Mm9MarkerRadius = 12.0f * 2.56f;

float mm9Distance2d(const GameplayWorldPoint &from, float x, float y)
{
    return length2d(x - from.x, y - from.y);
}

// It stands idle (AIBase::SetAnimState and the idle think, MM9_AMBIENT_ANIMATION.md section 2.1): entering idle arms
// its fidget 5-12 s later; when that comes it plays one fidget clip, picked uniformly among its model's
// (ActorRuntimeFacts::fidgetClips), once, then idles again with a fresh wait. Only idle runs the timer: a walk, a fight
// or any other state arms it anew when the actor returns to idle.
void AI_Mm9IdleStand(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    ActorMm9State &state = mm9State(ai);
    state.idleThisStep = true;
    ai.setActionSeconds(0.0f);

    // NPCBase.inc OnRUDEExit: after a talk it turns back to the facing it had, at 180 degrees a second.
    if (state.talkTurnBack)
    {
        const float turn = Pi * (ai.frame() != nullptr ? std::max(0.0f, ai.frame()->fixedStepSeconds) : 0.0f);
        const float left = std::remainder(state.talkYawRadians - actor.runtime.yawRadians, 2.0f * Pi);

        if (std::abs(left) <= turn)
        {
            ai.faceYaw(state.talkYawRadians);
            state.talkTurnBack = false;
        }
        else
        {
            ai.faceYaw(normalizeAngleRadians(actor.runtime.yawRadians + std::copysign(turn, left)));
        }
    }

    if (!state.idleLastStep || (state.fidgetVariant >= 0 && state.fidgetSeconds <= 0.0f))
    {
        state.fidgetVariant = -1;
        state.fidgetSeconds = 0.0f;
        state.idleFidgetWaitSeconds = mm9IdleFidgetWaitSeconds(
            mm9Unit(actor.actorId, state.idleRollCount++, Mm9IdleFidgetWaitSalt));
        AI_Stand(ai);
        return;
    }

    if (state.fidgetVariant >= 0)
    {
        AI_HoldIdle(ai);
        return;
    }

    if (state.idleFidgetWaitSeconds > 0.0f)
    {
        AI_Stand(ai);
        return;
    }

    // SetState(fidget, -1): a model without fidget variants plays its one fidget (the sprite's length, or the clip's,
    // which the presentation plays to its end).
    const ActorFidgetClips &clips = actor.runtime.fidgetClips;
    const int variant = mm9FidgetVariant(
        mm9Unit(actor.actorId, state.idleRollCount++, Mm9FidgetVariantSalt), clips.count);
    state.fidgetVariant = int8_t(variant);
    state.fidgetSeconds = clips.count > 0 ? clips.seconds[size_t(variant)] : actor.runtime.boredAnimationSeconds;
    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Bored);
    ai.setAnimationTimeTicks(0.0f);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();
    ActorAiDecision &decision = ai.decide(ActorAiDecisionKind::Fidget, "idle");
    decision.variant = variant;
    decision.seconds = state.fidgetSeconds;

    if (actorBoredSoundRoll(actor.actorId, actor.runtime.idleDecisionCount))
    {
        ActorAudioRequest boredAudio = {};
        boredAudio.kind = ActorAiAudioRequestKind::Bored;
        boredAudio.actorIndex = actor.actorIndex;
        boredAudio.position = actor.movement.position;
        ai.requestAudio(boredAudio);
    }

    ai.setIdleDecisionCount(actor.runtime.idleDecisionCount + 1);
}

// One step of a wander walk along (directionX, directionY), facing it, at its walking speed.
void AI_Mm9WanderMove(ActorAiCommandContext &ai, float directionX, float directionY)
{
    mm9State(ai).talkTurnBack = false;
    ai.faceYaw(std::atan2(directionY, directionX));
    ai.setActionSeconds(0.0f);
    AI_RandomMove(ai, directionX, directionY);
}

// RunTo or WalkTo a point (a marker, a hiding place): MM9 steers along its rails, OpenYAMM along the path planner's
// route, so the move is a pursuit of the point (motionState sets its pace: a walk or a run).
void AI_Mm9MoveTo(ActorAiCommandContext &ai, const GameplayWorldPoint &point, ActorAiMotionState motionState)
{
    const ActorAiFacts &actor = ai.actor();
    // A walk faces its way: no turn back after a talk (NPCBase.inc OnRUDEExit walks to its marker again).
    mm9State(ai).talkTurnBack = false;
    const float deltaX = point.x - actor.movement.position.x;
    const float deltaY = point.y - actor.movement.position.y;
    const float distance = std::max(0.001f, length2d(deltaX, deltaY));
    ai.setMotionState(motionState);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.resetAnimationOnChange();
    ai.setMovementAction(ActorAiMovementAction::Pursue);
    ai.setMoveDirection(deltaX / distance, deltaY / distance);
    ai.setDesiredMovement(deltaX / distance, deltaY / distance);
    ai.faceYaw(std::atan2(deltaY, deltaX));
    ai.setActionSeconds(0.0f);
    ai.setMeleePursuitActive(true);
}

// The point a move to a point heads for: the step's movement intent aims at it instead of the actor's target.
void applyMm9MoveTarget(ActorAiUpdate &update, const ActorAiFacts &actor, const GameplayWorldPoint &point)
{
    update.movementIntent.targetPosition = point;
    update.movementIntent.targetEdgeDistance =
        length2d(point.x - actor.movement.position.x, point.y - actor.movement.position.y);
    update.movementIntent.inMeleeRange = false;
    update.movementIntent.meleePursuitActive = true;
}

// BaseWander.inc for a monster holding no target: a second after it appears its placement's wander starts; it waits
// WanderWaitMin-Max (3-8 s), then walks its marker path (WalkTo the next marker, then waits again) or aimlessly
// (turns 15-180 degrees, or toward where it started once beyond its leash, and walks WanderTimeMin-Max). Beyond its
// leash it stops until the walk's time runs out; a walk stopped by a wall waits and then turns less (15-90 degrees).
// After a fight the wander starts again where it stands with a wait, and a path goes on to the marker after the one it
// was walking to (MM9 quirk reproduced: BaseWanderStop forgets the marker, the next walk takes the next one).
std::optional<GameplayWorldPoint> AI_Mm9Idle(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    ActorMm9State &state = mm9State(ai);
    const Mm9AiPlacement placement = actor.movement.mm9Placement.value_or(Mm9AiPlacement{});
    const int pathCount = int(actor.movement.mm9PathPoints.size());
    const bool path = placement.wander == Mm9AiWanderMode::Path && pathCount >= 2;
    const bool aimless = placement.wander == Mm9AiWanderMode::Aimless
        || (placement.wander == Mm9AiWanderMode::Path && !path);
    const bool canWalk = actor.movement.movementAllowed && actor.movement.effectiveMoveSpeed > 0.0f;

    if (state.wanderPhase == Mm9WanderPhase::Startup && state.wanderSeconds <= 0.0f)
    {
        state.wanderPhase = path || aimless ? Mm9WanderPhase::Waiting : Mm9WanderPhase::Off;
        state.wanderSeconds = -1.0f;
    }

    if (!canWalk || (!path && !aimless) || state.wanderPhase == Mm9WanderPhase::Off
        || state.wanderPhase == Mm9WanderPhase::Startup)
    {
        AI_Mm9IdleStand(ai);
        return std::nullopt;
    }

    const auto markerPoint = [&]()
    {
        const std::array<int32_t, 3> &point =
            actor.movement.mm9PathPoints[size_t(std::clamp(int(state.pathMarker), 0, pathCount - 1))];
        return GameplayWorldPoint{float(point[0]), float(point[1]), float(point[2])};
    };

    const auto startWait = [&]()
    {
        float wait = mm9NoteRandom(state, mm9WanderSeconds(placement.wanderWaitMinSeconds,
            placement.wanderWaitMaxSeconds, mm9Roll(actor, state, Mm9WanderWaitSalt)));

        // BaseWanderStart: a wait below 0.2 s starts the walk at once.
        if (wait < 0.2f)
        {
            wait = 0.0f;
        }

        state.wanderPhase = Mm9WanderPhase::Waiting;
        state.wanderSeconds = wait;
        ActorAiDecision &decision = ai.decide(ActorAiDecisionKind::WanderWait, path ? "path" : "aimless");
        decision.seconds = wait;
    };

    if (state.wanderPhase == Mm9WanderPhase::Waiting && state.wanderSeconds < 0.0f)
    {
        startWait();
    }

    if (state.wanderPhase == Mm9WanderPhase::Waiting && state.wanderSeconds <= 0.0f)
    {
        if (path)
        {
            const float unit = mm9Roll(actor, state, Mm9PathMarkerSalt);
            state.pathMarker = int16_t(state.pathFirst ? mm9FirstPathMarker(pathCount, placement.pathRandom, unit)
                : mm9NextPathMarker(state.pathMarker, pathCount, placement.pathRandom, unit));
            state.pathFirst = false;
            state.wanderPhase = Mm9WanderPhase::ToMarker;
            ActorAiDecision &decision = ai.decide(ActorAiDecisionKind::Patrol);
            decision.marker = state.pathMarker;
            AI_Mm9MoveTo(ai, markerPoint(), ActorAiMotionState::Wandering);
            return markerPoint();
        }
        else
        {
            // BaseWanderPickRandomDir, then BaseWanderStartWalking.
            const float deltaHomeX = actor.movement.homePosition.x - actor.movement.position.x;
            const float deltaHomeY = actor.movement.homePosition.y - actor.movement.position.y;
            const bool home = mm9BeyondLeash(deltaHomeX, deltaHomeY, placement.wanderLeash);
            float yaw = actor.runtime.yawRadians;

            if (home)
            {
                yaw = std::atan2(deltaHomeY, deltaHomeX);
            }
            else
            {
                const float angleUnit = mm9Roll(actor, state, Mm9WanderAngleSalt);
                const float turn = mm9WanderTurnRadians(state.wanderObstacle, angleUnit,
                    mm9Roll(actor, state, Mm9WanderSideSalt));
                mm9NoteRandom(state, turn * 180.0f / Pi);
                yaw = normalizeAngleRadians(yaw + turn);
            }

            state.wanderObstacle = false;
            state.wanderHalted = false;
            state.flightDirectionX = std::cos(yaw);
            state.flightDirectionY = std::sin(yaw);
            state.wanderSeconds = mm9NoteRandom(state, mm9WanderSeconds(placement.wanderTimeMinSeconds,
                placement.wanderTimeMaxSeconds, mm9Roll(actor, state, Mm9WanderTimeSalt)));
            state.wanderPhase = Mm9WanderPhase::Walking;
            ActorAiDecision &decision = ai.decide(home ? ActorAiDecisionKind::Leash : ActorAiDecisionKind::Wander,
                home ? "home" : "aimless");
            decision.seconds = state.wanderSeconds;
            AI_Mm9WanderMove(ai, state.flightDirectionX, state.flightDirectionY);
            return std::nullopt;
        }
    }

    if (state.wanderPhase == Mm9WanderPhase::Waiting)
    {
        AI_Mm9IdleStand(ai);
        return std::nullopt;
    }

    if (state.wanderPhase == Mm9WanderPhase::ToMarker)
    {
        const GameplayWorldPoint point = markerPoint();

        if (mm9Distance2d(actor.movement.position, point.x, point.y)
            <= float(actor.stats.radius) + Mm9MarkerRadius + Mm9WanderMarkerRange)
        {
            ActorAiDecision &reached = ai.decide(ActorAiDecisionKind::MarkerReached);
            reached.marker = state.pathMarker;
            ai.update().state.earlierDecision = reached;
            AI_Stand(ai);
            startWait();
            return std::nullopt;
        }

        AI_Mm9MoveTo(ai, point, ActorAiMotionState::Wandering);
        return point;
    }

    // Walking aimlessly.
    if (state.wanderSeconds <= 0.0f)
    {
        AI_Stand(ai);
        startWait();
        return std::nullopt;
    }

    if (state.wanderHalted)
    {
        AI_Mm9IdleStand(ai);
        return std::nullopt;
    }

    const float deltaHomeX = actor.movement.homePosition.x - actor.movement.position.x;
    const float deltaHomeY = actor.movement.homePosition.y - actor.movement.position.y;
    const bool facingHome = deltaHomeX * state.flightDirectionX + deltaHomeY * state.flightDirectionY > 0.0f;

    // BaseWanderLeashCheck: beyond its leash it stops (a walk home runs on).
    if (!facingHome && mm9BeyondLeash(deltaHomeX, deltaHomeY, placement.wanderLeash))
    {
        state.wanderHalted = true;
        ai.decide(ActorAiDecisionKind::Leash, "stop");
        AI_Stand(ai);
        return std::nullopt;
    }

    // The wall stopped it (the movement step cleared its walk): BaseWanderObstacle turns it away and waits.
    if (actor.runtime.motionState == ActorAiMotionState::Wandering && !hasMoveDirection(actor))
    {
        state.wanderObstacle = true;
        ai.faceYaw(normalizeAngleRadians(actor.runtime.yawRadians + Pi));
        AI_Stand(ai);
        startWait();
        return std::nullopt;
    }

    AI_Mm9WanderMove(ai, state.flightDirectionX, state.flightDirectionY);
    return std::nullopt;
}

// A flight's movement (BaseRun.inc): a run along the direction its last tick chose, a run to its hiding place (on
// arrival it stops, turns around, calls for help and the flight ends: BaseRunHideArrival), or a cower in place.
void AI_Mm9Flee(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    ActorMm9State &state = mm9State(ai);

    if (state.fleeMode == Mm9FleeMode::Cower)
    {
        AI_Stand(ai);
        applyActiveMovementCommit(actor, false, ai.update());
        return;
    }

    // A townsperson's refuge is the guard it runs to (RunTo the guard: it arrives touching it), where the world says it
    // stands now (the candidates' places the step it chose one).
    const ActorMm9WorldFacts &world = actor.mm9World;
    const bool refuge = state.fleeMode == Mm9FleeMode::Hide && state.refugeActorIndex != static_cast<size_t>(-1);
    std::optional<GameplayWorldPoint> refugePoint;
    float refugeRadius = 0.0f;

    if (refuge && world.refugeActorIndex == state.refugeActorIndex)
    {
        refugePoint = world.refugePosition;
        refugeRadius = world.refugeRadius;
    }

    for (size_t candidate = 0; refuge && !refugePoint && candidate < world.refugeCount; ++candidate)
    {
        if (world.refugeActorIndices[candidate] == state.refugeActorIndex)
        {
            refugePoint = world.refugePositions[candidate];
            refugeRadius = world.refugeRadii[candidate];
        }
    }

    if (refuge && !refugePoint)
    {
        AI_Stand(ai);
        applyActiveMovementCommit(actor, false, ai.update());
        return;
    }

    if (refuge || (state.fleeMode == Mm9FleeMode::Hide && state.hidingPlace >= 0
        && size_t(state.hidingPlace) < actor.movement.mm9HidingPlaces.size()))
    {
        const GameplayWorldPoint point = refuge ? *refugePoint : GameplayWorldPoint{
            float(actor.movement.mm9HidingPlaces[size_t(state.hidingPlace)][0]),
            float(actor.movement.mm9HidingPlaces[size_t(state.hidingPlace)][1]),
            float(actor.movement.mm9HidingPlaces[size_t(state.hidingPlace)][2])};
        const float deltaX = point.x - actor.movement.position.x;
        const float deltaY = point.y - actor.movement.position.y;
        const float distance = length2d(deltaX, deltaY);
        const float arrival = refuge ? float(actor.stats.radius) + refugeRadius + Mm9WanderMarkerRange
            : float(actor.stats.radius) + Mm9MarkerRadius + Mm9WanderMarkerRange;

        if (distance <= arrival)
        {
            ActorMm9Request request = ai.update().mm9Request.value_or(ActorMm9Request{});
            request.help = true;
            request.callTargetKind = state.targetKind;
            request.callTargetActorIndex = state.targetActorIndex;
            ai.update().mm9Request = request;
            ActorAiDecision arrived =
                mm9Decision(ActorAiDecisionKind::Hide, state.targetKind, state.targetActorIndex, "arrived");
            arrived.marker = refuge ? int(state.refugeActorIndex) : int(state.hidingPlace);
            ai.update().state.layerDecision = arrived;
            ai.decide(ActorAiDecisionKind::GiveUp, "fled");
            mm9ClearTarget(state);
            AI_Stand(ai);
            ai.faceYaw(normalizeAngleRadians(actor.runtime.yawRadians + Pi));
            applyActiveMovementCommit(actor, false, ai.update());
            return;
        }

        ai.decide(ActorAiDecisionKind::Flee, refuge ? "guard" : "hide");
        AI_Mm9MoveTo(ai, point, ActorAiMotionState::Fleeing);
        applyActiveMovementCommit(actor, false, ai.update());
        applyMm9MoveTarget(ai.update(), actor, point);
        return;
    }

    // A run along the direction its last tick chose (BaseRunAwayFace).
    const float directionX = state.flightDirectionX;
    const float directionY = state.flightDirectionY;
    ai.decide(ActorAiDecisionKind::Flee, "run");
    ai.setMotionState(ActorAiMotionState::Fleeing);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.resetAnimationOnChange();
    ai.setMovementAction(ActorAiMovementAction::Flee);
    ai.setMoveDirection(directionX, directionY);
    ai.setDesiredMovement(directionX, directionY);
    ai.faceYaw(std::atan2(directionY, directionX));
    ai.setActionSeconds(0.0f);
    applyActiveMovementCommit(actor, false, ai.update());
}

// It stands still facing yawRadians: a resurrecter's ResurrectSpell (facing its corpse), a raised monster's Resurrect
// clip, a monster waiting for a door to open. The world plays the clip.
void AI_Mm9HoldStill(ActorAiCommandContext &ai, std::optional<float> yawRadians)
{
    const ActorAiFacts &actor = ai.actor();
    AI_Stand(ai);

    if (yawRadians)
    {
        ai.faceYaw(*yawRadians);
    }

    applyActiveMovementCommit(actor, false, ai.update());
}

// BaseDoor.inc BD_OnDoor: walking, running or flying into a closed AI-triggerable door within 45 degrees of facing it,
// it stops, faces the door, opens it and pauses its timers for the door's open time, then carries on.
bool AI_Mm9Door(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorMm9WorldFacts &world = actor.mm9World;
    ActorMm9State &state = mm9State(ai);
    const float doorYaw = std::atan2(-world.doorNormalY, -world.doorNormalX);

    if (state.doorSeconds > 0.0f)
    {
        AI_Mm9HoldStill(ai, doorYaw);
        return true;
    }

    // The world reports the door only when a move of its own ran into it (walking, running or flying).
    if (!world.doorAhead
        || !mm9DoorAhead(std::cos(actor.runtime.yawRadians), std::sin(actor.runtime.yawRadians), world.doorNormalX,
            world.doorNormalY))
    {
        return false;
    }

    state.doorSeconds = world.doorOpenSeconds;
    ActorMm9Request request = ai.update().mm9Request.value_or(ActorMm9Request{});
    request.openDoorId = world.doorId;
    ai.update().mm9Request = request;
    ActorAiDecision &decision = ai.decide(ActorAiDecisionKind::OpenDoor);
    decision.marker = int(world.doorId);
    decision.seconds = world.doorOpenSeconds;
    AI_Mm9HoldStill(ai, doorYaw);
    return true;
}

// FlyingIcky.scr IckyLaunch: woken from hanging it drops (MoveDir down at 100 LT/s) while its Launch clip plays.
void AI_Mm9Launch(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const float yaw = actor.runtime.yawRadians;
    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    AI_Mm9FlyMove(ai, std::cos(yaw), std::sin(yaw), 0.0f, -1.0f, 1.0f, yaw);
    ai.update().movementIntent.moveSpeed = Mm9LaunchDropSpeed;
}

// A reposition decision against the target it holds (also while the world does not offer it: out of sight and
// hearing).
ActorAiDecision &repositionDecide(ActorAiCommandContext &ai, const ActorMm9State &state, ActorAiDecisionKind kind,
    const char *pNote)
{
    ActorAiDecision &decision = ai.decide(kind, pNote);
    decision.targetKind = state.targetKind;
    decision.targetActorIndex = state.targetActorIndex;
    return decision;
}

// It stands: facing its target when it is offered, else where it looks.
void AI_RepositionHold(ActorAiCommandContext &ai)
{
    if (ai.actor().target.currentKind != ActorAiTargetKind::None)
    {
        AI_Mm9Wait(ai, ActorAiDecisionKind::None);
        return;
    }

    AI_Stand(ai);
    applyActiveMovementCommit(ai.actor(), false, ai.update());
}

// Asks the world to test these spots (ActorMm9Request::reposition); it answers at the next step.
void requestRepositionQuery(ActorAiCommandContext &ai, const ActorRepositionQuery &query)
{
    ActorMm9Request request = ai.update().mm9Request.value_or(ActorMm9Request{});
    request.reposition = query;
    ai.update().mm9Request = request;
}

// The reposition modifier (ActorTacticsFacts::reposition, ActorRepositionRules.h; an OpenYAMM addition, not MM9) on an
// MM9 ranged holder. With its target unseen for lost_sight_seconds it asks the world for a spot within its leash that
// sees where it last saw the target (it does not know where the target went) and walks there (at its run), else back
// to its post; it stops on the way once it sees the target, and its next shot check comes at once. A spot reached
// without the target in sight ends the searches for that place: its own perception finds the target or loses it. A target rushing it (outside its reach) makes it backpedal to a spot the world
// found room for, then shoot or cast. True: it moves or waits this step; false: the loop carries on (AI_Mm9Engage).
bool AI_Mm9Reposition(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts *pFrame = ai.frame();
    const Mm9AiProfile *pProfile = mm9WalkerProfile(actor);

    if (pFrame == nullptr || !actor.tactics.reposition || pProfile == nullptr
        || pProfile->archetype != Mm9AiArchetype::RangedHolder)
    {
        return false;
    }

    const RepositionModifier &settings = *actor.tactics.reposition;
    const ActorMm9WorldFacts &world = actor.mm9World;
    ActorMm9State &state = mm9State(ai);

    // No target, a flight, or no way to move: nothing to do (a back-off under way stops).
    if (state.targetKind == ActorAiTargetKind::None || state.fleeMode != Mm9FleeMode::None
        || !actor.movement.movementAllowed || actor.movement.effectiveMoveSpeed <= 0.0f)
    {
        if (state.repositionPhase == Mm9RepositionPhase::BackingOff)
        {
            setSkirmishPhase(ai, ActorSkirmishPhase::None, 0.0f);
        }

        state.repositionPhase = Mm9RepositionPhase::None;
        return false;
    }

    // A skirmisher's own footwork (an evade or a taunt after a blow) runs first.
    if (state.repositionPhase != Mm9RepositionPhase::BackingOff && skirmishPhase(ai) != ActorSkirmishPhase::None
        && skirmishSecondsLeft(ai) > 0.0f)
    {
        return false;
    }

    const GameplayWorldPoint &position = actor.movement.position;
    const GameplayWorldPoint &post = actor.movement.homePosition;
    const bool offered = actor.target.currentKind != ActorAiTargetKind::None;
    const bool seen = offered && actor.target.currentHasAttackLineOfSight;
    // The spot itself is what sees the target: it walks onto it (its post likewise).
    const float arrival = RepositionArrivalDistance;
    const float runSpeed = skirmishRunSpeed(actor);
    const float backpedalSpeed = std::max(1.0f, runSpeed * SkirmishBackpedalSpeedShare);
    bool backOffStarting = false;

    // The world's answer to the query out.
    if ((state.repositionPhase == Mm9RepositionPhase::SightQuery
            || state.repositionPhase == Mm9RepositionPhase::BackOffQuery)
        && world.repositionSerial != state.seenRepositionSerial)
    {
        state.seenRepositionSerial = world.repositionSerial;
        const bool backOff = state.repositionPhase == Mm9RepositionPhase::BackOffQuery;
        ActorAiDecision *pDecision = nullptr;

        if (world.repositionFound)
        {
            state.repositionSpot = world.repositionSpot;

            if (backOff)
            {
                state.repositionPhase = Mm9RepositionPhase::BackingOff;
                state.repositionSeconds = repositionDistance2d(position, world.repositionSpot) / backpedalSpeed;
                setSkirmishPhase(ai, ActorSkirmishPhase::BackOff, state.repositionSeconds);
                pDecision = &repositionDecide(ai, state, ActorAiDecisionKind::BackOffRush, "spot");
                backOffStarting = true;
            }
            else
            {
                state.repositionPhase = Mm9RepositionPhase::Moving;
                state.repositionSeconds =
                    repositionWalkLimitSeconds(repositionDistance2d(position, world.repositionSpot), runSpeed);
                pDecision = &repositionDecide(ai, state, ActorAiDecisionKind::Reposition, "spot");
            }

            pDecision->hasPoint = true;
            pDecision->point = world.repositionSpot;
        }
        else if (backOff)
        {
            state.repositionPhase = Mm9RepositionPhase::None;
            state.backOffWaitSeconds = settings.backOffCooldownSeconds;
            pDecision = &repositionDecide(ai, state, ActorAiDecisionKind::BackOffRush, "blocked");
        }
        else if (repositionDistance2d(position, post) > arrival)
        {
            state.repositionPhase = Mm9RepositionPhase::Returning;
            state.repositionSpot = post;
            state.repositionSeconds = repositionWalkLimitSeconds(repositionDistance2d(position, post), runSpeed);
            pDecision = &repositionDecide(ai, state, ActorAiDecisionKind::Reposition, "post");
            pDecision->hasPoint = true;
            pDecision->point = post;
        }
        else
        {
            state.repositionPhase = Mm9RepositionPhase::None;
            pDecision = &repositionDecide(ai, state, ActorAiDecisionKind::Reposition, "none");
        }

        pDecision->checks = world.repositionSightChecks;

        if (state.repositionPhase == Mm9RepositionPhase::None)
        {
            AI_RepositionHold(ai);
            return true;
        }
    }

    switch (state.repositionPhase)
    {
        case Mm9RepositionPhase::SightQuery:
        case Mm9RepositionPhase::BackOffQuery:
        {
            // A query the world dropped (the actor left its active set) is given up.
            if (state.repositionSeconds <= 0.0f)
            {
                state.repositionPhase = Mm9RepositionPhase::None;
                return false;
            }

            AI_RepositionHold(ai);
            return true;
        }
        case Mm9RepositionPhase::Moving:
        case Mm9RepositionPhase::Returning:
        {
            const bool moving = state.repositionPhase == Mm9RepositionPhase::Moving;
            const char *pArrived = nullptr;
            bool onSpot = false;

            if (seen)
            {
                pArrived = "sight";
            }
            else if (repositionDistance2d(position, state.repositionSpot) <= arrival)
            {
                pArrived = moving ? "spot" : "post";
                onSpot = moving;
            }
            else if (moving && repositionDistance2d(position, post) > settings.leashRadius + arrival)
            {
                pArrived = "leash";
            }
            else if (state.repositionSeconds <= 0.0f)
            {
                pArrived = "timeout";
            }

            if (pArrived != nullptr)
            {
                // On a spot that sees where its target was it searches no more for that place: its perception
                // finds the target there, or the target stays lost.
                state.lastSeenSearched = state.lastSeenSearched || onSpot;
                state.repositionPhase = Mm9RepositionPhase::None;
                state.repositionSearchWaitSeconds = settings.retrySeconds;
                state.shotCheckSeconds = 0.0f;
                ActorAiDecision &decision =
                    repositionDecide(ai, state, ActorAiDecisionKind::RepositionArrived, pArrived);
                decision.hasPoint = true;
                decision.point = position;
                AI_RepositionHold(ai);
                return true;
            }

            AI_Mm9MoveTo(ai, state.repositionSpot, ActorAiMotionState::Pursuing);
            applyActiveMovementCommit(actor, false, ai.update());
            applyMm9MoveTarget(ai.update(), actor, state.repositionSpot);
            return true;
        }
        case Mm9RepositionPhase::BackingOff:
        {
            const bool inReach = offered && mm9EdgeDistance(actor, *pFrame) <= pProfile->attackReach;
            // The movement step clears a move a wall stopped.
            const bool blocked = !backOffStarting && !hasMoveDirection(actor);

            if (inReach || blocked || skirmishSecondsLeft(ai) <= 0.0f
                || repositionDistance2d(position, state.repositionSpot) <= RepositionArrivalDistance)
            {
                state.repositionPhase = Mm9RepositionPhase::None;
                state.backOffWaitSeconds = settings.backOffCooldownSeconds;
                state.shotCheckSeconds = 0.0f;
                setSkirmishPhase(ai, ActorSkirmishPhase::None, 0.0f);

                // In reach it strikes as before.
                if (inReach)
                {
                    return false;
                }

                AI_RepositionHold(ai);
                return true;
            }

            const float deltaX = state.repositionSpot.x - position.x;
            const float deltaY = state.repositionSpot.y - position.y;
            const float distance = std::max(0.001f, length2d(deltaX, deltaY));
            ai.setMotionState(ActorAiMotionState::Pursuing);
            ai.setAnimationState(ActorAiAnimationState::Walking);
            ai.setAttackImpactTriggered(false);
            AI_SkirmishMove(ai, deltaX / distance, deltaY / distance, SkirmishBackpedalSpeedShare);
            return true;
        }
        case Mm9RepositionPhase::None:
            break;
    }

    // A rush: a target it sees closing fast, outside its reach and inside the trigger distance.
    if (seen && state.backOffWaitSeconds <= 0.0f)
    {
        float velocityX = 0.0f;
        float velocityY = 0.0f;
        skirmishTargetVelocity(actor, *pFrame, velocityX, velocityY);
        const float closing =
            repositionClosingSpeed(position, actor.target.currentPosition, velocityX, velocityY);

        if (repositionRushed(settings, mm9EdgeDistance(actor, *pFrame), pProfile->attackReach, closing))
        {
            ActorRepositionQuery query = {};
            query.needsSight = false;
            const float side =
                mm9Unit(actor.actorId, state.repositionCount++, RepositionSideSalt) < 0.5f ? -1.0f : 1.0f;
            query.count = uint8_t(repositionBackOffCandidates(position, actor.target.currentPosition, post, settings,
                side, query.candidates));
            query.maxSightChecks = uint8_t(settings.maxSightChecks);

            if (query.count == 0)
            {
                state.backOffWaitSeconds = settings.backOffCooldownSeconds;
                repositionDecide(ai, state, ActorAiDecisionKind::BackOffRush, "leash");
                AI_RepositionHold(ai);
                return true;
            }

            requestRepositionQuery(ai, query);
            state.repositionPhase = Mm9RepositionPhase::BackOffQuery;
            state.repositionSeconds = RepositionQueryTimeoutSeconds;
            AI_RepositionHold(ai);
            return true;
        }
    }

    // Lost sight: a search for a spot that sees where it last saw its target, at most once per retry_seconds.
    if (!seen && state.hasLastSeen && !state.lastSeenSearched && repositionLostSight(settings, state.unseenSeconds)
        && state.repositionSearchWaitSeconds <= 0.0f)
    {
        ActorRepositionQuery query = {};
        query.needsSight = true;
        query.target = state.lastSeenTarget;
        query.count = uint8_t(repositionCandidates(position, post, settings,
            mm9Unit(actor.actorId, state.repositionCount++, RepositionBearingSalt), query.candidates));
        query.minTargetDistance = settings.backOffTriggerDistance;
        query.maxSightChecks = uint8_t(settings.maxSightChecks);
        requestRepositionQuery(ai, query);
        state.repositionPhase = Mm9RepositionPhase::SightQuery;
        state.repositionSeconds = RepositionQueryTimeoutSeconds;
        state.repositionSearchWaitSeconds = settings.retrySeconds;
        AI_RepositionHold(ai);
        return true;
    }

    return false;
}

// The layers' holds before the native flow (AI_ActiveBehavior): a spawn-in, a launch from a hanging start, a raise, a
// resurrection spell, a door, a flight.
bool AI_Mm9LayerHold(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorMm9State &state = actor.runtime.mm9;

    // GreaterDemon.scr DoSpawnAnim faces the party (GetPlayerHandle, FaceObject) as its Spawn clip starts.
    if (state.spawnPhase != Mm9SpawnPhase::Done && state.spawnPhase != Mm9SpawnPhase::Unknown)
    {
        const ActorAiFrameFacts *pFrame = ai.frame();
        std::optional<float> yaw;

        if (state.spawnPhase == Mm9SpawnPhase::Spawn && pFrame != nullptr
            && state.spawnSeconds == actor.tactics.mm9Profile->spawnSeconds)
        {
            yaw = std::atan2(pFrame->party.position.y - actor.movement.position.y,
                pFrame->party.position.x - actor.movement.position.x);
        }

        AI_Mm9HoldStill(ai, yaw);
        return true;
    }

    // A woken start: a hanging one drops for its Launch clip, a lying one gets up with its Wakeup clip.
    if (state.wakeSeconds > 0.0f)
    {
        if (actor.tactics.mm9Profile->dormantPose == Mm9AiDormantPose::Hang)
        {
            AI_Mm9Launch(ai);
        }
        else
        {
            AI_Mm9HoldStill(ai, std::nullopt);
        }

        return true;
    }

    if (state.raiseSeconds > 0.0f)
    {
        AI_Mm9HoldStill(ai, std::nullopt);
        return true;
    }

    if (state.castSeconds > 0.0f)
    {
        const GameplayWorldPoint &corpse = actor.mm9World.resurrectCorpsePosition;
        const float deltaX = corpse.x - actor.movement.position.x;
        const float deltaY = corpse.y - actor.movement.position.y;
        AI_Mm9HoldStill(ai, deltaX * deltaX + deltaY * deltaY > 0.0001f
            ? std::optional<float>(std::atan2(deltaY, deltaX)) : std::nullopt);
        return true;
    }

    if (AI_Mm9Door(ai))
    {
        return true;
    }

    if (state.fleeMode != Mm9FleeMode::None && actor.status.spellEffects.fearRemainingSeconds <= 0.0f)
    {
        AI_Mm9Flee(ai);
        return true;
    }

    return AI_Mm9Reposition(ai);
}

// A dead MM9 monster that can be raised (its placement's CanBeResurrected and its model's Resurrect clip;
// AICommon.inc OnDeath, OnDeathDone, AskForResurrection, OnResurrect). Once its death clip ends it asks a resurrecter
// within 1 000 LT (one holding no target or the target it died holding) and again every 5 s while one answers; when an
// ask after the first finds none, a resurrecter raises itself 2-10 s later (anyone else stops asking: MM9 removes the
// corpse, OpenYAMM leaves it to be looted). Raised (by a resurrecter's DoResurrection key or itself) it waits until no
// actor stands within twice its radius (every 0.5 s) and rises: full health, its Resurrect clip, then its old target.
void AI_Mm9Corpse(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
{
    const Mm9AiProfile *pProfile = actor.tactics.mm9Profile ? &*actor.tactics.mm9Profile : nullptr;
    const bool raisable = pProfile != nullptr && pProfile->raiseSeconds > 0.0f && actor.movement.mm9Placement
        && actor.movement.mm9Placement->canBeResurrected;

    const ActorAiMotionState motionState = update.state.motionState.value_or(actor.runtime.motionState);

    if (!raisable || (motionState != ActorAiMotionState::Dead && motionState != ActorAiMotionState::Dying))
    {
        return;
    }

    const ActorMm9WorldFacts &world = actor.mm9World;
    ActorMm9State state = update.state.mm9.value_or(actor.runtime.mm9);

    // Only a death this session asks (the script's state is not saved: a corpse loaded with the map stays dead).
    if (motionState == ActorAiMotionState::Dying)
    {
        state.dyingSeen = true;
        update.state.mm9 = state;
        return;
    }

    if (!state.dyingSeen)
    {
        return;
    }
    const float stepSeconds = std::max(0.0f, frame.fixedStepSeconds);
    std::optional<ActorAiDecision> decision;
    ActorMm9Request request = update.mm9Request.value_or(ActorMm9Request{});
    bool requested = false;

    if (!state.corpseStarted)
    {
        state.corpseStarted = true;
        state.deathTargetKind = state.targetKind;
        state.deathTargetActorIndex = state.targetActorIndex;
        mm9ClearTarget(state);
        state.wanderPhase = Mm9WanderPhase::Off;
        state.asked = false;
        state.askAwaiting = false;
        state.askSeconds = 0.0f;
        state.selfRaiseSeconds = -1.0f;
        state.raisePending = false;
        state.seenRaiseSerial = world.raiseSerial;
        state.resurrectCorpse = static_cast<size_t>(-1);
        state.castSeconds = 0.0f;
    }

    if (state.askAwaiting)
    {
        state.askAwaiting = false;
        decision = mm9Decision(ActorAiDecisionKind::ResurrectAsk, state.deathTargetKind, state.deathTargetActorIndex,
            world.resurrecterFound ? "asked" : "none");

        if (world.resurrecterFound || !state.asked)
        {
            state.askSeconds = Mm9ResurrectAskSeconds;
        }
        else if (pProfile->resurrecter)
        {
            state.selfRaiseSeconds =
                mm9NoteRandom(state, mm9SelfRaiseDelaySeconds(mm9Roll(actor, state, Mm9SelfRaiseSalt)));
            decision->pNote = "self";
            decision->seconds = state.selfRaiseSeconds;
        }

        state.asked = true;
    }

    if (state.askSeconds >= 0.0f)
    {
        state.askSeconds = std::max(0.0f, state.askSeconds - stepSeconds);

        if (state.askSeconds <= 0.0f)
        {
            state.askSeconds = -1.0f;
            state.askAwaiting = true;
            request.askResurrection = true;
            requested = true;
        }
    }

    const char *pRaiseNote = "rise";

    if (state.selfRaiseSeconds >= 0.0f)
    {
        state.selfRaiseSeconds = std::max(0.0f, state.selfRaiseSeconds - stepSeconds);

        if (state.selfRaiseSeconds <= 0.0f)
        {
            state.selfRaiseSeconds = -1.0f;
            state.raisePending = true;
            state.raiseRetrySeconds = 0.0f;
        }
    }

    if (world.raiseSerial != state.seenRaiseSerial)
    {
        state.seenRaiseSerial = world.raiseSerial;
        state.raisePending = true;
        state.raiseRetrySeconds = 0.0f;
        state.askSeconds = -1.0f;
        state.selfRaiseSeconds = -1.0f;
    }
    else if (state.raisePending && pProfile->resurrecter && state.asked && !world.resurrecterFound)
    {
        pRaiseNote = "self";
    }

    if (state.raisePending)
    {
        state.raiseRetrySeconds = std::max(0.0f, state.raiseRetrySeconds - stepSeconds);

        if (state.raiseRetrySeconds <= 0.0f)
        {
            if (mm9CanRaiseNow(world.nearestActorDistance, float(actor.stats.radius)))
            {
                state.raisePending = false;
                state.corpseStarted = false;
                state.dyingSeen = false;
                state.askSeconds = -1.0f;
                state.askAwaiting = false;
                state.raiseSeconds = pProfile->raiseSeconds;
                request.revive = true;
                requested = true;
                decision = mm9Decision(ActorAiDecisionKind::Raised, state.deathTargetKind,
                    state.deathTargetActorIndex, pRaiseNote);
            }
            else
            {
                state.raiseRetrySeconds = Mm9RaiseRetrySeconds;
                decision = mm9Decision(ActorAiDecisionKind::Raised, state.deathTargetKind,
                    state.deathTargetActorIndex, "wait");
            }
        }
    }

    update.state.mm9 = state;

    if (requested)
    {
        update.mm9Request = request;
    }

    if (decision)
    {
        update.state.layerDecision = decision;
    }
}

ActorAiCommandContext beginActiveActorCommand(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const std::optional<ActorAiUpdate> &statusContinuation);

// A dead MM9 monster MM9 spawned with ScriptParams 1 whose row has a death spawn (LesserDemon.scr OnDeathDone): once
// its death clip ends, a Greater Demon spawns at its corpse, itself spawned with ScriptParams 1 (it spawns in). Only a
// death seen this session spawns (the script's state is not saved).
void AI_Mm9DeathSpawn(const ActorAiFacts &actor, ActorAiUpdate &update)
{
    if (!actor.tactics.mm9Profile || actor.tactics.mm9Profile->deathSpawnMonsterId == 0 || !actor.movement.mm9Spawned)
    {
        return;
    }

    const ActorAiMotionState motionState = update.state.motionState.value_or(actor.runtime.motionState);
    ActorMm9State state = update.state.mm9.value_or(actor.runtime.mm9);

    if (motionState == ActorAiMotionState::Dying)
    {
        if (!state.dyingSeen)
        {
            state.dyingSeen = true;
            update.state.mm9 = state;
        }

        return;
    }

    if (motionState != ActorAiMotionState::Dead || !state.dyingSeen || state.deathSpawned)
    {
        return;
    }

    state.deathSpawned = true;
    update.state.mm9 = state;
    ActorSpawnRequest request = {};
    request.sourceActorIndex = actor.actorIndex;
    request.monsterId = actor.tactics.mm9Profile->deathSpawnMonsterId;
    request.position = actor.movement.position;
    request.yawRadians = actor.runtime.yawRadians;
    request.hostile = actor.status.hostileToParty;
    request.group = actor.identity.group;
    request.mm9Spawned = true;
    update.spawnRequest = request;
    ActorAiDecision decision =
        mm9Decision(ActorAiDecisionKind::DeathSpawn, ActorAiTargetKind::None, static_cast<size_t>(-1), nullptr);
    decision.marker = request.monsterId;
    update.state.layerDecision = decision;
}

// A dormant start (MM9_MONSTER_AI_PLAN.md phase 4b; the scene's dormant hold): it rests in its pose (the world plays
// its clip) and notices nothing but what wakes it (mm9DormantWakes). A trigger and a hit wake it through the world
// (evt.WakeActor, a hit on a resting actor). A disturbed one also wakes on an alert naming a target that is not its
// friend (FlyingIcky.scr IckyAlert), a friend's help call (IckyHelp) or a target it notices, a hanging one only while
// it plays its fidget, every 2-10 s (Fidget registers OnFoundTarget); a sighted one wakes on a target it notices. It
// takes that target as it wakes; a hanging one drops and launches first (IckyLaunch).
ActorAiUpdate AI_Mm9Dormant(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiCommandContext ai = beginActiveActorCommand(actor, frame, std::nullopt);
    ActorMm9State &state = mm9State(ai);
    const Mm9AiProfile &profile = *actor.tactics.mm9Profile;
    const ActorMm9WorldFacts &world = actor.mm9World;
    const float stepSeconds = std::max(0.0f, frame.fixedStepSeconds);
    const Mm9AiDormantUntil until =
        profile.dormantUntil == Mm9AiDormantUntil::None ? Mm9AiDormantUntil::Trigger : profile.dormantUntil;
    const Mm9AiDormantPose pose = profile.dormantPose;

    if (!state.dormantHeld)
    {
        state.dormantHeld = true;
        state.dormantSeconds = 0.0f;
    }

    state.dormantSeconds += stepSeconds;

    // FlyingIcky.scr FidgetSetup, Fidget and FidgetDone: a hanging fidget 2-10 s after the last.
    if (pose == Mm9AiDormantPose::Hang && profile.dormantFidgetSeconds > 0.0f)
    {
        if (state.dormantFidgeting && state.dormantSeconds >= profile.dormantFidgetSeconds)
        {
            state.dormantFidgeting = false;
            state.dormantSeconds = 0.0f;
            state.dormantFidgetWaitSeconds = -1.0f;
        }

        if (!state.dormantFidgeting && state.dormantFidgetWaitSeconds < 0.0f)
        {
            state.dormantFidgetWaitSeconds = mm9NoteRandom(state,
                mm9HangFidgetWaitSeconds(mm9Roll(actor, state, Mm9HangFidgetSalt)));
        }

        if (!state.dormantFidgeting)
        {
            state.dormantFidgetWaitSeconds = std::max(0.0f, state.dormantFidgetWaitSeconds - stepSeconds);

            if (state.dormantFidgetWaitSeconds <= 0.0f)
            {
                state.dormantFidgeting = true;
                state.dormantSeconds = 0.0f;
                state.dormantFidgetWaitSeconds = -1.0f;
                ai.decide(ActorAiDecisionKind::Fidget, "hang");
            }
        }
    }

    const char *pWake = nullptr;
    ActorAiTargetKind wakeKind = ActorAiTargetKind::None;
    size_t wakeIndex = static_cast<size_t>(-1);

    if (world.callSerial != state.seenCallSerial)
    {
        state.seenCallSerial = world.callSerial;

        if (world.callTargetValid && world.callTargetKind != ActorAiTargetKind::None
            && mm9DormantWakes(until, pose, world.callIsHelp ? Mm9DormantEvent::Help : Mm9DormantEvent::Alert,
                state.dormantFidgeting))
        {
            pWake = world.callIsHelp ? "help" : "alert";
            wakeKind = world.callTargetKind;
            wakeIndex = world.callTargetActorIndex;
        }
    }

    if (pWake == nullptr && actor.target.currentCanSense && actor.target.currentKind != ActorAiTargetKind::None
        && mm9DormantWakes(until, pose, Mm9DormantEvent::Sighted, state.dormantFidgeting))
    {
        pWake = "sighted";
        wakeKind = actor.target.currentKind;
        wakeIndex = actor.target.currentActorIndex;
    }

    if (pWake != nullptr)
    {
        state.dormantHeld = false;
        state.dormantFidgeting = false;
        state.dormantFidgetWaitSeconds = -1.0f;
        state.wakeSeconds = mm9WakeHoldSeconds(pose, profile.wakeSeconds, profile.wakeupSeconds);
        mm9SetUpTarget(actor, state, wakeKind, wakeIndex);
        ActorMm9Request request = ai.update().mm9Request.value_or(ActorMm9Request{});
        request.wake = true;
        ai.update().mm9Request = request;
        ai.update().state.layerDecision = mm9Decision(ActorAiDecisionKind::Wake, wakeKind, wakeIndex, pWake);
    }

    AI_Mm9HoldStill(ai, std::nullopt);
    return ai.finish();
}

bool AI_AttackOrPursue(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts *pFrame = ai.frame();

    if (pFrame == nullptr || !actor.world.active)
    {
        return false;
    }

    // A townsperson never fights (NPCBase.inc: its targets are the people it talks to and those it runs from), nor
    // does a monster whose behaviour script keeps it passive (a cut-scene actor) or whose placement script runs no AI.
    if (mm9LoopActive(actor, pFrame) && (actor.tactics.mm9Profile->archetype == Mm9AiArchetype::Civilian
        || actor.behavior.mm9Script.passive || actor.tactics.mm9Profile->passive))
    {
        return false;
    }

    const GameplayActorService actorService = {};
    const ActorEngagementState engagement =
        resolveActorEngagement(actor, *pFrame, actorService);

    if (!engagement.shouldEngageTarget)
    {
        return false;
    }

    if (mm9LoopActive(actor, pFrame) && actor.behavior.mm9Script.drivesAttacks)
    {
        return AI_Mm9ScriptedEngage(ai);
    }

    if (mm9FlierLoopActive(actor, pFrame))
    {
        return AI_Mm9FlierEngage(ai, engagement);
    }

    if (mm9TurretLoopActive(actor, pFrame))
    {
        return AI_Mm9TurretEngage(ai);
    }

    if (mm9WalkerLoopActive(actor, pFrame))
    {
        return AI_Mm9Engage(ai, engagement);
    }

    CombatAbilityChoiceInput abilityInput = {};
    abilityInput.actorId = actor.actorId;
    abilityInput.attackDecisionCount = actor.runtime.attackDecisionCount;
    abilityInput.hasSpell1 = actor.stats.hasSpell1;
    abilityInput.spell1IsOkToCast =
        actor.stats.spell1CastSupported
        && monsterSpellIsOkToCast(
            actor.stats.spell1Name,
            actor.stats,
            actor.status,
            pFrame->party);
    abilityInput.spell1UseChance = actor.stats.spell1UseChance;
    abilityInput.hasSpell2 = actor.stats.hasSpell2;
    abilityInput.spell2IsOkToCast =
        actor.stats.spell2CastSupported
        && monsterSpellIsOkToCast(
            actor.stats.spell2Name,
            actor.stats,
            actor.status,
            pFrame->party);
    abilityInput.spell2UseChance = actor.stats.spell2UseChance;
    abilityInput.attack2Chance = actor.stats.attack2Chance;
    abilityInput.constraintState = actor.stats.attackConstraints;
    abilityInput.movementAllowed = actor.movement.movementAllowed;
    abilityInput.targetIsActor = engagement.targetIsActor;
    abilityInput.targetEdgeDistance = actor.target.currentEdgeDistance;
    abilityInput.rangedAttackReach = engagement.targetIsParty
        ? std::max(MaximumRangedAttackDistance, actor.target.partyAttackReach)
        : MaximumRangedAttackDistance;
    abilityInput.inMeleeRange = engagement.inMeleeRange;
    abilityInput.chooseRandomAbility = true;
    abilityInput.applyAbilityConstraints = true;
    // A ranged band shoots from anywhere inside it, and closes in from beyond it like any other monster.
    abilityInput.forceRangedCommit =
        actor.tactics.keepsRangedBand() && actor.target.currentEdgeDistance <= actor.tactics.rangedMaxDistance;
    const CombatAbilityChoiceResult abilityChoice = chooseCombatAbility(abilityInput);

    CombatEngagePlanInput engageInput = {};
    engageInput.abilityIsRanged = abilityChoice.abilityIsRanged;
    engageInput.abilityIsMelee = abilityChoice.abilityIsMelee;
    engageInput.inMeleeRange = engagement.inMeleeRange;
    engageInput.attackCooldownReady = actorAttackReady(actor, *pFrame);
    engageInput.movementAllowed = actor.movement.movementAllowed;
    engageInput.stationaryOrTooCloseForRangedPursuit = abilityChoice.stationaryOrTooCloseForRangedPursuit;
    engageInput.currentlyPursuing = actor.runtime.motionState == ActorAiMotionState::Pursuing;
    engageInput.crowdStandActive = actor.runtime.crowdStandRemainingSeconds > 0.0f;
    engageInput.actionSeconds = actor.runtime.actionSeconds;
    engageInput.currentMoveDirectionX = actor.movement.moveDirectionX;
    engageInput.currentMoveDirectionY = actor.movement.moveDirectionY;
    engageInput.targetEdgeDistance = actor.target.currentEdgeDistance;
    const CombatEngagePlan engagePlan = chooseCombatEngagePlan(engageInput);

    ai.setMeleePursuitActive(engagePlan.meleePursuitActive);
    ai.resetAnimationOnChange();
    ai.setAttackDecisionCount(abilityChoice.nextAttackDecisionCount);

    if (skirmishActive(actor, pFrame) && AI_SkirmishBeforeEngage(ai, engagement, engagePlan.action))
    {
        return true;
    }

    if (AI_TacticEngage(ai, abilityChoice, engagePlan))
    {
        return true;
    }

    if (engagePlan.action == CombatEngageAction::HoldCrowdStand)
    {
        ai.decide(ActorAiDecisionKind::CrowdHold);
        ai.setMotionState(ActorAiMotionState::Standing);
        ai.setAnimationState(actor.runtime.animationState == ActorAiAnimationState::Bored
            ? ActorAiAnimationState::Bored
            : ActorAiAnimationState::Standing);
        ai.setMovementAction(ActorAiMovementAction::Stand);
        ai.clearMovementDirection();
        applyActiveMovementCommit(actor, engagePlan.preserveCrowdSteering, ai.update());
        return true;
    }

    if (engagePlan.action == CombatEngageAction::StartRangedAttack
        || engagePlan.action == CombatEngageAction::StartMeleeAttack)
    {
        ai.setMotionState(ActorAiMotionState::Attacking);
        ai.setAnimationState(attackAnimationStateForAbility(abilityChoice.ability, actor.stats.attackConstraints));
        ai.setMovementAction(ActorAiMovementAction::Stand);
        ai.clearMovementDirection();
        ai.faceYaw(tacticFacingYaw(actor, pFrame, yawTowardTarget(actor)));
        AI_Attack(ai, abilityChoice);
        return true;
    }

    if (engagePlan.action == CombatEngageAction::StandForRangedBlock
        || engagePlan.action == CombatEngageAction::StandForMeleeCooldown)
    {
        ai.decide(engagePlan.action == CombatEngageAction::StandForRangedBlock ? ActorAiDecisionKind::WaitNoShot
            : ActorAiDecisionKind::WaitCooldown);
        ai.setMotionState(ActorAiMotionState::Standing);
        ai.setAnimationState(ActorAiAnimationState::Standing);
        ai.setMovementAction(ActorAiMovementAction::Stand);
        ai.clearMovementDirection();
        ai.faceYaw(tacticFacingYaw(actor, pFrame, yawTowardTarget(actor)));
        applyActiveMovementCommit(actor, engagePlan.preserveCrowdSteering, ai.update());
        return true;
    }

    if (engagePlan.action == CombatEngageAction::ContinueRangedPursuit
        || engagePlan.action == CombatEngageAction::ContinueMeleePursuit)
    {
        ai.setMotionState(ActorAiMotionState::Pursuing);
        ai.setAnimationState(ActorAiAnimationState::Walking);
        ai.setMovementAction(ActorAiMovementAction::Pursue);
        ai.setMoveDirection(actor.movement.moveDirectionX, actor.movement.moveDirectionY);
        ai.setDesiredMovement(actor.movement.moveDirectionX, actor.movement.moveDirectionY);
        applyActiveMovementCommit(actor, engagePlan.preserveCrowdSteering, ai.update());
        return true;
    }

    if (engagePlan.action == CombatEngageAction::StartMeleePursuitWithoutMovement)
    {
        ai.setMotionState(ActorAiMotionState::Pursuing);
        ai.setAnimationState(ActorAiAnimationState::Standing);
        ai.setMovementAction(ActorAiMovementAction::Stand);
        ai.clearMovementDirection();

        // A traversing turret keeps tracking a target it cannot shoot at this moment.
        if (actor.tactics.traverseRadiansPerSecond > 0.0f)
        {
            ai.faceYaw(tacticFacingYaw(actor, pFrame, yawTowardTarget(actor)));
        }
        applyActiveMovementCommit(actor, engagePlan.preserveCrowdSteering, ai.update());
        return true;
    }

    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    const float minimumActionSeconds =
        engagePlan.useRecoveryFloorForPursuit ? std::max(0.0f, actor.runtime.recoverySeconds) : 0.0f;
    AI_PursueByMode(ai, engagePlan.pursueMode, minimumActionSeconds);
    applyActiveMovementCommit(actor, engagePlan.preserveCrowdSteering, ai.update());
    return true;
}

void applyActiveAgingUpdates(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const std::optional<ActorAiUpdate> &statusContinuation,
    ActorAiUpdate &update)
{
    applyStatusContinuationUpdate(statusContinuation, update);
    applyActiveAnimationTickUpdate(actor, frame, update);
    applyActiveSpellTimerUpdate(actor, frame, update);
    applyActiveFrameTimerUpdate(actor, frame, update);
}

bool AI_ApplyStatusState(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts *pFrame = ai.frame();

    if (pFrame == nullptr)
    {
        return false;
    }

    const GameplayActorService actorService = {};
    const float animationTimeTicks = ageActorAnimationTimeTicks(actor, *pFrame);

    const ActorStatusFrameOutcome currentStatusFrame = resolveActorStatusFrame(
        actor.runtime.motionState == ActorAiMotionState::Stunned,
        actor.status.spellEffects.paralyzeRemainingSeconds > 0.0f,
        false,
        actor.runtime.actionSeconds,
        0.0f,
        pFrame->fixedStepSeconds);

    if (currentStatusFrame.action == ActorStatusFrameAction::HoldStun)
    {
        ai.setMotionState(ActorAiMotionState::Stunned);
        ai.setActionSeconds(currentStatusFrame.actionSeconds);
        ai.setAnimationState(ActorAiAnimationState::GotHit);
        ai.setAnimationTimeTicks(animationTimeTicks);
        AI_ClearMovement(ai);
        return true;
    }

    if (currentStatusFrame.action == ActorStatusFrameAction::RecoverFromStun)
    {
        ai.setMotionState(ActorAiMotionState::Standing);
        ai.setActionSeconds(currentStatusFrame.actionSeconds);
        ai.setAnimationState(ActorAiAnimationState::Standing);
        ai.setAnimationTimeTicks(0.0f);
        AI_ClearMovement(ai);
        return true;
    }

    GameplayActorSpellEffectState spellEffects = actor.status.spellEffects;
    actorService.updateSpellEffectTimers(spellEffects, pFrame->fixedStepSeconds, actor.status.defaultHostileToParty);
    ai.setSpellEffects(spellEffects);

    const ActorStatusFrameOutcome updatedStatusFrame = resolveActorStatusFrame(
        false,
        spellEffects.paralyzeRemainingSeconds > 0.0f,
        spellEffects.stunRemainingSeconds > 0.0f,
        actor.runtime.actionSeconds,
        spellEffects.stunRemainingSeconds,
        0.0f);

    if (updatedStatusFrame.action == ActorStatusFrameAction::HoldParalyze)
    {
        ai.setMotionState(ActorAiMotionState::Standing);
        ai.setActionSeconds(updatedStatusFrame.actionSeconds);
        ai.setAttackImpactTriggered(false);
        ai.setSpellEffects(spellEffects);
        ai.setAnimationState(ActorAiAnimationState::Standing);
        ai.setAnimationTimeTicks(0.0f);
        AI_ClearMovement(ai);
        return true;
    }

    if (updatedStatusFrame.action == ActorStatusFrameAction::ForceStun)
    {
        ai.setMotionState(ActorAiMotionState::Stunned);
        ai.setActionSeconds(updatedStatusFrame.actionSeconds);
        ai.setSpellEffects(spellEffects);
        ai.setAnimationState(ActorAiAnimationState::GotHit);
        ai.setAnimationTimeTicks(animationTimeTicks);
        AI_ClearMovement(ai);
        return true;
    }

    return false;
}

bool AI_DeathOrStatus(ActorAiCommandContext &ai)
{
    if (isDeadOrDying(ai.actor()))
    {
        AI_ApplyDeathState(ai);
        return true;
    }

    if (!isStatusLocked(ai.actor()))
    {
        return false;
    }

    return AI_ApplyStatusState(ai);
}

bool AI_ContinueCurrentAction(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();

    if (actor.runtime.motionState != ActorAiMotionState::Attacking)
    {
        return false;
    }

    ai.setMotionState(ActorAiMotionState::Attacking);
    ai.setAnimationState(attackAnimationStateForAbility(
        actor.runtime.queuedAttackAbility,
        actor.stats.attackConstraints));
    ai.setMovementAction(ActorAiMovementAction::Stand);
    if (!actor.runtime.attackImpactTriggered && actor.target.currentKind != ActorAiTargetKind::None
        && actor.target.currentCanSense)
    {
        const float dx = actor.target.currentPosition.x + actor.tactics.aimLead.x - actor.movement.position.x;
        const float dy = actor.target.currentPosition.y + actor.tactics.aimLead.y - actor.movement.position.y;
        if (dx * dx + dy * dy > 0.0001f)
        {
            // Release already aims at the current target. Keep windup facing consistent with that aim.
            ai.faceYaw(tacticFacingYaw(actor, ai.frame(), std::atan2(dy, dx)));
        }
    }
    return true;
}

void AI_Stand(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();

    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();

    if (actor.runtime.animationState != ActorAiAnimationState::Standing)
    {
        ai.setAnimationTimeTicks(0.0f);
    }
}

void AI_Bored(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const float yaw = ai.update().movementIntent.updateYaw
        ? ai.update().movementIntent.yawRadians : actor.runtime.yawRadians;
    if (!actorFidgetFacesListener(
            yaw,
            actor.world.listenerPosition.x - actor.movement.position.x,
            actor.world.listenerPosition.y - actor.movement.position.y))
    {
        AI_Stand(ai);
        ai.setActionSeconds(IdleStandSeconds);
        ai.setIdleDecisionSeconds(IdleStandSeconds);
        return;
    }

    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Bored);
    ai.setAnimationTimeTicks(0.0f);
    ai.setActionSeconds(actor.runtime.boredAnimationSeconds);
    ai.setIdleDecisionSeconds(actor.runtime.boredAnimationSeconds);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();

    if (actorBoredSoundRoll(actor.actorId, actor.runtime.idleDecisionCount))
    {
        ActorAudioRequest boredAudio = {};
        boredAudio.kind = ActorAiAudioRequestKind::Bored;
        boredAudio.actorIndex = actor.actorIndex;
        boredAudio.position = actor.movement.position;
        ai.requestAudio(boredAudio);
    }
}

void AI_WanderVoice(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    if (actorWanderSoundRoll(actor.actorId, actor.runtime.idleDecisionCount))
    {
        ActorAudioRequest audio = {};
        audio.kind = ActorAiAudioRequestKind::Bored;
        audio.actorIndex = actor.actorIndex;
        audio.position = actor.movement.position;
        ai.requestAudio(audio);
    }
}

void AI_RandomMove(ActorAiCommandContext &ai, const IdleBehaviorResult &idleBehavior)
{
    ai.setAttackImpactTriggered(false);
    ai.setActionSeconds(idleBehavior.actionSeconds);
    ai.setIdleDecisionSeconds(idleBehavior.idleDecisionSeconds);
    ai.setAnimationTimeTicks(0.0f);

    if (idleBehavior.updateYaw)
    {
        ai.faceYaw(idleBehavior.yawRadians);
    }

    if (idleBehavior.action == IdleBehaviorAction::Wander)
    {
        ai.decide(ActorAiDecisionKind::Wander);
        ai.setMotionState(ActorAiMotionState::Wandering);
        ai.setAnimationState(ActorAiAnimationState::Walking);
        ai.setMovementAction(ActorAiMovementAction::Wander);
        ai.setMoveDirection(idleBehavior.moveDirectionX, idleBehavior.moveDirectionY);
        ai.setDesiredMovement(idleBehavior.moveDirectionX, idleBehavior.moveDirectionY);
        AI_WanderVoice(ai);
        return;
    }

    if (idleBehavior.bored)
    {
        ai.decide(ActorAiDecisionKind::Fidget);
        AI_Bored(ai);
        return;
    }

    ai.decide(ActorAiDecisionKind::Stand);
    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();
}

void AI_RandomMove(ActorAiCommandContext &ai, float moveDirectionX, float moveDirectionY)
{
    const ActorAiFacts &actor = ai.actor();

    ai.setMotionState(ActorAiMotionState::Wandering);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.setMovementAction(ActorAiMovementAction::Wander);
    ai.setMoveDirection(moveDirectionX, moveDirectionY);
    ai.setDesiredMovement(moveDirectionX, moveDirectionY);

    if (actor.runtime.animationState != ActorAiAnimationState::Walking)
    {
        ai.setAnimationTimeTicks(0.0f);
    }
}

void AI_HoldIdle(ActorAiCommandContext &ai)
{
    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ai.actor().runtime.animationState == ActorAiAnimationState::Bored
        ? ActorAiAnimationState::Bored : ActorAiAnimationState::Standing);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();
}

void AI_StartIdleStand(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    ai.setIdleDecisionCount(actor.runtime.idleDecisionCount + 1);
    AI_RandomMove(ai, idleStandBehavior(actorChoosesBored(actor.actorId, actor.runtime.idleDecisionCount)));
}

// A post with nothing to fight (ActorTacticsFacts::holdPost): walks back to its home position, then turns to its
// placement direction and stands there with the native fidgets, never wandering.
void AI_HoldPost(ActorAiCommandContext &ai, float actionSeconds)
{
    const ActorAiFacts &actor = ai.actor();
    const float deltaHomeX = actor.movement.homePosition.x - actor.movement.position.x;
    const float deltaHomeY = actor.movement.homePosition.y - actor.movement.position.y;
    const float distanceToHome = length2d(deltaHomeX, deltaHomeY);

    if (actor.movement.movementAllowed && actor.movement.effectiveMoveSpeed > 0.0f
        && distanceToHome > TacticPostArrivalRadius)
    {
        const float directionX = deltaHomeX / distanceToHome;
        const float directionY = deltaHomeY / distanceToHome;
        ai.faceYaw(std::atan2(directionY, directionX));
        ai.setActionSeconds(std::min(TacticPostReturnStepSeconds, distanceToHome / actor.movement.effectiveMoveSpeed));
        ai.setIdleDecisionSeconds(0.0f);
        ai.decide(ActorAiDecisionKind::ReturnHome, actor.movement.patrolTarget ? "patrol" : "post");
        AI_RandomMove(ai, directionX, directionY);
        return;
    }

    if (AI_TacticIdleAim(ai))
    {
        return;
    }

    if (actor.runtime.motionState == ActorAiMotionState::Wandering)
    {
        AI_Stand(ai);
        ai.setActionSeconds(0.0f);
        actionSeconds = 0.0f;
    }

    if (actor.movement.hasHomeYaw
        && std::abs(normalizeAngleRadians(actor.movement.homeYawRadians - actor.runtime.yawRadians)) > 0.01f)
    {
        ai.faceYaw(tacticFacingYaw(actor, ai.frame(), actor.movement.homeYawRadians));
        AI_HoldIdle(ai);
        return;
    }

    if (actionSeconds <= 0.0f)
    {
        AI_StartIdleStand(ai);
        ai.setMotionState(ActorAiMotionState::Standing);
    }
    else
    {
        AI_HoldIdle(ai);
    }
}

void AI_StandOrBored(ActorAiCommandContext &ai, float actionSeconds)
{
    const ActorAiFacts &actor = ai.actor();

    if (actor.tactics.holdPost)
    {
        AI_HoldPost(ai, actionSeconds);
        return;
    }

    if (!actor.movement.movementAllowed || actor.status.hostileToParty || actor.movement.wanderRadius <= 0.0f)
    {
        if (!actor.movement.movementAllowed && AI_TacticIdleAim(ai))
        {
            return;
        }

        if (actionSeconds <= 0.0f)
        {
            AI_StartIdleStand(ai);
            ai.setMotionState(ActorAiMotionState::Standing);
        }
        else
        {
            AI_HoldIdle(ai);
        }

        return;
    }

    const float deltaHomeX = actor.movement.homePosition.x - actor.movement.position.x;
    const float deltaHomeY = actor.movement.homePosition.y - actor.movement.position.y;
    const float distanceToHome = length2d(deltaHomeX, deltaHomeY);

    if (distanceToHome > actor.movement.wanderRadius)
    {
        float moveDirectionX = 0.0f;
        float moveDirectionY = 0.0f;

        if (distanceToHome > 0.01f)
        {
            moveDirectionX = deltaHomeX / distanceToHome;
            moveDirectionY = deltaHomeY / distanceToHome;
            ai.faceYaw(std::atan2(moveDirectionY, moveDirectionX));
        }

        if (actor.runtime.motionState != ActorAiMotionState::Wandering || actionSeconds <= 0.0f)
        {
            if (actor.movement.effectiveMoveSpeed <= 0.0f)
            {
                AI_StartIdleStand(ai);
                return;
            }
            ai.setIdleDecisionCount(actor.runtime.idleDecisionCount + 1);
            ai.setActionSeconds(std::max(0.25f, distanceToHome / (4.0f * actor.movement.effectiveMoveSpeed)));
            ai.decide(ActorAiDecisionKind::ReturnHome, "wander_radius");
            AI_WanderVoice(ai);
        }
        AI_RandomMove(ai, moveDirectionX, moveDirectionY);
        return;
    }

    const bool hasMoveDirection =
        std::abs(actor.movement.moveDirectionX) > 0.001f || std::abs(actor.movement.moveDirectionY) > 0.001f;

    if (actionSeconds > 0.0f && hasMoveDirection)
    {
        AI_RandomMove(ai, actor.movement.moveDirectionX, actor.movement.moveDirectionY);
        return;
    }

    if (actor.runtime.motionState == ActorAiMotionState::Wandering)
    {
        AI_StartIdleStand(ai);
        ai.setMotionState(ActorAiMotionState::Standing);
        return;
    }

    if (actionSeconds > 0.0f)
    {
        AI_HoldIdle(ai);
        return;
    }

    IdleBehaviorResult idleBehavior = {};

    if (actor.movement.allowIdleWander)
    {
        idleBehavior = resolveIdleBehavior(
            actor.actorId,
            actor.runtime.idleDecisionCount,
            actor.movement.position.x,
            actor.movement.position.y,
            actor.movement.homePosition.x,
            actor.movement.homePosition.y,
            actor.runtime.yawRadians,
            actor.runtime.animationState == ActorAiAnimationState::Walking,
            actor.movement.wanderRadius,
            actor.movement.effectiveMoveSpeed);
    }
    else
    {
        idleBehavior = idleStandBehavior(actorChoosesBored(actor.actorId, actor.runtime.idleDecisionCount));
        idleBehavior.nextDecisionCount = actor.runtime.idleDecisionCount + 1;
    }

    ai.setIdleDecisionCount(idleBehavior.nextDecisionCount);
    AI_RandomMove(ai, idleBehavior);
}

ActorAiCommandContext beginActiveActorCommand(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const std::optional<ActorAiUpdate> &statusContinuation)
{
    ActorAiUpdate update = makeActorUpdate(actor);
    applyActiveAgingUpdates(actor, frame, statusContinuation, update);
    applyCombatEngagementUpdate(actor, frame, update);

    ActorAiCommandContext ai(actor, frame);
    ai.replaceUpdate(update);
    return ai;
}

ActorAiUpdate finishActiveMovementCommand(ActorAiCommandContext &ai)
{
    ActorAiUpdate update = ai.finish();
    applyActiveMovementCommit(ai.actor(), false, update);
    return update;
}

ActorAiUpdate AI_ActiveCurrentAction(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const std::optional<ActorAiUpdate> &statusContinuation,
    bool hasTarget)
{
    ActorAiCommandContext ai(actor, frame);
    AI_ContinueCurrentAction(ai);

    ActorAiUpdate update = ai.finish();
    applyActiveAgingUpdates(actor, frame, statusContinuation, update);
    applyDelayedAttackSound(actor, update);
    applyAttackImpactOutcome(actor, update);
    const bool attackImpactResolved =
        update.state.attackImpactTriggered.value_or(false) && !actor.runtime.attackImpactTriggered;
    const bool attackImpactApplied = update.state.attackImpactTriggered.value_or(actor.runtime.attackImpactTriggered);
    applyCombatEngagementUpdate(actor, frame, update);
    ai.replaceUpdate(update);

    const bool attackInProgress = ai.update().state.actionSeconds.value_or(actor.runtime.actionSeconds) > 0.0f;

    const bool skirmish = skirmishActive(actor, &frame);
    const bool mm9Mobile = actor.target.currentKind != ActorAiTargetKind::None && actor.movement.movementAllowed
        && actor.movement.effectiveMoveSpeed > 0.0f;
    // An MM9 crawler moves while it attacks too (AI_Mm9AttackStep); a skirmisher's footwork covers MM9 skirmishers. An
    // MM9 flier flies its pass or shot (AI_Mm9FlierAttackStep).
    const bool mm9Crawler = !skirmish && mm9WalkerLoopActive(actor, &frame) && mm9Mobile;
    const bool mm9Flier = !skirmish && mm9FlierLoopActive(actor, &frame) && mm9Mobile;

    if (attackImpactApplied && !attackInProgress)
    {
        if (skirmish && AI_SkirmishAttackDone(ai))
        {
            return ai.finish();
        }

        if (mm9Flier && AI_Mm9FlierAttackDone(ai))
        {
            return ai.finish();
        }

        AI_Stand(ai);
        return ai.finish();
    }

    if (attackImpactResolved)
    {
        // Applied at its contact frame: the attack keeps its stance until the native action ends.
        if (skirmish)
        {
            AI_SkirmishAttackStep(ai);
        }
        else if (mm9Crawler)
        {
            AI_Mm9AttackStep(ai);
        }
        else if (mm9Flier)
        {
            AI_Mm9FlierAttackStep(ai);
        }

        return ai.finish();
    }

    if (AI_CombatFlow(ai, attackInProgress))
    {
        if (attackInProgress && skirmish)
        {
            AI_SkirmishAttackStep(ai);
            return ai.finish();
        }

        if (attackInProgress && mm9Crawler)
        {
            AI_Mm9AttackStep(ai);
            return ai.finish();
        }

        if (attackInProgress && mm9Flier)
        {
            AI_Mm9FlierAttackStep(ai);
            return ai.finish();
        }

        return finishActiveMovementCommand(ai);
    }

    if (hasTarget && AI_AttackOrPursue(ai))
    {
        return ai.finish();
    }

    AI_StandOrBored(ai, ai.update().state.actionSeconds.value_or(actor.runtime.actionSeconds));
    return finishActiveMovementCommand(ai);
}

ActorAiUpdate AI_ActiveBehavior(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const std::optional<ActorAiUpdate> &statusContinuation,
    bool hasTarget)
{
    ActorAiCommandContext ai = beginActiveActorCommand(actor, frame, statusContinuation);

    // An MM9 monster's layers: rising, a resurrection spell, a door, a flight (MM9_MONSTER_AI_PLAN.md phase 4a).
    if (mm9LoopActive(actor, &frame) && AI_Mm9LayerHold(ai))
    {
        return ai.finish();
    }

    if (AI_ContinueFlee(ai))
    {
        return finishActiveMovementCommand(ai);
    }

    if (AI_CombatFlow(ai, false))
    {
        return finishActiveMovementCommand(ai);
    }

    if (hasTarget && AI_AttackOrPursue(ai))
    {
        return ai.finish();
    }

    // An MM9 monster holding a target the world offers from the next step (a switch this step) stands meanwhile.
    if (mm9LoopActive(actor, &frame) && actor.runtime.mm9.targetKind != ActorAiTargetKind::None)
    {
        AI_Stand(ai);
        return finishActiveMovementCommand(ai);
    }

    // An MM9 turret without a target scans (but one its script drives: Dragon.scr stands); any other MM9 monster
    // wanders by its placement.
    if (mm9TurretLoopActive(actor, &frame) && !actor.behavior.mm9Script.drivesAttacks)
    {
        AI_Mm9TurretIdle(ai);
        return ai.finish();
    }

    // (One that fights for the party, a summon or a charmed monster, keeps the native idle: it follows the party.)
    if (mm9LoopActive(actor, &frame) && actor.identity.ally != 999u
        && !gameplayActorFightsForParty(actor.identity.targetPolicy.controlMode))
    {
        const std::optional<GameplayWorldPoint> moveTarget = AI_Mm9Idle(ai);
        ActorAiUpdate update = finishActiveMovementCommand(ai);

        if (moveTarget)
        {
            applyMm9MoveTarget(update, actor, *moveTarget);
        }

        // A wander walks at MM9's walking speed (WalkVel).
        if (update.state.motionState.value_or(actor.runtime.motionState) == ActorAiMotionState::Wandering
            && actor.tactics.mm9Profile->walkSpeed > 0.0f)
        {
            update.movementIntent.moveSpeed = std::min(actor.tactics.mm9Profile->walkSpeed, MaxActorMoveSpeed);
        }

        return update;
    }

    AI_StandOrBored(ai, ai.update().state.actionSeconds.value_or(actor.runtime.actionSeconds));
    return finishActiveMovementCommand(ai);
}

// A behaviour script's action (see ActorBehaviorFacts): stand, keep facing the target and hold the scripted
// animation. Status, death and an attack already under way take precedence and are handled before this.
ActorAiUpdate AI_ScriptedHold(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const std::optional<ActorAiUpdate> &statusContinuation)
{
    ActorAiCommandContext ai = beginActiveActorCommand(actor, frame, statusContinuation);
    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(actor.behavior.holdAnimation);
    ai.setActionSeconds(0.0f);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();

    if (actor.behavior.holdRestartAnimation || actor.runtime.animationState != actor.behavior.holdAnimation)
    {
        ai.setAnimationTimeTicks(0.0f);
    }

    if (!actor.behavior.holdKeepsFacing && actor.target.currentKind != ActorAiTargetKind::None
        && actor.target.currentCanSense)
    {
        const float dx = actor.target.currentPosition.x - actor.movement.position.x;
        const float dy = actor.target.currentPosition.y - actor.movement.position.y;

        if (dx * dx + dy * dy > 0.0001f)
        {
            ai.faceYaw(std::atan2(dy, dx));
        }
    }

    return finishActiveMovementCommand(ai);
}

ActorAiUpdate updateBackgroundActor(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiCommandContext ai(actor, frame);
    if (actor.status.invisible)
    {
        return ai.finish();
    }
    const bool frameHandled = AI_DeathOrStatus(ai);

    if (frameHandled || ai.update().state.spellEffects)
    {
        return ai.finish();
    }

    const float remainingSeconds = std::max(0.0f, actor.runtime.actionSeconds - frame.fixedStepSeconds);
    ai.setAnimationTimeTicks(actor.runtime.animationTimeTicks + frame.fixedStepSeconds * ActorAiTicksPerSecond);
    ai.setActionSeconds(remainingSeconds);
    ai.setIdleDecisionSeconds(remainingSeconds);
    if (AI_TacticIdleAim(ai))
    {
        return ai.finish();
    }
    if (remainingSeconds > 0.0f)
    {
        AI_HoldIdle(ai);
    }
    else
    {
        // MM8's background StandOrBored requests the party direction before testing fidget facing; a post keeps
        // facing its placement direction.
        ai.faceYaw(actor.tactics.holdPost && actor.movement.hasHomeYaw
            ? actor.movement.homeYawRadians
            : std::atan2(
                actor.world.listenerPosition.y - actor.movement.position.y,
                actor.world.listenerPosition.x - actor.movement.position.x));
        AI_StartIdleStand(ai);
    }
    return ai.finish();
}

ActorAiUpdate updateActorSteps(ActorAiFacts &actorFacts, const ActorAiFrameFacts &frame);

ActorAiUpdate updateActor(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiFacts actorFacts = actor;

    // An MM9 monster's loop starts each step; a dormant one rests until it wakes (AI_Mm9Dormant).
    if (mm9LoopActive(actorFacts, &frame) && !isDeadOrDying(actorFacts) && actorFacts.movement.dormant
        && !isStatusLocked(actorFacts))
    {
        return AI_Mm9Dormant(actorFacts, frame);
    }

    if (mm9LoopActive(actorFacts, &frame) && !isDeadOrDying(actorFacts) && !actorFacts.movement.dormant)
    {
        const Mm9PreludeResult prelude = AI_Mm9Prelude(actorFacts, frame);
        ActorAiUpdate update = updateActorSteps(actorFacts, frame);
        mergeMm9Prelude(actorFacts, prelude, update);
        return update;
    }

    return updateActorSteps(actorFacts, frame);
}

ActorAiUpdate updateActorSteps(ActorAiFacts &actorFacts, const ActorAiFrameFacts &frame)
{
    std::optional<ActorAiUpdate> statusContinuation;

    {
        ActorAiCommandContext ai(actorFacts, frame);
        const bool frameHandled = AI_DeathOrStatus(ai);

        if (frameHandled)
        {
            return ai.finish();
        }

        ActorAiUpdate statusUpdate = ai.finish();

        if (statusUpdate.state.spellEffects)
        {
            actorFacts.status.spellEffects = *statusUpdate.state.spellEffects;
            statusContinuation = statusUpdate;
        }
    }

    const std::optional<ActorTargetCandidateFacts> target = chooseTarget(actorFacts, frame);
    const bool hasTarget = target.has_value();

    if (actorFacts.runtime.motionState == ActorAiMotionState::Attacking)
    {
        return AI_ActiveCurrentAction(actorFacts, frame, statusContinuation, hasTarget);
    }

    if (actorFacts.behavior.holdActive)
    {
        return AI_ScriptedHold(actorFacts, frame, statusContinuation);
    }

    return AI_ActiveBehavior(actorFacts, frame, statusContinuation, hasTarget);
}

void appendActorUpdate(ActorAiFrameResult &result, const ActorAiUpdate &update)
{
    result.actorUpdates.push_back(update);

    if (update.attackRequest)
    {
        if (update.attackRequest->kind == ActorAiAttackRequestKind::RangedProjectile
            || update.attackRequest->kind == ActorAiAttackRequestKind::SpellProjectile)
        {
            ActorProjectileRequest projectileRequest = {};
            projectileRequest.sourceActorIndex = update.actorIndex;
            projectileRequest.ability = update.attackRequest->ability;
            projectileRequest.targetKind = update.attackRequest->targetKind;
            projectileRequest.targetActorIndex = update.attackRequest->targetActorIndex;
            projectileRequest.damage = update.attackRequest->damage;
            projectileRequest.attackBonus = update.attackRequest->attackBonus;
            projectileRequest.damageType = update.attackRequest->damageType;
            projectileRequest.spellId = update.attackRequest->spellId;
            projectileRequest.skillLevel = update.attackRequest->skillLevel;
            projectileRequest.skillMastery = update.attackRequest->skillMastery;
            projectileRequest.projectileTokenOverride = update.attackRequest->projectileTokenOverride;
            projectileRequest.source = update.attackRequest->source;
            projectileRequest.target = update.attackRequest->target;
            result.projectileRequests.push_back(projectileRequest);
        }
    }

    for (const ActorAudioRequest &audioRequest : update.audioRequests)
    {
        result.audioRequests.push_back(audioRequest);
    }

    for (const ActorFxRequest &fxRequest : update.fxRequests)
    {
        result.fxRequests.push_back(fxRequest);
    }

    if (update.spawnRequest)
    {
        result.spawnRequests.push_back(*update.spawnRequest);
    }
}

void updateBackgroundActors(const ActorAiFrameFacts &facts, ActorAiFrameResult &result)
{
    for (const ActorAiFacts &actor : facts.backgroundActors)
    {
        ActorAiUpdate update = updateBackgroundActor(actor, facts);

        // A dead MM9 monster asks to be raised (AI_Mm9Corpse); a spawned one may spawn its successor.
        if (mm9LoopActive(actor, &facts) && isDeadOrDying(actor))
        {
            AI_Mm9Corpse(actor, facts, update);
            AI_Mm9DeathSpawn(actor, update);
        }

        appendActorUpdate(result, update);
    }
}

void updateActiveActors(const ActorAiFrameFacts &facts, ActorAiFrameResult &result)
{
    for (const ActorAiFacts &actor : facts.activeActors)
    {
        result.activeActorIndices.push_back(actor.actorIndex);
        appendActorUpdate(result, updateActor(actor, facts));
    }
}

ActorAiUpdate updateActorAfterWorldMovementInternal(const ActorAiFacts &actor)
{
    ActorAiCommandContext ai(actor);

    if (AI_CrowdSteer(ai))
    {
        return ai.finish();
    }

    AI_HandleMovementBlock(ai);

    return ai.finish();
}
}

ActorAiFrameResult GameplayActorAiSystem::updateActors(const ActorAiFrameFacts &facts) const
{
    ActorAiFrameResult result = {};

    if (facts.turnBased.mode == ActorTurnBasedMode::Hold)
    {
        ActorAiFrameFacts heldFacts = facts;

        for (ActorAiFacts &actor : heldFacts.backgroundActors)
        {
            actor.movement.movementAllowed = false;
        }

        for (ActorAiFacts &actor : heldFacts.activeActors)
        {
            actor.movement.movementAllowed = false;
        }

        updateBackgroundActors(heldFacts, result);
        updateActiveActors(heldFacts, result);
        return result;
    }

    updateBackgroundActors(facts, result);
    updateActiveActors(facts, result);

    if (facts.turnBased.mode == ActorTurnBasedMode::MoveOnly)
    {
        for (ActorAiUpdate &update : result.actorUpdates)
        {
            if (update.movementIntent.applyMovement && update.movementIntent.moveSpeed > 0.0f)
            {
                update.movementIntent.moveSpeed = std::min(
                    update.movementIntent.moveSpeed * TurnBasedWaitMoveSpeedMultiplier,
                    MaxActorMoveSpeed);
            }
        }
    }

    return result;
}

ActorAiUpdate GameplayActorAiSystem::updateActorAfterWorldMovement(const ActorAiFacts &facts) const
{
    return updateActorAfterWorldMovementInternal(facts);
}
}
