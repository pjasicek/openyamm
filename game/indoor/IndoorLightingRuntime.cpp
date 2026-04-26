#include "game/indoor/IndoorLightingRuntime.h"

#include "game/events/EventRuntime.h"
#include "game/fx/WorldFxSystem.h"
#include "game/gameplay/GameplayTorchLight.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapAssetLoader.h"
#include "game/party/Party.h"
#include "game/tables/SpriteTables.h"

#include <algorithm>
#include <cmath>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t BlvLightDisabledAttribute = 0x08u;
constexpr float IndoorAmbientMin = 0.18f;
constexpr float IndoorAmbientMax = 1.0f;
constexpr float IndoorLightScale = 1.35f;
constexpr uint8_t DefaultLightAlpha = 224;
constexpr uint8_t FxLightAlphaFallback = 208;

float indoorRenderLightKindWeight(IndoorRenderLightKind kind)
{
    switch (kind)
    {
        case IndoorRenderLightKind::Fx:
            return 12.0f;

        case IndoorRenderLightKind::Torch:
            return 10.0f;

        case IndoorRenderLightKind::Decoration:
            return 4.0f;

        case IndoorRenderLightKind::Static:
            return 1.0f;
    }

    return 1.0f;
}

bool isFxLight(IndoorRenderLightKind kind)
{
    return kind == IndoorRenderLightKind::Fx;
}

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

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha = 255)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

float distanceSquared(const bx::Vec3 &left, const bx::Vec3 &right)
{
    const float dx = left.x - right.x;
    const float dy = left.y - right.y;
    const float dz = left.z - right.z;
    return dx * dx + dy * dy + dz * dz;
}

bx::Vec3 closestPointOnBounds(const bx::Vec3 &point, const IndoorLightSelectionBounds &bounds)
{
    return {
        std::clamp(point.x, bounds.min.x, bounds.max.x),
        std::clamp(point.y, bounds.min.y, bounds.max.y),
        std::clamp(point.z, bounds.min.z, bounds.max.z)
    };
}

bx::Vec3 boundsCenter(const IndoorLightSelectionBounds &bounds)
{
    return {
        (bounds.min.x + bounds.max.x) * 0.5f,
        (bounds.min.y + bounds.max.y) * 0.5f,
        (bounds.min.z + bounds.max.z) * 0.5f
    };
}

bool lightTouchesBounds(const IndoorRenderLight &light, const IndoorLightSelectionBounds &bounds)
{
    if (!bounds.valid)
    {
        return true;
    }

    const bx::Vec3 closestPoint = closestPointOnBounds(light.position, bounds);
    return distanceSquared(light.position, closestPoint) <= light.radius * light.radius;
}

bool sectorVisible(const std::vector<uint8_t> *pVisibleSectorMask, size_t sectorId)
{
    return pVisibleSectorMask == nullptr
        || sectorId >= pVisibleSectorMask->size()
        || (*pVisibleSectorMask)[sectorId] != 0;
}

bool sectorVisible(const std::vector<uint8_t> *pVisibleSectorMask, int16_t sectorId)
{
    return sectorId < 0
        || sectorVisible(pVisibleSectorMask, static_cast<size_t>(sectorId));
}

void appendFrameLight(
    IndoorLightingFrame &frame,
    const IndoorRenderLight &light,
    bool global)
{
    if (light.radius <= 0.0f || light.intensity <= 0.0f)
    {
        return;
    }

    const uint32_t lightIndex = static_cast<uint32_t>(frame.lights.size());
    frame.lights.push_back(light);

    if (light.kind == IndoorRenderLightKind::Fx)
    {
        frame.fxLightIndices.push_back(lightIndex);
    }

    if (global || light.sectorId < 0)
    {
        frame.globalLightIndices.push_back(lightIndex);
        return;
    }

    const size_t sectorId = static_cast<size_t>(light.sectorId);

    if (sectorId >= frame.lightIndicesBySector.size())
    {
        frame.globalLightIndices.push_back(lightIndex);
        return;
    }

    frame.lightIndicesBySector[sectorId].push_back(lightIndex);
}

