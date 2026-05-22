#pragma once

#include "game/fx/WorldFxSystem.h"

#include <bx/math.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorLightSelectionBounds
{
    bx::Vec3 min = {0.0f, 0.0f, 0.0f};
    bx::Vec3 max = {0.0f, 0.0f, 0.0f};
    bool valid = false;
};

struct OutdoorSelectedFxLights
{
    static constexpr size_t MaxLights = 8;

    std::array<float, MaxLights * 4> positions = {};
    std::array<float, MaxLights * 4> colors = {};
    std::array<float, 4> params = {};
    uint32_t lightCount = 0;
    uint32_t rankedCandidateCount = 0;
    uint32_t filteredEmitterCount = 0;
};

class OutdoorLightingRuntime
{
public:
    void reset();
    void build(const WorldFxSystem &worldFxSystem);
    void build(const std::vector<WorldFxLightEmitter> &lightEmitters);

    OutdoorSelectedFxLights selectForBounds(
        const bx::Vec3 &fallbackReferencePosition,
        const OutdoorLightSelectionBounds &bounds) const;
    std::array<float, 3> sampleLightingRgb(const bx::Vec3 &position) const;

    uint32_t sourceLightCount() const;
    uint32_t clusteredInputLightCount() const;
    uint32_t outputClusterLightCount() const;

    static float emitterUniformIntensity(const WorldFxLightEmitter &light);

private:
    std::vector<uint32_t> lightCandidatesForBounds(const OutdoorLightSelectionBounds &bounds) const;

    std::vector<WorldFxLightEmitter> m_lights;
    std::unordered_map<uint64_t, std::vector<uint32_t>> m_lightIndicesByCell;
    std::vector<uint32_t> m_globalLightIndices;
    uint32_t m_sourceLightCount = 0;
    uint32_t m_clusteredInputLightCount = 0;
    uint32_t m_outputClusterLightCount = 0;
};
}
