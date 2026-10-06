#pragma once

#include <cstdint>
#include <span>

namespace bx
{
struct Vec3;
}

namespace OpenYAMM::Game
{
class ParticleSystem;
class WorldFxRenderResources;
struct WorldFxGlowBillboard;

class ParticleRenderer
{
public:
    static void initializeResources(WorldFxRenderResources &resources);
    static void shutdownResources(WorldFxRenderResources &resources);
    static void renderParticles(
        WorldFxRenderResources &resources,
        const ParticleSystem &particleSystem,
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        float aspectRatio,
        std::span<const WorldFxGlowBillboard> glows);
};
}
