#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
class MonsterTable;
class SpellTable;

class GameplayActorService
{
public:
    enum class SharedSpellDisposition : uint8_t
    {
        Unhandled = 0,
        Rejected = 1,
        Applied = 2,
    };

    enum class SharedSpellEffectKind : uint8_t
    {
        None = 0,
        Stun = 1,
        Slow = 2,
        Paralyze = 3,
        Fear = 4,
        Blind = 5,
        Control = 6,
        Shrink = 7,
        DarkGrasp = 8,
        DispelMagic = 9,
    };

    struct SharedSpellEffectResult
    {
        SharedSpellDisposition disposition = SharedSpellDisposition::Unhandled;
        SharedSpellEffectKind effectKind = SharedSpellEffectKind::None;
    };

    enum class DirectSpellImpactDisposition : uint8_t
    {
        Unhandled = 0,
        Rejected = 1,
        ApplyDamage = 2,
    };

    enum class DirectSpellImpactVisualKind : uint8_t
    {
        None = 0,
        ActorCenter = 1,
        ActorUpperBody = 2,
    };

    struct DirectSpellImpactResult
    {
        DirectSpellImpactDisposition disposition = DirectSpellImpactDisposition::Unhandled;
        DirectSpellImpactVisualKind visualKind = DirectSpellImpactVisualKind::None;
        int damage = 0;
        bool centerVisual = false;
        bool preferImpactObject = true;
    };

    struct FriendlyTargetEngagementResult
    {
        bool shouldEngageTarget = true;
        bool shouldPromoteHostility = false;
        float promotionRange = -1.0f;
    };

    enum class CrowdSteeringAction : uint8_t
    {
        SideStep = 0,
        Retreat = 1,
        Stand = 2,
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

    struct CrowdSteeringEligibilityInput
    {
        size_t contactedActorCount = 0;
        bool meleePursuitActive = false;
        bool pursuing = false;
        bool actorCanFly = false;
        bool inMeleeRange = false;
        float targetEdgeDistance = 0.0f;
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

    struct InactiveFidgetResult
    {
        bool shouldFidget = false;
        uint32_t nextDecisionCount = 0;
    };

    struct InactiveActorBehaviorInput
    {
        uint32_t actorId = 0;
        uint32_t idleDecisionCount = 0;
        bool currentAnimationBored = false;
        bool allowFidget = true;
        float actionSeconds = 0.0f;
        float idleDecisionSeconds = 0.0f;
        float deltaSeconds = 0.0f;
        float decisionIntervalSeconds = 0.0f;
    };

    struct InactiveActorBehaviorResult
    {
        bool keepCurrentAnimation = false;
        bool shouldSetStandingAnimation = false;
        bool shouldApplyIdleBehavior = false;
        IdleBehaviorResult idleBehavior = {};
        float actionSeconds = 0.0f;
        float idleDecisionSeconds = 0.0f;
        uint32_t nextIdleDecisionCount = 0;
    };

    enum class NonCombatBehaviorAction : uint8_t
    {
        Stand = 0,
        ApplyIdleBehavior = 1,
        ReturnHome = 2,
        ContinueMove = 3,
        StartIdleBehavior = 4,
    };

    struct NonCombatBehaviorInput
    {
        uint32_t actorId = 0;
        uint32_t idleDecisionCount = 0;
        bool hostileToParty = false;
        bool currentlyWandering = false;
        bool currentlyWalking = false;
        bool allowIdleWander = true;
        float actionSeconds = 0.0f;
        float moveDirectionX = 0.0f;
        float moveDirectionY = 0.0f;
        float preciseX = 0.0f;
        float preciseY = 0.0f;
        float homePreciseX = 0.0f;
        float homePreciseY = 0.0f;
        float currentYawRadians = 0.0f;
        float wanderRadius = 0.0f;
        float moveSpeed = 0.0f;
    };

    struct NonCombatBehaviorResult
    {
        NonCombatBehaviorAction action = NonCombatBehaviorAction::Stand;
        IdleBehaviorResult idleBehavior = {};
        float moveDirectionX = 0.0f;
        float moveDirectionY = 0.0f;
        bool updateYaw = false;
        float yawRadians = 0.0f;
    };

