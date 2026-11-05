#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"

#include <cstddef>
#include <functional>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class Party;
struct PartyMissileSource;
class CombatRules;
struct Character;
class ItemTable;
struct ObjectEntry;
class ObjectTable;
class SpecialItemEnchantTable;
class SpriteFrameTable;

class GameplayProjectileService
{
public:
    enum class MonsterAttackAbility
    {
        Attack1,
        Attack2,
        Spell1,
        Spell2,
    };

    // Homing of a true_aim monster's projectile (MonsterModifiers): each step it turns toward its target's current
    // position. Runtime only, never saved: a projectile in flight at a save flies straight on after the load.
    struct ProjectileHoming
    {
        enum class TargetKind : uint8_t
        {
            Party,
            Actor,
        };

        TargetKind targetKind = TargetKind::Party;
        size_t targetActorIndex = static_cast<size_t>(-1);
        uint32_t targetActorId = 0;
        float turnRadiansPerSecond = 0.0f;
        // Seconds it homes (0: its whole flight); then it flies straight on or, with expireAfter, expires.
        float maxSeconds = 0.0f;
        bool expireAfter = false;
        // Its speed when it was attached (kept while it turns).
        float speed = 0.0f;
        float elapsedSeconds = 0.0f;
        // The target is gone (dead or removed): it flies straight on.
        bool lost = false;
        // Homes only while the target's direction, seen from above, turns away from its flight slower than this
        // many radians a second, tested again each step: a faster sidestep leaves it flying straight on until its
        // line crosses the target again (0: no lock). MAW's monster missiles (FSPS-2-10), frame-rate independent.
        float lockRadiansPerSecond = 0.0f;
    };

    struct ProjectileState
    {
        enum class SourceKind
        {
            Actor,
            Event,
            Party,
        };

        uint32_t projectileId = 0;
        SourceKind sourceKind = SourceKind::Actor;
        uint32_t sourceId = 0;
        uint32_t sourcePartyMemberIndex = 0;
        int16_t sourceMonsterId = 0;
        bool fromSummonedMonster = false;
        MonsterAttackAbility ability = MonsterAttackAbility::Attack1;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t impactObjectDescriptionId = 0;
        uint16_t objectFlags = 0;
        GameplayProjectileVisualMode visualMode = GameplayProjectileVisualMode::SpriteBillboard;
        uint16_t radius = 0;
        uint16_t height = 0;
        int spellId = 0;
        int effectSoundId = 0;
        uint32_t impactSoundIdOverride = 0;
        uint32_t skillLevel = 0;
        uint32_t skillMastery = 0;
        std::string objectName;
        std::string objectSpriteName;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceZ = 0.0f;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float velocityX = 0.0f;
        float velocityY = 0.0f;
        float velocityZ = 0.0f;
        int damage = 0;
        int attackBonus = 0;
        CombatDamageType damageType = CombatDamageType::Physical;
        // Set for party attacks (CharacterAttackResult::shieldTier); otherwise the tier follows from the spell and
        // damage type (projectileShieldTier). Saved from save version 135.
        std::optional<ShieldAttackTier> shieldTier;
        // What the party weapon's tech skill adds to its shield hit (CharacterAttackResult::shieldModifiers); not
        // saved.
        ShieldHitModifiers shieldModifiers;
        // Resisted by the lower of the monster's physical and fire resistance (MAW's fire arrows); not saved.
        bool weakerOfPhysicalAndFire = false;
        // The radius its damage reaches around the impact when it is not the spell's (Carnage arrows); saved.
        float explosionRadius = 0.0f;
        // A party missile or spell whose damage was a critical hit, for the status line and combat log where it
        // lands; not saved.
        bool critical = false;
        // An event's missile (evt.FireMissile): it passes the party, whose damage the event deals itself, and bursts
        // at its target when its flight time ends unless it strikes something first; saved.
        bool eventMissile = false;
        float targetX = 0.0f;
        float targetY = 0.0f;
        float targetZ = 0.0f;
        bool useActorHitChance = false;
        bool turnBasedPendingAction = false;
        std::optional<ProjectileHoming> homing;
        uint32_t timeSinceCreatedTicks = 0;
        float lifetimeTickAccumulator = 0.0f;
        uint32_t lifetimeTicks = 0;
        int16_t sectorId = -1;
        bool isSettled = false;
        bool isExpired = false;
    };

