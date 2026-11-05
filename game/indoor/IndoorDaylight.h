#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorMapData;

// Scene `daylight` (devdocs/INDOOR_OPEN_SKY.md "Daylight"): the sun and sky light of an indoor map open to the sky (an
// MM9 city as a BLV) on its sectors open to the sky, by the game's time of day. Colours 0..1 (the scene's 0..255 /
// 255).
// Disabled on every map without the block: its faces, models and sprites light exactly as before.
struct IndoorDaylight
{
    bool enabled = false;
    // The open air's light in shade at noon (MM9 WorldInfo AmbientLight).
    std::array<float, 3> ambient = {0.0f, 0.0f, 0.0f};
    // The sun at full strength on a face turned toward it (MM9 StaticSunLight InnerColor x BrightScale).
    std::array<float, 3> sun = {0.0f, 0.0f, 0.0f};
    // Toward the sun, unit length (MM9's StaticSunLight, the direction its lightmaps were cooked with); none: the
    // Enhanced sky's moving sun (skySunDirection).
    std::optional<std::array<float, 3>> sunDirection;
    // How steeply a face takes the sun: min(1, gain x N.L). 1 is Lambert; MM9's lightmaps saturate on nearly every
    // unshadowed face turned toward their sun (N.L above about 0.05), which a gain of 4 approximates.
    float sunGain = 1.0f;
    // The whole daylight's scale at noon and at midnight (MM9 WorldProperties LightScale and NightLightScale).
    std::array<float, 3> dayScale = {1.0f, 1.0f, 1.0f};
    std::array<float, 3> nightScale = {1.0f, 1.0f, 1.0f};
    // 1 for each sector open to the sky (indoorOpenSkySectors), computed when the map loads.
    std::vector<uint8_t> sectors;
};

// The daylight at one moment, in the renderer's light units (1 = the texture as painted).
struct IndoorDaylightLight
{
    std::array<float, 3> ambient = {0.0f, 0.0f, 0.0f};
    std::array<float, 3> sun = {0.0f, 0.0f, 0.0f};
    // Toward the sun: the scene's sun_direction, else the Enhanced sky's sun (skySunDirection).
    std::array<float, 3> sunDirection = {0.0f, 0.0f, 1.0f};
    float sunGain = 1.0f;
};

// How much of the day's light there is: 1 at noon, 0 at midnight, 0.5 at 06:00 and 18:00. The outdoor maps' ambient
// curve (OutdoorWorldRuntime normalizedAmbientBrightness, normalised as outdoorBakedLightingWeights does).
float indoorDaylightWeight(float gameMinutes);

// The daylight at a game time: ambient x the scale (night to day by indoorDaylightWeight), the sun x the same scale x
// the weight, fading out as the sky's sun sets (skyNightAmount).
IndoorDaylightLight evaluateIndoorDaylight(const IndoorDaylight &daylight, float gameMinutes);

// How the fog's colour follows the daylight (scene fog `follow_daylight`): per channel, the open air's light at this
// game time over its light at noon, the light being indoorDaylightRoomLight's measure (ambient and half the sun, at
// most 1). 1 at noon; at midnight the night scale's share of the ambient. All 1 without daylight.
std::array<float, 3> indoorDaylightFogScale(const IndoorDaylight &daylight, float gameMinutes);

// The sky's hue on the daylight, as the outdoor bake takes it (applyOutdoorBakedLightingTint): each tint normalised to
// unit luminance, so only the hue moves.
void tintIndoorDaylight(IndoorDaylightLight &light, const std::array<float, 3> &sunTint,
    const std::array<float, 3> &skyTint);

// The room light of models, decorations and sprites in a sector open to the sky (one number, as a sector's ambient):
// the ambient's luminance and half the sun's (a standing figure has a lit and a shaded side), at most 1.
float indoorDaylightRoomLight(const IndoorDaylightLight &light);
// The ambient share alone (its luminance, at most 1): the light of a model's side turned away from the sun, when the
// model takes the sun by direction (IndoorRenderer: decorations and creatures in sectors open to the sky).
float indoorDaylightModelAmbient(const IndoorDaylightLight &light);

// Whether the sector takes the daylight: the map has daylight and the sector is open to the sky.
inline bool indoorDaylightSector(const IndoorDaylight &daylight, int sectorId)
{
    return daylight.enabled && sectorId >= 0 && size_t(sectorId) < daylight.sectors.size()
        && daylight.sectors[size_t(sectorId)] != 0;
}

// The sectors open to the sky: each sector whose IndoorSky faces cover at least a quarter of its floor area or 10 M
// square units (the sky shell over the city's air; not a house's skylight or a sliver of the shell), and every sector
// that reaches one of them down through a horizontal portal (a street room under its district's air over the roofs,
// through the roof line). Doorways and windows are vertical, so the rooms behind them stay closed.
std::vector<uint8_t> indoorOpenSkySectors(const IndoorMapData &mapData);
}
