#pragma once

#include "game/render/Mist.h"

#include <array>
#include <cstdint>

namespace OpenYAMM::Game
{
class ParticleSystem;

// A map's mist close to the eye (devdocs/MIST.md "Wisps"): the mist the shaders draw needs distance to show, so near
// the party it reads as clear air. A few large, faint, slowly drifting particles in the mist's colour stand in it
// where the mist is, around the eye; they stay where they appear and fade in and out over their lives.
class MistWisps
{
public:
    // Wisps kept alive around the eye, and the distance they appear within.
    static constexpr size_t TargetCount = 56;
    static constexpr float SpawnRadius = 650.0f;

    // Keeps the wisps' number up in the shared particle system. `elapsedSeconds` is the view's clock; `light` scales
    // the colours of the parts that follow the daylight, as packMistUniform takes it.
    void update(const MapMist &mist, const std::array<float, 3> &eye, float elapsedSeconds,
        const std::array<float, 3> &light, ParticleSystem &particles);

private:
    float random();
    bool spawn(const MapMist &mist, const std::array<float, 3> &eye, const std::array<float, 3> &light,
        float startAge, ParticleSystem &particles);

    uint32_t m_seed = 0x9e3779b9u;
    float m_lastElapsedSeconds = -1.0f;
    float m_spawnBudget = 0.0f;
};

// How thick the map's mist is at a point, 0..1 of each part's densest, and its colour there (display space, before
// the light): what a wisp at that point takes. Zero where there is no mist.
struct MistSample
{
    float density = 0.0f;
    std::array<float, 3> color = {};
    bool followsDaylight = true;
};
MistSample sampleMist(const MapMist &mist, const std::array<float, 3> &point);
}
