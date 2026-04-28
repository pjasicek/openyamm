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
constexpr float ActorCrowdSidestepAngleRadians = Pi / 4.0f;
constexpr float CrowdNoProgressThreshold = 8.0f;
constexpr float CrowdNoProgressStandSeconds = 1.2f;
constexpr float CrowdProbeWindowSeconds = 0.35f;
constexpr float CrowdProbeEdgeDistanceThreshold = 12.0f;
constexpr float CrowdReangleEngageRange = 1024.0f;
constexpr float ContactFleeFallbackSeconds = 0.25f;
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
    bool triggerOnMovementBlocked = false;
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
    bool inMeleeRange = false;
    bool chooseRandomAbility = true;
    bool applyAbilityConstraints = true;
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
    int damageBonus)
{
    AttackImpactOutcome result = {};
    result.damage = resolveBaseAttackImpactDamage(ability, monsterLevel, attack1Damage, attack2Damage)
        + std::max(0, damageBonus);

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

    if (spellName == "shield" || spellName == "stoneskin")
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

    if (spellName == "stoneskin")
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

    if (spellName == "stoneskin")
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

    if (spellName == "power cure")
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

    if (spellName == "hour of power"
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
    else if (spellName == "stoneskin")
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
    const bool hardRangedAbilityBlocked =
        input.constraintState.darkGraspActive
        || input.constraintState.blindActive
        || !input.constraintState.rangedCommitAllowed;

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
    target.attackLineOfSight = actor.target.currentHasAttackLineOfSight;
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
    result.inMeleeRange =
        combatTarget.edgeDistance <= meleeRangeForCombatTarget(result.targetIsActor)
        && combatTarget.attackLineOfSight;

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
    bool attackJustCompleted = false;
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

ActorMovementCommit buildActiveMovementCommit(
    const ActorAiFacts &actor,
    const ActorAiUpdate &update,
    bool preserveCrowdSteering)
{
    ActorMovementCommit result = {};
    const float verticalTargetDelta = actor.target.currentPosition.z - actor.world.targetZ;
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

    if (input.abilityIsMelee && input.crowdStandActive)
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
        const float sideSign = (decisionSeed & 1u) == 0u ? 1.0f : -1.0f;
        const float targetYaw = std::atan2(input.deltaTargetY, input.deltaTargetX);
        const float inwardWeight = 0.16f;
        const float sideYaw = targetYaw + sideSign * (Pi * 0.5f);
        const float moveX = std::cos(sideYaw) + std::cos(targetYaw) * inwardWeight;
        const float moveY = std::sin(sideYaw) + std::sin(targetYaw) * inwardWeight;
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
    update.movementIntent.moveSpeed = actor.movement.effectiveMoveSpeed;
    update.movementIntent.targetPosition = actor.target.currentPosition;
    update.movementIntent.targetEdgeDistance = actor.target.currentEdgeDistance;
    update.movementIntent.inMeleeRange = actor.movement.inMeleeRange;

    if (actor.stats.canFly)
    {
        const float verticalTargetDelta = actor.target.currentPosition.z - actor.world.targetZ;
        const float horizontalDistance =
            std::sqrt(
                (actor.target.currentPosition.x - actor.movement.position.x)
                    * (actor.target.currentPosition.x - actor.movement.position.x)
                + (actor.target.currentPosition.y - actor.movement.position.y)
                    * (actor.target.currentPosition.y - actor.movement.position.y));
        const float distance =
            std::sqrt(horizontalDistance * horizontalDistance + verticalTargetDelta * verticalTargetDelta);

        if (distance > 0.001f && std::abs(verticalTargetDelta) > 8.0f)
        {
            update.movementIntent.desiredMoveZ = std::clamp(verticalTargetDelta / distance, -1.0f, 1.0f);
        }
    }
}

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
        return true;
    }

    AI_ApplyCombatFlowOutcome(ai, flowOutcome);
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
        ai.setAnimationTimeTicks(actor.runtime.animationTimeTicks + pFrame->fixedStepSeconds * ActorAiTicksPerSecond);
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
    const bool hasTrigger =
        eligibility.contactedActorCount > 0
        || (eligibility.triggerOnMovementBlocked && eligibility.movementBlocked);

    return hasTrigger
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
    ai.setAnimationState(idleBehavior.bored ? ActorAiAnimationState::Bored : ActorAiAnimationState::Standing);
    ai.setAnimationTimeTicks(0.0f);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();
}