    struct ProjectileImpactState
    {
        uint32_t effectId = 0;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t sourceObjectFlags = 0;
        int sourceSpellId = 0;
        // Presentation only (per-monster impact visuals); not saved, so a loaded impact shows the recipe's own.
        int16_t sourceMonsterId = 0;
        // Presentation only, not saved: the unit direction the projectile flew when it struck, zero when unknown.
        float flightDirectionX = 0.0f;
        float flightDirectionY = 0.0f;
        float flightDirectionZ = 0.0f;
        std::string objectName;
        std::string objectSpriteName;
        std::string sourceObjectName;
        std::string sourceObjectSpriteName;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        uint32_t timeSinceCreatedTicks = 0;
        float lifetimeTickAccumulator = 0.0f;
        uint32_t lifetimeTicks = 0;
        int16_t sectorId = -1;
        size_t targetActorIndex = static_cast<size_t>(-1);
        bool freezeAnimation = false;
        bool isExpired = false;
    };

    struct ProjectileDefinition
    {
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t impactObjectDescriptionId = 0;
        uint16_t objectFlags = 0;
        GameplayProjectileVisualMode visualMode = GameplayProjectileVisualMode::SpriteBillboard;
        uint16_t radius = 0;
        uint16_t height = 0;
        int spellId = 0;
        int effectSoundId = 0;
        uint32_t lifetimeTicks = 0;
        float speed = 0.0f;
        std::string objectName;
        std::string objectSpriteName;
    };

    struct ProjectileSpawnRequest
    {
        ProjectileState::SourceKind sourceKind = ProjectileState::SourceKind::Actor;
        uint32_t sourceId = 0;
        uint32_t sourcePartyMemberIndex = 0;
        int16_t sourceMonsterId = 0;
        bool fromSummonedMonster = false;
        MonsterAttackAbility ability = MonsterAttackAbility::Attack1;
        ProjectileDefinition definition;
        uint32_t skillLevel = 0;
        uint32_t skillMastery = 0;
        int damage = 0;
        int attackBonus = 0;
        CombatDamageType damageType = CombatDamageType::Physical;
        std::optional<ShieldAttackTier> shieldTier;
        // What the party weapon's tech skill adds to its shield hit (CharacterAttackResult::shieldModifiers); not
        // saved.
        ShieldHitModifiers shieldModifiers;
        // Resisted by the lower of the monster's physical and fire resistance (MAW's fire arrows); not saved.
        bool weakerOfPhysicalAndFire = false;
        // The radius its damage reaches around the impact when it is not the spell's (Carnage arrows); not saved.
        float explosionRadius = 0.0f;
        // Its damage was a critical hit (ProjectileState::critical).
        bool critical = false;
        // An event's missile (ProjectileState::eventMissile), reaching its target in flightSeconds (0: at the
        // object's speed).
        bool eventMissile = false;
        float flightSeconds = 0.0f;
        bool useActorHitChance = false;
        bool turnBasedPendingAction = false;
        uint32_t impactSoundIdOverride = 0;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceZ = 0.0f;
        float targetX = 0.0f;
        float targetY = 0.0f;
        float targetZ = 0.0f;
        float spawnForwardOffset = 0.0f;
        int16_t sectorId = -1;
        bool allowInstantImpact = false;
    };

    struct ProjectileSpawnResult
    {
        enum class Kind
        {
            FailedZeroDistance,
            SpawnedProjectile,
            InstantImpact,
        };

        Kind kind = Kind::FailedZeroDistance;
        ProjectileState projectile;
        float directionX = 0.0f;
        float directionY = 0.0f;
        float directionZ = 0.0f;
        float speed = 0.0f;
    };

    struct ProjectileImpactVisualDefinition
    {
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        int16_t objectHeight = 0;
        uint32_t lifetimeTicks = 0;
        bool hasVisual = false;
        bool centerAnchored = false;
        std::string objectName;
        std::string objectSpriteName;
    };

