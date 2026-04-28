#pragma once

#include "game/gameplay/GameplayActorAiTypes.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/SkillData.h"

#include <cstddef>
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

    void bindTables(const MonsterTable *pMonsterTable, const SpellTable *pSpellTable);
    bool isBound() const;
    bool actorLooksUndead(int16_t monsterId) const;
    int16_t relationMonsterId(int16_t monsterId, uint32_t allyMonsterType) const;

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
    bool shouldFleeForAiType(GameplayActorAiType aiType, int currentHp, int maxHp) const;
    float initialAttackCooldownSeconds(uint32_t actorId, float recoverySeconds) const;
    float initialIdleDecisionSeconds(uint32_t actorId) const;
    bool isActorUnavailableForCombat(
        bool invisible,
        bool dead,
        bool hpDepleted,
        bool dyingState,
        bool deadState) const;
    bool canActorEnterHitReaction(
        bool invisible,
        bool dead,
        bool hpDepleted,
        bool dyingState,
        bool deadState,
        bool stunnedState,
        bool attackingState) const;
    bool partyIsVeryNearActor(
        float horizontalDistanceToParty,
        float verticalDistanceToParty,
        float actorRadius,
        float actorHeight,
        float partyCollisionRadius) const;
    float effectiveActorMoveSpeed(
        int configuredMoveSpeed,
        int defaultMoveSpeed,
        float slowMoveMultiplier,
        bool darkGraspActive) const;
    float effectiveRecoveryProgressMultiplier(const GameplayActorSpellEffectState &state) const;
    int effectiveAttackDamageBonus(
        GameplayActorAttackAbility ability,
        const GameplayActorSpellEffectState &state) const;
    int effectiveAttackHitBonus(const GameplayActorSpellEffectState &state) const;
    bool halveIncomingMissileDamage(const GameplayActorSpellEffectState &state) const;
    bool hasPainReflection(const GameplayActorSpellEffectState &state) const;
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
