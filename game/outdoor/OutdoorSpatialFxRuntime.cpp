#include "game/outdoor/OutdoorSpatialFxRuntime.h"

#include "game/app/GameSession.h"
#include "game/fx/FxSharedTypes.h"
#include "game/gameplay/GameplayTorchLight.h"
#include "game/fx/ParticleRecipes.h"
#include "game/party/Party.h"
#include "game/StringUtils.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/tables/SpriteTables.h"

#include <algorithm>
#include <cmath>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
constexpr float DecorationEmitterCooldownSeconds = 0.045f;
constexpr float DecorationSmokeEmitterCooldownSeconds = 0.14f;
constexpr float SpatialFxRefreshIntervalSeconds = 1.0f / 60.0f;
constexpr float ShadowHeightFadeDistance = 512.0f;
constexpr int32_t MapWeatherSnowing = 2;
constexpr int32_t MapWeatherRaining = 4;
constexpr float WeatherSnowParticlesPerSecond = 52.0f;
constexpr float WeatherRainParticlesPerSecond = 110.0f;
constexpr float WeatherSpawnForwardDistance = 900.0f;
constexpr float WeatherRainNearForwardDistance = 320.0f;
constexpr float WeatherSpawnHalfWidth = 1250.0f;
constexpr float WeatherSpawnDepth = 1850.0f;
constexpr float WeatherSpawnHeight = 900.0f;
constexpr float WeatherSpawnVolumeExpansionPerIntensity = 0.18f;

enum class DecorationLightPulseStyle
{
    None,
    FireFlicker,
    MagicPulse,
};

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

float clamp01(float value)
{
    return std::clamp(value, 0.0f, 1.0f);
}

float hash01(uint32_t value)
{
    return static_cast<float>(value & 0x00ffffffu) / static_cast<float>(0x01000000u);
}

float decorationEmitterSpawnZ(const DecorationBillboard &billboard)
{
    const float height = static_cast<float>(billboard.height);
    return static_cast<float>(billboard.z) + std::max(12.0f, height * 0.6f);
}

float decorationSmokeSpawnZ(const DecorationBillboard &billboard)
{
    const float height = static_cast<float>(billboard.height);
    return static_cast<float>(billboard.z) + std::max(18.0f, height * 0.35f);
}

uint64_t makeDecorationEmitterKey(const DecorationBillboard &billboard)
{
    return (static_cast<uint64_t>(billboard.entityIndex) << 32)
        ^ (static_cast<uint64_t>(static_cast<uint32_t>(billboard.x)) << 20)
        ^ (static_cast<uint64_t>(static_cast<uint32_t>(billboard.y)) << 8)
        ^ static_cast<uint64_t>(billboard.decorationId);
}

bool containsDecorationLightToken(const std::string &text, const char *token)
{
    return !text.empty() && text.find(token) != std::string::npos;
}

DecorationLightPulseStyle decorationLightPulseStyle(const DecorationEntry &decoration)
{
    if (hasDecorationFlag(decoration.flags, DecorationDescFlag::EmitFire))
    {
        return DecorationLightPulseStyle::FireFlicker;
    }

    const std::string searchableName = toLowerCopy(decoration.internalName + " " + decoration.hint);

    if (hasDecorationFlag(decoration.flags, DecorationDescFlag::FlickerFast)
        || hasDecorationFlag(decoration.flags, DecorationDescFlag::FlickerAverage)
        || containsDecorationLightToken(searchableName, "campfire")
        || containsDecorationLightToken(searchableName, "torch")
        || containsDecorationLightToken(searchableName, "beacon")
        || containsDecorationLightToken(searchableName, "brazier")
        || containsDecorationLightToken(searchableName, "fire")
        || containsDecorationLightToken(searchableName, "flame"))
    {
        return DecorationLightPulseStyle::FireFlicker;
    }

    if (hasDecorationFlag(decoration.flags, DecorationDescFlag::FlickerSlow)
        || containsDecorationLightToken(searchableName, "magic")
        || containsDecorationLightToken(searchableName, "pedestal")
        || containsDecorationLightToken(searchableName, "pedastal")
        || containsDecorationLightToken(searchableName, "altar"))
    {
        return DecorationLightPulseStyle::MagicPulse;
    }

    return DecorationLightPulseStyle::None;
}