    struct ProjectileImpactSpawnResult
    {
        bool spawned = false;
        const ProjectileImpactState *pImpact = nullptr;
    };

    struct Snapshot
    {
        uint32_t nextProjectileId = 1;
        uint32_t nextProjectileImpactId = 1;
        uint32_t nextFireSpikeTrapId = 1;
        std::vector<ProjectileState> projectiles;
        std::vector<ProjectileImpactState> projectileImpacts;
    };

    struct ProjectileMotionSegment
    {
        float startX = 0.0f;
        float startY = 0.0f;
        float startZ = 0.0f;
        float endX = 0.0f;
        float endY = 0.0f;
        float endZ = 0.0f;
    };

    struct ProjectileBounceSurfaceFacts
    {
        bool canBounce = false;
        bool requiresDownwardVelocity = false;
        float normalX = 0.0f;
        float normalY = 0.0f;
        float normalZ = 1.0f;
    };

    struct ProjectileAudioRequest
    {
        uint32_t soundId = 0;
        uint32_t sourceId = 0;
        std::string reason;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        bool positional = true;
    };

    struct ProjectileSpawnEffects
    {
        bool accepted = false;
        bool spawnInstantImpact = false;
        bool playReleaseAudio = false;
        bool logSpawn = false;
        float impactX = 0.0f;
        float impactY = 0.0f;
        float impactZ = 0.0f;
        std::optional<ProjectileAudioRequest> releaseAudioRequest;
    };

    struct AreaSpellProjectileShot
    {
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceHeightOffset = 0.0f;
        float targetX = 0.0f;
        float targetY = 0.0f;
        float targetZ = 0.0f;
    };

    struct MonsterProjectileDamageProfile
    {
        int diceRolls = 0;
        int diceSides = 0;
        int bonus = 0;
    };

    struct MonsterSpellDamageProfile
    {
        int baseDamage = 0;
        int diceSides = 0;
        uint32_t skillLevel = 0;
        SkillMastery skillMastery = SkillMastery::None;
    };

    struct ProjectilePartyImpactDamageInput
    {
        ProjectileState::SourceKind sourceKind = ProjectileState::SourceKind::Actor;
        bool eventSource = false;
        int projectileDamage = 0;
        int spellId = 0;
        uint32_t skillLevel = 0;
        bool hasMonsterFacts = false;
        int monsterLevel = 0;
        MonsterAttackAbility monsterAbility = MonsterAttackAbility::Attack1;
        MonsterProjectileDamageProfile attack1Damage;
        MonsterProjectileDamageProfile attack2Damage;
        MonsterSpellDamageProfile spell1Damage;
        MonsterSpellDamageProfile spell2Damage;
    };

    struct ProjectileAreaImpactActorFacts
    {
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        uint16_t radius = 0;
        uint16_t height = 0;
        bool unavailableForCombat = false;
        bool friendlyToProjectileSource = false;
        bool directImpactActor = false;
    };

    struct ProjectileAreaImpactInput
    {
        float impactX = 0.0f;
        float impactY = 0.0f;
        float impactZ = 0.0f;
        float impactRadius = 0.0f;
        float partyX = 0.0f;
        float partyY = 0.0f;
        float partyZ = 0.0f;
        float partyCollisionRadius = 0.0f;
        float partyCollisionHeight = 0.0f;
        bool canHitParty = true;
        int nonPartyProjectileDamage = 0;
        std::vector<ProjectileAreaImpactActorFacts> actors;
    };

    struct ProjectileAreaImpactActorHit
    {
        size_t actorIndex = 0;
        int damage = 0;
    };

    struct ProjectileAreaImpact
    {
        bool hitParty = false;
        int partyDamage = 0;
        std::vector<ProjectileAreaImpactActorHit> actorHits;
    };

    struct ProjectileDirectActorImpactInput
    {
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        int targetArmorClass = 0;
        int damageMultiplier = 1;
        bool halfIncomingMissileDamage = false;
        float targetDistance = 0.0f;
        int nonPartyProjectileDamage = 0;
        // The rules a party missile's hit is rolled by (Standard when null), and what they know of the target.
        const CombatRules *pCombatRules = nullptr;
        ActorRulesetFacts targetFacts;
        int partyCount = 1;
        // The party member who fired a party missile, while in the party.
        const Character *pShooter = nullptr;
        // The target's monster id (a world enchantment's bonus against its monsters).
        int targetMonsterId = 0;
    };

