#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActorAiTypes.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/rules/CrowdControlDiminishing.h"
#include "game/tables/MonsterModifiers.h"
#include "game/tables/MonsterTable.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
struct EventRuntimeState;
struct GameplayCombatActorInfo;

// The burst radius of a monster's attack missile (MonsterModifierSet::missileBlast); 0 for none and for spells.
float missileBlastRadius(const MonsterModifierSet *pModifiers, GameplayProjectileService::MonsterAttackAbility ability);

// The homing a true_aim monster gives the projectiles it fires at a target (MonsterModifierSet::trueAim); empty for a
// monster without it or a shot with no target (actor index invalid for TargetKind::Actor).
std::optional<GameplayProjectileService::ProjectileHoming> trueAimProjectileHoming(
    const MonsterModifierSet *pModifiers,
    GameplayProjectileService::ProjectileHoming::TargetKind targetKind,
    size_t targetActorIndex,
    uint32_t targetActorId);

// A monster's spell_conditions on its combat info (GameplayCombatController's hit conditions); a monster without them
// keeps the default: no spell condition. A spell slot a ruleset replaced (generatedSpell1/2) leaves no spell condition.
void applyHitConditionModifiers(
    const MonsterModifierSet *pModifiers,
    bool spell1Replaced,
    bool spell2Replaced,
    GameplayCombatActorInfo &info);

// Blinks of one world runtime's actors (MonsterModifierSet::blink), indexed by its actor indices. Shared decisions:
// triggers, cooldowns and the candidate spots; the world runtime checks a spot (floor, walls, other bodies, sight)
// and moves the actor. Runtime state only: cooldowns restart on every map load and after loading a save.
class GameplayActorModifiers
{
public:
    struct ActorFacts
    {
        int16_t monsterId = 0;
        uint32_t actorId = 0;
        // Alive and free to act (not dying, stunned or paralysed).
        bool canAct = false;
        // Feet.
        std::array<float, 3> position = {};
    };

    struct BlinkRequest
    {
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        const BlinkModifier *pBlink = nullptr;
        std::array<float, 3> origin = {};
        // Where the last threat came from (the attacker of the last hit, the target of its last shot), if known.
        std::optional<std::array<float, 3>> threat;
        // Deterministic per actor and blink, for the candidate spots.
        uint32_t seed = 0;
    };

    void bind(const MonsterModifierTable *pTable);
    void clear();
    bool active() const
    {
        return m_pTable != nullptr && m_pTable->hasBlink();
    }
    // A hit on the actor: source is the attacker's position, damaged that it lost hit points or shield, shieldBroke
    // that its energy shield broke.
    void observeHit(size_t actorIndex, int16_t monsterId, uint32_t actorId, const std::array<float, 3> &source,
        bool damaged, bool shieldBroke);
    // The actor fights: it released an attack at target.
    void observeAttack(size_t actorIndex, int16_t monsterId, uint32_t actorId, const std::array<float, 3> &target);
    // Per actor step: ages cooldowns and returns the actors due to blink now.
    std::vector<BlinkRequest> update(float deltaSeconds, size_t actorCount,
        const std::function<ActorFacts(size_t)> &actorFacts);
    // The world tried the request's spots: a blink starts the cooldown; a failure retries after a short delay.
    void finishBlink(const BlinkRequest &request, bool blinked);
    // Candidate spots (feet, at the origin's height) of a blink: random directions and distances within the
    // modifier's range, the ones turning away from the threat first. Deterministic for a seed.
    static std::vector<std::array<float, 3>> blinkCandidates(const BlinkRequest &request, size_t count);
    // The effect at both ends and the sound at the arrival, queued into the world's event runtime state.
    static void queueBlinkPresentation(EventRuntimeState &eventRuntimeState, const BlinkModifier &blink,
        const std::array<float, 3> &fromCenter, const std::array<float, 3> &toCenter);
    // The blink of a monster without the modifier that a script or the console makes blink (the modifier's defaults).
    static const BlinkModifier &defaultBlink()
    {
        static const BlinkModifier blink = {};
        return blink;
    }
    // Stagger rules (MonsterModifierSet::stagger): body damage the actor took, the clock their window and cooldown run
    // on, and whether a hit may start a hit reaction now (true for a monster without the rules; a yes starts its
    // cooldown).
    void recordDamage(size_t actorIndex, int16_t monsterId, uint32_t actorId, int damage);
    void tickStagger(float deltaSeconds);
    bool allowsStagger(size_t actorIndex, int16_t monsterId, uint32_t actorId, int maxHp);
    // Blinks so far (console, tests).
    uint32_t blinkCount() const
    {
        return m_blinkCount;
    }