bool lightMatchesSector(const IndoorRenderLight &light, int16_t sectorId, int16_t backSectorId)
{
    return light.sectorId < 0 || light.sectorId == sectorId || light.sectorId == backSectorId;
}

bx::Vec3 normalizedVector(const bx::Vec3 &value)
{
    const float length = std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);

    if (length <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {value.x / length, value.y / length, value.z / length};
}

float dotProduct(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

float lightDrawScore(
    const IndoorRenderLight &light,
    const bx::Vec3 &position,
    const bx::Vec3 &normalizedViewForward,
    int16_t sectorId,
    int16_t backSectorId)
{
    if (light.radius <= 1.0f || light.intensity <= 0.0f)
    {
        return -1.0f;
    }

    const bx::Vec3 toLight = {
        light.position.x - position.x,
        light.position.y - position.y,
        light.position.z - position.z
    };
    const float lightDistanceSquared = toLight.x * toLight.x + toLight.y * toLight.y + toLight.z * toLight.z;
    const float distance = std::sqrt(lightDistanceSquared);
    const bool affectsReferencePoint = distance <= light.radius;
    const bool matchesSector = lightMatchesSector(light, sectorId, backSectorId);
    const float inverseDistance = distance > 0.0001f ? 1.0f / distance : 0.0f;
    const float forwardDot = dotProduct(toLight, normalizedViewForward) * inverseDistance;
    const float frontScore = std::clamp((forwardDot + 0.25f) / 1.25f, 0.0f, 1.0f);
    const bool plausiblyVisible = frontScore > 0.0f;

    if (!affectsReferencePoint && !matchesSector && !plausiblyVisible)
    {
        return -1.0f;
    }

    const float distanceScore = light.radius * light.intensity / std::max(distance, 1.0f);
    const float sectorScore = matchesSector ? 200.0f : 0.0f;
    const float pointScore = affectsReferencePoint ? 500.0f : 0.0f;
    const float viewScore = frontScore * 1000.0f;

    return sectorScore + pointScore + viewScore + distanceScore * indoorRenderLightKindWeight(light.kind);
}

std::array<float, 3> lightContributionAtPoint(const IndoorRenderLight &light, const bx::Vec3 &position)
{
    if (light.radius <= 1.0f || light.intensity <= 0.0f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    const float lightDistanceSquared = distanceSquared(light.position, position);
    const float radiusSquared = light.radius * light.radius;

    if (lightDistanceSquared > radiusSquared)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    const float inverseRadiusSquared = 1.0f / radiusSquared;
    float attenuation = 1.0f - std::clamp(lightDistanceSquared * inverseRadiusSquared, 0.0f, 1.0f);
    attenuation *= attenuation;
    attenuation *= light.intensity * IndoorLightScale;

    return {
        redChannel(light.colorAbgr) * alphaChannel(light.colorAbgr) * attenuation,
        greenChannel(light.colorAbgr) * alphaChannel(light.colorAbgr) * attenuation,
        blueChannel(light.colorAbgr) * alphaChannel(light.colorAbgr) * attenuation
    };
}

void addLightingSample(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position,
    uint32_t lightIndex,
    std::array<float, 3> &rgb)
{
    if (lightIndex >= frame.lights.size())
    {
        return;
    }

    const IndoorRenderLight &light = frame.lights[lightIndex];
    const std::array<float, 3> contribution = lightContributionAtPoint(light, position);
    rgb[0] += contribution[0];
    rgb[1] += contribution[1];
    rgb[2] += contribution[2];
}

void addSectorLightingSample(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position,
    int16_t sectorId,
    std::array<float, 3> &rgb)
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= frame.lightIndicesBySector.size())
    {
        return;
    }

    for (uint32_t lightIndex : frame.lightIndicesBySector[static_cast<size_t>(sectorId)])
    {
        addLightingSample(frame, position, lightIndex, rgb);
    }
}

