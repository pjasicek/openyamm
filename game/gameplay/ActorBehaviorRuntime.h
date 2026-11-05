#pragma once

#include "engine/scripting/LuaStateOwner.h"
#include "game/gameplay/GameplayActorAiTypes.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/party/SkillData.h"
#include "game/tables/MonsterShields.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class ActorBehaviorCatalog;
class IGameplayWorldRuntime;
class Party;
class SpellTable;

struct ActorBehaviorSpell
{
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    int useChance = 100;
};

struct ActorBehaviorTimer
{
    std::string name;
    float remainingSeconds = 0.0f;
};

// The shield dome drawn for a ward (WorldFxSystem::syncShieldDomes, ShieldDomeRenderer).
struct ActorBehaviorWardVisual
{
    bool dome = true;
    std::array<uint8_t, 3> color = {170, 110, 255};
    float intensity = 1.0f;
    // Rim sharpness: higher values keep the glow closer to the silhouette.
    float rimPower = 3.0f;
    // 0 = smooth surface, 1 = strongly broken into drifting energy.
    float noise = 0.35f;
};

struct ActorBehaviorWard
{
    std::string id;
    float radius = 0.0f;
    // Negative: until removed or the actor dies.
    float remainingSeconds = -1.0f;
    float ageSeconds = 0.0f;
    ActorBehaviorWardVisual visual;
    // Optional effect respawned at the actor while the ward holds, so the player can see its extent.
    std::string effectId;
    float effectScale = 1.0f;
    float effectIntervalSeconds = 0.0f;
    float effectCooldownSeconds = 0.0f;
};

struct ActorBehaviorPerform
{
    std::string clip;
    ActorAiAnimationState fallbackAnimation = ActorAiAnimationState::AttackRanged;
    float durationSeconds = 0.0f;
    float elapsedSeconds = 0.0f;
    // Waits for an attack already under way; the hold begins once the actor is free.
    bool started = false;
};

// Everything a behaviour instance keeps between frames. It is saved with the map, so scripts may rely on it; the
// Lua state itself is not saved (script data lives in scriptState, written after every handler call).
struct ActorBehaviorInstanceState
{
    size_t actorIndex = static_cast<size_t>(-1);
    uint32_t actorId = 0;
    std::string behaviorId;
    bool started = false;
    bool deathHandled = false;
    int lastHp = 0;
    float ageSeconds = 0.0f;
    float thinkCooldownSeconds = 0.0f;
    uint32_t randomState = 0;
    std::vector<uint8_t> scriptState;
    std::vector<float> firedHealthThresholds;
    std::vector<ActorBehaviorTimer> timers;
    std::vector<ActorBehaviorWard> wards;
    std::optional<ActorBehaviorPerform> perform;
    std::optional<ActorBehaviorSpell> spellOverride;
    std::optional<ActorBehaviorSpell> nextCast;
    std::optional<GameplayActorAiType> aiTypeOverride;
    bool suppressFlee = false;
    // self:setSpeed: movement and attack rate times this (1: unchanged); self:setInvulnerable: no damage reaches the
    // actor (its shield included). Saved (save version 135).
    float speedMultiplier = 1.0f;
    bool invulnerable = false;
    // Per-actor tactics a script set: a leash (self:setLeash, a post at most this far from home), a ranged band
    // (self:setRangedBand) and a point it goes to and holds with no target (self:moveTo). Saved (version 135).
    std::optional<float> leashRadius;
    std::optional<std::array<float, 2>> rangedBand;
    std::optional<GameplayWorldPoint> moveTarget;
    // self:setArmoredFront: hits from within the arc (radians either side of its facing) deal the share.
    std::optional<std::array<float, 2>> armoredFront;
};