    // Charges (MonsterModifierSet::charge). Phases of one charge: wind-up, dash, then recovery (a short one after a
    // hit, the stumble after a miss); between charges the cooldown runs.
    enum class ChargePhase
    {
        Ready,
        Windup,
        Dash,
        Recover,
    };

    struct ChargeActorFacts
    {
        int16_t monsterId = 0;
        uint32_t actorId = 0;
        // Alive and free to act (not dying, stunned, paralysed, invisible or mid-attack).
        bool canAct = false;
        // Not dying or dead.
        bool alive = false;
        // Stunned or paralysed (a detonation's charge ends; an attack under way does not end it).
        bool incapacitated = false;
        // Hit points over maximum (frenzy's health_below).
        float healthShare = 1.0f;
        // Hostile to the party and aware of it (not party-controlled).
        bool engagesParty = false;
        // Hostile to the party (not party-controlled), aware of it or not: frenzy's health and shield triggers.
        bool hostileToParty = false;
        // Feet.
        std::array<float, 3> position = {};
        // Horizontal distance between the actor's and the party's edges.
        float partyEdgeDistance = 0.0f;
        // The party's feet.
        std::array<float, 3> partyPosition = {};
        // A post's leash (an actor placed `immobile` whose tactics hold a post): a dash stops this far from home.
        // 0 without a post.
        float leashRadius = 0.0f;
        std::array<float, 3> homePosition = {};
    };

    enum class ChargeStepResult
    {
        Moved,
        // A wall, a ledge, the floor's end, a decoration or another actor in the way.
        Blocked,
        // The party is in the way: the hit.
        Contact,
    };

    enum class ChargeEventKind
    {
        WindupStarted,
        Hit,
        Missed,
    };

    struct ChargeEvent
    {
        ChargeEventKind kind = ChargeEventKind::WindupStarted;
        size_t actorIndex = 0;
        const ChargeModifier *pCharge = nullptr;
        // Unit dash direction (horizontal).
        float directionX = 0.0f;
        float directionY = 0.0f;
    };

    // Detonations (MonsterModifierSet::detonate). Phases of one: the charge, then a short hold after the blast; between
    // detonations the cooldown runs. It never overlaps a charge or a frenzy's holds.
    enum class DetonatePhase
    {
        Ready,
        Charging,
        Blasted,
    };

    enum class DetonateEventKind
    {
        ChargeStarted,
        Exploded,
        // A stun, paralysis or death in the charge: no blast.
        Cancelled,
    };

    struct DetonateEvent
    {
        DetonateEventKind kind = DetonateEventKind::ChargeStarted;
        size_t actorIndex = 0;
        const DetonateModifier *pDetonate = nullptr;
    };

    // The actors' melee reach (edge to edge): a detonation's trigger distance when its modifier gives none.
    static constexpr float DetonateMeleeReach = 307.2f;
    // After its blast the actor holds this long (in turn-based mode the blast is its action).
    static constexpr float DetonateBlastHoldSeconds = 0.5f;