float decorationPulseFrequencyScale(const DecorationEntry &decoration)
{
    if (hasDecorationFlag(decoration.flags, DecorationDescFlag::FlickerFast))
    {
        return 1.2f;
    }

    if (hasDecorationFlag(decoration.flags, DecorationDescFlag::FlickerSlow))
    {
        return 0.72f;
    }

    return 1.0f;
}

void applyDecorationLightPulse(
    const DecorationEntry &decoration,
    uint64_t emitterKey,
    float elapsedTime,
    float &radius,
    uint8_t &alpha)
{
    const DecorationLightPulseStyle style = decorationLightPulseStyle(decoration);

    if (style == DecorationLightPulseStyle::None)
    {
        return;
    }

    const float phase = hash01(
        static_cast<uint32_t>(emitterKey)
        ^ static_cast<uint32_t>(emitterKey >> 32)
        ^ 0x9e3779b9u) * 6.28318530718f;
    const float speedScale = decorationPulseFrequencyScale(decoration);
    const float pulseTime = elapsedTime * speedScale;

    float radiusScale = 1.0f;
    float alphaScale = 1.0f;

    if (style == DecorationLightPulseStyle::FireFlicker)
    {
        const float flickerA = std::sin(pulseTime * 4.6f + phase);
        const float flickerB = std::sin(pulseTime * 7.4f + phase * 1.37f);
        const float flickerC = std::sin(pulseTime * 2.2f + phase * 0.71f);
        const float combined = 0.5f + 0.5f * (0.62f * flickerA + 0.16f * flickerB + 0.22f * flickerC);
        radiusScale = 0.96f + 0.08f * combined;
        alphaScale = 0.84f + 0.16f * combined;
    }
    else if (style == DecorationLightPulseStyle::MagicPulse)
    {
        const float baseWave = 0.5f + 0.5f * std::sin(pulseTime * 2.0f + phase);
        const float accentWave = 0.5f + 0.5f * std::sin(pulseTime * 4.1f + phase * 1.31f);
        const float combined = 0.72f * baseWave + 0.28f * accentWave;
        radiusScale = 0.94f + 0.18f * combined;
        alphaScale = 0.84f + 0.22f * combined;
    }

    radius *= radiusScale;
    alpha = static_cast<uint8_t>(std::clamp(
        static_cast<int>(std::lround(static_cast<float>(alpha) * alphaScale)),
        0,
        255));
}

}

void OutdoorSpatialFxRuntime::reset()
{
    m_emitterCooldownBySourceKey.clear();
    m_emitterSequenceBySourceKey.clear();
    m_spatialRefreshAccumulatorSeconds = 0.0f;
    m_snowEmissionAccumulator = 0.0f;
    m_rainEmissionAccumulator = 0.0f;
    m_weatherEmissionSequence = 0;
    m_hasSpatialSnapshot = false;
}

bool OutdoorSpatialFxRuntime::beginFrame(OutdoorGameView &view, float deltaSeconds)
{
    for (auto it = m_emitterCooldownBySourceKey.begin(); it != m_emitterCooldownBySourceKey.end();)
    {
        it->second = std::max(0.0f, it->second - deltaSeconds);

        if (it->second <= 0.0f)
        {
            it = m_emitterCooldownBySourceKey.erase(it);
        }
        else
        {
            ++it;
        }
    }

    syncWeatherParticles(view, deltaSeconds);

    m_spatialRefreshAccumulatorSeconds += deltaSeconds;
    const bool refreshSpatialFx =
        !m_hasSpatialSnapshot || m_spatialRefreshAccumulatorSeconds >= SpatialFxRefreshIntervalSeconds;

    if (refreshSpatialFx)
    {
        m_spatialRefreshAccumulatorSeconds = 0.0f;
        view.m_worldFxSystem.clearSpatialFx();
        m_hasSpatialSnapshot = true;
    }

    return refreshSpatialFx;
}

void OutdoorSpatialFxRuntime::syncSpatialFx(OutdoorGameView &view, bool refreshSpatialFx)
{
    syncOutdoorProjectileContactShadows(view, refreshSpatialFx);

    if (refreshSpatialFx)
    {
        syncPartyTorchLight(view);
        syncActorSpatialFx(view);
        syncDecorationEmitters(view);
        syncSpriteObjectSpatialFx(view);
    }
}

