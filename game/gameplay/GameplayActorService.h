#pragma once

#include "game/gameplay/GameplayActorAiTypes.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/Mm9ActorRules.h"
#include "game/party/SkillData.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
class MonsterTable;
class SpellTable;

class GameplayActorService
{
public:
    static constexpr float MaximumPartyEngagementRange = 10240.0f;

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
    void setPartyEngagementRange(float range);
    float configuredPartyEngagementRange() const;
    // A world's shorter limit on the party's shots and targeted spells: its declared engagement range (world.yml
    // actorAwareness partyEngagementRange, MM9's 3800), where its HUD turns yellow and its hits provoke. None for a
    // world that declares no range (MM6-MM8).
    void setWorldPartyHitReach(std::optional<float> reach);
    // How far from the party its shots and targeted spells reach a monster, in every ruleset: the yellow alert range,
    // 5120, as far as monsters shoot and cast at the party and as turn-based combat keeps shots; a world's shorter
    // range (MM9's 3800) in its place. A shot vanishes beyond it and a targeted spell refuses a farther monster.
    float partyHitReach() const;
    // How MM9 loop monsters perceive the party (world.yml actorAwareness mm9Sight, mm9Provoke).
    void setMm9PartyAwareness(const Mm9PartyAwareness &awareness);
    const Mm9PartyAwareness &mm9PartyAwareness() const;
    // The world's melee vertical reach (WorldActorCombatDefinition; 0: melee ignores height).
    void setMeleeVerticalReach(float share);
    float meleeVerticalReach() const
    {
        return m_meleeVerticalReach;
    }
    // True when a melee blow between bodies standing at these feet heights reaches across their height difference:
    // always with no vertical reach (share 0), else when the difference is at most the reach share of the lower
    // body's height (at least MinimumMeleeVerticalReach, so a step never stops a blow).
    static bool meleeReachesVertically(float share, float attackerFootZ, float attackerHeight, float targetFootZ,
        float targetHeight);
    bool meleeReachesVertically(float attackerFootZ, float attackerHeight, float targetFootZ,
        float targetHeight) const
    {
        return meleeReachesVertically(m_meleeVerticalReach, attackerFootZ, attackerHeight, targetFootZ, targetHeight);
    }
    static constexpr float MinimumMeleeVerticalReach = 48.0f;
    // world.yml friendlyActorsBlockParty: true (MM9) makes friendly actors solid to the party's movement as hostile ones
    // are; false (MM6-MM8) lets the party walk through them. Callers have already left out dead, dying and hidden actors.
    void setFriendlyActorsBlockParty(bool enabled);
    // The party's own charmed, enslaved or raised monsters stay passable in every world: they follow it about.
    bool actorBlocksPartyMovement(bool hostileToParty, GameplayActorControlMode controlMode) const;
    // The world's level radius limit (WorldActorMovementDefinition; 0: none).
    void setLevelRadiusLimit(float limit);
    // The radius a monster's body meets the level with and plans its routes for: its own, at most the world's limit.
    float levelCollisionRadius(float radius) const
    {
        return m_levelRadiusLimit > 0.0f ? std::min(radius, m_levelRadiusLimit) : radius;
    }
    // How far a monster's melee blow on the party reaches when its attack lands, from the middle of its body to the
    // party's: MM8 pushes the blow with reach 0x1400 and lands it within reach + 32 (MM8-Rel.exe 0x402238, 0x4374bf).
    // A party that steps back during the swing is still hit; only walls (line of sight) stop the blow.
    static constexpr float MonsterMeleeImpactReach = 5120.0f + 32.0f;
    bool isBound() const;
    bool actorLooksUndead(int16_t monsterId) const;
    int16_t relationMonsterId(int16_t monsterId, uint32_t allyMonsterType) const;

    DirectSpellImpactResult resolveDirectSpellImpact(
        uint32_t spellId,
        uint32_t skillLevel,
        int baseDamage,
        bool actorLooksUndead) const;
    static std::optional<bx::Vec3> spellPushVelocity(
        uint32_t spellId,
        uint32_t skillLevel,
        float actorX,
        float actorY,
        float sourceX,
        float sourceY);

    SharedSpellEffectResult tryApplySharedSpellEffect(
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        bool actorLooksUndead,
        bool defaultHostileToParty,
        int spellResistance,
        GameplayActorSpellEffectState &state,
        std::optional<float> rulesetSeconds = std::nullopt) const;

    void updateSpellEffectTimers(
        GameplayActorSpellEffectState &state,
        float deltaSeconds,
        bool defaultHostileToParty) const;
    // Whether any of the actor's spell effects still counts down.
    static bool hasRunningSpellEffectTimer(const GameplayActorSpellEffectState &state);

    bool isPartyControlledActor(GameplayActorControlMode controlMode) const;
    // pRelationOverrides: the map's evt.SetMonsterRelation rows, which replace the faction relation (as for targets).
    bool monsterIdsAreFriendly(
        int16_t leftMonsterId,
        int16_t rightMonsterId,
        const std::unordered_map<uint32_t, int32_t> *pRelationOverrides = nullptr) const;
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
        bool attackingState,
        bool force = false) const;
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
    // pRelationOverrides: the map's evt.SetMonsterRelation rows (EventRuntimeState::monsterRelationOverrides), which
    // replace the faction relation between the two monsters: a positive one makes the actor engage at its range, 0
    // stops it. A row may name an actor group on either side (relationGroupSide: MM9's AddEnemy on a few placed
    // guards, not on their whole monster row); a group's row wins over its monsters' rows.
    GameplayActorTargetPolicyResult resolveActorTargetPolicy(
        const GameplayActorTargetPolicyState &actor,
        const GameplayActorTargetPolicyState &target,
        const std::unordered_map<uint32_t, int32_t> *pRelationOverrides = nullptr) const;
    static uint32_t relationOverrideKey(uint32_t leftMonsterId, uint32_t rightMonsterId)
    {
        return (leftMonsterId << 16) | (rightMonsterId & 0xFFFFu);
    }
    // A relation row's side naming an actor group (1-32767) instead of a monster: monster ids never set bit 15.
    static uint32_t relationGroupSide(uint32_t group)
    {
        return 0x8000u | (group & 0x7FFFu);
    }

    bool clearSpellEffects(
        GameplayActorSpellEffectState &state,
        bool defaultHostileToParty) const;

    bool breakFearAndControlOnPartyDamage(GameplayActorSpellEffectState &state) const;

    int effectiveArmorClass(int baseArmorClass, const GameplayActorSpellEffectState &state) const;

private:
    GameplayActorTargetPolicyResult resolveFactionTargetPolicy(
        const GameplayActorTargetPolicyState &actor,
        const GameplayActorTargetPolicyState &target) const;
    const MonsterTable *m_pMonsterTable = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    float m_partyEngagementRange = MaximumPartyEngagementRange;
    std::optional<float> m_worldPartyHitReach;
    Mm9PartyAwareness m_mm9PartyAwareness;
    float m_meleeVerticalReach = 0.0f;
    float m_levelRadiusLimit = 0.0f;
    bool m_friendlyActorsBlockParty = false;
};
}