    // What a world runtime does for a charge: sight to the party, one dash step (the blink spot checks: floor within
    // maxHeightChange, walls, other bodies; it moves the actor and faces it along the dash) and the presentation and
    // the hit of an event.
    struct ChargeWorld
    {
        std::function<bool(size_t actorIndex)> hasLineOfSightToParty;
        std::function<ChargeStepResult(size_t actorIndex, float x, float y, float maxHeightChange, float yaw)> step;
        std::function<void(const ChargeEvent &event)> handle;
        // A frenzy's roar starts (its flash and sound).
        std::function<void(size_t actorIndex, const FrenzyModifier &frenzy)> frenzyRoared;
        // A detonation's charge starts, ends in its blast or is cancelled.
        std::function<void(const DetonateEvent &event)> detonated;
    };

    // A charge step is at most this long (so a fast dash cannot step through a thin wall or past the party), and the
    // floor may rise or drop at most this much over one step.
    static constexpr float ChargeStepLength = 24.0f;
    static constexpr float ChargeStepHeightChange = 48.0f;
    // After a hit the charger recovers this long before the cooldown runs.
    static constexpr float ChargeHitRecoverSeconds = 0.35f;

    bool chargeActive() const
    {
        return m_pTable != nullptr && m_pTable->hasCharge();
    }
    // Per fixed actor step, after the AI: starts charges, runs the wind-up timers and the dashes.
    void updateCharges(float deltaSeconds, size_t actorCount, const std::function<ChargeActorFacts(size_t)> &actorFacts,
        const ChargeWorld &world);
    // Before the AI: a charging actor holds (ActorBehaviorFacts::holdActive) so its AI neither moves nor attacks.
    void applyChargeHolds(ActorAiFrameFacts &facts) const;
    // The actor's charge phase (Ready without a charge).
    ChargePhase chargePhase(size_t actorIndex) const;
    // While a charger recovers from a hit with ChargeModifier::strikeSeconds: true, and the playback time of its
    // `charge_strike` script clip.
    bool chargeStrikeClip(size_t actorIndex, uint32_t actorId, float &clipSeconds) const;
    // The script clip role (actors.yml `script_clips`) a modifier plays on the actor's model now and its playback
    // time: `frenzy` in a frenzy's roar, `spent` in its spent hold, `charge_strike` after a charge's hit, `detonate` in
    // a detonation's charge.
    bool scriptedClip(size_t actorIndex, uint32_t actorId, const char *&pRole, float &clipSeconds) const;
    // Starts a charge now when the actor has the modifier (console, scenarios): the trigger band, sight and cooldown
    // are not checked. False without the modifier or while it charges already.
    bool startCharge(size_t actorIndex, int16_t monsterId, uint32_t actorId, const std::array<float, 3> &position,
        const std::array<float, 3> &partyPosition, const ChargeWorld &world);
    // Charges so far, and those that hit or missed (console, tests).
    uint32_t chargeCount() const
    {
        return m_chargeCount;
    }
    uint32_t chargeHitCount() const
    {
        return m_chargeHitCount;
    }
    uint32_t chargeMissCount() const
    {
        return m_chargeMissCount;
    }
    struct ChargeHit
    {
        int damage = 1;
        CombatDamageType damageType = CombatDamageType::Physical;
        GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
        // Contact always lands (stepping aside is the defence): an attack bonus past any armour roll.
        int attackBonus = 1000;
    };

    // Frenzies (MonsterModifierSet::frenzy). Phases of one frenzy: the roar, the frenzy itself, then the spent hold;
    // between frenzies the cooldown runs. A frenzy and a charge never overlap: no charge starts in the roar or the
    // spent hold, and no frenzy starts during a charge.
    enum class FrenzyPhase
    {
        Ready,
        Roar,
        Active,
        Spent,
    };