// An MM9 boss script's hold on its MM9 loop (MM9_MONSTER_AI_PLAN.md phase 5): its directives (self:setMm9), its
// one-shot commands for the next AI step, what the last AI step showed it and the loop's events it has not handled yet.
// Runtime only, never saved: scripts set their directives in onStart and again in onLoad.
struct ActorBehaviorMm9Script
{
    struct Event
    {
        // onTargetChanged (the loop's held target), onAttackDone, onHit (the attacker), onTrigger (text: the message).
        std::string handler;
        ActorAiTargetKind targetKind = ActorAiTargetKind::None;
        size_t targetActorIndex = static_cast<size_t>(-1);
        std::string text;
    };

    bool configured = false;
    bool drivesAttacks = false;
    bool passive = false;
    bool ignoresCalls = false;
    // YanmirBase.scr, Njam1000.inc, EboraBath.scr: CanDamage FALSE, no physical damage reaches it.
    bool immunePhysical = false;
    float chaseLimitSeconds = -1.0f;
    float turnRadiansPerSecond = 0.0f;

    bool setTarget = false;
    ActorAiTargetKind targetKind = ActorAiTargetKind::None;
    size_t targetActorIndex = static_cast<size_t>(-1);
    std::optional<GameplayActorAttackAbility> attack;
    std::vector<std::string> traceLines;

    // The last AI step: the target the loop holds, its edge distance (MM9's AIGetDistance), a clear line to it and how
    // high it is above this actor's feet; its attack ready, an attack under way, resting dormant; its radius.
    bool viewValid = false;
    ActorAiTargetKind heldKind = ActorAiTargetKind::None;
    size_t heldActorIndex = static_cast<size_t>(-1);
    bool targetOffered = false;
    float targetDistance = 0.0f;
    bool targetClear = false;
    float targetHeight = 0.0f;
    bool attackReady = false;
    bool attacking = false;
    bool dormant = false;
    // The world perceives the party for it this step (MM9's OnFoundPlayer; a passive script sees it too).
    bool sensesParty = false;
    float radius = 0.0f;
    uint32_t damageSerial = 0;

    // Its placement (the scene's mm9_ai): the MM9 script it ran and its params, the summon class and points.
    bool placementRead = false;
    std::string script;
    std::string scriptParams;
    std::string summonClass;
    std::vector<std::array<int32_t, 3>> summonPoints;

    std::vector<Event> events;
};

// An actor as the last AI step saw it, for an MM9 boss script's self:targets (phase 5).
struct ActorBehaviorAiActorView
{
    size_t actorIndex = 0;
    int16_t monsterId = 0;
    GameplayWorldPoint position;
    float radius = 0.0f;
    float height = 0.0f;
    int currentHp = 0;
    bool hostileToParty = false;
    // Dead or dying, or hidden (an invisible bit: left the map, not placed yet): never a target.
    bool dead = false;
    bool invisible = false;
};

// Presentation view of an active ward: where to draw its dome and the projectile hits that ripple it.
struct ActorBehaviorWardDisplay
{
    struct Impact
    {
        // Unit direction from the ward centre to the hit.
        GameplayWorldPoint direction;
        float ageSeconds = 0.0f;
    };

    uint32_t actorId = 0;
    std::string wardId;
    GameplayWorldPoint center;
    float radius = 0.0f;
    float groundZ = 0.0f;
    float ageSeconds = 0.0f;
    float remainingSeconds = -1.0f;
    ActorBehaviorWardVisual visual;
    std::vector<Impact> impacts;
};

struct ActorBehaviorActorFacts
{
    size_t actorIndex = static_cast<size_t>(-1);
    uint32_t actorId = 0;
    int16_t monsterId = 0;
    int currentHp = 0;
    int maxHp = 0;
    bool dead = false;
    bool hostileToParty = false;
    GameplayWorldPoint position;
    float height = 0.0f;
    ActorAiAnimationState animationState = ActorAiAnimationState::Standing;
    float yawRadians = 0.0f;
};

