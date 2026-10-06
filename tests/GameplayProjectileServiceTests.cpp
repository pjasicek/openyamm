#include "doctest/doctest.h"

#include "game/audio/SoundIds.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/fx/FxSharedTypes.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ParticleSystem.h"
#include "game/party/SkillData.h"
#include "game/party/SpellIds.h"

#include <algorithm>
#include <vector>

using OpenYAMM::Game::GameplayProjectileService;
using OpenYAMM::Game::SoundId;
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

float storedReferenceRoundParticleSize(float particleSize = 1.0f)
{
    return particleSize * 24.0f / 5.04f;
}
}

TEST_CASE("actor disintegration particles are bounded, expire and resume at the death clock")
{
    using namespace OpenYAMM::Game;
    ParticleSystem particles;
    FxRecipes::spawnActorDisintegrationParticles(particles, 42, 10, 20, 30, 179, 0, 1.25f);
    CHECK(particles.particleCount() == 80);
    const ParticleSystem::DebugStats stats = particles.debugStats();
    CHECK(stats.activeByMaterial[size_t(FxParticleMaterial::Mist)] == 64);
    CHECK(stats.activeByMaterial[size_t(FxParticleMaterial::Smoke)] == 16);
    particles.update(0.5f);
    ParticleSystem resumed;
    FxRecipes::spawnActorDisintegrationParticles(resumed, 42, 10, 20, 30, 179, 0.5f, 1.25f);
    REQUIRE(resumed.particleCount() == particles.particleCount());
    for (size_t i = 0; i < particles.particleCount(); ++i)
    {
        CHECK(resumed.particles()[i].z == doctest::Approx(particles.particles()[i].z));
    }
    particles.update(1.0f);
    CHECK(particles.particleCount() == 0);
    FxRecipes::spawnActorDisintegrationParticles(particles, 42, 10, 20, 30, 179, 1.25f, 1.25f);
    CHECK(particles.particleCount() == 0);
    for (uint32_t i = 0; i < 100; ++i)
    {
        FxRecipes::spawnActorDisintegrationParticles(particles, i, 10, 20, 30, 179, 0, 1.25f);
    }
    CHECK(particles.particleCount() == particles.maxParticleCount());
    particles.update(1.3f);
    CHECK(particles.particleCount() == 0);
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

TEST_CASE("monster spell projectile damage uses spell dice instead of monster level fallback")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectilePartyImpactDamageInput input = {};
    input.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Actor;
    input.hasMonsterFacts = true;
    input.monsterLevel = 25;
    input.monsterAbility = GameplayProjectileService::MonsterAttackAbility::Spell1;
    input.spellId = static_cast<int>(SpellId::LightningBolt);
    input.spell1Damage.diceSides = 8;
    input.spell1Damage.skillLevel = 7;
    input.spell1Damage.skillMastery = SkillMastery::Master;

    for (int rollIndex = 0; rollIndex < 32; ++rollIndex)
    {
        const int damage = service.resolveProjectilePartyImpactDamage(input);
        CHECK_GE(damage, 7);
        CHECK_LE(damage, 56);
    }
}

TEST_CASE("monster attack projectile damage rolls monster table dice")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectilePartyImpactDamageInput input = {};
    input.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Actor;
    input.hasMonsterFacts = true;
    input.monsterLevel = 25;
    input.monsterAbility = GameplayProjectileService::MonsterAttackAbility::Attack1;
    input.attack1Damage.diceRolls = 2;
    input.attack1Damage.diceSides = 4;
    input.attack1Damage.bonus = 3;

    for (int rollIndex = 0; rollIndex < 32; ++rollIndex)
    {
        const int damage = service.resolveProjectilePartyImpactDamage(input);
        CHECK_GE(damage, 5);
        CHECK_LE(damage, 11);
    }
}