    bool frenzyActive() const
    {
        return m_pTable != nullptr && m_pTable->hasFrenzy();
    }
    // Per fixed actor step, after the AI: triggers, the roar, the frenzy and the spent hold (the charges' facts).
    void updateFrenzies(float deltaSeconds, size_t actorCount,
        const std::function<ChargeActorFacts(size_t)> &actorFacts, const ChargeWorld &world);
    // Before the AI: the roar and the spent hold hold the actor; a frenzy multiplies its move speed and the rate its
    // attack recovery runs down.
    void applyFrenzies(ActorAiFrameFacts &facts) const;
    FrenzyPhase frenzyPhase(size_t actorIndex) const;
    // Starts a frenzy's roar now when the actor has the modifier (console, scenarios): the triggers and the cooldown
    // are not checked. False without the modifier, while it is in a frenzy or while it charges.
    bool startFrenzy(size_t actorIndex, int16_t monsterId, uint32_t actorId, const ChargeWorld &world);
    // The multiplier of the actor's move speed: the frenzy's speed_multiplier while it lasts, else 1.
    float moveSpeedMultiplier(size_t actorIndex, uint32_t actorId) const;
    // The multiplier of the actor's model emission: the frenzy's glow_multiplier while it lasts, a detonation's rising
    // glow while it charges, else 1.
    float emissionMultiplier(size_t actorIndex, uint32_t actorId) const;
    // Frenzies so far (console, tests).
    uint32_t frenzyCount() const
    {
        return m_frenzyCount;
    }
    // The roar's flash and sound, queued into the world's event runtime state.
    static void queueFrenzyPresentation(EventRuntimeState &eventRuntimeState, const FrenzyModifier &frenzy,
        const std::array<float, 3> &center);

    bool detonateActive() const
    {
        return m_pTable != nullptr && m_pTable->hasDetonate();
    }
    // Per fixed actor step, before the AI (so the charge holds it at once): starts charges, runs them and the blasts.
    // pTurnBasedGrants (turn-based mode): the actors the turn engine lets act this step; a charge then starts only on
    // the actor's turn and explodes at the start of its next one instead of after windup_seconds, and the cooldown
    // counts the actor's turns (a grant spent waiting it out) instead of seconds.
    void updateDetonations(float deltaSeconds, size_t actorCount,
        const std::function<ChargeActorFacts(size_t)> &actorFacts, const ChargeWorld &world,
        const std::vector<size_t> *pTurnBasedGrants);
    // Before the AI: a charging (or just blasted) actor holds.
    void applyDetonationHolds(ActorAiFrameFacts &facts) const;
    DetonatePhase detonatePhase(size_t actorIndex, uint32_t actorId) const;
    // The share of the charge done (0-1; 0 when not charging).
    float detonateChargeShare(size_t actorIndex, uint32_t actorId) const;
    // Starts a detonation's charge now when the actor has the modifier (console, scenarios): the trigger distance,
    // sight and cooldown are not checked. False without the modifier, while it detonates, charges or frenzies.
    bool startDetonation(size_t actorIndex, int16_t monsterId, uint32_t actorId, const ChargeWorld &world);
    // The diminishing-returns history Standard's rules hold a boss-modifier monster by (MonsterModifierSet::boss); null
    // for every other monster. Cleared with the map.
    CrowdControlDiminishingReturns *bossCrowdControl(int16_t monsterId);
    // The seconds a blow's fear and berserk hold a boss-modifier monster (applyBossBlowCrowdControl); unset: the
    // world's own duration (the skill level in minutes).
    struct BossBlowControl
    {
        std::optional<float> fearSeconds;
        std::optional<float> berserkSeconds;
    };
    // A party blow's stun or paralysis on a boss-modifier monster under Standard rules (their seconds not set by the
    // rules) becomes MAW's weapon paralysis through diminishing returns (bossBlowCrowdControlSeconds): no stun, the
    // paralysis 2 s from a stun (Master) and 4 s from a paralysis (Grandmaster), less with repeats. A blow's fear or
    // berserk (item effects) lasts as MAW's Fear or Berserk spell at the blow's mastery through the control group's
    // diminishing returns (bossBlowControlSeconds); a share of 0 clears it. MAW's own blows and every other monster's
    // pass unchanged.
    BossBlowControl applyBossBlowCrowdControl(CharacterAttackResult &attack, int16_t monsterId, uint64_t targetKey,
        double nowSeconds);
    // Detonations started, exploded and cancelled so far (console, tests).
    uint32_t detonationCount() const
    {
        return m_detonationCount;
    }
    uint32_t detonationBlastCount() const
    {
        return m_detonationBlastCount;
    }
    uint32_t detonationCancelCount() const
    {
        return m_detonationCancelCount;
    }
    // A co-op guest's copy of a host's monster (ReplicaActorPose flags): mirrors its charge for the glow, and says
    // which edges the presentation must show (true when the charge began or the blast went off with this pose).
    struct ReplicaDetonateEdges
    {
        bool chargeStarted = false;
        bool exploded = false;
        bool cancelled = false;
    };
    ReplicaDetonateEdges applyReplicaDetonation(size_t actorIndex, int16_t monsterId, uint32_t actorId, bool charging,
        bool blasted);
    // The co-op pose flags (ReplicaActorPose::DetonateCharging, DetonateBlasted) of a phase.
    static uint8_t replicaPoseFlags(DetonatePhase phase);
    // A guest's frame: its mirrored charges go on (the glow rises between the host's messages).
    void tickReplicaDetonations(float deltaSeconds);
    // The charge effect (carried on the body, growing) and sound, and the blast's effect and sound. A co-op guest
    // shows the effects without the sounds, which its host's world sends it.
    // The charge effect's scales follow the body: 1 for a body 200 tall (at least 0.5).
    static void queueDetonateChargePresentation(EventRuntimeState &eventRuntimeState, const DetonateModifier &detonate,
        size_t actorIndex, const std::array<float, 3> &center, float bodyHeight, bool withSound = true);
    static void queueDetonateStopPresentation(EventRuntimeState &eventRuntimeState, const DetonateModifier &detonate,
        size_t actorIndex);
    static void queueDetonateBlastPresentation(EventRuntimeState &eventRuntimeState, const DetonateModifier &detonate,
        size_t actorIndex, const std::array<float, 3> &center, bool withSound = true);

