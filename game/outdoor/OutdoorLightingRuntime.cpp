#include "game/outdoor/OutdoorLightingRuntime.h"

#include "game/render/lighting/FxLightClustering.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float OutdoorFxLightGridCellSize = 512.0f;
constexpr float OutdoorLocalFxLightSelectionPadding = 96.0f;
constexpr float OutdoorMaxUniformFxLightIntensity = 2.5f;
constexpr float OutdoorFxLightingAmbient = 1.0f;
constexpr float OutdoorFxLightingScale = 1.6f;
constexpr float OutdoorFxClusterCellSize = 1536.0f;
constexpr uint32_t OutdoorFxClusterThreshold = 4;
constexpr uint32_t MaxOutdoorFxClusters = 8;
constexpr float MaxOutdoorFxClusterRadius = 960.0f;
constexpr float OutdoorLargeLightRadius = 8192.0f;

float redChannel(uint32_t colorAbgr)
{
    return static_cast<float>(colorAbgr & 0xffu) / 255.0f;
}

float greenChannel(uint32_t colorAbgr)
{
    return static_cast<float>((colorAbgr >> 8) & 0xffu) / 255.0f;
}

float blueChannel(uint32_t colorAbgr)
{
    return static_cast<float>((colorAbgr >> 16) & 0xffu) / 255.0f;
}

float alphaChannel(uint32_t colorAbgr)
{
    return static_cast<float>((colorAbgr >> 24) & 0xffu) / 255.0f;
}

bx::Vec3 outdoorBoundsCenter(const OutdoorLightSelectionBounds &bounds)
{
    return {
        (bounds.min.x + bounds.max.x) * 0.5f,
        (bounds.min.y + bounds.max.y) * 0.5f,
        (bounds.min.z + bounds.max.z) * 0.5f
    };
}

bx::Vec3 closestPointOnOutdoorBounds(const bx::Vec3 &point, const OutdoorLightSelectionBounds &bounds)
{
    return {
        std::clamp(point.x, bounds.min.x, bounds.max.x),
        std::clamp(point.y, bounds.min.y, bounds.max.y),
        std::clamp(point.z, bounds.min.z, bounds.max.z)
    };
}

float outdoorDistanceSquared(const bx::Vec3 &left, const bx::Vec3 &right)
{
    const float dx = left.x - right.x;
    const float dy = left.y - right.y;
    const float dz = left.z - right.z;
    return dx * dx + dy * dy + dz * dz;
}

int32_t outdoorFxLightGridCell(float value)
{
    return static_cast<int32_t>(std::floor(value / OutdoorFxLightGridCellSize));
}

uint64_t outdoorFxLightGridKey(int32_t cellX, int32_t cellY)
{
    return (static_cast<uint64_t>(static_cast<uint32_t>(cellX)) << 32)
        | static_cast<uint64_t>(static_cast<uint32_t>(cellY));
}

bool outdoorLightTouchesBounds(const WorldFxLightEmitter &light, const OutdoorLightSelectionBounds &bounds)
{
    if (!bounds.valid)
    {
        return true;
    }

    const bx::Vec3 lightPosition = {light.x, light.y, light.z};
    const bx::Vec3 closestPoint = closestPointOnOutdoorBounds(lightPosition, bounds);
    const float effectiveRadius = light.radius + OutdoorLocalFxLightSelectionPadding;
    return outdoorDistanceSquared(lightPosition, closestPoint) <= effectiveRadius * effectiveRadius;
}

RenderLight renderLightFromOutdoorEmitter(const WorldFxLightEmitter &emitter)
{
    RenderLight light = {};
    light.position = {emitter.x, emitter.y, emitter.z};
    light.radius = emitter.radius;
    light.colorAbgr = emitter.colorAbgr;
    light.intensity = emitter.intensity;
    light.sectorId = emitter.sectorId;
    light.kind = emitter.kind;
    light.stableId = emitter.stableId;
    light.dynamic = true;
    light.important = emitter.important;
    return light;
}

WorldFxLightEmitter outdoorEmitterFromRenderLight(const RenderLight &light)
{
    WorldFxLightEmitter emitter = {};
    emitter.x = light.position.x;
    emitter.y = light.position.y;
    emitter.z = light.position.z;
    emitter.radius = light.radius;
    emitter.colorAbgr = light.colorAbgr;
    emitter.intensity = light.intensity;
    emitter.sectorId = light.sectorId;
    emitter.kind = light.kind;
    emitter.stableId = light.stableId;
    emitter.important = light.important;
    return emitter;
}