    struct ProjectileDirectActorImpact
    {
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        int damage = 0;
        bool hit = true;
        bool applyPartyProjectileDamage = false;
        bool applyNonPartyProjectileDamage = false;
        bool queuePartyProjectileActorEvent = false;
    };

    enum class ProjectileFrameCollisionKind
    {
        None,
        Party,
        Actor,
        World,
    };

    struct ProjectileFrameCollisionFacts
    {
        ProjectileFrameCollisionKind kind = ProjectileFrameCollisionKind::None;
        GameplayWorldPoint point;
        std::string colliderName;
        size_t worldFaceIndex = static_cast<size_t>(-1);
        size_t actorIndex = static_cast<size_t>(-1);
        uint32_t actorId = 0;
        int targetArmorClass = 0;
        int damageMultiplier = 1;
        bool halfIncomingMissileDamage = false;
        float targetDistance = 0.0f;
        const CombatRules *pCombatRules = nullptr;
        ActorRulesetFacts targetFacts;
        int partyCount = 1;
        // The party member who fired a party missile, while in the party.
        const Character *pShooter = nullptr;
        // The target's monster id (ProjectileDirectActorImpactInput::targetMonsterId).
        int targetMonsterId = 0;
        bool waterTerrainImpact = false;
        ProjectileBounceSurfaceFacts bounceSurface;
    };

    struct ProjectileFrameBounceResult
    {
        GameplayWorldPoint point;
        float normalX = 0.0f;
        float normalY = 0.0f;
        float normalZ = 1.0f;
        float bounceFactor = 0.0f;
        float stopVelocity = 0.0f;
        float groundDamping = 0.0f;
    };

    enum class ProjectileFrameFxKind
    {
        ProjectileImpact,
        WaterSplash,
    };

    struct ProjectileFrameFxRequest
    {
        ProjectileFrameFxKind kind = ProjectileFrameFxKind::ProjectileImpact;
        GameplayWorldPoint point;
        bool centerVertically = false;
    };

    struct ProjectileFrameAreaImpactResult
    {
        GameplayWorldPoint point;
        float radius = 0.0f;
        bool logHits = false;
        ProjectileAreaImpact impact;
    };

    // A sphere that stops projectiles crossing into it from outside (an actor behaviour's ward). Projectiles that
    // start inside, such as the owner's own, pass.
    struct ProjectileWardFacts
    {
        size_t ownerActorIndex = static_cast<size_t>(-1);
        uint32_t ownerActorId = 0;
        GameplayWorldPoint center;
        float radius = 0.0f;
        std::string wardId;
    };

    struct ProjectileWardBlock
    {
        size_t ownerActorIndex = static_cast<size_t>(-1);
        uint32_t ownerActorId = 0;
        std::string wardId;
        GameplayWorldPoint point;
    };

    struct ProjectileFrameFacts
    {
        float deltaSeconds = 0.0f;
        float gravity = 0.0f;
        float bounceFactor = 0.0f;
        float bounceStopVelocity = 0.0f;
        float groundDamping = 0.0f;

        ProjectileMotionSegment motion;

        bool hasCollision = false;
        ProjectileFrameCollisionFacts collision;

        GameplayWorldPoint partyPosition;
        float partyCollisionRadius = 0.0f;
        float partyCollisionHeight = 0.0f;
        bool canHitParty = true;
        // Turn-based combat is on: a party shot the queue waits on vanishes once far from the party.
        bool turnBasedActive = false;
        int nonPartyProjectileDamage = 0;

        std::vector<ProjectileAreaImpactActorFacts> areaActors;
        const std::vector<ProjectileWardFacts> *pWards = nullptr;
    };

    struct ProjectileFrameResult
    {
        ProjectileMotionSegment motion;
        bool applyMotionEnd = false;
        bool expireProjectile = false;
        bool logCollision = false;
        bool logLifetimeExpiry = false;

