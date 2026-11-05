#include "game/indoor/IndoorLightingRuntime.h"

#include "game/events/EventRuntime.h"
#include "game/fx/WorldFxSystem.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/gameplay/GameplayTorchLight.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMapData.h"
#include "game/indoor/IndoorModelLighting.h"
#include "game/maps/MapAssetLoader.h"
#include "game/party/Party.h"
#include "game/render/lighting/FxLightClustering.h"
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
constexpr float IndoorTorchLightIntensityScale = 1.5f;
constexpr uint8_t DefaultLightAlpha = 224;
constexpr uint8_t FxLightAlphaFallback = 208;
constexpr size_t InvalidDecorationDecorVarIndex = static_cast<size_t>(-1);
constexpr size_t MaxDecorationDecorVarCount = 125;
constexpr float IndoorFxClusterCellSize = 256.0f;
constexpr float MaxIndoorFxClusterRadius = 640.0f;
constexpr float MaxIndoorFxClusterIntensity = 2.5f;
constexpr size_t MaxIndoorTorchLightsPerDraw = 1;
constexpr size_t MaxIndoorStaticLightsPerDraw = 4;
constexpr size_t MaxIndoorFxLightsPerDraw = 7;

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

std::vector<size_t> buildIndoorInteractiveDecorationDecorVarIndices(
    const IndoorMapData &mapData,
    const DecorationBillboardSet *pDecorationBillboardSet)
{
    std::vector<size_t> decorVarIndices(mapData.entities.size(), InvalidDecorationDecorVarIndex);

    if (pDecorationBillboardSet == nullptr)
    {
        return decorVarIndices;
    }

    size_t decorVarIndex = 0;

    for (size_t entityIndex = 0; entityIndex < mapData.entities.size(); ++entityIndex)
    {
        const IndoorEntity &entity = mapData.entities[entityIndex];

        if (entity.scriptEventId() != 0)
        {
            continue;
        }

        const DecorationLookupResult decoration =
            pDecorationBillboardSet->decorationTable.resolveMapDecoration(entity.decorationListId, entity.name);
        const DecorationEntry *pDecoration = decoration.pEntry;

        if (pDecoration == nullptr)
        {
            continue;
        }

        if (resolveInteractiveDecorationBindingSpec(*pDecoration, entity.name))
        {
            if (decorVarIndex < MaxDecorationDecorVarCount)
            {
                decorVarIndices[entityIndex] = decorVarIndex;
            }

            ++decorVarIndex;
        }
    }

    return decorVarIndices;
}

bool isFxLight(IndoorRenderLightKind kind)
{
    return kind == IndoorRenderLightKind::Fx;
}

bool isTorchLight(IndoorRenderLightKind kind)
{
    return kind == IndoorRenderLightKind::Torch;
}

bool isStaticDetailLight(IndoorRenderLightKind kind)
{
    return kind == IndoorRenderLightKind::Static || kind == IndoorRenderLightKind::Decoration;
}

bool sampleFilterIncludesLight(IndoorLightingSampleFilter filter, IndoorRenderLightKind kind)
{
    switch (filter)
    {
        case IndoorLightingSampleFilter::All:
            return true;
        case IndoorLightingSampleFilter::StaticDetailOnly:
            return isStaticDetailLight(kind);
        case IndoorLightingSampleFilter::DynamicOnly:
            return !isStaticDetailLight(kind);
    }

    return true;
}

