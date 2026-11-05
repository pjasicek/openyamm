#pragma once

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
// A map's indoor fog (scene `fog`, devdocs/INDOOR_FOG.md): every world pixel fades linearly into one colour between
// two distances from the eye. Disabled on every map without the scene block.
struct IndoorFog
{
    bool enabled = false;
    std::array<float, 3> color = {0.0f, 0.0f, 0.0f};   // display space, 0..1
    float nearDistance = 0.0f;
    float farDistance = 0.0f;
    // Scene `model: lithtech`: MM9's fog. The distance is the view depth (camera-space z), and a face fades its
    // texture into the colour and its light into indoorFogLightPassColor, as MM9's two passes do. Off: the distance
    // from the eye and one fade of the lit colour.
    bool lithtech = false;
    // Scene `night`: the fog after dark (MM9's WeatherMan TurnOffAtNight switches to its FogOff state), taken by
    // indoorFogAt as the sky's night falls. Without it the day's fog stays at every hour.
    bool hasNight = false;
    std::array<float, 3> nightColor = {0.0f, 0.0f, 0.0f};
    float nightNearDistance = 0.0f;
    float nightFarDistance = 0.0f;
    // Scene `sky` (0..1, per state): how much of an open sky (devdocs/INDOOR_OPEN_SKY.md) is drawn as the fog colour.
    // MM9 fogs its sky box with SkyFogNearZ/FarZ whenever its fog is on, which leaves the box wholly in the fog colour
    // (devdocs/INDOOR_FOG.md "The sky in fog"). 0: the sky stays clear (every map without the key).
    float sky = 0.0f;
    float nightSky = 0.0f;
    // Scene `follow_daylight: true`: the colour (and so the fogged sky) darkens with the open air's light by the time
    // of day (indoorDaylightFogScale; 1 at noon). Only with the scene's `daylight` block.
    bool followsDaylight = false;
};

// The fog at a moment: the day's mixed into the night's by `night` (0..1, skyNightAmount); the fog itself when it has
// no night state.
inline IndoorFog indoorFogAt(const IndoorFog &fog, float night)
{
    if (!fog.enabled || !fog.hasNight)
    {
        return fog;
    }
    const float blend = std::clamp(night, 0.0f, 1.0f);
    IndoorFog result = fog;
    for (size_t channel = 0; channel < 3; ++channel)
    {
        result.color[channel] = fog.color[channel] + (fog.nightColor[channel] - fog.color[channel]) * blend;
    }
    result.nearDistance = fog.nearDistance + (fog.nightNearDistance - fog.nearDistance) * blend;
    result.farDistance = fog.farDistance + (fog.nightFarDistance - fog.farDistance) * blend;
    result.sky = fog.sky + (fog.nightSky - fog.sky) * blend;
    result.hasNight = false;
    return result;
}

// The colour MM9 fogs its lightmap pass into (d3d.ren 0x10009660, used at 0x100638d6): the fog byte i becomes
// 255 sqrt(i / 512), so 127 stays 127 and white becomes 179. Fully fogged, a lightmapped face shows colour x this.
inline std::array<float, 3> indoorFogLightPassColor(const std::array<float, 3> &color)
{
    std::array<float, 3> result = {};
    for (size_t channel = 0; channel < 3; ++channel)
    {
        // Both conversions truncate (d3d.ren converts with integer shifts).
        const float index = std::floor(std::clamp(color[channel], 0.0f, 1.0f) * 255.0f + 0.001f);
        result[channel] = std::min(std::floor(255.0f * std::sqrt(index / 512.0f)), 255.0f) / 255.0f;
    }
    return result;
}

// How much of the open sky this fog (a moment's, from indoorFogAt) draws in its colour: 0 without fog.
inline float indoorFogSkyCover(const IndoorFog &fog)
{
    return fog.enabled ? std::clamp(fog.sky, 0.0f, 1.0f) : 0.0f;
}

// How far a pixel `distance` units from the eye has faded into the fog colour: 0 up to near, 1 from far on.
inline float indoorFogRatio(const IndoorFog &fog, float distance)
{
    if (!fog.enabled)
    {
        return 0.0f;
    }
    return std::clamp((distance - fog.nearDistance) / std::max(fog.farDistance - fog.nearDistance, 1.0f), 0.0f, 1.0f);
}

// The fog as the billboard (u_fogColor, u_fogDensities, u_fogDistances) and model (u_modelFog) uniforms, whose shaders
// take a linear fog when the densities' w is 1. Disabled, these are the constants those draws always passed indoors.
inline std::array<float, 4> indoorFogColorUniform(const IndoorFog &fog)
{
    return fog.enabled ? std::array<float, 4>{fog.color[0], fog.color[1], fog.color[2], 1.0f}
                       : std::array<float, 4>{0.0f, 0.0f, 0.0f, 0.0f};
}

inline std::array<float, 4> indoorFogDensitiesUniform(const IndoorFog &fog)
{
    return {0.0f, 0.0f, 0.0f, fog.enabled ? 1.0f : 0.0f};
}

inline std::array<float, 4> indoorFogDistancesUniform(const IndoorFog &fog)
{
    return fog.enabled ? std::array<float, 4>{fog.nearDistance, fog.farDistance, fog.farDistance + 1.0f, 0.0f}
                       : std::array<float, 4>{4096.0f, 4096.0f, 4096.0f, 0.0f};
}

// The face programs' fog mode (u_indoorFogMode): x 1 = the distance is the view depth, y 1 = MM9's two-pass fade; and
// the light's fog colour (u_indoorFogLight). Both zero for the plain fog.
inline std::array<float, 4> indoorFogModeUniform(const IndoorFog &fog)
{
    return {fog.lithtech ? 1.0f : 0.0f, fog.lithtech ? 1.0f : 0.0f, 0.0f, 0.0f};
}

inline std::array<float, 4> indoorFogLightUniform(const IndoorFog &fog)
{
    if (!fog.lithtech)
    {
        return {0.0f, 0.0f, 0.0f, 0.0f};
    }
    const std::array<float, 3> light = indoorFogLightPassColor(fog.color);
    return {light[0], light[1], light[2], 0.0f};
}
}