std::array<float, 3> clampedLightingSample(std::array<float, 3> rgb)
{
    rgb[0] = std::clamp(rgb[0], 0.0f, 2.0f);
    rgb[1] = std::clamp(rgb[1], 0.0f, 2.0f);
    rgb[2] = std::clamp(rgb[2], 0.0f, 2.0f);
    return rgb;
}

std::array<float, 3> approximateLightContribution(
    const IndoorRenderLight &light,
    const bx::Vec3 &referencePosition,
    const IndoorLightSelectionBounds &bounds)
{
    const bx::Vec3 samplePoint = bounds.valid ? boundsCenter(bounds) : referencePosition;
    return lightContributionAtPoint(light, samplePoint);
}

IndoorDrawLightSet packDrawLightSet(
    const IndoorLightingFrame &frame,
    const std::array<uint32_t, MaxIndoorDrawLights> &lightIndices,
    size_t selectedLightCount,
    const std::array<float, 3> &approximateRgb)
{
    IndoorDrawLightSet lightSet = {};
    const size_t lightCount = std::min(selectedLightCount, MaxIndoorDrawLights);

    for (size_t index = 0; index < lightCount; ++index)
    {
        const uint32_t lightIndex = lightIndices[index];

        if (lightIndex >= frame.lights.size())
        {
            continue;
        }

        const IndoorRenderLight &light = frame.lights[lightIndex];
        const size_t base = index * 4;
        lightSet.positions[base + 0] = light.position.x;
        lightSet.positions[base + 1] = light.position.y;
        lightSet.positions[base + 2] = light.position.z;
        lightSet.positions[base + 3] = light.radius;
        lightSet.colors[base + 0] = redChannel(light.colorAbgr);
        lightSet.colors[base + 1] = greenChannel(light.colorAbgr);
        lightSet.colors[base + 2] = blueChannel(light.colorAbgr);
        lightSet.colors[base + 3] = alphaChannel(light.colorAbgr) * light.intensity * IndoorLightScale;
    }

    lightSet.lightCount = lightCount;
    lightSet.params = {{
        static_cast<float>(lightCount),
        std::clamp(frame.ambient + approximateRgb[0], 0.0f, 2.0f),
        std::clamp(frame.ambient + approximateRgb[1], 0.0f, 2.0f),
        std::clamp(frame.ambient + approximateRgb[2], 0.0f, 2.0f)
    }};
    return lightSet;
}

struct CandidateLightList
{
    static constexpr size_t InlineCapacity = 128;

    std::array<uint32_t, InlineCapacity> inlineIndices = {};
    std::vector<uint32_t> overflowIndices;
    size_t inlineCount = 0;

    size_t size() const
    {
        return inlineCount + overflowIndices.size();
    }

    uint32_t at(size_t index) const
    {
        if (index < inlineCount)
        {
            return inlineIndices[index];
        }

        return overflowIndices[index - inlineCount];
    }

    void push(uint32_t lightIndex)
    {
        if (inlineCount < inlineIndices.size())
        {
            inlineIndices[inlineCount] = lightIndex;
            ++inlineCount;
            return;
        }

        overflowIndices.push_back(lightIndex);
    }
};

void appendLightCandidate(
    const IndoorLightingFrame &frame,
    CandidateLightList &candidateLightIndices,
    uint32_t lightIndex)
{
    if (lightIndex >= frame.lights.size())
    {
        return;
    }

    candidateLightIndices.push(lightIndex);
}