std::vector<WorldFxLightEmitter> buildClusteredOutdoorFxLights(
    const std::vector<WorldFxLightEmitter> &sourceLights,
    uint32_t &clusteredInputLightCount,
    uint32_t &outputClusterLightCount)
{
    clusteredInputLightCount = 0;
    outputClusterLightCount = 0;

    std::vector<RenderLight> renderLights;
    renderLights.reserve(sourceLights.size());

    for (const WorldFxLightEmitter &emitter : sourceLights)
    {
        renderLights.push_back(renderLightFromOutdoorEmitter(emitter));
    }

    FxLightClusterConfig clusterConfig = {};
    clusterConfig.cellSize = OutdoorFxClusterCellSize;
    clusterConfig.thresholdPerSector = OutdoorFxClusterThreshold;
    clusterConfig.maxClustersPerSector = MaxOutdoorFxClusters;
    clusterConfig.maxRadius = MaxOutdoorFxClusterRadius;
    clusterConfig.maxIntensity = OutdoorMaxUniformFxLightIntensity;
    clusterConfig.allowSectorlessLights = true;

    const FxLightClusterResult clusteredLights =
        FxLightClustering::clusterSectorFxLights(renderLights, clusterConfig);

    clusteredInputLightCount = clusteredLights.clusteredInputLights;
    outputClusterLightCount = clusteredLights.outputClusterLights;

    std::vector<WorldFxLightEmitter> emitters;
    emitters.reserve(clusteredLights.lights.size());

    for (const RenderLight &light : clusteredLights.lights)
    {
        emitters.push_back(outdoorEmitterFromRenderLight(light));
    }

    return emitters;
}

bool insertOutdoorRankedLight(
    std::array<std::pair<const WorldFxLightEmitter *, float>, OutdoorSelectedFxLights::MaxLights> &rankedLights,
    size_t &rankedLightCount,
    const WorldFxLightEmitter &light,
    float score)
{
    if (rankedLightCount == OutdoorSelectedFxLights::MaxLights && score <= rankedLights[rankedLightCount - 1].second)
    {
        return false;
    }

    size_t insertIndex = rankedLightCount;

    if (rankedLightCount < OutdoorSelectedFxLights::MaxLights)
    {
        ++rankedLightCount;
    }
    else
    {
        insertIndex = OutdoorSelectedFxLights::MaxLights - 1;
    }

    while (insertIndex > 0 && score > rankedLights[insertIndex - 1].second)
    {
        rankedLights[insertIndex] = rankedLights[insertIndex - 1];
        --insertIndex;
    }

    rankedLights[insertIndex] = {&light, score};
    return true;
}

void appendUniqueCandidate(
    std::vector<uint32_t> &candidates,
    std::vector<uint8_t> &seen,
    uint32_t lightIndex)
{
    if (lightIndex >= seen.size() || seen[lightIndex] != 0)
    {
        return;
    }

    seen[lightIndex] = 1;
    candidates.push_back(lightIndex);
}
}

void OutdoorLightingRuntime::reset()
{
    m_lights.clear();
    m_lightIndicesByCell.clear();
    m_globalLightIndices.clear();
    m_sourceLightCount = 0;
    m_clusteredInputLightCount = 0;
    m_outputClusterLightCount = 0;
}

void OutdoorLightingRuntime::build(const WorldFxSystem &worldFxSystem)
{
    build(worldFxSystem.lightEmitters());
}

