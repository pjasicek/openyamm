#include "game/gameplay/GameplayProjectileService.h"

namespace OpenYAMM::Game
{
void GameplayProjectileService::clear()
{
    m_nextProjectileId = 1;
    m_nextProjectileImpactId = 1;
    m_projectiles.clear();
    m_projectileImpacts.clear();
}

GameplayProjectileService::Snapshot GameplayProjectileService::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.nextProjectileId = m_nextProjectileId;
    snapshot.nextProjectileImpactId = m_nextProjectileImpactId;
    snapshot.projectiles = m_projectiles;
    snapshot.projectileImpacts = m_projectileImpacts;
    return snapshot;
}

void GameplayProjectileService::restoreSnapshot(const Snapshot &snapshot)
{
    m_nextProjectileId = snapshot.nextProjectileId;
    m_nextProjectileImpactId = snapshot.nextProjectileImpactId;
    m_projectiles = snapshot.projectiles;
    m_projectileImpacts = snapshot.projectileImpacts;
}

uint32_t GameplayProjectileService::nextProjectileId() const
{
    return m_nextProjectileId;
}

uint32_t GameplayProjectileService::allocateProjectileId()
{
    return m_nextProjectileId++;
}

uint32_t GameplayProjectileService::allocateProjectileImpactId()
{
    return m_nextProjectileImpactId++;
}

std::vector<GameplayProjectileService::ProjectileState> &GameplayProjectileService::projectiles()
{
    return m_projectiles;
}

const std::vector<GameplayProjectileService::ProjectileState> &GameplayProjectileService::projectiles() const
{
    return m_projectiles;
}

std::vector<GameplayProjectileService::ProjectileImpactState> &GameplayProjectileService::projectileImpacts()
{
    return m_projectileImpacts;
}

const std::vector<GameplayProjectileService::ProjectileImpactState> &
GameplayProjectileService::projectileImpacts() const
{
    return m_projectileImpacts;
}

size_t GameplayProjectileService::projectileCount() const
{
    return m_projectiles.size();
}

const GameplayProjectileService::ProjectileState *
GameplayProjectileService::projectileState(size_t projectileIndex) const
{
    if (projectileIndex >= m_projectiles.size())
    {
        return nullptr;
    }

    return &m_projectiles[projectileIndex];
}

size_t GameplayProjectileService::projectileImpactCount() const
{
    return m_projectileImpacts.size();
}

const GameplayProjectileService::ProjectileImpactState *
GameplayProjectileService::projectileImpactState(size_t effectIndex) const
{
    if (effectIndex >= m_projectileImpacts.size())
    {
        return nullptr;
    }

    return &m_projectileImpacts[effectIndex];
}

void GameplayProjectileService::collectProjectilePresentationState(
    std::vector<GameplayProjectilePresentationState> &projectiles,
    std::vector<GameplayProjectileImpactPresentationState> &impacts) const
{
    projectiles.clear();
    impacts.clear();
    projectiles.reserve(m_projectiles.size());
    impacts.reserve(m_projectileImpacts.size());

    for (const ProjectileState &projectile : m_projectiles)
    {
        if (projectile.isExpired)
        {
            continue;
        }

        GameplayProjectilePresentationState state = {};
        state.projectileId = projectile.projectileId;
        state.objectDescriptionId = projectile.objectDescriptionId;
        state.objectSpriteId = projectile.objectSpriteId;
        state.objectSpriteFrameIndex = projectile.objectSpriteFrameIndex;
        state.objectFlags = projectile.objectFlags;
        state.radius = projectile.radius;
        state.height = projectile.height;
        state.spellId = projectile.spellId;
        state.objectName = projectile.objectName;
        state.objectSpriteName = projectile.objectSpriteName;
        state.x = projectile.x;
        state.y = projectile.y;
        state.z = projectile.z;
        state.velocityX = projectile.velocityX;
        state.velocityY = projectile.velocityY;
        state.velocityZ = projectile.velocityZ;
        state.timeSinceCreatedTicks = projectile.timeSinceCreatedTicks;
        projectiles.push_back(std::move(state));
    }

    for (const ProjectileImpactState &impact : m_projectileImpacts)
    {
        if (impact.isExpired)
        {
            continue;
        }

        GameplayProjectileImpactPresentationState state = {};
        state.effectId = impact.effectId;
        state.objectDescriptionId = impact.objectDescriptionId;
        state.objectSpriteId = impact.objectSpriteId;
        state.objectSpriteFrameIndex = impact.objectSpriteFrameIndex;
        state.sourceObjectFlags = impact.sourceObjectFlags;
        state.sourceSpellId = impact.sourceSpellId;
        state.objectName = impact.objectName;
        state.objectSpriteName = impact.objectSpriteName;
        state.sourceObjectName = impact.sourceObjectName;
        state.sourceObjectSpriteName = impact.sourceObjectSpriteName;
        state.x = impact.x;
        state.y = impact.y;
        state.z = impact.z;
        state.timeSinceCreatedTicks = impact.timeSinceCreatedTicks;
        state.freezeAnimation = impact.freezeAnimation;
        impacts.push_back(std::move(state));
    }
}
}
