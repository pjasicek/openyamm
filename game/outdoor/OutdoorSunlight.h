#pragma once

#include "game/app/GameSettings.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorWorldRuntime.h"

#include <algorithm>
#include <array>

namespace OpenYAMM::Game
{
// XYZ points toward the sun, scaled by direct intensity; W is the ambient share of base illumination.
inline std::array<float, 4> buildOutdoorSunlight(
    const OutdoorMapData &mapData,
    const OutdoorWorldRuntime::AtmosphereState &atmosphere)
{
    if (mapData.sceneProfile != OutdoorSceneProfile::ClassicOdm
        || mapData.locationType != OutdoorLocationType::Exterior || mapData.lightingData || atmosphere.underwater)
    {
        return {0.0f, 0.0f, 0.0f, 1.0f};
    }

    // The atmosphere owns the clock, forced-light/dark flags, sun direction and twilight state.
    const float ambient = std::clamp(atmosphere.ambientBrightness, 0.0f, 1.0f);
    const float daylight = atmosphere.isNight ? 0.0f : 1.0f - std::clamp(atmosphere.fogDensity, 0.0f, 1.0f);
    const float intensity = (ambient + 0.3f) * daylight;
    return {
        atmosphere.sunDirectionX * intensity,
        atmosphere.sunDirectionY * intensity,
        atmosphere.sunDirectionZ * intensity,
        ambient
    };
}

inline std::array<float, 4> outdoorBakedLightingWeights(const OutdoorWorldRuntime::AtmosphereState &atmosphere)
{
    const float daylight = atmosphere.isNight ? 0.0f
        : std::clamp((atmosphere.ambientBrightness - 0.15f) / 0.54f, 0.0f, 1.0f)
            * (1.0f - std::clamp(atmosphere.fogDensity, 0.0f, 1.0f));
    return {daylight, 0.12f + 0.88f * daylight, 0.0f, 0.0f};
}

// Two vec4s match u_bakedLighting[2]. Shared by surface shaders and CPU sprite-probe evaluation.
inline std::array<std::array<float, 4>, 2> outdoorBakedLightingColors(
    const OutdoorWorldRuntime::AtmosphereState &atmosphere, const GameSettings &settings)
{
    const std::array<float, 4> weights = outdoorBakedLightingWeights(atmosphere);
    std::array<std::array<float, 4>, 2> colors = {};
    for (size_t channel = 0; channel < 3; ++channel)
    {
        colors[0][channel] = weights[0] * settings.bakedSunStrength * settings.bakedSunColor[channel];
        colors[1][channel] = weights[1] * settings.bakedSkyStrength * settings.bakedSkyColor[channel];
    }
    return colors;
}

inline float outdoorBillboardBaseLight(const std::array<float, 4> &sunlight)
{
    // A billboard has no fixed world-space facing. Use the horizontal-ground response for its base light.
    // Neutral/excluded worlds retain the existing 0.85 billboard base.
    return std::clamp(sunlight[3] + std::max(sunlight[2], 0.0f), 0.0f, 0.85f);
}
}
