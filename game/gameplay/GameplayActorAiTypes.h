#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class ActorAiTargetKind : uint8_t
{
    None = 0,
    Party = 1,
    Actor = 2,
};

enum class ActorAiMotionState : uint8_t
{
    Standing = 0,
    Wandering = 1,
    Pursuing = 2,
    Fleeing = 3,
    Stunned = 4,
    Attacking = 5,
    Dying = 6,
    Dead = 7,
};

enum class ActorAiAnimationState : uint8_t
{
    Standing = 0,
    Walking = 1,
    AttackMelee = 2,
    AttackRanged = 3,
    GotHit = 4,
    Dying = 5,
    Dead = 6,
    Bored = 7,
};

enum class ActorAiMovementAction : uint8_t
{
    None = 0,
    Stand = 1,
    Move = 2,
    Pursue = 3,
    Flee = 4,
    Wander = 5,
};

enum class ActorAiAttackRequestKind : uint8_t
{
    None = 0,
    PartyMelee = 1,
    ActorMelee = 2,
    RangedProjectile = 3,
    SpellProjectile = 4,
};

enum class ActorAiAudioRequestKind : uint8_t
{
    None = 0,
    Alert = 1,
    Attack = 2,
    Hit = 3,
    Death = 4,
};

enum class ActorAiFxRequestKind : uint8_t
{
    None = 0,
    Hit = 1,
    Death = 2,
    Spell = 3,
};

struct ActorPartyFacts
{
    GameplayWorldPoint position = {};
    float collisionRadius = 0.0f;
    float collisionHeight = 0.0f;
    bool invisible = false;
};

struct ActorIdentityFacts
{
    uint32_t actorId = 0;
    int16_t monsterId = 0;
    std::string displayName;
    uint32_t group = 0;
    uint32_t ally = 0;
    uint8_t hostilityType = 0;
    GameplayActorTargetPolicyState targetPolicy = {};
};

struct ActorStatsFacts
{
    struct AttackDamageFacts
    {
        int diceRolls = 0;
        int diceSides = 0;
        int bonus = 0;
    };

    GameplayActorAiType aiType = GameplayActorAiType::Normal;
    int monsterLevel = 0;
    int currentHp = 0;
    int maxHp = 0;
    int armorClass = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint16_t moveSpeed = 0;
    bool canFly = false;
    bool hasSpell1 = false;
    bool hasSpell2 = false;
    int spell1UseChance = 0;
    int spell2UseChance = 0;
    int attack2Chance = 0;
    AttackDamageFacts attack1Damage = {};
    AttackDamageFacts attack2Damage = {};
    GameplayActorAttackConstraintState attackConstraints = {};
};

struct ActorRuntimeFacts
{
    ActorAiMotionState motionState = ActorAiMotionState::Standing;
    ActorAiAnimationState animationState = ActorAiAnimationState::Standing;
    GameplayActorAttackAbility queuedAttackAbility = GameplayActorAttackAbility::Attack1;
    float animationTimeTicks = 0.0f;
    float recoverySeconds = 0.0f;
    float attackAnimationSeconds = 0.0f;
    float meleeAttackAnimationSeconds = 0.0f;
    float rangedAttackAnimationSeconds = 0.0f;
    float attackCooldownSeconds = 0.0f;
    float idleDecisionSeconds = 0.0f;
    float actionSeconds = 0.0f;
    float crowdSideLockRemainingSeconds = 0.0f;
    float crowdNoProgressSeconds = 0.0f;
    float crowdLastEdgeDistance = 0.0f;
    float crowdRetreatRemainingSeconds = 0.0f;
    float crowdStandRemainingSeconds = 0.0f;
    float crowdProbeEdgeDistance = 0.0f;
    float crowdProbeElapsedSeconds = 0.0f;
    float yawRadians = 0.0f;
    uint32_t idleDecisionCount = 0;
    uint32_t pursueDecisionCount = 0;
    uint32_t attackDecisionCount = 0;
    uint8_t crowdEscapeAttempts = 0;
    int8_t crowdSideSign = 0;
    bool attackImpactTriggered = false;
};

struct ActorStatusFacts
{
    GameplayActorSpellEffectState spellEffects = {};
    bool invisible = false;
    bool dead = false;
    bool hostileToParty = false;
    bool bloodSplatSpawned = false;
    bool hasDetectedParty = false;
    bool defaultHostileToParty = false;
};

struct ActorTargetCandidateFacts
{
    ActorAiTargetKind kind = ActorAiTargetKind::None;
    size_t actorIndex = static_cast<size_t>(-1);
    uint32_t actorId = 0;
    int16_t monsterId = 0;
    int currentHp = 0;
    GameplayActorTargetPolicyState policy = {};
    GameplayWorldPoint position = {};
    GameplayWorldPoint audioPosition = {};
    uint16_t radius = 0;
    uint16_t height = 0;
    bool unavailable = false;
    bool hasLineOfSight = false;
};

struct ActorTargetFacts
{
    ActorAiTargetKind currentKind = ActorAiTargetKind::None;
    size_t currentActorIndex = static_cast<size_t>(-1);
    int currentRelationToTarget = 0;
    int currentHp = 0;
    GameplayWorldPoint currentPosition = {};
    GameplayWorldPoint currentAudioPosition = {};
    float currentDistance = 0.0f;
    float currentEdgeDistance = 0.0f;
    bool currentCanSense = false;
    bool partyCanSenseActor = false;
    std::vector<ActorTargetCandidateFacts> candidates;
};