    // A charge's hit: its fixed damage (physical), or a roll of the monster's melee attack from seed: Attack1, or
    // Attack2 when Attack1 fires a missile and Attack2 does not (a Lancer's lance thrust).
    static ChargeHit chargeHit(const ChargeModifier &charge, const MonsterTable::MonsterStatsEntry *pStats,
        uint32_t seed);
    // The party knock-back impulse of a hit (horizontal velocity along the dash and an upward velocity) that throws
    // the party about distance units under gravity.
    static std::array<float, 3> chargeKnockbackImpulse(float directionX, float directionY, float distance,
        float gravity);
    // The wind-up flash and sound, and the hit sound, queued into the world's event runtime state.
    static void queueChargeWindupPresentation(EventRuntimeState &eventRuntimeState, const ChargeModifier &charge,
        const std::array<float, 3> &center);
    static void queueChargeHitPresentation(EventRuntimeState &eventRuntimeState, const ChargeModifier &charge,
        const std::array<float, 3> &center);

private:
    struct ChargeEntry
    {
        bool used = false;
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        const ChargeModifier *pCharge = nullptr;
        ChargePhase phase = ChargePhase::Ready;
        float timerSeconds = 0.0f;
        float cooldownSeconds = 0.0f;
        float directionX = 0.0f;
        float directionY = 0.0f;
        float travelled = 0.0f;
        float x = 0.0f;
        float y = 0.0f;
        bool stumbling = false;
    };

    ChargeEntry *ensureCharge(size_t actorIndex, int16_t monsterId, uint32_t actorId);
    void beginWindup(ChargeEntry &entry, size_t actorIndex, const std::array<float, 3> &position,
        const std::array<float, 3> &partyPosition, const ChargeWorld &world);
    void endDash(ChargeEntry &entry, size_t actorIndex, bool hit, const ChargeWorld &world);
    // True when (x, y) lies beyond the actor's post leash.
    static bool beyondLeash(const ChargeActorFacts &facts, float x, float y);

