#include "game/gameplay/GameplayActorAiSystem.h"

#include "game/gameplay/GameplayActorService.h"

#include <algorithm>
#include <cmath>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ActorAiTicksPerSecond = 128.0f;
constexpr float ActorAiUpdateStepSeconds = 1.0f / ActorAiTicksPerSecond;
constexpr float Pi = 3.14159265358979323846f;
constexpr float ActorCrowdSideLockSeconds = 0.22f;
constexpr float ActorCrowdRetreatAngleRadians = Pi * 0.53f;
constexpr float CrowdNoProgressThreshold = 8.0f;
constexpr float CrowdNoProgressStandSeconds = 1.2f;
constexpr float CrowdProbeWindowSeconds = 0.35f;
constexpr float CrowdProbeEdgeDistanceThreshold = 12.0f;
constexpr float CrowdReangleEngageRange = 1024.0f;
constexpr float ActorMeleeRange = 307.2f;
constexpr float HostilityLongRange = 10240.0f;
constexpr float IdleStandSeconds = 1.5f;
constexpr float IdleBoredSeconds = 2.0f;
constexpr uint32_t IdleStandChancePercent = 25u;

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
    bool shouldPlayPartyAlert = false;
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

enum class ActorNonCombatAction : uint8_t
{
    Stand = 0,
    ApplyIdleBehavior = 1,
    ReturnHome = 2,
    ContinueMove = 3,
    StartIdleBehavior = 4,
};

enum class PursueActionMode : uint8_t
{
    OffsetShort = 0,
    Direct = 1,
    OffsetWide = 2,
};

enum class CombatEngageDecisionAction : uint8_t
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

enum class CombatEngageApplicationState : uint8_t
{
    Standing = 0,
    Attacking = 1,
    Pursuing = 2,
};

enum class CombatEngageApplicationAnimation : uint8_t
{
    Standing = 0,
    Walking = 1,
    BoredOrStanding = 2,
    AttackAbility = 3,
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

struct AttackStartPatch
{
    float attackCooldownSeconds = 0.0f;
    float actionSeconds = 0.0f;
};

struct AttackImpactPatch
{
    AttackImpactAction action = AttackImpactAction::None;
    int damage = 0;
};

struct ActorNonCombatPatch
{
    ActorNonCombatAction action = ActorNonCombatAction::Stand;
    IdleBehaviorResult idleBehavior = {};
    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    bool updateYaw = false;
    float yawRadians = 0.0f;
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
};

struct CombatAbilityDecisionInput
{
    uint32_t actorId = 0;
    uint32_t attackDecisionCount = 0;
    bool hasSpell1 = false;
    int spell1UseChance = 0;
    bool hasSpell2 = false;
    int spell2UseChance = 0;
    int attack2Chance = 0;
    GameplayActorAttackConstraintState constraintState = {};
    bool movementAllowed = false;
    bool targetIsActor = false;
    float targetEdgeDistance = 0.0f;
    bool inMeleeRange = false;
    bool chooseRandomAbility = true;
    bool applyAbilityConstraints = true;
};

struct CombatAbilityDecisionResult
{
    GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
    uint32_t nextAttackDecisionCount = 0;
    bool abilityIsRanged = false;
    bool abilityIsMelee = true;
    bool stationaryOrTooCloseForRangedPursuit = false;
};

struct CombatEngageDecisionInput
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

struct CombatEngageDecisionResult
{
    CombatEngageDecisionAction action = CombatEngageDecisionAction::StartMeleePursuit;
    PursueActionMode pursueMode = PursueActionMode::Direct;
    bool meleePursuitActive = false;
    bool preserveCrowdSteering = false;
    bool useRecoveryFloorForPursuit = false;
};

struct CombatEngageApplicationInput
{
    CombatEngageDecisionAction action = CombatEngageDecisionAction::StartMeleePursuit;
    PursueActionMode pursueMode = PursueActionMode::Direct;
    bool useRecoveryFloorForPursuit = false;
    float recoverySeconds = 0.0f;
};

struct CombatEngageApplicationResult
{
    CombatEngageApplicationState state = CombatEngageApplicationState::Standing;
    CombatEngageApplicationAnimation animation = CombatEngageApplicationAnimation::Standing;
    PursueActionMode pursueMode = PursueActionMode::Direct;
    bool clearMoveDirection = false;
    bool faceTarget = false;
    bool startAttack = false;
    bool useCurrentMoveAsDesired = false;
    bool startPursueAction = false;
    float minimumPursueActionSeconds = 0.0f;
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
    IdleBehaviorResult result = idleStandBehavior(false);
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
        result = idleStandBehavior(false);
        result.nextDecisionCount = idleDecisionCount + 1;
        result.updateYaw = true;
        result.yawRadians = proposedYaw;
    }

    return result;
}

int averageAttackDamage(const AttackDamageProfile &profile)
{
    if (profile.diceRolls <= 0 || profile.diceSides <= 0)
    {
        return std::max(0, profile.bonus);
    }

    return profile.diceRolls * (profile.diceSides + 1) / 2 + profile.bonus;
}