struct ActorMovementFacts
{
    GameplayWorldPoint position = {};
    GameplayWorldPoint homePosition = {};
    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float velocityZ = 0.0f;
    float wanderRadius = 0.0f;
    float effectiveMoveSpeed = 0.0f;
    float distanceToParty = 0.0f;
    float edgeDistanceToParty = 0.0f;
    size_t contactedActorCount = 0;
    bool meleePursuitActive = false;
    bool inMeleeRange = false;
    bool allowCrowdSteering = false;
    bool allowIdleWander = false;
    bool movementAllowed = false;
    bool movementBlocked = false;
};

struct ActorWorldFacts
{
    float targetZ = 0.0f;
    float floorZ = 0.0f;
    int sectorId = 0;
    bool active = false;
    bool activeByDistance = false;
    bool sameSectorAsParty = false;
    bool portalPathToParty = false;
};

struct ActorAiFacts
{
    size_t actorIndex = static_cast<size_t>(-1);
    uint32_t actorId = 0;

    ActorIdentityFacts identity = {};
    ActorStatsFacts stats = {};
    ActorRuntimeFacts runtime = {};
    ActorStatusFacts status = {};
    ActorTargetFacts target = {};
    ActorMovementFacts movement = {};
    ActorWorldFacts world = {};
};

struct ActorStateUpdate
{
    std::optional<ActorAiMotionState> motionState;
    std::optional<uint8_t> hostilityType;
    std::optional<bool> hostileToParty;
    std::optional<bool> hasDetectedParty;
    std::optional<bool> dead;
    std::optional<bool> bloodSplatSpawned;
    std::optional<float> recoverySeconds;
    std::optional<float> attackCooldownSeconds;
    std::optional<float> idleDecisionSeconds;
    std::optional<float> actionSeconds;
    std::optional<float> crowdSideLockRemainingSeconds;
    std::optional<float> crowdNoProgressSeconds;
    std::optional<float> crowdLastEdgeDistance;
    std::optional<float> crowdRetreatRemainingSeconds;
    std::optional<float> crowdStandRemainingSeconds;
    std::optional<float> crowdProbeEdgeDistance;
    std::optional<float> crowdProbeElapsedSeconds;
    std::optional<uint32_t> idleDecisionCount;
    std::optional<uint32_t> pursueDecisionCount;
    std::optional<uint32_t> attackDecisionCount;
    std::optional<uint8_t> crowdEscapeAttempts;
    std::optional<int8_t> crowdSideSign;
    std::optional<bool> attackImpactTriggered;
    std::optional<GameplayActorAttackAbility> queuedAttackAbility;
    std::optional<GameplayActorSpellEffectState> spellEffects;
};

struct ActorAnimationUpdate
{
    std::optional<ActorAiAnimationState> animationState;
    std::optional<float> animationTimeTicks;
    bool resetAnimationTime = false;
    bool resetOnAnimationChange = false;
};

struct ActorMovementIntent
{
    ActorAiMovementAction action = ActorAiMovementAction::None;
    GameplayWorldPoint targetPosition = {};
    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    float desiredMoveX = 0.0f;
    float desiredMoveY = 0.0f;
    float yawRadians = 0.0f;
    float actionSeconds = 0.0f;
    float moveSpeed = 0.0f;
    float targetEdgeDistance = 0.0f;
    bool updateYaw = false;
    bool clearVelocity = false;
    bool applyMovement = false;
    bool meleePursuitActive = false;
    bool inMeleeRange = false;
    bool resetCrowdSteering = false;
    bool updateCrowdProbePosition = false;
};

struct ActorAttackRequest
{
    ActorAiAttackRequestKind kind = ActorAiAttackRequestKind::None;
    GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
    ActorAiTargetKind targetKind = ActorAiTargetKind::None;
    size_t targetActorIndex = static_cast<size_t>(-1);
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    int damage = 0;
    GameplayWorldPoint source = {};
    GameplayWorldPoint target = {};
};

struct ActorProjectileRequest
{
    size_t sourceActorIndex = static_cast<size_t>(-1);
    GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
    ActorAiTargetKind targetKind = ActorAiTargetKind::None;
    uint32_t objectId = 0;
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    int damage = 0;
    GameplayWorldPoint source = {};
    GameplayWorldPoint target = {};
};

struct ActorAudioRequest
{
    ActorAiAudioRequestKind kind = ActorAiAudioRequestKind::None;
    size_t actorIndex = static_cast<size_t>(-1);
    GameplayWorldPoint position = {};
};

struct ActorFxRequest
{
    ActorAiFxRequestKind kind = ActorAiFxRequestKind::None;
    size_t actorIndex = static_cast<size_t>(-1);
    uint32_t spellId = 0;
    GameplayWorldPoint position = {};
};

struct ActorAiUpdate
{
    size_t actorIndex = static_cast<size_t>(-1);

    ActorStateUpdate state = {};
    ActorAnimationUpdate animation = {};
    ActorMovementIntent movementIntent = {};

    std::optional<ActorAttackRequest> attackRequest;
    std::vector<ActorAudioRequest> audioRequests;
    std::vector<ActorFxRequest> fxRequests;
};

struct ActorAiFrameFacts
{
    float deltaSeconds = 0.0f;
    float fixedStepSeconds = 0.0f;
    ActorPartyFacts party = {};
    std::vector<ActorAiFacts> backgroundActors;
    std::vector<ActorAiFacts> activeActors;
};

struct ActorAiFrameResult
{
    std::vector<ActorAiUpdate> actorUpdates;
    std::vector<ActorProjectileRequest> projectileRequests;
    std::vector<ActorAudioRequest> audioRequests;
    std::vector<ActorFxRequest> fxRequests;
};
}
