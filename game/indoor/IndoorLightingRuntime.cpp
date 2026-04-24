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
#include <unordered_set>

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

bool decorationHidden(const EventRuntimeState *pState, const DecorationBillboard &billboard)
{
    if (pState == nullptr)
    {
        return false;
    }

    const uint32_t overrideKey =
        billboard.eventIdPrimary != 0 ? billboard.eventIdPrimary : billboard.eventIdSecondary;

    if (overrideKey == 0)
    {
        return false;
    }

    const auto iterator = pState->spriteOverrides.find(overrideKey);

    return iterator != pState->spriteOverrides.end() && iterator->second.hidden;
}

void appendRankedLight(
    std::vector<IndoorRenderLight> &lights,
    const IndoorRenderLight &light)
{
    if (light.radius <= 0.0f || light.intensity <= 0.0f)
    {
        return;
    }

    lights.push_back(light);
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

    for (const IndoorRenderLight &light : frame.lights)
    {
        if (light.radius <= 1.0f)
        {
            continue;
        }

        const float distance = std::sqrt(distanceSquared(light.position, position));
        const float ratio = std::clamp(distance / light.radius, 0.0f, 1.0f);
        float attenuation = 1.0f - ratio * ratio;
        attenuation *= attenuation;
        attenuation *= light.intensity * IndoorLightScale;

        rgb[0] += redChannel(light.colorAbgr) * alphaChannel(light.colorAbgr) * attenuation;
        rgb[1] += greenChannel(light.colorAbgr) * alphaChannel(light.colorAbgr) * attenuation;
        rgb[2] += blueChannel(light.colorAbgr) * alphaChannel(light.colorAbgr) * attenuation;
    }

    rgb[0] = std::clamp(rgb[0], 0.0f, 2.0f);
    rgb[1] = std::clamp(rgb[1], 0.0f, 2.0f);
    rgb[2] = std::clamp(rgb[2], 0.0f, 2.0f);
    return rgb;
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

IndoorLightingFrame IndoorLightingRuntime::buildFrame(const IndoorLightingFrameInput &input) const
{
    IndoorLightingFrame frame = {};
    frame.ambient = ambientFromMinAmbientLightLevel(0);

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

    std::vector<IndoorRenderLight> candidates;
    candidates.reserve(MaxIndoorRenderLights * 4);

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
            appendRankedLight(frame.lights, torch);
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
            light.kind = IndoorRenderLightKind::Fx;
            appendRankedLight(candidates, light);
        }
    }

    if (input.pMapData != nullptr)
    {
        std::unordered_set<size_t> appendedLightIds;

        for (size_t sectorId = 0; sectorId < input.pMapData->sectors.size(); ++sectorId)
        {
            if (!sectorVisible(input.pVisibleSectorMask, sectorId))
            {
                continue;
            }

            const IndoorSector &sector = input.pMapData->sectors[sectorId];

            for (uint16_t lightId : sector.lightIds)
            {
                if (lightId >= input.pMapData->lights.size() || appendedLightIds.count(lightId) != 0)
                {
                    continue;
                }

                const IndoorLight &source = input.pMapData->lights[lightId];

                if (source.radius <= 0
                    || !isBlvLightEnabledByState(
                        static_cast<uint32_t>(source.attributes),
                        input.pEventRuntimeState,
                        lightId))
                {
                    continue;
                }

                IndoorRenderLight light = {};
                light.position = {
                    static_cast<float>(source.x),
                    static_cast<float>(source.y),
                    static_cast<float>(source.z)
                };
                light.radius = static_cast<float>(source.radius);
                light.colorAbgr =
                    lightColorAbgr(source.red, source.green, source.blue, DefaultLightAlpha, input.coloredLights);
                light.intensity = 1.0f;
                light.sectorId = static_cast<int16_t>(sectorId);
                light.kind = IndoorRenderLightKind::Static;
                appendRankedLight(candidates, light);
                appendedLightIds.insert(lightId);
            }
        }
    }

    if (input.pDecorationBillboardSet != nullptr)
    {
        for (const DecorationBillboard &billboard : input.pDecorationBillboardSet->billboards)
        {
            if (!sectorVisible(input.pVisibleSectorMask, billboard.sectorId))
            {
                continue;
            }

            if (decorationHidden(input.pEventRuntimeState, billboard))
            {
                continue;
            }

            const DecorationEntry *pDecoration =
                input.pDecorationBillboardSet->decorationTable.get(billboard.decorationId);

            if (pDecoration == nullptr)
            {
                continue;
            }

            const SpriteFrameEntry *pFrame =
                input.pDecorationBillboardSet->spriteFrameTable.getFrame(billboard.spriteId, 0);

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

            uint8_t red = 255;
            uint8_t green = 255;
            uint8_t blue = 255;

            if (pDecoration->lightRed != 0 || pDecoration->lightGreen != 0 || pDecoration->lightBlue != 0)
            {
                red = pDecoration->lightRed;
                green = pDecoration->lightGreen;
                blue = pDecoration->lightBlue;
            }

            IndoorRenderLight light = {};
            light.position = {
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z) + static_cast<float>(std::max<uint16_t>(billboard.height, 1)) * 0.5f
            };
            light.radius = radius;
            light.colorAbgr = lightColorAbgr(red, green, blue, 208, input.coloredLights);
            light.intensity = 1.0f;
            light.sectorId = billboard.sectorId;
            light.kind = IndoorRenderLightKind::Decoration;
            appendRankedLight(candidates, light);
        }
    }

    std::sort(
        candidates.begin(),
        candidates.end(),
        [&input](const IndoorRenderLight &left, const IndoorRenderLight &right)
        {
            const float leftDistance =
                std::max(std::sqrt(distanceSquared(left.position, input.cameraPosition)), 1.0f);
            const float rightDistance =
                std::max(std::sqrt(distanceSquared(right.position, input.cameraPosition)), 1.0f);
            const float leftScore = left.radius * left.intensity / leftDistance;
            const float rightScore = right.radius * right.intensity / rightDistance;
            return leftScore > rightScore;
        });

    for (const IndoorRenderLight &candidate : candidates)
    {
        if (frame.lights.size() >= MaxIndoorRenderLights)
        {
            break;
        }

        frame.lights.push_back(candidate);
    }

    return frame;
}
}