    struct ActorInitialTimingInput
    {
        uint32_t actorId = 0;
        float recoverySeconds = 0.0f;
    };

    struct ActorInitialTimingResult
    {
        float attackCooldownSeconds = 0.0f;
        float idleDecisionSeconds = 0.0f;
    };

    struct ActorCombatAvailabilityInput
    {
        bool invisible = false;
        bool dead = false;
        bool hpDepleted = false;
        bool dyingState = false;
        bool deadState = false;
    };

    struct ActorHitReactionInput
    {
        ActorCombatAvailabilityInput availability = {};
        bool stunnedState = false;
        bool attackingState = false;
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

    struct AttackStartInput
    {
        uint32_t actorId = 0;
        uint32_t attackDecisionCount = 0;
        bool abilityIsRanged = false;
        float attackAnimationSeconds = 0.0f;
        float recoverySeconds = 0.0f;
    };

    struct AttackStartResult
    {
        float attackCooldownSeconds = 0.0f;
        float actionSeconds = 0.0f;
    };

    struct AttackDamageProfile
    {
        int diceRolls = 0;
        int diceSides = 0;
        int bonus = 0;
    };

    enum class AttackImpactAction : uint8_t
    {
        None = 0,
        RangedRelease = 1,
        PartyMeleeImpact = 2,
        ActorMeleeImpact = 3,
    };

    struct AttackImpactInput
    {
        GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
        int monsterLevel = 0;
        AttackDamageProfile attack1Damage;
        AttackDamageProfile attack2Damage;
        bool abilityIsRanged = false;
        bool abilityIsMelee = false;
        bool hasCombatTarget = false;
        bool targetIsParty = false;
        bool targetIsActor = false;
        bool shrinkActive = false;
        float shrinkDamageMultiplier = 1.0f;
        bool darkGraspActive = false;
    };

    struct AttackImpactResult
    {
        AttackImpactAction action = AttackImpactAction::None;
        int damage = 0;
        bool shouldSpawnProjectile = false;
    };

    enum class CombatTargetKind : uint8_t
    {
        None = 0,
        Party = 1,
        Actor = 2,
    };

    struct CombatTargetCandidate
    {
        size_t actorIndex = static_cast<size_t>(-1);
        GameplayActorTargetPolicyState policyState = {};
        float preciseX = 0.0f;
        float preciseY = 0.0f;
        float targetZ = 0.0f;
        uint16_t radius = 0;
        bool unavailable = false;
        bool hasLineOfSight = false;
    };

    struct CombatTargetInput
    {
        size_t actorIndex = static_cast<size_t>(-1);
        GameplayActorTargetPolicyState actorPolicyState = {};
        float actorX = 0.0f;
        float actorY = 0.0f;
        float actorTargetZ = 0.0f;
        uint16_t actorRadius = 0;
        float partyX = 0.0f;
        float partyY = 0.0f;
        float partyTargetZ = 0.0f;
        float partyCollisionRadius = 0.0f;
        const std::vector<CombatTargetCandidate> *pActorCandidates = nullptr;
    };

    struct CombatTargetResult
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
        bool partyCanSense = false;
    };

    struct ActorPartyProximityInput
    {
        float horizontalDistanceToParty = 0.0f;
        float verticalDistanceToParty = 0.0f;
        float actorRadius = 0.0f;
        float actorHeight = 0.0f;
        float partyCollisionRadius = 0.0f;
    };

    struct ActorPartyProximityResult
    {
        bool veryNearParty = false;
    };

    struct CombatEngagementInput
    {
        GameplayActorTargetPolicyState actorPolicyState = {};
        CombatTargetResult combatTarget = {};
        GameplayActorAiType aiType = GameplayActorAiType::Normal;
        uint8_t hostilityType = 0;
        int currentHp = 0;
        int maxHp = 0;
        bool hostileToParty = false;
        bool hasDetectedParty = false;
        bool partyIsVeryNearActor = false;
    };

    struct CombatEngagementResult
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

    enum class PursueActionMode : uint8_t
    {
        OffsetShort = 0,
        Direct = 1,
        OffsetWide = 2,
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

