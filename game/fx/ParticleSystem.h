#pragma once

#include "game/fx/FxSharedTypes.h"

#include <array>
#include <vector>

namespace OpenYAMM::Game
{
class ParticleSystem
{
public:
    struct DebugStats
    {
        size_t activeParticles = 0;
        size_t maxParticles = 0;
        size_t emittedThisFrame = 0;
        size_t rejectedThisFrame = 0;
        std::array<size_t, 5> activeByMaterial = {};
        std::array<size_t, 2> activeByBlendMode = {};
        std::array<size_t, 5> activeByTag = {};
    };

    ParticleSystem();

    void beginFrame();
    void reset();
    void update(float deltaSeconds);
    bool addParticle(const FxParticleState &particle);

    const std::vector<FxParticleState> &particles() const;
    size_t particleCount() const;
    size_t maxParticleCount() const;
    DebugStats debugStats() const;

private:
    static size_t materialIndex(FxParticleMaterial material);
    static size_t blendModeIndex(FxParticleBlendMode blendMode);
    static size_t tagIndex(FxParticleTag tag);

    size_t m_maxParticles = 4096;
    size_t m_emittedThisFrame = 0;
    size_t m_rejectedThisFrame = 0;
    std::vector<FxParticleState> m_particles;
};
}
