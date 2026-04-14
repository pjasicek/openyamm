#pragma once

#include <cstdint>
#include <string>

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
    MeteorShower,
    Starburst,
    Implosion,
    Cannonball,
    LightningBolt,
    IceBolt,
    PoisonSpray,
    AcidBurst,
    LightBolt,
    DragonBreath,
    DarkFireBolt,
    ToxicCloud,
    GenericParticleTrail,
    GenericFireTrail,
    GenericLineTrail,
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

uint32_t projectileRecipeColorAbgr(ProjectileRecipe recipe);
float projectileRecipeGlowRadius(ProjectileRecipe recipe);
float projectileRecipeAnchorOffset(ProjectileRecipe recipe, uint16_t radius, uint16_t height);
float projectileRecipeBackOffset(ProjectileRecipe recipe, uint16_t radius);
bool projectileRecipeUsesDedicatedImpactFx(ProjectileRecipe recipe);

void spawnProjectileTrailParticles(
    ParticleSystem &particleSystem,
    const ProjectileSpawnContext &context,
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
}
}
