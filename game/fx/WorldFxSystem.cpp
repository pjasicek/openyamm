#include "game/fx/WorldFxSystem.h"

#include "game/gameplay/ActorAiTrace.h"

#include "game/StringUtils.h"
#include "game/app/GameSession.h"
#include "game/audio/GameAudioSystem.h"
#include "game/data/GameDataRepository.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ProjectileEffectBindings.h"
#include "game/fx/import/EffectDefinitionLoader.h"
#include "game/gameplay/ActorBehaviorRuntime.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/ActorModelPresentation.h"
#include "game/maps/ActorModelManifest.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"
#include "game/tables/MonsterProjectileTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/ObjectTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpriteTables.h"
#include "engine/AssetFileSystem.h"
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <optional>
#include <cmath>
#include <iostream>
#include <numbers>
#include <stdexcept>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
// Seconds the shatter of a broken energy shield shows (fs_model_shield's break animation).
constexpr float ShieldShellBreakSeconds = 0.75f;
// Seconds a hit or the raise lifts a resting shell to its full strength, fading back to the rest strength.
constexpr float ShieldShellFlareSeconds = 0.6f;

// The energy shield shell over an actor's model (GameplayActorShieldView), none while its shield is down and done
// shattering. Hits keep their world points: footZ and the body height place the rise sweep.
std::optional<Engine::ModelShieldShell> actorShieldShell(const GameplayActorShieldView &shield, float footZ,
    float bodyHeight, float seconds, bool withHits)
{
    const bool shattering = shield.secondsSinceBreak >= 0.0f && shield.secondsSinceBreak < ShieldShellBreakSeconds;
    if (!shield.present || (!shield.raised && !shattering))
    {
        return std::nullopt;
    }
    Engine::ModelShieldShell shell;
    shell.color = shield.color;
    shell.fraction = shield.fraction;
    // At rest a raised shell shows its rest strength; a hit or the raise flares it to the full strength. Steadier
    // and brighter the fuller the pool; full brightness while it shatters.
    float flare = shield.secondsSinceRaise >= 0.0f && shield.secondsSinceRaise < ShieldShellFlareSeconds
        ? 1.0f - shield.secondsSinceRaise / ShieldShellFlareSeconds : 0.0f;
    for (const std::array<float, 4> &hit : shield.hits)
    {
        if (hit[3] >= 0.0f && hit[3] < ShieldShellFlareSeconds)
        {
            flare = std::max(flare, 1.0f - hit[3] / ShieldShellFlareSeconds);
        }
    }
    const float rest = shield.restIntensity >= 0.0f ? shield.restIntensity : shield.intensity;
    const float raisedStrength = rest + (shield.intensity - rest) * flare;
    shell.strength = shield.raised ? raisedStrength * (0.55f + 0.45f * shield.fraction) : shield.intensity;
    shell.breakSeconds = shattering && !shield.raised ? shield.secondsSinceBreak : -1.0f;
    shell.raiseSeconds = shield.raised ? shield.secondsSinceRaise : -1.0f;
    shell.seconds = seconds;
    shell.footZ = footZ;
    shell.bodyHeight = std::max(bodyHeight, 1.0f);
    shell.thickness = std::clamp(bodyHeight * 0.02f, 2.0f, 8.0f);
    for (size_t hit = 0; hit < Engine::ModelShieldShell::MaxHits; ++hit)
    {
        shell.hits[hit] = withHits && hit < shield.hits.size() ? shield.hits[hit]
            : std::array<float, 4>{0.0f, 0.0f, 0.0f, -1.0f};
    }
    return shell;
}

constexpr float ParticleUpdateStepSeconds = 1.0f / 30.0f;
constexpr float MaxParticleUpdateAccumulationSeconds = 0.25f;
constexpr float DefaultProjectileTrailCooldownSeconds = 1.0f / 30.0f;
constexpr float HangingProjectileTrailCooldownSeconds = 2.0f / 128.0f;
constexpr float SparksProjectileTrailCooldownSeconds = 0.10f;
constexpr float ProjectileFxVisualSizeScale = 1.25f;
constexpr float PartySpellFxRingRadius = 28.0f;
constexpr float ImpactLightRadiusScale = 1.18f;
constexpr float ImpactLightIntensityScale = 1.35f;
constexpr uint32_t CannonballPseudoSpellId = 136;
// Visual-only spell flights: a debuff's bolt crosses most ranges in a blink; a drain's stolen life swoops back to the
// party in under one and a half seconds.
constexpr float SpellBoltSpeed = 6000.0f;
constexpr float SpellBoltMinSeconds = 0.04f;
constexpr float SpellBoltMaxSeconds = 0.6f;
constexpr float DrainFlightSpeed = 1100.0f;
constexpr float DrainFlightMinSeconds = 0.45f;
constexpr float DrainFlightMaxSeconds = 1.3f;
constexpr float DrainFlightBow = 140.0f;
// A drain striking a crowd (Souldrinker) sends at most this many lives back at once, so their trails stay readable.
constexpr size_t MaxDrainFlights = 8;
// Flights to and from the party end or start this far in front of its eyes, and a little lower, so they neither fill
// the screen nor pass through the camera.
constexpr float PartyFlightStandOff = 110.0f;
constexpr float PartyFlightDrop = 40.0f;
// Creature auras are authored for a creature this tall and scaled to the real one within these limits.
constexpr float AuraReferenceActorHeight = 150.0f;
constexpr float AuraMinScale = 0.6f;
constexpr float AuraMaxScale = 3.0f;
// The party's own buff and heal auras play this far in front of its eyes and this far below them, so they rise
// into the lower part of the view.
constexpr float PartyAuraDistance = 150.0f;
constexpr float PartyAuraDrop = 75.0f;
// An impact on the party (within PartyHitReach of its body) plays this far in front of its eyes, smaller, so a fireball
// bursting on the party shows in front of it instead of blinding it; its light stays where it struck. It plays where
// the hit came from on screen, a little lower, held between the vertical limits and within PartyHitEdgeX of the side
// edges (screen fractions from the centre). A hit from beside or behind flares at that side's edge, partly off screen,
// lower and smaller the further round it came (fully so PartyHitEdgeBlend past the view), showing which way to turn.
// Both worlds draw with a 60 degree vertical field of view.
constexpr float PartyHitReach = 224.0f;
constexpr float PartyHitBodyDrop = 80.0f;
constexpr float PartyHitDistance = 160.0f;
constexpr float PartyHitTanHalfVerticalFov = 0.57735f;
constexpr float PartyHitDropY = 0.3f;
constexpr float PartyHitMinY = -0.6f;
constexpr float PartyHitMaxY = 0.3f;
constexpr float PartyHitEdgeX = 0.9f;
constexpr float PartyHitEdgeY = -0.45f;
constexpr float PartyHitEdgeBlend = 0.5f;
constexpr float PartyHitScale = 0.6f;
constexpr float PartyHitEdgeScale = 0.45f;

// Where an impact on the party plays (see PartyHitReach) and at what scale. fromBody runs from the party's body to the
// struck point, the hit's direction when the impact does not know the projectile's flight.
std::array<float, 3> partyHitShownPosition(
    const IGameplayWorldRuntime &world,
    const GameplayProjectileImpactPresentationState &impact,
    const std::array<float, 3> &fromBody,
    float &scale)
{
    std::array<float, 3> toSource = {-impact.flightDirectionX, -impact.flightDirectionY, -impact.flightDirectionZ};
    if (toSource[0] == 0.0f && toSource[1] == 0.0f && toSource[2] == 0.0f)
    {
        toSource = fromBody;
    }

    // The camera's axes: forward along the view, right and up across the screen.
    const float yaw = world.gameplayCameraYawRadians();
    const float pitch = world.gameplayCameraPitchRadians();
    const std::array<float, 3> forward = {
        std::cos(yaw) * std::cos(pitch), std::sin(yaw) * std::cos(pitch), std::sin(pitch)};
    const std::array<float, 3> right = {std::sin(yaw), -std::cos(yaw), 0.0f};
    const std::array<float, 3> up = {
        -std::cos(yaw) * std::sin(pitch), -std::sin(yaw) * std::sin(pitch), std::cos(pitch)};
    const auto dot = [](const std::array<float, 3> &a, const std::array<float, 3> &b)
    {
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    };
    const float sourceForward = dot(toSource, forward);
    const float sourceRight = dot(toSource, right);
    const float sourceUp = dot(toSource, up);

    // Screen position (fractions of the half-width and half-height from the centre) of where the hit came from.
    const float tanHalfHorizontalFov = PartyHitTanHalfVerticalFov * std::max(world.gameplayViewAspectRatio(), 0.1f);
    float screenX = 0.0f;
    float screenY = -PartyHitDropY;
    float edge = 0.0f;
    const float sourceAcross = std::sqrt(sourceForward * sourceForward + sourceRight * sourceRight);
    if (sourceAcross > 0.001f)
    {
        const float azimuth = std::atan2(sourceRight, sourceForward);
        const float halfHorizontalFov = std::atan(tanHalfHorizontalFov);
        const float side = sourceRight < 0.0f ? -1.0f : 1.0f;
        screenX = std::abs(azimuth) < halfHorizontalFov
            ? std::clamp(std::tan(azimuth) / tanHalfHorizontalFov, -PartyHitEdgeX, PartyHitEdgeX)
            : side * PartyHitEdgeX;
        edge = std::clamp((std::abs(azimuth) - halfHorizontalFov) / PartyHitEdgeBlend, 0.0f, 1.0f);
        const float frontY = std::clamp(
            sourceUp / sourceAcross / PartyHitTanHalfVerticalFov - PartyHitDropY, PartyHitMinY, PartyHitMaxY);
        screenY = frontY + (PartyHitEdgeY - frontY) * edge;
    }
    scale = PartyHitScale + (PartyHitEdgeScale - PartyHitScale) * edge;

    std::array<float, 3> shown = {};
    for (size_t axis = 0; axis < 3; ++axis)
    {
        shown[axis] = forward[axis] + right[axis] * screenX * tanHalfHorizontalFov
            + up[axis] * screenY * PartyHitTanHalfVerticalFov;
    }
    const float length = std::sqrt(dot(shown, shown));
    return {world.partyX() + shown[0] / length * PartyHitDistance,
        world.partyY() + shown[1] / length * PartyHitDistance,
        world.partyEyeZ() + shown[2] / length * PartyHitDistance};
}

// value modulo a positive period, in [0, period): std::fmod compiles to a slow x87 loop, and every actor model runs
// several of these each frame.
float wrapPeriod(float value, float period)
{
    return value - period * std::floor(value / period);
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

bool isCannonballProjectile(const GameplayProjectilePresentationState &projectile)
{
    return projectile.spellId == CannonballPseudoSpellId
        || projectile.objectName == "Cannonball"
        || projectile.objectSpriteName == "CANNBL";
}

bool isSparksSpellProjectile(const GameplayProjectilePresentationState &projectile)
{
    return projectile.spellId >= 0
        && spellIdFromValue(static_cast<uint32_t>(projectile.spellId)) == SpellId::Sparks;
}

uint32_t partySpellFxColorAbgr(const PartySpellCastResult &result)
{
    if (result.effectKind == PartySpellCastEffectKind::CharacterRestore
        || result.effectKind == PartySpellCastEffectKind::PartyRestore)
    {
        return makeAbgr(192, 255, 192, 224);
    }

    if (spellIdInRange(result.spellId, SpellId::LightBolt, SpellId::DivineIntervention))
    {
        return makeAbgr(255, 240, 180, 224);
    }

    if (spellIdInRange(result.spellId, SpellId::Reanimate, SpellId::SoulDrinker))
    {
        return makeAbgr(180, 112, 255, 224);
    }

    if (spellIdInRange(result.spellId, SpellId::CureWeakness, SpellId::PowerCure))
    {
        return makeAbgr(132, 224, 120, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::Telepathy, SpellId::Enslave))
    {
        return makeAbgr(224, 132, 255, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::DetectLife, SpellId::Resurrection))
    {
        return makeAbgr(208, 192, 255, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::Stun, SpellId::MassDistortion))
    {
        return makeAbgr(180, 220, 132, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::Awaken, SpellId::LloydsBeacon))
    {
        return makeAbgr(160, 224, 255, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::WizardEye, SpellId::Starburst))
    {
        return makeAbgr(255, 228, 132, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::TorchLight, SpellId::Incinerate))
    {
        return makeAbgr(255, 144, 72, 224);
    }

    return makeAbgr(255, 255, 255, 208);
}

uint32_t withScaledAlpha(uint32_t colorAbgr, float alphaScale)
{
    const float clampedScale = std::clamp(alphaScale, 0.0f, 1.0f);
    const uint8_t red = static_cast<uint8_t>(colorAbgr & 0xffu);
    const uint8_t green = static_cast<uint8_t>((colorAbgr >> 8) & 0xffu);
    const uint8_t blue = static_cast<uint8_t>((colorAbgr >> 16) & 0xffu);
    const uint8_t alpha = static_cast<uint8_t>(
        std::clamp(
            static_cast<int>(std::lround(static_cast<float>((colorAbgr >> 24) & 0xffu) * clampedScale)),
            0,
            255));

    return makeAbgr(red, green, blue, alpha);
}

float impactLightDurationSeconds(
    FxRecipes::ProjectileRecipe recipe,
    const GameplayProjectileImpactPresentationState &impact)
{
    const float presentationSeconds =
        impact.lifetimeTicks > 0
            ? static_cast<float>(impact.lifetimeTicks) / 128.0f
            : 0.0f;
    float recipeSeconds = 0.68f;

    switch (recipe)
    {
    case FxRecipes::ProjectileRecipe::Blaster:
        recipeSeconds = 0.25f;
        break;
    case FxRecipes::ProjectileRecipe::Fireball:
    case FxRecipes::ProjectileRecipe::DragonBreath:
        recipeSeconds = 0.92f;
        break;
    case FxRecipes::ProjectileRecipe::MeteorShower:
    case FxRecipes::ProjectileRecipe::Starburst:
    case FxRecipes::ProjectileRecipe::Implosion:
        recipeSeconds = 1.08f;
        break;
    case FxRecipes::ProjectileRecipe::ToxicCloud:
        recipeSeconds = 1.0f;
        break;
    case FxRecipes::ProjectileRecipe::None:
        recipeSeconds = 0.0f;
        break;
    default:
        break;
    }

    return std::max(recipeSeconds, presentationSeconds);
}

float impactLightRadius(FxRecipes::ProjectileRecipe recipe)
{
    if (FxRecipes::projectileRecipeIsBindingOnly(recipe))
    {
        return 0.0f;
    }

    const float recipeGlowRadius = FxRecipes::projectileRecipeGlowRadius(recipe);

    switch (recipe)
    {
    case FxRecipes::ProjectileRecipe::Blaster:
        return 256.0f;
    case FxRecipes::ProjectileRecipe::MeteorShower:
        return std::max(recipeGlowRadius, 128.0f) * ImpactLightRadiusScale;
    case FxRecipes::ProjectileRecipe::Starburst:
        return std::max(recipeGlowRadius, 136.0f) * ImpactLightRadiusScale;
    case FxRecipes::ProjectileRecipe::Implosion:
        return std::max(recipeGlowRadius, 152.0f) * ImpactLightRadiusScale;
    case FxRecipes::ProjectileRecipe::None:
        return 0.0f;
    default:
        return std::max(recipeGlowRadius, 96.0f) * ImpactLightRadiusScale;
    }
}

bool shouldTriggerPartySpellSparkles(PartySpellCastEffectKind effectKind)
{
    return effectKind == PartySpellCastEffectKind::CharacterRestore
        || effectKind == PartySpellCastEffectKind::PartyRestore;
}

bool shouldTriggerPartySpellBuffAura(PartySpellCastEffectKind effectKind)
{
    return effectKind == PartySpellCastEffectKind::PartyBuff
        || effectKind == PartySpellCastEffectKind::CharacterBuff;
}

float projectileTrailCooldownSeconds(FxRecipes::ProjectileRecipe recipe)
{
    switch (recipe)
    {
        case FxRecipes::ProjectileRecipe::Sparks:
            return SparksProjectileTrailCooldownSeconds;

        default:
            if (FxRecipes::projectileRecipeUsesHangingProjectileTrail(recipe))
            {
                return HangingProjectileTrailCooldownSeconds;
            }

            return DefaultProjectileTrailCooldownSeconds;
    }
}

bool projectileRecipeEmitsTrailParticles(int spellIdValue, FxRecipes::ProjectileRecipe recipe)
{
    if (recipe == FxRecipes::ProjectileRecipe::Blaster
        || recipe == FxRecipes::ProjectileRecipe::Sparks
        || recipe == FxRecipes::ProjectileRecipe::Arrow
        || recipe == FxRecipes::ProjectileRecipe::FireArrow)
    {
        return false;
    }

    const FxRecipes::ProjectileFxRecipe &fxRecipe = FxRecipes::projectileFxRecipe(recipe);

    if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::RenderSprite)
    {
        return false;
    }

    if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::None
        && (fxRecipe.impactPrimitive != FxRecipes::ProjectileFxPrimitive::None
            || fxRecipe.mobileLightRadius > 0.0f
            || !fxRecipe.renderProjectileBillboard))
    {
        return false;
    }

    const SpellId spellId = spellIdFromValue(static_cast<uint32_t>(spellIdValue));
    return spellId != SpellId::MindBlast
        && spellId != SpellId::PsychicShock
        && spellId != SpellId::Harm
        && spellId != SpellId::ToxicCloud
        && spellId != SpellId::Incinerate;
}

// The rotation turning an effect's +X towards a direction of travel (shortest arc from +X); identity when still.
std::array<float, 4> flightRotation(const std::array<float, 3> &velocity)
{
    const float speed = std::sqrt(velocity[0] * velocity[0] + velocity[1] * velocity[1] + velocity[2] * velocity[2]);
    if (speed <= 1.0e-3f)
    {
        return {0.0f, 0.0f, 0.0f, 1.0f};
    }
    const std::array<float, 3> direction = {velocity[0] / speed, velocity[1] / speed, velocity[2] / speed};
    std::array<float, 4> rotation = direction[0] < -0.9999f
        ? std::array<float, 4>{0.0f, 0.0f, 1.0f, 0.0f}
        : std::array<float, 4>{0.0f, -direction[2], direction[1], 1.0f + direction[0]};
    const float rotationLength = std::sqrt(rotation[0] * rotation[0] + rotation[1] * rotation[1] +
        rotation[2] * rotation[2] + rotation[3] * rotation[3]);
    for (float &component : rotation)
    {
        component /= rotationLength;
    }
    return rotation;
}

// A point PartyFlightStandOff units from the party's eyes towards another point.
std::array<float, 3> partyStandOffPoint(const std::array<float, 3> &partyEyes, const std::array<float, 3> &toward)
{
    const std::array<float, 3> delta = {toward[0] - partyEyes[0], toward[1] - partyEyes[1], toward[2] - partyEyes[2]};
    const float distance = std::sqrt(delta[0] * delta[0] + delta[1] * delta[1] + delta[2] * delta[2]);
    const float reach = distance > 1.0e-3f ? std::min(PartyFlightStandOff, distance * 0.5f) / distance : 0.0f;
    return {partyEyes[0] + delta[0] * reach, partyEyes[1] + delta[1] * reach, partyEyes[2] + delta[2] * reach};
}

std::optional<std::array<float, 3>> actorCenterPosition(GameSession &session, size_t actorIndex)
{
    IGameplayWorldRuntime *pWorldRuntime = session.activeWorldRuntime();
    GameplayRuntimeActorState actorState = {};
    if (pWorldRuntime == nullptr || !pWorldRuntime->actorRuntimeState(actorIndex, actorState))
    {
        return std::nullopt;
    }

    return std::array<float, 3>{
        actorState.preciseX,
        actorState.preciseY,
        actorState.preciseZ + static_cast<float>(actorState.height) * 0.5f
    };
}

void syncAmbientEffect(EffectSystem &effects, const EffectLibrary &library, const std::string &id,
    EffectHandle &handle, const EffectSpawnParams &params, bool emitting)
{
    if (!emitting)
    {
        effects.stop(handle, EffectStopMode::Drain);
        handle = {};
        return;
    }
    const EffectDefinition *pDefinition = library.find(id);
    if (pDefinition == nullptr)
    {
        return; // Model-only headless checks do not load the effect library.
    }
    // Start the next emission cycle while the previous cycle's last particles finish fading.
    if (effects.elapsedSeconds(handle) >= pDefinition->durationSeconds)
    {
        effects.stop(handle, EffectStopMode::Drain);
        handle = {};
    }
    if (!effects.contains(handle))
    {
        handle = effects.spawn(id, params);
    }
    effects.setTransform(handle, params.position, params.rotation, params.scale);
}
}

uint32_t WorldFxSystem::ActorModelBinding::gaitClip(ActorModelGait gait) const
{
    return gait == ActorModelGait::Walk ? clips[size_t(ActorAiAnimationState::Walking)]
        : gait == ActorModelGait::Run ? runClip : sprintClip;
}

float WorldFxSystem::ActorModelBinding::gaitStride(ActorModelGait gait) const
{
    return gait == ActorModelGait::Walk ? strideLength
        : gait == ActorModelGait::Run ? runStrideLength : sprintStrideLength;
}

WorldFxSystem::WorldFxSystem()
{
    m_namedEffects.setModelRuntime(
        &m_models,
        [this](const std::string &id)
        {
            return m_namedEffectResources.findModel(id);
        });
}

void WorldFxSystem::reset()
{
    m_particleUpdateAccumulatorSeconds = 0.0f;
    m_particleSystem.reset();
    m_waterRipples = {};
    m_namedEffects.clear();
    m_beams.clear();
    processNamedEffectAudio();
    for (const auto &[key, instanceId] : m_namedSoundInstances)
    {
        if (m_pNamedEffectAudioSystem != nullptr)
        {
            m_pNamedEffectAudioSystem->stopSoundInstance(instanceId);
        }
    }
    m_namedSoundInstances.clear();
    m_namedEffectLibrary.clear();
    m_namedEffectResources.clear();
    m_inspectPortrait.reset();
    m_actorModels.clear();
    m_actorModelBindings.clear();
    m_pActorModelManifest.reset();
    m_failedActorModelBindings.clear();
    m_actorBurnSurfaces.clear();
    m_corpseAssets.clear();
    m_actorModelsConfigured = false;
    m_corpseSatchelStates.clear();
    m_satchelAssets = {};
    m_projectileModels.clear();
    m_projectileModelBindings.clear();
    m_itemModels.clear();
    m_loadedItemModels.clear();
    m_missingItemModel = {};
    m_reportedMissingItemIcons.clear();
    m_models.clear();
    m_modelAssets.clear();
    m_glowBillboards.clear();
    m_lightEmitters.clear();
    m_contactShadows.clear();
    m_segmentProjectiles.clear();
    m_projectileTrailStates.clear();
    m_persistentImpactLights.clear();
    m_seenImpactIds.clear();
    m_projectileImpactEffectRebinds.clear();
    m_attachedImpactEffects.clear();
    m_projectileFlightEffects.clear();
    m_spellVisualFlights.clear();
    m_partyAuraEffects.clear();
}

bool WorldFxSystem::configureActorModels(const Engine::AssetFileSystem &assets,
    std::shared_ptr<const ActorModelManifest> pManifest, const MonsterTable &monsters,
    const SpriteFrameTable *pSpriteFrames, std::span<const std::string> eagerDescriptors, std::string &error)
{
    // Bindings built later (a summoned monster) use the tables of the current map.
    m_pActorModelAssets = &assets;
    m_pActorModelMonsters = &monsters;
    m_pActorModelSpriteFrames = pSpriteFrames;
    if (m_actorModelsConfigured)
    {
        return true;
    }
    m_actorModelsConfigured = true;
    m_pActorModelManifest = std::move(pManifest);
    for (const std::string &descriptor : eagerDescriptors)
    {
        if (m_pActorModelManifest != nullptr && m_pActorModelManifest->binds(descriptor)
            && !m_actorModelBindings.contains(descriptor) && !buildActorModelBinding(descriptor, error))
        {
            return false;
        }
    }
    return true;
}

bool WorldFxSystem::configureActorModels(const Engine::AssetFileSystem &assets, const std::string &manifestPath,
    const MonsterTable &monsters, const SpriteFrameTable *pSpriteFrames, std::string &error)
{
    if (m_actorModelsConfigured)
    {
        return true;
    }
    std::shared_ptr<ActorModelManifest> pManifest = std::make_shared<ActorModelManifest>();
    if (!pManifest->load(assets, {manifestPath}, {}, monsters, error))
    {
        return false;
    }
    std::vector<std::string> descriptors;
    for (const auto &[descriptor, entry] : pManifest->entries())
    {
        descriptors.push_back(descriptor);
    }
    return configureActorModels(assets, std::move(pManifest), monsters, pSpriteFrames, descriptors, error);
}

const WorldFxSystem::ActorModelBinding *WorldFxSystem::actorModelBinding(const std::string &descriptor)
{
    const auto built = m_actorModelBindings.find(descriptor);
    if (built != m_actorModelBindings.end())
    {
        return &built->second;
    }
    if (m_pActorModelManifest == nullptr || !m_pActorModelManifest->binds(descriptor)
        || m_failedActorModelBindings.contains(descriptor))
    {
        return nullptr;
    }
    std::string error;
    if (!buildActorModelBinding(descriptor, error))
    {
        // Reported once; the monster then has no model.
        std::cerr << "Actor model load failed: " << error << '\n';
        m_failedActorModelBindings.insert(descriptor);
        return nullptr;
    }
    return &m_actorModelBindings.at(descriptor);
}

