#include "doctest/doctest.h"

#include "game/gameplay/GameplayProjectileService.h"
#include "game/fx/FxSharedTypes.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ParticleSystem.h"
#include "game/party/SkillData.h"
#include "game/party/SpellIds.h"

using OpenYAMM::Game::GameplayProjectileService;
using OpenYAMM::Game::SkillMastery;
using OpenYAMM::Game::SpellId;
using OpenYAMM::Game::FxRecipes::ProjectileRecipe;

namespace
{
GameplayProjectileService::ProjectileState makePartyProjectile(int damage = 10)
{
    GameplayProjectileService::ProjectileState projectile = {};
    projectile.projectileId = 42;
    projectile.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Party;
    projectile.sourceId = 1;
    projectile.damage = damage;
    return projectile;
}

GameplayProjectileService::ProjectileState makeActorProjectile(uint32_t sourceActorId = 10)
{
    GameplayProjectileService::ProjectileState projectile = {};
    projectile.projectileId = 84;
    projectile.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Actor;
    projectile.sourceId = sourceActorId;
    projectile.damage = 9;
    return projectile;
}
}

TEST_CASE("projectile area impact hits party and filters actors without map runtime")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileAreaImpactInput input = {};
    input.impactX = 0.0f;
    input.impactY = 0.0f;
    input.impactZ = 64.0f;
    input.impactRadius = 128.0f;
    input.partyX = 40.0f;
    input.partyY = 0.0f;
    input.partyZ = 0.0f;
    input.partyCollisionRadius = 32.0f;
    input.partyCollisionHeight = 128.0f;
    input.canHitParty = true;

    GameplayProjectileService::ProjectileAreaImpactActorFacts hitActor = {};
    hitActor.actorIndex = 3;
    hitActor.actorId = 100;
    hitActor.x = 80.0f;
    hitActor.y = 0.0f;
    hitActor.z = 0.0f;
    hitActor.radius = 32;
    hitActor.height = 128;
    input.actors.push_back(hitActor);

    GameplayProjectileService::ProjectileAreaImpactActorFacts directActor = hitActor;
    directActor.actorIndex = 4;
    directActor.actorId = 101;
    directActor.directImpactActor = true;
    input.actors.push_back(directActor);

    GameplayProjectileService::ProjectileAreaImpactActorFacts friendlyActor = hitActor;
    friendlyActor.actorIndex = 5;
    friendlyActor.actorId = 102;
    friendlyActor.friendlyToProjectileSource = true;
    input.actors.push_back(friendlyActor);

    const GameplayProjectileService::ProjectileAreaImpact impact =
        service.buildProjectileAreaImpact(makePartyProjectile(12), input);

    CHECK(impact.hitParty);
    CHECK_EQ(impact.partyDamage, 12);
    REQUIRE_EQ(impact.actorHits.size(), 1u);
    CHECK_EQ(impact.actorHits.front().actorIndex, 3u);
    CHECK_EQ(impact.actorHits.front().damage, 12);
}

TEST_CASE("sparks projectile uses shared lightning-style fx and light recipe")
{
    const ProjectileRecipe recipe = OpenYAMM::Game::FxRecipes::classifyProjectileRecipe(
        static_cast<int>(SpellId::Sparks),
        "Sparks",
        "spell02",
        0);

    CHECK(recipe == ProjectileRecipe::Sparks);
    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe));
    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeGlowRadius(recipe) > 0.0f);
}

TEST_CASE("fireball and dragon breath impacts add full size red area pulse")
{
    const ProjectileRecipe recipes[] = {ProjectileRecipe::Fireball, ProjectileRecipe::DragonBreath};

    for (const ProjectileRecipe recipe : recipes)
    {
        OpenYAMM::Game::ParticleSystem particleSystem;
        OpenYAMM::Game::FxRecipes::ImpactSpawnContext context = {};
        context.recipe = recipe;
        context.objectName = recipe == ProjectileRecipe::Fireball ? "Fireball" : "Dragon Breath";
        context.spriteName = recipe == ProjectileRecipe::Fireball ? "fire04" : "spell97";

        OpenYAMM::Game::FxRecipes::spawnImpactParticles(particleSystem, context);

        const OpenYAMM::Game::FxParticleState *pPulse = nullptr;

        for (const OpenYAMM::Game::FxParticleState &particle : particleSystem.particles())
        {
            if (particle.motion == OpenYAMM::Game::FxParticleMotion::StaticFade
                && particle.blendMode == OpenYAMM::Game::FxParticleBlendMode::Additive
                && particle.alignment == OpenYAMM::Game::FxParticleAlignment::CameraFacing
                && particle.material == OpenYAMM::Game::FxParticleMaterial::SoftBlob
                && particle.tag == OpenYAMM::Game::FxParticleTag::Impact
                && particle.size >= 130.0f
                && particle.size < 140.0f
                && particle.endSize == particle.size)
            {
                pPulse = &particle;
                break;
            }
        }

        REQUIRE(pPulse != nullptr);
        CHECK_EQ(pPulse->startColorAbgr & 0xffu, 255u);
        CHECK_GT((pPulse->startColorAbgr >> 8) & 0xffu, 64u);
        CHECK_LT((pPulse->startColorAbgr >> 8) & 0xffu, 100u);
        CHECK_GT((pPulse->startColorAbgr >> 24) & 0xffu, 220u);
        CHECK_EQ(pPulse->endColorAbgr, pPulse->startColorAbgr);
        CHECK_GT(pPulse->fadeOutStartSeconds, 0.0f);
        CHECK_LT(pPulse->fadeOutStartSeconds, 0.01f);
        CHECK_LT(pPulse->lifetimeSeconds, 0.7f);
    }
}