    enum class CombatFlowAction : uint8_t
    {
        ContinueAttack = 0,
        BlindWander = 1,
        Flee = 2,
        EngageTarget = 3,
        FriendlyNearParty = 4,
        NonCombat = 5,
    };

    struct CombatFlowDecisionInput
    {
        bool attackInProgress = false;
        bool blindActive = false;
        bool shouldFlee = false;
        bool fearActive = false;
        bool shouldEngageTarget = false;
        bool friendlyNearParty = false;
    };

    struct CombatFlowDecisionResult
    {
        CombatFlowAction action = CombatFlowAction::NonCombat;
    };

    enum class CombatFlowApplicationState : uint8_t
    {
        Standing = 0,
        Attacking = 1,
        Wandering = 2,
        Fleeing = 3,
    };

    enum class CombatFlowApplicationAnimation : uint8_t
    {
        Standing = 0,
        Walking = 1,
        Current = 2,
    };

    struct CombatFlowApplicationInput
    {
        CombatFlowAction action = CombatFlowAction::NonCombat;
        bool movementAllowed = false;
        float currentYawRadians = 0.0f;
        float currentMoveDirectionX = 0.0f;
        float currentMoveDirectionY = 0.0f;
        float targetDeltaX = 0.0f;
        float targetDeltaY = 0.0f;
        float targetHorizontalDistance = 0.0f;
        float actionSeconds = 0.0f;
        float idleDecisionSeconds = 0.0f;
    };

    struct CombatFlowApplicationResult
    {
        CombatFlowApplicationState state = CombatFlowApplicationState::Standing;
        CombatFlowApplicationAnimation animation = CombatFlowApplicationAnimation::Standing;
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

    struct ActiveActorUpdateCandidate
    {
        size_t actorIndex = static_cast<size_t>(-1);
        float distanceToParty = 0.0f;
        bool eligible = false;
    };

    struct ActiveActorUpdateSelectionInput
    {
        const std::vector<ActiveActorUpdateCandidate> *pCandidates = nullptr;
        size_t actorCount = 0;
        size_t maxActiveActors = 0;
        float activeRange = 0.0f;
    };

    struct ActiveActorUpdateSelectionResult
    {
        std::vector<bool> activeActorMask;
    };

    enum class ActorFrameRouteAction : uint8_t
    {
        Active = 0,
        Inactive = 1,
        MissingStats = 2,
    };

    struct ActorFrameRouteInput
    {
        bool hasMonsterStats = false;
        bool selectedForActiveUpdate = false;
    };

    struct ActorFrameRouteResult
    {
        ActorFrameRouteAction action = ActorFrameRouteAction::Inactive;
    };

    struct ActorFrameTimerInput
    {
        bool attacking = false;
        float idleDecisionSeconds = 0.0f;
        float attackCooldownSeconds = 0.0f;
        float actionSeconds = 0.0f;
        float crowdSideLockRemainingSeconds = 0.0f;
        float crowdRetreatRemainingSeconds = 0.0f;
        float crowdStandRemainingSeconds = 0.0f;
        float slowRecoveryMultiplier = 1.0f;
        float deltaSeconds = 0.0f;
    };

    struct ActorFrameTimerResult
    {
        float idleDecisionSeconds = 0.0f;
        float attackCooldownSeconds = 0.0f;
        float actionSeconds = 0.0f;
        float crowdSideLockRemainingSeconds = 0.0f;
        float crowdRetreatRemainingSeconds = 0.0f;
        float crowdStandRemainingSeconds = 0.0f;
    };

    struct ActorAnimationTickInput
    {
        bool walking = false;
        bool slowActive = false;
        float slowMoveMultiplier = 1.0f;
        float baseTickDelta = 0.0f;
    };

    struct ActorAnimationTickResult
    {
        float tickDelta = 0.0f;
    };

    struct ActorMovementBlockInput
    {
        bool movementBlocked = false;
        bool pursuing = false;
        float actionSeconds = 0.0f;
    };

    struct ActorMovementBlockResult
    {
        bool zeroVelocity = false;
        bool resetMoveDirection = false;
        bool stand = false;
        float actionSeconds = 0.0f;
    };