bool WorldFxSystem::buildActorModelBinding(const std::string &descriptor, std::string &error)
{
    constexpr std::array<const char *, 8> StateNames = {
        "standing", "walking", "attack_melee", "attack_ranged", "hit", "dying", "dead", "fidget"};
    const ActorModelManifest::Entry &manifestEntry = *m_pActorModelManifest->find(descriptor);
    const YAML::Node &entry = manifestEntry.node;
    const std::string &manifestPath = manifestEntry.manifestPath;
    try
    {
        const Engine::ModelLoadResult loaded =
            m_modelAssets.load(*m_pActorModelAssets, entry["model"].as<std::string>());
        if (!loaded)
        {
            error = loaded.error;
            return false;
        }
        ActorModelBinding binding;
        binding.asset = loaded.asset;
        if (const YAML::Node ambient = entry["ambient_effect"])
        {
            binding.ambientEffect = ambient["id"].as<std::string>();
            binding.ambientRadius = ambient["radius"].as<float>();
            if (binding.ambientEffect.empty() || !std::isfinite(binding.ambientRadius)
                || binding.ambientRadius <= 0.0f)
            {
                throw std::runtime_error("actor ambient effect needs an id and positive radius: " + descriptor);
            }
            if (m_namedEffectLibrary.size() != 0 && m_namedEffectLibrary.find(binding.ambientEffect) == nullptr)
            {
                throw std::runtime_error("actor ambient effect not found: " + binding.ambientEffect);
            }
        }
        if (entry["skin"])
        {
            const std::string skin = entry["skin"].as<std::string>();
            const std::optional<uint32_t> variant = binding.asset->findMaterialVariant(skin);
            if (!variant)
            {
                throw std::runtime_error("actor model skin not found: " + skin);
            }
            binding.materialVariant = *variant;
        }
        const YAML::Node attachments = entry["attachments"];
        for (size_t attachmentIndex = 0; attachments && attachmentIndex < attachments.size(); ++attachmentIndex)
        {
            const YAML::Node item = attachments[attachmentIndex];
            const Engine::ModelLoadResult carried =
                m_modelAssets.load(*m_pActorModelAssets, item["model"].as<std::string>());
            if (!carried)
            {
                error = carried.error;
                return false;
            }
            const std::optional<uint32_t> node = binding.asset->findNode(item["node"].as<std::string>());
            if (!node || !carried.asset->skins.empty())
            {
                error = "actor attachment needs a node of the actor and an unskinned model: " + descriptor;
                return false;
            }
            Engine::ModelAttachment attachment{carried.asset, *node, 0};
            // Without its own skin, an item split from the body follows the carrier's skin (same variant names).
            if (item["skin"])
            {
                const std::optional<uint32_t> variant =
                    carried.asset->findMaterialVariant(item["skin"].as<std::string>());
                if (!variant)
                {
                    error = "actor attachment skin not found: " + item["skin"].as<std::string>();
                    return false;
                }
                attachment.materialVariant = *variant;
            }
            else if (entry["skin"])
            {
                attachment.materialVariant =
                    carried.asset->findMaterialVariant(entry["skin"].as<std::string>()).value_or(0);
            }
            binding.attachments.push_back(std::move(attachment));
        }
        binding.scale = entry["scale"].as<float>();
        binding.fxReferenceScale = binding.scale;
        if (entry["scale_reference"])
        {
            const auto standingScale = [&](const std::string &name)
            {
                const MonsterEntry *pMonster = m_pActorModelMonsters->findByInternalName(name);
                const std::optional<uint16_t> frame = pMonster != nullptr && m_pActorModelSpriteFrames != nullptr
                    ? m_pActorModelSpriteFrames->findFrameIndexBySpriteName(pMonster->spriteNames[0]) : std::nullopt;
                const SpriteFrameEntry *pFrame = frame ? m_pActorModelSpriteFrames->getFrame(*frame, 0) : nullptr;
                if (pFrame == nullptr || !std::isfinite(pFrame->scale) || pFrame->scale <= 0.0f)
                {
                    throw std::runtime_error("actor model scale requires a valid standing sprite: " + name);
                }
                return pFrame->scale;
            };
            binding.scale *= standingScale(descriptor) / standingScale(entry["scale_reference"].as<std::string>());
        }
        binding.yawOffset = entry["yaw_offset"].as<float>(0.0f);
        if (entry["fixed_yaw_degrees"])
        {
            const float degrees = entry["fixed_yaw_degrees"].as<float>();
            if (!std::isfinite(degrees))
            {
                error = "actor model fixed_yaw_degrees must be finite: " + descriptor;
                return false;
            }
            binding.fixedYaw = degrees * std::numbers::pi_v<float> / 180.0f;
        }
        binding.zOffset = entry["z_offset"].as<float>(0.0f);
        const YAML::Node deathNode = entry["death_effect"];
        const std::string deathEffect = !deathNode ? "none"
            : deathNode.IsMap() ? deathNode["type"].as<std::string>() : deathNode.as<std::string>();
        if (deathEffect != "none" && deathEffect != "disintegration" && deathEffect != "explosion"
            && deathEffect != "burn")
        {
            error = "unknown actor model death effect: " + deathEffect;
            return false;
        }
        binding.disintegrates = deathEffect == "disintegration";
        binding.explodes = deathEffect == "explosion";
        if (deathEffect == "burn")
        {
            ActorBurnDeath burn;
            burn.startSeconds = deathNode["start"].as<float>(0.0f);
            burn.endSeconds = deathNode["end"].as<float>(1.0f);
            burn.style.charWidth = deathNode["char_width"].as<float>(burn.style.charWidth);
            burn.style.edgeWidth = deathNode["edge_width"].as<float>(burn.style.edgeWidth);
            burn.style.fireWidth = deathNode["fire_width"].as<float>(0.0f);
            const std::vector<float> color =
                deathNode["color"].as<std::vector<float>>(std::vector<float>{1.0f, 0.18f, 0.02f});
            const float brightness = deathNode["brightness"].as<float>(2.0f);
            burn.flamesPerSecond = deathNode["flames_per_second"].as<float>(0.0f);
            burn.flameSize = deathNode["flame_size"].as<float>(0.0f);
            const std::vector<int> lightColor =
                deathNode["light"]["color"].as<std::vector<int>>(std::vector<int>{255, 140, 60});
            burn.lightRadius = deathNode["light"]["radius"].as<float>(0.0f);
            const auto valid = [](float value, float low, float high)
            {
                return std::isfinite(value) && value >= low && value <= high;
            };
            if (color.size() != 3 || lightColor.size() != 3 || !valid(burn.startSeconds, 0.0f, 30.0f)
                || !valid(burn.endSeconds, burn.startSeconds + 0.01f, 30.0f)
                || !valid(burn.style.charWidth, 0.0f, 1.0f) || !valid(burn.style.edgeWidth, 0.001f, 0.5f)
                || !valid(burn.style.fireWidth, 0.0f, 1.0f) || !valid(brightness, 0.0f, 16.0f)
                || !valid(burn.flamesPerSecond, 0.0f, 1000.0f) || !valid(burn.flameSize, 0.0f, 512.0f)
                || !valid(burn.lightRadius, 0.0f, 4096.0f)
                || !std::all_of(color.begin(), color.end(), [&](float value) { return valid(value, 0.0f, 1.0f); })
                || !std::all_of(lightColor.begin(), lightColor.end(),
                    [](int value) { return value >= 0 && value <= 255; }))
            {
                error = "invalid burn death effect: " + descriptor;
                return false;
            }
            for (size_t channel = 0; channel < 3; ++channel)
            {
                burn.style.color[channel] = color[channel] * brightness;
            }
            burn.lightColorAbgr = makeAbgr(uint8_t(lightColor[0]), uint8_t(lightColor[1]),
                uint8_t(lightColor[2]), 255);
            if (deathNode["flame_color"])
            {
                const std::vector<int> flameColor = deathNode["flame_color"].as<std::vector<int>>();
                if (flameColor.size() != 3 || !std::all_of(flameColor.begin(), flameColor.end(),
                        [](int value) { return value >= 0 && value <= 255; }))
                {
                    error = "invalid burn death flame_color: " + descriptor;
                    return false;
                }
                burn.flameTint = std::array<uint8_t, 3>{uint8_t(flameColor[0]), uint8_t(flameColor[1]),
                    uint8_t(flameColor[2])};
            }
            std::shared_ptr<const ActorBurnSurface> &surface =
                m_actorBurnSurfaces[{binding.asset.get(), binding.materialVariant}];
            if (surface == nullptr)
            {
                surface = buildActorBurnSurface(*binding.asset, binding.materialVariant, error);
                if (surface == nullptr)
                {
                    error = descriptor + ": " + error;
                    return false;
                }
            }
            burn.surface = surface;
            binding.burn = std::move(burn);
        }
        if (binding.disintegrates)
        {
            Engine::ModelPose rest;
            Engine::resetModelPose(*binding.asset, rest);
            Engine::evaluateModelHierarchy(*binding.asset, Engine::identityModelMatrix(), rest);
            const Engine::ModelBounds bounds = Engine::modelExactPoseBounds(*binding.asset, rest);
            binding.height = bounds.valid ? bounds.max[1] - bounds.min[1] : 0.0f;
        }
        if (!std::isfinite(binding.scale) || binding.scale <= 0 || !std::isfinite(binding.yawOffset)
            || !std::isfinite(binding.zOffset))
        {
            error = "invalid actor model placement: " + descriptor;
            return false;
        }
        // Wimps never fight back, so they may omit the attack clips and hold the standing pose instead.
        const MonsterTable::MonsterStatsEntry *pStats = m_pActorModelMonsters->findStatsByPictureName(descriptor);
        const bool wimp = pStats != nullptr && pStats->aiType == MonsterTable::MonsterAiType::Wimp;
        std::array<bool, 2> attackClipOmitted = {};
        for (size_t i = 0; i < StateNames.size(); ++i)
        {
            const bool attack = i == 2 || i == 3;
            if (attack && wimp && !entry["clips"][StateNames[i]])
            {
                attackClipOmitted[i - 2] = true;
                binding.clips[i] = binding.clips[0];
                continue;
            }
            const std::string clipName = entry["clips"][StateNames[i]].as<std::string>();
            const std::optional<uint32_t> clip = binding.asset->findClip(clipName);
            if (!clip)
            {
                error = "actor model clip not found: " + clipName;
                return false;
            }
            binding.clips[i] = *clip;
        }
        for (const auto &scriptClip : entry["script_clips"])
        {
            const std::string clipName = scriptClip.second.as<std::string>();
            const std::optional<uint32_t> clip = binding.asset->findClip(clipName);
            if (!clip)
            {
                error = "actor model script clip not found: " + clipName;
                return false;
            }
            binding.scriptClips[scriptClip.first.as<std::string>()] = *clip;
        }
        if (const auto backpedal = binding.scriptClips.find("backpedal"); backpedal != binding.scriptClips.end())
        {
            binding.backpedalClip = backpedal->second;
        }
        if (const auto backpedalRun = binding.scriptClips.find("backpedal_run");
            backpedalRun != binding.scriptClips.end())
        {
            binding.backpedalRunClip = backpedalRun->second;
        }
        const YAML::Node animation = entry["animation"];
        if (animation)
        {
            if (animation["eye_color"])
            {
                const std::vector<int> color = animation["eye_color"].as<std::vector<int>>();
                if (color.size() != 3 || std::any_of(color.begin(), color.end(),
                    [](int value) { return value < 0 || value > 255; }))
                {
                    throw std::runtime_error("actor eye_color requires three sRGB bytes: " + descriptor);
                }
                binding.eyeColorAbgr = makeAbgr(uint8_t(color[0]), uint8_t(color[1]), uint8_t(color[2]), 176);
            }
            for (const char *removed : {"cast_color", "cast_glow_scale", "cast_focus_socket", "cast_focus_glow_scale",
                     "ranged_hand_effects", "ranged_hand_sockets"})
            {
                if (animation[removed])
                {
                    throw std::runtime_error(std::string("actor animation ") + removed
                        + " is replaced by the events' glow, release, glow_scale, color and effects: " + descriptor);
                }
            }
            const auto requireClip = [&](const char *name)
            {
                const std::string clipName = animation[name].as<std::string>();
                const std::optional<uint32_t> clip = binding.asset->findClip(clipName);
                if (!clip)
                {
                    throw std::runtime_error("actor animation clip not found: " + clipName);
                }
                return *clip;
            };
            // Optional: spellcasters are required to have one below.
            if (animation["cast"])
            {
                binding.castClip = requireClip("cast");
            }
            if (const YAML::Node look = animation["look"])
            {
                for (const YAML::Node &nodeName : look["nodes"])
                {
                    const std::optional<uint32_t> node = binding.asset->findNode(nodeName.as<std::string>());
                    if (!node)
                    {
                        throw std::runtime_error("actor look node not found: " + nodeName.as<std::string>());
                    }
                    binding.lookNodes.push_back(*node);
                }
                constexpr float Degrees = std::numbers::pi_v<float> / 180.0f;
                // Head pivot height above the feet in model units, from the rest pose (glTF +Y up).
                Engine::ModelPose rest;
                Engine::resetModelPose(*binding.asset, rest);
                Engine::evaluateModelHierarchy(*binding.asset, Engine::identityModelMatrix(), rest);
                binding.lookHeadHeight = rest.globalMatrices[binding.lookNodes.back()][13];
                binding.lookMaxYaw = look["max_yaw_degrees"].as<float>() * Degrees;
                binding.lookMaxPitch = look["max_pitch_degrees"].as<float>() * Degrees;
                binding.lookMinPitch = look["min_pitch_degrees"]
                    ? look["min_pitch_degrees"].as<float>() * Degrees : -binding.lookMaxPitch;
                const std::string lookTarget = look["target"].as<std::string>("party");
                binding.lookAtCombatTarget = lookTarget == "combat";
                if (look["hold_clip"])
                {
                    const std::optional<uint32_t> clip = binding.asset->findClip(look["hold_clip"].as<std::string>());
                    if (!clip)
                    {
                        throw std::runtime_error("actor look hold_clip not found: " + descriptor);
                    }
                    binding.lookHoldClip = *clip;
                }
                if (binding.lookNodes.empty() || !std::isfinite(binding.lookMaxYaw)
                    || !std::isfinite(binding.lookMaxPitch) || binding.lookMaxYaw < 0.0f
                    || binding.lookMaxYaw > 1.6f || binding.lookMaxPitch < 0.0f || binding.lookMaxPitch > 1.0f
                    || !std::isfinite(binding.lookMinPitch) || binding.lookMinPitch < -1.0f
                    || binding.lookMinPitch > binding.lookMaxPitch || (lookTarget != "party" && lookTarget != "combat")
                    || (binding.lookHoldClip != UINT32_MAX && !binding.lookAtCombatTarget))
                {
                    throw std::runtime_error("invalid actor look: " + descriptor);
                }
            }
            binding.runClip = requireClip("run");
            binding.strideLength = animation["stride_length"].as<float>();
            binding.runStrideLength = animation["run_stride_length"].as<float>(binding.strideLength * 1.55f);
            if (animation["sprint"])
            {
                binding.sprintClip = requireClip("sprint");
                if (!animation["sprint_stride_length"])
                {
                    throw std::runtime_error("actor animation sprint needs sprint_stride_length: " + descriptor);
                }
                binding.sprintStrideLength = animation["sprint_stride_length"].as<float>();
            }
            if (!std::isfinite(binding.strideLength) || binding.strideLength <= 0.0f
                || !std::isfinite(binding.runStrideLength) || binding.runStrideLength <= 0.0f
                || !std::isfinite(binding.sprintStrideLength) || binding.sprintStrideLength < 0.0f
                || (binding.sprintClip != UINT32_MAX && binding.sprintStrideLength == 0.0f))
            {
                throw std::runtime_error("invalid actor animation stride: " + descriptor);
            }
            for (const ActorModelGait gait : {ActorModelGait::Walk, ActorModelGait::Run, ActorModelGait::Sprint})
            {
                const uint32_t gaitClip = binding.gaitClip(gait);
                const float seconds = gaitClip != UINT32_MAX ? binding.asset->clips[gaitClip].durationSeconds : 0.0f;
                binding.gaitSpeeds[size_t(gait)] = seconds > 0.0f ? binding.gaitStride(gait) / seconds : 0.0f;
            }
            binding.maxGaitRate = ActorModelDefaultMaxGaitRate;
            if (const YAML::Node gaitRate = animation["gait_rate"])
            {
                if (!gaitRate.IsSequence() || gaitRate.size() != 2)
                {
                    throw std::runtime_error("actor animation gait_rate needs [min, max]: " + descriptor);
                }
                binding.minGaitRate = gaitRate[0].as<float>();
                binding.maxGaitRate = gaitRate[1].as<float>();
                if (!std::isfinite(binding.minGaitRate)
                    || !std::isfinite(binding.maxGaitRate) || binding.minGaitRate < 0.0f || binding.maxGaitRate < 0.0f
                    || (binding.maxGaitRate > 0.0f && binding.maxGaitRate < binding.minGaitRate))
                {
                    throw std::runtime_error("invalid actor animation gait_rate: " + descriptor);
                }
            }
            binding.blendSeconds = animation["blend_seconds"].as<float>(-1.0f);
            binding.deathBlendSeconds =
                animation["death_blend_seconds"].as<float>(ActorModelDefaultDeathBlendSeconds);
            if (!std::isfinite(binding.blendSeconds) || binding.blendSeconds > 1.0f
                || !std::isfinite(binding.deathBlendSeconds) || binding.deathBlendSeconds < 0.0f
                || binding.deathBlendSeconds > 1.0f)
            {
                throw std::runtime_error("invalid actor animation blend: " + descriptor);
            }
            // The upper-body layer (MM9's `Top` track): an attack on the move plays over the gait from this node
            // down. Without one (MM9's plain animator) the attack plays with the whole body, moving or not.
            if (const YAML::Node upperBodyRoot = animation["upper_body_root"])
            {
                const std::string rootName = upperBodyRoot.as<std::string>();
                const std::optional<uint32_t> root = binding.asset->findNode(rootName);
                if (!root)
                {
                    throw std::runtime_error("actor animation mask root not found: " + rootName);
                }
                std::shared_ptr<std::vector<float>> mask =
                    std::make_shared<std::vector<float>>(binding.asset->nodes.size(), 0.0f);
                for (uint32_t node : binding.asset->hierarchyOrder)
                {
                    const int32_t parent = binding.asset->nodes[node].parentIndex;
                    (*mask)[node] = node == *root ? 1.0f : parent >= 0 ? (*mask)[parent] : 0.0f;
                }
                binding.upperBodyMask = std::move(mask);
            }
            // Named sockets: a node (`name: Node`), or a point on a node (`name: {node: Bone, offset: [x, y, z]}`).
            std::unordered_map<std::string, ActorModelBinding::Socket> sockets;
            for (const auto &socketEntry : animation["sockets"])
            {
                const YAML::Node value = socketEntry.second;
                const std::string nodeName = value.IsMap() ? value["node"].as<std::string>() : value.as<std::string>();
                const std::optional<uint32_t> node = binding.asset->findNode(nodeName);
                if (!node)
                {
                    throw std::runtime_error("actor animation socket node not found: " + descriptor + " " + nodeName);
                }
                ActorModelBinding::Socket socket;
                socket.node = *node;
                if (value.IsMap() && value["offset"])
                {
                    const std::vector<float> offset = value["offset"].as<std::vector<float>>();
                    if (offset.size() != 3 || !std::all_of(offset.begin(), offset.end(),
                            [](float component) { return std::isfinite(component); }))
                    {
                        throw std::runtime_error("actor animation socket offset requires three numbers: " + descriptor);
                    }
                    socket.offset = {offset[0], offset[1], offset[2]};
                }
                sockets[socketEntry.first.as<std::string>()] = socket;
            }
            const auto findSocket = [&](const YAML::Node &name)
            {
                const auto socket = sockets.find(name.as<std::string>());
                if (socket == sockets.end())
                {
                    throw std::runtime_error("actor animation event socket is not in animation.sockets: " + descriptor
                        + " " + name.as<std::string>());
                }
                return socket->second;
            };
            for (size_t eye = 0; eye < binding.eyes.size(); ++eye)
            {
                const auto socket = sockets.find(eye == 0 ? "eye_left" : "eye_right");
                if (socket != sockets.end())
                {
                    binding.eyes[eye] = socket->second;
                }
            }
            // Action events, in ActionEvent order: the melee attack, ranged attack and cast clips.
            constexpr std::array<const char *, 3> EventRoles = {"attack_melee", "attack_ranged", "cast"};
            const YAML::Node events = animation["events"];
            for (const auto &event : events)
            {
                const std::string role = event.first.as<std::string>();
                const auto roleIterator = std::find(EventRoles.begin(), EventRoles.end(), role);
                if (roleIterator == EventRoles.end())
                {
                    throw std::runtime_error("unknown actor animation event role: " + role);
                }
                const size_t roleIndex = size_t(roleIterator - EventRoles.begin());
                if ((roleIndex < 2 && attackClipOmitted[roleIndex])
                    || (roleIndex == 2 && binding.castClip == UINT32_MAX))
                {
                    throw std::runtime_error("actor animation event on an omitted clip: " + descriptor + " "
                        + role);
                }
                const uint32_t clip = roleIndex == 2 ? binding.castClip : binding.clips[2 + roleIndex];
                ActorModelBinding::ActionEvent &actionEvent = binding.actionEvents[roleIndex];
                // Unmarked (no impact): the clip runs on the action clock; the event may still name sockets.
                actionEvent.impactSeconds = event.second["impact"].as<float>(-1.0f);
                if (event.second["impact"] && (!std::isfinite(actionEvent.impactSeconds)
                    || actionEvent.impactSeconds <= 0.0f
                    || actionEvent.impactSeconds > binding.asset->clips[clip].durationSeconds))
                {
                    throw std::runtime_error("actor animation event impact outside its clip: " + descriptor + " "
                        + role);
                }
                for (const auto &key : event.second)
                {
                    const std::string name = key.first.as<std::string>();
                    // A melee blow launches nothing: it may glow (glow, glow_scale, color) but has no release.
                    if (name != "impact" && name != "glow" && name != "glow_scale" && name != "color"
                        && (roleIndex == 0 || (name != "release" && (roleIndex != 1 || name != "effects"))))
                    {
                        throw std::runtime_error("unknown actor animation event key: " + descriptor + " " + role + " "
                            + name);
                    }
                }
                if (const YAML::Node glow = event.second["glow"])
                {
                    if (!glow.IsSequence() || glow.size() == 0 || glow.size() > actionEvent.glow.size())
                    {
                        throw std::runtime_error("actor animation event glow requires one to four sockets: "
                            + descriptor + " " + role);
                    }
                    for (const YAML::Node &name : glow)
                    {
                        actionEvent.glow[actionEvent.glowCount++] = findSocket(name);
                    }
                }
                if (event.second["release"])
                {
                    actionEvent.release = findSocket(event.second["release"]);
                }
                actionEvent.glowScale = event.second["glow_scale"].as<float>(1.0f);
                if (!std::isfinite(actionEvent.glowScale) || actionEvent.glowScale <= 0.0f)
                {
                    throw std::runtime_error("invalid actor animation event glow_scale: " + descriptor + " " + role);
                }
                if (event.second["color"])
                {
                    const std::vector<int> color = event.second["color"].as<std::vector<int>>();
                    if (color.size() != 3 || std::any_of(color.begin(), color.end(),
                        [](int value) { return value < 0 || value > 255; }))
                    {
                        throw std::runtime_error("actor animation event color requires three sRGB bytes: "
                            + descriptor + " " + role);
                    }
                    actionEvent.colorAbgr = makeAbgr(uint8_t(color[0]), uint8_t(color[1]), uint8_t(color[2]), 255);
                }
                if (roleIndex == 0 && actionEvent.glowCount > 0 && actionEvent.colorAbgr == 0)
                {
                    throw std::runtime_error("actor melee glow requires a color: " + descriptor);
                }
                // A ranged attack's named effects, per element, replace the glow while its missile winds up.
                if (const YAML::Node effects = event.second["effects"])
                {
                    if (pStats == nullptr || !effects.IsMap() || actionEvent.glowCount == 0)
                    {
                        throw std::runtime_error(
                            "actor ranged effects require missile data, a map and glow sockets: " + descriptor);
                    }
                    for (const auto &recipe : effects)
                    {
                        const FxRecipes::ProjectileRecipe element =
                            FxRecipes::classifyProjectileRecipe(0, recipe.first.as<std::string>(), "", 0);
                        const std::string effect = recipe.second.as<std::string>();
                        if (element < FxRecipes::ProjectileRecipe::MonsterAirBolt
                            || element > FxRecipes::ProjectileRecipe::MonsterDarkBolt
                            || m_namedEffectLibrary.find(effect) == nullptr)
                        {
                            throw std::runtime_error("actor ranged effect element/effect not found: " + descriptor);
                        }
                        for (size_t slot = 0; slot < 2; ++slot)
                        {
                            const bool hasMissile = slot == 0 ? pStats->attack1HasMissile : pStats->attack2HasMissile;
                            const std::string &token = slot == 0
                                ? pStats->attack1MissileType : pStats->attack2MissileType;
                            if (hasMissile && element == FxRecipes::classifyProjectileRecipe(0, token, "", 0))
                            {
                                if (!actionEvent.effects[slot].empty())
                                {
                                    throw std::runtime_error("duplicate actor ranged effect element: " + descriptor);
                                }
                                actionEvent.effects[slot] = effect;
                            }
                        }
                    }
                }
            }
        }
        // A spellcaster names its cast clip; it may name its attack clip to cast with the attack gesture.
        if (pStats != nullptr && (pStats->hasSpell1 || pStats->hasSpell2) && binding.castClip == UINT32_MAX)
        {
            throw std::runtime_error("spellcasting actor model requires a cast clip: " + descriptor);
        }
        // The standing pose's top, in model units above the feet: anchors health bars and quest markers.
        Engine::ModelPose standing;
        Engine::resetModelPose(*binding.asset, standing);
        Engine::evaluateModelClip(*binding.asset, binding.clips[0], 0.0f, standing);
        Engine::evaluateModelHierarchy(*binding.asset, Engine::identityModelMatrix(), standing);
        const Engine::ModelBounds standingBounds = Engine::modelExactPoseBounds(*binding.asset, standing, true);
        binding.standingHeight = standingBounds.valid ? standingBounds.max[1] : 0.0f;
        m_actorModelBindings.emplace(descriptor, std::move(binding));
    }
    catch (const YAML::Exception &exception)
    {
        error = manifestPath + ": " + exception.what();
        return false;
    }
    catch (const std::runtime_error &exception)
    {
        error = manifestPath + ": " + exception.what();
        return false;
    }
    return true;
}