void appendSectorLightCandidates(
    const IndoorLightingFrame &frame,
    CandidateLightList &candidateLightIndices,
    int16_t sectorId)
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= frame.lightIndicesBySector.size())
    {
        return;
    }

    for (uint32_t lightIndex : frame.lightIndicesBySector[static_cast<size_t>(sectorId)])
    {
        appendLightCandidate(frame, candidateLightIndices, lightIndex);
    }
}

bool selectedLightContains(
    const std::array<uint32_t, MaxIndoorDrawLights> &selectedLightIndices,
    size_t selectedLightCount,
    uint32_t lightIndex)
{
    for (size_t index = 0; index < selectedLightCount; ++index)
    {
        if (selectedLightIndices[index] == lightIndex)
        {
            return true;
        }
    }

    return false;
}

template <size_t Capacity>
void insertRankedLight(
    std::array<std::pair<uint32_t, float>, Capacity> &rankedLights,
    size_t &rankedLightCount,
    uint32_t lightIndex,
    float score)
{
    if (Capacity == 0)
    {
        return;
    }

    if (rankedLightCount == Capacity && score <= rankedLights[rankedLightCount - 1].second)
    {
        return;
    }

    size_t insertIndex = rankedLightCount;

    if (rankedLightCount < Capacity)
    {
        ++rankedLightCount;
    }
    else
    {
        insertIndex = Capacity - 1;
    }

    while (insertIndex > 0 && score > rankedLights[insertIndex - 1].second)
    {
        rankedLights[insertIndex] = rankedLights[insertIndex - 1];
        --insertIndex;
    }

    rankedLights[insertIndex] = {lightIndex, score};
}

bool trySelectLight(
    std::array<uint32_t, MaxIndoorDrawLights> &selectedLightIndices,
    size_t &selectedLightCount,
    uint32_t lightIndex)
{
    if (selectedLightCount >= MaxIndoorDrawLights
        || selectedLightContains(selectedLightIndices, selectedLightCount, lightIndex))
    {
        return false;
    }

    selectedLightIndices[selectedLightCount] = lightIndex;
    ++selectedLightCount;
    return true;
}
}

bool IndoorLightingRuntime::isBlvLightEnabledByState(
    uint32_t attributes,
    const EventRuntimeState *pState,
    size_t lightId)
{
    if (pState != nullptr)
    {
        const auto iterator = pState->indoorLightsEnabled.find(static_cast<uint32_t>(lightId));

        if (iterator != pState->indoorLightsEnabled.end())
        {
            return iterator->second;
        }
    }

    return (attributes & BlvLightDisabledAttribute) == 0;
}

float IndoorLightingRuntime::ambientFromMinAmbientLightLevel(int minAmbientLightLevel)
{
    const int clampedLevel = std::clamp(minAmbientLightLevel, 0, 31);
    const float ambient = (248.0f - static_cast<float>(clampedLevel << 3)) / 255.0f;
    return std::clamp(ambient, IndoorAmbientMin, IndoorAmbientMax);
}

std::array<float, 3> IndoorLightingRuntime::sampleLightingRgb(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position)
{
    std::array<float, 3> rgb = {frame.ambient, frame.ambient, frame.ambient};

    for (uint32_t lightIndex = 0; lightIndex < frame.lights.size(); ++lightIndex)
    {
        addLightingSample(frame, position, lightIndex, rgb);
    }

    return clampedLightingSample(rgb);
}

std::array<float, 3> IndoorLightingRuntime::sampleLightingRgbForSectors(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position,
    int16_t sectorId,
    int16_t backSectorId)
{
    if (sectorId < 0 && backSectorId < 0)
    {
        return sampleLightingRgb(frame, position);
    }

    std::array<float, 3> rgb = {frame.ambient, frame.ambient, frame.ambient};

    for (uint32_t lightIndex : frame.globalLightIndices)
    {
        addLightingSample(frame, position, lightIndex, rgb);
    }

    addSectorLightingSample(frame, position, sectorId, rgb);

    if (backSectorId != sectorId)
    {
        addSectorLightingSample(frame, position, backSectorId, rgb);
    }

    return clampedLightingSample(rgb);
}

