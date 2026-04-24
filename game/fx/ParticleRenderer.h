#pragma once

#include <cstdint>

namespace bx
{
struct Vec3;
}

namespace OpenYAMM::Game
{
class ParticleSystem;
class WorldFxRenderResources;

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
        float aspectRatio);
};
}
