#include "game/fx/ParticleRecipes.h"

#include "game/party/SpellIds.h"
#include "game/StringUtils.h"
#include "game/SpriteObjectDefs.h"
#include "game/fx/FxSharedTypes.h"
#include "game/fx/ParticleSystem.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <functional>

namespace OpenYAMM::Game
{
namespace FxRecipes
{
namespace
{
struct LayerRecipe
{
    uint32_t startColorAbgr = 0xffffffffu;
    uint32_t endColorAbgr = 0x00ffffffu;
    uint32_t count = 0;
    float startOffset = 0.0f;
    float offsetStep = 0.0f;
    float lateralSpread = 0.0f;
    float verticalSpread = 0.0f;
    float inheritedVelocity = 0.0f;
    float upwardVelocity = 0.0f;
    float startSize = 0.0f;
    float endSize = 0.0f;
    float lifetimeSeconds = 0.0f;
    float drag = 0.0f;
    float rotationJitterRadians = 0.0f;
    float angularVelocityRadians = 0.0f;
    float stretch = 1.0f;
    float fadeInSeconds = 0.0f;
    FxParticleMotion motion = FxParticleMotion::VelocityTrail;
    FxParticleBlendMode blendMode = FxParticleBlendMode::Alpha;
    FxParticleAlignment alignment = FxParticleAlignment::CameraFacing;
    FxParticleMaterial material = FxParticleMaterial::SoftBlob;
    FxParticleTag tag = FxParticleTag::Misc;
};

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

bool containsToken(const std::string &value, const char *pToken)
{
    return toLowerCopy(value).find(pToken) != std::string::npos;
}

float hashToUnit(uint32_t value)
{
    return static_cast<float>(value & 0xffffu) / 65535.0f;
}

uint32_t varyAlpha(uint32_t colorAbgr, float multiplier)
{
    const uint32_t alpha = (colorAbgr >> 24) & 0xffu;
    const uint32_t scaledAlpha =
        static_cast<uint32_t>(std::lround(std::clamp(multiplier, 0.0f, 2.0f) * static_cast<float>(alpha)));
    return (colorAbgr & 0x00ffffffu) | (std::min(scaledAlpha, 255u) << 24);
}

void emitLayerParticles(
    ParticleSystem &particleSystem,
    uint32_t baseSeed,
    float x,
    float y,
    float z,
    float directionX,
    float directionY,
    float directionZ,
    float velocityX,
    float velocityY,
    float velocityZ,
    const LayerRecipe &layer)
{
    for (uint32_t particleIndex = 0; particleIndex < layer.count; ++particleIndex)
    {
        const uint32_t seed = baseSeed ^ (particleIndex * 2654435761u);
        const float lateralJitter = (hashToUnit(seed) * 2.0f - 1.0f) * layer.lateralSpread;
        const float verticalJitter = (hashToUnit(seed >> 8) * 2.0f - 1.0f) * layer.verticalSpread;
        const float trailOffset = layer.startOffset + static_cast<float>(particleIndex) * layer.offsetStep;
        const float swirl = hashToUnit(seed >> 16) * 2.0f - 1.0f;

        FxParticleState particle = {};
        particle.x = x - directionX * trailOffset + lateralJitter;
        particle.y = y - directionY * trailOffset - lateralJitter * 0.55f;
        particle.z = z - directionZ * trailOffset + verticalJitter;
        particle.velocityX = velocityX * layer.inheritedVelocity + (-directionY) * swirl * 12.0f;
        particle.velocityY = velocityY * layer.inheritedVelocity + directionX * swirl * 12.0f;
        particle.velocityZ = velocityZ * layer.inheritedVelocity + layer.upwardVelocity + verticalJitter * 4.0f;
        particle.size = layer.startSize;
        particle.endSize = layer.endSize;
        particle.drag = layer.drag;
        particle.rotationRadians = swirl * layer.rotationJitterRadians;
        particle.angularVelocityRadians = swirl * layer.angularVelocityRadians;
        particle.stretch = layer.stretch;
        particle.ageSeconds = 0.0f;
        particle.fadeInSeconds = layer.fadeInSeconds;
        particle.lifetimeSeconds = layer.lifetimeSeconds * (0.88f + hashToUnit(seed >> 4) * 0.24f);
        particle.startColorAbgr = varyAlpha(layer.startColorAbgr, 0.9f + hashToUnit(seed >> 12) * 0.25f);
        particle.endColorAbgr = layer.endColorAbgr;
        particle.motion = layer.motion;
        particle.blendMode = layer.blendMode;
        particle.alignment = layer.alignment;
        particle.material = layer.material;
        particle.tag = layer.tag;

        if (!particleSystem.addParticle(particle))
        {
            return;
        }
    }
}

void emitBurstParticle(
    ParticleSystem &particleSystem,
    float x,
    float y,
    float z,
    float size,
    uint32_t startColorAbgr,
    uint32_t endColorAbgr,
    float velocityScale,
    uint32_t seed,
    FxParticleMaterial material,
    FxParticleAlignment alignment,
    float stretch)
{
    const float angle = static_cast<float>(seed % 1024u) * (6.28318530717958647692f / 1024.0f);
    const float radial = 0.35f + static_cast<float>((seed >> 10) & 0xffu) / 255.0f * 0.65f;
    const float swirl = hashToUnit(seed >> 18) * 2.0f - 1.0f;

    FxParticleState particle = {};
    particle.x = x;
    particle.y = y;
    particle.z = z;
    const float spreadVelocityScale = velocityScale * 1.5f;
    particle.velocityX = std::cos(angle) * spreadVelocityScale * radial;
    particle.velocityY = std::sin(angle) * spreadVelocityScale * radial;
    particle.velocityZ =
        spreadVelocityScale * (0.2f + static_cast<float>((seed >> 18) & 0xffu) / 255.0f * 0.8f);
    particle.size = size;
    particle.endSize = size * 0.4f;
    particle.drag = 2.2f;
    particle.rotationRadians = swirl * 0.7f;
    particle.angularVelocityRadians = swirl * 3.2f;
    particle.stretch = stretch;
    particle.ageSeconds = 0.0f;
    particle.lifetimeSeconds = 0.45f + static_cast<float>((seed >> 26) & 0x1fu) / 31.0f * 0.35f;
    particle.startColorAbgr = startColorAbgr;
    particle.endColorAbgr = endColorAbgr;
    particle.motion = FxParticleMotion::Burst;
    particle.blendMode = FxParticleBlendMode::Additive;
    particle.alignment = alignment;
    particle.material = material;
    particle.tag = FxParticleTag::Impact;
    particleSystem.addParticle(particle);
}

void emitDebuffAuraLayer(
    ParticleSystem &particleSystem,
    uint32_t baseSeed,
    float x,
    float y,
    float z,
    float actorHeight,
    float frontDirectionX,
    float frontDirectionY,
    uint32_t count,
    float lateralRadius,
    float minHeightFraction,
    float maxHeightFraction,
    float upwardVelocity,
    float startSize,
    float endSize,
    float lifetimeSeconds,
    float drag,
    uint32_t startColorAbgr,
    uint32_t endColorAbgr,
    FxParticleMaterial material,
    FxParticleBlendMode blendMode)
{
    const float clampedHeight = std::max(72.0f, actorHeight);
    const float frontLength = std::sqrt(frontDirectionX * frontDirectionX + frontDirectionY * frontDirectionY);
    const float normalizedFrontX = frontLength > 0.001f ? frontDirectionX / frontLength : 1.0f;
    const float normalizedFrontY = frontLength > 0.001f ? frontDirectionY / frontLength : 0.0f;
    const float sideX = -normalizedFrontY;
    const float sideY = normalizedFrontX;
    const float forwardExtent = lateralRadius * 0.96f;
    const float sideExtent = lateralRadius * 0.72f;

    for (uint32_t particleIndex = 0; particleIndex < count; ++particleIndex)
    {
        const uint32_t seed = baseSeed ^ (particleIndex * 2654435761u);
        const float forwardDistance = forwardExtent * (0.08f + hashToUnit(seed) * 0.92f);
        const float sideDistance = sideExtent * (hashToUnit(seed >> 7) * 2.0f - 1.0f);
        const float heightFraction = minHeightFraction + (maxHeightFraction - minHeightFraction) * hashToUnit(seed >> 13);
        const float tangent = hashToUnit(seed >> 19) * 2.0f - 1.0f;
        const float sizeJitter = 0.72f + hashToUnit(seed >> 23) * 0.56f;
        const float offsetX = normalizedFrontX * forwardDistance + sideX * sideDistance;
        const float offsetY = normalizedFrontY * forwardDistance + sideY * sideDistance;

        FxParticleState particle = {};
        particle.x = x + offsetX;
        particle.y = y + offsetY;
        particle.z = z + clampedHeight * heightFraction;
        particle.velocityX = normalizedFrontX * 3.0f + sideX * tangent * 6.0f;
        particle.velocityY = normalizedFrontY * 3.0f + sideY * tangent * 6.0f;
        particle.velocityZ = upwardVelocity * (0.82f + hashToUnit(seed >> 4) * 0.36f);
        particle.size = startSize * sizeJitter;
        particle.endSize = endSize * (0.9f + hashToUnit(seed >> 11) * 0.2f);
        particle.drag = drag;
        particle.rotationRadians = tangent * 0.9f;
        particle.angularVelocityRadians = tangent * 1.6f;
        particle.stretch = 1.0f;
        particle.ageSeconds = 0.0f;
        particle.fadeInSeconds = 0.10f;
        particle.lifetimeSeconds = lifetimeSeconds * (0.94f + hashToUnit(seed >> 17) * 0.12f);
        particle.fadeOutStartSeconds = particle.lifetimeSeconds * 0.78f;
        particle.startColorAbgr = varyAlpha(startColorAbgr, 0.9f + hashToUnit(seed >> 21) * 0.2f);
        particle.endColorAbgr = endColorAbgr;
        particle.motion = FxParticleMotion::Drift;
        particle.blendMode = blendMode;
        particle.alignment = FxParticleAlignment::CameraFacing;
        particle.material = material;
        particle.tag = FxParticleTag::Buff;
        if (!particleSystem.addParticle(particle))
        {
            return;
        }
    }
}

uint32_t deriveImpactColorAbgr(const std::string &objectName, const std::string &spriteName)
{
    const bool isFire =
        containsToken(objectName, "fire")
        || containsToken(objectName, "meteor")
        || containsToken(objectName, "cannon")
        || containsToken(spriteName, "fire");
    const bool isLightning =
        containsToken(objectName, "lightning")
        || containsToken(objectName, "spark")
        || containsToken(spriteName, "spark")
        || containsToken(objectName, "laser");
    const bool isPoison =
        containsToken(objectName, "poison")
        || containsToken(objectName, "acid")
        || containsToken(objectName, "toxic");
    const bool isIce =
        containsToken(objectName, "ice")
        || containsToken(objectName, "frost")
        || containsToken(objectName, "light")
        || containsToken(objectName, "sunray")
        || containsToken(spriteName, "ice")
        || containsToken(spriteName, "sun");
    const bool isDark =
        containsToken(objectName, "dark")
        || containsToken(spriteName, "dark")
        || containsToken(objectName, "dragon breath");

    if (isFire)
    {
        return makeAbgr(255, 96, 32, 220);
    }

    if (isLightning)
    {
        return makeAbgr(240, 220, 64, 220);
    }

    if (isPoison)
    {
        return makeAbgr(64, 220, 128, 220);
    }

    if (isIce)
    {
        return makeAbgr(210, 230, 255, 220);
    }

    if (isDark)
    {
        return makeAbgr(160, 96, 220, 216);
    }

    return makeAbgr(192, 192, 192, 200);
}

}

ProjectileRecipe classifyProjectileRecipe(
    int spellId,
    const std::string &objectName,
    const std::string &spriteName,
    uint16_t objectFlags)
{
    if (spellId == 2
        || containsToken(objectName, "fire bolt")
        || containsToken(objectName, "fire arrow")
        || containsToken(spriteName, "fire02"))
    {
        return ProjectileRecipe::FireBolt;
    }

    if (spellId == 6
        || containsToken(objectName, "fireball")
        || containsToken(spriteName, "fire04"))
    {
        return ProjectileRecipe::Fireball;
    }

    if (spellId == 9
        || containsToken(objectName, "meteor shower")
        || containsToken(spriteName, "spell09"))
    {
        return ProjectileRecipe::MeteorShower;
    }

    if (spellId == 22
        || containsToken(objectName, "starburst")
        || containsToken(spriteName, "spell22"))
    {
        return ProjectileRecipe::Starburst;
    }

    if (spellId == 20
        || containsToken(objectName, "implosion")
        || containsToken(spriteName, "spell57c"))
    {
        return ProjectileRecipe::Implosion;
    }

    if (spellId == 15
        || containsToken(objectName, "sparks")
        || containsToken(spriteName, "spell02"))
    {
        return ProjectileRecipe::Sparks;
    }

    if (spellId == 18
        || containsToken(objectName, "lightning bolt")
        || containsToken(objectName, "laser")
        || containsToken(spriteName, "spell18")
        || containsToken(spriteName, "lzrbolt"))
    {
        return ProjectileRecipe::LightningBolt;
    }

    if (spellId == 26
        || spellId == 32
        || containsToken(objectName, "ice bolt")
        || containsToken(objectName, "ice blast")
        || containsToken(spriteName, "spell26"))
    {
        return ProjectileRecipe::IceBolt;
    }

    if (spellId == 24
        || containsToken(objectName, "poison spray"))
    {
        return ProjectileRecipe::PoisonSpray;
    }

    if (spellId == 11 || containsToken(objectName, "incinerate"))
    {
        return ProjectileRecipe::FireBolt;
    }

    if (spellId == 29
        || spellId == 37
        || containsToken(objectName, "acid burst"))
    {
        return ProjectileRecipe::AcidBurst;
    }

    if (spellId == 59
        || spellId == 65
        || containsToken(objectName, "mind blast")
        || containsToken(objectName, "psychic shock"))
    {
        return ProjectileRecipe::DarkFireBolt;
    }

    if (spellId == 78
        || spellId == 84
        || spellId == 87
        || spellId == 70
        || containsToken(objectName, "light bolt")
        || containsToken(objectName, "harm")
        || containsToken(objectName, "prismatic")
        || containsToken(objectName, "sunray")
        || containsToken(spriteName, "sp78b")
        || containsToken(spriteName, "spell84")
        || containsToken(spriteName, "spell87"))
    {
        return ProjectileRecipe::LightBolt;
    }

    if (spellId == 97
        || containsToken(objectName, "dragon breath")
        || containsToken(spriteName, "spell97"))
    {
        return ProjectileRecipe::DragonBreath;
    }

    if (containsToken(objectName, "darkfire bolt")
        || containsToken(spriteName, "spell99"))
    {
        return ProjectileRecipe::DarkFireBolt;
    }

    if (spellId == 90
        || containsToken(objectName, "toxic cloud")
        || containsToken(spriteName, "spell90"))
    {
        return ProjectileRecipe::ToxicCloud;
    }

    if ((objectFlags & ObjectDescTrailFire) != 0)
    {
        return ProjectileRecipe::GenericFireTrail;
    }

    if ((objectFlags & ObjectDescTrailParticle) != 0)
    {
        return ProjectileRecipe::GenericParticleTrail;
    }

    if ((objectFlags & ObjectDescTrailLine) != 0)
    {
        return ProjectileRecipe::GenericLineTrail;
    }

    return ProjectileRecipe::None;
}

uint32_t projectileRecipeColorAbgr(ProjectileRecipe recipe)
{
    switch (recipe)
    {
    case ProjectileRecipe::FireBolt:
    case ProjectileRecipe::Fireball:
    case ProjectileRecipe::MeteorShower:
    case ProjectileRecipe::Cannonball:
    case ProjectileRecipe::DragonBreath:
    case ProjectileRecipe::GenericFireTrail:
        return makeAbgr(255, 120, 32, 220);
    case ProjectileRecipe::Starburst:
        return makeAbgr(255, 244, 180, 220);
    case ProjectileRecipe::Implosion:
        return makeAbgr(176, 216, 255, 208);
    case ProjectileRecipe::Sparks:
        return makeAbgr(255, 220, 90, 216);
    case ProjectileRecipe::LightningBolt:
        return makeAbgr(255, 220, 90, 220);
    case ProjectileRecipe::IceBolt:
        return makeAbgr(180, 220, 255, 210);
    case ProjectileRecipe::PoisonSpray:
    case ProjectileRecipe::AcidBurst:
    case ProjectileRecipe::ToxicCloud:
    case ProjectileRecipe::GenericParticleTrail:
        return makeAbgr(96, 220, 128, 210);
    case ProjectileRecipe::LightBolt:
        return makeAbgr(255, 255, 220, 220);
    case ProjectileRecipe::DarkFireBolt:
        return makeAbgr(180, 96, 255, 220);
    case ProjectileRecipe::GenericLineTrail:
        return makeAbgr(220, 220, 220, 200);
    case ProjectileRecipe::None:
    default:
        return makeAbgr(255, 255, 255, 180);
    }
}

float projectileRecipeGlowRadius(ProjectileRecipe recipe)
{
    switch (recipe)
    {
    case ProjectileRecipe::Fireball:
    case ProjectileRecipe::DragonBreath:
        return 224.0f;
    case ProjectileRecipe::MeteorShower:
        return 176.0f;
    case ProjectileRecipe::Cannonball:
        return 192.0f;
    case ProjectileRecipe::Starburst:
        return 192.0f;
    case ProjectileRecipe::Implosion:
        return 168.0f;
    case ProjectileRecipe::Sparks:
        return 112.0f;
    case ProjectileRecipe::LightBolt:
    case ProjectileRecipe::LightningBolt:
        return 176.0f;
    case ProjectileRecipe::IceBolt:
    case ProjectileRecipe::DarkFireBolt:
    case ProjectileRecipe::ToxicCloud:
        return 152.0f;
    case ProjectileRecipe::FireBolt:
    case ProjectileRecipe::PoisonSpray:
    case ProjectileRecipe::AcidBurst:
    case ProjectileRecipe::GenericFireTrail:
    case ProjectileRecipe::GenericParticleTrail:
    case ProjectileRecipe::GenericLineTrail:
        return 128.0f;
    case ProjectileRecipe::None:
    default:
        return 0.0f;
    }
}

float projectileRecipeAnchorOffset(ProjectileRecipe recipe, uint16_t radius, uint16_t height)
{
    const float baselineOffset =
        std::max(std::max(static_cast<float>(height) * 0.5f, static_cast<float>(radius) * 0.75f), 8.0f);

    switch (recipe)
    {
    case ProjectileRecipe::ToxicCloud:
        return std::max(baselineOffset, 36.0f);
    case ProjectileRecipe::Cannonball:
        return std::max(baselineOffset, 28.0f);
    case ProjectileRecipe::PoisonSpray:
    case ProjectileRecipe::AcidBurst:
        return std::max(baselineOffset, 20.0f);
    case ProjectileRecipe::DragonBreath:
        return std::max(baselineOffset, 18.0f);
    case ProjectileRecipe::MeteorShower:
    case ProjectileRecipe::Starburst:
        return std::max(baselineOffset, 16.0f);
    case ProjectileRecipe::Fireball:
        return std::max(baselineOffset, 14.0f);
    case ProjectileRecipe::IceBolt:
    case ProjectileRecipe::LightBolt:
    case ProjectileRecipe::Sparks:
    case ProjectileRecipe::LightningBolt:
    case ProjectileRecipe::DarkFireBolt:
    case ProjectileRecipe::FireBolt:
    case ProjectileRecipe::GenericFireTrail:
    case ProjectileRecipe::GenericParticleTrail:
    case ProjectileRecipe::GenericLineTrail:
    case ProjectileRecipe::None:
    default:
        return baselineOffset;
    }
}

float projectileRecipeBackOffset(ProjectileRecipe recipe, uint16_t radius)
{
    const float radiusHalfOffset = std::max(static_cast<float>(radius) * 0.5f, 0.0f);

    switch (recipe)
    {
    case ProjectileRecipe::ToxicCloud:
    case ProjectileRecipe::PoisonSpray:
    case ProjectileRecipe::AcidBurst:
        return radiusHalfOffset;
    case ProjectileRecipe::Cannonball:
        return 0.0f;
    case ProjectileRecipe::DragonBreath:
        return 8.0f;
    case ProjectileRecipe::MeteorShower:
    case ProjectileRecipe::Starburst:
    case ProjectileRecipe::Implosion:
        return 3.0f;
    case ProjectileRecipe::Fireball:
        return 6.0f;
    case ProjectileRecipe::FireBolt:
    case ProjectileRecipe::Sparks:
    case ProjectileRecipe::LightningBolt:
    case ProjectileRecipe::IceBolt:
    case ProjectileRecipe::LightBolt:
    case ProjectileRecipe::DarkFireBolt:
    case ProjectileRecipe::GenericFireTrail:
    case ProjectileRecipe::GenericParticleTrail:
    case ProjectileRecipe::GenericLineTrail:
    case ProjectileRecipe::None:
    default:
        return 0.0f;
    }
}

bool projectileRecipeUsesDedicatedImpactFx(ProjectileRecipe recipe)
{
    return recipe != ProjectileRecipe::None;
}

void spawnProjectileTrailParticles(
    ParticleSystem &particleSystem,
    const ProjectileSpawnContext &context,
    ProjectileRecipe recipe)
{
    const SpellId spellId = spellIdFromValue(static_cast<uint32_t>(context.spellId));

    if (spellId == SpellId::MindBlast
        || spellId == SpellId::PsychicShock
        || spellId == SpellId::Harm
        || spellId == SpellId::Sparks
        || spellId == SpellId::ToxicCloud
        || spellId == SpellId::Incinerate)
    {
        return;
    }

    const float velocityLength = std::sqrt(
        context.velocityX * context.velocityX
        + context.velocityY * context.velocityY
        + context.velocityZ * context.velocityZ);
    float directionX = 0.0f;
    float directionY = 0.0f;
    float directionZ = 1.0f;

    if (velocityLength > 0.001f)
    {
        directionX = context.velocityX / velocityLength;
        directionY = context.velocityY / velocityLength;
        directionZ = context.velocityZ / velocityLength;
    }

    const bool affectedByGravity = (context.objectFlags & ObjectDescNoGravity) == 0;

    const auto applyGravityTrailTuning =
        [affectedByGravity](LayerRecipe &layer)
        {
            if (!affectedByGravity)
            {
                return;
            }

            layer.startOffset *= 0.72f;
            layer.offsetStep *= 0.74f;
            layer.inheritedVelocity *= 0.30f;
            layer.lifetimeSeconds *= 0.86f;
            layer.drag = std::max(layer.drag, 0.1f) * 1.35f;
            layer.motion = FxParticleMotion::BallisticTrail;
        };

    const uint32_t colorAbgr = projectileRecipeColorAbgr(recipe);
    const uint32_t baseSeed = context.projectileId * 2246822519u;

    if (recipe == ProjectileRecipe::Cannonball)
    {
        LayerRecipe emberTrail = {};
        emberTrail.startColorAbgr = makeAbgr(92, 88, 80, 120);
        emberTrail.endColorAbgr = makeAbgr(120, 112, 104, 0);
        emberTrail.count = 2u;
        emberTrail.startOffset = 0.0f;
        emberTrail.offsetStep = 0.0f;
        emberTrail.lateralSpread = 0.9f;
        emberTrail.verticalSpread = 0.6f;
        emberTrail.inheritedVelocity = 0.24f;
        emberTrail.upwardVelocity = 0.0f;
        emberTrail.startSize = 9.0f;
        emberTrail.endSize = 12.0f;
        emberTrail.lifetimeSeconds = 0.28f;
        emberTrail.drag = 6.0f;
        emberTrail.rotationJitterRadians = 0.5f;
        emberTrail.angularVelocityRadians = 0.8f;
        emberTrail.stretch = 1.0f;
        emberTrail.fadeInSeconds = 0.06f;
        emberTrail.motion = FxParticleMotion::BallisticTrail;
        emberTrail.blendMode = FxParticleBlendMode::Alpha;
        emberTrail.alignment = FxParticleAlignment::CameraFacing;
        emberTrail.material = FxParticleMaterial::Smoke;
        emberTrail.tag = FxParticleTag::Trail;
        emitLayerParticles(
            particleSystem,
            baseSeed,
            context.x,
            context.y,
            context.z,
            directionX,
            directionY,
            directionZ,
            context.velocityX,
            context.velocityY,
            context.velocityZ,
            emberTrail);
        return;
    }

    if (recipe == ProjectileRecipe::FireBolt
        || recipe == ProjectileRecipe::Fireball
        || recipe == ProjectileRecipe::MeteorShower
        || recipe == ProjectileRecipe::DragonBreath
        || recipe == ProjectileRecipe::DarkFireBolt
        || (context.objectFlags & ObjectDescTrailFire) != 0)
    {
        LayerRecipe emberLayer = {};
        emberLayer.startColorAbgr = colorAbgr;
        emberLayer.endColorAbgr = makeAbgr(255, 180, 64, 0);
        emberLayer.count =
            recipe == ProjectileRecipe::Fireball || recipe == ProjectileRecipe::DragonBreath ? 10u
                : (recipe == ProjectileRecipe::MeteorShower ? 5u : 7u);
        emberLayer.startOffset = 7.0f;
        emberLayer.offsetStep = 5.8f;
        emberLayer.lateralSpread = 2.6f;
        emberLayer.verticalSpread = 1.4f;
        emberLayer.inheritedVelocity = 0.18f;
        emberLayer.upwardVelocity = 10.0f;
        emberLayer.startSize =
            recipe == ProjectileRecipe::Fireball || recipe == ProjectileRecipe::DragonBreath ? 9.0f
                : (recipe == ProjectileRecipe::MeteorShower ? 7.5f : 7.0f);
        emberLayer.endSize = emberLayer.startSize * 0.38f;
        emberLayer.lifetimeSeconds =
            recipe == ProjectileRecipe::Fireball || recipe == ProjectileRecipe::DragonBreath ? 0.36f
                : (recipe == ProjectileRecipe::MeteorShower ? 0.26f : 0.30f);
        emberLayer.drag = 4.5f;
        emberLayer.rotationJitterRadians = 0.5f;
        emberLayer.angularVelocityRadians = 4.0f;
        emberLayer.stretch = 1.0f;
        emberLayer.motion = FxParticleMotion::VelocityTrail;
        emberLayer.blendMode = FxParticleBlendMode::Additive;
        emberLayer.alignment = FxParticleAlignment::CameraFacing;
        emberLayer.material = FxParticleMaterial::HardBlob;
        emberLayer.tag = FxParticleTag::Trail;
        applyGravityTrailTuning(emberLayer);
        emitLayerParticles(
            particleSystem,
            baseSeed,
            context.x,
            context.y,
            context.z,
            directionX,
            directionY,
            directionZ,
            context.velocityX,
            context.velocityY,
            context.velocityZ,
            emberLayer);

        if (recipe == ProjectileRecipe::Cannonball)
        {
            return;
        }

        LayerRecipe smokeLayer = {};
        smokeLayer.startColorAbgr =
            recipe == ProjectileRecipe::DarkFireBolt ? makeAbgr(112, 72, 144, 96) : makeAbgr(84, 84, 84, 88);
        smokeLayer.endColorAbgr = makeAbgr(84, 84, 84, 0);
        smokeLayer.count =
            recipe == ProjectileRecipe::Fireball || recipe == ProjectileRecipe::DragonBreath ? 5u
                : (recipe == ProjectileRecipe::MeteorShower ? 2u : (recipe == ProjectileRecipe::Cannonball ? 4u : 3u));
        smokeLayer.startOffset =
            recipe == ProjectileRecipe::MeteorShower ? 5.0f : (recipe == ProjectileRecipe::Cannonball ? 6.0f : 10.0f);
        smokeLayer.offsetStep =
            recipe == ProjectileRecipe::MeteorShower ? 4.5f : (recipe == ProjectileRecipe::Cannonball ? 5.5f : 8.0f);
        smokeLayer.lateralSpread = 3.4f;
        smokeLayer.verticalSpread = 2.2f;
        smokeLayer.inheritedVelocity = recipe == ProjectileRecipe::Cannonball ? 0.03f : 0.06f;
        smokeLayer.upwardVelocity = recipe == ProjectileRecipe::Cannonball ? 6.0f : 14.0f;
        smokeLayer.startSize =
            recipe == ProjectileRecipe::DragonBreath ? 16.0f
                : (recipe == ProjectileRecipe::MeteorShower ? 10.0f
                    : (recipe == ProjectileRecipe::Cannonball ? 13.0f : 12.0f));
        smokeLayer.endSize = smokeLayer.startSize * 1.9f;
        smokeLayer.lifetimeSeconds =
            recipe == ProjectileRecipe::MeteorShower ? 0.30f : (recipe == ProjectileRecipe::Cannonball ? 0.42f : 0.48f);
        smokeLayer.drag = recipe == ProjectileRecipe::Cannonball ? 3.0f : 2.2f;
        smokeLayer.rotationJitterRadians = 0.9f;
        smokeLayer.angularVelocityRadians = 1.2f;
        smokeLayer.motion = FxParticleMotion::Drift;
        smokeLayer.blendMode = FxParticleBlendMode::Alpha;
        smokeLayer.alignment = FxParticleAlignment::CameraFacing;
        smokeLayer.material = FxParticleMaterial::Smoke;
        smokeLayer.tag = FxParticleTag::Trail;
        applyGravityTrailTuning(smokeLayer);
        emitLayerParticles(
            particleSystem,
            baseSeed ^ 0x9e3779b9u,
            context.x,
            context.y,
            context.z,
            directionX,
            directionY,
            directionZ,
            context.velocityX,
            context.velocityY,
            context.velocityZ,
            smokeLayer);
        return;
    }

    if (recipe == ProjectileRecipe::Starburst)
    {
        LayerRecipe sparkLayer = {};
        sparkLayer.startColorAbgr = colorAbgr;
        sparkLayer.endColorAbgr = makeAbgr(255, 255, 255, 0);
        sparkLayer.count = 6u;
        sparkLayer.startOffset = 3.5f;
        sparkLayer.offsetStep = 3.2f;
        sparkLayer.lateralSpread = 1.2f;
        sparkLayer.verticalSpread = 1.0f;
        sparkLayer.inheritedVelocity = 0.14f;
        sparkLayer.upwardVelocity = 0.0f;
        sparkLayer.startSize = 5.5f;
        sparkLayer.endSize = 2.0f;
        sparkLayer.lifetimeSeconds = 0.22f;
        sparkLayer.drag = 5.0f;
        sparkLayer.stretch = 1.0f;
        sparkLayer.motion = FxParticleMotion::VelocityTrail;
        sparkLayer.blendMode = FxParticleBlendMode::Additive;
        sparkLayer.alignment = FxParticleAlignment::CameraFacing;
        sparkLayer.material = FxParticleMaterial::SoftBlob;
        sparkLayer.tag = FxParticleTag::Trail;
        emitLayerParticles(
            particleSystem,
            baseSeed,
            context.x,
            context.y,
            context.z,
            directionX,
            directionY,
            directionZ,
            context.velocityX,
            context.velocityY,
            context.velocityZ,
            sparkLayer);

        LayerRecipe moteLayer = {};
        moteLayer.startColorAbgr = varyAlpha(colorAbgr, 0.75f);
        moteLayer.endColorAbgr = makeAbgr(255, 255, 255, 0);
        moteLayer.count = 3u;
        moteLayer.startOffset = 4.0f;
        moteLayer.offsetStep = 3.8f;
        moteLayer.lateralSpread = 1.6f;
        moteLayer.verticalSpread = 1.2f;
        moteLayer.inheritedVelocity = 0.10f;
        moteLayer.upwardVelocity = 1.0f;
        moteLayer.startSize = 6.0f;
        moteLayer.endSize = 2.8f;
        moteLayer.lifetimeSeconds = 0.24f;
        moteLayer.drag = 4.4f;
        moteLayer.motion = FxParticleMotion::VelocityTrail;
        moteLayer.blendMode = FxParticleBlendMode::Additive;
        moteLayer.alignment = FxParticleAlignment::CameraFacing;
        moteLayer.material = FxParticleMaterial::SoftBlob;
        moteLayer.tag = FxParticleTag::Trail;
        emitLayerParticles(
            particleSystem,
            baseSeed ^ 0x3c6ef372u,
            context.x,
            context.y,
            context.z,
            directionX,
            directionY,
            directionZ,
            context.velocityX,
            context.velocityY,
            context.velocityZ,
            moteLayer);
        return;
    }

    if (recipe == ProjectileRecipe::Sparks
        || recipe == ProjectileRecipe::LightningBolt
        || recipe == ProjectileRecipe::GenericLineTrail
        || (context.objectFlags & ObjectDescTrailLine) != 0)
    {
        LayerRecipe sparkLayer = {};
        sparkLayer.startColorAbgr = colorAbgr;
        sparkLayer.endColorAbgr = makeAbgr(255, 255, 220, 0);
        sparkLayer.count = recipe == ProjectileRecipe::GenericLineTrail ? 4u
            : (recipe == ProjectileRecipe::Sparks ? 2u : 8u);
        sparkLayer.startOffset = 5.0f;
        sparkLayer.offsetStep = 3.6f;
        sparkLayer.lateralSpread = 1.2f;
        sparkLayer.verticalSpread = 1.0f;
        sparkLayer.inheritedVelocity = 0.28f;
        sparkLayer.startSize = recipe == ProjectileRecipe::GenericLineTrail ? 4.0f
            : (recipe == ProjectileRecipe::Sparks ? 4.6f : 5.5f);
        sparkLayer.endSize = 1.8f;
        sparkLayer.lifetimeSeconds = recipe == ProjectileRecipe::Sparks ? 0.10f : 0.16f;
        sparkLayer.drag = 8.0f;
        sparkLayer.stretch = 2.4f;
        sparkLayer.motion = FxParticleMotion::VelocityTrail;
        sparkLayer.blendMode = FxParticleBlendMode::Additive;
        sparkLayer.alignment = FxParticleAlignment::VelocityStretched;
        sparkLayer.material = FxParticleMaterial::Spark;
        sparkLayer.tag = FxParticleTag::Trail;
        applyGravityTrailTuning(sparkLayer);
        emitLayerParticles(
            particleSystem,
            baseSeed,
            context.x,
            context.y,
            context.z,
            directionX,
            directionY,
            directionZ,
            context.velocityX,
            context.velocityY,
            context.velocityZ,
            sparkLayer);
        return;
    }

    if (recipe == ProjectileRecipe::IceBolt || recipe == ProjectileRecipe::LightBolt)
    {
        LayerRecipe moteLayer = {};
        moteLayer.startColorAbgr = colorAbgr;
        moteLayer.endColorAbgr = makeAbgr(255, 255, 255, 0);
        moteLayer.count = recipe == ProjectileRecipe::LightBolt ? 6u : 7u;
        moteLayer.startOffset = 6.0f;
        moteLayer.offsetStep = 4.6f;
        moteLayer.lateralSpread = 1.9f;
        moteLayer.verticalSpread = 1.2f;
        moteLayer.inheritedVelocity = 0.20f;
        moteLayer.upwardVelocity = 3.0f;
        moteLayer.startSize = recipe == ProjectileRecipe::LightBolt ? 6.0f : 6.8f;
        moteLayer.endSize = 2.6f;
        moteLayer.lifetimeSeconds = recipe == ProjectileRecipe::LightBolt ? 0.20f : 0.24f;
        moteLayer.drag = 5.5f;
        moteLayer.rotationJitterRadians = 0.4f;
        moteLayer.angularVelocityRadians = 2.0f;
        moteLayer.motion = FxParticleMotion::VelocityTrail;
        moteLayer.blendMode = FxParticleBlendMode::Additive;
        moteLayer.alignment = FxParticleAlignment::CameraFacing;
        moteLayer.material = recipe == ProjectileRecipe::LightBolt ? FxParticleMaterial::SoftBlob
            : FxParticleMaterial::HardBlob;
        moteLayer.tag = FxParticleTag::Trail;
        applyGravityTrailTuning(moteLayer);
        emitLayerParticles(
            particleSystem,
            baseSeed,
            context.x,
            context.y,
            context.z,
            directionX,
            directionY,
            directionZ,
            context.velocityX,
            context.velocityY,
            context.velocityZ,
            moteLayer);

        if (recipe == ProjectileRecipe::IceBolt)
        {
            LayerRecipe mistLayer = {};
            mistLayer.startColorAbgr = makeAbgr(180, 220, 255, 84);
            mistLayer.endColorAbgr = makeAbgr(200, 230, 255, 0);
            mistLayer.count = 3u;
            mistLayer.startOffset = 8.0f;
            mistLayer.offsetStep = 6.8f;
            mistLayer.lateralSpread = 2.8f;
            mistLayer.verticalSpread = 1.8f;
            mistLayer.inheritedVelocity = 0.08f;
            mistLayer.upwardVelocity = 5.0f;
            mistLayer.startSize = 10.0f;
            mistLayer.endSize = 16.0f;
            mistLayer.lifetimeSeconds = 0.34f;
            mistLayer.drag = 2.6f;
            mistLayer.rotationJitterRadians = 0.8f;
            mistLayer.angularVelocityRadians = 0.7f;
            mistLayer.motion = FxParticleMotion::Drift;
            mistLayer.blendMode = FxParticleBlendMode::Alpha;
            mistLayer.alignment = FxParticleAlignment::CameraFacing;
            mistLayer.material = FxParticleMaterial::Mist;
            mistLayer.tag = FxParticleTag::Trail;
            applyGravityTrailTuning(mistLayer);
            emitLayerParticles(
                particleSystem,
                baseSeed ^ 0x3c6ef372u,
                context.x,
                context.y,
                context.z,
                directionX,
                directionY,
                directionZ,
                context.velocityX,
                context.velocityY,
                context.velocityZ,
                mistLayer);
        }

        return;
    }

    if (recipe == ProjectileRecipe::PoisonSpray
        || recipe == ProjectileRecipe::AcidBurst
        || recipe == ProjectileRecipe::ToxicCloud
        || recipe == ProjectileRecipe::GenericParticleTrail
        || (context.objectFlags & ObjectDescTrailParticle) != 0)
    {
        LayerRecipe hazeLayer = {};
        hazeLayer.startColorAbgr = colorAbgr;
        hazeLayer.endColorAbgr = makeAbgr(96, 220, 128, 0);
        hazeLayer.count = recipe == ProjectileRecipe::ToxicCloud ? 7u : 5u;
        hazeLayer.startOffset = recipe == ProjectileRecipe::ToxicCloud ? 4.0f : 8.0f;
        hazeLayer.offsetStep = recipe == ProjectileRecipe::ToxicCloud ? 7.0f : 6.4f;
        hazeLayer.lateralSpread = 3.8f;
        hazeLayer.verticalSpread = 2.4f;
        hazeLayer.inheritedVelocity = 0.10f;
        hazeLayer.upwardVelocity = 8.0f;
        hazeLayer.startSize = recipe == ProjectileRecipe::ToxicCloud ? 12.0f : 9.0f;
        hazeLayer.endSize = hazeLayer.startSize * 1.8f;
        hazeLayer.lifetimeSeconds = recipe == ProjectileRecipe::ToxicCloud ? 0.50f : 0.36f;
        hazeLayer.drag = 2.4f;
        hazeLayer.rotationJitterRadians = 0.9f;
        hazeLayer.angularVelocityRadians = 0.9f;
        hazeLayer.motion = FxParticleMotion::Drift;
        hazeLayer.blendMode = FxParticleBlendMode::Alpha;
        hazeLayer.alignment = FxParticleAlignment::CameraFacing;
        hazeLayer.material = FxParticleMaterial::Mist;
        hazeLayer.tag = FxParticleTag::Trail;
        applyGravityTrailTuning(hazeLayer);
        emitLayerParticles(
            particleSystem,
            baseSeed,
            context.x,
            context.y,
            context.z,
            directionX,
            directionY,
            directionZ,
            context.velocityX,
            context.velocityY,
            context.velocityZ,
            hazeLayer);

        LayerRecipe moteLayer = {};
        moteLayer.startColorAbgr = varyAlpha(colorAbgr, 0.85f);
        moteLayer.endColorAbgr = makeAbgr(160, 255, 180, 0);
        moteLayer.count = 3u;
        moteLayer.startOffset = recipe == ProjectileRecipe::ToxicCloud ? 3.0f : 6.0f;
        moteLayer.offsetStep = recipe == ProjectileRecipe::ToxicCloud ? 5.2f : 4.8f;
        moteLayer.lateralSpread = 2.1f;
        moteLayer.verticalSpread = 1.2f;
        moteLayer.inheritedVelocity = 0.16f;
        moteLayer.upwardVelocity = 3.0f;
        moteLayer.startSize = recipe == ProjectileRecipe::ToxicCloud ? 6.0f : 5.5f;
        moteLayer.endSize = 2.2f;
        moteLayer.lifetimeSeconds = recipe == ProjectileRecipe::ToxicCloud ? 0.28f : 0.24f;
        moteLayer.drag = 4.8f;
        moteLayer.stretch = 1.2f;
        moteLayer.motion = FxParticleMotion::VelocityTrail;
        moteLayer.blendMode = FxParticleBlendMode::Additive;
        moteLayer.alignment = FxParticleAlignment::CameraFacing;
        moteLayer.material = FxParticleMaterial::SoftBlob;
        moteLayer.tag = FxParticleTag::Trail;
        applyGravityTrailTuning(moteLayer);
        emitLayerParticles(
            particleSystem,
            baseSeed ^ 0xbb67ae85u,
            context.x,
            context.y,
            context.z,
            directionX,
            directionY,
            directionZ,
            context.velocityX,
            context.velocityY,
            context.velocityZ,
            moteLayer);
    }
}

void spawnImpactParticles(ParticleSystem &particleSystem, const ImpactSpawnContext &context)
{
    const ProjectileRecipe recipe = context.recipe;
    const uint32_t colorAbgr =
        recipe != ProjectileRecipe::None ? projectileRecipeColorAbgr(recipe)
            : deriveImpactColorAbgr(context.objectName, context.spriteName);
    const bool isFire =
        recipe == ProjectileRecipe::FireBolt
        || recipe == ProjectileRecipe::Fireball
        || recipe == ProjectileRecipe::MeteorShower
        || recipe == ProjectileRecipe::Cannonball
        || recipe == ProjectileRecipe::DragonBreath
        || recipe == ProjectileRecipe::DarkFireBolt
        || recipe == ProjectileRecipe::GenericFireTrail
        || (recipe == ProjectileRecipe::None
            && (containsToken(context.objectName, "fire")
                || containsToken(context.objectName, "dragon breath")
                || containsToken(context.spriteName, "fire")));
    const bool isFireBolt = recipe == ProjectileRecipe::FireBolt;
    const bool isFireballFamily =
        recipe == ProjectileRecipe::Fireball
        || recipe == ProjectileRecipe::MeteorShower
        || recipe == ProjectileRecipe::DragonBreath
        || recipe == ProjectileRecipe::DarkFireBolt;
    const bool isLightning =
        recipe == ProjectileRecipe::Sparks
        || recipe == ProjectileRecipe::LightningBolt
        || recipe == ProjectileRecipe::GenericLineTrail
        || (recipe == ProjectileRecipe::None
            && (containsToken(context.objectName, "lightning")
                || containsToken(context.spriteName, "spark")
                || containsToken(context.objectName, "laser")));
    const bool isPoison =
        recipe == ProjectileRecipe::PoisonSpray
        || recipe == ProjectileRecipe::AcidBurst
        || recipe == ProjectileRecipe::ToxicCloud
        || recipe == ProjectileRecipe::GenericParticleTrail
        || (recipe == ProjectileRecipe::None
            && (containsToken(context.objectName, "poison")
                || containsToken(context.objectName, "acid")
                || containsToken(context.objectName, "toxic")));
    const bool isLight =
        recipe == ProjectileRecipe::LightBolt
        || recipe == ProjectileRecipe::Starburst
        || (recipe == ProjectileRecipe::None
            && (containsToken(context.objectName, "light bolt")
                || containsToken(context.objectName, "sunray")
                || containsToken(context.objectName, "prismatic")));
    const bool isImplosion = recipe == ProjectileRecipe::Implosion;
    const bool isIce =
        recipe == ProjectileRecipe::IceBolt
        || (recipe == ProjectileRecipe::None
            && (containsToken(context.objectName, "ice")
                || containsToken(context.objectName, "frost")
                || containsToken(context.spriteName, "ice")));
    const bool isIceBolt = recipe == ProjectileRecipe::IceBolt;
    const bool isCannonball = recipe == ProjectileRecipe::Cannonball;
    const uint32_t baseSeed = static_cast<uint32_t>(std::hash<std::string>{}(context.objectName + context.spriteName));

    const auto emitCoreFlash =
        [&](uint32_t count, float startSize, float velocityScale, float stretch)
        {
            for (uint32_t particleIndex = 0; particleIndex < count; ++particleIndex)
            {
                emitBurstParticle(
                    particleSystem,
                    context.x,
                    context.y,
                    context.z + 10.0f,
                    startSize + static_cast<float>(particleIndex % 3u) * 1.5f,
                    colorAbgr,
                    varyAlpha(colorAbgr, 0.0f),
                    velocityScale + static_cast<float>(particleIndex % 5u) * 8.0f,
                    baseSeed ^ (particleIndex * 2654435761u),
                    FxParticleMaterial::SoftBlob,
                    FxParticleAlignment::CameraFacing,
                    stretch);
            }
        };

    const auto emitSparkSplash =
        [&](uint32_t count, float startSize, float velocityScale, uint32_t startSeed)
        {
            for (uint32_t particleIndex = 0; particleIndex < count; ++particleIndex)
            {
                emitBurstParticle(
                    particleSystem,
                    context.x,
                    context.y,
                    context.z + 12.0f,
                    startSize + static_cast<float>(particleIndex % 2u) * 1.5f,
                    colorAbgr,
                    varyAlpha(colorAbgr, 0.0f),
                    velocityScale + static_cast<float>(particleIndex % 4u) * 12.0f,
                    startSeed ^ (particleIndex * 2246822519u),
                    FxParticleMaterial::Spark,
                    FxParticleAlignment::VelocityStretched,
                    2.1f);
            }
        };

    const auto emitRoundSplash =
        [&](uint32_t count, float startSize, float velocityScale, uint32_t startSeed)
        {
            for (uint32_t particleIndex = 0; particleIndex < count; ++particleIndex)
            {
                emitBurstParticle(
                    particleSystem,
                    context.x,
                    context.y,
                    context.z + 12.0f,
                    startSize + static_cast<float>(particleIndex % 2u) * 1.5f,
                    colorAbgr,
                    varyAlpha(colorAbgr, 0.0f),
                    velocityScale + static_cast<float>(particleIndex % 4u) * 12.0f,
                    startSeed ^ (particleIndex * 2246822519u),
                    FxParticleMaterial::HardBlob,
                    FxParticleAlignment::CameraFacing,
                    1.0f);
            }
        };

    const auto emitSoftCloud =
        [&](uint32_t startColor,
            uint32_t endColor,
            uint32_t count,
            float startSize,
            float endSize,
            float lifetimeSeconds,
            float upwardVelocity,
            FxParticleMaterial material)
        {
            LayerRecipe cloudLayer = {};
            cloudLayer.startColorAbgr = startColor;
            cloudLayer.endColorAbgr = endColor;
            cloudLayer.count = count;
            cloudLayer.startOffset = 0.0f;
            cloudLayer.offsetStep = 2.5f;
            cloudLayer.lateralSpread = 9.0f;
            cloudLayer.verticalSpread = 5.0f;
            cloudLayer.inheritedVelocity = 0.0f;
            cloudLayer.upwardVelocity = upwardVelocity;
            cloudLayer.startSize = startSize;
            cloudLayer.endSize = endSize;
            cloudLayer.lifetimeSeconds = lifetimeSeconds;
            cloudLayer.drag = 2.2f;
            cloudLayer.rotationJitterRadians = 0.9f;
            cloudLayer.angularVelocityRadians = 0.8f;
            cloudLayer.motion = FxParticleMotion::Drift;
            cloudLayer.blendMode = FxParticleBlendMode::Alpha;
            cloudLayer.alignment = FxParticleAlignment::CameraFacing;
            cloudLayer.material = material;
            cloudLayer.tag = FxParticleTag::Impact;
            emitLayerParticles(
                particleSystem,
                baseSeed ^ 0x9e3779b9u,
                context.x,
                context.y,
                context.z + 6.0f,
                0.0f,
                0.0f,
                1.0f,
                0.0f,
                0.0f,
                0.0f,
                cloudLayer);
        };

    const auto emitEmberSplash =
        [&](uint32_t count, float startSize, float velocityScale)
        {
            for (uint32_t particleIndex = 0; particleIndex < count; ++particleIndex)
            {
                emitBurstParticle(
                    particleSystem,
                    context.x,
                    context.y,
                    context.z + 10.0f,
                    startSize + static_cast<float>(particleIndex % 3u) * 1.8f,
                    colorAbgr,
                    varyAlpha(colorAbgr, 0.0f),
                    velocityScale + static_cast<float>(particleIndex % 4u) * 14.0f,
                    baseSeed ^ 0x7f4a7c15u ^ (particleIndex * 3266489917u),
                    FxParticleMaterial::HardBlob,
                    FxParticleAlignment::CameraFacing,
                    1.0f);
            }
        };

    if (isLightning)
    {
        emitCoreFlash(14u, 8.0f, 72.0f, 1.0f);
        emitSparkSplash(18u, 6.0f, 128.0f, baseSeed ^ 0x51ed270bu);
        return;
    }

    if (isLight)
    {
        const bool isStarburst = recipe == ProjectileRecipe::Starburst;
        emitCoreFlash(
            isStarburst ? 22u : 16u,
            isStarburst ? 11.0f : 9.0f,
            isStarburst ? 96.0f : 78.0f,
            1.0f);
        emitRoundSplash(
            isStarburst ? 16u : 10u,
            isStarburst ? 6.5f : 5.0f,
            isStarburst ? 116.0f : 92.0f,
            baseSeed ^ 0xa24baed4u);
        if (isStarburst)
        {
            emitCoreFlash(8u, 7.5f, 74.0f, 1.0f);
        }
        return;
    }

    if (isImplosion)
    {
        emitCoreFlash(18u, 14.0f, 42.0f, 1.0f);
        emitCoreFlash(10u, 10.0f, 26.0f, 1.0f);

        emitSoftCloud(
            makeAbgr(176, 216, 255, 104),
            makeAbgr(216, 236, 255, 0),
            10u,
            18.0f,
            46.0f,
            0.52f,
            12.0f,
            FxParticleMaterial::Mist);

        LayerRecipe moteLayer = {};
        moteLayer.startColorAbgr = makeAbgr(192, 224, 255, 132);
        moteLayer.endColorAbgr = makeAbgr(224, 240, 255, 0);
        moteLayer.count = 8u;
        moteLayer.startOffset = 0.0f;
        moteLayer.offsetStep = 1.4f;
        moteLayer.lateralSpread = 10.0f;
        moteLayer.verticalSpread = 10.0f;
        moteLayer.inheritedVelocity = 0.0f;
        moteLayer.upwardVelocity = 4.0f;
        moteLayer.startSize = 9.0f;
        moteLayer.endSize = 3.0f;
        moteLayer.lifetimeSeconds = 0.36f;
        moteLayer.drag = 4.2f;
        moteLayer.rotationJitterRadians = 0.8f;
        moteLayer.angularVelocityRadians = 1.2f;
        moteLayer.motion = FxParticleMotion::Burst;
        moteLayer.blendMode = FxParticleBlendMode::Additive;
        moteLayer.alignment = FxParticleAlignment::CameraFacing;
        moteLayer.material = FxParticleMaterial::SoftBlob;
        moteLayer.tag = FxParticleTag::Impact;
        emitLayerParticles(
            particleSystem,
            baseSeed ^ 0x1f83d9abu,
            context.x,
            context.y,
            context.z + 12.0f,
            0.0f,
            0.0f,
            1.0f,
            0.0f,
            0.0f,
            0.0f,
            moteLayer);
        return;
    }

    if (isFire || isCannonball)
    {
        const bool isMeteorShower = recipe == ProjectileRecipe::MeteorShower;
        const uint32_t coreCount = isCannonball ? 16u : (isFireBolt ? 20u : (isMeteorShower ? 18u : 18u));
        const float coreSize = isCannonball ? 10.0f : (isFireBolt ? 10.5f : (isMeteorShower ? 10.5f : 11.0f));
        const float coreVelocity = isCannonball ? 68.0f : (isFireBolt ? 92.0f : (isMeteorShower ? 94.0f : 84.0f));
        const uint32_t emberCount = isCannonball ? 16u : (isFireBolt ? 24u : (isMeteorShower ? 22u : 22u));
        const float emberSize = isCannonball ? 9.0f : (isFireBolt ? 7.2f : (isMeteorShower ? 7.4f : 8.0f));
        const float emberVelocity = isCannonball ? 92.0f : (isFireBolt ? 120.0f : (isMeteorShower ? 106.0f : 104.0f));
        const uint32_t sparkCount = isCannonball ? 6u : (isFireBolt ? 12u : (isMeteorShower ? 10u : 8u));
        const float sparkVelocity = isCannonball ? 74.0f : (isFireBolt ? 98.0f : (isMeteorShower ? 90.0f : 86.0f));

        emitCoreFlash(coreCount, coreSize, coreVelocity, 1.0f);
        emitEmberSplash(emberCount, emberSize, emberVelocity);
        emitRoundSplash(sparkCount, isFireBolt ? 4.0f : 4.5f, sparkVelocity, baseSeed ^ 0x3c6ef372u);
        emitSoftCloud(
            isCannonball ? makeAbgr(96, 88, 72, 96) : makeAbgr(96, 84, 84, 92),
            makeAbgr(255, 255, 255, 0),
            isCannonball ? 7u : (isFireBolt ? 5u : (isMeteorShower ? 7u : 6u)),
            isCannonball ? 17.0f : (isFireBolt ? 13.0f : (isMeteorShower ? 14.0f : 15.0f)),
            isCannonball ? 34.0f : (isFireBolt ? 24.0f : (isMeteorShower ? 28.0f : 28.0f)),
            isCannonball ? 0.48f : (isFireBolt ? 0.28f : (isMeteorShower ? 0.34f : 0.38f)),
            isCannonball ? 12.0f : (isFireBolt ? 12.0f : (isMeteorShower ? 14.0f : 16.0f)),
            FxParticleMaterial::Smoke);

        if (isFireBolt)
        {
            emitCoreFlash(10u, 6.0f, 74.0f, 1.0f);
        }

        if (isMeteorShower)
        {
            emitCoreFlash(8u, 7.0f, 70.0f, 1.0f);
        }

        return;
    }

    if (isIce)
    {
        emitCoreFlash(isIceBolt ? 18u : 13u, isIceBolt ? 9.5f : 8.5f, isIceBolt ? 82.0f : 66.0f, 1.0f);
        emitRoundSplash(
            isIceBolt ? 12u : 8u,
            isIceBolt ? 5.8f : 5.0f,
            isIceBolt ? 90.0f : 78.0f,
            baseSeed ^ 0xbb67ae85u);
        emitSoftCloud(
            makeAbgr(200, 228, 255, isIceBolt ? 96 : 88),
            makeAbgr(255, 255, 255, 0),
            isIceBolt ? 6u : 5u,
            isIceBolt ? 14.0f : 13.0f,
            isIceBolt ? 28.0f : 24.0f,
            isIceBolt ? 0.34f : 0.30f,
            isIceBolt ? 10.0f : 8.0f,
            FxParticleMaterial::Mist);
        return;
    }

    if (isPoison)
    {
        emitCoreFlash(10u, 7.5f, 54.0f, 1.0f);
        emitSoftCloud(
            makeAbgr(96, 180, 96, 92),
            makeAbgr(160, 255, 180, 0),
            7u,
            14.0f,
            30.0f,
            0.42f,
            10.0f,
            FxParticleMaterial::Mist);

        LayerRecipe moteLayer = {};
        moteLayer.startColorAbgr = varyAlpha(colorAbgr, 0.95f);
        moteLayer.endColorAbgr = makeAbgr(160, 255, 180, 0);
        moteLayer.count = 8u;
        moteLayer.startOffset = 0.0f;
        moteLayer.offsetStep = 1.8f;
        moteLayer.lateralSpread = 6.5f;
        moteLayer.verticalSpread = 3.0f;
        moteLayer.inheritedVelocity = 0.0f;
        moteLayer.upwardVelocity = 6.0f;
        moteLayer.startSize = 6.0f;
        moteLayer.endSize = 2.0f;
        moteLayer.lifetimeSeconds = 0.24f;
        moteLayer.drag = 4.6f;
        moteLayer.rotationJitterRadians = 0.5f;
        moteLayer.angularVelocityRadians = 1.6f;
        moteLayer.motion = FxParticleMotion::Burst;
        moteLayer.blendMode = FxParticleBlendMode::Additive;
        moteLayer.alignment = FxParticleAlignment::CameraFacing;
        moteLayer.material = FxParticleMaterial::SoftBlob;
        moteLayer.tag = FxParticleTag::Impact;
        emitLayerParticles(
            particleSystem,
            baseSeed ^ 0x6a09e667u,
            context.x,
            context.y,
            context.z + 10.0f,
            0.0f,
            0.0f,
            1.0f,
            0.0f,
            0.0f,
            0.0f,
            moteLayer);
        return;
    }

    emitCoreFlash(12u, 8.0f, 68.0f, 1.0f);
    emitRoundSplash(6u, 4.5f, 72.0f, baseSeed ^ 0x243f6a88u);
}

void spawnDecorationFireParticles(
    ParticleSystem &particleSystem,
    uint32_t seed,
    float x,
    float y,
    float z,
    float emitterRadius)
{
    LayerRecipe emberLayer = {};
    emberLayer.startColorAbgr = makeAbgr(255, 128, 40, 232);
    emberLayer.endColorAbgr = makeAbgr(255, 188, 108, 0);
    emberLayer.count = 4u;
    emberLayer.startOffset = 0.0f;
    emberLayer.offsetStep = 1.4f;
    emberLayer.lateralSpread = std::max(5.5f, emitterRadius * 0.12f);
    emberLayer.verticalSpread = 2.5f;
    emberLayer.upwardVelocity = 28.0f;
    emberLayer.startSize = std::max(12.0f, emitterRadius * 0.16f);
    emberLayer.endSize = emberLayer.startSize * 0.45f;
    emberLayer.lifetimeSeconds = 0.30f;
    emberLayer.drag = 3.4f;
    emberLayer.rotationJitterRadians = 0.65f;
    emberLayer.angularVelocityRadians = 4.8f;
    emberLayer.motion = FxParticleMotion::Ascend;
    emberLayer.blendMode = FxParticleBlendMode::Additive;
    emberLayer.alignment = FxParticleAlignment::CameraFacing;
    emberLayer.material = FxParticleMaterial::Ember;
    emberLayer.tag = FxParticleTag::DecorationEmitter;
    emitLayerParticles(
        particleSystem,
        seed,
        x,
        y,
        z,
        0.0f,
        0.0f,
        1.0f,
        0.0f,
        0.0f,
        0.0f,
        emberLayer);

    LayerRecipe glowLayer = {};
    glowLayer.startColorAbgr = makeAbgr(255, 168, 72, 104);
    glowLayer.endColorAbgr = makeAbgr(255, 210, 132, 0);
    glowLayer.count = 2u;
    glowLayer.lateralSpread = std::max(4.0f, emitterRadius * 0.10f);
    glowLayer.verticalSpread = 2.0f;
    glowLayer.upwardVelocity = 10.0f;
    glowLayer.startSize = std::max(14.0f, emitterRadius * 0.20f);
    glowLayer.endSize = glowLayer.startSize * 1.55f;
    glowLayer.lifetimeSeconds = 0.22f;
    glowLayer.drag = 2.2f;
    glowLayer.rotationJitterRadians = 0.35f;
    glowLayer.angularVelocityRadians = 1.2f;
    glowLayer.motion = FxParticleMotion::Ascend;
    glowLayer.blendMode = FxParticleBlendMode::Additive;
    glowLayer.alignment = FxParticleAlignment::CameraFacing;
    glowLayer.material = FxParticleMaterial::SoftBlob;
    glowLayer.tag = FxParticleTag::DecorationEmitter;
    emitLayerParticles(
        particleSystem,
        seed ^ 0x51ed270bu,
        x,
        y,
        z,
        0.0f,
        0.0f,
        1.0f,
        0.0f,
        0.0f,
        0.0f,
        glowLayer);

    LayerRecipe smokeLayer = {};
    smokeLayer.startColorAbgr = makeAbgr(96, 96, 96, 78);
    smokeLayer.endColorAbgr = makeAbgr(88, 88, 88, 0);
    smokeLayer.count = 2u;
    smokeLayer.lateralSpread = std::max(4.0f, emitterRadius * 0.09f);
    smokeLayer.verticalSpread = 3.0f;
    smokeLayer.upwardVelocity = 18.0f;
    smokeLayer.startSize = std::max(14.0f, emitterRadius * 0.20f);
    smokeLayer.endSize = smokeLayer.startSize * 1.8f;
    smokeLayer.lifetimeSeconds = 0.68f;
    smokeLayer.drag = 1.4f;
    smokeLayer.rotationJitterRadians = 1.0f;
    smokeLayer.angularVelocityRadians = 1.2f;
    smokeLayer.motion = FxParticleMotion::Drift;
    smokeLayer.blendMode = FxParticleBlendMode::Alpha;
    smokeLayer.alignment = FxParticleAlignment::CameraFacing;
    smokeLayer.material = FxParticleMaterial::Smoke;
    smokeLayer.tag = FxParticleTag::DecorationEmitter;
    emitLayerParticles(
        particleSystem,
        seed ^ 0x9e3779b9u,
        x,
        y,
        z,
        0.0f,
        0.0f,
        1.0f,
        0.0f,
        0.0f,
        0.0f,
        smokeLayer);
}

void spawnDecorationSmokeParticles(
    ParticleSystem &particleSystem,
    uint32_t seed,
    float x,
    float y,
    float z,
    float emitterRadius)
{
    LayerRecipe smokeLayer = {};
    smokeLayer.startColorAbgr = makeAbgr(208, 208, 208, 88);
    smokeLayer.endColorAbgr = makeAbgr(168, 168, 168, 0);
    smokeLayer.count = 1u;
    smokeLayer.lateralSpread = std::max(9.0f, emitterRadius * 0.26f);
    smokeLayer.verticalSpread = 10.0f;
    smokeLayer.upwardVelocity = 112.0f;
    smokeLayer.startSize = std::max(24.0f, emitterRadius * 0.78f);
    smokeLayer.endSize = smokeLayer.startSize * 3.0f;
    smokeLayer.lifetimeSeconds = 2.60f;
    smokeLayer.drag = 0.18f;
    smokeLayer.rotationJitterRadians = 1.0f;
    smokeLayer.angularVelocityRadians = 0.8f;
    smokeLayer.fadeInSeconds = 0.28f;
    smokeLayer.motion = FxParticleMotion::Drift;
    smokeLayer.blendMode = FxParticleBlendMode::Alpha;
    smokeLayer.alignment = FxParticleAlignment::CameraFacing;
    smokeLayer.material = FxParticleMaterial::Smoke;
    smokeLayer.tag = FxParticleTag::DecorationEmitter;
    emitLayerParticles(
        particleSystem,
        seed,
        x,
        y,
        z,
        0.0f,
        0.0f,
        1.0f,
        0.0f,
        0.0f,
        0.0f,
        smokeLayer);

    LayerRecipe hazeLayer = {};
    hazeLayer.startColorAbgr = makeAbgr(228, 228, 228, 52);
    hazeLayer.endColorAbgr = makeAbgr(188, 188, 188, 0);
    hazeLayer.count = 1u;
    hazeLayer.lateralSpread = std::max(6.0f, emitterRadius * 0.20f);
    hazeLayer.verticalSpread = 6.0f;
    hazeLayer.upwardVelocity = 84.0f;
    hazeLayer.startSize = std::max(30.0f, emitterRadius * 0.98f);
    hazeLayer.endSize = hazeLayer.startSize * 2.5f;
    hazeLayer.lifetimeSeconds = 2.10f;
    hazeLayer.drag = 0.22f;
    hazeLayer.rotationJitterRadians = 0.8f;
    hazeLayer.angularVelocityRadians = 0.5f;
    hazeLayer.fadeInSeconds = 0.26f;
    hazeLayer.motion = FxParticleMotion::Drift;
    hazeLayer.blendMode = FxParticleBlendMode::Alpha;
    hazeLayer.alignment = FxParticleAlignment::CameraFacing;
    hazeLayer.material = FxParticleMaterial::Mist;
    hazeLayer.tag = FxParticleTag::DecorationEmitter;
    emitLayerParticles(
        particleSystem,
        seed ^ 0x85ebca6bu,
        x,
        y,
        z,
        0.0f,
        0.0f,
        1.0f,
        0.0f,
        0.0f,
        0.0f,
        hazeLayer);
}

void spawnBuffSparkles(
    ParticleSystem &particleSystem,
    uint32_t seed,
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr)
{
    LayerRecipe sparkleLayer = {};
    sparkleLayer.startColorAbgr = colorAbgr;
    sparkleLayer.endColorAbgr = makeAbgr(255, 255, 255, 0);
    sparkleLayer.count = 12u;
    sparkleLayer.lateralSpread = radius;
    sparkleLayer.verticalSpread = radius * 0.7f;
    sparkleLayer.upwardVelocity = 10.0f;
    sparkleLayer.startSize = 6.0f;
    sparkleLayer.endSize = 2.0f;
    sparkleLayer.lifetimeSeconds = 0.32f;
    sparkleLayer.drag = 4.0f;
    sparkleLayer.rotationJitterRadians = 0.6f;
    sparkleLayer.angularVelocityRadians = 2.8f;
    sparkleLayer.motion = FxParticleMotion::Drift;
    sparkleLayer.blendMode = FxParticleBlendMode::Additive;
    sparkleLayer.alignment = FxParticleAlignment::CameraFacing;
    sparkleLayer.material = FxParticleMaterial::Spark;
    sparkleLayer.tag = FxParticleTag::Buff;
    emitLayerParticles(
        particleSystem,
        seed,
        x,
        y,
        z,
        0.0f,
        0.0f,
        1.0f,
        0.0f,
        0.0f,
        0.0f,
        sparkleLayer);
}

void spawnActorDebuffParticles(
    ParticleSystem &particleSystem,
    uint32_t spellId,
    uint32_t seed,
    float x,
    float y,
    float z,
    float actorHeight,
    float frontDirectionX,
    float frontDirectionY)
{
    const SpellId resolvedSpellId = spellIdFromValue(spellId);

    uint32_t primaryStart = makeAbgr(182, 126, 228, 208);
    uint32_t primaryEnd = makeAbgr(216, 172, 244, 0);
    uint32_t secondaryStart = makeAbgr(150, 132, 240, 196);
    uint32_t secondaryEnd = makeAbgr(190, 174, 248, 0);
    float lateralRadius = std::max(58.0f, actorHeight * 0.38f);
    float upwardVelocity = 24.0f;
    float primaryStartSize = 56.0f;
    float primaryEndSize = 28.0f;
    float secondaryStartSize = 40.0f;
    float secondaryEndSize = 17.0f;
    float primaryLifetime = 2.5f;
    float secondaryLifetime = 2.5f;
    uint32_t primaryCount = 40u;
    uint32_t secondaryCount = 28u;

    switch (resolvedSpellId)
    {
        case SpellId::Slow:
        case SpellId::Stun:
            primaryStart = makeAbgr(176, 128, 220, 204);
            primaryEnd = makeAbgr(210, 172, 236, 0);
            secondaryStart = makeAbgr(146, 132, 236, 188);
            secondaryEnd = makeAbgr(186, 174, 242, 0);
            upwardVelocity = 20.0f;
            lateralRadius = std::max(54.0f, actorHeight * 0.36f);
            primaryLifetime = 2.5f;
            secondaryLifetime = 2.5f;
            break;

        case SpellId::Paralyze:
        case SpellId::TurnUndead:
            primaryStart = makeAbgr(190, 172, 238, 208);
            primaryEnd = makeAbgr(222, 204, 248, 0);
            secondaryStart = makeAbgr(160, 154, 242, 192);
            secondaryEnd = makeAbgr(198, 190, 248, 0);
            upwardVelocity = 22.0f;
            lateralRadius = std::max(52.0f, actorHeight * 0.35f);
            primaryStartSize = 54.0f;
            primaryEndSize = 27.0f;
            secondaryStartSize = 38.0f;
            secondaryEndSize = 16.0f;
            primaryLifetime = 2.5f;
            secondaryLifetime = 2.5f;
            break;

        case SpellId::Blind:
        case SpellId::DarkGrasp:
        case SpellId::ShrinkingRay:
            primaryStart = makeAbgr(176, 110, 230, 210);
            primaryEnd = makeAbgr(216, 156, 244, 0);
            secondaryStart = makeAbgr(144, 122, 238, 194);
            secondaryEnd = makeAbgr(184, 164, 246, 0);
            upwardVelocity = 26.0f;
            lateralRadius = std::max(56.0f, actorHeight * 0.37f);
            primaryLifetime = 2.5f;
            secondaryLifetime = 2.5f;
            break;

        default:
            break;
    }

    emitDebuffAuraLayer(
        particleSystem,
        seed,
        x,
        y,
        z,
        actorHeight,
        frontDirectionX,
        frontDirectionY,
        primaryCount,
        lateralRadius,
        0.10f,
        0.90f,
        upwardVelocity,
        primaryStartSize,
        primaryEndSize,
        primaryLifetime,
        0.55f,
        primaryStart,
        primaryEnd,
        FxParticleMaterial::HardBlob,
        FxParticleBlendMode::Alpha);

    emitDebuffAuraLayer(
        particleSystem,
        seed ^ 0x9e3779b9u,
        x,
        y,
        z,
        actorHeight,
        frontDirectionX,
        frontDirectionY,
        secondaryCount,
        lateralRadius * 0.88f,
        0.18f,
        0.94f,
        upwardVelocity + 4.0f,
        secondaryStartSize,
        secondaryEndSize,
        secondaryLifetime,
        0.42f,
        varyAlpha(secondaryStart, 1.2f),
        secondaryEnd,
        FxParticleMaterial::HardBlob,
        FxParticleBlendMode::Alpha);
}
}
}