IndoorDrawLightSet IndoorLightingRuntime::selectDrawLightSetForPoint(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position,
    const bx::Vec3 &viewForward)
{
    IndoorLightSelectionBounds bounds = {};
    return selectDrawLightSetForBounds(frame, position, viewForward, -1, -1, bounds);
}

IndoorDrawLightSet IndoorLightingRuntime::selectDrawLightSetForSectors(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &referencePosition,
    const bx::Vec3 &viewForward,
    int16_t sectorId,
    int16_t backSectorId)
{
    IndoorLightSelectionBounds bounds = {};
    return selectDrawLightSetForBounds(frame, referencePosition, viewForward, sectorId, backSectorId, bounds);
}

IndoorDrawLightSet IndoorLightingRuntime::selectDrawLightSetForBounds(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &referencePosition,
    const bx::Vec3 &viewForward,
    int16_t sectorId,
    int16_t backSectorId,
    const IndoorLightSelectionBounds &bounds)
{
    CandidateLightList candidateLightIndices = {};

    if (sectorId < 0 && backSectorId < 0)
    {
        for (uint32_t lightIndex = 0; lightIndex < frame.lights.size(); ++lightIndex)
        {
            appendLightCandidate(frame, candidateLightIndices, lightIndex);
        }
    }
    else
    {
        for (uint32_t lightIndex : frame.globalLightIndices)
        {
            appendLightCandidate(frame, candidateLightIndices, lightIndex);
        }

        appendSectorLightCandidates(frame, candidateLightIndices, sectorId);

        if (backSectorId != sectorId)
        {
            appendSectorLightCandidates(frame, candidateLightIndices, backSectorId);
        }

        if (bounds.valid)
        {
            // FX lights can visibly cross sector portals, but they should not be global candidates for every batch.
            for (uint32_t lightIndex : frame.fxLightIndices)
            {
                if (lightIndex >= frame.lights.size())
                {
                    continue;
                }

                const IndoorRenderLight &light = frame.lights[lightIndex];

                if (light.sectorId < 0 || light.sectorId == sectorId || light.sectorId == backSectorId)
                {
                    continue;
                }

                if (!lightTouchesBounds(light, bounds))
                {
                    continue;
                }

                appendLightCandidate(frame, candidateLightIndices, lightIndex);
            }
        }
    }

    const bx::Vec3 normalizedViewForward = normalizedVector(viewForward);
    constexpr size_t ReservedNonFxDetailLights = 4;
    std::array<std::pair<uint32_t, float>, ReservedNonFxDetailLights> rankedNonFxLights = {};
    std::array<std::pair<uint32_t, float>, MaxIndoorDrawLights> rankedLights = {};
    size_t rankedNonFxLightCount = 0;
    size_t rankedLightCount = 0;
    CandidateLightList touchingLightIndices = {};

    for (size_t candidateIndex = 0; candidateIndex < candidateLightIndices.size(); ++candidateIndex)
    {
        const uint32_t lightIndex = candidateLightIndices.at(candidateIndex);

        if (lightIndex >= frame.lights.size())
        {
            continue;
        }

        const IndoorRenderLight &light = frame.lights[lightIndex];

        if (!lightTouchesBounds(light, bounds))
        {
            continue;
        }

        touchingLightIndices.push(lightIndex);

        const float score = lightDrawScore(light, referencePosition, normalizedViewForward, sectorId, backSectorId);

        if (score <= 0.0f)
        {
            continue;
        }

        insertRankedLight(rankedLights, rankedLightCount, lightIndex, score);

        if (!isFxLight(light.kind))
        {
            insertRankedLight(rankedNonFxLights, rankedNonFxLightCount, lightIndex, score);
        }
    }

    std::array<uint32_t, MaxIndoorDrawLights> selectedLightIndices = {};
    size_t selectedLightCount = 0;

    for (size_t rankedIndex = 0; rankedIndex < rankedNonFxLightCount; ++rankedIndex)
    {
        trySelectLight(selectedLightIndices, selectedLightCount, rankedNonFxLights[rankedIndex].first);
    }

    for (size_t rankedIndex = 0; rankedIndex < rankedLightCount; ++rankedIndex)
    {
        if (selectedLightCount >= MaxIndoorDrawLights)
        {
            break;
        }

        trySelectLight(selectedLightIndices, selectedLightCount, rankedLights[rankedIndex].first);
    }

    std::array<float, 3> approximateRgb = {0.0f, 0.0f, 0.0f};

    for (size_t candidateIndex = 0; candidateIndex < touchingLightIndices.size(); ++candidateIndex)
    {
        const uint32_t lightIndex = touchingLightIndices.at(candidateIndex);

        if (lightIndex >= frame.lights.size()
            || selectedLightContains(selectedLightIndices, selectedLightCount, lightIndex))
        {
            continue;
        }

        const IndoorRenderLight &light = frame.lights[lightIndex];
        const float approximateTailLightScale = isFxLight(light.kind) ? 0.10f : 0.28f;
        const std::array<float, 3> contribution =
            approximateLightContribution(light, referencePosition, bounds);
        approximateRgb[0] += contribution[0] * approximateTailLightScale;
        approximateRgb[1] += contribution[1] * approximateTailLightScale;
        approximateRgb[2] += contribution[2] * approximateTailLightScale;
    }

    approximateRgb[0] = std::clamp(approximateRgb[0], 0.0f, 0.45f);
    approximateRgb[1] = std::clamp(approximateRgb[1], 0.0f, 0.45f);
    approximateRgb[2] = std::clamp(approximateRgb[2], 0.0f, 0.45f);
    return packDrawLightSet(frame, selectedLightIndices, selectedLightCount, approximateRgb);
}