void WorldFxSystem::stopActorChargeFx(ActorModelInstance &model, EffectStopMode mode)
{
    for (EffectHandle &effect : model.chargeEffects)
    {
        m_namedEffects.stop(effect, mode);
        effect = {};
    }
}

std::optional<std::array<float, 3>> WorldFxSystem::actorSocketPoint(const ActorModelInstance &model,
    const ActorModelBinding::Socket &socket) const
{
    const Engine::ModelMatrix *pNode = m_models.nodeMatrix(model.handle, socket.node);
    if (pNode == nullptr)
    {
        return std::nullopt;
    }
    const Engine::ModelMatrix &node = *pNode;
    const std::array<float, 3> &offset = socket.offset;
    std::array<float, 3> point = {};
    for (size_t axis = 0; axis < 3; ++axis)
    {
        point[axis] = node[axis] * offset[0] + node[4 + axis] * offset[1] + node[8 + axis] * offset[2]
            + node[12 + axis];
    }
    return point;
}

void WorldFxSystem::resolveActorCharge(ActorModelInstance &model) const
{
    // The projectile the charge releases: the spell's, or the ranged attack's missile object.
    // A melee blow has none: it glows only in its event's colour.
    FxRecipes::ProjectileRecipe recipe = FxRecipes::ProjectileRecipe::None;
    std::string chargeObjectName;
    if (model.chargeRole == ActorCharge::Cast)
    {
        recipe = FxRecipes::classifyProjectileRecipe(int(model.chargeSpellId), "", "", 0);
    }
    else if (model.chargeRole == ActorCharge::Ranged && m_pProjectileMonsterTable != nullptr
        && m_pMonsterProjectileTable != nullptr && m_pProjectileObjectTable != nullptr)
    {
        const MonsterTable::MonsterStatsEntry *pStats = m_pProjectileMonsterTable->findStatsById(model.monsterId);
        const MonsterProjectileEntry *pMissile = pStats == nullptr ? nullptr
            : m_pMonsterProjectileTable->findByToken(
                model.secondaryAttack ? pStats->attack2MissileType : pStats->attack1MissileType);
        const ObjectEntry *pObject = pMissile == nullptr ? nullptr
            : m_pProjectileObjectTable->findByObjectId(int16_t(pMissile->objectId));
        if (pObject != nullptr)
        {
            recipe = FxRecipes::classifyProjectileRecipe(0, pObject->internalName, pObject->spriteName,
                pObject->flags);
            chargeObjectName = pObject->internalName;
        }
    }
    const ActorModelBinding::ActionEvent &event = model.pBinding->actionEvents[size_t(model.chargeRole) - 1];
    model.chargeResolved = true;
    model.chargeEffect = model.chargeRole == ActorCharge::Ranged ? event.effects[model.secondaryAttack] : std::string();
    // A spell always charges (white without an element); a physical missile (an arrow, a rock) only in an authored
    // colour.
    model.chargeGlows = model.chargeEffect.empty() && (model.chargeRole == ActorCharge::Cast || event.colorAbgr != 0
        || (recipe != FxRecipes::ProjectileRecipe::None && recipe != FxRecipes::ProjectileRecipe::Arrow
            && recipe != FxRecipes::ProjectileRecipe::FireArrow && recipe != FxRecipes::ProjectileRecipe::Cannonball));
    // The colour of the projectile's flight light when the enhanced style gives it one (a robot's plasma bolt, a
    // dragon's breath), else of its recipe.
    const ProjectileEffectBinding *pProjectile = projectileEffectBinding(recipe, model.monsterId, chargeObjectName);
    model.chargeColor = event.colorAbgr != 0 ? event.colorAbgr
        : pProjectile != nullptr && pProjectile->light
            ? makeAbgr(pProjectile->light->rgb[0], pProjectile->light->rgb[1], pProjectile->light->rgb[2], 255)
            : FxRecipes::projectileRecipeColorAbgr(recipe);
}

void WorldFxSystem::updateActorLook(ActorModelInstance &model, const GameplayRuntimeActorState &state,
    const IGameplayWorldRuntime &world, float scale, float partyDistance, float deltaSeconds, bool canLook,
    bool talking)
{
    // The party's eyes (the camera), seen from the head pivot at its rest height. The look eases back to the clip's
    // own head when the party is behind the reach of the turn, far away, or the actor is dying. It is decided and
    // applied at most 30 times a second (15 beyond the animation LOD distance), each actor on its own phase.
    constexpr float LookRange = 2048.0f;
    constexpr float BehindMargin = 0.35f;
    constexpr float EaseSeconds = 0.18f;
    // An idle turret's scan pitch (and its return to it from a held aim) eases slowly.
    constexpr float ScanEaseSeconds = 0.6f;
    const ActorModelBinding &binding = *model.pBinding;
    const float interval = partyDistance > 1500.0f ? 1.0f / 15.0f : 1.0f / 30.0f;
    if (!model.lookStarted)
    {
        model.lookClock = interval * std::fmod(float(model.actorId) * 0.618034f, 1.0f);
        model.lookStarted = true;
    }
    model.lookClock += deltaSeconds;
    if (model.lookClock < interval)
    {
        return;
    }
    const float stepSeconds = std::min(model.lookClock, 0.25f);
    model.lookClock = 0.0f;
    float targetYaw = 0.0f;
    float targetPitch = 0.0f;
    // The party's eyes within LookRange, or (`target: combat`) the combat target at any distance; an MM9 actor's the
    // target its AI holds or the party talking to it, at any distance, and nothing for a row without HeadTurn.
    canLook = canLook && state.headTurn;
    const bool heldActor = state.looksAtHeldTarget && !binding.lookAtCombatTarget && !talking && state.holdsActorTarget;
    const bool hasLookTarget = binding.lookAtCombatTarget ? state.hasAimTarget
        : state.looksAtHeldTarget ? talking || state.holdsPartyTarget || state.holdsActorTarget
        : partyDistance < LookRange;
    if (canLook && hasLookTarget)
    {
        const std::array<float, 3> target = binding.lookAtCombatTarget
            ? std::array<float, 3>{state.aimTargetX, state.aimTargetY, state.aimTargetZ}
            : heldActor ? std::array<float, 3>{state.heldTargetX, state.heldTargetY, state.heldTargetZ}
            : std::array<float, 3>{world.partyX(), world.partyY(), world.partyEyeZ()};
        const float dx = target[0] - state.preciseX;
        const float dy = target[1] - state.preciseY;
        const float dz = target[2] - (state.preciseZ + binding.zOffset + scale * binding.lookHeadHeight);
        const float yaw = std::remainder(std::atan2(dy, dx) - model.yaw, 2.0f * std::numbers::pi_v<float>);
        if (std::abs(yaw) <= binding.lookMaxYaw + BehindMargin)
        {
            targetYaw = std::clamp(yaw, -binding.lookMaxYaw, binding.lookMaxYaw);
            targetPitch = std::clamp(std::atan2(dz, std::hypot(dx, dy)), binding.lookMinPitch, binding.lookMaxPitch);
        }
    }
    // An idle turret (tactics `scan`): the body sweeps, the look only wanders the barrel's pitch.
    const bool scanning = canLook && binding.lookAtCombatTarget && !state.hasAimTarget && state.aimScanning;
    if (scanning)
    {
        targetPitch = std::clamp(state.aimScanPitchRadians, binding.lookMinPitch, binding.lookMaxPitch);
    }
    if (targetYaw == 0.0f && targetPitch == 0.0f && model.lookYaw == 0.0f && model.lookPitch == 0.0f)
    {
        return;
    }
    const float follow = 1.0f - std::exp(-stepSeconds / (scanning ? ScanEaseSeconds : EaseSeconds));
    model.lookYaw += (targetYaw - model.lookYaw) * follow;
    model.lookPitch += (targetPitch - model.lookPitch) * follow;
    if (std::abs(model.lookYaw) < 1.0e-4f && std::abs(model.lookPitch) < 1.0e-4f)
    {
        model.lookYaw = 0.0f;
        model.lookPitch = 0.0f;
        m_models.setNodeRotations(model.handle, {});
        return;
    }
    // World turn: pitch about the body's horizontal side axis (forward x up), then yaw about up. Each node takes an
    // equal power of it, so the chain's tip ends with the whole turn.
    using Quaternion = std::array<float, 4>;
    const auto axisAngle = [](float x, float y, float z, float angle)
    {
        const float half = 0.5f * angle;
        return Quaternion{x * std::sin(half), y * std::sin(half), z * std::sin(half), std::cos(half)};
    };
    const auto multiply = [](const Quaternion &a, const Quaternion &b)
    {
        return Quaternion{a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
            a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
            a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
            a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2]};
    };
    const Quaternion turn = multiply(axisAngle(0.0f, 0.0f, 1.0f, model.lookYaw),
        axisAngle(std::sin(model.yaw), -std::cos(model.yaw), 0.0f, model.lookPitch));
    const float sinHalf = std::hypot(turn[0], turn[1], turn[2]);
    const float angle = 2.0f * std::atan2(sinHalf, turn[3]) / float(binding.lookNodes.size());
    const Quaternion share = axisAngle(turn[0] / sinHalf, turn[1] / sinHalf, turn[2] / sinHalf, angle);
    std::vector<Engine::ModelNodeRotation> rotations;
    rotations.reserve(binding.lookNodes.size());
    for (uint32_t node : binding.lookNodes)
    {
        rotations.push_back({node, share});
    }
    m_models.setNodeRotations(model.handle, std::move(rotations));
}

void WorldFxSystem::syncActorModels(const IGameplayWorldRuntime &world, float worldDeltaSeconds,
    std::optional<size_t> liveActorIndex, float liveDeltaSeconds)
{
    if (m_inspectPortrait && !std::exchange(m_inspectPortrait->requested, false))
    {
        releaseInspectPortrait();
    }
    if (m_pActorModelManifest == nullptr || m_pActorModelManifest->entries().empty())
    {
        return;
    }
    const uint32_t syncPass = ++m_actorModelSyncPass;
    const MonsterTable *pMonsters = world.monsterTable();
    for (size_t index = 0; pMonsters != nullptr && index < world.mapActorCount(); ++index)
    {
        const float deltaSeconds = index == liveActorIndex ? liveDeltaSeconds : worldDeltaSeconds;
        GameplayRuntimeActorState state;
        if (!world.actorRuntimeState(index, state) || state.isInvisible)
        {
            // A NoCorpse actor turns invisible when it dies; its burning model finishes the death and burns out.
            const auto remains = m_actorModels.find(index);
            if (remains != m_actorModels.end() && burningRemains(remains->second, deltaSeconds))
            {
                remains->second.syncPass = syncPass;
            }
            continue;
        }
        const MonsterEntry *pMonster = pMonsters->findById(state.monsterId);
        if (pMonster == nullptr)
        {
            continue;
        }
        auto instance = m_actorModels.find(index);
        // The binding follows from the monster; an existing model of the same monster keeps its lookup.
        const ActorModelBinding *pBinding = instance != m_actorModels.end()
            && instance->second.monsterId == state.monsterId ? instance->second.pBinding : nullptr;
        if (pBinding == nullptr)
        {
            pBinding = actorModelBinding(pMonster->internalName);
            if (pBinding == nullptr)
            {
                continue;
            }
        }
        const ActorModelBinding &binding = *pBinding;
        if (goneCorpse(index) != nullptr)
        {
            continue;   // sunk; its loot satchel presents the actor
        }
        if (instance != m_actorModels.end()
            && (instance->second.actorId != state.actorId || instance->second.monsterId != state.monsterId))
        {
            stopActorChargeFx(instance->second, EffectStopMode::Drain);
            m_namedEffects.stop(instance->second.ambientEffect, EffectStopMode::Immediate);
            m_models.destroy(instance->second.handle);
            m_actorModels.erase(instance);
            instance = m_actorModels.end();
        }
        if (instance == m_actorModels.end())
        {
            const Engine::ModelInstanceHandle handle = m_models.create(binding.asset);
            m_models.setMaterialVariant(handle, binding.materialVariant);
            m_models.setAttachments(handle, binding.attachments);
            instance = m_actorModels.emplace(index, ActorModelInstance{handle, state.actorId, state.monsterId}).first;
        }
        instance->second.syncPass = syncPass;
        m_models.setOutlineColor(instance->second.handle, 0);
        m_models.setHitFlash(instance->second.handle, state.hitFlash);
        m_models.setEmissionMultiplier(instance->second.handle, state.emissionMultiplier);
        const std::optional<Engine::ModelShieldShell> shieldShell = actorShieldShell(state.shield, state.preciseZ,
            float(state.bodyHeight > 0 ? state.bodyHeight : state.height), m_shieldDomeTimeSeconds, true);
        m_models.setShieldShell(instance->second.handle, shieldShell ? &*shieldShell : nullptr);
        const size_t animationIndex = size_t(state.animationState);
        if (animationIndex >= binding.clips.size())
        {
            continue;
        }
        ActorModelInstance &model = instance->second;
        model.pBinding = &binding;
        const float scale = binding.scale * state.visualScale
            * (pMonster->height > 0 && state.bodyHeight > 0 ? float(state.bodyHeight) / pMonster->height : 1.0f);
        model.fxScale = scale / binding.fxReferenceScale;
        const float distance = std::hypot(state.preciseX - model.previousX, state.preciseY - model.previousY);
        const bool teleported = model.initialized && distance > std::max(256.0f, scale * 8.0f);
        const float speed = std::hypot(state.velocityX, state.velocityY);
        const float gaitSpeed = actorModelGaitSpeed(speed, state.intendedSpeed);
        const bool attacking = state.animationState == ActorAiAnimationState::AttackMelee
            || state.animationState == ActorAiAnimationState::AttackRanged;
        // The gait follows what the AI does (MM9_ANIMATION_AUDIT.md A5): a strike counts as hurrying (MM9's attack tick
        // runs to its target), and the gait changes only while the body moves.
        const bool hurrying = state.hurrying || attacking;
        if (binding.fixedYaw)
        {
            model.yaw = *binding.fixedYaw;
        }
        if (!model.initialized || teleported)
        {
            stopActorChargeFx(model, EffectStopMode::Immediate);
            m_namedEffects.stop(model.ambientEffect, EffectStopMode::Immediate);
            model.ambientEffect = {};
            model.yaw = binding.fixedYaw.value_or(state.yawRadians);
            model.gaitPhase = 0.0f;
            model.gaitTravelLead = 0.0f;
        }
        else if (!model.dying && state.animationState != ActorAiAnimationState::Dead && !binding.fixedYaw)
        {
            // Visual facing only. Collision, LOS, paths and projectile aiming retain the AI's exact yaw.
            // Footwork faces the target (the AI's yaw) however it moves.
            model.facingMovement = state.animationState == ActorAiAnimationState::Walking && speed > 4.0f
                && !state.footwork
                && actorModelFacesMovement(state.yawRadians, state.velocityX, state.velocityY, model.facingMovement);
            const float targetYaw =
                model.facingMovement ? std::atan2(state.velocityY, state.velocityX) : state.yawRadians;
            model.yaw = advanceActorModelYaw(model.yaw, targetYaw, deltaSeconds, 3.0f * std::numbers::pi_v<float>);
            if (binding.strideLength > 0.0f && deltaSeconds > 0.0f)
            {
                if (speed > 4.0f)
                {
                    const ActorModelGait chosen =
                        actorModelGait(gaitSpeed / scale, binding.gaitSpeeds, hurrying, model.gait);
                    // A body that starts moving, or turns from backpedalling to moving on, takes its gait at once (its
                    // clip changes anyway); one moving on holds it.
                    model.gait = model.locomoted && state.backpedalling == model.backwards
                        ? holdActorModelGait(model.gait, chosen, model.gaitHeldSeconds, deltaSeconds) : chosen;
                }
                const float stride = binding.gaitStride(model.gait);
                const uint32_t gaitClip = binding.gaitClip(model.gait);
                // The body moves in AI steps: the gait follows its speed between them (smoothActorModelGaitDistance).
                // A body slowed by collision keeps part of its intended gait (actorModelGaitSpeed).
                const float gaitDistance = std::max(
                    smoothActorModelGaitDistance(model.gaitTravelLead, distance, speed, deltaSeconds),
                    ActorModelHinderedGaitShare * state.intendedSpeed * deltaSeconds);
                model.gaitPhase = advanceActorModelGait(model.gaitPhase, actorModelGaitDistance(gaitDistance,
                    stride * scale, deltaSeconds, binding.asset->clips[gaitClip].durationSeconds,
                    gaitSpeed > 4.0f ? binding.minGaitRate : 0.0f, binding.maxGaitRate), stride * scale);
            }
        }
        const bool moving = speed > 4.0f && !teleported;
        // A behaviour script's clip (see ActorBehaviorRuntime) replaces the AI's fallback animation when the model
        // maps the role; otherwise the fallback state plays as usual.
        const auto scriptClip = state.scriptedClip.empty()
            ? binding.scriptClips.end() : binding.scriptClips.find(state.scriptedClip);
        const bool scripted = scriptClip != binding.scriptClips.end();
        const bool casting = !scripted && attacking && state.castingSpell && binding.castClip != UINT32_MAX;
        // A blow, ranged attack or spell charges at its glow sockets while it winds up (ActionEvent).
        const ActorCharge chargeRole = casting ? ActorCharge::Cast
            : scripted || state.castingSpell ? ActorCharge::None
            : state.animationState == ActorAiAnimationState::AttackRanged ? ActorCharge::Ranged
            : state.animationState == ActorAiAnimationState::AttackMelee && binding.actionEvents[0].glowCount > 0
                ? ActorCharge::Melee : ActorCharge::None;
        // A stop between two moves shorter than ActorModelStandGraceSeconds keeps the gait, still.
        model.standSeconds = state.animationState == ActorAiAnimationState::Standing
            ? model.standSeconds + deltaSeconds : 0.0f;
        const bool holdGait = !scripted && !teleported && model.presentedGait && binding.strideLength > 0.0f
            && state.animationState == ActorAiAnimationState::Standing
            && model.standSeconds < ActorModelStandGraceSeconds;
        const size_t presentedIndex = holdGait ? size_t(ActorAiAnimationState::Walking) : animationIndex;
        const bool restart = model.initialized && (model.previousState != presentedIndex
            || model.casting != casting || model.scripted != scripted
            || (attacking && state.animationTimeTicks + 0.01f < model.previousTime));
        // An attack's legs follow the body's motion as MM9's SetState does, held against step-to-step flicker
        // (advanceActorModelAttackLegs). A model without an upper-body mask (MM9's plain animator: no `Top`) attacks
        // with its whole body, moving or not.
        if (attacking)
        {
            advanceActorModelAttackLegs(model.attackLegs, restart || !model.initialized, moving, deltaSeconds);
        }
        const bool attackMoving = attacking && !teleported && model.attackLegs.moving && binding.upperBodyMask;
        const float elapsed = std::max(state.animationTimeTicks, 0.0f) / 128.0f;
        if (chargeRole != ActorCharge::None && (chargeRole != model.chargeRole || restart
                || model.secondaryAttack != state.secondaryAttack))
        {
            // The charge builds until the action releases: its end, or its sprite's contact frame.
            stopActorChargeFx(model, EffectStopMode::Drain);
            model.chargeDuration = std::max(0.1f, elapsed + state.actionSeconds - state.attackImpactLeadSeconds);
            model.chargeSpellId = casting ? state.castingSpellId : 0;
            model.chargeResolved = false;
            model.hasChargeOrigin = false;
            model.pendingRelease = false;
        }
        // The release may come as the action ends: the charge that was showing goes out then.
        const bool charged = chargeRole != ActorCharge::None || model.chargeRole != ActorCharge::None;
        model.chargeRole = chargeRole;
        model.secondaryAttack = state.secondaryAttack;
        model.chargeProgress = chargeRole != ActorCharge::None
            ? std::clamp(elapsed / model.chargeDuration, 0.0f, 1.0f) : 0.0f;
        if (charged && state.attackImpactTriggered && !model.previousImpact)
        {
            model.pendingRelease = model.hasChargeOrigin && model.chargeOriginAge < 0.15f;
        }
        if (state.animationState == ActorAiAnimationState::GotHit
            || state.animationState == ActorAiAnimationState::Dying || state.isInvisible)
        {
            model.pendingRelease = false;
            model.hasChargeOrigin = false;
        }
        uint32_t clip = scripted ? scriptClip->second : casting ? binding.castClip : binding.clips[animationIndex];
        float time = std::max(state.animationTimeTicks, 0.0f) / 128.0f;
        const float duration = binding.asset->clips[clip].durationSeconds;
        if (scripted)
        {
            time = std::clamp(state.scriptedClipSeconds, 0.0f, duration);
        }
        if (casting)
        {
            time = model.chargeProgress * duration;
        }
        // Marked actions (ActionEvent): the clip's wind-up [0, impact] spans the native action up to the moment the
        // game applies it (the action's end, or its sprite's contact frame), so the marker frame plays then; the rest
        // of the clip follows at its own speed, through the rest of the action and after it as follow-through.
        const size_t eventRole = casting ? 2 : state.animationState == ActorAiAnimationState::AttackMelee ? 0 : 1;
        const float impact = attacking && !scripted ? binding.actionEvents[eventRole].impactSeconds : -1.0f;
        if (impact > 0.0f)
        {
            if (model.markedClip != clip || restart)
            {
                model.markedDuration = std::max(0.1f,
                    elapsed + state.actionSeconds - state.attackImpactLeadSeconds);
                model.markedReleaseElapsed = -1.0f;
            }
            if (state.attackImpactTriggered)
            {
                // The game applied it when the wind-up was due (markedDuration); a frame that sees it later goes on
                // from there rather than holding the marker frame.
                if (model.markedReleaseElapsed < 0.0f)
                {
                    model.markedReleaseElapsed = std::min(elapsed, model.markedDuration);
                }
                time = std::min(duration, impact + elapsed - model.markedReleaseElapsed);
            }
            else
            {
                const float windup = casting
                    ? model.chargeProgress : std::clamp(elapsed / model.markedDuration, 0.0f, 1.0f);
                time = impact * windup;
            }
            model.markedClip = clip;
            model.markedImpact = impact;
            model.markedTime = time;
            model.followClip = UINT32_MAX;
        }
        else if (model.markedClip != UINT32_MAX)
        {
            // The marked action has ended; a hit, death or script cancels its follow-through.
            if (!scripted && (state.animationState == ActorAiAnimationState::Standing
                    || state.animationState == ActorAiAnimationState::Walking))
            {
                model.followClip = model.markedClip;
                model.followTime = std::max(model.markedTime, model.markedImpact);
                model.followStandingOnly = false;
            }
            model.markedClip = UINT32_MAX;
        }
        else if (model.initialized && !scripted && model.previousState == uint8_t(ActorAiAnimationState::Bored)
            && state.animationState == ActorAiAnimationState::Standing)
        {
            // The AI ends a fidget after the native sprite length; a longer fidget clip plays to its end. Fidgets that
            // reuse the standing or walking loop just continue that loop.
            const uint32_t fidgetClip = binding.clips[size_t(ActorAiAnimationState::Bored)];
            const float fidgetTime = std::max(model.previousTime, 0.0f) / 128.0f;
            if (fidgetClip != binding.clips[size_t(ActorAiAnimationState::Standing)]
                && fidgetClip != binding.clips[size_t(ActorAiAnimationState::Walking)]
                && fidgetTime < binding.asset->clips[fidgetClip].durationSeconds)
            {
                model.followClip = fidgetClip;
                model.followTime = fidgetTime;
                model.followStandingOnly = true;
            }
        }
        const bool dying = state.animationState == ActorAiAnimationState::Dying;
        if (binding.disintegrates && dying && !instance->second.dying)
        {
            const float height = binding.scale * state.visualScale * binding.height
                * (pMonster->height > 0 && state.bodyHeight > 0 ? float(state.bodyHeight) / pMonster->height : 1.0f);
            FxRecipes::spawnActorDisintegrationParticles(m_particleSystem, state.actorId,
                state.preciseX, state.preciseY, state.preciseZ + binding.zOffset, height, time, duration);
        }
        if (binding.explodes && dying && !instance->second.dying)
        {
            FxRecipes::ImpactSpawnContext explosion = {};
            explosion.recipe = FxRecipes::ProjectileRecipe::Fireball;
            explosion.x = state.preciseX;
            explosion.y = state.preciseY;
            explosion.z = state.preciseZ + binding.zOffset + float(state.height) * 0.5f;
            FxRecipes::spawnImpactParticles(m_particleSystem, explosion);
        }
        if (binding.burn)
        {
            // One clock from the start of dying, through the Dead state; a corpse first seen dead has burnt out.
            if (dying && !model.dying)
            {
                model.burnSeconds = time;
                model.burnFlameBudget = 0.0f;
            }
            else if (dying || state.animationState == ActorAiAnimationState::Dead)
            {
                model.burnSeconds = model.burnSeconds >= 0.0f ? model.burnSeconds + deltaSeconds
                    : binding.burn->endSeconds + 60.0f;
            }
            else
            {
                model.burnSeconds = -1.0f;
            }
        }
        instance->second.dying = dying;
        if (dying && !binding.disintegrates)
        {
            model.deathClipTime = time;
        }
        else if (state.animationState == ActorAiAnimationState::Dead && model.deathClipTime >= 0.0f)
        {
            // The AI switches to the corpse after the native sprite death length; a longer model death clip
            // finishes first, then the dead clip holds.
            const uint32_t deathClip = binding.clips[size_t(ActorAiAnimationState::Dying)];
            model.deathClipTime += deltaSeconds;
            if (model.deathClipTime < binding.asset->clips[deathClip].durationSeconds)
            {
                clip = deathClip;
                time = model.deathClipTime;
            }
            else
            {
                model.deathClipTime = -1.0f;
            }
        }
        else
        {
            model.deathClipTime = -1.0f;
        }
        if ((state.animationState == ActorAiAnimationState::Standing
                || state.animationState == ActorAiAnimationState::Walking) && duration > 0)
        {
            time = wrapPeriod(time, duration);
        }
        Engine::ModelAnimationLayer layer;
        bool backwardsChanged = false;
        bool reversed = false;
        const bool locomoting = binding.strideLength > 0.0f
            && (state.animationState == ActorAiAnimationState::Walking || attackMoving || holdGait);
        // After an attack the legs blend to the stand at once: holding them would add a second blend.
        model.presentedGait = locomoting && !attacking;
        model.locomoted = locomoting;
        if (locomoting)
        {
            const uint32_t locomotion = binding.gaitClip(model.gait);
            // The model backpedals when its AI asks it to (GameplayRuntimeActorState::backpedalling) and plays every
            // other move forwards, as MM9's Strafe state does: never from the angle between the motion and a facing
            // that lags the AI's (MM9_ANIMATION_AUDIT.md A2). A flier's back-off and swoop beat its wings forwards.
            const bool backwards = holdGait ? model.backwards : state.backpedalling;
            backwardsChanged = backwards != model.backwards;
            model.backwards = backwards;
            // A model's own backpedal clip plays forwards; otherwise the gait plays reversed.
            const uint32_t backpedal = !backwards ? UINT32_MAX
                : model.gait == ActorModelGait::Walk ? binding.backpedalClip
                : binding.backpedalRunClip != UINT32_MAX ? binding.backpedalRunClip : binding.backpedalClip;
            reversed = backwards && backpedal == UINT32_MAX;
            const float phase = reversed ? wrapPeriod(1.0f - model.gaitPhase, 1.0f) : model.gaitPhase;
            if (attacking && binding.upperBodyMask)
            {
                layer = {clip, time, 1.0f, binding.upperBodyMask};
            }
            clip = backpedal != UINT32_MAX ? backpedal : locomotion;
            time = phase * binding.asset->clips[clip].durationSeconds;
        }
        // Follow-through of a finished marked action: the whole body while the actor stands, the upper body over the
        // gait while it walks. It continues the action's clip, so the state change starts no blend.
        bool continuingFollow = false;
        if (model.followClip != UINT32_MAX)
        {
            model.followTime += deltaSeconds;
            const bool standing = state.animationState == ActorAiAnimationState::Standing;
            if (scripted || teleported || model.followTime >= binding.asset->clips[model.followClip].durationSeconds
                || (model.followStandingOnly && !standing)
                || !(standing || state.animationState == ActorAiAnimationState::Walking)
                || (locomoting && !binding.upperBodyMask) || (!locomoting && !standing))
            {
                model.followClip = UINT32_MAX;
            }
            else if (locomoting)
            {
                layer = {model.followClip, model.followTime, 1.0f, binding.upperBodyMask};
                continuingFollow = true;
            }
            else
            {
                clip = model.followClip;
                time = model.followTime;
                continuingFollow = true;
            }
        }
        // `look.hold_clip`: an actor tracking its combat target holds still instead of playing its idle (a turret's
        // scan would swing the guns off the target), and so does an idle turret whose scan its tactics drive.
        if (binding.lookHoldClip != UINT32_MAX && (state.hasAimTarget || state.aimScanning) && !scripted
            && !continuingFollow && !holdGait && (state.animationState == ActorAiAnimationState::Standing
                || state.animationState == ActorAiAnimationState::Bored))
        {
            clip = binding.lookHoldClip;
            time = 0.0f;
        }
        const float presentedTime = time;
        const Engine::ModelAnimationLayer presentedLayer = layer;
        // Animation LOD: actors sample their clips at most 240 times a second, at 60 Hz beyond ~7 m, 15 Hz beyond
        // ~14 m and the native sprite rate (8 Hz) beyond ~28 m. Pose evaluation was a third of the main thread with a
        // crowd at high frame rates. A per-actor phase offset spreads the updates; root motion stays per frame, and an
        // unchanged clip time only recomposes the joint hierarchy.
        const float partyDistance = std::hypot(state.preciseX - world.partyX(), state.preciseY - world.partyY());
        const float sampleStep = !m_actorAnimationLod ? 0.0f
            : partyDistance > 3000.0f ? 1.0f / 8.0f : partyDistance > 1500.0f ? 1.0f / 15.0f
            : partyDistance > 750.0f ? 1.0f / 60.0f : 1.0f / 240.0f;
        if (sampleStep > 0.0f)
        {
            const float offset = sampleStep * wrapPeriod(float(model.actorId) * 0.618034f, 1.0f);
            const auto quantize = [&](float seconds)
            {
                return std::max(0.0f, std::floor((seconds + offset) / sampleStep) * sampleStep - offset);
            };
            time = quantize(time);
            if (layer.weight > 0.0f)
            {
                layer.timeSeconds = quantize(layer.timeSeconds);
            }
        }
        const float sink = actorCorpseSinkDepth(index);
        m_models.setCoverage(model.handle, sink > 0.0f
            ? corpseSinkPresentation(m_corpseSatchelStates.at(index).restSeconds).coverage : 1.0f);
        const Engine::ModelTransform transform = Engine::gltfModelPlacement(
            {state.preciseX, state.preciseY, state.preciseZ + binding.zOffset - sink},
            model.yaw + binding.yawOffset, scale);
        if (!binding.lookNodes.empty())
        {
            updateActorLook(model, state, world, scale, partyDistance, deltaSeconds,
                !dying && !scripted && state.animationState != ActorAiAnimationState::Dead, index == liveActorIndex);
        }
        const float transitionSeconds = state.animationState == ActorAiAnimationState::Dead || teleported ? 0.0f
            : dying ? binding.deathBlendSeconds
            : binding.blendSeconds >= 0.0f ? binding.blendSeconds
            : state.animationState == ActorAiAnimationState::GotHit ? 0.06f : 0.12f;
        if (m_pAnimationTrace != nullptr)
        {
            traceActorAnimation(index, model, clip, presentedTime, presentedLayer, reversed,
                (restart && !continuingFollow) || backwardsChanged, transitionSeconds, speed, deltaSeconds);
        }
        m_models.sampleBlended(model.handle, clip, time, transform, deltaSeconds, transitionSeconds,
            layer, (restart && !continuingFollow) || backwardsChanged, sampleStep);
        model.transform = transform;
        const std::optional<Engine::ModelBurn> burn = actorBurn(model);
        m_models.setBurn(model.handle, burn ? &*burn : nullptr);
        if (burn && deltaSeconds > 0.0f)
        {
            spawnActorBurnFlames(model, *burn, deltaSeconds);
        }
        // A corpse no longer moves once the death clip has finished and its Dead clip is held (past its end, or the
        // corpse's clock stopped: dead actors are not updated). It is then drawn as a static instance of the baked pose
        // (instanced with every corpse of its model, no skinning, coarser LODs); picking and loot still use the actor
        // instance, whose frozen pose matches the bake.
        const uint32_t deadClip = binding.clips[size_t(ActorAiAnimationState::Dead)];
        const float deadDuration = binding.asset->clips[deadClip].durationSeconds;
        // A burnt body rests once its fire is out, with nothing left to draw.
        const bool corpseStandIn = state.animationState == ActorAiAnimationState::Dead && model.deathClipTime < 0.0f
            && clip == deadClip && layer.weight == 0.0f && model.initialized
            && (time >= deadDuration || state.animationTimeTicks == model.previousTime)
            && (!burn || Engine::modelBurnConsumed(*burn));
        if (corpseStandIn != model.corpseStandIn)
        {
            m_models.setStaticStandIn(model.handle, corpseStandIn && !binding.burn
                ? corpseAsset(binding.asset, deadClip, std::min(time, deadDuration)) : nullptr);
            model.corpseStandIn = corpseStandIn;
        }
        model.initialized = true;
        model.previousX = state.preciseX;
        model.previousY = state.preciseY;
        model.previousTime = state.animationTimeTicks;
        model.previousState = uint8_t(presentedIndex);
        model.casting = casting;
        model.scripted = scripted;
        model.previousImpact = state.attackImpactTriggered;
    }
    for (auto iterator = m_actorModels.begin(); iterator != m_actorModels.end();)
    {
        if (iterator->second.syncPass != syncPass)
        {
            stopActorChargeFx(iterator->second, EffectStopMode::Drain);
            m_namedEffects.stop(iterator->second.ambientEffect, EffectStopMode::Drain);
            m_models.destroy(iterator->second.handle);
            iterator = m_actorModels.erase(iterator);
        }
        else
        {
            ++iterator;
        }
    }
}