TEST_CASE("sparks projectile keeps lighting but skips emitted particles")
{
    const ProjectileRecipe recipe = OpenYAMM::Game::FxRecipes::classifyProjectileRecipe(
        static_cast<int>(SpellId::Sparks),
        "Sparks",
        "spell02",
        0);
    OpenYAMM::Game::ParticleSystem particleSystem;
    OpenYAMM::Game::FxRecipes::ProjectileSpawnContext context = {};
    context.spellId = static_cast<int>(SpellId::Sparks);
    context.objectName = "Sparks";
    context.spriteName = "spell02";

    CHECK(recipe == ProjectileRecipe::Sparks);
    OpenYAMM::Game::FxRecipes::spawnProjectileTrailParticles(particleSystem, context, recipe);
    CHECK_EQ(particleSystem.particleCount(), 0u);
    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe));
    CHECK_GT(OpenYAMM::Game::FxRecipes::projectileRecipeGlowRadius(recipe), 0.0f);

    OpenYAMM::Game::FxRecipes::ImpactSpawnContext impactContext = {};
    impactContext.recipe = recipe;
    impactContext.objectName = "Sparks";
    impactContext.spriteName = "spell02";
    OpenYAMM::Game::FxRecipes::spawnImpactParticles(particleSystem, impactContext);
    REQUIRE_EQ(particleSystem.particleCount(), 8u);

    for (const OpenYAMM::Game::FxParticleState &particle : particleSystem.particles())
    {
        CHECK_EQ(particle.startColorAbgr, 0xff14c8c8u);
        CHECK_EQ(particle.size, doctest::Approx(24.0f));
        CHECK_EQ(particle.endSize, doctest::Approx(24.0f));
        CHECK(particle.tag == OpenYAMM::Game::FxParticleTag::Impact);
    }
}

TEST_CASE("energy blaster projectile has no trail particles but keeps dedicated impact fx")
{
    const ProjectileRecipe recipe = OpenYAMM::Game::FxRecipes::classifyProjectileRecipe(
        0,
        "Laser",
        "lzrbolt",
        0);
    OpenYAMM::Game::ParticleSystem particleSystem;
    OpenYAMM::Game::FxRecipes::ProjectileSpawnContext context = {};
    context.objectName = "Laser";
    context.spriteName = "lzrbolt";

    OpenYAMM::Game::FxRecipes::spawnProjectileTrailParticles(particleSystem, context, recipe);

    CHECK(recipe == ProjectileRecipe::Blaster);
    CHECK_EQ(particleSystem.particleCount(), 0u);
    CHECK_EQ(OpenYAMM::Game::FxRecipes::projectileRecipeGlowRadius(recipe), 0.0f);
    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe));
}

TEST_CASE("monster elemental bolts use projectile colors and hanging trail recipes")
{
    struct Fixture
    {
        const char *pObjectName = "";
        const char *pSpriteName = "";
        ProjectileRecipe expectedRecipe = ProjectileRecipe::None;
        uint32_t expectedColorAbgr = 0xffffffffu;
    };

    const Fixture fixtures[] = {
        {"air", "spell101", ProjectileRecipe::MonsterAirBolt, 0xffffaa0au},
        {"earth", "spell102", ProjectileRecipe::MonsterEarthBolt, 0xff0e315cu},
        {"fire", "spell103", ProjectileRecipe::MonsterFireBolt, 0xff1e3cffu},
        {"water", "spell104", ProjectileRecipe::MonsterWaterBolt, 0xffd06200u},
        {"body", "", ProjectileRecipe::MonsterBodyBolt, 0xff50b40au},
        {"mind", "", ProjectileRecipe::MonsterMindBolt, 0xff05c8c8u},
        {"spirit", "", ProjectileRecipe::MonsterSpiritBolt, 0xffffaa0au},
        {"light", "spell106", ProjectileRecipe::MonsterLightBolt, 0xffffffffu},
        {"dark", "spell107", ProjectileRecipe::MonsterDarkBolt, 0xff7e7e7eu},
    };

    for (const Fixture &fixture : fixtures)
    {
        const ProjectileRecipe recipe = OpenYAMM::Game::FxRecipes::classifyProjectileRecipe(
            0,
            fixture.pObjectName,
            fixture.pSpriteName,
            0);
        const OpenYAMM::Game::FxRecipes::ProjectileFxRecipe &fxRecipe =
            OpenYAMM::Game::FxRecipes::projectileFxRecipe(recipe);

        CHECK(recipe == fixture.expectedRecipe);
        CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeUsesHangingProjectileTrail(recipe));
        CHECK_EQ(OpenYAMM::Game::FxRecipes::projectileRecipeColorAbgr(recipe), fixture.expectedColorAbgr);
        CHECK(fxRecipe.trailPrimitive == OpenYAMM::Game::FxRecipes::ProjectileFxPrimitive::HangingTrail);
        CHECK(fxRecipe.impactPrimitive == OpenYAMM::Game::FxRecipes::ProjectileFxPrimitive::SingleCollisionBurst);
    }
}