uint32_t IndoorLightingRuntime::lightColorAbgr(
    uint8_t red,
    uint8_t green,
    uint8_t blue,
    uint8_t alpha,
    bool coloredLights)
{
    if (coloredLights)
    {
        return makeAbgr(red, green, blue, alpha);
    }

    const uint8_t brightness = static_cast<uint8_t>(
        std::clamp(
            static_cast<int>(std::lround(
                static_cast<float>(red) * 0.299f
                    + static_cast<float>(green) * 0.587f
                    + static_cast<float>(blue) * 0.114f)),
            0,
            255));
    return makeAbgr(brightness, brightness, brightness, alpha);
}

IndoorLightingRuntime::StaticLightCache IndoorLightingRuntime::buildStaticCache(
    const IndoorMapData &mapData,
    const DecorationBillboardSet *pDecorationBillboardSet)
{
    StaticLightCache cache = {};
    cache.sourceIndicesBySector.resize(mapData.sectors.size());

    const auto appendCachedLight =
        [&cache](const CachedLightSource &source)
        {
            if (source.radius <= 0.0f || source.intensity <= 0.0f)
            {
                return;
            }

            const uint32_t sourceIndex = static_cast<uint32_t>(cache.sources.size());
            cache.sources.push_back(source);

            if (source.sectorId >= 0 && static_cast<size_t>(source.sectorId) < cache.sourceIndicesBySector.size())
            {
                cache.sourceIndicesBySector[static_cast<size_t>(source.sectorId)].push_back(sourceIndex);
            }
        };

    for (size_t sectorId = 0; sectorId < mapData.sectors.size(); ++sectorId)
    {
        const IndoorSector &sector = mapData.sectors[sectorId];

        for (uint16_t lightId : sector.lightIds)
        {
            if (lightId >= mapData.lights.size())
            {
                continue;
            }

            const IndoorLight &source = mapData.lights[lightId];

            if (source.radius <= 0)
            {
                continue;
            }

            CachedLightSource light = {};
            light.position = {
                static_cast<float>(source.x),
                static_cast<float>(source.y),
                static_cast<float>(source.z)
            };
            light.radius = static_cast<float>(source.radius);
            light.red = source.red;
            light.green = source.green;
            light.blue = source.blue;
            light.alpha = DefaultLightAlpha;
            light.intensity = 1.0f;
            light.sectorId = static_cast<int16_t>(sectorId);
            light.kind = IndoorRenderLightKind::Static;
            light.sourceAttributes = static_cast<uint32_t>(source.attributes);
            light.sourceLightId = lightId;
            appendCachedLight(light);
        }
    }

    if (pDecorationBillboardSet != nullptr)
    {
        for (const DecorationBillboard &billboard : pDecorationBillboardSet->billboards)
        {
            const DecorationEntry *pDecoration = pDecorationBillboardSet->decorationTable.get(billboard.decorationId);

            if (pDecoration == nullptr)
            {
                continue;
            }

            const SpriteFrameEntry *pFrame =
                pDecorationBillboardSet->spriteFrameTable.getFrame(billboard.spriteId, 0);
            float radius = 0.0f;

            if (pDecoration->lightRadius > 0)
            {
                radius = static_cast<float>(pDecoration->lightRadius);
            }

            if (pFrame != nullptr && pFrame->glowRadius > 0)
            {
                radius = std::max(radius, static_cast<float>(pFrame->glowRadius));
            }

            if (radius <= 0.0f)
            {
                continue;
            }

            CachedLightSource light = {};
            light.position = {
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z) + static_cast<float>(std::max<uint16_t>(billboard.height, 1)) * 0.5f
            };
            light.radius = radius;
            light.red = 255;
            light.green = 255;
            light.blue = 255;
            light.alpha = 208;
            light.intensity = 1.0f;
            light.sectorId = billboard.sectorId;
            light.kind = IndoorRenderLightKind::Decoration;
            light.runtimeOverrideKey =
                billboard.eventIdPrimary != 0 ? billboard.eventIdPrimary : billboard.eventIdSecondary;

            if (pDecoration->lightRed != 0 || pDecoration->lightGreen != 0 || pDecoration->lightBlue != 0)
            {
                light.red = pDecoration->lightRed;
                light.green = pDecoration->lightGreen;
                light.blue = pDecoration->lightBlue;
            }

            appendCachedLight(light);
        }
    }

    cache.valid = true;
    return cache;
}