void OutdoorSpatialFxRuntime::syncOutdoorProjectileContactShadows(OutdoorGameView &view, bool refreshSpatialFx)
{
    if (!refreshSpatialFx || !view.m_gameSettings.shadows)
    {
        return;
    }

    const std::vector<GameplayProjectilePresentationState> &projectiles =
        view.m_gameSession.gameplayFxService().activeProjectilePresentationStates();
    for (const GameplayProjectilePresentationState &projectile : projectiles)
    {
        addContactShadow(
            view,
            projectile.x,
            projectile.y,
            projectile.z,
            std::max(24.0f, projectile.radius * 0.75f),
            0.0f);
    }
}

void OutdoorSpatialFxRuntime::syncPartyTorchLight(OutdoorGameView &view)
{
    if (view.m_pOutdoorPartyRuntime == nullptr || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    const Party &party = view.m_pOutdoorPartyRuntime->party();
    const std::optional<GameplayTorchLight> torchLight =
        resolveGameplayTorchLight(party, true, view.m_pOutdoorWorldRuntime->atmosphereState().isNight);

    if (!torchLight)
    {
        return;
    }

    addLightEmitter(
        view,
        view.m_cameraTargetX,
        view.m_cameraTargetY,
        view.m_cameraTargetZ,
        torchLight->radius,
        torchLight->colorAbgr);
}

void OutdoorSpatialFxRuntime::syncActorSpatialFx(OutdoorGameView &view)
{
    if (view.m_pOutdoorWorldRuntime == nullptr || !view.m_outdoorActorPreviewBillboardSet.has_value())
    {
        return;
    }

    const ActorPreviewBillboardSet &billboardSet = *view.m_outdoorActorPreviewBillboardSet;

    for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

        if (pActor == nullptr || pActor->isDead || pActor->isInvisible)
        {
            continue;
        }

        addContactShadow(
            view,
            pActor->preciseX,
            pActor->preciseY,
            pActor->preciseZ,
            std::max(24.0f, static_cast<float>(pActor->radius) * 0.9f),
            static_cast<float>(pActor->height));

        const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(pActor->spriteFrameIndex, 0);

        if (pFrame != nullptr && pFrame->glowRadius > 0)
        {
            addLightEmitter(
                view,
                pActor->preciseX,
                pActor->preciseY,
                pActor->preciseZ + static_cast<float>(pActor->height) * 0.5f,
                static_cast<float>(pFrame->glowRadius),
                makeAbgr(255, 255, 255, 140));
        }
    }
}

