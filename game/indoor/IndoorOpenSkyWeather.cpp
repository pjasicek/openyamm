#include "game/indoor/IndoorOpenSkyWeather.h"

#include "game/audio/GameAudioSystem.h"
#include "game/indoor/IndoorMapData.h"
#include "game/render/SkyRenderer.h"
#include "game/render/SkyState.h"

#include <algorithm>
#include <cmath>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
// As the outdoor view (OutdoorRenderer): rain or snow below this shown strength leaves the sky as it is, and a game
// clock jump over this many minutes shows the new weather at once.
constexpr float ShownPrecipitationThreshold = 0.03f;
constexpr double SnapGameMinutes = 30.0;
// The roof map's cells (native units; about 0.6 m) and its largest side in cells (a BLV's int16 frame at 64 units).
constexpr float RoofCellSize = 64.0f;
constexpr uint32_t RoofMaxCells = 1024;
// The camera is under cover this far below a roof map surface (so standing on a floor is not under it).
constexpr float CoverMargin = 16.0f;
// The weather sound follows a change of cover (a door, a tunnel mouth) over about this many seconds.
constexpr float AudibilityFollowSeconds = 0.35f;
}

WeatherRoofMap buildIndoorWeatherRoofMap(const IndoorMapData &mapData)
{
    const auto drawnFromAbove = [](const IndoorFace &face)
    {
        return !face.isPortal && face.vertexIndices.size() >= 3
            && !hasFaceAttribute(face.attributes, FaceAttribute::IsPortal)
            && !hasFaceAttribute(face.attributes, FaceAttribute::IndoorSky)
            && !hasFaceAttribute(face.attributes, FaceAttribute::Invisible);
    };
    const auto point = [&mapData](uint16_t index) -> std::optional<std::array<float, 3>>
    {
        if (index >= mapData.vertices.size())
        {
            return std::nullopt;
        }

        const IndoorVertex &vertex = mapData.vertices[index];
        return std::array<float, 3>{float(vertex.x), float(vertex.y), float(vertex.z)};
    };
    float minX = 0.0f;
    float minY = 0.0f;
    float maxX = 0.0f;
    float maxY = 0.0f;
    bool any = false;

    for (const IndoorFace &face : mapData.faces)
    {
        if (!drawnFromAbove(face))
        {
            continue;
        }

        for (const uint16_t index : face.vertexIndices)
        {
            if (const std::optional<std::array<float, 3>> vertex = point(index))
            {
                minX = any ? std::min(minX, (*vertex)[0]) : (*vertex)[0];
                minY = any ? std::min(minY, (*vertex)[1]) : (*vertex)[1];
                maxX = any ? std::max(maxX, (*vertex)[0]) : (*vertex)[0];
                maxY = any ? std::max(maxY, (*vertex)[1]) : (*vertex)[1];
                any = true;
            }
        }
    }

    WeatherRoofMap roofMap;

    if (!any)
    {
        return roofMap;
    }

    roofMap.reset(minX, minY, maxX, maxY, RoofCellSize, RoofMaxCells);

    for (const IndoorFace &face : mapData.faces)
    {
        if (!drawnFromAbove(face))
        {
            continue;
        }

        const std::optional<std::array<float, 3>> first = point(face.vertexIndices[0]);

        for (size_t corner = 1; first && corner + 1 < face.vertexIndices.size(); ++corner)
        {
            const std::optional<std::array<float, 3>> second = point(face.vertexIndices[corner]);
            const std::optional<std::array<float, 3>> third = point(face.vertexIndices[corner + 1]);

            if (second && third)
            {
                roofMap.addTriangle(*first, *second, *third);
            }
        }
    }

    return roofMap;
}

void IndoorOpenSkyWeather::setRoofMap(WeatherRoofMap roofMap)
{
    m_roofMap = std::move(roofMap);
    m_roofMapUploaded = false;
    m_roofMapUnusable = false;
}

bool IndoorOpenSkyWeather::covers(float x, float y, float z) const
{
    return hasRoofMap() && m_roofMap.covers(x, y, z, CoverMargin);
}

