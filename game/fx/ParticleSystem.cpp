#include "game/fx/ParticleSystem.h"

#include <algorithm>

namespace OpenYAMM::Game
{
ParticleSystem::ParticleSystem()
{
    m_particles.reserve(m_maxParticles);
}

void ParticleSystem::beginFrame()
{
    m_emittedThisFrame = 0;
    m_rejectedThisFrame = 0;
}

void ParticleSystem::reset()
{
    m_particles.clear();
    m_emittedThisFrame = 0;
    m_rejectedThisFrame = 0;
}

void ParticleSystem::update(float deltaSeconds)
{
    for (FxParticleState &particle : m_particles)
    {
        particle.ageSeconds += deltaSeconds;

        if (particle.motion == FxParticleMotion::Ascend)
        {
            particle.x += particle.velocityX * deltaSeconds;
            particle.y += particle.velocityY * deltaSeconds;
            particle.z += std::max(24.0f, particle.velocityZ) * deltaSeconds;
        }
        else if (particle.motion == FxParticleMotion::Burst)
        {
            particle.x += particle.velocityX * deltaSeconds;
            particle.y += particle.velocityY * deltaSeconds;
            particle.z += particle.velocityZ * deltaSeconds;
            particle.velocityZ -= 180.0f * deltaSeconds;
            const float dragFactor = std::max(0.0f, 1.0f - particle.drag * deltaSeconds);
            particle.velocityX *= dragFactor;
            particle.velocityY *= dragFactor;
        }
        else if (particle.motion == FxParticleMotion::VelocityTrail)
        {
            particle.x += particle.velocityX * deltaSeconds;
            particle.y += particle.velocityY * deltaSeconds;
            particle.z += particle.velocityZ * deltaSeconds;
            const float dragFactor = std::max(0.0f, 1.0f - particle.drag * deltaSeconds);
            particle.velocityX *= dragFactor;
            particle.velocityY *= dragFactor;
            particle.velocityZ *= dragFactor;
        }
        else if (particle.motion == FxParticleMotion::BallisticTrail)
        {
            particle.x += particle.velocityX * deltaSeconds;
            particle.y += particle.velocityY * deltaSeconds;
            particle.z += particle.velocityZ * deltaSeconds;
            particle.velocityZ -= 900.0f * deltaSeconds;
            const float dragFactor = std::max(0.0f, 1.0f - particle.drag * deltaSeconds);
            particle.velocityX *= dragFactor;
            particle.velocityY *= dragFactor;
            particle.velocityZ *= dragFactor;
        }
        else if (particle.motion == FxParticleMotion::Drift)
        {
            particle.x += particle.velocityX * deltaSeconds;
            particle.y += particle.velocityY * deltaSeconds;
            particle.z += particle.velocityZ * deltaSeconds;
            const float dragFactor = std::max(0.0f, 1.0f - particle.drag * deltaSeconds);
            particle.velocityX *= dragFactor;
            particle.velocityY *= dragFactor;
            particle.velocityZ = std::max(8.0f, particle.velocityZ * dragFactor);
        }

        particle.rotationRadians += particle.angularVelocityRadians * deltaSeconds;
    }

    m_particles.erase(
        std::remove_if(
            m_particles.begin(),
            m_particles.end(),
            [](const FxParticleState &particle)
            {
                return particle.ageSeconds >= particle.lifetimeSeconds;
            }),
        m_particles.end());
}

bool ParticleSystem::addParticle(const FxParticleState &particle)
{
    if (m_particles.size() >= m_maxParticles)
    {
        ++m_rejectedThisFrame;
        return false;
    }

    m_particles.push_back(particle);
    ++m_emittedThisFrame;
    return true;
}

const std::vector<FxParticleState> &ParticleSystem::particles() const
{
    return m_particles;
}

size_t ParticleSystem::particleCount() const
{
    return m_particles.size();
}

size_t ParticleSystem::maxParticleCount() const
{
    return m_maxParticles;
}

ParticleSystem::DebugStats ParticleSystem::debugStats() const
{
    DebugStats stats = {};
    stats.activeParticles = m_particles.size();
    stats.maxParticles = m_maxParticles;
    stats.emittedThisFrame = m_emittedThisFrame;
    stats.rejectedThisFrame = m_rejectedThisFrame;

    for (const FxParticleState &particle : m_particles)
    {
        ++stats.activeByMaterial[materialIndex(particle.material)];
        ++stats.activeByBlendMode[blendModeIndex(particle.blendMode)];
        ++stats.activeByTag[tagIndex(particle.tag)];
    }

    return stats;
}

size_t ParticleSystem::materialIndex(FxParticleMaterial material)
{
    switch (material)
    {
    case FxParticleMaterial::SoftBlob:
        return 0;
    case FxParticleMaterial::HardBlob:
        return 1;
    case FxParticleMaterial::Smoke:
        return 2;
    case FxParticleMaterial::Mist:
        return 3;
    case FxParticleMaterial::Ember:
        return 4;
    case FxParticleMaterial::Spark:
        return 5;
    }

    return 0;
}

size_t ParticleSystem::blendModeIndex(FxParticleBlendMode blendMode)
{
    switch (blendMode)
    {
    case FxParticleBlendMode::Alpha:
        return 0;
    case FxParticleBlendMode::Additive:
        return 1;
    }

    return 0;
}

size_t ParticleSystem::tagIndex(FxParticleTag tag)
{
    switch (tag)
    {
    case FxParticleTag::Trail:
        return 0;
    case FxParticleTag::Impact:
        return 1;
    case FxParticleTag::DecorationEmitter:
        return 2;
    case FxParticleTag::Buff:
        return 3;
    case FxParticleTag::Misc:
        return 4;
    }

    return 0;
}
}
