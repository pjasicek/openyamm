#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
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
        uint16_t radius = 0;
        uint16_t height = 0;
        int spellId = 0;
        int effectSoundId = 0;
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
        bool useActorHitChance = false;
        uint32_t timeSinceCreatedTicks = 0;
        uint32_t lifetimeTicks = 0;
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
        std::string objectName;
        std::string objectSpriteName;
        std::string sourceObjectName;
        std::string sourceObjectSpriteName;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        uint32_t timeSinceCreatedTicks = 0;
        uint32_t lifetimeTicks = 0;
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
        bool useActorHitChance = false;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceZ = 0.0f;
        float targetX = 0.0f;
        float targetY = 0.0f;
        float targetZ = 0.0f;
        float spawnForwardOffset = 0.0f;
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

    struct ProjectileImpactRequest
    {
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t sourceObjectFlags = 0;
        int sourceSpellId = 0;
        std::string objectName;
        std::string objectSpriteName;
        std::string sourceObjectName;
        std::string sourceObjectSpriteName;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        uint32_t lifetimeTicks = 0;
        bool freezeAnimation = false;
    };

    struct ProjectileImpactVisualDefinition
    {
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        int16_t objectHeight = 0;
        uint32_t lifetimeTicks = 0;
        bool hasVisual = false;
        std::string objectName;
        std::string objectSpriteName;
    };

    struct ProjectileImpactPresentationResult
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

    enum class ProjectileFrameAdvanceKind
    {
        LifetimeExpired,
        Moving,
    };

    enum class ProjectileImpactReason
    {
        Collision,
        LifetimeExpired,
    };

    struct ProjectileImpactDecision
    {
        bool spawnDeathBlossomFallout = false;
        bool applyAreaDamage = false;
        bool spawnProjectileImpact = false;
        float impactRadius = 0.0f;
    };

    struct ProjectileBounceSurfaceFacts
    {
        bool canBounce = false;
        bool requiresDownwardVelocity = false;
        float normalX = 0.0f;
        float normalY = 0.0f;
        float normalZ = 1.0f;
    };

    struct ProjectileBounceDecision
    {
        bool shouldBounce = false;
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

    enum class ProjectileSpawnPresentationCommand
    {
        SpawnInstantImpact,
        PlayReleaseAudio,
        LogSpawn,
    };

    struct ProjectileSpawnPresentationDecision
    {
        bool accepted = false;
        float impactX = 0.0f;
        float impactY = 0.0f;
        float impactZ = 0.0f;
        std::optional<ProjectileAudioRequest> releaseAudioRequest;
        std::vector<ProjectileSpawnPresentationCommand> commands;
    };

    struct ProjectileSpawnPresentationOptions
    {
        bool playReleaseAudio = true;
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

    struct PartyProjectileActorImpactInput
    {
        uint32_t projectileId = 0;
        uint32_t targetActorId = 0;
        int damage = 0;
        int attackBonus = 0;
        int targetArmorClass = 0;
        int damageMultiplier = 1;
        float targetDistance = 0.0f;
        bool useActorHitChance = false;
    };

    struct MonsterProjectileDamageProfile
    {
        int diceRolls = 0;
        int diceSides = 0;
        int bonus = 0;
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
    };

    struct PartyProjectileActorImpactDecision
    {
        int damage = 0;
        bool hit = true;
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

    struct ProjectileAreaImpactActorDecision
    {
        size_t actorIndex = 0;
        int damage = 0;
    };

    struct ProjectileAreaImpactDecision
    {
        bool hitParty = false;
        int partyDamage = 0;
        std::vector<ProjectileAreaImpactActorDecision> actorHits;
    };

    struct ProjectileDirectPartyImpactInput
    {
        int nonPartyProjectileDamage = 0;
    };

    struct ProjectileDirectPartyImpactDecision
    {
        bool hitParty = false;
        int damage = 0;
    };

    struct ProjectileDirectActorImpactInput
    {
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        int targetArmorClass = 0;
        int damageMultiplier = 1;
        float targetDistance = 0.0f;
        int nonPartyProjectileDamage = 0;
    };

    struct ProjectileDirectActorImpactDecision
    {
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        int damage = 0;
        bool hit = true;
        bool applyPartyProjectileDamage = false;
        bool applyNonPartyProjectileDamage = false;
        bool queuePartyProjectileActorEvent = false;
    };

    struct ProjectileCollisionOutcomeInput
    {
        bool directPartyImpact = false;
        bool directActorImpact = false;
        size_t directActorIndex = 0;
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

    struct ProjectileCollisionOutcomeDecision
    {
        bool spawnDeathBlossomFallout = false;
        bool stopAfterDeathBlossomFallout = false;
        bool applyDirectPartyImpact = false;
        bool applyDirectActorImpact = false;
        bool applyAreaDamage = false;
        bool areaCanHitParty = true;
        float impactRadius = 0.0f;
        bool hasDirectActorIndex = false;
        size_t directActorIndex = 0;
    };

    enum class ProjectileLifetimeExpiryCommand
    {
        SpawnDeathBlossomFallout,
        ApplyAreaDamage,
        SpawnProjectileImpact,
        ExpireProjectile,
    };

    struct ProjectileLifetimeExpiryDecision
    {
        float impactRadius = 0.0f;
        std::vector<ProjectileLifetimeExpiryCommand> commands;
    };

    struct ProjectileCollisionPresentationInput
    {
        float impactX = 0.0f;
        float impactY = 0.0f;
        float impactZ = 0.0f;
        float projectileX = 0.0f;
        float projectileY = 0.0f;
        bool waterTerrainImpact = false;
        bool actorImpact = false;
    };

    struct ProjectileCollisionPresentationDecision
    {
        bool spawnWaterSplash = false;
        bool spawnProjectileImpact = false;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        bool centerProjectileImpactVertically = false;
    };

    enum class ProjectileCollisionResolutionCommand
    {
        SpawnDeathBlossomFallout,
        ApplyDirectPartyImpact,
        ApplyDirectActorImpact,
        ApplyAreaDamage,
        LogCollision,
        SpawnWaterSplash,
        SpawnProjectileImpact,
        ExpireProjectile,
    };

    struct ProjectileCollisionResolutionDecision
    {
        ProjectileCollisionOutcomeDecision outcome;
        ProjectileCollisionPresentationDecision presentation;
        std::vector<ProjectileCollisionResolutionCommand> commands;
    };

    enum class ProjectileCollisionFrameCommand
    {
        ApplyBounce,
        ApplyResolution,
    };

    struct ProjectileCollisionFrameDecision
    {
        ProjectileBounceDecision bounce;
        ProjectileCollisionResolutionDecision resolution;
        std::vector<ProjectileCollisionFrameCommand> commands;
    };

    enum class ProjectileUpdateFrameCommand
    {
        ApplyLifetimeExpiry,
        ApplyCollisionFrame,
        ApplyMotionEnd,
    };

    struct ProjectileFrameAdvanceResult
    {
        ProjectileFrameAdvanceKind kind = ProjectileFrameAdvanceKind::Moving;
        ProjectileMotionSegment motionSegment;
        ProjectileImpactDecision lifetimeImpactDecision;
        ProjectileLifetimeExpiryDecision lifetimeExpiryDecision;
    };

    struct ProjectileUpdateFrameDecision
    {
        ProjectileFrameAdvanceResult frameAdvance;
        ProjectileCollisionFrameDecision collisionFrame;
        std::vector<ProjectileUpdateFrameCommand> commands;
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

    struct FireSpikeTrapSpawnLimitDecision
    {
        uint32_t activeLimit = 0;
        uint32_t activeCount = 0;
        bool canSpawn = false;
    };

    struct FireSpikeTrapSpawnDecision
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

    enum class FireSpikeTrapTriggerCommand
    {
        ApplyActorImpact,
        SpawnImpactPresentation,
        ExpireTrap,
    };

    struct FireSpikeTrapTriggerDecision
    {
        bool triggered = false;
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        int damage = 0;
        std::vector<FireSpikeTrapTriggerCommand> commands;
    };

    struct FireSpikeTrapLifetimeFrame
    {
        uint32_t timeSinceCreatedTicks = 0;
    };

    struct FireSpikeTrapImpactPresentationInput
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

    uint32_t nextProjectileId() const;
    uint32_t allocateProjectileId();
    uint32_t allocateProjectileImpactId();
    static uint32_t ticksFromDeltaSeconds(float deltaSeconds);
    ProjectileSpawnResult spawnProjectile(const ProjectileSpawnRequest &request);
    ProjectileSpawnPresentationDecision buildProjectileSpawnPresentationDecision(
        const ProjectileSpawnResult &result) const;
    ProjectileSpawnPresentationDecision buildProjectileSpawnPresentationDecision(
        const ProjectileSpawnResult &result,
        const ProjectileSpawnPresentationOptions &options) const;
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
    const ProjectileImpactState &spawnProjectileImpact(const ProjectileImpactRequest &request);

    std::vector<ProjectileState> &projectiles();
    const std::vector<ProjectileState> &projectiles() const;
    std::vector<ProjectileImpactState> &projectileImpacts();
    const std::vector<ProjectileImpactState> &projectileImpacts() const;

    void advanceProjectileImpactLifetimes(uint32_t deltaTicks);
    void updateProjectileImpactPresentation(float deltaSeconds);
    bool advanceProjectileLifetime(ProjectileState &projectile, uint32_t deltaTicks) const;
    ProjectileMotionSegment advanceProjectileMotion(
        ProjectileState &projectile,
        float deltaSeconds,
        float gravity) const;
    ProjectileFrameAdvanceResult advanceProjectileFrame(
        ProjectileState &projectile,
        float deltaSeconds,
        float gravity) const;
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
    ProjectileImpactDecision buildProjectileImpactDecision(
        const ProjectileState &projectile,
        ProjectileImpactReason reason) const;
    ProjectileBounceDecision buildProjectileBounceDecision(
        const ProjectileState &projectile,
        const ProjectileBounceSurfaceFacts &surfaceFacts,
        float stopVelocity) const;
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
    bool shouldSpawnProjectileImpactPresentation(
        const ProjectileState &projectile,
        const ProjectileImpactVisualDefinition &definition) const;
    ProjectileImpactRequest buildProjectileImpactRequest(
        const ProjectileState &projectile,
        const ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z,
        bool centerVertically) const;
    ProjectileImpactRequest buildWaterSplashImpactRequest(
        const ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z) const;
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
    ProjectileImpactPresentationResult spawnProjectileImpactPresentation(
        const ProjectileState &projectile,
        const ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z,
        bool centerVertically);
    ProjectileImpactPresentationResult spawnWaterSplashImpactPresentation(
        const ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z);
    ProjectileImpactPresentationResult spawnImmediateSpellImpactPresentation(
        const ProjectileImpactVisualDefinition &definition,
        int sourceSpellId,
        const std::string &sourceObjectName,
        const std::string &sourceObjectSpriteName,
        float x,
        float y,
        float z,
        bool centerVertically,
        bool freezeAnimation);
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
    int resolvePartyProjectileDamageMultiplier(
        const ProjectileState &projectile,
        const Character *pSourceMember,
        const ItemTable *pItemTable,
        const SpecialItemEnchantTable *pSpecialItemEnchantTable,
        const std::string &targetMonsterName,
        const std::string &targetMonsterPictureName) const;
    PartyProjectileActorImpactDecision buildPartyProjectileActorImpactDecision(
        const PartyProjectileActorImpactInput &input) const;
    ProjectileAreaImpactDecision buildProjectileAreaImpactDecision(
        const ProjectileState &projectile,
        const ProjectileAreaImpactInput &input) const;
    ProjectileDirectPartyImpactDecision buildProjectileDirectPartyImpactDecision(
        const ProjectileState &projectile,
        const ProjectileDirectPartyImpactInput &input) const;
    ProjectileDirectActorImpactDecision buildProjectileDirectActorImpactDecision(
        const ProjectileState &projectile,
        const ProjectileDirectActorImpactInput &input) const;
    ProjectileCollisionOutcomeDecision buildProjectileCollisionOutcomeDecision(
        const ProjectileImpactDecision &impactDecision,
        const ProjectileCollisionOutcomeInput &input) const;
    ProjectileLifetimeExpiryDecision buildProjectileLifetimeExpiryDecision(
        const ProjectileImpactDecision &impactDecision) const;
    void expireProjectile(ProjectileState &projectile) const;
    ProjectileCollisionPresentationDecision buildProjectileCollisionPresentationDecision(
        const ProjectileImpactDecision &impactDecision,
        const ProjectileCollisionPresentationInput &input) const;
    ProjectileCollisionResolutionDecision buildProjectileCollisionResolutionDecision(
        const ProjectileImpactDecision &impactDecision,
        const ProjectileCollisionOutcomeInput &outcomeInput,
        const ProjectileCollisionPresentationInput &presentationInput) const;
    ProjectileCollisionFrameDecision buildProjectileCollisionFrameDecision(
        const ProjectileState &projectile,
        const ProjectileBounceSurfaceFacts &bounceSurfaceFacts,
        const ProjectileCollisionOutcomeInput &outcomeInput,
        const ProjectileCollisionPresentationInput &presentationInput,
        float bounceStopVelocity) const;
    ProjectileUpdateFrameDecision buildProjectileUpdateFrameDecision(
        const ProjectileState &projectile,
        const ProjectileFrameAdvanceResult &frameAdvance,
        bool collisionHit,
        const ProjectileBounceSurfaceFacts &bounceSurfaceFacts,
        const ProjectileCollisionOutcomeInput &outcomeInput,
        const ProjectileCollisionPresentationInput &presentationInput,
        float bounceStopVelocity) const;
    bool isProjectileSourceFriendlyToActor(
        const ProjectileState &projectile,
        const ProjectileActorRelationFacts &facts) const;
    bool canProjectileCollideWithParty(const ProjectileState &projectile) const;
    bool canProjectileCollideWithActor(
        const ProjectileState &projectile,
        const ProjectileCollisionActorFacts &actorFacts) const;
    uint32_t fireSpikeLimitForMastery(uint32_t skillMastery) const;
    FireSpikeTrapSpawnLimitDecision buildFireSpikeTrapSpawnLimitDecision(
        const FireSpikeTrapSpawnLimitInput &input) const;
    FireSpikeTrapSpawnDecision buildFireSpikeTrapSpawnDecision(const FireSpikeTrapSpawnLimitInput &input);
    FireSpikeTrapLifetimeFrame advanceFireSpikeTrapLifetime(
        uint32_t timeSinceCreatedTicks,
        float deltaSeconds) const;
    FireSpikeTrapTriggerDecision buildFireSpikeTrapTriggerDecision(
        const FireSpikeTrapTriggerInput &input) const;
    ProjectileState buildFireSpikeTrapImpactPresentationProjectile(
        const FireSpikeTrapImpactPresentationInput &input);
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

    static int16_t waterSplashObjectId();

private:
    static float spellImpactDamageRadius(uint32_t spellId);
    uint32_t allocateFireSpikeTrapId();

    uint32_t m_nextProjectileId = 1;
    uint32_t m_nextProjectileImpactId = 1;
    uint32_t m_nextFireSpikeTrapId = 1;
    std::vector<ProjectileState> m_projectiles;
    std::vector<ProjectileImpactState> m_projectileImpacts;
};
}