struct ActorBehaviorFrameFacts
{
    float deltaSeconds = 0.0f;
    // For self:qbit (null in tests without a party).
    const Party *pParty = nullptr;
    GameplayWorldPoint partyPosition;
    uint32_t actorCount = 0;
    // Scripted actors, plus actors appended since the last frame (candidates for a monster's default behaviour).
    std::vector<ActorBehaviorActorFacts> actors;
};

struct ActorBehaviorSoundRequest
{
    std::string soundName;
    GameplayWorldPoint position;
};

struct ActorBehaviorEffectRequest
{
    std::string effectId;
    GameplayWorldPoint position;
    float scale = 1.0f;
};

// A command a script gives its own actor that the world carries out: blink away (self:blink), suspend or restore its
// energy shield (self:suspendShield, self:restoreShield), leave the map with an effect (self:leave), or push its target
// away (self:push: the Dragon King's wing buffet).
struct ActorBehaviorActorCommand
{
    enum class Kind
    {
        Blink,
        SuspendShield,
        RestoreShield,
        Leave,
        Push,
    };

    Kind kind = Kind::Blink;
    size_t actorIndex = 0;
    // SuspendShield: seconds without regeneration (negative: until restoreShield). Leave: the effect at the actor.
    // Push: the distance, away from the actor, of the target (targetKind, targetActorIndex).
    float seconds = -1.0f;
    std::string effectId;
    ActorAiTargetKind targetKind = ActorAiTargetKind::None;
    size_t targetActorIndex = static_cast<size_t>(-1);
};

struct ActorBehaviorSummonRequest
{
    int16_t monsterId = 0;
    uint32_t count = 0;
    GameplayWorldPoint position;
};

struct ActorBehaviorFrameResult
{
    std::vector<ActorBehaviorSoundRequest> sounds;
    std::vector<ActorBehaviorEffectRequest> effects;
    std::vector<std::string> statusMessages;
    std::vector<ActorBehaviorSummonRequest> summons;
    std::vector<ActorBehaviorActorCommand> actorCommands;
    // Map events scripts ran (self:runEvent).
    std::vector<uint16_t> mapEvents;
};

// Per-map Lua behaviours layered on the shared monster AI. Scripts react to events (start, damage, health thresholds,
// timers, wards, death) and issue commands; native AI keeps moving, targeting and attacking. Each world runtime owns
// one, steps it before the actor AI, lets it adjust the AI facts of scripted actors and saves its snapshot.
class ActorBehaviorRuntime
{
public:
    struct Snapshot
    {
        std::vector<ActorBehaviorInstanceState> instances;
        uint32_t scannedActorCount = 0;
    };

    ActorBehaviorRuntime() = default;
    ActorBehaviorRuntime(const ActorBehaviorRuntime &) = delete;
    ActorBehaviorRuntime &operator=(const ActorBehaviorRuntime &) = delete;

    void bind(const ActorBehaviorCatalog *pCatalog, const SpellTable *pSpellTable);
    void reset();

    // Collects facts from the world, runs scripts and applies their commands.
    void step(IGameplayWorldRuntime &world, float deltaSeconds);

    ActorBehaviorFrameFacts collectFrameFacts(const IGameplayWorldRuntime &world, float deltaSeconds) const;
    ActorBehaviorFrameResult update(const ActorBehaviorFrameFacts &facts);
    static void applyFrameResult(IGameplayWorldRuntime &world, const ActorBehaviorFrameResult &result);