void AI_CrowdRetreat(ActorAiCommandContext &ai, const CrowdSteeringResult &crowdSteering)
{
    const ActorAiFacts &actor = ai.actor();
    const int sideSign = crowdSteering.sideSign > 0 ? 1 : -1;
    const float retreatAngle = actor.movement.crowdRetreatAngleRadians > 0.0f
        ? actor.movement.crowdRetreatAngleRadians
        : ActorCrowdRetreatAngleRadians;
    const float angleOffset = sideSign > 0 ? retreatAngle : -retreatAngle;
    const float yaw = normalizeAngleRadians(
        std::atan2(
            actor.target.currentPosition.y - actor.movement.position.y,
            actor.target.currentPosition.x - actor.movement.position.x)
        + angleOffset);
    const float moveDirectionX = std::cos(yaw);
    const float moveDirectionY = std::sin(yaw);

    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setActionSeconds(std::max(actor.runtime.actionSeconds, crowdSteering.retreatSeconds));
    ai.setAttackImpactTriggered(false);
    ai.setCrowdSideLockRemainingSeconds(crowdSteering.retreatSeconds);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.setMovementAction(ActorAiMovementAction::Pursue);
    ai.faceYaw(yaw);
    ai.setMoveDirection(moveDirectionX, moveDirectionY);
    ai.setDesiredMovement(moveDirectionX, moveDirectionY);
}

void AI_CrowdSidestep(ActorAiCommandContext &ai, const CrowdSteeringResult &crowdSteering)
{
    const ActorAiFacts &actor = ai.actor();
    const int sideSign = crowdSteering.sideSign > 0 ? 1 : -1;
    const float sidestepAngle = actor.movement.crowdSidestepAngleRadians > 0.0f
        ? actor.movement.crowdSidestepAngleRadians
        : ActorCrowdSidestepAngleRadians;
    const float angleOffset = sideSign > 0 ? sidestepAngle : -sidestepAngle;
    const float yaw = normalizeAngleRadians(
        std::atan2(
            actor.target.currentPosition.y - actor.movement.position.y,
            actor.target.currentPosition.x - actor.movement.position.x)
        + angleOffset);
    const float moveDirectionX = std::cos(yaw);
    const float moveDirectionY = std::sin(yaw);

    ai.setMotionState(ActorAiMotionState::Pursuing);
    ai.setActionSeconds(std::max(actor.runtime.actionSeconds, ActorCrowdSideLockSeconds));
    ai.setAttackImpactTriggered(false);
    ai.setCrowdSideLockRemainingSeconds(ActorCrowdSideLockSeconds);
    ai.setAnimationState(ActorAiAnimationState::Walking);
    ai.setMovementAction(ActorAiMovementAction::Pursue);
    ai.faceYaw(yaw);
    ai.setMoveDirection(moveDirectionX, moveDirectionY);
    ai.setDesiredMovement(moveDirectionX, moveDirectionY);
}