void OutdoorSpatialFxRuntime::syncDecorationEmitters(OutdoorGameView &view)
{
    if (!view.m_outdoorDecorationBillboardSet.has_value())
    {
        return;
    }

    const DecorationBillboardSet &billboardSet = *view.m_outdoorDecorationBillboardSet;
    for (const DecorationBillboard &billboard : billboardSet.billboards)
    {
        if (OutdoorInteractionController::isInteractiveDecorationHidden(view, billboard.entityIndex))
        {
            continue;
        }

        const DecorationEntry *pDecoration = billboardSet.decorationTable.get(billboard.decorationId);

        if (pDecoration == nullptr)
        {
            continue;
        }

        const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(billboard.spriteId, 0);

        float lightEmitterRadius = 0.0f;

        if (pDecoration->lightRadius > 0)
        {
            lightEmitterRadius = static_cast<float>(pDecoration->lightRadius);
        }

        if (pFrame != nullptr && pFrame->glowRadius > 0)
        {
            lightEmitterRadius = std::max(lightEmitterRadius, static_cast<float>(pFrame->glowRadius));
        }

        // OpenYAMM tuning: double legacy-style decoration light reach so static emitters read outdoors.
        lightEmitterRadius *= 2.0f;

        const float lightX = static_cast<float>(billboard.x);
        const float lightY = static_cast<float>(billboard.y);
        const float lightZ = decorationEmitterSpawnZ(billboard);
        if (lightEmitterRadius > 0.0f)
        {
            uint8_t lightRed = 255;
            uint8_t lightGreen = 255;
            uint8_t lightBlue = 255;

            if (pDecoration->lightRed != 0 || pDecoration->lightGreen != 0 || pDecoration->lightBlue != 0)
            {
                lightRed = static_cast<uint8_t>(pDecoration->lightRed);
                lightGreen = static_cast<uint8_t>(pDecoration->lightGreen);
                lightBlue = static_cast<uint8_t>(pDecoration->lightBlue);
            }

            uint8_t lightAlpha = 208;
            const uint64_t emitterKey = makeDecorationEmitterKey(billboard);
            applyDecorationLightPulse(
                *pDecoration,
                emitterKey,
                view.m_elapsedTime,
                lightEmitterRadius,
                lightAlpha);
            const uint32_t lightEmitterColorAbgr = makeAbgr(lightRed, lightGreen, lightBlue, lightAlpha);
            addLightEmitter(view, lightX, lightY, lightZ, lightEmitterRadius, lightEmitterColorAbgr);
        }

        const uint64_t emitterKey = makeDecorationEmitterKey(billboard);

        if (hasDecorationFlag(billboard.flags, DecorationDescFlag::EmitFire))
        {
            float &cooldown = m_emitterCooldownBySourceKey[emitterKey];

            if (cooldown <= 0.0f)
            {
                cooldown = DecorationEmitterCooldownSeconds;
                const uint32_t emissionSeed =
                    static_cast<uint32_t>(emitterKey)
                    ^ (++m_emitterSequenceBySourceKey[emitterKey] * 2654435761u);
                FxRecipes::spawnDecorationFireParticles(
                    view.m_worldFxSystem.particles(),
                    emissionSeed,
                    lightX,
                    lightY,
                    lightZ,
                    static_cast<float>(billboard.radius));
            }
        }

        if (hasDecorationFlag(billboard.flags, DecorationDescFlag::EmitSmoke))
        {
            const uint64_t smokeEmitterKey = emitterKey ^ 0x9e3779b97f4a7c15ull;
            float &cooldown = m_emitterCooldownBySourceKey[smokeEmitterKey];

            if (cooldown <= 0.0f)
            {
                cooldown = DecorationSmokeEmitterCooldownSeconds;
                const uint32_t emissionSeed =
                    static_cast<uint32_t>(smokeEmitterKey)
                    ^ (++m_emitterSequenceBySourceKey[smokeEmitterKey] * 2246822519u);
                FxRecipes::spawnDecorationSmokeParticles(
                    view.m_worldFxSystem.particles(),
                    emissionSeed,
                    lightX,
                    lightY,
                    decorationSmokeSpawnZ(billboard),
                    std::max(12.0f, static_cast<float>(billboard.radius)));
            }
        }
    }
}

void OutdoorSpatialFxRuntime::syncSpriteObjectSpatialFx(OutdoorGameView &view)
{
    if (!view.m_outdoorSpriteObjectBillboardSet.has_value())
    {
        return;
    }

    const SpriteObjectBillboardSet &billboardSet = *view.m_outdoorSpriteObjectBillboardSet;

    for (const SpriteObjectBillboard &billboard : billboardSet.billboards)
    {
        if (billboard.glowRadiusMultiplier <= 0)
        {
            continue;
        }

        const SpriteFrameEntry *pFrame =
            billboardSet.spriteFrameTable.getFrame(billboard.spriteFrameIndex, billboard.timeSinceCreatedTicks);

        if (pFrame == nullptr || pFrame->glowRadius <= 0)
        {
            continue;
        }

        addLightEmitter(
            view,
            static_cast<float>(billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z) + static_cast<float>(billboard.height) * 0.5f,
            static_cast<float>(pFrame->glowRadius * billboard.glowRadiusMultiplier),
            makeAbgr(255, 255, 255, 120));
        addGlowBillboard(
            view,
            static_cast<float>(billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z) + static_cast<float>(billboard.height) * 0.5f,
            static_cast<float>(pFrame->glowRadius * billboard.glowRadiusMultiplier),
            makeAbgr(255, 255, 255, 120));
    }
}