TEST_CASE("Hanging trail emits first and segment particles from previous and current positions")
{
    OpenYAMM::Game::ParticleSystem particleSystem;
    OpenYAMM::Game::FxRecipes::ProjectileSegmentSpawnContext context = {};
    context.projectileId = 77;
    context.currentX = 100.0f;
    context.currentY = 200.0f;
    context.currentZ = 300.0f;

    OpenYAMM::Game::FxRecipes::spawnHangingProjectileTrailParticles(
        particleSystem,
        context,
        ProjectileRecipe::MonsterFireBolt);

    REQUIRE_EQ(particleSystem.particleCount(), 2u);

    for (const OpenYAMM::Game::FxParticleState &particle : particleSystem.particles())
    {
        CHECK_EQ(particle.startColorAbgr, 0xff1e3cffu);
        CHECK_EQ(particle.endColorAbgr, 0x001e3cffu);
        CHECK_EQ(particle.size, doctest::Approx(storedReferenceRoundParticleSize()));
        CHECK_EQ(particle.endSize, doctest::Approx(storedReferenceRoundParticleSize()));
        CHECK_GE(particle.lifetimeSeconds, 1.0f);
        CHECK_LE(particle.lifetimeSeconds, 2.0f);
        CHECK(particle.motion == OpenYAMM::Game::FxParticleMotion::Ascend);
        CHECK(particle.tag == OpenYAMM::Game::FxParticleTag::Trail);
    }

    context.hasPreviousPosition = true;
    context.previousX = 100.0f;
    context.previousY = 200.0f;
    context.previousZ = 300.0f;
    context.currentX = 132.0f;
    context.currentY = 220.0f;
    context.currentZ = 308.0f;

    OpenYAMM::Game::FxRecipes::spawnHangingProjectileTrailParticles(
        particleSystem,
        context,
        ProjectileRecipe::MonsterFireBolt);

    REQUIRE_EQ(particleSystem.particleCount(), 6u);
    const OpenYAMM::Game::FxParticleState &midpointParticle = particleSystem.particles()[2];
    const OpenYAMM::Game::FxParticleState &currentParticle = particleSystem.particles()[4];

    CHECK_EQ(midpointParticle.x, doctest::Approx(120.0f));
    CHECK_EQ(midpointParticle.y, doctest::Approx(210.0f));
    CHECK_EQ(midpointParticle.z, doctest::Approx(304.0f));
    CHECK_EQ(currentParticle.x, doctest::Approx(136.0f));
    CHECK_EQ(currentParticle.y, doctest::Approx(220.0f));
    CHECK_EQ(currentParticle.z, doctest::Approx(308.0f));

    for (size_t particleIndex = 2; particleIndex < particleSystem.particles().size(); ++particleIndex)
    {
        const OpenYAMM::Game::FxParticleState &particle = particleSystem.particles()[particleIndex];
        CHECK_EQ(particle.size, doctest::Approx(storedReferenceRoundParticleSize()));
        CHECK_EQ(particle.endSize, doctest::Approx(storedReferenceRoundParticleSize()));
        CHECK_GE(particle.lifetimeSeconds, 0.75f);
        CHECK_LE(particle.lifetimeSeconds, 1.25f);
    }
}