void WorldFxSystem::traceActorAnimation(size_t actorIndex, const ActorModelInstance &model, uint32_t clip, float time,
    const Engine::ModelAnimationLayer &layer, bool reversed, bool restart, float transitionSeconds, float speed,
    float deltaSeconds) const
{
    const Engine::ModelAsset &asset = *model.pBinding->asset;
    const uint32_t previousClip = m_models.sampledClip(model.handle);
    const Engine::ModelAnimationLayer *pPreviousLayer = m_models.sampledLayer(model.handle);
    // As sampleBlended decides whether a transition starts.
    const bool transition = previousClip != UINT32_MAX && (restart || previousClip != clip
        || (pPreviousLayer != nullptr
            && (pPreviousLayer->clipIndex != layer.clipIndex || pPreviousLayer->mask != layer.mask)));
    ActorAnimationTraceSample sample;
    sample.clip = asset.clips[clip].name;
    sample.timeSeconds = time;
    sample.durationSeconds = asset.clips[clip].durationSeconds;
    sample.reversed = reversed;
    if (layer.weight > 0.0f && layer.clipIndex < asset.clips.size())
    {
        sample.layerClip = asset.clips[layer.clipIndex].name;
        sample.layerTimeSeconds = layer.timeSeconds;
        sample.layerDurationSeconds = asset.clips[layer.clipIndex].durationSeconds;
    }
    sample.speed = speed;
    sample.deltaSeconds = deltaSeconds;
    sample.blendSeconds = transition ? transitionSeconds : -1.0f;
    m_pAnimationTrace->observeAnimation(actorIndex, sample);
}

std::shared_ptr<const WorldFxSystem::ActorBurnSurface> WorldFxSystem::buildActorBurnSurface(
    const Engine::ModelAsset &asset, uint32_t variant, std::string &error)
{
    auto surface = std::make_shared<ActorBurnSurface>();
    // One point per cell of a grid 1/64 of the model's size, so flames spread by area rather than mesh density.
    const Engine::ModelBounds &bounds = asset.staticBounds;
    float extent = 0.0f;
    for (size_t axis = 0; axis < 3; ++axis)
    {
        extent = std::max(extent, bounds.max[axis] - bounds.min[axis]);
    }
    const float cell = std::max(extent, 0.001f) / 64.0f;
    std::unordered_set<uint64_t> occupied;
    for (uint32_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        const Engine::ModelNode &node = asset.nodes[nodeIndex];
        if (node.skinIndex < 0 || node.meshIndex < 0)
        {
            continue;
        }
        const Engine::ModelMesh &mesh = asset.meshes[node.meshIndex];
        for (uint32_t primitiveIndex = 0; primitiveIndex < mesh.primitives.size(); ++primitiveIndex)
        {
            const Engine::ModelPrimitive &primitive = mesh.primitives[primitiveIndex];
            if (primitive.influences.empty())
            {
                continue;
            }
            const int materialIndex = primitive.materialIndices[
                variant < primitive.materialIndices.size() ? variant : 0];
            const int imageIndex = materialIndex >= 0 && size_t(materialIndex) < asset.materials.size()
                ? asset.materials[materialIndex].burnMapImageIndex : -1;
            if (imageIndex < 0)
            {
                error = "a burn death needs a burn map on every skinned material";
                return nullptr;
            }
            // The burn map's order at each vertex, baked by the model cook, so its texture never decodes on the CPU.
            if (primitive.burnOrder.size() != primitive.vertices.size())
            {
                error = "a burn death needs the cooked _BURN_ORDER vertex attribute (cook the model with "
                    "tools/cook_models.py)";
                return nullptr;
            }
            for (uint32_t vertexIndex = 0; vertexIndex < primitive.vertices.size(); ++vertexIndex)
            {
                const std::array<float, 3> &position = primitive.vertices[vertexIndex].position;
                uint64_t key = 0;
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    key = key * 4096 + uint64_t(int64_t(std::floor(position[axis] / cell)) & 4095);
                }
                if (!occupied.insert(key).second)
                {
                    continue;
                }
                surface->points.push_back({primitive.burnOrder[vertexIndex], nodeIndex, primitiveIndex, vertexIndex});
            }
        }
    }
    if (surface->points.empty())
    {
        error = "a burn death needs a skinned mesh";
        return nullptr;
    }
    std::sort(surface->points.begin(), surface->points.end(),
        [](const ActorBurnSurface::Point &left, const ActorBurnSurface::Point &right)
        {
            return left.order < right.order;
        });
    return surface;
}

std::optional<Engine::ModelBurn> WorldFxSystem::actorBurn(const ActorModelInstance &model) const
{
    if (model.pBinding == nullptr || !model.pBinding->burn || model.burnSeconds < 0.0f)
    {
        return std::nullopt;
    }
    // The front sweeps from where the first texels start to char to where the last have burnt away, and on through
    // the lingering fire.
    const ActorBurnDeath &death = *model.pBinding->burn;
    Engine::ModelBurn burn = death.style;
    const float progress = (model.burnSeconds - death.startSeconds) / (death.endSeconds - death.startSeconds);
    burn.front = -burn.charWidth + progress * (1.0f + burn.edgeWidth + burn.charWidth);
    burn.seconds = model.burnSeconds;
    return burn;
}

bool WorldFxSystem::burningRemains(ActorModelInstance &model, float deltaSeconds)
{
    // Presentation only: the actor has left the game, so its model plays the rest of its death clip in place, holds
    // the end of its Dead clip and is released once the fire has consumed it.
    if (model.pBinding == nullptr || !model.pBinding->burn || model.burnSeconds < 0.0f || !model.initialized)
    {
        return false;
    }
    const ActorModelBinding &binding = *model.pBinding;
    model.burnSeconds += deltaSeconds;
    const std::optional<Engine::ModelBurn> burn = actorBurn(model);
    if (Engine::modelBurnConsumed(*burn))
    {
        return false;
    }
    uint32_t clip = binding.clips[size_t(ActorAiAnimationState::Dead)];
    float time = binding.asset->clips[clip].durationSeconds;
    if (model.deathClipTime >= 0.0f)
    {
        const uint32_t deathClip = binding.clips[size_t(ActorAiAnimationState::Dying)];
        model.deathClipTime += deltaSeconds;
        if (model.deathClipTime < binding.asset->clips[deathClip].durationSeconds)
        {
            clip = deathClip;
            time = model.deathClipTime;
        }
        else
        {
            model.deathClipTime = -1.0f;
        }
    }
    m_models.sampleBlended(model.handle, clip, time, model.transform, deltaSeconds, 0.0f);
    m_models.setBurn(model.handle, &*burn);
    if (deltaSeconds > 0.0f)
    {
        spawnActorBurnFlames(model, *burn, deltaSeconds);
    }
    return true;
}

void WorldFxSystem::spawnActorBurnFlames(ActorModelInstance &model, const Engine::ModelBurn &burn, float deltaSeconds)
{
    // Flames rise from the surface points in the burning band: the glowing edge and the fresh fire behind it.
    const ActorBurnDeath &death = *model.pBinding->burn;
    const std::vector<ActorBurnSurface::Point> &points = death.surface->points;
    const float lowest = burn.front - burn.edgeWidth - 0.5f * burn.fireWidth;
    const auto first = std::lower_bound(points.begin(), points.end(), lowest,
        [](const ActorBurnSurface::Point &point, float order) { return point.order < order; });
    const auto last = std::upper_bound(first, points.end(), burn.front + 0.5f * burn.edgeWidth,
        [](float order, const ActorBurnSurface::Point &point) { return order < point.order; });
    const Engine::ModelAsset *pAsset = m_models.asset(model.handle);
    const Engine::ModelPose *pPose = m_models.pose(model.handle, false);
    if (first == last || death.flamesPerSecond <= 0.0f || death.flameSize <= 0.0f || pAsset == nullptr
        || pPose == nullptr)
    {
        model.burnFlameBudget = 0.0f;
        return;
    }
    model.burnFlameBudget = std::min(model.burnFlameBudget + death.flamesPerSecond * deltaSeconds, 32.0f);
    for (; model.burnFlameBudget >= 1.0f; model.burnFlameBudget -= 1.0f)
    {
        const uint32_t seed = model.actorId * 0x9e3779b9u + ++model.burnFlameSerial * 0x85ebca6bu;
        const ActorBurnSurface::Point &point = first[((seed >> 7) ^ (seed >> 19)) % uint32_t(last - first)];
        const Engine::ModelPrimitive &primitive =
            pAsset->meshes[pAsset->nodes[point.nodeIndex].meshIndex].primitives[point.primitiveIndex];
        const std::array<float, 3> position =
            Engine::skinnedModelVertex(*pAsset, *pPose, point.nodeIndex, primitive, point.vertexIndex);
        FxRecipes::spawnActorBurnFlame(m_particleSystem, seed, position[0], position[1], position[2],
            death.flameSize * model.fxScale, death.flameTint);
    }
}

std::shared_ptr<const Engine::ModelAsset> WorldFxSystem::corpseAsset(
    const std::shared_ptr<const Engine::ModelAsset> &asset, uint32_t deadClip, float timeSeconds)
{
    // Keyed by the held time in milliseconds: a corpse shows its Dead clip at 0 s (actor clock stopped at death) or at
    // its end, so a model gets one or two bakes.
    const uint32_t milliseconds = uint32_t(std::lround(timeSeconds * 1000.0f));
    std::shared_ptr<const Engine::ModelAsset> &baked = m_corpseAssets[{asset.get(), deadClip, milliseconds}];
    if (baked == nullptr)
    {
        Engine::ModelPose pose;
        Engine::resetModelPose(*asset, pose);
        Engine::evaluateModelClip(*asset, deadClip, float(milliseconds) / 1000.0f, pose);
        Engine::evaluateModelHierarchy(*asset, Engine::identityModelMatrix(), pose);
        baked = Engine::bakeStaticModelPose(*asset, pose);
    }
    return baked;
}

bool WorldFxSystem::configureCorpseSatchels(const Engine::AssetFileSystem &assets, std::string &error)
{
    if (m_satchelAssets[0] != nullptr)
    {
        return true;
    }
    for (size_t tier = 0; tier < m_satchelAssets.size(); ++tier)
    {
        const std::string path = "engine/models/loot_satchel_t" + std::to_string(tier + 1) + ".glb";
        const Engine::ModelLoadResult loaded = m_modelAssets.load(assets, path);
        if (!loaded)
        {
            error = loaded.error;
            m_satchelAssets = {};
            return false;
        }
        m_satchelAssets[tier] = loaded.asset;
    }
    return true;
}

void WorldFxSystem::syncBeams(IGameplayWorldRuntime &world, float deltaSeconds)
{
    EventRuntimeState *pState = world.eventRuntimeState();
    const auto stopBeam = [this](const std::string &name)
    {
        for (auto beam = m_beams.begin(); beam != m_beams.end();)
        {
            if (beam->name == name)
            {
                m_namedEffects.stop(beam->handle, EffectStopMode::Drain);
                beam = m_beams.erase(beam);
            }
            else
            {
                ++beam;
            }
        }
    };
    if (pState != nullptr)
    {
        for (const std::string &name : pState->beamStops)
        {
            stopBeam(name);
        }
        pState->beamStops.clear();
        for (const EventRuntimeState::BeamRequest &request : pState->beamRequests)
        {
            // The same beam asked again moves (a turning gun's lock); another effect under its name replaces it.
            const auto drawing = std::find_if(m_beams.begin(), m_beams.end(), [&request](const ActiveBeam &beam)
            {
                return beam.name == request.name && beam.effectId == request.effectId;
            });
            if (drawing != m_beams.end() && m_namedEffects.contains(drawing->handle))
            {
                m_namedEffects.setTransform(drawing->handle, request.from, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f);
                drawing->to = request.to;
                drawing->toParty = request.toParty;
                drawing->timed = request.seconds > 0.0f;
                drawing->remainingSeconds = request.seconds;
                continue;
            }
            stopBeam(request.name);
            EffectSpawnParams params;
            params.position = request.from;
            const EffectHandle handle = m_namedEffects.spawn(request.effectId, params);
            if (!m_namedEffects.contains(handle))
            {
                std::cerr << "Scripted beam effect spawn failed: " << request.effectId << '\n';
                continue;
            }
            m_beams.push_back({request.name, request.effectId, handle, request.to, request.toParty,
                request.seconds > 0.0f, request.seconds});
        }
        pState->beamRequests.clear();
    }
    // The party's chest, where its shots come from.
    const std::array<float, 3> party = {world.partyX(), world.partyY(), world.partyFootZ() + 96.0f};
    for (auto beam = m_beams.begin(); beam != m_beams.end();)
    {
        beam->remainingSeconds -= deltaSeconds;
        if (!m_namedEffects.contains(beam->handle) || (beam->timed && beam->remainingSeconds <= 0.0f))
        {
            m_namedEffects.stop(beam->handle, EffectStopMode::Drain);
            beam = m_beams.erase(beam);
            continue;
        }
        m_namedEffects.setBeamTarget(beam->handle, beam->toParty ? party : beam->to);
        ++beam;
    }
}

void WorldFxSystem::syncShieldDomes(const IGameplayWorldRuntime &world, float deltaSeconds)
{
    constexpr float GrowSeconds = 0.35f;
    constexpr float FadeOutSeconds = 0.45f;
    m_shieldDomeTimeSeconds += deltaSeconds;

    for (auto &[key, state] : m_shieldDomeStates)
    {
        state.present = false;
    }

    const ActorBehaviorRuntime *pBehaviors = world.actorBehaviorRuntime();
    const std::vector<ActorBehaviorWardDisplay> noDisplays;

    for (const ActorBehaviorWardDisplay &display : pBehaviors != nullptr ? pBehaviors->wardDisplays() : noDisplays)
    {
        ShieldDomeState &state = m_shieldDomeStates[std::to_string(display.actorId) + ":" + display.wardId];
        state.present = true;
        state.fadeOutSeconds = 0.0f;
        ShieldDomeDraw &draw = state.draw;
        const float grow = std::clamp(display.ageSeconds / GrowSeconds, 0.0f, 1.0f);
        const float easedGrow = grow * grow * (3.0f - 2.0f * grow);
        draw.center = {display.center.x, display.center.y, display.center.z};
        draw.radius = display.radius * (0.75f + 0.25f * easedGrow);
        draw.groundZ = display.groundZ;
        draw.color = {display.visual.color[0] / 255.0f, display.visual.color[1] / 255.0f,
            display.visual.color[2] / 255.0f};
        // A brief flare as it forms, then the steady shell.
        draw.strength = display.visual.intensity * easedGrow * (1.0f + 0.6f * (1.0f - grow));
        draw.rimPower = display.visual.rimPower;
        draw.noise = display.visual.noise;

        std::vector<ActorBehaviorWardDisplay::Impact> impacts = display.impacts;
        std::sort(impacts.begin(), impacts.end(),
            [](const ActorBehaviorWardDisplay::Impact &left, const ActorBehaviorWardDisplay::Impact &right)
            {
                return left.ageSeconds < right.ageSeconds;
            });

        for (size_t hitIndex = 0; hitIndex < ShieldDomeDraw::MaxHits; ++hitIndex)
        {
            draw.hits[hitIndex] = hitIndex < impacts.size()
                ? std::array<float, 4>{impacts[hitIndex].direction.x, impacts[hitIndex].direction.y,
                    impacts[hitIndex].direction.z, impacts[hitIndex].ageSeconds}
                : std::array<float, 4>{0.0f, 0.0f, 0.0f, -1.0f};
        }
    }

    m_shieldDomes.clear();

    for (auto iterator = m_shieldDomeStates.begin(); iterator != m_shieldDomeStates.end();)
    {
        ShieldDomeState &state = iterator->second;
        ShieldDomeDraw draw = state.draw;

        if (!state.present)
        {
            // The ward lapsed, broke or its owner died: the shell swells slightly and fades out.
            state.fadeOutSeconds += deltaSeconds;

            if (state.fadeOutSeconds >= FadeOutSeconds)
            {
                iterator = m_shieldDomeStates.erase(iterator);
                continue;
            }

            const float fade = 1.0f - state.fadeOutSeconds / FadeOutSeconds;
            draw.strength *= fade;
            draw.radius *= 1.0f + 0.12f * (1.0f - fade);
        }

        m_shieldDomes.push_back(draw);
        ++iterator;
    }
}