TEST_CASE("projectile direct actor impact separates party and monster damage paths")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileDirectActorImpactInput input = {};
    input.actorIndex = 7;
    input.actorId = 200;
    input.damageMultiplier = 2;
    input.nonPartyProjectileDamage = 5;

    const GameplayProjectileService::ProjectileDirectActorImpact partyImpact =
        service.buildProjectileDirectActorImpact(makePartyProjectile(9), input);

    CHECK(partyImpact.applyPartyProjectileDamage);
    CHECK_FALSE(partyImpact.applyNonPartyProjectileDamage);
    CHECK(partyImpact.queuePartyProjectileActorEvent);
    CHECK_EQ(partyImpact.actorIndex, 7u);
    CHECK_EQ(partyImpact.actorId, 200u);
    CHECK_EQ(partyImpact.damage, 18);

    const GameplayProjectileService::ProjectileDirectActorImpact actorImpact =
        service.buildProjectileDirectActorImpact(makeActorProjectile(), input);

    CHECK_FALSE(actorImpact.applyPartyProjectileDamage);
    CHECK(actorImpact.applyNonPartyProjectileDamage);
    CHECK_FALSE(actorImpact.queuePartyProjectileActorEvent);
    CHECK_EQ(actorImpact.damage, 5);
}

TEST_CASE("projectile collision filters dead actor-source and friendly actors")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileCollisionActorFacts actorFacts = {};
    actorFacts.actorId = 20;

    CHECK(service.canProjectileCollideWithActor(makePartyProjectile(), actorFacts));

    actorFacts.actorId = 1;
    CHECK(service.canProjectileCollideWithActor(makePartyProjectile(), actorFacts));
    CHECK_FALSE(service.canProjectileCollideWithActor(makeActorProjectile(1), actorFacts));

    actorFacts.actorId = 20;
    actorFacts.dead = true;
    CHECK_FALSE(service.canProjectileCollideWithActor(makePartyProjectile(), actorFacts));

    actorFacts.dead = false;
    actorFacts.friendlyToProjectileSource = true;
    CHECK_FALSE(service.canProjectileCollideWithActor(makeActorProjectile(), actorFacts));
}

TEST_CASE("summoned actor projectiles do not collide with party allies")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileState projectile = makeActorProjectile();
    projectile.fromSummonedMonster = true;

    GameplayProjectileService::ProjectileActorRelationFacts facts = {};
    facts.targetHostileToParty = false;
    facts.targetPartyControlled = false;
    CHECK(service.isProjectileSourceFriendlyToActor(projectile, facts));

    facts.targetHostileToParty = true;
    CHECK_FALSE(service.isProjectileSourceFriendlyToActor(projectile, facts));

    facts.targetPartyControlled = true;
    CHECK(service.isProjectileSourceFriendlyToActor(projectile, facts));
}

TEST_CASE("fire spike spawn limits are mastery based and actor trigger chooses nearest hostile")
{
    GameplayProjectileService service;
    GameplayProjectileService::FireSpikeTrapSpawnLimitInput spawnInput = {};
    spawnInput.sourcePartyMemberIndex = 2;
    spawnInput.skillMastery = uint32_t(SkillMastery::Expert);

    for (uint32_t index = 0; index < 5; ++index)
    {
        GameplayProjectileService::FireSpikeActiveTrapFacts trap = {};
        trap.sourcePartyMemberIndex = 2;
        spawnInput.traps.push_back(trap);
    }

    GameplayProjectileService::FireSpikeTrapSpawnResult spawnResult = service.buildFireSpikeTrapSpawn(spawnInput);
    CHECK_EQ(spawnResult.activeLimit, 5u);
    CHECK_EQ(spawnResult.activeCount, 5u);
    CHECK_FALSE(spawnResult.accepted);

    spawnInput.traps.pop_back();
    spawnResult = service.buildFireSpikeTrapSpawn(spawnInput);
    CHECK(spawnResult.accepted);
    CHECK(spawnResult.trapId != 0);

    GameplayProjectileService::FireSpikeTrapTriggerInput triggerInput = {};
    triggerInput.trapId = spawnResult.trapId;
    triggerInput.trapRadius = 32;
    triggerInput.skillLevel = 10;
    triggerInput.skillMastery = uint32_t(SkillMastery::Expert);
    triggerInput.x = 0.0f;
    triggerInput.y = 0.0f;
    triggerInput.z = 0.0f;

    GameplayProjectileService::FireSpikeTrapActorFacts farHostile = {};
    farHostile.actorIndex = 9;
    farHostile.actorId = 300;
    farHostile.x = 60.0f;
    farHostile.z = -32.0f;
    farHostile.radius = 32;
    farHostile.height = 128;
    farHostile.hostileToParty = true;
    triggerInput.actors.push_back(farHostile);

    GameplayProjectileService::FireSpikeTrapActorFacts nearHostile = farHostile;
    nearHostile.actorIndex = 4;
    nearHostile.actorId = 301;
    nearHostile.x = 20.0f;
    triggerInput.actors.push_back(nearHostile);

    GameplayProjectileService::FireSpikeTrapActorFacts friendly = farHostile;
    friendly.actorIndex = 2;
    friendly.actorId = 302;
    friendly.x = 5.0f;
    friendly.hostileToParty = false;
    triggerInput.actors.push_back(friendly);

    const GameplayProjectileService::FireSpikeTrapTriggerResult triggerResult =
        service.buildFireSpikeTrapTrigger(triggerInput);

    CHECK(triggerResult.triggered);
    CHECK(triggerResult.applyActorImpact);
    CHECK(triggerResult.spawnImpactVisual);
    CHECK(triggerResult.expireTrap);
    CHECK_EQ(triggerResult.actorIndex, 4u);
    CHECK_EQ(triggerResult.actorId, 301u);
    CHECK(triggerResult.damage > 0);
}