        std::optional<ProjectileFrameBounceResult> bounce;
        std::optional<int> directPartyDamage;
        std::optional<ProjectileDirectActorImpact> directActorImpact;
        std::optional<ProjectileFrameAreaImpactResult> areaImpact;
        std::optional<ProjectileFrameFxRequest> fxRequest;
        std::optional<ProjectileAudioRequest> audioRequest;
        std::optional<GameplayWorldPoint> deathBlossomFalloutPoint;
        std::vector<ProjectileSpawnRequest> spawnedProjectiles;
        std::optional<ProjectileWardBlock> wardBlock;
        // Where a projectile that hit something ends: the hit point, not its last stepped position.
        std::optional<GameplayWorldPoint> endPoint;
    };

    // How a homing projectile ended (recentHomingEnds): what it hit, where, and whether it was still homing.
    struct HomingProjectileEnd
    {
        enum class Hit
        {
            Party,
            Actor,
            World,
            Ward,
            Expired,
        };

        uint32_t projectileId = 0;
        int16_t sourceMonsterId = 0;
        Hit hit = Hit::Expired;
        bool stillHoming = false;
        GameplayWorldPoint point;
    };

    struct ProjectileActorRelationFacts
    {
        bool eventSource = false;
        bool targetHostileToParty = false;
        bool targetPartyControlled = false;
        bool sourceMonsterKnown = false;
        bool sourceMonsterFriendlyToTarget = false;
    };

    struct ProjectileCollisionActorFacts
    {
        uint32_t actorId = 0;
        bool dead = false;
        bool unavailableForCombat = false;
        bool friendlyToProjectileSource = false;
    };

    struct FireSpikeTrapActorFacts
    {
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        uint16_t radius = 0;
        uint16_t height = 0;
        bool unavailableForCombat = false;
        bool hostileToParty = false;
        bool friendlyToTrapSource = false;
    };

    struct FireSpikeActiveTrapFacts
    {
        ProjectileState::SourceKind sourceKind = ProjectileState::SourceKind::Party;
        uint32_t sourcePartyMemberIndex = 0;
        bool expired = false;
    };

    struct FireSpikeTrapSpawnLimitInput
    {
        ProjectileState::SourceKind sourceKind = ProjectileState::SourceKind::Party;
        uint32_t sourcePartyMemberIndex = 0;
        uint32_t skillMastery = 0;
        std::vector<FireSpikeActiveTrapFacts> traps;
    };

    struct FireSpikeTrapSpawnResult
    {
        uint32_t activeLimit = 0;
        uint32_t activeCount = 0;
        uint32_t trapId = 0;
        bool accepted = false;
    };

    struct FireSpikeTrapTriggerInput
    {
        ProjectileState::SourceKind sourceKind = ProjectileState::SourceKind::Party;
        uint32_t trapId = 0;
        uint16_t trapRadius = 0;
        uint32_t skillLevel = 0;
        uint32_t skillMastery = 0;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        std::vector<FireSpikeTrapActorFacts> actors;
    };

    struct FireSpikeTrapTriggerResult
    {
        bool triggered = false;
        bool applyActorImpact = false;
        bool spawnImpactVisual = false;
        bool expireTrap = false;
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        int damage = 0;
    };

    struct FireSpikeTrapImpactProjectileInput
    {
        ProjectileState::SourceKind sourceKind = ProjectileState::SourceKind::Party;
        uint32_t sourceId = 0;
        uint32_t sourcePartyMemberIndex = 0;
        int16_t sourceMonsterId = 0;
        bool fromSummonedMonster = false;
        MonsterAttackAbility ability = MonsterAttackAbility::Attack1;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t impactObjectDescriptionId = 0;
        uint16_t objectFlags = 0;
        uint16_t radius = 0;
        uint16_t height = 0;
        int spellId = 0;
        int effectSoundId = 0;
        uint32_t skillLevel = 0;
        uint32_t skillMastery = 0;
        std::string objectName;
        std::string objectSpriteName;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        int damage = 0;
    };

    void clear();
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    void clearActiveProjectiles();

