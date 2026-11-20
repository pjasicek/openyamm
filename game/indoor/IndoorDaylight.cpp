#include "game/indoor/IndoorDaylight.h"

#include "game/indoor/IndoorMapData.h"
#include "game/render/SkyState.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;

float luminance(const std::array<float, 3> &rgb)
{
    return 0.2126f * rgb[0] + 0.7152f * rgb[1] + 0.0722f * rgb[2];
}
}

float indoorDaylightWeight(float gameMinutes)
{
    const float minute = std::fmod(std::fmod(gameMinutes, 1440.0f) + 1440.0f, 1440.0f);
    return std::clamp(0.5f + 0.5f * std::sin((minute - 360.0f) * 2.0f * Pi / 1440.0f), 0.0f, 1.0f);
}

IndoorDaylightLight evaluateIndoorDaylight(const IndoorDaylight &daylight, float gameMinutes)
{
    IndoorDaylightLight light = {};
    if (!daylight.enabled)
    {
        return light;
    }

    const float day = indoorDaylightWeight(gameMinutes);
    const float sunUp = 1.0f - skyNightAmount(gameMinutes);
    for (size_t channel = 0; channel < 3; ++channel)
    {
        const float scale =
            daylight.nightScale[channel] + (daylight.dayScale[channel] - daylight.nightScale[channel]) * day;
        light.ambient[channel] = daylight.ambient[channel] * scale;
        light.sun[channel] = daylight.sun[channel] * scale * day * sunUp;
    }
    light.sunDirection = daylight.sunDirection ? *daylight.sunDirection : skySunDirection(gameMinutes);
    light.sunGain = daylight.sunGain;
    return light;
}

std::array<float, 3> indoorDaylightFogScale(const IndoorDaylight &daylight, float gameMinutes)
{
    std::array<float, 3> scale = {1.0f, 1.0f, 1.0f};
    if (!daylight.enabled)
    {
        return scale;
    }

    constexpr float NoonMinutes = 12.0f * 60.0f;
    const IndoorDaylightLight now = evaluateIndoorDaylight(daylight, gameMinutes);
    const IndoorDaylightLight noon = evaluateIndoorDaylight(daylight, NoonMinutes);
    for (size_t channel = 0; channel < 3; ++channel)
    {
        const float lightNow = std::min(now.ambient[channel] + 0.5f * now.sun[channel], 1.0f);
        const float lightNoon = std::min(noon.ambient[channel] + 0.5f * noon.sun[channel], 1.0f);
        if (lightNoon > 0.001f)
        {
            scale[channel] = std::clamp(lightNow / lightNoon, 0.0f, 1.0f);
        }
    }
    return scale;
}

void tintIndoorDaylight(IndoorDaylightLight &light, const std::array<float, 3> &sunTint,
    const std::array<float, 3> &skyTint)
{
    const auto apply = [](std::array<float, 3> &rgb, const std::array<float, 3> &tint)
    {
        const float scale = 1.0f / std::max(luminance(tint), 0.001f);
        for (size_t channel = 0; channel < 3; ++channel)
        {
            rgb[channel] *= tint[channel] * scale;
        }
    };
    apply(light.sun, sunTint);
    apply(light.ambient, skyTint);
}

IndoorBakedDaylightScale indoorBakedDaylightScale(const IndoorDaylight &daylight, const IndoorDaylightLight &now,
    float minimumAmbient)
{
    IndoorBakedDaylightScale scale = {};
    if (!daylight.enabled)
    {
        return scale;
    }

    constexpr float Smallest = 0.0001f;
    for (size_t channel = 0; channel < 3; ++channel)
    {
        scale.ambientLevel[channel] = daylight.ambient[channel];
        const float noonAmbient = std::max(daylight.ambient[channel] * daylight.dayScale[channel], minimumAmbient);
        scale.ambientScale[channel] = noonAmbient > Smallest ? now.ambient[channel] / noonAmbient : 1.0f;
        const float noonSun = daylight.sun[channel] * daylight.dayScale[channel];
        scale.sunScale[channel] = noonSun > Smallest ? now.sun[channel] / noonSun : scale.ambientScale[channel];
    }
    return scale;
}

std::array<float, 3> indoorBakedDaylightTexel(const IndoorBakedDaylightScale &scale, const std::array<float, 3> &texel)
{
    std::array<float, 3> light = {};
    for (size_t channel = 0; channel < 3; ++channel)
    {
        const float ambient = std::min(texel[channel], scale.ambientLevel[channel]);
        light[channel] = ambient * scale.ambientScale[channel] + (texel[channel] - ambient) * scale.sunScale[channel];
    }
    return light;
}

float indoorOpenAirLightScale(const IndoorDaylight &daylight, const IndoorDaylightLight &now)
{
    if (!daylight.enabled)
    {
        return 1.0f;
    }
    constexpr float Smallest = 0.0001f;
    std::array<float, 3> noonSun = {};
    std::array<float, 3> noonAmbient = {};
    for (size_t channel = 0; channel < 3; ++channel)
    {
        noonSun[channel] = daylight.sun[channel] * daylight.dayScale[channel];
        noonAmbient[channel] = daylight.ambient[channel] * daylight.dayScale[channel];
    }
    if (luminance(noonSun) > Smallest)
    {
        return std::clamp(luminance(now.sun) / luminance(noonSun), 0.0f, 1.0f);
    }
    return luminance(noonAmbient) > Smallest ? std::clamp(luminance(now.ambient) / luminance(noonAmbient), 0.0f, 1.0f)
                                            : 1.0f;
}

float indoorDaylightRoomLight(const IndoorDaylightLight &light)
{
    return std::min(luminance(light.ambient) + 0.5f * luminance(light.sun), 1.0f);
}

float indoorDaylightModelAmbient(const IndoorDaylightLight &light)
{
    return std::min(luminance(light.ambient), 1.0f);
}

}
