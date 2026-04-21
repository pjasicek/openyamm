#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
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
        bool useActorHitChance = false;
        uint32_t timeSinceCreatedTicks = 0;
        uint32_t lifetimeTicks = 0;
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
        uint32_t lifetimeTicks = 0;
        bool freezeAnimation = false;
        bool isExpired = false;
    };

    struct Snapshot
    {
        uint32_t nextProjectileId = 1;
        uint32_t nextProjectileImpactId = 1;
        std::vector<ProjectileState> projectiles;
        std::vector<ProjectileImpactState> projectileImpacts;
    };

    void clear();
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);

    uint32_t nextProjectileId() const;
    uint32_t allocateProjectileId();
    uint32_t allocateProjectileImpactId();

    std::vector<ProjectileState> &projectiles();
    const std::vector<ProjectileState> &projectiles() const;
    std::vector<ProjectileImpactState> &projectileImpacts();
    const std::vector<ProjectileImpactState> &projectileImpacts() const;

    size_t projectileCount() const;
    const ProjectileState *projectileState(size_t projectileIndex) const;
    size_t projectileImpactCount() const;
    const ProjectileImpactState *projectileImpactState(size_t effectIndex) const;

    void collectProjectilePresentationState(
        std::vector<GameplayProjectilePresentationState> &projectiles,
        std::vector<GameplayProjectileImpactPresentationState> &impacts) const;

private:
    uint32_t m_nextProjectileId = 1;
    uint32_t m_nextProjectileImpactId = 1;
    std::vector<ProjectileState> m_projectiles;
    std::vector<ProjectileImpactState> m_projectileImpacts;
};
}