void IndoorOpenSkyWeather::configure(const std::optional<OutdoorWeatherProfile> &profile)
{
    m_profile = profile;
    m_presentation = {};
    m_lastElapsedSeconds = -1.0f;
    m_frameSeconds = 0.0f;
    m_wetnessMinute = -1;
    m_wetness = 0.0f;
    m_roofMap = {};
    m_roofMapUploaded = false;
    m_roofMapUnusable = false;
    m_audibility = 0.0f;
    m_fog = {};
}

void IndoorOpenSkyWeather::update(double gameMinutes, float elapsedSeconds, GameAudioSystem *pAudio, float audibility)
{
    if (!m_profile)
    {
        return;
    }

    const WeatherRules &rules = m_profile->weatherRules;
    const WeatherMapSettings &settings = m_profile->weatherMap;
    WeatherSample target = sampleRolledWeather(rules, settings, gameMinutes);
    m_fog = sampleOpenSkyFog(rules, settings, gameMinutes, m_debugFog);
    // Wetness integrates hours of weather: resampled once per game minute, as the outdoor runtime does.
    const int64_t minute = static_cast<int64_t>(std::floor(gameMinutes));

    if (minute != m_wetnessMinute)
    {
        m_wetness = sampleWetness(rules, settings, static_cast<double>(minute));
        m_wetnessMinute = minute;
    }

    target.wetness = m_wetness;
    if (m_debugPrecipitation)
    {
        // As the outdoor console override: the kind at the given strength, under clouds to match.
        target.precipitation = *m_debugPrecipitation;
        target.intensity = *m_debugPrecipitation == PrecipitationKind::None ? 0.0f : m_debugIntensity;
        target.cloudCover = std::max(target.cloudCover, target.intensity > 0.0f ? 0.6f + 0.4f * target.intensity : 0.0f);
        // A storm is heavy rain, forced or rolled: never thunder over forced snow or a forced clear sky.
        target.storm = target.precipitation == PrecipitationKind::Rain && target.intensity >= rules.stormThreshold;
        target.dryLightning = false;
    }
    m_lastTarget = target;
    m_frameSeconds = 0.0f;

    if (m_lastElapsedSeconds < 0.0f || std::abs(gameMinutes - m_lastGameMinutes) > SnapGameMinutes)
    {
        m_presentation.snap();
        m_audibility = audibility;
    }
    else
    {
        m_frameSeconds = std::max(elapsedSeconds - m_lastElapsedSeconds, 0.0f);
        // Under water is silent at once; cover fades the sound in and out.
        m_audibility = audibility <= 0.0f ? 0.0f
            : m_audibility + (audibility - m_audibility)
                * (1.0f - std::exp(-m_frameSeconds / AudibilityFollowSeconds));
    }

    m_lastElapsedSeconds = elapsedSeconds;
    m_lastGameMinutes = gameMinutes;
    m_presentation.update(rules, target, m_frameSeconds);
    const std::vector<LightningStrike> strikes = m_presentation.takeStrikes();

    if (pAudio != nullptr)
    {
        m_audio.update(*pAudio, rules.sounds, m_presentation, strikes, m_audibility, m_frameSeconds);
    }
}

void IndoorOpenSkyWeather::applyToSky(SkyInputs &inputs) const
{
    if (!m_profile)
    {
        return;
    }

    inputs.raining = m_presentation.rainLevel() > ShownPrecipitationThreshold;
    inputs.snowing = !inputs.raining && m_presentation.snowLevel() > ShownPrecipitationThreshold;
    inputs.precipitation = std::max(m_presentation.rainLevel(), m_presentation.snowLevel());
    inputs.lightningFlash = m_presentation.lightningFlash();
    inputs.foggy = m_fog.foggy;
    inputs.fogStrongDistance = m_fog.foggy ? m_fog.farDistance : 0.0f;
}

float IndoorOpenSkyWeather::rainRings() const
{
    if (!m_profile)
    {
        return 0.0f;
    }

    const float rain = m_presentation.rainLevel();
    return std::min(1.0f, rain * 10.0f) * (0.15f + 0.75f * rain);
}

