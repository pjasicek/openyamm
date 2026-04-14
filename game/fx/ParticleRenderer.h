#pragma once

#include <cstdint>

namespace bx
{
struct Vec3;
}

namespace OpenYAMM::Game
{
class OutdoorGameView;

class ParticleRenderer
{
public:
    static void initializeResources(OutdoorGameView &view);
    static void renderParticles(
        OutdoorGameView &view,
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        float aspectRatio);
};
}