void WorldFxSystem::syncCorpseSatchels(const IGameplayWorldRuntime &world, float deltaSeconds)
{
    if (m_satchelAssets[0] == nullptr)
    {
        return;
    }
    // GLB metres to world units, as the creature models. The satchels are authored at their in-game widths
    // (0.5-1.25 m, the size of the game's dropped items, so grass does not hide them).
    constexpr float UnitsPerMetre = 105.0f;
    const size_t actorCount = world.mapActorCount();
    for (auto iterator = m_corpseSatchelStates.lower_bound(actorCount); iterator != m_corpseSatchelStates.end();)
    {
        m_models.destroy(iterator->second.handle);
        iterator = m_corpseSatchelStates.erase(iterator);
    }
    // One pass over the actors, each state read once, with the ordered satchels walked alongside. A satchel goes when
    // its actor is no longer a fallen body (revived, gone invisible, or its slot reused by another actor).
    auto next = m_corpseSatchelStates.begin();
    for (size_t index = 0; index < actorCount; ++index)
    {
        GameplayRuntimeActorState state;
        const bool fallen = world.actorRuntimeState(index, state) && !state.isInvisible
            && (state.isDead || state.animationState == ActorAiAnimationState::Dying
                || state.animationState == ActorAiAnimationState::Dead);
        auto found = next != m_corpseSatchelStates.end() && next->first == index ? next : m_corpseSatchelStates.end();
        if (found != m_corpseSatchelStates.end())
        {
            ++next;
            if (!fallen || state.actorId != found->second.actorId)
            {
                m_models.destroy(found->second.handle);
                m_corpseSatchelStates.erase(found);
                found = m_corpseSatchelStates.end();
            }
        }
        if (!fallen)
        {
            continue;
        }
        const std::optional<uint32_t> lootValue = world.corpseLootValue(index);
        if (found == m_corpseSatchelStates.end())
        {
            CorpseSatchel corpse;
            corpse.actorId = state.actorId;
            corpse.yaw = std::fmod(float(state.actorId) * 2.399963f, 2.0f * std::numbers::pi_v<float>);
            // A corpse first seen at rest (a loaded map) shows its satchel at once; a fresh death plays out.
            if (state.animationState == ActorAiAnimationState::Dead && lootValue)
            {
                corpse.restSeconds = CorpseRestSeconds + std::max(CorpseSinkSeconds, CorpseSatchelAppearSeconds);
                corpse.gone = true;
            }
            found = m_corpseSatchelStates.emplace_hint(next, index, corpse);
        }
        CorpseSatchel &corpse = found->second;
        if (!corpse.gone)
        {
            // At rest: a model once its death clip has finished and its corpse pose is held, a sprite in its dead frame.
            // Without rolled loot (no corpse view), the body stays.
            const auto model = m_actorModels.find(index);
            const bool atRest = model != m_actorModels.end() ? model->second.corpseStandIn
                : state.animationState == ActorAiAnimationState::Dead;
            if (corpse.restSeconds < 0.0f && atRest && lootValue)
            {
                const Engine::ModelBounds *pPose =
                    model != m_actorModels.end() ? m_models.cullingBounds(model->second.handle) : nullptr;
                const float height = pPose != nullptr && pPose->valid ? pPose->max[2] - state.preciseZ
                    : float(state.bodyHeight > 0 ? state.bodyHeight : state.height);
                corpse.sinkDepth = std::max(height, 16.0f) + 8.0f;
                corpse.restSeconds = 0.0f;
            }
            else if (corpse.restSeconds >= 0.0f)
            {
                corpse.restSeconds += deltaSeconds;
            }
            corpse.gone = corpse.restSeconds >= 0.0f && corpseSinkPresentation(corpse.restSeconds).gone;
        }
        else
        {
            corpse.restSeconds += deltaSeconds;
        }
        // The satchel appears as the body starts to dissolve.
        const uint32_t tier = corpse.restSeconds >= CorpseRestSeconds && lootValue ? corpseSatchelTier(*lootValue) : 0;
        if (tier != corpse.tier)
        {
            m_models.destroy(corpse.handle);
            corpse.handle = tier > 0 ? m_models.create(m_satchelAssets[tier - 1]) : Engine::ModelInstanceHandle {};
            m_models.setStaticStandIn(corpse.handle, tier > 0 ? m_satchelAssets[tier - 1] : nullptr);
            corpse.tier = tier;
        }
        if (tier > 0)
        {
            const CorpseSinkPresentation presentation = corpseSinkPresentation(corpse.restSeconds);
            m_models.setCoverage(corpse.handle, presentation.satchelCoverage);
            m_models.setTransform(corpse.handle, Engine::gltfModelPlacement(
                {state.preciseX, state.preciseY, state.preciseZ - 2.0f}, corpse.yaw,
                UnitsPerMetre * presentation.satchelScale));
        }
    }
}

float WorldFxSystem::actorCorpseSinkDepth(size_t actorIndex) const
{
    const auto found = m_corpseSatchelStates.find(actorIndex);
    if (found == m_corpseSatchelStates.end() || found->second.restSeconds < 0.0f || found->second.gone)
    {
        return 0.0f;
    }
    return corpseSinkPresentation(found->second.restSeconds).depthFraction * found->second.sinkDepth;
}

const WorldFxSystem::CorpseSatchel *WorldFxSystem::goneCorpse(size_t actorIndex) const
{
    const auto found = m_corpseSatchelStates.find(actorIndex);
    return found != m_corpseSatchelStates.end() && found->second.gone ? &found->second : nullptr;
}

void WorldFxSystem::setActorModelVisibility(const std::function<bool(size_t actorIndex)> &visible)
{
    for (const auto &[actorIndex, model] : m_actorModels)
    {
        m_models.setVisible(model.handle, visible(actorIndex));
    }
    for (const auto &[actorIndex, corpse] : m_corpseSatchelStates)
    {
        if (m_models.contains(corpse.handle))
        {
            m_models.setVisible(corpse.handle, visible(actorIndex));
        }
    }
}

void WorldFxSystem::releaseInspectPortrait()
{
    if (m_inspectPortrait)
    {
        m_models.destroy(m_inspectPortrait->portrait.handle);
        m_inspectPortrait.reset();
    }
}

const WorldFxSystem::InspectPortrait *WorldFxSystem::syncInspectPortrait(const IGameplayWorldRuntime &world,
    size_t actorIndex, uint32_t animationTicks)
{
    GameplayRuntimeActorState state;
    const MonsterTable *pMonsters = world.monsterTable();
    const MonsterEntry *pMonster = pMonsters != nullptr && world.actorRuntimeState(actorIndex, state)
        ? pMonsters->findById(state.monsterId) : nullptr;
    const ActorModelBinding *pBinding = pMonster != nullptr ? actorModelBinding(pMonster->internalName) : nullptr;
    if (pBinding == nullptr)
    {
        releaseInspectPortrait();
        return nullptr;
    }
    if (m_inspectPortrait && (m_inspectPortrait->actorIndex != actorIndex
        || m_inspectPortrait->actorId != state.actorId || m_inspectPortrait->monsterId != state.monsterId))
    {
        releaseInspectPortrait();
    }
    const ActorModelBinding &binding = *pBinding;
    const Engine::ModelTransform transform = Engine::gltfModelPlacement({0.0f, 0.0f, 0.0f}, binding.yawOffset,
        binding.scale);
    const auto clipFor = [&](ActorAiAnimationState animation)
    {
        return binding.clips[size_t(animation)];
    };
    const auto durationFor = [&](ActorAiAnimationState animation)
    {
        return binding.asset->clips[clipFor(animation)].durationSeconds;
    };
    if (!m_inspectPortrait)
    {
        InspectPortraitState portrait;
        const Engine::ModelInstanceHandle handle = m_models.create(binding.asset, transform);
        m_models.setVisible(handle, false);
        m_models.setMaterialVariant(handle, binding.materialVariant);
        m_models.setAttachments(handle, binding.attachments);
        portrait.portrait.handle = handle;
        portrait.actorIndex = actorIndex;
        portrait.actorId = state.actorId;
        portrait.monsterId = state.monsterId;
        portrait.movingAtFirstInspect = std::hypot(state.velocityX, state.velocityY) > 4.0f;
        // Frame the poses the demonstration shows once, so the camera holds still while the clips play: the corners
        // of each skin joint's vertex box at each pose (a close outline of the body, unlike one box around a long
        // creature seen from an angle) and, outside the attack, of each carried item's box.
        std::vector<std::array<float, 3>> &points = portrait.portrait.framePoints;
        if (!binding.ambientEffect.empty())
        {
            const float radius = binding.ambientRadius * binding.scale / binding.fxReferenceScale;
            for (int corner = 0; corner < 8; ++corner)
            {
                points.push_back({(corner & 1) ? radius : -radius, (corner & 2) ? radius : -radius,
                    (corner & 4) ? radius : -radius});
            }
        }
        const auto addBox = [&](const Engine::ModelBounds &box, const Engine::ModelMatrix &m)
        {
            for (int corner = 0; box.valid && corner < 8; ++corner)
            {
                const float x = (corner & 1) != 0 ? box.max[0] : box.min[0];
                const float y = (corner & 2) != 0 ? box.max[1] : box.min[1];
                const float z = (corner & 4) != 0 ? box.max[2] : box.min[2];
                points.push_back({m[0] * x + m[4] * y + m[8] * z + m[12], m[1] * x + m[5] * y + m[9] * z + m[13],
                    m[2] * x + m[6] * y + m[10] * z + m[14]});
            }
        };
        const Engine::ModelAsset &asset = *binding.asset;
        const Engine::ModelDeformationBounds *pJointBounds = m_models.deformationBounds(handle);
        constexpr int SamplesPerClip = 6;
        for (const ActorAiAnimationState animation :
            {ActorAiAnimationState::Standing, ActorAiAnimationState::Bored, ActorAiAnimationState::AttackMelee})
        {
            if (animation == ActorAiAnimationState::AttackMelee)
            {
                portrait.portrait.restPointCount = points.size();
            }
            for (int sample = 0; sample <= SamplesPerClip; ++sample)
            {
                m_models.sample(handle, clipFor(animation), durationFor(animation) * sample / SamplesPerClip,
                    transform);
                const Engine::ModelPose *pPose = m_models.pose(handle, false);
                for (size_t nodeIndex = 0; pPose != nullptr && pJointBounds != nullptr
                    && nodeIndex < asset.nodes.size() && nodeIndex < pJointBounds->nodes.size(); ++nodeIndex)
                {
                    const Engine::ModelNode &node = asset.nodes[nodeIndex];
                    if (node.meshIndex < 0 || !Engine::modelMatrixVisible(pPose->globalMatrices[nodeIndex]))
                    {
                        continue;
                    }
                    const std::vector<Engine::ModelJointBounds> &joints = pJointBounds->nodes[nodeIndex];
                    for (size_t jointIndex = 0; jointIndex < joints.size(); ++jointIndex)
                    {
                        addBox(joints[jointIndex].base, node.skinIndex >= 0
                            ? Engine::multiplyModelMatrices(
                                pPose->globalMatrices[asset.skins[node.skinIndex].joints[jointIndex]],
                                asset.skins[node.skinIndex].inverseBindMatrices[jointIndex])
                            : pPose->globalMatrices[nodeIndex]);
                    }
                }
                // A swung weapon's sweep would shrink the whole portrait; it may reach past the edge instead.
                for (const Engine::ModelAttachment &attachment : binding.attachments)
                {
                    const Engine::ModelMatrix *pMatrix = m_models.nodeMatrix(handle, attachment.nodeIndex);
                    if (pMatrix != nullptr && animation != ActorAiAnimationState::AttackMelee)
                    {
                        addBox(attachment.asset->staticBounds, *pMatrix);
                    }
                }
            }
        }
        portrait.animation = ActorAiAnimationState::Bored;
        portrait.lengthSeconds = durationFor(portrait.animation);
        portrait.lastTicks = animationTicks;
        m_inspectPortrait = std::move(portrait);
        if (!binding.ambientEffect.empty())
        {
            m_inspectPortrait->portrait.effects.emplace(&m_namedEffectLibrary);
        }
    }

    InspectPortraitState &portrait = *m_inspectPortrait;
    portrait.requested = true;
    const auto nextRandom = [&]()
    {
        portrait.randomState = portrait.randomState * 1664525u + 1013904223u;
        return portrait.randomState >> 16;
    };
    // Ticks of 1/128 s, at most a quarter second per frame (as the sprite preview).
    const float deltaSeconds = float(std::min(animationTicks - portrait.lastTicks, 32u)) / 128.0f;
    portrait.lastTicks = animationTicks;
    portrait.timeSeconds += deltaSeconds;
    bool restart = false;
    if (portrait.timeSeconds > portrait.lengthSeconds)
    {
        portrait.timeSeconds = 0.0f;
        restart = true;
        if (portrait.animation != ActorAiAnimationState::Standing)
        {
            portrait.animation = ActorAiAnimationState::Standing;
            portrait.lengthSeconds = float(128u + nextRandom() % 128u) / 128.0f;
        }
        else
        {
            const bool fidget = (pMonster->inspectFidgetWhenMoving && portrait.movingAtFirstInspect)
                || nextRandom() % 100u >= uint32_t(std::max(0, pMonster->inspectAttackChance));
            portrait.animation = fidget ? ActorAiAnimationState::Bored : ActorAiAnimationState::AttackMelee;
            portrait.lengthSeconds = durationFor(portrait.animation);
        }
    }
    const float duration = durationFor(portrait.animation);
    const float time = portrait.animation == ActorAiAnimationState::Standing
        ? (duration > 0.0f ? std::fmod(portrait.timeSeconds, duration) : 0.0f)
        : std::min(portrait.timeSeconds, duration);
    m_models.sampleBlended(portrait.portrait.handle, clipFor(portrait.animation), time, transform, deltaSeconds,
        portrait.started ? 0.15f : 0.0f, {}, restart || !portrait.started);
    // The portrait shows a raised shield as it stands, without the world's hit ripples.
    const std::optional<Engine::ModelShieldShell> shieldShell = actorShieldShell(state.shield, 0.0f,
        float(state.bodyHeight > 0 ? state.bodyHeight : state.height), m_shieldDomeTimeSeconds, false);
    m_models.setShieldShell(portrait.portrait.handle, shieldShell ? &*shieldShell : nullptr);
    if (portrait.portrait.effects)
    {
        EffectSystem &effects = *portrait.portrait.effects;
        const EffectSpawnParams params = {.scale = binding.scale / binding.fxReferenceScale, .seed = state.actorId};
        syncAmbientEffect(effects, m_namedEffectLibrary, binding.ambientEffect, portrait.ambientEffect, params, true);
        effects.update(deltaSeconds);
    }
    portrait.started = true;
    return &portrait.portrait;
}

bool WorldFxSystem::hasActorModel(size_t actorIndex) const
{
    return m_actorModels.contains(actorIndex) || goneCorpse(actorIndex) != nullptr;
}

void WorldFxSystem::syncActorModelFx(const IGameplayWorldRuntime &world, float deltaSeconds, bool refreshSpatialFx)
{
    if (m_actorModels.empty())
    {
        return;
    }
    struct Candidate
    {
        ActorModelInstance *pModel;
        float distanceSquared;
    };
    std::array<Candidate, 8> candidates = {};
    size_t count = 0;
    for (auto &[index, model] : m_actorModels)
    {
        if (model.pBinding != nullptr && !model.pBinding->ambientEffect.empty())
        {
            const float dx = model.previousX - world.partyX();
            const float dy = model.previousY - world.partyY();
            const bool emitting = !model.dying && model.previousState != uint8_t(ActorAiAnimationState::Dead)
                && m_models.isVisible(model.handle) && dx * dx + dy * dy < 4096.0f * 4096.0f;
            const EffectSpawnParams params = {.position = model.transform.translation,
                .scale = model.fxScale, .seed = model.actorId};
            if (deltaSeconds > 0.0f || !emitting)
            {
                syncAmbientEffect(m_namedEffects, m_namedEffectLibrary, model.pBinding->ambientEffect,
                    model.ambientEffect, params, emitting);
            }
            else
            {
                m_namedEffects.setTransform(model.ambientEffect, params.position, params.rotation, params.scale);
            }
        }
        // A burning body's fire light: it swells as the burn takes hold and dies with the last flames.
        const std::optional<Engine::ModelBurn> burn = refreshSpatialFx ? actorBurn(model) : std::nullopt;
        const Engine::ModelBounds *pBounds = burn ? m_models.cullingBounds(model.handle) : nullptr;
        if (pBounds == nullptr || !pBounds->valid || model.pBinding->burn->lightRadius <= 0.0f)
        {
            continue;
        }
        const float end = 1.0f + burn->edgeWidth + burn->fireWidth;
        const float strength = std::clamp((burn->front + burn->charWidth) / (burn->charWidth + 0.15f), 0.0f, 1.0f)
            * std::clamp((end - burn->front) / 0.3f, 0.0f, 1.0f)
            * (0.88f + 0.12f * std::sin(model.burnSeconds * 23.0f));
        if (strength > 0.0f)
        {
            const ActorBurnDeath &death = *model.pBinding->burn;
            addLightEmitter((pBounds->min[0] + pBounds->max[0]) * 0.5f, (pBounds->min[1] + pBounds->max[1]) * 0.5f,
                (pBounds->min[2] + pBounds->max[2]) * 0.5f, death.lightRadius * model.fxScale * strength,
                death.lightColorAbgr, -1, RenderLightKind::GenericFx, model.actorId, false);
        }
    }
    const float yaw = world.gameplayCameraYawRadians();
    const float forwardX = std::cos(yaw), forwardY = std::sin(yaw);
    for (auto &[index, model] : m_actorModels)
    {
        model.fxCooldown = std::max(0.0f, model.fxCooldown - deltaSeconds);
        model.chargeOriginAge += deltaSeconds;
        const float dx = model.previousX - world.partyX();
        const float dy = model.previousY - world.partyY();
        const float distanceSquared = dx * dx + dy * dy;
        // ponytail: eight nearby attachments use a camera cone; reuse render visibility if hidden-room FX costs grow.
        const bool near = distanceSquared < 2048.0f * 2048.0f
            && dx * forwardX + dy * forwardY > 0.4f * std::sqrt(distanceSquared) - 160.0f;
        if (!near || model.dying || model.previousState == uint8_t(ActorAiAnimationState::Dead)
            || model.pBinding == nullptr
            || (model.pBinding->eyeColorAbgr == 0 && model.chargeRole == ActorCharge::None && !model.pendingRelease))
        {
            model.pendingRelease = false;
            model.hasChargeOrigin = false;
            continue;
        }
        size_t insert = 0;
        while (insert < count && candidates[insert].distanceSquared <= distanceSquared)
        {
            ++insert;
        }
        if (insert < candidates.size())
        {
            count = std::min(count + 1, candidates.size());
            for (size_t i = count - 1; i > insert; --i)
            {
                candidates[i] = candidates[i - 1];
            }
            candidates[insert] = {&model, distanceSquared};
        }
    }
    for (auto &[index, model] : m_actorModels)
    {
        // A charge's named effects last until its release, while the actor stays among the nearest.
        if (model.chargeRole == ActorCharge::None || model.previousImpact || std::none_of(candidates.begin(),
            candidates.begin() + count, [&](const Candidate &candidate) { return candidate.pModel == &model; }))
        {
            stopActorChargeFx(model, EffectStopMode::Drain);
        }
    }
    for (size_t i = 0; i < count; ++i)
    {
        ActorModelInstance &model = *candidates[i].pModel;
        const ActorModelBinding &binding = *model.pBinding;
        const bool charging = model.chargeRole != ActorCharge::None && !model.previousImpact
            && binding.actionEvents[size_t(model.chargeRole) - 1].glowCount > 0;
        if (charging)
        {
            if (!model.chargeResolved)
            {
                resolveActorCharge(model);
            }
            const ActorModelBinding::ActionEvent &event = binding.actionEvents[size_t(model.chargeRole) - 1];
            model.chargeOriginCount = 0;
            for (size_t socket = 0; socket < event.glowCount; ++socket)
            {
                if (const std::optional<std::array<float, 3>> point = actorSocketPoint(model, event.glow[socket]))
                {
                    model.chargeOrigins[model.chargeOriginCount++] = *point;
                }
            }
            if (model.chargeGlows && model.chargeOriginCount > 0)
            {
                model.hasChargeOrigin = true;
                model.chargeOriginAge = 0.0f;
            }
            for (size_t origin = 0; !model.chargeEffect.empty() && origin < model.chargeOriginCount; ++origin)
            {
                const std::array<float, 3> &point = model.chargeOrigins[origin];
                if (deltaSeconds > 0.0f && !m_namedEffects.contains(model.chargeEffects[origin]))
                {
                    EffectSpawnParams params;
                    params.position = point;
                    params.scale = model.fxScale;
                    params.seed = model.actorId;
                    model.chargeEffects[origin] = m_namedEffects.spawn(model.chargeEffect, params);
                }
                m_namedEffects.setTransform(model.chargeEffects[origin], point, {0, 0, 0, 1}, model.fxScale);
            }
        }
        // The charge goes out with the release (an attack applied at its contact frame keeps its clip until it ends).
        const float charge = charging && model.chargeGlows
            ? std::clamp((model.chargeProgress - 0.25f) / 0.5f, 0.0f, 1.0f) : 0.0f;
        const float chargeFxScale = 2.0f * model.fxScale
            * (model.chargeRole != ActorCharge::None ? binding.actionEvents[size_t(model.chargeRole) - 1].glowScale
                : 1.0f);
        if (refreshSpatialFx && model.hasChargeOrigin && charge > 0.0f)
        {
            const uint32_t coreColor = makeAbgr(
                ((model.chargeColor & 0xffu) + 255) / 2,
                (((model.chargeColor >> 8) & 0xffu) + 255) / 2,
                (((model.chargeColor >> 16) & 0xffu) + 255) / 2, 240);
            const float radius = (8.0f + 24.0f * charge) * chargeFxScale;
            for (size_t origin = 0; origin < model.chargeOriginCount; ++origin)
            {
                const std::array<float, 3> &point = model.chargeOrigins[origin];
                addGlowBillboard(point[0], point[1], point[2], radius,
                    (model.chargeColor & 0x00ffffffu) | 0xa0000000u);
                addGlowBillboard(point[0], point[1], point[2], radius * 0.5f, coreColor);
                if (origin == 0)
                {
                    addLightEmitter(point[0], point[1], point[2], 128.0f * charge * chargeFxScale, model.chargeColor,
                        -1, RenderLightKind::GenericFx, model.actorId, false);
                }
            }
        }
        if (deltaSeconds > 0.0f && model.pendingRelease && model.hasChargeOrigin)
        {
            for (size_t origin = 0; origin < model.chargeOriginCount; ++origin)
            {
                const std::array<float, 3> &point = model.chargeOrigins[origin];
                FxRecipes::spawnBuffSparkles(m_particleSystem, model.actorId, point[0], point[1], point[2], 8.0f,
                    model.chargeColor);
            }
            model.pendingRelease = false;
            model.hasChargeOrigin = false;
        }
        if (deltaSeconds <= 0.0f || model.fxCooldown > 0.0f)
        {
            continue;
        }
        model.fxCooldown = 0.10f;
        const auto spawnEmber = [&](const std::array<float, 3> &point, float size, uint32_t color,
            const std::array<float, 3> &velocity = {0, 0, 7}, float lifetimeSeconds = 0.18f)
        {
            FxParticleState ember;
            ember.x = point[0];
            ember.y = point[1];
            ember.z = point[2];
            ember.size = size;
            ember.endSize = size * 0.2f;
            ember.velocityX = velocity[0];
            ember.velocityY = velocity[1];
            ember.velocityZ = velocity[2];
            ember.motion = FxParticleMotion::Ascend;
            ember.lifetimeSeconds = lifetimeSeconds;
            ember.fadeOutStartSeconds = lifetimeSeconds - 0.13f;
            ember.startColorAbgr = color;
            ember.endColorAbgr = color & 0x00ffffffu;
            ember.blendMode = FxParticleBlendMode::Additive;
            ember.material = FxParticleMaterial::Ember;
            m_particleSystem.addParticle(ember);
        };
        if (model.hasChargeOrigin && charge > 0.0f)
        {
            for (size_t origin = 0; origin < model.chargeOriginCount; ++origin)
            {
                const std::array<float, 3> &point = model.chargeOrigins[origin];
                for (size_t spark = 0; spark < 3; ++spark)
                {
                    const float angle = model.chargeProgress * 12.0f + float(model.actorId)
                        + float(spark) * (2.0f * std::numbers::pi_v<float> / 3.0f);
                    const float x = std::cos(angle), y = std::sin(angle);
                    const float radius = (4.0f + 10.0f * charge) * chargeFxScale;
                    spawnEmber({point[0] + x * radius, point[1] + y * radius,
                        point[2] + std::sin(angle * 2.0f) * radius * 0.5f},
                        12.0f * chargeFxScale, (model.chargeColor & 0x00ffffffu) | 0xe0000000u,
                        {x * 32.0f * chargeFxScale, y * 32.0f * chargeFxScale, 45.0f * chargeFxScale}, 0.35f);
                }
            }
        }
        for (const std::optional<ActorModelBinding::Socket> &eye : binding.eyes)
        {
            const std::optional<std::array<float, 3>> point = eye ? actorSocketPoint(model, *eye) : std::nullopt;
            if (point && binding.eyeColorAbgr != 0)
            {
                spawnEmber(*point, 0.8f, binding.eyeColorAbgr);
            }
        }
    }
}

