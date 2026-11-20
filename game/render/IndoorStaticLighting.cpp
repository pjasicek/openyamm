#include "game/render/IndoorStaticLighting.h"

#include "game/events/EventRuntime.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapAssetLoader.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
float bakedDecorationLightRadius(
    const DecorationBillboardSet &billboardSet,
    const DecorationEntry &decoration)
{
    float radius = 0.0f;

    if (decoration.lightRadius > 0)
    {
        radius = static_cast<float>(decoration.lightRadius);
    }

    const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(decoration.spriteId, 0);

    if (pFrame != nullptr && pFrame->glowRadius > 0)
    {
        radius = std::max(radius, static_cast<float>(pFrame->glowRadius));
    }

    return radius;
}
}

std::optional<BakedStaticLightSource> bakedStaticLightSourceForDecoration(
    const DecorationBillboardSet &billboardSet,
    const DecorationBillboard &billboard,
    const EventRuntimeState *pEventRuntimeState,
    bool includeInactiveSources)
{
    const DecorationEntry *decoration = billboardSet.decorationTable.get(billboard.decorationId);
    if (decoration == nullptr || billboard.litByMapLight) return std::nullopt;
    decoration = runtimeDecorationEntry(
        billboardSet.decorationTable, *decoration, billboard.spriteOverrideKey(),
        includeInactiveSources ? nullptr : pEventRuntimeState);
    if (decoration == nullptr) return std::nullopt;

    float radius = bakedDecorationLightRadius(billboardSet, *decoration);
    if (includeInactiveSources)
    {
        // Subdivide for both toggle states once, so lighting changes only refresh vertex colours.
        if (const DecorationEntry *counterpart =
                toggleableDecorationCounterpart(billboardSet.decorationTable, *decoration))
        {
            const float alternateRadius = bakedDecorationLightRadius(billboardSet, *counterpart);
            if (alternateRadius > radius)
            {
                radius = alternateRadius;
                decoration = counterpart;
            }
        }
    }
    if (radius <= 0.0f) return std::nullopt;

    BakedStaticLightSource source = {};
    source.position = {
        static_cast<float>(billboard.x), static_cast<float>(billboard.y),
        static_cast<float>(billboard.z) + static_cast<float>(std::max<uint16_t>(billboard.height, 1)) * 0.5f
    };
    source.radius = radius;
    source.alpha = 208.0f / 255.0f;
    if (decoration->lightRed != 0 || decoration->lightGreen != 0 || decoration->lightBlue != 0)
    {
        source.red = decoration->lightRed;
        source.green = decoration->lightGreen;
        source.blue = decoration->lightBlue;
    }
    return source;
}

BakedStaticLightSource bakedStaticLightSourceForIndoorLight(const IndoorMapData &indoorMapData, size_t lightId)
{
    const IndoorLight &light = indoorMapData.lights[lightId];
    BakedStaticLightSource source = {};
    source.position = {
        static_cast<float>(light.x),
        static_cast<float>(light.y),
        static_cast<float>(light.z)
    };
    source.radius = static_cast<float>(light.radius);
    source.red = light.red;
    source.green = light.green;
    source.blue = light.blue;
    source.alpha = static_cast<float>(IndoorBakedStaticLightAlpha) / 255.0f;
    source.sourceId = uint32_t(lightId);
    source.openAir = indoorOpenAirLight(indoorMapData.daylight, lightId);
    return source;
}

std::vector<BakedStaticLightSource> buildBakedStaticLightSources(
    const IndoorMapData &indoorMapData,
    const EventRuntimeState *pEventRuntimeState,
    const DecorationBillboardSet *pDecorationBillboardSet,
    bool includeInactiveSources)
{
    std::vector<BakedStaticLightSource> sources;
    sources.reserve(indoorMapData.lights.size()
        + (pDecorationBillboardSet != nullptr ? pDecorationBillboardSet->billboards.size() : 0));

    for (size_t lightId = 0; lightId < indoorMapData.lights.size(); ++lightId)
    {
        const IndoorLight &light = indoorMapData.lights[lightId];

        if (light.radius <= 0
            || (pDecorationBillboardSet != nullptr && pDecorationBillboardSet->mapLightReplaced(lightId))
            || (!includeInactiveSources
                && !IndoorLightingRuntime::isBlvLightEnabledByState(
                    static_cast<uint32_t>(light.attributes),
                    pEventRuntimeState,
                    lightId)))
        {
            continue;
        }

        sources.push_back(bakedStaticLightSourceForIndoorLight(indoorMapData, lightId));
    }

    if (pDecorationBillboardSet == nullptr)
    {
        return sources;
    }

    for (size_t index = 0; index < pDecorationBillboardSet->billboards.size(); ++index)
    {
        if (auto source = bakedStaticLightSourceForDecoration(
                *pDecorationBillboardSet, pDecorationBillboardSet->billboards[index], pEventRuntimeState,
                includeInactiveSources))
        {
            source->sourceId = uint32_t(indoorMapData.lights.size() + index);
            sources.push_back(*source);
        }
    }

    return sources;
}
}