void OutdoorSpatialFxRuntime::syncWeatherParticles(OutdoorGameView &view, float deltaSeconds)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        m_snowEmissionAccumulator = 0.0f;
        m_rainEmissionAccumulator = 0.0f;
        return;
    }

    const int32_t weatherFlags = view.m_pOutdoorWorldRuntime->atmosphereState().weatherFlags;
    const float rainIntensity = std::clamp(view.m_pOutdoorWorldRuntime->atmosphereState().rainIntensity, 0.0f, 3.0f);
    const bool snowing = (weatherFlags & MapWeatherSnowing) != 0;
    const bool raining = (weatherFlags & MapWeatherRaining) != 0 && rainIntensity > 0.001f;

    if (!snowing)
    {
        m_snowEmissionAccumulator = 0.0f;
    }

    if (!raining)
    {
        m_rainEmissionAccumulator = 0.0f;
    }

    if (!snowing && !raining)
    {
        return;
    }

    const float yawRadians = view.effectiveCameraYawRadians();
    const float forwardX = std::cos(yawRadians);
    const float forwardY = std::sin(yawRadians);
    const float rightX = -forwardY;
    const float rightY = forwardX;
    const float cameraX = view.m_cameraTargetX;
    const float cameraY = view.m_cameraTargetY;
    const float cameraZ = view.m_cameraTargetZ;
    const float spawnVolumeScale =
        1.0f + std::max(0.0f, rainIntensity - 1.0f) * WeatherSpawnVolumeExpansionPerIntensity;
    const float spawnForwardDistance = WeatherSpawnForwardDistance * spawnVolumeScale;
    const float rainNearForwardDistance = WeatherRainNearForwardDistance * spawnVolumeScale;
    const float spawnHalfWidth = WeatherSpawnHalfWidth * spawnVolumeScale;
    const float spawnDepth = WeatherSpawnDepth * spawnVolumeScale;
    const float spawnHeight = WeatherSpawnHeight * spawnVolumeScale;

    auto emitSnowParticle =
        [&](uint32_t seed)
        {
            const float forwardOffset = 64.0f + hash01(seed) * spawnDepth;
            const float lateralOffset =
                (hash01(seed * 2246822519u) * 2.0f - 1.0f) * spawnHalfWidth;
            const float verticalOffset = 180.0f + hash01(seed * 3266489917u) * spawnHeight;
            const float driftSide = (hash01(seed * 668265263u) * 2.0f - 1.0f) * 26.0f;
            const float driftForward = (hash01(seed * 374761393u) * 2.0f - 1.0f) * 14.0f;

            FxParticleState particle = {};
            particle.x = cameraX + forwardX * (spawnForwardDistance + forwardOffset) + rightX * lateralOffset;
            particle.y = cameraY + forwardY * (spawnForwardDistance + forwardOffset) + rightY * lateralOffset;
            particle.z = cameraZ + verticalOffset;
            particle.velocityX = rightX * driftSide + forwardX * driftForward;
            particle.velocityY = rightY * driftSide + forwardY * driftForward;
            particle.velocityZ = -(90.0f + hash01(seed * 1274126177u) * 40.0f);
            particle.size = 22.0f + hash01(seed * 197830471u) * 10.0f;
            particle.endSize = particle.size * 0.9f;
            particle.drag = 0.08f;
            particle.rotationRadians = (hash01(seed * 2654435761u) * 2.0f - 1.0f) * 0.8f;
            particle.angularVelocityRadians = (hash01(seed * 1597334677u) * 2.0f - 1.0f) * 0.7f;
            particle.stretch = 1.0f;
            particle.ageSeconds = 0.0f;
            particle.fadeInSeconds = 0.08f;
            particle.fadeOutStartSeconds = 3.0f + hash01(seed * 3812015801u) * 0.6f;
            particle.lifetimeSeconds = particle.fadeOutStartSeconds + 0.7f;
            particle.startColorAbgr = makeAbgr(236, 240, 248, 208);
            particle.endColorAbgr = makeAbgr(236, 240, 248, 0);
            particle.motion = FxParticleMotion::VelocityTrail;
            particle.blendMode = FxParticleBlendMode::Alpha;
            particle.alignment = FxParticleAlignment::CameraFacing;
            particle.material = FxParticleMaterial::SoftBlob;
            particle.tag = FxParticleTag::Misc;
            view.m_worldFxSystem.particles().addParticle(particle);
        };

    auto emitRainParticle =
        [&](uint32_t seed)
        {
            const float forwardOffset = hash01(seed) * spawnDepth;
            const float lateralOffset =
                (hash01(seed * 2246822519u) * 2.0f - 1.0f) * spawnHalfWidth;
            const float verticalOffset = 120.0f + hash01(seed * 3266489917u) * (420.0f * spawnVolumeScale);
            const float slant = 24.0f + hash01(seed * 668265263u) * 34.0f;
            const float intensityScale = std::max(rainIntensity, 0.1f);

            FxParticleState particle = {};
            particle.x = cameraX + forwardX * (rainNearForwardDistance + forwardOffset) + rightX * lateralOffset;
            particle.y = cameraY + forwardY * (rainNearForwardDistance + forwardOffset) + rightY * lateralOffset;
            particle.z = cameraZ + verticalOffset;
            particle.velocityX = forwardX * slant;
            particle.velocityY = forwardY * slant;
            particle.velocityZ = -(2200.0f + hash01(seed * 1274126177u) * 700.0f);
            particle.size = (9.5f + hash01(seed * 197830471u) * 6.5f) * (0.9f + intensityScale * 0.24f);
            particle.endSize = particle.size * 0.6f;
            particle.drag = 0.0f;
            particle.rotationRadians = 0.0f;
            particle.angularVelocityRadians = 0.0f;
            particle.stretch = (8.5f + hash01(seed * 1597334677u) * 4.0f) * (0.95f + intensityScale * 0.18f);
            particle.ageSeconds = 0.0f;
            particle.fadeInSeconds = 0.0f;
            particle.fadeOutStartSeconds = 0.30f + hash01(seed * 3812015801u) * 0.08f;
            particle.lifetimeSeconds = particle.fadeOutStartSeconds + 0.12f;
            particle.startColorAbgr = makeAbgr(
                170,
                190,
                220,
                static_cast<uint8_t>(std::clamp(std::lround(120.0f + intensityScale * 44.0f), 0l, 255l)));
            particle.endColorAbgr = makeAbgr(170, 190, 220, 0);
            particle.motion = FxParticleMotion::VelocityTrail;
            particle.blendMode = FxParticleBlendMode::Alpha;
            particle.alignment = FxParticleAlignment::VelocityStretched;
            particle.material = FxParticleMaterial::HardBlob;
            particle.tag = FxParticleTag::Misc;
            view.m_worldFxSystem.particles().addParticle(particle);
        };

    if (snowing)
    {
        m_snowEmissionAccumulator += deltaSeconds * WeatherSnowParticlesPerSecond;

        while (m_snowEmissionAccumulator >= 1.0f)
        {
            --m_snowEmissionAccumulator;
            const uint32_t seed = ++m_weatherEmissionSequence * 2654435761u;
            emitSnowParticle(seed);
        }
    }

    if (raining)
    {
        m_rainEmissionAccumulator += deltaSeconds * WeatherRainParticlesPerSecond * rainIntensity;

        while (m_rainEmissionAccumulator >= 1.0f)
        {
            --m_rainEmissionAccumulator;
            const uint32_t seed = (++m_weatherEmissionSequence * 2246822519u) ^ 0x5f356495u;
            emitRainParticle(seed);
        }
    }
}

