#pragma once

#include "game/app/GameSettings.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorWorldRuntime.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <optional>

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

// Unit bake sun direction from the recipe profile, using the producer's convention.
inline std::optional<bx::Vec3> surfaceMaterialBakeSunDirection(float azimuthDegrees, float elevationDegrees)
{
    const float azimuth = azimuthDegrees * (3.14159265358979323846f / 180.0f);
    const float elevation = elevationDegrees * (3.14159265358979323846f / 180.0f);
    const bx::Vec3 direction = {
        std::cos(elevation) * std::cos(azimuth),
        std::cos(elevation) * std::sin(azimuth),
        std::sin(elevation)
    };
    const float length = std::sqrt(
        direction.x * direction.x + direction.y * direction.y + direction.z * direction.z);

    if (!std::isfinite(length) || length <= 0.0001f)
    {
        return std::nullopt;
    }

    return bx::Vec3{direction.x / length, direction.y / length, direction.z / length};
}

struct OutdoorMaterialSunInputs
{
    bx::Vec3 direction = {0.0f, 0.0f, 0.0f};
    std::array<float, 3> color = {0.0f, 0.0f, 0.0f};
    bool enabled = false;
};

// Separate material sun inputs: u_outdoorSunlight deliberately zeroes direct light whenever baked
// lighting exists, so it is never a usable sheen direction. Baked exteriors use the fixed bake
// direction weighted by the sampled sun source; nonbaked and lightmaps-off exteriors use the
// atmosphere direction and daylight gating; everything else carries no directional sheen.
inline OutdoorMaterialSunInputs buildOutdoorMaterialSunInputs(
    const OutdoorMapData &mapData,
    const OutdoorWorldRuntime::AtmosphereState &atmosphere,
    const GameSettings &settings,
    bool hasBakeSunDirection,
    const bx::Vec3 &bakeSunDirection)
{
    OutdoorMaterialSunInputs inputs = {};

    if (mapData.sceneProfile != OutdoorSceneProfile::ClassicOdm
        || mapData.locationType != OutdoorLocationType::Exterior
        || atmosphere.underwater)
    {
        return inputs;
    }

    if (mapData.lightingData && settings.lightmaps && mapData.lightingData->hasBakedSources()
        && hasBakeSunDirection)
    {
        const std::array<std::array<float, 4>, 2> colors = outdoorBakedLightingColors(atmosphere, settings);
        inputs.direction = bakeSunDirection;
        inputs.color = {colors[0][0], colors[0][1], colors[0][2]};
        inputs.enabled = true;
        return inputs;
    }

    const float ambient = std::clamp(atmosphere.ambientBrightness, 0.0f, 1.0f);
    const float daylight = atmosphere.isNight ? 0.0f : 1.0f - std::clamp(atmosphere.fogDensity, 0.0f, 1.0f);
    const float intensity = (ambient + 0.3f) * daylight;
    const bx::Vec3 sunDirection = {
        atmosphere.sunDirectionX,
        atmosphere.sunDirectionY,
        atmosphere.sunDirectionZ
    };
    const float length = std::sqrt(
        sunDirection.x * sunDirection.x + sunDirection.y * sunDirection.y
        + sunDirection.z * sunDirection.z);

    if (intensity <= 0.0f || !std::isfinite(length) || length <= 0.0001f)
    {
        return inputs;
    }

    inputs.direction = {sunDirection.x / length, sunDirection.y / length, sunDirection.z / length};
    inputs.color = {intensity, intensity, intensity};
    inputs.enabled = true;
    return inputs;
}
}