TEST_CASE("Stun particle sizes use reference particle size units")
{
    OpenYAMM::Game::ParticleSystem particleSystem;
    OpenYAMM::Game::FxRecipes::ProjectileSegmentSpawnContext context = {};
    context.projectileId = 88;
    context.currentX = 12.0f;
    context.currentY = 24.0f;
    context.currentZ = 36.0f;

    OpenYAMM::Game::FxRecipes::spawnStunTrailParticles(
        particleSystem,
        context,
        ProjectileRecipe::Stun);

    REQUIRE_EQ(particleSystem.particleCount(), 1u);
    CHECK_EQ(particleSystem.particles()[0].size, doctest::Approx(storedReferenceRoundParticleSize(1.0f)));

    context.hasPreviousPosition = true;
    context.previousX = context.currentX;
    context.previousY = context.currentY;
    context.previousZ = context.currentZ;
    context.currentX = 44.0f;

    OpenYAMM::Game::FxRecipes::spawnStunTrailParticles(
        particleSystem,
        context,
        ProjectileRecipe::Stun);

    REQUIRE_EQ(particleSystem.particleCount(), 3u);
    CHECK_EQ(particleSystem.particles()[1].size, doctest::Approx(storedReferenceRoundParticleSize(3.0f)));
    CHECK_EQ(particleSystem.particles()[2].size, doctest::Approx(storedReferenceRoundParticleSize(2.0f)));
}

TEST_CASE("Projectile metadata marks particle-only spell projectiles")
{
    const ProjectileRecipe particleOnlyRecipes[] = {
        ProjectileRecipe::FireBolt,
        ProjectileRecipe::Fireball,
        ProjectileRecipe::PoisonSpray,
        ProjectileRecipe::AcidBurst,
        ProjectileRecipe::LightBolt,
        ProjectileRecipe::LightningBolt,
        ProjectileRecipe::Sunray,
    };

    for (const ProjectileRecipe recipe : particleOnlyRecipes)
    {
        const OpenYAMM::Game::FxRecipes::ProjectileFxRecipe &fxRecipe =
            OpenYAMM::Game::FxRecipes::projectileFxRecipe(recipe);

        CHECK_FALSE(fxRecipe.renderProjectileBillboard);
    }
}

TEST_CASE("Segment projectile metadata covers lightning and sunray")
{
    struct Fixture
    {
        int spellId = 0;
        const char *pObjectName = "";
        const char *pSpriteName = "";
        ProjectileRecipe expectedRecipe = ProjectileRecipe::None;
        uint32_t expectedColorAbgr = 0xffffffffu;
        float expectedLightRadius = 0.0f;
    };

    const Fixture fixtures[] = {
        {
            static_cast<int>(SpellId::LightningBolt),
            "Lightning Bolt",
            "spell18",
            ProjectileRecipe::LightningBolt,
            0xff14c8c8u,
            256.0f
        },
        {
            static_cast<int>(SpellId::Sunray),
            "Sunray",
            "spell87",
            ProjectileRecipe::Sunray,
            0xffffffffu,
            128.0f
        },
    };

    for (const Fixture &fixture : fixtures)
    {
        const ProjectileRecipe recipe = OpenYAMM::Game::FxRecipes::classifyProjectileRecipe(
            fixture.spellId,
            fixture.pObjectName,
            fixture.pSpriteName,
            0);
        const OpenYAMM::Game::FxRecipes::ProjectileFxRecipe &fxRecipe =
            OpenYAMM::Game::FxRecipes::projectileFxRecipe(recipe);

        CHECK(recipe == fixture.expectedRecipe);
        CHECK(fxRecipe.trailPrimitive == OpenYAMM::Game::FxRecipes::ProjectileFxPrimitive::SegmentProjectile);
        CHECK_FALSE(fxRecipe.renderProjectileBillboard);
        CHECK_EQ(OpenYAMM::Game::FxRecipes::projectileRecipeColorAbgr(recipe), fixture.expectedColorAbgr);
        CHECK_EQ(OpenYAMM::Game::FxRecipes::projectileRecipeGlowRadius(recipe), doctest::Approx(
            fixture.expectedLightRadius));
    }
}