// A sunk or burnt-out corpse without loot has no satchel: its bounds are empty, so nothing is picked there.
namespace
{
const Engine::ModelBounds NoActorModelBounds = {};
}

std::optional<Engine::ModelInstanceHandle> WorldFxSystem::actorPickingHandle(size_t actorIndex) const
{
    if (const CorpseSatchel *pCorpse = goneCorpse(actorIndex))
    {
        return pCorpse->handle;
    }
    const auto iterator = m_actorModels.find(actorIndex);
    if (iterator == m_actorModels.end())
    {
        return std::nullopt;
    }
    // A burnt-out body leaves only its loot satchel or visible attachments (such as charred remains).
    const std::optional<Engine::ModelBurn> burn = actorBurn(iterator->second);
    if (burn && Engine::modelBurnConsumed(*burn))
    {
        const auto corpse = m_corpseSatchelStates.find(actorIndex);
        if (corpse != m_corpseSatchelStates.end())
        {
            return corpse->second.handle;
        }
    }
    return iterator->second.handle;
}

const Engine::ModelBounds *WorldFxSystem::actorModelBounds(size_t actorIndex) const
{
    const std::optional<Engine::ModelInstanceHandle> handle = actorPickingHandle(actorIndex);
    if (!handle)
    {
        return nullptr;
    }
    const Engine::ModelBounds *pBounds = m_models.pickingBounds(*handle);
    return pBounds != nullptr ? pBounds : &NoActorModelBounds;
}

std::optional<float> WorldFxSystem::actorModelPickRay(size_t actorIndex, const std::array<float, 3> &origin,
    const std::array<float, 3> &direction) const
{
    const std::optional<Engine::ModelInstanceHandle> handle = actorPickingHandle(actorIndex);
    return handle ? m_models.pickRay(*handle, origin, direction) : std::nullopt;
}

std::optional<float> WorldFxSystem::actorModelStandingTop(size_t actorIndex) const
{
    const auto iterator = m_actorModels.find(actorIndex);
    if (iterator == m_actorModels.end() || iterator->second.pBinding == nullptr || goneCorpse(actorIndex) != nullptr)
    {
        return std::nullopt;
    }
    const ActorModelBinding &binding = *iterator->second.pBinding;
    return binding.zOffset + binding.standingHeight * binding.fxReferenceScale * iterator->second.fxScale;
}

std::optional<std::array<float, 3>> WorldFxSystem::actorLaunchPoint(size_t actorIndex, bool spell, float x, float y,
    float z, float radius, float height) const
{
    const auto iterator = m_actorModels.find(actorIndex);
    if (iterator == m_actorModels.end() || iterator->second.pBinding == nullptr)
    {
        return std::nullopt;
    }
    // The release socket, else the one glow socket or the middle of several.
    const ActorModelBinding::ActionEvent &event = iterator->second.pBinding->actionEvents[spell ? 2 : 1];
    const std::span<const ActorModelBinding::Socket> sockets = event.release
        ? std::span<const ActorModelBinding::Socket>(&*event.release, 1)
        : std::span<const ActorModelBinding::Socket>(event.glow.data(), event.glowCount);
    if (sockets.empty())
    {
        return std::nullopt;
    }
    std::array<float, 3> point = {};
    for (const ActorModelBinding::Socket &socket : sockets)
    {
        const std::optional<std::array<float, 3>> socketPoint = actorSocketPoint(iterator->second, socket);
        if (!socketPoint)
        {
            return std::nullopt;
        }
        for (size_t axis = 0; axis < 3; ++axis)
        {
            point[axis] += (*socketPoint)[axis] / float(sockets.size());
        }
    }
    // A held staff head or bow sits within a few body radii of the actor, between its feet and above its head.
    if (!std::isfinite(point[0]) || !std::isfinite(point[1]) || !std::isfinite(point[2])
        || std::hypot(point[0] - x, point[1] - y) > std::max(128.0f, 3.0f * radius)
        || point[2] < z || point[2] > z + 1.5f * std::max(height, 32.0f))
    {
        return std::nullopt;
    }
    return point;
}

bool WorldFxSystem::actorModelClipSample(size_t actorIndex, std::string &clip, float &time, std::string &layerClip,
    float &layerTime) const
{
    const auto iterator = m_actorModels.find(actorIndex);
    const Engine::ModelAsset *pAsset = iterator != m_actorModels.end() ? m_models.asset(iterator->second.handle)
        : nullptr;
    const uint32_t clipIndex = pAsset != nullptr ? m_models.sampledClip(iterator->second.handle) : UINT32_MAX;
    if (clipIndex >= (pAsset != nullptr ? pAsset->clips.size() : 0))
    {
        return false;
    }
    clip = pAsset->clips[clipIndex].name;
    time = m_models.playbackTime(iterator->second.handle);
    const Engine::ModelAnimationLayer *pLayer = m_models.sampledLayer(iterator->second.handle);
    const bool layered = pLayer != nullptr && pLayer->weight > 0.0f && pLayer->clipIndex < pAsset->clips.size();
    layerClip = layered ? pAsset->clips[pLayer->clipIndex].name : std::string();
    layerTime = layered ? pLayer->timeSeconds : 0.0f;
    return true;
}

const Engine::ModelBounds *WorldFxSystem::actorModelCullingBounds(size_t actorIndex) const
{
    if (const CorpseSatchel *pCorpse = goneCorpse(actorIndex))
    {
        const Engine::ModelBounds *pBounds = m_models.motionBounds(pCorpse->handle);
        return pBounds != nullptr ? pBounds : &NoActorModelBounds;
    }
    const auto iterator = m_actorModels.find(actorIndex);
    if (iterator != m_actorModels.end())
    {
        const Engine::ModelBurn *pBurn = m_models.burn(iterator->second.handle);
        if (pBurn != nullptr && Engine::modelBurnConsumed(*pBurn))
        {
            return actorModelBounds(actorIndex);
        }
    }
    return iterator != m_actorModels.end() ? m_models.motionBounds(iterator->second.handle) : nullptr;
}

const Engine::ModelBounds *WorldFxSystem::actorModelPoseBounds(size_t actorIndex) const
{
    if (const CorpseSatchel *pCorpse = goneCorpse(actorIndex))
    {
        const Engine::ModelBounds *pBounds = m_models.cullingBounds(pCorpse->handle);
        return pBounds != nullptr ? pBounds : &NoActorModelBounds;
    }
    const auto iterator = m_actorModels.find(actorIndex);
    if (iterator != m_actorModels.end())
    {
        const Engine::ModelBurn *pBurn = m_models.burn(iterator->second.handle);
        if (pBurn != nullptr && Engine::modelBurnConsumed(*pBurn))
        {
            return actorModelBounds(actorIndex);
        }
    }
    return iterator != m_actorModels.end() ? m_models.cullingBounds(iterator->second.handle) : nullptr;
}

void WorldFxSystem::setActorModelOutline(size_t actorIndex, uint32_t colorAbgr)
{
    if (const CorpseSatchel *pCorpse = goneCorpse(actorIndex))
    {
        m_models.setOutlineColor(pCorpse->handle, colorAbgr);
        return;
    }
    const auto iterator = m_actorModels.find(actorIndex);
    if (iterator != m_actorModels.end())
    {
        m_models.setOutlineColor(iterator->second.handle, colorAbgr);
    }
}

size_t WorldFxSystem::NamedSoundKeyHash::operator()(const NamedSoundKey &key) const
{
    size_t value = static_cast<size_t>(key.owner.index);
    value ^= static_cast<size_t>(key.owner.generation) + 0x9e3779b9u + (value << 6) + (value >> 2);
    value ^= static_cast<size_t>(key.componentId) + 0x9e3779b9u + (value << 6) + (value >> 2);
    return value;
}

void WorldFxSystem::bindNamedEffectAudio(GameAudioSystem *pAudioSystem)
{
    if (m_pNamedEffectAudioSystem == pAudioSystem)
    {
        return;
    }
    for (const auto &[key, instanceId] : m_namedSoundInstances)
    {
        if (m_pNamedEffectAudioSystem != nullptr)
        {
            m_pNamedEffectAudioSystem->stopSoundInstance(instanceId);
        }
    }
    m_namedSoundInstances.clear();
    m_pNamedEffectAudioSystem = pAudioSystem;
}

bool WorldFxSystem::loadNamedEffectLibrary(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &libraryPath,
    const std::string &bindingManifestPath,
    std::string &error)
{
    EffectDefinitionLoader loader(&assetFileSystem);
    const std::optional<std::vector<std::shared_ptr<const EffectDefinition>>> definitions =
        loader.load(libraryPath, error);
    if (!definitions)
    {
        return false;
    }
    EffectLibrary library;
    EffectResourceLibrary resources;
    Engine::ModelAssetCache modelAssets;
    ProjectileEffectBindings projectileBindings;
    SpellAuraEffectBindings auraBindings;
    // The projectile and aura bindings sit beside the library they name (engine/effects/projectiles.yml and
    // spell_auras.yml).
    const size_t directoryEnd = libraryPath.find_last_of('/');
    const std::string bindingDirectory =
        directoryEnd == std::string::npos ? std::string() : libraryPath.substr(0, directoryEnd + 1);
    if (!library.replace(*definitions, error) ||
        !resources.load(assetFileSystem, bindingManifestPath, *definitions, error, &modelAssets) ||
        !loadProjectileEffectBindings(
            assetFileSystem, bindingDirectory + "projectiles.yml", library, projectileBindings, error) ||
        !loadSpellAuraEffectBindings(assetFileSystem, bindingDirectory + "spell_auras.yml", library, auraBindings,
            error))
    {
        return false;
    }
    for (const auto &[descriptor, binding] : m_actorModelBindings)
    {
        if (!binding.ambientEffect.empty() && library.find(binding.ambientEffect) == nullptr)
        {
            error = "actor ambient effect not found: " + descriptor + " " + binding.ambientEffect;
            return false;
        }
    }
    m_namedEffects.clear();
    m_projectileFlightEffects.clear();
    m_spellVisualFlights.clear();
    m_partyAuraEffects.clear();
    m_attachedImpactEffects.clear();
    m_spellAuraEffectBindings = std::move(auraBindings);
    m_namedEffectLibrary = std::move(library);
    m_namedEffectResources = std::move(resources);
    m_modelAssets = std::move(modelAssets);
    m_projectileEffectBindings = std::move(projectileBindings);
    return true;
}

const ProjectileEffectBinding *WorldFxSystem::projectileEffectBinding(
    FxRecipes::ProjectileRecipe recipe,
    int16_t monsterId,
    const std::string &objectName) const
{
    const MonsterTable::MonsterStatsEntry *pStats = monsterId != 0 && m_pProjectileMonsterTable != nullptr
        ? m_pProjectileMonsterTable->findStatsById(monsterId)
        : nullptr;
    return m_projectileEffectBindings.find(recipe, pStats != nullptr ? pStats->pictureName : std::string(),
        objectName);
}

bool WorldFxSystem::loadProjectileModels(const Engine::AssetFileSystem &assets, std::string &error)
{
    constexpr const char *BindingsPath = "engine/models/projectiles.yml";
    ProjectileModelBindings bindings;
    if (!loadProjectileModelBindings(assets, BindingsPath, bindings, error))
    {
        return false;
    }
    std::unordered_map<int16_t, LoadedProjectileModel> loaded;
    for (const auto &[objectId, binding] : bindings)
    {
        const Engine::ModelLoadResult result = m_modelAssets.load(assets, binding.model);
        if (!result)
        {
            error = std::string(BindingsPath) + ": object " + std::to_string(objectId) + ": " + result.error;
            return false;
        }
        const Engine::ModelBounds &bounds = result.asset->staticBounds;
        const float extent = bounds.valid ? bounds.max[2] - bounds.min[2] : 0.0f;
        if (extent <= 1.0e-4f)
        {
            error = std::string(BindingsPath) + ": object " + std::to_string(objectId) + ": " + binding.model +
                " has no extent along +Z";
            return false;
        }
        loaded[objectId] = {result.asset, binding.length / extent, binding.spinAxis,
            binding.spinDegreesPerSecond * std::numbers::pi_v<float> / 180.0f};
    }
    for (const auto &[key, model] : m_projectileModels)
    {
        m_models.destroy(model.handle);
    }
    m_projectileModels.clear();
    m_projectileModelBindings = std::move(loaded);
    return true;
}

const WorldFxSystem::LoadedProjectileModel *WorldFxSystem::projectileModelBinding(uint16_t objectDescriptionId) const
{
    if (m_projectileModelBindings.empty() || m_pProjectileObjectTable == nullptr)
    {
        return nullptr;
    }
    const ObjectEntry *pObject = m_pProjectileObjectTable->get(objectDescriptionId);
    if (pObject == nullptr)
    {
        return nullptr;
    }
    const auto found = m_projectileModelBindings.find(pObject->objectId);
    return found != m_projectileModelBindings.end() ? &found->second : nullptr;
}

void WorldFxSystem::syncProjectileModels(GameSession &session)
{
    if (m_projectileModelBindings.empty() && m_projectileModels.empty())
    {
        return;
    }
    for (auto &[key, model] : m_projectileModels)
    {
        model.seen = false;
    }
    // Flying projectiles, then the world's armed Fire Spike traps (their own id space, in the key's high half).
    std::vector<GameplayProjectilePresentationState> traps;
    if (const IGameplayWorldRuntime *pWorld = session.activeWorldRuntime())
    {
        pWorld->collectFireSpikeTrapPresentationStates(traps);
    }
    const std::vector<GameplayProjectilePresentationState> &flying =
        session.gameplayFxService().activeProjectilePresentationStates();
    for (size_t index = 0; index < flying.size() + traps.size(); ++index)
    {
        const bool trap = index >= flying.size();
        const GameplayProjectilePresentationState &projectile = trap ? traps[index - flying.size()] : flying[index];
        const LoadedProjectileModel *pBinding = projectileModelBinding(projectile.objectDescriptionId);
        if (pBinding == nullptr)
        {
            continue;
        }
        const uint64_t key = (uint64_t(trap ? 1 : 0) << 32) | projectile.projectileId;
        auto [found, inserted] = m_projectileModels.try_emplace(key);
        ProjectileModel &model = found->second;
        if (inserted)
        {
            model.handle = m_models.create(pBinding->asset);
            m_models.setStaticStandIn(model.handle, pBinding->asset);
        }
        model.seen = true;
        model.sectorId = projectile.sectorId;
        const float horizontalSpeed = std::hypot(projectile.velocityX, projectile.velocityY);
        if (!projectile.isSettled && horizontalSpeed + std::abs(projectile.velocityZ) > 1.0e-3f)
        {
            model.yaw = std::atan2(projectile.velocityY, projectile.velocityX) - 0.5f * std::numbers::pi_v<float>;
            model.pitch = std::atan2(projectile.velocityZ, horizontalSpeed);
        }
        // Yaw then pitch, so the model stays upright about its flight (its fins keep their roll), then its own spin;
        // the model's forward is OpenYAMM +Y, its up +Z and its side +X before turning. A settled projectile lies
        // level and still.
        const float halfYaw = 0.5f * model.yaw;
        const float halfPitch = projectile.isSettled ? 0.0f : 0.5f * model.pitch;
        const std::array<float, 4> yawPitch = {std::cos(halfYaw) * std::sin(halfPitch),
            std::sin(halfYaw) * std::sin(halfPitch), std::sin(halfYaw) * std::cos(halfPitch),
            std::cos(halfYaw) * std::cos(halfPitch)};
        std::array<float, 4> rotation = yawPitch;
        if (pBinding->spinAxis != ProjectileModelSpinAxis::None && !projectile.isSettled)
        {
            // Projectile ticks run at 128 a second; each projectile starts at its own angle.
            const float phase = float((projectile.projectileId * 2654435761u) >> 8) / float(1u << 24);
            const float halfAngle = 0.5f * (pBinding->spinRadiansPerSecond
                * float(projectile.timeSinceCreatedTicks) / 128.0f + phase * 2.0f * std::numbers::pi_v<float>);
            const float sine = std::sin(halfAngle);
            const std::array<float, 3> axis = pBinding->spinAxis == ProjectileModelSpinAxis::Forward
                ? std::array<float, 3>{0.0f, 1.0f, 0.0f}
                : pBinding->spinAxis == ProjectileModelSpinAxis::Up ? std::array<float, 3>{0.0f, 0.0f, 1.0f}
                : std::array<float, 3>{1.0f, 0.0f, 0.0f};
            const std::array<float, 4> spin = {axis[0] * sine, axis[1] * sine, axis[2] * sine, std::cos(halfAngle)};
            const std::array<float, 4> &a = yawPitch;
            rotation = {a[3] * spin[0] + a[0] * spin[3] + a[1] * spin[2] - a[2] * spin[1],
                a[3] * spin[1] - a[0] * spin[2] + a[1] * spin[3] + a[2] * spin[0],
                a[3] * spin[2] + a[0] * spin[1] - a[1] * spin[0] + a[2] * spin[3],
                a[3] * spin[3] - a[0] * spin[0] - a[1] * spin[1] - a[2] * spin[2]};
        }
        const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
            projectile.spellId, projectile.objectName, projectile.objectSpriteName, projectile.objectFlags);
        // Where the flight effects sit, so the model and its trail line up.
        const float anchorOffsetZ =
            FxRecipes::projectileRecipeAnchorOffset(recipe, projectile.radius, projectile.height);
        m_models.setTransform(model.handle, Engine::gltfModelPlacement(
            {projectile.x, projectile.y, projectile.z + anchorOffsetZ}, rotation, pBinding->scale));
    }
    for (auto iterator = m_projectileModels.begin(); iterator != m_projectileModels.end();)
    {
        if (iterator->second.seen)
        {
            ++iterator;
            continue;
        }
        m_models.destroy(iterator->second.handle);
        iterator = m_projectileModels.erase(iterator);
    }
}

void WorldFxSystem::setObjectModelVisibility(const std::function<bool(int16_t sectorId)> &visible)
{
    for (const auto &[key, model] : m_projectileModels)
    {
        m_models.setVisible(model.handle, visible(model.sectorId));
    }
    for (const auto &[key, model] : m_itemModels)
    {
        m_models.setVisible(model.handle, visible(model.sectorId));
    }
}

bool WorldFxSystem::loadItemModels(const Engine::AssetFileSystem &assets, std::string &error)
{
    for (const auto &[key, model] : m_itemModels)
    {
        m_models.destroy(model.handle);
        m_namedEffects.stop(model.sparkle, EffectStopMode::Immediate);
    }
    m_itemModels.clear();
    m_loadedItemModels.clear();
    m_reportedMissingItemIcons.clear();
    m_pItemModelAssets = &assets;
    const ItemModelBinding &placeholder = missingItemModelBinding();
    const Engine::ModelLoadResult result = m_modelAssets.load(assets, placeholder.model);
    const Engine::ModelBounds *pBounds = result ? &result.asset->staticBounds : nullptr;
    const float extent = pBounds != nullptr && pBounds->valid
        ? std::max(pBounds->max[0] - pBounds->min[0], pBounds->max[2] - pBounds->min[2]) : 0.0f;
    if (!result || extent <= 1.0e-4f)
    {
        error = "Missing-item placeholder " + placeholder.model + " failed to load: "
            + (result ? std::string("no horizontal extent") : result.error);
        m_missingItemModel = {};
        return false;
    }
    m_missingItemModel = {result.asset, placeholder.length / extent};
    error.clear();
    return true;
}

const WorldFxSystem::LoadedItemModel &WorldFxSystem::loadedItemModel(
    const GameplayWorldItemPresentationState &item, bool &placeholder)
{
    placeholder = true;
    const uint32_t itemId = item.itemId;
    const ItemDefinition *pItem = m_pItemTable != nullptr ? m_pItemTable->get(itemId) : nullptr;
    if (m_pItemTable == nullptr || m_pItemModelAssets == nullptr)
    {
        return m_missingItemModel;
    }
    const std::string icon = item.lootBag ? std::string("loot bag")
        : pItem != nullptr ? toLowerCopy(pItem->iconName) : std::string();
    if (!item.lootBag && !m_pItemTable->hasGroundModel(itemId))
    {
        if (m_reportedMissingItemIcons.insert(icon).second)
        {
            std::cerr << "Ground item " << itemId << " \"" << (pItem != nullptr ? pItem->name : std::string())
                      << "\" (icon " << (icon.empty() ? std::string("none") : icon)
                      << ") has no 3D model; drawing the placeholder\n";
        }
        return m_missingItemModel;
    }
    const ItemModelBinding &binding = item.lootBag ? lootBagModelBinding() : m_pItemTable->groundModel(itemId);
    auto [found, inserted] = m_loadedItemModels.try_emplace(binding.model);
    if (inserted)
    {
        const Engine::ModelLoadResult result = m_modelAssets.load(*m_pItemModelAssets, binding.model);
        const Engine::ModelBounds *pBounds = result ? &result.asset->staticBounds : nullptr;
        // The longest horizontal side (glTF X and Z) takes the binding's length.
        const float extent = pBounds != nullptr && pBounds->valid
            ? std::max(pBounds->max[0] - pBounds->min[0], pBounds->max[2] - pBounds->min[2]) : 0.0f;
        if (!result || extent <= 1.0e-4f)
        {
            std::cerr << "Ground item model " << binding.model << " (icon " << icon << ") failed to load: "
                      << (result ? std::string("no horizontal extent") : result.error)
                      << "; drawing the placeholder\n";
        }
        else
        {
            found->second = {result.asset, binding.length / extent};
        }
    }
    if (found->second.asset == nullptr)
    {
        return m_missingItemModel;
    }
    placeholder = false;
    return found->second;
}

