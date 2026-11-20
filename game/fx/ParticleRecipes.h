#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace OpenYAMM::Game
{
class ParticleSystem;

namespace FxRecipes
{
enum class ProjectileRecipe
{
    None,
    FireBolt,
    Fireball,
    FireSpike,
    Immolation,
    MeteorShower,
    Inferno,
    Incinerate,
    Starburst,
    Implosion,
    Cannonball,
    Blaster,
    Sparks,
    LightningBolt,
    IceBolt,
    IceBlastFallout,
    PoisonSpray,
    AcidBurst,
    LightBolt,
    Sunray,
    Stun,
    RockBlast,
    Blades,
    DeathBlossom,
    Harm,
    FlyingFist,
    DestroyUndead,
    Sharpmetal,
    DragonBreath,
    DarkFireBolt,
    MindBlast,
    ToxicCloud,
    MonsterAirBolt,
    MonsterEarthBolt,
    MonsterFireBolt,
    MonsterWaterBolt,
    MonsterBodyBolt,
    MonsterMindBolt,
    MonsterSpiritBolt,
    MonsterLightBolt,
    MonsterDarkBolt,
    Arrow,
    FireArrow,
    // Spells with no particle recipe of their own; the recipes only let engine/effects/projectiles.yml bind them
    // (see projectileRecipeIsBindingOnly). Charm to Control Undead are debuffs applied at once, which fly only when a
    // map event casts them. The traps are the bursts of discharged chest traps, which never fly.
    DeadlySwarm,
    MassDistortion,
    SpiritLash,
    PrismaticLight,
    SoulDrinker,
    Lifedrain,
    ShrinkingRay,
    Charm,
    Blind,
    Telepathy,
    Berserk,
    Enslave,
    ControlUndead,
    FireTrap,
    ElecTrap,
    ColdTrap,
    PoisonTrap,
    Armageddon,
    GenericParticleTrail,
    GenericFireTrail,
    GenericLineTrail,
};

enum class ProjectileFxPrimitive
{
    None,
    RenderSprite,
    HangingTrail,
    SegmentProjectile,
    SingleCollisionBurst,
    RadialCollisionBurst,
    FireballSphereBurst,
    ImplosionSphere,
    MindBlastAfterEffect,
    Stun,
};

enum class ProjectileFxMaterial
{
    None,
    Effpar01,
    Effpar02,
    Effpar03,
};

struct ProjectileFxRecipe
{
    ProjectileFxPrimitive trailPrimitive = ProjectileFxPrimitive::None;
    ProjectileFxPrimitive impactPrimitive = ProjectileFxPrimitive::None;
    ProjectileFxMaterial trailMaterial = ProjectileFxMaterial::None;
    ProjectileFxMaterial impactMaterial = ProjectileFxMaterial::None;
    uint32_t colorAbgr = 0xffffffffu;
    uint32_t impactColorAbgr = 0xffffffffu;
    uint32_t mobileLightColorAbgr = 0xffffffffu;
    float mobileLightRadius = 0.0f;
    bool renderProjectileBillboard = true;
};

struct ProjectileSpawnContext
{
    uint32_t projectileId = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    int spellId = 0;
    std::string objectName;
    std::string spriteName;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float velocityZ = 0.0f;
};

struct ProjectileSegmentSpawnContext
{
    uint32_t projectileId = 0;
    bool hasPreviousPosition = false;
    float previousX = 0.0f;
    float previousY = 0.0f;
    float previousZ = 0.0f;
    float currentX = 0.0f;
    float currentY = 0.0f;
    float currentZ = 0.0f;
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float velocityZ = 0.0f;
};

struct ImpactSpawnContext
{
    ProjectileRecipe recipe = ProjectileRecipe::None;
    std::string objectName;
    std::string spriteName;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

ProjectileRecipe classifyProjectileRecipe(
    int spellId,
    const std::string &objectName,
    const std::string &spriteName,
    uint16_t objectFlags);
std::string_view projectileRecipeName(ProjectileRecipe recipe);
std::optional<ProjectileRecipe> projectileRecipeFromName(std::string_view name);

uint32_t projectileRecipeColorAbgr(ProjectileRecipe recipe);
uint32_t projectileRecipeImpactColorAbgr(ProjectileRecipe recipe);
uint32_t projectileRecipeLightColorAbgr(ProjectileRecipe recipe);
const ProjectileFxRecipe &projectileFxRecipe(ProjectileRecipe recipe);
bool projectileRecipeUsesHangingProjectileTrail(ProjectileRecipe recipe);
float projectileRecipeGlowRadius(ProjectileRecipe recipe);
float projectileRecipeAnchorOffset(ProjectileRecipe recipe, uint16_t radius, uint16_t height);
float projectileRecipeBackOffset(ProjectileRecipe recipe, uint16_t radius);
bool projectileRecipeUsesDedicatedImpactFx(ProjectileRecipe recipe);
// Arrows and the spells listed after them in ProjectileRecipe have recipes only so the enhanced style can bind effects:
// they have no classic impact burst or impact light.
bool projectileRecipeIsBindingOnly(ProjectileRecipe recipe);
bool projectileRecipeShowsImpactBillboard(ProjectileRecipe recipe);

void spawnProjectileTrailParticles(
    ParticleSystem &particleSystem,
    const ProjectileSpawnContext &context,
    ProjectileRecipe recipe);

void spawnHangingProjectileTrailParticles(
    ParticleSystem &particleSystem,
    const ProjectileSegmentSpawnContext &context,
    ProjectileRecipe recipe);

void spawnStunTrailParticles(
    ParticleSystem &particleSystem,
    const ProjectileSegmentSpawnContext &context,
    ProjectileRecipe recipe);

void spawnImpactParticles(
    ParticleSystem &particleSystem,
    const ImpactSpawnContext &context);

void spawnDecorationFireParticles(
    ParticleSystem &particleSystem,
    uint32_t seed,
    float x,
    float y,
    float z,
    float emitterRadius);

void spawnDecorationSmokeParticles(
    ParticleSystem &particleSystem,
    uint32_t seed,
    float x,
    float y,
    float z,
    float emitterRadius);

void spawnBuffSparkles(
    ParticleSystem &particleSystem,
    uint32_t seed,
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr);

void spawnActorDisintegrationParticles(ParticleSystem &particleSystem, uint32_t seed,
    float x, float y, float z, float actorHeight, float elapsedSeconds, float durationSeconds);

// One tongue of flame rising from a point of a burning creature's surface (actors.yml death_effect: burn), with an
// occasional ember or wisp of smoke. size: the flame's width in world units. tint: the flame's RGB (flame_color);
// without one the fire is orange.
void spawnActorBurnFlame(ParticleSystem &particleSystem, uint32_t seed, float x, float y, float z, float size,
    const std::optional<std::array<uint8_t, 3>> &tint = std::nullopt);

void spawnActorDebuffParticles(
    ParticleSystem &particleSystem,
    uint32_t spellId,
    uint32_t seed,
    float x,
    float y,
    float z,
    float actorHeight,
    float frontDirectionX,
    float frontDirectionY);

void spawnActorBuffParticles(
    ParticleSystem &particleSystem,
    uint32_t spellId,
    uint32_t seed,
    float x,
    float y,
    float z,
    float actorHeight,
    float frontDirectionX,
    float frontDirectionY);
}
}