TEST_CASE("Normal-sprite projectile families do not get particle-only recipes")
{
    struct Fixture
    {
        int spellId = 0;
        const char *pObjectName = "";
        const char *pSpriteName = "";
    };

    const Fixture fixtures[] = {
        {0, "FireArrow", "FrArw"},
        {static_cast<int>(SpellId::DeadlySwarm), "Deadly Swarm", "spell37"},
        {static_cast<int>(SpellId::PrismaticLight), "Prismatic Light", "spell84"},
    };

    for (const Fixture &fixture : fixtures)
    {
        const ProjectileRecipe recipe = OpenYAMM::Game::FxRecipes::classifyProjectileRecipe(
            fixture.spellId,
            fixture.pObjectName,
            fixture.pSpriteName,
            0);
        const OpenYAMM::Game::FxRecipes::ProjectileFxRecipe &fxRecipe =
            OpenYAMM::Game::FxRecipes::projectileFxRecipe(recipe);

        CHECK(recipe == ProjectileRecipe::None);
        CHECK(fxRecipe.renderProjectileBillboard);
        CHECK_FALSE(OpenYAMM::Game::FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe));
    }
}

TEST_CASE("FX-only projectile presentation still spawns dedicated impact state")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileState projectile = makePartyProjectile();
    projectile.visualMode = OpenYAMM::Game::GameplayProjectileVisualMode::FxOnly;
    projectile.spellId = static_cast<int>(SpellId::LightningBolt);
    projectile.objectName = "Lightning Bolt";
    projectile.objectSpriteName = "spell18";
    projectile.sectorId = 4;

    service.projectiles().push_back(projectile);

    std::vector<OpenYAMM::Game::GameplayProjectilePresentationState> projectiles;
    std::vector<OpenYAMM::Game::GameplayProjectileImpactPresentationState> impacts;
    service.collectProjectilePresentationState(projectiles, impacts);

    REQUIRE_EQ(projectiles.size(), 1u);
    CHECK(projectiles.front().visualMode == OpenYAMM::Game::GameplayProjectileVisualMode::FxOnly);
    CHECK_EQ(projectiles.front().objectName, "Lightning Bolt");

    GameplayProjectileService::ProjectileImpactVisualDefinition definition = {};
    definition.objectName = "Lightning Bolt Impact";
    definition.objectSpriteName = "spell18c";
    definition.lifetimeTicks = 16;
    definition.hasVisual = false;

    const GameplayProjectileService::ProjectileImpactSpawnResult impact =
        service.spawnProjectileImpactVisual(projectile, definition, 10.0f, 20.0f, 30.0f, false, 7);

    REQUIRE(impact.spawned);
    REQUIRE(impact.pImpact != nullptr);
    CHECK_EQ(impact.pImpact->sourceSpellId, static_cast<int>(SpellId::LightningBolt));
    CHECK_EQ(impact.pImpact->sourceObjectName, "Lightning Bolt");
    CHECK_EQ(impact.pImpact->sourceObjectSpriteName, "spell18");
    CHECK_EQ(impact.pImpact->sectorId, 4);
    CHECK_EQ(impact.pImpact->targetActorIndex, 7u);

    service.collectProjectilePresentationState(projectiles, impacts);
    REQUIRE_EQ(impacts.size(), 1u);
    CHECK_EQ(impacts.front().targetActorIndex, 7u);
}