    struct FrenzyEntry
    {
        bool used = false;
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        const FrenzyModifier *pFrenzy = nullptr;
        FrenzyPhase phase = FrenzyPhase::Ready;
        float timerSeconds = 0.0f;
        float cooldownSeconds = 0.0f;
        float sincePeriodicSeconds = 0.0f;
        // The health trigger fired (it fires once); its frenzy still waits to start.
        bool healthTriggerUsed = false;
        bool healthPending = false;
        // A shield break asked for a frenzy, for shieldPendingSeconds more.
        float shieldPendingSeconds = 0.0f;
    };

    FrenzyEntry *ensureFrenzy(size_t actorIndex, int16_t monsterId, uint32_t actorId);
    const FrenzyEntry *frenzyEntry(size_t actorIndex, uint32_t actorId) const;
    void beginRoar(FrenzyEntry &entry, size_t actorIndex, const ChargeWorld &world);
    // True while the actor's frenzy holds it (the roar or the spent hold): no charge starts.
    bool frenzyHolds(size_t actorIndex, uint32_t actorId) const;

    struct DetonateEntry
    {
        bool used = false;
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        const DetonateModifier *pDetonate = nullptr;
        DetonatePhase phase = DetonatePhase::Ready;
        // Charging: the seconds charged; Blasted: the hold left.
        float timerSeconds = 0.0f;
        float cooldownSeconds = 0.0f;
        // Turn-based: the actor's own turns left before it may charge again (detonateCooldownTurns).
        int cooldownTurns = 0;
    };

    DetonateEntry *ensureDetonate(size_t actorIndex, int16_t monsterId, uint32_t actorId);
    const DetonateEntry *detonateEntry(size_t actorIndex, uint32_t actorId) const;
    void beginDetonation(DetonateEntry &entry, size_t actorIndex, const ChargeWorld &world);
    // True while the actor's detonation holds it (its charge or the hold after the blast): no charge or frenzy starts.
    bool detonationHolds(size_t actorIndex, uint32_t actorId) const;

    CrowdControlDiminishingReturns m_bossCrowdControl;
    std::vector<DetonateEntry> m_detonations;
    uint32_t m_detonationCount = 0;
    uint32_t m_detonationBlastCount = 0;
    uint32_t m_detonationCancelCount = 0;
    std::vector<FrenzyEntry> m_frenzies;
    uint32_t m_frenzyCount = 0;
    std::vector<ChargeEntry> m_charges;
    uint32_t m_chargeCount = 0;
    uint32_t m_chargeHitCount = 0;
    uint32_t m_chargeMissCount = 0;

private:
    struct Entry
    {
        bool used = false;
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        const BlinkModifier *pBlink = nullptr;
        float cooldownSeconds = 0.0f;
        float sincePeriodicSeconds = 0.0f;
        float sinceCombatSeconds = 1000.0f;
        // A hit or a shield break asked for a blink, for pendingSeconds more.
        float pendingSeconds = 0.0f;
        uint32_t hitCount = 0;
        uint32_t blinkCount = 0;
        std::optional<std::array<float, 3>> threat;
    };

    Entry *ensure(size_t actorIndex, int16_t monsterId, uint32_t actorId);

    struct StaggerEntry
    {
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        float cooldownUntilSeconds = 0.0f;
        // Damage and when it landed (the stagger clock), oldest first.
        std::vector<std::pair<float, int>> damage;
    };

    StaggerEntry *staggerEntry(size_t actorIndex, int16_t monsterId, uint32_t actorId, const StaggerModifier *&pStagger);

    const MonsterModifierTable *m_pTable = nullptr;
    std::vector<StaggerEntry> m_staggers;
    float m_staggerClockSeconds = 0.0f;
    std::vector<Entry> m_entries;
    uint32_t m_blinkCount = 0;
};
}