TEST_CASE("projectile frame without collision advances motion without expiring")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileState projectile = makePartyProjectile();
    projectile.x = 10.0f;
    projectile.y = 20.0f;
    projectile.z = 30.0f;
    projectile.velocityX = 100.0f;
    projectile.velocityY = 0.0f;
    projectile.velocityZ = 10.0f;
    projectile.lifetimeTicks = 1000;

    GameplayProjectileService::ProjectileFrameFacts facts = {};
    facts.deltaSeconds = 0.25f;
    facts.gravity = 8.0f;

    const GameplayProjectileService::ProjectileFrameResult result =
        service.updateProjectileFrame(projectile, facts);

    CHECK(result.applyMotionEnd);
    CHECK_FALSE(result.expireProjectile);
    CHECK_EQ(result.motion.startX, doctest::Approx(10.0f));
    CHECK_EQ(result.motion.endX, doctest::Approx(35.0f));
    CHECK_EQ(result.motion.endZ, doctest::Approx(32.0f));
}

TEST_CASE("projectile lifetime advances at 128hz instead of render-frame rate")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileState projectile = makePartyProjectile();
    projectile.velocityY = 4000.0f;
    projectile.lifetimeTicks = 8;

    GameplayProjectileService::ProjectileFrameFacts facts = {};
    facts.deltaSeconds = 1.0f / 5000.0f;

    for (int frameIndex = 0; frameIndex < 8; ++frameIndex)
    {
        const GameplayProjectileService::ProjectileFrameResult result =
            service.updateProjectileFrame(projectile, facts);

        CHECK_FALSE(result.expireProjectile);

        if (result.applyMotionEnd)
        {
            service.applyProjectileMotionEnd(projectile, result.motion);
        }
    }

    CHECK(projectile.timeSinceCreatedTicks < projectile.lifetimeTicks);

    bool expired = false;
    for (int frameIndex = 0; frameIndex < 400; ++frameIndex)
    {
        const GameplayProjectileService::ProjectileFrameResult result =
            service.updateProjectileFrame(projectile, facts);

        if (result.expireProjectile)
        {
            expired = true;
            break;
        }

        if (result.applyMotionEnd)
        {
            service.applyProjectileMotionEnd(projectile, result.motion);
        }
    }

    CHECK(expired);
}

TEST_CASE("projectile impact lifetime advances at 128hz instead of render-frame rate")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileImpactVisualDefinition definition = {};
    definition.objectDescriptionId = 1;
    definition.objectSpriteId = 158;
    definition.objectSpriteFrameIndex = 158;
    definition.lifetimeTicks = 8;
    definition.hasVisual = true;
    definition.objectName = "Splash";
    definition.objectSpriteName = "splash";

    const GameplayProjectileService::ProjectileImpactSpawnResult spawnResult =
        service.spawnWaterSplashImpactVisual(definition, 0.0f, 0.0f, 0.0f);
    REQUIRE(spawnResult.spawned);

    const float highFrameRateDeltaSeconds = 1.0f / 5000.0f;

    for (int frameIndex = 0; frameIndex < 8; ++frameIndex)
    {
        service.updateProjectileImpactPresentation(highFrameRateDeltaSeconds);
    }

    CHECK_EQ(service.projectileImpactCount(), 1u);
    const GameplayProjectileService::ProjectileImpactState *pImpact = service.projectileImpactState(0);
    REQUIRE(pImpact != nullptr);
    CHECK(pImpact->timeSinceCreatedTicks < definition.lifetimeTicks);

    for (int frameIndex = 0; frameIndex < 400; ++frameIndex)
    {
        service.updateProjectileImpactPresentation(highFrameRateDeltaSeconds);
    }

    CHECK_EQ(service.projectileImpactCount(), 0u);
}