TEST_CASE("Special impact primitives emit expected particle counts")
{
    struct Fixture
    {
        ProjectileRecipe recipe = ProjectileRecipe::None;
        const char *pObjectName = "";
        const char *pSpriteName = "";
        size_t expectedParticleCount = 0;
    };

    const Fixture fixtures[] = {
        {ProjectileRecipe::Fireball, "Fireball", "fire04", 11u},
        {ProjectileRecipe::FireSpike, "Fire Spike", "spell07", 8u},
        {ProjectileRecipe::MeteorShower, "Meteor Shower", "spell09", 24u},
        {ProjectileRecipe::Inferno, "Inferno", "spell10", 8u},
        {ProjectileRecipe::Incinerate, "Incinerate", "spell11", 20u},
        {ProjectileRecipe::Implosion, "Implosion", "spell57c", 1u},
        {ProjectileRecipe::Blades, "Blades", "spell39c", 10u},
        {ProjectileRecipe::Harm, "Harm", "spell70", 10u},
        {ProjectileRecipe::FlyingFist, "Flying Fist", "spell76", 10u},
        {ProjectileRecipe::Sharpmetal, "Shrap Metal", "spell93", 10u},
    };

    for (const Fixture &fixture : fixtures)
    {
        OpenYAMM::Game::ParticleSystem particleSystem;
        OpenYAMM::Game::FxRecipes::ImpactSpawnContext context = {};
        context.recipe = fixture.recipe;
        context.objectName = fixture.pObjectName;
        context.spriteName = fixture.pSpriteName;

        OpenYAMM::Game::FxRecipes::spawnImpactParticles(particleSystem, context);

        CHECK_EQ(particleSystem.particleCount(), fixture.expectedParticleCount);
    }
}

TEST_CASE("Harm recipe separates travel light color from impact blood color")
{
    const ProjectileRecipe recipe = OpenYAMM::Game::FxRecipes::classifyProjectileRecipe(
        static_cast<int>(SpellId::Harm),
        "Harm",
        "spell70",
        0);

    CHECK(recipe == ProjectileRecipe::Harm);
    CHECK_EQ(OpenYAMM::Game::FxRecipes::projectileRecipeColorAbgr(recipe), 0xff0f6464u);
    CHECK_EQ(OpenYAMM::Game::FxRecipes::projectileRecipeLightColorAbgr(recipe), 0xff0f6464u);
    CHECK_EQ(OpenYAMM::Game::FxRecipes::projectileRecipeImpactColorAbgr(recipe), 0xff0000f0u);
    CHECK_EQ(OpenYAMM::Game::FxRecipes::projectileRecipeGlowRadius(recipe), doctest::Approx(128.0f));
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

TEST_CASE("fireball and spell dragon breath keep dedicated impact particles and show impact billboards")
{
    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeUsesDedicatedImpactFx(ProjectileRecipe::Fireball));
    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeShowsImpactBillboard(ProjectileRecipe::Fireball));
    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeUsesDedicatedImpactFx(ProjectileRecipe::DragonBreath));
    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeShowsImpactBillboard(ProjectileRecipe::DragonBreath));

    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeUsesDedicatedImpactFx(ProjectileRecipe::FireBolt));
    CHECK_FALSE(OpenYAMM::Game::FxRecipes::projectileRecipeShowsImpactBillboard(ProjectileRecipe::FireBolt));
    CHECK(OpenYAMM::Game::FxRecipes::projectileRecipeUsesDedicatedImpactFx(ProjectileRecipe::Sparks));
    CHECK_FALSE(OpenYAMM::Game::FxRecipes::projectileRecipeShowsImpactBillboard(ProjectileRecipe::Sparks));
}

TEST_CASE("projectile recipe debug names round trip and ignore separators")
{
    using OpenYAMM::Game::FxRecipes::projectileRecipeFromName;
    using OpenYAMM::Game::FxRecipes::projectileRecipeName;

    CHECK_EQ(projectileRecipeName(ProjectileRecipe::Implosion), "implosion");
    CHECK_EQ(projectileRecipeFromName("implosion"), ProjectileRecipe::Implosion);
    CHECK_EQ(projectileRecipeFromName("Dragon Breath"), ProjectileRecipe::DragonBreath);
    CHECK_EQ(projectileRecipeFromName("dragon-breath"), ProjectileRecipe::DragonBreath);
    CHECK_EQ(projectileRecipeFromName("ICE_BLAST_FALLOUT"), ProjectileRecipe::IceBlastFallout);
    CHECK_FALSE(projectileRecipeFromName("not-a-projectile"));
}