    uint32_t nextProjectileId() const;
    uint32_t allocateProjectileId();
    uint32_t allocateProjectileImpactId();
    static uint32_t ticksFromDeltaSeconds(float deltaSeconds);
    // What the projectile is to an energy shield: its party attack tier, else a spell, else by damage type.
    static ShieldAttackTier projectileShieldTier(const ProjectileState &projectile);
    // What the party's projectile adds to its shield hit: its weapon's modifiers, or its caster's Lattice Resonator
    // for a spell.
    static ShieldHitModifiers partyShieldModifiers(const ProjectileState &projectile, const Party *pParty);
    ProjectileSpawnResult spawnProjectile(const ProjectileSpawnRequest &request);
    // A party spell that leaps on from the monster it hit (MAW's Chain Lightning): a copy, one mastery lower, from that
    // monster to the nearest other living hostile one within 768; nothing when the rules stop it or none is near.
    std::optional<ProjectileSpawnRequest> buildChainSpawnRequest(
        const ProjectileState &projectile,
        const CombatRules &rules,
        const IGameplayWorldRuntime &world,
        size_t struckActorIndex) const;
    ProjectileSpawnEffects buildProjectileSpawnEffects(
        const ProjectileSpawnResult &result) const;
    ProjectileSpawnEffects buildProjectileSpawnEffects(
        const ProjectileSpawnResult &result,
        bool playReleaseAudio) const;
    std::vector<AreaSpellProjectileShot> buildMeteorShowerProjectileShots(
        uint32_t skillMastery,
        uint32_t nextProjectileId,
        float targetX,
        float targetY,
        float targetZ) const;
    std::vector<AreaSpellProjectileShot> buildStarburstProjectileShots(
        uint32_t nextProjectileId,
        float targetX,
        float targetY,
        float targetZ) const;
    std::vector<ProjectileState> &projectiles();
    const std::vector<ProjectileState> &projectiles() const;
    std::vector<ProjectileImpactState> &projectileImpacts();
    const std::vector<ProjectileImpactState> &projectileImpacts() const;
    static GameplayProjectileVisualMode monsterProjectileVisualModeForObjectId(int objectId);
    static bool projectileVisualModeUsesDedicatedFxImpact(const ProjectileState &projectile);