    struct ActorFrameCommitInput
    {
        bool attackInProgress = false;
        bool proposedAnimationChanged = false;
        bool preserveCrowdSteering = false;
        bool movementAllowed = false;
        float desiredMoveX = 0.0f;
        float desiredMoveY = 0.0f;
    };

    struct ActorFrameCommitResult
    {
        bool keepCurrentAnimation = false;
        bool resetAnimationTime = false;
        bool resetCrowdSteering = false;
        bool clearVelocity = true;
        bool applyMovement = false;
    };

    struct ActorAttackFrameInput
    {
        bool attacking = false;
        bool impactTriggered = false;
        float actionSeconds = 0.0f;
    };

    struct ActorAttackFrameResult
    {
        bool attackInProgress = false;
        bool attackJustCompleted = false;
    };

    struct ActorMoveSpeedInput
    {
        int configuredMoveSpeed = 0;
        int defaultMoveSpeed = 0;
        float slowMoveMultiplier = 1.0f;
        bool darkGraspActive = false;
    };

    struct ActorMoveSpeedResult
    {
        float moveSpeed = 0.0f;
    };

    enum class ActorStatusFrameAction : uint8_t
    {
        Continue = 0,
        HoldStun = 1,
        RecoverFromStun = 2,
        HoldParalyze = 3,
        ForceStun = 4,
    };

    struct ActorStatusFrameInput
    {
        bool currentlyStunned = false;
        bool paralyzeActive = false;
        bool stunActive = false;
        float actionSeconds = 0.0f;
        float stunRemainingSeconds = 0.0f;
        float deltaSeconds = 0.0f;
    };

    struct ActorStatusFrameResult
    {
        ActorStatusFrameAction action = ActorStatusFrameAction::Continue;
        float actionSeconds = 0.0f;
    };

    enum class ActorDeathFrameAction : uint8_t
    {
        Continue = 0,
        HoldDead = 1,
        MarkDead = 2,
        AdvanceDying = 3,
    };

    struct ActorDeathFrameInput
    {
        bool dead = false;
        bool hpDepleted = false;
        bool dying = false;
        float actionSeconds = 0.0f;
        float deltaSeconds = 0.0f;
    };

    struct ActorDeathFrameResult
    {
        ActorDeathFrameAction action = ActorDeathFrameAction::Continue;
        float actionSeconds = 0.0f;
        bool finishedDying = false;
    };

    void bindTables(const MonsterTable *pMonsterTable, const SpellTable *pSpellTable);
    bool isBound() const;
    bool actorLooksUndead(int16_t monsterId) const;

    DirectSpellImpactResult resolveDirectSpellImpact(
        uint32_t spellId,
        uint32_t skillLevel,
        int baseDamage,
        int actorCurrentHp,
        bool actorLooksUndead) const;

    SharedSpellEffectResult tryApplySharedSpellEffect(
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        bool actorLooksUndead,
        bool defaultHostileToParty,
        GameplayActorSpellEffectState &state) const;

    void updateSpellEffectTimers(
        GameplayActorSpellEffectState &state,
        float deltaSeconds,
        bool defaultHostileToParty) const;