void WorldFxSystem::syncItemModels(GameSession &session, float deltaSeconds)
{
    // The placeholder turns once every four seconds.
    constexpr float PlaceholderTurnRadiansPerSecond = std::numbers::pi_v<float> * 0.5f;
    // Raised a hair over the ground so the underside's rim does not flicker into it.
    constexpr float GroundLift = 0.5f;
    // Sparkles are a few pixels across beyond this, and cost nothing there.
    constexpr float SparkleRange = 3072.0f;
    constexpr float SparkleJumpsPerSecond = 12.0f;
    // Items smaller on screen than this are not drawn: a field of them to the horizon cost a full model each.
    constexpr float MinimumPixels = 8.0f;
    // By WorldItemSparkle.
    static const std::array<std::string, WorldItemSparkleCount> SparkleEffects = {"",
        "openyamm:fx/item_sparkle/valuable", "openyamm:fx/item_sparkle/precious", "openyamm:fx/item_sparkle/artifact",
        "openyamm:fx/item_sparkle/quest", "openyamm:fx/item_sparkle/coins"};
    m_pItemTable = &session.data().itemTable();
    m_itemModelSeconds = std::fmod(m_itemModelSeconds + deltaSeconds, 3600.0f);
    for (auto &[key, model] : m_itemModels)
    {
        model.seen = false;
    }
    std::vector<GameplayWorldItemPresentationState> items;
    const IGameplayWorldRuntime *pWorld = session.activeWorldRuntime();
    if (pWorld != nullptr)
    {
        pWorld->collectWorldItemPresentationStates(items);
    }
    for (const GameplayWorldItemPresentationState &item : items)
    {
        bool placeholder = false;
        const LoadedItemModel &loaded = loadedItemModel(item, placeholder);
        if (loaded.asset == nullptr)
        {
            continue;
        }
        auto [found, inserted] = m_itemModels.try_emplace(item.key);
        ItemModel &model = found->second;
        if (!inserted && (model.itemId != item.itemId || model.placeholder != placeholder))
        {
            m_models.destroy(model.handle);
            m_namedEffects.stop(model.sparkle, EffectStopMode::Immediate);
            inserted = true;
        }
        if (inserted)
        {
            model = {};
            model.handle = m_models.create(loaded.asset);
            m_models.setStaticStandIn(model.handle, loaded.asset, MinimumPixels);
            model.itemId = item.itemId;
            model.placeholder = placeholder;
        }
        model.seen = true;
        model.sectorId = item.sectorId;

        const ItemModelBinding &binding = placeholder ? missingItemModelBinding()
            : item.lootBag ? lootBagModelBinding() : m_pItemTable->groundModel(item.itemId);
        float yaw = worldItemYawRadians(item.key);
        if (placeholder)
        {
            yaw += m_itemModelSeconds * PlaceholderTurnRadiansPerSecond;
        }
        std::array<float, 3> position = {item.x, item.y, item.z};
        std::array<float, 3> up = {0.0f, 0.0f, 1.0f};
        if (item.moving || item.floating)
        {
            // In flight: flat at its simulated height, fitted to nothing.
            model.restPosition.reset();
        }
        else
        {
            // At rest: fitted once to the drawn ground under its footprint (the placeholder only sits on it).
            const std::array<float, 3> simulated = {item.x, item.y, item.z};
            if (!model.restPosition || *model.restPosition != simulated)
            {
                std::array<std::optional<float>, WorldItemFootprintSampleCount> heights = {};
                if (m_itemGroundSampler)
                {
                    const WorldItemFootprint footprint =
                        placeholder ? WorldItemFootprint{} : worldItemFootprintOffsets(binding, yaw);
                    for (size_t index = 0; index < WorldItemFootprintSampleCount; ++index)
                    {
                        heights[index] =
                            m_itemGroundSampler(item.x + footprint[index][0], item.y + footprint[index][1], item.z);
                    }
                }
                model.restPose = fitWorldItemRestingPose(binding, placeholder ? 0.0f : yaw, heights, item.z);
                model.restPosition = simulated;
            }
            position[2] = model.restPose.z + GroundLift;
            up = model.restPose.normal;
        }

        // Shortest arc from up to the ground normal, then the yaw about the tilted up.
        const float halfYaw = yaw * 0.5f;
        const std::array<float, 4> yawRotation = {0.0f, 0.0f, std::sin(halfYaw), std::cos(halfYaw)};
        const float w = 1.0f + up[2];
        const float length = std::sqrt(up[1] * up[1] + up[0] * up[0] + w * w);
        const std::array<float, 4> tilt = {-up[1] / length, up[0] / length, 0.0f, w / length};
        const std::array<float, 4> rotation = {
            tilt[3] * yawRotation[0] + tilt[0] * yawRotation[3] + tilt[1] * yawRotation[2] - tilt[2] * yawRotation[1],
            tilt[3] * yawRotation[1] - tilt[0] * yawRotation[2] + tilt[1] * yawRotation[3] + tilt[2] * yawRotation[0],
            tilt[3] * yawRotation[2] + tilt[0] * yawRotation[1] - tilt[1] * yawRotation[0] + tilt[2] * yawRotation[3],
            tilt[3] * yawRotation[3] - tilt[0] * yawRotation[0] - tilt[1] * yawRotation[1] - tilt[2] * yawRotation[2]};
        m_models.setTransform(model.handle, Engine::gltfModelPlacement(position, rotation, loaded.scale));

        const float dx = item.x - pWorld->partyX();
        const float dy = item.y - pWorld->partyY();
        const bool sparkling = item.sparkle != WorldItemSparkle::None && m_models.isVisible(model.handle)
            && dx * dx + dy * dy < SparkleRange * SparkleRange;
        if (sparkling || model.sparkle != EffectHandle {})
        {
            // The emitter jumps between random points over the item's top, SparkleJumpsPerSecond times a second; its
            // glints stay where they were shed, so a long blade or a breastplate glitters all over.
            const uint32_t jump = uint32_t(m_itemModelSeconds * SparkleJumpsPerSecond);
            uint32_t hash = (item.key * 2654435761u) ^ (jump * 0x9e3779b9u);
            hash ^= hash >> 15;
            hash *= 0x2c1b3c6du;
            hash ^= hash >> 12;
            const float u = 0.15f + 0.7f * float(hash & 0xffffu) / 65535.0f;
            const float v = 0.15f + 0.7f * float(hash >> 16) / 65535.0f;
            const float localX = binding.boundsMin[0] + u * (binding.boundsMax[0] - binding.boundsMin[0]);
            const float localY = binding.boundsMin[1] + v * (binding.boundsMax[1] - binding.boundsMin[1]);
            const float offsetX = localX * std::cos(yaw) - localY * std::sin(yaw);
            const float offsetY = localX * std::sin(yaw) + localY * std::cos(yaw);
            // On the tilted resting plane, most of the way up the item.
            const float top = 0.7f * binding.boundsMax[2];
            const std::string &effect = SparkleEffects[size_t(item.sparkle)];
            const EffectSpawnParams params = {.position = {position[0] + offsetX + up[0] * top,
                position[1] + offsetY + up[1] * top,
                position[2] - (up[0] * offsetX + up[1] * offsetY) / up[2] + up[2] * top}, .seed = item.key};
            if (deltaSeconds > 0.0f || !sparkling)
            {
                syncAmbientEffect(m_namedEffects, m_namedEffectLibrary, effect, model.sparkle, params, sparkling);
            }
            else
            {
                m_namedEffects.setTransform(model.sparkle, params.position, params.rotation, params.scale);
            }
        }
    }
    for (auto iterator = m_itemModels.begin(); iterator != m_itemModels.end();)
    {
        if (iterator->second.seen)
        {
            ++iterator;
            continue;
        }
        m_models.destroy(iterator->second.handle);
        m_namedEffects.stop(iterator->second.sparkle, EffectStopMode::Drain);
        iterator = m_itemModels.erase(iterator);
    }
}

void WorldFxSystem::setItemModelOutline(uint32_t key, uint32_t colorAbgr)
{
    const auto found = m_itemModels.find(key);
    if (found != m_itemModels.end())
    {
        m_models.setOutlineColor(found->second.handle, colorAbgr);
    }
}

bool WorldFxSystem::projectileShowsNativeSprite(const GameplayProjectilePresentationState &projectile) const
{
    if (projectileModelBinding(projectile.objectDescriptionId) != nullptr)
    {
        return false;
    }
    const bool classic = projectile.visualMode != GameplayProjectileVisualMode::FxOnly;
    const ProjectileEffectBinding *pBinding = projectileEffectBinding(
        FxRecipes::classifyProjectileRecipe(
            projectile.spellId,
            projectile.objectName,
            projectile.objectSpriteName,
            projectile.objectFlags),
        projectile.sourceMonsterId,
        projectile.objectName);
    return pBinding != nullptr && pBinding->nativeSprite ? *pBinding->nativeSprite : classic;
}

bool WorldFxSystem::isWaterSplashImpact(const GameplayProjectileImpactPresentationState &impact) const
{
    const ObjectEntry *pObject =
        m_pProjectileObjectTable != nullptr ? m_pProjectileObjectTable->get(impact.objectDescriptionId) : nullptr;
    return pObject != nullptr && pObject->objectId == GameplayProjectileService::waterSplashObjectId();
}

bool WorldFxSystem::projectileImpactUsesNamedEffect(const GameplayProjectileImpactPresentationState &impact) const
{
    if (isWaterSplashImpact(impact))
    {
        return !m_projectileEffectBindings.waterSplash().empty();
    }
    const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
        impact.sourceSpellId,
        impact.sourceObjectName,
        impact.sourceObjectSpriteName,
        impact.sourceObjectFlags);
    if (hasProjectileImpactEffectRebind(recipe))
    {
        return true;
    }
    const ProjectileEffectBinding *pBinding =
        projectileEffectBinding(recipe, impact.sourceMonsterId, impact.sourceObjectName);
    return pBinding != nullptr && !pBinding->impact.empty();
}

bool WorldFxSystem::projectileImpactShowsNativeSprite(const GameplayProjectileImpactPresentationState &impact) const
{
    if (projectileImpactUsesNamedEffect(impact))
    {
        return false;
    }
    const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
        impact.sourceSpellId,
        impact.sourceObjectName,
        impact.sourceObjectSpriteName,
        impact.sourceObjectFlags);
    return !FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe)
        || FxRecipes::projectileRecipeShowsImpactBillboard(recipe);
}

std::vector<std::string> WorldFxSystem::projectileEffectSpriteResources() const
{
    std::vector<std::string> resources;
    std::vector<std::string> effectIds = m_projectileEffectBindings.effectIds();
    const std::vector<std::string> auraIds = m_spellAuraEffectBindings.effectIds();
    effectIds.insert(effectIds.end(), auraIds.begin(), auraIds.end());
    for (const auto &[descriptor, binding] : m_actorModelBindings)
    {
        if (!binding.ambientEffect.empty())
        {
            effectIds.push_back(binding.ambientEffect);
        }
    }
    for (const std::string &id : effectIds)
    {
        const EffectDefinition *pDefinition = m_namedEffectLibrary.find(id);
        if (pDefinition == nullptr)
        {
            continue;
        }
        for (const EffectSpriteDefinition &sprite : pDefinition->sprites)
        {
            resources.push_back(sprite.spriteResource);
        }
        for (const EffectSpriteEmitterDefinition &emitter : pDefinition->spriteEmitters)
        {
            resources.push_back(emitter.spriteResource);
        }
        for (const EffectRibbonDefinition &ribbon : pDefinition->ribbons)
        {
            resources.push_back(ribbon.spriteResource);
        }
    }
    std::sort(resources.begin(), resources.end());
    resources.erase(std::unique(resources.begin(), resources.end()), resources.end());
    return resources;
}

// Spawns, moves or switches the flight (or, once settled, the settled) effect of one projectile. Returns false when
// its binding names no effect for that state (the recipe's classic trail then draws as before).
bool WorldFxSystem::syncProjectileFlightEffect(
    uint32_t projectileId,
    const ProjectileEffectBinding *pBinding,
    bool settled,
    const std::array<float, 3> &projectilePosition,
    float anchorOffsetZ,
    const std::array<float, 3> &velocity)
{
    const std::string *pEffectId = pBinding == nullptr ? nullptr : settled ? &pBinding->settled : &pBinding->flight;
    const std::unordered_map<uint32_t, ProjectileFlightEffect>::iterator it =
        m_projectileFlightEffects.find(projectileId);
    if (it != m_projectileFlightEffects.end() && (pEffectId == nullptr || it->second.settled != settled))
    {
        m_namedEffects.stop(it->second.handle, EffectStopMode::Drain);
        m_projectileFlightEffects.erase(it);
    }
    if (pEffectId == nullptr || pEffectId->empty())
    {
        return false;
    }
    // Turn the effect's +X towards the direction of flight; a settled effect stays upright.
    const std::array<float, 4> rotation =
        settled ? std::array<float, 4>{0.0f, 0.0f, 0.0f, 1.0f} : flightRotation(velocity);
    const std::array<float, 3> position = {
        projectilePosition[0], projectilePosition[1], projectilePosition[2] + anchorOffsetZ};
    const std::unordered_map<uint32_t, ProjectileFlightEffect>::iterator current =
        m_projectileFlightEffects.find(projectileId);
    if (current != m_projectileFlightEffects.end() && m_namedEffects.contains(current->second.handle))
    {
        m_namedEffects.setTransform(current->second.handle, position, rotation, 1.0f);
        current->second.anchorOffsetZ = anchorOffsetZ;
        current->second.rotation = rotation;
        return true;
    }
    EffectSpawnParams params;
    params.position = position;
    params.rotation = rotation;
    params.seed = projectileId * 2654435761u + (settled ? 17u : 9u);
    m_projectileFlightEffects[projectileId] =
        {m_namedEffects.spawn(*pEffectId, params), settled, anchorOffsetZ, rotation};
    return true;
}

void WorldFxSystem::stopProjectileFlightEffects()
{
    for (const auto &[projectileId, effect] : m_projectileFlightEffects)
    {
        m_namedEffects.stop(effect.handle, EffectStopMode::Drain);
    }
    m_projectileFlightEffects.clear();
}

void WorldFxSystem::beginFrame()
{
    m_particleSystem.beginFrame();
}

void WorldFxSystem::updateParticles(float deltaSeconds, bool paused)
{
    m_waterRipples.advance(deltaSeconds, paused);
    beginFrame();
    m_namedEffects.update(deltaSeconds, paused);
    if (!paused)
    {
        m_models.update(deltaSeconds);
    }
    processNamedEffectAudio();

    if (paused)
    {
        return;
    }

    m_particleUpdateAccumulatorSeconds =
        std::min(MaxParticleUpdateAccumulationSeconds, m_particleUpdateAccumulatorSeconds + deltaSeconds);

    while (m_particleUpdateAccumulatorSeconds >= ParticleUpdateStepSeconds)
    {
        m_particleSystem.update(ParticleUpdateStepSeconds);
        m_particleUpdateAccumulatorSeconds -= ParticleUpdateStepSeconds;
    }
}

void WorldFxSystem::processNamedEffectAudio()
{
    const std::vector<EffectSoundEvent> events = m_namedEffects.consumeSoundEvents();
    for (const EffectSoundEvent &event : events)
    {
        const NamedSoundKey key = {.owner = event.owner, .componentId = event.componentId};
        if (event.kind == EffectSoundEventKind::Stop)
        {
            const auto iterator = m_namedSoundInstances.find(key);
            if (iterator != m_namedSoundInstances.end())
            {
                if (m_pNamedEffectAudioSystem != nullptr)
                {
                    m_pNamedEffectAudioSystem->stopSoundInstance(iterator->second);
                }
                m_namedSoundInstances.erase(iterator);
            }
            continue;
        }
        if (event.kind == EffectSoundEventKind::Move)
        {
            const auto iterator = m_namedSoundInstances.find(key);
            if (iterator != m_namedSoundInstances.end() && m_pNamedEffectAudioSystem != nullptr)
            {
                m_pNamedEffectAudioSystem->setSoundInstancePosition(
                    iterator->second,
                    {event.position[0], event.position[1], event.position[2]});
            }
            continue;
        }
        if (m_pNamedEffectAudioSystem == nullptr)
        {
            continue;
        }
        const std::optional<std::string> path = m_namedEffectResources.findAssetPath(event.soundResource);
        if (!path)
        {
            continue;
        }
        const std::optional<GameAudioSystem::WorldPosition> position = event.spatial
            ? std::optional<GameAudioSystem::WorldPosition>({
                event.position[0], event.position[1], event.position[2]})
            : std::nullopt;
        const uint64_t instanceId = m_pNamedEffectAudioSystem->playAssetInstance(
            *path,
            GameAudioSystem::PlaybackGroup::World,
            position,
            event.loop,
            event.volume,
            event.pitch,
            event.innerRadius,
            event.outerRadius);
        if (instanceId != 0)
        {
            m_namedSoundInstances[key] = instanceId;
        }
    }
}

EffectLibrary &WorldFxSystem::namedEffectLibrary()
{
    return m_namedEffectLibrary;
}

const EffectLibrary &WorldFxSystem::namedEffectLibrary() const
{
    return m_namedEffectLibrary;
}

EffectSystem &WorldFxSystem::namedEffects()
{
    return m_namedEffects;
}

const EffectSystem &WorldFxSystem::namedEffects() const
{
    return m_namedEffects;
}

const EffectResourceLibrary &WorldFxSystem::namedEffectResources() const
{
    return m_namedEffectResources;
}

bool WorldFxSystem::setProjectileImpactEffectRebind(
    FxRecipes::ProjectileRecipe recipe,
    const std::string &effectId)
{
    if (recipe == FxRecipes::ProjectileRecipe::None || m_namedEffectLibrary.find(effectId) == nullptr)
    {
        return false;
    }

    m_projectileImpactEffectRebinds[recipe] = effectId;
    return true;
}

bool WorldFxSystem::clearProjectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe)
{
    return m_projectileImpactEffectRebinds.erase(recipe) != 0;
}

bool WorldFxSystem::hasProjectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe) const
{
    return projectileImpactEffectRebind(recipe) != nullptr;
}

const std::string *WorldFxSystem::projectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe) const
{
    const std::unordered_map<FxRecipes::ProjectileRecipe, std::string>::const_iterator it =
        m_projectileImpactEffectRebinds.find(recipe);
    return it != m_projectileImpactEffectRebinds.end() ? &it->second : nullptr;
}

Engine::ModelAssetCache &WorldFxSystem::modelAssets()
{
    return m_modelAssets;
}

Engine::ModelInstanceSystem &WorldFxSystem::models()
{
    return m_models;
}

const Engine::ModelInstanceSystem &WorldFxSystem::models() const
{
    return m_models;
}

void WorldFxSystem::syncProjectileFx(GameSession &session, float deltaSeconds, bool refreshSpatialFx)
{
    m_pProjectileMonsterTable = &session.data().monsterTable();
    m_pMonsterProjectileTable = &session.data().monsterProjectileTable();
    m_pProjectileObjectTable = &session.data().objectTable();
    syncProjectileModels(session);
    syncItemModels(session, deltaSeconds);
    if (const IGameplayWorldRuntime *pWorld = session.activeWorldRuntime())
    {
        syncActorModelFx(*pWorld, deltaSeconds, refreshSpatialFx);
    }
    updateProjectileTrailCooldowns(deltaSeconds);
    updatePersistentImpactLights(deltaSeconds);
    syncProjectileTrails(session, refreshSpatialFx);
    syncProjectileImpacts(session);
    updateSpellVisualFlights(session, deltaSeconds);
    updatePartyAuraEffects(session);
    emitPersistentImpactLights(refreshSpatialFx);
    cleanupSeenProjectileImpactIds(session);
}

void WorldFxSystem::triggerPartySpellFx(const PartySpellCastResult &result)
{
    if (!result.succeeded() || !result.hasSourcePoint)
    {
        return;
    }

    // The enhanced style plays one bound aura in front of the party instead of the particles around it.
    const bool buffAura = shouldTriggerPartySpellBuffAura(result.effectKind);
    if (buffAura || shouldTriggerPartySpellSparkles(result.effectKind))
    {
        const std::string &effectId = m_spellAuraEffectBindings.find(
            buffAura ? SpellAuraKind::PartyBuff : SpellAuraKind::Heal,
            result.spellId);
        if (!effectId.empty())
        {
            PartyAuraEffect aura;
            aura.effectId = effectId;
            aura.seed = result.spellId * 2654435761u ^ static_cast<uint32_t>(m_partyAuraEffects.size() + 1);
            m_partyAuraEffects.push_back(std::move(aura));
            return;
        }
    }

    const uint32_t sparkleColorAbgr = partySpellFxColorAbgr(result);
    const size_t affectedCount = result.affectedCharacterIndices.size();
    const size_t sparkleCount = std::max<size_t>(1, affectedCount == 0 ? 1 : affectedCount);

    for (size_t sparkleIndex = 0; sparkleIndex < sparkleCount; ++sparkleIndex)
    {
        const float angleRadians =
            (6.28318530717958647692f * static_cast<float>(sparkleIndex)) / static_cast<float>(sparkleCount);
        const float offsetRadius = sparkleCount > 1 ? PartySpellFxRingRadius : 0.0f;
        const float sparkleX = result.sourceX + std::cos(angleRadians) * offsetRadius;
        const float sparkleY = result.sourceY + std::sin(angleRadians) * offsetRadius;
        const float sparkleZ =
            result.sourceZ + (sparkleCount > 1 ? static_cast<float>(sparkleIndex % 2) * 10.0f : 0.0f);
        const float sparkleRadius = result.effectKind == PartySpellCastEffectKind::PartyRestore ? 30.0f : 24.0f;
        const uint32_t sparkleSeed =
            (result.spellId * 2654435761u) ^ static_cast<uint32_t>(sparkleIndex * 2246822519u);

        if (shouldTriggerPartySpellBuffAura(result.effectKind))
        {
            FxRecipes::spawnActorBuffParticles(
                m_particleSystem,
                result.spellId,
                sparkleSeed,
                sparkleX,
                sparkleY,
                sparkleZ - 44.0f,
                148.0f,
                std::cos(angleRadians),
                std::sin(angleRadians));
        }
        else if (shouldTriggerPartySpellSparkles(result.effectKind))
        {
            FxRecipes::spawnBuffSparkles(
                m_particleSystem,
                sparkleSeed,
                sparkleX,
                sparkleY,
                sparkleZ,
                sparkleRadius,
                sparkleColorAbgr);
        }
    }
}

void WorldFxSystem::setShadowsEnabled(bool enabled)
{
    m_shadowsEnabled = enabled;

    if (!m_shadowsEnabled)
    {
        m_contactShadows.clear();
    }
}

void WorldFxSystem::spawnActorDebuffFx(
    uint32_t spellId,
    uint32_t seed,
    float x,
    float y,
    float z,
    float actorHeight,
    float frontDirectionX,
    float frontDirectionY,
    size_t actorIndex)
{
    if (spawnActorAuraEffect(SpellAuraKind::CreatureDebuff, spellId, seed, x, y, z, actorHeight, actorIndex))
    {
        return;
    }
    // Dispel Magic has only an enhanced aura; the classic style shows nothing.
    if (spellIdFromValue(spellId) == SpellId::DispelMagic)
    {
        return;
    }
    FxRecipes::spawnActorDebuffParticles(
        m_particleSystem,
        spellId,
        seed,
        x,
        y,
        z,
        actorHeight,
        frontDirectionX,
        frontDirectionY);
}

void WorldFxSystem::spawnPartyActorDebuffFx(
    uint32_t spellId,
    uint32_t seed,
    size_t actorIndex,
    float x,
    float y,
    float z,
    float actorHeight,
    float partyX,
    float partyY)
{
    const ProjectileEffectBinding *pBinding = projectileEffectBinding(
        FxRecipes::classifyProjectileRecipe(static_cast<int>(spellId), "", "", 0),
        0);
    if (pBinding == nullptr || pBinding->flight.empty())
    {
        spawnActorDebuffFx(spellId, seed, x, y, z, actorHeight, x - partyX, y - partyY, actorIndex);
        return;
    }

    SpellVisualFlight flight;
    flight.flightEffect = pBinding->flight;
    flight.target = {x, y, z + actorHeight * 0.5f};
    flight.fromParty = true;
    flight.targetActorIndex = actorIndex;
    flight.speed = SpellBoltSpeed;
    flight.minSeconds = SpellBoltMinSeconds;
    flight.maxSeconds = SpellBoltMaxSeconds;
    flight.impactEffect = pBinding->impact;
    flight.impactFollowsTarget = pBinding->impactFollowsTarget;
    flight.debuffSpellId = spellId;
    flight.seed = seed;
    m_spellVisualFlights.push_back(std::move(flight));
}

bool WorldFxSystem::spawnSpellImpactEffect(uint32_t spellId, float x, float y, float z, uint32_t seed)
{
    const ProjectileEffectBinding *pBinding = projectileEffectBinding(
        FxRecipes::classifyProjectileRecipe(static_cast<int>(spellId), "", "", 0),
        0);
    if (pBinding == nullptr || pBinding->impact.empty())
    {
        return false;
    }
    EffectSpawnParams params;
    params.position = {x, y, z};
    params.seed = seed;
    return m_namedEffects.contains(m_namedEffects.spawn(pBinding->impact, params));
}

void WorldFxSystem::spawnActorBuffFx(
    uint32_t spellId,
    uint32_t seed,
    float x,
    float y,
    float z,
    float actorHeight,
    float frontDirectionX,
    float frontDirectionY,
    size_t actorIndex)
{
    if (spawnActorAuraEffect(SpellAuraKind::CreatureBuff, spellId, seed, x, y, z, actorHeight, actorIndex))
    {
        return;
    }
    FxRecipes::spawnActorBuffParticles(
        m_particleSystem,
        spellId,
        seed,
        x,
        y,
        z,
        actorHeight,
        frontDirectionX,
        frontDirectionY);
}

void WorldFxSystem::clearSpatialFx()
{
    m_glowBillboards.clear();
    m_lightEmitters.clear();
    m_contactShadows.clear();
    m_segmentProjectiles.clear();
}

void WorldFxSystem::addContactShadow(float x, float y, float z, float radius, uint32_t colorAbgr)
{
    if (!m_shadowsEnabled)
    {
        return;
    }

    WorldFxContactShadow shadow = {};
    shadow.x = x;
    shadow.y = y;
    shadow.z = z;
    shadow.radius = radius;
    shadow.colorAbgr = colorAbgr;
    m_contactShadows.push_back(shadow);
}

void WorldFxSystem::addSegmentProjectile(
    float startX,
    float startY,
    float startZ,
    float endX,
    float endY,
    float endZ,
    float width,
    uint32_t colorAbgr)
{
    if (width <= 0.0f)
    {
        return;
    }

    WorldFxSegmentProjectile segment = {};
    segment.startX = startX;
    segment.startY = startY;
    segment.startZ = startZ;
    segment.endX = endX;
    segment.endY = endY;
    segment.endZ = endZ;
    segment.width = width;
    segment.colorAbgr = colorAbgr;
    m_segmentProjectiles.push_back(segment);
}

void WorldFxSystem::addGlowBillboard(
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr,
    bool renderVisibleBillboard)
{
    if (!renderVisibleBillboard)
    {
        return;
    }

    WorldFxGlowBillboard billboard = {};
    billboard.x = x;
    billboard.y = y;
    billboard.z = z;
    billboard.radius = radius;
    billboard.colorAbgr = colorAbgr;
    billboard.renderVisibleBillboard = renderVisibleBillboard;
    m_glowBillboards.push_back(billboard);
}

void WorldFxSystem::addLightEmitter(
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr,
    int16_t sectorId,
    RenderLightKind kind,
    uint32_t stableId,
    bool important)
{
    WorldFxLightEmitter light = {};
    light.x = x;
    light.y = y;
    light.z = z;
    light.radius = radius;
    light.colorAbgr = colorAbgr;
    light.sectorId = sectorId;
    light.kind = kind;
    light.stableId = stableId;
    light.important = important;
    m_lightEmitters.push_back(light);
}

ParticleSystem &WorldFxSystem::particles()
{
    return m_particleSystem;
}

const ParticleSystem &WorldFxSystem::particles() const
{
    return m_particleSystem;
}

const std::vector<WorldFxGlowBillboard> &WorldFxSystem::glowBillboards() const
{
    return m_glowBillboards;
}

const std::vector<WorldFxContactShadow> &WorldFxSystem::contactShadows() const
{
    return m_contactShadows;
}

const std::vector<WorldFxSegmentProjectile> &WorldFxSystem::segmentProjectiles() const
{
    return m_segmentProjectiles;
}

void WorldFxSystem::updateProjectileTrailCooldowns(float deltaSeconds)
{
    for (std::unordered_map<uint32_t, ProjectileFxTrailState>::iterator it = m_projectileTrailStates.begin();
        it != m_projectileTrailStates.end();
        ++it)
    {
        it->second.cooldownSeconds = std::max(0.0f, it->second.cooldownSeconds - deltaSeconds);
    }
}