void IndoorLightingRuntime::rebuildStaticCache(
    const IndoorMapData &mapData,
    const DecorationBillboardSet *pDecorationBillboardSet)
{
    m_staticLightCache = buildStaticCache(mapData, pDecorationBillboardSet);
}

void IndoorLightingRuntime::clearStaticCache()
{
    m_staticLightCache = {};
}

IndoorLightingFrame IndoorLightingRuntime::buildFrame(const IndoorLightingFrameInput &input) const
{
    IndoorLightingFrame frame = {};
    frame.ambient = ambientFromMinAmbientLightLevel(0);

    if (input.pMapData != nullptr)
    {
        frame.lightIndicesBySector.resize(input.pMapData->sectors.size());
    }

    if (input.pMapData != nullptr && !input.pMapData->sectors.empty())
    {
        int maxAmbientLightLevel = 0;

        for (size_t sectorId = 0; sectorId < input.pMapData->sectors.size(); ++sectorId)
        {
            if (!sectorVisible(input.pVisibleSectorMask, sectorId))
            {
                continue;
            }

            const int sectorAmbientLightLevel =
                static_cast<int>(input.pMapData->sectors[sectorId].minAmbientLightLevel);
            maxAmbientLightLevel = std::max(maxAmbientLightLevel, sectorAmbientLightLevel);
        }

        frame.ambient = ambientFromMinAmbientLightLevel(maxAmbientLightLevel);
    }

    if (input.pParty != nullptr)
    {
        if (const std::optional<GameplayTorchLight> torchLight =
                resolveGameplayTorchLight(*input.pParty, false, true))
        {
            IndoorRenderLight torch = {};
            torch.position = input.cameraPosition;
            torch.radius = torchLight->radius;
            torch.colorAbgr = torchLight->colorAbgr;
            torch.intensity = torchLight->intensity;
            torch.kind = IndoorRenderLightKind::Torch;
            appendFrameLight(frame, torch, true);
        }
    }

    if (input.pWorldFxSystem != nullptr)
    {
        for (const WorldFxLightEmitter &emitter : input.pWorldFxSystem->lightEmitters())
        {
            IndoorRenderLight light = {};
            light.position = {emitter.x, emitter.y, emitter.z};
            light.radius = emitter.radius;
            light.colorAbgr =
                emitter.colorAbgr != 0
                    ? emitter.colorAbgr
                    : makeAbgr(255, 255, 255, FxLightAlphaFallback);
            light.intensity = 1.0f;
            light.sectorId = emitter.sectorId;
            light.kind = IndoorRenderLightKind::Fx;
            appendFrameLight(frame, light, false);
        }
    }

    StaticLightCache fallbackCache = {};
    const StaticLightCache *pStaticCache = &m_staticLightCache;

    if (!pStaticCache->valid && input.pMapData != nullptr)
    {
        fallbackCache = buildStaticCache(*input.pMapData, input.pDecorationBillboardSet);
        pStaticCache = &fallbackCache;
    }

    if (pStaticCache->valid)
    {
        std::vector<uint8_t> appendedSourceIndices(pStaticCache->sources.size(), 0);
        const auto appendCachedSource =
            [&](uint32_t sourceIndex)
            {
                if (sourceIndex >= pStaticCache->sources.size())
                {
                    return;
                }

                if (appendedSourceIndices[sourceIndex] != 0)
                {
                    return;
                }

                appendedSourceIndices[sourceIndex] = 1;
                const CachedLightSource &source = pStaticCache->sources[sourceIndex];

                if (source.kind == IndoorRenderLightKind::Static
                    && !isBlvLightEnabledByState(
                        source.sourceAttributes,
                        input.pEventRuntimeState,
                        source.sourceLightId))
                {
                    return;
                }

                if (source.kind == IndoorRenderLightKind::Decoration
                    && source.runtimeOverrideKey != 0
                    && input.pEventRuntimeState != nullptr)
                {
                    const auto iterator = input.pEventRuntimeState->spriteOverrides.find(source.runtimeOverrideKey);

                    if (iterator != input.pEventRuntimeState->spriteOverrides.end() && iterator->second.hidden)
                    {
                        return;
                    }
                }

                IndoorRenderLight light = {};
                light.position = source.position;
                light.radius = source.radius;
                light.colorAbgr =
                    lightColorAbgr(source.red, source.green, source.blue, source.alpha, input.coloredLights);
                light.intensity = source.intensity;
                light.sectorId = source.sectorId;
                light.kind = source.kind;
                appendFrameLight(frame, light, false);
            };

        if (!pStaticCache->sourceIndicesBySector.empty())
        {
            for (size_t sectorId = 0; sectorId < pStaticCache->sourceIndicesBySector.size(); ++sectorId)
            {
                if (!sectorVisible(input.pVisibleSectorMask, sectorId))
                {
                    continue;
                }

                for (uint32_t sourceIndex : pStaticCache->sourceIndicesBySector[sectorId])
                {
                    appendCachedSource(sourceIndex);
                }
            }
        }
        else
        {
            for (uint32_t sourceIndex = 0; sourceIndex < pStaticCache->sources.size(); ++sourceIndex)
            {
                appendCachedSource(sourceIndex);
            }
        }
    }

    return frame;
}
}