    // Applies script directives to scripted actors and the catalogue's tactics to every actor of a monster with them.
    void applyAiFacts(ActorAiFrameFacts &facts);
    void observeAiResult(const ActorAiFrameResult &result);
    void applyPresentation(size_t actorIndex, GameplayRuntimeActorState &state) const;
    // True for a monster whose tactics turn it at a traverse rate (a turret): the world runtimes skip their instant
    // reaction turns (hit, alert) for it, and its AI turns it to the attacker at that rate instead.
    bool turnsAtTraverseRate(int16_t monsterId) const;
    // The MM9 AI profile of a monster row on an MM9 loop (the walkers, swimmers, fliers, turrets with the Dragon King,
    // townsfolk and guards; null for every other monster): the world runtimes read its perception, attack reach,
    // sweep, wince, alert radius, water and pods with it. standInCivilian: the actor is a townsperson placed on a row
    // without a profile (scene mm9_civilian), which runs mm9StandInCivilianProfile in a world with MM9 profiles.
    const Mm9AiProfile *mm9LoopProfile(int16_t monsterId, bool standInCivilian = false) const;
    // self:setSpeed and self:setInvulnerable of a scripted actor (1 and false without a script); a hit of the tier
    // also misses an actor whose MM9 script is immune to physical damage (self:setMm9{immune = "physical"}).
    float speedMultiplier(size_t actorIndex, uint32_t actorId) const;
    bool invulnerable(size_t actorIndex, ShieldAttackTier tier) const;
    // An MM9 map trigger sent to a scripted actor (MM9's Trigger <object>, <message>; an arena's `trigger` event): its
    // script's onTrigger runs at the next step. False without a script.
    bool trigger(size_t actorIndex, const std::string &message);
    // The actors of the last AI step (an MM9 boss script's self:targets); empty without scripted actors.
    const std::vector<ActorBehaviorAiActorView> &aiActors() const;
    // The party's centre (its feet plus half its height) and radius at the last AI step.
    const GameplayWorldPoint &aiPartyPosition() const;
    float aiPartyRadius() const;
    // The share of a hit from source an armoured front lets through (self:setArmoredFront; 1 without one).
    float incomingDamageMultiplier(size_t actorIndex, const GameplayWorldPoint &actorPosition, float actorYawRadians,
        const GameplayWorldPoint &source) const;
    // The post leash of a monster whose tactics hold a post (0 without one); it applies only to actors the map placed
    // `immobile`.
    float postLeashRadius(int16_t monsterId) const;

    const std::vector<GameplayProjectileService::ProjectileWardFacts> &projectileWards() const;
    const std::vector<ActorBehaviorWardDisplay> &wardDisplays() const;
    void recordWardBlock(const GameplayProjectileService::ProjectileWardBlock &block);

    bool attach(size_t actorIndex, uint32_t actorId, const std::string &behaviorId, std::string &error);
    // Map scripts and the console: keeps a running instance of the same behaviour (map on-load events re-run on
    // every load), replaces a different one.
    bool attachToWorldActor(
        const IGameplayWorldRuntime &world,
        size_t actorIndex,
        const std::string &behaviorId,
        std::string &error);
    const ActorBehaviorInstanceState *instance(size_t actorIndex) const;
    std::vector<const ActorBehaviorInstanceState *> instances() const;

    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);

    // Lua-facing implementation; public only for the C callbacks in ActorBehaviorRuntime.cpp.
    struct LuaCallContext;
    LuaCallContext *activeCall() const;
    const SpellTable *spellTable() const;