void IndoorOpenSkyWeather::render(uint16_t viewId, const std::array<float, 3> &camera, float yawRadians,
    const float *pProjection, uint16_t viewHeight, const SkyFrameState *pSky, WeatherQuality quality,
    const WeatherGroundQuery &ground, bool covered, const std::array<float, 3> *pHaze)
{
    if (!m_profile || quality == WeatherQuality::Off
        || (m_presentation.rainLevel() <= 0.0f && m_presentation.snowLevel() <= 0.0f
            && m_presentation.ashLevel() <= 0.0f))
    {
        m_renderer.resetCamera();
        return;
    }

    if (!m_renderer.isReady())
    {
        if (m_rendererInitializeAttempted)
        {
            return;
        }

        m_rendererInitializeAttempted = true;

        if (!m_renderer.initialize())
        {
            std::cerr << "Cannot create weather rendering resources.\n";
            return;
        }
    }

    if (!m_roofMapUploaded)
    {
        m_roofMapUploaded = true;
        m_roofMapUnusable = !m_renderer.setRoofMap(m_roofMap.empty() ? nullptr : &m_roofMap);

        if (m_roofMapUnusable)
        {
            std::cerr << "Weather roof map unavailable on this GPU: weather shows only in open-sky sectors.\n";
        }
    }

    // Lit as the outdoor view lights it: the sky's brightness with part of its hue, dimmed by cloud, lit by lightning.
    std::array<float, 3> light = {0.6f, 0.6f, 0.6f};

    if (pSky != nullptr)
    {
        const std::array<float, 3> tint = skyEnvironmentTint(*pSky);
        const float luminance = 0.2126f * tint[0] + 0.7152f * tint[1] + 0.0722f * tint[2];

        for (size_t channel = 0; channel < 3; ++channel)
        {
            light[channel] = 0.05f + 0.9f * std::min(luminance + (tint[channel] - luminance) * 0.35f, 1.3f);
        }
    }

    const float cloudDimming = 1.0f - 0.25f * m_presentation.cloudCover();
    // In a scene's fog the drops and flakes are seen through its colour, which follows the daylight but not the
    // cloud that dims the sky's light here, and MM9's fogs are brighter than its sky: lit by the sky alone, snow fell
    // as dark specks through Frosgard City's grey fog and rain as dark streaks through Sturmford's. They take at least
    // the light that makes rain as bright as the haze (snow brighter, ash darker).
    constexpr float HazeLight = 1.3f;

    for (size_t channel = 0; channel < 3; ++channel)
    {
        light[channel] *= cloudDimming;
        if (pHaze != nullptr)
        {
            light[channel] = std::max(light[channel], (*pHaze)[channel] * HazeLight);
        }
        light[channel] += 0.9f * m_presentation.lightningFlash();
    }

    const WeatherRules &rules = m_profile->weatherRules;
    const WeatherMapSettings &settings = m_profile->weatherMap;
    WeatherDrawFrame frame;
    frame.camera = camera;
    frame.forward = {std::cos(yawRadians), std::sin(yawRadians)};
    frame.groundHeight = ground;
    frame.deltaSeconds = m_frameSeconds;
    frame.rainLevel = m_presentation.rainLevel();
    frame.snowLevel = m_presentation.snowLevel();
    frame.ashLevel = m_presentation.ashLevel();
    frame.snowLook = rules.snowFlakes;
    frame.ashLook = settings.ashLook.value_or(rules.ashFlakes);
    frame.rainColor = settings.rainColor;
    frame.windX = m_presentation.windX();
    frame.windY = m_presentation.windY();
    frame.light = light;
    frame.pixelWorldSize = 2.0f / std::max(std::abs(pProjection[5]) * static_cast<float>(viewHeight), 1.0f);
    frame.quality = quality;
    frame.curtain = !covered;
    m_renderer.render(viewId, frame);
}

void IndoorOpenSkyWeather::setDebugPrecipitation(std::optional<PrecipitationKind> kind, float intensity)
{
    m_debugPrecipitation = kind;
    m_debugIntensity = std::clamp(intensity, 0.0f, 1.0f);
}

void IndoorOpenSkyWeather::shutdown(GameAudioSystem *pAudio, bool gpuAlive)
{
    if (pAudio != nullptr)
    {
        m_audio.stop(*pAudio);
    }
    else
    {
        m_audio.forget();
    }

    if (gpuAlive)
    {
        m_renderer.shutdown();
    }

    m_rendererInitializeAttempted = false;
    m_profile.reset();
    m_roofMap = {};
    m_roofMapUploaded = false;
    m_roofMapUnusable = false;
}
}