void OutdoorLightingRuntime::build(const std::vector<WorldFxLightEmitter> &lightEmitters)
{
    reset();

    m_sourceLightCount = static_cast<uint32_t>(lightEmitters.size());
    m_lights = buildClusteredOutdoorFxLights(
        lightEmitters,
        m_clusteredInputLightCount,
        m_outputClusterLightCount);

    for (size_t lightIndex = 0; lightIndex < m_lights.size(); ++lightIndex)
    {
        const WorldFxLightEmitter &light = m_lights[lightIndex];

        if (light.radius <= 1.0f || emitterUniformIntensity(light) <= 0.01f)
        {
            continue;
        }

        if (light.radius > OutdoorLargeLightRadius)
        {
            m_globalLightIndices.push_back(static_cast<uint32_t>(lightIndex));
            continue;
        }

        const float effectiveRadius = light.radius + OutdoorLocalFxLightSelectionPadding;
        const int32_t minCellX = outdoorFxLightGridCell(light.x - effectiveRadius);
        const int32_t maxCellX = outdoorFxLightGridCell(light.x + effectiveRadius);
        const int32_t minCellY = outdoorFxLightGridCell(light.y - effectiveRadius);
        const int32_t maxCellY = outdoorFxLightGridCell(light.y + effectiveRadius);

        for (int32_t cellY = minCellY; cellY <= maxCellY; ++cellY)
        {
            for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
            {
                m_lightIndicesByCell[outdoorFxLightGridKey(cellX, cellY)].push_back(
                    static_cast<uint32_t>(lightIndex));
            }
        }
    }
}

OutdoorSelectedFxLights OutdoorLightingRuntime::selectForBounds(
    const bx::Vec3 &fallbackReferencePosition,
    const OutdoorLightSelectionBounds &bounds) const
{
    OutdoorSelectedFxLights result = {};
    std::array<std::pair<const WorldFxLightEmitter *, float>, OutdoorSelectedFxLights::MaxLights> rankedLights = {};
    size_t rankedLightCount = 0;
    const bx::Vec3 referencePosition = bounds.valid ? outdoorBoundsCenter(bounds) : fallbackReferencePosition;
    const std::vector<uint32_t> candidateIndices = lightCandidatesForBounds(bounds);

    if (candidateIndices.size() < m_lights.size())
    {
        result.filteredEmitterCount += static_cast<uint32_t>(m_lights.size() - candidateIndices.size());
    }

    for (uint32_t lightIndex : candidateIndices)
    {
        if (lightIndex >= m_lights.size())
        {
            continue;
        }

        const WorldFxLightEmitter &light = m_lights[lightIndex];

        if (light.radius <= 1.0f)
        {
            ++result.filteredEmitterCount;
            continue;
        }

        const float intensity = emitterUniformIntensity(light);

        if (intensity <= 0.01f)
        {
            ++result.filteredEmitterCount;
            continue;
        }

        if (!outdoorLightTouchesBounds(light, bounds))
        {
            ++result.filteredEmitterCount;
            continue;
        }

        const bx::Vec3 lightPosition = {light.x, light.y, light.z};
        const bx::Vec3 closestPoint = bounds.valid
            ? closestPointOnOutdoorBounds(lightPosition, bounds)
            : referencePosition;
        const float distance = std::sqrt(outdoorDistanceSquared(lightPosition, closestPoint));
        const float importantScale = light.important ? 1.35f : 1.0f;
        const float score = (light.radius * intensity * importantScale) / std::max(distance, 64.0f);
        ++result.rankedCandidateCount;
        insertOutdoorRankedLight(rankedLights, rankedLightCount, light, score);
    }

    result.positions.fill(0.0f);
    result.colors.fill(0.0f);

    for (size_t index = 0; index < rankedLightCount; ++index)
    {
        const WorldFxLightEmitter &light = *rankedLights[index].first;
        const size_t baseIndex = index * 4;
        result.positions[baseIndex + 0] = light.x;
        result.positions[baseIndex + 1] = light.y;
        result.positions[baseIndex + 2] = light.z;
        result.positions[baseIndex + 3] = light.radius;
        result.colors[baseIndex + 0] = redChannel(light.colorAbgr);
        result.colors[baseIndex + 1] = greenChannel(light.colorAbgr);
        result.colors[baseIndex + 2] = blueChannel(light.colorAbgr);
        result.colors[baseIndex + 3] = emitterUniformIntensity(light);
    }

    result.lightCount = static_cast<uint32_t>(rankedLightCount);
    result.params = {{
        static_cast<float>(result.lightCount),
        OutdoorFxLightingAmbient,
        OutdoorFxLightingScale,
        0.0f
    }};
    return result;
}