private:
    struct InstanceRecord
    {
        ActorBehaviorInstanceState state;
        int selfReference = LUA_NOREF;
        int stateReference = LUA_NOREF;
        bool needsLoadCallback = false;
        bool failed = false;
        std::vector<std::string> pendingWardBlocks;
        // Recent blocks for the dome ripple; presentation only, never saved.
        struct WardImpact
        {
            std::string wardId;
            GameplayWorldPoint point;
            float ageSeconds = 0.0f;
        };
        std::vector<WardImpact> wardImpacts;
        bool performRestartPending = false;
        ActorBehaviorMm9Script mm9;
    };

    bool ensureLua();
    void destroyLua();
    int moduleReference(const std::string &behaviorId);
    bool ensureInstanceLua(InstanceRecord &record);
    bool pushHandler(InstanceRecord &record, const char *pHandlerName, const char *pTableKey);
    bool callPushedHandler(
        InstanceRecord &record,
        const ActorBehaviorActorFacts &actor,
        const ActorBehaviorFrameFacts &facts,
        ActorBehaviorFrameResult &result,
        const char *pHandlerName,
        int argumentCount,
        const std::function<void(lua_State *)> &pushArguments);
    bool callHandler(
        InstanceRecord &record,
        const ActorBehaviorActorFacts &actor,
        const ActorBehaviorFrameFacts &facts,
        ActorBehaviorFrameResult &result,
        const char *pHandlerName,
        const char *pTableKey,
        int argumentCount,
        const std::function<void(lua_State *)> &pushArguments);
    void updateInstance(
        InstanceRecord &record,
        const ActorBehaviorActorFacts &actor,
        const ActorBehaviorFrameFacts &facts,
        ActorBehaviorFrameResult &result);
    void fireHealthThresholds(
        InstanceRecord &record,
        const ActorBehaviorActorFacts &actor,
        const ActorBehaviorFrameFacts &facts,
        ActorBehaviorFrameResult &result);
    void rebuildProjectileWards(const ActorBehaviorFrameFacts &facts);
    void applyTactics(ActorAiFrameFacts &facts);
    // An MM9 boss script's directives into its AI facts, and what the step shows it (its view, the loop's events).
    void applyMm9Script(InstanceRecord &record, ActorAiFacts &actor);
    void readMm9Placement(const IGameplayWorldRuntime &world, size_t actorIndex, ActorBehaviorMm9Script &script) const;
    // An MM9 monster's profile (ActorTacticsFacts::mm9Profile) with its placement's overrides.
    void applyMm9AiProfile(ActorAiFacts &actor) const;
    void updateTacticTurret(ActorAiFacts &actor, bool active, float stepSeconds);
    void reportScriptError(InstanceRecord &record, const std::string &message);

    const ActorBehaviorCatalog *m_pCatalog = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    std::unordered_map<size_t, InstanceRecord> m_instances;
    uint32_t m_scannedActorCount = 0;
    std::vector<GameplayProjectileService::ProjectileWardFacts> m_projectileWards;
    std::vector<ActorBehaviorWardDisplay> m_wardDisplays;
    // The target each actor with tactics engaged at the last AI step, for its model's aim (presentation only, never
    // saved: the next step after a load fills it again).
    struct TacticAim
    {
        uint32_t actorId = 0;
        GameplayWorldPoint point;
    };
    std::unordered_map<size_t, TacticAim> m_tacticAims;
    // A turret's idle scan, the hold of its last aim and the velocity estimate of its target for the lead (tactics
    // `scan`, `lead_seconds`; presentation-grade state, never saved: after a load the scan restarts from the facing).
    struct TacticTurret
    {
        uint32_t actorId = 0;
        TurretScanState scan;
        uint32_t scanStarts = 0;
        float centreYawRadians = 0.0f;
        float scanPitchRadians = 0.0f;
        bool scanning = false;
        bool engaged = false;
        float holdRemainingSeconds = 0.0f;
        float heldYawRadians = 0.0f;
        bool hasHeldAim = false;
        GameplayWorldPoint heldAim;
        ActorAiTargetKind targetKind = ActorAiTargetKind::None;
        size_t targetActorIndex = static_cast<size_t>(-1);
        bool hasTargetSample = false;
        GameplayWorldPoint targetSample;
        GameplayWorldPoint targetVelocity;
    };
    std::unordered_map<size_t, TacticTurret> m_tacticTurrets;
    // The last AI step's actors and party, for MM9 boss scripts (filled only while a script runs).
    std::vector<ActorBehaviorAiActorView> m_aiActors;
    GameplayWorldPoint m_aiPartyPosition;
    float m_aiPartyRadius = 0.0f;

    std::optional<Engine::LuaStateOwner> m_lua;
    bool m_luaFailed = false;
    std::unordered_map<std::string, int> m_moduleReferences;
    LuaCallContext *m_pActiveCall = nullptr;
};
}
