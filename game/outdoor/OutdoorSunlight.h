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
    const OutdoorWorldRuntime::AtmosphereState &atmosphere,
    bool lightingDataEnabled = true)
{
    if (mapData.sceneProfile != OutdoorSceneProfile::ClassicOdm
        || mapData.locationType != OutdoorLocationType::Exterior
        || (lightingDataEnabled && mapData.lightingData) || atmosphere.underwater)
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

// Enhanced sky hue for the baked sun and sky terms. Both tints are normalised to unit luminance so only the hue moves;
// day/night brightness stays with outdoorBakedLightingWeights.
inline void applyOutdoorBakedLightingTint(std::array<std::array<float, 4>, 2> &colors,
    const std::array<float, 3> &sunTint, const std::array<float, 3> &skyTint)
{
    const auto normalised = [](const std::array<float, 3> &tint)
    {
        const float luminance = std::max(0.2126f * tint[0] + 0.7152f * tint[1] + 0.0722f * tint[2], 0.001f);
        return std::array<float, 3>{tint[0] / luminance, tint[1] / luminance, tint[2] / luminance};
    };
    const std::array<float, 3> sun = normalised(sunTint);
    const std::array<float, 3> sky = normalised(skyTint);

    for (size_t channel = 0; channel < 3; ++channel)
    {
        colors[0][channel] *= sun[channel];
        colors[1][channel] *= sky[channel];
    }
}

// Rain clouds hide the sun and dim the sky light; a lightning flash lights everything for a moment.
inline void applyOutdoorWeatherLighting(std::array<std::array<float, 4>, 2> &colors, float rainCloudCover,
    float lightningFlash)
{
    const float cloud = std::clamp(rainCloudCover, 0.0f, 1.0f);
    const float flash = std::clamp(lightningFlash, 0.0f, 1.0f);

    for (size_t channel = 0; channel < 3; ++channel)
    {
        colors[0][channel] *= 1.0f - 0.7f * cloud;
        colors[1][channel] = colors[1][channel] * (1.0f - 0.25f * cloud) + 1.4f * flash;
    }
}

inline float outdoorBillboardBaseLight(const std::array<float, 4> &sunlight)
{
    // A billboard has no fixed world-space facing. Use the horizontal-ground response for its base light.
    // Neutral/excluded worlds retain the existing 0.85 billboard base.
    return std::clamp(sunlight[3] + std::max(sunlight[2], 0.0f), 0.0f, 0.85f);
}
}