void OutdoorSpatialFxRuntime::addContactShadow(
    OutdoorGameView &view,
    float x,
    float y,
    float z,
    float radius,
    float heightScale)
{
    if (!view.m_gameSettings.shadows || !view.m_outdoorMapData.has_value())
    {
        return;
    }

    float floorHeight = 0.0f;

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        floorHeight = view.m_pOutdoorWorldRuntime->sampleSupportFloorHeight(x, y, z, 5.0f, 5.0f);
    }
    else
    {
        floorHeight = sampleOutdoorSupportFloorHeight(*view.m_outdoorMapData, x, y, z);
    }

    const float heightAboveFloor = std::max(0.0f, z - floorHeight);
    const float alphaScale = 1.0f - clamp01(heightAboveFloor / ShadowHeightFadeDistance);

    if (alphaScale <= 0.05f)
    {
        return;
    }

    const float shadowRadius =
        std::max(12.0f, radius * (1.0f - clamp01(heightAboveFloor / std::max(64.0f, heightScale + 64.0f))));
    const uint32_t shadowColorAbgr = makeAbgr(0, 0, 0, static_cast<uint8_t>(std::lround(96.0f * alphaScale)));
    view.m_worldFxSystem.addContactShadow(x, y, floorHeight + 1.0f, shadowRadius, shadowColorAbgr);
}

void OutdoorSpatialFxRuntime::addGlowBillboard(
    OutdoorGameView &view,
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr)
{
    view.m_worldFxSystem.addGlowBillboard(x, y, z, radius, colorAbgr);
}

void OutdoorSpatialFxRuntime::addLightEmitter(
    OutdoorGameView &view,
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr)
{
    view.m_worldFxSystem.addLightEmitter(x, y, z, radius, colorAbgr);
}
}