IndoorRenderLight indoorLightFromRenderLight(const RenderLight &source)
{
    IndoorRenderLight light = {};
    light.position = source.position;
    light.radius = source.radius;
    light.colorAbgr = source.colorAbgr;
    light.intensity = source.intensity;
    light.sectorId = source.sectorId;
    light.kind = IndoorRenderLightKind::Fx;
    light.stableId = source.stableId;
    return light;
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

float visibilityPlaneDistance(const IndoorVisibilityPlane &plane, const bx::Vec3 &point)
{
    return plane.normal.x * point.x + plane.normal.y * point.y + plane.normal.z * point.z + plane.distance;
}

bool sphereIntersectsVisibilityFrustum(
    const bx::Vec3 &center,
    float radius,
    const IndoorVisibilityFrustum &frustum)
{
    const float effectiveRadius = std::max(radius, 0.0f);

    for (const IndoorVisibilityPlane &plane : frustum)
    {
        if (visibilityPlaneDistance(plane, center) < -effectiveRadius)
        {
            return false;
        }
    }

    return true;
}

bool sphereIntersectsVisibleSectorFrustums(
    const std::vector<std::vector<IndoorVisibilityFrustum>> *pVisibleSectorFrustums,
    int16_t sectorId,
    const bx::Vec3 &center,
    float radius)
{
    if (pVisibleSectorFrustums == nullptr || pVisibleSectorFrustums->empty())
    {
        return true;
    }

    if (sectorId < 0 || static_cast<size_t>(sectorId) >= pVisibleSectorFrustums->size())
    {
        return false;
    }

    const std::vector<IndoorVisibilityFrustum> &frustums =
        (*pVisibleSectorFrustums)[static_cast<size_t>(sectorId)];

    for (const IndoorVisibilityFrustum &frustum : frustums)
    {
        if (sphereIntersectsVisibilityFrustum(center, radius, frustum))
        {
            return true;
        }
    }

    return false;
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

    if (global || light.sectorId < 0 || static_cast<size_t>(light.sectorId) >= frame.lightIndicesBySector.size())
    {
        frame.globalLightIndices.push_back(lightIndex);
        return;
    }

    // Listed in every room it reaches (its own when it has no reach list).
    std::vector<std::vector<uint32_t>> &lists =
        light.kind == IndoorRenderLightKind::Fx ? frame.dynamicLightIndicesBySector : frame.lightIndicesBySector;
    const auto list = [&](int16_t sectorId)
    {
        if (sectorId >= 0 && static_cast<size_t>(sectorId) < lists.size())
        {
            lists[static_cast<size_t>(sectorId)].push_back(lightIndex);
        }
    };
    if (light.reach.count == 0)
    {
        list(light.sectorId);
    }
    for (uint8_t entry = 0; entry < light.reach.count; ++entry)
    {
        list(light.reach.sectors[entry]);
    }
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
    std::array<float, 3> &rgb,
    IndoorLightingSampleFilter filter)
{
    if (lightIndex >= frame.lights.size())
    {
        return;
    }

    const IndoorRenderLight &light = frame.lights[lightIndex];

    if (!sampleFilterIncludesLight(filter, light.kind))
    {
        return;
    }

    const std::array<float, 3> contribution = lightContributionAtPoint(light, position);
    rgb[0] += contribution[0];
    rgb[1] += contribution[1];
    rgb[2] += contribution[2];
}

// Whether a frame light is listed in the sector (appendFrameLight's rule).
bool listedInSector(const IndoorLightingFrame &frame, uint32_t lightIndex, int16_t sectorId)
{
    if (sectorId < 0 || lightIndex >= frame.lights.size())
    {
        return false;
    }
    const IndoorRenderLight &light = frame.lights[lightIndex];
    if (light.sectorId < 0)
    {
        return false;
    }
    return light.reach.count == 0 ? light.sectorId == sectorId
        : std::find(light.reach.sectors.begin(), light.reach.sectors.begin() + light.reach.count, sectorId)
            != light.reach.sectors.begin() + light.reach.count;
}

// skipSector: lights listed there too were already counted (a light is listed in every room it reaches).
void addSectorLightingSample(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position,
    int16_t sectorId,
    std::array<float, 3> &rgb,
    IndoorLightingSampleFilter filter,
    int16_t skipSector = -1)
{
    if (sectorId < 0)
    {
        return;
    }

    if (static_cast<size_t>(sectorId) < frame.lightIndicesBySector.size())
    {
        for (uint32_t lightIndex : frame.lightIndicesBySector[static_cast<size_t>(sectorId)])
        {
            if (!listedInSector(frame, lightIndex, skipSector))
            {
                addLightingSample(frame, position, lightIndex, rgb, filter);
            }
        }
    }

    if (static_cast<size_t>(sectorId) >= frame.dynamicLightIndicesBySector.size())
    {
        return;
    }

    for (uint32_t lightIndex : frame.dynamicLightIndicesBySector[static_cast<size_t>(sectorId)])
    {
        if (!listedInSector(frame, lightIndex, skipSector))
        {
            addLightingSample(frame, position, lightIndex, rgb, filter);
        }
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
        lightSet.stableIds[index] = light.stableId;
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
    int16_t sectorId,
    int16_t skipSector = -1)
{
    if (sectorId < 0)
    {
        return;
    }

    if (static_cast<size_t>(sectorId) < frame.lightIndicesBySector.size())
    {
        for (uint32_t lightIndex : frame.lightIndicesBySector[static_cast<size_t>(sectorId)])
        {
            if (!listedInSector(frame, lightIndex, skipSector))
            {
                appendLightCandidate(frame, candidateLightIndices, lightIndex);
            }
        }
    }

    if (static_cast<size_t>(sectorId) >= frame.dynamicLightIndicesBySector.size())
    {
        return;
    }

    for (uint32_t lightIndex : frame.dynamicLightIndicesBySector[static_cast<size_t>(sectorId)])
    {
        if (!listedInSector(frame, lightIndex, skipSector))
        {
            appendLightCandidate(frame, candidateLightIndices, lightIndex);
        }
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

template <size_t Capacity>
void selectRankedLightsUpToBudget(
    std::array<uint32_t, MaxIndoorDrawLights> &selectedLightIndices,
    size_t &selectedLightCount,
    const std::array<std::pair<uint32_t, float>, Capacity> &rankedLights,
    size_t rankedLightCount,
    size_t budget)
{
    size_t selectedFromBudget = 0;

    for (size_t rankedIndex = 0; rankedIndex < rankedLightCount; ++rankedIndex)
    {
        if (selectedLightCount >= MaxIndoorDrawLights || selectedFromBudget >= budget)
        {
            break;
        }

        if (trySelectLight(selectedLightIndices, selectedLightCount, rankedLights[rankedIndex].first))
        {
            ++selectedFromBudget;
        }
    }
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

int IndoorLightingRuntime::sectorAmbientLevel(const IndoorMapData &mapData, const EventRuntimeState *pState,
    size_t sectorId)
{
    if (pState != nullptr && !pState->sectorAmbientLevels.empty())
    {
        const auto iterator = pState->sectorAmbientLevels.find(uint16_t(sectorId));

        if (iterator != pState->sectorAmbientLevels.end())
        {
            return iterator->second;
        }
    }

    return sectorId < mapData.sectors.size() ? int(mapData.sectors[sectorId].minAmbientLightLevel) : 0;
}

float IndoorLightingRuntime::sectorAmbient(const IndoorLightingFrame &frame, int16_t sectorId)
{
    return sectorId >= 0 && size_t(sectorId) < frame.sectorAmbient.size() ? frame.sectorAmbient[size_t(sectorId)]
                                                                          : frame.ambient;
}

void IndoorLightReachList::assign(const std::vector<int16_t> &reached)
{
    count = reached.size() <= sectors.size() ? uint8_t(reached.size()) : 0;
    std::copy_n(reached.begin(), count, sectors.begin());
}

bool IndoorLightReachList::reachesReceiver(int16_t sector, int16_t backSector) const
{
    if (sector < 0 && backSector < 0)
    {
        return true;
    }
    return (sector >= 0 && reaches(sector)) || (backSector >= 0 && reaches(backSector));
}

bool IndoorLightReachList::reaches(int16_t sector) const
{
    const auto last = sectors.begin() + count;
    return count == 0 || sector < 0 || std::find(sectors.begin(), last, sector) != last;
}

std::array<float, 3> IndoorLightingRuntime::sampleLightingRgb(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position,
    LightingStats *pStats,
    IndoorLightingSampleFilter filter)
{
    if (pStats != nullptr)
    {
        ++pStats->billboardSamples;
    }

    std::array<float, 3> rgb = {frame.ambient, frame.ambient, frame.ambient};

    for (uint32_t lightIndex = 0; lightIndex < frame.lights.size(); ++lightIndex)
    {
        addLightingSample(frame, position, lightIndex, rgb, filter);
    }

    return clampedLightingSample(rgb);
}

std::array<float, 3> IndoorLightingRuntime::sampleLightingRgbForSectors(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position,
    int16_t sectorId,
    int16_t backSectorId,
    LightingStats *pStats,
    IndoorLightingSampleFilter filter)
{
    if (pStats != nullptr)
    {
        ++pStats->billboardSamples;
    }

    if (sectorId < 0 && backSectorId < 0)
    {
        return sampleLightingRgb(frame, position, nullptr, filter);
    }

    // The receiving room's own ambient.
    const float ambient = sectorAmbient(frame, sectorId >= 0 ? sectorId : backSectorId);
    std::array<float, 3> rgb = {ambient, ambient, ambient};

    for (uint32_t lightIndex : frame.globalLightIndices)
    {
        addLightingSample(frame, position, lightIndex, rgb, filter);
    }

    addSectorLightingSample(frame, position, sectorId, rgb, filter);

    if (backSectorId != sectorId)
    {
        addSectorLightingSample(frame, position, backSectorId, rgb, filter, sectorId);
    }

    return clampedLightingSample(rgb);
}

float IndoorLightingRuntime::mapLightStrength()
{
    return float(DefaultLightAlpha) / 255.0f * IndoorLightScale;
}

std::array<float, 3> IndoorLightingRuntime::sampleModelLightRgb(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position,
    float lightScale)
{
    std::array<float, 3> rgb = {0.0f, 0.0f, 0.0f};
    const float scale = lightScale / mapLightStrength();
    for (const IndoorRenderLight &light : frame.lights)
    {
        const float strength = alphaChannel(light.colorAbgr) * light.intensity * IndoorLightScale * scale
            * indoorModelLightFalloff(distanceSquared(light.position, position), light.radius);
        rgb[0] += redChannel(light.colorAbgr) * strength;
        rgb[1] += greenChannel(light.colorAbgr) * strength;
        rgb[2] += blueChannel(light.colorAbgr) * strength;
    }
    return rgb;
}

IndoorDrawLightSet IndoorLightingRuntime::selectDrawLightSetForPoint(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &position,
    const bx::Vec3 &viewForward,
    LightingStats *pStats,
    bool includeStaticLights)
{
    IndoorLightSelectionBounds bounds = {};
    return selectDrawLightSetForBounds(
        frame,
        position,
        viewForward,
        -1,
        -1,
        bounds,
        pStats,
        includeStaticLights);
}

IndoorDrawLightSet IndoorLightingRuntime::selectDrawLightSetForSectors(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &referencePosition,
    const bx::Vec3 &viewForward,
    int16_t sectorId,
    int16_t backSectorId,
    LightingStats *pStats,
    bool includeStaticLights)
{
    IndoorLightSelectionBounds bounds = {};
    return selectDrawLightSetForBounds(
        frame,
        referencePosition,
        viewForward,
        sectorId,
        backSectorId,
        bounds,
        pStats,
        includeStaticLights);
}

std::vector<Engine::LightGridLight> IndoorLightingRuntime::gridLights(const IndoorLightingFrame &frame)
{
    std::vector<Engine::LightGridLight> lights;
    lights.reserve(frame.lights.size());
    for (const IndoorRenderLight &light : frame.lights)
    {
        Engine::LightGridLight gridLight;
        gridLight.position = {light.position.x, light.position.y, light.position.z};
        gridLight.radius = light.radius;
        gridLight.color = {redChannel(light.colorAbgr), greenChannel(light.colorAbgr), blueChannel(light.colorAbgr)};
        gridLight.intensity = alphaChannel(light.colorAbgr) * light.intensity * IndoorLightScale;
        gridLight.sector = light.sectorId;
        gridLight.reach = light.reach.sectors;
        gridLight.reachCount = light.reach.count;
        gridLight.dynamic = !isStaticDetailLight(light.kind);
        lights.push_back(gridLight);
    }
    return lights;
}

IndoorDrawLightSet IndoorLightingRuntime::selectDrawLightSetForBounds(
    const IndoorLightingFrame &frame,
    const bx::Vec3 &referencePosition,
    const bx::Vec3 &viewForward,
    int16_t sectorId,
    int16_t backSectorId,
    const IndoorLightSelectionBounds &bounds,
    LightingStats *pStats,
    bool includeStaticLights)
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
            appendSectorLightCandidates(frame, candidateLightIndices, backSectorId, sectorId);
        }

    }

    const bx::Vec3 normalizedViewForward = normalizedVector(viewForward);
    std::array<std::pair<uint32_t, float>, MaxIndoorDrawLights> rankedTorchLights = {};
    std::array<std::pair<uint32_t, float>, MaxIndoorDrawLights> rankedStaticLights = {};
    std::array<std::pair<uint32_t, float>, MaxIndoorDrawLights> rankedFxLights = {};
    std::array<std::pair<uint32_t, float>, MaxIndoorDrawLights> rankedLights = {};
    size_t rankedTorchLightCount = 0;
    size_t rankedStaticLightCount = 0;
    size_t rankedFxLightCount = 0;
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

        if (!includeStaticLights && isStaticDetailLight(light.kind))
        {
            continue;
        }

        if (!lightTouchesBounds(light, bounds))
        {
            continue;
        }

        touchingLightIndices.push(lightIndex);

        float score = lightDrawScore(light, referencePosition, normalizedViewForward, sectorId, backSectorId);

        if (score <= 0.0f)
        {
            continue;
        }

        insertRankedLight(rankedLights, rankedLightCount, lightIndex, score);

        if (isTorchLight(light.kind))
        {
            insertRankedLight(rankedTorchLights, rankedTorchLightCount, lightIndex, score);
        }
        else if (isStaticDetailLight(light.kind))
        {
            insertRankedLight(rankedStaticLights, rankedStaticLightCount, lightIndex, score);
        }
        else if (isFxLight(light.kind))
        {
            insertRankedLight(rankedFxLights, rankedFxLightCount, lightIndex, score);
        }
    }

    std::array<uint32_t, MaxIndoorDrawLights> selectedLightIndices = {};
    size_t selectedLightCount = 0;

    selectRankedLightsUpToBudget(
        selectedLightIndices,
        selectedLightCount,
        rankedTorchLights,
        rankedTorchLightCount,
        MaxIndoorTorchLightsPerDraw);
    selectRankedLightsUpToBudget(
        selectedLightIndices,
        selectedLightCount,
        rankedFxLights,
        rankedFxLightCount,
        MaxIndoorFxLightsPerDraw);
    selectRankedLightsUpToBudget(
        selectedLightIndices,
        selectedLightCount,
        rankedStaticLights,
        rankedStaticLightCount,
        MaxIndoorStaticLightsPerDraw);
    selectRankedLightsUpToBudget(
        selectedLightIndices,
        selectedLightCount,
        rankedLights,
        rankedLightCount,
        MaxIndoorDrawLights);

    std::array<float, 3> approximateRgb = {0.0f, 0.0f, 0.0f};
    uint32_t omittedTailLightCount = 0;

    for (size_t candidateIndex = 0; candidateIndex < touchingLightIndices.size(); ++candidateIndex)
    {
        const uint32_t lightIndex = touchingLightIndices.at(candidateIndex);

        if (lightIndex >= frame.lights.size()
            || selectedLightContains(selectedLightIndices, selectedLightCount, lightIndex))
        {
            continue;
        }

        ++omittedTailLightCount;
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
    if (pStats != nullptr)
    {
        recordLightingSelection(
            *pStats,
            static_cast<uint32_t>(candidateLightIndices.size()),
            static_cast<uint32_t>(selectedLightCount),
            omittedTailLightCount);
    }
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
    const DecorationBillboardSet *pDecorationBillboardSet,
    const EventRuntimeState *pState,
    const std::vector<int16_t> &mapLightSectors)
{
    StaticLightCache cache = {};
    cache.lightRevision = pState != nullptr ? pState->indoorLightRevision : 0;
    cache.sourceIndicesBySector.resize(mapData.sectors.size());
    const std::vector<size_t> decorationDecorVarIndices =
        buildIndoorInteractiveDecorationDecorVarIndices(mapData, pDecorationBillboardSet);

    const auto appendCachedLight =
        [&cache](const CachedLightSource &source)
        {
            if (source.radius <= 0.0f || source.intensity <= 0.0f)
            {
                return;
            }

            cache.sources.push_back(source);
        };

    // One source per map light, in the sector it stands in (MM6 maps list most lights in most sectors; the lights a
    // room receives are its reach, assignReach).
    // The first sector listing each light (-1: unlisted), its sector when mapLightSectors has none.
    std::vector<int16_t> listed(mapData.lights.size(), -1);
    for (size_t sectorId = 0; sectorId < mapData.sectors.size(); ++sectorId)
    {
        for (const uint16_t lightId : mapData.sectors[sectorId].lightIds)
        {
            if (lightId < listed.size() && listed[lightId] < 0)
            {
                listed[lightId] = int16_t(sectorId);
            }
        }
    }
    for (size_t lightId = 0; lightId < mapData.lights.size(); ++lightId)
    {
        const IndoorLight &source = mapData.lights[lightId];

        if (listed[lightId] < 0 || source.radius <= 0
            || (pDecorationBillboardSet != nullptr && pDecorationBillboardSet->mapLightReplaced(lightId)))
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
        light.sectorId = lightId < mapLightSectors.size() && mapLightSectors[lightId] >= 0 ? mapLightSectors[lightId]
                                                                                          : listed[lightId];
        light.kind = IndoorRenderLightKind::Static;
        light.sourceAttributes = static_cast<uint32_t>(source.attributes);
        light.sourceLightId = lightId;
        appendCachedLight(light);
    }

    if (pDecorationBillboardSet != nullptr)
    {
        for (const DecorationBillboard &billboard : pDecorationBillboardSet->billboards)
        {
            const DecorationEntry *pDecoration = pDecorationBillboardSet->decorationTable.get(billboard.decorationId);

            if (pDecoration == nullptr || billboard.litByMapLight)
            {
                continue;
            }

            pDecoration = runtimeDecorationEntry(
                pDecorationBillboardSet->decorationTable, *pDecoration, billboard.spriteOverrideKey(), pState);
            if (pDecoration == nullptr)
            {
                continue;
            }

            const SpriteFrameEntry *pFrame =
                pDecorationBillboardSet->spriteFrameTable.getFrame(pDecoration->spriteId, 0);
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
            light.runtimeOverrideKey = billboard.spriteOverrideKey();

            if (billboard.entityIndex < mapData.entities.size()
                && billboard.entityIndex < decorationDecorVarIndices.size())
            {
                const size_t decorVarIndex = decorationDecorVarIndices[billboard.entityIndex];

                if (decorVarIndex != InvalidDecorationDecorVarIndex)
                {
                    const IndoorEntity &entity = mapData.entities[billboard.entityIndex];
                    const std::optional<InteractiveDecorationBindingSpec> bindingSpec =
                        resolveInteractiveDecorationBindingSpec(*pDecoration, entity.name);

                    if (bindingSpec && bindingSpec->hideWhenCleared)
                    {
                        light.decorationDecorVarIndex = decorVarIndex;
                        light.decorationClearedState = bindingSpec->eventCount;
                        light.hideDecorationWhenCleared = true;
                    }
                }
            }

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
    const DecorationBillboardSet *pDecorationBillboardSet,
    const EventRuntimeState *pState)
{
    m_lightReach.build(mapData, buildIndoorPortalGraph(mapData));
    // Each map light's own sector: where it stands, else the first sector listing it.
    m_mapLightSectors.assign(mapData.lights.size(), -1);
    for (size_t sectorId = 0; sectorId < mapData.sectors.size(); ++sectorId)
    {
        for (const uint16_t lightId : mapData.sectors[sectorId].lightIds)
        {
            if (lightId < m_mapLightSectors.size() && m_mapLightSectors[lightId] < 0)
            {
                m_mapLightSectors[lightId] = int16_t(sectorId);
            }
        }
    }
    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    for (size_t lightId = 0; lightId < mapData.lights.size(); ++lightId)
    {
        const IndoorLight &light = mapData.lights[lightId];
        if (const std::optional<int16_t> sector = findIndoorSectorForPoint(mapData, mapData.vertices,
                {float(light.x), float(light.y), float(light.z)}, &geometryCache, false))
        {
            m_mapLightSectors[lightId] = *sector;
        }
    }
    m_pulsingLightSectors.clear();
    for (const IndoorPulsingLight &light : mapData.pulsingLights)
    {
        m_pulsingLightSectors.push_back(findIndoorSectorForPoint(mapData, mapData.vertices,
            {light.position[0], light.position[1], light.position[2]}, &geometryCache, false).value_or(-1));
    }
    m_staticLightCache = buildStaticCache(mapData, pDecorationBillboardSet, pState, m_mapLightSectors);
    assignReach(m_staticLightCache);
}

void IndoorLightingRuntime::clearStaticCache()
{
    m_staticLightCache = {};
    m_lightReach.clear();
}

void IndoorLightingRuntime::assignReach(StaticLightCache &cache) const
{
    // A source is a candidate wherever one of the sectors it reaches is visible; without a reach list, in its own.
    std::vector<int16_t> reached;
    for (uint32_t sourceIndex = 0; sourceIndex < cache.sources.size(); ++sourceIndex)
    {
        CachedLightSource &source = cache.sources[sourceIndex];
        m_lightReach.reach(std::span<const int16_t>(&source.sectorId, 1), source.position, source.radius, reached);
        source.reach.assign(reached);
        if (source.reach.count == 0)
        {
            reached.assign(1, source.sectorId);
        }
        for (const int16_t sector : reached)
        {
            if (sector >= 0 && size_t(sector) < cache.sourceIndicesBySector.size())
            {
                cache.sourceIndicesBySector[size_t(sector)].push_back(sourceIndex);
            }
        }
    }
}

IndoorLightingFrame IndoorLightingRuntime::buildFrame(const IndoorLightingFrameInput &input) const
{
    IndoorLightingFrame frame = {};
    frame.ambient = ambientFromMinAmbientLightLevel(0);
    frame.indoorLightRevision = input.pEventRuntimeState != nullptr ? input.pEventRuntimeState->indoorLightRevision : 0;
    frame.coloredLights = input.coloredLights;

    if (input.pMapData != nullptr)
    {
        frame.lightIndicesBySector.resize(input.pMapData->sectors.size());
        frame.dynamicLightIndicesBySector.resize(input.pMapData->sectors.size());
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
                sectorAmbientLevel(*input.pMapData, input.pEventRuntimeState, sectorId);
            maxAmbientLightLevel = std::max(maxAmbientLightLevel, sectorAmbientLightLevel);
        }

        frame.ambient = ambientFromMinAmbientLightLevel(maxAmbientLightLevel);
        frame.sectorAmbient.resize(input.pMapData->sectors.size());
        for (size_t sectorId = 0; sectorId < input.pMapData->sectors.size(); ++sectorId)
        {
            frame.sectorAmbient[sectorId] =
                ambientFromMinAmbientLightLevel(
                    sectorAmbientLevel(*input.pMapData, input.pEventRuntimeState, sectorId));
        }
    }

    if (input.pParty != nullptr)
    {
        if (const std::optional<GameplayTorchLight> torchLight =
                resolveGameplayTorchLight(*input.pParty, false, 1.0f, input.warmTorchLight))
        {
            IndoorRenderLight torch = {};
            torch.position = input.cameraPosition;
            torch.radius = torchLight->radius;
            torch.colorAbgr = torchLight->colorAbgr;
            torch.intensity = torchLight->intensity * IndoorTorchLightIntensityScale;
            torch.kind = IndoorRenderLightKind::Torch;
            torch.stableId = 0x746f7263u;
            appendFrameLight(frame, torch, true);
        }
    }

    if (input.pWorldFxSystem != nullptr)
    {
        std::vector<RenderLight> fxLights;
        fxLights.reserve(input.pWorldFxSystem->lightEmitters().size());

        for (const WorldFxLightEmitter &emitter : input.pWorldFxSystem->lightEmitters())
        {
            const bx::Vec3 lightPosition = {emitter.x, emitter.y, emitter.z};

            if (!sectorVisible(input.pVisibleSectorMask, emitter.sectorId)
                || (emitter.sectorId >= 0
                    && !sphereIntersectsVisibleSectorFrustums(
                        input.pVisibleSectorFrustums,
                        emitter.sectorId,
                        lightPosition,
                        emitter.radius)))
            {
                continue;
            }

            RenderLight light = {};
            light.position = lightPosition;
            light.radius = emitter.radius;
            light.colorAbgr =
                emitter.colorAbgr != 0
                    ? emitter.colorAbgr
                    : makeAbgr(255, 255, 255, FxLightAlphaFallback);
            light.intensity = emitter.intensity;
            light.sectorId = emitter.sectorId;
            light.kind = emitter.kind;
            light.stableId = emitter.stableId;
            light.dynamic = true;
            light.important = emitter.important;
            fxLights.push_back(light);
        }

        FxLightClusterConfig clusterConfig = {};
        clusterConfig.cellSize = IndoorFxClusterCellSize;
        clusterConfig.thresholdPerSector = input.fxClusterThreshold;
        clusterConfig.maxClustersPerSector = input.fxClusterThreshold;
        clusterConfig.maxRadius = MaxIndoorFxClusterRadius;
        clusterConfig.maxIntensity = MaxIndoorFxClusterIntensity;
        clusterConfig.allowSectorlessLights = true;
        const FxLightClusterResult clusteredLights =
            FxLightClustering::clusterSectorFxLights(fxLights, clusterConfig);
        frame.sourceFxLightCount = static_cast<uint32_t>(fxLights.size());
        frame.clusteredFxLightCount = clusteredLights.outputClusterLights;

        std::vector<int16_t> reached;
        for (const RenderLight &sourceLight : clusteredLights.lights)
        {
            IndoorRenderLight light = indoorLightFromRenderLight(sourceLight);
            m_lightReach.reach(std::span<const int16_t>(&light.sectorId, 1), light.position, light.radius, reached);
            light.reach.assign(reached);
            appendFrameLight(frame, light, false);
        }
    }

    // Scene pulsing lights (MM9's GlowingLight): dynamic lights whose intensity and radius follow their sines.
    if (input.pMapData != nullptr && m_pulsingLightSectors.size() == input.pMapData->pulsingLights.size())
    {
        const auto wave = [&input](const std::array<float, 4> &curve)
        {
            const float cycles = curve[2] * input.timeSeconds + curve[3];
            const float blend = 0.5f + 0.5f * std::sin(cycles * 2.0f * bx::kPi);
            return curve[0] + (curve[1] - curve[0]) * blend;
        };
        std::vector<int16_t> reached;

        for (size_t index = 0; index < input.pMapData->pulsingLights.size(); ++index)
        {
            const IndoorPulsingLight &source = input.pMapData->pulsingLights[index];
            const int16_t sectorId = m_pulsingLightSectors[index];
            bool enabled = source.startOn;

            if (input.pEventRuntimeState != nullptr)
            {
                const auto stateIt = input.pEventRuntimeState->indoorLightsEnabled.find(source.lightKey);
                enabled = stateIt != input.pEventRuntimeState->indoorLightsEnabled.end() ? stateIt->second : enabled;
            }

            if (!enabled || sectorId < 0)
            {
                continue;
            }

            IndoorRenderLight light = {};
            light.position = {source.position[0], source.position[1], source.position[2]};
            light.radius = wave(source.radius);
            light.intensity = wave(source.intensity);
            light.colorAbgr = makeAbgr(source.color[0], source.color[1], source.color[2], 255);
            light.sectorId = sectorId;
            light.kind = IndoorRenderLightKind::Fx;
            light.stableId = 0x706c0000u + source.lightKey;
            m_lightReach.reach(std::span<const int16_t>(&light.sectorId, 1), light.position, light.radius, reached);
            // drawn when a room it reaches is in view
            if (!std::any_of(reached.begin(), reached.end(),
                    [&input](int16_t reachedSector)
                    {
                        return reachedSector >= 0 && sectorVisible(input.pVisibleSectorMask, size_t(reachedSector));
                    })
                && !sectorVisible(input.pVisibleSectorMask, size_t(sectorId)))
            {
                continue;
            }

            light.reach.assign(reached);
            appendFrameLight(frame, light, false);
        }
    }

    if (input.pMapData != nullptr
        && (!m_staticLightCache.valid || m_staticLightCache.lightRevision != frame.indoorLightRevision))
    {
        m_staticLightCache = buildStaticCache(
            *input.pMapData, input.pDecorationBillboardSet, input.pEventRuntimeState, m_mapLightSectors);
        assignReach(m_staticLightCache);
    }
    const StaticLightCache *pStaticCache = &m_staticLightCache;

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

                if (source.radius <= 0.0f || source.intensity <= 0.0f)
                {
                    return;
                }

                if (source.kind == IndoorRenderLightKind::Static
                    && !isBlvLightEnabledByState(
                        source.sourceAttributes,
                        input.pEventRuntimeState,
                        source.sourceLightId))
                {
                    return;
                }

                if (source.kind == IndoorRenderLightKind::Decoration && input.pEventRuntimeState != nullptr)
                {
                    const auto iterator = input.pEventRuntimeState->spriteOverrides.find(source.runtimeOverrideKey);

                    if (iterator != input.pEventRuntimeState->spriteOverrides.end() && iterator->second.hidden)
                    {
                        return;
                    }
                }

                if (source.kind == IndoorRenderLightKind::Decoration
                    && source.hideDecorationWhenCleared
                    && input.pEventRuntimeState != nullptr
                    && source.decorationDecorVarIndex < input.pEventRuntimeState->decorVars.size()
                    && input.pEventRuntimeState->decorVars[source.decorationDecorVarIndex]
                        == source.decorationClearedState)
                {
                    return;
                }

                // Seen through the portals of any room it reaches.
                bool seen = source.reach.count == 0
                    && sphereIntersectsVisibleSectorFrustums(
                        input.pVisibleSectorFrustums, source.sectorId, source.position, source.radius);
                for (uint8_t entry = 0; entry < source.reach.count && !seen; ++entry)
                {
                    seen = sphereIntersectsVisibleSectorFrustums(
                        input.pVisibleSectorFrustums, source.reach.sectors[entry], source.position, source.radius);
                }
                // Without occlusion (scene model_lighting): in the view of any visible room.
                for (size_t sectorId = 0; input.lightsIgnoreReach && input.pVisibleSectorFrustums != nullptr && !seen
                    && sectorId < input.pVisibleSectorFrustums->size(); ++sectorId)
                {
                    seen = !(*input.pVisibleSectorFrustums)[sectorId].empty() && sphereIntersectsVisibleSectorFrustums(
                        input.pVisibleSectorFrustums, int16_t(sectorId), source.position, source.radius);
                }
                if (!seen)
                {
                    return;
                }

                IndoorRenderLight light = {};
                light.position = source.position;
                light.radius = source.radius;
                light.colorAbgr =
                    lightColorAbgr(source.red, source.green, source.blue, source.alpha, input.coloredLights);
                light.intensity = source.intensity;
                light.sectorId = source.sectorId;
                light.kind = source.kind;
                light.reach = source.reach;
                light.stableId =
                    source.kind == IndoorRenderLightKind::Static
                        ? static_cast<uint32_t>(source.sourceLightId + 1)
                        : source.runtimeOverrideKey;
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