    bool isPartyControlledActor(GameplayActorControlMode controlMode) const;
    bool monsterIdsAreFriendly(int16_t leftMonsterId, int16_t rightMonsterId) const;
    bool monsterIdsAreHostile(int16_t leftMonsterId, int16_t rightMonsterId) const;
    float partyEngagementRange(const GameplayActorTargetPolicyState &actor) const;
    float hostilityPromotionRangeForFriendlyActor(int relation) const;
    FriendlyTargetEngagementResult resolveFriendlyTargetEngagement(
        const GameplayActorTargetPolicyState &actor,
        uint8_t hostilityType,
        int relationToTarget,
        float targetDistanceSquared) const;
    bool shouldFleeForAiType(GameplayActorAiType aiType, int currentHp, int maxHp) const;
    GameplayActorAttackChoiceResult chooseAttackAbility(
        uint32_t actorId,
        uint32_t attackDecisionCount,
        bool hasSpell1,
        int spell1UseChance,
        bool hasSpell2,
        int spell2UseChance,
        int attack2Chance) const;
    ActorInitialTimingResult resolveActorInitialTiming(const ActorInitialTimingInput &input) const;
    bool isActorUnavailableForCombat(const ActorCombatAvailabilityInput &input) const;
    bool canActorEnterHitReaction(const ActorHitReactionInput &input) const;
    GameplayActorAttackAbility resolveAttackAbilityConstraints(
        GameplayActorAttackAbility chosenAbility,
        const GameplayActorAttackConstraintState &state) const;
    bool shouldCommitToRangedAbility(const RangedAbilityCommitInput &input) const;
    AttackStartResult resolveAttackStart(const AttackStartInput &input) const;
    AttackImpactResult resolveAttackImpact(const AttackImpactInput &input) const;
    CombatTargetResult resolveCombatTarget(const CombatTargetInput &input) const;
    ActorPartyProximityResult resolveActorPartyProximity(const ActorPartyProximityInput &input) const;
    CombatEngagementResult resolveCombatEngagement(const CombatEngagementInput &input) const;
    CombatAbilityDecisionResult resolveCombatAbilityDecision(const CombatAbilityDecisionInput &input) const;
    CombatEngageDecisionResult resolveCombatEngageDecision(const CombatEngageDecisionInput &input) const;
    CombatEngageApplicationResult resolveCombatEngageApplication(
        const CombatEngageApplicationInput &input) const;
    CombatFlowDecisionResult resolveCombatFlowDecision(const CombatFlowDecisionInput &input) const;
    CombatFlowApplicationResult resolveCombatFlowApplication(const CombatFlowApplicationInput &input) const;
    ActiveActorUpdateSelectionResult selectActiveActorUpdates(const ActiveActorUpdateSelectionInput &input) const;
    ActorFrameRouteResult resolveActorFrameRoute(const ActorFrameRouteInput &input) const;
    ActorFrameTimerResult advanceActorFrameTimers(const ActorFrameTimerInput &input) const;
    ActorAnimationTickResult advanceActorAnimationTick(const ActorAnimationTickInput &input) const;
    ActorMoveSpeedResult resolveActorMoveSpeed(const ActorMoveSpeedInput &input) const;
    ActorMovementBlockResult resolveActorMovementBlock(const ActorMovementBlockInput &input) const;
    ActorFrameCommitResult resolveActorFrameCommit(const ActorFrameCommitInput &input) const;
    ActorAttackFrameResult resolveActorAttackFrame(const ActorAttackFrameInput &input) const;
    ActorStatusFrameResult resolveActorStatusFrame(const ActorStatusFrameInput &input) const;
    ActorDeathFrameResult resolveActorDeathFrame(const ActorDeathFrameInput &input) const;
    PursueActionResult resolvePursueAction(const PursueActionInput &input) const;
    CrowdSteeringResult resolveCrowdSteering(
        uint32_t actorId,
        uint32_t pursueDecisionCount,
        float targetEdgeDistance,
        float deltaSeconds,
        const CrowdSteeringState &state) const;
    bool shouldApplyCrowdSteering(const CrowdSteeringEligibilityInput &input) const;
    IdleBehaviorResult idleStandBehavior(bool bored) const;
    InactiveFidgetResult resolveInactiveFidget(uint32_t actorId, uint32_t idleDecisionCount) const;
    InactiveActorBehaviorResult resolveInactiveActorBehavior(const InactiveActorBehaviorInput &input) const;
    NonCombatBehaviorResult resolveNonCombatBehavior(const NonCombatBehaviorInput &input) const;
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
        float moveSpeed) const;
    GameplayActorTargetPolicyResult resolveActorTargetPolicy(
        const GameplayActorTargetPolicyState &actor,
        const GameplayActorTargetPolicyState &target) const;

    bool clearSpellEffects(
        GameplayActorSpellEffectState &state,
        bool defaultHostileToParty) const;

    int effectiveArmorClass(int baseArmorClass, const GameplayActorSpellEffectState &state) const;

private:
    const MonsterTable *m_pMonsterTable = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
};
}