void WorldFxSystem::updatePersistentImpactLights(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    for (std::unordered_map<uint32_t, PersistentImpactLight>::iterator it = m_persistentImpactLights.begin();
        it != m_persistentImpactLights.end();)
    {
        it->second.elapsedSeconds += deltaSeconds;

        if (it->second.elapsedSeconds >= it->second.durationSeconds)
        {
            it = m_persistentImpactLights.erase(it);
        }
        else
        {
            ++it;
        }
    }
}

void WorldFxSystem::emitPersistentImpactLights(bool refreshSpatialFx)
{
    if (!refreshSpatialFx)
    {
        return;
    }

    for (const std::pair<const uint32_t, PersistentImpactLight> &entry : m_persistentImpactLights)
    {
        const PersistentImpactLight &light = entry.second;

        if (light.radius <= 0.0f || light.durationSeconds <= 0.0f)
        {
            continue;
        }

        const float fade = std::clamp(1.0f - light.elapsedSeconds / light.durationSeconds, 0.0f, 1.0f);

        if (fade <= 0.0f)
        {
            continue;
        }

        addLightEmitter(
            light.x,
            light.y,
            light.z,
            light.radius,
            withScaledAlpha(light.colorAbgr, fade * ImpactLightIntensityScale),
            light.sectorId,
            RenderLightKind::Impact,
            entry.first);
    }
}

void WorldFxSystem::syncProjectileTrails(GameSession &session, bool refreshSpatialFx)
{
    const ObjectTable &objectTable = session.data().objectTable();
    const std::vector<GameplayProjectilePresentationState> &projectiles =
        session.gameplayFxService().activeProjectilePresentationStates();
    std::unordered_set<uint32_t> activeProjectileIds;
    activeProjectileIds.reserve(projectiles.size());

    for (const GameplayProjectilePresentationState &projectile : projectiles)
    {
        activeProjectileIds.insert(projectile.projectileId);

        if (isSparksSpellProjectile(projectile))
        {
            constexpr FxRecipes::ProjectileRecipe recipe = FxRecipes::ProjectileRecipe::Sparks;
            const float projectileCenterZ =
                projectile.z + FxRecipes::projectileRecipeAnchorOffset(recipe, projectile.radius, projectile.height);
            const ProjectileEffectBinding *pBinding = projectileEffectBinding(recipe, projectile.sourceMonsterId);
            syncProjectileFlightEffect(
                projectile.projectileId,
                pBinding,
                projectile.isSettled,
                {projectile.x, projectile.y, projectile.z},
                projectileCenterZ - projectile.z,
                {projectile.velocityX, projectile.velocityY, projectile.velocityZ});
            if (refreshSpatialFx)
            {
                uint32_t colorAbgr = FxRecipes::projectileRecipeColorAbgr(recipe);
                float glowRadius = FxRecipes::projectileRecipeGlowRadius(recipe);
                if (pBinding != nullptr && pBinding->light)
                {
                    const std::array<uint8_t, 3> &rgb = pBinding->light->rgb;
                    colorAbgr = makeAbgr(rgb[0], rgb[1], rgb[2], 255);
                    glowRadius = pBinding->light->radius;
                }

                if (glowRadius > 0.0f)
                {
                    addLightEmitter(
                        projectile.x,
                        projectile.y,
                        projectileCenterZ,
                        glowRadius,
                        makeAbgr(
                            static_cast<uint8_t>(colorAbgr & 0xffu),
                            static_cast<uint8_t>((colorAbgr >> 8) & 0xffu),
                            static_cast<uint8_t>((colorAbgr >> 16) & 0xffu),
                            255),
                        projectile.sectorId,
                        RenderLightKind::Projectile,
                        projectile.projectileId);
                }
            }

            continue;
        }

        const ObjectEntry *pObjectEntry = objectTable.get(projectile.objectDescriptionId);

        if (pObjectEntry == nullptr || isCannonballProjectile(projectile))
        {
            continue;
        }

        const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
            projectile.spellId,
            projectile.objectName,
            projectile.objectSpriteName,
            pObjectEntry->flags);
        const float projectileCenterZ =
            projectile.z + FxRecipes::projectileRecipeAnchorOffset(
                recipe,
                projectile.radius,
                projectile.height);
        const ProjectileEffectBinding *pBinding =
            projectileEffectBinding(recipe, projectile.sourceMonsterId, projectile.objectName);
        const bool flightEffect = syncProjectileFlightEffect(
            projectile.projectileId,
            pBinding,
            projectile.isSettled,
            {projectile.x, projectile.y, projectile.z},
            projectileCenterZ - projectile.z,
            {projectile.velocityX, projectile.velocityY, projectile.velocityZ});

        if (!flightEffect && projectileRecipeEmitsTrailParticles(projectile.spellId, recipe))
        {
            const float velocityLength = std::sqrt(
                projectile.velocityX * projectile.velocityX
                + projectile.velocityY * projectile.velocityY
                + projectile.velocityZ * projectile.velocityZ);
            float directionX = 0.0f;
            float directionY = 0.0f;
            float directionZ = 1.0f;

            if (velocityLength > 0.001f)
            {
                directionX = projectile.velocityX / velocityLength;
                directionY = projectile.velocityY / velocityLength;
                directionZ = projectile.velocityZ / velocityLength;
            }

            const float backOffset = FxRecipes::projectileRecipeBackOffset(recipe, projectile.radius);
            const float anchoredX = projectile.x - directionX * backOffset;
            const float anchoredY = projectile.y - directionY * backOffset;
            FxRecipes::ProjectileSpawnContext trailContext = {};
            trailContext.projectileId = projectile.projectileId;
            trailContext.objectFlags = pObjectEntry->flags;
            trailContext.radius = projectile.radius;
            trailContext.height = projectile.height;
            trailContext.spellId = projectile.spellId;
            trailContext.objectName = projectile.objectName;
            trailContext.spriteName = projectile.objectSpriteName;
            trailContext.x = anchoredX;
            trailContext.y = anchoredY;
            trailContext.z = projectileCenterZ;
            trailContext.velocityX = projectile.velocityX;
            trailContext.velocityY = projectile.velocityY;
            trailContext.velocityZ = projectile.velocityZ;
            ProjectileFxTrailState &trailState = m_projectileTrailStates[projectile.projectileId];

            if (!projectile.isSettled && trailState.cooldownSeconds <= 0.0f)
            {
                trailState.cooldownSeconds = projectileTrailCooldownSeconds(recipe);
                const FxRecipes::ProjectileFxRecipe &fxRecipe = FxRecipes::projectileFxRecipe(recipe);

                if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::SegmentProjectile)
                {
                    if (trailState.hasPreviousPosition)
                    {
                        addSegmentProjectile(
                            trailState.previousX,
                            trailState.previousY,
                            trailState.previousZ,
                            anchoredX,
                            anchoredY,
                            projectileCenterZ,
                            20.0f * ProjectileFxVisualSizeScale,
                            fxRecipe.colorAbgr);
                    }

                    trailState.previousX = anchoredX;
                    trailState.previousY = anchoredY;
                    trailState.previousZ = projectileCenterZ;
                    trailState.hasPreviousPosition = true;
                }
                else if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::HangingTrail)
                {
                    FxRecipes::ProjectileSegmentSpawnContext segmentContext = {};
                    segmentContext.projectileId = projectile.projectileId;
                    segmentContext.hasPreviousPosition = trailState.hasPreviousPosition;
                    segmentContext.previousX = trailState.previousX;
                    segmentContext.previousY = trailState.previousY;
                    segmentContext.previousZ = trailState.previousZ;
                    segmentContext.currentX = anchoredX;
                    segmentContext.currentY = anchoredY;
                    segmentContext.currentZ = projectileCenterZ;
                    segmentContext.velocityX = projectile.velocityX;
                    segmentContext.velocityY = projectile.velocityY;
                    segmentContext.velocityZ = projectile.velocityZ;
                    FxRecipes::spawnHangingProjectileTrailParticles(m_particleSystem, segmentContext, recipe);
                    trailState.previousX = anchoredX;
                    trailState.previousY = anchoredY;
                    trailState.previousZ = projectileCenterZ;
                    trailState.hasPreviousPosition = true;
                }
                else if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::Stun)
                {
                    FxRecipes::ProjectileSegmentSpawnContext segmentContext = {};
                    segmentContext.projectileId = projectile.projectileId;
                    segmentContext.hasPreviousPosition = trailState.hasPreviousPosition;
                    segmentContext.previousX = trailState.previousX;
                    segmentContext.previousY = trailState.previousY;
                    segmentContext.previousZ = trailState.previousZ;
                    segmentContext.currentX = anchoredX;
                    segmentContext.currentY = anchoredY;
                    segmentContext.currentZ = projectileCenterZ;
                    segmentContext.velocityX = projectile.velocityX;
                    segmentContext.velocityY = projectile.velocityY;
                    segmentContext.velocityZ = projectile.velocityZ;
                    FxRecipes::spawnStunTrailParticles(m_particleSystem, segmentContext, recipe);
                    trailState.previousX = anchoredX;
                    trailState.previousY = anchoredY;
                    trailState.previousZ = projectileCenterZ;
                    trailState.hasPreviousPosition = true;
                }
                else
                {
                    FxRecipes::spawnProjectileTrailParticles(m_particleSystem, trailContext, recipe);
                }
            }
        }

        float glowRadius = FxRecipes::projectileRecipeGlowRadius(recipe);
        uint32_t lightColor = FxRecipes::projectileRecipeLightColorAbgr(recipe);
        if (pBinding != nullptr && pBinding->light)
        {
            glowRadius = pBinding->light->radius;
            lightColor = makeAbgr(pBinding->light->rgb[0], pBinding->light->rgb[1], pBinding->light->rgb[2], 255);
        }

        if (refreshSpatialFx && glowRadius > 0.0f)
        {
            addLightEmitter(
                projectile.x,
                projectile.y,
                projectileCenterZ,
                glowRadius,
                makeAbgr(
                    static_cast<uint8_t>(lightColor & 0xffu),
                    static_cast<uint8_t>((lightColor >> 8) & 0xffu),
                    static_cast<uint8_t>((lightColor >> 16) & 0xffu),
                    255),
                projectile.sectorId,
                RenderLightKind::Projectile,
                projectile.projectileId);
        }
    }

    for (std::unordered_map<uint32_t, ProjectileFxTrailState>::iterator it = m_projectileTrailStates.begin();
        it != m_projectileTrailStates.end();)
    {
        if (activeProjectileIds.find(it->first) == activeProjectileIds.end())
        {
            it = m_projectileTrailStates.erase(it);
        }
        else
        {
            ++it;
        }
    }

    // A finished projectile's flight effect drains: its head goes at once, its ribbon and sheds fade out. A fast
    // projectile may have flown far since its last frame, so the effect first moves to where it ended (the hit point),
    // letting the trail reach the target.
    const std::vector<GameplayProjectileEndPresentationState> &endedProjectiles =
        session.gameplayFxService().endedProjectilePresentationStates();
    for (std::unordered_map<uint32_t, ProjectileFlightEffect>::iterator it = m_projectileFlightEffects.begin();
        it != m_projectileFlightEffects.end();)
    {
        if (activeProjectileIds.find(it->first) == activeProjectileIds.end())
        {
            const std::vector<GameplayProjectileEndPresentationState>::const_iterator ended = std::find_if(
                endedProjectiles.begin(),
                endedProjectiles.end(),
                [&](const GameplayProjectileEndPresentationState &end)
                {
                    return end.projectileId == it->first;
                });
            if (ended != endedProjectiles.end())
            {
                m_namedEffects.setTransform(
                    it->second.handle,
                    {ended->x, ended->y, ended->z + it->second.anchorOffsetZ},
                    it->second.rotation,
                    1.0f);
            }
            m_namedEffects.stop(it->second.handle, EffectStopMode::Drain);
            it = m_projectileFlightEffects.erase(it);
        }
        else
        {
            ++it;
        }
    }
}

void WorldFxSystem::syncProjectileImpacts(GameSession &session)
{
    updateAttachedImpactEffects(session);

    const std::vector<GameplayProjectileImpactPresentationState> &impacts =
        session.gameplayFxService().activeProjectileImpactPresentationStates();
    const IGameplayWorldRuntime *pWorld = session.activeWorldRuntime();

    for (const GameplayProjectileImpactPresentationState &impact : impacts)
    {
        const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
            impact.sourceSpellId,
            impact.sourceObjectName,
            impact.sourceObjectSpriteName,
            impact.sourceObjectFlags);

        // A debug rebind wins over a bound impact; a rebind also drops the impact light, a bound impact keeps it.
        const std::string *pEffectRebind = projectileImpactEffectRebind(recipe);
        const ProjectileEffectBinding *pBinding =
            pEffectRebind == nullptr
                ? projectileEffectBinding(recipe, impact.sourceMonsterId, impact.sourceObjectName) : nullptr;
        const std::string *pImpactEffect = pEffectRebind != nullptr ? pEffectRebind
            : pBinding != nullptr && !pBinding->impact.empty() ? &pBinding->impact : nullptr;
        if (pImpactEffect == nullptr && !m_projectileEffectBindings.waterSplash().empty()
            && isWaterSplashImpact(impact))
        {
            pImpactEffect = &m_projectileEffectBindings.waterSplash();
        }
        if (pImpactEffect == nullptr && !FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe))
        {
            continue;
        }

        const bool isNewImpact = m_seenImpactIds.insert(impact.effectId).second;

        // Where the impact effect plays: on the party, in front of its eyes (PartyHitReach). Its loose particles
        // spray from where it struck, mostly out of view.
        std::array<float, 3> shownPosition = {impact.x, impact.y, impact.z};
        float shownScale = 1.0f;
        if (pWorld != nullptr && impact.targetActorIndex == static_cast<size_t>(-1))
        {
            const float dx = impact.x - pWorld->partyX();
            const float dy = impact.y - pWorld->partyY();
            const float dz = impact.z - (pWorld->partyEyeZ() - PartyHitBodyDrop);
            if (dx * dx + dy * dy + dz * dz <= PartyHitReach * PartyHitReach)
            {
                shownPosition = partyHitShownPosition(*pWorld, impact, {dx, dy, dz}, shownScale);
            }
        }

        if (isNewImpact)
        {
            if (pImpactEffect != nullptr)
            {
                EffectSpawnParams params;
                params.position = shownPosition;
                params.scale = shownScale;
                std::optional<std::array<float, 3>> targetPosition;
                const bool followsTarget =
                    pEffectRebind != nullptr || (pBinding != nullptr && pBinding->impactFollowsTarget);
                if (followsTarget && impact.targetActorIndex != static_cast<size_t>(-1))
                {
                    targetPosition = actorCenterPosition(session, impact.targetActorIndex);
                    if (targetPosition)
                    {
                        params.position = *targetPosition;
                    }
                }
                params.seed = impact.effectId;
                const EffectHandle handle = m_namedEffects.spawn(*pImpactEffect, params);
                if (targetPosition && m_namedEffects.contains(handle))
                {
                    m_attachedImpactEffects.push_back({handle, impact.targetActorIndex, *targetPosition});
                }
            }

            // A drain's stolen life flies from the struck point back to the party that cast it.
            const size_t drainFlights = static_cast<size_t>(std::count_if(
                m_spellVisualFlights.begin(),
                m_spellVisualFlights.end(),
                [](const SpellVisualFlight &flight) { return flight.targetActorIndex == static_cast<size_t>(-1); }));
            if (pBinding != nullptr && !pBinding->returnFlight.empty() && impact.sourceMonsterId == 0
                && drainFlights < MaxDrainFlights)
            {
                SpellVisualFlight flight;
                flight.flightEffect = pBinding->returnFlight;
                flight.origin = {impact.x, impact.y, impact.z};
                flight.speed = DrainFlightSpeed;
                flight.minSeconds = DrainFlightMinSeconds;
                flight.maxSeconds = DrainFlightMaxSeconds;
                flight.bow = DrainFlightBow;
                flight.seed = impact.effectId * 2246822519u + 5u;
                m_spellVisualFlights.push_back(std::move(flight));
            }
            else
            {
                FxRecipes::ImpactSpawnContext impactContext = {};
                impactContext.recipe = recipe;
                impactContext.objectName = impact.objectName;
                impactContext.spriteName = impact.objectSpriteName;
                impactContext.x = impact.x;
                impactContext.y = impact.y;
                impactContext.z = impact.z;
                FxRecipes::spawnImpactParticles(m_particleSystem, impactContext);
            }
        }

        if (pEffectRebind != nullptr)
        {
            continue;
        }

        const std::optional<ProjectileEffectLight> boundLight =
            pBinding != nullptr ? pBinding->impactLight : std::optional<ProjectileEffectLight>();
        const float lightRadius = boundLight ? boundLight->radius : impactLightRadius(recipe);
        const float lightDuration = impactLightDurationSeconds(recipe, impact);

        if (isNewImpact && lightRadius > 0.0f && lightDuration > 0.0f)
        {
            PersistentImpactLight light = {};
            light.x = impact.x;
            light.y = impact.y;
            light.z = impact.z + 16.0f;
            light.radius = lightRadius;
            light.durationSeconds = lightDuration;
            light.colorAbgr = boundLight
                ? makeAbgr(boundLight->rgb[0], boundLight->rgb[1], boundLight->rgb[2], 255)
                : FxRecipes::projectileRecipeImpactColorAbgr(recipe);
            light.sectorId = impact.sectorId;
            m_persistentImpactLights[impact.effectId] = light;
        }
    }
}

void WorldFxSystem::updateAttachedImpactEffects(GameSession &session)
{
    m_attachedImpactEffects.erase(
        std::remove_if(
            m_attachedImpactEffects.begin(),
            m_attachedImpactEffects.end(),
            [&](AttachedImpactEffect &attached)
            {
                if (!m_namedEffects.contains(attached.handle))
                {
                    return true;
                }

                const std::optional<std::array<float, 3>> position =
                    actorCenterPosition(session, attached.actorIndex);
                if (!position)
                {
                    return true;
                }
                if (*position == attached.position)
                {
                    return false;
                }

                attached.position = *position;
                return !m_namedEffects.setTransform(
                    attached.handle,
                    attached.position,
                    {0.0f, 0.0f, 0.0f, 1.0f},
                    attached.scale);
            }),
        m_attachedImpactEffects.end());
}

void WorldFxSystem::updateSpellVisualFlights(GameSession &session, float deltaSeconds)
{
    const IGameplayWorldRuntime *pWorld = session.activeWorldRuntime();
    if (pWorld == nullptr)
    {
        stopSpellVisualFlights();
        return;
    }
    const std::array<float, 3> partyEyes = {pWorld->partyX(), pWorld->partyY(), pWorld->partyEyeZ() - PartyFlightDrop};
    constexpr size_t NoActor = static_cast<size_t>(-1);

    for (std::vector<SpellVisualFlight>::iterator it = m_spellVisualFlights.begin(); it != m_spellVisualFlights.end();)
    {
        SpellVisualFlight &flight = *it;
        if (flight.targetActorIndex != NoActor)
        {
            if (const std::optional<std::array<float, 3>> position =
                    actorCenterPosition(session, flight.targetActorIndex))
            {
                flight.target = *position;
            }
        }
        if (!flight.started)
        {
            if (flight.fromParty)
            {
                flight.origin = partyStandOffPoint(partyEyes, flight.target);
            }
            if (flight.targetActorIndex == NoActor)
            {
                flight.target = partyStandOffPoint(partyEyes, flight.origin);
            }
            const float distance = std::hypot(flight.target[0] - flight.origin[0],
                flight.target[1] - flight.origin[1], flight.target[2] - flight.origin[2]);
            flight.durationSeconds = std::clamp(distance / flight.speed, flight.minSeconds, flight.maxSeconds);
            EffectSpawnParams params;
            params.position = flight.origin;
            params.rotation = flightRotation({flight.target[0] - flight.origin[0],
                flight.target[1] - flight.origin[1], flight.target[2] - flight.origin[2]});
            params.seed = flight.seed;
            flight.handle = m_namedEffects.spawn(flight.flightEffect, params);
            flight.started = true;
        }
        else if (flight.targetActorIndex == NoActor)
        {
            flight.target = partyStandOffPoint(partyEyes, flight.origin);
        }
        if (!m_namedEffects.contains(flight.handle))
        {
            it = m_spellVisualFlights.erase(it);
            continue;
        }

        flight.progress = std::min(1.0f, flight.progress + deltaSeconds / flight.durationSeconds);
        const float bowPhase = std::numbers::pi_v<float> * flight.progress;
        std::array<float, 3> position;
        std::array<float, 3> direction;
        for (size_t axis = 0; axis < 3; ++axis)
        {
            position[axis] = flight.origin[axis] + (flight.target[axis] - flight.origin[axis]) * flight.progress;
            direction[axis] = flight.target[axis] - flight.origin[axis];
        }
        position[2] += flight.bow * std::sin(bowPhase);
        direction[2] += flight.bow * std::numbers::pi_v<float> * std::cos(bowPhase);
        m_namedEffects.setTransform(flight.handle, position, flightRotation(direction), 1.0f);
        if (flight.progress < 1.0f)
        {
            ++it;
            continue;
        }

        m_namedEffects.stop(flight.handle, EffectStopMode::Drain);
        if (!flight.impactEffect.empty())
        {
            EffectSpawnParams params;
            params.position = flight.target;
            params.seed = flight.seed ^ 0x9e3779b9u;
            const EffectHandle handle = m_namedEffects.spawn(flight.impactEffect, params);
            if (flight.impactFollowsTarget && flight.targetActorIndex != NoActor && m_namedEffects.contains(handle))
            {
                m_attachedImpactEffects.push_back({handle, flight.targetActorIndex, flight.target});
            }
        }
        // A bolt's own impact stands in for the debuff's aura.
        GameplayRuntimeActorState actorState = {};
        if (flight.impactEffect.empty() && flight.debuffSpellId != 0 && flight.targetActorIndex != NoActor
            && pWorld->actorRuntimeState(flight.targetActorIndex, actorState))
        {
            spawnActorDebuffFx(
                flight.debuffSpellId,
                flight.seed,
                actorState.preciseX,
                actorState.preciseY,
                actorState.preciseZ,
                static_cast<float>(actorState.height),
                actorState.preciseX - partyEyes[0],
                actorState.preciseY - partyEyes[1],
                flight.targetActorIndex);
        }
        it = m_spellVisualFlights.erase(it);
    }
}

bool WorldFxSystem::spawnActorAuraEffect(
    SpellAuraKind kind,
    uint32_t spellId,
    uint32_t seed,
    float x,
    float y,
    float z,
    float actorHeight,
    size_t actorIndex)
{
    const std::string &effectId = m_spellAuraEffectBindings.find(kind, spellId);
    if (effectId.empty())
    {
        return false;
    }
    EffectSpawnParams params;
    params.position = {x, y, z + actorHeight * 0.5f};
    params.scale = std::clamp(actorHeight / AuraReferenceActorHeight, AuraMinScale, AuraMaxScale);
    params.seed = seed;
    const EffectHandle handle = m_namedEffects.spawn(effectId, params);
    if (!m_namedEffects.contains(handle))
    {
        return false;
    }
    if (actorIndex != static_cast<size_t>(-1))
    {
        m_attachedImpactEffects.push_back({handle, actorIndex, params.position, params.scale});
    }
    return true;
}

void WorldFxSystem::updatePartyAuraEffects(GameSession &session)
{
    const IGameplayWorldRuntime *pWorld = session.activeWorldRuntime();
    if (pWorld == nullptr)
    {
        return;
    }
    const float yaw = pWorld->gameplayCameraYawRadians();
    const std::array<float, 3> position = {
        pWorld->partyX() + std::cos(yaw) * PartyAuraDistance,
        pWorld->partyY() + std::sin(yaw) * PartyAuraDistance,
        pWorld->partyEyeZ() - PartyAuraDrop};
    for (std::vector<PartyAuraEffect>::iterator it = m_partyAuraEffects.begin(); it != m_partyAuraEffects.end();)
    {
        if (!it->started)
        {
            EffectSpawnParams params;
            params.position = position;
            params.seed = it->seed;
            it->handle = m_namedEffects.spawn(it->effectId, params);
            it->started = true;
        }
        if (!m_namedEffects.setTransform(it->handle, position, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f))
        {
            it = m_partyAuraEffects.erase(it);
            continue;
        }
        ++it;
    }
}

void WorldFxSystem::stopSpellVisualFlights()
{
    for (const SpellVisualFlight &flight : m_spellVisualFlights)
    {
        if (flight.started)
        {
            m_namedEffects.stop(flight.handle, EffectStopMode::Drain);
        }
    }
    m_spellVisualFlights.clear();
}

void WorldFxSystem::cleanupSeenProjectileImpactIds(GameSession &session)
{
    std::unordered_set<uint32_t> activeImpactIds;
    const std::vector<GameplayProjectileImpactPresentationState> &impacts =
        session.gameplayFxService().activeProjectileImpactPresentationStates();
    activeImpactIds.reserve(impacts.size());

    for (const GameplayProjectileImpactPresentationState &impact : impacts)
    {
        activeImpactIds.insert(impact.effectId);
    }

    for (std::unordered_set<uint32_t>::iterator it = m_seenImpactIds.begin(); it != m_seenImpactIds.end();)
    {
        if (activeImpactIds.find(*it) == activeImpactIds.end())
        {
            it = m_seenImpactIds.erase(it);
        }
        else
        {
            ++it;
        }
    }
}
}