std::array<float, 3> OutdoorLightingRuntime::sampleLightingRgb(const bx::Vec3 &position) const
{
    std::array<float, 3> rgb = {0.0f, 0.0f, 0.0f};

    const auto sampleLight =
        [&rgb, &position, this](uint32_t lightIndex)
        {
            if (lightIndex >= m_lights.size())
            {
                return;
            }

            const WorldFxLightEmitter &light = m_lights[lightIndex];
            const float intensity = emitterUniformIntensity(light);

            if (light.radius <= 1.0f || intensity <= 0.01f)
            {
                return;
            }

            const bx::Vec3 lightPosition = {light.x, light.y, light.z};
            const float distanceSquared = outdoorDistanceSquared(lightPosition, position);
            const float radius = std::max(light.radius, 1.0f);

            if (distanceSquared > radius * radius)
            {
                return;
            }

            float attenuation = 1.0f - std::clamp(distanceSquared / (radius * radius), 0.0f, 1.0f);
            attenuation *= attenuation;
            const float contribution = intensity * attenuation * OutdoorFxLightingScale;
            rgb[0] += redChannel(light.colorAbgr) * contribution;
            rgb[1] += greenChannel(light.colorAbgr) * contribution;
            rgb[2] += blueChannel(light.colorAbgr) * contribution;
        };

    for (uint32_t lightIndex : m_globalLightIndices)
    {
        sampleLight(lightIndex);
    }

    const int32_t cellX = outdoorFxLightGridCell(position.x);
    const int32_t cellY = outdoorFxLightGridCell(position.y);
    const auto iterator = m_lightIndicesByCell.find(outdoorFxLightGridKey(cellX, cellY));

    if (iterator != m_lightIndicesByCell.end())
    {
        for (uint32_t lightIndex : iterator->second)
        {
            sampleLight(lightIndex);
        }
    }

    rgb[0] = std::clamp(rgb[0], 0.0f, 1.2f);
    rgb[1] = std::clamp(rgb[1], 0.0f, 1.2f);
    rgb[2] = std::clamp(rgb[2], 0.0f, 1.2f);
    return rgb;
}

uint32_t OutdoorLightingRuntime::sourceLightCount() const
{
    return m_sourceLightCount;
}

uint32_t OutdoorLightingRuntime::clusteredInputLightCount() const
{
    return m_clusteredInputLightCount;
}

uint32_t OutdoorLightingRuntime::outputClusterLightCount() const
{
    return m_outputClusterLightCount;
}

float OutdoorLightingRuntime::emitterUniformIntensity(const WorldFxLightEmitter &light)
{
    return std::clamp(
        alphaChannel(light.colorAbgr) * std::max(light.intensity, 0.0f),
        0.0f,
        OutdoorMaxUniformFxLightIntensity);
}

std::vector<uint32_t> OutdoorLightingRuntime::lightCandidatesForBounds(
    const OutdoorLightSelectionBounds &bounds) const
{
    std::vector<uint32_t> candidates;

    if (!bounds.valid)
    {
        candidates.reserve(m_lights.size());

        for (size_t lightIndex = 0; lightIndex < m_lights.size(); ++lightIndex)
        {
            candidates.push_back(static_cast<uint32_t>(lightIndex));
        }

        return candidates;
    }

    std::vector<uint8_t> seen(m_lights.size(), 0);
    candidates.reserve(OutdoorSelectedFxLights::MaxLights * 4);

    for (uint32_t lightIndex : m_globalLightIndices)
    {
        appendUniqueCandidate(candidates, seen, lightIndex);
    }

    const int32_t minCellX = outdoorFxLightGridCell(bounds.min.x);
    const int32_t maxCellX = outdoorFxLightGridCell(bounds.max.x);
    const int32_t minCellY = outdoorFxLightGridCell(bounds.min.y);
    const int32_t maxCellY = outdoorFxLightGridCell(bounds.max.y);

    for (int32_t cellY = minCellY; cellY <= maxCellY; ++cellY)
    {
        for (int32_t cellX = minCellX; cellX <= maxCellX; ++cellX)
        {
            const auto iterator = m_lightIndicesByCell.find(outdoorFxLightGridKey(cellX, cellY));

            if (iterator == m_lightIndicesByCell.end())
            {
                continue;
            }

            for (uint32_t lightIndex : iterator->second)
            {
                appendUniqueCandidate(candidates, seen, lightIndex);
            }
        }
    }

    return candidates;
}

}