    void advanceProjectileImpactLifetimes(float deltaSeconds);
    void updateProjectileImpactPresentation(float deltaSeconds);
    bool advanceProjectileLifetime(ProjectileState &projectile, float deltaSeconds) const;
    // Whether a party shot still holds up the turn-based queue: while it flies, for at most two seconds, so a miss into
    // the sky or a stray Spark does not keep the turn for its whole lifetime. It flies on and can still hit.
    static bool holdsTurnBasedQueue(const ProjectileState &projectile);
    ProjectileMotionSegment advanceProjectileMotion(
        ProjectileState &projectile,
        float deltaSeconds,
        float gravity) const;
    ProjectileFrameResult updateProjectileFrame(
        ProjectileState &projectile,
        const ProjectileFrameFacts &facts) const;
    // Gives every live projectile of actor sourceActorId spawned since firstProjectileId (nextProjectileId() before
    // the spawn) this homing, at its current speed; returns how many.
    size_t attachHoming(uint32_t firstProjectileId, uint32_t sourceActorId, const ProjectileHoming &homing);
    // The same for the missiles party member sourcePartyMemberIndex fired since firstProjectileId.
    size_t attachPartyHoming(
        uint32_t firstProjectileId,
        uint32_t sourcePartyMemberIndex,
        const ProjectileHoming &homing);
    // Turns the velocity toward target by at most maxTurnRadians and sets its length to speed. False when the
    // velocity is zero or the target lies at the position.
    static bool steerVelocityToward(
        float &velocityX,
        float &velocityY,
        float &velocityZ,
        const GameplayWorldPoint &position,
        const GameplayWorldPoint &target,
        float speed,
        float maxTurnRadians);
    // Records how a homing projectile ended by this frame result (scenario checks, debug); others are not recorded.
    void recordHomingEnd(const ProjectileState &projectile, const ProjectileFrameResult &result);
    // The last 32 homing ends, oldest first.
    const std::vector<HomingProjectileEnd> &recentHomingEnds() const
    {
        return m_recentHomingEnds;
    }
    // One step of a homing projectile before its motion: steers toward pTarget, or with no target (null) stops
    // homing and flies straight on. True when its homing time ran out and it is to expire (expireAfter).
    static bool steerHomingProjectile(
        ProjectileState &projectile,
        const GameplayWorldPoint *pTarget,
        float deltaSeconds);
    static std::optional<ProjectileWardBlock> findProjectileWardBlock(
        const ProjectileState &projectile,
        const ProjectileMotionSegment &motion,
        const std::vector<ProjectileWardFacts> &wards,
        float maximumSegmentFraction);
    void applyProjectileMotionEnd(
        ProjectileState &projectile,
        const ProjectileMotionSegment &motionSegment) const;
    void applyProjectileBounce(
        ProjectileState &projectile,
        float impactX,
        float impactY,
        float impactZ,
        float normalX,
        float normalY,
        float normalZ,
        float bounceFactor,
        float stopVelocity,
        float groundDamping) const;
    void settleProjectile(ProjectileState &projectile) const;
    std::vector<ProjectileSpawnRequest> buildDeathBlossomFalloutSpawnRequests(
        const ProjectileState &projectile,
        const ProjectileDefinition &shardDefinition,
        float x,
        float y,
        float z) const;
    std::vector<ProjectileSpawnResult> spawnDeathBlossomFalloutProjectiles(
        const ProjectileState &projectile,
        const ProjectileDefinition &shardDefinition,
        float x,
        float y,
        float z);
    bool shouldSpawnProjectileImpactVisual(
        const ProjectileState &projectile,
        const ProjectileImpactVisualDefinition &definition) const;
    ProjectileImpactVisualDefinition buildProjectileImpactVisualDefinition(
        uint16_t objectDescriptionId,
        const ObjectEntry &objectEntry,
        const SpriteFrameTable *pSpriteFrameTable) const;
    std::optional<ProjectileImpactVisualDefinition> buildProjectileImpactVisualDefinition(
        uint16_t objectDescriptionId,
        const ObjectTable *pObjectTable,
        const SpriteFrameTable *pSpriteFrameTable) const;
    std::optional<ProjectileImpactVisualDefinition> buildWaterSplashImpactVisualDefinition(
        const ObjectTable *pObjectTable,
        const SpriteFrameTable *pSpriteFrameTable) const;
    ProjectileImpactSpawnResult spawnProjectileImpactVisual(
        const ProjectileState &projectile,
        const ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z,
        bool centerVertically,
        size_t targetActorIndex = static_cast<size_t>(-1));
    ProjectileImpactSpawnResult spawnWaterSplashImpactVisual(
        const ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z);
    // targetActorIndex: the actor the spell struck, so an enhanced impact can follow it.
    ProjectileImpactSpawnResult spawnImmediateSpellImpactVisual(
        const ProjectileImpactVisualDefinition &definition,
        int sourceSpellId,
        const std::string &sourceObjectName,
        const std::string &sourceObjectSpriteName,
        float x,
        float y,
        float z,
        bool centerVertically,
        bool freezeAnimation,
        size_t targetActorIndex = static_cast<size_t>(-1));
    std::optional<ProjectileAudioRequest> buildProjectileReleaseAudioRequest(
        const ProjectileState &projectile,
        float x,
        float y,
        float z) const;
    std::optional<ProjectileAudioRequest> buildProjectileImpactAudioRequest(
        const ProjectileState &projectile,
        float x,
        float y,
        float z) const;
    std::optional<ProjectileAudioRequest> buildWaterSplashAudioRequest(float x, float y, float z) const;
    int resolveProjectilePartyImpactDamage(const ProjectilePartyImpactDamageInput &input) const;
    // A party spell the world rolls itself (Fire Spike trap, Armageddon): the rules' roll (MAW rolls the spell), else
    // `trapRoll`, the world's own.
    static int partyWorldSpellDamage(
        const Party *pParty,
        const SpellTable *pSpellTable,
        uint32_t sourcePartyMemberIndex,
        int spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int trapRoll);
    int resolvePartyProjectileDamageMultiplier(
        const ProjectileState &projectile,
        const Character *pSourceMember,
        const ItemTable *pItemTable,
        const SpecialItemEnchantTable *pSpecialItemEnchantTable,
        uint32_t targetMonsterKindFlags,
        const CombatRules &rules) const;
    ProjectileAreaImpact buildProjectileAreaImpact(
        const ProjectileState &projectile,
        const ProjectileAreaImpactInput &input) const;
    ProjectileDirectActorImpact buildProjectileDirectActorImpact(
        const ProjectileState &projectile,
        const ProjectileDirectActorImpactInput &input) const;
    void expireProjectile(
        ProjectileState &projectile,
        const std::optional<GameplayWorldPoint> &endPoint = std::nullopt);
    bool isProjectileSourceFriendlyToActor(
        const ProjectileState &projectile,
        const ProjectileActorRelationFacts &facts) const;
    static float directActorProjectileHitRadius(
        const ProjectileState &projectile,
        float actorRadius);
    bool canProjectileCollideWithParty(const ProjectileState &projectile) const;
    bool canProjectileCollideWithActor(
        const ProjectileState &projectile,
        const ProjectileCollisionActorFacts &actorFacts) const;
    FireSpikeTrapSpawnResult buildFireSpikeTrapSpawn(const FireSpikeTrapSpawnLimitInput &input);
    uint32_t advanceFireSpikeTrapLifetime(
        uint32_t timeSinceCreatedTicks,
        float deltaSeconds) const;
    FireSpikeTrapTriggerResult buildFireSpikeTrapTrigger(
        const FireSpikeTrapTriggerInput &input) const;
    ProjectileState buildFireSpikeTrapImpactProjectile(
        const FireSpikeTrapImpactProjectileInput &input);
    void eraseExpiredProjectiles();
    void eraseExpiredProjectileImpacts();
    void eraseExpiredProjectilesAndImpacts();