int resolveBaseAttackImpactDamage(
    GameplayActorAttackAbility ability,
    int monsterLevel,
    const AttackDamageProfile &attack1Damage,
    const AttackDamageProfile &attack2Damage)
{
    const int fallbackAttackDamage = std::max(1, monsterLevel / 2);
    const int fallbackSpellDamage = std::max(2, monsterLevel);

    switch (ability)
    {
        case GameplayActorAttackAbility::Attack2:
        {
            const int damage = averageAttackDamage(attack2Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
        case GameplayActorAttackAbility::Spell1:
        case GameplayActorAttackAbility::Spell2:
            return fallbackSpellDamage;
        case GameplayActorAttackAbility::Attack1:
        default:
        {
            const int damage = averageAttackDamage(attack1Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
    }
}

AttackStartPatch startAttack(
    uint32_t actorId,
    uint32_t attackDecisionCount,
    bool abilityIsRanged,
    float attackAnimationSeconds,
    float recoverySeconds)
{
    AttackStartPatch result = {};

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
    return result;
}

AttackImpactPatch finishAttackImpact(
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
    bool darkGraspActive)
{
    AttackImpactPatch result = {};
    result.damage = resolveBaseAttackImpactDamage(ability, monsterLevel, attack1Damage, attack2Damage);

    if (shrinkActive)
    {
        result.damage = std::max(
            1,
            static_cast<int>(std::round(static_cast<float>(result.damage) * shrinkDamageMultiplier)));
    }

    if (darkGraspActive && abilityIsMelee)
    {
        result.damage = std::max(1, (result.damage + 1) / 2);
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

GameplayActorAttackAbility fallbackMeleeAttackAbility(
    GameplayActorAttackAbility chosenAbility,
    const GameplayActorAttackConstraintState &constraints)
{
    if (chosenAbility == GameplayActorAttackAbility::Attack1 && !constraints.attack1IsRanged)
    {
        return chosenAbility;
    }

    if (!constraints.attack1IsRanged)
    {
        return GameplayActorAttackAbility::Attack1;
    }

    if (!constraints.attack2IsRanged)
    {
        return GameplayActorAttackAbility::Attack2;
    }

    return chosenAbility;
}

float meleeRangeForCombatTarget(bool targetIsActor)
{
    return targetIsActor ? ActorMeleeRange * 0.5f : ActorMeleeRange;
}

GameplayActorAttackChoiceResult chooseAttackAbility(
    uint32_t actorId,
    uint32_t attackDecisionCount,
    bool hasSpell1,
    int spell1UseChance,
    bool hasSpell2,
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

    if (hasSpell1 && passesChance(spell1UseChance, 0x13579bdfu))
    {
        result.ability = GameplayActorAttackAbility::Spell1;
        return result;
    }

    if (hasSpell2 && passesChance(spell2UseChance, 0x2468ace0u))
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
    const GameplayActorAttackConstraintState &constraints)
{
    if (!attackAbilityIsRanged(chosenAbility, constraints))
    {
        return chosenAbility;
    }

    if (constraints.blindActive || constraints.darkGraspActive || !constraints.rangedCommitAllowed)
    {
        return fallbackMeleeAttackAbility(chosenAbility, constraints);
    }

    return chosenAbility;
}

bool shouldCommitToRangedAbility(const RangedAbilityCommitInput &input)
{
    if (!input.abilityIsRanged)
    {
        return false;
    }

    if (input.targetEdgeDistance >= 5120.0f)
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

CombatAbilityDecisionResult resolveCombatAbilityDecision(const CombatAbilityDecisionInput &input)
{
    CombatAbilityDecisionResult result = {};
    result.nextAttackDecisionCount = input.attackDecisionCount;

    GameplayActorAttackAbility chosenAbility = GameplayActorAttackAbility::Attack1;

    if (input.chooseRandomAbility)
    {
        const GameplayActorAttackChoiceResult attackChoice =
            chooseAttackAbility(
                input.actorId,
                input.attackDecisionCount,
                input.hasSpell1,
                input.spell1UseChance,
                input.hasSpell2,
                input.spell2UseChance,
                input.attack2Chance);
        result.nextAttackDecisionCount = attackChoice.nextDecisionCount;
        chosenAbility = attackChoice.ability;
    }

    GameplayActorAttackConstraintState constraintState = input.constraintState;

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

        if (!shouldCommitToRangedAbility(rangedCommitInput))
        {
            constraintState.rangedCommitAllowed = false;
        }
    }

    if (input.applyAbilityConstraints)
    {
        chosenAbility = resolveAttackAbilityConstraints(chosenAbility, constraintState);
    }

    const bool rawAbilityIsRanged = attackAbilityIsRanged(chosenAbility, input.constraintState);
    result.ability = chosenAbility;
    result.abilityIsRanged =
        rawAbilityIsRanged
        && !input.constraintState.darkGraspActive
        && !input.constraintState.blindActive;
    result.abilityIsMelee = !rawAbilityIsRanged;
    result.stationaryOrTooCloseForRangedPursuit = !input.movementAllowed || input.inMeleeRange;
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

float attackAnimationSecondsForAbility(
    const ActorAiFacts &actor,
    GameplayActorAttackAbility ability,
    const GameplayActorAttackConstraintState &constraints)
{
    return attackAbilityIsRanged(ability, constraints)
        ? actor.runtime.rangedAttackAnimationSeconds
        : actor.runtime.meleeAttackAnimationSeconds;
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
    target.partyCanSense = actor.target.partyCanSenseActor;

    return target;
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
    result.shouldEngageTarget = result.hasCombatTarget && combatTarget.canSense;
    result.inMeleeRange = combatTarget.edgeDistance <= meleeRangeForCombatTarget(result.targetIsActor);

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

    if (result.targetIsParty && !actor.status.hasDetectedParty)
    {
        result.hasDetectedParty = true;
        result.shouldPlayPartyAlert = true;
    }
    else if (!result.targetIsParty || !combatTarget.partyCanSense)
    {
        result.hasDetectedParty = false;
    }

    result.shouldFlee =
        result.shouldEngageTarget
        && combatTarget.distanceToTarget <= HostilityLongRange
        && actorService.shouldFleeForAiType(actor.stats.aiType, actor.stats.currentHp, actor.stats.maxHp);
    result.friendlyNearParty =
        !result.shouldEngageTarget
        && !actor.status.hostileToParty
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
        || state.darkGraspRemainingSeconds > 0.0f;
}

ActorAiUpdate makeActorUpdate(const ActorAiFacts &actor)
{
    ActorAiUpdate update = {};
    update.actorIndex = actor.actorIndex;
    return update;
}

struct ActorFrameTimerAging
{
    float idleDecisionSeconds = 0.0f;
    float attackCooldownSeconds = 0.0f;
    float actionSeconds = 0.0f;
    float crowdSideLockRemainingSeconds = 0.0f;
    float crowdRetreatRemainingSeconds = 0.0f;
    float crowdStandRemainingSeconds = 0.0f;
};

struct ActorFrameCommitPatch
{
    bool keepCurrentAnimation = false;
    bool resetAnimationTime = false;
    bool resetCrowdSteering = false;
    bool clearVelocity = true;
    bool applyMovement = false;
};

struct ActorMovementBlockPatch
{
    bool zeroVelocity = false;
    bool resetMoveDirection = false;
    bool stand = false;
    float actionSeconds = 0.0f;
};

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

struct ActorCombatFlowPatch
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
    bool attackJustCompleted = false;
};

enum class ActorDeathFrameAction : uint8_t
{
    Continue = 0,
    HoldDead = 1,
    MarkDead = 2,
    AdvanceDying = 3,
};

struct ActorDeathFramePatch
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

struct ActorStatusFramePatch
{
    ActorStatusFrameAction action = ActorStatusFrameAction::Continue;
    float actionSeconds = 0.0f;
};

ActorStatusFramePatch resolveActorStatusFrame(
    bool currentlyStunned,
    bool paralyzeActive,
    bool stunActive,
    float actionSeconds,
    float stunRemainingSeconds,
    float deltaSeconds)
{
    ActorStatusFramePatch result = {};
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

ActorAttackFrameState buildActorAttackFrameState(bool attacking, bool impactTriggered, float actionSeconds)
{
    ActorAttackFrameState result = {};

    if (!attacking)
    {
        return result;
    }

    result.attackInProgress = actionSeconds > 0.0f;
    result.attackJustCompleted = !result.attackInProgress && !impactTriggered;
    return result;
}

ActorDeathFramePatch resolveActorDeathFrame(
    bool dead,
    bool hpDepleted,
    bool dying,
    float actionSeconds,
    float deltaSeconds)
{
    ActorDeathFramePatch result = {};

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
    const float recoveryStepSeconds =
        deltaSeconds / std::max(1.0f, actor.status.spellEffects.slowRecoveryMultiplier);
    const bool attacking = actor.runtime.motionState == ActorAiMotionState::Attacking;

    result.idleDecisionSeconds = std::max(0.0f, actor.runtime.idleDecisionSeconds - deltaSeconds);
    result.attackCooldownSeconds = std::max(0.0f, actor.runtime.attackCooldownSeconds - recoveryStepSeconds);
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
    return result;
}

ActorFrameCommitPatch buildActiveFrameCommitPatch(
    const ActorAiFacts &actor,
    const ActorAiUpdate &update,
    bool attackInProgress)
{
    ActorFrameCommitPatch result = {};
    result.keepCurrentAnimation = attackInProgress;
    result.resetAnimationTime = false;
    result.resetCrowdSteering = !update.preserveCrowdSteering;
    result.applyMovement =
        actor.movement.movementAllowed
        && (std::abs(update.movementIntent.desiredMoveX) > 0.001f
            || std::abs(update.movementIntent.desiredMoveY) > 0.001f);
    return result;
}

ActorMovementBlockPatch buildPostMovementBlockPatch(const ActorAiFacts &actor)
{
    ActorMovementBlockPatch result = {};

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

ActorCombatFlowPatch buildCombatFlowPatch(
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
    ActorCombatFlowPatch result = {};
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

CombatEngageDecisionResult resolveCombatEngageDecision(const CombatEngageDecisionInput &input)
{
    CombatEngageDecisionResult result = {};
    const bool currentlyPursuingWithMoveDirection =
        input.currentlyPursuing
        && input.actionSeconds > 0.0f
        && (std::abs(input.currentMoveDirectionX) > 0.001f
            || std::abs(input.currentMoveDirectionY) > 0.001f);

    if (input.abilityIsMelee && input.crowdStandActive)
    {
        result.action = CombatEngageDecisionAction::HoldCrowdStand;
        result.preserveCrowdSteering = true;
        return result;
    }

    if (input.abilityIsRanged)
    {
        if (input.attackCooldownReady)
        {
            result.action = CombatEngageDecisionAction::StartRangedAttack;
            return result;
        }

        if (input.stationaryOrTooCloseForRangedPursuit)
        {
            result.action = CombatEngageDecisionAction::StandForRangedBlock;
            return result;
        }

        if (currentlyPursuingWithMoveDirection)
        {
            result.action = CombatEngageDecisionAction::ContinueRangedPursuit;
            return result;
        }

        result.action = CombatEngageDecisionAction::StartRangedPursuit;
        result.pursueMode = PursueActionMode::OffsetShort;
        result.useRecoveryFloorForPursuit = true;
        return result;
    }

    if (input.abilityIsMelee && input.inMeleeRange)
    {
        if (input.attackCooldownReady)
        {
            result.action = CombatEngageDecisionAction::StartMeleeAttack;
            return result;
        }

        result.action = CombatEngageDecisionAction::StandForMeleeCooldown;
        return result;
    }

    result.meleePursuitActive = input.abilityIsMelee;
    result.preserveCrowdSteering = input.abilityIsMelee;

    if (!input.movementAllowed)
    {
        result.action = CombatEngageDecisionAction::StartMeleePursuitWithoutMovement;
        return result;
    }

    if (currentlyPursuingWithMoveDirection)
    {
        result.action = CombatEngageDecisionAction::ContinueMeleePursuit;
        return result;
    }

    result.action = CombatEngageDecisionAction::StartMeleePursuit;
    result.pursueMode =
        input.targetEdgeDistance >= 1024.0f ? PursueActionMode::OffsetWide : PursueActionMode::Direct;
    return result;
}

CombatEngageApplicationResult resolveCombatEngageApplication(const CombatEngageApplicationInput &input)
{
    CombatEngageApplicationResult result = {};
    result.pursueMode = input.pursueMode;
    result.minimumPursueActionSeconds =
        input.useRecoveryFloorForPursuit ? std::max(0.0f, input.recoverySeconds) : 0.0f;

    if (input.action == CombatEngageDecisionAction::HoldCrowdStand)
    {
        result.state = CombatEngageApplicationState::Standing;
        result.animation = CombatEngageApplicationAnimation::BoredOrStanding;
        result.clearMoveDirection = true;
        return result;
    }

    if (input.action == CombatEngageDecisionAction::StartRangedAttack
        || input.action == CombatEngageDecisionAction::StartMeleeAttack)
    {
        result.state = CombatEngageApplicationState::Attacking;
        result.animation = CombatEngageApplicationAnimation::AttackAbility;
        result.clearMoveDirection = true;
        result.faceTarget = true;
        result.startAttack = true;
        return result;
    }

    if (input.action == CombatEngageDecisionAction::StandForRangedBlock
        || input.action == CombatEngageDecisionAction::StandForMeleeCooldown)
    {
        result.state = CombatEngageApplicationState::Standing;
        result.animation = CombatEngageApplicationAnimation::Standing;
        result.clearMoveDirection = true;
        result.faceTarget = true;
        return result;
    }

    if (input.action == CombatEngageDecisionAction::ContinueRangedPursuit
        || input.action == CombatEngageDecisionAction::ContinueMeleePursuit)
    {
        result.state = CombatEngageApplicationState::Pursuing;
        result.animation = CombatEngageApplicationAnimation::Walking;
        result.useCurrentMoveAsDesired = true;
        return result;
    }

    if (input.action == CombatEngageDecisionAction::StartMeleePursuitWithoutMovement)
    {
        result.state = CombatEngageApplicationState::Pursuing;
        result.animation = CombatEngageApplicationAnimation::Standing;
        result.clearMoveDirection = true;
        return result;
    }

    result.state = CombatEngageApplicationState::Pursuing;
    result.animation = CombatEngageApplicationAnimation::Walking;
    result.startPursueAction = true;
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

    if (input.mode == PursueActionMode::OffsetShort)
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

ActorAiMotionState actorMotionStateFromCombatEngage(CombatEngageApplicationState state)
{
    switch (state)
    {
        case CombatEngageApplicationState::Attacking:
            return ActorAiMotionState::Attacking;
        case CombatEngageApplicationState::Pursuing:
            return ActorAiMotionState::Pursuing;
        case CombatEngageApplicationState::Standing:
        default:
            return ActorAiMotionState::Standing;
    }
}

ActorAiAnimationState actorAnimationStateFromCombatEngage(
    CombatEngageApplicationAnimation animation,
    const ActorAiFacts &actor,
    GameplayActorAttackAbility ability)
{
    switch (animation)
    {
        case CombatEngageApplicationAnimation::Walking:
            return ActorAiAnimationState::Walking;
        case CombatEngageApplicationAnimation::BoredOrStanding:
            return actor.runtime.animationState == ActorAiAnimationState::Bored
                ? ActorAiAnimationState::Bored
                : ActorAiAnimationState::Standing;
        case CombatEngageApplicationAnimation::AttackAbility:
            return attackAnimationStateForAbility(ability, actor.stats.attackConstraints);
        case CombatEngageApplicationAnimation::Standing:
        default:
            return ActorAiAnimationState::Standing;
    }
}

void applyCombatFlowApplication(
    const ActorAiFacts &actor,
    const ActorCombatFlowPatch &application,
    ActorAiUpdate &update)
{
    update.combatFlowHandled = true;
    update.statePatch.motionState = actorMotionStateFromCombatFlow(application.motion);
    update.animationPatch.animationState = actorAnimationStateFromCombatFlow(application.animation, actor);
    update.statePatch.actionSeconds = application.actionSeconds;
    update.statePatch.idleDecisionSeconds = application.idleDecisionSeconds;

    if (application.motion == ActorCombatFlowMotion::Attacking)
    {
        update.movementIntent.action = ActorAiMovementAction::Stand;
    }
    else if (application.motion == ActorCombatFlowMotion::Wandering)
    {
        update.movementIntent.action = ActorAiMovementAction::Wander;
    }
    else if (application.motion == ActorCombatFlowMotion::Fleeing)
    {
        update.movementIntent.action = ActorAiMovementAction::Flee;
    }
    else
    {
        update.movementIntent.action = ActorAiMovementAction::Stand;
    }

    if (application.clearMoveDirection)
    {
        update.movementIntent.moveDirectionX = 0.0f;
        update.movementIntent.moveDirectionY = 0.0f;
    }

    if (application.updateMoveDirection)
    {
        update.movementIntent.moveDirectionX = application.moveDirectionX;
        update.movementIntent.moveDirectionY = application.moveDirectionY;
    }

    if (application.updateDesiredMove)
    {
        update.movementIntent.desiredMoveX = application.desiredMoveX;
        update.movementIntent.desiredMoveY = application.desiredMoveY;
        update.movementIntent.applyMovement = true;
    }

    if (application.updateYaw)
    {
        update.movementIntent.updateYaw = true;
        update.movementIntent.yawRadians = application.yawRadians;
    }

    if (application.clearVelocity)
    {
        update.movementIntent.clearVelocity = true;
    }
}

void applyActiveFrameCommitPatch(
    const ActorAiFacts &actor,
    bool attackInProgress,
    ActorAiUpdate &update)
{
    const ActorFrameCommitPatch frameCommit = buildActiveFrameCommitPatch(actor, update, attackInProgress);

    update.frameCommitHandled = true;
    update.animationPatch.keepCurrentAnimation = frameCommit.keepCurrentAnimation;
    update.animationPatch.resetAnimationTime = frameCommit.resetAnimationTime;
    update.resetCrowdSteering = frameCommit.resetCrowdSteering;
    update.movementIntent.clearVelocity = frameCommit.clearVelocity;
    update.movementIntent.applyMovement = frameCommit.applyMovement;
}

std::optional<ActorCombatFlowPatch> resolveSharedCombatFlowApplication(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    bool attackInProgress)
{
    const ActorTargetState combatTarget = buildActorTargetStateFromFacts(actor);
    const GameplayActorService actorService = {};
    const ActorEngagementState engagement =
        resolveActorEngagement(actor, frame, actorService);

    const ActorCombatFlowAction flowAction = chooseCombatFlowAction(
        attackInProgress,
        actor.status.spellEffects.blindRemainingSeconds > 0.0f,
        engagement.shouldFlee,
        actor.status.spellEffects.fearRemainingSeconds > 0.0f,
        engagement.shouldEngageTarget,
        engagement.friendlyNearParty);

    if (!combatFlowActionCanBeAppliedByShared(flowAction))
    {
        return std::nullopt;
    }

    const float actionSeconds = std::max(
        0.0f,
        actor.runtime.actionSeconds - (actor.runtime.motionState == ActorAiMotionState::Attacking
            ? frame.fixedStepSeconds / std::max(1.0f, actor.status.spellEffects.slowRecoveryMultiplier)
            : frame.fixedStepSeconds));
    const float idleDecisionSeconds =
        std::max(0.0f, actor.runtime.idleDecisionSeconds - frame.fixedStepSeconds);

    return buildCombatFlowPatch(
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
        target.hasLineOfSight = true;
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

ActorAiUpdate aiHoldDeathState(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiUpdate update = makeActorUpdate(actor);
    const ActorDeathFramePatch deathFrame = resolveActorDeathFrame(
        actor.status.dead || actor.runtime.motionState == ActorAiMotionState::Dead,
        actor.stats.currentHp <= 0,
        actor.runtime.motionState == ActorAiMotionState::Dying,
        actor.runtime.actionSeconds,
        frame.fixedStepSeconds);

    update.statePatch.attackImpactTriggered = false;
    update.movementIntent.action = ActorAiMovementAction::Stand;
    update.movementIntent.clearVelocity = true;

    if (deathFrame.action == ActorDeathFrameAction::HoldDead)
    {
        update.statePatch.motionState = ActorAiMotionState::Dead;
        update.animationPatch.animationState = ActorAiAnimationState::Dead;
        return update;
    }

    if (deathFrame.action == ActorDeathFrameAction::MarkDead || deathFrame.finishedDying)
    {
        ActorFxRequest deathFx = {};
        deathFx.kind = ActorAiFxRequestKind::Death;
        deathFx.actorIndex = actor.actorIndex;
        deathFx.position = actor.movement.position;
        update.fxRequests.push_back(deathFx);

        update.statePatch.dead = true;
        update.statePatch.motionState = ActorAiMotionState::Dead;
        update.statePatch.actionSeconds = 0.0f;
        update.animationPatch.animationState = ActorAiAnimationState::Dead;
        update.animationPatch.animationTimeTicks = 0.0f;
        return update;
    }

    if (deathFrame.action == ActorDeathFrameAction::AdvanceDying)
    {
        ActorFxRequest deathFx = {};
        deathFx.kind = ActorAiFxRequestKind::Death;
        deathFx.actorIndex = actor.actorIndex;
        deathFx.position = actor.movement.position;
        update.fxRequests.push_back(deathFx);

        update.statePatch.motionState = ActorAiMotionState::Dying;
        update.statePatch.actionSeconds = deathFrame.actionSeconds;
        update.animationPatch.animationState = ActorAiAnimationState::Dying;
        update.animationPatch.animationTimeTicks =
            actor.runtime.animationTimeTicks + frame.fixedStepSeconds * ActorAiTicksPerSecond;
    }

    return update;
}

float ageActorAnimationTimeTicks(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    return actor.runtime.animationTimeTicks + actorAnimationTickDelta(actor, frame);
}

void applyActiveAnimationTickPatch(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
{
    if (!actor.world.active)
    {
        return;
    }

    update.animationPatch.animationTimeTicks = ageActorAnimationTimeTicks(actor, frame);
}

void clearActorMovement(ActorAiUpdate &update)
{
    update.movementIntent.action = ActorAiMovementAction::Stand;
    update.movementIntent.clearVelocity = true;
}

void applyActiveSpellTimerPatch(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
{
    if (!actor.world.active || update.statePatch.spellEffects || !hasActiveSpellEffectTimer(actor.status.spellEffects))
    {
        return;
    }

    GameplayActorSpellEffectState spellEffects = actor.status.spellEffects;
    const GameplayActorService actorService = {};
    actorService.updateSpellEffectTimers(spellEffects, frame.fixedStepSeconds, actor.status.defaultHostileToParty);
    update.statePatch.spellEffects = spellEffects;
}

void applyStatusContinuationPatch(const std::optional<ActorAiUpdate> &statusUpdate, ActorAiUpdate &update)
{
    if (!statusUpdate || !statusUpdate->statePatch.spellEffects)
    {
        return;
    }

    update.statePatch.spellEffects = *statusUpdate->statePatch.spellEffects;
}

void applyActiveFrameTimerPatch(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
{
    if (!actor.world.active)
    {
        return;
    }

    const ActorFrameTimerAging frameTimers = ageActorFrameTimers(actor, frame);

    update.statePatch.idleDecisionSeconds = frameTimers.idleDecisionSeconds;
    update.statePatch.attackCooldownSeconds = frameTimers.attackCooldownSeconds;
    update.statePatch.actionSeconds = frameTimers.actionSeconds;
    update.statePatch.crowdSideLockRemainingSeconds = frameTimers.crowdSideLockRemainingSeconds;
    update.statePatch.crowdRetreatRemainingSeconds = frameTimers.crowdRetreatRemainingSeconds;
    update.statePatch.crowdStandRemainingSeconds = frameTimers.crowdStandRemainingSeconds;
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
    return eligibility.contactedActorCount > 0
        && eligibility.meleePursuitActive
        && eligibility.pursuing
        && !eligibility.actorCanFly
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

void applyCrowdSteeringStatePatch(const CrowdSteeringState &state, ActorAiUpdate &update)
{
    update.statePatch.crowdNoProgressSeconds = state.noProgressSeconds;
    update.statePatch.crowdLastEdgeDistance = state.lastEdgeDistance;
    update.statePatch.crowdRetreatRemainingSeconds = state.retreatRemainingSeconds;
    update.statePatch.crowdStandRemainingSeconds = state.standRemainingSeconds;
    update.statePatch.crowdProbeEdgeDistance = state.probeEdgeDistance;
    update.statePatch.crowdProbeElapsedSeconds = state.probeElapsedSeconds;
    update.statePatch.crowdEscapeAttempts = state.escapeAttempts;
    update.statePatch.crowdSideSign = state.sideSign;
}

void applyCrowdStandPatch(const CrowdSteeringResult &crowdSteering, ActorAiUpdate &update)
{
    const GameplayActorService actorService = {};
    IdleBehaviorResult idleBehavior = idleStandBehavior(crowdSteering.bored);
    idleBehavior.actionSeconds = std::max(idleBehavior.actionSeconds, crowdSteering.standSeconds);
    idleBehavior.idleDecisionSeconds = std::max(idleBehavior.idleDecisionSeconds, crowdSteering.standSeconds);

    update.statePatch.motionState = ActorAiMotionState::Standing;
    update.statePatch.actionSeconds = idleBehavior.actionSeconds;
    update.statePatch.idleDecisionSeconds = idleBehavior.idleDecisionSeconds;
    update.statePatch.attackImpactTriggered = false;
    update.statePatch.crowdSideLockRemainingSeconds = 0.0f;
    update.animationPatch.animationState =
        idleBehavior.bored ? ActorAiAnimationState::Bored : ActorAiAnimationState::Standing;
    update.animationPatch.animationTimeTicks = 0.0f;
    update.movementIntent.action = ActorAiMovementAction::Stand;
    update.movementIntent.moveDirectionX = 0.0f;
    update.movementIntent.moveDirectionY = 0.0f;
    update.movementIntent.clearVelocity = true;

}

void applyCrowdMovePatch(
    const ActorAiFacts &actor,
    const CrowdSteeringResult &crowdSteering,
    bool retreat,
    ActorAiUpdate &update)
{
    const int sideSign = crowdSteering.sideSign > 0 ? 1 : -1;
    const float angleOffset =
        retreat
        ? (sideSign > 0 ? ActorCrowdRetreatAngleRadians : -ActorCrowdRetreatAngleRadians)
        : (sideSign > 0 ? Pi / 4.0f : -Pi / 4.0f);
    const float yaw = normalizeAngleRadians(
        std::atan2(
            actor.target.currentPosition.y - actor.movement.position.y,
            actor.target.currentPosition.x - actor.movement.position.x)
        + angleOffset);
    const float actionSeconds =
        retreat
        ? std::max(actor.runtime.actionSeconds, crowdSteering.retreatSeconds)
        : std::max(actor.runtime.actionSeconds, ActorCrowdSideLockSeconds);

    update.statePatch.motionState = ActorAiMotionState::Pursuing;
    update.statePatch.actionSeconds = actionSeconds;
    update.statePatch.attackImpactTriggered = false;
    update.statePatch.crowdSideLockRemainingSeconds =
        retreat ? crowdSteering.retreatSeconds : ActorCrowdSideLockSeconds;
    update.animationPatch.animationState = ActorAiAnimationState::Walking;
    update.movementIntent.action = ActorAiMovementAction::Pursue;
    update.movementIntent.updateYaw = true;
    update.movementIntent.yawRadians = yaw;
    update.movementIntent.moveDirectionX = std::cos(yaw);
    update.movementIntent.moveDirectionY = std::sin(yaw);
    update.movementIntent.desiredMoveX = update.movementIntent.moveDirectionX;
    update.movementIntent.desiredMoveY = update.movementIntent.moveDirectionY;
    update.movementIntent.applyMovement = true;
}

void applyPostMovementCrowdSteering(const ActorAiFacts &actor, ActorAiUpdate &update)
{
    if (!actor.movement.allowCrowdSteering)
    {
        return;
    }

    CrowdSteeringEligibility crowdSteering = {};
    crowdSteering.contactedActorCount = actor.movement.contactedActorCount;
    crowdSteering.meleePursuitActive = actor.movement.meleePursuitActive;
    crowdSteering.pursuing = actor.runtime.motionState == ActorAiMotionState::Pursuing;
    crowdSteering.actorCanFly = actor.stats.canFly;
    crowdSteering.inMeleeRange = actor.movement.inMeleeRange;
    crowdSteering.targetEdgeDistance = actor.target.currentEdgeDistance;

    if (!shouldApplyCrowdSteering(crowdSteering))
    {
        return;
    }

    const CrowdSteeringResult crowdSteeringResult =
        resolveCrowdSteering(
            actor.actorId,
            actor.runtime.pursueDecisionCount,
            actor.target.currentEdgeDistance,
            ActorAiUpdateStepSeconds,
            buildCrowdSteeringState(actor));

    update.crowdSteeringHandled = true;
    update.statePatch.pursueDecisionCount = crowdSteeringResult.nextDecisionCount;
    applyCrowdSteeringStatePatch(crowdSteeringResult.state, update);

    if (crowdSteeringResult.action == CrowdSteeringAction::Stand)
    {
        applyCrowdStandPatch(crowdSteeringResult, update);
    }
    else if (crowdSteeringResult.action == CrowdSteeringAction::Retreat)
    {
        applyCrowdMovePatch(actor, crowdSteeringResult, true, update);
    }
    else
    {
        applyCrowdMovePatch(actor, crowdSteeringResult, false, update);
    }
}

void applyCombatEngagementPatch(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
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
        update.statePatch.hostilityType = engagement.hostilityType;
    }

    if (engagement.hasDetectedParty != actor.status.hasDetectedParty)
    {
        update.statePatch.hasDetectedParty = engagement.hasDetectedParty;
    }

    if (engagement.shouldPlayPartyAlert)
    {
        ActorAudioRequest alert = {};
        alert.kind = ActorAiAudioRequestKind::Alert;
        alert.actorIndex = actor.actorIndex;
        alert.position = actor.movement.position;
        alert.position.z += static_cast<float>(actor.stats.height) * 0.5f;
        update.audioRequests.push_back(alert);
    }
}

void applyAttackImpactPatch(const ActorAiFacts &actor, ActorAiUpdate &update)
{
    if (!actor.world.active || actor.runtime.motionState != ActorAiMotionState::Attacking)
    {
        return;
    }

    const float actionSeconds = update.statePatch.actionSeconds.value_or(actor.runtime.actionSeconds);
    const ActorAttackFrameState attackFrame =
        buildActorAttackFrameState(true, actor.runtime.attackImpactTriggered, actionSeconds);

    if (!attackFrame.attackJustCompleted)
    {
        return;
    }

    const bool abilityIsRanged =
        attackAbilityIsRanged(actor.runtime.queuedAttackAbility, actor.stats.attackConstraints);
    const bool abilityIsMelee = !abilityIsRanged;
    const AttackImpactPatch attackImpact = finishAttackImpact(
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
        actor.status.spellEffects.darkGraspRemainingSeconds > 0.0f);

    update.statePatch.attackImpactTriggered = true;

    if (attackImpact.action == AttackImpactAction::None)
    {
        return;
    }

    ActorAttackRequest request = {};
    request.ability = actor.runtime.queuedAttackAbility;
    request.targetKind = actor.target.currentKind;
    request.targetActorIndex = actor.target.currentActorIndex;
    request.damage = attackImpact.damage;
    request.source = actor.movement.position;
    request.target = actor.target.currentPosition;

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

        if (actor.target.currentActorIndex != static_cast<size_t>(-1) && actor.target.currentHp > 0)
        {
            ActorAudioRequest hitAudio = {};
            hitAudio.kind =
                attackImpact.damage >= actor.target.currentHp
                ? ActorAiAudioRequestKind::Death
                : ActorAiAudioRequestKind::Hit;
            hitAudio.actorIndex = actor.target.currentActorIndex;
            hitAudio.position = actor.target.currentAudioPosition;
            update.audioRequests.push_back(hitAudio);
        }
    }

    update.attackRequest = request;
}

bool applyEngageTargetBehavior(const ActorAiFacts &actor, const ActorAiFrameFacts &frame, ActorAiUpdate &update)
{
    if (!actor.world.active)
    {
        return false;
    }

    const GameplayActorService actorService = {};
    const ActorEngagementState engagement =
        resolveActorEngagement(actor, frame, actorService);

    if (!engagement.shouldEngageTarget)
    {
        return false;
    }

    CombatAbilityDecisionInput abilityInput = {};
    abilityInput.actorId = actor.actorId;
    abilityInput.attackDecisionCount = actor.runtime.attackDecisionCount;
    abilityInput.hasSpell1 = actor.stats.hasSpell1;
    abilityInput.spell1UseChance = actor.stats.spell1UseChance;
    abilityInput.hasSpell2 = actor.stats.hasSpell2;
    abilityInput.spell2UseChance = actor.stats.spell2UseChance;
    abilityInput.attack2Chance = actor.stats.attack2Chance;
    abilityInput.constraintState = actor.stats.attackConstraints;
    abilityInput.movementAllowed = actor.movement.movementAllowed;
    abilityInput.targetIsActor = engagement.targetIsActor;
    abilityInput.targetEdgeDistance = actor.target.currentEdgeDistance;
    abilityInput.inMeleeRange = engagement.inMeleeRange;
    abilityInput.chooseRandomAbility = true;
    abilityInput.applyAbilityConstraints = true;
    const CombatAbilityDecisionResult abilityDecision = resolveCombatAbilityDecision(abilityInput);

    CombatEngageDecisionInput engageInput = {};
    engageInput.abilityIsRanged = abilityDecision.abilityIsRanged;
    engageInput.abilityIsMelee = abilityDecision.abilityIsMelee;
    engageInput.inMeleeRange = engagement.inMeleeRange;
    engageInput.attackCooldownReady = actor.runtime.attackCooldownSeconds <= 0.0f;
    engageInput.movementAllowed = actor.movement.movementAllowed;
    engageInput.stationaryOrTooCloseForRangedPursuit = abilityDecision.stationaryOrTooCloseForRangedPursuit;
    engageInput.currentlyPursuing = actor.runtime.motionState == ActorAiMotionState::Pursuing;
    engageInput.crowdStandActive = actor.runtime.crowdStandRemainingSeconds > 0.0f;
    engageInput.actionSeconds = actor.runtime.actionSeconds;
    engageInput.currentMoveDirectionX = actor.movement.moveDirectionX;
    engageInput.currentMoveDirectionY = actor.movement.moveDirectionY;
    engageInput.targetEdgeDistance = actor.target.currentEdgeDistance;
    const CombatEngageDecisionResult engageDecision = resolveCombatEngageDecision(engageInput);

    CombatEngageApplicationInput engageApplicationInput = {};
    engageApplicationInput.action = engageDecision.action;
    engageApplicationInput.pursueMode = engageDecision.pursueMode;
    engageApplicationInput.useRecoveryFloorForPursuit = engageDecision.useRecoveryFloorForPursuit;
    engageApplicationInput.recoverySeconds = actor.runtime.recoverySeconds;
    const CombatEngageApplicationResult engageApplication =
        resolveCombatEngageApplication(engageApplicationInput);

    update.combatEngageHandled = true;
    update.meleePursuitActive = engageDecision.meleePursuitActive;
    update.preserveCrowdSteering = engageDecision.preserveCrowdSteering;
    update.statePatch.motionState = actorMotionStateFromCombatEngage(engageApplication.state);
    update.animationPatch.animationState =
        actorAnimationStateFromCombatEngage(engageApplication.animation, actor, abilityDecision.ability);
    update.statePatch.attackDecisionCount = abilityDecision.nextAttackDecisionCount;

    if (engageApplication.clearMoveDirection)
    {
        update.movementIntent.action = ActorAiMovementAction::Stand;
        update.movementIntent.moveDirectionX = 0.0f;
        update.movementIntent.moveDirectionY = 0.0f;
    }

    if (engageApplication.faceTarget)
    {
        update.movementIntent.updateYaw = true;
        update.movementIntent.yawRadians = std::atan2(
            actor.target.currentPosition.y - actor.movement.position.y,
            actor.target.currentPosition.x - actor.movement.position.x);
    }

    if (engageApplication.useCurrentMoveAsDesired)
    {
        update.movementIntent.desiredMoveX = actor.movement.moveDirectionX;
        update.movementIntent.desiredMoveY = actor.movement.moveDirectionY;
        update.movementIntent.applyMovement = true;
    }

    if (engageApplication.startAttack)
    {
        const float attackAnimationSeconds = attackAnimationSecondsForAbility(
            actor,
            abilityDecision.ability,
            actor.stats.attackConstraints);

        const AttackStartPatch attackStart = startAttack(
            actor.actorId,
            abilityDecision.nextAttackDecisionCount,
            abilityDecision.abilityIsRanged,
            attackAnimationSeconds,
            actor.runtime.recoverySeconds);

        update.statePatch.motionState = ActorAiMotionState::Attacking;
        update.statePatch.queuedAttackAbility = abilityDecision.ability;
        update.statePatch.attackCooldownSeconds = attackStart.attackCooldownSeconds;
        update.statePatch.actionSeconds = attackStart.actionSeconds;
        update.statePatch.attackImpactTriggered = false;
        update.animationPatch.animationState =
            attackAnimationStateForAbility(abilityDecision.ability, actor.stats.attackConstraints);
        update.animationPatch.animationTimeTicks = 0.0f;
        update.movementIntent.action = ActorAiMovementAction::Stand;
        update.movementIntent.clearVelocity = false;
        update.movementIntent.moveDirectionX = 0.0f;
        update.movementIntent.moveDirectionY = 0.0f;

        ActorAudioRequest attackAudio = {};
        attackAudio.kind = ActorAiAudioRequestKind::Attack;
        attackAudio.actorIndex = actor.actorIndex;
        attackAudio.position = actor.movement.position;
        attackAudio.position.z += static_cast<float>(actor.stats.height) * 0.5f;
        update.audioRequests.push_back(attackAudio);
        return true;
    }

    if (engageApplication.startPursueAction)
    {
        const ActorTargetState combatTarget = buildActorTargetStateFromFacts(actor);

        PursueActionInput pursueInput = {};
        pursueInput.actorId = actor.actorId;
        pursueInput.pursueDecisionCount = actor.runtime.pursueDecisionCount;
        pursueInput.deltaTargetX = combatTarget.deltaX;
        pursueInput.deltaTargetY = combatTarget.deltaY;
        pursueInput.distanceToTarget = combatTarget.horizontalDistanceToTarget;
        pursueInput.moveSpeed = actor.movement.effectiveMoveSpeed;
        pursueInput.minimumActionSeconds = engageApplication.minimumPursueActionSeconds;
        pursueInput.mode = engageApplication.pursueMode;
        const PursueActionResult pursueAction = resolvePursueAction(pursueInput);
        update.statePatch.pursueDecisionCount = pursueAction.nextDecisionCount;

        if (pursueAction.started)
        {
            update.movementIntent.action = ActorAiMovementAction::Pursue;
            update.movementIntent.updateYaw = true;
            update.movementIntent.yawRadians = pursueAction.yawRadians;
            update.movementIntent.moveDirectionX = pursueAction.moveDirectionX;
            update.movementIntent.moveDirectionY = pursueAction.moveDirectionY;
            update.movementIntent.desiredMoveX = pursueAction.moveDirectionX;
            update.movementIntent.desiredMoveY = pursueAction.moveDirectionY;
            update.movementIntent.applyMovement = true;
            update.statePatch.actionSeconds = pursueAction.actionSeconds;
            update.statePatch.attackImpactTriggered = false;
        }
        else
        {
            update.statePatch.motionState = ActorAiMotionState::Standing;
            update.animationPatch.animationState = ActorAiAnimationState::Standing;
        }
    }

    applyActiveFrameCommitPatch(actor, false, update);
    return true;
}

std::optional<ActorAiUpdate> aiEngageTargetIfReady(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiUpdate update = makeActorUpdate(actor);
    applyActiveAnimationTickPatch(actor, frame, update);
    applyActiveSpellTimerPatch(actor, frame, update);
    applyActiveFrameTimerPatch(actor, frame, update);
    applyCombatEngagementPatch(actor, frame, update);

    if (!applyEngageTargetBehavior(actor, frame, update))
    {
        return std::nullopt;
    }

    return update;
}

std::optional<ActorAiUpdate> aiEngageTargetIfReadyWithStatusContinuation(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const std::optional<ActorAiUpdate> &statusContinuation)
{
    ActorAiUpdate update = makeActorUpdate(actor);
    applyStatusContinuationPatch(statusContinuation, update);
    applyActiveAnimationTickPatch(actor, frame, update);
    applyActiveSpellTimerPatch(actor, frame, update);
    applyActiveFrameTimerPatch(actor, frame, update);
    applyCombatEngagementPatch(actor, frame, update);

    if (!applyEngageTargetBehavior(actor, frame, update))
    {
        return std::nullopt;
    }

    return update;
}

std::optional<ActorAiUpdate> aiResolveStatusState(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiUpdate update = makeActorUpdate(actor);
    const GameplayActorService actorService = {};
    const float animationTimeTicks = ageActorAnimationTimeTicks(actor, frame);

    const ActorStatusFramePatch currentStatusFrame = resolveActorStatusFrame(
        actor.runtime.motionState == ActorAiMotionState::Stunned,
        actor.status.spellEffects.paralyzeRemainingSeconds > 0.0f,
        false,
        actor.runtime.actionSeconds,
        0.0f,
        frame.fixedStepSeconds);

    if (currentStatusFrame.action == ActorStatusFrameAction::HoldStun)
    {
        update.statusLockHandled = true;
        update.statePatch.motionState = ActorAiMotionState::Stunned;
        update.statePatch.actionSeconds = currentStatusFrame.actionSeconds;
        update.animationPatch.animationState = ActorAiAnimationState::GotHit;
        update.animationPatch.animationTimeTicks = animationTimeTicks;
        clearActorMovement(update);
        return update;
    }

    if (currentStatusFrame.action == ActorStatusFrameAction::RecoverFromStun)
    {
        update.statusLockHandled = true;
        update.statePatch.motionState = ActorAiMotionState::Standing;
        update.statePatch.actionSeconds = currentStatusFrame.actionSeconds;
        update.animationPatch.animationState = ActorAiAnimationState::Standing;
        update.animationPatch.animationTimeTicks = 0.0f;
        clearActorMovement(update);
        return update;
    }

    GameplayActorSpellEffectState spellEffects = actor.status.spellEffects;
    actorService.updateSpellEffectTimers(spellEffects, frame.fixedStepSeconds, actor.status.defaultHostileToParty);
    update.statePatch.spellEffects = spellEffects;

    const ActorStatusFramePatch updatedStatusFrame = resolveActorStatusFrame(
        false,
        spellEffects.paralyzeRemainingSeconds > 0.0f,
        spellEffects.stunRemainingSeconds > 0.0f,
        actor.runtime.actionSeconds,
        spellEffects.stunRemainingSeconds,
        0.0f);

    if (updatedStatusFrame.action == ActorStatusFrameAction::HoldParalyze)
    {
        update.statusLockHandled = true;
        update.statePatch.motionState = ActorAiMotionState::Standing;
        update.statePatch.actionSeconds = updatedStatusFrame.actionSeconds;
        update.statePatch.attackImpactTriggered = false;
        update.statePatch.spellEffects = spellEffects;
        update.animationPatch.animationState = ActorAiAnimationState::Standing;
        update.animationPatch.animationTimeTicks = 0.0f;
        clearActorMovement(update);
        return update;
    }

    if (updatedStatusFrame.action == ActorStatusFrameAction::ForceStun)
    {
        update.statusLockHandled = true;
        update.statePatch.motionState = ActorAiMotionState::Stunned;
        update.statePatch.actionSeconds = updatedStatusFrame.actionSeconds;
        update.statePatch.spellEffects = spellEffects;
        update.animationPatch.animationState = ActorAiAnimationState::GotHit;
        update.animationPatch.animationTimeTicks = animationTimeTicks;
        clearActorMovement(update);
        return update;
    }

    if (update.statePatch.spellEffects)
    {
        return update;
    }

    return std::nullopt;
}

ActorAiUpdate aiContinueAttack(const ActorAiFacts &actor)
{
    ActorAiUpdate update = makeActorUpdate(actor);
    update.statePatch.motionState = ActorAiMotionState::Attacking;
    update.animationPatch.animationState = actor.runtime.queuedAttackAbility == GameplayActorAttackAbility::Attack1
        || actor.runtime.queuedAttackAbility == GameplayActorAttackAbility::Attack2
        ? ActorAiAnimationState::AttackMelee
        : ActorAiAnimationState::AttackRanged;
    update.movementIntent.action = ActorAiMovementAction::Stand;
    return update;
}

void applyIdleBehaviorPatch(
    const IdleBehaviorResult &idleBehavior,
    ActorAiUpdate &update)
{
    update.statePatch.attackImpactTriggered = false;
    update.statePatch.actionSeconds = idleBehavior.actionSeconds;
    update.statePatch.idleDecisionSeconds = idleBehavior.idleDecisionSeconds;
    update.animationPatch.animationTimeTicks = 0.0f;

    if (idleBehavior.updateYaw)
    {
        update.movementIntent.updateYaw = true;
        update.movementIntent.yawRadians = idleBehavior.yawRadians;
    }

    if (idleBehavior.action == IdleBehaviorAction::Wander)
    {
        update.statePatch.motionState = ActorAiMotionState::Wandering;
        update.animationPatch.animationState = ActorAiAnimationState::Walking;
        update.movementIntent.action = ActorAiMovementAction::Wander;
        update.movementIntent.moveDirectionX = idleBehavior.moveDirectionX;
        update.movementIntent.moveDirectionY = idleBehavior.moveDirectionY;
        update.movementIntent.desiredMoveX = idleBehavior.moveDirectionX;
        update.movementIntent.desiredMoveY = idleBehavior.moveDirectionY;
        update.movementIntent.applyMovement = true;
        return;
    }

    update.statePatch.motionState = ActorAiMotionState::Standing;
    update.animationPatch.animationState =
        idleBehavior.bored ? ActorAiAnimationState::Bored : ActorAiAnimationState::Standing;
    update.movementIntent.action = ActorAiMovementAction::Stand;
    update.movementIntent.moveDirectionX = 0.0f;
    update.movementIntent.moveDirectionY = 0.0f;
    update.movementIntent.clearVelocity = true;
}

ActorNonCombatPatch resolveActorNonCombatBehavior(const ActorAiFacts &actor, float actionSeconds)
{
    ActorNonCombatPatch result = {};

    if (actor.status.hostileToParty || actor.movement.wanderRadius <= 0.0f)
    {
        result.action = actionSeconds <= 0.0f
            ? ActorNonCombatAction::ApplyIdleBehavior
            : ActorNonCombatAction::Stand;
        result.idleBehavior = idleStandBehavior(false);
        return result;
    }

    const float deltaHomeX = actor.movement.homePosition.x - actor.movement.position.x;
    const float deltaHomeY = actor.movement.homePosition.y - actor.movement.position.y;
    const float distanceToHome = length2d(deltaHomeX, deltaHomeY);

    if (distanceToHome > actor.movement.wanderRadius)
    {
        result.action = ActorNonCombatAction::ReturnHome;

        if (distanceToHome > 0.01f)
        {
            result.moveDirectionX = deltaHomeX / distanceToHome;
            result.moveDirectionY = deltaHomeY / distanceToHome;
            result.updateYaw = true;
            result.yawRadians = std::atan2(result.moveDirectionY, result.moveDirectionX);
        }

        return result;
    }

    const bool hasMoveDirection =
        std::abs(actor.movement.moveDirectionX) > 0.001f || std::abs(actor.movement.moveDirectionY) > 0.001f;

    if (actionSeconds > 0.0f && hasMoveDirection)
    {
        result.action = ActorNonCombatAction::ContinueMove;
        result.moveDirectionX = actor.movement.moveDirectionX;
        result.moveDirectionY = actor.movement.moveDirectionY;
        return result;
    }

    if (actor.runtime.motionState == ActorAiMotionState::Wandering)
    {
        result.action = ActorNonCombatAction::ApplyIdleBehavior;
        result.idleBehavior = idleStandBehavior(false);
        return result;
    }

    if (actionSeconds > 0.0f)
    {
        result.action = ActorNonCombatAction::Stand;
        return result;
    }

    result.action = ActorNonCombatAction::StartIdleBehavior;

    if (!actor.movement.allowIdleWander)
    {
        result.idleBehavior = idleStandBehavior(false);
        result.idleBehavior.nextDecisionCount = actor.runtime.idleDecisionCount + 1;
        return result;
    }

    result.idleBehavior = resolveIdleBehavior(
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
    return result;
}

void applyNonCombatBehavior(const ActorAiFacts &actor, ActorAiUpdate &update)
{
    const float actionSeconds = update.statePatch.actionSeconds.value_or(actor.runtime.actionSeconds);
    const ActorNonCombatPatch nonCombatBehavior = resolveActorNonCombatBehavior(actor, actionSeconds);

    update.nonCombatHandled = true;

    if (nonCombatBehavior.action == ActorNonCombatAction::ApplyIdleBehavior)
    {
        applyIdleBehaviorPatch(nonCombatBehavior.idleBehavior, update);
        update.statePatch.motionState = ActorAiMotionState::Standing;
        return;
    }

    if (nonCombatBehavior.action == ActorNonCombatAction::ReturnHome)
    {
        update.statePatch.motionState = ActorAiMotionState::Wandering;
        update.animationPatch.animationState = ActorAiAnimationState::Walking;
        update.movementIntent.action = ActorAiMovementAction::Wander;
        update.movementIntent.moveDirectionX = nonCombatBehavior.moveDirectionX;
        update.movementIntent.moveDirectionY = nonCombatBehavior.moveDirectionY;
        update.movementIntent.desiredMoveX = nonCombatBehavior.moveDirectionX;
        update.movementIntent.desiredMoveY = nonCombatBehavior.moveDirectionY;
        update.movementIntent.applyMovement = true;

        if (nonCombatBehavior.updateYaw)
        {
            update.movementIntent.updateYaw = true;
            update.movementIntent.yawRadians = nonCombatBehavior.yawRadians;
        }

        if (actor.runtime.animationState != ActorAiAnimationState::Walking)
        {
            update.animationPatch.animationTimeTicks = 0.0f;
        }

        return;
    }

    if (nonCombatBehavior.action == ActorNonCombatAction::ContinueMove)
    {
        update.statePatch.motionState = ActorAiMotionState::Wandering;
        update.animationPatch.animationState = ActorAiAnimationState::Walking;
        update.movementIntent.action = ActorAiMovementAction::Wander;
        update.movementIntent.moveDirectionX = nonCombatBehavior.moveDirectionX;
        update.movementIntent.moveDirectionY = nonCombatBehavior.moveDirectionY;
        update.movementIntent.desiredMoveX = nonCombatBehavior.moveDirectionX;
        update.movementIntent.desiredMoveY = nonCombatBehavior.moveDirectionY;
        update.movementIntent.applyMovement = true;

        if (actor.runtime.animationState != ActorAiAnimationState::Walking)
        {
            update.animationPatch.animationTimeTicks = 0.0f;
        }

        return;
    }

    if (nonCombatBehavior.action == ActorNonCombatAction::StartIdleBehavior)
    {
        update.statePatch.idleDecisionCount = nonCombatBehavior.idleBehavior.nextDecisionCount;
        applyIdleBehaviorPatch(nonCombatBehavior.idleBehavior, update);
        return;
    }

    update.statePatch.motionState = ActorAiMotionState::Standing;
    update.animationPatch.animationState = ActorAiAnimationState::Standing;
    update.movementIntent.action = ActorAiMovementAction::Stand;
    update.movementIntent.moveDirectionX = 0.0f;
    update.movementIntent.moveDirectionY = 0.0f;
    update.movementIntent.clearVelocity = true;

    if (actor.runtime.animationState != ActorAiAnimationState::Standing)
    {
        update.animationPatch.animationTimeTicks = 0.0f;
    }
}

ActorAiUpdate aiStandOrWander(const ActorAiFacts &actor)
{
    ActorAiUpdate update = makeActorUpdate(actor);

    if (actor.runtime.motionState == ActorAiMotionState::Wandering && actor.movement.movementAllowed)
    {
        update.statePatch.motionState = ActorAiMotionState::Wandering;
        update.animationPatch.animationState = ActorAiAnimationState::Walking;
        update.movementIntent.action = ActorAiMovementAction::Wander;
        update.movementIntent.moveDirectionX = actor.movement.moveDirectionX;
        update.movementIntent.moveDirectionY = actor.movement.moveDirectionY;
        update.movementIntent.applyMovement = true;
    }
    else
    {
        update.statePatch.motionState = ActorAiMotionState::Standing;
        update.animationPatch.animationState = ActorAiAnimationState::Standing;
        update.movementIntent.action = ActorAiMovementAction::Stand;
    }

    return update;
}

ActorAiUpdate aiNonCombat(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiUpdate update = aiStandOrWander(actor);
    applyActiveAnimationTickPatch(actor, frame, update);
    applyActiveSpellTimerPatch(actor, frame, update);
    applyActiveFrameTimerPatch(actor, frame, update);
    applyCombatEngagementPatch(actor, frame, update);
    applyNonCombatBehavior(actor, update);
    applyActiveFrameCommitPatch(actor, false, update);
    return update;
}

ActorAiUpdate aiNonCombatWithStatusContinuation(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame,
    const std::optional<ActorAiUpdate> &statusContinuation)
{
    ActorAiUpdate update = aiStandOrWander(actor);
    applyStatusContinuationPatch(statusContinuation, update);
    applyActiveAnimationTickPatch(actor, frame, update);
    applyActiveSpellTimerPatch(actor, frame, update);
    applyActiveFrameTimerPatch(actor, frame, update);
    applyCombatEngagementPatch(actor, frame, update);
    applyNonCombatBehavior(actor, update);
    applyActiveFrameCommitPatch(actor, false, update);
    return update;
}

void applyNonCombatBehaviorFrame(const ActorAiFacts &actor, ActorAiUpdate &update)
{
    applyNonCombatBehavior(actor, update);
    applyActiveFrameCommitPatch(actor, false, update);
}

ActorAiUpdate updateBackgroundActor(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    if (isDeadOrDying(actor))
    {
        return aiHoldDeathState(actor, frame);
    }

    if (isStatusLocked(actor))
    {
        const std::optional<ActorAiUpdate> statusUpdate = aiResolveStatusState(actor, frame);

        if (statusUpdate)
        {
            return *statusUpdate;
        }
    }

    return aiStandOrWander(actor);
}

ActorAiUpdate updateActor(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    if (isDeadOrDying(actor))
    {
        return aiHoldDeathState(actor, frame);
    }

    ActorAiFacts actorFacts = actor;
    std::optional<ActorAiUpdate> statusContinuation;

    if (isStatusLocked(actor))
    {
        const std::optional<ActorAiUpdate> statusUpdate = aiResolveStatusState(actor, frame);

        if (statusUpdate)
        {
            if (statusUpdate->statusLockHandled)
            {
                return *statusUpdate;
            }

            statusContinuation = statusUpdate;

            if (statusUpdate->statePatch.spellEffects)
            {
                actorFacts.status.spellEffects = *statusUpdate->statePatch.spellEffects;
            }
        }
    }

    const std::optional<ActorTargetCandidateFacts> target = chooseTarget(actorFacts, frame);

    if (actorFacts.runtime.motionState == ActorAiMotionState::Attacking)
    {
        ActorAiUpdate update = aiContinueAttack(actorFacts);
        applyStatusContinuationPatch(statusContinuation, update);
        applyActiveAnimationTickPatch(actorFacts, frame, update);
        applyActiveSpellTimerPatch(actorFacts, frame, update);
        applyActiveFrameTimerPatch(actorFacts, frame, update);
        applyAttackImpactPatch(actorFacts, update);
        applyCombatEngagementPatch(actorFacts, frame, update);

        const bool attackInProgress =
            update.statePatch.actionSeconds.value_or(actorFacts.runtime.actionSeconds) > 0.0f;
        const std::optional<ActorCombatFlowPatch> combatFlowApplication =
            resolveSharedCombatFlowApplication(actorFacts, frame, attackInProgress);

        if (combatFlowApplication)
        {
            applyCombatFlowApplication(actorFacts, *combatFlowApplication, update);
            applyActiveFrameCommitPatch(actorFacts, attackInProgress, update);
            return update;
        }

        if (target && applyEngageTargetBehavior(actorFacts, frame, update))
        {
            return update;
        }

        applyNonCombatBehaviorFrame(actorFacts, update);
        return update;
    }

    {
        ActorAiUpdate update = makeActorUpdate(actorFacts);
        applyStatusContinuationPatch(statusContinuation, update);
        applyActiveAnimationTickPatch(actorFacts, frame, update);
        applyActiveSpellTimerPatch(actorFacts, frame, update);
        applyActiveFrameTimerPatch(actorFacts, frame, update);
        applyCombatEngagementPatch(actorFacts, frame, update);

        const std::optional<ActorCombatFlowPatch> combatFlowApplication =
            resolveSharedCombatFlowApplication(actorFacts, frame, false);

        if (combatFlowApplication)
        {
            applyCombatFlowApplication(actorFacts, *combatFlowApplication, update);
            applyActiveFrameCommitPatch(actorFacts, false, update);
            return update;
        }
    }

    if (target)
    {
        const std::optional<ActorAiUpdate> engageTargetUpdate = statusContinuation
            ? aiEngageTargetIfReadyWithStatusContinuation(actorFacts, frame, statusContinuation)
            : aiEngageTargetIfReady(actorFacts, frame);

        if (engageTargetUpdate)
        {
            return *engageTargetUpdate;
        }

        return statusContinuation
            ? aiNonCombatWithStatusContinuation(actorFacts, frame, statusContinuation)
            : aiNonCombat(actorFacts, frame);
    }

    return statusContinuation
        ? aiNonCombatWithStatusContinuation(actorFacts, frame, statusContinuation)
        : aiNonCombat(actorFacts, frame);
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
            projectileRequest.damage = update.attackRequest->damage;
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
}

void updateBackgroundActors(const ActorAiFrameFacts &facts, ActorAiFrameResult &result)
{
    for (const ActorAiFacts &actor : facts.backgroundActors)
    {
        appendActorUpdate(result, updateBackgroundActor(actor, facts));
    }
}

void updateActiveActors(const ActorAiFrameFacts &facts, ActorAiFrameResult &result)
{
    for (const ActorAiFacts &actor : facts.activeActors)
    {
        appendActorUpdate(result, updateActor(actor, facts));
    }
}

ActorAiUpdate updateActorAfterWorldMovementInternal(const ActorAiFacts &actor)
{
    ActorAiUpdate update = makeActorUpdate(actor);

    applyPostMovementCrowdSteering(actor, update);

    const ActorMovementBlockPatch movementBlock = buildPostMovementBlockPatch(actor);

    if (movementBlock.zeroVelocity)
    {
        update.movementIntent.clearVelocity = true;
    }

    if (movementBlock.resetMoveDirection)
    {
        update.movementIntent.action = ActorAiMovementAction::Stand;
        update.movementIntent.moveDirectionX = 0.0f;
        update.movementIntent.moveDirectionY = 0.0f;
        update.statePatch.actionSeconds = movementBlock.actionSeconds;
    }

    if (movementBlock.stand)
    {
        update.statePatch.motionState = ActorAiMotionState::Standing;
        update.animationPatch.animationState = ActorAiAnimationState::Standing;
    }

    return update;
}
}

ActorAiFrameResult GameplayActorAiSystem::updateActors(const ActorAiFrameFacts &facts) const
{
    ActorAiFrameResult result = {};

    updateBackgroundActors(facts, result);
    updateActiveActors(facts, result);

    return result;
}

ActorAiUpdate GameplayActorAiSystem::updateActorAfterWorldMovement(const ActorAiFacts &facts) const
{
    return updateActorAfterWorldMovementInternal(facts);
}
}