bool AI_CrowdSteer(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();

    if (!actor.movement.allowCrowdSteering)
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
    crowdSteering.triggerOnMovementBlocked = actor.movement.crowdSteeringTriggersOnMovementBlocked;
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

void applyAttackImpactOutcome(const ActorAiFacts &actor, ActorAiUpdate &update)
{
    if (!actor.world.active || actor.runtime.motionState != ActorAiMotionState::Attacking)
    {
        return;
    }

    const float actionSeconds = update.state.actionSeconds.value_or(actor.runtime.actionSeconds);
    const ActorAttackFrameState attackFrame =
        buildActorAttackFrameState(true, actor.runtime.attackImpactTriggered, actionSeconds);

    if (!attackFrame.attackJustCompleted)
    {
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
        actorService.effectiveAttackDamageBonus(actor.runtime.queuedAttackAbility, spellEffects));

    update.state.attackImpactTriggered = true;

    if (attackImpact.action == AttackImpactAction::None)
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
        ai.setMovementAction(ActorAiMovementAction::Pursue);
        ai.faceYaw(pursueAction.yawRadians);
        ai.setMoveDirection(pursueAction.moveDirectionX, pursueAction.moveDirectionY);
        ai.setDesiredMovement(pursueAction.moveDirectionX, pursueAction.moveDirectionY);
        ai.setActionSeconds(pursueAction.actionSeconds);
        ai.setAttackImpactTriggered(false);
        return;
    }

    const float verticalTargetDelta = actor.target.currentPosition.z - actor.world.targetZ;
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

void AI_StartAttack(ActorAiCommandContext &ai, const CombatAbilityChoiceResult &abilityChoice)
{
    const ActorAiFacts &actor = ai.actor();
    const float attackAnimationSeconds = attackAnimationSecondsForAbility(
        actor,
        abilityChoice.ability,
        actor.stats.attackConstraints);

    const AttackStartOutcome attackStart = startAttack(
        actor.actorId,
        abilityChoice.nextAttackDecisionCount,
        abilityChoice.abilityIsRanged,
        attackAnimationSeconds,
        actor.runtime.recoverySeconds);

    ai.setMotionState(ActorAiMotionState::Attacking);
    ai.setQueuedAttackAbility(abilityChoice.ability);
    ai.setAttackCooldownSeconds(attackStart.attackCooldownSeconds);
    ai.setActionSeconds(attackStart.actionSeconds);
    ai.setAttackImpactTriggered(false);
    ai.setAnimationState(attackAnimationStateForAbility(abilityChoice.ability, actor.stats.attackConstraints));
    ai.setAnimationTimeTicks(0.0f);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();

    ActorAudioRequest attackAudio = {};
    attackAudio.kind = ActorAiAudioRequestKind::Attack;
    attackAudio.actorIndex = actor.actorIndex;
    attackAudio.position = actor.movement.position;
    attackAudio.position.z += static_cast<float>(actor.stats.height) * 0.5f;
    ai.requestAudio(attackAudio);
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

bool AI_AttackOrPursue(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();
    const ActorAiFrameFacts *pFrame = ai.frame();

    if (pFrame == nullptr || !actor.world.active)
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
    abilityInput.inMeleeRange = engagement.inMeleeRange;
    abilityInput.chooseRandomAbility = true;
    abilityInput.applyAbilityConstraints = true;
    const CombatAbilityChoiceResult abilityChoice = chooseCombatAbility(abilityInput);

    CombatEngagePlanInput engageInput = {};
    engageInput.abilityIsRanged = abilityChoice.abilityIsRanged;
    engageInput.abilityIsMelee = abilityChoice.abilityIsMelee;
    engageInput.inMeleeRange = engagement.inMeleeRange;
    engageInput.attackCooldownReady = actor.runtime.attackCooldownSeconds <= 0.0f;
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

    if (engagePlan.action == CombatEngageAction::HoldCrowdStand)
    {
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
        ai.faceYaw(std::atan2(
            actor.target.currentPosition.y - actor.movement.position.y,
            actor.target.currentPosition.x - actor.movement.position.x));
        AI_Attack(ai, abilityChoice);
        return true;
    }

    if (engagePlan.action == CombatEngageAction::StandForRangedBlock
        || engagePlan.action == CombatEngageAction::StandForMeleeCooldown)
    {
        ai.setMotionState(ActorAiMotionState::Standing);
        ai.setAnimationState(ActorAiAnimationState::Standing);
        ai.setMovementAction(ActorAiMovementAction::Stand);
        ai.clearMovementDirection();
        ai.faceYaw(std::atan2(
            actor.target.currentPosition.y - actor.movement.position.y,
            actor.target.currentPosition.x - actor.movement.position.x));
        applyActiveMovementCommit(actor, engagePlan.preserveCrowdSteering, ai.update());
        return true;
    }

    if (engagePlan.action == CombatEngageAction::ContinueRangedPursuit
        || engagePlan.action == CombatEngageAction::ContinueMeleePursuit)
    {
        ai.setMotionState(ActorAiMotionState::Pursuing);
        ai.setAnimationState(ActorAiAnimationState::Walking);
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
    ai.setAnimationState(actor.runtime.queuedAttackAbility == GameplayActorAttackAbility::Attack1
        || actor.runtime.queuedAttackAbility == GameplayActorAttackAbility::Attack2
        ? ActorAiAnimationState::AttackMelee
        : ActorAiAnimationState::AttackRanged);
    ai.setMovementAction(ActorAiMovementAction::Stand);
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
    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Bored);
    ai.setMovementAction(ActorAiMovementAction::Stand);
    ai.clearMovementDirection();
    ai.clearVelocity();
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
        ai.setMotionState(ActorAiMotionState::Wandering);
        ai.setAnimationState(ActorAiAnimationState::Walking);
        ai.setMovementAction(ActorAiMovementAction::Wander);
        ai.setMoveDirection(idleBehavior.moveDirectionX, idleBehavior.moveDirectionY);
        ai.setDesiredMovement(idleBehavior.moveDirectionX, idleBehavior.moveDirectionY);
        return;
    }

    if (idleBehavior.bored)
    {
        AI_Bored(ai);
        return;
    }

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

void AI_StandOrBored(ActorAiCommandContext &ai)
{
    const ActorAiFacts &actor = ai.actor();

    if (actor.runtime.motionState == ActorAiMotionState::Wandering && actor.movement.movementAllowed)
    {
        ai.setMotionState(ActorAiMotionState::Wandering);
        ai.setAnimationState(ActorAiAnimationState::Walking);
        ai.setMovementAction(ActorAiMovementAction::Wander);
        ai.setMoveDirection(actor.movement.moveDirectionX, actor.movement.moveDirectionY);
        ai.update().movementIntent.applyMovement = true;
        return;
    }

    ai.setMotionState(ActorAiMotionState::Standing);
    ai.setAnimationState(ActorAiAnimationState::Standing);
    ai.setMovementAction(ActorAiMovementAction::Stand);
}

void AI_StandOrBored(ActorAiCommandContext &ai, float actionSeconds)
{
    const ActorAiFacts &actor = ai.actor();

    if (actor.status.hostileToParty || actor.movement.wanderRadius <= 0.0f)
    {
        if (actionSeconds <= 0.0f)
        {
            AI_RandomMove(ai, idleStandBehavior(false));
            ai.setMotionState(ActorAiMotionState::Standing);
        }
        else
        {
            AI_Stand(ai);
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
        AI_RandomMove(ai, idleStandBehavior(false));
        ai.setMotionState(ActorAiMotionState::Standing);
        return;
    }

    if (actionSeconds > 0.0f)
    {
        AI_Stand(ai);
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
        idleBehavior = idleStandBehavior(false);
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
    applyAttackImpactOutcome(actor, update);
    const bool attackImpactResolved =
        update.state.attackImpactTriggered.value_or(false) && !actor.runtime.attackImpactTriggered;
    applyCombatEngagementUpdate(actor, frame, update);
    ai.replaceUpdate(update);

    if (attackImpactResolved)
    {
        return ai.finish();
    }

    const bool attackInProgress = ai.update().state.actionSeconds.value_or(actor.runtime.actionSeconds) > 0.0f;

    if (AI_CombatFlow(ai, attackInProgress))
    {
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

    if (AI_ContinueFlee(ai))
    {
        return ai.finish();
    }

    if (AI_CombatFlow(ai, false))
    {
        return finishActiveMovementCommand(ai);
    }

    if (hasTarget && AI_AttackOrPursue(ai))
    {
        return ai.finish();
    }

    AI_StandOrBored(ai, ai.update().state.actionSeconds.value_or(actor.runtime.actionSeconds));
    return finishActiveMovementCommand(ai);
}

ActorAiUpdate updateBackgroundActor(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiCommandContext ai(actor, frame);
    const bool frameHandled = AI_DeathOrStatus(ai);

    if (frameHandled || ai.update().state.spellEffects)
    {
        return ai.finish();
    }

    ActorAiCommandContext standAi(actor);
    AI_StandOrBored(standAi);
    return standAi.finish();
}

ActorAiUpdate updateActor(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiFacts actorFacts = actor;
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
            projectileRequest.damage = update.attackRequest->damage;
            projectileRequest.attackBonus = update.attackRequest->attackBonus;
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

    updateBackgroundActors(facts, result);
    updateActiveActors(facts, result);

    return result;
}

ActorAiUpdate GameplayActorAiSystem::updateActorAfterWorldMovement(const ActorAiFacts &facts) const
{
    return updateActorAfterWorldMovementInternal(facts);
}
}