TEST_CASE("fireball and spell dragon breath travel particles are scaled without changing fire bolt")
{
    struct RecipeFixture
    {
        ProjectileRecipe recipe = ProjectileRecipe::None;
        int spellId = 0;
        const char *pObjectName = "";
        const char *pSpriteName = "";
        float expectedMinimumMaxSize = 0.0f;
        float expectedMaximumMaxSize = 0.0f;
    };

    const RecipeFixture fixtures[] = {
        {ProjectileRecipe::Fireball, static_cast<int>(SpellId::Fireball), "Fireball", "fire04", 20.0f, 50.0f},
        {
            ProjectileRecipe::DragonBreath,
            static_cast<int>(SpellId::DragonBreath),
            "Dragon Breath",
            "spell97",
            30.0f,
            60.0f
        },
        {ProjectileRecipe::FireBolt, static_cast<int>(SpellId::FireBolt), "Fire Bolt", "fire02", 0.0f, 25.0f},
    };

    for (const RecipeFixture &fixture : fixtures)
    {
        OpenYAMM::Game::ParticleSystem particleSystem;
        OpenYAMM::Game::FxRecipes::ProjectileSpawnContext context = {};
        context.projectileId = 42;
        context.spellId = fixture.spellId;
        context.objectName = fixture.pObjectName;
        context.spriteName = fixture.pSpriteName;
        context.velocityX = 256.0f;

        OpenYAMM::Game::FxRecipes::spawnProjectileTrailParticles(particleSystem, context, fixture.recipe);

        float maxParticleSize = 0.0f;

        for (const OpenYAMM::Game::FxParticleState &particle : particleSystem.particles())
        {
            maxParticleSize = std::max(maxParticleSize, particle.size);
        }

        CHECK_GT(maxParticleSize, fixture.expectedMinimumMaxSize);
        CHECK_LT(maxParticleSize, fixture.expectedMaximumMaxSize);
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

TEST_CASE("party projectile direct actor hit radius has small-monster floor")
{
    const GameplayProjectileService::ProjectileState partyProjectile = makePartyProjectile();
    const GameplayProjectileService::ProjectileState actorProjectile = makeActorProjectile();

    CHECK_EQ(GameplayProjectileService::directActorProjectileHitRadius(partyProjectile, 20.0f), 32.0f);
    CHECK_EQ(GameplayProjectileService::directActorProjectileHitRadius(partyProjectile, 50.0f), 50.0f);
    CHECK_EQ(GameplayProjectileService::directActorProjectileHitRadius(actorProjectile, 4.0f), 8.0f);
    CHECK_EQ(GameplayProjectileService::directActorProjectileHitRadius(actorProjectile, 20.0f), 20.0f);
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

TEST_CASE("projectile spawn forward offset stays on the ray and does not overshoot close targets")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileSpawnRequest request = {};
    request.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Party;
    request.definition.speed = 100.0f;
    request.definition.lifetimeTicks = 100;
    request.turnBasedPendingAction = true;
    request.sourceX = 0.0f;
    request.sourceY = 0.0f;
    request.sourceZ = 0.0f;
    request.targetX = 10.0f;
    request.targetY = 0.0f;
    request.targetZ = 10.0f;
    request.spawnForwardOffset = 100.0f;

    const GameplayProjectileService::ProjectileSpawnResult result = service.spawnProjectile(request);

    CHECK(result.kind == GameplayProjectileService::ProjectileSpawnResult::Kind::SpawnedProjectile);
    CHECK(result.projectile.turnBasedPendingAction);
    CHECK_EQ(result.projectile.x, doctest::Approx(10.0f));
    CHECK_EQ(result.projectile.y, doctest::Approx(0.0f));
    CHECK_EQ(result.projectile.z, doctest::Approx(10.0f));
    CHECK_EQ(result.projectile.velocityX, doctest::Approx(70.71068f));
    CHECK_EQ(result.projectile.velocityY, doctest::Approx(0.0f));
    CHECK_EQ(result.projectile.velocityZ, doctest::Approx(70.71068f));
}

TEST_CASE("direct party projectile impact does not also apply splash to the party")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileState projectile = makeActorProjectile();
    projectile.spellId = static_cast<int>(SpellId::Fireball);
    projectile.damage = 17;
    projectile.lifetimeTicks = 1000;

    GameplayProjectileService::ProjectileFrameFacts facts = {};
    facts.deltaSeconds = 1.0f / 128.0f;
    facts.hasCollision = true;
    facts.collision.kind = GameplayProjectileService::ProjectileFrameCollisionKind::Party;
    facts.collision.point = {0.0f, 0.0f, 64.0f};
    facts.canHitParty = true;
    facts.nonPartyProjectileDamage = 17;
    facts.partyPosition = {0.0f, 0.0f, 64.0f};
    facts.partyCollisionRadius = 64.0f;
    facts.partyCollisionHeight = 128.0f;

    const GameplayProjectileService::ProjectileFrameResult result =
        service.updateProjectileFrame(projectile, facts);

    REQUIRE(result.directPartyDamage.has_value());
    CHECK_EQ(*result.directPartyDamage, 17);
    REQUIRE(result.areaImpact.has_value());
    CHECK_FALSE(result.areaImpact->impact.hitParty);
    CHECK(result.expireProjectile);
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

TEST_CASE("dragon breath projectile sound pair uses dragon release and impact ids")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileState projectile = makePartyProjectile();
    projectile.spellId = static_cast<int>(OpenYAMM::Game::spellIdValue(SpellId::FireBolt));
    projectile.effectSoundId = static_cast<int>(SoundId::DragonBreath);
    projectile.impactSoundIdOverride = static_cast<uint32_t>(SoundId::DragonBreathImpact);

    const std::optional<GameplayProjectileService::ProjectileAudioRequest> releaseAudio =
        service.buildProjectileReleaseAudioRequest(projectile, 10.0f, 20.0f, 30.0f);
    REQUIRE(releaseAudio);
    CHECK_EQ(releaseAudio->soundId, static_cast<uint32_t>(SoundId::DragonBreath));

    const std::optional<GameplayProjectileService::ProjectileAudioRequest> impactAudio =
        service.buildProjectileImpactAudioRequest(projectile, 40.0f, 50.0f, 60.0f);
    REQUIRE(impactAudio);
    CHECK_EQ(impactAudio->soundId, static_cast<uint32_t>(SoundId::DragonBreathImpact));
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

TEST_CASE("center anchored projectile impact visuals keep the collision point z")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileState projectile = makePartyProjectile();

    GameplayProjectileService::ProjectileImpactVisualDefinition bottomAnchoredDefinition = {};
    bottomAnchoredDefinition.objectDescriptionId = 1;
    bottomAnchoredDefinition.objectSpriteId = 158;
    bottomAnchoredDefinition.objectSpriteFrameIndex = 158;
    bottomAnchoredDefinition.objectHeight = 64;
    bottomAnchoredDefinition.lifetimeTicks = 8;
    bottomAnchoredDefinition.hasVisual = true;
    bottomAnchoredDefinition.centerAnchored = false;

    const GameplayProjectileService::ProjectileImpactSpawnResult bottomAnchoredResult =
        service.spawnProjectileImpactVisual(projectile, bottomAnchoredDefinition, 10.0f, 20.0f, 100.0f, true);
    REQUIRE(bottomAnchoredResult.spawned);
    REQUIRE(bottomAnchoredResult.pImpact != nullptr);
    CHECK_EQ(bottomAnchoredResult.pImpact->z, 68.0f);

    GameplayProjectileService::ProjectileImpactVisualDefinition centerAnchoredDefinition = bottomAnchoredDefinition;
    centerAnchoredDefinition.centerAnchored = true;

    const GameplayProjectileService::ProjectileImpactSpawnResult centerAnchoredResult =
        service.spawnProjectileImpactVisual(projectile, centerAnchoredDefinition, 10.0f, 20.0f, 100.0f, true);
    REQUIRE(centerAnchoredResult.spawned);
    REQUIRE(centerAnchoredResult.pImpact != nullptr);
    CHECK_EQ(centerAnchoredResult.pImpact->z, 100.0f);
}
