#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/SkillData.h"

#include <cstdint>

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

    void bindTables(const MonsterTable *pMonsterTable, const SpellTable *pSpellTable);
    bool isBound() const;
    bool actorLooksUndead(int16_t monsterId) const;

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
    GameplayActorAttackAbility resolveAttackAbilityConstraints(
        GameplayActorAttackAbility chosenAbility,
        const GameplayActorAttackConstraintState &state) const;
    CrowdSteeringResult resolveCrowdSteering(
        uint32_t actorId,
        uint32_t pursueDecisionCount,
        float targetEdgeDistance,
        float deltaSeconds,
        const CrowdSteeringState &state) const;
    IdleBehaviorResult idleStandBehavior(bool bored) const;
    InactiveFidgetResult resolveInactiveFidget(uint32_t actorId, uint32_t idleDecisionCount) const;
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
