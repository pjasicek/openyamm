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
        bool useActorHitChance = false;
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
        CombatDamageType damageType = CombatDamageType::Physical;
        bool useActorHitChance = false;
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
        int nonPartyProjectileDamage = 0;

        std::vector<ProjectileAreaImpactActorFacts> areaActors;
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

    uint32_t nextProjectileId() const;
    uint32_t allocateProjectileId();
    uint32_t allocateProjectileImpactId();
    static uint32_t ticksFromDeltaSeconds(float deltaSeconds);
    ProjectileSpawnResult spawnProjectile(const ProjectileSpawnRequest &request);
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

    void advanceProjectileImpactLifetimes(float deltaSeconds);
    void updateProjectileImpactPresentation(float deltaSeconds);
    bool advanceProjectileLifetime(ProjectileState &projectile, float deltaSeconds) const;
    ProjectileMotionSegment advanceProjectileMotion(
        ProjectileState &projectile,
        float deltaSeconds,
        float gravity) const;
    ProjectileFrameResult updateProjectileFrame(
        ProjectileState &projectile,
        const ProjectileFrameFacts &facts) const;
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
        bool centerVertically);
    ProjectileImpactSpawnResult spawnWaterSplashImpactVisual(
        const ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z);
    ProjectileImpactSpawnResult spawnImmediateSpellImpactVisual(
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
    ProjectileAreaImpact buildProjectileAreaImpact(
        const ProjectileState &projectile,
        const ProjectileAreaImpactInput &input) const;
    ProjectileDirectActorImpact buildProjectileDirectActorImpact(
        const ProjectileState &projectile,
        const ProjectileDirectActorImpactInput &input) const;
    void expireProjectile(ProjectileState &projectile) const;
    bool isProjectileSourceFriendlyToActor(
        const ProjectileState &projectile,
        const ProjectileActorRelationFacts &facts) const;
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

    static int16_t waterSplashObjectId();

private:
    static float spellImpactDamageRadius(uint32_t spellId);
    static uint32_t fireSpikeLimitForMastery(uint32_t skillMastery);
    std::optional<int> buildProjectileDirectPartyDamage(
        const ProjectileState &projectile,
        int nonPartyProjectileDamage) const;
    const ProjectileImpactState &addProjectileImpact(ProjectileImpactState impact);
    uint32_t allocateFireSpikeTrapId();

    uint32_t m_nextProjectileId = 1;
    uint32_t m_nextProjectileImpactId = 1;
    uint32_t m_nextFireSpikeTrapId = 1;
    std::vector<ProjectileState> m_projectiles;
    std::vector<ProjectileImpactState> m_projectileImpacts;
};
}
