#include "game/fx/WorldFxSystem.h"

#include "game/app/GameSession.h"
#include "game/data/GameDataRepository.h"
#include "game/fx/ParticleRecipes.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"
#include "game/tables/ObjectTable.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ParticleUpdateStepSeconds = 1.0f / 30.0f;
constexpr float MaxParticleUpdateAccumulationSeconds = 0.25f;
constexpr float ProjectileTrailCooldownSeconds = 0.018f;
constexpr float PartySpellFxRingRadius = 28.0f;
constexpr uint32_t CannonballPseudoSpellId = 136;

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

bool shouldTriggerPartySpellSparkles(PartySpellCastEffectKind effectKind)
{
    return effectKind == PartySpellCastEffectKind::PartyBuff
        || effectKind == PartySpellCastEffectKind::CharacterBuff
        || effectKind == PartySpellCastEffectKind::CharacterRestore
        || effectKind == PartySpellCastEffectKind::PartyRestore;
}
}

void WorldFxSystem::reset()
{
    m_particleUpdateAccumulatorSeconds = 0.0f;
    m_particleSystem.reset();
    m_glowBillboards.clear();
    m_lightEmitters.clear();
    m_contactShadows.clear();
    m_trailCooldownByProjectileId.clear();
    m_seenImpactIds.clear();
}

void WorldFxSystem::beginFrame()
{
    m_particleSystem.beginFrame();
}

void WorldFxSystem::updateParticles(float deltaSeconds, bool paused)
{
    beginFrame();

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

void WorldFxSystem::syncProjectileFx(GameSession &session, float deltaSeconds, bool refreshSpatialFx)
{
    updateProjectileTrailCooldowns(deltaSeconds);
    syncProjectileTrails(session, refreshSpatialFx);
    syncProjectileImpacts(session);
    cleanupSeenProjectileImpactIds(session);
}

void WorldFxSystem::triggerPartySpellFx(const PartySpellCastResult &result)
{
    if (!result.succeeded() || !result.hasSourcePoint || !shouldTriggerPartySpellSparkles(result.effectKind))
    {
        return;
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
    float frontDirectionY)
{
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

void WorldFxSystem::clearSpatialFx()
{
    m_glowBillboards.clear();
    m_lightEmitters.clear();
    m_contactShadows.clear();
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

void WorldFxSystem::addGlowBillboard(
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr,
    bool renderVisibleBillboard)
{
    WorldFxGlowBillboard billboard = {};
    billboard.x = x;
    billboard.y = y;
    billboard.z = z;
    billboard.radius = radius;
    billboard.colorAbgr = colorAbgr;
    billboard.renderVisibleBillboard = renderVisibleBillboard;
    m_glowBillboards.push_back(billboard);
}

void WorldFxSystem::addLightEmitter(float x, float y, float z, float radius, uint32_t colorAbgr)
{
    WorldFxLightEmitter light = {};
    light.x = x;
    light.y = y;
    light.z = z;
    light.radius = radius;
    light.colorAbgr = colorAbgr;
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

const std::vector<WorldFxLightEmitter> &WorldFxSystem::lightEmitters() const
{
    return m_lightEmitters;
}

const std::vector<WorldFxContactShadow> &WorldFxSystem::contactShadows() const
{
    return m_contactShadows;
}

void WorldFxSystem::updateProjectileTrailCooldowns(float deltaSeconds)
{
    for (std::unordered_map<uint32_t, float>::iterator it = m_trailCooldownByProjectileId.begin();
        it != m_trailCooldownByProjectileId.end();)
    {
        it->second = std::max(0.0f, it->second - deltaSeconds);

        if (it->second <= 0.0f)
        {
            it = m_trailCooldownByProjectileId.erase(it);
        }
        else
        {
            ++it;
        }
    }
}

void WorldFxSystem::syncProjectileTrails(GameSession &session, bool refreshSpatialFx)
{
    const ObjectTable &objectTable = session.data().objectTable();
    const std::vector<GameplayProjectilePresentationState> &projectiles =
        session.gameplayFxService().activeProjectilePresentationStates();

    for (const GameplayProjectilePresentationState &projectile : projectiles)
    {
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
        const uint32_t trailColor = FxRecipes::projectileRecipeColorAbgr(recipe);
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
        const float projectileCenterZ =
            projectile.z + FxRecipes::projectileRecipeAnchorOffset(
                recipe,
                projectile.radius,
                projectile.height);

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
        float &cooldown = m_trailCooldownByProjectileId[projectile.projectileId];

        if (cooldown <= 0.0f)
        {
            cooldown = ProjectileTrailCooldownSeconds;
            FxRecipes::spawnProjectileTrailParticles(m_particleSystem, trailContext, recipe);
        }

        const float glowRadius = FxRecipes::projectileRecipeGlowRadius(recipe);

        if (refreshSpatialFx && glowRadius > 0.0f)
        {
            addLightEmitter(
                projectile.x,
                projectile.y,
                projectileCenterZ,
                glowRadius,
                makeAbgr(
                    static_cast<uint8_t>(trailColor & 0xffu),
                    static_cast<uint8_t>((trailColor >> 8) & 0xffu),
                    static_cast<uint8_t>((trailColor >> 16) & 0xffu),
                    255));
            addGlowBillboard(projectile.x, projectile.y, projectile.z, glowRadius, trailColor, false);
        }
    }
}

void WorldFxSystem::syncProjectileImpacts(GameSession &session)
{
    const std::vector<GameplayProjectileImpactPresentationState> &impacts =
        session.gameplayFxService().activeProjectileImpactPresentationStates();

    for (const GameplayProjectileImpactPresentationState &impact : impacts)
    {
        if (!m_seenImpactIds.insert(impact.effectId).second)
        {
            continue;
        }

        const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
            impact.sourceSpellId,
            impact.sourceObjectName,
            impact.sourceObjectSpriteName,
            impact.sourceObjectFlags);

        if (!FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe))
        {
            continue;
        }

        FxRecipes::ImpactSpawnContext impactContext = {};
        impactContext.recipe = recipe;
        impactContext.objectName = impact.objectName;
        impactContext.spriteName = impact.objectSpriteName;
        impactContext.x = impact.x;
        impactContext.y = impact.y;
        impactContext.z = impact.z;
        FxRecipes::spawnImpactParticles(m_particleSystem, impactContext);

        const float impactLightRadius =
            recipe == FxRecipes::ProjectileRecipe::MeteorShower ? 128.0f
                : recipe == FxRecipes::ProjectileRecipe::Starburst
                ? 136.0f
                : recipe == FxRecipes::ProjectileRecipe::Implosion
                ? 152.0f
                : 96.0f;

        addLightEmitter(
            impact.x,
            impact.y,
            impact.z + 16.0f,
            impactLightRadius,
            FxRecipes::projectileRecipeColorAbgr(recipe));
    }
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