    size_t projectileCount() const;
    const ProjectileState *projectileState(size_t projectileIndex) const;
    size_t projectileImpactCount() const;
    const ProjectileImpactState *projectileImpactState(size_t effectIndex) const;

    void collectProjectilePresentationState(
        std::vector<GameplayProjectilePresentationState> &projectiles,
        std::vector<GameplayProjectileImpactPresentationState> &impacts) const;
    // Projectiles that ended since the last call, with their final positions.
    std::vector<GameplayProjectileEndPresentationState> takeEndedProjectiles();

    static int16_t waterSplashObjectId();
    // How far a spell's impact damage reaches (Fireball's also sets a Carnage arrow's); 0 for a single target.
    static float spellImpactDamageRadius(uint32_t spellId);
    // Who sent a party projectile, for the rules' damage to the monster it struck (no attacker for any other).
    static PartyMissileSource partyMissileSource(
        const ProjectileState &projectile,
        const Party *pParty,
        const ItemTable *pItemTable,
        const MonsterTable::MonsterStatsEntry &targetStats,
        int targetCurrentHp);
    // A monster's every resistance, for the rules that pick among them.
    static MonsterDamageResistances monsterDamageResistances(const MonsterTable::MonsterStatsEntry &stats);

private:
    static uint32_t fireSpikeLimitForMastery(uint32_t skillMastery);
    std::optional<int> buildProjectileDirectPartyDamage(
        const ProjectileState &projectile,
        int nonPartyProjectileDamage) const;
    const ProjectileImpactState &addProjectileImpact(ProjectileImpactState impact);
    uint32_t allocateFireSpikeTrapId();

    size_t attachHomingWhere(
        uint32_t firstProjectileId,
        const ProjectileHoming &homing,
        const std::function<bool(const ProjectileState &)> &fromSource);

    uint32_t m_nextProjectileId = 1;
    uint32_t m_nextProjectileImpactId = 1;
    uint32_t m_nextFireSpikeTrapId = 1;
    std::vector<ProjectileState> m_projectiles;
    std::vector<ProjectileImpactState> m_projectileImpacts;
    std::vector<GameplayProjectileEndPresentationState> m_endedProjectiles;
    std::vector<HomingProjectileEnd> m_recentHomingEnds;
};
}
